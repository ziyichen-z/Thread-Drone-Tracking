using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TetheredTracking.Editor
{
    /// <summary>
    /// P1-M2-RATE-003 Amendment DR-B B2.1 route-legality evidence.
    ///
    /// The must-pass half of the difficulty-config audit includes the
    /// accepted SCENE-002 route-legality audit, and BC-DRB-3 compares the
    /// difficulty report field by field against an **archived D1 baseline
    /// report**. No such D1 report existed for the SCENE-004 circuit — the
    /// SCENE-002 generator is hardwired to `scenario.default.json` and
    /// asserts a legacy-route defect — so this generator produces both, from
    /// the frozen scenario bytes, with the same `RoadSceneAuditor` machinery
    /// and the same scene deconfliction the carrier runs with.
    ///
    /// Only `scenario_id` and `target.speed_mps` differ between the two
    /// configs, so the two reports must agree on every BC-DRB-3 field; the
    /// Python audit tool is what enforces that. This generator only writes
    /// what it measures and refuses to write a non-CLEAR report.
    /// </summary>
    public static class P1Rate003DifficultyEvidenceGenerator
    {
        const string ScenePath =
            "Assets/SimplePoly City - Low Poly Assets/Demo/"
            + "SimplePoly City - Low Poly Assets_Demo Scene.unity";

        internal readonly struct Target
        {
            public readonly string ConfigFileName;
            public readonly string EvidenceFileName;

            public Target(string configFileName, string evidenceFileName)
            {
                ConfigFileName = configFileName;
                EvidenceFileName = evidenceFileName;
            }
        }

        internal static readonly Target[] Targets =
        {
            new Target(
                "scenario.p1-scene-004.json",
                "P1-M2-RATE-003-d1-road-audit.json"),
            new Target(
                "scenario.p1-scene-004-d2.json",
                "P1-M2-RATE-003-d2-road-audit.json"),
        };

        public static void Generate()
        {
            foreach (Target target in Targets) GenerateOne(target);
        }

        static void GenerateOne(Target target)
        {
            // Re-open the scene per config so a previous run's vehicle
            // relocations cannot leak into the next audit.
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            string scenarioPath = RuntimePaths.ProjectFile(
                "config",
                target.ConfigFileName);
            ScenarioConfig scenario = ScenarioConfig.FromJsonStrict(
                File.ReadAllText(scenarioPath));
            RoadSceneData roadData = RoadSceneDataLoader.LoadVerified(
                scenario.road_data_sha256);

            IReadOnlyList<Transform> vehicleRoots =
                SceneVehicleAdjustmentApplier.FindSceneVehicleRoots();
            SceneVehicleAdjustmentApplier.Apply(
                scenario.scene_adjustments,
                vehicleRoots);

            IReadOnlyList<Transform> roots =
                RoadSceneAuditor.FindStaticRenderableRoots();
            RoadSceneAuditReport report = RoadSceneAuditor.Audit(
                scenario.scenario_id,
                scenario.TargetRoute(),
                scenario.scene_adjustments.route_corridor,
                roadData,
                roots);
            if (report.status != "CLEAR"
                || report.road_violation_count != 0
                || report.obstacle_violation_count != 0)
            {
                throw new InvalidOperationException(
                    $"{target.ConfigFileName} route is not clear: status "
                    + $"{report.status}, {report.road_violation_count} road / "
                    + $"{report.obstacle_violation_count} obstacle violations.");
            }
            string path = RuntimePaths.ProjectFile(
                "docs",
                "evidence",
                target.EvidenceFileName);
            File.WriteAllText(path, JsonUtility.ToJson(report, true) + "\n");
            Debug.Log(
                $"P1-M2-RATE-003 route-legality audit for "
                + $"{scenario.scenario_id}: {report.status}, "
                + $"{report.route_sample_count} route samples, "
                + $"{report.audited_obstacle_count} obstacles audited.");
        }
    }
}
