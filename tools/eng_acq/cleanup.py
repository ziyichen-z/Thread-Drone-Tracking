"""H-5 清理承接（AC-16 修订 1、AC-9 修订 1；§7 (g) 用户答复：清单入证据后本地删除、5060 由用户自行删除）。

- 盘点（只读）：本地 `runtime/hold-diag-loopb-*`（LOOP-001 阶段 B 槽位隔离物，位于采集副本 = 数据根
  `~/TetheredDroneTracking-full/runtime/`；仓库主树 `runtime/` 下同名路径一并核查）、诊断 6 留在 `runtime/` 的
  桥文件与帧（只入清单、不删）、5060 F 盘 `repo-b`（远端，本项访问 0，大小 `UNKNOWN_UNVERIFIED`）。
- 删除：只对清单中 `deletable()` 为真的 `runtime/hold-diag-loopb-*` 目录执行；方式为移入当前用户废纸篓
  （`~/.Trash/`，可恢复），不做不可恢复的永久删除；永久清空由用户自行决定。其他路径一律不动。
"""

from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path
import re
import shutil
from typing import Any

from tools.eng_acq import common

HOLD_PATTERN = re.compile(r"^runtime/hold-diag-loopb-[A-Za-z0-9]+$")
SOURCE = "docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md（§2.3 槽位隔离逐次记录：各诊断发令前把上一轮残留移入 hold 目录，移动前后树摘要相同）；docs/parked-status.md「P1-ENG-LOOP-001 收口与 P1-ENG-ACQ-001 承接（2026-09-28）」第 4 条"
DIAG6_WINDOW = ("2026-09-23T18:00:00", "2026-09-23T23:59:59")


def deletable(relative: str) -> bool:
    """只有 `runtime/hold-diag-loopb-<名>` 顶层目录可删（AC-16 修订 1）；含 `..` 或其他路径一律否。"""
    normalized = os.path.normpath(relative).replace(os.sep, "/")
    return normalized == relative.rstrip("/") and bool(HOLD_PATTERN.match(normalized))


def _tree(path: Path) -> dict[str, Any]:
    files = [p for p in path.rglob("*") if p.is_file()]
    return {
        "size_bytes": sum(p.stat().st_size for p in files),
        "file_count": len(files),
        "top_level": sorted(p.name for p in path.iterdir()),
    }


def _mtime(path: Path) -> str:
    return _dt.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%S")


def inventory() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for label, root in (("data_root_capture_copy", common.DATA_ROOT), ("main_worktree", common.PROJECT_ROOT)):
        runtime = root / "runtime"
        found = sorted(runtime.glob("hold-diag-loopb-*")) if runtime.exists() else []
        if not found:
            entries.append({"location": label, "path": f"{common.rel(runtime)}/hold-diag-loopb-*", "present": False, "suggested_action": "NONE_ABSENT"})
        for path in found:
            relative = f"runtime/{path.name}"
            entries.append(
                {
                    "location": label,
                    "path": common.rel(path),
                    "relative": relative,
                    "present": True,
                    "kind": "directory",
                    **_tree(path),
                    "mtime_local": _mtime(path),
                    "source": SOURCE,
                    "retention_reason": "LOOP-001 阶段 B 诊断槽位隔离物；诊断 5/6 不进证据链（H-3）；原日志与预览另存 outputs/eng-loop/…/diagnostics/ 与 docs/unity-test-log.md 摘要；无保留义务",
                    "suggested_action": "DELETE_LOCAL（§7 (g) 用户答复；AC-16 修订 1）" if deletable(relative) else "KEEP",
                    "deletable": deletable(relative),
                }
            )
    runtime = common.DATA_ROOT / "runtime"
    residues = []
    for path in sorted(runtime.iterdir()) if runtime.exists() else []:
        if path.name.startswith("hold-diag-loopb-"):
            continue
        stamp = _mtime(path)
        if DIAG6_WINDOW[0] <= stamp <= DIAG6_WINDOW[1]:
            item = {"path": common.rel(path), "kind": "directory" if path.is_dir() else "file", "mtime_local": stamp}
            item.update(_tree(path) if path.is_dir() else {"size_bytes": path.stat().st_size, "file_count": 1})
            residues.append(item)
    entries.append(
        {
            "location": "data_root_capture_copy",
            "path": f"{common.rel(runtime)}（诊断 6 桥文件与帧，mtime 2026-09-23 18:00 后）",
            "present": bool(residues),
            "items": residues,
            "source": "docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md「现状」：5060 服务已停；runtime/ 留有诊断 6 会话写出的桥文件与帧",
            "retention_reason": "下次发令前按操作单 C §2.3 隔离；本次答复未授权删除",
            "suggested_action": "LIST_ONLY（AC-16 修订 1：不因本次答复获得删除许可）",
            "deletable": False,
        }
    )
    entries.append(
        {
            "location": "remote_5060",
            "path": "5060 F 盘 repo-b（LOOP-001 阶段 B 传输副本）",
            "present": "UNKNOWN_UNVERIFIED",
            "size_bytes": "UNKNOWN_UNVERIFIED",
            "source": "docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md（F 盘 repo 本地 robocopy 为 repo-b；R4/R6/R7 传输记录）",
            "retention_reason": "阶段 B 服务副本；LOOP-001 已 CLOSED_SUPERSEDED",
            "suggested_action": "USER_DELETES（§7 (g)：5060 由用户自行删除；本项 5060 访问 0，不远端盘点）",
            "deletable": False,
        }
    )
    candidates = [e["path"] for e in entries if e.get("deletable")]
    return {
        "work_id": common.WORK_ID,
        "generated_utc": common.utc_now(),
        "authorization": "docs/authorizations.md 2026-09-28「P1-ENG-ACQ-001 — 用户签发 §5 阶段 1+2 执行信封…并答复 §7 (g)(h)(i)」；提案 AC-16 修订 1 / AC-9 修订 1",
        "status": "INVENTORY_WRITTEN_BEFORE_DELETION",
        "entries": entries,
        "delete_candidates": candidates,
        "deletion": None,
        "remote_access": 0,
    }


def apply(inventory_payload: dict[str, Any]) -> dict[str, Any]:
    """清单已入证据后执行：只移动 `deletable` 的本地 hold 目录到 `~/.Trash/`（可恢复）；逐项记录结果。"""
    stamp = _dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    trash = Path.home() / ".Trash" / f"{common.WORK_ID}-hold-diag-loopb-{stamp}"
    results = []
    for entry in inventory_payload["entries"]:
        if not entry.get("deletable"):
            continue
        root = common.DATA_ROOT if entry["location"] == "data_root_capture_copy" else common.PROJECT_ROOT
        relative = entry["relative"]
        if not deletable(relative):
            raise PermissionError(f"not deletable: {relative}")
        source = root / relative
        if not source.is_dir() or source.is_symlink():
            results.append({"path": entry["path"], "result": "SKIPPED_NOT_A_DIRECTORY"})
            continue
        trash.mkdir(parents=True, exist_ok=True)
        destination = trash / f"{entry['location']}--{source.name}"
        shutil.move(str(source), str(destination))
        results.append({"path": entry["path"], "result": "MOVED_TO_TRASH", "trash_path": common.rel(destination), "exists_after": source.exists()})
    return {"method": "move to ~/.Trash（可恢复；永久清空由用户决定）", "applied_utc": common.utc_now(), "results": results}
