using System;
using NUnit.Framework;
using TetheredTracking.Scene006;
using UnityEngine;

namespace TetheredTracking.Tests
{
    /// <summary>
    /// P1-SCENE-006 prompt law v2 (§3.2 / acceptance criterion B). The
    /// scene-driven replay is exercised by the real `RunPromptSelection`
    /// run that produces the committed artifact; these tests pin the law's
    /// arithmetic and its fail-closed behaviour without a scene, including
    /// the concrete F23 prompt frame that the old law admitted.
    /// </summary>
    public sealed class Scene006PromptSelectionEditModeTests
    {
        const int Width = 640;
        const int Height = 480;

        static Scene006PromptSelection.Band Band(
            string metric, double q05, double q95, int count)
        {
            return new Scene006PromptSelection.Band
            {
                metric = metric,
                unit = metric == "min_side_px" ? "px" : "deg",
                computed = true,
                count = count,
                q05 = q05,
                q95 = q95,
            };
        }

        static Scene006PromptSelection.WarmupTick Tick(
            int k,
            float x,
            float y,
            float width,
            float height,
            float minSidePx,
            float offNadirDeg,
            bool visible = true,
            string status = "OK")
        {
            return new Scene006PromptSelection.WarmupTick
            {
                k = k,
                geometrically_visible = visible,
                frustum_visible = visible,
                target_box_status = status,
                target_bbox_xywh_norm = new NormalizedBoundingBox
                {
                    x = x,
                    y = y,
                    width = width,
                    height = height,
                },
                min_side_px = minSidePx,
                applied_off_nadir_deg = offNadirDeg,
            };
        }

        static Scene006PromptSelection.WarmupTick Evaluate(
            Scene006PromptSelection.WarmupTick record,
            Scene006PromptSelection.Band minSide,
            Scene006PromptSelection.Band offNadir)
        {
            Scene006PromptSelection.EvaluateEligibility(
                record, minSide, offNadir, Width, Height);
            return record;
        }

        [Test]
        public void BandEndpointsAreTheDomainsType7Quantiles()
        {
            // n = 5: q05 -> index 0.2 (lower branch), q95 -> index 3.8
            // (upper-anchor branch). Hand-computed: 12 and 48.
            var values = new[] { 10f, 20f, 30f, 40f, 50f };
            Scene006PromptSelection.Band band =
                Scene006PromptSelection.ComputeBand("min_side_px", "px", values);

            Assert.IsTrue(band.computed);
            Assert.AreEqual(5, band.count);
            Assert.AreEqual("type-7", band.quantile_method);
            Assert.AreEqual(12.0, band.q05, 1e-12);
            Assert.AreEqual(48.0, band.q95, 1e-12);
        }

        [Test]
        public void AnInBandUntruncatedWarmupFrameIsEligible()
        {
            Scene006PromptSelection.WarmupTick record = Evaluate(
                Tick(7, 0.30f, 0.30f, 0.10f, 0.14f, 64f, 44f),
                Band("min_side_px", 35.0, 90.0, 52),
                Band("applied_off_nadir_deg", 42.0, 45.0, 52));

            Assert.IsTrue(record.clause_a_visible);
            Assert.IsTrue(record.clause_b_box_ok);
            Assert.IsTrue(record.clause_c_untruncated);
            Assert.IsTrue(record.clause_d_scale_band);
            Assert.IsTrue(record.clause_e_off_nadir_band);
            Assert.IsTrue(record.eligible);
            Assert.AreEqual(string.Empty, record.first_failed_clause);
        }

        /// <summary>
        /// The whole point of the redirection: the accepted `k* = 2` frame
        /// — border-clipped at `x = 0.000`, `min(w,h) = 143.2 px`,
        /// `23.1 deg` off-nadir against a domain pinned near the `45 deg`
        /// clamp — must be mechanically refused. The old law admitted it.
        /// </summary>
        [Test]
        public void TheF23PromptFrameIsRejectedOnTruncationScaleAndObliquity()
        {
            Scene006PromptSelection.Band minSide =
                Band("min_side_px", 35.142524f, 90.0, 52);
            Scene006PromptSelection.Band offNadir =
                Band("applied_off_nadir_deg", 45.0, 45.0, 52);

            Scene006PromptSelection.WarmupTick record = Evaluate(
                Tick(2, 0.0f, 0.20f, 0.30f, 0.40f, 143.2294464111328f, 23.1f),
                minSide,
                offNadir);

            Assert.IsTrue(record.clause_a_visible);
            Assert.IsTrue(record.clause_b_box_ok);
            Assert.IsFalse(record.clause_c_untruncated, "x = 0.000 is clipped");
            Assert.IsFalse(
                record.clause_d_scale_band, "143.2 px is above the q95 scale");
            Assert.IsFalse(
                record.clause_e_off_nadir_band,
                "23.1 deg is below the domain's q05 obliquity");
            Assert.IsFalse(record.eligible);
            Assert.AreEqual("c_untruncated", record.first_failed_clause);
        }

