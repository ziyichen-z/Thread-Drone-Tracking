using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TetheredTracking.Editor
{
    public static class RoadSceneEvidenceGenerator
    {
        const string ScenePath =
            "Assets/SimplePoly City - Low Poly Assets/Demo/"
            + "SimplePoly City - Low Poly Assets_Demo Scene.unity";
        const float EnvelopeTopWorldY = 2.25f;
        const float MeasuredLaneAsphaltHalfWidthM = 6f;

        [Serializable]
        sealed class EvidenceSummary
        {
            public string schema_version = "p1-scene-002-evidence/v1";
            public string road_data_sha256;
            public int baseline_road_violations;
            public int baseline_obstacle_violations;
            public int corrected_road_violations;
            public int corrected_obstacle_violations;
            public int corrected_audited_obstacles;
            public int corrected_overhead_exemptions;
            public int corrected_vehicle_corridor_audited;
            public int corrected_vehicle_corridor_violations;
            public string[] relocated_scene_objects;
            public Vector3[] relocated_positions_m;
        }

        public static void GenerateRoadData()
        {
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            Transform[] roots = SceneRoots();
            var roadNames = new HashSet<string>(StringComparer.Ordinal);
            var surfaces = new List<RoadSurfacePatch>();
            var footprints = new Dictionary<string, RoadObstacleFootprint>(
                StringComparer.Ordinal);

            foreach (Transform root in roots)
            {
                string canonical =
                    SceneVehicleAdjustmentApplier.CanonicalPrefabName(root.name);
                if (canonical.StartsWith("Road ", StringComparison.Ordinal))
                {
                    roadNames.Add(canonical);
                    if (HasAsphaltSurface(canonical)
                        && TryMeasureAsphaltPatch(
                        root,
                        canonical,
                        out RoadSurfacePatch surface))
                    {
                        surfaces.Add(surface);
                    }
                    continue;
                }
                RoadObstacleFootprint measured = MeasureFootprint(root, canonical);
                if (footprints.TryGetValue(canonical, out RoadObstacleFootprint existing))
                {
                    footprints[canonical] = Merge(existing, measured);
                }
                else footprints.Add(canonical, measured);
            }

            if (surfaces.Count == 0)
                throw new InvalidOperationException(
                    "No asphalt surface patches were measured.");
            var data = new RoadSceneData
            {
                schema_version = RoadSceneData.Schema,
                road_surface_tolerance_m = 0.1f,
                road_surface_allowlist =
                    roadNames.OrderBy(value => value, StringComparer.Ordinal).ToArray(),
                surfaces = surfaces
                    .OrderBy(value => value.id, StringComparer.Ordinal)
                    .ToArray(),
                obstacle_footprints = footprints.Values
                    .OrderBy(value => value.canonical_name, StringComparer.Ordinal)
                    .ToArray(),
            };
            data.Validate();
            string json = JsonUtility.ToJson(data, true) + "\n";
            File.WriteAllText(RoadSceneDataLoader.ProjectPath, json);
            Debug.Log(
                $"P1-SCENE-002 road data generated: {data.surfaces.Length} patches, "
                + $"{data.obstacle_footprints.Length} obstacle prefabs, SHA-256 "
                + RoadSceneDataLoader.Sha256(File.ReadAllBytes(
                    RoadSceneDataLoader.ProjectPath)));
        }

        public static void GenerateEvidence()
        {
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            string configPath = RuntimePaths.ProjectFile(
                "config",
                "scenario.default.json");
            ScenarioConfig config = ScenarioConfig.FromJsonStrict(
                File.ReadAllText(configPath));
            RoadSceneData roadData = RoadSceneDataLoader.LoadVerified(
                config.road_data_sha256);
            Transform[] roots = SceneRoots();
            Vector3[] oldRoute =
            {
                new Vector3(132f, 0.2f, 117f),
                new Vector3(180f, 0.2f, 117f),
                new Vector3(183f, 0.2f, 114f),
                new Vector3(183f, 0.2f, 66f),
                new Vector3(180f, 0.2f, 63f),
                new Vector3(132f, 0.2f, 63f),
                new Vector3(129f, 0.2f, 66f),
                new Vector3(129f, 0.2f, 114f),
            };
            RoadSceneAuditReport before = RoadSceneAuditor.Audit(
                config.scenario_id + "-legacy-route",
                oldRoute,
                config.scene_adjustments.route_corridor,
                roadData,
                roots);
            Write("P1-SCENE-002-audit-before.json", before);
            if (before.road_violation_count == 0
                || before.obstacle_violation_count < 3)
            {
                throw new InvalidOperationException(
                    "Legacy route did not reproduce the required road/obstacle defect.");
            }

            Transform[] vehicleRoots =
                SceneVehicleAdjustmentApplier.FindSceneVehicleRoots().ToArray();
            IReadOnlyList<Transform> relocated =
                SceneVehicleAdjustmentApplier.Apply(
                    config.scene_adjustments,
                    vehicleRoots);
            RouteCorridorAuditReport vehicleCorridor =
                RouteCorridorAuditor.Audit(
                    config.scenario_id,
                    config.TargetRoute(),
                    config.scene_adjustments.route_corridor,
                    vehicleRoots);
            if (vehicleCorridor.violation_count != 0)
            {
                throw new InvalidOperationException(
                    $"Corrected legacy vehicle-corridor gate has "
                    + $"{vehicleCorridor.violation_count} violation(s).");
            }
            RoadSceneAuditReport after = RoadSceneAuditor.Audit(
                config.scenario_id + "-corrected-route",
                config.TargetRoute(),
                config.scene_adjustments.route_corridor,
                roadData,
                roots);
            Write("P1-SCENE-002-audit-after.json", after);
            if (after.road_violation_count != 0
                || after.obstacle_violation_count != 0)
            {
                throw new InvalidOperationException(
                    $"Corrected route is not clear: {after.road_violation_count} "
                    + $"road, {after.obstacle_violation_count} obstacle violations.");
            }
            Write("P1-SCENE-002-audit-summary.json", new EvidenceSummary
            {
                road_data_sha256 = config.road_data_sha256,
                baseline_road_violations = before.road_violation_count,
                baseline_obstacle_violations = before.obstacle_violation_count,
                corrected_road_violations = after.road_violation_count,
                corrected_obstacle_violations = after.obstacle_violation_count,
                corrected_audited_obstacles = after.audited_obstacle_count,
                corrected_overhead_exemptions = after.overhead_exemption_count,
                corrected_vehicle_corridor_audited =
                    vehicleCorridor.audited_vehicle_count,
                corrected_vehicle_corridor_violations =
                    vehicleCorridor.violation_count,
                relocated_scene_objects = relocated.Select(root => root.name).ToArray(),
                relocated_positions_m =
                    relocated.Select(root => root.position).ToArray(),
            });
            Debug.Log(
                $"P1-SCENE-002 evidence generated: road {before.road_violation_count}"
                + $"→{after.road_violation_count}, obstacles "
                + $"{before.obstacle_violation_count}→{after.obstacle_violation_count}.");
        }

        static Transform[] SceneRoots()
        {
            return UnityEngine.Object.FindObjectsByType<Transform>(
                    FindObjectsInactive.Exclude,
                    FindObjectsSortMode.None)
                .Where(root => root.parent == null)
                .Where(root =>
                    root.GetComponentsInChildren<MeshRenderer>(false).Length > 0)
                .OrderBy(root => root.name, StringComparer.Ordinal)
                .ToArray();
        }

        static bool TryMeasureAsphaltPatch(
            Transform root,
            string canonical,
            out RoadSurfacePatch patch)
        {
            var localVertices = new List<Vector3>();
            foreach (MeshFilter filter in root.GetComponentsInChildren<MeshFilter>(false))
            {
                MeshRenderer renderer = filter.GetComponent<MeshRenderer>();
                Mesh mesh = filter.sharedMesh;
                if (renderer == null || mesh == null) continue;
                Material[] materials = renderer.sharedMaterials;
                for (int submesh = 0; submesh < mesh.subMeshCount; submesh++)
                {
                    string materialName = submesh < materials.Length
                        && materials[submesh] != null
                            ? materials[submesh].name
                            : string.Empty;
                    if (!IsAsphaltMaterial(materialName)) continue;
                    int[] triangles = mesh.GetTriangles(submesh);
                    Vector3[] vertices = mesh.vertices;
                    foreach (int vertexIndex in triangles)
                    {
                        Vector3 world = filter.transform.TransformPoint(
                            vertices[vertexIndex]);
                        localVertices.Add(root.InverseTransformPoint(world));
                    }
                }
            }
            if (localVertices.Count == 0)
            {
                patch = null;
                return false;
            }
            float minX = localVertices.Min(value => value.x);
            float maxX = localVertices.Max(value => value.x);
            float minZ = localVertices.Min(value => value.z);
            float maxZ = localVertices.Max(value => value.z);
            float surfaceY = localVertices.Max(value => value.y);
            Vector3 localCenter = new Vector3(
                (minX + maxX) * 0.5f,
                surfaceY,
                (minZ + maxZ) * 0.5f);
            Vector3 worldCenter = root.TransformPoint(localCenter);
            Vector3 scale = root.lossyScale;
            float halfExtentX = (maxX - minX) * 0.5f * scale.x;
            float halfExtentZ = (maxZ - minZ) * 0.5f * scale.z;
            if (canonical.StartsWith("Road Lane", StringComparison.Ordinal))
                halfExtentX = Mathf.Min(
                    halfExtentX,
                    MeasuredLaneAsphaltHalfWidthM);
            patch = new RoadSurfacePatch
            {
                id = root.name + "@"
                    + worldCenter.x.ToString("R") + ","
                    + worldCenter.z.ToString("R"),
                canonical_name = canonical,
                center_x_m = worldCenter.x,
                center_z_m = worldCenter.z,
                yaw_deg = root.eulerAngles.y,
                half_extent_x_m = halfExtentX,
                half_extent_z_m = halfExtentZ,
                surface_y_m = worldCenter.y,
            };
            return true;
        }

        static bool IsAsphaltMaterial(string name)
        {
            return name.IndexOf("Road", StringComparison.OrdinalIgnoreCase) >= 0
                && name.IndexOf("Concrete", StringComparison.OrdinalIgnoreCase) < 0;
        }

        static bool HasAsphaltSurface(string canonical)
        {
            return canonical.StartsWith("Road Lane", StringComparison.Ordinal)
                || canonical.StartsWith("Road Intersection", StringComparison.Ordinal)
                || canonical.StartsWith(
                    "Road T_Intersection",
                    StringComparison.Ordinal)
                || canonical.StartsWith("Road Corner", StringComparison.Ordinal)
                || canonical == "Road Tile"
                || canonical == "Road Tile Small";
        }

        static RoadObstacleFootprint MeasureFootprint(
            Transform root,
            string canonical)
        {
            var full = new List<Vector3>();
            var ground = new List<Vector3>();
            var overhead = new List<Vector3>();
            foreach (MeshFilter filter in root.GetComponentsInChildren<MeshFilter>(false))
            {
                Mesh mesh = filter.sharedMesh;
                if (mesh == null) continue;
                Vector3[] vertices = mesh.vertices;
                for (int submesh = 0; submesh < mesh.subMeshCount; submesh++)
                {
                    int[] triangles = mesh.GetTriangles(submesh);
                    for (int index = 0; index < triangles.Length; index += 3)
                    {
                        Vector3[] triangle =
                        {
                            root.InverseTransformPoint(
                                filter.transform.TransformPoint(
                                    vertices[triangles[index]])),
                            root.InverseTransformPoint(
                                filter.transform.TransformPoint(
                                    vertices[triangles[index + 1]])),
                            root.InverseTransformPoint(
                                filter.transform.TransformPoint(
                                    vertices[triangles[index + 2]])),
                        };
                        full.AddRange(triangle);
                        float minimumWorldY = triangle
                            .Select(root.TransformPoint)
                            .Min(value => value.y);
                        if (minimumWorldY <= EnvelopeTopWorldY)
                            ground.AddRange(triangle);
                        else overhead.AddRange(triangle);
                    }
                }
            }
            if (full.Count == 0)
                throw new InvalidOperationException(
                    $"Could not measure a footprint for '{root.name}'.");
            bool overheadOnly = ground.Count == 0;
            if (overheadOnly) ground.AddRange(full);
            return new RoadObstacleFootprint
            {
                canonical_name = canonical,
                classification = overheadOnly ? "overhead" : "ground-obstacle",
                group = Group(canonical),
                full_min_x_m = full.Min(value => value.x),
                full_max_x_m = full.Max(value => value.x),
                full_min_y_m = full.Min(value => value.y),
                full_max_y_m = full.Max(value => value.y),
                full_min_z_m = full.Min(value => value.z),
                full_max_z_m = full.Max(value => value.z),
                ground_min_x_m = ground.Min(value => value.x),
                ground_max_x_m = ground.Max(value => value.x),
                ground_min_z_m = ground.Min(value => value.z),
                ground_max_z_m = ground.Max(value => value.z),
                overhead_min_y_m = overhead.Count == 0
                    ? full.Max(value => value.y) + 1f
                    : overhead.Min(value => value.y),
            };
        }

        static string Group(string canonical)
        {
            if (canonical.StartsWith("Vehicle_", StringComparison.Ordinal))
                return "vehicle";
            if (canonical.StartsWith("Props_", StringComparison.Ordinal))
                return "prop";
            if (canonical.StartsWith("Natures_", StringComparison.Ordinal))
                return "nature";
            if (canonical.StartsWith("Building", StringComparison.Ordinal))
                return "building";
            return "other";
        }

        static RoadObstacleFootprint Merge(
            RoadObstacleFootprint left,
            RoadObstacleFootprint right)
        {
            if (left.group != right.group)
                throw new InvalidOperationException(
                    $"Prefab '{left.canonical_name}' has inconsistent groups.");
            return new RoadObstacleFootprint
            {
                canonical_name = left.canonical_name,
                classification =
                    left.classification == "ground-obstacle"
                    || right.classification == "ground-obstacle"
                        ? "ground-obstacle"
                        : "overhead",
                group = left.group,
                full_min_x_m = Mathf.Min(left.full_min_x_m, right.full_min_x_m),
                full_max_x_m = Mathf.Max(left.full_max_x_m, right.full_max_x_m),
                full_min_y_m = Mathf.Min(left.full_min_y_m, right.full_min_y_m),
                full_max_y_m = Mathf.Max(left.full_max_y_m, right.full_max_y_m),
                full_min_z_m = Mathf.Min(left.full_min_z_m, right.full_min_z_m),
                full_max_z_m = Mathf.Max(left.full_max_z_m, right.full_max_z_m),
                ground_min_x_m =
                    Mathf.Min(left.ground_min_x_m, right.ground_min_x_m),
                ground_max_x_m =
                    Mathf.Max(left.ground_max_x_m, right.ground_max_x_m),
                ground_min_z_m =
                    Mathf.Min(left.ground_min_z_m, right.ground_min_z_m),
                ground_max_z_m =
                    Mathf.Max(left.ground_max_z_m, right.ground_max_z_m),
                overhead_min_y_m =
                    Mathf.Min(left.overhead_min_y_m, right.overhead_min_y_m),
            };
        }

        static void Write(string name, object report)
        {
            string path = RuntimePaths.ProjectFile("docs", "evidence", name);
            File.WriteAllText(path, JsonUtility.ToJson(report, true) + "\n");
        }
    }
}
