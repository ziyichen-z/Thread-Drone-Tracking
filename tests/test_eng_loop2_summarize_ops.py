"""P1-ENG-LOOP-002 OpsK1K2K3K4：收尾离线摘要（AC-8 修订 3 / AC-14 修订 1 / AC-18 修订 1；O4）。

临时目录替身：计划由生产 `play_ops.build_plan` 生成；原流按生产写出格式（会话 journal 的 receipt/state/
designation/suspect_raised 行、`ops-web.jsonl` 的 submit_begin/submit_result/preview_displayed 行）。正式评分经
记录型 Python 替身（只拦截 `analyze_play score`），验证恰调用一次、只引用不重算。零模型、零回放。
"""

from __future__ import annotations

import io
import json
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

from tools.eng_loop2 import play_ops
from tools.eng_loop2 import summarize_ops as summ

SID = "loop2-p1"

STUB = r'''#!__PY__
import json, os, sys
args = sys.argv[1:]
open(os.environ.get("STUB_LOG", "/dev/null"), "a").write(json.dumps(args) + "\n")
if args[:3] == ["-m", "tools.eng_loop2.analyze_play", "score"]:
    out = args[args.index("--out") + 1]
    if os.environ.get("STUB_SCORE_NO_OUT"):  # 评分进程失败且未产出输出（如超时/中止）
        sys.exit(int(os.environ.get("STUB_SCORE_RC", "5")))
    json.dump({"schema": "p1-eng-loop-002-four-numbers/v2", "funnel": {"n_accepted": 3, "classes": {"X": 3}},
               "number_one": {"by_truth_source": {"red": 1}}, "number_two": {}, "number_three": {}, "explicit_report": {"e": 1},
               "mislock": {}, "intent_status": {}, "frame_identity_mismatch": {"total": 0}, "layout_binding": {"ok": True},
               "samples": [{"secret": "not cited"}]}, open(out, "w"))
    sys.exit(int(os.environ.get("STUB_SCORE_RC", "0")))
sys.exit(9)
'''


class OpsDir:
    def __init__(self, root: Path):
        self.root = root
        self.ops = root / "play"
        (self.ops / "sessions" / SID).mkdir(parents=True)
        self.plan_path = root / "ops-plan.json"
        plan = play_ops.build_plan({"intent": "Vehicle_SUV_color01 (1)", "text": "the suv"}, {"intent": "Vehicle_Taxi (2)", "text": "the taxi"}, "red_car")
        self.plan_path.write_text(json.dumps(plan), encoding="utf-8")
        self.journal_rows: list[dict[str, Any]] = []
        self.ops_rows: list[dict[str, Any]] = []
        self.t = 1000.0

    def journal(self, kind: str, **fields: Any) -> None:
        self.t += 1.0
        self.journal_rows.append({"session_id": SID, "kind": kind, "at_unix_s": self.t, "epoch": fields.pop("epoch", 1), **fields})

    def submit(self, rid: str, action: str, binding: dict[str, Any] | None = None) -> None:
        self.ops_rows.append({"kind": "submit_begin", "session_id": SID, "request_id": rid, "action": action})
        self.ops_rows.append({"kind": "submit_result", "session_id": SID, "request_id": rid, "action": action, "binding": binding or {}})
        self.journal("receipt", receipt={"request_id": rid, "action": action, "outcome": "APPLIED", "at_sequence": 1})

    def write(self, steps: list[dict[str, Any]] | None, *, record: bool = True, feedback: list[dict[str, Any]] | None = None) -> None:
        with (self.ops / "sessions" / SID / "language-session.jsonl").open("w") as h:
            for row in self.journal_rows:
                h.write(json.dumps(row) + "\n")
        with (self.ops / "ops-web.jsonl").open("w") as h:
            for row in self.ops_rows:
                h.write(json.dumps(row) + "\n")
        if record:
            (self.ops / "play-record.json").write_text(json.dumps({"attempts": [{"playbook": "P1", "session_id": SID, "steps": steps,
                                                                                  "terminal_reason": "operator_stop"}]}))
        if feedback is not None:
            (self.ops / "feedback.jsonl").write_text("".join(json.dumps(f) + "\n" for f in feedback))


