"""P1-M2-RATE-003 §6 + Amendment DR-B B1 decision-function tests."""

from __future__ import annotations

import itertools
import unittest

from controller import rate3_decision
from controller.rate3_decision import (
    DIFFICULTIES,
    PHASES,
    RATES,
    THETA,
    THETA_GEOM,
    Rate3DecisionError,
    build_decision_body,
    build_difficulty_cell,
    difficulty_disposition,
    median_of_three,
    quantile_type7,
    research_final_action,
)


def row(
    difficulty,
    phase,
    rate_hz,
    *,
    conditional,
    c_geom=0.9,
    c_track=0.5,
    admissible=True,
    calibration_sha256=None,
    lap_period_s=31.0,
):
    slot = f"rs3-{difficulty.lower()}-p{phase}-r{rate_hz}"
    return {
        "run_id": slot,
        "difficulty": difficulty,
        "phase": phase,
        "rate_hz": rate_hz,
        "admissible": admissible,
        "c_track_given_geom": conditional,
        "c_geom": c_geom,
        "c_track": c_track,
        "calibration_sha256": (
            calibration_sha256
            or f"{difficulty.lower()}{phase}".ljust(64, "0")
        ),
        "lap_period_s": lap_period_s,
    }


def cell_rows(difficulty, fast, slow, **overrides):
    """Six rows for one difficulty; `fast`/`slow` are per-phase sequences."""

    rows = []
    for index, phase in enumerate(PHASES):
        rows.append(
            row(difficulty, phase, 20, conditional=fast[index], **overrides)
        )
        rows.append(
            row(difficulty, phase, 5, conditional=slow[index], **overrides)
        )
    return rows


class QuantileTests(unittest.TestCase):
    def test_type7_matches_the_numpy_reference_value_for_value(self):
        numpy = None
        try:
            import numpy  # noqa: F401
        except ImportError:  # pragma: no cover - reference not installed
            numpy = None
        samples = [
            [1.0],
            [1.0, 2.0],
            [3.0, 1.0, 2.0],
            [0.5, 0.25, 0.75, 1.0, 0.0],
            [float(value) * 0.37 - 4.0 for value in range(17)],
            [-2.5, -2.5, 0.0, 7.25, 7.25, 9.0, 11.5],
        ]
        probabilities = (0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0, 1.0 / 3.0)
        if numpy is None:
            self.skipTest("numpy reference implementation is not installed")
        for values, probability in itertools.product(samples, probabilities):
            with self.subTest(values=values, probability=probability):
                self.assertEqual(
                    quantile_type7(values, probability),
                    float(
                        numpy.quantile(
                            numpy.array(values, dtype=float),
                            probability,
                            method="linear",
                        )
                    ),
                )

    def test_type7_matches_an_independent_hand_computation(self):
        # h = (n-1)p; n = 5, p = 0.05 -> h = 0.2 between 0.0 and 0.25.
        self.assertAlmostEqual(
            quantile_type7([0.0, 0.25, 0.5, 0.75, 1.0], 0.05),
            0.0 + 0.2 * 0.25,
            places=15,
        )
        self.assertEqual(quantile_type7([0.0, 0.25, 0.5, 0.75, 1.0], 0.5), 0.5)

    def test_quantile_rejects_empty_and_non_finite_inputs(self):
        with self.assertRaises(Rate3DecisionError):
            quantile_type7([], 0.5)
        with self.assertRaises(Rate3DecisionError):
            quantile_type7([1.0, float("nan")], 0.5)
        with self.assertRaises(Rate3DecisionError):
            quantile_type7([1.0], 1.5)

    def test_median_of_three_has_no_interpolation(self):
        self.assertEqual(median_of_three([0.1, 0.9, 0.4]), 0.4)
        with self.assertRaises(Rate3DecisionError):
            median_of_three([0.1, 0.9])


