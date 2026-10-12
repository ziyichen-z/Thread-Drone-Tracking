using System;
using System.IO;
using UnityEngine;

namespace TetheredTracking
{
    /// <summary>
    /// What the shared truth writer needs from a scouting session.
    ///
    /// Introduced to close Sonnet round 1 note 1: the writer used to hardcode
    /// its sidecar directory to the literal `p1-detect-scouting`, while the
    /// scout-3 analyzer reads `p1-scene-004-scouting`. Reusing the writer for
    /// a second profile would then have written every sidecar where nothing
    /// reads it, and every tick would have come back as a missing pair —
    /// tripping `CAPTURE_INCOMPLETE` no matter how the detector performed.
    /// The directory is now derived from the session, so a new profile cannot
    /// silently inherit another profile's path.
    /// </summary>
    internal interface IScoutingTruthSession
    {
        /// <summary>Runtime subdirectory that owns this profile's sessions.</summary>
        string SessionRoot { get; }
        string SessionId { get; }
        string WorkId { get; }
        string ScenarioId { get; }
        string GimbalDriver { get; }
        string TruthSchema { get; }
        string ScenarioConfigSha256 { get; }

        string Validate();
    }

    [Serializable]
    internal sealed class P1DetectScoutingSession : IScoutingTruthSession
    {
        internal const string RuntimeSessionRoot = "p1-detect-scouting";

        internal const string TruthDirectedGimbalDriver =
            "truth_directed_scouting";

        public string schema_version = "p1-detect-scouting-session/v1";
        public string work_id;
        public string session_id;
        public string scenario_id;
        public bool non_measurement;
        public string gimbal_driver;
        public string scenario_config_sha256;
        public float loop_duration_s;
        public float sample_hz;
        public float remote_slant_range_min_m;
        public float detector_confidence_min;
        public float detector_iou_min;

        public string SessionRoot => RuntimeSessionRoot;
        public string SessionId => session_id;
        public string WorkId => work_id;
        public string ScenarioId => scenario_id;
        public string GimbalDriver => gimbal_driver;
        public string TruthSchema => P1DetectScoutingTruthWriter.TruthSchemaV2;
        public string ScenarioConfigSha256 => scenario_config_sha256;

        public string Validate()
        {
            if (schema_version != "p1-detect-scouting-session/v1")
                return "invalid_scouting_session_schema";
            if (work_id != "P1-DETECT-001"
                || scenario_id != "p1-detect-scouting"
                || !non_measurement
                || gimbal_driver != TruthDirectedGimbalDriver)
                return "invalid_scouting_session_identity";
            if (!SafeSessionId(session_id))
                return "invalid_scouting_session_id";
            if (!RateStudyProtocol.IsSha256(scenario_config_sha256))
                return "invalid_scouting_config_hash";
            if (!Approximately(loop_duration_s, 106.485f)
                || !Approximately(sample_hz, 2f)
                || !Approximately(remote_slant_range_min_m, 65f)
                || !Approximately(detector_confidence_min, 0.25f)
                || !Approximately(detector_iou_min, 0.30f))
                return "invalid_scouting_frozen_parameter";
            return null;
        }

        internal static bool TryLoad(
            string path,
            out P1DetectScoutingSession session,
            out string error)
        {
            session = null;
            error = null;
            if (!File.Exists(path)) return false;
            try
            {
                session = JsonUtility.FromJson<P1DetectScoutingSession>(
                    File.ReadAllText(path));
            }
            catch (Exception exception)
            {
                error = "invalid_scouting_session_json:"
                    + exception.GetType().Name;
                return true;
            }
            error = session == null
                ? "invalid_scouting_session_json"
                : session.Validate();
            return true;
        }

        internal static bool SafeSessionId(string value)
        {
            if (string.IsNullOrEmpty(value) || value.Length > 48) return false;
            for (int index = 0; index < value.Length; index++)
            {
                char character = value[index];
                bool lower = character >= 'a' && character <= 'z';
                bool digit = character >= '0' && character <= '9';
                if (!lower && !digit && character != '-') return false;
            }
            return value[0] >= 'a' && value[0] <= 'z';
        }

