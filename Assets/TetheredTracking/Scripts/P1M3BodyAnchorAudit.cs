using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;

namespace TetheredTracking
{
    /// <summary>
    /// P1-M3-BODY-001 batch 1a-alpha tool 1 contract: the never-performed
    /// support/clearance audit for the <b>main-loop</b> anchor
    /// <c>(132, 0.2, 117)</c> (BC-M34-4 (c), BC-BODY1-3 hard gate 1).
    ///
    /// Two deliberate differences from the SCENE-003/SCENE-004 contracts:
    ///
    /// * There is <b>no lattice</b>. The accepted proposal freezes the anchor
    ///   (<c>P1-M3-BODY-001</c> section 5.1: anchor <c>(132,117)</c> does not
    ///   move), so this is a verdict on one declared position, not a search
    ///   for a legal one. A relocation would be a scene-design change and is
    ///   out of this work ID's scope.
    /// * The anchor elevation is <b>declared</b> by the frozen scenario and
    ///   checked against the measured support surface. SCENE-004 derived the
    ///   elevation because it was authoring a new anchor; here the scenario
    ///   bytes already exist and the audit's job is to say whether they are
    ///   supported.
    ///
    /// Every safety value below is byte-identical to the two prior accepted
    /// anchor contracts (<c>config/p1-scene-003-anchor-placement.json</c> and
    /// <c>config/p1-scene-004-anchor-placement.json</c>): hover offset 25 m,
    /// support tolerance 0.05 m, anchor/hover nominal radius 1.0 m, corridor
    /// nominal radius 0.5 m, clearance margin 0.5 m. No new safety value is
    /// proposed by this batch (BC-BODY1-10 requests no user authorization),
    /// and the corridor radius pair matches the proposal section 3.5
    /// pre-registration (0.5 + 0.5 = 1.0 m).
    /// </summary>
    [Serializable]
    public sealed class P1M3BodyAnchorPlacementContract
    {
        public const string Schema = "p1-m3-body-001-anchor-placement/v1";
        public const string WorkId = "P1-M3-BODY-001";
        public const string FileName = "p1-m3-body-001-anchor-placement.json";

        public string schema_version;
        public string work_id;
        public ScenarioVector3 audited_anchor_world_m;
        public float hover_offset_y_m = float.NaN;
        public string[] support_surface_allowlist;
        public float support_height_tolerance_m = float.NaN;
        public float anchor_nominal_radius_m = float.NaN;
        public float hover_nominal_radius_m = float.NaN;
        public float corridor_nominal_radius_m = float.NaN;
        public float clearance_margin_m = float.NaN;

        public Vector3 AuditedAnchor => audited_anchor_world_m.Value;
        public float AnchorEffectiveRadius =>
            anchor_nominal_radius_m + clearance_margin_m;
        public float HoverEffectiveRadius =>
            hover_nominal_radius_m + clearance_margin_m;
        public float CorridorEffectiveRadius =>
            corridor_nominal_radius_m + clearance_margin_m;

        public void Validate()
        {
            if (schema_version != Schema || work_id != WorkId)
                throw new InvalidOperationException(
                    "invalid_p1_m3_body_anchor_contract_identity");
            if (audited_anchor_world_m == null)
                throw new InvalidOperationException(
                    "missing_p1_m3_body_audited_anchor");
            RequireFinite(AuditedAnchor, "audited_anchor_world_m");
            RequirePositive(hover_offset_y_m, "hover_offset_y_m");
            RequirePositive(
                support_height_tolerance_m,
                "support_height_tolerance_m");
            RequirePositive(anchor_nominal_radius_m, "anchor_nominal_radius_m");
            RequirePositive(hover_nominal_radius_m, "hover_nominal_radius_m");
            RequirePositive(
                corridor_nominal_radius_m,
                "corridor_nominal_radius_m");
            RequireNonNegative(clearance_margin_m, "clearance_margin_m");
            if (support_surface_allowlist == null
                || support_surface_allowlist.Length == 0)
            {
                throw new InvalidOperationException(
                    "support_surface_allowlist must not be empty");
            }
            string[] normalized = support_surface_allowlist
                .Select(item => item?.Trim())
                .ToArray();
            if (normalized.Any(string.IsNullOrEmpty)
                || normalized.Distinct(StringComparer.Ordinal).Count()
                    != normalized.Length)
            {
                throw new InvalidOperationException(
                    "support_surface_allowlist contains blank or duplicate names");
            }
            support_surface_allowlist = normalized;
        }

