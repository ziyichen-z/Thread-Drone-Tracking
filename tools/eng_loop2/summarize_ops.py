"""P1-ENG-LOOP-002 OpsK1K2K3K4：收尾离线操作摘要（AC-8 修订 3 / AC-14 修订 1 / AC-18 修订 1；O4）。

在 Play 停止、归档之后由 `play_ops` 以**独立进程**调用（也可人工离线调用）；输出不回流任何在线工具。

* 计划—实际漏斗：逐步列预登记计划、实际发送/跳过（SKIPPED_NOT_IN_VIEW）/未执行/拒收/无候选/无选择/
  结果未知及原因；跳过不成样本，其余已受理命令一条不删（失败分母保持）。
* 客观事件（只读会话原流，不读真值）：是否指定、TRACKING、切换、释放、SUSPECTED/LOST、TERMINAL 及实际命令；
  未播种即「未验证」，初始 LOST 不代证「跟踪后丢失」，状态名不证明跟对/身份正确。
* 一致性：计划 ↔ 提交记录（`ops-web.jsonl`）↔ 会话回执（request_id）↔ 网页选择绑定流。
* 本人反馈：`feedback.jsonl` 原样分列；缺失写「未反馈」，不默认通过。
* 正式模式：每个有归档的尝试至多调用一次原 CLI `python -m tools.eng_loop2.analyze_play score`（计入原实现回放次数，
  不另造「摘要回放」；输出已存在即拒绝重跑），摘要只**引用**其四表与漏斗原值，不重算、不新增通过率/性能门。
  R1@OpsK1K2K3K4 R1-4 / AC-10 修订 7：每次评分调用**之前**按已签全批实际调用总上限守账（B-main 评分资源修订 1
  `SCORE:CHANGE:1`：≤ 3，是总次数而非每归档/每摘要；`score-ledger.json` 持久计数、原账继承不重置，成功/失败/超时/
  中止共账、先扣后调，没有免费重评；账本不可读即不评分），下一次会越界即不调用、照记 `S-ENVELOPE`。
  R1-3：评分非 0 退出或守账越界时摘要照写并列入 `failures`，本进程非 0 退出（由 `play_ops` 置失败）。
  诊断模式不调用评分、不判门。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "p1-eng-loop-002-ops-summary/v1"
SESSION_IDS = {"P1": "loop2-p1", "P2": "loop2-p2", "P3": "loop2-p3"}
#: 原评分输出中被引用（不重算）的键：漏斗 + 四类数字表 + 误锁。
SCORE_KEYS = ("funnel", "intent_status", "number_one", "number_two", "number_three", "explicit_report", "mislock",
              "frame_identity_mismatch", "layout_binding")
#: `HALTED`：已受理后被 STOP/故障/中断封住（仍是样本，不改成未执行）；`MISSING_RECORD`/`NO_PLAY_RECORD` 是记录未知，
#: 与确实未执行（`NOT_EXECUTED`）分列（C6@OpsK1K2K3K4 C6-3）。
STEP_OUTCOMES = ("DONE", "SKIPPED_NOT_IN_VIEW", "REFUSED", "NO_CANDIDATE", "NO_DECISION", "NOT_EXECUTED", "UNKNOWN", "HALTED")
RECORD_UNKNOWN = frozenset({"MISSING_RECORD", "NO_PLAY_RECORD"})
#: AC-10 修订 7（同名提案「SUB3核清与评分上限落实」§3，B-main 评分资源修订 1 `SCORE:CHANGE:1`）：实现自证对正式归档的
#: 评分**全批实际调用总上限 ≤ 3**（替代修订 6 的 2；不是每归档 3/每摘要 3）。三归档各首次成功合计 3；第 4 次实际调用在
#: 调用前拒绝（`S-ENVELOPE`、非 0）。原账继承不重置（若已用 2 只剩 1）。复核证据核实（≤ 1 次）不经本工具。
FORMAL_SCORE_LIMIT = 3
SCORE_LEDGER = "score-ledger.json"
SCORE_LEDGER_KEY = "formal_score_calls"


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], int]:
    """(记录, 坏行数)；文件缺失返回 ([], -1)。"""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return [], -1
    records, bad = [], 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            bad += 1
            continue
        if isinstance(record, dict):
            records.append(record)
        else:
            bad += 1
    return records, bad


def read_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --- 客观事件（会话原流） -------------------------------------------------------------


def objective_events(journal: Sequence[Mapping[str, Any]], session_id: str) -> dict[str, Any]:
    rows = [r for r in journal if r.get("session_id") == session_id]
    states = [r for r in rows if r.get("kind") == "state"]
    tracking_at = [float(r["at_unix_s"]) for r in states if r.get("state") == "TRACKING" and isinstance(r.get("at_unix_s"), (int, float))]
    first_tracking = min(tracking_at) if tracking_at else None
    entries = Counter(str(r.get("state")) for r in states)
    lost_after = [
        {"state": r.get("state"), "reason": r.get("reason"), "at_unix_s": r.get("at_unix_s")}
        for r in states
        if r.get("state") in {"SUSPECTED", "LOST"} and first_tracking is not None
        and isinstance(r.get("at_unix_s"), (int, float)) and float(r["at_unix_s"]) > first_tracking
        and r.get("reason") != "operator_release"
    ]
    initial_lost = [r for r in states if r.get("state") == "LOST" and (first_tracking is None or float(r.get("at_unix_s") or 0) <= first_tracking)]
    receipts = [r for r in rows if r.get("kind") == "receipt"]
    actions = Counter(f"{(r.get('receipt') or {}).get('action')}:{(r.get('receipt') or {}).get('outcome')}" for r in receipts)
    designations = [r for r in rows if r.get("kind") == "designation"]
    tracked_epochs = sorted({r.get("epoch") for r in states if r.get("state") == "TRACKING"}, key=str)
    terminal = [r for r in states if r.get("state") == "TERMINAL"]
    suspects = [r for r in rows if r.get("kind") == "suspect_raised"]
    releases = [r for r in receipts if (r.get("receipt") or {}).get("action") == "release" and (r.get("receipt") or {}).get("outcome") == "APPLIED"]
    return {
        "state_entries": dict(sorted(entries.items())),
        "receipts_by_action_outcome": dict(sorted(actions.items())),
        "designation_events": len(designations),
        "designation_results": dict(sorted(Counter(str((r.get("designation") or {}).get("result")) for r in designations).items())),
        "tracking_entries": len(tracking_at),
        "tracking_epochs": tracked_epochs,
        "releases_applied": len(releases),
        "suspect_raised": len(suspects),
        "suspect_kinds": dict(sorted(Counter(str(r.get("suspect_kind")) for r in suspects).items())),
        "suspected_or_lost_after_tracking": lost_after,
        "initial_lost_entries": len(initial_lost),
        "terminal_reason": terminal[-1].get("reason") if terminal else None,
        "claims": {
            "follow": "EVENT_OCCURRED（只证明进入 TRACKING，不证明跟对）" if tracking_at else "UNVERIFIED（未播种）",
            "switch_target": "EVENT_OCCURRED（≥2 个纪元进入 TRACKING；身份未由状态名证明）" if len(tracked_epochs) >= 2 else "UNVERIFIED",
            "lost_after_tracking": "EVENT_OCCURRED（跟踪后 SUSPECTED/LOST 原样记录；判对错只在离线评分）" if lost_after
            else "UNVERIFIED（无跟踪后丢失事件；初始 LOST 不代证）",
            "explicit_report": f"suspect_raised={len(suspects)}（原显式报告原样记录，未自动 confirm-lost/dismiss）",
        },
    }


# --- 计划 ↔ 实际 ↔ 回执 一致性 ----------------------------------------------------------


def plan_vs_actual(planned: Sequence[Mapping[str, Any]], actual: Sequence[Mapping[str, Any]] | None) -> dict[str, Any]:
    by_id = {str(s.get("step_id")): s for s in (actual or [])}
    rows = []
    for step in planned:
        got = by_id.get(str(step["step_id"]), {})
        status = got.get("status") or ("MISSING_RECORD" if actual is not None else "NO_PLAY_RECORD")
        rows.append({
            "step_id": step["step_id"], "planned_action": step["action"], "instruction": step.get("instruction"),
            "intent": step.get("intent"), "delay_s": step.get("delay_s"), "status": status, "reason": got.get("reason"),
            "request_id": got.get("request_id"),
            "is_sample": status not in {"SKIPPED_NOT_IN_VIEW", "NOT_EXECUTED", "MISSING_RECORD", "NO_PLAY_RECORD"}
            and step.get("kind") == "designate",
        })
    counts = Counter(r["status"] for r in rows)
    designate = [r for r in rows if r["planned_action"] in {"ask", "respecify"}]
    return {
        "steps": rows,
        "counts": dict(sorted(counts.items())),
        "designate_planned": len(designate),
        "designate_sent": sum(1 for r in designate if r["request_id"]),
        "designate_skipped_not_in_view": sum(1 for r in designate if r["status"] == "SKIPPED_NOT_IN_VIEW"),
        "designate_not_executed": sum(1 for r in designate if r["status"] == "NOT_EXECUTED"),
        "designate_record_unknown": sum(1 for r in designate if r["status"] in RECORD_UNKNOWN),
        "designate_halted": sum(1 for r in designate if r["status"] == "HALTED"),
        "note": "SKIPPED_NOT_IN_VIEW 仅由本人点击产生、不成样本；其余已受理命令全部保留（不按未 TRACKING/none/拒绝/过期删样本）；"
                "HALTED = 已受理后被 STOP/故障/中断封住（仍是样本）；未执行与记录未知分列",
    }


def consistency(rows: Sequence[Mapping[str, Any]], ops_log: Sequence[Mapping[str, Any]], journal: Sequence[Mapping[str, Any]],
                session_id: str) -> list[str]:
    issues: list[str] = []
    submits = {r.get("request_id"): r for r in ops_log if r.get("kind") == "submit_result" and r.get("session_id") == session_id}
    begins = {r.get("request_id") for r in ops_log if r.get("kind") == "submit_begin" and r.get("session_id") == session_id}
    receipts: dict[str, Mapping[str, Any]] = {}
    for record in journal:
        receipt = record.get("receipt") if record.get("kind") == "receipt" else None
        if isinstance(receipt, dict) and receipt.get("request_id") and record.get("session_id") == session_id:
            receipts.setdefault(str(receipt["request_id"]), receipt)
    for row in rows:
        rid = row.get("request_id")
        if row["status"] == "SKIPPED_NOT_IN_VIEW" and rid:
            issues.append(f"{row['step_id']}: 跳过的步骤带 request_id {rid}")
        if row["status"] == "NOT_EXECUTED" and rid:
            issues.append(f"{row['step_id']}: 记为未执行却带 request_id {rid}（已受理命令不得事后改写为未执行）")
        if rid and row["planned_action"] in {"ask", "respecify"}:
            if rid not in begins:
                issues.append(f"{row['step_id']}: request_id {rid} 无 submit_begin 记录")
            submit = submits.get(rid) or {}
            if submit.get("action") != row["planned_action"]:
                issues.append(f"{row['step_id']}: 提交动作 {submit.get('action')} ≠ 计划 {row['planned_action']}")
            receipt = receipts.get(str(rid))
            if row["status"] != "UNKNOWN" and receipt is None:
                issues.append(f"{row['step_id']}: request_id {rid} 在会话原流无回执")
            if receipt is not None and receipt.get("action") != row["planned_action"]:
                issues.append(f"{row['step_id']}: 回执动作 {receipt.get('action')} ≠ 计划 {row['planned_action']}")
    for rid, receipt in receipts.items():
        if receipt.get("action") in {"ask", "respecify", "confirm", "reject", "release"} and rid not in submits:
            issues.append(f"会话回执 {rid}（{receipt.get('action')}）不来自本工具提交记录（第二写者/CLI 绕过？）")
    for rid, submit in submits.items():
        if submit.get("action") == "confirm":
            result_id = (submit.get("binding") or {}).get("result_id")
            shown = [r for r in ops_log if r.get("kind") == "preview_displayed" and r.get("result_id") == result_id]
            if not shown:
                issues.append(f"confirm {rid}: 绑定结果 {result_id} 无浏览器显示成功记录")
    return issues


def request_timeline(ops_log: Sequence[Mapping[str, Any]], journal: Sequence[Mapping[str, Any]], session_id: str) -> list[dict[str, Any]]:
    """W5/AC-18 修订 1：逐提交列来源/动作/绑定/CLI 起止/退出码与会话原流回执（写盘时刻、结局、detail）。"""
    receipts: dict[str, Mapping[str, Any]] = {}
    for record in journal:
        receipt = record.get("receipt") if record.get("kind") == "receipt" else None
        if isinstance(receipt, dict) and receipt.get("request_id") and record.get("session_id") == session_id:
            receipts.setdefault(str(receipt["request_id"]), {"outcome": receipt.get("outcome"), "detail": record.get("detail"),
                                                             "journal_at_unix_s": record.get("at_unix_s")})
    rows = []
    for record in ops_log:
        if record.get("kind") != "submit_result" or record.get("session_id") != session_id:
            continue
        rid = str(record.get("request_id"))
        rows.append({"request_id": rid, "source": record.get("source"), "action": record.get("action"),
                     "binding": record.get("binding"), "exit_code": record.get("exit_code"), "unknown": record.get("unknown"),
                     "cli_started_unix_s": record.get("cli_started_unix_s"), "cli_finished_unix_s": record.get("cli_finished_unix_s"),
                     "session_receipt": receipts.get(rid, "MISSING")})
    return rows


# --- 正式评分（原 CLI，独立进程，恰一次） -----------------------------------------------------


def take_score_call(ops_dir: Path) -> tuple[bool, str]:
    """R1-4 / AC-10 修订 7：评分调用**之前**守账；成功即先记一次（之后无论评分成败都已计入）。返回 (可调用, 说明)。"""
    path = Path(ops_dir) / SCORE_LEDGER
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {SCORE_LEDGER_KEY: 0}
        raw = data.get(SCORE_LEDGER_KEY) if isinstance(data, dict) else None
        # 原账须是非负整数（缺键/布尔/小数/负数都按不可读拒评，不当作 0 重置）
        used = raw if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0 else None
    except (OSError, ValueError, TypeError):
        used = None
    if used is None:
        return False, f"S-ENVELOPE 评分账本 {path.name} 不可读：不评分（fail-closed）"
    if used + 1 > FORMAL_SCORE_LIMIT:
        return False, f"S-ENVELOPE formal_score_calls would exceed {FORMAL_SCORE_LIMIT} (used {used}, +1)：不评分、照记"
    data[SCORE_LEDGER_KEY] = used + 1
    path.write_text(json.dumps(data, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    return True, f"formal_score_calls {used + 1}/{FORMAL_SCORE_LIMIT}"


def run_score(python: str, ops_dir: Path, session_id: str) -> dict[str, Any]:
    unity = ops_dir / session_id / "unity-runtime"
    out = ops_dir / session_id / "score.json"
    if out.exists():
        return {"called": False, "reason": "score_output_exists（不重跑；回放次数守账）", "out": str(out)}
    allowed, ledger_note = take_score_call(ops_dir)
    if not allowed:
        return {"called": False, "reason": ledger_note, "out": str(out)}
    argv = [python, "-m", "tools.eng_loop2.analyze_play", "score", "--session-dir", str(ops_dir / "sessions" / session_id),
            "--unity-dir", str(unity), "--runs-dir", str(unity / "runs"), "--scenario-copy", str(unity / "scenario_config.json"),
            "--out", str(out)]
    done = subprocess.run(argv, capture_output=True, text=True, check=False)
    (ops_dir / session_id).mkdir(parents=True, exist_ok=True)
    (ops_dir / session_id / "score.stderr").write_text(done.stderr, encoding="utf-8")
    return {"called": True, "argv": argv, "rc": done.returncode, "out": str(out), "stderr_tail": done.stderr[-400:],
            "ledger": ledger_note}


def cite_score(path: Path) -> dict[str, Any]:
    document = read_json(path)
    if not isinstance(document, dict):
        return {"available": False}
    return {"available": True, "sha256": sha256_file(path), "schema": document.get("schema"),
            "cited": {key: document.get(key) for key in SCORE_KEYS},
            "note": "原 analyze_play score 输出逐值引用，不重算、不合并、不新增通过率"}


# --- 汇总 ---------------------------------------------------------------------------


def summarize(ops_dir: Path, plan_path: Path, mode: str, python: str) -> dict[str, Any]:
    ops_dir = Path(ops_dir)
    plan = read_json(plan_path) or {}
    record = read_json(ops_dir / "play-record.json")
    ops_log, ops_bad = read_jsonl(ops_dir / "ops-web.jsonl")
    feedback, _ = read_jsonl(ops_dir / "feedback.jsonl")
    attempts_in = (record or {}).get("attempts") if isinstance(record, dict) else None
    if not attempts_in:
        attempts_in = [{"playbook": p, "session_id": s} for p, s in SESSION_IDS.items() if (ops_dir / "sessions" / s).is_dir()]
    attempts = []
    failures: list[dict[str, Any]] = []
    for attempt in attempts_in:
        playbook, session_id = attempt.get("playbook"), attempt.get("session_id")
        journal, journal_bad = read_jsonl(ops_dir / "sessions" / str(session_id) / "language-session.jsonl")
        actual = attempt.get("steps")
        if actual is None and record is not None:
            actual = []  # 有尝试记录但缺逐步记录 → 逐步 MISSING_RECORD（记录未知），不冒充「无 Play 记录」或未执行
        steps = plan_vs_actual((plan.get("playbooks") or {}).get(playbook, []), actual)
        given = [f for f in feedback if f.get("attempt") == session_id]
        item: dict[str, Any] = {
            "playbook": playbook, "session_id": session_id,
            "stop": attempt.get("stop"), "terminal_reason_recorded": attempt.get("terminal_reason"),
            "play_button_times": attempt.get("play_button_times", "UNKNOWN"),
            "plan_vs_actual": steps,
            "journal": "MISSING" if journal_bad == -1 else {"rows": len(journal), "bad_lines": journal_bad},
            "objective_events": objective_events(journal, str(session_id)) if journal_bad != -1 else "UNVERIFIED（会话原流缺失）",
            "consistency_issues": consistency(steps["steps"], ops_log, journal, str(session_id)),
            "request_timeline": request_timeline(ops_log, journal, str(session_id)),
            "user_feedback": given or "未反馈",
            "model_loads": attempt.get("model_loads"),
            "archive": attempt.get("archive"),
            # 尝试原记录（失败路径也保留）：是否开始、会话 rc/进程、封住原因、全部 STOP 与收尾各步
            "attempted": attempt.get("attempted"),
            "session_rc": attempt.get("session_rc"),
            "session_process": attempt.get("session_process"),
            "halted": attempt.get("halted"),
            "stops_all": attempt.get("stops_all"),
            "closeout": attempt.get("closeout"),
        }
        if mode == "formal":
            if (ops_dir / str(session_id) / "unity-runtime").is_dir():
                item["score_call"] = run_score(python, ops_dir, str(session_id))
                item["score"] = cite_score(ops_dir / str(session_id) / "score.json")
                call = item["score_call"]
                if call.get("called") and call.get("rc") != 0:
                    failures.append({"code": "UNKNOWN", "session_id": session_id,
                                     "detail": f"{session_id} analyze_play score rc={call.get('rc')}（评分未证明完成）"})
                elif not call.get("called") and str(call.get("reason", "")).startswith("S-ENVELOPE"):
                    failures.append({"code": "S-ENVELOPE", "session_id": session_id, "detail": f"{session_id} {call['reason']}"})
            else:
                item["score_call"] = {"called": False, "reason": "归档缺失：不评分（不读 runtime/）"}
        else:
            item["score_call"] = {"called": False, "reason": "诊断模式：不调用正式评分、不判门"}
        attempts.append(item)
    summary = {
        "schema": SCHEMA, "mode": mode, "plan_sha256": sha256_file(plan_path) if Path(plan_path).is_file() else None,
        "play_record": "present" if record is not None else "MISSING", "ops_log_bad_lines": ops_bad,
        "attempts": attempts,
        "failures": failures,
        "boundary": "自动摘要不代独立复核结论、不等于用户验收或门通过；按钮起止无可靠来源仍 UNKNOWN",
    }
    return summary


def render_markdown(summary: Mapping[str, Any]) -> str:
    lines = [f"# P1-ENG-LOOP-002 操作收尾摘要（{summary['mode']}；自动生成，不是独立复核/验收）", ""]
    for item in summary["attempts"]:
        lines.append(f"## {item['session_id']}（{item['playbook']}）")
        pva = item["plan_vs_actual"]
        lines.append(f"- 计划 ask/respecify {pva['designate_planned']}：发送 {pva['designate_sent']}、跳过（不在画面）"
                     f"{pva['designate_skipped_not_in_view']}、未执行 {pva['designate_not_executed']}、封住 {pva['designate_halted']}、"
                     f"记录未知 {pva['designate_record_unknown']}；步骤结局 {pva['counts']}")
        events = item["objective_events"]
        if isinstance(events, dict):
            lines.append(f"- 客观事件：TERMINAL={events['terminal_reason']}；进入 TRACKING {events['tracking_entries']} 次；"
                         f"释放 {events['releases_applied']}；疑似报告 {events['suspect_raised']}")
            for key, value in events["claims"].items():
                lines.append(f"  - {key}: {value}")
        else:
            lines.append(f"- 客观事件：{events}")
        lines.append(f"- 一致性问题：{len(item['consistency_issues'])}" + "".join(f"\n  - {i}" for i in item["consistency_issues"]))
        call = item.get("score_call") or {}
        lines.append(f"- 评分调用：{'rc=' + str(call.get('rc')) if call.get('called') else call.get('reason')}")
        lines.append(f"- 本人反馈：{item['user_feedback'] if isinstance(item['user_feedback'], str) else '见 feedback.jsonl'}")
        if item.get("stop"):
            lines.append(f"- STOP：{item['stop']}")
        lines.append("")
    for failure in summary.get("failures") or []:
        lines.append(f"- 摘要失败：{failure['code']} {failure['detail']}")
    lines.append(summary["boundary"])
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="summarize_ops", description=__doc__.splitlines()[0])
    parser.add_argument("--ops-dir", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--mode", choices=("formal", "diagnostic"), required=True)
    parser.add_argument("--python", default=sys.executable)
    arguments = parser.parse_args(argv)
    out_json = arguments.ops_dir / "ops-summary.json"
    out_md = arguments.ops_dir / "ops-summary.md"
    for path in (out_json, out_md):
        if path.exists():
            print(f"拒绝覆盖已有摘要 {path}（不重跑评分）", file=sys.stderr)
            return 2
    summary = summarize(arguments.ops_dir, arguments.plan, arguments.mode, arguments.python)
    text = json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n"
    summary["summary_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(summary), encoding="utf-8")
    print(f"OPS_SUMMARY {out_json}")
    if summary["failures"]:
        for failure in summary["failures"]:
            print(f"SUMMARY_FAILURE {failure['code']} {failure['detail']}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
