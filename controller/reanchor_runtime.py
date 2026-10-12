from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import threading
import time
from typing import Any, Callable, Mapping, Sequence

from .reanchor import (
    BufferedFrame, FrameHistory, ReanchorConfig, ReplayResult, angular_distance,
    SingleFlightWorker, TripleGateState, replay_tracker, world_los,
)
from .reanchor_models import DinoV2Embedder, YoloeProposer, build_candidates
from .sensor_protocol import (
    SYSTEM_MONOTONIC_CLOCK_ID,
    validate_system_monotonic_frame,
)
from .trackers import BoxNorm, TrackerPlugin, TrackerResult, clip_box_norm


@dataclass(frozen=True)
class RuntimeEvent:
    frame_id: int
    event: str
    fields: Mapping[str, Any]


class ReanchorRuntime:
    """Main-thread persistence facade around one zero-queue model worker."""

    def __init__(
        self,
        config: ReanchorConfig,
        tracker_factory: Callable[[], TrackerPlugin],
        *,
        proposer: Any | None = None,
        embedder: Any | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        monotonic_clock_id: str | None = None,
    ):
        # P5 身份绑定：进程内单调源不是输出字段，默认 time.monotonic 即
        # system-stopwatch/v1；非默认注入必须显式声明同一时钟。
        if monotonic is time.monotonic:
            declared_clock_id = SYSTEM_MONOTONIC_CLOCK_ID
        else:
            if monotonic_clock_id != SYSTEM_MONOTONIC_CLOCK_ID:
                raise ValueError(
                    "non-default monotonic injection must explicitly declare "
                    f"monotonic_clock_id={SYSTEM_MONOTONIC_CLOCK_ID!r}"
                )
            declared_clock_id = monotonic_clock_id
        self.monotonic_clock_id = declared_clock_id
        self.config = config
        self.p = config.parameters
        self.proposer = proposer or YoloeProposer(config)
        self.embedder = embedder or DinoV2Embedder(config)
        self.tracker_factory = tracker_factory
        self.monotonic = monotonic
        self.gate = TripleGateState(config)
        self.history = FrameHistory(float(self.p["frame_buffer_s"]))
        self.worker = SingleFlightWorker(
            timeout_s=float(self.p["worker_timeout_s"]),
            failure_limit=int(self.p["consecutive_failure_limit"]),
            monotonic=monotonic,
        )
        self._lock = threading.Lock()
        self._pending: ReplayResult | None = None
        self._pending_fields: Mapping[str, Any] | None = None
        self._events: list[RuntimeEvent] = []
        self.anchor_embedding: Sequence[float] | None = None
        self.next_tick_capture_s: float | None = None
        self.planned_ticks = 0
        self.completed_unexpired_rounds = 0
        self.reseed_failures = 0
        self.fatal_reason: str | None = None

    def initialize(self, bundle: Any, box_norm: BoxNorm) -> None:
        self.anchor_embedding = self.embedder.embed(bundle.image, box_norm)
        self.proposer.initialize(bundle.image, box_norm)
        self.after_frame(bundle, TrackerResult(box_norm, True, 1.0, "placeholder"), released=False)

    def before_update(
        self,
        last_consumed_frame_id: int,
        *,
        old_tracker_instance_id: int | None = None,
    ) -> TrackerPlugin | None:
        with self._lock:
            pending = self._pending
            if pending is None:
                return None
            pending_fields = self._pending_fields
            self._pending = None
            self._pending_fields = None
            source_capture = (
                float(pending_fields["source_capture_monotonic_s"])
                if pending_fields is not None
                and "source_capture_monotonic_s" in pending_fields
                else None
            )
            if (
                source_capture is None
                or self.monotonic() - source_capture
                > float(self.p["maximum_result_age_s"])
            ):
                self._events.append(RuntimeEvent(last_consumed_frame_id, "RESEED_DISCARDED_STALE", {"reason": "atomic_swap_result_too_old"}))
                self.reseed_failures += 1
                return None
            if pending.head_frame_id != last_consumed_frame_id or self.history.head_frame_id != last_consumed_frame_id:
                self._events.append(RuntimeEvent(last_consumed_frame_id, "RESEED_DISCARDED_NOT_CONVERGED", {"reason": "atomic_head_mismatch"}))
                self.reseed_failures += 1
                return None
            head = self.history.get(last_consumed_frame_id)
            if (
                head is None
                or pending.last_result is None
                or pending.last_result.box_norm is None
            ):
                self._events.append(RuntimeEvent(last_consumed_frame_id, "RESEED_DISCARDED_INVALID_BOX", {"reason": "missing_catchup_head_box"}))
                self.reseed_failures += 1
                return None
            try:
                head_los = world_los(
                    pending.last_result.box_norm,
                    head.metadata,
                    basis_tolerance=float(self.p["basis_tolerance"]),
                    quaternion_tolerance=float(self.p["quaternion_tolerance"]),
                )
            except (TypeError, ValueError) as exception:
                self._events.append(RuntimeEvent(last_consumed_frame_id, "RESEED_DISCARDED_INVALID_BOX", {"reason": type(exception).__name__}))
                self.reseed_failures += 1
                return None
            self.gate.reseed_succeeded(head_los, head.capture_monotonic_s)
            self.reseed_failures = 0
            self._events.append(RuntimeEvent(last_consumed_frame_id, "REANCHOR", {
                "source_frame_id": pending.source_frame_id,
                "catchup_frame_id": pending.head_frame_id,
                "replay_count": pending.replay_count,
                "replay_latency_ms": pending.elapsed_ms,
                "old_tracker_instance_id": old_tracker_instance_id,
                "new_tracker_instance_id": id(pending.tracker),
                **dict(pending_fields or {}),
            }))
            return pending.tracker

    def after_frame(self, bundle: Any, result: TrackerResult, *, released: bool) -> None:
        capture = validate_system_monotonic_frame(
            bundle.metadata,
            context="reanchor",
        )
        box = clip_box_norm(result.box_norm) if result.ok and result.box_norm is not None else None
        with self._lock:
            if self.history.get(bundle.frame_id) is None:
                self.history.append(BufferedFrame(bundle.frame_id, capture, bundle.image, bundle.metadata, box))
        if not released:
            return
        with self._lock:
            anchor_missing = self.gate.anchor is None
        if anchor_missing:
            if box is None:
                self.fatal_reason = "reanchor_release_anchor_unavailable"
                self._events.append(RuntimeEvent(bundle.frame_id, "REANCHOR_FAIL_CLOSED", {"reason": self.fatal_reason}))
                return
            try:
                release_los = world_los(
                    box,
                    bundle.metadata,
                    basis_tolerance=float(self.p["basis_tolerance"]),
                    quaternion_tolerance=float(self.p["quaternion_tolerance"]),
                )
            except (TypeError, ValueError) as exception:
                self.fatal_reason = "reanchor_release_metadata_invalid"
                self._events.append(RuntimeEvent(bundle.frame_id, "REANCHOR_FAIL_CLOSED", {"reason": type(exception).__name__}))
                return
            with self._lock:
                if self.gate.anchor is None:
                    self.gate.set_anchor(release_los, capture)
                    self.next_tick_capture_s = capture + float(self.p["cadence_s"])
        if self.next_tick_capture_s is None or capture + 1e-9 < self.next_tick_capture_s:
            return
        cadence = float(self.p["cadence_s"])
        due_ticks = int((capture - self.next_tick_capture_s) // cadence) + 1
        self.planned_ticks += due_ticks
        self.next_tick_capture_s += due_ticks * cadence
        if due_ticks > 1:
            self._events.append(
                RuntimeEvent(
                    bundle.frame_id,
                    "ROUND_SKIPPED_CADENCE_GAP",
                    {"skipped_ticks": due_ticks - 1},
                )
            )
        if self.worker.busy:
            self._events.append(RuntimeEvent(bundle.frame_id, "ROUND_SKIPPED_BUSY", {}))
            return
        source_frame_id = bundle.frame_id
        source_capture = capture
        source_image = bundle.image
        source_metadata = dict(bundle.metadata)
        source_sot_box = box

        def round_work() -> Mapping[str, Any]:
            started = self.monotonic()
            batch = self.proposer.propose(source_image)
            appearance_started = self.monotonic()
            with self._lock:
                anchor = self.gate.anchor
            assert self.anchor_embedding is not None and anchor is not None
            candidates, crop_invalid = build_candidates(
                batch, source_image, source_metadata, self.embedder,
                self.anchor_embedding, anchor.los_world,
                basis_tolerance=float(self.p["basis_tolerance"]),
                quaternion_tolerance=float(self.p["quaternion_tolerance"]),
            )
            appearance_gate_latency_ms = (
                self.monotonic() - appearance_started
            ) * 1000.0
            if self.monotonic() - source_capture > float(self.p["maximum_result_age_s"]):
                return {
                    "source_frame_id": source_frame_id,
                    "source_capture_monotonic_s": source_capture,
                    "detector_latency_ms": batch.detector_latency_ms,
                    "appearance_gate_latency_ms": appearance_gate_latency_ms,
                    "class_candidate_count": len(batch.boxes_norm),
                    "crop_invalid_count": crop_invalid,
                    "decision": "ROUND_DISCARDED_STALE",
                    "margin": None,
                    "winner": None,
                    "replay": None,
                }
            with self._lock:
                current_anchor = self.gate.anchor
                if current_anchor is None:
                    raise RuntimeError("motion anchor became unavailable")
                if current_anchor != anchor:
                    candidates = tuple(
                        replace(
                            candidate,
                            motion_angle_rad=angular_distance(
                                candidate.world_los,
                                current_anchor.los_world,
                            ),
                        )
                        for candidate in candidates
                    )
                decision = self.gate.evaluate(
                    candidates, sot_box_norm=source_sot_box,
                    capture_monotonic_s=source_capture,
                    class_candidate_count=len(batch.boxes_norm),
                    crop_invalid_count=crop_invalid,
                    lost=source_sot_box is None,
                )
            replay = None
            trigger_reason = None
            if decision.trigger_reseed and decision.winner is not None:
                trigger_reason = (
                    "LOST_DIRECT"
                    if source_sot_box is None
                    else "K_HYSTERESIS"
                )
                replay = self._catch_up(
                    source_frame_id,
                    decision.winner.box_norm,
                    started,
                )
            return {
                "source_frame_id": source_frame_id,
                "source_capture_monotonic_s": source_capture,
                "detector_latency_ms": batch.detector_latency_ms,
                "appearance_gate_latency_ms": appearance_gate_latency_ms,
                "class_candidate_count": len(batch.boxes_norm),
                "crop_invalid_count": crop_invalid,
                "decision": decision.outcome,
                "trigger_reason": trigger_reason,
                "margin": decision.margin,
                "winner": asdict(decision.winner) if decision.winner else None,
                "replay": replay,
            }
        message = self.worker.submit(round_work)
        self._events.append(RuntimeEvent(bundle.frame_id, message.event, {"started_monotonic_s": message.started_monotonic_s}))

    def _catch_up(
        self,
        source_frame_id: int,
        box: BoxNorm,
        started: float,
    ) -> ReplayResult:
        while self.monotonic() - started <= float(self.p["catchup_timeout_s"]):
            with self._lock:
                snapshot = self.history.snapshot()
                head = snapshot.head_frame_id
            if head is None:
                self._increment_reseed_failure()
                return ReplayResult(
                    "RESEED_DISCARDED_MISSING_FRAME",
                    None,
                    source_frame_id,
                    None,
                    0,
                    (self.monotonic() - started) * 1000.0,
                    None,
                    "empty_history",
                )
            replay = replay_tracker(
                self.tracker_factory, snapshot, source_frame_id=source_frame_id,
                source_box_norm=box, target_head_frame_id=head,
                maximum_source_age_s=float(self.p["maximum_result_age_s"]),
                catchup_timeout_s=max(0.001, float(self.p["catchup_timeout_s"]) - (self.monotonic() - started)),
                monotonic=self.monotonic,
            )
            if replay.event != "RESEED_READY":
                self._increment_reseed_failure()
                return replay
            with self._lock:
                if self.history.head_frame_id == head:
                    return replay
        self._increment_reseed_failure()
        return ReplayResult(
            "RESEED_DISCARDED_NOT_CONVERGED",
            None,
            source_frame_id,
            None,
            0,
            (self.monotonic() - started) * 1000.0,
            None,
            "catchup_timeout",
        )

    def poll(self) -> None:
        message = self.worker.poll()
        if message is None:
            self._refresh_fatal()
            return
        fields = {"reason": message.reason, "completed_monotonic_s": message.completed_monotonic_s}
        if message.completed_monotonic_s is not None:
            fields["worker_latency_ms"] = (
                message.completed_monotonic_s - message.started_monotonic_s
            ) * 1000.0
        if message.event == "ROUND_COMPLETE":
            payload = dict(message.payload)
            source = int(payload["source_frame_id"])
            replay = payload.pop("replay", None)
            if replay is not None and not isinstance(replay, ReplayResult):
                raise RuntimeError("invalid replay worker payload")
            payload["replay"] = replay.event if replay is not None else None
            completed = message.completed_monotonic_s or self.monotonic()
            age = completed - float(payload["source_capture_monotonic_s"])
            if age <= float(self.p["maximum_result_age_s"]):
                self.completed_unexpired_rounds += 1
            elif payload["decision"] != "ROUND_DISCARDED_STALE":
                payload["decision"] = "ROUND_DISCARDED_STALE"
            if replay is not None:
                if (
                    replay.event == "RESEED_READY"
                    and payload["decision"] != "ROUND_DISCARDED_STALE"
                ):
                    winner = payload.get("winner") or {}
                    with self._lock:
                        self._pending = replay
                        self._pending_fields = {
                            "source_capture_monotonic_s": payload["source_capture_monotonic_s"],
                            "detector_confidence": winner.get("detector_confidence"),
                            "reid_cosine": winner.get("reid_cosine"),
                            "motion_angle_rad": winner.get("motion_angle_rad"),
                            "margin": payload.get("margin"),
                            "trigger_reason": payload.get("trigger_reason"),
                        }
                elif replay.event == "RESEED_READY":
                    self._increment_reseed_failure()
                    replay = ReplayResult(
                        "RESEED_DISCARDED_STALE",
                        None,
                        replay.source_frame_id,
                        replay.head_frame_id,
                        replay.replay_count,
                        replay.elapsed_ms,
                        replay.last_result,
                        "round_completed_after_maximum_result_age",
                    )
            fields.update(payload)
            self._events.append(RuntimeEvent(source, str(payload["decision"]), fields))
            if replay is not None and replay.event != "RESEED_READY":
                self._events.append(
                    RuntimeEvent(
                        source,
                        replay.event,
                        {
                            "reason": replay.reason,
                            "source_frame_id": replay.source_frame_id,
                            "catchup_frame_id": replay.head_frame_id,
                            "replay_count": replay.replay_count,
                            "replay_latency_ms": replay.elapsed_ms,
                        },
                    )
                )
        else:
            self._events.append(RuntimeEvent(-1, message.event, fields))
        self._refresh_fatal()

    def _refresh_fatal(self) -> None:
        with self._lock:
            reseed_failures = self.reseed_failures
        if self.worker.fail_closed or reseed_failures >= int(self.p["consecutive_failure_limit"]):
            self.fatal_reason = "reanchor_consecutive_failure_limit"
        if self.worker.timed_out_alive:
            self.fatal_reason = "reanchor_worker_timeout_alive"

    def _increment_reseed_failure(self) -> None:
        with self._lock:
            self.reseed_failures += 1

    def drain_events(self) -> tuple[RuntimeEvent, ...]:
        events = tuple(self._events)
        self._events.clear()
        return events

    def close(self) -> bool:
        return self.worker.close(float(self.p["worker_join_timeout_s"]))

    def emit_summary(self) -> None:
        rate = (
            self.completed_unexpired_rounds / self.planned_ticks
            if self.planned_ticks
            else None
        )
        self._events.append(
            RuntimeEvent(
                (
                    self.history.head_frame_id
                    if self.history.head_frame_id is not None
                    else -1
                ),
                "REANCHOR_CHANNEL_SUMMARY",
                {
                    "planned_ticks": self.planned_ticks,
                    "completed_unexpired_rounds": self.completed_unexpired_rounds,
                    "cadence_completion_rate": rate,
                    "cadence_completion_minimum": float(self.p["cadence_completion_minimum"]),
                    "cadence_qualified": (
                        rate is not None
                        and rate >= float(self.p["cadence_completion_minimum"])
                    ),
                },
            )
        )

    def manifest_identity(self) -> Mapping[str, Any]:
        return {
            **self.config.identity(),
            "monotonic_clock_id": self.monotonic_clock_id,
        }
