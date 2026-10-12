"""常驻关联回放（E1/E2 共用）与 E2 读数（§3.9；AC-5/AC-8）。

- 回放：每段新建一个 `make_resident_associator`（冻结 BoT-SORT 参数，只改传入的 `track_buffer`），逐帧恰一次
  `update(boxes, img)`；`pose` 用相邻帧 sidecar 位姿单应（`set_pose_warp`），`optflow` 读核过 sha 的 JPEG 走库原
  `sparseOptFlow`，`none` 不补偿（`pose`/`none` 给空图，不读 JPEG）。每帧输出行、`lost_stracks` 预测框与移除 ID
  经 `rows_from_library` 交 `ResidentCore.record`（与插件 `step` 同一实现）写历史；记录流落 `outputs/eng-acq/`。
- E2：红车 FAST-001 R4 口径 A 13 s 保持率（`window_summary` 七类结局与守恒式逐字复用，另加 H-9 空窗断言）、
  每对象 ID 切换数（`sequence_metrics`）、静止车 track 寿命；位姿单应自检表（a7 旋转 ≥ 5° 相邻帧）。
- 真值只在评分（`replay.bind` IoU ≥ 0.3 逐帧绑定）与自检中出现，不进关联器输入。
"""

from __future__ import annotations

import gzip
import json
import statistics
from pathlib import Path
from typing import Any, Mapping, Sequence

from controller.det_assoc_tracker import make_resident_associator
from controller.pose_gmc import pose_homography, rotation_angle_deg, warp_box_xyxy
from controller.resident_core import ResidentCore, TrackRow, rows_from_library
from tools.eng_acq import common
from tools.eng_acq.data import FRAME_HEIGHT, FRAME_WIDTH, RED_ID, SPEC, Frame, ImageCache
from tools.eng_fast import replay as fast_replay

WINDOW_S = 13.0
MAX_GAP_S = 2.0
EMPTY_WINDOW_MAX_GAP_S = 8.0
BUFFERS: tuple[int, ...] = (10, 20, 30)
GMC_SOURCES: tuple[str, ...] = ("pose", "optflow", "none")
SELFCHECK_MIN_ROTATION_DEG = 5.0


class EmptyWindow(AssertionError):
    """H-9（FAST-001 R1-2）：窗口内零帧（>8 s 空窗）不得零证据判 `KEPT`，线束拒绝。"""


def frozen_args(track_buffer: int) -> dict[str, Any]:
    args = dict(common.read_json(SPEC)["association"]["args"])
    args["track_buffer"] = int(track_buffer)
    return args


def _blank() -> Any:
    import numpy as np  # noqa: PLC0415

    return np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)


def replay_segment(frames: Sequence[Frame], gmc_source: str, track_buffer: int, images: ImageCache | None, guard: Any = None) -> list[dict[str, Any]]:
    """一段：逐帧恰一次库 `update`，返回每帧 `HistoryEntry.as_record()`（常驻核心写历史的同一输入）。"""
    associator = make_resident_associator("botsort", frozen_args(track_buffer), gmc_source)
    core = ResidentCore(128)
    blank = _blank()
    records: list[dict[str, Any]] = []
    previous: Mapping[str, Any] | None = None
    for frame in frames:
        if guard is not None:
            guard.check()
        if gmc_source == "pose" and previous is not None:
            associator.set_pose_warp(pose_homography(previous, frame.metadata))
        image = images.get(frame) if gmc_source == "optflow" else blank
        removed_before = {int(t.track_id) for t in associator.removed_stracks}
        output = associator.update(fast_replay.as_boxes(frame.dets, FRAME_WIDTH, FRAME_HEIGHT), image)
        rows = [[float(v) for v in row] for row in output.tolist()] if len(output) else []
        removed_after = {int(t.track_id) for t in associator.removed_stracks}
        tracked, lost = rows_from_library(rows, list(associator.lost_stracks), FRAME_WIDTH, FRAME_HEIGHT)
        entry = core.record(frame.frame_id, frame.metadata, tracked, lost, sorted(removed_after - removed_before), int(associator.frame_id))
        records.append(entry.as_record())
        previous = frame.metadata
    if associator.frame_id != len(frames):
        raise AssertionError("associator frame_id ≠ frames")
    return records


def rows_of(record: Mapping[str, Any], state: str) -> list[TrackRow]:
    return [
        TrackRow(int(t["track_id"]), tuple(t["box_norm"]), float(t["score"]), int(t["cls"]), t["state"])  # type: ignore[arg-type]
        for t in record["tracks"]
        if t["state"] == state
    ]


