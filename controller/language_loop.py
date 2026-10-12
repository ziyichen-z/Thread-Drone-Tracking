"""P1-ENG-LOOP-001 §3.3/§3.4/§3.6/§3.8：会话状态机、查询 worker、角色 A/B 与 CLI。

一条链路：操作者 CLI 写 `language_request.json` → 会话取 `latest` 完整 bundle N →
角色 A 查询 → K1 四个检查点 → 候选与预览 → 人 `confirm` → 新段静音 `initialize(N)`
→ 放行 → 追平（每次写桥过发布最终门）→ 角色 B 低频核验只提醒 → 人 `confirm_lost`
/ `respecify` 换新 `track_id`。

VLM 不在控制回路里：核验提醒、`dismiss`、跟踪器 `raw_lost`/`raw_ok` 都**不碰**
发布门；发布门只由播种瞬态（静音→放行）与段 finalize 改变（§3.4 边界表）。

本模块不改 `TrackLoop`、`RuntimePublisher`、观测协议与 `tools/eng_sft/`：段内一切
由注入的 `SnapshotRepository`、`GatedPublisher` 与日志包装器完成。

P1-ENG-CAPTURE-001（`run --language off`，捕获模式）：不读 K 收据、不建适配器与 worker；常驻载体以
`unify_vehicle` + `pose-center` 构造，`controller.target_manager` 逐帧管连续性、修复、预测 look_at 与报告，
动作闭集新增 `click`（图像点击即绑定，不调 VLM、无确认）。`--language on`（缺省，兼容模式）行为保持现状，
唯一变化是指针写入改经 `TargetManager.commit_binding`/`release_binding`（准入与副作用逐条等同现行）。

P1-ENG-ACQ-001（`SessionConfig.resident=True`，缺省关闭，LOOP-001 段式路径逐字不变）：会话启动即建
**单一常驻 `TrackLoop`**（插件 `det-assoc-v1` 常驻模式，`step` 逐帧），「段」改为「指定纪元」记账；
播种不再 `init`、不再回放积压（静音播种退役）；`TRACKING`/`SUSPECTED` 下允许 `ask`/`respecify`（跟踪中
指定），有指针时 `QUERYING`/`AWAITING_CONFIRMATION` 保持发布；`confirm` 走 `designate(box_k, N)` 的六值
闭集（§3.6）；`TRACK_ENDED` 经人确认进入 `ACQUIRING`：世界点转向通道每个 `designation_id` 至多一次、
到位判据、N-of-M 收养，失败回 `hold` 并报 `LOST(acquire_failed)`（§3.7，不自动重试、不自动重播种）。
"""

from __future__ import annotations

import argparse
from collections import deque
import copy
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import platform
import queue
import shutil
import sys
import threading
import time
from typing import Any, Callable, Iterable, Mapping, Sequence
import uuid

from . import language_bridge as bridge
from .gated_publisher import (
    RECEIPTS_FILE,
    SETTLE_DROPPED,
    SETTLE_PUBLISHED,
    FrameIdentityChanged,
    FrameSnapshot,
    FrameSnapshotRing,
    GatedPublisher,
    SnapshotRepository,
    sha256_bytes,
    verify_frame_identity,
)
from .language_bridge import (
    Instruction,
    InstructionUnsupported,
    LanguageBridgeError,
    SessionSlotBusy,
    WriterBusy,
)
from .language_selector import (
    MERGE_EQUIVALENCE_IOU,
    VERIFY_IOU,
    Candidate,
    RawSelection,
    Selection,
    SelectorError,
    sha256_file,
    interpret,
    iou_norm_xywh,
)
from .protocol import atomic_write
from .geolocate import GeometryRejected, box_ground_intersection
from .pose_gmc import project_world_point, rotation_angle_deg
from .protocol import RUNTIME
from .resident_core import (
    AMBIGUOUS as DESIGNATION_AMBIGUOUS,
    BOUND,
    BOUND_COASTING,
    TRACK_ENDED,
    TRACKED as ROW_TRACKED,
    full_kf_state_from_associator,
    library_kf_predictor,
)
from . import target_manager as tmgr
from .run_log import RunLogger
from .track_loop import FrameRepository, RuntimePublisher, TrackLoop, _build_body_runtime
from .trackers import ScriptedTracker, TrackerResult, create_tracker

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# --- AC-10 修订 1 冻结的规则常数 ------------------------------------------

#: 宿主分档阈值（`A` = 合格且 p95 ≤ 该值）。
HOST_TIER_P95_S = 6.0
#: 人工确认预算。
T_CONF_S = 10.0
#: 写桥容差帧数；`T_pub = K_PUB / hz`。
K_PUB = 2
#: 停帧判据与发布年龄上限。
T_STALL_S = 3.0
#: 查询在途硬限。
T_HARD_S = 60.0
#: 核验周期。
T_V_S = 10.0
#: 有界重试上限。
ATTEMPT_LIMIT = 3
#: 连续告警到此值即提醒。
CONSECUTIVE_ALERT = 2
#: 资格式的固定余量：`K_ret + K_conf + K_pub ≤ R − 8`。
QUALIFICATION_MARGIN = 8
#: §3.6：同一触发源的最小间隔。
TRIGGER_RATE_LIMIT_S = 3.0
#: §3.4：`stop` 时 join 在途线程的上限。
WORKER_JOIN_S = 5.0
#: §3.2：CLI 等回执的上限。
RECEIPT_WAIT_S = 5.0
#: CLI 与会话的轮询间隔。
POLL_INTERVAL_S = 0.02

SESSION_JOURNAL = "language-session.jsonl"
RESULTS_FILE = "results.jsonl"

#: 终端 `TrackLoop` 事件 → §3.4 的 `seg_end` 原因。只列本项真正可达的两个：段从不装
#: rate / qualification / re-anchor / body planner，`INVALID_CLOCK`、`REANCHOR_FAIL_CLOSED`、
#: `BODY_COMMAND_FAIL_CLOSED` 都属未启用子系统。它们真的出现时不被静默吸收，而是走
#: AC-4 修订 2 的兜底：原事件逐字记进会话 JSONL 并标 `unexpected_segment_end`，
#: 段按 `metadata_invalid` fail-closed 终止。（坏元数据的正常路径是
#: `repository.load` 抛 `ValueError`，在 `_advance_segment` 就被映射，不经这里。）
#: AC-16 修订 1：核验返回检查失败 → `verify.inconclusive_reason`。按 `_check_return`
#: 的**返回值**取，不按「哪一层失败」取；`verdict` 字面永远只是 `inconclusive`。
VERIFY_RETURN_INCONCLUSIVE: dict[str, str] = {
    "wall_deadline_exceeded": "stale",
    "frames_late_exceeded": "stale",
    "negative_frame_delta": "frame_identity",
    "bundle_missing": "frame_identity",
    "image_identity_changed": "frame_identity",
    "metadata_invalid": "frame_identity",
}

TERMINAL_EVENT_REASONS: dict[str, str] = {
    "GAP": "frame_gap",
    "REINIT_REQUIRED": "frame_rollback",
}

# --- P1-ENG-LOOP-002 阶段 A（K1/K2/K3）-----------------------------------------

#: A1：`run --body-policy` 闭集；缺省 `threshold`（LOOP-001/ACQ-001 路径逐字不变）。
BODY_POLICIES: tuple[str, ...] = ("threshold", "standoff")
#: A4：逐次呈现延迟 Δ 的闭区间（秒）。
DELAY_MIN_S = 0.0
DELAY_MAX_S = 8.0
#: A5：常驻载体每会话至多重建次数；第 3 次需要重建时 → `TERMINAL(rebuild_limit)`。
RESIDENT_REBUILD_LIMIT = 2
#: A5：常驻路径进入 `TERMINAL` 的原因（不重建）。`duration_reached` 与 `backend_fatal` 之外的 `seg_end` 照旧重建。
RESIDENT_TERMINAL_SEG_END = frozenset({"duration_reached"})
#: §3.2：jetson 单宿主收据的宿主名（新路径；`mac`/`5060` 两宿主决策逐字不变）。
JETSON_HOST = "jetson"

#: A3：会话 JSONL 事件名闭集（AC-4）。`_journal` 遇闭集外名字即抛错；核心事件（`drain_events`、
#: `designation.events`）同样经 `_journal` 落盘，故其动态名在此逐个枚举（`resident_core.py` 的
#: `L2_*`/`COASTING_*`，缺 `event` 键时的兜底名 `core_event`）。
CORE_EVENT_KINDS: tuple[str, ...] = (
    "COASTING_RECOVERED",
    "COASTING_TO_TRACK_ENDED",
    "L2_STARTED",
    "L2_FAILED",
    "L2_ADOPTED",
    "L2_AMBIGUOUS",
    "core_event",
)
JOURNAL_KINDS: frozenset[str] = frozenset(
    {
        # LOOP-001 / ACQ-001 既有字面量
        "ILLEGAL_WRITER_SUSPECTED",
        "acquire_adopted",
        "acquire_arrived",
        "acquire_failed",
        "acquire_geometry_rejected",
        "acquire_started",
        "backend_exception",
        "backend_fatal",
        "designate_failed_restore",
        "designation",
        "designation_unavailable",
        "frames_processed",
        "pending_dropped",
        "pointer_bound",
        "preview_unavailable",
        "query_started",
        "query_submitted",
        "receipt",
        "request_unaddressable",
        "resident_loop_closed",
        "resident_loop_started",
        "resident_start_failed",
        "seeding_aborted",
        "segment_retired",
        "segment_seeded",
        "segment_summary_failed",
        "session_lock_replaced",
        "session_started",
        "state",
        "suspect_raised",
        "unexpected_segment_end",
        "verify_pairing_unavailable",
        "verify_skipped",
        "worker_abandoned",
        # P1-ENG-LOOP-002 新事件（A4/A5/§3.2）
        "result_arrived",
        "result_presented",
        "presentation_discarded",
        "resident_rebuild_limit",
        # P1-ENG-CAPTURE-001 §3.8（目标管理器事件，只追加）
        "tm_event",
        "tm_transition",
        "binding_committed",
        "authorization",
        "click_received",
        *CORE_EVENT_KINDS,
        # P1-ENG-FASTFIX-001 §3.2/§3.3/§3.5（只追加）：降级/升级、逐阶段耗时与重捕事件。
        "publish_dropped",
        "publish_escalated",
        "frame_timing",
        "reacquire_started",
        "reacquire_skipped",
        "reacquire_canceled",
        "reacquired_after_rebuild",
        "reacquire_failed",
    }
)
#: FASTFIX：本项追加的事件名（静态检查「只在末尾追加」用；`JOURNAL_KINDS` 是 frozenset，次序以本元组为准）。
FASTFIX_JOURNAL_KINDS: tuple[str, ...] = (
    "publish_dropped",
    "publish_escalated",
    "frame_timing",
    "reacquire_started",
    "reacquire_skipped",
    "reacquire_canceled",
    "reacquired_after_rebuild",
    "reacquire_failed",
)
#: FASTFIX §3.3：管理器重捕事件 → 会话 JSONL 同名事件（`_tm_sink` 逐个字面量分支）。
REACQUIRE_EVENT_KINDS = frozenset(
    {"reacquire_started", "reacquire_skipped", "reacquire_canceled", "reacquired_after_rebuild", "reacquire_failed"}
)

#: P1-ENG-CAPTURE-001 C9：捕获模式（`--language off`）下一律 `REQUEST_INVALID(language_disabled)` 的语言动作。
LANGUAGE_ONLY_ACTIONS = frozenset({"ask", "respecify", "verify", "confirm", "reject", "dismiss"})
#: C2/C1：捕获模式常驻载体的显式构造值（构造器缺省 `per_class`/`pose` 不变）。
CAPTURE_CLASS_POLICY = "unify_vehicle"
CAPTURE_GMC_SOURCE = "pose-center"
#: IR-1：捕获入口显式启用增强历史视图（兼容/缺省工厂保持旧消费视图）。
CAPTURE_HISTORY_VIEW = "capture"


@dataclass(frozen=True)
class LanguageOffTiming:
    """C9：`--language off` 不读 K 收据；`k_pub` 取常量 `K_PUB`，hz 与保留帧数取生效场景。

    只提供会话用到的计时字段与日志 `payload()`；不是 K 收据，不参与任何宿主/模型决策。"""

    hz: float
    retained_frame_count: int
    k_pub: int = K_PUB
    backend: str | None = None
    model_form: str | None = None
    host: str | None = None

    @property
    def t_pub_s(self) -> float:
        return self.k_pub / self.hz

    @property
    def model_identity(self) -> dict[str, Any]:
        return {}

    def payload(self) -> dict[str, Any]:
        return {
            "language": "off",
            "hz": self.hz,
            "retained_frame_count": self.retained_frame_count,
            "k_pub": self.k_pub,
            "t_pub_s": self.t_pub_s,
        }


# --- K 收据与宿主决策（§3.3） ---------------------------------------------


def k_ret_of(p95_s: float, hz: float) -> int:
    return math.ceil(float(p95_s) * float(hz)) + 2


def k_conf_of(hz: float, t_conf_s: float = T_CONF_S) -> int:
    return math.ceil(float(t_conf_s) * float(hz))


def qualifies(p95_s: float, hz: float, retained: int, k_pub: int = K_PUB) -> bool:
    """`K_ret + K_conf + K_pub ≤ R − 8`（§3.3 宿主资格）。"""
    return (
        k_ret_of(p95_s, hz) + k_conf_of(hz) + int(k_pub)
        <= int(retained) - QUALIFICATION_MARGIN
    )


def host_tier(p95_s: float | None, hz: float, retained: int) -> str:
    """先资格后分档（AR2-6）：`A` / `B` / `C` / `FAIL`。"""
    if p95_s is None or not math.isfinite(float(p95_s)):
        return "FAIL"
    if not qualifies(float(p95_s), hz, retained):
        return "C"
    return "A" if float(p95_s) <= HOST_TIER_P95_S else "B"


def decide_host(
    mac_tier: str, mac_p95_s: float | None, gpu_tier: str, gpu_p95_s: float | None
) -> tuple[str, str]:
    """§3.3 宿主决策表。返回 (`mac` / `5060` / `HOST_UNDECIDED`, 理由)。"""
    if mac_tier == "A":
        return "mac", "mac_tier_a"
    if gpu_tier == "A":
        return "5060", "gpu_tier_a"
    if mac_tier == "B" and gpu_tier == "B":
        if mac_p95_s is None or gpu_p95_s is None:
            return "HOST_UNDECIDED", "missing_measurement"
        # 平局取 Mac（单机、无网络）。
        return ("mac", "tie_or_mac_faster") if mac_p95_s <= gpu_p95_s else ("5060", "gpu_faster")
    if mac_tier == "B" and gpu_tier in {"C", "FAIL"}:
        return "mac", "only_mac_qualifies"
    if mac_tier in {"C", "FAIL"} and gpu_tier == "B":
        return "5060", "only_gpu_qualifies"
    return "HOST_UNDECIDED", "neither_host_qualifies"


class ConfigMismatch(LanguageBridgeError):
    """K 收据绑定的 `hz`/`R`/宿主/后端/模型形态与实际不符（§3.3）。"""


@dataclass(frozen=True)
class KReceipt:
    """会话启动读入的 K 收据；任一绑定项变化都不得沿用旧收据（AC-10 修订 1）。"""

    hz: float
    retained_frame_count: int
    p95_s: float
    k_ret: int
    k_conf: int
    k_pub: int
    host: str
    backend: str
    model_form: str
    model_identity: Mapping[str, Any] = field(default_factory=dict)
    scenario_id: str | None = None
    source_reports: Mapping[str, Any] = field(default_factory=dict)

    @property
    def t_ret_s(self) -> float:
        return self.k_ret / self.hz

    @property
    def t_pub_s(self) -> float:
        return self.k_pub / self.hz

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> "KReceipt":
        try:
            receipt = cls(
                hz=float(document["hz"]),
                retained_frame_count=int(document["retained_frame_count"]),
                p95_s=float(document["p95_s"]),
                k_ret=int(document["k_ret"]),
                k_conf=int(document["k_conf"]),
                k_pub=int(document["k_pub"]),
                host=str(document["host"]),
                backend=str(document["backend"]),
                model_form=str(document["model_form"]),
                model_identity=dict(document.get("model_identity", {})),
                scenario_id=document.get("scenario_id"),
                source_reports=dict(document.get("source_reports", {})),
            )
        except (KeyError, TypeError, ValueError) as exception:
            raise ConfigMismatch(f"malformed K receipt: {exception}") from exception
        if receipt.backend not in bridge.BACKENDS:
            raise ConfigMismatch(f"unknown backend {receipt.backend!r}")
        if receipt.model_form not in bridge.MODEL_FORMS:
            raise ConfigMismatch(f"unknown model form {receipt.model_form!r}")
        try:
            # AC-21：`candidates` ⇔ `detector-tracks` 成对；交叉形态的收据不可用。
            bridge.require_backend_model_form(receipt.backend, receipt.model_form)
        except LanguageBridgeError as exception:
            raise ConfigMismatch(f"CONFIG_MISMATCH: {exception}") from exception
        if receipt.backend == bridge.CANDIDATES_BACKEND and (
            not math.isfinite(receipt.p95_s) or receipt.p95_s < 0
        ):
            # AC-21 单宿主收据：`p95_s` 须有限且 ≥ 0（VLM/replay 收据的既有语义不变）。
            raise ConfigMismatch("CONFIG_MISMATCH: candidates K receipt p95_s must be finite and non-negative")
        expected_ret = k_ret_of(receipt.p95_s, receipt.hz)
        expected_conf = k_conf_of(receipt.hz)
        if receipt.k_ret != expected_ret or receipt.k_conf != expected_conf or receipt.k_pub != K_PUB:
            raise ConfigMismatch("K receipt constants disagree with its own p95/hz")
        return receipt

    def payload(self) -> dict[str, Any]:
        return {
            "hz": self.hz,
            "retained_frame_count": self.retained_frame_count,
            "p95_s": self.p95_s,
            "k_ret": self.k_ret,
            "k_conf": self.k_conf,
            "k_pub": self.k_pub,
            "t_ret_s": self.t_ret_s,
            "t_pub_s": self.t_pub_s,
            "t_conf_s": T_CONF_S,
            "t_stall_s": T_STALL_S,
            "host": self.host,
            "backend": self.backend,
            "model_form": self.model_form,
            "model_identity": dict(self.model_identity),
            "scenario_id": self.scenario_id,
            "source_reports": dict(self.source_reports),
            "qualifies": qualifies(self.p95_s, self.hz, self.retained_frame_count),
        }


def build_k_receipt(
    *,
    hz: float,
    retained_frame_count: int,
    p95_s: float,
    host: str,
    backend: str,
    model_form: str,
    model_identity: Mapping[str, Any] | None = None,
    scenario_id: str | None = None,
) -> KReceipt:
    return KReceipt(
        hz=float(hz),
        retained_frame_count=int(retained_frame_count),
        p95_s=float(p95_s),
        k_ret=k_ret_of(p95_s, hz),
        k_conf=k_conf_of(hz),
        k_pub=K_PUB,
        host=host,
        backend=backend,
        model_form=model_form,
        model_identity=dict(model_identity or {}),
        scenario_id=scenario_id,
    )


def effective_scenario_document(runtime: Path, config_path: Path | None = None) -> dict[str, Any]:
    """实际生效的场景文档：`runtime/scenario_config.json` 覆盖版本化缺省。"""
    default = Path(config_path or PROJECT_ROOT / "config" / "scenario.default.json")
    document = json.loads(default.read_text(encoding="utf-8"))
    override = Path(runtime) / "scenario_config.json"
    if override.is_file():
        document = json.loads(override.read_text(encoding="utf-8"))
    return document


def read_scenario(runtime: Path, config_path: Path | None = None) -> dict[str, Any]:
    """实际生效的场景配置：`runtime/scenario_config.json` 覆盖版本化缺省。"""
    document = effective_scenario_document(runtime, config_path)
    sensor = document.get("sensor", {})
    return {
        "scenario_id": document.get("scenario_id"),
        "capture_hz": float(sensor["capture_hz"]),
        "retained_frame_count": int(sensor["retained_frame_count"]),
    }


# --- 查询 worker（§3.4） ---------------------------------------------------


@dataclass(frozen=True)
class QuerySnapshot:
    """查询/返回/确认三个检查点共用的**不可变**帧绑定（AC-2 修订 1）。"""

    frame_id: int
    image_sha256: str
    copy_path: Path
    capture_monotonic_s: float | None
    capture_unix_s: float | None
    snapshot: FrameSnapshot


@dataclass
class QueryJob:
    query_id: str
    purpose: str
    epoch: int
    segment_index: int | None
    verify_epoch: int
    attempt: int
    instruction: Instruction
    frame: QuerySnapshot
    submitted_monotonic_s: float
    query_unix_s: float
    latest_at_query: int
    request_id: str | None = None
    tracker_box: tuple[float, float, float, float] | None = None


@dataclass
class QueryOutcome:
    job: QueryJob
    raw: RawSelection | None
    error: SelectorError | None
    finished_monotonic_s: float
    latency_ms: float | None


def inline_spawn(target: Callable[[], None], name: str) -> Any:
    """测试用：同步执行查询，结果照常进队列（保持与线程路径同一条代码路径）。"""
    target()
    return None


def thread_spawn(target: Callable[[], None], name: str) -> threading.Thread:
    thread = threading.Thread(target=target, daemon=True, name=name)
    thread.start()
    return thread


class LanguageWorker:
    """自带的单飞 worker：至多一个在途 + 至多一条 pending（§3.4，不复用 `SingleFlightWorker`）。"""

    def __init__(
        self,
        adapter: Any,
        *,
        t_hard_s: float = T_HARD_S,
        spawn: Callable[[Callable[[], None], str], Any] = thread_spawn,
        monotonic: Callable[[], float] = time.monotonic,
        on_call_started: Callable[["QueryJob"], None] | None = None,
    ):
        self._adapter = adapter
        self.t_hard_s = float(t_hard_s)
        self._spawn = spawn
        self._monotonic = monotonic
        self._on_call_started = on_call_started
        #: 真实进入 `predict_one` 的次数（信封的「本地模型查询行」按此计）。
        self.calls_started = 0
        self._results: "queue.Queue[QueryOutcome]" = queue.Queue()
        self._in_flight: QueryJob | None = None
        self._handle: Any = None
        self.pending: QueryJob | None = None
        self.stuck = False
        self.abandoned: list[str] = []
        self._dropped: list[str] = []
        #: 超硬限后被放弃、但线程可能仍存活的任务：(线程句柄, query_id)。
        self._stranded: list[tuple[Any, str]] = []
        #: 被直接丢弃、永远不会产生回包的 job；会话据此解钉帧环副本。
        self.dropped_jobs: list[QueryJob] = []

    @property
    def busy(self) -> bool:
        return self._in_flight is not None

    @property
    def in_flight(self) -> QueryJob | None:
        return self._in_flight

    def submit(self, job: QueryJob) -> tuple[str, QueryJob | None]:
        """返回 (`STARTED` / `PENDING_QUEUED`, 被替换的旧 pending)。"""
        if self.stuck:
            raise SelectorError("worker_stuck", "worker needs a restart")
        if self._in_flight is None and self.pending is None:
            self._start(job)
            return "STARTED", None
        superseded = self.pending
        self.pending = job
        return "PENDING_QUEUED", superseded

    def _start(self, job: QueryJob) -> None:
        self._in_flight = job
        # AC-6 修订 1：真实模型调用只在这里计数一次，与尝试数、`query_id` 序号分列。
        self.calls_started += 1
        if self._on_call_started is not None:
            self._on_call_started(job)

        def run() -> None:
            started = float(self._monotonic())
            raw: RawSelection | None = None
            error: SelectorError | None = None
            # AC-8 修订 2：try 只圈 `predict_one` 的执行边界，实参在 try 之外求值，
            # 会话侧的数据异常不得被吞成 `worker_died`。
            image_path = job.frame.copy_path
            surface = job.instruction.surface
            g4 = job.instruction.g4
            try:
                raw = self._adapter.predict_one(job.query_id, image_path, surface, g4)
            except SelectorError as exception:
                error = exception
            except Exception as exception:  # 适配器边界的普通异常：保留类型与消息
                error = SelectorError(
                    "worker_died", f"{type(exception).__name__}: {exception}"
                )
            finished = float(self._monotonic())
            self._results.put(
                QueryOutcome(
                    job=job,
                    raw=raw,
                    error=error,
                    finished_monotonic_s=finished,
                    latency_ms=(
                        raw.latency_ms
                        if raw is not None and raw.latency_ms is not None
                        else (finished - started) * 1000.0
                    ),
                )
            )

        self._handle = self._spawn(run, f"language-worker-{job.query_id}")

    def poll(self) -> list[QueryOutcome]:
        """取回已完成的结果，必要时标 `worker_stuck`，空闲则启动 pending。"""
        outcomes: list[QueryOutcome] = []
        while True:
            try:
                outcome = self._results.get_nowait()
            except queue.Empty:
                break
            if self._in_flight is not None and outcome.job.query_id == self._in_flight.query_id:
                self._in_flight = None
                self._handle = None
            if outcome.job.query_id in self._dropped:
                # 超硬限之后到达的回包一律丢弃（§3.4）。
                continue
            if outcome.error is not None and outcome.error.reason == "worker_stuck":
                # U-A-2：适配器自己报 stuck 时也要立刻封住 worker，
                # 否则下面的 pending 派发会再打一次模型。
                self.stuck = True
                if self.pending is not None:
                    self.dropped_jobs.append(self.pending)
                    self.pending = None
            outcomes.append(outcome)
        if self._in_flight is not None:
            elapsed = float(self._monotonic()) - self._in_flight.submitted_monotonic_s
            if elapsed > self.t_hard_s:
                self.stuck = True
                self._dropped.append(self._in_flight.query_id)
                stuck_job = self._in_flight
                # U-A-3：线程很可能还活着。句柄与 query_id 留给 `stop()`，
                # 否则 `stop` 会因为 handle=None 直接返回，既不 join 也不记
                # `worker_abandoned`（§3.4 / AC-17）。
                if self._handle is not None:
                    self._stranded.append((self._handle, stuck_job.query_id))
                self._in_flight = None
                self._handle = None
                if self.pending is not None:
                    self.dropped_jobs.append(self.pending)
                    self.pending = None
                outcomes.append(
                    QueryOutcome(
                        job=stuck_job,
                        raw=None,
                        error=SelectorError("worker_stuck", "T_hard exceeded"),
                        finished_monotonic_s=float(self._monotonic()),
                        latency_ms=elapsed * 1000.0,
                    )
                )
        if self._in_flight is None and self.pending is not None and not self.stuck:
            job = self.pending
            self.pending = None
            self._start(job)
        return outcomes

    def drop_pending(self) -> QueryJob | None:
        job = self.pending
        self.pending = None
        return job

    def stop(self, join_s: float | None = None) -> str | None:
        """`stop`：join 在途线程 ≤ 5 s，未结束记 `worker_abandoned` 后退出。

        U-A-3：超硬限时被清掉的在途任务留在 `_stranded` 里，这里同样要 join 并
        记名——那次 `predict_one` 已经真的跑过，按 AC-6 修订 1 仍要能对账。
        """
        # 默认值在调用时取模块常量，便于测试收紧等待（行为不变）。
        join_s = WORKER_JOIN_S if join_s is None else float(join_s)
        self.pending = None
        pairs: list[tuple[Any, str | None]] = list(self._stranded)
        self._stranded = []
        if self._handle is not None:
            pairs.append(
                (self._handle, self._in_flight.query_id if self._in_flight else None)
            )
        abandoned = False
        # `stop` 的总等待由这条截止保证（§3.4「join 在途线程 ≤ 5 s」），
        # 不依赖「pairs 里最多一个真线程」这种未声明的不变量。
        deadline = float(self._monotonic()) + float(join_s)
        for handle, query_id in pairs:
            if isinstance(handle, threading.Thread):
                remaining = max(0.0, deadline - float(self._monotonic()))
                handle.join(remaining)
                if handle.is_alive():
                    abandoned = True
                    if query_id is not None and query_id not in self.abandoned:
                        self.abandoned.append(query_id)
        self._in_flight = None
        self._handle = None
        return "worker_abandoned" if abandoned else None


