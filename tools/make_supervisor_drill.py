#!/usr/bin/env python3
"""COORD-015 §10 合成演练夹具生成器（仅标准库）。

在临时目录生成一个独立的 git 仓库副本：精简状态板、账本、角色入口、
消耗账本样例与合成工作项 DRILL-001。所有生成文件标注
「合成演练，不构成任何真实 D/C/R 轮次或门决定」；本工具不读取、不触碰
真实仓库的状态板、账本或暂停项，演练只在夹具目录内进行。

另提供 A5 六段演练中可机械化的脚手架：派发日志（supervisor-dispatch.jsonl）
事件构造与追加、提案 open_items: 机读行注入、§3.2/§3.8 提交主题与尾注
生成器。本工具不编排子代理，也不调用 codex exec；真实演练在后续会话进行。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

DRILL_WORK_ID = "DRILL-001"
SYNTHETIC_MARK = "合成演练，不构成任何真实 D/C/R 轮次或门决定"
DISPATCH_LOG = "docs/evidence/supervisor-dispatch.jsonl"

EVENT_KINDS = (
    "requested", "started", "end_confirmed", "finished",
    "reconciled", "aborted", "duplicate_callback",
)
END_CONFIRMABLE_SOURCES = ("callback", "stop_call", "pid_gone", "user_quote")
SECTION_END_RE = re.compile(r"^#{1,3} ")


def commit_subject(work_id: str, round_name: str, summary: str) -> str:
    return f"{work_id} {round_name} {summary}"


def commit_trailers(dispatch_id: str, role: str) -> str:
    return (f"Dispatch-Id: {dispatch_id}\n"
            f"Role-Check: {role} pass")


def dispatch_event(kind: str, dispatch_id: str, work_id: str = DRILL_WORK_ID,
                   **fields) -> dict:
    if kind not in EVENT_KINDS:
        raise ValueError(f"事件类型不在闭集：{kind}")
    if (kind == "end_confirmed"
            and fields.get("source") not in END_CONFIRMABLE_SOURCES):
        raise ValueError(f"end_confirmed.source 不在闭集：{fields.get('source')}")
    return {"event": kind, "dispatch_id": dispatch_id, "work_id": work_id,
            "synthetic": True, **fields}


def append_dispatch_event(repo: Path, event: dict) -> Path:
    path = repo / DISPATCH_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return path


def read_dispatch_log(repo: Path) -> list:
    path = repo / DISPATCH_LOG
    if not path.exists():
        return []
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def open_items_line(items) -> str:
    return "open_items: " + (", ".join(items) if items else "none")


def inject_open_items(proposal_path: Path, items, round_no: int) -> None:
    """把 open_items: 行插入唯一 `### D<round_no>` 节末（COORD-015 BC-14 节绑定；
    COORD-016 修 COORD-015 R2@落地 R2-1：不再追加到文件尾）。

    节 = 唯一一行匹配 `^### D<n>(?![0-9A-Za-z])` 的标题起，至其后第一行匹配
    `^#{1,3} ` 的标题（不含）或文件尾止；行插在节内最后一个非空行之后。
    标题缺失或多于 1 行即 ValueError（不猜位置）。
    """
    lines = proposal_path.read_text(encoding="utf-8").splitlines()
    heading = re.compile(rf"^### D{round_no}(?![0-9A-Za-z])")
    starts = [index for index, line in enumerate(lines) if heading.match(line)]
    if len(starts) != 1:
        raise ValueError(f"`### D{round_no}` 节标题有 {len(starts)} 行（须恰好 1 行）")
    start = starts[0]
    end = next((index for index in range(start + 1, len(lines))
                if SECTION_END_RE.match(lines[index])), len(lines))
    last = max(index for index in range(start, end) if lines[index].strip())
    lines[last + 1:last + 1] = ["", open_items_line(items)]
    proposal_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _board() -> str:
    return f"""# Current status（{SYNTHETIC_MARK}）

## Gate board

| Work ID | Scope | Design | Implementation/auto evidence | Independent review | Unity/hardware | Overall | Lifecycle |
|---|---|---|---|---|---|---|---|
| `{DRILL_WORK_ID}` | 合成演练工作项 | 合成 | 合成 | `N/A` | `N/A` | `ACCEPTED` | `ACTIVE` |

## Active handoffs

| Owner/next role | Work ID | Requested action | Scope | Progress | Status | Consuming | Return to |
|---|---|---|---|---|---|---|---|
| Acceptance | `{DRILL_WORK_ID}`@ACCEPTED | 合成演练交接 | — | — | `IMPLEMENTING` | no | — |

## Log
"""


def _ledger() -> str:
    return f"""# 用户关键授权账本（{SYNTHETIC_MARK}）

格式略（合成夹具）。

---

## 2026-09-25 {DRILL_WORK_ID} — 决策信封：DRILL-001 D 类代拍（合成）