        [Test]
        public void EachClauseRejectsIndependentlyAndInOrder()
        {
            Scene006PromptSelection.Band minSide =
                Band("min_side_px", 35.0, 90.0, 52);
            Scene006PromptSelection.Band offNadir =
                Band("applied_off_nadir_deg", 40.0, 45.0, 52);

            Assert.AreEqual(
                "a_visible",
                Evaluate(
                    Tick(0, 0.3f, 0.3f, 0.1f, 0.1f, 64f, 44f, visible: false,
                        status: "TARGET_NOT_VISIBLE"),
                    minSide, offNadir).first_failed_clause);
            Assert.AreEqual(
                "b_box_ok",
                Evaluate(
                    Tick(1, 0.3f, 0.3f, 0.1f, 0.1f, float.NaN, 44f,
                        status: "TARGET_VISIBLE_UNPROJECTABLE"),
                    minSide, offNadir).first_failed_clause);

            // Truncation: each of the four edges, at the exact 2.0 px limit
            // (admissible, closed interval) and just inside it (refused).
            Assert.IsTrue(
                Evaluate(
                    Tick(3, 2f / Width, 2f / Height, 0.3f, 0.3f, 64f, 44f),
                    minSide, offNadir).clause_c_untruncated,
                "exactly 2.0 px of margin is admissible");
            Assert.AreEqual(
                "c_untruncated",
                Evaluate(
                    Tick(3, 1.9f / Width, 0.3f, 0.3f, 0.3f, 64f, 44f),
                    minSide, offNadir).first_failed_clause,
                "left edge");
            Assert.AreEqual(
                "c_untruncated",
                Evaluate(
                    Tick(3, 0.3f, 1.9f / Height, 0.3f, 0.3f, 64f, 44f),
                    minSide, offNadir).first_failed_clause,
                "top edge");
            Assert.AreEqual(
                "c_untruncated",
                Evaluate(
                    Tick(3, 0.5f, 0.3f, 0.5f, 0.3f, 64f, 44f),
                    minSide, offNadir).first_failed_clause,
                "right edge");
            Assert.AreEqual(
                "c_untruncated",
                Evaluate(
                    Tick(3, 0.3f, 0.5f, 0.3f, 0.5f, 64f, 44f),
                    minSide, offNadir).first_failed_clause,
                "bottom edge");

            // Scale band: both sides are closed, both sides reject outside.
            Assert.IsTrue(
                Evaluate(
                    Tick(4, 0.3f, 0.3f, 0.2f, 0.2f, 35f, 44f),
                    minSide, offNadir).clause_d_scale_band,
                "q05 itself is inside the band");
            Assert.IsTrue(
                Evaluate(
                    Tick(4, 0.3f, 0.3f, 0.2f, 0.2f, 90f, 44f),
                    minSide, offNadir).clause_d_scale_band,
                "q95 itself is inside the band");
            Assert.AreEqual(
                "d_scale_band",
                Evaluate(
                    Tick(4, 0.3f, 0.3f, 0.2f, 0.2f, 34.9f, 44f),
                    minSide, offNadir).first_failed_clause);
            Assert.AreEqual(
                "d_scale_band",
                Evaluate(
                    Tick(4, 0.3f, 0.3f, 0.2f, 0.2f, 90.1f, 44f),
                    minSide, offNadir).first_failed_clause);

            // Off-nadir band: two-sided as well.
            Assert.AreEqual(
                "e_off_nadir_band",
                Evaluate(
                    Tick(5, 0.3f, 0.3f, 0.2f, 0.2f, 64f, 39.9f),
                    minSide, offNadir).first_failed_clause);
            Assert.AreEqual(
                "e_off_nadir_band",
                Evaluate(
                    Tick(5, 0.3f, 0.3f, 0.2f, 0.2f, 64f, 45.1f),
                    minSide, offNadir).first_failed_clause);
        }

