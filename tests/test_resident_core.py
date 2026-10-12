#!/usr/bin/env python3
"""P1-ENG-ACQ-001 AC-2/AC-3/AC-19：`ResidentCore` 历史、六值闭集与第二级 k 帧起跟回放（纯 Python）。

SOT 用 `ScriptedTracker` 替身、帧源用内存仓库替身、`monotonic` 可注入；不需要 ultralytics/cv2。
"""

from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import resident_core as rc  # noqa: E402
from controller.trackers import ScriptedTracker, TrackerResult  # noqa: E402

A = (0.10, 0.10, 0.10, 0.10)
B = (0.50, 0.50, 0.10, 0.10)
C = (0.52, 0.50, 0.10, 0.10)  # 与 B 高度重叠


def meta(frame_id: int) -> dict:
    return {
        "frame_id": frame_id,
        "simulation_time_s": frame_id * 0.2,
        "capture_monotonic_s": 100.0 + frame_id * 0.2,
        "camera_position_world_m": [0.0, 25.0, 0.0],
        "camera_rotation_xyzw": [0.7071068, 0.0, 0.0, 0.7071068],
        "intrinsics_px": {"fx": 415.69, "fy": 415.69, "cx": 320.0, "cy": 240.0},
    }


def tracked(track_id: int, box, score: float = 0.9) -> rc.TrackRow:
    return rc.TrackRow(track_id, tuple(box), score, 0, rc.TRACKED)


def lost(track_id: int, box) -> rc.TrackRow:
    return rc.TrackRow(track_id, tuple(box), 0.8, 0, rc.LOST)


class Bundle:
    def __init__(self, frame_id: int):
        self.frame_id = frame_id
        self.image = f"image-{frame_id}"
        self.metadata = meta(frame_id)


class MemoryRepository:
    """帧源替身：`load(frame_id)` 与 `FrameRepository` 同形；缺帧抛 `FileNotFoundError`。"""

    def __init__(self, frame_ids):
        self.frame_ids = set(frame_ids)
        self.loads: list[int] = []

    def load(self, frame_id: int) -> Bundle:
        self.loads.append(frame_id)
        if frame_id not in self.frame_ids:
            raise FileNotFoundError(frame_id)
        return Bundle(frame_id)


class SotFactory:
    def __init__(self, results, init_ok=True, raise_on_update=None):
        self.results = list(results)
        self.init_ok = init_ok
        self.raise_on_update = raise_on_update
        self.calls = 0
        self.instances: list = []

    def __call__(self):
        self.calls += 1
        tracker = ScriptedTracker(list(self.results), init_ok=self.init_ok)
        if self.raise_on_update is not None:
            error = self.raise_on_update

            def update(_image):
                raise error

            tracker.update = update  # type: ignore[method-assign]
        self.instances.append(tracker)
        return tracker


def ok(box) -> TrackerResult:
    return TrackerResult(tuple(box), True, 0.9, "tracker")


def core_with(frames, depth=100, **config) -> rc.ResidentCore:
    """frames: [(frame_id, tracked_rows, lost_rows, removed_ids)]"""
    core = rc.ResidentCore(depth, rc.ResolverConfig(l_replay_frames=depth, **config))
    for index, (frame_id, t_rows, l_rows, removed) in enumerate(frames, start=1):
        core.record(frame_id, meta(frame_id), t_rows, l_rows, removed, index)
    return core


def runner_for(core, repository, factory, clock=None):
    kwargs = {"monotonic": clock} if clock is not None else {}
    return rc.repository_level2_runner(
        repository, factory, core.config, maximum_source_age_s=core.history_depth / 5.0, **kwargs
    )


