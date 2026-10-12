from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .protocol import atomic_write, finite, latest_frame_bundle, packet
except ImportError:
    from protocol import atomic_write, finite, latest_frame_bundle, packet


def observation(
    frame_id: int,
    x: float,
    y: float,
    width: float,
    height: float,
    track_id: str = "target-0",
    confidence: float = 1.0,
    expires_after_s: float = 2.0,
    runtime: Path | None = None,
):
    if frame_id < 0:
        raise ValueError("frame_id must be non-negative")
    if not track_id:
        raise ValueError("track_id must not be empty")
    box = {
        "x": finite(x, "x"),
        "y": finite(y, "y"),
        "width": finite(width, "width"),
        "height": finite(height, "height"),
    }
    if box["width"] <= 0 or box["height"] <= 0:
        raise ValueError("width and height must be positive")
    if (
        box["x"] < 0.0
        or box["y"] < 0.0
        or box["x"] + box["width"] > 1.0
        or box["y"] + box["height"] > 1.0
    ):
        raise ValueError("bbox must be clipped inside normalized image bounds [0, 1]")
    confidence_value = finite(confidence, "confidence")
    if not 0.0 <= confidence_value <= 1.0:
        raise ValueError("confidence must be in [0, 1]")
    payload = packet(
        "tracking_observation",
        {},
        expires_after_s,
        protocol_name="tethered-tracking-observation/v1",
    )
    payload.pop("command")
    payload["observation"] = {
        "frame_id": int(frame_id),
        "track_id": track_id,
        "bbox_xywh_norm": box,
        "confidence": confidence_value,
    }
    return atomic_write("tracking_observation.json", payload, runtime)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Publish a tracker result using image-clipped normalized top-left "
            "xywh coordinates."
        )
    )
    parser.add_argument("--frame-id", type=int)
    parser.add_argument("--latest", action="store_true", help="use the latest fully published frame id")
    parser.add_argument("--track-id", default="target-0")
    parser.add_argument("--x", type=float, required=True)
    parser.add_argument("--y", type=float, required=True)
    parser.add_argument("--width", type=float, required=True)
    parser.add_argument("--height", type=float, required=True)
    parser.add_argument("--confidence", type=float, default=1.0)
    parser.add_argument("--expires", type=float, default=2.0)
    args = parser.parse_args()
    if args.latest:
        frame_id, _, _ = latest_frame_bundle()
    elif args.frame_id is not None:
        frame_id = args.frame_id
    else:
        parser.error("provide --frame-id or --latest")
    path = observation(
        frame_id,
        args.x,
        args.y,
        args.width,
        args.height,
        args.track_id,
        args.confidence,
        args.expires,
    )
    print(path)


if __name__ == "__main__":
    main()