        [Test]
        public void ADegenerateBandStillAdmitsItsOwnEndpoint()
        {
            // If the whole domain is pinned at the 45 deg clamp the band
            // collapses; the law then admits only an exactly-45 deg warmup
            // frame. Recorded because that is the structural-empty risk the
            // amendment accepted rather than widened the pool for.
            Scene006PromptSelection.Band offNadir =
                Band("applied_off_nadir_deg", 45.0, 45.0, 52);
            Scene006PromptSelection.Band minSide =
                Band("min_side_px", 35.0, 90.0, 52);

            Assert.IsTrue(
                Evaluate(
                    Tick(9, 0.3f, 0.3f, 0.2f, 0.2f, 64f, 45f),
                    minSide, offNadir).clause_e_off_nadir_band);
            Assert.IsFalse(
                Evaluate(
                    Tick(9, 0.3f, 0.3f, 0.2f, 0.2f, 64f, 44.99f),
                    minSide, offNadir).clause_e_off_nadir_band);
        }

        [Test]
        public void AnUncomputedBandRefusesEverything()
        {
            var band = new Scene006PromptSelection.Band
            {
                metric = "min_side_px",
                unit = "px",
                computed = false,
            };
            Scene006PromptSelection.WarmupTick record = Evaluate(
                Tick(6, 0.3f, 0.3f, 0.2f, 0.2f, 64f, 44f),
                band,
                band);
            Assert.IsFalse(record.eligible);
            Assert.AreEqual("d_scale_band", record.first_failed_clause);
        }

        static Scene006PromptSelection.Artifact SyntheticArtifact(
            int selectedTick)
        {
            return new Scene006PromptSelection.Artifact
            {
                status = selectedTick == Scene006PromptSelection.NoSelection
                    ? Scene006PromptSelection.StatusPromptLawUnsatisfiable
                    : Scene006PromptSelection.StatusSelected,
                terminal = selectedTick == Scene006PromptSelection.NoSelection
                    ? Scene006PromptSelection.StatusPromptLawUnsatisfiable
                    : string.Empty,
                selected_tick = selectedTick,
                diagnostic_tick = 275,
                scenario_id = "p1-scene-006-difficult-v1",
                scenario_sha256 = new string('a', 64),
                trace_sha256 = new string('b', 64),
                warmup_pool = Scene006PromptSelection.WarmupPool(),
                measurement_tick_set = Scene006ProbeRenderer.ProbeTicks(),
                measurement_ticks = new[]
                {
                    new Scene006PromptSelection.MeasurementTick
                    {
                        k = 15,
                        geometrically_visible = true,
                        target_box_status = "OK",
                        min_side_px = 70.5f,
                        applied_off_nadir_deg = 45f,
                    },
                },
                d_v = new Scene006PromptSelection.DomainSection
                {
                    measurement_tick_count = 106,
                    visible_count = 52,
                    all_members_box_ok = true,
                    members = new[] { 15 },
                    non_ok_members = Array.Empty<int>(),
                    denominator_assertion_count = 52,
                    denominator_assertion_ok = true,
                },
                min_side_band = Band("min_side_px", 35.0, 90.0, 52),
                off_nadir_band = Band("applied_off_nadir_deg", 45.0, 45.0, 52),
                warmup_ticks = new[]
                {
                    Tick(2, 0.0f, 0.2f, 0.3f, 0.4f, 143.2f, 23.1f),
                },
                p3_cross_check = Array.Empty<Scene006PromptSelection.CrossCheck>(),
            };
        }

