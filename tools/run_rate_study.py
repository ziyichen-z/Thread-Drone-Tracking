from __future__ import annotations

import argparse
import copy
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from typing import Any, Mapping, Sequence
from controller.trackers import (
    DEFAULT_NANOTRACK_V2_MODEL_DIR,
    DEFAULT_NANOTRACK_V2_SPEC,
)
from tools.run_track_experiment import (
    PROJECT_ROOT,
    load_scenario,
    route_timing_s,
    sha256_file,
    tracker_command,
)


RUNTIME_DEFAULT = PROJECT_ROOT / "runtime"
RATE_CONFIGS = {
    5: PROJECT_ROOT / "config" / "scenario.rate-study-5hz.json",
    20: PROJECT_ROOT / "config" / "scenario.rate-study-20hz.json",
}
CONDITIONS = ("follow", "nadir")
REPLICATES = (1, 2, 3)
INIT_WINDOW_S = (7.0, 8.0)
CALIBRATION_SCHEMA = "p1-rate-study-calibration/v1"
CALIBRATION_STATUS_SCHEMA = "p1-rate-study-calibration-status/v1"
BOX_PREVIEW_SCHEMA = "p1-rate-study-box-preview/v1"
STAGE_SCHEMA = "p1-rate-study-stage/v1"
STATUS_SCHEMA = "p1-rate-study-attempt-status/v1"
SUMMARY_SCHEMA = "p1-rate-study-summary/v1"
PLANNED_DURATION_TOLERANCE_S = 1e-6
SAFE_SUFFIX = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
SLOT_FILES = (
    "tracking_observation.json",
    "gimbal_command.json",
    "body_command.json",
    "metrics.json",
)


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _finite(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _validate_box(values: Sequence[float]) -> tuple[float, float, float, float]:
    if len(values) != 4:
        raise ValueError("box must contain normalized x, y, width, height")
    x, y, width, height = (
        _finite(value, f"box[{index}]") for index, value in enumerate(values)
    )
    if x < 0.0 or y < 0.0 or width <= 0.0 or height <= 0.0:
        raise ValueError("box must have non-negative origin and positive size")
    if x + width > 1.0 or y + height > 1.0:
        raise ValueError("box must be fully inside the normalized image")
    return x, y, width, height


def scenario_for_rate(rate_hz: int) -> tuple[Path, dict[str, Any]]:
    try:
        path = RATE_CONFIGS[int(rate_hz)]
    except (KeyError, ValueError) as exception:
        raise ValueError("rate must be exactly 5 or 20 Hz") from exception
    return path, load_scenario(path)


def validate_rate_configs() -> dict[str, Any]:
    path5, config5 = scenario_for_rate(5)
    path20, config20 = scenario_for_rate(20)
    expected = {
        5: ("rate-study-5hz", 5.0, 128, 512),
        20: ("rate-study-20hz", 20.0, 512, 2048),
    }
    for rate, config in ((5, config5), (20, config20)):
        scenario_id, capture_hz, retained, pending = expected[rate]
        actual = (
            config.get("scenario_id"),
            config.get("sensor", {}).get("capture_hz"),
            config.get("sensor", {}).get("retained_frame_count"),
            config.get("evaluation", {}).get("maximum_pending_frame_count"),
        )
        if actual != (scenario_id, capture_hz, retained, pending):
            raise ValueError(
                f"{rate} Hz config does not match the accepted derived values: {actual!r}"
            )

    normalized5 = copy.deepcopy(config5)
    normalized20 = copy.deepcopy(config20)
    for config in (normalized5, normalized20):
        config["scenario_id"] = "rate-study-normalized"
        config["sensor"]["capture_hz"] = 0.0
        config["sensor"]["retained_frame_count"] = 0
        config["evaluation"]["maximum_pending_frame_count"] = 0
    if normalized5 != normalized20:
        raise ValueError(
            "rate configs differ outside scenario_id, capture_hz, "
            "retained_frame_count, and maximum_pending_frame_count"
        )

    timing5 = route_timing_s(config5)
    timing20 = route_timing_s(config20)
    if timing5 != timing20:
        raise ValueError("rate configs produce different route timing")
    return {
        "schema_version": "p1-rate-study-config-validation/v1",
        "rates_hz": [5, 20],
        "replicates_per_cell": 3,
        "measured_sessions": 12,
        "calibration_sessions": 2,
        "init_window_simulation_s": list(INIT_WINDOW_S),
        "config_sha256": {
            "5": sha256_file(path5),
            "20": sha256_file(path20),
        },
        **timing5,
    }


def install_config(rate_hz: int, runtime: Path) -> dict[str, Any]:
    validation = validate_rate_configs()
    source, scenario = scenario_for_rate(rate_hz)
    destination = Path(runtime) / "scenario_config.json"
    _atomic_bytes(destination, source.read_bytes())
    installed_hash = sha256_file(destination)
    expected_hash = validation["config_sha256"][str(rate_hz)]
    if installed_hash != expected_hash:
        raise RuntimeError("installed scenario config hash mismatch")
    return {
        "scenario_id": scenario["scenario_id"],
        "config_path": str(destination),
        "config_sha256": installed_hash,
    }


def clean_runtime_slots(runtime: Path) -> list[str]:
    runtime = Path(runtime)
    runtime.mkdir(parents=True, exist_ok=True)
    removed: list[str] = []
    for name in SLOT_FILES:
        path = runtime / name
        if path.is_file():
            path.unlink()
            removed.append(name)
    frames = runtime / "frames"
    if frames.is_dir():
        shutil.rmtree(frames)
        removed.append("frames/")
    return removed


def prepare_session(rate_hz: int, runtime: Path) -> dict[str, Any]:
    installed = install_config(rate_hz, runtime)
    removed = clean_runtime_slots(runtime)
    return {
        "schema_version": "p1-rate-study-session-preparation/v1",
        "rate_hz": rate_hz,
        **installed,
        "removed_runtime_slots": removed,
        "next_action": (
            "start a fresh Unity Play session, run past 8 s, then pause "
            "before the 25.6 s retained window discards [7,8) frames"
        ),
    }


def _frame_candidates(
    runtime: Path,
    scenario_id: str,
    start_s: float = INIT_WINDOW_S[0],
    end_s: float = INIT_WINDOW_S[1],
    *,
    expected_sensor_schema: str = "tethered-sensor-frame/v1",
) -> list[dict[str, Any]]:
    frames = Path(runtime) / "frames"
    candidates: list[dict[str, Any]] = []
    for metadata_path in frames.glob("frame_*.json"):
        metadata = _read_object(metadata_path)
        if metadata.get("scenario_id") != scenario_id:
            continue
        if metadata.get("schema_version") != expected_sensor_schema:
            raise ValueError(
                f"{metadata_path.name} has sensor schema "
                f"{metadata.get('schema_version')!r}; expected "
                f"{expected_sensor_schema!r}"
            )
        if expected_sensor_schema == "tethered-sensor-frame/v2":
            capture_monotonic_s = _finite(
                metadata.get("capture_monotonic_s"),
                "capture_monotonic_s",
            )
            if capture_monotonic_s < 0.0:
                raise ValueError("capture_monotonic_s must be non-negative")
        simulation_time_s = _finite(
            metadata.get("simulation_time_s"), "simulation_time_s"
        )
        if not start_s <= simulation_time_s < end_s:
            continue
        frame_id = int(metadata.get("frame_id", -1))
        image_path = frames / f"frame_{frame_id:010d}.jpg"
        if frame_id < 0 or not image_path.is_file():
            continue
        candidates.append(
            {
                "frame_id": frame_id,
                "simulation_time_s": simulation_time_s,
                "metadata_path": metadata_path,
                "image_path": image_path,
                "image_sha256": sha256_file(image_path),
                "metadata_sha256": sha256_file(metadata_path),
            }
        )
    candidates.sort(key=lambda item: (item["simulation_time_s"], item["frame_id"]))
    return candidates


def select_init_frame(runtime: Path, rate_hz: int) -> dict[str, Any]:
    _, scenario = scenario_for_rate(rate_hz)
    candidates = _frame_candidates(runtime, scenario["scenario_id"])
    if not candidates:
        raise FileNotFoundError(
            "no complete retained frame exists in simulation_time_s "
            f"[{INIT_WINDOW_S[0]:.1f}, {INIT_WINDOW_S[1]:.1f})"
        )
    return candidates[0]


def preview_init_frame(runtime: Path, rate_hz: int) -> dict[str, Any]:
    frame = select_init_frame(runtime, rate_hz)
    destination = Path(runtime) / "rate-study" / "previews"
    destination.mkdir(parents=True, exist_ok=True)
    image_path = destination / f"rate{rate_hz}-init.jpg"
    metadata_path = destination / f"rate{rate_hz}-init.json"
    shutil.copy2(frame["image_path"], image_path)
    shutil.copy2(frame["metadata_path"], metadata_path)
    return {
        "rate_hz": rate_hz,
        "frame_id": frame["frame_id"],
        "simulation_time_s": frame["simulation_time_s"],
        "image_sha256": frame["image_sha256"],
        "metadata_sha256": frame["metadata_sha256"],
        "preview_image": str(image_path),
        "preview_metadata": str(metadata_path),
    }


def _render_box_overlay(
    source: Path,
    destination: Path,
    box_norm: Sequence[float],
    label: str,
) -> dict[str, int]:
    import cv2

    box = _validate_box(box_norm)
    image = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"cannot decode preview image: {source}")
    height_px, width_px = image.shape[:2]
    left = max(0, min(width_px - 1, math.floor(box[0] * width_px)))
    top = max(0, min(height_px - 1, math.floor(box[1] * height_px)))
    right = max(
        left,
        min(width_px - 1, math.ceil((box[0] + box[2]) * width_px) - 1),
    )
    bottom = max(
        top,
        min(height_px - 1, math.ceil((box[1] + box[3]) * height_px) - 1),
    )
    color = (0, 255, 0)
    cv2.rectangle(image, (left, top), (right, bottom), color, 2)
    text_y = top - 7 if top >= 22 else min(height_px - 7, bottom + 18)
    cv2.putText(
        image,
        label,
        (left, text_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        color,
        2,
        cv2.LINE_AA,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(destination), image):
        raise OSError(f"failed to write box overlay: {destination}")
    return {
        "x": left,
        "y": top,
        "width": right - left + 1,
        "height": bottom - top + 1,
    }


def preview_calibration_box(
    runtime: Path,
    rate_hz: int,
    box_norm: Sequence[float],
) -> dict[str, Any]:
    box = _validate_box(box_norm)
    preview = preview_init_frame(runtime, rate_hz)
    preview_directory = Path(runtime) / "rate-study" / "previews"
    overlay_path = preview_directory / f"rate{rate_hz}-init-box.jpg"
    manifest_path = preview_directory / f"rate{rate_hz}-init-box.json"
    pixel_box = _render_box_overlay(
        Path(preview["preview_image"]),
        overlay_path,
        box,
        f"{rate_hz} Hz target",
    )
    manifest = {
        "schema_version": BOX_PREVIEW_SCHEMA,
        "rate_hz": rate_hz,
        "frame_id": preview["frame_id"],
        "simulation_time_s": preview["simulation_time_s"],
        "image_sha256": preview["image_sha256"],
        "metadata_sha256": preview["metadata_sha256"],
        "box_xywh_norm": list(box),
        "box_xywh_px": pixel_box,
        "raw_preview_image": preview["preview_image"],
        "box_overlay_image": str(overlay_path),
        "box_overlay_sha256": sha256_file(overlay_path),
    }
    _atomic_json(manifest_path, manifest)
    return {**manifest, "box_preview_manifest": str(manifest_path)}


def _expected_installed_config(runtime: Path, rate_hz: int) -> str:
    config_path, _ = scenario_for_rate(rate_hz)
    expected = sha256_file(config_path)
    installed_path = Path(runtime) / "scenario_config.json"
    if not installed_path.is_file() or sha256_file(installed_path) != expected:
        raise ValueError(
            f"runtime scenario config is not the accepted {rate_hz} Hz config"
        )
    return expected


def calibration_directory(runtime: Path, rate_hz: int) -> Path:
    return Path(runtime) / "runs" / f"rate{rate_hz}-calib"


def capture_calibration(
    runtime: Path,
    rate_hz: int,
    box_norm: Sequence[float],
    confirmed: bool,
) -> dict[str, Any]:
    if not confirmed:
        raise ValueError("calibration capture requires explicit box-overlay confirmation")
    box = _validate_box(box_norm)
    config_hash = _expected_installed_config(runtime, rate_hz)
    frame = select_init_frame(runtime, rate_hz)
    preview_manifest_path = (
        Path(runtime)
        / "rate-study"
        / "previews"
        / f"rate{rate_hz}-init-box.json"
    )
    preview_manifest = _read_object(preview_manifest_path)
    expected_preview = {
        "schema_version": BOX_PREVIEW_SCHEMA,
        "rate_hz": rate_hz,
        "frame_id": frame["frame_id"],
        "image_sha256": frame["image_sha256"],
        "metadata_sha256": frame["metadata_sha256"],
        "box_xywh_norm": list(box),
    }
    for key, expected in expected_preview.items():
        if preview_manifest.get(key) != expected:
            raise ValueError(f"calibration box preview {key} mismatch")
    overlay_path = preview_manifest_path.with_name(f"rate{rate_hz}-init-box.jpg")
    if preview_manifest.get("box_overlay_image") != str(overlay_path):
        raise ValueError("calibration box preview overlay path mismatch")
    if not overlay_path.is_file():
        raise FileNotFoundError("calibration box overlay is missing")
    if preview_manifest.get("box_overlay_sha256") != sha256_file(overlay_path):
        raise ValueError("calibration box overlay hash mismatch")
    destination = calibration_directory(runtime, rate_hz)
    destination.mkdir(parents=True, exist_ok=False)
    try:
        shutil.copy2(frame["image_path"], destination / "reference.jpg")
        shutil.copy2(frame["metadata_path"], destination / "reference.json")
        shutil.copy2(overlay_path, destination / "reference-box-preview.jpg")
        shutil.copy2(
            preview_manifest_path,
            destination / "reference-box-preview.json",
        )
        _, scenario = scenario_for_rate(rate_hz)
        manifest = {
            "schema_version": CALIBRATION_SCHEMA,
            "session_id": destination.name,
            "rate_hz": rate_hz,
            "scenario_id": scenario["scenario_id"],
            "scenario_config_sha256": config_hash,
            "init_window_simulation_s": list(INIT_WINDOW_S),
            "reference_frame_id": frame["frame_id"],
            "reference_simulation_time_s": frame["simulation_time_s"],
            "reference_image_sha256": frame["image_sha256"],
            "reference_metadata_sha256": frame["metadata_sha256"],
            "reference_box_xywh_norm": list(box),
            "reference_box_preview_sha256": sha256_file(
                destination / "reference-box-preview.jpg"
            ),
        }
        _atomic_json(destination / "manifest.json", manifest)
        return manifest
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def load_calibration(runtime: Path, rate_hz: int) -> dict[str, Any]:
    directory = calibration_directory(runtime, rate_hz)
    manifest = _read_object(directory / "manifest.json")
    if manifest.get("schema_version") != CALIBRATION_SCHEMA:
        raise ValueError(f"invalid calibration schema for {rate_hz} Hz")
    config_path, scenario = scenario_for_rate(rate_hz)
    checks = {
        "rate_hz": rate_hz,
        "scenario_id": scenario["scenario_id"],
        "scenario_config_sha256": sha256_file(config_path),
        "reference_image_sha256": sha256_file(directory / "reference.jpg"),
        "reference_metadata_sha256": sha256_file(directory / "reference.json"),
        "reference_box_preview_sha256": sha256_file(
            directory / "reference-box-preview.jpg"
        ),
    }
    for key, expected in checks.items():
        if manifest.get(key) != expected:
            raise ValueError(f"calibration {key} mismatch")
    _validate_box(manifest.get("reference_box_xywh_norm", ()))
    return manifest


def invalidate_calibration(
    runtime: Path,
    rate_hz: int,
    suffix: str,
    reason: str,
) -> Path:
    if not SAFE_SUFFIX.fullmatch(suffix) or not suffix.startswith("invalid-"):
        raise ValueError("invalid suffix must look like invalid-a")
    if not reason.strip():
        raise ValueError("invalid reason must not be empty")
    source = calibration_directory(runtime, rate_hz)
    manifest = load_calibration(runtime, rate_hz)
    invalid_id = f"{source.name}-{suffix}"
    destination = Path(runtime) / "runs" / invalid_id
    if destination.exists():
        raise FileExistsError(f"invalid calibration already exists: {invalid_id}")
    _atomic_json(
        source / "calibration-status.json",
        {
            "schema_version": CALIBRATION_STATUS_SCHEMA,
            "session_id": invalid_id,
            "invalidated_from_session_id": manifest["session_id"],
            "rate_hz": rate_hz,
            "classification": "INVALID",
            "admissible": False,
            "reason": reason.strip(),
        },
    )
    shutil.move(str(source), str(destination))
    return destination


def canonical_replicate_id(rate_hz: int, condition: str, replicate: int) -> str:
    if rate_hz not in RATE_CONFIGS:
        raise ValueError("rate must be 5 or 20")
    if condition not in CONDITIONS:
        raise ValueError("condition must be follow or nadir")
    if replicate not in REPLICATES:
        raise ValueError("replicate must be 1, 2, or 3")
    return f"rate{rate_hz}-{condition}-r{replicate}"


def stage_run(
    runtime: Path,
    rate_hz: int,
    condition: str,
    replicate: int,
    attempt_suffix: str | None = None,
) -> dict[str, Any]:
    replicate_id = canonical_replicate_id(rate_hz, condition, replicate)
    if attempt_suffix is not None and not SAFE_SUFFIX.fullmatch(attempt_suffix):
        raise ValueError("attempt suffix must use lowercase letters, digits, and dash")
    attempt_id = (
        replicate_id if attempt_suffix is None else f"{replicate_id}-{attempt_suffix}"
    )
    if (Path(runtime) / "runs" / attempt_id).exists():
        raise FileExistsError(f"run attempt already exists: {attempt_id}")
    stage_directory = Path(runtime) / "rate-study" / "staging" / attempt_id
    stage_directory.mkdir(parents=True, exist_ok=False)
    try:
        config_hash = _expected_installed_config(runtime, rate_hz)
        calibration = load_calibration(runtime, rate_hz)
        frame = select_init_frame(runtime, rate_hz)
        shutil.copy2(frame["image_path"], stage_directory / "init.jpg")
        shutil.copy2(frame["metadata_path"], stage_directory / "init.json")
        staged_box_preview = stage_directory / "init-box-preview.jpg"
        _render_box_overlay(
            stage_directory / "init.jpg",
            staged_box_preview,
            calibration["reference_box_xywh_norm"],
            f"{rate_hz} Hz frozen target",
        )
        timing = route_timing_s(scenario_for_rate(rate_hz)[1])
        stage = {
            "schema_version": STAGE_SCHEMA,
            "attempt_id": attempt_id,
            "replicate_id": replicate_id,
            "attempt_suffix": attempt_suffix,
            "rate_hz": rate_hz,
            "condition": condition,
            "replicate_index": replicate,
            "scenario_id": scenario_for_rate(rate_hz)[1]["scenario_id"],
            "scenario_config_sha256": config_hash,
            "init_window_simulation_s": list(INIT_WINDOW_S),
            "init_frame_id": frame["frame_id"],
            "init_simulation_time_s": frame["simulation_time_s"],
            "init_image_sha256": frame["image_sha256"],
            "init_metadata_sha256": frame["metadata_sha256"],
            "init_box_preview_sha256": sha256_file(staged_box_preview),
            "reference_frame_id": calibration["reference_frame_id"],
            "reference_simulation_time_s": calibration[
                "reference_simulation_time_s"
            ],
            "reference_image_sha256": calibration["reference_image_sha256"],
            "reference_box_xywh_norm": calibration["reference_box_xywh_norm"],
            "staged_init_image": str(
                Path("rate-study") / "staging" / attempt_id / "init.jpg"
            ),
            "staged_init_metadata": str(
                Path("rate-study") / "staging" / attempt_id / "init.json"
            ),
            "staged_init_box_preview": str(
                Path("rate-study")
                / "staging"
                / attempt_id
                / "init-box-preview.jpg"
            ),
            **timing,
            "visual_confirmation": "PENDING",
        }
        _atomic_json(stage_directory / "stage.json", stage)
        return stage
    except Exception:
        shutil.rmtree(stage_directory, ignore_errors=True)
        raise


def load_stage(runtime: Path, attempt_id: str) -> tuple[Path, dict[str, Any]]:
    directory = Path(runtime) / "rate-study" / "staging" / attempt_id
    stage = _read_object(directory / "stage.json")
    if stage.get("schema_version") != STAGE_SCHEMA:
        raise ValueError("invalid stage schema")
    if stage.get("attempt_id") != attempt_id:
        raise ValueError("stage attempt_id mismatch")
    return directory, stage


def invalidate_stage(
    runtime: Path,
    attempt_id: str,
    suffix: str,
    reason: str,
) -> Path:
    if not SAFE_SUFFIX.fullmatch(suffix) or not suffix.startswith("invalid-"):
        raise ValueError("invalid suffix must look like invalid-a")
    if not reason.strip():
        raise ValueError("invalid reason must not be empty")
    stage_directory, stage = load_stage(runtime, attempt_id)
    invalid_id = f"{stage['replicate_id']}-{suffix}"
    destination = Path(runtime) / "runs" / invalid_id
    if destination.exists():
        raise FileExistsError(f"invalid attempt already exists: {invalid_id}")
    stage["attempt_id"] = invalid_id
    stage["invalidated_from_stage_id"] = attempt_id
    stage["visual_confirmation"] = "FAILED"
    _atomic_json(stage_directory / "stage.json", stage)
    _atomic_json(
        stage_directory / "rate-study-status.json",
        {
            "schema_version": STATUS_SCHEMA,
            "attempt_id": invalid_id,
            "replicate_id": stage["replicate_id"],
            "classification": "INVALID",
            "reason": reason.strip(),
            "admissible": False,
        },
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(stage_directory), str(destination))
    return destination


def invalidate_completed_run(runtime: Path, attempt_id: str, reason: str) -> Path:
    if not reason.strip():
        raise ValueError("invalid reason must not be empty")
    run_directory = Path(runtime) / "runs" / attempt_id
    manifest = _read_object(run_directory / "manifest.json")
    status_path = run_directory / "rate-study-status.json"
    status = _read_object(status_path)
    if manifest.get("run_id") != attempt_id or status.get("attempt_id") != attempt_id:
        raise ValueError("attempt identity mismatch")
    if status.get("schema_version") != STATUS_SCHEMA:
        raise ValueError("invalid attempt status schema")
    status["previous_classification"] = status.get("classification")
    status["classification"] = "INVALID"
    status["admissible"] = False
    status["reason"] = reason.strip()
    _atomic_json(status_path, status)
    return status_path


def _verify_staged_frame(runtime: Path, stage: Mapping[str, Any]) -> None:
    frame_id = int(stage["init_frame_id"])
    stem = f"frame_{frame_id:010d}"
    image = Path(runtime) / "frames" / f"{stem}.jpg"
    metadata = Path(runtime) / "frames" / f"{stem}.json"
    if not image.is_file() or not metadata.is_file():
        raise FileNotFoundError("staged init frame is no longer retained")
    if sha256_file(image) != stage["init_image_sha256"]:
        raise ValueError("staged init image changed")
    if sha256_file(metadata) != stage["init_metadata_sha256"]:
        raise ValueError("staged init metadata changed")
    overlay = (
        Path(runtime)
        / "rate-study"
        / "staging"
        / str(stage["attempt_id"])
        / "init-box-preview.jpg"
    )
    if not overlay.is_file():
        raise FileNotFoundError("staged init box preview is missing")
    if sha256_file(overlay) != stage["init_box_preview_sha256"]:
        raise ValueError("staged init box preview changed")


def duration_completion(
    summary: Mapping[str, Any],
    planned_duration_s: Any,
) -> dict[str, Any]:
    planned = _finite(planned_duration_s, "planned_duration_s")
    actual = _finite(summary.get("actual_duration_s"), "actual_duration_s")
    if planned <= 0.0:
        raise ValueError("planned_duration_s must be positive")
    if actual < 0.0:
        raise ValueError("actual_duration_s must be non-negative")
    shortfall = max(0.0, planned - actual)
    return {
        "actual_duration_s": actual,
        "planned_duration_s": planned,
        "duration_tolerance_s": PLANNED_DURATION_TOLERANCE_S,
        "duration_shortfall_s": shortfall,
        "duration_complete": shortfall <= PLANNED_DURATION_TOLERANCE_S,
    }


def launch_staged_run(
    runtime: Path,
    attempt_id: str,
    python_executable: Path,
    ground_plane_y_m: float,
    confirmed: bool,
    tracker: str = "csrt",
    tracker_model_spec: Path = DEFAULT_NANOTRACK_V2_SPEC,
    tracker_model_dir: Path = DEFAULT_NANOTRACK_V2_MODEL_DIR,
) -> subprocess.CompletedProcess[str]:
    if not confirmed:
        raise ValueError("launch requires explicit visual box confirmation")
    stage_directory, stage = load_stage(runtime, attempt_id)
    rate_hz = int(stage["rate_hz"])
    _expected_installed_config(runtime, rate_hz)
    calibration = load_calibration(runtime, rate_hz)
    _verify_staged_frame(runtime, stage)
    if calibration["reference_image_sha256"] != stage["reference_image_sha256"]:
        raise ValueError("staged reference calibration changed")
    run_directory = Path(runtime) / "runs" / attempt_id
    if run_directory.exists():
        raise FileExistsError(f"run attempt already exists: {attempt_id}")

    scenario = scenario_for_rate(rate_hz)[1]
    command = tracker_command(
        python_executable=python_executable,
        runtime=Path(runtime).resolve(),
        init_frame=int(stage["init_frame_id"]),
        init_box=stage["reference_box_xywh_norm"],
        track_id=scenario["target"]["track_id"],
        scenario_id=stage["scenario_id"],
        condition=stage["condition"],
        ground_plane_y_m=_finite(ground_plane_y_m, "ground_plane_y_m"),
        planned_duration_s=float(stage["planned_duration_s"]),
        run_id=attempt_id,
        tracker=tracker,
        tracker_model_spec=tracker_model_spec,
        tracker_model_dir=tracker_model_dir,
        rate_study={
            "rate_hz": rate_hz,
            "replicate_index": stage["replicate_index"],
            "replicate_id": stage["replicate_id"],
            "attempt_id": attempt_id,
            "loop_duration_s": stage["loop_duration_s"],
            "scenario_config_sha256": stage["scenario_config_sha256"],
            "init_image_sha256": stage["init_image_sha256"],
            "reference_image_sha256": stage["reference_image_sha256"],
            "reference_frame_id": stage["reference_frame_id"],
            "reference_simulation_time_s": stage[
                "reference_simulation_time_s"
            ],
        },
    )
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        check=False,
    )
    artifact_errors: list[str] = []
    completion: dict[str, Any] | None = None
    if not run_directory.is_dir():
        artifact_errors.append("run_directory_missing")
    else:
        for source_name, destination_name in (
            ("init.jpg", "init-frame.jpg"),
            ("init.json", "init-frame.json"),
            ("init-box-preview.jpg", "init-frame-box-preview.jpg"),
            ("stage.json", "rate-study-stage.json"),
        ):
            shutil.copy2(
                stage_directory / source_name,
                run_directory / destination_name,
            )
        metrics_path = run_directory / "metrics.final.json"
        if not metrics_path.is_file():
            artifact_errors.append("metrics_final_missing")
        else:
            metrics = _read_object(metrics_path)
            if metrics.get("schema_version") != "tethered-evaluation/v1":
                artifact_errors.append("metrics_schema_mismatch")
            if metrics.get("scenario_id") != stage["scenario_id"]:
                artifact_errors.append("metrics_scenario_mismatch")
        summary_path = run_directory / "summary.json"
        if not summary_path.is_file():
            artifact_errors.append("summary_missing")
        else:
            try:
                summary = _read_object(summary_path)
                if summary.get("schema_version") != "p1-track-run/v1":
                    artifact_errors.append("summary_schema_mismatch")
                else:
                    completion = duration_completion(
                        summary, stage["planned_duration_s"]
                    )
                    if not completion["duration_complete"]:
                        artifact_errors.append("planned_duration_not_reached")
            except (TypeError, ValueError):
                artifact_errors.append("summary_duration_invalid")
    classification = "COMPLETE"
    if artifact_errors or completed.returncode not in {0, 2}:
        classification = "INVALID"
    if run_directory.is_dir():
        status = {
            "schema_version": STATUS_SCHEMA,
            "attempt_id": attempt_id,
            "replicate_id": stage["replicate_id"],
            "classification": classification,
            "admissible": classification == "COMPLETE",
            "tracker_exit_code": completed.returncode,
            "artifact_errors": artifact_errors,
            "visual_confirmation": "CONFIRMED",
        }
        if completion is not None:
            status.update(completion)
        _atomic_json(
            run_directory / "rate-study-status.json",
            status,
        )
    return completed


