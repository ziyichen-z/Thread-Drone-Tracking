using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking
{
    public sealed class RateStudyScoutingTool : MonoBehaviour
    {
        [Serializable]
        sealed class Candidate
        {
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
            public string schema_version = "p1-rate2-scouting/v1";
            public string scenario_id;
            public string status;
            public float route_perimeter_m;
            public float spacing_m = 0.5f;
            public float required_margin = 0.15f;
            public float required_separation_target_widths = 1f;
            public int active_distractor_count;
            public int expected_distractor_count = -1;
            public string validation_error;
            public float selected_route_s_m = -1f;
            public Candidate[] candidates;
        }

        [ContextMenu("Generate RATE-002 Scouting Qualification")]
        public void GenerateCurrentScenarioQualification()
        {
            bool qualified = GenerateAndWrite(TetheredScenarioBootstrap.Instance);
            if (qualified)
                Debug.Log("RATE-002 scouting selected the minimum qualifying route distance.");
            else
                Debug.LogError("RATE-002 scouting found no qualifying route position.");
        }

        public bool GenerateAndWrite(TetheredScenarioBootstrap scenario)
        {
            if (scenario == null || scenario.Target == null || scenario.SensorCamera == null)
                throw new ArgumentException("A complete scenario is required.", nameof(scenario));
            LoopTargetVehicle target = scenario.Target;
            Camera camera = scenario.SensorCamera;
            Vector3 originalPosition = target.transform.position;
            Quaternion originalRotation = target.transform.rotation;
            Quaternion originalCameraRotation = camera.transform.rotation;
            bool originalMotion = target.MotionEnabled;
            bool selectedApplied = false;
            try
            {
                target.SetMotionEnabled(false);
                camera.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
                Renderer[] targetRenderers = target.GetComponentsInChildren<Renderer>(false);
                RateStudyDistractor[] markers =
                    FindObjectsByType<RateStudyDistractor>(FindObjectsInactive.Exclude);
                var distractorRenderers = new List<Renderer[]>();
                foreach (RateStudyDistractor marker in markers)
                {
                    if (marker.transform == target.transform
                        || marker.transform.IsChildOf(target.transform)) continue;
                    Renderer[] renderers = marker.GetComponentsInChildren<Renderer>(false);
                    if (renderers.Length > 0) distractorRenderers.Add(renderers);
                }

                Vector3[] route = scenario.Config.TargetRoute();
                float perimeter = RateStudyScouting.ClosedRoutePerimeter(route);
                int expectedDistractorCount =
                    scenario.Config.scene_adjustments == null
                        ? -1
                        : scenario.Config.scene_adjustments.expected_distractor_count;
                string distractorValidationError = DistractorCountValidationError(
                    scenario.Config,
                    distractorRenderers.Count);
                if (distractorValidationError != null)
                {
                    var invalidReport = new Report
                    {
                        scenario_id = scenario.Config.scenario_id,
                        status = "INVALID_SCOUTING",
                        route_perimeter_m = perimeter,
                        active_distractor_count = distractorRenderers.Count,
                        expected_distractor_count = expectedDistractorCount,
                        validation_error = distractorValidationError,
                        candidates = Array.Empty<Candidate>(),
                    };
                    AtomicFile.WriteAllText(
                        RuntimePaths.File("scouting_qualification.json"),
                        JsonUtility.ToJson(invalidReport, true) + "\n");
                    return false;
                }
                float[] distances = RateStudyScouting.CandidateDistances(route);
                var candidates = new Candidate[distances.Length];
                float selected = -1f;
                for (int index = 0; index < distances.Length; index++)
                {
                    float distance = distances[index];
                    target.PlaceAtRouteDistance(distance);
                    NormalizedBoundingBox targetBox =
                        RateStudyScouting.ProjectRenderersUnclipped(camera, targetRenderers);
                    var projectedDistractors = new List<NormalizedBoundingBox>();
                    foreach (Renderer[] renderers in distractorRenderers)
                    {
                        NormalizedBoundingBox box =
                            RateStudyScouting.ProjectRenderersUnclipped(camera, renderers);
                        if (box != null) projectedDistractors.Add(box);
                    }
                    RateStudyScouting.Separation separation =
                        RateStudyScouting.NearestDistractor(
                            targetBox,
                            projectedDistractors,
                            scenario.Config.sensor.width,
                            scenario.Config.sensor.height);
                    bool qualified = RateStudyScouting.Qualifies(
                        targetBox,
                        separation,
                        scenario.Config.sensor.width);
                    if (qualified && selected < 0f) selected = distance;
                    candidates[index] = new Candidate
                    {
                        route_s_m = distance,
                        target_bbox_xywh_norm = targetBox,
                        frame_margin = targetBox == null
                            ? -1f
                            : RateStudyScouting.FrameMargin(targetBox),
                        has_active_distractor = separation.HasDistractor,
                        nearest_distractor_center_distance_px =
                            separation.NearestCenterDistancePixels,
                        nearest_distractor_iou = separation.NearestIoU,
                        qualified = qualified,
                    };
                }

                var report = new Report
                {
                    scenario_id = scenario.Config.scenario_id,
                    status = selected < 0f ? "INVALID_SCOUTING" : "QUALIFIED",
                    route_perimeter_m = perimeter,
                    active_distractor_count = distractorRenderers.Count,
                    expected_distractor_count = expectedDistractorCount,
                    selected_route_s_m = selected,
                    candidates = candidates,
                };
                AtomicFile.WriteAllText(
                    RuntimePaths.File("scouting_qualification.json"),
                    JsonUtility.ToJson(report, true) + "\n");
                if (selected < 0f) return false;
                target.PlaceAtRouteDistance(selected);
                selectedApplied = true;
                return true;
            }
            finally
            {
                camera.transform.rotation = originalCameraRotation;
                target.SetMotionEnabled(originalMotion);
                if (!selectedApplied)
                    target.transform.SetPositionAndRotation(originalPosition, originalRotation);
            }
        }

        internal static string DistractorCountValidationError(
            ScenarioConfig config,
            int activeDistractorCount)
        {
            if (config == null) throw new ArgumentNullException(nameof(config));
            int expected = config.scene_adjustments == null
                ? -1
                : config.scene_adjustments.expected_distractor_count;
            return expected >= 0 && activeDistractorCount != expected
                ? "active_distractor_count_mismatch"
                : null;
        }
    }
}
