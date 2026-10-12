#!/usr/bin/env python3
"""表 F 评分、表 G 判定与表 L 跨环境结论（本地专用；纯标准库）。

冻结闭集成员，但**不进 K3 代码束**：评分与判定只在本地对回传预测执行，gold
文件永不上云。云端只用 `prompt_v2` / `parse` 产出预测行。

分母纪律：每组的分母是该组 manifest 的全部 gate 行，解析失败、缺框、状态错都
留在分母里，不剔除（表 F 第一行）。预测文件与 manifest 必须一一对应，缺行 /
重复 / 多余即整次 `PREDICTIONS_INCOMPLETE`，不评分。
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import itertools
import json
from pathlib import Path
import random
import sys
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_sft import receipts  # noqa: E402

IOU_THRESHOLD = 0.5
BOOTSTRAP_ROUNDS = 2000
BOOTSTRAP_SEED = 20260912
BOOTSTRAP_PERCENTILES = (2.5, 97.5)

# 表 G 功能门阈值（D3 接受时冻结）。
GATE_G3_REPORT_MIN = 0.70
GATE_G3_STRICT_MIN = 0.50
GATE_FALSE_AMBIGUOUS_MAX = 0.10
GATE_FALSE_NONE_MAX = 0.05
GATE_G5_NONE_MIN = 0.80
NON_INFERIOR_MIN_PP = -2.0

# 表 L：迁移比的小分母规则与结论阈值。
TRANSFER_MIN_UNITY_DELTA_PP = 5.0
TRANSFER_M1_MIN_PP = 10.0
TRANSFER_M6_MIN_PP = -5.0

SUCCESS_GROUPS: tuple[str, ...] = ("G1", "G1t", "G2", "G2t", "G4")
SET_GROUPS: tuple[str, ...] = ("G3", "G3t")
NONE_GROUPS: tuple[str, ...] = ("G5",)
DIAGNOSTIC_GROUPS: tuple[str, ...] = ("G3p",)
# 表 L (1)：003 冻结 eval-row 的必含字段与组闭集。
TRANSFER_REQUIRED_FIELDS: tuple[str, ...] = (
    "row_id",
    "frame_path",
    "group",
    "gate_row",
    "surface",
    "gold_state",
    "gold_boxes_norm_xywh",
    "stratum",
)
TRANSFER_GROUPS: frozenset[str] = frozenset({"G1", "G3", "G3p", "G5"})


# --- 几何 -----------------------------------------------------------------


def xywh_to_xyxy(box: Sequence[float]) -> tuple[float, float, float, float]:
    return (box[0], box[1], box[0] + box[2], box[1] + box[3])


def iou(gold_norm_xywh: Sequence[float], predicted_1000: Sequence[int]) -> float:
    """gold 归一化 xywh 与预测的 1000 制整数框的 IoU（预测先 /1000）。"""
    ax1, ay1, ax2, ay2 = xywh_to_xyxy(gold_norm_xywh)
    bx1, by1, bx2, by2 = (value / 1000.0 for value in predicted_1000)
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    intersection = (ix2 - ix1) * (iy2 - iy1)
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - intersection
    return intersection / union if union > 0 else 0.0


def max_cardinality_matching(
    gold_boxes: Sequence[Sequence[float]], predicted_boxes: Sequence[Sequence[int]]
) -> int:
    """IoU ≥ 0.5 边上的最大基数一对一匹配（≤ 4 × ≤ 8，穷举）。"""
    if not gold_boxes or not predicted_boxes:
        return 0
    edges = [
        [iou(gold, predicted) >= IOU_THRESHOLD for predicted in predicted_boxes]
        for gold in gold_boxes
    ]
    best = 0
    indices = range(len(predicted_boxes))
    size = min(len(gold_boxes), len(predicted_boxes))
    for take in range(size, 0, -1):
        for gold_subset in itertools.combinations(range(len(gold_boxes)), take):
            for assignment in itertools.permutations(indices, take):
                if all(edges[g][p] for g, p in zip(gold_subset, assignment)):
                    return take
        if best:
            break
    return best


# --- 预测文件 -------------------------------------------------------------


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def check_completeness(
    manifest_rows: Sequence[Mapping[str, Any]], predictions: Sequence[Mapping[str, Any]]
) -> None:
    """行集合一一对应；缺行 / 重复 `row_id` / 多余行 → 整次 `PREDICTIONS_INCOMPLETE`。"""
    expected = [row["row_id"] for row in manifest_rows]
    actual = [row["row_id"] for row in predictions]
    duplicates = sorted({row for row, count in Counter(actual).items() if count > 1})
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if duplicates or missing or extra:
        raise receipts.PredictionsIncomplete(
            "预测文件与 manifest 不一一对应",
            offending=[{"duplicates": duplicates[:10], "missing": missing[:10], "extra": extra[:10]}],
        )


# --- 表 F 评分 ------------------------------------------------------------


@dataclass
class RowScore:
    row_id: str
    group: str
    gate_row: bool
    stratum: str
    class_word: str | None
    seen_target: bool | None
    status_pred: str | None
    parse_error: str | None
    success: bool | None
    reported: bool | None
    true_positive: int | None
    false_positive: int | None
    false_negative: int | None
    f1: float | None
    strict_success: bool | None
    gray_hit: bool | None


def _class_of(row: Mapping[str, Any]) -> str | None:
    noun = row.get("noun")
    if isinstance(noun, dict):
        return noun.get("class")
    program = row.get("relation_program")
    if isinstance(program, dict):
        return program.get("target", {}).get("class")
    return None


def score_rows(
    manifest_rows: Sequence[Mapping[str, Any]],
    predictions: Sequence[Mapping[str, Any]],
    *,
    gray_boxes: Mapping[str, Sequence[Sequence[float]]] | None = None,
) -> list[RowScore]:
    """逐行评分（表 F）。`gray_boxes` 是 G3′ 诊断用的 M 原框，按 `row_id` 给出。"""
    check_completeness(manifest_rows, predictions)
    by_row = {row["row_id"]: row for row in predictions}
    scores: list[RowScore] = []
    for row in manifest_rows:
        prediction = by_row[row["row_id"]]
        status = prediction.get("status_pred")
        boxes = prediction.get("boxes_1000") or []
        group = row["group"]
        gold_boxes = row.get("gold_boxes_norm_xywh") or []
        success = reported = strict = gray_hit = None
        tp = fp = fn = None
        f1 = None
        if group in SUCCESS_GROUPS:
            success = bool(
                status == "unique" and boxes and gold_boxes and iou(gold_boxes[0], boxes[0]) >= IOU_THRESHOLD
            )
        elif group in SET_GROUPS:
            reported = status == "ambiguous"
            if reported:
                tp = max_cardinality_matching(gold_boxes, boxes)
                fp = len(boxes) - tp
                fn = len(gold_boxes) - tp
                denominator = 2 * tp + fp + fn
                f1 = (2 * tp / denominator) if denominator else 0.0
            else:
                tp, fp, fn, f1 = 0, len(boxes), len(gold_boxes), 0.0
            strict = bool(reported and f1 == 1.0)
        elif group in NONE_GROUPS:
            success = status == "none"
        elif group in DIAGNOSTIC_GROUPS:
            reported = status == "ambiguous"
            if status == "unique" and boxes:
                candidates = (gray_boxes or {}).get(row["row_id"])
                if candidates is None:
                    raise receipts.InputHashChanged(
                        f"G3′ 诊断缺 M 原框：{row['row_id']}", offending=[row["row_id"]]
                    )
                gray_hit = any(iou(box, boxes[0]) >= IOU_THRESHOLD for box in candidates)
        scores.append(
            RowScore(
                row_id=row["row_id"],
                group=group,
                gate_row=bool(row.get("gate_row")),
                stratum=row.get("stratum", "NA"),
                class_word=_class_of(row),
                seen_target=row.get("seen_target"),
                status_pred=status,
                parse_error=prediction.get("parse_error"),
                success=success,
                reported=reported,
                true_positive=tp,
                false_positive=fp,
                false_negative=fn,
                f1=f1,
                strict_success=strict,
                gray_hit=gray_hit,
            )
        )
    return scores


def _rate(numerator: int, denominator: int) -> float | None:
    return (numerator / denominator) if denominator else None


def group_metrics(scores: Sequence[RowScore], group: str) -> dict[str, Any]:
    rows = [score for score in scores if score.group == group]
    total = len(rows)
    metrics: dict[str, Any] = {"rows": total}
    if not total:
        return metrics
    metrics["false_ambiguous_rate"] = _rate(sum(1 for s in rows if s.status_pred == "ambiguous"), total)
    metrics["false_none_rate"] = _rate(sum(1 for s in rows if s.status_pred == "none"), total)
    metrics["invalid_rate"] = _rate(sum(1 for s in rows if s.status_pred is None), total)
    if group in SUCCESS_GROUPS or group in NONE_GROUPS:
        metrics["success_rate"] = _rate(sum(1 for s in rows if s.success), total)
        if group in NONE_GROUPS:
            metrics["none_rate"] = metrics["success_rate"]
            metrics.pop("false_none_rate", None)
    if group in SET_GROUPS:
        metrics["report_rate"] = _rate(sum(1 for s in rows if s.reported), total)
        metrics["strict_success_rate"] = _rate(sum(1 for s in rows if s.strict_success), total)
        metrics["macro_f1"] = sum(s.f1 or 0.0 for s in rows) / total
        metrics["true_positive"] = sum(s.true_positive or 0 for s in rows)
        metrics["false_positive"] = sum(s.false_positive or 0 for s in rows)
        metrics["false_negative"] = sum(s.false_negative or 0 for s in rows)
    if group in DIAGNOSTIC_GROUPS:
        metrics["report_rate"] = _rate(sum(1 for s in rows if s.reported), total)
        unique_rows = [s for s in rows if s.status_pred == "unique"]
        metrics["unique_rows"] = len(unique_rows)
        metrics["any_member_hit_rate"] = _rate(
            sum(1 for s in unique_rows if s.gray_hit), len(unique_rows)
        )
    metrics["by_stratum"] = _slice(rows, lambda s: s.stratum)
    metrics["by_class"] = _slice(rows, lambda s: s.class_word)
    metrics["by_seen"] = _slice(rows, lambda s: str(s.seen_target))
    return metrics


def _slice(rows: Sequence[RowScore], key: Callable[[RowScore], Any]) -> dict[str, Any]:
    buckets: dict[Any, list[RowScore]] = defaultdict(list)
    for row in rows:
        buckets[key(row)].append(row)
    output: dict[str, Any] = {}
    for name, bucket in sorted(buckets.items(), key=lambda item: str(item[0])):
        entry: dict[str, Any] = {"rows": len(bucket)}
        if any(row.success is not None for row in bucket):
            entry["success_rate"] = _rate(sum(1 for row in bucket if row.success), len(bucket))
        if any(row.strict_success is not None for row in bucket):
            entry["strict_success_rate"] = _rate(
                sum(1 for row in bucket if row.strict_success), len(bucket)
            )
        output[str(name)] = entry
    return output


def combined_metrics(scores: Sequence[RowScore], groups: Sequence[str]) -> dict[str, Any]:
    """G1∪G2 之类的合并组：分母是各组 gate 行之和。"""
    rows = [score for score in scores if score.group in groups]
    total = len(rows)
    return {
        "rows": total,
        "success_rate": _rate(sum(1 for s in rows if s.success), total),
        "false_ambiguous_rate": _rate(sum(1 for s in rows if s.status_pred == "ambiguous"), total),
        "false_none_rate": _rate(sum(1 for s in rows if s.status_pred == "none"), total),
        "invalid_rate": _rate(sum(1 for s in rows if s.status_pred is None), total),
    }


def row_outcome(score: RowScore) -> float:
    """该行的配对结果值：集合组取严格成功，其余取 Success / none 率。

    C2-2：集合组（G3/G3t）的 `success` 恒为 None，直接拿它做配对差会让任何两次结果都算成
    0 pp。严格成功是表 F 给集合组定义的行级二值结果，配对差按它算才有意义。
    """
    if score.group in SET_GROUPS:
        return float(bool(score.strict_success))
    return float(bool(score.success))


def row_report_rate(score: RowScore) -> float:
    return float(bool(score.reported))


def row_f1(score: RowScore) -> float:
    return float(score.f1 or 0.0)


def paired_difference(
    scores_a: Sequence[RowScore],
    scores_b: Sequence[RowScore],
    groups: Sequence[str] = ("G1", "G2"),
    outcome: Callable[[RowScore], float] = row_outcome,
) -> dict[str, Any]:
    """同一行域的配对差（A − B），行级 bootstrap 百分位区间（描述性）。"""
    left = {s.row_id: s for s in scores_a if s.group in groups}
    right = {s.row_id: s for s in scores_b if s.group in groups}
    shared = sorted(set(left) & set(right))
    differences = [outcome(left[r]) - outcome(right[r]) for r in shared]
    if not differences:
        return {"rows": 0, "point_estimate_pp": None, "ci_pp": None}
    point = sum(differences) / len(differences)
    rng = random.Random(BOOTSTRAP_SEED)
    samples = []
    for _ in range(BOOTSTRAP_ROUNDS):
        draw = [differences[rng.randrange(len(differences))] for _ in differences]
        samples.append(sum(draw) / len(draw))
    samples.sort()

    def percentile(value: float) -> float:
        index = min(len(samples) - 1, max(0, int(round(value / 100.0 * (len(samples) - 1)))))
        return samples[index] * 100.0

    return {
        "rows": len(shared),
        "point_estimate_pp": point * 100.0,
        "ci_pp": [percentile(BOOTSTRAP_PERCENTILES[0]), percentile(BOOTSTRAP_PERCENTILES[1])],
        "bootstrap": {"rounds": BOOTSTRAP_ROUNDS, "seed": BOOTSTRAP_SEED},
    }


# --- 表 G 判定 ------------------------------------------------------------


def functional_gate(metrics: Mapping[str, Any]) -> dict[str, Any]:
    """表 G 功能门 (a)(b)(c)：全部成立才 `GATE_MET`。"""
    g3 = metrics.get("G3", {})
    combined = metrics.get("G1_G2", {})
    g5 = metrics.get("G5", {})
    checks = {
        "a_g3_report_rate": (g3.get("report_rate"), GATE_G3_REPORT_MIN, "min"),
        "a_g3_strict_success": (g3.get("strict_success_rate"), GATE_G3_STRICT_MIN, "min"),
        "b_false_ambiguous": (combined.get("false_ambiguous_rate"), GATE_FALSE_AMBIGUOUS_MAX, "max"),
        "b_false_none": (combined.get("false_none_rate"), GATE_FALSE_NONE_MAX, "max"),
        "c_g5_none_rate": (g5.get("none_rate"), GATE_G5_NONE_MIN, "min"),
    }
    detail: dict[str, Any] = {}
    passed = True
    for name, (value, threshold, direction) in checks.items():
        if value is None:
            ok = False
        else:
            ok = value >= threshold if direction == "min" else value <= threshold
        detail[name] = {"value": value, "threshold": threshold, "direction": direction, "pass": ok}
        passed = passed and ok
    return {"status": "GATE_MET" if passed else "GATE_NOT_MET", "checks": detail}


def non_inferiority(paired: Mapping[str, Any]) -> dict[str, Any]:
    """表 G (d)：点估计 ≥ −2.0 pp 即 `NON_INFERIOR`；CI 只披露。"""
    point = paired.get("point_estimate_pp")
    status = "INFERIOR" if point is None or point < NON_INFERIOR_MIN_PP else "NON_INFERIOR"
    return {"status": status, "point_estimate_pp": point, "ci_pp": paired.get("ci_pp"),
            "threshold_pp": NON_INFERIOR_MIN_PP}


def transfer_verdict(
    unity_deltas: Mapping[str, float | None], syndrone_deltas: Mapping[str, float | None] | None,
    *, not_run_reason: str | None = None
) -> dict[str, Any]:
    """表 L：机械判定，实现者不解释。

    `NOT_RUN(<原因>)` 优先；否则按 m1/m6 阈值给 `TRANSFER_OBSERVED` /
    `NOT_OBSERVED`。迁移比只在 |d_U(m)| ≥ 5.0 pp 时计算，否则
    `NA(UNITY_DELTA_SMALL)`；d_U(m) < 0 时只披露。
    """
    if not_run_reason or syndrone_deltas is None:
        return {"status": f"NOT_RUN({not_run_reason or 'SFT_003_NOT_DONE'})", "ratios": {}}
    ratios: dict[str, Any] = {}
    for name, unity in unity_deltas.items():
        syndrone = syndrone_deltas.get(name)
        if unity is None or syndrone is None or abs(unity) < TRANSFER_MIN_UNITY_DELTA_PP:
            ratios[name] = "NA(UNITY_DELTA_SMALL)"
        else:
            ratios[name] = {
                "ratio": syndrone / unity,
                "disclosure_only": unity < 0,
            }
    observed = (
        (unity_deltas.get("m1") or 0.0) >= TRANSFER_M1_MIN_PP
        and (syndrone_deltas.get("m1") or 0.0) >= TRANSFER_M1_MIN_PP
        and (syndrone_deltas.get("m6") if syndrone_deltas.get("m6") is not None else -999.0)
        >= TRANSFER_M6_MIN_PP
    )
    return {
        "status": "TRANSFER_OBSERVED" if observed else "NOT_OBSERVED",
        "ratios": ratios,
        "thresholds": {
            "m1_min_pp": TRANSFER_M1_MIN_PP,
            "m6_min_pp": TRANSFER_M6_MIN_PP,
            "ratio_min_unity_delta_pp": TRANSFER_MIN_UNITY_DELTA_PP,
        },
    }


def validate_transfer_rows(rows: Sequence[Mapping[str, Any]], blind_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """表 L (1)(2)：003 冻结 eval-row 与盲文件的 schema 校验；返回不满足项。"""
    problems: list[str] = []
    for row in rows:
        missing = [field for field in TRANSFER_REQUIRED_FIELDS if field not in row]
        if missing:
            problems.append(f"MISSING_FIELDS:{','.join(sorted(set(missing)))}")
            break
    groups = {row.get("group") for row in rows}
    if not groups <= TRANSFER_GROUPS:
        problems.append(f"GROUP_CLOSED_SET:{sorted(groups - TRANSFER_GROUPS)}")
    states = {row.get("gold_state") for row in rows}
    if not states <= {"unique", "ambiguous", "none", None}:
        problems.append("GOLD_STATE_CLOSED_SET")
    row_ids = [row["row_id"] for row in rows if "row_id" in row]
    blind_ids = [row.get("row_id") for row in blind_rows]
    if sorted(row_ids) != sorted(blind_ids):
        problems.append("BLIND_ROWS_NOT_ONE_TO_ONE")
    gold_fields = {"gold_state", "gold_boxes_norm_xywh", "gold_bbox_2d_1000", "gold_text_len"}
    if any(gold_fields & set(row) for row in blind_rows):
        problems.append("BLIND_ROWS_CARRY_GOLD")
    return problems


def map_v1_output(entry: Mapping[str, Any]) -> dict[str, Any]:
    """把旧探针（v1）的一条输出映射到三态，供表 F 的 v1 诊断附表配对。

    v1 的 prompt 只要求单框定位，没有三态协议，所以映射是**机械的**、也只作诊断：
    `invalid_output` → `null`（无效）；`reported_ambiguity` → `ambiguous`；
    解析出框 → `unique`；既没框也没报歧义 → `none`。v1 的 `success` 是它自己按 IoU ≥ 0.5
    对**当时的单目标 gold** 判的，原样带出，不与本次三态 gold 混算。
    """
    if entry.get("invalid_output"):
        status = None
    elif entry.get("reported_ambiguity"):
        status = "ambiguous"
    elif (entry.get("parsed") or {}).get("bbox_2d") is not None:
        status = "unique"
    else:
        status = "none"
    return {
        "status_v1": status,
        "success_v1": entry.get("success"),
        "iou_v1": entry.get("iou"),
        "invalid_v1": bool(entry.get("invalid_output")),
        "label_v1": (entry.get("parsed") or {}).get("label"),
    }


def v1_diagnostic_rows(
    manifest_rows: Sequence[Mapping[str, Any]],
    scores: Sequence[RowScore],
    legacy_predictions: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """表 F「v1 诊断附表」：405 条 legacy 行的 v1 输出映射三态后，与本次结果配对。

    每条 legacy 行出一行（重复键的两条各自成行），`row_id_v1` 是 v1 原 `row_id`，因此计数与
    守恒表一致。`legacy_predictions` 缺省为空时只带 v1 的组/gold 与本次结果（K4 夹具路径）；
    传入 `data/legacy/predictions.jsonl` 时逐行映射三态并给出与本次状态是否一致。只报告。
    """
    by_row = {score.row_id: score for score in scores}
    predictions = legacy_predictions or {}
    rows: list[dict[str, Any]] = []
    for row in manifest_rows:
        score = by_row.get(row["row_id"])
        for entry in row.get("legacy_probe") or []:
            v1 = predictions.get(entry["row_id"])
            mapped = map_v1_output(v1) if v1 is not None else {
                "status_v1": None, "success_v1": None, "iou_v1": None,
                "invalid_v1": None, "label_v1": None,
            }
            status_pred = None if score is None else score.status_pred
            rows.append(
                {
                    "row_id_v1": entry["row_id"],
                    "group_v1": entry["group_v1"],
                    "object_id_v1": entry["object_id_v1"],
                    "gold_v1_xywh": entry["gold_v1_xywh"],
                    "eval_row_id": row["row_id"],
                    "group": row["group"],
                    "gold_state": row.get("gold_state"),
                    "status_pred": status_pred,
                    "parse_error": None if score is None else score.parse_error,
                    "success": None if score is None else score.success,
                    "reported": None if score is None else score.reported,
                    "v1_prediction_present": v1 is not None,
                    **mapped,
                    "status_agrees_with_v1": (
                        None if (v1 is None or status_pred is None and mapped["status_v1"] is None)
                        else status_pred == mapped["status_v1"]
                    ),
                }
            )
    return rows


def summarise(
    manifest_rows: Sequence[Mapping[str, Any]],
    predictions: Sequence[Mapping[str, Any]],
    *,
    baseline: Sequence[Mapping[str, Any]] | None = None,
    gray_boxes: Mapping[str, Sequence[Sequence[float]]] | None = None,
    legacy_predictions: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """一次完整评分 + 表 G 判定（不含跨环境分支；那一支由调用方按表 L 提供）。"""
    scores = score_rows(manifest_rows, predictions, gray_boxes=gray_boxes)
    metrics = {group: group_metrics(scores, group) for group in
               SUCCESS_GROUPS + SET_GROUPS + NONE_GROUPS + DIAGNOSTIC_GROUPS}
    metrics["G1_G2"] = combined_metrics(scores, ("G1", "G2"))
    paired: dict[str, Any] = {"rows": 0, "point_estimate_pp": None, "ci_pp": None}
    per_group_paired: dict[str, Any] = {}
    if baseline is not None:
        baseline_scores = score_rows(manifest_rows, baseline, gray_boxes=gray_boxes)
        paired = paired_difference(scores, baseline_scores)
        # 表 G「目标车子组与增量」：逐组配对差（含 t 子组），描述性、不入功能门。
        # 集合组按严格成功配对，并另给报告率与 macro F1 的配对差，避免只报一个二值。
        for group in SUCCESS_GROUPS + SET_GROUPS + NONE_GROUPS:
            entry = paired_difference(scores, baseline_scores, groups=(group,))
            entry["outcome"] = "strict_success" if group in SET_GROUPS else "success"
            if group in SET_GROUPS:
                entry["report_rate_diff"] = paired_difference(
                    scores, baseline_scores, groups=(group,), outcome=row_report_rate
                )
                entry["macro_f1_diff"] = paired_difference(
                    scores, baseline_scores, groups=(group,), outcome=row_f1
                )
            per_group_paired[group] = entry
    return {
        "schema_version": f"{receipts.SCHEMA_PREFIX}/eval-summary/v1",
        "work_id": receipts.WORK_ID,
        "rows": len(manifest_rows),
        "metrics": metrics,
        "paired_difference_g1g2": paired,
        "paired_difference_by_group": per_group_paired,
        "v1_diagnostic_rows": v1_diagnostic_rows(manifest_rows, scores, legacy_predictions),
        "verdict": {
            "functional_gate": functional_gate(metrics),
            "vocabulary_non_inferiority": non_inferiority(paired),
        },
    }


def load_gray_boxes(
    manifest_rows: Sequence[Mapping[str, Any]],
    *,
    repo_root: Path,
    local_root: Path,
) -> dict[str, Sequence[Sequence[float]]] | None:
    """G3′ 行存在时按 `frame_id + definite_ids` 从已绑定 S3 取回 M 的原框（AC-3 修订 1）。

    取框与源绑定校验都在 `build_sft_data.load_definite_boxes` 里；本函数只负责让**评分
    入口**用上它——此前 `main` 不传 `gray_boxes`，合法的 unique 预测会被当成缺 M 框。
    该模块不进 K3 代码束，这条本地依赖不影响云端。
    """
    if not any(row.get("group") in DIAGNOSTIC_GROUPS for row in manifest_rows):
        return None
    from tools.eng_sft import build_sft_data  # noqa: PLC0415 - 单向依赖，避免顶层循环

    return build_sft_data.load_definite_boxes(
        manifest_rows, repo_root=repo_root, local_root=local_root
    )


def load_legacy_predictions(local_root: Path) -> dict[str, dict[str, Any]] | None:
    """读 `data/legacy/predictions.jsonl`（`build` 从探针复制的那份），按 v1 `row_id` 索引。"""
    path = Path(local_root) / "data" / "legacy" / "predictions.jsonl"
    if not path.is_file():
        return None
    return {row["row_id"]: row for row in load_jsonl(path)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-SFT-002 评分与判定（本地）")
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--local-root", default=None)
    parser.add_argument("--manifest", help="eval.jsonl（含 gold）")
    parser.add_argument("--predictions", help="回传预测 jsonl")
    parser.add_argument("--baseline", help="零样本对照预测 jsonl（配对差用）")
    parser.add_argument("--out", help="写出摘要 JSON")
    parser.add_argument("--validate", help="校验 003 冻结 eval-row（表 L (1)(2)）")
    parser.add_argument("--validate-blind", help="与 --validate 配套的盲文件")
    parser.add_argument("--verdict", help="只打印已有摘要 JSON 的表 G 判定")
    args = parser.parse_args(argv)

    if args.verdict:
        document = json.loads(Path(args.verdict).read_text(encoding="utf-8"))
        print(json.dumps(document.get("verdict", {}), ensure_ascii=False, indent=2))
        return 0
    if args.validate:
        rows = load_jsonl(Path(args.validate))
        blind = load_jsonl(Path(args.validate_blind)) if args.validate_blind else []
        problems = validate_transfer_rows(rows, blind)
        if problems:
            print("NOT_RUN(INCOMPATIBLE_EVAL_SCHEMA:" + ";".join(problems) + ")")
            return 1
        print(f"schema ok：{len(rows)} 行")
        return 0
    if not args.manifest or not args.predictions:
        parser.error("需要 --manifest 与 --predictions")
    root = Path(args.repo_root)
    local = Path(args.local_root) if args.local_root else root / receipts.LOCAL_ROOT
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    started = time.monotonic()
    try:
        manifest_rows = load_jsonl(Path(args.manifest))
        predictions = load_jsonl(Path(args.predictions))
        baseline = load_jsonl(Path(args.baseline)) if args.baseline else None
        # C1-3：G3′ 的诊断取框必须走绑定源；评分入口自己接通，不靠调用方手工传。
        gray_boxes = load_gray_boxes(manifest_rows, repo_root=root, local_root=local)
        legacy_predictions = load_legacy_predictions(local)  # C2-3：v1 附表真去消费旧探针输出
        summary = summarise(
            manifest_rows,
            predictions,
            baseline=baseline,
            gray_boxes=gray_boxes,
            legacy_predictions=legacy_predictions,
        )
        outputs: list[dict[str, Any]] = []
        if args.out:
            out_path = receipts.assert_output_allowed(Path(args.out), root)  # C1-5：入口自己守边界
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            outputs.append(receipts.output_record(out_path))
        writer.write_run_receipt(
            "return",
            started=started,
            outputs=outputs,
            extra={
                "stage_detail": "score",
                "rows": len(manifest_rows),
                "gray_rows": 0 if gray_boxes is None else len(gray_boxes),
                "verdict": summary["verdict"]["functional_gate"]["status"],
            },
        )
    except receipts.EngSftError as exc:
        writer.write_failure_receipt("return", exc.reason, exc.offending, message=str(exc))
        print(f"评分失败（{exc.reason}）：{exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary["verdict"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
