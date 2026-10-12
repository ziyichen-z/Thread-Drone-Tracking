using System;
using System.IO;
using System.Text;
using UnityEngine;

namespace TetheredTracking
{
    public enum RateStudyExperimentState
    {
        Hold,
        Released,
        Aborted,
    }

    public sealed class RateStudyExperimentController : MonoBehaviour
    {
        public float pollInterval = 0.02f;
        public bool IsActive { get; private set; }
        public RateStudyExperimentState State { get; private set; } =
            RateStudyExperimentState.Hold;
        public bool MeasurementEnabled =>
            !IsActive || State == RateStudyExperimentState.Released;
        public bool ControlEnabled =>
            !IsActive || State == RateStudyExperimentState.Released;
        public long ReleaseFrameId { get; private set; } = -1;

        RateStudySession session;
        LoopTargetVehicle target;
        SensorFrameWriter frameWriter;
        string runtimeRoot;
        string lastControlSha256;
        float timer;
        long rejectedReleaseCommands;
        long rejectedControlCommands;
        string lastRejectionCode;
        string lastRejectionChannel;
        string lastRejectionCommandId;
        long rejectionSequence;
        bool initializationBlocked;

        internal RateStudySession Session => session;

        internal bool UsesSharedHostClock => session != null && session.IsRate3;

        internal void Initialize(
            ScenarioConfig scenarioConfig,
            LoopTargetVehicle configuredTarget,
            SensorFrameWriter configuredFrameWriter)
        {
            Initialize(
                scenarioConfig,
                configuredTarget,
                configuredFrameWriter,
                RuntimePaths.Root);
        }

        internal void Initialize(
            ScenarioConfig scenarioConfig,
            LoopTargetVehicle configuredTarget,
            SensorFrameWriter configuredFrameWriter,
            string configuredRuntimeRoot)
        {
            if (string.IsNullOrWhiteSpace(configuredRuntimeRoot))
                throw new ArgumentException(
                    "Runtime root is required.",
                    nameof(configuredRuntimeRoot));
            runtimeRoot = configuredRuntimeRoot;
            Directory.CreateDirectory(runtimeRoot);
            target = configuredTarget;
            frameWriter = configuredFrameWriter;
            string sessionPath = Path.Combine(runtimeRoot, "rate_study_session.json");
            if (!RateStudySession.TryLoad(sessionPath, out RateStudySession loaded, out string error))
            {
                IsActive = false;
                return;
            }
            IsActive = true;
            session = loaded;
            if (error != null
                || scenarioConfig == null
                || session == null
                || session.scenario_id != scenarioConfig.scenario_id)
            {
                BlockHold(error ?? "invalid_session_scenario");
                return;
            }
            if (HasStaleRuntimeSlot(runtimeRoot))
            {
                BlockHold("stale_runtime_slot");
                return;
            }
            EnterHold();
        }

        internal void InitializeForTests(
            RateStudySession configuredSession,
            string configuredRuntimeRoot,
            LoopTargetVehicle configuredTarget)
        {
            session = configuredSession;
            runtimeRoot = configuredRuntimeRoot;
            target = configuredTarget;
            IsActive = true;
            string error = session?.Validate();
            if (error != null)
            {
                BlockHold(error);
                return;
            }
            EnterHold();
        }

        void EnterHold()
        {
            State = RateStudyExperimentState.Hold;
            if (target != null)
            {
                try { target.PlaceAtRouteDistance(session.hold_route_s_m); }
                catch (Exception)
                {
                    BlockHold("invalid_hold_route_distance");
                    return;
                }
                target.SetMotionEnabled(false);
            }
            WriteState();
        }

        void Update()
        {
            if (!IsActive || initializationBlocked) return;
            timer += Time.deltaTime;
            if (timer < pollInterval) return;
            timer = 0f;
            PollControl();
        }

        void PollControl()
        {
            string path = Path.Combine(runtimeRoot, "experiment_control.json");
            if (!File.Exists(path)) return;
            byte[] bytes;
            try { bytes = File.ReadAllBytes(path); }
            catch (IOException) { return; }
            string sha256 = RateStudyProtocol.Sha256(bytes);
            if (sha256 == lastControlSha256) return;
            lastControlSha256 = sha256;
            ProcessCommand(
                bytes,
                frameWriter == null ? -1 : frameWriter.LastPublishedFrameId,
                UnixNow(),
                UsesSharedHostClock
                    ? SensorFrameWriter.HostMonotonicSeconds()
                    : Time.realtimeSinceStartupAsDouble,
                frameWriter == null
                    ? Time.timeAsDouble
                    : frameWriter.CurrentSimulationTimeSeconds);
        }

