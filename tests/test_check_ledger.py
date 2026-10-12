from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import check_ledger as cl

TOOL_PATH = Path(cl.__file__).resolve()
WORK_ID = "W-001"
DECISION_TITLE = "决策信封：W-001 D 类代拍"
EXECUTION_TITLE = "执行信封：W-001 K4 阶段"
LEDGER_HEAD = "# 用户关键授权账本\n\n格式略（合成夹具）。\n"


def run_git(args, cwd):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def decision_envelope_entry(title=DECISION_TITLE, work_id=WORK_ID, date="2026-09-20",
                            at="2026-09-20T08:00:00Z", classes="[D1, D4]",
                            block_override=None):
    block = block_override if block_override is not None else (
        "supervisor_decision_envelope:\n"
        "  enabled: true\n"
        f"  classes: {classes}\n"
        "  expires_at: 2026-12-31\n"
        "  veto_window_days: 7\n"
    )
    return (f"\n---\n\n## {date} {work_id} — {title}\n\n"
            f"- 用户原话：\"合成\"。\n- at: {at}\n- 代录会话: 合成\n\n{block}")


def execution_envelope_entry(title=EXECUTION_TITLE, work_id=WORK_ID, date="2026-09-20",
                             at="2026-09-20T08:00:00Z", max_increment="{API 次数: 5}",
                             max_total="{API 次数: 10}", expires="K4",
                             block_override=None):
    block = block_override if block_override is not None else (
        "supervisor_subdelegation:\n"
        "  enabled: true\n"
        f"  max_increment: {max_increment}\n"
        f"  max_total: {max_total}\n"
        f"  expires_at: {expires}\n"
    )
    return (f"\n---\n\n## {date} {work_id} — {title}\n\n"
            f"- 用户原话：\"合成\"。\n- at: {at}\n- 代录会话: 合成\n\n{block}")


def _filter_lines(lines, drop):
    return [l for l in lines if not any(l.startswith(f"- {key}:") for key in drop)]


def sub_entry(title, precheck, env_title=EXECUTION_TITLE, work_id=WORK_ID,
              date="2026-09-21", at="2026-09-21T09:00:00Z",
              increment="{API 次数: 2}", request_id="W-001:abcd1234:SUB:1",
              counter_key=None, drop=(), extra_lines=""):
    counter_key = counter_key if counter_key is not None else request_id
    lines = _filter_lines([
        f"- at: {at}",
        "- delegated_class: SUB",
        f"- cites_execution_envelope: {env_title}",
        "- decision: 批准追加",
        "- reason: 合成",
        f"- increment: {increment}",
        f"- request_id: {request_id}",
        f"- counter_key: {counter_key}",
        f"- precheck_head: {precheck}",
    ], drop)
    body = "\n".join(lines)
    return f"\n---\n\n## {date} {work_id} — supervisor 代拍：{title}\n\n{body}\n{extra_lines}"


def d_class_entry(title, precheck, cls="D4", env_title=DECISION_TITLE, work_id=WORK_ID,
                  date="2026-09-21", at="2026-09-21T09:00:00Z",
                  counter_key="W-001:D4:1", veto_until="2026-09-28T09:00:00Z",
                  drop=(), extra_lines=""):
    lines = _filter_lines([
        f"- at: {at}",
        f"- delegated_class: {cls}",
        f"- cites_decision_envelope: {env_title}",
        "- decision: 选推荐项",
        "- reason: 合成",
        f"- counter_key: {counter_key}",
        f"- precheck_head: {precheck}",
        f"- veto_until: {veto_until}",
    ], drop)
    body = "\n".join(lines)
    return f"\n---\n\n## {date} {work_id} — supervisor 代拍：{title}\n\n{body}\n{extra_lines}"


def d1_entry(title, precheck, round_name="D2", now=2, prev=4, work_id=WORK_ID,
             date="2026-09-22", at="2026-09-22T09:00:00Z", counter_key=None, drop=()):
    counter_key = counter_key or f"{work_id}:D1:{round_name}"
    lines = _filter_lines([
        f"- at: {at}",
        "- delegated_class: D1",
        f"- cites_decision_envelope: {DECISION_TITLE}",
        "- decision: 选 (a) 保留范围",
        f"- counter_key: {counter_key}",
        f"- precheck_head: {precheck}",
        "- veto_until: 2026-09-29T09:00:00Z",
        f"- round: {round_name}",
        f"- open_items_now: {now}",
        f"- open_items_prev: {prev}",
    ], drop)
    body = "\n".join(lines)
    return f"\n---\n\n## {date} {work_id} — supervisor 代拍：{title}\n\n{body}\n"


def revoke_entry(target=EXECUTION_TITLE, work_id=WORK_ID, date="2026-09-21",
                 at="2026-09-21T15:00:00Z"):
    return (f"\n---\n\n## {date} {work_id} — 用户撤回信封：{target}\n\n"
            f"- at: {at}\n- supervisor_envelope_revoke: {target}\n")


def board(status="IMPLEMENTING", lifecycle="ACTIVE", work_id=WORK_ID, extra_log=""):
    return f"""# Current status

## Gate board

| Work ID | Scope | Design | Implementation/auto evidence | Independent review | Unity/hardware | Overall | Lifecycle |
|---|---|---|---|---|---|---|---|
| `{work_id}` | 合成 | 合成 | 合成 | `N/A` | `N/A` | `ACCEPTED` | `{lifecycle}` |

## Active handoffs

| Owner/next role | Work ID | Requested action | Scope | Progress | Status | Consuming | Return to |
|---|---|---|---|---|---|---|---|
| Implementation | `{work_id}`@ACCEPTED | 合成 | — | — | `{status}` | no | — |

## Log
{extra_log}
"""


def proposal(*open_items, work_id=WORK_ID):
    parts = [f"# {work_id} — 合成提案\n"]
    for index, value in enumerate(open_items, 1):
        parts.append(f"\n### D{index} 接受侧裁定\n\n裁定原文（合成）。\n")
        if value is not None:
            parts.append(f"\nopen_items: {value}\n")
    return "".join(parts)


