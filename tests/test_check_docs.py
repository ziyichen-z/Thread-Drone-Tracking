from datetime import date, timedelta
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.check_docs import check_hooks_path, collect_violations


# Current state 的合规 bullet。各用例用它做定位替换，避免追加重名的
# `## Current state` 节——check_docs.section_body 只认第一处同名节，
# 重名节会被静默忽略。
CURRENT_STATE_BULLET = "- `P1-M0-001` baseline closed with review and Unity evidence."

# 合规交接行（COORD-007 R8：Consuming 列 + Gate-echo `ID`@token；COORD-019：Lane 列 fast/vlm）。
ACTIVE_ROW = "| User | `P1-M0-001`@DONE | Confirm closure | `UNITY_PASSED` | yes | fast |"
PAUSED_ROW = (
    "| Ideation | `P1-M7-DEPLOY-001`@OUT_OF_CURRENT_SCOPE | Hold "
    "| `PAUSED_SINGLE_TRACK` | no | vlm |"
)

PASS_STATUS = f"""# Current status

Last updated: 2026-08-12

## Current state

{CURRENT_STATE_BULLET}

## Active handoffs

| Owner/next role | Work ID | Requested action | Status | Consuming | Lane |
|---|---|---|---|---|---|
{ACTIVE_ROW}
{PAUSED_ROW}

## Gate board

| Work ID | Scope | Independent review | Unity/hardware | Overall | Lifecycle |
|---|---|---|---|---|---|
| `P1-M0-001` | Baseline | `PASS` (`docs/reviews/P1-M0-001.md`) | `PASS_8_OF_8` | `DONE` | `ACTIVE` |
| `P1-M7-DEPLOY-001` | Deployment | `N/A` | Orin required later | `OUT_OF_CURRENT_SCOPE` | `PAUSED` |

Metric fragments such as `C_track=0.0311135` and `269.0007310/268.9705627 s`
must not be mistaken for commit IDs.

## Log

### 2026-08-12 — decision one

Body.
"""

# COORD-010 批 1（用户授权 2026-09-07）：全文 500 行硬拒绝已移除，体量阀只剩
# 分节上限。`## Log` 没有分节上限，因此下面的填充把状态板撑到远超旧硬顶，
# 用来同时做「超长仍通过」的正例和「其余规则不随之松开」的反例底板。
OVERSIZED_LOG_FILLER = "filler line\n" * 600

# COORD-012 U1（用户授权 2026-09-20；同日用户裁定去掉日期判据、终止与否改读
# Gate board `Lifecycle` 列）：`## Log` 可压池 ≤300 行。可压池 = 全部条目扣除
# (i) 本批次新写、(ii) 标题关联的 work item 中有 Lifecycle 非 ENDED 的条目；
# 无关联 work ID 的条目直接入池、不看日期。超长填充因此挂在 ACTIVE work item
# 的条目下，「超长仍通过」正例才继续成立。
ACTIVE_GATE_ROW = "| `P1-ACTIVE-001` | Active work | `N/A` | pending | `IMPLEMENTING` | `ACTIVE` |"
PAUSED_GATE_ROW = (
    "| `P1-PAUSED-001` | Paused work | `N/A` | pending | `REVISION_REQUESTED_ROUND_2` | `PAUSED` |"
)
CLOSED_GATE_ROW = (
    "| `P1-CLOSED-001` | Closed work | `N/A` | n/a | `CLOSED_NEGATIVE_RESULT` | `ENDED` |"
)
ACTIVE_LOG_HEADING = "### 2026-08-12 — P1-ACTIVE-001 long narrative\n\n"

# COORD-013（用户直接授权 2026-09-21）：`ENDED` 行不再留在状态板，关闭方同一提交
# 把整行移入 docs/parked-status.md「已终止（ENDED）」表。夹具里的 `P1-M0-001` 仍是
# DONE 行，但 Lifecycle 取 `ACTIVE`（它还有一条确认收尾的活跃交接），只为机械地
# 覆盖 DONE/Gate-echo/复核文件检查；`P1-CLOSED-001` 只在需要它违规时才放上状态板，
# 其余用例里它代表「已移入 parked、状态板上无行」的已终止项。


def with_extra_gate_rows(doc: str) -> str:
    return doc.replace(
        "| `P1-M7-DEPLOY-001` | Deployment",
        ACTIVE_GATE_ROW + "\n" + PAUSED_GATE_ROW
        + "\n| `P1-M7-DEPLOY-001` | Deployment",
    )


def without_lifecycle_column(doc: str) -> str:
    return (
        doc.replace(
            "| Overall | Lifecycle |\n|---|---|---|---|---|---|",
            "| Overall |\n|---|---|---|---|---|",
        )
        .replace("| `DONE` | `ACTIVE` |", "| `DONE` |")
        .replace("| `OUT_OF_CURRENT_SCOPE` | `PAUSED` |", "| `OUT_OF_CURRENT_SCOPE` |")
    )


