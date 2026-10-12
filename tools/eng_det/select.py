"""选择与冻结（合同 §3.2、AC-2、AC-13）：conf / run / 关联算法与参数三项选择**只引用 V 读数**。

- `vtable --run R`：R 的 `last.pt` 在 V（a7 整族，不抽帧）上检测一次，按 {0.25, 0.40} 两个 conf 出表 V
  （标 `SELECTION_DOMAIN`）与 V-门；conf 规则：两者中使 V FP/帧 ≤ 0.50 的最小值，都不满足取 0.40 并标
  `CONF_FLOOR_NOT_MET`。
- `decide-run2`：run-1 任一 V-门未过（含 NOT_EVALUABLE）→ 需要 run-2（imgsz 960）。
- `assoc`：选定 run 与 conf 后，在 V 序列上跑 {ByteTrack, BoT-SORT(GMC)} × match {0.8, 0.7} × buffer {30, 60}，
  取 13 s 保持率（口径 A）最高者；并列依次取 ByteTrack、buffer 30、match 0.8。
- `freeze`：写 `-freeze.json` 与 `config/det-assoc-v1.models.json`。冻结后禁止训练与选择变更。

所有选择函数的输入表都带 `domain` 标签；非 `V` 一律拒绝（`SelectionRefused`，test:`tests.test_eng_det_select`）。
实现读法 IR-5：规格文件含冻结文件 sha，冻结文件记「去掉 `freeze` 字段的规格核心 sha」（避免互相引用的环）。
"""

from __future__ import annotations

import datetime as _dt
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.eng_det import common, dataset, evaluate
from tools.eng_det.ledger import Ledger
from tools.eng_det.train import FREEZE_EVIDENCE, TRAIN_EVIDENCE, load_train_evidence, save_train_evidence

V_FAMILIES = ("p1-vlm-survey-a7-p1-c1-s1",)
SPEC_PATH = common.PROJECT_ROOT / "config" / "det-assoc-v1.models.json"
SELECT_DIR = common.OUT_ROOT / "select"
DETS_DIR = common.OUT_ROOT / "dets"
NMS_IOU = 0.7  # ultralytics predict 缺省 iou（不做超参搜索）
ASSOC_GRID: tuple[tuple[str, float, int], ...] = tuple(
    (algorithm, match, buffer) for algorithm in ("bytetrack", "botsort") for match in (0.8, 0.7) for buffer in (30, 60)
)
V_GATE_KEYS = ("V-1", "V-1s", "V-2", "V-3")


class SelectionRefused(RuntimeError):
    """选择输入不是 V（H 零参与）或冻结后再选。"""


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def require_v(item: Mapping[str, Any]) -> None:
    if item.get("domain") != "V":
        raise SelectionRefused(f"选择只接受 V 读数，收到 domain={item.get('domain')!r}")


def choose_conf(results_by_conf: Mapping[float, Mapping[str, Any]]) -> dict[str, Any]:
    for result in results_by_conf.values():
        require_v(result)
    ordered = sorted(results_by_conf)
    if tuple(ordered) != evaluate.CONF_CANDIDATES:
        raise SelectionRefused(f"conf 候选须为 {evaluate.CONF_CANDIDATES}")
    for conf in ordered:
        value = results_by_conf[conf]["fp_per_frame_050"]
        if value is not None and value <= 0.50:
            return {"conf": conf, "flag": None, "basis": {str(c): results_by_conf[c]["fp_per_frame_050"] for c in ordered}}
    return {"conf": 0.40, "flag": "CONF_FLOOR_NOT_MET", "basis": {str(c): results_by_conf[c]["fp_per_frame_050"] for c in ordered}}


def gates_passed(v_gates: Mapping[str, Any]) -> int:
    return sum(1 for key in V_GATE_KEYS if v_gates[key]["verdict"] == evaluate.MET)


def needs_run2(run1: Mapping[str, Any]) -> bool:
    require_v(run1)
    return gates_passed(run1["v_gates"]) < len(V_GATE_KEYS)


