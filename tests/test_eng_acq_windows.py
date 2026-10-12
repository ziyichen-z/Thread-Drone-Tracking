#!/usr/bin/env python3
"""P1-ENG-ACQ-001 AC-8 / H-9（FAST-001 R1-2）：E2 复用 `window_summary` 前的「空窗即拒绝」断言。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_acq import e2  # noqa: E402
from tools.eng_fast import replay as fast_replay  # noqa: E402


class EmptyWindowGuard(unittest.TestCase):
    def test_empty_window_rejected(self):
        """>8 s 空窗：原 `window_outcome` 会零证据判 KEPT；线束断言先拒绝。"""
        times = [0.0, 0.2, 0.4, 20.0, 20.2, 40.0]
        bindings = [1, 1, 1, 1, 1, 1]
        self.assertEqual(fast_replay.window_outcome(times, bindings, 2, 13.0, 30), (fast_replay.KEPT, 0))  # 复现缺陷
        with self.assertRaises(e2.EmptyWindow):
            e2.guarded_window_summary(times, bindings, 13.0, 30)

    def test_window_without_frames_rejected_even_below_gap_limit(self):
        times = [0.0, 7.9, 15.8, 23.7, 31.6]
        with self.assertRaises(e2.EmptyWindow):
            e2.assert_no_empty_window(times, [1, 1, 1, 1, 1], 5.0)

    def test_dense_sequence_passes_and_matches_window_summary(self):
        times = [i * 0.2 for i in range(200)]
        bindings = [1 if i % 7 else 0 for i in range(200)]
        self.assertEqual(e2.guarded_window_summary(times, bindings, 13.0, 30), fast_replay.window_summary(times, bindings, 13.0, 30))

    def test_pool_windows_conserved(self):
        times = [i * 0.2 for i in range(200)]
        piece = e2.guarded_window_summary(times, [1] * 200, 13.0, 30)
        pooled = e2.pool_windows([piece, piece])
        self.assertEqual(pooled["V"], 2 * piece["V"])
        self.assertTrue(pooled["conserved"])


if __name__ == "__main__":
    unittest.main()
