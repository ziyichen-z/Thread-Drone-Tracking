#!/usr/bin/env python3
"""P1-ENG-LOOP-002 A6 / §3.5：四类数字唯一算法的离线评分器（K4）。

只读：会话 JSONL、`results.jsonl`、`publish-receipts.jsonl`、段日志、Unity 帧环旁车、
`m3_body_truth.jsonl`、几何文件与归档内的生效场景副本。真值只在本文件的评分函数里使用；
本文件**不**被 `controller/`、`tools/eng_loop2/llama_adapter.py`、`tools/language_serve.py`
导入（AC-9）。纯标准库 + `tools/dist_data` 纯函数；不加载任何模型。

子命令：
- `score`：对一个正式归档按 §3.5 产出漏斗与四表（描述性，不设门）。
- `archive-dryrun`：对 attempt 2 与 FRAME-001 两份既有归档的确认性试读（A6，描述、不作验收）。
- `derive-bc`：§3.6 B/C 派生（不读归档）。

时间一律取仿真帧轴（真值行 `simulation_time_s`，§3.3）；墙钟只作描述列。
"""

from __future__ import annotations

import argparse
import bisect
import datetime as _dt
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - 直接以脚本运行时
    sys.path.insert(0, str(REPO_ROOT))

from tools.dist_data import bind_layout, project_boxes  # noqa: E402

#: v2（C1 返工）：四类数字按真值来源分列（红车 Unity 真值 / 静止车几何近似 / 意图无效），不再出合并表；
#: 逐样本输出各数字结局与 time-to-bind/time-to-center 可复算时长。
SCHEMA = "p1-eng-loop-002-four-numbers/v2"
DRYRUN_SCHEMA = "p1-eng-loop-002-archive-dryrun/v1"
BC_SCHEMA = "p1-eng-loop-002-bc-derivation/v1"

# --- §3.5.6 数值出处（全部描述性） -------------------------------------------
IOU_THRESHOLD = 0.3  # 场景 evaluation.tracking_iou_threshold / FAST-001 BIND_IOU
COASTING_LIMIT_FRAMES = 30  # f_p 窗口（合同既有 coasting_limit）
TRACK_BUFFER = 30  # 冻结规格；漏检段达 31 帧 → LOST_BEYOND_BUFFER
SURVIVAL_WINDOWS_S = (13.0, 8.0)  # 主 13 s、并列 8 s（FAST-001 WINDOWS_S）
#: 移植 `tools/eng_acq/e2.py::EMPTY_WINDOW_MAX_GAP_S`（不 import：该模块顶层导入关联器）。
EMPTY_WINDOW_MAX_GAP_S = 8.0
N_CAP_FRAMES = 52
CENTER_RADIUS_PX = 64.0
CENTER_RUN_FRAMES = 5
CENTER_WINDOW_S = 13.0
IMAGE_WIDTH_PX = 640
IMAGE_HEIGHT_PX = 480
POSITION_TOLERANCE_M = 1e-3
MISLOCK_WINDOW_S = 13.0
PUBLISH_HZ = 5.0
INSUFFICIENT_N = 5
DELTA_EFF_BUCKETS: tuple[tuple[str, float, float], ...] = (
    ("[0,1)", 0.0, 1.0),
    ("[1,2)", 1.0, 2.0),
    ("[2,4)", 2.0, 4.0),
    ("[4,8)", 4.0, 8.0),
    ("[8,inf)", 8.0, math.inf),
)
OFF_AXIS_BUCKETS = ("in_view", "out_le_45deg", "out_gt_45deg", "NO_POSE")
SLANT_BUCKETS = ("lt_20m", "20_35m", "gt_35m", "NO_POSE")
OFF_AXIS_LIMIT_DEG = 45.0
BC_POOL_RADIUS_M = 40.0

ACCEPTED_OUTCOMES = frozenset({"APPLIED", "PENDING_QUEUED"})
SAMPLE_ACTIONS = frozenset({"ask", "respecify"})
#: 观察终点 E 的「下一条被受理」命令（`confirm_lost` 两种拼写都认）。
E_STOP_ACTIONS = frozenset({"release", "confirm_lost", "confirm-lost", "stop"})
PRESENTED_STATUSES = frozenset({"unique", "ambiguous"})
DESIGNATE_REPORTED_RESULTS = frozenset({"AMBIGUOUS", "NO_TRACK_AT_K", "FRAME_NOT_IN_HISTORY"})
BOUND_RESULTS = frozenset({"BOUND", "BOUND_COASTING"})
QUERY_ROW_KINDS = frozenset({"query_submitted", "query_started"})
DOWNSTREAM_PREFIXES = ("acquire_", "COASTING_", "L2_")
RED_CAR = "red_car"

FUNNEL_CLASSES: tuple[str, ...] = (
    "ATTRIBUTION_CONFLICT",
    "SUPERSEDED",
    "INTERRUPTED",
    "QUERY_FAILED",
    "STALE_REJECTED",
    "VLM_REPORTED",
    "OPERATOR_REJECTED",
    "UNCONFIRMED_SUPERSEDED",
    "UNCONFIRMED_AT_END",
    "DESIGNATE_REPORTED",
    "ACQUIRE_PATH",
    "BOUND_DIRECT",
)
INTENT_STATUSES = ("valid", "no_intent", "intent_unknown")
#: §3.5.1：红车 = Unity 真值；静止车 = 几何近似（AABB 投影）——两口径分列报告、不合并（C1-AC8-4）。
#: 意图非 `valid` 的样本无真值来源，在各数字第一步即 `NOT_EVALUABLE(no_intent|intent_unknown)`，单列。
TRUTH_SOURCES = ("red_car_unity_truth", "static_vehicle_geometry_approx", "intent_not_valid")
EXPLICIT_CLASSES = frozenset({"QUERY_FAILED", "STALE_REJECTED", "VLM_REPORTED", "DESIGNATE_REPORTED"})
EXPLICIT_RATIO_SET_ASIDE = frozenset(
    {"OPERATOR_REJECTED", "UNCONFIRMED_SUPERSEDED", "UNCONFIRMED_AT_END", "SUPERSEDED", "INTERRUPTED", "ATTRIBUTION_CONFLICT"}
)


class AnalyzeError(RuntimeError):
    """评分输入或守恒不成立（fail-closed）。"""


class ConservationError(AnalyzeError):
    """§3.5.2/§3.5.4 守恒式不等即抛错。"""


# --- 小工具 -----------------------------------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def iou_xywh(a: Sequence[float], b: Sequence[float]) -> float:
    """归一化 top-left `xywh` 的 IoU（两轴等比缩放下与像素 IoU 相同）。"""
    ax0, ay0, aw, ah = (float(v) for v in a)
    bx0, by0, bw, bh = (float(v) for v in b)
    ix = max(0.0, min(ax0 + aw, bx0 + bw) - max(ax0, bx0))
    iy = max(0.0, min(ay0 + ah, by0 + bh) - max(ay0, by0))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return 0.0 if union <= 0.0 else inter / union


def label(klass: str, args: Sequence[str] = ()) -> str:
    return f"{klass}({', '.join(args)})" if args else klass


def rate(numerator: int, denominator: int) -> dict[str, Any]:
    flags = []
    value = None
    if denominator <= 0:
        flags.append("ZERO_DENOMINATOR")
    else:
        value = numerator / denominator
    if denominator < INSUFFICIENT_N:
        flags.append("INSUFFICIENT_N")
    return {"value": value, "numerator": numerator, "denominator": denominator, "flags": flags}


def bucket_entry(counts: Mapping[str, int]) -> dict[str, Any]:
    n = sum(counts.values())
    return {"n": n, "counts": dict(sorted(counts.items())), "flags": ["INSUFFICIENT_N"] if n < INSUFFICIENT_N else []}


def delta_bucket(delta: float | None) -> str:
    if delta is None:
        return "NO_POSE"
    for name, low, high in DELTA_EFF_BUCKETS:
        if low <= delta < high:
            return name
    return "negative"


def slant_bucket(distance: float | None) -> str:
    if distance is None:
        return "NO_POSE"
    if distance < 20.0:
        return "lt_20m"
    if distance <= 35.0:
        return "20_35m"
    return "gt_35m"


# --- 输入 -------------------------------------------------------------------


@dataclass
class ArchivePaths:
    session_dir: Path
    unity_dir: Path
    runs_dir: Path | None = None
    scenario_copy: Path | None = None
    reference_scenario: Path = REPO_ROOT / "config" / "scenario.default.json"


class SidecarStore:
    """Unity 帧环旁车（`frame_<N>.json`）的只读缓存：返回 (字节 sha256, 文档)。"""

    def __init__(self, directory: Path | None):
        self.directory = Path(directory) if directory is not None else None
        self._cache: dict[int, tuple[str, dict[str, Any]] | None] = {}

    def get(self, frame_id: int) -> tuple[str, dict[str, Any]] | None:
        if frame_id in self._cache:
            return self._cache[frame_id]
        value = None
        if self.directory is not None:
            path = self.directory / f"frame_{int(frame_id):010d}.json"
            if path.exists():
                data = path.read_bytes()
                value = (sha256_bytes(data), json.loads(data.decode("utf-8")))
        self._cache[frame_id] = value
        return value

    def frame_ids(self) -> list[int]:
        if self.directory is None or not self.directory.exists():
            return []
        out = []
        for path in self.directory.glob("frame_*.json"):
            try:
                out.append(int(path.stem.split("_", 1)[1]))
            except ValueError:
                continue
        return sorted(out)


def _segment_dirs(runs_dir: Path, session_id: str | None) -> list[Path]:
    if not runs_dir.exists():
        return []
    picked = []
    for directory in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
        manifest = directory / "manifest.json"
        if not manifest.exists() or not (directory / "frames.jsonl").exists():
            continue
        document = json.loads(manifest.read_text(encoding="utf-8"))
        if session_id is None or document.get("session_id") == session_id:
            picked.append(directory)
    return picked


def vehicle_name_set(geometry: Mapping[str, Any]) -> set[str]:
    names = Counter(i["scene_object_name"] for i in geometry.get("instances", []) if i.get("group") == "vehicle")
    return {name for name, count in names.items() if count == 1}


def default_geometry_loader() -> dict[str, Any]:
    """§3.5.1：直接使用 `load_base_geometry` 返回的已调整几何（S0 sha 钉死）。"""
    return bind_layout.load_base_geometry(REPO_ROOT)


# --- 布局绑定（§3.5.1） ------------------------------------------------------


def layout_binding(
    scenario_copy: Path | None,
    manifests: Sequence[Mapping[str, Any]],
    reference_scenario: Path,
    geometry: Mapping[str, Any],
) -> dict[str, Any]:
    """副本缺失/sha 不符 → `layout_unbound`；`scene_adjustments` 不等 → `layout_mismatch`；
    相等 → `BOUND`（调用方直接用已调整几何，**不调用 `apply_layout`**、不逆施）。"""
    result: dict[str, Any] = {"status": None, "detail": None, "scenario_copy_sha256": None, "scenario_copy_id": None}
    if scenario_copy is None or not Path(scenario_copy).exists():
        result.update(status="layout_unbound", detail="scenario_copy_missing")
        return result
    copy_bytes = Path(scenario_copy).read_bytes()
    copy_sha = sha256_bytes(copy_bytes)
    copy_doc = json.loads(copy_bytes.decode("utf-8"))
    result["scenario_copy_sha256"] = copy_sha
    result["scenario_copy_id"] = copy_doc.get("scenario_id")
    if not manifests:
        result.update(status="layout_unbound", detail="no_segment_manifest")
        return result
    for manifest in manifests:
        planner = manifest.get("body_planner") or {}
        recorded = planner.get("effective_scenario_sha256") if isinstance(planner, Mapping) else None
        if recorded is None:
            result.update(status="layout_unbound", detail="manifest_without_effective_scenario_sha256")
            return result
        if recorded != copy_sha:
            result.update(status="layout_unbound", detail="scenario_copy_sha_mismatch")
            return result
    reference_bytes = Path(reference_scenario).read_bytes()
    if sha256_bytes(reference_bytes) != geometry.get("source_scenario_sha256"):
        result.update(status="layout_unbound", detail="reference_scenario_sha_not_geometry_source")
        return result
    reference_doc = json.loads(reference_bytes.decode("utf-8"))
    if copy_doc.get("scene_adjustments") != reference_doc.get("scene_adjustments"):
        result.update(status="layout_mismatch", detail="scene_adjustments_differ")
        return result
    result.update(status="BOUND", detail="scene_adjustments_equal_use_load_base_geometry")
    return result


# --- 会话 JSONL 索引 ----------------------------------------------------------


def _receipt(row: Mapping[str, Any]) -> Mapping[str, Any]:
    value = row.get("receipt")
    return value if isinstance(value, Mapping) else {}


def _is_accepted_sample_row(row: Mapping[str, Any]) -> bool:
    receipt = _receipt(row)
    return row.get("kind") == "receipt" and receipt.get("action") in SAMPLE_ACTIONS and receipt.get("outcome") in ACCEPTED_OUTCOMES


def _is_applied(row: Mapping[str, Any], actions: Iterable[str]) -> bool:
    receipt = _receipt(row)
    return row.get("kind") == "receipt" and receipt.get("action") in set(actions) and receipt.get("outcome") == "APPLIED"


def _is_terminal_row(row: Mapping[str, Any]) -> bool:
    return row.get("kind") == "state" and row.get("state") == "TERMINAL"


def _is_downstream(kind: str) -> bool:
    return any(kind.startswith(prefix) for prefix in DOWNSTREAM_PREFIXES)


