using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;

namespace TetheredTracking
{
    [Serializable]
    public sealed class RateStudySession
    {
        public string schema_version = "p1-rate2-session/v1";
        public string study_id;
        public string run_id;
        public string scenario_id;
        public string tracker_id;
        public string tracker_identity_sha256;
        public string model_identity_sha256;
        public long init_frame_id = -1;
        public string init_image_sha256;
        public float hold_route_s_m;
        public int minimum_ready_seq = 20;
        public int minimum_processed_frames = 20;
        public float planned_duration_s;
        public string sensor_frame_schema;
        public string capture_monotonic_clock_id;

        internal bool IsRate3 => schema_version == "p1-rate3-session/v1";

        internal string Validate()
        {
            if (schema_version == "p1-rate2-session/v1") return ValidateRate2();
            if (schema_version == "p1-rate3-session/v1") return ValidateRate3();
            return "invalid_session_schema";
        }

        string ValidateRate2()
        {
            if (string.IsNullOrWhiteSpace(study_id)
                || string.IsNullOrWhiteSpace(run_id)
                || string.IsNullOrWhiteSpace(scenario_id)
                || string.IsNullOrWhiteSpace(tracker_id)) return "missing_session_identity";
            if (study_id != "P1-M2-RATE-002-B2" || tracker_id != "nanotrack-v2")
                return "invalid_batch_or_tracker_identity";
            string expectedScenario = ExpectedScenario(run_id);
            if (expectedScenario == null || scenario_id != expectedScenario)
                return "invalid_run_or_scenario_identity";
            if (!RateStudyProtocol.IsSha256(tracker_identity_sha256)
                || !RateStudyProtocol.IsSha256(model_identity_sha256)
                || !RateStudyProtocol.IsSha256(init_image_sha256))
                return "invalid_session_hash";
            if (init_frame_id < 0
                || minimum_ready_seq != 20
                || minimum_processed_frames != 20)
                return "invalid_session_counter";
            if (!RateStudyProtocol.Finite(hold_route_s_m) || hold_route_s_m < 0f)
                return "invalid_hold_route_distance";
            return null;
        }

        string ValidateRate3()
        {
            if (string.IsNullOrWhiteSpace(study_id)
                || string.IsNullOrWhiteSpace(run_id)
                || string.IsNullOrWhiteSpace(scenario_id)
                || string.IsNullOrWhiteSpace(tracker_id)) return "missing_session_identity";
            bool clockSmoke = study_id == "P1-M2-RATE-003-CLOCKSMOKE";
            if ((!clockSmoke && study_id != "P1-M2-RATE-003-B1")
                || tracker_id != "nanotrack-v2")
                return "invalid_batch_or_tracker_identity";
            string expectedScenario = ExpectedScenarioRate3(run_id, clockSmoke);
            if (expectedScenario == null || scenario_id != expectedScenario)
                return "invalid_run_or_scenario_identity";
            if (!RateStudyProtocol.IsSha256(tracker_identity_sha256)
                || !RateStudyProtocol.IsSha256(model_identity_sha256)
                || !RateStudyProtocol.IsSha256(init_image_sha256))
                return "invalid_session_hash";
            if (init_frame_id < 0
                || minimum_ready_seq != 20
                || minimum_processed_frames != 20)
                return "invalid_session_counter";
            if (!RateStudyProtocol.Finite(hold_route_s_m) || hold_route_s_m < 0f)
                return "invalid_hold_route_distance";
            float expectedDuration = clockSmoke ? 30.0f : 150.0f;
            if (!RateStudyProtocol.Finite(planned_duration_s)
                || Math.Abs(planned_duration_s - expectedDuration) > 1e-6f)
                return "invalid_session_counter";
            if (sensor_frame_schema != "tethered-sensor-frame/v3"
                || capture_monotonic_clock_id != RateStudyProtocol.SharedHostClockId)
                return "invalid_session_clock_identity";
            return null;
        }

        static string ExpectedScenarioRate3(string runId, bool clockSmoke)
        {
            if (clockSmoke)
                return runId == "rs3-clock-smoke" ? "p1-scene-004" : null;
            if (runId == "rs3-probe-d2") return "p1-scene-004-d2";
            // Scouting has no RATE session: like RATE-002 §3 it runs as a
            // stand-alone Unity tool with the experiment controller inactive,
            // so `rs3-scouting` is deliberately not a session identity here.
            string[] pieces = runId?.Split('-');
            if (pieces == null || pieces.Length != 4 || pieces[0] != "rs3")
                return null;
            bool validDifficulty = pieces[1] == "d1" || pieces[1] == "d2";
            bool validPhase = pieces[2] == "p1" || pieces[2] == "p2" || pieces[2] == "p3";
            // BC-DRB-4 replaces the two `rs3-d{1|2}-calib` slots with six
            // per-phase `rs3-d{1|2}-p{1|2|3}-calib` HOLD calibration slots.
            bool validTail = pieces[3] == "r5"
                || pieces[3] == "r20"
                || pieces[3] == "calib";
            if (!validDifficulty || !validPhase || !validTail) return null;
            return pieces[1] == "d2" ? "p1-scene-004-d2" : "p1-scene-004";
        }

        static string ExpectedScenario(string runId)
        {
            if (runId == "rs2-pilot" || runId == "rs2-r20-calib")
                return "rate-study-20hz";
            if (runId == "rs2-r5-calib") return "rate-study-5hz";
            string[] pieces = runId?.Split('-');
            if (pieces == null || pieces.Length != 4 || pieces[0] != "rs2")
                return null;
            bool validRate = pieces[1] == "r5" || pieces[1] == "r20";
            bool validCondition = pieces[2] == "follow" || pieces[2] == "nadir";
            bool validReplicate =
                pieces[3] == "1" || pieces[3] == "2" || pieces[3] == "3";
            if (!validRate || !validCondition || !validReplicate) return null;
            return pieces[1] == "r5" ? "rate-study-5hz" : "rate-study-20hz";
        }

