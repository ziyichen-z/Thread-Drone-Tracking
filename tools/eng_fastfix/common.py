"""P1-ENG-FASTFIX-001 证据工具公用件：可派生标识运行时解析（不手写 SHA）与路径常量。

- `accepted_base_commit()`：同名提案首次出现 `Status: ACCEPTED` 的提交（D2 接受裁定提交），由 git 运行时解析。
- `base_source(path)`：该提交上某文件的原文（AC-1/AC-10/AC-12 的「diff 为空」与「修改前逐值相同」对照）。
- `export_base_controller(dest)`：把该提交的 `controller/` 导出为独立包目录（修前红/行为对照用）。

本模块不导入 `controller`、不读真值。
"""

from __future__ import annotations

import io
from pathlib import Path
import subprocess
import tarfile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROPOSAL = "docs/proposals/P1-ENG-FASTFIX-001-publish-degrade-and-reacquire.md"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "eng-fastfix"
EVIDENCE_ROOT = PROJECT_ROOT / "docs" / "evidence"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)


def accepted_base_commit() -> str | None:
    """同名提案 `Status: ACCEPTED` 首次进入的提交（`git log -S` 最早一条）；git 不可用 → None。"""
    done = _git("log", "--format=%H", "--reverse", "-S", "Status: ACCEPTED", "--", PROPOSAL)
    if done.returncode != 0:
        return None
    lines = [line.strip() for line in done.stdout.splitlines() if line.strip()]
    return lines[0] if lines else None


def base_source(relative_path: str) -> str | None:
    """接受基线提交上 `relative_path` 的原文；git 不可用或文件不存在 → None。"""
    base = accepted_base_commit()
    if base is None:
        return None
    shown = _git("show", f"{base}:{relative_path}")
    return shown.stdout if shown.returncode == 0 else None


def changed_paths() -> list[str] | None:
    """相对接受基线的改动路径（已提交 + 工作树 + 未跟踪）；git 不可用 → None。"""
    base = accepted_base_commit()
    if base is None:
        return None
    committed = _git("diff", "--name-only", base).stdout.split()
    untracked = _git("ls-files", "--others", "--exclude-standard").stdout.split()
    return sorted(set(committed) | set(untracked))


def export_base_controller(destination: Path) -> Path:
    """把接受基线的 `controller/` 导出到 `destination`（独立包目录）。"""
    base = accepted_base_commit()
    if base is None:
        raise RuntimeError("git history unavailable")
    done = subprocess.run(["git", "archive", "--format=tar", base, "controller"], cwd=PROJECT_ROOT, capture_output=True, check=True)
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


#: USER-4A 准入原件（七题答复 SOURCE 限用途扩至本项 AC-7）：只列原始帧与清单；真值路径只在 `score.py`。
ADMITTED_ROOT = PROJECT_ROOT / "outputs" / "eng-loop" / "P1-ENG-LOOP-002" / "diagnostics" / "20261008T213653Z"
ADMITTED_FRAMES = ADMITTED_ROOT / "play" / "diag-loop2-214005" / "frames"
ADMITTED_SUMS = ADMITTED_ROOT / "replay-transfer" / "SHA256SUMS"
