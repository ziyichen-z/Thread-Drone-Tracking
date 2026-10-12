using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// Edit-Mode scene preparation for the P1-SCENE-006 batch-1 offline
    /// tools: opens the city scene on the frozen scenario bytes, applies the
    /// frozen vehicle adjustments, loads the verified road data, and builds
    /// the tool-owned actors (target replica, evaluation camera, occlusion
    /// proxies). Zero Play, zero scenario creation, zero session/run ID.
    /// Everything created here is marked DontSave and destroyed by
    /// <see cref="Cleanup"/>.
    /// </summary>
    public sealed class Scene006SceneRig
    {
        public const string CityScenePath =
            "Assets/SimplePoly City - Low Poly Assets/Demo/"
            + "SimplePoly City - Low Poly Assets_Demo Scene.unity";
        public const string DefaultScenarioPath = "scenario.default.json";

        public ScenarioConfig Config;
        public string ScenarioSha256;
        public RoadSceneData RoadData;
        public Transform[] StaticRoots;
        public GameObject TargetReplica;
        public Renderer[] TargetRenderers;
        public Camera EvaluationCamera;
        public GameObject OcclusionRoot;
        readonly List<GameObject> owned = new List<GameObject>();

        public static ScenarioConfig LoadFrozenScenario(
            out string sha256,
            string fileName = DefaultScenarioPath)
        {
            string path = RuntimePaths.ProjectFile("config", fileName);
            byte[] bytes = File.ReadAllBytes(path);
            sha256 = Scene006RouteGeometry.Sha256Hex(bytes);
            ScenarioConfig config = ScenarioConfig.FromJsonStrict(
                System.Text.Encoding.UTF8.GetString(bytes));
            config.source_path = path;
            return config;
        }

        public void OpenCityScene()
        {
            EditorSceneManager.OpenScene(CityScenePath, OpenSceneMode.Single);
        }

        /// <summary>
        /// Applies the frozen scene_adjustments to the open scene. Edit-Mode
        /// batch runs never save the scene; the placement guard starts fresh
        /// so every relocation is a legal placement-phase operation.
        /// </summary>
        public void ApplySceneAdjustments()
        {
            if (Config.scene_adjustments == null) return;
            SceneVehicleAdjustmentApplier.Apply(
                Config.scene_adjustments,
                SceneVehicleAdjustmentApplier.FindSceneVehicleRoots(),
                new PlacementPhaseGuard());
        }

        public void LoadRoadData()
        {
            RoadData = RoadSceneDataLoader.LoadVerified(
                Config.road_data_sha256);
        }

        public void CollectStaticRoots(params Transform[] excluded)
        {
            StaticRoots = RoadSceneAuditor
                .FindStaticRenderableRoots(excluded)
                .Where(root => root != null && root.gameObject.activeInHierarchy)
                .ToArray();
        }

        /// <summary>
        /// Target replica built by the §3.1 single production construction
        /// source (`TargetVisualFactory`), so the offline probe renders the
        /// same painted body/roof cubes the runtime bootstrap builds — the
        /// F23 appearance gap. Geometry is unchanged (body at (0, 0.5, 0)
        /// scaled (2, 1, 4), roof at (0, 1.2, -0.2) scaled (1.7, 0.7, 2)),
        /// so every batch-1 geometric gate keeps its reviewed values.
        ///
        /// Editor-side consumer bookkeeping only (§3.1.2 exhaustive list):
        /// `DestroyImmediate` for the colliders, `DontSave` on the created
        /// objects, and the replica root's name/ownership.
        /// </summary>
        public void CreateTargetReplica()
        {
            TargetReplica = new GameObject("Scene006TargetReplica")
            {
                hideFlags = HideFlags.DontSave,
            };
            TargetVisualFactory.Build build =
                TargetVisualFactory.AddTargetVisual(TargetReplica.transform);
            UnityEngine.Object.DestroyImmediate(build.BodyCollider);
            UnityEngine.Object.DestroyImmediate(build.RoofCollider);
            build.Body.hideFlags = HideFlags.DontSave;
            build.Roof.hideFlags = HideFlags.DontSave;
            TargetRenderers = new[] { build.BodyRenderer, build.RoofRenderer };
            owned.Add(TargetReplica);
        }

        /// <summary>
        /// Evaluation camera with the frozen sensor intrinsics
        /// (Scripts/TetheredScenarioBootstrap.cs:198-206): vertical FOV from
        /// the optics under test, aspect = width / height, near 0.3, far
        /// 500, disabled (posed explicitly and rendered/queried by the tool).
        /// </summary>
        public void CreateEvaluationCamera(
            float verticalFovDeg,
            int imageWidth,
            int imageHeight)
        {
            var go = new GameObject("Scene006EvaluationCamera")
            {
                hideFlags = HideFlags.DontSave,
            };
            EvaluationCamera = go.AddComponent<Camera>();
            EvaluationCamera.enabled = false;
            EvaluationCamera.fieldOfView = verticalFovDeg;
            EvaluationCamera.aspect = imageWidth / (float)imageHeight;
            EvaluationCamera.nearClipPlane = 0.3f;
            EvaluationCamera.farClipPlane = 500f;
            owned.Add(go);
        }

        /// <summary>
        /// Builds the same invisible mesh-collider proxies the runtime
        /// evaluator uses (EvaluationOcclusionGeometry), so offline raycasts
        /// see the rendered city geometry. Only the tool-owned target replica
        /// is excluded (it is the raycast target, never an occluder).
        /// </summary>
        public void BuildOcclusionProxies()
        {
            OcclusionRoot = new GameObject("Scene006OcclusionGeometry")
            {
                hideFlags = HideFlags.DontSave,
            };
            var geometry =
                OcclusionRoot.AddComponent<EvaluationOcclusionGeometry>();
            geometry.Build(TargetReplica.transform);
            owned.Add(OcclusionRoot);
        }

        /// <summary>
        /// The full instance set as T4 certificate prisms (F2 literal
        /// §5.4.4): every active static root — road-surface and
        /// support-allowlist instances included — transformed through the
        /// real TRS. Road-surface instances have no obstacle footprint
        /// prototype; their prisms come from the measured road_data
        /// surfaces (rectangle + yaw + surface_y, with the 0.2 m slab
        /// thickness that matches the frozen ground plane 0.2000004).
        /// Unsupported TRS configurations and unclassified non-road roots
        /// fail closed (throw), never silently pass.
        /// </summary>
        public Scene006PathCertificate.ObstaclePrism[] BuildAllInstancePrisms(
            string[] supportSurfaceAllowlist)
        {
            var prisms = new List<Scene006PathCertificate.ObstaclePrism>(
                BuildObstaclePrisms(supportSurfaceAllowlist));
            var supportNames = new HashSet<string>(
                supportSurfaceAllowlist, StringComparer.Ordinal);
            var footprints = RoadData.obstacle_footprints.ToDictionary(
                item => item.canonical_name, StringComparer.Ordinal);
            foreach (Transform root in StaticRoots)
            {
                string canonical =
                    SceneVehicleAdjustmentApplier.CanonicalPrefabName(root.name);
                if (!supportNames.Contains(canonical)) continue;
                if (!footprints.TryGetValue(
                    canonical, out RoadObstacleFootprint footprint))
                {
                    throw new InvalidOperationException(
                        "unclassified_obstacle:" + root.name);
                }
                prisms.Add(TransformPrism(root, footprint));
            }
            foreach (RoadSurfacePatch surface in RoadData.surfaces)
            {
                float radians = surface.yaw_deg * Mathf.Deg2Rad;
                Vector2 center = new Vector2(
                    surface.center_x_m, surface.center_z_m);
                Vector2 right = new Vector2(
                    Mathf.Cos(radians), Mathf.Sin(radians));
                Vector2 forward = new Vector2(
                    -Mathf.Sin(radians), Mathf.Cos(radians));
                Vector2[] corners =
                {
                    center + right * surface.half_extent_x_m
                        + forward * surface.half_extent_z_m,
                    center - right * surface.half_extent_x_m
                        + forward * surface.half_extent_z_m,
                    center - right * surface.half_extent_x_m
                        - forward * surface.half_extent_z_m,
                    center + right * surface.half_extent_x_m
                        - forward * surface.half_extent_z_m,
                };
                prisms.Add(new Scene006PathCertificate.ObstaclePrism(
                    surface.id,
                    corners,
                    surface.surface_y_m - RoadSlabThicknessM,
                    surface.surface_y_m));
            }
            return prisms.ToArray();
        }

        public const float RoadSlabThicknessM = 0.2f;

        /// <summary>
        /// The T5/§5.5 obstacle set as T4 certificate prisms: every active
        /// static root except the road-surface and support-allowlist
        /// instances, transformed through the real TRS with the anchor-audit
        /// footprint semantics. Unsupported TRS configurations and
        /// unclassified roots fail closed (throw), never silently pass.
        /// </summary>
        public Scene006PathCertificate.ObstaclePrism[] BuildObstaclePrisms(
            string[] supportSurfaceAllowlist)
        {
            var roadNames = new HashSet<string>(
                RoadData.road_surface_allowlist, StringComparer.Ordinal);
            var supportNames = new HashSet<string>(
                supportSurfaceAllowlist, StringComparer.Ordinal);
            var footprints = RoadData.obstacle_footprints.ToDictionary(
                item => item.canonical_name, StringComparer.Ordinal);
            var prisms = new List<Scene006PathCertificate.ObstaclePrism>();
            foreach (Transform root in StaticRoots)
            {
                string canonical =
                    SceneVehicleAdjustmentApplier.CanonicalPrefabName(root.name);
                if (roadNames.Contains(canonical)
                    || supportNames.Contains(canonical))
                {
                    continue;
                }
                if (!footprints.TryGetValue(
                    canonical, out RoadObstacleFootprint footprint))
                {
                    throw new InvalidOperationException(
                        "unclassified_obstacle:" + root.name);
                }
                prisms.Add(TransformPrism(root, footprint));
            }
            return prisms.ToArray();
        }

        /// <summary>
        /// Replicates the anchor-audit footprint transform
        /// (Scripts/P1Scene003AnchorAudit.cs:549-595): fail-closed TRS
        /// check, the eight full-AABB corners transformed for the vertical
        /// range, and the four XZ side corners at local y = 0.
        /// </summary>
        static Scene006PathCertificate.ObstaclePrism TransformPrism(
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
                    source.full_min_x_m, 0f, source.full_min_z_m))),
                ToXZ(root.TransformPoint(new Vector3(
                    source.full_max_x_m, 0f, source.full_min_z_m))),
                ToXZ(root.TransformPoint(new Vector3(
                    source.full_max_x_m, 0f, source.full_max_z_m))),
                ToXZ(root.TransformPoint(new Vector3(
                    source.full_min_x_m, 0f, source.full_max_z_m))),
            };
            return new Scene006PathCertificate.ObstaclePrism(
                root.name, corners, minY, maxY);
        }

        static Vector2 ToXZ(Vector3 value) => new Vector2(value.x, value.z);

        public void Cleanup()
        {
            foreach (GameObject go in owned)
            {
                if (go != null) UnityEngine.Object.DestroyImmediate(go);
            }
            owned.Clear();
            TargetReplica = null;
            TargetRenderers = null;
            EvaluationCamera = null;
            OcclusionRoot = null;
        }
    }
}
