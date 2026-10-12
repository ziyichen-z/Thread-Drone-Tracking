#!/usr/bin/env python3
"""P1-ENG-ACQ-001 AC-7/AC-20：E1 十五桶互斥穷尽与守恒、AR2-2 抽样、扰动臂分位数、第二级前缀回放与
`replay_tracker` 逐事件等价（合成数据；不读数据根、不跑库）。"""

from __future__ import annotations

from collections import Counter
import itertools
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller.reanchor import BufferedFrame, replay_tracker  # noqa: E402
from controller.resident_core import RESULTS, box_iou  # noqa: E402
from controller.trackers import ScriptedTracker, TrackerResult  # noqa: E402
from tools.eng_acq import e1  # noqa: E402
from tools.eng_acq.data import Frame  # noqa: E402

A = (0.10, 0.10, 0.10, 0.10)
B = (0.50, 0.50, 0.10, 0.10)


def frame(frame_id: int, statics=(), red=None, t=None) -> Frame:
    sim_t = frame_id * 0.2 if t is None else t
    metadata = {"frame_id": frame_id, "simulation_time_s": sim_t, "camera_rotation_xyzw": [0.7071068, 0, 0, 0.7071068], "camera_position_world_m": [0, 25, 0], "intrinsics_px": {"fx": 415.69, "fy": 415.69, "cx": 320.0, "cy": 240.0}}
    return Frame("syn", "seg", frame_id, f"seg/frame_{frame_id:010d}.jpg", sim_t, metadata, (), tuple(statics), red, None)


def record(frame_id: int, library_frame_id: int, tracked=(), lost=(), removed=()):
    rows = [{"track_id": i, "box_norm": list(b), "score": 0.9, "cls": 0, "state": "tracked"} for i, b in tracked]
    rows += [{"track_id": i, "box_norm": list(b), "score": 0.8, "cls": 0, "state": "lost"} for i, b in lost]
    return {"frame_id": frame_id, "library_frame_id": library_frame_id, "tracks": rows, "removed_ids": list(removed)}


def rows_of(rec, state):
    from tools.eng_acq import e2  # noqa: PLC0415 — 需要 ultralytics 的模块不在此导入；rows_of 为纯函数副本

    return e2.rows_of(rec, state)


def pure_rows_of(rec, state):
    from controller.resident_core import TrackRow  # noqa: PLC0415

    return [TrackRow(int(t["track_id"]), tuple(t["box_norm"]), float(t["score"]), int(t["cls"]), t["state"]) for t in rec["tracks"] if t["state"] == state]


