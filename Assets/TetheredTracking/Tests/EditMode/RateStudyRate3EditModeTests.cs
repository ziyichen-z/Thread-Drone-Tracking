using System;
using System.IO;
using System.Text;
using NUnit.Framework;
using UnityEngine;

namespace TetheredTracking.Tests
{
    public sealed class RateStudyRate3SessionValidationTests
    {
        [Test]
        public void ClockSmokeSession_ValidatePasses()
        {
            Assert.That(
                Rate3ControllerFixture.CreateClockSmokeSession().Validate(),
                Is.Null);
        }

        [TestCase("rs3-probe-d2", "p1-scene-004-d2")]
        [TestCase("rs3-d1-p1-calib", "p1-scene-004")]
        [TestCase("rs3-d2-p3-calib", "p1-scene-004-d2")]
        [TestCase("rs3-d1-p1-r5", "p1-scene-004")]
        [TestCase("rs3-d2-p3-r20", "p1-scene-004-d2")]
        public void BatchSession_ValidatePassesForDeclaredRunAndScenario(
            string runId,
            string scenarioId)
        {
            Assert.That(
                Rate3ControllerFixture.CreateBatchSession(runId, scenarioId).Validate(),
                Is.Null);
        }

        [Test]
        public void BatchSession_ValidatePassesForAllSixCalibrationSlots()
        {
            // BC-DRB-4 replaces the two per-difficulty calibration slots with
            // one HOLD slot per (difficulty, phase).
            foreach (string difficulty in new[] { "d1", "d2" })
            foreach (string phase in new[] { "p1", "p2", "p3" })
            {
                string runId = $"rs3-{difficulty}-{phase}-calib";
                string scenarioId =
                    difficulty == "d2" ? "p1-scene-004-d2" : "p1-scene-004";
                Assert.That(
                    Rate3ControllerFixture.CreateBatchSession(runId, scenarioId)
                        .Validate(),
                    Is.Null,
                    runId);
            }
        }

        [TestCase("rs3-d1-calib", "p1-scene-004")]
        [TestCase("rs3-d2-calib", "p1-scene-004-d2")]
        [TestCase("rs3-scouting", "p1-scene-004")]
        public void BatchSession_RejectsSupersededOrNonSessionIdentities(
            string runId,
            string scenarioId)
        {
            // The revision-3 calibration IDs are superseded, and scouting is a
            // stand-alone tool run with no RATE session.
            Assert.That(
                Rate3ControllerFixture.CreateBatchSession(runId, scenarioId).Validate(),
                Is.EqualTo("invalid_run_or_scenario_identity"));
        }

        [Test]
        public void BatchSession_ValidatePassesForAllTwelveMatrixRuns()
        {
            foreach (string difficulty in new[] { "d1", "d2" })
            foreach (string phase in new[] { "p1", "p2", "p3" })
            foreach (string rate in new[] { "r5", "r20" })
            {
                string runId = $"rs3-{difficulty}-{phase}-{rate}";
                string scenarioId =
                    difficulty == "d2" ? "p1-scene-004-d2" : "p1-scene-004";
                Assert.That(
                    Rate3ControllerFixture.CreateBatchSession(runId, scenarioId).Validate(),
                    Is.Null,
                    runId);
            }
        }

        [TestCase("rs3-d1-p1-r5", "p1-scene-004-d2")]
        [TestCase("rs3-d2-p1-r20", "p1-scene-004")]
        [TestCase("rs3-unknown-run", "p1-scene-004")]
        public void BatchSession_RejectsWrongScenarioOrUnknownRun(
            string runId,
            string scenarioId)
        {
            Assert.That(
                Rate3ControllerFixture.CreateBatchSession(runId, scenarioId).Validate(),
                Is.EqualTo("invalid_run_or_scenario_identity"));
        }

        [Test]
        public void ClockSmokeStudy_RejectsResearchRunIdentity()
        {
            RateStudySession session = Rate3ControllerFixture.CreateClockSmokeSession();
            session.run_id = "rs3-d1-p1-r5";

            Assert.That(session.Validate(), Is.EqualTo("invalid_run_or_scenario_identity"));
        }

        [Test]
        public void BatchStudy_RejectsClockSmokeRunIdentity()
        {
            RateStudySession session =
                Rate3ControllerFixture.CreateBatchSession("rs3-clock-smoke", "p1-scene-004");

            Assert.That(session.Validate(), Is.EqualTo("invalid_run_or_scenario_identity"));
        }

