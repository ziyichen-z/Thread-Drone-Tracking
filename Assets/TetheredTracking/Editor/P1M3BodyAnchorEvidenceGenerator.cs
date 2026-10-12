using System.Collections.Generic;
using System.IO;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TetheredTracking.Editor
{
    /// <summary>
    /// P1-M3-BODY-001 batch 1a-alpha tool 1: runs the main-loop anchor
    /// support/clearance audit against the real checked-in city scene and
    /// writes the hash-bound evidence artifact (BC-M34-4 (c), hard gate 1 of
    /// BC-BODY1-3).
    ///
    /// Editor-side query only - no Play mode, no scenario/session/run ID, no
    /// quota (BC-BODY1-10). Unlike SCENE-004 this generator does not author
    /// an anchor: the anchor already exists in the frozen
    /// <c>config/scenario.default.json</c> bytes and the audit's job is to
    /// return a verdict on it, so the scenario is a real input here and the
    /// auditor cross-checks that the contract audits the same position.
    /// </summary>
    public static class P1M3BodyAnchorEvidenceGenerator
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
            P1M3BodyAnchorPlacementContract contract =
                P1M3BodyAnchorPlacementContractLoader.Load(
                    out string contractSha256);

            // The clearance verdict has to be about the scene the simulation
            // runs, so the scenario's vehicle relocations and removals are
            // applied first - the same order as
            // `TetheredScenarioBootstrap` and the SCENE-003 generator. The
            // scene is opened, mutated in memory and never saved, so the
            // checked-in scene bytes are untouched.
            SceneVehicleAdjustmentApplier.Apply(scenario.scene_adjustments);
            IReadOnlyList<Transform> roots =
                RoadSceneAuditor.FindStaticRenderableRoots();
            P1M3BodyAnchorAuditReport report = P1M3BodyAnchorAuditor.Audit(
                scenario,
                P1M3BodyAnchorPlacementContractLoader.Sha256(scenarioBytes),
                roadData,
                roots,
                contract,
                contractSha256);
            string destination = RuntimePaths.ProjectFile(
                "docs",
                "evidence",
                "P1-M3-BODY-001-anchor-audit.json");
            // BC-P2-10 established one strict-JSON serialization boundary for
            // artifacts in this project (`JsonUtility` prints bare `NaN`,
            // which no strict parser accepts, and the Python checkers use
            // `json.load`). That reviewed scanner is reused rather than
            // duplicated so the two boundaries cannot drift apart; the
            // fail-closed check below is what makes the reuse load-bearing.
            string json = Scene006.Scene006Json.ToStrictJson(
                JsonUtility.ToJson(report, true));
            if (Scene006.Scene006Json.ContainsNonFiniteToken(json))
                throw new IOException(
                    "p1_m3_body_anchor_audit_non_finite_token");
            File.WriteAllText(destination, json + "\n");
            Debug.Log(
                $"P1-M3-BODY-001 anchor audit: status {report.status}, "
                + $"reason '{report.rejection_reason}', "
                + $"support {report.support_status} at y "
                + $"{report.support_surface_y_m} (error "
                + $"{report.support_height_error_m} m), "
                + $"clearance {report.clearance_status}, "
                + $"{report.scene_root_count} roots, "
                + $"{report.audited_obstacle_count} audited obstacles, "
                + $"{report.blocker_count} blockers, "
                + $"route centreline distance "
                + $"{report.route_centerline_distance_m} m (diagnostic).");
        }
    }
}
