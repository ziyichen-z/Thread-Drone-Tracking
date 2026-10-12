"""评估公共件（合同 §3.1.3、§3.3、§3.4；AC-3/AC-4）：检测、ignore 过滤匹配、分桶召回、FP/帧、门判定、
序列构造与口径 A 回放。`select`（只看 V）与 `qualify`（H 一次）共用；本模块自身不区分域，
域约束由调用方的表标签 `domain` 与 `select.require_v` / `qualify.FreezeGuard` 执行。

匹配（§3.1.3，写在本项内、不改 FAST-001 `recall.py`）：每帧检测按分数降序，与**未匹配**正样本
IoU ≥ 阈值（0.50 主 / 0.30 副）贪心一对一匹配（候选类别无关，与 FAST-001 同）；未匹配检测若与
任一 ignore 框 IoA（交集/检测面积）≥ 0.5 → 丢弃；其余未匹配检测 = FP。整帧排除帧不进任何分母。
"""

from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from tools.eng_det import common
from tools.eng_fast import replay as fast_replay

CONF_FLOOR = 0.25
CONF_CANDIDATES = (0.25, 0.40)
IOU_MAIN = 0.50
IOU_SIDE = 0.30
IGNORE_IOA = 0.5
N_MIN_RECALL = 50
N_MIN_FP_FRAMES = 300
N_MIN_WINDOWS = 30
MAX_GAP_S = 2.0
WINDOW_GATE_S = 13.0

MET = "MET"
GATE_NOT_MET = "GATE_NOT_MET"
NOT_EVALUABLE = "NOT_EVALUABLE"


# --- 检测 -------------------------------------------------------------------


class Detector:
    """冻结或候选权重的 ultralytics 检测器；每次实例化记一次 `model_start`（不限次、逐次记账）。"""

    def __init__(self, weights: Path, imgsz: int, device: str, *, label: str, ledger: Any = None, conf: float = CONF_FLOOR):
        from ultralytics import YOLO  # noqa: PLC0415

        if ledger is not None:
            ledger.charge("model_start", 1, label=label, weights_sha256=common.sha256_file(weights), device=device, imgsz=imgsz)
        self.weights = Path(weights)
        self.weights_sha256 = common.sha256_file(weights)
        self.imgsz = int(imgsz)
        self.device = device
        self.conf = float(conf)
        self.model = YOLO(str(weights))

    def detect_image(self, image: Any) -> list[list[float]]:
        height, width = image.shape[:2]
        results = self.model.predict(source=image, imgsz=self.imgsz, conf=self.conf, device=self.device, verbose=False)
        boxes = results[0].boxes
        rows = []
        for (x1, y1, x2, y2), score, label in zip(boxes.xyxy.cpu().tolist(), boxes.conf.cpu().tolist(), boxes.cls.cpu().tolist()):
            left, top = max(0.0, x1 / width), max(0.0, y1 / height)
            right, bottom = min(1.0, x2 / width), min(1.0, y2 / height)
            if right <= left or bottom <= top or not math.isfinite(score):
                continue
            rows.append([round(left, 7), round(top, 7), round(right - left, 7), round(bottom - top, 7), round(float(score), 6), float(int(label))])
        return rows


def read_image(frame_id: str) -> Any:
    import cv2  # noqa: PLC0415

    image = cv2.imread(str(common.data_path(frame_id)), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"无法读取 {frame_id}")
    return image


def detect_frames(detector: Detector, frame_ids: Sequence[str], cache: Path) -> dict[str, list[list[float]]]:
    """逐帧检测（conf ≥ 0.25 已由库过滤）；缓存头记录权重 sha/imgsz/device，不符则重算。"""
    header = {"weights_sha256": detector.weights_sha256, "imgsz": detector.imgsz, "device": detector.device, "conf": detector.conf}
    out: dict[str, list[list[float]]] = {}
    if cache.exists():
        with gzip.open(cache, "rt", encoding="utf-8") as handle:
            first = json.loads(handle.readline())
            if first == {"header": header}:
                for line in handle:
                    row = json.loads(line)
                    out[row["frame_id"]] = row["dets"]
    missing = [f for f in frame_ids if f not in out]
    if missing:
        common.refuse_protected(cache)
        cache.parent.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        for frame_id in missing:
            out[frame_id] = detector.detect_image(read_image(frame_id))
        rows = [{"header": header}] + [{"frame_id": f, "dets": out[f]} for f in sorted(out)]
        common.write_jsonl(cache, rows)
        print(json.dumps({"cache": common.rel_project(cache), "detected": len(missing), "s": round(time.perf_counter() - started, 1)}), flush=True)
    return {f: out[f] for f in frame_ids}


