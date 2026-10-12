using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TetheredTracking.Editor
{
    /// <summary>
    /// SCENE-004 scene deconfliction evidence.
    ///
    /// The SCENE-001/002 generator is hardwired to `scenario.default.json`
    /// and asserts exactly three baseline corridor violations, so it cannot
    /// serve this circuit. This generator runs the same audit machinery
    /// against the SCENE-004 scenario and additionally surveys the parked
    /// vehicles near the circuit, which is what the distractor selection
    /// needs (a distractor has to be close enough to appear in frame, not
    /// merely marked).
    ///
    /// It is intentionally free of expected-count assertions: the before
    /// state is an observation, and only the after state is a gate.
    /// </summary>
    public static class P1Scene004SceneEvidenceGenerator
    {
        [Serializable]
        sealed class VehicleSurveyEntry
        {
            public string name;
            public string canonical_name;
            public float x_m;
            public float z_m;
            public float distance_to_circuit_m;
            public float distance_to_anchor_m;
        }

        [Serializable]
        sealed class SceneSurvey
        {
            public string schema_version = "p1-scene-004-scene-survey/v1";
            public string work_id = "P1-SCENE-004";
            public string scenario_id;
            public string scenario_sha256;
            public int before_violation_count;
            public int after_violation_count;
            public string[] before_violating_vehicles;
            public int audited_vehicle_count;
            public int expected_distractor_count;
            public int marked_distractor_count;
            public VehicleSurveyEntry[] nearby_vehicles;
        }

        const string ScenePath =
            "Assets/SimplePoly City - Low Poly Assets/Demo/"
            + "SimplePoly City - Low Poly Assets_Demo Scene.unity";
        const float SurveyRadiusM = 40f;

        public static void Generate()
        {
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            string scenarioPath = RuntimePaths.ProjectFile(
                "config",
                "scenario.p1-scene-004.json");
            byte[] scenarioBytes = File.ReadAllBytes(scenarioPath);
            ScenarioConfig scenario = ScenarioConfig.FromJsonStrict(
                File.ReadAllText(scenarioPath));
            Vector3[] route = scenario.TargetRoute();
            Vector3 anchor = scenario.anchor_world_m.Value;

            IReadOnlyList<Transform> roots =
                SceneVehicleAdjustmentApplier.FindSceneVehicleRoots();
            RouteCorridorAuditReport before = RouteCorridorAuditor.Audit(
                scenario.scenario_id + "-before-adjustments",
                route,
                scenario.scene_adjustments.route_corridor,
                roots);

            VehicleSurveyEntry[] survey = roots
                .Select(root => new VehicleSurveyEntry
                {
                    name = root.name,
                    canonical_name =
                        SceneVehicleAdjustmentApplier.CanonicalPrefabName(root.name),
                    x_m = root.position.x,
                    z_m = root.position.z,
                    distance_to_circuit_m = DistanceToRoute(root.position, route),
                    distance_to_anchor_m = Vector2.Distance(
                        new Vector2(root.position.x, root.position.z),
                        new Vector2(anchor.x, anchor.z)),
                })
                .Where(entry => entry.distance_to_circuit_m <= SurveyRadiusM)
                .OrderBy(entry => entry.distance_to_circuit_m)
                .ToArray();

            SceneVehicleAdjustmentApplier.Apply(scenario.scene_adjustments, roots);
            RouteCorridorAuditReport after = RouteCorridorAuditor.Audit(
                scenario.scenario_id + "-after-adjustments",
                route,
                scenario.scene_adjustments.route_corridor,
                roots);

            int marked = roots.Count(
                root => root != null
                    && root.GetComponent<RateStudyDistractor>() != null);
            var document = new SceneSurvey
            {
                scenario_id = scenario.scenario_id,
                scenario_sha256 =
                    P1Scene004AnchorPlacementContractLoader.Sha256(scenarioBytes),
                before_violation_count = before.violation_count,
                after_violation_count = after.violation_count,
                before_violating_vehicles = before.violations == null
                    ? Array.Empty<string>()
                    : before.violations
                        .Select(item => item.scene_object_name)
                        .Distinct(StringComparer.Ordinal)
                        .OrderBy(item => item, StringComparer.Ordinal)
                        .ToArray(),
                audited_vehicle_count = after.audited_vehicle_count,
                expected_distractor_count =
                    scenario.scene_adjustments.expected_distractor_count,
                marked_distractor_count = marked,
                nearby_vehicles = survey,
            };
            File.WriteAllText(
                RuntimePaths.ProjectFile(
                    "docs",
                    "evidence",
                    "P1-SCENE-004-scene-survey.json"),
                JsonUtility.ToJson(document, true) + "\n");
            Debug.Log(
                $"P1-SCENE-004 scene survey: before {before.violation_count}, "
                + $"after {after.violation_count} violations, "
                + $"{survey.Length} vehicles within {SurveyRadiusM} m, "
                + $"{marked} marked distractors "
                + $"(expected {document.expected_distractor_count}).");
        }

        static float DistanceToRoute(Vector3 position, Vector3[] route)
        {
            var point = new Vector2(position.x, position.z);
            float minimum = float.PositiveInfinity;
            for (int index = 0; index < route.Length; index++)
            {
                Vector3 startPoint = route[index];
                Vector3 endPoint = route[(index + 1) % route.Length];
                var start = new Vector2(startPoint.x, startPoint.z);
                var end = new Vector2(endPoint.x, endPoint.z);
                Vector2 delta = end - start;
                float t = delta.sqrMagnitude <= 1e-6f
                    ? 0f
                    : Mathf.Clamp01(Vector2.Dot(point - start, delta)
                        / delta.sqrMagnitude);
                minimum = Mathf.Min(
                    minimum,
                    Vector2.Distance(point, start + t * delta));
            }
            return minimum;
        }
    }
}