@dataclass
class Sample:
    request_id: str | None
    action: str
    row: int
    epoch: int
    intent: Any
    intent_status: str
    delay_s: float | None
    conflicts: set[str] = field(default_factory=set)
    x_row: int | None = None  # None = 日志末尾
    x_kind: str = "log_end"  # next_accepted | terminal | log_end
    cause: str = "log_end"
    query_ids: list[str] = field(default_factory=list)
    attempts: list[dict[str, Any]] = field(default_factory=list)
    presented: dict[str, Any] | None = None
    failure: dict[str, Any] | None = None
    phase: str = "query_pending"
    result_arrived: list[dict[str, Any]] = field(default_factory=list)
    confirms: list[tuple[int, dict[str, Any]]] = field(default_factory=list)
    rejects: list[tuple[int, dict[str, Any]]] = field(default_factory=list)
    designation_rows: list[tuple[int, dict[str, Any]]] = field(default_factory=list)
    designation: dict[str, Any] | None = None
    designation_row: int | None = None
    designation_key: tuple[int, int] | None = None
    worker_abandoned: bool = False
    delay_injected_s: float | None = None
    pointer_epochs: list[dict[str, Any]] = field(default_factory=list)
    acquire_failed: dict[str, Any] | None = None
    coasting_ended: dict[str, Any] | None = None
    klass: str = ""
    args: tuple[str, ...] = ()
    h: int | None = None
    k: int | None = None
    delta_eff_s: float | None = None
    e_frame: int | None = None
    f_p: int | None = None
    numbers: dict[str, Any] = field(default_factory=dict)


class Archive:
    """一个会话归档的只读视图（所有路径显式给出；不读 `runtime/` 可变文件）。"""

    def __init__(
        self,
        paths: ArchivePaths,
        *,
        geometry: Mapping[str, Any] | None = None,
        geometry_loader: Callable[[], Mapping[str, Any]] = default_geometry_loader,
    ):
        self.paths = paths
        session_dir = Path(paths.session_dir)
        unity_dir = Path(paths.unity_dir)
        self.journal = read_jsonl(session_dir / "language-session.jsonl")
        results_path = session_dir / "results.jsonl"
        self.results = read_jsonl(results_path) if results_path.exists() else []
        receipts_path = session_dir / "publish-receipts.jsonl"
        self.publish_receipts = read_jsonl(receipts_path) if receipts_path.exists() else []
        self.session_frames_dir = session_dir / "frames"
        self.session_id = next((row.get("session_id") for row in self.journal if row.get("session_id")), None)
        runs_dir = Path(paths.runs_dir) if paths.runs_dir is not None else unity_dir / "runs"
        self.segment_dirs = _segment_dirs(runs_dir, self.session_id)
        self.manifests = [json.loads((d / "manifest.json").read_text(encoding="utf-8")) for d in self.segment_dirs]
        self.segment_rows: list[dict[str, Any]] = []
        for directory in self.segment_dirs:
            self.segment_rows.extend(read_jsonl(directory / "frames.jsonl"))
        truth_path = unity_dir / "m3_body_truth.jsonl"
        self.truth: dict[int, dict[str, Any]] = {}
        if truth_path.exists():
            for row in read_jsonl(truth_path):
                self.truth.setdefault(int(row["frame_id"]), row)
        self.sidecars = SidecarStore(unity_dir / "frames")
        self.geometry = dict(geometry) if geometry is not None else dict(geometry_loader())
        self.layout = layout_binding(paths.scenario_copy, self.manifests, paths.reference_scenario, self.geometry)
        self.input_files = {
            "language-session.jsonl": sha256_file(session_dir / "language-session.jsonl"),
            "results.jsonl": sha256_file(results_path) if results_path.exists() else None,
            "publish-receipts.jsonl": sha256_file(receipts_path) if receipts_path.exists() else None,
            "m3_body_truth.jsonl": sha256_file(truth_path) if truth_path.exists() else None,
            "segment_runs": [d.name for d in self.segment_dirs],
        }


# --- 评分器 -----------------------------------------------------------------


