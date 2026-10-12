from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .protocol import atomic_write, finite, packet
except ImportError:
    from protocol import atomic_write, finite, packet


def look_at(
    x: float,
    z: float,
    y: float = 0.0,
    expires_after_s: float = 2.0,
    runtime: Path | None = None,
):
    return atomic_write("gimbal_command.json", packet("gimbal", {
        "mode": "look_at_world",
        "target_world_m": {
            "x": finite(x, "x"), "y": finite(y, "y"), "z": finite(z, "z")},
    }, expires_after_s), runtime)


def nadir(expires_after_s: float = 2.0, runtime: Path | None = None):
    return atomic_write(
        "gimbal_command.json",
        packet("gimbal", {"mode": "nadir"}, expires_after_s),
        runtime,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("look-at", "nadir"), required=True)
    parser.add_argument("--x", type=float)
    parser.add_argument("--y", type=float, default=0.0)
    parser.add_argument("--z", type=float)
    parser.add_argument("--expires", type=float, default=2.0)
    args = parser.parse_args()
    if args.mode == "look-at":
        if args.x is None or args.z is None:
            parser.error("look-at requires --x and --z")
        path = look_at(args.x, args.z, args.y, args.expires)
    else:
        path = nadir(args.expires)
    print(path)


if __name__ == "__main__":
    main()
