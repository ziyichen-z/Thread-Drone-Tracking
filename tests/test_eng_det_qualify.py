#!/usr/bin/env python3
"""P1-ENG-FAST-002 AC-3 / AC-4 / AC-13：§3.1.3 匹配与 FP 反例、门判定与 `N_min`、子序列切分、
口径 B 判定、冻结守卫（全部纯函数或临时文件，不读数据根、不跑模型）。"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_det import common, evaluate, plugin_replay  # noqa: E402
from tools.eng_det import qualify  # noqa: E402
from tools.eng_det import select as sel  # noqa: E402
from tools.eng_det.ledger import Ledger  # noqa: E402
from tools.eng_fast import replay as fast_replay  # noqa: E402

BOX = [0.4, 0.4, 0.1, 0.1]


def det(box, score=0.9, cls=0.0):
    return [*box, score, cls]


def positive(box, cls=0, side=40.0):
    return {"cls": cls, "box": box, "side_px": side, "depth_m": 40.0, "status": "OK" if cls == 0 else "-"}


def row(frame_id, positives=(), ignores=(), excluded=False, family="fam"):
    return {
        "frame_id": frame_id,
        "family": family,
        "excluded": excluded,
        "positives": list(positives),
        "ignores": [{"box": b, "why": w} for b, w in ignores],
    }


class FpCounterexamples(unittest.TestCase):
    """§3.1.3 五条 FP 反例 + conf 过滤。"""

    def test_detection_on_ignore_box_is_not_fp(self):
        result = evaluate.match_frame([det(BOX)], [], [BOX], 0.5, 0.25)
        self.assertEqual((result["tp"], result["fp"], result["discarded"]), (0, 0, 1))

    def test_two_detections_on_one_positive_is_one_tp_one_fp(self):
        result = evaluate.match_frame([det(BOX, 0.9), det(BOX, 0.8)], [BOX], [], 0.5, 0.25)
        self.assertEqual((result["tp"], result["fp"], result["hits"]), (1, 1, [True]))

    def test_excluded_frame_not_in_denominator_nor_fp(self):
        rows = [row("a", [positive(BOX)]), row("b", excluded=True)]
        dets = {"a": [det(BOX)], "b": [det([0.1, 0.1, 0.1, 0.1])] * 5}
        result = evaluate.evaluate(rows, dets, 0.25)
        self.assertEqual((result["frames"], result["fp_050"], len(result["outcomes"])), (1, 0, 1))

    def test_stratum_ignored_object_is_ignore_in_evaluation(self):
        rows = [row("a", [], [(BOX, "iii_stratum")])]
        result = evaluate.evaluate(rows, {"a": [det(BOX)]}, 0.25)
        self.assertEqual((result["fp_050"], result["discarded_by_ignore_050"], result["outcomes"]), (0, 1, []))

    def test_11px_object_is_ignore_not_positive(self):
        small = [0.4, 0.4, 11 / 640, 11 / 480]
        rows = [row("a", [], [(small, "i_small")])]
        result = evaluate.evaluate(rows, {"a": [det(small)]}, 0.25)
        self.assertEqual((result["fp_050"], len(result["outcomes"])), (0, 0))

    def test_truth_invisible_target_ignore_q2(self):
        rows = [row("a", [], [(BOX, "iv_truth_invisible")])]
        result = evaluate.evaluate(rows, {"a": [det(BOX, cls=1.0)]}, 0.25)
        self.assertEqual((result["fp_050"], result["discarded_by_ignore_050"]), (0, 1))

    def test_ioa_threshold_and_conf_filter(self):
        partly = [0.4, 0.4, 0.15, 0.1]  # 与 ignore 框 BOX 的 IoA = 2/3 ≥ 0.5
        self.assertEqual(evaluate.match_frame([det(partly)], [], [BOX], 0.5, 0.25)["discarded"], 1)
        mostly_outside = [0.45, 0.4, 0.2, 0.1]
        self.assertEqual(evaluate.match_frame([det(mostly_outside)], [], [BOX], 0.5, 0.25)["fp"], 1)
        self.assertEqual(evaluate.match_frame([det(BOX, 0.3)], [BOX], [], 0.5, 0.40)["hits"], [False])

    def test_class_agnostic_greedy_by_score(self):
        near = [0.405, 0.4, 0.1, 0.1]
        result = evaluate.match_frame([det(near, 0.5), det(BOX, 0.95, 1.0)], [BOX, near], [], 0.5, 0.25)
        self.assertEqual((result["tp"], result["fp"]), (2, 0))


class GateTests(unittest.TestCase):
    def test_recall_cell_below_n_min_is_not_met(self):
        c = evaluate.cell([{"hit_030": True, "hit_050": True}] * 49)
        self.assertEqual(evaluate.recall_cell_verdict(c, 0.9)["verdict"], "N/A(INSUFFICIENT_N=49)")
        self.assertEqual(evaluate.recall_cell_verdict(evaluate.cell([{"hit_030": True, "hit_050": True}] * 50), 0.9)["verdict"], evaluate.MET)

    def test_gate_three_states(self):
        met = {"verdict": evaluate.MET}
        fail = {"verdict": evaluate.GATE_NOT_MET}
        na = {"verdict": "N/A(INSUFFICIENT_N=3)"}
        self.assertEqual(evaluate.gate({"a": met, "b": met})["verdict"], evaluate.MET)
        self.assertEqual(evaluate.gate({"a": met, "b": na, "c": fail})["verdict"], evaluate.GATE_NOT_MET)
        self.assertEqual(evaluate.gate({"a": met, "b": na})["verdict"], "NOT_EVALUABLE(b)")

    def test_fp_needs_300_frames(self):
        self.assertTrue(evaluate.fp_verdict({"frames": 299, "fp_per_frame_050": 0.0})["verdict"].startswith("N/A"))
        self.assertEqual(evaluate.fp_verdict({"frames": 300, "fp_per_frame_050": 0.51})["verdict"], evaluate.GATE_NOT_MET)

    def test_retention_no_segment_and_insufficient(self):
        self.assertEqual(evaluate.retention_verdict(None, 0.9)["verdict"], "N/A(NO_SEGMENT)")
        self.assertEqual(evaluate.retention_verdict({"D": 29, "retention": 1.0}, 0.9)["verdict"], "N/A(INSUFFICIENT_N=29)")
        self.assertEqual(evaluate.retention_verdict({"D": 30, "retention": 0.9}, 0.9)["verdict"], evaluate.MET)

    def test_detection_gates_use_single_conf_table(self):
        full = {"hit_030": True, "hit_050": True}
        table = evaluate.recall_table(
            [{"cls": c, "stratum": s, "axis": "axial", "distance_bin": "NA", **full} for c in common.CLASS_NAMES for s in common.STRATA for _ in range(50)],
            "H",
        )
        result = evaluate.detection_gates(table, {"frames": 300, "fp_per_frame_050": 0.1}, "G")
        self.assertEqual({k: v["verdict"] for k, v in result.items()}, {"G-1": "MET", "G-1s": "MET", "G-2": "MET", "G-3": "MET"})


def seq_row(i, t, visible=True, excluded=False):
    return {"frame_id": f"f{i:04d}", "sim_t": t, "excluded": excluded, "family": "fam", "session": "s", "positives": [positive(BOX, 1)] if visible else [], "ignores": []}


class SequenceTests(unittest.TestCase):
    def test_split_on_gap_over_2s_and_drop_short(self):
        rows = [seq_row(i, i * 0.2) for i in range(200)] + [seq_row(1000 + i, 100 + i * 0.2) for i in range(20)]
        kept, info = evaluate.split_subsequences(rows, 30)
        self.assertEqual((info["pieces"], info["kept"], info["dropped"]), (2, 1, 1))
        for piece in kept:
            times = [r["sim_t"] for r in piece]
            self.assertLessEqual(max(b - a for a, b in zip(times, times[1:])), evaluate.MAX_GAP_S)
            fast_replay.check_timestamps(times)
        kept60, _ = evaluate.split_subsequences(rows[:100], 60)  # 19.8 s < 13 s + 60 × 0.2 s
        self.assertEqual(kept60, [])

    def test_target_truth_excluded_or_absent_is_none(self):
        self.assertIsNone(evaluate.target_truth(seq_row(0, 0.0, excluded=True)))
        self.assertIsNone(evaluate.target_truth(seq_row(0, 0.0, visible=False)))
        self.assertEqual(evaluate.target_truth(seq_row(0, 0.0)), BOX)

    def test_pool_windows_skips_pieces_without_judged_windows(self):
        piece = lambda kept, d: {"windows": {"13s": {**{k: 0 for k in fast_replay.OUTCOMES}, "KEPT": kept, "ID_SWITCH": d - kept, "V": d, "D": d}}}  # noqa: E731
        pooled = evaluate.pool_windows([piece(8, 10), piece(0, 0), piece(20, 20)], "13s")
        self.assertEqual((pooled["D"], pooled["KEPT"], pooled["pieces_with_D"], pooled["retention"]), (30, 28, 2, round(28 / 30, 6)))
        self.assertIsNone(evaluate.pool_windows([piece(0, 0)], "13s"))


class CaliberBTests(unittest.TestCase):
    def test_score_frame_closed_set(self):
        self.assertEqual(plugin_replay.score_frame(True, BOX, BOX), plugin_replay.HIT)
        self.assertEqual(plugin_replay.score_frame(True, [0.45, 0.4, 0.1, 0.1], BOX), plugin_replay.DRIFT)
        self.assertEqual(plugin_replay.score_frame(False, None, BOX), plugin_replay.MISS)
        self.assertEqual(plugin_replay.score_frame(True, BOX, None), plugin_replay.NOT_SCORED)

    def test_run_piece_inits_on_first_visible_and_never_rebinds(self):
        from controller.trackers import TrackerResult  # noqa: PLC0415

        class Fake:
            library_frame_id = 0
            bound_track_id = 7

            def __init__(self):
                self.inits = []
                self.script = [TrackerResult(tuple(BOX), True, 0.9, "tracker"), TrackerResult.lost("bound_track_unmatched"), TrackerResult.lost("bound_track_removed"), TrackerResult(tuple([0.45, 0.4, 0.1, 0.1]), True, 0.8, "tracker")]

            def init(self, image, box):
                self.inits.append(box)
                self.library_frame_id = 1
                return True

            def update(self, image):
                self.library_frame_id += 1
                return self.script.pop(0)

        piece = [seq_row(i, i * 0.2, visible=i != 0) for i in range(6)]
        truths = [evaluate.target_truth(r) for r in piece]
        fake = Fake()
        record = plugin_replay.run_piece(fake, piece, truths, lambda fid: None)
        self.assertEqual((record["init_index"], len(fake.inits), record["library_frame_id_after_init"]), (1, 1, 1))
        self.assertEqual(record["counts"], {"HIT": 1, "MISS": 2, "DRIFT": 1})
        self.assertEqual(record["first_bound_track_removed_s"], 0.6)  # 初始化 t=0.2，首次 removed 在 t=0.8
        self.assertEqual([f["state"] for f in record["per_frame"]], ["TRACKING", "LOST", "LOST", "TRACKING"])


class FreezeGuard(unittest.TestCase):
    """AC-13：无冻结 → 拒绝；sha 不符 → 拒绝；第 2 次 H 评估 → 拒绝；冻结后仍有 run → 拒绝。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.weights = tmp / "last.pt"
        self.weights.write_bytes(b"w")
        self.freeze = tmp / "freeze.json"
        self.spec = tmp / "spec.json"
        self.train = tmp / "train.json"
        self.ledger = Ledger(path=tmp / "ledger.json")
        spec = {"tracker": "det-assoc-v1", "weights": {"path": str(self.weights), "sha256": common.sha256_file(self.weights)}}
        frozen = {
            "frozen_at": "2026-09-28T10:00:00Z",
            "weights": {"path": str(self.weights), "sha256": common.sha256_file(self.weights)},
            "spec_core_sha256": sel.spec_core_sha256(spec),
        }
        self.freeze.write_text(json.dumps(frozen), encoding="utf-8")
        spec["freeze"] = {"sha256": common.sha256_file(self.freeze)}
        self.spec.write_text(json.dumps(spec), encoding="utf-8")
        self.train.write_text(json.dumps({"runs": [{"run_id": "run-1", "ended_at": "2026-09-28T09:00:00Z"}]}), encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def guard(self, **overrides):
        kwargs = {"freeze_path": self.freeze, "spec_path": self.spec, "train_path": self.train, "ledger": self.ledger}
        kwargs.update(overrides)
        return qualify.FreezeGuard(**kwargs)

    def test_clean_freeze_verifies(self):
        self.assertIn("frozen", self.guard().verify())

    def test_missing_freeze_refused(self):
        with self.assertRaises(qualify.FreezeGuardRefused):
            self.guard(freeze_path=self.freeze.with_name("absent.json")).verify()

    def test_weights_sha_mismatch_refused(self):
        self.weights.write_bytes(b"x")
        with self.assertRaises(qualify.FreezeGuardRefused):
            self.guard().verify()

    def test_freeze_edited_after_spec_refused(self):
        self.freeze.write_text(self.freeze.read_text(encoding="utf-8").replace("10:00", "11:00"), encoding="utf-8")
        with self.assertRaises(qualify.FreezeGuardRefused):
            self.guard().verify()

    def test_run_after_freeze_refused(self):
        self.train.write_text(json.dumps({"runs": [{"run_id": "run-2", "ended_at": "2026-09-28T12:00:00Z"}]}), encoding="utf-8")
        with self.assertRaises(qualify.FreezeGuardRefused):
            self.guard().verify()

    def test_second_h_evaluation_refused(self):
        guard = self.guard()
        guard.charge_h()
        self.assertEqual(self.ledger.used("h_evaluation"), 1)
        with self.assertRaises(qualify.FreezeGuardRefused):
            guard.charge_h()


if __name__ == "__main__":
    unittest.main()