def steps(**status: str) -> list[dict[str, Any]]:
    base = {"P1-1": "DONE", "P1-2": "SKIPPED_NOT_IN_VIEW", "P1-3": "NO_CANDIDATE", "P1-4": "NOT_EXECUTED", "P1-5": "NOT_EXECUTED"}
    base.update(status)
    rids = {"P1-1": "r1", "P1-3": "r3"}
    return [{"step_id": k, "status": v, "reason": None, "request_id": rids.get(k) if v not in {"SKIPPED_NOT_IN_VIEW", "NOT_EXECUTED"} else None}
            for k, v in base.items()]


class SummaryTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = OpsDir(Path(self.tmp.name))
        self.stub = Path(self.tmp.name) / "py-stub"
        self.stub.write_text(STUB.replace("__PY__", sys.executable))
        self.stub.chmod(self.stub.stat().st_mode | stat.S_IXUSR)

    def standard(self) -> None:
        d = self.d
        d.journal("state", state="IDLE")
        d.journal("state", state="LOST", reason="tracker_failure")  # 初始 LOST：不代证跟踪后丢失
        d.submit("r1", "ask")
        d.journal("state", state="AWAITING_CONFIRMATION")
        d.ops_rows.append({"kind": "preview_displayed", "result_id": f"{SID}-res1"})
        d.submit("c1", "confirm", {"result_id": f"{SID}-res1"})
        d.journal("designation", designation={"result": "BOUND_DIRECT"})
        d.journal("state", state="TRACKING")
        d.journal("suspect_raised", suspect_kind="lost", reason="verify_none")
        d.journal("state", state="SUSPECTED")
        d.submit("r3", "ask")
        d.submit("s1", "stop")
        d.journal("state", state="TERMINAL", reason="operator_stop")


class PlanVsActualTests(SummaryTestBase):
    def test_skips_separated_failures_kept_in_denominator(self) -> None:
        self.standard()
        self.d.write(steps())
        summary = summ.summarize(self.d.ops, self.d.plan_path, "diagnostic", str(self.stub))
        pva = summary["attempts"][0]["plan_vs_actual"]
        self.assertEqual((pva["designate_planned"], pva["designate_sent"], pva["designate_skipped_not_in_view"], pva["designate_not_executed"]),
                         (4, 2, 1, 1))
        samples = {r["step_id"]: r["is_sample"] for r in pva["steps"]}
        self.assertEqual(samples, {"P1-1": True, "P1-2": False, "P1-3": True, "P1-4": False, "P1-5": False})
        self.assertEqual(pva["counts"]["NO_CANDIDATE"], 1)

    def test_missing_play_record_and_missing_journal(self) -> None:
        self.d.write(None, record=False)
        (self.d.ops / "sessions" / SID / "language-session.jsonl").unlink()
        summary = summ.summarize(self.d.ops, self.d.plan_path, "diagnostic", str(self.stub))
        self.assertEqual(summary["play_record"], "MISSING")
        attempt = summary["attempts"][0]
        self.assertEqual(attempt["journal"], "MISSING")
        self.assertIn("UNVERIFIED", attempt["objective_events"])
        self.assertEqual({r["status"] for r in attempt["plan_vs_actual"]["steps"]}, {"NO_PLAY_RECORD"})

    def test_attempt_without_step_record_is_record_unknown_not_unexecuted(self) -> None:
        """C6-3：有尝试记录但逐步记录缺失 → MISSING_RECORD（记录未知），与确实未执行分列，不冒充无 Play 记录。"""
        self.standard()
        self.d.write(None)
        pva = summ.summarize(self.d.ops, self.d.plan_path, "diagnostic", str(self.stub))["attempts"][0]["plan_vs_actual"]
        self.assertEqual({r["status"] for r in pva["steps"]}, {"MISSING_RECORD"})
        self.assertEqual((pva["designate_not_executed"], pva["designate_record_unknown"]), (0, 4))

    def test_halted_accepted_steps_stay_samples_with_their_receipts(self) -> None:
        """C6-3：已受理后被封住（HALTED）仍是样本、request_id 对上原回执；其余未执行分列。"""
        self.standard()
        record = steps(**{"P1-3": "HALTED"})
        self.d.write(record)
        attempt = summ.summarize(self.d.ops, self.d.plan_path, "diagnostic", str(self.stub))["attempts"][0]
        pva = attempt["plan_vs_actual"]
        row = next(r for r in pva["steps"] if r["step_id"] == "P1-3")
        self.assertEqual((row["status"], row["request_id"], row["is_sample"]), ("HALTED", "r3", True))
        self.assertEqual((pva["designate_sent"], pva["designate_halted"], pva["designate_not_executed"]), (2, 1, 1))
        self.assertEqual(attempt["consistency_issues"], [])


