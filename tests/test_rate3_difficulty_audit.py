"""P1-M2-RATE-003 Amendment DR-B B2 difficulty-audit tests (BC-DRB-2/3)."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.build_rate3_difficulty_audit import (
    D1_GEOMETRY_ARTIFACT_PATH,
    FLOAT_ABS_TOLERANCE,
    MUST_PASS_GATES,
    RECORD_ONLY_GATES,
    ROAD_AUDIT_COMPARED_FIELDS,
    build_difficulty_audit,
    declared_config_difference,
    typed_equality_findings,
)
from tools.build_scene004_geometry import SCENARIO_PATH as D1_SCENARIO_PATH
from tools.run_track_experiment import PROJECT_ROOT

D2_SCENARIO_PATH = PROJECT_ROOT / "config" / "scenario.p1-scene-004-d2.json"


def road_audit(scenario_id="p1-scene-004", **overrides):
    report = {
        "schema_version": "p1-scene-road-audit/v1",
        "scenario_id": scenario_id,
        "status": "CLEAR",
        "route_sample_count": 427,
        "road_violation_count": 0,
        "road_violations": [],
        "audited_obstacle_count": 779,
        "overhead_exemption_count": 0,
        "obstacle_violation_count": 0,
        "vehicle_violation_count": 0,
        "prop_violation_count": 0,
        "nature_violation_count": 0,
        "building_violation_count": 0,
        "other_violation_count": 0,
        "obstacle_violations": [],
    }
    report.update(overrides)
    return report


def write(path: Path, value) -> Path:
    path.write_text(json.dumps(value, indent=1) + "\n", encoding="utf-8")
    return path


class TypedEqualityTests(unittest.TestCase):
    def test_bit_equal_floats_pass(self):
        self.assertEqual(typed_equality_findings(0.1 + 0.2, 0.1 + 0.2), [])

    def test_float_fallback_is_exactly_1e_minus_9(self):
        self.assertEqual(FLOAT_ABS_TOLERANCE, 1e-9)
        self.assertEqual(typed_equality_findings(1.0, 1.0 + 5e-10), [])
        self.assertEqual(len(typed_equality_findings(1.0, 1.0 + 1e-8)), 1)

    def test_integers_get_no_float_fallback(self):
        self.assertEqual(typed_equality_findings(49, 49), [])
        self.assertEqual(len(typed_equality_findings(49, 50)), 1)
        self.assertEqual(len(typed_equality_findings(49, 49.0)), 1)

    def test_booleans_strings_and_enums_are_exact(self):
        self.assertEqual(typed_equality_findings(True, True), [])
        self.assertEqual(len(typed_equality_findings(True, 1)), 1)
        self.assertEqual(len(typed_equality_findings("CLEAR", "OK")), 1)

    def test_array_length_and_order_are_exact(self):
        self.assertEqual(typed_equality_findings([1, 2, 3], [1, 2, 3]), [])
        self.assertEqual(len(typed_equality_findings([1, 2], [1, 2, 3])), 1)
        self.assertEqual(len(typed_equality_findings([2, 1], [1, 2])), 2)

    def test_key_set_mismatch_fails_closed(self):
        findings = typed_equality_findings({"a": 1}, {"a": 1, "b": 2})
        self.assertEqual(len(findings), 1)
        self.assertIn("key set mismatch", findings[0])

    def test_non_finite_and_missing_values_fail_closed(self):
        self.assertEqual(
            len(typed_equality_findings(float("nan"), float("nan"))), 1
        )
        self.assertEqual(len(typed_equality_findings(float("inf"), 1.0)), 1)
        self.assertEqual(len(typed_equality_findings(None, 1.0)), 1)

    def test_nested_paths_are_reported(self):
        findings = typed_equality_findings(
            {"gate": {"value": 1.0}}, {"gate": {"value": 2.0}}, "root"
        )
        self.assertEqual(len(findings), 1)
        self.assertIn("root.gate.value", findings[0])


class DeclaredConfigDifferenceTests(unittest.TestCase):
    def test_real_d1_and_d2_configs_differ_only_where_declared(self):
        d1 = json.loads(D1_SCENARIO_PATH.read_text())
        d2 = json.loads(D2_SCENARIO_PATH.read_text())
        result = declared_config_difference(d2, d1)
        self.assertTrue(result["passed"], result["findings"])
        self.assertEqual(
            result["observed_difference_keys"],
            ["scenario_id", "target.speed_mps"],
        )

    def test_an_undeclared_difference_fails_closed(self):
        d1 = json.loads(D1_SCENARIO_PATH.read_text())
        d2 = json.loads(D2_SCENARIO_PATH.read_text())
        d2["drone"]["initial_altitude_m"] = 26.0
        result = declared_config_difference(d2, d1)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("initial_altitude_m" in finding for finding in result["findings"])
        )

    def test_a_missing_declared_difference_fails_closed(self):
        d1 = json.loads(D1_SCENARIO_PATH.read_text())
        result = declared_config_difference(dict(d1), d1)
        self.assertFalse(result["passed"])


class DifficultyAuditTests(unittest.TestCase):
    def audit(self, directory, *, difficulty=None, baseline=None, **kwargs):
        directory = Path(directory)
        difficulty_path = write(
            directory / "d2-road-audit.json",
            difficulty
            if difficulty is not None
            else road_audit("p1-scene-004-d2"),
        )
        baseline_path = write(
            directory / "d1-road-audit.json",
            baseline if baseline is not None else road_audit("p1-scene-004"),
        )
        return build_difficulty_audit(
            difficulty_scenario_path=D2_SCENARIO_PATH,
            difficulty_label="D2",
            difficulty_road_audit_path=difficulty_path,
            d1_road_audit_path=baseline_path,
            **kwargs,
        )

    def test_must_pass_gates_pass_and_equal_the_archived_d1_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = self.audit(directory)
            self.assertEqual(artifact["status"], "ENVELOPE_OK", artifact["failures"])
            for gate in MUST_PASS_GATES:
                row = artifact["must_pass"]["gates"][gate]
                self.assertTrue(row["gate_passed"], gate)
                self.assertTrue(row["equal_to_d1_baseline"], row)
            self.assertTrue(
                artifact["must_pass"]["geometry_value_equality"]["passed"]
            )
            self.assertFalse(artifact["d1_baseline"]["regenerated"])

    def test_speed_derived_gates_are_record_only_triples(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = self.audit(directory)
            for gate in RECORD_ONLY_GATES:
                triple = artifact["record_only"][gate]
                self.assertIn("difficulty_value", triple)
                self.assertIn("d1_baseline_value", triple)
                self.assertIn("delta", triple)
                self.assertFalse(triple["gating"])
            loop = artifact["record_only"]["loop_period_s"]
            # 62.14213562373095 / 8.0; far outside the [30, 45] s D1 gate and
            # deliberately not part of the status.
            self.assertAlmostEqual(
                loop["difficulty_value"], 7.767766952966369, places=12
            )
            self.assertEqual(artifact["status"], "ENVELOPE_OK")
            self.assertTrue(artifact["record_only"]["per_distractor"])
            for row in artifact["record_only"]["per_distractor"]:
                self.assertIn("fully_in_frame_ticks", row)
                self.assertIn("tick_count", row)

    def test_missing_route_legality_reports_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = build_difficulty_audit(
                difficulty_scenario_path=D2_SCENARIO_PATH,
                difficulty_label="D2",
                difficulty_road_audit_path=None,
                d1_road_audit_path=Path(directory) / "absent.json",
            )
            self.assertEqual(artifact["status"], "ENVELOPE_OUT_OF_BOUNDS")
            self.assertTrue(
                any("route_legality" in failure for failure in artifact["failures"])
            )

    def test_route_legality_gate_requires_clear_and_zero_violations(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = self.audit(
                directory,
                difficulty=road_audit(
                    "p1-scene-004-d2",
                    status="VIOLATIONS",
                    road_violation_count=2,
                    road_violations=[{"sample_index": 1}],
                ),
                baseline=road_audit(
                    "p1-scene-004",
                    status="VIOLATIONS",
                    road_violation_count=2,
                    road_violations=[{"sample_index": 1}],
                ),
            )
            self.assertEqual(artifact["status"], "ENVELOPE_OUT_OF_BOUNDS")
            legality = artifact["must_pass"]["route_legality"]
            # Field equality holds, but it never replaces the pass gate.
            self.assertTrue(legality["equal_to_d1_baseline"])
            self.assertFalse(legality["gate_passed"])
            self.assertFalse(legality["passed"])

    def test_route_legality_field_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = self.audit(
                directory,
                difficulty=road_audit(
                    "p1-scene-004-d2", route_sample_count=428
                ),
            )
            self.assertEqual(artifact["status"], "ENVELOPE_OUT_OF_BOUNDS")
            legality = artifact["must_pass"]["route_legality"]
            self.assertTrue(legality["gate_passed"])
            self.assertFalse(legality["equal_to_d1_baseline"])
            self.assertTrue(
                any(
                    "route_sample_count" in finding
                    for finding in legality["equality_findings"]
                )
            )

    def test_scenario_id_is_the_only_exempt_route_audit_field(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = self.audit(directory)
            legality = artifact["must_pass"]["route_legality"]
            self.assertEqual(legality["exempt_fields"], ["scenario_id"])
            self.assertEqual(
                legality["compared_fields"], list(ROAD_AUDIT_COMPARED_FIELDS)
            )
            self.assertNotIn("scenario_id", ROAD_AUDIT_COMPARED_FIELDS)
            self.assertEqual(len(ROAD_AUDIT_COMPARED_FIELDS), 14)

    def test_committed_evidence_chain_reproduces_envelope_ok(self):
        """BC-B2-CQ2: the archived D1/D2 reports must actually pass."""

        d1_report = PROJECT_ROOT / "docs" / "evidence" / (
            "P1-M2-RATE-003-d1-road-audit.json"
        )
        d2_report = PROJECT_ROOT / "docs" / "evidence" / (
            "P1-M2-RATE-003-d2-road-audit.json"
        )
        committed = PROJECT_ROOT / "docs" / "evidence" / (
            "P1-M2-RATE-003-d2-difficulty-audit.json"
        )
        for path in (d1_report, d2_report, committed):
            self.assertTrue(path.is_file(), path)
        artifact = build_difficulty_audit(
            difficulty_scenario_path=D2_SCENARIO_PATH,
            difficulty_label="D2",
            difficulty_road_audit_path=d2_report,
            d1_road_audit_path=d1_report,
        )
        self.assertEqual(artifact["status"], "ENVELOPE_OK", artifact["failures"])
        self.assertEqual(artifact["failures"], [])
        stored = json.loads(committed.read_text())
        self.assertEqual(stored["status"], "ENVELOPE_OK")
        # `generated_unix_s` is the only field a re-run may change.
        stored.pop("generated_unix_s")
        artifact.pop("generated_unix_s")
        self.assertEqual(stored, artifact)

    def test_geometry_drift_against_the_baseline_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = json.loads(D1_GEOMETRY_ARTIFACT_PATH.read_text())
            baseline["gates"]["max_slant_range_m"]["value"] += 0.01
            drifted = write(Path(directory) / "baseline.json", baseline)
            artifact = self.audit(
                directory, d1_geometry_artifact_path=drifted
            )
            self.assertEqual(artifact["status"], "ENVELOPE_OUT_OF_BOUNDS")
            self.assertTrue(
                any(
                    "must_pass_gate_not_equal_to_d1" in failure
                    for failure in artifact["failures"]
                )
            )


if __name__ == "__main__":
    unittest.main()
