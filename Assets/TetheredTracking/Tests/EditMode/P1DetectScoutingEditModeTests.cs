using System;
using System.IO;
using NUnit.Framework;
using UnityEngine;

namespace TetheredTracking.Tests
{
    public sealed class P1DetectScoutingEditModeTests
    {
        [Test]
        public void SessionValidationFreezesIdentityAndEveryApprovedThreshold()
        {
            P1DetectScoutingSession session = ValidSession();
            Assert.That(session.Validate(), Is.Null);

            session.non_measurement = false;
            Assert.That(
                session.Validate(),
                Is.EqualTo("invalid_scouting_session_identity"));
            session.non_measurement = true;
            session.gimbal_driver = "controller_follow";
            Assert.That(
                session.Validate(),
                Is.EqualTo("invalid_scouting_session_identity"));
            session.gimbal_driver =
                P1DetectScoutingSession.TruthDirectedGimbalDriver;
            session.remote_slant_range_min_m = 64.9f;
            Assert.That(
                session.Validate(),
                Is.EqualTo("invalid_scouting_frozen_parameter"));
            session.remote_slant_range_min_m = 65f;
            session.detector_iou_min = 0.29f;
            Assert.That(
                session.Validate(),
                Is.EqualTo("invalid_scouting_frozen_parameter"));
        }

        [TestCase("scout-a", true)]
        [TestCase("a", true)]
        [TestCase("Scouting", false)]
        [TestCase("../escape", false)]
        [TestCase("1-leading", false)]
        [TestCase("", false)]
        public void SessionIdsArePathSafe(string value, bool expected)
        {
            Assert.That(P1DetectScoutingSession.SafeSessionId(value), Is.EqualTo(expected));
        }

        [Test]
        public void TruthWriterPublishesImmutablePerFrameSidecars()
        {
            string root = Path.Combine(
                Path.GetTempPath(),
                "p1-detect-scouting-" + Guid.NewGuid().ToString("N"));
            try
            {
                P1DetectScoutingSession session = ValidSession();
                var writer = new P1DetectScoutingTruthWriter(session, root);
                var document = new P1DetectScoutingTruthDocument
                {
                    work_id = session.work_id,
                    session_id = session.session_id,
                    scenario_id = session.scenario_id,
                    frame_id = 7,
                    simulation_time_s = 7.25f,
                    target_track_id = "target-0",
                    target_visible = true,
                    target_visible_sample_fraction = 0.8f,
                    target_slant_range_m = 70f,
                    target_bbox_xywh_norm = Box(0.2f, 0.3f, 0.1f, 0.1f),
                    distractors = new[]
                    {
                        new P1DetectScoutingDistractorTruth
                        {
                            distractor_id = "Environment/Vehicle_Taxi",
                            bbox_xywh_norm = Box(0.6f, 0.3f, 0.1f, 0.1f),
                        },
                    },
                };

                document.gimbal_driver = "controller_follow";
                Assert.Throws<InvalidOperationException>(
                    () => writer.Write(document));
                document.gimbal_driver =
                    P1DetectScoutingSession.TruthDirectedGimbalDriver;
                writer.Write(document);
                string path = Path.Combine(
                    root,
                    "p1-detect-scouting",
                    session.session_id,
                    "truth",
                    "frame_0000000007.json");
                Assert.That(File.Exists(path), Is.True);
                P1DetectScoutingTruthDocument loaded =
                    JsonUtility.FromJson<P1DetectScoutingTruthDocument>(
                        File.ReadAllText(path));
                Assert.That(loaded.schema_version, Is.EqualTo("p1-detect-scouting-truth/v2"));
                Assert.That(loaded.frame_id, Is.EqualTo(7));
                Assert.That(
                    loaded.gimbal_driver,
                    Is.EqualTo(
                        P1DetectScoutingSession.TruthDirectedGimbalDriver));
                Assert.That(loaded.distractors.Length, Is.EqualTo(1));
                Assert.Throws<IOException>(() => writer.Write(document));
            }
            finally
            {
                if (Directory.Exists(root)) Directory.Delete(root, true);
            }
        }

