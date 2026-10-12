"""D3 合格判定（合同 §3.3、§3.4、§3.4.1；AC-3/AC-4/AC-13）：冻结后在 H 上**只评一次**。

一次 `run` 调用完成全部 H 读数（表 A、FP/帧、G-1…G-3、口径 A 的 G-6、口径 B 的 H 插件回放），
开始读 H 之前先过 `FreezeGuard`：冻结文件与规格文件存在且互相核对、权重 sha 一致、所有训练 run
结束早于冻结时刻；然后扣 `h_evaluation`（上限 1，第 2 次 fail-closed）。
表 B / G-4 / G-5（演示路线，T 内，`TRAINED_ON_ATOM`）与口径 B 的 V、scout-1 读数同一次运行出数，
表 V 取自选择记录（`SELECTION_DOMAIN`）。输出 `-recall.json`、`-replay.json`。
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.eng_det import common, dataset, evaluate, plugin_replay
from tools.eng_det.ledger import Ledger
from tools.eng_det.train import FREEZE_EVIDENCE, TRAIN_EVIDENCE, load_train_evidence

SPEC_PATH = common.PROJECT_ROOT / "config" / "det-assoc-v1.models.json"
RECALL_EVIDENCE = common.evidence("recall.json")
REPLAY_EVIDENCE = common.evidence("replay.json")
DETS_DIR = common.OUT_ROOT / "dets"
QUALIFY_DIR = common.OUT_ROOT / "qualify"

H_SEQUENCE_FAMILIES = (
    "m3-armB",
    "s004-scout",
    "p1-vlm-survey-a3-p1-c1-s1",
    "p1-vlm-survey-a4-p1-c1-s1",
    "p1-vlm-survey-a6-p1-c1-s1",
    "p1-vlm-survey-a9-p1-c1-s1",
)
SCOUT1_FAMILY = "detect-scout1"
ARM_A_FAMILY = "m3-armA"
TABLE_B_FAMILIES = (SCOUT1_FAMILY, ARM_A_FAMILY)
V_FAMILIES = ("p1-vlm-survey-a7-p1-c1-s1",)


class FreezeGuardRefused(RuntimeError):
    """AC-13：无冻结、sha 不符、冻结后仍有 run，或第 2 次 H 评估。"""


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class FreezeGuard:
    def __init__(self, freeze_path: Path = FREEZE_EVIDENCE, spec_path: Path = SPEC_PATH, train_path: Path = TRAIN_EVIDENCE, ledger: Ledger | None = None):
        self.freeze_path = Path(freeze_path)
        self.spec_path = Path(spec_path)
        self.train_path = Path(train_path)
        self.ledger = ledger or Ledger()

    def verify(self) -> dict[str, Any]:
        """只读核对（不扣额）；任一不符抛 `FreezeGuardRefused`。"""
        from tools.eng_det.select import spec_core_sha256  # noqa: PLC0415

        if not self.freeze_path.exists():
            raise FreezeGuardRefused("冻结文件不存在：拒绝读取 H")
        if not self.spec_path.exists():
            raise FreezeGuardRefused("规格文件不存在：拒绝读取 H")
        frozen = common.read_json(self.freeze_path)
        spec = common.read_json(self.spec_path)
        if spec.get("freeze", {}).get("sha256") != common.sha256_file(self.freeze_path):
            raise FreezeGuardRefused("规格文件记录的冻结文件 sha 不符")
        if spec_core_sha256(spec) != frozen["spec_core_sha256"]:
            raise FreezeGuardRefused("规格核心 sha 与冻结文件不符")
        weights = common.PROJECT_ROOT / frozen["weights"]["path"]
        if not weights.exists() or common.sha256_file(weights) != frozen["weights"]["sha256"]:
            raise FreezeGuardRefused("权重 sha 与冻结文件不符")
        if spec["weights"]["sha256"] != frozen["weights"]["sha256"]:
            raise FreezeGuardRefused("规格权重 sha 与冻结文件不符")
        runs = common.read_json(self.train_path)["runs"] if self.train_path.exists() else []
        late = [r["run_id"] for r in runs if not r.get("ended_at") or r["ended_at"] >= frozen["frozen_at"]]
        if late:
            raise FreezeGuardRefused(f"存在未早于冻结时刻结束的 run：{late}")
        return {"frozen": frozen, "spec": spec, "weights": weights}

    def charge_h(self) -> None:
        if self.ledger.used("h_evaluation") >= 1:
            raise FreezeGuardRefused("H 已评估 1 次：第 2 次 fail-closed（AC-13）")
        self.ledger.charge("h_evaluation", 1, freeze_sha256=common.sha256_file(self.freeze_path))


def _rows_for(rows: Sequence[Mapping[str, Any]], families: Sequence[str]) -> list[Mapping[str, Any]]:
    return [r for r in rows if r["family"] in families]


def _pieces(rows: Sequence[Mapping[str, Any]], families: Sequence[str], buffer: int) -> tuple[dict[str, list], dict[str, Any]]:
    out: dict[str, list] = {}
    stats: dict[str, Any] = {}
    for session, items in evaluate.sessions(rows, families).items():
        kept, info = evaluate.split_subsequences(items, buffer)
        out[session] = kept
        stats[session] = info
    return out, stats


def _replay_sessions(pieces_by_session, dets, frozen) -> dict[str, list[dict[str, Any]]]:
    assoc = frozen["association"]
    return {
        session: [evaluate.replay_piece(p, dets, frozen["conf"], assoc["algorithm"], assoc["match_thresh"], assoc["track_buffer"]) for p in pieces]
        for session, pieces in pieces_by_session.items()
    }


def _family_of_session(rows: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    return {r["session"]: r["family"] for r in rows}


def run(device: str = "mps") -> dict[str, Any]:
    guard = FreezeGuard()
    context = guard.verify()
    frozen, weights = context["frozen"], context["weights"]
    ledger = guard.ledger
    _identity, rows = dataset.load_index()
    guard.charge_h()  # 从这里起才读取 H
    started = _now()
    h_rows = [r for r in rows if r["domain"] == "H"]
    b_rows = _rows_for([r for r in rows if r["domain"] == "T"], TABLE_B_FAMILIES)
    v_rows = [r for r in rows if r["domain"] == "V"]
    detector = evaluate.Detector(weights, frozen["imgsz"], device, label="qualify-frozen", ledger=ledger)
    h_dets = evaluate.detect_frames(detector, [r["frame_id"] for r in h_rows if not r["excluded"]], DETS_DIR / "frozen-H.jsonl.gz")
    b_dets = evaluate.detect_frames(detector, [r["frame_id"] for r in b_rows], DETS_DIR / "frozen-B.jsonl.gz")
    v_dets = evaluate.detect_frames(detector, [r["frame_id"] for r in v_rows], DETS_DIR / "frozen-V.jsonl.gz")
    conf = float(frozen["conf"])
    other = [c for c in evaluate.CONF_CANDIDATES if c != conf][0]

    # --- 表 A（H）与 G-1…G-3 ---
    h_main = evaluate.evaluate(h_rows, h_dets, conf, evaluate.distance_with_slant)
    h_other = evaluate.evaluate(h_rows, h_dets, other, evaluate.distance_with_slant)
    table_a = evaluate.recall_table(h_main["outcomes"], "H", "HELD_OUT")
    gates = evaluate.detection_gates(table_a, h_main, "G")
    fp_by_family = {}
    for family in sorted({r["family"] for r in h_rows}):
        subset = [r for r in h_rows if r["family"] == family]
        result = evaluate.evaluate(subset, h_dets, conf) if any(not r["excluded"] for r in subset) else None
        fp_by_family[family] = None if result is None else {k: v for k, v in result.items() if k != "outcomes"}

    # --- 表 B（演示路线，TRAINED_ON_ATOM）与 G-4（斜距 50–65 / ≥65 m 目标，IoU 0.3）---
    b_main = evaluate.evaluate(b_rows, b_dets, conf, evaluate.distance_with_slant)
    table_b = evaluate.recall_table(b_main["outcomes"], "T", "TRAINED_ON_ATOM")
    g4_cells = {}
    for bin_ in ("50-65", ">=65"):
        items = [o for o in b_main["outcomes"] if o["cls"] == "target" and o["axis"] == "slant" and o["distance_bin"] == bin_]
        g4_cells[f"target|slant|{bin_}"] = evaluate.recall_cell_verdict(evaluate.cell(items), 0.80, "rate_030")
    gates["G-4"] = evaluate.gate(g4_cells)

    # --- 表 V（选择域，描述性；冻结 run 的选择记录）---
    selection = load_train_evidence()["selection"]["vtables"][frozen["chosen_run"]]

    # --- 口径 A：G-5（T 内演示路线）与 G-6（H 合并）---
    buffer = int(frozen["association"]["track_buffer"])
    all_dets = {**h_dets, **b_dets, **v_dets}
    scout_pieces, scout_stats = _pieces(b_rows, (SCOUT1_FAMILY,), buffer)
    arm_a_pieces, arm_a_stats = _pieces(b_rows, (ARM_A_FAMILY,), buffer)
    h_pieces, h_stats = _pieces(h_rows, H_SEQUENCE_FAMILIES, buffer)
    scout_replay = _replay_sessions(scout_pieces, all_dets, frozen)
    arm_a_replay = _replay_sessions(arm_a_pieces, all_dets, frozen)
    h_replay = _replay_sessions(h_pieces, all_dets, frozen)
    family_of = _family_of_session(rows)
    flat = lambda d: [p for pieces in d.values() for p in pieces]  # noqa: E731
    g5 = {
        "scout-1": evaluate.retention_verdict(evaluate.pool_windows(flat(scout_replay), "13s"), 0.90),
        "m3-armA(D>0 段合并)": evaluate.retention_verdict(evaluate.pool_windows(flat(arm_a_replay), "13s"), 0.90),
    }
    gates["G-5"] = evaluate.gate(g5)
    gates["G-6"] = evaluate.gate({"H 合并": evaluate.retention_verdict(evaluate.pool_windows(flat(h_replay), "13s"), 0.80)})
    per_family_13s = {}
    for family in H_SEQUENCE_FAMILIES:
        pieces = [p for s, ps in h_replay.items() if family_of[s] == family for p in ps]
        per_family_13s[family] = {
            "13s": evaluate.pool_windows(pieces, "13s"),
            "8s": evaluate.pool_windows(pieces, "8s"),
            "report_only_verdict": evaluate.retention_verdict(evaluate.pool_windows(pieces, "13s"), 0.80),
        }
    fast001_comparison = {}
    for label, source in (
        ("scout-1（TRAINED_ON_ATOM）", scout_replay),
        ("scout-4（H）", {s: p for s, p in h_replay.items() if "scout-4" in s}),
        ("BODY arm A 五段（TRAINED_ON_ATOM）", {s: p for s, p in arm_a_replay.items() if "p1-m3-body-001-arm-a" in s}),
    ):
        fast001_comparison[label] = {
            "sessions": sorted(source),
            "13s": evaluate.pool_windows(flat(source), "13s"),
            "8s": evaluate.pool_windows(flat(source), "8s"),
        }

    # --- 口径 B：插件本体（V、H、scout-1）---
    from controller.det_assoc_tracker import DetAssocTracker  # noqa: PLC0415

    ledger.charge("model_start", 1, label="qualify-plugin-caliber-B", device=device)
    plugin = DetAssocTracker(spec_path=SPEC_PATH, device=device)
    v_pieces, v_stats = _pieces(v_rows, V_FAMILIES, buffer)
    caliber_b: dict[str, Any] = {}
    carrier_reference = None
    full_records = {}
    for label, pieces_by_session in (("V", v_pieces), ("H", h_pieces), ("scout-1", scout_pieces)):
        records = []
        for session, pieces in pieces_by_session.items():
            for piece in pieces:
                truths = [evaluate.target_truth(r) for r in piece]
                record = plugin_replay.run_piece(plugin, piece, truths, evaluate.read_image)
                record["session"] = session
                record["family"] = family_of[session]
                records.append(record)
        full_records[label] = records
        caliber_b[label] = plugin_replay.pool(records)
        if label == "H":
            caliber_b["H_by_family"] = {
                family: plugin_replay.pool([r for r in records if r["family"] == family]) for family in H_SEQUENCE_FAMILIES
            }
        if label == "scout-1":
            chosen = next((r for r in records if r.get("init") == "OK" and r.get("per_frame")), None)
            if chosen is not None:
                piece_frames = next(p for s, ps in scout_pieces.items() for p in ps if p[0]["frame_id"] == chosen["first_frame"])
                carrier_reference = {
                    "session": chosen["session"],
                    "frames": [r["frame_id"] for r in piece_frames[chosen["init_index"] :]],
                    "init_frame": chosen["init_frame"],
                    "init_box": chosen["init_box"],
                    "plugin_manifest": dict(plugin.manifest_identity()),
                    "per_frame": [{k: f[k] for k in ("frame_id", "state", "box", "reason")} for f in chosen["per_frame"]],
                    "library_frame_id_after_init": chosen["library_frame_id_after_init"],
                }
    common.write_json(QUALIFY_DIR / "caliber-b-full.json", full_records)
    finished = _now()

    recall = {
        "work_id": common.WORK_ID,
        "h_evaluation": {"started_at": started, "finished_at": finished, "count": 1},
        "freeze_sha256": common.sha256_file(FREEZE_EVIDENCE),
        "conf": conf,
        "other_conf_descriptive": other,
        "table_A_H": table_a,
        "fp_H": {k: v for k, v in h_main.items() if k != "outcomes"},
        "fp_H_other_conf_descriptive": {k: v for k, v in h_other.items() if k != "outcomes"},
        "table_A_H_other_conf_descriptive": evaluate.recall_table(h_other["outcomes"], "H", "HELD_OUT|OTHER_CONF_DESCRIPTIVE"),
        "fp_H_by_family": fp_by_family,
        "table_B_demo_route": table_b,
        "fp_B": {k: v for k, v in b_main.items() if k != "outcomes"},
        "table_V_selection": selection,
        "gates": {k: gates[k] for k in ("G-1", "G-1s", "G-2", "G-3", "G-4")},
        "h_frames": {"retained": sum(1 for r in h_rows if not r["excluded"]), "excluded": sum(1 for r in h_rows if r["excluded"])},
    }
    common.write_json(RECALL_EVIDENCE, recall)
    replay_doc = {
        "work_id": common.WORK_ID,
        "freeze_sha256": common.sha256_file(FREEZE_EVIDENCE),
        "association": frozen["association"],
        "conf": conf,
        "caliber_A": {
            "tag": "口径 A（关联层能力，每帧真值 IoU ≥ 0.30 重绑定，FAST-001 R4 同口径）",
            "subsequences": {"scout-1": scout_stats, "m3-armA": arm_a_stats, "H": h_stats},
            "G-5_cells_TRAINED_ON_ATOM": g5,
            "H_pooled": {"13s": evaluate.pool_windows(flat(h_replay), "13s"), "8s": evaluate.pool_windows(flat(h_replay), "8s")},
            "H_by_family": per_family_13s,
            "fast001_same_sequence_comparison": fast001_comparison,
            "sequence_metrics_totals": {
                name: {
                    "id_switches": sum(p["sequence"]["id_switches"] for p in flat(data)),
                    "fragments": sum(p["sequence"]["fragments"] for p in flat(data)),
                    "max_interval_s": max((p["max_interval_s"] for p in flat(data)), default=None),
                }
                for name, data in (("scout-1", scout_replay), ("m3-armA", arm_a_replay), ("H", h_replay))
            },
            "pieces": {"scout-1": scout_replay, "m3-armA": arm_a_replay, "H": h_replay},
        },
        "caliber_B": caliber_b,
        "caliber_B_subsequences_V": v_stats,
        "carrier_reference": carrier_reference,
        "gates": {k: gates[k] for k in ("G-5", "G-6")},
    }
    common.write_json(REPLAY_EVIDENCE, replay_doc)
    return {"gates": {k: v["verdict"] for k, v in gates.items()}, "started": started, "finished": finished}


def main(argv: Sequence[str] | None = None) -> None:
    import argparse  # noqa: PLC0415

    parser = argparse.ArgumentParser(description="P1-ENG-FAST-002 H 一次评估（冻结后）")
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("--device", default="mps")
    args = parser.parse_args(argv)
    if args.mode == "verify":
        context = FreezeGuard().verify()
        print(json.dumps({"frozen_at": context["frozen"]["frozen_at"], "weights": context["frozen"]["weights"]}, ensure_ascii=False))
    else:
        print(json.dumps(run(args.device), ensure_ascii=False))


if __name__ == "__main__":
    main()