        [TestCase("P1-M2-RATE-002-B2")]
        [TestCase("P1-M2-RATE-003-B3")]
        public void Rate3Session_RejectsForeignStudyIdentity(string studyId)
        {
            RateStudySession session = Rate3ControllerFixture.CreateClockSmokeSession();
            session.study_id = studyId;

            Assert.That(session.Validate(), Is.EqualTo("invalid_batch_or_tracker_identity"));
        }

        [Test]
        public void UnknownSessionSchema_IsRejected()
        {
            RateStudySession session = Rate3ControllerFixture.CreateClockSmokeSession();
            session.schema_version = "p1-rate9-session/v1";

            Assert.That(session.Validate(), Is.EqualTo("invalid_session_schema"));
        }

        [Test]
        public void ClockSmokeSession_RejectsBatchPlannedDuration()
        {
            RateStudySession session = Rate3ControllerFixture.CreateClockSmokeSession();
            session.planned_duration_s = 150.0f;

            Assert.That(session.Validate(), Is.EqualTo("invalid_session_counter"));
        }

        [Test]
        public void BatchSession_RejectsClockSmokePlannedDuration()
        {
            RateStudySession session =
                Rate3ControllerFixture.CreateBatchSession("rs3-d1-p1-r5", "p1-scene-004");
            session.planned_duration_s = 30.0f;

            Assert.That(session.Validate(), Is.EqualTo("invalid_session_counter"));
        }

        [Test]
        public void Rate3Session_RejectsWrongSensorFrameSchema()
        {
            RateStudySession session = Rate3ControllerFixture.CreateClockSmokeSession();
            session.sensor_frame_schema = "tethered-sensor-frame/v2";

            Assert.That(session.Validate(), Is.EqualTo("invalid_session_clock_identity"));
        }

        [Test]
        public void Rate3Session_RejectsWrongCaptureClockId()
        {
            RateStudySession session = Rate3ControllerFixture.CreateClockSmokeSession();
            session.capture_monotonic_clock_id = "unity-realtime-since-startup/v1";

            Assert.That(session.Validate(), Is.EqualTo("invalid_session_clock_identity"));
        }

        [Test]
        public void LegacyRate2SessionJson_WithoutRate3Fields_ValidatesAsBefore()
        {
            string legacyJson = "{"
                + "\"schema_version\":\"p1-rate2-session/v1\","
                + "\"study_id\":\"P1-M2-RATE-002-B2\","
                + "\"run_id\":\"rs2-r20-follow-1\","
                + "\"scenario_id\":\"rate-study-20hz\","
                + "\"tracker_id\":\"nanotrack-v2\","
                + "\"tracker_identity_sha256\":\"" + new string('a', 64) + "\","
                + "\"model_identity_sha256\":\"" + new string('c', 64) + "\","
                + "\"init_frame_id\":140,"
                + "\"init_image_sha256\":\"" + new string('b', 64) + "\","
                + "\"hold_route_s_m\":0.0,"
                + "\"minimum_ready_seq\":20,"
                + "\"minimum_processed_frames\":20"
                + "}";

            RateStudySession session =
                JsonUtility.FromJson<RateStudySession>(legacyJson);

            Assert.That(session.planned_duration_s, Is.EqualTo(0f));
            Assert.That(session.sensor_frame_schema, Is.Null);
            Assert.That(session.capture_monotonic_clock_id, Is.Null);
            Assert.That(session.IsRate3, Is.False);
            Assert.That(session.Validate(), Is.Null);
        }

        [Test]
        public void Rate2Session_IgnoresRate3Fields()
        {
            RateStudySession session = Rate3ControllerFixture.CreateRate2Session();
            session.planned_duration_s = 999.0f;
            session.sensor_frame_schema = "garbage";
            session.capture_monotonic_clock_id = "garbage";

            Assert.That(session.Validate(), Is.Null);
        }
    }

    public sealed class RateStudyRate3ReleaseTests
    {
        [TestCase(0.0)]
        [TestCase(1.0)]
        [TestCase(2.0)]
        public void FreshReady_ReleaseAcceptedAndAckCarriesRate3ClockIdentity(
            double readyAgeSeconds)
        {
            using Rate3ControllerFixture fixture = Rate3ControllerFixture.Create(
                Rate3ControllerFixture.CreateClockSmokeSession());
            byte[] ready = fixture.Ready(
                lastProcessedFrameId: 41,
                publisherMonotonicSeconds: 501.0 - readyAgeSeconds);
            byte[] command = fixture.Release("release-rate3-fresh", ready);

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                currentFrameId: 42,
                unixSeconds: 1001.0,
                monotonicSeconds: 501.0,
                simulationSeconds: 11.0);

