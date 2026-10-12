using System;
using System.IO;
using System.Text.RegularExpressions;
using UnityEngine;

namespace TetheredTracking
{
    internal enum QualificationFrameDisposition
    {
        Ordinary,
        ResetAndHold,
        Hold,
        ResetAndMeasure,
        Measure,
    }

    [Serializable]
    internal sealed class QualificationMetricsOrigin
    {
        public string schema_version =
            QualificationReleaseGate.MetricsOriginSchema;
        public string protocol_id;
        public string run_id;
        public string scenario_id;
        public string command_id;
        public string release_command_sha256;
        public string active_marker_sha256;
        public long release_frame_id;
        public double release_monotonic_s;
        public double release_simulation_s;
    }

    internal sealed class QualificationReleaseGate
    {
        [Serializable]
        sealed class ActiveMarker
        {
            public string schema_version;
            public string protocol_id;
            public string run_id;
            public string scenario_id;
            public string command_id;
            public string manifest_sha256;
            public string ready_sha256;
            public string release_command_sha256;
            public string command_relative_path;
            public double not_before_capture_monotonic_s;
        }

        [Serializable]
        sealed class ReleaseCommand
        {
            public string schema_version;
            public string protocol_id;
            public string run_id;
            public string scenario_id;
            public string command_id;
            public string manifest_sha256;
            public string ready_sha256;
            public double issued_unix_s;
            public double not_before_capture_monotonic_s;
        }

        internal const string ActiveSchema =
            "p1-detect-qualification-active/v1";
        internal const string CommandSchema =
            "p1-detect-qualification-release-command/v1";
        internal const string ProtocolId =
            "host-monotonic-first-live-frame/v1";
        internal const string MetricsOriginSchema =
            "p1-detect-qualification-metrics-origin/v1";
        internal const string ActivePointerFile =
            "p1_detect_qualification_release.json";

        static readonly Regex RunIdPattern = new(
            "^p1-detect-001-qual-[1-9][0-9]*$",
            RegexOptions.CultureInvariant);

        readonly string runtimeRoot;
        readonly string expectedScenarioId;
        readonly double sessionStartedUnixSeconds;
        readonly double sessionStartedMonotonicSeconds;
        bool armed;
        bool released;
        bool resetIssued;
        string ignoredActiveMarkerSha256;
        ActiveMarker marker;
        string activeMarkerSha256;
        long releaseFrameId = -1;
        double releaseMonotonicSeconds;
        double releaseSimulationSeconds;

        internal QualificationReleaseGate(
            string configuredRuntimeRoot,
            string scenarioId,
            double? configuredSessionStartedUnixSeconds = null,
            double? configuredSessionStartedMonotonicSeconds = null)
        {
            runtimeRoot = Path.GetFullPath(configuredRuntimeRoot);
            expectedScenarioId = scenarioId;
            sessionStartedUnixSeconds =
                configuredSessionStartedUnixSeconds
                ?? DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;
            sessionStartedMonotonicSeconds =
                configuredSessionStartedMonotonicSeconds
                ?? SensorFrameWriter.HostMonotonicSeconds();
            if (!RateStudyProtocol.Finite(sessionStartedUnixSeconds)
                || sessionStartedUnixSeconds < 0.0
                || !RateStudyProtocol.Finite(
                    sessionStartedMonotonicSeconds)
                || sessionStartedMonotonicSeconds < 0.0)
                throw new ArgumentOutOfRangeException(
                    nameof(configuredSessionStartedMonotonicSeconds),
                    "qualification evaluator session clocks must be finite "
                    + "and non-negative");
        }

        internal QualificationFrameDisposition EvaluateFrame(
            SensorFrameInfo frame)
        {
            if (!armed && !TryArm())
                return QualificationFrameDisposition.Ordinary;
            bool reset = !resetIssued;
            resetIssued = true;
            if (!released)
            {
                if (frame.CaptureMonotonicSeconds
                    < marker.not_before_capture_monotonic_s)
                {
                    return reset
                        ? QualificationFrameDisposition.ResetAndHold
                        : QualificationFrameDisposition.Hold;
                }
                released = true;
                releaseFrameId = frame.FrameId;
                releaseMonotonicSeconds = frame.CaptureMonotonicSeconds;
                releaseSimulationSeconds = frame.SimulationTimeSeconds;
                return reset
                    ? QualificationFrameDisposition.ResetAndMeasure
                    : QualificationFrameDisposition.Measure;
            }
            return frame.FrameId >= releaseFrameId
                ? QualificationFrameDisposition.Measure
                : QualificationFrameDisposition.Hold;
        }

        internal bool AllowsObservation(long frameId)
        {
            if (!armed && !TryArm()) return true;
            return released && frameId >= releaseFrameId;
        }

        internal QualificationMetricsOrigin MetricsOrigin =>
            !released
                ? null
                : new QualificationMetricsOrigin
                {
                    protocol_id = ProtocolId,
                    run_id = marker.run_id,
                    scenario_id = marker.scenario_id,
                    command_id = marker.command_id,
                    release_command_sha256 =
                        marker.release_command_sha256,
                    active_marker_sha256 = activeMarkerSha256,
                    release_frame_id = releaseFrameId,
                    release_monotonic_s = releaseMonotonicSeconds,
                    release_simulation_s = releaseSimulationSeconds,
                };