class ObjectiveEventTests(SummaryTestBase):
    def test_initial_lost_does_not_prove_lost_after_tracking(self) -> None:
        d = self.d
        d.journal("state", state="LOST", reason="tracker_failure")
        d.journal("state", state="IDLE")
        events = summ.objective_events(d.journal_rows, SID)
        self.assertEqual(events["initial_lost_entries"], 1)
        self.assertIn("UNVERIFIED", events["claims"]["lost_after_tracking"])
        self.assertIn("UNVERIFIED", events["claims"]["follow"])

    def test_events_after_tracking_and_release_excluded(self) -> None:
        self.standard()
        self.d.journal("state", state="LOST", reason="operator_release")
        events = summ.objective_events(self.d.journal_rows, SID)
        self.assertEqual(events["tracking_entries"], 1)
        self.assertEqual([e["state"] for e in events["suspected_or_lost_after_tracking"]], ["SUSPECTED"])
        self.assertIn("EVENT_OCCURRED", events["claims"]["follow"])
        self.assertIn("EVENT_OCCURRED", events["claims"]["lost_after_tracking"])
        self.assertIn("UNVERIFIED", events["claims"]["switch_target"])
        self.assertEqual(events["designation_results"], {"BOUND_DIRECT": 1})
        self.assertEqual(events["terminal_reason"], "operator_stop")
        self.assertEqual(events["suspect_raised"], 1)


class ConsistencyTests(SummaryTestBase):
    def test_clean_record_has_no_issues_and_feedback_missing_is_reported(self) -> None:
        self.standard()
        self.d.write(steps())
        attempt = summ.summarize(self.d.ops, self.d.plan_path, "diagnostic", str(self.stub))["attempts"][0]
        self.assertEqual(attempt["consistency_issues"], [])
        self.assertEqual(attempt["user_feedback"], "未反馈")

    def test_request_timeline_binds_each_submit_to_its_session_receipt(self) -> None:
        self.standard()
        self.d.ops_rows.append({"kind": "submit_result", "session_id": SID, "request_id": "u1", "action": "ask", "unknown": True})
        self.d.write(steps())
        rows = summ.summarize(self.d.ops, self.d.plan_path, "diagnostic", str(self.stub))["attempts"][0]["request_timeline"]
        by_id = {r["request_id"]: r for r in rows}
        self.assertEqual(by_id["c1"]["session_receipt"]["outcome"], "APPLIED")
        self.assertEqual(by_id["c1"]["binding"], {"result_id": f"{SID}-res1"})
        self.assertEqual(by_id["u1"]["session_receipt"], "MISSING")

    def test_foreign_writer_undisplayed_confirm_and_skip_with_request(self) -> None:
        self.standard()
        self.d.journal("receipt", receipt={"request_id": "cli-manual-1", "action": "ask", "outcome": "APPLIED", "at_sequence": 9})
        self.d.ops_rows = [r for r in self.d.ops_rows if r.get("kind") != "preview_displayed"]
        bad = steps()
        bad[1]["request_id"] = "r2"
        self.d.write(bad)
        issues = summ.summarize(self.d.ops, self.d.plan_path, "diagnostic", str(self.stub))["attempts"][0]["consistency_issues"]
        text = "\n".join(issues)
        self.assertIn("cli-manual-1", text)
        self.assertIn("无浏览器显示成功记录", text)
        self.assertIn("跳过的步骤带 request_id r2", text)

    def test_r1_1_not_executed_step_carrying_request_id_is_reported(self) -> None:
        """OPSR1返工 R1-1：「未执行」却带 request_id（已受理被事后改写）必须报一致性问题。"""
        self.standard()
        record = steps()
        record[2].update(status="NOT_EXECUTED")  # P1-3 原已受理 r3
        self.assertEqual(record[2]["request_id"], "r3")
        self.d.write(record)
        attempt = summ.summarize(self.d.ops, self.d.plan_path, "diagnostic", str(self.stub))["attempts"][0]
        self.assertTrue(any("P1-3" in i and "未执行" in i and "r3" in i for i in attempt["consistency_issues"]), attempt["consistency_issues"])

    def test_feedback_kept_verbatim_and_separate(self) -> None:
        self.standard()
        self.d.write(steps(), feedback=[{"attempt": SID, "label": "FAIL", "button_text": "失败", "text": "没跟上"}])
        attempt = summ.summarize(self.d.ops, self.d.plan_path, "diagnostic", str(self.stub))["attempts"][0]
        self.assertEqual(attempt["user_feedback"][0]["text"], "没跟上")


