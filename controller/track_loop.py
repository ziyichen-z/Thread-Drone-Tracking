from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import shutil
import sys
import time
from typing import Any, Callable, Mapping, Sequence
import uuid

from . import body_entry, gimbal_entry, tracking_entry
from .body_planner import (
    CONTRACT_VERSION as BODY_CONTRACT_VERSION,
    BodyCommand,
    BodyPlanner,
    HoldBodyPlanner,
    PlatformState,
    ThresholdBodyPlanner,
    load_corridor_prisms,
)
from .geolocate import GeometryRejected, box_ground_intersection
from .protocol import RUNTIME
from .qualification_protocol import (
    MANIFEST_KEY as QUALIFICATION_RELEASE_MANIFEST_KEY,
    QUALIFICATION_RUN_ID,
    QualificationProtocolError,
    QualificationReleaseLifecycle,
    manifest_identity as qualification_release_manifest_identity,
    request_release as request_qualification_release,
)
from .rate2_protocol import (
    SENSOR_SCHEMA as RATE2_FRAME_SCHEMA,
    Rate2TrackerLifecycle,
    load_session as load_rate2_session,
)
from .rate3_protocol import (
    Rate3TrackerLifecycle,
    load_session as load_rate3_session,
)
from .run_log import RunLogger, finalize_run
from .scenario_tether import (
    effective_scenario_path,
    parse_tether_settings,
    safety_bounds as scenario_safety_bounds,
)
from .standoff_planner import (
    FrameBodyConfig,
    StandoffBodyPlanner,
    StandoffFixed,
    StandoffGeometry,
    StandoffParams,
    load_frame_body_config,
)
from .sensor_protocol import (
    SENSOR_FRAME_SCHEMA_V3,
    validate_system_monotonic_frame,
)
from .world_estimate import WorldEstimateFilter
from .trackers import (
    BoxNorm,
    DEFAULT_NANOTRACK_V2_MODEL_DIR,
    DEFAULT_NANOTRACK_V2_SPEC,
    TrackerPlugin,
    TrackerResult,
    clip_box_norm,
    create_tracker,
    sha256_file,
)
from .reanchor import DEFAULT_CONFIG as DEFAULT_REANCHOR_CONFIG, load_reanchor_config
from .resident_core import ProtocolMisuse


FRAME_SCHEMA = SENSOR_FRAME_SCHEMA_V3
MANIFEST_SCHEMA = "tethered-frame-manifest/v1"
TRACKING_STATES = {"TRACKING", "LOST", "ERROR_REINIT_REQUIRED"}
# P1-ENG-ACQ-001 AC-15 修订 1：常驻载体追平时窗口外旧帧只 step 不发布，帧记录 `publish_skip_reason` 取此值。
PUBLISH_SKIP_OUTSIDE_WINDOW = "outside_resident_publish_window"


@dataclass(frozen=True)
class FrameBundle:
    frame_id: int
    image_path: Path
    metadata_path: Path
    image: Any
    metadata: dict[str, Any]


class FrameRepository:
    def __init__(
        self,
        runtime: Path,
        image_loader: Callable[[Path], Any] | None = None,
        expected_frame_schema: str = FRAME_SCHEMA,
    ):
        self.runtime = Path(runtime)
        self.frames_directory = self.runtime / "frames"
        self._image_loader = image_loader or load_cv_image
        self.expected_frame_schema = expected_frame_schema

    def latest_frame_id(self) -> int:
        manifest_path = self.frames_directory / "latest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != MANIFEST_SCHEMA:
            raise ValueError(
                f"unsupported frame manifest: {manifest.get('schema_version')!r}"
            )
        frame_id = int(manifest["frame_id"])
        if frame_id < 0:
            raise ValueError("latest frame_id must be non-negative")
        return frame_id

    def frame_paths(self, frame_id: int) -> tuple[Path, Path]:
        if frame_id < 0:
            raise ValueError("frame_id must be non-negative")
        stem = f"frame_{frame_id:010d}"
        return (
            self.frames_directory / f"{stem}.jpg",
            self.frames_directory / f"{stem}.json",
        )

    def load(self, frame_id: int) -> FrameBundle:
        image_path, metadata_path = self.frame_paths(frame_id)
        if not image_path.is_file() or not metadata_path.is_file():
            raise FileNotFoundError(
                f"exact retained frame bundle {frame_id} is unavailable"
            )
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("schema_version") != self.expected_frame_schema:
            raise ValueError(
                f"frame {frame_id} has unsupported schema "
                f"{metadata.get('schema_version')!r}; expected "
                f"{self.expected_frame_schema!r}"
            )
        if int(metadata.get("frame_id", -1)) != frame_id:
            raise ValueError(f"frame {frame_id} metadata id mismatch")
        if self.expected_frame_schema == FRAME_SCHEMA:
            validate_system_monotonic_frame(
                metadata,
                context=f"frame {frame_id}",
            )
        image = self._image_loader(image_path)
        return FrameBundle(frame_id, image_path, metadata_path, image, metadata)

    def dump_frame(self, frame_id: int, destination: Path) -> Path:
        image_path, metadata_path = self.frame_paths(frame_id)
        if not image_path.is_file() or not metadata_path.is_file():
            raise FileNotFoundError(
                f"exact retained frame bundle {frame_id} is unavailable"
            )
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image_path, destination)
        return destination


def load_cv_image(path: Path) -> Any:
    try:
        import cv2
    except ImportError as exception:
        raise RuntimeError(
            "cv2 is unavailable; activate .venv-track and install "
            "tools/requirements-track.txt"
        ) from exception
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"OpenCV could not decode frame image: {path}")
    return image


class RuntimePublisher:
    def __init__(self, runtime: Path, expires_after_s: float):
        self.runtime = Path(runtime)
        self.expires_after_s = float(expires_after_s)

    def hold_body(self) -> Path:
        return body_entry.hold(self.expires_after_s, runtime=self.runtime)

    def set_nadir(self) -> Path:
        return gimbal_entry.nadir(self.expires_after_s, runtime=self.runtime)

    def observation(
        self,
        frame_id: int,
        track_id: str,
        box_norm: BoxNorm,
        confidence: float,
    ) -> Path:
        return tracking_entry.observation(
            frame_id,
            *box_norm,
            track_id=track_id,
            confidence=confidence,
            expires_after_s=self.expires_after_s,
            runtime=self.runtime,
        )

    def look_at(self, point_world_m: Sequence[float]) -> Path:
        return gimbal_entry.look_at(
            float(point_world_m[0]),
            float(point_world_m[2]),
            float(point_world_m[1]),
            self.expires_after_s,
            runtime=self.runtime,
        )

    def body_command(self, command: BodyCommand) -> Path:
        """Publish a planner decision; ``body_entry`` stays the only writer."""
        if command.mode == "hold":
            return body_entry.hold(command.expires_after_s, runtime=self.runtime)
        vx, vy, vz = command.velocity_world_mps
        return body_entry.velocity(
            vx,
            vz,
            vy,
            command.expires_after_s,
            runtime=self.runtime,
        )


