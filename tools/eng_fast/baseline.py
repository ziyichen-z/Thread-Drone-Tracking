"""臂 D 无 VLM 基线（合同 §3.5.2 第 4 行）。

- 类别：候选裁图的 DINOv2 嵌入对 train∪dev 族裁图库做 kNN（k=5，余弦）多数票；
- 颜色：HSV 色相直方图对六色原型（原型取自 S5 `VERIFIED` 颜色对象的 train∪dev 裁图）最近邻；
- G4：按候选框 x 中心序执行关系（与上游 `tier1_lang.execute` 同一最小分隔 40 px）；
- 满足指令的候选数 0/1/≥2 → none/unique/ambiguous。

裁图库与原型的采样口径见实现读法 IR-6/IR-7（确定性哈希序，不按结果调整）。
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import math
from typing import Any, Callable, Iterable, Mapping, Sequence

from tools.eng_fast import common

K_NEIGHBOURS = 5
BANK_PER_OBJECT = 20
BANK_MIN_SHORT_SIDE_PX = 16.0
PROTO_PER_OBJECT = 10
HUE_BINS = 18
SATURATION_MIN = 64  # OpenCV S ∈ [0,255]；≈ 0.25
VALUE_MIN = 51  # OpenCV V ∈ [0,255]；≈ 0.20
SEED = "P1-ENG-FAST-001/armD/20260923"
VIEWER_SIDE_MIN_SEPARATION_PX = 40.0  # = tools/dist_data/contract.VIEWER_SIDE_MIN_SEPARATION_PX（测试逐值核对）


def _key(*parts: str) -> str:
    return hashlib.sha256("|".join((SEED, *parts)).encode("utf-8")).hexdigest()


def bank_samples(
    pool: Iterable[Mapping[str, Any]], per_object: int = BANK_PER_OBJECT
) -> list[dict[str, Any]]:
    """IR-6：train∪dev 帧中已验证类别的 `OK` 目录车与帧级已绑定目标车（类别 car），短边 ≥16 px；
    每个 object_id 按确定性哈希序取前 20 张。"""
    by_object: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for frame in pool:
        for vehicle in frame["vehicles"]:
            if vehicle.get("class_word") and common.short_side_px(vehicle["box"]) >= BANK_MIN_SHORT_SIDE_PX:
                by_object[vehicle["object_id"]].append(
                    {"frame_id": frame["frame_id"], "object_id": vehicle["object_id"], "class_word": vehicle["class_word"], "box": vehicle["box"]}
                )
        dynamic = frame.get("dynamic")
        if dynamic and dynamic.get("definite") and dynamic.get("box"):
            if common.short_side_px(dynamic["box"]) >= BANK_MIN_SHORT_SIDE_PX:
                by_object["dynamic-target"].append(
                    {"frame_id": frame["frame_id"], "object_id": "dynamic-target", "class_word": "car", "box": dynamic["box"]}
                )
    samples = []
    for object_id, items in sorted(by_object.items()):
        items.sort(key=lambda item: _key("bank", item["frame_id"], object_id))
        samples.extend(items[:per_object])
    return samples


def prototype_samples(
    pool: Iterable[Mapping[str, Any]],
    verified_colors: Mapping[str, str],
    per_object: int = PROTO_PER_OBJECT,
) -> list[dict[str, Any]]:
    """IR-7：S5 `VERIFIED` 颜色对象（颜色 ∈ 六色词表）在 train∪dev 帧中的 `OK` 裁图（短边 ≥16 px）；
    帧目录索引只含车辆，故原型取 VERIFIED 颜色车辆；每对象按哈希序取前 10 张。"""
    by_object: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for frame in pool:
        for vehicle in frame["vehicles"]:
            color = verified_colors.get(vehicle["object_id"])
            if color and common.short_side_px(vehicle["box"]) >= BANK_MIN_SHORT_SIDE_PX:
                by_object[vehicle["object_id"]].append(
                    {"frame_id": frame["frame_id"], "object_id": vehicle["object_id"], "color_word": color, "box": vehicle["box"]}
                )
    samples = []
    for object_id, items in sorted(by_object.items()):
        items.sort(key=lambda item: _key("proto", item["frame_id"], object_id))
        samples.extend(items[:per_object])
    return samples


def hue_histogram(bgr_crop: Any) -> list[float]:
    """18 个色相桶（S ≥ 64 且 V ≥ 51 的像素）+ 1 个无彩色桶，L1 归一化（IR-7：灰色需要无彩色桶才可表示）。"""
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    hsv = cv2.cvtColor(bgr_crop, cv2.COLOR_BGR2HSV).reshape(-1, 3)
    chromatic = (hsv[:, 1] >= SATURATION_MIN) & (hsv[:, 2] >= VALUE_MIN)
    hues = hsv[chromatic, 0].astype(np.int64) * HUE_BINS // 180
    counts = np.bincount(np.clip(hues, 0, HUE_BINS - 1), minlength=HUE_BINS).astype(np.float64)
    achromatic = float((~chromatic).sum())
    vector = np.concatenate([counts, [achromatic]])
    total = vector.sum()
    return (vector / total).tolist() if total > 0 else [0.0] * (HUE_BINS + 1)


def build_prototypes(histograms: Sequence[tuple[str, Sequence[float]]]) -> dict[str, list[float]]:
    grouped: dict[str, list[Sequence[float]]] = defaultdict(list)
    for color, histogram in histograms:
        grouped[color].append(histogram)
    return {
        color: [sum(h[i] for h in items) / len(items) for i in range(len(items[0]))]
        for color, items in sorted(grouped.items())
    }


def nearest_color(histogram: Sequence[float], prototypes: Mapping[str, Sequence[float]]) -> str:
    return min(
        prototypes, key=lambda color: (sum(abs(a - b) for a, b in zip(histogram, prototypes[color])), color)
    )


def knn_class(
    vector: Sequence[float], bank: Sequence[tuple[str, Sequence[float]]], k: int = K_NEIGHBOURS
) -> tuple[str, list[tuple[float, str]]]:
    """余弦 kNN 多数票；并列取相似度和大者，再按类别名。"""
    scored = sorted(
        ((sum(a * b for a, b in zip(vector, emb)), label) for label, emb in bank), key=lambda item: (-item[0], item[1])
    )[:k]
    votes: dict[str, list[float]] = defaultdict(list)
    for similarity, label in scored:
        votes[label].append(similarity)
    winner = sorted(votes, key=lambda label: (-len(votes[label]), -sum(votes[label]), label))[0]
    return winner, scored


def _matches(candidate: Mapping[str, Any], spec: Mapping[str, Any]) -> bool:
    if candidate.get("pred_class") != spec.get("class"):
        return False
    return spec.get("color") is None or candidate.get("pred_color") == spec.get("color")


def decide(row: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """一行的臂 D 输出（候选须已带 `pred_class` / `pred_color`）。"""
    if not candidates:
        return {"status": "none", "object_ids": [], "flag": "K0"}
    program = row.get("relation_program")
    if program is None:
        chosen = [c["object_id"] for c in candidates if _matches(c, row["noun"])]
    else:
        relation = program["relation"]
        refs = [c for c in candidates if _matches(c, relation["ref"])]
        targets = [c for c in candidates if _matches(c, program["target"])]
        chosen = []
        for candidate in targets:
            cx = (candidate["box"][0] + candidate["box"][2] / 2) * common.FRAME_WIDTH
            for ref in refs:
                if ref["object_id"] == candidate["object_id"]:
                    continue
                delta = cx - (ref["box"][0] + ref["box"][2] / 2) * common.FRAME_WIDTH
                if abs(delta) < VIEWER_SIDE_MIN_SEPARATION_PX:
                    continue
                if (relation["type"] == "viewer_left_of" and delta < 0) or (
                    relation["type"] == "viewer_right_of" and delta > 0
                ):
                    chosen.append(candidate["object_id"])
                    break
    status = "none" if not chosen else "unique" if len(chosen) == 1 else "ambiguous"
    return {"status": status, "object_ids": sorted(chosen), "flag": None}