        public static bool TryLoad(string path, out RateStudySession session, out string error)
        {
            session = null;
            error = null;
            if (!File.Exists(path)) return false;
            try
            {
                session = JsonUtility.FromJson<RateStudySession>(File.ReadAllText(path));
            }
            catch (Exception exception)
            {
                error = "invalid_session_json:" + exception.GetType().Name;
                return true;
            }
            error = session == null ? "invalid_session_json" : session.Validate();
            return true;
        }
    }

    [Serializable]
    internal sealed class TrackerReadyDocument
    {
        public string schema_version;
        public string state;
        public string study_id;
        public string run_id;
        public string scenario_id;
        public string tracker_id;
        public string tracker_identity_sha256;
        public string model_identity_sha256;
        public long init_frame_id;
        public string init_image_sha256;
        public long last_processed_frame_id;
        public long processed_frame_count;
        public long seq;
        public double publisher_monotonic_s;
        public string publisher_clock_id;
        public double heartbeat_interval_s;
    }

    [Serializable]
    internal sealed class ExperimentControlDocument
    {
        public string schema_version;
        public string channel;
        public string command_type;
        public string command_id;
        public string study_id;
        public string run_id;
        public string scenario_id;
        public string tracker_id;
        public string tracker_identity_sha256;
        public string model_identity_sha256;
        public long init_frame_id;
        public string init_image_sha256;
        public string ready_json_base64;
        public string ready_sha256;
        public string release_clock_id;
    }

    [Serializable]
    internal class ReleaseAckDocument
    {
        public string schema_version = "p1-rate2-release-ack/v1";
        public string command_id;
        public string study_id;
        public string run_id;
        public string scenario_id;
        public string release_command_sha256;
        public string ready_sha256;
        public string tracker_id;
        public string tracker_identity_sha256;
        public string model_identity_sha256;
        public long init_frame_id;
        public string init_image_sha256;
        public long ready_seq;
        public long processed_frame_count;
        public long current_frame_id;
        public long last_processed_frame_id;
        public long accepted_backlog_frames;
        public long release_frame_id;
        public double release_unix_s;
        public double release_monotonic_s;
        public double release_simulation_s;
    }

    [Serializable]
    internal sealed class ReleaseAckDocumentV3 : ReleaseAckDocument
    {
        public string release_clock_id = "system-stopwatch/v1";

        public ReleaseAckDocumentV3()
        {
            schema_version = "p1-rate3-release-ack/v1";
        }
    }

    [Serializable]
    internal sealed class ExperimentStateDocument
    {
        public string schema_version = "p1-rate2-experiment-state/v1";
        public string study_id;
        public string run_id;
        public string state;
        public long rejected_release_commands;
        public long rejected_control_commands;
        public string last_rejection_code;
        public string last_rejection_channel;
        public string last_rejection_command_id;
        public double updated_unix_s;
    }

    [Serializable]
    internal sealed class ExperimentRejectionDocument
    {
        public string schema_version = "p1-rate2-experiment-rejection/v1";
        public string study_id;
        public string run_id;
        public string state;
        public string code;
        public string channel;
        public string command_id;
        public long sequence;
        public double rejected_unix_s;
    }

    internal static class RateStudyProtocol
    {
        internal const string ReleaseCommandSchema = "p1-rate2-release-command/v1";
        internal const string AbortCommandSchema = "p1-rate2-abort-command/v1";
        internal const string ReadySchema = "p1-rate2-tracker-ready/v2";
        internal const string ReleaseCommandSchemaV3 = "p1-rate3-release-command/v1";
        internal const string AbortCommandSchemaV3 = "p1-rate3-abort-command/v1";
        internal const string ReadySchemaV3 = "p1-rate3-tracker-ready/v1";
        internal const string SharedHostClockId = "system-stopwatch/v1";

        internal static string Sha256(byte[] bytes)
        {
            using SHA256 sha256 = SHA256.Create();
            byte[] digest = sha256.ComputeHash(bytes);
            var builder = new StringBuilder(digest.Length * 2);
            foreach (byte value in digest) builder.Append(value.ToString("x2"));
            return builder.ToString();
        }

        internal static bool IsSha256(string value)
        {
            if (value == null || value.Length != 64) return false;
            foreach (char character in value)
            {
                bool digit = character >= '0' && character <= '9';
                bool lower = character >= 'a' && character <= 'f';
                if (!digit && !lower) return false;
            }
            return true;
        }

        internal static bool Finite(double value) =>
            !double.IsNaN(value) && !double.IsInfinity(value);

        internal static bool Finite(float value) =>
            !float.IsNaN(value) && !float.IsInfinity(value);

        internal static bool SameIdentity(
            RateStudySession session,
            string studyId,
            string runId,
            string scenarioId,
            string trackerId,
            string trackerIdentitySha256,
            string modelIdentitySha256,
            long initFrameId,
            string initImageSha256)
        {
            return session != null
                && studyId == session.study_id
                && runId == session.run_id
                && scenarioId == session.scenario_id
                && trackerId == session.tracker_id
                && trackerIdentitySha256 == session.tracker_identity_sha256
                && modelIdentitySha256 == session.model_identity_sha256
                && initFrameId == session.init_frame_id
                && initImageSha256 == session.init_image_sha256;
        }
    }
}
