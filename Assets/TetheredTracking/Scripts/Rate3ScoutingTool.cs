using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking
{
    /// <summary>
    /// P1-M2-RATE-003 §4 three-phase scouting.
    ///
    /// RATE-002's tool selects the single first qualifying arc length from
    /// zero. RATE-003 needs three deterministic matched design points: for
    /// each ideal phase in {0, P/3, 2P/3}, the first qualifying candidate
    /// searching **forward** along arc length, wrapping once. No operator
    /// discretion anywhere in the loop, and the full candidate table —
    /// including every disqualified candidate — is published so a reviewer
    /// can see that nothing was cherry-picked.
    ///
    /// The qualification predicate is RATE-002 §3 verbatim (margin >= 0.15,
    /// nearest distractor IoU = 0 and centre distance >= one target box
    /// width), reused rather than reimplemented.
    ///
    /// Scouting projects the HOLD camera with the target parked at each
    /// candidate, so it is independent of `target.speed_mps`: one scouting
    /// slot covers both difficulties.
    /// </summary>
    public sealed class Rate3ScoutingTool : MonoBehaviour
    {
        internal const string ReportFileName = "rate3_scouting_qualification.json";
        internal const string ReportSchema = "p1-rate3-scouting/v1";
        internal const string StudyId = "P1-M2-RATE-003-B1";
        internal const string RunId = "rs3-scouting";
        internal const int PhaseCount = 3;

        [Serializable]
        internal sealed class Candidate
        {
            public int index;
            public float route_s_m;
            public NormalizedBoundingBox target_bbox_xywh_norm;
            public float frame_margin;
            public bool has_active_distractor;
            public float nearest_distractor_center_distance_px;
            public float nearest_distractor_iou;
            public bool qualified;
        }

        [Serializable]
        sealed class Report
        {
            public string schema_version = ReportSchema;
            public string study_id = StudyId;
            public string run_id = RunId;
            public string scenario_id;
            public string status;
            public float route_perimeter_m;
            public float spacing_m = 0.5f;
            public float required_margin = 0.15f;
            public float required_separation_target_widths = 1f;
            public float required_nearest_distractor_iou = 0f;
            public int active_distractor_count;
            public int expected_distractor_count = -1;
            public string validation_error;
            public float[] ideal_phase_s_m;
            public float[] selected_route_s_m;
            public int[] selected_candidate_index;
            public Candidate[] candidates;
        }

        [ContextMenu("Generate RATE-003 Three-Phase Scouting Table")]
        public void GenerateCurrentScenarioQualification()
        {
            bool qualified = GenerateAndWrite(TetheredScenarioBootstrap.Instance);
            if (qualified)
                Debug.Log(
                    "RATE-003 scouting froze three deterministic phase "
                    + "positions.");
            else
                Debug.LogError(
                    "RATE-003 scouting is INVALID_SCOUTING; no measurement "
                    + "may start.");
        }

        public bool GenerateAndWrite(TetheredScenarioBootstrap scenario)
        {
            if (scenario == null
                || scenario.Target == null
                || scenario.SensorCamera == null)
                throw new ArgumentException(
                    "A complete scenario is required.",
                    nameof(scenario));
            LoopTargetVehicle target = scenario.Target;
            Camera camera = scenario.SensorCamera;
            Vector3 originalPosition = target.transform.position;
            Quaternion originalRotation = target.transform.rotation;
            Quaternion originalCameraRotation = camera.transform.rotation;
            bool originalMotion = target.MotionEnabled;
            try
            {
                target.SetMotionEnabled(false);
                camera.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
                Renderer[] targetRenderers =
                    target.GetComponentsInChildren<Renderer>(false);
                var distractorRenderers = new List<Renderer[]>();
                foreach (RateStudyDistractor marker in
                    FindObjectsByType<RateStudyDistractor>(
                        FindObjectsInactive.Exclude))
                {
                    if (marker.transform == target.transform
                        || marker.transform.IsChildOf(target.transform)) continue;
                    Renderer[] renderers =
                        marker.GetComponentsInChildren<Renderer>(false);
                    if (renderers.Length > 0) distractorRenderers.Add(renderers);
                }

                Vector3[] route = scenario.Config.TargetRoute();
                float perimeter = RateStudyScouting.ClosedRoutePerimeter(route);
                int expectedDistractorCount =
                    scenario.Config.scene_adjustments == null
                        ? -1
                        : scenario.Config.scene_adjustments.expected_distractor_count;
                string validationError =
                    RateStudyScoutingTool.DistractorCountValidationError(
                        scenario.Config,
                        distractorRenderers.Count);
                float[] idealPhases = IdealPhases(perimeter);
                if (validationError != null)
                {
                    WriteInvalid(
                        scenario,
                        perimeter,
                        distractorRenderers.Count,
                        expectedDistractorCount,
                        validationError,
                        idealPhases,
                        Array.Empty<Candidate>());
                    return false;
                }

                float[] distances = RateStudyScouting.CandidateDistances(route);
                var candidates = new Candidate[distances.Length];
                for (int index = 0; index < distances.Length; index++)
                {
                    target.PlaceAtRouteDistance(distances[index]);
                    NormalizedBoundingBox targetBox =
                        RateStudyScouting.ProjectRenderersUnclipped(
                            camera,
                            targetRenderers);
                    var projected = new List<NormalizedBoundingBox>();
                    foreach (Renderer[] renderers in distractorRenderers)
                    {
                        NormalizedBoundingBox box =
                            RateStudyScouting.ProjectRenderersUnclipped(
                                camera,
                                renderers);
                        if (box != null) projected.Add(box);
                    }
                    RateStudyScouting.Separation separation =
                        RateStudyScouting.NearestDistractor(
                            targetBox,
                            projected,
                            scenario.Config.sensor.width,
                            scenario.Config.sensor.height);
                    candidates[index] = new Candidate
                    {
                        index = index,
                        route_s_m = distances[index],
                        target_bbox_xywh_norm = targetBox,
                        frame_margin = targetBox == null
                            ? -1f
                            : RateStudyScouting.FrameMargin(targetBox),
                        has_active_distractor = separation.HasDistractor,
                        nearest_distractor_center_distance_px =
                            separation.NearestCenterDistancePixels,
                        nearest_distractor_iou = separation.NearestIoU,
                        qualified = RateStudyScouting.Qualifies(
                            targetBox,
                            separation,
                            scenario.Config.sensor.width),
                    };
                }

                var selectedIndex = new int[PhaseCount];
                var selectedDistance = new float[PhaseCount];
                string selectionError = SelectPhases(
                    candidates,
                    idealPhases,
                    selectedIndex,
                    selectedDistance);
                if (selectionError != null)
                {
                    WriteInvalid(
                        scenario,
                        perimeter,
                        distractorRenderers.Count,
                        expectedDistractorCount,
                        selectionError,
                        idealPhases,
                        candidates);
                    return false;
                }

                var report = new Report
                {
                    scenario_id = scenario.Config.scenario_id,
                    status = "QUALIFIED",
                    route_perimeter_m = perimeter,
                    active_distractor_count = distractorRenderers.Count,
                    expected_distractor_count = expectedDistractorCount,
                    ideal_phase_s_m = idealPhases,
                    selected_route_s_m = selectedDistance,
                    selected_candidate_index = selectedIndex,
                    candidates = candidates,
                };
                AtomicFile.WriteAllText(
                    RuntimePaths.File(ReportFileName),
                    JsonUtility.ToJson(report, true) + "\n");
                return true;
            }
            finally
            {
                camera.transform.rotation = originalCameraRotation;
                target.SetMotionEnabled(originalMotion);
                target.transform.SetPositionAndRotation(
                    originalPosition,
                    originalRotation);
            }
        }

        internal static float[] IdealPhases(float perimeter)
        {
            var phases = new float[PhaseCount];
            for (int index = 0; index < PhaseCount; index++)
                phases[index] = perimeter * index / PhaseCount;
            return phases;
        }

        /// <summary>
        /// For each ideal phase, take the first qualifying candidate at or
        /// after it in arc length, wrapping once. Returns null on success,
        /// otherwise the fail-closed validation error.
        /// </summary>
        internal static string SelectPhases(
            IReadOnlyList<Candidate> candidates,
            IReadOnlyList<float> idealPhases,
            int[] selectedIndex,
            float[] selectedDistance)
        {
            if (candidates == null || candidates.Count == 0)
                return "no_scouting_candidates";
            for (int phase = 0; phase < idealPhases.Count; phase++)
            {
                int start = 0;
                while (start < candidates.Count
                    && candidates[start].route_s_m < idealPhases[phase]) start++;
                int chosen = -1;
                for (int step = 0; step < candidates.Count; step++)
                {
                    int index = (start + step) % candidates.Count;
                    if (!candidates[index].qualified) continue;
                    chosen = index;
                    break;
                }
                if (chosen < 0) return "no_qualified_candidate_for_phase";
                selectedIndex[phase] = chosen;
                selectedDistance[phase] = candidates[chosen].route_s_m;
            }
            for (int left = 0; left < selectedIndex.Length; left++)
            {
                for (int right = left + 1; right < selectedIndex.Length; right++)
                {
                    if (selectedIndex[left] == selectedIndex[right])
                        return "phase_collision";
                }
            }
            return null;
        }

        void WriteInvalid(
            TetheredScenarioBootstrap scenario,
            float perimeter,
            int activeDistractorCount,
            int expectedDistractorCount,
            string validationError,
            float[] idealPhases,
            Candidate[] candidates)
        {
            var report = new Report
            {
                scenario_id = scenario.Config.scenario_id,
                status = "INVALID_SCOUTING",
                route_perimeter_m = perimeter,
                active_distractor_count = activeDistractorCount,
                expected_distractor_count = expectedDistractorCount,
                validation_error = validationError,
                ideal_phase_s_m = idealPhases,
                selected_route_s_m = Array.Empty<float>(),
                selected_candidate_index = Array.Empty<int>(),
                candidates = candidates,
            };
            AtomicFile.WriteAllText(
                RuntimePaths.File(ReportFileName),
                JsonUtility.ToJson(report, true) + "\n");
        }
    }
}
