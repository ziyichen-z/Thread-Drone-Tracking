using System.Collections.Generic;
using System.IO;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TetheredTracking.Editor
{
    /// <summary>
    /// P1-M3-BODY-001 batch 1a-alpha: drives
    /// <see cref="P1M3BodySceneGeometry"/> against the real checked-in city
    /// scene and writes the obstacle prism evidence artifact tool 2 and the
    /// corridor builder both derive from.
    ///
    /// Editor query only: no Play mode, no scenario/session/run ID, no quota
    /// (BC-BODY1-10).
    /// </summary>
    public static class P1M3BodySceneGeometryGenerator
    {
        const string ScenePath =
            "Assets/SimplePoly City - Low Poly Assets/Demo/"
            + "SimplePoly City - Low Poly Assets_Demo Scene.unity";

        public static void Generate()
        {
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            string scenarioPath = RuntimePaths.ProjectFile(
                "config",
                "scenario.default.json");
            byte[] scenarioBytes = File.ReadAllBytes(scenarioPath);
            ScenarioConfig scenario = ScenarioConfig.FromJsonStrict(
                File.ReadAllText(scenarioPath));
            RoadSceneData roadData =
                RoadSceneDataLoader.LoadVerified(scenario.road_data_sha256);

            // Occluders must be the scene the simulation runs, not the raw
            // authored scene: `scenario.default.json` moves three vehicles
            // off the route and deletes three more, and several of those sit
            // on or beside the circuit. This is the bootstrap's own order -
            // apply, then harvest, then audit - and the scene is mutated in
            // memory only and never saved.
            IReadOnlyList<Transform> relocated =
                SceneVehicleAdjustmentApplier.Apply(scenario.scene_adjustments);
            IReadOnlyList<Transform> roots =
                RoadSceneAuditor.FindStaticRenderableRoots();
            RoadSceneAuditReport roadAudit = RoadSceneAuditor.Audit(
                scenario.scenario_id,
                scenario.TargetRoute(),
                scenario.scene_adjustments.route_corridor,
                roadData,
                roots);

            P1M3BodySceneGeometryArtifact artifact = P1M3BodySceneGeometry.Build(
                scenario,
                P1M3BodyAnchorPlacementContractLoader.Sha256(scenarioBytes),
                roadData,
                roots,
                ScenePath,
                sceneAdjustmentsApplied: true,
                relocatedVehicleCount: relocated.Count,
                roadAudit: roadAudit);
            string destination = RuntimePaths.ProjectFile(
                "docs",
                "evidence",
                "P1-M3-BODY-001-scene-geometry.json");
            string json = Scene006.Scene006Json.ToStrictJson(
                JsonUtility.ToJson(artifact, true));
            if (Scene006.Scene006Json.ContainsNonFiniteToken(json))
                throw new IOException(
                    "p1_m3_body_scene_geometry_non_finite_token");
            File.WriteAllText(destination, json + "\n");
            Debug.Log(
                $"P1-M3-BODY-001 scene geometry: {artifact.scene_root_count} "
                + $"roots, {artifact.road_surface_root_count} road surfaces, "
                + $"{artifact.instance_count} obstacle instances "
                + "(road-audit basis, scene adjustments applied, "
                + $"{artifact.relocated_vehicle_count} vehicles relocated); "
                + $"road audit {artifact.road_audit_status} with "
                + $"{artifact.road_audit_obstacle_count} audited obstacles.");
        }
    }
}