def log_entries(title: str, dated: str, count: int, lines_each: int = 10) -> str:
    """生成 count 条 Log 条目，每条恰好 lines_each 个物理行（标题+空行+正文+空行）。"""
    body = "\n".join(f"narrative {index}" for index in range(lines_each - 3))
    return "".join(
        f"### {dated} — {title} round {n}\n\n{body}\n\n" for n in range(count)
    )


def days_ago(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


OVERSIZED_STATUS = with_extra_gate_rows(PASS_STATUS) + ACTIVE_LOG_HEADING + OVERSIZED_LOG_FILLER


def write_status_repo(
    root: Path,
    status_text: str,
    review_ids=(),
    review_files=None,
    ledger_text=None,
    history_text=None,
    parked_text=None,
) -> None:
    reviews_dir = root / "docs" / "reviews"
    reviews_dir.mkdir(parents=True)
    (root / "docs" / "current-status.md").write_text(status_text, encoding="utf-8")
    if ledger_text is not None:
        (root / "docs" / "implementation-status.md").write_text(ledger_text, encoding="utf-8")
    if history_text is not None:
        (root / "docs" / "status-history.md").write_text(history_text, encoding="utf-8")
    if parked_text is not None:
        (root / "docs" / "parked-status.md").write_text(parked_text, encoding="utf-8")
    for work_id in review_ids:
        (reviews_dir / f"{work_id}.md").write_text(f"# {work_id}\n", encoding="utf-8")
    for name, text in (review_files or {}).items():
        (reviews_dir / name).write_text(text, encoding="utf-8")


def violations_for(
    status_text: str,
    review_ids=("P1-M0-001",),
    review_files=None,
    ledger_text=None,
    history_text=None,
    parked_text=None,
) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_status_repo(
            root,
            status_text,
            review_ids=review_ids,
            review_files=review_files,
            ledger_text=ledger_text,
            history_text=history_text,
            parked_text=parked_text,
        )
        return collect_violations(root)


class CheckDocsTest(unittest.TestCase):
    def test_compliant_minimal_status_passes(self):
        self.assertEqual(violations_for(PASS_STATUS), [])

    def test_each_violation_kind_is_reported(self):
        bad = with_extra_gate_rows(PASS_STATUS).replace(
            "Last updated: 2026-08-12",
            "Last updated: sometime",
        )
        bad = bad.replace(
            "| `P1-M0-001` | Baseline | `PASS` (`docs/reviews/P1-M0-001.md`) | `PASS_8_OF_8` | `DONE` |",
            "| `P1-M0-001` | Baseline | `PASS` (candidate `abcdef1`) | `PASS_8_OF_8` | `DONE` |",
        )
        bad += ACTIVE_LOG_HEADING + OVERSIZED_LOG_FILLER
        # 不创建任何 docs/reviews/ 文件，使复核文件检查违规。
        violations = violations_for(bad, review_ids=())
        joined = "\n".join(violations)
        self.assertGreaterEqual(len(violations), 3)
        self.assertIn("P1-M0-001.md 不存在", joined)
        self.assertIn("`abcdef1`", joined)
        self.assertIn("Last updated", joined)
        # COORD-010 批 1 回归：总行数远超旧 500 行硬顶不再产生体量违规。
        self.assertNotIn("超过硬上限", joined)

    def test_oversized_status_passes_when_sections_stay_within_caps(self):
        # COORD-010 批 1 正例（用户授权 2026-09-07）：全文 500 行硬拒绝移除后，
        # 分节全部合法的状态板即便远超旧硬顶也必须零违规通过——体量治理不再
        # 靠总行数反复压缩提交。
        self.assertGreater(len(OVERSIZED_STATUS.splitlines()), 500)
        self.assertEqual(violations_for(OVERSIZED_STATUS), [])

    def test_oversized_status_still_enforces_every_other_rule(self):
        # COORD-010 批 1 反例：移除行数阀不得顺带松开任何一条其余规则，
        # 逐条在「超长但分节合法」的底板上复验。
        stale_echo = OVERSIZED_STATUS.replace(
            "`P1-M0-001`@DONE", "`P1-M0-001`@STALE_TOKEN"
        )
        self.assertIn("缺少 Gate-echo", "\n".join(violations_for(stale_echo)))

        second_consuming = OVERSIZED_STATUS.replace(
            PAUSED_ROW,
            PAUSED_ROW
            + "\n| Review | `P1-M0-001`@DONE | Re-verify | `IMPLEMENTING` | yes | fast |",
        )
        self.assertIn("超过该路上限 1 条", "\n".join(violations_for(second_consuming)))

        no_unity = OVERSIZED_STATUS.replace(
            "| `PASS_8_OF_8` | `DONE` |", "| pending | `DONE` |"
        )
        self.assertIn("既无 PASS 也无 UNITY_NA", "\n".join(violations_for(no_unity)))

        blocked = {"P1-M0-001.md": "# P1-M0-001\n- blocks_consuming_gate: F17\n"}
        self.assertIn(
            "blocks_consuming_gate",
            "\n".join(violations_for(OVERSIZED_STATUS, review_files=blocked)),
        )

        over_cap = OVERSIZED_STATUS.replace(
            CURRENT_STATE_BULLET, "filler line\n" * 105
        )
        self.assertIn("'## Current state'", "\n".join(violations_for(over_cap)))

    def test_done_row_needs_review_and_unity_evidence(self):
        no_unity = PASS_STATUS.replace(
            "| `P1-M0-001` | Baseline | `PASS` (`docs/reviews/P1-M0-001.md`) | `PASS_8_OF_8` | `DONE` |",
            "| `P1-M0-001` | Baseline | `PASS` (`docs/reviews/P1-M0-001.md`) | pending | `DONE` |",
        )
        joined = "\n".join(violations_for(no_unity))
        self.assertIn("既无 PASS 也无 UNITY_NA", joined)

    def test_consuming_cap_is_enforced(self):
        # COORD-019 双路：同一路第 2 条消耗性交接超限。
        second_consuming = PASS_STATUS.replace(
            PAUSED_ROW,
            PAUSED_ROW
            + "\n| Review | `P1-M0-001`@DONE | Re-verify | `IMPLEMENTING` | yes | fast |",
        )
        joined = "\n".join(violations_for(second_consuming))
        self.assertIn("消耗性活跃交接", joined)
        self.assertIn("`fast` 路", joined)
        self.assertIn("超过该路上限 1 条", joined)

    def test_consuming_cap_is_per_lane(self):
        # COORD-019 双路：另一路的消耗性交接不与本路合计。
        other_lane = PASS_STATUS.replace(
            PAUSED_ROW,
            PAUSED_ROW
            + "\n| Review | `P1-M0-001`@DONE | Re-verify | `IMPLEMENTING` | yes | vlm |",
        )
        self.assertEqual(violations_for(other_lane), [])

    def test_zero_consumption_cap_is_enforced(self):
        extra = "".join(
            f"\n| Ideation | `P1-M0-001`@DONE | Draft {index} | `PROPOSED` | no | fast |"
            for index in range(3)
        )
        doc = PASS_STATUS.replace(PAUSED_ROW, PAUSED_ROW + extra)
        joined = "\n".join(violations_for(doc))
        self.assertIn("零消耗活跃交接", joined)
        self.assertIn("超过该路上限 2 条", joined)

    def test_zero_consumption_cap_is_per_lane(self):
        extra = "".join(
            f"\n| Ideation | `P1-M0-001`@DONE | Draft {index} | `PROPOSED` | no | {lane} |"
            for index, lane in enumerate(("fast", "fast", "vlm", "vlm"))
        )
        doc = PASS_STATUS.replace(PAUSED_ROW, PAUSED_ROW + extra)
        self.assertEqual(violations_for(doc), [])

    def test_consuming_column_is_required_and_validated(self):
        no_column = PASS_STATUS.replace(
            "| Owner/next role | Work ID | Requested action | Status | Consuming | Lane |",
            "| Owner/next role | Work ID | Requested action | Status | Lane |",
        ).replace(ACTIVE_ROW, ACTIVE_ROW.replace("| yes | fast |", "| fast |")).replace(
            PAUSED_ROW, PAUSED_ROW.replace("| no | vlm |", "| vlm |")
        )
        joined = "\n".join(violations_for(no_column))
        self.assertIn("Consuming", joined)

        bad_value = PASS_STATUS.replace(
            ACTIVE_ROW, ACTIVE_ROW.replace("| yes |", "| maybe |")
        )
        joined = "\n".join(violations_for(bad_value))
        self.assertIn("必须为 yes", joined)

    def test_lane_column_is_required_and_validated(self):
        # COORD-019 双路：Lane 列缺失或非闭集值 fail-closed。
        no_column = PASS_STATUS.replace(
            "| Owner/next role | Work ID | Requested action | Status | Consuming | Lane |",
            "| Owner/next role | Work ID | Requested action | Status | Consuming |",
        ).replace(ACTIVE_ROW, ACTIVE_ROW.replace("| yes | fast |", "| yes |")).replace(
            PAUSED_ROW, PAUSED_ROW.replace("| no | vlm |", "| no |")
        )
        joined = "\n".join(violations_for(no_column))
        self.assertIn("Lane", joined)

        bad_value = PASS_STATUS.replace(ACTIVE_ROW, ACTIVE_ROW.replace("| fast |", "| gpu |"))
        joined = "\n".join(violations_for(bad_value))
        self.assertIn("必须为 fast / vlm", joined)

    def test_gate_echo_is_required_and_verbatim(self):
        # 引用 work ID 但完全缺 @token 注记。
        missing = PASS_STATUS.replace("`P1-M0-001`@DONE", "`P1-M0-001`")
        joined = "\n".join(violations_for(missing))
        self.assertIn("缺少 Gate-echo", joined)
        self.assertIn("`P1-M0-001`@DONE", joined)

        # 注记存在但与 Gate board 当前 Overall token 不一致。
        stale = PASS_STATUS.replace("`P1-M0-001`@DONE", "`P1-M0-001`@UNITY_PASSED")
        joined = "\n".join(violations_for(stale))
        self.assertIn("缺少 Gate-echo", joined)

    def test_hooks_path_check_is_still_enforced(self):
        # §7 行 6：hook 检查须「保留并回归」；批 1 只删全文行数阀，
        # 提交前自检钩子的正反例必须留有直接证据。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            self.assertIn("core.hooksPath", "\n".join(check_hooks_path(root)))
            subprocess.run(
                ["git", "config", "core.hooksPath", "tools/githooks"],
                cwd=root,
                check=True,
            )
            self.assertEqual(check_hooks_path(root), [])

    def test_section_line_caps(self):
        doc = PASS_STATUS.replace(CURRENT_STATE_BULLET, "filler line\n" * 105)
        joined = "\n".join(violations_for(doc))
        self.assertIn("'## Current state'", joined)
        self.assertIn("超过上限 100 行", joined)
        # 分节上限是 COORD-010 批 1 之后唯一的体量阀；报错不再提全文硬顶。
        self.assertNotIn("超过硬上限", joined)

    def test_gate_echo_enforced_when_gate_cells_contain_pipes(self):
        # F4 回归（COORD-007 复核轮 2）：gate 行单元格含字面竖线（如主
        # 指标名 `C_track|geom`）时该行必须仍进入 Gate-echo 执法。修复前
        # 裸竖线切列使 Overall 落到无 token 单元格，token 表静默丢行，
        # 篡改 echo 也能通过检查。
        piped = PASS_STATUS.replace(
            "| `PASS_8_OF_8` | `DONE` |",
            "| focused split `C_track|geom` gate PASS | `DONE` |",
        )
        self.assertEqual(violations_for(piped), [])  # 正确 echo 仍须通过
        stale = piped.replace("`P1-M0-001`@DONE", "`P1-M0-001`@STALE_TOKEN")
        joined = "\n".join(violations_for(stale))
        self.assertIn("缺少 Gate-echo", joined)
        self.assertIn("`P1-M0-001`@DONE", joined)

    def test_gate_row_with_unparsable_overall_is_flagged(self):
        # F4/N9 回归：Overall 单元格无反引号 token 的 gate 行不得静默
        # 丢行——丢行即违规（fail-closed），否则该 ID 逃出 echo 执法。
        plain = PASS_STATUS.replace(
            "| `PASS_8_OF_8` | `DONE` |", "| `PASS_8_OF_8` | DONE |"
        )
        joined = "\n".join(violations_for(plain))
        self.assertIn("Overall", joined)
        self.assertIn("P1-M0-001", joined)

    def test_gate_echo_matches_multi_segment_work_ids(self):
        # F4 补充回归（接受角色真实板篡改探针发现）：真实 work ID 的
        # AREA 常含多段（P1-M3-BODY-001、P1-VLM-CAL-001、
        # P1-M3M4-SCOPE-002）；引用侧正则若只匹配单段 AREA，这些 ID 的
        # echo 永不执法——与 F4 同类的静默免检。
        doc = PASS_STATUS.replace("P1-M0-001", "P1-M3-BODY-001")
        self.assertEqual(
            violations_for(doc, review_ids=("P1-M3-BODY-001",)), []
        )
        stale = doc.replace("`P1-M3-BODY-001`@DONE", "`P1-M3-BODY-001`@STALE")
        joined = "\n".join(violations_for(stale, review_ids=("P1-M3-BODY-001",)))
        self.assertIn("缺少 Gate-echo", joined)
        self.assertIn("`P1-M3-BODY-001`@DONE", joined)

    def test_milestone_rows_enter_echo_grammar(self):
        # N12 裁定回归（COORD-007 接受轮 5）：echo 执法判据 = Gate board
        # token 表成员资格，凡在 Gate board 有行的反引号标识（含 `M1` 类
        # 里程碑行）被交接行引用时都必须携带 echo；不再以 work ID 文法
        # 作为执法前置——那正是第四洞的同类残留。
        doc = PASS_STATUS.replace(
            "| `P1-M7-DEPLOY-001` | Deployment",
            "| `M1` (milestone) | Milestone | `N/A` | later | `OPEN_AWAITING_X` | `PAUSED` |\n"
            "| `P1-M7-DEPLOY-001` | Deployment",
        )
        with_ref = doc.replace(
            "| Confirm closure |", "| Confirm closure toward `M1` |"
        )
        joined = "\n".join(violations_for(with_ref))
        self.assertIn("缺少 Gate-echo", joined)
        self.assertIn("`M1`@OPEN_AWAITING_X", joined)
        ok = doc.replace(
            "| Confirm closure |",
            "| Confirm closure toward `M1`@OPEN_AWAITING_X |",
        )
        self.assertEqual(violations_for(ok), [])

    def test_open_consuming_gate_block_pauses_consuming_rows(self):
        # COORD-009 (b)：复核文件里未 release 的 blocks_consuming_gate 行必须
        # 拦住所有未暂停的 Consuming=yes 交接；暂停或 release 后放行。
        review = {
            "P1-M0-001.md": "# P1-M0-001\n\n#### F17（CLASS_2，上轮漏检）\n"
            "blocks_consuming_gate: F17\n"
        }
        joined = "\n".join(violations_for(PASS_STATUS, review_files=review))
        self.assertIn("blocks_consuming_gate", joined)
        self.assertIn("F17", joined)
        self.assertIn("PAUSED_CONSUMING_GATE_BLOCKED", joined)

        paused = PASS_STATUS.replace(
            ACTIVE_ROW,
            ACTIVE_ROW.replace("`UNITY_PASSED`", "`PAUSED_CONSUMING_GATE_BLOCKED_F17`"),
        )
        self.assertEqual(violations_for(paused, review_files=review), [])

        released = {
            "P1-M0-001.md": review["P1-M0-001.md"]
            + "\n## Round 2\n- releases_consuming_gate: F17\n"
        }
        self.assertEqual(violations_for(PASS_STATUS, review_files=released), [])

        # 零消耗交接不受 blocks 行约束。
        zero_only = PASS_STATUS.replace(ACTIVE_ROW, ACTIVE_ROW.replace("| yes |", "| no |"))
        self.assertEqual(violations_for(zero_only, review_files=review), [])

    def test_consuming_gate_pairs_in_file_order(self):
        # 顺序缺口回归（COORD-009 修订后 Codex 指出）：release 只关闭其之前
        # 打开的 block；先 release 后 block 仍是未闭的 block；release 之后再次
        # block 重新打开。集合式配对会把这两种情形静默放过。
        release_first = {
            "P1-M0-001.md": "# P1-M0-001\n- releases_consuming_gate: F17\n"
            "\n## Round 3\n- blocks_consuming_gate: F17\n"
        }
        joined = "\n".join(violations_for(PASS_STATUS, review_files=release_first))
        self.assertIn("blocks_consuming_gate", joined)
        self.assertIn("F17", joined)

        reblocked = {
            "P1-M0-001.md": "# P1-M0-001\n- blocks_consuming_gate: F17\n"
            "\n## Round 2\n- releases_consuming_gate: F17\n"
            "\n## Round 4\n- blocks_consuming_gate: F17\n"
        }
        joined = "\n".join(violations_for(PASS_STATUS, review_files=reblocked))
        self.assertIn("F17", joined)

        closed_in_order = {
            "P1-M0-001.md": "# P1-M0-001\n- blocks_consuming_gate: F17\n"
            "\n## Round 2\n- releases_consuming_gate: F17\n"
        }
        self.assertEqual(violations_for(PASS_STATUS, review_files=closed_in_order), [])

    def test_ledger_released_scope_gap_row_counts_as_release(self):
        # COORD-009 修订 B：接受角色无 docs/reviews/* 写权限，其改标 SCOPE_GAP 的
        # release 是账本「范围外已知缺陷」中状态恰为 RELEASED_SCOPE_GAP 的行。
        review = {"P1-M0-001.md": "# P1-M0-001\n- blocks_consuming_gate: F17\n"}
        ledger_head = (
            "# ledger\n\n## 范围外已知缺陷（SCOPE_GAP 账本，COORD-009）\n\n"
            "| Work ID | Finding | 来源（复核文件/轮次） | 依据 | 裁定日期 | 状态 |\n"
            "|---|---|---|---|---|---|\n"
        )
        released = ledger_head + (
            "| `P1-M0-001` | F17 | docs/reviews/P1-M0-001.md R2@m0 | SCOPE_GAP | 2026-09-03 | `RELEASED_SCOPE_GAP` |\n"
        )
        self.assertEqual(
            violations_for(PASS_STATUS, review_files=review, ledger_text=released), []
        )
        # OPEN 记债不是 release；另一个 work ID 的行也不是。
        still_open = ledger_head + (
            "| `P1-M0-001` | F17 | docs/reviews/P1-M0-001.md R2@m0 | SCOPE_GAP | 2026-09-03 | `OPEN` |\n"
            "| `P1-OTHER-001` | F17 | docs/reviews/P1-OTHER-001.md R1@x | SCOPE_GAP | 2026-09-03 | `RELEASED_SCOPE_GAP` |\n"
        )
        joined = "\n".join(
            violations_for(PASS_STATUS, review_files=review, ledger_text=still_open)
        )
        self.assertIn("F17", joined)
        self.assertIn("RELEASED_SCOPE_GAP", joined)

    def test_consuming_gate_scan_skips_readme_prescreen_and_fences(self):
        # 模板示例（README、预筛、围栏代码块）不得被当成真实的 blocks 行。
        review = {
            "README.md": "blocks_consuming_gate: F1\n",
            "P1-M0-001-prescreen.md": "blocks_consuming_gate: F2\n",
            "P1-M0-001.md": "# P1-M0-001\n```\nblocks_consuming_gate: F3\n```\n"
            "围栏外的普通叙述提到 blocks_consuming_gate: F4 不算机读行。\n",
        }
        self.assertEqual(violations_for(PASS_STATUS, review_files=review), [])

    def test_malformed_handoff_row_is_rejected(self):
        # F5 回归（COORD-007 复核轮 2）：短于表头列数的交接行必须响亮
        # 拒绝，不得静默逃出轨道上限与 Consuming 校验。
        short = PASS_STATUS.replace(
            PAUSED_ROW,
            PAUSED_ROW
            + "\n| Review | `P1-M0-001`@DONE | Re-verify | `IMPLEMENTING` |",
        )
        joined = "\n".join(violations_for(short))
        self.assertIn("畸形", joined)


class LogCompressiblePoolTest(unittest.TestCase):
    # COORD-012 U1（用户签字授权 2026-09-20）+ 同日用户裁定（账本「用户裁定：
    # 无关联条目直接入可压池、Gate board 加终止/暂停明确标识…」）：可压池 ≤300 行
    # 由 check_docs 机械强制；终止与否只看 Gate board `Lifecycle` 列。

    def test_entries_of_ended_items_moved_off_board_are_pooled(self):
        # COORD-013：已终止项整行移入 parked，状态板上无行，其条目按无关联直接
        # 入池；40 条 × 10 行 = 400 行，日期无关。
        doc = with_extra_gate_rows(PASS_STATUS)
        doc += log_entries("P1-CLOSED-001 narrative", days_ago(1), 14)
        doc += log_entries("P1-GONE-002 narrative", days_ago(2), 13)
        doc += log_entries("`P1-GONE-003` narrative", days_ago(3), 13)
        joined = "\n".join(violations_for(doc))
        self.assertIn("可压池", joined)
        self.assertIn("超过上限 300 行", joined)
        self.assertIn("docs/status-history.md", joined)
        # 恰好 300 行时零违规（上限含等号）。
        within = with_extra_gate_rows(PASS_STATUS).replace(
            "### 2026-08-12 — decision one\n\nBody.\n", ""
        )
        within += log_entries("P1-CLOSED-001 narrative", days_ago(1), 30)
        self.assertEqual(violations_for(within), [])

    def test_entries_linked_to_active_or_paused_work_items_are_protected(self):
        for work_id in ("P1-ACTIVE-001", "P1-PAUSED-001"):
            doc = with_extra_gate_rows(PASS_STATUS)
            doc += log_entries(f"{work_id} narrative", "2026-08-01", 40)
            self.assertEqual(violations_for(doc), [], msg=work_id)
        # 多 ID 标题只要有一个 work item 非 ENDED 即整条不可压（保守方向）。
        mixed = with_extra_gate_rows(PASS_STATUS)
        mixed += log_entries("P1-CLOSED-001 + P1-PAUSED-001 narrative", "2026-08-01", 40)
        self.assertEqual(violations_for(mixed), [])

    def test_unlinked_entries_enter_the_pool_regardless_of_date(self):
        # 用户裁定 2026-09-20：取消 7 天兜底——无关联 work ID 的条目即使是今天
        # 写的（已提交）也直接入池；关联判据 = 标题含完整 Work ID，子串不算。
        recent = PASS_STATUS + log_entries("process note", days_ago(0), 40)
        joined = "\n".join(violations_for(recent))
        self.assertIn("可压池", joined)
        self.assertIn("超过上限 300 行", joined)
        substring = with_extra_gate_rows(PASS_STATUS)
        substring += log_entries("P1-ACTIVE-0010 narrative", days_ago(0), 40)
        self.assertIn("可压池", "\n".join(violations_for(substring)))

    def test_entries_new_in_this_batch_are_excluded_until_committed(self):
        # (i) 本批次新写 = 工作树里 HEAD 尚无的条目：提交前不计入可压池，
        # 提交后即计入（阈值生效即处置，与分节上限同机制）。
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "core.hooksPath", "tools/githooks"], cwd=root, check=True
            )
            write_status_repo(root, PASS_STATUS, review_ids=("P1-M0-001",))
            self.assertEqual(collect_violations(root), [])
            subprocess.run([*git, "add", "-A"], cwd=root, check=True)
            subprocess.run([*git, "commit", "-q", "-m", "base"], cwd=root, check=True)
            grown = PASS_STATUS + log_entries("P1-CLOSED-001 narrative", days_ago(1), 40)
            (root / "docs" / "current-status.md").write_text(grown, encoding="utf-8")
            self.assertEqual(collect_violations(root), [])
            subprocess.run([*git, "commit", "-q", "-am", "grow"], cwd=root, check=True)
            joined = "\n".join(collect_violations(root))
            self.assertIn("可压池", joined)

    def test_heading_date_is_not_parsed_any_more(self):
        # 日期判据取消后，合并条目 `YYYY-MM-DD/DD` 与无日期标题都只按行数计入，
        # 不再有格式拒绝。
        ranged = PASS_STATUS + log_entries("P1-CLOSED-001 merged", "2026-09-04/05", 40)
        self.assertIn("可压池", "\n".join(violations_for(ranged)))
        undated = PASS_STATUS + "### 未标日期的条目\n\nBody.\n"
        self.assertEqual(violations_for(undated), [])

    def test_lifecycle_column_is_required_and_closed_set(self):
        # 用户裁定 2026-09-20：终止与否必须由 Gate board `Lifecycle` 列明示
        # （ACTIVE/PAUSED/ENDED）；缺列或非闭集值 fail-closed 拒绝，且该行
        # 关联的条目按未终止保护，不进可压池。
        missing = without_lifecycle_column(PASS_STATUS)
        joined = "\n".join(violations_for(missing))
        self.assertIn("Lifecycle", joined)
        bad_value = PASS_STATUS.replace("| `DONE` | `ACTIVE` |", "| `DONE` | `FINISHED` |")
        bad_value += log_entries("P1-M0-001 narrative", days_ago(1), 40)
        joined = "\n".join(violations_for(bad_value))
        self.assertIn("Lifecycle", joined)
        self.assertIn("FINISHED", joined)
        self.assertNotIn("可压池", joined)

    def test_status_history_is_never_scanned(self):
        # COORD-012 U3：docs/status-history.md 是单向沉淀池，不是事实源；
        # 其内容（伪 commit ID、blocks 机读行、超长分节）不得触发任何检查。
        history = (
            "# history\n\n## Current state\n\n" + "filler line\n" * 200
            + "\n- blocks_consuming_gate: F99\n- candidate `abcdef1`\n"
        )
        self.assertEqual(violations_for(PASS_STATUS, history_text=history), [])