def choose_run(candidates: Sequence[Mapping[str, Any]]) -> str:
    """V-门通过数最多者；并列取 V target S 召回 @0.5 高者；再并列取 run-1。"""
    for item in candidates:
        require_v(item)
    if not candidates:
        raise SelectionRefused("无有效 run")

    def key(item: Mapping[str, Any]) -> tuple[int, float, int]:
        s_rate = item["table"]["classes"]["target"]["by_stratum"]["S"]["rate_050"] or 0.0
        return (gates_passed(item["v_gates"]), float(s_rate), 1 if item["run_id"] == "run-1" else 0)

    return max(candidates, key=key)["run_id"]


def choose_association(results: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    """13 s 保持率最高；并列依次取 ByteTrack、buffer 30、match 0.8。"""
    for item in results:
        require_v(item)

    def key(item: Mapping[str, Any]) -> tuple[float, int, int, int]:
        retention = item["pooled_13s"]["retention"] if item["pooled_13s"] else -1.0
        return (
            float(retention if retention is not None else -1.0),
            1 if item["algorithm"] == "bytetrack" else 0,
            1 if item["track_buffer"] == 30 else 0,
            1 if item["match_thresh"] == 0.8 else 0,
        )

    return max(results, key=key)


# --- CLI 动作 ---------------------------------------------------------------


def _refuse_if_frozen() -> None:
    if FREEZE_EVIDENCE.exists():
        raise SelectionRefused("冻结文件已存在：本项内禁止选择变更（AC-13）")


def _run_record(run_id: str) -> Mapping[str, Any]:
    for run in load_train_evidence()["runs"]:
        if run["run_id"] == run_id:
            if run["status"] != "DONE":
                raise SelectionRefused(f"{run_id} 状态 {run['status']}，不是有效 run")
            return run
    raise SelectionRefused(f"未知 run {run_id}")


def v_rows() -> list[dict[str, Any]]:
    _identity, rows = dataset.load_index()
    chosen = [r for r in rows if r["domain"] == "V"]
    if {r["family"] for r in chosen} != set(V_FAMILIES):
        raise SelectionRefused("V 域族与 §3.1.1 不符")
    return chosen


def vtable(run_id: str, device: str = "mps") -> dict[str, Any]:
    _refuse_if_frozen()
    run = _run_record(run_id)
    weights = common.PROJECT_ROOT / run["last_pt"]["path"]
    if common.sha256_file(weights) != run["last_pt"]["sha256"]:
        raise SelectionRefused("last.pt sha 与训练记录不符")
    rows = v_rows()
    detector = evaluate.Detector(weights, run["imgsz"], device, label=f"select-vtable-{run_id}", ledger=Ledger())
    dets = evaluate.detect_frames(detector, [r["frame_id"] for r in rows], DETS_DIR / f"{run_id}-V.jsonl.gz")
    results = {}
    for conf in evaluate.CONF_CANDIDATES:
        result = evaluate.evaluate(rows, dets, conf)
        result["domain"] = "V"
        results[conf] = result
    chosen = choose_conf(results)
    main = results[chosen["conf"]]
    table = evaluate.recall_table(main["outcomes"], "V", "SELECTION_DOMAIN")
    side = results[[c for c in evaluate.CONF_CANDIDATES if c != chosen["conf"]][0]]
    record = {
        "run_id": run_id,
        "domain": "V",
        "tag": "SELECTION_DOMAIN",
        "at": _now(),
        "weights_sha256": run["last_pt"]["sha256"],
        "imgsz": run["imgsz"],
        "device": device,
        "conf_choice": chosen,
        "table": table,
        "fp": {str(c): {k: v for k, v in r.items() if k != "outcomes"} for c, r in results.items()},
        "table_other_conf_descriptive": evaluate.recall_table(side["outcomes"], "V", "SELECTION_DOMAIN|OTHER_CONF_DESCRIPTIVE"),
        "v_gates": evaluate.detection_gates(table, main, "V"),
    }
    common.write_json(SELECT_DIR / f"{run_id}-vtable.json", record)
    document = load_train_evidence()
    document.setdefault("selection", {}).setdefault("vtables", {})[run_id] = {
        k: record[k] for k in ("run_id", "domain", "tag", "at", "weights_sha256", "imgsz", "device", "conf_choice", "fp", "v_gates")
    } | {"table_by_stratum": {c: record["table"]["classes"][c]["by_stratum"] for c in common.CLASS_NAMES}}
    save_train_evidence(document)
    return record


def load_vtable(run_id: str) -> dict[str, Any]:
    return common.read_json(SELECT_DIR / f"{run_id}-vtable.json")


def v_sequences(track_buffer: int) -> tuple[list[list[Mapping[str, Any]]], dict[str, Any]]:
    pieces: list[list[Mapping[str, Any]]] = []
    stats = {}
    for session, rows in evaluate.sessions(v_rows(), V_FAMILIES).items():
        kept, info = evaluate.split_subsequences(rows, track_buffer)
        pieces.extend(kept)
        stats[session] = info
    return pieces, stats


def assoc(run_id: str) -> dict[str, Any]:
    _refuse_if_frozen()
    record = load_vtable(run_id)
    require_v(record)
    conf = record["conf_choice"]["conf"]
    rows = v_rows()
    run = _run_record(run_id)
    # 复用 vtable 的 V 检测缓存（同权重 sha/imgsz/device），不再启动模型。
    dets = _cached_dets(DETS_DIR / f"{run_id}-V.jsonl.gz", run["last_pt"]["sha256"])
    results = []
    for algorithm, match, buffer in ASSOC_GRID:
        pieces, stats = v_sequences(buffer)
        replays = [evaluate.replay_piece(p, dets, conf, algorithm, match, buffer) for p in pieces]
        results.append(
            {
                "domain": "V",
                "algorithm": algorithm,
                "match_thresh": match,
                "track_buffer": buffer,
                "subsequences": stats,
                "pooled_13s": evaluate.pool_windows(replays, "13s"),
                "pooled_8s": evaluate.pool_windows(replays, "8s"),
                "id_switches": sum(r["sequence"]["id_switches"] for r in replays),
                "fragments": sum(r["sequence"]["fragments"] for r in replays),
                "max_interval_s": max((r["max_interval_s"] for r in replays), default=None),
            }
        )
        print(json.dumps({"algorithm": algorithm, "match": match, "buffer": buffer, "r13": results[-1]["pooled_13s"]}), flush=True)
    chosen = choose_association(results)
    document = load_train_evidence()
    document.setdefault("selection", {})["association"] = {
        "run_id": run_id,
        "conf": conf,
        "domain": "V",
        "tag": "SELECTION_DOMAIN",
        "grid": results,
        "chosen": {k: chosen[k] for k in ("algorithm", "match_thresh", "track_buffer")},
        "at": _now(),
    }
    save_train_evidence(document)
    return document["selection"]["association"]


def _cached_dets(path: Path, weights_sha256: str) -> dict[str, list[list[float]]]:
    rows = common.read_jsonl(path)
    if rows[0]["header"]["weights_sha256"] != weights_sha256:
        raise SelectionRefused("V 检测缓存与权重不符")
    return {r["frame_id"]: r["dets"] for r in rows[1:]}


def spec_core_sha256(spec: Mapping[str, Any]) -> str:
    core = {k: v for k, v in spec.items() if k != "freeze"}
    return common.sha256_bytes(common.json_bytes(core))


def freeze(run_ids: Sequence[str]) -> dict[str, Any]:
    _refuse_if_frozen()
    document = load_train_evidence()
    candidates = [load_vtable(r) for r in run_ids]
    chosen_run = choose_run(candidates)
    association = document["selection"]["association"]
    if association["run_id"] != chosen_run:
        raise SelectionRefused(f"关联选择基于 {association['run_id']}，与选定 run {chosen_run} 不符")
    record = load_vtable(chosen_run)
    run = _run_record(chosen_run)
    weights_rel = run["last_pt"]["path"]
    chosen_assoc = association["chosen"]
    args = evaluate.frozen_tracker_args(chosen_assoc["algorithm"], chosen_assoc["match_thresh"], chosen_assoc["track_buffer"])
    spec: dict[str, Any] = {
        "schema_version": "tethered-tracker-models/v1",
        "tracker": "det-assoc-v1",
        "ultralytics_version": "8.4.104",
        "weights": {"path": weights_rel, "sha256": run["last_pt"]["sha256"], "size_bytes": run["last_pt"]["bytes"]},
        "imgsz": run["imgsz"],
        "conf": record["conf_choice"]["conf"],
        "nms_iou": NMS_IOU,
        "classes": {"0": "vehicle", "1": "target"},
        "device_policy": {"preferred": "mps", "fallback": "cpu"},
        "association": {"algorithm": chosen_assoc["algorithm"], "args": args},
        "provenance": {"work_id": common.WORK_ID, "run_id": chosen_run, "selection": "V only（SELECTION_DOMAIN）"},
    }
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=common.PROJECT_ROOT).stdout.strip()
    runs = document["runs"]
    frozen = {
        "work_id": common.WORK_ID,
        "frozen_at": _now(),
        "git_head_at_freeze": head,
        "weights": {"path": weights_rel, "sha256": run["last_pt"]["sha256"], "bytes": run["last_pt"]["bytes"]},
        "spec_path": common.rel_project(SPEC_PATH),
        "spec_core_sha256": spec_core_sha256(spec),
        "conf": spec["conf"],
        "conf_flag": record["conf_choice"]["flag"],
        "imgsz": spec["imgsz"],
        "nms_iou": NMS_IOU,
        "association": {"algorithm": chosen_assoc["algorithm"], "match_thresh": chosen_assoc["match_thresh"], "track_buffer": chosen_assoc["track_buffer"], "args": args},
        "v_gates": record["v_gates"],
        "valid_runs": [r["run_id"] for r in runs if r["status"] == "DONE"],
        "all_runs": [{"run_id": r["run_id"], "status": r["status"], "ended_at": r.get("ended_at")} for r in runs],
        "chosen_run": chosen_run,
        "selection_basis": {
            "run_rule": "V-门通过数最多；并列取 V target S @0.5 高者；再并列 run-1",
            "per_run": {c["run_id"]: {"v_gates_passed": gates_passed(c["v_gates"]), "target_S_rate_050": c["table"]["classes"]["target"]["by_stratum"]["S"]["rate_050"]} for c in candidates},
            "conf_rule": "{0.25, 0.40} 中使 V FP/帧 ≤ 0.50 的最小值",
            "association_rule": "V 序列 13 s 保持率最高；并列 ByteTrack → buffer 30 → match 0.8",
        },
        "h_used_in_selection": False,
    }
    common.write_json(FREEZE_EVIDENCE, frozen)
    spec["freeze"] = {"path": common.rel_project(FREEZE_EVIDENCE), "sha256": common.sha256_file(FREEZE_EVIDENCE)}
    common.write_json(SPEC_PATH, spec)
    return frozen


def main(argv: Sequence[str] | None = None) -> None:
    import argparse  # noqa: PLC0415

    parser = argparse.ArgumentParser(description="P1-ENG-FAST-002 选择与冻结（只看 V）")
    sub = parser.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("vtable")
    p.add_argument("--run", required=True)
    p.add_argument("--device", default="mps")
    p = sub.add_parser("decide-run2")
    p = sub.add_parser("assoc")
    p.add_argument("--run", required=True)
    p = sub.add_parser("freeze")
    p.add_argument("--runs", nargs="+", required=True)
    args = parser.parse_args(argv)
    if args.mode == "vtable":
        record = vtable(args.run, args.device)
        print(json.dumps({"conf": record["conf_choice"], "v_gates": {k: v["verdict"] for k, v in record["v_gates"].items()}}, ensure_ascii=False))
    elif args.mode == "decide-run2":
        print(json.dumps({"needs_run2": needs_run2(load_vtable("run-1"))}))
    elif args.mode == "assoc":
        print(json.dumps(assoc(args.run)["chosen"]))
    else:
        frozen = freeze(args.runs)
        print(json.dumps({k: frozen[k] for k in ("chosen_run", "conf", "imgsz", "association")}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