- 用户原话："合成"。
- at: 2026-09-25T08:00:00Z
- 代录会话: 合成

supervisor_decision_envelope:
  enabled: true
  classes: [D1, D4, D5, D6]
  expires_at: 2026-12-31
  veto_window_days: 7

---

## 2026-09-25 {DRILL_WORK_ID} — 执行信封：DRILL-001 K4 阶段（合成）

- 用户原话："合成"。
- at: 2026-09-25T08:00:00Z
- 代录会话: 合成

supervisor_subdelegation:
  enabled: true
  max_increment: {{API 次数: 5}}
  max_total: {{API 次数: 10}}
  expires_at: K4
"""


def _proposal() -> str:
    # COORD-016 §3：带 d7_range:（BC 行条款格，正向资格 kind=/bc=）与 d7_recommend:
    # （非 `### D<n>` 裁定节）样例行；Status 为 PROPOSED，D7 演练时由演练脚本改为 ACCEPTED。
    return f"""# {DRILL_WORK_ID} — 合成演练提案（{SYNTHETIC_MARK}）

Status: PROPOSED（合成）

## Binding clarifications (BC table)

| 编号 | 条款 | 复核项 | 证明方式 | 标签 | 依据 | 日期 |
|---|---|---|---|---|---|---|
| BC-1 | 合格门门值（合成）`d7_range: gate1 in [0.50, 0.80] kind=门值 bc=BC-1` | 行为 | test:合成 | BASE | 合成 | 2026-09-26 |
| BC-2 | 最小样本量（合成）`d7_range: n_min in {{200, 400}} kind=最小样本量 bc=BC-2` | 测试覆盖 | test:合成 | BASE | 合成 | 2026-09-26 |

## Pending rulings（待裁定）

d7_recommend: gate1 = 0.70

d7_recommend: n_min = 400

## Codex review decision

### D1 接受侧裁定

裁定原文（合成）。

### D2 接受侧裁定

裁定原文（合成）。
"""


def _role_entry(role: str) -> str:
    return (f"# {role} 角色入口（{SYNTHETIC_MARK}）\n\n"
            "被 supervisor 拉起时：按 §3.8 在带内返回报告（work_id、this_round、"
            "commits[]、handoff、next_owner、needs_user、consumed、checks），"
            "收工提交信息末尾带 Dispatch-Id 与 Role-Check 尾注。\n")


def _consumption_ledger() -> str:
    return json.dumps({
        "work_id": DRILL_WORK_ID,
        "synthetic": True,
        "note": SYNTHETIC_MARK,
        "events": [
            {"at": "2026-09-25T08:30:00Z", "dimension": "API 次数",
             "amount": 1, "note": "合成样例"},
        ],
    }, ensure_ascii=False, indent=2) + "\n"


def _drill_readme() -> str:
    return f"""# DRILL-001 合成演练夹具

{SYNTHETIC_MARK}。本目录是 COORD-015 §10 的演练夹具：精简状态板、账本、
角色入口与消耗账本样例均为合成；夹具内子代理与 codex exec 的 cwd 为本目录；
不触碰真实状态板、账本或暂停项。每项核查逐条记 {{pass, fail, N/A(理由)}}。
"""


def build_drill_repo(dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    files = {
        "DRILL.md": _drill_readme(),
        "docs/current-status.md": _board(),
        "docs/authorizations.md": _ledger(),
        f"docs/proposals/{DRILL_WORK_ID}-synthetic-drill.md": _proposal(),
        "docs/evidence/DRILL-001-ledger.json": _consumption_ledger(),
        DISPATCH_LOG: "",
    }
    for role in ("ideation", "acceptance", "implementation", "review", "chore", "supervisor"):
        files[f"docs/roles/{role}.md"] = _role_entry(role)
        files[f".claude/commands/{role}.md"] = _role_entry(role)
    for rel, text in files.items():
        path = dest / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=dest, check=True,
                   capture_output=True, text=True)
    subprocess.run(["git", "-c", "user.name=drill", "-c", "user.email=drill@example.com",
                    "add", "-A"], cwd=dest, check=True, capture_output=True, text=True)
    subprocess.run(["git", "-c", "user.name=drill", "-c", "user.email=drill@example.com",
                    "commit", "-q", "-m",
                    commit_subject(DRILL_WORK_ID, "D0", f"夹具初始化（{SYNTHETIC_MARK}）")],
                   cwd=dest, check=True, capture_output=True, text=True)
    return dest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="生成 COORD-015 §10 合成演练夹具（不触碰真实状态板/账本）")
    parser.add_argument("--dest", type=Path,
                        help="夹具目标目录（默认：新建临时目录）")
    args = parser.parse_args(argv)
    dest = args.dest
    if dest is None:
        dest = Path(tempfile.mkdtemp(prefix="supervisor-drill-"))
    build_drill_repo(dest.resolve())
    print(f"夹具已生成：{dest.resolve()}（{SYNTHETIC_MARK}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