def proposal_newest_first(r1, r2, work_id=WORK_ID):
    # 与真实提案同布局（BC-14 / R1@落地 复判）：`### D<n>` 最新在上，其上另有
    # 一个含 `open_items: none` 的非 D 节；D2 节内含 `####` 残留子节。
    return (f"# {work_id} — 合成提案\n"
            "\n## Codex review decision\n"
            "\n### 接受后修订 1 审核（不新增 D 轮）\n\n审核原文（合成）。\n\nopen_items: none\n"
            "\n### D2 接受侧裁定\n\n裁定原文（合成）。\n"
            "\n#### AD2-1 — 残留子节\n\n残留原文（合成）。\n"
            f"\nopen_items: {r2}\n"
            "\n### D1 历史裁定\n\n裁定原文（合成）。\n"
            f"\nopen_items: {r1}\n")


def structural(text):
    return cl.structural_errors(cl.parse_entries(text))


class StructuralTests(unittest.TestCase):
    """§5.4 失败关闭清单逐项一例 + §5.5 全序/撤销/到期（纯文本判定）。"""

    def base(self):
        return LEDGER_HEAD + decision_envelope_entry() + execution_envelope_entry()

    def test_unknown_machine_key_rejected(self):
        text = self.base() + sub_entry("t", "a" * 40, extra_lines="- bogus_key: 1\n")
        self.assertTrue(any("未知机读键" in e for e in structural(text)))

    def test_negative_and_non_integer_increment_rejected(self):
        for bad in ("{API 次数: -1}", "{API 次数: 1.5}", "{API 次数: nan}"):
            with self.subTest(bad=bad):
                text = self.base() + sub_entry("t", "a" * 40, increment=bad)
                self.assertTrue(any("increment" in e for e in structural(text)))

    def test_missing_required_field_rejected(self):
        text = self.base() + sub_entry("t", "a" * 40, drop=("request_id",))
        self.assertTrue(any("request_id" in e for e in structural(text)))

    def test_duplicate_title_rejected(self):
        text = (self.base()
                + sub_entry("同一标题", "a" * 40, request_id="W-001:abcd1234:SUB:1")
                + sub_entry("同一标题", "b" * 40, at="2026-09-21T10:00:00Z",
                            request_id="W-001:abcd1234:SUB:2"))
        self.assertTrue(any("同标题重复条目" in e for e in structural(text)))

    def test_d_class_citing_execution_envelope_rejected(self):
        text = self.base() + d_class_entry("t", "a" * 40, env_title=EXECUTION_TITLE)
        self.assertTrue(any("D 类引用执行信封" in e for e in structural(text)))

    def test_sub_citing_decision_envelope_rejected(self):
        text = self.base() + sub_entry("t", "a" * 40, env_title=DECISION_TITLE)
        self.assertTrue(any("SUB 引用决策信封" in e for e in structural(text)))

    def test_cross_work_item_envelope_rejected(self):
        text = self.base() + sub_entry("t", "a" * 40, work_id="W-002")
        self.assertTrue(any("串用他工作项信封" in e for e in structural(text)))

    def test_class_not_in_envelope_classes_rejected(self):
        text = self.base() + d_class_entry("t", "a" * 40, cls="D6")
        self.assertTrue(any("不在被引信封 classes" in e for e in structural(text)))

    def test_sub_dimension_not_in_block_rejected(self):
        text = self.base() + sub_entry("t", "a" * 40, increment="{GPU·h: 1}")
        self.assertTrue(any("维度不在块内" in e for e in structural(text)))

    def test_increment_exceeds_max_increment_rejected(self):
        text = self.base() + sub_entry("t", "a" * 40, increment="{API 次数: 6}")
        self.assertTrue(any("超 max_increment" in e for e in structural(text)))

    def test_duplicate_request_id_rejected(self):
        text = (self.base()
                + sub_entry("第一条", "a" * 40, request_id="W-001:abcd1234:SUB:1")
                + sub_entry("第二条", "b" * 40, at="2026-09-21T10:00:00Z",
                            request_id="W-001:abcd1234:SUB:1",
                            counter_key="W-001:abcd1234:SUB:1b"))
        self.assertTrue(any("同一 request_id" in e for e in structural(text)))

    def test_duplicate_counter_key_rejected(self):
        text = (self.base()
                + d_class_entry("第一条", "a" * 40)
                + d_class_entry("第二条", "b" * 40, at="2026-09-21T10:00:00Z"))
        self.assertTrue(any("counter_key" in e for e in structural(text)))

    def test_envelope_missing_expires_at_rejected(self):
        block = ("supervisor_subdelegation:\n"
                 "  enabled: true\n"
                 "  max_increment: {API 次数: 5}\n"
                 "  max_total: {API 次数: 10}\n")
        text = LEDGER_HEAD + execution_envelope_entry(block_override=block)
        self.assertTrue(any("缺必填 expires_at" in e for e in structural(text)))

    def test_d_class_missing_veto_until_rejected(self):
        text = self.base() + d_class_entry("t", "a" * 40, drop=("veto_until",))
        self.assertTrue(any("veto_until" in e for e in structural(text)))

    def test_sub_with_veto_until_rejected(self):
        text = self.base() + sub_entry(
            "t", "a" * 40, extra_lines="- veto_until: 2026-09-29T09:00:00Z\n")
        self.assertTrue(any("SUB 不得写 veto_until" in e for e in structural(text)))

    def test_d1_missing_round_and_open_items_rejected(self):
        text = self.base() + d1_entry("t", "a" * 40, drop=("round", "open_items_now"))
        errors = structural(text)
        self.assertTrue(any("round" in e for e in errors))
        self.assertTrue(any("open_items_now" in e for e in errors))

    def test_counterexample1_entry_before_revoke_passes(self):
        # §5.5 反例 1：同日 09:00 代拍、15:00 撤销 → 旧条目仍合法。
        text = (self.base() + sub_entry("旧代拍", "a" * 40) + revoke_entry())
        self.assertEqual(structural(text), [])

    def test_new_entry_after_revoke_rejected(self):
        text = (self.base() + sub_entry("旧代拍", "a" * 40) + revoke_entry()
                + sub_entry("撤销后新代拍", "b" * 40, at="2026-09-21T16:00:00Z",
                            request_id="W-001:abcd1234:SUB:2"))
        self.assertTrue(any("被撤销" in e for e in structural(text)))

    def test_counterexample2_entry_before_signing_rejected(self):
        # §5.5 反例 2：09:00 代拍、11:00 才签发信封 → 不合法（同日不能靠日期放过）。
        text = (LEDGER_HEAD
                + execution_envelope_entry(date="2026-09-21", at="2026-09-21T11:00:00Z")
                + sub_entry("早于签发的代拍", "a" * 40))
        self.assertTrue(any("签发不先于代拍" in e for e in structural(text)))

    def test_old_entry_survives_later_date_expiry(self):
        # 到期后的旧条目通过；到期日之后的新条目拒绝。
        text = (LEDGER_HEAD
                + execution_envelope_entry(expires="[K4, 2026-09-21]")
                + sub_entry("到期日当天的旧代拍", "a" * 40))
        self.assertEqual(structural(text), [])
        text += sub_entry("到期后的新代拍", "b" * 40, date="2026-09-22",
                          at="2026-09-22T09:00:00Z", request_id="W-001:abcd1234:SUB:2")
        self.assertTrue(any("到期" in e for e in structural(text)))

    def test_cumulative_exceeds_max_total_rejected(self):
        text = self.base()
        for index in range(3):
            text += sub_entry(f"第{index + 1}笔", "a" * 40,
                              at=f"2026-09-21T0{9 + index}:00:00Z",
                              increment="{API 次数: 4}",
                              request_id=f"W-001:abcd1234:SUB:{index + 1}")
        self.assertTrue(any("累计追加超 max_total" in e for e in structural(text)))

    def test_veto_entry_checks(self):
        veto = ("\n---\n\n## 2026-09-23 W-001 — 用户否决代拍：{target}\n\n- at: {at}\n")
        with self.subTest(case="unknown target"):
            text = self.base() + d_class_entry("某代拍", "a" * 40)
            text += veto.format(target="supervisor 代拍：不存在的代拍",
                                at="2026-09-23T09:00:00Z")
            self.assertTrue(any("否决目标" in e for e in structural(text)))
        with self.subTest(case="after veto window"):
            text = self.base() + d_class_entry("某代拍", "a" * 40,
                                               veto_until="2026-09-22T09:00:00Z")
            text += veto.format(target="supervisor 代拍：某代拍",
                                at="2026-09-23T09:00:00Z")
            self.assertTrue(any("否决窗口" in e for e in structural(text)))

    def test_sub_citing_global_envelope_rejected(self):
        # R1-2 / BC-5：SUB 引用的执行信封 work ID 须等于条目 work ID，`全局` 不放行。
        text = (LEDGER_HEAD + execution_envelope_entry(work_id="全局")
                + sub_entry("引全局信封的 SUB", "a" * 40))
        self.assertTrue(any("串用他工作项信封" in e for e in structural(text)))

    def test_same_at_upper_entry_is_newer(self):
        # R1-3 / BC-5 §5.5：at: 与日期都相同时按文件位置，靠上者更新（账本最新在前）。
        at = "2026-09-21T09:00:00Z"
        envelope = execution_envelope_entry(date="2026-09-21", at=at)
        entry = sub_entry("同 at 的代拍", "a" * 40, at=at)
        with self.subTest(case="envelope above entry → envelope newer → rejected"):
            text = LEDGER_HEAD + envelope + entry
            self.assertTrue(any("签发不先于代拍" in e for e in structural(text)))
        with self.subTest(case="envelope below entry → envelope older → passes"):
            text = LEDGER_HEAD + entry + envelope
            self.assertEqual(structural(text), [])

    def test_veto_missing_at_rejected(self):
        # R1-4 / BC-15：否决条目 at: 必填，缺失即拒绝，不得跳过否决窗口判定。
        text = self.base() + d_class_entry("某代拍", "a" * 40,
                                           veto_until="2026-09-22T09:00:00Z")
        text += ("\n---\n\n## 2026-09-30 W-001 — 用户否决代拍：supervisor 代拍：某代拍\n\n"
                 "- 代录会话: 合成\n")
        self.assertTrue(any("缺必填 at:" in e for e in structural(text)))

    def test_valid_sample_passes(self):
        text = (self.base()
                + sub_entry("合规 SUB", "a" * 40)
                + d_class_entry("合规 D4", "b" * 40, at="2026-09-21T10:00:00Z",
                                counter_key="W-001:D4:2"))
        self.assertEqual(structural(text), [])

    def test_non_utc_offset_at_rejected(self):
        # §5.4：at: 只接受 UTC（Z 或 +00:00），其他偏移即使可换算也拒绝。
        for bad in ("2026-09-21T17:00:00+08:00", "2026-09-21T04:00:00-05:00",
                    "2026-09-21T09:00:00+0000", "2026-09-21T09:00:00"):
            with self.subTest(at=bad):
                text = self.base() + sub_entry("t", "a" * 40, at=bad)
                self.assertTrue(any("at: 不是" in e for e in structural(text)))
        for good in ("2026-09-21T09:00:00Z", "2026-09-21T09:00:00+00:00"):
            with self.subTest(at=good):
                text = self.base() + sub_entry("t", "a" * 40, at=good)
                self.assertEqual(structural(text), [])

    def test_legacy_stock_entries_untouched(self):
        # 现存历史条目（无 at:、无机读行）必须判为合法存量。
        legacy = (LEDGER_HEAD +
                  "\n---\n\n## 2026-09-25 COORD-015 — 用户处置 D5 审查残留 AD5-1：保留范围\n\n"
                  "- 用户原话（逐字）：\"(a) 修正 AD5-1 出 D6（推荐）\"。\n"
                  "- 授权范围：按 workflow §4.2 (a) 保留范围。\n"
                  "- 信封：无。\n"
                  "- 代录角色/会话：Ideation（2026-09-25）。\n")
        self.assertEqual(structural(legacy), [])


class RepoCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        run_git(["init", "-q"], self.root)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def stage(self, *rels):
        run_git(["add", *rels], self.root)

    def commit(self, message):
        run_git(["add", "-A"], self.root)
        run_git(["commit", "-q", "-m", message], self.root)

    def head(self):
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root,
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def base_ledger(self):
        return LEDGER_HEAD + decision_envelope_entry() + execution_envelope_entry()

    def init_repo(self, board_text=None, proposal_text=None, ledger=None, message="init"):
        self.write("docs/current-status.md", board_text if board_text is not None else board())
        self.write("docs/proposals/W-001-synthetic.md",
                   proposal_text if proposal_text is not None
                   else proposal("AD1-1, AD1-2, AD1-3, AD1-4", "AD2-1, AD2-2"))
        self.write("docs/authorizations.md", ledger if ledger is not None else self.base_ledger())
        self.commit(message)

    def precommit_errors(self):
        return cl.check_precommit(self.root)

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(TOOL_PATH), "--root", str(self.root), *args],
            capture_output=True, text=True, check=False)


class PrecommitViewTests(RepoCase):
    """§5.6 快照/首父/X 判定与真实 pre-commit 路径（临时 git 仓库）。"""

    def stage_sub(self, precheck, **kwargs):
        self.write("docs/authorizations.md",
                   self.base_ledger() + sub_entry("一笔 SUB", precheck, **kwargs))
        self.stage("docs/authorizations.md")

    def test_non_ancestor_precheck_rejected(self):
        self.init_repo()
        self.stage_sub("0" * 40)
        self.commit("W-001 入账非祖先快照")
        self.assertTrue(any("首父" in e for e in self.precommit_errors()))

    def test_precheck_not_first_parent_rejected(self):
        self.init_repo()
        first = self.head()
        self.write("docs/current-status.md", board(extra_log="\n### 2026-09-21 — 合成日志\n"))
        self.commit("W-001 推进一行日志")
        self.stage_sub(first)
        self.commit("W-001 入账旧快照")
        self.assertTrue(any("首父" in e for e in self.precommit_errors()))

    def test_stale_snapshot_p_x_e_rejected(self):
        # §5.6 反例：线性历史 P → X → E、precheck_head = P → 拒绝。
        self.init_repo()
        point_p = self.head()
        self.write("docs/current-status.md", board(lifecycle="PAUSED"))
        self.commit("W-001 暂停（X）")
        self.stage_sub(point_p)
        self.commit("W-001 入账 E")
        self.assertTrue(self.precommit_errors())

    def test_entry_committed_before_x_passes(self):
        self.init_repo()
        self.stage_sub(self.head())
        self.commit("W-001 入账 E0")
        self.write("docs/current-status.md", board(lifecycle="PAUSED"))
        self.commit("W-001 暂停（X 在 E0 之后）")
        self.assertEqual(self.precommit_errors(), [])

    def test_reapply_after_expiry_and_resume_rejected(self):
        # 到期 → 恢复 → 再申请：X 一旦存在永久生效。
        self.init_repo()
        self.write("docs/current-status.md", board(lifecycle="PAUSED"))
        self.commit("W-001 暂停（X）")
        self.write("docs/current-status.md", board())
        self.commit("W-001 恢复")
        self.stage_sub(self.head())
        self.assertTrue(any("已失效" in e for e in self.precommit_errors()))

    def test_valid_first_entry_passes(self):
        # 真实 pre-commit 路径：合法首次入账（含首次签发信封）通过。
        self.init_repo(ledger=LEDGER_HEAD)
        self.stage_sub(self.head())
        self.assertEqual(self.precommit_errors(), [])
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_first_entry_precheck_not_head_rejected(self):
        self.init_repo(ledger=LEDGER_HEAD)
        self.stage_sub("0" * 40)
        self.assertTrue(any("precheck_head == HEAD" in e for e in self.precommit_errors()))

    def test_envelope_signed_at_stop_point_x_equals_s(self):
        # 签发时已在停点：X = S，引用它的条目一律拒绝。
        self.init_repo(board_text=board(status="AWAITING_C1_AT_K4"), ledger=LEDGER_HEAD)
        self.write("docs/authorizations.md",
                   LEDGER_HEAD + execution_envelope_entry())
        self.commit("W-001 签发执行信封（S）")
        signed = self.head()
        start, x = cl.first_invalidation(self.root, WORK_ID, EXECUTION_TITLE)
        self.assertEqual(start, signed)
        self.assertEqual(x, signed)
        result = self.run_cli("--first-invalidation", WORK_ID, "--envelope", EXECUTION_TITLE)
        self.assertEqual(result.returncode, 1)
        self.assertIn(signed, result.stdout)
        self.stage_sub(self.head())
        self.assertTrue(any("已失效" in e for e in self.precommit_errors()))

    def test_historical_rejudgement_consistent_with_post_commit(self):
        self.init_repo()
        self.stage_sub(self.head())
        self.assertEqual(self.precommit_errors(), [])
        self.commit("W-001 入账 SUB")
        self.assertEqual(self.precommit_errors(), [])

    def test_ad5_subject_match_only_log_change_passes(self):
        # AD5-1 例 1：提交主题匹配 ^W-001 C1@K4 但状态板未到期（只改 Log）
        # → 主题不产生 X，SUB 条目提交前通过、提交后复判通过。
        self.init_repo()
        self.write("docs/current-status.md", board(extra_log="\n### 2026-09-21 — 合成日志\n"))
        self.commit("W-001 C1@K4 合成主题（只改 Log）")
        self.stage_sub(self.head())
        self.assertEqual(self.precommit_errors(), [])
        self.commit("W-001 入账 SUB")
        self.assertEqual(self.precommit_errors(), [])

    def test_ad5_subject_match_without_board_change_passes(self):
        # AD5-1 例 2：主题匹配却不改状态板的提交 X′ 不被枚举、不是 X → 两视图均通过。
        self.init_repo()
        self.write("docs/proposals/W-001-synthetic.md",
                   proposal("AD1-1, AD1-2, AD1-3, AD1-4", "AD2-1, AD2-2", "AD3-1"))
        self.commit("W-001 C1@K4 合成主题（不改状态板）")
        self.stage_sub(self.head())
        self.assertEqual(self.precommit_errors(), [])
        self.commit("W-001 入账 SUB")
        self.assertEqual(self.precommit_errors(), [])

    def test_ad5_same_commit_entry_and_expiry_rejected(self):
        # AD5-1 例 3：同一提交既写 SUB 条目又把状态板改到停点
        # → 提交前拒绝（虚拟提交命中）、提交后拒绝（X = commit(E)）。
        self.init_repo()
        self.write("docs/authorizations.md",
                   self.base_ledger() + sub_entry("一笔 SUB", self.head()))
        self.write("docs/current-status.md", board(status="AWAITING_C1_AT_K4"))
        self.stage("docs/authorizations.md", "docs/current-status.md")
        self.assertTrue(any("已失效" in e for e in self.precommit_errors()))
        self.commit("W-001 同提交入账与到期")
        self.assertTrue(self.precommit_errors())


