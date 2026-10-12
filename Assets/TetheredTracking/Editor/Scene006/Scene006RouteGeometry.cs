using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// Closed-route geometry for the P1-SCENE-006 batch-1 offline tools.
    /// ClosedRoutePerimeter/SampleClosedRoute replicate the internal
    /// RateStudyScouting semantics (Scripts/RateStudyScouting.cs:35-87)
    /// operation-for-operation in float32 so the frozen trace matches the
    /// runtime vehicle; the internal originals are not accessible from this
    /// assembly, and EditMode tests cross-check equivalence against them.
    /// </summary>
    public static class Scene006RouteGeometry
    {
        public readonly struct RouteSample
        {
            public readonly Vector3 Position;
            public readonly int NextWaypointIndex;

            public RouteSample(Vector3 position, int nextWaypointIndex)
            {
                Position = position;
                NextWaypointIndex = nextWaypointIndex;
            }
        }

        public static bool Finite(float value) =>
            !float.IsNaN(value) && !float.IsInfinity(value);

        public static bool IsSha256(string value)
        {
            if (string.IsNullOrEmpty(value) || value.Length != 64) return false;
            foreach (char character in value)
            {
                bool digit = character >= '0' && character <= '9';
                bool lower = character >= 'a' && character <= 'f';
                if (!digit && !lower) return false;
            }
            return true;
        }

        public static string Sha256Hex(byte[] bytes)
        {
            using SHA256 sha = SHA256.Create();
            byte[] digest = sha.ComputeHash(bytes);
            var builder = new StringBuilder(digest.Length * 2);
            foreach (byte value in digest) builder.Append(value.ToString("x2"));
            return builder.ToString();
        }

        static void ValidateRoute(IReadOnlyList<Vector3> route)
        {
            if (route == null || route.Count < 2)
                throw new ArgumentException(
                    "Route requires at least two points.", nameof(route));
            foreach (Vector3 point in route)
            {
                if (!Finite(point.x) || !Finite(point.y) || !Finite(point.z))
                    throw new ArgumentException(
                        "Route points must be finite.", nameof(route));
            }
        }

        public static float ClosedRoutePerimeter(IReadOnlyList<Vector3> route)
        {
            ValidateRoute(route);
            float perimeter = 0f;
            for (int index = 0; index < route.Count; index++)
                perimeter += Vector3.Distance(
                    route[index], route[(index + 1) % route.Count]);
            if (!Finite(perimeter) || perimeter <= Mathf.Epsilon)
                throw new ArgumentException(
                    "Closed route perimeter must be positive.", nameof(route));
            return perimeter;
        }

        public static RouteSample SampleClosedRoute(
            IReadOnlyList<Vector3> route,
            float distanceMeters)
        {
            ValidateRoute(route);
            if (!Finite(distanceMeters) || distanceMeters < 0f)
                throw new ArgumentOutOfRangeException(nameof(distanceMeters));
            float perimeter = ClosedRoutePerimeter(route);
            float remaining = distanceMeters % perimeter;
            for (int index = 0; index < route.Count; index++)
            {
                int next = (index + 1) % route.Count;
                float length = Vector3.Distance(route[index], route[next]);
                if (length <= Mathf.Epsilon) continue;
                if (remaining < length || index == route.Count - 1)
                {
                    float fraction = Mathf.Clamp01(remaining / length);
                    return new RouteSample(
                        Vector3.Lerp(route[index], route[next], fraction),
                        next);
                }
                remaining -= length;
            }
            throw new InvalidOperationException(
                "Closed route contains no positive segment.");
        }

        /// <summary>
        /// Minimum horizontal (XZ) distance from a point to the closed route
        /// polyline. Used by the T5 route-anchor sub-gate (>= 1.5 m).
        /// </summary>
        public static float DistanceToClosedRoute(
            Vector2 point,
            IReadOnlyList<Vector3> route)
        {
            ValidateRoute(route);
            float best = float.PositiveInfinity;
            for (int index = 0; index < route.Count; index++)
            {
                Vector2 start = new Vector2(route[index].x, route[index].z);
                Vector3 end3 = route[(index + 1) % route.Count];
                Vector2 end = new Vector2(end3.x, end3.z);
                Vector2 delta = end - start;
                float length = delta.magnitude;
                if (length <= 1e-6f) continue;
                Vector2 direction = delta / length;
                float along = Mathf.Clamp(
                    Vector2.Dot(point - start, direction), 0f, length);
                best = Mathf.Min(
                    best, Vector2.Distance(point, start + direction * along));
            }
            if (float.IsInfinity(best))
                throw new ArgumentException(
                    "Route contains no non-zero-length segment.");
            return best;
        }

        /// <summary>
        /// Gimbal-request off-nadir angle from a body position to a route
        /// point, using the TetheredGimbal.LateUpdate formula
        /// (Scripts/TetheredGimbal.cs:33-37): atan2(horizontal,
        /// max(0.1, -delta.y)) in degrees.
        /// </summary>
        public static float OffAxisDeg(Vector3 bodyPosition, Vector3 routePoint)
        {
            Vector3 delta = routePoint - bodyPosition;
            float horizontal = new Vector2(delta.x, delta.z).magnitude;
            float height = Mathf.Max(0.1f, -delta.y);
            return Mathf.Atan2(horizontal, height) * Mathf.Rad2Deg;
        }

        /// <summary>
        /// §3.6 frozen initial phase: s_init = argmin over s in [0, perimeter)
        /// of the off-axis angle from p_hover to the route point at s; ties
        /// take the smaller s. The minimum over each segment is attained at
        /// the clamped perpendicular projection of the body XZ onto the
        /// segment (or an endpoint), so the scan is analytic and
        /// deterministic. Baseline batches use s_init = 0 (§5.2.2); this
        /// computation exists for candidate-side completeness.
        /// </summary>
        public static float ArgminOffAxisPhase(
            Vector3 bodyPosition,
            IReadOnlyList<Vector3> route)
        {
            ValidateRoute(route);
            float bestAngle = float.PositiveInfinity;
            float bestS = 0f;
            float prefix = 0f;
            for (int index = 0; index < route.Count; index++)
            {
                Vector3 start = route[index];
                Vector3 end = route[(index + 1) % route.Count];
                Vector2 delta = new Vector2(end.x - start.x, end.z - start.z);
                float length = delta.magnitude;
                if (length <= 1e-6f) continue;
                float u = Mathf.Clamp01(
                    Vector2.Dot(
                        new Vector2(
                            bodyPosition.x - start.x,
                            bodyPosition.z - start.z),
                        delta / length)
                    / length);
                Vector3 point = Vector3.Lerp(start, end, u);
                float angle = OffAxisDeg(bodyPosition, point);
                if (angle < bestAngle)
                {
                    bestAngle = angle;
                    bestS = prefix + u * length;
                }
                prefix += length;
            }
            if (float.IsInfinity(bestAngle))
                throw new ArgumentException(
                    "Route contains no non-zero-length segment.");
            return bestS;
        }
    }
}