# --- 段内运行记录（§3.6 的处理帧环由日志包装器登记） ----------------------


@dataclass(frozen=True)
class ProcessedFrame:
    frame_id: int
    box_norm: tuple[float, float, float, float] | None
    ok: bool
    state: str
    event: str | None
    reason: str | None
    confidence: float | None


class RecordingRunLogger:
    """包装 `RunLogger`：记录写入之后才把该帧登记进会话的处理帧环（§3.6）。"""

    def __init__(self, logger: RunLogger, sink: Callable[[ProcessedFrame], None]):
        self._logger = logger
        self._sink = sink

    @property
    def run_id(self) -> str:
        return self._logger.run_id

    @property
    def run_directory(self) -> Path:
        return self._logger.run_directory

    def append(self, record: Mapping[str, Any]) -> None:
        self._logger.append(record)
        box = record.get("box_norm")
        self._sink(
            ProcessedFrame(
                frame_id=int(record["frame_id"]),
                box_norm=(
                    tuple(float(value) for value in box)
                    if isinstance(box, (list, tuple)) and len(box) == 4
                    else None
                ),
                ok=bool(record.get("ok")),
                state=str(record.get("state")),
                event=record.get("event"),
                reason=record.get("reason"),
                confidence=(
                    float(record["confidence"])
                    if isinstance(record.get("confidence"), (int, float))
                    and not isinstance(record.get("confidence"), bool)
                    else None
                ),
            )
        )

    def snapshot_json(self, name: str, data: Mapping[str, Any]) -> Path:
        return self._logger.snapshot_json(name, data)

    def close(self) -> None:
        self._logger.close()

    def finalize(self) -> tuple[Path, dict[str, Any]]:
        return self._logger.finalize()


# --- 预览（§3.2(b)） ------------------------------------------------------


class PreviewUnavailable(RuntimeError):
    """本解释器没有 Pillow：预览不生成，`preview_path` 为 null 并记录原因。"""


def render_preview(
    source_image: Path,
    destination: Path,
    candidates: Sequence[Candidate],
    tracker_box: Sequence[float] | None = None,
) -> Path:
    """原帧 + 带 index 的候选框（核验时另画配对跟踪框）。需要 Pillow。"""
    try:
        from PIL import Image, ImageDraw
    except ImportError as exception:  # pragma: no cover - 取决于解释器
        raise PreviewUnavailable("pillow is not installed") from exception
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source_image) as image:
        canvas = image.convert("RGB")
    width, height = canvas.size
    draw = ImageDraw.Draw(canvas)
    if tracker_box is not None:
        x, y, box_width, box_height = (float(value) for value in tracker_box)
        draw.rectangle(
            [x * width, y * height, (x + box_width) * width, (y + box_height) * height],
            outline=(0, 255, 0),
            width=2,
        )
        draw.text((x * width + 3, y * height + 3), "tracker", fill=(0, 255, 0))
    for candidate in candidates:
        x, y, box_width, box_height = candidate.bbox_xywh_norm
        draw.rectangle(
            [x * width, y * height, (x + box_width) * width, (y + box_height) * height],
            outline=(255, 0, 0),
            width=2,
        )
        draw.text((x * width + 3, y * height + 3), str(candidate.index), fill=(255, 0, 0))
    canvas.save(destination, format="PNG")
    return destination


# --- 会话 ------------------------------------------------------------------


@dataclass(frozen=True)
class AcquireParams:
    """§3.7 申请值（D1/D2 裁定 (d)：会话配置项，记录生效值，不是冻结值）。"""

    omega_arr_deg_s: float = 5.0
    n_arr: int = 2
    t_slew_s: float = 3.0
    window_m: int = 5
    n_adopt: int = 3
    r_adopt_px: float = 40.0
    margin_px: float = 15.0

    def payload(self) -> dict[str, Any]:
        return {
            "omega_arr_deg_s": self.omega_arr_deg_s,
            "n_arr": self.n_arr,
            "t_slew_s": self.t_slew_s,
            "window_m": self.window_m,
            "n_adopt": self.n_adopt,
            "r_adopt_px": self.r_adopt_px,
            "margin_px": self.margin_px,
        }


@dataclass
class SessionConfig:
    session_id: str
    session_root: Path
    runtime: Path
    receipt: KReceipt
    adapter: Any
    tracker_name: str = "nanotrack-v2"
    condition: str = "follow"
    ground_plane_y_m: float = 0.0
    maximum_ground_range_m: float = 400.0
    planned_duration_s: float = 300.0
    scenario_id: str | None = None
    attempt_limit: int = ATTEMPT_LIMIT
    verify_interval_s: float = T_V_S
    t_hard_s: float = T_HARD_S
    expires_after_s: float = 2.0
    diagnostic: bool = False
    run_root: Path | None = None
    tracker_factory: Callable[[], Any] | None = None
    decode: Callable[[Path], Any] | None = None
    preview: Callable[..., Path] | None = None
    worker_spawn: Callable[[Callable[[], None], str], Any] = thread_spawn
    monotonic: Callable[[], float] = time.monotonic
    unix: Callable[[], float] = time.time
    is_alive: Callable[[int], bool] = bridge.default_is_alive
    pid: int | None = None
    scenario_config_path: Path | None = None
    #: R-B8 / AC-19：冻结的 BODY-001 阈值规划器配置与其场景；`run` 入口总是给出，配置不符即拒绝启动。
    #: 为 None 时不接规划器，只供离线回放演示与旧测试构造（不是 Play 路径）。
    body_planner_config: Path | None = None
    body_scenario_config: Path | None = None
    #: P1-ENG-ACQ-001：常驻单一 TrackLoop（指针式快层）。缺省 False = LOOP-001 段式路径不变。
    resident: bool = False
    acquire: AcquireParams = field(default_factory=AcquireParams)
    #: §3.8 最小伺服步进限速 ω_max（°/s）；每帧上限 = ω_max / capture_hz。
    servo_omega_max_deg_s: float = 30.0
    #: P1-ENG-LOOP-002 A1：机身策略（`threshold` 缺省不变；`standoff` 走 FRAME-001 构造器并要求显式覆盖文件）。
    body_policy: str = "threshold"
    #: A5：常驻检测器的底层权重加载器（缺省 = `det_assoc_tracker._default_model_loader`）；会话以一次性
    #: 缓存包装它，重建 `TrackLoop` 时复用已加载模型。测试注入计数替身。
    model_loader: Callable[[Path], Any] | None = None
    #: §3.2 jetson 启动校验：部署摘要与 git 状态的取值来源（缺省 = 本仓库工作树；测试注入）。
    code_root: Path | None = None
    git_state: Callable[[], tuple[str | None, bool]] | None = None
    #: P1-ENG-CAPTURE-001 C9：`False` = `run --language off` 捕获模式（`receipt`/`adapter` 可为 None）。
    language: bool = True
    #: 捕获参数文件（§3.7）；缺省 `config/p1-eng-capture-001.json`。兼容模式只取其 sha 记日志。
    capture_config: Path | None = None
    #: P1-ENG-FASTFIX-001 §3.7：捕获模式门值/降级/重捕参数文件；缺省 `config/p1-eng-fastfix-001.json`。兼容模式不读。
    fastfix_config: Path | None = None


@dataclass(frozen=True)
class BodyRuntime:
    """会话启动时由冻结 `_build_body_runtime` 构造并校验的原型；每段深拷贝出独立实例（AC-4 修订 4）。"""

    planner: Any
    estimator: Any
    expires_after_s: float
    identity: dict[str, Any]

    def fresh(self) -> tuple[Any, Any]:
        return copy.deepcopy(self.planner), copy.deepcopy(self.estimator)


def bind_body_runtime(
    planner_config: Path,
    scenario_config: Path,
    *,
    live_scenario: Mapping[str, Any],
    capture_hz: float,
    scenario_id: str | None,
    ground_plane_y_m: float,
    policy: str = "threshold",
    runtime: Path | None = None,
) -> BodyRuntime:
    """AC-19：复用冻结阈值规划器；任何不符都以 `ConfigMismatch` 拒绝启动，绝不降级为无规划器跟踪。

    P1-ENG-LOOP-002 A1：`policy="standoff"` 另走 FRAME-001 既有构造器（`runtime=` 与显式
    `ground_plane_y_m` 一并传入）；`threshold`（缺省）路径逐字不变。
    """
    if policy not in BODY_POLICIES:
        raise ConfigMismatch(f"CONFIG_MISMATCH: unknown body policy {policy!r}")
    if policy == "standoff":
        return _bind_standoff_runtime(
            Path(planner_config),
            Path(scenario_config),
            capture_hz=capture_hz,
            scenario_id=scenario_id,
            ground_plane_y_m=ground_plane_y_m,
            runtime=runtime,
        )
    try:
        body_scenario = json.loads(Path(scenario_config).read_text(encoding="utf-8"))
        if body_scenario != dict(live_scenario):
            raise ValueError("body scenario differs from the live (effective) scenario")
        planner_document = json.loads(Path(planner_config).read_text(encoding="utf-8"))
        command = planner_document.get("command") or {}
        config_hz = float(command.get("capture_hz"))
        if abs(config_hz - float(capture_hz)) > 1e-9:
            raise ValueError(f"planner capture_hz {config_hz} differs from the live {capture_hz}")
        planner, estimator, expires_after_s, identity = _build_body_runtime(
            Path(planner_config),
            Path(scenario_config),
            "threshold",
            scenario_id=scenario_id or body_scenario.get("scenario_id"),
            ground_plane_y_m=ground_plane_y_m,
        )
        # 冻结合同：命令有效期 = 2 / capture_hz。
        if abs(float(expires_after_s) - 2.0 / float(capture_hz)) > 1e-9:
            raise ValueError(f"planner expires_after_s {expires_after_s} is not 2 / capture_hz")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ConfigMismatch(f"CONFIG_MISMATCH: body planner refused: {exc}") from exc
    return BodyRuntime(planner, estimator, float(expires_after_s), dict(identity))


#: A1：`standoff` 只认显式覆盖文件（生效场景回退不改，AR1-4）。
SCENARIO_OVERRIDE_NAME = "scenario_config.json"


def _bind_standoff_runtime(
    planner_config: Path,
    scenario_config: Path,
    *,
    capture_hz: float,
    scenario_id: str | None,
    ground_plane_y_m: float,
    runtime: Path | None,
) -> BodyRuntime:
    """A1：`standoff-band-v1` 接到会话。

    * 要求 `runtime/scenario_config.json` **存在**（缺失即拒绝启动）：此时本模块的旧解析器
      `effective_scenario_document` 与 `scenario_tether.effective_scenario_path` 都返回同一文件，
      回退分歧不出现；`effective_scenario_document` 的缺省回退（default）对其余路径保持原样。
    * `--body-scenario-config` 须与该文件**逐值相等**。
    * 构造经 FRAME-001 的 `_build_body_runtime(..., "standoff", runtime=...)`（它另核生效场景与配置钉住的 sha）。
    * 身份块补 `name`（规划器名）；配置 sha 与生效场景 sha 由构造器运行时计算（不手抄）。
    """
    try:
        if runtime is None:
            raise ValueError("the standoff body policy needs the runtime directory")
        override = Path(runtime) / SCENARIO_OVERRIDE_NAME
        if not override.is_file():
            raise ValueError(
                f"the standoff body policy requires an explicit {SCENARIO_OVERRIDE_NAME} under the runtime directory"
            )
        override_document = json.loads(override.read_text(encoding="utf-8"))
        body_scenario = json.loads(Path(scenario_config).read_text(encoding="utf-8"))
        if body_scenario != override_document:
            raise ValueError("body scenario differs value-for-value from runtime/scenario_config.json")
        sensor = body_scenario.get("sensor") or {}
        if abs(float(sensor.get("capture_hz")) - float(capture_hz)) > 1e-9:
            raise ValueError(f"scenario capture_hz {sensor.get('capture_hz')} differs from the live {capture_hz}")
        planner, estimator, expires_after_s, identity = _build_body_runtime(
            Path(planner_config),
            Path(scenario_config),
            "standoff",
            scenario_id=scenario_id or body_scenario.get("scenario_id"),
            ground_plane_y_m=ground_plane_y_m,
            runtime=Path(runtime),
        )
        if abs(float(expires_after_s) - 2.0 / float(capture_hz)) > 1e-9:
            raise ValueError(f"planner expires_after_s {expires_after_s} is not 2 / capture_hz")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ConfigMismatch(f"CONFIG_MISMATCH: standoff body planner refused: {exc}") from exc
    identity = dict(identity)
    identity["name"] = getattr(planner, "name", None)
    return BodyRuntime(planner, estimator, float(expires_after_s), identity)


class _SessionModelCache:
    """A5：常驻检测器权重的会话级一次性加载缓存。

    `create_tracker(..., resident=True, model_loader=cache.load)` 把它透传给 `DetAssocTracker`；同一权重路径
    第二次请求直接返回已加载对象（`det_assoc_tracker.py`/`trackers.py` 零改动）。`loads` 只计真实调用底层
    加载器的次数（AC-3：每会话 = 1）。
    """

    def __init__(self, loader: Callable[[Path], Any] | None, *, monotonic: Callable[[], float] | None = None):
        self._loader = loader
        self._models: dict[str, Any] = {}
        self.loads = 0
        self.requests = 0
        #: P1-ENG-FASTFIX-001 §3.5：给出会话 monotonic（只在捕获模式）时，返回对象是计时包装，记模型 `predict`
        #: 返回时刻 `m_det`；缺省 None = 原对象原样返回（兼容模式不变）。
        self._monotonic = monotonic
        self.last_predict_return_monotonic: float | None = None

    def load(self, weights_path: Path) -> Any:
        self.requests += 1
        key = str(Path(weights_path))
        if key not in self._models:
            loader = self._loader
            if loader is None:
                from .det_assoc_tracker import _default_model_loader  # noqa: PLC0415 — 只在真实常驻路径导入

                loader = _default_model_loader
            model = loader(Path(weights_path))
            self.loads += 1
            self._models[key] = model if self._monotonic is None else _TimedModel(model, self)
        return self._models[key]

    def payload(self) -> dict[str, Any]:
        return {"model_loads": self.loads, "model_requests": self.requests}


class _TimedModel:
    """FASTFIX §3.5：模型计时包装（只包 `predict`，记返回时刻 = `m_det`）；其余属性透传。不改检测调用与结果。"""

    def __init__(self, model: Any, cache: "_SessionModelCache"):
        self._model = model
        self._cache = cache

    def predict(self, *args: Any, **kwargs: Any) -> Any:
        result = self._model.predict(*args, **kwargs)
        assert self._cache._monotonic is not None
        self._cache.last_predict_return_monotonic = float(self._cache._monotonic())
        return result

    def __getattr__(self, name: str) -> Any:
        return getattr(self._model, name)


class _CaptureHook:
    """P1-ENG-CAPTURE-001：`TrackLoop` 捕获模式钩子 → 会话的 `TargetManager`（单写者、串行）。"""

    def __init__(self, session: "LanguageSession"):
        self._session = session

    def on_frame(self, entry: Any, *, newest: bool) -> Any:
        session = self._session
        manager = session.target_manager
        assert manager is not None
        pending = session._pending_capture_click
        if pending is not None and pending.get("result") is None and int(entry.frame_id) >= int(pending["k"]):
            # §3.3 ①→⑤（C1-3 / RR-1）：该帧已入历史、尚未授权——先处理替换请求，再对该帧求值与产生效果。
            session._commit_pending_click(pending, int(entry.frame_id))
        reacq = None
        if manager.reacquire_open and manager.binding is None:
            # FASTFIX §3.3：窗口内本帧合成先验（库同类 KF 连推 + pose-center）与同源 monotonic，作为非真值输入落盘。
            reacq = dict(manager.reacquire_prior_for(entry, session._reacq_predictor) or {})
            reacq["at_monotonic_s"] = float(session._monotonic())
        outcome = manager.on_frame(entry, newest=newest, wall_unix_s=float(session._unix()), reacq=reacq)
        session._capture_outcomes.append(outcome)
        if newest:
            session._note_hint_candidate(entry)
        session._handle_reacquire_result()
        return outcome

    def monotonic(self) -> float:
        return float(self._session._monotonic())

    def detect_return_monotonic(self) -> float | None:
        return self._session._model_cache.last_predict_return_monotonic

    def note_frame_timing(self, record: Mapping[str, Any]) -> None:
        self._session._journal_frame_timing(record)

    def on_frame_settled(self, settle: Mapping[str, Any]) -> None:
        self._session._on_frame_settled(settle)

    def effect_current(self, effect: Any, *, frame_id: int | None = None) -> bool:
        manager = self._session.target_manager
        return manager is not None and manager.effect_current(effect, frame_id=frame_id)

    def note_control_limited(self, effect: Any) -> None:
        manager = self._session.target_manager
        if manager is not None:
            manager.note_control_limited(effect)