class Buckets(unittest.TestCase):
    def test_buckets_exhaustive_and_conserved(self):
        """AC-7：任意 (r 存在, 结果, 可见, IoU) 组合恰落一桶；合成层上两条守恒式成立。"""
        seen = Counter()
        for r_exists, result, visible, iou in itertools.product((True, False), RESULTS, (True, False), (0.0, 0.29, 0.3, 0.9)):
            bucket = e1.classify(r_exists, result, visible, iou)
            self.assertIn(bucket, e1.BUCKETS)
            seen[bucket] += 1
        self.assertEqual(set(seen), set(e1.BUCKETS))
        with self.assertRaises(ValueError):
            e1.classify(True, "SEVENTH", True, 1.0)
        # 合成一个序列：k 帧有静止车 A（被 track 1 跟住）与红车 B（未检测）；运行完整 run_combo + aggregate。
        frames = [frame(i, statics=(("car-a", A),), red=B if i < 40 else None) for i in range(80)]
        records = [record(i, i + 1, tracked=[(1, A)]) for i in range(80)]
        samples, _ = e1.build_samples("syn", [frames], "none")

        class Prefix:
            sot_runs = sot_frames = 0

            def result_at(self, k, box, h):
                from controller.reanchor import ReplayResult  # noqa: PLC0415

                return ReplayResult("RESEED_READY", None, k, h, h - k, 1.0, TrackerResult((0.9, 0.9, 0.05, 0.05), True, 0.9, "tracker"))

        combo = e1.run_combo("syn", [frames], [records], samples, "pose", "none", lambda i: Prefix(), pure_rows_of)
        rows = e1.aggregate("syn", "TAG", samples, combo, "pose", "none")
        self.assertEqual(len(rows), len(e1.CLASSES) * len(e1.SIZES) * len(e1.DELTAS_S))
        for row in rows:
            self.assertTrue(e1.conservation_ok(row), row)
            if row["N_all"] == 0:
                self.assertTrue(all(v is None for v in row["ratios"].values()))
        static_1s = next(r for r in rows if r["class"] == "static" and r["size"] == "L" and r["delta_s"] == 1.0)
        self.assertEqual(static_1s["buckets"]["BOUND_V_CORRECT"], static_1s["N_vis"])
        red_rows = [r for r in rows if r["class"] == "red" and r["N_all"]]
        self.assertTrue(red_rows)
        self.assertTrue(all(r["buckets"]["NOTRACK_V"] + r["buckets"]["NOTRACK_INVISIBLE"] + r["buckets"]["NO_RESOLVE_FRAME"] == r["N_all"] for r in red_rows))
        self.assertTrue(all(r["level2"]["failed_by_reason"]["no_adoption"] == r["N_res"] for r in red_rows))

    def test_ratios_null_on_zero_denominators(self):
        counts = {name: 0 for name in e1.BUCKETS}
        self.assertTrue(all(v is None for v in e1.ratios(counts, 0, 0, 0, 0).values()))

    def test_resolve_frame_same_segment_first_at_or_after(self):
        frames = [frame(i) for i in range(10)]
        self.assertEqual(e1.resolve_frame_index(frames, 0, 1.0), 5)
        self.assertIsNone(e1.resolve_frame_index(frames, 5, 2.0))