        static void RequireFinite(Vector3 value, string label)
        {
            if (!Finite(value.x) || !Finite(value.y) || !Finite(value.z))
                throw new InvalidOperationException(label + " must be finite");
        }

        static void RequirePositive(float value, string label)
        {
            if (!Finite(value) || value <= 0f)
                throw new InvalidOperationException(label + " must be positive");
        }

        static void RequireNonNegative(float value, string label)
        {
            if (!Finite(value) || value < 0f)
                throw new InvalidOperationException(
                    label + " must be non-negative");
        }

        static bool Finite(float value) =>
            !float.IsNaN(value) && !float.IsInfinity(value);
    }

    public static class P1M3BodyAnchorPlacementContractLoader
    {
        public static string ProjectPath =>
            RuntimePaths.ProjectFile(
                "config",
                P1M3BodyAnchorPlacementContract.FileName);

        public static P1M3BodyAnchorPlacementContract Load(
            out string sha256,
            string path = null)
        {
            string resolved = path ?? ProjectPath;
            if (!File.Exists(resolved))
                throw new FileNotFoundException(
                    "missing_p1_m3_body_anchor_contract",
                    resolved);
            byte[] bytes = File.ReadAllBytes(resolved);
            sha256 = Sha256(bytes);
            P1M3BodyAnchorPlacementContract contract;
            try
            {
                contract = JsonUtility.FromJson<P1M3BodyAnchorPlacementContract>(
                    Encoding.UTF8.GetString(bytes));
            }
            catch (Exception exception)
            {
                throw new InvalidOperationException(
                    "invalid_p1_m3_body_anchor_contract_json",
                    exception);
            }
            if (contract == null)
                throw new InvalidOperationException(
                    "empty_p1_m3_body_anchor_contract");
            contract.Validate();
            return contract;
        }

        public static string Sha256(byte[] bytes)
        {
            if (bytes == null) throw new ArgumentNullException(nameof(bytes));
            using SHA256 sha = SHA256.Create();
            return string.Concat(
                sha.ComputeHash(bytes).Select(value => value.ToString("x2")));
        }
    }

    [Serializable]
    public sealed class P1M3BodyAnchorSupportMatch
    {
        public string id;
        public string source;
        public float surface_y_m;
    }

    [Serializable]
    public sealed class P1M3BodyAnchorBlocker
    {
        public string scene_object_name;
        public string canonical_name;
        public string group;
        public string reason;
        public float horizontal_distance_m;
        public float obstacle_min_y_m;
        public float obstacle_max_y_m;
        public bool anchor_cylinder;
        public bool corridor_cylinder;
        public bool hover_sphere;
    }

    [Serializable]
    public sealed class P1M3BodyAnchorAuditReport
    {
        public string schema_version = "p1-m3-body-001-anchor-audit/v1";
        public string work_id = P1M3BodyAnchorPlacementContract.WorkId;
        public string status;
        public string rejection_reason;
        public string source_scenario_id;
        public string source_scenario_sha256;
        public string road_data_sha256;
        public string anchor_contract_sha256;
        public ScenarioVector3 audited_anchor_world_m;
        public ScenarioVector3 hover_point_world_m;
        public float anchor_effective_radius_m = float.NaN;
        public float hover_effective_radius_m = float.NaN;
        public float corridor_effective_radius_m = float.NaN;
        public string support_status;
        public string clearance_status;
        public float support_surface_y_m = float.NaN;
        public float support_height_error_m = float.NaN;
        public P1M3BodyAnchorSupportMatch[] support_matches;
        public int scene_root_count;
        public int audited_obstacle_count;
        public int blocker_count;
        public P1M3BodyAnchorBlocker[] blockers;
        // Disclosed diagnostic, never a gate: the accepted audit is
        // support + clearance only (BC-M34-4 (c)). See the evidence file.
        public float route_centerline_distance_m = float.NaN;
        public float route_corridor_half_width_m = float.NaN;
        public string[] support_surface_allowlist;
    }