class LanguageSession:
    """§3.4 的八态 × 九动作会话。未列组合一律回执 `REQUEST_INVALID`，状态不变。"""

    def __init__(self, config: SessionConfig):
        self.language = bool(config.language)
        if not self.language:
            self._init_language_off(config)
            return
        selected_report = validate_measurement_sources(config.receipt)
        identity = dict(getattr(config.adapter, "identity", {}))
        if (identity.get("backend") != config.receipt.backend
                or identity.get("model_form") != config.receipt.model_form
                or any(identity.get(k) != v for k, v in config.receipt.model_identity.items())):
            raise ConfigMismatch("CONFIG_MISMATCH: adapter identity differs from the K receipt")
        if config.receipt.backend == "http":
            endpoint = (selected_report or {}).get("transport", {}).get("endpoint")
            if not endpoint or getattr(config.adapter, "base_url", "").rstrip("/") != endpoint.rstrip("/"):
                raise ConfigMismatch("CONFIG_MISMATCH: live HTTP endpoint differs from the measured host")
            try:
                config.adapter.bind_identity(config.receipt.model_identity)
            except (SelectorError, AttributeError) as exc:
                raise ConfigMismatch(f"CONFIG_MISMATCH: live HTTP identity was not verified: {exc}") from exc
        jetson_binding: dict[str, Any] | None = None
        if config.receipt.host == JETSON_HOST:
            # §3.2：jetson 单宿主路径另核场景、代码版本、部署摘要、机器名与桌面重算身份（旧路径不变）。
            jetson_binding = validate_jetson_session(
                config.receipt,
                selected_report or {},
                config.adapter,
                runtime=Path(config.runtime),
                scenario_config_path=config.scenario_config_path,
                code_root=Path(config.code_root or PROJECT_ROOT),
                git_state=config.git_state,
            )
        self.config = config
        self.session_id = config.session_id
        self.session_dir = Path(config.session_root) / config.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.runtime = Path(config.runtime)
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.receipt = config.receipt
        self._monotonic = config.monotonic
        self._unix = config.unix

        scenario = read_scenario(self.runtime, config.scenario_config_path)
        if (
            abs(scenario["capture_hz"] - self.receipt.hz) > 1e-9
            or scenario["retained_frame_count"] != self.receipt.retained_frame_count
        ):
            raise ConfigMismatch(
                "CONFIG_MISMATCH: the live scenario hz/R differ from the K receipt"
            )
        self._init_common(config, scenario, jetson_binding)

    def _init_language_off(self, config: SessionConfig) -> None:
        """C9：`--language off` 不读 K 收据、不建适配器与 worker；只接受常驻 `det-assoc-v1`。"""
        if not config.resident:
            raise ConfigMismatch("CONFIG_MISMATCH: --language off needs --tracker det-assoc-v1 --resident")
        if config.receipt is not None or config.adapter is not None:
            raise ConfigMismatch("CONFIG_MISMATCH: --language off takes no K receipt and no adapter")
        self.config = config
        self.session_id = config.session_id
        self.session_dir = Path(config.session_root) / config.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.runtime = Path(config.runtime)
        self.runtime.mkdir(parents=True, exist_ok=True)
        self._monotonic = config.monotonic
        self._unix = config.unix
        scenario = read_scenario(self.runtime, config.scenario_config_path)
        hz = float(scenario["capture_hz"])
        # P1-ENG-FASTFIX-001 §3.7（G3）：捕获模式 `t_pub_s`/`k_pub`/`N_drop`/`T_reacq`/`auto_reacquire` 改由本项配置读取；
        # 违反结构约束 → 拒绝启动。首候选 = 现行常数（0.4 s / 2 帧，移植限值）。
        capture_params, _capture_sha, _capture_text = tmgr.load_capture_config(
            Path(config.capture_config or tmgr.DEFAULT_CAPTURE_CONFIG)
        )
        try:
            self.fastfix, self.fastfix_sha256, _fastfix_text = tmgr.load_fastfix_config(
                Path(config.fastfix_config or tmgr.DEFAULT_FASTFIX_CONFIG), capture_params, hz
            )
        except (OSError, tmgr.FastfixConfigInvalid) as exc:
            raise ConfigMismatch(f"CONFIG_MISMATCH: fastfix config refused: {exc}") from exc
        self.receipt = LanguageOffTiming(hz, int(scenario["retained_frame_count"]), k_pub=self.fastfix.k_pub)
        self._init_common(config, scenario, None)

    def _init_common(self, config: SessionConfig, scenario: Mapping[str, Any], jetson_binding: Any) -> None:
        self.scenario = scenario
        self.body_runtime: BodyRuntime | None = None
        if config.body_planner_config is not None:
            if config.body_policy == "threshold":
                # A1 反例：缺省 `threshold` 的调用序列与 ACQ-001 通过候选逐字一致（不传新参数）。
                self.body_runtime = bind_body_runtime(
                    Path(config.body_planner_config),
                    Path(config.body_scenario_config or PROJECT_ROOT / "config" / "scenario.default.json"),
                    live_scenario=effective_scenario_document(self.runtime, config.scenario_config_path),
                    capture_hz=self.receipt.hz,
                    scenario_id=config.scenario_id,
                    ground_plane_y_m=config.ground_plane_y_m,
                )
            else:
                self.body_runtime = bind_body_runtime(
                    Path(config.body_planner_config),
                    Path(config.body_scenario_config or PROJECT_ROOT / "config" / "scenario.default.json"),
                    live_scenario=effective_scenario_document(self.runtime, config.scenario_config_path),
                    capture_hz=self.receipt.hz,
                    scenario_id=config.scenario_id,
                    ground_plane_y_m=config.ground_plane_y_m,
                    policy=config.body_policy,
                    runtime=self.runtime,
                )
        elif config.body_policy != "threshold":
            raise ConfigMismatch("CONFIG_MISMATCH: --body-policy standoff needs a body planner config")
        self._jetson_binding = jetson_binding

        self.ring = FrameSnapshotRing(
            self.session_dir / "frames",
            capacity=self.receipt.retained_frame_count,
            decode=config.decode,
            monotonic=self._monotonic,
            unix=self._unix,
        )
        # FASTFIX §3.5：只有捕获会话记逐阶段标记（兼容/段式路径时钟读取次数不变）。
        self.ring.record_marks = bool(config.resident) and not self.language
        self.repository = SnapshotRepository(
            FrameRepository(self.runtime, image_loader=self.ring.image_loader),
            self.ring,
        )
        # C9：捕获模式不建 worker（`self.worker is None`）。
        self.worker = (
            LanguageWorker(
                config.adapter,
                t_hard_s=config.t_hard_s,
                spawn=config.worker_spawn,
                monotonic=self._monotonic,
                on_call_started=self._on_model_call_started,
            )
            if self.language
            else None
        )
        self.receipts_path = self.session_dir / RECEIPTS_FILE
        self.journal_path = self.session_dir / SESSION_JOURNAL
        self.results_path = self.session_dir / RESULTS_FILE
        self.previews_dir = self.session_dir / "previews"
        self.queries_dir = self.session_dir / "queries"

        # --- 会话状态 ---
        self.state = "IDLE"
        self.reason: str | None = None
        self.epoch = 0
        self.sequence = 0
        self.verify_epoch = 0
        self.segment_index = 0
        self.segments_seeded = 0
        self.track_id: str | None = None
        self.suspect_kind: str | None = None
        self.suspect_id: str | None = None
        self.suspect_reason: str | None = None
        self.since_frame_id: int | None = None
        self.since_unix_s: float | None = None
        self.last_progress_unix_s: float | None = None
        self.retired_track_ids: list[dict[str, Any]] = []
        self.last_request: dict[str, Any] | None = None
        self.pending_request: dict[str, Any] | None = None
        #: request_id → 最近一次见到的写入身份（`command_id`, `issued_unix_s`）；
        #: 身份不变 = 槽内残留重读，身份变了 = 同 id 被重新写入（§3.2(a)）。
        self.consumed_requests: dict[str, tuple[int | None, float | None]] = {}
        self.terminal_exit = False

        # --- 角色 A ---
        self.attempt = 0
        self.current_instruction: Instruction | None = None
        self.confirmed_instruction: Instruction | None = None
        self.candidates: tuple[Candidate, ...] = ()
        self.candidate_result_id: str | None = None
        self.candidate_frame: QuerySnapshot | None = None
        self.candidate_presented_monotonic_s: float | None = None
        self.candidate_query_monotonic_s: float | None = None
        #: 当前候选集的预览路径；为 None 表示预览未生成成功（AC-5 修订 1）。
        self.candidate_preview_path: str | None = None
        #: 产出当前候选的那次查询身份，确认失败的结果行沿用它，不另铸幽灵 query_id。
        self.candidate_query_id: str | None = None
        self.candidate_query_unix_s: float | None = None
        self._retry_min_frame_id: int | None = None
        self._retry_waiting_since: float | None = None
        self._query_sequence = 0
        self._result_sequence = 0
        self._suspect_sequence = 0

        # --- 角色 B ---
        self.next_due_unix_s: float | None = None
        self.last_verified_frame_id: int | None = None
        self.consecutive_alert = 0
        self.alert_kind: str | None = None
        self.last_verdict: str | None = None
        self.last_verify_query_id: str | None = None
        self.in_flight_verify_query_id: str | None = None
        self._trigger_last: dict[str, float] = {}
        self._confidences: deque[float] = deque(maxlen=25)

        # --- 段 ---
        self.loop: TrackLoop | None = None
        self.publisher: GatedPublisher | None = None
        self.logger: RecordingRunLogger | None = None
        self.processed: deque[ProcessedFrame] = deque(maxlen=512)
        self._new_records: list[ProcessedFrame] = []
        self.segment_started_frame_id: int | None = None

        self._session_lock: bridge.LockHolder | None = None
        self._last_state_document: dict[str, Any] | None = None

        # --- P1-ENG-ACQ-001 常驻（指针式快层）---
        self.resident = bool(config.resident)
        self.designation: dict[str, Any] | None = None
        self._pre_query: tuple[str, str | None, str | None, str | None, str | None] | None = None
        self._acquire: dict[str, Any] | None = None
        self._designated_box: tuple[float, ...] | None = None
        self.resident_loops_started = 0
        #: R2-1（AC-15 修订 1、§3.8）：会话最后一条实际写入 `gimbal_command.json` 的云台指令点。
        #: 常驻载体拆除时从旧 `GatedPublisher` 取出，重建时交给新发布器作为限速基准——云台通道是会话唯一的，
        #: 重建前后两条已写指令相邻，不因载体重建而清空基准。
        self._last_gimbal_point_world_m: tuple[float, float, float] | None = None

        # --- P1-ENG-LOOP-002 ---
        #: A5：会话级一次性模型缓存与常驻重建计数（每会话 ≤ RESIDENT_REBUILD_LIMIT）。
        #: FASTFIX §3.5：捕获会话的缓存返回计时包装（`m_det`）；兼容模式原样。
        self._model_cache = _SessionModelCache(
            config.model_loader, monotonic=self._monotonic if (self.resident and not self.language) else None
        )
        self.resident_rebuilds = 0
        #: A4：当前指定纪元的呈现延迟 Δ（秒；`ask`/`respecify` 受理时设定，同纪元内各次尝试共用）。
        self._designate_delay_s = 0.0
        #: A4：已到达、已过返回检查点、等待 Δ 到期才呈现的候选结果（挂起期间状态保持 `QUERYING`）。
        self._pending_presentation: dict[str, Any] | None = None

        # --- P1-ENG-CAPTURE-001 ---
        #: 捕获模式 = 语言关闭（`run --language off`）；兼容模式 = 语言开启的常驻会话。
        self.capture = self.resident and not self.language
        self.target_manager: tmgr.TargetManager | None = None
        self._capture_outcomes: list[Any] = []
        #: C1-3（§3.3 ①）：追平途中待在 k 帧授权之前提交的点击（`_CaptureHook.on_frame` 在该帧 ⑤ 之前处理）。
        self._pending_capture_click: dict[str, Any] | None = None
        # --- P1-ENG-FASTFIX-001（只在捕获模式使用）---
        if not self.capture:
            self.fastfix = None
            self.fastfix_sha256 = None
        #: §3.3 提示候选：本批最新帧、管理器已接受观测时的绑定键完整 KF 深复制（帧结算 PUBLISHED/DROPPED 才入列）。
        self._hint_pending: dict[int, Any] = {}
        self._hint_candidates: deque[Any] = deque(maxlen=(self.fastfix.t_reacq + 2) if self.fastfix is not None else 1)
        #: 库同类 KF 预测器（取自旧载体绑定键轨迹；重建后用于合成先验）。
        self._reacq_predictor: Any = None
        #: 重捕在途时旧外部指针（人可凭它 release）。
        self._reacq_token: str | None = None
        self._capture_tracker: Any = None
        self._batch_settle: Mapping[str, Any] | None = None
        self._journal_prev: tuple[float, int] | None = None
        if self.resident:
            capture_params, capture_sha, capture_text = tmgr.load_capture_config(
                Path(config.capture_config or tmgr.DEFAULT_CAPTURE_CONFIG)
            )
            self.target_manager = tmgr.TargetManager(
                capture_params,
                mode=tmgr.CAPTURE if self.capture else tmgr.COMPAT,
                config_sha256=capture_sha,
                config_text=capture_text if self.capture else None,
                # FASTFIX AC-13（R2-2 承接）：捕获会话落盘输入带行间链；兼容模式内存输入格式不变。
                inputs=tmgr.InputsLog(self.session_dir / tmgr.INPUTS_FILE if self.capture else None, chain=self.capture),
                sink=self._tm_sink,
                ground_plane_y_m=config.ground_plane_y_m,
                maximum_ground_range_m=config.maximum_ground_range_m,
                **({"fastfix": self.fastfix, "fastfix_config_sha256": self.fastfix_sha256} if self.capture else {}),
            )

    # --- 生命周期 ---------------------------------------------------------

    def start(self) -> None:
        holder, replaced = bridge.acquire_session_lock(
            self.runtime,
            session_id=self.session_id,
            pid=self.config.pid,
            now=self._unix(),
            is_alive=self.config.is_alive,
        )
        self._session_lock = holder
        if replaced is not None:
            self._journal(
                "session_lock_replaced",
                replaced_pid=replaced.pid,
                replaced_session_id=replaced.session_id,
            )
        self._journal(
            "session_started",
            **({"language": "off", "capture_config_sha256": self.target_manager.config_sha256} if self.capture else {}),
            **({"fastfix_config_sha256": self.fastfix_sha256, "fastfix_params": self.fastfix.as_record()}
               if self.capture and self.fastfix is not None else {}),
            k_receipt=self.receipt.payload(),
            scenario=self.scenario,
            diagnostic=self.config.diagnostic,
            body_planner=None if self.body_runtime is None else self.body_runtime.identity,
            **(
                {"body_policy": self.config.body_policy}
                if self.config.body_policy != "threshold"
                else {}
            ),
            **({"jetson_binding": self._jetson_binding} if self._jetson_binding is not None else {}),
        )
        self._publish_state(force=True)

    def close(self) -> None:
        if self.logger is not None:
            self.logger.close()
            self.logger = None
        if self._session_lock is not None:
            bridge.release_session_lock(
                self.runtime, session_id=self.session_id, pid=self._session_lock.pid
            )
            self._session_lock = None

    def run(self, *, max_ticks: int | None = None, sleep: Callable[[float], None] = time.sleep) -> str:
        ticks = 0
        while self.state != "TERMINAL":
            self.tick()
            ticks += 1
            if max_ticks is not None and ticks >= max_ticks:
                break
            if self.state != "TERMINAL":
                sleep(POLL_INTERVAL_S)
        return self.state

    # --- 主循环 -----------------------------------------------------------

    def tick(self) -> None:
        if not self.language:
            # C9：捕获模式无适配器/worker/核验，只消费请求、推进常驻载体与发布状态。
            self._consume_request()
            self._advance_segment()
            self._publish_state()
            return
        self._check_adapter_health()
        self._poll_worker()
        self._maybe_present()
        self._consume_request()
        self._advance_segment()
        self._resume_designate_retry()
        self._maybe_verify()
        self._publish_state()

    # --- 请求（§3.2 单槽 + AC-1 修订 1 的恰一次） ------------------------

    def _consume_request(self) -> None:
        envelope = bridge.read_request(self.runtime)
        if envelope is None:
            return
        if not envelope.addressable:
            self._journal("request_unaddressable", invalid_reason=envelope.invalid_reason)
            return
        written = (envelope.command_id, envelope.issued_unix_s)
        if envelope.request_id in self.consumed_requests:
            # 会话每 tick 重读单槽：同一次写入的残留静默；同 id 的重新写入
            # （CLI 用同一个 --request-id 重试）不再执行，只回执 IGNORED_DUPLICATE
            # 恰一次。无写入头的请求分不出两者，按残留处理。
            if written in (self.consumed_requests[envelope.request_id], (None, None)):
                return
            self.consumed_requests[envelope.request_id] = written
            self._receipt(envelope, "IGNORED_DUPLICATE")
            return
        if bridge.read_writer_lock(self.runtime) is None:
            # 绕过写者锁的写入不承诺可检测；观察到就记一笔。
            self._journal(
                "ILLEGAL_WRITER_SUSPECTED", request_id=envelope.request_id
            )
        self.consumed_requests[envelope.request_id] = written
        if envelope.session_id != self.session_id:
            self._receipt(envelope, "IGNORED_FOREIGN_SESSION")
            return
        if self.state == "TERMINAL":
            self._receipt(envelope, "IGNORED_TERMINAL")
            return
        if envelope.invalid_reason is not None:
            self._receipt(envelope, "REQUEST_INVALID", detail=envelope.invalid_reason)
            return
        self._dispatch(envelope)

    def _receipt(
        self,
        envelope: Any,
        outcome: str,
        *,
        detail: str | None = None,
        request_id: str | None = None,
        action: str | None = None,
        delay_injected_s: float | None = None,
    ) -> None:
        self.sequence += 1
        receipt = {
            "request_id": request_id or getattr(envelope, "request_id", None),
            "action": action or getattr(envelope, "action", None),
            "outcome": outcome,
            "at_sequence": self.sequence,
        }
        self.last_request = receipt
        extra: dict[str, Any] = {}
        if receipt["action"] in {"ask", "respecify"}:
            # A4：`--intent` 与 `--delay-s` 只写进回执日志（不进查询、不进 prompt、不影响任何决策）。
            delay_s, intent, _invalid = designate_options(envelope)
            extra = {"intent": intent, "delay_s": delay_s}
        if delay_injected_s is not None:
            extra["delay_injected_s"] = delay_injected_s
        self._journal("receipt", receipt=receipt, detail=detail, **extra)
        self._publish_state(force=True)

    def _dispatch(self, envelope: Any) -> None:
        action = envelope.action
        if not self.language and action in LANGUAGE_ONLY_ACTIONS:
            # C9 / AC-13：语言关闭时语言动作一律拒绝，状态不变。
            self._receipt(envelope, "REQUEST_INVALID", detail="language_disabled")
            return
        handler = getattr(self, f"_action_{action.replace('-', '_')}", None)
        if handler is None:  # pragma: no cover - action 闭集由 bridge 保证
            self._receipt(envelope, "REQUEST_INVALID", detail="unknown_action")
            return
        handler(envelope)

    # -- 九个动作 --

    #: §3.4 表里允许 `ask` 的状态；`TRACKING`/`SUSPECTED` 不在其中。
    _ASK_STATES = frozenset(
        {"IDLE", "QUERYING", "AWAITING_CONFIRMATION", "LOST", "REINIT_REQUIRED"}
    )

    #: P1-ENG-ACQ-001 §3.6：常驻会话另允许跟踪中指定（`TRACKING`/`SUSPECTED` → `QUERYING`，保留指针、继续发布）。
    _RESIDENT_ASK_STATES = _ASK_STATES | frozenset({"TRACKING", "SUSPECTED"})

    def _action_ask(self, envelope: Any) -> None:
        if self.state not in (self._RESIDENT_ASK_STATES if self.resident else self._ASK_STATES):
            self._receipt(envelope, "REQUEST_INVALID", detail=f"ask_in_{self.state}")
            return
        if self.state in {"LOST", "REINIT_REQUIRED"} and self.reason == "backend_fatal":
            # AC-17 修订 1：`backend_fatal` 只允许 stop / 读状态。
            self._receipt(envelope, "REQUEST_INVALID", detail="backend_fatal_needs_restart")
            return
        if envelope.instruction is None:
            self._receipt(envelope, "REQUEST_INVALID", detail="missing_instruction")
            return
        _delay, _intent, invalid = designate_options(envelope)
        if invalid is not None:
            self._receipt(envelope, "REQUEST_INVALID", detail=invalid)
            return
        self._begin_designate(envelope, envelope.instruction)

    def _action_respecify(self, envelope: Any) -> None:
        if self.state in {"LOST", "REINIT_REQUIRED"} and self.reason == "backend_fatal":
            self._receipt(envelope, "REQUEST_INVALID", detail="backend_fatal_needs_restart")
            return
        allowed = {
            "IDLE",
            "QUERYING",
            "AWAITING_CONFIRMATION",
            "SUSPECTED",
            "LOST",
            "REINIT_REQUIRED",
        }
        if self.resident:
            allowed.add("TRACKING")
        if self.state not in allowed:
            self._receipt(envelope, "REQUEST_INVALID", detail=f"respecify_in_{self.state}")
            return
        instruction = envelope.instruction or self.confirmed_instruction or self.current_instruction
        if instruction is None:
            self._receipt(envelope, "REQUEST_INVALID", detail="no_instruction_to_reuse")
            return
        _delay, _intent, invalid = designate_options(envelope)
        if invalid is not None:
            self._receipt(envelope, "REQUEST_INVALID", detail=invalid)
            return
        if self.state == "SUSPECTED" and not self.resident:
            # 等价 `confirm_lost` 后 `respecify`：先 finalize 旧段。
            self._finalize_segment(self.suspect_reason or "tracker_failure")
        self._begin_designate(envelope, instruction)

    def _action_confirm(self, envelope: Any) -> None:
        if self.state != "AWAITING_CONFIRMATION":
            self._receipt(envelope, "REQUEST_INVALID", detail=f"confirm_in_{self.state}")
            return
        if envelope.token != self.candidate_result_id:
            self._receipt(envelope, "REQUEST_INVALID", detail="token_mismatch")
            return
        index = envelope.candidate_index
        if index is None or index >= len(self.candidates):
            self._receipt(envelope, "REQUEST_INVALID", detail="candidate_index_out_of_range")
            return
        if self.candidate_preview_path is None:
            # AC-5 修订 1：有候选就必须先有绑定源帧、index 一一对应的预览；
            # 缺依赖/渲染失败可记 null，但此时确认一律 `REQUEST_INVALID`：
            # 候选、epoch、段都不变，不 initialize、不写观测或控制。
            self._receipt(envelope, "REQUEST_INVALID", detail="preview_unavailable")
            return
        reject_reason = self._check_confirmation()
        if reject_reason is not None:
            # A4：Δ 使确认越过现行检查点时按现行原因码处理，日志附本纪元注入的 Δ。
            self._receipt(
                envelope, "APPLIED", detail=reject_reason, delay_injected_s=self._designate_delay_s
            )
            self._emit_result(
                purpose="designate",
                status="stale_rejected",
                reject_reason=reject_reason,
                frame=self.candidate_frame,
                request_id=envelope.request_id,
                query_id=self.candidate_query_id,
                query_unix_s=self.candidate_query_unix_s,
            )
            self._discard_candidates()
            self._after_designate_failure("candidate_expired")
            return
        self._receipt(envelope, "APPLIED")
        if self.resident:
            self._designate_resident(self.candidates[index])
            return
        self._seed_segment(self.candidates[index])

    def _action_reject(self, envelope: Any) -> None:
        if self.state != "AWAITING_CONFIRMATION":
            self._receipt(envelope, "REQUEST_INVALID", detail=f"reject_in_{self.state}")
            return
        if envelope.token != self.candidate_result_id:
            self._receipt(envelope, "REQUEST_INVALID", detail="token_mismatch")
            return
        self._receipt(envelope, "APPLIED")
        self._discard_candidates()
        self._after_designate_failure("operator_reject")

    def _action_verify(self, envelope: Any) -> None:
        if self.state not in {"TRACKING", "SUSPECTED"}:
            self._receipt(envelope, "REQUEST_INVALID", detail=f"verify_in_{self.state}")
            return
        self._receipt(envelope, "APPLIED")
        self._request_verification("operator")

    def _action_confirm_lost(self, envelope: Any) -> None:
        if self.state != "SUSPECTED":
            self._receipt(envelope, "REQUEST_INVALID", detail=f"confirm_lost_in_{self.state}")
            return
        if envelope.token != self.suspect_id:
            self._receipt(envelope, "REQUEST_INVALID", detail="token_mismatch")
            return
        self._receipt(envelope, "APPLIED")
        reason = self.suspect_reason or "tracker_failure"
        if self.resident:
            self._retire_pointer(reason)
        else:
            self._finalize_segment(reason)
        self._enter("LOST", reason=reason)

    def _action_dismiss(self, envelope: Any) -> None:
        if self.state != "SUSPECTED":
            self._receipt(envelope, "REQUEST_INVALID", detail=f"dismiss_in_{self.state}")
            return
        if envelope.token != self.suspect_id:
            self._receipt(envelope, "REQUEST_INVALID", detail="token_mismatch")
            return
        self._receipt(envelope, "APPLIED")
        self.consecutive_alert = 0
        self.alert_kind = None
        self.verify_epoch += 1
        self.in_flight_verify_query_id = None
        self.next_due_unix_s = float(self._unix()) + self.config.verify_interval_s
        self.suspect_kind = None
        self.suspect_id = None
        self.suspect_reason = None
        self._enter("TRACKING", reason=None)

    def _action_release(self, envelope: Any) -> None:
        manager = self.target_manager
        if (self.capture and manager is not None and manager._reacq_active() and self.state == "REINIT_REQUIRED"
                and self._reacq_token is not None):
            # FASTFIX §3.3 ①：重捕在途时人可凭旧外部指针 release——取消原任务、提示作废（release 优先于点击与自动）。
            if envelope.token != self._reacq_token:
                self._receipt(envelope, "REQUEST_INVALID", detail="token_mismatch")
                return
            self._receipt(envelope, "APPLIED")
            manager.release_binding("operator_release", cancel_task=True)
            manager.take_reacquire_result()
            self._reacq_token = None
            self._enter("LOST", reason="operator_release")
            return
        # 捕获模式：BROKEN/DISPUTED（SUSPECTED）时人可 release（§3.6）。
        allowed = {"TRACKING", "SUSPECTED"} if self.capture else {"TRACKING"}
        if self.state not in allowed:
            self._receipt(envelope, "REQUEST_INVALID", detail=f"release_in_{self.state}")
            return
        if envelope.token != self.track_id:
            self._receipt(envelope, "REQUEST_INVALID", detail="token_mismatch")
            return
        self._receipt(envelope, "APPLIED")
        if self.resident:
            self._retire_pointer("operator_release")
        else:
            self._finalize_segment("operator_release")
        self._enter("LOST", reason="operator_release")

    def _action_stop(self, envelope: Any) -> None:
        self._receipt(envelope, "APPLIED")
        self.stop("operator_stop", request_id=envelope.request_id)

    # --- P1-ENG-CAPTURE-001 C7：点击入口 ------------------------------------------

    def _action_click(self, envelope: Any) -> None:
        """k 帧历史解析「包含点的框」→ 逐帧验证 k→当前证据链 → `commit_binding`；同一 tick 内完成。

        §3.3 ①→⑤（C1-3 / RR-1）：页面帧 k 尚未处理时追平——追平处理到 k 帧（已入历史、尚未授权）时先提交点击，
        再对该帧授权与产生效果，同帧状态与发出的命令一致；k 已处理时在历史头提交（该帧效果在请求被消费之前已发出），
        新绑定的首个效果在下一被处理帧。"""
        if not self.capture:
            if self.target_manager is not None:
                self.target_manager._emit("tm_event", "click", frame_id=None, accepted=False, reason="click_unavailable",
                                          request_id=envelope.request_id)
            self._receipt(envelope, "REQUEST_INVALID", detail="click_unavailable")
            return
        click = dict(envelope.click or {})
        k = int(click["frame_id"])
        assert self.target_manager is not None
        reacq_canceled = self.target_manager.cancel_reacquire("user_click")
        if reacq_canceled:
            # FASTFIX §3.3 / 首次接受释义 1（C1-3）：点击只作废重捕提示与缓冲，随后完整执行现行点击事务，由它决定
            # 任务终态——成功即新 TRACKING 任务；拒收按现行规则零状态变化（不取消任务、不改 TaskSpec/runtime/version/
            # 绑定）。stop/release 取消原任务的路径不经此处。
            self.target_manager.take_reacquire_result()
            self._reacq_token = None
            seg_end = getattr((self.target_manager.reacq or {}).get("hint"), "seg_end", None)
            try:
                self._action_click_transaction(envelope, click, k)
            finally:
                manager = self.target_manager
                if manager.binding is None and self.state == "REINIT_REQUIRED" and self.reason == tmgr.REASON_REACQUIRING:
                    # 不再自动重捕（仅会话投影）：原因回到触发拆载体的原因（如 `publish_expired`），等人点击/release/stop。
                    self._enter("REINIT_REQUIRED", reason=seg_end if seg_end in bridge.STATE_REASONS else None)
            return
        self._action_click_transaction(envelope, click, k)

    def _action_click_transaction(self, envelope: Any, click: Mapping[str, Any], k: int) -> None:
        assert self.target_manager is not None
        core = getattr(getattr(self.loop, "tracker", None), "core", None) if self.loop is not None else None
        head_at_consume = getattr(core, "head_frame_id", None) if core is not None else None
        page = dict(click.get("page") or {})
        page["head_at_consume"] = head_at_consume
        pending: dict[str, Any] = {"envelope": envelope, "click": click, "k": k, "page": page, "result": None}
        if core is not None and core.history(k) is None and (head_at_consume is None or k > head_at_consume):
            # 页面显示的帧尚未被处理：追平（受理子段计入「提交帧历史头 − 消费时历史头」）；提交在 k 帧授权之前完成。
            self._pending_capture_click = pending
            try:
                self._advance_resident()
            finally:
                self._pending_capture_click = None
            if pending["result"] is not None:
                self._finish_click(envelope, pending["result"])
                return
            core = getattr(getattr(self.loop, "tracker", None), "core", None) if self.loop is not None else None
        head = getattr(core, "head_frame_id", None) if core is not None else None
        self._finish_click(envelope, self._resolve_click(pending, core, head))

    def _resolve_click(self, pending: Mapping[str, Any], core: Any, head: int | None) -> tuple[str, Any, int | None]:
        """管理器解析与提交；提交成功/回滚失败的会话外部副作用（纪元、状态、安全 HOLD）在核心提交后立即执行。"""
        assert self.target_manager is not None
        click, k, envelope = pending["click"], int(pending["k"]), pending["envelope"]
        actual_sha = None
        try:
            image_path, _metadata_path = self.repository.frame_paths(k)
            actual_sha = sha256_bytes(Path(image_path).read_bytes())
        except (FileNotFoundError, OSError, KeyError, ValueError):
            actual_sha = None
        word, commit, _info = self.target_manager.click(
            request_id=str(envelope.request_id),
            x_px=float(click["x_px"]),
            y_px=float(click["y_px"]),
            frame_id=k,
            image_sha256=str(click["image_sha256"]),
            actual_image_sha256=actual_sha,
            history=(core.history if core is not None else (lambda _f: None)),
            head_frame_id=head,
            ended_ids=(core.ended_ids if core is not None else ()),
            page=dict(pending["page"]),
        )
        if commit is not None and commit.accepted:
            self._pre_query = None
            self._new_pointer_epoch(int(self.target_manager.track_key), head)
            self._enter("TRACKING", reason=None)
        elif commit is not None and commit.fail_closed:
            self._binding_fail_closed()
        return word, commit, head

    def _commit_pending_click(self, pending: dict[str, Any], frame_id: int) -> None:
        """追平中处理到 `frame_id`（≥ k，已入历史、尚未授权）：以该帧为历史头解析并提交（§3.3 ①）。"""
        core = getattr(getattr(self.loop, "tracker", None), "core", None) if self.loop is not None else None
        pending["result"] = self._resolve_click(pending, core, frame_id)

    def _finish_click(self, envelope: Any, result: tuple[str, Any, int | None]) -> None:
        word, commit, _head = result
        if word == "image_mismatch":
            self._receipt(envelope, "REQUEST_INVALID", detail="image_mismatch")
            return
        if word == "pixel_out_of_frame":
            self._receipt(envelope, "REQUEST_INVALID", detail="pixel_out_of_frame")
            return
        if commit is not None and commit.accepted:
            self._receipt(envelope, "APPLIED")
            return
        if commit is not None and commit.fail_closed:
            self._receipt(envelope, "APPLIED", detail=tmgr.REASON_ROLLBACK_FAILED)
            return
        # 解析/证据链/提交被拒：零状态变化，换目标被拒时继续跟旧目标。
        self._receipt(envelope, "APPLIED", detail=word)

    def _tm_sink(self, kind: str, record: Mapping[str, Any]) -> None:
        """目标管理器事件 → 会话 JSONL（事件名闭集逐个字面量，AC-4 of LOOP-002 机检口径）。"""
        fields = {k: v for k, v in record.items() if k not in {"kind", "state", "epoch", "sequence", "session_id"}}
        if kind == "tm_transition":
            self._journal("tm_transition", **fields)
        elif kind == "binding_committed":
            self._journal("binding_committed", **fields)
        elif kind == "authorization":
            self._journal("authorization", **fields)
        elif kind == "click_received":
            self._journal("click_received", **fields)
        elif kind == "reacquire_started":
            # FASTFIX §3.3：重捕事件逐个字面量落盘（事件名闭集静态检查口径）。
            self._journal("reacquire_started", **fields)
        elif kind == "reacquire_skipped":
            self._journal("reacquire_skipped", **fields)
        elif kind == "reacquire_canceled":
            self._journal("reacquire_canceled", **fields)
        elif kind == "reacquired_after_rebuild":
            self._journal("reacquired_after_rebuild", **fields)
        elif kind == "reacquire_failed":
            self._journal("reacquire_failed", **fields)
        else:
            self._journal("tm_event", tm_kind=kind, **fields)

    def _capture_hold(self, reason: str) -> None:
        """捕获模式显式 HOLD（STOP/STALE/回滚失败）：经机身安全通道写 hold 并留 `body_safety_hold` 收据。"""
        if self.publisher is None:
            return
        from .body_planner import BodyCommand  # noqa: PLC0415

        expires = self.body_runtime.expires_after_s if self.body_runtime is not None else self.config.expires_after_s
        self.publisher.body_command(BodyCommand.hold(expires, reason))

    def _binding_fail_closed(self) -> None:
        """AR1-3 提交回滚失败：串行 HOLD、停云台新效果、作废在途效果、退外部纪元，`REINIT_REQUIRED`。"""
        self._capture_hold(tmgr.REASON_ROLLBACK_FAILED)
        if self.publisher is not None:
            self.publisher.clear_association()
        self._retire_pointer(tmgr.REASON_ROLLBACK_FAILED, clear_core=False)
        self._enter("REINIT_REQUIRED", reason=tmgr.REASON_ROLLBACK_FAILED)

    # --- 角色 A：指定 ----------------------------------------------------

    def _begin_designate(self, envelope: Any, instruction: Instruction) -> None:
        if self.resident and self.state not in {"QUERYING", "AWAITING_CONFIRMATION"}:
            # §3.6：解析失败或其余三值回到确认前状态（SUSPECTED 计数与疑点保留）。
            self._pre_query = (self.state, self.reason, self.suspect_kind, self.suspect_id, self.suspect_reason)
        # A4：挂起中的呈现随纪元改变丢弃（不补写结果行）；新纪元的 Δ 取本次请求（缺省 0）。
        self._discard_pending_presentation("epoch_changed")
        delay_s, _intent, _invalid = designate_options(envelope)
        self._designate_delay_s = float(delay_s)
        self.epoch += 1
        self.attempt = 1
        self.current_instruction = instruction
        self._discard_candidates()
        self._retry_min_frame_id = None
        self._retry_waiting_since = None
        self._enter("QUERYING", reason=None)
        self._issue_designate(envelope.request_id, envelope)

    def _issue_designate(self, request_id: str | None, envelope: Any | None) -> None:
        assert self.current_instruction is not None
        if self.resident:
            # 常驻：先追平到最新帧，查询帧 N 随即在历史里（候选后端与 `designate(box, N)` 都按 N 取历史）。
            self._advance_resident()
            if self.state == "TERMINAL":
                # A5：追平途中会话已终止（`duration_reached`/`rebuild_limit`）——不再发起查询。
                if envelope is not None:
                    self._receipt(envelope, "IGNORED_TERMINAL", detail="session_terminal")
                return
        if self.worker.stuck:
            # 同上：`backend_fatal` 之后不再发起查询，等操作者 `stop` 重启进程。
            if envelope is not None:
                self._receipt(envelope, "REQUEST_INVALID", detail="backend_fatal_needs_restart")
            return
        frame, failure = self._acquire_frame(self._retry_min_frame_id)
        if failure == "no_new_frame_wait":
            # 等新帧：这一次不发查询，下一 tick 再试（有界于 T_ret）。
            if envelope is not None:
                self._receipt(envelope, "APPLIED", detail="waiting_for_new_frame")
            return
        if frame is None:
            if envelope is not None:
                self._receipt(envelope, "APPLIED", detail=failure)
            self._designate_failure(
                status="stale_rejected" if failure != "no_new_frame" else "no_new_frame",
                reject_reason=failure if failure != "no_new_frame" else None,
                frame=None,
                request_id=request_id,
            )
            return
        job = self._submit_query(
            purpose="designate",
            instruction=self.current_instruction,
            frame=frame,
            request_id=request_id,
        )
        if envelope is not None:
            self._receipt(
                envelope,
                "APPLIED" if self.worker.in_flight is job else "PENDING_QUEUED",
            )

    def _acquire_frame(
        self, minimum_frame_id: int | None
    ) -> tuple[QuerySnapshot | None, str | None]:
        """查询检查点：N 为完整 bundle、元数据 `frame_id == N` 且时钟合法。"""
        try:
            latest = self.repository.latest_frame_id()
        except (FileNotFoundError, KeyError, ValueError, OSError):
            return None, "bundle_missing"
        if minimum_frame_id is not None and latest <= minimum_frame_id:
            waited = (
                float(self._monotonic()) - self._retry_waiting_since
                if self._retry_waiting_since is not None
                else 0.0
            )
            if self._retry_waiting_since is None:
                self._retry_waiting_since = float(self._monotonic())
                return None, "no_new_frame_wait"
            if waited <= self.receipt.t_ret_s:
                return None, "no_new_frame_wait"
            self._retry_waiting_since = None
            return None, "no_new_frame"
        self._retry_waiting_since = None
        try:
            self.repository.load(latest)
        except FileNotFoundError:
            return None, "bundle_missing"
        except FrameIdentityChanged:
            return None, "image_identity_changed"
        except ValueError:
            return None, "metadata_invalid"
        snapshot = self.ring.snapshot(latest)
        if snapshot is None:  # pragma: no cover - bind 成功即存在
            return None, "bundle_missing"
        return (
            QuerySnapshot(
                frame_id=snapshot.frame_id,
                image_sha256=snapshot.image_sha256,
                copy_path=snapshot.copy_path,
                capture_monotonic_s=snapshot.capture_monotonic_s,
                capture_unix_s=snapshot.capture_unix_s,
                snapshot=snapshot,
            ),
            None,
        )

    def _submit_query(
        self,
        *,
        purpose: str,
        instruction: Instruction,
        frame: QuerySnapshot,
        request_id: str | None = None,
        tracker_box: Sequence[float] | None = None,
    ) -> QueryJob:
        self._query_sequence += 1
        job = QueryJob(
            query_id=f"{self.session_id}-q{self._query_sequence}",
            purpose=purpose,
            epoch=self.epoch,
            segment_index=self.segment_index if self.track_id else None,
            verify_epoch=self.verify_epoch,
            attempt=self.attempt if purpose == "designate" else 1,
            instruction=instruction,
            frame=frame,
            submitted_monotonic_s=float(self._monotonic()),
            query_unix_s=float(self._unix()),
            latest_at_query=frame.frame_id,
            request_id=request_id,
            tracker_box=tuple(float(value) for value in tracker_box)
            if tracker_box is not None
            else None,
        )
        self.ring.pin(frame.frame_id)
        try:
            outcome, superseded = self.worker.submit(job)
        except SelectorError as exception:
            self.ring.unpin(frame.frame_id)
            self._handle_backend_fatal(exception)
            raise
        if superseded is not None:
            self.ring.unpin(superseded.frame.frame_id)
            self._superseded_receipt(superseded)
        if purpose == "verify":
            self.in_flight_verify_query_id = job.query_id
        self._journal(
            "query_submitted",
            query_id=job.query_id,
            purpose=purpose,
            frame_id=frame.frame_id,
            attempt=job.attempt,
            epoch=job.epoch,
            queued=outcome == "PENDING_QUEUED",
        )
        return job

    def _superseded_receipt(self, job: QueryJob) -> None:
        if job.request_id is None:
            return
        self.sequence += 1
        receipt = {
            "request_id": job.request_id,
            "action": None,
            "outcome": "SUPERSEDED",
            "at_sequence": self.sequence,
        }
        self._journal("receipt", receipt=receipt, detail="pending_superseded")

    # --- worker 回包 -----------------------------------------------------

    def _check_adapter_health(self) -> None:
        """U-A-1：适配器的有界退出钩子。

        `http` 后端在「提交已被接纳、响应丢失」之后可能长期无法确认服务端可用。
        若只在下一次 `predict_one` 入口检查，操作者不再 `ask` 时就永远不会到期。
        会话每轮问一次，于是持续不明也有界地落到 `backend_fatal`。
        """
        if self.state in {"TERMINAL", "REINIT_REQUIRED"} and self.reason == "backend_fatal":
            return
        if self.state == "TERMINAL":
            return
        check = getattr(self.config.adapter, "health_check", None)
        if check is None:
            return
        try:
            check()
        except SelectorError as exception:
            if exception.reason != "worker_stuck":
                return
            self.worker.stuck = True
            self._journal(
                "backend_exception",
                query_id=None,
                purpose="health_check",
                reason=exception.reason,
                status=exception.status,
                detail=exception.detail,
            )
            self._handle_backend_fatal(exception)

    def _on_model_call_started(self, job: "QueryJob") -> None:
        """AC-6 修订 1：真实进入 `predict_one` 的那一刻留痕，不依赖 `stop()` 才落盘。"""
        self._journal(
            "query_started",
            query_id=job.query_id,
            purpose=job.purpose,
            frame_id=job.frame.frame_id,
            attempt=job.attempt,
            model_calls_started=self.worker.calls_started,
        )

    def _poll_worker(self) -> None:
        outcomes = self.worker.poll()
        while self.worker.dropped_jobs:
            # 被直接丢弃的 pending 永远不会有回包；不解钉的话那一帧会永久
            # 留在帧环里淘汰不掉（与 SUPERSEDED 分支对齐）。
            dropped = self.worker.dropped_jobs.pop()
            self.ring.unpin(dropped.frame.frame_id)
            self._journal(
                "pending_dropped", query_id=dropped.query_id, purpose=dropped.purpose
            )
        for outcome in outcomes:
            if outcome.error is not None:
                # AC-8 修订 2：异常的类型与消息进会话诊断；桥结果闭集一字不改。
                self._journal(
                    "backend_exception",
                    query_id=outcome.job.query_id,
                    purpose=outcome.job.purpose,
                    reason=outcome.error.reason,
                    status=outcome.error.status,
                    detail=outcome.error.detail,
                )
            self.ring.unpin(outcome.job.frame.frame_id)
            stuck = (
                outcome.error is not None and outcome.error.reason == "worker_stuck"
            )
            if outcome.job.purpose == "designate":
                self._handle_designate_outcome(outcome)
            else:
                self._handle_verify_outcome(outcome)
            if stuck and self.state != "TERMINAL" and self.reason != "backend_fatal":
                # U-A-2：回包因旧 `epoch`/`segment_index`/`verify_epoch` 被丢弃时，
                # 丢的只是**结果**；worker 生命周期故障仍须到达 `backend_fatal`
                # （AC-16 修订 1「backend_fatal 独立终止不被屏蔽」、AC-17 修订 1）。
                self._handle_backend_fatal(outcome.error)

    def _stale_epoch(self, job: QueryJob) -> bool:
        if job.epoch != self.epoch:
            return True
        if job.purpose == "verify" and job.verify_epoch != self.verify_epoch:
            return True
        if job.purpose == "verify" and job.segment_index != (
            self.segment_index if self.track_id else None
        ):
            return True
        return False

    def _handle_designate_outcome(self, outcome: QueryOutcome) -> None:
        job = outcome.job
        if self._stale_epoch(job) or self.state != "QUERYING":
            self._append_result_line(
                {
                    "query_id": job.query_id,
                    "status": "IGNORED_STALE_EPOCH",
                    "epoch": job.epoch,
                    "current_epoch": self.epoch,
                    "purpose": job.purpose,
                }
            )
            return
        if outcome.error is not None:
            if outcome.error.reason == "worker_stuck":
                # AC-8 修订 2 / AC-17 修订 1：超硬限之后**只允许 stop / 读状态**，
                # 不得先走一次普通重试再进 fatal——那既会再发一次查询，又会让
                # `worker.submit` 的 `SelectorError` 逃出 `tick()` 使会话无法 `stop`。
                self._emit_result(
                    purpose="designate",
                    status="backend_error",
                    reject_reason="worker_stuck",
                    frame=job.frame,
                    request_id=job.request_id,
                    job=job,
                    latency_ms=outcome.latency_ms,
                )
                self._handle_backend_fatal(outcome.error)
                return
            self._designate_failure(
                status=outcome.error.status,
                reject_reason=outcome.error.reason,
                frame=job.frame,
                request_id=job.request_id,
                job=job,
                latency_ms=outcome.latency_ms,
            )
            return
        reject_reason = self._check_return(job)
        if reject_reason is not None:
            self._designate_failure(
                status="stale_rejected",
                reject_reason=reject_reason,
                frame=job.frame,
                request_id=job.request_id,
                job=job,
                latency_ms=outcome.latency_ms,
            )
            return
        selection = interpret(outcome.raw)
        if selection.status in {"none", "parse_failed"}:
            self._designate_failure(
                status=selection.status,
                reject_reason=None,
                frame=job.frame,
                request_id=job.request_id,
                job=job,
                latency_ms=outcome.latency_ms,
                selection=selection,
            )
            return
        # A4：已过返回检查点、解释为 unique/ambiguous 的结果先记「到达」；呈现（结果行、呈现时刻、
        # `AWAITING_CONFIRMATION` 迁移）挂起 Δ 后由 `_maybe_present` 完成。Δ = 0 同 tick 呈现，与现行一致。
        delay_s = float(self._designate_delay_s)
        arrived = float(self._monotonic())
        self._journal(
            "result_arrived",
            query_id=job.query_id,
            request_id=job.request_id,
            status=selection.status,
            head_frame_id=self._head_frame_id(),
            delay_s=delay_s,
        )
        self._pending_presentation = {
            "job": job,
            "selection": selection,
            "latency_ms": outcome.latency_ms,
            "epoch": job.epoch,
            "delay_s": delay_s,
            "due_monotonic_s": arrived + delay_s,
        }
        self._maybe_present()

    def _head_frame_id(self) -> int | None:
        """A4：「结果到达/呈现」时刻会话已处理的最新传感器帧（常驻 = 关联器历史头；否则 = 最近处理帧）。"""
        core = getattr(getattr(self.loop, "tracker", None), "core", None) if self.loop is not None else None
        head = getattr(core, "head_frame_id", None) if core is not None else None
        if isinstance(head, int):
            return head
        return self.processed[-1].frame_id if self.processed else None

    def _maybe_present(self) -> None:
        """A4：Δ 到期即呈现；纪元已变或状态已离开 `QUERYING` 即丢弃（不补写结果行）。"""
        pending = self._pending_presentation
        if pending is None:
            return
        if pending["epoch"] != self.epoch:
            self._discard_pending_presentation("epoch_changed")
            return
        if self.state != "QUERYING":
            self._discard_pending_presentation("state_changed")
            return
        if float(self._monotonic()) < float(pending["due_monotonic_s"]):
            return
        self._pending_presentation = None
        job: QueryJob = pending["job"]
        selection: Selection = pending["selection"]
        # 以下呈现步骤与 Δ 引入前逐行相同（预览生成代码不改，只是调用时刻在呈现时）。
        self.candidates = selection.candidates
        self.candidate_frame = job.frame
        self.candidate_query_monotonic_s = job.submitted_monotonic_s
        self.candidate_query_id = job.query_id
        self.candidate_query_unix_s = job.query_unix_s
        self.candidate_preview_path = self._preview(job, selection.candidates, None)
        preview = self.candidate_preview_path
        result_id = self._emit_result(
            purpose="designate",
            status=selection.status,
            frame=job.frame,
            job=job,
            selection=selection,
            latency_ms=pending["latency_ms"],
            preview_path=preview,
            request_id=job.request_id,
        )
        self.candidate_result_id = result_id
        self.candidate_presented_monotonic_s = float(self._monotonic())
        self._journal(
            "result_presented",
            query_id=job.query_id,
            result_id=result_id,
            status=selection.status,
            delay_s=float(pending["delay_s"]),
            head_frame_id=self._head_frame_id(),
        )
        self._enter("AWAITING_CONFIRMATION", reason=None)

    def _discard_pending_presentation(self, reason: str) -> None:
        pending = self._pending_presentation
        if pending is None:
            return
        self._pending_presentation = None
        self._journal(
            "presentation_discarded",
            query_id=pending["job"].query_id,
            reason=reason,
            delay_s=float(pending["delay_s"]),
        )

    def _designate_failure(
        self,
        *,
        status: str,
        reject_reason: str | None,
        frame: QuerySnapshot | None,
        request_id: str | None,
        job: QueryJob | None = None,
        latency_ms: float | None = None,
        selection: Selection | None = None,
    ) -> None:
        """五类失败共用：写一份结果，`attempt` 递增或落 `retry_exhausted`。"""
        last_status, last_reason = status, reject_reason
        if self.attempt >= self.config.attempt_limit:
            self._emit_result(
                purpose="designate",
                status="retry_exhausted",
                frame=frame,
                job=job,
                latency_ms=latency_ms,
                request_id=request_id,
                last_status=last_status,
                last_reject_reason=last_reason,
                selection=selection,
            )
            self._after_designate_failure("retry_exhausted")
            return
        self._emit_result(
            purpose="designate",
            status=status,
            reject_reason=reject_reason,
            frame=frame,
            job=job,
            latency_ms=latency_ms,
            request_id=request_id,
            selection=selection,
        )
        self.attempt += 1
        if frame is not None:
            self._retry_min_frame_id = frame.frame_id
        self._retry_waiting_since = None
        self._issue_designate(request_id, None)

    def _resume_designate_retry(self) -> None:
        if self.state != "QUERYING":
            return
        if self._pending_presentation is not None:
            # A4：呈现挂起中不再发起查询（worker 空闲、T_hard 不计时）。
            return
        if self.worker.busy or self.worker.pending is not None:
            return
        if self.current_instruction is None:
            return
        if self._retry_min_frame_id is None and self._retry_waiting_since is None:
            return
        self._issue_designate(None, None)

    def _after_designate_failure(self, reason: str) -> None:
        """§3.4：有过段 → `REINIT_REQUIRED(reason)`；否则回 `IDLE`。

        常驻会话（§3.6「QUERYING（有指针）R_des(fail) → 按 LOOP-001 规则，指针不变」）：回到提问前的状态，
        指针与发布不受影响；提问前无指针时同样回到提问前状态（IDLE/LOST/REINIT_REQUIRED）。"""
        self._discard_candidates()
        if self.resident:
            self._journal("designate_failed_restore", reason=reason)
            self._restore_pre_query()
            return
        if self.segments_seeded > 0:
            self._enter("REINIT_REQUIRED", reason=reason)
        else:
            self._enter("IDLE", reason=None)

    def _discard_candidates(self) -> None:
        self.candidates = ()
        self.candidate_result_id = None
        self.candidate_frame = None
        self.candidate_presented_monotonic_s = None
        self.candidate_preview_path = None
        self.candidate_query_id = None
        self.candidate_query_unix_s = None

    # --- 检查点（§3.3） --------------------------------------------------

    def _check_return(self, job: QueryJob) -> str | None:
        """返回检查点：帧差、墙钟截止（含停帧）、N 的身份重核。"""
        try:
            latest = self.repository.latest_frame_id()
        except (FileNotFoundError, KeyError, ValueError, OSError):
            return "bundle_missing"
        delta = latest - job.frame.frame_id
        if delta < 0:
            return "negative_frame_delta"
        if delta > self.receipt.k_ret:
            return "frames_late_exceeded"
        elapsed = float(self._monotonic()) - job.submitted_monotonic_s
        if elapsed > self.receipt.t_ret_s:
            # 含停帧：`L_r == N` 但墙钟已过。
            return "wall_deadline_exceeded"
        return verify_frame_identity(self.repository.frames_directory, job.frame.snapshot)

    def _check_confirmation(self) -> str | None:
        """确认检查点：累计帧差、累计截止，外加 AC-2 修订 1 的呈现时刻窗口。"""
        frame = self.candidate_frame
        if frame is None:  # pragma: no cover - 状态保证
            return "bundle_missing"
        try:
            latest = self.repository.latest_frame_id()
        except (FileNotFoundError, KeyError, ValueError, OSError):
            return "bundle_missing"
        delta = latest - frame.frame_id
        if delta < 0:
            return "negative_frame_delta"
        if delta > self.receipt.k_ret + self.receipt.k_conf:
            return "frames_late_exceeded"
        now = float(self._monotonic())
        if self.candidate_query_monotonic_s is not None:
            if now - self.candidate_query_monotonic_s > self.receipt.t_ret_s + T_CONF_S:
                return "wall_deadline_exceeded"
        if self.candidate_presented_monotonic_s is not None:
            presented = now - self.candidate_presented_monotonic_s
            if presented < 0.0 or presented > T_CONF_S:
                return "wall_deadline_exceeded"
        return verify_frame_identity(self.repository.frames_directory, frame.snapshot)

    # --- 播种与段 ---------------------------------------------------------

    def _run_root(self) -> Path:
        if self.config.run_root is not None:
            return Path(self.config.run_root)
        return self.session_dir if self.config.diagnostic else self.runtime

    def _seed_segment(self, candidate: Candidate) -> None:
        frame = self.candidate_frame
        assert frame is not None
        self.segment_index += 1
        track_id = f"{self.session_id}-t{self.segment_index}"
        run_id = f"{self.session_id}-seg{self.segment_index}"
        logger = RunLogger(
            self._run_root(),
            run_id,
            {
                "work_id": "P1-ENG-LOOP-001",
                "session_id": self.session_id,
                "track_id": track_id,
                "segment_index": self.segment_index,
                "scenario_id": self.config.scenario_id or self.scenario.get("scenario_id"),
                "condition": self.config.condition,
                "tracker": self.config.tracker_name,
                "planned_duration_s": self.config.planned_duration_s,
                "k_receipt": self.receipt.payload(),
                "body_planner": None
                if self.body_runtime is None
                else self.body_runtime.identity,
                "diagnostic": self.config.diagnostic,
                "instruction_surface": self.current_instruction.surface
                if self.current_instruction
                else None,
            },
        )
        recording = RecordingRunLogger(logger, self._register_record)
        publisher = GatedPublisher(
            RuntimePublisher(self.runtime, self.config.expires_after_s),
            self.ring,
            frames_directory=self.repository.frames_directory,
            receipts_path=self.receipts_path,
            k_pub=self.receipt.k_pub,
            t_pub_s=self.receipt.t_pub_s,
            t_stall_s=T_STALL_S,
            track_id=track_id,
            monotonic=self._monotonic,
            unix=self._unix,
        )
        tracker = (
            self.config.tracker_factory()
            if self.config.tracker_factory is not None
            else create_tracker(self.config.tracker_name)
        )
        body: dict[str, Any] = {}
        if self.body_runtime is not None:
            # AC-4 修订 4：每段独立的规划器与估计器实例（不继承上一段的滞回或估计状态）。
            planner, estimator = self.body_runtime.fresh()
            body = {
                "body_planner": planner,
                "body_estimator": estimator,
                "body_expires_after_s": self.body_runtime.expires_after_s,
            }
        loop = TrackLoop(
            self.repository,
            tracker,
            publisher,
            recording,
            track_id=track_id,
            condition=self.config.condition,
            ground_plane_y_m=self.config.ground_plane_y_m,
            maximum_ground_range_m=self.config.maximum_ground_range_m,
            planned_duration_s=self.config.planned_duration_s,
            **body,
        )
        self.processed.clear()
        self._new_records = []
        self._confidences.clear()
        try:
            loop.initialize(frame.frame_id, candidate.bbox_xywh_norm)
        except FrameIdentityChanged as exception:
            self._abort_seeding(publisher, recording, "image_identity_changed", exception)
            return
        except FileNotFoundError as exception:
            self._abort_seeding(publisher, recording, "bundle_missing", exception)
            return
        except RuntimeError as exception:
            self._abort_seeding(publisher, recording, "tracker_rejected_init", exception)
            return
        except ValueError as exception:
            self._abort_seeding(publisher, recording, "metadata_invalid", exception)
            return
        publisher.unmute()
        self.segments_seeded += 1
        self.loop = loop
        self.publisher = publisher
        self.logger = recording
        self.track_id = track_id
        self.confirmed_instruction = self.current_instruction
        self.segment_started_frame_id = frame.frame_id
        self.since_frame_id = frame.frame_id
        self.last_progress_unix_s = float(self._unix())
        self.consecutive_alert = 0
        self.alert_kind = None
        self.last_verdict = None
        self.last_verified_frame_id = None
        self.in_flight_verify_query_id = None
        self.verify_epoch += 1
        self.next_due_unix_s = float(self._unix()) + self.config.verify_interval_s
        self._discard_candidates()
        self._journal(
            "segment_seeded",
            track_id=track_id,
            run_id=run_id,
            frame_id=frame.frame_id,
            candidate_index=candidate.index,
        )
        self._enter("TRACKING", reason=None)

    def _abort_seeding(
        self,
        publisher: GatedPublisher,
        logger: RecordingRunLogger,
        reason: str,
        exception: BaseException | None = None,
    ) -> None:
        """初始化前失败：不播种、不留活段（§3.3「不初始化」只限初始化前失败）。

        `segment_index` 只增不减：失败的那次已经建了段目录，`run_id` 不得复用。
        「有过段」由 `segments_seeded` 判断，所以中止不会把没播过种的会话说成有段。
        """
        publisher.finalize()
        logger.close()
        self._journal(
            "seeding_aborted",
            reason=reason,
            segment_index=self.segment_index,
            detail=None if exception is None else f"{type(exception).__name__}: {exception}",
        )
        self._discard_candidates()
        self._after_designate_failure(
            reason if reason in bridge.STATE_REASONS else "bundle_missing"
        )

    def _register_record(self, record: ProcessedFrame) -> None:
        self.processed.append(record)
        self._new_records.append(record)
        if record.confidence is not None:
            self._confidences.append(record.confidence)

    def _advance_segment(self) -> None:
        if self.resident:
            self._advance_resident()
            return
        if self.loop is None or self.state not in {"TRACKING", "SUSPECTED"}:
            return
        self._new_records = []
        seg_end: str | None = None
        try:
            processed = self.loop.process_available()
        except FrameIdentityChanged:
            seg_end = "image_identity_changed"
            processed = 0
        except FileNotFoundError:
            # `latest.json` 或帧成员消失：段按 `bundle_missing` fail-closed 终止。
            seg_end = "bundle_missing"
            processed = 0
        except ValueError:
            # 无 rate lifecycle 时坏元数据直接抛出（`track_loop.py:437-440`）。
            seg_end = "metadata_invalid"
            processed = 0
        if seg_end is None and self.publisher is not None and self.publisher.fatal_reason:
            seg_end = self.publisher.fatal_reason
        if seg_end is None and self.loop.terminal:
            seg_end = self._terminal_reason()
        now_unix = float(self._unix())
        if processed:
            self.last_progress_unix_s = now_unix
        raw_lost = any(not record.ok for record in self._new_records if record.event != "INIT")
        if self._new_records:
            self._journal(
                "frames_processed",
                count=len(self._new_records),
                frame_ids=[record.frame_id for record in self._new_records],
                raw_states=[record.state for record in self._new_records],
            )
        if seg_end is None and self.loop.complete:
            seg_end = "duration_reached"
        if seg_end is None and self.state in {"TRACKING", "SUSPECTED"}:
            if (
                self.last_progress_unix_s is not None
                and now_unix - self.last_progress_unix_s > T_STALL_S
            ):
                seg_end = "frame_stall"
        if seg_end is not None:
            self._finalize_segment(seg_end)
            self._enter("REINIT_REQUIRED", reason=seg_end)
            return
        if raw_lost and self.state == "TRACKING":
            self._raise_suspect("tracker_failure", "tracker_failure")

    def _terminal_reason(self) -> str:
        for record in reversed(self._new_records or list(self.processed)):
            if record.event in TERMINAL_EVENT_REASONS:
                return TERMINAL_EVENT_REASONS[record.event]
            if record.event is not None and record.state == "ERROR_REINIT_REQUIRED":
                # AC-4 修订 2：原事件逐字留痕并明确标为 `unexpected_segment_end`；
                # 这**不是** `tracker_state.reason` 的新增枚举，段仍按 metadata_invalid 终止。
                self._journal(
                    "unexpected_segment_end",
                    event=record.event,
                    reason=record.reason,
                    frame_id=record.frame_id,
                )
                return "metadata_invalid"
        return "metadata_invalid"

    def _finalize_segment(self, reason: str) -> None:
        """段 finalize：发布门关闭、`retired_track_ids` 追加恰一次。"""
        if self.resident:
            self._teardown_resident(reason)
            return
        if self.loop is None or self.track_id is None:
            return
        if self.publisher is not None:
            self.publisher.finalize()
        last_frame = self.processed[-1].frame_id if self.processed else self.since_frame_id
        self.retired_track_ids.append(
            {
                "track_id": self.track_id,
                "from_frame_id": self.segment_started_frame_id,
                "to_frame_id": last_frame,
                "retired_reason": reason,
            }
        )
        if self.logger is not None:
            try:
                self.logger.finalize()
            except (ValueError, FileNotFoundError, KeyError) as exception:
                self._journal("segment_summary_failed", detail=str(exception))
                self.logger.close()
        self._journal(
            "segment_retired",
            track_id=self.track_id,
            reason=reason,
            to_frame_id=last_frame,
        )
        self.loop = None
        self.publisher = None
        self.logger = None
        self.track_id = None
        self.in_flight_verify_query_id = None
        self.verify_epoch += 1
        self.next_due_unix_s = None


    # --- P1-ENG-ACQ-001 常驻会话（§3.5–§3.8） --------------------------------

    def _ensure_resident_loop(self) -> None:
        """会话启动（有帧后）即建单一常驻 `TrackLoop`；终止后下一 tick 从最新帧重建（历史随之清空）。"""
        if self.loop is not None or self.state == "TERMINAL":
            return
        try:
            latest = self.repository.latest_frame_id()
        except (FileNotFoundError, KeyError, ValueError, OSError):
            return
        self.resident_loops_started += 1
        run_id = f"{self.session_id}-resident{self.resident_loops_started}"
        placeholder_track = f"{self.session_id}-t0"
        logger = RunLogger(
            self._run_root(),
            run_id,
            {
                "work_id": "P1-ENG-CAPTURE-001" if self.capture else "P1-ENG-ACQ-001",
                "session_id": self.session_id,
                "resident": True,
                "scenario_id": self.config.scenario_id or self.scenario.get("scenario_id"),
                "condition": self.config.condition,
                "tracker": self.config.tracker_name,
                "planned_duration_s": self.config.planned_duration_s,
                "k_receipt": self.receipt.payload(),
                "acquire": self.config.acquire.payload(),
                "servo_omega_max_deg_s": self.config.servo_omega_max_deg_s,
                "body_planner": None if self.body_runtime is None else self.body_runtime.identity,
                "diagnostic": self.config.diagnostic,
            },
        )
        recording = RecordingRunLogger(logger, self._register_record)
        publisher = GatedPublisher(
            RuntimePublisher(self.runtime, self.config.expires_after_s),
            self.ring,
            frames_directory=self.repository.frames_directory,
            receipts_path=self.receipts_path,
            k_pub=self.receipt.k_pub,
            t_pub_s=self.receipt.t_pub_s,
            t_stall_s=T_STALL_S,
            track_id=placeholder_track,
            monotonic=self._monotonic,
            unix=self._unix,
            # P1-ENG-LOOP-002 A3：常驻路径的显式 `hold_body()` 补写 `body_safety_hold` 收据（段式路径不变）。
            hold_receipts=True,
            # P1-ENG-FASTFIX-001 G1：只在捕获模式启用分级门与按最新帧结算（兼容模式 `_gate` 首拒即致命不变）。
            **({"classified": True, "n_drop": self.fastfix.n_drop} if self.capture and self.fastfix is not None else {}),
        )
        # R2-1：跨载体承接会话最后已写云台点（首个载体为 None，与原先相同）。
        publisher.last_gimbal_point_world_m = self._last_gimbal_point_world_m
        # A5：真实常驻插件经会话缓存加载器构造——重建 `TrackLoop`/关联器但不再调用底层权重加载。
        if self.config.tracker_factory is not None:
            tracker = self.config.tracker_factory()
        elif self.capture:
            # C1/C2：只有捕获模式会话入口显式传 `unify_vehicle` + `pose-center`（构造器缺省不变）。
            tracker = create_tracker(
                self.config.tracker_name,
                resident=True,
                model_loader=self._model_cache.load,
                class_policy=CAPTURE_CLASS_POLICY,
                gmc_source=CAPTURE_GMC_SOURCE,
                history_view=CAPTURE_HISTORY_VIEW,
            )
        else:
            tracker = create_tracker(
                self.config.tracker_name, resident=True, model_loader=self._model_cache.load
            )
        attach = getattr(tracker, "attach_frame_source", None)
        if callable(attach):
            # 第二级帧源 = 载体同一 `FrameRepository` 的只读原件（不经会话快照环，不改发布门信任根）。
            attach(FrameRepository(self.runtime, image_loader=self.config.decode))
        body: dict[str, Any] = {}
        if self.body_runtime is not None:
            planner, estimator = self.body_runtime.fresh()
            body = {"body_planner": planner, "body_estimator": estimator, "body_expires_after_s": self.body_runtime.expires_after_s}
        loop = TrackLoop(
            self.repository,
            tracker,
            publisher,
            recording,
            track_id=placeholder_track,
            condition=self.config.condition,
            ground_plane_y_m=self.config.ground_plane_y_m,
            maximum_ground_range_m=self.config.maximum_ground_range_m,
            planned_duration_s=self.config.planned_duration_s,
            resident_publish_window=self.receipt.k_pub,
            servo_max_deg_per_frame=self.config.servo_omega_max_deg_s / self.receipt.hz,
            **({"capture_hook": _CaptureHook(self)} if self.capture else {}),
            **body,
        )
        if not loop.resident:
            publisher.finalize()
            recording.close()
            raise ConfigMismatch("CONFIG_MISMATCH: resident session needs a resident tracker (det-assoc-v1 resident)")
        publisher.unmute()
        self.processed.clear()
        self._new_records = []
        self._capture_tracker = tracker
        try:
            loop.start(latest)
        except (FrameIdentityChanged, FileNotFoundError, ValueError) as exception:
            publisher.finalize()
            recording.close()
            self._journal("resident_start_failed", frame_id=latest, detail=f"{type(exception).__name__}: {exception}")
            return
        self.loop = loop
        self.publisher = publisher
        self.logger = recording
        self.segment_started_frame_id = latest
        self.last_progress_unix_s = float(self._unix())
        if self.target_manager is not None:
            # §3.5：管理器的绑定端口 = 本载体的指针核心（重建后重新接上；episode 计数跨载体延续）。
            self.target_manager.attach_port(getattr(tracker, "core", tracker))
            if self.capture:
                self.target_manager.on_watchdog(stale=False, at_monotonic_s=float(self._monotonic()))
        bind = getattr(self.config.adapter, "bind_history", None)
        if callable(bind):
            bind(tracker.history)
        # A5 / AC-14：模型加载计数随段日志落盘（每会话 = 1；重建复用缓存不增）。
        model_cache = dict(
            self._model_cache.payload(),
            resident_rebuilds=self.resident_rebuilds,
            rebuild_limit=RESIDENT_REBUILD_LIMIT,
        )
        recording.snapshot_json("model_cache.json", model_cache)
        reacquiring = self.capture and self.target_manager is not None and self.target_manager.reacquire_pending
        # FASTFIX §3.3：重捕窗口起点 = 本事件；`m_ready` 与事件同源 monotonic（同一读数写进事件并交管理器）。
        m_ready = float(self._monotonic()) if reacquiring else None
        self._journal(
            "resident_loop_started",
            run_id=run_id,
            frame_id=latest,
            manifest=_jsonable(tracker.manifest_identity()),
            **model_cache,
            **({"reacquire_window": {"f_ready": latest, "m_ready": m_ready}} if reacquiring else {}),
        )
        if reacquiring:
            assert self.target_manager is not None and m_ready is not None
            if self.target_manager.open_reacquire_window(f_ready=latest, m_ready=m_ready, hz=self.receipt.hz):
                self._enter("REINIT_REQUIRED", reason=tmgr.REASON_REACQUIRING)
            self._handle_reacquire_result()

    def _pointer_active(self) -> bool:
        return self.track_id is not None or self.state == "ACQUIRING"

    def _advance_resident(self) -> None:
        self._ensure_resident_loop()
        if self.loop is None:
            return
        self._new_records = []
        self._capture_outcomes = []
        self._batch_settle = None
        seg_end: str | None = None
        seg_source: str | None = None
        try:
            processed = self.loop.process_available()
        except FrameIdentityChanged:
            seg_end, processed = "image_identity_changed", 0
        except FileNotFoundError:
            seg_end, processed = "bundle_missing", 0
        except ValueError:
            seg_end, processed = "metadata_invalid", 0
        if seg_end is None and self.publisher is not None and self.publisher.fatal_reason:
            seg_end = self.publisher.fatal_reason
            seg_source = "publisher"
        if seg_end is None and self.loop.terminal:
            seg_end = self._terminal_reason()
        now_unix = float(self._unix())
        if processed:
            self.last_progress_unix_s = now_unix
        if self._new_records:
            # A6（H-2 运行时侧摘要）：对每个已处理帧的 `runtime/frames/frame_<N>.json` 当刻字节求 sha256，
            # 与 `frame_ids` 同序；读不到 → null 并附原因（只改本模块，不改 Unity、不复制旁车）。
            digests, missing = self._metadata_digests([record.frame_id for record in self._new_records])
            self._journal(
                "frames_processed",
                count=len(self._new_records),
                frame_ids=[record.frame_id for record in self._new_records],
                raw_states=[record.state for record in self._new_records],
                metadata_sha256=digests,
                metadata_sha256_missing_reason=missing,
            )
        tracker = self.loop.tracker
        drain = getattr(getattr(tracker, "core", None), "drain_events", None)
        coasting_ended = False
        if callable(drain):
            for event in drain():
                self._journal(event.get("event", "core_event"), **{k: v for k, v in event.items() if k != "event"})
                if (
                    event.get("event") == "COASTING_TO_TRACK_ENDED"
                    and self.designation is not None
                    and event.get("designation_id") == self.designation.get("designation_id")
                ):
                    # §3.4：`BOUND_COASTING` 超时（从未找回）→ 转 `TRACK_ENDED` 处置；同一 designation_id 之内，
                    # 尚未捕获，第三级转向重捕属 D.1 允许的自动执行。
                    self.designation["result"] = TRACK_ENDED
                    coasting_ended = True
        if seg_end is None and self.loop.complete:
            seg_end = "duration_reached"
        if seg_end is None and self._pointer_active():
            if self.last_progress_unix_s is not None and now_unix - self.last_progress_unix_s > T_STALL_S:
                seg_end = "frame_stall"
                if self.capture and self.target_manager is not None:
                    # #8：无新帧 > T_STALL_S → STALE，撤权（显式 hold），不续发运动命令。
                    self.target_manager.on_watchdog(stale=True, at_monotonic_s=float(self._monotonic()))
                    self._capture_hold("frame_stall")
        if seg_end is not None:
            pointer_was_active = self._pointer_active()
            if seg_end in RESIDENT_TERMINAL_SEG_END:
                # A5：常驻段仿真时长到点 → 会话 `TERMINAL(duration_reached)`，不重建（D1 (f)）。
                self._acquire = None
                self.stop(seg_end)
                return
            # FASTFIX §3.3：拆载体前（旧载体仍在）按「时序升级」与否生成重捕提示或记 `reacquire_skipped`；
            # 有提示时退指针不取消任务（回 ACQUIRING），无提示保持现行取消。
            hint = self._prepare_reacquire_hint(seg_end, seg_source)
            self._teardown_resident(seg_end, cancel_task=hint is None)
            if self.resident_rebuilds >= RESIDENT_REBUILD_LIMIT:
                # A5：第 3 次需要重建 → `TERMINAL(rebuild_limit)`（STOP `S-REBUILD`）。
                self._acquire = None
                self._journal(
                    "resident_rebuild_limit",
                    seg_end=seg_end,
                    resident_rebuilds=self.resident_rebuilds,
                    rebuild_limit=RESIDENT_REBUILD_LIMIT,
                )
                self.stop("rebuild_limit")
                return
            # 其余 `seg_end`（发布门/帧异常/`frame_stall`）沿现行恢复：下一 tick 由缓存模型重建载体。
            self.resident_rebuilds += 1
            if pointer_was_active or self.state in {"TRACKING", "SUSPECTED", "ACQUIRING"}:
                self._acquire = None
                self._enter("REINIT_REQUIRED", reason=seg_end)
            return
        if self.capture:
            self._expire_reacquire_tick()
            self._apply_capture_projection()
            return
        if self.state == "ACQUIRING":
            self._acquire_step([record.frame_id for record in self._new_records])
            return
        if coasting_ended and self.state == "TRACKING" and self._designated_box is not None and self.designation is not None:
            self._begin_acquiring(
                int(self.designation["designation_id"]),
                self.designation.get("track_id"),
                self._designated_box,
                int(self.designation["frame_id_k"]),
            )
            return
        removed = any(
            (not record.ok) and record.reason == "bound_track_removed" for record in self._new_records
        )
        if removed and self.state == "TRACKING" and self.track_id is not None:
            # §3.6：捕获后的丢失只由人处置——不自动重捕（D.1）。
            self._raise_suspect("tracker_failure", "tracker_failure")

    def _apply_capture_projection(self) -> None:
        """§3.6：管理器（捕获模式）状态投影到九态外壳；只取本批最后一帧的投影。

        捕获模式下「库删 ID 后才报 tracker_failure」不再触发（BROKEN 先报）。"""
        if self.target_manager is None or self.target_manager.binding is None or self.track_id is None:
            return
        projection = next((o.projection for o in reversed(self._capture_outcomes) if o.projection is not None), None)
        if projection is None:
            return
        state, reason = projection
        settle = self._batch_settle
        if (
            state == "TRACKING"
            and reason in (None, tmgr.REASON_PREDICTING)
            and settle is not None
            and settle.get("outcome") == SETTLE_DROPPED
        ):
            # FASTFIX §3.2：本批最新帧发布被时序丢弃 → `TRACKING/publish_degraded`（管理器其他原因优先；下一 PUBLISHED 帧恢复）。
            reason = tmgr.REASON_PUBLISH_DEGRADED
        if state == "SUSPECTED":
            if self.state != "SUSPECTED" or self.reason != reason:
                kind = "ambiguous" if reason == tmgr.REASON_DISPUTED else "lost"
                self._suspect_sequence += 1
                self.suspect_kind = kind
                self.suspect_id = f"{self.session_id}-s{self._suspect_sequence}"
                self.suspect_reason = reason
                self._journal("suspect_raised", suspect_kind=kind, reason=reason, suspect_id=self.suspect_id)
                self._enter("SUSPECTED", reason=reason)
            return
        if self.state != "TRACKING" or self.reason != reason:
            self._enter("TRACKING", reason=reason)

    def _metadata_digests(self, frame_ids: Sequence[int]) -> tuple[list[str | None], list[str | None]]:
        digests: list[str | None] = []
        missing: list[str | None] = []
        for frame_id in frame_ids:
            try:
                _image, metadata_path = self.repository.frame_paths(int(frame_id))
                digests.append(sha256_bytes(Path(metadata_path).read_bytes()))
                missing.append(None)
            except FileNotFoundError:
                digests.append(None)
                missing.append("file_missing")
            except (OSError, KeyError, ValueError) as exception:
                digests.append(None)
                missing.append(f"unreadable:{type(exception).__name__}")
        return digests, missing

    def _retire_pointer(self, reason: str, *, clear_core: bool = True, cancel_task: bool = True) -> None:
        """退指针（纪元结束）：`retired_track_ids` 追加恰一次；常驻关联器不动。

        `clear_core=False` 只结束对外纪元、不动核心指针（`designate` 已把核心指针换成新 j 时使用，保留其 coasting 记账）。"""
        if self.track_id is None:
            return
        last_frame = self.processed[-1].frame_id if self.processed else self.since_frame_id
        self.retired_track_ids.append(
            {
                "track_id": self.track_id,
                "from_frame_id": self.segment_started_frame_id,
                "to_frame_id": last_frame,
                "retired_reason": reason,
            }
        )
        self._journal("segment_retired", track_id=self.track_id, reason=reason, to_frame_id=last_frame)
        if clear_core and self.target_manager is not None:
            # C5/§3.5：会话内一切清指针都经唯一入口 `release_binding`（不再动态 `follow(None)`）。
            self.target_manager.release_binding(reason, cancel_task=cancel_task)
        self.track_id = None
        self.in_flight_verify_query_id = None
        self.verify_epoch += 1
        self.next_due_unix_s = None

    def _teardown_resident(self, reason: str, *, cancel_task: bool = True) -> None:
        """会话级终止（回退/缺帧/门拒/停帧/stop）：退指针后关闭常驻载体，历史清空。

        FASTFIX §3.3：`cancel_task=False` 只在已生成重捕提示时（`release_binding` 任务回 ACQUIRING，TaskSpec 不变）。"""
        self._retire_pointer(reason, cancel_task=cancel_task)
        self._hint_candidates.clear()
        self._hint_pending.clear()
        if self.loop is None:
            return
        if self.publisher is not None:
            self.publisher.finalize()
            # R2-1：保存最后已写云台点，供下一 tick 重建的载体作为限速基准。
            written = getattr(self.publisher, "last_gimbal_point_world_m", None)
            if written is not None:
                self._last_gimbal_point_world_m = written
        if self.logger is not None:
            try:
                self.logger.finalize()
            except (ValueError, FileNotFoundError, KeyError) as exception:
                self._journal("segment_summary_failed", detail=str(exception))
                self.logger.close()
        self._journal("resident_loop_closed", reason=reason)
        if self.target_manager is not None:
            # §3.5 拆除：管理器收到 resident_teardown 关闭 episode（无 follow；核心随载体丢弃）。
            self.target_manager.on_teardown(reason)
        self.loop = None
        self.publisher = None
        self.logger = None

    # --- P1-ENG-FASTFIX-001：降级/升级记账、逐阶段耗时、重捕提示与窗口 -----------------------------------

    def _note_hint_candidate(self, entry: Any) -> None:
        """本批最新帧、管理器本帧已接受观测：深复制绑定键 `tracker.step` 返回后的完整 KF（posterior）与该帧位姿，
        待帧结算（无完整性命中）后才入提示候选；拆载体时不现取旧状态冒充更早的 f_last。"""
        manager = self.target_manager
        self._hint_pending.clear()
        if not self.capture or manager is None or manager.binding is None or manager.belief is None:
            return
        frame_id = int(entry.frame_id)
        if manager.belief.observation_status != tmgr.OBSERVED or manager.belief.t0 != frame_id:
            return
        key = manager.binding.track_key
        associator = getattr(self._capture_tracker, "associator", None)
        state = full_kf_state_from_associator(
            associator, key, sensor_frame_id=frame_id, library_frame_id=int(entry.library_frame_id)
        )
        self._hint_pending[frame_id] = (key, state, tmgr.pose_metadata_of(entry))

    def _on_frame_settled(self, settle: Mapping[str, Any]) -> None:
        self._batch_settle = settle
        frame_id = int(settle["frame_id"])
        pending = self._hint_pending.pop(frame_id, None)
        self._hint_pending.clear()
        if pending is not None and settle.get("outcome") in (SETTLE_PUBLISHED, SETTLE_DROPPED):
            key, state, pose = pending
            self._hint_candidates.append(tmgr.HintCandidate(frame_id, key, state, pose, str(settle["outcome"])))
        n_drop = None if self.fastfix is None else self.fastfix.n_drop
        if settle.get("outcome") == SETTLE_DROPPED:
            self._journal(
                "publish_dropped",
                frame_id=frame_id,
                reasons=list(settle.get("temporal_reasons") or []),
                streak=settle.get("streak"),
                n_drop=n_drop,
                escalated=bool(settle.get("escalated")),
                fastfix_config_sha256=self.fastfix_sha256,
            )
        if settle.get("escalated"):
            escalation = getattr(self.publisher, "escalation", None) or {}
            self._journal(
                "publish_escalated",
                frame_id=frame_id,
                reason=escalation.get("reason"),
                streak=settle.get("streak"),
                n_drop=n_drop,
                fastfix_config_sha256=self.fastfix_sha256,
            )

    def _journal_frame_timing(self, record: Mapping[str, Any]) -> None:
        """§3.5：每个被处理帧恰一条 `frame_timing`；本条自身写盘耗时记在下一条 `journal_prev_s`（单列，不入任何 total）。"""
        fields = dict(record)
        previous = self._journal_prev
        fields["journal_prev_s"] = None if previous is None else previous[0]
        fields["journal_prev_frame_id"] = None if previous is None else previous[1]
        started = float(self._monotonic())
        self._journal("frame_timing", **fields)
        self._journal_prev = (float(self._monotonic()) - started, int(record["frame_id"]))

    def _prepare_reacquire_hint(self, seg_end: str, seg_source: str | None) -> Any:
        """§3.3 提示生成（拆载体前）：只在「时序升级」导致的拆载体生成；其余有绑定的拆载体记 `reacquire_skipped`。"""
        manager = self.target_manager
        if not self.capture or manager is None or self.fastfix is None:
            return None
        escalation = getattr(self.publisher, "escalation", None) if self.publisher is not None else None
        timing = seg_source == "publisher" and escalation is not None and escalation.get("reason") == seg_end
        if not timing and manager.binding is None:
            return None
        hint = manager.prepare_reacquire_hint(
            seg_end=seg_end,
            timing_escalation=timing,
            escalation_frame=None if escalation is None else escalation.get("frame_id"),
            auto_reacquire=self.fastfix.auto_reacquire,
            candidates=list(self._hint_candidates),
        )
        if hint is not None:
            self._reacq_token = self.track_id
            self._reacq_predictor = library_kf_predictor(getattr(self._capture_tracker, "associator", None), hint.track_key)
        return hint

    def _expire_reacquire_tick(self) -> None:
        """§3.3：到期判定每 tick 执行（零新帧亦然）。"""
        manager = self.target_manager
        if not self.capture or manager is None or not manager.reacquire_open:
            return
        if manager.expire_reacquire(at_monotonic_s=float(self._monotonic())):
            self._handle_reacquire_result()

    def _handle_reacquire_result(self) -> None:
        """管理器重捕终局 → 会话外部副作用：提交 = 新指针纪元 + `TRACKING/rebuild_reacquired`；失败/歧义 =
        `REINIT_REQUIRED/reacquire_failed|reacquire_ambiguous`（显式报告、等人点击）；回滚失败沿现行 fail-closed。
        取消由取消方（stop/release/点击）设定会话状态。"""
        manager = self.target_manager
        if manager is None:
            return
        result = manager.take_reacquire_result()
        if result is None:
            return
        kind = result.get("result")
        if kind == "committed":
            self._pre_query = None
            self._reacq_token = None
            self._new_pointer_epoch(int(result["track_key"]), result.get("frame_id"))
            self._enter("TRACKING", reason=tmgr.REASON_REBUILD_REACQUIRED)
        elif kind in ("failed", "ambiguous"):
            self._reacq_token = None
            self._enter("REINIT_REQUIRED", reason=result.get("reason"))
        elif kind == "rollback_failed":
            self._reacq_token = None
            self._binding_fail_closed()

    def _restore_pre_query(self) -> None:
        previous = self._pre_query
        self._pre_query = None
        if previous is None:
            self._enter("IDLE", reason=None)
            return
        state, reason, suspect_kind, suspect_id, suspect_reason = previous
        if state == "TRACKING" and self.track_id is None:
            state, reason = "LOST", reason or "tracker_failure"
        if state == "SUSPECTED" and (self.track_id is None or suspect_id is None):
            state, reason = "LOST", suspect_reason or "tracker_failure"
        if state == "SUSPECTED":
            self.suspect_kind, self.suspect_id, self.suspect_reason = suspect_kind, suspect_id, suspect_reason
        if state in {"LOST", "REINIT_REQUIRED"} and reason is None:
            reason = "operator_reject"
        self._enter(state, reason=reason)

    def _new_pointer_epoch(self, track_id: int, frame_id: int | None) -> None:
        """对外 `track_id = <session>-t<n>`，n 随每次 `BOUND` 递增；旧指针进 `retired_track_ids`。"""
        if self.track_id is not None:
            # 跟踪中改指定：旧纪元由操作者的新确认释放（`retired_reason` 取既有闭集 `operator_release`；
            # 捕获模式的点击换目标记 `superseded_by_click`）。
            self._retire_pointer("superseded_by_click" if self.capture else "operator_release", clear_core=False)
        assert self.loop is not None
        # C5：核心指针已由 `TargetManager.commit_binding` 在此之前写好；这里只执行外部纪元副作用（AR1-3）。
        self.segment_index += 1
        external = f"{self.session_id}-t{self.segment_index}"
        self.track_id = external
        self.loop.track_id = external
        if self.publisher is not None:
            self.publisher.track_id = external
        self.segments_seeded += 1
        self.confirmed_instruction = self.current_instruction
        self.segment_started_frame_id = frame_id
        self.since_frame_id = frame_id
        self.consecutive_alert = 0
        self.alert_kind = None
        self.last_verdict = None
        self.last_verified_frame_id = None
        self.in_flight_verify_query_id = None
        self.verify_epoch += 1
        self.next_due_unix_s = float(self._unix()) + self.config.verify_interval_s
        self._confidences.clear()
        self._journal("pointer_bound", track_id=external, library_track_id=int(track_id), frame_id=frame_id)

    def _designate_resident(self, candidate: Candidate) -> None:
        """§3.6：`confirm k` → `designate(box_k, N)`；六值迁移。第二级回放同步有界（≤ `T_replay`），
        期间状态停留在 `AWAITING_CONFIRMATION`、不 `step` 新帧、不发布。"""
        frame = self.candidate_frame
        assert frame is not None
        self._advance_resident()  # 追平到 ≥ N（常驻 step，不是 init 回放）
        if self.state == "TERMINAL":
            # A5：追平途中会话已终止——指定不可用，状态保持 TERMINAL（不回退到提问前状态）。
            self._journal("designation_unavailable", reason="session_terminal", frame_id=frame.frame_id)
            self._discard_candidates()
            return
        if self.loop is None:
            self._journal("designation_unavailable", reason="resident_loop_absent", frame_id=frame.frame_id)
            self._discard_candidates()
            self._restore_pre_query()
            return
        # AR1-3：尝试分配与绑定事务两阶段——先取号（失败也占号），再纯解析，结果照旧记录，BOUND* 再经提交。
        tracker = self.loop.tracker
        core = tracker.core
        designation_id = core.allocate_designation_id()
        designation = tracker.resolve_designation(candidate.bbox_xywh_norm, frame.frame_id, designation_id)
        core.record_designation(designation)
        self._designated_box = tuple(candidate.bbox_xywh_norm)
        record = designation.as_record()
        for event in designation.events:
            self._journal(event["event"], **{k: v for k, v in event.items() if k != "event"})
        self._journal("designation", designation=record, candidate_index=candidate.index)
        self.designation = record
        self._discard_candidates()
        result = designation.result
        selector = tmgr.LanguageCompatSelector(designation_id, tuple(candidate.bbox_xywh_norm), int(frame.frame_id))
        if result in (BOUND, BOUND_COASTING):
            assert self.target_manager is not None and designation.track_id is not None
            commit = self.target_manager.commit_binding(
                origin="lang_confirm",
                track_key=int(designation.track_id),
                expected_version=self.target_manager.version,
                source_frame=int(frame.frame_id),
                commit_frame=designation.head_frame_id,
                evidence={"designation_id": designation_id, "result": result},
                selector=selector,
                coasting_designation_id=designation_id if result == BOUND_COASTING else None,
            )
            if commit.accepted:
                self._pre_query = None
                self._new_pointer_epoch(int(designation.track_id), designation.head_frame_id)
                self._enter("TRACKING", reason=None)
                return
            if commit.fail_closed:
                self._pre_query = None
                self._binding_fail_closed()
                return
            self._restore_pre_query()
            return
        if result == TRACK_ENDED:
            self._pre_query = None
            if self.target_manager is not None:
                self.target_manager.accept_language_task(selector, frame_id=int(frame.frame_id))
            self._begin_acquiring(designation.designation_id, designation.track_id, candidate.bbox_xywh_norm, frame.frame_id)
            return
        self._restore_pre_query()

    # --- §3.7 无同帧观测的转向通道 --------------------------------------------

    def _begin_acquiring(self, designation_id: int, track_id: int | None, box: Sequence[float], frame_id_k: int) -> None:
        assert self.loop is not None
        core = self.loop.tracker.core
        entry_k = core.history(frame_id_k)
        metadata_k = self._history_metadata(entry_k)
        acquire: dict[str, Any] = {
            "designation_id": designation_id,
            "started_monotonic_s": float(self._monotonic()),
            "arrived": False,
            "arrival_streak": 0,
            "window_frames": 0,
            "adopt_streak": 0,
            "adopt_track": None,
            "status": "SLEWING",
        }
        try:
            point = box_ground_intersection(
                box, metadata_k, self.config.ground_plane_y_m, self.config.maximum_ground_range_m
            ).point_world_m
        except (GeometryRejected, ValueError, TypeError) as exception:
            self._journal("acquire_geometry_rejected", detail=str(exception))
            # A7（ACQ R1-4 承接）：几何拒绝不再冒充转向超时，cause = `geometry_rejected`。
            self._acquire_failed(acquire, "geometry_rejected", designation_id=designation_id)
            return
        velocity = self._track_ground_velocity(core, int(track_id) if track_id is not None else None)
        acquire.update(
            {
                "world_point_k": list(point),
                "frame_id_k": frame_id_k,
                "time_k_s": entry_k.simulation_time_s if entry_k is not None else None,
                "velocity_world_mps": list(velocity) if velocity is not None else None,
            }
        )
        # R1-1（§3.7）：转向指令用外推世界点——k 帧点 + 地面差分速度 ×（发令时历史头仿真时刻 − t_k）；
        # 无速度（静止）时即 k 帧点。到位与收养判据沿用同一 `_acquire_point`。
        head_frame_id = core.head_frame_id
        head_entry = core.history(head_frame_id) if head_frame_id is not None else None
        slew_time_s = head_entry.simulation_time_s if head_entry is not None else None
        slew_point = self._acquire_point(acquire, slew_time_s)
        acquire.update({"slew_time_s": slew_time_s, "slew_point_world_m": list(slew_point)})
        # 旧指针退出（人已确认新目标）；转向期间无指针、无观测，机身只收 hold。
        # 已确认的语言任务进入 acquire（不取消，AR1-3 计数矩阵）。
        self._retire_pointer("operator_release", cancel_task=False)
        if self.publisher is not None:
            self.publisher.clear_association()
            self.publisher.hold_body(reason="acquiring")
            self.publisher.slew_look_at(slew_point, designation_id)
        self._acquire = acquire
        self._journal("acquire_started", **{k: v for k, v in acquire.items() if k != "started_monotonic_s"})
        self._update_designation_acquire()
        self._enter("ACQUIRING", reason=None)

    def _history_metadata(self, entry: Any) -> dict[str, Any]:
        if entry is None:
            return {}
        position = list(entry.camera_position_world_m or ())
        rotation = list(entry.camera_rotation_xyzw or ())
        metadata: dict[str, Any] = {
            "camera_position_world_m": position,
            "camera_rotation_xyzw": rotation,
            "intrinsics_px": dict(entry.intrinsics_px or {}),
            "width": entry.width or 640,
            "height": entry.height or 480,
        }
        if len(rotation) == 4:
            from .reanchor import _rotate_quaternion  # noqa: PLC0415

            metadata["camera_right_world"] = list(_rotate_quaternion((1.0, 0.0, 0.0), rotation))
            metadata["camera_up_world"] = list(_rotate_quaternion((0.0, 1.0, 0.0), rotation))
            metadata["camera_forward_world"] = list(_rotate_quaternion((0.0, 0.0, 1.0), rotation))
        return metadata

    def _track_ground_velocity(self, core: Any, track_id: int | None) -> tuple[float, float, float] | None:
        """k 帧命中轨迹有 ≥ 2 帧 tracked 历史时用其地面点差分速度（红车）；否则静止。"""
        if track_id is None:
            return None
        points: list[tuple[float, tuple[float, float, float]]] = []
        for frame_id in sorted(core._history):  # noqa: SLF001 — 只读历史
            entry = core.history(frame_id)
            row = entry.row(track_id)
            if row is None or row.state != ROW_TRACKED or entry.simulation_time_s is None:
                continue
            try:
                point = box_ground_intersection(
                    row.box_norm, self._history_metadata(entry), self.config.ground_plane_y_m, self.config.maximum_ground_range_m
                ).point_world_m
            except (GeometryRejected, ValueError, TypeError):
                continue
            points.append((entry.simulation_time_s, tuple(point)))
        if len(points) < 2 or points[-1][0] <= points[0][0]:
            return None
        (t0, p0), (t1, p1) = points[0], points[-1]
        return tuple((p1[i] - p0[i]) / (t1 - t0) for i in range(3))  # type: ignore[return-value]

    def _acquire_point(self, acquire: Mapping[str, Any], time_s: float | None) -> tuple[float, float, float]:
        point = acquire["world_point_k"]
        velocity = acquire.get("velocity_world_mps")
        if velocity is None or time_s is None or acquire.get("time_k_s") is None:
            return tuple(point)  # type: ignore[return-value]
        dt = float(time_s) - float(acquire["time_k_s"])
        return tuple(float(point[i]) + float(velocity[i]) * dt for i in range(3))  # type: ignore[return-value]

    def _acquire_step(self, frame_ids: Sequence[int]) -> None:
        acquire = self._acquire
        if acquire is None or self.loop is None:
            return
        params = self.config.acquire
        core = self.loop.tracker.core
        for frame_id in frame_ids:
            entry = core.history(frame_id)
            previous = core.history(frame_id - 1)
            if entry is None:
                continue
            metadata = self._history_metadata(entry)
            target = self._acquire_point(acquire, entry.simulation_time_s)
            pixel = project_world_point(target, metadata) if metadata.get("intrinsics_px") else None
            in_frame = pixel is not None and 0.0 <= pixel[0] < metadata["width"] and 0.0 <= pixel[1] < metadata["height"]
            if not acquire["arrived"]:
                rate = None
                if previous is not None and previous.camera_rotation_xyzw and entry.camera_rotation_xyzw and previous.simulation_time_s is not None and entry.simulation_time_s is not None and entry.simulation_time_s > previous.simulation_time_s:
                    rate = rotation_angle_deg(
                        {"camera_rotation_xyzw": list(previous.camera_rotation_xyzw)},
                        {"camera_rotation_xyzw": list(entry.camera_rotation_xyzw)},
                    ) / (entry.simulation_time_s - previous.simulation_time_s)
                settled = rate is not None and rate < params.omega_arr_deg_s and in_frame
                acquire["arrival_streak"] = acquire["arrival_streak"] + 1 if settled else 0
                if acquire["arrival_streak"] >= params.n_arr:
                    acquire["arrived"] = True
                    acquire["status"] = "ADOPTING"
                    acquire["arrived_frame_id"] = frame_id
                    self._journal("acquire_arrived", frame_id=frame_id, pixel=list(pixel) if pixel else None)
                elif float(self._monotonic()) - acquire["started_monotonic_s"] > params.t_slew_s:
                    self._acquire_failed(acquire, "slew_timeout")
                    return
                continue
            # 收养：到位后窗口 M 帧内，检测 track 框中心与投影点距离 ≤ r_adopt 连续 N 帧。
            acquire["window_frames"] += 1
            chosen, ambiguous = self._adoption_candidate(entry, pixel, params, metadata["width"], metadata["height"])
            if ambiguous:
                acquire["ambiguous_candidates"] = ambiguous
                self._acquire_failed(acquire, "adopt_timeout", result=DESIGNATION_AMBIGUOUS, candidates=ambiguous)
                return
            if chosen is not None and chosen == acquire["adopt_track"]:
                acquire["adopt_streak"] += 1
            else:
                acquire["adopt_track"] = chosen
                acquire["adopt_streak"] = 1 if chosen is not None else 0
            if acquire["adopt_streak"] >= params.n_adopt:
                self._acquire_adopted(acquire, int(chosen), frame_id)
                return
            if acquire["window_frames"] >= params.window_m:
                self._acquire_failed(acquire, "adopt_timeout")
                return
        if not acquire["arrived"] and float(self._monotonic()) - acquire["started_monotonic_s"] > params.t_slew_s:
            self._acquire_failed(acquire, "slew_timeout")

    def _adoption_candidate(
        self, entry: Any, pixel: tuple[float, float] | None, params: AcquireParams, width: int, height: int
    ) -> tuple[int | None, list[int]]:
        if pixel is None:
            return None, []
        distances = []
        for row in entry.rows(ROW_TRACKED):
            x, y, w, h = row.box_norm
            cx, cy = (x + w / 2.0) * width, (y + h / 2.0) * height
            distance = math.hypot(cx - pixel[0], cy - pixel[1])
            if distance <= params.r_adopt_px:
                distances.append((distance, row.track_id))
        distances.sort()
        if not distances:
            return None, []
        if len(distances) >= 2 and distances[1][0] - distances[0][0] < params.margin_px:
            return None, [track_id for _d, track_id in distances]
        return distances[0][1], []

    def _acquire_adopted(self, acquire: dict[str, Any], track_id: int, frame_id: int) -> None:
        if self.target_manager is not None:
            # §3.5 语言转向收养（lang_acquire）：现行判据原样，只改为经 `commit_binding` 写指针。
            commit = self.target_manager.commit_binding(
                origin="lang_acquire",
                track_key=int(track_id),
                expected_version=self.target_manager.version,
                source_frame=None,
                commit_frame=int(frame_id),
                evidence={"designation_id": acquire.get("designation_id")},
            )
            if not commit.accepted:
                if commit.fail_closed:
                    self._acquire = None
                    self._binding_fail_closed()
                return
        acquire["status"] = "ADOPTED"
        acquire["adopted_track_id"] = track_id
        self._journal("acquire_adopted", designation_id=acquire["designation_id"], track_id=track_id, frame_id=frame_id)
        self._acquire = None
        if self.designation is not None:
            self.designation["result"] = BOUND
            self.designation["track_id"] = track_id
        self._update_designation_acquire(acquire)
        self._new_pointer_epoch(track_id, frame_id)
        self._enter("TRACKING", reason=None)

    def _acquire_failed(self, acquire: dict[str, Any], cause: str, *, result: str | None = None, candidates: Sequence[int] = (), designation_id: int | None = None) -> None:
        """`ACQUIRE_FAILED`：`hold_body`，云台停在当前指向，`LOST(acquire_failed)`；不重试、不自动重播种。"""
        acquire["status"] = "ACQUIRE_FAILED"
        acquire["cause"] = cause
        self._journal("acquire_failed", designation_id=acquire.get("designation_id", designation_id), cause=cause, candidates=list(candidates))
        if self.publisher is not None:
            self.publisher.hold_body(reason="acquire_failed")
        self._acquire = None
        if self.designation is not None and result is not None:
            self.designation["result"] = result
            self.designation["candidates"] = list(candidates)
        self._update_designation_acquire(acquire)
        self._retire_pointer("acquire_failed")
        if self.target_manager is not None:
            # release / teardown（含 acquire 失败）：无绑定可关；已确认的 acquire 任务随之结束。
            self.target_manager.release_binding("acquire_failed", cancel_task=True)
        self._enter("LOST", reason="acquire_failed")

    def _update_designation_acquire(self, acquire: Mapping[str, Any] | None = None) -> None:
        source = acquire if acquire is not None else self._acquire
        if self.designation is None or source is None:
            return
        self.designation["acquire"] = {
            key: source.get(key)
            for key in ("status", "cause", "world_point_k", "velocity_world_mps", "arrived_frame_id", "adopted_track_id", "ambiguous_candidates")
            if source.get(key) is not None
        }

    # --- 角色 B：语义核验（§3.6） ----------------------------------------

    def _maybe_verify(self) -> None:
        if self.state != "TRACKING" or self.loop is None:
            return
        now = float(self._unix())
        if self.next_due_unix_s is not None and now >= self.next_due_unix_s:
            self._request_verification("due")
            return
        latest_record = self._latest_record()
        if latest_record is None or latest_record.box_norm is None:
            return
        if _touches_border(latest_record.box_norm):
            self._request_verification("border")
            return
        if self._score_dropped(latest_record.confidence):
            self._request_verification("score")

    def _score_dropped(self, confidence: float | None) -> bool:
        if confidence is None or len(self._confidences) < 5:
            return False
        ordered = sorted(self._confidences)
        middle = len(ordered) // 2
        median = (
            ordered[middle]
            if len(ordered) % 2
            else (ordered[middle - 1] + ordered[middle]) / 2.0
        )
        return confidence < median / 2.0

    def _request_verification(self, source: str) -> None:
        now = float(self._unix())
        last = self._trigger_last.get(source)
        if source != "due" and last is not None and now - last < TRIGGER_RATE_LIMIT_S:
            return
        if self.state not in {"TRACKING", "SUSPECTED"} or self.loop is None:
            return
        if self.worker.stuck:
            return
        if self.worker.busy or self.worker.pending is not None:
            # worker 忙则等下一轮询；触发不改状态。
            return
        instruction = self.confirmed_instruction
        if instruction is None:  # pragma: no cover - 段存在即有已确认指令
            return
        self._trigger_last[source] = now
        paired = self._pairing_frame()
        if paired is None:
            return
        record, snapshot = paired
        self._submit_query(
            purpose="verify",
            instruction=instruction,
            frame=snapshot,
            tracker_box=record.box_norm,
        )
        if source == "due":
            self.next_due_unix_s = now + self.config.verify_interval_s

    def _latest_record(self) -> ProcessedFrame | None:
        for record in reversed(self.processed):
            if record.event != "INIT" or record.box_norm is not None:
                return record
        return None

    def _pairing_frame(self) -> tuple[ProcessedFrame, QuerySnapshot] | None:
        """配对帧 P = 本段最近一帧**已处理**的帧（不是 latest）。"""
        record = self._latest_record()
        if record is None:
            return None
        if (
            self.last_verified_frame_id is not None
            and record.frame_id <= self.last_verified_frame_id
        ):
            self._record_skip("same_frame", record.frame_id)
            return None
        if record.box_norm is None:
            self._record_skip("no_tracker_box", record.frame_id)
            return None
        # §3.6 的第四条发起前条件「P 仍在盘且身份一致」由 AC-16 修订 3（P-B-2
        # 裁定采纳 (a)）正式取名：不硬套 `verify_skipped` 那三个名字（会错标），
        # 另记 `verify_pairing_unavailable`，原因走自己的五值闭集。
        snapshot = self.ring.snapshot(record.frame_id)
        if snapshot is None:
            self._record_pairing_unavailable("snapshot_missing", record.frame_id)
            return None
        identity = verify_frame_identity(self.repository.frames_directory, snapshot)
        if identity is not None:
            self._record_pairing_unavailable(identity, record.frame_id)
            return None
        try:
            latest = self.repository.latest_frame_id()
        except (FileNotFoundError, KeyError, ValueError, OSError):
            self._record_pairing_unavailable("latest_unreadable", record.frame_id)
            return None
        if latest - record.frame_id > self.receipt.k_pub:
            self._record_skip("tracking_lag", record.frame_id)
            return None
        return record, QuerySnapshot(
            frame_id=snapshot.frame_id,
            image_sha256=snapshot.image_sha256,
            copy_path=snapshot.copy_path,
            capture_monotonic_s=snapshot.capture_monotonic_s,
            capture_unix_s=snapshot.capture_unix_s,
            snapshot=snapshot,
        )

    def _record_skip(self, reason: str, frame_id: int | None) -> None:
        """发起前跳过：**只**进会话 JSONL（AC-16 修订 2）。

        不产结果行、不占 `query_id`、不调模型、不计完成核验、不改连续告警或疑似。
        """
        self._journal(
            "verify_skipped",
            reason=bridge._require_member(
                reason, bridge.VERIFY_SKIP_REASONS, "verify_skipped.reason"
            ),
            frame_id=frame_id,
        )

    def _record_pairing_unavailable(self, reason: str, frame_id: int | None) -> None:
        """配对帧本身不可信任：同样是发起前跳过，只进会话 JSONL（AC-16 修订 3）。

        与 `verify_skipped` 分开记，是为了不把 AC-16 修订 2 定死的三个成员拿来
        错标别的情形；原因走 `PAIRING_UNAVAILABLE_REASONS` 五值闭集并带已知
        `P.frame_id`，不产结果行、不占 `query_id`、不调模型、不计完成核验。
        """
        self._journal(
            "verify_pairing_unavailable",
            reason=bridge._require_member(
                reason,
                bridge.PAIRING_UNAVAILABLE_REASONS,
                "verify_pairing_unavailable.reason",
            ),
            frame_id=frame_id,
        )

    def _handle_verify_outcome(self, outcome: QueryOutcome) -> None:
        job = outcome.job
        self.in_flight_verify_query_id = None
        if self._stale_epoch(job):
            # `dismiss`/`confirm_lost`/新段/`stop` 之后到达的旧回包一律丢弃，
            # 不得重新触发提醒（§3.6）。
            self._append_result_line(
                {
                    "query_id": job.query_id,
                    "status": "IGNORED_STALE_EPOCH",
                    "epoch": job.epoch,
                    "verify_epoch": job.verify_epoch,
                    "current_verify_epoch": self.verify_epoch,
                    "purpose": "verify",
                }
            )
            return
        verdict = "inconclusive"
        inconclusive_reason: str | None = None
        selection: Selection | None = None
        reject_reason: str | None = None
        if outcome.error is not None:
            status = outcome.error.status
            reject_reason = outcome.error.reason
            inconclusive_reason = "backend_error"
        else:
            # AC-16 修订 1：核验走**同一条**返回检查点（帧差 → 墙钟 → 身份），
            # 不另写一套缩水判据；`frames_late_exceeded` 与 `negative_frame_delta`
            # 因此都可达。
            returned = self._check_return(job)
            if returned is not None:
                status = "stale_rejected"
                reject_reason = returned
                inconclusive_reason = VERIFY_RETURN_INCONCLUSIVE[returned]
            else:
                selection = interpret(outcome.raw)
                status = selection.status
                if selection.status == "parse_failed":
                    inconclusive_reason = "parse_failed"
                elif selection.status == "ambiguous":
                    verdict = "ambiguous"
                elif selection.status == "none":
                    verdict = "none"
                else:
                    overlap = iou_norm_xywh(
                        job.tracker_box or (0.0, 0.0, 0.0, 0.0),
                        selection.candidates[0].bbox_xywh_norm,
                    )
                    verdict = "consistent" if overlap >= VERIFY_IOU else "drift"
        self.last_verified_frame_id = job.frame.frame_id
        self.last_verdict = verdict
        self.last_verify_query_id = job.query_id
        self._apply_verdict(verdict)
        if self.state == "TRACKING":
            # §3.6：每次核验结束 `next_due = 完成时刻 + T_v`。
            self.next_due_unix_s = float(self._unix()) + self.config.verify_interval_s
        self._emit_verify_result(
            job, outcome, verdict, inconclusive_reason, selection, status,
            reject_reason=reject_reason,
        )
        if outcome.error is not None and outcome.error.reason == "worker_stuck":
            self._handle_backend_fatal(outcome.error)
            return
        if self.state == "TRACKING" and verdict == "ambiguous":
            self._raise_suspect("ambiguous", "verify_ambiguous")
        elif self.state == "TRACKING" and self.consecutive_alert >= CONSECUTIVE_ALERT:
            kind = self.alert_kind or "lost"
            self._raise_suspect(
                kind, "verify_none" if kind == "lost" else "verify_drift"
            )

    def _apply_verdict(self, verdict: str) -> None:
        if verdict == "consistent":
            self.consecutive_alert = 0
            self.alert_kind = None
        elif verdict == "none":
            self.consecutive_alert += 1
            self.alert_kind = "lost"
        elif verdict == "drift":
            self.consecutive_alert += 1
            self.alert_kind = "drift"
        elif verdict == "ambiguous":
            self.consecutive_alert = 0
        # `inconclusive` 不改计数。

    def _raise_suspect(self, kind: str, reason: str) -> None:
        self._suspect_sequence += 1
        self.suspect_kind = kind
        self.suspect_id = f"{self.session_id}-s{self._suspect_sequence}"
        self.suspect_reason = reason
        self._journal(
            "suspect_raised",
            suspect_kind=kind,
            reason=reason,
            suspect_id=self.suspect_id,
        )
        self._enter("SUSPECTED", reason=None)

    def _emit_verify_result(
        self,
        job: QueryJob,
        outcome: QueryOutcome,
        verdict: str,
        inconclusive_reason: str | None,
        selection: Selection | None,
        status: str,
        *,
        reject_reason: str | None = None,
    ) -> None:
        overlap = None
        if selection is not None and selection.status == "unique" and job.tracker_box:
            overlap = iou_norm_xywh(job.tracker_box, selection.candidates[0].bbox_xywh_norm)
        preview = self._preview(
            job, selection.candidates if selection is not None else (), job.tracker_box
        )
        self._emit_result(
            purpose="verify",
            status=status,
            reject_reason=reject_reason,
            frame=job.frame,
            job=job,
            selection=selection,
            latency_ms=outcome.latency_ms,
            preview_path=preview,
            verify={
                "paired_frame_id": job.frame.frame_id,
                "tracker_box_at_frame": list(job.tracker_box) if job.tracker_box else None,
                "iou": overlap,
                "verdict": verdict,
                "inconclusive_reason": inconclusive_reason,
                "consecutive_alert": self.consecutive_alert,
                "alert_kind": self.alert_kind,
            },
        )

    # --- 结果与状态发布 ---------------------------------------------------

    def _preview(
        self,
        job: QueryJob,
        candidates: Sequence[Candidate],
        tracker_box: Sequence[float] | None,
    ) -> str | None:
        if not candidates and tracker_box is None:
            return None
        renderer = self.config.preview or render_preview
        destination = self.previews_dir / f"{job.frame.frame_id}-{job.query_id}.png"
        try:
            path = renderer(job.frame.copy_path, destination, candidates, tracker_box)
        except Exception as exception:
            # 渲染失败一律 fail-closed 记同一个合同点名的诊断；AC-5 修订 1 的确认门
            # 只看「有没有预览」，所以缺依赖与渲染异常走同一条出口。
            self._journal(
                "preview_unavailable",
                query_id=job.query_id,
                source=(
                    "missing_dependency"
                    if isinstance(exception, PreviewUnavailable)
                    else "render_failed"
                ),
                detail=f"{type(exception).__name__}: {exception}",
            )
            return None
        return str(path)

    def _emit_result(
        self,
        *,
        purpose: str,
        status: str,
        frame: QuerySnapshot | None,
        reject_reason: str | None = None,
        job: QueryJob | None = None,
        selection: Selection | None = None,
        latency_ms: float | None = None,
        preview_path: str | None = None,
        request_id: str | None = None,
        last_status: str | None = None,
        last_reject_reason: str | None = None,
        verify: Mapping[str, Any] | None = None,
        query_id: str | None = None,
        query_unix_s: float | None = None,
    ) -> str:
        self._result_sequence += 1
        result_id = f"{self.session_id}-res{self._result_sequence}"
        if job is not None:
            query_id = job.query_id
        elif query_id is None:
            # AC-6 修订 1：取帧前就失败的尝试没有 job，仍分配唯一 `query_id` 并计一次
            # 尝试；真实模型调用数另由 `worker.calls_started` 计，两者分列。
            self._query_sequence += 1
            query_id = f"{self.session_id}-q{self._query_sequence}"
        identity = dict(getattr(self.config.adapter, "identity", {}) or {})
        model = None
        if identity:
            model = {
                "backend": identity.get("backend", self.receipt.backend),
                "model_form": identity.get("model_form", self.receipt.model_form),
                "base_repo_revision": identity.get("base_repo_revision"),
                "weights_sha256": identity.get("weights_sha256"),
                "prompt_template_sha256": identity.get("prompt_template_sha256"),
                "vocab_sha256": identity.get("vocab_sha256"),
                "g4_segment_sha256": identity.get("g4_segment_sha256"),
                "device": identity.get("device"),
                "finish_reason": (
                    selection.raw.finish_reason if selection is not None else None
                ),
                "gen_tokens": selection.raw.gen_tokens if selection is not None else None,
                "replay_blind_sha256": identity.get("replay_blind_sha256"),
                "replay_predictions_sha256": identity.get("replay_predictions_sha256"),
            }
            # A2(d)：六个 llama 身份键只在身份块携带时写入（全有或全无；旧后端结果字节形态不变）。
            for key in bridge.LLAMA_IDENTITY_KEYS:
                if identity.get(key) is not None:
                    model[key] = identity.get(key)
        frames_late = None
        if frame is not None and job is not None:
            try:
                frames_late = self.repository.latest_frame_id() - frame.frame_id
            except (FileNotFoundError, KeyError, ValueError, OSError):
                frames_late = None
        payload = bridge.result_payload(
            query_id=query_id,
            result_id=result_id,
            request_id=request_id,
            epoch=self.epoch,
            segment_index=self.segment_index if self.track_id else None,
            attempt=self.attempt if purpose == "designate" else 1,
            attempt_limit=self.config.attempt_limit,
            purpose=purpose,
            status=status,
            frame_id=frame.frame_id if frame else None,
            frame_sha256=frame.image_sha256 if frame else None,
            capture_monotonic_s=frame.capture_monotonic_s if frame else None,
            capture_unix_s=frame.capture_unix_s if frame else None,
            query_unix_s=(
                job.query_unix_s
                if job
                else (query_unix_s if query_unix_s is not None else float(self._unix()))
            ),
            reject_reason=reject_reason,
            last_status=last_status,
            last_reject_reason=last_reject_reason,
            candidates=[candidate.payload() for candidate in (selection.candidates if selection else ())]
            if status in {"unique", "ambiguous"}
            else [],
            verify=verify,
            model=model,
            latency_ms=latency_ms,
            frames_late=frames_late,
            k_ret=self.receipt.k_ret,
            wall_elapsed_s=(
                float(self._monotonic()) - job.submitted_monotonic_s if job else None
            ),
            preview_path=preview_path,
            raw_output=selection.raw.raw_output if selection is not None else None,
            parse_error=selection.parse_error if selection is not None else None,
            expires_after_s=self.config.expires_after_s,
        )
        bridge.write_result(self.runtime, payload)
        self._append_result_line(payload["result"])
        return result_id

    def _append_result_line(self, record: Mapping[str, Any]) -> None:
        with self.results_path.open("a", encoding="utf-8") as handle:
            json.dump(dict(record), handle, sort_keys=True, allow_nan=False)
            handle.write("\n")

    def _enter(self, state: str, *, reason: str | None) -> None:
        if state not in bridge.SESSION_STATES:  # pragma: no cover - 闭集保证
            raise LanguageBridgeError(f"unknown session state {state!r}")
        self.state = state
        self.reason = reason
        self.since_unix_s = float(self._unix())
        if state not in {"SUSPECTED"}:
            self.suspect_kind = None if state != "SUSPECTED" else self.suspect_kind
        if state in {"IDLE", "LOST", "REINIT_REQUIRED", "TERMINAL"}:
            self.suspect_kind = None
            self.suspect_id = None
            if state != "LOST":
                self.suspect_reason = None
        self._journal("state", state=state, reason=reason)
        self._publish_state(force=True)

    def _publish_state(self, *, force: bool = False) -> None:
        document = bridge.tracker_state_payload(
            session_id=self.session_id,
            state=self.state,
            sequence=self.sequence,
            epoch=self.epoch,
            publishing=bool(self.publisher and self.publisher.publishing)
            and (not self.resident or (self.track_id is not None and self.state in bridge.PUBLISHING_STATES)),
            suspect_kind=self.suspect_kind if self.state == "SUSPECTED" else None,
            suspect_id=self.suspect_id if self.state == "SUSPECTED" else None,
            tracker_raw_state=self._tracker_raw_state(),
            reason=self.reason,
            track_id=self.track_id,
            segment_index=self.segment_index if self.track_id else None,
            since_frame_id=self.since_frame_id,
            since_unix_s=self.since_unix_s,
            last_published_frame_id=(
                self.publisher.last_published_frame_id if self.publisher else None
            ),
            last_progress_unix_s=self.last_progress_unix_s,
            retired_track_ids=self.retired_track_ids,
            verification={
                "paired_frame_id": self.last_verified_frame_id,
                "last_verdict": self.last_verdict,
                "last_query_id": self.last_verify_query_id,
                "consecutive_alert": self.consecutive_alert,
                "alert_kind": self.alert_kind,
                "next_due_unix_s": self.next_due_unix_s,
                "in_flight_query_id": self.in_flight_verify_query_id,
                "verify_epoch": self.verify_epoch,
            },
            last_request=self.last_request,
            pending_request=self.pending_request,
            expires_after_s=self.config.expires_after_s,
            designation=self.designation if self.resident else None,
        )
        comparable = json.dumps(document["tracker_state"], sort_keys=True)
        if not force and comparable == json.dumps(
            (self._last_state_document or {}).get("tracker_state", {}), sort_keys=True
        ):
            return
        bridge.write_tracker_state(self.runtime, document)
        self._last_state_document = document

    def _tracker_raw_state(self) -> str | None:
        if self.loop is None:
            return None
        return "TRACKING" if self.loop.state == "TRACKING" else "LOST"

    def _journal(self, kind: str, **fields: Any) -> None:
        if kind not in JOURNAL_KINDS:
            # A3（AC-4）：事件名闭集；闭集外名字是程序错误，不静默落盘。
            raise LanguageBridgeError(f"session journal kind {kind!r} is outside JOURNAL_KINDS")
        record = {
            "at_unix_s": float(self._unix()),
            "at_monotonic_s": float(self._monotonic()),
            "session_id": self.session_id,
            "kind": kind,
            "state": self.state,
            "epoch": self.epoch,
            "sequence": self.sequence,
            **fields,
        }
        with self.journal_path.open("a", encoding="utf-8") as handle:
            json.dump(record, handle, sort_keys=True, allow_nan=False, default=str)
            handle.write("\n")

    # --- 终止 -------------------------------------------------------------

    def _handle_backend_fatal(self, error: SelectorError) -> None:
        """`worker_stuck`：段 finalize → `REINIT_REQUIRED(backend_fatal)`，须 `stop` 重启。

        P1-ENG-LOOP-002 A5：常驻会话 `backend_fatal` → `TERMINAL(backend_fatal)`（VLM 不可用即结束本次，
        不重建常驻载体，STOP `S-BACKEND`）。段式路径不变。"""
        self._journal("backend_fatal", reason=error.reason, detail=error.detail)
        if self.resident:
            if self.state != "TERMINAL":
                self.stop("backend_fatal")
            return
        if self.loop is not None:
            self._finalize_segment("backend_fatal")
        self._enter("REINIT_REQUIRED", reason="backend_fatal")

    def stop(self, reason: str = "operator_stop", *, request_id: str | None = None) -> None:
        self.epoch += 1
        # A4：挂起中的呈现随纪元改变丢弃，不补写结果行。
        self._discard_pending_presentation("epoch_changed")
        if self.capture and self.target_manager is not None:
            # #7 / AC-11：STOP 与授权、命令写出在同一单写者内串行——先置停止（在途效果作废），再写显式 hold。
            # FASTFIX §3.3：重捕提示在途时同时作废（原因 = 本次 stop 的原因，如 `rebuild_limit`）。
            self.target_manager.request_stop(request_id=request_id, cause=reason)
            self.target_manager.take_reacquire_result()
            self._capture_hold("operator_stop")
        if self.loop is not None:
            self._finalize_segment(reason)
        abandoned = self.worker.stop() if self.worker is not None else None
        if abandoned is not None:
            # 被放弃的那次 predict_one 已经真的跑过，按 AC-6 修订 1 仍计信封。
            self._journal(
                "worker_abandoned",
                detail=abandoned,
                query_ids=list(self.worker.abandoned),
                model_calls_started=self.worker.calls_started,
            )
        self._enter("TERMINAL", reason=reason)
        self.close()


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def designate_options(envelope: Any) -> tuple[float | None, str | None, str | None]:
    """A4：从请求体取逐次 `delay_s` 与 `intent`（两者只随 `ask`/`respecify` 出现）。

    返回 `(Δ, intent, invalid_reason)`：Δ 缺省 0.0、须为有限数且 ∈ [0, 8]；`intent` 缺省 None、须为非空
    字符串。不合即 `invalid_reason`（会话回执 `REQUEST_INVALID`）。`intent` 只用于回执日志，不进查询、
    不进 prompt、不影响任何决策（AC-5/AC-9）。
    """
    raw = getattr(envelope, "raw", None)
    body = raw.get("request") if isinstance(raw, Mapping) else None
    body = body if isinstance(body, Mapping) else {}
    delay = body.get("delay_s")
    intent = body.get("intent")
    invalid: str | None = None
    delay_s: float | None
    if delay is None:
        delay_s = 0.0
    elif isinstance(delay, bool) or not isinstance(delay, (int, float)) or not math.isfinite(float(delay)):
        delay_s, invalid = None, "invalid_delay"
    else:
        delay_s = float(delay)
        if not DELAY_MIN_S <= delay_s <= DELAY_MAX_S:
            invalid = "delay_out_of_range"
    if intent is not None and (not isinstance(intent, str) or not intent.strip()):
        intent, invalid = None, invalid or "invalid_intent"
    return delay_s, intent, invalid


