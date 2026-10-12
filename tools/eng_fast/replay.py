"""P2b 序列回放（合同 §3.4、AC-5；AR2-2/AR2-3）。

钉版 `ultralytics 8.4.104` 实装接口：`BYTETracker(args)` / `BOTSORT(args)`，args 取库默认
`bytetrack.yaml` / `botsort.yaml`（与 `trackers/track.py` 同一构造路径，**不传 `frame_rate`**）；
每帧恰好一次 `tracker.update(boxes, img)`；`track_buffer`（= `max_frames_lost`）按**调用帧数**计，
秒数只用于报表。依赖 `lap>=0.5.12`：未装时本模块的库路径直接抛 `LapUnavailable`，
不触发 ultralytics 的自动安装（入口已设 `YOLO_AUTOINSTALL=False`，且导入前先探测 `lap`）。

窗口结局（§3.4，七类互斥，按序判定、命中即止）：(1) `UNBOUND_START`；(2) `CENSORED_END`；
(3) `TRUTH_GAP`；(4) 按时间顺序扫描，最先发生者定结局：`ID_SWITCH` / `LOST_BEYOND_BUFFER` /
`UNRESOLVED_END_MISS` / `KEPT`。(1)–(3) 为排除类，保持率 = `KEPT` / D，
D = `KEPT` + `ID_SWITCH` + `LOST_BEYOND_BUFFER` + `UNRESOLVED_END_MISS`。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import importlib.util
import os
import statistics
from typing import Any, Mapping, Sequence

from tools.eng_fast import common

os.environ.setdefault("YOLO_AUTOINSTALL", "False")

BIND_IOU = 0.30
WINDOWS_S: tuple[float, ...] = (8.0, 13.0)
ALGORITHMS: tuple[str, ...] = ("bytetrack", "botsort")

UNBOUND_START = "UNBOUND_START"
CENSORED_END = "CENSORED_END"
TRUTH_GAP = "TRUTH_GAP"
ID_SWITCH = "ID_SWITCH"
LOST_BEYOND_BUFFER = "LOST_BEYOND_BUFFER"
UNRESOLVED_END_MISS = "UNRESOLVED_END_MISS"
KEPT = "KEPT"
EXCLUDED = (UNBOUND_START, CENSORED_END, TRUTH_GAP)
JUDGED = (KEPT, ID_SWITCH, LOST_BEYOND_BUFFER, UNRESOLVED_END_MISS)
OUTCOMES = EXCLUDED + JUDGED

BOUND_SAME = "BOUND_SAME"
BOUND_OTHER = "BOUND_OTHER"
MISS = "MISS"
INVISIBLE = "INVISIBLE"

NO_BINDING = 0  # b_i = ∅（ByteTrack/BoT-SORT 的 track_id 从 1 起）


class LapUnavailable(RuntimeError):
    """`lap` 未安装：P2b 全部格写 `N/A(LAP_UNAVAILABLE)` 并回用户。"""


class InvalidTimestamps(ValueError):
    """时间戳重复或倒退：该序列 `INVALID_TIMESTAMPS`，不出数。"""


# --- 库适配层（AR2-3 具名）---------------------------------------------------


def require_lap() -> str:
    spec = importlib.util.find_spec("lap")
    if spec is None:
        raise LapUnavailable("LAP_UNAVAILABLE: No module named 'lap'")
    import lap  # noqa: PLC0415

    return str(lap.__version__)


def tracker_args(algorithm: str) -> Any:
    require_lap()
    from ultralytics.utils import IterableSimpleNamespace, YAML  # noqa: PLC0415
    from ultralytics.utils.checks import check_yaml  # noqa: PLC0415

    return IterableSimpleNamespace(**YAML.load(check_yaml(f"{algorithm}.yaml")))


def make_tracker(algorithm: str) -> Any:
    args = tracker_args(algorithm)
    from ultralytics.trackers import BOTSORT, BYTETracker  # noqa: PLC0415

    if algorithm == "bytetrack":
        return BYTETracker(args=args)
    if algorithm == "botsort":
        return BOTSORT(args=args)
    raise ValueError(algorithm)


def as_boxes(dets_norm: Sequence[Sequence[float]], width: int, height: int) -> Any:
    """检测输出（归一化 xywh + score + cls）→ `Boxes(tensor[N,6]=[x1,y1,x2,y2,score,cls], orig_shape).cpu().numpy()`。"""
    import torch  # noqa: PLC0415
    from ultralytics.engine.results import Boxes  # noqa: PLC0415

    rows = [
        [d[0] * width, d[1] * height, (d[0] + d[2]) * width, (d[1] + d[3]) * height, float(d[4]), float(d[5])]
        for d in dets_norm
    ]
    tensor = torch.tensor(rows, dtype=torch.float32) if rows else torch.zeros((0, 6), dtype=torch.float32)
    return Boxes(tensor, orig_shape=(height, width)).cpu().numpy()


def run_sequence(
    tracker: Any, frames: Sequence[tuple[Sequence[Sequence[float]], Any, int, int]]
) -> list[list[list[float]]]:
    """逐帧恰好一次 `update(boxes, img)`；返回每帧输出行 `[x1,y1,x2,y2,track_id,score,cls,idx]`。"""
    outputs: list[list[list[float]]] = []
    for dets, image, width, height in frames:
        image = image() if callable(image) else image  # 允许惰性读帧（长序列不整段驻留内存）
        result = tracker.update(as_boxes(dets, width, height), image)
        outputs.append([[float(v) for v in row] for row in result.tolist()] if len(result) else [])
    if tracker.frame_id != len(frames):
        raise AssertionError(f"tracker.frame_id {tracker.frame_id} ≠ 帧数 {len(frames)}")
    return outputs


def bind(
    truth_boxes: Sequence[Sequence[float] | None], outputs: Sequence[Sequence[Sequence[float]]], width: int, height: int
) -> list[int | None]:
    """b_i：可见帧取与真值框 max IoU ≥ 0.3 的 track ID（并列取 IoU 大者再 ID 小者），无匹配 = 0；不可见 = None。"""
    bindings: list[int | None] = []
    for truth, rows in zip(truth_boxes, outputs):
        if truth is None:
            bindings.append(None)
            continue
        best: tuple[float, int] | None = None
        for row in rows:
            box = (row[0] / width, row[1] / height, (row[2] - row[0]) / width, (row[3] - row[1]) / height)
            value = common.iou_xywh(truth, box)
            if value < BIND_IOU:
                continue
            key = (-value, int(row[4]))
            if best is None or key < best:
                best = key
        bindings.append(NO_BINDING if best is None else best[1])
    return bindings


# --- 窗口结局（纯函数，可合成反例红绿）---------------------------------------


def check_timestamps(times: Sequence[float]) -> None:
    if any(right <= left for left, right in zip(times, times[1:])):
        raise InvalidTimestamps("INVALID_TIMESTAMPS")


def frame_type(binding: int | None, start_id: int) -> str:
    if binding is None:
        return INVISIBLE
    if binding == NO_BINDING:
        return MISS
    return BOUND_SAME if binding == start_id else BOUND_OTHER


def window_outcome(
    times: Sequence[float], bindings: Sequence[int | None], start: int, window_s: float, buffer: int
) -> tuple[str, int]:
    """起点 `start`（须 ∈ V）的结局与漂移回归段长（0 = 无；只在 `LOST_BEYOND_BUFFER` 时可能 > 0）。

    漂移回归段长 = 超出 buffer 的漏检段在以同 ID 结束时的总调用帧数；IR-8：钉版库实测在
    L = buffer + 1 时仍可原 ID 找回（被标记移除的轨迹在下一帧仍参与关联），判定阈值仍按 §3.4
    字面（L ≥ buffer + 1 → `LOST_BEYOND_BUFFER`），这类找回单列子计数。"""
    start_id = bindings[start]
    if start_id is None:
        raise ValueError("起点必须是可见帧")
    if start_id == NO_BINDING:
        return UNBOUND_START, 0
    end_time = times[start] + window_s
    if end_time > times[-1]:
        return CENSORED_END, 0
    window = [j for j in range(start + 1, len(times)) if times[j] <= end_time]
    run = 0
    for j in window:
        run = run + 1 if bindings[j] is None else 0
        if run > buffer:
            return TRUTH_GAP, 0
    miss = 0
    position = start + 1
    last_in_window = window[-1] if window else start
    while position < len(times):
        kind = frame_type(bindings[position], start_id)
        inside = position <= last_in_window
        if not inside and miss == 0:
            break  # 窗口已扫完且无跨末端漏检段
        if kind == BOUND_OTHER:
            return ID_SWITCH, 0
        if kind == BOUND_SAME:
            miss = 0
            if not inside:
                break  # 跨末端漏检段以同 ID 恢复（L ≤ buffer）
        else:
            miss += 1
            if miss == buffer + 1:
                return LOST_BEYOND_BUFFER, _drift_return(bindings, position + 1, start_id, miss)
        position += 1
    if miss > 0 and position >= len(times):
        return UNRESOLVED_END_MISS, 0
    return KEPT, 0


def _drift_return(bindings: Sequence[int | None], position: int, start_id: int, miss: int) -> int:
    """漏检段继续直到下一个绑定帧：以同 ID 结束 → 返回该段总长（漂移回归，只作子计数），否则 0。"""
    while position < len(bindings):
        binding = bindings[position]
        if binding is not None and binding != NO_BINDING:
            return miss if binding == start_id else 0
        miss += 1
        position += 1
    return 0


def window_summary(
    times: Sequence[float],
    bindings: Sequence[int | None],
    window_s: float,
    buffer: int,
    start_bins: Sequence[str] | None = None,
) -> dict[str, Any]:
    """一个（序列, W, 算法）：七类计数、drift_return、保持率与守恒式（总体与逐距离桶）。"""
    visible = [i for i, binding in enumerate(bindings) if binding is not None]
    per_bin: dict[str, Counter] = defaultdict(Counter)
    total: Counter = Counter()
    drift = 0
    drift_at_boundary = 0
    for start in visible:
        outcome, drift_length = window_outcome(times, bindings, start, window_s, buffer)
        total[outcome] += 1
        drift += int(drift_length > 0)
        drift_at_boundary += int(drift_length == buffer + 1)
        per_bin[start_bins[start] if start_bins else "ALL"][outcome] += 1
    result = _counts(total, len(visible))
    result["drift_return"] = drift
    result["drift_return_at_L_eq_buffer_plus_1"] = drift_at_boundary
    result["by_start_distance_bin"] = {
        name: _counts(counter, sum(counter.values())) for name, counter in sorted(per_bin.items())
    }
    return result


def _counts(counter: Counter, visible: int) -> dict[str, Any]:
    judged = sum(counter[name] for name in JUDGED)
    conserved = visible == sum(counter[name] for name in EXCLUDED) + judged
    if not conserved:
        raise AssertionError(f"守恒式不成立：|V| {visible} ≠ 排除 + D {dict(counter)}")
    return {
        "V": visible,
        **{name: int(counter[name]) for name in OUTCOMES},
        "D": judged,
        "retention": round(counter[KEPT] / judged, 6) if judged else None,
        "conserved": conserved,
    }


def sequence_metrics(times: Sequence[float], bindings: Sequence[int | None], buffer: int) -> dict[str, Any]:
    """序列级：ID 切换、碎片、最长同 ID 秒数（允许 ≤ buffer 漏检）、漏检段长分布、帧间隔。"""
    switches = 0
    previous = None
    for binding in bindings:
        if binding is None or binding == NO_BINDING:
            continue
        if previous is not None and binding != previous:
            switches += 1
        previous = binding
    fragments = 0
    in_miss = False
    for binding in bindings:
        if binding is None:
            continue
        if binding == NO_BINDING:
            if not in_miss:
                fragments += 1
            in_miss = True
        else:
            in_miss = False
    segments: list[int] = []
    current = 0
    seen_bound = False
    longest = 0.0
    run_id = None
    run_start = run_last = 0.0
    gap = 0
    for index, binding in enumerate(bindings):
        bound = binding is not None and binding != NO_BINDING
        if bound:
            if seen_bound and current:
                segments.append(current)
            current = 0
            seen_bound = True
            if run_id == binding and gap <= buffer:
                run_last = times[index]
            else:
                run_id, run_start, run_last = binding, times[index], times[index]
            gap = 0
            longest = max(longest, run_last - run_start)
        else:
            current += 1
            gap += 1
    if seen_bound and current:
        segments.append(current)
    intervals = [right - left for left, right in zip(times, times[1:])]
    median_interval = statistics.median(intervals) if intervals else None
    return {
        "frames": len(times),
        "visible_frames": sum(1 for b in bindings if b is not None),
        "bound_frames": sum(1 for b in bindings if b not in (None, NO_BINDING)),
        "id_switches": switches,
        "fragments": fragments,
        "longest_same_id_s": round(longest, 6),
        "miss_segment_lengths": {
            "count": len(segments),
            **common.quantiles(segments),
            "max": max(segments) if segments else None,
            "histogram": dict(sorted(Counter(min(s, buffer + 1) for s in segments).items())),
        },
        "frame_interval_s": common.quantiles(intervals),
        "track_buffer_calls": buffer,
        "track_buffer_median_seconds": round(buffer * median_interval, 6) if median_interval else None,
    }
