using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;

namespace TetheredTracking
{
    [Serializable]
    public sealed class SceneXZ
    {
        public float x = float.NaN;
        public float z = float.NaN;

        public Vector2 Value => new Vector2(x, z);
    }

    /// <summary>
    /// P1-SCENE-004 anchor placement contract.
    ///
    /// Two deliberate differences from the P1-SCENE-003 contract, both from
    /// the accepted revision 2 design:
    ///
    /// * The anchor elevation is <b>derived</b> from the measured support
    ///   surface instead of being asserted up front. SCENE-003 froze
    ///   <c>y = 0.2 +/- 0.05</c>, which is the *road* surface elevation, and
    ///   every grass candidate was rejected at roughly 1.3e-6 m. The
    ///   tolerance now only decides whether several support surfaces under
    ///   one candidate disagree.
    /// * Each lattice candidate must additionally satisfy the geometry
    ///   envelope against the frozen circuit (BC3), so the deterministic
    ///   fallback cannot hand back an anchor that a later gate rejects.
    /// </summary>
    [Serializable]
    public sealed class P1Scene004AnchorPlacementContract
    {
        public const string Schema = "p1-scene-004-anchor-placement/v1";
        public const string WorkId = "P1-SCENE-004";
        public const string FileName = "p1-scene-004-anchor-placement.json";

        public string schema_version;
        public string work_id;
        public SceneXZ requested_anchor_world_m;
        public float hover_offset_y_m = float.NaN;
        public string[] support_surface_allowlist;
        public float support_height_tolerance_m = float.NaN;
        public float anchor_nominal_radius_m = float.NaN;
        public float hover_nominal_radius_m = float.NaN;
        public float corridor_nominal_radius_m = float.NaN;
        public float clearance_margin_m = float.NaN;
        public float lattice_step_m = float.NaN;
        public float lattice_radius_m = float.NaN;
        public float target_plane_y_m = float.NaN;
        public float envelope_max_slant_range_m = float.NaN;
        public float envelope_max_off_nadir_deg = float.NaN;
        public float envelope_off_nadir_margin_min_deg = float.NaN;
        public float envelope_route_sample_spacing_m = float.NaN;
        public SceneXZ[] circuit_world_m;

