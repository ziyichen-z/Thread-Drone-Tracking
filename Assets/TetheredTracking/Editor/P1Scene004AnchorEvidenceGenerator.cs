using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TetheredTracking.Editor
{
    /// <summary>
    /// Runs the SCENE-004 anchor audit against the real checked-in city
    /// scene and writes the hash-bound evidence artifact.
    ///
    /// The scenario argument only carries the road-data identity: the
    /// SCENE-004 scenario config is authored *from* this audit's derived
    /// anchor, so it cannot be an input to it. The audited anchor candidate,
    /// circuit and gates all come from the anchor placement contract, whose
    /// SHA-256 is recorded in the report.
    /// </summary>
    public static class P1Scene004AnchorEvidenceGenerator
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
            P1Scene004AnchorPlacementContract contract =
                P1Scene004AnchorPlacementContractLoader.Load(
                    out string contractSha256);

            IReadOnlyList<Transform> roots =
                RoadSceneAuditor.FindStaticRenderableRoots();
            P1Scene004AnchorAuditReport report =
                P1Scene004AnchorAuditor.Audit(
                    scenario,
                    P1Scene004AnchorPlacementContractLoader.Sha256(
                        scenarioBytes),
                    roadData,
                    roots,
                    contract,
                    contractSha256);
            string destination = RuntimePaths.ProjectFile(
                "docs",
                "evidence",
                "P1-SCENE-004-anchor-audit.json");
            File.WriteAllText(
                destination,
                JsonUtility.ToJson(report, true) + "\n");
            Debug.Log(
                $"P1-SCENE-004 anchor audit: {report.candidate_count} candidates, "
                + $"{report.support_rejection_count} support rejections, "
                + $"{report.road_overlap_rejection_count} road overlaps, "
                + $"{report.envelope_rejection_count} envelope rejections, "
                + $"{report.clearance_rejection_count} clearance rejections, "
                + $"status {report.status}, "
                + $"anchor ({report.selected_anchor_world_m?.x}, "
                + $"{report.selected_anchor_world_m?.y}, "
                + $"{report.selected_anchor_world_m?.z}), "
                + $"max slant {report.selected_maximum_slant_range_m} m, "
                + $"max off-nadir {report.selected_maximum_off_nadir_deg} deg.");
        }
    }
}