            Assert.That(accepted, Is.True);
            Assert.That(
                fixture.Controller.State,
                Is.EqualTo(RateStudyExperimentState.Released));
            Assert.That(fixture.Target.MotionEnabled, Is.True);
            string ackJson = File.ReadAllText(
                Path.Combine(fixture.Root, "release_ack.json"));
            StringAssert.Contains("\"schema_version\": \"p1-rate3-release-ack/v1\"", ackJson);
            StringAssert.Contains(
                "\"release_clock_id\": \"system-stopwatch/v1\"",
                ackJson);
            ReleaseAckDocumentV3 ack =
                JsonUtility.FromJson<ReleaseAckDocumentV3>(ackJson);
            Assert.That(ack.release_clock_id, Is.EqualTo("system-stopwatch/v1"));
            Assert.That(ack.release_monotonic_s, Is.EqualTo(501.0));
            Assert.That(ack.release_command_sha256, Is.EqualTo(RateStudyProtocol.Sha256(command)));
            Assert.That(ack.ready_sha256, Is.EqualTo(RateStudyProtocol.Sha256(ready)));
            Assert.That(ack.accepted_backlog_frames, Is.EqualTo(1));
        }

        [Test]
        public void FutureReady_RejectedAsClockIdentityAndHolds()
        {
            using Rate3ControllerFixture fixture = Rate3ControllerFixture.Create(
                Rate3ControllerFixture.CreateClockSmokeSession());
            byte[] command = fixture.Release(
                "release-rate3-future",
                fixture.Ready(41, publisherMonotonicSeconds: 502.0));

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                42,
                monotonicSeconds: 501.0);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            AssertRejection(fixture, "invalid_ready_clock_identity");
        }

        [Test]
        public void StaleReady_BeyondTwoHeartbeatsRejectedAsClockIdentity()
        {
            using Rate3ControllerFixture fixture = Rate3ControllerFixture.Create(
                Rate3ControllerFixture.CreateClockSmokeSession());
            byte[] command = fixture.Release(
                "release-rate3-stale",
                fixture.Ready(41, publisherMonotonicSeconds: 498.9));

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                42,
                monotonicSeconds: 501.0);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            AssertRejection(fixture, "invalid_ready_clock_identity");
        }

        [Test]
        public void ReadyWithWrongPublisherClockId_RejectedAsClockIdentity()
        {
            using Rate3ControllerFixture fixture = Rate3ControllerFixture.Create(
                Rate3ControllerFixture.CreateClockSmokeSession());
            byte[] command = fixture.Release(
                "release-rate3-wrong-publisher-clock",
                fixture.Ready(
                    41,
                    publisherMonotonicSeconds: 501.0,
                    publisherClockId: "unity-realtime-since-startup/v1"));

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                42,
                monotonicSeconds: 501.0);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            AssertRejection(fixture, "invalid_ready_clock_identity");
        }

        [TestCase(0.0)]
        [TestCase(1.5)]
        public void ReadyWithOutOfRangeHeartbeat_RejectedAsClockIdentity(
            double heartbeatIntervalSeconds)
        {
            using Rate3ControllerFixture fixture = Rate3ControllerFixture.Create(
                Rate3ControllerFixture.CreateClockSmokeSession());
            byte[] command = fixture.Release(
                "release-rate3-bad-heartbeat",
                fixture.Ready(
                    41,
                    publisherMonotonicSeconds: 501.0,
                    heartbeatIntervalSeconds: heartbeatIntervalSeconds));

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                42,
                monotonicSeconds: 501.0);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            AssertRejection(fixture, "invalid_ready_clock_identity");
        }

        [Test]
        public void Rate2ReadySchema_OnRate3Session_RejectedAsReadyEvidence()
        {
            using Rate3ControllerFixture fixture = Rate3ControllerFixture.Create(
                Rate3ControllerFixture.CreateClockSmokeSession());
            byte[] command = fixture.Release(
                "release-rate3-v2-ready",
                fixture.Ready(
                    41,
                    publisherMonotonicSeconds: 501.0,
                    readySchema: RateStudyProtocol.ReadySchema));

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                42,
                monotonicSeconds: 501.0);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            AssertRejection(fixture, "invalid_ready_evidence");
        }

        [TestCase(null)]
        [TestCase("unity-realtime-since-startup/v1")]
        public void ReleaseCommandWithMissingOrWrongClockId_RejectedBeforeTransition(
            string releaseClockId)
        {
            using Rate3ControllerFixture fixture = Rate3ControllerFixture.Create(
                Rate3ControllerFixture.CreateClockSmokeSession());
            byte[] command = fixture.Release(
                "release-rate3-bad-release-clock",
                fixture.Ready(41, publisherMonotonicSeconds: 501.0),
                releaseClockId: releaseClockId);

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                42,
                monotonicSeconds: 501.0);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            Assert.That(fixture.Target.MotionEnabled, Is.False);
            AssertRejection(fixture, "invalid_release_clock_id");
            Assert.That(
                File.Exists(Path.Combine(fixture.Root, "release_ack.json")),
                Is.False);
        }

        [Test]
        public void Rate3Session_RejectsRate2ReleaseCommandSchema()
        {
            using Rate3ControllerFixture fixture = Rate3ControllerFixture.Create(
                Rate3ControllerFixture.CreateClockSmokeSession());
            byte[] command = fixture.Release(
                "release-rate3-v2-command",
                fixture.Ready(41, publisherMonotonicSeconds: 501.0),
                commandSchema: RateStudyProtocol.ReleaseCommandSchema);

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                42,
                monotonicSeconds: 501.0);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            AssertRejection(fixture, "invalid_command_schema_or_type");
        }

        [Test]
        public void Rate2Session_RejectsRate3ReleaseCommandSchema()
        {
            using Rate3ControllerFixture fixture = Rate3ControllerFixture.Create(
                Rate3ControllerFixture.CreateRate2Session());
            byte[] command = fixture.Release(
                "release-rate2-v3-command",
                fixture.Ready(41, publisherMonotonicSeconds: 500.0),
                commandSchema: RateStudyProtocol.ReleaseCommandSchemaV3);

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                42,
                monotonicSeconds: 501.0);

            Assert.That(accepted, Is.False);
            Assert.That(fixture.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            AssertRejection(fixture, "invalid_command_schema_or_type");
        }

        [Test]
        public void Rate2Session_ReleaseFlowAndAckBytesRemainUnchanged()
        {
            using Rate3ControllerFixture fixture = Rate3ControllerFixture.Create(
                Rate3ControllerFixture.CreateRate2Session());
            byte[] ready = fixture.Ready(41, publisherMonotonicSeconds: 123.0);
            byte[] command = fixture.Release(
                "release-rate2-unchanged",
                ready,
                commandSchema: RateStudyProtocol.ReleaseCommandSchema,
                releaseClockId: null);

            bool accepted = fixture.Controller.ProcessCommandForTests(
                command,
                42,
                unixSeconds: 1001.0,
                monotonicSeconds: 501.0,
                simulationSeconds: 11.0);

            Assert.That(accepted, Is.True);
            Assert.That(
                fixture.Controller.State,
                Is.EqualTo(RateStudyExperimentState.Released));
            string ackJson = File.ReadAllText(
                Path.Combine(fixture.Root, "release_ack.json"));
            StringAssert.Contains("\"schema_version\": \"p1-rate2-release-ack/v1\"", ackJson);
            Assert.That(ackJson.Contains("release_clock_id"), Is.False);
            ReleaseAckDocument ack =
                JsonUtility.FromJson<ReleaseAckDocument>(ackJson);
            Assert.That(ack.release_monotonic_s, Is.EqualTo(501.0));
            Assert.That(ack.ready_seq, Is.EqualTo(20));
        }

        static void AssertRejection(Rate3ControllerFixture fixture, string expectedCode)
        {
            ExperimentStateDocument state = JsonUtility.FromJson<ExperimentStateDocument>(
                File.ReadAllText(Path.Combine(fixture.Root, "experiment_state.json")));
            Assert.That(state.last_rejection_code, Is.EqualTo(expectedCode));
        }
    }

    // Frame-schema selection in SensorFrameWriter.Capture() depends on the live
    // rendering stack (camera/RenderTexture/ReadPixels) and the scenario
    // bootstrapper, so it is not unit-testable in EditMode; the v3 selection for
    // RATE-003 sessions is covered by the rs3-clock-smoke Play Mode session.
    sealed class Rate3ControllerFixture : IDisposable
    {
        internal string Root { get; private set; }
        internal RateStudySession Session { get; private set; }
        internal RateStudyExperimentController Controller { get; private set; }
        internal LoopTargetVehicle Target { get; private set; }

        internal static Rate3ControllerFixture Create(RateStudySession session)
        {
            var fixture = new Rate3ControllerFixture
            {
                Root = CreateDirectory(),
                Session = session,
            };
            GameObject targetObject = new GameObject("Rate3Target");
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
            GameObject controllerObject = new GameObject("Rate3Controller");
            fixture.Controller =
                controllerObject.AddComponent<RateStudyExperimentController>();
            fixture.Controller.InitializeForTests(
                fixture.Session,
                fixture.Root,
                fixture.Target);
            return fixture;
        }

        internal static RateStudySession CreateClockSmokeSession() =>
            new()
            {
                schema_version = "p1-rate3-session/v1",
                study_id = "P1-M2-RATE-003-CLOCKSMOKE",
                run_id = "rs3-clock-smoke",
                scenario_id = "p1-scene-004",
                tracker_id = "nanotrack-v2",
                tracker_identity_sha256 = new string('a', 64),
                model_identity_sha256 = new string('c', 64),
                init_frame_id = 140,
                init_image_sha256 = new string('b', 64),
                hold_route_s_m = 0f,
                minimum_ready_seq = 20,
                minimum_processed_frames = 20,
                planned_duration_s = 30.0f,
                sensor_frame_schema = "tethered-sensor-frame/v3",
                capture_monotonic_clock_id = RateStudyProtocol.SharedHostClockId,
            };

        internal static RateStudySession CreateBatchSession(string runId, string scenarioId) =>
            new()
            {
                schema_version = "p1-rate3-session/v1",
                study_id = "P1-M2-RATE-003-B1",
                run_id = runId,
                scenario_id = scenarioId,
                tracker_id = "nanotrack-v2",
                tracker_identity_sha256 = new string('a', 64),
                model_identity_sha256 = new string('c', 64),
                init_frame_id = 140,
                init_image_sha256 = new string('b', 64),
                hold_route_s_m = 0f,
                minimum_ready_seq = 20,
                minimum_processed_frames = 20,
                planned_duration_s = 150.0f,
                sensor_frame_schema = "tethered-sensor-frame/v3",
                capture_monotonic_clock_id = RateStudyProtocol.SharedHostClockId,
            };

        internal static RateStudySession CreateRate2Session() =>
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

        internal byte[] Ready(
            long lastProcessedFrameId,
            double publisherMonotonicSeconds,
            double heartbeatIntervalSeconds = 1.0,
            string publisherClockId = RateStudyProtocol.SharedHostClockId,
            string readySchema = null)
        {
            bool rate3 = Session.IsRate3;
            var ready = new TrackerReadyDocument
            {
                schema_version = readySchema
                    ?? (rate3 ? RateStudyProtocol.ReadySchemaV3 : RateStudyProtocol.ReadySchema),
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
                publisher_monotonic_s = publisherMonotonicSeconds,
                publisher_clock_id = rate3 ? publisherClockId : null,
                heartbeat_interval_s = rate3 ? heartbeatIntervalSeconds : 0.0,
            };
            return JsonBytes(ready);
        }

        internal ExperimentControlDocument ReleaseDocument(
            string commandId,
            byte[] ready,
            string commandSchema = null,
            string releaseClockId = RateStudyProtocol.SharedHostClockId)
        {
            bool rate3 = Session.IsRate3;
            return new ExperimentControlDocument
            {
                schema_version = commandSchema
                    ?? (rate3
                        ? RateStudyProtocol.ReleaseCommandSchemaV3
                        : RateStudyProtocol.ReleaseCommandSchema),
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
                release_clock_id = rate3 ? releaseClockId : null,
            };
        }

        internal byte[] Release(
            string commandId,
            byte[] ready,
            string commandSchema = null,
            string releaseClockId = RateStudyProtocol.SharedHostClockId) =>
            JsonBytes(ReleaseDocument(commandId, ready, commandSchema, releaseClockId));

        internal static byte[] JsonBytes(object document) =>
            Encoding.UTF8.GetBytes(JsonUtility.ToJson(document, true) + "\n");

        internal static string CreateDirectory()
        {
            string root = Path.Combine(
                Path.GetTempPath(),
                "RateStudyRate3EditModeTests",
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
