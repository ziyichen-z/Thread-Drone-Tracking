using System;
using System.IO;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TetheredTracking.Editor
{
    public static class SceneCorridorEvidenceGenerator
    {
        [Serializable]
        sealed class EvidenceSummary
        {
            public string schema_version = "p1-scene-corridor-evidence/v1";
            public int audited_vehicle_count;
            public int before_violation_count;
            public int after_violation_count;
            public string[] relocated_scene_objects;
            public Vector3[] relocated_positions_m;
            public int occlusion_candidate_renderers;
            public int occlusion_proxy_colliders;
            public int occlusion_existing_colliders;
            public int occlusion_failed_proxies;
            public bool every_relocated_vehicle_has_proxy;
        }

        const string ScenePath =
            "Assets/SimplePoly City - Low Poly Assets/Demo/"
            + "SimplePoly City - Low Poly Assets_Demo Scene.unity";

        public static void Generate()
        {
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            ScenarioConfig config = JsonUtility.FromJson<ScenarioConfig>(
                File.ReadAllText(
                    RuntimePaths.ProjectFile("config", "scenario.default.json")));
            if (config == null || config.scene_adjustments == null)
                throw new InvalidOperationException(
                    "scenario.default.json must contain scene_adjustments.");
            var roots = SceneVehicleAdjustmentApplier.FindSceneVehicleRoots();
            RouteCorridorAuditReport before = RouteCorridorAuditor.Audit(
                config.scenario_id + "-before-adjustments",
                config.TargetRoute(),
                config.scene_adjustments.route_corridor,
                roots);
            Write("P1-SCENE-001-corridor-before.json", before);
            if (before.violation_count != 3)
                throw new InvalidOperationException(
                    $"Expected exactly 3 baseline violations, got "
                    + $"{before.violation_count}.");

            var relocated =
                SceneVehicleAdjustmentApplier.Apply(config.scene_adjustments, roots);
            RouteCorridorAuditReport after = RouteCorridorAuditor.Audit(
                config.scenario_id + "-after-adjustments",
                config.TargetRoute(),
                config.scene_adjustments.route_corridor,
                roots);
            Write("P1-SCENE-001-corridor-after.json", after);
            if (after.violation_count != 0)
                throw new InvalidOperationException(
                    $"Expected zero post-adjustment violations, got "
                    + $"{after.violation_count}.");

            GameObject anchor = new GameObject("EvidenceAnchor");
            GameObject drone = new GameObject("EvidenceDrone");
            GameObject target = new GameObject("EvidenceTarget");
            GameObject geometryObject = new GameObject("EvidenceOcclusionGeometry");
            EvaluationOcclusionGeometry geometry =
                geometryObject.AddComponent<EvaluationOcclusionGeometry>();
            int proxyCount = 0;
            try
            {
                geometry.Build(anchor.transform, drone.transform, target.transform);
                proxyCount = geometry.ProxyColliderCount;
                bool everyRelocatedHasProxy = relocated.All(root =>
                    root.GetComponentsInChildren<MeshCollider>(true).Length > 0);
                if (geometry.FailedProxyCount != 0 || !everyRelocatedHasProxy)
                    throw new InvalidOperationException(
                        "Occlusion proxy verification failed after relocation.");
                Write("P1-SCENE-001-corridor-summary.json", new EvidenceSummary
                {
                    audited_vehicle_count = after.audited_vehicle_count,
                    before_violation_count = before.violation_count,
                    after_violation_count = after.violation_count,
                    relocated_scene_objects = relocated.Select(root => root.name).ToArray(),
                    relocated_positions_m =
                        relocated.Select(root => root.position).ToArray(),
                    occlusion_candidate_renderers = geometry.CandidateRendererCount,
                    occlusion_proxy_colliders = geometry.ProxyColliderCount,
                    occlusion_existing_colliders = geometry.ExistingColliderCount,
                    occlusion_failed_proxies = geometry.FailedProxyCount,
                    every_relocated_vehicle_has_proxy = everyRelocatedHasProxy,
                });
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(geometryObject);
                UnityEngine.Object.DestroyImmediate(anchor);
                UnityEngine.Object.DestroyImmediate(drone);
                UnityEngine.Object.DestroyImmediate(target);
            }

            Debug.Log(
                $"P1-SCENE-001 corridor evidence generated: "
                + $"{before.violation_count} before, {after.violation_count} after, "
                + $"{after.audited_vehicle_count} vehicles audited, "
                + $"{proxyCount} occlusion proxies.");
        }

        static void Write(string name, object report)
        {
            string path = RuntimePaths.ProjectFile("docs", "evidence", name);
            File.WriteAllText(path, JsonUtility.ToJson(report, true) + "\n");
        }
    }
}