# --- 匹配与召回 -------------------------------------------------------------


def match_frame(
    dets: Sequence[Sequence[float]],
    positives: Sequence[Sequence[float]],
    ignores: Sequence[Sequence[float]],
    iou_thr: float,
    conf: float,
) -> dict[str, Any]:
    """§3.1.3 单帧匹配：返回每个正样本是否命中与 TP/FP/丢弃计数（纯函数）。"""
    kept = sorted((d for d in dets if float(d[4]) >= conf), key=lambda d: -float(d[4]))
    matched = [False] * len(positives)
    tp = fp = discarded = 0
    for det in kept:
        best_index, best_iou = -1, iou_thr
        for index, box in enumerate(positives):
            if matched[index]:
                continue
            value = common.iou_xywh(det[:4], box)
            if value >= best_iou and (best_index < 0 or value > best_iou):
                best_index, best_iou = index, value
        if best_index >= 0:
            matched[best_index] = True
            tp += 1
        elif any(common.ioa_xywh(det[:4], region) >= IGNORE_IOA for region in ignores):
            discarded += 1
        else:
            fp += 1
    return {"hits": matched, "tp": tp, "fp": fp, "discarded": discarded, "detections": len(kept)}


def evaluate(
    rows: Iterable[Mapping[str, Any]],
    dets: Mapping[str, Sequence[Sequence[float]]],
    conf: float,
    distance_of: Callable[[Mapping[str, Any], Mapping[str, Any]], tuple[str, float | None]] | None = None,
) -> dict[str, Any]:
    """一个评估域在一个 conf 下：逐正样本命中（双 IoU）+ FP/帧（双 IoU）。整帧排除帧跳过。"""
    outcomes = []
    frames = 0
    fp = {IOU_MAIN: 0, IOU_SIDE: 0}
    discarded = {IOU_MAIN: 0, IOU_SIDE: 0}
    detections = 0
    for row in rows:
        if row["excluded"]:
            continue
        frames += 1
        frame_dets = dets[row["frame_id"]]
        positives = [p["box"] for p in row["positives"]]
        ignores = [i["box"] for i in row["ignores"]]
        per_iou = {thr: match_frame(frame_dets, positives, ignores, thr, conf) for thr in (IOU_MAIN, IOU_SIDE)}
        detections += per_iou[IOU_MAIN]["detections"]
        for thr, result in per_iou.items():
            fp[thr] += result["fp"]
            discarded[thr] += result["discarded"]
        for index, p in enumerate(row["positives"]):
            axis, metres = distance_of(row, p) if distance_of else ("axial", p.get("depth_m"))
            outcomes.append(
                {
                    "frame_id": row["frame_id"],
                    "family": row["family"],
                    "cls": common.CLASS_NAMES[p["cls"]],
                    "stratum": common.stratum_of(p["side_px"]),
                    "axis": axis,
                    "distance_bin": common.distance_bin(metres) if metres is not None else "NA",
                    "hit_030": per_iou[IOU_SIDE]["hits"][index],
                    "hit_050": per_iou[IOU_MAIN]["hits"][index],
                }
            )
    return {
        "conf": conf,
        "frames": frames,
        "detections": detections,
        "fp_050": fp[IOU_MAIN],
        "fp_030": fp[IOU_SIDE],
        "discarded_by_ignore_050": discarded[IOU_MAIN],
        "discarded_by_ignore_030": discarded[IOU_SIDE],
        "fp_per_frame_050": round(fp[IOU_MAIN] / frames, 6) if frames else None,
        "fp_per_frame_030": round(fp[IOU_SIDE] / frames, 6) if frames else None,
        "outcomes": outcomes,
    }


