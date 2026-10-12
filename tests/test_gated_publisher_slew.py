#!/usr/bin/env python3
"""P1-ENG-ACQ-001 AC-14（§3.7）：无同帧观测的转向通道 `slew_look_at` 与速度指令仍须同帧观测。"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller.body_planner import BodyCommand  # noqa: E402
from controller.gated_publisher import (  # noqa: E402
    RECEIPT_CHANNELS,
    BodyCommandNotWritten,
    FrameSnapshotRing,
    GatedPublisher,
)


class Inner:
    def __init__(self):
        self.calls: list[tuple[str, object]] = []

    def look_at(self, point):
        self.calls.append(("look_at", tuple(point)))
        return Path("gimbal_command.json")

    def hold_body(self):
        self.calls.append(("hold_body", None))

    def set_nadir(self):
        self.calls.append(("set_nadir", None))

    def observation(self, *args):
        self.calls.append(("observation", args))

    def body_command(self, command):
        self.calls.append(("body_command", command.mode))
        return Path("body_command.json")


class SlewChannel(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.inner = Inner()
        self.publisher = GatedPublisher(
            self.inner,
            FrameSnapshotRing(root / "ring", capacity=4),
            frames_directory=root / "frames",
            receipts_path=root / "publish-receipts.jsonl",
            k_pub=2,
            t_pub_s=0.4,
            t_stall_s=3.0,
            track_id="s1-t0",
        )
        self.receipts_path = root / "publish-receipts.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def receipts(self):
        return [json.loads(line) for line in self.receipts_path.read_text(encoding="utf-8").splitlines()]

    def test_slew_at_most_once_per_designation(self):
        self.publisher.unmute()
        self.assertIsNotNone(self.publisher.slew_look_at((10.0, 0.0, 20.0), 7))
        self.assertIsNone(self.publisher.slew_look_at((11.0, 0.0, 21.0), 7))
        self.assertIsNotNone(self.publisher.slew_look_at((12.0, 0.0, 22.0), 8))
        rows = self.receipts()
        self.assertEqual([(r["channel"], r["outcome"], r["reason"]) for r in rows], [
            ("slew_look_at", "WRITTEN", None),
            ("slew_look_at", "PUBLISH_REJECTED", "slew_repeated"),
            ("slew_look_at", "WRITTEN", None),
        ])
        self.assertEqual([c for c in self.inner.calls if c[0] == "look_at"], [("look_at", (10.0, 0.0, 20.0)), ("look_at", (12.0, 0.0, 22.0))])
        self.assertIsNone(self.publisher.fatal_reason)  # 重复转向只拒绝、不终止
        self.assertIn("slew_look_at", RECEIPT_CHANNELS)

    def test_slew_needs_no_same_frame_observation_but_respects_mute_and_finalize(self):
        self.assertIsNone(self.publisher.slew_look_at((1.0, 0.0, 1.0), 1))
        self.assertEqual(self.receipts()[-1]["outcome"], "MUTED_DROPPED")
        self.publisher.unmute()
        self.assertIsNone(self.publisher.accepted_frame_id)
        self.assertIsNotNone(self.publisher.slew_look_at((1.0, 0.0, 1.0), 1))
        self.publisher.finalize()
        count = len(self.receipts())
        self.assertIsNone(self.publisher.slew_look_at((1.0, 0.0, 1.0), 2))
        self.assertEqual(len(self.receipts()), count)

    def test_velocity_during_acquiring_is_orphan_control_hold_passes(self):
        self.publisher.unmute()
        self.publisher.accepted_frame_id = 41  # 旧指针最后一帧的关联
        self.publisher.clear_association()
        self.publisher.slew_look_at((1.0, 0.0, 1.0), 3)
        with self.assertRaises(BodyCommandNotWritten):
            self.publisher.body_command(BodyCommand.velocity(1.0, 0.0, 0.4, "test"))
        self.assertEqual(self.receipts()[-1]["reason"], "orphan_control")
        self.publisher.body_command(BodyCommand.hold(0.4, "no_observation"))
        self.assertEqual(self.receipts()[-1]["channel"], "body_safety_hold")
        self.assertEqual(self.inner.calls[-1], ("body_command", "hold"))


if __name__ == "__main__":
    unittest.main()