def _touches_border(box: Sequence[float], margin: float = 0.01) -> bool:
    x, y, width, height = (float(value) for value in box)
    return x < margin or y < margin or x + width > 1.0 - margin or y + height > 1.0 - margin


# --- 夹具帧发布器（§3.8 `replay-demo` 与测试共用） ------------------------


class FixtureFramePublisher:
    """把已有 JPEG 按 `tethered-sensor-frame/v3` 发布成帧包（两成员 + 原子指针）。

    只写调用方给的目录；阶段 A 的可运行示例和无 GPU 测试都用它，不需要 Unity。
    """

    def __init__(
        self,
        runtime: Path,
        *,
        capture_hz: float = 5.0,
        unix: Callable[[], float] = time.time,
        width: int = 640,
        height: int = 480,
        vertical_fov_deg: float = 60.0,
        scenario_id: str = "deterministic-loop-default",
        camera_position_world_m: Sequence[float] = (132.0, 25.2, 117.0),
    ):
        self.runtime = Path(runtime)
        self.frames = self.runtime / "frames"
        self.frames.mkdir(parents=True, exist_ok=True)
        self.capture_hz = float(capture_hz)
        self._unix = unix
        self.width = width
        self.height = height
        self.vertical_fov_deg = vertical_fov_deg
        self.scenario_id = scenario_id
        self.camera_position_world_m = tuple(camera_position_world_m)
        # 相机姿态（缺省正下方）；测试可改成一组正交基来模拟云台接近限位。
        self.camera_forward_world: tuple[float, float, float] = (0.0, -1.0, 0.0)
        self.camera_right_world: tuple[float, float, float] = (1.0, 0.0, 0.0)
        self.camera_up_world: tuple[float, float, float] = (0.0, 0.0, 1.0)
        #: 与缺省正下方基一致的四元数；常驻测试可改它模拟云台转动（P1-ENG-ACQ-001 §3.7 到位判据）。
        self.camera_rotation_xyzw: tuple[float, float, float, float] = (0.7071068286895752, 0.0, 0.0, 0.7071068286895752)
        self.next_frame_id = 0
        self.capture_monotonic_s = 1.0

    def publish(self, image_bytes: bytes, *, frame_id: int | None = None) -> int:
        identifier = self.next_frame_id if frame_id is None else int(frame_id)
        self.next_frame_id = identifier + 1
        stem = f"frame_{identifier:010d}"
        (self.frames / f"{stem}.jpg").write_bytes(image_bytes)
        metadata = {
            # 与 Unity `SensorFrameWriter` 的 v3 帧包同字段（真实样本：
            # `runtime/frames.1b-diagnostic-hold/frame_0000000012.json`）。
            "schema_version": "tethered-sensor-frame/v3",
            "frame_id": identifier,
            "scenario_id": self.scenario_id,
            "capture_unix_s": float(self._unix()),
            "capture_monotonic_s": self.capture_monotonic_s,
            "capture_monotonic_clock_id": "system-stopwatch/v1",
            "simulation_time_s": self.capture_monotonic_s,
            "width": self.width,
            "height": self.height,
            "vertical_fov_deg": self.vertical_fov_deg,
            "horizontal_fov_deg": 75.17817687988281,
            "intrinsics_px": {
                "cx": self.width / 2.0,
                "cy": self.height / 2.0,
                "fx": 415.69219970703125,
                "fy": 415.69219970703125,
            },
            "camera_position_world_m": list(self.camera_position_world_m),
            "camera_forward_world": list(self.camera_forward_world),
            "camera_right_world": list(self.camera_right_world),
            "camera_up_world": list(self.camera_up_world),
            "camera_rotation_xyzw": list(self.camera_rotation_xyzw),
            "gimbal_saturated": False,
            "tether_saturated": False,
        }
        self.capture_monotonic_s += 1.0 / self.capture_hz
        (self.frames / f"{stem}.json").write_text(
            json.dumps(metadata, sort_keys=True), encoding="utf-8"
        )
        self.publish_pointer(identifier)
        return identifier

    def publish_pointer(self, frame_id: int) -> None:
        stem = f"frame_{frame_id:010d}"
        pointer = {
            "schema_version": "tethered-frame-manifest/v1",
            "frame_id": int(frame_id),
            "image_file": f"{stem}.jpg",
            "metadata_file": f"{stem}.json",
        }
        temporary = self.frames / "latest.json.tmp"
        temporary.write_text(json.dumps(pointer, sort_keys=True), encoding="utf-8")
        temporary.replace(self.frames / "latest.json")