class DispositionTests(unittest.TestCase):
    def test_floor_precedes_ceiling_and_rate_effect(self):
        # Ordered rules: floor is decided before any rate-effect branch, so a
        # large delta inside the floor band is still FLOOR.
        self.assertEqual(
            difficulty_disposition(c_20=0.29, c_5=0.10, delta=0.19, complete=True),
            "FLOOR",
        )

    def test_ceiling_requires_both_rates_and_small_delta(self):
        self.assertEqual(
            difficulty_disposition(c_20=0.9, c_5=0.88, delta=0.02, complete=True),
            "CEILING",
        )
        self.assertEqual(
            difficulty_disposition(c_20=0.9, c_5=0.79, delta=0.11, complete=True),
            "RATE_EFFECT_POSITIVE",
        )

    def test_theta_boundary_is_inclusive_for_no_effect(self):
        self.assertEqual(
            difficulty_disposition(
                c_20=0.60, c_5=0.55, delta=THETA, complete=True
            ),
            "NO_EFFECT_DETECTED_MIDBAND",
        )
        self.assertEqual(
            difficulty_disposition(
                c_20=0.60, c_5=0.55, delta=-THETA, complete=True
            ),
            "NO_EFFECT_DETECTED_MIDBAND",
        )

    def test_inverted_and_incomplete_branches(self):
        self.assertEqual(
            difficulty_disposition(c_20=0.4, c_5=0.6, delta=-0.2, complete=True),
            "RATE_EFFECT_INVERTED",
        )
        self.assertEqual(
            difficulty_disposition(c_20=0.4, c_5=0.6, delta=-0.2, complete=False),
            "BLOCKED_INCOMPLETE_CELL",
        )
        self.assertEqual(
            difficulty_disposition(
                c_20=float("nan"), c_5=0.6, delta=0.0, complete=True
            ),
            "BLOCKED_INCOMPLETE_CELL",
        )

    def test_every_disposition_pair_produces_exactly_one_final_action(self):
        for d1, d2 in itertools.product(
            rate3_decision.DISPOSITIONS, repeat=2
        ):
            action = research_final_action(d1_disposition=d1, d2_disposition=d2)
            self.assertIn(action, rate3_decision.FINAL_ACTIONS)
            self.assertNotIn("_D1", action)

    def test_d1_never_changes_the_final_action_choice(self):
        for d1 in rate3_decision.DISPOSITIONS:
            if d1 == "BLOCKED_INCOMPLETE_CELL":
                continue
            self.assertEqual(
                research_final_action(
                    d1_disposition=d1, d2_disposition="RATE_EFFECT_POSITIVE"
                ),
                "M2_RATE_CONTRAST_ESTABLISHED",
            )


class DifficultyCellTests(unittest.TestCase):
    def test_complete_cell_reports_paired_and_unconditional_quantities(self):
        rows = cell_rows("D1", [0.9, 0.85, 0.95], [0.5, 0.45, 0.55])
        cell = build_difficulty_cell("D1", rows)
        self.assertTrue(cell["complete"])
        self.assertEqual(cell["c_20"], 0.9)
        self.assertEqual(cell["c_5"], 0.5)
        self.assertAlmostEqual(cell["delta"], 0.4, places=12)
        self.assertEqual(len(cell["delta_geom_i"]), 3)
        self.assertEqual(cell["delta_track_i"], [0.0, 0.0, 0.0])
        self.assertEqual(cell["disposition"], "RATE_EFFECT_POSITIVE")
        self.assertFalse(cell["flags"]["CGEOM_DIVERGENCE_FLAG"])

    def test_missing_or_inadmissible_run_blocks_the_cell(self):
        rows = cell_rows("D1", [0.9, 0.85, 0.95], [0.5, 0.45, 0.55])
        rows[0]["admissible"] = False
        cell = build_difficulty_cell("D1", rows)
        self.assertFalse(cell["complete"])
        self.assertEqual(cell["disposition"], "BLOCKED_INCOMPLETE_CELL")
        self.assertIsNone(cell["flags"]["CGEOM_DIVERGENCE_FLAG"])

        cell = build_difficulty_cell("D1", rows[:-1])
        self.assertEqual(cell["disposition"], "BLOCKED_INCOMPLETE_CELL")

    def test_pairing_mismatch_makes_both_runs_of_the_pair_non_admissible(self):
        rows = cell_rows("D1", [0.9, 0.85, 0.95], [0.5, 0.45, 0.55])
        rows[1]["calibration_sha256"] = "f" * 64
        findings = rate3_decision.pairing_findings(rows)["D1"]
        self.assertEqual(len(findings), 1)
        self.assertIn("BC-DRB-5", findings[0])
        cell = build_difficulty_cell("D1", rows)
        self.assertEqual(cell["disposition"], "BLOCKED_INCOMPLETE_CELL")

    def test_dispersion_and_sign_flags(self):
        rows = cell_rows("D1", [0.90, 0.50, 0.60], [0.50, 0.52, 0.55])
        cell = build_difficulty_cell("D1", rows)
        self.assertTrue(cell["flags"]["DISPERSION_FLAG"])
        self.assertTrue(cell["flags"]["SIGN_INCONSISTENT_FLAG"])

    def test_cgeom_divergence_flag_uses_theta_geom(self):
        rows = cell_rows("D1", [0.9, 0.85, 0.95], [0.5, 0.45, 0.55])
        for entry in rows:
            entry["c_geom"] = 0.90 if entry["rate_hz"] == 20 else 0.86
        cell = build_difficulty_cell("D1", rows)
        self.assertFalse(cell["flags"]["CGEOM_DIVERGENCE_FLAG"])
        for entry in rows:
            if entry["phase"] == 2 and entry["rate_hz"] == 5:
                entry["c_geom"] = 0.80
        cell = build_difficulty_cell("D1", rows)
        self.assertTrue(cell["flags"]["CGEOM_DIVERGENCE_FLAG"])
        self.assertEqual(cell["theta_geom"], THETA_GEOM)
        self.assertEqual(THETA_GEOM, 0.05)


