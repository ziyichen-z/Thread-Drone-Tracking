using System;
using System.Collections.Generic;
using NUnit.Framework;
using TetheredTracking.Scene006;
using UnityEngine;

namespace TetheredTracking.Tests
{
    /// <summary>
    /// P1-SCENE-006 batch-1c tool-stage tests (C_tool′): the §5.4 frozen
    /// selection, the BC-B1C-2 support-binding check, the T5 re-audit
    /// comparator and the candidate-mode T4/T6 runners. No P3 artifact is
    /// produced by these tests; the real capture waits for the C_tool′
    /// review (BC-B1C-3).
    /// </summary>
    public sealed class Scene006FinalistEditModeTests
    {
        static Scene006FinalistSelection.CellInput Input(
            string family,
            float anchorX,
            float anchorZ,
            float altitude,
            float vfov,
            double lPoint,
            double lOcc,
            double total,
            double p05) =>
            new Scene006FinalistSelection.CellInput
            {
                Family = family,
                AnchorX = anchorX,
                AnchorZ = anchorZ,
                AltitudeM = altitude,
                VerticalFovDeg = vfov,
                SInit = 184.22793579101562f,
                TraceSha256 = new string('c', 64),
                LPoint = lPoint,
                LOcc = lOcc,
                TotalLoss = total,
                MinSideP05Px = p05,
            };

        static List<Scene006FinalistSelection.CellInput> ReviewedCells() =>
            new List<Scene006FinalistSelection.CellInput>
            {
                Input("B", 195f, 30f, 20f, 40f,
                    0.33888888359069824, 0.0574074387550354,
                    0.39629632234573364, 37.06139373779297),
                Input("B", 197f, 30f, 16f, 35f,
                    0.5, 0.05370369553565979,
                    0.5537036657333374, 30.289955139160156),
                Input("B", 197f, 30f, 16f, 40f,
                    0.44074076414108276, 0.06481480598449707,
                    0.5055555701255798, 35.14252471923828),
            };

        [Test]
        public void SelectionOnReviewedCellsPicksLeastMarginalized()
        {
            Scene006FinalistSelection.SelectionResult result =
                Scene006FinalistSelection.Select(ReviewedCells());
            Assert.AreEqual("FINALIST_SELECTED", result.Status);
            Assert.AreEqual(3, result.Ordered.Count);
            // Hand-computed: cell (197,30,16,40) scores ~0.08466 (m_T3a),
            // (195,30,20,40) ~0.04233 (m_T3a), (197,30,16,35) exactly 0
            // (L_point at the 0.50 band edge).
            Assert.AreEqual(0.0, result.Ordered[2].score, 1e-12);
            Assert.AreEqual(35f, result.Ordered[2].vertical_fov_deg);
            Assert.Greater(
                result.Ordered[0].score, result.Ordered[1].score);
            Assert.AreEqual(0.08465603419712612,
                result.Ordered[0].score, 1e-9);
            Assert.AreEqual(0.042328221457344,
                result.Ordered[1].score, 1e-9);
            Scene006FinalistSelection.ScoredCell finalist = result.Finalist;
            Assert.AreEqual(197f, finalist.anchor_x_m);
            Assert.AreEqual(30f, finalist.anchor_z_m);
            Assert.AreEqual(16f, finalist.initial_altitude_m);
            Assert.AreEqual(40f, finalist.vertical_fov_deg);
            Assert.AreEqual(0, finalist.rank);
        }

        [Test]
        public void SelectionFiniteChecksFailClosed()
        {
            var cells = new List<Scene006FinalistSelection.CellInput>
            {
                Input("B", 195f, 30f, 20f, 40f,
                    double.NaN, 0.05, 0.2, 30.0),
                Input("B", 197f, 30f, 16f, 40f,
                    0.3, 0.06, 0.3, double.PositiveInfinity),
            };
            Scene006FinalistSelection.SelectionResult result =
                Scene006FinalistSelection.Select(cells);
            // Both cells carry non-finite inputs: F is empty, and neither
            // margin formula ever ran (no +Inf laundering into m_t1 = 1).
            Assert.AreEqual("BLOCKED_GEOMETRY_INFEASIBLE", result.Status);
            Assert.AreEqual(0, result.Ordered.Count);
            Assert.IsNull(result.Finalist);
            Scene006FinalistSelection.ScoredCell scored =
                Scene006FinalistSelection.Score(cells[1]);
            Assert.AreEqual("SCORE_INPUT_NOT_FINITE", scored.terminal);
            Assert.IsTrue(double.IsNaN(scored.m_t1));
        }