#: AC-21：`candidates` 后端的身份 = K 收据 `model_identity` 必须逐字等于的三字段（无权重、无设备）。
CANDIDATES_IDENTITY: dict[str, str] = {
    "backend": bridge.CANDIDATES_BACKEND,
    "model_form": bridge.CANDIDATES_MODEL_FORM,
    "source": "det-assoc-v1 resident history",
}
#: AC-21 单宿主报告：两组（`none` / 8 个 `tracked`）各至少这么多次 `predict_one` 墙钟样本。
CANDIDATES_MIN_SAMPLES = 100
#: `candidates` 后端只配常驻指针式快层（CLARIFY：与 `--tracker det-assoc-v1 --resident` 配套）。
CANDIDATES_TRACKER = "det-assoc-v1"


def nearest_rank_p95(samples: Sequence[float]) -> float:
    """最近秩 p95：升序第 ceil(0.95·n) 个样本（AC-21 单宿主预检报告与校验共用）。"""
    ordered = sorted(float(value) for value in samples)
    if not ordered:
        raise ValueError("p95 needs at least one sample")
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def machine_name() -> str:
    """本机机器名（AC-21：单宿主报告记录它，会话启动时逐字比对）。"""
    return platform.node()


class CandidatesBackend:
    """P1-ENG-ACQ-001 §3.10 S2-d：候选来源 = 查询帧 N 上常驻关联器的 `tracked` 轨迹（不经 VLM、零模型调用）。

    输出与 VLM 同一文本契约（`tools/eng_sft/parse.py` 表 B：`none` / `unique` / `ambiguous` 2…8 个候选，
    0–1000 整数 `bbox_2d`），因此下游 `interpret` → 预览 → `confirm` → `designate(box, N)` 与 VLM 路径完全相同。
    候选只来自快层检测 track，**不得用真值投影**。帧号取自会话帧环副本的文件名（`frame_<id>.jpg`）。
    """

    MAX_CANDIDATES = 8

    def __init__(self) -> None:
        self.identity = dict(CANDIDATES_IDENTITY)
        self._history: Callable[[int], Any] | None = None
        self.calls = 0

    def bind_history(self, history: Callable[[int], Any]) -> None:
        self._history = history

    def predict_one(self, query_id: str, image_path: Path, surface: str, g4: Any) -> RawSelection:
        self.calls += 1
        frame_id = int(Path(image_path).stem.split("_")[1])
        entry = self._history(frame_id) if self._history is not None else None
        rows = [] if entry is None else sorted(entry.rows(ROW_TRACKED), key=lambda r: (-(r.box_norm[2] * r.box_norm[3]), r.track_id))
        boxes = []
        for row in rows[: self.MAX_CANDIDATES]:
            x, y, w, h = row.box_norm
            box = [int(round(x * 1000)), int(round(y * 1000)), int(round((x + w) * 1000)), int(round((y + h) * 1000))]
            box = [min(1000, max(0, v)) for v in box]
            if box[0] < box[2] and box[1] < box[3]:
                boxes.append(box)
        if not boxes:
            text = json.dumps({"status": "none"})
        elif len(boxes) == 1:
            text = json.dumps({"status": "unique", "bbox_2d": boxes[0]})
        else:
            text = json.dumps({"status": "ambiguous", "candidates": [{"bbox_2d": b} for b in boxes]})
        return RawSelection(raw_output=text, finish_reason="stop", gen_tokens=None, latency_ms=0.0, prompt_sha256=None, model_id="candidates")