def cell(items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    n = len(items)
    h30 = [bool(i["hit_030"]) for i in items]
    h50 = [bool(i["hit_050"]) for i in items]
    return {
        "n": n,
        "hit_030": sum(h30),
        "hit_050": sum(h50),
        "rate_030": round(sum(h30) / n, 6) if n else None,
        "rate_050": round(sum(h50) / n, 6) if n else None,
        "ci95_030": common.bootstrap_ci(h30),
        "ci95_050": common.bootstrap_ci(h50),
    }


def recall_table(outcomes: Sequence[Mapping[str, Any]], domain: str, tag: str | None = None) -> dict[str, Any]:
    """类别 × 短边 S/M/L（门用）+ 短边 × 距离档（分轴：axial / slant / none）描述格；无单一总召回。"""
    table: dict[str, Any] = {"domain": domain, "tag": tag, "classes": {}}
    for cls_name in common.CLASS_NAMES:
        items = [o for o in outcomes if o["cls"] == cls_name]
        by_stratum = {s: cell([o for o in items if o["stratum"] == s]) for s in common.STRATA}
        cross: dict[str, Any] = {}
        for axis in sorted({o["axis"] for o in items}):
            for s in common.STRATA:
                for d in (*common.DISTANCE_BINS, "NA"):
                    subset = [o for o in items if o["axis"] == axis and o["stratum"] == s and o["distance_bin"] == d]
                    if subset:
                        cross[f"{axis}|{s}|{d}"] = cell(subset)
        by_distance: dict[str, Any] = {}
        for axis in sorted({o["axis"] for o in items}):
            for d in (*common.DISTANCE_BINS, "NA"):
                subset = [o for o in items if o["axis"] == axis and o["distance_bin"] == d]
                if subset:
                    by_distance[f"{axis}|{d}"] = cell(subset)
        table["classes"][cls_name] = {"by_stratum": by_stratum, "stratum_x_distance": cross, "by_distance": by_distance}
    return table


# --- 门判定（AR1-4）---------------------------------------------------------


def recall_cell_verdict(c: Mapping[str, Any], threshold: float, iou_key: str = "rate_050") -> dict[str, Any]:
    n = int(c["n"])
    if n < N_MIN_RECALL:
        return {"n": n, "value": c.get(iou_key), "threshold": threshold, "verdict": f"N/A(INSUFFICIENT_N={n})"}
    value = float(c[iou_key])
    return {"n": n, "value": value, "threshold": threshold, "verdict": MET if value >= threshold else GATE_NOT_MET}


def fp_verdict(result: Mapping[str, Any], threshold: float = 0.50) -> dict[str, Any]:
    frames = int(result["frames"])
    if frames < N_MIN_FP_FRAMES:
        return {"n": frames, "value": result["fp_per_frame_050"], "threshold": threshold, "verdict": f"N/A(INSUFFICIENT_N={frames})"}
    value = float(result["fp_per_frame_050"])
    return {"n": frames, "value": value, "threshold": threshold, "verdict": MET if value <= threshold else GATE_NOT_MET}


def retention_verdict(summary: Mapping[str, Any] | None, threshold: float) -> dict[str, Any]:
    if summary is None:
        return {"n": 0, "value": None, "threshold": threshold, "verdict": "N/A(NO_SEGMENT)"}
    judged = int(summary["D"])
    if judged < N_MIN_WINDOWS:
        return {"n": judged, "value": summary.get("retention"), "threshold": threshold, "verdict": f"N/A(INSUFFICIENT_N={judged})"}
    value = float(summary["retention"])
    return {"n": judged, "value": value, "threshold": threshold, "verdict": MET if value >= threshold else GATE_NOT_MET}


def gate(cells: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """一门 = 全部定义格：全可判且过 → MET；任一可判未过 → GATE_NOT_MET；否则 NOT_EVALUABLE(<格>)。"""
    verdicts = {name: c["verdict"] for name, c in cells.items()}
    if any(v == GATE_NOT_MET for v in verdicts.values()):
        overall = GATE_NOT_MET
    elif all(v == MET for v in verdicts.values()):
        overall = MET
    else:
        overall = f"{NOT_EVALUABLE}({','.join(sorted(n for n, v in verdicts.items() if v != MET))})"
    return {"verdict": overall, "cells": dict(cells)}


def detection_gates(table: Mapping[str, Any], fp_result: Mapping[str, Any], prefix: str) -> dict[str, Any]:
    """G-1/G-1s/G-2/G-3（或 V-1/V-1s/V-2/V-3）：冻结 conf 单阈值、IoU 0.50 主口径。"""
    t = table["classes"]["target"]["by_stratum"]
    v = table["classes"]["vehicle"]["by_stratum"]
    return {
        f"{prefix}-1": gate({"target|M": recall_cell_verdict(t["M"], 0.90), "target|L": recall_cell_verdict(t["L"], 0.90)}),
        f"{prefix}-1s": gate({"target|S": recall_cell_verdict(t["S"], 0.70)}),
        f"{prefix}-2": gate(
            {
                "vehicle|M": recall_cell_verdict(v["M"], 0.90),
                "vehicle|L": recall_cell_verdict(v["L"], 0.90),
                "vehicle|S": recall_cell_verdict(v["S"], 0.70),
            }
        ),
        f"{prefix}-3": gate({"fp_per_frame": fp_verdict(fp_result)}),
    }


# --- 序列（§3.4）-------------------------------------------------------------


def target_truth(row: Mapping[str, Any]) -> list[float] | None:
    """序列真值：目标车正样本框（可见）或 None（不可见/ignore/整帧排除）。"""
    if row["excluded"]:
        return None
    for p in row["positives"]:
        if p["cls"] == common.CLASS_TARGET:
            return list(p["box"])
    return None


def split_subsequences(rows: Sequence[Mapping[str, Any]], track_buffer: int) -> tuple[list[list[Mapping[str, Any]]], dict[str, Any]]:
    """会话内按仿真时间升序；帧间隔 > 2 s 处切分；短于 13 s + track_buffer 帧（按该子序列中位间隔折秒）丢弃。"""
    ordered = sorted(rows, key=lambda r: (r["sim_t"], r["frame_id"]))
    pieces: list[list[Mapping[str, Any]]] = []
    current: list[Mapping[str, Any]] = []
    for row in ordered:
        if current and row["sim_t"] - current[-1]["sim_t"] > MAX_GAP_S:
            pieces.append(current)
            current = []
        current.append(row)
    if current:
        pieces.append(current)
    kept, dropped = [], []
    for piece in pieces:
        times = [r["sim_t"] for r in piece]
        intervals = [b - a for a, b in zip(times, times[1:])]
        median = statistics.median(intervals) if intervals else 0.0
        need = WINDOW_GATE_S + track_buffer * median
        duration = times[-1] - times[0]
        (kept if len(piece) > 1 and duration >= need else dropped).append(piece)
    return kept, {"pieces": len(pieces), "kept": len(kept), "dropped": len(dropped), "dropped_frames": sum(len(p) for p in dropped)}


def tracker_for(algorithm: str, match_thresh: float, track_buffer: int) -> Any:
    args = fast_replay.tracker_args(algorithm)
    args.match_thresh = float(match_thresh)
    args.track_buffer = int(track_buffer)
    from ultralytics.trackers import BOTSORT, BYTETracker  # noqa: PLC0415

    return BOTSORT(args=args) if algorithm == "botsort" else BYTETracker(args=args)


def frozen_tracker_args(algorithm: str, match_thresh: float, track_buffer: int) -> dict[str, Any]:
    args = fast_replay.tracker_args(algorithm)
    args.match_thresh = float(match_thresh)
    args.track_buffer = int(track_buffer)
    return {key: getattr(args, key) for key in args.__dict__}


def replay_piece(
    piece: Sequence[Mapping[str, Any]],
    dets: Mapping[str, Sequence[Sequence[float]]],
    conf: float,
    algorithm: str,
    match_thresh: float,
    track_buffer: int,
) -> dict[str, Any]:
    """口径 A：冻结关联器逐帧恰一次 `update`；每帧真值 IoU ≥ 0.30 重绑定（`replay.bind`）；七类结局。"""
    tracker = tracker_for(algorithm, match_thresh, track_buffer)
    frames = []
    for row in piece:
        frame_dets = [d for d in dets[row["frame_id"]] if float(d[4]) >= conf]
        loader = (lambda fid=row["frame_id"]: read_image(fid)) if algorithm == "botsort" else _blank_image
        frames.append((frame_dets, loader, common.FRAME_WIDTH, common.FRAME_HEIGHT))
    outputs = fast_replay.run_sequence(tracker, frames)
    times = [float(r["sim_t"]) for r in piece]
    fast_replay.check_timestamps(times)
    if max((b - a for a, b in zip(times, times[1:])), default=0.0) > MAX_GAP_S:
        raise AssertionError("子序列最大间隔 > 2 s")
    truths = [target_truth(r) for r in piece]
    bindings = fast_replay.bind(truths, outputs, common.FRAME_WIDTH, common.FRAME_HEIGHT)
    return {
        "first_frame": piece[0]["frame_id"],
        "frames": len(piece),
        "duration_s": round(times[-1] - times[0], 3),
        "max_interval_s": round(max((b - a for a, b in zip(times, times[1:])), default=0.0), 6),
        "windows": {f"{int(w)}s": fast_replay.window_summary(times, bindings, w, track_buffer) for w in fast_replay.WINDOWS_S},
        "sequence": fast_replay.sequence_metrics(times, bindings, track_buffer),
    }


_BLANK: Any = None


def _blank_image() -> Any:
    """ByteTrack 不读图（GMC 只在 BoT-SORT）：给一张固定空图，免读盘。"""
    global _BLANK
    if _BLANK is None:
        import numpy as np  # noqa: PLC0415

        _BLANK = np.zeros((common.FRAME_HEIGHT, common.FRAME_WIDTH, 3), dtype=np.uint8)
    return _BLANK


def pool_windows(pieces: Sequence[Mapping[str, Any]], window: str) -> dict[str, Any] | None:
    """合并若干子序列的窗口计数（D>0 的子序列才计入；无 → None = NO_SEGMENT）。"""
    total: Counter = Counter()
    used = 0
    for piece in pieces:
        summary = piece["windows"][window]
        if summary["D"] <= 0:
            continue
        used += 1
        for key in (*fast_replay.OUTCOMES, "V", "D"):
            total[key] += int(summary[key])
        total["drift_return"] += int(summary.get("drift_return", 0))
    if not used:
        return None
    return {
        **{k: int(v) for k, v in total.items()},
        "pieces_with_D": used,
        "retention": round(total[fast_replay.KEPT] / total["D"], 6) if total["D"] else None,
    }


def sessions(rows: Iterable[Mapping[str, Any]], families: Sequence[str]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["family"] in families:
            grouped[row["session"]].append(row)
    return dict(sorted(grouped.items()))


# --- 离线斜距（Table B / G-4；只进评分）---------------------------------------

_SLANT_CACHE: dict[str, dict[int, float | None]] = {}


def target_slant_m(frame_id: str) -> float | None:
    """演示路线帧的目标斜距（既有 Unity 真值 sidecar；只用于离线分桶，AC-8）。"""
    from tools.dist_data import roots  # noqa: PLC0415

    source = roots.truth_source_for(frame_id)
    if source is None:
        return None
    path, schema = source
    absolute = common.data_path(path)
    number = int(Path(frame_id).stem.split("_")[1])
    if schema == "scouting":
        if not absolute.is_file():
            return None
        value = json.loads(absolute.read_text(encoding="utf-8")).get("target_slant_range_m")
        return float(value) if value is not None and math.isfinite(float(value)) else None
    if path not in _SLANT_CACHE:
        table: dict[int, float | None] = {}
        with open(absolute, encoding="utf-8") as handle:
            for line in handle:
                item = json.loads(line)
                try:
                    table[int(item["frame_id"])] = math.dist(
                        (item["target_world_x_m"], item["target_world_y_m"], item["target_world_z_m"]),
                        (item["body_world_x_m"], item["body_world_y_m"], item["body_world_z_m"]),
                    )
                except (KeyError, TypeError):
                    table[int(item["frame_id"])] = None
        _SLANT_CACHE[path] = table
    return _SLANT_CACHE[path].get(number)


def distance_with_slant(row: Mapping[str, Any], positive: Mapping[str, Any]) -> tuple[str, float | None]:
    """车辆：轴向深度；目标：演示路线/m3 会话有斜距则用斜距，否则无距离（NA）。"""
    if positive["cls"] == common.CLASS_VEHICLE:
        return "axial", positive.get("depth_m")
    slant = target_slant_m(row["frame_id"])
    return ("slant", slant) if slant is not None else ("none", None)
