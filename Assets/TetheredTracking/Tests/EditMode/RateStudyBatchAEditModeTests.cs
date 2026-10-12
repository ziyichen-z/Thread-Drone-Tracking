using System;
using System.IO;
using System.Text;
using NUnit.Framework;
using UnityEngine;

namespace TetheredTracking.Tests
{
    public sealed class RateStudyProtocolTests
    {
        [Test]
        public void SensorMetadataV2_ContainsFiniteMonotonicCaptureTime()
        {
            var metadata = new SensorFrameWriter.FrameMetadataV2
            {
                scenario_id = "scenario",
                frame_id = 7,
                simulation_time_s = 1.5f,
                capture_unix_s = 1000.0,
                capture_monotonic_s = 42.25,
            };

            string json = JsonUtility.ToJson(metadata);

            StringAssert.Contains("\"schema_version\":\"tethered-sensor-frame/v2\"", json);
            StringAssert.Contains("\"capture_monotonic_s\":42.25", json);
            var frame = new SensorFrameInfo(7, 1.5f, 0.05f, 1000.0, 42.25);
            Assert.That(frame.CaptureMonotonicSeconds, Is.EqualTo(42.25));
        }

        [Test]
        public void SensorMetadataV3_ContainsSharedHostMonotonicClockIdentity()
        {
            string json = JsonUtility.ToJson(new SensorFrameWriter.FrameMetadataV3
            {
                scenario_id = "ordinary-scenario",
                frame_id = 3,
                capture_unix_s = 1000.0,
                capture_monotonic_s = 41.5,
            });

            StringAssert.Contains("\"schema_version\":\"tethered-sensor-frame/v3\"", json);
            StringAssert.Contains("\"capture_monotonic_s\":41.5", json);
            StringAssert.Contains(
                "\"capture_monotonic_clock_id\":\"system-stopwatch/v1\"",
                json);
        }

        [Test]
        public void SharedHostMonotonicClock_IsFiniteNonNegativeAndAdvances()
        {
            double first = SensorFrameWriter.HostMonotonicSeconds();
            double second = SensorFrameWriter.HostMonotonicSeconds();

            Assert.That(double.IsNaN(first) || double.IsInfinity(first), Is.False);
            Assert.That(first, Is.GreaterThanOrEqualTo(0.0));
            Assert.That(second, Is.GreaterThanOrEqualTo(first));
        }

        [Test]
        public void Release_AcceptsByteBoundReadyAndWritesCompleteAck()
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            byte[] ready = fixture.Ready(lastProcessedFrameId: 41);
            byte[] command = fixture.Release("release-1", ready);

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                currentFrameId: 42,
                unixSeconds: 1001.0,
                monotonicSeconds: 501.0,
                simulationSeconds: 11.0);