# --- CLI（§3.8） -----------------------------------------------------------


def send_request(
    runtime: Path,
    *,
    session_id: str,
    action: str,
    instruction: Instruction | None = None,
    candidate_index: int | None = None,
    token: str | None = None,
    request_id: str | None = None,
    wait_s: float = RECEIPT_WAIT_S,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    delay_s: float | None = None,
    intent: str | None = None,
    click: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """写一条请求并等回执；并发 CLI 拿不到写者锁即 `WRITER_BUSY` 且不写。

    P1-ENG-CAPTURE-001 C7：`click` 动作随附点击字段（x_px、y_px、frame_id、image_sha256，可选 page）；
    点击页进程内直接调本函数（不起 CLI 子进程），退出码语义由调用方按 CLI 同一口径映射。

    接管了死写者锁（上一个 CLI 建锁后被杀）时，被清理的持有者当场打到 stderr，
    并随返回字典的 `replaced_writer_lock` 交给调用方（AC-1 修订 1「并记日志」）。
    """
    identifier = request_id or f"{session_id}-req-{uuid.uuid4().hex[:8]}"
    replaced: dict[str, Any] = {}

    def report_cleared(dead: bridge.LockHolder) -> None:
        replaced.update(
            pid=dead.pid, request_id=dead.request_id, created_unix_s=dead.created_unix_s
        )
        print(
            "已清理死写者锁："
            f"pid={dead.pid} request_id={dead.request_id} "
            f"created_unix_s={dead.created_unix_s}",
            file=sys.stderr,
        )

    if (delay_s is not None or intent is not None) and action not in {"ask", "respecify"}:
        raise LanguageBridgeError("--delay-s/--intent only apply to ask and respecify")
    if (action == "click") != (click is not None):
        raise LanguageBridgeError("the click action needs click fields (and only click takes them)")
    if click is not None:
        bridge.validate_click_fields(click)
    holder = bridge.acquire_writer_lock(
        runtime, request_id=identifier, on_dead_lock_cleared=report_cleared
    )
    extra = {"replaced_writer_lock": dict(replaced)} if replaced else {}
    try:
        if click is not None:
            payload = bridge.request_payload(
                session_id=session_id, request_id=identifier, action=action, token=token, click=click
            )
            atomic_write(bridge.REQUEST_FILE, payload, runtime)
        elif delay_s is None and intent is None:
            bridge.write_request(
                runtime,
                session_id=session_id,
                request_id=identifier,
                action=action,
                instruction=instruction,
                candidate_index=candidate_index,
                token=token,
            )
        else:
            # A4：逐次 Δ 与意图标签随请求体传给会话（`language_request/v1` 的可选字段；旧读者忽略未知键）。
            payload = bridge.request_payload(
                session_id=session_id,
                request_id=identifier,
                action=action,
                instruction=instruction,
                candidate_index=candidate_index,
                token=token,
            )
            if delay_s is not None:
                payload["request"]["delay_s"] = float(delay_s)
            if intent is not None:
                payload["request"]["intent"] = str(intent)
            atomic_write(bridge.REQUEST_FILE, payload, runtime)
        deadline = monotonic() + wait_s
        while monotonic() < deadline:
            try:
                document = bridge.read_tracker_state(runtime)
            except LanguageBridgeError:
                document = None
            receipt = (
                (document or {}).get("tracker_state", {}).get("last_request")
                if document
                else None
            )
            if receipt and receipt.get("request_id") == identifier:
                return {"request_id": identifier, "receipt": receipt, **extra}
            sleep(POLL_INTERVAL_S)
        # AC-1 修订 1：超时只释放锁并报「结果未知」，不换新 id 重发。
        return {
            "request_id": identifier,
            "receipt": None,
            "note": "结果未知，可能稍后执行；重试请用同一个 --request-id",
            **extra,
        }
    finally:
        bridge.release_writer_lock(runtime, request_id=identifier, pid=holder.pid)


def _validate_candidates_source(receipt: KReceipt, current_machine: str) -> dict[str, Any]:
    """AC-21（B2）：`candidates` 只认 Unity 主机本地生成的一份 `mac` 适配器预检报告。

    不要 5060 报告、不跑双宿主决策、不接受 VLM 权重身份；报告字节 SHA、机器名、宿主、
    后端/形态/身份、`p95_s`/`hz`/`retained_frame_count` 与收据逐项相等，两组样本各
    ≥ `CANDIDATES_MIN_SAMPLES` 且 p95 可由原始样本复算，资格式成立。
    """
    if receipt.host != "mac":
        raise ValueError("candidates receipts are single-host: host must be 'mac'")
    if dict(receipt.model_identity) != CANDIDATES_IDENTITY:
        raise ValueError("candidates receipt model_identity must equal the adapter identity exactly")
    if set(receipt.source_reports) != {"mac"}:
        raise ValueError("candidates receipts take exactly one 'mac' source report")
    reference = receipt.source_reports["mac"]
    path = Path(reference["path"])
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if sha256_file(path) != reference["sha256"]:
        raise ValueError("source report SHA changed: mac")
    report = json.loads(path.read_text(encoding="utf-8"))
    if report["host"] != "mac" or report["verdict"] != "OK":
        raise ValueError("incomplete/wrong host report: mac")
    if report["machine_name"] != current_machine:
        raise ValueError(
            f"report machine {report['machine_name']!r} differs from this machine {current_machine!r}"
        )
    for key in ("backend", "model_form", "model_identity", "hz", "retained_frame_count", "p95_s"):
        if report[key] != getattr(receipt, key):
            raise ValueError(f"receipt binding differs from the measured report: {key}")
    p95_s = float(report["p95_s"])
    if not math.isfinite(p95_s) or p95_s < 0:
        raise ValueError("report p95_s must be finite and non-negative")
    groups = report["groups"]
    if set(groups) != {"none", "tracked"}:
        raise ValueError("report must carry the 'none' and 'tracked' sample groups")
    group_p95 = []
    for name, group in groups.items():
        samples = [float(value) for value in group["samples_s"]]
        if len(samples) < CANDIDATES_MIN_SAMPLES or len(samples) != group["sample_count"]:
            raise ValueError(f"report group {name} has too few samples")
        if not all(math.isfinite(value) and value >= 0 for value in samples):
            raise ValueError(f"report group {name} has invalid samples")
        if nearest_rank_p95(samples) != group["p95_s"]:
            raise ValueError(f"report group {name} p95 does not match its samples")
        group_p95.append(float(group["p95_s"]))
    if p95_s != max(group_p95):
        raise ValueError("report p95_s must be the larger group p95")
    if not qualifies(p95_s, receipt.hz, receipt.retained_frame_count):
        raise ValueError("candidates receipt does not qualify (K_ret + K_conf + K_pub > R - 8)")
    return report


_HEX64_CHARS = frozenset("0123456789abcdef")


def _is_hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= _HEX64_CHARS


def _validate_jetson_source(receipt: KReceipt) -> dict[str, Any]:
    """P1-ENG-LOOP-002 §3.2：jetson 单宿主收据只认它自己那一份报告（按字节 sha 绑定）。

    报告须为 `host == "jetson"`、`verdict == "OK"`、`backend == "http"`、`model_form == "c2-merged"`，带
    `transport.endpoint`、`environment.git_head` 与 `environment.dirty == false`、`serve_code_sha256`、`machine`，
    `model_identity` 六键齐全且合法；收据的绑定项与报告逐项相等，资格式成立。`mac`/`5060` 两宿主规则不经此处。
    """
    if receipt.backend != "http" or receipt.model_form != "c2-merged":
        raise ValueError("jetson receipts bind backend 'http' with model_form 'c2-merged'")
    if set(receipt.source_reports) != {JETSON_HOST}:
        raise ValueError("jetson receipts take exactly one 'jetson' source report")
    reference = receipt.source_reports[JETSON_HOST]
    path = Path(reference["path"])
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if sha256_file(path) != reference["sha256"]:
        raise ValueError("source report SHA changed: jetson")
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("host") != JETSON_HOST or report.get("verdict") != "OK":
        raise ValueError("incomplete/wrong host report: jetson")
    for key in ("backend", "model_form", "model_identity", "hz", "retained_frame_count", "p95_s"):
        if report[key] != getattr(receipt, key):
            raise ValueError(f"receipt binding differs from the measured report: {key}")
    endpoint = (report.get("transport") or {}).get("endpoint")
    if not isinstance(endpoint, str) or not endpoint:
        raise ValueError("jetson report lacks transport.endpoint")
    environment = report.get("environment") or {}
    if not isinstance(environment.get("git_head"), str) or not environment.get("git_head"):
        raise ValueError("jetson report lacks environment.git_head")
    if environment.get("dirty") is not False:
        raise ValueError("jetson report was measured from a dirty working tree")
    if not _is_hex64(report.get("serve_code_sha256")):
        raise ValueError("jetson report lacks a hex64 serve_code_sha256")
    if not isinstance(report.get("machine"), str) or not report.get("machine"):
        raise ValueError("jetson report lacks the board machine name")
    try:
        llama = bridge.validate_llama_identity(dict(receipt.model_identity))
    except LanguageBridgeError as exc:
        raise ValueError(f"jetson model identity invalid: {exc}") from exc
    if not llama:
        raise ValueError("jetson model identity must carry the six llama keys")
    if not qualifies(receipt.p95_s, receipt.hz, receipt.retained_frame_count):
        raise ValueError("jetson receipt does not qualify (K_ret + K_conf + K_pub > R - 8)")
    return report


def code_git_state(code_root: Path) -> tuple[str | None, bool]:
    """§3.2：`(HEAD, dirty)`；dirty = 整个工作树 `git status --porcelain` 非空（IR-6 不接受缩窄：
    tests/、文档等任何已跟踪改动或未跟踪文件都算脏；只有 `.gitignore` 忽略的 `runtime/`/`outputs/`
    本来不进该输出）。git 不可用 → `(None, True)`。"""
    import subprocess  # noqa: PLC0415

    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=code_root, capture_output=True, text=True, check=True
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            cwd=code_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None, True
    return (head or None), bool(status)


def validate_jetson_session(
    receipt: KReceipt,
    report: Mapping[str, Any],
    adapter: Any,
    *,
    runtime: Path,
    scenario_config_path: Path | None,
    code_root: Path,
    git_state: Callable[[], tuple[str | None, bool]] | None = None,
) -> dict[str, Any]:
    """§3.2 会话启动校验（仅 jetson 路径新增）：任一不符 → `ConfigMismatch`，会话不建任何目录。

    已由 `validate_measurement_sources` 与 `bind_identity` 核过：报告 host/sha/`transport`、六键与
    `/status` 身份逐键相等。此处另核：`scenario_id` = 生效场景；`environment.git_head` = 会话进程 HEAD 且
    会话代码路径干净；`/status.machine` = 报告 `machine`；`/status.serve_code_sha256` == 报告值 == 会话对
    本工作树按 A2(a) 同一定义重算的部署摘要；`response_format`/`decode`/`prompt` 身份 == 桌面重算。
    """
    from tools.eng_loop2 import deploy_digest  # noqa: PLC0415 — AC-9 闭集第 5 项（纯标准库）

    from .language_selector import _prompt_identity  # noqa: PLC0415

    try:
        scenario = read_scenario(Path(runtime), scenario_config_path)
        if receipt.scenario_id != scenario.get("scenario_id"):
            raise ValueError(
                f"receipt scenario_id {receipt.scenario_id!r} differs from the effective scenario {scenario.get('scenario_id')!r}"
            )
        head, dirty = git_state() if git_state is not None else code_git_state(code_root)
        expected_head = (report.get("environment") or {}).get("git_head")
        if head is None or head != expected_head:
            raise ValueError(f"session HEAD {head!r} differs from the measured git_head {expected_head!r}")
        if dirty:
            raise ValueError("session working tree is dirty (git status --porcelain non-empty)")
        status_document = adapter.status_document()
        if status_document.get("machine") != report.get("machine"):
            raise ValueError(
                f"/status machine {status_document.get('machine')!r} differs from the report {report.get('machine')!r}"
            )
        digests = deploy_digest.desktop_identity_digests(code_root)
        served = status_document.get("serve_code_sha256")
        if not (served == report.get("serve_code_sha256") == digests["serve_code_sha256"]):
            raise ValueError("serve_code_sha256 differs between /status, the report and the local recomputation")
        identity = dict(receipt.model_identity)
        for key in ("response_format_sha256", "decode_config_sha256"):
            if identity.get(key) != digests[key]:
                raise ValueError(f"{key} differs from the local recomputation")
        if identity.get("prompt_template_sha256") != _prompt_identity(False)["prompt_template_sha256"]:
            raise ValueError("prompt_template_sha256 differs from the local recomputation")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, SelectorError, LanguageBridgeError) as exc:
        raise ConfigMismatch(f"CONFIG_MISMATCH: jetson session binding refused: {exc}") from exc
    return {
        "git_head": head,
        "machine": status_document.get("machine"),
        "serve_code_sha256": served,
        "scenario_id": scenario.get("scenario_id"),
    }


