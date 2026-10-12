"""P3 VLM 四臂（合同 §3.5；AC-6）：臂 A 候选匹配换算、臂 B/C 图与 prompt、分页合并、评分与配对诊断。

候选集（B/C/D 共用）见 `inputs.candidate_set`（IR-1）。索引类臂的成功判据是**对象身份相等**
（选中候选的 `object_id` = gold `target_object_ids`），不做 IoU。臂 A 复用 SFT-002 既有整帧预测
（零新查询），整帧预测框与候选框 max IoU ≥ 0.5 者视为选中该候选。

prompt：沿用 prompt v2 的首段、词表段与 G4 段逐字（`tools/eng_sft/prompt_v2.py`，只导入），只把
坐标段/回复段换成索引版。解析器是 `vlm_remote.parse_index_reply`（5060 与 Mac 同一份）。
"""

from __future__ import annotations

from collections import Counter, defaultdict
import math
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from tools.eng_fast import common
from tools.eng_fast.vlm_remote import INVALID, parse_index_reply

ARMS_INDEXED = ("B", "C")
PAGE_SIZE = 16
GRID_COLS = 4
GRID_ROWS = 4
CELL_IMAGE_PX = 224
LABEL_BAND_PX = 32
CROP_EXPAND = 1.5
ARM_A_IOU = 0.5
SMOKE_ROWS = 32

SUCCESS_GROUPS = ("G1", "G1t", "G2", "G2t", "G4")
SET_GROUPS = ("G3", "G3t")
NONE_GROUPS = ("G5",)
DIAGNOSTIC_GROUPS = ("G3p",)
EXCLUDED_GROUPS = ("LEGACY_ONLY",)
FALSE_RATE_GROUPS = ("G1", "G2")

CANDIDATE_SEGMENT = {
    "B": (
        "Candidates: the image is a grid of numbered crops; each crop shows one candidate object cut out "
        "(with some surrounding context) from the same aerial image. The label above each crop gives the "
        "candidate number and the object's center in the original aerial image as x=...,y=... (0 to 1 "
        "relative to the image width and height, origin at the top-left corner, x increasing to the right "
        "and y increasing downward)."
    ),
    "C": (
        "Candidates: every candidate object in the image is outlined with a thin box, and the number next "
        "to each box is that candidate's number."
    ),
}
REPLY_INDEX_SEGMENT = (
    "Reply with exactly one JSON object and nothing else:\n"
    '- exactly one candidate matches: {"status": "unique", "index": n}\n'
    '- two or more candidates match: {"status": "ambiguous", "indices": [n, ...]} listing every matching '
    "candidate\n"
    '- no candidate matches: {"status": "none"}'
)


def build_prompt_text(arm: str, surface: str, g4: bool, vocab: str = "unity-v2") -> str:
    from tools.eng_sft import prompt_v2  # noqa: PLC0415

    segments = [prompt_v2.HEAD_SEGMENT.replace("{surface}", surface), prompt_v2.vocab_segment(vocab)]
    if g4:
        segments.append(prompt_v2.G4_SEGMENT)
    segments.extend([CANDIDATE_SEGMENT[arm], REPLY_INDEX_SEGMENT])
    return "\n".join(segments)


def pages(candidates: Sequence[Mapping[str, Any]]) -> list[list[Mapping[str, Any]]]:
    return [list(candidates[i : i + PAGE_SIZE]) for i in range(0, len(candidates), PAGE_SIZE)]


# --- 渲染（Mac，.venv-yoloe 的 cv2）----------------------------------------


