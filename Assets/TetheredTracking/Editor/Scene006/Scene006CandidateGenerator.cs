using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// P1-SCENE-006 amendment 1 batch-1b capture driver (BC-AM1-1–6).
    ///
    /// Single headless entry point so the whole batch is captured on one
    /// clean HEAD (§5.6: capture_commit == tool_commit == C_tool; the
    /// pre-capture `git status --porcelain` must be empty and is recorded):
    ///
    ///   .../Unity -batchmode -nographics -projectPath <repo> \
    ///     -executeMethod TetheredTracking.Scene006.Scene006CandidateGenerator.RunBatch1b \
    ///     -quit -logFile runtime/test-results/p1-scene-006-batch1b.log
    ///
    /// Order (fail closed at every named terminal, family B skipped after
    /// one): 1) family B relocation recompute + §3.3.2 row comparison +
    /// landing audits + SCENE-002 authoritative road/swept-corridor audit
    /// on the translated route (§3.3.1, before any geometry gate);
    /// 2) P1: per family, full T5 at the family lattice centre for each of
    /// the five frozen altitudes, per (anchor, altitude) pair state;
    /// 3) P2: the §5.3 preregistered grid restricted to P1-legal pairs —
    /// per anchor s_init (altitude-independence verified, fail closed on
    /// drift), per-anchor v2 trace artifact, T1/T2/T3 with per-tick
    /// occlusion attribution. Zero config/scene bytes: the scene file hash
    /// is recorded before and after and must be identical; the Edit Mode
    /// session never saves. No Play, no scenario/session/run IDs.
    /// </summary>
    public static class Scene006CandidateGenerator
    {
        const string RouteAuditArtifactPath =
            "docs/evidence/P1-SCENE-006-familyb-route-audit.json";

        [Serializable]
        public sealed class CaptureIdentity
        {
            public string capture_commit;
            public string tool_commit;
            public string git_status_porcelain;
            public string scene_state_sha256;
            public string scene_file_sha256_before;
            public string scene_file_sha256_after;
            public bool scene_saved;
        }

        [Serializable]
        public sealed class GridAnchorStatus
        {
            public float x_m;
            public float z_m;
            public float support_y_m;
            public float[] legal_altitudes_m;
        }

        [Serializable]
        public sealed class P1AltitudeReport
        {
            public float altitude_m;
            public Scene006AnchorPreflight.ModeReport report;
        }

        [Serializable]
        public sealed class P1FamilyReport
        {
            public string schema_version = "p1-scene-006-p1/v1";
            public string work_id = "P1-SCENE-006";
            public int batch = 11; // batch 1b
            public string family;
            public Scene006Evaluation.Vec3 lattice_center_m;
            public string route_identity;
            public string source_scenario_id;
            public string source_scenario_sha256;
            public string road_data_sha256;
            public CaptureIdentity capture;
            public string status;
            public GridAnchorStatus[] grid_anchors;
            public P1AltitudeReport[] altitudes;
        }

        [Serializable]
        public sealed class P2AnchorRecord
        {
            public float anchor_x_m;
            public float anchor_z_m;
            public float support_y_m;
            public float s_init;
            public bool s_init_altitude_consistent;
            public string trace_artifact;
            public string trace_sha256;
            public int trace_first_lap_steps;
            public string first_lap_status;
            public float[] legal_altitudes_m;
            public Scene006CandidateEvaluation.CellRecord[] cells;
        }

        [Serializable]
        public sealed class P2FamilyReport
        {
            public string schema_version = "p1-scene-006-p2/v1";
            public string work_id = "P1-SCENE-006";
            public int batch = 11; // batch 1b
            public string family;
            public string route_identity;
            public string source_scenario_id;
            public string source_scenario_sha256;
            public string road_data_sha256;
            public CaptureIdentity capture;
            public string status;
            public int in_band_cell_count;
            public int evaluated_cell_count;
            public P2AnchorRecord[] anchors;
        }

        [Serializable]
        public sealed class FamilyBRouteAuditReport
        {
            public string schema_version =
                "p1-scene-006-familyb-route-audit/v1";
            public string work_id = "P1-SCENE-006";
            public int batch = 11;
            public string source_scenario_id;
            public string source_scenario_sha256;
            public string road_data_sha256;
            public CaptureIdentity capture;
            public string status;
            public Scene006Evaluation.Vec3[] translated_route;
            public Scene006RelocationSolver.RelocationRecord[] relocations;
            public int relocation_obstacle_instance_count;
            public int road_violation_count;
            public int obstacle_violation_count;
            public int corridor_violation_count;
            public int audited_obstacle_count;
            public int audited_vehicle_count;
            public RoadSceneAuditReport road_audit;
            public RouteCorridorAuditReport corridor_audit;
        }

        public static void RunBatch1b()
        {
            RunGuarded(() =>
            {
                CaptureIdentity identity = CaptureIdentityRecord();
                ScenarioConfig config = Scene006SceneRig.LoadFrozenScenario(
                    out string scenarioSha256);

                // Family B first: its legality gate precedes any family-B
                // geometry gate (§3.3.1).
                string familyBStatus = RunFamilyBLegality(
                    config, scenarioSha256, identity);
                RunFamily(
                    Scene006CandidateContract.FamilyA,
                    config,
                    scenarioSha256,
                    identity,
                    applyFamilyBRelocations: false);
                if (familyBStatus == "CLEAR")
                {
                    RunFamily(
                        Scene006CandidateContract.FamilyB,
                        config,
                        scenarioSha256,
                        identity,
                        applyFamilyBRelocations: true);
                }
                else
                {
                    UnityEngine.Debug.Log(
                        "[SCENE-006] family B skipped after legality "
                        + "terminal: " + familyBStatus);
                }
                UnityEngine.Debug.Log(
                    "[SCENE-006] batch 1b capture complete");
            });
        }

        // ----------------------------------------------------------------
        // Family B: recompute, landing audit, route legality
        // ----------------------------------------------------------------

        static string RunFamilyBLegality(
            ScenarioConfig config,
            string scenarioSha256,
            CaptureIdentity identity)
        {
            var rig = new Scene006SceneRig
            {
                Config = config,
                ScenarioSha256 = scenarioSha256,
            };
            string status;
            var report = new FamilyBRouteAuditReport
            {
                source_scenario_id = config.scenario_id,
                source_scenario_sha256 = scenarioSha256,
                road_data_sha256 = config.road_data_sha256,
            };
            try
            {
                rig.OpenCityScene();
                rig.ApplySceneAdjustments();
                rig.LoadRoadData();
                rig.CollectStaticRoots();
                identity.scene_state_sha256 = SceneStateHash(rig);
                Vector3[] route = Scene006CandidateContract.FamilyRoute(
                    Scene006CandidateContract.FamilyB, config.TargetRoute());
                report.translated_route = ToVec3Array(route);

                // Recompute the five rows on the pre-relocation scene.
                var footprints = new Dictionary<string, RoadObstacleFootprint>(
                    StringComparer.Ordinal);
                foreach (RoadObstacleFootprint footprint
                    in rig.RoadData.obstacle_footprints)
                {
                    footprints[footprint.canonical_name] = footprint;
                }
                var obstacles =
                    new List<Scene006RelocationSolver.InstanceFootprint>();
                var byRoot = new Dictionary<Transform,
                    Scene006RelocationSolver.InstanceFootprint>();
                foreach (Transform root in rig.StaticRoots)
                {
                    string canonical =
                        SceneVehicleAdjustmentApplier.CanonicalPrefabName(
                            root.name);
                    if (!footprints.TryGetValue(
                        canonical, out RoadObstacleFootprint prototype))
                    {
                        continue; // road surfaces: no obstacle prototype
                    }
                    Scene006RelocationSolver.InstanceFootprint instance =
                        Scene006RelocationSolver.BuildFootprint(
                            root, prototype);
                    if (instance.MaxY - instance.MinY
                        <= Scene006RelocationSolver.MinObstacleThicknessM)
                    {
                        continue; // grass tiles and other flat planes
                    }
                    obstacles.Add(instance);
                    byRoot[root] = instance;
                }

                Transform[] vehicleRoots = SceneVehicleAdjustmentApplier
                    .FindSceneVehicleRoots()
                    .ToArray();
                var records =
                    new List<Scene006RelocationSolver.RelocationRecord>();
                var subjects = new List<Transform>();
                var placed =
                    new List<Scene006RelocationSolver.InstanceFootprint>();
                bool mismatch = false;
                bool noLanding = false;
                foreach (Scene006CandidateContract.AuthorizedRelocation row
                    in Scene006CandidateContract.FamilyBRelocations)
                {
                    Transform subject = FindUniqueVehicle(
                        vehicleRoots, row.PrefabName, row.OriginalXz);
                    subjects.Add(subject);
                    Scene006RelocationSolver.InstanceFootprint subjectFootprint =
                        byRoot[subject];
                    var sceneObstacles =
                        new List<Scene006RelocationSolver.InstanceFootprint>();
                    foreach (Scene006RelocationSolver.InstanceFootprint obstacle
                        in obstacles)
                    {
                        if (obstacle != subjectFootprint)
                            sceneObstacles.Add(obstacle);
                    }
                    Scene006RelocationSolver.RecomputedLanding recomputed =
                        Scene006RelocationSolver.Recompute(
                            subjectFootprint,
                            route,
                            rig.RoadData,
                            sceneObstacles,
                            placed);
                    var record = new Scene006RelocationSolver.RelocationRecord
                    {
                        prefab_name = row.PrefabName,
                        original_x_m = row.OriginalXz.x,
                        original_z_m = row.OriginalXz.y,
                        current_route_clearance_m = Scene006RelocationSolver
                            .FootprintRouteDistance(subjectFootprint, route),
                        authorized_segment_index = row.NearestSegmentIndex,
                        recomputed_segment_index =
                            recomputed.NearestSegmentIndex,
                        authorized_direction = row.Direction,
                        recomputed_direction =
                            recomputed.Solved ? recomputed.Direction : "",
                        authorized_displacement_m = row.DisplacementM,
                        recomputed_displacement_m =
                            recomputed.Solved ? recomputed.DisplacementM : 0f,
                        authorized_new_position_m = ToVec3(row.NewPosition),
                        recomputed_new_position_m = recomputed.Solved
                            ? ToVec3(recomputed.NewPosition)
                            : null,
                        recompute_match = Scene006RelocationSolver.Matches(
                            row, recomputed),
                    };
                    records.Add(record);
                    UnityEngine.Debug.Log(
                        $"[SCENE-006] relocation {row.PrefabName} "
                        + $"({row.OriginalXz.x},{row.OriginalXz.y}): "
                        + $"clearance {record.current_route_clearance_m:F4}, "
                        + $"recomputed seg {recomputed.NearestSegmentIndex} "
                        + $"{record.recomputed_direction} "
                        + $"{record.recomputed_displacement_m:F1} -> "
                        + (recomputed.Solved
                            ? $"({recomputed.NewPosition.x:F3}, "
                              + $"{recomputed.NewPosition.z:F3})"
                            : "NO_LANDING")
                        + $"; authorized seg {row.NearestSegmentIndex} "
                        + $"{row.Direction} {row.DisplacementM:F1} -> "
                        + $"({row.NewPosition.x:F3}, {row.NewPosition.z:F3}); "
                        + $"match {record.recompute_match}");
                    if (!recomputed.Solved)
                    {
                        noLanding = true;
                    }
                    else
                    {
                        if (!record.recompute_match) mismatch = true;
                        placed.Add(Scene006RelocationSolver.Translated(
                            subjectFootprint,
                            new Vector2(
                                recomputed.NewPosition.x
                                    - subjectFootprint.RootPosition.x,
                                recomputed.NewPosition.z
                                    - subjectFootprint.RootPosition.z)));
                    }
                }
                report.relocations = records.ToArray();
                report.relocation_obstacle_instance_count = obstacles.Count;
                if (noLanding)
                {
                    status = "RELOCATION_NO_LEGAL_LANDING";
                    report.status = status;
                    StampAndWrite(report, identity);
                    return status;
                }
                if (mismatch)
                {
                    status = "RELOCATION_RECOMPUTE_MISMATCH";
                    report.status = status;
                    StampAndWrite(report, identity);
                    return status;
                }

                // Apply the five authorized rows (fail closed inside the
                // applier on any non-unique binding), then audit landings.
                ApplyFamilyBRelocations();
                identity.scene_state_sha256 = SceneStateHash(rig);
                UnityEngine.Debug.Log(
                    "[SCENE-006] family B relocations applied; "
                    + "running landing audits");
                bool landingIllegal = false;
                var postObstacles =
                    new List<Scene006RelocationSolver.InstanceFootprint>();
                var postByRoot = new Dictionary<Transform,
                    Scene006RelocationSolver.InstanceFootprint>();
                foreach (Transform root in rig.StaticRoots)
                {
                    string canonical =
                        SceneVehicleAdjustmentApplier.CanonicalPrefabName(
                            root.name);
                    if (!footprints.TryGetValue(
                        canonical, out RoadObstacleFootprint prototype))
                    {
                        continue;
                    }
                    Scene006RelocationSolver.InstanceFootprint instance =
                        Scene006RelocationSolver.BuildFootprint(
                            root, prototype);
                    if (instance.MaxY - instance.MinY
                        <= Scene006RelocationSolver.MinObstacleThicknessM)
                    {
                        continue;
                    }
                    postObstacles.Add(instance);
                    postByRoot[root] = instance;
                }
                for (int rowIndex = 0; rowIndex < records.Count; rowIndex++)
                {
                    Scene006RelocationSolver.RelocationRecord record =
                        records[rowIndex];
                    // The vehicles are already at their new positions; bind
                    // by the transform captured during the recompute, never
                    // by re-matching the original coordinates.
                    Transform subject = subjects[rowIndex];
                    Scene006RelocationSolver.InstanceFootprint landing =
                        postByRoot[subject];
                    record.landing_road_coverage = Scene006RelocationSolver
                        .FullyOnRoadSurfaces(landing, rig.RoadData);
                    bool clear = true;
                    foreach (Scene006RelocationSolver.InstanceFootprint obstacle
                        in postObstacles)
                    {
                        if (obstacle == landing) continue;
                        if (Scene006RelocationSolver.Overlaps(
                            landing.Corners, obstacle.Corners))
                        {
                            clear = false;
                            record.landing_blocking_object = obstacle.Name;
                            break;
                        }
                    }
                    record.landing_static_clearance = clear;
                    if (!record.landing_road_coverage || !clear)
                        landingIllegal = true;
                }
                if (landingIllegal)
                {
                    status = "RELOCATION_LANDING_ILLEGAL";
                    report.status = status;
                    StampAndWrite(report, identity);
                    return status;
                }

                // SCENE-002 authoritative route legality on the translated
                // route, on the same frozen temporary scene state (§3.3.3).
                RoadSceneAuditReport roadAudit = RoadSceneAuditor.Audit(
                    config.scenario_id + "-scene006-familyb-candidate",
                    route,
                    config.scene_adjustments.route_corridor,
                    rig.RoadData,
                    rig.StaticRoots);
                RouteCorridorAuditReport corridorAudit =
                    RouteCorridorAuditor.Audit(
                        config.scenario_id + "-scene006-familyb-candidate",
                        route,
                        config.scene_adjustments.route_corridor);
                report.road_audit = roadAudit;
                report.corridor_audit = corridorAudit;
                report.road_violation_count = roadAudit.road_violation_count;
                report.obstacle_violation_count =
                    roadAudit.obstacle_violation_count;
                report.corridor_violation_count =
                    corridorAudit.violation_count;
                report.audited_obstacle_count =
                    roadAudit.audited_obstacle_count;
                report.audited_vehicle_count =
                    corridorAudit.audited_vehicle_count;
                status = roadAudit.road_violation_count == 0
                    && roadAudit.obstacle_violation_count == 0
                    && corridorAudit.violation_count == 0
                    ? "CLEAR" : "ROUTE_LEGALITY_FAILED";
                report.status = status;
                StampAndWrite(report, identity);
                return status;
            }
            finally
            {
                rig.Cleanup();
            }
        }

        static Transform FindUniqueVehicle(
            Transform[] vehicleRoots, string prefabName, Vector2 originalXz)
        {
            var matches = new List<Transform>();
            foreach (Transform root in vehicleRoots)
            {
                if (!string.Equals(
                    SceneVehicleAdjustmentApplier.CanonicalPrefabName(
                        root.name),
                    prefabName,
                    StringComparison.Ordinal)) continue;
                if (Vector2.Distance(
                    new Vector2(root.position.x, root.position.z),
                    originalXz)
                    <= Scene006CandidateContract.RelocationMatchToleranceM)
                {
                    matches.Add(root);
                }
            }
            if (matches.Count != 1)
            {
                throw new InvalidOperationException(
                    $"relocation binding '{prefabName}' at {originalXz} "
                    + $"matched {matches.Count} scene roots; "
                    + "exactly one is required");
            }
            return matches[0];
        }

        static void ApplyFamilyBRelocations()
        {
            var rows = Scene006CandidateContract.FamilyBRelocations;
            var configs = new VehicleRelocationScenarioConfig[rows.Length];
            for (int index = 0; index < rows.Length; index++)
            {
                Scene006CandidateContract.AuthorizedRelocation row =
                    rows[index];
                configs[index] = new VehicleRelocationScenarioConfig
                {
                    prefab_name = row.PrefabName,
                    original_xz_m = new ScenarioVector2(
                        row.OriginalXz.x, row.OriginalXz.y),
                    match_tolerance_m =
                        Scene006CandidateContract.RelocationMatchToleranceM,
                    new_position_m = new ScenarioVector3(
                        row.NewPosition.x,
                        row.NewPosition.y,
                        row.NewPosition.z),
                    mark_as_distractor = false,
                    remove_from_scene = false,
                };
            }
            var adjustments = new SceneAdjustmentsScenarioConfig
            {
                vehicle_relocations = configs,
            };
            SceneVehicleAdjustmentApplier.Apply(
                adjustments,
                SceneVehicleAdjustmentApplier.FindSceneVehicleRoots(),
                new PlacementPhaseGuard());
        }

        // ----------------------------------------------------------------
        // P1 + P2 per family
        // ----------------------------------------------------------------

        static void RunFamily(
            string family,
            ScenarioConfig config,
            string scenarioSha256,
            CaptureIdentity identity,
            bool applyFamilyBRelocations)
        {
            var rig = new Scene006SceneRig
            {
                Config = config,
                ScenarioSha256 = scenarioSha256,
            };
            try
            {
                rig.OpenCityScene();
                rig.ApplySceneAdjustments();
                if (applyFamilyBRelocations) ApplyFamilyBRelocations();
                rig.LoadRoadData();
                rig.CreateTargetReplica();
                rig.CreateEvaluationCamera(
                    Scene006CandidateContract.VerticalFovsDeg[0],
                    config.sensor.width,
                    config.sensor.height);
                rig.CollectStaticRoots(rig.TargetReplica.transform);
                rig.BuildOcclusionProxies();
                identity.scene_state_sha256 = SceneStateHash(rig);

                Vector3[] route = Scene006CandidateContract.FamilyRoute(
                    family, config.TargetRoute());
                Vector2 center =
                    Scene006CandidateContract.LatticeCenter(family);
                string routeIdentity = family == Scene006CandidateContract.FamilyA
                    ? "frozen_route"
                    : "frozen_route+(+60,-60)";

                // P1: full T5 per altitude at the family lattice centre.
                var altitudeReports =
                    new P1AltitudeReport[
                        Scene006CandidateContract.AltitudesM.Length];
                for (int index = 0;
                    index < Scene006CandidateContract.AltitudesM.Length;
                    index++)
                {
                    float altitude =
                        Scene006CandidateContract.AltitudesM[index];
                    altitudeReports[index] = new P1AltitudeReport
                    {
                        altitude_m = altitude,
                        report = Scene006AnchorPreflight.RunMode(
                            Scene006AnchorPreflight.ModeCandidatePreflight,
                            config,
                            scenarioSha256,
                            rig.RoadData,
                            rig.StaticRoots,
                            new Vector3(center.x, 0f, center.y),
                            altitude,
                            route),
                    };
                    UnityEngine.Debug.Log(
                        $"[SCENE-006] P1 family {family} altitude "
                        + $"{altitude}: {altitudeReports[index].report.status} "
                        + $"({altitudeReports[index].report.legal_candidate_count}"
                        + $"/{altitudeReports[index].report.candidate_count})");
                }

                Vector2[] gridAnchors =
                    Scene006CandidateContract.GridAnchors(family);
                var gridStatus = new GridAnchorStatus[gridAnchors.Length];
                int legalPairCount = 0;
                bool anyAltitudeLegal = false;
                for (int anchor = 0; anchor < gridAnchors.Length; anchor++)
                {
                    var legalAltitudes = new List<float>();
                    float supportY = float.NaN;
                    foreach (P1AltitudeReport altitudeReport in altitudeReports)
                    {
                        Scene006AnchorPreflight.CandidateRecord candidate =
                            FindCandidate(
                                altitudeReport.report, gridAnchors[anchor]);
                        if (candidate == null)
                        {
                            throw new InvalidOperationException(
                                "grid anchor is not a lattice candidate: "
                                + gridAnchors[anchor]);
                        }
                        if (altitudeReport.report.legal_candidate_count > 0)
                            anyAltitudeLegal = true;
                        if (!candidate.legal) continue;
                        legalAltitudes.Add(altitudeReport.altitude_m);
                        if (float.IsNaN(supportY))
                        {
                            supportY = candidate.support_surface_y_m;
                        }
                        else if (Mathf.Abs(
                            supportY - candidate.support_surface_y_m) > 1e-5f)
                        {
                            throw new InvalidOperationException(
                                "support y differs across altitudes for the "
                                + "same candidate; P2 cannot bind a single "
                                + "support instance");
                        }
                    }
                    legalPairCount += legalAltitudes.Count;
                    gridStatus[anchor] = new GridAnchorStatus
                    {
                        x_m = gridAnchors[anchor].x,
                        z_m = gridAnchors[anchor].y,
                        support_y_m = supportY,
                        legal_altitudes_m = legalAltitudes.ToArray(),
                    };
                }

                string p1Status;
                if (!anyAltitudeLegal)
                {
                    p1Status = "BLOCKED_ANCHOR_PLACEMENT_V3";
                }
                else if (legalPairCount == 0)
                {
                    p1Status = "BLOCKED_NO_SAFE_SCREEN_POINT";
                }
                else
                {
                    p1Status = "P1_OK";
                }
                var p1 = new P1FamilyReport
                {
                    family = family,
                    lattice_center_m = ToVec3(
                        new Vector3(center.x, 0f, center.y)),
                    route_identity = routeIdentity,
                    source_scenario_id = config.scenario_id,
                    source_scenario_sha256 = scenarioSha256,
                    road_data_sha256 = config.road_data_sha256,
                    status = p1Status,
                    grid_anchors = gridStatus,
                    altitudes = altitudeReports,
                };
                p1.capture = StampIdentity(identity);
                WriteArtifact(ArtifactPath("p1", family), p1);
                UnityEngine.Debug.Log(
                    $"[SCENE-006] P1 family {family}: {p1Status}, "
                    + $"{legalPairCount} legal grid pairs");
                if (p1Status != "P1_OK") return;

                // P2: the preregistered grid restricted to legal pairs.
                var anchorRecords = new List<P2AnchorRecord>();
                int inBand = 0;
                int evaluated = 0;
                foreach (GridAnchorStatus anchor in gridStatus)
                {
                    if (anchor.legal_altitudes_m.Length == 0) continue;
                    anchorRecords.Add(RunP2Anchor(
                        family,
                        anchor,
                        config,
                        route,
                        rig,
                        identity,
                        ref evaluated,
                        ref inBand));
                }
                var p2 = new P2FamilyReport
                {
                    family = family,
                    route_identity = routeIdentity,
                    source_scenario_id = config.scenario_id,
                    source_scenario_sha256 = scenarioSha256,
                    road_data_sha256 = config.road_data_sha256,
                    status = inBand > 0
                        ? "P2_OK" : "BLOCKED_GEOMETRY_INFEASIBLE",
                    in_band_cell_count = inBand,
                    evaluated_cell_count = evaluated,
                    anchors = anchorRecords.ToArray(),
                };
                p2.capture = StampIdentity(identity);
                WriteArtifact(ArtifactPath("p2", family), p2);
                UnityEngine.Debug.Log(
                    $"[SCENE-006] P2 family {family}: {p2.status}, "
                    + $"{inBand}/{evaluated} cells in band");
            }
            finally
            {
                rig.Cleanup();
            }
        }

        static P2AnchorRecord RunP2Anchor(
            string family,
            GridAnchorStatus anchor,
            ScenarioConfig config,
            Vector3[] route,
            Scene006SceneRig rig,
            CaptureIdentity identity,
            ref int evaluated,
            ref int inBand)
        {
            // §3.6: s_init is the off-axis argmin phase; it is altitude
            // independent on a level route, which is verified explicitly
            // (fail closed on drift) rather than assumed.
            float sInit = float.NaN;
            bool sInitConsistent = true;
            foreach (float altitude in anchor.legal_altitudes_m)
            {
                Vector3 pHover = Scene006StationSet.HoverPosition(
                    new Vector3(anchor.x_m, 0f, anchor.z_m),
                    anchor.support_y_m,
                    altitude);
                float candidate =
                    Scene006RouteGeometry.ArgminOffAxisPhase(pHover, route);
                if (float.IsNaN(sInit))
                {
                    sInit = candidate;
                }
                else if (Mathf.Abs(candidate - sInit) > 1e-4f)
                {
                    sInitConsistent = false;
                }
            }
            if (!sInitConsistent)
            {
                throw new InvalidOperationException(
                    $"s_init depends on altitude for family {family} anchor "
                    + $"({anchor.x_m}, {anchor.z_m}); the per-anchor trace "
                    + "binding is undefined");
            }

            Scene006Trace.State[] trace = Scene006Trace.Generate(
                route, config.target.speed_mps, sInit);
            string traceSha = Scene006Trace.HashStates(trace);
            int firstLap = Scene006Trace.FirstLapSteps(route, sInit, trace);
            string tracePath = string.Format(
                CultureInfo.InvariantCulture,
                "docs/evidence/P1-SCENE-006-trace-{0}-{1:0.0#}-{2:0.0#}.json",
                family,
                anchor.x_m,
                anchor.z_m);
            Scene006TraceArtifact.Artifact traceArtifact =
                Scene006TraceArtifact.Build(
                    config.scenario_id,
                    rig.ScenarioSha256,
                    family,
                    new Vector3(anchor.x_m, 0f, anchor.z_m),
                    anchor.support_y_m,
                    sInit,
                    trace,
                    firstLap);
            // §5.6: the trace artifact is an independent artifact and must
            // carry the same dual identity and zero-write proof as the
            // P1/P2/route-audit artifacts (B1B-R1).
            traceArtifact.capture = StampIdentity(identity);
            Scene006TraceArtifact.Write(tracePath, traceArtifact);
            bool horizonShort = firstLap <= 0
                || firstLap > Scene006Trace.HorizonSteps;

            var cells = new List<Scene006CandidateEvaluation.CellRecord>();
            foreach (float altitude in anchor.legal_altitudes_m)
            {
                foreach (float vfov in Scene006CandidateContract.VerticalFovsDeg)
                {
                    evaluated++;
                    if (horizonShort)
                    {
                        cells.Add(new Scene006CandidateEvaluation.CellRecord
                        {
                            family = family,
                            anchor_x_m = anchor.x_m,
                            anchor_z_m = anchor.z_m,
                            support_y_m = anchor.support_y_m,
                            initial_altitude_m = altitude,
                            vertical_fov_deg = vfov,
                            s_init = sInit,
                            trace_sha256 = traceSha,
                            trace_artifact = tracePath,
                            trace_first_lap_steps = firstLap,
                            terminal = "HORIZON_SHORT",
                        });
                        continue;
                    }
                    var inputs = new Scene006CandidateEvaluation.Inputs
                    {
                        Family = family,
                        AnchorXz = new Vector2(anchor.x_m, anchor.z_m),
                        SupportY = anchor.support_y_m,
                        AltitudeM = altitude,
                        VerticalFovDeg = vfov,
                        ImageWidth = config.sensor.width,
                        ImageHeight = config.sensor.height,
                        Route = route,
                        Trace = trace,
                        SInit = sInit,
                        TraceSha256 = traceSha,
                        TraceArtifactPath = tracePath,
                        FirstLapSteps = firstLap,
                        TargetRoot = rig.TargetReplica.transform,
                        TargetRenderers = rig.TargetRenderers,
                        Cam = rig.EvaluationCamera,
                    };
                    Scene006CandidateEvaluation.CellRecord cell =
                        Scene006CandidateEvaluation.RunCell(inputs);
                    if (cell.gates_in_band) inBand++;
                    cells.Add(cell);
                }
            }
            UnityEngine.Debug.Log(
                $"[SCENE-006] P2 family {family} anchor "
                + $"({anchor.x_m}, {anchor.z_m}): s_init {sInit}, "
                + $"first lap {(horizonShort ? "HORIZON_SHORT" : firstLap.ToString())}, "
                + $"{cells.Count} cells");
            return new P2AnchorRecord
            {
                anchor_x_m = anchor.x_m,
                anchor_z_m = anchor.z_m,
                support_y_m = anchor.support_y_m,
                s_init = sInit,
                s_init_altitude_consistent = sInitConsistent,
                trace_artifact = tracePath,
                trace_sha256 = traceSha,
                trace_first_lap_steps = firstLap,
                first_lap_status = horizonShort ? "HORIZON_SHORT" : "MEASURED",
                legal_altitudes_m = anchor.legal_altitudes_m,
                cells = cells.ToArray(),
            };
        }

        static Scene006AnchorPreflight.CandidateRecord FindCandidate(
            Scene006AnchorPreflight.ModeReport report, Vector2 anchor)
        {
            foreach (Scene006AnchorPreflight.CandidateRecord candidate
                in report.candidates)
            {
                if (Mathf.Abs(candidate.x_m - anchor.x) <= 1e-6f
                    && Mathf.Abs(candidate.z_m - anchor.y) <= 1e-6f)
                {
                    return candidate;
                }
            }
            return null;
        }

        // ----------------------------------------------------------------
        // Identity, hashing, IO
        // ----------------------------------------------------------------

        static string ArtifactPath(string stage, string family) =>
            $"docs/evidence/P1-SCENE-006-{stage}-family{family}.json";

        static Scene006Evaluation.Vec3 ToVec3(Vector3 value) =>
            new Scene006Evaluation.Vec3
            {
                x = value.x,
                y = value.y,
                z = value.z,
            };

        static Scene006Evaluation.Vec3[] ToVec3Array(Vector3[] values)
        {
            var result = new Scene006Evaluation.Vec3[values.Length];
            for (int index = 0; index < values.Length; index++)
                result[index] = ToVec3(values[index]);
            return result;
        }

        static CaptureIdentity CaptureIdentityRecord()
        {
            string head = RunGit("rev-parse HEAD");
            string porcelain = RunGit("status --porcelain");
            if (porcelain.Length != 0)
            {
                throw new InvalidOperationException(
                    "capture requires a clean worktree; git status "
                    + "--porcelain is non-empty:\n" + porcelain);
            }
            // Batch 1b captures P1/P2 directly on the tool commit, so the
            // two identity fields coincide by construction (§5.6 ①); the
            // zero-diff proof obligation only exists when they differ.
            return new CaptureIdentity
            {
                capture_commit = head,
                tool_commit = head,
                git_status_porcelain = porcelain,
                scene_state_sha256 = "",
                scene_file_sha256_before = SceneFileHash(),
                scene_file_sha256_after = "",
                scene_saved = false,
            };
        }

        /// <summary>
        /// Stamps an artifact with the capture identity plus the scene-file
        /// "unsaved" proof (§3.3.3): the scene .unity bytes must be
        /// identical to the batch-start hash, or the run fails closed.
        /// </summary>
        static CaptureIdentity StampIdentity(CaptureIdentity identity)
        {
            string after = SceneFileHash();
            if (after != identity.scene_file_sha256_before)
            {
                throw new InvalidOperationException(
                    "scene file changed during capture; the zero-write "
                    + "contract is violated");
            }
            return new CaptureIdentity
            {
                capture_commit = identity.capture_commit,
                tool_commit = identity.tool_commit,
                git_status_porcelain = identity.git_status_porcelain,
                scene_state_sha256 = identity.scene_state_sha256,
                scene_file_sha256_before = identity.scene_file_sha256_before,
                scene_file_sha256_after = after,
                scene_saved = false,
            };
        }

        static void StampAndWrite(
            FamilyBRouteAuditReport report, CaptureIdentity identity)
        {
            report.capture = StampIdentity(identity);
            WriteArtifact(RouteAuditArtifactPath, report);
        }

        static string SceneStateHash(Scene006SceneRig rig)
        {
            var builder = new StringBuilder();
            foreach (Transform root in rig.StaticRoots)
            {
                builder.Append(root.name).Append('|')
                    .Append(root.position.ToString("R")).Append('|')
                    .Append(root.rotation.ToString("R")).Append('|')
                    .Append(root.lossyScale.ToString("R")).Append('\n');
            }
            return Scene006RouteGeometry.Sha256Hex(
                Encoding.UTF8.GetBytes(builder.ToString()));
        }

        static string SceneFileHash()
        {
            return Scene006RouteGeometry.Sha256Hex(
                File.ReadAllBytes(Scene006SceneRig.CityScenePath));
        }

        static string RunGit(string arguments)
        {
            string projectRoot = Path.GetFullPath(
                Path.Combine(Application.dataPath, ".."));
            var startInfo = new ProcessStartInfo("git", arguments)
            {
                WorkingDirectory = projectRoot,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
            };
            using System.Diagnostics.Process process =
                System.Diagnostics.Process.Start(startInfo);
            string stdout = process.StandardOutput.ReadToEnd();
            string stderr = process.StandardError.ReadToEnd();
            process.WaitForExit();
            if (process.ExitCode != 0)
            {
                throw new InvalidOperationException(
                    "git " + arguments + " failed: " + stderr);
            }
            return stdout.Trim();
        }

        static void WriteArtifact<T>(string projectRelativePath, T report)
        {
            AtomicFile.WriteAllText(
                RuntimePaths.ProjectFile(projectRelativePath.Split('/')),
                JsonUtility.ToJson(report, true) + "\n");
        }

        delegate void Run();

        static void RunGuarded(Run run)
        {
            try
            {
                run();
            }
            catch (Exception exception)
            {
                UnityEngine.Debug.LogException(exception);
                UnityEditor.EditorApplication.Exit(1);
            }
        }
    }
}
