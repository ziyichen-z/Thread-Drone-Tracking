#!/usr/bin/env python3
"""COORD-013 验收 §6-1/§6-2/§6-3 的机械核对。

用法：python3 docs/evidence/COORD-013-move-check.py <迁移前状态板> <迁移后状态板> <parked>
- §6-2：迁移前后对比，被删除或被改写的行不得含活跃项 ID；
- §6-3：每一条被删除的非空行都能在 parked 中逐字找到，规则改写行除外（下方闭集，逐条列出）；
- §6-1：打印迁移前后 `## Log` 之前的结构节字节（每行含换行）。
"""
import sys
from collections import Counter

ACTIVE_ID = "P1-ENG-LOOP-001"
REWRITE_PREFIXES = (          # 规则文字改写：不是移动，按闭集豁免
    "Last updated: ",
    "compression goes to `docs/status-history.md`",
    "with git history as the authoritative archive.",
    "`Lifecycle` column (user ruling 2026-09-20, COORD-012)",
    "`PAUSED` = stopped but not terminated",
    "paused by user); `ENDED` = terminated",
    "superseded). Only `ENDED` rows' Log entries",
    "(or the user) sets this column together with Overall",
    "**Other dispositions and evidence:** consult each work ID in the Gate board;",
    "| Cite BODY-001 results",
)


def read(p):
    return open(p, encoding="utf-8").read().split("\n")


def struct_bytes(lines):
    end = next((i for i, l in enumerate(lines) if l.strip() == "## Log"), len(lines))
    return sum(len(l.encode()) + 1 for l in lines[:end])


old, new, parked = read(sys.argv[1]), read(sys.argv[2]), read(sys.argv[3])
removed = Counter(l for l in old if l.strip()) - Counter(l for l in new if l.strip())
added = Counter(l for l in new if l.strip()) - Counter(l for l in old if l.strip())
parked_set = set(parked)
fail = []
exempt, found = [], 0
for line, n in removed.items():
    if ACTIVE_ID in line:
        fail.append(f"§6-2 含活跃项 ID 的行被删除/改写：{line[:100]}")
    if line in parked_set:
        found += n
    elif line.startswith(REWRITE_PREFIXES):
        exempt.append(line)
    else:
        fail.append(f"§6-3 被删除的行未在 parked 中逐字找到：{line[:100]}")
print(f"§6-1 结构节字节：迁移前 {struct_bytes(old)} B → 迁移后 {struct_bytes(new)} B")
print(f"§6-3 被删除非空行 {sum(removed.values())} 条：在 parked 中逐字找到 {found} 条；规则改写豁免 {len(exempt)} 条")
for line in exempt:
    print(f"    豁免（规则改写）：{line[:90]}")
print(f"新增非空行 {sum(added.values())} 条（一行索引、规则改写、指针）：")
for line in added:
    print(f"    + {line[:110]}")
if fail:
    print("FAIL")
    for f in fail:
        print("  " + f)
    sys.exit(1)
print("PASS：§6-2 无含活跃项 ID 的行被删改；§6-3 移动完整。")