    /// <summary>
    /// Single-position support/clearance audit for the frozen main-loop
    /// anchor. Geometry primitives come from
    /// <see cref="P1Scene003AnchorAuditor"/> unchanged (proposal section 5.2:
    /// "reuse the SCENE-003 primitives, build nothing new"), so this audit
    /// cannot drift away from the two that came before it.
    ///
    /// One reporting difference from SCENE-003: that auditor returned on the
    /// first blocking object because it was ranking 1,257 lattice candidates
    /// and only needed the first legal one. Here there is exactly one
    /// position and a FAIL stops the whole batch, so <b>every</b> blocker is
    /// collected and reported. The verdict is unchanged - any blocker is a
    /// FAIL - and no gate is loosened.
    /// </summary>
    public static class P1M3BodyAnchorAuditor
    {
        const float GeometryEpsilon = P1Scene003AnchorAuditor.GeometryEpsilon;

        public const string StatusClear = "CLEAR";
        public const string StatusFailed = "ANCHOR_PLACEMENT_AUDIT_FAILED";

        public static P1M3BodyAnchorAuditReport Audit(
            ScenarioConfig scenario,
            string scenarioSha256,
            RoadSceneData roadData,
            IEnumerable<Transform> sceneRoots,
            P1M3BodyAnchorPlacementContract contract,
            string contractSha256)
        {
            if (scenario == null) throw new ArgumentNullException(nameof(scenario));
            if (roadData == null) throw new ArgumentNullException(nameof(roadData));
            if (sceneRoots == null) throw new ArgumentNullException(nameof(sceneRoots));
            if (contract == null) throw new ArgumentNullException(nameof(contract));
            if (!RateStudyProtocol.IsSha256(scenarioSha256)
                || !RateStudyProtocol.IsSha256(contractSha256))
            {
                throw new InvalidOperationException(
                    "anchor audit inputs need lowercase SHA-256 identities");
            }
            contract.Validate();
            roadData.Validate();
            RequireScenarioAgreement(scenario, contract);

            Transform[] roots = sceneRoots
                .Where(root => root != null && root.gameObject.activeInHierarchy)
                .OrderBy(root => root.name, StringComparer.Ordinal)
                .ToArray();
            var supportNames = new HashSet<string>(
                contract.support_surface_allowlist,
                StringComparer.Ordinal);
            var roadNames = new HashSet<string>(
                roadData.road_surface_allowlist,
                StringComparer.Ordinal);
            var footprints = roadData.obstacle_footprints.ToDictionary(
                item => item.canonical_name,
                StringComparer.Ordinal);

            Vector3 anchor = contract.AuditedAnchor;
            var report = new P1M3BodyAnchorAuditReport
            {
                source_scenario_id = scenario.scenario_id,
                source_scenario_sha256 = scenarioSha256,
                road_data_sha256 = scenario.road_data_sha256,
                anchor_contract_sha256 = contractSha256,
                audited_anchor_world_m =
                    new ScenarioVector3(anchor.x, anchor.y, anchor.z),
                hover_point_world_m = new ScenarioVector3(
                    anchor.x,
                    anchor.y + contract.hover_offset_y_m,
                    anchor.z),
                anchor_effective_radius_m = contract.AnchorEffectiveRadius,
                hover_effective_radius_m = contract.HoverEffectiveRadius,
                corridor_effective_radius_m = contract.CorridorEffectiveRadius,
                support_status = "NOT_EVALUATED",
                clearance_status = "NOT_EVALUATED",
                support_matches = Array.Empty<P1M3BodyAnchorSupportMatch>(),
                blockers = Array.Empty<P1M3BodyAnchorBlocker>(),
                scene_root_count = roots.Length,
                support_surface_allowlist =
                    contract.support_surface_allowlist.ToArray(),
            };
            AttachRouteDiagnostic(report, scenario, anchor);

            List<P1M3BodyAnchorSupportMatch> support;
            try
            {
                support = SupportAt(
                    new Vector2(anchor.x, anchor.z),
                    roadData,
                    roots,
                    supportNames,
                    footprints);
            }
            catch (InvalidOperationException exception)
                when (IsUnsupportedTrs(exception))
            {
                return Fail(
                    report,
                    "UNSUPPORTED_SUPPORT_TRS",
                    supportFailed: true,
                    blockingObject: UnsupportedTrsName(exception));
            }
            report.support_matches = support
                .OrderBy(item => item.id, StringComparer.Ordinal)
                .ToArray();
            if (support.Count == 0)
                return Fail(report, "SUPPORT_NOT_FOUND", supportFailed: true);

            float minimumY = support.Min(item => item.surface_y_m);
            float maximumY = support.Max(item => item.surface_y_m);
            report.support_surface_y_m = minimumY;
            report.support_height_error_m = anchor.y - minimumY;
            if (maximumY - minimumY > GeometryEpsilon)
                return Fail(report, "SUPPORT_HEIGHT_CONFLICT", supportFailed: true);
            if (Mathf.Abs(report.support_height_error_m)
                > contract.support_height_tolerance_m + GeometryEpsilon)
            {
                return Fail(
                    report,
                    "SUPPORT_HEIGHT_MISMATCH",
                    supportFailed: true);
            }
            report.support_status = "PASS";

            var blockers = new List<P1M3BodyAnchorBlocker>();
            int audited = 0;
            foreach (Transform root in roots)
            {
                string canonical =
                    SceneVehicleAdjustmentApplier.CanonicalPrefabName(root.name);
                if (roadNames.Contains(canonical)
                    || supportNames.Contains(canonical))
                {
                    continue;
                }
                if (!footprints.TryGetValue(
                    canonical,
                    out RoadObstacleFootprint footprint))
                {
                    blockers.Add(new P1M3BodyAnchorBlocker
                    {
                        scene_object_name = root.name,
                        canonical_name = canonical,
                        group = "",
                        reason = "UNCLASSIFIED_OBSTACLE",
                        horizontal_distance_m = float.NaN,
                        obstacle_min_y_m = float.NaN,
                        obstacle_max_y_m = float.NaN,
                    });
                    continue;
                }
                audited++;
                P1M3BodyAnchorBlocker blocker;
                try
                {
                    blocker = Intersect(
                        anchor,
                        minimumY,
                        root,
                        canonical,
                        footprint,
                        contract);
                }
                catch (InvalidOperationException exception)
                    when (IsUnsupportedTrs(exception))
                {
                    blockers.Add(new P1M3BodyAnchorBlocker
                    {
                        scene_object_name = root.name,
                        canonical_name = canonical,
                        group = footprint.group,
                        reason = "UNSUPPORTED_OBSTACLE_TRS",
                        horizontal_distance_m = float.NaN,
                        obstacle_min_y_m = float.NaN,
                        obstacle_max_y_m = float.NaN,
                    });
                    continue;
                }
                if (blocker != null) blockers.Add(blocker);
            }
            report.audited_obstacle_count = audited;
            report.blockers = blockers
                .OrderBy(item => item.scene_object_name, StringComparer.Ordinal)
                .ToArray();
            report.blocker_count = report.blockers.Length;
            if (report.blocker_count > 0)
            {
                report.clearance_status = "FAIL";
                report.status = StatusFailed;
                report.rejection_reason = report.blockers[0].reason;
                return report;
            }
            report.clearance_status = "PASS";
            report.status = StatusClear;
            report.rejection_reason = "";
            return report;
        }