        [Test]
        public void TruthDirectedGimbalUsesPlantAndDisablesExternalReceiver()
        {
            GameObject evaluatorObject = new GameObject("Evaluator");
            GameObject gimbalObject = new GameObject("Gimbal");
            GameObject targetObject = new GameObject("Target");
            try
            {
                CoverageEvaluator evaluator =
                    evaluatorObject.AddComponent<CoverageEvaluator>();
                TetheredGimbal gimbal =
                    gimbalObject.AddComponent<TetheredGimbal>();
                GimbalCommandReceiver receiver =
                    evaluatorObject.AddComponent<GimbalCommandReceiver>();
                targetObject.transform.position = new Vector3(12f, 1f, -4f);
                float maximumOffNadir = gimbal.maximumOffNadirDeg;

                evaluator.ConfigureScoutingGimbal(
                    ValidSession(),
                    gimbal,
                    targetObject.transform,
                    receiver);

                Assert.That(receiver.enabled, Is.False);
                Assert.That(gimbal.HasTarget, Is.True);
                Assert.That(gimbal.TargetWorld, Is.EqualTo(targetObject.transform.position));
                Assert.That(gimbal.maximumOffNadirDeg, Is.EqualTo(maximumOffNadir));

                targetObject.transform.position = new Vector3(-8f, 2f, 6f);
                evaluator.UpdateScoutingGimbalForTests();
                Assert.That(gimbal.TargetWorld, Is.EqualTo(targetObject.transform.position));

                P1DetectScoutingSession invalid = ValidSession();
                invalid.gimbal_driver = "controller_follow";
                Assert.Throws<InvalidOperationException>(
                    () => evaluator.ConfigureScoutingGimbal(
                        invalid,
                        gimbal,
                        targetObject.transform,
                        receiver));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(evaluatorObject);
                UnityEngine.Object.DestroyImmediate(gimbalObject);
                UnityEngine.Object.DestroyImmediate(targetObject);
            }
        }

        [Test]
        public void TruthWriterWritesExplicitNullForUnprojectableBoxes()
        {
            string root = Path.Combine(
                Path.GetTempPath(),
                "p1-detect-scouting-" + Guid.NewGuid().ToString("N"));
            try
            {
                P1DetectScoutingSession session = ValidSession();
                var writer = new P1DetectScoutingTruthWriter(session, root);
                var document = new P1DetectScoutingTruthDocument
                {
                    work_id = session.work_id,
                    session_id = session.session_id,
                    scenario_id = session.scenario_id,
                    frame_id = 8,
                    simulation_time_s = 8.25f,
                    target_track_id = "target-0",
                    target_visible = true,
                    target_visible_sample_fraction = 0.2f,
                    target_slant_range_m = 70f,
                    target_bbox_xywh_norm = null,
                    distractors = new[]
                    {
                        new P1DetectScoutingDistractorTruth
                        {
                            distractor_id = "Environment/Vehicle_Taxi",
                            bbox_xywh_norm = null,
                        },
                    },
                };

                writer.Write(document);
                string path = Path.Combine(
                    root,
                    "p1-detect-scouting",
                    session.session_id,
                    "truth",
                    "frame_0000000008.json");
                string json = File.ReadAllText(path);
                Assert.That(json, Does.Contain("\"target_visible\": true"));
                Assert.That(
                    json,
                    Does.Contain("\"target_bbox_xywh_norm\": null"));
                Assert.That(json, Does.Contain("\"bbox_xywh_norm\": null"));
                Assert.Throws<IOException>(() => writer.Write(document));
            }
            finally
            {
                if (Directory.Exists(root)) Directory.Delete(root, true);
            }
        }