def validate_measurement_sources(
    receipt: KReceipt, *, current_machine: str | None = None
) -> dict[str, Any] | None:
    """A real backend may only reuse the two reports whose bytes issued this K."""
    if receipt.backend == "replay":
        return None
    if receipt.host == JETSON_HOST:
        try:
            return _validate_jetson_source(receipt)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise ConfigMismatch(f"CONFIG_MISMATCH: invalid K measurement binding: {exc}") from exc
    if receipt.backend == bridge.CANDIDATES_BACKEND:
        try:
            return _validate_candidates_source(
                receipt, machine_name() if current_machine is None else current_machine
            )
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise ConfigMismatch(f"CONFIG_MISMATCH: invalid K measurement binding: {exc}") from exc
    try:
        if set(receipt.source_reports) != {"mac", "5060"}:
            raise ValueError("both source reports are required")
        reports = {}
        for host, reference in receipt.source_reports.items():
            path = Path(reference["path"])
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            if sha256_file(path) != reference["sha256"]:
                raise ValueError(f"source report SHA changed: {host}")
            report = json.loads(path.read_text(encoding="utf-8"))
            if report["host"] != host or report["verdict"] not in {"OK", "FAIL"}:
                raise ValueError(f"incomplete/wrong host report: {host}")
            tier = (host_tier(report["p95_s"], report["hz"], report["retained_frame_count"])
                    if report["verdict"] == "OK" else "FAIL")
            if report["tier"] != tier:
                raise ValueError(f"report tier is inconsistent: {host}")
            reports[host] = report
        choice, _ = decide_host(reports["mac"]["tier"], reports["mac"].get("p95_s"),
                                reports["5060"]["tier"], reports["5060"].get("p95_s"))
        if receipt.host != choice or choice == "HOST_UNDECIDED":
            raise ValueError("receipt host differs from the two-host decision")
        selected = reports[choice]
        for key in ("backend", "model_form", "model_identity", "hz", "retained_frame_count", "p95_s"):
            if selected[key] != getattr(receipt, key):
                raise ValueError(f"receipt binding differs from the measured report: {key}")
        expected_backend, expected_device = ("local-hf", "mps") if choice == "mac" else ("http", "cuda")
        if receipt.backend != expected_backend or receipt.model_identity.get("device") != expected_device:
            raise ValueError("host/backend/device binding is inconsistent")
        if not receipt.model_identity.get("weights_sha256"):
            raise ValueError("missing measured weights identity")
        return selected
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ConfigMismatch(f"CONFIG_MISMATCH: invalid K measurement binding: {exc}") from exc