        [Test]
        public void SelectionTieBreakChainIsDeterministic()
        {
            // Equal scores: vfov ascending decides first.
            var tie = new List<Scene006FinalistSelection.CellInput>
            {
                Input("B", 195f, 30f, 20f, 30f, 0.3, 0.2, 0.3, 30.0),
                Input("B", 197f, 30f, 20f, 25f, 0.3, 0.2, 0.3, 30.0),
            };
            Scene006FinalistSelection.SelectionResult result =
                Scene006FinalistSelection.Select(tie);
            Assert.AreEqual(25f, result.Finalist.vertical_fov_deg);
            // Then altitude ascending.
            tie = new List<Scene006FinalistSelection.CellInput>
            {
                Input("B", 195f, 30f, 24f, 30f, 0.3, 0.2, 0.3, 30.0),
                Input("B", 197f, 30f, 16f, 30f, 0.3, 0.2, 0.3, 30.0),
            };
            result = Scene006FinalistSelection.Select(tie);
            Assert.AreEqual(16f, result.Finalist.initial_altitude_m);
            // Then family ordinal.
            tie = new List<Scene006FinalistSelection.CellInput>
            {
                Input("B", 195f, 30f, 20f, 30f, 0.3, 0.2, 0.3, 30.0),
                Input("A", 150f, 108f, 20f, 30f, 0.3, 0.2, 0.3, 30.0),
            };
            result = Scene006FinalistSelection.Select(tie);
            Assert.AreEqual("A", result.Finalist.family);
            // Score equality is binary64 ==: +0.0 ties with -0.0 and falls
            // through to the next field instead of ordering by sign.
            tie = new List<Scene006FinalistSelection.CellInput>
            {
                Input("B", 197f, 30f, 16f, 40f, 0.5, 0.05, 0.15, 25.0),
                Input("B", 197f, 30f, 16f, 35f, 0.5, 0.05, 0.15, 25.0),
            };
            result = Scene006FinalistSelection.Select(tie);
            Assert.AreEqual(35f, result.Finalist.vertical_fov_deg);
        }

        [Test]
        public void AnchorRankFollowsTheFrozenLatticeOrder()
        {
            Assert.AreEqual(
                0, Scene006FinalistSelection.AnchorRank("B", 195f, 30f));
            int near = Scene006FinalistSelection.AnchorRank("B", 197f, 30f);
            int farther =
                Scene006FinalistSelection.AnchorRank("B", 199f, 30f);
            Assert.Greater(near, 0);
            Assert.Greater(farther, near);
            // Equal squared distance (dx = 2 vs dz = 2): x ascending breaks
            // the tie, so (195, 32) precedes (197, 30).
            int tieX = Scene006FinalistSelection.AnchorRank("B", 195f, 32f);
            Assert.Less(tieX, near);
            Assert.Throws<InvalidOperationException>(
                () => Scene006FinalistSelection.AnchorRank(
                    "B", 195.3f, 30f));
        }

        static Scene006CandidateGenerator.P1FamilyReport SyntheticP1(
            string supportId,
            bool legal,
            float anchorX,
            float anchorZ,
            float altitude)
        {
            var candidate = new Scene006AnchorPreflight.CandidateRecord
            {
                rank = 0,
                x_m = anchorX,
                y_m = 0f,
                z_m = anchorZ,
                support_ids = supportId == null
                    ? Array.Empty<string>()
                    : new[] { supportId },
                support_surface_y_m = 0f,
                support_status = "PASS",
                clearance_status = "PASS",
                route_gate_status = "PASS",
                legal = legal,
            };
            var altitudeReport = new Scene006CandidateGenerator
                .P1AltitudeReport
            {
                altitude_m = altitude,
                report = new Scene006AnchorPreflight.ModeReport
                {
                    mode = Scene006AnchorPreflight.ModeCandidatePreflight,
                    status = legal
                        ? "CANDIDATES_AVAILABLE"
                        : "BLOCKED_ANCHOR_PLACEMENT_V2",
                    candidates = new[] { candidate },
                },
            };
            var grid = new Scene006CandidateGenerator.GridAnchorStatus
            {
                x_m = anchorX,
                z_m = anchorZ,
                support_y_m = 0f,
                legal_altitudes_m = legal ? new[] { altitude } : new float[0],
            };
            return new Scene006CandidateGenerator.P1FamilyReport
            {
                family = "B",
                status = "P1_OK",
                grid_anchors = new[] { grid },
                altitudes = new[] { altitudeReport },
            };
        }