class Scorer:
    """§3.5 唯一算法；每个方法对应合同一小节。"""

    def __init__(self, archive: Archive):
        self.a = archive
        self.vehicle_names = vehicle_name_set(archive.geometry)
        self.instances = list(archive.geometry.get("instances", []))
        self.instance_by_name = {i["scene_object_name"]: i for i in self.instances}
        self.layout_status = archive.layout["status"]
        self.copy_scenario_id = archive.layout.get("scenario_copy_id")
        self.frame_identity_mismatch: dict[int, list[str]] = {}
        self.h2_scenario_check_unavailable: set[int] = set()
        self.result_frame_checks = Counter()
        self._projection_cache: dict[int, Any] = {}
        self._identity_cache: dict[int, tuple[str, Any] | None] = {}
        self.blocker_calls: list[tuple[int, list[tuple[str, Any, float]]]] = []
        self._index_frames()
        self._index_journal()

    # --- 帧序列（§3.5.1「指针框与帧序列」）---

    def _index_frames(self) -> None:
        by_frame: dict[int, dict[str, Any]] = {}
        duplicates = 0
        for row in sorted(self.a.segment_rows, key=lambda r: int(r["frame_id"])):
            frame_id = int(row["frame_id"])
            if frame_id in by_frame:
                duplicates += 1
                continue
            by_frame[frame_id] = row
        self.duplicate_frame_rows = duplicates
        self.seg_row = by_frame
        self.frames = sorted(by_frame)
        self.frame_pos = {f: i for i, f in enumerate(self.frames)}
        # §3.3/§3.5.1（C1-AC8-1，IR-3 边界）：帧时刻唯一来源 = 真值行 `simulation_time_s`。无真值
        # 时刻的帧时刻为 None（帧型按 NO_POSE 据实处理），段日志时刻只作诊断计数、不进任何数字。
        self.frames_without_truth_time = 0
        self.frames_without_truth_time_with_segment_time = 0
        self.time: dict[int, float | None] = {}
        for frame_id in self.frames:
            truth = self.a.truth.get(frame_id)
            if truth is not None and truth.get("simulation_time_s") is not None:
                self.time[frame_id] = float(truth["simulation_time_s"])
            else:
                self.time[frame_id] = None
                self.frames_without_truth_time += 1
                if by_frame[frame_id].get("simulation_time_s") is not None:
                    self.frames_without_truth_time_with_segment_time += 1

    def sim(self, frame_id: int | None) -> float | None:
        """帧的仿真时刻：只取真值行（§3.3）；无真值行或其无时刻 → None。"""
        if frame_id is None:
            return None
        if frame_id in self.time:
            return self.time[frame_id]
        truth = self.a.truth.get(frame_id)
        if truth is None or truth.get("simulation_time_s") is None:
            return None
        return float(truth["simulation_time_s"])

    def frames_between(self, start: int, end: int | None, *, include_start: bool = False) -> list[int]:
        """会话帧序列中 (start, end]（或 [start, end]）的帧，按帧号升序；end 为 None 时无上界。"""
        return [
            f for f in self.frames
            if (f >= start if include_start else f > start) and (end is None or f <= end)
        ]

    def split_at_time(self, frames: Sequence[int], end_time: float) -> tuple[list[int], list[int]]:
        """按帧轴切窗口：第一个**已知**真值时刻 > end_time 的帧起为窗外，其前为窗内（闭端点）。

        无真值时刻的帧不推定时刻：在首个已知越界帧之前者一律计入窗内，由帧型 NO_POSE 据实处理。
        """
        for position, frame_id in enumerate(frames):
            t = self.sim(frame_id)
            if t is not None and t > end_time:
                return list(frames[:position]), list(frames[position:])
        return list(frames), []

    # --- 会话 JSONL 索引 ---

    def _index_journal(self) -> None:
        journal = self.a.journal
        self.runtime_digest: dict[int, tuple[str | None, str | None]] = {}
        self.processed_marks: list[tuple[int, int]] = []  # (row, frame_id) 按行序
        generation = 0
        self.generation_at: list[int] = []
        for index, row in enumerate(journal):
            if row.get("kind") == "resident_loop_started":
                generation += 1
            self.generation_at.append(generation)
            if row.get("kind") == "frames_processed":
                frame_ids = [int(f) for f in row.get("frame_ids") or []]
                digests = row.get("metadata_sha256")
                reasons = row.get("metadata_sha256_missing_reason")
                for position, frame_id in enumerate(frame_ids):
                    digest = digests[position] if isinstance(digests, list) and position < len(digests) else None
                    if isinstance(digests, list):
                        reason = reasons[position] if isinstance(reasons, list) and position < len(reasons) else None
                    else:
                        reason = "field_absent_in_archive"
                    self.runtime_digest.setdefault(frame_id, (digest, reason))
                    self.processed_marks.append((index, frame_id))
        self._mark_rows = [row for row, _ in self.processed_marks]
        self._mark_running_last: list[int] = []
        for _, frame_id in self.processed_marks:
            self._mark_running_last.append(frame_id)

    def last_frame_before(self, row_index: int | None) -> int | None:
        """行序在 `row_index` 之前最后一个已处理帧（`None` = 会话最后已处理帧）。"""
        if not self.processed_marks:
            return None
        if row_index is None:
            return self.processed_marks[-1][1]
        position = bisect.bisect_left(self._mark_rows, row_index)
        return self._mark_running_last[position - 1] if position > 0 else None

    # --- §3.5.1 样本、意图、归属、冲突 ---

    def intent_status(self, intent: Any) -> str:
        if intent is None:
            return "no_intent"
        if isinstance(intent, str) and (intent == RED_CAR or intent in self.vehicle_names):
            return "valid"
        return "intent_unknown"

    def build_samples(self) -> list[Sample]:
        journal = self.a.journal
        samples: list[Sample] = []
        self.command_invalid = Counter()
        for index, row in enumerate(journal):
            if row.get("kind") != "receipt":
                continue
            receipt = _receipt(row)
            if _is_accepted_sample_row(row):
                intent = row.get("intent")
                delay = row.get("delay_s")
                samples.append(
                    Sample(
                        request_id=receipt.get("request_id"),
                        action=str(receipt.get("action")),
                        row=index,
                        epoch=int(row.get("epoch", -1)),
                        intent=intent,
                        intent_status=self.intent_status(intent),
                        delay_s=float(delay) if isinstance(delay, (int, float)) else (0.0 if "delay_s" in row else None),
                    )
                )
            elif receipt.get("outcome") == "REQUEST_INVALID" or str(receipt.get("outcome", "")).startswith("IGNORED_"):
                self.command_invalid[f"{receipt.get('action')}:{receipt.get('outcome')}:{row.get('detail')}"] += 1
        # C1：两个受理行同 request_id。
        by_request = defaultdict(list)
        for sample in samples:
            by_request[sample.request_id].append(sample)
        for group in by_request.values():
            if len(group) > 1:
                for sample in group:
                    sample.conflicts.add("C1")
        # C2：两个受理行同 epoch，或 epoch 未按行序严格递增。
        by_epoch = defaultdict(list)
        for sample in samples:
            by_epoch[sample.epoch].append(sample)
        for group in by_epoch.values():
            if len(group) > 1:
                for sample in group:
                    sample.conflicts.add("C2")
        for previous, current in zip(samples, samples[1:]):
            if current.epoch <= previous.epoch:
                previous.conflicts.add("C2")
                current.conflicts.add("C2")
        # X_s：下一受理行 / TERMINAL 行 / 日志末尾。
        terminal_rows = [i for i, row in enumerate(journal) if _is_terminal_row(row)]
        for position, sample in enumerate(samples):
            next_accepted = samples[position + 1].row if position + 1 < len(samples) else None
            next_terminal = next((i for i in terminal_rows if i > sample.row), None)
            candidates = [(next_accepted, "next_accepted"), (next_terminal, "terminal")]
            candidates = [(r, k) for r, k in candidates if r is not None]
            if candidates:
                sample.x_row, sample.x_kind = min(candidates)
                if sample.x_kind == "terminal":
                    sample.cause = str(journal[sample.x_row].get("reason") or "unknown")
                else:
                    sample.cause = "next_accepted"
            abandoned_end = sample.x_row if sample.x_row is not None else len(journal)
            sample.worker_abandoned = any(
                journal[i].get("kind") == "worker_abandoned" for i in range(sample.row + 1, abandoned_end + 1) if i < len(journal)
            )
        self.samples = samples
        return samples

    def attribute(self) -> None:
        journal = self.a.journal
        # C2 冲突样本同 epoch 时也按 epoch 收行（仍入类 0，不进分母）。
        epoch_groups = defaultdict(list)
        for sample in self.samples:
            epoch_groups[sample.epoch].append(sample)
        self.unattributed = Counter()
        # 设计查询 query_id → epoch 集合（C3）。
        query_epochs: dict[str, set[int]] = defaultdict(set)
        for row in journal:
            kind = row.get("kind")
            if kind in QUERY_ROW_KINDS and row.get("purpose") == "designate":
                query_epochs[str(row.get("query_id"))].add(int(row.get("epoch", -1)))
            elif kind in {"result_arrived", "result_presented"}:
                query_epochs[str(row.get("query_id"))].add(int(row.get("epoch", -1)))
        designate_results = [r for r in self.a.results if r.get("purpose") == "designate"]
        for result in designate_results:
            query_epochs[str(result.get("query_id"))].add(int(result.get("epoch", -1)))
        conflicting_epochs = set()
        for epoch_set in query_epochs.values():
            if len(epoch_set) > 1:
                conflicting_epochs |= epoch_set
        for sample in self.samples:
            if sample.epoch in conflicting_epochs:
                sample.conflicts.add("C3")
        # 结果行按行内 epoch 归属。
        results_by_epoch = defaultdict(list)
        for result in designate_results:
            epoch = int(result.get("epoch", -1))
            if epoch in epoch_groups:
                results_by_epoch[epoch].append(result)
            else:
                self.unattributed[f"results:{result.get('status')}"] += 1
        # 会话行按 epoch 归属。
        rows_by_epoch = defaultdict(list)
        self.unavailable_reattributed = 0
        for index, row in enumerate(journal):
            kind = str(row.get("kind"))
            relevant = (
                (kind in QUERY_ROW_KINDS and row.get("purpose") == "designate")
                or kind in {"result_arrived", "result_presented", "designation", "designation_unavailable"}
            )
            if not relevant:
                continue
            epoch = int(row.get("epoch", -1))
            if epoch not in epoch_groups and kind == "designation_unavailable":
                # AC-8 修订 2（IR-9）：确认后追平途中会话终止，`stop()` 先增 epoch 再写
                # `designation_unavailable(session_terminal)`；该行与其受理 confirm 仍属原 e_s。
                origin = self._unavailable_origin_epoch(index)
                if origin is not None and origin in epoch_groups:
                    rows_by_epoch[origin].append((index, row))
                    self.unavailable_reattributed += 1
                    continue
            if epoch in epoch_groups:
                rows_by_epoch[epoch].append((index, row))
            else:
                self.unattributed[kind] += 1
        for sample in self.samples:
            rows = rows_by_epoch.get(sample.epoch, [])
            results = results_by_epoch.get(sample.epoch, [])
            queries = []
            for _index, row in rows:
                if row.get("kind") in QUERY_ROW_KINDS and row.get("query_id") not in queries:
                    queries.append(row.get("query_id"))
            for result in results:
                if result.get("query_id") not in queries:
                    queries.append(result.get("query_id"))
            sample.query_ids = [str(q) for q in queries]
            sample.attempts = [
                {k: r.get(k) for k in ("query_id", "attempt", "status", "reject_reason", "last_status", "last_reject_reason", "request_id")}
                for r in results
            ]
            presented = [r for r in results if r.get("status") in PRESENTED_STATUSES]
            failures = [
                r
                for r in results
                if r.get("status") == "retry_exhausted"
                or (r.get("status") == "backend_error" and r.get("reject_reason") == "worker_stuck")
            ]
            sample.presented = presented[0] if presented else None
            sample.failure = failures[0] if failures else None
            sample.result_arrived = [row for _i, row in rows if row.get("kind") == "result_arrived"]
            if sample.result_arrived and not presented:
                sample.phase = "presentation_pending"
            # 同 epoch 的确认/拒绝回执。
            for index, row in enumerate(journal):
                if int(row.get("epoch", -1)) != sample.epoch:
                    continue
                if _is_applied(row, {"confirm"}):
                    sample.confirms.append((index, row))
                    if row.get("delay_injected_s") is not None:
                        sample.delay_injected_s = float(row["delay_injected_s"])
                elif _is_applied(row, {"reject"}):
                    sample.rejects.append((index, row))
            sample.designation_rows = [(i, row) for i, row in rows if row.get("kind") in {"designation", "designation_unavailable"}]
            # C4：结果行 request_id 非 null 且既非 s 的、也非 e_s 内受理 confirm 的。
            allowed = {sample.request_id} | {_receipt(row).get("request_id") for _i, row in sample.confirms}
            for result in results:
                if result.get("request_id") is not None and result.get("request_id") not in allowed:
                    sample.conflicts.add("C4")
            # C5。
            if len(presented) + len(failures) > 1:
                sample.conflicts.add("C5")
            if len(sample.designation_rows) > 1:
                sample.conflicts.add("C5")
            for index, _row in sample.designation_rows:
                if not any(c_index < index for c_index, _c in sample.confirms):
                    sample.conflicts.add("C5")
            for c_index, c_row in sample.confirms:
                after_designation = any(index > c_index for index, _r in sample.designation_rows)
                stale_after = self._confirm_stale_row(sample, c_row) is not None
                if not (after_designation or stale_after):
                    sample.conflicts.add("C5")
            designations = [(i, row) for i, row in sample.designation_rows if row.get("kind") == "designation"]
            if designations:
                index, row = designations[0]
                record = row.get("designation") or {}
                sample.designation = dict(record)
                sample.designation_row = index
                if record.get("designation_id") is not None:
                    sample.designation_key = (self.generation_at[index], int(record["designation_id"]))
                sample.h = record.get("head_frame_id")
                sample.k = record.get("frame_id_k")
                sim_h, sim_k = self.sim(sample.h), self.sim(sample.k)
                sample.delta_eff_s = None if sim_h is None or sim_k is None else sim_h - sim_k
        # C6：同一 designation_id 归入两个样本。
        by_key = defaultdict(list)
        for sample in self.samples:
            if sample.designation_key is not None:
                by_key[sample.designation_key].append(sample)
        for group in by_key.values():
            if len(group) > 1:
                for sample in group:
                    sample.conflicts.add("C6")
        self._attribute_downstream(by_key)

    def _unavailable_origin_epoch(self, index: int) -> int | None:
        """`designation_unavailable` 行所属确认的 epoch：其前最近一个受理 `confirm`，且二者之间只有
        会话终止（`stop()` 增 epoch 并写 `TERMINAL`）——无其他受理样本行、指定结果或不可用行。"""
        journal = self.a.journal
        saw_terminal = False
        for position in range(index - 1, -1, -1):
            row = journal[position]
            kind = row.get("kind")
            if _is_applied(row, {"confirm"}):
                return int(row.get("epoch", -1)) if saw_terminal else None
            if _is_terminal_row(row):
                saw_terminal = True
            elif _is_accepted_sample_row(row) or kind in {"designation", "designation_unavailable"}:
                return None
        return None

    def _confirm_stale_row(self, sample: Sample, confirm_row: Mapping[str, Any]) -> dict[str, Any] | None:
        """确认检查点过期行：e_s 内 `stale_rejected` 且 `query_id` 为呈现结果的查询（或 request_id 为该 confirm）。"""
        if sample.presented is None:
            return None
        confirm_id = _receipt(confirm_row).get("request_id")
        for result in self.a.results:
            if result.get("purpose") != "designate" or int(result.get("epoch", -1)) != sample.epoch:
                continue
            if result.get("status") != "stale_rejected":
                continue
            if result.get("query_id") == sample.presented.get("query_id") or (
                confirm_id is not None and result.get("request_id") == confirm_id
            ):
                return result
        return None

    def _attribute_downstream(self, by_key: Mapping[tuple[int, int], list[Sample]]) -> None:
        """§3.5.1 (ii)：下游事件按 (常驻代, designation_id) 归属；重复行取行序首行。"""
        journal = self.a.journal
        seen: set[tuple[Any, ...]] = set()
        self.duplicate_event_rows = Counter()
        self.downstream: dict[tuple[int, int], list[tuple[int, dict[str, Any]]]] = defaultdict(list)
        for index, row in enumerate(journal):
            kind = str(row.get("kind"))
            if not _is_downstream(kind):
                continue
            if row.get("designation_id") is None:
                if kind.startswith("acquire_"):
                    # `acquire_arrived`/`acquire_geometry_rejected` 不带 designation_id：归于当时进行中的 acquire。
                    continue
                self.unattributed[kind] += 1
                continue
            key = (self.generation_at[index], int(row["designation_id"]))
            dedup = (kind, key, row.get("frame_id"))
            if dedup in seen:
                self.duplicate_event_rows[kind] += 1
                continue
            seen.add(dedup)
            if key not in by_key:
                self.unattributed[kind] += 1
                continue
            self.downstream[key].append((index, row))
        # 指针 epoch（C1-AC8-2，AC-8 修订 1）：designation（BOUND/BOUND_COASTING）或同 (常驻代,
        # designation_id) 的 acquire_adopted 之后、**同一 e_s 与同一常驻代**内紧随的 pointer_bound；遇到
        # 别的指定去向/采纳行、受理样本行、TERMINAL、常驻重建或 epoch 改变即止——缺自身指针时不借下一
        # 样本的指针，也不跨代。归不进任何样本的 pointer_bound 计 `unattributed_rows`。
        claimed: dict[int, int] = {}
        self.pointer_bound_claim_conflicts = 0
        for position, sample in enumerate(self.samples):
            if sample.designation_key is None or sample.designation is None:
                continue
            anchors = []
            if sample.designation.get("result") in BOUND_RESULTS and sample.designation_row is not None:
                anchors.append(sample.designation_row)
            for index, row in self.downstream.get(sample.designation_key, []):
                kind = row.get("kind")
                if kind == "acquire_adopted":
                    anchors.append(index)
                elif kind == "acquire_failed" and sample.acquire_failed is None:
                    sample.acquire_failed = {**row, "_row": index}
                elif kind == "COASTING_TO_TRACK_ENDED" and sample.coasting_ended is None:
                    sample.coasting_ended = {**row, "_row": index}
            for anchor in sorted(anchors):
                bound = self._own_pointer_bound(anchor, sample.epoch, sample.designation_key[0])
                if bound is None:
                    continue
                index, row = bound
                if index in claimed and claimed[index] != position:
                    self.pointer_bound_claim_conflicts += 1
                    continue
                claimed[index] = position
                end_frame = None
                for later in journal[index + 1 :]:
                    if later.get("kind") == "segment_retired" and later.get("track_id") == row.get("track_id"):
                        end_frame = later.get("to_frame_id")
                        break
                sample.pointer_epochs.append(
                    {
                        "track_id": row.get("track_id"),
                        "library_track_id": row.get("library_track_id"),
                        "start_frame": int(row.get("frame_id")) if row.get("frame_id") is not None else -1,
                        "end_frame": None if end_frame is None else int(end_frame),
                        "pointer_bound_row": index,
                    }
                )
        for index, row in enumerate(journal):
            if row.get("kind") == "pointer_bound" and index not in claimed:
                self.unattributed["pointer_bound"] += 1

    def _own_pointer_bound(self, anchor: int, epoch: int, generation: int) -> tuple[int, dict[str, Any]] | None:
        """锚点行之后紧随的本样本 pointer_bound（同 epoch、同常驻代），否则 None。"""
        journal = self.a.journal
        for index in range(anchor + 1, len(journal)):
            row = journal[index]
            kind = row.get("kind")
            if int(row.get("epoch", -1)) != epoch or self.generation_at[index] != generation:
                return None
            if kind == "pointer_bound":
                return index, row
            if (
                kind in {"designation", "designation_unavailable", "acquire_adopted", "resident_loop_started"}
                or _is_accepted_sample_row(row)
                or _is_terminal_row(row)
            ):
                return None
        return None

    # --- §3.5.2 漏斗 ---

    def classify(self, sample: Sample) -> None:
        if sample.conflicts:
            sample.klass, sample.args = "ATTRIBUTION_CONFLICT", tuple(sorted(sample.conflicts))
            return
        if sample.presented is None and sample.failure is None:
            if sample.x_kind == "next_accepted":
                sample.klass, sample.args = "SUPERSEDED", (sample.phase,)
            else:
                sample.klass, sample.args = "INTERRUPTED", (sample.phase, sample.cause)
            return
        if sample.failure is not None:
            failure = sample.failure
            if failure.get("status") == "backend_error":
                sample.klass, sample.args = "QUERY_FAILED", ("backend_error",)
                return
            last = str(failure.get("last_status"))
            if last == "stale_rejected":
                sample.klass, sample.args = "STALE_REJECTED", ("query", str(failure.get("last_reject_reason")))
            elif last == "none":
                sample.klass, sample.args = "VLM_REPORTED", ("none",)
            else:
                sample.klass, sample.args = "QUERY_FAILED", (last,)
            return
        # 有 P_s：确认阶段。
        if sample.confirms:
            _c_index, c_row = sample.confirms[0]
            stale = self._confirm_stale_row(sample, c_row)
            if stale is not None:
                sample.klass, sample.args = "STALE_REJECTED", ("confirm", str(stale.get("reject_reason")))
                return
            unavailable = [row for _i, row in sample.designation_rows if row.get("kind") == "designation_unavailable"]
            if unavailable:
                sample.klass, sample.args = "INTERRUPTED", ("designation_unavailable", str(unavailable[0].get("reason")))
                return
            result = str((sample.designation or {}).get("result"))
            self.resolve_window_frames(sample)
            if result in DESIGNATE_REPORTED_RESULTS:
                sample.klass, sample.args = "DESIGNATE_REPORTED", (result,)
                return
            if result == "TRACK_ENDED":
                sample.klass, sample.args = "ACQUIRE_PATH", ("track_ended",)
                return
            if result == "BOUND_COASTING" and sample.coasting_ended is not None:
                coast_frame = sample.coasting_ended.get("frame_id")
                if sample.f_p is None or (coast_frame is not None and int(coast_frame) < sample.f_p):
                    sample.klass, sample.args = "ACQUIRE_PATH", ("coasting_timeout",)
                    return
            sample.klass, sample.args = "BOUND_DIRECT", ("bound" if result == "BOUND" else "coasting_recovered",)
            return
        if sample.rejects:
            sample.klass, sample.args = "OPERATOR_REJECTED", ()
            return
        if sample.x_kind == "next_accepted":
            sample.klass, sample.args = "UNCONFIRMED_SUPERSEDED", ()
        else:
            sample.klass, sample.args = "UNCONFIRMED_AT_END", (sample.cause,)

    # --- E 与 f_p（§3.5.1） ---

    def resolve_window_frames(self, sample: Sample) -> None:
        if sample.designation_row is None or sample.h is None:
            return
        journal = self.a.journal
        stop_row = None
        for index in range(sample.designation_row + 1, len(journal)):
            row = journal[index]
            if _is_accepted_sample_row(row) or _is_applied(row, E_STOP_ACTIONS) or _is_terminal_row(row):
                stop_row = index
                break
        sample.e_frame = self.last_frame_before(stop_row)
        sample.f_p = None
        if sample.e_frame is None:
            return
        for frame_id in self.frames:
            if frame_id <= sample.h or frame_id > sample.e_frame:
                continue
            if self.pointer_box(sample, frame_id) is not None:
                sample.f_p = frame_id
                break

    def pointer_epoch_at(self, sample: Sample, frame_id: int) -> dict[str, Any] | None:
        for epoch in sample.pointer_epochs:
            if frame_id > epoch["start_frame"] and (epoch["end_frame"] is None or frame_id <= epoch["end_frame"]):
                return epoch
        return None

    def pointer_box(self, sample: Sample, frame_id: int) -> list[float] | None:
        row = self.seg_row.get(frame_id)
        if row is None or row.get("ok") is not True or row.get("box_norm") is None:
            return None
        if self.pointer_epoch_at(sample, frame_id) is None:
            return None
        return [float(v) for v in row["box_norm"]]

    # --- 帧身份（H-2）与意图框 ---

    def identity(self, frame_id: int) -> tuple[str, Any] | None:
        """H-2 (1)–(4)：None = 通过；否则 ("metadata_unbound"|"frame_identity_mismatch"|"no_sidecar"|"no_truth", 细节)。"""
        if frame_id in self._identity_cache:
            return self._identity_cache[frame_id]
        verdict: tuple[str, Any] | None
        truth = self.a.truth.get(frame_id)
        sidecar = self.a.sidecars.get(frame_id)
        if truth is None:
            verdict = ("no_truth", None)
        elif sidecar is None:
            verdict = ("no_sidecar", None)
        else:
            digest, reason = self.runtime_digest.get(frame_id, (None, "frame_not_in_frames_processed"))
            if digest is None:
                verdict = ("metadata_unbound", reason)
            else:
                file_sha, doc = sidecar
                failed = []
                if file_sha != digest:
                    failed.append("1_metadata_sha256")
                seg = self.seg_row.get(frame_id)
                times = [doc.get("simulation_time_s"), truth.get("simulation_time_s")]
                if seg is not None:
                    times.append(seg.get("simulation_time_s"))
                if doc.get("frame_id") != frame_id or len({float(t) if t is not None else None for t in times}) != 1:
                    failed.append("2_frame_id_or_time")
                position = doc.get("camera_position_world_m") or [None, None, None]
                body = [truth.get("body_world_x_m"), truth.get("body_world_y_m"), truth.get("body_world_z_m")]
                try:
                    if any(abs(float(p) - float(b)) > POSITION_TOLERANCE_M for p, b in zip(position, body)):
                        failed.append("3_camera_position")
                except (TypeError, ValueError):
                    failed.append("3_camera_position")
                if self.copy_scenario_id is None:
                    self.h2_scenario_check_unavailable.add(frame_id)
                elif doc.get("scenario_id") != self.copy_scenario_id:
                    failed.append("4_scenario_id")
                if failed:
                    self.frame_identity_mismatch[frame_id] = failed
                    verdict = ("frame_identity_mismatch", failed)
                else:
                    verdict = None
        self._identity_cache[frame_id] = verdict
        return verdict

    def _red_blocker(self, frame_id: int, camera: project_boxes.Camera) -> list[tuple[str, Any, float]]:
        truth = self.a.truth.get(frame_id)
        if truth is None or not truth.get("truth_box_available"):
            return []
        box = [truth["truth_box_x"], truth["truth_box_y"], truth["truth_box_width"], truth["truth_box_height"]]
        target = (float(truth["target_world_x_m"]), float(truth["target_world_y_m"]), float(truth["target_world_z_m"]))
        depth = camera.to_camera_space(target)[2]
        return [(RED_CAR, project_boxes.denormalize_xywh(box, camera), depth)]

    def static_projection(self, frame_id: int) -> tuple[str, Any]:
        """静止车：("NO_POSE", 原因) 或 ("OK", {name: ProjectedObject})。"""
        if frame_id in self._projection_cache:
            return self._projection_cache[frame_id]
        verdict = self.identity(frame_id)
        if verdict is not None:
            value: tuple[str, Any] = ("NO_POSE", verdict[0])
        else:
            _sha, doc = self.a.sidecars.get(frame_id)  # type: ignore[misc]
            try:
                camera = project_boxes.Camera.from_sidecar(doc)
            except project_boxes.ProjectionError:
                value = ("NO_POSE", "sidecar_invalid")
            else:
                blockers = self._red_blocker(frame_id, camera)
                self.blocker_calls.append((frame_id, blockers))
                projected = project_boxes.project_instances(camera, self.instances, extra_blockers=blockers)
                value = ("OK", {p.object_id: p for p in projected})
        self._projection_cache[frame_id] = value
        return value

    def intent_pose(self, intent: str, frame_id: int) -> tuple[str, Any]:
        """("NO_POSE", 原因) / ("INVISIBLE", 状态) / ("VISIBLE", 归一化框)。

        无真值时刻的帧一律 NO_POSE（§3.3：时刻只来自真值行；段日志时刻不替代）。"""
        if self.sim(frame_id) is None:
            return ("NO_POSE", "no_truth" if self.a.truth.get(frame_id) is None else "no_truth_time")
        if intent == RED_CAR:
            truth = self.a.truth.get(frame_id)
            if truth is None:
                return ("NO_POSE", "no_truth")
            if not truth.get("truth_box_available"):
                return ("INVISIBLE", "truth_box_unavailable")
            return ("VISIBLE", [truth["truth_box_x"], truth["truth_box_y"], truth["truth_box_width"], truth["truth_box_height"]])
        state, value = self.static_projection(frame_id)
        if state == "NO_POSE":
            return ("NO_POSE", value)
        projected = value.get(intent)
        if projected is None:
            return ("INVISIBLE", "NOT_IN_GEOMETRY")
        if projected.status == "OK" and projected.visible_norm_xywh is not None:
            return ("VISIBLE", list(projected.visible_norm_xywh))
        return ("INVISIBLE", projected.status)

    def frame_type(self, sample: Sample, frame_id: int) -> tuple[str, Any]:
        """帧型（§3.5.1）：NO_POSE → INVISIBLE → ON → OFF → MISS。"""
        state, value = self.intent_pose(str(sample.intent), frame_id)
        if state in {"NO_POSE", "INVISIBLE"}:
            return (state, value)
        box = self.pointer_box(sample, frame_id)
        if box is None:
            return ("MISS", None)
        return ("ON", value) if iou_xywh(box, value) >= IOU_THRESHOLD else ("OFF", value)

    def layout_excluded(self, sample: Sample) -> str | None:
        """静止车意图且布局未绑定 → 该数字的 `NOT_EVALUABLE(layout_*)`。"""
        if sample.intent != RED_CAR and self.layout_status != "BOUND":
            return str(self.layout_status)
        return None

    # --- §3.5.3 数字一 ---

    def number_one(self, sample: Sample) -> tuple[str, ...] | None:
        if sample.klass not in {"BOUND_DIRECT", "ACQUIRE_PATH", "DESIGNATE_REPORTED"}:
            return None
        if sample.intent_status != "valid":
            return ("NOT_EVALUABLE", sample.intent_status)
        excluded = self.layout_excluded(sample)
        if excluded:
            return ("NOT_EVALUABLE", excluded)
        if sample.klass == "ACQUIRE_PATH":
            return ("TO_ACQUIRE",)
        if sample.klass == "DESIGNATE_REPORTED":
            return ("REPORTED",)
        h = int(sample.h)  # BOUND_DIRECT 必有 designation
        limit = h + COASTING_LIMIT_FRAMES
        if sample.f_p is not None and sample.f_p <= limit:
            kind, detail = self.frame_type(sample, sample.f_p)
            if kind == "ON":
                return ("RESOLVED_CORRECT",)
            if kind == "OFF":
                return ("RESOLVED_WRONG",)
            return ("NOT_EVALUABLE", f"{kind}:{detail}")
        if sample.e_frame is None or sample.e_frame < limit:
            return ("CENSORED",)
        return ("BOUND_NO_PUBLISH",)

    # --- §3.5.4 数字二 ---

    def entry_gate(self, sample: Sample) -> tuple[str, ...] | None:
        """进入起点集 S 前的按序判定；返回 None 表示进入 S。"""
        if sample.intent_status != "valid":
            return ("NOT_EVALUABLE", sample.intent_status)
        excluded = self.layout_excluded(sample)
        if excluded:
            return ("NOT_EVALUABLE", excluded)
        if sample.f_p is None:
            return ("NO_FIRST_PUBLISH",)
        kind, _ = self.frame_type(sample, sample.f_p)
        if kind not in {"ON", "OFF"}:
            return ("START_UNSCORABLE", kind)
        return None

    def survival(self, sample: Sample, window_s: float) -> dict[str, Any]:
        f_p = int(sample.f_p)  # type: ignore[arg-type]
        start_kind, _ = self.frame_type(sample, f_p)
        changes = 0
        if start_kind == "OFF":
            return {"outcome": "UNBOUND_START", "pointer_track_changed": 0}
        t0 = self.sim(f_p)  # 起点帧型 ON ⇒ 有真值时刻（NO_POSE 不入 S）
        end_time = float(t0) + window_s  # type: ignore[arg-type]
        after = self.frames_between(f_p, sample.e_frame)
        e_time = self.sim(sample.e_frame)
        if e_time is not None:
            if end_time > e_time:
                return {"outcome": "CENSORED_END", "pointer_track_changed": 0}
        elif not any(self.sim(f) is not None and self.sim(f) >= end_time for f in after):  # type: ignore[operator]
            # E 无真值时刻、其前也无已知越过窗尾的帧：是否截尾无法由真值时间轴判定 → 按 NO_POSE 排除。
            return {"outcome": "TRUTH_GAP", "detail": "no_pose", "pointer_track_changed": 0}
        window, _beyond = self.split_at_time(after, end_time)
        window_set = set(window)
        kinds = {f: self.frame_type(sample, f)[0] for f in window}
        if any(kind == "NO_POSE" for kind in kinds.values()):
            return {"outcome": "TRUTH_GAP", "detail": "no_pose", "pointer_track_changed": 0}
        run = 0
        for f in window:
            run = run + 1 if kinds[f] == "INVISIBLE" else 0
            if run > TRACK_BUFFER:
                return {"outcome": "TRUTH_GAP", "detail": "invisible", "pointer_track_changed": 0}
        # 窗内帧均非 NO_POSE ⇒ 均有真值时刻。
        times = [float(t0)] + [float(self.sim(f)) for f in window]  # type: ignore[arg-type]
        if not window or any(b - a > EMPTY_WINDOW_MAX_GAP_S for a, b in zip(times, times[1:])):
            # ACQ `e2.assert_no_empty_window` 在此抛 `EmptyWindow`；本项改为显式排除类。
            return {"outcome": "TRUTH_GAP", "detail": "empty_window", "pointer_track_changed": 0}
        miss = 0
        last_track = (self.pointer_epoch_at(sample, f_p) or {}).get("library_track_id")
        outcome = None
        for frame_id in after:
            inside = frame_id in window_set
            if not inside and miss == 0:
                outcome = "KEPT"
                break
            kind = kinds.get(frame_id) or self.frame_type(sample, frame_id)[0]
            if not inside and kind == "NO_POSE":
                return {"outcome": "TRUTH_GAP", "detail": "no_pose_ext", "pointer_track_changed": changes}
            if kind == "OFF":
                outcome = "ID_SWITCH"
                break
            if kind == "ON":
                track = (self.pointer_epoch_at(sample, frame_id) or {}).get("library_track_id")
                if track != last_track:
                    changes += 1
                    last_track = track
                miss = 0
                if not inside:
                    outcome = "KEPT"
                    break
            else:
                miss += 1
                if miss == TRACK_BUFFER + 1:
                    outcome = "LOST_BEYOND_BUFFER"
                    break
        if outcome is None:
            outcome = "UNRESOLVED_END_MISS" if miss > 0 else "KEPT"
        return {"outcome": outcome, "pointer_track_changed": changes}

    # --- §3.5.5 数字三 ---

    def capture(self, sample: Sample) -> dict[str, Any] | None:
        if sample.klass not in {"BOUND_DIRECT", "ACQUIRE_PATH"}:
            return None
        if sample.intent_status != "valid":
            return {"outcome": "NOT_EVALUABLE", "detail": sample.intent_status}
        excluded = self.layout_excluded(sample)
        if excluded:
            return {"outcome": "NOT_EVALUABLE", "detail": excluded}
        h = int(sample.h) if sample.h is not None else None
        if h is None:
            return {"outcome": "NOT_EVALUABLE", "detail": "no_head_frame"}
        cap = h + N_CAP_FRAMES
        events: list[tuple[int, int, str]] = []  # (帧, 优先级, 名)
        if sample.f_p is not None:
            events.append((sample.f_p, 0, "f_p"))
        if sample.acquire_failed is not None:
            failed_frame = self.last_frame_before(sample.acquire_failed["_row"])
            events.append((failed_frame if failed_frame is not None else h, 1, "acquire_failed"))
        if sample.e_frame is not None:
            events.append((sample.e_frame, 2, "E"))
        else:
            events.append((h, 2, "E"))
        events.append((cap, 3, "cap"))
        first = min(events)
        if first[2] == "E":
            return {"outcome": "CENSORED"}
        if first[2] == "acquire_failed":
            return {"outcome": "ACQUIRE_FAILED", "detail": str(sample.acquire_failed.get("cause"))}
        if first[2] == "cap":
            return {"outcome": "CAPTURE_TIMEOUT"}
        kind, detail = self.frame_type(sample, sample.f_p)  # type: ignore[arg-type]
        if kind == "OFF":
            return {"outcome": "WRONG_CAPTURE"}
        if kind != "ON":
            return {"outcome": "NOT_EVALUABLE", "detail": f"{kind}:{detail}"}
        out: dict[str, Any] = {"outcome": "CAPTURED"}
        sim_fp, sim_h = self.sim(sample.f_p), self.sim(h)
        out["time_to_bind_s"] = None if sim_fp is None or sim_h is None else sim_fp - sim_h
        out.update(self.time_to_center(sample))
        return out

    def time_to_center(self, sample: Sample) -> dict[str, Any]:
        """§3.5.5 time-to-center：自 f_p 起意图框中心距 (320, 240) < 64 px 连续 5 帧的首帧；
        截止 min(f_p + 13 s, E)（闭端点；按真值时间轴）。输出结局与可复算时长（C1-AC8-3）。"""
        f_p = int(sample.f_p)  # type: ignore[arg-type]
        t0 = float(self.sim(f_p))  # type: ignore[arg-type]  # 只对 CAPTURED（f_p 为 ON ⇒ 有真值时刻）
        sim_h = self.sim(sample.h)
        limit = t0 + CENTER_WINDOW_S
        frames = self.frames_between(f_p, sample.e_frame, include_start=True)
        window, beyond = self.split_at_time(frames, limit)
        run, run_start = 0, None
        for frame_id in window:
            state, box = self.intent_pose(str(sample.intent), frame_id)
            if state != "VISIBLE":
                run, run_start = 0, None  # INVISIBLE / NO_POSE 打断连续计数
                continue
            cx = (float(box[0]) + float(box[2]) / 2.0) * IMAGE_WIDTH_PX
            cy = (float(box[1]) + float(box[3]) / 2.0) * IMAGE_HEIGHT_PX
            if math.hypot(cx - IMAGE_WIDTH_PX / 2.0, cy - IMAGE_HEIGHT_PX / 2.0) < CENTER_RADIUS_PX:
                if run == 0:
                    run_start = frame_id
                run += 1
                if run >= CENTER_RUN_FRAMES:
                    t_center = float(self.sim(run_start))  # type: ignore[arg-type]
                    return {
                        "center": "CENTERED",
                        "center_run_start_frame": run_start,
                        "time_to_center_from_f_p_s": t_center - t0,
                        "time_to_center_from_h_s": None if sim_h is None else t_center - sim_h,
                    }
            else:
                run, run_start = 0, None
        e_time = self.sim(sample.e_frame)
        reached = bool(beyond) or (e_time is not None and e_time >= limit)
        return {
            "center": "CENTER_NOT_REACHED" if reached else "CENTER_CENSORED",
            "center_run_start_frame": None,
            "time_to_center_from_f_p_s": None,
            "time_to_center_from_h_s": None,
        }

    def off_axis(self, sample: Sample) -> tuple[str, str]:
        """k 帧旁车相机前向与意图中心方向夹角 × 斜距；k 帧无旁车/未过 H-2 → NO_POSE 桶。"""
        k = sample.k
        if k is None or self.identity(int(k)) is not None:
            return ("NO_POSE", "NO_POSE")
        _sha, doc = self.a.sidecars.get(int(k))  # type: ignore[misc]
        try:
            camera = project_boxes.Camera.from_sidecar(doc)
        except project_boxes.ProjectionError:
            return ("NO_POSE", "NO_POSE")
        if sample.intent == RED_CAR:
            truth = self.a.truth.get(int(k))
            center = (float(truth["target_world_x_m"]), float(truth["target_world_y_m"]), float(truth["target_world_z_m"]))
        else:
            instance = self.instance_by_name.get(str(sample.intent))
            if instance is None:
                return ("NO_POSE", "NO_POSE")
            center = (
                (instance["min_x_m"] + instance["max_x_m"]) / 2.0,
                (instance["min_y_m"] + instance["max_y_m"]) / 2.0,
                (instance["min_z_m"] + instance["max_z_m"]) / 2.0,
            )
        x, y, z = camera.to_camera_space(center)
        distance = math.sqrt(x * x + y * y + z * z)
        bucket = None
        if z > 0.0:
            u, v = camera.project_camera_point((x, y, z))
            if 0.0 <= u < camera.width and 0.0 <= v < camera.height:
                bucket = "in_view"
        if bucket is None:
            angle = math.degrees(math.acos(max(-1.0, min(1.0, z / distance)))) if distance > 0 else 0.0
            bucket = "out_le_45deg" if angle <= OFF_AXIS_LIMIT_DEG else "out_gt_45deg"
        return (bucket, slant_bucket(distance))

    # --- 误锁时长 ---

    def mislock_duration(self, sample: Sample) -> dict[str, Any]:
        """[f_p, min(E, f_p + 13 s)]（闭端点，真值时间轴）内帧型 OFF 且已发布观测的帧数 ÷ 5，并列这些帧上
        归属本样本指针 epoch 的 WRITTEN `observation`/`body_command` 收据数。"""
        f_p = int(sample.f_p)  # type: ignore[arg-type]
        t0 = float(self.sim(f_p))  # type: ignore[arg-type]  # f_p 帧型 ON/OFF ⇒ 有真值时刻
        frames = self.frames_between(f_p, sample.e_frame, include_start=True)
        window, _beyond = self.split_at_time(frames, t0 + MISLOCK_WINDOW_S)
        off_frames = [
            frame_id
            for frame_id in window
            if self.frame_type(sample, frame_id)[0] == "OFF" and self.seg_row[frame_id].get("published_observation") is True
        ]
        track_ids = {epoch["track_id"] for epoch in sample.pointer_epochs}
        frame_set = set(off_frames)
        written = Counter(
            r.get("channel")
            for r in self.a.publish_receipts
            if r.get("outcome") == "WRITTEN"
            and r.get("channel") in {"observation", "body_command"}
            and r.get("frame_id") in frame_set
            and r.get("track_id") in track_ids
        )
        return {"off_published_frames": len(off_frames), "duration_s": len(off_frames) / PUBLISH_HZ, "written_receipts": dict(written)}

    # --- 会话结果帧 sha（H-2 末句） ---

    def check_result_frames(self) -> None:
        for result in self.a.results:
            frame_id, digest = result.get("frame_id"), result.get("frame_sha256")
            if frame_id is None or digest is None:
                continue
            path = self.a.session_frames_dir / f"frame_{int(frame_id):010d}.jpg"
            if not path.exists():
                self.result_frame_checks["unverifiable_missing_jpeg"] += 1
            elif sha256_file(path) == digest:
                self.result_frame_checks["match"] += 1
            else:
                self.result_frame_checks["mismatch"] += 1

    # --- 汇总 ---

    def run(self) -> dict[str, Any]:
        self.build_samples()
        self.attribute()
        for sample in self.samples:
            self.classify(sample)
        self.check_result_frames()
        return self.report()

    def truth_source(self, sample: Sample) -> str:
        if sample.intent_status != "valid":
            return "intent_not_valid"
        return "red_car_unity_truth" if sample.intent == RED_CAR else "static_vehicle_geometry_approx"

    def compute_numbers(self, sample: Sample) -> None:
        """逐样本求各数字结局（只算一次；汇总与逐样本记录共用）。"""
        numbers: dict[str, Any] = {"truth_source": self.truth_source(sample)}
        numbers["number_one"] = self.number_one(sample)
        bound = sample.klass in {"BOUND_DIRECT", "ACQUIRE_PATH"}
        numbers["entry_gate"] = self.entry_gate(sample) if bound else None
        numbers["in_S"] = bound and numbers["entry_gate"] is None
        numbers["survival"] = {}
        if numbers["in_S"]:
            for window in SURVIVAL_WINDOWS_S:
                numbers["survival"][f"W_{int(window)}s"] = self.survival(sample, window)
            start_kind = self.frame_type(sample, int(sample.f_p))[0]  # type: ignore[arg-type]
            outcome_13 = numbers["survival"]["W_13s"]["outcome"]
            numbers["mislock"] = start_kind == "OFF" or outcome_13 == "ID_SWITCH"
            numbers["mislock_window_partial"] = (not numbers["mislock"]) and start_kind == "ON" and outcome_13 in {
                "CENSORED_END",
                "TRUTH_GAP",
            }
            numbers["mislock_duration"] = self.mislock_duration(sample) if numbers["mislock"] else None
            numbers["off_axis"] = self.off_axis(sample)
        numbers["capture"] = self.capture(sample)
        if numbers["capture"] is not None and numbers["capture"]["outcome"] != "NOT_EVALUABLE":
            numbers["capture_bucket"] = self.off_axis(sample)
        sample.numbers = numbers

    def report(self) -> dict[str, Any]:
        samples = self.samples
        n = len(samples)
        funnel = Counter(s.klass for s in samples)
        labels = Counter(label(s.klass, s.args) for s in samples)
        intents = Counter(s.intent_status for s in samples)
        if sum(funnel.values()) != n or sum(intents.values()) != n or any(k not in FUNNEL_CLASSES for k in funnel):
            raise ConservationError(f"漏斗守恒不成立：受理 {n}，十二类 {sum(funnel.values())}，意图 {sum(intents.values())}")
        cross = {klass: {status: 0 for status in INTENT_STATUSES} for klass in FUNNEL_CLASSES}
        for sample in samples:
            cross[sample.klass][sample.intent_status] += 1
        for sample in samples:
            self.compute_numbers(sample)
        by_source = {source: [s for s in samples if s.numbers["truth_source"] == source] for source in TRUTH_SOURCES}
        source_n = {source: len(group) for source, group in by_source.items()}
        if sum(source_n.values()) != n:
            raise ConservationError("真值来源分组守恒不成立")

        number_one = self._number_one_tables(by_source)
        number_two, mislock = self._number_two_tables(by_source)
        number_three = self._number_three_tables(by_source)
        explicit_report = self._explicit_tables(by_source)

        mismatch_checks = Counter(check for checks in self.frame_identity_mismatch.values() for check in checks)
        return {
            "schema": SCHEMA,
            "truth_sources": {
                "red_car_unity_truth": "红车：同帧 m3_body_truth（Unity 真值，CoverageEvaluator 写）",
                "static_vehicle_geometry_approx": "静止车：旁车相机 + 几何 AABB 投影（几何近似，非 Unity 真值）",
                "intent_not_valid": "意图缺失/不在闭集：无真值来源，各数字第一步 NOT_EVALUABLE",
                "merged_table": None,
                "note": "§3.5.1：两种口径分列报告，本输出不含合并比率或合并计数表",
                "samples_by_source": source_n,
            },
            "layout_binding": self.a.layout,
            "frame_identity_mismatch": {
                "frames": len(self.frame_identity_mismatch),
                "by_check": dict(sorted(mismatch_checks.items())),
                "result_frame_sha256_mismatch": self.result_frame_checks.get("mismatch", 0),
                "total": len(self.frame_identity_mismatch) + self.result_frame_checks.get("mismatch", 0),
                "examples": sorted(self.frame_identity_mismatch.items())[:5],
            },
            "result_frame_sha256_checks": dict(sorted(self.result_frame_checks.items())),
            "h2_scenario_check_unavailable_frames": len(self.h2_scenario_check_unavailable),
            "unattributed_rows": dict(sorted(self.unattributed.items())),
            "designation_unavailable_reattributed_to_confirm_epoch": self.unavailable_reattributed,
            "pointer_bound_claim_conflicts": self.pointer_bound_claim_conflicts,
            "duplicate_event_rows": sum(self.duplicate_event_rows.values()),
            "duplicate_event_rows_by_kind": dict(sorted(self.duplicate_event_rows.items())),
            "duplicate_frame_rows": self.duplicate_frame_rows,
            "frame_time_source": {
                "source": "m3_body_truth.simulation_time_s",
                "frames_without_truth_time": self.frames_without_truth_time,
                "frames_without_truth_time_with_segment_time_diagnostic_only": self.frames_without_truth_time_with_segment_time,
                "segment_log_time_used_for_numbers": False,
            },
            "attribution_conflicts": dict(sorted(Counter(c for s in samples for c in s.conflicts).items())),
            "command_invalid": dict(sorted(self.command_invalid.items())),
            "funnel": {
                "n_accepted": n,
                "classes": {klass: funnel.get(klass, 0) for klass in FUNNEL_CLASSES},
                "labels": dict(sorted(labels.items())),
                "conservation": {"n_accepted": n, "sum_classes": sum(funnel.values()), "sum_intent_status": sum(intents.values())},
            },
            "funnel_x_intent_status": cross,
            "intent_status": {status: intents.get(status, 0) for status in INTENT_STATUSES},
            "number_one": number_one,
            "number_two": number_two,
            "number_three": number_three,
            "mislock": mislock,
            "explicit_report": explicit_report,
            "samples": [self.sample_record(s) for s in samples],
        }

    @staticmethod
    def _conserved(name: str, total: int, parts: Mapping[str, int]) -> dict[str, Any]:
        if sum(parts.values()) != total:
            raise ConservationError(f"{name}：按真值来源分列之和 {sum(parts.values())} ≠ 原始 n {total}")
        return {"n_raw_total": total, "sum_by_truth_source": sum(parts.values()), "by_truth_source": dict(parts)}

    def _number_one_tables(self, by_source: Mapping[str, list[Sample]]) -> dict[str, Any]:
        def _one_rates(counts: Mapping[str, int]) -> dict[str, Any]:
            rc = counts.get("RESOLVED_CORRECT", 0)
            rw = counts.get("RESOLVED_WRONG", 0)
            ne = sum(v for k, v in counts.items() if k.startswith("NOT_EVALUABLE"))
            censored = counts.get("CENSORED", 0)
            total = sum(counts.values())
            return {"conditional_RC_over_RC_RW": rate(rc, rc + rw), "overall": rate(rc, total - ne - censored)}

        tables: dict[str, Any] = {}
        parts: dict[str, int] = {}
        for source, group in by_source.items():
            counts = Counter()
            buckets: dict[str, Counter] = defaultdict(Counter)
            for sample in group:
                outcome = sample.numbers["number_one"]
                if outcome is None:
                    continue
                key = label(outcome[0], outcome[1:])
                counts[key] += 1
                buckets[delta_bucket(sample.delta_eff_s)][key] += 1
            parts[source] = sum(counts.values())
            tables[source] = {
                "n_raw": parts[source],
                "counts": dict(sorted(counts.items())),
                "rates": _one_rates(counts),
                "by_delta_eff_bucket": {
                    bucket: {**bucket_entry(c), "rates": _one_rates(c)} for bucket, c in sorted(buckets.items())
                },
            }
        total = sum(1 for group in by_source.values() for s in group if s.numbers["number_one"] is not None)
        return {"conservation": self._conserved("数字一", total, parts), "by_truth_source": tables}

    def _number_two_tables(self, by_source: Mapping[str, list[Sample]]) -> tuple[dict[str, Any], dict[str, Any]]:
        tables: dict[str, Any] = {}
        mislock_tables: dict[str, Any] = {}
        parts: dict[str, int] = {}
        s_parts: dict[str, int] = {}
        for source, group in by_source.items():
            bound = [s for s in group if s.klass in {"BOUND_DIRECT", "ACQUIRE_PATH"}]
            gate = Counter()
            start_set = []
            for sample in bound:
                verdict = sample.numbers["entry_gate"]
                if verdict is None:
                    start_set.append(sample)
                else:
                    gate[label(verdict[0], verdict[1:])] += 1
            if len(bound) != sum(gate.values()) + len(start_set):
                raise ConservationError("数字二进入 S 前守恒不成立")
            parts[source], s_parts[source] = len(bound), len(start_set)
            windows: dict[str, Any] = {}
            for window in SURVIVAL_WINDOWS_S:
                name = f"W_{int(window)}s"
                outcomes = Counter()
                by_path: dict[str, Counter] = defaultdict(Counter)
                by_axis: dict[str, Counter] = defaultdict(Counter)
                changes = 0
                for sample in start_set:
                    result = sample.numbers["survival"][name]
                    key = result["outcome"] + (f"({result['detail']})" if result.get("detail") else "")
                    outcomes[key] += 1
                    changes += result["pointer_track_changed"]
                    path = "direct" if sample.klass == "BOUND_DIRECT" else "via_acquiring"
                    by_path[path][key] += 1
                    by_axis[sample.numbers["off_axis"][0]][key] += 1
                kept = outcomes.get("KEPT", 0)
                denominator = kept + sum(outcomes.get(k, 0) for k in ("ID_SWITCH", "LOST_BEYOND_BUFFER", "UNRESOLVED_END_MISS"))
                excluded = sum(v for k, v in outcomes.items() if k in {"UNBOUND_START", "CENSORED_END"} or k.startswith("TRUTH_GAP"))
                if len(start_set) != excluded + denominator:
                    raise ConservationError("数字二 |S| = 排除三类 + D 不成立")
                windows[name] = {
                    "n_S": len(start_set),
                    "counts": dict(sorted(outcomes.items())),
                    "survival_KEPT_over_D": rate(kept, denominator),
                    "pointer_track_changed": changes,
                    "by_entry_path": {k: bucket_entry(v) for k, v in sorted(by_path.items())},
                    "by_off_axis_bucket": {k: bucket_entry(v) for k, v in sorted(by_axis.items())},
                }
            tables[source] = {
                "n_raw_bound_samples": len(bound),
                "entry_gate": dict(sorted(gate.items())),
                "n_S": len(start_set),
                "windows": windows,
            }
            mislocked = [s for s in start_set if s.numbers["mislock"]]
            durations = [{"request_id": s.request_id, **s.numbers["mislock_duration"]} for s in mislocked]
            mislock_tables[source] = {
                "n_S": len(start_set),
                "mislock": len(mislocked),
                "mislock_rate": rate(len(mislocked), len(start_set)),
                "mislock_window_partial": sum(1 for s in start_set if s.numbers["mislock_window_partial"]),
                "durations": durations,
                "duration_total_s": sum(d["duration_s"] for d in durations),
            }
        total_bound = sum(1 for g in by_source.values() for s in g if s.klass in {"BOUND_DIRECT", "ACQUIRE_PATH"})
        total_s = sum(1 for g in by_source.values() for s in g if s.numbers["in_S"])
        number_two = {
            "conservation": self._conserved("数字二绑定样本", total_bound, parts),
            "conservation_S": self._conserved("数字二起点集 S", total_s, s_parts),
            "by_truth_source": tables,
            "differences_from_window_outcome": [
                "起点为每个绑定样本的 f_p，而非全部可见帧",
                "身份按意图对象 IoU ≥ 0.3，而非 track_id；指针 track_id 在 ON 帧之间变化只计 pointer_track_changed",
                "序列末端改为观察终点 E",
                "新增 TRUTH_GAP(no_pose|no_pose_ext) 与 TRUTH_GAP(empty_window)（e2 原为抛 EmptyWindow）",
                "其余（漏检段含不可见帧、跨窗口尾延伸、31 帧判据）同原函数",
            ],
        }
        mislock = {"conservation": self._conserved("误锁分母 |S|", total_s, s_parts), "by_truth_source": mislock_tables}
        return number_two, mislock

    def _number_three_tables(self, by_source: Mapping[str, list[Sample]]) -> dict[str, Any]:
        def _three_rates(counts: Mapping[str, int]) -> dict[str, Any]:
            captured = counts.get("CAPTURED", 0)
            total = sum(counts.values())
            ne_all = sum(v for k, v in counts.items() if k.startswith("NOT_EVALUABLE"))
            ne_intent = sum(v for k, v in counts.items() if k in {"NOT_EVALUABLE(no_intent)", "NOT_EVALUABLE(intent_unknown)"})
            return {
                "success": rate(captured, total - counts.get("CENSORED", 0) - ne_all),
                "success_including_censored": rate(captured, total - ne_intent),
            }

        def _durations(values: list[float | None]) -> dict[str, Any]:
            known = [v for v in values if v is not None]
            return {
                "n": len(values),
                "n_without_truth_time": len(values) - len(known),
                "median": statistics.median(known) if known else None,
                "values": values,
            }

        tables: dict[str, Any] = {}
        parts: dict[str, int] = {}
        for source, group in by_source.items():
            counts = Counter()
            by_path: dict[str, Counter] = defaultdict(Counter)
            buckets: dict[str, Counter] = defaultdict(Counter)
            bind: list[float | None] = []
            centers = Counter()
            from_f_p: list[float | None] = []
            from_h: list[float | None] = []
            for sample in group:
                result = sample.numbers["capture"]
                if result is None:
                    continue
                key = result["outcome"] + (f"({result['detail']})" if result.get("detail") else "")
                counts[key] += 1
                path = "direct" if sample.klass == "BOUND_DIRECT" else "via_acquiring"
                by_path[path][key] += 1
                axis, slant = sample.numbers.get("capture_bucket") or ("NO_POSE", "NO_POSE")
                buckets[f"{axis}|{slant}"][key] += 1
                if result["outcome"] == "CAPTURED":
                    bind.append(result.get("time_to_bind_s"))
                    centers[result["center"]] += 1
                    if result["center"] == "CENTERED":
                        from_f_p.append(result["time_to_center_from_f_p_s"])
                        from_h.append(result["time_to_center_from_h_s"])
            parts[source] = sum(counts.values())
            tables[source] = {
                "n_raw": parts[source],
                "counts": dict(sorted(counts.items())),
                "rates": _three_rates(counts),
                "by_entry_path": {k: {**bucket_entry(v), "rates": _three_rates(v)} for k, v in sorted(by_path.items())},
                "by_off_axis_x_slant": {k: bucket_entry(v) for k, v in sorted(buckets.items())},
                "time_to_bind_s": _durations(bind),
                "time_to_center": {
                    "outcomes": {name: centers.get(name, 0) for name in ("CENTERED", "CENTER_NOT_REACHED", "CENTER_CENSORED")},
                    "time_to_center_from_f_p_s": _durations(from_f_p),
                    "time_to_center_from_h_s": _durations(from_h),
                    "definition": "自 f_p 起意图框中心距 (320,240) < 64 px 连续 5 帧的首帧；截止 min(f_p+13 s, E)；仅 CAPTURED；from_h 为并列起点",
                },
            }
        total = sum(1 for g in by_source.values() for s in g if s.numbers["capture"] is not None)
        return {"conservation": self._conserved("数字三", total, parts), "by_truth_source": tables}

    def _explicit_tables(self, by_source: Mapping[str, list[Sample]]) -> dict[str, Any]:
        tables: dict[str, Any] = {}
        for source, group in by_source.items():
            explicit = silent = undeterminable = 0
            aside = Counter()
            invalid_intent_explicit = Counter()
            for sample in group:
                capture = sample.numbers["capture"]
                capture_outcome = None if capture is None else capture["outcome"]
                is_explicit = sample.klass in EXPLICIT_CLASSES or capture_outcome == "ACQUIRE_FAILED"
                if sample.intent_status != "valid":
                    if is_explicit:
                        invalid_intent_explicit[sample.klass] += 1
                    aside[f"intent:{sample.intent_status}"] += 1
                    continue
                if sample.klass in EXPLICIT_RATIO_SET_ASIDE:
                    aside[sample.klass] += 1
                    continue
                one_value = sample.numbers["number_one"]
                is_silent = (one_value is not None and one_value[0] == "RESOLVED_WRONG") or capture_outcome == "WRONG_CAPTURE"
                if is_explicit:
                    explicit += 1
                elif is_silent:
                    silent += 1
                elif self.layout_excluded(sample) and sample.klass in {"BOUND_DIRECT", "ACQUIRE_PATH"}:
                    undeterminable += 1
            tables[source] = {
                "explicit": explicit,
                "silent_error": silent,
                "ratio_explicit_over_explicit_plus_silent": rate(explicit, explicit + silent),
                "set_aside": dict(sorted(aside.items())),
                "invalid_intent_explicit_classes": dict(sorted(invalid_intent_explicit.items())),
                "silent_undeterminable_layout": undeterminable,
            }
        samples = [s for group in by_source.values() for s in group]
        designations = [s.designation for s in samples if s.designation is not None and not s.conflicts]
        six = Counter(str(d.get("result")) for d in designations)
        acquire_failed = sum(1 for s in samples if s.acquire_failed is not None and not s.conflicts)
        acq_explicit = sum(six.get(r, 0) for r in DESIGNATE_REPORTED_RESULTS) + acquire_failed
        return {
            "funnel_scope_by_truth_source": tables,
            "acq_3_10_scope": {
                "truth_used": False,
                "note": "只用运行时六值去向与 acquire_failed，不涉真值，故不按真值来源分列",
                "n_designations": len(designations),
                "six_value_distribution": dict(sorted(six.items())),
                "acquire_failed": acquire_failed,
                "explicit_over_designations": rate(acq_explicit, len(designations)),
            },
        }

    def sample_record(self, sample: Sample) -> dict[str, Any]:
        arrived = sample.result_arrived[0] if sample.result_arrived else {}
        presented = sample.presented or sample.failure or {}
        model = presented.get("model") or {}
        numbers = sample.numbers
        one = numbers.get("number_one")
        gate = numbers.get("entry_gate")
        return {
            "request_id": sample.request_id,
            "action": sample.action,
            "epoch": sample.epoch,
            "intent": sample.intent,
            "intent_status": sample.intent_status,
            "truth_source": numbers.get("truth_source"),
            "delay_s": sample.delay_s,
            "funnel": label(sample.klass, sample.args),
            "attempt_statuses": [a.get("status") for a in sample.attempts],
            "vlm_status_at_arrival": arrived.get("status"),
            "finish_reason": model.get("finish_reason"),
            "parse_error": presented.get("parse_error"),
            "designation_result": (sample.designation or {}).get("result"),
            "acquire_failed_cause": (sample.acquire_failed or {}).get("cause"),
            "delay_injected_s": sample.delay_injected_s,
            "delta_eff_s": sample.delta_eff_s,
            "worker_abandoned": sample.worker_abandoned,
            "k": sample.k,
            "h": sample.h,
            "E": sample.e_frame,
            "f_p": sample.f_p,
            "pointer_epochs": [
                {k: epoch.get(k) for k in ("track_id", "library_track_id", "start_frame", "end_frame", "pointer_bound_row")}
                for epoch in sample.pointer_epochs
            ],
            "number_one": None if one is None else label(one[0], one[1:]),
            "number_two_entry_gate": None if gate is None else label(gate[0], gate[1:]),
            "survival": {
                name: result["outcome"] + (f"({result['detail']})" if result.get("detail") else "")
                for name, result in (numbers.get("survival") or {}).items()
            },
            "mislock": numbers.get("mislock"),
            "mislock_duration": numbers.get("mislock_duration"),
            "capture": numbers.get("capture"),
        }


