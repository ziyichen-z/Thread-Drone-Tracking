using System;
using System.IO;
using NUnit.Framework;
using UnityEngine;

namespace TetheredTracking.Tests
{
    public sealed class QualificationReleaseEditModeTests
    {
        [Serializable]
        sealed class CommandDocument
        {
            public string schema_version =
                QualificationReleaseGate.CommandSchema;
            public string protocol_id =
                QualificationReleaseGate.ProtocolId;
            public string run_id = "p1-detect-001-qual-99";
            public string scenario_id = "p1-scene-004";
            public string command_id = "command-1";
            public string manifest_sha256;
            public string ready_sha256;
            public double issued_unix_s = 100.0;
            public double not_before_capture_monotonic_s = 500.0;
        }

        [Serializable]
        sealed class ActiveDocument
        {
            public string schema_version =
                QualificationReleaseGate.ActiveSchema;
            public string protocol_id =
                QualificationReleaseGate.ProtocolId;
            public string run_id = "p1-detect-001-qual-99";
            public string scenario_id = "p1-scene-004";
            public string command_id = "command-1";
            public string manifest_sha256;
            public string ready_sha256;
            public string release_command_sha256;
            public string command_relative_path =
                "runs/p1-detect-001-qual-99/"
                + "qualification-release-command.json";
            public double not_before_capture_monotonic_s = 500.0;
        }

        [Test]
        public void Gate_ResetsAtMarkerAndUsesFirstFrameAtHostBoundary()
        {
            string runtime = CreateRuntime(out string runDirectory);
            try
            {
                var gate = new QualificationReleaseGate(
                    runtime,
                    "p1-scene-004",
                    90.0,
                    490.0);
                Assert.That(
                    gate.EvaluateFrame(Frame(8, 8f, 400.0)),
                    Is.EqualTo(QualificationFrameDisposition.Ordinary));
                WriteProtocol(runtime, runDirectory);

                Assert.That(
                    gate.EvaluateFrame(Frame(9, 9f, 499.9)),
                    Is.EqualTo(
                        QualificationFrameDisposition.ResetAndHold));
                Assert.That(gate.AllowsObservation(9), Is.False);
                Assert.That(
                    gate.EvaluateFrame(Frame(10, 10f, 500.0)),
                    Is.EqualTo(QualificationFrameDisposition.Measure));
                Assert.That(gate.AllowsObservation(10), Is.True);
                Assert.That(
                    gate.EvaluateFrame(Frame(11, 11f, 500.2)),
                    Is.EqualTo(QualificationFrameDisposition.Measure));

                QualificationMetricsOrigin identity = gate.MetricsOrigin;
                Assert.That(identity.run_id, Is.EqualTo(
                    "p1-detect-001-qual-99"));
                Assert.That(identity.release_frame_id, Is.EqualTo(10));
                Assert.That(identity.release_monotonic_s, Is.EqualTo(500.0));
                Assert.That(identity.release_simulation_s, Is.EqualTo(10.0));
            }
            finally
            {
                Directory.Delete(runtime, true);
            }
        }

        [Test]
        public void Gate_FailsClosedWhenBoundReadyArtifactChanges()
        {
            string runtime = CreateRuntime(out string runDirectory);
            try
            {
                WriteProtocol(runtime, runDirectory);
                File.WriteAllText(
                    Path.Combine(
                        runDirectory,
                        "qualification-release-ready.json"),
                    "{\"tampered\":true}");
                var gate = new QualificationReleaseGate(
                    runtime,
                    "p1-scene-004",
                    90.0,
                    490.0);
                Assert.Throws<InvalidOperationException>(
                    () => gate.EvaluateFrame(Frame(10, 10f, 500.0)));
            }
            finally
            {
                Directory.Delete(runtime, true);
            }
        }

        [Test]
        public void ForeignMarker_IsInertForDifferentScenario()
        {
            string runtime = CreateRuntime(out string runDirectory);
            try
            {
                WriteProtocol(runtime, runDirectory);
                var gate = new QualificationReleaseGate(
                    runtime,
                    "rate-study-20hz",
                    90.0,
                    490.0);
                Assert.That(
                    gate.EvaluateFrame(Frame(10, 10f, 600.0)),
                    Is.EqualTo(QualificationFrameDisposition.Ordinary));
                Assert.That(gate.AllowsObservation(10), Is.True);
                Assert.That(gate.MetricsOrigin, Is.Null);
            }
            finally
            {
                Directory.Delete(runtime, true);
            }
        }