        static Scene006CandidateGenerator.P2FamilyReport SyntheticP2(
            float anchorX,
            float anchorZ,
            float altitude)
        {
            var cell = new Scene006CandidateEvaluation.CellRecord
            {
                family = "B",
                anchor_x_m = anchorX,
                anchor_z_m = anchorZ,
                initial_altitude_m = altitude,
                vertical_fov_deg = 40f,
                gates_in_band = true,
            };
            var anchor = new Scene006CandidateGenerator.P2AnchorRecord
            {
                anchor_x_m = anchorX,
                anchor_z_m = anchorZ,
                legal_altitudes_m = new[] { altitude },
                cells = new[] { cell },
            };
            return new Scene006CandidateGenerator.P2FamilyReport
            {
                family = "B",
                status = "P2_OK",
                in_band_cell_count = 1,
                anchors = new[] { anchor },
            };
        }

        [Test]
        public void SupportBindingAcceptsSingleGrassInstance()
        {
            Scene006FinalistGenerator.SupportBindingRecord[] records =
                Scene006FinalistGenerator.VerifySupportBinding(
                    SyntheticP1("Natures_Grass Tile (3)", true, 197f, 30f, 16f),
                    SyntheticP2(197f, 30f, 16f));
            Assert.AreEqual(1, records.Length);
            Assert.IsTrue(records[0].ok);
            Assert.AreEqual("", records[0].mismatch);
            Assert.IsTrue(records[0].p1_legal);
            Assert.IsTrue(records[0].single_support);
            Assert.IsTrue(records[0].grass_allowlist_match);
        }

        [Test]
        public void SupportBindingFailsClosedOnEveryMismatchClass()
        {
            // road_data surface id as support (the F6 shape).
            AssertMismatch(
                SyntheticP1("Road Tile@210,30", true, 197f, 30f, 16f),
                "grass-allowlist");
            // Zero support instances.
            AssertMismatch(
                SyntheticP1(null, true, 197f, 30f, 16f),
                "exactly one");
            // Not legal in P1.
            AssertMismatch(
                SyntheticP1("Natures_Grass Tile", false, 197f, 30f, 16f),
                "not legal");
            // Cell anchor absent from the P1 lattice.
            AssertMismatch(
                SyntheticP1("Natures_Grass Tile", true, 195f, 32f, 16f),
                "missing from P1 lattice");
            // P1 grid record lacks the cell's altitude (binding mismatch).
            Scene006CandidateGenerator.P1FamilyReport p1 =
                SyntheticP1("Natures_Grass Tile", true, 197f, 30f, 16f);
            p1.grid_anchors[0].legal_altitudes_m = new[] { 20f };
            AssertMismatch(p1, "binding differs");
        }

        static void AssertMismatch(
            Scene006CandidateGenerator.P1FamilyReport p1,
            string expectedFragment)
        {
            Scene006FinalistGenerator.SupportBindingRecord[] records =
                Scene006FinalistGenerator.VerifySupportBinding(
                    p1, SyntheticP2(197f, 30f, 16f));
            Assert.AreEqual(1, records.Length);
            Assert.IsFalse(records[0].ok);
            StringAssert.Contains(expectedFragment, records[0].mismatch);
        }

        [Test]
        public void T5RecheckComparatorMatchesAndDetects()
        {
            Scene006AnchorPreflight.ModeReport left =
                SyntheticP1("Natures_Grass Tile", true, 197f, 30f, 16f)
                    .altitudes[0].report;
            Scene006AnchorPreflight.ModeReport right =
                SyntheticP1("Natures_Grass Tile", true, 197f, 30f, 16f)
                    .altitudes[0].report;
            Assert.IsTrue(
                Scene006FinalistGenerator.ModeReportsEqual(
                    left, right, out string divergence));
            Assert.AreEqual("", divergence);
            right.candidates[0].route_gate_status = "FAIL";
            Assert.IsFalse(
                Scene006FinalistGenerator.ModeReportsEqual(
                    left, right, out divergence));
            StringAssert.Contains("route_gate_status", divergence);
            StringAssert.Contains("'PASS' vs 'FAIL'", divergence);
            Assert.IsFalse(
                Scene006FinalistGenerator.ModeReportsEqual(
                    left, null, out _));
        }

