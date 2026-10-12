using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace TetheredTracking
{
    public static class SceneVehicleAdjustmentApplier
    {
        public static IReadOnlyList<Transform> FindSceneVehicleRoots()
        {
            return UnityEngine.Object.FindObjectsByType<Transform>(
                    FindObjectsInactive.Exclude,
                    FindObjectsSortMode.None)
                .Where(transform => transform.parent == null)
                .Where(transform => IsVehicleName(transform.name))
                .OrderBy(transform => transform.name, StringComparer.Ordinal)
                .ToArray();
        }

        public static IReadOnlyList<Transform> Apply(
            SceneAdjustmentsScenarioConfig adjustments,
            IEnumerable<Transform> candidateRoots = null,
            PlacementPhaseGuard placementGuard = null)
        {
            if (adjustments == null) return Array.Empty<Transform>();
            placementGuard?.RequirePlacementAllowed("scene_adjustments");
            if (adjustments.vehicle_relocations == null)
                throw new InvalidOperationException(
                    "scene_adjustments.vehicle_relocations is required.");
            Transform[] roots = (candidateRoots ?? FindSceneVehicleRoots())
                .Where(root => root != null)
                .ToArray();
            var selected = new HashSet<Transform>();
            var relocated = new List<Transform>();

            foreach (VehicleRelocationScenarioConfig relocation
                in adjustments.vehicle_relocations)
            {
                if (relocation == null
                    || string.IsNullOrWhiteSpace(relocation.prefab_name)
                    || relocation.original_xz_m == null
                    || (!relocation.remove_from_scene
                        && relocation.new_position_m == null)
                    || !IsPositiveFinite(relocation.match_tolerance_m))
                {
                    throw new InvalidOperationException(
                        "vehicle relocation config is incomplete or invalid.");
                }
                string expectedName = relocation.prefab_name.Trim();
                Vector2 expectedPosition = relocation.original_xz_m.Value;
                Transform[] matches = roots
                    .Where(root => string.Equals(
                        CanonicalPrefabName(root.name),
                        expectedName,
                        StringComparison.Ordinal))
                    .Where(root => Vector2.Distance(
                        new Vector2(root.position.x, root.position.z),
                        expectedPosition) <= relocation.match_tolerance_m)
                    .ToArray();
                if (matches.Length != 1)
                {
                    throw new InvalidOperationException(
                        $"vehicle relocation '{expectedName}' at "
                        + $"({expectedPosition.x:R}, {expectedPosition.y:R}) matched "
                        + $"{matches.Length} scene roots; exactly one is required.");
                }
                Transform match = matches[0];
                if (!selected.Add(match))
                    throw new InvalidOperationException(
                        $"scene vehicle '{match.name}' is selected by multiple relocations.");
                if (relocation.remove_from_scene)
                {
                    if (relocation.mark_as_distractor)
                        throw new InvalidOperationException(
                            $"removed vehicle '{expectedName}' cannot be a distractor.");
                    match.gameObject.SetActive(false);
                }
                else
                {
                    Vector3 destination = relocation.new_position_m.Value;
                    if (!IsFinite(destination))
                        throw new InvalidOperationException(
                            $"vehicle relocation '{expectedName}' destination must be finite.");
                    match.position = destination;
                }
                if (!relocation.remove_from_scene
                    && relocation.mark_as_distractor
                    && match.GetComponent<RateStudyDistractor>() == null)
                {
                    match.gameObject.AddComponent<RateStudyDistractor>();
                }
                relocated.Add(match);
            }

            Physics.SyncTransforms();
            return relocated;
        }

        public static bool IsVehicleName(string name)
        {
            return CanonicalPrefabName(name).StartsWith(
                "Vehicle_",
                StringComparison.Ordinal);
        }

        public static string CanonicalPrefabName(string sceneObjectName)
        {
            if (string.IsNullOrEmpty(sceneObjectName)) return string.Empty;
            if (!sceneObjectName.EndsWith(")", StringComparison.Ordinal))
                return sceneObjectName;
            int marker = sceneObjectName.LastIndexOf(" (", StringComparison.Ordinal);
            if (marker < 0 || marker + 3 >= sceneObjectName.Length)
                return sceneObjectName;
            for (int index = marker + 2; index < sceneObjectName.Length - 1; index++)
            {
                if (!char.IsDigit(sceneObjectName[index])) return sceneObjectName;
            }
            return sceneObjectName.Substring(0, marker);
        }

        static bool IsPositiveFinite(float value)
        {
            return value > 0f && !float.IsNaN(value) && !float.IsInfinity(value);
        }

        static bool IsFinite(Vector3 value)
        {
            return !float.IsNaN(value.x) && !float.IsInfinity(value.x)
                && !float.IsNaN(value.y) && !float.IsInfinity(value.y)
                && !float.IsNaN(value.z) && !float.IsInfinity(value.z);
        }
    }

    [Serializable]
    public sealed class RouteCorridorViolation
    {
        public string prefab_name;
        public string scene_object_name;
        public float center_x_m;
        public float center_z_m;
        public float centerline_distance_m;
        public float vehicle_half_extent_m;
        public float required_centerline_distance_m;
        public float clearance_m;
        public float route_s_m;
    }

    [Serializable]
    public sealed class RouteCorridorAuditReport
    {
        public string schema_version = "p1-scene-route-corridor-audit/v1";
        public string scenario_id;
        public string status;
        public float target_half_width_m;
        public float clearance_margin_m;
        public int audited_vehicle_count;
        public int violation_count;
        public RouteCorridorViolation[] violations;
    }

    public static class RouteCorridorAuditor
    {
        struct NearestRoutePoint
        {
            public float distance;
            public float routeS;
            public Vector2 segmentDirection;
        }

        public static RouteCorridorAuditReport Audit(
            string scenarioId,
            Vector3[] route,
            RouteCorridorScenarioConfig corridor,
            IEnumerable<Transform> vehicleRoots = null)
        {
            if (route == null || route.Length < 2)
                throw new ArgumentException("A route with at least two points is required.");
            if (corridor == null
                || !IsPositiveFinite(corridor.target_half_width_m)
                || !IsNonNegativeFinite(corridor.clearance_margin_m))
            {
                throw new ArgumentException("A valid route corridor config is required.");
            }

            Transform[] roots = (vehicleRoots
                ?? SceneVehicleAdjustmentApplier.FindSceneVehicleRoots())
                .Where(root => root != null)
                .Where(root => root.gameObject.activeInHierarchy)
                .Where(root => SceneVehicleAdjustmentApplier.IsVehicleName(root.name))
                .OrderBy(root => root.name, StringComparer.Ordinal)
                .ToArray();
            var violations = new List<RouteCorridorViolation>();
            int audited = 0;
            foreach (Transform root in roots)
            {
                if (!TryRendererBounds(root, out Bounds bounds)) continue;
                audited++;
                Vector2 center = new Vector2(bounds.center.x, bounds.center.z);
                NearestRoutePoint nearest = NearestPointOnClosedRoute(center, route);
                Vector2 normal = new Vector2(
                    -nearest.segmentDirection.y,
                    nearest.segmentDirection.x);
                float vehicleHalfExtent =
                    Mathf.Abs(normal.x) * bounds.extents.x
                    + Mathf.Abs(normal.y) * bounds.extents.z;
                float required =
                    corridor.target_half_width_m
                    + vehicleHalfExtent
                    + corridor.clearance_margin_m;
                float clearance =
                    nearest.distance
                    - corridor.target_half_width_m
                    - vehicleHalfExtent;
                if (nearest.distance + 1e-5f >= required) continue;
                violations.Add(new RouteCorridorViolation
                {
                    prefab_name =
                        SceneVehicleAdjustmentApplier.CanonicalPrefabName(root.name),
                    scene_object_name = root.name,
                    center_x_m = center.x,
                    center_z_m = center.y,
                    centerline_distance_m = nearest.distance,
                    vehicle_half_extent_m = vehicleHalfExtent,
                    required_centerline_distance_m = required,
                    clearance_m = clearance,
                    route_s_m = nearest.routeS,
                });
            }
            violations.Sort((left, right) => left.route_s_m.CompareTo(right.route_s_m));
            return new RouteCorridorAuditReport
            {
                scenario_id = scenarioId,
                status = violations.Count == 0 ? "CLEAR" : "INVALID_ROUTE_CORRIDOR",
                target_half_width_m = corridor.target_half_width_m,
                clearance_margin_m = corridor.clearance_margin_m,
                audited_vehicle_count = audited,
                violation_count = violations.Count,
                violations = violations.ToArray(),
            };
        }

        public static void WriteReport(
            RouteCorridorAuditReport report,
            string path = null)
        {
            if (report == null) throw new ArgumentNullException(nameof(report));
            AtomicFile.WriteAllText(
                path ?? RuntimePaths.File("route_corridor_audit.json"),
                JsonUtility.ToJson(report, true) + "\n");
        }

        static NearestRoutePoint NearestPointOnClosedRoute(
            Vector2 point,
            Vector3[] route)
        {
            float bestDistance = float.PositiveInfinity;
            float bestRouteS = 0f;
            Vector2 bestDirection = Vector2.right;
            float prefix = 0f;
            for (int index = 0; index < route.Length; index++)
            {
                Vector2 start = new Vector2(route[index].x, route[index].z);
                Vector3 end3 = route[(index + 1) % route.Length];
                Vector2 end = new Vector2(end3.x, end3.z);
                Vector2 delta = end - start;
                float length = delta.magnitude;
                if (length <= 1e-6f) continue;
                Vector2 direction = delta / length;
                float along = Mathf.Clamp(Vector2.Dot(point - start, direction), 0f, length);
                float distance = Vector2.Distance(point, start + direction * along);
                if (distance < bestDistance)
                {
                    bestDistance = distance;
                    bestRouteS = prefix + along;
                    bestDirection = direction;
                }
                prefix += length;
            }
            if (float.IsInfinity(bestDistance))
                throw new ArgumentException("Route contains no non-zero-length segment.");
            return new NearestRoutePoint
            {
                distance = bestDistance,
                routeS = bestRouteS,
                segmentDirection = bestDirection,
            };
        }

        internal static bool TryRendererBounds(Transform root, out Bounds bounds)
        {
            Renderer[] renderers = root.GetComponentsInChildren<Renderer>(false);
            bool found = false;
            bounds = default;
            foreach (Renderer renderer in renderers)
            {
                if (renderer == null || !renderer.enabled) continue;
                if (!found)
                {
                    bounds = renderer.bounds;
                    found = true;
                }
                else bounds.Encapsulate(renderer.bounds);
            }
            return found;
        }

        static bool IsPositiveFinite(float value)
        {
            return value > 0f && !float.IsNaN(value) && !float.IsInfinity(value);
        }

        static bool IsNonNegativeFinite(float value)
        {
            return value >= 0f && !float.IsNaN(value) && !float.IsInfinity(value);
        }
    }

    public sealed class RouteCorridorDynamicMonitor : MonoBehaviour
    {
        readonly struct MonitoredObstacle
        {
            public readonly Transform Root;
            public readonly RoadObstacleFootprint Footprint;

            public MonitoredObstacle(
                Transform root,
                RoadObstacleFootprint footprint)
            {
                Root = root;
                Footprint = footprint;
            }
        }

        [Serializable]
        sealed class DynamicReport
        {
            public string schema_version = "p1-scene-dynamic-intersection/v1";
            public string scenario_id;
            public int checked_frames;
            public int intersection_frames;
            public string[] intersecting_scene_object_names;
        }

        LoopTargetVehicle target;
        MonitoredObstacle[] obstacles = Array.Empty<MonitoredObstacle>();
        string scenarioId;
        string outputPath;
        int checkedFrames;
        int intersectionFrames;
        readonly HashSet<string> intersectingNames =
            new HashSet<string>(StringComparer.Ordinal);

        public void Configure(
            string configuredScenarioId,
            LoopTargetVehicle configuredTarget,
            RoadSceneData roadData,
            IEnumerable<Transform> configuredSceneRoots,
            string configuredOutputPath = null)
        {
            scenarioId = configuredScenarioId;
            target = configuredTarget != null
                ? configuredTarget
                : throw new ArgumentNullException(nameof(configuredTarget));
            if (roadData == null) throw new ArgumentNullException(nameof(roadData));
            roadData.Validate();
            if (configuredSceneRoots == null)
                throw new ArgumentNullException(nameof(configuredSceneRoots));
            outputPath = configuredOutputPath
                ?? RuntimePaths.File("route_corridor_dynamic.json");
            var allowlist = new HashSet<string>(
                roadData.road_surface_allowlist,
                StringComparer.Ordinal);
            var footprints = roadData.obstacle_footprints.ToDictionary(
                item => item.canonical_name,
                StringComparer.Ordinal);
            obstacles = configuredSceneRoots
                .Where(root => root != null)
                .Where(root => root != target.transform)
                .Where(root => root.gameObject.activeInHierarchy)
                .Select(root =>
                {
                    string canonical =
                        SceneVehicleAdjustmentApplier.CanonicalPrefabName(root.name);
                    if (allowlist.Contains(canonical))
                        return new MonitoredObstacle(null, null);
                    if (!footprints.TryGetValue(
                        canonical,
                        out RoadObstacleFootprint footprint))
                    {
                        throw new InvalidOperationException(
                            $"Road data has no classification/footprint for active "
                            + $"renderer root '{root.name}' "
                            + $"(canonical '{canonical}').");
                    }
                    return new MonitoredObstacle(root, footprint);
                })
                .Where(item => item.Root != null)
                .ToArray();
            Write();
        }

        void LateUpdate()
        {
            Sample();
        }

        internal void Sample()
        {
            if (target == null) return;
            checkedFrames++;
            if (!RouteCorridorAuditor.TryRendererBounds(target.transform, out Bounds targetBounds))
            {
                Write();
                return;
            }
            bool intersects = false;
            foreach (MonitoredObstacle obstacle in obstacles)
            {
                Transform root = obstacle.Root;
                if (root == null || !root.gameObject.activeInHierarchy) continue;
                if (!RoadSceneAuditor.TargetBoundsIntersectObstacle(
                    targetBounds,
                    root,
                    obstacle.Footprint))
                {
                    continue;
                }
                intersects = true;
                intersectingNames.Add(root.name);
            }
            if (intersects) intersectionFrames++;
            Write();
        }

        internal int CheckedFrames => checkedFrames;
        internal int IntersectionFrames => intersectionFrames;
        internal int MonitoredObstacleCount => obstacles.Length;
        internal string[] IntersectingNames =>
            intersectingNames.OrderBy(
                value => value,
                StringComparer.Ordinal).ToArray();

        void Write()
        {
            var names = IntersectingNames;
            AtomicFile.WriteAllText(
                outputPath,
                JsonUtility.ToJson(new DynamicReport
                {
                    scenario_id = scenarioId,
                    checked_frames = checkedFrames,
                    intersection_frames = intersectionFrames,
                    intersecting_scene_object_names = names,
                }, true) + "\n");
        }
    }
}