        static bool Approximately(float left, float right) =>
            RateStudyProtocol.Finite(left)
            && Mathf.Abs(left - right) <= 1e-4f;
    }

    [Serializable]
    internal sealed class P1DetectScoutingDistractorTruth
    {
        public string distractor_id;
        public NormalizedBoundingBox bbox_xywh_norm;
        public string box_status;
    }

    [Serializable]
    internal sealed class P1DetectScoutingTruthDocument
    {
        public string schema_version =
            P1DetectScoutingTruthWriter.TruthSchemaV2;
        public string work_id;
        public string session_id;
        public string scenario_id;
        public string gimbal_driver =
            P1DetectScoutingSession.TruthDirectedGimbalDriver;
        public long frame_id;
        public float simulation_time_s;
        public string target_track_id;
        public bool target_visible;
        public float target_visible_sample_fraction;
        public float target_slant_range_m;
        public NormalizedBoundingBox target_bbox_xywh_norm;
        public string target_box_status;
        public P1DetectScoutingDistractorTruth[] distractors;
    }

    internal sealed class P1DetectScoutingTruthWriter
    {
        const float BoundaryRoundoffTolerance = 1e-5f;

        internal const string TruthSchemaV1 = "p1-detect-scouting-truth/v1";
        internal const string TruthSchemaV2 = "p1-detect-scouting-truth/v2";

        /// <summary>Box present and canonicalisable.</summary>
        internal const string BoxStatusValid = "VALID";

        /// <summary>
        /// The target is visible to the evaluator but its box cannot be
        /// projected into the frame. Before v2 this threw, which left no
        /// sidecar on disk at all: the offline analyzer then had to score the
        /// tick as a detector miss (`MISSING_IMAGE_TRUTH_PAIR`), so a
        /// pointing/geometry fact was laundered into a recall number.
        /// scout-1 lost 18 of 45 samples this way. Under BC2 the document is
        /// still written, carries this status, and is accounted for in its
        /// own class outside the gating denominator.
        /// </summary>
        internal const string BoxStatusUnprojectable = "TARGET_VISIBLE_UNPROJECTABLE";

        /// <summary>No box was offered because the target is not visible.</summary>
        internal const string BoxStatusNotVisible = "TARGET_NOT_VISIBLE";

        /// <summary>
        /// A distractor has no box. Unlike the target, this is the ordinary
        /// case — a parked vehicle is simply outside the frame most of the
        /// time — so it does not borrow the target-shaped
        /// `TARGET_VISIBLE_UNPROJECTABLE` label (Sonnet round 1 note 3).
        /// Consumers gate on `!= VALID`, so the distinction is descriptive.
        /// </summary>
        internal const string BoxStatusNotInFrame = "NOT_IN_FRAME";

        readonly IScoutingTruthSession session;
        readonly string truthDirectory;

        internal P1DetectScoutingTruthWriter(
            IScoutingTruthSession session,
            string runtimeRoot)
        {
            this.session = session
                ?? throw new ArgumentNullException(nameof(session));
            string error = session.Validate();
            if (error != null) throw new InvalidOperationException(error);
            if (string.IsNullOrWhiteSpace(session.SessionRoot))
                throw new InvalidOperationException(
                    "invalid_scouting_session_root");
            // Derived from the session, never a literal: see
            // IScoutingTruthSession's remarks.
            truthDirectory = Path.Combine(
                runtimeRoot,
                session.SessionRoot,
                session.SessionId,
                "truth");
            Directory.CreateDirectory(truthDirectory);
        }

        internal string TruthDirectory => truthDirectory;