def _metric(metrics: Mapping[str, Any], key: str) -> float:
    aggregate = metrics.get("aggregate")
    if not isinstance(aggregate, Mapping):
        raise ValueError("metrics aggregate must be an object")
    return _finite(aggregate.get(key), f"aggregate.{key}")


def summarize_attempt(run_directory: Path) -> dict[str, Any]:
    manifest = _read_object(run_directory / "manifest.json")
    status = _read_object(run_directory / "rate-study-status.json")
    summary = _read_object(run_directory / "summary.json")
    metrics = _read_object(run_directory / "metrics.final.json")
    rate_study = manifest.get("rate_study")
    if not isinstance(rate_study, Mapping):
        raise ValueError(f"{run_directory.name} has no rate_study manifest section")
    if manifest.get("schema_version") != "p1-track-run/v1":
        raise ValueError(f"{run_directory.name} manifest schema mismatch")
    if status.get("schema_version") != STATUS_SCHEMA:
        raise ValueError(f"{run_directory.name} status schema mismatch")
    if summary.get("schema_version") != "p1-track-run/v1":
        raise ValueError(f"{run_directory.name} summary schema mismatch")
    if metrics.get("schema_version") != "tethered-evaluation/v1":
        raise ValueError(f"{run_directory.name} metrics schema mismatch")
    if manifest.get("run_id") != run_directory.name:
        raise ValueError(f"{run_directory.name} manifest run identity mismatch")
    if status.get("attempt_id") != run_directory.name:
        raise ValueError(f"{run_directory.name} status attempt identity mismatch")
    if rate_study.get("attempt_id") != run_directory.name:
        raise ValueError(f"{run_directory.name} rate-study attempt identity mismatch")
    if status.get("classification") != "COMPLETE" or not status.get("admissible"):
        raise ValueError(f"{run_directory.name} is not an admissible attempt")
    completion = duration_completion(summary, manifest.get("planned_duration_s"))
    if not completion["duration_complete"]:
        raise ValueError(
            f"{run_directory.name} did not reach planned duration: "
            f"actual={completion['actual_duration_s']:.6f}s, "
            f"planned={completion['planned_duration_s']:.6f}s, "
            f"tolerance={completion['duration_tolerance_s']:.6f}s"
        )
    if metrics.get("scenario_id") != manifest.get("scenario_id"):
        raise ValueError(f"{run_directory.name} metrics scenario mismatch")
    compute_p95 = summary.get("compute_latency_ms", {}).get("p95")
    backlog_p95 = summary.get("backlog_count", {}).get("p95")
    s1_wall_cadence = summary.get(
        "wall_clock_capture_cadence_post_launch",
        {},
    )
    wall_rate = s1_wall_cadence.get("rate_hz")
    reinit = int(summary.get("reinit_required_records", 0))
    rate_hz = int(rate_study["rate_hz"])
    condition = manifest.get("condition")
    replicate_index = int(rate_study["replicate_index"])
    expected_replicate_id = canonical_replicate_id(
        rate_hz, condition, replicate_index
    )
    if rate_study.get("replicate_id") != expected_replicate_id:
        raise ValueError(f"{run_directory.name} replicate identity mismatch")
    if status.get("replicate_id") != expected_replicate_id:
        raise ValueError(f"{run_directory.name} status replicate identity mismatch")
    config_path, expected_scenario = scenario_for_rate(rate_hz)
    if manifest.get("scenario_id") != expected_scenario["scenario_id"]:
        raise ValueError(f"{run_directory.name} scenario_id is not rate-canonical")
    if rate_study.get("scenario_config_sha256") != sha256_file(config_path):
        raise ValueError(f"{run_directory.name} scenario config hash mismatch")
    sustainable = None
    sustainability = None
    if rate_hz == 20:
        sustainability = {
            "s1_wall_capture_rate_ge_19hz": (
                s1_wall_cadence.get("strictly_increasing") is True
                and wall_rate is not None
                and float(wall_rate) >= 19.0
            ),
            "s2_compute_p95_lt_50ms": (
                compute_p95 is not None and float(compute_p95) < 50.0
            ),
            "s3_backlog_p95_le_1_no_reinit": (
                backlog_p95 is not None
                and float(backlog_p95) <= 1.0
                and reinit == 0
            ),
        }
        sustainable = all(sustainability.values())
    aggregate = metrics["aggregate"]
    return {
        "attempt_id": manifest["run_id"],
        "replicate_id": rate_study["replicate_id"],
        "rate_hz": rate_hz,
        "condition": condition,
        "replicate_index": replicate_index,
        **completion,
        "c_track": _metric(metrics, "c_track"),
        "c_geom": _metric(metrics, "c_geom"),
        "c_track_given_geom": _metric(metrics, "c_track_given_geom"),
        "matched_tracking_observations": int(
            aggregate.get("matched_tracking_observations", 0)
        ),
        "incorrect_tracking_observations": int(
            aggregate.get("incorrect_tracking_observations", 0)
        ),
        "unmatched_tracking_observations": int(
            aggregate.get("unmatched_tracking_observations", 0)
        ),
        "time_to_first_lost_s": _finite(
            summary.get("time_to_first_lost_s"), "time_to_first_lost_s"
        ),
        "time_to_first_lost_right_censored": bool(
            summary.get("time_to_first_lost_right_censored")
        ),
        "loop_duration_s": _finite(
            rate_study.get("loop_duration_s"), "loop_duration_s"
        ),
        "compute_latency_ms": summary.get("compute_latency_ms"),
        "frame_age_ms": summary.get("frame_age_ms"),
        "wall_clock_capture_cadence": summary.get(
            "wall_clock_capture_cadence"
        ),
        "wall_clock_capture_cadence_post_launch": s1_wall_cadence,
        "wall_clock_capture_window": summary.get(
            "wall_clock_capture_window"
        ),
        "simulation_time_cadence": summary.get("simulation_time_cadence"),
        "backlog_count": summary.get("backlog_count"),
        "lost_records": int(summary.get("lost_records", 0)),
        "gap_events": int(summary.get("gap_events", 0)),
        "geo_reject_events": int(summary.get("geo_reject_events", 0)),
        "reinit_required_records": reinit,
        "rate_sustainability": sustainability,
        "rate_sustainable": sustainable,
    }


