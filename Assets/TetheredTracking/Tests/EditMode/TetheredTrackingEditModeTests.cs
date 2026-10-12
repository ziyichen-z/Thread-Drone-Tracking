using System;
using System.IO;
using NUnit.Framework;
using UnityEngine;

namespace TetheredTracking.Tests
{
    public sealed class ScenarioConfigTests
    {
        [Test]
        public void Normalize_ReplacesNonFiniteValuesAndClampsLimits()
        {
            ScenarioConfig config = ScenarioConfig.CreateDefault();
            config.scenario_id = " ";
            config.anchor_world_m = new ScenarioVector3(
                float.NaN,
                float.PositiveInfinity,
                float.NegativeInfinity);
            config.drone.tether_length_m = 35f;
            config.drone.minimum_altitude_m = -1f;
            config.drone.maximum_altitude_m = 100f;
            config.drone.initial_altitude_m = float.NaN;
            config.drone.maximum_speed_mps = 0f;
            config.drone.maximum_acceleration_mps2 = float.PositiveInfinity;
            config.gimbal.maximum_off_nadir_deg = 100f;
            config.gimbal.slew_rate_deg_per_second = 0f;
            config.sensor.width = 1;
            config.sensor.height = 5000;
            config.sensor.vertical_fov_deg = float.NaN;
            config.sensor.capture_hz = float.PositiveInfinity;
            config.sensor.jpeg_quality = 0;
            config.sensor.retained_frame_count = 1;
            config.target.track_id = "";
            config.target.speed_mps = -3f;
            config.target.route_world_m = new[]
            {
                null,
                new ScenarioVector3(
                    float.PositiveInfinity,
                    float.NaN,
                    float.NegativeInfinity),
            };
            config.evaluation.minimum_visible_sample_fraction = float.NaN;
            config.evaluation.tracking_iou_threshold = float.PositiveInfinity;
            config.evaluation.maximum_pending_frame_count = 1;

            config.Normalize();

            Assert.That(config.scenario_id, Is.EqualTo("deterministic-loop-default"));
            AssertVector(config.Anchor, new Vector3(132f, 0.2f, 117f));
            Assert.That(config.drone.minimum_altitude_m, Is.EqualTo(8f));
            Assert.That(config.drone.maximum_altitude_m, Is.EqualTo(35f));
            Assert.That(config.drone.initial_altitude_m, Is.EqualTo(25f));
            Assert.That(config.drone.maximum_speed_mps, Is.EqualTo(4f));
            Assert.That(config.drone.maximum_acceleration_mps2, Is.EqualTo(4f));
            Assert.That(config.gimbal.maximum_off_nadir_deg, Is.EqualTo(89f));
            Assert.That(config.gimbal.slew_rate_deg_per_second, Is.EqualTo(120f));
            Assert.That(config.sensor.width, Is.EqualTo(64));
            Assert.That(config.sensor.height, Is.EqualTo(4096));
            Assert.That(config.sensor.vertical_fov_deg, Is.EqualTo(60f));
            Assert.That(config.sensor.capture_hz, Is.EqualTo(5f));
            Assert.That(config.sensor.jpeg_quality, Is.EqualTo(1));
            Assert.That(config.sensor.retained_frame_count, Is.EqualTo(4));
            Assert.That(config.target.track_id, Is.EqualTo("target-0"));
            Assert.That(config.target.speed_mps, Is.Zero);
            AssertVector(
                config.target.route_world_m[0].Value,
                new Vector3(125.5f, 0.2f, 117.5f));
            AssertVector(
                config.target.route_world_m[1].Value,
                new Vector3(174.5f, 0.2f, 117.5f));
            Assert.That(config.evaluation.minimum_visible_sample_fraction, Is.EqualTo(0.2f));
            Assert.That(config.evaluation.tracking_iou_threshold, Is.EqualTo(0.3f));
            Assert.That(config.evaluation.maximum_pending_frame_count, Is.EqualTo(16));
        }

        [Test]
        public void Normalize_ReconstructsMissingNestedSectionsAndRoute()
        {
            var config = new ScenarioConfig
            {
                anchor_world_m = null,
                drone = null,
                gimbal = null,
                sensor = null,
                target = null,
                evaluation = null,
            };

            config.Normalize();

            Assert.That(config.anchor_world_m, Is.Not.Null);
            Assert.That(config.drone, Is.Not.Null);
            Assert.That(config.gimbal, Is.Not.Null);
            Assert.That(config.sensor, Is.Not.Null);
            Assert.That(config.target, Is.Not.Null);
            Assert.That(config.evaluation, Is.Not.Null);
            Assert.That(config.target.route_world_m, Has.Length.GreaterThanOrEqualTo(2));
        }

        static void AssertVector(Vector3 actual, Vector3 expected)
        {
            Assert.That(actual.x, Is.EqualTo(expected.x).Within(1e-6f));
            Assert.That(actual.y, Is.EqualTo(expected.y).Within(1e-6f));
            Assert.That(actual.z, Is.EqualTo(expected.z).Within(1e-6f));
        }
    }

    public sealed class CoverageMathTests
    {
        [Test]
        public void IntersectionOverUnion_HandlesIdenticalPartialAndDisjointBoxes()
        {
            var first = Box(0.1f, 0.1f, 0.4f, 0.4f);
            var partial = Box(0.3f, 0.3f, 0.4f, 0.4f);
            var disjoint = Box(0.6f, 0.6f, 0.2f, 0.2f);

            Assert.That(
                CoverageEvaluator.IntersectionOverUnion(first, first),
                Is.EqualTo(1f).Within(1e-6f));
            Assert.That(
                CoverageEvaluator.IntersectionOverUnion(first, partial),
                Is.EqualTo(1f / 7f).Within(1e-6f));
            Assert.That(
                CoverageEvaluator.IntersectionOverUnion(first, disjoint),
                Is.Zero);
            Assert.That(
                CoverageEvaluator.IntersectionOverUnion(null, first),
                Is.Zero);
        }