def write_records(path: Path, payload: Mapping[str, Any]) -> str:
    common.refuse_protected(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = gzip.compress(common.json_bytes(payload), mtime=0)
    return common.atomic_write_bytes(path, data)


def read_records(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def records_path(sequence: str, gmc_source: str, track_buffer: int) -> Path:
    return common.OUT_DIR / "records" / f"{sequence}-{gmc_source}-b{track_buffer}.json.gz"


# --- E2 读数 ----------------------------------------------------------------


def _pixel_rows(record: Mapping[str, Any]) -> list[list[float]]:
    rows = []
    for t in record["tracks"]:
        if t["state"] != "tracked":
            continue
        x, y, w, h = t["box_norm"]
        rows.append([x * FRAME_WIDTH, y * FRAME_HEIGHT, (x + w) * FRAME_WIDTH, (y + h) * FRAME_HEIGHT, t["track_id"], t["score"], t["cls"], 0])
    return rows


def assert_no_empty_window(times: Sequence[float], bindings: Sequence[int | None], window_s: float) -> None:
    """H-9：每个非截尾起点的窗口内至少有一帧，且片内最大帧间隔 ≤ 8 s；否则拒绝。"""
    if any(b - a > EMPTY_WINDOW_MAX_GAP_S for a, b in zip(times, times[1:])):
        raise EmptyWindow("frame gap > 8 s inside a scored piece")
    for start, binding in enumerate(bindings):
        if binding is None:
            continue
        end = times[start] + window_s
        if end > times[-1]:
            continue
        if not any(times[start] < t <= end for t in times[start + 1 :]):
            raise EmptyWindow(f"empty {window_s} s window at start {start}")


def guarded_window_summary(times: Sequence[float], bindings: Sequence[int | None], window_s: float, buffer: int) -> dict[str, Any]:
    assert_no_empty_window(times, bindings, window_s)
    return fast_replay.window_summary(times, bindings, window_s, buffer)


def _pieces(frames: Sequence[Frame], track_buffer: int) -> list[tuple[int, int]]:
    """口径 A 子序列：帧间隔 > 2 s 切分；短于 13 s + buffer × 中位间隔的丢弃（同 `evaluate.split_subsequences`）。"""
    cuts = [0] + [i for i in range(1, len(frames)) if frames[i].sim_t - frames[i - 1].sim_t > MAX_GAP_S] + [len(frames)]
    kept = []
    for a, b in zip(cuts, cuts[1:]):
        times = [f.sim_t for f in frames[a:b]]
        intervals = [y - x for x, y in zip(times, times[1:])]
        median = statistics.median(intervals) if intervals else 0.0
        if b - a > 1 and times[-1] - times[0] >= WINDOW_S + track_buffer * median:
            kept.append((a, b))
    return kept


def segment_metrics(frames: Sequence[Frame], records: Sequence[Mapping[str, Any]], track_buffer: int) -> dict[str, Any]:
    outputs = [_pixel_rows(r) for r in records]
    times = [f.sim_t for f in frames]
    # 红车口径 A 13 s 保持率（逐字复用 window_summary + 空窗断言）。
    red_pieces = []
    for a, b in _pieces(frames, track_buffer):
        truths = [f.red for f in frames[a:b]]
        bindings = fast_replay.bind(truths, outputs[a:b], FRAME_WIDTH, FRAME_HEIGHT)
        red_pieces.append(guarded_window_summary(times[a:b], bindings, WINDOW_S, track_buffer))
    # 每对象 ID 切换与静止车 track 寿命。
    object_ids = sorted({object_id for f in frames for object_id in f.objects()})
    per_object: dict[str, Any] = {}
    lifetimes: list[float] = []
    for object_id in object_ids:
        truths = [f.objects().get(object_id) for f in frames]
        bindings = fast_replay.bind(truths, outputs, FRAME_WIDTH, FRAME_HEIGHT)
        metrics = fast_replay.sequence_metrics(times, bindings, track_buffer)
        spans: dict[int, list[float]] = {}
        for t, b in zip(times, bindings):
            if b not in (None, fast_replay.NO_BINDING):
                spans.setdefault(int(b), []).append(t)
        if object_id != RED_ID:
            lifetimes.extend(max(v) - min(v) for v in spans.values())
        per_object[object_id] = {
            "class": "red" if object_id == RED_ID else "static",
            "visible_frames": metrics["visible_frames"],
            "bound_frames": metrics["bound_frames"],
            "id_switches": metrics["id_switches"],
            "distinct_bound_ids": len(spans),
        }
    return {"red_windows_13s": red_pieces, "objects": per_object, "static_track_lifetimes_s": lifetimes}


def pool_windows(pieces: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total: dict[str, int] = {k: 0 for k in (*fast_replay.OUTCOMES, "V", "D")}
    for piece in pieces:
        for key in total:
            total[key] += int(piece[key])
    judged = total["D"]
    conserved = total["V"] == sum(total[k] for k in fast_replay.EXCLUDED) + judged
    if not conserved:
        raise AssertionError("pooled window counts not conserved")
    return {**total, "retention": round(total[fast_replay.KEPT] / judged, 6) if judged else None, "pieces": len(pieces), "conserved": conserved}


def quantiles(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "mean": None, "median": None, "p90": None}
    ordered = sorted(values)
    p90 = ordered[min(len(ordered) - 1, int(round(0.9 * (len(ordered) - 1))))]
    return {"n": len(ordered), "mean": round(statistics.fmean(ordered), 6), "median": round(statistics.median(ordered), 6), "p90": round(p90, 6)}


def summarize(sequence: str, gmc_source: str, track_buffer: int, segments: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    pieces = [p for s in segments for p in s["red_windows_13s"]]
    objects: dict[str, Any] = {}
    lifetimes: list[float] = []
    for index, s in enumerate(segments):
        lifetimes.extend(s["static_track_lifetimes_s"])
        for object_id, value in s["objects"].items():
            objects[f"seg{index}:{object_id}"] = value
    switches_static = [v["id_switches"] for v in objects.values() if v["class"] == "static"]
    switches_red = [v["id_switches"] for v in objects.values() if v["class"] == "red"]
    return {
        "sequence": sequence,
        "gmc_source": gmc_source,
        "track_buffer_calls": track_buffer,
        "track_buffer_s_nominal": round(track_buffer * 0.2, 3),
        "red_retention_13s_caliber_A": pool_windows(pieces) if pieces else None,
        "id_switches": {
            "static_objects": len(switches_static),
            "static_total": sum(switches_static),
            "static_per_object": quantiles([float(v) for v in switches_static]),
            "red_segments": len(switches_red),
            "red_total": sum(switches_red),
        },
        "static_track_lifetime_s": quantiles(lifetimes),
        "empty_window_assertion": "present; not triggered",
    }


# --- 位姿单应自检（AC-5 第三条）----------------------------------------------


def _center(box: Sequence[float]) -> tuple[float, float]:
    return (float(box[0]) + float(box[2]) / 2) * FRAME_WIDTH, (float(box[1]) + float(box[3]) / 2) * FRAME_HEIGHT


def pose_selfcheck(segments: Sequence[Sequence[Frame]], min_rotation_deg: float = SELFCHECK_MIN_ROTATION_DEG) -> dict[str, Any]:
    """旋转 ≥ 5° 的相邻帧：静止车真值框经 H（四角 AABB）映射后与下一帧真值框中心误差，对照无补偿。"""
    compensated: list[float] = []
    uncompensated: list[float] = []
    frame_pairs = 0
    for frames in segments:
        for previous, current in zip(frames, frames[1:]):
            if rotation_angle_deg(previous.metadata, current.metadata) < min_rotation_deg:
                continue
            frame_pairs += 1
            h = pose_homography(previous.metadata, current.metadata)
            now = dict(current.statics)
            for object_id, box in previous.statics:
                if object_id not in now:
                    continue
                x, y, w, hh = box
                warped = warp_box_xyxy(h, (x * FRAME_WIDTH, y * FRAME_HEIGHT, (x + w) * FRAME_WIDTH, (y + hh) * FRAME_HEIGHT))
                target = _center(now[object_id])
                uncompensated.append(((target[0] - _center(box)[0]) ** 2 + (target[1] - _center(box)[1]) ** 2) ** 0.5)
                if warped is None:
                    compensated.append(float("inf"))
                    continue
                cx, cy = (warped[0] + warped[2]) / 2, (warped[1] + warped[3]) / 2
                compensated.append(((target[0] - cx) ** 2 + (target[1] - cy) ** 2) ** 0.5)
    finite = [v for v in compensated if v != float("inf")]
    return {
        "min_rotation_deg": min_rotation_deg,
        "frame_pairs": frame_pairs,
        "object_pairs": len(uncompensated),
        "warp_behind_camera": len(compensated) - len(finite),
        "center_error_px_pose_homography": quantiles(finite),
        "center_error_px_no_compensation": quantiles(uncompensated),
        "pose_better_than_none_median": (quantiles(finite)["median"] or 0) < (quantiles(uncompensated)["median"] or 0) if finite and uncompensated else None,
    }
