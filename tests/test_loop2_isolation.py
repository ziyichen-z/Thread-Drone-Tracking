"""P1-ENG-LOOP-002 AC-9：导入隔离（枚举闭集，AST）。

* `controller/` 对 `tools.*` 的导入只允许五项：冻结推理依赖 `tools.eng_sft.{parse, prompt_v2, train_lora}`、
  `serve` 子命令的 `tools.language_serve`，以及纯标准库部署摘要 `tools.eng_loop2.deploy_digest`。
* `controller/`、`tools/eng_loop2/llama_adapter.py`、`tools/language_serve.py`、`tools/eng_loop2/deploy_digest.py`
  不导入真值/评分闭集，源码不含 `m3_body_truth`/`CoverageEvaluator` 记号。
* `intent`（A4 意图标签）只出现在请求解析、回执日志与 CLI，不进任何 controller 决策函数。
既有 `test_eng_acq_guards.py::ControllerIsolation` 不改，与本文件并存。
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONTROLLER_TOOLS_ALLOWED = frozenset(
    {
        "tools.eng_sft.parse",
        "tools.eng_sft.prompt_v2",
        "tools.eng_sft.train_lora",
        "tools.language_serve",
        "tools.eng_loop2.deploy_digest",
    }
)
TRUTH_SCORING_PREFIXES = (
    "tools.eng_acq",
    "tools.eng_fast",
    "tools.eng_det",
    "tools.dist_data",
    "tools.eng_asset",
    "tools.analyze_m3_body",
    "tools.frame_follow_replay",
    "tools.eng_loop2.analyze_play",
)
TRUTH_TOKENS = ("m3_body_truth", "CoverageEvaluator")
DEPLOY_SIDE = (
    PROJECT_ROOT / "tools" / "eng_loop2" / "llama_adapter.py",
    PROJECT_ROOT / "tools" / "eng_loop2" / "deploy_digest.py",
    PROJECT_ROOT / "tools" / "language_serve.py",
)


def imported_modules(path: Path) -> set[str]:
    """文件里所有 import 语句（含函数内惰性导入）解析出的绝对模块名；`from a import b` 记为 `a.b`。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for alias in node.names:
                names.add(f"{node.module}.{alias.name}")
                names.add(node.module)
    return names


def controller_files() -> list[Path]:
    return sorted((PROJECT_ROOT / "controller").glob("*.py"))


class Loop2IsolationTests(unittest.TestCase):
    def test_controller_tools_imports_are_the_enumerated_closed_set(self) -> None:
        offending: dict[str, list[str]] = {}
        seen: set[str] = set()
        for path in controller_files():
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    statements = [({alias.name}, alias.name) for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    # `from tools.eng_sft import prompt_v2` 的目标是子模块；`from tools.eng_sft.parse import f` 的目标是模块本身。
                    statements = [({node.module, f"{node.module}.{alias.name}"}, f"{node.module}:{alias.name}") for alias in node.names]
                else:
                    continue
                for candidates, label in statements:
                    if not any(name == "tools" or name.startswith("tools.") for name in candidates):
                        continue
                    hit = candidates & CONTROLLER_TOOLS_ALLOWED
                    if hit:
                        seen.update(hit)
                    else:
                        offending.setdefault(path.name, []).append(label)
        self.assertEqual(offending, {})
        self.assertEqual(seen, CONTROLLER_TOOLS_ALLOWED)

    def test_controller_and_deploy_side_never_import_truth_or_scoring(self) -> None:
        for path in [*controller_files(), *DEPLOY_SIDE]:
            with self.subTest(path=path.name):
                for name in imported_modules(path):
                    self.assertFalse(
                        any(name == prefix or name.startswith(prefix + ".") for prefix in TRUTH_SCORING_PREFIXES),
                        f"{path.name} imports {name}",
                    )
                source = path.read_text(encoding="utf-8")
                for token in TRUTH_TOKENS:
                    self.assertNotIn(token, source)

    def test_intent_only_in_request_parsing_receipts_and_cli(self) -> None:
        path = PROJECT_ROOT / "controller" / "language_loop.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        allowed = {"designate_options", "_receipt", "send_request", "build_parser", "main"}
        found: set[str] = set()
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for node in ast.walk(function):
                mentions = (
                    (isinstance(node, ast.Name) and node.id == "intent")
                    or (isinstance(node, ast.arg) and node.arg == "intent")
                    or (isinstance(node, ast.Attribute) and node.attr == "intent")
                    or (isinstance(node, ast.Constant) and node.value in {"intent", "--intent"})
                )
                if mentions:
                    found.add(function.name)
        self.assertTrue(found)
        self.assertEqual(found - allowed, set())
        # 会话对象上不保存意图（只有回执日志里有）。
        source = path.read_text(encoding="utf-8")
        self.assertNotIn("self.intent", source)
        self.assertNotIn("_intent =", source.replace("_intent, _invalid", "").replace("_intent, invalid", ""))


# --- P1-ENG-LOOP-002 AC-9 修订 1（OpsK1K2K3K4）：在线操作工具与离线摘要的边界（只追加，既有断言不改） ---

ONLINE_OPS = (
    PROJECT_ROOT / "tools" / "eng_loop2" / "play_ops.py",
    PROJECT_ROOT / "tools" / "eng_loop2" / "operator_web.py",
)
OFFLINE_SUMMARY = PROJECT_ROOT / "tools" / "eng_loop2" / "summarize_ops.py"
#: 在线工具另不得导入离线摘要（其输出不回流）。
ONLINE_FORBIDDEN_IMPORTS = TRUTH_SCORING_PREFIXES + ("tools.eng_loop2.summarize_ops",)
#: 只读操作，用于证明归档函数只移动、不读取被移动文件。
READ_CALLS = frozenset({"open", "read_text", "read_bytes", "load", "loads", "read"})


def function_named(tree: ast.AST, name: str) -> ast.FunctionDef:
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)