        /// <summary>
        /// BC-P2-5: the E-empty artifact is still produced and carries a
        /// literal JSON null, never a `-1` sentinel a reader could mistake
        /// for a tick.
        /// </summary>
        [Test]
        public void EmptyEligibilityArtifactSerializesSelectedTickAsNull()
        {
            Scene006PromptSelection.Artifact artifact =
                SyntheticArtifact(Scene006PromptSelection.NoSelection);
            string json = Scene006PromptSelection.Serialize(artifact);

            StringAssert.Contains("\"selected_tick\": null", json);
            Assert.IsFalse(
                json.Contains("\"selected_tick\": -1"),
                "the sentinel must not survive into the artifact");
            StringAssert.Contains(
                "\"terminal\": \"T1P2_PROMPT_LAW_UNSATISFIABLE\"", json);

            Scene006PromptSelection.Artifact roundTrip =
                Scene006PromptSelection.Deserialize(json);
            Assert.AreEqual(
                Scene006PromptSelection.NoSelection, roundTrip.selected_tick);
            Assert.AreEqual(
                Scene006PromptSelection.StatusPromptLawUnsatisfiable,
                roundTrip.status);
            Assert.AreEqual(52, roundTrip.d_v.visible_count);
        }

        [Test]
        public void SelectedArtifactRoundTripsWithItsTick()
        {
            string json = Scene006PromptSelection.Serialize(
                SyntheticArtifact(7));
            StringAssert.Contains("\"selected_tick\": 7", json);
            Assert.AreEqual(
                7,
                Scene006PromptSelection.Deserialize(json).selected_tick);
            Assert.Throws<InvalidOperationException>(
                () => Scene006PromptSelection.Deserialize(
                    "{\"schema_version\":\"wrong\"}"));
        }

        /// <summary>
        /// B3: the capture-time recompute has to notice any drift. Each
        /// mutation below is a row the renderer must refuse to write over.
        /// </summary>
        [Test]
        public void CompareCatchesEveryDriftedRow()
        {
            Scene006PromptSelection.Artifact committed = SyntheticArtifact(7);
            CollectionAssert.IsEmpty(
                Scene006PromptSelection.Compare(
                    committed, SyntheticArtifact(7)));

            (string name, Action<Scene006PromptSelection.Artifact> mutate)[]
                cases =
                {
                    ("selected-tick", a => a.selected_tick = 8),
                    ("diagnostic-tick", a => a.diagnostic_tick = 280),
                    ("status", a => a.status = "SOMETHING_ELSE"),
                    ("trace", a => a.trace_sha256 = new string('c', 64)),
                    ("domain-count", a => a.d_v.visible_count = 51),
                    ("band-q05", a => a.min_side_band.q05 = 35.5),
                    ("band-q95", a => a.off_nadir_band.q95 = 44.0),
                    ("warmup-eligible", a => a.warmup_ticks[0].eligible = true),
                    ("warmup-min-side",
                        a => a.warmup_ticks[0].min_side_px = 143.3f),
                    ("measurement-status",
                        a => a.measurement_ticks[0].target_box_status =
                            "TARGET_VISIBLE_UNPROJECTABLE"),
                    ("measurement-off-nadir",
                        a => a.measurement_ticks[0].applied_off_nadir_deg =
                            44.9f),
                };
            foreach ((string name, Action<Scene006PromptSelection.Artifact>
                mutate) in cases)
            {
                Scene006PromptSelection.Artifact drifted = SyntheticArtifact(7);
                mutate(drifted);
                CollectionAssert.IsNotEmpty(
                    Scene006PromptSelection.Compare(committed, drifted),
                    "drift went unnoticed: " + name);
            }
        }

        /// <summary>
        /// BC-P2-10: the rewrite is a scanner, not a text search. A string
        /// value containing "NaN" or "null" is data and must survive
        /// untouched in both directions.
        /// </summary>
        [Test]
        public void StrictJsonRewritesValueTokensAndLeavesStringsAlone()
        {
            const string dialect =
                "{\"note\": \"NaN and null and \\\"Infinity\\\"\", "
                + "\"a\": NaN, \"b\": [1.5, -Infinity, Infinity], \"c\": -1}";
            const string strict =
                "{\"note\": \"NaN and null and \\\"Infinity\\\"\", "
                + "\"a\": null, \"b\": [1.5, null, null], \"c\": -1}";

            Assert.AreEqual(strict, Scene006Json.ToStrictJson(dialect));
            Assert.IsTrue(Scene006Json.ContainsNonFiniteToken(dialect));
            Assert.IsFalse(Scene006Json.ContainsNonFiniteToken(strict));

            // Reverse: every remaining null is an unavailable number.
            const string back =
                "{\"note\": \"NaN and null and \\\"Infinity\\\"\", "
                + "\"a\": NaN, \"b\": [1.5, NaN, NaN], \"c\": -1}";
            Assert.AreEqual(back, Scene006Json.FromStrictJson(strict));
            Assert.Throws<InvalidOperationException>(
                () => Scene006Json.ToStrictJson("{\"unterminated: NaN}"));
        }