        internal bool ProcessCommandForTests(
            byte[] commandBytes,
            long currentFrameId,
            double unixSeconds = 1000.0,
            double monotonicSeconds = 500.0,
            double simulationSeconds = 10.0)
        {
            return ProcessCommand(
                commandBytes,
                currentFrameId,
                unixSeconds,
                monotonicSeconds,
                simulationSeconds);
        }

        bool ProcessCommand(
            byte[] commandBytes,
            long currentFrameId,
            double unixSeconds,
            double monotonicSeconds,
            double simulationSeconds)
        {
            if (!IsActive || commandBytes == null || commandBytes.Length == 0) return false;
            ExperimentControlDocument command;
            try
            {
                command = JsonUtility.FromJson<ExperimentControlDocument>(
                    Encoding.UTF8.GetString(commandBytes));
            }
            catch (Exception)
            {
                RejectRelease("invalid_command_json", null);
                return false;
            }
            if (command == null
                || command.channel != "experiment_control"
                || string.IsNullOrWhiteSpace(command.command_id))
            {
                RejectRelease("invalid_command_envelope", command?.command_id);
                return false;
            }
            bool rate3 = UsesSharedHostClock;
            string releaseSchema = rate3
                ? RateStudyProtocol.ReleaseCommandSchemaV3
                : RateStudyProtocol.ReleaseCommandSchema;
            string abortSchema = rate3
                ? RateStudyProtocol.AbortCommandSchemaV3
                : RateStudyProtocol.AbortCommandSchema;
            bool isAbort = command.command_type == "abort"
                && command.schema_version == abortSchema;
            bool isRelease = command.command_type == "release"
                && command.schema_version == releaseSchema;
            if (!isAbort && !isRelease)
            {
                RejectRelease("invalid_command_schema_or_type", command.command_id);
                return false;
            }
            if (rate3
                && isRelease
                && command.release_clock_id != RateStudyProtocol.SharedHostClockId)
            {
                RejectRelease("invalid_release_clock_id", command.command_id);
                return false;
            }
            if (!RateStudyProtocol.SameIdentity(
                session,
                command.study_id,
                command.run_id,
                command.scenario_id,
                command.tracker_id,
                command.tracker_identity_sha256,
                command.model_identity_sha256,
                command.init_frame_id,
                command.init_image_sha256))
            {
                Abort("fatal_identity_mismatch", command.command_id);
                return false;
            }
            if (isAbort)
            {
                Abort("explicit_abort", command.command_id);
                return true;
            }
            if (State == RateStudyExperimentState.Released)
            {
                RejectRelease("release_replay_after_released", command.command_id);
                return false;
            }
            if (State == RateStudyExperimentState.Aborted)
            {
                RejectRelease("release_after_aborted", command.command_id);
                return false;
            }

            if (!RateStudyProtocol.IsSha256(command.ready_sha256)
                || string.IsNullOrWhiteSpace(command.ready_json_base64))
            {
                RejectRelease("invalid_ready_binding", command.command_id);
                return false;
            }
            byte[] readyBytes;
            try { readyBytes = Convert.FromBase64String(command.ready_json_base64); }
            catch (FormatException)
            {
                RejectRelease("invalid_ready_base64", command.command_id);
                return false;
            }
            if (RateStudyProtocol.Sha256(readyBytes) != command.ready_sha256)
            {
                RejectRelease("ready_hash_mismatch", command.command_id);
                return false;
            }
            TrackerReadyDocument ready;
            try
            {
                ready = JsonUtility.FromJson<TrackerReadyDocument>(
                    Encoding.UTF8.GetString(readyBytes));
            }
            catch (Exception)
            {
                RejectRelease("invalid_ready_json", command.command_id);
                return false;
            }
            string readyError = rate3
                ? ValidReadyRate3Error(ready, monotonicSeconds)
                : (ValidReady(ready) ? null : "invalid_ready_evidence");
            if (readyError != null)
            {
                RejectRelease(readyError, command.command_id);
                return false;
            }
            if (!RateStudyProtocol.SameIdentity(
                session,
                ready.study_id,
                ready.run_id,
                ready.scenario_id,
                ready.tracker_id,
                ready.tracker_identity_sha256,
                ready.model_identity_sha256,
                ready.init_frame_id,
                ready.init_image_sha256))
            {
                Abort("fatal_ready_identity_mismatch", command.command_id);
                return false;
            }
            long backlog = currentFrameId - ready.last_processed_frame_id;
            if (backlog < 0 || backlog > 1)
            {
                RejectRelease("backlog_out_of_range", command.command_id);
                return false;
            }
            if (!RateStudyProtocol.Finite(unixSeconds)
                || !RateStudyProtocol.Finite(monotonicSeconds)
                || !RateStudyProtocol.Finite(simulationSeconds))
            {
                RejectRelease("invalid_release_clock", command.command_id);
                return false;
            }

            string commandSha256 = RateStudyProtocol.Sha256(commandBytes);
            State = RateStudyExperimentState.Released;
            ReleaseFrameId = currentFrameId;
            TetheredScenarioBootstrap.Instance?.StartMeasurement(
                "rate-study-release-frame");
            if (target != null) target.SetMotionEnabled(true);
            ReleaseAckDocument ack;
            if (rate3)
            {
                ack = new ReleaseAckDocumentV3
                {
                    command_id = command.command_id,
                    study_id = session.study_id,
                    run_id = session.run_id,
                    scenario_id = session.scenario_id,
                    release_command_sha256 = commandSha256,
                    ready_sha256 = command.ready_sha256,
                    tracker_id = session.tracker_id,
                    tracker_identity_sha256 = session.tracker_identity_sha256,
                    model_identity_sha256 = session.model_identity_sha256,
                    init_frame_id = session.init_frame_id,
                    init_image_sha256 = session.init_image_sha256,
                    ready_seq = ready.seq,
                    processed_frame_count = ready.processed_frame_count,
                    current_frame_id = currentFrameId,
                    last_processed_frame_id = ready.last_processed_frame_id,
                    accepted_backlog_frames = backlog,
                    release_frame_id = currentFrameId,
                    release_unix_s = unixSeconds,
                    release_monotonic_s = monotonicSeconds,
                    release_simulation_s = simulationSeconds,
                };
            }
            else
            {
                ack = new ReleaseAckDocument
                {
                    command_id = command.command_id,
                    study_id = session.study_id,
                    run_id = session.run_id,
                    scenario_id = session.scenario_id,
                    release_command_sha256 = commandSha256,
                    ready_sha256 = command.ready_sha256,
                    tracker_id = session.tracker_id,
                    tracker_identity_sha256 = session.tracker_identity_sha256,
                    model_identity_sha256 = session.model_identity_sha256,
                    init_frame_id = session.init_frame_id,
                    init_image_sha256 = session.init_image_sha256,
                    ready_seq = ready.seq,
                    processed_frame_count = ready.processed_frame_count,
                    current_frame_id = currentFrameId,
                    last_processed_frame_id = ready.last_processed_frame_id,
                    accepted_backlog_frames = backlog,
                    release_frame_id = currentFrameId,
                    release_unix_s = unixSeconds,
                    release_monotonic_s = monotonicSeconds,
                    release_simulation_s = simulationSeconds,
                };
            }
            AtomicFile.WriteAllBytes(
                Path.Combine(runtimeRoot, "release_command.accepted.json"),
                commandBytes);
            AtomicFile.WriteAllText(
                Path.Combine(runtimeRoot, "release_ack.json"),
                JsonUtility.ToJson(ack, true) + "\n");
            WriteState();
            return true;
        }

