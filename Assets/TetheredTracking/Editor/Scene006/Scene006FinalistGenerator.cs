using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// P1-SCENE-006 amendment 1 batch 1c (§5.4 P3) runner — BC-B1C-1–5.
    ///
    /// Input is only the reviewed batch-1b artifacts (`77595c8`): the
    /// family-B P1/P2 JSON files are read from docs/evidence/ and bound by
    /// their SHA-256 in the P3 artifact. The §5.4 frozen selection picks
    /// the unique finalist; BC-B1C-2 verifies from the reviewed P1 artifact
    /// that every in-band cell and the finalist is legal with support bound
    /// to exactly one grass-allowlist instance — before any P3 gate value
    /// is produced. The finalist then gets the T5 re-audit (must equal the
    /// P1 altitude report item by item, else fail closed), the §5.4 T4
    /// station/certificate audit with the literal §5.4.4 head trim bound to
    /// that support instance, and the T6 acquisition scan. T1/T2/T3 gate
    /// values are never recomputed or overridden here: C_hold for T4 and
    /// the T6 size-gate median are read from the P2 cell.
    ///
    /// Zero config/scene bytes, zero Play, zero scenario/session/run IDs.
    /// Batch 2 stays BLOCKED_USER_GO; a P3_OK here is not a batch-2 GO.
    ///
    /// Entry point (only after the C_tool′ review passes):
    ///
    ///   .../Unity -batchmode -nographics -projectPath <repo> \
    ///     -executeMethod TetheredTracking.Scene006.Scene006FinalistGenerator.RunBatch1c \
    ///     -quit -logFile runtime/test-results/p1-scene-006-batch1c.log
    /// </summary>
    public static class Scene006FinalistGenerator
    {
        public const string P3Schema = "p1-scene-006-p3/v1";
        public const string P1ArtifactPath =
            "docs/evidence/P1-SCENE-006-p1-familyB.json";
        public const string P2ArtifactPath =
            "docs/evidence/P1-SCENE-006-p2-familyB.json";
        public const string P3ArtifactPath =
            "docs/evidence/P1-SCENE-006-p3-finalist.json";

        public static readonly string[] GrassAllowlist =
            { "Natures_Grass Tile", "Natures_Grass Tile Small" };

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
        public sealed class ArtifactBinding
        {
            public string path;
            public string sha256;
        }

        [Serializable]
        public sealed class SupportBindingRecord
        {
            public float anchor_x_m;
            public float anchor_z_m;
            public float initial_altitude_m;
            public int p1_candidate_rank = -1;
            public bool p1_legal;
            public string[] support_ids;
            public bool single_support;
            public bool grass_allowlist_match;
            public bool p1_p2_binding_consistent;
            public bool ok;
            public string mismatch = "";
        }

        [Serializable]
        public sealed class SelectionSection
        {
            public ArtifactBinding p1_artifact;
            public ArtifactBinding p2_artifact;
            public Scene006FinalistSelection.ScoredCell[] ranking;
            public Scene006FinalistSelection.ScoredCell finalist;
            public int f_count;
        }

        [Serializable]
        public sealed class T5RecheckRecord
        {
            public bool equal;
            public string divergence = "";
            public string p1_contract_sha256 = "";
            public string recheck_contract_sha256 = "";
        }

        [Serializable]
        public sealed class T4CandidateRecord
        {
            public string c_hold_source = "p2_cell_c_geom";
            public float c_hold;
            public float best_c_station = float.NaN;
            public int best_station_index = -1;
            public float g_station = float.NaN;
            public float gate_threshold = Scene006Evaluation.T4GainMin;
            public string gate;
            public int station_count;
            public int certificate_pass_count;
            public int body_rejection_count;
            public int tether_rejection_count;
            public int path_rejection_count;
            public string bound_support_instance = "";
            public Scene006Evaluation.StationRecord[] stations;
        }

        [Serializable]
        public sealed class P3Report
        {
            public string schema_version = P3Schema;
            public string work_id = "P1-SCENE-006";
            public int batch = 12; // batch 1c
            public string family = Scene006CandidateContract.FamilyB;
            public string source_scenario_id;
            public string source_scenario_sha256;
            public string road_data_sha256;
            public CaptureIdentity capture;
            public string status;
            public SelectionSection selection;
            public SupportBindingRecord[] support_binding;
            public float finalist_trace_s_init = float.NaN;
            public string finalist_trace_sha256 = "";
            public string finalist_trace_artifact = "";
            public T5RecheckRecord t5_recheck;
            public T4CandidateRecord t4;
            public Scene006Evaluation.T6Record t6;
        }

        // ------------------------------------------------------------
        // Pure guards (unit-tested without a scene)
        // ------------------------------------------------------------

        /// <summary>
        /// BC-B1C-2: for every reviewed in-band cell, the P1 candidate at
        /// the same (anchor, altitude) must be legal and supported by
        /// exactly one instance whose canonical name is one of the two
        /// grass allowlist entries; the P2 legal-altitude list must match
        /// the P1 grid record. Any violation is a mismatch record, never a
        /// silent pass.
        /// </summary>
        public static SupportBindingRecord[] VerifySupportBinding(
            Scene006CandidateGenerator.P1FamilyReport p1,
            Scene006CandidateGenerator.P2FamilyReport p2)
        {
            var records = new List<SupportBindingRecord>();
            var grassNames = new HashSet<string>(
                GrassAllowlist, StringComparer.Ordinal);
            foreach (Scene006CandidateGenerator.P2AnchorRecord anchor
                in p2.anchors)
            {
                foreach (Scene006CandidateEvaluation.CellRecord cell
                    in anchor.cells)
                {
                    if (!cell.gates_in_band) continue;
                    var record = new SupportBindingRecord
                    {
                        anchor_x_m = cell.anchor_x_m,
                        anchor_z_m = cell.anchor_z_m,
                        initial_altitude_m = cell.initial_altitude_m,
                    };
                    records.Add(record);
                    Scene006AnchorPreflight.CandidateRecord candidate = null;
                    foreach (Scene006CandidateGenerator.P1AltitudeReport
                        altitudeReport in p1.altitudes)
                    {
                        if (Mathf.Abs(
                            altitudeReport.altitude_m
                                - cell.initial_altitude_m) > 1e-6f)
                        {
                            continue;
                        }
                        foreach (Scene006AnchorPreflight.CandidateRecord item
                            in altitudeReport.report.candidates)
                        {
                            if (Mathf.Abs(item.x_m - cell.anchor_x_m) <= 1e-6f
                                && Mathf.Abs(item.z_m - cell.anchor_z_m)
                                    <= 1e-6f)
                            {
                                candidate = item;
                                break;
                            }
                        }
                    }
                    bool gridConsistent = false;
                    foreach (Scene006CandidateGenerator.GridAnchorStatus grid
                        in p1.grid_anchors)
                    {
                        if (Mathf.Abs(grid.x_m - cell.anchor_x_m) <= 1e-6f
                            && Mathf.Abs(grid.z_m - cell.anchor_z_m) <= 1e-6f)
                        {
                            gridConsistent = ContainsValue(
                                grid.legal_altitudes_m,
                                cell.initial_altitude_m);
                            break;
                        }
                    }
                    record.p1_p2_binding_consistent = gridConsistent;
                    if (candidate == null)
                    {
                        record.mismatch = "cell anchor missing from P1 lattice";
                        continue;
                    }
                    record.p1_candidate_rank = candidate.rank;
                    record.p1_legal = candidate.legal;
                    record.support_ids = candidate.support_ids
                        ?? Array.Empty<string>();
                    record.single_support = record.support_ids.Length == 1;
                    record.grass_allowlist_match =
                        record.support_ids.Length == 1
                        && grassNames.Contains(
                            SceneVehicleAdjustmentApplier.CanonicalPrefabName(
                                record.support_ids[0]));
                    if (!record.p1_legal)
                        record.mismatch = "P1 candidate is not legal";
                    else if (!record.single_support)
                        record.mismatch =
                            "support does not bind exactly one instance";
                    else if (!record.grass_allowlist_match)
                        record.mismatch =
                            "support instance is not a grass-allowlist name";
                    else if (!record.p1_p2_binding_consistent)
                        record.mismatch = "P1/P2 legal-altitude binding differs";
                    record.ok = record.mismatch == "";
                }
            }
            return records.ToArray();
        }

        static bool ContainsValue(float[] values, float needle)
        {
            foreach (float value in values)
                if (Mathf.Abs(value - needle) <= 1e-6f) return true;
            return false;
        }

        /// <summary>
        /// T5 re-audit equality (§5.3: the P3 re-run must match the P1
        /// altitude report item by item; any difference fails closed).
        /// Float fields compare NaN-aware (round-3 F10): `SupportAt`
        /// legitimately records `support_surface_y_m = NaN` for
        /// `SUPPORT_NOT_FOUND` candidates, and a byte-identical re-run must
        /// compare equal — IEEE `NaN != NaN` would make
        /// `ModeReportsEqual(x, x)` false on every real family-B report.
        /// Both-NaN counts as same; genuinely different values (including
        /// NaN vs finite) still diverge.
        /// </summary>
        public static bool ModeReportsEqual(
            Scene006AnchorPreflight.ModeReport expected,
            Scene006AnchorPreflight.ModeReport actual,
            out string divergence)
        {
            divergence = "";
            if (expected == null || actual == null)
            {
                divergence = "missing report";
                return false;
            }
            if (expected.candidate_count != actual.candidate_count
                || expected.legal_candidate_count
                    != actual.legal_candidate_count
                || expected.support_rejection_count
                    != actual.support_rejection_count
                || expected.clearance_rejection_count
                    != actual.clearance_rejection_count
                || expected.route_rejection_count
                    != actual.route_rejection_count
                || expected.status != actual.status
                || !SameFloat(
                    expected.hover_offset_y_m, actual.hover_offset_y_m))
            {
                divergence = "report-level counts/status differ";
                return false;
            }
            for (int index = 0; index < expected.candidates.Length; index++)
            {
                Scene006AnchorPreflight.CandidateRecord left =
                    expected.candidates[index];
                Scene006AnchorPreflight.CandidateRecord right =
                    actual.candidates[index];
                string where = $"candidate[{index}] "
                    + $"({left.x_m}, {left.z_m})";
                if (left.rank != right.rank)
                {
                    divergence = $"{where}: rank {left.rank} vs {right.rank}";
                    return false;
                }
                (string name, float l, float r)[] floatFields =
                {
                    ("x_m", left.x_m, right.x_m),
                    ("y_m", left.y_m, right.y_m),
                    ("z_m", left.z_m, right.z_m),
                    ("center_distance_m",
                        left.center_distance_m, right.center_distance_m),
                    ("support_surface_y_m",
                        left.support_surface_y_m, right.support_surface_y_m),
                    ("route_distance_m",
                        left.route_distance_m, right.route_distance_m),
                };
                bool floatDiverged = false;
                foreach ((string name, float l, float r) in floatFields)
                {
                    if (SameFloat(l, r)) continue;
                    divergence = $"{where}: {name} {l} vs {r}";
                    floatDiverged = true;
                    break;
                }
                if (floatDiverged) return false;
                (string name, string l, string r)[] stringFields =
                {
                    ("support_status",
                        left.support_status, right.support_status),
                    ("clearance_status",
                        left.clearance_status, right.clearance_status),
                    ("scene003_rejection_reason",
                        left.scene003_rejection_reason ?? "",
                        right.scene003_rejection_reason ?? ""),
                    ("blocking_object",
                        left.blocking_object ?? "",
                        right.blocking_object ?? ""),
                    ("route_gate_status",
                        left.route_gate_status, right.route_gate_status),
                    ("rejection_reason",
                        left.rejection_reason ?? "",
                        right.rejection_reason ?? ""),
                };
                bool stringDiverged = false;
                foreach ((string name, string l, string r) in stringFields)
                {
                    if (l == r) continue;
                    divergence = $"{where}: {name} '{l}' vs '{r}'";
                    stringDiverged = true;
                    break;
                }
                if (stringDiverged) return false;
                if (left.legal != right.legal)
                {
                    divergence = $"{where}: legal {left.legal} vs "
                        + right.legal;
                    return false;
                }
                string[] leftIds = left.support_ids
                    ?? Array.Empty<string>();
                string[] rightIds = right.support_ids
                    ?? Array.Empty<string>();
                if (leftIds.Length != rightIds.Length)
                {
                    divergence = $"{where}: support_ids length "
                        + $"{leftIds.Length} vs {rightIds.Length}";
                    return false;
                }
                for (int id = 0; id < leftIds.Length; id++)
                {
                    if (leftIds[id] != rightIds[id])
                    {
                        divergence = $"{where}: support_ids[{id}] "
                            + $"'{leftIds[id]}' vs '{rightIds[id]}'";
                        return false;
                    }
                }
            }
            return true;
        }

        static bool SameFloat(float left, float right) =>
            left == right || (float.IsNaN(left) && float.IsNaN(right));

        // ------------------------------------------------------------
        // Candidate-mode T4 / T6 (single finalist; both read P2 values)
        // ------------------------------------------------------------

        public static T4CandidateRecord RunCandidateT4(
            Scene006SceneRig rig,
            Scene006Trace.State[] trace,
            Vector3 anchor,
            float supportY,
            float altitudeM,
            float verticalFovDeg,
            Scene006PathCertificate.ObstaclePrism[] obstacles,
            string boundSupportInstance,
            float cHoldFromP2)
        {
            rig.EvaluationCamera.fieldOfView = verticalFovDeg;
            Vector3 pHover = Scene006StationSet.HoverPosition(
                anchor, supportY, altitudeM);
            Scene006StationSet.Station[] stations = Scene006StationSet.Build(
                anchor, supportY, altitudeM);
            var record = new T4CandidateRecord
            {
                c_hold = cHoldFromP2,
                station_count = stations.Length,
                bound_support_instance = boundSupportInstance ?? "",
            };
            var stationRecords =
                new Scene006Evaluation.StationRecord[stations.Length];
            float best = float.NegativeInfinity;
            for (int index = 0; index < stations.Length; index++)
            {
                Scene006StationSet.Station station = stations[index];
                Scene006PathCertificate.Certificate certificate =
                    Scene006PathCertificate.Evaluate(
                        anchor,
                        pHover,
                        supportY,
                        station.World,
                        obstacles,
                        boundSupportInstance);
                stationRecords[index] = new Scene006Evaluation.StationRecord
                {
                    index = index,
                    height_agl_m = station.HeightAglM,
                    world_m = new Scene006Evaluation.Vec3
                    {
                        x = station.World.x,
                        y = station.World.y,
                        z = station.World.z,
                    },
                    is_hover = station.IsHover,
                    certificate = new Scene006Evaluation.CertificateRecord
                    {
                        passed = certificate.Passed,
                        path_rejected = certificate.PathRejected,
                        body_rejected = certificate.BodyRejected,
                        tether_rejected = certificate.TetherRejected,
                        blocking_obstacle = certificate.BlockingObstacle,
                        duration_s = certificate.DurationSeconds,
                        sample_count = certificate.SampleCount,
                    },
                };
                if (certificate.BodyRejected) record.body_rejection_count++;
                if (certificate.TetherRejected) record.tether_rejection_count++;
                if (certificate.PathRejected) record.path_rejection_count++;
                // §5.4.5: certificate failures never enter max_p.
                if (!certificate.Passed) continue;
                record.certificate_pass_count++;
                float cStation = ReplayCoverage(
                    rig, trace, station.World);
                stationRecords[index].c_station = cStation;
                if (cStation > best)
                {
                    best = cStation;
                    record.best_station_index = index;
                }
            }
            record.stations = stationRecords;
            if (record.best_station_index >= 0)
            {
                record.best_c_station = best;
                record.g_station = best - cHoldFromP2;
            }
            record.gate = record.best_station_index >= 0
                && record.g_station >= Scene006Evaluation.T4GainMin
                ? "PASS" : "FAIL";
            return record;
        }

        public static Scene006Evaluation.T6Record RunCandidateT6(
            Scene006SceneRig rig,
            Scene006Trace.State[] trace,
            Vector3 pHover,
            float p2DomainMedianPx,
            int imageWidth,
            int imageHeight)
        {
            var window = new Scene006Evaluation.T6SampleRecord[
                Scene006Evaluation.T6AcquisitionWindow + 1];
            int kStar = -1;
            float promptMinSide = float.NaN;
            Quaternion gimbal = Scene006GimbalReplay.InitialRotation;
            for (int k = 0; k <= Scene006Evaluation.T6AcquisitionWindow; k++)
            {
                Scene006Trace.State state = trace[k];
                rig.TargetReplica.transform.SetPositionAndRotation(
                    state.Position, state.Rotation);
                if (k >= 1)
                {
                    gimbal = Scene006GimbalReplay.Update(
                        gimbal, pHover, state.Position);
                }
                rig.EvaluationCamera.transform.SetPositionAndRotation(
                    pHover, gimbal);
                Bounds bounds = rig.TargetRenderers[0].bounds;
                for (int index = 1; index < rig.TargetRenderers.Length; index++)
                    bounds.Encapsulate(rig.TargetRenderers[index].bounds);
                Vector3[] corners = Scene006Visibility.BoundsCorners(bounds);
                Scene006Visibility.Snapshot snapshot =
                    Scene006Visibility.Evaluate(
                        rig.EvaluationCamera,
                        bounds,
                        corners,
                        (origin, point) =>
                            Scene006Visibility.HasClearLineOfSight(
                                origin, point, rig.TargetReplica.transform));
                NormalizedBoundingBox box = Scene006Visibility.ProjectBounds(
                    rig.EvaluationCamera, corners);
                float minSide = box == null
                    ? float.NaN
                    : Scene006Visibility.MinSidePx(
                        box,
                        imageWidth,
                        imageHeight);
                window[k] = new Scene006Evaluation.T6SampleRecord
                {
                    k = k,
                    frustum_visible = snapshot.FrustumVisible,
                    geometrically_visible = snapshot.GeometricallyVisible,
                    min_side_px = minSide,
                };
                if (kStar < 0 && snapshot.GeometricallyVisible)
                {
                    kStar = k;
                    promptMinSide = minSide;
                }
            }
            var record = new Scene006Evaluation.T6Record
            {
                k_star = kStar,
                prompt_min_side_px = promptMinSide,
                t1_domain_median_px = p2DomainMedianPx,
                samples = window,
            };
            if (kStar >= 0 && !Scene006RouteGeometry.Finite(promptMinSide))
            {
                record.gate = "PROBE_FIDELITY_CONTRADICTION";
            }
            else
            {
                record.gate = kStar >= 0
                    && Scene006RouteGeometry.Finite(promptMinSide)
                    && promptMinSide >= p2DomainMedianPx
                    ? "PASS" : "FAIL";
            }
            return record;
        }

        static float ReplayCoverage(
            Scene006SceneRig rig,
            Scene006Trace.State[] trace,
            Vector3 bodyPosition)
        {
            Quaternion gimbal = Scene006GimbalReplay.InitialRotation;
            int visible = 0;
            for (int k = 1; k < trace.Length; k++)
            {
                Scene006Trace.State state = trace[k];
                rig.TargetReplica.transform.SetPositionAndRotation(
                    state.Position, state.Rotation);
                gimbal = Scene006GimbalReplay.Update(
                    gimbal, bodyPosition, state.Position);
                rig.EvaluationCamera.transform.SetPositionAndRotation(
                    bodyPosition, gimbal);
                Bounds bounds = rig.TargetRenderers[0].bounds;
                for (int index = 1; index < rig.TargetRenderers.Length; index++)
                    bounds.Encapsulate(rig.TargetRenderers[index].bounds);
                Scene006Visibility.Snapshot snapshot =
                    Scene006Visibility.Evaluate(
                        rig.EvaluationCamera,
                        bounds,
                        Scene006Visibility.BoundsCorners(bounds),
                        (origin, point) =>
                            Scene006Visibility.HasClearLineOfSight(
                                origin, point, rig.TargetReplica.transform));
                if (snapshot.GeometricallyVisible) visible++;
            }
            return visible / 540f;
        }

        // ------------------------------------------------------------
        // Orchestration (runs only after the C_tool′ review passes)
        // ------------------------------------------------------------

        public static void RunBatch1c()
        {
            try
            {
                RunBatch1cInner();
            }
            catch (Exception exception)
            {
                UnityEngine.Debug.LogException(exception);
                EditorApplication.Exit(1);
            }
        }

        static void RunBatch1cInner()
        {
            CaptureIdentity identity = CaptureIdentityRecord();
            ScenarioConfig config = Scene006SceneRig.LoadFrozenScenario(
                out string scenarioSha256);
            var report = new P3Report
            {
                source_scenario_id = config.scenario_id,
                source_scenario_sha256 = scenarioSha256,
                road_data_sha256 = config.road_data_sha256,
            };

            // Bind the reviewed batch-1b inputs by content hash (BC-B1C-1).
            string p1Json = File.ReadAllText(
                RuntimePaths.ProjectFile(P1ArtifactPath.Split('/')));
            string p2Json = File.ReadAllText(
                RuntimePaths.ProjectFile(P2ArtifactPath.Split('/')));
            Scene006CandidateGenerator.P1FamilyReport p1 =
                JsonUtility.FromJson<Scene006CandidateGenerator.P1FamilyReport>(
                    p1Json);
            Scene006CandidateGenerator.P2FamilyReport p2 =
                JsonUtility.FromJson<Scene006CandidateGenerator.P2FamilyReport>(
                    p2Json);
            if (p1 == null || p2 == null
                || p1.schema_version != "p1-scene-006-p1/v1"
                || p2.schema_version != "p1-scene-006-p2/v1"
                || p1.family != Scene006CandidateContract.FamilyB
                || p2.family != Scene006CandidateContract.FamilyB
                || p1.status != "P1_OK"
                || p2.status != "P2_OK")
            {
                throw new InvalidOperationException(
                    "reviewed P1/P2 family-B artifacts are missing, "
                    + "malformed or not in their P1_OK/P2_OK state");
            }

            // §5.4 frozen selection over the reviewed in-band cells.
            var inputs = new List<Scene006FinalistSelection.CellInput>();
            foreach (Scene006CandidateGenerator.P2AnchorRecord anchor
                in p2.anchors)
            {
                foreach (Scene006CandidateEvaluation.CellRecord cell
                    in anchor.cells)
                {
                    if (!cell.gates_in_band) continue;
                    inputs.Add(new Scene006FinalistSelection.CellInput
                    {
                        Family = cell.family,
                        AnchorX = cell.anchor_x_m,
                        AnchorZ = cell.anchor_z_m,
                        AltitudeM = cell.initial_altitude_m,
                        VerticalFovDeg = cell.vertical_fov_deg,
                        SInit = cell.s_init,
                        TraceSha256 = cell.trace_sha256,
                        LPoint = cell.l_point,
                        LOcc = cell.l_occ,
                        TotalLoss = cell.total_loss,
                        MinSideP05Px = cell.t1_min_side_p05_px,
                    });
                }
            }
            Scene006FinalistSelection.SelectionResult selection =
                Scene006FinalistSelection.Select(inputs);
            report.selection = new SelectionSection
            {
                p1_artifact = Bind(P1ArtifactPath),
                p2_artifact = Bind(P2ArtifactPath),
                ranking = selection.Table.ToArray(),
                finalist = selection.Finalist,
                f_count = selection.Ordered.Count,
            };
            if (selection.Status == "BLOCKED_GEOMETRY_INFEASIBLE")
            {
                report.status = "BLOCKED_GEOMETRY_INFEASIBLE";
                StampAndWrite(report, identity);
                return;
            }
            Scene006FinalistSelection.ScoredCell finalist =
                selection.Finalist;

            // BC-B1C-2 before any P3 gate value.
            report.support_binding = VerifySupportBinding(p1, p2);
            foreach (SupportBindingRecord record in report.support_binding)
            {
                if (record.ok) continue;
                report.status = "SUPPORT_SEMANTICS_MISMATCH";
                StampAndWrite(report, identity);
                return;
            }

            // Finalist cell (P2 authoritative values for T4/T6 inputs).
            Scene006CandidateEvaluation.CellRecord finalistCell = null;
            foreach (Scene006CandidateGenerator.P2AnchorRecord anchor
                in p2.anchors)
            {
                foreach (Scene006CandidateEvaluation.CellRecord cell
                    in anchor.cells)
                {
                    if (cell.gates_in_band
                        && Mathf.Abs(cell.anchor_x_m - finalist.anchor_x_m)
                            <= 1e-6f
                        && Mathf.Abs(cell.anchor_z_m - finalist.anchor_z_m)
                            <= 1e-6f
                        && Mathf.Abs(
                            cell.initial_altitude_m
                                - finalist.initial_altitude_m) <= 1e-6f
                        && Mathf.Abs(
                            cell.vertical_fov_deg
                                - finalist.vertical_fov_deg) <= 1e-6f)
                    {
                        finalistCell = cell;
                    }
                }
            }
            if (finalistCell == null)
                throw new InvalidOperationException(
                    "finalist cell missing from the reviewed P2 artifact");

            var rig = new Scene006SceneRig
            {
                Config = config,
                ScenarioSha256 = scenarioSha256,
            };
            try
            {
                rig.OpenCityScene();
                rig.ApplySceneAdjustments();
                ApplyFamilyBRelocationsForP3();
                rig.LoadRoadData();
                rig.CreateTargetReplica();
                rig.CreateEvaluationCamera(
                    finalist.vertical_fov_deg,
                    config.sensor.width,
                    config.sensor.height);
                rig.CollectStaticRoots(rig.TargetReplica.transform);
                rig.BuildOcclusionProxies();
                identity.scene_state_sha256 = SceneStateHash(rig);

                Vector3[] route = Scene006CandidateContract.FamilyRoute(
                    Scene006CandidateContract.FamilyB, config.TargetRoute());
                Scene006Trace.State[] trace = Scene006Trace.Generate(
                    route, config.target.speed_mps, finalist.s_init);
                string traceSha = Scene006Trace.HashStates(trace);
                report.finalist_trace_s_init = finalist.s_init;
                report.finalist_trace_sha256 = traceSha;
                report.finalist_trace_artifact = finalistCell.trace_artifact;
                if (traceSha != finalistCell.trace_sha256)
                {
                    report.status = "TRACE_BINDING_MISMATCH";
                    StampAndWrite(report, identity);
                    return;
                }

                // T5 re-audit at the finalist altitude: must equal the P1
                // altitude report item by item (§5.3).
                Scene006AnchorPreflight.ModeReport expectedP1 = null;
                foreach (Scene006CandidateGenerator.P1AltitudeReport
                    altitudeReport in p1.altitudes)
                {
                    if (Mathf.Abs(
                        altitudeReport.altitude_m
                            - finalist.initial_altitude_m) <= 1e-6f)
                    {
                        expectedP1 = altitudeReport.report;
                    }
                }
                Scene006AnchorPreflight.ModeReport recheck =
                    Scene006AnchorPreflight.RunMode(
                        Scene006AnchorPreflight.ModeCandidatePreflight,
                        config,
                        scenarioSha256,
                        rig.RoadData,
                        rig.StaticRoots,
                        new Vector3(
                            Scene006CandidateContract.FamilyBCenter.x,
                            0f,
                            Scene006CandidateContract.FamilyBCenter.y),
                        finalist.initial_altitude_m,
                        route);
                bool equal = ModeReportsEqual(
                    expectedP1, recheck, out string divergence);
                report.t5_recheck = new T5RecheckRecord
                {
                    equal = equal,
                    divergence = divergence,
                    p1_contract_sha256 =
                        expectedP1.anchor_contract_sha256,
                    recheck_contract_sha256 =
                        recheck.anchor_contract_sha256,
                };
                if (!equal)
                {
                    report.status = "T5_RECHECK_DIVERGENCE";
                    StampAndWrite(report, identity);
                    return;
                }

                string boundSupport = "";
                float supportY = float.NaN;
                foreach (SupportBindingRecord record in report.support_binding)
                {
                    if (Mathf.Abs(record.anchor_x_m - finalist.anchor_x_m)
                            <= 1e-6f
                        && Mathf.Abs(record.anchor_z_m - finalist.anchor_z_m)
                            <= 1e-6f
                        && Mathf.Abs(
                            record.initial_altitude_m
                                - finalist.initial_altitude_m) <= 1e-6f)
                    {
                        boundSupport = record.support_ids[0];
                    }
                }
                foreach (Scene006CandidateGenerator.GridAnchorStatus grid
                    in p1.grid_anchors)
                {
                    if (Mathf.Abs(grid.x_m - finalist.anchor_x_m) <= 1e-6f
                        && Mathf.Abs(grid.z_m - finalist.anchor_z_m) <= 1e-6f)
                    {
                        supportY = grid.support_y_m;
                    }
                }
                if (boundSupport == "" || !Scene006RouteGeometry.Finite(supportY))
                    throw new InvalidOperationException(
                        "finalist support binding incomplete");

                var anchor = new Vector3(
                    finalist.anchor_x_m, supportY, finalist.anchor_z_m);
                Scene006PathCertificate.ObstaclePrism[] obstacles =
                    rig.BuildAllInstancePrisms(GrassAllowlist);
                report.t4 = RunCandidateT4(
                    rig,
                    trace,
                    anchor,
                    supportY,
                    finalist.initial_altitude_m,
                    finalist.vertical_fov_deg,
                    obstacles,
                    boundSupport,
                    finalistCell.c_geom);
                Vector3 pHover = Scene006StationSet.HoverPosition(
                    anchor, supportY, finalist.initial_altitude_m);
                report.t6 = RunCandidateT6(
                    rig,
                    trace,
                    pHover,
                    finalistCell.t1_min_side_median_px,
                    config.sensor.width,
                    config.sensor.height);
                report.status = report.t4.gate == "PASS"
                    && report.t6.gate == "PASS"
                    ? "P3_OK"
                    : "BLOCKED_FINALIST_AUDIT_FAILED";
                StampAndWrite(report, identity);
                UnityEngine.Debug.Log(
                    $"[SCENE-006] batch 1c: finalist "
                    + $"({finalist.anchor_x_m}, {finalist.anchor_z_m}) "
                    + $"h={finalist.initial_altitude_m} "
                    + $"vfov={finalist.vertical_fov_deg} "
                    + $"score={finalist.score}; T4 {report.t4.gate} "
                    + $"(G {report.t4.g_station:F4}), T6 {report.t6.gate} "
                    + $"(k* {report.t6.k_star}) -> {report.status}");
            }
            finally
            {
                rig.Cleanup();
            }
        }

        static ArtifactBinding Bind(string projectRelativePath)
        {
            return new ArtifactBinding
            {
                path = projectRelativePath,
                sha256 = Scene006RouteGeometry.Sha256Hex(
                    File.ReadAllBytes(
                        RuntimePaths.ProjectFile(
                            projectRelativePath.Split('/')))),
            };
        }

        static void ApplyFamilyBRelocationsForP3()
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
            // §5.6 ④: P3 captures on the reviewed C_tool′, so the two
            // identity fields coincide by construction.
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

        static void StampAndWrite(P3Report report, CaptureIdentity identity)
        {
            string after = SceneFileHash();
            if (after != identity.scene_file_sha256_before)
            {
                throw new InvalidOperationException(
                    "scene file changed during capture; the zero-write "
                    + "contract is violated");
            }
            report.capture = new CaptureIdentity
            {
                capture_commit = identity.capture_commit,
                tool_commit = identity.tool_commit,
                git_status_porcelain = identity.git_status_porcelain,
                scene_state_sha256 = identity.scene_state_sha256,
                scene_file_sha256_before =
                    identity.scene_file_sha256_before,
                scene_file_sha256_after = after,
                scene_saved = false,
            };
            AtomicFile.WriteAllText(
                RuntimePaths.ProjectFile(P3ArtifactPath.Split('/')),
                JsonUtility.ToJson(report, true) + "\n");
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
            var startInfo = new System.Diagnostics.ProcessStartInfo(
                "git", arguments)
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
    }
}
