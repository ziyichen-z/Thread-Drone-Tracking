"""COORD-016 §4 A3 / BC-5：具名路由检查 tools/check_route_text.py 的反例。"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import check_route_text as crt

TOOL_PATH = Path(crt.__file__).resolve()
PREFIX = "COORD-016 协调落地"


def git(args, cwd):
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


class RouteTextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        git(["init", "-q"], self.root)
        # 基线：甲句、旧句、乙句（乙句跨行，检查按去换行归一化比对）。
        self.write("docs/a.md", "# A\n\n甲句不变。旧句。乙句\n  跨行不变。\n")
        self.write("docs/b.md", "# B\n\n丙句不变。\n")
        self.commit("基线提交")
        self.base = git(["rev-parse", "HEAD"], self.root)
        self.write("docs/a.md", "# A\n\n甲句不变。新句（例外 MARK）。乙句\n  跨行不变。\n")
        self.commit(f"{PREFIX}：文档替换句")
        self.first = git(["rev-parse", "HEAD"], self.root)
        self.write("docs/b.md", "# B\n\n丙句不变。\n\n工具提交附注。\n")
        self.commit(f"{PREFIX}（工具与测试）")
        self.spec_path = self.root / "spec.json"
        self.spec = {
            "work_id": "COORD-016",
            "baseline_grep": f"^{PREFIX}",
            "expected": [
                {"id": "E1", "file": "docs/a.md", "text": "新句（例外 MARK）。", "count": 1},
            ],
            "closure_markers": [
                {"marker": "MARK", "files": ["docs/a.md", "docs/b.md"]},
            ],
            "unchanged": [
                {"id": "U1", "file": "docs/a.md", "text": "甲句不变。"},
                {"id": "U2", "file": "docs/a.md", "text": "乙句跨行不变。"},
                {"id": "U3", "file": "docs/b.md", "text": "丙句不变。"},
            ],
        }
        self.save_spec()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, message):
        git(["add", "-A"], self.root)
        git(["commit", "-q", "-m", message], self.root)

    def save_spec(self):
        self.spec_path.write_text(json.dumps(self.spec, ensure_ascii=False), encoding="utf-8")

    def run_cli(self):
        return subprocess.run(
            [sys.executable, str(TOOL_PATH), "--spec", str(self.spec_path), "--root", str(self.root)],
            capture_output=True, text=True, check=False)

    def test_all_positions_pass(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(self.base, result.stdout)

    def test_baseline_is_first_prefixed_commit_parent(self):
        # BC-5：基线 = 首个「COORD-016 协调落地」提交的首父，不是最后一个同前缀提交的首父。
        self.assertEqual(crt.resolve_baseline(self.root, f"^{PREFIX}"), self.base)
        self.assertNotEqual(crt.resolve_baseline(self.root, f"^{PREFIX}"), self.first)

    def test_missing_expected_sentence_fails(self):
        self.write("docs/a.md", "# A\n\n甲句不变。乙句\n  跨行不变。\n")
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("E1", result.stdout)

    def test_duplicate_expected_sentence_fails(self):
        self.write("docs/a.md",
                   "# A\n\n甲句不变。新句（例外 MARK）。乙句\n  跨行不变。新句（例外 MARK）。\n")
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("E1", result.stdout)

    def test_changed_unchanged_sentence_fails(self):
        self.write("docs/a.md", "# A\n\n甲句改动了。新句（例外 MARK）。乙句\n  跨行不变。\n")
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("U1", result.stdout)

    def test_rewritten_in_place_but_copied_elsewhere_fails(self):
        # C1-1：原位置改写、别处补旧句——全文计数不变，但原位置已不逐字相同 → 失败。
        self.write("docs/a.md",
                   "# A\n\n甲句改动了。新句（例外 MARK）。乙句\n  跨行不变。\n\n## 附\n\n补一句。\n\n甲句不变。\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn("FAIL U1", result.stdout)
        self.assertIn("PASS U2", result.stdout)

    def test_cross_line_sentence_rewritten_in_place_but_copied_elsewhere_fails(self):
        # C1-1 同类：跨行不变句在原位被改写、另起段落补回旧句 → 失败。
        self.write("docs/a.md",
                   "# A\n\n甲句不变。新句（例外 MARK）。乙句\n  跨行改了。\n\n## 附\n\n乙句跨行不变。\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn("FAIL U2", result.stdout)
        self.assertIn("PASS U1", result.stdout)

    def test_deleted_unchanged_sentence_fails(self):
        self.write("docs/b.md", "# B\n\n工具提交附注。\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn("FAIL U3", result.stdout)

    def test_copied_unchanged_sentence_fails(self):
        self.write("docs/b.md", "# B\n\n丙句不变。\n\n工具提交附注。丙句不变。\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn("FAIL U3", result.stdout)

    def test_unchanged_sentence_survives_edits_around_it(self):
        # 正例：原位句逐字保留，前后插删其他内容、改动同行邻句、整体重缩进折行均不误报。
        self.write("docs/a.md",
                   "# A\n\n前置新段。\n\n甲句不变。新句（例外 MARK）。又一句。乙句\n    跨行不变。\n")
        self.write("docs/b.md", "# B\n\n新增首段。\n\n丙句不变。\n\n工具提交附注。\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, msg=result.stdout)

    def test_unlisted_marker_occurrence_fails(self):
        # 规格闭集：标记词在被扫文件中出现而规格未列（漏列）→ 失败。
        self.write("docs/b.md", "# B\n\n丙句不变。\n\n另一处未列入规格的 MARK。\n")
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MARK", result.stdout)

    def test_unchanged_text_absent_from_baseline_fails(self):
        self.spec["unchanged"].append({"id": "U4", "file": "docs/a.md", "text": "基线里没有的句子。"})
        self.save_spec()
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("U4", result.stdout)

    def test_no_prefixed_commit_is_error(self):
        self.spec["baseline_grep"] = "^不存在的前缀"
        self.save_spec()
        result = self.run_cli()
        self.assertEqual(result.returncode, 2, msg=result.stdout)


if __name__ == "__main__":
    unittest.main()