        bool ValidReady(TrackerReadyDocument ready)
        {
            return ready != null
                && ready.schema_version == RateStudyProtocol.ReadySchema
                && ready.state == "TRACKING"
                && ready.last_processed_frame_id >= 0
                && ready.processed_frame_count >= session.minimum_processed_frames
                && ready.seq >= session.minimum_ready_seq
                && RateStudyProtocol.Finite(ready.publisher_monotonic_s)
                && ready.publisher_monotonic_s >= 0.0;
        }

        string ValidReadyRate3Error(TrackerReadyDocument ready, double monotonicSeconds)
        {
            if (ready == null
                || ready.schema_version != RateStudyProtocol.ReadySchemaV3
                || ready.state != "TRACKING"
                || ready.last_processed_frame_id < 0
                || ready.processed_frame_count < session.minimum_processed_frames
                || ready.seq < session.minimum_ready_seq)
                return "invalid_ready_evidence";
            double readyAgeSeconds = monotonicSeconds - ready.publisher_monotonic_s;
            if (ready.publisher_clock_id != RateStudyProtocol.SharedHostClockId
                || !RateStudyProtocol.Finite(ready.publisher_monotonic_s)
                || ready.publisher_monotonic_s < 0.0
                || !RateStudyProtocol.Finite(ready.heartbeat_interval_s)
                || ready.heartbeat_interval_s <= 0.0
                || ready.heartbeat_interval_s > 1.0
                || readyAgeSeconds < 0.0
                || readyAgeSeconds > 2.0 * ready.heartbeat_interval_s)
                return "invalid_ready_clock_identity";
            return null;
        }

