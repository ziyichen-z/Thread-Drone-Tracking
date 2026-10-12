#!/usr/bin/env python3
"""COORD-013 一次性迁移：非活跃项从 docs/current-status.md 移入 docs/parked-status.md。

用户直接授权（docs/authorizations.md 2026-09-21「COORD-013 — …」）。移动而非复制：
ENDED 的 Gate board 行整行移入；PAUSED 行与暂停交接行在状态板留一行索引、原行移入；
只涉及非活跃项的段落逐字移入。任何含活跃项 ID 的块一律不动（验收 §6-2）。
用法：python3 docs/evidence/COORD-013-migrate.py <repo_root>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT))
from tools.check_docs import INLINE_CODE_RE, split_table_row  # noqa: E402

ACTIVE_ID = "P1-ENG-LOOP-001"
STATUS = ROOT / "docs" / "current-status.md"
PARKED = ROOT / "docs" / "parked-status.md"
TODAY = "2026-09-21"
PARKED_LINK = "`docs/parked-status.md`"

lines = STATUS.read_text(encoding="utf-8").split("\n")


def sec(title: str) -> tuple[int, int]:
    start = lines.index(f"## {title}")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    return start, end


def token(cell: str) -> str:
    m = INLINE_CODE_RE.search(cell)
    return m.group(1) if m else cell.strip()


def blocks(body: list[str]) -> list[list[str]]:
    out, cur = [], []
    for line in body:
        if line.strip():
            cur.append(line)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def short_scope(scope: str) -> str:
    s = re.sub(r"[（(]`docs/[^`]+`[）)]", "", scope).strip()
    if len(s) <= 48:
        return s
    for i, ch in enumerate(s):
        if 12 <= i <= 48 and ch in "；;。，,：:（(—":
            return s[:i].strip()
    return s[:46].rstrip() + "…"


moved: dict[str, list[str]] = {}
new = list(lines)

# ---------- Gate board ----------
g0, g1 = sec("Gate board")
hdr_i = next(i for i in range(g0, g1) if lines[i].startswith("| Work ID |"))
header = split_table_row(lines[hdr_i])
col = {name: header.index(name) for name in header}
ended_rows, paused_rows, gate_out = [], [], []
i = hdr_i + 2
while i < g1 and lines[i].startswith("|"):
    row = lines[i]
    cells = split_table_row(row)
    life = token(cells[col["Lifecycle"]])
    if life == "ENDED":
        assert ACTIVE_ID not in row, row[:80]
        ended_rows.append(row)
    elif life == "PAUSED":
        assert ACTIVE_ID not in row, row[:80]
        paused_rows.append(row)
        review = "`N/A`" if cells[col["Independent review"]].strip("` ").upper() == "N/A" else "→ parked"
        one = (
            f"| `{token(cells[col['Work ID']])}` | {short_scope(cells[col['Scope']])} | → parked "
            f"| → parked | {review} | → parked | `{token(cells[col['Overall']])}` | `PAUSED` |"
        )
        assert len(one.encode()) <= 400, one
        gate_out.append(one)
    else:
        gate_out.append(row)
    i += 1
table_end = i
gate_out.append(
    "| `COORD-013` | 状态板接力成本（开工只读当前工作、交接一件事只写一处） "
    f"| 用户直接授权（账本 {TODAY}） | 已落地 → parked | `N/A` | `N/A` "
    "| `LANDED_AWAITING_REMEASURE` | `PAUSED` |"
)
# 表前说明：Lifecycle 规则改写（规则文字，不是移动）
pre = lines[g0 + 1:hdr_i]
lc_start = next(k for k, l in enumerate(pre) if l.startswith("`Lifecycle` column"))
lc_end = next(k for k in range(lc_start, len(pre)) if not pre[k].strip())
new_pre = pre[:lc_start] + [
    "`Lifecycle` (COORD-012/013): `ACTIVE` = has an active handoff; `PAUSED` = stopped, not",
    f"terminated — one-line index here (≤ 400 B), original row and detail in {PARKED_LINK};",
    f"`ENDED` rows are not kept here: the closing role moves the whole row to {PARKED_LINK}",
    "「已终止（ENDED）」 in the same commit. Acceptance (or the user) sets it with Overall; chore never does.",
] + pre[lc_end:]
# 表后：P1-M0-001 注记与 YOLOE 小节整体移出
post = lines[table_end:g1]
post_moved = [l for l in post if l.strip()]
for l in post_moved:
    assert ACTIVE_ID not in l, l[:80]
moved["来自 Gate board 节（表后说明与 YOLOE simulation/deployment split 小节）"] = post_moved
gate_new = [lines[g0]] + new_pre + [lines[hdr_i], lines[hdr_i + 1]] + gate_out + [""]

# ---------- Active handoffs ----------
h0, h1 = sec("Active handoffs")
hh = next(i for i in range(h0, h1) if lines[i].startswith("| Owner/next role"))
hcols = split_table_row(lines[hh])
st_col, wid_col = hcols.index("Status"), hcols.index("Work ID")
cons_col = hcols.index("Consuming")
handoff_paused, handoff_out = [], []
j = hh + 2
while j < h1 and lines[j].startswith("|"):
    row = lines[j]
    cells = split_table_row(row)
    if token(cells[st_col]).startswith("PAUSED"):
        assert ACTIVE_ID not in row, row[:80]
        handoff_paused.append(row)
        one = (
            f"| {cells[0]} | {cells[wid_col]} | 暂停；停点与恢复条件见 {PARKED_LINK} | — | — "
            f"| {cells[st_col]} | {cells[cons_col]} | — |"
        )
        assert len(one.encode()) <= 300, one
        handoff_out.append(one)
    else:
        handoff_out.append(row)
    j += 1
after = [l for l in lines[j:h1] if l.strip()]
for l in after:
    assert ACTIVE_ID not in l, l[:80]
moved["来自 Active handoffs 表后说明"] = after
handoff_new = lines[h0:hh + 2] + handoff_out + [""]

# ---------- Current state ----------
c0, c1 = sec("Current state")
keep_prefixes = (
    "**COORD-010 状态迁移批已获用户",
    "**Other dispositions and evidence:**",
    "use **On-demand history**",
    "Baseline history is on private GitHub",
)
cs_body = lines[c0 + 1:c1]
intro = blocks(cs_body)[0]
cs_keep, cs_moved = [], []
for b in blocks(cs_body)[1:]:
    for l in b:
        if ACTIVE_ID in l or l.startswith(keep_prefixes):
            cs_keep.append(l)
        else:
            cs_moved.append(l)
moved["来自 Current state"] = cs_moved
cs_keep = [
    l.replace("consult each work ID in the Gate board;",
              f"consult each work ID in the Gate board or {PARKED_LINK};")
    for l in cs_keep
]
nonactive = (
    f"**Non-active work items** (`PAUSED`/`ENDED`): gate values, open obligations, stop points and "
    f"constraints live in {PARKED_LINK} (source of truth, not read at start; COORD-013)."
)
# 保持原有分段：COORD-010/LOOP-001 两行一段，Other dispositions 三行一段
k = next(n for n, l in enumerate(cs_keep) if l.startswith("**Other dispositions"))
cs_new = [lines[c0], ""] + intro + ["", nonactive, ""] + cs_keep[:k] + [""] + cs_keep[k:] + [""]

# ---------- Immediate next actions ----------
n0, n1 = sec("Immediate next actions")
na_keep, na_moved, standing = [], [], []
for b in blocks(lines[n0 + 1:n1]):
    if any(ACTIVE_ID in l for l in b):
        na_keep.append(b)
    elif b[0].startswith("**Standing pointers."):
        standing = b
    else:
        na_moved.extend(b + [""])
moved["来自 Immediate next actions"] = na_moved[:-1] if na_moved else []
na_new = [lines[n0], ""]
for b in na_keep:
    na_new += b + [""]

# ---------- Active constraints ----------
a0, a1 = sec("Active constraints and decisions")
move_bullets = (
    "- Under v0.3.13", "- Before any 1c collection", "- **Two registered M3′ findings",
    "- **Two pre-registered limitations", "- M3′ batch 1 runs under",
)
bullets, cur = [], None
for l in lines[a0 + 1:a1]:
    if l.startswith("- "):
        cur = [l]
        bullets.append(cur)
    elif l.startswith("  ") and cur is not None:
        cur.append(l)
ac_keep, ac_moved = [], []
for b in bullets:
    (ac_moved if b[0].startswith(move_bullets) else ac_keep).extend(b)
assert sum(1 for b in bullets if b[0].startswith(move_bullets)) == len(move_bullets)
for l in ac_moved:
    assert ACTIVE_ID not in l
moved["来自 Active constraints and decisions（研究轨道约束，暂停中）"] = ac_moved
ac_new = [lines[a0], ""] + ac_keep + [""]

# ---------- On-demand history ----------
o0, o1 = sec("On-demand history")
od = lines[o0:o1]
sep = next(k for k, l in enumerate(od) if l.startswith("|---"))
od = od[:sep + 1] + [
    "| Resume a paused item, cite an ended item's result or wording, or start a new work item "
    f"| {PARKED_LINK} → the work ID's rows and moved paragraphs (Standing pointers there before any "
    "new item); paused items' Overall/Lifecycle follow the Gate board index here |"
] + od[sep + 1:]
body_row = [k for k, l in enumerate(od) if l.startswith("| Cite BODY-001 results")]
assert len(body_row) == 1 and od[body_row[0]].rstrip().endswith("|")
od[body_row[0]] = od[body_row[0]].rstrip()[:-1].rstrip() + f"; frozen claim wording in {PARKED_LINK} |"

# ---------- 文件头 ----------
head = lines[:c0]
head = [l.replace("Last updated: 2026-09-20", f"Last updated: {TODAY}") for l in head]
wi = next(k for k, l in enumerate(head) if "with git history as the authoritative archive." in l)
head[wi] = head[wi].replace(
    "with git history as the authoritative archive.",
    f"with git history as the authoritative archive. Non-active items live in {PARKED_LINK} (COORD-013).",
)

# ---------- 组装 ----------
order = ["Current state", "Role assignment", "Gate board", "Active handoffs",
         "Immediate next actions", "Active constraints and decisions", "On-demand history"]
secs = {"Current state": cs_new, "Gate board": gate_new, "Active handoffs": handoff_new,
        "Immediate next actions": na_new, "Active constraints and decisions": ac_new,
        "On-demand history": od}
assert [l for l in lines if l.startswith("## ")][:len(order)] == [f"## {t}" for t in order]
out = list(head)
for t in order:
    s, e = sec(t)
    out += secs.get(t, lines[s:e])
log0 = lines.index("## Log")
out += lines[log0:]
STATUS.write_text("\n".join(out), encoding="utf-8")

# ---------- parked ----------
P = []
P += [
    "# 暂停与已终止工作台账（parked status）", "",
    "本文件是**事实源**（COORD-013，用户直接授权 2026-09-21，见 `docs/authorizations.md` 同日条目）：",
    "收纳非活跃 work item（Gate board `Lifecycle` 为 `PAUSED` 或 `ENDED`）的门值、未闭义务、停点、",
    "恢复条件与约束原文。**不进开工必读**；在以下情况读对应部分：恢复某个暂停项；引用某个已终止项",
    "的结论或措辞；开新工作项前读「常设指针」；诊断旧决定。", "",
    "规则：", "",
    "- 每个值只存一处。`ENDED` 项的 Gate board 行整行只在本文件「已终止（ENDED）」表。`PAUSED` 项",
    "  在状态板保留一行索引，其 Overall 与 Lifecycle **以状态板为准**；本文件保存移出时的原行与原段落，",
    "  与状态板冲突时以状态板为准。",
    "- 移动而非复制：原文逐字保留，不改门值、verdict、未闭义务或授权原话。",
    "- 状态迁移由接受角色或用户维护：关闭（→ `ENDED`）时同一提交把 Gate board 整行追加到「已终止」表；",
    "  暂停（→ `PAUSED`）时同一提交把状态板行压成一行索引（≤ 400 B）、原行与停点追加到「暂停」节；",
    "  恢复（→ `ACTIVE`）时在该项原行下方加注「YYYY-MM-DD 已恢复，现状以状态板为准」，原文不改。",
    "- `tools/check_docs.py` 只对「已终止（ENDED）」节的首个表执行 DONE 行双证据检查，其余内容不扫描。",
    "- 与 `docs/status-history.md` 互不收纳：history 只收 `## Log` 移出的过程叙述，且不是事实源。", "",
    "## 已终止（ENDED）", "",
    f"Gate board 原行（{TODAY} 自状态板整行移入；以后关闭的项追加在表末）：", "",
    lines[hdr_i], lines[hdr_i + 1], *ended_rows, "",
    "## 暂停（PAUSED）", "",
    f"以下为 {TODAY} 移出时的原文；Overall 与 Lifecycle 以状态板一行索引为准。", "",
    "### Gate board 原行", "",
    lines[hdr_i], lines[hdr_i + 1], *paused_rows, "",
    "### 交接行原文", "",
    lines[hh], lines[hh + 1], *handoff_paused, "",
    "### `COORD-013`（2026-09-21 落地，待复测）", "",
    "- 提案：`docs/proposals/COORD-013-status-board-relay-cost.md`（末节「落地记录」）；授权：",
    "  `docs/authorizations.md` 2026-09-21 条目；证据：`docs/evidence/COORD-013-*`。",
    "- 未闭义务（提案 §6-5/§6-6）：落地后接下来 10 次交接提交对状态板的写入中位数复测，目标 ≤ 2,200 B",
    "  （报告，不设门）；落地后 30 天内若有会话因信息移入本文件而接力失败，归因到具体条目即回滚该条。",
    "- O4（COORD-008/009/010 改 `ENDED`）未执行：COORD-008/009 仍带首批验证义务，COORD-010 行被",
    "  `docs/engineering-workflow.md` 引为工程轨道生效状态。", "",
    "## 从状态板各节移出的段落（2026-09-21，逐字）", "",
]
for title, body in moved.items():
    if not body:
        continue
    P += [f"### {title}", ""] + body + [""]
P += ["### 常设指针（来自 Immediate next actions；开新工作项前读）", ""] + standing + [""]
PARKED.write_text("\n".join(P), encoding="utf-8")
print("ended", len(ended_rows), "paused", len(paused_rows), "handoff_paused", len(handoff_paused))
for t, b in moved.items():
    print(f"  moved {len(b):3d} lines: {t}")
print("  standing pointers", len(standing), "lines")
