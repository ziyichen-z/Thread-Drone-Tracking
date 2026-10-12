#!/usr/bin/env python3
"""P1-ENG-FAST-002 AC-2：选择函数只接受 V 读数（H 输入 → 拒绝）与 §3.2 选择规则的具名反例（纯函数）。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_det import evaluate  # noqa: E402
from tools.eng_det import select as sel  # noqa: E402


def fp_result(domain, fp):
    return {"domain": domain, "fp_per_frame_050": fp}


def gates(passed):
    keys = ("V-1", "V-1s", "V-2", "V-3")
    return {k: {"verdict": evaluate.MET if i < passed else evaluate.GATE_NOT_MET} for i, k in enumerate(keys)}


def candidate(run_id, passed, s_rate, domain="V"):
    return {
        "run_id": run_id,
        "domain": domain,
        "v_gates": gates(passed),
        "table": {"classes": {"target": {"by_stratum": {"S": {"rate_050": s_rate}}}}},
    }


def assoc(algorithm, match, buffer, retention, domain="V"):
    return {
        "domain": domain,
        "algorithm": algorithm,
        "match_thresh": match,
        "track_buffer": buffer,
        "pooled_13s": {"retention": retention} if retention is not None else None,
    }


class OnlyVTests(unittest.TestCase):
    def test_conf_choice_rejects_h_table(self):
        with self.assertRaises(sel.SelectionRefused):
            sel.choose_conf({0.25: fp_result("H", 0.1), 0.40: fp_result("V", 0.1)})

    def test_run_choice_rejects_h_table(self):
        with self.assertRaises(sel.SelectionRefused):
            sel.choose_run([candidate("run-1", 4, 0.8), candidate("run-2", 4, 0.9, domain="H")])

    def test_association_choice_rejects_h_table(self):
        with self.assertRaises(sel.SelectionRefused):
            sel.choose_association([assoc("bytetrack", 0.8, 30, 0.9, domain="H")])

    def test_run2_decision_rejects_h_table(self):
        with self.assertRaises(sel.SelectionRefused):
            sel.needs_run2(candidate("run-1", 4, 0.8, domain="H"))


class RuleTests(unittest.TestCase):
    def test_conf_smallest_meeting_fp_else_floor_flag(self):
        self.assertEqual(sel.choose_conf({0.25: fp_result("V", 0.5), 0.40: fp_result("V", 0.2)})["conf"], 0.25)
        self.assertEqual(sel.choose_conf({0.25: fp_result("V", 0.6), 0.40: fp_result("V", 0.3)})["conf"], 0.40)
        floor = sel.choose_conf({0.25: fp_result("V", 0.9), 0.40: fp_result("V", 0.7)})
        self.assertEqual((floor["conf"], floor["flag"]), (0.40, "CONF_FLOOR_NOT_MET"))

    def test_conf_candidates_are_fixed(self):
        with self.assertRaises(sel.SelectionRefused):
            sel.choose_conf({0.25: fp_result("V", 0.1), 0.30: fp_result("V", 0.1)})

    def test_run2_needed_when_any_v_gate_not_met(self):
        self.assertFalse(sel.needs_run2(candidate("run-1", 4, 0.8)))
        self.assertTrue(sel.needs_run2(candidate("run-1", 3, 0.8)))
        not_evaluable = candidate("run-1", 4, 0.8)
        not_evaluable["v_gates"]["V-1s"]["verdict"] = "NOT_EVALUABLE(target|S)"
        self.assertTrue(sel.needs_run2(not_evaluable))

    def test_run_choice_gates_then_s_rate_then_run1(self):
        self.assertEqual(sel.choose_run([candidate("run-1", 3, 0.9), candidate("run-2", 4, 0.1)]), "run-2")
        self.assertEqual(sel.choose_run([candidate("run-1", 3, 0.5), candidate("run-2", 3, 0.6)]), "run-2")
        self.assertEqual(sel.choose_run([candidate("run-2", 3, 0.6), candidate("run-1", 3, 0.6)]), "run-1")

    def test_association_tie_breaks(self):
        grid = [assoc(a, m, b, 0.8) for a, m, b in sel.ASSOC_GRID]
        chosen = sel.choose_association(grid)
        self.assertEqual((chosen["algorithm"], chosen["track_buffer"], chosen["match_thresh"]), ("bytetrack", 30, 0.8))
        grid[-1]["pooled_13s"]["retention"] = 0.81
        chosen = sel.choose_association(grid)
        self.assertEqual((chosen["algorithm"], chosen["match_thresh"], chosen["track_buffer"]), sel.ASSOC_GRID[-1])
        self.assertEqual(len(sel.ASSOC_GRID), 8)

    def test_spec_core_sha_ignores_freeze_block_only(self):
        spec = {"tracker": "det-assoc-v1", "conf": 0.25}
        base = sel.spec_core_sha256(spec)
        self.assertEqual(base, sel.spec_core_sha256({**spec, "freeze": {"sha256": "0" * 64}}))
        self.assertNotEqual(base, sel.spec_core_sha256({**spec, "conf": 0.40}))


if __name__ == "__main__":
    unittest.main()