class ScoringTests(SummaryTestBase):
    def archive(self) -> None:
        (self.d.ops / SID / "unity-runtime").mkdir(parents=True)

    def test_formal_calls_original_score_once_and_only_cites(self) -> None:
        self.standard()
        self.d.write(steps())
        self.archive()
        log = Path(self.tmp.name) / "stub.log"
        import os

        os.environ["STUB_LOG"] = str(log)
        self.addCleanup(os.environ.pop, "STUB_LOG", None)
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(summ.main(["--ops-dir", str(self.d.ops), "--plan", str(self.d.plan_path), "--mode", "formal", "--python", str(self.stub)]), 0)
        calls = [json.loads(l) for l in log.read_text().splitlines()]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][:3], ["-m", "tools.eng_loop2.analyze_play", "score"])
        self.assertEqual(calls[0][calls[0].index("--scenario-copy") + 1], str(self.d.ops / SID / "unity-runtime" / "scenario_config.json"))
        summary = json.loads((self.d.ops / "ops-summary.json").read_text())
        score = summary["attempts"][0]["score"]
        self.assertEqual(score["cited"]["funnel"], {"n_accepted": 3, "classes": {"X": 3}})
        self.assertEqual(set(score["cited"]), set(summ.SCORE_KEYS))
        self.assertNotIn("samples", score["cited"])
        self.assertTrue((self.d.ops / "ops-summary.md").read_text().startswith("# P1-ENG-LOOP-002 操作收尾摘要（formal"))
        # 第二次：拒绝覆盖摘要，评分不再调用
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(summ.main(["--ops-dir", str(self.d.ops), "--plan", str(self.d.plan_path), "--mode", "formal", "--python", str(self.stub)]), 2)
        self.assertEqual(len(log.read_text().splitlines()), 1)
        # 直接复用函数：score 输出已存在也不重跑
        self.assertFalse(summ.run_score(str(self.stub), self.d.ops, SID)["called"])

    def stub_log(self) -> Path:
        import os

        log = Path(self.tmp.name) / "stub.log"
        os.environ["STUB_LOG"] = str(log)
        self.addCleanup(os.environ.pop, "STUB_LOG", None)
        return log

    def run_main(self) -> int:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return summ.main(["--ops-dir", str(self.d.ops), "--plan", str(self.d.plan_path), "--mode", "formal", "--python", str(self.stub)])

    # OPSR1返工 R1-3(c)：原评分非 0 退出 → 摘要照写并记失败，自身非 0 退出
    def test_r1_3_score_nonzero_rc_makes_summary_exit_nonzero(self) -> None:
        import os

        self.standard()
        self.d.write(steps())
        self.archive()
        log = self.stub_log()
        os.environ["STUB_SCORE_RC"] = "4"
        self.addCleanup(os.environ.pop, "STUB_SCORE_RC", None)
        self.assertNotEqual(self.run_main(), 0)
        self.assertEqual(len(log.read_text().splitlines()), 1)
        summary = json.loads((self.d.ops / "ops-summary.json").read_text())
        self.assertEqual(summary["attempts"][0]["score_call"]["rc"], 4)
        self.assertEqual([f["code"] for f in summary["failures"]], ["UNKNOWN"])

    # OPSR1返工 R1-4（AC-10 修订 7 后按现行常量）：每次评分**之前**守账（成功/失败共账，持久化）；第 N+1 次拒绝并照记
    # S-ENVELOPE，非 0 退出
    def test_r1_4_formal_score_calls_are_guarded_before_each_call(self) -> None:
        limit = summ.FORMAL_SCORE_LIMIT
        sessions = self.archives(limit + 1)
        log = self.stub_log()
        self.assertEqual(self.run_main(), 3)
        self.assertEqual(len(log.read_text().splitlines()), limit)
        summary = json.loads((self.d.ops / "ops-summary.json").read_text())
        calls = [a["score_call"] for a in summary["attempts"]]
        self.assertEqual([c["called"] for c in calls], [True] * limit + [False])
        self.assertTrue(calls[-1]["reason"].startswith("S-ENVELOPE"))
        self.assertIn("S-ENVELOPE", [f["code"] for f in summary["failures"]])
        ledger = json.loads((self.d.ops / summ.SCORE_LEDGER).read_text())
        self.assertEqual(ledger["formal_score_calls"], limit)
        # 重跑（换掉摘要）：账已满，不再调用；已有输出的归档也不重跑
        self.drop_summary()
        self.assertEqual(self.run_main(), 3)
        self.assertEqual(len(log.read_text().splitlines()), limit)
        # 账本不可读 → 不评分（fail-closed）
        (self.d.ops / summ.SCORE_LEDGER).write_text("{broken")
        call = summ.run_score(str(self.stub), self.d.ops, sessions[-1])
        self.assertFalse(call["called"])
        self.assertTrue(call["reason"].startswith("S-ENVELOPE"))

    # --- 评分诊断合批修复：AC-10 修订 7（全批实际调用总上限 3；生产 summarize/run_score 入口） ---

    def archives(self, count: int) -> list[str]:
        sessions = [f"loop2-p{i + 1}" if i < 3 else f"loop2-p{i + 1}-x" for i in range(count)]
        attempts = []
        for index, sid in enumerate(sessions):
            (self.d.ops / "sessions" / sid).mkdir(parents=True, exist_ok=True)
            (self.d.ops / sid / "unity-runtime").mkdir(parents=True)
            attempts.append({"playbook": ("P1", "P2", "P3")[min(index, 2)], "session_id": sid, "steps": [], "attempted": True})
        (self.d.ops / "play-record.json").write_text(json.dumps({"attempts": attempts}))
        (self.d.ops / "ops-web.jsonl").write_text("")
        return sessions

    def drop_summary(self) -> None:
        for name in ("ops-summary.json", "ops-summary.md"):
            (self.d.ops / name).unlink()

    def summary_calls(self) -> list[dict[str, Any]]:
        return [a["score_call"] for a in json.loads((self.d.ops / "ops-summary.json").read_text())["attempts"]]

    def test_ac10_r7_three_archives_scored_fourth_call_refused_before_call(self) -> None:
        self.archives(4)
        log = self.stub_log()
        self.assertEqual(self.run_main(), 3)  # 第 4 次被拒 → S-ENVELOPE、非 0
        self.assertEqual(len(log.read_text().splitlines()), 3)
        calls = self.summary_calls()
        self.assertEqual([c["called"] for c in calls], [True, True, True, False])
        self.assertEqual([c["ledger"] for c in calls[:3]], ["formal_score_calls 1/3", "formal_score_calls 2/3", "formal_score_calls 3/3"])
        self.assertTrue(calls[3]["reason"].startswith("S-ENVELOPE formal_score_calls would exceed 3 (used 3, +1)"))
        self.assertEqual(json.loads((self.d.ops / summ.SCORE_LEDGER).read_text())["formal_score_calls"], 3)
        self.assertFalse((self.d.ops / "loop2-p4-x" / "score.json").exists())

    def test_ac10_r7_three_archives_all_scored_exit_zero(self) -> None:
        self.archives(3)
        log = self.stub_log()
        self.assertEqual(self.run_main(), 0)
        self.assertEqual(len(log.read_text().splitlines()), 3)
        self.assertEqual([c["called"] for c in self.summary_calls()], [True, True, True])

    def test_ac10_r7_failed_calls_consume_and_no_free_rescore(self) -> None:
        import os

        self.archives(3)
        log = self.stub_log()
        os.environ["STUB_SCORE_NO_OUT"] = "1"
        self.addCleanup(os.environ.pop, "STUB_SCORE_NO_OUT", None)
        self.assertEqual(self.run_main(), 3)  # 三次都失败（无输出）：已扣 3
        self.assertEqual(len(log.read_text().splitlines()), 3)
        self.assertEqual(json.loads((self.d.ops / summ.SCORE_LEDGER).read_text())["formal_score_calls"], 3)
        # 换摘要重评（跨摘要共账）：账已满，第 4 次在调用前即拒，没有免费重评
        os.environ.pop("STUB_SCORE_NO_OUT")
        self.drop_summary()
        self.assertEqual(self.run_main(), 3)
        self.assertEqual(len(log.read_text().splitlines()), 3)
        self.assertTrue(all(c["reason"].startswith("S-ENVELOPE") for c in self.summary_calls()))

    def test_ac10_r7_inherited_ledger_is_not_reset(self) -> None:
        self.archives(3)
        (self.d.ops / summ.SCORE_LEDGER).write_text(json.dumps({"formal_score_calls": 2}))
        log = self.stub_log()
        self.assertEqual(self.run_main(), 3)
        self.assertEqual(len(log.read_text().splitlines()) if log.exists() else 0, 1)  # 已用 2，只剩 1
        self.assertEqual([c["called"] for c in self.summary_calls()], [True, False, False])
        self.assertEqual(json.loads((self.d.ops / summ.SCORE_LEDGER).read_text())["formal_score_calls"], 3)

    def test_ac10_r7_existing_output_cited_not_counted_and_bad_ledger_refused(self) -> None:
        sessions = self.archives(3)
        (self.d.ops / sessions[0] / "score.json").write_text(json.dumps({"schema": "p1-eng-loop-002-four-numbers/v2", "funnel": {"n": 1}}))
        log = self.stub_log()
        self.assertEqual(self.run_main(), 0)
        self.assertEqual(len(log.read_text().splitlines()), 2)  # 已有输出只引用，不调用、不计
        calls = self.summary_calls()
        self.assertFalse(calls[0]["called"])
        self.assertTrue(calls[0]["reason"].startswith("score_output_exists"))
        self.assertEqual(json.loads((self.d.ops / summ.SCORE_LEDGER).read_text())["formal_score_calls"], 2)
        # 原账不可读/非法（缺键、布尔、小数、负数、非对象）一律拒评，不当作 0
        target = self.d.ops / "loop2-p9"
        (target / "unity-runtime").mkdir(parents=True)
        for bad in ("{broken", "{}", '{"formal_score_calls": true}', '{"formal_score_calls": 1.5}',
                    '{"formal_score_calls": -5}', "[2]"):
            (self.d.ops / summ.SCORE_LEDGER).write_text(bad)
            call = summ.run_score(str(self.stub), self.d.ops, "loop2-p9")
            self.assertFalse(call["called"], bad)
            self.assertIn("不可读", call["reason"], bad)
        self.assertEqual(len(log.read_text().splitlines()), 2)

    def test_formal_without_archive_and_diagnostic_never_score(self) -> None:
        self.standard()
        self.d.write(steps())
        formal = summ.summarize(self.d.ops, self.d.plan_path, "formal", str(self.stub))["attempts"][0]
        self.assertFalse(formal["score_call"]["called"])
        self.archive()
        diagnostic = summ.summarize(self.d.ops, self.d.plan_path, "diagnostic", str(self.stub))["attempts"][0]
        self.assertFalse(diagnostic["score_call"]["called"])
        self.assertIn("诊断模式", diagnostic["score_call"]["reason"])
        self.assertNotIn("score", diagnostic)


if __name__ == "__main__":
    unittest.main()