def score_archive(
    paths: ArchivePaths,
    *,
    geometry: Mapping[str, Any] | None = None,
    geometry_loader: Callable[[], Mapping[str, Any]] = default_geometry_loader,
) -> dict[str, Any]:
    archive = Archive(paths, geometry=geometry, geometry_loader=geometry_loader)
    report = Scorer(archive).run()
    report["inputs"] = {
        "session_dir": str(paths.session_dir),
        "unity_dir": str(paths.unity_dir),
        "scenario_copy": None if paths.scenario_copy is None else str(paths.scenario_copy),
        "reference_scenario": str(paths.reference_scenario),
        "files_sha256": archive.input_files,
        "geometry_source_scenario_sha256": archive.geometry.get("source_scenario_sha256"),
    }
    return report


# --- §3.6 B/C 派生 -----------------------------------------------------------


def synthetic_centered_sidecar(position: Sequence[float], target: Sequence[float], sensor: Mapping[str, Any]) -> dict[str, Any]:
    """从位姿对目标合成居中相机（Unity 左手系约定：right = up_world × forward）。"""
    fx_, fy_, fz_ = (float(target[i]) - float(position[i]) for i in range(3))
    norm = math.sqrt(fx_ * fx_ + fy_ * fy_ + fz_ * fz_)
    forward = (fx_ / norm, fy_ / norm, fz_ / norm)
    right = (forward[2], 0.0, -forward[0])  # (0,1,0) × forward 的分量形式
    r_norm = math.hypot(right[0], right[2])
    right = (right[0] / r_norm, 0.0, right[2] / r_norm)
    up = (
        forward[1] * right[2] - forward[2] * right[1],
        forward[2] * right[0] - forward[0] * right[2],
        forward[0] * right[1] - forward[1] * right[0],
    )
    width, height = int(sensor["width"]), int(sensor["height"])
    vfov = float(sensor["vertical_fov_deg"])
    focal = (height / 2.0) / math.tan(math.radians(vfov) / 2.0)
    return {
        "camera_position_world_m": list(position),
        "camera_forward_world": list(forward),
        "camera_right_world": list(right),
        "camera_up_world": list(up),
        "intrinsics_px": {"fx": focal, "fy": focal, "cx": width / 2.0, "cy": height / 2.0},
        "width": width,
        "height": height,
        "vertical_fov_deg": vfov,
    }