        internal void Write(P1DetectScoutingTruthDocument document)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));
            if (document.schema_version != session.TruthSchema
                || document.work_id != session.WorkId
                || document.session_id != session.SessionId
                || document.scenario_id != session.ScenarioId
                || document.gimbal_driver != session.GimbalDriver
                || document.frame_id < 0
                || !RateStudyProtocol.Finite(document.simulation_time_s)
                || document.simulation_time_s < 0f
                || !RateStudyProtocol.Finite(document.target_slant_range_m)
                || document.target_slant_range_m < 0f
                || !RateStudyProtocol.Finite(
                    document.target_visible_sample_fraction)
                || document.target_visible_sample_fraction < 0f
                || document.target_visible_sample_fraction > 1f
                || string.IsNullOrWhiteSpace(document.target_track_id)
                || document.distractors == null)
                throw new InvalidOperationException("invalid_scouting_truth");
            if (document.target_bbox_xywh_norm != null)
            {
                if (TryCanonicalizeBox(
                    document.target_bbox_xywh_norm,
                    out NormalizedBoundingBox canonicalTarget))
                {
                    document.target_bbox_xywh_norm = canonicalTarget;
                    document.target_box_status = BoxStatusValid;
                }
                else
                {
                    // BC2: never drop the document. An unprojectable box is a
                    // pointing fact, not a detector failure, so it is recorded
                    // explicitly instead of vanishing into a missing file.
                    document.target_bbox_xywh_norm = null;
                    document.target_box_status = BoxStatusUnprojectable;
                }
            }
            else
            {
                document.target_box_status = document.target_visible
                    ? BoxStatusUnprojectable
                    : BoxStatusNotVisible;
            }
            foreach (P1DetectScoutingDistractorTruth distractor
                in document.distractors)
            {
                if (distractor == null
                    || string.IsNullOrWhiteSpace(distractor.distractor_id))
                    throw new InvalidOperationException(
                        "invalid_scouting_distractor_truth");
                if (distractor.bbox_xywh_norm != null
                    && TryCanonicalizeBox(
                        distractor.bbox_xywh_norm,
                        out NormalizedBoundingBox canonicalDistractor))
                {
                    distractor.bbox_xywh_norm = canonicalDistractor;
                    distractor.box_status = BoxStatusValid;
                }
                else
                {
                    distractor.bbox_xywh_norm = null;
                    distractor.box_status = BoxStatusNotInFrame;
                }
            }

            string destination = Path.Combine(
                truthDirectory,
                "frame_" + document.frame_id.ToString("D10") + ".json");
            WriteCreateOnce(
                destination,
                SerializeWithExplicitNullBoxes(document) + "\n");
        }

        static string SerializeWithExplicitNullBoxes(
            P1DetectScoutingTruthDocument document)
        {
            string json = JsonUtility.ToJson(document, true);
            json = ReplaceZeroBoxObjectsWithNull(
                json,
                "target_bbox_xywh_norm");
            return ReplaceZeroBoxObjectsWithNull(json, "bbox_xywh_norm");
        }

        static string ReplaceZeroBoxObjectsWithNull(
            string json,
            string propertyName)
        {
            string token = "\"" + propertyName + "\"";
            int searchFrom = 0;
            while (true)
            {
                int property = json.IndexOf(
                    token,
                    searchFrom,
                    StringComparison.Ordinal);
                if (property < 0) return json;
                int colon = json.IndexOf(':', property + token.Length);
                if (colon < 0) return json;
                int objectStart = colon + 1;
                while (objectStart < json.Length
                    && char.IsWhiteSpace(json[objectStart]))
                    objectStart++;
                if (objectStart >= json.Length || json[objectStart] != '{')
                {
                    searchFrom = objectStart + 1;
                    continue;
                }
                int depth = 0;
                int objectEnd = -1;
                for (int index = objectStart; index < json.Length; index++)
                {
                    if (json[index] == '{') depth++;
                    else if (json[index] == '}')
                    {
                        depth--;
                        if (depth == 0)
                        {
                            objectEnd = index;
                            break;
                        }
                    }
                }
                if (objectEnd < 0) return json;
                string objectJson = json.Substring(
                    objectStart,
                    objectEnd - objectStart + 1);
                NormalizedBoundingBox box =
                    JsonUtility.FromJson<NormalizedBoundingBox>(objectJson);
                if (box != null
                    && box.x == 0f
                    && box.y == 0f
                    && box.width == 0f
                    && box.height == 0f)
                {
                    json = json.Substring(0, objectStart)
                        + "null"
                        + json.Substring(objectEnd + 1);
                    searchFrom = objectStart + 4;
                }
                else
                {
                    searchFrom = objectEnd + 1;
                }
            }
        }

        internal static void WriteCreateOnce(string destination, string contents)
        {
            string directory = Path.GetDirectoryName(destination);
            if (string.IsNullOrEmpty(directory))
                throw new ArgumentException(
                    "Destination needs a directory.",
                    nameof(destination));
            Directory.CreateDirectory(directory);
            string temporary = Path.Combine(
                directory,
                "." + Path.GetFileName(destination) + "."
                + Guid.NewGuid() + ".tmp");
            try
            {
                File.WriteAllText(temporary, contents);
                File.Move(temporary, destination);
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
        }

        static bool ValidBox(NormalizedBoundingBox box)
        {
            return box != null
                && RateStudyProtocol.Finite(box.x)
                && RateStudyProtocol.Finite(box.y)
                && RateStudyProtocol.Finite(box.width)
                && RateStudyProtocol.Finite(box.height)
                && box.x >= 0f
                && box.y >= 0f
                && box.width > 0f
                && box.height > 0f
                && box.x + box.width <= 1f
                && box.y + box.height <= 1f;
        }

        static bool TryCanonicalizeBox(
            NormalizedBoundingBox box,
            out NormalizedBoundingBox canonical)
        {
            canonical = null;
            if (box == null
                || !RateStudyProtocol.Finite(box.x)
                || !RateStudyProtocol.Finite(box.y)
                || !RateStudyProtocol.Finite(box.width)
                || !RateStudyProtocol.Finite(box.height)
                || box.x < 0f
                || box.y < 0f
                || box.x > 1f
                || box.y > 1f
                || box.width <= 0f
                || box.height <= 0f)
                return false;
            float right = box.x + box.width;
            float bottom = box.y + box.height;
            if (!RateStudyProtocol.Finite(right)
                || !RateStudyProtocol.Finite(bottom)
                || right > 1f + BoundaryRoundoffTolerance
                || bottom > 1f + BoundaryRoundoffTolerance)
                return false;
            canonical = new NormalizedBoundingBox
            {
                x = box.x,
                y = box.y,
                width = Mathf.Min(box.width, 1f - box.x),
                height = Mathf.Min(box.height, 1f - box.y),
            };
            return ValidBox(canonical);
        }
    }

    internal sealed class P1DetectScoutingGimbalDriver
    {
        TetheredGimbal gimbal;
        Transform target;

        internal bool ExternalCommandReceiverDisabled { get; private set; }

        internal void Configure(
            IScoutingTruthSession session,
            TetheredGimbal configuredGimbal,
            Transform configuredTarget,
            Behaviour externalCommandReceiver)
        {
            if (session == null || session.Validate() != null)
                throw new InvalidOperationException(
                    "invalid_truth_directed_scouting_session");
            if (configuredGimbal == null || configuredTarget == null)
                throw new InvalidOperationException(
                    "missing_truth_directed_scouting_plant");

            gimbal = configuredGimbal;
            target = configuredTarget;
            if (externalCommandReceiver != null)
            {
                externalCommandReceiver.enabled = false;
                ExternalCommandReceiverDisabled = true;
                Debug.Log(
                    "P1-DETECT-001 truth_directed_scouting active; "
                    + "external GimbalCommandReceiver disabled.");
            }
            else
            {
                Debug.Log(
                    "P1-DETECT-001 truth_directed_scouting active; "
                    + "external GimbalCommandReceiver absent.");
            }
            UpdateTarget();
        }

        internal void UpdateTarget()
        {
            if (gimbal == null || target == null)
                throw new InvalidOperationException(
                    "truth_directed_scouting_not_configured");
            gimbal.LookAtWorld(target.position);
        }
    }
}
