#!/usr/bin/env python3
"""P1-ENG-FASTFIX-001 AC-19（K4）：粗粒度账本——启动前按剩余量拦截、尝试即记失败不返还、UNKNOWN/损坏拒启、未列维度为 0。"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_fastfix import ledger  # noqa: E402

ENVELOPE_A = {"candidates": 3, "yolo_loads": 14, "wall_s": 7200, "disk_peak_bytes": 2_000_000_000, "git_new_bytes": 2_000_000_000}


class LedgerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "ledger.json"
        ledger.create(self.path, stage="A", envelope=ENVELOPE_A, authorization="FASTFIX:A:1")

    def test_launch_refused_when_balance_insufficient(self):
        ledger.record(self.path, "yolo_loads", 13, note="attempts")
        ledger.check_launch(ledger.read(self.path), {"yolo_loads": 1})
        with self.assertRaisesRegex(ledger.LedgerRefused, "S-BUDGET"):
            ledger.check_launch(ledger.read(self.path), {"yolo_loads": 2})

    def test_attempt_recorded_and_failure_not_refunded(self):
        ledger.record(self.path, "yolo_loads", 1, note="attempt 1 (failed)")
        ledger.record(self.path, "yolo_loads", 1, note="retry")
        self.assertEqual(ledger.read(self.path)["used"]["yolo_loads"], 2)
        self.assertEqual(len(ledger.read(self.path)["entries"]), 2)

    def test_unlisted_dimension_is_zero(self):
        with self.assertRaisesRegex(ledger.LedgerRefused, "not in the signed envelope"):
            ledger.check_launch(ledger.read(self.path), {"unity_play": 1})
        with self.assertRaises(ledger.LedgerRefused):
            ledger.record(self.path, "tx_bytes", 1, note="no TX signed")

    def test_unknown_and_corruption_refuse_every_launch(self):
        with self.assertRaises(ledger.LedgerUnknown):
            ledger.record(self.path, "disk_peak_bytes", unknown=True, note="meter unavailable")
        self.assertEqual(ledger.read(self.path)["used"]["disk_peak_bytes"], ledger.UNKNOWN)  # 已落账、不推余额
        with self.assertRaises(ledger.LedgerUnknown):
            ledger.check_launch(ledger.read(self.path), {"yolo_loads": 1})
        other = self.path.with_name("other.json")
        ledger.create(other, stage="A", envelope=ENVELOPE_A, authorization="x")
        document = json.loads(other.read_text(encoding="utf-8"))
        document["used"]["yolo_loads"] = 0.5  # 手改而未重算校验和
        other.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(ledger.LedgerUnknown):
            ledger.read(other)
        missing = self.path.with_name("missing.json")
        with self.assertRaises(ledger.LedgerUnknown):
            ledger.read(missing)

    def test_out_of_bounds_dimension_blocks_unrelated_launch(self):
        """全维上限校验（承接 CAPTURE R1-4 教训）：任一维已越界（含未申请维度）→ 一切启动拒绝。"""
        with self.assertRaises(ledger.LedgerRefused):
            ledger.record(self.path, "candidates", 4, note="over")
        self.assertEqual(ledger.read(self.path)["used"]["candidates"], 4)  # 已记、不返还
        with self.assertRaisesRegex(ledger.LedgerRefused, "out of bounds"):
            ledger.check_launch(ledger.read(self.path), {"wall_s": 1})

    def test_wall_clock_union_and_disk_peak(self):
        ledger.record(self.path, "wall_s", interval=(100.0, 160.0), note="a")
        ledger.record(self.path, "wall_s", interval=(150.0, 200.0), note="b overlaps")
        ledger.record(self.path, "wall_s", interval=(300.0, 310.0), note="c")
        self.assertEqual(ledger.read(self.path)["used"]["wall_s"], 110.0)
        ledger.record(self.path, "disk_peak_bytes", 500, note="p1")
        ledger.record(self.path, "disk_peak_bytes", 300, note="p2")
        self.assertEqual(ledger.read(self.path)["used"]["disk_peak_bytes"], 500)
        with self.assertRaises(ledger.LedgerRefused):
            ledger.check_launch(ledger.read(self.path), {"disk_peak_bytes": 3_000_000_000})

    def test_existing_ledger_not_overwritten(self):
        with self.assertRaises(ledger.LedgerRefused):
            ledger.create(self.path, stage="A", envelope=ENVELOPE_A, authorization="again")


class ContinuationTests(unittest.TestCase):
    """「续做信封落实」§5：后继账本承接非磁盘已用量、旧账字节不变、续做磁盘维独立且不补 0、UNKNOWN/越界拒启。"""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.source = self.root / "ledger-A.json"
        ledger.create(self.source, stage="A", envelope={"candidates": 3, "yolo_loads": 14, "wall_s": 7200,
                                                        "disk_peak_bytes": 2_000_000_000}, authorization="A")
        ledger.record(self.source, "candidates", 2, note="c1+c2")
        ledger.record(self.source, "yolo_loads", 3, note="loads (estimate label kept)")
        ledger.record(self.source, "wall_s", interval=(100.0, 200.0), note="i1 estimate")
        ledger.record(self.source, "wall_s", interval=(150.0, 400.0), note="i2")
        with self.assertRaises(ledger.LedgerUnknown):
            ledger.record(self.source, "disk_peak_bytes", note="unknowable", unknown=True)
        self.source_bytes = self.source.read_bytes()
        self.path = self.root / "ledger-A-continuation.json"

    def _create(self, initial=123_456):
        return ledger.create_continuation(self.path, source=self.source, authorization="A+REBASE+MUTEX",
                                          disk_limit=3_000_000_000, initial_disk_u=initial, source_note="hist UNKNOWN")

    def test_carry_over_counts_intervals_and_source_bytes_unchanged(self):
        doc = self._create()
        self.assertEqual(doc["used"]["candidates"], 2)
        self.assertEqual(doc["used"]["yolo_loads"], 3)
        self.assertEqual(doc["used"]["wall_s"], 300.0)
        self.assertEqual(doc["intervals"]["wall_s"], [[100.0, 200.0], [150.0, 400.0]])
        self.assertEqual(doc["used"]["disk_peak_bytes"], 123_456)
        self.assertEqual(doc["source"]["used"]["disk_peak_bytes"], ledger.UNKNOWN)
        self.assertEqual(len(doc["source"]["carried_entries"]), 4)
        self.assertEqual(self.source.read_bytes(), self.source_bytes)
        self.assertEqual(ledger.problems(doc), [])
        ledger.check_launch(doc, {"candidates": 1, "yolo_loads": 11})
        with self.assertRaisesRegex(ledger.LedgerRefused, "S-BUDGET"):
            ledger.check_launch(doc, {"candidates": 2})

    def test_repeat_create_refused_and_attempts_not_refunded(self):
        self._create()
        with self.assertRaises(ledger.LedgerRefused):
            self._create()
        ledger.record(self.path, "candidates", 1, note="candidate 3 (attempt)")
        ledger.record(self.path, "wall_s", interval=(1000.0, 1010.0), note="new")
        doc = ledger.read(self.path)
        self.assertEqual(doc["used"]["candidates"], 3)
        self.assertEqual(doc["used"]["wall_s"], 310.0)
        with self.assertRaisesRegex(ledger.LedgerRefused, "S-BUDGET"):
            ledger.check_launch(doc, {"candidates": 1})

    def test_disk_window_stop_line_reserve_and_unknown(self):
        doc = self._create(initial=1_000_000_000)
        self.assertGreater(ledger.check_disk_window(doc, 1_100_000_000, 500_000_000, 200_000_000), 0)
        with self.assertRaisesRegex(ledger.LedgerRefused, "S-DISK"):
            ledger.check_disk_window(doc, 2_600_000_000, 50_000_000, 50_000_000)
        with self.assertRaises(ledger.LedgerUnknown):
            ledger.check_disk_window(doc, None, 0, 0)
        with self.assertRaises(ledger.LedgerUnknown):
            ledger.check_disk_window(doc, 900_000_000, 0, 0)
        with self.assertRaises(ledger.LedgerUnknown):
            ledger.record(self.path, "disk_peak_bytes", note="meter lost", unknown=True)
        with self.assertRaises(ledger.LedgerUnknown):
            ledger.check_launch(ledger.read(self.path), {"candidates": 1})

    def test_corrupt_source_refuses_carry_over(self):
        self.source.write_text(self.source_bytes.decode("utf-8").replace('"stage": "A"', '"stage": "B"'), encoding="utf-8")
        with self.assertRaises(ledger.LedgerUnknown):
            self._create()
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
