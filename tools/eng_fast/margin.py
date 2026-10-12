"""P2a 静态 margin（合同 §3.3 后半、AC-4）：同族同会话、≥2 辆同类 `OK` 车辆的帧对。

margin = cos(锚, f_{i+Δ} 上 o) − max cos(锚, f_{i+Δ} 上同类其他对象)；锚 = f_i 上 o 的裁剪嵌入。
Δ ∈ {1, 5, 13} s，按 sidecar `simulation_time_s` 取最近帧、容差 ±0.2 s。报 margin 分布、
`≥0.1` 通过率与锚-自身 `≥0.5` 通过率，按短边层与类别分桶；裁剪 <2 px 记 `CROP_INVALID`。
嵌入器为冻结 `DinoV2Embedder`（源码/权重/许可 sha 与 torch 钉版在其构造器内核对）。
"""

from __future__ import annotations

import bisect
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from tools.eng_fast import common

DELTAS_S: tuple[float, ...] = (1.0, 5.0, 13.0)
TOLERANCE_S = 0.2
MARGIN_PASS = 0.1
SELF_PASS = 0.5
TARGET_PAIRS = 200
PAIR_CAP = 300  # IR-4：每 Δ 按确定性哈希序取前 300 对（≥200 目标的余量）
SEED = "P1-ENG-FAST-001/P2a/20260923"
SIDECAR_CACHE = common.OUT_ROOT / "cache" / "catalog-sim-times.jsonl.gz"


def session_of(frame_id: str) -> str:
    return str(Path(frame_id).parent.as_posix())


def load_sim_times(frame_ids: Iterable[str]) -> dict[str, float]:
    """逐帧 sidecar `simulation_time_s`（缓存；缺 sidecar 即失败）。"""
    wanted = sorted(set(frame_ids))
    if SIDECAR_CACHE.exists():
        rows = common.read_jsonl(SIDECAR_CACHE)
        cached = {row["frame_id"]: row["t"] for row in rows}
        if all(frame in cached for frame in wanted):
            return {frame: cached[frame] for frame in wanted}
    times = {}
    for frame in wanted:
        sidecar = common.absolute(frame).with_suffix(".json")
        document = json.loads(sidecar.read_text(encoding="utf-8"))
        times[frame] = float(document["simulation_time_s"])
    common.write_jsonl(SIDECAR_CACHE, [{"frame_id": f, "t": t} for f, t in sorted(times.items())])
    return times


def eligible_pairs(
    index: Mapping[str, Mapping[str, Any]], times: Mapping[str, float], delta: float
) -> list[dict[str, Any]]:
    """IR-4：f_i 上 o 与 ≥1 辆同类其他 `OK` 车同框（即 ≥2 辆同类）；f_{i+Δ} 为同会话最近帧（±0.2 s），
    其上 o 仍为 `OK` 且另有 ≥1 辆同类 `OK` 车。只取已知类别的目录车（不含动态目标）。"""
    by_session: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for frame_id, row in index.items():
        if row.get("usable") and frame_id in times:
            by_session[session_of(frame_id)].append((times[frame_id], frame_id))
    pairs = []
    for session, entries in sorted(by_session.items()):
        entries.sort()
        stamps = [stamp for stamp, _ in entries]
        for stamp, frame_id in entries:
            anchor_row = index[frame_id]
            classes: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
            for vehicle in anchor_row["vehicles"]:
                if vehicle.get("class_word"):
                    classes[vehicle["class_word"]].append(vehicle)
            groups = {c: v for c, v in classes.items() if len(v) >= 2}
            if not groups:
                continue
            goal = stamp + delta
            position = bisect.bisect_left(stamps, goal)
            nearest = None
            for candidate in (position - 1, position):
                if 0 <= candidate < len(entries) and abs(stamps[candidate] - goal) <= TOLERANCE_S:
                    if nearest is None or abs(stamps[candidate] - goal) < abs(stamps[nearest] - goal):
                        nearest = candidate
            if nearest is None:
                continue
            later_id = entries[nearest][1]
            if later_id == frame_id:
                continue
            later = {v["object_id"]: v for v in index[later_id]["vehicles"] if v.get("class_word")}
            for class_word, members in sorted(groups.items()):
                for member in members:
                    target = later.get(member["object_id"])
                    if target is None:
                        continue
                    others = [
                        v for oid, v in later.items() if v["class_word"] == class_word and oid != member["object_id"]
                    ]
                    if not others:
                        continue
                    pairs.append(
                        {
                            "delta_s": delta,
                            "session": session,
                            "family": anchor_row["family"],
                            "anchor_frame": frame_id,
                            "later_frame": later_id,
                            "dt_s": round(stamps[nearest] - stamp, 6),
                            "object_id": member["object_id"],
                            "class_word": class_word,
                            "anchor_box": list(member["box"]),
                            "later_box": list(target["box"]),
                            "others": [{"object_id": v["object_id"], "box": list(v["box"])} for v in others],
                        }
                    )
    return pairs


