#!/usr/bin/env python3
"""P1-ENG-ACQ-001 AC-9（含修订 1）：零消耗与隔离守卫。

- 受保护写入：数据根与仓库 `runtime/` 结构性拒绝；
- 静态检查：`controller/` 任何模块不导入 `tools.*`、索引/真值模块或 C2 预测文件；
- 账本：零维度全 0，回放次数与墙钟不超信封；越界时守卫抛 `EnvelopeExhausted`；
- 清理：`runtime/` 零写入断言只具名剔除 AC-16 修订 1 准许的 `hold-diag-loopb-*` 删除。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_acq import common  # noqa: E402

FORBIDDEN_IN_CONTROLLER = ("catalog-index", "catalog_index", "eval-adapter", "frames_catalog", "eng-fast/", "dist_data")
#: 真值/索引/评分来源包：控制器任何模块都不得导入（既有 `tools.eng_sft`（VLM 解析/提示）与 `tools.language_serve`
#: 不是真值来源，按既有复核结论保留，不在本检查范围内）。
TRUTH_PACKAGES = ("tools.eng_acq", "tools.eng_fast", "tools.eng_det", "tools.dist_data", "tools.eng_asset")


class ProtectedWrites(unittest.TestCase):
    def test_runtime_and_data_root_refused(self):
        for root in common.PROTECTED_ROOTS:
            with self.assertRaises(PermissionError):
                common.refuse_protected(root / "x.json")
            with self.assertRaises(PermissionError):
                common.atomic_write_bytes(root / "sub" / "y.json", b"{}")
        common.refuse_protected(common.OUT_DIR / "ok.json")
        common.refuse_protected(common.EVIDENCE_DIR / "ok.json")


class ControllerIsolation(unittest.TestCase):
    def test_controller_imports_no_tools_or_truth(self):
        offenders = []
        for path in sorted((PROJECT_ROOT / "controller").glob("*.py")):
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    names = [node.module]
                offenders.extend(f"{path.name}:{name}" for name in names if any(name == p or name.startswith(p + ".") for p in TRUTH_PACKAGES))
                if isinstance(node, ast.ImportFrom) and node.module == "tools":
                    offenders.extend(f"{path.name}:tools.{alias.name}" for alias in node.names if f"tools.{alias.name}" in TRUTH_PACKAGES)
            if path.name in ("resident_core.py", "pose_gmc.py", "det_assoc_tracker.py"):
                offenders.extend(f"{path.name}:{token}" for token in FORBIDDEN_IN_CONTROLLER if token in source)
        self.assertEqual(offenders, [])


class Ledger(unittest.TestCase):
    def ledger_path(self, entries):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, dir=common.OUT_DIR if common.OUT_DIR.exists() else None)
        json.dump({"work_id": common.WORK_ID, "envelope": common.ENVELOPE, "entries": entries, "totals": {}}, handle)
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def test_guard_refuses_over_budget(self):
        path = self.ledger_path([{"kind": "sequence_replay", "sequence_replays": 39, "wall_s": 10.0, "status": "ok"}])
        common.require_budget(1, path)
        with self.assertRaises(common.EnvelopeExhausted):
            common.require_budget(2, path)
        path = self.ledger_path([{"kind": "e1_resolution", "sequence_replays": 0, "wall_s": 10800.0, "status": "ok"}])
        with self.assertRaises(common.EnvelopeExhausted):
            common.require_budget(0, path)

    def test_failed_runs_are_charged(self):
        path = self.ledger_path([])
        with self.assertRaises(RuntimeError):
            with common.charged("sequence_replay", "boom", sequence_replays=1, cmd="test", path=path):
                raise RuntimeError("fail")
        totals = common.totals(common.load_ledger(path))
        self.assertEqual((totals["sequence_replays"], totals["failed_entries"]), (1, 1))

    def test_committed_ledger_zero_dimensions_and_within_envelope(self):
        if not common.LEDGER_PATH.exists():
            self.skipTest("本项消耗账本尚未生成")
        ledger = common.load_ledger()
        totals = common.totals(ledger)
        for dimension in common.ENVELOPE["zero_dimensions"]:
            self.assertEqual(totals[dimension], 0, dimension)
        self.assertLessEqual(totals["sequence_replays"], common.ENVELOPE["sequence_replays_max"])
        self.assertLessEqual(totals["cpu_wall_s"], common.ENVELOPE["cpu_wall_s_max"])


class CleanupScope(unittest.TestCase):
    def test_only_hold_diag_loopb_is_deletable(self):
        from tools.eng_acq import cleanup  # noqa: PLC0415

        self.assertTrue(cleanup.deletable("runtime/hold-diag-loopb-6"))
        for path in ("runtime/frames", "runtime/tracking_observation.json", "runtime/hold-diag-loopb-6/../frames", "runtime/models/nanotrack-v2", "outputs/eng-loop"):
            self.assertFalse(cleanup.deletable(path), path)


if __name__ == "__main__":
    unittest.main()
