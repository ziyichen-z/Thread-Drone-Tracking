from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

from controller.rate2_protocol import (
    IDENTITY_KEYS,
    SESSION_SCHEMA,
    STUDY_ID,
    TRACKER_ID,
    Rate2ProtocolError,
    archive_release_provenance,
    atomic_bytes,
    atomic_json,
    build_release_command,
    canonical_json_bytes,
    create_once_json,
    identity_hashes,
    latest_frame_id,
    load_session,
    read_consistent_ready,
    read_json_bytes,
    sha256_file,
    validate_provenance,
    validate_release_bundle,
    validate_session,
)
from controller.sensor_protocol import SENSOR_FRAME_SCHEMA_V2
from controller.trackers import (
    DEFAULT_NANOTRACK_V2_MODEL_DIR,
    DEFAULT_NANOTRACK_V2_SPEC,
    create_tracker,
)
from tools.run_rate_study import (
    _frame_candidates,
    _render_box_overlay,
    _validate_box,
    scenario_for_rate,
)
from tools.run_track_experiment import PROJECT_ROOT, route_timing_s, tracker_command


RUNTIME_DEFAULT = PROJECT_ROOT / "runtime"
CAMPAIGN_SCHEMA = "p1-rate2-campaign/v1"
CALIBRATION_PREVIEW_SCHEMA = "p1-rate2-calibration-preview/v1"
CALIBRATION_SCHEMA = "p1-rate2-calibration/v1"
ATTEMPT_STATUS_SCHEMA = "p1-rate2-attempt-status/v1"
QUALIFICATION_SCHEMA = "p1-rate2-qualification/v1"
DECISION_SCHEMA = "p1-rate2-decision-a/v1"
COORDINATOR_FAILURE_SCHEMA = "p1-rate2-coordinator-failure/v1"
FAILED_ATTEMPT_SCHEMA = "p1-rate2-failed-attempt/v1"
MAX_ATTEMPTS_PER_RUN = 3
RELEASE_POLL_INTERVAL_S = 0.005
TRIGGER_BRANCH = "stop"
DECISION_FINAL_ACTIONS = {
    "CONTINUE_REMAINING_CELLS",
    "TERMINATED_AT_DECISION_A",
    "BLOCKED_INVALID_CELL",
}
FORMAL_RUN_ORDER = (
    "rs2-r20-follow-1",
    "rs2-r20-follow-2",
    "rs2-r20-follow-3",
    "rs2-r20-nadir-1",
    "rs2-r20-nadir-2",
    "rs2-r20-nadir-3",
    "rs2-r5-follow-1",
    "rs2-r5-follow-2",
    "rs2-r5-follow-3",
    "rs2-r5-nadir-1",
    "rs2-r5-nadir-2",
    "rs2-r5-nadir-3",
)
SESSION_ORDER = (
    "rs2-r20-calib",
    "rs2-pilot",
    *FORMAL_RUN_ORDER[:3],
    "decision-a",
    *FORMAL_RUN_ORDER[3:6],
    "rs2-r5-calib",
    *FORMAL_RUN_ORDER[6:],
)
SLOT_FILES = (
    "tracker_ready.json",
    "experiment_control.json",
    "release_command.accepted.json",
    "release_ack.json",
    "release_coordinator_failure.json",
    "tracking_observation.json",
    "gimbal_command.json",
    "body_command.json",
    "metrics.json",
    "experiment_state.json",
)
SLOT_DIRECTORIES = ("experiment_rejections",)


def campaign_directory(runtime: Path) -> Path:
    return Path(runtime) / "rate-study" / STUDY_ID


def campaign_manifest_path(runtime: Path) -> Path:
    return campaign_directory(runtime) / "campaign.json"


def decision_path(runtime: Path) -> Path:
    return campaign_directory(runtime) / "decision_a.json"


def failed_attempts_directory(runtime: Path, run_id: str) -> Path:
    return campaign_directory(runtime) / "failed-attempts" / run_id


def calibration_directory(runtime: Path, rate_hz: int) -> Path:
    if rate_hz not in {5, 20}:
        raise ValueError("rate_hz must be 5 or 20")
    return campaign_directory(runtime) / "calibrations" / f"rate{rate_hz}"


def calibration_preview_path(runtime: Path, rate_hz: int) -> Path:
    return (
        campaign_directory(runtime)
        / "previews"
        / f"rate{rate_hz}-calibration.json"
    )


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


def prepare_campaign(runtime: Path) -> dict[str, Any]:
    if campaign_manifest_path(runtime).is_file():
        return load_campaign(runtime)
    existing_runs = sorted(
        path.name for path in (Path(runtime) / "runs").glob("rs2-*")
    )
    if existing_runs:
        raise FileExistsError(
            "campaign manifest must be frozen before RATE-002 data: "
            + ", ".join(existing_runs)
        )
    manifest = {
        "schema_version": CAMPAIGN_SCHEMA,
        "study_id": STUDY_ID,
        "tracker_id": TRACKER_ID,
        "trigger_branch": TRIGGER_BRANCH,
        "session_order": list(SESSION_ORDER),
        "qualification": {
            "rate_hz": 20,
            "condition": "follow",
            "planned_duration_s": 30.0,
            "minimum_ready_seq": 20,
            "minimum_processed_frames": 20,
        },
        "decision_rule_version": "p1-rate2-rules-r1prime-r3prime/v1",
        "fixed_order_time_confound": (
            "20 Hz follow is measured before remaining cells; load/time drift "
            "must not be attributed solely to frame rate"
        ),
        "created_unix_s": time.time(),
    }
    create_once_json(campaign_manifest_path(runtime), manifest)
    return _read_object(campaign_manifest_path(runtime))


def load_campaign(runtime: Path) -> dict[str, Any]:
    campaign = _read_object(campaign_manifest_path(runtime))
    if campaign.get("schema_version") != CAMPAIGN_SCHEMA:
        raise ValueError("invalid RATE-002 campaign schema")
    if campaign.get("study_id") != STUDY_ID:
        raise ValueError("invalid RATE-002 campaign study_id")
    if campaign.get("tracker_id") != TRACKER_ID:
        raise ValueError("invalid RATE-002 campaign tracker_id")
    if campaign.get("trigger_branch") != TRIGGER_BRANCH:
        raise ValueError("RATE-002 trigger_branch must remain frozen to stop")
    if campaign.get("session_order") != list(SESSION_ORDER):
        raise ValueError("RATE-002 session order changed")
    return campaign


