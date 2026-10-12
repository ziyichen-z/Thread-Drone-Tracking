from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import tempfile
from typing import Any, Mapping, Sequence

import cv2

from controller.reanchor import load_reanchor_config
from controller.sensor_protocol import (
    SENSOR_FRAME_SCHEMA_V1,
    SENSOR_FRAME_SCHEMA_V3,
    validate_system_monotonic_frame,
)
from controller.reanchor_models import CropInvalid, DinoV2Embedder, YoloeProposer
from tools.run_rate_study import _render_box_overlay, _validate_box
from tools.run_track_experiment import PROJECT_ROOT, load_scenario, route_timing_s


WORK_ID = "P1-DETECT-001"
SESSION_SCHEMA = "p1-detect-scouting-session/v1"
REFERENCE_PREVIEW_SCHEMA = "p1-detect-scouting-reference-preview/v1"
REFERENCE_SCHEMA = "p1-detect-scouting-reference/v1"
TRUTH_SCHEMA = "p1-detect-scouting-truth/v1"
RESULT_SCHEMA = "p1-detect-scouting-result/v1"
REANALYSIS_RESULT_SCHEMA = "p1-detect-scouting-result/v2"
REANALYSIS_PLAN_SCHEMA = "p1-detect-scouting-reanalysis-plan/v1"
SUPERSESSION_SCHEMA = "p1-detect-scouting-supersession/v1"
COMPLETION_SCHEMA = "p1-detect-scouting-completion/v1"
REANALYSIS_COMPLETION_SCHEMA = "p1-detect-scouting-completion/v2"
SCENARIO_ID = "p1-detect-scouting"
SCENARIO_CONFIG = PROJECT_ROOT / "config" / "scenario.p1-detect-scouting.json"
REANCHOR_CONFIG = PROJECT_ROOT / "config" / "detector-reanchor.models.json"
DEFAULT_RUNTIME = PROJECT_ROOT / "runtime"
ACTIVE_SESSION_NAME = "p1_detect_scouting_session.json"
SESSION_ID = re.compile(r"^[a-z][a-z0-9-]{0,47}$")
LOOP_DURATION_S = 106.485
SAMPLE_HZ = 2.0
SAMPLE_INTERVAL_S = 1.0 / SAMPLE_HZ
REMOTE_SLANT_RANGE_MIN_M = 65.0
DETECTOR_CONFIDENCE_MIN = 0.25
DETECTOR_IOU_MIN = 0.30
REID_THRESHOLD = 0.5
REID_MARGIN = 0.1
INIT_WINDOW_S = (7.0, 8.0)
GIMBAL_DRIVER = "truth_directed_scouting"
RECALL_INTERPRETATION = "ORACLE_POINTED_DETECTABILITY_UPPER_BOUND"
A3_ANALYSIS_ID = "bbox-schema-v2"
A3_REASON = "BBOX_SCHEMA_MISMATCH"
BOX_OBJECT_KEYS = ("x", "y", "width", "height")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


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


