using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace TetheredTracking
{
    public class CoverageEvaluator : MonoBehaviour
    {
        /// <summary>
        /// One evaluation-domain truth sample on the released RATE-003
        /// measurement span (§5 inter-frame displacement, §11 lap period).
        /// Offline analysis input only; never a controller or perception
        /// input, and never part of outbound sensor metadata.
        /// </summary>
        [Serializable]
        internal sealed class Rate3EvaluationTruthRecord
        {
            public string schema_version = "p1-rate3-evaluation-truth/v1";
            public string study_id;
            public string run_id;
            public long frame_id;
            public long release_frame_id;
            public float simulation_time_s;
            public double capture_monotonic_s;
            public string capture_monotonic_clock_id;
            public bool geometrically_visible;
            public bool truth_box_available;
            public float truth_box_x;
            public float truth_box_y;
            public float truth_box_width;
            public float truth_box_height;
            public float truth_center_x_px;
            public float truth_center_y_px;
            public float target_world_x_m;
            public float target_world_z_m;
        }

        internal const string Rate3EvaluationTruthFileName =
            "evaluation_truth.jsonl";

        /// <summary>
        /// P1-M3-BODY-001 batch 1c (Acceptance round 11 §B.2, round 12 §B.5):
        /// one per-sensor-frame evaluation-domain truth plus body-platform
        /// sample for ordinary (non-experiment, non-qualification) Plays.
        /// v2 adds the actual body position and the plant's AppliedVelocity
        /// so the offline cost axis integrates applied, never requested,
        /// velocity. Offline analysis input only; never a controller or
        /// perception input, never part of outbound sensor metadata, and
        /// never read by any decision path. The run binding (run_id,
        /// first/last frame, counts, file hashes) is produced offline by
        /// tools/analyze_m3_body.py; this stream deliberately carries no
        /// run identity because the tracker run is only created mid-Play.
        /// </summary>
        [Serializable]
        internal sealed class M3BodyTruthRecord
        {
            public string schema_version = "p1-m3-body-truth/v2";
            public string scenario_id;
            public long frame_id;
            public float simulation_time_s;
            public double capture_monotonic_s;
            public string capture_monotonic_clock_id;
            public float target_world_x_m;
            public float target_world_y_m;
            public float target_world_z_m;
            public float body_world_x_m;
            public float body_world_y_m;
            public float body_world_z_m;
            public float applied_velocity_x_mps;
            public float applied_velocity_y_mps;
            public float applied_velocity_z_mps;
            public bool intersects_frustum;
            public bool has_unoccluded_sample;
            public bool geometrically_visible;
            public float visible_sample_fraction;
            public bool truth_box_available;
            public float truth_box_x;
            public float truth_box_y;
            public float truth_box_width;
            public float truth_box_height;
            public float truth_center_x_px;
            public float truth_center_y_px;
            public float target_bbox_area_px;
            public float target_center_error_px;
            public bool gimbal_saturated;
            public bool tether_saturated;
            public float evaluation_aspect_width_over_height;
        }

        internal const string M3BodyTruthFileName = "m3_body_truth.jsonl";

        [Serializable]
        class MetricThresholds
        {
            public float minimum_visible_sample_fraction;
            public float tracking_iou;
        }

        [Serializable]
        class CurrentMetrics
        {
            public long frame_id = -1;
            public bool target_intersects_frustum;
            public bool target_unoccluded;
            public bool c_geom;
            public bool tracking_observation_received;
            public bool tracking_success;
            public float tracking_iou;
            public float visible_sample_fraction;
            public float target_bbox_area_px;
            public float target_center_error_px;
        }

        [Serializable]
        class AggregateMetrics
        {
            public float c_geom;
            public float c_track;
            public float c_track_given_geom;
            public float mean_visible_sample_fraction;
            public float mean_target_bbox_area_px_when_visible;
            public float rms_target_center_error_px_when_visible;
            public int sensor_frames;
            public int matched_tracking_observations;
            public int unmatched_tracking_observations;
            public int incorrect_tracking_observations;
        }

        [Serializable]
        class OcclusionGeometryDiagnostics
        {
            public int candidate_renderers;
            public int mesh_collider_proxies;
            public int existing_colliders;
            public int failed_proxies;
            public int excluded_renderers;
            public int layer;
            public bool used_default_layer_fallback;
        }

        /// <summary>
        /// P1-EVAL-001 per-run evaluation-projection provenance: the sensor
        /// capture dimensions and the aspect every truth projection in this
        /// run was pinned to. Appended to the tethered-evaluation/v1 document;
        /// existing fields, formulas and thresholds are unchanged.
        /// </summary>
        [Serializable]
        class EvaluationProjection
        {
            public int sensor_width_px;
            public int sensor_height_px;
            public float aspect_width_over_height;
        }

        [Serializable]
        class MetricsDocument
        {
            public string schema_version = "tethered-evaluation/v1";
            public string scenario_id;
            public float elapsed_simulation_s;
            public MetricThresholds thresholds;
            public CurrentMetrics current;
            public AggregateMetrics aggregate;
            public QualificationMetricsOrigin qualification_release;
            public OcclusionGeometryDiagnostics occlusion_geometry;
            public bool gimbal_saturated;
            public bool tether_saturated;
            public EvaluationProjection evaluation_projection;
        }

        sealed class FrameRecord
        {
            public long FrameId;
            public float WeightSeconds;
            public bool GeometricallyVisible;
            public NormalizedBoundingBox GroundTruthBox;
            public bool ObservationProcessed;
        }

        internal readonly struct VisibilitySnapshot
        {
            public readonly bool IntersectsFrustum;
            public readonly bool HasUnoccludedSample;
            public readonly bool GeometricallyVisible;
            public readonly float VisibleSampleFraction;
            public readonly NormalizedBoundingBox GroundTruthBox;
            public readonly float BoundingBoxAreaPixels;
            public readonly float CenterErrorPixels;

            public VisibilitySnapshot(
                bool intersectsFrustum,
                bool hasUnoccludedSample,
                bool geometricallyVisible,
                float visibleSampleFraction,
                NormalizedBoundingBox groundTruthBox,
                float boundingBoxAreaPixels,
                float centerErrorPixels)
            {
                IntersectsFrustum = intersectsFrustum;
                HasUnoccludedSample = hasUnoccludedSample;
                GeometricallyVisible = geometricallyVisible;
                VisibleSampleFraction = visibleSampleFraction;
                GroundTruthBox = groundTruthBox;
                BoundingBoxAreaPixels = boundingBoxAreaPixels;
                CenterErrorPixels = centerErrorPixels;
            }
        }

        internal readonly struct AggregationSnapshot
        {
            public readonly float TotalDuration;
            public readonly float GeometricDuration;
            public readonly float TrackingDuration;
            public readonly float CGeom;
            public readonly float CTrack;
            public readonly float CTrackGivenGeom;
            public readonly int SensorFrames;
            public readonly int MatchedObservations;
            public readonly int UnmatchedObservations;
            public readonly int IncorrectObservations;
            public readonly int PendingFrames;

            public AggregationSnapshot(
                float totalDuration,
                float geometricDuration,
                float trackingDuration,
                int sensorFrames,
                int matchedObservations,
                int unmatchedObservations,
                int incorrectObservations,
                int pendingFrames)
            {
                TotalDuration = totalDuration;
                GeometricDuration = geometricDuration;
                TrackingDuration = trackingDuration;
                CGeom = geometricDuration / Mathf.Max(totalDuration, Mathf.Epsilon);
                CTrack = trackingDuration / Mathf.Max(totalDuration, Mathf.Epsilon);
                CTrackGivenGeom = trackingDuration
                    / Mathf.Max(geometricDuration, Mathf.Epsilon);
                SensorFrames = sensorFrames;
                MatchedObservations = matchedObservations;
                UnmatchedObservations = unmatchedObservations;
                IncorrectObservations = incorrectObservations;
                PendingFrames = pendingFrames;
            }
        }

        readonly Dictionary<long, FrameRecord> pendingFrames = new();
        readonly Queue<long> pendingFrameOrder = new();

        SensorFrameWriter frameWriter;
        TrackingObservationReceiver observationReceiver;
        Renderer[] targetRenderers;
        RateStudyDistractor[] scoutingDistractors =
            Array.Empty<RateStudyDistractor>();
        IScoutingTruthSession scoutingSession;
        P1DetectScoutingTruthWriter scoutingTruthWriter;
        P1DetectScoutingGimbalDriver scoutingGimbalDriver;
        QualificationReleaseGate qualificationReleaseGate;
        StreamWriter rate3TruthWriter;
        StreamWriter m3TruthWriter;
        ScenarioConfig config;
        // P1-EVAL-001: bound once from config before the first evaluation
        // frame; never follows Game view, Screen or post-targetTexture
        // camera state.
        float evaluationAspect;
        CurrentMetrics current = new();
        float writeTimer;
        float totalDuration;
        float geometricDuration;
        float trackingDuration;
        float visibleFractionIntegral;
        float visibleAreaIntegral;
        float visibleCenterErrorSquaredIntegral;
        int sensorFrames;
        int matchedObservations;
        int unmatchedObservations;
        int incorrectObservations;

        void Start()
        {
            TetheredScenarioBootstrap scenario = TetheredScenarioBootstrap.Instance;
            if (scenario == null) return;
            config = scenario.Config;
            evaluationAspect = SensorAspectOrThrow(config);
            qualificationReleaseGate = new QualificationReleaseGate(
                RuntimePaths.Root,
                config.scenario_id);
            frameWriter = scenario.FrameWriter;
            observationReceiver = scenario.ObservationReceiver;
            targetRenderers = scenario.Target.GetComponentsInChildren<Renderer>();
            ConfigureScouting(scenario);
            if (frameWriter != null) frameWriter.FramePublished += OnFramePublished;
            if (observationReceiver != null) observationReceiver.ObservationReceived += OnObservationReceived;
        }

        void OnDestroy()
        {
            if (frameWriter != null) frameWriter.FramePublished -= OnFramePublished;
            if (observationReceiver != null) observationReceiver.ObservationReceived -= OnObservationReceived;
            CloseRate3TruthWriter();
            CloseM3TruthWriter();
        }

        void OnApplicationQuit()
        {
            CloseRate3TruthWriter();
            CloseM3TruthWriter();
        }

        void CloseRate3TruthWriter()
        {
            if (rate3TruthWriter == null) return;
            try
            {
                rate3TruthWriter.Flush();
                rate3TruthWriter.Dispose();
            }
            finally
            {
                rate3TruthWriter = null;
            }
        }

        void CloseM3TruthWriter()
        {
            if (m3TruthWriter == null) return;
            try
            {
                m3TruthWriter.Flush();
                m3TruthWriter.Dispose();
            }
            finally
            {
                m3TruthWriter = null;
            }
        }

        void Update()
        {
            scoutingGimbalDriver?.UpdateTarget();
            writeTimer += Time.deltaTime;
            if (writeTimer < 1f) return;
            writeTimer -= 1f;
            WriteMetrics();
        }

        void OnFramePublished(SensorFrameInfo frame)
        {
            TetheredScenarioBootstrap scenario = TetheredScenarioBootstrap.Instance;
            if (scenario == null || config == null) return;
            QualificationFrameDisposition qualificationDisposition =
                qualificationReleaseGate == null
                    ? QualificationFrameDisposition.Ordinary
                    : qualificationReleaseGate.EvaluateFrame(frame);
            if (scenario.ExperimentController != null
                && scenario.ExperimentController.IsActive
                && qualificationDisposition
                    != QualificationFrameDisposition.Ordinary)
                throw new InvalidOperationException(
                    "multiple_release_protocols_are_active");
            if (!MeasurementFrameAllowed(
                scenario.ExperimentController,
                frame.FrameId)) return;
            bool qualificationFrameAllowed =
                ApplyQualificationDisposition(qualificationDisposition);
            if (!qualificationFrameAllowed)
            {
                WriteMetrics();
                return;
            }
            VisibilitySnapshot snapshot = EvaluateVisibility(
                scenario.SensorCamera, scenario.Target.transform, targetRenderers);
            WriteScoutingTruth(scenario, frame, snapshot);
            WriteRate3EvaluationTruth(scenario, frame, snapshot);
            WriteM3BodyTruth(scenario, frame, snapshot, qualificationDisposition);
            RecordFrame(frame, snapshot);
            if (RequiresImmediateMetricsWrite(
                scenario.ExperimentController,
                frame.FrameId)
                || qualificationDisposition
                    == QualificationFrameDisposition.ResetAndMeasure)
            {
                // RATE-002 copies metrics.json as soon as its tracker reaches
                // the release-origin cutoff. A one-second publication timer
                // can therefore expose a stale pre-cutoff document even when
                // the in-memory aggregation is current.
                writeTimer = 0f;
                WriteMetrics();
            }
        }

        void ConfigureScouting(TetheredScenarioBootstrap scenario)
        {
            string legacyPath = RuntimePaths.File(
                "p1_detect_scouting_session.json");
            string scene004Path = RuntimePaths.File(
                P1Scene004ScoutingSession.FileName);
            bool hasLegacy = P1DetectScoutingSession.TryLoad(
                legacyPath,
                out P1DetectScoutingSession legacySession,
                out string legacyError);
            bool hasScene004 = P1Scene004ScoutingSession.TryLoad(
                scene004Path,
                out P1Scene004ScoutingSession scene004Session,
                out string scene004Error);
            // Two active scouting profiles would make the capture's identity
            // ambiguous; fail closed rather than pick one.
            if (hasLegacy && hasScene004)
                throw new InvalidOperationException(
                    "multiple_active_scouting_sessions");
            if (!hasLegacy && !hasScene004) return;
            string error = hasLegacy ? legacyError : scene004Error;
            IScoutingTruthSession loaded = hasLegacy
                ? (IScoutingTruthSession)legacySession
                : scene004Session;
            if (error != null)
                throw new InvalidOperationException(error);
            if (scenario.ExperimentController != null
                && scenario.ExperimentController.IsActive)
                throw new InvalidOperationException(
                    "scouting_session_must_be_non_measurement");
            if (config.scenario_id != loaded.ScenarioId)
                throw new InvalidOperationException(
                    "scouting_scenario_identity_mismatch");
            if (!File.Exists(config.source_path)
                || RateStudyProtocol.Sha256(
                    File.ReadAllBytes(config.source_path))
                != loaded.ScenarioConfigSha256)
                throw new InvalidOperationException(
                    "scouting_scenario_hash_mismatch");

            scoutingSession = loaded;
            scoutingDistractors = FindObjectsByType<RateStudyDistractor>();
            Array.Sort(
                scoutingDistractors,
                (left, right) => string.CompareOrdinal(
                    StableObjectId(left.transform),
                    StableObjectId(right.transform)));
            int expected = config.scene_adjustments == null
                ? 0
                : config.scene_adjustments.expected_distractor_count;
            if (scoutingDistractors.Length != expected)
                throw new InvalidOperationException(
                    "scouting_distractor_count_mismatch");
            for (int index = 1; index < scoutingDistractors.Length; index++)
            {
                if (StableObjectId(scoutingDistractors[index - 1].transform)
                    == StableObjectId(scoutingDistractors[index].transform))
                    throw new InvalidOperationException(
                        "scouting_distractor_identity_collision");
            }
            scoutingTruthWriter = new P1DetectScoutingTruthWriter(
                loaded,
                RuntimePaths.Root);
            ConfigureScoutingGimbal(
                loaded,
                scenario.Gimbal,
                scenario.Target.transform,
                scenario.GetComponent<GimbalCommandReceiver>());
        }

        internal void ConfigureScoutingGimbal(
            IScoutingTruthSession session,
            TetheredGimbal gimbal,
            Transform target,
            Behaviour externalCommandReceiver)
        {
            scoutingGimbalDriver = new P1DetectScoutingGimbalDriver();
            scoutingGimbalDriver.Configure(
                session,
                gimbal,
                target,
                externalCommandReceiver);
        }

        internal void UpdateScoutingGimbalForTests() =>
            scoutingGimbalDriver?.UpdateTarget();

        /// <summary>
        /// P1-M2-RATE-003 §5/§11 evaluation-domain truth stream.
        ///
        /// The inter-frame displacement probe and the measured lap period
        /// both need the projected truth-box centre and the target world
        /// position on the released measurement span. Ground truth may only
        /// ever be produced inside this evaluator, so the stream is written
        /// here, to an offline analysis sidecar that no controller,
        /// perception input or outbound sensor metadata reads. The offline
        /// RATE-003 orchestrator is the only consumer; it collects the file
        /// into the run directory at finalize time.
        ///
        /// It is written only for an active RATE-003 (`p1-rate3-session/v1`)
        /// session and only for frames that already passed the release gate,
        /// so ordinary runs, RATE-002 replays and HOLD frames produce
        /// nothing at all.
        /// </summary>
        void WriteRate3EvaluationTruth(
            TetheredScenarioBootstrap scenario,
            SensorFrameInfo frame,
            VisibilitySnapshot snapshot)
        {
            RateStudyExperimentController experiment = scenario.ExperimentController;
            if (experiment == null
                || !experiment.IsActive
                || !experiment.UsesSharedHostClock
                || experiment.State != RateStudyExperimentState.Released
                || experiment.Session == null) return;
            Vector3 position = scenario.Target.transform.position;
            NormalizedBoundingBox box = snapshot.GroundTruthBox;
            var record = new Rate3EvaluationTruthRecord
            {
                study_id = experiment.Session.study_id,
                run_id = experiment.Session.run_id,
                frame_id = frame.FrameId,
                release_frame_id = experiment.ReleaseFrameId,
                simulation_time_s = frame.SimulationTimeSeconds,
                capture_monotonic_s = frame.CaptureMonotonicSeconds,
                capture_monotonic_clock_id = RateStudyProtocol.SharedHostClockId,
                geometrically_visible = snapshot.GeometricallyVisible,
                truth_box_available = box != null,
                truth_box_x = box == null ? -1f : box.x,
                truth_box_y = box == null ? -1f : box.y,
                truth_box_width = box == null ? -1f : box.width,
                truth_box_height = box == null ? -1f : box.height,
                truth_center_x_px = box == null
                    ? -1f
                    : (box.x + box.width * 0.5f) * config.sensor.width,
                truth_center_y_px = box == null
                    ? -1f
                    : (box.y + box.height * 0.5f) * config.sensor.height,
                target_world_x_m = position.x,
                target_world_z_m = position.z,
            };
            if (rate3TruthWriter == null)
            {
                rate3TruthWriter = new StreamWriter(
                    new FileStream(
                        RuntimePaths.File(Rate3EvaluationTruthFileName),
                        FileMode.Append,
                        FileAccess.Write,
                        FileShare.Read));
            }
            rate3TruthWriter.WriteLine(JsonUtility.ToJson(record));
            rate3TruthWriter.Flush();
        }

        /// <summary>
        /// Only ordinary frames of an ordinary run carry M3 truth: any
        /// active experiment (RATE) or any non-ordinary qualification
        /// disposition already owns its own truth/measurement contract, so
        /// those frames produce nothing here.
        /// </summary>
        internal static bool M3BodyTruthAllowed(
            RateStudyExperimentController experiment,
            QualificationFrameDisposition qualificationDisposition)
        {
            if (experiment != null && experiment.IsActive) return false;
            return qualificationDisposition
                == QualificationFrameDisposition.Ordinary;
        }

        internal static M3BodyTruthRecord BuildM3BodyTruthRecord(
            string scenarioId,
            SensorFrameInfo frame,
            Vector3 targetPosition,
            Vector3 bodyPosition,
            Vector3 appliedVelocity,
            VisibilitySnapshot snapshot,
            bool gimbalSaturated,
            bool tetherSaturated,
            float sensorWidth,
            float sensorHeight,
            float evaluationAspect)
        {
            NormalizedBoundingBox box = snapshot.GroundTruthBox;
            var record = new M3BodyTruthRecord
            {
                scenario_id = scenarioId,
                frame_id = frame.FrameId,
                simulation_time_s = frame.SimulationTimeSeconds,
                capture_monotonic_s = frame.CaptureMonotonicSeconds,
                capture_monotonic_clock_id = RateStudyProtocol.SharedHostClockId,
                target_world_x_m = targetPosition.x,
                target_world_y_m = targetPosition.y,
                target_world_z_m = targetPosition.z,
                body_world_x_m = bodyPosition.x,
                body_world_y_m = bodyPosition.y,
                body_world_z_m = bodyPosition.z,
                applied_velocity_x_mps = appliedVelocity.x,
                applied_velocity_y_mps = appliedVelocity.y,
                applied_velocity_z_mps = appliedVelocity.z,
                intersects_frustum = snapshot.IntersectsFrustum,
                has_unoccluded_sample = snapshot.HasUnoccludedSample,
                geometrically_visible = snapshot.GeometricallyVisible,
                visible_sample_fraction = snapshot.VisibleSampleFraction,
                truth_box_available = box != null,
                truth_box_x = box == null ? -1f : box.x,
                truth_box_y = box == null ? -1f : box.y,
                truth_box_width = box == null ? -1f : box.width,
                truth_box_height = box == null ? -1f : box.height,
                truth_center_x_px = box == null
                    ? -1f
                    : (box.x + box.width * 0.5f) * sensorWidth,
                truth_center_y_px = box == null
                    ? -1f
                    : (box.y + box.height * 0.5f) * sensorHeight,
                target_bbox_area_px = snapshot.BoundingBoxAreaPixels,
                target_center_error_px = snapshot.CenterErrorPixels,
                gimbal_saturated = gimbalSaturated,
                tether_saturated = tetherSaturated,
                evaluation_aspect_width_over_height = evaluationAspect,
            };
            if (!float.IsFinite(record.target_world_x_m)
                || !float.IsFinite(record.target_world_y_m)
                || !float.IsFinite(record.target_world_z_m)
                || !float.IsFinite(record.body_world_x_m)
                || !float.IsFinite(record.body_world_y_m)
                || !float.IsFinite(record.body_world_z_m)
                || !float.IsFinite(record.applied_velocity_x_mps)
                || !float.IsFinite(record.applied_velocity_y_mps)
                || !float.IsFinite(record.applied_velocity_z_mps)
                || !float.IsFinite(record.visible_sample_fraction)
                || !float.IsFinite(record.truth_box_x)
                || !float.IsFinite(record.truth_box_y)
                || !float.IsFinite(record.truth_box_width)
                || !float.IsFinite(record.truth_box_height)
                || !float.IsFinite(record.truth_center_x_px)
                || !float.IsFinite(record.truth_center_y_px)
                || !float.IsFinite(record.target_bbox_area_px)
                || !float.IsFinite(record.target_center_error_px)
                || !float.IsFinite(record.evaluation_aspect_width_over_height)
                || !float.IsFinite(record.simulation_time_s)
                || !double.IsFinite(record.capture_monotonic_s))
            {
                throw new InvalidOperationException(
                    "m3_body_truth_non_finite");
            }
            return record;
        }

        /// <summary>
        /// P1-M3-BODY-001 batch 1c offline truth carrier. One JSONL line per
        /// evaluated sensor frame, truncated once per Play (the writer lives
        /// and dies with this component), so the file always holds exactly
        /// the current Play's frames. Ground truth may only ever be produced
        /// inside this evaluator; the file is an offline analysis sidecar
        /// that no controller, perception input or outbound sensor metadata
        /// reads. The only consumer is tools/analyze_m3_body.py, which binds
        /// it to the run after the Play.
        /// </summary>
        void WriteM3BodyTruth(
            TetheredScenarioBootstrap scenario,
            SensorFrameInfo frame,
            VisibilitySnapshot snapshot,
            QualificationFrameDisposition qualificationDisposition)
        {
            if (!M3BodyTruthAllowed(
                scenario.ExperimentController,
                qualificationDisposition)) return;
            M3BodyTruthRecord record = BuildM3BodyTruthRecord(
                config.scenario_id,
                frame,
                scenario.Target.transform.position,
                scenario.Drone.transform.position,
                scenario.Drone.AppliedVelocity,
                snapshot,
                scenario.Gimbal.Saturated,
                scenario.Drone.TetherSaturated,
                config.sensor.width,
                config.sensor.height,
                evaluationAspect);
            if (m3TruthWriter == null)
            {
                m3TruthWriter = new StreamWriter(
                    new FileStream(
                        RuntimePaths.File(M3BodyTruthFileName),
                        FileMode.Create,
                        FileAccess.Write,
                        FileShare.Read));
            }
            m3TruthWriter.WriteLine(JsonUtility.ToJson(record));
            m3TruthWriter.Flush();
        }

        void WriteScoutingTruth(
            TetheredScenarioBootstrap scenario,
            SensorFrameInfo frame,
            VisibilitySnapshot snapshot)
        {
            if (scoutingTruthWriter == null) return;
            Camera camera = scenario.SensorCamera;
            Transform target = scenario.Target.transform;
            var distractors = new P1DetectScoutingDistractorTruth[
                scoutingDistractors.Length];
            for (int index = 0; index < scoutingDistractors.Length; index++)
            {
                RateStudyDistractor marker = scoutingDistractors[index];
                distractors[index] = new P1DetectScoutingDistractorTruth
                {
                    distractor_id = StableObjectId(marker.transform),
                    bbox_xywh_norm = ProjectRenderers(
                        camera,
                        marker.GetComponentsInChildren<Renderer>(),
                        evaluationAspect),
                };
            }
            scoutingTruthWriter.Write(new P1DetectScoutingTruthDocument
            {
                work_id = scoutingSession.WorkId,
                session_id = scoutingSession.SessionId,
                scenario_id = scoutingSession.ScenarioId,
                gimbal_driver = scoutingSession.GimbalDriver,
                frame_id = frame.FrameId,
                simulation_time_s = frame.SimulationTimeSeconds,
                target_track_id = scenario.Target.trackId,
                target_visible = snapshot.GeometricallyVisible,
                target_visible_sample_fraction =
                    snapshot.VisibleSampleFraction,
                target_slant_range_m = Vector3.Distance(
                    camera.transform.position,
                    target.position),
                target_bbox_xywh_norm = snapshot.GroundTruthBox,
                distractors = distractors,
            });
        }

        internal static NormalizedBoundingBox ProjectRenderers(
            Camera camera,
            Renderer[] renderers,
            float sensorAspect)
        {
            if (camera == null || renderers == null || renderers.Length == 0)
                return null;
            Bounds bounds = renderers[0].bounds;
            for (int index = 1; index < renderers.Length; index++)
                bounds.Encapsulate(renderers[index].bounds);
            return ProjectBounds(camera, BoundsCorners(bounds), sensorAspect);
        }

        internal static string StableObjectId(Transform transform)
        {
            if (transform == null) return null;
            string value = transform.name;
            Transform parent = transform.parent;
            while (parent != null)
            {
                value = parent.name + "/" + value;
                parent = parent.parent;
            }
            return value;
        }

        void RecordFrame(SensorFrameInfo frame, VisibilitySnapshot snapshot)
        {
            float weight = frame.DeltaSimulationSeconds > 0f
                ? frame.DeltaSimulationSeconds
                : 1f / config.sensor.capture_hz;

            totalDuration += weight;
            sensorFrames++;
            visibleFractionIntegral += snapshot.VisibleSampleFraction * weight;
            if (snapshot.GeometricallyVisible)
            {
                geometricDuration += weight;
                visibleAreaIntegral += snapshot.BoundingBoxAreaPixels * weight;
                visibleCenterErrorSquaredIntegral += snapshot.CenterErrorPixels
                    * snapshot.CenterErrorPixels * weight;
            }
            var record = new FrameRecord
            {
                FrameId = frame.FrameId,
                WeightSeconds = weight,
                GeometricallyVisible = snapshot.GeometricallyVisible,
                GroundTruthBox = snapshot.GroundTruthBox,
            };
            pendingFrames[frame.FrameId] = record;
            pendingFrameOrder.Enqueue(frame.FrameId);
            PrunePendingFrames();

            current = new CurrentMetrics
            {
                frame_id = frame.FrameId,
                target_intersects_frustum = snapshot.IntersectsFrustum,
                target_unoccluded = snapshot.HasUnoccludedSample,
                c_geom = snapshot.GeometricallyVisible,
                visible_sample_fraction = snapshot.VisibleSampleFraction,
                target_bbox_area_px = snapshot.BoundingBoxAreaPixels,
                target_center_error_px = snapshot.CenterErrorPixels,
            };
        }

        void OnObservationReceived(TrackingObservation observation)
        {
            TetheredScenarioBootstrap scenario = TetheredScenarioBootstrap.Instance;
            if (scenario == null) return;
            if (!MeasurementFrameAllowed(
                scenario.ExperimentController,
                observation.FrameId)) return;
            if (qualificationReleaseGate != null
                && !qualificationReleaseGate.AllowsObservation(
                    observation.FrameId)) return;
            RecordObservation(observation, scenario.Target.trackId);
        }

        void RecordObservation(
            TrackingObservation observation,
            string expectedTrackId)
        {
            if (!pendingFrames.TryGetValue(observation.FrameId, out FrameRecord record))
            {
                unmatchedObservations++;
                return;
            }
            if (record.ObservationProcessed) return;
            record.ObservationProcessed = true;
            matchedObservations++;

            float iou = IntersectionOverUnion(record.GroundTruthBox, observation.Box);
            bool correctIdentity = observation.TrackId == expectedTrackId;
            bool success = record.GeometricallyVisible && correctIdentity
                && iou >= config.evaluation.tracking_iou_threshold;
            if (success) trackingDuration += record.WeightSeconds;
            else incorrectObservations++;

            if (current.frame_id == observation.FrameId)
            {
                current.tracking_observation_received = true;
                current.tracking_iou = iou;
                current.tracking_success = success;
            }
        }

        internal void ConfigureAggregationForTests(
            float captureHz,
            int maximumPendingFrameCount,
            float trackingIouThreshold)
        {
            config = ScenarioConfig.CreateDefault();
            config.sensor.capture_hz = captureHz;
            config.evaluation.maximum_pending_frame_count = maximumPendingFrameCount;
            config.evaluation.tracking_iou_threshold = trackingIouThreshold;
            config.Normalize();
            evaluationAspect = SensorAspectOrThrow(config);
        }

        /// <summary>
        /// P1-EVAL-001: the single source of the evaluation projection
        /// aspect — config.sensor.width / (float) config.sensor.height
        /// (640/480 for the default scenario). Non-positive sensor
        /// dimensions fail closed here even though ScenarioConfig.Normalize
        /// already clamps them into [64, 4096]: a truth projection must
        /// never silently fall back to the camera's current aspect.
        /// </summary>
        internal static float SensorAspectOrThrow(ScenarioConfig config)
        {
            if (config == null
                || config.sensor == null
                || config.sensor.width <= 0
                || config.sensor.height <= 0)
                throw new InvalidOperationException(
                    "evaluation_sensor_dimensions_invalid");
            return config.sensor.width / (float)config.sensor.height;
        }

        /// <summary>
        /// P1-EVAL-001: Camera.WorldToViewportPoint with the aspect pinned
        /// to the sensor capture aspect instead of the camera's current
        /// aspect (Game view / Screen state after SensorFrameWriter clears
        /// targetTexture). Reproduces the perspective, vertical-fieldOfView,
        /// non-physical projection the runtime SensorCamera uses; camera
        /// state is never read beyond transform/fieldOfView and never
        /// modified. Callers gate on z &gt; 0 exactly as with
        /// WorldToViewportPoint.
        /// </summary>
        internal static Vector3 WorldToSensorViewportPoint(
            Camera camera,
            Vector3 worldPoint,
            float sensorAspect)
        {
            // worldToCameraMatrix follows the OpenGL convention: points in
            // front of the camera have NEGATIVE z (and x/y otherwise match
            // Unity camera space). Negate z to recover Unity's
            // forward-is-positive-Z camera space that WorldToViewportPoint
            // reports.
            Vector3 cameraSpace =
                camera.worldToCameraMatrix.MultiplyPoint(worldPoint);
            float forward = -cameraSpace.z;
            float tanHalfVerticalFov = Mathf.Tan(
                0.5f * camera.fieldOfView * Mathf.Deg2Rad);
            float normalizedX = cameraSpace.x
                / (forward * tanHalfVerticalFov * sensorAspect);
            float normalizedY = cameraSpace.y
                / (forward * tanHalfVerticalFov);
            return new Vector3(
                0.5f + 0.5f * normalizedX,
                0.5f + 0.5f * normalizedY,
                forward);
        }

        internal void RecordAggregationFrameForTests(
            long frameId,
            float simulationTimeSeconds,
            float deltaSimulationSeconds,
            bool geometricallyVisible,
            NormalizedBoundingBox groundTruthBox)
        {
            RecordFrame(
                new SensorFrameInfo(
                    frameId,
                    simulationTimeSeconds,
                    deltaSimulationSeconds,
                    0.0,
                    0.0),
                new VisibilitySnapshot(
                    geometricallyVisible,
                    geometricallyVisible,
                    geometricallyVisible,
                    geometricallyVisible ? 1f : 0f,
                    groundTruthBox,
                    groundTruthBox == null ? 0f : groundTruthBox.width * groundTruthBox.height,
                    0f));
        }

        internal void RecordGatedAggregationFrameForTests(
            RateStudyExperimentController experiment,
            long frameId,
            float simulationTimeSeconds,
            float deltaSimulationSeconds,
            bool geometricallyVisible,
            NormalizedBoundingBox groundTruthBox)
        {
            if (!MeasurementFrameAllowed(experiment, frameId)) return;
            RecordAggregationFrameForTests(
                frameId,
                simulationTimeSeconds,
                deltaSimulationSeconds,
                geometricallyVisible,
                groundTruthBox);
        }

        internal static bool MeasurementFrameAllowed(
            RateStudyExperimentController experiment,
            long frameId) =>
            experiment == null || experiment.AcceptsMeasurementFrame(frameId);

        internal static bool RequiresImmediateMetricsWrite(
            RateStudyExperimentController experiment,
            long frameId) =>
            experiment != null
            && experiment.IsActive
            && MeasurementFrameAllowed(experiment, frameId);

        internal void RecordAggregationObservationForTests(
            TrackingObservation observation,
            string expectedTrackId)
        {
            RecordObservation(observation, expectedTrackId);
        }

        internal AggregationSnapshot AggregationForTests()
        {
            return new AggregationSnapshot(
                totalDuration,
                geometricDuration,
                trackingDuration,
                sensorFrames,
                matchedObservations,
                unmatchedObservations,
                incorrectObservations,
                pendingFrames.Count);
        }

        void ResetAggregation()
        {
            pendingFrames.Clear();
            pendingFrameOrder.Clear();
            current = new CurrentMetrics();
            totalDuration = 0f;
            geometricDuration = 0f;
            trackingDuration = 0f;
            visibleFractionIntegral = 0f;
            visibleAreaIntegral = 0f;
            visibleCenterErrorSquaredIntegral = 0f;
            sensorFrames = 0;
            matchedObservations = 0;
            unmatchedObservations = 0;
            incorrectObservations = 0;
        }

        internal bool ApplyQualificationDisposition(
            QualificationFrameDisposition disposition)
        {
            if (disposition == QualificationFrameDisposition.ResetAndHold
                || disposition
                    == QualificationFrameDisposition.ResetAndMeasure)
            {
                ResetAggregation();
                writeTimer = 0f;
            }
            return disposition
                    != QualificationFrameDisposition.ResetAndHold
                && disposition != QualificationFrameDisposition.Hold;
        }

        internal bool HasPendingFrameForTests(long frameId)
        {
            return pendingFrames.ContainsKey(frameId);
        }

        VisibilitySnapshot EvaluateVisibility(Camera camera, Transform target, Renderer[] renderers)
        {
            if (camera == null || target == null || renderers == null || renderers.Length == 0)
                return new VisibilitySnapshot(false, false, false, 0f, null, 0f, 0f);

            Bounds bounds = renderers[0].bounds;
            for (int index = 1; index < renderers.Length; index++) bounds.Encapsulate(renderers[index].bounds);
            Vector3[] corners = BoundsCorners(bounds);
            Vector3[] samples = VisibilitySamples(bounds, corners);
            int inFrustumCount = 0;
            int visibleCount = 0;
            foreach (Vector3 point in samples)
            {
                Vector3 viewport = WorldToSensorViewportPoint(
                    camera, point, evaluationAspect);
                bool inFrustum = viewport.z > 0f && viewport.x >= 0f && viewport.x <= 1f
                    && viewport.y >= 0f && viewport.y <= 1f;
                if (!inFrustum) continue;
                inFrustumCount++;
                if (HasClearLineOfSight(camera.transform.position, point, target)) visibleCount++;
            }

            float visibleFraction = visibleCount / (float)samples.Length;
            bool geometricallyVisible = visibleFraction >= config.evaluation.minimum_visible_sample_fraction;
            NormalizedBoundingBox box = ProjectBounds(camera, corners, evaluationAspect);
            float areaPixels = box == null ? 0f
                : box.width * box.height * config.sensor.width * config.sensor.height;
            float centerError = box == null ? 0f : Mathf.Sqrt(
                Mathf.Pow((box.x + box.width * 0.5f - 0.5f) * config.sensor.width, 2f)
                + Mathf.Pow((box.y + box.height * 0.5f - 0.5f) * config.sensor.height, 2f));
            return new VisibilitySnapshot(
                inFrustumCount > 0,
                visibleCount > 0,
                geometricallyVisible,
                visibleFraction,
                box,
                areaPixels,
                centerError);
        }

        static bool HasClearLineOfSight(Vector3 origin, Vector3 point, Transform target)
        {
            Vector3 delta = point - origin;
            float distance = delta.magnitude;
            if (distance <= 0.05f) return true;
            RaycastHit[] hits = Physics.RaycastAll(
                origin, delta / distance, distance - 0.05f, ~0, QueryTriggerInteraction.Ignore);
            foreach (RaycastHit hit in hits)
            {
                if (hit.transform == target || hit.transform.IsChildOf(target)) continue;
                return false;
            }
            return true;
        }

        internal static NormalizedBoundingBox ProjectBounds(
            Camera camera,
            Vector3[] corners,
            float sensorAspect)
        {
            float minX = float.PositiveInfinity;
            float minY = float.PositiveInfinity;
            float maxX = float.NegativeInfinity;
            float maxY = float.NegativeInfinity;
            bool hasFrontPoint = false;
            foreach (Vector3 corner in corners)
            {
                Vector3 viewport = WorldToSensorViewportPoint(
                    camera, corner, sensorAspect);
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
            if (clippedMaxX <= clippedMinX || clippedMaxY <= clippedMinY) return null;
            return new NormalizedBoundingBox
            {
                x = clippedMinX,
                y = 1f - clippedMaxY,
                width = clippedMaxX - clippedMinX,
                height = clippedMaxY - clippedMinY,
            };
        }

        internal static Vector3[] BoundsCorners(Bounds bounds)
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

        internal static Vector3[] VisibilitySamples(Bounds bounds, Vector3[] corners)
        {
            Vector3 center = bounds.center;
            Vector3 extents = bounds.extents;
            var samples = new Vector3[15];
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

        internal static float IntersectionOverUnion(
            NormalizedBoundingBox first,
            NormalizedBoundingBox second)
        {
            if (first == null || second == null) return 0f;
            float firstX2 = first.x + first.width;
            float firstY2 = first.y + first.height;
            float secondX2 = second.x + second.width;
            float secondY2 = second.y + second.height;
            float intersectionWidth = Mathf.Max(0f, Mathf.Min(firstX2, secondX2) - Mathf.Max(first.x, second.x));
            float intersectionHeight = Mathf.Max(0f, Mathf.Min(firstY2, secondY2) - Mathf.Max(first.y, second.y));
            float intersection = intersectionWidth * intersectionHeight;
            float union = first.width * first.height + second.width * second.height - intersection;
            return union > 0f ? intersection / union : 0f;
        }

        void PrunePendingFrames()
        {
            while (pendingFrameOrder.Count > config.evaluation.maximum_pending_frame_count)
            {
                long expired = pendingFrameOrder.Dequeue();
                pendingFrames.Remove(expired);
            }
        }

        void WriteMetrics()
        {
            TetheredScenarioBootstrap scenario = TetheredScenarioBootstrap.Instance;
            if (scenario == null || config == null) return;
            MetricsDocument document = BuildMetricsDocument(
                scenario.OcclusionGeometry,
                scenario.Gimbal.Saturated,
                scenario.Drone.TetherSaturated);
            AtomicFile.WriteAllText(
                RuntimePaths.File("metrics.json"), JsonUtility.ToJson(document, true) + "\n");
        }

        MetricsDocument BuildMetricsDocument(
            EvaluationOcclusionGeometry geometry,
            bool gimbalSaturated,
            bool tetherSaturated)
        {
            float safeTotal = Mathf.Max(totalDuration, Mathf.Epsilon);
            float safeGeometric = Mathf.Max(geometricDuration, Mathf.Epsilon);
            return new MetricsDocument
            {
                scenario_id = config.scenario_id,
                elapsed_simulation_s = totalDuration,
                thresholds = new MetricThresholds
                {
                    minimum_visible_sample_fraction = config.evaluation.minimum_visible_sample_fraction,
                    tracking_iou = config.evaluation.tracking_iou_threshold,
                },
                current = current,
                qualification_release =
                    qualificationReleaseGate?.MetricsOrigin,
                aggregate = new AggregateMetrics
                {
                    c_geom = geometricDuration / safeTotal,
                    c_track = trackingDuration / safeTotal,
                    c_track_given_geom = trackingDuration / safeGeometric,
                    mean_visible_sample_fraction = visibleFractionIntegral / safeTotal,
                    mean_target_bbox_area_px_when_visible = visibleAreaIntegral / safeGeometric,
                    rms_target_center_error_px_when_visible = Mathf.Sqrt(
                        visibleCenterErrorSquaredIntegral / safeGeometric),
                    sensor_frames = sensorFrames,
                    matched_tracking_observations = matchedObservations,
                    unmatched_tracking_observations = unmatchedObservations,
                    incorrect_tracking_observations = incorrectObservations,
                },
                occlusion_geometry = new OcclusionGeometryDiagnostics
                {
                    candidate_renderers = geometry == null ? 0 : geometry.CandidateRendererCount,
                    mesh_collider_proxies = geometry == null ? 0 : geometry.ProxyColliderCount,
                    existing_colliders = geometry == null ? 0 : geometry.ExistingColliderCount,
                    failed_proxies = geometry == null ? 0 : geometry.FailedProxyCount,
                    excluded_renderers = geometry == null ? 0 : geometry.ExcludedRendererCount,
                    layer = geometry == null ? -1 : geometry.OcclusionLayer,
                    used_default_layer_fallback = geometry != null
                        && geometry.UsedDefaultLayerFallback,
                },
                gimbal_saturated = gimbalSaturated,
                tether_saturated = tetherSaturated,
                evaluation_projection = new EvaluationProjection
                {
                    sensor_width_px = config.sensor.width,
                    sensor_height_px = config.sensor.height,
                    aspect_width_over_height = evaluationAspect,
                },
            };
        }

        internal string MetricsJsonForTests() =>
            JsonUtility.ToJson(BuildMetricsDocument(null, false, false));

        void OnGUI()
        {
            float safeTotal = Mathf.Max(totalDuration, Mathf.Epsilon);
            float safeGeometric = Mathf.Max(geometricDuration, Mathf.Epsilon);
            GUI.Label(new Rect(10, 10, 620, 24),
                $"Tethered tracking | C_geom {geometricDuration / safeTotal:P1} | "
                + $"C_track {trackingDuration / safeTotal:P1} | "
                + $"C_track|geom {trackingDuration / safeGeometric:P1}");
        }
    }
}
