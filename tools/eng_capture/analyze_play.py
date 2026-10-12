"""P1-ENG-CAPTURE-001 AC-22…25（停点 `PlayK2K4`）：唯一一次 Play 的离线读数（零模型加载）。

输入：捕获会话目录（`language-session.jsonl`、`publish-receipts.jsonl`、`tm_inputs.jsonl`）、点击页原流
（`click-web.jsonl`）、配置 `config/p1-eng-capture-001.json`，以及 Unity 真值 `m3_body_truth.jsonl`。
**真值只进本文件 `score_` 前缀函数**（AC-16 静态检查）；本模块不被 `controller/` 或 `click_web.py` 导入。

口径（同名提案 §4 AC-22…25 原文，冻结）：
* AC-22：分母 = 全部发出的点击（含被拒、超时、UNKNOWN、未绑定）；e2e = 提交帧历史头 − 页面收到点击时
  `latest.json` 的 frame_id；受理子段 = 提交帧历史头 − 消费时历史头；e2e ≤ 1 且已绑定为该次 PASS。
* AC-23：被跟实例在每次失去已接受观测后要么窗口内修复、要么在 age = T_report/T_repair 准时报告；
  SUPPORTED 期间被跟实例不是红车的帧数照记（= 0 只是本次观察，不作风险上界）。
* AC-24：授权行 7 成立帧都有 `predicted_look_at` WRITTEN；逐窗按 AC-18 同一 IoU 口径判 PASS/FAIL/NOT_EVALUABLE。
* AC-25：S2 提交时真值水平距离 d₀；N = ⌈(d₀ − 14)/(v_max − v_target)⌉ + t_lead + slack（d₀ ≤ 14 取常数项）；
  进带 = N 内进入 [10, 14] m；保持 = 进带后至 S4 首次点击前授权 FOLLOW 的全部帧都在带内；d₀ < 10 → NOT_EVALUABLE。
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(REPO_ROOT))

from controller import target_manager as tm  # noqa: E402

WIDTH, HEIGHT = 640, 480


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# --- AC-22 点击时延（无真值） --------------------------------------------------------------


def click_latency(click_log: Sequence[Mapping[str, Any]], journal: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """逐次点击：页面收到时 latest、提交帧历史头、消费时历史头；被拒/未绑定/UNKNOWN 也在分母（AC-22 原文）。

    R1-3：每次点击按自身 `click_id` 配对（`click_submitted` 给 click_id → request_id；缺该行时退回 `submit_begin`/`refused`
    记录 binding 内的 click_id），**不按数组位置**——页面本地拒绝（在途/已封/重复/stop 已发）只记 `refused`、不记
    `submit_begin`，被拒点击单独成行且 request_id 为空。页面拒收的畸形点击（`click_refused`）同样计入分母。
    另记墙钟（描述）：已绑定行 = 提交事件 `at_unix_s` − 页面收到点击 `click_received_unix_s`（同机时钟）。"""
    received = [r for r in click_log if r.get("kind") in ("click_received", "click_refused")]
    replies = {r.get("request_id"): r for r in click_log if r.get("kind") == "submit_result"}
    submitted = {r.get("click_id"): r for r in click_log if r.get("kind") == "click_submitted" and r.get("click_id")}
    begins = {(r.get("binding") or {}).get("click_id"): r for r in click_log
              if r.get("kind") == "submit_begin" and r.get("action") == "click" and (r.get("binding") or {}).get("click_id")}
    page_refusals = {(r.get("binding") or {}).get("click_id"): r for r in click_log
                     if r.get("kind") == "refused" and r.get("action") == "click" and (r.get("binding") or {}).get("click_id")}
    committed = {r.get("evidence", {}).get("request_id"): r for r in journal if r.get("kind") == "binding_committed" and r.get("origin") == "click"}
    consumed = {r.get("request_id"): r for r in journal if r.get("kind") == "click_received"}
    rows = []
    for index, click in enumerate(received):
        click_id = click.get("click_id")
        outcome = submitted.get(click_id) if click_id else None
        begin = begins.get(click_id) if click_id else None
        refusal = page_refusals.get(click_id) if click_id else None
        if click.get("kind") == "click_refused":
            request_id, refused, refused_reason = None, True, click.get("reason")
        elif outcome is not None:
            request_id, refused = outcome.get("request_id"), bool(outcome.get("refused"))
            refused_reason = None if not refused else (refusal or {}).get("reason") or outcome.get("message")
        else:
            request_id = None if begin is None else begin.get("request_id")
            refused = refusal is not None and begin is None
            refused_reason = None if refusal is None else refusal.get("reason")
        reply = replies.get(request_id) if request_id else None
        commit = committed.get(request_id) if request_id else None
        consume = consumed.get(request_id) if request_id else None
        latest = click.get("latest_frame_id_at_click")
        commit_head = None if commit is None else commit.get("frame_id")
        consume_head = None if consume is None else (consume.get("page") or {}).get("head_at_consume")
        e2e = None if commit_head is None or latest is None else int(commit_head) - int(latest)
        accepted = None if commit_head is None or consume_head is None else int(commit_head) - int(consume_head)
        verdict = "PASS" if commit is not None and e2e is not None and e2e <= 1 else "FAIL"
        received_unix = click.get("click_received_unix_s")
        wall = None if commit is None or received_unix is None or commit.get("at_unix_s") is None else float(commit["at_unix_s"]) - float(received_unix)
        rows.append({
            "index": index + 1, "click_id": click_id, "request_id": request_id, "refused": refused, "refused_reason": refused_reason,
            "frame_id_clicked": click.get("frame_id"), "click_received_unix_s": received_unix,
            "latest_frame_id_at_click": latest, "commit_head": commit_head, "consume_head": consume_head,
            "e2e_frames": e2e, "acceptance_subsegment_frames": accepted, "bound": commit is not None,
            "commit_event_seq": None if commit is None else commit.get("event_seq"),
            "unknown": bool(reply and reply.get("unknown")) or bool(outcome and outcome.get("unknown")),
            "receipt": None if reply is None else reply.get("receipt"),
            "wall_s": wall, "wall_note": "描述（commit at_unix_s − 页面收到点击 click_received_unix_s，同机时钟），不是门",
            "verdict": verdict,
        })
    return {
        "denominator": len(rows),
        "verdict": "PASS" if rows and all(r["verdict"] == "PASS" for r in rows) else ("NOT_EVALUABLE" if not rows else "FAIL"),
        "acceptance_subsegment_all_le_1": all(r["acceptance_subsegment_frames"] is not None and r["acceptance_subsegment_frames"] <= 1 for r in rows) if rows else None,
        "rows": rows,
    }


# --- 真值（只在 score_） ----------------------------------------------------------------


def score_truth(path: Path) -> dict[int, dict[str, Any]]:
    return {int(r["frame_id"]): r for r in read_jsonl(path)}


def score_truth_box(row: Mapping[str, Any] | None) -> tuple[float, float, float, float] | None:
    if not row or not row.get("truth_box_available") or not row.get("geometrically_visible", True):
        return None
    return (float(row["truth_box_x"]), float(row["truth_box_y"]), float(row["truth_box_width"]), float(row["truth_box_height"]))


def _iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return 0.0 if union <= 0 else inter / union


def frame_states(inputs: Sequence[Mapping[str, Any]], events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """由落盘 reducer 输入重放（`controller.target_manager` 同一实现）得到逐帧信念与绑定框（无真值）。"""
    frames = []
    for line in inputs:
        if line.get("kind") != "frame":
            continue
        frames.append({"frame_id": int(line["frame_id"]), "history": line["history"]})
    return frames


def red_car_segment_start(per_frame: Sequence[Mapping[str, Any]], commit_frame: int, commit_event_seq: int | None) -> int:
    """红车段起点（无真值）：S2 提交之后**第一个按新绑定授权的帧**——授权事件序号在 S2 提交事件之后、帧号 ≥ 提交帧。
    IR-C2-1：消费时 k 已处理的点击在历史头提交，该帧已发效果仍属旧绑定，不算进红车段；追平路径（k 帧授权前提交）
    起点即提交帧。缺事件序号时退回提交帧。"""
    if commit_event_seq is None:
        return int(commit_frame)
    for record in sorted(per_frame, key=lambda r: (r["frame_id"], r.get("event_seq") or 0)):
        if record["frame_id"] >= int(commit_frame) and (record.get("event_seq") or 0) > int(commit_event_seq):
            return int(record["frame_id"])
    return int(commit_frame)


def score_red_car_loop(per_frame: Sequence[Mapping[str, Any]], events: Sequence[Mapping[str, Any]], truth: Mapping[int, Mapping[str, Any]],
                       params: tm.CaptureParams, *, segment: tuple[int | None, int | None]) -> dict[str, Any]:
    """AC-23：`per_frame` = 逐帧 {frame_id, continuity, observation, age, observed_box_norm}（来自重放）。

    R1-3(d)：只在红车段 `segment` = [S2 提交后首个新绑定授权帧（`red_car_segment_start`）, S4 首次点击帧) 内统计
    （AC-23「红车 ≥ 1 圈内」；端点 None = 不限）；
    段外（S1 静止车阶段、S4 之后）的失观测与确认跟踪帧不计入。段末仍未结束的失观测照列（`ended_at` 为 None），其
    报告/到期截止落在段内而未发生即记不准时，落在段外则记 None（段外不判）。"""
    first, end = segment
    inside = [r for r in per_frame if (first is None or r["frame_id"] >= first) and (end is None or r["frame_id"] < end)]
    wrong = []
    losses = []
    current = None
    for record in inside:
        f = record["frame_id"]
        truth_box = score_truth_box(truth.get(f))
        if record.get("continuity") == tm.SUPPORTED and record.get("observation") == tm.OBSERVED and record.get("observed_box_norm") and truth_box:
            if _iou(record["observed_box_norm"], truth_box) < 0.5:
                wrong.append(f)
        if record.get("observation") == tm.PREDICTED and current is None:
            current = {"lost_from": f, "t0": f - (record.get("age") or 1)}
        if current is not None and (record.get("observation") == tm.OBSERVED or record.get("continuity") in (tm.BROKEN, tm.DISPUTED)):
            current["ended_at"] = f
            current["ended_as"] = record.get("continuity") if record.get("observation") != tm.OBSERVED else "observed"
            losses.append(current)
            current = None
    if current is not None:
        current["ended_at"] = None
        current["ended_as"] = "open_at_segment_end"
        losses.append(current)
    last = inside[-1]["frame_id"] if inside else None
    reports = {e.get("frame_id"): e for e in events if e.get("type") == "report"}
    broken = {e.get("frame_id"): e for e in events if e.get("type") == "continuity" and e.get("reason") == "continuity_broken"}
    for loss in losses:
        t0 = loss["t0"]
        report_frame, broken_frame = t0 + params.t_report, t0 + params.t_repair
        if loss["ended_at"] is not None:
            loss["report_on_time"] = report_frame in reports or loss["ended_at"] < report_frame
            loss["broken_on_time"] = loss.get("ended_as") != tm.BROKEN or broken_frame in broken
        else:
            loss["report_on_time"] = (report_frame in reports) if last is not None and report_frame <= last else None
            loss["broken_on_time"] = (broken_frame in broken) if last is not None and broken_frame <= last else None
    return {"segment": [first, end], "frames_in_segment": len(inside),
            "supported_frames_not_red_car": wrong, "supported_frames_not_red_car_count": len(wrong),
            "note": "=0 只是本次样本观察，不作风险上界（USER-4A 第 4 项）", "losses": losses,
            "all_losses_on_time": all(l["report_on_time"] is not False and l["broken_on_time"] is not False for l in losses)}


def score_body_band(truth: Mapping[int, Mapping[str, Any]], s2_frame: int, s4_frame: int | None, follow_frames: Iterable[int],
                    formula: Mapping[str, Any], hz: float = 5.0, *, authorized_frames: Iterable[int] | None = None) -> dict[str, Any]:
    """AC-25：进带与保持分别判；另报带内比例、全部越界帧原值与非 FOLLOW 帧数。

    R1-3(c)：保持窗 = [进带帧, S4 首次点击帧)（无 S4 时到最后一个已授权帧为止）。授权 FOLLOW 但缺真值的帧**不计入带内**，
    单列 `follow_frames_without_truth`（证据缺失：保持项不判 PASS，记 EVIDENCE_MISSING；不从带内比例分母去掉）；
    `non_follow_frames` = 保持窗内已授权而非 FOLLOW 的帧数（`authorized_frames` = 有授权事件的帧；未给出时记 None，`main` 总是给出）。"""
    def horizontal(row: Mapping[str, Any]) -> float:
        return math.hypot(float(row["target_world_x_m"]) - float(row["body_world_x_m"]), float(row["target_world_z_m"]) - float(row["body_world_z_m"]))

    low, high = formula["band_m"]
    authorized = None if authorized_frames is None else sorted(int(f) for f in authorized_frames)
    if s2_frame not in truth:
        return {"d0_m": None, "entry": "EVIDENCE_MISSING", "hold": "EVIDENCE_MISSING", "verdict": "EVIDENCE_MISSING",
                "reason": "no truth row at the S2 commit frame"}
    d0 = horizontal(truth[s2_frame])
    if d0 < float(formula["not_evaluable_below_m"]):
        return {"d0_m": d0, "entry": "NOT_EVALUABLE", "verdict": "NOT_EVALUABLE"}
    extra = max(0.0, math.ceil((d0 - high) / (formula["v_max_mps"] - formula["v_target_mps"]))) if d0 > high else 0.0
    n_s = extra + formula["t_lead_s"] + formula["slack_s"]
    deadline = s2_frame + int(math.ceil(n_s * hz))
    entered = next((f for f in sorted(truth) if s2_frame <= f <= deadline and low <= horizontal(truth[f]) <= high), None)
    if s4_frame is not None:
        end = s4_frame
    else:
        end = max([*(authorized or []), *truth]) + 1
    follow_set = {int(f) for f in follow_frames}
    follow = sorted(f for f in follow_set if entered is not None and entered <= f < end)
    missing = [f for f in follow if f not in truth]
    outside = [{"frame_id": f, "distance_m": horizontal(truth[f])} for f in follow if f in truth and not low <= horizontal(truth[f]) <= high]
    inside = len(follow) - len(outside) - len(missing)
    non_follow = None if authorized is None else [f for f in authorized if entered is not None and entered <= f < end and f not in follow_set]
    entry_ok = entered is not None
    hold = "FAIL" if not entry_ok or outside else ("EVIDENCE_MISSING" if missing else "PASS")
    verdict = "FAIL" if not entry_ok or hold == "FAIL" else hold
    return {"d0_m": d0, "N_s": n_s, "deadline_frame": deadline, "entered_frame": entered, "hold_window": [entered, end],
            "entry": "PASS" if entry_ok else "FAIL", "hold": hold, "verdict": verdict,
            "in_band_fraction": None if not follow else inside / len(follow), "outside_frames": outside,
            "follow_frames": len(follow), "follow_frames_without_truth": missing, "non_follow_frames": None if non_follow is None else len(non_follow)}


def velocity_only_on_supported(receipts: Sequence[Mapping[str, Any]], authorizations: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    """S-B-UNSAFE / AC-25 末句：非 OBSERVED+SUPPORTED 帧不得有 WRITTEN 速度型 `body_command`。"""
    bad = [r.get("frame_id") for r in receipts if r.get("channel") == "body_command" and r.get("outcome") == "WRITTEN"
           and (authorizations.get(r.get("frame_id")) or {}).get("result", {}).get("row") != 6]
    return {"violations": bad, "ok": not bad}


def per_frame_from_logs(journal: Sequence[Mapping[str, Any]], inputs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """逐帧状态（无真值）：授权事件给 continuity/observation/age；绑定键 = 该授权事件**之前**最后一次提交（按 event_seq；
    C1-3：标某帧号、却在该帧授权之后才发生的提交不改写该帧，状态与效果同属一个版本）；观测框 = 该帧落盘历史中绑定键的
    tracked 行框（OBSERVED 帧）；另带策略后原始检测与各键同帧 prior（AC-24 按 AC-18 原检测定义独立评分）。"""
    commits = sorted((r.get("event_seq", 0), r.get("new_track_key")) for r in journal if r.get("kind") == "binding_committed")
    history = {int(line["frame_id"]): line["history"] for line in inputs if line.get("kind") == "frame"}
    out = []
    for event in sorted((r for r in journal if r.get("kind") == "authorization"), key=lambda r: (r["frame_id"], r.get("event_seq", 0))):
        f = int(event["frame_id"])
        key = None
        for seq, track_key in commits:
            if seq < event.get("event_seq", 0):
                key = track_key
        box = None
        entry = history.get(f)
        priors: dict[str, list[float]] = {}
        raw: list[list[float]] = []
        if entry is not None:
            library_frame_id = entry.get("library_frame_id")
            for snap in entry.get("prior_snapshots", []) or []:
                if (snap.get("valid") and snap.get("phase") == "prior" and snap.get("sensor_frame_id") == f
                        and snap.get("library_frame_id") == library_frame_id):
                    priors[str(snap["track_key"])] = [float(v) for v in snap["xywh_px"]]
            raw = [[*(float(v) for v in det["box_px"]), float(det.get("conf", 0.0)), float(det.get("cls", 0))]
                   for det in entry.get("raw_detections", []) or []]
            if key is not None:
                row = next((t for t in entry["tracks"] if t["track_id"] == key), None)
                if row is not None and event["inputs"]["observation"] == tm.OBSERVED:
                    box = row["box_norm"]
        out.append({"frame_id": f, "event_seq": event.get("event_seq"), "continuity": event["inputs"]["continuity"], "observation": event["inputs"]["observation"],
                    "age": event["inputs"]["age"], "row": event["result"]["row"], "observed_box_norm": box,
                    "prior_xywh_px": None if key is None else priors.get(str(key)), "track_key": key,
                    "raw_detections_px": raw, "priors_xywh_px": priors})
    return out


def _px_to_norm(box_px: Sequence[float]) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = (float(v) for v in box_px[:4])
    return (x1 / WIDTH, y1 / HEIGHT, (x2 - x1) / WIDTH, (y2 - y1) / HEIGHT)


def score_prediction_windows(per_frame: Sequence[Mapping[str, Any]], receipts: Sequence[Mapping[str, Any]],
                             truth: Mapping[int, Mapping[str, Any]], params: tm.CaptureParams) -> dict[str, Any]:
    """AC-24：行 7 帧都有 `predicted_look_at` WRITTEN；逐窗按 AC-18 同一口径判 IoU（C1-2 / 预复核关注项）：下一次真实观测 =
    窗口后 T_repair 帧内首个与真值 IoU ≥ 0.5 的**策略后原始检测**（不要求被接受），预测框 = 该窗口原绑定键在该帧的同帧 prior；
    无此检测 → NOT_EVALUABLE；原键无同帧 prior → 记证据缺失（EVIDENCE_MISSING，原因 `original_key_same_frame_prior_missing`；
    用户 2026-10-10 IR-C2-5 裁定：不扩 NOT_EVALUABLE、不从分母去掉、不计通过——该窗留在可评分母内，总判不为 PASS）。"""
    written = {r.get("frame_id") for r in receipts if r.get("channel") == "predicted_look_at" and r.get("outcome") == "WRITTEN"}
    by_frame = {r["frame_id"]: r for r in per_frame}
    windows: list[list[int]] = []
    for record in per_frame:
        if record["row"] == 7:
            if windows and windows[-1][-1] == record["frame_id"] - 1:
                windows[-1].append(record["frame_id"])
            else:
                windows.append([record["frame_id"]])
    rows = []
    for window in windows:
        end = window[-1]
        original = by_frame[window[0]].get("track_key")
        found = None
        for f in range(end + 1, end + 1 + params.t_repair):
            record = by_frame.get(f)
            truth_box = score_truth_box(truth.get(f))
            if record is None or truth_box is None:
                continue
            best = None
            for det in record.get("raw_detections_px") or []:
                iou = _iou(_px_to_norm(det), truth_box)
                if iou >= 0.5 and (best is None or iou > best[1]):
                    best = (list(det[:4]), iou)
            if best is not None:
                found = (f, best[0])
                break
        reason = None
        prior = None if found is None or original is None else (by_frame[found[0]].get("priors_xywh_px") or {}).get(str(original))
        if found is None:
            verdict, iou, reason = "NOT_EVALUABLE", None, "no_detection_matching_truth_within_t_repair"
        elif prior is None:
            verdict, iou, reason = "EVIDENCE_MISSING", None, "original_key_same_frame_prior_missing"
        else:
            xc, yc, w, h = prior
            iou = _iou(((xc - w / 2) / WIDTH, (yc - h / 2) / HEIGHT, w / WIDTH, h / HEIGHT), _px_to_norm(found[1]))
            verdict = "PASS" if iou >= 0.3 else "FAIL"
        rows.append({"window": window, "original_key": original, "all_look_at_written": set(window) <= written, "iou": iou,
                     "verdict": verdict, "not_evaluable_reason": reason, "next_observation_frame": None if found is None else found[0]})
    evaluable = [r for r in rows if r["verdict"] != "NOT_EVALUABLE"]  # EVIDENCE_MISSING 留在分母内（IR-C2-5）
    if not evaluable:
        overall = "NOT_EVALUABLE"
    elif any(r["verdict"] == "FAIL" or not r["all_look_at_written"] for r in evaluable):
        overall = "FAIL"
    elif any(r["verdict"] == "EVIDENCE_MISSING" for r in evaluable):
        overall = "EVIDENCE_MISSING"
    else:
        overall = "PASS"
    return {"verdict": overall, "n_windows": len(rows), "n_evaluable": len(evaluable), "rows": rows}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-CAPTURE-001 Play 读数（AC-22…25，零模型）")
    parser.add_argument("--session-dir", type=Path, required=True)
    parser.add_argument("--click-log", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--s2-click", type=int, required=True, help="S2（红车）是第几次点击（1 起）")
    parser.add_argument("--s4-click", type=int, default=None, help="S4 首次点击是第几次点击（1 起）")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args(argv)
    params, _sha, text = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)
    formula = json.loads(text)["body_band_formula"]
    journal = read_jsonl(arguments.session_dir / "language-session.jsonl")
    inputs = read_jsonl(arguments.session_dir / tm.INPUTS_FILE)
    receipts = read_jsonl(arguments.session_dir / "publish-receipts.jsonl")
    clicks = read_jsonl(arguments.click_log)
    truth = score_truth(arguments.truth)
    latency = click_latency(clicks, journal)
    per_frame = per_frame_from_logs(journal, inputs)
    tm_events = [r for r in journal if r.get("kind") in ("tm_event", "tm_transition", "binding_committed")]
    authorizations = {r["frame_id"]: r for r in journal if r.get("kind") == "authorization"}
    s2 = latency["rows"][arguments.s2_click - 1]["commit_head"] if len(latency["rows"]) >= arguments.s2_click else None
    s4 = None
    if arguments.s4_click is not None and len(latency["rows"]) >= arguments.s4_click:
        s4 = latency["rows"][arguments.s4_click - 1]["latest_frame_id_at_click"]
    # R1-3(d)：AC-23 只在红车段 [S2 提交后首个新绑定授权帧, S4 首次点击帧) 内统计；S2 未绑定 → 无红车段（与 AC-25 同记 NOT_EVALUABLE）。
    red_car = ({"verdict": "NOT_EVALUABLE", "reason": "S2 not bound"} if s2 is None
               else score_red_car_loop(per_frame, tm_events, truth, params,
                                       segment=(red_car_segment_start(per_frame, int(s2), latency["rows"][arguments.s2_click - 1]["commit_event_seq"]), s4)))
    report: dict[str, Any] = {"AC-22": latency, "AC-23": red_car,
                              "AC-24": score_prediction_windows(per_frame, receipts, truth, params)}
    follow = [f for f, r in authorizations.items() if r["result"]["body"] == tm.FOLLOW]
    report["AC-25"] = ({"verdict": "NOT_EVALUABLE", "reason": "S2 not bound"} if s2 is None
                       else score_body_band(truth, int(s2), s4, follow, formula, authorized_frames=authorizations))
    report["AC-25"]["velocity_only_on_supported"] = velocity_only_on_supported(receipts, authorizations)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v.get("verdict") for k, v in report.items()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