        /// <summary>
        /// The audit is only meaningful if it audits the anchor the frozen
        /// scenario actually runs. A contract that drifted from the scenario
        /// bytes would produce a clean report about a position nothing uses.
        /// </summary>
        static void RequireScenarioAgreement(
            ScenarioConfig scenario,
            P1M3BodyAnchorPlacementContract contract)
        {
            if (scenario.anchor_world_m == null)
                throw new InvalidOperationException(
                    "scenario_has_no_anchor_world_m");
            Vector3 scenarioAnchor = scenario.anchor_world_m.Value;
            Vector3 audited = contract.AuditedAnchor;
            if (Mathf.Abs(scenarioAnchor.x - audited.x) > GeometryEpsilon
                || Mathf.Abs(scenarioAnchor.y - audited.y) > GeometryEpsilon
                || Mathf.Abs(scenarioAnchor.z - audited.z) > GeometryEpsilon)
            {
                throw new InvalidOperationException(
                    "audited_anchor_differs_from_scenario_anchor");
            }
        }

        /// <summary>
        /// Distance from the anchor to the frozen route centreline, recorded
        /// next to the corridor half width the scene audit uses. This is a
        /// <b>disclosed diagnostic only</b>: BC-M34-4 (c) freezes the audit
        /// as support + clearance, and inventing an extra gate here would be
        /// the implementation role reinterpreting an accepted clarification.
        /// The number is published so Acceptance can rule on it.
        /// </summary>
        static void AttachRouteDiagnostic(
            P1M3BodyAnchorAuditReport report,
            ScenarioConfig scenario,
            Vector3 anchor)
        {
            ScenarioVector3[] route = scenario.target?.route_world_m;
            if (route == null || route.Length < 2) return;
            var point = new Vector2(anchor.x, anchor.z);
            float best = float.PositiveInfinity;
            for (int index = 0; index < route.Length; index++)
            {
                Vector3 start3 = route[index].Value;
                Vector3 end3 = route[(index + 1) % route.Length].Value;
                var start = new Vector2(start3.x, start3.z);
                var end = new Vector2(end3.x, end3.z);
                Vector2 delta = end - start;
                float lengthSquared = delta.sqrMagnitude;
                float t = lengthSquared <= GeometryEpsilon
                    ? 0f
                    : Mathf.Clamp01(Vector2.Dot(point - start, delta) / lengthSquared);
                best = Mathf.Min(best, Vector2.Distance(point, start + t * delta));
            }
            report.route_centerline_distance_m = best;
            RouteCorridorScenarioConfig corridor =
                scenario.scene_adjustments?.route_corridor;
            report.route_corridor_half_width_m = corridor == null
                ? float.NaN
                : corridor.target_half_width_m + corridor.clearance_margin_m;
        }

