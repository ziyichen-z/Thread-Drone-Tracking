"""P1-ENG-CAPTURE-001 证据工具公用件：可派生标识运行时解析（不手写 SHA）、基线源导出、输出根与准入根。

- `accepted_base_commit()`：同名提案首次出现 `Status: ACCEPTED` 的提交（终局裁定提交），由 git 运行时解析。
- `play_code_commit()`：F18 记载的 10-08 Play 代码提交（从提案 F18 行运行时读取，不手抄）。
- `export_controller(commit, dest)`：把该提交的 `controller/` 导出为独立包目录（基线臂与兼容回归使用）。
- `accepted_base_literal(path, name)`：接受基线上某模块级字面量常量（闭集）的值，供「旧完整前缀逐位比较」（IR-3）。
"""

from __future__ import annotations

import ast
import io
from pathlib import Path
import re
import subprocess
import tarfile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROPOSAL = "docs/proposals/P1-ENG-CAPTURE-001-moving-target-capture-round1.md"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "eng-capture"
#: USER-4A 准入根（只限原始帧、位姿、真值；真值只进评分）。
ADMITTED_ROOT = PROJECT_ROOT / "outputs" / "eng-loop" / "P1-ENG-LOOP-002" / "diagnostics" / "20261008T213653Z"
ADMITTED_FRAMES = ADMITTED_ROOT / "play" / "diag-loop2-214005" / "frames"
ADMITTED_TRUTH = ADMITTED_ROOT / "play" / "diag-loop2-214005" / "m3_body_truth.jsonl"
ADMITTED_SUMS = ADMITTED_ROOT / "replay-transfer" / "SHA256SUMS"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)


def accepted_base_commit() -> str | None:
    """同名提案 `Status: ACCEPTED` 首次进入的提交（`git log -S` 最早一条）；git 不可用 → None。"""
    done = _git("log", "--format=%H", "--reverse", "-S", "Status: ACCEPTED", "--", PROPOSAL)
    if done.returncode != 0:
        return None
    lines = [line.strip() for line in done.stdout.splitlines() if line.strip()]
    return lines[0] if lines else None


def play_code_commit() -> str | None:
    """提案 F18 行记载的 10-08 Play 代码提交缩写（运行时从提案读取并经 git 展开为完整 SHA）。"""
    text = (PROJECT_ROOT / PROPOSAL).read_text(encoding="utf-8")
    match = re.search(r"\| F18 \| `git diff ([0-9a-f]{7,40}) HEAD -- controller/`", text)
    if match is None:
        return None
    done = _git("rev-parse", "--verify", f"{match.group(1)}^{{commit}}")
    return done.stdout.strip() if done.returncode == 0 else None


def controller_equivalent(left: str, right: str) -> bool:
    """两提交的 `controller/` 是否逐字节等价（F18 等价核验）。"""
    done = _git("diff", "--quiet", left, right, "--", "controller/")
    return done.returncode == 0


def export_controller(commit: str, destination: Path) -> Path:
    """把 `<commit>:controller/` 导出到 `destination`（作为独立包目录，例如 `.../controller_base`）。"""
    done = subprocess.run(["git", "archive", "--format=tar", commit, "controller"], cwd=PROJECT_ROOT, capture_output=True, check=True)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(done.stdout)) as archive:
        for member in archive.getmembers():
            if not member.name.startswith("controller/") or member.name.endswith("/") or "__pycache__" in member.name:
                continue
            target = destination / member.name[len("controller/"):]
            target.parent.mkdir(parents=True, exist_ok=True)
            handle = archive.extractfile(member)
            if handle is not None:
                target.write_bytes(handle.read())
    return destination


def accepted_base_literal(relative_path: str, name: str) -> object | None:
    """接受基线提交上 `relative_path` 的模块级常量 `name`（须为字面量，`ast.literal_eval`）；git 不可用 → None。"""
    base = accepted_base_commit()
    if base is None:
        return None
    shown = _git("show", f"{base}:{relative_path}")
    if shown.returncode != 0:
        return None
    for node in ast.parse(shown.stdout).body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(t, ast.Name) and t.id == name for t in targets) and node.value is not None:
            return ast.literal_eval(node.value)
    raise LookupError(f"{name} not found in {relative_path}@{base}")