class D1Tests(RepoCase):
    """COORD-015 BC-12/BC-14 + COORD-016 §2.1/BC-1：D1 按提案 open_items: 行非递增、每提案累计 ≤ 3。"""

    def init_d1(self, proposal_text=None):
        self.init_repo(proposal_text=proposal_text)

    def stage_d1(self, **kwargs):
        self.write("docs/authorizations.md",
                   self.base_ledger() + d1_entry("D1 代拍", self.head(), **kwargs))
        self.stage("docs/authorizations.md")

    def test_d1_decreasing_and_consistent_passes(self):
        self.init_d1()
        self.stage_d1(now=2, prev=4)
        self.assertEqual(self.precommit_errors(), [])

    def test_d1_flat_passes(self):
        # COORD-016 §2.1 / BC-1：r(n) == r(n−1)（持平）通过（修前按严格递减拒绝）。
        self.init_d1(proposal_text=proposal("AD1-1, AD1-2", "AD2-1, AD2-2"))
        self.stage_d1(now=2, prev=2)
        self.assertEqual(self.precommit_errors(), [])

    def test_d1_increase_rejected(self):
        # COORD-016 §2.1：r(n) > r(n−1)（残留数增加）拒绝。
        self.init_d1(proposal_text=proposal("AD1-1, AD1-2", "AD2-1, AD2-2, AD2-3"))
        self.stage_d1(now=3, prev=2)
        errors = self.precommit_errors()
        self.assertTrue(any("残留数增加（3 > 2）" in e for e in errors), msg=errors)

    def test_d1_third_passes_fourth_rejected_same_work_id(self):
        # COORD-016 §2.1 / BC-1：同 work ID 第 3 条 D1 通过、第 4 条拒绝（每提案累计 ≤ 3）。
        self.init_d1(proposal_text=proposal(*(["AD-1, AD-2"] * 5)))
        ledger = self.base_ledger()
        for index, round_no in enumerate((2, 3, 4), start=1):
            ledger += d1_entry(f"D1 代拍第 {index} 条", self.head(), round_name=f"D{round_no}",
                               now=2, prev=2, at=f"2026-09-22T0{index}:00:00Z")
            self.write("docs/authorizations.md", ledger)
            self.stage("docs/authorizations.md")
            self.assertEqual(self.precommit_errors(), [], msg=f"第 {index} 条")
            self.commit(f"W-001 入账第 {index} 条 D1")
        ledger += d1_entry("D1 代拍第 4 条", self.head(), round_name="D5",
                           now=2, prev=2, at="2026-09-22T05:00:00Z")
        self.write("docs/authorizations.md", ledger)
        self.stage("docs/authorizations.md")
        errors = self.precommit_errors()
        self.assertTrue(any("累计上限" in e for e in errors), msg=errors)

    def test_d1_vetoed_entries_still_count(self):
        # BC-1：计数含已入账而后被否决的 D1 条目，不因否决返还。
        text = LEDGER_HEAD + decision_envelope_entry()
        for index, round_no in enumerate((2, 3, 4), start=1):
            text += d1_entry(f"D1 第 {index} 条", "a" * 40, round_name=f"D{round_no}",
                             now=2, prev=2, at=f"2026-09-22T0{index}:00:00Z")
        text += ("\n---\n\n## 2026-09-22 W-001 — 用户否决代拍：supervisor 代拍：D1 第 1 条\n\n"
                 "- at: 2026-09-22T01:30:00Z\n")
        self.assertFalse(any("累计上限" in e for e in structural(text)))
        text += d1_entry("D1 第 4 条", "a" * 40, round_name="D5", now=2, prev=2,
                         at="2026-09-22T05:00:00Z")
        self.assertTrue(any("累计上限" in e for e in structural(text)))

    def test_d1_missing_open_items_line_rejected(self):
        self.init_d1(proposal_text=proposal("AD1-1, AD1-2", None))
        self.stage_d1(now=2, prev=2)
        self.assertTrue(any("open_items" in e for e in self.precommit_errors()))

    def test_d1_second_entry_same_round_rejected(self):
        self.init_d1()
        self.stage_d1(now=2, prev=4)
        self.commit("W-001 入账第一条 D1")
        self.write("docs/authorizations.md",
                   self.base_ledger()
                   + d1_entry("D1 代拍", "a" * 40, now=2, prev=4)
                   + d1_entry("D1 代拍同轮第二条", self.head(), now=2, prev=4))
        self.stage("docs/authorizations.md")
        errors = self.precommit_errors()
        self.assertTrue(any("同一轮第二条 D1" in e or "counter_key" in e for e in errors))

    def test_d1_newest_first_layout_legal_passes(self):
        # R1-1 / BC-14：`### D<n>` 最新在上，r(1)=4 → r(2)=2，条目 now=2/prev=4 → 通过。
        self.init_d1(proposal_text=proposal_newest_first(
            "AD1-1, AD1-2, AD1-3, AD1-4", "AD2-1, AD2-2"))
        self.stage_d1(now=2, prev=4)
        self.assertEqual(self.precommit_errors(), [])

    def test_d1_newest_first_layout_increase_rejected(self):
        # R1-1 / BC-14：r(1)=2 → r(2)=4（增加），条目按文件序写 now=2/prev=4 →
        # 须按节绑定读出 r(2)=4、r(1)=2 并拒绝（COORD-016：残留数增加 4 > 2）。
        self.init_d1(proposal_text=proposal_newest_first(
            "AD1-1, AD1-2", "AD2-1, AD2-2, AD2-3, AD2-4"))
        self.stage_d1(now=2, prev=4)
        errors = self.precommit_errors()
        self.assertTrue(any("残留数增加（4 > 2）" in e for e in errors), msg=errors)

    def test_d1_section_binding_fail_closed(self):
        # BC-14 (3)：标题 0/≥2 行、节内匹配行 0/≥2 行、匹配行非节末 → 拒绝。
        good_d1 = "\n### D1 接受侧裁定\n\n原文。\n\nopen_items: AD1-1, AD1-2, AD1-3\n"
        cases = {
            "no D2 heading": "# W-001\n" + good_d1 + "\n### 其他节\n\nopen_items: AD2-1\n",
            "two D2 headings": ("# W-001\n\n### D2 甲\n\nopen_items: AD2-1\n"
                                "\n### D2 乙\n\nopen_items: AD2-1\n" + good_d1),
            "two lines in section": ("# W-001\n\n### D2 裁定\n\nopen_items: AD2-1\n"
                                     "\nopen_items: AD2-1\n" + good_d1),
            "line not last": ("# W-001\n\n### D2 裁定\n\nopen_items: AD2-1\n"
                              "\n补充说明。\n" + good_d1),
            "D10 is not D1": ("# W-001\n\n### D2 裁定\n\nopen_items: AD2-1\n"
                              "\n### D10 裁定\n\nopen_items: AD10-1, AD10-2\n"),
        }
        for name, text in cases.items():
            with self.subTest(case=name):
                self.fresh_repo()
                self.init_d1(proposal_text=text)
                self.stage_d1(now=1, prev=3)
                self.assertTrue(any("open_items" in e or "### D" in e
                                    for e in self.precommit_errors()))

    def fresh_repo(self):
        # 子用例各用一个新临时仓库。
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        run_git(["init", "-q"], self.root)