            Assert.That(accepted, Is.True);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Released));
            Assert.That(fixture.Target.MotionEnabled, Is.True);
            Assert.That(
                File.ReadAllBytes(Path.Combine(fixture.Root, "release_command.accepted.json")),
                Is.EqualTo(command));
            ReleaseAckDocument ack = JsonUtility.FromJson<ReleaseAckDocument>(
                File.ReadAllText(Path.Combine(fixture.Root, "release_ack.json")));
            Assert.That(ack.release_command_sha256, Is.EqualTo(RateStudyProtocol.Sha256(command)));
            Assert.That(ack.ready_sha256, Is.EqualTo(RateStudyProtocol.Sha256(ready)));
            Assert.That(ack.current_frame_id, Is.EqualTo(42));
            Assert.That(ack.last_processed_frame_id, Is.EqualTo(41));
            Assert.That(ack.accepted_backlog_frames, Is.EqualTo(1));
            Assert.That(ack.ready_seq, Is.EqualTo(20));
            Assert.That(ack.processed_frame_count, Is.EqualTo(20));
            Assert.That(ack.release_monotonic_s, Is.EqualTo(501.0));
        }

        [TestCase(42, 43)]
        [TestCase(42, 40)]
        public void Release_RejectsFutureOrMoreThanOneFrameBacklog(
            long currentFrameId,
            long lastProcessedFrameId)
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            byte[] command = fixture.Release(
                "bad-backlog",
                fixture.Ready(lastProcessedFrameId));

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                currentFrameId);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            Assert.That(fixture.Target.MotionEnabled, Is.False);
            ExperimentStateDocument state = JsonUtility.FromJson<ExperimentStateDocument>(
                File.ReadAllText(Path.Combine(fixture.Root, "experiment_state.json")));
            Assert.That(state.last_rejection_code, Is.EqualTo("backlog_out_of_range"));
            Assert.That(File.Exists(Path.Combine(fixture.Root, "release_ack.json")), Is.False);
        }

        [Test]
        public void Release_ReplayAfterReleasedIsPersistedWithoutAbort()
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            byte[] command = fixture.Release("release-1", fixture.Ready(42));
            Assert.That(fixture.Controller.ProcessCommandForTests(command, 42), Is.True);

            Assert.That(fixture.Controller.ProcessCommandForTests(command, 42), Is.False);

            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Released));
            ExperimentStateDocument state = JsonUtility.FromJson<ExperimentStateDocument>(
                File.ReadAllText(Path.Combine(fixture.Root, "experiment_state.json")));
                Assert.That(state.rejected_release_commands, Is.EqualTo(1));
                Assert.That(state.last_rejection_code, Is.EqualTo("release_replay_after_released"));
                Assert.That(
                    Directory.GetFiles(
                        Path.Combine(fixture.Root, "experiment_rejections"),
                        "*.json"),
                    Has.Length.EqualTo(1));
        }

        [Test]
        public void Release_FatalIdentityMismatchAborts()
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            byte[] ready = fixture.Ready(42);
            ExperimentControlDocument command = fixture.ReleaseDocument("wrong-run", ready);
            command.run_id = "another-run";

            bool accepted = fixture.Controller.ProcessCommandForTests(
                ControllerFixture.JsonBytes(command),
                42);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Aborted));
            Assert.That(fixture.Target.MotionEnabled, Is.False);
        }

        [Test]
        public void Release_FatalReadyIdentityMismatchAborts()
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            TrackerReadyDocument ready = JsonUtility.FromJson<TrackerReadyDocument>(
                Encoding.UTF8.GetString(fixture.Ready(42)));
            ready.tracker_identity_sha256 = new string('c', 64);
            byte[] readyBytes = ControllerFixture.JsonBytes(ready);

            bool accepted = fixture.Controller.ProcessCommandForTests(
                fixture.Release("bad-ready-identity", readyBytes),
                42);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Aborted));
        }

        [Test]
        public void Release_RejectsReadyBeforeFrozenWarmup()
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            TrackerReadyDocument ready = JsonUtility.FromJson<TrackerReadyDocument>(
                Encoding.UTF8.GetString(fixture.Ready(42)));
            ready.seq = 19;
            ready.processed_frame_count = 19;
            byte[] readyBytes = ControllerFixture.JsonBytes(ready);

            bool accepted = fixture.Controller.ProcessCommandForTests(
                fixture.Release("early-ready", readyBytes),
                42);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            ExperimentStateDocument state = JsonUtility.FromJson<ExperimentStateDocument>(
                File.ReadAllText(Path.Combine(fixture.Root, "experiment_state.json")));
            Assert.That(state.last_rejection_code, Is.EqualTo("invalid_ready_evidence"));
        }

        [Test]
        public void Release_RejectsTamperedReadyBytesWithoutChangingState()
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            byte[] ready = fixture.Ready(42);
            ExperimentControlDocument command = fixture.ReleaseDocument("tampered", ready);
            command.ready_sha256 = new string('f', 64);

            bool accepted = fixture.Controller.ProcessCommandForTests(
                ControllerFixture.JsonBytes(command),
                42);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
        }

        [Test]
        public void Release_RejectsNonFiniteUnityClock()
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            byte[] command = fixture.Release("bad-clock", fixture.Ready(42));

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                42,
                monotonicSeconds: double.NaN);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            Assert.That(File.Exists(Path.Combine(fixture.Root, "release_ack.json")), Is.False);
        }

        [Test]
        public void ExplicitAbort_IsTheOnlyNonIdentityCommandThatAborts()
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            ExperimentControlDocument command = fixture.ReleaseDocument(
                "abort-1",
                fixture.Ready(42));
            command.schema_version = RateStudyProtocol.AbortCommandSchema;
            command.command_type = "abort";
            command.ready_json_base64 = null;
            command.ready_sha256 = null;

            bool handled = fixture.Controller.ProcessCommandForTests(
                ControllerFixture.JsonBytes(command),
                42);

            Assert.That(handled, Is.True);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Aborted));
        }

        [Test]
        public void Hold_SuppressesControlAndTargetMotionForSimulatedSixtySeconds()
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            Vector3 heldPosition = fixture.Target.transform.position;

            Assert.That(fixture.Controller.AuthorizeControl("gimbal", 17), Is.False);
            for (int index = 0; index < 60; index++) fixture.Target.Step(1f);

            Assert.That(fixture.Target.transform.position, Is.EqualTo(heldPosition));
            ExperimentStateDocument state = JsonUtility.FromJson<ExperimentStateDocument>(
                File.ReadAllText(Path.Combine(fixture.Root, "experiment_state.json")));
            Assert.That(state.rejected_control_commands, Is.EqualTo(1));
            Assert.That(state.last_rejection_channel, Is.EqualTo("gimbal"));

            byte[] command = fixture.Release("release-after-hold", fixture.Ready(42));
            Assert.That(fixture.Controller.ProcessCommandForTests(command, 42), Is.True);
            fixture.Target.Step(1f);
            Assert.That(fixture.Target.transform.position, Is.Not.EqualTo(heldPosition));
        }

        [Test]
        public void PrepareRuntimeSlots_RemovesEveryTransactionSlot()
        {
            string root = ControllerFixture.CreateDirectory();
            try
            {
                string[] names =
                {
                    "tracker_ready.json",
                    "experiment_control.json",
                    "release_ack.json",
                    "release_command.accepted.json",
                    "experiment_state.json",
                };
                foreach (string name in names)
                    File.WriteAllText(Path.Combine(root, name), "stale");
                Directory.CreateDirectory(Path.Combine(root, "experiment_rejections"));
                File.WriteAllText(
                    Path.Combine(root, "experiment_rejections", "rejection_000001.json"),
                    "stale");
                Assert.That(RateStudyExperimentController.HasStaleRuntimeSlot(root), Is.True);

                RateStudyExperimentController.PrepareRuntimeSlots(root);

                foreach (string name in names)
                    Assert.That(File.Exists(Path.Combine(root, name)), Is.False, name);
                Assert.That(
                    Directory.Exists(Path.Combine(root, "experiment_rejections")),
                    Is.False);
                Assert.That(RateStudyExperimentController.HasStaleRuntimeSlot(root), Is.False);
            }
            finally
            {
                if (Directory.Exists(root)) Directory.Delete(root, true);
            }
        }

        [TestCase("study")]
        [TestCase("tracker")]
        [TestCase("run_scenario")]
        [TestCase("hash")]
        public void InvalidSessionIdentity_BlocksInHoldWithoutInventingAbortTransition(
            string invalidDimension)
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            RateStudySession invalid = ControllerFixture.CloneSession(fixture.Session);
            switch (invalidDimension)
            {
                case "study":
                    invalid.study_id = "another-study";
                    break;
                case "tracker":
                    invalid.tracker_id = "csrt";
                    break;
                case "run_scenario":
                    invalid.scenario_id = "rate-study-5hz";
                    break;
                case "hash":
                    invalid.model_identity_sha256 = "not-a-sha256";
                    break;
                default:
                    Assert.Fail("Unexpected invalid identity dimension.");
                    break;
            }
            GameObject controllerObject = new GameObject("InvalidSessionController");
            try
            {
                RateStudyExperimentController controller =
                    controllerObject.AddComponent<RateStudyExperimentController>();
                controller.InitializeForTests(invalid, fixture.Root, fixture.Target);

                Assert.That(controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
                Assert.That(controller.ControlEnabled, Is.False);
                Assert.That(controller.MeasurementEnabled, Is.False);
                Assert.That(fixture.Target.MotionEnabled, Is.False);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(controllerObject);
            }
        }

        [Test]
        public void ProductionInitialize_NoSessionPreservesOrdinaryPassthrough()
        {
            string root = ControllerFixture.CreateDirectory();
            GameObject controllerObject = new GameObject("NoSessionController");
            try
            {
                RateStudyExperimentController controller =
                    controllerObject.AddComponent<RateStudyExperimentController>();
                controller.Initialize(
                    ScenarioConfig.CreateDefault(),
                    null,
                    null,
                    root);

                Assert.That(controller.IsActive, Is.False);
                Assert.That(controller.ControlEnabled, Is.True);
                Assert.That(controller.MeasurementEnabled, Is.True);
                Assert.That(
                    File.Exists(Path.Combine(root, "experiment_state.json")),
                    Is.False);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(controllerObject);
                if (Directory.Exists(root)) Directory.Delete(root, true);
            }
        }

        [TestCase(false, "invalid_session_scenario")]
        [TestCase(true, "stale_runtime_slot")]
        public void ProductionInitialize_InvalidScenarioOrStaleSlotBlocksHold(
            bool createStaleSlot,
            string expectedCode)
        {
            string root = ControllerFixture.CreateDirectory();
            GameObject controllerObject = new GameObject("BlockedProductionController");
            try
            {
                RateStudySession session = ControllerFixture.CreateSession();
                File.WriteAllText(
                    Path.Combine(root, "rate_study_session.json"),
                    JsonUtility.ToJson(session, true) + "\n");
                if (createStaleSlot)
                    File.WriteAllText(Path.Combine(root, "tracker_ready.json"), "{}\n");
                ScenarioConfig config = ScenarioConfig.CreateDefault();
                config.scenario_id = createStaleSlot
                    ? session.scenario_id
                    : "different-scenario";

                RateStudyExperimentController controller =
                    controllerObject.AddComponent<RateStudyExperimentController>();
                controller.Initialize(config, null, null, root);

                Assert.That(controller.IsActive, Is.True);
                Assert.That(controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
                Assert.That(controller.ControlEnabled, Is.False);
                Assert.That(controller.MeasurementEnabled, Is.False);
                ExperimentStateDocument state = JsonUtility.FromJson<ExperimentStateDocument>(
                    File.ReadAllText(Path.Combine(root, "experiment_state.json")));
                Assert.That(state.last_rejection_code, Is.EqualTo(expectedCode));
                Assert.That(state.last_rejection_channel, Is.EqualTo("session_initialization"));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(controllerObject);
                if (Directory.Exists(root)) Directory.Delete(root, true);
            }
        }

        [Test]
        public void ProductionInitialize_ValidSessionEntersHoldFromDisk()
        {
            string root = ControllerFixture.CreateDirectory();
            GameObject controllerObject = new GameObject("ValidProductionController");
            try
            {
                RateStudySession session = ControllerFixture.CreateSession();
                File.WriteAllText(
                    Path.Combine(root, "rate_study_session.json"),
                    JsonUtility.ToJson(session, true) + "\n");
                ScenarioConfig config = ScenarioConfig.CreateDefault();
                config.scenario_id = session.scenario_id;

                RateStudyExperimentController controller =
                    controllerObject.AddComponent<RateStudyExperimentController>();
                controller.Initialize(config, null, null, root);

                Assert.That(controller.IsActive, Is.True);
                Assert.That(controller.Session.run_id, Is.EqualTo(session.run_id));
                Assert.That(controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
                Assert.That(controller.ControlEnabled, Is.False);
                ExperimentStateDocument state = JsonUtility.FromJson<ExperimentStateDocument>(
                    File.ReadAllText(Path.Combine(root, "experiment_state.json")));
                Assert.That(state.state, Is.EqualTo("HOLD"));
                Assert.That(state.last_rejection_code, Is.Null.Or.Empty);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(controllerObject);
                if (Directory.Exists(root)) Directory.Delete(root, true);
            }
        }

        [Test]
        public void Evaluator_ExcludesHoldFramesAndStartsAtRelease()
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            GameObject evaluatorObject = new GameObject("GatedEvaluator");
            try
            {
                CoverageEvaluator evaluator = evaluatorObject.AddComponent<CoverageEvaluator>();
                evaluator.ConfigureAggregationForTests(20f, 2048, 0.3f);
                var truth = new NormalizedBoundingBox
                {
                    x = 0.2f,
                    y = 0.2f,
                    width = 0.2f,
                    height = 0.2f,
                };

                evaluator.RecordGatedAggregationFrameForTests(
                    fixture.Controller,
                    1,
                    0.05f,
                    0.05f,
                    true,
                    truth);
                Assert.That(evaluator.AggregationForTests().SensorFrames, Is.Zero);

                Assert.That(
                    fixture.Controller.ProcessCommandForTests(
                        fixture.Release("release-evaluator", fixture.Ready(42)),
                        42),
                    Is.True);
                evaluator.RecordGatedAggregationFrameForTests(
                    fixture.Controller,
                    43,
                    0.10f,
                    0.05f,
                    true,
                    truth);
                Assert.That(evaluator.AggregationForTests().SensorFrames, Is.EqualTo(1));
                Assert.That(
                    evaluator.AggregationForTests().TotalDuration,
                    Is.EqualTo(0.05f).Within(1e-6f));
                evaluator.RecordGatedAggregationFrameForTests(
                    fixture.Controller,
                    42,
                    0.10f,
                    0.05f,
                    true,
                    truth);
                Assert.That(evaluator.AggregationForTests().SensorFrames, Is.EqualTo(1));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(evaluatorObject);
            }
        }

        [Test]
        public void Evaluator_Rate2AcceptedFramesRequireImmediateMetricsPublication()
        {
            using ControllerFixture fixture = ControllerFixture.Create();

            Assert.That(
                CoverageEvaluator.RequiresImmediateMetricsWrite(
                    fixture.Controller,
                    41),
                Is.False,
                "HOLD frames must not publish measurement metrics");
            Assert.That(
                fixture.Controller.ProcessCommandForTests(
                    fixture.Release("release-metrics-cadence", fixture.Ready(42)),
                    42),
                Is.True);
            Assert.That(
                CoverageEvaluator.RequiresImmediateMetricsWrite(
                    fixture.Controller,
                    42),
                Is.False,
                "the release boundary frame itself is not a measurement frame");
            Assert.That(
                CoverageEvaluator.RequiresImmediateMetricsWrite(
                    fixture.Controller,
                    43),
                Is.True,
                "the first accepted RATE-002 frame must refresh metrics immediately");
            Assert.That(
                CoverageEvaluator.RequiresImmediateMetricsWrite(null, 43),
                Is.False,
                "ordinary sessions retain the existing periodic publication cadence");
        }

        [Test]
        public void Evaluator_PublicElapsedTimeExcludesLongHoldAndUsesAcceptedDuration()
        {
            using ControllerFixture fixture = ControllerFixture.Create();
            GameObject evaluatorObject = new GameObject("ReleaseElapsedEvaluator");
            try
            {
                CoverageEvaluator evaluator = evaluatorObject.AddComponent<CoverageEvaluator>();
                evaluator.ConfigureAggregationForTests(20f, 2048, 0.3f);
                var truth = new NormalizedBoundingBox
                {
                    x = 0.2f,
                    y = 0.2f,
                    width = 0.2f,
                    height = 0.2f,
                };

                evaluator.RecordGatedAggregationFrameForTests(
                    fixture.Controller,
                    41,
                    1000.0f,
                    0.05f,
                    true,
                    truth);
                Assert.That(
                    fixture.Controller.ProcessCommandForTests(
                        fixture.Release("release-after-long-hold", fixture.Ready(42)),
                        42,
                        simulationSeconds: 1000.0),
                    Is.True);
                evaluator.RecordGatedAggregationFrameForTests(
                    fixture.Controller,
                    43,
                    1000.05f,
                    0.05f,
                    true,
                    truth);
                evaluator.RecordGatedAggregationFrameForTests(
                    fixture.Controller,
                    44,
                    1000.10f,
                    0.05f,
                    true,
                    truth);

                ElapsedMetricsDocument metrics =
                    JsonUtility.FromJson<ElapsedMetricsDocument>(
                        evaluator.MetricsJsonForTests());
                Assert.That(
                    metrics.elapsed_simulation_s,
                    Is.EqualTo(0.10f).Within(1e-6f));
                Assert.That(
                    evaluator.AggregationForTests().SensorFrames,
                    Is.EqualTo(2));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(evaluatorObject);
            }
        }

        [Serializable]
        sealed class ElapsedMetricsDocument
        {
            public float elapsed_simulation_s;
        }
    }

    public sealed class RateStudyScoutingTests
    {
        static readonly Vector3[] SquareRoute =
        {
            new(0f, 0f, 0f),
            new(1f, 0f, 0f),
            new(1f, 0f, 1f),
            new(0f, 0f, 1f),
        };

        [Test]
        public void CandidateGrid_IsExactHalfMeterSetAndExcludesWrapEndpoint()
        {
            float[] distances = RateStudyScouting.CandidateDistances(SquareRoute, 0.5f);

            Assert.That(RateStudyScouting.ClosedRoutePerimeter(SquareRoute), Is.EqualTo(4f));
            Assert.That(distances, Is.EqualTo(new[] { 0f, 0.5f, 1f, 1.5f, 2f, 2.5f, 3f, 3.5f }));
            Assert.That(distances, Has.None.EqualTo(4f));
        }

        [Test]
        public void RouteSampling_InterpolatesClosingSegmentDeterministically()
        {
            RateStudyScouting.RouteSample sample =
                RateStudyScouting.SampleClosedRoute(SquareRoute, 3.5f);

            Assert.That(sample.Position, Is.EqualTo(new Vector3(0f, 0f, 0.5f)));
            Assert.That(sample.NextWaypointIndex, Is.Zero);
        }

        [Test]
        public void Qualification_UsesMinimumAcrossAllActiveDistractors()
        {
            NormalizedBoundingBox target = Box(0.3f, 0.3f, 0.2f, 0.2f);
            NormalizedBoundingBox far = Box(0.8f, 0.8f, 0.1f, 0.1f);
            NormalizedBoundingBox nearOverlap = Box(0.35f, 0.35f, 0.2f, 0.2f);

            RateStudyScouting.Separation separation =
                RateStudyScouting.NearestDistractor(
                    target,
                    new[] { far, nearOverlap },
                    640,
                    480);

            Assert.That(separation.HasDistractor, Is.True);
            Assert.That(separation.NearestIoU, Is.GreaterThan(0f));
            Assert.That(RateStudyScouting.Qualifies(target, separation, 640), Is.False);
        }

        [Test]
        public void Qualification_RequiresMarginAndOneTargetWidthSeparation()
        {
            NormalizedBoundingBox centered = Box(0.3f, 0.3f, 0.2f, 0.2f);
            var tooNear = new RateStudyScouting.Separation(127f, 0f, true);
            var exactlyOneWidth = new RateStudyScouting.Separation(128f, 0f, true);
            NormalizedBoundingBox nearEdge = Box(0.1f, 0.3f, 0.2f, 0.2f);

            Assert.That(RateStudyScouting.Qualifies(centered, tooNear, 640), Is.False);
            Assert.That(RateStudyScouting.Qualifies(centered, exactlyOneWidth, 640), Is.True);
            Assert.That(
                RateStudyScouting.Qualifies(nearEdge, exactlyOneWidth, 640),
                Is.False);
        }

        [Test]
        public void Projection_RemainsUnclippedSoMarginCanRejectOffFrameCandidates()
        {
            GameObject cameraObject = new GameObject("ScoutingCamera");
            GameObject rendererObject = GameObject.CreatePrimitive(PrimitiveType.Cube);
            try
            {
                Camera camera = cameraObject.AddComponent<Camera>();
                camera.enabled = false;
                camera.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
                rendererObject.transform.position = new Vector3(7f, 0f, 5f);

                NormalizedBoundingBox box = RateStudyScouting.ProjectRenderersUnclipped(
                    camera,
                    rendererObject.GetComponentsInChildren<Renderer>());

                Assert.That(box, Is.Not.Null);
                Assert.That(box.x + box.width, Is.GreaterThan(1f));
                Assert.That(RateStudyScouting.FrameMargin(box), Is.LessThan(0f));
                Assert.That(
                    RateStudyScouting.Qualifies(
                        box,
                        new RateStudyScouting.Separation(-1f, 0f, false),
                        640),
                    Is.False);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(cameraObject);
                UnityEngine.Object.DestroyImmediate(rendererObject);
            }
        }

        static NormalizedBoundingBox Box(float x, float y, float width, float height) =>
            new()
            {
                x = x,
                y = y,
                width = width,
                height = height,
            };
    }

    sealed class ControllerFixture : IDisposable
    {
        internal string Root { get; private set; }
        internal RateStudySession Session { get; private set; }
        internal RateStudyExperimentController Controller { get; private set; }
        internal LoopTargetVehicle Target { get; private set; }

        internal static ControllerFixture Create()
        {
            var fixture = new ControllerFixture
            {
                Root = CreateDirectory(),
                Session = CreateSession(),
            };
            GameObject targetObject = new GameObject("RateStudyTarget");
            fixture.Target = targetObject.AddComponent<LoopTargetVehicle>();
            fixture.Target.Configure(
                "target-0",
                new[]
                {
                    Vector3.zero,
                    new Vector3(10f, 0f, 0f),
                    new Vector3(10f, 0f, 10f),
                },
                2f);
            GameObject controllerObject = new GameObject("RateStudyController");
            fixture.Controller = controllerObject.AddComponent<RateStudyExperimentController>();
            fixture.Controller.InitializeForTests(
                fixture.Session,
                fixture.Root,
                fixture.Target);
            return fixture;
        }

        internal static RateStudySession CreateSession() =>
            new()
            {
                study_id = "P1-M2-RATE-002-B2",
                run_id = "rs2-r20-follow-1",
                scenario_id = "rate-study-20hz",
                tracker_id = "nanotrack-v2",
                tracker_identity_sha256 = new string('a', 64),
                model_identity_sha256 = new string('c', 64),
                init_frame_id = 140,
                init_image_sha256 = new string('b', 64),
                hold_route_s_m = 0f,
                minimum_ready_seq = 20,
                minimum_processed_frames = 20,
            };

        internal static RateStudySession CloneSession(RateStudySession source) =>
            JsonUtility.FromJson<RateStudySession>(JsonUtility.ToJson(source));

        internal byte[] Ready(long lastProcessedFrameId)
        {
            var ready = new TrackerReadyDocument
            {
                schema_version = RateStudyProtocol.ReadySchema,
                state = "TRACKING",
                study_id = Session.study_id,
                run_id = Session.run_id,
                scenario_id = Session.scenario_id,
                tracker_id = Session.tracker_id,
                tracker_identity_sha256 = Session.tracker_identity_sha256,
                model_identity_sha256 = Session.model_identity_sha256,
                init_frame_id = Session.init_frame_id,
                init_image_sha256 = Session.init_image_sha256,
                last_processed_frame_id = lastProcessedFrameId,
                processed_frame_count = 20,
                seq = 20,
                publisher_monotonic_s = 123.0,
            };
            return JsonBytes(ready);
        }

        internal ExperimentControlDocument ReleaseDocument(string commandId, byte[] ready)
        {
            return new ExperimentControlDocument
            {
                schema_version = RateStudyProtocol.ReleaseCommandSchema,
                channel = "experiment_control",
                command_type = "release",
                command_id = commandId,
                study_id = Session.study_id,
                run_id = Session.run_id,
                scenario_id = Session.scenario_id,
                tracker_id = Session.tracker_id,
                tracker_identity_sha256 = Session.tracker_identity_sha256,
                model_identity_sha256 = Session.model_identity_sha256,
                init_frame_id = Session.init_frame_id,
                init_image_sha256 = Session.init_image_sha256,
                ready_json_base64 = Convert.ToBase64String(ready),
                ready_sha256 = RateStudyProtocol.Sha256(ready),
            };
        }

        internal byte[] Release(string commandId, byte[] ready) =>
            JsonBytes(ReleaseDocument(commandId, ready));

        internal static byte[] JsonBytes(object document) =>
            Encoding.UTF8.GetBytes(JsonUtility.ToJson(document, true) + "\n");

        internal static string CreateDirectory()
        {
            string root = Path.Combine(
                Path.GetTempPath(),
                "RateStudyBatchAEditModeTests",
                Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(root);
            return root;
        }

        public void Dispose()
        {
            if (Controller != null) UnityEngine.Object.DestroyImmediate(Controller.gameObject);
            if (Target != null) UnityEngine.Object.DestroyImmediate(Target.gameObject);
            if (Directory.Exists(Root)) Directory.Delete(Root, true);
        }
    }
}