_VARIANT_TOKEN = re.compile(r"^color\d+$")


def describe_vehicle(name: str, canonical: str | None) -> str:
    """只由对象名派生的文字描述（不用真值）：`Vehicle_Car_Taxi (2)` → `the car taxi`。"""
    base = (canonical or name).split(" (")[0]
    tokens = [t for t in base.replace("-", "_").split("_") if t and t.lower() not in {"vehicle", "veh"}]
    words: list[str] = []
    for token in tokens:
        part = ""
        for char in token:
            if char.isupper() and part and not part[-1].isupper():
                words.append(part)
                part = char
            else:
                part += char
        if part:
            words.append(part)
    kept = [w.lower() for w in words if not w.isdigit() and not _VARIANT_TOKEN.match(w.lower())]
    return "the " + " ".join(kept)


def name_variant_tokens(name: str, canonical: str | None) -> list[str]:
    """对象名里的 `colorNN` 等变体编号：不是颜色名，不能派生颜色，只原样列出。"""
    base = (canonical or name).split(" (")[0]
    return [t for t in base.split("_") if _VARIANT_TOKEN.match(t.lower())]


def derive_bc(scenario: Mapping[str, Any], geometry: Mapping[str, Any]) -> dict[str, Any]:
    anchor = scenario["anchor_world_m"]
    altitude = float(scenario["drone"]["initial_altitude_m"])
    limit = float(scenario["gimbal"]["maximum_off_nadir_deg"])
    position = (float(anchor["x"]), float(anchor["y"]) + altitude, float(anchor["z"]))
    instances = list(geometry["instances"])
    pool = []
    for instance in instances:
        if instance.get("group") != "vehicle":
            continue
        cx, cz = bind_layout.xz_center(instance)
        distance = math.hypot(cx - position[0], cz - position[2])
        if distance > BC_POOL_RADIUS_M:
            continue
        center = (cx, (instance["min_y_m"] + instance["max_y_m"]) / 2.0, cz)
        sidecar = synthetic_centered_sidecar(position, center, scenario["sensor"])
        camera = project_boxes.Camera.from_sidecar(sidecar)
        forward = sidecar["camera_forward_world"]
        off_nadir = math.degrees(math.acos(max(-1.0, min(1.0, -float(forward[1])))))
        projected = {p.object_id: p for p in project_boxes.project_instances(camera, instances)}
        status = projected[instance["scene_object_name"]].status
        pool.append(
            {
                "scene_object_name": instance["scene_object_name"],
                "canonical_name": instance.get("canonical_name"),
                "xz_distance_m": round(distance, 3),
                "off_nadir_deg": round(off_nadir, 2),
                "projection_status": status,
                "eligible": off_nadir <= limit and status == "OK",
            }
        )
    pool.sort(key=lambda row: row["xz_distance_m"])
    eligible = [row for row in pool if row["eligible"]]
    chosen = eligible[:2]
    return {
        "schema": BC_SCHEMA,
        "start_pose": {"camera_position_world_m": list(position), "anchor_world_m": dict(anchor), "initial_altitude_m": altitude},
        "pool_radius_m": BC_POOL_RADIUS_M,
        "maximum_off_nadir_deg": limit,
        "pool": pool,
        "status": "OK" if len(chosen) == 2 else "BC_DERIVATION_LT_2",
        "B": None if len(chosen) < 1 else {**chosen[0], "description": describe_vehicle(chosen[0]["scene_object_name"], chosen[0]["canonical_name"]), "name_variant_tokens": name_variant_tokens(chosen[0]["scene_object_name"], chosen[0]["canonical_name"])},
        "C": None if len(chosen) < 2 else {**chosen[1], "description": describe_vehicle(chosen[1]["scene_object_name"], chosen[1]["canonical_name"]), "name_variant_tokens": name_variant_tokens(chosen[1]["scene_object_name"], chosen[1]["canonical_name"])},
    }


