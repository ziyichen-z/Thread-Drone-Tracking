using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TetheredTracking.Editor
{
    public static class P1Scene003AnchorEvidenceGenerator
    {
        const string ScenePath =
            "Assets/SimplePoly City - Low Poly Assets/Demo/"
            + "SimplePoly City - Low Poly Assets_Demo Scene.unity";

        public static void Generate()
        {
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            string scenarioPath = RuntimePaths.ProjectFile(
                "config",
                "scenario.p1-detect-scouting.json");
            byte[] scenarioBytes = File.ReadAllBytes(scenarioPath);
            ScenarioConfig scenario = ScenarioConfig.FromJsonStrict(
                File.ReadAllText(scenarioPath));
            RoadSceneData roadData =
                RoadSceneDataLoader.LoadVerified(scenario.road_data_sha256);
            P1Scene003AnchorPlacementContract contract =
                P1Scene003AnchorPlacementContractLoader.Load(
                    out string contractSha256);

            SceneVehicleAdjustmentApplier.Apply(scenario.scene_adjustments);
            IReadOnlyList<Transform> roots =
                RoadSceneAuditor.FindStaticRenderableRoots();
            P1Scene003AnchorAuditReport report =
                P1Scene003AnchorAuditor.Audit(
                    scenario,
                    P1Scene003AnchorPlacementContractLoader.Sha256(
                        scenarioBytes),
                    roadData,
                    roots,
                    contract,
                    contractSha256);
            string destination = RuntimePaths.ProjectFile(
                "docs",
                "evidence",
                "P1-SCENE-003-anchor-audit.json");
            File.WriteAllText(
                destination,
                JsonUtility.ToJson(report, true) + "\n");
            if (report.status != "BLOCKED_ANCHOR_PLACEMENT"
                || report.legal_candidate_count != 0)
            {
                throw new InvalidOperationException(
                    "P1-SCENE-003 checked-in geometry unexpectedly found "
                    + "a legal anchor candidate.");
            }
            Debug.Log(
                $"P1-SCENE-003 anchor audit generated: {report.candidate_count} "
                + "candidates, "
                + $"{report.support_rejection_count} support rejections, "
                + $"{report.clearance_rejection_count} clearance rejections, "
                + $"status {report.status}.");
        }
    }
}
