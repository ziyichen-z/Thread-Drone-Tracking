from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .protocol import atomic_write, finite, packet
except ImportError:
    from protocol import atomic_write, finite, packet


def velocity(
    vx: float,
    vz: float,
    vy: float = 0.0,
    expires_after_s: float = 0.5,
    runtime: Path | None = None,
):
    return atomic_write("body_command.json", packet("body", {
        "mode": "velocity_world",
        "velocity_world_mps": {
            "x": finite(vx, "vx"),
            "y": finite(vy, "vy"),
            "z": finite(vz, "vz"),
        },
    }, expires_after_s), runtime)


def hold(expires_after_s: float = 2.0, runtime: Path | None = None):
    return atomic_write(
        "body_command.json",
        packet("body", {"mode": "hold"}, expires_after_s),
        runtime,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("velocity", "hold"), required=True)
    parser.add_argument("--vx", type=float, default=0.0)
    parser.add_argument("--vy", type=float, default=0.0)
    parser.add_argument("--vz", type=float, default=0.0)
    parser.add_argument("--expires", type=float, default=0.5)
    args = parser.parse_args()
    path = velocity(args.vx, args.vz, args.vy, args.expires) if args.mode == "velocity" else hold(args.expires)
    print(path)


if __name__ == "__main__":
    main()