        public bool AuthorizeControl(string channel, long commandId)
        {
            if (ControlEnabled) return true;
            rejectedControlCommands++;
            lastRejectionCode = "control_suppressed_before_release";
            lastRejectionChannel = channel;
            lastRejectionCommandId = commandId.ToString();
            PersistRejection();
            WriteState();
            return false;
        }

        public bool AcceptsMeasurementFrame(long frameId)
        {
            return !IsActive
                || (State == RateStudyExperimentState.Released
                    && frameId > ReleaseFrameId);
        }

        void RejectRelease(string code, string commandId)
        {
            rejectedReleaseCommands++;
            lastRejectionCode = code;
            lastRejectionChannel = "experiment_control";
            lastRejectionCommandId = commandId;
            PersistRejection();
            WriteState();
        }

        void Abort(string code, string commandId = null)
        {
            IsActive = true;
            State = RateStudyExperimentState.Aborted;
            if (target != null) target.SetMotionEnabled(false);
            lastRejectionCode = code;
            lastRejectionChannel = "experiment_control";
            lastRejectionCommandId = commandId;
            if (code != "explicit_abort") PersistRejection();
            WriteState();
        }

        void BlockHold(string code)
        {
            IsActive = true;
            initializationBlocked = true;
            State = RateStudyExperimentState.Hold;
            if (target != null) target.SetMotionEnabled(false);
            lastRejectionCode = code;
            lastRejectionChannel = "session_initialization";
            lastRejectionCommandId = null;
            PersistRejection();
            WriteState();
        }

        void PersistRejection()
        {
            if (string.IsNullOrEmpty(runtimeRoot)) return;
            rejectionSequence++;
            string directory = Path.Combine(runtimeRoot, "experiment_rejections");
            var document = new ExperimentRejectionDocument
            {
                study_id = session?.study_id,
                run_id = session?.run_id,
                state = State.ToString().ToUpperInvariant(),
                code = lastRejectionCode,
                channel = lastRejectionChannel,
                command_id = lastRejectionCommandId,
                sequence = rejectionSequence,
                rejected_unix_s = UnixNow(),
            };
            AtomicFile.WriteAllText(
                Path.Combine(
                    directory,
                    "rejection_" + rejectionSequence.ToString("D6") + ".json"),
                JsonUtility.ToJson(document, true) + "\n");
        }

        void WriteState()
        {
            if (string.IsNullOrEmpty(runtimeRoot)) return;
            var document = new ExperimentStateDocument
            {
                study_id = session?.study_id,
                run_id = session?.run_id,
                state = State.ToString().ToUpperInvariant(),
                rejected_release_commands = rejectedReleaseCommands,
                rejected_control_commands = rejectedControlCommands,
                last_rejection_code = lastRejectionCode,
                last_rejection_channel = lastRejectionChannel,
                last_rejection_command_id = lastRejectionCommandId,
                updated_unix_s = UnixNow(),
            };
            AtomicFile.WriteAllText(
                Path.Combine(runtimeRoot, "experiment_state.json"),
                JsonUtility.ToJson(document, true) + "\n");
        }

        internal static bool HasStaleRuntimeSlot(string root)
        {
            return File.Exists(Path.Combine(root, "tracker_ready.json"))
                || File.Exists(Path.Combine(root, "experiment_control.json"))
                || File.Exists(Path.Combine(root, "release_ack.json"))
                || File.Exists(Path.Combine(root, "release_command.accepted.json"))
                // A leftover RATE-003 evaluation-truth stream would silently
                // prepend a previous attempt's samples to this run's §5/§11
                // analysis, so it is a stale slot like any other.
                || File.Exists(Path.Combine(
                    root,
                    CoverageEvaluator.Rate3EvaluationTruthFileName))
                || Directory.Exists(Path.Combine(root, "experiment_rejections"));
        }

        public static void PrepareRuntimeSlots(string root)
        {
            if (string.IsNullOrWhiteSpace(root))
                throw new ArgumentException("Runtime root is required.", nameof(root));
            Directory.CreateDirectory(root);
            string[] names =
            {
                "tracker_ready.json",
                "experiment_control.json",
                "release_ack.json",
                "release_command.accepted.json",
                "experiment_state.json",
                CoverageEvaluator.Rate3EvaluationTruthFileName,
            };
            foreach (string name in names)
            {
                string path = Path.Combine(root, name);
                if (File.Exists(path)) File.Delete(path);
            }
            string rejections = Path.Combine(root, "experiment_rejections");
            if (Directory.Exists(rejections)) Directory.Delete(rejections, true);
        }

        static double UnixNow() =>
            DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;
    }
}