class Subsample(unittest.TestCase):
    def test_stratified_proportional_and_fixed_seed(self):
        samples = [e1.Sample(0, i, i, f"o{i}", "static" if i % 3 else "red", "S" if i % 2 else "L", A, A) for i in range(1500)]
        chosen, flagged = e1.subsample(samples)
        again, _ = e1.subsample(samples)
        self.assertTrue(flagged)
        self.assertEqual(len(chosen), 600)
        self.assertEqual(chosen, again)
        by_stratum = Counter((s.cls, s.size) for s in chosen)
        total = Counter((s.cls, s.size) for s in samples)
        for key, count in by_stratum.items():
            self.assertLessEqual(abs(count - 600 * total[key] / 1500), 1)
        small, flagged_small = e1.subsample(samples[:10])
        self.assertFalse(flagged_small)
        self.assertEqual(len(small), 10)

    def test_unsampled_are_not_bucketed(self):
        """AR2-2：触发数 > 600 时未抽中的 (k, o, Δ) 不入 15 桶、不计 NO_TRACK_AT_K，层记 NOT_EVALUABLE_AR2-2。"""
        statics = tuple((f"car-{j}", (0.01 * j, 0.5, 0.005, 0.005)) for j in range(20))
        frames = [frame(i, statics=statics) for i in range(40)]
        records = [record(i, i + 1) for i in range(40)]  # 无任何轨迹 → 全部触发第二级
        samples, _ = e1.build_samples("syn", [frames], "none")
        self.assertGreater(len(samples), 600)

        class Prefix:
            def result_at(self, k, box, h):
                from controller.reanchor import ReplayResult  # noqa: PLC0415

                return ReplayResult("RESEED_READY", None, k, h, h - k, 1.0, TrackerResult((0.9, 0.9, 0.05, 0.05), True, 0.9, "tracker"))

        combo = e1.run_combo("syn", [frames], [records], samples, "pose", "none", lambda i: Prefix(), pure_rows_of)
        self.assertEqual((combo["triggered"], combo["selected"], combo["subsampled"]), (len(samples), 600, True))
        rows = e1.aggregate("syn", "TAG", samples, combo, "pose", "none")
        affected = [r for r in rows if r["not_run"]["ar2_2"]]
        self.assertTrue(affected)
        for row in affected:
            self.assertEqual(row["status"], "NOT_EVALUABLE_AR2-2")
            self.assertEqual(row["ratios_scope"], "subsample_diagnostic_only")
            self.assertTrue(e1.conservation_ok(row))
            self.assertLess(row["buckets"]["NOTRACK_V"] + row["buckets"]["NOTRACK_INVISIBLE"], row["N_all"] - row["buckets"]["NO_RESOLVE_FRAME"])


    def test_a7_full_sample_other_sequences_capped(self):
        """AC-7 修订 2（SUB:1）：a7 第二级触发 (k, o) 全样本运行、无 `not_run_ar2_2`；其他序列仍守 600 上限。"""
        self.assertIsNone(e1.level2_cap("a7"))
        self.assertEqual(e1.level2_cap("scout-1"), 600)
        self.assertEqual(e1.level2_cap("m3-armA"), 600)
        statics = tuple((f"car-{j}", (0.01 * j, 0.5, 0.005, 0.005)) for j in range(20))
        frames = [frame(i, statics=statics) for i in range(40)]
        records = [record(i, i + 1) for i in range(40)]  # 无任何轨迹 → 全部触发第二级
        samples, _ = e1.build_samples("a7", [frames], "none")
        self.assertGreater(len(samples), 600)

        class Prefix:
            def result_at(self, k, box, h):
                from controller.reanchor import ReplayResult  # noqa: PLC0415

                return ReplayResult("RESEED_READY", None, k, h, h - k, 1.0, TrackerResult((0.9, 0.9, 0.05, 0.05), True, 0.9, "tracker"))

        full = e1.run_combo("a7", [frames], [records], samples, "pose", "none", lambda i: Prefix(), pure_rows_of)
        self.assertEqual((full["triggered"], full["selected"], full["subsampled"]), (len(samples), len(samples), False))
        rows = e1.aggregate("a7", "TAG", samples, full, "pose", "none")
        self.assertTrue(all(r["not_run"]["ar2_2"] == 0 and r["status"] == "EVALUATED" and e1.conservation_ok(r) for r in rows))
        capped = e1.run_combo("scout-1", [frames], [records], samples, "pose", "none", lambda i: Prefix(), pure_rows_of)
        self.assertEqual((capped["selected"], capped["subsampled"]), (600, True))


class Perturbation(unittest.TestCase):
    def test_c2_quantiles_within_tolerance_and_deterministic(self):
        boxes = [(0.05 + (i % 17) * 0.05, 0.05 + (i % 13) * 0.06, 0.03 + (i % 5) * 0.02, 0.03 + (i % 7) * 0.015) for i in range(3000)]
        realized = [box_iou(e1.perturb_box(b, f"key-{i}"), b) for i, b in enumerate(boxes)]
        achieved = e1.realized_quantiles(realized)
        for key, value in e1.C2_QUANTILES.items():
            self.assertLessEqual(abs(achieved[key] - value), e1.QUANTILE_TOLERANCE, (key, achieved))
        self.assertEqual(e1.perturb_box(boxes[3], "key-3"), e1.perturb_box(boxes[3], "key-3"))
        for i, b in enumerate(boxes[:200]):
            out = e1.perturb_box(b, f"key-{i}")
            self.assertTrue(0.0 <= out[0] and 0.0 <= out[1] and out[0] + out[2] <= 1.0 + 1e-12 and out[1] + out[3] <= 1.0 + 1e-12)

    def test_uniform_arm_not_executed(self):
        with self.assertRaises(ValueError):
            e1.build_samples("syn", [[frame(0, statics=(("a", A),))]], "uniform")


