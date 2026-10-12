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
    public sealed class P1Scene003AnchorPlacementContract
    {
        public const string Schema = "p1-scene-003-anchor-placement/v1";
        public const string WorkId = "P1-SCENE-003";
        public const string FileName = "p1-scene-003-anchor-placement.json";

        public string schema_version;
        public string work_id;
        public ScenarioVector3 requested_anchor_world_m;
        public float hover_offset_y_m = float.NaN;
        public string[] support_surface_allowlist;
        public float support_height_tolerance_m = float.NaN;
        public float anchor_nominal_radius_m = float.NaN;
        public float hover_nominal_radius_m = float.NaN;
        public float corridor_nominal_radius_m = float.NaN;
        public float clearance_margin_m = float.NaN;
        public float lattice_step_m = float.NaN;
        public float lattice_radius_m = float.NaN;

        public Vector3 RequestedAnchor => requested_anchor_world_m.Value;
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
                    "invalid_p1_scene_003_anchor_contract_identity");
            if (requested_anchor_world_m == null)
                throw new InvalidOperationException(
                    "missing_p1_scene_003_requested_anchor");
            RequireFinite(RequestedAnchor, "requested_anchor_world_m");
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

    public static class P1Scene003AnchorPlacementContractLoader
    {
        public static string ProjectPath =>
            RuntimePaths.ProjectFile(
                "config",
                P1Scene003AnchorPlacementContract.FileName);

        public static P1Scene003AnchorPlacementContract Load(
            out string sha256,
            string path = null)
        {
            string resolved = path ?? ProjectPath;
            byte[] bytes = File.ReadAllBytes(resolved);
            sha256 = Sha256(bytes);
            P1Scene003AnchorPlacementContract contract;
            try
            {
                contract = JsonUtility.FromJson<P1Scene003AnchorPlacementContract>(
                    Encoding.UTF8.GetString(bytes));
            }
            catch (Exception exception)
            {
                throw new InvalidOperationException(
                    "invalid_p1_scene_003_anchor_contract_json",
                    exception);
            }
            if (contract == null)
                throw new InvalidOperationException(
                    "empty_p1_scene_003_anchor_contract");
            contract.Validate();
            return contract;
        }

        public static string Sha256(byte[] bytes)
        {
            using SHA256 sha = SHA256.Create();
            return string.Concat(
                sha.ComputeHash(bytes).Select(value => value.ToString("x2")));
        }
    }

    [Serializable]
    public sealed class P1Scene003AnchorCandidateAudit
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
        public string rejection_reason;
        public string blocking_object;
    }

    [Serializable]
    public sealed class P1Scene003AnchorAuditReport
    {
        public string schema_version = "p1-scene-003-anchor-audit/v1";
        public string work_id = P1Scene003AnchorPlacementContract.WorkId;
        public string status;
        public string source_scenario_id;
        public string source_scenario_sha256;
        public string road_data_sha256;
        public string anchor_contract_sha256;
        public ScenarioVector3 requested_anchor_world_m;
        public ScenarioVector3 selected_anchor_world_m;
        public int candidate_count;
        public int support_rejection_count;
        public int clearance_rejection_count;
        public int legal_candidate_count;
        public string[] support_surface_allowlist;
        public P1Scene003AnchorCandidateAudit[] candidates;
    }

    public static class P1Scene003AnchorAuditor
    {
        internal const float GeometryEpsilon = 1e-5f;

        internal readonly struct Footprint
        {
            internal readonly Vector2[] Corners;
            internal readonly float MinY;
            internal readonly float MaxY;

            internal Footprint(Vector2[] corners, float minY, float maxY)
            {
                Corners = corners;
                MinY = minY;
                MaxY = maxY;
            }
        }

        readonly struct SupportMatch
        {
            internal readonly string Id;
            internal readonly float SurfaceY;

            internal SupportMatch(string id, float surfaceY)
            {
                Id = id;
                SurfaceY = surfaceY;
            }
        }

        public static P1Scene003AnchorAuditReport Audit(
            ScenarioConfig scenario,
            string scenarioSha256,
            RoadSceneData roadData,
            IEnumerable<Transform> sceneRoots,
            P1Scene003AnchorPlacementContract contract,
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
            P1Scene003AnchorCandidateAudit[] candidates =
                CandidatePositions(contract)
                    .Select((position, index) => AuditCandidate(
                        index,
                        position,
                        roadData,
                        roots,
                        supportNames,
                        roadNames,
                        footprints,
                        contract))
                    .ToArray();
            P1Scene003AnchorCandidateAudit selected = candidates.FirstOrDefault(
                item => item.rejection_reason == null);

            return new P1Scene003AnchorAuditReport
            {
                status = selected == null
                    ? "BLOCKED_ANCHOR_PLACEMENT"
                    : "CLEAR",
                source_scenario_id = scenario.scenario_id,
                source_scenario_sha256 = scenarioSha256,
                road_data_sha256 = scenario.road_data_sha256,
                anchor_contract_sha256 = contractSha256,
                requested_anchor_world_m = new ScenarioVector3(
                    contract.RequestedAnchor.x,
                    contract.RequestedAnchor.y,
                    contract.RequestedAnchor.z),
                selected_anchor_world_m = selected == null
                    ? null
                    : new ScenarioVector3(selected.x_m, selected.y_m, selected.z_m),
                candidate_count = candidates.Length,
                support_rejection_count = candidates.Count(
                    item => item.support_status != "PASS"),
                clearance_rejection_count = candidates.Count(
                    item => item.support_status == "PASS"
                        && item.clearance_status != "PASS"),
                legal_candidate_count = candidates.Count(
                    item => item.rejection_reason == null),
                support_surface_allowlist =
                    contract.support_surface_allowlist.ToArray(),
                candidates = candidates,
            };
        }

        public static void Write(
            P1Scene003AnchorAuditReport report,
            string path = null)
        {
            if (report == null) throw new ArgumentNullException(nameof(report));
            AtomicFile.WriteAllText(
                path ?? RuntimePaths.File("p1_scene_003_anchor_audit.json"),
                JsonUtility.ToJson(report, true) + "\n");
        }

        static IEnumerable<Vector3> CandidatePositions(
            P1Scene003AnchorPlacementContract contract)
        {
            Vector3 center = contract.RequestedAnchor;
            int extent = Mathf.CeilToInt(
                contract.lattice_radius_m / contract.lattice_step_m);
            var candidates = new List<Vector3>();
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
                    candidates.Add(new Vector3(
                        center.x + dx,
                        center.y,
                        center.z + dz));
                }
            }
            return candidates
                .OrderBy(item => HorizontalDistanceSquared(item, center))
                .ThenBy(item => item.x)
                .ThenBy(item => item.z);
        }

        static P1Scene003AnchorCandidateAudit AuditCandidate(
            int rank,
            Vector3 position,
            RoadSceneData roadData,
            Transform[] roots,
            HashSet<string> supportNames,
            HashSet<string> roadNames,
            IReadOnlyDictionary<string, RoadObstacleFootprint> footprints,
            P1Scene003AnchorPlacementContract contract)
        {
            var result = new P1Scene003AnchorCandidateAudit
            {
                rank = rank,
                x_m = position.x,
                y_m = position.y,
                z_m = position.z,
                center_distance_m = Mathf.Sqrt(HorizontalDistanceSquared(
                    position,
                    contract.RequestedAnchor)),
                support_ids = Array.Empty<string>(),
                support_surface_y_m = float.NaN,
                support_status = "NOT_EVALUATED",
                clearance_status = "NOT_EVALUATED",
            };
            List<SupportMatch> support;
            try
            {
                support = SupportAt(
                    new Vector2(position.x, position.z),
                    roadData,
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
            if (maximumY - minimumY > GeometryEpsilon)
            {
                result.support_status = "FAIL";
                result.rejection_reason = "SUPPORT_HEIGHT_CONFLICT";
                return result;
            }
            if (Mathf.Abs(position.y - minimumY)
                > contract.support_height_tolerance_m + GeometryEpsilon)
            {
                result.support_status = "FAIL";
                result.rejection_reason = "SUPPORT_HEIGHT_MISMATCH";
                return result;
            }
            result.support_status = "PASS";

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
                        position,
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

        static List<SupportMatch> SupportAt(
            Vector2 point,
            RoadSceneData roadData,
            IEnumerable<Transform> roots,
            HashSet<string> supportNames,
            IReadOnlyDictionary<string, RoadObstacleFootprint> footprints)
        {
            var matches = new List<SupportMatch>();
            foreach (RoadSurfacePatch surface in roadData.surfaces)
            {
                if (StrictlyInsideSurface(point, surface))
                    matches.Add(new SupportMatch(surface.id, surface.surface_y_m));
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
                Footprint transformed = TransformFootprint(root, footprint);
                if (!StrictlyInsideConvex(point, transformed.Corners)) continue;
                matches.Add(new SupportMatch(
                    root.name,
                    transformed.MaxY));
            }
            return matches;
        }

        internal static bool StrictlyInsideSurface(
            Vector2 point,
            RoadSurfacePatch surface)
        {
            float radians = -surface.yaw_deg * Mathf.Deg2Rad;
            float cosine = Mathf.Cos(radians);
            float sine = Mathf.Sin(radians);
            Vector2 delta = point - new Vector2(
                surface.center_x_m,
                surface.center_z_m);
            float localX = cosine * delta.x - sine * delta.y;
            float localZ = sine * delta.x + cosine * delta.y;
            return Mathf.Abs(localX)
                    < surface.half_extent_x_m - GeometryEpsilon
                && Mathf.Abs(localZ)
                    < surface.half_extent_z_m - GeometryEpsilon;
        }

        static bool IntersectsEffectiveVolumes(
            Vector3 anchor,
            float groundY,
            Transform root,
            RoadObstacleFootprint source,
            P1Scene003AnchorPlacementContract contract)
        {
            Footprint obstacle = TransformFootprint(root, source);
            Vector2 center = new Vector2(anchor.x, anchor.z);
            float horizontalDistance = DistanceToConvex(
                center,
                obstacle.Corners);
            float hoverY = anchor.y + contract.hover_offset_y_m;

            bool anchorCylinder =
                horizontalDistance
                    <= contract.AnchorEffectiveRadius + GeometryEpsilon
                && IntervalsOverlap(
                    obstacle.MinY,
                    obstacle.MaxY,
                    groundY,
                    groundY + contract.clearance_margin_m);
            bool corridorCylinder =
                horizontalDistance
                    <= contract.CorridorEffectiveRadius + GeometryEpsilon
                && IntervalsOverlap(
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

        internal static Footprint TransformFootprint(
            Transform root,
            RoadObstacleFootprint source)
        {
            RequireSupportedTransform(root);
            var world = new List<Vector3>(8);
            foreach (float x in new[] { source.full_min_x_m, source.full_max_x_m })
            {
                foreach (float y in new[]
                    { source.full_min_y_m, source.full_max_y_m })
                {
                    foreach (float z in new[]
                        { source.full_min_z_m, source.full_max_z_m })
                    {
                        world.Add(root.TransformPoint(new Vector3(x, y, z)));
                    }
                }
            }
            Vector2[] corners =
            {
                ToXZ(root.TransformPoint(new Vector3(
                    source.full_min_x_m, 0f, source.full_min_z_m))),
                ToXZ(root.TransformPoint(new Vector3(
                    source.full_max_x_m, 0f, source.full_min_z_m))),
                ToXZ(root.TransformPoint(new Vector3(
                    source.full_max_x_m, 0f, source.full_max_z_m))),
                ToXZ(root.TransformPoint(new Vector3(
                    source.full_min_x_m, 0f, source.full_max_z_m))),
            };
            return new Footprint(
                corners,
                world.Min(item => item.y),
                world.Max(item => item.y));
        }

        internal static void RequireSupportedTransform(Transform root)
        {
            Vector3 scale = root.lossyScale;
            if (!FiniteNonZero(scale.x)
                || !FiniteNonZero(scale.y)
                || !FiniteNonZero(scale.z)
                || Vector3.Angle(root.up, Vector3.up) > 0.01f)
            {
                throw new InvalidOperationException(
                    $"unsupported_anchor_audit_trs:{root.name}");
            }
        }

        internal static bool StrictlyInsideConvex(Vector2 point, Vector2[] polygon)
        {
            float sign = 0f;
            for (int index = 0; index < polygon.Length; index++)
            {
                float cross = Cross(
                    polygon[(index + 1) % polygon.Length] - polygon[index],
                    point - polygon[index]);
                if (Mathf.Abs(cross) <= GeometryEpsilon) return false;
                float current = Mathf.Sign(cross);
                if (sign == 0f) sign = current;
                else if (current != sign) return false;
            }
            return true;
        }

        internal static float DistanceToConvex(Vector2 point, Vector2[] polygon)
        {
            if (PointInsideOrOnConvex(point, polygon)) return 0f;
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

        static bool PointInsideOrOnConvex(Vector2 point, Vector2[] polygon)
        {
            float sign = 0f;
            for (int index = 0; index < polygon.Length; index++)
            {
                float cross = Cross(
                    polygon[(index + 1) % polygon.Length] - polygon[index],
                    point - polygon[index]);
                if (Mathf.Abs(cross) <= GeometryEpsilon) continue;
                float current = Mathf.Sign(cross);
                if (sign == 0f) sign = current;
                else if (current != sign) return false;
            }
            return true;
        }

        internal static bool IntervalsOverlap(
            float leftMin,
            float leftMax,
            float rightMin,
            float rightMax) =>
            leftMin <= rightMax + GeometryEpsilon
            && leftMax >= rightMin - GeometryEpsilon;

        static float HorizontalDistanceSquared(Vector3 left, Vector3 right)
        {
            float dx = left.x - right.x;
            float dz = left.z - right.z;
            return dx * dx + dz * dz;
        }

        internal static Vector2 ToXZ(Vector3 value) => new Vector2(value.x, value.z);
        static float Cross(Vector2 left, Vector2 right) =>
            left.x * right.y - left.y * right.x;
        static bool FiniteNonZero(float value) =>
            value != 0f && !float.IsNaN(value) && !float.IsInfinity(value);
    }
}
