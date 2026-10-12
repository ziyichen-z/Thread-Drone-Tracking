using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// §5.5 T5 safety audit for P1-SCENE-006, built on the reviewed
    /// P1-SCENE-003 anchor auditor with the §5.5 parameter contract:
    ///
    /// * support allowlist ["Natures_Grass Tile", "Natures_Grass Tile
    ///   Small"] with +/-0.05 m tolerance (inherited);
    /// * candidate anchor y is requested at 0.0, not the retired 0.2 — the
    ///   authoritative per-candidate support height is the auditor-measured
    ///   support_surface_y_m recorded per candidate (support y is derived
    ///   from the measured surface, never carried over);
    /// * ground_plane_y_m = 0.2000004 stays frozen as the vehicle driving
    ///   plane / LOS calibration plane and is recorded separately from the
    ///   anchor support y (two different quantities);
    /// * anchor column 1.0 + 0.5 m, vertical tether corridor 0.5 + 0.5 = 1.0
    ///   m effective radius from the support surface to the hover height,
    ///   participation band [support_y, hover_y + 1.5 m], hover sphere
    ///   1.0 + 0.5 m at the 20.0 m hover point — all evaluated by the
    ///   inherited auditor with hover_offset_y_m = 20.0;
    /// * obstacle set: every active static root through its real TRS,
    ///   fail-closed on unsupported TRS; exclusions are exactly the support
    ///   allowlist and road-surface instances;
    /// * support verdict: strict interior (half_extent - 1e-5), zero hits
    ///   fail closed, multi-hit height conflict fails closed; closed-set
    ///   tangency is a violation;
    /// * candidate lattice: step 0.5 m, radius &lt;= 10 m, ordered by
    ///   distance then x then z, centred on the requested ring centre;
    /// * NEW route-anchor sub-gate: minimum horizontal distance from the
    ///   candidate to the frozen target route must be &gt;= 1.5 m;
    /// * road/vehicle swept corridor stays zero-violation (inherited: the
    ///   route is unchanged, so the frozen SCENE-002 verdict carries; the
    ///   preflight itself moves nothing).
    ///
    /// Candidate-lattice disposition (§5.5, R18): if every candidate is
    /// rejected the report status is BLOCKED_ANCHOR_PLACEMENT_V2, which
    /// returns to design; no batch-2 GO may be requested on that outcome.
    /// The current-anchor baseline run has no V2 semantics and reports its
    /// own counts honestly.
    /// </summary>
    public static class Scene006AnchorPreflight
    {
        public const string ModeCandidatePreflight = "candidate_preflight";
        public const string ModeCurrentAnchorBaseline = "current_anchor_baseline";
        public const float RouteDistanceMinM = 1.5f;
        public const float GroundPlaneYM = 0.2000004f;
        public const float CandidateHoverOffsetM = 20.0f;

        public static readonly string[] SupportAllowlist =
            { "Natures_Grass Tile", "Natures_Grass Tile Small" };

        [Serializable]
        public sealed class CandidateRecord
        {
            public int rank;
            public float x_m;
            public float y_m;
            public float z_m;
            public float center_distance_m;
            public string[] support_ids;
            public float support_surface_y_m;
            public string support_status;
            public string clearance_status;
            public string scene003_rejection_reason;
            public string blocking_object;
            public float route_distance_m;
            public string route_gate_status;
            public string rejection_reason;
            // F4 (schema v2): computed pre-serialization so consumers never
            // re-derive legality from string fields. JsonUtility flattens
            // null strings to "", so the string fields above use "" as the
            // no-value convention; `legal` is the authoritative boolean.
            public bool legal;
        }

        [Serializable]
        public sealed class ModeReport
        {
            public string mode;
            public string status;
            public Scene006Evaluation.Vec3 requested_anchor_world_m;
            public float hover_offset_y_m;
            public string[] support_surface_allowlist;
            public string anchor_contract_sha256;
            public int candidate_count;
            public int support_rejection_count;
            public int clearance_rejection_count;
            public int route_rejection_count;
            public int legal_candidate_count;
            public CandidateRecord[] candidates;
        }

        [Serializable]
        public sealed class PreflightReport
        {
            // v2 (F4): per-candidate `legal` boolean added; the string
            // fields rejection_reason / blocking_object /
            // scene003_rejection_reason keep "" as the documented no-value
            // convention (JsonUtility flattens null to ""). The frozen
            // batch-1 artifact stays v1 and is never regenerated.
            public string schema_version = "p1-scene-006-anchor-preflight/v2";
            public string work_id = "P1-SCENE-006";
            public int batch = 1;
            public string source_scenario_id;
            public string source_scenario_sha256;
            public string road_data_sha256;
            public float ground_plane_y_m = GroundPlaneYM;
            public float route_distance_min_m = RouteDistanceMinM;
            public string contract_json_sha256;
            public ModeReport candidate_preflight;
            public ModeReport current_anchor_baseline;
        }

        public static P1Scene003AnchorPlacementContract BuildContract(
            Vector3 requested,
            float hoverOffsetM)
        {
            var contract = new P1Scene003AnchorPlacementContract
            {
                schema_version = P1Scene003AnchorPlacementContract.Schema,
                work_id = P1Scene003AnchorPlacementContract.WorkId,
                requested_anchor_world_m = new ScenarioVector3(
                    requested.x, requested.y, requested.z),
                hover_offset_y_m = hoverOffsetM,
                support_surface_allowlist = SupportAllowlist.ToArray(),
                support_height_tolerance_m = 0.05f,
                anchor_nominal_radius_m = 1.0f,
                hover_nominal_radius_m = 1.0f,
                corridor_nominal_radius_m = 0.5f,
                clearance_margin_m = 0.5f,
                lattice_step_m = 0.5f,
                lattice_radius_m = 10.0f,
            };
            contract.Validate();
            return contract;
        }

        public static string ContractSha256(
            P1Scene003AnchorPlacementContract contract)
        {
            string json = JsonUtility.ToJson(contract, true) + "\n";
            return Scene006RouteGeometry.Sha256Hex(
                Encoding.UTF8.GetBytes(json));
        }

        public static ModeReport RunMode(
            string mode,
            ScenarioConfig scenario,
            string scenarioSha256,
            RoadSceneData roadData,
            IEnumerable<Transform> sceneRoots,
            Vector3 requested,
            float hoverOffsetM,
            IReadOnlyList<Vector3> route)
        {
            P1Scene003AnchorPlacementContract contract =
                BuildContract(requested, hoverOffsetM);
            string contractSha = ContractSha256(contract);
            P1Scene003AnchorAuditReport audit = P1Scene003AnchorAuditor.Audit(
                scenario,
                scenarioSha256,
                roadData,
                sceneRoots,
                contract,
                contractSha);

            var candidates = new CandidateRecord[audit.candidates.Length];
            int routeRejections = 0;
            for (int index = 0; index < audit.candidates.Length; index++)
            {
                P1Scene003AnchorCandidateAudit source = audit.candidates[index];
                float routeDistance = Scene006RouteGeometry.DistanceToClosedRoute(
                    new Vector2(source.x_m, source.z_m), route);
                bool routePass =
                    routeDistance >= RouteDistanceMinM - 1e-5f;
                if (!routePass) routeRejections++;
                string combined = source.rejection_reason;
                if (combined == null && !routePass)
                    combined = "ROUTE_ANCHOR_DISTANCE";
                candidates[index] = new CandidateRecord
                {
                    rank = source.rank,
                    x_m = source.x_m,
                    y_m = source.y_m,
                    z_m = source.z_m,
                    center_distance_m = source.center_distance_m,
                    support_ids = source.support_ids,
                    support_surface_y_m = source.support_surface_y_m,
                    support_status = source.support_status,
                    clearance_status = source.clearance_status,
                    scene003_rejection_reason = source.rejection_reason,
                    blocking_object = source.blocking_object,
                    route_distance_m = routeDistance,
                    route_gate_status = routePass ? "PASS" : "FAIL",
                    rejection_reason = combined,
                    legal = combined == null,
                };
            }
            int legal = candidates.Count(item => item.legal);
            string status;
            if (mode == ModeCandidatePreflight)
            {
                status = legal == 0
                    ? "BLOCKED_ANCHOR_PLACEMENT_V2"
                    : "CANDIDATES_AVAILABLE";
            }
            else
            {
                status = legal == 0
                    ? "BASELINE_ALL_REJECTED"
                    : "BASELINE_CLEAR";
            }
            return new ModeReport
            {
                mode = mode,
                status = status,
                requested_anchor_world_m = new Scene006Evaluation.Vec3
                {
                    x = requested.x,
                    y = requested.y,
                    z = requested.z,
                },
                hover_offset_y_m = hoverOffsetM,
                support_surface_allowlist = SupportAllowlist.ToArray(),
                anchor_contract_sha256 = contractSha,
                candidate_count = candidates.Length,
                support_rejection_count = candidates.Count(
                    item => item.support_status != "PASS"),
                clearance_rejection_count = candidates.Count(
                    item => item.support_status == "PASS"
                        && item.clearance_status != "PASS"),
                route_rejection_count = routeRejections,
                legal_candidate_count = legal,
                candidates = candidates,
            };
        }
    }
}
