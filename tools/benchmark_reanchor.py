from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
import platform
import time
from typing import Any

import numpy as np

from controller.reanchor import DEFAULT_CONFIG, load_reanchor_config
from controller.reanchor_runtime import ReanchorRuntime
from controller.sensor_protocol import (
    SENSOR_FRAME_SCHEMA_V3,
    SYSTEM_MONOTONIC_CLOCK_ID,
)
from controller.trackers import TrackerResult, create_tracker


@dataclass(frozen=True)
class SyntheticFrame:
    frame_id: int
    image: Any
    metadata: dict[str, Any]


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return (
        ordered[lower] * (upper - position)
        + ordered[upper] * (position - lower)
    )


def _image() -> np.ndarray:
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    yy, xx = np.indices((144, 192))
    checker = ((xx // 12 + yy // 12) % 2) * 180 + 50
    image[144:288, 192:384, 0] = checker
    image[144:288, 192:384, 1] = checker[::-1]
    image[144:288, 192:384, 2] = 220
    return image


def _frame(frame_id: int, image: np.ndarray, capture: float) -> SyntheticFrame:
    return SyntheticFrame(
        frame_id,
        image,
        {
            "schema_version": SENSOR_FRAME_SCHEMA_V3,
            "capture_monotonic_clock_id": SYSTEM_MONOTONIC_CLOCK_ID,
            "width": 640,
            "height": 480,
            "capture_monotonic_s": capture,
            "intrinsics_px": {
                "fx": 554.256258,
                "fy": 554.256258,
                "cx": 320.0,
                "cy": 240.0,
            },
            "camera_right_world": [1.0, 0.0, 0.0],
            "camera_up_world": [0.0, 1.0, 0.0],
            "camera_forward_world": [0.0, 0.0, 1.0],
            "camera_rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
        },
    )


def run(frames: int, rate_hz: float) -> dict[str, Any]:
    if frames < 45 or rate_hz <= 0.0:
        raise ValueError("benchmark needs at least 45 frames and a positive rate")
    config = load_reanchor_config(DEFAULT_CONFIG)
    factory = lambda: create_tracker("nanotrack-v2")
    tracker = factory()
    runtime = ReanchorRuntime(config, factory)
    image = _image()
    box = (0.3, 0.3, 0.3, 0.3)
    initial_capture = time.monotonic()
    initial = _frame(0, image, initial_capture)
    started = time.perf_counter()
    if not tracker.init(image, box):
        raise RuntimeError("NanoTrack rejected synthetic initialization")
    runtime.initialize(initial, box)
    initialization_ms = (time.perf_counter() - started) * 1000.0
    latencies: list[float] = []
    result = TrackerResult(box, True, 1.0, "placeholder")
    next_frame = time.monotonic()
    for frame_id in range(1, frames + 1):
        next_frame += 1.0 / rate_hz
        delay = next_frame - time.monotonic()
        if delay > 0.0:
            time.sleep(delay)
        bundle = _frame(frame_id, image, time.monotonic())
        started = time.perf_counter()
        replacement = runtime.before_update(
            frame_id - 1,
            old_tracker_instance_id=id(tracker),
        )
        if replacement is not None:
            tracker = replacement
        result = tracker.update(image)
        runtime.after_frame(bundle, result, released=True)
        runtime.poll()
        latencies.append((time.perf_counter() - started) * 1000.0)
        if runtime.fatal_reason:
            raise RuntimeError(runtime.fatal_reason)
    deadline = time.monotonic() + float(config.parameters["worker_timeout_s"])
    while runtime.worker.busy and time.monotonic() < deadline:
        time.sleep(0.01)
        runtime.poll()
    runtime.poll()
    worker_closed = runtime.close()
    runtime.poll()
    runtime.emit_summary()
    events = runtime.drain_events()
    detector_latencies = [
        float(event.fields["detector_latency_ms"])
        for event in events
        if isinstance(event.fields.get("detector_latency_ms"), (int, float))
    ]
    appearance_gate_latencies = [
        float(event.fields["appearance_gate_latency_ms"])
        for event in events
        if isinstance(event.fields.get("appearance_gate_latency_ms"), (int, float))
    ]
    worker_latencies = [
        float(event.fields["worker_latency_ms"])
        for event in events
        if isinstance(event.fields.get("worker_latency_ms"), (int, float))
    ]
    replay_latencies = [
        float(event.fields["replay_latency_ms"])
        for event in events
        if isinstance(event.fields.get("replay_latency_ms"), (int, float))
    ]
    summary = next(
        (dict(event.fields) for event in reversed(events) if event.event == "REANCHOR_CHANNEL_SUMMARY"),
        {},
    )
    return {
        "schema_version": "p1-detect-001-synthetic-benchmark/v1",
        "synthetic_only": True,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "config_sha256": config.sha256,
        "frames": frames,
        "rate_hz": rate_hz,
        "initialization_ms": initialization_ms,
        "main_loop_latency_ms": {
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
            "max": max(latencies),
        },
        "detector_latency_ms": detector_latencies,
        "appearance_gate_latency_ms": appearance_gate_latencies,
        "worker_latency_ms": worker_latencies,
        "replay_latency_ms": replay_latencies,
        "worker_closed": worker_closed,
        "fatal_reason": runtime.fatal_reason,
        "channel": summary,
        "events": [event.event for event in events],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the P1-DETECT-001 implementation benchmark on synthetic pixels only."
    )
    parser.add_argument("--frames", type=int, default=60)
    parser.add_argument("--rate-hz", type=float, default=20.0)
    args = parser.parse_args()
    print(json.dumps(run(args.frames, args.rate_hz), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