        [Test]
        public void ProjectBounds_UsesNormalizedTopLeftOrigin()
        {
            GameObject cameraObject = new GameObject("ProjectionTestCamera");
            try
            {
                Camera camera = cameraObject.AddComponent<Camera>();
                camera.enabled = false;
                camera.fieldOfView = 60f;
                camera.aspect = 1f;
                camera.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
                Vector3 lowerLeft = new Vector3(-1f, -2f, 10f);
                Vector3 upperRight = new Vector3(1f, 3f, 10f);

                NormalizedBoundingBox box = CoverageEvaluator.ProjectBounds(
                    camera,
                    new[] { lowerLeft, upperRight },
                    1f);
                Vector3 lowerViewport = camera.WorldToViewportPoint(lowerLeft);
                Vector3 upperViewport = camera.WorldToViewportPoint(upperRight);

                Assert.That(box, Is.Not.Null);
                Assert.That(box.x, Is.EqualTo(lowerViewport.x).Within(1e-5f));
                Assert.That(box.y, Is.EqualTo(1f - upperViewport.y).Within(1e-5f));
                Assert.That(
                    box.width,
                    Is.EqualTo(upperViewport.x - lowerViewport.x).Within(1e-5f));
                Assert.That(
                    box.height,
                    Is.EqualTo(upperViewport.y - lowerViewport.y).Within(1e-5f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(cameraObject);
            }
        }

        [Test]
        public void SensorProjection_MatchesUnityOracleAtPinnedAspect()
        {
            // P1-EVAL-001: with the camera aspect deliberately mismatched to
            // the non-square sensor aspect, the pinned projection must
            // reproduce the viewport Unity computes when the camera aspect
            // actually equals the sensor aspect, and must ignore the
            // camera's current aspect.
            GameObject cameraObject = new GameObject("PinnedAspectOracleCamera");
            try
            {
                Camera camera = cameraObject.AddComponent<Camera>();
                camera.enabled = false;
                camera.fieldOfView = 60f;
                camera.aspect = 16f / 9f;
                camera.transform.SetPositionAndRotation(
                    new Vector3(3f, 5f, -2f), Quaternion.Euler(35f, -20f, 10f));
                const float sensorAspect = 640f / 480f;
                Vector3[] points =
                {
                    new Vector3(0f, 0f, 10f),
                    new Vector3(5f, -3f, 8f),
                    new Vector3(-7f, 4f, 25f),
                };
                foreach (Vector3 point in points)
                {
                    Vector3 pinned = CoverageEvaluator.WorldToSensorViewportPoint(
                        camera, point, sensorAspect);
                    camera.aspect = sensorAspect;
                    Vector3 oracle = camera.WorldToViewportPoint(point);
                    camera.aspect = 16f / 9f;
                    Vector3 mismatched = camera.WorldToViewportPoint(point);
                    Assert.That(pinned.x, Is.EqualTo(oracle.x).Within(1e-5f));
                    Assert.That(pinned.y, Is.EqualTo(oracle.y).Within(1e-5f));
                    Assert.That(pinned.z, Is.EqualTo(oracle.z).Within(1e-5f));
                    // The vertical frustum is aspect-independent (fixed
                    // vertical FOV); the horizontal one is not.
                    Assert.That(pinned.y, Is.EqualTo(mismatched.y).Within(1e-5f));
                    Assert.That(
                        pinned.x, Is.Not.EqualTo(mismatched.x).Within(1e-4f));
                }
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(cameraObject);
            }
        }

        [Test]
        public void SensorProjection_FalsifiesGameViewAspectDependency()
        {
            // P1-EVAL-001 round 7 section C item 3: the old defect scored a
            // target as in-frustum whenever the Game-view frustum contained
            // it. A point inside a 16:9 Game view but outside the 4:3
            // sensor frustum must be outside under the pinned projection.
            GameObject cameraObject = new GameObject("PinnedAspectFrustumCamera");
            try
            {
                Camera camera = cameraObject.AddComponent<Camera>();
                camera.enabled = false;
                camera.fieldOfView = 60f;
                camera.aspect = 16f / 9f;
                camera.transform.SetPositionAndRotation(
                    Vector3.zero, Quaternion.identity);
                const float sensorAspect = 640f / 480f;
                // z = 10, vertical FOV 60: half-height = 10*tan(30) = 5.774.
                // 16:9 half-width = 10.26 (inside), 4:3 half-width = 7.70
                // (outside).
                Vector3 edgePoint = new Vector3(9f, 0f, 10f);

                Vector3 oldPath = camera.WorldToViewportPoint(edgePoint);
                Vector3 pinned = CoverageEvaluator.WorldToSensorViewportPoint(
                    camera, edgePoint, sensorAspect);

                Assert.That(oldPath.z, Is.GreaterThan(0f));
                Assert.That(
                    oldPath.x,
                    Is.GreaterThanOrEqualTo(0f).And.LessThanOrEqualTo(1f));
                Assert.That(pinned.z, Is.GreaterThan(0f));
                Assert.That(pinned.x, Is.GreaterThan(1f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(cameraObject);
            }
        }

        [Test]
        public void ProjectBounds_PinnedToSensorAspectUnderMismatchedCameraAspect()
        {
            // Truth-box projection follows the sensor aspect, not the
            // camera's current aspect: identical to Unity's own projection
            // with the aspect forced to the sensor value, different from
            // the mismatched Game-view projection.
            GameObject cameraObject = new GameObject("PinnedAspectBoxCamera");
            try
            {
                Camera camera = cameraObject.AddComponent<Camera>();
                camera.enabled = false;
                camera.fieldOfView = 60f;
                camera.aspect = 16f / 9f;
                camera.transform.SetPositionAndRotation(
                    Vector3.zero, Quaternion.identity);
                const float sensorAspect = 640f / 480f;
                // Fully inside both the 4:3 and 16:9 frames so the Unity
                // oracle below needs no clipping semantics of its own.
                Vector3[] corners = CoverageEvaluator.BoundsCorners(
                    new Bounds(new Vector3(4f, 0f, 10f), new Vector3(2f, 2f, 2f)));

                NormalizedBoundingBox pinned = CoverageEvaluator.ProjectBounds(
                    camera, corners, sensorAspect);
                camera.aspect = sensorAspect;
                NormalizedBoundingBox oracle = ProjectBoundsViaUnity(camera, corners);
                camera.aspect = 16f / 9f;
                NormalizedBoundingBox mismatched =
                    ProjectBoundsViaUnity(camera, corners);

                Assert.That(pinned, Is.Not.Null);
                Assert.That(oracle, Is.Not.Null);
                Assert.That(mismatched, Is.Not.Null);
                Assert.That(pinned.x, Is.EqualTo(oracle.x).Within(1e-5f));
                Assert.That(pinned.y, Is.EqualTo(oracle.y).Within(1e-5f));
                Assert.That(pinned.width, Is.EqualTo(oracle.width).Within(1e-5f));
                Assert.That(pinned.height, Is.EqualTo(oracle.height).Within(1e-5f));
                Assert.That(
                    pinned.width,
                    Is.Not.EqualTo(mismatched.width).Within(1e-4f));
                Assert.That(pinned.height, Is.EqualTo(mismatched.height).Within(1e-5f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(cameraObject);
            }
        }

        static NormalizedBoundingBox ProjectBoundsViaUnity(
            Camera camera,
            Vector3[] corners)
        {
            float minX = float.PositiveInfinity;
            float minY = float.PositiveInfinity;
            float maxX = float.NegativeInfinity;
            float maxY = float.NegativeInfinity;
            foreach (Vector3 corner in corners)
            {
                Vector3 viewport = camera.WorldToViewportPoint(corner);
                if (viewport.z <= 0f) continue;
                minX = Mathf.Min(minX, viewport.x);
                minY = Mathf.Min(minY, viewport.y);
                maxX = Mathf.Max(maxX, viewport.x);
                maxY = Mathf.Max(maxY, viewport.y);
            }
            if (float.IsPositiveInfinity(minX)) return null;
            return new NormalizedBoundingBox
            {
                x = minX,
                y = 1f - maxY,
                width = maxX - minX,
                height = maxY - minY,
            };
        }

        [Test]
        public void SensorAspect_NonPositiveDimensionsFailClosed()
        {
            ScenarioConfig zeroWidth = ScenarioConfig.CreateDefault();
            zeroWidth.sensor.width = 0;
            Assert.Throws<InvalidOperationException>(
                () => CoverageEvaluator.SensorAspectOrThrow(zeroWidth));
            ScenarioConfig negativeHeight = ScenarioConfig.CreateDefault();
            negativeHeight.sensor.height = -1;
            Assert.Throws<InvalidOperationException>(
                () => CoverageEvaluator.SensorAspectOrThrow(negativeHeight));

            // Existing config validation clamps non-positive dimensions
            // into [64, 4096] before the evaluator ever sees them.
            ScenarioConfig normalized = ScenarioConfig.CreateDefault();
            normalized.sensor.width = 0;
            normalized.sensor.height = -3;
            normalized.Normalize();
            Assert.That(normalized.sensor.width, Is.EqualTo(64));
            Assert.That(normalized.sensor.height, Is.EqualTo(64));
            Assert.That(
                CoverageEvaluator.SensorAspectOrThrow(normalized),
                Is.EqualTo(1f).Within(1e-6f));
            Assert.That(
                CoverageEvaluator.SensorAspectOrThrow(
                    ScenarioConfig.CreateDefault()),
                Is.EqualTo(640f / 480f).Within(1e-6f));
        }

        [Test]
        public void VisibilitySamples_ContainCornersCenterAndFaceCenters()
        {
            var bounds = new Bounds(
                new Vector3(3f, 5f, 7f),
                new Vector3(2f, 4f, 6f));
            Vector3[] corners = CoverageEvaluator.BoundsCorners(bounds);

            Vector3[] samples = CoverageEvaluator.VisibilitySamples(bounds, corners);

            Assert.That(corners, Has.Length.EqualTo(8));
            Assert.That(samples, Has.Length.EqualTo(15));
            for (int index = 0; index < corners.Length; index++)
                Assert.That(samples[index], Is.EqualTo(corners[index]));
            Assert.That(samples[8], Is.EqualTo(bounds.center));
            Assert.That(samples[9], Is.EqualTo(bounds.center + Vector3.up * bounds.extents.y));
            Assert.That(samples[10], Is.EqualTo(bounds.center - Vector3.up * bounds.extents.y));
            Assert.That(samples[11], Is.EqualTo(bounds.center + Vector3.right * bounds.extents.x));
            Assert.That(samples[12], Is.EqualTo(bounds.center - Vector3.right * bounds.extents.x));
            Assert.That(samples[13], Is.EqualTo(bounds.center + Vector3.forward * bounds.extents.z));
            Assert.That(samples[14], Is.EqualTo(bounds.center - Vector3.forward * bounds.extents.z));
        }

        static NormalizedBoundingBox Box(float x, float y, float width, float height)
        {
            return new NormalizedBoundingBox
            {
                x = x,
                y = y,
                width = width,
                height = height,
            };
        }
    }

    public sealed class CoverageEvaluatorAggregationTests
    {
        [Test]
        public void Aggregation_UsesFrameDurationsAndCaptureRateFallback()
        {
            CoverageEvaluator evaluator = CreateEvaluator("WeightedAggregation", 20f, 2048);
            try
            {
                NormalizedBoundingBox truth = Box(0.2f, 0.2f, 0.3f, 0.3f);
                evaluator.RecordAggregationFrameForTests(1, 0.2f, 0.2f, true, truth);
                evaluator.RecordAggregationObservationForTests(
                    Observation(1, "target-0", truth), "target-0");

                evaluator.RecordAggregationFrameForTests(2, 0.25f, 0f, true, truth);
                evaluator.RecordAggregationObservationForTests(
                    Observation(2, "wrong-target", truth), "target-0");

                evaluator.RecordAggregationFrameForTests(3, 0.35f, 0.1f, false, truth);
                evaluator.RecordAggregationObservationForTests(
                    Observation(3, "target-0", truth), "target-0");
                evaluator.RecordAggregationFrameForTests(4, 0.5f, 0.15f, true, truth);

                CoverageEvaluator.AggregationSnapshot state =
                    evaluator.AggregationForTests();
                Assert.That(state.TotalDuration, Is.EqualTo(0.5f).Within(1e-4f));
                Assert.That(state.GeometricDuration, Is.EqualTo(0.4f).Within(1e-4f));
                Assert.That(state.TrackingDuration, Is.EqualTo(0.2f).Within(1e-4f));
                Assert.That(state.CGeom, Is.EqualTo(0.8f).Within(1e-5f));
                Assert.That(state.CTrack, Is.EqualTo(0.4f).Within(1e-5f));
                Assert.That(state.CTrackGivenGeom, Is.EqualTo(0.5f).Within(1e-5f));
                Assert.That(state.SensorFrames, Is.EqualTo(4));
                Assert.That(state.MatchedObservations, Is.EqualTo(3));
                Assert.That(state.IncorrectObservations, Is.EqualTo(2));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(evaluator.gameObject);
            }
        }

        [Test]
        public void ObservationStateMachine_HandlesMatchedIncorrectDuplicateAndUnmatched()
        {
            CoverageEvaluator evaluator = CreateEvaluator("ObservationState", 5f, 512);
            try
            {
                NormalizedBoundingBox truth = Box(0.1f, 0.1f, 0.3f, 0.3f);
                evaluator.RecordAggregationFrameForTests(10, 0.2f, 0.2f, true, truth);
                evaluator.RecordAggregationObservationForTests(
                    Observation(10, "target-0", truth), "target-0");
                evaluator.RecordAggregationObservationForTests(
                    Observation(10, "wrong-target", Box(0.7f, 0.7f, 0.1f, 0.1f)),
                    "target-0");

                evaluator.RecordAggregationFrameForTests(11, 0.4f, 0.2f, true, truth);
                evaluator.RecordAggregationObservationForTests(
                    Observation(11, "target-0", Box(0.7f, 0.7f, 0.1f, 0.1f)),
                    "target-0");
                evaluator.RecordAggregationObservationForTests(
                    Observation(999, "target-0", truth), "target-0");

                CoverageEvaluator.AggregationSnapshot state =
                    evaluator.AggregationForTests();
                Assert.That(state.MatchedObservations, Is.EqualTo(2));
                Assert.That(state.IncorrectObservations, Is.EqualTo(1));
                Assert.That(state.UnmatchedObservations, Is.EqualTo(1));
                Assert.That(state.TrackingDuration, Is.EqualTo(0.2f).Within(1e-4f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(evaluator.gameObject);
            }
        }

        [TestCase(5f, 512)]
        [TestCase(20f, 2048)]
        public void PendingPruning_PreservesAcceptedAttributionAcrossEquivalentWindows(
            float captureHz,
            int maximumPendingFrames)
        {
            CoverageEvaluator evaluator = CreateEvaluator(
                $"PendingPruning{captureHz}",
                captureHz,
                maximumPendingFrames);
            try
            {
                NormalizedBoundingBox truth = Box(0.2f, 0.2f, 0.2f, 0.2f);
                float weight = 1f / captureHz;
                evaluator.RecordAggregationFrameForTests(0, 0f, 0f, true, truth);
                evaluator.RecordAggregationObservationForTests(
                    Observation(0, "target-0", truth), "target-0");
                for (int frameId = 1; frameId <= maximumPendingFrames; frameId++)
                {
                    evaluator.RecordAggregationFrameForTests(
                        frameId,
                        frameId * weight,
                        0f,
                        true,
                        truth);
                }

                CoverageEvaluator.AggregationSnapshot beforeLateDuplicate =
                    evaluator.AggregationForTests();
                Assert.That(beforeLateDuplicate.PendingFrames, Is.EqualTo(maximumPendingFrames));
                Assert.That(evaluator.HasPendingFrameForTests(0), Is.False);
                Assert.That(evaluator.HasPendingFrameForTests(1), Is.True);
                Assert.That(
                    beforeLateDuplicate.TrackingDuration,
                    Is.EqualTo(weight).Within(1e-4f));

                evaluator.RecordAggregationObservationForTests(
                    Observation(0, "target-0", truth), "target-0");
                CoverageEvaluator.AggregationSnapshot afterLateDuplicate =
                    evaluator.AggregationForTests();
                Assert.That(afterLateDuplicate.UnmatchedObservations, Is.EqualTo(1));
                Assert.That(
                    afterLateDuplicate.TrackingDuration,
                    Is.EqualTo(weight).Within(1e-4f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(evaluator.gameObject);
            }
        }

        [Serializable]
        sealed class EvaluationProjectionRecord
        {
            public int sensor_width_px;
            public int sensor_height_px;
            public float aspect_width_over_height;
        }

        [Test]
        public void MetricsJson_RecordsPinnedEvaluationProjection()
        {
            // P1-EVAL-001 round 7 section C item 2: every metrics.json
            // carries a top-level evaluation_projection object with exactly
            // these three keys; the default run records 640/480 and
            // 640f/480f. Existing document fields are unchanged.
            CoverageEvaluator evaluator = CreateEvaluator("ProjectionRecord", 5f, 512);
            try
            {
                string json = evaluator.MetricsJsonForTests();
                int keyStart = json.IndexOf(
                    "\"evaluation_projection\":{", StringComparison.Ordinal);
                Assert.That(keyStart, Is.GreaterThanOrEqualTo(0));
                int bodyStart = json.IndexOf('{', keyStart);
                int bodyEnd = json.IndexOf('}', bodyStart);
                Assert.That(bodyEnd, Is.GreaterThan(bodyStart));
                string body = json.Substring(
                    bodyStart + 1, bodyEnd - bodyStart - 1);
                Assert.That(body.Split(','), Has.Length.EqualTo(3));

                EvaluationProjectionRecord record =
                    JsonUtility.FromJson<EvaluationProjectionRecord>(
                        json.Substring(bodyStart, bodyEnd - bodyStart + 1));
                Assert.That(record, Is.Not.Null);
                Assert.That(record.sensor_width_px, Is.EqualTo(640));
                Assert.That(record.sensor_height_px, Is.EqualTo(480));
                Assert.That(
                    record.aspect_width_over_height,
                    Is.EqualTo(640f / 480f).Within(1e-6f));

                Assert.That(
                    json,
                    Does.Contain("\"schema_version\":\"tethered-evaluation/v1\""));
                Assert.That(json, Does.Contain("\"thresholds\":{"));
                Assert.That(json, Does.Contain("\"aggregate\":{"));
                Assert.That(json, Does.Contain("\"occlusion_geometry\":{"));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(evaluator.gameObject);
            }
        }

        static CoverageEvaluator CreateEvaluator(
            string name,
            float captureHz,
            int maximumPendingFrames)
        {
            var gameObject = new GameObject(name);
            CoverageEvaluator evaluator = gameObject.AddComponent<CoverageEvaluator>();
            evaluator.ConfigureAggregationForTests(
                captureHz,
                maximumPendingFrames,
                0.3f);
            return evaluator;
        }

        static TrackingObservation Observation(
            long frameId,
            string trackId,
            NormalizedBoundingBox box)
        {
            return new TrackingObservation(frameId, trackId, box, 1f, 0.0);
        }

        static NormalizedBoundingBox Box(float x, float y, float width, float height)
        {
            return new NormalizedBoundingBox
            {
                x = x,
                y = y,
                width = width,
                height = height,
            };
        }
    }

    public sealed class TetheredDronePlantTests
    {
        [Test]
        public void Step_ClampsCommandSpeedAndAcceleration()
        {
            TetheredDronePlant plant = CreatePlant("AccelerationPlant");
            try
            {
                plant.maximumSpeed = 4f;
                plant.maximumAcceleration = 2f;
                plant.transform.position = plant.anchor + Vector3.up * 5f;

                plant.SetVelocity(new Vector3(100f, 0f, 0f));
                plant.Step(0.5f);

                Assert.That(plant.CommandedVelocity.magnitude, Is.EqualTo(4f).Within(1e-6f));
                Assert.That(plant.AppliedVelocity.x, Is.EqualTo(1f).Within(1e-6f));
                Assert.That(plant.transform.position.x, Is.EqualTo(0.5f).Within(1e-6f));
                Assert.That(plant.transform.position.y, Is.EqualTo(5f).Within(1e-6f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(plant.gameObject);
            }
        }

        [Test]
        public void Step_ClampsAltitudeAndTetherSphere()
        {
            TetheredDronePlant horizontal = CreatePlant("HorizontalClampPlant");
            TetheredDronePlant low = CreatePlant("MinimumAltitudePlant");
            TetheredDronePlant high = CreatePlant("MaximumAltitudePlant");
            try
            {
                horizontal.transform.position = Vector3.up * 8f;
                horizontal.SetVelocity(new Vector3(4f, 0f, 0f));
                horizontal.Step(10f);
                Assert.That(horizontal.transform.position.x, Is.EqualTo(6f).Within(1e-5f));
                Assert.That(horizontal.transform.position.y, Is.EqualTo(8f).Within(1e-5f));
                Assert.That(
                    (horizontal.transform.position - horizontal.anchor).magnitude,
                    Is.EqualTo(10f).Within(1e-5f));
                Assert.That(horizontal.TetherSaturated, Is.True);

                low.transform.position = Vector3.up * 5f;
                low.SetVelocity(new Vector3(0f, -4f, 0f));
                low.Step(10f);
                Assert.That(low.transform.position.y, Is.EqualTo(2f).Within(1e-5f));

                high.transform.position = Vector3.up * 5f;
                high.SetVelocity(new Vector3(0f, 4f, 0f));
                high.Step(10f);
                Assert.That(high.transform.position.y, Is.EqualTo(8f).Within(1e-5f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(horizontal.gameObject);
                UnityEngine.Object.DestroyImmediate(low.gameObject);
                UnityEngine.Object.DestroyImmediate(high.gameObject);
            }
        }

        // ---------------------------------------------------------------
        // P1-ENG-FRAME-001 Part T (AC-2, AC-4, AC-19 golden vectors).
        // ---------------------------------------------------------------

        /// <summary>
        /// Pre-change <c>TetheredDronePlant</c> kept verbatim as the AC-2
        /// reference: field and method bodies are copied from the K2 base
        /// (the parent of the first "P1-ENG-FRAME-001 K2" commit); the only
        /// adaptation is that <c>transform</c> is a plain field instead of
        /// the MonoBehaviour property. Reviewers diff the Step body against
        /// the base file.
        /// </summary>
        sealed class LegacyPlantReference
        {
            public Transform transform;
            public Vector3 anchor = new Vector3(132f, 0f, 117f);
            public float tetherLength = 35f;
            public float minimumAltitude = 8f;
            public float maximumAltitude = 32f;
            public float maximumSpeed = 4f;
            public float maximumAcceleration = 4f;
            public float yawRate = 120f;

            public Vector3 CommandedVelocity { get; private set; }
            public Vector3 AppliedVelocity { get; private set; }
            public bool TetherSaturated { get; private set; }

            public void SetVelocity(Vector3 worldVelocity)
            {
                CommandedVelocity = Vector3.ClampMagnitude(worldVelocity, maximumSpeed);
            }

            public void Hold()
            {
                CommandedVelocity = Vector3.zero;
            }

            internal void Step(float deltaTime)
            {
                AppliedVelocity = Vector3.MoveTowards(
                    AppliedVelocity, CommandedVelocity, maximumAcceleration * deltaTime);
                Vector3 next = transform.position + AppliedVelocity * deltaTime;
                Vector3 relative = next - anchor;
                TetherSaturated = relative.magnitude > tetherLength;

                float vertical = Mathf.Clamp(relative.y, minimumAltitude, maximumAltitude);
                vertical = Mathf.Min(vertical, tetherLength);
                Vector2 horizontal = new Vector2(relative.x, relative.z);
                float maximumHorizontal = Mathf.Sqrt(Mathf.Max(0f, tetherLength * tetherLength - vertical * vertical));
                if (horizontal.magnitude > maximumHorizontal)
                {
                    horizontal = horizontal.normalized * maximumHorizontal;
                    TetherSaturated = true;
                }
                next = anchor + new Vector3(horizontal.x, vertical, horizontal.y);

                transform.position = next;
                Vector3 horizontalVelocity = new Vector3(AppliedVelocity.x, 0f, AppliedVelocity.z);
                if (horizontalVelocity.sqrMagnitude > 0.0001f)
                {
                    float yaw = Mathf.Atan2(horizontalVelocity.x, horizontalVelocity.z) * Mathf.Rad2Deg;
                    transform.rotation = Quaternion.RotateTowards(
                        transform.rotation, Quaternion.Euler(0f, yaw, 0f), yawRate * deltaTime);
                }
            }
        }

        /// <summary>Plant parameter set shared with tests/test_frame_follow_replay.py.</summary>
        struct PlantParams
        {
            public Vector3 Anchor;
            public float TetherLength;
            public float MinimumAltitude;
            public float MaximumAltitude;
            public float MaximumSpeed;
            public float MaximumAcceleration;
            public Vector3 Start;
            public bool TetherEnabled;
            public bool HasGeofence;
            public Vector4 Geofence; // min_x, max_x, min_z, max_z

            public PlantParams(
                Vector3 anchor, float tetherLength, float minimumAltitude, float maximumAltitude,
                Vector3 start, bool tetherEnabled, bool hasGeofence = false, Vector4 geofence = default)
            {
                Anchor = anchor;
                TetherLength = tetherLength;
                MinimumAltitude = minimumAltitude;
                MaximumAltitude = maximumAltitude;
                MaximumSpeed = 4f;
                MaximumAcceleration = 4f;
                Start = start;
                TetherEnabled = tetherEnabled;
                HasGeofence = hasGeofence;
                Geofence = geofence;
            }
        }

        static readonly PlantParams TP = new PlantParams(
            Vector3.zero, 35f, 8f, 32f, new Vector3(0f, 25f, 0f), true);
        static readonly PlantParams UP = new PlantParams(
            Vector3.zero, 10f, 8f, 32f, new Vector3(0f, 25f, 0f), false,
            true, new Vector4(-22f, 58f, -67f, 13f));
        static readonly PlantParams RT = new PlantParams(
            Vector3.zero, 10f, 2f, 8f, new Vector3(0f, 5f, 0f), true);
        static readonly PlantParams RU = new PlantParams(
            Vector3.zero, 3f, 2f, 8f, new Vector3(0f, 5f, 0f), false,
            true, new Vector4(-6f, 6f, -4f, 8f));
        static readonly PlantParams Realistic = new PlantParams(
            new Vector3(132f, 0.2f, 117f), 35f, 8f, 32f, new Vector3(132f, 25.2f, 117f), true);

        /// <summary>Same generator as tests/test_frame_follow_replay.py.</summary>
        sealed class XorShift32
        {
            uint state;
            public XorShift32(uint seed) { state = seed; }
            public uint Next()
            {
                uint x = state;
                x ^= x << 13;
                x ^= x >> 17;
                x ^= x << 5;
                state = x;
                return x;
            }
            public float NextUnit() => (Next() >> 8) * (1f / 16777216f);
        }

        /// <summary>
        /// One command per step: a scripted segment list, or (random) a
        /// seeded list of held segments. Each delegate receives the command
        /// (null = Hold) for every step in order.
        /// </summary>
        static System.Collections.Generic.List<Vector3?> ScriptedCommands(params (Vector3 velocity, int steps)[] segments)
        {
            var commands = new System.Collections.Generic.List<Vector3?>();
            foreach ((Vector3 velocity, int steps) in segments)
                for (int index = 0; index < steps; index++) commands.Add(velocity);
            return commands;
        }

        static System.Collections.Generic.List<Vector3?> RandomCommands(uint seed, int steps)
        {
            var rng = new XorShift32(seed);
            var commands = new System.Collections.Generic.List<Vector3?>();
            while (commands.Count < steps)
            {
                float r = rng.NextUnit();
                Vector3? command = null;
                if (!(r < 0.15f))
                {
                    float vx = rng.NextUnit() * 12f - 6f;
                    float vy = rng.NextUnit() * 6f - 3f;
                    float vz = rng.NextUnit() * 12f - 6f;
                    command = new Vector3(vx, vy, vz);
                }
                int duration = 10 + (int)(rng.NextUnit() * 50f);
                for (int index = 0; index < duration && commands.Count < steps; index++)
                    commands.Add(command);
            }
            return commands;
        }

        static TetheredDronePlant CreateConfiguredPlant(string name, PlantParams p, bool assignTetherFlag = true)
        {
            var gameObject = new GameObject(name);
            TetheredDronePlant plant = gameObject.AddComponent<TetheredDronePlant>();
            plant.anchor = p.Anchor;
            plant.tetherLength = p.TetherLength;
            plant.minimumAltitude = p.MinimumAltitude;
            plant.maximumAltitude = p.MaximumAltitude;
            plant.maximumSpeed = p.MaximumSpeed;
            plant.maximumAcceleration = p.MaximumAcceleration;
            if (assignTetherFlag) plant.tetherEnabled = p.TetherEnabled;
            plant.ConfigureGeofence(p.HasGeofence
                ? new GeofenceScenarioConfig
                {
                    min_x = p.Geofence.x,
                    max_x = p.Geofence.y,
                    min_z = p.Geofence.z,
                    max_z = p.Geofence.w,
                }
                : null);
            plant.transform.position = p.Start;
            return plant;
        }

        static void Apply(TetheredDronePlant plant, Vector3? command)
        {
            if (command.HasValue) plant.SetVelocity(command.Value);
            else plant.Hold();
        }

        static void AssertBitwise(float actual, float expected, string label)
        {
            Assert.That(
                BitConverter.ToInt32(BitConverter.GetBytes(actual), 0),
                Is.EqualTo(BitConverter.ToInt32(BitConverter.GetBytes(expected), 0)),
                label + $" actual={actual:R} expected={expected:R}");
        }

        static void RunAgainstLegacy(string label, PlantParams p, System.Collections.Generic.List<Vector3?> commands, bool assignTetherFlag, float deltaTime)
        {
            TetheredDronePlant plant = CreateConfiguredPlant(label + "-current", p, assignTetherFlag);
            var legacyObject = new GameObject(label + "-legacy");
            var legacy = new LegacyPlantReference
            {
                transform = legacyObject.transform,
                anchor = p.Anchor,
                tetherLength = p.TetherLength,
                minimumAltitude = p.MinimumAltitude,
                maximumAltitude = p.MaximumAltitude,
                maximumSpeed = p.MaximumSpeed,
                maximumAcceleration = p.MaximumAcceleration,
            };
            legacyObject.transform.position = p.Start;
            try
            {
                Assert.That(plant.tetherEnabled, Is.True, label + " must run the tethered path");
                Assert.That(plant.geofenceEnabled, Is.False, label + " has no geofence");
                for (int index = 0; index < commands.Count; index++)
                {
                    Apply(plant, commands[index]);
                    if (commands[index].HasValue) legacy.SetVelocity(commands[index].Value);
                    else legacy.Hold();
                    plant.Step(deltaTime);
                    legacy.Step(deltaTime);
                    string at = $"{label} step {index + 1}";
                    AssertBitwise(plant.transform.position.x, legacyObject.transform.position.x, at + " x");
                    AssertBitwise(plant.transform.position.y, legacyObject.transform.position.y, at + " y");
                    AssertBitwise(plant.transform.position.z, legacyObject.transform.position.z, at + " z");
                    AssertBitwise(plant.AppliedVelocity.x, legacy.AppliedVelocity.x, at + " vx");
                    AssertBitwise(plant.AppliedVelocity.y, legacy.AppliedVelocity.y, at + " vy");
                    AssertBitwise(plant.AppliedVelocity.z, legacy.AppliedVelocity.z, at + " vz");
                    Assert.That(plant.TetherSaturated, Is.EqualTo(legacy.TetherSaturated), at + " saturated");
                }
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(plant.gameObject);
                UnityEngine.Object.DestroyImmediate(legacyObject);
            }
        }

        [Test]
        public void Step_TetherEnabledMatchesLegacyReferenceBitwise()
        {
            PlantParams existingAcceleration = new PlantParams(
                Vector3.zero, 10f, 2f, 8f, new Vector3(0f, 5f, 0f), true);
            existingAcceleration.MaximumAcceleration = 2f;
            PlantParams existingHorizontal = new PlantParams(
                Vector3.zero, 10f, 2f, 8f, new Vector3(0f, 8f, 0f), true);
            existingHorizontal.MaximumAcceleration = 100f;
            PlantParams existingVertical = new PlantParams(
                Vector3.zero, 10f, 2f, 8f, new Vector3(0f, 5f, 0f), true);
            existingVertical.MaximumAcceleration = 100f;
            var sequences = new (string label, PlantParams p, System.Collections.Generic.List<Vector3?> commands, float dt)[]
            {
                // The two pre-existing examples, with their own step sizes.
                ("existing-1-acceleration", existingAcceleration,
                    ScriptedCommands((new Vector3(100f, 0f, 0f), 1)), 0.5f),
                ("existing-2-horizontal", existingHorizontal,
                    ScriptedCommands((new Vector3(4f, 0f, 0f), 1)), 10f),
                ("existing-2-low", existingVertical,
                    ScriptedCommands((new Vector3(0f, -4f, 0f), 1)), 10f),
                ("existing-2-high", existingVertical,
                    ScriptedCommands((new Vector3(0f, 4f, 0f), 1)), 10f),
                // Acceleration, outward saturation, altitude limits, oblique
                // slide and seeded random sequences (>= 1,000 steps).
                ("GT1-acceleration", TP, ScriptedCommands((new Vector3(4f, 0f, 0f), 100)), 0.02f),
                ("GT2-outward-saturation", TP, ScriptedCommands((new Vector3(4f, 0f, 3f), 2000)), 0.02f),
                ("GT3-altitude-limits", TP, ScriptedCommands((new Vector3(0f, 4f, 0f), 500), (new Vector3(0f, -4f, 0f), 1000)), 0.02f),
                ("GT4-oblique-slide", TP, ScriptedCommands((new Vector3(4f, 0f, 0f), 400), (new Vector3(0f, 0f, 4f), 400)), 0.02f),
                ("GT5-random-1000", RT, RandomCommands(0x2545F491u, 1000), 0.02f),
                ("realistic-random-1500", Realistic, RandomCommands(0x01234567u, 1500), 0.02f),
            };
            foreach ((string label, PlantParams p, System.Collections.Generic.List<Vector3?> commands, float dt) in sequences)
            {
                // "Field missing" = the component default; "true" = assigned.
                RunAgainstLegacy(label + "/default-flag", p, commands, false, dt);
                RunAgainstLegacy(label + "/explicit-true", p, commands, true, dt);
            }
        }

        static void AssertGolden(string label, PlantParams p, System.Collections.Generic.List<Vector3?> commands, float[][] golden)
        {
            TetheredDronePlant plant = CreateConfiguredPlant(label, p);
            try
            {
                int next = 0;
                for (int index = 0; index < commands.Count; index++)
                {
                    Apply(plant, commands[index]);
                    plant.Step(0.02f);
                    if (next < golden.Length && (int)golden[next][0] == index + 1)
                    {
                        float[] row = golden[next];
                        string at = $"{label} step {index + 1}";
                        Assert.That(plant.transform.position.x, Is.EqualTo(row[1]).Within(1e-5f), at + " x");
                        Assert.That(plant.transform.position.y, Is.EqualTo(row[2]).Within(1e-5f), at + " y");
                        Assert.That(plant.transform.position.z, Is.EqualTo(row[3]).Within(1e-5f), at + " z");
                        Assert.That(plant.AppliedVelocity.x, Is.EqualTo(row[4]).Within(1e-5f), at + " vx");
                        Assert.That(plant.AppliedVelocity.y, Is.EqualTo(row[5]).Within(1e-5f), at + " vy");
                        Assert.That(plant.AppliedVelocity.z, Is.EqualTo(row[6]).Within(1e-5f), at + " vz");
                        Assert.That(plant.TetherSaturated, Is.EqualTo(row[7] > 0.5f), at + " saturated");
                        next++;
                    }
                }
                Assert.That(next, Is.EqualTo(golden.Length), label + " checkpoints");
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(plant.gameObject);
            }
        }

        [Test]
        public void Step_TetheredGoldenVectors()
        {
            AssertGolden("GT1", TP, ScriptedCommands((new Vector3(4f, 0f, 0f), 100)), GoldenGT1);
            AssertGolden("GT2", TP, ScriptedCommands((new Vector3(4f, 0f, 3f), 2000)), GoldenGT2);
            AssertGolden("GT3", TP, ScriptedCommands((new Vector3(0f, 4f, 0f), 500), (new Vector3(0f, -4f, 0f), 1000)), GoldenGT3);
            AssertGolden("GT4", TP, ScriptedCommands((new Vector3(4f, 0f, 0f), 400), (new Vector3(0f, 0f, 4f), 400)), GoldenGT4);
            AssertGolden("GT5", RT, RandomCommands(0x2545F491u, 1000), GoldenGT5);
        }

        [Test]
        public void Step_UntetheredGoldenVectors()
        {
            AssertGolden("GU1", UP, ScriptedCommands((new Vector3(4f, 0f, 0f), 1000)), GoldenGU1);
            AssertGolden("GU2", UP, ScriptedCommands((new Vector3(0f, 4f, 0f), 500), (new Vector3(0f, -4f, 0f), 1000)), GoldenGU2);
            AssertGolden("GU3", UP, ScriptedCommands((new Vector3(-3f, 0f, -4f), 1500)), GoldenGU3);
            AssertGolden("GU4", RU, RandomCommands(0x9E3779B9u, 1000), GoldenGU4);
        }

        static Vector3 RunPlant(PlantParams p, System.Collections.Generic.List<Vector3?> commands, out bool everSaturated, out TetheredDronePlant left)
        {
            TetheredDronePlant plant = CreateConfiguredPlant("ac4", p);
            everSaturated = false;
            foreach (Vector3? command in commands)
            {
                Apply(plant, command);
                plant.Step(0.02f);
                everSaturated |= plant.TetherSaturated;
            }
            left = plant;
            return plant.transform.position;
        }

        static PlantParams Tethered(PlantParams p)
        {
            p.TetherEnabled = true;
            p.HasGeofence = false;
            return p;
        }

        [Test]
        public void Step_TetherOff_CanPassThirtyFiveMetresFromAnchor()
        {
            // UP with a 35 m cable: off -> reaches the 58 m geofence edge;
            // red: the same sequence with the tether on stays inside 35 m.
            PlantParams off = UP;
            off.TetherLength = 35f;
            var commands = ScriptedCommands((new Vector3(4f, 0f, 0f), 1000));
            Vector3 offEnd = RunPlant(off, commands, out _, out TetheredDronePlant offPlant);
            Vector3 onEnd = RunPlant(Tethered(off), commands, out _, out TetheredDronePlant onPlant);
            try
            {
                Assert.That((offEnd - off.Anchor).magnitude, Is.GreaterThan(35f));
                Assert.That(offEnd.x, Is.EqualTo(58f));
                Assert.That((onEnd - off.Anchor).magnitude, Is.LessThanOrEqualTo(35f + 1e-4f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(offPlant.gameObject);
                UnityEngine.Object.DestroyImmediate(onPlant.gameObject);
            }
        }

        [Test]
        public void Step_TetherOff_NeverReportsTetherSaturated()
        {
            var commands = RandomCommands(0x9E3779B9u, 1000);
            RunPlant(RU, commands, out bool offSaturated, out TetheredDronePlant offPlant);
            RunPlant(Tethered(RU), commands, out bool onSaturated, out TetheredDronePlant onPlant);
            try
            {
                Assert.That(offSaturated, Is.False);
                Assert.That(onSaturated, Is.True, "red: the same sequence saturates a 3 m cable");
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(offPlant.gameObject);
                UnityEngine.Object.DestroyImmediate(onPlant.gameObject);
            }
        }

        [Test]
        public void Step_TetherOff_AltitudeBandIsNotCappedByTetherLength()
        {
            // UP: cable 10 m, band [8, 32]. Off climbs to 32; on is capped at 10.
            var up = ScriptedCommands((new Vector3(0f, 4f, 0f), 500));
            Vector3 offTop = RunPlant(UP, up, out _, out TetheredDronePlant offPlant);
            Vector3 onTop = RunPlant(Tethered(UP), up, out _, out TetheredDronePlant onPlant);
            var down = ScriptedCommands((new Vector3(0f, -4f, 0f), 1000));
            Vector3 offBottom = RunPlant(UP, down, out _, out TetheredDronePlant lowPlant);
            try
            {
                Assert.That(offTop.y, Is.EqualTo(32f));
                Assert.That(onTop.y, Is.EqualTo(10f), "red: the tether caps the climb");
                Assert.That(offBottom.y, Is.EqualTo(8f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(offPlant.gameObject);
                UnityEngine.Object.DestroyImmediate(onPlant.gameObject);
                UnityEngine.Object.DestroyImmediate(lowPlant.gameObject);
            }
        }

        [Test]
        public void Step_TetherOff_SpeedAndAccelerationClampsUnchanged()
        {
            PlantParams off = UP;
            off.MaximumAcceleration = 2f;
            TetheredDronePlant plant = CreateConfiguredPlant("ac4-speed", off);
            try
            {
                plant.SetVelocity(new Vector3(100f, 0f, 0f));
                plant.Step(0.5f);
                Assert.That(plant.CommandedVelocity.magnitude, Is.EqualTo(4f).Within(1e-6f));
                Assert.That(plant.AppliedVelocity.x, Is.EqualTo(1f).Within(1e-6f));
                Assert.That(plant.transform.position.x, Is.EqualTo(0.5f).Within(1e-6f));
                for (int index = 0; index < 100; index++) plant.Step(0.02f);
                Assert.That(plant.AppliedVelocity.magnitude, Is.EqualTo(4f).Within(1e-5f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(plant.gameObject);
            }
        }

        [Test]
        public void Step_TetherOff_StaysInsideGeofence()
        {
            var commands = RandomCommands(0x9E3779B9u, 1000);
            TetheredDronePlant plant = CreateConfiguredPlant("ac4-fence", RU);
            PlantParams unfenced = RU;
            unfenced.HasGeofence = false;
            TetheredDronePlant free = CreateConfiguredPlant("ac4-free", unfenced);
            try
            {
                bool freeLeft = false;
                foreach (Vector3? command in commands)
                {
                    Apply(plant, command);
                    Apply(free, command);
                    plant.Step(0.02f);
                    free.Step(0.02f);
                    Vector3 p = plant.transform.position;
                    Assert.That(p.x, Is.InRange(RU.Geofence.x, RU.Geofence.y));
                    Assert.That(p.z, Is.InRange(RU.Geofence.z, RU.Geofence.w));
                    Vector3 f = free.transform.position;
                    freeLeft |= f.x < RU.Geofence.x || f.x > RU.Geofence.y
                        || f.z < RU.Geofence.z || f.z > RU.Geofence.w;
                }
                Assert.That(freeLeft, Is.True, "red: without the geofence the sequence leaves the rectangle");
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(plant.gameObject);
                UnityEngine.Object.DestroyImmediate(free.gameObject);
            }
        }

        // AC-19 golden vectors: generated by the float32 mirror in
        // tools/frame_follow_replay.py and asserted here against the real
        // plant; tests/test_frame_follow_replay.py asserts the same literals.
        // K2补跑: regenerated after the mirror adopted the runtime's
        // store-rounding (double temporaries, float32 at each store), which
        // reproduces this plant bit for bit on every step of all nine
        // sequences.
        static readonly float[][] GoldenGT1 =
        {
            new[] { 10f, 0.0879999846f, 25f, 0f, 0.799999893f, 0f, 0f, 0f },
            new[] { 20f, 0.335999995f, 25f, 0f, 1.60000014f, 0f, 0f, 0f },
            new[] { 30f, 0.743999958f, 25f, 0f, 2.39999986f, 0f, 0f, 0f },
            new[] { 40f, 1.3119998f, 25f, 0f, 3.19999909f, 0f, 0f, 0f },
            new[] { 50f, 2.03999949f, 25f, 0f, 3.99999833f, 0f, 0f, 0f },
            new[] { 60f, 2.83999872f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 70f, 3.63999796f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 80f, 4.4399972f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 90f, 5.23999643f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 100f, 6.03999567f, 25f, 0f, 4f, 0f, 0f, 0f },
        };

        static readonly float[][] GoldenGT2 =
        {
            new[] { 250f, 14.4320173f, 25f, 10.8240108f, 3.20000005f, 0f, 2.4000001f, 0f },
            new[] { 500f, 19.59589f, 25f, 14.6969757f, 3.20000005f, 0f, 2.4000001f, 1f },
            new[] { 750f, 19.59589f, 25f, 14.6969757f, 3.20000005f, 0f, 2.4000001f, 1f },
            new[] { 1000f, 19.59589f, 25f, 14.6969757f, 3.20000005f, 0f, 2.4000001f, 1f },
            new[] { 1250f, 19.59589f, 25f, 14.6969757f, 3.20000005f, 0f, 2.4000001f, 1f },
            new[] { 1500f, 19.59589f, 25f, 14.6969757f, 3.20000005f, 0f, 2.4000001f, 1f },
            new[] { 1750f, 19.59589f, 25f, 14.6969757f, 3.20000005f, 0f, 2.4000001f, 1f },
            new[] { 2000f, 19.59589f, 25f, 14.6969757f, 3.20000005f, 0f, 2.4000001f, 1f },
        };

        static readonly float[][] GoldenGT3 =
        {
            new[] { 250f, 0f, 32f, 0f, 0f, 4f, 0f, 0f },
            new[] { 500f, 0f, 32f, 0f, 0f, 4f, 0f, 0f },
            new[] { 750f, 0f, 17.9600124f, 0f, 0f, -4f, 0f, 0f },
            new[] { 1000f, 0f, 8f, 0f, 0f, -4f, 0f, 0f },
            new[] { 1250f, 0f, 8f, 0f, 0f, -4f, 0f, 0f },
            new[] { 1500f, 0f, 8f, 0f, 0f, -4f, 0f, 0f },
        };

        static readonly float[][] GoldenGT4 =
        {
            new[] { 100f, 6.03999567f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 200f, 14.0399885f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 300f, 22.0399818f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 400f, 24.4948978f, 25f, 0f, 4f, 0f, 0f, 1f },
            new[] { 500f, 23.9620972f, 25f, 5.0811305f, 0f, 0f, 4f, 1f },
            new[] { 600f, 21.3439598f, 25f, 12.0181236f, 0f, 0f, 4f, 1f },
            new[] { 700f, 17.5433311f, 25f, 17.0947819f, 0f, 0f, 4f, 1f },
            new[] { 800f, 13.6484098f, 25f, 20.3401318f, 0f, 0f, 4f, 1f },
        };

        static readonly float[][] GoldenGU1 =
        {
            new[] { 100f, 6.03999567f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 200f, 14.0399885f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 300f, 22.0399818f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 400f, 30.0399742f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 500f, 38.0401115f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 600f, 46.0402946f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 700f, 54.0404778f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 800f, 58f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 900f, 58f, 25f, 0f, 4f, 0f, 0f, 0f },
            new[] { 1000f, 58f, 25f, 0f, 4f, 0f, 0f, 0f },
        };

        static readonly float[][] GoldenGU2 =
        {
            new[] { 250f, 0f, 32f, 0f, 0f, 4f, 0f, 0f },
            new[] { 500f, 0f, 32f, 0f, 0f, 4f, 0f, 0f },
            new[] { 750f, 0f, 17.9600124f, 0f, 0f, -4f, 0f, 0f },
            new[] { 1000f, 0f, 8f, 0f, 0f, -4f, 0f, 0f },
            new[] { 1250f, 0f, 8f, 0f, 0f, -4f, 0f, 0f },
            new[] { 1500f, 0f, 8f, 0f, 0f, -4f, 0f, 0f },
        };

        static readonly float[][] GoldenGU3 =
        {
            new[] { 250f, -10.8240108f, 25f, -14.4320173f, -2.4000001f, 0f, -3.20000005f, 0f },
            new[] { 500f, -22f, 25f, -30.4318352f, -2.4000001f, 0f, -3.20000005f, 0f },
            new[] { 750f, -22f, 25f, -46.4316292f, -2.4000001f, 0f, -3.20000005f, 0f },
            new[] { 1000f, -22f, 25f, -62.4314232f, -2.4000001f, 0f, -3.20000005f, 0f },
            new[] { 1250f, -22f, 25f, -67f, -2.4000001f, 0f, -3.20000005f, 0f },
            new[] { 1500f, -22f, 25f, -67f, -2.4000001f, 0f, -3.20000005f, 0f },
        };

        static readonly float[][] GoldenGT5 =
        {
            new[] { 100f, 0.519257009f, 4.05134153f, -4.60377693f, 0.153559178f, -0.433554888f, -0.860100508f, 0f },
            new[] { 200f, 1.27687144f, 2.5350132f, -0.833194196f, -0.416952521f, -0.667861342f, 3.0893147f, 0f },
            new[] { 300f, -0.334574133f, 2f, -1.31887376f, -0.303861678f, -0.362520397f, -1.04750013f, 0f },
            new[] { 400f, 4.44619226f, 2f, -3.60124016f, 2.84949875f, -1.02996123f, -1.69780946f, 0f },
            new[] { 500f, 6.13281345f, 2f, -7.64124393f, 0.215932488f, -0.0979860201f, -0.0370391011f, 1f },
            new[] { 600f, 7.4738431f, 2f, -5.89801025f, -0.285673857f, -1.06080639f, 1.8880918f, 0f },
            new[] { 700f, 6.85658503f, 2f, -5.77157831f, -0.84620893f, -0.245325789f, -2.74192381f, 0f },
            new[] { 800f, 4.56154537f, 2.87072921f, -8.42325497f, -1.65329504f, 0.77787751f, -2.63765621f, 1f },
            new[] { 900f, 1.22841585f, 3.2162075f, -9.38866329f, -0.523528695f, -0.246588632f, -2.35964012f, 1f },
            new[] { 1000f, 0.720393121f, 3.69406033f, -9.26471519f, 0f, 0f, 0f, 0f },
        };

        static readonly float[][] GoldenGU4 =
        {
            new[] { 100f, 3.66593957f, 5.74986649f, -3.29295897f, 2.37924504f, 1.63427246f, -0.0278320611f, 0f },
            new[] { 200f, 3.48592257f, 6.39644527f, -3.58467913f, -2.44546962f, 0.968946815f, -0.113235362f, 0f },
            new[] { 300f, -1.9059552f, 8f, -4f, -0.545584559f, 1.13389969f, -0.920637548f, 0f },
            new[] { 400f, -0.357191235f, 8f, -3.82422161f, 1.27530098f, 0.647857368f, 1.0493114f, 0f },
            new[] { 500f, 0.430335164f, 8f, -2.76775002f, -0.494385391f, 0.661547244f, 1.10971653f, 0f },
            new[] { 600f, 1.82742918f, 8f, -0.812999606f, -0.109506994f, 0.392788291f, 0.367884785f, 0f },
            new[] { 700f, 3.14223123f, 7.82431364f, -3.05586004f, -0.84871769f, -0.46538192f, -0.503107965f, 0f },
            new[] { 800f, -0.337541521f, 7.16489172f, -4f, 0f, 0f, 0f, 0f },
            new[] { 900f, -0.342940629f, 7.52480316f, -4f, 0f, 0f, 0f, 0f },
            new[] { 1000f, -0.319679201f, 6.51986837f, -1.03227425f, -2.09782743f, 0.332731903f, 1.53960145f, 0f },
        };

        static TetheredDronePlant CreatePlant(string name)
        {
            var gameObject = new GameObject(name);
            TetheredDronePlant plant = gameObject.AddComponent<TetheredDronePlant>();
            plant.anchor = Vector3.zero;
            plant.tetherLength = 10f;
            plant.minimumAltitude = 2f;
            plant.maximumAltitude = 8f;
            plant.maximumSpeed = 4f;
            plant.maximumAcceleration = 100f;
            return plant;
        }
    }

    public sealed class AtomicFileTests
    {
        [Test]
        public void Write_ReplacesDestinationAndLeavesNoTemporaryFile()
        {
            string directory = Path.Combine(
                Path.GetTempPath(),
                "TetheredTrackingEditModeTests",
                Guid.NewGuid().ToString("N"));
            string textPath = Path.Combine(directory, "state.json");
            string bytesPath = Path.Combine(directory, "frame.bin");
            try
            {
                AtomicFile.WriteAllText(textPath, "first");
                AtomicFile.WriteAllText(textPath, "second");
                AtomicFile.WriteAllBytes(bytesPath, new byte[] { 1, 2, 3, 4 });

                Assert.That(File.ReadAllText(textPath), Is.EqualTo("second"));
                Assert.That(File.ReadAllBytes(bytesPath), Is.EqualTo(new byte[] { 1, 2, 3, 4 }));
                Assert.That(
                    Directory.GetFiles(directory, "*.tmp", SearchOption.TopDirectoryOnly),
                    Is.Empty);
            }
            finally
            {
                if (Directory.Exists(directory)) Directory.Delete(directory, true);
            }
        }
    }

    public sealed class SimulationTimerHudTests
    {
        [TestCase(0.0, "00:00.0")]
        [TestCase(7.25, "00:07.3")]
        [TestCase(59.99, "01:00.0")]
        [TestCase(110.0, "01:50.0")]
        [TestCase(3672.34, "61:12.3")]
        public void FormatElapsedUsesMinutesSecondsAndTenths(
            double seconds,
            string expected)
        {
            Assert.That(
                SimulationTimerHud.FormatElapsed(seconds),
                Is.EqualTo(expected));
        }

        [Test]
        public void InvalidElapsedTimeFailsClosedToZero()
        {
            Assert.That(
                SimulationTimerHud.FormatElapsed(double.NaN),
                Is.EqualTo("00:00.0"));
            Assert.That(
                SimulationTimerHud.FormatElapsed(double.PositiveInfinity),
                Is.EqualTo("00:00.0"));
            Assert.That(
                SimulationTimerHud.FormatElapsed(-1.0),
                Is.EqualTo("00:00.0"));
        }

        [Test]
        public void TimerPanelIsAnchoredAtTheUpperRightMargin()
        {
            Rect panel = SimulationTimerHud.TimerRect(1920f);
            Assert.That(panel.xMax, Is.EqualTo(1910f));
            Assert.That(panel.y, Is.EqualTo(10f));
            Assert.That(panel.width, Is.EqualTo(230f));
            Assert.That(panel.height, Is.EqualTo(70f));
        }
    }

    public sealed class SensorFrameWriterTests
    {
        [Serializable]
        sealed class Manifest
        {
            public string schema_version;
            public long frame_id;
            public string image_file;
            public string metadata_file;
            public double published_unix_s;
        }

        [Test]
        public void PublishFrameBundle_PublishesManifestForCompleteImmutablePair()
        {
            string directory = Path.Combine(
                Path.GetTempPath(),
                "TetheredTrackingEditModeTests",
                Guid.NewGuid().ToString("N"));
            try
            {
                byte[] image = { 7, 8, 9 };
                const string metadata = "{\"frame_id\":42}\n";

                SensorFrameWriter.PublishFrameBundle(
                    directory,
                    42,
                    image,
                    metadata,
                    1234.5);

                string manifestPath = Path.Combine(directory, "latest.json");
                Manifest manifest = JsonUtility.FromJson<Manifest>(File.ReadAllText(manifestPath));
                string imagePath = Path.Combine(directory, manifest.image_file);
                string metadataPath = Path.Combine(directory, manifest.metadata_file);
                Assert.That(manifest.schema_version, Is.EqualTo("tethered-frame-manifest/v1"));
                Assert.That(manifest.frame_id, Is.EqualTo(42));
                Assert.That(manifest.published_unix_s, Is.EqualTo(1234.5).Within(1e-9));
                Assert.That(File.Exists(imagePath), Is.True);
                Assert.That(File.Exists(metadataPath), Is.True);
                Assert.That(File.ReadAllBytes(imagePath), Is.EqualTo(image));
                Assert.That(File.ReadAllText(metadataPath), Is.EqualTo(metadata));
                Assert.That(
                    Directory.GetFiles(directory, "*.tmp", SearchOption.TopDirectoryOnly),
                    Is.Empty);
            }
            finally
            {
                if (Directory.Exists(directory)) Directory.Delete(directory, true);
            }
        }
    }

    public sealed class EvaluationOcclusionGeometryTests
    {
        [Test]
        public void BuildFromRenderers_ExcludesRuntimeRootsAndBuildsOnlyNeededProxy()
        {
            Mesh mesh = TriangleMesh();
            GameObject excludedRoot = new GameObject("ExcludedActor");
            GameObject excludedVisual = RendererObject(
                "ExcludedVisual",
                mesh,
                excludedRoot.transform);
            GameObject candidate = RendererObject("Candidate", mesh);
            GameObject existing = RendererObject("ExistingCollider", mesh);
            existing.AddComponent<BoxCollider>();
            GameObject geometryObject = new GameObject("EvaluationGeometry");
            EvaluationOcclusionGeometry geometry =
                geometryObject.AddComponent<EvaluationOcclusionGeometry>();

            try
            {
                geometry.BuildFromRenderers(
                    new[]
                    {
                        excludedVisual.GetComponent<MeshRenderer>(),
                        candidate.GetComponent<MeshRenderer>(),
                        existing.GetComponent<MeshRenderer>(),
                    },
                    excludedRoot.transform);

                Assert.That(geometry.ExcludedRendererCount, Is.EqualTo(1));
                Assert.That(geometry.CandidateRendererCount, Is.EqualTo(2));
                Assert.That(geometry.ProxyColliderCount, Is.EqualTo(1));
                Assert.That(geometry.ExistingColliderCount, Is.EqualTo(1));
                Assert.That(geometry.FailedProxyCount, Is.Zero);
                Assert.That(
                    candidate.GetComponentsInChildren<MeshCollider>(true),
                    Has.Length.EqualTo(1));
                Assert.That(
                    excludedRoot.GetComponentsInChildren<MeshCollider>(true),
                    Is.Empty);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(geometryObject);
                UnityEngine.Object.DestroyImmediate(excludedRoot);
                UnityEngine.Object.DestroyImmediate(candidate);
                UnityEngine.Object.DestroyImmediate(existing);
                UnityEngine.Object.DestroyImmediate(mesh);
            }
        }

        [Test]
        public void Build_RequiresExplicitNonNullExclusionRoots()
        {
            GameObject geometryObject = new GameObject("EvaluationGeometryValidation");
            try
            {
                EvaluationOcclusionGeometry geometry =
                    geometryObject.AddComponent<EvaluationOcclusionGeometry>();
                Assert.Throws<ArgumentException>(() => geometry.Build());
                Assert.Throws<ArgumentException>(() => geometry.Build((Transform)null));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(geometryObject);
            }
        }

        static GameObject RendererObject(string name, Mesh mesh, Transform parent = null)
        {
            var gameObject = new GameObject(name);
            if (parent != null) gameObject.transform.SetParent(parent, false);
            gameObject.AddComponent<MeshFilter>().sharedMesh = mesh;
            gameObject.AddComponent<MeshRenderer>();
            return gameObject;
        }

        static Mesh TriangleMesh()
        {
            var mesh = new Mesh
            {
                name = "EditModeTriangle",
                vertices = new[]
                {
                    Vector3.zero,
                    Vector3.right,
                    Vector3.up,
                },
                triangles = new[] { 0, 1, 2 },
            };
            mesh.RecalculateBounds();
            return mesh;
        }
    }

    /// <summary>
    /// P1-ENG-FRAME-001 Part T: scenario tether switch parsing (AC-1),
    /// existing-scenario bitwise regression (AC-3) and the versioned
    /// no-override default (AC-27). Never calls <c>ScenarioConfig.Load()</c>
    /// so the shared <c>runtime/</c> slot is not touched.
    /// </summary>
    public sealed class ScenarioTetherSwitchTests
    {
        const string DroneTail = "\"maximum_acceleration_mps2\": 4.0";
        const string ValidFence =
            "\"geofence_xz_m\": { \"min_x\": 110.0, \"max_x\": 190.0, \"min_z\": 50.0, \"max_z\": 130.0 }";
        const string InvertedFence =
            "\"geofence_xz_m\": { \"min_x\": 190.0, \"max_x\": 110.0, \"min_z\": 50.0, \"max_z\": 130.0 }";
        const string FenceWithoutHome =
            "\"geofence_xz_m\": { \"min_x\": 140.0, \"max_x\": 190.0, \"min_z\": 50.0, \"max_z\": 130.0 }";

        /// <summary>
        /// Every <c>config/scenario*.json</c> that existed before this work
        /// item (the K2 base); <c>scenario.untethered.json</c> is the only
        /// addition.
        /// </summary>
        static readonly string[] ExistingScenarioNames =
        {
            "scenario.default.json",
            "scenario.p1-detect-scouting.json",
            "scenario.p1-scene-004-d2-r5.json",
            "scenario.p1-scene-004-d2.json",
            "scenario.p1-scene-004-r5.json",
            "scenario.p1-scene-004.json",
            "scenario.p1-scene-006.json",
            "scenario.p1-vlm-survey-a1-p1-c1.json",
            "scenario.p1-vlm-survey-a2-p1-c1.json",
            "scenario.p1-vlm-survey-a3-p1-c1.json",
            "scenario.p1-vlm-survey-a4-p1-c1.json",
            "scenario.p1-vlm-survey-a6-p1-c1.json",
            "scenario.p1-vlm-survey-a7-p1-c1.json",
            "scenario.p1-vlm-survey-a9-p1-c1.json",
            "scenario.rate-study-20hz.json",
            "scenario.rate-study-5hz.json",
            "scenario.scene-validation.json",
        };

        static string DefaultJson() => File.ReadAllText(
            RuntimePaths.ProjectFile("config", "scenario.default.json"));

        static string WithDroneKeys(string extra)
        {
            string json = DefaultJson();
            int first = json.IndexOf(DroneTail, StringComparison.Ordinal);
            Assert.That(first, Is.GreaterThanOrEqualTo(0));
            Assert.That(json.IndexOf(DroneTail, first + 1, StringComparison.Ordinal), Is.EqualTo(-1));
            return json.Replace(DroneTail, DroneTail + ", " + extra);
        }

        [Test]
        public void ClosedFixtureSet_VerdictsMatchThePythonParser()
        {
            // Same names, inputs and verdicts as
            // tests/test_frame_tether_switch.py::TetherSwitchParserTests.
            var fixtures = new (string name, string json, bool accepted, bool tetherEnabled, bool hasFence)[]
            {
                ("missing", DefaultJson(), true, true, false),
                ("true", WithDroneKeys("\"tether_enabled\": true"), true, true, false),
                ("true+fence", WithDroneKeys("\"tether_enabled\": true, " + ValidFence), true, true, true),
                ("false+fence", WithDroneKeys("\"tether_enabled\": false, " + ValidFence), true, false, true),
                ("false+no-fence", WithDroneKeys("\"tether_enabled\": false"), false, false, false),
                ("false+inverted-fence", WithDroneKeys("\"tether_enabled\": false, " + InvertedFence), false, false, false),
                ("false+fence-without-home", WithDroneKeys("\"tether_enabled\": false, " + FenceWithoutHome), false, false, false),
            };
            foreach ((string name, string json, bool accepted, bool tetherEnabled, bool hasFence) in fixtures)
            {
                if (!accepted)
                {
                    Assert.Throws<InvalidOperationException>(
                        () => ScenarioConfig.FromJsonStrict(json), name);
                    continue;
                }
                ScenarioConfig config = ScenarioConfig.FromJsonStrict(json);
                Assert.That(config.drone.tether_enabled, Is.EqualTo(tetherEnabled), name);
                Assert.That(config.drone.geofence_xz_m != null, Is.EqualTo(hasFence), name);
                if (hasFence)
                {
                    Assert.That(config.drone.geofence_xz_m.min_x, Is.EqualTo(110f), name);
                    Assert.That(config.drone.geofence_xz_m.max_x, Is.EqualTo(190f), name);
                    Assert.That(config.drone.geofence_xz_m.min_z, Is.EqualTo(50f), name);
                    Assert.That(config.drone.geofence_xz_m.max_z, Is.EqualTo(130f), name);
                }
            }
        }

        [Test]
        public void ExistingScenarioFiles_NormalizeBitwiseAsBeforeAndStayTethered()
        {
            string directory = RuntimePaths.ProjectFile("config");
            var names = new System.Collections.Generic.List<string>();
            foreach (string path in Directory.GetFiles(directory, "scenario*.json"))
            {
                string name = Path.GetFileName(path);
                if (name != "scenario.untethered.json") names.Add(name);
            }
            names.Sort(StringComparer.Ordinal);
            CollectionAssert.AreEqual(ExistingScenarioNames, names);

            foreach (string name in names)
            {
                string json = File.ReadAllText(Path.Combine(directory, name));
                ScenarioConfig current = ScenarioConfig.FromJsonStrict(json);
                ScenarioConfig reference = JsonUtility.FromJson<ScenarioConfig>(json);
                LegacyNormalizeDroneGimbalSensor(reference);

                AssertSame(current.drone.initial_altitude_m, reference.drone.initial_altitude_m, name + " initial_altitude_m");
                AssertSame(current.drone.tether_length_m, reference.drone.tether_length_m, name + " tether_length_m");
                AssertSame(current.drone.minimum_altitude_m, reference.drone.minimum_altitude_m, name + " minimum_altitude_m");
                AssertSame(current.drone.maximum_altitude_m, reference.drone.maximum_altitude_m, name + " maximum_altitude_m");
                AssertSame(current.drone.maximum_speed_mps, reference.drone.maximum_speed_mps, name + " maximum_speed_mps");
                AssertSame(current.drone.maximum_acceleration_mps2, reference.drone.maximum_acceleration_mps2, name + " maximum_acceleration_mps2");
                AssertSame(current.gimbal.maximum_off_nadir_deg, reference.gimbal.maximum_off_nadir_deg, name + " maximum_off_nadir_deg");
                AssertSame(current.gimbal.slew_rate_deg_per_second, reference.gimbal.slew_rate_deg_per_second, name + " slew_rate_deg_per_second");
                Assert.That(current.sensor.width, Is.EqualTo(reference.sensor.width), name + " width");
                Assert.That(current.sensor.height, Is.EqualTo(reference.sensor.height), name + " height");
                AssertSame(current.sensor.vertical_fov_deg, reference.sensor.vertical_fov_deg, name + " vertical_fov_deg");
                AssertSame(current.sensor.capture_hz, reference.sensor.capture_hz, name + " capture_hz");
                Assert.That(current.sensor.jpeg_quality, Is.EqualTo(reference.sensor.jpeg_quality), name + " jpeg_quality");
                Assert.That(current.sensor.retained_frame_count, Is.EqualTo(reference.sensor.retained_frame_count), name + " retained_frame_count");
                Assert.That(current.drone.tether_enabled, Is.True, name + " tether_enabled");
                Assert.That(current.drone.geofence_xz_m, Is.Null, name + " geofence");
            }
        }

        [Test]
        public void VersionedDefault_IsTheUntetheredScenarioAndLoadOrderIsUnchanged()
        {
            string path = ScenarioConfig.VersionedDefaultPath;
            StringAssert.EndsWith("config/scenario.untethered.json", path.Replace('\\', '/'));
            Assert.That(File.Exists(path), Is.True);

            ScenarioConfig untethered = ScenarioConfig.FromJsonStrict(File.ReadAllText(path));
            Assert.That(untethered.scenario_id, Is.EqualTo("deterministic-loop-untethered"));
            Assert.That(untethered.drone.tether_enabled, Is.False);
            Assert.That(untethered.drone.geofence_xz_m, Is.Not.Null);
            Assert.That(untethered.drone.geofence_xz_m.min_x, Is.EqualTo(110f));
            Assert.That(untethered.drone.geofence_xz_m.max_x, Is.EqualTo(190f));
            Assert.That(untethered.drone.geofence_xz_m.min_z, Is.EqualTo(50f));
            Assert.That(untethered.drone.geofence_xz_m.max_z, Is.EqualTo(130f));
            Assert.That(untethered.drone.initial_altitude_m, Is.EqualTo(25f));
            Assert.That(untethered.drone.minimum_altitude_m, Is.EqualTo(8f));
            Assert.That(untethered.drone.maximum_altitude_m, Is.EqualTo(32f));

            ScenarioConfig legacyDefault = ScenarioConfig.FromJsonStrict(DefaultJson());
            Assert.That(legacyDefault.scenario_id, Is.EqualTo("deterministic-loop-default"));
            Assert.That(legacyDefault.drone.tether_enabled, Is.True);

            // Load() itself is not called (shared runtime/); the override-first
            // branch and the built-in fallback stay verbatim in the source.
            string source = File.ReadAllText(RuntimePaths.ProjectFile(
                "Assets", "TetheredTracking", "Scripts", "ScenarioConfig.cs"));
            StringAssert.Contains(
                "string path = File.Exists(runtimeOverride) ? runtimeOverride : projectDefault;", source);
            StringAssert.Contains("string runtimeOverride = RuntimePaths.File(\"scenario_config.json\");", source);
            StringAssert.Contains("string projectDefault = VersionedDefaultPath;", source);
            StringAssert.Contains("if (config == null) config = CreateDefault();", source);
        }

        // C1@K2返工 fixtures outside the AC-1 closed set. Same names, inserted
        // text and verdicts as tests/test_frame_tether_switch.py
        // (EXPLICIT_VALUE_FIXTURES / KEY_CONTEXT_FIXTURES); keep both tables
        // in sync.
        const string GimbalTail = "\"slew_rate_deg_per_second\": 120.0";
        const string AllNanFence =
            "\"geofence_xz_m\": { \"min_x\": NaN, \"max_x\": NaN, \"min_z\": NaN, \"max_z\": NaN }";

        static string WithGimbalKeys(string json, string extra)
        {
            int first = json.IndexOf(GimbalTail, StringComparison.Ordinal);
            Assert.That(first, Is.GreaterThanOrEqualTo(0));
            Assert.That(json.IndexOf(GimbalTail, first + 1, StringComparison.Ordinal), Is.EqualTo(-1));
            return json.Replace(GimbalTail, GimbalTail + ", " + extra);
        }

        static string Fence(string minX, string maxX, string minZ, string maxZ) =>
            "\"geofence_xz_m\": { \"min_x\": " + minX + ", \"max_x\": " + maxX
            + ", \"min_z\": " + minZ + ", \"max_z\": " + maxZ + " }";

        static (string name, string json, bool accepted, bool tetherEnabled, bool hasFence)[] ExplicitValueFixtures()
        {
            return new (string, string, bool, bool, bool)[]
            {
                ("fence-all-nan", WithDroneKeys(AllNanFence), false, false, false),
                ("true+fence-all-nan", WithDroneKeys("\"tether_enabled\": true, " + AllNanFence), false, false, false),
                ("false+fence-all-nan", WithDroneKeys("\"tether_enabled\": false, " + AllNanFence), false, false, false),
                ("true+fence-one-nan", WithDroneKeys("\"tether_enabled\": true, " + Fence("NaN", "190.0", "50.0", "130.0")), false, false, false),
                ("true+fence-infinity", WithDroneKeys("\"tether_enabled\": true, " + Fence("110.0", "Infinity", "50.0", "130.0")), false, false, false),
                ("true+fence-negative-infinity", WithDroneKeys("\"tether_enabled\": true, " + Fence("110.0", "190.0", "-Infinity", "130.0")), false, false, false),
                ("true+fence-overflow", WithDroneKeys("\"tether_enabled\": true, " + Fence("110.0", "190.0", "50.0", "1e999")), false, false, false),
                ("true+fence-all-bool", WithDroneKeys("\"tether_enabled\": true, " + Fence("true", "true", "false", "false")), false, false, false),
                ("true+fence-string-bound", WithDroneKeys("\"tether_enabled\": true, " + Fence("\"110\"", "190.0", "50.0", "130.0")), false, false, false),
                ("true+fence-null-bound", WithDroneKeys("\"tether_enabled\": true, " + Fence("null", "190.0", "50.0", "130.0")), false, false, false),
                ("true+fence-null", WithDroneKeys("\"tether_enabled\": true, \"geofence_xz_m\": null"), false, false, false),
                ("true+fence-array", WithDroneKeys("\"tether_enabled\": true, \"geofence_xz_m\": [110.0, 190.0, 50.0, 130.0]"), false, false, false),
                ("true+fence-missing-bound", WithDroneKeys("\"tether_enabled\": true, \"geofence_xz_m\": { \"min_x\": 110.0, \"max_x\": 190.0, \"min_z\": 50.0 }"), false, false, false),
                ("switch-number+fence", WithDroneKeys("\"tether_enabled\": 0, " + ValidFence), false, false, false),
                ("switch-string+fence", WithDroneKeys("\"tether_enabled\": \"false\", " + ValidFence), false, false, false),
                ("switch-null", WithDroneKeys("\"tether_enabled\": null"), false, false, false),
                ("true+fence-integer-bounds", WithDroneKeys("\"tether_enabled\": true, " + Fence("110", "190", "50", "130")), true, true, true),
            };
        }

        static (string name, string json, bool accepted, bool tetherEnabled, bool hasFence)[] KeyContextFixtures()
        {
            return new (string, string, bool, bool, bool)[]
            {
                ("keys-in-another-object",
                    WithGimbalKeys(DefaultJson(), "\"tether_enabled\": false, \"geofence_xz_m\": { \"note\": 1 }"),
                    true, true, false),
                ("keys-nested-in-drone",
                    WithDroneKeys("\"notes\": { \"tether_enabled\": false, \"geofence_xz_m\": { \"min_x\": NaN } }"),
                    true, true, false),
                ("keys-in-a-string",
                    WithDroneKeys("\"notes\": \"\\\"tether_enabled\\\": false, \\\"geofence_xz_m\\\": {}\""),
                    true, true, false),
                ("false+fence-in-another-object",
                    WithGimbalKeys(WithDroneKeys("\"tether_enabled\": false"), ValidFence),
                    false, false, false),
            };
        }

        /// <summary>
        /// Runs every fixture and reports all mismatches at once (refusal =
        /// <see cref="InvalidOperationException"/> from FromJsonStrict).
        /// </summary>
        static void AssertFixtureVerdicts(
            (string name, string json, bool accepted, bool tetherEnabled, bool hasFence)[] fixtures)
        {
            var mismatches = new System.Collections.Generic.List<string>();
            foreach ((string name, string json, bool accepted, bool tetherEnabled, bool hasFence) in fixtures)
            {
                ScenarioConfig config = null;
                Exception error = null;
                try { config = ScenarioConfig.FromJsonStrict(json); }
                catch (Exception exception) { error = exception; }
                if (!accepted)
                {
                    if (error == null)
                        mismatches.Add(name + ": accepted, expected refusal");
                    else if (!(error is InvalidOperationException))
                        mismatches.Add(name + ": refused with " + error.GetType().Name + ", expected InvalidOperationException");
                    continue;
                }
                if (error != null)
                {
                    mismatches.Add(name + ": refused (" + error.Message + "), expected acceptance");
                    continue;
                }
                if (config.drone.tether_enabled != tetherEnabled)
                    mismatches.Add(name + ": tether_enabled " + config.drone.tether_enabled);
                if ((config.drone.geofence_xz_m != null) != hasFence)
                    mismatches.Add(name + ": geofence present " + (config.drone.geofence_xz_m != null));
                if (hasFence && config.drone.geofence_xz_m != null
                    && !(config.drone.geofence_xz_m.min_x == 110f && config.drone.geofence_xz_m.max_x == 190f
                        && config.drone.geofence_xz_m.min_z == 50f && config.drone.geofence_xz_m.max_z == 130f))
                    mismatches.Add(name + ": geofence values differ");
            }
            Assert.That(mismatches, Is.Empty, string.Join("; ", mismatches));
        }

        [Test]
        public void ExplicitTetherKeyValues_AreRefusedLikeThePythonParser()
        {
            // C1@K2返工 (AC-1, IR-10/IR-13 rejected): an explicitly written
            // non-finite or non-numeric geofence is refused in both modes,
            // never silently treated as "no geofence"; a non-bool switch is
            // refused on both sides.
            AssertFixtureVerdicts(ExplicitValueFixtures());
        }

        [Test]
        public void TetherKeysOutsideTheDroneObject_MeanMissing()
        {
            // C1@K2返工 (AC-1): the section 3.1 keys are read from the direct
            // members of the root "drone" object only; the same names
            // anywhere else never change the "missing = tether on, no
            // geofence" verdict.
            AssertFixtureVerdicts(KeyContextFixtures());
        }

        [Test]
        public void SerializerPaths_NeverMaterialiseAGeofence()
        {
            // C1@K2返工 (AC-1/AC-3; replaces the K2补跑 all-NaN sentinel
            // regression, IR-13 rejected). JsonUtility cannot represent a
            // null member, so the geofence stays outside JsonUtility: a raw
            // parse or a ToJson round trip never yields one, and a non-null
            // geofence is always validated.

            // Raw JsonUtility parse (SceneAdjustmentConfigTests path).
            ScenarioConfig raw = JsonUtility.FromJson<ScenarioConfig>(DefaultJson());
            Assert.That(raw.drone.geofence_xz_m, Is.Null, "raw parse leaves the geofence absent");
            raw.Normalize();
            Assert.That(raw.drone.tether_enabled, Is.True);
            Assert.That(raw.drone.geofence_xz_m, Is.Null);

            // ToJson round trip of a fenceless config (Scene006 probe path).
            string written = JsonUtility.ToJson(ScenarioConfig.FromJsonStrict(DefaultJson()));
            StringAssert.DoesNotContain("geofence_xz_m", written, "round trip writes no geofence");
            ScenarioConfig roundTrip = ScenarioConfig.FromJsonStrict(written);
            Assert.That(roundTrip.drone.tether_enabled, Is.True);
            Assert.That(roundTrip.drone.geofence_xz_m, Is.Null);

            // Tether off: the serializer cannot carry the geofence, so a
            // round trip or a raw parse is refused (fail closed), never
            // silently untethered without a fence.
            string untetheredJson = File.ReadAllText(ScenarioConfig.VersionedDefaultPath);
            string offWritten = JsonUtility.ToJson(ScenarioConfig.FromJsonStrict(untetheredJson));
            StringAssert.DoesNotContain("geofence_xz_m", offWritten);
            InvalidOperationException offRoundTrip =
                Assert.Throws<InvalidOperationException>(() => ScenarioConfig.FromJsonStrict(offWritten));
            StringAssert.Contains("geofence_xz_m is required", offRoundTrip.Message);
            ScenarioConfig rawOff = JsonUtility.FromJson<ScenarioConfig>(untetheredJson);
            Assert.That(rawOff.drone.tether_enabled, Is.False);
            Assert.That(rawOff.drone.geofence_xz_m, Is.Null, "raw parse leaves the geofence absent");
            InvalidOperationException rawOffMissing =
                Assert.Throws<InvalidOperationException>(() => rawOff.Normalize());
            StringAssert.Contains("geofence_xz_m is required", rawOffMissing.Message);

            // No all-NaN "unset" sentinel: a non-null geofence is validated
            // with the tether on, whether wholly or partly unset.
            ScenarioConfig allNan = ScenarioConfig.FromJsonStrict(DefaultJson());
            allNan.drone.geofence_xz_m = new GeofenceScenarioConfig();
            InvalidOperationException allNanRefused =
                Assert.Throws<InvalidOperationException>(() => allNan.Normalize());
            StringAssert.Contains("geofence_xz_m.min_x must be finite", allNanRefused.Message);
            ScenarioConfig partial = ScenarioConfig.FromJsonStrict(DefaultJson());
            partial.drone.geofence_xz_m = new GeofenceScenarioConfig { max_x = 190f, min_z = 50f, max_z = 130f };
            InvalidOperationException partialRefused =
                Assert.Throws<InvalidOperationException>(() => partial.Normalize());
            StringAssert.Contains("geofence_xz_m.min_x must be finite", partialRefused.Message);
        }

        static void AssertSame(float actual, float expected, string label)
        {
            Assert.That(
                BitConverter.ToInt32(BitConverter.GetBytes(actual), 0),
                Is.EqualTo(BitConverter.ToInt32(BitConverter.GetBytes(expected), 0)),
                label);
        }

        // Verbatim copy of the pre-change ScenarioConfig.Normalize lines for
        // drone/gimbal/sensor (K2 base), applied to a raw JsonUtility parse.
        static void LegacyNormalizeDroneGimbalSensor(ScenarioConfig config)
        {
            ScenarioConfig fallback = ScenarioConfig.CreateDefault();
            if (config.drone == null) config.drone = fallback.drone;
            if (config.gimbal == null) config.gimbal = fallback.gimbal;
            if (config.sensor == null) config.sensor = fallback.sensor;
            DroneScenarioConfig drone = config.drone;
            GimbalScenarioConfig gimbal = config.gimbal;
            SensorScenarioConfig sensor = config.sensor;

            drone.tether_length_m = Positive(drone.tether_length_m, fallback.drone.tether_length_m);
            drone.minimum_altitude_m = Mathf.Clamp(
                Positive(drone.minimum_altitude_m, fallback.drone.minimum_altitude_m), 0.1f, drone.tether_length_m);
            drone.maximum_altitude_m = Mathf.Clamp(
                Positive(drone.maximum_altitude_m, fallback.drone.maximum_altitude_m),
                drone.minimum_altitude_m, drone.tether_length_m);
            drone.initial_altitude_m = Mathf.Clamp(
                Finite(drone.initial_altitude_m, fallback.drone.initial_altitude_m),
                drone.minimum_altitude_m, drone.maximum_altitude_m);
            drone.maximum_speed_mps = Positive(drone.maximum_speed_mps, fallback.drone.maximum_speed_mps);
            drone.maximum_acceleration_mps2 = Positive(
                drone.maximum_acceleration_mps2, fallback.drone.maximum_acceleration_mps2);

            gimbal.maximum_off_nadir_deg = Mathf.Clamp(
                Finite(gimbal.maximum_off_nadir_deg, fallback.gimbal.maximum_off_nadir_deg),
                0f, 89f);
            gimbal.slew_rate_deg_per_second = Positive(
                gimbal.slew_rate_deg_per_second, fallback.gimbal.slew_rate_deg_per_second);
            sensor.width = Mathf.Clamp(sensor.width, 64, 4096);
            sensor.height = Mathf.Clamp(sensor.height, 64, 4096);
            sensor.vertical_fov_deg = Mathf.Clamp(
                Finite(sensor.vertical_fov_deg, fallback.sensor.vertical_fov_deg),
                5f, 150f);
            sensor.capture_hz = Mathf.Clamp(
                Finite(sensor.capture_hz, fallback.sensor.capture_hz),
                0.1f, 60f);
            sensor.jpeg_quality = Mathf.Clamp(sensor.jpeg_quality, 1, 100);
            sensor.retained_frame_count = Mathf.Clamp(sensor.retained_frame_count, 4, 10000);
        }

        static float Finite(float value, float fallback)
        {
            return float.IsNaN(value) || float.IsInfinity(value) ? fallback : value;
        }

        static float Positive(float value, float fallback)
        {
            value = Finite(value, fallback);
            return value <= 0f ? fallback : value;
        }
    }

    /// <summary>P1-ENG-FRAME-001 AC-5: cable visual only with the tether on.</summary>
    public sealed class TetherBootstrapConstructionTests
    {
        [Test]
        public void TetherLine_IsCreatedOnlyWhenTetherEnabled_WithUnchangedParameters()
        {
            ScenarioConfig on = ScenarioConfig.FromJsonStrict(File.ReadAllText(
                RuntimePaths.ProjectFile("config", "scenario.default.json")));
            ScenarioConfig off = ScenarioConfig.FromJsonStrict(File.ReadAllText(
                RuntimePaths.ProjectFile("config", "scenario.untethered.json")));
            var drone = new GameObject("TetherBootstrapDrone");
            TetherLineVisual created = null;
            int before = UnityEngine.Object.FindObjectsByType<TetherLineVisual>(
                FindObjectsInactive.Include).Length;
            try
            {
                Assert.That(TetheredScenarioBootstrap.CreateTetherLine(off, drone.transform), Is.Null);
                Assert.That(
                    UnityEngine.Object.FindObjectsByType<TetherLineVisual>(FindObjectsInactive.Include).Length,
                    Is.EqualTo(before));

                created = TetheredScenarioBootstrap.CreateTetherLine(on, drone.transform);
                Assert.That(created, Is.Not.Null);
                Assert.That(created.gameObject.name, Is.EqualTo("TetherLine"));
                Assert.That(created.drone, Is.SameAs(drone.transform));
                Assert.That(created.anchor, Is.EqualTo(on.Anchor));
                Assert.That(created.GetComponent<LineRenderer>(), Is.Not.Null);
                Assert.That(
                    UnityEngine.Object.FindObjectsByType<TetherLineVisual>(FindObjectsInactive.Include).Length,
                    Is.EqualTo(before + 1));
            }
            finally
            {
                if (created != null) UnityEngine.Object.DestroyImmediate(created.gameObject);
                UnityEngine.Object.DestroyImmediate(drone);
            }
        }

        [Test]
        public void AnchorMarkerAndOcclusionRoots_DoNotDependOnTheTetherSwitch()
        {
            // CreateAnchor uses Destroy (Play only), so the unconditional
            // anchor marker and the unchanged OcclusionGeometry.Build inputs
            // are pinned on the source text; the reviewer diffs the rest.
            string source = File.ReadAllText(RuntimePaths.ProjectFile(
                "Assets", "TetheredTracking", "Scripts", "TetheredScenarioBootstrap.cs"));
            int awake = source.IndexOf("void Awake()", StringComparison.Ordinal);
            int awakeEnd = source.IndexOf("void ApplySceneAdjustments()", StringComparison.Ordinal);
            Assert.That(awake, Is.GreaterThanOrEqualTo(0));
            string awakeBody = source.Substring(awake, awakeEnd - awake);
            StringAssert.Contains("            CreateAnchor();\n            CreateDrone();", awakeBody.Replace("\r\n", "\n"));
            StringAssert.Contains("marker.name = \"TetherAnchor\";", source);
            StringAssert.Contains(
                "OcclusionGeometry.Build(anchorVisual, Drone.transform, Target.transform);", source);
            int anchorStart = source.IndexOf("void CreateAnchor()", StringComparison.Ordinal);
            int anchorEnd = source.IndexOf("void CreateDrone()", StringComparison.Ordinal);
            Assert.That(source.Substring(anchorStart, anchorEnd - anchorStart), Does.Not.Contain("tether_enabled"));
            int occlusionStart = source.IndexOf("void CreateEvaluationOcclusionGeometry()", StringComparison.Ordinal);
            int occlusionEnd = source.IndexOf("void CreateOverheadCamera()", StringComparison.Ordinal);
            Assert.That(source.Substring(occlusionStart, occlusionEnd - occlusionStart), Does.Not.Contain("tether"));
        }
    }

    /// <summary>
    /// P1-ENG-FRAME-001 AC-6: the frame metadata field set, types and unit
    /// suffixes are unchanged (tethered-sensor-frame/v3).
    /// </summary>
    public sealed class FrameProtocolInvariantTests
    {
        [Test]
        public void SensorFrameMetadataV3_FieldSetIsUnchanged()
        {
            var actual = new System.Collections.Generic.List<string>();
            foreach (System.Reflection.FieldInfo field in typeof(SensorFrameWriter.FrameMetadataV3).GetFields(
                System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance))
                actual.Add(field.Name + ":" + field.FieldType.Name);
            actual.Sort(StringComparer.Ordinal);
            var expected = new System.Collections.Generic.List<string>
            {
                "camera_forward_world:Single[]",
                "camera_position_world_m:Single[]",
                "camera_right_world:Single[]",
                "camera_rotation_xyzw:Single[]",
                "camera_up_world:Single[]",
                "capture_monotonic_clock_id:String",
                "capture_monotonic_s:Double",
                "capture_unix_s:Double",
                "frame_id:Int64",
                "gimbal_saturated:Boolean",
                "height:Int32",
                "horizontal_fov_deg:Single",
                "intrinsics_px:CameraIntrinsics",
                "scenario_id:String",
                "schema_version:String",
                "simulation_time_s:Single",
                "tether_saturated:Boolean",
                "vertical_fov_deg:Single",
                "width:Int32",
            };
            expected.Sort(StringComparer.Ordinal);
            CollectionAssert.AreEqual(expected, actual);

            var intrinsics = new System.Collections.Generic.List<string>();
            foreach (System.Reflection.FieldInfo field in typeof(SensorFrameWriter.CameraIntrinsics).GetFields(
                System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance))
                intrinsics.Add(field.Name + ":" + field.FieldType.Name);
            intrinsics.Sort(StringComparer.Ordinal);
            CollectionAssert.AreEqual(
                new[] { "cx:Single", "cy:Single", "fx:Single", "fy:Single" }, intrinsics);
            Assert.That(
                new SensorFrameWriter.FrameMetadataV3().schema_version,
                Is.EqualTo("tethered-sensor-frame/v3"));
        }
    }
}
