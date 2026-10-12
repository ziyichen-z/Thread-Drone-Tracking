"""P1-M2-RATE-003 §1.2 clock-smoke orchestrator.

Dedicated non-measurement identity ``rs3-clock-smoke`` /
``P1-M2-RATE-003-CLOCKSMOKE``.  It proves the v3 shared-clock contract
end to end without consuming any research-data identity and never
computes or reports C_track/C_geom.  No attempt limit applies.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

from controller import rate3_protocol
from controller.rate2_protocol import (
    IDENTITY_KEYS,
    Rate2ProtocolError,
    atomic_bytes,
    atomic_json,
    canonical_json_bytes,
    create_once_json,
    identity_hashes,
    latest_frame_id,
    read_json_bytes,
    sha256_file,
)
from controller.run_log import read_frame_records
from controller.trackers import (
    DEFAULT_NANOTRACK_V2_MODEL_DIR,
    DEFAULT_NANOTRACK_V2_SPEC,
)
from tools.run_rate2_study import SLOT_DIRECTORIES, SLOT_FILES
from tools.run_rate_study import _validate_box
from tools.run_track_experiment import PROJECT_ROOT, tracker_command


RUNTIME_DEFAULT = PROJECT_ROOT / "runtime"
DEFAULT_REANCHOR_CONFIG = PROJECT_ROOT / "config" / "detector-reanchor.models.json"
COORDINATOR_FAILURE_SCHEMA = "p1-rate3-coordinator-failure/v1"
RELEASE_POLL_INTERVAL_S = 0.005
SCENARIO_ID = "p1-scene-004"
SESSION_FILE = "rate_study_session.json"


def archive_root(runtime: Path) -> Path:
    return Path(runtime) / "rate-study" / rate3_protocol.CLOCK_SMOKE_STUDY_ID


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be finite")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _read_object(path: Path) -> dict[str, Any]:
    _, value = read_json_bytes(path)
    return value


def _require_clock_smoke_session(session: Mapping[str, Any]) -> None:
    if session.get("study_id") != rate3_protocol.CLOCK_SMOKE_STUDY_ID:
        raise ValueError(
            "clock-smoke orchestrator only drives the "
            f"{rate3_protocol.CLOCK_SMOKE_STUDY_ID} identity"
        )
    if session.get("run_id") != rate3_protocol.CLOCK_SMOKE_RUN_ID:
        raise ValueError(
            "clock-smoke orchestrator only drives run "
            f"{rate3_protocol.CLOCK_SMOKE_RUN_ID}"
        )


def _load_clock_smoke_session(runtime: Path) -> dict[str, Any]:
    _, session = rate3_protocol.load_session(runtime)
    _require_clock_smoke_session(session)
    return session


def build_clock_smoke_session(
    *,
    init_frame_id: int,
    init_image_sha256: str,
    hold_route_s_m: float,
    tracker_identity: Mapping[str, Any],
) -> dict[str, Any]:
    tracker_hash, model_hash = identity_hashes(tracker_identity)
    session = {
        "schema_version": rate3_protocol.SESSION_SCHEMA,
        "study_id": rate3_protocol.CLOCK_SMOKE_STUDY_ID,
        "run_id": rate3_protocol.CLOCK_SMOKE_RUN_ID,
        "scenario_id": SCENARIO_ID,
        "tracker_id": rate3_protocol.TRACKER_ID,
        "tracker_identity_sha256": tracker_hash,
        "model_identity_sha256": model_hash,
        "init_frame_id": int(init_frame_id),
        "init_image_sha256": init_image_sha256,
        "hold_route_s_m": _finite(hold_route_s_m, "hold_route_s_m"),
        "minimum_ready_seq": 20,
        "minimum_processed_frames": 20,
        "planned_duration_s": rate3_protocol.CLOCK_SMOKE_PLANNED_DURATION_S,
        "sensor_frame_schema": rate3_protocol.SENSOR_SCHEMA,
        "capture_monotonic_clock_id": rate3_protocol.CLOCK_ID,
    }
    return rate3_protocol.validate_session(session)


def prepare_session(
    runtime: Path,
    session: Mapping[str, Any],
) -> dict[str, Any]:
    runtime = Path(runtime)
    validated = rate3_protocol.validate_session(session)
    _require_clock_smoke_session(validated)
    # 会话/研究互斥：任何研究数据身份（B1 session 或研究 run 目录痕迹）
    # 存在即 fail-closed。
    session_path = runtime / SESSION_FILE
    if session_path.is_file():
        existing = _read_object(session_path)
        if existing.get("study_id") != rate3_protocol.CLOCK_SMOKE_STUDY_ID:
            raise FileExistsError(
                "a research RATE-003 session is already installed; "
                "clock-smoke and research identities are mutually exclusive"
            )
    research_runs = sorted(
        path.name
        for path in (runtime / "runs").glob("rs3-*")
        if path.is_dir() and path.name != rate3_protocol.CLOCK_SMOKE_RUN_ID
    )
    if research_runs:
        raise FileExistsError(
            "research RATE-003 run directories are present; clock-smoke and "
            "research identities are mutually exclusive: "
            + ", ".join(research_runs)
        )
    if (runtime / "runs" / rate3_protocol.CLOCK_SMOKE_RUN_ID).exists():
        raise FileExistsError(
            f"run directory already exists: {rate3_protocol.CLOCK_SMOKE_RUN_ID}"
        )
    stale = [name for name in SLOT_FILES if (runtime / name).exists()]
    stale.extend(
        f"{name}/" for name in SLOT_DIRECTORIES if (runtime / name).exists()
    )
    if stale:
        raise FileExistsError(
            "stale runtime slots must be archived/removed before prepare: "
            + ", ".join(stale)
        )
    create_once_json(session_path, validated)
    return _read_object(session_path)


def clock_smoke_tracker_command(
    *,
    python_executable: Path,
    runtime: Path,
    init_box: Sequence[float],
    ground_plane_y_m: float,
    reanchor_config: Path = DEFAULT_REANCHOR_CONFIG,
    tracker_model_spec: Path = DEFAULT_NANOTRACK_V2_SPEC,
    tracker_model_dir: Path = DEFAULT_NANOTRACK_V2_MODEL_DIR,
) -> list[str]:
    session = _load_clock_smoke_session(runtime)
    box = _validate_box(init_box)
    command = tracker_command(
        python_executable=python_executable,
        runtime=Path(runtime).resolve(),
        init_frame=int(session["init_frame_id"]),
        init_box=box,
        track_id="target-0",
        scenario_id=SCENARIO_ID,
        condition="follow",
        ground_plane_y_m=ground_plane_y_m,
        planned_duration_s=rate3_protocol.CLOCK_SMOKE_PLANNED_DURATION_S,
        run_id=rate3_protocol.CLOCK_SMOKE_RUN_ID,
        tracker=rate3_protocol.TRACKER_ID,
        tracker_model_spec=tracker_model_spec,
        tracker_model_dir=tracker_model_dir,
    )
    command.append("--rate3-session")
    command.extend(("--reanchor-config", str(reanchor_config)))
    return command


def launch_tracker(
    *,
    python_executable: Path,
    runtime: Path,
    init_box: Sequence[float],
    ground_plane_y_m: float,
    reanchor_config: Path = DEFAULT_REANCHOR_CONFIG,
) -> subprocess.CompletedProcess[str]:
    command = clock_smoke_tracker_command(
        python_executable=python_executable,
        runtime=runtime,
        init_box=init_box,
        ground_plane_y_m=ground_plane_y_m,
        reanchor_config=reanchor_config,
    )
    return subprocess.run(command, cwd=PROJECT_ROOT, text=True, check=False)


def _coordinator_failure(
    runtime: Path,
    session: Mapping[str, Any],
    *,
    stage: str,
    reason: str,
) -> None:
    atomic_json(
        Path(runtime) / "release_coordinator_failure.json",
        {
            "schema_version": COORDINATOR_FAILURE_SCHEMA,
            "study_id": session["study_id"],
            "run_id": session["run_id"],
            "stage": stage,
            "reason": reason,
            "failed_unix_s": time.time(),
        },
    )


def coordinate_release(
    runtime: Path,
    *,
    confirmed: bool,
    timeout_s: float = 10.0,
    poll_interval_s: float = RELEASE_POLL_INTERVAL_S,
    monotonic: Any = time.monotonic,
    sleeper: Any = time.sleep,
    command_id: str | None = None,
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("release requires completed operator confirmation")
    runtime = Path(runtime)
    session = _load_clock_smoke_session(runtime)
    run_directory = runtime / "runs" / rate3_protocol.CLOCK_SMOKE_RUN_ID
    if not (run_directory / "manifest.json").is_file():
        raise FileNotFoundError("tracker run manifest is not available")
    timeout = _finite(timeout_s, "timeout_s")
    poll = _finite(poll_interval_s, "poll_interval_s")
    if timeout <= 0.0 or poll <= 0.0:
        raise ValueError("timeout and poll interval must be positive")
    deadline = monotonic() + timeout
    previous_seq = -1
    ready_bytes: bytes | None = None
    last_ready_error = "tracker_ready_unavailable"
    while monotonic() < deadline:
        try:
            candidate_bytes, ready, observed_frame_id = (
                rate3_protocol.read_consistent_ready(
                    runtime,
                    session,
                    previous_seq=previous_seq,
                    now_monotonic_s=monotonic(),
                )
            )
            ready_seq = int(ready["seq"])
            ready_frame_id = int(ready["last_processed_frame_id"])
            if previous_seq < 0:
                previous_seq = ready_seq
            elif (
                observed_frame_id == ready_frame_id
                and latest_frame_id(runtime) == ready_frame_id
            ):
                ready_bytes = candidate_bytes
                break
            else:
                previous_seq = ready_seq
                last_ready_error = (
                    "tracker-ready has no zero-backlog command-transport budget"
                )
        except (FileNotFoundError, Rate2ProtocolError) as exception:
            last_ready_error = f"{type(exception).__name__}:{exception}"
        sleeper(poll)
    if ready_bytes is None:
        _coordinator_failure(
            runtime,
            session,
            stage="ready_prefilter",
            reason=last_ready_error,
        )
        raise TimeoutError("no fresh advancing tracker-ready heartbeat")
    command_bytes = rate3_protocol.build_release_command(
        session,
        ready_bytes,
        command_id=command_id or f"rate3-release-{time.time_ns()}",
    )
    atomic_bytes(runtime / "experiment_control.json", command_bytes)
    deadline = monotonic() + timeout
    ack_path = runtime / "release_ack.json"
    accepted_path = runtime / "release_command.accepted.json"
    while monotonic() < deadline:
        if ack_path.is_file() and accepted_path.is_file():
            try:
                accepted_bytes = accepted_path.read_bytes()
                if accepted_bytes != command_bytes:
                    raise Rate2ProtocolError(
                        "Unity accepted command bytes differ from coordinator command"
                    )
                ack_bytes = ack_path.read_bytes()
                ack = rate3_protocol.validate_release_bundle(
                    command_bytes, ack_bytes, session
                )
                provenance = rate3_protocol.archive_release_provenance(
                    runtime,
                    run_directory,
                    session,
                )
                return {
                    "command_id": ack["command_id"],
                    "release_frame_id": ack["release_frame_id"],
                    "accepted_backlog_frames": ack["accepted_backlog_frames"],
                    "release_monotonic_s": ack["release_monotonic_s"],
                    "release_clock_id": ack["release_clock_id"],
                    "provenance": provenance,
                }
            except (OSError, ValueError, Rate2ProtocolError) as exception:
                _coordinator_failure(
                    runtime,
                    session,
                    stage="ack_validation",
                    reason=f"{type(exception).__name__}:{exception}",
                )
                raise
        sleeper(poll)
    _coordinator_failure(
        runtime,
        session,
        stage="ack_wait",
        reason="release_ack_timeout",
    )
    raise TimeoutError("Unity release ack did not arrive before timeout")


def verify_run(run_directory: Path) -> dict[str, Any]:
    """Check the clock contract of one clock-smoke run directory.

    Never computes or reports C_track/C_geom; the clock-smoke identity is
    non-measurement by construction.
    """
    run_directory = Path(run_directory)
    failures: list[str] = []
    checks: dict[str, Any] = {}
    provenance: dict[str, Any] | None = None
    try:
        provenance = rate3_protocol.validate_provenance(run_directory)
        checks["provenance_valid"] = True
    except (FileNotFoundError, Rate2ProtocolError, ValueError) as exception:
        checks["provenance_valid"] = False
        failures.append(f"provenance:{type(exception).__name__}:{exception}")
    try:
        records, truncated = read_frame_records(run_directory / "frames.jsonl")
    except (FileNotFoundError, ValueError) as exception:
        records, truncated = [], 0
        failures.append(f"frames:{type(exception).__name__}:{exception}")
    frame_records = [
        record
        for record in records
        if record.get("record_kind", "frame") == "frame"
    ]
    previous_capture: float | None = None
    clock_frames = 0
    strictly_increasing = True
    for record in frame_records:
        if record.get("capture_monotonic_clock_id") != rate3_protocol.CLOCK_ID:
            failures.append(
                "frame "
                f"{record.get('frame_id')}: capture_monotonic_clock_id "
                f"{record.get('capture_monotonic_clock_id')!r}"
            )
            continue
        capture = record.get("capture_monotonic_s")
        if (
            isinstance(capture, bool)
            or not isinstance(capture, (int, float))
            or not math.isfinite(float(capture))
            or float(capture) < 0.0
        ):
            failures.append(
                f"frame {record.get('frame_id')}: capture_monotonic_s "
                "is not finite and non-negative"
            )
            continue
        clock_frames += 1
        if previous_capture is not None and float(capture) <= previous_capture:
            strictly_increasing = False
            failures.append(
                f"frame {record.get('frame_id')}: capture_monotonic_s "
                "is not strictly increasing"
            )
        previous_capture = float(capture)
    checks["clock_validated_frames"] = clock_frames
    checks["capture_strictly_increasing"] = strictly_increasing
    if truncated:
        failures.append("frames.jsonl has a truncated tail")
    if provenance is not None:
        release_monotonic_s = float(provenance["release_monotonic_s"])
        for record in frame_records:
            if record.get("phase") != "measurement":
                continue
            capture = record.get("capture_monotonic_s")
            if not isinstance(capture, (int, float)) or isinstance(
                capture, bool
            ):
                failures.append(
                    f"frame {record.get('frame_id')}: measurement record "
                    "lacks capture_monotonic_s"
                )
            elif float(capture) < release_monotonic_s:
                failures.append(
                    f"frame {record.get('frame_id')}: measurement capture "
                    "precedes release_monotonic_s"
                )
    summary_path = run_directory / "summary.json"
    if not summary_path.is_file():
        failures.append("summary.json is missing")
    else:
        summary = _read_object(summary_path)
        event_counts = summary.get("event_counts")
        invalid_clock_events = (
            int(event_counts.get("INVALID_CLOCK", 0))
            if isinstance(event_counts, Mapping)
            else 0
        )
        checks["invalid_clock_events"] = invalid_clock_events
        if invalid_clock_events != 0:
            failures.append("summary reports INVALID_CLOCK events")
        monotonic_cadence = summary.get(
            "monotonic_capture_cadence_post_release"
        )
        checks["monotonic_cadence_strictly_increasing"] = (
            isinstance(monotonic_cadence, Mapping)
            and monotonic_cadence.get("strictly_increasing") is True
        )
        if not checks["monotonic_cadence_strictly_increasing"]:
            failures.append(
                "summary monotonic cadence is not strictly increasing"
            )
        checks["summary_release_clock_id"] = summary.get("release_clock_id")
        if summary.get("release_clock_id") != rate3_protocol.CLOCK_ID:
            failures.append(
                "summary release_clock_id does not match "
                f"{rate3_protocol.CLOCK_ID!r}"
            )
    return {
        "run_id": run_directory.name,
        "study_id": rate3_protocol.CLOCK_SMOKE_STUDY_ID,
        "verdict": "PASS" if not failures else "FAIL",
        "checks": checks,
        "failures": failures,
    }


def archive_run(runtime: Path) -> dict[str, Any]:
    runtime = Path(runtime)
    source = runtime / "runs" / rate3_protocol.CLOCK_SMOKE_RUN_ID
    if not source.is_dir():
        raise FileNotFoundError(
            f"clock-smoke run directory is missing: {source}"
        )
    stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    destination = (
        archive_root(runtime) / f"smoke-{stamp}-{time.time_ns() % 1_000_000:06d}"
    )
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    # 清空 runtime 槽位，使下一次 smoke 可以直接 prepare（无 attempt 上限）。
    for name in (*SLOT_FILES, SESSION_FILE):
        (runtime / name).unlink(missing_ok=True)
    for name in SLOT_DIRECTORIES:
        shutil.rmtree(runtime / name, ignore_errors=True)
    return {
        "run_id": rate3_protocol.CLOCK_SMOKE_RUN_ID,
        "archived_to": str(destination),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="P1-M2-RATE-003 clock-smoke coordinator (non-measurement)"
    )
    parser.add_argument("--runtime", type=Path, default=RUNTIME_DEFAULT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare-session")
    prepare.add_argument("--init-frame", type=int, required=True)
    prepare.add_argument("--init-image-sha256", required=True)
    prepare.add_argument("--hold-route-s-m", type=float, required=True)

    launch = subparsers.add_parser("launch")
    launch.add_argument("--box", type=float, nargs=4, required=True)
    launch.add_argument("--ground-plane-y-m", type=float, required=True)
    launch.add_argument("--python", type=Path, default=Path(sys.executable))
    launch.add_argument(
        "--reanchor-config",
        type=Path,
        default=DEFAULT_REANCHOR_CONFIG,
    )

    release = subparsers.add_parser("release")
    release.add_argument("--confirmed", action="store_true")
    release.add_argument("--timeout-s", type=float, default=10.0)
    release.add_argument(
        "--poll-interval-s",
        type=float,
        default=RELEASE_POLL_INTERVAL_S,
    )

    subparsers.add_parser("verify")
    subparsers.add_parser("archive")
    return parser


def _default_tracker_identity() -> dict[str, Any]:
    from controller.trackers import create_tracker

    tracker = create_tracker(
        rate3_protocol.TRACKER_ID,
        nanotrack_spec_path=DEFAULT_NANOTRACK_V2_SPEC,
        nanotrack_model_dir=DEFAULT_NANOTRACK_V2_MODEL_DIR,
    )
    return dict(tracker.manifest_identity())


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    runtime = args.runtime.resolve()
    if args.command == "prepare-session":
        result: Any = prepare_session(
            runtime,
            build_clock_smoke_session(
                init_frame_id=args.init_frame,
                init_image_sha256=args.init_image_sha256,
                hold_route_s_m=args.hold_route_s_m,
                tracker_identity=_default_tracker_identity(),
            ),
        )
    elif args.command == "launch":
        completed = launch_tracker(
            python_executable=args.python,
            runtime=runtime,
            init_box=args.box,
            ground_plane_y_m=args.ground_plane_y_m,
            reanchor_config=args.reanchor_config,
        )
        raise SystemExit(completed.returncode)
    elif args.command == "release":
        result = coordinate_release(
            runtime,
            confirmed=args.confirmed,
            timeout_s=args.timeout_s,
            poll_interval_s=args.poll_interval_s,
        )
    elif args.command == "verify":
        result = verify_run(runtime / "runs" / rate3_protocol.CLOCK_SMOKE_RUN_ID)
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        if result["verdict"] != "PASS":
            raise SystemExit(1)
        return
    elif args.command == "archive":
        result = archive_run(runtime)
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