def _directory_hashes(directory: Path) -> dict[str, str]:
    return {
        str(path.relative_to(directory)): sha256_file(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def failed_attempt_count(runtime: Path, run_id: str) -> int:
    directory = failed_attempts_directory(runtime, run_id)
    receipts = sorted(directory.glob("attempt-*.json"))
    for expected_number, receipt_path in enumerate(receipts, start=1):
        receipt = _read_object(receipt_path)
        if (
            receipt.get("schema_version") != FAILED_ATTEMPT_SCHEMA
            or receipt.get("study_id") != STUDY_ID
            or receipt.get("run_id") != run_id
            or receipt.get("attempt_number") != expected_number
        ):
            raise ValueError("invalid failed-attempt receipt sequence")
        archive = directory / f"attempt-{expected_number}-run"
        if receipt.get("archived_directory") != str(archive):
            raise ValueError("failed-attempt archive path mismatch")
        if receipt.get("file_sha256") != _directory_hashes(archive):
            raise ValueError("failed-attempt archive hash mismatch")
    return len(receipts)


def archive_failed_attempt(runtime: Path, run_id: str, reason: str) -> dict[str, Any]:
    if not reason.strip():
        raise ValueError("failed attempt reason must not be empty")
    load_campaign(runtime)
    authorize_session_identity(run_id)
    source = Path(runtime) / "runs" / run_id
    if not source.is_dir():
        raise FileNotFoundError(f"failed run directory is missing: {run_id}")
    count = failed_attempt_count(runtime, run_id)
    if count >= MAX_ATTEMPTS_PER_RUN:
        raise RuntimeError("accepted RATE-002 attempt limit is already exhausted")
    number = count + 1
    directory = failed_attempts_directory(runtime, run_id)
    archive = directory / f"attempt-{number}-run"
    if archive.exists():
        raise FileExistsError(archive)
    directory.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(archive))
    receipt = {
        "schema_version": FAILED_ATTEMPT_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": run_id,
        "attempt_number": number,
        "reason": reason.strip(),
        "archived_directory": str(archive),
        "file_sha256": _directory_hashes(archive),
        "archived_unix_s": time.time(),
    }
    create_once_json(directory / f"attempt-{number}.json", receipt)
    return _read_object(directory / f"attempt-{number}.json")


def nanotrack_identity(
    *,
    tracker_model_spec: Path = DEFAULT_NANOTRACK_V2_SPEC,
    tracker_model_dir: Path = DEFAULT_NANOTRACK_V2_MODEL_DIR,
) -> dict[str, Any]:
    tracker = create_tracker(
        TRACKER_ID,
        nanotrack_spec_path=tracker_model_spec,
        nanotrack_model_dir=tracker_model_dir,
    )
    return dict(tracker.manifest_identity())


def build_session(
    *,
    run_id: str,
    init_frame_id: int,
    init_image_sha256: str,
    hold_route_s_m: float,
    tracker_identity: Mapping[str, Any],
) -> dict[str, Any]:
    tracker_hash, model_hash = identity_hashes(tracker_identity)
    session = {
        "schema_version": SESSION_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": run_id,
        "scenario_id": (
            "rate-study-5hz" if "-r5-" in f"-{run_id}-" else "rate-study-20hz"
        ),
        "tracker_id": TRACKER_ID,
        "tracker_identity_sha256": tracker_hash,
        "model_identity_sha256": model_hash,
        "init_frame_id": int(init_frame_id),
        "init_image_sha256": init_image_sha256,
        "hold_route_s_m": _finite(hold_route_s_m, "hold_route_s_m"),
        "minimum_ready_seq": 20,
        "minimum_processed_frames": 20,
    }
    return validate_session(session)


def prepare_session(
    runtime: Path,
    session: Mapping[str, Any],
) -> dict[str, Any]:
    runtime = Path(runtime)
    load_campaign(runtime)
    validated = validate_session(session)
    authorize_session(runtime, str(validated["run_id"]))
    run_id = str(validated["run_id"])
    if run_id not in {"rs2-r20-calib", "rs2-r5-calib"}:
        rate_hz = 5 if validated["scenario_id"] == "rate-study-5hz" else 20
        calibration = load_calibration(runtime, rate_hz)
        if validated["init_frame_id"] != calibration["reference_frame_id"]:
            raise ValueError("session init frame does not match frozen calibration")
        if validated["init_image_sha256"] != calibration["reference_image_sha256"]:
            raise ValueError("session init image does not match frozen calibration")
    stale = [name for name in SLOT_FILES if (runtime / name).exists()]
    stale.extend(
        f"{name}/"
        for name in SLOT_DIRECTORIES
        if (runtime / name).exists()
    )
    if stale:
        raise FileExistsError(
            "stale RATE-002 runtime slots must be archived/removed before prepare: "
            + ", ".join(stale)
        )
    session_path = runtime / "rate_study_session.json"
    create_once_json(session_path, validated)
    return _read_object(session_path)


def select_rate2_init_frame(
    runtime: Path,
    rate_hz: int,
    *,
    start_s: float = 0.0,
    end_s: float = float("inf"),
) -> dict[str, Any]:
    _, scenario = scenario_for_rate(rate_hz)
    candidates = _frame_candidates(
        runtime,
        scenario["scenario_id"],
        start_s,
        end_s,
        expected_sensor_schema=SENSOR_FRAME_SCHEMA_V2,
    )
    if not candidates:
        raise FileNotFoundError("no RATE-002 v2 HOLD frame is available")
    return candidates[-1]


def preview_calibration(
    runtime: Path,
    rate_hz: int,
    box_norm: Sequence[float],
) -> dict[str, Any]:
    runtime = Path(runtime)
    box = _validate_box(box_norm)
    _, installed_session = load_session(runtime)
    expected_run_id = f"rs2-r{rate_hz}-calib"
    if installed_session["run_id"] != expected_run_id:
        raise ValueError(
            f"installed session must be {expected_run_id} for calibration"
        )
    frame = select_rate2_init_frame(runtime, rate_hz)
    preview_path = calibration_preview_path(runtime, rate_hz)
    overlay_path = preview_path.with_suffix(".jpg")
    pixel_box = _render_box_overlay(
        frame["image_path"],
        overlay_path,
        box,
        f"RATE-002 {rate_hz} Hz target",
    )
    preview = {
        "schema_version": CALIBRATION_PREVIEW_SCHEMA,
        "study_id": STUDY_ID,
        "session_id": expected_run_id,
        "rate_hz": rate_hz,
        "scenario_id": installed_session["scenario_id"],
        "reference_frame_id": frame["frame_id"],
        "reference_simulation_time_s": frame["simulation_time_s"],
        "reference_image_sha256": frame["image_sha256"],
        "reference_metadata_sha256": frame["metadata_sha256"],
        "reference_box_xywh_norm": list(box),
        "reference_box_xywh_px": pixel_box,
        "overlay_path": str(overlay_path),
        "overlay_sha256": sha256_file(overlay_path),
    }
    atomic_json(preview_path, preview)
    return preview


def freeze_calibration(
    runtime: Path,
    rate_hz: int,
    *,
    confirmed: bool,
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("calibration freeze requires visual overlay confirmation")
    runtime = Path(runtime)
    preview_path = calibration_preview_path(runtime, rate_hz)
    preview = _read_object(preview_path)
    if preview.get("schema_version") != CALIBRATION_PREVIEW_SCHEMA:
        raise ValueError("invalid RATE-002 calibration preview schema")
    expected = {
        "study_id": STUDY_ID,
        "session_id": f"rs2-r{rate_hz}-calib",
        "rate_hz": rate_hz,
        "scenario_id": f"rate-study-{rate_hz}hz",
    }
    for key, value in expected.items():
        if preview.get(key) != value:
            raise ValueError(f"calibration preview {key} mismatch")
    frame_id = int(preview["reference_frame_id"])
    stem = f"frame_{frame_id:010d}"
    source_image = runtime / "frames" / f"{stem}.jpg"
    source_metadata = runtime / "frames" / f"{stem}.json"
    overlay_path = preview_path.with_suffix(".jpg")
    hashes = {
        "reference_image_sha256": sha256_file(source_image),
        "reference_metadata_sha256": sha256_file(source_metadata),
        "overlay_sha256": sha256_file(overlay_path),
    }
    for key, value in hashes.items():
        if preview.get(key) != value:
            raise ValueError(f"calibration preview {key} binding changed")
    destination = calibration_directory(runtime, rate_hz)
    if destination.exists():
        return load_calibration(runtime, rate_hz)
    destination.mkdir(parents=True, exist_ok=False)
    try:
        shutil.copy2(source_image, destination / "reference.jpg")
        shutil.copy2(source_metadata, destination / "reference.json")
        shutil.copy2(overlay_path, destination / "reference-box-preview.jpg")
        shutil.copy2(preview_path, destination / "reference-box-preview.json")
        manifest = {
            "schema_version": CALIBRATION_SCHEMA,
            "study_id": STUDY_ID,
            "session_id": f"rs2-r{rate_hz}-calib",
            "rate_hz": rate_hz,
            "scenario_id": f"rate-study-{rate_hz}hz",
            "reference_frame_id": frame_id,
            "reference_simulation_time_s": preview[
                "reference_simulation_time_s"
            ],
            "reference_image_sha256": hashes["reference_image_sha256"],
            "reference_metadata_sha256": hashes[
                "reference_metadata_sha256"
            ],
            "reference_box_xywh_norm": preview["reference_box_xywh_norm"],
            "reference_box_preview_sha256": hashes["overlay_sha256"],
            "frozen_unix_s": time.time(),
        }
        create_once_json(destination / "manifest.json", manifest)
        return load_calibration(runtime, rate_hz)
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def load_calibration(runtime: Path, rate_hz: int) -> dict[str, Any]:
    destination = calibration_directory(runtime, rate_hz)
    manifest = _read_object(destination / "manifest.json")
    if manifest.get("schema_version") != CALIBRATION_SCHEMA:
        raise ValueError("invalid RATE-002 calibration schema")
    expected = {
        "study_id": STUDY_ID,
        "session_id": f"rs2-r{rate_hz}-calib",
        "rate_hz": rate_hz,
        "scenario_id": f"rate-study-{rate_hz}hz",
        "reference_image_sha256": sha256_file(destination / "reference.jpg"),
        "reference_metadata_sha256": sha256_file(
            destination / "reference.json"
        ),
        "reference_box_preview_sha256": sha256_file(
            destination / "reference-box-preview.jpg"
        ),
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"RATE-002 calibration {key} mismatch")
    _validate_box(manifest.get("reference_box_xywh_norm", ()))
    return manifest


def rate2_tracker_command(
    *,
    python_executable: Path,
    runtime: Path,
    init_box: Sequence[float],
    condition: str,
    ground_plane_y_m: float,
    planned_duration_s: float,
    tracker_model_spec: Path = DEFAULT_NANOTRACK_V2_SPEC,
    tracker_model_dir: Path = DEFAULT_NANOTRACK_V2_MODEL_DIR,
) -> list[str]:
    _, session = load_session(runtime)
    rate_hz = 5 if session["scenario_id"] == "rate-study-5hz" else 20
    calibration = load_calibration(runtime, rate_hz)
    if list(_validate_box(init_box)) != calibration["reference_box_xywh_norm"]:
        raise ValueError("launch box differs from frozen RATE-002 calibration")
    if session["init_frame_id"] != calibration["reference_frame_id"]:
        raise ValueError("launch init frame differs from frozen calibration")
    if session["init_image_sha256"] != calibration["reference_image_sha256"]:
        raise ValueError("launch init image differs from frozen calibration")
    run_id = str(session["run_id"])
    expected_condition = (
        "follow"
        if run_id == "rs2-pilot"
        else (
            run_id.split("-")[2]
            if run_id not in {"rs2-r20-calib", "rs2-r5-calib"}
            else None
        )
    )
    if expected_condition is None:
        raise ValueError("calibration sessions do not launch the tracker")
    if condition != expected_condition:
        raise ValueError("launch condition differs from frozen run identity")
    timing = route_timing_s(scenario_for_rate(rate_hz)[1])
    expected_duration = 30.0 if run_id == "rs2-pilot" else timing["planned_duration_s"]
    if abs(float(planned_duration_s) - expected_duration) > 1e-9:
        raise ValueError("launch planned duration differs from frozen schedule")
    _, scenario = scenario_for_rate(
        rate_hz
    )
    command = tracker_command(
        python_executable=python_executable,
        runtime=Path(runtime).resolve(),
        init_frame=int(session["init_frame_id"]),
        init_box=init_box,
        track_id=scenario["target"]["track_id"],
        scenario_id=str(session["scenario_id"]),
        condition=condition,
        ground_plane_y_m=ground_plane_y_m,
        planned_duration_s=planned_duration_s,
        run_id=str(session["run_id"]),
        tracker=TRACKER_ID,
        tracker_model_spec=tracker_model_spec,
        tracker_model_dir=tracker_model_dir,
    )
    command.append("--rate2-session")
    return command


def launch_tracker(
    *,
    python_executable: Path,
    runtime: Path,
    init_box: Sequence[float],
    condition: str,
    ground_plane_y_m: float,
    planned_duration_s: float,
    tracker_model_spec: Path = DEFAULT_NANOTRACK_V2_SPEC,
    tracker_model_dir: Path = DEFAULT_NANOTRACK_V2_MODEL_DIR,
) -> subprocess.CompletedProcess[str]:
    command = rate2_tracker_command(
        python_executable=python_executable,
        runtime=runtime,
        init_box=init_box,
        condition=condition,
        ground_plane_y_m=ground_plane_y_m,
        planned_duration_s=planned_duration_s,
        tracker_model_spec=tracker_model_spec,
        tracker_model_dir=tracker_model_dir,
    )
    return subprocess.run(command, cwd=PROJECT_ROOT, text=True, check=False)


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
    _, session = load_session(runtime)
    run_directory = runtime / "runs" / str(session["run_id"])
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
            candidate_bytes, ready, observed_frame_id = read_consistent_ready(
                runtime,
                session,
                previous_seq=previous_seq,
                now_monotonic_s=monotonic(),
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
        atomic_json(
            runtime / "release_coordinator_failure.json",
            {
                "schema_version": COORDINATOR_FAILURE_SCHEMA,
                "study_id": session["study_id"],
                "run_id": session["run_id"],
                "stage": "ready_prefilter",
                "reason": last_ready_error,
                "failed_unix_s": time.time(),
            },
        )
        raise TimeoutError("no fresh advancing tracker-ready heartbeat")
    command_bytes = build_release_command(
        session,
        ready_bytes,
        command_id=command_id or f"rate2-release-{time.time_ns()}",
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
                ack = validate_release_bundle(command_bytes, ack_bytes, session)
                provenance = archive_release_provenance(
                    runtime,
                    run_directory,
                    session,
                )
                return {
                    "command_id": ack["command_id"],
                    "release_frame_id": ack["release_frame_id"],
                    "accepted_backlog_frames": ack["accepted_backlog_frames"],
                    "release_monotonic_s": ack["release_monotonic_s"],
                    "provenance": provenance,
                }
            except (OSError, ValueError, Rate2ProtocolError) as exception:
                atomic_json(
                    runtime / "release_coordinator_failure.json",
                    {
                        "schema_version": COORDINATOR_FAILURE_SCHEMA,
                        "study_id": session["study_id"],
                        "run_id": session["run_id"],
                        "stage": "ack_validation",
                        "reason": f"{type(exception).__name__}:{exception}",
                        "failed_unix_s": time.time(),
                    },
                )
                raise
        sleeper(poll)
    atomic_json(
        runtime / "release_coordinator_failure.json",
        {
            "schema_version": COORDINATOR_FAILURE_SCHEMA,
            "study_id": session["study_id"],
            "run_id": session["run_id"],
            "stage": "ack_wait",
            "reason": "release_ack_timeout",
            "failed_unix_s": time.time(),
        },
    )
    raise TimeoutError("Unity release ack did not arrive before timeout")


def _metrics(run_directory: Path) -> dict[str, Any]:
    metrics = _read_object(run_directory / "metrics.final.json")
    if metrics.get("schema_version") != "tethered-evaluation/v1":
        raise ValueError("invalid evaluator metrics schema")
    aggregate = metrics.get("aggregate")
    if not isinstance(aggregate, Mapping):
        raise ValueError("metrics aggregate is missing")
    return metrics


def finalize_attempt(run_directory: Path) -> dict[str, Any]:
    run_directory = Path(run_directory)
    existing_status = run_directory / "rate2-status.json"
    if existing_status.is_file():
        status = _read_object(existing_status)
        if (
            status.get("schema_version") != ATTEMPT_STATUS_SCHEMA
            or status.get("run_id") != run_directory.name
        ):
            raise ValueError("existing RATE-002 attempt status is invalid")
        bindings = {
            "manifest_sha256": sha256_file(run_directory / "manifest.json"),
            "release_provenance_sha256": sha256_file(
                run_directory / "release_provenance.json"
            ),
            "summary_sha256": sha256_file(run_directory / "summary.json"),
            "metrics_sha256": sha256_file(run_directory / "metrics.final.json"),
        }
        if any(status.get(key) != value for key, value in bindings.items()):
            raise ValueError("existing RATE-002 status artifact binding mismatch")
        return status
    provenance = validate_provenance(run_directory)
    manifest = _read_object(run_directory / "manifest.json")
    summary = _read_object(run_directory / "summary.json")
    metrics = _metrics(run_directory)
    rate2 = manifest.get("rate2")
    if not isinstance(rate2, Mapping):
        raise ValueError("run manifest lacks RATE-002 identity")
    if manifest.get("run_id") != run_directory.name:
        raise ValueError("run directory/manifest identity mismatch")
    if provenance.get("run_id") != run_directory.name:
        raise ValueError("run provenance identity mismatch")
    planned = _finite(manifest.get("planned_duration_s"), "planned_duration_s")
    actual = _finite(summary.get("actual_duration_s"), "actual_duration_s")
    metrics_elapsed = _finite(
        metrics.get("elapsed_simulation_s"),
        "metrics.elapsed_simulation_s",
    )
    errors: list[str] = []
    if actual + 1e-6 < planned:
        errors.append("planned_duration_not_reached")
    monotonic_cadence = summary.get("monotonic_capture_cadence_post_release")
    if not isinstance(monotonic_cadence, Mapping):
        errors.append("monotonic_cadence_missing")
        monotonic_cadence = {}
    target_rate = 5 if manifest.get("scenario_id") == "rate-study-5hz" else 20
    frame_tolerance_s = 1.0 / target_rate + 1e-6
    if metrics_elapsed + frame_tolerance_s < planned:
        errors.append("evaluator_duration_not_reached")
    if metrics_elapsed > actual + frame_tolerance_s:
        errors.append("evaluator_duration_exceeds_tracker_window")
    wall_rate = monotonic_cadence.get("rate_hz")
    s1 = (
        monotonic_cadence.get("strictly_increasing") is True
        and isinstance(wall_rate, (int, float))
        and not isinstance(wall_rate, bool)
        and math.isfinite(float(wall_rate))
        and float(wall_rate) >= target_rate * 0.95
    )
    compute_p95 = (summary.get("compute_latency_ms") or {}).get("p95")
    s2 = (
        isinstance(compute_p95, (int, float))
        and not isinstance(compute_p95, bool)
        and math.isfinite(float(compute_p95))
        and float(compute_p95) < 50.0
    )
    backlog_p95 = (summary.get("backlog_count") or {}).get("p95")
    s3 = (
        isinstance(backlog_p95, (int, float))
        and not isinstance(backlog_p95, bool)
        and math.isfinite(float(backlog_p95))
        and float(backlog_p95) <= 1.0
        and int(summary.get("reinit_required_records", 0)) == 0
    )
    if target_rate == 20:
        if not s1:
            errors.append("S1_RATE_UNSUSTAINABLE")
        if not s2:
            errors.append("S2_COMPUTE_LATENCY")
        if not s3:
            errors.append("S3_BACKLOG_OR_REINIT")
    bindings = {
        "manifest_sha256": sha256_file(run_directory / "manifest.json"),
        "release_provenance_sha256": sha256_file(
            run_directory / "release_provenance.json"
        ),
        "summary_sha256": sha256_file(run_directory / "summary.json"),
        "metrics_sha256": sha256_file(run_directory / "metrics.final.json"),
    }
    status = {
        "schema_version": ATTEMPT_STATUS_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": run_directory.name,
        "admissible": not errors,
        "classification": "COMPLETE" if not errors else "INVALID",
        "errors": errors,
        "planned_duration_s": planned,
        "actual_duration_s": actual,
        "metrics_elapsed_simulation_s": metrics_elapsed,
        **bindings,
        "gates": (
            {"S1": s1, "S2": s2, "S3": s3}
            if target_rate == 20
            else {"S1": None, "S2": None, "S3": None}
        ),
        "finalized_unix_s": time.time(),
    }
    create_once_json(run_directory / "rate2-status.json", status)
    return _read_object(run_directory / "rate2-status.json")


def attempt_row(run_directory: Path) -> dict[str, Any]:
    run_directory = Path(run_directory)
    status = _read_object(run_directory / "rate2-status.json")
    if status.get("schema_version") != ATTEMPT_STATUS_SCHEMA:
        raise ValueError("invalid RATE-002 attempt status schema")
    if status.get("run_id") != run_directory.name or not status.get("admissible"):
        raise ValueError(f"{run_directory.name} is not admissible")
    status_bindings = {
        "manifest_sha256": sha256_file(run_directory / "manifest.json"),
        "release_provenance_sha256": sha256_file(
            run_directory / "release_provenance.json"
        ),
        "summary_sha256": sha256_file(run_directory / "summary.json"),
        "metrics_sha256": sha256_file(run_directory / "metrics.final.json"),
    }
    if any(status.get(key) != value for key, value in status_bindings.items()):
        raise ValueError(f"{run_directory.name} status artifact binding mismatch")
    provenance = validate_provenance(run_directory)
    manifest = _read_object(run_directory / "manifest.json")
    summary = _read_object(run_directory / "summary.json")
    aggregate = _metrics(run_directory)["aggregate"]
    matched = int(aggregate.get("matched_tracking_observations", 0))
    incorrect = int(aggregate.get("incorrect_tracking_observations", 0))
    c_geom = _finite(aggregate.get("c_geom"), "aggregate.c_geom")
    conditional = _finite(
        aggregate.get("c_track_given_geom"),
        "aggregate.c_track_given_geom",
    )
    if c_geom <= 0.0 or matched == 0:
        conditional = 0.0
    incorrect_ratio = 1.0 if matched == 0 else incorrect / matched
    planned = _finite(manifest.get("planned_duration_s"), "planned_duration_s")
    lost_records = int(summary.get("lost_records", 0))
    first_lost = (
        _finite(summary.get("time_to_first_lost_s"), "time_to_first_lost_s")
        if lost_records > 0
        else planned
    )
    return {
        "run_id": run_directory.name,
        "manifest_sha256": sha256_file(run_directory / "manifest.json"),
        "release_provenance_sha256": sha256_file(
            run_directory / "release_provenance.json"
        ),
        "release_unix_s": provenance["release_unix_s"],
        "c_track_given_geom": conditional,
        "matched_tracking_observations": matched,
        "incorrect_tracking_observations": incorrect,
        "incorrect_over_matched": incorrect_ratio,
        "time_to_first_lost_s": first_lost,
        "time_to_first_lost_right_censored": lost_records == 0,
        "planned_duration_s": planned,
    }


def qualify_pilot(runtime: Path) -> dict[str, Any]:
    qualification_path = campaign_directory(runtime) / "qualification.json"
    if qualification_path.is_file():
        return validate_qualification(runtime)
    run_directory = Path(runtime) / "runs" / "rs2-pilot"
    row = attempt_row(run_directory)
    if abs(float(row["planned_duration_s"]) - 30.0) > 1e-9:
        raise ValueError("qualification pilot planned duration must equal 30.0 s")
    summary = _read_object(run_directory / "summary.json")
    gates = {
        "s1_s3": all(
            _read_object(run_directory / "rate2-status.json")["gates"].values()
        ),
        "no_lost_gap_reinit": (
            int(summary.get("lost_records", 0)) == 0
            and int(summary.get("gap_events", 0)) == 0
            and int(summary.get("reinit_required_records", 0)) == 0
        ),
        "c_track_given_geom_ge_0_25": row["c_track_given_geom"] >= 0.25,
        "matched_observations_positive": row["matched_tracking_observations"] > 0,
        "incorrect_over_matched_lt_0_5": row["incorrect_over_matched"] < 0.5,
    }
    qualification = {
        "schema_version": QUALIFICATION_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": "rs2-pilot",
        "planned_duration_s": 30.0,
        "passed": all(gates.values()),
        "gates": gates,
        "run_manifest_sha256": row["manifest_sha256"],
        "release_provenance_sha256": row["release_provenance_sha256"],
        "generated_unix_s": time.time(),
    }
    create_once_json(
        qualification_path,
        qualification,
    )
    return validate_qualification(runtime)


def validate_qualification(runtime: Path) -> dict[str, Any]:
    path = campaign_directory(runtime) / "qualification.json"
    value = _read_object(path)
    if (
        value.get("schema_version") != QUALIFICATION_SCHEMA
        or value.get("study_id") != STUDY_ID
        or value.get("run_id") != "rs2-pilot"
    ):
        raise ValueError("qualification artifact identity is invalid")
    run_directory = Path(runtime) / "runs" / "rs2-pilot"
    if value.get("run_manifest_sha256") != sha256_file(
        run_directory / "manifest.json"
    ):
        raise ValueError("qualification manifest hash mismatch")
    if value.get("release_provenance_sha256") != sha256_file(
        run_directory / "release_provenance.json"
    ):
        raise ValueError("qualification provenance hash mismatch")
    return value


def _qualification_passed(runtime: Path) -> bool:
    try:
        value = validate_qualification(runtime)
    except (FileNotFoundError, ValueError, Rate2ProtocolError):
        return False
    return value.get("passed") is True


def build_decision_a(
    runtime: Path,
    *,
    invalid_cell_exhausted: bool = False,
) -> dict[str, Any]:
    load_campaign(runtime)
    if decision_path(runtime).is_file():
        return validate_decision_a(runtime)
    expected_runs = [f"rs2-r20-follow-{index}" for index in (1, 2, 3)]
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    for run_id in expected_runs:
        try:
            rows.append(attempt_row(Path(runtime) / "runs" / run_id))
        except (FileNotFoundError, ValueError, Rate2ProtocolError):
            missing.append(run_id)
    if missing:
        exhausted = {
            run_id: failed_attempt_count(runtime, run_id)
            for run_id in missing
        }
        if (
            not invalid_cell_exhausted
            or any(count < MAX_ATTEMPTS_PER_RUN for count in exhausted.values())
        ):
            raise RuntimeError(
                "20 Hz follow cell is incomplete; exhaust the accepted rerun "
                "limit before recording BLOCKED_INVALID_CELL"
            )
        decision = {
            "schema_version": DECISION_SCHEMA,
            "study_id": STUDY_ID,
            "rule_version": "p1-rate2-rules-r1prime-r3prime/v1",
            "trigger_branch": TRIGGER_BRANCH,
            "run_ids": expected_runs,
            "missing_or_invalid_run_ids": missing,
            "rerun_limit_exhausted": True,
            "failed_attempt_counts": exhausted,
            "triggered": None,
            "rules": None,
            "threshold_sensitivity": None,
            "final_action": "BLOCKED_INVALID_CELL",
            "m2_status": "M2_NOT_CLOSABLE",
            "generated_unix_s": time.time(),
        }
    else:
        conditional_values = [row["c_track_given_geom"] for row in rows]
        ratio_values = [row["incorrect_over_matched"] for row in rows]
        lost_values = [row["time_to_first_lost_s"] for row in rows]
        loop_duration_s = route_timing_s(scenario_for_rate(20)[1])[
            "loop_duration_s"
        ]
        medians = {
            "c_track_given_geom": statistics.median(conditional_values),
            "incorrect_over_matched": statistics.median(ratio_values),
            "time_to_first_lost_s": statistics.median(lost_values),
        }
        rules = {
            "R1_prime": {
                "value": medians["c_track_given_geom"],
                "threshold": 0.25,
                "comparison": "<",
                "triggered": medians["c_track_given_geom"] < 0.25,
            },
            "R2_prime": {
                "value": medians["incorrect_over_matched"],
                "threshold": 0.5,
                "comparison": ">=",
                "triggered": medians["incorrect_over_matched"] >= 0.5,
            },
            "R3_prime": {
                "value_s": medians["time_to_first_lost_s"],
                "threshold_loop_duration_s": loop_duration_s,
                "comparison": "<",
                "triggered": medians["time_to_first_lost_s"] < loop_duration_s,
            },
        }
        triggered = any(rule["triggered"] for rule in rules.values())
        decision = {
            "schema_version": DECISION_SCHEMA,
            "study_id": STUDY_ID,
            "rule_version": "p1-rate2-rules-r1prime-r3prime/v1",
            "trigger_branch": TRIGGER_BRANCH,
            "runs": rows,
            "run_ids": expected_runs,
            "missing_or_invalid_run_ids": [],
            "rules": rules,
            "triggered": triggered,
            "threshold_sensitivity": {
                "R1_prime": {
                    str(threshold): medians["c_track_given_geom"] < threshold
                    for threshold in (0.15, 0.25, 0.35)
                },
                "R2_prime": {
                    str(threshold): medians["incorrect_over_matched"] >= threshold
                    for threshold in (0.3, 0.5, 0.7)
                },
            },
            "actual_session_order": [
                row["run_id"]
                for row in sorted(rows, key=lambda item: item["release_unix_s"])
            ],
            "final_action": (
                "TERMINATED_AT_DECISION_A"
                if triggered
                else "CONTINUE_REMAINING_CELLS"
            ),
            "m2_status": "M2_NOT_CLOSABLE" if triggered else "PENDING_FULL_MATRIX",
            "generated_unix_s": time.time(),
        }
    create_once_json(decision_path(runtime), decision)
    return validate_decision_a(runtime)


def validate_decision_a(runtime: Path) -> dict[str, Any]:
    decision = _read_object(decision_path(runtime))
    if decision.get("schema_version") != DECISION_SCHEMA:
        raise ValueError("invalid Decision A schema")
    if decision.get("study_id") != STUDY_ID:
        raise ValueError("invalid Decision A study_id")
    if decision.get("trigger_branch") != TRIGGER_BRANCH:
        raise ValueError("Decision A trigger branch changed")
    action = decision.get("final_action")
    if action not in DECISION_FINAL_ACTIONS:
        raise ValueError("invalid Decision A final action")
    triggered = decision.get("triggered")
    if action == "BLOCKED_INVALID_CELL":
        if (
            triggered is not None
            or not decision.get("missing_or_invalid_run_ids")
            or decision.get("rerun_limit_exhausted") is not True
            or decision.get("rules") is not None
        ):
            raise ValueError("blocked Decision A has invalid tri-state semantics")
        expected_counts = {
            run_id: failed_attempt_count(runtime, run_id)
            for run_id in decision["missing_or_invalid_run_ids"]
        }
        if (
            decision.get("failed_attempt_counts") != expected_counts
            or any(
                count < MAX_ATTEMPTS_PER_RUN
                for count in expected_counts.values()
            )
        ):
            raise ValueError("blocked Decision A attempt-limit evidence mismatch")
        return decision
    if not isinstance(triggered, bool):
        raise ValueError("complete Decision A must have a boolean result")
    if (action == "TERMINATED_AT_DECISION_A") != triggered:
        raise ValueError("Decision A action does not match trigger result")
    rows = decision.get("runs")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("Decision A must bind exactly three runs")
    expected_ids = [f"rs2-r20-follow-{index}" for index in (1, 2, 3)]
    if decision.get("run_ids") != expected_ids:
        raise ValueError("Decision A run IDs changed")
    for row, run_id in zip(rows, expected_ids):
        run_directory = Path(runtime) / "runs" / run_id
        if row.get("run_id") != run_id:
            raise ValueError("Decision A run order/identity mismatch")
        if row.get("manifest_sha256") != sha256_file(
            run_directory / "manifest.json"
        ):
            raise ValueError("Decision A manifest hash mismatch")
        if row.get("release_provenance_sha256") != sha256_file(
            run_directory / "release_provenance.json"
        ):
            raise ValueError("Decision A provenance hash mismatch")
        current = attempt_row(run_directory)
        stable_fields = (
            "c_track_given_geom",
            "matched_tracking_observations",
            "incorrect_tracking_observations",
            "incorrect_over_matched",
            "time_to_first_lost_s",
            "time_to_first_lost_right_censored",
            "planned_duration_s",
        )
        if any(row.get(key) != current.get(key) for key in stable_fields):
            raise ValueError("Decision A run inputs no longer match artifacts")
    conditional = statistics.median(
        float(row["c_track_given_geom"]) for row in rows
    )
    ratio = statistics.median(float(row["incorrect_over_matched"]) for row in rows)
    lost = statistics.median(float(row["time_to_first_lost_s"]) for row in rows)
    loop_duration_s = route_timing_s(scenario_for_rate(20)[1])["loop_duration_s"]
    recomputed = {
        "R1_prime": conditional < 0.25,
        "R2_prime": ratio >= 0.5,
        "R3_prime": lost < loop_duration_s,
    }
    rules = decision.get("rules")
    if not isinstance(rules, Mapping):
        raise ValueError("Decision A rules are missing")
    if any(
        not isinstance(rules.get(key), Mapping)
        or rules[key].get("triggered") is not value
        for key, value in recomputed.items()
    ):
        raise ValueError("Decision A rule outputs do not match run inputs")
    numeric_expectations = {
        "R1_prime": ("value", conditional, "threshold", 0.25, "comparison", "<"),
        "R2_prime": ("value", ratio, "threshold", 0.5, "comparison", ">="),
        "R3_prime": (
            "value_s",
            lost,
            "threshold_loop_duration_s",
            loop_duration_s,
            "comparison",
            "<",
        ),
    }
    for key, expected in numeric_expectations.items():
        rule = rules[key]
        for index in range(0, len(expected), 2):
            if rule.get(expected[index]) != expected[index + 1]:
                raise ValueError(f"Decision A {key} input/threshold mismatch")
    if triggered is not any(recomputed.values()):
        raise ValueError("Decision A OR result does not match rules")
    expected_sensitivity = {
        "R1_prime": {
            str(threshold): conditional < threshold
            for threshold in (0.15, 0.25, 0.35)
        },
        "R2_prime": {
            str(threshold): ratio >= threshold
            for threshold in (0.3, 0.5, 0.7)
        },
    }
    if decision.get("threshold_sensitivity") != expected_sensitivity:
        raise ValueError("Decision A sensitivity table mismatch")
    expected_order = [
        row["run_id"]
        for row in sorted(rows, key=lambda item: item["release_unix_s"])
    ]
    if decision.get("actual_session_order") != expected_order:
        raise ValueError("Decision A actual session order mismatch")
    return decision


def authorize_session(runtime: Path, run_id: str) -> None:
    load_campaign(runtime)
    authorize_session_identity(run_id)
    run_directory = Path(runtime) / "runs" / run_id
    if run_directory.exists():
        raise FileExistsError(f"run directory already exists: {run_id}")
    if failed_attempt_count(runtime, run_id) >= MAX_ATTEMPTS_PER_RUN:
        raise PermissionError(f"attempt limit exhausted for {run_id}")
    if run_id == "rs2-r20-calib":
        return
    if run_id == "rs2-pilot":
        load_calibration(runtime, 20)
        return
    formal_follow = list(FORMAL_RUN_ORDER[:3])
    if run_id in set(formal_follow):
        if not _qualification_passed(runtime):
            raise PermissionError("qualification pilot has not passed")
        index = formal_follow.index(run_id)
        _require_admissible_predecessors(runtime, formal_follow[:index])
        return
    if run_id == "decision-a":
        raise ValueError("decision-a is an offline gate, not a Unity session")
    if run_id in set(SESSION_ORDER):
        decision = validate_decision_a(runtime)
        if decision["final_action"] != "CONTINUE_REMAINING_CELLS":
            raise PermissionError(
                f"Decision A blocks further sessions: {decision['final_action']}"
            )
        predecessor_count = (
            6
            if run_id == "rs2-r5-calib"
            else FORMAL_RUN_ORDER.index(run_id)
        )
        _require_admissible_predecessors(
            runtime,
            FORMAL_RUN_ORDER[:predecessor_count],
        )
        return
    raise ValueError(f"run_id is not part of the frozen RATE-002 schedule: {run_id}")


def _require_admissible_predecessors(
    runtime: Path,
    predecessors: Sequence[str],
) -> None:
    for predecessor in predecessors:
        try:
            attempt_row(Path(runtime) / "runs" / predecessor)
        except (FileNotFoundError, ValueError, Rate2ProtocolError) as error:
            raise PermissionError(
                f"frozen order requires admissible predecessor {predecessor}"
            ) from error


def authorize_session_identity(run_id: str) -> None:
    allowed = {
        "rs2-r20-calib",
        "rs2-r5-calib",
        "rs2-pilot",
        *(
            f"rs2-r{rate}-{condition}-{replicate}"
            for rate in (5, 20)
            for condition in ("follow", "nadir")
            for replicate in (1, 2, 3)
        ),
    }
    if run_id not in allowed:
        raise ValueError(
            f"run_id is not part of the frozen RATE-002 schedule: {run_id}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="P1-M2-RATE-002 coordinator")
    parser.add_argument("--runtime", type=Path, default=RUNTIME_DEFAULT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare-campaign")

    prepare = subparsers.add_parser("prepare-session")
    prepare.add_argument("--run-id", required=True)
    prepare.add_argument("--init-frame", type=int, required=True)
    prepare.add_argument("--init-image-sha256", required=True)
    prepare.add_argument("--hold-route-s-m", type=float, required=True)

    preview = subparsers.add_parser("preview-calibration")
    preview.add_argument("--rate", type=int, choices=(5, 20), required=True)
    preview.add_argument("--box", type=float, nargs=4, required=True)

    freeze = subparsers.add_parser("freeze-calibration")
    freeze.add_argument("--rate", type=int, choices=(5, 20), required=True)
    freeze.add_argument("--confirmed", action="store_true")

    release = subparsers.add_parser("release")
    release.add_argument("--confirmed", action="store_true")
    release.add_argument("--timeout-s", type=float, default=10.0)
    release.add_argument(
        "--poll-interval-s",
        type=float,
        default=RELEASE_POLL_INTERVAL_S,
    )

    launch = subparsers.add_parser("launch")
    launch.add_argument("--condition", choices=("follow", "nadir"), required=True)
    launch.add_argument("--box", type=float, nargs=4, required=True)
    launch.add_argument("--ground-plane-y-m", type=float, required=True)
    launch.add_argument("--planned-duration-s", type=float, required=True)
    launch.add_argument("--python", type=Path, default=Path(sys.executable))

    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--run-id", required=True)

    failed = subparsers.add_parser("archive-failed-attempt")
    failed.add_argument("--run-id", required=True)
    failed.add_argument("--reason", required=True)

    subparsers.add_parser("qualify-pilot")
    decision = subparsers.add_parser("decision-a")
    decision.add_argument("--invalid-cell-exhausted", action="store_true")

    authorize = subparsers.add_parser("authorize")
    authorize.add_argument("--run-id", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    runtime = args.runtime.resolve()
    if args.command == "prepare-campaign":
        result: Any = prepare_campaign(runtime)
    elif args.command == "prepare-session":
        identity = nanotrack_identity()
        result = prepare_session(
            runtime,
            build_session(
                run_id=args.run_id,
                init_frame_id=args.init_frame,
                init_image_sha256=args.init_image_sha256,
                hold_route_s_m=args.hold_route_s_m,
                tracker_identity=identity,
            ),
        )
    elif args.command == "release":
        result = coordinate_release(
            runtime,
            confirmed=args.confirmed,
            timeout_s=args.timeout_s,
            poll_interval_s=args.poll_interval_s,
        )
    elif args.command == "preview-calibration":
        result = preview_calibration(runtime, args.rate, args.box)
    elif args.command == "freeze-calibration":
        result = freeze_calibration(
            runtime,
            args.rate,
            confirmed=args.confirmed,
        )
    elif args.command == "launch":
        completed = launch_tracker(
            python_executable=args.python,
            runtime=runtime,
            init_box=args.box,
            condition=args.condition,
            ground_plane_y_m=args.ground_plane_y_m,
            planned_duration_s=args.planned_duration_s,
        )
        raise SystemExit(completed.returncode)
    elif args.command == "finalize":
        result = finalize_attempt(runtime / "runs" / args.run_id)
    elif args.command == "archive-failed-attempt":
        result = archive_failed_attempt(runtime, args.run_id, args.reason)
    elif args.command == "qualify-pilot":
        result = qualify_pilot(runtime)
    elif args.command == "decision-a":
        result = build_decision_a(
            runtime,
            invalid_cell_exhausted=args.invalid_cell_exhausted,
        )
    elif args.command == "authorize":
        authorize_session(runtime, args.run_id)
        result = {"authorized": True, "run_id": args.run_id}
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
