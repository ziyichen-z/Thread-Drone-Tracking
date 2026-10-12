using System;
using System.IO;
using UnityEngine;

namespace TetheredTracking
{
    /// <summary>
    /// The `scout-3` scouting session for the SCENE-004 benign circuit.
    ///
    /// A separate type rather than a reuse of
    /// <see cref="P1DetectScoutingSession"/>, for two independent reasons:
    /// that class pins `scenario_id` to `p1-detect-scouting` and pins the
    /// hard scene's frozen parameters (106.485 s loop, 65 m remote band), and
    /// its session root is the legacy directory. scout-3 carries its own
    /// frozen protocol and its own runtime root, and the two cannot collide.
    ///
    /// The frozen loop period is bound to the geometry artifact rather than
    /// restated here, so the session cannot drift from the circuit the
    /// envelope gates were computed on.
    /// </summary>
    [Serializable]
    internal sealed class P1Scene004ScoutingSession : IScoutingTruthSession
    {
        internal const string RuntimeSessionRoot = "p1-scene-004-scouting";
        internal const string Schema = "p1-scene-004-scouting-session/v1";
        internal const string ProfileId = "p1-scene-004-scout-3/v1";
        internal const string ExpectedWorkId = "P1-SCENE-004";
        internal const string ExpectedScenarioId = "p1-scene-004";
        internal const string FileName = "p1_scene_004_scouting_session.json";

        public string schema_version = Schema;
        public string work_id;
        public string profile_id;
        public string session_id;
        public string scenario_id;
        public bool non_measurement;
        public string gimbal_driver;
        public string scenario_config_sha256;
        public string geometry_sha256;
        public float loop_period_s;
        public float sample_hz;
        public int minimum_loops;
        public float detector_confidence_min;
        public float detector_iou_min;
        public float gating_recall_min;

        public string SessionRoot => RuntimeSessionRoot;
        public string SessionId => session_id;
        public string WorkId => work_id;
        public string ScenarioId => scenario_id;
        public string GimbalDriver => gimbal_driver;
        public string TruthSchema => P1DetectScoutingTruthWriter.TruthSchemaV2;
        public string ScenarioConfigSha256 => scenario_config_sha256;

        public string Validate()
        {
            if (schema_version != Schema)
                return "invalid_scene004_scouting_session_schema";
            if (work_id != ExpectedWorkId
                || profile_id != ProfileId
                || scenario_id != ExpectedScenarioId
                || !non_measurement
                || gimbal_driver
                    != P1DetectScoutingSession.TruthDirectedGimbalDriver)
                return "invalid_scene004_scouting_session_identity";
            if (!P1DetectScoutingSession.SafeSessionId(session_id))
                return "invalid_scene004_scouting_session_id";
            if (!RateStudyProtocol.IsSha256(scenario_config_sha256)
                || !RateStudyProtocol.IsSha256(geometry_sha256))
                return "invalid_scene004_scouting_hash";
            if (!RateStudyProtocol.Finite(loop_period_s)
                || loop_period_s <= 0f
                || !Approximately(sample_hz, 2f)
                || minimum_loops < 3
                || !Approximately(detector_confidence_min, 0.25f)
                || !Approximately(detector_iou_min, 0.30f)
                || !Approximately(gating_recall_min, 0.7f))
                return "invalid_scene004_scouting_frozen_parameter";
            return null;
        }

        internal static bool TryLoad(
            string path,
            out P1Scene004ScoutingSession session,
            out string error)
        {
            session = null;
            error = null;
            if (!File.Exists(path)) return false;
            try
            {
                session = JsonUtility.FromJson<P1Scene004ScoutingSession>(
                    File.ReadAllText(path));
            }
            catch (Exception exception)
            {
                error = "invalid_scene004_scouting_session_json:"
                    + exception.GetType().Name;
                return true;
            }
            error = session == null
                ? "invalid_scene004_scouting_session_json"
                : session.Validate();
            return true;
        }

        static bool Approximately(float left, float right) =>
            RateStudyProtocol.Finite(left)
            && Mathf.Abs(left - right) <= 1e-4f;
    }
}