D7_TITLE = "决策信封：W-001 D7 代拍"
G_RANGE = "d7_range: g1 in [0.50, 0.80] kind=门值 bc=BC-2"
N_RANGE = "d7_range: n1 in {200, 400} kind=最小样本量 bc=BC-3"


def d7_proposal(status="ACCEPTED", g_range=G_RANGE, n_range=N_RANGE,
                recommends=("d7_recommend: g1 = 0.70", "d7_recommend: n1 = 400"),
                extra_rows=(), d_section_extra=""):
    rows = [
        "| BC-1 | 合成条款。 | 行为 | test:x | BASE | 合成 | 2026-09-26 |",
        f"| BC-2 | 合格门门值合成条款 `{g_range}` | 行为 | test:x | BASE | 合成 | 2026-09-26 |"
        if g_range else "| BC-2 | 合格门门值合成条款 | 行为 | test:x | BASE | 合成 | 2026-09-26 |",
        f"| BC-3 | 最小样本量合成条款 `{n_range}` | 测试覆盖 | test:x | BASE | 合成 | 2026-09-26 |"
        if n_range else "| BC-3 | 最小样本量合成条款 | 测试覆盖 | test:x | BASE | 合成 | 2026-09-26 |",
        *extra_rows,
    ]
    table = "\n".join(rows)
    recs = "\n\n".join(recommends)
    return (f"# W-001 — 合成提案\n\nStatus: {status}（合成）\n\n"
            "## Binding clarifications (BC table)\n\n"
            "| 编号 | 条款 | 复核项 | 证明方式 | 标签 | 依据 | 日期 |\n"
            "|---|---|---|---|---|---|---|\n"
            f"{table}\n\n"
            "## Pending rulings（待裁定）\n\n"
            f"{recs}\n\n"
            "## Codex review decision\n\n"
            f"### D1 接受裁定\n\n裁定原文（合成）。{d_section_extra}\n\nopen_items: none\n")