def padded(row: str, marker: str, total_bytes: int) -> str:
    """把 row 中的 marker 后补 x，使整行恰好 total_bytes 字节（UTF-8）。"""
    extra = total_bytes - len(row.encode("utf-8"))
    assert extra >= 0, (row, total_bytes)
    return row.replace(marker, marker + "x" * extra, 1)


PAUSED_BOARD_ANCHOR = "| `P1-M7-DEPLOY-001` | Deployment"


def committed_repo(root: Path, status_text: str) -> list[str]:
    """在 root 建 git 仓库并提交 status_text，返回 git 命令前缀。"""
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "core.hooksPath", "tools/githooks"], cwd=root, check=True)
    write_status_repo(root, status_text, review_ids=("P1-M0-001",))
    subprocess.run([*git, "add", "-A"], cwd=root, check=True)
    subprocess.run([*git, "commit", "-q", "-m", "base"], cwd=root, check=True)
    return git


class RelayCostTest(unittest.TestCase):
    # COORD-013（用户直接授权 2026-09-21）：状态板只装当前工作、交接一件事只写
    # 一处——ENDED 行移入 docs/parked-status.md，PAUSED 行与暂停交接行压成一行，
    # 改动过的活跃行与新 Log 条目有字节上限，结构节总字节有稳态上限。

    def test_ended_rows_are_not_kept_on_the_board(self):
        doc = PASS_STATUS.replace(
            PAUSED_BOARD_ANCHOR, CLOSED_GATE_ROW + "\n" + PAUSED_BOARD_ANCHOR
        )
        joined = "\n".join(violations_for(doc))
        self.assertIn("P1-CLOSED-001", joined)
        self.assertIn("docs/parked-status.md", joined)

    def test_paused_gate_row_byte_cap(self):
        at_cap = padded(PAUSED_GATE_ROW, "Paused work", 400)
        ok = PASS_STATUS.replace(PAUSED_BOARD_ANCHOR, at_cap + "\n" + PAUSED_BOARD_ANCHOR)
        self.assertEqual(violations_for(ok), [])
        over = padded(PAUSED_GATE_ROW, "Paused work", 401)
        bad = PASS_STATUS.replace(PAUSED_BOARD_ANCHOR, over + "\n" + PAUSED_BOARD_ANCHOR)
        joined = "\n".join(violations_for(bad))
        self.assertIn("P1-PAUSED-001", joined)
        self.assertIn("400", joined)

    def test_paused_handoff_row_byte_cap(self):
        ok = PASS_STATUS.replace(PAUSED_ROW, padded(PAUSED_ROW, "Hold", 300))
        self.assertEqual(violations_for(ok), [])
        bad = PASS_STATUS.replace(PAUSED_ROW, padded(PAUSED_ROW, "Hold", 301))
        joined = "\n".join(violations_for(bad))
        self.assertIn("P1-M7-DEPLOY-001", joined)
        self.assertIn("300", joined)

    def test_changed_active_rows_byte_cap(self):
        # 只查本提交改动过的活跃行：HEAD 中逐字存在的超长行不拦（存量不回溯），
        # 一经改写即须 ≤ 800 B。
        gate_row = (
            "| `P1-M0-001` | Baseline | `PASS` (`docs/reviews/P1-M0-001.md`) "
            "| `PASS_8_OF_8` | `DONE` | `ACTIVE` |"
        )
        long_gate = padded(gate_row, "Baseline", 900)
        long_handoff = padded(ACTIVE_ROW, "Confirm closure", 900)
        base = PASS_STATUS.replace(gate_row, long_gate).replace(ACTIVE_ROW, long_handoff)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            committed_repo(root, base)
            self.assertEqual(collect_violations(root), [])
            edited = base.replace(long_gate, long_gate.replace("Baselinex", "BaselineY", 1))
            edited = edited.replace(
                long_handoff, long_handoff.replace("Confirm closurex", "Confirm closureY", 1)
            )
            (root / "docs" / "current-status.md").write_text(edited, encoding="utf-8")
            joined = "\n".join(collect_violations(root))
            self.assertIn("Gate board", joined)
            self.assertIn("Active handoffs", joined)
            self.assertIn("800", joined)
            shrunk = base.replace(long_gate, padded(gate_row, "Baseline", 800))
            shrunk = shrunk.replace(long_handoff, padded(ACTIVE_ROW, "Confirm closure", 800))
            (root / "docs" / "current-status.md").write_text(shrunk, encoding="utf-8")
            self.assertEqual(collect_violations(root), [])

    def test_new_log_entry_byte_cap(self):
        heading = "### 2026-09-21 — P1-M0-001 relay note"

        def with_entry(total_bytes: int) -> str:
            body = "x" * (total_bytes - len((heading + "\n\n").encode("utf-8")))
            return PASS_STATUS.replace(
                "## Log\n\n", "## Log\n\n" + heading + "\n\n" + body + "\n\n", 1
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git = committed_repo(root, PASS_STATUS)
            (root / "docs" / "current-status.md").write_text(with_entry(600), encoding="utf-8")
            self.assertEqual(collect_violations(root), [])
            (root / "docs" / "current-status.md").write_text(with_entry(601), encoding="utf-8")
            joined = "\n".join(collect_violations(root))
            self.assertIn("600", joined)
            self.assertIn("relay note", joined)
            # 提交后不再是本批次新写，存量不回溯。
            subprocess.run([*git, "commit", "-q", "-am", "entry"], cwd=root, check=True)
            self.assertEqual(collect_violations(root), [])

    def test_structure_bytes_cap(self):
        def with_filler(count: int) -> str:
            filler = ("- " + "x" * 698 + "\n") * count
            return PASS_STATUS.replace(CURRENT_STATE_BULLET, filler)

        self.assertEqual(violations_for(with_filler(40)), [])
        joined = "\n".join(violations_for(with_filler(44)))
        self.assertIn("30000", joined)
        # `## Log` 之后的内容不计入结构节。
        self.assertEqual(violations_for(OVERSIZED_STATUS), [])

    def test_parked_ended_table_done_rows_need_evidence(self):
        header = (
            "# parked\n\n## 已终止（ENDED）\n\n"
            "| Work ID | Scope | Independent review | Unity/hardware | Overall | Lifecycle |\n"
            "|---|---|---|---|---|---|\n"
        )
        bad = header + "| `P1-OLD-001` | Old | pending | pending | `DONE` | `ENDED` |\n"
        joined = "\n".join(violations_for(PASS_STATUS, parked_text=bad))
        self.assertIn("P1-OLD-001", joined)
        self.assertIn("parked-status.md", joined)
        good = header + "| `P1-OLD-001` | Old | `PASS` | `UNITY_NA` | `DONE` | `ENDED` |\n"
        self.assertEqual(violations_for(PASS_STATUS, parked_text=good), [])

    def test_rest_of_parked_file_is_not_scanned(self):
        parked = (
            "# parked\n\n## 暂停（PAUSED）\n\n"
            "| Work ID | Scope | Independent review | Unity/hardware | Overall | Lifecycle |\n"
            "|---|---|---|---|---|---|\n"
            "| `P1-X-001` | x | pending | pending | `DONE` | `ENDED` |\n\n"
            + "filler line\n" * 200
            + "- blocks_consuming_gate: F99\n- candidate `abcdef1`\n"
        )
        self.assertEqual(violations_for(PASS_STATUS, parked_text=parked), [])


if __name__ == "__main__":
    unittest.main()
