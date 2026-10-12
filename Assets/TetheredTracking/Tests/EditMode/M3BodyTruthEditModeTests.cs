using System;
using NUnit.Framework;
using UnityEngine;

namespace TetheredTracking.Tests
{
    /// <summary>
    /// P1-M3-BODY-001 batch 1c rework (Acceptance round 11 §B.2): the
    /// run-bound M3 offline truth carrier in CoverageEvaluator — record
    /// shape, minus-one conventions, non-finite fail-closed guard and the
    /// ordinary-run gating predicate.
    /// </summary>
    public sealed class M3BodyTruthEditModeTests
    {
        static CoverageEvaluator.VisibilitySnapshot SnapshotWithBox()
        {
            return new CoverageEvaluator.VisibilitySnapshot(
                intersectsFrustum: true,
                hasUnoccludedSample: true,
                geometricallyVisible: true,
                visibleSampleFraction: 0.6f,
                groundTruthBox: new NormalizedBoundingBox
                {
                    x = 0.4f,
                    y = 0.4f,
                    width = 0.05f,
                    height = 0.05f,
                },
                boundingBoxAreaPixels: 768f,
                centerErrorPixels: 5f);
        }

        static SensorFrameInfo Frame(long frameId) =>
            new SensorFrameInfo(
                frameId,
                simulationTimeSeconds: frameId * 0.2f,
                deltaSimulationSeconds: 0.2f,
                captureUnixSeconds: 1000.0 + frameId * 0.2,
                captureMonotonicSeconds: 500.0 + frameId * 0.2);

        [Test]
        public void TruthRecordCarriesFrameIdentityTruthBoxAndSaturation()
        {
            CoverageEvaluator.M3BodyTruthRecord record =
                CoverageEvaluator.BuildM3BodyTruthRecord(
                    "deterministic-loop-default",
                    Frame(7),
                    new Vector3(125.5f, 0.2f, 117.5f),
                    new Vector3(132f, 25f, 117f),
                    new Vector3(1.5f, 0f, -0.5f),
                    SnapshotWithBox(),
                    gimbalSaturated: true,
                    tetherSaturated: false,
                    sensorWidth: 640f,
                    sensorHeight: 480f,
                    evaluationAspect: 640f / 480f);

            Assert.That(record.schema_version, Is.EqualTo("p1-m3-body-truth/v2"));
            Assert.That(record.scenario_id, Is.EqualTo("deterministic-loop-default"));
            Assert.That(record.frame_id, Is.EqualTo(7));
            Assert.That(record.target_world_x_m, Is.EqualTo(125.5f));
            Assert.That(record.target_world_z_m, Is.EqualTo(117.5f));
            Assert.That(record.body_world_x_m, Is.EqualTo(132f));
            Assert.That(record.body_world_y_m, Is.EqualTo(25f));
            Assert.That(record.applied_velocity_x_mps, Is.EqualTo(1.5f));
            Assert.That(record.applied_velocity_z_mps, Is.EqualTo(-0.5f));
            Assert.That(record.geometrically_visible, Is.True);
            Assert.That(record.truth_box_available, Is.True);
            Assert.That(record.truth_center_x_px, Is.EqualTo(0.425f * 640f));
            Assert.That(record.truth_center_y_px, Is.EqualTo(0.425f * 480f));
            Assert.That(record.gimbal_saturated, Is.True);
            Assert.That(record.tether_saturated, Is.False);
            Assert.That(
                record.capture_monotonic_clock_id,
                Is.EqualTo("system-stopwatch/v1"));

            string json = JsonUtility.ToJson(record);
            StringAssert.Contains("\"frame_id\":7", json);
            StringAssert.Contains("\"geometrically_visible\":true", json);
            StringAssert.Contains("\"applied_velocity_x_mps\":1.5", json);
            StringAssert.DoesNotContain("NaN", json);
        }

        [Test]
        public void TruthRecordWithoutBoxWritesMinusOnes()
        {
            var snapshot = new CoverageEvaluator.VisibilitySnapshot(
                intersectsFrustum: false,
                hasUnoccludedSample: false,
                geometricallyVisible: false,
                visibleSampleFraction: 0f,
                groundTruthBox: null,
                boundingBoxAreaPixels: 0f,
                centerErrorPixels: 0f);
            CoverageEvaluator.M3BodyTruthRecord record =
                CoverageEvaluator.BuildM3BodyTruthRecord(
                    "deterministic-loop-default",
                    Frame(3),
                    new Vector3(1f, 0.2f, 2f),
                    new Vector3(132f, 25f, 117f),
                    Vector3.zero,
                    snapshot,
                    gimbalSaturated: false,
                    tetherSaturated: false,
                    sensorWidth: 640f,
                    sensorHeight: 480f,
                    evaluationAspect: 640f / 480f);

            Assert.That(record.truth_box_available, Is.False);
            Assert.That(record.truth_box_x, Is.EqualTo(-1f));
            Assert.That(record.truth_box_width, Is.EqualTo(-1f));
            Assert.That(record.truth_center_x_px, Is.EqualTo(-1f));
            Assert.That(record.truth_center_y_px, Is.EqualTo(-1f));
        }

        [Test]
        public void TruthRecordRejectsNonFiniteValues()
        {
            Assert.Throws<InvalidOperationException>(() =>
                CoverageEvaluator.BuildM3BodyTruthRecord(
                    "deterministic-loop-default",
                    Frame(1),
                    new Vector3(float.NaN, 0.2f, 0f),
                    new Vector3(132f, 25f, 117f),
                    Vector3.zero,
                    SnapshotWithBox(),
                    gimbalSaturated: false,
                    tetherSaturated: false,
                    sensorWidth: 640f,
                    sensorHeight: 480f,
                    evaluationAspect: 640f / 480f));
            Assert.Throws<InvalidOperationException>(() =>
                CoverageEvaluator.BuildM3BodyTruthRecord(
                    "deterministic-loop-default",
                    Frame(1),
                    new Vector3(125.5f, 0.2f, 117.5f),
                    new Vector3(132f, 25f, 117f),
                    new Vector3(0f, float.PositiveInfinity, 0f),
                    SnapshotWithBox(),
                    gimbalSaturated: false,
                    tetherSaturated: false,
                    sensorWidth: 640f,
                    sensorHeight: 480f,
                    evaluationAspect: 640f / 480f));
        }

        [Test]
        public void TruthGatingRequiresOrdinaryRunAndOrdinaryFrame()
        {
            Assert.That(
                CoverageEvaluator.M3BodyTruthAllowed(
                    null, QualificationFrameDisposition.Ordinary),
                Is.True);
            foreach (QualificationFrameDisposition disposition in Enum
                .GetValues(typeof(QualificationFrameDisposition)))
            {
                if (disposition == QualificationFrameDisposition.Ordinary)
                    continue;
                Assert.That(
                    CoverageEvaluator.M3BodyTruthAllowed(null, disposition),
                    Is.False,
                    disposition.ToString());
            }
        }
    }
}
