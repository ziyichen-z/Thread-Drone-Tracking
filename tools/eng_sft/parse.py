#!/usr/bin/env python3
"""表 B 解析器（fail-closed；纯标准库）。

冻结闭集成员，也是 K3 代码束成员：云端只用它把生成文本转成预测行，评分一律在
本地。判据链：去 fence 并计数 → JSON → `status` 闭集 → 框长度 4 / 整数 /
0–1000 / `x1 < x2 ∧ y1 < y2` → `candidates` 2…8。

**任一 `parse_error ≠ null` 即 `status_pred = null`**：模型原样给出的状态只存
`raw_status` 供诊断，绝不因为「状态词看着对」就放行一条框不合法的预测。
"""

from __future__ import annotations

import json
import re
from typing import Any

# 表 B `parse_error` 闭集。
JSON_ERROR = "JSON_ERROR"
SCHEMA_ERROR = "SCHEMA_ERROR"
RANGE_ERROR = "RANGE_ERROR"
ORDER_ERROR = "ORDER_ERROR"
TRUNCATED = "TRUNCATED"
PARSE_ERRORS: tuple[str, ...] = (JSON_ERROR, SCHEMA_ERROR, RANGE_ERROR, ORDER_ERROR, TRUNCATED)

STATUS_VALUES: tuple[str, ...] = ("unique", "ambiguous", "none")
COORD_MIN, COORD_MAX = 0, 1000
CANDIDATES_MIN, CANDIDATES_MAX = 2, 8

_FENCE_RE = re.compile(r"```[a-zA-Z0-9_+-]*\n?")
# 截断的判据之一：生成在达到 token 上限处停下（greedy 解码的 `length`）。
TRUNCATING_FINISH_REASONS: frozenset[str] = frozenset({"length", "max_new_tokens", "TRUNCATED"})


def strip_fences(raw: str) -> tuple[str, int]:
    """去掉 markdown fence 并返回 fence 标记数（`fence_stripped` 记录该计数）。"""
    fences = len(_FENCE_RE.findall(raw))
    cleaned = _FENCE_RE.sub("", raw)
    cleaned = cleaned.replace("```", "")
    return cleaned.strip(), fences


def _bbox_problem(box: Any) -> str | None:
    if not isinstance(box, list) or len(box) != 4:
        return SCHEMA_ERROR
    for value in box:
        if isinstance(value, bool) or not isinstance(value, int):
            return SCHEMA_ERROR
    if any(value < COORD_MIN or value > COORD_MAX for value in box):
        return RANGE_ERROR
    if box[0] >= box[2] or box[1] >= box[3]:
        return ORDER_ERROR
    return None


def parse_prediction(
    raw_output: str, *, finish_reason: str | None = None
) -> dict[str, Any]:
    """解析一条生成文本，返回表 C `prediction` 的解析字段子集。"""
    stripped, fences = strip_fences(raw_output or "")
    result: dict[str, Any] = {
        "raw_output": raw_output,
        "fence_stripped": fences,
        "raw_status": None,
        "parsed": None,
        "parse_error": None,
        "status_pred": None,
        "boxes_1000": [],
    }

    if finish_reason is not None and finish_reason in TRUNCATING_FINISH_REASONS:
        result["parse_error"] = TRUNCATED
        return result

    try:
        document = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        result["parse_error"] = JSON_ERROR
        return result

    if not isinstance(document, dict):
        result["parse_error"] = SCHEMA_ERROR
        return result

    status = document.get("status")
    if isinstance(status, str):
        result["raw_status"] = status

    if status not in STATUS_VALUES:
        result["parse_error"] = SCHEMA_ERROR
        return result

    if status == "none":
        if set(document) != {"status"}:
            result["parse_error"] = SCHEMA_ERROR
            return result
        result["parsed"] = {"status": "none"}
        result["status_pred"] = "none"
        return result

    if status == "unique":
        if set(document) != {"status", "bbox_2d"}:
            result["parse_error"] = SCHEMA_ERROR
            return result
        problem = _bbox_problem(document["bbox_2d"])
        if problem:
            result["parse_error"] = problem
            return result
        result["parsed"] = {"status": "unique", "bbox_2d": list(document["bbox_2d"])}
        result["status_pred"] = "unique"
        result["boxes_1000"] = [list(document["bbox_2d"])]
        return result

    # status == "ambiguous"
    if set(document) != {"status", "candidates"}:
        result["parse_error"] = SCHEMA_ERROR
        return result
    candidates = document["candidates"]
    if not isinstance(candidates, list) or not CANDIDATES_MIN <= len(candidates) <= CANDIDATES_MAX:
        result["parse_error"] = SCHEMA_ERROR
        return result
    boxes: list[list[int]] = []
    for item in candidates:
        if not isinstance(item, dict) or set(item) != {"bbox_2d"}:
            result["parse_error"] = SCHEMA_ERROR
            return result
        problem = _bbox_problem(item["bbox_2d"])
        if problem:
            result["parse_error"] = problem
            return result
        boxes.append(list(item["bbox_2d"]))
    result["parsed"] = {"status": "ambiguous", "candidates": [{"bbox_2d": b} for b in boxes]}
    result["status_pred"] = "ambiguous"
    result["boxes_1000"] = boxes
    return result