        [Test]
        public void TruthWriterCanonicalizesOnlyBoundaryRoundoff()
        {
            string root = Path.Combine(
                Path.GetTempPath(),
                "p1-detect-scouting-" + Guid.NewGuid().ToString("N"));
            try
            {
                P1DetectScoutingSession session = ValidSession();
                var writer = new P1DetectScoutingTruthWriter(session, root);
                var document = new P1DetectScoutingTruthDocument
                {
                    work_id = session.work_id,
                    session_id = session.session_id,
                    scenario_id = session.scenario_id,
                    frame_id = 9,
                    simulation_time_s = 9.25f,
                    target_track_id = "target-0",
                    target_visible = true,
                    target_visible_sample_fraction = 1f,
                    target_slant_range_m = 70f,
                    target_bbox_xywh_norm = Box(0.2f, 0.2f, 0.1f, 0.1f),
                    distractors = new[]
                    {
                        new P1DetectScoutingDistractorTruth
                        {
                            distractor_id = "Environment/Vehicle_Taxi",
                            bbox_xywh_norm = Box(
                                0.3f,
                                0.8f,
                                0.1f,
                                0.2000001f),
                        },
                    },
                };

                writer.Write(document);
                string path = Path.Combine(
                    root,
                    "p1-detect-scouting",
                    session.session_id,
                    "truth",
                    "frame_0000000009.json");
                P1DetectScoutingTruthDocument loaded =
                    JsonUtility.FromJson<P1DetectScoutingTruthDocument>(
                        File.ReadAllText(path));
                NormalizedBoundingBox canonical =
                    loaded.distractors[0].bbox_xywh_norm;
                Assert.That(
                    canonical.y + canonical.height,
                    Is.LessThanOrEqualTo(1f));
                Assert.That(canonical.height, Is.LessThan(0.2000001f));

                Assert.That(
                    loaded.target_box_status,
                    Is.EqualTo(P1DetectScoutingTruthWriter.BoxStatusValid));
                Assert.That(
                    loaded.distractors[0].box_status,
                    Is.EqualTo(P1DetectScoutingTruthWriter.BoxStatusValid));

                // BC2: material overflow no longer throws away the document.
                // Dropping it left no sidecar on disk, and the offline
                // analyzer then had to score the tick as a detector miss —
                // scout-1 lost 18 of 45 samples exactly this way. The
                // document is now written with an explicit status instead.
                document.frame_id = 10;
                document.target_bbox_xywh_norm = Box(0.2f, 0.9f, 0.1f, 0.201f);
                document.distractors[0].bbox_xywh_norm =
                    Box(0.3f, 0.8f, 0.1f, 0.201f);
                Assert.DoesNotThrow(() => writer.Write(document));
                string overflowPath = Path.Combine(
                    root,
                    "p1-detect-scouting",
                    session.session_id,
                    "truth",
                    "frame_0000000010.json");
                Assert.That(File.Exists(overflowPath), Is.True);
                P1DetectScoutingTruthDocument overflow =
                    JsonUtility.FromJson<P1DetectScoutingTruthDocument>(
                        File.ReadAllText(overflowPath));
                Assert.That(
                    overflow.target_box_status,
                    Is.EqualTo(
                        P1DetectScoutingTruthWriter.BoxStatusUnprojectable));
                // JsonUtility materialises a null object field as a zeroed
                // instance rather than null, so the *status* is what carries
                // the meaning on disk. The offline classifier keys off it.
                Assert.That(overflow.target_bbox_xywh_norm.width, Is.Zero);
                Assert.That(overflow.target_bbox_xywh_norm.height, Is.Zero);
                // Note 3: a distractor without a box is the ordinary
                // off-screen case, so it carries its own label rather than
                // the target-shaped one.
                Assert.That(
                    overflow.distractors[0].box_status,
                    Is.EqualTo(
                        P1DetectScoutingTruthWriter.BoxStatusNotInFrame));
                Assert.That(overflow.distractors[0].bbox_xywh_norm.width, Is.Zero);
                Assert.That(overflow.distractors[0].bbox_xywh_norm.height, Is.Zero);

                // A blank distractor id still fails closed.
                document.frame_id = 11;
                document.distractors[0].distractor_id = "  ";
                InvalidOperationException error =
                    Assert.Throws<InvalidOperationException>(
                        () => writer.Write(document));
                Assert.That(
                    error.Message,
                    Is.EqualTo("invalid_scouting_distractor_truth"));
            }
            finally
            {
                if (Directory.Exists(root)) Directory.Delete(root, true);
            }
        }

        [Test]
        public void StableObjectIdIncludesHierarchyAndRendererProjectionIsClipped()
        {
            GameObject parent = new GameObject("Environment");
            GameObject child = GameObject.CreatePrimitive(PrimitiveType.Cube);
            GameObject cameraObject = new GameObject("Camera");
            try
            {
                child.name = "Vehicle_Taxi";
                child.transform.SetParent(parent.transform);
                child.transform.position = new Vector3(0f, 0f, 5f);
                Camera camera = cameraObject.AddComponent<Camera>();
                camera.transform.position = Vector3.zero;
                camera.transform.rotation = Quaternion.identity;

                Assert.That(
                    CoverageEvaluator.StableObjectId(child.transform),
                    Is.EqualTo("Environment/Vehicle_Taxi"));
                NormalizedBoundingBox box = CoverageEvaluator.ProjectRenderers(
                    camera,
                    child.GetComponentsInChildren<Renderer>(),
                    640f / 480f);
                Assert.That(box, Is.Not.Null);
                Assert.That(box.x, Is.GreaterThanOrEqualTo(0f));
                Assert.That(box.y, Is.GreaterThanOrEqualTo(0f));
                Assert.That(box.x + box.width, Is.LessThanOrEqualTo(1f));
                Assert.That(box.y + box.height, Is.LessThanOrEqualTo(1f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(parent);
                UnityEngine.Object.DestroyImmediate(cameraObject);
            }
        }

        [Test]
        public void CheckedInScenarioIsDedicatedTwentyHertzFullLoopCapture()
        {
            string path = RuntimePaths.ProjectFile(
                "config",
                "scenario.p1-detect-scouting.json");
            ScenarioConfig config = ScenarioConfig.FromJsonStrict(
                File.ReadAllText(path));
            Assert.That(config.scenario_id, Is.EqualTo("p1-detect-scouting"));
            Assert.That(config.sensor.capture_hz, Is.EqualTo(20f));
            Assert.That(config.sensor.retained_frame_count, Is.EqualTo(2560));
            Assert.That(config.evaluation.maximum_pending_frame_count, Is.EqualTo(4096));
            Assert.That(config.scene_adjustments.expected_distractor_count, Is.EqualTo(1));
        }

        static P1DetectScoutingSession ValidSession()
        {
            return new P1DetectScoutingSession
            {
                work_id = "P1-DETECT-001",
                session_id = "scout-test",
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
            };
        }

        static NormalizedBoundingBox Box(
            float x,
            float y,
            float width,
            float height)
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
}