def d7_envelope(classes="[D1, D4, D7]"):
    return decision_envelope_entry(title=D7_TITLE, classes=classes)


def d7_entry(title, precheck, qid="g1", decision="0.70", range_text=G_RANGE,
             work_id=WORK_ID, date="2026-09-26", at="2026-09-26T09:00:00Z",
             counter_key=None, drop=()):
    counter_key = counter_key or f"{work_id}:D7:{qid}"
    lines = _filter_lines([
        f"- at: {at}",
        "- delegated_class: D7",
        f"- cites_decision_envelope: {D7_TITLE}",
        f"- decision: {decision}",
        f"- question_id: {qid}",
        f"- range: {range_text}",
        f"- counter_key: {counter_key}",
        f"- precheck_head: {precheck}",
        "- veto_until: 2026-10-03T09:00:00Z",
    ], drop)
    body = "\n".join(lines)
    return f"\n---\n\n## {date} {work_id} — supervisor 代拍：{title}\n\n{body}\n"


class D7Tests(RepoCase):
    """COORD-016 §2.2 / BC-2 / BC-3：D7 预注册合同数值按推荐（A2 反例逐条）。"""

    def init_d7(self, proposal_text=None, classes="[D1, D4, D7]"):
        self.init_repo(proposal_text=proposal_text if proposal_text is not None else d7_proposal(),
                       ledger=LEDGER_HEAD + d7_envelope(classes=classes))

    def ledger_with(self, *entries, classes="[D1, D4, D7]"):
        return LEDGER_HEAD + d7_envelope(classes=classes) + "".join(entries)

    def stage_d7(self, *entries, classes="[D1, D4, D7]"):
        self.write("docs/authorizations.md", self.ledger_with(*entries, classes=classes))
        self.stage("docs/authorizations.md")

    def assert_rejected(self, needle, errors=None):
        errors = self.precommit_errors() if errors is None else errors
        self.assertTrue(any(needle in e for e in errors), msg=errors)

    def test_d7_interval_valid_passes_both_views(self):
        self.init_d7()
        self.stage_d7(d7_entry("g1 按推荐", self.head()))
        self.assertEqual(self.precommit_errors(), [])
        self.commit("W-001 入账 D7")
        self.assertEqual(self.precommit_errors(), [])

    def test_d7_closed_set_valid_passes(self):
        self.init_d7()
        self.stage_d7(d7_entry("n1 按推荐", self.head(), qid="n1", decision="400",
                               range_text=N_RANGE))
        self.assertEqual(self.precommit_errors(), [])

    def test_d7_value_outside_interval_rejected(self):
        self.init_d7(proposal_text=d7_proposal(
            recommends=("d7_recommend: g1 = 0.90", "d7_recommend: n1 = 400")))
        self.stage_d7(d7_entry("g1 超上界", self.head(), decision="0.90"))
        self.assert_rejected("D7 推荐值出区间")

    def test_d7_value_outside_closed_set_rejected(self):
        self.init_d7(proposal_text=d7_proposal(
            recommends=("d7_recommend: g1 = 0.70", "d7_recommend: n1 = 300")))
        self.stage_d7(d7_entry("n1 出闭集", self.head(), qid="n1", decision="300",
                               range_text=N_RANGE))
        self.assert_rejected("D7 推荐值不在闭集")

    def test_d7_closed_set_non_numeric_rejected(self):
        # COORD-016 R1-1（BC-2，提案 §2.2 语法闭集）：闭集元素与推荐值都须匹配
        # -?[0-9]+(\.[0-9]+)?（不带单位、不带指数）；合法数值闭集仍通过。
        cases = [
            # (闭集, 推荐值, 须出现的拒绝原因)
            ("{200帧, 400帧}", "400帧", ("D7 d7_range 片段语法不合", "D7 推荐值不是数值字面")),
            ("{2e2, 4e2}", "4e2", ("D7 d7_range 片段语法不合", "D7 推荐值不是数值字面")),
            ("{200, 400}", "400帧", ("D7 推荐值不是数值字面",)),
            ("{200, 400}", "400", ()),
        ]
        for raw_set, recommended, needles in cases:
            with self.subTest(raw_set=raw_set, recommended=recommended):
                tmp = tempfile.TemporaryDirectory()
                self.addCleanup(tmp.cleanup)
                self.root = Path(tmp.name)
                run_git(["init", "-q"], self.root)
                n_range = f"d7_range: n1 in {raw_set} kind=最小样本量 bc=BC-3"
                self.init_d7(proposal_text=d7_proposal(
                    n_range=n_range,
                    recommends=("d7_recommend: g1 = 0.70", f"d7_recommend: n1 = {recommended}")))
                self.stage_d7(d7_entry("n1 按推荐", self.head(), qid="n1",
                                       decision=recommended, range_text=n_range))
                errors = self.precommit_errors()
                if not needles:
                    self.assertEqual(errors, [])
                for needle in needles:
                    self.assert_rejected(needle, errors)

    def test_d7_decision_not_recommend_literal_rejected(self):
        # 数值相等但字面不同（0.7 ≠ 0.70）也拒绝：decision 逐字 = 推荐值字面。
        self.init_d7()
        self.stage_d7(d7_entry("g1 字面不符", self.head(), decision="0.7"))
        self.assert_rejected("D7 decision 与推荐值字面不逐字相等")

    def test_d7_missing_range_rejected(self):
        self.init_d7(proposal_text=d7_proposal(g_range=None))
        self.stage_d7(d7_entry("g1 缺资格行", self.head()))
        self.assert_rejected("D7 快照中题 g1 的 d7_range 行有 0 行")

    def test_d7_two_recommend_lines_rejected(self):
        self.init_d7(proposal_text=d7_proposal(
            recommends=("d7_recommend: g1 = 0.70", "d7_recommend: g1 = 0.70",
                        "d7_recommend: n1 = 400")))
        self.stage_d7(d7_entry("g1 两行推荐", self.head()))
        self.assert_rejected("D7 快照中题 g1 的 d7_recommend 行有 2 行")

    def test_d7_envelope_without_d7_rejected(self):
        self.init_d7(classes="[D1, D4]")
        self.stage_d7(d7_entry("信封无 D7", self.head()), classes="[D1, D4]")
        self.assert_rejected("类 D7 不在被引信封 classes")

    def test_d7_second_entry_same_id_rejected(self):
        self.init_d7()
        first = d7_entry("g1 第一条", self.head())
        self.stage_d7(first)
        self.commit("W-001 入账 D7 第一条")
        second = d7_entry("g1 第二条", self.head(), at="2026-09-26T10:00:00Z",
                          counter_key="W-001:D7:g1-again")
        self.stage_d7(first, second)
        self.assert_rejected("D7 同一 <id> 第 2 条代拍")

    def test_d7_same_batch_staged_range_rejected_both_views(self):
        # 同批暂存资格行/推荐行 + 代拍条目：pre-commit 读 HEAD: 已提交提案（无该行）→ 拒绝；
        # 提交后按 commit(E) 首父提案复判 → 仍拒绝（BC-3）。
        self.init_d7(proposal_text=d7_proposal(g_range=None, recommends=("d7_recommend: n1 = 400",)))
        self.write("docs/proposals/W-001-synthetic.md", d7_proposal())
        self.stage("docs/proposals/W-001-synthetic.md")
        self.stage_d7(d7_entry("同批补行", self.head()))
        self.assert_rejected("D7 快照中题 g1 的 d7_range 行有 0 行")
        self.commit("W-001 同批补行与代拍")
        self.assert_rejected("D7 快照中题 g1 的 d7_range 行有 0 行")

    def test_d7_big_integer_exact_decimal_rejected(self):
        big = "d7_range: g1 in [9007199254740992, 9007199254740992] kind=门值 bc=BC-2"
        self.init_d7(proposal_text=d7_proposal(
            g_range=big, recommends=("d7_recommend: g1 = 9007199254740993",
                                     "d7_recommend: n1 = 400")))
        self.stage_d7(d7_entry("大整数", self.head(), decision="9007199254740993",
                               range_text=big))
        self.assert_rejected("D7 推荐值出区间")

    def test_d7_widened_range_after_commit_historical_unchanged(self):
        # 提交后把 d7_range 改宽：历史条目仍按 commit(E) 首父快照复判，结论不变（仍拒绝）。
        self.init_d7(proposal_text=d7_proposal(
            recommends=("d7_recommend: g1 = 0.90", "d7_recommend: n1 = 400")))
        self.stage_d7(d7_entry("g1 超上界入账", self.head(), decision="0.90"))
        self.commit("W-001 入账超上界 D7（绕过钩子的合成）")
        self.assert_rejected("D7 推荐值出区间")
        wide = "d7_range: g1 in [0.50, 0.95] kind=门值 bc=BC-2"
        self.write("docs/proposals/W-001-synthetic.md", d7_proposal(
            g_range=wide, recommends=("d7_recommend: g1 = 0.90", "d7_recommend: n1 = 400")))
        self.commit("W-001 提交后改宽 d7_range")
        self.assert_rejected("D7 推荐值出区间")

    def test_d7_kind_missing_rejected(self):
        bad = "d7_range: g1 in [0.50, 0.80] bc=BC-2"
        self.init_d7(proposal_text=d7_proposal(g_range=bad))
        self.stage_d7(d7_entry("种类缺失", self.head(), range_text=bad))
        self.assert_rejected("D7 d7_range 片段 kind= 须恰好 1 次")

    def test_d7_kind_not_in_closed_set_rejected(self):
        bad = "d7_range: g1 in [0.50, 0.80] kind=速度上限 bc=BC-2"
        self.init_d7(proposal_text=d7_proposal(g_range=bad))
        self.stage_d7(d7_entry("种类闭集外", self.head(), range_text=bad))
        self.assert_rejected("D7 kind 不在闭集")

    def test_d7_bc_mismatch_rejected(self):
        bad = "d7_range: g1 in [0.50, 0.80] kind=门值 bc=BC-3"
        self.init_d7(proposal_text=d7_proposal(g_range=bad))
        self.stage_d7(d7_entry("行编号不符", self.head(), range_text=bad))
        self.assert_rejected("D7 bc= 与所在行首格编号不符")

    def test_d7_range_outside_clause_cell_rejected(self):
        # 片段写在「依据」格而非条款格 → 不是正向资格（BC-2）。
        row = f"| BC-4 | 合成条款 | 行为 | test:x | BASE | `{G_RANGE.replace('BC-2', 'BC-4')}` | 2026-09-26 |"
        self.init_d7(proposal_text=d7_proposal(g_range=None, extra_rows=(row,)))
        self.stage_d7(d7_entry("写在依据格", self.head(),
                               range_text=G_RANGE.replace("BC-2", "BC-4")))
        self.assert_rejected("D7 d7_range 不在 BC/AC 表行的条款格内")

    def test_d7_status_not_accepted_rejected(self):
        self.init_d7(proposal_text=d7_proposal(status="PROPOSED"))
        self.stage_d7(d7_entry("未接受", self.head()))
        self.assert_rejected("D7 快照提案 Status: 行不以 `Status: ACCEPTED` 开头")

    def test_d7_recommend_inside_round_section_rejected(self):
        # BC-3：推荐行须在非 `### D<n>` 裁定节。
        self.init_d7(proposal_text=d7_proposal(
            recommends=("d7_recommend: n1 = 400",),
            d_section_extra="\n\nd7_recommend: g1 = 0.70"))
        self.stage_d7(d7_entry("推荐在 D 节", self.head()))
        self.assert_rejected("D7 d7_recommend 行位于 `### D<n>` 裁定节内")

    def test_d7_range_field_not_verbatim_rejected(self):
        self.init_d7()
        self.stage_d7(d7_entry("片段不逐字", self.head(),
                               range_text="d7_range: g1 in [0.5, 0.8] kind=门值 bc=BC-2"))
        self.assert_rejected("D7 range 与快照 d7_range 片段不逐字相等")

    def test_d7_historical_precheck_not_first_parent_rejected(self):
        self.init_d7()
        stale = self.head()
        self.write("docs/current-status.md", board(extra_log="\n### 2026-09-26 — 合成日志\n"))
        self.commit("W-001 推进一行日志")
        self.stage_d7(d7_entry("旧快照", stale))
        self.assert_rejected("precheck_head == HEAD")
        self.commit("W-001 入账旧快照 D7")
        self.assert_rejected("D7 precheck_head 不是 commit(E) 的首父")

    def test_d7_missing_question_id_and_range_rejected(self):
        text = self.ledger_with(d7_entry("缺字段", "a" * 40, drop=("question_id", "range")))
        errors = structural(text)
        self.assertTrue(any("D7 缺必填 question_id" in e for e in errors), msg=errors)
        self.assertTrue(any("D7 缺必填 range" in e for e in errors), msg=errors)


