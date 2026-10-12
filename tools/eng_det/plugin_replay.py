"""口径 B 插件身份回放（合同 §3.4.1、AR2-2；AC-4 描述性读数，不设门）。

用**插件本体** `DetAssocTracker`：子序列首个可见帧用真值框（用户框的离线替身）调用 `init` 一次，之后逐帧
`update`，不改绑。真值只进入评分：可见帧上 `ok ∧ IoU(插件框, 真值) ≥ 0.5` → `HIT`；`ok` 但 IoU < 0.5 →
`DRIFT`；lost 且真值可见 → `MISS`；真值不可见 → 不计（`NOT_SCORED`）。另记首次 `bound_track_removed`
距初始化的仿真秒数。逐帧 `(state, box, reason)` 原样保存，供口径 C 载体自测（§3.6、AC-6）逐帧比对。
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from tools.eng_det import common

HIT = "HIT"
DRIFT = "DRIFT"
MISS = "MISS"
NOT_SCORED = "NOT_SCORED"
HIT_IOU = 0.5


def score_frame(ok: bool, box: Sequence[float] | None, truth: Sequence[float] | None) -> str:
    """纯函数：单帧口径 B 判定。"""
    if truth is None:
        return NOT_SCORED
    if not ok or box is None:
        return MISS
    return HIT if common.iou_xywh(box, truth) >= HIT_IOU else DRIFT


def run_piece(plugin: Any, piece: Sequence[Mapping[str, Any]], truths: Sequence[Sequence[float] | None], load_image: Any) -> dict[str, Any]:
    """一条子序列：首个可见帧 `init`（真值框作用户框替身），其后逐帧 `update`。"""
    start = next((i for i, t in enumerate(truths) if t is not None), None)
    if start is None:
        return {"first_frame": piece[0]["frame_id"], "init": "NO_VISIBLE_FRAME", "counts": {}}
    init_box = [float(v) for v in truths[start]]
    init_ok = bool(plugin.init(load_image(piece[start]["frame_id"]), init_box))
    library_frame_id_after_init = getattr(plugin, "library_frame_id", None)
    record: dict[str, Any] = {
        "first_frame": piece[0]["frame_id"],
        "init_frame": piece[start]["frame_id"],
        "init_index": start,
        "init_box": init_box,
        "init": "OK" if init_ok else "INIT_REJECTED",
        "library_frame_id_after_init": library_frame_id_after_init,
        "bound_track_id": getattr(plugin, "bound_track_id", None),
    }
    if not init_ok:
        record["counts"] = {}
        record["visible_after_init"] = sum(1 for t in truths[start + 1 :] if t is not None)
        return record
    counts: Counter = Counter()
    per_frame = []
    first_removed_s = None
    t0 = float(piece[start]["sim_t"])
    for index in range(start + 1, len(piece)):
        result = plugin.update(load_image(piece[index]["frame_id"]))
        box = list(result.box_norm) if result.box_norm is not None else None
        verdict = score_frame(bool(result.ok), box, truths[index])
        counts[verdict] += 1
        if result.reason == "bound_track_removed" and first_removed_s is None:
            first_removed_s = round(float(piece[index]["sim_t"]) - t0, 3)
        per_frame.append(
            {
                "frame_id": piece[index]["frame_id"],
                "state": "TRACKING" if result.ok else "LOST",
                "box": box,
                "reason": result.reason,
                "confidence": result.confidence,
                "confidence_source": result.confidence_source,
                "score": verdict,
            }
        )
    visible = counts[HIT] + counts[DRIFT] + counts[MISS]
    record.update(
        {
            "counts": dict(counts),
            "visible_after_init": visible,
            "hit_ratio": round(counts[HIT] / visible, 6) if visible else None,
            "first_bound_track_removed_s": first_removed_s,
            "library_frame_id_end": getattr(plugin, "library_frame_id", None),
            "per_frame": per_frame,
        }
    )
    return record


def pool(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts: Counter = Counter()
    for r in records:
        counts.update(r.get("counts", {}))
    visible = counts[HIT] + counts[DRIFT] + counts[MISS]
    removed = [r["first_bound_track_removed_s"] for r in records if r.get("first_bound_track_removed_s") is not None]
    return {
        "pieces": len(records),
        "init_ok": sum(1 for r in records if r.get("init") == "OK"),
        "init_rejected": sum(1 for r in records if r.get("init") == "INIT_REJECTED"),
        "no_visible_frame": sum(1 for r in records if r.get("init") == "NO_VISIBLE_FRAME"),
        "counts": dict(counts),
        "visible_after_init": visible,
        "hit_ratio": round(counts[HIT] / visible, 6) if visible else None,
        "drift": counts[DRIFT],
        "pieces_with_bound_track_removed": len(removed),
        "first_bound_track_removed_s": common.quantiles(removed) if removed else None,
        "tag": "口径 B（插件身份，描述性，不设门）",
    }