def _crop_expanded(image: Any, box: Sequence[float]) -> Any:
    height, width = image.shape[:2]
    cx, cy = (box[0] + box[2] / 2) * width, (box[1] + box[3] / 2) * height
    half_w, half_h = box[2] * width * CROP_EXPAND / 2, box[3] * height * CROP_EXPAND / 2
    left, right = max(0, int(math.floor(cx - half_w))), min(width, int(math.ceil(cx + half_w)))
    top, bottom = max(0, int(math.floor(cy - half_h))), min(height, int(math.ceil(cy + half_h)))
    if right - left < 1 or bottom - top < 1:
        left, right = max(0, int(cx) - 1), min(width, int(cx) + 1)
        top, bottom = max(0, int(cy) - 1), min(height, int(cy) + 1)
    return image[top:bottom, left:right]


def render_grid(image: Any, page: Sequence[Mapping[str, Any]]) -> Any:
    """臂 B：≤16 个候选裁图（外扩 1.5 倍、等比缩放到长边 224 px），拼 4×4 网格；每格上方标号与中心坐标。"""
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    cell_h = CELL_IMAGE_PX + LABEL_BAND_PX
    canvas = np.full((GRID_ROWS * cell_h, GRID_COLS * CELL_IMAGE_PX, 3), 128, dtype=np.uint8)
    for slot, candidate in enumerate(page):
        row, col = divmod(slot, GRID_COLS)
        x0, y0 = col * CELL_IMAGE_PX, row * cell_h
        crop = _crop_expanded(image, candidate["box"])
        ch, cw = crop.shape[:2]
        scale = CELL_IMAGE_PX / max(ch, cw)
        new_w, new_h = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))
        resized = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        oy = y0 + LABEL_BAND_PX + (CELL_IMAGE_PX - new_h) // 2
        ox = x0 + (CELL_IMAGE_PX - new_w) // 2
        canvas[oy : oy + new_h, ox : ox + new_w] = resized
        canvas[y0 : y0 + LABEL_BAND_PX, x0 : x0 + CELL_IMAGE_PX] = 0
        cx = candidate["box"][0] + candidate["box"][2] / 2
        cy = candidate["box"][1] + candidate["box"][3] / 2
        label = f"{candidate['index']}  x={cx:.2f},y={cy:.2f}"
        cv2.putText(canvas, label, (x0 + 6, y0 + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.rectangle(canvas, (x0, y0), (x0 + CELL_IMAGE_PX - 1, y0 + cell_h - 1), (0, 0, 0), 1)
    return canvas


def render_marks(image: Any, candidates: Sequence[Mapping[str, Any]]) -> Any:
    """臂 C：原帧叠加全部 K 个候选框（线宽 1 px、白色）与编号（黑底白字，置于框外，不遮框内）。"""
    import cv2  # noqa: PLC0415

    canvas = image.copy()
    height, width = canvas.shape[:2]
    scale = 0.45 if len(candidates) <= 8 else 0.38
    for candidate in candidates:
        x, y, w, h = candidate["box"]
        x1, y1 = int(round(x * width)), int(round(y * height))
        x2, y2 = int(round((x + w) * width)) - 1, int(round((y + h) * height)) - 1
        cv2.rectangle(canvas, (x1, y1), (max(x1, x2), max(y1, y2)), (255, 255, 255), 1)
    for candidate in candidates:
        x, y, w, h = candidate["box"]
        x1, y1 = int(round(x * width)), int(round(y * height))
        y2 = int(round((y + h) * height)) - 1
        text = str(candidate["index"])
        (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
        box_h = th + base + 2
        top = y1 - box_h - 1 if y1 - box_h - 1 >= 0 else min(height - box_h, y2 + 2)
        left = min(max(0, x1), width - tw - 3)
        cv2.rectangle(canvas, (left, top), (left + tw + 2, top + box_h), (0, 0, 0), -1)
        cv2.putText(canvas, text, (left + 1, top + th + 1), cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1, cv2.LINE_AA)
    return canvas


# --- 分页合并（§3.5.3 闭集，按序判定、命中即止）------------------------------


def merge_pages(k: int, page_results: Sequence[Mapping[str, Any] | None]) -> dict[str, Any]:
    """`page_results[i]` = 该页最终解析（重试后）或 None（`NOT_RUN`）。返回行结果。"""
    if k == 0:
        return {"status": "none", "indices": [], "flag": "K0"}
    if any(result is None for result in page_results):
        return {"status": "NOT_RUN", "indices": [], "flag": "NOT_RUN"}
    if any(result["status"] == INVALID for result in page_results):
        return {"status": INVALID, "indices": [], "flag": "INVALID"}
    uniques = [result["indices"][0] for result in page_results if result["status"] == "unique"]
    if any(result["status"] == "ambiguous" for result in page_results):
        chosen = set(uniques)
        for result in page_results:
            if result["status"] == "ambiguous":
                chosen |= set(result["indices"])
        return {"status": "ambiguous", "indices": sorted(chosen), "flag": None}
    if len(uniques) >= 2:
        return {"status": "ambiguous", "indices": sorted(uniques), "flag": None}
    if len(uniques) == 1:
        return {"status": "unique", "indices": uniques, "flag": None}
    return {"status": "none", "indices": [], "flag": None}


def final_page_result(first: Mapping[str, Any] | None, retry: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    """每页最终解析：首次非 INVALID 即用首次；首次 INVALID 且有重试 → 用重试结果。"""
    if first is None:
        return None
    if first["parse"]["status"] != INVALID or retry is None:
        return first["parse"]
    return retry["parse"]


# --- 臂 A：整帧预测 → 候选 ------------------------------------------------


def arm_a_selection(prediction: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    status = prediction.get("status_pred")
    if status is None:
        return {"status": INVALID, "object_ids": [], "flag": "PARSE_ERROR"}
    if status == "none":
        return {"status": "none", "object_ids": [], "flag": None}
    chosen: list[str] = []
    unmatched = 0
    for box_1000 in prediction.get("boxes_1000") or []:
        box = (box_1000[0] / 1000, box_1000[1] / 1000, (box_1000[2] - box_1000[0]) / 1000, (box_1000[3] - box_1000[1]) / 1000)
        best = max(
            ((common.iou_xywh(box, c["box"]), c["object_id"]) for c in candidates), default=(0.0, None)
        )
        if best[1] is None or best[0] < ARM_A_IOU:
            unmatched += 1
            continue
        if best[1] not in chosen:
            chosen.append(best[1])
    flag = "NO_CANDIDATE_MATCH" if unmatched else None
    return {"status": status, "object_ids": chosen, "flag": flag, "unmatched_boxes": unmatched}


# --- 评分（§3.5.1）----------------------------------------------------------


def row_outcome(row: Mapping[str, Any], selection: Mapping[str, Any]) -> dict[str, Any]:
    """一行一臂：`selection` = {status, object_ids, flag}；返回各报表量的逐行布尔。"""
    status = selection["status"]
    chosen = set(selection.get("object_ids") or [])
    gold = set(row.get("target_object_ids") or [])
    group = row["group"]
    fully_matched = selection.get("flag") != "NO_CANDIDATE_MATCH"
    outcome: dict[str, Any] = {"status": status, "flag": selection.get("flag")}
    if group in SUCCESS_GROUPS:
        outcome["success"] = status == "unique" and fully_matched and chosen == gold and len(gold) == 1
    elif group in SET_GROUPS:
        outcome["report"] = status == "ambiguous"
        outcome["strict"] = status == "ambiguous" and fully_matched and chosen == gold
    elif group in NONE_GROUPS:
        outcome["none"] = status == "none"
    elif group in DIAGNOSTIC_GROUPS:
        outcome["report"] = status == "ambiguous"
        outcome["any_member"] = bool(chosen & set(row.get("definite_ids") or []))
    if group in FALSE_RATE_GROUPS:
        outcome["false_none"] = status == "none"
        outcome["false_ambiguous"] = status == "ambiguous"
    return outcome


def _rate(values: Sequence[bool]) -> dict[str, Any]:
    n = len(values)
    k = sum(1 for v in values if v)
    return {"k": k, "n": n, "rate": round(k / n, 6) if n else None, "ci95": common.bootstrap_ci(values)}


def score_arm(rows: Sequence[Mapping[str, Any]], outcomes: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """按 §3.5.1 分组/分母/层汇总一臂（`outcomes[row_id]` 缺失 = 该行未出结果，按失败计入并单列）。"""
    report: dict[str, Any] = {"groups": {}, "counts": Counter()}
    by_group: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_group[row["group"]].append(row)
    for group, members in sorted(by_group.items()):
        if group in EXCLUDED_GROUPS:
            report["groups"][group] = {"rows": len(members), "excluded": True}
            continue
        entry: dict[str, Any] = {"rows": len(members)}
        metrics = (
            ["success"] if group in SUCCESS_GROUPS else ["report", "strict"] if group in SET_GROUPS
            else ["none"] if group in NONE_GROUPS else ["report", "any_member"]
        )
        for metric in metrics:
            values = [bool(outcomes.get(r["row_id"], {}).get(metric, False)) for r in members]
            entry[metric] = _rate(values)
            if group not in NONE_GROUPS:
                entry[f"{metric}_by_stratum"] = {
                    stratum: _rate(
                        [bool(outcomes.get(r["row_id"], {}).get(metric, False)) for r in members if r["stratum"] == stratum]
                    )
                    for stratum in common.STRATA
                    if any(r["stratum"] == stratum for r in members)
                }
        entry["status_counts"] = dict(Counter(outcomes.get(r["row_id"], {}).get("status", "MISSING") for r in members))
        entry["flag_counts"] = dict(
            Counter(outcomes.get(r["row_id"], {}).get("flag") for r in members if outcomes.get(r["row_id"], {}).get("flag"))
        )
        report["groups"][group] = entry
    false_rows = [r for r in rows if r["group"] in FALSE_RATE_GROUPS]
    report["g1_g2_false_rates"] = {
        "rows": len(false_rows),
        "false_none": _rate([bool(outcomes.get(r["row_id"], {}).get("false_none")) for r in false_rows]),
        "false_ambiguous": _rate([bool(outcomes.get(r["row_id"], {}).get("false_ambiguous")) for r in false_rows]),
    }
    for row in rows:
        outcome = outcomes.get(row["row_id"])
        report["counts"]["missing" if outcome is None else (outcome.get("flag") or "no_flag")] += 1
    report["counts"] = dict(report["counts"])
    return report


def paired_diagnostic(
    rows: Sequence[Mapping[str, Any]],
    outcomes: Mapping[str, Mapping[str, Any]],
    det_hit: Mapping[str, bool],
) -> dict[str, Any]:
    """§3.5.4：成功组逐行 2×2 {det_hit × arm_ok}（同行两种独立测量的交集，不是链路成功率或上界）。"""
    result: dict[str, Any] = {}
    buckets: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["group"] in SUCCESS_GROUPS:
            buckets["ALL_SUCCESS_GROUPS"].append(row)
            buckets[f"stratum:{row['stratum']}"].append(row)
    for name, members in sorted(buckets.items()):
        table = Counter()
        for row in members:
            hit = bool(det_hit[row["row_id"]])
            ok = bool(outcomes.get(row["row_id"], {}).get("success"))
            table[f"det_{'hit' if hit else 'miss'}__arm_{'ok' if ok else 'fail'}"] += 1
        n = len(members)
        both = table["det_hit__arm_ok"]
        hits = both + table["det_hit__arm_fail"]
        result[name] = {
            "n": n,
            "table": {
                key: int(table[key])
                for key in ("det_hit__arm_ok", "det_hit__arm_fail", "det_miss__arm_ok", "det_miss__arm_fail")
            },
            "P_arm_ok_and_det_hit": round(both / n, 6) if n else None,
            "P_arm_ok_given_det_hit": round(both / hits, 6) if hits else None,
        }
    return result