def string_constants(node: ast.AST) -> list[str]:
    return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


class OpsIsolationTests(unittest.TestCase):
    def test_online_ops_tools_never_import_truth_scoring_geometry_or_summary(self) -> None:
        for path in ONLINE_OPS:
            with self.subTest(path=path.name):
                for name in imported_modules(path):
                    self.assertFalse(
                        any(name == prefix or name.startswith(prefix + ".") for prefix in ONLINE_FORBIDDEN_IMPORTS),
                        f"{path.name} imports {name}",
                    )
                self.assertNotIn("CoverageEvaluator", path.read_text(encoding="utf-8"))

    def test_operator_web_has_no_truth_scoring_or_geometry_strings(self) -> None:
        tree = ast.parse(ONLINE_OPS[1].read_text(encoding="utf-8"))
        text = "\n".join(string_constants(tree))
        for token in ("m3_body_truth", "analyze_play", "summarize_ops", "derive-bc", "geometry", "score"):
            self.assertNotIn(token, text)

    def test_truth_file_only_moved_by_archive_without_reading(self) -> None:
        tree = ast.parse(ONLINE_OPS[0].read_text(encoding="utf-8"))
        owners = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and any("m3_body_truth" in s for s in string_constants(node))
        }
        self.assertEqual(owners, {"archive_attempt"})
        archive = function_named(tree, "archive_attempt")
        calls = {
            (n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", None))
            for n in ast.walk(archive)
            if isinstance(n, ast.Call)
        }
        self.assertEqual(calls & READ_CALLS, set())

    def test_scoring_and_geometry_only_offline_outside_the_online_schedule(self) -> None:
        tree = ast.parse(ONLINE_OPS[0].read_text(encoding="utf-8"))
        owners: dict[str, set[str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for token in ("analyze_play", "summarize_ops"):
                    if any(token in s for s in string_constants(node)):
                        owners.setdefault(token, set()).add(node.name)
        # derive-bc 只在 Play 前离线冻结计划；离线摘要只在收尾后以独立进程调用（正式 stage_play；
        # IR-OPS-5 诊断 run_offline_summary，见下方 test_diagnostic_summary_only_after_closeout_without_scoring）。
        self.assertEqual(owners, {"analyze_play": {"freeze_plan"}, "summarize_ops": {"stage_play", "run_offline_summary"}})
        scheduler = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "PlanScheduler")
        text = "\n".join(string_constants(scheduler))
        for token in ("analyze_play", "summarize_ops", "m3_body_truth", "derive", "geometry", "score"):
            self.assertNotIn(token, text)

    def test_frozen_plan_carries_text_and_intent_only(self) -> None:
        tree = ast.parse(ONLINE_OPS[0].read_text(encoding="utf-8"))
        keys = next(
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "PLAN_STEP_KEYS" for t in node.targets)
        )
        names = set(string_constants(keys))
        self.assertEqual(
            names,
            {"step_id", "kind", "action", "instruction", "intent", "delay_s", "description", "observe_s", "follow_s", "release_after"},
        )

    def test_diagnostic_summary_only_after_closeout_without_scoring(self) -> None:
        """IR-OPS-5 §4.8：诊断只在收尾之后以独立进程 `summarize_ops --mode diagnostic` 摘要，不评分、不读真值。"""
        tree = ast.parse(ONLINE_OPS[0].read_text(encoding="utf-8"))
        run = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "DiagnosticRun")
        summary = next(n for n in run.body if isinstance(n, ast.FunctionDef) and n.name == "run_offline_summary")
        strings = string_constants(summary)
        self.assertIn("diagnostic", strings)
        self.assertNotIn("formal", strings)
        for token in ("analyze_play", "m3_body_truth", "score", "derive", "geometry"):
            self.assertFalse(any(token in text for text in string_constants(run)), token)
        execute = next(n for n in run.body if isinstance(n, ast.FunctionDef) and n.name == "execute")
        calls = [n.func.attr for n in ast.walk(execute) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and isinstance(n.func.value, ast.Name) and n.func.value.id == "self"]
        self.assertLess(calls.index("closeout"), calls.index("run_offline_summary"))

    def test_offline_summary_uses_the_original_scorer_only_as_a_separate_process(self) -> None:
        names = imported_modules(OFFLINE_SUMMARY)
        self.assertFalse(any(n.startswith("tools.eng_loop2.analyze_play") for n in names))
        self.assertIn("subprocess", names)
        self.assertIn("tools.eng_loop2.analyze_play", OFFLINE_SUMMARY.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
