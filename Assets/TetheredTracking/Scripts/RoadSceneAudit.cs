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
    public sealed class RoadSurfacePatch
    {
        public string id;
        public string canonical_name;
        public float center_x_m;
        public float center_z_m;
        public float yaw_deg;
        public float half_extent_x_m;
        public float half_extent_z_m;
        public float surface_y_m;
    }

    [Serializable]
    public sealed class RoadObstacleFootprint
    {
        public string canonical_name;
        public string classification;
        public string group;
        public float full_min_x_m;
        public float full_max_x_m;
        public float full_min_y_m;
        public float full_max_y_m;
        public float full_min_z_m;
        public float full_max_z_m;
        public float ground_min_x_m;
        public float ground_max_x_m;
        public float ground_min_z_m;
        public float ground_max_z_m;
        public float overhead_min_y_m;
    }

    [Serializable]
    public sealed class RoadSceneData
    {
        public const string Schema = "p1-scene-road-data/v1";
        public string schema_version;
        public float road_surface_tolerance_m;
        public string[] road_surface_allowlist;
        public RoadSurfacePatch[] surfaces;
        public RoadObstacleFootprint[] obstacle_footprints;

        public void Validate()
        {
            if (schema_version != Schema)
                throw new InvalidOperationException(
                    $"Unsupported road-data schema '{schema_version}'.");
            RequireNonNegativeFinite(
                road_surface_tolerance_m,
                "road_surface_tolerance_m");
            if (road_surface_allowlist == null || road_surface_allowlist.Length == 0)
                throw new InvalidOperationException(
                    "road_surface_allowlist must not be empty.");
            if (surfaces == null || surfaces.Length == 0)
                throw new InvalidOperationException("surfaces must not be empty.");
            if (obstacle_footprints == null || obstacle_footprints.Length == 0)
                throw new InvalidOperationException(
                    "obstacle_footprints must not be empty.");

            var roadNames = new HashSet<string>(StringComparer.Ordinal);
            foreach (string name in road_surface_allowlist)
            {
                if (string.IsNullOrWhiteSpace(name) || !roadNames.Add(name))
                    throw new InvalidOperationException(
                        "road_surface_allowlist contains a blank or duplicate entry.");
            }

            var surfaceIds = new HashSet<string>(StringComparer.Ordinal);
            foreach (RoadSurfacePatch surface in surfaces)
            {
                if (surface == null
                    || string.IsNullOrWhiteSpace(surface.id)
                    || !surfaceIds.Add(surface.id))
                {
                    throw new InvalidOperationException(
                        "surfaces contains a null, blank, or duplicate id.");
                }
                if (!roadNames.Contains(surface.canonical_name))
                    throw new InvalidOperationException(
                        $"surface '{surface.id}' has an unknown road classification.");
                RequireFinite(surface.center_x_m, surface.id + ".center_x_m");
                RequireFinite(surface.center_z_m, surface.id + ".center_z_m");
                RequireFinite(surface.yaw_deg, surface.id + ".yaw_deg");
                RequirePositiveFinite(
                    surface.half_extent_x_m,
                    surface.id + ".half_extent_x_m");
                RequirePositiveFinite(
                    surface.half_extent_z_m,
                    surface.id + ".half_extent_z_m");
                RequireFinite(surface.surface_y_m, surface.id + ".surface_y_m");
            }

            var footprintNames = new HashSet<string>(StringComparer.Ordinal);
            foreach (RoadObstacleFootprint footprint in obstacle_footprints)
            {
                if (footprint == null
                    || string.IsNullOrWhiteSpace(footprint.canonical_name)
                    || !footprintNames.Add(footprint.canonical_name))
                {
                    throw new InvalidOperationException(
                        "obstacle_footprints contains a null, blank, or duplicate entry.");
                }
                if (footprint.classification != "ground-obstacle"
                    && footprint.classification != "overhead")
                    throw new InvalidOperationException(
                        $"Unknown classification '{footprint.classification}' for "
                        + $"'{footprint.canonical_name}'.");
                if (footprint.group != "vehicle"
                    && footprint.group != "prop"
                    && footprint.group != "nature"
                    && footprint.group != "building"
                    && footprint.group != "other")
                {
                    throw new InvalidOperationException(
                        $"Unknown obstacle group '{footprint.group}' for "
                        + $"'{footprint.canonical_name}'.");
                }
                ValidateBounds(footprint);
                if (roadNames.Contains(footprint.canonical_name))
                    throw new InvalidOperationException(
                        $"'{footprint.canonical_name}' has duplicate road/obstacle classes.");
            }
        }

        static void ValidateBounds(RoadObstacleFootprint footprint)
        {
            RequireFinite(footprint.full_min_x_m, "full_min_x_m");
            RequireFinite(footprint.full_max_x_m, "full_max_x_m");
            RequireFinite(footprint.full_min_y_m, "full_min_y_m");
            RequireFinite(footprint.full_max_y_m, "full_max_y_m");
            RequireFinite(footprint.full_min_z_m, "full_min_z_m");
            RequireFinite(footprint.full_max_z_m, "full_max_z_m");
            RequireFinite(footprint.ground_min_x_m, "ground_min_x_m");
            RequireFinite(footprint.ground_max_x_m, "ground_max_x_m");
            RequireFinite(footprint.ground_min_z_m, "ground_min_z_m");
            RequireFinite(footprint.ground_max_z_m, "ground_max_z_m");
            RequireFinite(footprint.overhead_min_y_m, "overhead_min_y_m");
            if (footprint.full_min_x_m > footprint.full_max_x_m
                || footprint.full_min_y_m > footprint.full_max_y_m
                || footprint.full_min_z_m > footprint.full_max_z_m
                || footprint.ground_min_x_m > footprint.ground_max_x_m
                || footprint.ground_min_z_m > footprint.ground_max_z_m)
            {
                throw new InvalidOperationException(
                    $"Invalid footprint bounds for '{footprint.canonical_name}'.");
            }
        }

        static void RequireFinite(float value, string label)
        {
            if (float.IsNaN(value) || float.IsInfinity(value))
                throw new InvalidOperationException(label + " must be finite.");
        }

        static void RequirePositiveFinite(float value, string label)
        {
            RequireFinite(value, label);
            if (value <= 0f)
                throw new InvalidOperationException(label + " must be positive.");
        }

        static void RequireNonNegativeFinite(float value, string label)
        {
            RequireFinite(value, label);
            if (value < 0f)
                throw new InvalidOperationException(label + " must be non-negative.");
        }
    }

    public static class RoadSceneDataLoader
    {
        public const string FileName = "road_data.json";

        public static string ProjectPath =>
            RuntimePaths.ProjectFile("config", FileName);

        public static RoadSceneData LoadVerified(
            string expectedSha256,
            string path = null)
        {
            if (!RateStudyProtocol.IsSha256(expectedSha256))
                throw new InvalidOperationException(
                    "road_data_sha256 must be a lowercase SHA-256 digest.");
            string resolvedPath = path ?? ProjectPath;
            if (!File.Exists(resolvedPath))
                throw new FileNotFoundException(
                    "Required road-data file is missing.",
                    resolvedPath);
            byte[] bytes = File.ReadAllBytes(resolvedPath);
            string actual = Sha256(bytes);
            if (!string.Equals(actual, expectedSha256, StringComparison.Ordinal))
                throw new InvalidOperationException(
                    $"Road-data SHA-256 mismatch: expected {expectedSha256}, got {actual}.");
            RoadSceneData data;
            try
            {
                data = JsonUtility.FromJson<RoadSceneData>(
                    Encoding.UTF8.GetString(bytes));
            }
            catch (Exception exception)
            {
                throw new InvalidOperationException(
                    "Road-data JSON is invalid.",
                    exception);
            }
            if (data == null)
                throw new InvalidOperationException(
                    "Road-data JSON produced no document.");
            data.Validate();
            return data;
        }

        public static string Sha256(byte[] bytes)
        {
            using SHA256 sha = SHA256.Create();
            byte[] digest = sha.ComputeHash(bytes);
            var builder = new StringBuilder(digest.Length * 2);
            foreach (byte value in digest) builder.Append(value.ToString("x2"));
            return builder.ToString();
        }
    }

    [Serializable]
    public sealed class RoadLegalityViolation
    {
        public int sample_index;
        public float route_s_m;
        public float x_m;
        public float z_m;
        public string reason;
    }

    [Serializable]
    public sealed class SceneObstacleViolation
    {
        public string canonical_name;
        public string scene_object_name;
        public string group;
        public float center_x_m;
        public float center_z_m;
        public float route_s_m;
        public float centerline_distance_m;
        public float required_centerline_distance_m;
        public float obstacle_min_y_m;
        public float obstacle_max_y_m;
        public float envelope_min_y_m;
        public float envelope_max_y_m;
    }

    [Serializable]
    public sealed class RoadSceneAuditReport
    {
        public string schema_version = "p1-scene-road-audit/v1";
        public string scenario_id;
        public string status;
        public int route_sample_count;
        public int road_violation_count;
        public RoadLegalityViolation[] road_violations;
        public int audited_obstacle_count;
        public int overhead_exemption_count;
        public int obstacle_violation_count;
        public int vehicle_violation_count;
        public int prop_violation_count;
        public int nature_violation_count;
        public int building_violation_count;
        public int other_violation_count;
        public SceneObstacleViolation[] obstacle_violations;
    }

    public static class RoadSceneAuditor
    {
        const float GeometryEpsilon = 1e-5f;

        struct RoutePoint
        {
            public float distance;
            public float routeS;
            public Vector2 direction;
            public Vector3 world;
        }

        public static IReadOnlyList<Transform> FindStaticRenderableRoots(
            IEnumerable<Transform> excludedRoots = null)
        {
            var excluded = new HashSet<Transform>(
                (excludedRoots ?? Array.Empty<Transform>())
                    .Where(root => root != null));
            return UnityEngine.Object.FindObjectsByType<Transform>(
                    FindObjectsInactive.Exclude,
                    FindObjectsSortMode.None)
                .Where(transform => transform.parent == null)
                .Where(transform => !excluded.Contains(transform))
                .Where(transform =>
                    transform.GetComponentsInChildren<MeshRenderer>(false).Length > 0)
                .OrderBy(transform => transform.name, StringComparer.Ordinal)
                .ToArray();
        }

        public static RoadSceneAuditReport Audit(
            string scenarioId,
            Vector3[] route,
            RouteCorridorScenarioConfig corridor,
            RoadSceneData roadData,
            IEnumerable<Transform> sceneRoots)
        {
            ValidateInputs(route, corridor, roadData);
            Transform[] roots = (sceneRoots ?? throw new ArgumentNullException(
                    nameof(sceneRoots)))
                .Where(root => root != null)
                .Where(root => root.gameObject.activeInHierarchy)
                .OrderBy(root => root.name, StringComparer.Ordinal)
                .ToArray();
            var roadViolations = AuditRoadRoute(route, corridor, roadData);
            var obstacleViolations = new List<SceneObstacleViolation>();
            int audited = 0;
            int overheadExemptions = 0;
            var allowlist = new HashSet<string>(
                roadData.road_surface_allowlist,
                StringComparer.Ordinal);
            var footprints = roadData.obstacle_footprints.ToDictionary(
                item => item.canonical_name,
                StringComparer.Ordinal);

            foreach (Transform root in roots)
            {
                string canonical =
                    SceneVehicleAdjustmentApplier.CanonicalPrefabName(root.name);
                if (allowlist.Contains(canonical)) continue;
                if (!footprints.TryGetValue(canonical, out RoadObstacleFootprint footprint))
                    throw new InvalidOperationException(
                        $"Road data has no classification/footprint for active "
                        + $"renderer root '{root.name}' (canonical '{canonical}').");
                audited++;
                if (AuditObstacle(
                    route,
                    corridor,
                    roadData,
                    root,
                    footprint,
                    out SceneObstacleViolation violation,
                    out bool overheadExempt))
                {
                    obstacleViolations.Add(violation);
                }
                if (overheadExempt) overheadExemptions++;
            }

            obstacleViolations.Sort(
                (left, right) => left.route_s_m.CompareTo(right.route_s_m));
            return new RoadSceneAuditReport
            {
                scenario_id = scenarioId,
                status = roadViolations.Count == 0 && obstacleViolations.Count == 0
                    ? "CLEAR"
                    : "INVALID_SCENE_LEGALITY",
                route_sample_count = RouteSampleCount(route, corridor.road_sample_spacing_m),
                road_violation_count = roadViolations.Count,
                road_violations = roadViolations.ToArray(),
                audited_obstacle_count = audited,
                overhead_exemption_count = overheadExemptions,
                obstacle_violation_count = obstacleViolations.Count,
                vehicle_violation_count =
                    obstacleViolations.Count(item => item.group == "vehicle"),
                prop_violation_count =
                    obstacleViolations.Count(item => item.group == "prop"),
                nature_violation_count =
                    obstacleViolations.Count(item => item.group == "nature"),
                building_violation_count =
                    obstacleViolations.Count(item => item.group == "building"),
                other_violation_count =
                    obstacleViolations.Count(item => item.group == "other"),
                obstacle_violations = obstacleViolations.ToArray(),
            };
        }

        public static void WriteReport(
            RoadSceneAuditReport report,
            string path = null)
        {
            if (report == null) throw new ArgumentNullException(nameof(report));
            AtomicFile.WriteAllText(
                path ?? RuntimePaths.File("road_scene_audit.json"),
                JsonUtility.ToJson(report, true) + "\n");
        }

        internal static bool AuditObstacle(
            Vector3[] route,
            RouteCorridorScenarioConfig corridor,
            RoadSceneData roadData,
            Transform root,
            RoadObstacleFootprint footprint,
            out SceneObstacleViolation violation,
            out bool overheadExempt)
        {
            RequireSupportedFootprintTransform(root);
            Footprint2 ground = TransformFootprint(
                root,
                footprint.ground_min_x_m,
                footprint.ground_max_x_m,
                footprint.ground_min_z_m,
                footprint.ground_max_z_m);
            Footprint2 full = TransformFootprint(
                root,
                footprint.full_min_x_m,
                footprint.full_max_x_m,
                footprint.full_min_z_m,
                footprint.full_max_z_m);
            RoutePoint groundCenterNearest =
                NearestPointOnClosedRoute(ground.Center, route);
            RoutePoint fullCenterNearest =
                NearestPointOnClosedRoute(full.Center, route);
            RoutePoint groundBoundaryNearest =
                NearestFootprintPointOnClosedRoute(ground, route);
            RoutePoint fullBoundaryNearest =
                NearestFootprintPointOnClosedRoute(full, route);
            float groundHalf =
                ground.SupportHalfExtent(groundCenterNearest.direction);
            float fullHalf =
                full.SupportHalfExtent(fullCenterNearest.direction);
            float requiredGround =
                corridor.target_half_width_m
                + corridor.clearance_margin_m
                + groundHalf;
            float requiredFull =
                corridor.target_half_width_m
                + corridor.clearance_margin_m
                + fullHalf;
            float sweptHalfWidth =
                corridor.target_half_width_m + corridor.clearance_margin_m;
            bool groundIntersects =
                groundBoundaryNearest.distance + GeometryEpsilon < sweptHalfWidth;
            bool fullIntersects =
                fullBoundaryNearest.distance + GeometryEpsilon < sweptHalfWidth;

            float surfaceY = SurfaceHeightAt(
                new Vector2(
                    fullBoundaryNearest.world.x,
                    fullBoundaryNearest.world.z),
                roadData,
                true);
            float envelopeMin = surfaceY;
            float envelopeMax =
                surfaceY
                + corridor.target_height_m
                + corridor.vertical_clearance_margin_m;
            Vector2 verticalBounds = TransformVerticalBounds(root, footprint);
            float obstacleMin = verticalBounds.x;
            float obstacleMax = verticalBounds.y;
            bool verticalIntersects =
                obstacleMin <= envelopeMax + GeometryEpsilon
                && obstacleMax >= envelopeMin - GeometryEpsilon;
            float overheadWorldY = TransformHorizontalPlaneMinimumY(
                root,
                footprint.full_min_x_m,
                footprint.full_max_x_m,
                footprint.overhead_min_y_m,
                footprint.full_min_z_m,
                footprint.full_max_z_m);
            if (footprint.classification == "overhead")
            {
                overheadExempt =
                    fullIntersects
                    && obstacleMin > envelopeMax + GeometryEpsilon;
                if (overheadExempt || !fullIntersects || !verticalIntersects)
                {
                    violation = null;
                    return false;
                }
            }
            overheadExempt =
                fullIntersects
                && !groundIntersects
                && overheadWorldY > envelopeMax + GeometryEpsilon;
            if (!verticalIntersects
                || overheadExempt
                || (!groundIntersects && !fullIntersects))
            {
                violation = null;
                return false;
            }

            RoutePoint nearest =
                groundIntersects ? groundCenterNearest : fullCenterNearest;
            float required = groundIntersects ? requiredGround : requiredFull;
            violation = new SceneObstacleViolation
            {
                canonical_name = footprint.canonical_name,
                scene_object_name = root.name,
                group = footprint.group,
                center_x_m = root.position.x,
                center_z_m = root.position.z,
                route_s_m = nearest.routeS,
                centerline_distance_m = nearest.distance,
                required_centerline_distance_m = required,
                obstacle_min_y_m = obstacleMin,
                obstacle_max_y_m = obstacleMax,
                envelope_min_y_m = envelopeMin,
                envelope_max_y_m = envelopeMax,
            };
            return true;
        }

        internal static bool TargetBoundsIntersectObstacle(
            Bounds targetBounds,
            Transform root,
            RoadObstacleFootprint footprint)
        {
            if (root == null) throw new ArgumentNullException(nameof(root));
            if (footprint == null)
                throw new ArgumentNullException(nameof(footprint));
            RequireSupportedFootprintTransform(root);

            Footprint2 target = AxisAlignedFootprint(
                targetBounds.min.x,
                targetBounds.max.x,
                targetBounds.min.z,
                targetBounds.max.z);
            Footprint2 ground = TransformFootprint(
                root,
                footprint.ground_min_x_m,
                footprint.ground_max_x_m,
                footprint.ground_min_z_m,
                footprint.ground_max_z_m);
            Footprint2 full = TransformFootprint(
                root,
                footprint.full_min_x_m,
                footprint.full_max_x_m,
                footprint.full_min_z_m,
                footprint.full_max_z_m);
            bool groundIntersects = ConvexPolygonsIntersect(
                target.Corners,
                ground.Corners);
            bool fullIntersects = ConvexPolygonsIntersect(
                target.Corners,
                full.Corners);
            if (!groundIntersects && !fullIntersects) return false;

            Vector2 verticalBounds = TransformVerticalBounds(root, footprint);
            bool verticalIntersects =
                verticalBounds.x <= targetBounds.max.y + GeometryEpsilon
                && verticalBounds.y >= targetBounds.min.y - GeometryEpsilon;
            if (!verticalIntersects) return false;
            if (groundIntersects || footprint.classification == "overhead")
                return true;

            float overheadWorldY = TransformHorizontalPlaneMinimumY(
                root,
                footprint.full_min_x_m,
                footprint.full_max_x_m,
                footprint.overhead_min_y_m,
                footprint.full_min_z_m,
                footprint.full_max_z_m);
            return overheadWorldY <= targetBounds.max.y + GeometryEpsilon;
        }

        static void RequireSupportedFootprintTransform(Transform root)
        {
            if (root == null) throw new ArgumentNullException(nameof(root));
            Vector3 scale = root.lossyScale;
            bool finiteNonZeroScale =
                IsFiniteNonZero(scale.x)
                && IsFiniteNonZero(scale.y)
                && IsFiniteNonZero(scale.z);
            if (!finiteNonZeroScale)
                throw new InvalidOperationException(
                    $"Obstacle root '{root.name}' has an unsupported zero/non-finite TRS scale.");
            if (Vector3.Angle(root.up, Vector3.up) > 0.01f)
                throw new InvalidOperationException(
                    $"Obstacle root '{root.name}' has pitch/roll; the version-1 "
                    + "XZ ground-footprint schema supports yaw plus exact "
                    + "uniform or non-uniform scale only.");
        }

        static bool IsFiniteNonZero(float value)
        {
            return value != 0f && !float.IsNaN(value) && !float.IsInfinity(value);
        }

        static List<RoadLegalityViolation> AuditRoadRoute(
            Vector3[] route,
            RouteCorridorScenarioConfig corridor,
            RoadSceneData roadData)
        {
            float perimeter = ClosedRoutePerimeter(route);
            int count = RouteSampleCount(route, corridor.road_sample_spacing_m);
            var violations = new List<RoadLegalityViolation>();
            for (int index = 0; index < count; index++)
            {
                float routeS = Mathf.Min(
                    index * corridor.road_sample_spacing_m,
                    perimeter);
                RoutePoint sample = SampleClosedRoute(route, routeS);
                if (!TrySurfaceAt(
                    new Vector2(sample.world.x, sample.world.z),
                    roadData,
                    out float surfaceY))
                {
                    violations.Add(new RoadLegalityViolation
                    {
                        sample_index = index,
                        route_s_m = routeS,
                        x_m = sample.world.x,
                        z_m = sample.world.z,
                        reason = "outside_asphalt_band",
                    });
                    continue;
                }
                float targetBottom = sample.world.y + corridor.target_bottom_offset_m;
                if (Mathf.Abs(targetBottom - surfaceY)
                    > roadData.road_surface_tolerance_m)
                {
                    violations.Add(new RoadLegalityViolation
                    {
                        sample_index = index,
                        route_s_m = routeS,
                        x_m = sample.world.x,
                        z_m = sample.world.z,
                        reason = "target_bottom_not_on_road_surface",
                    });
                }
            }
            return violations;
        }

        static int RouteSampleCount(Vector3[] route, float spacing)
        {
            return Mathf.CeilToInt(ClosedRoutePerimeter(route) / spacing) + 1;
        }

        static float ClosedRoutePerimeter(Vector3[] route)
        {
            float perimeter = 0f;
            for (int index = 0; index < route.Length; index++)
                perimeter += Vector3.Distance(
                    route[index],
                    route[(index + 1) % route.Length]);
            if (perimeter <= GeometryEpsilon)
                throw new ArgumentException("Route contains no non-zero-length segment.");
            return perimeter;
        }

        static RoutePoint SampleClosedRoute(Vector3[] route, float distance)
        {
            float perimeter = ClosedRoutePerimeter(route);
            float wrapped = Mathf.Repeat(distance, perimeter);
            float prefix = 0f;
            for (int index = 0; index < route.Length; index++)
            {
                Vector3 start = route[index];
                Vector3 end = route[(index + 1) % route.Length];
                float length = Vector3.Distance(start, end);
                if (length <= GeometryEpsilon) continue;
                if (wrapped <= prefix + length + GeometryEpsilon)
                {
                    float along = Mathf.Clamp(wrapped - prefix, 0f, length);
                    Vector3 direction3 = (end - start) / length;
                    return new RoutePoint
                    {
                        distance = 0f,
                        routeS = distance,
                        direction = new Vector2(direction3.x, direction3.z).normalized,
                        world = start + direction3 * along,
                    };
                }
                prefix += length;
            }
            throw new InvalidOperationException("Could not sample closed route.");
        }

        static RoutePoint NearestPointOnClosedRoute(Vector2 point, Vector3[] route)
        {
            float bestDistance = float.PositiveInfinity;
            float bestRouteS = 0f;
            Vector2 bestDirection = Vector2.right;
            Vector3 bestWorld = route[0];
            float prefix = 0f;
            for (int index = 0; index < route.Length; index++)
            {
                Vector3 start3 = route[index];
                Vector3 end3 = route[(index + 1) % route.Length];
                Vector2 start = new Vector2(start3.x, start3.z);
                Vector2 end = new Vector2(end3.x, end3.z);
                Vector2 delta = end - start;
                float length = delta.magnitude;
                if (length <= GeometryEpsilon) continue;
                Vector2 direction = delta / length;
                float along = Mathf.Clamp(Vector2.Dot(point - start, direction), 0f, length);
                float distance = Vector2.Distance(point, start + direction * along);
                if (distance < bestDistance)
                {
                    float t = along / length;
                    bestDistance = distance;
                    bestRouteS = prefix + along;
                    bestDirection = direction;
                    bestWorld = Vector3.Lerp(start3, end3, t);
                }
                prefix += length;
            }
            if (float.IsInfinity(bestDistance))
                throw new ArgumentException("Route contains no non-zero-length segment.");
            return new RoutePoint
            {
                distance = bestDistance,
                routeS = bestRouteS,
                direction = bestDirection,
                world = bestWorld,
            };
        }

        static bool TrySurfaceAt(
            Vector2 point,
            RoadSceneData roadData,
            out float surfaceY)
        {
            float bestMargin = float.NegativeInfinity;
            surfaceY = 0f;
            bool found = false;
            foreach (RoadSurfacePatch surface in roadData.surfaces)
            {
                float radians = -surface.yaw_deg * Mathf.Deg2Rad;
                float cosine = Mathf.Cos(radians);
                float sine = Mathf.Sin(radians);
                Vector2 delta = point - new Vector2(
                    surface.center_x_m,
                    surface.center_z_m);
                float localX = cosine * delta.x - sine * delta.y;
                float localZ = sine * delta.x + cosine * delta.y;
                float margin = Mathf.Min(
                    surface.half_extent_x_m - Mathf.Abs(localX),
                    surface.half_extent_z_m - Mathf.Abs(localZ));
                if (margin < -GeometryEpsilon || margin <= bestMargin) continue;
                found = true;
                bestMargin = margin;
                surfaceY = surface.surface_y_m;
            }
            return found;
        }

        static float SurfaceHeightAt(
            Vector2 point,
            RoadSceneData roadData,
            bool nearestFallback)
        {
            if (TrySurfaceAt(point, roadData, out float surfaceY)) return surfaceY;
            if (!nearestFallback)
                throw new InvalidOperationException(
                    $"No road surface contains ({point.x:R}, {point.y:R}).");
            RoadSurfacePatch nearest = roadData.surfaces
                .OrderBy(surface => Vector2.SqrMagnitude(
                    point - new Vector2(surface.center_x_m, surface.center_z_m)))
                .First();
            return nearest.surface_y_m;
        }

        static void ValidateInputs(
            Vector3[] route,
            RouteCorridorScenarioConfig corridor,
            RoadSceneData roadData)
        {
            if (route == null || route.Length < 2)
                throw new ArgumentException("A route with at least two points is required.");
            if (corridor == null)
                throw new ArgumentNullException(nameof(corridor));
            if (roadData == null)
                throw new ArgumentNullException(nameof(roadData));
            roadData.Validate();
        }

        readonly struct Footprint2
        {
            public readonly float MinX;
            public readonly float MaxX;
            public readonly float MinZ;
            public readonly float MaxZ;
            public readonly Vector2[] Corners;
            public Vector2 Center => new Vector2(
                (MinX + MaxX) * 0.5f,
                (MinZ + MaxZ) * 0.5f);

            public Footprint2(Vector2[] corners)
            {
                Corners = corners;
                MinX = corners.Min(item => item.x);
                MaxX = corners.Max(item => item.x);
                MinZ = corners.Min(item => item.y);
                MaxZ = corners.Max(item => item.y);
            }

            public float SupportHalfExtent(Vector2 routeDirection)
            {
                Vector2 normal = new Vector2(-routeDirection.y, routeDirection.x);
                return Mathf.Abs(normal.x) * (MaxX - MinX) * 0.5f
                    + Mathf.Abs(normal.y) * (MaxZ - MinZ) * 0.5f;
            }
        }

        static Footprint2 TransformFootprint(
            Transform root,
            float minX,
            float maxX,
            float minZ,
            float maxZ)
        {
            Vector3[] world =
            {
                root.TransformPoint(new Vector3(minX, 0f, minZ)),
                root.TransformPoint(new Vector3(maxX, 0f, minZ)),
                root.TransformPoint(new Vector3(maxX, 0f, maxZ)),
                root.TransformPoint(new Vector3(minX, 0f, maxZ)),
            };
            return new Footprint2(
                world.Select(item => new Vector2(item.x, item.z)).ToArray());
        }

        static Footprint2 AxisAlignedFootprint(
            float minX,
            float maxX,
            float minZ,
            float maxZ)
        {
            return new Footprint2(new[]
            {
                new Vector2(minX, minZ),
                new Vector2(maxX, minZ),
                new Vector2(maxX, maxZ),
                new Vector2(minX, maxZ),
            });
        }

        static bool ConvexPolygonsIntersect(
            Vector2[] left,
            Vector2[] right)
        {
            return !HasSeparatingAxis(left, right)
                && !HasSeparatingAxis(right, left);
        }

        static bool HasSeparatingAxis(
            Vector2[] axesFrom,
            Vector2[] other)
        {
            for (int index = 0; index < axesFrom.Length; index++)
            {
                Vector2 edge =
                    axesFrom[(index + 1) % axesFrom.Length] - axesFrom[index];
                Vector2 axis = new Vector2(-edge.y, edge.x);
                if (axis.sqrMagnitude <= GeometryEpsilon) continue;
                float leftMin = float.PositiveInfinity;
                float leftMax = float.NegativeInfinity;
                foreach (Vector2 point in axesFrom)
                {
                    float projection = Vector2.Dot(point, axis);
                    leftMin = Mathf.Min(leftMin, projection);
                    leftMax = Mathf.Max(leftMax, projection);
                }
                float rightMin = float.PositiveInfinity;
                float rightMax = float.NegativeInfinity;
                foreach (Vector2 point in other)
                {
                    float projection = Vector2.Dot(point, axis);
                    rightMin = Mathf.Min(rightMin, projection);
                    rightMax = Mathf.Max(rightMax, projection);
                }
                if (leftMax < rightMin - GeometryEpsilon
                    || rightMax < leftMin - GeometryEpsilon)
                {
                    return true;
                }
            }
            return false;
        }

        static RoutePoint NearestFootprintPointOnClosedRoute(
            Footprint2 footprint,
            Vector3[] route)
        {
            float bestDistance = float.PositiveInfinity;
            float bestRouteS = 0f;
            Vector2 bestDirection = Vector2.right;
            Vector3 bestWorld = route[0];
            float prefix = 0f;
            for (int routeIndex = 0; routeIndex < route.Length; routeIndex++)
            {
                Vector3 start3 = route[routeIndex];
                Vector3 end3 = route[(routeIndex + 1) % route.Length];
                Vector2 start = new Vector2(start3.x, start3.z);
                Vector2 end = new Vector2(end3.x, end3.z);
                Vector2 delta = end - start;
                float length = delta.magnitude;
                if (length <= GeometryEpsilon) continue;
                Vector2 direction = delta / length;
                if (PointInConvexPolygon(start, footprint.Corners))
                    Consider(0f, 0f);
                for (int edge = 0; edge < footprint.Corners.Length; edge++)
                {
                    Vector2 edgeStart = footprint.Corners[edge];
                    Vector2 edgeEnd =
                        footprint.Corners[(edge + 1) % footprint.Corners.Length];
                    SegmentDistance(
                        start,
                        end,
                        edgeStart,
                        edgeEnd,
                        out float distance,
                        out float routeT);
                    Consider(distance, routeT);
                }
                prefix += length;

                void Consider(float distance, float routeT)
                {
                    if (distance >= bestDistance) return;
                    bestDistance = distance;
                    bestRouteS = prefix + routeT * length;
                    bestDirection = direction;
                    bestWorld = Vector3.Lerp(start3, end3, routeT);
                }
            }
            if (float.IsInfinity(bestDistance))
                throw new ArgumentException(
                    "Route contains no non-zero-length segment.");
            return new RoutePoint
            {
                distance = bestDistance,
                routeS = bestRouteS,
                direction = bestDirection,
                world = bestWorld,
            };
        }

        static void SegmentDistance(
            Vector2 routeStart,
            Vector2 routeEnd,
            Vector2 edgeStart,
            Vector2 edgeEnd,
            out float distance,
            out float routeT)
        {
            Vector2 route = routeEnd - routeStart;
            Vector2 edge = edgeEnd - edgeStart;
            float denominator = Cross(route, edge);
            if (Mathf.Abs(denominator) > GeometryEpsilon)
            {
                Vector2 offset = edgeStart - routeStart;
                float intersectionRouteT = Cross(offset, edge) / denominator;
                float intersectionEdgeT = Cross(offset, route) / denominator;
                if (intersectionRouteT >= 0f && intersectionRouteT <= 1f
                    && intersectionEdgeT >= 0f && intersectionEdgeT <= 1f)
                {
                    distance = 0f;
                    routeT = intersectionRouteT;
                    return;
                }
            }

            distance = PointSegmentDistance(
                routeStart,
                edgeStart,
                edgeEnd,
                out _);
            routeT = 0f;
            float candidate = PointSegmentDistance(
                routeEnd,
                edgeStart,
                edgeEnd,
                out _);
            if (candidate < distance)
            {
                distance = candidate;
                routeT = 1f;
            }
            candidate = PointSegmentDistance(
                edgeStart,
                routeStart,
                routeEnd,
                out float candidateRouteT);
            if (candidate < distance)
            {
                distance = candidate;
                routeT = candidateRouteT;
            }
            candidate = PointSegmentDistance(
                edgeEnd,
                routeStart,
                routeEnd,
                out candidateRouteT);
            if (candidate < distance)
            {
                distance = candidate;
                routeT = candidateRouteT;
            }
        }

        static float PointSegmentDistance(
            Vector2 point,
            Vector2 start,
            Vector2 end,
            out float segmentT)
        {
            Vector2 delta = end - start;
            float lengthSquared = delta.sqrMagnitude;
            segmentT = lengthSquared <= GeometryEpsilon
                ? 0f
                : Mathf.Clamp01(Vector2.Dot(point - start, delta) / lengthSquared);
            return Vector2.Distance(point, start + segmentT * delta);
        }

        static bool PointInConvexPolygon(Vector2 point, Vector2[] polygon)
        {
            float sign = 0f;
            for (int index = 0; index < polygon.Length; index++)
            {
                float cross = Cross(
                    polygon[(index + 1) % polygon.Length] - polygon[index],
                    point - polygon[index]);
                if (Mathf.Abs(cross) <= GeometryEpsilon) continue;
                if (sign == 0f)
                    sign = Mathf.Sign(cross);
                else if (Mathf.Sign(cross) != sign)
                    return false;
            }
            return true;
        }

        static float Cross(Vector2 left, Vector2 right)
        {
            return left.x * right.y - left.y * right.x;
        }

        static Vector2 TransformVerticalBounds(
            Transform root,
            RoadObstacleFootprint footprint)
        {
            var corners = new List<Vector3>(8);
            foreach (float x in new[]
                { footprint.full_min_x_m, footprint.full_max_x_m })
            {
                foreach (float y in new[]
                    { footprint.full_min_y_m, footprint.full_max_y_m })
                {
                    foreach (float z in new[]
                        { footprint.full_min_z_m, footprint.full_max_z_m })
                    {
                        corners.Add(root.TransformPoint(new Vector3(x, y, z)));
                    }
                }
            }
            return new Vector2(
                corners.Min(item => item.y),
                corners.Max(item => item.y));
        }

        static float TransformHorizontalPlaneMinimumY(
            Transform root,
            float minX,
            float maxX,
            float y,
            float minZ,
            float maxZ)
        {
            Vector3[] corners =
            {
                root.TransformPoint(new Vector3(minX, y, minZ)),
                root.TransformPoint(new Vector3(minX, y, maxZ)),
                root.TransformPoint(new Vector3(maxX, y, minZ)),
                root.TransformPoint(new Vector3(maxX, y, maxZ)),
            };
            return corners.Min(item => item.y);
        }
    }
}