# --- archive-dryrun（A6 确认性试读，描述、不作验收） ---------------------------


def _verdict(observed: Any, expected: Any, *, tolerance: float | None = None) -> str:
    if tolerance is not None and isinstance(observed, (int, float)) and isinstance(expected, (int, float)):
        return "一致" if abs(float(observed) - float(expected)) <= tolerance else "不一致"
    return "一致" if observed == expected else "不一致"


def _item(name: str, observed: Any, expected: Any, source: str, *, tolerance: float | None = None, note: str | None = None) -> dict[str, Any]:
    entry = {"item": name, "observed": observed, "contract": expected, "source": source, "verdict": _verdict(observed, expected, tolerance=tolerance)}
    if note:
        entry["note"] = note
    return entry


def _pool_names(scenario: Mapping[str, Any], geometry: Mapping[str, Any]) -> list[str]:
    anchor = scenario["anchor_world_m"]
    names = []
    for instance in geometry["instances"]:
        if instance.get("group") != "vehicle":
            continue
        cx, cz = bind_layout.xz_center(instance)
        if math.hypot(cx - float(anchor["x"]), cz - float(anchor["z"])) <= BC_POOL_RADIUS_M:
            names.append(instance["scene_object_name"])
    return sorted(names)


def projection_readout(
    sidecar_dir: Path,
    truth: Mapping[int, Mapping[str, Any]],
    geometry: Mapping[str, Any],
    pool: Sequence[str],
) -> dict[str, Any]:
    """静止车投影试读（描述）：全几何 + 红车遮挡体；另列「只以车辆为遮挡体」。"""
    store = SidecarStore(sidecar_dir)
    instances = list(geometry["instances"])
    vehicles = [i for i in instances if i.get("group") == "vehicle"]
    full: dict[str, Counter] = {name: Counter() for name in pool}
    vehicles_only_ok: Counter = Counter()
    frames = store.frame_ids()
    position_ok = 0
    red_pixel_errors = []
    for frame_id in frames:
        sha_doc = store.get(frame_id)
        if sha_doc is None:
            continue
        _sha, doc = sha_doc
        camera = project_boxes.Camera.from_sidecar(doc)
        row = truth.get(frame_id)
        blockers: list[tuple[str, Any, float]] = []
        if row is not None:
            body = (row["body_world_x_m"], row["body_world_y_m"], row["body_world_z_m"])
            if all(abs(float(p) - float(b)) <= POSITION_TOLERANCE_M for p, b in zip(doc["camera_position_world_m"], body)):
                position_ok += 1
            if row.get("truth_box_available"):
                box = [row["truth_box_x"], row["truth_box_y"], row["truth_box_width"], row["truth_box_height"]]
                target = (float(row["target_world_x_m"]), float(row["target_world_y_m"]), float(row["target_world_z_m"]))
                cam_point = camera.to_camera_space(target)
                blockers = [(RED_CAR, project_boxes.denormalize_xywh(box, camera), cam_point[2])]
                if cam_point[2] > 0:
                    u, v = camera.project_camera_point(cam_point)
                    center_x = row.get("truth_center_x_px", (float(box[0]) + float(box[2]) / 2.0) * camera.width)
                    center_y = row.get("truth_center_y_px", (float(box[1]) + float(box[3]) / 2.0) * camera.height)
                    red_pixel_errors.append(math.hypot(u - float(center_x), v - float(center_y)))
        projected = {p.object_id: p for p in project_boxes.project_instances(camera, instances, extra_blockers=blockers)}
        for name in pool:
            full[name][projected[name].status] += 1
        for p in project_boxes.project_instances(camera, vehicles, extra_blockers=blockers):
            if p.status == "OK":
                vehicles_only_ok[p.object_id] += 1
    return {
        "frames": len(frames),
        "frame_range": [frames[0], frames[-1]] if frames else None,
        "pool_status_full_geometry": {name: dict(counter) for name, counter in full.items()},
        "vehicles_only_blockers_ok_frames": dict(sorted(vehicles_only_ok.items())),
        "camera_position_vs_truth_body_le_1e-3": [position_ok, len(frames)],
        "red_car_projection_vs_truth_center_px": {
            "n": len(red_pixel_errors),
            "median": statistics.median(red_pixel_errors) if red_pixel_errors else None,
        },
        "metadata_binding": "metadata_unbound（旧归档无运行时元数据摘要，F25）",
    }


