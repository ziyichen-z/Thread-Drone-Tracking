"""P1 分桶召回与 FP/帧（合同 §3.3、§3.2.2、AC-2/AC-3）。

命中：真值框在同帧检测输出（类别无关，score ≥ 0.25 已在检测层过滤）中 max IoU ≥ 阈值；
双口径 0.30 / 0.50 并列。每格给 `hit/n`、bootstrap 95% CI（2,000 轮，seed 20260923）。
斜距表（scout-1/scout-4/BODY-001）与轴向深度表（609 行的 448 目录帧）分表、不合并。
FP/帧 = 未与任何真值框（IoU ≥ 0.30）匹配的检测数 / 帧，按来源分列，**只作描述**。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Sequence

from tools.eng_fast import common
from tools.eng_fast.inputs import FrameRec, GTObject

FP_MATCH_IOU = 0.30
NOT_AUTHORIZED = "N/A(NOT_AUTHORIZED_T1_UNSIGNED)"
NO_SESSION_REFERENCE = "N/A(NO_SESSION_REFERENCE)"
BANK_EMPTY = "N/A(BANK_EMPTY)"


def max_iou(box: Sequence[float], dets: Sequence[Sequence[float]]) -> float:
    return max((common.iou_xywh(box, det[:4]) for det in dets), default=0.0)


def instance_flag(obj: GTObject, bank_object_ids: set[str]) -> str:
    if obj.kind == common.TARGET_KIND_PRIMITIVE:
        return "same_instance_by_design"
    if obj.object_id is None:
        return "INSTANCE_UNKNOWN"
    return "same_instance_in_bank" if obj.object_id in bank_object_ids else "not_in_bank"


def object_outcomes(
    frames: Iterable[FrameRec],
    detections: Mapping[str, Sequence[Sequence[float]]],
    bank_object_ids: set[str],
) -> list[dict[str, Any]]:
    """每个真值对象一行：分桶键 + 两口径命中。缺检测记录即失败（不静默跳过）。"""
    outcomes = []
    for frame in frames:
        if not frame.objects:
            continue
        if frame.path not in detections:
            raise KeyError(f"检测缓存缺帧 {frame.path}")
        dets = detections[frame.path]
        for obj in frame.objects:
            best = max_iou(obj.box, dets)
            outcomes.append(
                {
                    "path": frame.path,
                    "object_id": obj.object_id,
                    "kind": obj.kind,
                    "instance": instance_flag(obj, bank_object_ids),
                    "stratum": common.stratum_of(common.short_side_px(obj.box)),
                    "distance_bin": common.distance_bin(obj.distance_m),
                    "max_iou": round(best, 6),
                    "hit_030": best >= 0.30,
                    "hit_050": best >= 0.50,
                }
            )
    return outcomes


def _cell(outcomes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    n = len(outcomes)
    hits30 = [bool(item["hit_030"]) for item in outcomes]
    hits50 = [bool(item["hit_050"]) for item in outcomes]
    return {
        "n": n,
        "hit_030": sum(hits30),
        "hit_050": sum(hits50),
        "rate_030": round(sum(hits30) / n, 6) if n else None,
        "rate_050": round(sum(hits50) / n, 6) if n else None,
        "ci95_030": common.bootstrap_ci(hits30),
        "ci95_050": common.bootstrap_ci(hits50),
    }


def bucket_table(outcomes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """按 种类 × 实例标记 × (短边 × 距离档 全交叉 + 两条单轴边际) 出格；不出单一总召回。"""
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for item in outcomes:
        grouped[(item["kind"], item["instance"])].append(item)
    table: dict[str, Any] = {}
    for (kind, instance), items in sorted(grouped.items()):
        cross: dict[str, Any] = {}
        by_stratum: dict[str, Any] = {}
        by_distance: dict[str, Any] = {}
        for stratum in (*common.STRATA, "NA"):
            subset = [i for i in items if i["stratum"] == stratum]
            if subset:
                by_stratum[stratum] = _cell(subset)
            for distance in (*common.DISTANCE_BINS, "NA"):
                cell = [i for i in subset if i["distance_bin"] == distance]
                if cell:
                    cross[f"{stratum}|{distance}"] = _cell(cell)
        for distance in (*common.DISTANCE_BINS, "NA"):
            subset = [i for i in items if i["distance_bin"] == distance]
            if subset:
                by_distance[distance] = _cell(subset)
        table[f"{kind}|{instance}"] = {
            "stratum_x_distance": cross,
            "by_stratum": by_stratum,
            "by_distance": by_distance,
        }
    return table


def fp_per_frame(
    frames: Iterable[FrameRec], detections: Mapping[str, Sequence[Sequence[float]]]
) -> dict[str, Any]:
    count_frames = 0
    false_positives = 0
    detections_total = 0
    for frame in frames:
        if not frame.has_truth:
            continue
        if frame.path not in detections:
            raise KeyError(f"检测缓存缺帧 {frame.path}")
        count_frames += 1
        truths = [obj.box for obj in frame.objects]
        for det in detections[frame.path]:
            detections_total += 1
            if max_iou(det[:4], [list(t) for t in truths]) < FP_MATCH_IOU:
                false_positives += 1
    return {
        "frames": count_frames,
        "detections": detections_total,
        "unmatched_detections": false_positives,
        "fp_per_frame": round(false_positives / count_frames, 6) if count_frames else None,
        "note": "描述性；真值清单之外的场景车辆被检出也计为未匹配（scout 真值只列 1–2 辆干扰车，BODY 真值不列干扰车）",
    }


# --- AC-3：旧数复算 --------------------------------------------------------


def legacy_alignment(
    legacy: Mapping[str, Any],
    frames_by_number: Mapping[int, FrameRec],
    detections: Mapping[str, Sequence[Sequence[float]]],
    *,
    expected: Mapping[str, int],
) -> dict[str, Any]:
    """以旧结果的逐 tick 样本（帧号 + 状态）为 tick 计划，用 T0-oracle 复算命中并逐格对照。

    旧口径：conf ≥ 0.25、IoU ≥ 0.30；scout-1 的 `MISSING_*` tick 计为漏（`COUNT_AS_RECALL_MISS`），
    scout-4 分母 = `PAIRED_VISIBLE`。
    """
    samples = legacy["samples"]
    rows = []
    hits = 0
    denominator = 0
    mismatches = []
    for sample in samples:
        status = sample.get("status") or sample.get("accounting_class")
        if status in ("MISSING_SENSOR_FRAME", "MISSING_IMAGE_TRUTH_PAIR", "TARGET_BOX_MISSING"):
            denominator += 1
            rows.append({"tick_index": sample["tick_index"], "status": status, "hit": False, "legacy_hit": False})
            continue
        if status not in ("REMOTE_VISIBLE", "PAIRED_VISIBLE"):
            continue
        denominator += 1
        frame = frames_by_number.get(int(sample["frame_id"]))
        if frame is None or frame.target_box is None:
            raise KeyError(f"旧样本帧 {sample['frame_id']} 在当前输入中无目标真值框")
        best = max_iou(frame.target_box, detections[frame.path])
        hit = best >= 0.30
        hits += int(hit)
        legacy_hit = bool(sample["recall_hit"])
        legacy_iou = sample.get("maximum_target_iou")
        if hit != legacy_hit:
            mismatches.append(sample["tick_index"])
        rows.append(
            {
                "tick_index": sample["tick_index"],
                "frame_id": int(sample["frame_id"]),
                "status": status,
                "max_iou": round(best, 6),
                "legacy_max_iou": legacy_iou,
                "hit": hit,
                "legacy_hit": legacy_hit,
            }
        )
    legacy_iou_deltas = [
        abs(row["max_iou"] - row["legacy_max_iou"])
        for row in rows
        if row.get("legacy_max_iou") is not None and "max_iou" in row
    ]
    aligned = hits == expected["hits"] and denominator == expected["denominator"] and not mismatches
    return {
        "expected": dict(expected),
        "recomputed": {"hits": hits, "denominator": denominator},
        "per_tick_hit_mismatches": mismatches,
        "max_abs_iou_delta_vs_legacy": round(max(legacy_iou_deltas), 6) if legacy_iou_deltas else None,
        "aligned": aligned,
        "disposition": "ALIGNED" if aligned else "MISALIGNED_STOP_CITING_LEGACY",
        "ticks": rows,
    }