        public Vector2 RequestedAnchor => requested_anchor_world_m.Value;
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
                    "invalid_p1_scene_004_anchor_contract_identity");
            if (requested_anchor_world_m == null)
                throw new InvalidOperationException(
                    "missing_p1_scene_004_requested_anchor");
            RequireFinite(RequestedAnchor.x, "requested_anchor_world_m.x");
            RequireFinite(RequestedAnchor.y, "requested_anchor_world_m.z");
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
            RequirePositive(lattice_step_m, "lattice_step_m");
            RequirePositive(lattice_radius_m, "lattice_radius_m");
            RequireFinite(target_plane_y_m, "target_plane_y_m");
            RequirePositive(
                envelope_max_slant_range_m,
                "envelope_max_slant_range_m");
            RequirePositive(
                envelope_max_off_nadir_deg,
                "envelope_max_off_nadir_deg");
            if (envelope_max_off_nadir_deg >= 90f)
                throw new InvalidOperationException(
                    "envelope_max_off_nadir_deg must be below 90");
            RequireNonNegative(
                envelope_off_nadir_margin_min_deg,
                "envelope_off_nadir_margin_min_deg");
            RequirePositive(
                envelope_route_sample_spacing_m,
                "envelope_route_sample_spacing_m");
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
            if (circuit_world_m == null || circuit_world_m.Length < 3)
                throw new InvalidOperationException(
                    "circuit_world_m needs at least three vertices");
            foreach (SceneXZ vertex in circuit_world_m)
            {
                if (vertex == null)
                    throw new InvalidOperationException(
                        "circuit_world_m contains a null vertex");
                RequireFinite(vertex.x, "circuit_world_m.x");
                RequireFinite(vertex.z, "circuit_world_m.z");
            }
        }

        static void RequireFinite(float value, string label)
        {
            if (!Finite(value))
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

    public static class P1Scene004AnchorPlacementContractLoader
    {
        public static string ProjectPath =>
            RuntimePaths.ProjectFile(
                "config",
                P1Scene004AnchorPlacementContract.FileName);

        public static P1Scene004AnchorPlacementContract Load(
            out string sha256)
        {
            string path = ProjectPath;
            if (!File.Exists(path))
                throw new FileNotFoundException(
                    "missing_p1_scene_004_anchor_contract",
                    path);
            byte[] bytes = File.ReadAllBytes(path);
            sha256 = Sha256(bytes);
            var contract =
                JsonUtility.FromJson<P1Scene004AnchorPlacementContract>(
                    Encoding.UTF8.GetString(bytes));
            if (contract == null)
                throw new InvalidOperationException(
                    "unreadable_p1_scene_004_anchor_contract");
            contract.Validate();
            return contract;
        }

        public static string Sha256(byte[] bytes)
        {
            if (bytes == null) throw new ArgumentNullException(nameof(bytes));
            using (var algorithm = SHA256.Create())
            {
                return string.Concat(
                    algorithm.ComputeHash(bytes)
                        .Select(value => value.ToString("x2")));
            }
        }
    }

    [Serializable]
    public sealed class P1Scene004AnchorCandidateAudit
    {
        public int rank;
        public float x_m;
        public float z_m;
        public float center_distance_m;
        public string[] support_ids;
        public float support_surface_y_m;
        public float derived_anchor_y_m;
        public string support_status;
        public string road_disjoint_status;
        public string envelope_status;
        public string clearance_status;
        public float maximum_slant_range_m;
        public float maximum_off_nadir_deg;
        public float off_nadir_margin_deg;
        public float slant_range_margin_m;
        public string rejection_reason;
        public string blocking_object;
    }

    [Serializable]
    public sealed class P1Scene004AnchorAuditReport
    {
        public string schema_version = "p1-scene-004-anchor-audit/v1";
        public string work_id = P1Scene004AnchorPlacementContract.WorkId;
        public string status;
        public string source_scenario_id;
        public string source_scenario_sha256;
        public string road_data_sha256;
        public string anchor_contract_sha256;
        public SceneXZ requested_anchor_world_m;
        public ScenarioVector3 selected_anchor_world_m;
        public float selected_maximum_slant_range_m = float.NaN;
        public float selected_maximum_off_nadir_deg = float.NaN;
        public float selected_off_nadir_margin_deg = float.NaN;
        public float selected_slant_range_margin_m = float.NaN;
        public int candidate_count;
        public int support_rejection_count;
        public int road_overlap_rejection_count;
        public int envelope_rejection_count;
        public int clearance_rejection_count;
        public int legal_candidate_count;
        public string[] support_surface_allowlist;
        public P1Scene004AnchorCandidateAudit[] candidates;
    }

    /// <summary>
    /// Deterministic support/road-disjointness/envelope/clearance audit for
    /// the SCENE-004 roadside anchor. Geometry primitives are reused from
    /// <see cref="P1Scene003AnchorAuditor"/> unchanged so the two audits
    /// cannot drift apart; only the gates differ.
    /// </summary>
    public static class P1Scene004AnchorAuditor
    {
        const float GeometryEpsilon = P1Scene003AnchorAuditor.GeometryEpsilon;

        public static P1Scene004AnchorAuditReport Audit(
            ScenarioConfig scenario,
            string scenarioSha256,
            RoadSceneData roadData,
            IEnumerable<Transform> sceneRoots,
            P1Scene004AnchorPlacementContract contract,
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
            Vector2[] circuit = CircuitSamples(contract);

            P1Scene004AnchorCandidateAudit[] candidates =
                CandidatePositions(contract)
                    .Select((position, index) => AuditCandidate(
                        index,
                        position,
                        roadData,
                        roots,
                        supportNames,
                        roadNames,
                        footprints,
                        circuit,
                        contract))
                    .ToArray();
            P1Scene004AnchorCandidateAudit selected = candidates.FirstOrDefault(
                item => item.rejection_reason == null);

            return new P1Scene004AnchorAuditReport
            {
                status = BlockingStatus(selected, candidates),
                source_scenario_id = scenario.scenario_id,
                source_scenario_sha256 = scenarioSha256,
                road_data_sha256 = scenario.road_data_sha256,
                anchor_contract_sha256 = contractSha256,
                requested_anchor_world_m = new SceneXZ
                {
                    x = contract.RequestedAnchor.x,
                    z = contract.RequestedAnchor.y,
                },
                selected_anchor_world_m = selected == null
                    ? null
                    : new ScenarioVector3(
                        selected.x_m,
                        selected.derived_anchor_y_m,
                        selected.z_m),
                selected_maximum_slant_range_m = selected?.maximum_slant_range_m
                    ?? float.NaN,
                selected_maximum_off_nadir_deg = selected?.maximum_off_nadir_deg
                    ?? float.NaN,
                selected_off_nadir_margin_deg = selected?.off_nadir_margin_deg
                    ?? float.NaN,
                selected_slant_range_margin_m = selected?.slant_range_margin_m
                    ?? float.NaN,
                candidate_count = candidates.Length,
                support_rejection_count = candidates.Count(
                    item => item.support_status != "PASS"),
                road_overlap_rejection_count = candidates.Count(
                    item => item.support_status == "PASS"
                        && item.road_disjoint_status != "PASS"),
                envelope_rejection_count = candidates.Count(
                    item => item.road_disjoint_status == "PASS"
                        && item.envelope_status != "PASS"),
                clearance_rejection_count = candidates.Count(
                    item => item.envelope_status == "PASS"
                        && item.clearance_status != "PASS"),
                legal_candidate_count = candidates.Count(
                    item => item.rejection_reason == null),
                support_surface_allowlist =
                    contract.support_surface_allowlist.ToArray(),
                candidates = candidates,
            };
        }

        /// <summary>
        /// Disposition row the artifact belongs to.
        ///
        /// The proposal's table separates row 1 (`BLOCKED_ANCHOR_PLACEMENT`,
        /// no legal anchor) from row 2 (`ENVELOPE_OUT_OF_BOUNDS`, the circuit
        /// geometry is wrong). Collapsing both into row 1 would send an
        /// envelope problem back to the wrong place, so the dominant
        /// rejection reason decides (Sonnet round 1 note 5).
        /// </summary>
        internal static string BlockingStatus(
            P1Scene004AnchorCandidateAudit selected,
            P1Scene004AnchorCandidateAudit[] candidates)
        {
            if (selected != null) return "CLEAR";
            bool anySupported = false;
            foreach (P1Scene004AnchorCandidateAudit candidate in candidates)
            {
                if (candidate.support_status == "PASS"
                    && candidate.road_disjoint_status == "PASS")
                {
                    anySupported = true;
                    break;
                }
            }
            // If nothing even reached the envelope gate the anchor region is
            // the problem; otherwise the circuit is.
            return anySupported
                ? "ENVELOPE_OUT_OF_BOUNDS"
                : "BLOCKED_ANCHOR_PLACEMENT";
        }

        public static void Write(
            P1Scene004AnchorAuditReport report,
            string path = null)
        {
            if (report == null) throw new ArgumentNullException(nameof(report));
            AtomicFile.WriteAllText(
                path ?? RuntimePaths.File("p1_scene_004_anchor_audit.json"),
                JsonUtility.ToJson(report, true) + "\n");
        }

        internal static Vector2[] CircuitSamples(
            P1Scene004AnchorPlacementContract contract)
        {
            var samples = new List<Vector2>();
            SceneXZ[] vertices = contract.circuit_world_m;
            for (int index = 0; index < vertices.Length; index++)
            {
                Vector2 start = vertices[index].Value;
                Vector2 end = vertices[(index + 1) % vertices.Length].Value;
                float length = Vector2.Distance(start, end);
                int steps = Mathf.Max(
                    1,
                    Mathf.CeilToInt(length / contract.envelope_route_sample_spacing_m));
                for (int step = 0; step < steps; step++)
                {
                    samples.Add(Vector2.Lerp(start, end, (float)step / steps));
                }
            }
            return samples.ToArray();
        }

        static IEnumerable<Vector2> CandidatePositions(
            P1Scene004AnchorPlacementContract contract)
        {
            Vector2 center = contract.RequestedAnchor;
            int extent = Mathf.CeilToInt(
                contract.lattice_radius_m / contract.lattice_step_m);
            var candidates = new List<Vector2>();
            for (int xIndex = -extent; xIndex <= extent; xIndex++)
            {
                for (int zIndex = -extent; zIndex <= extent; zIndex++)
                {
                    float dx = xIndex * contract.lattice_step_m;
                    float dz = zIndex * contract.lattice_step_m;
                    if (dx * dx + dz * dz
                        > contract.lattice_radius_m
                            * contract.lattice_radius_m
                            + GeometryEpsilon)
                    {
                        continue;
                    }
                    candidates.Add(new Vector2(center.x + dx, center.y + dz));
                }
            }
            return candidates
                .OrderBy(item => (item - center).sqrMagnitude)
                .ThenBy(item => item.x)
                .ThenBy(item => item.y);
        }

        static P1Scene004AnchorCandidateAudit AuditCandidate(
            int rank,
            Vector2 position,
            RoadSceneData roadData,
            Transform[] roots,
            HashSet<string> supportNames,
            HashSet<string> roadNames,
            IReadOnlyDictionary<string, RoadObstacleFootprint> footprints,
            Vector2[] circuit,
            P1Scene004AnchorPlacementContract contract)
        {
            var result = new P1Scene004AnchorCandidateAudit
            {
                rank = rank,
                x_m = position.x,
                z_m = position.y,
                center_distance_m =
                    Vector2.Distance(position, contract.RequestedAnchor),
                support_ids = Array.Empty<string>(),
                support_surface_y_m = float.NaN,
                derived_anchor_y_m = float.NaN,
                support_status = "NOT_EVALUATED",
                road_disjoint_status = "NOT_EVALUATED",
                envelope_status = "NOT_EVALUATED",
                clearance_status = "NOT_EVALUATED",
                maximum_slant_range_m = float.NaN,
                maximum_off_nadir_deg = float.NaN,
                off_nadir_margin_deg = float.NaN,
                slant_range_margin_m = float.NaN,
            };

            float radius = contract.AnchorEffectiveRadius;
            List<(string Id, float SurfaceY)> support;
            try
            {
                support = SupportUnderDisc(
                    position,
                    radius,
                    roots,
                    supportNames,
                    footprints);
            }
            catch (InvalidOperationException exception)
                when (exception.Message.StartsWith(
                    "unsupported_anchor_audit_trs:",
                    StringComparison.Ordinal))
            {
                result.support_status = "FAIL";
                result.rejection_reason = "UNSUPPORTED_SUPPORT_TRS";
                result.blocking_object = exception.Message.Substring(
                    "unsupported_anchor_audit_trs:".Length);
                return result;
            }
            result.support_ids = support
                .Select(item => item.Id)
                .OrderBy(item => item, StringComparer.Ordinal)
                .ToArray();
            if (support.Count == 0)
            {
                result.support_status = "FAIL";
                result.rejection_reason = "SUPPORT_NOT_FOUND";
                return result;
            }
            float minimumY = support.Min(item => item.SurfaceY);
            float maximumY = support.Max(item => item.SurfaceY);
            result.support_surface_y_m = minimumY;
            if (maximumY - minimumY
                > contract.support_height_tolerance_m + GeometryEpsilon)
            {
                result.support_status = "FAIL";
                result.rejection_reason = "SUPPORT_HEIGHT_CONFLICT";
                return result;
            }
            // The elevation is derived, never asserted: this is the whole
            // point of the SCENE-003 lesson.
            result.support_status = "PASS";
            result.derived_anchor_y_m = minimumY;

            string roadOverlap = RoadOverlap(position, radius, roadData, roadNames);
            if (roadOverlap != null)
            {
                result.road_disjoint_status = "FAIL";
                result.rejection_reason = "ANCHOR_DISC_OVERLAPS_ROAD";
                result.blocking_object = roadOverlap;
                return result;
            }
            result.road_disjoint_status = "PASS";

            float hoverY = minimumY + contract.hover_offset_y_m;
            float verticalDrop = hoverY - contract.target_plane_y_m;
            float maximumHorizontal = 0f;
            foreach (Vector2 sample in circuit)
            {
                maximumHorizontal = Mathf.Max(
                    maximumHorizontal,
                    Vector2.Distance(position, sample));
            }
            float maximumSlant = Mathf.Sqrt(
                maximumHorizontal * maximumHorizontal
                + verticalDrop * verticalDrop);
            float maximumOffNadir = Mathf.Atan2(
                maximumHorizontal,
                verticalDrop) * Mathf.Rad2Deg;
            result.maximum_slant_range_m = maximumSlant;
            result.maximum_off_nadir_deg = maximumOffNadir;
            result.off_nadir_margin_deg =
                contract.envelope_max_off_nadir_deg - maximumOffNadir;
            result.slant_range_margin_m =
                contract.envelope_max_slant_range_m - maximumSlant;
            if (verticalDrop <= 0f
                || maximumSlant
                    > contract.envelope_max_slant_range_m + GeometryEpsilon
                || maximumOffNadir
                    > contract.envelope_max_off_nadir_deg + GeometryEpsilon
                || result.off_nadir_margin_deg
                    < contract.envelope_off_nadir_margin_min_deg
                        - GeometryEpsilon)
            {
                result.envelope_status = "FAIL";
                result.rejection_reason = "ENVELOPE_OUT_OF_BOUNDS";
                return result;
            }
            result.envelope_status = "PASS";

            var anchor = new Vector3(position.x, minimumY, position.y);
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
                    result.clearance_status = "FAIL";
                    result.rejection_reason = "UNCLASSIFIED_OBSTACLE";
                    result.blocking_object = root.name;
                    return result;
                }
                bool intersects;
                try
                {
                    intersects = IntersectsEffectiveVolumes(
                        anchor,
                        minimumY,
                        root,
                        footprint,
                        contract);
                }
                catch (InvalidOperationException exception)
                    when (exception.Message.StartsWith(
                        "unsupported_anchor_audit_trs:",
                        StringComparison.Ordinal))
                {
                    result.clearance_status = "FAIL";
                    result.rejection_reason = "UNSUPPORTED_OBSTACLE_TRS";
                    result.blocking_object = root.name;
                    return result;
                }
                if (intersects)
                {
                    result.clearance_status = "FAIL";
                    result.rejection_reason = "CLEARANCE_INTERSECTION";
                    result.blocking_object = root.name;
                    return result;
                }
            }
            result.clearance_status = "PASS";
            return result;
        }

        /// <summary>
        /// Support surfaces that contain the whole expanded anchor disc, not
        /// merely its centre point. SCENE-003 only tested the centre, which
        /// would allow a disc to hang over a boundary.
        /// </summary>
        static List<(string Id, float SurfaceY)> SupportUnderDisc(
            Vector2 center,
            float radius,
            IEnumerable<Transform> roots,
            HashSet<string> supportNames,
            IReadOnlyDictionary<string, RoadObstacleFootprint> footprints)
        {
            // Support comes only from allowlisted scene prefabs.
            // `RoadSceneData.Validate` already forces every entry of
            // `surfaces` to be an allowlisted *road*, and a road is never a
            // legal anchor support here — the disc must be disjoint from it
            // (see RoadOverlap). SCENE-003 accepted any road-data surface as
            // support; that latent hole is closed rather than carried over.
            var matches = new List<(string, float)>();
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
                    center,
                    transformed.Corners))
                {
                    continue;
                }
                if (DistanceToBoundary(center, transformed.Corners)
                    <= radius + GeometryEpsilon)
                {
                    continue;
                }
                matches.Add((root.name, transformed.MaxY));
            }
            return matches;
        }

        /// <summary>Name of the first road surface the disc touches, or null.</summary>
        static string RoadOverlap(
            Vector2 center,
            float radius,
            RoadSceneData roadData,
            HashSet<string> roadNames)
        {
            foreach (RoadSurfacePatch surface in roadData.surfaces)
            {
                if (!roadNames.Contains(surface.canonical_name)) continue;
                if (DiscTouchesSurface(center, radius, surface)) return surface.id;
            }
            return null;
        }

        internal static bool DiscTouchesSurface(
            Vector2 center,
            float radius,
            RoadSurfacePatch surface)
        {
            Vector2 local = ToLocal(center, surface);
            float dx = Mathf.Max(
                0f,
                Mathf.Abs(local.x) - surface.half_extent_x_m);
            float dz = Mathf.Max(
                0f,
                Mathf.Abs(local.y) - surface.half_extent_z_m);
            return Mathf.Sqrt(dx * dx + dz * dz) <= radius + GeometryEpsilon;
        }

        static Vector2 ToLocal(Vector2 point, RoadSurfacePatch surface)
        {
            float radians = -surface.yaw_deg * Mathf.Deg2Rad;
            float cosine = Mathf.Cos(radians);
            float sine = Mathf.Sin(radians);
            Vector2 delta = point - new Vector2(
                surface.center_x_m,
                surface.center_z_m);
            return new Vector2(
                cosine * delta.x - sine * delta.y,
                sine * delta.x + cosine * delta.y);
        }

        internal static float DistanceToBoundary(Vector2 point, Vector2[] polygon)
        {
            float minimum = float.PositiveInfinity;
            for (int index = 0; index < polygon.Length; index++)
            {
                Vector2 start = polygon[index];
                Vector2 end = polygon[(index + 1) % polygon.Length];
                Vector2 delta = end - start;
                float t = delta.sqrMagnitude <= GeometryEpsilon
                    ? 0f
                    : Mathf.Clamp01(Vector2.Dot(point - start, delta)
                        / delta.sqrMagnitude);
                minimum = Mathf.Min(
                    minimum,
                    Vector2.Distance(point, start + t * delta));
            }
            return minimum;
        }

        static bool IntersectsEffectiveVolumes(
            Vector3 anchor,
            float groundY,
            Transform root,
            RoadObstacleFootprint source,
            P1Scene004AnchorPlacementContract contract)
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
                <= contract.HoverEffectiveRadius
                    * contract.HoverEffectiveRadius
                    + GeometryEpsilon;
            return anchorCylinder || corridorCylinder || hoverSphere;
        }
    }
}