def _cell_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fields = (
        "c_track",
        "c_geom",
        "c_track_given_geom",
        "time_to_first_lost_s",
    )
    result: dict[str, Any] = {"runs": len(rows)}
    for field in fields:
        values = [float(row[field]) for row in rows]
        result[field] = {
            "median": statistics.median(values),
            "minimum": min(values),
            "maximum": max(values),
        }
    return result


def summarize_runs(runtime: Path, strict: bool = True) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    invalid_attempts: list[str] = []
    for directory in sorted((Path(runtime) / "runs").glob("rate*-*-r*")):
        status_path = directory / "rate-study-status.json"
        if not status_path.is_file():
            continue
        status = _read_object(status_path)
        if status.get("classification") != "COMPLETE":
            invalid_attempts.append(directory.name)
            continue
        rows.append(summarize_attempt(directory))

    expected = {
        canonical_replicate_id(rate, condition, replicate)
        for rate in RATE_CONFIGS
        for condition in CONDITIONS
        for replicate in REPLICATES
    }
    selected: dict[str, dict[str, Any]] = {}
    duplicates: dict[str, list[str]] = {}
    for row in rows:
        replicate_id = row["replicate_id"]
        if replicate_id in selected:
            duplicates.setdefault(
                replicate_id, [selected[replicate_id]["attempt_id"]]
            ).append(row["attempt_id"])
        else:
            selected[replicate_id] = row
    missing = sorted(expected - selected.keys())
    unexpected = sorted(selected.keys() - expected)
    if strict and (missing or duplicates or unexpected):
        raise ValueError(
            f"rate study selection incomplete/ambiguous: missing={missing}, "
            f"duplicates={duplicates}, unexpected={unexpected}"
        )

    selected_rows = [selected[key] for key in sorted(selected)]
    cells: dict[str, Any] = {}
    for rate in RATE_CONFIGS:
        for condition in CONDITIONS:
            cell_rows = [
                row
                for row in selected_rows
                if row["rate_hz"] == rate and row["condition"] == condition
            ]
            if cell_rows:
                cells[f"{rate}hz-{condition}"] = _cell_summary(cell_rows)

    decision: dict[str, Any] = {"status": "INCOMPLETE"}
    if not missing and not duplicates and not unexpected:
        high_rate_rows = [row for row in selected_rows if row["rate_hz"] == 20]
        if not all(row["rate_sustainable"] for row in high_rate_rows):
            decision = {"status": "BLOCKED_RATE_UNSUSTAINABLE"}
        else:
            cell = cells["20hz-follow"]
            conditional = cell["c_track_given_geom"]["median"]
            continuity = cell["time_to_first_lost_s"]["median"]
            loop_duration = statistics.median(
                row["loop_duration_s"]
                for row in high_rate_rows
                if row["condition"] == "follow"
            )
            r1 = conditional < 0.25
            r2 = continuity < loop_duration
            decision = {
                "status": "TRIGGER_P1_TRACK_002" if r1 or r2 else "DEFER_P1_TRACK_002",
                "r1_conditional_coverage_below_25pct": r1,
                "r2_continuity_below_one_loop": r2,
                "threshold_sensitivity": {
                    str(threshold): conditional < threshold
                    for threshold in (0.15, 0.25, 0.35)
                },
                "c_track_given_geom_median": conditional,
                "time_to_first_lost_s_median": continuity,
                "loop_duration_s": loop_duration,
            }
    return {
        "schema_version": SUMMARY_SCHEMA,
        "protocol": {
            "rates_hz": [5, 20],
            "conditions": list(CONDITIONS),
            "replicates_per_cell": 3,
            "primary_outcome": "c_track",
            "analysis": "descriptive closed-loop diagnostic; not causal identification",
        },
        "selection": {
            "missing_replicates": missing,
            "duplicate_replicates": duplicates,
            "unexpected_replicates": unexpected,
            "invalid_attempts": invalid_attempts,
        },
        "runs": selected_rows,
        "cells": cells,
        "decision": decision,
    }