        static List<P1M3BodyAnchorSupportMatch> SupportAt(
            Vector2 point,
            RoadSceneData roadData,
            IEnumerable<Transform> roots,
            HashSet<string> supportNames,
            IReadOnlyDictionary<string, RoadObstacleFootprint> footprints)
        {
            var matches = new List<P1M3BodyAnchorSupportMatch>();
            foreach (RoadSurfacePatch surface in roadData.surfaces)
            {
                if (!P1Scene003AnchorAuditor.StrictlyInsideSurface(point, surface))
                    continue;
                matches.Add(new P1M3BodyAnchorSupportMatch
                {
                    id = surface.id,
                    source = "road_surface",
                    surface_y_m = surface.surface_y_m,
                });
            }
            foreach (Transform root in roots)
            {
                string canonical =
                    SceneVehicleAdjustmentApplier.CanonicalPrefabName(root.name);
                if (!supportNames.Contains(canonical)) continue;
                if (!footprints.TryGetValue(
                    canonical,
                    out RoadObstacleFootprint footprint))
                {
                    continue;
                }
                P1Scene003AnchorAuditor.Footprint transformed =
                    P1Scene003AnchorAuditor.TransformFootprint(root, footprint);
                if (!P1Scene003AnchorAuditor.StrictlyInsideConvex(
                    point,
                    transformed.Corners))
                {
                    continue;
                }
                matches.Add(new P1M3BodyAnchorSupportMatch
                {
                    id = root.name,
                    source = "support_prefab",
                    surface_y_m = transformed.MaxY,
                });
            }
            return matches;
        }

