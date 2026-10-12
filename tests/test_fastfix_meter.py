#!/usr/bin/env python3
"""P1-ENG-FASTFIX-001 AC-11（K2）：计量工具——停令延迟、只遍历声明根、采样起止、输出上限与截断、隔离。"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_fastfix import meter  # noqa: E402


class SlowWalker:
    """假遍历器：每根 15 万条路径、单次采样约 5 s（分块 sleep）；记录被遍历的根。"""

    def __init__(self, paths=150_000, seconds=5.0, chunks=200):
        self.paths, self.seconds, self.chunks = paths, seconds, chunks
        self.roots = []

    def __call__(self, root):
        self.roots.append(Path(root))
        per_chunk = self.paths // self.chunks
        for _ in range(self.chunks):
            time.sleep(self.seconds / self.chunks)
            for _ in range(per_chunk):
                yield 10


class MeterTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def rows(self, path):
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def test_stop_latency_during_a_long_sample_is_within_one_second(self):
        walker = SlowWalker()
        stop = self.root / "STOP"
        m = meter.Meter({"session": self.root / "s"}, self.root / "meter.jsonl", interval_s=30.0, stop_file=stop, walker=walker)
        result = {}
        thread = threading.Thread(target=lambda: result.update(m.run()))
        thread.start()
        time.sleep(1.0)  # 采样进行中
        issued = time.monotonic()
        stop.write_text("stop\n", encoding="utf-8")
        thread.join(timeout=5.0)
        finished = time.monotonic()
        self.assertFalse(thread.is_alive())
        self.assertLessEqual(finished - issued, 1.0)
        self.assertEqual(result["reason"], "stop_file")
        self.assertEqual(m.samples, 0)  # 被打断的采样不写半截读数
        self.assertLessEqual(m.stop_tick_s, 0.5)

    def test_walks_only_declared_roots_and_records_start_end(self):
        walker = SlowWalker(paths=1000, seconds=0.05, chunks=10)
        stop = self.root / "STOP"
        roots = {"session": self.root / "s", "frames": self.root / "f"}
        m = meter.Meter(roots, self.root / "meter.jsonl", interval_s=0.1, stop_file=stop, walker=walker)
        thread = threading.Thread(target=m.run)
        thread.start()
        time.sleep(0.6)
        stop.write_text("stop\n", encoding="utf-8")
        thread.join(timeout=5.0)
        self.assertEqual(set(walker.roots), set(roots.values()))
        samples = [r for r in self.rows(self.root / "meter.jsonl") if r["kind"] == "sample"]
        self.assertGreaterEqual(len(samples), 2)
        for sample in samples:
            for key in ("start_monotonic_s", "end_monotonic_s", "start_unix_s", "end_unix_s"):
                self.assertIn(key, sample)
            self.assertLessEqual(sample["start_monotonic_s"], sample["end_monotonic_s"])
            self.assertEqual(set(sample["roots"]), {"session", "frames"})
            self.assertEqual(sample["total_bytes"], 2 * 1000 * 10)

    def test_output_cap_truncates_and_stops_monitoring(self):
        walker = SlowWalker(paths=10, seconds=0.0, chunks=1)
        alert = self.root / "ALERT"
        m = meter.Meter({"a": self.root / "a"}, self.root / "meter.jsonl", interval_s=0.0, walker=walker, max_output_bytes=4000,
                        alert_file=alert)
        thread = threading.Thread(target=m.run)
        thread.start()
        thread.join(timeout=5.0)
        self.assertFalse(thread.is_alive())
        rows = self.rows(self.root / "meter.jsonl")
        self.assertEqual([r for r in rows if r["kind"] == "meter_truncated"].__len__(), 1)
        self.assertEqual(rows[-1]["reason"], "meter_truncated")
        self.assertLessEqual((self.root / "meter.jsonl").stat().st_size, 4000)
        self.assertTrue(alert.is_file())

    def test_disk_threshold_raises_stop_condition(self):
        sizes = iter([[100], [100 + 950]])

        def walker(root):
            yield from next(sizes)

        m = meter.Meter({"a": self.root / "a"}, self.root / "meter.jsonl", interval_s=0.01, walker=walker,
                        disk_limit_bytes=1000, disk_stop_fraction=0.9, alert_file=self.root / "ALERT")
        summary = m.run()
        self.assertEqual(summary["reason"], "S-DISK")
        condition = [r for r in self.rows(self.root / "meter.jsonl") if r["kind"] == "stop_condition"][0]
        self.assertEqual((condition["code"], condition["new_bytes"]), ("S-DISK", 950))

    def test_real_walker_lstat_only_and_skips_missing_root(self):
        (self.root / "d" / "sub").mkdir(parents=True)
        (self.root / "d" / "x.bin").write_bytes(b"12345")
        (self.root / "d" / "sub" / "y.bin").write_bytes(b"123")
        (self.root / "d" / "link").symlink_to(self.root / "d" / "x.bin")
        self.assertEqual(sorted(meter.walk_sizes(self.root / "d")), [3, 5])
        self.assertEqual(list(meter.walk_sizes(self.root / "missing")), [])

    # --- C1-4（AC-19、首次接受释义 5–6）：不可核读与采样/输出故障可见 UNKNOWN 并停令，不写成 0 或存活计量 ----------

    def test_unreadable_directory_is_unknown_not_zero(self):
        locked = self.root / "d" / "locked"
        locked.mkdir(parents=True)
        (locked / "x.bin").write_bytes(b"12345")
        locked.chmod(0)
        self.addCleanup(locked.chmod, 0o755)
        with self.assertRaises(meter.MeterUnknown):
            list(meter.walk_sizes(self.root / "d"))
        m = meter.Meter({"d": self.root / "d"}, self.root / "meter.jsonl", interval_s=0.01, alert_file=self.root / "ALERT")
        summary = m.run()
        self.assertEqual(summary["reason"], "S-UNKNOWN")
        self.assertIn("unreadable", summary["unknown"])
        rows = self.rows(self.root / "meter.jsonl")
        self.assertFalse([r for r in rows if r["kind"] == "sample"])
        self.assertEqual([r["code"] for r in rows if r["kind"] == "stop_condition"], ["S-UNKNOWN"])
        self.assertTrue((self.root / "ALERT").is_file())

    def test_unreadable_entry_oserror_is_unknown(self):
        def walker(root):
            yield 10
            raise meter.MeterUnknown("unreadable entry x: OSError(5)")

        summary = meter.Meter({"a": self.root / "a"}, self.root / "meter.jsonl", interval_s=0.01, walker=walker).run()
        self.assertEqual(summary["reason"], "S-UNKNOWN")

    def test_unexpected_sampler_exception_stops_with_unknown(self):
        def walker(root):
            raise RuntimeError("boom")
            yield  # pragma: no cover

        started = time.monotonic()
        summary = meter.Meter({"a": self.root / "a"}, self.root / "meter.jsonl", interval_s=0.01, walker=walker).run()
        self.assertLess(time.monotonic() - started, 2.0)
        self.assertEqual(summary["reason"], "S-UNKNOWN")
        self.assertIn("sampler_failed:RuntimeError", summary["unknown"])

    def test_sampler_thread_lost_is_detected_by_stop_checker(self):
        m = meter.Meter({"a": self.root / "a"}, self.root / "meter.jsonl", interval_s=0.01, walker=lambda root: iter([1]))
        m._sampler = lambda: None  # noqa: SLF001 — 模拟采样线程无停令退出（失联）
        started = time.monotonic()
        summary = m.run()
        self.assertLessEqual(time.monotonic() - started, 1.0)
        self.assertEqual(summary["reason"], "S-UNKNOWN")
        self.assertEqual(summary["unknown"], "sampler_thread_lost")

    def test_output_write_failure_is_unknown(self):
        out_dir = self.root / "out"
        out_dir.mkdir()
        m = meter.Meter({"a": self.root / "a"}, out_dir / "meter.jsonl", interval_s=0.01, walker=lambda root: iter([1]))
        out_dir.chmod(0o500)
        self.addCleanup(out_dir.chmod, 0o755)
        summary = m.run()
        self.assertEqual(summary["reason"], "S-UNKNOWN")
        self.assertIn("output_write_failed", summary["unknown"])

    def test_no_controller_import_and_no_truth(self):
        source = (PROJECT_ROOT / "tools" / "eng_fastfix" / "meter.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        modules = [n.module if isinstance(n, ast.ImportFrom) else a.name for n in ast.walk(tree)
                   if isinstance(n, (ast.Import, ast.ImportFrom)) for a in (n.names if isinstance(n, ast.Import) else [n])]
        self.assertFalse([m for m in modules if m and ("controller" in m or "score" in m or "eng_capture" in m)])
        for token in ("m3_body_truth", "truth_box", "CoverageEvaluator"):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
