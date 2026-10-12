using System;
using System.Collections;
using System.IO;
using System.Text;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace TetheredTracking.Tests
{
    public sealed class RateStudyBatchAPlayModeTests
    {
        [UnityTest]
        public IEnumerator HoldAndRelease_GateMotionAndMeasurementAcrossFrames()
        {
            string root = Path.Combine(
                Path.GetTempPath(),
                "RateStudyBatchAPlayModeTests",
                Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(root);
            GameObject targetObject = new GameObject("PlayModeRateTarget");
            GameObject controllerObject = new GameObject("PlayModeRateController");
            try
            {
                LoopTargetVehicle target = targetObject.AddComponent<LoopTargetVehicle>();
                target.Configure(
                    "target-0",
                    new[]
                    {
                        Vector3.zero,
                        new Vector3(10f, 0f, 0f),
                        new Vector3(10f, 0f, 10f),
                    },
                    2f);
                var session = new RateStudySession
                {
                    study_id = "P1-M2-RATE-002-B2",
                    run_id = "rs2-pilot",
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
                RateStudyExperimentController controller =
                    controllerObject.AddComponent<RateStudyExperimentController>();
                controller.InitializeForTests(session, root, target);
                Vector3 held = target.transform.position;

                yield return null;
                yield return null;

                Assert.That(controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
                Assert.That(controller.ControlEnabled, Is.False);
                Assert.That(controller.MeasurementEnabled, Is.False);
                Assert.That(target.transform.position, Is.EqualTo(held));

                byte[] ready = Encoding.UTF8.GetBytes(
                    JsonUtility.ToJson(new TrackerReadyDocument
                    {
                        schema_version = RateStudyProtocol.ReadySchema,
                        state = "TRACKING",
                        study_id = session.study_id,
                        run_id = session.run_id,
                        scenario_id = session.scenario_id,
                        tracker_id = session.tracker_id,
                        tracker_identity_sha256 = session.tracker_identity_sha256,
                        model_identity_sha256 = session.model_identity_sha256,
                        init_frame_id = session.init_frame_id,
                        init_image_sha256 = session.init_image_sha256,
                        last_processed_frame_id = 20,
                        processed_frame_count = 20,
                        seq = 20,
                        publisher_monotonic_s = 10.0,
                    }, true) + "\n");
                byte[] command = Encoding.UTF8.GetBytes(
                    JsonUtility.ToJson(new ExperimentControlDocument
                    {
                        schema_version = RateStudyProtocol.ReleaseCommandSchema,
                        channel = "experiment_control",
                        command_type = "release",
                        command_id = "release-play",
                        study_id = session.study_id,
                        run_id = session.run_id,
                        scenario_id = session.scenario_id,
                        tracker_id = session.tracker_id,
                        tracker_identity_sha256 = session.tracker_identity_sha256,
                        model_identity_sha256 = session.model_identity_sha256,
                        init_frame_id = session.init_frame_id,
                        init_image_sha256 = session.init_image_sha256,
                        ready_json_base64 = Convert.ToBase64String(ready),
                        ready_sha256 = RateStudyProtocol.Sha256(ready),
                    }, true) + "\n");
                Assert.That(controller.ProcessCommandForTests(command, 20), Is.True);

                yield return null;

                Assert.That(controller.State, Is.EqualTo(RateStudyExperimentState.Released));
                Assert.That(controller.ControlEnabled, Is.True);
                Assert.That(controller.MeasurementEnabled, Is.True);
                Assert.That(target.transform.position, Is.Not.EqualTo(held));
            }
            finally
            {
                UnityEngine.Object.Destroy(controllerObject);
                UnityEngine.Object.Destroy(targetObject);
                if (Directory.Exists(root)) Directory.Delete(root, true);
            }
        }

        [UnityTest]
        public IEnumerator Hold_FollowAndNadirHaveIdenticalPreReleasePlatformAndCameraPose()
        {
            using ConditionRig follow = ConditionRig.Create("rs2-r20-follow-1");
            using ConditionRig nadir = ConditionRig.Create("rs2-r20-nadir-1");

            follow.Gimbal.LookAtWorld(
                follow.Camera.position + new Vector3(10f, -5f, 10f));
            nadir.Gimbal.LookNadir();
            Assert.That(follow.Gimbal.HasTarget, Is.True);
            Assert.That(nadir.Gimbal.HasTarget, Is.False);

            yield return null;
            yield return new WaitForSeconds(0.02f);
            yield return null;

            Assert.That(follow.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            Assert.That(nadir.Controller.State, Is.EqualTo(RateStudyExperimentState.Hold));
            Assert.That(follow.Gimbal.HasTarget, Is.False);
            Assert.That(nadir.Gimbal.HasTarget, Is.False);
            Assert.That(follow.Drone.CommandedVelocity, Is.EqualTo(Vector3.zero));
            Assert.That(nadir.Drone.CommandedVelocity, Is.EqualTo(Vector3.zero));
            AssertVectorComponentsEqual(
                follow.Platform.position,
                nadir.Platform.position,
                "platform position");
            AssertQuaternionComponentsEqual(
                follow.Platform.rotation,
                nadir.Platform.rotation,
                "platform rotation");
            AssertVectorComponentsEqual(
                follow.Camera.position,
                nadir.Camera.position,
                "camera position");
            AssertQuaternionComponentsEqual(
                follow.Camera.rotation,
                nadir.Camera.rotation,
                "camera rotation");
            Assert.That(
                Quaternion.Angle(
                    follow.Camera.rotation,
                    Quaternion.Euler(90f, 0f, 0f)),
                Is.LessThan(1e-4f));
        }

        [UnityTest]
        public IEnumerator TruthDirectedScoutingFollowUsesTheClampedGimbalPlant()
        {
            GameObject evaluatorObject = new GameObject("ScoutingEvaluator");
            GameObject cameraObject = new GameObject("ScoutingCamera");
            GameObject targetObject = new GameObject("ScoutingTarget");
            try
            {
                cameraObject.transform.position = new Vector3(0f, 25f, 0f);
                cameraObject.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
                targetObject.transform.position = new Vector3(100f, 0f, 0f);
                TetheredGimbal gimbal =
                    cameraObject.AddComponent<TetheredGimbal>();
                gimbal.maximumOffNadirDeg = 45f;
                gimbal.slewRateDegPerSecond = 10000000f;
                GimbalCommandReceiver receiver =
                    cameraObject.AddComponent<GimbalCommandReceiver>();
                receiver.pollInterval = 1000f;
                CoverageEvaluator evaluator =
                    evaluatorObject.AddComponent<CoverageEvaluator>();
                evaluator.ConfigureScoutingGimbal(
                    new P1DetectScoutingSession
                    {
                        work_id = "P1-DETECT-001",
                        session_id = "scout-play",
                        scenario_id = "p1-detect-scouting",
                        non_measurement = true,
                        gimbal_driver =
                            P1DetectScoutingSession.TruthDirectedGimbalDriver,
                        scenario_config_sha256 = new string('a', 64),
                        loop_duration_s = 106.485f,
                        sample_hz = 2f,
                        remote_slant_range_min_m = 65f,
                        detector_confidence_min = 0.25f,
                        detector_iou_min = 0.30f,
                    },
                    gimbal,
                    targetObject.transform,
                    receiver);

                yield return null;

                Assert.That(receiver.enabled, Is.False);
                Assert.That(gimbal.HasTarget, Is.True);
                Assert.That(gimbal.Saturated, Is.True);
                Assert.That(gimbal.maximumOffNadirDeg, Is.EqualTo(45f));
                Assert.That(
                    Vector3.Angle(cameraObject.transform.forward, Vector3.down),
                    Is.EqualTo(45f).Within(1e-3f));
            }
            finally
            {
                UnityEngine.Object.Destroy(evaluatorObject);
                UnityEngine.Object.Destroy(cameraObject);
                UnityEngine.Object.Destroy(targetObject);
            }
        }

        static void AssertVectorComponentsEqual(
            Vector3 actual,
            Vector3 expected,
            string label)
        {
            Assert.That(actual.x, Is.EqualTo(expected.x).Within(1e-6f), label + " x");
            Assert.That(actual.y, Is.EqualTo(expected.y).Within(1e-6f), label + " y");
            Assert.That(actual.z, Is.EqualTo(expected.z).Within(1e-6f), label + " z");
        }

        static void AssertQuaternionComponentsEqual(
            Quaternion actual,
            Quaternion expected,
            string label)
        {
            Assert.That(actual.x, Is.EqualTo(expected.x).Within(1e-6f), label + " x");
            Assert.That(actual.y, Is.EqualTo(expected.y).Within(1e-6f), label + " y");
            Assert.That(actual.z, Is.EqualTo(expected.z).Within(1e-6f), label + " z");
            Assert.That(actual.w, Is.EqualTo(expected.w).Within(1e-6f), label + " w");
        }

        sealed class ConditionRig : IDisposable
        {
            internal string Root { get; private set; }
            internal Transform Platform { get; private set; }
            internal Transform Camera { get; private set; }
            internal TetheredDronePlant Drone { get; private set; }
            internal TetheredGimbal Gimbal { get; private set; }
            internal RateStudyExperimentController Controller { get; private set; }

            GameObject platformObject;
            GameObject cameraObject;
            GameObject targetObject;
            GameObject controllerObject;

            internal static ConditionRig Create(string runId)
            {
                var rig = new ConditionRig
                {
                    Root = Path.Combine(
                        Path.GetTempPath(),
                        "RateStudyBatchAPlayModePoseTests",
                        Guid.NewGuid().ToString("N")),
                    platformObject = new GameObject("Platform-" + runId),
                    cameraObject = new GameObject("Camera-" + runId),
                    targetObject = new GameObject("Target-" + runId),
                    controllerObject = new GameObject("Controller-" + runId),
                };
                Directory.CreateDirectory(rig.Root);

                rig.Platform = rig.platformObject.transform;
                rig.Platform.SetPositionAndRotation(
                    new Vector3(0f, 20f, 0f),
                    Quaternion.identity);
                rig.Drone = rig.platformObject.AddComponent<TetheredDronePlant>();
                rig.Drone.anchor = Vector3.zero;
                rig.Drone.minimumAltitude = 8f;
                rig.Drone.maximumAltitude = 32f;
                rig.Drone.tetherLength = 35f;

                rig.Camera = rig.cameraObject.transform;
                rig.Camera.SetParent(rig.Platform, false);
                rig.Camera.localPosition = Vector3.zero;
                rig.Camera.rotation = Quaternion.Euler(90f, 0f, 0f);
                rig.Gimbal = rig.cameraObject.AddComponent<TetheredGimbal>();
                rig.Gimbal.slewRateDegPerSecond = 10000f;

                LoopTargetVehicle target =
                    rig.targetObject.AddComponent<LoopTargetVehicle>();
                target.Configure(
                    "target-0",
                    new[]
                    {
                        Vector3.zero,
                        new Vector3(10f, 0f, 0f),
                        new Vector3(10f, 0f, 10f),
                    },
                    2f);
                var session = new RateStudySession
                {
                    study_id = "P1-M2-RATE-002-B2",
                    run_id = runId,
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
                rig.Controller =
                    rig.controllerObject.AddComponent<RateStudyExperimentController>();
                rig.Controller.InitializeForTests(session, rig.Root, target);

                BodyCommandReceiver bodyReceiver =
                    rig.platformObject.AddComponent<BodyCommandReceiver>();
                bodyReceiver.pollInterval = 1000f;
                bodyReceiver.ConfigureForTests(rig.Controller, rig.Drone);
                GimbalCommandReceiver gimbalReceiver =
                    rig.cameraObject.AddComponent<GimbalCommandReceiver>();
                gimbalReceiver.pollInterval = 1000f;
                gimbalReceiver.ConfigureForTests(rig.Controller, rig.Gimbal);
                return rig;
            }

            public void Dispose()
            {
                if (controllerObject != null) UnityEngine.Object.Destroy(controllerObject);
                if (targetObject != null) UnityEngine.Object.Destroy(targetObject);
                if (cameraObject != null) UnityEngine.Object.Destroy(cameraObject);
                if (platformObject != null) UnityEngine.Object.Destroy(platformObject);
                if (Directory.Exists(Root)) Directory.Delete(Root, true);
            }
        }
    }
}