        [Test]
        public void StaleMarker_CannotHijackSameScenarioSession()
        {
            string runtime = CreateRuntime(out string runDirectory);
            try
            {
                WriteProtocol(runtime, runDirectory);
                var gate = new QualificationReleaseGate(
                    runtime,
                    "p1-scene-004",
                    110.0,
                    510.0);
                QualificationFrameDisposition disposition =
                    gate.EvaluateFrame(Frame(10, 10f, 600.0));
                Assert.That(
                    disposition,
                    Is.EqualTo(QualificationFrameDisposition.Ordinary));
                Assert.That(gate.AllowsObservation(10), Is.True);
                Assert.That(gate.MetricsOrigin, Is.Null);

                var evaluatorObject =
                    new GameObject("StaleMarkerEvaluator");
                CoverageEvaluator evaluator =
                    evaluatorObject.AddComponent<CoverageEvaluator>();
                try
                {
                    evaluator.ConfigureAggregationForTests(
                        5f,
                        512,
                        0.3f);
                    evaluator.RecordAggregationFrameForTests(
                        1,
                        0.2f,
                        0.2f,
                        false,
                        null);
                    Assert.That(
                        evaluator.ApplyQualificationDisposition(
                            disposition),
                        Is.True);
                    Assert.That(
                        evaluator.AggregationForTests().SensorFrames,
                        Is.EqualTo(1));
                }
                finally
                {
                    UnityEngine.Object.DestroyImmediate(
                        evaluatorObject);
                }
            }
            finally
            {
                Directory.Delete(runtime, true);
            }
        }

        [Test]
        public void EvaluatorReset_DropsAllPreReleaseAggregation()
        {
            var gameObject = new GameObject("QualificationEvaluatorReset");
            CoverageEvaluator evaluator =
                gameObject.AddComponent<CoverageEvaluator>();
            try
            {
                evaluator.ConfigureAggregationForTests(5f, 512, 0.3f);
                var box = new NormalizedBoundingBox
                {
                    x = 0.1f,
                    y = 0.1f,
                    width = 0.2f,
                    height = 0.2f,
                };
                evaluator.RecordAggregationFrameForTests(
                    1,
                    0.2f,
                    0.2f,
                    true,
                    box);
                evaluator.RecordAggregationObservationForTests(
                    new TrackingObservation(
                        1,
                        "target-0",
                        box,
                        1f,
                        0.0),
                    "target-0");
                Assert.That(
                    evaluator.AggregationForTests().SensorFrames,
                    Is.EqualTo(1));

                Assert.That(
                    evaluator.ApplyQualificationDisposition(
                        QualificationFrameDisposition.ResetAndMeasure),
                    Is.True);
                CoverageEvaluator.AggregationSnapshot reset =
                    evaluator.AggregationForTests();
                Assert.That(reset.SensorFrames, Is.Zero);
                Assert.That(reset.MatchedObservations, Is.Zero);
                Assert.That(reset.TotalDuration, Is.Zero);

                evaluator.RecordAggregationFrameForTests(
                    2,
                    0.4f,
                    0.2f,
                    true,
                    box);
                Assert.That(
                    evaluator.AggregationForTests().SensorFrames,
                    Is.EqualTo(1));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(gameObject);
            }
        }

        static SensorFrameInfo Frame(
            long frameId,
            float simulationTimeSeconds,
            double captureMonotonicSeconds) =>
            new(
                frameId,
                simulationTimeSeconds,
                0.2f,
                100.0 + frameId,
                captureMonotonicSeconds);

        static string CreateRuntime(out string runDirectory)
        {
            string runtime = Path.Combine(
                Path.GetTempPath(),
                "qualification-release-" + Guid.NewGuid().ToString("N"));
            runDirectory = Path.Combine(
                runtime,
                "runs",
                "p1-detect-001-qual-99");
            Directory.CreateDirectory(runDirectory);
            return runtime;
        }

        static void WriteProtocol(
            string runtime,
            string runDirectory)
        {
            byte[] manifest = System.Text.Encoding.UTF8.GetBytes(
                "{\"scenario_id\":\"p1-scene-004\"}\n");
            byte[] ready = System.Text.Encoding.UTF8.GetBytes(
                "{\"schema_version\":\"ready-test\"}\n");
            File.WriteAllBytes(
                Path.Combine(runDirectory, "manifest.json"),
                manifest);
            File.WriteAllBytes(
                Path.Combine(
                    runDirectory,
                    "qualification-release-ready.json"),
                ready);
            var command = new CommandDocument
            {
                manifest_sha256 = RateStudyProtocol.Sha256(manifest),
                ready_sha256 = RateStudyProtocol.Sha256(ready),
            };
            byte[] commandBytes = System.Text.Encoding.UTF8.GetBytes(
                JsonUtility.ToJson(command, true) + "\n");
            File.WriteAllBytes(
                Path.Combine(
                    runDirectory,
                    "qualification-release-command.json"),
                commandBytes);
            var active = new ActiveDocument
            {
                manifest_sha256 = command.manifest_sha256,
                ready_sha256 = command.ready_sha256,
                release_command_sha256 =
                    RateStudyProtocol.Sha256(commandBytes),
            };
            File.WriteAllText(
                Path.Combine(
                    runtime,
                    QualificationReleaseGate.ActivePointerFile),
                JsonUtility.ToJson(active, true) + "\n");
        }
    }
}
