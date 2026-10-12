using System;
using System.IO;
using NUnit.Framework;

namespace TetheredTracking.Tests
{
    /// <summary>
    /// P1-M2-RATE-003 batch-2 Unity-side behaviour: the §4 three-phase
    /// scouting selection and the runtime-slot hygiene that keeps a previous
    /// attempt's evaluation-truth stream out of the next run's §5/§11
    /// analysis.
    /// </summary>
    public sealed class Rate3ScoutingSelectionTests
    {
        static Rate3ScoutingTool.Candidate Candidate(
            int index,
            float routeDistance,
            bool qualified) =>
            new()
            {
                index = index,
                route_s_m = routeDistance,
                frame_margin = qualified ? 0.2f : 0.01f,
                qualified = qualified,
            };

        static Rate3ScoutingTool.Candidate[] Ring(params int[] qualifiedIndices)
        {
            var candidates = new Rate3ScoutingTool.Candidate[30];
            for (int index = 0; index < candidates.Length; index++)
            {
                bool qualified = Array.IndexOf(qualifiedIndices, index) >= 0;
                candidates[index] = Candidate(index, index * 1f, qualified);
            }
            return candidates;
        }

        [Test]
        public void IdealPhases_AreZeroOneThirdAndTwoThirdsOfThePerimeter()
        {
            float[] phases = Rate3ScoutingTool.IdealPhases(30f);

            Assert.That(phases.Length, Is.EqualTo(3));
            Assert.That(phases[0], Is.EqualTo(0f));
            Assert.That(phases[1], Is.EqualTo(10f).Within(1e-5f));
            Assert.That(phases[2], Is.EqualTo(20f).Within(1e-5f));
        }

        [Test]
        public void SelectPhases_TakesTheFirstQualifiedCandidateAtOrAfterEachPhase()
        {
            Rate3ScoutingTool.Candidate[] candidates = Ring(2, 13, 24);
            var selectedIndex = new int[3];
            var selectedDistance = new float[3];

            string error = Rate3ScoutingTool.SelectPhases(
                candidates,
                Rate3ScoutingTool.IdealPhases(30f),
                selectedIndex,
                selectedDistance);

            Assert.That(error, Is.Null);
            Assert.That(selectedIndex, Is.EqualTo(new[] { 2, 13, 24 }));
            Assert.That(selectedDistance, Is.EqualTo(new[] { 2f, 13f, 24f }));
        }

        [Test]
        public void SelectPhases_WrappingCollapsesAPhaseAndIsRefused()
        {
            // Nothing qualifies at or after 20 m, so phase 3 wraps to the
            // first qualified candidate of the ring — which is already
            // phase 1's design point, because phase 1's ideal position is 0.
            // Any wrap therefore collapses the matched design and must be
            // refused, exactly like "no qualifying candidate for a phase".
            Rate3ScoutingTool.Candidate[] candidates = Ring(1, 11, 12);
            var selectedIndex = new int[3];
            var selectedDistance = new float[3];

            string error = Rate3ScoutingTool.SelectPhases(
                candidates,
                Rate3ScoutingTool.IdealPhases(30f),
                selectedIndex,
                selectedDistance);

            Assert.That(error, Is.EqualTo("phase_collision"));
        }

        [Test]
        public void SelectPhases_FailsClosedWhenTwoPhasesCollapse()
        {
            // A single qualified candidate makes all three design points the
            // same position; the paired design would degenerate.
            Rate3ScoutingTool.Candidate[] candidates = Ring(5);
            var selectedIndex = new int[3];
            var selectedDistance = new float[3];

            string error = Rate3ScoutingTool.SelectPhases(
                candidates,
                Rate3ScoutingTool.IdealPhases(30f),
                selectedIndex,
                selectedDistance);

            Assert.That(error, Is.EqualTo("phase_collision"));
        }

        [Test]
        public void SelectPhases_FailsClosedWithNoQualifiedCandidate()
        {
            Rate3ScoutingTool.Candidate[] candidates = Ring();
            var selectedIndex = new int[3];
            var selectedDistance = new float[3];

            Assert.That(
                Rate3ScoutingTool.SelectPhases(
                    candidates,
                    Rate3ScoutingTool.IdealPhases(30f),
                    selectedIndex,
                    selectedDistance),
                Is.EqualTo("no_qualified_candidate_for_phase"));
            Assert.That(
                Rate3ScoutingTool.SelectPhases(
                    Array.Empty<Rate3ScoutingTool.Candidate>(),
                    Rate3ScoutingTool.IdealPhases(30f),
                    selectedIndex,
                    selectedDistance),
                Is.EqualTo("no_scouting_candidates"));
        }
    }

    public sealed class Rate3EvaluationTruthSlotTests
    {
        static string CreateDirectory()
        {
            string root = Path.Combine(
                Path.GetTempPath(),
                "Rate3Batch2EditModeTests",
                Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(root);
            return root;
        }

        [Test]
        public void StaleEvaluationTruthStreamIsAStaleRuntimeSlot()
        {
            string root = CreateDirectory();
            try
            {
                Assert.That(
                    RateStudyExperimentController.HasStaleRuntimeSlot(root),
                    Is.False);
                File.WriteAllText(
                    Path.Combine(
                        root,
                        CoverageEvaluator.Rate3EvaluationTruthFileName),
                    "{}\n");

                Assert.That(
                    RateStudyExperimentController.HasStaleRuntimeSlot(root),
                    Is.True);
            }
            finally
            {
                Directory.Delete(root, true);
            }
        }

        [Test]
        public void PrepareRuntimeSlotsClearsTheEvaluationTruthStream()
        {
            string root = CreateDirectory();
            try
            {
                string path = Path.Combine(
                    root,
                    CoverageEvaluator.Rate3EvaluationTruthFileName);
                File.WriteAllText(path, "{}\n");

                RateStudyExperimentController.PrepareRuntimeSlots(root);

                Assert.That(File.Exists(path), Is.False);
                Assert.That(
                    RateStudyExperimentController.HasStaleRuntimeSlot(root),
                    Is.False);
            }
            finally
            {
                Directory.Delete(root, true);
            }
        }

        [Test]
        public void EvaluationTruthRecordCarriesTheClockAndOfflineIdentity()
        {
            var record = new CoverageEvaluator.Rate3EvaluationTruthRecord
            {
                study_id = "P1-M2-RATE-003-B1",
                run_id = "rs3-d1-p1-r20",
                frame_id = 321,
                release_frame_id = 320,
                simulation_time_s = 12.5f,
                capture_monotonic_s = 501.25,
                capture_monotonic_clock_id = RateStudyProtocol.SharedHostClockId,
                geometrically_visible = true,
                truth_box_available = true,
                truth_center_x_px = 352.5f,
                truth_center_y_px = 78.25f,
                target_world_x_m = 128.5f,
                target_world_z_m = 116.0f,
            };

            string json = UnityEngine.JsonUtility.ToJson(record);

            StringAssert.Contains(
                "\"schema_version\":\"p1-rate3-evaluation-truth/v1\"",
                json);
            StringAssert.Contains(
                "\"capture_monotonic_clock_id\":\"system-stopwatch/v1\"",
                json);
            StringAssert.Contains("\"run_id\":\"rs3-d1-p1-r20\"", json);
        }
    }
}