class _Window:
    def __init__(self, frames):
        self.frames = {f.frame_id: f for f in frames}

    def get(self, frame_id):
        f = self.frames.get(frame_id)
        return None if f is None else BufferedFrame(frame_id, f.sim_t, f"img-{frame_id}", f.metadata, None)

    def after_through(self, a, b):
        for frame_id in range(a + 1, b + 1):
            item = self.get(frame_id)
            if item is None:
                raise FileNotFoundError(frame_id)
            yield item


class PrefixEquivalence(unittest.TestCase):
    """前缀共享回放对每个 h 给出与 `replay_tracker(k→h)` 相同的事件、原因、帧数与末框。"""

    def check(self, script, *, init_ok=True, box=A, seconds_per_update=None, raise_at=None, frames=None):
        """时钟按「已执行的 SOT 更新次数 × 每次耗时」推进，两种实现对同一工作量看到同一耗时。"""
        frames = frames or [frame(i) for i in range(12)]
        work = {"updates": 0}

        def factory():
            tracker = ScriptedTracker(list(script), init_ok=init_ok)
            original = tracker.update

            def update(image):
                work["updates"] += 1
                if raise_at is not None and work["updates"] == raise_at:
                    raise KeyError("boom")
                return original(image)

            tracker.update = update  # type: ignore[method-assign]
            return tracker

        def clock():
            return 0.0 if seconds_per_update is None else seconds_per_update * work["updates"]

        prefix = e1.PrefixSot(frames, factory, lambda f: f"img-{f.frame_id}", t_replay_s=2.0, maximum_source_age_s=25.6, monotonic=clock)
        window = _Window(frames)
        got_all = {h: prefix.result_at(2, box, h) for h in range(3, 11)}
        for h in range(3, 11):
            work["updates"] = 0  # 每次独立回放从零工作量起算（replay_tracker 在建 SOT 前取起始时刻）
            expected = replay_tracker(factory, window, source_frame_id=2, source_box_norm=list(box), target_head_frame_id=h, maximum_source_age_s=25.6, catchup_timeout_s=2.0, monotonic=clock)
            got = got_all[h]
            self.assertEqual((got.event, got.reason, got.head_frame_id, got.replay_count), (expected.event, expected.reason, expected.head_frame_id, expected.replay_count), h)
            self.assertEqual(got.last_result, expected.last_result, h)
        self.assertLessEqual(prefix.sot_runs, 1)
        return got_all

    def test_success(self):
        self.check([TrackerResult(B, True, 0.9, "tracker")] * 20)

    def test_sot_lost_midway(self):
        self.check([TrackerResult(B, True, 0.9, "tracker")] * 3 + [TrackerResult.lost("tracker_reported_failure")] + [TrackerResult(B, True, 0.9, "tracker")] * 9)

    def test_out_of_frame_box(self):
        self.check([TrackerResult(B, True, 0.9, "tracker"), TrackerResult((0.95, 0.5, 0.1, 0.1), True, 0.9, "tracker")] + [TrackerResult(B, True, 0.9, "tracker")] * 9)

    def test_init_failure_and_invalid_source(self):
        self.check([], init_ok=False)
        self.check([TrackerResult(B, True, 0.9, "tracker")] * 12, box=(0.95, 0.95, 0.1, 0.1))

    def test_non_init_exception(self):
        self.check([TrackerResult(B, True, 0.9, "tracker")] * 12, raise_at=3)

    def test_timeout(self):
        results = self.check([TrackerResult(B, True, 0.9, "tracker")] * 12, seconds_per_update=0.45)
        self.assertEqual((results[10].event, results[10].head_frame_id), ("RESEED_DISCARDED_NOT_CONVERGED", 7))

    def test_frame_cap(self):
        frames = [frame(i) for i in range(80)]
        prefix = e1.PrefixSot(frames, lambda: ScriptedTracker([TrackerResult(B, True, 0.9, "tracker")] * 80), lambda f: None, t_replay_s=2.0, maximum_source_age_s=25.6)
        # 信封修订 SUB:2（2026-09-29）：每 (k, o) ≤ 66 帧（原 65）；SUB:3 起为 a7、m3-armA 的值（缺省）。
        self.assertEqual(e1.FRAME_CAP, 66)
        self.assertEqual(prefix.result_at(0, A, 66).replay_count, 66)
        with self.assertRaises(e1.FrameCapExceeded):
            prefix.result_at(0, A, 67)
        self.assertTrue(all(run.frames_computed <= e1.FRAME_CAP for run in prefix.cache.values()))

    def test_frame_cap_by_sequence(self):
        """AC-7/AC-20 修订 3（SUB:3）：scout-1 每 (k, o) ≤ 87 帧，a7、m3-armA 仍 ≤ 66；前缀不越过所在序列的上限。"""
        self.assertEqual(e1.frame_cap("scout-1"), 87)
        self.assertEqual(e1.frame_cap("a7"), 66)
        self.assertEqual(e1.frame_cap("m3-armA"), 66)
        frames = [frame(i, t=i * 0.15) for i in range(100)]
        prefix = e1.PrefixSot(frames, lambda: ScriptedTracker([TrackerResult(B, True, 0.9, "tracker")] * 100), lambda f: None, t_replay_s=2.0, maximum_source_age_s=25.6, frame_cap=e1.frame_cap("scout-1"))
        self.assertEqual(prefix.result_at(0, A, 87).replay_count, 87)
        with self.assertRaises(e1.FrameCapExceeded):
            prefix.result_at(0, A, 88)
        self.assertTrue(all(run.frames_computed <= 87 for run in prefix.cache.values()))
        self.assertEqual(max(run.frames_computed for run in prefix.cache.values()), 87)