def render_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# P1-M2-RATE-001 generated rate-study summary",
        "",
        "This is generated diagnostic evidence. The follow/nadir × rate "
        "interaction is descriptive and does not identify a single causal mechanism.",
        "",
        "| run | rate | condition | actual/planned (s) | C_track | C_geom | C_track_given_geom | first LOST (s) | raw wall Hz | S1 post-launch Hz | sustainable |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary.get("runs", []):
        raw_wall_rate = (
            row.get("wall_clock_capture_cadence", {}) or {}
        ).get("rate_hz")
        s1_wall_rate = (
            row.get("wall_clock_capture_cadence_post_launch", {}) or {}
        ).get("rate_hz")
        raw_wall_text = (
            f"{float(raw_wall_rate):.6f}"
            if raw_wall_rate is not None
            else "N/A"
        )
        s1_wall_text = (
            f"{float(s1_wall_rate):.6f}"
            if s1_wall_rate is not None
            else "N/A"
        )
        lines.append(
            f"| {row['attempt_id']} | {row['rate_hz']} | {row['condition']} | "
            f"{row['actual_duration_s']:.3f}/{row['planned_duration_s']:.3f} | "
            f"{row['c_track']:.6f} | {row['c_geom']:.6f} | "
            f"{row['c_track_given_geom']:.6f} | "
            f"{row['time_to_first_lost_s']:.3f} | "
            f"{raw_wall_text} | {s1_wall_text} | "
            f"{row['rate_sustainable']} |"
        )
    lines.extend(
        (
            "",
            "Decision: `" + str(summary.get("decision", {}).get("status")) + "`.",
            "",
        )
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare, stage, run, and summarize P1-M2-RATE-001 sessions."
    )
    parser.add_argument("--runtime", type=Path, default=RUNTIME_DEFAULT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--rate", type=int, choices=(5, 20), required=True)

    preview = subparsers.add_parser("preview")
    preview.add_argument("--rate", type=int, choices=(5, 20), required=True)

    preview_box = subparsers.add_parser("preview-box")
    preview_box.add_argument("--rate", type=int, choices=(5, 20), required=True)
    preview_box.add_argument(
        "--box",
        type=float,
        nargs=4,
        required=True,
        metavar=("X", "Y", "WIDTH", "HEIGHT"),
    )

    calibrate = subparsers.add_parser("calibrate")
    calibrate.add_argument("--rate", type=int, choices=(5, 20), required=True)
    calibrate.add_argument("--confirmed", action="store_true")
    calibrate.add_argument(
        "--box",
        type=float,
        nargs=4,
        required=True,
        metavar=("X", "Y", "WIDTH", "HEIGHT"),
    )

    invalid_calibration = subparsers.add_parser("invalidate-calibration")
    invalid_calibration.add_argument(
        "--rate", type=int, choices=(5, 20), required=True
    )
    invalid_calibration.add_argument("--suffix", required=True)
    invalid_calibration.add_argument("--reason", required=True)

    stage = subparsers.add_parser("stage")
    stage.add_argument("--rate", type=int, choices=(5, 20), required=True)
    stage.add_argument("--condition", choices=CONDITIONS, required=True)
    stage.add_argument("--replicate", type=int, choices=REPLICATES, required=True)
    stage.add_argument("--attempt-suffix")

    invalid = subparsers.add_parser("invalidate-stage")
    invalid.add_argument("--stage-id", required=True)
    invalid.add_argument("--suffix", required=True)
    invalid.add_argument("--reason", required=True)

    invalid_run = subparsers.add_parser("invalidate-run")
    invalid_run.add_argument("--attempt-id", required=True)
    invalid_run.add_argument("--reason", required=True)

    launch = subparsers.add_parser("launch")
    launch.add_argument("--stage-id", required=True)
    launch.add_argument("--confirmed", action="store_true")
    launch.add_argument("--ground-plane-y-m", type=float, required=True)
    launch.add_argument("--python", type=Path, default=Path(sys.executable))
    launch.add_argument(
        "--tracker",
        choices=("csrt", "nanotrack-v2"),
        default="csrt",
    )
    launch.add_argument(
        "--tracker-model-spec",
        type=Path,
        default=DEFAULT_NANOTRACK_V2_SPEC,
    )
    launch.add_argument(
        "--tracker-model-dir",
        type=Path,
        default=DEFAULT_NANOTRACK_V2_MODEL_DIR,
    )

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("--allow-incomplete", action="store_true")
    summarize.add_argument(
        "--output-json",
        type=Path,
        default=RUNTIME_DEFAULT / "rate-study" / "summary.json",
    )
    summarize.add_argument(
        "--output-markdown",
        type=Path,
        default=RUNTIME_DEFAULT / "rate-study" / "summary.md",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    runtime = args.runtime.resolve()
    if args.command == "validate":
        result: Any = validate_rate_configs()
    elif args.command == "prepare":
        result = prepare_session(args.rate, runtime)
    elif args.command == "preview":
        result = preview_init_frame(runtime, args.rate)
    elif args.command == "preview-box":
        result = preview_calibration_box(runtime, args.rate, args.box)
    elif args.command == "calibrate":
        result = capture_calibration(
            runtime,
            args.rate,
            args.box,
            args.confirmed,
        )
    elif args.command == "invalidate-calibration":
        result = {
            "invalid_calibration_directory": str(
                invalidate_calibration(
                    runtime,
                    args.rate,
                    args.suffix,
                    args.reason,
                )
            )
        }
    elif args.command == "stage":
        result = stage_run(
            runtime,
            args.rate,
            args.condition,
            args.replicate,
            args.attempt_suffix,
        )
    elif args.command == "invalidate-stage":
        result = {
            "invalid_attempt_directory": str(
                invalidate_stage(
                    runtime,
                    args.stage_id,
                    args.suffix,
                    args.reason,
                )
            )
        }
    elif args.command == "invalidate-run":
        result = {
            "invalid_status": str(
                invalidate_completed_run(
                    runtime,
                    args.attempt_id,
                    args.reason,
                )
            )
        }
    elif args.command == "launch":
        completed = launch_staged_run(
            runtime,
            args.stage_id,
            args.python,
            args.ground_plane_y_m,
            args.confirmed,
            args.tracker,
            args.tracker_model_spec,
            args.tracker_model_dir,
        )
        raise SystemExit(completed.returncode)
    elif args.command == "summarize":
        result = summarize_runs(runtime, strict=not args.allow_incomplete)
        output_json = args.output_json
        output_markdown = args.output_markdown
        if output_json == RUNTIME_DEFAULT / "rate-study" / "summary.json":
            output_json = runtime / "rate-study" / "summary.json"
        if output_markdown == RUNTIME_DEFAULT / "rate-study" / "summary.md":
            output_markdown = runtime / "rate-study" / "summary.md"
        _atomic_json(output_json, result)
        output_markdown.parent.mkdir(parents=True, exist_ok=True)
        output_markdown.write_text(render_markdown(result), encoding="utf-8")
        result = {
            "summary_json": str(output_json),
            "summary_markdown": str(output_markdown),
            "decision": result["decision"],
        }
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
