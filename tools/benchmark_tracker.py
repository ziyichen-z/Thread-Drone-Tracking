from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import time
from typing import Sequence

from controller.trackers import (
    DEFAULT_NANOTRACK_V2_MODEL_DIR,
    DEFAULT_NANOTRACK_V2_SPEC,
    NanoTrackV2Tracker,
)


def percentile(values: Sequence[float], percentile_value: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0.0 <= percentile_value <= 100.0:
        raise ValueError("percentile must be in [0, 100]")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * percentile_value / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def synthetic_frame(width: int, height: int):
    import cv2
    import numpy as np

    image = np.zeros((height, width, 3), dtype=np.uint8)
    tile = max(8, min(width, height) // 24)
    for row in range(0, height, tile):
        for column in range(0, width, tile):
            value = 35 + ((row // tile + column // tile) % 2) * 25
            image[row : row + tile, column : column + tile] = value
    left = width * 3 // 8
    top = height * 3 // 8
    right = width * 5 // 8
    bottom = height * 5 // 8
    cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), -1)
    cv2.line(image, (left, top), (right, bottom), (255, 255, 255), 3)
    return image


def benchmark(
    *,
    spec_path: Path,
    model_dir: Path,
    width: int,
    height: int,
    warmup_updates: int,
    measured_updates: int,
) -> dict:
    if width <= 0 or height <= 0:
        raise ValueError("image dimensions must be positive")
    if warmup_updates < 0 or measured_updates <= 0:
        raise ValueError("warmup must be non-negative and measured updates positive")
    frame = synthetic_frame(width, height)
    tracker = NanoTrackV2Tracker(
        spec_path=spec_path,
        model_dir=model_dir,
    )
    if not tracker.init(frame, (0.375, 0.375, 0.25, 0.25)):
        raise RuntimeError("NanoTrack-v2 benchmark initialization failed")
    for _ in range(warmup_updates):
        result = tracker.update(frame)
        if not result.ok:
            raise RuntimeError(f"warm-up update failed: {result.reason}")
    latencies_ms: list[float] = []
    for _ in range(measured_updates):
        started = time.perf_counter()
        result = tracker.update(frame)
        latencies_ms.append((time.perf_counter() - started) * 1000.0)
        if not result.ok:
            raise RuntimeError(f"measured update failed: {result.reason}")
    identity = tracker.manifest_identity()
    p95_ms = percentile(latencies_ms, 95.0)
    return {
        "schema_version": "p1-tracker-benchmark/v1",
        "tracker": identity,
        "image": {
            "source": "deterministic-synthetic",
            "width": width,
            "height": height,
        },
        "warmup_updates": warmup_updates,
        "measured_updates": measured_updates,
        "compute_latency_ms": {
            "minimum": min(latencies_ms),
            "mean": sum(latencies_ms) / len(latencies_ms),
            "p50": percentile(latencies_ms, 50.0),
            "p95": p95_ms,
            "maximum": max(latencies_ms),
        },
        "acceptance": {
            "p95_limit_ms": 50.0,
            "p95_below_limit": p95_ms < 50.0,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure standalone NanoTrack-v2 CPU update latency."
    )
    parser.add_argument("--spec", type=Path, default=DEFAULT_NANOTRACK_V2_SPEC)
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=DEFAULT_NANOTRACK_V2_MODEL_DIR,
    )
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--warmup-updates", type=int, default=20)
    parser.add_argument("--measured-updates", type=int, default=100)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    result = benchmark(
        spec_path=args.spec,
        model_dir=args.model_dir,
        width=args.width,
        height=args.height,
        warmup_updates=args.warmup_updates,
        measured_updates=args.measured_updates,
    )
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if not result["acceptance"]["p95_below_limit"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
