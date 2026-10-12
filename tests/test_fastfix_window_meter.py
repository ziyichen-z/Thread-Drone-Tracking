#!/usr/bin/env python3
"""P1-ENG-FASTFIX-001「续做信封落实」§4：整窗计量 U(t)=C+E+R 的累计/去重/旗标规则（假读取器，零模型）。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_fastfix import window_meter as wm  # noqa: E402

T0 = {"claude_app_pid": 1, "coalition_ids": [10, 11],
      "raw": {"byteswritten": 100, "logical_immediate_writes": 0, "logical_deferred_writes": 200, "logical_metadata_writes": 50}}


class FakeReader:
    def __init__(self):
        self.claude = {f: 0 for f in wm.CRU_FIELDS}
        self.claude.update({"byteswritten": 100, "logical_deferred_writes": 200, "logical_metadata_writes": 50})
        self.ext = {f: 0 for f in wm.CRU_FIELDS}
        self.cid = {1: 10, 7: 20}
        self.life = 1000
        self.start = 5
        self.used = 10_000
        self.fail = None

    def coalition_of(self, pid):
        if self.fail == "coal":
            raise wm.MeterError("denied")
        return self.cid[pid]

    def coalition_usage(self, cid):
        return dict(self.claude if cid == 10 else self.ext)

    def pid_rusage(self, pid):
        return {"diskio_byteswritten": self.life, "logical_writes": 0, "proc_start_abstime": self.start}

    def container_used(self, path):
        return self.used


class WindowMeterTests(unittest.TestCase):
    def make(self, reader):
        return wm.WindowMeter(reader, T0, [7], "/", stop_at=2700, limit=3000)

    def test_cumulative_from_fixed_t0_sum_of_write_fields(self):
        r = FakeReader()
        m = self.make(r)
        self.assertEqual(m.sample()["C"], 0)
        r.claude["byteswritten"] += 30
        r.claude["logical_deferred_writes"] += 40
        r.claude["logical_invalidated_writes"] += 999  # 不扣减、不计入
        rec = m.sample()
        self.assertEqual(rec["C"], 70)
        self.assertEqual(rec["E"], 1000)  # 外部进程终身写量绝对值；外部联盟自首读起 0
        r.ext["logical_deferred_writes"] += 5
        self.assertEqual(m.sample()["E"], 1005)

    def test_container_peak_never_decreases_and_flags(self):
        r = FakeReader()
        m = self.make(r)
        m.sample()
        r.used += 500
        self.assertEqual(m.sample()["R"], 500)
        r.used -= 400  # 删除不返还
        rec = m.sample()
        self.assertEqual(rec["R"], 500)
        self.assertEqual(rec["U"], 0 + 1000 + 500)
        r.claude["byteswritten"] += 1300
        self.assertIn("STOP_DISK", m.sample()["flags"])
        r.claude["byteswritten"] += 300
        self.assertIn("STOP_BUDGET", m.sample()["flags"])

    def test_unknown_on_regression_coalition_change_identity_and_read_failure(self):
        for mutate in ("regress", "coalition", "identity", "fail"):
            r = FakeReader()
            m = self.make(r)
            m.sample()
            if mutate == "regress":
                r.claude["logical_deferred_writes"] -= 1
            elif mutate == "coalition":
                r.cid[1] = 99
            elif mutate == "identity":
                r.start = 6
            else:
                r.fail = "coal"
            rec = m.sample()
            self.assertIn("UNKNOWN", rec["flags"], mutate)
            self.assertIsNone(rec["U"], mutate)


class MultiCoalitionTests(unittest.TestCase):
    """B/C 操作单：阶段起点 `snapshot` 记多个具名执行者联盟（同联盟去重），U 的 C 为各联盟自起点累计之和。"""

    def test_snapshot_dedupes_and_sums_members(self):
        r = FakeReader()
        r.cid = {1: 10, 2: 10, 3: 30, 7: 20}
        usage = {10: dict(r.claude), 30: {f: 0 for f in wm.CRU_FIELDS}}
        r.coalition_usage = lambda cid: dict(usage[cid]) if cid in usage else dict(r.ext)
        t0 = wm.snapshot(r, [1, 2, 3])
        self.assertEqual([m["coalition_id"] for m in t0["coalitions"]], [10, 30])
        m = wm.WindowMeter(r, t0, [], "/", stop_at=2700, limit=3000)
        self.assertEqual(m.sample()["C"], 0)
        usage[10]["byteswritten"] += 7
        usage[30]["logical_metadata_writes"] += 5
        self.assertEqual(m.sample()["C"], 12)
        usage[30]["logical_metadata_writes"] -= 1
        self.assertIn("UNKNOWN", m.sample()["flags"])


if __name__ == "__main__":
    unittest.main()
