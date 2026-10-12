using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking
{
    internal static class RateStudyScouting
    {
        internal readonly struct RouteSample
        {
            public readonly Vector3 Position;
            public readonly int NextWaypointIndex;

            public RouteSample(Vector3 position, int nextWaypointIndex)
            {
                Position = position;
                NextWaypointIndex = nextWaypointIndex;
            }
        }

        internal readonly struct Separation
        {
            public readonly float NearestCenterDistancePixels;
            public readonly float NearestIoU;
            public readonly bool HasDistractor;

            public Separation(float nearestCenterDistancePixels, float nearestIoU, bool hasDistractor)
            {
                NearestCenterDistancePixels = nearestCenterDistancePixels;
                NearestIoU = nearestIoU;
                HasDistractor = hasDistractor;
            }
        }

        internal static float ClosedRoutePerimeter(IReadOnlyList<Vector3> route)
        {
            ValidateRoute(route);
            float perimeter = 0f;
            for (int index = 0; index < route.Count; index++)
                perimeter += Vector3.Distance(route[index], route[(index + 1) % route.Count]);
            if (!RateStudyProtocol.Finite(perimeter) || perimeter <= Mathf.Epsilon)
                throw new ArgumentException("Closed route perimeter must be positive.", nameof(route));
            return perimeter;
        }

        internal static float[] CandidateDistances(
            IReadOnlyList<Vector3> route,
            float spacingMeters = 0.5f)
        {
            if (!RateStudyProtocol.Finite(spacingMeters) || spacingMeters <= 0f)
                throw new ArgumentOutOfRangeException(nameof(spacingMeters));
            float perimeter = ClosedRoutePerimeter(route);
            int count = Mathf.CeilToInt(perimeter / spacingMeters);
            var distances = new List<float>(count);
            for (int index = 0; index < count; index++)
            {
                float distance = index * spacingMeters;
                if (distance < perimeter) distances.Add(distance);
            }
            return distances.ToArray();
        }

        internal static RouteSample SampleClosedRoute(
            IReadOnlyList<Vector3> route,
            float distanceMeters)
        {
            ValidateRoute(route);
            if (!RateStudyProtocol.Finite(distanceMeters) || distanceMeters < 0f)
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
            throw new InvalidOperationException("Closed route contains no positive segment.");
        }

        internal static Separation NearestDistractor(
            NormalizedBoundingBox target,
            IReadOnlyList<NormalizedBoundingBox> distractors,
            int width,
            int height)
        {
            if (target == null || distractors == null || distractors.Count == 0)
                return new Separation(-1f, 0f, false);
            float nearestDistance = float.PositiveInfinity;
            float nearestIou = 0f;
            foreach (NormalizedBoundingBox distractor in distractors)
            {
                if (distractor == null) continue;
                float dx = ((distractor.x + distractor.width * 0.5f)
                    - (target.x + target.width * 0.5f)) * width;
                float dy = ((distractor.y + distractor.height * 0.5f)
                    - (target.y + target.height * 0.5f)) * height;
                float distance = Mathf.Sqrt(dx * dx + dy * dy);
                float iou = CoverageEvaluator.IntersectionOverUnion(target, distractor);
                if (distance < nearestDistance - 1e-5f)
                {
                    nearestDistance = distance;
                    nearestIou = iou;
                }
                else if (Mathf.Abs(distance - nearestDistance) <= 1e-5f)
                {
                    nearestIou = Mathf.Max(nearestIou, iou);
                }
            }
            return float.IsPositiveInfinity(nearestDistance)
                ? new Separation(-1f, 0f, false)
                : new Separation(nearestDistance, nearestIou, true);
        }

        internal static float FrameMargin(NormalizedBoundingBox box)
        {
            if (box == null) return float.NegativeInfinity;
            return Mathf.Min(
                Mathf.Min(box.x, box.y),
                Mathf.Min(1f - box.x - box.width, 1f - box.y - box.height));
        }

        internal static bool Qualifies(
            NormalizedBoundingBox target,
            Separation separation,
            int imageWidth,
            float requiredMargin = 0.15f)
        {
            if (target == null || FrameMargin(target) < requiredMargin) return false;
            if (!separation.HasDistractor) return true;
            return separation.NearestIoU <= 0f
                && separation.NearestCenterDistancePixels + 1e-4f
                    >= target.width * imageWidth;
        }

        internal static NormalizedBoundingBox ProjectRenderersUnclipped(
            Camera camera,
            IReadOnlyList<Renderer> renderers)
        {
            if (camera == null || renderers == null || renderers.Count == 0) return null;
            float minX = float.PositiveInfinity;
            float minY = float.PositiveInfinity;
            float maxX = float.NegativeInfinity;
            float maxY = float.NegativeInfinity;
            bool hasFrontPoint = false;
            foreach (Renderer renderer in renderers)
            {
                if (renderer == null || !renderer.gameObject.activeInHierarchy) continue;
                foreach (Vector3 corner in CoverageEvaluator.BoundsCorners(renderer.bounds))
                {
                    Vector3 viewport = camera.WorldToViewportPoint(corner);
                    if (viewport.z <= 0f) continue;
                    hasFrontPoint = true;
                    minX = Mathf.Min(minX, viewport.x);
                    minY = Mathf.Min(minY, viewport.y);
                    maxX = Mathf.Max(maxX, viewport.x);
                    maxY = Mathf.Max(maxY, viewport.y);
                }
            }
            if (!hasFrontPoint || maxX <= minX || maxY <= minY) return null;
            return new NormalizedBoundingBox
            {
                x = minX,
                y = 1f - maxY,
                width = maxX - minX,
                height = maxY - minY,
            };
        }

        static void ValidateRoute(IReadOnlyList<Vector3> route)
        {
            if (route == null || route.Count < 2)
                throw new ArgumentException("Route requires at least two points.", nameof(route));
            foreach (Vector3 point in route)
            {
                if (!RateStudyProtocol.Finite(point.x)
                    || !RateStudyProtocol.Finite(point.y)
                    || !RateStudyProtocol.Finite(point.z))
                    throw new ArgumentException("Route points must be finite.", nameof(route));
            }
        }
    }
}