def _dir_jpeg_stats(directory: Path) -> dict[str, Any]:
    files = sorted(directory.glob("frame_*.jpg"))
    ids = [int(p.stem.split("_", 1)[1]) for p in files]
    return {"count": len(files), "bytes": sum(p.stat().st_size for p in files), "range": [ids[0], ids[-1]] if ids else None, "ids": set(ids)}


def archive_dryrun(
    attempt2_session: Path,
    attempt2_unity: Path,
    frame001_run: Path,
    *,
    reference_scenario: Path,
    untethered_scenario: Path,
    geometry: Mapping[str, Any],
) -> dict[str, Any]:
    scenario = json.loads(Path(untethered_scenario).read_text(encoding="utf-8"))
    pool = _pool_names(scenario, geometry)
    vehicles = [i["scene_object_name"] for i in geometry["instances"] if i.get("group") == "vehicle"]
    items: list[dict[str, Any]] = []
    items.append(_item("几何车辆数 / 重名数", [len(vehicles), len(vehicles) - len(set(vehicles))], [101, 0], "F24/F27"))
    items.append(_item("锚点 xz 40 m 内车辆数", len(pool), 6, "F24/F27"))

    # --- attempt 2 ---
    a2: dict[str, Any] = {}
    unity_frames = Path(attempt2_unity) / "frames"
    ring = _dir_jpeg_stats(unity_frames)
    sidecar_ids = SidecarStore(unity_frames).frame_ids()
    items.append(_item("attempt2 Unity 帧环 JPEG 数/字节", [ring["count"], ring["bytes"]], [1500, 124914153], "F22"))
    items.append(_item("attempt2 Unity 帧环范围", ring["range"], [1512, 3011], "F22"))
    items.append(_item("attempt2 旁车数", len(sidecar_ids), 1500, "F22"))
    truth_rows = read_jsonl(Path(attempt2_unity) / "m3_body_truth.jsonl")
    truth = {}
    for row in truth_rows:
        truth.setdefault(int(row["frame_id"]), row)
    items.append(_item("attempt2 真值行数/帧范围", [len(truth_rows), min(truth), max(truth)], [3012, 0, 3011], "F22"))
    items.append(_item("attempt2 truth_box_available 行数", sum(1 for r in truth_rows if r.get("truth_box_available")), 1294, "F22"))
    journal = read_jsonl(Path(attempt2_session) / "language-session.jsonl")
    receipts = read_jsonl(Path(attempt2_session) / "publish-receipts.jsonl")
    results = read_jsonl(Path(attempt2_session) / "results.jsonl")
    kinds = Counter(r.get("kind") for r in journal)
    items.append(_item("attempt2 会话 JSONL 行数", len(journal), 1009, "F22/§8"))
    items.append(
        _item(
            "attempt2 会话 JSONL kind 分布（frames_processed/state/receipt/query_*/designation/pointer_bound/resident_loop_*）",
            [
                kinds["frames_processed"],
                kinds["state"],
                kinds["receipt"],
                kinds["query_submitted"] + kinds["query_started"],
                kinds["designation"],
                kinds["pointer_bound"],
                kinds["resident_loop_started"] + kinds["resident_loop_closed"],
            ],
            [941, 19, 16, 14, 2, 2, 4],
            "§8",
        )
    )
    channels = Counter(r.get("channel") for r in receipts)
    items.append(
        _item(
            "attempt2 publish-receipts 行数与通道（body_safety_hold/observation/look_at/body_command）",
            [len(receipts), channels["body_safety_hold"], channels["observation"], channels["look_at"], channels["body_command"]],
            [1556, 862, 307, 307, 80],
            "F22",
        )
    )
    session_ring = _dir_jpeg_stats(Path(attempt2_session) / "frames")
    session_sidecars = len(list((Path(attempt2_session) / "frames").glob("frame_*.json")))
    items.append(_item("attempt2 会话帧环 JPEG 数/字节/范围/旁车数", [session_ring["count"], session_ring["bytes"], session_ring["range"], session_sidecars], [961, 49575497, [0, 960], 0], "F22"))
    statuses = Counter(r.get("status") for r in results)
    sha_match = 0
    for r in results:
        if r.get("frame_id") is None:
            continue
        path = Path(attempt2_session) / "frames" / f"frame_{int(r['frame_id']):010d}.jpg"
        if path.exists() and sha256_file(path) == r.get("frame_sha256"):
            sha_match += 1
    items.append(_item("attempt2 results.jsonl 行数 / 全部 ambiguous / frame_sha256 与会话帧环相符", [len(results), statuses.get("ambiguous", 0), sha_match], [7, 7, 7], "§8"))
    segment_dirs = _segment_dirs(Path(attempt2_unity) / "runs", None)
    seg_counts = {d.name: sum(1 for _ in (d / "frames.jsonl").open()) for d in segment_dirs}
    items.append(_item("attempt2 段日志行数（resident1/resident2）", sorted(seg_counts.values(), reverse=True), [901, 61], "F22"))
    session_frames = {int(f) for row in journal if row.get("kind") == "frames_processed" for f in row.get("frame_ids") or []}
    seg_rows: dict[int, dict[str, Any]] = {}
    for d in segment_dirs:
        for row in read_jsonl(d / "frames.jsonl"):
            seg_rows.setdefault(int(row["frame_id"]), row)
    session_window = set(session_ring["ids"])
    items.append(
        _item(
            "attempt2 帧交集：会话∩真值 / 会话∩Unity 帧环 / 三者",
            [len(session_window & set(truth)), len(session_window & ring["ids"]), len(session_window & set(truth) & ring["ids"])],
            [961, 0, 0],
            "F23",
            note=f"会话窗口取会话帧环 0–960；frames_processed 报告帧 {len(session_frames)} 个",
        )
    )
    time_equal = sum(
        1
        for f, row in seg_rows.items()
        if f in truth
        and row.get("simulation_time_s") == truth[f].get("simulation_time_s")
        and row.get("capture_monotonic_s") == truth[f].get("capture_monotonic_s")
    )
    items.append(_item("attempt2 段日志 simulation_time_s/capture_monotonic_s 与真值逐值相等（全量）", [time_equal, len(seg_rows)], [len(seg_rows), len(seg_rows)], "F23（D2 抽 5 帧）"))
    ious = []
    for f, row in seg_rows.items():
        t = truth.get(f)
        if row.get("ok") is True and row.get("box_norm") is not None and t is not None and t.get("truth_box_available"):
            ious.append(iou_xywh(row["box_norm"], [t["truth_box_x"], t["truth_box_y"], t["truth_box_width"], t["truth_box_height"]]))
    items.append(
        _item(
            "attempt2 红车离线 IoU（n / 中位 / 最小）",
            [len(ious), round(statistics.median(ious), 3) if ious else None, round(min(ious), 3) if ious else None],
            [307, 0.902, 0.646],
            "F23",
        )
    )
    items.append(
        _item("attempt2 会话窗口内红车真值可见帧", sum(1 for f in session_window if truth.get(f, {}).get("truth_box_available")), 545, "§8")
    )
    digests = [row.get("metadata_sha256") for row in journal if row.get("kind") == "frames_processed"]
    items.append(_item("attempt2 frames_processed 带 metadata_sha256 的行数", sum(1 for d in digests if d is not None), 0, "F25"))
    a2_projection = projection_readout(unity_frames, truth, geometry, pool)
    a2_status = {name: dict(c) for name, c in a2_projection["pool_status_full_geometry"].items()}
    observed_shape = sorted(
        "EXCLUDED_OCCLUDED_all" if c == {"EXCLUDED_OCCLUDED": len(sidecar_ids)} else ("NOT_IN_VIEW_all" if c == {"NOT_IN_VIEW": len(sidecar_ids)} else "other")
        for c in a2_status.values()
    )
    items.append(
        _item(
            "attempt2 Unity 帧环 6 辆池内车状态（全几何 + 红车遮挡体）",
            observed_shape,
            sorted(["NOT_IN_VIEW_all"] * 5 + ["EXCLUDED_OCCLUDED_all"]),
            "F27/§8",
        )
    )
    items.append(_item("attempt2 旁车相机位置 vs 真值机身 ≤1e-3 m", a2_projection["camera_position_vs_truth_body_le_1e-3"], [1500, 1500], "F25"))
    a2_red = a2_projection["red_car_projection_vs_truth_center_px"]["median"]
    pool_ok_vehicles_only = {k: v for k, v in a2_projection["vehicles_only_blockers_ok_frames"].items()}
    a2["projection"] = {**a2_projection, "pool_status_full_geometry": a2_status, "vehicles_only_blockers_ok_frames": pool_ok_vehicles_only}
    a2_manifests = [json.loads((d / "manifest.json").read_text(encoding="utf-8")) for d in segment_dirs]
    a2["layout_binding_formal"] = layout_binding(None, a2_manifests, reference_scenario, geometry)
    a2["manifest_body_planner_keys"] = [sorted((m.get("body_planner") or {}).keys()) for m in a2_manifests]
    items.append(_item("attempt2 布局绑定（归档无场景副本）", a2["layout_binding_formal"]["status"], "layout_unbound", "§3.5.1/F26", note="threshold 段 manifest 无 effective_scenario_sha256"))
    # 漏斗（旧归档无 intent → 全部 no_intent，事实不是错误）。
    report = score_archive(
        ArchivePaths(session_dir=Path(attempt2_session), unity_dir=Path(attempt2_unity), scenario_copy=None, reference_scenario=reference_scenario),
        geometry=geometry,
    )
    a2["score_summary"] = {
        key: report[key]
        for key in (
            "funnel",
            "funnel_x_intent_status",
            "intent_status",
            "attribution_conflicts",
            "unattributed_rows",
            "duplicate_event_rows",
            "duplicate_frame_rows",
            "frame_identity_mismatch",
            "result_frame_sha256_checks",
            "command_invalid",
            "layout_binding",
        )
    }
    a2["score_samples"] = report["samples"]
    a2["score_number_tables_n"] = {
        source: {
            "number_one": report["number_one"]["by_truth_source"][source]["counts"],
            "number_two_entry_gate": report["number_two"]["by_truth_source"][source]["entry_gate"],
            "number_three": report["number_three"]["by_truth_source"][source]["counts"],
            "mislock_n_S": report["mislock"]["by_truth_source"][source]["n_S"],
            "explicit_report_funnel_scope": report["explicit_report"]["funnel_scope_by_truth_source"][source],
        }
        for source in TRUTH_SOURCES
    }
    a2["score_number_tables_n"]["acq_3_10_scope"] = report["explicit_report"]["acq_3_10_scope"]
    a2["score_frame_time_source"] = report["frame_time_source"]
    items.append(_item("attempt2 受理样本全部 no_intent", report["intent_status"], {"valid": 0, "no_intent": report["funnel"]["n_accepted"], "intent_unknown": 0}, "§3.5.1"))

    # --- FRAME-001 play-2 ---
    f1: dict[str, Any] = {}
    run = Path(frame001_run)
    f1_seg = read_jsonl(run / "frames.jsonl")
    f1_truth_rows = read_jsonl(run / "m3_body_truth.jsonl")
    f1_truth = {}
    for row in f1_truth_rows:
        f1_truth.setdefault(int(row["frame_id"]), row)
    meta_dir = run / "retained_frame_metadata"
    f1_sidecars = SidecarStore(meta_dir).frame_ids()
    f1_images = sorted((run / "retained_frame_images").glob("frame_*.jpg"))
    items.append(_item("FRAME-001 段日志/真值/旁车/图像数", [len(f1_seg), len(f1_truth_rows), len(f1_sidecars), len(f1_images)], [1366, 1390, 128, 128], "§8"))
    items.append(_item("FRAME-001 旁车帧范围", [f1_sidecars[0], f1_sidecars[-1]] if f1_sidecars else None, [1262, 1389], "§8"))
    items.append(_item("FRAME-001 会话 JSONL 存在", (run / "language-session.jsonl").exists(), False, "§8"))
    f1_projection = projection_readout(meta_dir, f1_truth, geometry, pool)
    f1_shape = sorted("NOT_IN_VIEW_all" if c == {"NOT_IN_VIEW": len(f1_sidecars)} else "other" for c in f1_projection["pool_status_full_geometry"].values())
    items.append(_item("FRAME-001 6 辆池内车 × 128 帧状态", f1_shape, ["NOT_IN_VIEW_all"] * 6, "F27/§8"))
    items.append(_item("FRAME-001 旁车相机位置 vs 真值机身 ≤1e-3 m", f1_projection["camera_position_vs_truth_body_le_1e-3"], [128, 128], "F25"))
    f1_red = f1_projection["red_car_projection_vs_truth_center_px"]["median"]
    red_pair = sorted(round(v, 1) for v in (a2_red, f1_red) if v is not None)
    items.append(
        _item(
            "红车真值世界点投影 vs 真值框中心像素差中位（两归档，无序比对）",
            red_pair,
            [5.5, 6.4],
            "F27",
            note=f"F27 只写「5.5/6.4 px（两归档）」未标明对应归档；实测 attempt2 {None if a2_red is None else round(a2_red, 1)} / FRAME-001 {None if f1_red is None else round(f1_red, 1)}",
        )
    )
    f1_manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    untethered_sha = sha256_file(Path(untethered_scenario))
    items.append(
        _item(
            "FRAME-001 manifest effective_scenario_sha256 = untethered 当前 sha",
            (f1_manifest.get("body_planner") or {}).get("effective_scenario_sha256") == untethered_sha,
            True,
            "F26",
        )
    )
    f1["layout_binding_formal"] = layout_binding(None, [f1_manifest], reference_scenario, geometry)
    items.append(_item("FRAME-001 布局绑定（归档无场景副本）", f1["layout_binding_formal"]["status"], "layout_unbound", "§3.5.1"))
    items.append(
        _item(
            "两归档旁车位置一致合计",
            [a2_projection["camera_position_vs_truth_body_le_1e-3"][0] + f1_projection["camera_position_vs_truth_body_le_1e-3"][0],
             a2_projection["camera_position_vs_truth_body_le_1e-3"][1] + f1_projection["camera_position_vs_truth_body_le_1e-3"][1]],
            [1628, 1628],
            "F25/§8",
        )
    )
    f1["projection"] = f1_projection
    a2_always = sorted(k for k, v in a2_projection["vehicles_only_blockers_ok_frames"].items() if v == a2_projection["frames"])
    items.append(
        _item(
            "只以车辆（+红车）为遮挡体：attempt2 Unity 帧环全部帧恒 OK 的车辆数",
            len(a2_always),
            6,
            "§8 D3「6 辆恒 OK」",
            note=f"恒 OK 车辆：{a2_always}；§8「末段静止机位」与遮挡体集合口径未写清（本读法含红车遮挡体）",
        )
    )
    a2_ok = set(a2_projection["vehicles_only_blockers_ok_frames"])
    f1_ok = set(f1_projection["vehicles_only_blockers_ok_frames"])
    items.append(
        _item(
            "只以车辆（+红车）为遮挡体：出现过 OK 的车辆数 attempt2 / FRAME-001 / 两者并集中位于 40 m 池内者",
            [len(a2_ok), len(f1_ok), len((a2_ok | f1_ok) & set(pool))],
            [7, 6, 1],
            "§8 D3",
            note="§8「6 辆恒 OK」「末段静止机位」口径未写清，此处只比对出现过 OK 的车辆数",
        )
    )
    f1_metadata_digest_files = [p.name for p in meta_dir.iterdir() if not p.name.startswith("frame_")] if meta_dir.exists() else []
    items.append(_item("FRAME-001 retained_frame_metadata 摘要/索引文件", f1_metadata_digest_files, [], "F25"))
    a2_index_files = [p.name for p in unity_frames.iterdir() if not p.name.startswith("frame_") and p.name != "latest.json"]
    items.append(_item("attempt2 Unity 帧环摘要/索引文件（latest.json 除外）", a2_index_files, [], "F25"))

    # B/C 合成居中（与 F27 对照）
    bc = derive_bc(scenario, geometry)
    le45 = sorted(row["off_nadir_deg"] for row in bc["pool"] if row["off_nadir_deg"] <= float(scenario["gimbal"]["maximum_off_nadir_deg"]))
    items.append(_item("合成居中：6 辆投影状态全 OK", all(row["projection_status"] == "OK" for row in bc["pool"]) and len(bc["pool"]) == 6, True, "F27"))
    items.append(_item("合成居中：离天底角 ≤45° 辆数", len(le45), 2, "F27"))
    items.append(_item("合成居中：≤45° 两辆约 16°/21°", [round(v) for v in le45], [16, 21], "F27", note="按整数度比对"))
    others = sorted(row["off_nadir_deg"] for row in bc["pool"] if row["off_nadir_deg"] > 45.0)
    items.append(_item("合成居中：其余离天底角落在 49°–58°", bool(others) and others[0] >= 49.0 and others[-1] <= 58.99, True, "F27/§8", note=f"实测 {others}"))

    return {
        "schema": DRYRUN_SCHEMA,
        "purpose": "A6 确认性试读（描述、不作验收）；静止车读数一律 metadata_unbound",
        "pool_40m": pool,
        "comparison": items,
        "inconsistent_items": [item["item"] for item in items if item["verdict"] != "一致"],
        "attempt2": a2,
        "frame001_play2": f1,
        "bc_synthetic": bc,
    }