        bool TryArm()
        {
            string activePath = Path.Combine(
                runtimeRoot,
                ActivePointerFile);
            if (!File.Exists(activePath)) return false;
            byte[] activeBytes = File.ReadAllBytes(activePath);
            string loadedActiveSha256 =
                RateStudyProtocol.Sha256(activeBytes);
            if (loadedActiveSha256 == ignoredActiveMarkerSha256)
                return false;
            ActiveMarker loaded;
            try
            {
                loaded = JsonUtility.FromJson<ActiveMarker>(
                    System.Text.Encoding.UTF8.GetString(activeBytes));
            }
            catch (Exception)
            {
                return IgnoreMarker(loadedActiveSha256);
            }
            if (!MarkerCanTargetThisSession(loaded))
                return IgnoreMarker(loadedActiveSha256);
            string expectedRelative =
                $"runs/{loaded.run_id}/qualification-release-command.json";
            if (loaded.command_relative_path != expectedRelative)
                return IgnoreMarker(loadedActiveSha256);
            string commandPath = Path.Combine(
                runtimeRoot,
                "runs",
                loaded.run_id,
                "qualification-release-command.json");
            if (!File.Exists(commandPath))
                return IgnoreMarker(loadedActiveSha256);
            byte[] commandBytes = File.ReadAllBytes(commandPath);
            ReleaseCommand command;
            try
            {
                command = JsonUtility.FromJson<ReleaseCommand>(
                    System.Text.Encoding.UTF8.GetString(commandBytes));
            }
            catch (Exception)
            {
                return IgnoreMarker(loadedActiveSha256);
            }
            if (!CommandWasIssuedForThisSession(command))
                return IgnoreMarker(loadedActiveSha256);
            ValidateMarker(loaded);
            if (RateStudyProtocol.Sha256(commandBytes)
                != loaded.release_command_sha256)
                throw new InvalidOperationException(
                    "qualification_release_command_hash_mismatch");
            ValidateCommand(command, loaded);
            ValidateBoundArtifact(
                Path.Combine(
                    runtimeRoot,
                    "runs",
                    loaded.run_id,
                    "manifest.json"),
                loaded.manifest_sha256,
                "qualification_manifest_hash_mismatch");
            ValidateBoundArtifact(
                Path.Combine(
                    runtimeRoot,
                    "runs",
                    loaded.run_id,
                    "qualification-release-ready.json"),
                loaded.ready_sha256,
                "qualification_ready_hash_mismatch");
            marker = loaded;
            activeMarkerSha256 = loadedActiveSha256;
            armed = true;
            return true;
        }

        bool MarkerCanTargetThisSession(ActiveMarker value) =>
            value != null
            && value.schema_version == ActiveSchema
            && value.protocol_id == ProtocolId
            && RunIdPattern.IsMatch(value.run_id ?? "")
            && value.scenario_id == expectedScenarioId
            && value.scenario_id == "p1-scene-004"
            && RateStudyProtocol.Finite(
                value.not_before_capture_monotonic_s)
            && value.not_before_capture_monotonic_s >= 0.0;

        bool CommandWasIssuedForThisSession(ReleaseCommand command) =>
            command != null
            && RateStudyProtocol.Finite(command.issued_unix_s)
            && command.issued_unix_s > sessionStartedUnixSeconds
            && RateStudyProtocol.Finite(
                command.not_before_capture_monotonic_s)
            && command.not_before_capture_monotonic_s
                > sessionStartedMonotonicSeconds;

        bool IgnoreMarker(string sha256)
        {
            ignoredActiveMarkerSha256 = sha256;
            return false;
        }

        void ValidateMarker(ActiveMarker value)
        {
            if (value == null
                || value.schema_version != ActiveSchema
                || value.protocol_id != ProtocolId)
                throw new InvalidOperationException(
                    "qualification_active_marker_identity_invalid");
            if (!RunIdPattern.IsMatch(value.run_id ?? "")
                || value.scenario_id != expectedScenarioId
                || value.scenario_id != "p1-scene-004"
                || string.IsNullOrWhiteSpace(value.command_id))
                throw new InvalidOperationException(
                    "qualification_active_marker_run_invalid");
            if (!RateStudyProtocol.IsSha256(value.manifest_sha256)
                || !RateStudyProtocol.IsSha256(value.ready_sha256)
                || !RateStudyProtocol.IsSha256(
                    value.release_command_sha256)
                || !RateStudyProtocol.Finite(
                    value.not_before_capture_monotonic_s)
                || value.not_before_capture_monotonic_s < 0.0)
                throw new InvalidOperationException(
                    "qualification_active_marker_fields_invalid");
        }

        static void ValidateCommand(
            ReleaseCommand command,
            ActiveMarker active)
        {
            if (command == null
                || command.schema_version != CommandSchema
                || command.protocol_id != ProtocolId
                || command.run_id != active.run_id
                || command.scenario_id != active.scenario_id
                || command.command_id != active.command_id
                || command.manifest_sha256 != active.manifest_sha256
                || command.ready_sha256 != active.ready_sha256
                || !RateStudyProtocol.Finite(command.issued_unix_s)
                || command.issued_unix_s < 0.0
                || !RateStudyProtocol.Finite(
                    command.not_before_capture_monotonic_s)
                || command.not_before_capture_monotonic_s
                    != active.not_before_capture_monotonic_s)
                throw new InvalidOperationException(
                    "qualification_release_command_identity_invalid");
        }

        static void ValidateBoundArtifact(
            string path,
            string expectedSha256,
            string error)
        {
            if (!File.Exists(path)
                || RateStudyProtocol.Sha256(File.ReadAllBytes(path))
                    != expectedSha256)
                throw new InvalidOperationException(error);
        }
    }
}
