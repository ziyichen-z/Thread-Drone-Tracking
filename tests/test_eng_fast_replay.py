#!/usr/bin/env python3
"""P1-ENG-FAST-001 AC-5：P2b 七类互斥结局的 11 条具名反例、守恒式与钉版库边界红绿。

合成序列只用于判定逻辑（纯函数）；库边界三条（`adapter_boxes_fields`、`one_update_per_frame`、
`library_buffer_boundary`）直接调钉版 ultralytics 跟踪器，需要 `.venv-yoloe`（含 `lap`），
缺依赖时跳过并在证据日志中如实记录。
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_fast import replay  # noqa: E402
from tools.eng_fast.replay import (  # noqa: E402
    CENSORED_END,
    ID_SWITCH,
    KEPT,
    LOST_BEYOND_BUFFER,
    NO_BINDING,
    TRUTH_GAP,
    UNBOUND_START,
    UNRESOLVED_END_MISS,
)

BUFFER = 30
DT = 0.2  # 5 Hz：W = 8 s → 窗口内 40 个调用帧


def times(n: int) -> list[float]:
    return [round(i * DT, 6) for i in range(n)]


def outcome(bindings, start=0, window=8.0, buffer=BUFFER):
    return replay.window_outcome(times(len(bindings)), bindings, start, window, buffer)


HAVE_LIBS = importlib.util.find_spec("lap") is not None and importlib.util.find_spec("ultralytics") is not None


class NamedCounterexamples(unittest.TestCase):
    """§3.4 的 11 条具名反例。"""

    def test_start_unbound_excluded(self) -> None:
        bindings = [NO_BINDING] + [1] * 60
        self.assertEqual(outcome(bindings), (UNBOUND_START, False))
        summary = replay.window_summary(times(len(bindings)), bindings, 8.0, BUFFER)
        self.assertEqual(summary["UNBOUND_START"], 1)

    def test_end_censored_excluded(self) -> None:
        bindings = [1] * 30  # 序列只有 5.8 s，8 s 窗口越过末帧
        self.assertEqual(outcome(bindings), (CENSORED_END, False))

    def test_recover_same_id_within_buffer_kept(self) -> None:
        bindings = [1] * 5 + [NO_BINDING] * 30 + [1] * 30
        self.assertEqual(outcome(bindings), (KEPT, False))

    def test_recover_new_id_is_switch(self) -> None:
        bindings = [1] * 5 + [NO_BINDING] * 5 + [2] * 60
        self.assertEqual(outcome(bindings), (ID_SWITCH, False))

    def test_miss_beyond_buffer_not_kept(self) -> None:
        bindings = [1] * 2 + [NO_BINDING] * 31 + [2] * 40
        self.assertEqual(outcome(bindings)[0], LOST_BEYOND_BUFFER)

    def test_truth_gap_excluded(self) -> None:
        bindings = [1] * 2 + [None] * 31 + [1] * 40
        self.assertEqual(outcome(bindings), (TRUTH_GAP, False))

    def test_end_gap_resolved_same_id_after_window_kept(self) -> None:
        # 窗口 (0, 8] s = 帧 1…40；帧 36…45 漏检（L = 10 ≤ 30），帧 46 同 ID 恢复（在窗口之外）。
        bindings = [1] * 36 + [NO_BINDING] * 10 + [1] * 20
        self.assertEqual(outcome(bindings), (KEPT, False))

    def test_end_gap_resolved_other_id_after_window_switch(self) -> None:
        bindings = [1] * 36 + [NO_BINDING] * 10 + [2] * 20
        self.assertEqual(outcome(bindings), (ID_SWITCH, False))

    def test_end_gap_unresolved_at_sequence_end_not_kept(self) -> None:
        bindings = [1] * 36 + [NO_BINDING] * 10  # 序列在漏检中结束，L = 10 ≤ 30
        self.assertEqual(outcome(bindings), (UNRESOLVED_END_MISS, False))
        # 起点 0…5（t ≤ 1.0 s，窗口不越过末帧 9.0 s）全部 UNRESOLVED；6…35 删失；36…45 无绑定。
        summary = replay.window_summary(times(len(bindings)), bindings, 8.0, BUFFER)
        self.assertEqual(summary["UNRESOLVED_END_MISS"], 6)
        self.assertEqual(summary["KEPT"], 0)
        self.assertEqual(summary["D"], 6)
        self.assertEqual(summary["retention"], 0.0)

    def test_drift_return_beyond_buffer_not_kept(self) -> None:
        bindings = [1] * 2 + [NO_BINDING] * 31 + [1] * 40
        self.assertEqual(outcome(bindings), (LOST_BEYOND_BUFFER, 31))
        summary = replay.window_summary(times(len(bindings)), bindings, 8.0, BUFFER)
        self.assertGreaterEqual(summary["drift_return"], 1)
        self.assertGreaterEqual(summary["drift_return_at_L_eq_buffer_plus_1"], 1)
        longer = [1] * 2 + [NO_BINDING] * 40 + [1] * 40
        self.assertEqual(outcome(longer), (LOST_BEYOND_BUFFER, 40))

    def test_counts_conserve(self) -> None:
        bindings = (
            [NO_BINDING] * 3 + [1] * 10 + [NO_BINDING] * 12 + [1] * 10 + [None] * 35 + [2] * 20 + [NO_BINDING] * 40 + [2] * 5
        )
        bins = ["<35" if i % 2 else ">=65" for i in range(len(bindings))]
        for window in replay.WINDOWS_S:
            summary = replay.window_summary(times(len(bindings)), bindings, window, BUFFER, bins)
            self.assertTrue(summary["conserved"])
            excluded = summary["UNBOUND_START"] + summary["CENSORED_END"] + summary["TRUTH_GAP"]
            self.assertEqual(summary["V"], excluded + summary["D"])
            for bucket in summary["by_start_distance_bin"].values():
                self.assertTrue(bucket["conserved"])
                self.assertEqual(
                    bucket["V"], bucket["UNBOUND_START"] + bucket["CENSORED_END"] + bucket["TRUTH_GAP"] + bucket["D"]
                )
            self.assertEqual(sum(b["V"] for b in summary["by_start_distance_bin"].values()), summary["V"])


class TimestampAndMetrics(unittest.TestCase):
    def test_invalid_timestamps_rejected(self) -> None:
        with self.assertRaises(replay.InvalidTimestamps):
            replay.check_timestamps([0.0, 0.2, 0.2, 0.4])
        with self.assertRaises(replay.InvalidTimestamps):
            replay.check_timestamps([0.0, 0.4, 0.2])

    def test_sequence_metrics(self) -> None:
        bindings = [1, 1, NO_BINDING, NO_BINDING, 1, None, 2, 2, NO_BINDING, 2]
        metrics = replay.sequence_metrics(times(len(bindings)), bindings, BUFFER)
        self.assertEqual(metrics["id_switches"], 1)
        self.assertEqual(metrics["fragments"], 2)
        self.assertEqual(metrics["miss_segment_lengths"]["count"], 3)
        self.assertAlmostEqual(metrics["track_buffer_median_seconds"], 30 * DT, places=6)

    def test_bind_prefers_highest_iou_then_smaller_id(self) -> None:
        truth = [(0.1, 0.1, 0.2, 0.2), None, (0.5, 0.5, 0.1, 0.1)]
        rows = [
            [[64, 48, 192, 144, 7, 0.9, 0, 0], [64, 48, 192, 144, 3, 0.9, 0, 1]],
            [[0, 0, 10, 10, 5, 0.9, 0, 0]],
            [[0, 0, 10, 10, 5, 0.9, 0, 0]],
        ]
        self.assertEqual(replay.bind(truth, rows, 640, 480), [3, None, NO_BINDING])


@unittest.skipUnless(HAVE_LIBS, "需要 .venv-yoloe（ultralytics 8.4.104 + lap）")
class LibraryBoundary(unittest.TestCase):
    """钉版库实测：事实 20 的读码结论以此为准。"""

    def _image(self):
        import numpy as np  # noqa: PLC0415

        rng = np.random.default_rng(20260923)
        return rng.integers(0, 255, size=(480, 640, 3), dtype=np.uint8)

    def test_adapter_boxes_fields(self) -> None:
        import numpy as np  # noqa: PLC0415

        dets = [[0.1, 0.2, 0.3, 0.4, 0.9, 0.0], [0.5, 0.5, 0.1, 0.1, 0.2, 1.0]]
        boxes = replay.as_boxes(dets, 640, 480)
        np.testing.assert_allclose(boxes.conf, [0.9, 0.2], rtol=1e-6)
        np.testing.assert_allclose(boxes.cls, [0.0, 1.0])
        np.testing.assert_allclose(boxes.xywh[0], [0.25 * 640, 0.4 * 480, 0.3 * 640, 0.4 * 480], rtol=1e-5)
        subset = boxes[boxes.conf >= 0.25]
        self.assertEqual(len(subset), 1)
        self.assertEqual(len(replay.as_boxes([], 640, 480)), 0)

    def test_one_update_per_frame(self) -> None:
        for algorithm in replay.ALGORITHMS:
            tracker = replay.make_tracker(algorithm)
            self.assertFalse(hasattr(tracker.args, "frame_rate") and tracker.args.frame_rate is not None)
            frames = [([[0.4, 0.4, 0.1, 0.1, 0.9, 0.0]] if i % 3 else [], self._image(), 640, 480) for i in range(12)]
            replay.run_sequence(tracker, frames)
            self.assertEqual(tracker.frame_id, 12)

    def _boundary(self, algorithm: str, empty_calls: int) -> tuple[int, int]:
        """目标连续 5 帧、空检测 `empty_calls` 次调用、再出现：返回 (消失前 ID, 再出现后 ID)。"""
        tracker = replay.make_tracker(algorithm)
        box = [[0.4, 0.4, 0.1, 0.1, 0.9, 0.0]]
        image = self._image()
        frames = [(box, image, 640, 480)] * 5 + [([], image, 640, 480)] * empty_calls + [(box, image, 640, 480)] * 2
        outputs = replay.run_sequence(tracker, frames)
        first = int(outputs[4][0][4])
        after = int(outputs[5 + empty_calls][0][4]) if outputs[5 + empty_calls] else -1
        if after == -1:  # 新轨迹首帧可能尚未激活：取下一帧
            after = int(outputs[6 + empty_calls][0][4])
        return first, after

    def test_library_buffer_boundary(self) -> None:
        """AC-5 库边界实测（合同：「这是对库边界的实测，事实 20 的读码结论以它为准」）。

        实测（两算法相同）：空检测 30 次 → 同 ID（与合同一致）；31 次 → **仍同 ID**（与事实 20 的
        「L ≥ 31 必为新 ID」不符：`merge_track_pools` 先按 `removed_stracks` 剔除 lost 池、后追加本帧
        移除项，被标记移除的轨迹在下一帧仍参与关联）；32 次 → 新 ID。实测边界记入证据 IR-8 交 C1 裁定；
        判定阈值仍按 §3.4 字面（L ≥ 31 → LOST_BEYOND_BUFFER），L = 31 的原 ID 找回单列子计数。
        """
        for algorithm in replay.ALGORITHMS:
            with self.subTest(algorithm=algorithm):
                self.assertEqual(replay.make_tracker(algorithm).max_frames_lost, 30)
                first, after = self._boundary(algorithm, 30)
                self.assertEqual(first, after, "空检测恰 30 次调用后应同 ID 恢复")
                first, after = self._boundary(algorithm, 31)
                self.assertEqual(first, after, "实测：空检测 31 次调用后仍同 ID（IR-8，与事实 20 不符）")
                first, after = self._boundary(algorithm, 32)
                self.assertNotEqual(first, after, "空检测 32 次调用后为新 ID")

if __name__ == "__main__":
    unittest.main()
