"""S6 审计协议：三互斥 panel、配额、通过线与 attempt 状态机（§2.7，BC-DATA-5）。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import audit_tool, contract  # noqa: E402


def pool(strata: dict[str, int]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for stratum, count in strata.items():
        for index in range(count):
            mapping[f"{stratum}#sample-{index:04d}"] = stratum
    return mapping


class SeedTest(unittest.TestCase):
    def test_seed_template_is_per_audit_and_panel(self) -> None:
        self.assertEqual(
            audit_tool.panel_seed("A2", 1), "P1-VLM-DATA-001/audit/A2/panel-1"
        )

    def test_unknown_audit_or_panel_is_rejected(self) -> None:
        with self.assertRaises(audit_tool.AuditError):
            audit_tool.panel_seed("A9", 0)
        with self.assertRaises(audit_tool.AuditError):
            audit_tool.panel_seed("A1", 3)

    def test_sample_key_is_digest_then_utf8_id(self) -> None:
        key = audit_tool.sample_sort_key("A3", 0, "frame|program|object")
        self.assertEqual(len(key[0]), 32)
        self.assertEqual(key[1], "frame|program|object".encode("utf-8"))


class QuotaTest(unittest.TestCase):
    def test_base_then_capacity_descending_transfer(self) -> None:
        allocation = audit_tool.allocate_quota(
            {"a": 30, "b": 30, "c": 4}, base=16, total=48
        )
        self.assertEqual(sum(allocation.values()), 48)
        self.assertEqual(allocation["c"], 4)  # 格内不足则全取
        self.assertEqual(allocation["a"] + allocation["b"], 44)
        self.assertEqual(allocation["a"], 28)  # 余额按容量降序、并列按 key 升序转移

    def test_ties_break_on_stratum_key_bytes(self) -> None:
        allocation = audit_tool.allocate_quota({"a": 10, "b": 10}, base=4, total=9)
        self.assertEqual(sum(allocation.values()), 9)
        self.assertEqual(allocation["a"], 5)  # 并列按 key UTF-8 升序先补
        self.assertEqual(allocation["b"], 4)

    def test_insufficient_capacity_is_a_terminal(self) -> None:
        with self.assertRaises(audit_tool.AuditTerminal) as caught:
            audit_tool.allocate_quota({"a": 3, "b": 2}, base=16, total=200)
        self.assertEqual(caught.exception.terminal, "AUDIT_PANEL_CAPACITY_INSUFFICIENT")

    def test_base_above_total_is_reclaimed_deterministically(self) -> None:
        allocation = audit_tool.allocate_quota({"a": 50, "b": 50}, base=40, total=50)
        self.assertEqual(sum(allocation.values()), 50)


class PanelTest(unittest.TestCase):
    def test_three_panels_are_mutually_exclusive(self) -> None:
        strata = {f"s{index}": 100 for index in range(12)}
        panels = audit_tool.build_panels(
            "A2",
            pool(strata),
            total=contract.AUDIT_A2_PANEL_SAMPLES,
            base=contract.AUDIT_A2_STRATUM_BASE,
        )
        self.assertEqual(len(panels), 3)
        seen: set[str] = set()
        for members in panels.values():
            self.assertEqual(len(members), contract.AUDIT_A2_PANEL_SAMPLES)
            self.assertEqual(seen & set(members), set())
            seen |= set(members)

    def test_a3_panels_use_four_strata_of_twenty_five(self) -> None:
        strata = {f"grid{index}": 150 for index in range(4)}
        panels = audit_tool.build_panels(
            "A3",
            pool(strata),
            total=contract.AUDIT_A3_PANEL_SAMPLES,
            base=contract.AUDIT_A3_STRATUM_BASE,
        )
        self.assertEqual(len(panels["panel-0"]), contract.AUDIT_A3_PANEL_SAMPLES)

    def test_capacity_shortfall_does_not_shrink_the_denominator(self) -> None:
        strata = {f"s{index}": 20 for index in range(12)}
        with self.assertRaises(audit_tool.AuditTerminal) as caught:
            audit_tool.build_panels(
                "A2",
                pool(strata),
                total=contract.AUDIT_A2_PANEL_SAMPLES,
                base=contract.AUDIT_A2_STRATUM_BASE,
            )
        self.assertEqual(caught.exception.terminal, "AUDIT_PANEL_CAPACITY_INSUFFICIENT")

    def test_generation_is_deterministic(self) -> None:
        strata = {f"s{index}": 100 for index in range(12)}
        first = audit_tool.build_panels("A2", pool(strata), total=200, base=16)
        second = audit_tool.build_panels("A2", pool(strata), total=200, base=16)
        self.assertEqual(first, second)

    def test_panels_differ_between_audits(self) -> None:
        strata = {f"s{index}": 100 for index in range(12)}
        a2 = audit_tool.build_panels("A2", pool(strata), total=200, base=16)
        a3 = audit_tool.build_panels("A3", pool(strata), total=200, base=16)
        self.assertNotEqual(a2["panel-0"], a3["panel-0"])


class VerdictTest(unittest.TestCase):
    def test_a1_class_map_allows_zero_failures(self) -> None:
        self.assertEqual(audit_tool.evaluate_a1(0, [True] * 20, [True] * 25, [])["verdict"], "PASS")
        self.assertEqual(audit_tool.evaluate_a1(1, [True] * 20, [True] * 25, [])["verdict"], "FAIL")

    def test_a1_crop_limits(self) -> None:
        one_bad = [True] * 19 + [False]
        self.assertEqual(audit_tool.evaluate_a1(0, one_bad, [True] * 25, [])["verdict"], "PASS")
        two_bad = [True] * 18 + [False, False]
        self.assertEqual(audit_tool.evaluate_a1(0, two_bad, [True] * 25, [])["verdict"], "FAIL")

    def test_group_colour_rejection_is_data_not_attempt_failure(self) -> None:
        """被判错词的组立即永久 UNVERIFIED，不计入 (b)/(c) 的失败条数。"""
        result = audit_tool.evaluate_a1(
            0, [True] * 20, [True] * 25, ["Vehicle_Bus_color02|color02"]
        )
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(
            result["permanently_unverified_groups"], ["Vehicle_Bus_color02|color02"]
        )

    def test_a2_limits_use_floor_of_the_rates(self) -> None:
        result = audit_tool.evaluate_a2(200, 150, rejections=10, false_includes=3)
        self.assertEqual(result["reject_limit"], 10)
        self.assertEqual(result["false_include_limit"], 3)
        self.assertEqual(result["verdict"], "PASS")

    def test_a2_false_include_denominator_is_panel_ok_count(self) -> None:
        strict = audit_tool.evaluate_a2(200, 50, rejections=0, false_includes=2)
        self.assertEqual(strict["false_include_limit"], 1)
        self.assertEqual(strict["verdict"], "FAIL")

    def test_a2_mechanical_track_uses_crosscheck_thresholds(self) -> None:
        self.assertEqual(audit_tool.evaluate_a2_mechanical(0.95, 0.6)["verdict"], "PASS")
        self.assertEqual(audit_tool.evaluate_a2_mechanical(0.85, 0.6)["verdict"], "FAIL")
        self.assertEqual(audit_tool.evaluate_a2_mechanical(0.95, 0.4)["verdict"], "FAIL")

    def test_a3_tolerates_no_false_unique(self) -> None:
        self.assertEqual(audit_tool.evaluate_a3(0)["verdict"], "PASS")
        self.assertEqual(audit_tool.evaluate_a3(1)["verdict"], "FAIL")


class StateMachineTest(unittest.TestCase):
    def test_attempts_consume_panels_in_order(self) -> None:
        machine = audit_tool.AuditStateMachine("A3")
        self.assertEqual(machine.panel_for_next_attempt(), "panel-0")
        machine.record("FAIL")
        machine.register_fix("投影器少算一格", "tools/dist_data/project_boxes.py")
        self.assertEqual(machine.panel_for_next_attempt(), "panel-1")

    def test_no_fix_no_retry(self) -> None:
        machine = audit_tool.AuditStateMachine("A3")
        machine.record("FAIL")
        with self.assertRaises(audit_tool.AuditError):
            machine.panel_for_next_attempt()

    def test_fix_registration_requires_description_and_change(self) -> None:
        machine = audit_tool.AuditStateMachine("A1")
        machine.record("FAIL")
        with self.assertRaises(audit_tool.AuditError):
            machine.register_fix("", "x")
        with self.assertRaises(audit_tool.AuditError):
            machine.register_fix("desc", "")

    def test_third_failure_exhausts_the_audit(self) -> None:
        machine = audit_tool.AuditStateMachine("A2")
        for index in range(contract.AUDIT_MAX_ATTEMPTS):
            machine.record("FAIL")
            machine.register_fix(f"fix-{index}", "change")
        with self.assertRaises(audit_tool.AuditTerminal) as caught:
            machine.panel_for_next_attempt()
        self.assertEqual(caught.exception.terminal, "AUDIT_EXHAUSTED_FAIL")

    def test_supersession_resets_attempts_and_escalates_after_two(self) -> None:
        machine = audit_tool.AuditStateMachine("A2")
        machine.note_catalog_supersession()
        self.assertEqual(machine.panel_for_next_attempt(), "panel-0")
        machine.note_catalog_supersession()
        with self.assertRaises(audit_tool.AuditTerminal) as caught:
            machine.note_catalog_supersession()
        self.assertEqual(caught.exception.terminal, "AUDIT_ESCALATE_TO_USER")

    def test_no_hidden_seed_rotation_path(self) -> None:
        """同一审计最多 9 个 panel attempt（3 × (1 + 2 次 supersession)）。"""
        self.assertEqual(audit_tool.AuditStateMachine("A1").max_panel_attempts(), 9)

    def test_passing_attempt_needs_no_fix(self) -> None:
        machine = audit_tool.AuditStateMachine("A1")
        machine.record("PASS")
        with self.assertRaises(audit_tool.AuditError):
            machine.register_fix("desc", "change")


class WorkloadTest(unittest.TestCase):
    def test_estimate_matches_the_proposal_order_of_magnitude(self) -> None:
        estimate = audit_tool.user_workload_estimate(25)
        self.assertEqual(estimate["total"], 9 + 20 + 25 + 25 + 200 + 100)
        self.assertEqual(estimate["class_map_checklist"], 9)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