class TrackLoop:
    def __init__(
        self,
        repository: FrameRepository,
        tracker: TrackerPlugin,
        publisher: RuntimePublisher,
        logger: RunLogger,
        *,
        track_id: str,
        condition: str,
        ground_plane_y_m: float,
        maximum_ground_range_m: float,
        planned_duration_s: float,
        rate2_lifecycle: Rate2TrackerLifecycle | None = None,
        rate3_lifecycle: Rate3TrackerLifecycle | None = None,
        reanchor_runtime: Any | None = None,
        qualification_lifecycle: QualificationReleaseLifecycle | None = None,
        body_planner: BodyPlanner | None = None,
        body_estimator: WorldEstimateFilter | None = None,
        body_expires_after_s: float | None = None,
        resident_publish_window: int | None = None,
        servo_max_deg_per_frame: float | None = None,
        capture_hook: Any | None = None,
    ):
        if not track_id.strip():
            raise ValueError("track_id must not be empty")
        if condition not in {"follow", "nadir"}:
            raise ValueError("condition must be follow or nadir")
        self.ground_plane_y_m = _finite(
            ground_plane_y_m, "ground_plane_y_m"
        )
        self.maximum_ground_range_m = _finite(
            maximum_ground_range_m, "maximum_ground_range_m"
        )
        self.planned_duration_s = _finite(
            planned_duration_s, "planned_duration_s"
        )
        if self.maximum_ground_range_m <= 0.0:
            raise ValueError("maximum_ground_range_m must be positive")
        if self.planned_duration_s <= 0.0:
            raise ValueError("planned_duration_s must be positive")
        self.repository = repository
        self.tracker = tracker
        self.publisher = publisher
        self.logger = logger
        self.track_id = track_id
        self.condition = condition
        self.rate2_lifecycle = rate2_lifecycle
        self.rate3_lifecycle = rate3_lifecycle
        self._rate_lifecycle = (
            rate2_lifecycle if rate2_lifecycle is not None else rate3_lifecycle
        )
        self.reanchor_runtime = reanchor_runtime
        self.qualification_lifecycle = qualification_lifecycle
        if body_planner is not None and body_estimator is None:
            # Contract fail-safe (b) would make every decision a hold; wiring
            # a policy without the estimator is a configuration error.
            raise ValueError("a body planner requires the body estimator")
        if body_planner is not None or body_estimator is not None:
            if body_expires_after_s is None:
                raise ValueError("body wiring requires body_expires_after_s")
            self.body_expires_after_s = _finite(
                body_expires_after_s, "body_expires_after_s"
            )
            if self.body_expires_after_s <= 0.0:
                raise ValueError("body_expires_after_s must be positive")
        else:
            self.body_expires_after_s = None
        self.body_planner = body_planner
        self.body_estimator = body_estimator
        # BC-BODY1-20 (b): set by _body_step when both the command write and
        # the fallback hold write fail; the frame loop then terminates the
        # run fail closed after appending this frame's record.
        self._body_fail_closed_reason: str | None = None
        release_lifecycles = sum(
            lifecycle is not None
            for lifecycle in (
                self.rate2_lifecycle,
                self.rate3_lifecycle,
                self.qualification_lifecycle,
            )
        )
        if release_lifecycles > 1:
            raise ValueError("track loop cannot combine release lifecycles")
        self._invalid_clock_fail_closed = (
            self._rate_lifecycle is not None
            and getattr(self._rate_lifecycle, "requires_wall_completion", False)
        )
        # P1-ENG-ACQ-001 §3.1：常驻协议按插件是否具备 `step` 且声明 `mode == "resident"` 判定
        # （`compat` 模式的 det-assoc-v1 也有 `step` 属性但调用即 `ProtocolMisuse`，不可据此误判）。
        self.resident = is_resident_tracker(tracker)
        if self.resident and (
            release_lifecycles
            or reanchor_runtime is not None
        ):
            raise ValueError("the resident protocol does not combine with release lifecycles or re-anchor")
        if resident_publish_window is not None and resident_publish_window < 0:
            raise ValueError("resident_publish_window must be non-negative")
        self.resident_publish_window = resident_publish_window
        if servo_max_deg_per_frame is not None and not (
            math.isfinite(servo_max_deg_per_frame) and servo_max_deg_per_frame > 0.0
        ):
            raise ValueError("servo_max_deg_per_frame must be positive")
        self.servo_max_deg_per_frame = servo_max_deg_per_frame
        #: P1-ENG-CAPTURE-001 C4/C6（捕获模式）：目标管理器钩子。为 None（缺省，含兼容模式）时常驻路径逐字不变；
        #: 非 None 时每帧把常驻历史交管理器（①–④），只对本批最新帧按其授权效果发布（⑤，B7）。
        if capture_hook is not None and not self.resident:
            raise ValueError("the capture hook requires a resident tracker")
        self.capture_hook = capture_hook
        self.last_servo_point: tuple[float, float, float] | None = None
        self.last_frame_id: int | None = None
        self.initial_simulation_time_s: float | None = None
        self.last_simulation_time_s: float | None = None
        self.last_measurement_elapsed_s: float | None = None
        self.last_measurement_wall_elapsed_s: float | None = None
        self.state = "LOST"
        self.terminal = False

    @property
    def elapsed_simulation_s(self) -> float:
        if (
            self._rate_lifecycle is not None
            or self.qualification_lifecycle is not None
        ):
            return max(0.0, self.last_measurement_elapsed_s or 0.0)
        if (
            self.initial_simulation_time_s is None
            or self.last_simulation_time_s is None
        ):
            return 0.0
        return max(
            0.0,
            self.last_simulation_time_s - self.initial_simulation_time_s,
        )

    @property
    def complete(self) -> bool:
        if self.terminal:
            return True
        if self.qualification_lifecycle is not None or (
            self._rate_lifecycle is not None
            and getattr(
                self._rate_lifecycle, "requires_wall_completion", False
            )
        ):
            return (
                self.elapsed_simulation_s >= self.planned_duration_s
                and max(0.0, self.last_measurement_wall_elapsed_s or 0.0)
                >= self.planned_duration_s
            )
        return self.elapsed_simulation_s >= self.planned_duration_s

    def initialize(self, frame_id: int, box_norm: Sequence[float]) -> None:
        if self.resident:
            raise ProtocolMisuse("initialize(frame_id, box) is not available on a resident tracker; use start(frame_id)")
        if self.last_frame_id is not None:
            raise RuntimeError("track loop is already initialized")
        bundle = self.repository.load(frame_id)
        clipped = clip_box_norm(box_norm)
        if clipped is None:
            raise ValueError("initial box is degenerate or outside the image")
        started = time.perf_counter()
        initialized = self.tracker.init(bundle.image, clipped)
        compute_latency_ms = (time.perf_counter() - started) * 1000.0
        if not initialized:
            raise RuntimeError("tracker rejected the exact initialization frame/box")

        if self._rate_lifecycle is None:
            self.publisher.hold_body()
            if self.condition == "nadir":
                self.publisher.set_nadir()

        result = TrackerResult(clipped, True, 1.0, "placeholder")
        publication = (
            _empty_publication()
            if self.qualification_lifecycle is not None
            else self._publish_latest(
                bundle,
                result,
                allow_control=self._rate_lifecycle is None,
            )
        )
        self.initial_simulation_time_s = _metadata_float(
            bundle.metadata, "simulation_time_s"
        )
        self.last_simulation_time_s = self.initial_simulation_time_s
        self.last_frame_id = frame_id
        self.state = "TRACKING"
        protocol_fields = self._protocol_fields(bundle)
        self._append_record(
            bundle,
            result,
            state="TRACKING",
            event="INIT",
            compute_latency_ms=compute_latency_ms,
            backlog_count=0,
            skipped_count=0,
            publication=publication,
            recovered_from_lost=False,
            protocol_fields=protocol_fields,
        )
        if self.reanchor_runtime is not None:
            self.reanchor_runtime.initialize(bundle, clipped)
            self._drain_reanchor_events()
        if self._rate_lifecycle is not None:
            self._rate_lifecycle.publish_ready(frame_id, "TRACKING")
        if self.qualification_lifecycle is not None:
            self.qualification_lifecycle.publish_ready(bundle.metadata)

    def process_available(self, latest_frame_id: int | None = None) -> int:
        if self.last_frame_id is None:
            raise RuntimeError("track loop must be initialized first")
        if self.terminal:
            return 0
        if self.resident:
            return self._process_resident(latest_frame_id)
        if self._rate_lifecycle is not None:
            self._rate_lifecycle.poll_release_ack()
        if self.qualification_lifecycle is not None:
            self.qualification_lifecycle.poll_release_command()
        if self.reanchor_runtime is not None:
            self.reanchor_runtime.poll()
            if self.reanchor_runtime.fatal_reason:
                self._record_terminal_error(
                    self.last_frame_id,
                    event="REANCHOR_FAIL_CLOSED",
                    reason=self.reanchor_runtime.fatal_reason,
                )
                self._drain_reanchor_events()
                return 0
            self._drain_reanchor_events()
        latest = (
            self.repository.latest_frame_id()
            if latest_frame_id is None
            else int(latest_frame_id)
        )
        if latest < self.last_frame_id:
            self._record_terminal_error(
                latest,
                event="REINIT_REQUIRED",
                reason="frame_id_reset_or_rollback",
            )
            return 0
        if latest == self.last_frame_id:
            return 0

        expected_ids = list(range(self.last_frame_id + 1, latest + 1))
        bundles: list[FrameBundle] = []
        for expected_id in expected_ids:
            try:
                bundles.append(self.repository.load(expected_id))
            except FileNotFoundError:
                self._record_terminal_error(
                    expected_id,
                    event="GAP",
                    reason="retained_intermediate_frame_missing",
                )
                return 0
            except ValueError as exception:
                if not self._invalid_clock_fail_closed:
                    raise
                # RATE-003 §1.1(b)：坏时钟帧在该帧任何副作用之前终止 run。
                self._record_terminal_error(
                    expected_id,
                    event="INVALID_CLOCK",
                    reason=str(exception),
                )
                return 0

        processed: list[
            tuple[
                FrameBundle,
                TrackerResult,
                float,
                bool,
                Mapping[str, Any] | None,
            ]
        ] = []
        previous_state = self.state
        consumed_frame_id = self.last_frame_id
        for bundle in bundles:
            if self.reanchor_runtime is not None:
                replacement = self.reanchor_runtime.before_update(
                    consumed_frame_id,
                    old_tracker_instance_id=id(self.tracker),
                )
                if replacement is not None:
                    self.tracker = replacement
            started = time.perf_counter()
            raw_result = self.tracker.update(bundle.image)
            compute_latency_ms = (time.perf_counter() - started) * 1000.0
            result = _publication_ready_result(raw_result)
            recovered = previous_state == "LOST" and result.ok
            previous_state = "TRACKING" if result.ok else "LOST"
            if self._invalid_clock_fail_closed:
                try:
                    protocol_fields = self._protocol_fields(bundle)
                except ValueError as exception:
                    # RATE-003 §1.1(b)：时钟身份不符的帧不产生任何
                    # 观测/控制/re-anchor/记录副作用，run 以 INVALID_CLOCK 终止。
                    self._record_terminal_error(
                        bundle.frame_id,
                        event="INVALID_CLOCK",
                        reason=str(exception),
                    )
                    return 0
            else:
                protocol_fields = self._protocol_fields(bundle)
            processed.append(
                (
                    bundle,
                    result,
                    compute_latency_ms,
                    recovered,
                    protocol_fields,
                )
            )
            consumed_frame_id = bundle.frame_id
            if self.reanchor_runtime is not None:
                released = (
                    protocol_fields is None
                    or protocol_fields.get("phase") == "measurement"
                )
                if self._invalid_clock_fail_closed:
                    try:
                        self.reanchor_runtime.after_frame(
                            bundle, result, released=released
                        )
                    except ValueError as exception:
                        # RATE-003 §1.1(b)：re-anchor 侧时钟校验失败同样
                        # 在该帧副作用之前 fail-closed 终止。
                        self._record_terminal_error(
                            bundle.frame_id,
                            event="INVALID_CLOCK",
                            reason=str(exception),
                        )
                        return 0
                else:
                    self.reanchor_runtime.after_frame(
                        bundle, result, released=released
                    )
                self.reanchor_runtime.poll()
                if self.reanchor_runtime.fatal_reason:
                    self._record_terminal_error(
                        bundle.frame_id,
                        event="REANCHOR_FAIL_CLOSED",
                        reason=self.reanchor_runtime.fatal_reason,
                    )
                    self._drain_reanchor_events()
                    return 0

        backlog_count = max(0, len(processed) - 1)
        for index, (
            bundle,
            result,
            compute_latency_ms,
            recovered,
            protocol_fields,
        ) in enumerate(processed):
            is_latest = index == len(processed) - 1
            qualification_measurement = (
                self.qualification_lifecycle is None
                or (
                    protocol_fields is not None
                    and protocol_fields.get("phase") == "measurement"
                )
            )
            publication = (
                self._publish_latest(
                    bundle,
                    result,
                    allow_control=(
                        self._rate_lifecycle is None
                        or self._rate_lifecycle.frame_phase(bundle.metadata)
                        == "measurement"
                    ),
                )
                if is_latest and qualification_measurement
                else _empty_publication()
            )
            state = "TRACKING" if result.ok else "LOST"
            event: str | None = "LOST" if not result.ok else None
            if publication["geo_reject_reason"] is not None:
                event = "GEO_REJECT"
            body_fields = self._body_step(bundle, result) if is_latest else None
            self._append_record(
                bundle,
                result,
                state=state,
                event=event,
                compute_latency_ms=compute_latency_ms,
                backlog_count=backlog_count,
                skipped_count=0 if is_latest else 1,
                publication=publication,
                recovered_from_lost=recovered,
                protocol_fields=protocol_fields,
                body_fields=body_fields,
            )
            if self._body_fail_closed_reason is not None:
                # BC-BODY1-20 (b): both the command write and the fallback
                # hold failed; this frame's record carrying both errors is
                # already appended, so terminate the run fail closed.
                self._record_terminal_error(
                    bundle.frame_id,
                    event="BODY_COMMAND_FAIL_CLOSED",
                    reason=self._body_fail_closed_reason,
                )
                return 0
            self.last_simulation_time_s = _metadata_float(
                bundle.metadata, "simulation_time_s"
            )
            if protocol_fields is not None:
                elapsed = protocol_fields.get("measurement_elapsed_s")
                if elapsed is not None:
                    self.last_measurement_elapsed_s = float(elapsed)
                wall_elapsed = protocol_fields.get("measurement_wall_elapsed_s")
                if wall_elapsed is not None:
                    self.last_measurement_wall_elapsed_s = float(wall_elapsed)
            if self._rate_lifecycle is not None:
                self._rate_lifecycle.publish_ready(bundle.frame_id, state)
        self.last_frame_id = latest
        self.state = previous_state
        self._drain_reanchor_events()
        return len(processed)

    # --- P1-ENG-ACQ-001 常驻路径（§3.1/§3.5/§3.8；K1/K2/K3）------------------------

    def start(self, frame_id: int) -> None:
        """常驻协议起点：不带框、不调 `init`；对 `frame_id` 帧 `step` + `pointer_result` 一次并记录。"""
        if not self.resident:
            raise ProtocolMisuse("start(frame_id) is only available on a resident tracker")
        if self.last_frame_id is not None:
            raise RuntimeError("track loop is already started")
        bundle = self.repository.load(frame_id)
        self.publisher.hold_body()
        if self.condition == "nadir":
            self.publisher.set_nadir()
        self.initial_simulation_time_s = _metadata_float(bundle.metadata, "simulation_time_s")
        self.last_simulation_time_s = self.initial_simulation_time_s
        self._resident_frame(bundle, latest=frame_id, event_override="RESIDENT_START", previous_state="LOST")
        self.last_frame_id = frame_id

    def _process_resident(self, latest_frame_id: int | None) -> int:
        """逐帧：读帧 → `step(image, frame_id, metadata)` → `pointer_result(frame_id)` → 发布判定 → 记录。

        与旧路径不同，读帧、处理与发布逐帧交替（发布最终门 ① 要求被发布帧是最近一次加载的帧）；
        `resident_publish_window` 非空时只发布 `latest − frame_id ≤ 窗口` 的帧，其中 latest 在该帧发布前重读
        `latest.json`（与门 ④ 同源，R1-3；追平期间的旧帧只处理不发布，与门 ④ `K_pub` 同口径；帧记录
        `publish_skip_reason = outside_resident_publish_window`，AC-15 修订 1），
        空 = 每个处理帧都发布（§3.8）。窗口内帧的 `look_at` 仍经现有发布门，被拒不推进限速基准。
        机身步只在批末帧（规划器输入路径不变）。
        """
        latest = (
            self.repository.latest_frame_id()
            if latest_frame_id is None
            else int(latest_frame_id)
        )
        assert self.last_frame_id is not None
        if latest < self.last_frame_id:
            self._record_terminal_error(latest, event="REINIT_REQUIRED", reason="frame_id_reset_or_rollback")
            return 0
        if latest == self.last_frame_id:
            return 0
        processed = 0
        previous_state = self.state
        for expected_id in range(self.last_frame_id + 1, latest + 1):
            try:
                bundle = self.repository.load(expected_id)
            except FileNotFoundError:
                self._capture_partial_timing(expected_id, latest, "frame_missing")
                self._record_terminal_error(expected_id, event="GAP", reason="retained_intermediate_frame_missing")
                return processed
            except BaseException as error:
                # FASTFIX §3.5：读/解码/元数据异常帧——已过标记照记、未到达段 null 并附原因，再原样上抛（现行处置不变）。
                self._capture_partial_timing(expected_id, latest, f"load_failed:{type(error).__name__}")
                raise
            previous_state = self._resident_frame(bundle, latest=latest, previous_state=previous_state)
            processed += 1
            self.last_simulation_time_s = _metadata_float(bundle.metadata, "simulation_time_s")
            self.last_frame_id = expected_id
            if self._body_fail_closed_reason is not None:
                self._record_terminal_error(bundle.frame_id, event="BODY_COMMAND_FAIL_CLOSED", reason=self._body_fail_closed_reason)
                return processed
        self.state = previous_state
        return processed

    def _resident_frame(
        self,
        bundle: FrameBundle,
        *,
        latest: int,
        previous_state: str,
        event_override: str | None = None,
    ) -> str:
        clock = self._capture_clock()
        m_step0 = clock() if clock is not None else None
        if clock is not None:
            # FASTFIX C1-1：`m_assoc` 取库关联器 `update` 的实际返回时刻（计时包装，不改冻结关联文件），
            # 不再用 `step` 返回（其后的历史组装归入 tm 段，不冒作纯关联段）。
            self._assoc_return_m = None
            self._ensure_assoc_timing(clock)
        started = time.perf_counter()
        try:
            self.tracker.step(bundle.image, bundle.frame_id, bundle.metadata)  # type: ignore[attr-defined]
        except BaseException as error:
            if clock is not None:
                reached = self._step_marks(m_step0, clock())
                self._capture_partial_timing(
                    bundle.frame_id, latest, f"step_failed:{type(error).__name__}",
                    reached={"m_det": self._detect_mark(reached), "m_assoc": reached.get("m_assoc")},
                )
            raise
        m_step_end = clock() if clock is not None else None
        m_assoc = self._step_marks(m_step0, m_step_end).get("m_assoc") if clock is not None else None
        raw_result = self.tracker.pointer_result(bundle.frame_id)  # type: ignore[attr-defined]
        compute_latency_ms = (time.perf_counter() - started) * 1000.0
        if self.capture_hook is not None:
            return self._capture_frame(
                bundle, raw_result, latest=latest, previous_state=previous_state,
                event_override=event_override, compute_latency_ms=compute_latency_ms,
                marks={"m_step0": m_step0, "m_assoc": m_assoc, "m_step_end": m_step_end},
            )
        result = _publication_ready_result(raw_result)
        recovered = previous_state == "LOST" and result.ok
        state = "TRACKING" if result.ok else "LOST"
        is_latest = bundle.frame_id == latest
        window = self.resident_publish_window
        # R1-3：窗口判定与门 ④ 同源——发布前（本帧 step 之后）重读 `latest.json`，批内 Unity 写出的新帧
        # 计入判定；批首 latest 只决定本批处理到哪一帧。门 ①④ 本身不变。
        publish_latest = latest if window is None else self._publish_time_latest(latest)
        publish = window is None or publish_latest - bundle.frame_id <= window
        publication = self._publish_resident(bundle, result) if publish else _empty_publication()
        # AC-15 修订 1：窗口外的追平旧帧照常 step，但逐帧显式记录「因窗口外跳过发布」，不为其发 look_at。
        publish_skip_reason = None if publish else PUBLISH_SKIP_OUTSIDE_WINDOW
        event: str | None = event_override or ("LOST" if not result.ok else None)
        if publication["geo_reject_reason"] is not None:
            event = "GEO_REJECT"
        # 批末帧若已被批内新帧挤出窗口，它不再是「最新帧」：本批不做机身步（不发无同帧观测的机身指令），
        # 由下一批的批末帧照常执行。
        body_fields = self._body_step(bundle, result) if is_latest and publish else None
        self._append_record(
            bundle,
            result,
            state=state,
            event=event,
            compute_latency_ms=compute_latency_ms,
            backlog_count=max(0, latest - bundle.frame_id),
            skipped_count=0 if publish else 1,
            publication=publication,
            recovered_from_lost=recovered,
            body_fields=body_fields,
            resident_fields={
                "publish_skip_reason": publish_skip_reason,
                "resident_publish_window": window,
                "publish_latest_frame_id": publish_latest,
            },
        )
        self.state = state
        return state

    def _capture_frame(
        self,
        bundle: FrameBundle,
        raw_result: TrackerResult,
        *,
        latest: int,
        previous_state: str,
        event_override: str | None,
        compute_latency_ms: float,
        marks: Mapping[str, Any] | None = None,
    ) -> str:
        """捕获模式一帧：历史交管理器（①–④）；⑤ 只对本批最新帧求值，发布前复核效果仍有效（A12）。

        观测只在 OBSERVED 帧发（画幅裁剪框）；云台按授权发观测/预测 P_center（经现行 `servo_clamp`）；
        机身：FOLLOW 经规划器与现行约束，其余每帧显式 HOLD 收据。旧帧只处理、不发命令（B7）。

        P1-ENG-FASTFIX-001：最新帧发布前 `begin_frame`、机身步后 `settle_frame`（按最新帧一次结算 streak，G1）；
        每个被处理帧恰一条逐阶段耗时（G5，经钩子只进会话日志）。"""
        result = _publication_ready_result(raw_result)
        recovered = previous_state == "LOST" and result.ok
        state = "TRACKING" if result.ok else "LOST"
        window = self.resident_publish_window
        publish_latest = latest if window is None else self._publish_time_latest(latest)
        newest = bundle.frame_id == latest and (window is None or publish_latest - bundle.frame_id <= window)
        clock = self._capture_clock()
        m_tm: float | None = None
        settle: dict[str, Any] | None = None
        try:
            entry = self.tracker.history(bundle.frame_id)  # type: ignore[attr-defined]
            outcome = self.capture_hook.on_frame(entry, newest=newest)
            m_tm = clock() if clock is not None else None
            effect = outcome.effect if newest else None
            publication = _empty_publication()
            publication["capture"] = None
            body_fields = None
            begin = getattr(self.publisher, "begin_frame", None) if newest else None
            if callable(begin):
                begin(bundle.frame_id)
            if effect is not None and not self.capture_hook.effect_current(effect, frame_id=bundle.frame_id):
                publication["capture"] = {"effect_seq": effect.effect_seq, "dropped": "stale_effect"}
                effect = None
            if effect is not None:
                publication["capture"] = {
                    "effect_seq": effect.effect_seq,
                    "body": effect.body,
                    "gimbal": effect.gimbal,
                    "authorization_row": effect.authorization_row,
                    "reason_codes": list(effect.reason_codes),
                    "valid_until_frame": effect.valid_until_frame,
                }
                body_result: TrackerResult = TrackerResult.lost("capture_hold")
                if effect.observation_box_norm is not None and effect.observation_confidence is not None:
                    observed = _publication_ready_result(
                        TrackerResult(tuple(effect.observation_box_norm), True, float(effect.observation_confidence), "tracker")
                    )
                    if observed.ok and observed.box_norm is not None and observed.confidence is not None:
                        self.publisher.observation(bundle.frame_id, self.track_id, observed.box_norm, observed.confidence)
                        publication["published_observation"] = True
                        if effect.body == "FOLLOW":
                            body_result = observed
                elif hasattr(self.publisher, "clear_association"):
                    self.publisher.clear_association()
                if effect.authorization_row == 5:
                    publication["geo_reject_reason"] = "capture_center_geometry_rejected"
                if effect.gimbal != "none" and effect.aim_point_world_m is not None and self.condition != "nadir":
                    self._capture_look_at(bundle, effect, publication)
                body_fields = self._body_step(bundle, body_result)
            settle_frame = getattr(self.publisher, "settle_frame", None) if newest else None
            if callable(settle_frame):
                settle = settle_frame(bundle.frame_id)
                note_settled = getattr(self.capture_hook, "on_frame_settled", None)
                if settle is not None and callable(note_settled):
                    note_settled(settle)
        except BaseException as error:
            # C1-1（§3.5、首次接受释义 4）：管理器或发布阶段异常仍恰一行计时——已到达标记照记，未到达段带原因，再原样上抛。
            if clock is not None:
                stage = "tm_failed" if m_tm is None else "publish_failed"
                step = marks or {}
                m_assoc = step.get("m_assoc")
                self._capture_partial_timing(
                    bundle.frame_id, latest, f"{stage}:{type(error).__name__}",
                    reached={
                        "m_det": self._detect_mark({"m_step0": step.get("m_step0"),
                                                    "m_upper": m_assoc if m_assoc is not None else step.get("m_step_end")}),
                        "m_assoc": m_assoc, "m_tm": m_tm,
                    },
                    settle=settle if settle is not None else self._unsettled_gate_evals(bundle.frame_id),
                )
            raise
        if clock is not None:
            m_end = clock() if newest else m_tm
            self._emit_capture_timing(bundle.frame_id, newest, marks or {}, m_tm, m_end, settle)
        event: str | None = event_override or ("LOST" if not result.ok else None)
        if publication["geo_reject_reason"] is not None:
            event = "GEO_REJECT"
        self._append_record(
            bundle,
            result,
            state=state,
            event=event,
            compute_latency_ms=compute_latency_ms,
            backlog_count=max(0, latest - bundle.frame_id),
            skipped_count=0 if newest else 1,
            publication=publication,
            recovered_from_lost=recovered,
            body_fields=body_fields,
            resident_fields={
                "publish_skip_reason": None if newest else PUBLISH_SKIP_OUTSIDE_WINDOW,
                "resident_publish_window": window,
                "publish_latest_frame_id": publish_latest,
                "capture_projection": None if outcome.projection is None else list(outcome.projection),
                "capture_effect": publication.get("capture"),
                "look_at_kind": publication.get("look_at_kind"),
                "servo_clamped": bool(publication.get("servo_clamped", False)),
                "look_at_rejected": bool(publication.get("look_at_rejected", False)),
            },
        )
        self.state = state
        return state

    # --- P1-ENG-FASTFIX-001 §3.5（G5）：逐阶段耗时（同源会话 monotonic；只进会话日志，不进桥文件） ---------------

    def _capture_clock(self) -> Callable[[], float] | None:
        """捕获钩子提供的会话 monotonic（与帧环、`GatedPublisher` 同源）；兼容/段式路径为 None（不读时钟）。"""
        if self.capture_hook is None:
            return None
        clock = getattr(self.capture_hook, "monotonic", None)
        return clock if callable(clock) else None

    def _load_marks(self, frame_id: int) -> Mapping[str, Any]:
        ring = getattr(self.repository, "ring", None)
        marks = getattr(ring, "load_marks", None) if ring is not None else None
        return dict(marks.get(int(frame_id), {})) if isinstance(marks, Mapping) else {}

    def _emit_capture_timing(
        self, frame_id: int, newest: bool, step_marks: Mapping[str, Any], m_tm: float | None, m_end: float | None,
        settle: Mapping[str, Any] | None,
    ) -> None:
        note = getattr(self.capture_hook, "note_frame_timing", None)
        if not callable(note):
            return
        loaded = self._load_marks(frame_id)
        detector = getattr(self.capture_hook, "detect_return_monotonic", None)
        m_assoc = step_marks.get("m_assoc")
        m_det = self._detect_mark({"m_step0": step_marks.get("m_step0"),
                                   "m_upper": m_assoc if m_assoc is not None else step_marks.get("m_step_end")})
        points = {
            "m_read0": loaded.get("m_read0"), "m_L": loaded.get("m_L"), "m_dec": loaded.get("m_dec"),
            "m_det": m_det, "m_assoc": m_assoc, "m_tm": m_tm, "m_end": m_end,
        }
        note(capture_timing_record(frame_id, newest, points, settle))

    def _ensure_assoc_timing(self, clock: Callable[[], float]) -> None:
        """C1-1：给常驻载体的库关联器 `update` 套实例级计时包装（记返回时刻；不改调用、参数与返回值）。
        关联器尚未创建（载体首帧懒建）时包装其工厂，使首帧也取到边界；替身无关联器 → 不包装，`m_assoc` 缺并带原因。"""
        tracker = self.tracker
        associator = getattr(tracker, "associator", None)
        if associator is not None:
            self._wrap_assoc_update(associator, clock)
            return
        maker = getattr(tracker, "_make_resident_tracker", None)
        if not callable(maker) or getattr(maker, "_fastfix_timed", False):
            return

        def make_timed(*args: Any, **kwargs: Any) -> Any:
            created = maker(*args, **kwargs)
            self._wrap_assoc_update(created, clock)
            return created

        make_timed._fastfix_timed = True  # type: ignore[attr-defined]
        try:
            tracker._make_resident_tracker = make_timed  # type: ignore[attr-defined]
        except AttributeError:
            return

    def _wrap_assoc_update(self, associator: Any, clock: Callable[[], float]) -> None:
        update = getattr(associator, "update", None)
        if not callable(update) or getattr(update, "_fastfix_timed", False):
            return

        def timed_update(*args: Any, **kwargs: Any) -> Any:
            output = update(*args, **kwargs)
            self._assoc_return_m = float(clock())
            return output

        timed_update._fastfix_timed = True  # type: ignore[attr-defined]
        try:
            associator.update = timed_update
        except AttributeError:
            return

    def _step_marks(self, m_step0: float | None, m_upper: float | None) -> dict[str, Any]:
        """本帧 step 区间内的关联返回标记（区间外 = 旧帧残留，不串帧）。"""
        mark = getattr(self, "_assoc_return_m", None)
        ok = mark is not None and m_step0 is not None and m_upper is not None and m_step0 <= mark <= m_upper
        return {"m_step0": m_step0, "m_upper": m_upper, "m_assoc": float(mark) if ok else None}

    def _detect_mark(self, window: Mapping[str, Any]) -> float | None:
        """本帧检测返回标记：只认落在本帧 step 区间 `[m_step0, m_upper]` 内的模型返回时刻（旧帧标记不串帧）。"""
        detector = getattr(self.capture_hook, "detect_return_monotonic", None)
        if not callable(detector):
            return None
        candidate = detector()
        low, high = window.get("m_step0"), window.get("m_upper")
        if candidate is None or low is None or high is None or not (low <= candidate <= high):
            return None
        return float(candidate)

    def _unsettled_gate_evals(self, frame_id: int) -> dict[str, Any] | None:
        """R1-1（AC-9）：结算前上抛（底层观测/云台写失败）时，只读取发布器本帧上下文中已读的门读数；
        不调用 `settle_frame`、不改结算/streak（`outcome` 留 None = 未结算）。"""
        ctx = getattr(self.publisher, "_frame_ctx", None)
        if not isinstance(ctx, Mapping) or ctx.get("frame_id") != int(frame_id):
            return None
        return {"gate_evals": list(ctx.get("gate_evals") or []), "outcome": None}

    def _capture_partial_timing(
        self, frame_id: int, latest: int, missing_reason: str, *, reached: Mapping[str, Any] | None = None,
        settle: Mapping[str, Any] | None = None,
    ) -> None:
        """失败帧：已过标记照记（含 step/管理器/发布中途已到达的 m_det/m_assoc/m_tm），未到达段 null 并附
        `missing_reason`（不计入 §3.4 统计）；`settle` 给出时保留本帧已读门读数 `gate_eval_s`（R1-1）。"""
        clock = self._capture_clock()
        note = getattr(self.capture_hook, "note_frame_timing", None)
        if clock is None or not callable(note):
            return
        loaded = self._load_marks(frame_id)
        got = dict(reached or {})
        points = {"m_read0": loaded.get("m_read0"), "m_L": loaded.get("m_L"), "m_dec": loaded.get("m_dec"),
                  "m_det": got.get("m_det"), "m_assoc": got.get("m_assoc"), "m_tm": got.get("m_tm"), "m_end": None}
        record = capture_timing_record(frame_id, int(frame_id) == int(latest), points, settle)
        record["failed"] = True
        record["missing_reason"] = dict(record.get("missing_reason") or {}, frame=missing_reason)
        note(record)

    def _capture_look_at(self, bundle: FrameBundle, effect: Any, publication: dict[str, Any]) -> None:
        target = tuple(float(v) for v in effect.aim_point_world_m)
        point = servo_clamp(self._servo_baseline(), target, bundle.metadata, self.servo_max_deg_per_frame)
        receipts_before = _receipt_count(self.publisher)
        if effect.gimbal == "predicted":
            predicted = getattr(self.publisher, "predicted_look_at", None)
            if not callable(predicted):
                publication["look_at_rejected"] = True
                return
            predicted(bundle.frame_id, point, valid_until_frame=effect.valid_until_frame)
            written = receipts_before is None or any(
                getattr(item, "channel", None) == "predicted_look_at" and getattr(item, "outcome", None) == "WRITTEN"
                for item in self.publisher.receipts[receipts_before:]
            )
        else:
            self.publisher.look_at(point)
            written = _look_at_written(self.publisher, receipts_before)
        if not written:
            publication["look_at_rejected"] = True
            return
        self.last_servo_point = point
        publication["published_gimbal_command"] = True
        publication["look_at_world_m"] = list(point)
        publication["look_at_kind"] = effect.gimbal
        if point != target:
            publication["servo_clamped"] = True
            note = getattr(self.capture_hook, "note_control_limited", None)
            if callable(note):
                note(effect)

    def _publish_time_latest(self, batch_latest: int) -> int:
        """发布判定用的最新帧：重读与门 ④ 同一个 `latest.json`；读不到或更旧时取批首值（只增不减）。"""
        try:
            current = int(self.repository.latest_frame_id())
        except (FileNotFoundError, KeyError, ValueError, TypeError, OSError):
            return batch_latest
        return max(batch_latest, current)

    def _publish_resident(self, bundle: FrameBundle, result: TrackerResult) -> dict[str, Any]:
        """只发布指针 track：观测 + 最小伺服 `look_at`（相邻指令视线角变化 ≤ `servo_max_deg_per_frame`）。"""
        publication = _empty_publication()
        if not result.ok or result.box_norm is None or result.confidence is None:
            return publication
        self.publisher.observation(bundle.frame_id, self.track_id, result.box_norm, result.confidence)
        publication["published_observation"] = True
        if self.condition == "nadir":
            return publication
        try:
            intersection = box_ground_intersection(
                result.box_norm, bundle.metadata, self.ground_plane_y_m, self.maximum_ground_range_m
            )
        except GeometryRejected as exception:
            publication["geo_reject_reason"] = str(exception)
            return publication
        point = servo_clamp(
            self._servo_baseline(),
            tuple(intersection.point_world_m),  # type: ignore[arg-type]
            bundle.metadata,
            self.servo_max_deg_per_frame,
        )
        receipts_before = _receipt_count(self.publisher)
        self.publisher.look_at(point)
        if not _look_at_written(self.publisher, receipts_before):
            # AC-15 修订 1：限速以「已发」指令为基准——被发布门拒绝（或静音丢弃）的 look_at 不推进基准，
            # 也不记为已发，避免下一条已发指令相对上一条已发指令超过 ω_max/hz。
            publication["look_at_rejected"] = True
            return publication
        self.last_servo_point = point
        publication["published_gimbal_command"] = True
        publication["look_at_world_m"] = list(point)
        if point != tuple(intersection.point_world_m):
            publication["servo_clamped"] = True
        return publication

    def _servo_baseline(self) -> tuple[float, float, float] | None:
        """限速基准 = 上一条实际写入的云台指令（IR-22）。门控发布器记录同一云台通道上最后一条 `WRITTEN`
        的点（含 §3.7 转向 `slew_look_at`，R1-2）；无此记录的直写发布器退回本环最后一条已发 `look_at`。"""
        written = getattr(self.publisher, "last_gimbal_point_world_m", self)
        if written is None or isinstance(written, tuple):
            return written
        return self.last_servo_point

    def _drain_reanchor_events(self) -> None:
        if self.reanchor_runtime is None:
            return
        phase = (
            self._rate_lifecycle.phase
            if self._rate_lifecycle is not None
            else (
                self.qualification_lifecycle.phase
                if self.qualification_lifecycle is not None
                else "measurement"
            )
        )
        for item in self.reanchor_runtime.drain_events():
            self.logger.append(
                {
                    "record_kind": "event",
                    "frame_id": item.frame_id,
                    "phase": phase,
                    "state": self.state,
                    "event": item.event,
                    "reanchor": dict(item.fields),
                    "capture_unix_s": None,
                    "simulation_time_s": None,
                    "capture_monotonic_s": None,
                    "measurement_elapsed_s": self.last_measurement_elapsed_s,
                    "ok": self.state == "TRACKING",
                }
            )

    def _protocol_fields(
        self,
        bundle: FrameBundle,
    ) -> Mapping[str, Any] | None:
        if self._rate_lifecycle is not None:
            return self._rate_lifecycle.record_fields(bundle.metadata)
        if self.qualification_lifecycle is not None:
            return self.qualification_lifecycle.record_fields(bundle.metadata)
        return None

    def _publish_latest(
        self,
        bundle: FrameBundle,
        result: TrackerResult,
        *,
        allow_control: bool = True,
    ) -> dict[str, Any]:
        publication = _empty_publication()
        if not result.ok or result.box_norm is None or result.confidence is None:
            return publication
        self.publisher.observation(
            bundle.frame_id,
            self.track_id,
            result.box_norm,
            result.confidence,
        )
        publication["published_observation"] = True
        if self.condition == "nadir" or not allow_control:
            return publication
        try:
            intersection = box_ground_intersection(
                result.box_norm,
                bundle.metadata,
                self.ground_plane_y_m,
                self.maximum_ground_range_m,
            )
        except GeometryRejected as exception:
            publication["geo_reject_reason"] = str(exception)
            return publication
        self.publisher.look_at(intersection.point_world_m)
        publication["published_gimbal_command"] = True
        publication["look_at_world_m"] = list(intersection.point_world_m)
        return publication

    def _platform_state(self, bundle: FrameBundle) -> PlatformState | None:
        """Build the contract's platform view from v3 frame metadata.

        Returns ``None`` when any required field is missing or non-finite;
        the planner contract then forces ``hold`` (fail-safe (b)). The
        saturation flags are carried by the type but the threshold policy
        never reads them (BC-BODY1-6, review note N3).
        """
        try:
            forward = bundle.metadata["camera_forward_world"]
            position = bundle.metadata["camera_position_world_m"]
            if len(forward) != 3 or len(position) != 3:
                raise ValueError("platform vectors must have three elements")
            return PlatformState(
                frame_id=bundle.frame_id,
                capture_monotonic_s=_metadata_float(
                    bundle.metadata, "capture_monotonic_s"
                ),
                position_world_m=tuple(
                    _finite(position[axis], f"camera_position_world_m[{axis}]")
                    for axis in range(3)
                ),  # type: ignore[arg-type]
                camera_forward_world=tuple(
                    _finite(forward[axis], f"camera_forward_world[{axis}]")
                    for axis in range(3)
                ),  # type: ignore[arg-type]
                gimbal_saturated=bool(
                    bundle.metadata.get("gimbal_saturated", False)
                ),
                tether_saturated=bool(
                    bundle.metadata.get("tether_saturated", False)
                ),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def _body_step(
        self,
        bundle: FrameBundle,
        result: TrackerResult,
    ) -> dict[str, Any] | None:
        """P1-M3-BODY-001 batch 1a-beta per-frame body loop.

        Proposal section 2's branch table, verbatim:

        * ``initialize()`` behaviour is untouched - this method is never
          called there (the one-time ``hold_body()`` stays as it was);
        * a rate or qualification lifecycle owns control, so no body command
          is published (this method returns before any side effect);
        * a frame without an observation publishes ``hold``;
        * a planner ``hold``/``velocity`` decision is published as returned,
          with ``expires_after_s`` frozen at ``2 / capture_hz``;
        * any exception path publishes ``hold`` and is recorded, never
          swallowed;
        * a failed command write triggers exactly one immediate fallback
          ``hold`` (BC-BODY1-20 (a)); if that write also fails, both errors
          are recorded and the run terminates fail closed (BC-BODY1-20 (b)).
          The receiver's expiry fallback is an independent safety net and is
          never a substitute for this one.

        The estimator runs and is logged for both arms; batch 1's threshold
        policy never reads it (BC-M34-3). The step runs on latest frames
        only, mirroring the gimbal publication cadence.
        """
        if self.body_planner is None and self.body_estimator is None:
            return None
        if (
            self.qualification_lifecycle is not None
            or self._rate_lifecycle is not None
        ):
            return None
        fields: dict[str, Any] = {}
        estimate = None
        now_s = 0.0
        try:
            now_s = _metadata_float(bundle.metadata, "capture_monotonic_s")
        except ValueError:
            pass
        if self.body_estimator is not None:
            estimate_fields: dict[str, Any] = {}
            usable = result.ok and result.box_norm is not None
            try:
                if not self.body_estimator.initialized:
                    if usable:
                        estimate = self.body_estimator.initialize(
                            result.box_norm,
                            bundle.metadata,
                            self.ground_plane_y_m,
                            now_s,
                        )
                        estimate_fields["step"] = "initialized"
                    else:
                        estimate_fields["step"] = "awaiting_first_measurement"
                elif usable:
                    try:
                        estimate = self.body_estimator.update(
                            result.box_norm,
                            bundle.metadata,
                            self.ground_plane_y_m,
                            now_s,
                        )
                        estimate_fields["step"] = "fused"
                    except GeometryRejected as exception:
                        estimate = self.body_estimator.advance(now_s)
                        estimate_fields["step"] = "predict_only"
                        estimate_fields["geo_reject_reason"] = str(exception)
                else:
                    estimate = self.body_estimator.advance(now_s)
                    estimate_fields["step"] = "predict_only"
            except (ValueError, GeometryRejected) as exception:
                estimate = None
                estimate_fields["step"] = "error"
                estimate_fields["error"] = str(exception)
            if estimate is not None:
                estimate_fields["mean"] = list(estimate.mean)
                estimate_fields["covariance"] = [
                    list(row) for row in estimate.covariance
                ]
                estimate_fields["valid_at_monotonic_s"] = (
                    estimate.valid_at_monotonic_s
                )
                nis = self.body_estimator.last_nis
                if nis is not None:
                    estimate_fields["nis"] = nis
            fields["world_estimate"] = estimate_fields
        if self.body_planner is None:
            return fields
        planner_fields: dict[str, Any] = {"name": self.body_planner.name}
        assert self.body_expires_after_s is not None
        try:
            if not (result.ok and result.box_norm is not None):
                command = BodyCommand.hold(
                    self.body_expires_after_s, "no_observation"
                )
            else:
                command = self.body_planner.decide(
                    self._platform_state(bundle),
                    estimate,
                    now_s,
                )
        except Exception as exception:  # noqa: BLE001 - branch table row 7
            planner_fields["planner_error"] = repr(exception)
            command = BodyCommand.hold(
                self.body_expires_after_s, "planner_exception"
            )
        # The planner's original request is logged first; the publish outcome
        # is logged separately, so a fallback hold is never recorded as if
        # the original command had been published (BC-BODY1-20 (a)).
        planner_fields["mode"] = command.mode
        planner_fields["reason"] = command.reason
        planner_fields["velocity_world_mps"] = list(command.velocity_world_mps)
        try:
            self.publisher.body_command(command)
            planner_fields["published"] = True
            planner_fields["published_mode"] = command.mode
        except Exception as first_error:  # noqa: BLE001 - fail closed below
            # BC-BODY1-20 (a): a failed body-command write triggers exactly
            # one immediate explicit ``hold`` attempt.
            planner_fields["publish_error"] = repr(first_error)
            fallback = BodyCommand.hold(
                self.body_expires_after_s, "publish_failure_fallback"
            )
            try:
                self.publisher.body_command(fallback)
                planner_fields["published"] = True
                planner_fields["published_mode"] = fallback.mode
                planner_fields["published_reason"] = fallback.reason
            except Exception as second_error:  # noqa: BLE001
                # BC-BODY1-20 (b): both writes failed - keep both errors and
                # terminate the run fail closed. The frame loop appends this
                # frame's record (with these fields) and then the terminal
                # record; no further planner decisions are produced.
                planner_fields["published"] = False
                planner_fields["fallback_error"] = repr(second_error)
                self._body_fail_closed_reason = (
                    "body command publish failed and fallback hold failed: "
                    f"{second_error!r}"
                )
        fields["body_planner"] = planner_fields
        return fields

    def _append_record(
        self,
        bundle: FrameBundle,
        result: TrackerResult,
        *,
        state: str,
        event: str | None,
        compute_latency_ms: float,
        backlog_count: int,
        skipped_count: int,
        publication: Mapping[str, Any],
        recovered_from_lost: bool,
        protocol_fields: Mapping[str, Any] | None = None,
        body_fields: Mapping[str, Any] | None = None,
        resident_fields: Mapping[str, Any] | None = None,
    ) -> None:
        if state not in TRACKING_STATES:
            raise ValueError(f"invalid tracking state {state!r}")
        capture_unix_s = _metadata_float(bundle.metadata, "capture_unix_s")
        frame_age_ms = (time.time() - capture_unix_s) * 1000.0
        record = {
                "frame_id": bundle.frame_id,
                "capture_unix_s": capture_unix_s,
                "simulation_time_s": _metadata_float(
                    bundle.metadata, "simulation_time_s"
                ),
                "box_norm": (
                    list(result.box_norm) if result.box_norm is not None else None
                ),
                "ok": result.ok,
                "confidence": result.confidence,
                "confidence_source": result.confidence_source,
                "state": state,
                "event": event,
                "reason": result.reason,
                "compute_stage": "init" if event == "INIT" else "update",
                "compute_latency_ms": compute_latency_ms,
                "frame_age_ms": frame_age_ms,
                "backlog_count": backlog_count,
                "skipped_count": skipped_count,
                "published_observation": bool(
                    publication["published_observation"]
                ),
                "published_gimbal_command": bool(
                    publication["published_gimbal_command"]
                ),
                "look_at_world_m": publication["look_at_world_m"],
                "geo_reject_reason": publication["geo_reject_reason"],
                "recovered_from_lost": recovered_from_lost,
            }
        if protocol_fields is not None:
            record.update(protocol_fields)
        elif self._rate_lifecycle is None:
            record["phase"] = "measurement"
            record["capture_monotonic_s"] = bundle.metadata.get(
                "capture_monotonic_s"
            )
            record["measurement_elapsed_s"] = (
                _metadata_float(bundle.metadata, "simulation_time_s")
                - (self.initial_simulation_time_s or 0.0)
            )
        else:
            record.update(self._rate_lifecycle.record_fields(bundle.metadata))
        if body_fields is not None:
            # P1-M3-BODY-001 batch 1a-beta: appended keys only; no existing
            # run-log key is changed (backward-compatible schema extension).
            record.update(body_fields)
        if resident_fields is not None:
            # P1-ENG-ACQ-001 AC-15 修订 1：常驻路径追加键（跳过发布原因、发布窗口），既有键不变。
            record.update(resident_fields)
        self.logger.append(record)

    def _record_terminal_error(
        self,
        frame_id: int,
        *,
        event: str,
        reason: str,
    ) -> None:
        self.logger.append(
            {
                "frame_id": frame_id,
                "capture_unix_s": None,
                "simulation_time_s": None,
                "box_norm": None,
                "ok": False,
                "confidence": None,
                "confidence_source": "none",
                "state": "ERROR_REINIT_REQUIRED",
                "event": event,
                "reason": reason,
                "compute_stage": None,
                "compute_latency_ms": None,
                "frame_age_ms": None,
                "backlog_count": 0,
                "skipped_count": 0,
                "published_observation": False,
                "published_gimbal_command": False,
                "look_at_world_m": None,
                "geo_reject_reason": None,
                "recovered_from_lost": False,
                "phase": (
                    self._rate_lifecycle.phase
                    if self._rate_lifecycle is not None
                    else (
                        self.qualification_lifecycle.phase
                        if self.qualification_lifecycle is not None
                        else "measurement"
                    )
                ),
                "capture_monotonic_s": None,
                "measurement_elapsed_s": None,
            }
        )
        self.state = "ERROR_REINIT_REQUIRED"
        self.terminal = True


#: P1-ENG-FASTFIX-001 §3.5：七个同源 monotonic 标记与六个相邻不重叠段（段之和 = `total_s`）。
TIMING_MARKS: tuple[str, ...] = ("m_read0", "m_L", "m_dec", "m_det", "m_assoc", "m_tm", "m_end")
TIMING_SEGMENTS: tuple[tuple[str, str, str], ...] = (
    ("read_s", "m_read0", "m_L"),
    ("decode_s", "m_L", "m_dec"),
    ("detect_s", "m_dec", "m_det"),
    ("associate_s", "m_det", "m_assoc"),
    ("tm_s", "m_assoc", "m_tm"),
    ("publish_s", "m_tm", "m_end"),
)


def capture_timing_record(
    frame_id: int, newest: bool, points: Mapping[str, Any], settle: Mapping[str, Any] | None
) -> dict[str, Any]:
    """§3.5 `frame_timing`：`frame_id`、`batch_position`、六段耗时、`total_s = m_end − m_read0`；旧帧 `publish_s = 0`、
    `publish_attempted = false`；缺标记的段为 null 并在 `missing_reason` 写明（不以 null 免除可测段）。
    `gate_eval_s` = 同帧各次门求值的 `load_elapsed`（与门同源同起点，供 §3.4）。"""
    record: dict[str, Any] = {"frame_id": int(frame_id), "batch_position": "newest" if newest else "backlog"}
    missing: dict[str, str] = {}
    for name, start, end in TIMING_SEGMENTS:
        a, b = points.get(start), points.get(end)
        if a is None or b is None:
            record[name] = None
            missing[name] = f"mark_unavailable:{start if a is None else end}"
        else:
            record[name] = float(b) - float(a)
    first, last = points.get("m_read0"), points.get("m_end")
    record["total_s"] = None if first is None or last is None else float(last) - float(first)
    if record["total_s"] is None:
        missing["total_s"] = "mark_unavailable"
    record["publish_attempted"] = bool(newest)
    record["marks"] = {key: points.get(key) for key in TIMING_MARKS}
    record["gate_eval_s"] = [] if settle is None else list(settle.get("gate_evals") or [])
    record["settle_outcome"] = None if settle is None else settle.get("outcome")
    if missing:
        record["missing_reason"] = missing
    return record


def is_resident_tracker(tracker: Any) -> bool:
    """§3.1：具备 `step` 且声明 `mode == "resident"` 的插件走常驻载体路径。"""
    return callable(getattr(tracker, "step", None)) and getattr(tracker, "mode", None) == "resident"


def _direction(origin: Sequence[float], point: Sequence[float]) -> tuple[float, float, float] | None:
    delta = [float(point[i]) - float(origin[i]) for i in range(3)]
    norm = math.sqrt(sum(v * v for v in delta))
    if not math.isfinite(norm) or norm <= 1e-9:
        return None
    return (delta[0] / norm, delta[1] / norm, delta[2] / norm)


def los_angle_deg(origin: Sequence[float], left: Sequence[float], right: Sequence[float]) -> float:
    a = _direction(origin, left)
    b = _direction(origin, right)
    if a is None or b is None:
        return 0.0
    dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
    return math.degrees(math.acos(dot))


def servo_clamp(
    previous: Sequence[float] | None,
    target: Sequence[float],
    metadata: Mapping[str, Any],
    max_deg: float | None,
) -> tuple[float, float, float]:
    """§3.8 步进限速：相邻指令视线角变化 > 上限时，把指令点沿地面从上次指令点向目标点移动到角变化
    恰为上限处（二分）；≤ 上限或无上次指令时直接指向目标。视线原点取本帧相机位置（平台自身状态）。"""
    target_point = (float(target[0]), float(target[1]), float(target[2]))
    if previous is None or max_deg is None:
        return target_point
    origin = metadata.get("camera_position_world_m")
    if not isinstance(origin, Sequence) or len(origin) != 3:
        return target_point
    if los_angle_deg(origin, previous, target_point) <= max_deg:
        return target_point
    low, high = 0.0, 1.0
    for _ in range(60):
        middle = (low + high) / 2.0
        candidate = tuple(float(previous[i]) + middle * (target_point[i] - float(previous[i])) for i in range(3))
        if los_angle_deg(origin, previous, candidate) <= max_deg:
            low = middle
        else:
            high = middle
    return tuple(float(previous[i]) + low * (target_point[i] - float(previous[i])) for i in range(3))  # type: ignore[return-value]


def _publication_ready_result(result: TrackerResult) -> TrackerResult:
    if not result.ok:
        return TrackerResult.lost(result.reason or "tracker_reported_failure")
    if result.box_norm is None:
        return TrackerResult.lost("missing_tracker_box")
    try:
        clipped = clip_box_norm(result.box_norm)
    except (TypeError, ValueError):
        clipped = None
    if clipped is None:
        return TrackerResult.lost("invalid_tracker_box")
    confidence = result.confidence
    source = result.confidence_source
    if confidence is None:
        confidence = 1.0
        source = "placeholder"
    confidence = float(confidence)
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        return TrackerResult.lost("invalid_tracker_confidence")
    if source not in {"tracker", "placeholder"}:
        return TrackerResult.lost("invalid_confidence_source")
    return TrackerResult(clipped, True, confidence, source, result.reason)


def _receipt_count(publisher: Any) -> int | None:
    receipts = getattr(publisher, "receipts", None)
    return len(receipts) if isinstance(receipts, list) else None


def _look_at_written(publisher: Any, receipts_before: int | None) -> bool:
    """门控发布器（有 `receipts` 收据表）：本次调用新增的收据中有 `look_at` `WRITTEN` 才算已发；
    无收据表的直写发布器写入即返回（写失败抛异常），视为已发。"""
    if receipts_before is None:
        return True
    receipts = getattr(publisher, "receipts")
    return any(
        getattr(item, "channel", None) == "look_at" and getattr(item, "outcome", None) == "WRITTEN"
        for item in receipts[receipts_before:]
    )


def _empty_publication() -> dict[str, Any]:
    return {
        "published_observation": False,
        "published_gimbal_command": False,
        "look_at_world_m": None,
        "geo_reject_reason": None,
    }


def _metadata_float(metadata: Mapping[str, Any], key: str) -> float:
    if key not in metadata:
        raise ValueError(f"frame metadata is missing {key}")
    return _finite(metadata[key], key)


def _finite(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _manifest(
    args: argparse.Namespace,
    tracker: TrackerPlugin,
    run_id: str,
    rate2_session: Mapping[str, Any] | None = None,
    rate3_session: Mapping[str, Any] | None = None,
    reanchor_identity: Mapping[str, Any] | None = None,
    qualification_release_identity: Mapping[str, Any] | None = None,
    body_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    cli_args = {
        key: str(value) if isinstance(value, Path) else value
        for key, value in vars(args).items()
    }
    identity_provider = getattr(tracker, "manifest_identity", None)
    if callable(identity_provider):
        tracker_identity = dict(identity_provider())
    else:
        tracker_identity = {
            "name": tracker.name,
            "backend": tracker.backend,
            "pinned_version": tracker.version,
        }
    manifest = {
        "run_id": run_id,
        "scenario_id": args.scenario_id,
        "condition": args.condition,
        "tracker": tracker_identity,
        "cli_args": cli_args,
        "init": {
            "frame_id": args.init_frame,
            "box_norm": list(args.init_box),
        },
        "track_id": args.track_id,
        "ground_plane_y_m": args.ground_plane_y_m,
        "planned_duration_s": args.planned_duration_s,
    }
    rate_study_values = {
        "rate_hz": args.rate_study_rate_hz,
        "replicate_index": args.rate_study_replicate,
        "replicate_id": args.rate_study_replicate_id,
        "attempt_id": args.rate_study_attempt_id,
        "loop_duration_s": args.loop_duration_s,
        "scenario_config_sha256": args.scenario_config_sha256,
        "init_image_sha256": args.init_image_sha256,
        "reference_image_sha256": args.reference_image_sha256,
        "reference_frame_id": args.reference_frame_id,
        "reference_simulation_time_s": args.reference_simulation_time_s,
    }
    if any(value is not None for value in rate_study_values.values()):
        manifest["rate_study"] = rate_study_values
    if rate2_session is not None:
        manifest["rate2"] = {
            key: rate2_session[key]
            for key in (
                "study_id",
                "run_id",
                "scenario_id",
                "tracker_id",
                "tracker_identity_sha256",
                "model_identity_sha256",
                "init_frame_id",
                "init_image_sha256",
                "hold_route_s_m",
            )
        }
    if rate3_session is not None:
        manifest["rate3"] = {
            key: rate3_session[key]
            for key in (
                "study_id",
                "run_id",
                "scenario_id",
                "tracker_id",
                "tracker_identity_sha256",
                "model_identity_sha256",
                "init_frame_id",
                "init_image_sha256",
                "hold_route_s_m",
                "planned_duration_s",
                "sensor_frame_schema",
                "capture_monotonic_clock_id",
            )
        }
    if reanchor_identity is not None:
        manifest["reanchor"] = dict(reanchor_identity)
    if qualification_release_identity is not None:
        manifest[QUALIFICATION_RELEASE_MANIFEST_KEY] = dict(
            qualification_release_identity
        )
    if body_identity is not None:
        manifest["body_planner"] = dict(body_identity)
    return manifest


def _validate_frame_scenario(bundle: FrameBundle, expected_scenario_id: str) -> None:
    actual = bundle.metadata.get("scenario_id")
    if actual != expected_scenario_id:
        raise ValueError(
            f"initial frame scenario_id {actual!r} does not match "
            f"requested {expected_scenario_id!r}"
        )


def build_standoff_planner(
    body_config: Mapping[str, Any],
    scenario: Mapping[str, Any],
    params: StandoffParams,
    fixed: StandoffFixed,
    *,
    project_root: Path,
) -> StandoffBodyPlanner:
    """P1-ENG-FRAME-001 Part P: assemble ``standoff-band-v1`` (section 3.6).

    Everything except the candidate ``params`` and the section 3.7 ``fixed``
    block is reused verbatim from the frozen BODY-001 config: the fallback
    policy values, ``command.expires_after_s`` and the corridor artifact
    (pinned by hash). The embedded fallback is an unmodified
    ``ThresholdBodyPlanner``; with the tether off it carries no corridor
    prisms (proposal AC-14). The same frozen prisms serve the body-segment
    obstacle query (proposal section 3.4, a read-only second use).
    Shared by ``_build_body_runtime`` and ``tools/frame_follow_replay.py``.
    """
    settings = parse_tether_settings(scenario)
    command = body_config.get("command")
    if not isinstance(command, Mapping):
        raise ValueError("body planner config command must be an object")
    if command.get("contract_version") != BODY_CONTRACT_VERSION:
        raise ValueError("body planner config contract version mismatch")
    expires_after_s = _finite(command.get("expires_after_s"), "expires_after_s")
    if expires_after_s <= 0.0:
        raise ValueError("expires_after_s must be positive")
    gimbal = scenario.get("gimbal")
    if not isinstance(gimbal, Mapping):
        raise ValueError("scenario gimbal must be an object")
    maximum_off_nadir_deg = _finite(
        gimbal.get("maximum_off_nadir_deg"), "gimbal.maximum_off_nadir_deg"
    )
    corridor = body_config.get("corridor")
    if not isinstance(corridor, Mapping):
        raise ValueError("body planner config corridor must be an object")
    corridor_artifact = project_root / str(corridor["artifact_path"])
    if sha256_file(corridor_artifact) != corridor.get("artifact_sha256"):
        raise ValueError("corridor artifact hash does not match the config")
    prisms = load_corridor_prisms(corridor_artifact)
    corridor_radius_m = _finite(
        corridor.get("corridor_nominal_radius_m"),
        "corridor.corridor_nominal_radius_m",
    ) + _finite(corridor.get("clearance_margin_m"), "corridor.clearance_margin_m")
    if abs(corridor_radius_m - fixed.corridor_pad_m) > 1e-12:
        raise ValueError(
            "fixed.corridor_pad_m must equal the BODY-001 corridor radius plus clearance"
        )
    policy = body_config.get("policy")
    if not isinstance(policy, Mapping):
        raise ValueError("body planner config policy must be an object")
    tethered = settings.tether_enabled
    fallback = ThresholdBodyPlanner(
        margin_trigger_deg=_finite(
            policy.get("margin_trigger_deg"), "policy.margin_trigger_deg"
        ),
        margin_release_deg=_finite(
            policy.get("margin_release_deg"), "policy.margin_release_deg"
        ),
        v_cmd_mps=_finite(policy.get("v_cmd_mps"), "policy.v_cmd_mps"),
        expires_after_s=expires_after_s,
        maximum_off_nadir_deg=maximum_off_nadir_deg,
        anchor_world_m=settings.anchor_world_m,
        corridor_prisms=prisms if tethered else None,
        corridor_radius_m=corridor_radius_m if tethered else None,
    )
    fence = settings.geofence
    geometry = StandoffGeometry(
        anchor_world_m=settings.anchor_world_m,
        tether_enabled=tethered,
        tether_length_m=settings.tether_length_m,
        geofence_xz_m=(
            (fence.min_x, fence.max_x, fence.min_z, fence.max_z)
            if fence is not None
            else None
        ),
        maximum_off_nadir_deg=maximum_off_nadir_deg,
    )
    return StandoffBodyPlanner(
        params=params,
        fixed=fixed,
        geometry=geometry,
        expires_after_s=expires_after_s,
        fallback=fallback,
        obstacle_prisms=prisms,
        corridor_prisms=prisms if tethered else None,
    )


def _estimator_from_body_config(
    body_config: Mapping[str, Any], project_root: Path
) -> WorldEstimateFilter:
    """The BODY-001 estimator, priors and calibration reused verbatim."""
    calibration = body_config.get("calibration")
    if not isinstance(calibration, Mapping):
        raise ValueError("body planner config calibration must be an object")
    calibration_artifact = project_root / str(calibration["artifact_path"])
    if sha256_file(calibration_artifact) != calibration.get("artifact_sha256"):
        raise ValueError("calibration artifact hash does not match the config")
    estimator_config = body_config.get("estimator")
    if not isinstance(estimator_config, Mapping):
        raise ValueError("body planner config estimator must be an object")
    return WorldEstimateFilter(
        q_accel_mps2=_finite(
            estimator_config.get("q_accel_mps2"), "estimator.q_accel_mps2"
        ),
        sigma_px=_finite(calibration.get("sigma_px"), "calibration.sigma_px"),
        sigma_att_deg=_finite(
            estimator_config.get("sigma_att_deg"), "estimator.sigma_att_deg"
        ),
        sigma_y_m=_finite(estimator_config.get("sigma_y_m"), "estimator.sigma_y_m"),
        initial_velocity_sigma_mps=_finite(
            estimator_config.get("initial_velocity_sigma_mps"),
            "estimator.initial_velocity_sigma_mps",
        ),
    )


def _build_standoff_runtime(
    config_path: Path,
    scenario_path: Path,
    *,
    scenario_id: str,
    ground_plane_y_m: float,
    runtime: Path | None,
) -> tuple[BodyPlanner, WorldEstimateFilter, float, dict[str, Any]]:
    """P1-ENG-FRAME-001 section 3.8: the ``standoff`` body runtime.

    Fails closed unless the FRAME config (and every hash it pins) loads, the
    explicit ``ground_plane_y_m`` is present and finite, the body scenario
    matches ``--scenario-id``, and the body scenario equals - value for
    value - the scenario Unity will actually load (``effective_scenario_path``:
    the runtime override when present, otherwise
    ``config/scenario.untethered.json``). The whole scenario document is used
    only as a configuration identity binding; the ground plane calibration
    comes solely from the explicit argument, with no default and nothing
    derived from the scenario (AC-22 修订 1).
    """
    project_root = Path(__file__).resolve().parents[1]
    if runtime is None:
        raise ValueError("the standoff body policy needs the runtime directory")
    if ground_plane_y_m is None or isinstance(ground_plane_y_m, bool):
        raise ValueError("the standoff body policy needs an explicit finite ground_plane_y_m")
    try:
        _finite(ground_plane_y_m, "ground_plane_y_m")
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"ground_plane_y_m must be an explicit finite number ({error})"
        ) from error
    frame: FrameBodyConfig = load_frame_body_config(
        Path(config_path), project_root=project_root
    )
    scenario = json.loads(Path(scenario_path).read_text(encoding="utf-8"))
    if scenario.get("schema_version") != "tethered-scenario/v1":
        raise ValueError(
            f"unsupported scenario schema {scenario.get('schema_version')!r}"
        )
    if scenario.get("scenario_id") != scenario_id:
        raise ValueError(
            f"body scenario {scenario.get('scenario_id')!r} does not match "
            f"--scenario-id {scenario_id!r}"
        )
    effective = effective_scenario_path(Path(runtime))
    effective_document = json.loads(effective.read_text(encoding="utf-8"))
    if effective_document != scenario:
        raise ValueError(
            f"body scenario {str(scenario_path)!r} differs from the effective "
            f"scenario Unity loads ({str(effective)!r})"
        )
    planner = build_standoff_planner(
        frame.body_001_config,
        scenario,
        frame.params,
        frame.fixed,
        project_root=project_root,
    )
    estimator = _estimator_from_body_config(frame.body_001_config, project_root)
    expires_after_s = planner.expires_after_s
    bounds = scenario_safety_bounds(parse_tether_settings(scenario))
    bounds.update(
        {
            "command_v_max_mps": frame.fixed.v_max_mps,
            "command_vy_mps": 0.0,
            "obstacle_pad_m": frame.fixed.obstacle_pad_m,
            "corridor_pad_m": (
                frame.fixed.corridor_pad_m if bounds["tether_enabled"] else None
            ),
            "shorten_step_m": frame.fixed.shorten_step_m,
            "min_residual_speed_mps": frame.fixed.min_residual_speed_mps,
            "d_plaus_m": frame.fixed.d_plaus_m,
            "expires_after_s": expires_after_s,
        }
    )
    identity = {
        "policy": "standoff",
        "planner": planner.name,
        "contract_version": BODY_CONTRACT_VERSION,
        "config_path": str(config_path),
        "config_sha256": frame.sha256,
        "selected_candidate": frame.selected_candidate,
        "params": frame.params.as_dict(),
        "fixed": frame.fixed.as_dict(),
        "body_001_config_sha256": frame.body_001_config_sha256,
        "replay_evidence_sha256": frame.replay_evidence_sha256,
        "scenario_config_path": str(scenario_path),
        "scenario_config_sha256": sha256_file(scenario_path),
        "effective_scenario_path": str(effective),
        "effective_scenario_sha256": sha256_file(effective),
        "expires_after_s": expires_after_s,
        "safety_bounds": bounds,
    }
    return planner, estimator, expires_after_s, identity


def _build_body_runtime(
    config_path: Path,
    scenario_path: Path,
    policy_name: str,
    *,
    scenario_id: str,
    ground_plane_y_m: float,
    runtime: Path | None = None,
) -> tuple[BodyPlanner, WorldEstimateFilter, float, dict[str, Any]]:
    """Construct the batch 1a-beta body runtime from the frozen configs.

    Fails closed on any schema, contract, hash or scenario inconsistency; the
    pre-registered policy values are read from ``config/p1-m3-body-001.json``,
    never from CLI arguments. The gimbal limit and the anchor are read from
    the frozen scenario (BC-BODY1-6: referenced, not duplicated).

    P1-ENG-FRAME-001 adds ``standoff``: its config is
    ``config/p1-eng-frame-001-body.json`` and it also needs ``runtime`` for
    the effective-scenario check (section 3.8); ``hold``/``threshold`` are
    unchanged.
    """
    if policy_name == "standoff":
        return _build_standoff_runtime(
            config_path,
            scenario_path,
            scenario_id=scenario_id,
            ground_plane_y_m=ground_plane_y_m,
            runtime=runtime,
        )
    project_root = Path(__file__).resolve().parents[1]
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if config.get("schema_version") != "p1-m3-body-001/v1":
        raise ValueError(
            f"unsupported body planner config schema "
            f"{config.get('schema_version')!r}"
        )
    command = config.get("command")
    if not isinstance(command, Mapping):
        raise ValueError("body planner config command must be an object")
    if command.get("contract_version") != BODY_CONTRACT_VERSION:
        raise ValueError("body planner config contract version mismatch")
    expires_after_s = _finite(command.get("expires_after_s"), "expires_after_s")
    if expires_after_s <= 0.0:
        raise ValueError("expires_after_s must be positive")

    scenario = json.loads(Path(scenario_path).read_text(encoding="utf-8"))
    if scenario.get("schema_version") != "tethered-scenario/v1":
        raise ValueError(
            f"unsupported scenario schema {scenario.get('schema_version')!r}"
        )
    if scenario.get("scenario_id") != scenario_id:
        raise ValueError(
            f"body scenario {scenario.get('scenario_id')!r} does not match "
            f"--scenario-id {scenario_id!r}"
        )
    anchor_raw = scenario.get("anchor_world_m")
    if not isinstance(anchor_raw, Mapping):
        raise ValueError("scenario anchor_world_m must be an object")
    anchor = tuple(
        _finite(anchor_raw.get(axis), f"anchor_world_m.{axis}")
        for axis in ("x", "y", "z")
    )
    gimbal = scenario.get("gimbal")
    if not isinstance(gimbal, Mapping):
        raise ValueError("scenario gimbal must be an object")
    maximum_off_nadir_deg = _finite(
        gimbal.get("maximum_off_nadir_deg"), "gimbal.maximum_off_nadir_deg"
    )
    route = scenario.get("target", {}).get("route_world_m")
    if not isinstance(route, list) or not route:
        raise ValueError("scenario target.route_world_m must be a list")
    for index, point in enumerate(route):
        route_y = _finite(point.get("y"), f"route_world_m[{index}].y")
        if abs(route_y - ground_plane_y_m) > 1e-9:
            raise ValueError(
                "ground_plane_y_m does not match the frozen scenario route "
                f"height (route_world_m[{index}].y = {route_y})"
            )

    calibration = config.get("calibration")
    if not isinstance(calibration, Mapping):
        raise ValueError("body planner config calibration must be an object")
    calibration_artifact = project_root / str(calibration["artifact_path"])
    if sha256_file(calibration_artifact) != calibration.get("artifact_sha256"):
        raise ValueError("calibration artifact hash does not match the config")
    estimator_config = config.get("estimator")
    if not isinstance(estimator_config, Mapping):
        raise ValueError("body planner config estimator must be an object")
    estimator = WorldEstimateFilter(
        q_accel_mps2=_finite(
            estimator_config.get("q_accel_mps2"), "estimator.q_accel_mps2"
        ),
        sigma_px=_finite(calibration.get("sigma_px"), "calibration.sigma_px"),
        sigma_att_deg=_finite(
            estimator_config.get("sigma_att_deg"), "estimator.sigma_att_deg"
        ),
        sigma_y_m=_finite(
            estimator_config.get("sigma_y_m"), "estimator.sigma_y_m"
        ),
        initial_velocity_sigma_mps=_finite(
            estimator_config.get("initial_velocity_sigma_mps"),
            "estimator.initial_velocity_sigma_mps",
        ),
    )

    policy = config.get("policy")
    if not isinstance(policy, Mapping):
        raise ValueError("body planner config policy must be an object")
    if policy_name == "hold":
        planner: BodyPlanner = HoldBodyPlanner(expires_after_s=expires_after_s)
    elif policy_name == "threshold":
        # P1-ENG-FRAME-001 Part T (T5, AC-8): the frozen BODY-001 policy
        # assumes a cable; a tether-off scenario refuses it. A missing switch
        # means tether on, so every existing scenario builds exactly as before.
        if not parse_tether_settings(scenario).tether_enabled:
            raise ValueError(
                "threshold body policy requires a tethered scenario "
                "(drone.tether_enabled is false)"
            )
        corridor = config.get("corridor")
        if not isinstance(corridor, Mapping):
            raise ValueError("body planner config corridor must be an object")
        prisms = None
        corridor_radius_m = None
        if policy.get("tether_corridor_check"):
            corridor_artifact = project_root / str(corridor["artifact_path"])
            if sha256_file(corridor_artifact) != corridor.get("artifact_sha256"):
                raise ValueError(
                    "corridor artifact hash does not match the config"
                )
            prisms = load_corridor_prisms(corridor_artifact)
            corridor_radius_m = _finite(
                corridor.get("corridor_nominal_radius_m"),
                "corridor.corridor_nominal_radius_m",
            ) + _finite(
                corridor.get("clearance_margin_m"),
                "corridor.clearance_margin_m",
            )
        planner = ThresholdBodyPlanner(
            margin_trigger_deg=_finite(
                policy.get("margin_trigger_deg"), "policy.margin_trigger_deg"
            ),
            margin_release_deg=_finite(
                policy.get("margin_release_deg"), "policy.margin_release_deg"
            ),
            v_cmd_mps=_finite(policy.get("v_cmd_mps"), "policy.v_cmd_mps"),
            expires_after_s=expires_after_s,
            maximum_off_nadir_deg=maximum_off_nadir_deg,
            anchor_world_m=anchor,
            corridor_prisms=prisms,
            corridor_radius_m=corridor_radius_m,
        )
    else:
        raise ValueError(f"unsupported body policy {policy_name!r}")
    identity = {
        "policy": policy_name,
        "planner": planner.name,
        "contract_version": BODY_CONTRACT_VERSION,
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "scenario_config_sha256": sha256_file(scenario_path),
        "expires_after_s": expires_after_s,
    }
    return planner, estimator, expires_after_s, identity


def run_tracker(args: argparse.Namespace) -> int:
    if args.rate2_session and args.reanchor_config is not None:
        raise ValueError(
            "detector re-anchor is incompatible with the RATE-002 v2 "
            "process-relative monotonic clock"
        )
    if args.body_policy is not None and (
        args.rate2_session or args.rate3_session or args.qualification_release_barrier
    ):
        # Proposal section 2 branch table: those protocols own body control,
        # so the batch 1a-beta wiring never runs alongside them.
        raise ValueError(
            "body planner wiring is incompatible with the rate-study and "
            "qualification release protocols"
        )
    if args.qualification_release_barrier:
        if args.rate2_session:
            raise ValueError(
                "qualification release barrier is incompatible with RATE-002"
            )
        if args.rate3_session:
            raise ValueError(
                "qualification release barrier is incompatible with RATE-003"
            )
        if args.reanchor_config is None:
            raise ValueError(
                "qualification release barrier requires detector re-anchor"
            )
    runtime = Path(args.runtime).resolve()
    # RATE-003 §1.1(a)：会话校验必须早于模型构造、run 目录创建与任何
    # run 副作用；帧 schema 路由由会话文件声明决定，不用全局常量。
    rate3_session: dict[str, Any] | None = None
    if args.rate3_session:
        _, rate3_session = load_rate3_session(runtime)
        # 复核 round 1 finding 1（BC-R3-1）：CLI 时长必须等于会话冻结值，
        # 否则 manifest 哈希链会携带两个矛盾的 planned_duration_s。
        session_planned = float(rate3_session["planned_duration_s"])
        if abs(float(args.planned_duration_s) - session_planned) > 1e-9:
            raise ValueError(
                "--planned-duration-s does not match the RATE-003 session's "
                f"frozen planned_duration_s ({session_planned})"
            )
    repository = FrameRepository(
        runtime,
        expected_frame_schema=(
            RATE2_FRAME_SCHEMA
            if args.rate2_session
            else (
                rate3_session["sensor_frame_schema"]
                if rate3_session is not None
                else FRAME_SCHEMA
            )
        ),
    )
    initial_bundle = repository.load(args.init_frame)
    _validate_frame_scenario(initial_bundle, args.scenario_id)
    tracker = create_tracker(
        args.tracker,
        nanotrack_spec_path=args.tracker_model_spec,
        nanotrack_model_dir=args.tracker_model_dir,
    )
    reanchor = None
    if args.reanchor_config is not None:
        if args.tracker != "nanotrack-v2":
            raise ValueError("detector re-anchor requires tracker nanotrack-v2")
        from .reanchor_runtime import ReanchorRuntime

        reanchor_config = load_reanchor_config(args.reanchor_config)
        project_root = Path(__file__).resolve().parents[1]
        expected_spec = (
            project_root / str(reanchor_config.tracker_factory["spec"])
        ).resolve()
        expected_model_dir = (
            project_root / str(reanchor_config.tracker_factory["model_dir"])
        ).resolve()
        if (
            Path(args.tracker_model_spec).resolve() != expected_spec
            or Path(args.tracker_model_dir).resolve() != expected_model_dir
        ):
            raise ValueError(
                "reanchor NanoTrack factory arguments differ from the frozen config"
            )
        reanchor = ReanchorRuntime(
            reanchor_config,
            lambda: create_tracker(
                "nanotrack-v2",
                nanotrack_spec_path=args.tracker_model_spec,
                nanotrack_model_dir=args.tracker_model_dir,
            ),
        )
    run_id = args.run_id or (
        f"{args.condition}-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    )
    body_planner: BodyPlanner | None = None
    body_estimator: WorldEstimateFilter | None = None
    body_expires_after_s: float | None = None
    body_identity: dict[str, Any] | None = None
    if args.body_policy is not None:
        (
            body_planner,
            body_estimator,
            body_expires_after_s,
            body_identity,
        ) = _build_body_runtime(
            args.body_planner_config,
            args.body_scenario_config,
            args.body_policy,
            scenario_id=args.scenario_id,
            ground_plane_y_m=args.ground_plane_y_m,
            runtime=runtime,
        )
    rate2_session: dict[str, Any] | None = None
    lifecycle: Rate2TrackerLifecycle | None = None
    if args.rate2_session:
        _, rate2_session = load_rate2_session(runtime)
        init_image_path, _ = repository.frame_paths(args.init_frame)
        identity_provider = getattr(tracker, "manifest_identity", None)
        if not callable(identity_provider):
            raise ValueError("RATE-002 tracker must expose manifest_identity()")
        lifecycle = Rate2TrackerLifecycle(
            runtime,
            rate2_session,
            dict(identity_provider()),
            init_frame_id=args.init_frame,
            init_image_sha256=sha256_file(init_image_path),
            scenario_id=args.scenario_id,
            run_id=run_id,
        )
    rate3_lifecycle: Rate3TrackerLifecycle | None = None
    if args.rate3_session:
        assert rate3_session is not None
        # RATE-003 §1/track_loop.py:795 互斥解除的依据（不是单纯删断言）：
        # rate3 会话把帧 capture、ready、release ack 与 re-anchor 内部单调源
        # 全链路钉死在 system-stopwatch/v1，reanchor 每帧
        # validate_system_monotonic_frame 已成立，v2 时代的时钟互斥不再适用；
        # 但两侧声明时钟必须显式一致，不一致即拒绝。
        if reanchor is not None and (
            reanchor.monotonic_clock_id
            != rate3_session["capture_monotonic_clock_id"]
        ):
            raise ValueError(
                "reanchor monotonic clock identity does not match the "
                "RATE-003 session capture_monotonic_clock_id"
            )
        init_image_path, _ = repository.frame_paths(args.init_frame)
        identity_provider = getattr(tracker, "manifest_identity", None)
        if not callable(identity_provider):
            raise ValueError("RATE-003 tracker must expose manifest_identity()")
        rate3_lifecycle = Rate3TrackerLifecycle(
            runtime,
            rate3_session,
            dict(identity_provider()),
            init_frame_id=args.init_frame,
            init_image_sha256=sha256_file(init_image_path),
            scenario_id=args.scenario_id,
            run_id=run_id,
        )
    logger = RunLogger(
        runtime,
        run_id,
        _manifest(
            args,
            tracker,
            run_id,
            rate2_session,
            rate3_session=rate3_session,
            reanchor_identity=(
                reanchor.manifest_identity() if reanchor is not None else None
            ),
            qualification_release_identity=(
                qualification_release_manifest_identity()
                if args.qualification_release_barrier
                else None
            ),
            body_identity=body_identity,
        ),
    )
    qualification_lifecycle = (
        QualificationReleaseLifecycle(
            runtime,
            run_id,
            scenario_id=args.scenario_id,
            init_frame_id=args.init_frame,
        )
        if args.qualification_release_barrier
        else None
    )
    loop = TrackLoop(
        repository,
        tracker,
        RuntimePublisher(runtime, args.expires_after_s),
        logger,
        track_id=args.track_id,
        condition=args.condition,
        ground_plane_y_m=args.ground_plane_y_m,
        maximum_ground_range_m=args.maximum_ground_range_m,
        planned_duration_s=args.planned_duration_s,
        rate2_lifecycle=lifecycle,
        rate3_lifecycle=rate3_lifecycle,
        reanchor_runtime=reanchor,
        qualification_lifecycle=qualification_lifecycle,
        body_planner=body_planner,
        body_estimator=body_estimator,
        body_expires_after_s=body_expires_after_s,
    )
    exit_code = 0
    try:
        loop.initialize(args.init_frame, args.init_box)
        while not loop.complete:
            loop.process_available()
            if not loop.complete:
                time.sleep(args.poll_interval_s)
        if loop.terminal:
            exit_code = 2
    except KeyboardInterrupt:
        exit_code = 130
    finally:
        worker_closed = True
        if reanchor is not None:
            reanchor.poll()
            worker_closed = reanchor.close()
            reanchor.poll()
            reanchor.emit_summary()
            loop._drain_reanchor_events()
            if not worker_closed:
                exit_code = 3
        metrics_path = runtime / "metrics.json"
        metrics_error: str | None = None
        metrics_snapshotted = False
        if metrics_path.is_file():
            try:
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
                if (
                    isinstance(metrics, dict)
                    and metrics.get("schema_version") == "tethered-evaluation/v1"
                    and metrics.get("scenario_id") == args.scenario_id
                ):
                    if qualification_lifecycle is not None:
                        qualification_lifecycle.validate_metrics(
                            metrics,
                            planned_duration_s=args.planned_duration_s,
                        )
                    logger.snapshot_json("metrics.final.json", metrics)
                    metrics_snapshotted = True
                elif qualification_lifecycle is not None:
                    metrics_error = (
                        "qualification metrics schema/scenario mismatch"
                    )
            except (
                OSError,
                json.JSONDecodeError,
                QualificationProtocolError,
            ) as exception:
                if qualification_lifecycle is not None:
                    metrics_error = str(exception)
        elif qualification_lifecycle is not None:
            metrics_error = "qualification metrics.json is missing"
        if qualification_lifecycle is not None and not metrics_snapshotted:
            exit_code = 4
        summary_path, summary = logger.finalize()
        if (
            qualification_lifecycle is not None
            and metrics_error is None
            and summary["metrics_snapshot_present"]
        ):
            qualification_lifecycle.clear_active_pointer()
        print(
            json.dumps(
                {
                    "run_id": run_id,
                    "summary": str(summary_path),
                    "state": loop.state,
                    "records": summary["total_frame_records"],
                    "qualification_metrics_error": metrics_error,
                },
                sort_keys=True,
            )
        )
    return exit_code


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run or inspect an external SOT tracking session."
    )
    parser.add_argument("--runtime", type=Path, default=RUNTIME)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--finalize", metavar="RUN_ID")
    modes.add_argument("--dump-frame", type=int, metavar="FRAME_ID")
    modes.add_argument("--release-qualification", metavar="RUN_ID")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--tracker",
        choices=("csrt", "nanotrack-v2", "det-assoc-v1"),
        default="csrt",
    )
    parser.add_argument(
        "--tracker-model-spec",
        type=Path,
        default=DEFAULT_NANOTRACK_V2_SPEC,
    )
    parser.add_argument(
        "--tracker-model-dir",
        type=Path,
        default=DEFAULT_NANOTRACK_V2_MODEL_DIR,
    )
    parser.add_argument(
        "--reanchor-config",
        type=Path,
        help=(
            "enable the accepted minimal triple-gated re-anchor carrier; "
            f"default frozen config is {DEFAULT_REANCHOR_CONFIG}"
        ),
    )
    parser.add_argument("--init-frame", type=int)
    parser.add_argument(
        "--init-box",
        type=float,
        nargs=4,
        metavar=("X", "Y", "WIDTH", "HEIGHT"),
    )
    parser.add_argument("--track-id")
    parser.add_argument("--scenario-id")
    parser.add_argument("--condition", choices=("follow", "nadir"))
    parser.add_argument("--ground-plane-y-m", type=float)
    parser.add_argument("--planned-duration-s", type=float)
    parser.add_argument("--run-id")
    parser.add_argument("--rate-study-rate-hz", type=int)
    parser.add_argument("--rate-study-replicate", type=int)
    parser.add_argument("--rate-study-replicate-id")
    parser.add_argument("--rate-study-attempt-id")
    parser.add_argument("--loop-duration-s", type=float)
    parser.add_argument("--scenario-config-sha256")
    parser.add_argument("--init-image-sha256")
    parser.add_argument("--reference-image-sha256")
    parser.add_argument("--reference-frame-id", type=int)
    parser.add_argument("--reference-simulation-time-s", type=float)
    parser.add_argument(
        "--rate2-session",
        action="store_true",
        help="enforce the installed P1-M2-RATE-002 session and v2 frame schema",
    )
    parser.add_argument(
        "--rate3-session",
        action="store_true",
        help=(
            "enforce the installed P1-M2-RATE-003 session, v3 frame schema "
            "and the system-stopwatch/v1 shared clock"
        ),
    )
    parser.add_argument(
        "--qualification-release-barrier",
        action="store_true",
        help=(
            "require the reviewed P1-DETECT qualification release command "
            "and first-live-frame acknowledgement"
        ),
    )
    parser.add_argument("--maximum-ground-range-m", type=float, default=1000.0)
    parser.add_argument("--expires-after-s", type=float, default=1.0)
    parser.add_argument("--poll-interval-s", type=float, default=0.02)
    parser.add_argument(
        "--body-policy",
        choices=("hold", "threshold", "standoff"),
        default=None,
        help=(
            "P1-M3-BODY-001 batch 1a-beta: run the per-frame body loop with "
            "the selected v1 policy (requires --body-planner-config and "
            "--body-scenario-config); P1-ENG-FRAME-001 adds standoff"
        ),
    )
    parser.add_argument(
        "--body-planner-config",
        type=Path,
        help=(
            "frozen P1-M3-BODY-001 config (policy, command, corridor, "
            "estimator); for standoff, config/p1-eng-frame-001-body.json"
        ),
    )
    parser.add_argument(
        "--body-scenario-config",
        type=Path,
        help="frozen scenario the body runtime reads the gimbal limit and anchor from",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    runtime = Path(args.runtime).resolve()
    if args.finalize is not None:
        path, summary = finalize_run(runtime, args.finalize)
        print(json.dumps({"summary": str(path), **summary}, sort_keys=True))
        return
    if args.dump_frame is not None:
        if args.output is None:
            parser.error("--dump-frame requires --output")
        path = FrameRepository(runtime).dump_frame(args.dump_frame, args.output)
        print(path)
        return
    if args.release_qualification is not None:
        path, command = request_qualification_release(
            runtime,
            args.release_qualification,
        )
        print(
            json.dumps(
                {
                    "release_command": str(path),
                    "run_id": command["run_id"],
                    "command_id": command["command_id"],
                    "not_before_capture_monotonic_s": command[
                        "not_before_capture_monotonic_s"
                    ],
                },
                sort_keys=True,
            )
        )
        return

    required = (
        "init_frame",
        "init_box",
        "track_id",
        "scenario_id",
        "condition",
        "ground_plane_y_m",
        "planned_duration_s",
    )
    missing = [f"--{name.replace('_', '-')}" for name in required if getattr(args, name) is None]
    if missing:
        parser.error("tracking run requires " + ", ".join(missing))
    if args.init_frame < 0:
        parser.error("--init-frame must be non-negative")
    if args.poll_interval_s <= 0.0:
        parser.error("--poll-interval-s must be positive")
    if args.expires_after_s <= 0.0:
        parser.error("--expires-after-s must be positive")
    try:
        _finite(args.poll_interval_s, "poll_interval_s")
        _finite(args.expires_after_s, "expires_after_s")
        _finite(args.ground_plane_y_m, "ground_plane_y_m")
        planned_duration_s = _finite(
            args.planned_duration_s, "planned_duration_s"
        )
        maximum_ground_range_m = _finite(
            args.maximum_ground_range_m, "maximum_ground_range_m"
        )
        if planned_duration_s <= 0.0:
            raise ValueError("planned_duration_s must be positive")
        if maximum_ground_range_m <= 0.0:
            raise ValueError("maximum_ground_range_m must be positive")
        if clip_box_norm(args.init_box) is None:
            raise ValueError("init_box must intersect the normalized image")
        if not args.track_id.strip() or not args.scenario_id.strip():
            raise ValueError("track_id and scenario_id must not be empty")
        rate_study_values = {
            "rate_study_rate_hz": args.rate_study_rate_hz,
            "rate_study_replicate": args.rate_study_replicate,
            "rate_study_replicate_id": args.rate_study_replicate_id,
            "rate_study_attempt_id": args.rate_study_attempt_id,
            "loop_duration_s": args.loop_duration_s,
            "scenario_config_sha256": args.scenario_config_sha256,
            "init_image_sha256": args.init_image_sha256,
            "reference_image_sha256": args.reference_image_sha256,
            "reference_frame_id": args.reference_frame_id,
            "reference_simulation_time_s": args.reference_simulation_time_s,
        }
        if any(value is not None for value in rate_study_values.values()):
            missing_rate_values = [
                name
                for name, value in rate_study_values.items()
                if value is None
            ]
            if missing_rate_values:
                raise ValueError(
                    "rate-study manifest metadata is incomplete: "
                    + ", ".join(missing_rate_values)
                )
        if args.rate_study_rate_hz is not None:
            if args.rate_study_rate_hz not in {5, 20}:
                raise ValueError("rate_study_rate_hz must be 5 or 20")
            if args.rate_study_replicate not in {1, 2, 3}:
                raise ValueError("rate_study_replicate must be 1, 2, or 3")
            if not args.rate_study_replicate_id.strip():
                raise ValueError("rate_study_replicate_id must not be empty")
            if not args.rate_study_attempt_id.strip():
                raise ValueError("rate_study_attempt_id must not be empty")
            if _finite(args.loop_duration_s, "loop_duration_s") <= 0.0:
                raise ValueError("loop_duration_s must be positive")
            _finite(
                args.reference_simulation_time_s,
                "reference_simulation_time_s",
            )
            if args.reference_frame_id < 0:
                raise ValueError("reference_frame_id must be non-negative")
            for name in (
                "scenario_config_sha256",
                "init_image_sha256",
                "reference_image_sha256",
            ):
                value = getattr(args, name)
                if not re.fullmatch(r"[0-9a-f]{64}", value):
                    raise ValueError(f"{name} must be a lowercase SHA-256")
        if args.rate2_session and args.rate3_session:
            raise ValueError(
                "--rate2-session and --rate3-session are mutually exclusive"
            )
        if args.rate2_session:
            if args.tracker != "nanotrack-v2":
                raise ValueError("RATE-002 requires tracker nanotrack-v2")
            if args.rate_study_rate_hz is not None:
                raise ValueError(
                    "RATE-002 session cannot use legacy RATE-001 manifest options"
                )
        if args.rate3_session:
            if args.tracker != "nanotrack-v2":
                raise ValueError("RATE-003 requires tracker nanotrack-v2")
            if args.rate_study_rate_hz is not None:
                raise ValueError(
                    "RATE-003 session cannot use legacy RATE-001 manifest options"
                )
        if args.qualification_release_barrier:
            if args.rate2_session:
                raise ValueError(
                    "qualification release barrier is incompatible with RATE-002"
                )
            if args.rate3_session:
                raise ValueError(
                    "qualification release barrier is incompatible with RATE-003"
                )
            if args.reanchor_config is None:
                raise ValueError(
                    "qualification release barrier requires --reanchor-config"
                )
            if args.tracker != "nanotrack-v2":
                raise ValueError(
                    "qualification release barrier requires tracker nanotrack-v2"
                )
            if args.condition != "follow":
                raise ValueError(
                    "qualification release barrier requires follow condition"
                )
            if args.scenario_id != "p1-scene-004":
                raise ValueError(
                    "qualification release barrier requires scenario p1-scene-004"
                )
            if args.run_id is None or not QUALIFICATION_RUN_ID.fullmatch(
                args.run_id
            ):
                raise ValueError(
                    "qualification release barrier requires run_id "
                    "p1-detect-001-qual-N"
                )
            if planned_duration_s < 150.0:
                raise ValueError(
                    "qualification release barrier requires planned duration >= 150 s"
                )
        if args.body_policy is not None:
            if args.body_planner_config is None or args.body_scenario_config is None:
                raise ValueError(
                    "--body-policy requires --body-planner-config and "
                    "--body-scenario-config"
                )
            if (
                args.rate2_session
                or args.rate3_session
                or args.qualification_release_barrier
            ):
                raise ValueError(
                    "body planner wiring is incompatible with the rate-study "
                    "and qualification release protocols"
                )
        elif (
            args.body_planner_config is not None
            or args.body_scenario_config is not None
        ):
            raise ValueError(
                "--body-planner-config/--body-scenario-config require --body-policy"
            )
    except (TypeError, ValueError) as exception:
        parser.error(str(exception))
    raise SystemExit(run_tracker(args))


if __name__ == "__main__":
    main(sys.argv[1:])
