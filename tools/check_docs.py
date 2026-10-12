#!/usr/bin/env python3
"""docs/current-status.md 的机械合规自检（仅标准库）。

对应 AGENTS.md“共享状态更新”和 docs/collaboration-workflow.md §6 的硬上限
（COORD-007 R8/R9，2026-08-12 用户授权：滚动节条数/单条行数检查删除，
单线执行改为执行轨道纪律并新增 Gate-echo；COORD-010 批 1，2026-09-07 用户
授权：移除全文 500 行硬拒绝，体量阀只留分节上限，其余检查全部保留）：

1. 分节行数上限：Current state <= 100、Immediate next actions <= 50、
   Active handoffs <= 70（全文不再设行数硬顶）；
2. 执行轨道纪律（COORD-003，经 COORD-007 R8 修订；COORD-019 双路，用户
   直接授权 2026-10-10）：Active handoffs 中 Status 不以 PAUSED 开头的活跃
   交接按 `Lane` 列（闭集 fast / vlm）分路计数，每路 Consuming=yes 的 <= 1 条、
   Consuming=no 的 <= 2 条；Consuming 列必填 yes/no，Lane 列必填闭集值；少于
   表头列数的畸形行 fail-closed 拒绝（复核轮 2 F5）；
3. Gate-echo（COORD-007 R8）：Active handoffs 每行内引用的、在
   Gate board 有行的反引号标识（work ID 与 `M1` 类里程碑行，含本行
   自身的）必须以 `ID`@token 形式携带 Gate board 当前 Overall 首个
   反引号 token 的逐字拷贝（判据 = token 表成员资格，接受轮 5 N12
   裁定）；切列时反引号内的字面竖线（如 `C_track|geom`）不作分隔符，
   行长不足或 Overall 无 token 的 gate 行即违规（F4/N9，fail-closed）；
4. Gate board 表中独立复核列非 N/A 的 work ID 在 docs/reviews/ 有同名文件；
5. 状态板中所有反引号包裹的 7 位十六进制 commit ID 均能通过
   `git cat-file -t` 验证存在；
6. 顶部 "Last updated:" 日期可按 YYYY-MM-DD 解析；
7. Gate board 中 Overall 恰为 DONE 的行，独立复核列必须含 PASS，
   Unity/hardware 列必须含 PASS 或 UNITY_NA（对应"无双证据不得 DONE"）；
8. `git config core.hooksPath` 已指向 tools/githooks（保证提交前自检生效）；
9. 消耗性门机检（COORD-009 (b)）：docs/reviews/*.md（排除 README.md、
   *-prescreen.md 与围栏代码块内的行）中未被同文件**其后**的
   `releases_consuming_gate: <finding-id>` 配对的
   `blocks_consuming_gate: <finding-id>` 行存在时（按文件顺序配对：release
   只关闭其之前打开的 block，release 之后再次出现的 block 重新打开，先于
   任何 block 的 release 无效），Active handoffs 不得有
   Status 不以 PAUSED 开头的 Consuming=yes 交接（复核者在同一提交把受影响
   交接改为 PAUSED_CONSUMING_GATE_BLOCKED_<finding-id>）。接受角色无
   docs/reviews/* 写权限，其改标 SCOPE_GAP 的 release 走
   docs/implementation-status.md「范围外已知缺陷」账本行：Work ID + Finding +
   状态 RELEASED_SCOPE_GAP 的行视为 docs/reviews/<Work ID>.md 中该 finding 的
   release（按 finding-id 匹配，不看顺序；COORD-009 修订 B）；
10. `## Log` 可压池上限（COORD-012 U1，用户签字授权 2026-09-20；同日用户裁定
    去掉日期判据、终止与否改读 Gate board `Lifecycle` 列）：可压池 = 全部 Log
    条目扣除 (i) 本批次新写（HEAD 版本尚无该标题）与 (ii) 标题关联的 work item
    中有 `Lifecycle` 非 ENDED 的条目（多 ID 标题有一个非 ENDED 即整条不计）；
    不关联任何 Gate board work ID 的条目直接计入，不看日期。关联 = 条目标题含
    完整 Gate board Work ID。可压池总行数 <= 300（含标题与空行的物理行）。
    Gate board 必须有 `Lifecycle` 列（闭集 ACTIVE / PAUSED / ENDED，逐行明示
    只是暂停还是已经终止），缺列、缺值或非闭集值即违规，且该行关联的条目按
    未终止保护（fail-closed）。docs/status-history.md 是压缩/删除移出叙述的
    单向沉淀池（写入前须经用户按 work item 一次同意），本工具不扫描它。
11. 状态板只装当前工作（COORD-013，用户直接授权 2026-09-21）：
    (a) Gate board 不得有 `Lifecycle`=ENDED 的行——关闭方同一提交把整行移入
        docs/parked-status.md「已终止（ENDED）」表（其 Log 条目随之按无关联计入
        可压池）；(b) PAUSED 行 <= 400 B、Status 以 PAUSED 开头的交接行 <= 300 B
        （一行索引，停点与四列叙述在 parked）；(c) 本提交改动过的 ACTIVE Gate
        board 行与活跃交接行各 <= 800 B（HEAD 中逐字存在的行不查，存量不回溯）；
        (d) 本批次新写的 Log 条目 <= 600 B（判据同第 10 条 (i)）；(e) `## Log`
        之前的结构节总字节（每行含换行）<= 30000 B；(f) 对 docs/parked-status.md
        「已终止（ENDED）」节的首个表执行第 7 条 DONE 行双证据检查，防止同一提交
        置 DONE 并移出绕过；parked 其余内容不扫描。字节均按 UTF-8 计。

任一违规都会逐条列出并以非零码退出。分节超限时压缩或删除该节的**旧**
内容（保留指针、结论和未闭义务；移出的叙述整段移入 docs/status-history.md，
git 历史仍是权威档案），或把过程叙述移进 docs/evidence/、docs/reviews/ 等
归属文件，不要压缩本批次新条目。
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATUS_RELPATH = Path("docs") / "current-status.md"
REVIEWS_RELPATH = Path("docs") / "reviews"

# COORD-010 批 1（用户授权 2026-09-07）：全文 500 行硬拒绝已移除，体量阀
# 只剩下面的分节上限。写不下的处置是把过程叙述移进
# docs/reviews/、docs/evidence/、docs/design-reviews/、docs/unity-test-log.md
# 等归属文件，不是为总行数反复压缩提交。
SECTION_LINE_CAPS = {
    "Current state": 100,
    "Immediate next actions": 50,
    "Active handoffs": 70,
}
GATE_BOARD_SECTION = "Gate board"
HANDOFF_SECTION = "Active handoffs"
WORK_ID_COLUMN = "Work ID"
REVIEW_COLUMN = "Independent review"
UNITY_COLUMN = "Unity/hardware"
OVERALL_COLUMN = "Overall"
STATUS_COLUMN = "Status"
# 执行轨道纪律（COORD-003，COORD-007 R8 修订）：Status 以此前缀开头的
# 交接不占轨道；活跃交接按 Consuming 列分别设上限。
PAUSED_PREFIX = "PAUSED"
CONSUMING_COLUMN = "Consuming"
CONSUMING_VALUES = ("yes", "no")
MAX_CONSUMING_ACTIVE = 1
MAX_ZERO_CONSUMPTION_ACTIVE = 2
# 双路并发（COORD-019，用户直接授权 2026-10-10）：交接表 `Lane` 列必填，闭集
# fast / vlm；上述两个上限按路分别计数，归路判断由写行角色负责、接受角色可更正。
LANE_COLUMN = "Lane"
LANE_VALUES = ("fast", "vlm")
# Gate-echo（COORD-007 R8）执法判据 = Gate board token 表成员资格：
# 凡在 Gate board 有行的反引号标识（work ID 与 `M1` 类里程碑行）被交接
# 行引用即须携带 echo。曾以 work ID 文法作执法前置——单段限定漏掉多段
# AREA（复核轮 2 后自查第四洞），文法本身又漏掉里程碑行（复核轮 3
# N12）；接受轮 5 裁定改为成员资格判据，不再维护形状正则。
EXPECTED_HOOKS_PATH = "tools/githooks"
# 消耗性门机检（COORD-009 (b)）：复核文件的机读行不带 work ID——DATA-001 未改动
# 行上的缺陷烧掉的可能是 DATA-002 的 attempt；过严的代价是一次人工 release。
CONSUMING_GATE_BLOCK_RE = re.compile(
    r"^\s*(?:[-*]\s+)?blocks_consuming_gate:\s*(\S+)\s*$"
)
CONSUMING_GATE_RELEASE_RE = re.compile(
    r"^\s*(?:[-*]\s+)?releases_consuming_gate:\s*(\S+)\s*$"
)
REVIEW_SCAN_EXCLUDED_NAMES = ("README.md",)
REVIEW_PRESCREEN_SUFFIX = "-prescreen.md"
CONSUMING_GATE_PAUSE_PREFIX = "PAUSED_CONSUMING_GATE_BLOCKED"
# 账本 release（COORD-009 修订 B）：接受角色在自己的文件里改标 SCOPE_GAP。
LEDGER_RELPATH = Path("docs") / "implementation-status.md"
LEDGER_SECTION_PREFIX = "## 范围外已知缺陷"
LEDGER_WORK_ID_COLUMN = "Work ID"
LEDGER_FINDING_COLUMN = "Finding"
LEDGER_STATUS_COLUMN = "状态"
LEDGER_RELEASE_STATUS = "RELEASED_SCOPE_GAP"

# `## Log` 可压池上限（COORD-012 U1，用户签字授权 2026-09-20；同日用户裁定）。
# D1 曾把 N6(a) 修正为「早于当天−7 天的条目 <=300 行」；D2 采用户第二轮意见把
# 保护对象改为「进行中 work item 的条目」并给无关联条目留 7 天兜底；用户随即
# 裁定去掉该日期兜底（它是本工具唯一随日历变化的判据），并要求终止与否由
# Gate board 新增的 `Lifecycle` 列逐行明示，而不是按 Overall token 前缀推断。
# 数值与 AGENTS.md「共享状态更新」/docs/roles/chore.md 同批维护。
LOG_SECTION = "Log"
LOG_COMPRESSIBLE_POOL_LINE_CAP = 300
LIFECYCLE_COLUMN = "Lifecycle"
LIFECYCLE_VALUES = ("ACTIVE", "PAUSED", "ENDED")
LIFECYCLE_ENDED = "ENDED"
LOG_POOL_REPORT_TOP = 5
LOG_HEADING_PREVIEW_CHARS = 72
# 压缩/删除移出叙述的单向沉淀池（COORD-012 U3）：不是事实源，本工具不扫描。
HISTORY_RELPATH = Path("docs") / "status-history.md"

# COORD-013（用户直接授权 2026-09-21）：状态板只装当前工作、交接一件事只写一处。
PARKED_RELPATH = Path("docs") / "parked-status.md"
PARKED_ENDED_SECTION = "已终止（ENDED）"
LIFECYCLE_ACTIVE = "ACTIVE"
LIFECYCLE_PAUSED = "PAUSED"
STRUCTURE_BYTES_CAP = 30000
ACTIVE_GATE_ROW_BYTES_CAP = 800
PAUSED_GATE_ROW_BYTES_CAP = 400
ACTIVE_HANDOFF_ROW_BYTES_CAP = 800
PAUSED_HANDOFF_ROW_BYTES_CAP = 300
NEW_LOG_ENTRY_BYTES_CAP = 600

INLINE_CODE_RE = re.compile(r"`([^`]+)`")
# 紧邻小数点的 7 位数字是 `0.0311135` 这类指标值片段，不是 commit ID。
COMMIT_ID_RE = re.compile(r"(?<![0-9a-f.])[0-9a-f]{7}(?![0-9a-f.])")
LAST_UPDATED_RE = re.compile(r"^Last updated:\s*(.*\S)\s*$")
LAST_UPDATED_SCAN_LINES = 10


def section_body(lines: list[str], title: str) -> list[str] | None:
    """返回 `## title` 节内部的行（不含标题行）；找不到该节返回 None。"""
    start = None
    for index, line in enumerate(lines):
        if line.strip() == f"## {title}":
            start = index + 1
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return lines[start:end]


def split_table_row(row: str) -> list[str]:
    """按列切分 Markdown 表行。

    反引号内的字面竖线（如主指标名 `C_track|geom`）不是列分隔符——
    按裸 `|` 切列曾使含该指标名的 gate 行整体错位并静默逃出 Gate-echo
    执法（COORD-007 复核轮 2 F4/F5 根因）。"""
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    for char in row.strip():
        if char == "`":
            in_code = not in_code
            current.append(char)
        elif char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def is_separator_row(cells: list[str]) -> bool:
    return all(set(cell) <= set(":- ") for cell in cells)


def check_section_line_caps(lines: list[str]) -> list[str]:
    violations = []
    for title, cap in SECTION_LINE_CAPS.items():
        body = section_body(lines, title)
        if body is None:
            continue
        if len(body) > cap:
            violations.append(
                f"'## {title}' 节共 {len(body)} 行，超过上限 {cap} 行；请淘汰或"
                "压缩旧内容（DONE/CLOSED 条目压成 <=4 行摘要），或把过程叙述移进"
                "docs/reviews/、docs/evidence/、docs/design-reviews/、docs/unity-test-log.md"
                "等归属文件，不要压缩最新条目。"
            )
    return violations


def section_table(lines: list[str], title: str, purpose: str) -> tuple[list[str] | None, list[str]]:
    """返回 (指定节内首个 Markdown 表的行, 违规列表)；找不到表时表行为 None。"""
    body = section_body(lines, title)
    if body is None:
        return None, [f"未找到 '## {title}' 节，无法{purpose}。"]
    table = []
    for line in body:
        if line.lstrip().startswith("|"):
            table.append(line)
        elif table:
            break
    if len(table) < 2:
        return None, [f"'## {title}' 节中未找到状态表。"]
    return table, []


def gate_board_table(lines: list[str]) -> tuple[list[str] | None, list[str]]:
    """返回 (Gate board 表行, 违规列表)；找不到表时表行为 None。"""
    return section_table(lines, GATE_BOARD_SECTION, "检查复核文件对应关系")


def handoff_activity(
    lines: list[str],
) -> tuple[dict[str, list[str]], dict[str, list[str]], list[str]]:
    """解析 Active handoffs：返回 (按路的消耗性活跃交接标签, 按路的零消耗活跃
    交接标签, 违规列表)。两个字典的键恒为 LANE_VALUES（COORD-019 双路）。
    活跃 = Status 不以 PAUSED 开头；畸形行、非法 Consuming 值与缺失/非闭集的
    Lane 值记为违规并跳过（fail-closed）。"""
    consuming_active: dict[str, list[str]] = {lane: [] for lane in LANE_VALUES}
    zero_active: dict[str, list[str]] = {lane: [] for lane in LANE_VALUES}
    table, errors = section_table(lines, HANDOFF_SECTION, "检查执行轨道纪律")
    if table is None:
        return consuming_active, zero_active, errors
    header = split_table_row(table[0])
    required = (WORK_ID_COLUMN, STATUS_COLUMN, CONSUMING_COLUMN, LANE_COLUMN)
    missing = [column for column in required if column not in header]
    if missing:
        return consuming_active, zero_active, [
            f"'{HANDOFF_SECTION}' 表头缺少 {', '.join(missing)} 列，"
            "无法检查执行轨道纪律。"
        ]
    work_col = header.index(WORK_ID_COLUMN)
    status_col = header.index(STATUS_COLUMN)
    consuming_col = header.index(CONSUMING_COLUMN)
    lane_col = header.index(LANE_COLUMN)
    violations = []
    for row in table[1:]:
        cells = split_table_row(row)
        if is_separator_row(cells):
            continue
        if len(cells) <= max(work_col, status_col, consuming_col, lane_col):
            label = cells[0] if cells else row.strip()
            violations.append(
                f"'{HANDOFF_SECTION}' 行 '{label}' 只有 {len(cells)} 个单元格，"
                "少于表头列数——畸形行按 fail-closed 拒绝（COORD-007 复核轮 2 "
                "F5），无法核对轨道纪律与 Consuming 列；请补全该行。"
            )
            continue
        id_match = INLINE_CODE_RE.search(cells[work_col])
        label = id_match.group(1) if id_match else cells[work_col]
        consuming_value = cells[consuming_col].strip().strip("`").lower()
        if consuming_value not in CONSUMING_VALUES:
            violations.append(
                f"'{HANDOFF_SECTION}' 行 '{label}' 的 {CONSUMING_COLUMN} 列是 "
                f"'{cells[consuming_col]}'，必须为 yes（创建/消耗 scenario/"
                "session/run ID、Play 配额或 API 预算）或 no。"
            )
            continue
        lane_value = cells[lane_col].strip().strip("`").lower()
        if lane_value not in LANE_VALUES:
            violations.append(
                f"'{HANDOFF_SECTION}' 行 '{label}' 的 {LANE_COLUMN} 列是 "
                f"'{cells[lane_col]}'，必须为 {' / '.join(LANE_VALUES)}（双路并发，"
                "COORD-019；归路判据见 AGENTS.md「执行轨道纪律」）。"
            )
            continue
        if cells[status_col].strip("` ").upper().startswith(PAUSED_PREFIX):
            continue
        if consuming_value == "yes":
            consuming_active[lane_value].append(label)
        else:
            zero_active[lane_value].append(label)
    return consuming_active, zero_active, violations


def check_track_discipline(lines: list[str]) -> list[str]:
    """执行轨道纪律（COORD-003，COORD-007 R8 修订，COORD-019 双路）：
    每路 1 消耗 + <=2 零消耗。"""
    consuming_by_lane, zero_by_lane, violations = handoff_activity(lines)
    violations = list(violations)
    for lane in LANE_VALUES:
        consuming_active = consuming_by_lane[lane]
        zero_active = zero_by_lane[lane]
        if len(consuming_active) > MAX_CONSUMING_ACTIVE:
            violations.append(
                f"'{HANDOFF_SECTION}' `{lane}` 路有 {len(consuming_active)} 条消耗性活跃交接"
                f"（{'、'.join(consuming_active)}），超过该路上限 {MAX_CONSUMING_ACTIVE} 条。"
                "向用户逐条汇报，由用户决定保留哪条，其余 Status 改为 "
                f"{PAUSED_PREFIX}_<原因>（细则见 AGENTS.md「执行轨道纪律」）。"
            )
        if len(zero_active) > MAX_ZERO_CONSUMPTION_ACTIVE:
            violations.append(
                f"'{HANDOFF_SECTION}' `{lane}` 路有 {len(zero_active)} 条零消耗活跃交接"
                f"（{'、'.join(zero_active)}），超过该路上限 "
                f"{MAX_ZERO_CONSUMPTION_ACTIVE} 条。向用户逐条汇报，由用户决定"
                f"保留哪些，其余 Status 改为 {PAUSED_PREFIX}_<原因>"
                "（细则见 AGENTS.md「执行轨道纪律」）。"
            )
    return violations


def gate_overall_tokens(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    """Gate board 中每个 work ID 的 Overall 首个反引号 token。

    返回 (tokens, violations)：行长不足或 Overall 无反引号 token 的
    gate 行是违规而不是跳过——静默丢行会使该 ID 永远逃出 Gate-echo
    执法（COORD-007 复核轮 2 F4/N9，fail-closed）。"""
    table, _ = gate_board_table(lines)
    if table is None:
        return {}, []
    header = split_table_row(table[0])
    if WORK_ID_COLUMN not in header or OVERALL_COLUMN not in header:
        return {}, []
    work_col = header.index(WORK_ID_COLUMN)
    overall_col = header.index(OVERALL_COLUMN)
    tokens: dict[str, str] = {}
    violations: list[str] = []
    for row in table[1:]:
        cells = split_table_row(row)
        if is_separator_row(cells):
            continue
        if len(cells) <= max(work_col, overall_col):
            label = cells[0] if cells else row.strip()
            violations.append(
                f"Gate board 行 '{label}' 只有 {len(cells)} 个单元格，少于"
                "表头列数，无法提取 Overall token——丢行即违规"
                "（COORD-007 复核轮 2 F4/N9，fail-closed）。"
            )
            continue
        id_match = INLINE_CODE_RE.search(cells[work_col])
        if id_match is None:
            continue
        overall_match = INLINE_CODE_RE.search(cells[overall_col])
        if overall_match is None:
            violations.append(
                f"Gate board 中 `{id_match.group(1)}` 的 Overall 单元格 "
                f"'{cells[overall_col]}' 没有反引号 token，该 ID 会逃出 "
                "Gate-echo 执法——丢行即违规（COORD-007 复核轮 2 F4/N9）。"
            )
            continue
        tokens[id_match.group(1)] = overall_match.group(1)
    return tokens, violations


def check_handoff_gate_echo(lines: list[str]) -> list[str]:
    """Gate-echo（COORD-007 R8）：交接行内引用的 work ID 必须逐字携带其
    Gate board 当前 Overall token（`ID`@token，至少标注一次）。"""
    table, errors = section_table(lines, HANDOFF_SECTION, "检查 Gate-echo")
    if table is None:
        return errors
    tokens, violations = gate_overall_tokens(lines)
    violations = list(violations)
    for row in table[1:]:
        cells = split_table_row(row)
        if is_separator_row(cells):
            continue
        referenced: list[str] = []
        for span in INLINE_CODE_RE.findall(row):
            if span in tokens and span not in referenced:
                referenced.append(span)
        for work_id in referenced:
            expected = f"`{work_id}`@{tokens[work_id]}"
            if expected not in row:
                violations.append(
                    f"'{HANDOFF_SECTION}' 行引用 `{work_id}` 但缺少 Gate-echo "
                    f"'{expected}'（Gate board 当前 Overall token 逐字拷贝，"
                    "至少标注一次；门值变化时必须同批更新引用行）。"
                )
    return violations


def check_gate_board_reviews(lines: list[str], reviews_dir: Path) -> list[str]:
    table, errors = gate_board_table(lines)
    if table is None:
        return errors
    header = split_table_row(table[0])
    if WORK_ID_COLUMN not in header or REVIEW_COLUMN not in header:
        return [
            f"Gate board 表头缺少 '{WORK_ID_COLUMN}' 或 '{REVIEW_COLUMN}' 列，"
            "无法检查复核文件对应关系。"
        ]
    work_col = header.index(WORK_ID_COLUMN)
    review_col = header.index(REVIEW_COLUMN)
    violations = []
    for row in table[1:]:
        cells = split_table_row(row)
        if is_separator_row(cells) or len(cells) <= max(work_col, review_col):
            continue
        id_match = INLINE_CODE_RE.search(cells[work_col])
        if id_match is None:
            continue
        work_id = id_match.group(1)
        review_cell = cells[review_col].strip("` ")
        if review_cell.upper() == "N/A":
            continue
        if not (reviews_dir / f"{work_id}.md").is_file():
            violations.append(
                f"Gate board 中 `{work_id}` 的独立复核列不是 N/A，但 "
                f"{REVIEWS_RELPATH}/{work_id}.md 不存在。"
            )
    return violations


def open_consuming_gate_blocks(reviews_dir: Path) -> dict[str, list[str]]:
    """每个复核文件中未被同文件其后的 releases 行配对的 blocks finding-id。

    按文件顺序配对：release 只关闭其之前打开的 block；release 之后再次出现
    的同名 block 重新打开；先于任何 block 的 release 无效。集合式配对曾让
    "先 release 后 block"与"旧 release 抵销新 block"静默通过（COORD-009
    修订后 Codex 指出的顺序缺口）。跳过 README.md、*-prescreen.md 与围栏
    代码块内的行（模板示例不计）。"""
    open_blocks: dict[str, list[str]] = {}
    if not reviews_dir.is_dir():
        return open_blocks
    for path in sorted(reviews_dir.glob("*.md")):
        if path.name in REVIEW_SCAN_EXCLUDED_NAMES or path.name.endswith(
            REVIEW_PRESCREEN_SUFFIX
        ):
            continue
        open_ids: list[str] = []
        in_fence = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            block_match = CONSUMING_GATE_BLOCK_RE.match(line)
            if block_match is not None:
                if block_match.group(1) not in open_ids:
                    open_ids.append(block_match.group(1))
                continue
            release_match = CONSUMING_GATE_RELEASE_RE.match(line)
            if release_match is not None and release_match.group(1) in open_ids:
                open_ids.remove(release_match.group(1))
        if open_ids:
            open_blocks[path.name] = list(open_ids)
    return open_blocks


def ledger_released_findings(ledger_path: Path) -> dict[str, set[str]]:
    """账本「范围外已知缺陷」表中状态恰为 RELEASED_SCOPE_GAP 的 work ID → finding 集。

    找不到账本、该节或表时返回空（无 release，fail-closed 方向）。"""
    released: dict[str, set[str]] = {}
    if not ledger_path.is_file():
        return released
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().startswith(LEDGER_SECTION_PREFIX):
            start = index + 1
            break
    if start is None:
        return released
    table: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.lstrip().startswith("|"):
            table.append(line)
        elif table:
            break
    if len(table) < 2:
        return released
    header = split_table_row(table[0])
    required = (LEDGER_WORK_ID_COLUMN, LEDGER_FINDING_COLUMN, LEDGER_STATUS_COLUMN)
    if any(column not in header for column in required):
        return released
    work_col = header.index(LEDGER_WORK_ID_COLUMN)
    finding_col = header.index(LEDGER_FINDING_COLUMN)
    status_col = header.index(LEDGER_STATUS_COLUMN)
    for row in table[1:]:
        cells = split_table_row(row)
        if is_separator_row(cells) or len(cells) <= max(work_col, finding_col, status_col):
            continue
        if cells[status_col].strip().strip("`*").strip() != LEDGER_RELEASE_STATUS:
            continue
        id_match = INLINE_CODE_RE.search(cells[work_col])
        work_id = id_match.group(1) if id_match else cells[work_col].strip().strip("`")
        finding = cells[finding_col].strip().strip("`")
        if work_id and finding:
            released.setdefault(work_id, set()).add(finding)
    return released


def check_consuming_gate_blocks(
    lines: list[str], reviews_dir: Path, ledger_path: Path | None = None
) -> list[str]:
    """消耗性门机检（COORD-009 (b)）：未 release 的 blocks 行存在时，不得有
    未暂停的 Consuming=yes 交接。账本 RELEASED_SCOPE_GAP 行视同 release（修订 B）。"""
    open_blocks = open_consuming_gate_blocks(reviews_dir)
    if open_blocks and ledger_path is not None:
        released = ledger_released_findings(ledger_path)
        for name in list(open_blocks):
            work_id = name[: -len(".md")]
            remaining = [f for f in open_blocks[name] if f not in released.get(work_id, set())]
            if remaining:
                open_blocks[name] = remaining
            else:
                del open_blocks[name]
    if not open_blocks:
        return []
    consuming_by_lane, _, _ = handoff_activity(lines)
    consuming_active = [
        label for lane in LANE_VALUES for label in consuming_by_lane[lane]
    ]
    if not consuming_active:
        return []
    described = "；".join(
        f"{name}: {', '.join(findings)}" for name, findings in open_blocks.items()
    )
    return [
        f"复核文件存在未 release 的 blocks_consuming_gate 行（{described}），但 "
        f"'{HANDOFF_SECTION}' 仍有未暂停的消耗性交接（{'、'.join(consuming_active)}）。"
        f"把这些交接的 Status 改为 {CONSUMING_GATE_PAUSE_PREFIX}_<finding-id>，或由"
        "复核角色红绿核实后写 releases_consuming_gate: <finding-id>，或由接受角色在 "
        f"{LEDGER_RELPATH}「范围外已知缺陷」写状态 {LEDGER_RELEASE_STATUS} 的账本行"
        "（COORD-009 (b)，修订 B）。"
    ]


def check_gate_board_done_rows(lines: list[str]) -> list[str]:
    """Overall 恰为 DONE 的行必须同时具备复核与 Unity 证据。"""
    table, _ = gate_board_table(lines)
    if table is None:
        return []  # 缺节/缺表已由 check_gate_board_reviews 报告。
    return done_row_violations(table, "Gate board")


def done_row_violations(table: list[str], where: str) -> list[str]:
    """对一张 Gate board 格式的表执行 DONE 行双证据检查（where 用于报错定位）。"""
    header = split_table_row(table[0])
    required = (WORK_ID_COLUMN, REVIEW_COLUMN, UNITY_COLUMN, OVERALL_COLUMN)
    missing = [column for column in required if column not in header]
    if missing:
        return [
            f"{where} 表头缺少 {', '.join(missing)} 列，无法检查 DONE 行证据。"
        ]
    work_col = header.index(WORK_ID_COLUMN)
    review_col = header.index(REVIEW_COLUMN)
    unity_col = header.index(UNITY_COLUMN)
    overall_col = header.index(OVERALL_COLUMN)
    violations = []
    for row in table[1:]:
        cells = split_table_row(row)
        if is_separator_row(cells) or len(cells) <= max(
            work_col, review_col, unity_col, overall_col
        ):
            continue
        overall = cells[overall_col].strip().strip("`*").strip()
        if overall != "DONE":
            continue
        id_match = INLINE_CODE_RE.search(cells[work_col])
        work_id = id_match.group(1) if id_match else cells[work_col]
        if "PASS" not in cells[review_col]:
            violations.append(
                f"{where} 中 `{work_id}` Overall 为 DONE，但独立复核列没有 "
                "PASS 证据；运行时行没有复核+Unity 双证据不得置 DONE。"
            )
        unity_cell = cells[unity_col]
        if "PASS" not in unity_cell and "UNITY_NA" not in unity_cell:
            violations.append(
                f"{where} 中 `{work_id}` Overall 为 DONE，但 Unity/hardware "
                "列既无 PASS 也无 UNITY_NA；运行时行没有复核+Unity 双证据不得置 DONE。"
            )
    return violations


def log_entries(lines: list[str]) -> list[list[str]]:
    """`## Log` 节内以 `### ` 开头的条目，每条 = 标题行到下一条标题前的全部物理行。"""
    body = section_body(lines, LOG_SECTION)
    if body is None:
        return []
    entries: list[list[str]] = []
    current: list[str] | None = None
    for line in body:
        if line.startswith("### "):
            current = [line]
            entries.append(current)
        elif current is not None:
            current.append(line)
    return entries


def gate_work_ids(lines: list[str]) -> list[str]:
    """Gate board 全部行的 Work ID（含里程碑行），作为 Log 标题关联判据的标识表。"""
    table, _ = gate_board_table(lines)
    if table is None:
        return []
    header = split_table_row(table[0])
    if WORK_ID_COLUMN not in header:
        return []
    work_col = header.index(WORK_ID_COLUMN)
    ids: list[str] = []
    for row in table[1:]:
        cells = split_table_row(row)
        if is_separator_row(cells) or len(cells) <= work_col:
            continue
        id_match = INLINE_CODE_RE.search(cells[work_col])
        if id_match is not None and id_match.group(1) not in ids:
            ids.append(id_match.group(1))
    return ids


def gate_lifecycles(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    """Gate board 每个 work ID 的 `Lifecycle` 闭集值（用户裁定 2026-09-20）。

    返回 (values, violations)：缺列、缺值或非闭集值都是违规（fail-closed），
    这些行不进 values，调用方按「未终止」保护其关联的 Log 条目。"""
    table, _ = gate_board_table(lines)
    if table is None:
        return {}, []
    header = split_table_row(table[0])
    if WORK_ID_COLUMN not in header:
        return {}, []
    if LIFECYCLE_COLUMN not in header:
        return {}, [
            f"Gate board 表头缺少 '{LIFECYCLE_COLUMN}' 列（闭集 "
            f"{'/'.join(LIFECYCLE_VALUES)}，逐行明示只是暂停还是已经终止；用户裁定 "
            "2026-09-20，COORD-012），无法判定 Log 可压池——缺列即违规，所有关联"
            "条目按未终止保护。"
        ]
    work_col = header.index(WORK_ID_COLUMN)
    lifecycle_col = header.index(LIFECYCLE_COLUMN)
    values: dict[str, str] = {}
    violations: list[str] = []
    for row in table[1:]:
        cells = split_table_row(row)
        if is_separator_row(cells) or len(cells) <= work_col:
            continue
        id_match = INLINE_CODE_RE.search(cells[work_col])
        if id_match is None:
            continue
        work_id = id_match.group(1)
        if len(cells) <= lifecycle_col:
            violations.append(
                f"Gate board 中 `{work_id}` 的行只有 {len(cells)} 个单元格，缺 "
                f"{LIFECYCLE_COLUMN} 值——缺值即违规，该行按未终止保护其 Log 条目"
                "（fail-closed）。"
            )
            continue
        value_match = INLINE_CODE_RE.search(cells[lifecycle_col])
        value = value_match.group(1) if value_match else cells[lifecycle_col].strip()
        if value not in LIFECYCLE_VALUES:
            violations.append(
                f"Gate board 中 `{work_id}` 的 {LIFECYCLE_COLUMN} 单元格 "
                f"'{cells[lifecycle_col]}' 不在闭集 {'/'.join(LIFECYCLE_VALUES)} 内；"
                "该行按未终止保护其 Log 条目（fail-closed）。"
            )
            continue
        values[work_id] = value
    return values, violations


def linked_gate_ids(heading: str, work_ids: list[str]) -> list[str]:
    """标题中出现的完整 Gate board 标识（词边界匹配；子串与缩写不算关联）。"""
    title = heading[len("### "):]
    return [
        work_id
        for work_id in work_ids
        if re.search(
            r"(?<![A-Za-z0-9_-])" + re.escape(work_id) + r"(?![A-Za-z0-9_-])", title
        )
    ]


def head_log_headings(repo_root: Path) -> set[str] | None:
    """HEAD 版本状态板的 Log 标题集（判定「本批次新写」）；无 git/HEAD 时返回 None。"""
    head_lines = head_status_lines(repo_root)
    if head_lines is None:
        return None
    return {entry[0] for entry in log_entries(head_lines)}


def head_status_lines(repo_root: Path) -> list[str] | None:
    """HEAD 版本状态板的全部行；无 git/HEAD 或该文件未提交时返回 None。"""
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{STATUS_RELPATH.as_posix()}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.splitlines()


def heading_preview(heading: str) -> str:
    if len(heading) <= LOG_HEADING_PREVIEW_CHARS:
        return heading
    return heading[:LOG_HEADING_PREVIEW_CHARS] + "…"


def check_log_compressible_pool(lines: list[str], repo_root: Path) -> list[str]:
    """`## Log` 可压池上限（COORD-012 U1 + 用户裁定 2026-09-20）：见模块 docstring 第 10 条。

    不可压 = (i) 本批次新写（HEAD 尚无该标题）/ (ii) 关联 work item 有
    `Lifecycle` 非 ENDED（含缺值/非闭集值的行，fail-closed）；其余条目（含无关联
    work ID 的条目）按物理行数累加，超过 LOG_COMPRESSIBLE_POOL_LINE_CAP 即违规。"""
    entries = log_entries(lines)
    if not entries:
        return []
    work_ids = gate_work_ids(lines)
    lifecycles, violations = gate_lifecycles(lines)
    violations = list(violations)
    committed = head_log_headings(repo_root)
    pool: list[tuple[int, str]] = []
    for entry in entries:
        heading = entry[0]
        if committed is not None and heading not in committed:
            continue  # (i) 本批次新写
        linked = linked_gate_ids(heading, work_ids)
        if linked and any(
            lifecycles.get(work_id) != LIFECYCLE_ENDED for work_id in linked
        ):
            continue  # (ii) 关联未终止（或标识不合法）的 work item
        pool.append((len(entry), heading))
    total = sum(count for count, _ in pool)
    if total > LOG_COMPRESSIBLE_POOL_LINE_CAP:
        largest = sorted(pool, key=lambda item: item[0], reverse=True)[:LOG_POOL_REPORT_TOP]
        described = "；".join(
            f"{count} 行 '{heading_preview(heading)}'" for count, heading in largest
        )
        violations.append(
            f"'## {LOG_SECTION}' 可压池共 {total} 行（{len(pool)} 条：关联 work item 全部 "
            f"{LIFECYCLE_COLUMN}=`{LIFECYCLE_ENDED}` 的条目 + 无关联 work ID 的条目；"
            "本批次新写与关联未终止 work item 的条目不计），超过上限 "
            f"{LOG_COMPRESSIBLE_POOL_LINE_CAP} 行（COORD-012 U1，用户裁定 2026-09-20）。"
            "处置见 docs/roles/chore.md「允许的任务」：按压缩标准压缩可压池条目（保留结论、"
            f"证据指针、未闭义务；移出的叙述整段移入 {HISTORY_RELPATH.as_posix()}，移动而非"
            "复制，移入前须先经用户以 work item 为单位一次同意），不压本批次新条目与未终止 "
            f"work item 的条目。最大的条目：{described}。"
        )
    return violations


def row_bytes(row: str) -> int:
    return len(row.encode("utf-8"))


def cell_token(cell: str) -> str:
    match = INLINE_CODE_RE.search(cell)
    return match.group(1) if match else cell.strip()


def check_gate_board_row_caps(lines: list[str], head_lines: list[str] | None) -> list[str]:
    """COORD-013 (a)(b)(c)：ENDED 行不留板；PAUSED 行 <= 400 B；改动过的 ACTIVE 行 <= 800 B。"""
    table, _ = gate_board_table(lines)
    if table is None:
        return []
    header = split_table_row(table[0])
    if WORK_ID_COLUMN not in header or LIFECYCLE_COLUMN not in header:
        return []  # 缺列已由 Lifecycle 检查报告。
    work_col = header.index(WORK_ID_COLUMN)
    lifecycle_col = header.index(LIFECYCLE_COLUMN)
    committed = set(head_lines) if head_lines is not None else None
    violations = []
    for row in table[1:]:
        cells = split_table_row(row)
        if is_separator_row(cells) or len(cells) <= max(work_col, lifecycle_col):
            continue
        work_id = cell_token(cells[work_col])
        lifecycle = cell_token(cells[lifecycle_col])
        size = row_bytes(row)
        if lifecycle == LIFECYCLE_ENDED:
            violations.append(
                f"Gate board 中 `{work_id}` 的 {LIFECYCLE_COLUMN} 为 ENDED——已终止的行不留在"
                f"状态板：关闭方在同一提交把整行移入 {PARKED_RELPATH.as_posix()}"
                f"「{PARKED_ENDED_SECTION}」表（COORD-013）。"
            )
        elif lifecycle == LIFECYCLE_PAUSED and size > PAUSED_GATE_ROW_BYTES_CAP:
            violations.append(
                f"Gate board 中 PAUSED 行 `{work_id}` 共 {size} B，超过上限 "
                f"{PAUSED_GATE_ROW_BYTES_CAP} B：暂停项只留一行索引（ID、简短 Scope、Overall、"
                f"Lifecycle），四列叙述移入 {PARKED_RELPATH.as_posix()}（COORD-013）。"
            )
        elif (
            lifecycle == LIFECYCLE_ACTIVE
            and size > ACTIVE_GATE_ROW_BYTES_CAP
            and committed is not None
            and row not in committed
        ):
            violations.append(
                f"Gate board 中本提交改动过的 ACTIVE 行 `{work_id}` 共 {size} B，超过上限 "
                f"{ACTIVE_GATE_ROW_BYTES_CAP} B：单元格只写门值 token 与证据指针，叙述留在"
                "复核/证据文件（COORD-013）。"
            )
    return violations


def check_handoff_row_caps(lines: list[str], head_lines: list[str] | None) -> list[str]:
    """COORD-013 (b)(c)：暂停交接行 <= 300 B；本提交改动过的活跃交接行 <= 800 B。"""
    table, _ = section_table(lines, HANDOFF_SECTION, "检查交接行字节上限")
    if table is None:
        return []
    header = split_table_row(table[0])
    if STATUS_COLUMN not in header:
        return []
    status_col = header.index(STATUS_COLUMN)
    work_col = header.index(WORK_ID_COLUMN) if WORK_ID_COLUMN in header else None
    committed = set(head_lines) if head_lines is not None else None
    violations = []
    for row in table[1:]:
        cells = split_table_row(row)
        if is_separator_row(cells) or len(cells) <= status_col:
            continue  # 畸形行已由执行轨道纪律检查报告。
        label = cells[work_col] if work_col is not None and len(cells) > work_col else row[:60]
        size = row_bytes(row)
        if cell_token(cells[status_col]).startswith(PAUSED_PREFIX):
            if size > PAUSED_HANDOFF_ROW_BYTES_CAP:
                violations.append(
                    f"'{HANDOFF_SECTION}' 暂停行 {label} 共 {size} B，超过上限 "
                    f"{PAUSED_HANDOFF_ROW_BYTES_CAP} B：暂停交接只留一行，停点与恢复条件移入 "
                    f"{PARKED_RELPATH.as_posix()}（COORD-013）。"
                )
        elif size > ACTIVE_HANDOFF_ROW_BYTES_CAP and committed is not None and row not in committed:
            violations.append(
                f"'{HANDOFF_SECTION}' 本提交改动过的活跃行 {label} 共 {size} B，超过上限 "
                f"{ACTIVE_HANDOFF_ROW_BYTES_CAP} B：交接行是写「谁接手、做什么、读哪个文件」的"
                "唯一处，过程叙述留在复核/证据文件（COORD-013）。"
            )
    return violations


def check_new_log_entry_caps(lines: list[str], head_lines: list[str] | None) -> list[str]:
    """COORD-013 (d)：本批次新写（HEAD 尚无该标题）的 Log 条目 <= 600 B。"""
    if head_lines is None:
        return []
    committed = {entry[0] for entry in log_entries(head_lines)}
    violations = []
    for entry in log_entries(lines):
        if entry[0] in committed:
            continue
        size = row_bytes("\n".join(entry).rstrip())
        if size > NEW_LOG_ENTRY_BYTES_CAP:
            violations.append(
                f"'## {LOG_SECTION}' 新条目 '{heading_preview(entry[0])}' 共 {size} B，超过上限 "
                f"{NEW_LOG_ENTRY_BYTES_CAP} B：只写一句结论加指针，过程叙述留在复核/证据文件"
                "（COORD-013）。"
            )
    return violations


def check_structure_bytes(lines: list[str]) -> list[str]:
    """COORD-013 (e)：`## Log` 之前的结构节总字节（每行含换行）<= 30000 B。"""
    end = len(lines)
    for index, line in enumerate(lines):
        if line.strip() == f"## {LOG_SECTION}":
            end = index
            break
    size = sum(row_bytes(line) + 1 for line in lines[:end])
    if size > STRUCTURE_BYTES_CAP:
        return [
            f"'## {LOG_SECTION}' 之前的结构节共 {size} B，超过上限 {STRUCTURE_BYTES_CAP} B"
            f"（COORD-013 稳态门）：非活跃项的内容移入 {PARKED_RELPATH.as_posix()}，过程叙述"
            "移入复核/证据文件；状态板只装当前工作。"
        ]
    return []


def check_parked_done_rows(repo_root: Path) -> list[str]:
    """COORD-013 (f)：parked「已终止（ENDED）」节首个表的 DONE 行双证据检查。"""
    parked_path = repo_root / PARKED_RELPATH
    if not parked_path.is_file():
        return []
    parked_lines = parked_path.read_text(encoding="utf-8").splitlines()
    table, _ = section_table(parked_lines, PARKED_ENDED_SECTION, "检查 DONE 行证据")
    if table is None:
        return []
    return done_row_violations(table, f"{PARKED_RELPATH.as_posix()}「{PARKED_ENDED_SECTION}」")


def check_hooks_path(repo_root: Path) -> list[str]:
    try:
        inside = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if inside.returncode != 0 or inside.stdout.strip() != "true":
            return []  # 非 git 工作树（如测试夹具目录）不检查钩子配置。
        result = subprocess.run(
            ["git", "config", "core.hooksPath"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ["无法执行 git config，无法确认提交前自检钩子已启用。"]
    value = result.stdout.strip()
    if result.returncode != 0 or value != EXPECTED_HOOKS_PATH:
        return [
            f"git config core.hooksPath 当前是 '{value or '未设置'}'，应为 "
            f"'{EXPECTED_HOOKS_PATH}'；运行 `git config core.hooksPath "
            f"{EXPECTED_HOOKS_PATH}` 启用提交前自检。"
        ]
    return []


def referenced_commit_ids(text: str) -> list[str]:
    ids: list[str] = []
    for span in INLINE_CODE_RE.findall(text):
        for commit_id in COMMIT_ID_RE.findall(span):
            if commit_id not in ids:
                ids.append(commit_id)
    return ids


def commit_exists(commit_id: str, repo_root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "cat-file", "-t", commit_id],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def check_commit_ids(text: str, repo_root: Path) -> list[str]:
    violations = []
    for commit_id in referenced_commit_ids(text):
        if not commit_exists(commit_id, repo_root):
            violations.append(
                f"状态板引用的 commit `{commit_id}` 未通过 `git cat-file -t` "
                "验证（对象不存在，或检查目录不是 git 仓库）。"
            )
    return violations


def check_last_updated(lines: list[str]) -> list[str]:
    for line in lines[:LAST_UPDATED_SCAN_LINES]:
        match = LAST_UPDATED_RE.match(line)
        if match is None:
            continue
        value = match.group(1)
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return [f"顶部 'Last updated' 日期 '{value}' 无法按 YYYY-MM-DD 解析。"]
        return []
    return [
        f"docs/current-status.md 前 {LAST_UPDATED_SCAN_LINES} 行内未找到 "
        "'Last updated: YYYY-MM-DD' 行。"
    ]


def collect_violations(repo_root: Path) -> list[str]:
    status_path = repo_root / STATUS_RELPATH
    if not status_path.is_file():
        return [f"{STATUS_RELPATH} 不存在，无法执行文档合规检查。"]
    text = status_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    violations = []
    violations += check_section_line_caps(lines)
    violations += check_track_discipline(lines)
    violations += check_handoff_gate_echo(lines)
    violations += check_gate_board_reviews(lines, repo_root / REVIEWS_RELPATH)
    violations += check_consuming_gate_blocks(
        lines, repo_root / REVIEWS_RELPATH, repo_root / LEDGER_RELPATH
    )
    violations += check_gate_board_done_rows(lines)
    violations += check_log_compressible_pool(lines, repo_root)
    head_lines = head_status_lines(repo_root)
    violations += check_gate_board_row_caps(lines, head_lines)
    violations += check_handoff_row_caps(lines, head_lines)
    violations += check_new_log_entry_caps(lines, head_lines)
    violations += check_structure_bytes(lines)
    violations += check_parked_done_rows(repo_root)
    violations += check_commit_ids(text, repo_root)
    violations += check_last_updated(lines)
    violations += check_hooks_path(repo_root)
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="docs/current-status.md 机械合规自检（硬上限见 AGENTS.md）"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        help="仓库根目录（默认：本脚本所在仓库）",
    )
    args = parser.parse_args(argv)
    violations = collect_violations(args.root.resolve())
    if violations:
        print(f"docs 合规检查未通过，共 {len(violations)} 项违规：")
        for index, violation in enumerate(violations, start=1):
            print(f"  {index}. {violation}")
        return 1
    print(
        "docs 合规检查通过：分节上限、执行轨道纪律、Gate-echo、"
        "复核文件、消耗性门 blocks、DONE 行双证据、Log 可压池、状态板字节上限与"
        "parked DONE 行、commit 引用、Last updated、hooksPath 均符合要求。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