def _create_once(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _session_directory(runtime: Path, session_id: str) -> Path:
    if not SESSION_ID.fullmatch(session_id):
        raise ValueError("session_id must match [a-z][a-z0-9-]{0,47}")
    return Path(runtime) / "p1-detect-scouting" / session_id


def validate_scouting_config() -> dict[str, Any]:
    scouting = load_scenario(SCENARIO_CONFIG)
    baseline = load_scenario(
        PROJECT_ROOT / "config" / "scenario.rate-study-20hz.json"
    )
    actual = (
        scouting.get("scenario_id"),
        scouting.get("sensor", {}).get("capture_hz"),
        scouting.get("sensor", {}).get("retained_frame_count"),
        scouting.get("evaluation", {}).get("maximum_pending_frame_count"),
    )
    expected = (SCENARIO_ID, 20.0, 2560, 4096)
    if actual != expected:
        raise ValueError(
            f"scouting config does not match the frozen capture contract: {actual!r}"
        )
    normalized_scouting = json.loads(json.dumps(scouting))
    normalized_baseline = json.loads(json.dumps(baseline))
    for value in (normalized_scouting, normalized_baseline):
        value["scenario_id"] = "normalized"
        value["sensor"]["retained_frame_count"] = 0
        value["evaluation"]["maximum_pending_frame_count"] = 0
    if normalized_scouting != normalized_baseline:
        raise ValueError(
            "scouting config differs from the frozen 20 Hz follow geometry "
            "outside scenario identity and retention limits"
        )
    timing = route_timing_s(scouting)
    if not math.isclose(
        timing["loop_duration_s"],
        LOOP_DURATION_S,
        abs_tol=5e-4,
    ):
        raise ValueError(
            "scouting route loop duration differs from the frozen 106.485 s"
        )
    return {
        "scenario_config": str(SCENARIO_CONFIG),
        "scenario_config_sha256": sha256_file(SCENARIO_CONFIG),
        **timing,
    }


def _session_document(session_id: str) -> dict[str, Any]:
    validation = validate_scouting_config()
    return {
        "schema_version": SESSION_SCHEMA,
        "work_id": WORK_ID,
        "session_id": session_id,
        "scenario_id": SCENARIO_ID,
        "non_measurement": True,
        "gimbal_driver": GIMBAL_DRIVER,
        "scenario_config_sha256": validation["scenario_config_sha256"],
        "loop_duration_s": LOOP_DURATION_S,
        "sample_hz": SAMPLE_HZ,
        "remote_slant_range_min_m": REMOTE_SLANT_RANGE_MIN_M,
        "detector_confidence_min": DETECTOR_CONFIDENCE_MIN,
        "detector_iou_min": DETECTOR_IOU_MIN,
    }


def prepare_session(runtime: Path, session_id: str) -> dict[str, Any]:
    runtime = Path(runtime)
    directory = _session_directory(runtime, session_id)
    active_path = runtime / ACTIVE_SESSION_NAME
    if active_path.exists():
        raise FileExistsError(
            f"active scouting session already exists: {active_path}"
        )
    if (runtime / "rate_study_session.json").exists():
        raise RuntimeError(
            "RATE-002 measurement session is active; scouting must be non-measurement"
        )
    frames = runtime / "frames"
    if frames.exists() and any(frames.iterdir()):
        raise RuntimeError(
            "runtime/frames is not empty; archive it before scouting preparation"
        )
    if (runtime / "metrics.json").exists():
        raise RuntimeError(
            "runtime/metrics.json exists; archive it before scouting preparation"
        )
    if directory.exists():
        raise FileExistsError(f"scouting session directory exists: {directory}")

    directory.mkdir(parents=True)
    installed = runtime / "scenario_config.json"
    if installed.exists():
        _create_once(
            directory / "preexisting-scenario-config.json",
            installed.read_bytes(),
        )
    _atomic_bytes(installed, SCENARIO_CONFIG.read_bytes())
    if sha256_file(installed) != sha256_file(SCENARIO_CONFIG):
        raise RuntimeError("installed scouting scenario hash mismatch")

    document = _session_document(session_id)
    payload = _json_bytes(document)
    _create_once(directory / "manifest.json", payload)
    _create_once(active_path, payload)
    return {
        **document,
        "session_directory": str(directory),
        "active_session": str(active_path),
        "next_action": (
            "start a fresh Unity Play session; the validation-only "
            "truth_directed_scouting driver owns the gimbal and discards "
            "external gimbal commands; stop between "
            "114 s and 120 s simulation time so [7,8) plus one full loop "
            "remain inside the 128 s retained window"
        ),
    }


def _load_session(runtime: Path) -> tuple[dict[str, Any], Path]:
    runtime = Path(runtime)
    active = _read_object(runtime / ACTIVE_SESSION_NAME)
    expected = _session_document(str(active.get("session_id", "")))
    if active != expected:
        raise ValueError("active scouting session differs from the frozen contract")
    directory = _session_directory(runtime, active["session_id"])
    manifest = _read_object(directory / "manifest.json")
    if manifest != active:
        raise ValueError("active scouting session and durable manifest differ")
    return active, directory


def _frame_metadata(runtime: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((Path(runtime) / "frames").glob("frame_*.json")):
        if path.name == "latest.json":
            continue
        value = _read_object(path)
        schema = value.get("schema_version")
        if schema not in {SENSOR_FRAME_SCHEMA_V1, SENSOR_FRAME_SCHEMA_V3}:
            raise ValueError(f"{path.name} is not a scouting sensor frame")
        if schema == SENSOR_FRAME_SCHEMA_V3:
            try:
                validate_system_monotonic_frame(value, context=path.name)
            except ValueError as exception:
                raise ValueError(
                    f"{path.name} has invalid system monotonic capture time"
                ) from exception
        if value.get("scenario_id") != SCENARIO_ID:
            raise ValueError(f"{path.name} has the wrong scouting scenario")
        frame_id = int(value.get("frame_id", -1))
        simulation_time = float(value.get("simulation_time_s", float("nan")))
        if frame_id < 0 or not math.isfinite(simulation_time):
            raise ValueError(f"{path.name} has invalid frame identity")
        stem = f"frame_{frame_id:010d}"
        if path.stem != stem:
            raise ValueError(f"{path.name} does not match its frame_id")
        records.append(
            {
                "frame_id": frame_id,
                "simulation_time_s": simulation_time,
                "metadata_path": path,
                "image_path": path.with_suffix(".jpg"),
            }
        )
    records.sort(key=lambda item: (item["simulation_time_s"], item["frame_id"]))
    if any(
        right["simulation_time_s"] <= left["simulation_time_s"]
        or right["frame_id"] <= left["frame_id"]
        for left, right in zip(records, records[1:])
    ):
        raise ValueError("scouting frames must be strictly increasing")
    return records


def preview_reference(runtime: Path) -> dict[str, Any]:
    session, directory = _load_session(runtime)
    candidates = [
        record
        for record in _frame_metadata(runtime)
        if INIT_WINDOW_S[0]
        <= record["simulation_time_s"]
        < INIT_WINDOW_S[1]
        and record["image_path"].is_file()
    ]
    if not candidates:
        raise ValueError("no complete scouting frame exists in [7,8) s")
    selected = candidates[0]
    destination = directory / "reference-preview.jpg"
    _create_once(destination, selected["image_path"].read_bytes())
    document = {
        "schema_version": REFERENCE_PREVIEW_SCHEMA,
        "work_id": WORK_ID,
        "session_id": session["session_id"],
        "scenario_id": SCENARIO_ID,
        "frame_id": selected["frame_id"],
        "simulation_time_s": selected["simulation_time_s"],
        "image_sha256": sha256_file(destination),
        "metadata_sha256": sha256_file(selected["metadata_path"]),
        "preview_image": str(destination),
    }
    _create_once(directory / "reference-preview.json", _json_bytes(document))
    return document


def bind_reference(
    runtime: Path,
    box_xywh_norm: Sequence[float],
) -> dict[str, Any]:
    session, directory = _load_session(runtime)
    preview = _read_object(directory / "reference-preview.json")
    if (
        preview.get("schema_version") != REFERENCE_PREVIEW_SCHEMA
        or preview.get("session_id") != session["session_id"]
    ):
        raise ValueError("invalid scouting reference preview")
    image_path = Path(str(preview["preview_image"]))
    if sha256_file(image_path) != preview.get("image_sha256"):
        raise ValueError("scouting reference preview hash mismatch")
    box = _validate_box(box_xywh_norm)
    overlay = directory / "reference-box-preview.jpg"
    if overlay.exists():
        raise FileExistsError(f"reference box preview exists: {overlay}")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=directory,
        prefix=".reference-box-preview.",
        suffix=".jpg",
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        _render_box_overlay(image_path, temporary, box, "P1-DETECT init")
        _create_once(overlay, temporary.read_bytes())
    finally:
        temporary.unlink(missing_ok=True)
    reference = {
        "schema_version": REFERENCE_SCHEMA,
        "work_id": WORK_ID,
        "session_id": session["session_id"],
        "scenario_id": SCENARIO_ID,
        "frame_id": int(preview["frame_id"]),
        "simulation_time_s": float(preview["simulation_time_s"]),
        "image_path": str(image_path),
        "image_sha256": preview["image_sha256"],
        "metadata_sha256": preview["metadata_sha256"],
        "box_xywh_norm": list(box),
        "box_preview_path": str(overlay),
        "box_preview_sha256": sha256_file(overlay),
    }
    _create_once(directory / "reference.json", _json_bytes(reference))
    return reference


def intersection_over_union(
    left: Any,
    right: Any,
) -> float:
    lx, ly, lw, lh = normalize_box(left)
    rx, ry, rw, rh = normalize_box(right)
    x1 = max(lx, rx)
    y1 = max(ly, ry)
    x2 = min(lx + lw, rx + rw)
    y2 = min(ly + lh, ry + rh)
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = lw * lh + rw * rh - intersection
    return intersection / union if union > 0.0 else 0.0


def _truth_path(directory: Path, frame_id: int) -> Path:
    return directory / "truth" / f"frame_{frame_id:010d}.json"


def _load_truth(
    path: Path,
    *,
    session_id: str,
    frame_id: int,
    simulation_time_s: float,
) -> dict[str, Any]:
    value = _read_object(path)
    if (
        value.get("schema_version") != TRUTH_SCHEMA
        or value.get("work_id") != WORK_ID
        or value.get("session_id") != session_id
        or value.get("scenario_id") != SCENARIO_ID
        or value.get("gimbal_driver") != GIMBAL_DRIVER
        or int(value.get("frame_id", -1)) != frame_id
        or not math.isclose(
            float(value.get("simulation_time_s", float("nan"))),
            simulation_time_s,
            abs_tol=1e-4,
        )
    ):
        raise ValueError(f"{path.name} has mismatched scouting truth identity")
    return value


def _summary(values: Sequence[float]) -> dict[str, Any]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return {"count": 0, "min": None, "median": None, "max": None}
    return {
        "count": len(ordered),
        "min": ordered[0],
        "median": statistics.median(ordered),
        "max": ordered[-1],
        "mean": statistics.fmean(ordered),
    }


def normalize_box(
    value: Any,
) -> tuple[float, float, float, float]:
    if isinstance(value, Mapping):
        if set(value) != set(BOX_OBJECT_KEYS) or len(value) != len(
            BOX_OBJECT_KEYS
        ):
            raise ValueError(
                "box object must contain exactly x, y, width, height"
            )
        raw = tuple(value[key] for key in BOX_OBJECT_KEYS)
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        raw = tuple(value)
    else:
        raise TypeError(
            "box must be an x/y/width/height object or four-element sequence"
        )
    if any(
        isinstance(item, bool) or not isinstance(item, (int, float))
        for item in raw
    ):
        raise TypeError("box coordinates must be JSON numbers")
    return _validate_box(raw)


def _read_image(path: Path) -> Any:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"could not read image {path}")
    return image


def _cosine_or_none(
    embedder: Any,
    reference_embedding: Sequence[float],
    image: Any,
    box: Any,
) -> tuple[float | None, str | None]:
    try:
        normalized = normalize_box(box)
        embedding = embedder.embed(image, normalized)
        return float(embedder.cosine(reference_embedding, embedding)), None
    except (CropInvalid, TypeError, ValueError):
        return None, "CROP_INVALID"


def analyze_session(
    runtime: Path,
    *,
    proposer: Any | None = None,
    embedder: Any | None = None,
    result_path: Path | None = None,
    result_schema: str = RESULT_SCHEMA,
    analysis_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    session, directory = _load_session(runtime)
    frozen_config = load_reanchor_config(REANCHOR_CONFIG)
    if (
        float(frozen_config.parameters["detector_threshold"])
        != DETECTOR_CONFIDENCE_MIN
        or float(frozen_config.parameters["reid_threshold"])
        != REID_THRESHOLD
        or float(frozen_config.parameters["ambiguity_margin"])
        != REID_MARGIN
    ):
        raise ValueError(
            "re-anchor model config differs from the frozen scouting thresholds"
        )
    reference = _read_object(directory / "reference.json")
    if (
        reference.get("schema_version") != REFERENCE_SCHEMA
        or reference.get("session_id") != session["session_id"]
    ):
        raise ValueError("invalid scouting reference")
    reference_image_path = Path(str(reference["image_path"]))
    if sha256_file(reference_image_path) != reference.get("image_sha256"):
        raise ValueError("scouting reference image hash mismatch")
    reference_metadata_path = (
        Path(runtime)
        / "frames"
        / f"frame_{int(reference['frame_id']):010d}.json"
    )
    if (
        not reference_metadata_path.is_file()
        or sha256_file(reference_metadata_path)
        != reference.get("metadata_sha256")
    ):
        raise ValueError("scouting reference metadata hash mismatch")
    reference_box = normalize_box(reference["box_xywh_norm"])

    records = _frame_metadata(runtime)
    if not records:
        raise ValueError("scouting capture contains no sensor frames")
    start = float(reference["simulation_time_s"])
    required_end = start + LOOP_DURATION_S
    if records[-1]["simulation_time_s"] < required_end:
        raise ValueError(
            "scouting capture does not cover one full loop after initialization"
        )

    if proposer is None or embedder is None:
        proposer = proposer or YoloeProposer(frozen_config)
        embedder = embedder or DinoV2Embedder(frozen_config)
    reference_image = _read_image(reference_image_path)
    proposer.initialize(reference_image, reference_box)
    reference_embedding = embedder.embed(reference_image, reference_box)

    times = [float(record["simulation_time_s"]) for record in records]
    tick_count = int(math.floor(LOOP_DURATION_S * SAMPLE_HZ)) + 1
    samples: list[dict[str, Any]] = []
    target_scores: list[float] = []
    distractor_scores: list[float] = []
    hits = 0
    denominator = 0
    missing_pairs = 0
    target_gate_passes = 0
    separation_gate_passes = 0
    separation_opportunities = 0

    for tick_index in range(tick_count):
        tick = start + tick_index * SAMPLE_INTERVAL_S
        position = bisect.bisect_left(times, tick)
        if position >= len(records) or times[position] >= tick + SAMPLE_INTERVAL_S:
            denominator += 1
            missing_pairs += 1
            samples.append(
                {
                    "tick_index": tick_index,
                    "tick_simulation_time_s": tick,
                    "status": "MISSING_SENSOR_FRAME",
                    "recall_hit": False,
                }
            )
            continue

        record = records[position]
        truth_path = _truth_path(directory, int(record["frame_id"]))
        image_path = Path(record["image_path"])
        if not truth_path.is_file() or not image_path.is_file():
            denominator += 1
            missing_pairs += 1
            samples.append(
                {
                    "tick_index": tick_index,
                    "tick_simulation_time_s": tick,
                    "frame_id": record["frame_id"],
                    "status": "MISSING_IMAGE_TRUTH_PAIR",
                    "recall_hit": False,
                }
            )
            continue

        truth = _load_truth(
            truth_path,
            session_id=session["session_id"],
            frame_id=int(record["frame_id"]),
            simulation_time_s=float(record["simulation_time_s"]),
        )
        range_m = float(truth.get("target_slant_range_m", float("nan")))
        if (
            not bool(truth.get("target_visible"))
            or not math.isfinite(range_m)
            or range_m < REMOTE_SLANT_RANGE_MIN_M
        ):
            continue

        denominator += 1
        target_box = truth.get("target_bbox_xywh_norm")
        if target_box is None:
            samples.append(
                {
                    "tick_index": tick_index,
                    "tick_simulation_time_s": tick,
                    "frame_id": record["frame_id"],
                    "status": "TARGET_BOX_MISSING",
                    "recall_hit": False,
                }
            )
            continue

        image = _read_image(image_path)
        batch = proposer.propose(image)
        proposal_ious = [
            intersection_over_union(box, target_box)
            for box, confidence in zip(batch.boxes_norm, batch.confidences)
            if float(confidence) >= DETECTOR_CONFIDENCE_MIN
        ]
        maximum_iou = max(proposal_ious, default=0.0)
        hit = maximum_iou >= DETECTOR_IOU_MIN
        if hit:
            hits += 1

        target_cosine, target_error = _cosine_or_none(
            embedder,
            reference_embedding,
            image,
            target_box,
        )
        if target_cosine is not None:
            target_scores.append(target_cosine)
            if target_cosine >= REID_THRESHOLD:
                target_gate_passes += 1

        per_distractor: list[dict[str, Any]] = []
        frame_distractor_scores: list[float] = []
        raw_distractors = truth.get("distractors")
        if not isinstance(raw_distractors, list):
            raise ValueError(f"{truth_path.name} lacks distractor truth")
        for distractor in raw_distractors:
            if not isinstance(distractor, Mapping):
                raise ValueError(f"{truth_path.name} has invalid distractor truth")
            score, error = _cosine_or_none(
                embedder,
                reference_embedding,
                image,
                distractor.get("bbox_xywh_norm"),
            )
            if score is not None:
                distractor_scores.append(score)
                frame_distractor_scores.append(score)
            per_distractor.append(
                {
                    "distractor_id": distractor.get("distractor_id"),
                    "cosine": score,
                    "error": error,
                }
            )
        if target_cosine is not None and frame_distractor_scores:
            separation_opportunities += 1
            if (
                target_cosine >= REID_THRESHOLD
                and target_cosine - max(frame_distractor_scores) >= REID_MARGIN
            ):
                separation_gate_passes += 1

        samples.append(
            {
                "tick_index": tick_index,
                "tick_simulation_time_s": tick,
                "frame_id": record["frame_id"],
                "simulation_time_s": record["simulation_time_s"],
                "target_slant_range_m": range_m,
                "status": "REMOTE_VISIBLE",
                "proposal_count": len(batch.boxes_norm),
                "maximum_target_iou": maximum_iou,
                "recall_hit": hit,
                "target_cosine": target_cosine,
                "target_embedding_error": target_error,
                "distractors": per_distractor,
            }
        )

    if denominator == 0:
        raise ValueError("scouting capture has no remote-visible or missing samples")
    recall = hits / denominator
    recall_decision = (
        "GO_CURRENT_GEOMETRY"
        if recall >= 0.5
        else "RETURN_TO_USER_OPTION_B"
    )
    overall_decision = (
        "RETURN_TO_USER_OPTION_B"
        if recall_decision == "RETURN_TO_USER_OPTION_B"
        else "AWAITING_EMBEDDING_FEASIBILITY_REVIEW"
    )
    result = {
        "schema_version": result_schema,
        "work_id": WORK_ID,
        "session": session,
        "reference": reference,
        "model_identity": {
            "reanchor_config_path": str(REANCHOR_CONFIG),
            "reanchor_config_sha256": sha256_file(REANCHOR_CONFIG),
            "detector_weights_sha256": frozen_config.detector["sha256"],
            "appearance_weights_sha256": frozen_config.appearance["weights"][
                "sha256"
            ],
            "appearance_source_sha256": frozen_config.appearance["source"][
                "archive_sha256"
            ],
        },
        "frozen_protocol": {
            "loop_duration_s": LOOP_DURATION_S,
            "sample_hz": SAMPLE_HZ,
            "remote_slant_range_min_m": REMOTE_SLANT_RANGE_MIN_M,
            "detector_confidence_min": DETECTOR_CONFIDENCE_MIN,
            "detector_iou_min": DETECTOR_IOU_MIN,
            "recall_go_min": 0.5,
            "reid_threshold": REID_THRESHOLD,
            "reid_margin": REID_MARGIN,
            "missing_pair_policy": "COUNT_AS_RECALL_MISS",
            "gimbal_driver": GIMBAL_DRIVER,
        },
        "recall": {
            "hits": hits,
            "denominator": denominator,
            "value": recall,
            "missing_pair_misses": missing_pairs,
            "decision": recall_decision,
            "interpretation": RECALL_INTERPRETATION,
            "closed_loop_recall_claimed": False,
        },
        "embedding": {
            "target_cosine": _summary(target_scores),
            "distractor_cosine": _summary(distractor_scores),
            "target_threshold_passes": target_gate_passes,
            "target_score_count": len(target_scores),
            "separation_margin_passes": separation_gate_passes,
            "separation_opportunities": separation_opportunities,
            "feasibility_decision": "REQUIRES_REVIEW",
        },
        "overall_decision": overall_decision,
        "samples": samples,
    }
    if analysis_identity is not None:
        result["analysis_identity"] = dict(analysis_identity)
    destination = result_path or directory / "scouting-result.json"
    _create_once(destination, _json_bytes(result))
    return result


def _create_or_validate_document(
    path: Path,
    document: Mapping[str, Any],
) -> dict[str, Any]:
    expected = dict(document)
    if path.exists():
        actual = _read_object(path)
        if actual != expected:
            raise ValueError(f"{path.name} differs from the frozen document")
        return actual
    _create_once(path, _json_bytes(expected))
    return expected


def reanalyze_a3_session(
    runtime: Path,
    *,
    supersedes_result_sha256: str,
    proposer: Any | None = None,
    embedder: Any | None = None,
) -> dict[str, Any]:
    runtime = Path(runtime)
    session, directory = _load_session(runtime)
    if not re.fullmatch(r"[0-9a-f]{64}", supersedes_result_sha256):
        raise ValueError("superseded result hash must be lowercase SHA-256")
    if (directory / "completion.json").exists():
        raise RuntimeError("completed scouting session cannot be reanalyzed")

    superseded_path = directory / "scouting-result.json"
    if not superseded_path.is_file():
        raise FileNotFoundError("canonical scouting result does not exist")
    actual_superseded_sha256 = sha256_file(superseded_path)
    if actual_superseded_sha256 != supersedes_result_sha256:
        raise ValueError("canonical scouting result hash does not match")
    superseded = _read_object(superseded_path)
    if (
        superseded.get("schema_version") != RESULT_SCHEMA
        or superseded.get("work_id") != WORK_ID
        or superseded.get("session") != session
    ):
        raise ValueError("canonical scouting result identity mismatch")

    result_name = f"scouting-result-{A3_ANALYSIS_ID}.json"
    receipt_name = f"supersession-{A3_ANALYSIS_ID}.json"
    plan = {
        "schema_version": REANALYSIS_PLAN_SCHEMA,
        "work_id": WORK_ID,
        "session_id": session["session_id"],
        "analysis_id": A3_ANALYSIS_ID,
        "reason": A3_REASON,
        "superseded_result_path": str(superseded_path),
        "superseded_result_sha256": supersedes_result_sha256,
        "reanalysis_result_path": str(directory / result_name),
        "accepted_box_schemas": [
            "FINITE_OBJECT_EXACT_KEYS_X_Y_WIDTH_HEIGHT",
            "FINITE_FOUR_ELEMENT_SEQUENCE",
        ],
    }
    plan_path = directory / f"reanalysis-{A3_ANALYSIS_ID}.json"
    _create_or_validate_document(plan_path, plan)
    analysis_identity = {
        "analysis_id": A3_ANALYSIS_ID,
        "reason": A3_REASON,
        "reanalysis_plan_sha256": sha256_file(plan_path),
        "supersedes_result_sha256": supersedes_result_sha256,
    }
    result_path = directory / result_name
    if result_path.exists():
        result = _read_object(result_path)
        if (
            result.get("schema_version") != REANALYSIS_RESULT_SCHEMA
            or result.get("work_id") != WORK_ID
            or result.get("session") != session
            or result.get("analysis_identity") != analysis_identity
        ):
            raise ValueError("existing A3 reanalysis result identity mismatch")
    else:
        result = analyze_session(
            runtime,
            proposer=proposer,
            embedder=embedder,
            result_path=result_path,
            result_schema=REANALYSIS_RESULT_SCHEMA,
            analysis_identity=analysis_identity,
        )

    receipt = {
        "schema_version": SUPERSESSION_SCHEMA,
        "work_id": WORK_ID,
        "session_id": session["session_id"],
        "analysis_id": A3_ANALYSIS_ID,
        "reason": A3_REASON,
        "superseded_result_path": str(superseded_path),
        "superseded_result_sha256": supersedes_result_sha256,
        "reanalysis_result_path": str(result_path),
        "reanalysis_result_sha256": sha256_file(result_path),
        "reanalysis_plan_sha256": sha256_file(plan_path),
    }
    receipt_path = directory / receipt_name
    _create_or_validate_document(receipt_path, receipt)
    return {"result": result, "supersession": receipt}


def close_session(
    runtime: Path,
    *,
    analysis_id: str | None = None,
) -> dict[str, Any]:
    runtime = Path(runtime)
    session, directory = _load_session(runtime)
    if analysis_id is None:
        if (directory / f"reanalysis-{A3_ANALYSIS_ID}.json").exists():
            raise RuntimeError(
                "A3 reanalysis plan exists; canonical result cannot be closed"
            )
        result_path = directory / "scouting-result.json"
        result_schema = RESULT_SCHEMA
        completion_schema = COMPLETION_SCHEMA
        supersession_path = None
    elif analysis_id == A3_ANALYSIS_ID:
        result_path = directory / f"scouting-result-{analysis_id}.json"
        result_schema = REANALYSIS_RESULT_SCHEMA
        completion_schema = REANALYSIS_COMPLETION_SCHEMA
        supersession_path = directory / f"supersession-{analysis_id}.json"
    else:
        raise ValueError("unsupported scouting analysis identity")
    result = _read_object(result_path)
    if (
        result.get("schema_version") != result_schema
        or result.get("work_id") != WORK_ID
        or result.get("session") != session
    ):
        raise ValueError("invalid scouting result identity")
    supersession_sha256 = None
    if supersession_path is not None:
        supersession = _read_object(supersession_path)
        superseded_path = directory / "scouting-result.json"
        if (
            supersession.get("schema_version") != SUPERSESSION_SCHEMA
            or supersession.get("work_id") != WORK_ID
            or supersession.get("session_id") != session["session_id"]
            or supersession.get("analysis_id") != analysis_id
            or supersession.get("reason") != A3_REASON
            or result.get("analysis_identity", {}).get("analysis_id")
            != analysis_id
            or result.get("analysis_identity", {}).get(
                "supersedes_result_sha256"
            )
            != sha256_file(superseded_path)
            or supersession.get("superseded_result_sha256")
            != sha256_file(superseded_path)
            or supersession.get("reanalysis_result_sha256")
            != sha256_file(result_path)
        ):
            raise ValueError("invalid scouting supersession receipt")
        supersession_sha256 = sha256_file(supersession_path)
    completion = {
        "schema_version": completion_schema,
        "work_id": WORK_ID,
        "session_id": session["session_id"],
        "result_sha256": sha256_file(result_path),
        "overall_decision": result.get("overall_decision"),
    }
    if analysis_id is not None:
        completion["analysis_id"] = analysis_id
        completion["supersession_receipt_sha256"] = supersession_sha256
    _create_once(directory / "completion.json", _json_bytes(completion))
    active_path = runtime / ACTIVE_SESSION_NAME
    if active_path.read_bytes() != (directory / "manifest.json").read_bytes():
        raise ValueError("active scouting session changed before close")
    active_path.unlink()
    return completion


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare and evaluate the frozen P1-DETECT-001 scouting gate."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    prepare.add_argument("--session-id", required=True)

    preview = subparsers.add_parser("preview-reference")
    preview.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)

    bind = subparsers.add_parser("bind-reference")
    bind.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    bind.add_argument(
        "--box",
        type=float,
        nargs=4,
        required=True,
        metavar=("X", "Y", "WIDTH", "HEIGHT"),
    )

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)

    reanalyze = subparsers.add_parser("reanalyze-a3")
    reanalyze.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    reanalyze.add_argument(
        "--supersedes-result-sha256",
        required=True,
    )

    close = subparsers.add_parser("close")
    close.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    close.add_argument("--analysis-id", choices=(A3_ANALYSIS_ID,))
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_argument_parser().parse_args(argv)
    if args.command == "prepare":
        value = prepare_session(args.runtime, args.session_id)
    elif args.command == "preview-reference":
        value = preview_reference(args.runtime)
    elif args.command == "bind-reference":
        value = bind_reference(args.runtime, args.box)
    elif args.command == "analyze":
        value = analyze_session(args.runtime)
    elif args.command == "reanalyze-a3":
        value = reanalyze_a3_session(
            args.runtime,
            supersedes_result_sha256=args.supersedes_result_sha256,
        )
    elif args.command == "close":
        value = close_session(args.runtime, analysis_id=args.analysis_id)
    else:
        raise AssertionError(args.command)
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
