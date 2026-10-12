#!/usr/bin/env python3
"""P1-ENG-CAPTURE-001 AC-16（K4）：真值隔离（静态）与禁改路径 diff 为空（相对本提案 ACCEPTED 裁定提交，运行时由 git 解析）。"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_capture.common import accepted_base_commit  # noqa: E402

TRUTH_TOKENS = ("m3_body_truth", "truth_box", "truth_center", "target_world_x_m", "target_world_z_m", "body_world_", "geometrically_visible",
                "CoverageEvaluator", "visible_sample_fraction")
SCORING_FILES = ("tools/eng_capture/replay.py", "tools/eng_capture/analyze_play.py", "tools/eng_capture/formal_run.py")


def code_strings(tree: ast.AST) -> list[tuple[ast.AST, str]]:
    """模块内全部字符串常量与名字（去掉模块/类/函数 docstring）。"""
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                docstrings.add(id(first.value))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            out.append((node, node.value))
        elif isinstance(node, ast.Name):
            out.append((node, node.id))
        elif isinstance(node, ast.Attribute):
            out.append((node, node.attr))
    return out


def enclosing_functions(tree: ast.AST) -> dict[int, str]:
    owner: dict[int, str] = {}
    for function in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        for node in ast.walk(function):
            owner.setdefault(id(node), function.name)
    for function in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        for node in ast.walk(function):
            if function.name.startswith("score_"):
                owner[id(node)] = function.name
    return owner


class TruthIsolationTests(unittest.TestCase):
    def test_controller_and_click_page_never_read_truth(self):
        files = sorted((PROJECT_ROOT / "controller").glob("*.py")) + [PROJECT_ROOT / "tools" / "eng_capture" / "click_web.py"]
        offenders = []
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for _node, text in code_strings(tree):
                if any(token in text for token in TRUTH_TOKENS):
                    offenders.append((path.name, text[:60]))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module = node.module if isinstance(node, ast.ImportFrom) else ",".join(a.name for a in node.names)
                    if module and ("eng_capture.replay" in module or "analyze_play" in module or "formal_run" in module or module.startswith("tools.eng_loop2.analyze")):
                        offenders.append((path.name, module))
        self.assertEqual(offenders, [])

    def test_truth_only_inside_score_functions(self):
        offenders = []
        for relative in SCORING_FILES:
            tree = ast.parse((PROJECT_ROOT / relative).read_text(encoding="utf-8"))
            owner = enclosing_functions(tree)
            for node, text in code_strings(tree):
                if any(token in text for token in TRUTH_TOKENS) and not owner.get(id(node), "").startswith("score_"):
                    offenders.append((relative, owner.get(id(node)), text[:60]))
        self.assertEqual(offenders, [])


class SelectionInputIsolationTests(unittest.TestCase):
    """AC-28 / IR-7：真值不得生成送入两臂的选择输入（点击点、轨迹键、修复候选、KF 输入）。

    静态部分：正式回放执行体里一切 `click`/`clicks` 赋值的右值不引用真值变量或 `score_` 函数，且已无真值→点击函数；
    动态部分（真值改变不改变两臂选择输入、两臂同点）见 `tests/test_capture_replay.py::RollSelectionInputTests`。"""

    def test_click_assignments_never_read_truth(self):
        tree = ast.parse((PROJECT_ROOT / "tools" / "eng_capture" / "formal_run.py").read_text(encoding="utf-8"))
        names = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertNotIn("score_click_point", names)
        offenders = []
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Assign):
                targets = [t for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                targets = [node.target]
            if not any(t.id in {"click", "clicks", "roll_clicks"} for t in targets) or node.value is None:
                continue
            for inner in ast.walk(node.value):
                text = inner.id if isinstance(inner, ast.Name) else inner.attr if isinstance(inner, ast.Attribute) else None
                if text and ("truth" in text or text.startswith("score_")):
                    offenders.append((node.lineno, text))
        self.assertEqual(offenders, [])

    def test_roll_sequence_click_comes_only_from_its_parameter(self):
        tree = ast.parse((PROJECT_ROOT / "tools" / "eng_capture" / "formal_run.py").read_text(encoding="utf-8"))
        function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "roll_sequence")
        self.assertIn("click", [a.arg for a in function.args.args])
        for call in [n for n in ast.walk(function) if isinstance(n, ast.Call)]:
            for keyword in call.keywords:
                if keyword.arg == "clicks":
                    self.assertEqual(ast.unparse(keyword.value), "clicks")


def _git(*args):
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)


class FrozenPathTests(unittest.TestCase):
    def setUp(self):
        self.base = accepted_base_commit()
        if self.base is None:
            self.skipTest("git history unavailable")

    def test_forbidden_paths_have_no_diff(self):
        paths = ["Assets", "controller/scenario_tether.py", "docs/proposals/P1-ENG-LOOP-002-closed-loop-four-numbers.md"]
        self.assertEqual(_git("diff", "--name-only", self.base, "--", *paths).stdout.strip(), "")
        changed = _git("diff", "--name-only", self.base).stdout.split() + _git("ls-files", "--others", "--exclude-standard").stdout.split()
        self.assertEqual([p for p in changed if p.endswith(".unity") or p.startswith("config/scenario.")], [])
        eng_loop2 = [p for p in changed if p.startswith("tools/eng_loop2/")]
        self.assertEqual(eng_loop2, [p for p in eng_loop2 if p == "tools/eng_loop2/operator_web.py"])

    def test_candidates_backend_and_source_validation_unchanged(self):
        base_source = _git("show", f"{self.base}:controller/language_loop.py").stdout
        current = (PROJECT_ROOT / "controller" / "language_loop.py").read_text(encoding="utf-8")

        def segment(text, name):
            tree = ast.parse(text)
            node = next(n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name == name)
            return ast.get_source_segment(text, node)

        for name in ("CandidatesBackend", "_validate_candidates_source", "LanguageWorker"):
            self.assertEqual(segment(current, name), segment(base_source, name), name)



# --- P1-ENG-FASTFIX-001 AC-12（K4）：评分入口隔离与禁改路径（相对本项 ACCEPTED 裁定提交） -----------------------------

from tools.eng_fastfix import common as fastfix_common  # noqa: E402

FASTFIX_RUNTIME_FILES = ("tools/eng_fastfix/replay.py", "tools/eng_fastfix/meter.py", "tools/eng_fastfix/ledger.py",
                         "tools/eng_fastfix/common.py", "tools/eng_fastfix/__init__.py",
                         "tools/eng_fastfix/window_meter.py")  # R1 N-2：窗口计量器同受静态导入图/真值 token 检查
FASTFIX_ALLOWED_CHANGES = {
    "controller/gated_publisher.py", "controller/track_loop.py", "controller/language_loop.py", "controller/target_manager.py",
    "controller/language_bridge.py", "controller/resident_core.py", "config/p1-eng-fastfix-001.json",
}
_OPENED: list[str] = []
_AUDIT = {"on": False}


def _audit(event, args):  # noqa: ANN001
    if _AUDIT["on"] and event == "open" and args and isinstance(args[0], (str, bytes, Path)):
        _OPENED.append(str(args[0]))


sys.addaudithook(_audit)


class FastfixTruthIsolationTests(unittest.TestCase):
    def test_runtime_entries_never_import_score_or_name_truth(self):
        files = sorted((PROJECT_ROOT / "controller").glob("*.py")) + [PROJECT_ROOT / f for f in FASTFIX_RUNTIME_FILES]
        score_tree = ast.parse((PROJECT_ROOT / "tools" / "eng_fastfix" / "score.py").read_text(encoding="utf-8"))
        score_names = {n.name for n in score_tree.body if isinstance(n, ast.FunctionDef)}
        self.assertTrue(score_names and all(name.startswith("score_") or name == "main" for name in score_names))
        offenders = []
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            runtime_tool = "eng_fastfix" in str(path)
            for node, text in code_strings(tree):
                if (any(token in text for token in TRUTH_TOKENS) or (text in score_names and text != "main")
                        or (runtime_tool and text.startswith("score_"))):
                    offenders.append((path.name, text[:60]))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    names = [a.name for a in node.names]
                    if node.module.endswith("eng_fastfix.score") or (node.module.endswith("eng_fastfix") and "score" in names):
                        offenders.append((path.name, node.module))
                if isinstance(node, ast.Import) and any(a.name.endswith("eng_fastfix.score") for a in node.names):
                    offenders.append((path.name, "import score"))
        self.assertEqual(offenders, [])

    def test_truth_only_inside_score_functions(self):
        tree = ast.parse((PROJECT_ROOT / "tools" / "eng_fastfix" / "score.py").read_text(encoding="utf-8"))
        owner = enclosing_functions(tree)
        offenders = [(owner.get(id(node)), text[:60]) for node, text in code_strings(tree)
                     if any(token in text for token in TRUTH_TOKENS) and not owner.get(id(node), "").startswith("score_")]
        self.assertEqual(offenders, [])

    def test_poisoned_truth_identical_runtime_bytes_and_truth_never_opened(self):
        """动态：同一回放与捕获会话在旁置真值为原样/毒化副本时运行时产物逐字节相同；打开审计不含真值路径。"""
        import importlib.util  # noqa: PLC0415

        sys.path.insert(0, str(PROJECT_ROOT / "tests"))
        try:
            spec = importlib.util.spec_from_file_location("fx_replay_fixture", PROJECT_ROOT / "tests" / "test_fastfix_replay.py")
            fixture = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fixture)  # type: ignore[union-attr]
        finally:
            sys.path.remove(str(PROJECT_ROOT / "tests"))
        if not fixture.library_ready():
            self.skipTest("pinned library or admitted frames unavailable")
        from tools.eng_fastfix import replay  # noqa: PLC0415

        truth_name = "m3_body_" + "truth.jsonl"
        outputs = []
        with tempfile.TemporaryDirectory() as directory:
            for variant in ("original", "poisoned"):
                root = Path(directory) / variant
                frames_dir = root / "play" / "diag" / "frames"
                frames_dir.mkdir(parents=True)
                for frame_id in fixture.FRAME_RANGE:
                    for suffix in (".jpg", ".json"):
                        name = f"frame_{frame_id:010d}{suffix}"
                        shutil.copy2(fixture.ADMITTED_FRAMES / name, frames_dir / name)
                truth_source = fastfix_common.ADMITTED_ROOT / "play" / "diag-loop2-214005" / truth_name
                truth_target = root / "play" / "diag" / truth_name
                if variant == "original" and truth_source.is_file():
                    shutil.copy2(truth_source, truth_target)
                else:
                    truth_target.write_text('{"frame_id": 0, "poison": true}\n', encoding="utf-8")
                _OPENED.clear()
                _AUDIT["on"] = True
                try:
                    frames, factory, _wrapped = fixture.build_fixture(frames_dir)
                    report = replay.run_ac7(frames, {"click": fixture.CLICK, "injection_rule": fixture.RULE}, factory)
                finally:
                    _AUDIT["on"] = False
                self.assertFalse([p for p in _OPENED if truth_name in p], variant)
                outputs.append(json.dumps(report, sort_keys=True))
        self.assertEqual(outputs[0], outputs[1])

    def test_capture_session_never_opens_truth_beside_runtime(self):
        sys.path.insert(0, str(PROJECT_ROOT / "tests"))
        try:
            import test_capture_session as session_tests  # noqa: PLC0415
        finally:
            sys.path.remove(str(PROJECT_ROOT / "tests"))
        truth_name = "m3_body_" + "truth.jsonl"
        harness = session_tests.fx_harness(self)
        (harness.runtime / truth_name).write_text('{"frame_id": 0}\n', encoding="utf-8")
        _OPENED.clear()
        _AUDIT["on"] = True
        try:
            harness.decode.delays[harness.publisher.next_frame_id] = 0.5
            harness.publish(3)
        finally:
            _AUDIT["on"] = False
        self.assertTrue(_OPENED)
        self.assertFalse([p for p in _OPENED if truth_name in p])


class FastfixFrozenPathTests(unittest.TestCase):
    def setUp(self):
        self.base = fastfix_common.accepted_base_commit()
        if self.base is None:
            self.skipTest("git history unavailable")

    def test_forbidden_paths_have_no_diff(self):
        paths = ["Assets", "config/det-assoc-v1.models.json", "docs/evidence/P1-ENG-FAST-002-freeze.json",
                 "config/p1-eng-capture-001.json", "controller/det_assoc_tracker.py", "controller/scenario_tether.py",
                 "tools/eng_loop2", "tools/eng_capture"]
        self.assertEqual(_git("diff", "--name-only", self.base, "--", *paths).stdout.strip(), "")
        changed = fastfix_common.changed_paths() or []
        self.assertEqual([p for p in changed if p.endswith(".unity") or p.startswith("config/scenario.")], [])

    def test_changed_files_inside_closed_set(self):
        """本项改动 ⊆ §2.1 闭集：运行时代码/配置/工具路径（`controller/`、`config/`、`tools/`、`Assets/`）里相对接受基线的改动只能是
        闭集文件与 `tools/eng_fastfix/`；用户授权协调批次的工作流基础设施（`tools/check_*.py`、`tools/githooks/`）不属本项改动、不计。"""
        changed = fastfix_common.changed_paths() or []
        runtime_paths = [p for p in changed if p.startswith(("controller/", "config/", "tools/", "Assets/"))]
        infrastructure = [p for p in runtime_paths if p.startswith("tools/githooks/")
                          or (p.startswith("tools/check_") and p.endswith(".py"))]
        outside = [p for p in runtime_paths if p not in infrastructure
                   and not (p in FASTFIX_ALLOWED_CHANGES or p.startswith("tools/eng_fastfix/"))]
        self.assertEqual(outside, [])

    def test_language_worker_and_candidates_backend_unchanged(self):
        base_source = _git("show", f"{self.base}:controller/language_loop.py").stdout
        current = (PROJECT_ROOT / "controller" / "language_loop.py").read_text(encoding="utf-8")

        def segment(text, name):
            tree = ast.parse(text)
            node = next(n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name == name)
            return ast.get_source_segment(text, node)

        for name in ("CandidatesBackend", "_validate_candidates_source", "LanguageWorker"):
            self.assertEqual(segment(current, name), segment(base_source, name), name)


if __name__ == "__main__":
    unittest.main()
