"""E1 陈旧指定解析成功率随延迟（§3.9，AC-7/AC-20 及修订 1；AR2-2 接受处置）。

样本 (k, o)：k 为序列帧、o 为 k 帧 OK 可见对象（静止车 `vehicles[]`、红车 `dynamic`）；指定框：干净臂 = o 在 k 帧
真值框；扰动臂 `c2_quantiles` = 真值框随机缩放 + 平移（固定种子），实现 IoU 的 p10/p25/p50 与 C2 347 行分位数之差
≤ 0.05（只取提案事实 14 的三个统计量，不读逐帧 C2 预测文件、不回放 H 帧）。

延迟 Δ ∈ {1, 2, 4.2, 5.4, 8, 13} s；解析帧 r = 同段内首个 t ≥ t_k + Δ 的帧；解析 = 常驻核心记录到 h = r 时调
`ResidentCore.designate(box, k)`（三级全走；第二级在数据根 JPEG 上以冻结 `nanotrack-v2` 从 k 起跟回放到 r）。
每个 (k, o, Δ) 落入且仅落入 15 桶之一；守恒式逐层逐 Δ 断言。

第二级代价与 AR2-2（现行上限 = 提案决策记录「信封修订 SUB:1/SUB:2 落实（2026-09-29；CLARIFY）」，AC-7/AC-20 修订 2）：
a7 的第二级触发 (k, o) 全样本运行；其他序列每（序列 × gmc_source × 臂）第一级无轨迹过门的 (k, o)（= 第二级触发集，
与 Δ 无关）> 600 时按固定种子分层（对象类 × 尺寸）等比抽 600（`LEVEL2_SUBSAMPLED`）；未抽中的 (k, o) 在有解析帧的 Δ 上
**不运行解析**，不入 15 桶、不计 `NO_TRACK_AT_K`/成功，计入 `not_run_ar2_2`，受影响层记 `NOT_EVALUABLE_AR2-2`。SOT 回放
每 (k, o) 至多 `frame_cap(序列)` 帧（信封修订 SUB:3，AC-7/AC-20 修订 3：scout-1 ≤ 87，a7、m3-armA ≤ 66）：需要更多帧的
(k, o, Δ) 同样不运行，计 `not_run_frame_cap`，层记 `NOT_EVALUABLE_FRAME_CAP`。
第二级 SOT 结果按 (段, k, 框) 在同一进程内跨 gmc_source 复用（结果只取决于 k 帧框与帧图像，与关联器无关）。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import hashlib
import math
import random
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

from controller.reanchor import ReplayResult, valid_replay_box
from controller.resident_core import (
    AMBIGUOUS,
    BOUND,
    BOUND_COASTING,
    FRAME_NOT_IN_HISTORY,
    LEVEL2_FIXED_REASONS,
    NO_TRACK_AT_K,
    TRACK_ENDED,
    TRACKED,
    ResidentCore,
    ResolverConfig,
    box_iou,
    select_track,
)
from controller.trackers import TrackerPlugin, TrackerResult, clip_box_norm
from tools.eng_acq.data import RED_ID, Frame, size_bin

DELTAS_S: tuple[float, ...] = (1.0, 2.0, 4.2, 5.4, 8.0, 13.0)
ARMS: tuple[str, ...] = ("none", "c2_quantiles")
CLASSES: tuple[str, ...] = ("static", "red")
SIZES: tuple[str, ...] = ("S", "M", "L")
CORRECT_IOU = 0.3
LEVEL2_CAP = 600
#: 信封修订 SUB:1（2026-09-29）：这些序列的第二级触发 (k, o) 全样本运行，不受 LEVEL2_CAP 约束。
LEVEL2_FULL_SAMPLE_SEQUENCES: tuple[str, ...] = ("a7",)
#: 信封修订 SUB:2（2026-09-29）：每 (k, o) SOT 回放 ≤ 66 帧（原 65）；SUB:3 起为未单列序列的缺省值（a7、m3-armA）。
FRAME_CAP = 66
#: 信封修订 SUB:3（2026-09-29；AC-7/AC-20 修订 3）：按序列取值的每 (k, o) SOT 回放帧上限，优先于 FRAME_CAP。
FRAME_CAP_BY_SEQUENCE: dict[str, int] = {"scout-1": 87}
SUBSAMPLE_SEED = 20260928
PERTURB_SEED = 20260929

BUCKETS: tuple[str, ...] = (
    "NO_RESOLVE_FRAME",
    "BOUND_V_CORRECT",
    "BOUND_V_WRONG",
    "BOUND_INVISIBLE",
    "COASTING_V_CORRECT",
    "COASTING_V_WRONG",
    "COASTING_INVISIBLE",
    "ENDED_V",
    "ENDED_INVISIBLE",
    "NOTRACK_V",
    "NOTRACK_INVISIBLE",
    "AMBIG_V",
    "AMBIG_INVISIBLE",
    "OUTHIST_V",
    "OUTHIST_INVISIBLE",
)
VISIBLE_BUCKETS = ("BOUND_V_CORRECT", "BOUND_V_WRONG", "COASTING_V_CORRECT", "COASTING_V_WRONG", "ENDED_V", "NOTRACK_V", "AMBIG_V", "OUTHIST_V")

#: C2 347 行（金标与预测均 unique）IoU 分位数：提案 §0 事实 14 / §8（构思会话只读复算），本线束只取这三个统计量。
C2_QUANTILES: dict[str, float] = {"p10": 0.358, "p25": 0.743, "p50": 0.862}
C2_SOURCE = "docs/proposals/P1-ENG-ACQ-001-pointer-fast-layer-target-switch-acquisition.md §0 事实 14 / §8（347 行；中位 0.862、p25 0.743、p10 0.358、≥0.5 占 0.870、≥0.3 占 0.905）"
#: 目标 IoU 的分段线性逆 CDF 结点（经 347 行统计量：p9.5≈0.30（≥0.3 占 0.905）、p13≈0.50（≥0.5 占 0.870））。
PERTURB_KNOTS: tuple[tuple[float, float], ...] = (
    (0.0, 0.05),
    (0.095, 0.30),
    (0.10, 0.358),
    (0.13, 0.50),
    (0.25, 0.743),
    (0.50, 0.862),
    (1.0, 0.98),
)
QUANTILE_TOLERANCE = 0.05


def classify(r_exists: bool, result: str | None, visible_r: bool, iou_r: float | None) -> str:
    """(k, o, Δ) → 15 桶之一（互斥且穷尽；表 §3.9）。"""
    if not r_exists:
        return "NO_RESOLVE_FRAME"
    suffix = "V" if visible_r else "INVISIBLE"
    if result == BOUND:
        if not visible_r:
            return "BOUND_INVISIBLE"
        return "BOUND_V_CORRECT" if (iou_r or 0.0) >= CORRECT_IOU else "BOUND_V_WRONG"
    if result == BOUND_COASTING:
        if not visible_r:
            return "COASTING_INVISIBLE"
        return "COASTING_V_CORRECT" if (iou_r or 0.0) >= CORRECT_IOU else "COASTING_V_WRONG"
    if result == TRACK_ENDED:
        return f"ENDED_{suffix}"
    if result == NO_TRACK_AT_K:
        return f"NOTRACK_{suffix}"
    if result == AMBIGUOUS:
        return f"AMBIG_{suffix}"
    if result == FRAME_NOT_IN_HISTORY:
        return f"OUTHIST_{suffix}"
    raise ValueError(f"result {result!r} outside the closed set")


def ratios(counts: Mapping[str, int], n_res: int, n_vis: int, n_inv: int, adopted: int) -> dict[str, float | None]:
    def div(a: int, b: int) -> float | None:
        return round(a / b, 6) if b else None

    return {
        "resolve_ok": div(counts["BOUND_V_CORRECT"] + counts["COASTING_V_CORRECT"], n_vis),
        "false_lock": div(counts["BOUND_V_WRONG"] + counts["BOUND_INVISIBLE"] + counts["COASTING_V_WRONG"], n_res),
        "report_ok_invisible": div(
            counts["COASTING_INVISIBLE"] + counts["ENDED_INVISIBLE"] + counts["NOTRACK_INVISIBLE"] + counts["AMBIG_INVISIBLE"] + counts["OUTHIST_INVISIBLE"],
            n_inv,
        ),
        "explicit_unbound_visible": div(counts["ENDED_V"] + counts["NOTRACK_V"] + counts["AMBIG_V"] + counts["OUTHIST_V"], n_vis),
        "level2_share": div(adopted, counts["BOUND_V_CORRECT"]),
    }


# --- 扰动臂 -------------------------------------------------------------------


def _inverse_cdf(u: float) -> float:
    for (u0, v0), (u1, v1) in zip(PERTURB_KNOTS, PERTURB_KNOTS[1:]):
        if u <= u1:
            return v0 + (v1 - v0) * (u - u0) / (u1 - u0)
    return PERTURB_KNOTS[-1][1]


def _sample_rng(key: str) -> random.Random:
    digest = hashlib.sha256(f"{PERTURB_SEED}|{key}".encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def perturb_box(box: Sequence[float], key: str) -> tuple[float, float, float, float]:
    """固定种子：目标 IoU ~ 逆 CDF；缩放 s ∈ [1/s', s']（s' = min(1.15, 1/√IoU)），沿随机方向平移至达到目标 IoU；
    结果裁剪到画幅（VLM 框在画内）。裁剪退化时退回真值框（计入实现分布）。"""
    rng = _sample_rng(key)
    target = _inverse_cdf(rng.random())
    x, y, w, h = (float(v) for v in box)
    cx, cy = x + w / 2, y + h / 2
    s_max = min(1.15, 1.0 / math.sqrt(max(target, 1e-6)))
    scale = math.exp(rng.uniform(-math.log(s_max), math.log(s_max)))
    sx = scale * math.exp(rng.uniform(-0.05, 0.05))
    sy = scale / math.exp(rng.uniform(-0.05, 0.05))
    nw, nh = w * sx, h * sy
    angle = rng.uniform(0.0, 2 * math.pi)
    dx, dy = math.cos(angle), math.sin(angle)

    def at(t: float) -> tuple[float, float, float, float]:
        return (cx + dx * t * w - nw / 2, cy + dy * t * h - nh / 2, nw, nh)

    if box_iou(at(0.0), box) <= target:
        candidate = at(0.0)
    else:
        lo, hi = 0.0, 3.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if box_iou(at(mid), box) > target:
                lo = mid
            else:
                hi = mid
        candidate = at((lo + hi) / 2)
    clipped = clip_box_norm(candidate)
    if clipped is None or not valid_replay_box(clipped):
        return tuple(clip_box_norm(box) or box)  # type: ignore[return-value]
    return clipped


def realized_quantiles(values: Sequence[float]) -> dict[str, float]:
    ordered = sorted(values)

    def q(p: float) -> float:
        if not ordered:
            return float("nan")
        position = p * (len(ordered) - 1)
        lower = math.floor(position)
        upper = min(len(ordered) - 1, lower + 1)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

    return {"p10": round(q(0.10), 6), "p25": round(q(0.25), 6), "p50": round(q(0.50), 6)}


# --- 第二级：前缀共享的 SOT 回放（与 `replay_tracker` 逐事件等价）-----------------------


@dataclass
class PrefixRun:
    """从 k 起跟一次、逐帧推进到 `last` 的结果；`result_at(h)` 合成 `replay_tracker(k→h)` 的同一 `ReplayResult`。"""

    source_frame_id: int
    terminal_event: str | None = None  # 起跟前即终止：RESEED_FAILED / RESEED_DISCARDED_INVALID_BOX
    terminal_reason: str | None = None
    init_elapsed_ms: float = 0.0
    steps: list[tuple[int, float, TrackerResult | None, float, str | None]] = field(default_factory=list)
    # 每步：(frame_id, 处理该帧前已用秒, 更新结果, 处理后已用毫秒, 异常类名)
    last_frame: int = 0
    frames_computed: int = 0


class PrefixSot:
    """`replay_tracker` 的前缀共享实现：同一 (段, k, 框) 只起跟一次，各 Δ 共用前缀（§3.9「各 Δ 共用前缀」）。"""

    def __init__(
        self,
        frames: Sequence[Frame],
        sot_factory: Callable[[], TrackerPlugin],
        image_of: Callable[[Frame], Any],
        *,
        t_replay_s: float,
        maximum_source_age_s: float,
        frame_cap: int = FRAME_CAP,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        self.frames = {f.frame_id: f for f in frames}
        self.sot_factory = sot_factory
        self.image_of = image_of
        self.t_replay_s = t_replay_s
        self.maximum_source_age_s = maximum_source_age_s
        self.frame_cap = frame_cap
        self.monotonic = monotonic
        self.cache: dict[tuple[int, tuple[float, ...]], PrefixRun] = {}
        self.sot_runs = 0
        self.sot_frames = 0

    def run(self, k: int, box: Sequence[float], last: int) -> PrefixRun:
        key = (int(k), tuple(round(float(v), 12) for v in box))
        run = self.cache.get(key)
        if run is None:
            run = PrefixRun(int(k))
            self.cache[key] = run
            self._start(run, box)
            # 一次推进到 min(k + frame_cap, 段末) 后释放 SOT 实例（各 Δ 共用前缀；不驻留模型实例）。
            self._advance(run, min(int(k) + self.frame_cap, max(self.frames)))
            if hasattr(run, "tracker"):
                del run.tracker  # type: ignore[attr-defined]
        return run

    def _start(self, run: PrefixRun, box: Sequence[float]) -> None:
        self._started = self.monotonic()
        run.started = self._started  # type: ignore[attr-defined]
        source = self.frames[run.source_frame_id]
        try:
            tracker = self.sot_factory()
            if not valid_replay_box(box):
                run.terminal_event, run.terminal_reason = "RESEED_DISCARDED_INVALID_BOX", "invalid_source_box"
                return
            self.sot_runs += 1
            if not tracker.init(self.image_of(source), list(box)):
                run.terminal_event, run.terminal_reason = "RESEED_FAILED", "tracker_init_failed"
                return
        except Exception as error:  # noqa: BLE001 — 与 replay_tracker 同：非 init 异常 → RESEED_FAILED
            run.terminal_event, run.terminal_reason = "RESEED_FAILED", type(error).__name__
            return
        run.tracker = tracker  # type: ignore[attr-defined]
        run.last_frame = run.source_frame_id
        run.init_elapsed_ms = (self.monotonic() - run.started) * 1000.0  # type: ignore[attr-defined]

    def _advance(self, run: PrefixRun, last: int) -> None:
        tracker = getattr(run, "tracker", None)
        if tracker is None:
            return
        while run.last_frame < last:
            if run.steps and (run.steps[-1][4] is not None or not _step_ok(run.steps[-1][2])):
                return  # 前缀已终止（异常或 SOT 丢失）
            frame_id = run.last_frame + 1
            frame = self.frames.get(frame_id)
            if frame is None:
                return  # 中间帧缺失：result_at 按 MISSING 处理
            if frame_id - run.source_frame_id > self.frame_cap:
                return
            before = self.monotonic() - run.started  # type: ignore[attr-defined]
            try:
                result = tracker.update(self.image_of(frame))
                error = None
            except Exception as exception:  # noqa: BLE001
                result, error = None, type(exception).__name__
            after_ms = (self.monotonic() - run.started) * 1000.0  # type: ignore[attr-defined]
            run.steps.append((frame_id, before, result, after_ms, error))
            run.last_frame = frame_id
            run.frames_computed += 1
            self.sot_frames += 1

    def result_at(self, k: int, box: Sequence[float], h: int) -> ReplayResult:
        """与 `controller.reanchor.replay_tracker(k→h)` 相同的事件、原因、计数与末结果。"""
        k, h = int(k), int(h)
        source = self.frames.get(k)
        head = self.frames.get(h)
        if source is None:
            return ReplayResult("RESEED_DISCARDED_MISSING_FRAME", None, k, None, 0, 0.0, None, "source_frame_missing")
        if head is None:
            return ReplayResult("RESEED_DISCARDED_MISSING_FRAME", None, k, None, 0, 0.0, None, "target_frame_missing")
        if head.sim_t - source.sim_t > self.maximum_source_age_s:
            return ReplayResult("RESEED_DISCARDED_STALE", None, k, None, 0, 0.0, None, "source_result_too_old")
        if h - k > self.frame_cap:
            raise FrameCapExceeded(h - k)
        run = self.run(k, box, h)
        if run.terminal_event is not None:
            return ReplayResult(run.terminal_event, None, k, None, 0, run.init_elapsed_ms, None, run.terminal_reason)
        if any(frame_id not in self.frames for frame_id in range(k + 1, h + 1)):
            return ReplayResult("RESEED_DISCARDED_MISSING_FRAME", None, k, None, 0, 0.0, None, "intermediate_frame_missing")
        last_result: TrackerResult | None = TrackerResult(clip_box_norm(box), True, 1.0, "placeholder")
        count = 0
        elapsed_ms = run.init_elapsed_ms
        for frame_id, before, result, after_ms, error in run.steps:
            if frame_id > h:
                break
            if before > self.t_replay_s:
                return ReplayResult("RESEED_DISCARDED_NOT_CONVERGED", None, k, frame_id - 1, count, before * 1000.0, last_result, "catchup_timeout")
            if error is not None:
                return ReplayResult("RESEED_FAILED", None, k, None, 0, after_ms, None, error)
            last_result = result
            count += 1
            elapsed_ms = after_ms
            if not _step_ok(result):
                return ReplayResult("RESEED_DISCARDED_INVALID_BOX", None, k, frame_id, count, after_ms, last_result, "invalid_replay_box")
        if count != h - k:
            raise AssertionError(f"prefix for k={k} did not reach h={h}")
        return ReplayResult("RESEED_READY", None, k, h, count, elapsed_ms, last_result)


class FrameCapExceeded(RuntimeError):
    """第二级需要超过该序列 `frame_cap` 帧的回放（信封 SUB:3：scout-1 ≤ 87，其他 ≤ 66）：不运行。"""


def _step_ok(result: TrackerResult | None) -> bool:
    return result is not None and bool(result.ok) and valid_replay_box(result.box_norm)


# --- 样本与主循环 ----------------------------------------------------------------


@dataclass(frozen=True)
class Sample:
    segment_index: int
    k: int
    k_index: int
    object_id: str
    cls: str
    size: str
    box: tuple[float, float, float, float]
    truth_box: tuple[float, float, float, float]


def build_samples(sequence: str, segments: Sequence[Sequence[Frame]], arm: str) -> tuple[list[Sample], list[float]]:
    samples: list[Sample] = []
    realized: list[float] = []
    for segment_index, frames in enumerate(segments):
        for k_index, frame in enumerate(frames):
            for object_id, truth in sorted(frame.objects().items()):
                cls = "red" if object_id == RED_ID else "static"
                if arm == "none":
                    box = tuple(float(v) for v in truth)
                elif arm == "c2_quantiles":
                    box = perturb_box(truth, f"{sequence}|{frame.path}|{object_id}")
                    realized.append(box_iou(box, truth))
                else:
                    raise ValueError(f"arm {arm!r} not executed (uniform is not selected; §7 (i))")
                samples.append(Sample(segment_index, frame.frame_id, k_index, object_id, cls, size_bin(truth), box, tuple(truth)))  # type: ignore[arg-type]
    return samples, realized


def resolve_frame_index(frames: Sequence[Frame], k_index: int, delta: float) -> int | None:
    target = frames[k_index].sim_t + delta
    for index in range(k_index + 1, len(frames)):
        if frames[index].sim_t >= target - 1e-9:
            return index
    return None


def frame_cap(sequence: str) -> int:
    """该序列每 (k, o) 第二级 SOT 回放帧上限（SUB:3：scout-1 87；其他 66）。"""
    return FRAME_CAP_BY_SEQUENCE.get(sequence, FRAME_CAP)


def level2_cap(sequence: str) -> int | None:
    """该序列每（gmc_source × 臂）第二级 (k, o) 上限；`None` = 全样本（SUB:1，a7）。"""
    return None if sequence in LEVEL2_FULL_SAMPLE_SEQUENCES else LEVEL2_CAP


def subsample(triggered: Sequence[Sample], cap: int | None = LEVEL2_CAP, seed: int = SUBSAMPLE_SEED) -> tuple[set[Sample], bool]:
    """> cap 时按（对象类 × 尺寸）等比（最大余数法）抽取 cap 个，固定种子；`cap is None` = 全样本不抽。"""
    if cap is None or len(triggered) <= cap:
        return set(triggered), False
    strata: dict[tuple[str, str], list[Sample]] = defaultdict(list)
    for sample in triggered:
        strata[(sample.cls, sample.size)].append(sample)
    total = len(triggered)
    quotas = {key: cap * len(items) / total for key, items in strata.items()}
    allocation = {key: int(math.floor(q)) for key, q in quotas.items()}
    remainder = cap - sum(allocation.values())
    for key in sorted(quotas, key=lambda key: (-(quotas[key] - allocation[key]), key))[:remainder]:
        allocation[key] += 1
    rng = random.Random(seed)
    chosen: set[Sample] = set()
    for key in sorted(strata):
        items = sorted(strata[key], key=lambda s: (s.segment_index, s.k, s.object_id))
        chosen.update(rng.sample(items, allocation[key]))
    return chosen, True


def layer_key(sequence: str, sample: Sample, gmc: str, arm: str) -> tuple[str, str, str, str, str]:
    return (sequence, sample.cls, sample.size, gmc, arm)


def run_combo(
    sequence: str,
    segments: Sequence[Sequence[Frame]],
    records: Sequence[Sequence[Mapping[str, Any]]],
    samples: Sequence[Sample],
    gmc: str,
    arm: str,
    prefix_for_segment: Callable[[int], PrefixSot],
    rows_of: Callable[[Mapping[str, Any], str], Any],
    guard: Any = None,
) -> dict[str, Any]:
    """一个（序列 × gmc_source × 臂）：先按 k 帧历史定第二级触发集（AR2-2 抽样），再逐帧记录并在 r 帧解析。"""
    config = ResolverConfig()
    # 触发集：第一级在 history(k) 的 tracked 行上无轨迹过门（与 designate 同一 select_track）。
    triggered = []
    for sample in samples:
        record = records[sample.segment_index][sample.k_index]
        kind, _j, _c, _i = select_track(sample.box, rows_of(record, TRACKED), config.tau, config.margin)
        if kind == "none":
            triggered.append(sample)
    selected, subsampled = subsample(triggered, level2_cap(sequence))
    triggered_set = set(triggered)
    cap_frames = frame_cap(sequence)
    # 解析计划：r 帧索引 → [(sample, Δ)]
    plan: dict[tuple[int, int], list[tuple[Sample, float]]] = defaultdict(list)
    outcomes: dict[tuple[Sample, float], dict[str, Any]] = {}
    for sample in samples:
        frames = segments[sample.segment_index]
        for delta in DELTAS_S:
            r_index = resolve_frame_index(frames, sample.k_index, delta)
            if r_index is None:
                outcomes[(sample, delta)] = {"bucket": "NO_RESOLVE_FRAME"}
                continue
            if sample in triggered_set and sample not in selected:
                outcomes[(sample, delta)] = {"not_run": "ar2_2"}
                continue
            if sample in triggered_set and frames[r_index].frame_id - sample.k > cap_frames:
                outcomes[(sample, delta)] = {"not_run": "frame_cap"}
                continue
            plan[(sample.segment_index, r_index)].append((sample, delta))
    level2_calls: Counter = Counter()
    for segment_index, frames in enumerate(segments):
        core = ResidentCore(128, config)
        prefix = prefix_for_segment(segment_index)

        def runner(k: int, box: Sequence[float], h: int, _prefix: PrefixSot = prefix) -> ReplayResult:
            level2_calls["calls"] += 1
            return _prefix.result_at(k, box, h)

        for index, (frame, record) in enumerate(zip(frames, records[segment_index])):
            if guard is not None:
                guard.check()
            core.record(frame.frame_id, frame.metadata, rows_of(record, "tracked"), rows_of(record, "lost"), record["removed_ids"], record["library_frame_id"])
            for sample, delta in plan.get((segment_index, index), ()):
                expect_level2 = sample in triggered_set
                before_calls = level2_calls["calls"]
                designation = core.designate(sample.box, sample.k, runner)
                if (level2_calls["calls"] > before_calls) != expect_level2:
                    raise AssertionError("level-2 trigger pre-evaluation disagrees with designate")
                truth_r = frame.objects().get(sample.object_id)
                visible = truth_r is not None
                iou_r = None
                if designation.result in (BOUND, BOUND_COASTING) and visible and designation.track_id is not None:
                    row = core.history(frame.frame_id).row(designation.track_id)  # type: ignore[union-attr]
                    iou_r = box_iou(row.box_norm, truth_r) if row is not None else 0.0
                outcomes[(sample, delta)] = {
                    "bucket": classify(True, designation.result, visible, iou_r),
                    "level": designation.resolution_level,
                    "level2": None if designation.level2 is None else dict(designation.level2),
                }
                # 每个 (k, o, Δ) 是独立的一次指定：解析后撤指针，不让上一次指定的 coasting 记账影响下一次解析。
                core.follow(None)
    return {"outcomes": outcomes, "triggered": len(triggered), "selected": len(selected), "subsampled": subsampled, "level2_calls": level2_calls["calls"]}


def aggregate(sequence: str, tag: str, samples: Sequence[Sample], combo: Mapping[str, Any], gmc: str, arm: str) -> list[dict[str, Any]]:
    """每层每 Δ 一行：`N_all`/`N_res`/`N_vis`/`N_inv`、15 桶、level2 子表、比例与守恒断言；空层也出行。"""
    by_layer: dict[tuple[str, str], list[Sample]] = defaultdict(list)
    for sample in samples:
        by_layer[(sample.cls, sample.size)].append(sample)
    rows = []
    for cls in CLASSES:
        for size in SIZES:
            members = by_layer.get((cls, size), [])
            for delta in DELTAS_S:
                counts = Counter({name: 0 for name in BUCKETS})
                not_run: Counter = Counter()
                level2 = {"triggered": 0, "attempted": 0, "adopted": 0, "ambiguous": 0, "failed_by_reason": {}}
                failed: Counter = Counter()
                for sample in members:
                    outcome = combo["outcomes"][(sample, delta)]
                    if "not_run" in outcome:
                        not_run[outcome["not_run"]] += 1
                        continue
                    counts[outcome["bucket"]] += 1
                    info = outcome.get("level2")
                    if info is not None:
                        level2["triggered"] += 1
                        if info.get("attempted"):
                            level2["attempted"] += 1
                        reason = info.get("reason")
                        if reason is None and outcome.get("level") == 2 and outcome["bucket"].startswith("BOUND"):
                            level2["adopted"] += 1
                        elif reason is None and outcome.get("level") == 2:
                            level2["ambiguous"] += 1
                        elif reason is not None:
                            key = reason.split("@")[0] + "@<f>" if "@" in reason else reason
                            failed[key] += 1
                level2["failed_by_reason"] = {name: failed.get(name, 0) for name in (*LEVEL2_FIXED_REASONS, "sot_lost@<f>", "replay_timeout@<f>")}
                n_all = len(members)
                n_not_run = sum(not_run.values())
                n_res = n_all - counts["NO_RESOLVE_FRAME"] - n_not_run
                n_vis = sum(counts[name] for name in VISIBLE_BUCKETS)
                n_inv = n_res - n_vis
                if sum(counts.values()) + n_not_run != n_all or n_vis + n_inv + counts["NO_RESOLVE_FRAME"] + n_not_run != n_all:
                    raise AssertionError(f"conservation failed for {(sequence, cls, size, gmc, arm, delta)}")
                if not_run["ar2_2"]:
                    status = "NOT_EVALUABLE_AR2-2"
                elif not_run["frame_cap"]:
                    status = "NOT_EVALUABLE_FRAME_CAP"
                else:
                    status = "EVALUATED"
                rows.append(
                    {
                        "sequence": sequence,
                        "tag": tag,
                        "class": cls,
                        "size": size,
                        "gmc_source": gmc,
                        "arm": arm,
                        "delta_s": delta,
                        "status": status,
                        "N_all": n_all,
                        "N_res": n_res,
                        "N_vis": n_vis,
                        "N_inv": n_inv,
                        "not_run": {"ar2_2": not_run["ar2_2"], "frame_cap": not_run["frame_cap"]},
                        "buckets": {name: counts[name] for name in BUCKETS},
                        "level2": level2,
                        "ratios": ratios(counts, n_res, n_vis, n_inv, level2["adopted"]),
                        "ratios_scope": "full_sample" if status == "EVALUATED" else "subsample_diagnostic_only",
                        "conserved": True,
                    }
                )
    return rows


def conservation_ok(row: Mapping[str, Any]) -> bool:
    counts = row["buckets"]
    not_run = sum(row["not_run"].values())
    return (
        sum(counts.values()) + not_run == row["N_all"]
        and row["N_vis"] + row["N_inv"] + counts["NO_RESOLVE_FRAME"] + not_run == row["N_all"]
        and set(counts) == set(BUCKETS)
    )


def iter_level2_reasons(rows: Iterable[Mapping[str, Any]]) -> set[str]:
    return {name for row in rows for name, value in row["level2"]["failed_by_reason"].items() if value}