class BoardExpiredFailClosedTests(RepoCase):
    """§5.4 失败关闭：Active handoffs 表头或 Status 列缺失时判到期，而非未到期。"""

    def test_intact_board_not_expired(self):
        self.assertFalse(cl.board_expired(board(), WORK_ID, "K4"))

    def test_missing_active_handoffs_section_expired(self):
        text = board().replace("## Active handoffs", "## Handoffs (renamed)")
        self.assertTrue(cl.board_expired(text, WORK_ID, "K4"))

    def test_missing_active_handoffs_table_expired(self):
        head, _, tail = board().partition("## Active handoffs")
        text = head + "## Active handoffs\n\n（表格缺失）\n\n## Log" + tail.split("## Log", 1)[1]
        self.assertTrue(cl.board_expired(text, WORK_ID, "K4"))

    def test_missing_status_column_expired(self):
        text = (board()
                .replace("| Progress | Status | Consuming |", "| Progress | State | Consuming |"))
        self.assertTrue(cl.board_expired(text, WORK_ID, "K4"))

    def test_precommit_rejects_when_handoff_header_missing(self):
        # 真实 pre-commit 路径：S 处状态板缺 Status 列 → X = S，引用该信封的新条目拒绝。
        broken = board().replace("| Progress | Status | Consuming |",
                                 "| Progress | State | Consuming |")
        self.init_repo(board_text=broken, ledger=LEDGER_HEAD)
        self.write("docs/authorizations.md", LEDGER_HEAD + execution_envelope_entry())
        self.commit("W-001 签发执行信封（S，状态板表头损坏）")
        signed = self.head()
        _, x = cl.first_invalidation(self.root, WORK_ID, EXECUTION_TITLE)
        self.assertEqual(x, signed)
        self.stage_sub(self.head())
        self.assertTrue(any("已失效" in e for e in self.precommit_errors()))

    def stage_sub(self, precheck, **kwargs):
        self.write("docs/authorizations.md",
                   LEDGER_HEAD + execution_envelope_entry()
                   + sub_entry("一笔 SUB", precheck, **kwargs))
        self.stage("docs/authorizations.md")


if __name__ == "__main__":
    unittest.main()
