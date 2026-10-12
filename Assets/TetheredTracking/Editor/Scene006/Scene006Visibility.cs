using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// The §5.3 authoritative fidelity gate: an offline visibility predicate
    /// point-for-point equivalent to CoverageEvaluator.EvaluateVisibility
    /// (Scripts/CoverageEvaluator.cs, method `EvaluateVisibility`).
    ///
    /// Per target state the predicate takes the union AABB of the target
    /// child renderers, builds the same 15 samples (8 corners + center + 6
    /// face centres), tests each sample against the camera viewport
    /// rectangle (z &gt; 0, x/y in [0, 1]) and, when rays are enabled, the
    /// same RaycastAll(origin, dir, distance - 0.05, ~0,
    /// QueryTriggerInteraction.Ignore) line-of-sight check that skips only
    /// the target root itself. The denominator is always 15; the boolean is
    /// visibleFraction &gt;= 0.2. With rays disabled the same construction
    /// yields the per-sample C_frustum boolean (§5.2.8).
    ///
    /// The runtime originals are private/internal to TetheredTracking.Runtime
    /// and unreachable from this assembly, so the semantics are replicated
    /// here; EditMode tests verify equivalence against the internal
    /// originals (which the test assembly can see via InternalsVisibleTo).
    /// </summary>
    public static class Scene006Visibility
    {
        public const int SampleCount = 15;
        public const float VisibleFractionThreshold = 0.2f;
        public const float RaycastTrimM = 0.05f;

        public readonly struct Snapshot
        {
            public readonly int FrustumSampleCount;
            public readonly int VisibleSampleCount;
            public readonly float FrustumFraction;
            public readonly float VisibleFraction;
            public readonly bool FrustumVisible;
            public readonly bool GeometricallyVisible;

            public Snapshot(int frustumSampleCount, int visibleSampleCount)
            {
                FrustumSampleCount = frustumSampleCount;
                VisibleSampleCount = visibleSampleCount;
                FrustumFraction = frustumSampleCount / (float)SampleCount;
                VisibleFraction = visibleSampleCount / (float)SampleCount;
                FrustumVisible = FrustumFraction >= VisibleFractionThreshold;
                GeometricallyVisible = VisibleFraction >= VisibleFractionThreshold;
            }
        }

        public static Vector3[] BoundsCorners(Bounds bounds)
        {
            Vector3 min = bounds.min;
            Vector3 max = bounds.max;
            return new[]
            {
                new Vector3(min.x, min.y, min.z), new Vector3(min.x, min.y, max.z),
                new Vector3(min.x, max.y, min.z), new Vector3(min.x, max.y, max.z),
                new Vector3(max.x, min.y, min.z), new Vector3(max.x, min.y, max.z),
                new Vector3(max.x, max.y, min.z), new Vector3(max.x, max.y, max.z),
            };
        }

        public static Vector3[] VisibilitySamples(Bounds bounds, Vector3[] corners)
        {
            Vector3 center = bounds.center;
            Vector3 extents = bounds.extents;
            var samples = new Vector3[SampleCount];
            Array.Copy(corners, samples, corners.Length);
            samples[8] = center;
            samples[9] = center + Vector3.up * extents.y;
            samples[10] = center - Vector3.up * extents.y;
            samples[11] = center + Vector3.right * extents.x;
            samples[12] = center - Vector3.right * extents.x;
            samples[13] = center + Vector3.forward * extents.z;
            samples[14] = center - Vector3.forward * extents.z;
            return samples;
        }

        public static Snapshot Evaluate(
            Camera camera,
            Bounds bounds,
            Vector3[] corners,
            Func<Vector3, Vector3, bool> lineOfSight)
        {
            Vector3[] samples = VisibilitySamples(bounds, corners);
            int inFrustumCount = 0;
            int visibleCount = 0;
            Vector3 origin = camera.transform.position;
            foreach (Vector3 point in samples)
            {
                Vector3 viewport = camera.WorldToViewportPoint(point);
                bool inFrustum = viewport.z > 0f
                    && viewport.x >= 0f && viewport.x <= 1f
                    && viewport.y >= 0f && viewport.y <= 1f;
                if (!inFrustum) continue;
                inFrustumCount++;
                if (lineOfSight == null || lineOfSight(origin, point))
                    visibleCount++;
            }
            return new Snapshot(inFrustumCount, visibleCount);
        }

        /// <summary>
        /// The evaluator line-of-sight check (CoverageEvaluator.cs, method
        /// `HasClearLineOfSight`):
        /// RaycastAll over every layer, triggers ignored, ray shortened by
        /// 0.05 m; any hit outside the target subtree occludes.
        /// </summary>
        public static bool HasClearLineOfSight(
            Vector3 origin,
            Vector3 point,
            Transform target)
        {
            return OccludingRoots(origin, point, target).Length == 0;
        }

        /// <summary>
        /// Same raycast as <see cref="HasClearLineOfSight"/> but returns the
        /// sorted distinct scene-root names of every occluding hit (empty
        /// when the line of sight is clear). Batch-1b P2 cells record this
        /// per-tick occlusion attribution (amendment §5.3).
        /// </summary>
        public static string[] OccludingRoots(
            Vector3 origin,
            Vector3 point,
            Transform target)
        {
            Vector3 delta = point - origin;
            float distance = delta.magnitude;
            if (distance <= RaycastTrimM) return Array.Empty<string>();
            RaycastHit[] hits = Physics.RaycastAll(
                origin,
                delta / distance,
                distance - RaycastTrimM,
                ~0,
                QueryTriggerInteraction.Ignore);
            var blockers = new HashSet<string>(StringComparer.Ordinal);
            foreach (RaycastHit hit in hits)
            {
                if (hit.transform == target || hit.transform.IsChildOf(target))
                    continue;
                Transform root = hit.transform;
                while (root.parent != null) root = root.parent;
                blockers.Add(root.name);
            }
            var result = new string[blockers.Count];
            blockers.CopyTo(result);
            Array.Sort(result, StringComparer.Ordinal);
            return result;
        }

        /// <summary>
        /// Replicates CoverageEvaluator.ProjectBounds
        /// (Scripts/CoverageEvaluator.cs, method `ProjectBounds`): project the
        /// bounds corners,
        /// drop corners at/behind the near plane (z &lt;= 0), clamp to the
        /// frame, and return a top-left-origin normalized xywh box; null when
        /// no corner is in front or the clipped box is degenerate.
        /// </summary>
        public static NormalizedBoundingBox ProjectBounds(
            Camera camera,
            Vector3[] corners)
        {
            float minX = float.PositiveInfinity;
            float minY = float.PositiveInfinity;
            float maxX = float.NegativeInfinity;
            float maxY = float.NegativeInfinity;
            bool hasFrontPoint = false;
            foreach (Vector3 corner in corners)
            {
                Vector3 viewport = camera.WorldToViewportPoint(corner);
                if (viewport.z <= 0f) continue;
                hasFrontPoint = true;
                minX = Mathf.Min(minX, viewport.x);
                minY = Mathf.Min(minY, viewport.y);
                maxX = Mathf.Max(maxX, viewport.x);
                maxY = Mathf.Max(maxY, viewport.y);
            }
            if (!hasFrontPoint) return null;

            float clippedMinX = Mathf.Clamp01(minX);
            float clippedMaxX = Mathf.Clamp01(maxX);
            float clippedMinY = Mathf.Clamp01(minY);
            float clippedMaxY = Mathf.Clamp01(maxY);
            if (clippedMaxX <= clippedMinX || clippedMaxY <= clippedMinY)
                return null;
            return new NormalizedBoundingBox
            {
                x = clippedMinX,
                y = 1f - clippedMaxY,
                width = clippedMaxX - clippedMinX,
                height = clippedMaxY - clippedMinY,
            };
        }

        /// <summary>
        /// Union of child-renderer world AABBs, then projection — the
        /// evaluator's ProjectRenderers construction
        /// (Scripts/CoverageEvaluator.cs, method `ProjectRenderers`).
        /// </summary>
        public static NormalizedBoundingBox ProjectRenderers(
            Camera camera,
            Renderer[] renderers)
        {
            if (camera == null || renderers == null || renderers.Length == 0)
                return null;
            Bounds bounds = renderers[0].bounds;
            for (int index = 1; index < renderers.Length; index++)
                bounds.Encapsulate(renderers[index].bounds);
            return ProjectBounds(camera, BoundsCorners(bounds));
        }

        public static float MinSidePx(
            NormalizedBoundingBox box,
            int imageWidth,
            int imageHeight)
        {
            return Mathf.Min(
                box.width * imageWidth,
                box.height * imageHeight);
        }

        /// <summary>
        /// Type-7 quantile (numpy "linear" method), bit-compatible with
        /// controller/rate3_decision.py:quantile_type7 including the
        /// gamma &gt;= 0.5 upper-anchor lerp branch. Frozen for the T1 p05
        /// and the T6 domain median (§5.1, §5.2.8).
        /// </summary>
        public static double QuantileType7(
            IReadOnlyList<float> values,
            double probability)
        {
            if (values == null || values.Count == 0)
                throw new InvalidOperationException(
                    "quantile of an empty sample is undefined");
            if (probability < 0.0 || probability > 1.0)
                throw new ArgumentOutOfRangeException(nameof(probability));
            var ordered = new List<double>(values.Count);
            foreach (float value in values)
            {
                if (!Scene006RouteGeometry.Finite(value))
                    throw new InvalidOperationException(
                        "quantile input must be finite");
                ordered.Add(value);
            }
            ordered.Sort();
            if (ordered.Count == 1) return ordered[0];
            double virtualIndex = probability * (ordered.Count - 1);
            int previousIndex = (int)Math.Floor(virtualIndex);
            int nextIndex = Math.Min(previousIndex + 1, ordered.Count - 1);
            double gamma = virtualIndex - previousIndex;
            double lower = ordered[previousIndex];
            double upper = ordered[nextIndex];
            double difference = upper - lower;
            if (gamma >= 0.5) return upper - difference * (1.0 - gamma);
            return lower + difference * gamma;
        }
    }
}