        /// <summary>
        /// BC-P2-10 at the artifact boundary: an unprojectable warmup frame
        /// has no `min_side_px` and no edge margins. Those fields ship as
        /// JSON `null` — never a bare `NaN`, and never a finite sentinel
        /// that would read as a measurement — and come back as NaN.
        /// </summary>
        [Test]
        public void SerializedArtifactIsStandardJsonAndKeepsUnavailableNumbers()
        {
            Scene006PromptSelection.Artifact artifact = SyntheticArtifact(
                Scene006PromptSelection.NoSelection);
            Scene006PromptSelection.WarmupTick invisible = Tick(
                0, 0f, 0f, 0f, 0f, float.NaN, 42.5f,
                visible: false, status: "TARGET_NOT_VISIBLE");
            invisible.target_bbox_xywh_norm = null;
            invisible.margin_left_px = float.NaN;
            invisible.margin_right_px = float.NaN;
            invisible.margin_top_px = float.NaN;
            invisible.margin_bottom_px = float.NaN;
            artifact.warmup_ticks = new[]
            {
                invisible, artifact.warmup_ticks[0],
            };
            artifact.measurement_ticks[0].min_side_px = float.NaN;

            string json = Scene006PromptSelection.Serialize(artifact);
            Assert.IsFalse(
                Scene006Json.ContainsNonFiniteToken(json),
                "a committed artifact must be readable by a strict parser");
            StringAssert.Contains("\"min_side_px\": null", json);
            StringAssert.Contains("\"margin_left_px\": null", json);
            StringAssert.Contains("\"selected_tick\": null", json);

            Scene006PromptSelection.Artifact roundTrip =
                Scene006PromptSelection.Deserialize(json);
            Assert.IsTrue(
                float.IsNaN(roundTrip.warmup_ticks[0].min_side_px),
                "null must come back as unavailable, not as 0");
            Assert.IsTrue(
                float.IsNaN(roundTrip.warmup_ticks[0].margin_left_px));
            Assert.IsTrue(
                float.IsNaN(roundTrip.measurement_ticks[0].min_side_px));
            Assert.AreEqual(
                Scene006PromptSelection.NoSelection, roundTrip.selected_tick);
            CollectionAssert.IsEmpty(
                Scene006PromptSelection.Compare(artifact, roundTrip),
                "the strict round trip must not perturb any compared row");
        }

        [Test]
        public void WarmupPoolIsTheT6AcquisitionWindow()
        {
            CollectionAssert.AreEqual(
                new[] { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 },
                Scene006PromptSelection.WarmupPool());
            foreach (int k in Scene006PromptSelection.WarmupPool())
            {
                CollectionAssert.DoesNotContain(
                    Scene006ProbeRenderer.ProbeTicks(),
                    k,
                    "the prompt pool never intersects the measurement set");
            }
        }

        /// <summary>
        /// The law's applied off-nadir is the gimbal law's own clamped
        /// angle, read through the single definition the replay uses.
        /// </summary>
        [Test]
        public void AppliedOffNadirIsTheClampedGimbalLawAngle()
        {
            var hover = new Vector3(0f, 16f, 0f);
            Assert.AreEqual(
                0f,
                Scene006GimbalReplay.AppliedOffNadirDeg(
                    hover, new Vector3(0f, 0f, 0f)),
                1e-4f,
                "straight below the gimbal is nadir");
            Assert.AreEqual(
                45f,
                Scene006GimbalReplay.AppliedOffNadirDeg(
                    hover, new Vector3(16f, 0f, 0f)),
                1e-4f);
            Assert.AreEqual(
                Scene006GimbalReplay.MaximumOffNadirDeg,
                Scene006GimbalReplay.AppliedOffNadirDeg(
                    hover, new Vector3(400f, 0f, 0f)),
                1e-6f,
                "beyond the limit the law clamps");
        }
    }
}