# --- CLI -------------------------------------------------------------------


def _git_head() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        return None


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _provenance(argv: Sequence[str]) -> dict[str, Any]:
    return {"command": "python -m tools.eng_loop2.analyze_play " + " ".join(argv), "generated_at_utc": _now(), "git_head_at_run": _git_head()}


def _json_default(value: Any) -> Any:
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(type(value))


def _write(document: Mapping[str, Any], out: Path | None) -> None:
    text = json.dumps(document, ensure_ascii=False, indent=1, sort_keys=False, default=_json_default) + "\n"
    if out is None:
        sys.stdout.write(text)
    else:
        Path(out).write_text(text, encoding="utf-8")


def _reject_runtime_inputs(paths: Iterable[Path | None]) -> None:
    """§3.5.1：评分时不读 `runtime/` 下任何可变文件。"""
    runtime = (REPO_ROOT / "runtime").resolve()
    for path in paths:
        if path is None:
            continue
        resolved = Path(path).resolve()
        if resolved == runtime or runtime in resolved.parents:
            raise AnalyzeError(f"评分输入不得位于 runtime/：{path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="analyze_play", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    score = sub.add_parser("score", help="§3.5 四类数字（正式归档）")
    score.add_argument("--session-dir", type=Path, required=True)
    score.add_argument("--unity-dir", type=Path, required=True)
    score.add_argument("--runs-dir", type=Path, default=None)
    score.add_argument("--scenario-copy", type=Path, default=None, help="归档内本会话生效场景副本")
    score.add_argument("--reference-scenario", type=Path, default=REPO_ROOT / "config" / "scenario.default.json")
    score.add_argument("--out", type=Path, default=None)
    dry = sub.add_parser("archive-dryrun", help="A6 对两份既有归档的确认性试读")
    dry.add_argument("--attempt2-session", type=Path, default=REPO_ROOT / "outputs/eng-acq/P1-ENG-ACQ-001/play-d1/sessions/acq-d1-2")
    dry.add_argument("--attempt2-unity", type=Path, default=REPO_ROOT / "outputs/eng-acq/P1-ENG-ACQ-001/play-d1/acq-d1-2/unity-runtime")
    dry.add_argument("--frame001-run", type=Path, default=REPO_ROOT / "runtime/runs/p1-eng-frame-001-play-2")
    dry.add_argument("--reference-scenario", type=Path, default=REPO_ROOT / "config" / "scenario.default.json")
    dry.add_argument("--untethered-scenario", type=Path, default=REPO_ROOT / "config" / "scenario.untethered.json")
    dry.add_argument("--out", type=Path, default=None)
    bc = sub.add_parser("derive-bc", help="§3.6 B/C 派生")
    bc.add_argument("--scenario", type=Path, default=REPO_ROOT / "config" / "scenario.untethered.json")
    bc.add_argument("--out", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    if args.command == "score":
        _reject_runtime_inputs([args.session_dir, args.unity_dir, args.runs_dir, args.scenario_copy, args.reference_scenario])
        report = score_archive(
            ArchivePaths(args.session_dir, args.unity_dir, args.runs_dir, args.scenario_copy, args.reference_scenario)
        )
        _write({"provenance": _provenance(argv), **report}, args.out)
        return 0
    if args.command == "archive-dryrun":
        document = archive_dryrun(
            args.attempt2_session,
            args.attempt2_unity,
            args.frame001_run,
            reference_scenario=args.reference_scenario,
            untethered_scenario=args.untethered_scenario,
            geometry=default_geometry_loader(),
        )
        _write({"provenance": _provenance(argv), **document}, args.out)
        return 0
    scenario = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
    document = derive_bc(scenario, default_geometry_loader())
    _write({"provenance": _provenance(argv), **document}, args.out)
    if document["status"] != "OK":
        print("BC_DERIVATION_LT_2", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
