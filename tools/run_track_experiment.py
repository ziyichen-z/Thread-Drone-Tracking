from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

from controller.trackers import (
    DEFAULT_NANOTRACK_V2_MODEL_DIR,
    DEFAULT_NANOTRACK_V2_SPEC,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIO = PROJECT_ROOT / "config" / "scenario.untethered.json"
DEFAULT_RUNTIME = PROJECT_ROOT / "runtime"


def _finite(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def load_scenario(path: Path) -> dict[str, Any]:
    scenario = json.loads(Path(path).read_text(encoding="utf-8"))
    if scenario.get("schema_version") != "tethered-scenario/v1":
        raise ValueError(
            f"unsupported scenario schema {scenario.get('schema_version')!r}"
        )
    return scenario


def two_loop_duration_s(scenario: Mapping[str, Any]) -> float:
    return route_timing_s(scenario)["planned_duration_s"]


def route_timing_s(scenario: Mapping[str, Any]) -> dict[str, float]:
    target = scenario.get("target")
    if not isinstance(target, Mapping):
        raise ValueError("scenario target must be an object")
    speed = _finite(target.get("speed_mps"), "target.speed_mps")
    if speed <= 0.0:
        raise ValueError("target.speed_mps must be positive")
    raw_route = target.get("route_world_m")
    if not isinstance(raw_route, list) or len(raw_route) < 2:
        raise ValueError("target.route_world_m must contain at least two points")
    route: list[tuple[float, float, float]] = []
    for index, point in enumerate(raw_route):
        if not isinstance(point, Mapping):
            raise ValueError(f"target.route_world_m[{index}] must be an object")
        route.append(
            (
                _finite(point.get("x"), f"route[{index}].x"),
                _finite(point.get("y"), f"route[{index}].y"),
                _finite(point.get("z"), f"route[{index}].z"),
            )
        )
    perimeter = 0.0
    for start, end in zip(route, route[1:] + route[:1]):
        perimeter += math.sqrt(
            sum((end[axis] - start[axis]) ** 2 for axis in range(3))
        )
    if perimeter <= 0.0:
        raise ValueError("target route perimeter must be positive")
    loop_duration_s = perimeter / speed
    return {
        "route_perimeter_m": perimeter,
        "loop_duration_s": loop_duration_s,
        "planned_duration_s": 2.0 * loop_duration_s + 60.0,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tracker_command(
    *,
    python_executable: Path,
    runtime: Path,
    init_frame: int,
    init_box: Sequence[float],
    track_id: str,
    scenario_id: str,
    condition: str,
    ground_plane_y_m: float,
    planned_duration_s: float,
    run_id: str | None,
    tracker: str = "csrt",
    tracker_model_spec: Path = DEFAULT_NANOTRACK_V2_SPEC,
    tracker_model_dir: Path = DEFAULT_NANOTRACK_V2_MODEL_DIR,
    rate_study: Mapping[str, Any] | None = None,
) -> list[str]:
    command = [
        str(python_executable),
        "-m",
        "controller.track_loop",
        "--runtime",
        str(runtime),
        "--tracker",
        tracker,
        "--init-frame",
        str(init_frame),
        "--init-box",
        *(str(value) for value in init_box),
        "--track-id",
        track_id,
        "--scenario-id",
        scenario_id,
        "--condition",
        condition,
        "--ground-plane-y-m",
        str(ground_plane_y_m),
        "--planned-duration-s",
        str(planned_duration_s),
    ]
    if tracker == "nanotrack-v2":
        command.extend(
            (
                "--tracker-model-spec",
                str(tracker_model_spec),
                "--tracker-model-dir",
                str(tracker_model_dir),
            )
        )
    if run_id:
        command.extend(("--run-id", run_id))
    if rate_study:
        option_names = {
            "rate_hz": "--rate-study-rate-hz",
            "replicate_index": "--rate-study-replicate",
            "replicate_id": "--rate-study-replicate-id",
            "attempt_id": "--rate-study-attempt-id",
            "loop_duration_s": "--loop-duration-s",
            "scenario_config_sha256": "--scenario-config-sha256",
            "init_image_sha256": "--init-image-sha256",
            "reference_image_sha256": "--reference-image-sha256",
            "reference_frame_id": "--reference-frame-id",
            "reference_simulation_time_s": "--reference-simulation-time-s",
        }
        for key, option in option_names.items():
            value = rate_study.get(key)
            if value is not None:
                command.extend((option, str(value)))
    return command


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compute the deterministic two-loop duration outside perception "
            "and launch the accepted P1-TRACK-001 baseline."
        )
    )
    parser.add_argument("--scenario-config", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument(
        "--tracker",
        choices=("csrt", "nanotrack-v2"),
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
    parser.add_argument("--init-frame", type=int, required=True)
    parser.add_argument(
        "--init-box",
        type=float,
        nargs=4,
        required=True,
        metavar=("X", "Y", "WIDTH", "HEIGHT"),
    )
    parser.add_argument("--track-id", required=True)
    parser.add_argument("--condition", choices=("follow", "nadir"), required=True)
    parser.add_argument("--ground-plane-y-m", type=float, required=True)
    parser.add_argument("--run-id")
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="print the truth-isolated tracker command without executing it",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    if args.init_frame < 0:
        parser.error("--init-frame must be non-negative")
    if not args.track_id.strip():
        parser.error("--track-id must not be empty")
    ground_plane_y_m = _finite(args.ground_plane_y_m, "ground_plane_y_m")
    if not all(math.isfinite(value) for value in args.init_box):
        parser.error("--init-box values must be finite")
    if args.init_box[2] <= 0.0 or args.init_box[3] <= 0.0:
        parser.error("--init-box width and height must be positive")
    scenario = load_scenario(args.scenario_config)
    scenario_id = scenario.get("scenario_id")
    if not isinstance(scenario_id, str) or not scenario_id.strip():
        raise ValueError("scenario_id must be a non-empty string")
    timing = route_timing_s(scenario)
    planned_duration_s = timing["planned_duration_s"]
    command = tracker_command(
        python_executable=args.python,
        runtime=args.runtime.resolve(),
        init_frame=args.init_frame,
        init_box=args.init_box,
        track_id=args.track_id,
        scenario_id=scenario_id,
        condition=args.condition,
        ground_plane_y_m=ground_plane_y_m,
        planned_duration_s=planned_duration_s,
        run_id=args.run_id,
        tracker=args.tracker,
        tracker_model_spec=args.tracker_model_spec,
        tracker_model_dir=args.tracker_model_dir,
    )
    print(
        json.dumps(
            {
                "scenario_id": scenario_id,
                "condition": args.condition,
                "planned_duration_s": planned_duration_s,
                "loop_duration_s": timing["loop_duration_s"],
                "scenario_config_sha256": sha256_file(args.scenario_config),
                "command": command,
            },
            indent=2,
        )
    )
    if args.print_only:
        return
    completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
