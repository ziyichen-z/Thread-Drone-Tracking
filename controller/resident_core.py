"""P1-ENG-ACQ-001 §3.1/§3.2/§3.4/§3.4.1/§3.5：常驻关联的轨迹历史、指针与 `designate` 解析器。

本模块**无 ultralytics 依赖**：插件 `DetAssocTracker(mode="resident").step` 与离线 E1/E2 线束
（`tools/eng_acq`）共用同一个 `ResidentCore`（AC-6 证明两条路径逐帧一致）。只导入标准库与
`controller.trackers` / `controller.reanchor` 的几何与回放件；不导入任何真值、索引或 `tools.*`（AC-9）。

- 历史（K1）：环形缓冲，容量 `history_depth`（≥ 100，缺省 128 = `retained_frame_count`）；键**只取
  传感器 `frame_id`**（严格递增，否则 `ProtocolMisuse`）；库调用计数 `library_frame_id` 只记录、不作键。
  每条含该帧相机位姿、全部 `tracked` 行（库输出）与 `lost` 行（`lost_stracks` 的 KF 预测框）及该帧
  被移除的 ID。
- 指针（K3）：`follow(track_id)` 只改指针，不触碰关联器；`pointer_result(frame_id)` 纯读历史。
- 解析（K3，AC-3/AC-19 接受释义）：三级顺序的前两级——第一级同帧历史匹配，第一级无轨迹过门时
  第二级在 k 帧图像上起跟一次性 SOT、有界回放到历史头 h 并按同帧判据收养；结果只取六值闭集，
  `resolution_level` 与 `level2` 只作字段。第三级（世界点转向重捕）由会话在 `TRACK_ENDED` 后执行。
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
import math
from typing import Any, Callable, Iterator, Mapping, Sequence

from .reanchor import BufferedFrame, ReplayResult, replay_tracker
from .trackers import TrackerPlugin, TrackerResult, clip_box_norm

BOUND = "BOUND"
BOUND_COASTING = "BOUND_COASTING"
TRACK_ENDED = "TRACK_ENDED"
NO_TRACK_AT_K = "NO_TRACK_AT_K"
AMBIGUOUS = "AMBIGUOUS"
FRAME_NOT_IN_HISTORY = "FRAME_NOT_IN_HISTORY"
#: 六值闭集（§3.4）；不得出现第七值。
RESULTS: tuple[str, ...] = (BOUND, BOUND_COASTING, TRACK_ENDED, NO_TRACK_AT_K, AMBIGUOUS, FRAME_NOT_IN_HISTORY)

#: `level2.reason` 闭集（§3.4.1 + AC-3 接受释义）：固定值与两个带 `@<frame_id>` 的前缀。
LEVEL2_FIXED_REASONS: tuple[str, ...] = (
    "not_attempted_frame_missing",
    "source_too_old",
    "sot_init_failed",
    "invalid_source_box",
    "replay_error",
    "no_adoption",
)
LEVEL2_FRAME_REASON_PREFIXES: tuple[str, ...] = ("sot_lost@", "replay_timeout@")

TRACKED = "tracked"
LOST = "lost"
#: P1-ENG-CAPTURE-001 C3（AR1-2）：库 `tracked_stracks` 中尚未激活的轨迹（F14；只作修复证据，永不算 ok）。
UNCONFIRMED = "unconfirmed"
ROW_STATES: tuple[str, ...] = (TRACKED, LOST, UNCONFIRMED)

#: AR1-2 KF 快照阶段：`prior` = 本帧量测更新前（补偿后）；`posterior` = 本帧已用检测更新。
KF_PRIOR = "prior"
KF_POSTERIOR = "posterior"
KF_PHASES: tuple[str, ...] = (KF_PRIOR, KF_POSTERIOR)

REASON_NO_POINTER = "no_pointer"
REASON_UNMATCHED = "bound_track_unmatched"
REASON_REMOVED = "bound_track_removed"
REASON_INVALID_BOX = "invalid_tracker_box"

MIN_HISTORY_DEPTH = 100
DEFAULT_HISTORY_DEPTH = 128
#: P1-ENG-CAPTURE-001 IR-1（AC-3/13 修订 2）：历史消费视图。缺省 `compat` = 旧消费视图（出画/退化 lost 行与
#: 未确认行视为无该行，指针按旧帧判 `bound_track_removed`）；只有捕获入口显式传 `capture` 才启用增强历史
#: （保留带 `out_of_frame` 的 lost 行与未确认行，指针判 UNMATCHED）。不从 class_policy/GMC 值推断。
HISTORY_VIEW_COMPAT = "compat"
HISTORY_VIEW_CAPTURE = "capture"
HISTORY_VIEWS: tuple[str, ...] = (HISTORY_VIEW_COMPAT, HISTORY_VIEW_CAPTURE)


class ProtocolMisuse(RuntimeError):
    """常驻/兼容两种模式的方法集互斥、`step` 帧序回退或重复（§3.1）；不静默降级。"""


def is_level2_reason(reason: Any) -> bool:
    if not isinstance(reason, str):
        return False
    if reason in LEVEL2_FIXED_REASONS:
        return True
    for prefix in LEVEL2_FRAME_REASON_PREFIXES:
        if reason.startswith(prefix):
            tail = reason[len(prefix):]
            return tail.isdigit()
    return False


@dataclass(frozen=True)
class ResolverConfig:
    """§3.4 申请值（D1/D2 裁定 (d)：插件配置项，记录生效值，不改冻结规格）。"""

    tau: float = 0.5
    margin: float = 0.2
    coasting_limit: int = 30
    t_replay_s: float = 2.0
    l_replay_frames: int = DEFAULT_HISTORY_DEPTH

    def as_record(self) -> dict[str, Any]:
        return {
            "tau": self.tau,
            "margin": self.margin,
            "backup_criterion": "track_center_inside_designated_box",
            "coasting_limit_calls": self.coasting_limit,
            "t_replay_s": self.t_replay_s,
            "l_replay_frames": self.l_replay_frames,
        }


@dataclass(frozen=True)
class KfSnapshot:
    """P1-ENG-CAPTURE-001 §3.1 / AR1-2：库 KF 的只读深复制（不回写库）。

    单位：检测输入画幅像素（640×480）、像素²、每帧。`valid=False` 时 `invalid_reason` 非空，消费方一律
    fail-closed（运动门不过、授权落行 8）。对齐键 = (sensor_frame_id, library_frame_id, track_key, phase)。"""

    sensor_frame_id: int
    library_frame_id: int
    track_key: int
    phase: str
    xywh_px: tuple[float, float, float, float]
    vel_px_per_frame: tuple[float, float]
    pos_cov_px2: tuple[tuple[float, float], tuple[float, float]]
    valid: bool = True
    invalid_reason: str | None = None

    def as_record(self) -> dict[str, Any]:
        # 非有限分量记 null（日志禁 NaN）；无效快照的 `valid=False` 与原因照记，重放按原因 fail-closed。
        return {
            "sensor_frame_id": self.sensor_frame_id,
            "library_frame_id": self.library_frame_id,
            "track_key": self.track_key,
            "phase": self.phase,
            "xywh_px": [_finite_or_none(v) for v in self.xywh_px],
            "vel_px_per_frame": [_finite_or_none(v) for v in self.vel_px_per_frame],
            "pos_cov_px2": [[_finite_or_none(v) for v in row] for row in self.pos_cov_px2],
            "valid": self.valid,
            "invalid_reason": self.invalid_reason,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "KfSnapshot":
        return make_kf_snapshot(
            int(record["sensor_frame_id"]),
            int(record["library_frame_id"]),
            int(record["track_key"]),
            str(record["phase"]),
            record.get("xywh_px"),
            record.get("vel_px_per_frame"),
            record.get("pos_cov_px2"),
            forced_invalid=None if record.get("valid", True) else (record.get("invalid_reason") or "kf_invalid"),
        )


def _finite_or_none(value: float) -> float | None:
    number = float(value)
    return number if math.isfinite(number) else None


def _float_tuple(values: Any, length: int) -> tuple[float, ...] | None:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or len(values) != length:
        return None
    try:
        return tuple(float(v) for v in values)
    except (TypeError, ValueError):
        return None


def make_kf_snapshot(
    sensor_frame_id: int,
    library_frame_id: int,
    track_key: int,
    phase: str,
    xywh: Any,
    velocity: Any,
    pos_cov: Any,
    *,
    forced_invalid: str | None = None,
) -> KfSnapshot:
    """构造并校验快照：非有限分量、w/h ≤ 0、协方差非对称或最小特征值 < −1e-9 → `valid=False` + 原因。"""
    if phase not in KF_PHASES:
        raise ValueError(f"kf phase {phase!r} outside {KF_PHASES}")
    box = _float_tuple(xywh, 4)
    vel = _float_tuple(velocity, 2)
    rows = (
        tuple(_float_tuple(row, 2) for row in pos_cov)
        if isinstance(pos_cov, Sequence) and not isinstance(pos_cov, (str, bytes)) and len(pos_cov) == 2
        else None
    )
    reason = forced_invalid
    if reason is None and (box is None or vel is None or rows is None or any(row is None for row in rows)):
        reason = "kf_unreadable"
    if reason is None:
        values = [*box, *vel, *rows[0], *rows[1]]  # type: ignore[misc]
        if not all(math.isfinite(v) for v in values):
            reason = "kf_non_finite"
        elif box[2] <= 0.0 or box[3] <= 0.0:  # type: ignore[index]
            reason = "kf_non_positive_size"
        else:
            a, b = rows[0]  # type: ignore[index]
            c, d = rows[1]  # type: ignore[index]
            if abs(b - c) > 1e-9 * max(1.0, abs(b), abs(c)):
                reason = "kf_cov_asymmetric"
            else:
                half_trace = (a + d) / 2.0
                det = a * d - b * c
                disc = math.sqrt(max(half_trace * half_trace - det, 0.0))
                if half_trace - disc < -1e-9:
                    reason = "kf_cov_not_psd"
    zero2 = ((0.0, 0.0), (0.0, 0.0))
    return KfSnapshot(
        int(sensor_frame_id),
        int(library_frame_id),
        int(track_key),
        phase,
        tuple(box) if box is not None else (0.0, 0.0, 0.0, 0.0),  # type: ignore[arg-type]
        tuple(vel) if vel is not None else (0.0, 0.0),  # type: ignore[arg-type]
        tuple(tuple(row) for row in rows) if rows is not None and all(r is not None for r in rows) else zero2,  # type: ignore[arg-type]
        reason is None,
        reason,
    )


@dataclass(frozen=True)
class RawDetection:
    """C3：本帧策略后检测（未裁剪像素框、置信度、策略后类别）；只在进程内与会话日志。"""

    det_index: int
    box_px: tuple[float, float, float, float]
    conf: float
    cls: int

    @property
    def center_px(self) -> tuple[float, float]:
        return ((self.box_px[0] + self.box_px[2]) / 2.0, (self.box_px[1] + self.box_px[3]) / 2.0)

    def as_record(self) -> dict[str, Any]:
        return {"det_index": self.det_index, "box_px": [float(v) for v in self.box_px], "conf": self.conf, "cls": self.cls}

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "RawDetection":
        return cls(int(record["det_index"]), tuple(float(v) for v in record["box_px"]), float(record["conf"]), int(record["cls"]))  # type: ignore[arg-type]


@dataclass(frozen=True)
class TrackRow:
    track_id: int
    box_norm: tuple[float, float, float, float]
    score: float
    cls: int
    state: str
    #: C3（AR1-2）：本帧完整策略后检测数组里的匹配下标（无则 −1）。
    matched_det_index: int = -1
    #: C3：出画或退化的 lost 框（未裁剪归一化框），不再丢弃；指针此时判 UNMATCHED。
    out_of_frame: bool = False
    #: C3：该行库 KF 的本帧快照（发生量测更新者 posterior，未更新者 prior）；无效 → None + 原因。
    kf: KfSnapshot | None = None
    kf_invalid_reason: str | None = None

    def as_record(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "track_id": self.track_id,
            "box_norm": [float(v) for v in self.box_norm],
            "score": self.score,
            "cls": self.cls,
            "state": self.state,
        }
        # 旧字段集逐字不变；新列只在非缺省时出现（ACQ 线束旧记录可原样解析）。
        if self.matched_det_index != -1:
            record["matched_det_index"] = self.matched_det_index
        if self.out_of_frame:
            record["out_of_frame"] = True
        if self.kf is not None:
            record["kf"] = self.kf.as_record()
        if self.kf_invalid_reason is not None:
            record["kf_invalid_reason"] = self.kf_invalid_reason
        return record


@dataclass(frozen=True)
class HistoryEntry:
    frame_id: int
    simulation_time_s: float | None
    capture_monotonic_s: float | None
    camera_position_world_m: tuple[float, ...] | None
    camera_rotation_xyzw: tuple[float, ...] | None
    intrinsics_px: Mapping[str, float] | None
    library_frame_id: int
    tracks: tuple[TrackRow, ...]
    removed_ids: tuple[int, ...]
    width: int | None = None
    height: int | None = None
    #: C3（AR1-2）：本帧策略后原始检测、两阶段 KF 快照与非有限框静默丢弃的 ID（只在进程内与会话日志）。
    raw_detections: tuple[RawDetection, ...] = ()
    prior_snapshots: tuple[KfSnapshot, ...] = ()
    post_snapshots: tuple[KfSnapshot, ...] = ()
    silently_dropped_ids: tuple[int, ...] = ()
    #: 关联器是否提供了更新前 prior（未提供 = 全部缺失，消费方 fail-closed）。
    priors_available: bool = False

    def rows(self, state: str) -> tuple[TrackRow, ...]:
        return tuple(row for row in self.tracks if row.state == state)

    def row(self, track_id: int) -> TrackRow | None:
        return next((row for row in self.tracks if row.track_id == track_id), None)

    def prior(self, track_id: int) -> KfSnapshot | None:
        return next((snap for snap in self.prior_snapshots if snap.track_key == int(track_id)), None)

    def post(self, track_id: int) -> KfSnapshot | None:
        return next((snap for snap in self.post_snapshots if snap.track_key == int(track_id)), None)

    def detection(self, det_index: int) -> RawDetection | None:
        if det_index < 0:
            return None
        return next((det for det in self.raw_detections if det.det_index == int(det_index)), None)

    def as_record(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "frame_id": self.frame_id,
            "simulation_time_s": self.simulation_time_s,
            "capture_monotonic_s": self.capture_monotonic_s,
            "library_frame_id": self.library_frame_id,
            "tracks": [row.as_record() for row in self.tracks],
            "removed_ids": list(self.removed_ids),
        }
        # 新列只在非空时出现（旧记录字段集逐字不变）。
        if self.raw_detections:
            record["raw_detections"] = [det.as_record() for det in self.raw_detections]
        if self.prior_snapshots or self.priors_available:
            record["prior_snapshots"] = [snap.as_record() for snap in self.prior_snapshots]
            record["priors_available"] = self.priors_available
        if self.post_snapshots:
            record["post_snapshots"] = [snap.as_record() for snap in self.post_snapshots]
        if self.silently_dropped_ids:
            record["silently_dropped_ids"] = list(self.silently_dropped_ids)
        return record


@dataclass(frozen=True)
class Designation:
    designation_id: int
    result: str
    frame_id_k: int
    head_frame_id: int | None
    resolution_level: int | None
    track_id: int | None
    level1: Mapping[str, Any]
    level2: Mapping[str, Any] | None
    candidates: tuple[int, ...] = ()
    events: tuple[Mapping[str, Any], ...] = ()

    def as_record(self) -> dict[str, Any]:
        return {
            "designation_id": self.designation_id,
            "frame_id_k": self.frame_id_k,
            "head_frame_id": self.head_frame_id,
            "result": self.result,
            "resolution_level": self.resolution_level,
            "track_id": self.track_id,
            "level1": dict(self.level1),
            "level2": None if self.level2 is None else dict(self.level2),
            "candidates": list(self.candidates),
        }


Level2Runner = Callable[[int, Sequence[float], int], ReplayResult]


def box_iou(left: Sequence[float], right: Sequence[float]) -> float:
    a = clip_box_norm(left)
    b = clip_box_norm(right)
    if a is None or b is None:
        return 0.0
    ix = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = a[2] * a[3] + b[2] * b[3] - inter
    return 0.0 if union <= 0.0 else inter / union


def center_inside(row_box: Sequence[float], box: Sequence[float]) -> bool:
    cx = float(row_box[0]) + float(row_box[2]) / 2.0
    cy = float(row_box[1]) + float(row_box[3]) / 2.0
    x, y, w, h = (float(v) for v in box)
    return x <= cx <= x + w and y <= cy <= y + h


def select_track(
    box: Sequence[float], rows: Sequence[TrackRow], tau: float, margin: float
) -> tuple[str, int | None, tuple[int, ...], dict[str, Any]]:
    """同帧判据（第一级匹配与第二级收养共用）。

    返回 `("one", j, (), info)` / `("ambiguous", None, 候选, info)` / `("none", None, (), info)`。
    过门 = IoU ≥ τ；≥ 2 条过门时裕度 = 最佳 − 次佳（均在过门者中），裕度 ≥ m 取最佳，否则歧义；
    0 条过门时用备用判据「轨迹框中心落在指定框内」，恰好 1 条满足才取（≥ 2 条或 0 条 = 无过门）。
    """
    scored = sorted(((box_iou(box, row.box_norm), row.track_id) for row in rows), key=lambda item: (-item[0], item[1]))
    passers = [(value, track_id) for value, track_id in scored if value >= tau]
    info: dict[str, Any] = {
        "passers": [[track_id, round(value, 6)] for value, track_id in passers],
        "best_iou": round(scored[0][0], 6) if scored else None,
    }
    if len(passers) == 1:
        info["criterion"] = "iou"
        return "one", passers[0][1], (), info
    if len(passers) >= 2:
        gap = passers[0][0] - passers[1][0]
        info["margin"] = round(gap, 6)
        if gap >= margin:
            info["criterion"] = "iou_margin"
            return "one", passers[0][1], (), info
        info["criterion"] = "ambiguous_margin"
        return "ambiguous", None, tuple(track_id for _value, track_id in passers), info
    inside = sorted(row.track_id for row in rows if center_inside(row.box_norm, box))
    info["center_inside"] = inside
    if len(inside) == 1:
        info["criterion"] = "center_inside"
        return "one", inside[0], (), info
    info["criterion"] = "none"
    return "none", None, (), info


def level2_mapping(replay: ReplayResult) -> tuple[str, str | None, dict[str, Any]]:
    """AC-3 接受释义：`replay_tracker` 事件 → (结果, level2.reason, 诊断字段)。

    `RESEED_READY` 返回 `("READY", None, {})`，由调用方做 h 帧收养。"""
    event = replay.event
    diagnostic: dict[str, Any] = {"replay_event": event, "replay_reason": replay.reason}
    if event == "RESEED_READY":
        return "READY", None, diagnostic
    if event == "RESEED_DISCARDED_MISSING_FRAME":
        return NO_TRACK_AT_K, "not_attempted_frame_missing", diagnostic
    if event == "RESEED_DISCARDED_STALE":
        return NO_TRACK_AT_K, "source_too_old", diagnostic
    if event == "RESEED_DISCARDED_NOT_CONVERGED":
        first_unprocessed = (replay.head_frame_id if replay.head_frame_id is not None else replay.source_frame_id) + 1
        return NO_TRACK_AT_K, f"replay_timeout@{first_unprocessed}", diagnostic
    if event == "RESEED_DISCARDED_INVALID_BOX":
        if replay.reason == "invalid_source_box":
            return NO_TRACK_AT_K, "invalid_source_box", diagnostic
        failed = replay.head_frame_id if replay.head_frame_id is not None else replay.source_frame_id
        return NO_TRACK_AT_K, f"sot_lost@{failed}", diagnostic
    if event == "RESEED_FAILED":
        if replay.reason == "tracker_init_failed":
            return NO_TRACK_AT_K, "sot_init_failed", diagnostic
        diagnostic["exception_class"] = replay.reason
        return NO_TRACK_AT_K, "replay_error", diagnostic
    diagnostic["exception_class"] = f"unknown_event:{event}"
    return NO_TRACK_AT_K, "replay_error", diagnostic


class RepositoryFrameWindow:
    """§3.4.1 帧源适配器：与载体同一 `FrameRepository`（离线线束为数据根归档），只暴露 [k, h] 窗口，
    提供 `replay_tracker` 所需的 `get` / `after_through`；逐帧惰性读取，不建内存帧缓存。

    `clock_key`：STALE 判定用的采集时钟字段（运行时 v3 帧为 `capture_monotonic_s`；
    离线 v1 归档可指定 `simulation_time_s`）。"""

    def __init__(self, repository: Any, first_frame_id: int, last_frame_id: int, *, clock_key: str = "capture_monotonic_s"):
        self._repository = repository
        self.first = int(first_frame_id)
        self.last = int(last_frame_id)
        self.clock_key = clock_key
        self.loads = 0

    def get(self, frame_id: int) -> BufferedFrame | None:
        frame_id = int(frame_id)
        if not self.first <= frame_id <= self.last:
            return None
        try:
            bundle = self._repository.load(frame_id)
        except (FileNotFoundError, ValueError):
            return None
        self.loads += 1
        clock = bundle.metadata.get(self.clock_key)
        if isinstance(clock, bool) or not isinstance(clock, (int, float)) or not math.isfinite(float(clock)):
            return None
        return BufferedFrame(frame_id, float(clock), bundle.image, bundle.metadata, None)

    def after_through(self, start_exclusive: int, end_inclusive: int) -> Iterator[BufferedFrame]:
        for frame_id in range(int(start_exclusive) + 1, int(end_inclusive) + 1):
            frame = self.get(frame_id)
            if frame is None:
                raise FileNotFoundError("replay intermediate frame missing")
            yield frame


def repository_level2_runner(
    repository: Any,
    sot_factory: Callable[[], TrackerPlugin],
    config: ResolverConfig,
    *,
    maximum_source_age_s: float,
    clock_key: str = "capture_monotonic_s",
    monotonic: Callable[[], float] | None = None,
) -> Level2Runner:
    """运行时第二级：`replay_tracker` 原样复用（事实 18），帧源为 [k, h] 窗口。"""

    def run(k: int, box: Sequence[float], h: int) -> ReplayResult:
        window = RepositoryFrameWindow(repository, k, h, clock_key=clock_key)
        kwargs: dict[str, Any] = {}
        if monotonic is not None:
            kwargs["monotonic"] = monotonic
        return replay_tracker(
            sot_factory,
            window,  # type: ignore[arg-type]
            source_frame_id=int(k),
            source_box_norm=list(box),
            target_head_frame_id=int(h),
            maximum_source_age_s=maximum_source_age_s,
            catchup_timeout_s=config.t_replay_s,
            **kwargs,
        )

    return run


def _metadata_float(metadata: Mapping[str, Any], key: str) -> float | None:
    value = metadata.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _metadata_int(metadata: Mapping[str, Any], key: str) -> int | None:
    value = metadata.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def _metadata_tuple(metadata: Mapping[str, Any], key: str) -> tuple[float, ...] | None:
    value = metadata.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    try:
        return tuple(float(v) for v in value)
    except (TypeError, ValueError):
        return None


class ResidentCore:
    """历史 + 指针 + 解析器（插件与线束共用的同一实现）。"""

    def __init__(
        self, history_depth: int = DEFAULT_HISTORY_DEPTH, config: ResolverConfig | None = None, *, history_view: str = HISTORY_VIEW_COMPAT
    ):
        if isinstance(history_depth, bool) or not isinstance(history_depth, int) or history_depth < MIN_HISTORY_DEPTH:
            raise ValueError(f"history_depth must be an integer ≥ {MIN_HISTORY_DEPTH}")
        if history_view not in HISTORY_VIEWS:
            raise ValueError(f"history_view must be one of {HISTORY_VIEWS}")
        self.history_view = history_view
        self.history_depth = history_depth
        self.config = config or ResolverConfig(l_replay_frames=history_depth)
        if self.config.l_replay_frames > history_depth:
            raise ValueError("L_replay must not exceed history_depth")
        self._history: OrderedDict[int, HistoryEntry] = OrderedDict()
        self._pointer: int | None = None
        self._ended_ids: set[int] = set()
        self._next_designation_id = 1
        self.designation: Designation | None = None
        self._coasting: dict[str, Any] | None = None
        self._events: list[dict[str, Any]] = []

    # --- 历史（K1）-----------------------------------------------------------

    @property
    def head_frame_id(self) -> int | None:
        return next(reversed(self._history)) if self._history else None

    def history(self, frame_id: int) -> HistoryEntry | None:
        return self._history.get(int(frame_id))

    def __len__(self) -> int:
        return len(self._history)

    def record(
        self,
        frame_id: int,
        metadata: Mapping[str, Any],
        tracked_rows: Sequence[TrackRow],
        lost_rows: Sequence[TrackRow],
        removed_ids: Sequence[int],
        library_frame_id: int,
        *,
        unconfirmed_rows: Sequence[TrackRow] = (),
        raw_detections: Sequence[RawDetection] = (),
        prior_snapshots: Sequence[KfSnapshot] = (),
        post_snapshots: Sequence[KfSnapshot] = (),
        silently_dropped_ids: Sequence[int] = (),
        priors_available: bool = False,
    ) -> HistoryEntry:
        if isinstance(frame_id, bool) or not isinstance(frame_id, int):
            raise ProtocolMisuse("frame_id must be the integer sensor frame id")
        head = self.head_frame_id
        if head is not None and frame_id <= head:
            raise ProtocolMisuse(f"frame_id {frame_id} must be strictly greater than history head {head}")
        rows: list[TrackRow] = []
        compat_view = self.history_view == HISTORY_VIEW_COMPAT
        for row, state in (
            [(r, TRACKED) for r in tracked_rows] + [(r, LOST) for r in lost_rows] + [(r, UNCONFIRMED) for r in unconfirmed_rows]
        ):
            if row.state != state:
                raise ValueError(f"row {row.track_id} state {row.state!r} is not {state!r}")
            if compat_view and (row.out_of_frame or row.state == UNCONFIRMED):
                # IR-1：兼容视图在旧 `_norm_box` 会丢弃的条件下仍视为无该行；未确认行不进旧消费视图。
                continue
            rows.append(row)
        intrinsics = metadata.get("intrinsics_px")
        entry = HistoryEntry(
            frame_id=frame_id,
            simulation_time_s=_metadata_float(metadata, "simulation_time_s"),
            capture_monotonic_s=_metadata_float(metadata, "capture_monotonic_s"),
            camera_position_world_m=_metadata_tuple(metadata, "camera_position_world_m"),
            camera_rotation_xyzw=_metadata_tuple(metadata, "camera_rotation_xyzw"),
            intrinsics_px=dict(intrinsics) if isinstance(intrinsics, Mapping) else None,
            library_frame_id=int(library_frame_id),
            tracks=tuple(rows),
            removed_ids=tuple(int(v) for v in removed_ids),
            width=_metadata_int(metadata, "width"),
            height=_metadata_int(metadata, "height"),
            raw_detections=tuple(raw_detections),
            prior_snapshots=tuple(prior_snapshots),
            post_snapshots=tuple(post_snapshots),
            silently_dropped_ids=tuple(int(v) for v in silently_dropped_ids),
            priors_available=bool(priors_available),
        )
        self._history[frame_id] = entry
        while len(self._history) > self.history_depth:
            self._history.popitem(last=False)
        self._update_coasting(entry)
        return entry

    def clear(self) -> None:
        """会话终止（回退/缺帧）：历史清空；指针与纪元一并清除。"""
        self._history.clear()
        self._pointer = None
        self._coasting = None

    # --- 指针（K3）-----------------------------------------------------------

    def pointer(self) -> int | None:
        return self._pointer

    def follow(self, track_id: int | None) -> None:
        new = None if track_id is None else int(track_id)
        if new != self._pointer:
            self._coasting = None  # 换指针才结束上一次指定的 coasting 记账；同 id 重复 follow 不改
        self._pointer = new

    def pointer_result(self, frame_id: int) -> TrackerResult:
        """纯读历史、不检测：无指针 → `no_pointer`；指针在该帧 tracked → ok；lost 池 → unmatched；否则 removed。"""
        if self._pointer is None:
            return TrackerResult.lost(REASON_NO_POINTER)
        entry = self.history(frame_id)
        if entry is None:
            raise ProtocolMisuse(f"pointer_result({frame_id}) has no history entry")
        if self._pointer in self._ended_ids:
            return TrackerResult.lost(REASON_REMOVED)
        row = entry.row(self._pointer)
        if row is None:
            return TrackerResult.lost(REASON_REMOVED)
        if row.state != TRACKED or row.out_of_frame:
            # C3：lost（含出画 `out_of_frame`）与未确认行都不算 ok。
            return TrackerResult.lost(REASON_UNMATCHED)
        box = clip_box_norm(row.box_norm)
        score = float(row.score)
        if box is None or not math.isfinite(score) or not 0.0 <= score <= 1.0:
            return TrackerResult.lost(REASON_INVALID_BOX)
        return TrackerResult(box_norm=box, ok=True, confidence=score, confidence_source="tracker")

    def drain_events(self) -> list[dict[str, Any]]:
        events, self._events = self._events, []
        return events

    def _update_coasting(self, entry: HistoryEntry) -> None:
        if self._coasting is None or self._pointer is None:
            return
        self._coasting["steps"] += 1
        row = entry.row(self._pointer)
        base = {"designation_id": self._coasting["designation_id"], "track_id": self._pointer, "frame_id": entry.frame_id}
        if row is not None and row.state == TRACKED:
            self._coasting = None
            self._events.append({"event": "COASTING_RECOVERED", **base})
            return
        if row is None:
            self._coasting = None
            self._events.append({"event": "COASTING_TO_TRACK_ENDED", "cause": "removed", **base})
            return
        # 上限 = `coasting_limit` 次 step（先到者）：第 limit 次 step 仍未找回即转 `TRACK_ENDED`（IR-8，C1 退回修正差一）。
        if self._coasting["steps"] >= self.config.coasting_limit:
            self._coasting = None
            self._ended_ids.add(self._pointer)
            self._events.append({"event": "COASTING_TO_TRACK_ENDED", "cause": "coasting_limit", **base})

    # --- 解析（K3）-----------------------------------------------------------

    def allocate_designation_id(self) -> int:
        """兼容尝试分配（AR1-3）：每次解析尝试先取号并 +1（起点 1）；失败也已发生，不回滚。"""
        designation_id = self._next_designation_id
        self._next_designation_id += 1
        return designation_id

    def resolve_designation(
        self, box_norm: Sequence[float], k: int, level2_runner: Level2Runner | None, designation_id: int
    ) -> Designation:
        """C5 纯解析：判据逐字同现行 `designate` 两级；**不**改指针、coasting、designation 记录或计数。"""
        k = int(k)
        head = self.head_frame_id
        box = [float(v) for v in box_norm]
        entry_k = self.history(k)
        if entry_k is None or head is None:
            return _validated(Designation(designation_id, FRAME_NOT_IN_HISTORY, k, head, None, None, {"attempted": False}, None))
        entry_h = self.history(head)
        assert entry_h is not None
        cfg = self.config
        kind, j, candidates, info = select_track(box, entry_k.rows(TRACKED), cfg.tau, cfg.margin)
        level1 = {"attempted": True, **info}
        if kind == "ambiguous":
            return _validated(Designation(designation_id, AMBIGUOUS, k, head, 1, None, level1, None, candidates))
        if kind == "one":
            assert j is not None
            row_h = entry_h.row(j)
            if row_h is not None and row_h.state == TRACKED and j not in self._ended_ids:
                return _validated(Designation(designation_id, BOUND, k, head, 1, j, level1, None))
            if row_h is not None and row_h.state == LOST and j not in self._ended_ids:
                return _validated(Designation(designation_id, BOUND_COASTING, k, head, 1, j, level1, None))
            return _validated(Designation(designation_id, TRACK_ENDED, k, head, 1, j, level1, None))
        return _validated(self._level2(designation_id, box, k, head, entry_h, level1, level2_runner))

    def record_designation(self, designation: Designation) -> Designation:
        """解析结果（成功或失败）照旧写 `core.designation` 与核心事件（不动指针/coasting）。"""
        return self._finish(designation)

    def begin_coasting(self, designation_id: int) -> None:
        """BOUND_COASTING 绑定成功后按现行设 coasting（同一 designation_id、步数 0）；只由提交事务调用。"""
        self._coasting = {"designation_id": int(designation_id), "steps": 0}

    def designate(self, box_norm: Sequence[float], k: int, level2_runner: Level2Runner | None) -> Designation:
        """`designate(box, k)` 兼容外壳（只供 `tools/eng_acq/e1.py`；会话不调用，C5）：取号 → 纯解析 →
        BOUND/BOUND_COASTING 时 `follow(j)`（及 coasting）→ 记录；结果与修改前逐字一致。"""
        designation_id = self.allocate_designation_id()
        designation = self.resolve_designation(box_norm, k, level2_runner, designation_id)
        if designation.result in (BOUND, BOUND_COASTING):
            assert designation.track_id is not None
            self.follow(designation.track_id)
            if designation.result == BOUND_COASTING:
                self.begin_coasting(designation_id)
        return self._finish(designation)

    # --- AR1-3 绑定事务快照（只供 `controller/target_manager.py` 的提交事务；不是第二写指针入口）---------

    def snapshot_binding_state(self) -> dict[str, Any]:
        return _deep_copy(
            {
                "pointer": self._pointer,
                "coasting": self._coasting,
                "designation": self.designation,
                "next_designation_id": self._next_designation_id,
                "ended_ids": sorted(self._ended_ids),
                "events": list(self._events),
            }
        )

    def restore_binding_state(self, snapshot: Mapping[str, Any]) -> None:
        state = _deep_copy(dict(snapshot))
        self._pointer = state["pointer"]
        self._coasting = state["coasting"]
        self.designation = state["designation"]
        self._next_designation_id = int(state["next_designation_id"])
        self._ended_ids = set(int(v) for v in state["ended_ids"])
        self._events = list(state["events"])

    def binding_state_matches(self, snapshot: Mapping[str, Any]) -> bool:
        return self.snapshot_binding_state() == _deep_copy(dict(snapshot))

    @property
    def ended_ids(self) -> frozenset[int]:
        return frozenset(self._ended_ids)

    @property
    def coasting(self) -> Mapping[str, Any] | None:
        return None if self._coasting is None else dict(self._coasting)

    def _level2(
        self,
        designation_id: int,
        box: list[float],
        k: int,
        head: int,
        entry_h: HistoryEntry,
        level1: Mapping[str, Any],
        runner: Level2Runner | None,
    ) -> Designation:
        events: list[dict[str, Any]] = [{"event": "L2_STARTED", "designation_id": designation_id, "k": k, "h": head}]
        level2: dict[str, Any] = {"attempted": True, "reason": None, "replayed_frames": 0, "elapsed_ms": 0.0}
        if runner is None:
            raise ProtocolMisuse("designate requires a level-2 runner (§3.4.1)")
        if head - k > self.config.l_replay_frames:
            level2.update(attempted=False, reason="source_too_old")
            events.append({"event": "L2_FAILED", "designation_id": designation_id, "reason": "source_too_old", "replayed_frames": 0, "elapsed_ms": 0.0})
            return Designation(designation_id, NO_TRACK_AT_K, k, head, None, None, level1, level2, (), tuple(events))
        replay = runner(k, box, head)
        mapped, reason, diagnostic = level2_mapping(replay)
        level2.update(replayed_frames=int(replay.replay_count), elapsed_ms=round(float(replay.elapsed_ms), 3), **diagnostic)
        if mapped != "READY":
            level2["reason"] = reason
            if reason == "not_attempted_frame_missing":
                level2["attempted"] = False
            events.append({"event": "L2_FAILED", "designation_id": designation_id, "reason": reason, "replayed_frames": level2["replayed_frames"], "elapsed_ms": level2["elapsed_ms"]})
            return Designation(designation_id, NO_TRACK_AT_K, k, head, None, None, level1, level2, (), tuple(events))
        sot_box = replay.last_result.box_norm if replay.last_result is not None else None
        # SOT 实例到此丢弃：框只用于本次同帧收养判定，不发布、不进历史或观测。
        if sot_box is None:
            level2["reason"] = f"sot_lost@{head}"
            events.append({"event": "L2_FAILED", "designation_id": designation_id, "reason": level2["reason"], "replayed_frames": level2["replayed_frames"], "elapsed_ms": level2["elapsed_ms"]})
            return Designation(designation_id, NO_TRACK_AT_K, k, head, None, None, level1, level2, (), tuple(events))
        kind, j, candidates, info = select_track(sot_box, entry_h.rows(TRACKED), self.config.tau, self.config.margin)
        level2["adoption"] = info
        if kind == "one":
            assert j is not None
            # C5：纯解析不动指针；BOUND 的 `follow(j)` 由提交事务（或 e1 兼容外壳 `designate`）执行。
            level2["adopted_track_id"] = j
            events.append({"event": "L2_ADOPTED", "designation_id": designation_id, "track_id": j})
            return Designation(designation_id, BOUND, k, head, 2, j, level1, level2, (), tuple(events))
        if kind == "ambiguous":
            events.append({"event": "L2_AMBIGUOUS", "designation_id": designation_id, "candidates": list(candidates)})
            return Designation(designation_id, AMBIGUOUS, k, head, 2, None, level1, level2, candidates, tuple(events))
        level2["reason"] = "no_adoption"
        events.append({"event": "L2_FAILED", "designation_id": designation_id, "reason": "no_adoption", "replayed_frames": level2["replayed_frames"], "elapsed_ms": level2["elapsed_ms"]})
        return Designation(designation_id, NO_TRACK_AT_K, k, head, None, None, level1, level2, (), tuple(events))

    def _finish(self, designation: Designation) -> Designation:
        _validated(designation)
        self.designation = designation
        self._events.extend(dict(event) for event in designation.events)
        return designation


def _deep_copy(value: Any) -> Any:
    """纯标准库深复制（本模块导入闭集不含 `copy`）：容器逐层复制，不可变值与冻结数据类原样共享。"""
    if isinstance(value, dict):
        return {key: _deep_copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_deep_copy(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_deep_copy(item) for item in value)
    if isinstance(value, set):
        return {_deep_copy(item) for item in value}
    return value


def _validated(designation: Designation) -> Designation:
    if designation.result not in RESULTS:
        raise AssertionError(f"designate produced {designation.result!r} outside the closed set")
    if designation.level2 is not None and designation.level2.get("reason") is not None:
        if not is_level2_reason(designation.level2["reason"]):
            raise AssertionError(f"level2.reason {designation.level2['reason']!r} outside the closed set")
    return designation


@dataclass(frozen=True)
class FrameTracks:
    """`step` 的返回：该帧全部行（`tracked` 取库输出，`lost` 取 KF 预测框）。"""

    frame_id: int
    library_frame_id: int
    rows: tuple[TrackRow, ...]
    removed_ids: tuple[int, ...] = field(default_factory=tuple)


def rows_from_library(
    output_rows: Sequence[Sequence[float]],
    lost_tracks: Sequence[Any],
    width: int,
    height: int,
    *,
    dropped: list[int] | None = None,
) -> tuple[list[TrackRow], list[TrackRow]]:
    """库输出行 `[x1,y1,x2,y2,track_id,score,cls,idx]` 与 `lost_stracks`（`.xyxy`/`.track_id`/`.score`/`.cls`）
    → 归一化 `TrackRow`（插件 `step` 与线束共用，同一实现）。tracked 框按画幅裁剪，`idx` 记为 `matched_det_index`。

    P1-ENG-CAPTURE-001 C3：出画或退化的 lost 框**不再丢弃**，改存未裁剪归一化框并带 `out_of_frame`
    （指针此时判 UNMATCHED）；只有非有限框仍丢弃，其 ID 追加进 `dropped`（`silently_dropped_ids`）。"""
    tracked: list[TrackRow] = []
    for row in output_rows:
        box = _norm_box(row[0], row[1], row[2], row[3], width, height)
        if box is None:
            if dropped is not None:
                dropped.append(int(row[4]))
            continue
        index = -1
        if len(row) > 7:
            try:
                value = float(row[7])
                index = int(value) if math.isfinite(value) else -1
            except (TypeError, ValueError):
                index = -1
        tracked.append(TrackRow(int(row[4]), box, float(row[5]), int(row[6]), TRACKED, matched_det_index=index))
    lost: list[TrackRow] = []
    for track in lost_tracks:
        x1, y1, x2, y2 = (float(v) for v in track.xyxy)
        box = _norm_box(x1, y1, x2, y2, width, height)
        if box is not None:
            lost.append(TrackRow(int(track.track_id), box, float(track.score), int(track.cls), LOST))
            continue
        raw = _raw_norm_box(x1, y1, x2, y2, width, height)
        if raw is None:
            if dropped is not None:
                dropped.append(int(track.track_id))
            continue
        lost.append(TrackRow(int(track.track_id), raw, float(track.score), int(track.cls), LOST, out_of_frame=True))
    return tracked, lost


def _raw_norm_box(x1: float, y1: float, x2: float, y2: float, width: int, height: int) -> tuple[float, float, float, float] | None:
    """未裁剪归一化 xywh（出画/退化 lost 框保留用）；非有限 → None。"""
    values = [float(v) for v in (x1, y1, x2, y2)]
    if not all(math.isfinite(v) for v in values):
        return None
    return tuple(round(v, 9) for v in (values[0] / width, values[1] / height, (values[2] - values[0]) / width, (values[3] - values[1]) / height))  # type: ignore[return-value]


def _norm_box(x1: float, y1: float, x2: float, y2: float, width: int, height: int) -> tuple[float, float, float, float] | None:
    values = [float(v) for v in (x1, y1, x2, y2)]
    if not all(math.isfinite(v) for v in values):
        return None
    clipped = clip_box_norm((values[0] / width, values[1] / height, (values[2] - values[0]) / width, (values[3] - values[1]) / height))
    if clipped is None:
        return None
    return tuple(round(v, 9) for v in clipped)  # type: ignore[return-value]


# --- P1-ENG-FASTFIX-001 §3.3（G2；K3）：库 KF 完整状态的只读深复制 ---------------------------------------

#: 完整状态的布局闭集：BoT-SORT `BOTrack` = xywh（冻结规格 `botsort`）；ByteTrack `STrack` 的 xyah 不在本项路径，
#: 读到即判无效（不做单位换算、不冒充 xywh）。
FULL_KF_LAYOUTS: tuple[str, ...] = ("xywh",)
FULL_KF_DIM = 8


@dataclass(frozen=True)
class FullKfState:
    """一条库轨迹在某传感器帧的 **完整** KF 状态（8 维均值、8×8 协方差）的只读深复制（不回写库）。

    单位：检测输入画幅像素（均值前 4 维 xc, yc, w, h）、像素/帧（后 4 维速度）；协方差同单位平方。
    `phase` 取 `KF_PHASES`（本帧发生量测更新者 posterior，否则 prior）。`valid=False` 时 `invalid_reason` 非空，
    消费方一律 fail-closed（提示 `hint_invalid`）。`KfSnapshot` 只存位置块，无法恢复完整协方差，故另立本记录。"""

    sensor_frame_id: int
    library_frame_id: int
    track_key: int
    phase: str
    layout: str
    mean: tuple[float, ...]
    covariance: tuple[tuple[float, ...], ...]
    valid: bool = True
    invalid_reason: str | None = None

    def as_record(self) -> dict[str, Any]:
        return {
            "sensor_frame_id": self.sensor_frame_id,
            "library_frame_id": self.library_frame_id,
            "track_key": self.track_key,
            "phase": self.phase,
            "layout": self.layout,
            "mean": [_finite_or_none(v) for v in self.mean],
            "covariance": [[_finite_or_none(v) for v in row] for row in self.covariance],
            "valid": self.valid,
            "invalid_reason": self.invalid_reason,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "FullKfState":
        mean = record.get("mean")
        covariance = record.get("covariance")
        return make_full_kf_state(
            int(record["sensor_frame_id"]),
            int(record["library_frame_id"]),
            int(record["track_key"]),
            str(record["phase"]),
            str(record.get("layout")),
            [math.nan if v is None else v for v in mean] if isinstance(mean, Sequence) else None,
            [[math.nan if v is None else v for v in row] for row in covariance]
            if isinstance(covariance, Sequence) and all(isinstance(row, Sequence) for row in covariance) else None,
            forced_invalid=None if record.get("valid", True) else (record.get("invalid_reason") or "kf_invalid"),
        )


def full_state_problem(mean: Sequence[float], covariance: Sequence[Sequence[float]]) -> str | None:
    """完整状态有效性：任一分量非有限、w/h ≤ 0、协方差非对称或非半正定（LDLᵀ 主元 < −容差）→ 原因；否则 None。"""
    values = [*mean, *(v for row in covariance for v in row)]
    if not all(math.isfinite(float(v)) for v in values):
        return "kf_non_finite"
    if float(mean[2]) <= 0.0 or float(mean[3]) <= 0.0:
        return "kf_non_positive_size"
    n = len(mean)
    scale = max(1.0, max(abs(float(covariance[i][i])) for i in range(n)))
    for i in range(n):
        for j in range(i + 1, n):
            a, b = float(covariance[i][j]), float(covariance[j][i])
            if abs(a - b) > 1e-9 * max(1.0, abs(a), abs(b)):
                return "kf_cov_asymmetric"
    # 半正定：无主元交换的 LDLᵀ；主元 < −tol 即非半正定，|主元| ≤ tol 视为零列（半正定边界）。
    tol = 1e-9 * scale
    lower = [[0.0] * n for _ in range(n)]
    pivots = [0.0] * n
    for j in range(n):
        value = float(covariance[j][j]) - sum(lower[j][k] * lower[j][k] * pivots[k] for k in range(j))
        if value < -tol:
            return "kf_cov_not_psd"
        pivots[j] = value
        for i in range(j + 1, n):
            off = float(covariance[i][j]) - sum(lower[i][k] * lower[j][k] * pivots[k] for k in range(j))
            if abs(value) <= tol:
                if abs(off) > 1e-6 * scale:
                    return "kf_cov_not_psd"
                lower[i][j] = 0.0
            else:
                lower[i][j] = off / value
    return None


def make_full_kf_state(
    sensor_frame_id: int,
    library_frame_id: int,
    track_key: int,
    phase: str,
    layout: str,
    mean: Any,
    covariance: Any,
    *,
    forced_invalid: str | None = None,
) -> FullKfState:
    """构造并校验完整状态（纯标准库）；读不出/维数不符 → `kf_unreadable`，布局不在闭集 → `kf_layout_unsupported`。"""
    if phase not in KF_PHASES:
        raise ValueError(f"kf phase {phase!r} outside {KF_PHASES}")
    values = _float_tuple(mean, FULL_KF_DIM)
    rows = (
        tuple(_float_tuple(row, FULL_KF_DIM) for row in covariance)
        if isinstance(covariance, Sequence) and not isinstance(covariance, (str, bytes)) and len(covariance) == FULL_KF_DIM
        else None
    )
    reason = forced_invalid
    if reason is None and layout not in FULL_KF_LAYOUTS:
        reason = "kf_layout_unsupported"
    if reason is None and (values is None or rows is None or any(row is None for row in rows)):
        reason = "kf_unreadable"
    if reason is None:
        reason = full_state_problem(values, rows)  # type: ignore[arg-type]
    zero_mean = (0.0,) * FULL_KF_DIM
    zero_cov = tuple((0.0,) * FULL_KF_DIM for _ in range(FULL_KF_DIM))
    good_rows = rows is not None and all(row is not None for row in rows)
    return FullKfState(
        int(sensor_frame_id),
        int(library_frame_id),
        int(track_key),
        phase,
        str(layout),
        tuple(values) if values is not None else zero_mean,
        tuple(tuple(row) for row in rows) if good_rows else zero_cov,  # type: ignore[union-attr, arg-type]
        reason is None,
        reason,
    )


def full_kf_state_of_track(track: Any, *, sensor_frame_id: int, library_frame_id: int) -> FullKfState | None:
    """库轨迹对象 → 完整状态深复制（只读 `mean`/`covariance`/`frame_id`/`track_id`，不回写）；无 KF → None。

    phase：轨迹 `frame_id` = 库当前帧（本帧量测更新）→ posterior，否则 prior（与 `_post_snapshots` 同一判据）。"""
    mean = getattr(track, "mean", None)
    covariance = getattr(track, "covariance", None)
    if mean is None or covariance is None:
        return None
    phase = KF_POSTERIOR if getattr(track, "frame_id", None) == library_frame_id else KF_PRIOR
    layout = "xywh" if hasattr(track, "tlwh_to_xywh") else "xyah"
    try:
        copied_mean = [float(v) for v in mean]
        copied_cov = [[float(v) for v in row] for row in covariance]
        key = int(track.track_id)
    except (TypeError, ValueError, AttributeError):
        return make_full_kf_state(sensor_frame_id, library_frame_id, int(getattr(track, "track_id", -1)), phase, layout,
                                  None, None, forced_invalid="kf_unreadable")
    return make_full_kf_state(sensor_frame_id, library_frame_id, key, phase, layout, copied_mean, copied_cov)


def full_kf_state_from_associator(
    associator: Any, track_key: int, *, sensor_frame_id: int, library_frame_id: int
) -> FullKfState | None:
    """在常驻关联器的 `tracked_stracks`/`lost_stracks` 中按键找轨迹并深复制完整状态（只读）；找不到 → None。"""
    if associator is None:
        return None
    for track in [*getattr(associator, "tracked_stracks", []), *getattr(associator, "lost_stracks", [])]:
        if int(getattr(track, "track_id", -1)) == int(track_key):
            return full_kf_state_of_track(track, sensor_frame_id=sensor_frame_id, library_frame_id=library_frame_id)
    return None


def library_kf_predictor(associator: Any, track_key: int) -> Any:
    """该键库轨迹所用的 KF 对象（钉版库同类、同常数；`kalman_filter` 或类属性 `shared_kalman`）；找不到 → None。"""
    if associator is None:
        return None
    for track in [*getattr(associator, "tracked_stracks", []), *getattr(associator, "lost_stracks", [])]:
        if int(getattr(track, "track_id", -1)) == int(track_key):
            return getattr(track, "kalman_filter", None) or getattr(type(track), "shared_kalman", None)
    return None
