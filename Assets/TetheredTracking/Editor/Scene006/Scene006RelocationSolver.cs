using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// §3.3.2 / §9-step-11 relocation machinery for family B (batch 1b).
    ///
    /// The five authorized rows are the authorized scene content. This
    /// solver RE-COMPUTES the landings by the frozen rules — unique instance
    /// binding (prefab_name + original_xz_m, tolerance 0.1 m); nearest
    /// segment with lowest-index tie-break (|Δ| &lt;= 1e-6); left normal
    /// (-dir.z, dir.x) and its reverse; 0.1 m stepping (d = 0.1 * step, no
    /// accumulation drift) up to 30.0 m per side; first displacement
    /// satisfying (a) footprint-to-route distance &gt;= 2.0 m (0.25 m
    /// sampled polyline, point-to-footprint), (b) full road-surface coverage
    /// of the landing footprint on a 0.25 m grid, (c) zero overlap with the
    /// ground obstacle instances (thickness &gt; 0.05 m, self excluded),
    /// (d) zero overlap with already-placed relocations in application
    /// order; both sides solved takes the smaller displacement, ties take
    /// left — and compares them against the authorized rows. Any
    /// disagreement is RELOCATION_RECOMPUTE_MISMATCH (fail closed); no
    /// legal landing within 30 m is RELOCATION_NO_LEGAL_LANDING.
    ///
    /// The landing audit (§2.2a generalized static audit with the parked
    /// vehicle itself as the audit object + §2.2b road-data recheck)
    /// re-verifies (b)/(c)/(d) on the applied scene state; any failure is
    /// RELOCATION_LANDING_ILLEGAL. All three named terminals return to
    /// Acceptance; nothing here deletes a vehicle, changes a coordinate or
    /// "takes the tool value" over the authorized rows.
    /// </summary>
    public static class Scene006RelocationSolver
    {
        public const float StepM = 0.1f;
        public const float MaxDisplacementM = 30.0f;
        public const float RouteSampleSpacingM = 0.25f;
        public const float CoverageGridM = 0.25f;
        public const float RouteClearanceMinM = 2.0f;
        public const float SegmentTieEpsM = 1e-6f;
        public const float OverlapEpsM = 1e-5f;
        public const float MinObstacleThicknessM = 0.05f;
        // The authorized coordinates are published at 3 decimals; the
        // recompute comparison tolerance is the rounding level, not a
        // silent-override channel.
        public const float AuthorizedCompareToleranceM = 5e-4f;

        public sealed class InstanceFootprint
        {
            public string Name;
            public Vector2[] Corners; // world XZ, ground footprint
            public float MinY;
            public float MaxY;
            public Vector2 Center;
            public Vector3 RootPosition;
        }

        public sealed class RecomputedLanding
        {
            public bool Solved;
            public int NearestSegmentIndex;
            public string Direction;
            public float DisplacementM;
            public Vector3 NewPosition;
        }

        [Serializable]
        public sealed class RelocationRecord
        {
            public string prefab_name;
            public float original_x_m;
            public float original_z_m;
            public float current_route_clearance_m;
            public int authorized_segment_index;
            public int recomputed_segment_index;
            public string authorized_direction;
            public string recomputed_direction;
            public float authorized_displacement_m;
            public float recomputed_displacement_m;
            public Scene006Evaluation.Vec3 authorized_new_position_m;
            public Scene006Evaluation.Vec3 recomputed_new_position_m;
            public bool recompute_match;
            public bool landing_road_coverage;
            public bool landing_static_clearance;
            public string landing_blocking_object;
        }

        // ----------------------------------------------------------------
        // Footprints
        // ----------------------------------------------------------------

        /// <summary>
        /// Transformed ground footprint (XZ corners at local y = 0 from the
        /// ground bounds) with the full-bounds vertical range, replicating
        /// the anchor-audit TRS checks (fail closed on unsupported TRS).
        /// </summary>
        public static InstanceFootprint BuildFootprint(
            Transform root,
            RoadObstacleFootprint source)
        {
            Vector3 scale = root.lossyScale;
            bool unsupported = scale.x == 0f || scale.y == 0f || scale.z == 0f
                || !Scene006RouteGeometry.Finite(scale.x)
                || !Scene006RouteGeometry.Finite(scale.y)
                || !Scene006RouteGeometry.Finite(scale.z)
                || Vector3.Angle(root.up, Vector3.up) > 0.01f;
            if (unsupported)
                throw new InvalidOperationException(
                    "unsupported_anchor_audit_trs:" + root.name);

            float minY = float.PositiveInfinity;
            float maxY = float.NegativeInfinity;
            foreach (float x in new[] { source.full_min_x_m, source.full_max_x_m })
            {
                foreach (float y in new[] { source.full_min_y_m, source.full_max_y_m })
                {
                    foreach (float z in new[] { source.full_min_z_m, source.full_max_z_m })
                    {
                        float worldY = root.TransformPoint(new Vector3(x, y, z)).y;
                        minY = Mathf.Min(minY, worldY);
                        maxY = Mathf.Max(maxY, worldY);
                    }
                }
            }
            Vector2[] corners =
            {
                ToXZ(root.TransformPoint(new Vector3(
                    source.ground_min_x_m, 0f, source.ground_min_z_m))),
                ToXZ(root.TransformPoint(new Vector3(
                    source.ground_max_x_m, 0f, source.ground_min_z_m))),
                ToXZ(root.TransformPoint(new Vector3(
                    source.ground_max_x_m, 0f, source.ground_max_z_m))),
                ToXZ(root.TransformPoint(new Vector3(
                    source.ground_min_x_m, 0f, source.ground_max_z_m))),
            };
            var footprint = new InstanceFootprint
            {
                Name = root.name,
                Corners = corners,
                MinY = minY,
                MaxY = maxY,
                RootPosition = root.position,
            };
            Vector2 center = Vector2.zero;
            foreach (Vector2 corner in corners) center += corner;
            footprint.Center = center / corners.Length;
            return footprint;
        }

        static Vector2 ToXZ(Vector3 value) => new Vector2(value.x, value.z);

        public static InstanceFootprint Translated(
            InstanceFootprint source, Vector2 offset, string name = null)
        {
            var corners = new Vector2[source.Corners.Length];
            for (int index = 0; index < corners.Length; index++)
                corners[index] = source.Corners[index] + offset;
            return new InstanceFootprint
            {
                Name = name ?? source.Name,
                Corners = corners,
                MinY = source.MinY,
                MaxY = source.MaxY,
                Center = source.Center + offset,
            };
        }

        // ----------------------------------------------------------------
        // Geometry primitives
        // ----------------------------------------------------------------

        /// <summary>
        /// Footprint-to-route distance: the closed route polyline sampled
        /// every 0.25 m, point-to-footprint distance (§9 step 11).
        /// </summary>
        public static float FootprintRouteDistance(
            InstanceFootprint footprint,
            IReadOnlyList<Vector3> route)
        {
            float best = float.PositiveInfinity;
            foreach (Vector2 sample in SampleClosedRouteXZ(route, RouteSampleSpacingM))
            {
                best = Mathf.Min(
                    best,
                    Scene006PathCertificate.DistanceToConvex(
                        sample, footprint.Corners));
            }
            return best;
        }

        public static IEnumerable<Vector2> SampleClosedRouteXZ(
            IReadOnlyList<Vector3> route, float spacing)
        {
            for (int index = 0; index < route.Count; index++)
            {
                Vector3 start3 = route[index];
                Vector3 end3 = route[(index + 1) % route.Count];
                Vector2 start = new Vector2(start3.x, start3.z);
                Vector2 end = new Vector2(end3.x, end3.z);
                float length = Vector2.Distance(start, end);
                if (length <= 1e-6f) continue;
                int steps = Mathf.CeilToInt(length / spacing);
                for (int step = 0; step < steps; step++)
                    yield return Vector2.Lerp(start, end, step / (float)steps);
            }
        }

        /// <summary>
        /// Nearest route segment to a point; |distance Δ| &lt;= 1e-6 ties go
        /// to the lowest segment index (§3.3.2 direction rule).
        /// </summary>
        public static int NearestSegmentIndex(
            Vector2 point, IReadOnlyList<Vector3> route)
        {
            float best = float.PositiveInfinity;
            int bestIndex = -1;
            for (int index = 0; index < route.Count; index++)
            {
                Vector3 start3 = route[index];
                Vector3 end3 = route[(index + 1) % route.Count];
                Vector2 start = new Vector2(start3.x, start3.z);
                Vector2 end = new Vector2(end3.x, end3.z);
                Vector2 delta = end - start;
                float length = delta.magnitude;
                if (length <= 1e-6f) continue;
                float along = Mathf.Clamp(
                    Vector2.Dot(point - start, delta / length), 0f, length);
                float distance = Vector2.Distance(
                    point, start + delta / length * along);
                if (distance < best - SegmentTieEpsM)
                {
                    best = distance;
                    bestIndex = index;
                }
            }
            if (bestIndex < 0)
                throw new ArgumentException("route has no non-zero segment");
            return bestIndex;
        }

        /// <summary>Left normal of the segment in route order: (-dir.z, dir.x).</summary>
        public static Vector2 LeftNormal(IReadOnlyList<Vector3> route, int segmentIndex)
        {
            Vector3 start3 = route[segmentIndex];
            Vector3 end3 = route[(segmentIndex + 1) % route.Count];
            Vector2 delta = new Vector2(end3.x - start3.x, end3.z - start3.z);
            Vector2 direction = delta.normalized;
            return new Vector2(-direction.y, direction.x);
        }

        /// <summary>
        /// Road-surface coverage: the footprint interior sampled on a
        /// 0.25 m grid; every sample must lie strictly inside the union of
        /// the road_data surface rectangles (StrictlyInsideSurface
        /// semantics replicated from P1Scene003AnchorAudit.cs:486-502, which
        /// is internal to the runtime assembly).
        /// </summary>
        public static bool FullyOnRoadSurfaces(
            InstanceFootprint footprint, RoadSceneData roadData)
        {
            float minX = float.PositiveInfinity;
            float maxX = float.NegativeInfinity;
            float minZ = float.PositiveInfinity;
            float maxZ = float.NegativeInfinity;
            foreach (Vector2 corner in footprint.Corners)
            {
                minX = Mathf.Min(minX, corner.x);
                maxX = Mathf.Max(maxX, corner.x);
                minZ = Mathf.Min(minZ, corner.y);
                maxZ = Mathf.Max(maxZ, corner.y);
            }
            for (float x = minX; x <= maxX + 1e-6f; x += CoverageGridM)
            {
                for (float z = minZ; z <= maxZ + 1e-6f; z += CoverageGridM)
                {
                    var point = new Vector2(
                        Mathf.Min(x, maxX), Mathf.Min(z, maxZ));
                    if (Scene006PathCertificate.DistanceToConvex(
                            point, footprint.Corners) > OverlapEpsM)
                    {
                        continue;
                    }
                    bool covered = false;
                    foreach (RoadSurfacePatch surface in roadData.surfaces)
                    {
                        if (StrictlyInsideSurface(point, surface))
                        {
                            covered = true;
                            break;
                        }
                    }
                    if (!covered) return false;
                }
            }
            return true;
        }

        static bool StrictlyInsideSurface(Vector2 point, RoadSurfacePatch surface)
        {
            float radians = -surface.yaw_deg * Mathf.Deg2Rad;
            float cosine = Mathf.Cos(radians);
            float sine = Mathf.Sin(radians);
            Vector2 delta = point - new Vector2(
                surface.center_x_m, surface.center_z_m);
            float localX = cosine * delta.x - sine * delta.y;
            float localZ = sine * delta.x + cosine * delta.y;
            return Mathf.Abs(localX)
                    < surface.half_extent_x_m - OverlapEpsM
                && Mathf.Abs(localZ)
                    < surface.half_extent_z_m - OverlapEpsM;
        }

        /// <summary>
        /// Convex polygon overlap by the separating-axis test; closed-set
        /// tangency counts as overlap (the T5 convention).
        /// </summary>
        public static bool Overlaps(Vector2[] left, Vector2[] right)
        {
            return !Separated(left, right) && !Separated(right, left);
        }

        static bool Separated(Vector2[] reference, Vector2[] other)
        {
            for (int index = 0; index < reference.Length; index++)
            {
                Vector2 edge = reference[(index + 1) % reference.Length]
                    - reference[index];
                Vector2 axis = new Vector2(-edge.y, edge.x);
                if (axis.sqrMagnitude <= 1e-12f) continue;
                float refMin = float.PositiveInfinity;
                float refMax = float.NegativeInfinity;
                foreach (Vector2 vertex in reference)
                {
                    float projection = Vector2.Dot(vertex, axis);
                    refMin = Mathf.Min(refMin, projection);
                    refMax = Mathf.Max(refMax, projection);
                }
                float otherMin = float.PositiveInfinity;
                float otherMax = float.NegativeInfinity;
                foreach (Vector2 vertex in other)
                {
                    float projection = Vector2.Dot(vertex, axis);
                    otherMin = Mathf.Min(otherMin, projection);
                    otherMax = Mathf.Max(otherMax, projection);
                }
                // Strict separation requires a real gap; closed-set
                // tangency (gap <= eps) is overlap by the T5 convention.
                if (otherMax < refMin - OverlapEpsM
                    || refMax < otherMin - OverlapEpsM)
                {
                    return true;
                }
            }
            return false;
        }

        // ----------------------------------------------------------------
        // The frozen search
        // ----------------------------------------------------------------

        /// <summary>
        /// Recomputes one landing by the frozen rules. sceneObstacles must
        /// contain every ground obstacle instance (thickness &gt; 0.05 m)
        /// at its scene position with ONLY the subject excluded — the other
        /// relocation targets still count at their original positions (the
        /// "763 = 764 − self" accounting of §9 step 11) — and
        /// placedRelocations the already-placed rows at their new
        /// positions; that split is exactly the frozen (c)/(d) pair.
        /// </summary>
        public static RecomputedLanding Recompute(
            InstanceFootprint subject,
            IReadOnlyList<Vector3> route,
            RoadSceneData roadData,
            IReadOnlyList<InstanceFootprint> sceneObstacles,
            IReadOnlyList<InstanceFootprint> placedRelocations)
        {
            int segmentIndex = NearestSegmentIndex(subject.Center, route);
            Vector2 left = LeftNormal(route, segmentIndex);
            var result = new RecomputedLanding
            {
                NearestSegmentIndex = segmentIndex,
            };
            float? leftSolution = Search(
                subject, left, route, roadData, sceneObstacles,
                placedRelocations);
            float? rightSolution = Search(
                subject, -left, route, roadData, sceneObstacles,
                placedRelocations);
            if (leftSolution == null && rightSolution == null)
            {
                result.Solved = false;
                return result;
            }
            bool takeLeft;
            float displacement;
            if (leftSolution == null)
            {
                takeLeft = false;
                displacement = rightSolution.Value;
            }
            else if (rightSolution == null)
            {
                takeLeft = true;
                displacement = leftSolution.Value;
            }
            else if (leftSolution.Value < rightSolution.Value - 1e-6f)
            {
                takeLeft = true;
                displacement = leftSolution.Value;
            }
            else if (rightSolution.Value < leftSolution.Value - 1e-6f)
            {
                takeLeft = false;
                displacement = rightSolution.Value;
            }
            else
            {
                takeLeft = true; // displacement tie takes the left normal
                displacement = leftSolution.Value;
            }
            Vector2 offset = (takeLeft ? left : -left) * displacement;
            result.Solved = true;
            result.Direction = takeLeft ? "left" : "right";
            result.DisplacementM = displacement;
            // The landing position is the ROOT's new position: the vehicle
            // moves as a rigid body, so the root shifts by the same offset
            // as the footprint; the footprint centroid is not the anchor
            // point (the mesh ground bounds are not centred on the root).
            result.NewPosition = new Vector3(
                subject.RootPosition.x + offset.x,
                0f,
                subject.RootPosition.z + offset.y);
            return result;
        }

        static float? Search(
            InstanceFootprint subject,
            Vector2 normal,
            IReadOnlyList<Vector3> route,
            RoadSceneData roadData,
            IReadOnlyList<InstanceFootprint> sceneObstacles,
            IReadOnlyList<InstanceFootprint> placedRelocations)
        {
            int maxStep = Mathf.RoundToInt(MaxDisplacementM / StepM);
            for (int step = 1; step <= maxStep; step++)
            {
                float displacement = StepM * step;
                InstanceFootprint landing =
                    Translated(subject, normal * displacement);
                if (FootprintRouteDistance(landing, route)
                        < RouteClearanceMinM)
                {
                    continue;
                }
                if (!FullyOnRoadSurfaces(landing, roadData)) continue;
                bool blocked = false;
                foreach (InstanceFootprint obstacle in sceneObstacles)
                {
                    if (Overlaps(landing.Corners, obstacle.Corners))
                    {
                        blocked = true;
                        break;
                    }
                }
                if (blocked) continue;
                foreach (InstanceFootprint placed in placedRelocations)
                {
                    if (Overlaps(landing.Corners, placed.Corners))
                    {
                        blocked = true;
                        break;
                    }
                }
                if (blocked) continue;
                return displacement;
            }
            return null;
        }

        // ----------------------------------------------------------------
        // Row comparison
        // ----------------------------------------------------------------

        public static bool Matches(
            Scene006CandidateContract.AuthorizedRelocation authorized,
            RecomputedLanding recomputed)
        {
            if (!recomputed.Solved) return false;
            if (recomputed.NearestSegmentIndex
                != authorized.NearestSegmentIndex) return false;
            if (!string.Equals(
                recomputed.Direction, authorized.Direction,
                StringComparison.Ordinal)) return false;
            if (Mathf.Abs(recomputed.DisplacementM - authorized.DisplacementM)
                > AuthorizedCompareToleranceM) return false;
            return Vector3.Distance(
                recomputed.NewPosition, authorized.NewPosition)
                <= AuthorizedCompareToleranceM;
        }
    }
}