        [Test]
        public void T5RecheckComparatorTreatsBothNaNAsSame()
        {
            // Round-3 F10 regression: SupportAt records NaN support heights
            // for SUPPORT_NOT_FOUND candidates, so a byte-identical re-run
            // must compare equal on NaN fields.
            Scene006AnchorPreflight.ModeReport left =
                SyntheticP1("Natures_Grass Tile", true, 197f, 30f, 16f)
                    .altitudes[0].report;
            left.candidates[0].support_surface_y_m = float.NaN;
            Scene006AnchorPreflight.ModeReport right =
                SyntheticP1("Natures_Grass Tile", true, 197f, 30f, 16f)
                    .altitudes[0].report;
            right.candidates[0].support_surface_y_m = float.NaN;
            Assert.IsTrue(
                Scene006FinalistGenerator.ModeReportsEqual(
                    left, right, out string divergence));
            Assert.AreEqual("", divergence);
            // NaN vs finite still diverges.
            right.candidates[0].support_surface_y_m = 0.0f;
            Assert.IsFalse(
                Scene006FinalistGenerator.ModeReportsEqual(
                    left, right, out divergence));
            StringAssert.Contains("support_surface_y_m", divergence);
        }

        [Test]
        public void SelectionTableKeepsTerminalLabels()
        {
            // Round-3 F12: terminal-scored cells stay in the artifact table
            // with their label; only non-terminal cells are ranked.
            var cells = new List<Scene006FinalistSelection.CellInput>
            {
                Input("B", 195f, 30f, 20f, 40f, 0.3, 0.2, 0.3, 30.0),
                Input("B", 197f, 30f, 16f, 40f,
                    0.3, double.NaN, 0.3, 30.0),
            };
            Scene006FinalistSelection.SelectionResult result =
                Scene006FinalistSelection.Select(cells);
            Assert.AreEqual(1, result.Ordered.Count);
            Assert.AreEqual(2, result.Table.Count);
            Assert.AreEqual(0, result.Table[0].rank);
            Assert.AreEqual("", result.Table[0].terminal);
            Assert.AreEqual(-1, result.Table[1].rank);
            Assert.AreEqual(
                "SCORE_INPUT_NOT_FINITE", result.Table[1].terminal);
        }

        [Test]
        public void CandidateT6AndT4OnSyntheticRig()
        {
            Scene006TestLog.ExpectMaterialInstantiation();
            var rig = new Scene006SceneRig();
            try
            {
                rig.CreateTargetReplica();
                rig.CreateEvaluationCamera(40f, 640, 480);
                Vector3 anchor = new Vector3(5f, 0f, 5f);
                Vector3[] route =
                {
                    new Vector3(0f, 0f, 0f),
                    new Vector3(10f, 0f, 0f),
                    new Vector3(10f, 0f, 10f),
                    new Vector3(0f, 0f, 10f),
                };
                Scene006Trace.State[] trace = Scene006Trace.Generate(
                    route, 2f, 0f);
                Vector3 pHover = Scene006StationSet.HoverPosition(
                    anchor, 0f, 20f);

                Scene006Evaluation.T6Record t6 =
                    Scene006FinalistGenerator.RunCandidateT6(
                        rig, trace, pHover, 30f, 640, 480);
                Assert.AreEqual(0, t6.k_star);
                Assert.AreEqual(30f, t6.t1_domain_median_px);
                Assert.AreEqual(
                    t6.prompt_min_side_px >= 30f ? "PASS" : "FAIL",
                    t6.gate);

                // C_hold comes from the P2 cell, never recomputed: a
                // provided 0.4 with all-visible stations yields G = 0.6.
                Scene006FinalistGenerator.T4CandidateRecord t4 =
                    Scene006FinalistGenerator.RunCandidateT4(
                        rig,
                        trace,
                        anchor,
                        0f,
                        20f,
                        40f,
                        Array.Empty<Scene006PathCertificate.ObstaclePrism>(),
                        null,
                        0.4f);
                Assert.AreEqual(0.4f, t4.c_hold);
                Assert.AreEqual(1f, t4.best_c_station, 1e-6f);
                Assert.AreEqual(0.6f, t4.g_station, 1e-6f);
                Assert.AreEqual("PASS", t4.gate);
                Assert.AreEqual(0, t4.path_rejection_count);

                // A named bound support instance absent from the obstacle
                // set fails closed (F2 literal).
                Assert.Throws<InvalidOperationException>(
                    () => Scene006FinalistGenerator.RunCandidateT4(
                        rig,
                        trace,
                        anchor,
                        0f,
                        20f,
                        40f,
                        Array.Empty<Scene006PathCertificate.ObstaclePrism>(),
                        "Natures_Grass Tile (99)",
                        0.4f));
            }
            finally
            {
                rig.Cleanup();
            }
        }
    }
}