def _build_adapter(arguments: argparse.Namespace) -> Any:
    from .language_selector import HttpAdapter, ReplayAdapter, load_local_adapter

    if arguments.backend == bridge.CANDIDATES_BACKEND:
        # AC-21（B1）：零模型、零检测；候选由会话在常驻载体建立后 `bind_history` 接到查询帧 N 的历史。
        return CandidatesBackend()
    if arguments.backend == "replay":
        return ReplayAdapter(
            arguments.replay_blind,
            arguments.replay_predictions,
            expected_blind_sha256=arguments.replay_blind_sha256,
            expected_predictions_sha256=arguments.replay_predictions_sha256,
            model_form=arguments.model_form,
        )
    if arguments.backend == "http":
        receipt = KReceipt.from_document(
            json.loads(Path(arguments.k_receipt).read_text(encoding="utf-8"))
        )
        adapter = HttpAdapter(
            arguments.server_url,
            t_ret_s=receipt.t_ret_s,
            t_hard_s=T_HARD_S,
            model_form=arguments.model_form,
            weights_sha256=receipt.model_identity.get("weights_sha256"),
            base_repo_revision=receipt.model_identity.get("base_repo_revision"),
            device=receipt.model_identity.get("device", "cuda"),
        )
        if receipt.host == JETSON_HOST:
            # §3.2：jetson 收据的身份块含六个 llama 键；客户端身份以收据为期望，`bind_identity` 再逐键核对
            # 服务端 `/status` 自算身份（不接受用户传入 sha）。
            adapter.identity = dict(receipt.model_identity)
        return adapter
    return load_local_adapter(
        source=arguments.model_source,
        adapter_dir=arguments.adapter_dir,
        device=arguments.device,
        model_form=arguments.model_form,
        output_directory=Path(arguments.session_root) / arguments.session_id / "queries",
    )


def resolves_to_shared_runtime(runtime: Path) -> bool:
    """`--runtime` 是否**实际解析到**仓库真实 runtime 根（AC-12 修订 2）。

    `Path.resolve()` 的字符串相等覆盖相对路径、`..` 绕路与符号链接；但在大小写
    不敏感的文件系统上 `RUNTIME` 与 `runtime` 解析出的字符串并不相等，却是同一个
    目录。所以再比一次目录身份（`st_dev`/`st_ino`），两者任一成立即算共享槽。
    本函数**只 stat，不创建任何文件或目录**——同一行裁定要求拒绝前零写入。
    """
    candidate = Path(runtime)
    try:
        if candidate.resolve() == RUNTIME.resolve():
            return True
    except OSError:
        return False
    try:
        left, right = candidate.stat(), RUNTIME.stat()
    except OSError:
        # 目标或真实 runtime 尚不存在（全新 clone）：只能靠上面的字符串判定。
        return False
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def resolve_model_form(arguments: argparse.Namespace) -> str:
    """AC-21（B1）：省略 `--model-form` 时 `candidates` 取 `detector-tracks`、其余取 `c2-merged`；
    交叉形态与 `candidates` 缺 `--tracker det-assoc-v1 --resident` 均在启动前 `CONFIG_MISMATCH`。"""
    model_form = arguments.model_form
    if model_form is None:
        model_form = (
            bridge.CANDIDATES_MODEL_FORM
            if arguments.backend == bridge.CANDIDATES_BACKEND
            else "c2-merged"
        )
    try:
        bridge.require_backend_model_form(arguments.backend, model_form)
    except LanguageBridgeError as exception:
        raise ConfigMismatch(f"CONFIG_MISMATCH: {exception}") from exception
    if arguments.backend == bridge.CANDIDATES_BACKEND and (
        arguments.tracker != CANDIDATES_TRACKER or not getattr(arguments, "resident", False)
    ):
        raise ConfigMismatch(
            "CONFIG_MISMATCH: --backend candidates needs --tracker det-assoc-v1 --resident"
        )
    arguments.model_form = model_form
    return model_form


def _run_session(arguments: argparse.Namespace) -> int:
    resolve_model_form(arguments)
    runtime = Path(arguments.runtime)
    if resolves_to_shared_runtime(runtime) and not arguments.allow_shared_runtime:
        print(
            "拒绝启动：--runtime 指向共享的 runtime/（阶段 A 只写隔离目录）。"
            "阶段 B 获得授权后用 --allow-shared-runtime 明示。",
            file=sys.stderr,
        )
        return 2
    receipt = KReceipt.from_document(
        json.loads(Path(arguments.k_receipt).read_text(encoding="utf-8"))
    )
    selected_report = validate_measurement_sources(receipt)
    if arguments.backend != receipt.backend or arguments.model_form != receipt.model_form:
        raise ConfigMismatch("CONFIG_MISMATCH: requested backend/model form differs from K receipt")
    if receipt.backend == "http":
        endpoint = (selected_report or {}).get("transport", {}).get("endpoint")
        if not endpoint or arguments.server_url.rstrip("/") != endpoint.rstrip("/"):
            raise ConfigMismatch("CONFIG_MISMATCH: HTTP endpoint differs from the measured host")
    elif receipt.backend == "local-hf":
        if arguments.device != receipt.model_identity.get("device") or sys.platform != "darwin":
            raise ConfigMismatch("CONFIG_MISMATCH: local host/device differs from the measured Mac")
    if arguments.diagnostic and not arguments.session_id.startswith("diag-"):
        print("诊断会话的 session-id 必须以 diag- 开头（AC-12 修订 1）", file=sys.stderr)
        return 2
    config = SessionConfig(
        session_id=arguments.session_id,
        session_root=Path(arguments.session_root),
        runtime=runtime,
        receipt=receipt,
        adapter=_build_adapter(arguments),
        tracker_name=arguments.tracker,
        condition=arguments.condition,
        ground_plane_y_m=arguments.ground_plane_y_m,
        planned_duration_s=arguments.planned_duration_s,
        scenario_id=arguments.scenario_id,
        attempt_limit=arguments.attempt_limit,
        verify_interval_s=arguments.verify_interval_s,
        diagnostic=arguments.diagnostic,
        run_root=(
            Path(arguments.diagnostics_root) / arguments.session_id
            if arguments.diagnostic
            else None
        ),
        body_planner_config=Path(arguments.body_planner_config),
        body_scenario_config=Path(arguments.body_scenario_config),
        resident=bool(getattr(arguments, "resident", False)),
        body_policy=getattr(arguments, "body_policy", "threshold"),
    )
    session = LanguageSession(config)
    try:
        session.start()
        session.run()
    except SessionSlotBusy:
        print("SESSION_SLOT_BUSY：已有活会话占用该 runtime 槽", file=sys.stderr)
        return 3
    finally:
        session.close()
    return 0


def click_fields(arguments: argparse.Namespace) -> dict[str, Any] | None:
    """`click` 子命令参数 → 请求体 `click`（页面侧 e2e 起点只在点击页给出时附上）。"""
    if getattr(arguments, "command", None) != "click":
        return None
    fields: dict[str, Any] = {
        "x_px": float(arguments.x_px),
        "y_px": float(arguments.y_px),
        "frame_id": int(arguments.frame_id),
        "image_sha256": str(arguments.image_sha256),
    }
    page = {
        key: value
        for key, value in (
            ("latest_frame_id", arguments.page_latest_frame_id),
            ("click_received_unix_s", arguments.page_click_unix_s),
        )
        if value is not None
    }
    if page:
        fields["page"] = page
    return fields


def _run_capture_session(arguments: argparse.Namespace) -> int:
    """C9：`run --language off` 捕获模式入口——不读 K 收据、不建适配器与 worker，`k_pub` 取常量 `K_PUB`。"""
    runtime = Path(arguments.runtime)
    if resolves_to_shared_runtime(runtime) and not arguments.allow_shared_runtime:
        print(
            "拒绝启动：--runtime 指向共享的 runtime/（阶段 A 只写隔离目录）。"
            "阶段 B 获得授权后用 --allow-shared-runtime 明示。",
            file=sys.stderr,
        )
        return 2
    if arguments.tracker != CANDIDATES_TRACKER or not getattr(arguments, "resident", False):
        raise ConfigMismatch("CONFIG_MISMATCH: --language off needs --tracker det-assoc-v1 --resident")
    if arguments.k_receipt is not None or arguments.backend is not None:
        raise ConfigMismatch("CONFIG_MISMATCH: --language off takes no --k-receipt/--backend")
    if arguments.diagnostic and not arguments.session_id.startswith("diag-"):
        print("诊断会话的 session-id 必须以 diag- 开头（AC-12 修订 1）", file=sys.stderr)
        return 2
    config = SessionConfig(
        session_id=arguments.session_id,
        session_root=Path(arguments.session_root),
        runtime=runtime,
        receipt=None,
        adapter=None,
        tracker_name=arguments.tracker,
        condition=arguments.condition,
        ground_plane_y_m=arguments.ground_plane_y_m,
        planned_duration_s=arguments.planned_duration_s,
        scenario_id=arguments.scenario_id,
        diagnostic=arguments.diagnostic,
        run_root=(
            Path(arguments.diagnostics_root) / arguments.session_id
            if arguments.diagnostic
            else None
        ),
        body_planner_config=Path(arguments.body_planner_config),
        body_scenario_config=Path(arguments.body_scenario_config),
        resident=True,
        body_policy=getattr(arguments, "body_policy", "threshold"),
        language=False,
        capture_config=arguments.capture_config,
        fastfix_config=getattr(arguments, "fastfix_config", None),
    )
    session = LanguageSession(config)
    try:
        session.start()
        session.run()
    except SessionSlotBusy:
        print("SESSION_SLOT_BUSY：已有活会话占用该 runtime 槽", file=sys.stderr)
        return 3
    finally:
        session.close()
    return 0


def _delay_argument(text: str) -> float:
    """A4：`--delay-s` ∈ [0, 8] s（缺省 0）；越界或非有限数在写请求前拒绝。"""
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"--delay-s must be a number: {text!r}") from exc
    if not math.isfinite(value) or not DELAY_MIN_S <= value <= DELAY_MAX_S:
        raise argparse.ArgumentTypeError(f"--delay-s must be within [{DELAY_MIN_S}, {DELAY_MAX_S}] s")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="P1-ENG-LOOP-001 受限语言选框闭环会话与操作者入口"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="起会话进程")
    run.add_argument("--session-id", required=True)
    run.add_argument("--session-root", required=True)
    run.add_argument("--runtime", required=True)
    run.add_argument("--k-receipt", default=None, help="--language on 时必填（K 收据）；--language off 不读")
    run.add_argument("--backend", choices=bridge.BACKENDS, default=None, help="--language on 时必填")
    run.add_argument(
        "--language",
        choices=("on", "off"),
        default="on",
        help="P1-ENG-CAPTURE-001：on（缺省）= 兼容模式；off = 捕获模式（不读 K 收据、不建适配器与 worker，"
        "需 --tracker det-assoc-v1 --resident）",
    )
    run.add_argument(
        "--capture-config",
        type=Path,
        default=None,
        help="捕获参数文件（缺省 config/p1-eng-capture-001.json）",
    )
    run.add_argument(
        "--fastfix-config",
        type=Path,
        default=None,
        help="P1-ENG-FASTFIX-001 门值/降级/重捕参数文件（只在 --language off；缺省 config/p1-eng-fastfix-001.json）",
    )
    run.add_argument(
        "--model-form",
        choices=bridge.MODEL_FORMS,
        default=None,
        help="缺省：--backend candidates 取 detector-tracks，其余取 c2-merged（AC-21）",
    )
    run.add_argument("--model-source", type=Path)
    run.add_argument("--adapter-dir", type=Path)
    run.add_argument("--device", default="mps")
    run.add_argument("--server-url", default="http://127.0.0.1:8760")
    run.add_argument("--replay-blind", type=Path)
    run.add_argument("--replay-predictions", type=Path)
    run.add_argument("--replay-blind-sha256")
    run.add_argument("--replay-predictions-sha256")
    run.add_argument("--tracker", default="nanotrack-v2")
    run.add_argument(
        "--resident",
        action="store_true",
        help="P1-ENG-ACQ-001 常驻指针式快层（需 --tracker det-assoc-v1）；缺省为 LOOP-001 段式路径",
    )
    run.add_argument("--condition", choices=("follow", "nadir"), default="follow")
    run.add_argument("--ground-plane-y-m", type=float, default=0.0)
    run.add_argument("--planned-duration-s", type=float, default=300.0)
    run.add_argument("--scenario-id", default=None)
    run.add_argument("--attempt-limit", type=int, default=ATTEMPT_LIMIT)
    run.add_argument("--verify-interval-s", type=float, default=T_V_S)
    run.add_argument("--diagnostic", action="store_true")
    run.add_argument(
        "--body-planner-config",
        type=Path,
        default=PROJECT_ROOT / "config" / "p1-m3-body-001.json",
        help="R-B8：冻结 BODY-001 阈值规划器配置（总是启用，配置不符即拒绝启动）",
    )
    run.add_argument(
        "--body-scenario-config",
        type=Path,
        default=PROJECT_ROOT / "config" / "scenario.default.json",
        help="规划器读取锚点/云台限位的场景；必须与实际生效场景一致",
    )
    run.add_argument(
        "--body-policy",
        choices=BODY_POLICIES,
        default="threshold",
        help="P1-ENG-LOOP-002 A1：缺省 threshold（不变）；standoff 走 FRAME-001 standoff-band-v1，"
        "要求 runtime/scenario_config.json 存在且与 --body-scenario-config 逐值相等",
    )
    run.add_argument(
        "--diagnostics-root",
        default=str(PROJECT_ROOT / "outputs/eng-loop/P1-ENG-LOOP-001/diagnostics"),
    )
    run.add_argument(
        "--allow-shared-runtime",
        action="store_true",
        help="阶段 B 授权后才用：允许把共享 runtime/ 当作桥与段归档根",
    )

    for name, needs in (
        ("ask", "instruction"),
        ("confirm", "index"),
        ("reject", "token"),
        ("respecify", "optional-instruction"),
        ("verify", None),
        ("confirm-lost", "token"),
        ("dismiss", "token"),
        ("release", "token"),
        ("stop", None),
        ("click", "click"),
    ):
        command = subparsers.add_parser(name, help=f"发送 {name} 请求")
        command.add_argument("--session-id", required=True)
        command.add_argument("--runtime", required=True)
        command.add_argument("--request-id", default=None)
        if needs == "instruction":
            command.add_argument("instruction")
        if needs == "optional-instruction":
            command.add_argument("instruction", nargs="?", default=None)
        if needs == "index":
            command.add_argument("index", type=int)
            command.add_argument("--token", required=True)
        if needs == "token":
            command.add_argument("--token", required=True)
        if needs == "click":
            # P1-ENG-CAPTURE-001 C7：图像点击（只在 `run --language off` 捕获模式受理）。
            command.add_argument("--x-px", type=float, required=True)
            command.add_argument("--y-px", type=float, required=True)
            command.add_argument("--frame-id", type=int, required=True)
            command.add_argument("--image-sha256", required=True)
            command.add_argument("--page-latest-frame-id", type=int, default=None)
            command.add_argument("--page-click-unix-s", type=float, default=None)
        if name in {"ask", "respecify"}:
            # A4：逐次呈现延迟与意图标签（意图只写回执日志，不进查询/prompt/决策）。
            command.add_argument("--delay-s", type=_delay_argument, default=None)
            command.add_argument("--intent", default=None)
        # 同一个隔离边界：写请求也会在 runtime 里建写者锁与桥文件，
        # 所以九个操作者动作与 `run` 共用守卫与开关（AC-12 修订 2）。
        command.add_argument("--allow-shared-runtime", action="store_true")

    status = subparsers.add_parser("status", help="打印会话状态与最近结果")
    status.add_argument("--runtime", required=True)

    demo = subparsers.add_parser("replay-demo", help="夹具帧 + 回放桩的可运行示例")
    demo.add_argument("--session-root", required=True)
    demo.add_argument("--frames", type=Path, required=True, help="回放帧目录")
    demo.add_argument("--replay-blind", type=Path, required=True)
    demo.add_argument("--replay-predictions", type=Path, required=True)
    demo.add_argument("--base-predictions", type=Path, default=None)
    demo.add_argument("--verify-interval-s", type=float, default=1.0)

    serve = subparsers.add_parser("serve", help="起 5060 单工推理服务")
    serve.add_argument("rest", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.command == "run":
        if getattr(arguments, "language", "on") == "on" and (arguments.k_receipt is None or arguments.backend is None):
            parser.error("the following arguments are required: --k-receipt, --backend")
        if getattr(arguments, "language", "on") == "off":
            return _run_capture_session(arguments)
        return _run_session(arguments)
    if arguments.command == "serve":
        from tools import language_serve

        return language_serve.main(arguments.rest)
    if arguments.command == "status":
        document = bridge.read_tracker_state(Path(arguments.runtime))
        result = bridge.read_result(Path(arguments.runtime))
        print(json.dumps({"tracker_state": document, "last_result": result}, indent=2))
        return 0
    if arguments.command == "replay-demo":
        from .language_demo import run_replay_demo

        return run_replay_demo(arguments)
    action = arguments.command.replace("-", "_")
    if resolves_to_shared_runtime(Path(arguments.runtime)) and not getattr(
        arguments, "allow_shared_runtime", False
    ):
        print(
            "拒绝写请求：--runtime 指向共享的 runtime/（阶段 A 只写隔离目录）。"
            "阶段 B 获得授权后用 --allow-shared-runtime 明示。",
            file=sys.stderr,
        )
        return 2
    instruction = None
    if getattr(arguments, "instruction", None):
        try:
            instruction = bridge.parse_instruction(arguments.instruction)
        except InstructionUnsupported as exception:
            print(f"instruction_unsupported: {exception}", file=sys.stderr)
            return 2
    if action == "click":
        try:
            bridge.validate_click_fields(click_fields(arguments))
        except LanguageBridgeError as exception:
            print(f"click_invalid: {exception}", file=sys.stderr)
            return 2
    try:
        outcome = send_request(
            Path(arguments.runtime),
            session_id=arguments.session_id,
            action=action,
            instruction=instruction,
            candidate_index=getattr(arguments, "index", None),
            token=getattr(arguments, "token", None),
            request_id=arguments.request_id,
            delay_s=getattr(arguments, "delay_s", None),
            intent=getattr(arguments, "intent", None),
            click=click_fields(arguments),
        )
    except WriterBusy:
        print("WRITER_BUSY：另一个 CLI 正持有写者锁，本次未写入请求", file=sys.stderr)
        return 4
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return 0 if outcome.get("receipt") else 5


if __name__ == "__main__":
    raise SystemExit(main())
