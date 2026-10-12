using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// §5.4 T4 witness path certificates (the single frozen construction).
    ///
    /// Path shape: the straight segment p_hover -&gt; p. Both endpoints lie
    /// inside the tether ball (convex) and inside the [8, 32] m AGL band, so
    /// the whole segment does by convexity; these two facts are recorded,
    /// not re-sampled. The speed profile is rest-to-rest trapezoidal with
    /// |v| &lt;= 4.0 m/s and |a| &lt;= 4.0 m/s^2; its analytic duration is
    /// recorded and feeds no gate threshold.
    ///
    /// Clearance: conservative discrete sampling with N = ceil(len / delta),
    /// delta = 0.25 m, u_i = i * len / N for i = 0..N including both
    /// endpoints, so every path point lies within delta/2 of a sample. At
    /// each sample: (a) body sphere radius 1.0 + 0.5 + 0.125 = 1.625 m;
    /// (b) tether capsule anchor -&gt; sample with nominal 0.25 m + the same
    /// delta/2 inflation = 0.375 m (the per-parameter-point continuity
    /// argument of §5.4.3 covers every intermediate tether configuration
    /// between samples). Any sample violation fails the certificate.
    ///
    /// Anchor-end support trim (§5.4.4, literal — F2 fix, batch 1b): the
    /// head segment [0, d_trim] of every tether capsule queries ALL
    /// colliders and ignores only the bound measured support instance;
    /// the remainder beyond d_trim ignores nothing. d_trim = 1.70 m is
    /// derived from the station set's minimum tether elevation
    /// theta_min = atan(8 / sqrt(35^2 - 8^2)) = 13.212980 deg, so the
    /// inflated capsule cannot touch the support plane outside the trimmed
    /// head segment (1.70 * sin(theta_min) = 0.388571 &gt;= 0.375). The
    /// candidate obstacle set is the full instance set — road-surface and
    /// support-allowlist instances included (Scene006SceneRig.
    /// BuildAllInstancePrisms) — so a tether capsule crossing a road
    /// surface inside or outside the head segment fails closed, exactly as
    /// the frozen text requires. The batch-1 baseline path passes the T5
    /// obstacle set (road/support excluded by construction) with a null
    /// bound instance, which reproduces the batch-1 structural form.
    /// The bound is recorded in every artifact.
    ///
    /// Closed-set tangency counts as a violation (distance &lt;= radius +
    /// GeometryEpsilon), matching the T5 audit convention.
    /// </summary>
    public static class Scene006PathCertificate
    {
        public const float GeometryEpsilon = 1e-5f;
        public const float SamplingDeltaM = 0.25f;
        public const float BodyRadiusM = 1.625f;
        public const float TetherRadiusM = 0.375f;
        public const float TrimDistanceM = 1.70f;
        public const float MaxSpeedMps = 4.0f;
        public const float MaxAccelerationMps2 = 4.0f;
        public const float BallRadiusM = 35f;
        public const float MinBandAglM = 8f;
        public const float MaxBandAglM = 32f;
        public const float MinTetherElevationDeg = 13.212980f;

        public readonly struct ObstaclePrism
        {
            public readonly string Id;
            public readonly Vector2[] Corners;
            public readonly float MinY;
            public readonly float MaxY;

            public ObstaclePrism(
                string id, Vector2[] corners, float minY, float maxY)
            {
                Id = id;
                Corners = corners;
                MinY = minY;
                MaxY = maxY;
            }
        }

        public readonly struct Certificate
        {
            public readonly bool PathRejected;
            public readonly bool BodyRejected;
            public readonly bool TetherRejected;
            public readonly string BlockingObstacle;
            public readonly float DurationSeconds;
            public readonly int SampleCount;

            public bool Passed =>
                !PathRejected && !BodyRejected && !TetherRejected;

            public Certificate(
                bool pathRejected,
                bool bodyRejected,
                bool tetherRejected,
                string blockingObstacle,
                float durationSeconds,
                int sampleCount)
            {
                PathRejected = pathRejected;
                BodyRejected = bodyRejected;
                TetherRejected = tetherRejected;
                BlockingObstacle = blockingObstacle;
                DurationSeconds = durationSeconds;
                SampleCount = sampleCount;
            }
        }

        public static float TrapezoidDuration(float lengthM)
        {
            // Rest-to-rest with vmax = 4 m/s, amax = 4 m/s^2: triangular when
            // the cruise segment vanishes (length <= vmax^2 / amax = 4 m).
            if (lengthM <= MaxSpeedMps * MaxSpeedMps / MaxAccelerationMps2)
                return 2f * Mathf.Sqrt(lengthM / MaxAccelerationMps2);
            return lengthM / MaxSpeedMps + MaxSpeedMps / MaxAccelerationMps2;
        }

        public static Certificate Evaluate(
            Vector3 anchor,
            Vector3 pHover,
            float supportY,
            Vector3 station,
            IReadOnlyList<ObstaclePrism> obstacles,
            string supportInstanceId)
        {
            // §5.4.4 literal: the bound measured support instance must be
            // present in the queried set whenever one is named; silently
            // trimming an absent instance would weaken the head segment.
            if (supportInstanceId != null)
            {
                bool found = false;
                foreach (ObstaclePrism prism in obstacles)
                {
                    if (prism.Id == supportInstanceId)
                    {
                        found = true;
                        break;
                    }
                }
                if (!found)
                {
                    throw new InvalidOperationException(
                        "bound support instance is absent from the "
                        + "certificate obstacle set: " + supportInstanceId);
                }
            }
            // §5.4.1: the path is the straight segment p_hover -> station;
            // the tether capsule always runs from the anchor (ground) to the
            // sampled body position. Endpoint ball/band membership holds by
            // convexity of the ball and the band; both are verified here.
            Vector3 delta = station - pHover;
            float length = delta.magnitude;
            bool pathRejected = !Scene006RouteGeometry.Finite(length)
                || Vector3.Distance(anchor, pHover)
                    > BallRadiusM + GeometryEpsilon
                || Vector3.Distance(anchor, station)
                    > BallRadiusM + GeometryEpsilon
                || pHover.y - supportY < MinBandAglM - GeometryEpsilon
                || pHover.y - supportY > MaxBandAglM + GeometryEpsilon
                || station.y - supportY < MinBandAglM - GeometryEpsilon
                || station.y - supportY > MaxBandAglM + GeometryEpsilon;
            if (pathRejected)
                return new Certificate(true, false, false, null, 0f, 0);

            float duration = TrapezoidDuration(length);
            int intervals = Mathf.Max(
                0, Mathf.CeilToInt(length / SamplingDeltaM));

            // Broadphase: a violation needs distance <= 1.625 m somewhere
            // inside the swept triangle (anchor, p_hover, station), so
            // prisms whose AABB cannot reach the inflated triangle AABB are
            // exact rejects and skip the per-sample golden-section work.
            float inflate = BodyRadiusM + GeometryEpsilon;
            float pathMinX = Mathf.Min(
                anchor.x, Mathf.Min(pHover.x, station.x)) - inflate;
            float pathMaxX = Mathf.Max(
                anchor.x, Mathf.Max(pHover.x, station.x)) + inflate;
            float pathMinY = Mathf.Min(
                anchor.y, Mathf.Min(pHover.y, station.y)) - inflate;
            float pathMaxY = Mathf.Max(
                anchor.y, Mathf.Max(pHover.y, station.y)) + inflate;
            float pathMinZ = Mathf.Min(
                anchor.z, Mathf.Min(pHover.z, station.z)) - inflate;
            float pathMaxZ = Mathf.Max(
                anchor.z, Mathf.Max(pHover.z, station.z)) + inflate;
            var survivors = new List<ObstaclePrism>(obstacles.Count);
            foreach (ObstaclePrism prism in obstacles)
            {
                float minX = float.PositiveInfinity;
                float maxX = float.NegativeInfinity;
                float minZ = float.PositiveInfinity;
                float maxZ = float.NegativeInfinity;
                foreach (Vector2 corner in prism.Corners)
                {
                    minX = Mathf.Min(minX, corner.x);
                    maxX = Mathf.Max(maxX, corner.x);
                    minZ = Mathf.Min(minZ, corner.y);
                    maxZ = Mathf.Max(maxZ, corner.y);
                }
                bool reachable = minX <= pathMaxX && maxX >= pathMinX
                    && minZ <= pathMaxZ && maxZ >= pathMinZ
                    && prism.MinY <= pathMaxY && prism.MaxY >= pathMinY;
                if (reachable) survivors.Add(prism);
            }

            // Sample the segment at u_i = i * len / N including both
            // endpoints. A zero-length path (station == p_hover) degenerates
            // to the single hold configuration: one sample at p_hover, so
            // the body-at-hover and vertical-tether checks still run.
            bool bodyRejected = false;
            bool tetherRejected = false;
            string blocking = null;
            for (int i = 0; i <= intervals; i++)
            {
                float fraction = intervals == 0 ? 0f : i / (float)intervals;
                Vector3 sample = pHover + delta * fraction;
                foreach (ObstaclePrism prism in survivors)
                {
                    if (!bodyRejected
                        && PointPrismDistance(sample, prism)
                            <= BodyRadiusM + GeometryEpsilon)
                    {
                        bodyRejected = true;
                        blocking = prism.Id;
                    }
                    // §5.4.4 literal: for the bound measured support
                    // instance the head segment [0, d_trim] of the tether is
                    // exempt; every other instance — road surfaces and
                    // support-allowlist instances included — is queried over
                    // the full anchor -> sample segment.
                    bool boundSupport = supportInstanceId != null
                        && prism.Id == supportInstanceId;
                    float tetherDistance = boundSupport
                        ? TrimmedSegmentPrismDistance(anchor, sample, prism)
                        : SegmentPrismDistance(anchor, sample, prism);
                    if (!tetherRejected
                        && tetherDistance <= TetherRadiusM + GeometryEpsilon)
                    {
                        tetherRejected = true;
                        blocking = prism.Id;
                    }
                }
                if (bodyRejected && tetherRejected) break;
            }
            return new Certificate(
                false,
                bodyRejected,
                tetherRejected,
                blocking,
                duration,
                intervals + 1);
        }

        public static float PointPrismDistance(
            Vector3 point,
            ObstaclePrism prism)
        {
            float horizontal = DistanceToConvex(
                new Vector2(point.x, point.z), prism.Corners);
            float vertical = VerticalGap(point.y, prism.MinY, prism.MaxY);
            return Mathf.Sqrt(horizontal * horizontal + vertical * vertical);
        }

        /// <summary>
        /// Exact distance between the anchor-&gt;sample segment and an
        /// extruded convex prism. The per-parameter distance
        /// f(t) = dxz(t)^2 + dy(t)^2 is convex on [0, 1] (each term is a
        /// convex distance composed with an affine map), so golden-section
        /// minimization converges to the global minimum; 80 iterations make
        /// the bracket far below any float32 relevance.
        /// </summary>
        public static float SegmentPrismDistance(
            Vector3 a,
            Vector3 b,
            ObstaclePrism prism)
        {
            float F(float t)
            {
                Vector3 point = a + (b - a) * t;
                float horizontal = DistanceToConvex(
                    new Vector2(point.x, point.z), prism.Corners);
                float vertical = VerticalGap(point.y, prism.MinY, prism.MaxY);
                return horizontal * horizontal + vertical * vertical;
            }

            const double invPhi = 0.6180339887498949; // (sqrt(5) - 1) / 2
            double left = 0.0;
            double right = 1.0;
            double c = right - invPhi * (right - left);
            double d = left + invPhi * (right - left);
            double fc = F((float)c);
            double fd = F((float)d);
            for (int iteration = 0; iteration < 80; iteration++)
            {
                if (fc < fd)
                {
                    right = d;
                    d = c;
                    fd = fc;
                    c = right - invPhi * (right - left);
                    fc = F((float)c);
                }
                else
                {
                    left = c;
                    c = d;
                    fc = fd;
                    d = left + invPhi * (right - left);
                    fd = F((float)d);
                }
            }
            return Mathf.Sqrt((float)Math.Min(fc, fd));
        }

        /// <summary>
        /// Distance from the tether segment with the head [0, d_trim]
        /// removed — the §5.4.4 literal head trim applied to the bound
        /// measured support instance. When the segment is shorter than
        /// d_trim the whole segment is trimmed, which is only reachable for
        /// a degenerate zero-length hold configuration whose vertical
        /// tether is longer than d_trim by construction (AGL &gt;= 8 m).
        /// </summary>
        public static float TrimmedSegmentPrismDistance(
            Vector3 anchor,
            Vector3 sample,
            ObstaclePrism prism)
        {
            Vector3 delta = sample - anchor;
            float length = delta.magnitude;
            if (length <= TrimDistanceM) return float.PositiveInfinity;
            Vector3 trimmedStart =
                anchor + delta * (TrimDistanceM / length);
            return SegmentPrismDistance(trimmedStart, sample, prism);
        }

        static float VerticalGap(float value, float minY, float maxY)
        {
            if (value < minY) return minY - value;
            if (value > maxY) return value - maxY;
            return 0f;
        }

        // 2D convex-polygon distance, replicating the T5 audit primitives
        // (Scripts/P1Scene003AnchorAudit.cs:613-647): points inside or on the
        // polygon are at distance zero; otherwise the minimum edge distance.
        public static float DistanceToConvex(Vector2 point, Vector2[] polygon)
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
                    : Mathf.Clamp01(
                        Vector2.Dot(point - start, delta) / delta.sqrMagnitude);
                minimum = Mathf.Min(
                    minimum, Vector2.Distance(point, start + t * delta));
            }
            return minimum;
        }

        static bool PointInsideOrOnConvex(Vector2 point, Vector2[] polygon)
        {
            float sign = 0f;
            for (int index = 0; index < polygon.Length; index++)
            {
                Vector2 edge = polygon[(index + 1) % polygon.Length]
                    - polygon[index];
                Vector2 toPoint = point - polygon[index];
                float cross = edge.x * toPoint.y - edge.y * toPoint.x;
                if (Mathf.Abs(cross) <= GeometryEpsilon) continue;
                float current = Mathf.Sign(cross);
                if (sign == 0f) sign = current;
                else if (current != sign) return false;
            }
            return true;
        }
    }
}
