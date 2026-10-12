using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace TetheredTracking
{
    public class TetheredScenarioBootstrap : MonoBehaviour
    {
        public static TetheredScenarioBootstrap Instance { get; private set; }
        public TetheredDronePlant Drone { get; private set; }
        public TetheredGimbal Gimbal { get; private set; }
        public Camera SensorCamera { get; private set; }
        public LoopTargetVehicle Target { get; private set; }
        public SensorFrameWriter FrameWriter { get; private set; }
        public SimulationTimerHud TimerHud { get; private set; }
        public TrackingObservationReceiver ObservationReceiver { get; private set; }
        public EvaluationOcclusionGeometry OcclusionGeometry { get; private set; }
        public RateStudyExperimentController ExperimentController { get; private set; }
        public RateStudyScoutingTool ScoutingTool { get; private set; }
        public RouteCorridorDynamicMonitor CorridorMonitor { get; private set; }
        public PlacementJumpDiagnostic JumpDiagnostic { get; private set; }
        public ScenarioConfig Config { get; private set; }
        public RoadSceneData RoadData { get; private set; }
        public RoadSceneAuditReport SceneAudit { get; private set; }
        Transform anchorVisual;
        readonly PlacementPhaseGuard placementGuard = new PlacementPhaseGuard();
        IReadOnlyList<Transform> relocatedVehicles = Array.Empty<Transform>();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void AutoCreate()
        {
            if (FindAnyObjectByType<TetheredScenarioBootstrap>() != null) return;
            new GameObject("_TetheredScenario").AddComponent<TetheredScenarioBootstrap>();
        }

        void Awake()
        {
            Instance = this;
            Config = ScenarioConfig.Load();
            if (Config.scene_adjustments != null)
                RoadData = RoadSceneDataLoader.LoadVerified(Config.road_data_sha256);
            UnityEngine.Random.InitState(Config.random_seed);
            CreateOverheadCamera();
            CreateAnchor();
            CreateDrone();
            CreateTarget();
            ApplySceneAdjustments();
            CreateEvaluationOcclusionGeometry();
            FrameWriter = gameObject.AddComponent<SensorFrameWriter>();
            FrameWriter.Configure(Config.sensor);
            TimerHud = gameObject.AddComponent<SimulationTimerHud>();
            TimerHud.Configure(FrameWriter);
            ScoutingTool = gameObject.AddComponent<RateStudyScoutingTool>();
            ExperimentController = gameObject.AddComponent<RateStudyExperimentController>();
            ExperimentController.Initialize(Config, Target, FrameWriter);
            FrameWriter.FramePublished += OnFramePublished;
            gameObject.AddComponent<BodyCommandReceiver>();
            gameObject.AddComponent<GimbalCommandReceiver>();
            ObservationReceiver = gameObject.AddComponent<TrackingObservationReceiver>();
            gameObject.AddComponent<CoverageEvaluator>();
            Debug.Log($"Loaded tethered scenario '{Config.scenario_id}' from {Config.source_path}");
        }

        void ApplySceneAdjustments()
        {
            if (Config.scene_adjustments == null) return;
            var roots = SceneVehicleAdjustmentApplier.FindSceneVehicleRoots();
            relocatedVehicles = SceneVehicleAdjustmentApplier.Apply(
                Config.scene_adjustments,
                roots,
                placementGuard);
            RouteCorridorAuditReport report = RouteCorridorAuditor.Audit(
                Config.scenario_id,
                Config.TargetRoute(),
                Config.scene_adjustments.route_corridor,
                roots);
            RouteCorridorAuditor.WriteReport(report);
            if (report.violation_count != 0)
                throw new System.InvalidOperationException(
                    $"Scenario route corridor has {report.violation_count} violation(s); "
                    + "see runtime/route_corridor_audit.json.");
            Transform[] runtimeActors =
            {
                anchorVisual,
                Drone?.transform,
                Target?.transform,
                transform,
            };
            IReadOnlyList<Transform> staticRoots =
                RoadSceneAuditor.FindStaticRenderableRoots(runtimeActors);
            SceneAudit = RoadSceneAuditor.Audit(
                Config.scenario_id,
                Config.TargetRoute(),
                Config.scene_adjustments.route_corridor,
                RoadData,
                staticRoots);
            RoadSceneAuditor.WriteReport(SceneAudit);
            if (SceneAudit.road_violation_count != 0
                || SceneAudit.obstacle_violation_count != 0)
            {
                throw new InvalidOperationException(
                    $"Scenario legality audit found {SceneAudit.road_violation_count} "
                    + $"road and {SceneAudit.obstacle_violation_count} obstacle "
                    + "violation(s); see runtime/road_scene_audit.json.");
            }
            if (Config.scene_adjustments.route_corridor.enable_dynamic_intersection_audit)
            {
                CorridorMonitor = gameObject.AddComponent<RouteCorridorDynamicMonitor>();
                CorridorMonitor.Configure(
                    Config.scenario_id,
                    Target,
                    RoadData,
                    staticRoots);
            }
            if (Config.scene_adjustments.route_corridor.enable_jump_diagnostic)
            {
                JumpDiagnostic = gameObject.AddComponent<PlacementJumpDiagnostic>();
                Transform[] actors = new[] { Target.transform }
                    .Concat(relocatedVehicles.Where(
                        actor => actor.gameObject.activeInHierarchy))
                    .ToArray();
                float[] speeds = new[] { Config.target.speed_mps }
                    .Concat(relocatedVehicles
                        .Where(actor => actor.gameObject.activeInHierarchy)
                        .Select(_ => 0f))
                    .ToArray();
                JumpDiagnostic.Configure(
                    Config.scenario_id,
                    actors,
                    speeds,
                    Config.scene_adjustments.route_corridor.jump_epsilon_m);
            }
        }

        void OnFramePublished(SensorFrameInfo frame)
        {
            if (ExperimentController == null || !ExperimentController.IsActive)
                StartMeasurement("first-published-frame");
        }

        internal void StartMeasurement(string boundary)
        {
            placementGuard.StartMeasurement(boundary);
        }

        void CreateEvaluationOcclusionGeometry()
        {
            var root = new GameObject("_EvaluationOcclusionGeometry");
            root.transform.SetParent(transform, false);
            OcclusionGeometry = root.AddComponent<EvaluationOcclusionGeometry>();
            if (anchorVisual == null || Drone == null || Target == null)
                throw new System.InvalidOperationException(
                    "Runtime actor roots must exist before occlusion geometry is built.");
            OcclusionGeometry.Build(anchorVisual, Drone.transform, Target.transform);
        }

        void CreateOverheadCamera()
        {
            foreach (Camera existingCamera in FindObjectsByType<Camera>(FindObjectsInactive.Exclude))
                existingCamera.enabled = false;
            var go = new GameObject("OverviewCamera");
            go.transform.position = Config.Anchor + new Vector3(0f, 150f, -17f);
            go.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
            var overviewCamera = go.AddComponent<Camera>();
            overviewCamera.orthographic = true;
            overviewCamera.orthographicSize = 100f;
            overviewCamera.nearClipPlane = 0.3f;
            overviewCamera.farClipPlane = 300f;
            overviewCamera.depth = 100f;
            overviewCamera.tag = "MainCamera";
        }

        void CreateAnchor()
        {
            GameObject marker = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            marker.name = "TetherAnchor";
            marker.transform.position = Config.Anchor;
            marker.transform.localScale = new Vector3(1.2f, 0.2f, 1.2f);
            marker.GetComponent<Renderer>().material.color = new Color(0.95f, 0.75f, 0.1f);
            Destroy(marker.GetComponent<Collider>());
            anchorVisual = marker.transform;
        }

        void CreateDrone()
        {
            var drone = new GameObject("TetheredDrone_1");
            drone.transform.position = Config.Anchor + Vector3.up * Config.drone.initial_altitude_m;
            Drone = drone.AddComponent<TetheredDronePlant>();
            Drone.anchor = Config.Anchor;
            Drone.tetherLength = Config.drone.tether_length_m;
            Drone.minimumAltitude = Config.drone.minimum_altitude_m;
            Drone.maximumAltitude = Config.drone.maximum_altitude_m;
            Drone.maximumSpeed = Config.drone.maximum_speed_mps;
            Drone.maximumAcceleration = Config.drone.maximum_acceleration_mps2;
            Drone.tetherEnabled = Config.drone.tether_enabled;
            Drone.ConfigureGeofence(Config.drone.geofence_xz_m);
            AddDroneVisual(drone.transform);

            var cameraObject = new GameObject("SensorCamera");
            cameraObject.transform.SetParent(drone.transform);
            cameraObject.transform.localPosition = Vector3.zero;
            cameraObject.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
            SensorCamera = cameraObject.AddComponent<Camera>();
            SensorCamera.enabled = false;
            SensorCamera.fieldOfView = Config.sensor.vertical_fov_deg;
            SensorCamera.nearClipPlane = 0.3f;
            SensorCamera.farClipPlane = 500f;
            Gimbal = cameraObject.AddComponent<TetheredGimbal>();
            Gimbal.maximumOffNadirDeg = Config.gimbal.maximum_off_nadir_deg;
            Gimbal.slewRateDegPerSecond = Config.gimbal.slew_rate_deg_per_second;

            CreateTetherLine(Config, drone.transform);
        }

        /// <summary>
        /// P1-ENG-FRAME-001 Part T (AC-5): the cable visual exists only with
        /// the tether enabled, built exactly as before; with it disabled no
        /// <c>TetherLine</c> object is created. The anchor marker
        /// (<c>TetherAnchor</c>) is created unconditionally by
        /// <see cref="CreateAnchor"/> and stays as the home marker.
        /// </summary>
        internal static TetherLineVisual CreateTetherLine(ScenarioConfig config, Transform drone)
        {
            if (!config.drone.tether_enabled) return null;
            var tether = new GameObject("TetherLine");
            var visual = tether.AddComponent<TetherLineVisual>();
            visual.drone = drone;
            visual.anchor = config.Anchor;
            return visual;
        }

        void AddDroneVisual(Transform parent)
        {
            GameObject hub = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            hub.name = "DroneHub";
            hub.transform.SetParent(parent);
            hub.transform.localPosition = Vector3.zero;
            hub.transform.localScale = new Vector3(1.2f, 0.45f, 1.2f);
            hub.GetComponent<Renderer>().material.color = new Color(0.9f, 0.25f, 0.15f);
            Destroy(hub.GetComponent<Collider>());

            Vector3[] directions = {
                new Vector3(1f, 0f, 1f).normalized, new Vector3(1f, 0f, -1f).normalized,
                new Vector3(-1f, 0f, 1f).normalized, new Vector3(-1f, 0f, -1f).normalized,
            };
            foreach (Vector3 direction in directions)
            {
                GameObject arm = GameObject.CreatePrimitive(PrimitiveType.Cube);
                arm.transform.SetParent(parent);
                arm.transform.localPosition = direction * 0.8f;
                arm.transform.localRotation = Quaternion.LookRotation(direction);
                arm.transform.localScale = new Vector3(0.12f, 0.1f, 1.6f);
                arm.GetComponent<Renderer>().material.color = Color.gray;
                Destroy(arm.GetComponent<Collider>());
            }
        }

        void CreateTarget()
        {
            var target = new GameObject("TargetVehicle_Red");
            AddCarVisual(target.transform);
            Target = target.AddComponent<LoopTargetVehicle>();
            Target.SetPlacementGuard(placementGuard);
            Target.Configure(Config.target.track_id, Config.TargetRoute(), Config.target.speed_mps);
        }

        /// <summary>
        /// Pure delegation to the §3.1 single production construction source;
        /// the only runtime-side difference is collider removal, which the
        /// factory leaves to the consumer. The rendered result is literally
        /// unchanged from the pre-parity construction, so the scout-4 and
        /// qual-3 baselines measured on this object stay valid.
        /// </summary>
        void AddCarVisual(Transform parent)
        {
            TargetVisualFactory.Build build =
                TargetVisualFactory.AddTargetVisual(parent);
            Destroy(build.BodyCollider);
            Destroy(build.RoofCollider);
        }
    }
}