def pair_key(pair: Mapping[str, Any]) -> str:
    text = f"{SEED}|{pair['delta_s']}|{pair['anchor_frame']}|{pair['object_id']}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def select_pairs(pairs: Sequence[Mapping[str, Any]], cap: int = PAIR_CAP) -> list[Mapping[str, Any]]:
    return sorted(pairs, key=pair_key)[:cap]


def score_pairs(
    pairs: Sequence[Mapping[str, Any]],
    embed: Callable[[str, Sequence[float]], Sequence[float] | None],
    cosine: Callable[[Sequence[float], Sequence[float]], float],
) -> list[dict[str, Any]]:
    """embed(path, box) → 单位向量或 None（CROP_INVALID）。"""
    scored = []
    for pair in pairs:
        anchor = embed(pair["anchor_frame"], pair["anchor_box"])
        target = embed(pair["later_frame"], pair["later_box"])
        other_vectors = [embed(pair["later_frame"], other["box"]) for other in pair["others"]]
        valid_others = [vector for vector in other_vectors if vector is not None]
        record = {
            key: pair[key]
            for key in ("delta_s", "family", "anchor_frame", "later_frame", "dt_s", "object_id", "class_word")
        }
        record["stratum"] = common.stratum_of(common.short_side_px(pair["later_box"]))
        record["others"] = len(pair["others"])
        record["others_crop_invalid"] = len(other_vectors) - len(valid_others)
        if anchor is None or target is None or not valid_others:
            record["status"] = "CROP_INVALID"
            scored.append(record)
            continue
        self_cos = cosine(anchor, target)
        other_max = max(cosine(anchor, vector) for vector in valid_others)
        record.update(
            {
                "status": "OK",
                "self_cos": round(self_cos, 6),
                "max_other_cos": round(other_max, 6),
                "margin": round(self_cos - other_max, 6),
            }
        )
        scored.append(record)
    return scored


def _stats(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ok = [r for r in records if r["status"] == "OK"]
    margins = [r["margin"] for r in ok]
    return {
        "pairs": len(records),
        "crop_invalid": len(records) - len(ok),
        "scored": len(ok),
        "margin": common.quantiles(margins, (0.05, 0.25, 0.5, 0.75, 0.95)),
        "margin_ge_0_1": sum(1 for m in margins if m >= MARGIN_PASS),
        "margin_ge_0_1_rate": round(sum(1 for m in margins if m >= MARGIN_PASS) / len(ok), 6) if ok else None,
        "self_ge_0_5": sum(1 for r in ok if r["self_cos"] >= SELF_PASS),
        "self_ge_0_5_rate": round(sum(1 for r in ok if r["self_cos"] >= SELF_PASS) / len(ok), 6) if ok else None,
    }


def summarize(scored: Sequence[Mapping[str, Any]], eligible_counts: Mapping[float, int]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for delta in DELTAS_S:
        records = [r for r in scored if r["delta_s"] == delta]
        entry = {
            "eligible_pairs": int(eligible_counts.get(delta, 0)),
            "selected_pairs": len(records),
            "meets_target_200": sum(1 for r in records if r["status"] == "OK") >= TARGET_PAIRS,
            **_stats(records),
            "by_stratum": {s: _stats([r for r in records if r["stratum"] == s]) for s in common.STRATA},
            "by_class": {
                c: _stats([r for r in records if r["class_word"] == c])
                for c in sorted({r["class_word"] for r in records})
            },
            "by_family": {
                f: len([r for r in records if r["family"] == f]) for f in sorted({r["family"] for r in records})
            },
        }
        summary[f"{delta:g}s"] = entry
    return summary