class FrameCapBySequence(unittest.TestCase):
    def test_scout1_delta13_runs_under_87_others_capped_at_66(self):
        """SUB:3：帧间隔 0.15 s 时 Δ13 需 87 帧——序列名 scout-1 全部运行、层 EVALUATED；a7/m3-armA 同数据仍记 frame_cap 未运行。"""
        frames = [frame(i, statics=(("car-a", A),), t=i * 0.15) for i in range(100)]
        records = [record(i, i + 1) for i in range(100)]  # 无轨迹 → 全部触发第二级

        class Prefix:
            def __init__(self):
                self.max_gap = 0

            def result_at(self, k, box, h):
                from controller.reanchor import ReplayResult  # noqa: PLC0415

                self.max_gap = max(self.max_gap, h - k)
                return ReplayResult("RESEED_READY", None, k, h, h - k, 1.0, TrackerResult((0.9, 0.9, 0.05, 0.05), True, 0.9, "tracker"))

        for sequence, expect_capped in (("scout-1", False), ("m3-armA", True), ("a7", True)):
            samples, _ = e1.build_samples(sequence, [frames], "none")
            fake = Prefix()
            combo = e1.run_combo(sequence, [frames], [records], samples, "pose", "none", lambda i, _f=fake: _f, pure_rows_of)
            capped = sum(1 for v in combo["outcomes"].values() if v.get("not_run") == "frame_cap")
            rows = e1.aggregate(sequence, "TAG", samples, combo, "pose", "none")
            self.assertTrue(all(e1.conservation_ok(r) for r in rows))
            delta13 = [r for r in rows if r["delta_s"] == 13.0 and r["N_all"]]
            self.assertTrue(delta13)
            if expect_capped:
                self.assertGreater(capped, 0, sequence)
                self.assertLessEqual(fake.max_gap, 66, sequence)
                self.assertTrue(all(r["status"] == "NOT_EVALUABLE_FRAME_CAP" for r in delta13), sequence)
            else:
                self.assertEqual(capped, 0, sequence)
                self.assertEqual(fake.max_gap, 87, sequence)
                self.assertTrue(all(r["status"] == "EVALUATED" for r in rows), sequence)


if __name__ == "__main__":
    unittest.main()