        /// <summary>
        /// SCENE-003's three effective volumes, unchanged: the anchor
        /// cylinder at ground level, the tether corridor cylinder from ground
        /// to hover height, and the hover sphere around the nominal hover
        /// point. Returns null when the obstacle clears all three.
        /// </summary>
        static P1M3BodyAnchorBlocker Intersect(
            Vector3 anchor,
            float groundY,
            Transform root,
            string canonical,
            RoadObstacleFootprint source,
            P1M3BodyAnchorPlacementContract contract)
        {
            P1Scene003AnchorAuditor.Footprint obstacle =
                P1Scene003AnchorAuditor.TransformFootprint(root, source);
            var center = new Vector2(anchor.x, anchor.z);
            float horizontalDistance = P1Scene003AnchorAuditor.DistanceToConvex(
                center,
                obstacle.Corners);
            float hoverY = anchor.y + contract.hover_offset_y_m;

            bool anchorCylinder =
                horizontalDistance
                    <= contract.AnchorEffectiveRadius + GeometryEpsilon
                && P1Scene003AnchorAuditor.IntervalsOverlap(
                    obstacle.MinY,
                    obstacle.MaxY,
                    groundY,
                    groundY + contract.clearance_margin_m);
            bool corridorCylinder =
                horizontalDistance
                    <= contract.CorridorEffectiveRadius + GeometryEpsilon
                && P1Scene003AnchorAuditor.IntervalsOverlap(
                    obstacle.MinY,
                    obstacle.MaxY,
                    groundY,
                    hoverY);
            float verticalDistance = hoverY < obstacle.MinY
                ? obstacle.MinY - hoverY
                : hoverY > obstacle.MaxY
                    ? hoverY - obstacle.MaxY
                    : 0f;
            float hoverDistanceSquared =
                horizontalDistance * horizontalDistance
                + verticalDistance * verticalDistance;
            bool hoverSphere = hoverDistanceSquared
                <= contract.HoverEffectiveRadius * contract.HoverEffectiveRadius
                    + GeometryEpsilon;
            if (!anchorCylinder && !corridorCylinder && !hoverSphere) return null;
            return new P1M3BodyAnchorBlocker
            {
                scene_object_name = root.name,
                canonical_name = canonical,
                group = source.group,
                reason = "CLEARANCE_INTERSECTION",
                horizontal_distance_m = horizontalDistance,
                obstacle_min_y_m = obstacle.MinY,
                obstacle_max_y_m = obstacle.MaxY,
                anchor_cylinder = anchorCylinder,
                corridor_cylinder = corridorCylinder,
                hover_sphere = hoverSphere,
            };
        }

        static P1M3BodyAnchorAuditReport Fail(
            P1M3BodyAnchorAuditReport report,
            string reason,
            bool supportFailed,
            string blockingObject = null)
        {
            if (supportFailed) report.support_status = "FAIL";
            report.status = StatusFailed;
            report.rejection_reason = reason;
            if (blockingObject != null)
            {
                report.blockers = new[]
                {
                    new P1M3BodyAnchorBlocker
                    {
                        scene_object_name = blockingObject,
                        canonical_name = SceneVehicleAdjustmentApplier
                            .CanonicalPrefabName(blockingObject),
                        group = "",
                        reason = reason,
                        horizontal_distance_m = float.NaN,
                        obstacle_min_y_m = float.NaN,
                        obstacle_max_y_m = float.NaN,
                    },
                };
                report.blocker_count = 1;
            }
            return report;
        }

        static bool IsUnsupportedTrs(InvalidOperationException exception) =>
            exception.Message.StartsWith(
                "unsupported_anchor_audit_trs:",
                StringComparison.Ordinal);

        static string UnsupportedTrsName(InvalidOperationException exception) =>
            exception.Message.Substring("unsupported_anchor_audit_trs:".Length);
    }
}