class Closure(unittest.TestCase):
    def test_designate_result_closed_set(self):
        self.assertEqual(
            rc.RESULTS,
            ("BOUND", "BOUND_COASTING", "TRACK_ENDED", "NO_TRACK_AT_K", "AMBIGUOUS", "FRAME_NOT_IN_HISTORY"),
        )
        for reason in (*rc.LEVEL2_FIXED_REASONS, "sot_lost@12", "replay_timeout@7"):
            self.assertTrue(rc.is_level2_reason(reason), reason)
        for reason in ("sot_lost@", "sot_lost@x", "timeout", "not_attempted", None):
            self.assertFalse(rc.is_level2_reason(reason), reason)

    def test_module_imports_no_truth_or_tools(self):
        tree = ast.parse(Path(rc.__file__).read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(("." * node.level) + (node.module or ""))
        self.assertTrue(names <= {"__future__", "collections", "dataclasses", "math", "typing", ".reanchor", ".trackers"}, names)


class History(unittest.TestCase):
    def test_keyed_by_sensor_frame_id_and_rollback_rejected(self):
        core = core_with([(1000, [tracked(1, A)], [], []), (1001, [tracked(1, A)], [], [])])
        self.assertIsNotNone(core.history(1000))
        self.assertIsNone(core.history(1))
        self.assertEqual(core.history(1001).library_frame_id, 2)
        for bad in (1001, 999):
            with self.assertRaises(rc.ProtocolMisuse):
                core.record(bad, meta(bad), [], [], [], 3)

    def test_depth_eviction_and_minimum(self):
        core = core_with([(i, [], [], []) for i in range(105)], depth=100)
        self.assertEqual(len(core), 100)
        self.assertIsNone(core.history(4))
        self.assertIsNotNone(core.history(5))
        with self.assertRaises(ValueError):
            rc.ResidentCore(99)

    def test_entry_carries_pose_and_all_rows(self):
        core = core_with([(7, [tracked(1, A)], [lost(2, B)], [3])])
        entry = core.history(7)
        self.assertEqual(entry.camera_rotation_xyzw, (0.7071068, 0.0, 0.0, 0.7071068))
        self.assertEqual([r.state for r in entry.tracks], ["tracked", "lost"])
        self.assertEqual(entry.removed_ids, (3,))


class LevelOne(unittest.TestCase):
    """AC-3：第一级六值与 τ/m/备用判据边界、coasting 超时。"""

    def test_bound(self):
        core = core_with([(1, [tracked(5, A)], [], []), (2, [tracked(5, A)], [], [])])
        d = core.designate(A, 1, None)
        self.assertEqual((d.result, d.track_id, d.resolution_level, core.pointer()), ("BOUND", 5, 1, 5))

    def test_tau_boundary(self):
        # 指定框与轨迹框 IoU 恰为 0.5（宽度一半重叠：交 0.005 / 并 0.01 → 0.5）。
        half = (0.10, 0.10, 0.10, 0.05)
        core = core_with([(1, [tracked(5, (0.10, 0.10, 0.10, 0.10))], [], []), (2, [tracked(5, A)], [], [])])
        self.assertAlmostEqual(rc.box_iou(half, A), 0.5)
        self.assertEqual(core.designate(half, 1, None).result, "BOUND")
        smaller = (0.10, 0.10, 0.10, 0.049)
        self.assertLess(rc.box_iou(smaller, A), 0.5)
        # 中心不在框内时低于 τ 且无备用 → 走第二级（无跑者即协议误用）
        with self.assertRaises(rc.ProtocolMisuse):
            core.designate((0.10, 0.02, 0.10, 0.09), 1, None)

    def test_margin_boundary_and_ambiguous(self):
        box = (0.50, 0.50, 0.10, 0.10)
        high = (0.50, 0.50, 0.10, 0.10)  # IoU 1.0
        mid = (0.50, 0.50, 0.10, 0.079)  # IoU 0.79 → 裕度 0.21（≥ m）
        near = (0.50, 0.50, 0.10, 0.081)  # IoU 0.81 → 裕度 0.19（< m）
        core = core_with([(1, [tracked(1, high), tracked(2, mid)], [], []), (2, [tracked(1, high), tracked(2, mid)], [], [])])
        self.assertEqual(core.designate(box, 1, None).result, "BOUND")
        core = core_with([(1, [tracked(1, high), tracked(2, near)], [], []), (2, [tracked(1, high)], [], [])])
        d = core.designate(box, 1, None)
        self.assertEqual((d.result, d.candidates, core.pointer()), ("AMBIGUOUS", (1, 2), None))

    def test_backup_center_inside_unique(self):
        big = (0.0, 0.0, 0.5, 0.5)
        small = (0.2, 0.2, 0.02, 0.02)  # IoU 远低于 τ，中心在指定框内
        core = core_with([(1, [tracked(9, small)], [], []), (2, [tracked(9, small)], [], [])])
        d = core.designate(big, 1, None)
        self.assertEqual((d.result, d.track_id, d.level1["criterion"]), ("BOUND", 9, "center_inside"))

    def test_backup_two_centers_goes_to_level_two(self):
        big = (0.0, 0.0, 0.5, 0.5)
        rows = [tracked(9, (0.2, 0.2, 0.02, 0.02)), tracked(10, (0.3, 0.3, 0.02, 0.02))]
        repo = MemoryRepository(range(1, 3))
        factory = SotFactory([ok((0.9, 0.9, 0.05, 0.05))])
        core = core_with([(1, rows, [], []), (2, rows, [], [])])
        d = core.designate(big, 1, runner_for(core, repo, factory))
        self.assertEqual((d.result, d.level2["reason"]), ("NO_TRACK_AT_K", "no_adoption"))

    def test_bound_coasting_then_recovered(self):
        core = core_with([(1, [tracked(5, A)], [], []), (2, [], [lost(5, A)], [])])
        d = core.designate(A, 1, None)
        self.assertEqual((d.result, core.pointer()), ("BOUND_COASTING", 5))
        self.assertEqual(core.pointer_result(2).reason, "bound_track_unmatched")
        core.record(3, meta(3), [tracked(5, A)], [], [], 3)
        self.assertTrue(core.pointer_result(3).ok)
        self.assertIn("COASTING_RECOVERED", [e["event"] for e in core.drain_events()])

    def test_coasting_removed_turns_track_ended(self):
        core = core_with([(1, [tracked(5, A)], [], []), (2, [], [lost(5, A)], [])])
        core.designate(A, 1, None)
        core.drain_events()
        core.record(3, meta(3), [], [], [5], 3)
        events = core.drain_events()
        self.assertEqual([(e["event"], e["cause"]) for e in events], [("COASTING_TO_TRACK_ENDED", "removed")])
        self.assertEqual(core.pointer_result(3).reason, "bound_track_removed")

    def test_coasting_limit_turns_track_ended(self):
        core = core_with([(1, [tracked(5, A)], [], []), (2, [], [lost(5, A)], [])], coasting_limit=3)
        core.designate(A, 1, None)
        core.drain_events()
        for frame_id in range(3, 7):
            core.record(frame_id, meta(frame_id), [], [lost(5, A)], [], frame_id)
        events = core.drain_events()
        self.assertEqual([(e["event"], e["cause"]) for e in events], [("COASTING_TO_TRACK_ENDED", "coasting_limit")])
        self.assertEqual(core.pointer_result(6).reason, "bound_track_removed")

    def test_coasting_limit_boundary_fires_on_exact_step(self):
        """IR-8（C1 退回）：上限 = `coasting_limit` 次 step——第 limit 次 step 仍未找回即转 `TRACK_ENDED`，第 limit−1 次不转。"""
        for limit in (3, 30):
            with self.subTest(limit=limit):
                core = core_with([(1, [tracked(5, A)], [], []), (2, [], [lost(5, A)], [])], coasting_limit=limit)
                core.designate(A, 1, None)
                core.drain_events()
                for frame_id in range(3, 3 + limit - 1):
                    core.record(frame_id, meta(frame_id), [], [lost(5, A)], [], frame_id)
                self.assertEqual(core.drain_events(), [])  # 第 limit−1 次：仍 coasting
                self.assertEqual(core.pointer_result(2 + limit - 1).reason, "bound_track_unmatched")
                last = 2 + limit
                core.record(last, meta(last), [], [lost(5, A)], [], last)  # 第 limit 次
                events = core.drain_events()
                self.assertEqual(
                    [(e["event"], e["cause"], e["frame_id"]) for e in events],
                    [("COASTING_TO_TRACK_ENDED", "coasting_limit", last)],
                )
                self.assertEqual(core.pointer_result(last).reason, "bound_track_removed")

    def test_coasting_recovered_on_exact_limit_step_is_not_ended(self):
        """第 limit 次 step 找回 → `COASTING_RECOVERED`（找回优先），不转 `TRACK_ENDED`。"""
        core = core_with([(1, [tracked(5, A)], [], []), (2, [], [lost(5, A)], [])], coasting_limit=3)
        core.designate(A, 1, None)
        core.drain_events()
        for frame_id in (3, 4):
            core.record(frame_id, meta(frame_id), [], [lost(5, A)], [], frame_id)
        core.record(5, meta(5), [tracked(5, A)], [], [], 5)
        self.assertEqual([e["event"] for e in core.drain_events()], ["COASTING_RECOVERED"])
        self.assertTrue(core.pointer_result(5).ok)
        # 找回后再丢：coasting 记账已结束，超过上限也不再产生 `COASTING_TO_TRACK_ENDED`（不自动转向，D.1）。
        for frame_id in range(6, 12):
            core.record(frame_id, meta(frame_id), [], [lost(5, A)], [], frame_id)
        self.assertEqual(core.drain_events(), [])
        self.assertEqual(core.pointer_result(11).reason, "bound_track_unmatched")

    def test_coasting_same_id_follow_does_not_reset_count(self):
        """同 id 重复 `follow` 不重置 coasting 计数；第 limit 次 step 照常转 `TRACK_ENDED`。"""
        core = core_with([(1, [tracked(5, A)], [], []), (2, [], [lost(5, A)], [])], coasting_limit=3)
        core.designate(A, 1, None)
        core.drain_events()
        core.record(3, meta(3), [], [lost(5, A)], [], 3)
        core.follow(5)
        core.record(4, meta(4), [], [lost(5, A)], [], 4)
        core.follow(5)
        self.assertEqual(core.drain_events(), [])
        core.record(5, meta(5), [], [lost(5, A)], [], 5)
        self.assertEqual([(e["event"], e["cause"]) for e in core.drain_events()], [("COASTING_TO_TRACK_ENDED", "coasting_limit")])

    def test_track_ended_when_removed_at_head(self):
        core = core_with([(1, [tracked(5, A), tracked(6, B)], [], []), (2, [tracked(6, B)], [], [5])])
        core.follow(6)
        d = core.designate(A, 1, None)
        self.assertEqual((d.result, d.track_id, core.pointer()), ("TRACK_ENDED", 5, 6))

    def test_frame_not_in_history(self):
        core = core_with([(i, [tracked(1, A)], [], []) for i in range(1, 102)])
        factory = SotFactory([])
        d = core.designate(A, 1, runner_for(core, MemoryRepository(range(1, 102)), factory))
        self.assertEqual((d.result, factory.calls), ("FRAME_NOT_IN_HISTORY", 0))

    def test_pointer_result_no_pointer(self):
        core = core_with([(1, [tracked(1, A)], [], [])])
        self.assertEqual(core.pointer_result(1), TrackerResult.lost("no_pointer"))


class LevelTwo(unittest.TestCase):
    """AC-19（§3.4.1 + 接受释义）：k 帧漏检、k+1…h 有检测轨迹 j，SOT 从 k 起跟回放到 h 收养。"""

    def frames(self, h=5, head_rows=None):
        rows = [(1, [], [], [])]  # k = 1：检测替身漏检对象
        for frame_id in range(2, h + 1):
            rows.append((frame_id, head_rows if head_rows is not None else [tracked(7, B)], [], []))
        return rows

    def test_level2_success_adopted(self):
        core = core_with(self.frames())
        before = [core.history(f) for f in range(1, 6)]
        factory = SotFactory([ok(B)] * 4)
        repo = MemoryRepository(range(1, 6))
        d = core.designate(A, 1, runner_for(core, repo, factory))
        self.assertEqual((d.result, d.resolution_level, d.track_id, core.pointer()), ("BOUND", 2, 7, 7))
        self.assertEqual(factory.calls, 1)
        self.assertEqual(d.level2["replayed_frames"], 4)
        self.assertIn("elapsed_ms", d.level2)
        self.assertEqual([core.history(f) for f in range(1, 6)], before)  # SOT 框不进历史
        for got, want in zip(core.pointer_result(5).box_norm, B):  # 发布的是检测轨迹框
            self.assertAlmostEqual(got, want, places=9)
        self.assertEqual([e["event"] for e in d.events], ["L2_STARTED", "L2_ADOPTED"])

    def test_level2_failure_sot_lost(self):
        core = core_with(self.frames())
        core.follow(3)
        factory = SotFactory([ok(B), TrackerResult.lost("tracker_reported_failure")])
        d = core.designate(A, 1, runner_for(core, MemoryRepository(range(1, 6)), factory))
        self.assertEqual((d.result, d.level2["reason"], core.pointer()), ("NO_TRACK_AT_K", "sot_lost@3", 3))

    def test_level2_failure_no_adoption(self):
        core = core_with(self.frames())
        factory = SotFactory([ok((0.9, 0.9, 0.05, 0.05))] * 4)
        d = core.designate(A, 1, runner_for(core, MemoryRepository(range(1, 6)), factory))
        self.assertEqual((d.result, d.level2["reason"]), ("NO_TRACK_AT_K", "no_adoption"))

    def test_level2_failure_ambiguous(self):
        core = core_with(self.frames(head_rows=[tracked(7, B), tracked(8, C)]))
        factory = SotFactory([ok((0.51, 0.50, 0.10, 0.10))] * 4)
        d = core.designate(A, 1, runner_for(core, MemoryRepository(range(1, 6)), factory))
        self.assertEqual((d.result, d.resolution_level, d.candidates, core.pointer()), ("AMBIGUOUS", 2, (7, 8), None))

    def test_level2_failure_replay_timeout(self):
        core = core_with(self.frames())
        ticks = iter([0.0] + [0.1] * 3 + [5.0] * 20)
        factory = SotFactory([ok(B)] * 4)
        d = core.designate(A, 1, runner_for(core, MemoryRepository(range(1, 6)), factory, clock=lambda: next(ticks)))
        self.assertEqual(d.result, "NO_TRACK_AT_K")
        self.assertTrue(d.level2["reason"].startswith("replay_timeout@"), d.level2["reason"])

    def test_level2_invalid_source_box(self):
        core = core_with(self.frames())
        core.follow(3)
        factory = SotFactory([ok(B)] * 4)
        d = core.designate((0.95, 0.95, 0.10, 0.10), 1, runner_for(core, MemoryRepository(range(1, 6)), factory))
        self.assertEqual((d.result, d.level2["reason"], core.pointer()), ("NO_TRACK_AT_K", "invalid_source_box", 3))

    def test_level2_non_init_exception(self):
        core = core_with(self.frames())
        core.follow(3)
        factory = SotFactory([], raise_on_update=RuntimeError("boom"))
        d = core.designate(A, 1, runner_for(core, MemoryRepository(range(1, 6)), factory))
        self.assertEqual((d.result, d.level2["reason"], d.level2["exception_class"], core.pointer()), ("NO_TRACK_AT_K", "replay_error", "RuntimeError", 3))

    def test_level2_failure_init(self):
        core = core_with(self.frames())
        factory = SotFactory([], init_ok=False)
        d = core.designate(A, 1, runner_for(core, MemoryRepository(range(1, 6)), factory))
        self.assertEqual((d.result, d.level2["reason"]), ("NO_TRACK_AT_K", "sot_init_failed"))

    def test_level2_old_frame_outside_history(self):
        core = core_with([(1, [], [], [])] + [(f, [tracked(7, B)], [], []) for f in range(2, 103)])
        factory = SotFactory([ok(B)])
        d = core.designate(A, 1, runner_for(core, MemoryRepository(range(1, 103)), factory))
        self.assertEqual((d.result, factory.calls), ("FRAME_NOT_IN_HISTORY", 0))

    def test_level2_old_frame_evicted_from_source(self):
        core = core_with(self.frames())
        factory = SotFactory([ok(B)] * 4)
        d = core.designate(A, 1, runner_for(core, MemoryRepository(range(2, 6)), factory))
        self.assertEqual((d.result, d.level2["reason"], d.level2["attempted"]), ("NO_TRACK_AT_K", "not_attempted_frame_missing", False))

    def test_level2_not_triggered_when_level1_ambiguous_or_ended(self):
        factory = SotFactory([ok(B)])
        core = core_with([(1, [tracked(1, B), tracked(2, C)], [], []), (2, [tracked(1, B)], [], [])])
        repo = MemoryRepository(range(1, 3))
        self.assertEqual(core.designate((0.51, 0.50, 0.10, 0.10), 1, runner_for(core, repo, factory)).result, "AMBIGUOUS")
        core = core_with([(1, [tracked(1, A)], [], []), (2, [], [], [1])])
        self.assertEqual(core.designate(A, 1, runner_for(core, repo, factory)).result, "TRACK_ENDED")
        self.assertEqual(factory.calls, 0)

    def test_mapping_covers_every_replay_event(self):
        from controller.reanchor import ReplayResult  # noqa: PLC0415

        cases = {
            ("RESEED_DISCARDED_MISSING_FRAME", "source_frame_missing", None): "not_attempted_frame_missing",
            ("RESEED_DISCARDED_STALE", "source_result_too_old", None): "source_too_old",
            ("RESEED_DISCARDED_NOT_CONVERGED", "catchup_timeout", 6): "replay_timeout@7",
            ("RESEED_DISCARDED_INVALID_BOX", "invalid_source_box", None): "invalid_source_box",
            ("RESEED_DISCARDED_INVALID_BOX", "invalid_replay_box", 9): "sot_lost@9",
            ("RESEED_FAILED", "tracker_init_failed", None): "sot_init_failed",
            ("RESEED_FAILED", "ZeroDivisionError", None): "replay_error",
        }
        for (event, reason, head), expected in cases.items():
            result, mapped, _ = rc.level2_mapping(ReplayResult(event, None, 3, head, 0, 0.0, None, reason))
            self.assertEqual((result, mapped), ("NO_TRACK_AT_K", expected), event)
            self.assertTrue(rc.is_level2_reason(mapped))


# --- P1-ENG-CAPTURE-001 AC-3（K1）：历史契约补列 ------------------------------------------------------


class _Lost:
    def __init__(self, track_id, xyxy):
        self.track_id, self.xyxy, self.score, self.cls = track_id, list(xyxy), 0.8, 0.0


class HistoryContractTests(unittest.TestCase):
    def test_out_of_frame_lost_kept_and_non_finite_dropped(self):
        dropped = []
        tracked, lost = rc.rows_from_library(
            [[10.0, 10.0, 50.0, 50.0, 1, 0.9, 0.0, 2]],
            [_Lost(2, [-80.0, 10.0, -20.0, 50.0]), _Lost(3, [float("nan"), 0.0, 1.0, 1.0]), _Lost(4, [100.0, 100.0, 100.0, 120.0])],
            640, 480, dropped=dropped,
        )
        self.assertEqual(tracked[0].matched_det_index, 2)
        self.assertEqual([(r.track_id, r.out_of_frame) for r in lost], [(2, True), (4, True)])
        self.assertEqual(dropped, [3])
        # IR-1：捕获视图（捕获入口显式启用）保留出画/退化 lost 行，指针判 UNMATCHED。
        core = rc.ResidentCore(100, history_view=rc.HISTORY_VIEW_CAPTURE)
        core.record(1, meta(1), tracked, lost, [], 1, silently_dropped_ids=dropped)
        core.follow(2)
        self.assertEqual(core.pointer_result(1).reason, "bound_track_unmatched")
        self.assertEqual([r.track_id for r in core.history(1).rows(rc.LOST)], [2, 4])
        self.assertEqual(core.history(1).silently_dropped_ids, (3,))

    def test_compat_view_keeps_old_drop_and_removed(self):
        """IR-1：缺省（兼容/旧工厂）视图在旧 `_norm_box` 会丢弃的条件下仍视为无该行 → 指针判 `bound_track_removed`
        （与修改前同帧），未确认行也不进旧消费视图；coasting 记账按旧规则在该帧转 TRACK_ENDED(removed)。"""
        tracked, lost = rc.rows_from_library(
            [[10.0, 10.0, 50.0, 50.0, 1, 0.9, 0.0, 2]], [_Lost(2, [-80.0, 10.0, -20.0, 50.0]), _Lost(4, [100.0, 100.0, 100.0, 120.0])], 640, 480,
        )
        core = rc.ResidentCore(100)
        self.assertEqual(core.history_view, rc.HISTORY_VIEW_COMPAT)
        core.record(1, meta(1), [tracked[0], rc.TrackRow(2, B, 0.9, 0, rc.TRACKED)], [], [], 1)
        core.follow(2)
        core.begin_coasting(5)
        core.record(2, meta(2), tracked, lost, [], 2, unconfirmed_rows=[rc.TrackRow(9, A, 0.9, 0, rc.UNCONFIRMED, 0)])
        entry = core.history(2)
        self.assertEqual([(r.track_id, r.state) for r in entry.tracks], [(1, rc.TRACKED)])
        self.assertEqual(core.pointer_result(2).reason, rc.REASON_REMOVED)
        self.assertIsNone(core.coasting)
        self.assertEqual(core.drain_events()[-1]["event"], "COASTING_TO_TRACK_ENDED")
        with self.assertRaises(ValueError):
            rc.ResidentCore(100, history_view="guess-from-gmc")

    def test_unconfirmed_rows_never_ok(self):
        core = rc.ResidentCore(100, history_view=rc.HISTORY_VIEW_CAPTURE)
        row = rc.TrackRow(9, A, 0.9, 0, rc.UNCONFIRMED, 0)
        core.record(1, meta(1), [], [], [], 1, unconfirmed_rows=[row])
        core.follow(9)
        self.assertFalse(core.pointer_result(1).ok)
        self.assertEqual(core.history(1).rows(rc.UNCONFIRMED)[0].track_id, 9)

    def test_old_rows_record_keys_unchanged(self):
        self.assertEqual(set(tracked(1, A).as_record()), {"track_id", "box_norm", "score", "cls", "state"})
        entry = core_with([(7, [tracked(1, A)], [lost(2, B)], [3])]).history(7)
        self.assertEqual(set(entry.as_record()), {"frame_id", "simulation_time_s", "capture_monotonic_s", "library_frame_id", "tracks", "removed_ids"})

    def test_kf_snapshot_invalid_reasons(self):
        ok = rc.make_kf_snapshot(1, 1, 5, rc.KF_PRIOR, (1, 2, 3, 4), (0, 0), ((1, 0), (0, 1)))
        self.assertTrue(ok.valid)
        cases = {
            "kf_non_finite": ((float("nan"), 2, 3, 4), ((1, 0), (0, 1))),
            "kf_non_positive_size": ((1, 2, 0, 4), ((1, 0), (0, 1))),
            "kf_cov_asymmetric": ((1, 2, 3, 4), ((1, 0.5), (0, 1))),
            "kf_cov_not_psd": ((1, 2, 3, 4), ((1, 2), (2, 1))),
            "kf_unreadable": (None, ((1, 0), (0, 1))),
        }
        for reason, (box, cov) in cases.items():
            with self.subTest(reason=reason):
                snap = rc.make_kf_snapshot(1, 1, 5, rc.KF_POSTERIOR, box, (0, 0), cov)
                self.assertEqual((snap.valid, snap.invalid_reason), (False, reason))
                self.assertEqual(rc.KfSnapshot.from_record(snap.as_record()).invalid_reason, reason)
        with self.assertRaises(ValueError):
            rc.make_kf_snapshot(1, 1, 5, "bogus", (1, 2, 3, 4), (0, 0), ((1, 0), (0, 1)))

    def test_resolve_designation_shell_matches_designate(self):
        frames = [(1, [tracked(1, A), tracked(2, B)], [], []), (2, [tracked(2, B)], [lost(1, A)], [])]
        old, new = core_with(frames), core_with(frames)
        d_old = old.designate(A, 1, None)
        designation_id = new.allocate_designation_id()
        d_new = new.resolve_designation(A, 1, None, designation_id)
        self.assertIsNone(new.pointer())
        self.assertEqual(d_new, d_old)
        self.assertEqual((d_old.result, old.pointer(), old.coasting), ("BOUND_COASTING", 1, {"designation_id": 1, "steps": 0}))
        snapshot = new.snapshot_binding_state()
        new.follow(1)
        new.begin_coasting(designation_id)
        self.assertFalse(new.binding_state_matches(snapshot))
        new.restore_binding_state(snapshot)
        self.assertTrue(new.binding_state_matches(snapshot))


if __name__ == "__main__":
    unittest.main()
