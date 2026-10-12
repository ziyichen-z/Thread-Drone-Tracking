"""§3.1.2 派生标签分层语义抽查（AR1-2；接受处置 AR2-1 的 AC-1 释义，逐字执行）。

- 层闭集：抽查前数据集（无 `STRATUM_IGNORED`）全部正样本的非空层
  `类别|状态|短边档|族组`（target 状态维记 `-`）。
- 排序：每框按 `SHA256("20260926|" + 层键 + "|" + 帧 sha + "|" + object_id)` 升序；层按层键字典序；
  逐轮各层取下一框（每层 ≤ 8），总数到 300 即停；每层至少一框。非空层数 > 300 或某层取不到
  一框 → `NOT_EVALUABLE`，训练不得开始。
- 判定闭集：框 `OK` / `LOOSE` / `WRONG` / `INVISIBLE`；整帧 `UNLABELED_VISIBLE_VEHICLE` 计数
  （可见 ≥12 px 车辆既无正样本框也无 ignore 框）。
- 处置（先写后查）：层 (WRONG+INVISIBLE)/n > 20% → 该层的「类别 × 状态 × 短边档」跨族组
  `STRATUM_IGNORED`；10%–20% → `STRATUM_FLAGGED`；族组整帧抽查中 UNLABELED 帧比例 > 10% →
  该族组 FP/帧标 `UNLABELED_RISK`。
- 盲法：图版只画派生框，不含任何模型输出（此时尚无模型）。

判定由抽查者（实现角色，离线看图）写入 `outputs/eng-det/spotcheck/judgments.json`；
`finalize` 计算处置并写 `docs/evidence/P1-ENG-FAST-002-spotcheck.json`。
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.eng_det import common, dataset

SEED = "20260926"
PER_LAYER_MAX = 8
TOTAL_MAX = 300
FRAMES_PER_GROUP = 10
BOX_LABELS = ("OK", "LOOSE", "WRONG", "INVISIBLE")
IGNORE_ABOVE = 0.20
FLAG_FROM = 0.10
UNLABELED_RISK_ABOVE = 0.10

SPOT_DIR = common.OUT_ROOT / "spotcheck"
SAMPLE_PATH = SPOT_DIR / "sample.json"
JUDGMENTS_PATH = SPOT_DIR / "judgments.json"
EVIDENCE_PATH = common.evidence("spotcheck.json")

# Q-2 CLARIFY（2026-09-28）：Q-1 重建 + 标签修订后，仅目标层按 AR2-1 同一算法重抽一次。
TARGET_SAMPLE_PATH = SPOT_DIR / "target-resample-sample.json"
TARGET_JUDGMENTS_PATH = SPOT_DIR / "target-resample-judgments.json"


class SpotcheckNotEvaluable(RuntimeError):
    """AR2-1：非空层 > 300 或某层取不到一框 → 训练不得开始，交用户。"""


def order_key(layer_key: str, frame_sha: str, object_id: str) -> str:
    return hashlib.sha256(f"{SEED}|{layer_key}|{frame_sha}|{object_id}".encode("utf-8")).hexdigest()


def frame_order_key(group: str, frame_sha: str) -> str:
    return hashlib.sha256(f"{SEED}|frame|{group}|{frame_sha}".encode("utf-8")).hexdigest()


def sample_boxes(candidates: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    """AR2-1 轮转抽样。`candidates`：层键 → [{frame_sha, object_id, ...}]（任意序）。"""
    layers = sorted(key for key, items in candidates.items() if items)
    if len(layers) > TOTAL_MAX:
        raise SpotcheckNotEvaluable(f"非空层 {len(layers)} > {TOTAL_MAX}")
    ordered = {}
    for key in layers:
        # 同一层内逐字节相同的帧（不同 frame_id、同 sha）上的同一对象是同一个框：按
        # (帧 sha, object_id) 去重（保留 frame_id 最小者），保证「每层不得重复框」。
        unique: dict[tuple[str, str], Mapping[str, Any]] = {}
        for c in sorted(candidates[key], key=lambda c: c.get("frame_id", "")):
            unique.setdefault((c["frame_sha"], c["object_id"]), c)
        ordered[key] = sorted(unique.values(), key=lambda c: order_key(key, c["frame_sha"], c["object_id"]))
    chosen: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for round_index in range(PER_LAYER_MAX):
        for key in layers:
            if len(chosen) >= TOTAL_MAX:
                break
            items = ordered[key]
            if round_index >= len(items):
                continue
            item = items[round_index]
            identity = (key, item["frame_sha"], item["object_id"])
            if identity in seen:
                raise SpotcheckNotEvaluable(f"层 {key} 重复框 {identity}")
            seen.add(identity)
            chosen.append({**item, "layer_key": key, "round": round_index})
    per_layer = Counter(item["layer_key"] for item in chosen)
    missing = [key for key in layers if per_layer[key] < 1]
    if missing:
        raise SpotcheckNotEvaluable(f"层取不到一框：{missing[:5]}")
    return chosen


def sample_frames(frames_by_group: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    chosen = []
    for group in sorted(frames_by_group):
        items = sorted(frames_by_group[group], key=lambda f: frame_order_key(group, f["frame_sha"]))
        chosen.extend({**item, "group": group} for item in items[:FRAMES_PER_GROUP])
    return chosen


def decide(samples: Sequence[Mapping[str, Any]], judgments: Mapping[str, str], frame_samples: Sequence[Mapping[str, Any]], frame_judgments: Mapping[str, int]) -> dict[str, Any]:
    """处置规则（纯函数）。缺任一判定 → `NOT_EVALUABLE`（不默认为通过）。"""
    missing = [str(s["sample_id"]) for s in samples if str(s["sample_id"]) not in judgments]
    missing_frames = [str(f["sample_id"]) for f in frame_samples if str(f["sample_id"]) not in frame_judgments]
    if missing or missing_frames:
        raise SpotcheckNotEvaluable(f"缺判定：框 {missing[:5]} 帧 {missing_frames[:5]}")
    bad = [s for s in samples if judgments[str(s["sample_id"])] not in BOX_LABELS]
    if bad:
        raise SpotcheckNotEvaluable(f"判定不在闭集：{[str(s['sample_id']) for s in bad][:5]}")
    per_layer: dict[str, Counter] = defaultdict(Counter)
    for s in samples:
        per_layer[s["layer_key"]][judgments[str(s["sample_id"])]] += 1
    layers = {}
    ignored: set[str] = set()
    for key, counter in sorted(per_layer.items()):
        n = sum(counter.values())
        rate = (counter["WRONG"] + counter["INVISIBLE"]) / n
        if rate > IGNORE_ABOVE:
            disposition = "STRATUM_IGNORED"
            cls_name, status, side, _group = key.split("|")
            ignored.add(dataset.layer_of(cls_name, status, side))
        elif rate >= FLAG_FROM:
            disposition = "STRATUM_FLAGGED"
        else:
            disposition = "KEEP"
        layers[key] = {"n": n, **{label: counter[label] for label in BOX_LABELS}, "bad_rate": round(rate, 6), "disposition": disposition}
    groups = {}
    for group in sorted({f["group"] for f in frame_samples}):
        items = [f for f in frame_samples if f["group"] == group]
        flagged = sum(1 for f in items if int(frame_judgments[str(f["sample_id"])]) > 0)
        ratio = flagged / len(items)
        groups[group] = {
            "frames": len(items),
            "frames_with_unlabeled_visible_vehicle": flagged,
            "unlabeled_vehicles_total": sum(int(frame_judgments[str(f["sample_id"])]) for f in items),
            "ratio": round(ratio, 6),
            "flag": "UNLABELED_RISK" if ratio > UNLABELED_RISK_ABOVE else None,
        }
    return {
        "layers": layers,
        "stratum_ignored_layers": sorted(ignored),
        "stratum_flagged": sorted(k for k, v in layers.items() if v["disposition"] == "STRATUM_FLAGGED"),
        "loose_total": sum(v["LOOSE"] for v in layers.values()),
        "groups": groups,
        "unlabeled_risk_groups": sorted(g for g, v in groups.items() if v["flag"]),
    }


# --- 抽样与图版 -------------------------------------------------------------


def build_sample() -> dict[str, Any]:
    _identity, rows = dataset.load_index(dataset.PRELIM_INDEX_PATH)
    candidates: dict[str, list[dict[str, Any]]] = defaultdict(list)
    frames_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["excluded"]:
            continue
        frames_by_group[row["group"]].append({"frame_id": row["frame_id"], "frame_sha": row["sha256"], "domain": row["domain"]})
        for p in row["positives"]:
            candidates[p["stratum"]].append(
                {
                    "frame_id": row["frame_id"],
                    "frame_sha": row["sha256"],
                    "object_id": p["object_id"],
                    "box": p["box"],
                    "status": p["status"],
                    "cls": p["cls"],
                    "side_px": p["side_px"],
                    "domain": row["domain"],
                }
            )
    boxes = sample_boxes(candidates)
    for number, item in enumerate(boxes, start=1):
        item["sample_id"] = f"B{number:03d}"
    frames = sample_frames(frames_by_group)
    for number, item in enumerate(frames, start=1):
        item["sample_id"] = f"F{number:03d}"
    document = {
        "seed": SEED,
        "layer_candidates": {key: len(items) for key, items in sorted(candidates.items())},
        "nonempty_layers": len(candidates),
        "boxes": boxes,
        "frames": frames,
    }
    common.write_json(SAMPLE_PATH, document)
    return document


def target_candidates(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """目标层候选：保留帧（非整帧排除）上的全部 `target` 正样本，按 `target|-|短边档|族组` 分层。

    Q-2 转 ignore 的目标框不在正样本里，因而不是候选（合同「不再作为正样本或目标层抽样候选」）。
    """
    pool: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["excluded"]:
            continue
        for p in row["positives"]:
            if p["cls"] != common.CLASS_TARGET:
                continue
            pool[p["stratum"]].append(
                {
                    "frame_id": row["frame_id"],
                    "frame_sha": row["sha256"],
                    "object_id": p["object_id"],
                    "box": p["box"],
                    "status": p["status"],
                    "cls": p["cls"],
                    "side_px": p["side_px"],
                    "domain": row["domain"],
                }
            )
    return dict(pool)


def build_target_resample() -> dict[str, Any]:
    _identity, rows = dataset.load_index(dataset.PRELIM_INDEX_PATH)
    pool = target_candidates(rows)
    boxes = sample_boxes(pool)
    for number, item in enumerate(boxes, start=1):
        item["sample_id"] = f"T{number:03d}"
    document = {
        "seed": SEED,
        "scope": "target layers only（Q-2 CLARIFY）",
        "prelim_index_sha256": common.sha256_file(dataset.PRELIM_INDEX_PATH),
        "layer_candidates": {key: len(items) for key, items in sorted(pool.items())},
        "nonempty_layers": len(pool),
        "boxes": boxes,
        "frames": [],
    }
    common.write_json(TARGET_SAMPLE_PATH, document)
    return document


def target_resample_disposition(
    samples: Sequence[Mapping[str, Any]], judgments: Mapping[str, str], vehicle_ignored_layers: Sequence[str]
) -> dict[str, Any]:
    """目标层重抽的处置（AR2-1 判定阈值与跨族组规则不变）；车辆层沿用原抽查结论。"""
    if any(not str(s["layer_key"]).startswith("target|") for s in samples):
        raise SpotcheckNotEvaluable("目标层重抽样本混入非目标层")
    if any(not layer.startswith("vehicle|") for layer in vehicle_ignored_layers):
        raise SpotcheckNotEvaluable("沿用的原抽查层只能是车辆层")
    decision = decide(samples, judgments, [], {})
    effective = sorted(set(vehicle_ignored_layers) | set(decision["stratum_ignored_layers"]))
    return {**decision, "target_ignored_layers": decision["stratum_ignored_layers"], "effective_stratum_ignored_layers": effective}


def render_sheets(tiles_per_sheet: int = 12, sample_path: Path = SAMPLE_PATH, prefix: str = "") -> list[str]:
    """框图版（每格：上下文裁剪 + 派生框）与整帧图版（2×2，全部正样本/ignore 框）。"""
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    document = common.read_json(sample_path)
    _identity, rows = dataset.load_index(dataset.PRELIM_INDEX_PATH)
    by_id = {row["frame_id"]: row for row in rows}
    out_dir = SPOT_DIR / "sheets"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    tile_w, tile_h = 300, 250
    boxes = document["boxes"]
    for start in range(0, len(boxes), tiles_per_sheet):
        chunk = boxes[start : start + tiles_per_sheet]
        sheet = np.full((tile_h * 3, tile_w * 4, 3), 40, dtype=np.uint8)
        for position, item in enumerate(chunk):
            image = cv2.imread(str(common.data_path(item["frame_id"])))
            x, y, w, h = [v * s for v, s in zip(item["box"], (640, 480, 640, 480))]
            margin = max(w, h, 24.0)
            x1, y1 = int(max(0, x - margin)), int(max(0, y - margin))
            x2, y2 = int(min(640, x + w + margin)), int(min(480, y + h + margin))
            crop = image[y1:y2, x1:x2].copy()
            scale = min((tile_w - 4) / crop.shape[1], (tile_h - 22) / crop.shape[0])
            crop = cv2.resize(crop, (max(1, int(crop.shape[1] * scale)), max(1, int(crop.shape[0] * scale))), interpolation=cv2.INTER_NEAREST if scale > 2 else cv2.INTER_LINEAR)
            bx1, by1 = int((x - x1) * scale), int((y - y1) * scale)
            bx2, by2 = int((x + w - x1) * scale), int((y + h - y1) * scale)
            color = (0, 0, 255) if item["cls"] == 1 else (0, 255, 0)
            cv2.rectangle(crop, (bx1, by1), (bx2, by2), color, 1)
            row, col = divmod(position, 4)
            oy, ox = row * tile_h + 20, col * tile_w + 2
            sheet[oy : oy + crop.shape[0], ox : ox + crop.shape[1]] = crop
            label = f"{item['sample_id']} {common.CLASS_NAMES[item['cls']][0]} {item['status'][:6]} {int(item['side_px'])}px"
            cv2.putText(sheet, label, (ox, row * tile_h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        path = out_dir / f"{prefix}boxes-{start // tiles_per_sheet + 1:02d}.png"
        cv2.imwrite(str(path), sheet)
        written.append(str(path))
    frames = document["frames"]
    for start in range(0, len(frames), 4):
        chunk = frames[start : start + 4]
        sheet = np.full((480 * 2 + 40, 640 * 2 + 10, 3), 40, dtype=np.uint8)
        for position, item in enumerate(chunk):
            row_data = by_id[item["frame_id"]]
            image = cv2.imread(str(common.data_path(item["frame_id"])))
            for ignore in row_data["ignores"]:
                x, y, w, h = [v * s for v, s in zip(ignore["box"], (640, 480, 640, 480))]
                cv2.rectangle(image, (int(x), int(y)), (int(x + w), int(y + h)), (0, 255, 255), 1)
            for p in row_data["positives"]:
                x, y, w, h = [v * s for v, s in zip(p["box"], (640, 480, 640, 480))]
                cv2.rectangle(image, (int(x), int(y)), (int(x + w), int(y + h)), (0, 0, 255) if p["cls"] == 1 else (0, 255, 0), 1)
            row, col = divmod(position, 2)
            oy, ox = row * (480 + 20) + 20, col * (640 + 10)
            sheet[oy : oy + 480, ox : ox + 640] = image
            cv2.putText(sheet, f"{item['sample_id']} {item['group']}", (ox, oy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        path = out_dir / f"{prefix}frames-{start // 4 + 1:02d}.png"
        cv2.imwrite(str(path), sheet)
        written.append(str(path))
    return written


def finalize() -> dict[str, Any]:
    sample = common.read_json(SAMPLE_PATH)
    judgments = common.read_json(JUDGMENTS_PATH)
    decision = decide(sample["boxes"], judgments["boxes"], sample["frames"], judgments["frames"])
    document = {
        "work_id": common.WORK_ID,
        "rule_source": "提案 §3.1.2 + 「用户选 (a) 后的接受处置」AR2-1 行（AC-1 释义）",
        "blind": "图版只画派生框，无任何模型输出（抽查先于训练）",
        "reviewer": "实现角色（离线看图，非 Play）",
        "seed": sample["seed"],
        "nonempty_layers": sample["nonempty_layers"],
        "layer_candidates": sample["layer_candidates"],
        "layer_order": "层键字典序；每层按 SHA256(\"20260926|\"+层键+\"|\"+帧sha+\"|\"+object_id) 升序；逐轮各取下一框，≤8/层，总 ≤300",
        "boxes": [
            {k: s[k] for k in ("sample_id", "layer_key", "round", "frame_id", "frame_sha", "object_id", "box", "side_px", "domain")}
            | {"judgment": judgments["boxes"][s["sample_id"]], "note": judgments.get("notes", {}).get(s["sample_id"])}
            for s in sample["boxes"]
        ],
        "frames": [
            {k: f[k] for k in ("sample_id", "group", "frame_id", "frame_sha", "domain")}
            | {"unlabeled_visible_vehicles": int(judgments["frames"][f["sample_id"]]), "note": judgments.get("frame_notes", {}).get(f["sample_id"])}
            for f in sample["frames"]
        ],
        **decision,
    }
    common.write_json(EVIDENCE_PATH, document)
    return document


def finalize_target_resample() -> dict[str, Any]:
    """把目标层重抽写进 `-spotcheck.json`：原 2026-09-27 抽查记录原样保留（`round1` 字段不改），
    新增 `target_resample`，顶层 `stratum_ignored_layers` 改为生效集（原车辆层 ∪ 新目标层）。"""
    original = common.read_json(EVIDENCE_PATH)
    round1_ignored = original.get("round1_stratum_ignored_layers", original["stratum_ignored_layers"])
    sample = common.read_json(TARGET_SAMPLE_PATH)
    judgments = common.read_json(TARGET_JUDGMENTS_PATH)
    vehicle_layers = [layer for layer in round1_ignored if layer.startswith("vehicle|")]
    decision = target_resample_disposition(sample["boxes"], judgments["boxes"], vehicle_layers)
    original["round1_stratum_ignored_layers"] = round1_ignored
    original["round1_note"] = (
        "顶层 layers/boxes/frames/groups 为 2026-09-27 原抽查（数据集未含 Q-1/Q-2）；其中 target 层处置已被 "
        "target_resample 取代，车辆层与整帧抽查结论沿用（Q-2 CLARIFY：车辆层不因本项重抽）"
    )
    original["target_resample"] = {
        "rule_source": "提案「Q-1/Q-2 用户选 (a) 后的 AC-n 合同修订（CLARIFY，2026-09-28）」AC-1（Q-2）行 + AR2-1 原算法",
        "blind": "图版只画派生框，无任何模型输出（重抽仍在训练前）；不参照原抽查判定",
        "reviewer": "实现角色（离线看图，非 Play）",
        "prelim_index_sha256": sample["prelim_index_sha256"],
        "nonempty_layers": sample["nonempty_layers"],
        "layer_candidates": sample["layer_candidates"],
        "boxes": [
            {k: s[k] for k in ("sample_id", "layer_key", "round", "frame_id", "frame_sha", "object_id", "box", "side_px", "domain")}
            | {"judgment": judgments["boxes"][s["sample_id"]], "note": judgments.get("notes", {}).get(s["sample_id"])}
            for s in sample["boxes"]
        ],
        "layers": decision["layers"],
        "target_ignored_layers": decision["target_ignored_layers"],
        "stratum_flagged": decision["stratum_flagged"],
        "loose_total": decision["loose_total"],
    }
    original["stratum_ignored_layers"] = decision["effective_stratum_ignored_layers"]
    round1_flagged = original.get("round1_stratum_flagged", original["stratum_flagged"])
    original["round1_stratum_flagged"] = round1_flagged
    original["stratum_flagged"] = sorted(
        [k for k in round1_flagged if not k.startswith("target|")] + list(decision["stratum_flagged"])
    )
    common.write_json(EVIDENCE_PATH, original)
    return original


def load_decision() -> dict[str, Any]:
    """训练前置门：抽查证据必须存在且可评估（AC-1「在训练前完成」）。

    Q-2 CLARIFY 之后还要求目标层重抽已完成（`target_resample` 存在）。"""
    if not EVIDENCE_PATH.exists():
        raise SpotcheckNotEvaluable("抽查证据缺失：训练不得开始")
    document = common.read_json(EVIDENCE_PATH)
    if "target_resample" not in document:
        raise SpotcheckNotEvaluable("Q-2 目标层重抽未完成：训练不得开始")
    return {"stratum_ignored_layers": document["stratum_ignored_layers"], "sha256": common.sha256_file(EVIDENCE_PATH)}


def main(argv: Sequence[str] | None = None) -> None:
    import argparse  # noqa: PLC0415

    parser = argparse.ArgumentParser(description="§3.1.2 分层语义抽查")
    parser.add_argument("mode", choices=("sample", "sheets", "finalize", "target-sample", "target-sheets", "target-finalize"))
    args = parser.parse_args(argv)
    if args.mode == "sample":
        document = build_sample()
        print(json.dumps({"nonempty_layers": document["nonempty_layers"], "boxes": len(document["boxes"]), "frames": len(document["frames"])}))
    elif args.mode == "sheets":
        print("\n".join(render_sheets()))
    elif args.mode == "target-sample":
        document = build_target_resample()
        print(json.dumps({"nonempty_layers": document["nonempty_layers"], "boxes": len(document["boxes"]), "layer_candidates": document["layer_candidates"]}))
    elif args.mode == "target-sheets":
        print("\n".join(render_sheets(sample_path=TARGET_SAMPLE_PATH, prefix="target-resample-")))
    elif args.mode == "target-finalize":
        document = finalize_target_resample()
        print(json.dumps({"effective_ignored": document["stratum_ignored_layers"], "target_resample": document["target_resample"]["layers"]}, ensure_ascii=False))
    else:
        document = finalize()
        print(json.dumps({"ignored": document["stratum_ignored_layers"], "flagged": document["stratum_flagged"], "unlabeled_risk": document["unlabeled_risk_groups"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