class ResearchDecisionTests(unittest.TestCase):
    def rows(self, *, d1, d2, **overrides):
        return [
            *cell_rows("D1", d1[0], d1[1], **overrides),
            *cell_rows("D2", d2[0], d2[1], **overrides),
        ]

    def test_ceiling_d1_and_positive_d2_establishes_the_contrast(self):
        body = build_decision_body(
            self.rows(
                d1=([0.90, 0.91, 0.92], [0.88, 0.89, 0.90]),
                d2=([0.70, 0.72, 0.71], [0.40, 0.42, 0.41]),
            )
        )
        self.assertEqual(body["dispositions"]["D1"], "CEILING")
        self.assertEqual(body["final_action"], "M2_RATE_CONTRAST_ESTABLISHED")
        self.assertFalse(body["ladder_premise_violated"])
        self.assertFalse(body["heterogeneity_qualified"])
        self.assertFalse(body["dr_referral_required"])

    def test_non_ceiling_d1_sets_the_premise_flag_and_forces_dr_referral(self):
        body = build_decision_body(
            self.rows(
                d1=([0.60, 0.61, 0.62], [0.58, 0.59, 0.60]),
                d2=([0.70, 0.72, 0.71], [0.40, 0.42, 0.41]),
            )
        )
        self.assertTrue(body["ladder_premise_violated"])
        self.assertTrue(body["dr_referral_required"])
        self.assertEqual(body["final_action"], "M2_RATE_CONTRAST_ESTABLISHED")

    def test_heterogeneity_forces_a_qualifier_and_dr_referral(self):
        body = build_decision_body(
            self.rows(
                d1=([0.90, 0.91, 0.92], [0.88, 0.89, 0.90]),
                d2=([0.90, 0.50, 0.72], [0.40, 0.52, 0.41]),
            )
        )
        self.assertEqual(body["final_action"], "M2_RATE_CONTRAST_ESTABLISHED")
        self.assertTrue(body["heterogeneity_qualified"])
        self.assertIsNotNone(body["qualifier_text"])
        self.assertIn("Delta_1=", body["qualifier_text"])
        self.assertTrue(body["dr_referral_required"])

    def test_h2_flag_compares_c20_d2_with_c5_d1(self):
        body = build_decision_body(
            self.rows(
                d1=([0.90, 0.91, 0.92], [0.50, 0.50, 0.50]),
                d2=([0.90, 0.90, 0.90], [0.40, 0.42, 0.41]),
            )
        )
        self.assertAlmostEqual(body["h2_value"], 0.40, places=12)
        self.assertTrue(body["H2_DIVERGENCE_FLAG"])
        self.assertIsNone(body["h2_unavailable_reason"])

    def test_h2_and_cgeom_flags_are_null_when_a_cell_is_incomplete(self):
        rows = self.rows(
            d1=([0.90, 0.91, 0.92], [0.88, 0.89, 0.90]),
            d2=([0.70, 0.72, 0.71], [0.40, 0.42, 0.41]),
        )
        rows[0]["admissible"] = False
        body = build_decision_body(rows)
        self.assertEqual(body["final_action"], "BLOCKED_INCOMPLETE")
        self.assertIsNone(body["H2_DIVERGENCE_FLAG"])
        self.assertIsNone(body["CGEOM_DIVERGENCE_FLAG"])
        self.assertIsNotNone(body["h2_unavailable_reason"])
        self.assertIsNotNone(body["cgeom_flag_unavailable_reason"])

    def test_cgeom_divergence_never_changes_the_final_action(self):
        clean = self.rows(
            d1=([0.90, 0.91, 0.92], [0.88, 0.89, 0.90]),
            d2=([0.70, 0.72, 0.71], [0.40, 0.42, 0.41]),
        )
        diverged = [dict(entry) for entry in clean]
        for entry in diverged:
            entry["c_geom"] = 0.95 if entry["rate_hz"] == 20 else 0.60
        clean_body = build_decision_body(clean)
        diverged_body = build_decision_body(diverged)
        self.assertEqual(
            clean_body["final_action"], diverged_body["final_action"]
        )
        self.assertFalse(clean_body["CGEOM_DIVERGENCE_FLAG"])
        self.assertTrue(diverged_body["CGEOM_DIVERGENCE_FLAG"])
        self.assertTrue(diverged_body["cgeom_divergence_qualified"])
        self.assertIn(
            "delta_geom", diverged_body["cgeom_qualifier_text"]
        )
        self.assertTrue(diverged_body["dr_referral_required"])

    def test_pseudo_ceiling_caveat_is_required_on_a_diverged_d2_ceiling(self):
        rows = self.rows(
            d1=([0.90, 0.91, 0.92], [0.88, 0.89, 0.90]),
            d2=([0.90, 0.91, 0.92], [0.88, 0.89, 0.90]),
        )
        for entry in rows:
            if entry["difficulty"] == "D2":
                entry["c_geom"] = 0.95 if entry["rate_hz"] == 20 else 0.50
        body = build_decision_body(rows)
        self.assertEqual(body["final_action"], "H1_FALSIFIED_CEILING_AT_D2")
        self.assertTrue(body["pseudo_ceiling_caveat_required"])

    def test_unconditional_fields_are_present_even_when_the_flag_is_false(self):
        body = build_decision_body(
            self.rows(
                d1=([0.90, 0.91, 0.92], [0.88, 0.89, 0.90]),
                d2=([0.70, 0.72, 0.71], [0.40, 0.42, 0.41]),
            )
        )
        for difficulty in DIFFICULTIES:
            cell = body["difficulties"][difficulty]
            self.assertEqual(len(cell["c_geom_pairs"]), len(PHASES))
            self.assertEqual(len(cell["c_track_pairs"]), len(PHASES))
            self.assertIsNotNone(cell["delta_track"])

    def test_sensitivity_band_is_reported_without_a_second_disposition(self):
        body = build_decision_body(
            self.rows(
                d1=([0.90, 0.91, 0.92], [0.88, 0.89, 0.90]),
                d2=([0.70, 0.72, 0.71], [0.40, 0.42, 0.41]),
            )
        )
        sensitivity = body["difficulties"]["D2"]["sensitivity"]
        self.assertEqual(
            sorted(sensitivity), sorted(str(value) for value in (0.03, 0.05, 0.1))
        )
        self.assertEqual(body["dispositions"]["D2"], "RATE_EFFECT_POSITIVE")

    def test_rate_and_phase_coverage_is_exactly_the_frozen_design(self):
        self.assertEqual(RATES, (20, 5))
        self.assertEqual(PHASES, (1, 2, 3))
        self.assertEqual(DIFFICULTIES, ("D1", "D2"))


if __name__ == "__main__":
    unittest.main()
