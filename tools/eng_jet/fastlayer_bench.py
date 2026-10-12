"""S1/S2 板上快层线束（合同 §2.1 S1/S2、§3.1、AC-2/AC-3）。

冻结 `det-assoc-v1`（权重、规格、关联参数一字不改）只经构造函数注入运行：
`DetAssocTracker(spec_path=config/det-assoc-v1.models.json, model_loader=<载入 .engine 的 ultralytics YOLO>,
device="cuda:0", tracker_factory=<冻结库关联器 + GMC 计时包装>)`。规格文件的 `device_policy` 仍是
`mps→cpu`，因显式传 `device` 不经 `_resolve_device`；`manifest_identity()` 照常报告 `.pt` 的 sha，
引擎身份另记（不改插件身份）。

子命令（板上，`~/eng-jet/code` 为仓库镜像根）：
    export --imgsz 640 | --imgsz 480,640   从 sha 核对过的冻结 `.pt` 导出 TRT FP16 引擎（导出前后核 `.pt` sha）
    s1 --engine E --frames D --count 320 --init-box x y w h --frozen-v F   320 帧逐帧计时 + 检测级比对
    s2 --engine E --frames D --hz 15 --minutes 30 --init-box …              热稳态（每 5 min 一格）
    trtexec --engine E      剥 ultralytics 元数据后 `trtexec --loadEngine` 取 GPU Compute Time
    stack                   实跑栈读数（AC-2 修订 5：torch/TensorRT/CUDA 版本与 venv 构造方式）
    verify                  torch 安装后先验证（提案「needs_user」题 4）：`get_arch_list()` 含 sm_87、CUDA matmul 读回核对、
                            torch 与系统 TensorRT 同进程共存（小网络建引擎并推理）与进程已映射的 CUDA/TRT 库路径
矩形引擎加 `--imgsz-override 480 640`（见 `TimedModel`）。执行栈：板上系统 Python 3.12 的 `--system-site-packages` venv
`~/eng-jet/sysvenv`（复用系统 TensorRT 10.16；torch/torchvision 为官方 cu130 轮子；提案决策记录「S1/S2 系统栈落实（B）」）；
`tegrastats` 另行采集。容器路径（「S1/S2 容器栈落实」）已因 TRT 不支持 SM 87 弃用，代码对两者通用。

纯函数（`compare_frame`、`compare_detections`、`count_drops`、`bin_rows`、`throttle_events`、
`s1_verdict`、`s2_verdict`）不依赖 ultralytics/torch，可在桌面机单测。
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import threading
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

from tools.eng_jet import common

SPEC_PATH = common.PROJECT_ROOT / "config" / "det-assoc-v1.models.json"
LATENCY_GATE_MS = 200.0
REFERENCE_MS = 50.0
BOX_DIFF_LIMIT = 1e-3
COUNT_FRAMES = 50
FRAMES_DEFAULT = 320
S2_BIN_S = 300.0
S2_P95_RATIO = 1.2
S2_30HZ_IF_P95_LE_MS = 33.0
MATCH_IOU = 0.5
IOU_EDGES = (0.0, 0.5, 0.75, 0.9, 0.95, 0.99, 0.999, 1.0000001)
DIFF_EDGES = (0.0, 1e-6, 1e-5, 1e-4, 5e-4, 1e-3, 2e-3, 5e-3, 1e-2, math.inf)
GPU_DEVFREQ = "/sys/class/devfreq/17000000.gpu"


# --- 纯函数：检测级比对 ---------------------------------------------------------


def _iou_xywh(a: Sequence[float], b: Sequence[float]) -> float:
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw, ih = min(ax2, bx2) - max(a[0], b[0]), min(ay2, by2) - max(a[1], b[1])
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


def compare_frame(engine_rows: Sequence[Sequence[float]], reference_rows: Sequence[Sequence[float]]) -> dict[str, Any]:
    """一帧两侧检测行 `[x,y,w,h,conf,cls]`（归一化 top-left xywh）：同类贪心最大 IoU 配对（IoU ≥ 0.5）。

    返回两侧计数、配对数、配对 IoU、配对四坐标最大绝对差（无配对 → 0.0）、两侧未配对行数。"""
    pairs = []
    for i, e in enumerate(engine_rows):
        for j, r in enumerate(reference_rows):
            if int(e[5]) != int(r[5]):
                continue
            iou = _iou_xywh(e, r)
            if iou >= MATCH_IOU:
                pairs.append((iou, i, j))
    pairs.sort(key=lambda p: (-p[0], p[1], p[2]))
    used_e, used_r, matched = set(), set(), []
    for iou, i, j in pairs:
        if i in used_e or j in used_r:
            continue
        used_e.add(i)
        used_r.add(j)
        diff = max(abs(float(engine_rows[i][k]) - float(reference_rows[j][k])) for k in range(4))
        matched.append({"iou": iou, "max_abs_diff": diff, "conf_engine": float(engine_rows[i][4]), "conf_reference": float(reference_rows[j][4])})
    return {
        "n_engine": len(engine_rows),
        "n_reference": len(reference_rows),
        "matched": len(matched),
        "ious": [m["iou"] for m in matched],
        "max_abs_diff": max((m["max_abs_diff"] for m in matched), default=0.0),
        "unmatched_engine": len(engine_rows) - len(used_e),
        "unmatched_reference": len(reference_rows) - len(used_r),
    }


def histogram(values: Iterable[float], edges: Sequence[float]) -> list[dict[str, Any]]:
    values = list(values)
    bins = []
    for low, high in zip(edges, edges[1:]):
        bins.append({"low": low, "high": None if math.isinf(high) else high, "count": sum(1 for v in values if low <= v < high)})
    return bins


def compare_detections(engine: Mapping[int, Sequence[Sequence[float]]], reference: Mapping[int, Sequence[Sequence[float]]],
                       frame_ids: Sequence[int], count_frames: int = COUNT_FRAMES, init_frames: int = 1) -> dict[str, Any]:
    """逐帧比对（AC-2 修订 1 / IR-6 读法）。

    - 计数窗口 = 前 `count_frames` 帧（帧 0…49，沿 G-7 `images[:50]`）：计数不一致帧数；
    - 判门窗口 = 去掉前 `init_frames` 个 init 帧后的帧（1…320，n = 320）：配对框归一化最大差；
    - 未配对：两侧未配对检测在计数窗口 ∪ 判门窗口（即全部比对帧）内一律进不一致清单，任一未配对使一致性分量不通过；
    - init 帧（帧 0）的配对最大差另报，不进判门。"""
    per_frame = []
    for index, frame_id in enumerate(frame_ids):
        row = compare_frame(engine[frame_id], reference[frame_id])
        row["frame_id"] = frame_id
        row["index"] = index
        per_frame.append(row)
    head = per_frame[:count_frames]
    gate = per_frame[init_frames:]
    gate_ious = [iou for r in gate for iou in r["ious"]]
    count_mismatch_head = [r for r in head if r["n_engine"] != r["n_reference"]]
    count_mismatch_all = [r for r in per_frame if r["n_engine"] != r["n_reference"]]
    max_diff = max((r["max_abs_diff"] for r in gate), default=0.0)
    unmatched_engine = sum(r["unmatched_engine"] for r in per_frame)
    unmatched_reference = sum(r["unmatched_reference"] for r in per_frame)
    inconsistent = [
        {"frame_id": r["frame_id"], "n_engine": r["n_engine"], "n_reference": r["n_reference"], "max_abs_diff": r["max_abs_diff"],
         "unmatched_engine": r["unmatched_engine"], "unmatched_reference": r["unmatched_reference"]}
        for r in per_frame
        if r["n_engine"] != r["n_reference"] or r["max_abs_diff"] > BOX_DIFF_LIMIT or r["unmatched_engine"] or r["unmatched_reference"]
    ]
    return {
        "frames_compared": len(per_frame),
        "count_window": {"frame_ids": [head[0]["frame_id"], head[-1]["frame_id"]] if head else [], "n": len(head)},
        "count_frames_window": len(head),
        "count_mismatch_frames_first_window": len(count_mismatch_head),
        "count_mismatch_frames_all": len(count_mismatch_all),
        "gate_window": {"frame_ids": [gate[0]["frame_id"], gate[-1]["frame_id"]] if gate else [], "n": len(gate)},
        "box_max_abs_diff_norm": max_diff,
        "init_frames_box_max_abs_diff_norm": [{"frame_id": r["frame_id"], "max_abs_diff": r["max_abs_diff"]} for r in per_frame[:init_frames]],
        "limit": BOX_DIFF_LIMIT,
        "matched_pairs": len(gate_ious),
        "unmatched_engine_total": unmatched_engine,
        "unmatched_reference_total": unmatched_reference,
        "iou_histogram": histogram(gate_ious, IOU_EDGES),
        "iou_min": min(gate_ious) if gate_ious else None,
        "per_frame_max_diff_histogram": histogram([r["max_abs_diff"] for r in gate], DIFF_EDGES),
        "inconsistent_frames": inconsistent,
    }


def s1_verdict(update_ms: Sequence[float], comparison: Mapping[str, Any]) -> dict[str, Any]:
    """两分量同为 verdict 条件（AR1-2；AC-2 修订 1）：时延 p95 ≤ 200 ms；一致性 = 帧 0…49 计数不一致 0、
    帧 1…320 配对最大差 ≤ 1e-3、且两侧未配对检测 0。"""
    p95 = common.nearest_rank(update_ms, 0.95)
    latency_ok = p95 is not None and p95 <= LATENCY_GATE_MS
    unmatched = int(comparison.get("unmatched_engine_total", 0)) + int(comparison.get("unmatched_reference_total", 0))
    consistency_ok = (comparison["count_mismatch_frames_first_window"] == 0 and comparison["box_max_abs_diff_norm"] <= BOX_DIFF_LIMIT
                      and unmatched == 0)
    if not latency_ok:
        verdict = "STOP(LATENCY_OVER)"
    elif not consistency_ok:
        verdict = "STOP(FP16_BOX_DIVERGENCE)"
    else:
        verdict = "PASS"
    return {
        "latency": {"update_p95_ms": p95, "n": len(update_ms), "gate_ms": LATENCY_GATE_MS, "pass": latency_ok,
                    "within_50ms": p95 is not None and p95 <= REFERENCE_MS},
        "consistency": {"count_mismatch_first_50": comparison["count_mismatch_frames_first_window"],
                        "box_max_abs_diff_norm": comparison["box_max_abs_diff_norm"], "limit": BOX_DIFF_LIMIT,
                        "unmatched_detections": unmatched, "pass": consistency_ok},
        "verdict": verdict,
    }


# --- 纯函数：S2 节拍、分格与降频 ---------------------------------------------------


def due_index(elapsed_s: float, hz: float) -> int:
    """回放节拍：第 k 帧在 t0 + k/hz 到期；返回已到期的最大 k。"""
    return int(math.floor(elapsed_s * hz + 1e-9))


def count_drops(next_index: int, elapsed_s: float, hz: float) -> tuple[int, int]:
    """处理完成于 `elapsed_s`、本应处理 `next_index`：落后于节拍的帧计丢。返回 (下一处理帧号, 丢帧数)。"""
    due = due_index(elapsed_s, hz)
    if due <= next_index:
        return next_index, 0
    return due, due - next_index


def bin_rows(rows: Sequence[Mapping[str, Any]], bin_s: float = S2_BIN_S, duration_s: float | None = None) -> list[dict[str, Any]]:
    """每 `bin_s` 一格：{bin, n, p50, p95, max, dropped}（nearest-rank）。rows 含 t_s、t_update_ms、dropped_before。"""
    if duration_s is None:
        duration_s = max((r["t_s"] for r in rows), default=0.0)
    count = max(1, math.ceil(duration_s / bin_s - 1e-9))
    bins = []
    for index in range(count):
        low, high = index * bin_s, (index + 1) * bin_s
        cell = [r for r in rows if low <= r["t_s"] < high or (index == count - 1 and r["t_s"] >= high)]
        stats = common.summary([r["t_update_ms"] for r in cell])
        bins.append({"bin": index, "t_from_s": low, "t_to_s": high, **stats, "dropped": sum(int(r.get("dropped_before", 0)) for r in cell)})
    return bins


#: 明确对应 CPU/GPU 热限频的 cooling device 类型（AC-3 修订 1 / IR-7）；风扇等其余 cooling device 只报告、不判降频。
CPU_GPU_THROTTLE_COOLING = re.compile(r"^(cpufreq-cpu\d+|devfreq-[0-9a-f]+\.gpu|cpu-throttle-alert|gpu-throttle-alert)$")
FAN_COOLING = re.compile(r"fan", re.IGNORECASE)


def _cooling_type(key: str) -> str:
    return key.split(":", 1)[1] if ":" in key else key


def throttle_events(samples: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """热降频事件（AC-3 修订 1 / IR-7）：GPU devfreq `max_freq` 或任一核 `scaling_max_freq` 低于首样本，或明确对应 CPU/GPU 热限频的
    cooling device（`cpufreq-cpu*`、`devfreq-*.gpu`、`cpu-/gpu-throttle-alert`）`cur_state` 由首样本 0 变非 0。
    DVFS 下 `cur_freq` 随负载变化与风扇等其余 cooling device 的非零状态都不算降频（后者见 `other_cooling_changes`）。"""
    if not samples:
        return []
    first = samples[0]
    events = []
    for sample in samples[1:]:
        for key in ("gpu_max_freq", *sorted(k for k in sample if k.startswith("cpu_max_"))):
            if sample.get(key) is not None and first.get(key) is not None and sample[key] < first[key]:
                events.append({"t_s": sample["t_s"], "key": key, "value": sample[key], "initial": first[key],
                               "temps_mc": sample.get("temps_mc", {})})
        for key, value in sample.get("cooling", {}).items():
            if CPU_GPU_THROTTLE_COOLING.match(_cooling_type(key)) and value and not first.get("cooling", {}).get(key):
                events.append({"t_s": sample["t_s"], "key": f"cooling:{key}", "value": value, "initial": 0,
                               "temps_mc": sample.get("temps_mc", {})})
    return events


def other_cooling_changes(samples: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """非 CPU/GPU 热限频的 cooling device（风扇、soc/cv/hot-surface 告警）状态变化：只报告。风扇以外的告警非零时标为
    `unconfirmed_alerts`（不能确认是否 CPU/GPU 热限频 → S2 不得据此宣称 PASS，交回裁定）。"""
    changes: dict[str, dict[str, Any]] = {}
    for sample in samples:
        for key, value in sample.get("cooling", {}).items():
            if CPU_GPU_THROTTLE_COOLING.match(_cooling_type(key)):
                continue
            cell = changes.setdefault(key, {"max_state": 0, "first_nonzero_t_s": None})
            if value is not None and value > cell["max_state"]:
                cell["max_state"] = value
            if value and cell["first_nonzero_t_s"] is None:
                cell["first_nonzero_t_s"] = sample["t_s"]
    unconfirmed = sorted(k for k, v in changes.items() if v["max_state"] and not FAN_COOLING.search(_cooling_type(k)))
    return {"devices": changes, "unconfirmed_alerts": unconfirmed}


def frequency_evidence_gaps(samples: Sequence[Mapping[str, Any]]) -> list[str]:
    """频率上限读数缺失（None）的键：缺失即不能确认「频率无降频」，S2 不得宣称 PASS。"""
    gaps = set()
    if not samples:
        return ["no_samples"]
    for sample in samples:
        for key in ("gpu_max_freq", *(k for k in sample if k.startswith("cpu_max_"))):
            if sample.get(key) is None:
                gaps.add(key)
    return sorted(gaps)


def s2_verdict(bins: Sequence[Mapping[str, Any]], throttles: Sequence[Any], dropped_total: int,
               unconfirmed: Sequence[str] = (), frequency_gaps: Sequence[str] = ()) -> dict[str, Any]:
    """§2.1 S2 三项合取（AC-3 修订 1）：热降频 → `STOP(THERMAL_THROTTLE)`；丢帧 → `STOP(FRAME_DROP)`；末/首 5 min p95 比值 > 1.2
    → `STOP(LATENCY_OVER)`（预注册时延线未过）。频率证据不能确认时 verdict 留空并列 `ruling_needed`，不宣称 PASS。"""
    first, last = bins[0], bins[-1]
    ratio = (last["p95"] / first["p95"]) if first["p95"] and last["p95"] is not None else None
    ratio_ok = ratio is not None and last["p95"] <= S2_P95_RATIO * first["p95"]
    ruling_needed = [f"unconfirmed_cooling_alert:{k}" for k in unconfirmed] + [f"frequency_reading_missing:{k}" for k in frequency_gaps]
    if throttles:
        verdict: str | None = "STOP(THERMAL_THROTTLE)"
    elif dropped_total:
        verdict = "STOP(FRAME_DROP)"
    elif not ratio_ok:
        verdict = "STOP(LATENCY_OVER)"
    elif ruling_needed:
        verdict = None
    else:
        verdict = "PASS"
    return {"first_p95_ms": first["p95"], "last_p95_ms": last["p95"], "p95_ratio": None if ratio is None else round(ratio, 4),
            "ratio_limit": S2_P95_RATIO, "ratio_ok": ratio_ok, "throttle_events": len(throttles), "dropped_total": dropped_total,
            "ruling_needed": ruling_needed, "verdict": verdict}


# --- 板上运行件（需 ultralytics/torch；桌面机单测只走注入的假件）----------------------------


class Timed:
    """包装可调用对象并累计每次调用耗时（ms）；`pop()` 取出并清零。"""

    def __init__(self, fn: Callable[..., Any]):
        self.fn = fn
        self.calls: list[float] = []

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        try:
            return self.fn(*args, **kwargs)
        finally:
            self.calls.append((time.perf_counter() - started) * 1000.0)

    def pop(self) -> float:
        total = sum(self.calls)
        self.calls.clear()
        return total


class TimedModel:
    """引擎模型包装：`predict` 计时，其余属性透传。

    `imgsz_override`（仅矩形引擎）：ultralytics 静态引擎只接受导出时的输入形状，而插件每次按冻结规格传 `imgsz=640`
    （第二次起会覆盖引擎元数据里的形状）；矩形引擎因此在线束层把 `imgsz` 改写为引擎导出形状（如 `[480, 640]`），
    规格文件与插件代码不改，改写值记入证据。方形引擎不改写。"""

    def __init__(self, model: Any, imgsz_override: Sequence[int] | None = None):
        self._model = model
        self.imgsz_override = list(imgsz_override) if imgsz_override else None

        def predict(*args: Any, **kwargs: Any) -> Any:
            if self.imgsz_override is not None and "imgsz" in kwargs:
                kwargs["imgsz"] = list(self.imgsz_override)
            return model.predict(*args, **kwargs)

        self.predict = Timed(predict)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._model, name)


def timed_tracker_factory(base_factory: Callable[[str, Mapping[str, Any]], Any], sink: dict[str, Timed]) -> Callable[[str, Mapping[str, Any]], Any]:
    """冻结库关联器（不改参数）+ GMC 计时：包装实例的 `gmc.apply` 与 `update`。"""

    def factory(algorithm: str, args: Mapping[str, Any]) -> Any:
        tracker = base_factory(algorithm, args)
        gmc = getattr(tracker, "gmc", None)
        if gmc is not None and hasattr(gmc, "apply"):
            sink["gmc"] = Timed(gmc.apply)
            gmc.apply = sink["gmc"]
        sink["assoc"] = Timed(tracker.update)
        tracker.update = sink["assoc"]
        return tracker

    return factory


def make_plugin(engine_path: Path, device: str, sink: dict[str, Any], spec_path: Path = SPEC_PATH,
                yolo_factory: Callable[..., Any] | None = None, base_tracker_factory: Callable[..., Any] | None = None,
                imgsz_override: Sequence[int] | None = None) -> Any:
    from controller.det_assoc_tracker import DetAssocTracker, _default_tracker_factory  # noqa: PLC0415

    def loader(weights_path: Path) -> Any:
        if yolo_factory is None:
            from ultralytics import YOLO  # noqa: PLC0415

            model = YOLO(str(engine_path), task="detect")
        else:
            model = yolo_factory(engine_path)
        sink["model"] = TimedModel(model, imgsz_override)
        return sink["model"]

    return DetAssocTracker(spec_path=spec_path, device=device, model_loader=loader,
                           tracker_factory=timed_tracker_factory(base_tracker_factory or _default_tracker_factory, sink))


def detection_rows(model: Any, image: Any, imgsz: Any, conf: float, iou: float, device: str) -> list[list[float]]:
    """与冻结缓存同口径（`tools/eng_det/evaluate.Detector.detect_image`）：裁剪到画幅、归一化 xywh、7/6 位舍入。"""
    height, width = image.shape[:2]
    results = model.predict(source=image, imgsz=imgsz, conf=conf, iou=iou, device=device, verbose=False)
    boxes = results[0].boxes
    rows = []
    for (x1, y1, x2, y2), score, label in zip(boxes.xyxy.cpu().tolist(), boxes.conf.cpu().tolist(), boxes.cls.cpu().tolist()):
        left, top = max(0.0, x1 / width), max(0.0, y1 / height)
        right, bottom = min(1.0, x2 / width), min(1.0, y2 / height)
        if right <= left or bottom <= top or not math.isfinite(score):
            continue
        rows.append([round(left, 7), round(top, 7), round(right - left, 7), round(bottom - top, 7), round(float(score), 6), float(int(label))])
    return rows


def load_frozen_v(path: Path, frame_rel_prefix: str, frame_ids: Sequence[int]) -> dict[int, list[list[float]]]:
    import gzip  # noqa: PLC0415

    wanted = {f"{frame_rel_prefix}/{common.frame_name(i, 'jpg')}": i for i in frame_ids}
    out: dict[int, list[list[float]]] = {}
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        header = json.loads(handle.readline())
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row["frame_id"] in wanted:
                out[wanted[row["frame_id"]]] = row["dets"]
    missing = [i for i in frame_ids if i not in out]
    if missing:
        raise ValueError(f"frozen-V 缺帧 {missing[:5]}…")
    out_header = header.get("header", header)
    out[-1] = out_header  # type: ignore[assignment]
    return out


def venv_construction(prefix: str | None = None, base_prefix: str | None = None) -> dict[str, Any]:
    """AC-2 修订 5：venv 构造方式（`sys.prefix`/`sys.base_prefix` 与 `pyvenv.cfg` 原文）。"""
    prefix = prefix if prefix is not None else sys.prefix
    base_prefix = base_prefix if base_prefix is not None else sys.base_prefix
    cfg_path = Path(prefix) / "pyvenv.cfg"
    cfg: dict[str, str] = {}
    if cfg_path.is_file():
        for line in cfg_path.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep:
                cfg[key.strip()] = value.strip()
    return {"sys_prefix": prefix, "sys_base_prefix": base_prefix, "is_venv": prefix != base_prefix, "pyvenv_cfg": cfg,
            "system_site_packages": cfg.get("include-system-site-packages", "").lower() == "true"}


def runtime_stack() -> dict[str, Any]:
    """AC-2 修订 2/5：实跑读数（`torch.__version__`、`tensorrt.__version__`、CUDA 版本、venv 构造方式或镜像 tag 环境变量）。"""
    import platform  # noqa: PLC0415

    stack: dict[str, Any] = {"python": platform.python_version(), "machine": platform.machine(), "in_container": Path("/.dockerenv").exists(),
                             "venv": venv_construction(), "ld_library_path": os.environ.get("LD_LIBRARY_PATH"),
                             "image_env": {k: os.environ.get(k) for k in ("NVIDIA_PYTORCH_VERSION", "PYTORCH_VERSION", "CUDA_VERSION",
                                                                           "TRT_VERSION", "ENG_JET_IMAGE")}}
    files: dict[str, str | None] = {}
    for name in ("torch", "torchvision", "tensorrt", "ultralytics", "cv2", "numpy", "lap", "onnx"):
        try:
            module = __import__(name)
            stack[name] = getattr(module, "__version__", "?")
            files[name] = getattr(module, "__file__", None)
        except Exception as exception:  # noqa: BLE001
            stack[name] = f"unavailable:{type(exception).__name__}"
    stack["module_files"] = files
    try:
        import torch  # noqa: PLC0415

        stack["torch_cuda"] = torch.version.cuda
        stack["cuda_available"] = bool(torch.cuda.is_available())
        stack["cuda_device"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        stack["cuda_capability"] = list(torch.cuda.get_device_capability(0)) if torch.cuda.is_available() else None
        stack["cuda_arch_list"] = list(torch.cuda.get_arch_list())
        stack["cudnn"] = torch.backends.cudnn.version()
    except Exception as exception:  # noqa: BLE001
        stack["torch_cuda"] = f"unavailable:{type(exception).__name__}"
    return stack


# --- torch 安装后先验证（提案「needs_user」题 4 CLARIFY-B2；SM 87 与系统 TensorRT 共存）---------------------------

#: 进程已映射的 CUDA/TensorRT 相关库（共存核对点 (ii)：torch 取 venv 内 pip 库，TensorRT 取系统库）。
LIB_PATTERN = re.compile(r"/(libcudart|libcublasLt|libcublas|libnvinfer[^/]*|libcudnn[^/]*|libnvrtc[^/]*|libnvJitLink|libcuda|libcudss|"
                         r"libcusparse|libcufft|libcurand|libnccl|libnvToolsExt|libcupti)\.so[^/]*$")


def loaded_libraries(maps_text: str) -> list[str]:
    """`/proc/<pid>/maps` 原文 → 已映射的 CUDA/TRT 相关共享库路径（去重、排序）。"""
    found = set()
    for line in maps_text.splitlines():
        parts = line.split()
        if len(parts) >= 6 and LIB_PATTERN.search(parts[-1]):
            found.add(parts[-1])
    return sorted(found)


def library_origins(paths: Sequence[str], venv_prefix: str) -> dict[str, list[str]]:
    """按来源分组：venv 内 pip 轮子（`site-packages/nvidia/*`、`torch/lib`）与系统库（其余）。"""
    venv_prefix = venv_prefix.rstrip("/") + "/"
    venv = [p for p in paths if p.startswith(venv_prefix)]
    return {"venv": venv, "system": [p for p in paths if not p.startswith(venv_prefix)]}


def verify_summary(arch_list: Sequence[str], matmul: Mapping[str, Any], trt_in_torch: Mapping[str, Any],
                   trt_only: Mapping[str, Any] | None) -> dict[str, Any]:
    """题 4 的先验证判据：`get_arch_list()` 含 `sm_87`、CUDA matmul 读回核对通过（`is_available()` 为 True 不算通过）、
    torch 与系统 TensorRT 同进程建引擎并推理一致、不带 torch 的干净进程 TensorRT 建引擎通过。任一不过 → 不跑 S1/S2。"""
    checks = {
        "sm_87_in_arch_list": "sm_87" in list(arch_list),
        "cuda_matmul_readback": bool(matmul.get("ok")),
        "trt_with_torch_same_process": bool(trt_in_torch.get("ok")),
        "trt_clean_process_without_torch": bool(trt_only.get("ok")) if trt_only is not None else False,
    }
    return {"checks": checks, "pass": all(checks.values()), "failed": [k for k, v in checks.items() if not v]}


def cuda_matmul_smoke(n: int = 512) -> dict[str, Any]:
    """GPU 张量相乘并读回 CPU 核对：fp32 对 fp64 CPU 参照的相对最大差 ≤ 1e-3、fp16 ≤ 2e-2、全 1 矩阵乘积逐元素 == n（整数精确）。"""
    import torch  # noqa: PLC0415

    generator = torch.Generator().manual_seed(0)
    a = torch.randn(n, n, generator=generator, dtype=torch.float32)
    b = torch.randn(n, n, generator=generator, dtype=torch.float32)
    reference = a.double() @ b.double()
    scale = reference.abs().max().item()
    started = time.perf_counter()
    out32 = (a.cuda() @ b.cuda())
    out16 = (a.half().cuda() @ b.half().cuda())
    ones = torch.ones(n, n, device="cuda") @ torch.ones(n, n, device="cuda")
    torch.cuda.synchronize()
    wall_ms = (time.perf_counter() - started) * 1000.0
    rel32 = ((out32.cpu().double() - reference).abs().max().item()) / scale
    rel16 = ((out16.float().cpu().double() - reference).abs().max().item()) / scale
    exact = bool((ones.cpu() == float(n)).all().item())
    ok = math.isfinite(rel32) and rel32 <= 1e-3 and math.isfinite(rel16) and rel16 <= 2e-2 and exact
    return {"n": n, "fp32_rel_max_diff": rel32, "fp16_rel_max_diff": rel16, "ones_exact": exact, "wall_ms": round(wall_ms, 3),
            "tf32_allowed": bool(torch.backends.cuda.matmul.allow_tf32), "limits": {"fp32": 1e-3, "fp16": 2e-2}, "ok": ok}


def _tiny_trt_engine(trt: Any) -> tuple[Any, Any]:
    """小网络：y = x + x（FP16 标志），返回 (logger, 序列化引擎)。"""
    logger = trt.Logger(trt.Logger.WARNING)
    builder = trt.Builder(logger)
    network = builder.create_network(0)
    x = network.add_input("x", trt.float32, (1, 16, 8, 8))
    layer = network.add_elementwise(x, x, trt.ElementWiseOperation.SUM)
    layer.get_output(0).name = "y"
    network.mark_output(layer.get_output(0))
    config = builder.create_builder_config()
    config.set_flag(trt.BuilderFlag.FP16)
    return logger, builder.build_serialized_network(network, config)


def trt_smoke_with_torch() -> dict[str, Any]:
    """先 import torch 并初始化 CUDA，再在同进程用系统 TensorRT 建小引擎、以 torch 张量作 I/O 推理并核对。"""
    import tensorrt as trt  # noqa: PLC0415
    import torch  # noqa: PLC0415

    torch.cuda.init()
    started = time.perf_counter()
    logger, serialized = _tiny_trt_engine(trt)
    if serialized is None:
        return {"ok": False, "error": "build_serialized_network returned None", "tensorrt": trt.__version__}
    engine = trt.Runtime(logger).deserialize_cuda_engine(serialized)
    context = engine.create_execution_context()
    x = torch.randn(1, 16, 8, 8, device="cuda")
    y = torch.empty_like(x)
    context.set_tensor_address("x", x.data_ptr())
    context.set_tensor_address("y", y.data_ptr())
    stream = torch.cuda.current_stream()
    executed = bool(context.execute_async_v3(stream.cuda_stream))
    stream.synchronize()
    diff = (y - 2 * x).abs().max().item()
    return {"ok": executed and math.isfinite(diff) and diff <= 1e-2, "executed": executed, "max_abs_diff": diff,
            "tensorrt": trt.__version__, "tensorrt_file": trt.__file__, "serialized_bytes": serialized.nbytes,
            "wall_ms": round((time.perf_counter() - started) * 1000.0, 3)}


def trt_smoke_without_torch() -> dict[str, Any]:
    """干净进程（不 import torch）：系统 TensorRT 建同一小引擎并反序列化；进程已映射库另记。"""
    import tensorrt as trt  # noqa: PLC0415

    started = time.perf_counter()
    logger, serialized = _tiny_trt_engine(trt)
    ok = serialized is not None and trt.Runtime(logger).deserialize_cuda_engine(serialized) is not None
    return {"ok": ok, "tensorrt": trt.__version__, "tensorrt_file": trt.__file__, "torch_imported": "torch" in sys.modules,
            "libraries": loaded_libraries(Path("/proc/self/maps").read_text()), "wall_ms": round((time.perf_counter() - started) * 1000.0, 3)}


def torch_verify(trt_only: Mapping[str, Any] | None = None) -> dict[str, Any]:
    import torch  # noqa: PLC0415

    record: dict[str, Any] = {"ld_library_path": os.environ.get("LD_LIBRARY_PATH"), "torch": torch.__version__, "torch_cuda": torch.version.cuda,
                              "cuda_is_available": bool(torch.cuda.is_available()), "cuda_is_available_note": "不作通过依据（题 4）"}
    record["arch_list"] = list(torch.cuda.get_arch_list())
    try:
        record["device"] = torch.cuda.get_device_name(0)
        record["capability"] = list(torch.cuda.get_device_capability(0))
    except Exception as exception:  # noqa: BLE001
        record["device_error"] = f"{type(exception).__name__}: {exception}"
    try:
        record["matmul"] = cuda_matmul_smoke()
    except Exception as exception:  # noqa: BLE001
        record["matmul"] = {"ok": False, "error": f"{type(exception).__name__}: {exception}"}
    try:
        record["trt_with_torch"] = trt_smoke_with_torch()
    except Exception as exception:  # noqa: BLE001
        record["trt_with_torch"] = {"ok": False, "error": f"{type(exception).__name__}: {exception}"}
    libraries = loaded_libraries(Path("/proc/self/maps").read_text())
    record["libraries_torch_trt_process"] = library_origins(libraries, sys.prefix)
    record["trt_clean_process"] = dict(trt_only) if trt_only is not None else None
    record["summary"] = verify_summary(record["arch_list"], record["matmul"], record["trt_with_torch"], trt_only)
    record["runtime_stack"] = runtime_stack()
    return record


class Sampler(threading.Thread):
    """每秒读一次 sysfs 频率上限/当前值、温度与 cooling device（非 root 只读）。"""

    def __init__(self, t0: float, period_s: float = 1.0):
        super().__init__(daemon=True)
        self.t0, self.period_s, self.samples, self._halt = t0, period_s, [], threading.Event()

    @staticmethod
    def _read(path: str) -> int | None:
        try:
            return int(Path(path).read_text().split()[0])
        except (OSError, ValueError, IndexError):
            return None

    def snapshot(self) -> dict[str, Any]:
        sample: dict[str, Any] = {"t_s": round(time.perf_counter() - self.t0, 3), "unix": round(time.time(), 3),
                                  "gpu_max_freq": self._read(f"{GPU_DEVFREQ}/max_freq"), "gpu_cur_freq": self._read(f"{GPU_DEVFREQ}/cur_freq")}
        for cpu in sorted(Path("/sys/devices/system/cpu").glob("cpu[0-9]*")):
            sample[f"cpu_max_{cpu.name}"] = self._read(f"{cpu}/cpufreq/scaling_max_freq")
            sample[f"cpu_cur_{cpu.name}"] = self._read(f"{cpu}/cpufreq/scaling_cur_freq")
        sample["temps_mc"] = {}
        for zone in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
            try:
                sample["temps_mc"][(zone / "type").read_text().strip()] = self._read(str(zone / "temp"))
            except OSError:
                continue
        sample["cooling"] = {}
        for device in sorted(Path("/sys/class/thermal").glob("cooling_device*")):
            try:
                sample["cooling"][f"{device.name}:{(device / 'type').read_text().strip()}"] = self._read(str(device / "cur_state"))
            except OSError:
                continue
        return sample

    def run(self) -> None:
        while not self._halt.is_set():
            self.samples.append(self.snapshot())
            self._halt.wait(self.period_s)

    def stop(self) -> list[dict[str, Any]]:
        self._halt.set()
        self.join(timeout=5)
        return self.samples


def rss_mb() -> float | None:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024.0
    except OSError:
        return None
    return None


def read_frames(frames_dir: Path, frame_ids: Sequence[int]) -> list[Any]:
    import cv2  # noqa: PLC0415

    images = []
    for frame_id in frame_ids:
        image = cv2.imread(str(frames_dir / common.frame_name(frame_id, "jpg")), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"无法读取帧 {frame_id}")
        images.append(image)
    return images


def run_s1(engine: Path, frames_dir: Path, count: int, init_box: Sequence[float], frozen_v: Path, out_dir: Path,
           device: str = "cuda:0", frame_rel_prefix: str = common.A7_FRAMES_REL, imgsz_override: Sequence[int] | None = None) -> dict[str, Any]:
    """init 于帧 0，计时帧 1..count 的 `update`（n = count）；随后在同一引擎上逐帧检测 0..count 与 frozen-V 比对（IR-6）。"""
    spec = common.read_json(SPEC_PATH)
    frame_ids = list(range(count + 1))
    images = read_frames(frames_dir, frame_ids)
    sink: dict[str, Any] = {}
    started_unix = time.time()
    plugin = make_plugin(engine, device, sink, imgsz_override=imgsz_override)
    usage0, wall0 = resource.getrusage(resource.RUSAGE_SELF), time.perf_counter()
    init_started = time.perf_counter()
    if not plugin.init(images[0], init_box):
        return {"verdict": "INIT_REJECTED"}
    t_init = (time.perf_counter() - init_started) * 1000.0
    sink["model"].predict.pop()
    if "gmc" in sink:
        sink["gmc"].pop()
    sink["assoc"].pop()
    rows = []
    for frame_id, image in zip(frame_ids[1:], images[1:]):
        started = time.perf_counter()
        result = plugin.update(image)
        t_update = (time.perf_counter() - started) * 1000.0
        t_detect = sink["model"].predict.pop()
        t_gmc = sink["gmc"].pop() if "gmc" in sink else None
        t_assoc_total = sink["assoc"].pop()
        rows.append({"frame_id": frame_id, "plugin_state": "ok" if result.ok else "lost",
                     "box": list(result.box_norm) if result.box_norm else None, "reason": result.reason,
                     "t_update_ms": round(t_update, 4), "t_detect_ms": round(t_detect, 4),
                     "t_gmc_ms": None if t_gmc is None else round(t_gmc, 4),
                     "t_assoc_ms": round(t_assoc_total - (t_gmc or 0.0), 4)})
    usage1, wall1 = resource.getrusage(resource.RUSAGE_SELF), time.perf_counter()
    rss_after_updates = rss_mb()
    cpu_s = (usage1.ru_utime - usage0.ru_utime) + (usage1.ru_stime - usage0.ru_stime)
    imgsz: Any = list(imgsz_override) if imgsz_override else int(spec["imgsz"])
    detections = {fid: detection_rows(sink["model"]._model, img, imgsz, float(spec["conf"]), float(spec["nms_iou"]), device)
                  for fid, img in zip(frame_ids, images)}
    reference = load_frozen_v(frozen_v, frame_rel_prefix, frame_ids)
    header = reference.pop(-1)
    comparison = compare_detections(detections, reference, frame_ids)
    raw = out_dir / f"s1-{engine.stem}-frames.json"
    common.write_json(raw, {"rows": rows, "detections": {str(k): v for k, v in detections.items()}})
    timing = {key: common.summary([r[key] for r in rows if r[key] is not None], 4) for key in ("t_update_ms", "t_detect_ms", "t_gmc_ms", "t_assoc_ms")}
    return {
        "engine": common.rel_project(engine),
        "engine_sha256": common.sha256_file(engine),
        "imgsz_passed_to_predict": imgsz,
        "imgsz_override": list(imgsz_override) if imgsz_override else None,
        "manifest_identity": dict(plugin.manifest_identity()),
        "runtime_stack": runtime_stack(),
        "init": {"frame_id": 0, "box_norm": list(init_box), "t_init_ms": round(t_init, 4)},
        "frames": {"update_frame_ids": [frame_ids[1], frame_ids[-1]], "n_update": len(rows)},
        "frozen_v_header": header,
        "timing": timing,
        "plugin_state_counts": {state: sum(1 for r in rows if r["plugin_state"] == state) for state in ("ok", "lost")},
        "cpu_occupancy_pct": round(100.0 * cpu_s / (wall1 - wall0), 2),
        "cpu_occupancy_basis": "进程 user+sys CPU 秒 / init+320 帧 update 墙钟（100% = 一个核）",
        "rss_mb_after_updates": rss_after_updates,
        "ru_maxrss_mb": round(usage1.ru_maxrss / 1024.0, 2),
        "started_unix": round(started_unix, 3),
        "finished_unix": round(time.time(), 3),
        "raw_frames_file": raw.name,
        "raw_frames_sha256": common.sha256_file(raw),
        "comparison": comparison,
        "verdict": s1_verdict([r["t_update_ms"] for r in rows], comparison),
    }


def run_s2(engine: Path, frames_dir: Path, count: int, init_box: Sequence[float], hz: float, minutes: float, out_dir: Path,
           device: str = "cuda:0", imgsz_override: Sequence[int] | None = None) -> dict[str, Any]:
    """按 `hz` 节拍循环回放帧 0..count（每轮帧 0 重新 init，帧 1..count update），持续 `minutes`；每 5 min 一格。"""
    frame_ids = list(range(count + 1))
    images = read_frames(frames_dir, frame_ids)
    sink: dict[str, Any] = {}
    plugin = make_plugin(engine, device, sink, imgsz_override=imgsz_override)
    duration = minutes * 60.0
    t0 = time.perf_counter()
    t0_unix = time.time()
    sampler = Sampler(t0)
    sampler.start()
    rows, inits = [], []
    next_index, cycle_len = 0, len(frame_ids)
    while True:
        due_t = next_index / hz
        now = time.perf_counter() - t0
        if due_t >= duration:
            break
        if now < due_t:
            time.sleep(due_t - now)
        position = next_index % cycle_len
        started = time.perf_counter()
        if position == 0:
            ok = plugin.init(images[0], init_box)
            inits.append({"t_s": round(started - t0, 4), "t_init_ms": round((time.perf_counter() - started) * 1000.0, 4), "ok": bool(ok)})
        else:
            plugin.update(images[position])
            rows.append({"t_s": round(started - t0, 4), "t_update_ms": round((time.perf_counter() - started) * 1000.0, 4), "dropped_before": 0})
        for timer in ("model", "gmc", "assoc"):
            if timer in sink:
                (sink[timer].predict if timer == "model" else sink[timer]).pop()
        upcoming, dropped = count_drops(next_index + 1, time.perf_counter() - t0, hz)
        if dropped and rows:
            rows[-1]["dropped_after"] = dropped
        if dropped:
            rows.append({"t_s": round(time.perf_counter() - t0, 4), "t_update_ms": None, "dropped_before": dropped, "marker": True})
        next_index = upcoming
    samples = sampler.stop()
    timed = [r for r in rows if not r.get("marker")]
    dropped_total = sum(r["dropped_before"] for r in rows)
    bins = bin_rows(timed, duration_s=duration)
    for cell in bins:
        cell["dropped"] = sum(r["dropped_before"] for r in rows if cell["t_from_s"] <= r["t_s"] < cell["t_to_s"])
        window = [s for s in samples if cell["t_from_s"] <= s["t_s"] < cell["t_to_s"]]
        cell["samples"] = len(window)
        cell["gpu_cur_freq_hz"] = common.summary([s["gpu_cur_freq"] for s in window if s["gpu_cur_freq"]], 0)
        cell["gpu_max_freq_hz_min"] = min((s["gpu_max_freq"] for s in window if s["gpu_max_freq"]), default=None)
        cpu_max = [v for s in window for k, v in s.items() if k.startswith("cpu_max_") and v]
        cell["cpu_max_freq_khz_min"] = min(cpu_max, default=None)
        cpu_cur = [v for s in window for k, v in s.items() if k.startswith("cpu_cur_") and v]
        cell["cpu_cur_freq_khz"] = common.summary(cpu_cur, 0)
        cell["temps_c_max"] = {k: max((s["temps_mc"].get(k) or -1) for s in window) / 1000.0 for k in (window[0]["temps_mc"] if window else {})}
    throttles = throttle_events(samples)
    others = other_cooling_changes(samples)
    gaps = frequency_evidence_gaps(samples)
    raw = out_dir / f"s2-{engine.stem}-{int(hz)}hz.json"
    common.write_json(raw, {"rows": rows, "inits": inits, "samples": samples})
    return {"engine": common.rel_project(engine), "engine_sha256": common.sha256_file(engine), "hz": hz, "minutes": minutes,
            "imgsz_override": list(imgsz_override) if imgsz_override else None, "runtime_stack": runtime_stack(),
            "t0_unix": round(t0_unix, 3), "finished_unix": round(time.time(), 3), "updates": len(timed), "inits": len(inits),
            "inits_rejected": sum(1 for i in inits if not i["ok"]), "bins": bins, "samples": len(samples),
            "throttle_events": throttles[:50], "other_cooling_changes": others, "frequency_evidence_gaps": gaps,
            "raw_file": raw.name, "raw_sha256": common.sha256_file(raw),
            "verdict": s2_verdict(bins, throttles, dropped_total, others["unconfirmed_alerts"], gaps)}


def export_engine(imgsz: Sequence[int] | int, out_dir: Path) -> dict[str, Any]:
    """从冻结 `.pt` 导出 TRT FP16（`half=True`、`dynamic=False`）；导出前后核 `.pt` sha 与规格一致。"""
    from ultralytics import YOLO  # noqa: PLC0415

    spec = common.read_json(SPEC_PATH)
    weights = common.PROJECT_ROOT / spec["weights"]["path"]
    before = common.sha256_file(weights)
    if before != spec["weights"]["sha256"]:
        raise ValueError("冻结 .pt sha 与规格不符（导出前）")
    started = time.perf_counter()
    started_unix = time.time()
    args = {"format": "engine", "half": True, "imgsz": imgsz, "dynamic": False, "device": 0, "workspace": None, "simplify": False}
    produced = Path(YOLO(str(weights)).export(**args))
    wall = time.perf_counter() - started
    after = common.sha256_file(weights)
    if after != before:
        raise ValueError("冻结 .pt sha 在导出后改变")
    tag = "640" if isinstance(imgsz, int) else "x".join(str(v) for v in imgsz)
    target = out_dir / f"det-assoc-v1-fp16-{tag}.engine"
    target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(produced, target)
    onnx_src = produced.with_suffix(".onnx")
    onnx_info = None
    if onnx_src.exists():
        onnx_dst = out_dir / f"det-assoc-v1-{tag}.onnx"
        os.replace(onnx_src, onnx_dst)
        onnx_info = {"path": common.rel_project(onnx_dst), "sha256": common.sha256_file(onnx_dst), "size_bytes": onnx_dst.stat().st_size}
    import tensorrt  # noqa: PLC0415

    return {"engine": common.rel_project(target), "sha256": common.sha256_file(target), "size_bytes": target.stat().st_size,
            "export_args": args, "tensorrt_version": tensorrt.__version__, "runtime_stack": runtime_stack(), "onnx": onnx_info,
            "pt_sha256_before": before, "pt_sha256_after": after, "started_unix": round(started_unix, 3), "wall_s": round(wall, 1)}


def strip_ultralytics_metadata(engine: Path, plan: Path) -> dict[str, Any]:
    """ultralytics 引擎 = 4 字节小端元数据长度 + 元数据 JSON + TRT 序列化引擎；剥出纯 plan 供 `trtexec --loadEngine`。"""
    data = engine.read_bytes()
    length = int.from_bytes(data[:4], "little")
    meta = json.loads(data[4 : 4 + length].decode("utf-8"))
    plan.write_bytes(data[4 + length :])
    return {"plan": common.rel_project(plan), "plan_sha256": common.sha256_file(plan), "metadata": meta}


TRTEXEC_LINE = re.compile(r"(GPU Compute Time|Latency|Enqueue Time|H2D Latency|D2H Latency|Throughput):\s*(.*)$")


def parse_trtexec(text: str) -> dict[str, Any]:
    """`trtexec` 性能摘要行 → {名称: {min, max, mean, median, percentile(90%)…}}（ms；Throughput 为 qps）。"""
    out: dict[str, Any] = {}
    for line in text.splitlines():
        match = TRTEXEC_LINE.search(line)
        if not match:
            continue
        name, body = match.group(1), match.group(2)
        if name == "Throughput":
            number = re.match(r"([0-9.]+)", body)
            out[name] = float(number.group(1)) if number else body
            continue
        stats = {}
        for key, value in re.findall(r"([a-zA-Z]+(?:\(\d+%\))?)\s*=\s*([0-9.]+)\s*ms", body):
            stats[key] = float(value)
        if stats:
            out[name] = stats
    version = re.search(r"TensorRT version:\s*([0-9.]+)|\[TensorRT v(\d+)\]", text)
    if version:
        out["tensorrt_version_line"] = version.group(0)
    return out


def run_trtexec(engine: Path, out_dir: Path, trtexec: str = common.SYSTEM_TRTEXEC, duration_s: int = 10) -> dict[str, Any]:
    plan = out_dir / f"{engine.stem}.plan"
    stripped = strip_ultralytics_metadata(engine, plan)
    command = [trtexec, f"--loadEngine={plan}", "--warmUp=1000", f"--duration={duration_s}", "--iterations=100", "--avgRuns=100"]
    started = time.time()
    completed = subprocess.run(command, capture_output=True, text=True)
    log = out_dir / f"trtexec-{engine.stem}.log"
    log.write_text(completed.stdout + "\n--- stderr ---\n" + completed.stderr, encoding="utf-8")
    return {"engine": common.rel_project(engine), "engine_sha256": common.sha256_file(engine), **stripped, "command": " ".join(command),
            "returncode": completed.returncode, "log": log.name, "log_sha256": common.sha256_file(log), "started_unix": round(started, 3),
            "parsed": parse_trtexec(completed.stdout)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    exp = sub.add_parser("export")
    exp.add_argument("--imgsz", required=True)
    trt = sub.add_parser("trtexec")
    trt.add_argument("--engine", type=Path, required=True)
    trt.add_argument("--trtexec", default=common.SYSTEM_TRTEXEC)
    sub.add_parser("stack")
    ver = sub.add_parser("verify")
    ver.add_argument("--trt-only", action="store_true", help="干净进程：不 import torch，只做系统 TensorRT 小引擎")
    for name in ("s1", "s2"):
        p = sub.add_parser(name)
        p.add_argument("--engine", type=Path, required=True)
        p.add_argument("--frames", type=Path, required=True)
        p.add_argument("--count", type=int, default=FRAMES_DEFAULT)
        p.add_argument("--init-box", type=float, nargs=4, required=True)
        p.add_argument("--device", default="cuda:0")
        p.add_argument("--imgsz-override", type=int, nargs=2, default=None, metavar=("H", "W"))
        if name == "s1":
            p.add_argument("--frozen-v", type=Path, required=True)
        else:
            p.add_argument("--hz", type=float, default=15.0)
            p.add_argument("--minutes", type=float, default=30.0)
    parser.add_argument("--out", type=Path, default=Path(os.path.expanduser(f"{common.BOARD_ROOT}/results")))
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.action == "export":
        size = [int(v) for v in args.imgsz.split(",")]
        result = export_engine(size[0] if len(size) == 1 else size, args.out / "engines")
        name = f"export-{'x'.join(str(v) for v in size)}"
    elif args.action == "trtexec":
        result = run_trtexec(args.engine, args.out, trtexec=args.trtexec)
        name = f"trtexec-{args.engine.stem}"
    elif args.action == "verify" and args.trt_only:
        result = trt_smoke_without_torch()
        name = "verify-trt-only"
    elif args.action == "verify":
        env = {k: v for k, v in os.environ.items() if k != "LD_LIBRARY_PATH"}
        child = subprocess.run([sys.executable, "-m", "tools.eng_jet.fastlayer_bench", "--out", str(args.out), "verify", "--trt-only"],
                               capture_output=True, text=True, env=env, cwd=str(common.PROJECT_ROOT))
        trt_only_path = args.out / "verify-trt-only-summary.json"
        trt_only = common.read_json(trt_only_path) if child.returncode == 0 and trt_only_path.is_file() else \
            {"ok": False, "returncode": child.returncode, "stderr_tail": child.stderr[-2000:]}
        result = torch_verify(trt_only)
        result["verdict"] = result["summary"]
        name = "verify"
    elif args.action == "stack":
        result = runtime_stack()
        name = "stack"
    elif args.action == "s1":
        result = run_s1(args.engine, args.frames, args.count, args.init_box, args.frozen_v, args.out, args.device,
                        imgsz_override=args.imgsz_override)
        name = f"s1-{args.engine.stem}"
    else:
        result = run_s2(args.engine, args.frames, args.count, args.init_box, args.hz, args.minutes, args.out, args.device,
                        imgsz_override=args.imgsz_override)
        name = f"s2-{args.engine.stem}-{int(args.hz)}hz"
    common.write_json(args.out / f"{name}-summary.json", result)
    print(json.dumps(result.get("verdict", {k: result[k] for k in list(result)[:6]}), ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
