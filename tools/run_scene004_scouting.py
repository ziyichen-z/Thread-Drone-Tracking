"""P1-SCENE-004 `scout-3` scouting profile.

Deliberately a separate module from `tools/run_detector_scouting.py`. That
module carries the frozen DETECT-001 §8 protocol and the closed, immutable
`p1-detect-001-scout-1` chain; the accepted design keeps the legacy profile
and its read-only audit exactly as they are. Only pure helpers are reused
from it, so no legacy behaviour can drift.

What is different here, and why:

* **Accounting classes (BC2).** Every published frame yields a truth
  document. Each analysis tick lands in exactly one class:

  - `PAIRED_VISIBLE` — target visible with a canonical box. This is the
    **only** class in the gating denominator.
  - `TARGET_VISIBLE_UNPROJECTABLE` — visible but the box cannot be projected
    into the frame. The detector cannot find what is off-frame, so scoring
    this as a miss would launder a pointing fact into a recall number. Own
    class, own rate gate, never in the gating denominator.
  - `MISSING_IMAGE_TRUTH_PAIR` — no sidecar or no image. Capture health.
  - `TARGET_NOT_VISIBLE` — occluded; outside the analysis entirely.

* **Health gate first (B3).** Missing-pair rate > 5% or unprojectable rate
  > 2% is `CAPTURE_INCOMPLETE`, decided **before** recall. scout-1 lost
  18/45 samples to missing pairs while still counting as a complete capture,
  which alone would cap recall at 0.60 and trip a 0.7 gate — reporting a
  write-path defect as "detection is infeasible in the benign envelope".

* **Two denominators, one gate.** The strict denominator gates; the
  conservative denominator (strict + unprojectable + missing) is reported
  alongside. Which one gates is frozen here, before any capture exists.

* **Dual truth schema.** v2 carries the explicit box status; v1 is accepted
  read-only for legacy cross-checks, where a present box means `VALID`.

Nothing here tunes a threshold, and no decision is automatic: sufficient
separation evidence yields `AWAITING_EMBEDDING_FEASIBILITY_REVIEW`, never a
GO.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from controller.reanchor import load_reanchor_config
from controller.reanchor_models import DinoV2Embedder, YoloeProposer
from tools.run_detector_scouting import (
    DETECTOR_CONFIDENCE_MIN,
    DETECTOR_IOU_MIN,
    GIMBAL_DRIVER,
    REANCHOR_CONFIG,
    REID_MARGIN,
    REID_THRESHOLD,
    _cosine_or_none,
    _create_once,
    _json_bytes,
    _read_image,
    _read_object,
    _summary,
    intersection_over_union,
    normalize_box,
    sha256_file,
)
from tools.run_track_experiment import PROJECT_ROOT
from controller.sensor_protocol import (
    SENSOR_FRAME_SCHEMA_V1,
    SENSOR_FRAME_SCHEMA_V3,
    validate_system_monotonic_frame,
)

WORK_ID = "P1-SCENE-004"
PROFILE_ID = "p1-scene-004-scout-3/v1"
SCENARIO_ID = "p1-scene-004"
SCENARIO_CONFIG = PROJECT_ROOT / "config" / "scenario.p1-scene-004.json"
GEOMETRY_ARTIFACT = (
    PROJECT_ROOT / "docs" / "evidence" / "P1-SCENE-004-geometry.json"
)
SESSION_SCHEMA = "p1-scene-004-scouting-session/v1"
RESULT_SCHEMA = "p1-scene-004-scouting-result/v1"
TRUTH_SCHEMA_V1 = "p1-detect-scouting-truth/v1"
TRUTH_SCHEMA_V2 = "p1-detect-scouting-truth/v2"

BOX_STATUS_VALID = "VALID"
BOX_STATUS_UNPROJECTABLE = "TARGET_VISIBLE_UNPROJECTABLE"
BOX_STATUS_NOT_VISIBLE = "TARGET_NOT_VISIBLE"

SAMPLE_HZ = 2.0
SAMPLE_INTERVAL_S = 1.0 / SAMPLE_HZ
MINIMUM_LOOPS = 3
GATING_RECALL_MIN = 0.7
MISSING_PAIR_RATE_MAX = 0.05
UNPROJECTABLE_RATE_MAX = 0.02
DISTRACTOR_SAMPLE_MIN = 10
RECALL_INTERPRETATION = "ORACLE_POINTED_DETECTABILITY_UPPER_BOUND"
SCENARIO_LABEL = "benign-coverage carrier development scenario"

CLASS_PAIRED_VISIBLE = "PAIRED_VISIBLE"
CLASS_UNPROJECTABLE = BOX_STATUS_UNPROJECTABLE
CLASS_MISSING_PAIR = "MISSING_IMAGE_TRUTH_PAIR"
CLASS_NOT_VISIBLE = BOX_STATUS_NOT_VISIBLE


def loop_period_s() -> float:
    """Loop period from the frozen geometry artifact, never hardcoded."""
    return float(_read_object(GEOMETRY_ARTIFACT)["geometry"]["loop_period_s"])


def _frames(runtime: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((Path(runtime) / "frames").glob("frame_*.json")):
        value = _read_object(path)
        schema = value.get("schema_version")
        if schema not in {SENSOR_FRAME_SCHEMA_V1, SENSOR_FRAME_SCHEMA_V3}:
            raise ValueError(f"{path.name} is not a sensor frame")
        if schema == SENSOR_FRAME_SCHEMA_V3:
            try:
                validate_system_monotonic_frame(value, context=path.name)
            except ValueError as exception:
                raise ValueError(
                    f"{path.name} has invalid system monotonic capture time"
                ) from exception
        if value.get("scenario_id") != SCENARIO_ID:
            # Cross-profile rejection: a scout-1 capture cannot be analysed
            # with the scout-3 profile, and vice versa.
            raise ValueError(
                f"{path.name} belongs to scenario {value.get('scenario_id')!r}, "
                f"not {SCENARIO_ID!r}"
            )
        frame_id = int(value.get("frame_id", -1))
        simulation_time = float(value.get("simulation_time_s", float("nan")))
        if frame_id < 0 or not math.isfinite(simulation_time):
            raise ValueError(f"{path.name} has invalid frame identity")
        if path.stem != f"frame_{frame_id:010d}":
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
        raise ValueError("frames must be strictly increasing")
    return records


def classify_truth(truth: Mapping[str, Any]) -> str:
    """Accounting class of one truth document. Dual schema (v1 read-only)."""
    schema = truth.get("schema_version")
    if schema not in (TRUTH_SCHEMA_V1, TRUTH_SCHEMA_V2):
        raise ValueError(f"unsupported truth schema {schema!r}")
    if not bool(truth.get("target_visible")):
        return CLASS_NOT_VISIBLE
    box = truth.get("target_bbox_xywh_norm")
    if schema == TRUTH_SCHEMA_V1:
        # Legacy documents carry no status; a present box means VALID and an
        # absent one cannot be distinguished from an unprojectable box.
        return CLASS_PAIRED_VISIBLE if box is not None else CLASS_UNPROJECTABLE
    status = truth.get("target_box_status")
    if status == BOX_STATUS_VALID and box is not None:
        return CLASS_PAIRED_VISIBLE
    if status == BOX_STATUS_UNPROJECTABLE:
        return CLASS_UNPROJECTABLE
    if status == BOX_STATUS_NOT_VISIBLE:
        return CLASS_NOT_VISIBLE
    raise ValueError(f"invalid target_box_status {status!r} for a visible target")


def _load_truth(
    path: Path,
    *,
    session_id: str,
    frame_id: int,
    simulation_time_s: float,
) -> dict[str, Any]:
    value = _read_object(path)
    if (
        value.get("session_id") != session_id
        or value.get("scenario_id") != SCENARIO_ID
        or value.get("gimbal_driver") != GIMBAL_DRIVER
        or int(value.get("frame_id", -1)) != frame_id
        or not math.isclose(
            float(value.get("simulation_time_s", float("nan"))),
            simulation_time_s,
            abs_tol=1e-4,
        )
    ):
        raise ValueError(f"{path.name} has mismatched truth identity")
    return value


def analyze_session(
    runtime: Path,
    *,
    session_id: str,
    proposer: Any | None = None,
    embedder: Any | None = None,
    result_path: Path | None = None,
) -> dict[str, Any]:
    runtime = Path(runtime)
    directory = _session_directory(runtime, session_id)
    session = _read_object(directory / "manifest.json")
    if (
        session.get("schema_version") != SESSION_SCHEMA
        or session.get("work_id") != WORK_ID
        or session.get("profile_id") != PROFILE_ID
        or session.get("scenario_id") != SCENARIO_ID
        or session.get("session_id") != session_id
        or session.get("gimbal_driver") != GIMBAL_DRIVER
    ):
        raise ValueError("scout-3 manifest identity is invalid")
    if session.get("scenario_config_sha256") != sha256_file(SCENARIO_CONFIG):
        raise ValueError("scout-3 session is bound to different scenario bytes")
    if session.get("geometry_sha256") != sha256_file(GEOMETRY_ARTIFACT):
        raise ValueError("scout-3 session is bound to a different geometry artifact")

    reference = _read_object(directory / "reference.json")
    reference_image_path = directory / "reference-preview.jpg"
    if sha256_file(reference_image_path) != reference.get("image_sha256"):
        raise ValueError("reference image hash mismatch")
    reference_box = normalize_box(reference["box_xywh_norm"])

    frozen_config = load_reanchor_config(REANCHOR_CONFIG)
    if (
        float(frozen_config.parameters["detector_threshold"]) != DETECTOR_CONFIDENCE_MIN
        or float(frozen_config.parameters["reid_threshold"]) != REID_THRESHOLD
        or float(frozen_config.parameters["ambiguity_margin"]) != REID_MARGIN
    ):
        raise ValueError("model config differs from the frozen scouting thresholds")
    if proposer is None:
        proposer = YoloeProposer(frozen_config)
    if embedder is None:
        embedder = DinoV2Embedder(frozen_config)
    reference_image = _read_image(reference_image_path)
    proposer.initialize(reference_image, reference_box)
    reference_embedding = embedder.embed(reference_image, reference_box)

    records = _frames(runtime)
    if not records:
        raise ValueError("scout-3 capture contains no sensor frames")
    times = [float(record["simulation_time_s"]) for record in records]
    start = float(reference["simulation_time_s"])
    period = loop_period_s()
    window = period * MINIMUM_LOOPS
    if times[-1] < start + window:
        raise ValueError(
            f"capture covers {times[-1] - start:.3f} s after initialisation, "
            f"short of the required {window:.3f} s ({MINIMUM_LOOPS} loops)"
        )

    tick_count = int(math.floor(window * SAMPLE_HZ)) + 1
    samples: list[dict[str, Any]] = []
    counts = {
        CLASS_PAIRED_VISIBLE: 0,
        CLASS_UNPROJECTABLE: 0,
        CLASS_MISSING_PAIR: 0,
        CLASS_NOT_VISIBLE: 0,
    }
    hits = 0
    target_scores: list[float] = []
    distractor_scores: list[float] = []
    target_gate_passes = 0
    separation_opportunities = 0
    separation_gate_passes = 0
    slant_ranges: list[float] = []

    for tick_index in range(tick_count):
        tick = start + tick_index * SAMPLE_INTERVAL_S
        position = bisect.bisect_left(times, tick)
        record = (
            records[position]
            if position < len(records)
            and times[position] < tick + SAMPLE_INTERVAL_S
            else None
        )
        if record is None:
            counts[CLASS_MISSING_PAIR] += 1
            samples.append(
                {
                    "tick_index": tick_index,
                    "tick_simulation_time_s": tick,
                    "accounting_class": CLASS_MISSING_PAIR,
                    "reason": "NO_SENSOR_FRAME",
                    "recall_hit": False,
                }
            )
            continue

        frame_id = int(record["frame_id"])
        truth_path = directory / "truth" / f"frame_{frame_id:010d}.json"
        image_path = Path(record["image_path"])
        if not truth_path.is_file() or not image_path.is_file():
            counts[CLASS_MISSING_PAIR] += 1
            samples.append(
                {
                    "tick_index": tick_index,
                    "tick_simulation_time_s": tick,
                    "frame_id": frame_id,
                    "accounting_class": CLASS_MISSING_PAIR,
                    "reason": "NO_TRUTH_OR_IMAGE",
                    "recall_hit": False,
                }
            )
            continue

        truth = _load_truth(
            truth_path,
            session_id=session_id,
            frame_id=frame_id,
            simulation_time_s=float(record["simulation_time_s"]),
        )
        accounting_class = classify_truth(truth)
        counts[accounting_class] += 1
        if accounting_class != CLASS_PAIRED_VISIBLE:
            samples.append(
                {
                    "tick_index": tick_index,
                    "tick_simulation_time_s": tick,
                    "frame_id": frame_id,
                    "accounting_class": accounting_class,
                    "recall_hit": False,
                }
            )
            continue

        target_box = truth["target_bbox_xywh_norm"]
        range_m = float(truth.get("target_slant_range_m", float("nan")))
        slant_ranges.append(range_m)
        image = _read_image(image_path)
        batch = proposer.propose(image)
        ious = [
            intersection_over_union(box, target_box)
            for box, confidence in zip(batch.boxes_norm, batch.confidences)
            if float(confidence) >= DETECTOR_CONFIDENCE_MIN
        ]
        maximum_iou = max(ious, default=0.0)
        hit = maximum_iou >= DETECTOR_IOU_MIN
        if hit:
            hits += 1

        target_cosine, target_error = _cosine_or_none(
            embedder, reference_embedding, image, target_box
        )
        if target_cosine is not None:
            target_scores.append(target_cosine)
            if target_cosine >= REID_THRESHOLD:
                target_gate_passes += 1
        frame_distractor_scores: list[float] = []
        per_distractor: list[dict[str, Any]] = []
        for distractor in truth.get("distractors") or []:
            box = distractor.get("bbox_xywh_norm")
            status = distractor.get("box_status")
            if box is None or (
                status is not None and status != BOX_STATUS_VALID
            ):
                per_distractor.append(
                    {
                        "distractor_id": distractor.get("distractor_id"),
                        "cosine": None,
                        "error": status or BOX_STATUS_UNPROJECTABLE,
                    }
                )
                continue
            score, error = _cosine_or_none(
                embedder, reference_embedding, image, box
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
                "frame_id": frame_id,
                "simulation_time_s": record["simulation_time_s"],
                "accounting_class": CLASS_PAIRED_VISIBLE,
                "target_slant_range_m": range_m,
                "proposal_count": len(batch.boxes_norm),
                "maximum_target_iou": maximum_iou,
                "recall_hit": hit,
                "target_cosine": target_cosine,
                "target_embedding_error": target_error,
                "distractors": per_distractor,
            }
        )

    strict = counts[CLASS_PAIRED_VISIBLE]
    conservative = strict + counts[CLASS_UNPROJECTABLE] + counts[CLASS_MISSING_PAIR]
    if conservative == 0:
        raise ValueError("analysis window contains no scoreable ticks")
    missing_rate = counts[CLASS_MISSING_PAIR] / conservative
    unprojectable_rate = counts[CLASS_UNPROJECTABLE] / conservative
    strict_recall = hits / strict if strict else 0.0
    conservative_recall = hits / conservative

    # Health first (B3): a capture defect must never be reported as a
    # detectability finding.
    if missing_rate > MISSING_PAIR_RATE_MAX:
        decision = "CAPTURE_INCOMPLETE"
        reason = "MISSING_PAIR_RATE_ABOVE_LIMIT"
    elif unprojectable_rate > UNPROJECTABLE_RATE_MAX:
        decision = "CAPTURE_INCOMPLETE"
        reason = "UNPROJECTABLE_RATE_ABOVE_LIMIT"
    elif strict < 1:
        decision = "CAPTURE_INCOMPLETE"
        reason = "NO_PAIRED_VISIBLE_SAMPLES"
    elif strict_recall < GATING_RECALL_MIN:
        decision = "BENIGN_ENVELOPE_INFEASIBLE"
        reason = "STRICT_RECALL_BELOW_GATE"
    elif len(distractor_scores) < DISTRACTOR_SAMPLE_MIN:
        decision = "SEPARATION_EVIDENCE_INSUFFICIENT"
        reason = "DISTRACTOR_SAMPLES_BELOW_MINIMUM"
    else:
        decision = "AWAITING_EMBEDDING_FEASIBILITY_REVIEW"
        reason = "RECALL_AND_SEPARATION_EVIDENCE_SUFFICIENT"

    tail_threshold = (
        sorted(slant_ranges)[int(0.75 * (len(slant_ranges) - 1))]
        if slant_ranges
        else None
    )
    tail_samples = [
        sample
        for sample in samples
        if sample.get("accounting_class") == CLASS_PAIRED_VISIBLE
        and tail_threshold is not None
        and float(sample["target_slant_range_m"]) >= tail_threshold
    ]

    result = {
        "schema_version": RESULT_SCHEMA,
        "work_id": WORK_ID,
        "profile_id": PROFILE_ID,
        "scenario_label": SCENARIO_LABEL,
        "session": session,
        "reference": reference,
        "model_identity": {
            "reanchor_config_path": str(REANCHOR_CONFIG),
            "reanchor_config_sha256": sha256_file(REANCHOR_CONFIG),
            "detector_weights_sha256": frozen_config.detector["sha256"],
            "appearance_weights_sha256": frozen_config.appearance["weights"]["sha256"],
        },
        "frozen_protocol": {
            "loop_period_s": period,
            "minimum_loops": MINIMUM_LOOPS,
            "sample_hz": SAMPLE_HZ,
            "detector_confidence_min": DETECTOR_CONFIDENCE_MIN,
            "detector_iou_min": DETECTOR_IOU_MIN,
            "reid_threshold": REID_THRESHOLD,
            "reid_margin": REID_MARGIN,
            "gating_denominator": CLASS_PAIRED_VISIBLE,
            "gating_recall_min": GATING_RECALL_MIN,
            "missing_pair_rate_max": MISSING_PAIR_RATE_MAX,
            "unprojectable_rate_max": UNPROJECTABLE_RATE_MAX,
            "distractor_sample_min": DISTRACTOR_SAMPLE_MIN,
            "gimbal_driver": GIMBAL_DRIVER,
        },
        "accounting": {
            "tick_count": tick_count,
            "counts": counts,
            "strict_denominator": strict,
            "conservative_denominator": conservative,
            "missing_pair_rate": missing_rate,
            "unprojectable_rate": unprojectable_rate,
        },
        "recall": {
            "hits": hits,
            "strict_denominator": strict,
            "strict_value": strict_recall,
            "conservative_denominator": conservative,
            "conservative_value": conservative_recall,
            "gated_on": "strict_value",
            "interpretation": RECALL_INTERPRETATION,
            "closed_loop_recall_claimed": False,
        },
        "embedding": {
            "target_cosine": _summary(target_scores),
            "distractor_cosine": _summary(distractor_scores),
            "target_threshold_passes": target_gate_passes,
            "separation_opportunities": separation_opportunities,
            "separation_margin_passes": separation_gate_passes,
            "feasibility_decision": "REQUIRES_REVIEW",
        },
        "descriptive_upper_quartile": {
            "slant_range_threshold_m": tail_threshold,
            "sample_count": len(tail_samples),
            "recall": (
                sum(1 for item in tail_samples if item["recall_hit"])
                / len(tail_samples)
                if tail_samples
                else None
            ),
            "gating": False,
        },
        "decision": decision,
        "decision_reason": reason,
        "samples": samples,
    }
    destination = result_path or directory / "scouting-result.json"
    _create_once(destination, _json_bytes(result))
    return result


# --- session lifecycle -------------------------------------------------------
#
# Create-once throughout: every document is written exactly once and any later
# write must reproduce identical bytes. The active-session marker at the
# runtime root is what Unity's CoverageEvaluator picks up, and its
# `session_root` must agree with the directory this module reads — the two
# used to be independent literals, which is the hazard Sonnet round 1 note 1
# identified. `SESSION_ROOT` below is the single source for the Python side and
# is asserted against the C# constant by a test.

SESSION_ROOT = "p1-scene-004-scouting"
ACTIVE_SESSION_NAME = "p1_scene_004_scouting_session.json"
SESSION_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,47}$")
INIT_WINDOW_S = (7.0, 8.0)
REFERENCE_SCHEMA = "p1-scene-004-scouting-reference/v1"
REFERENCE_PREVIEW_SCHEMA = "p1-scene-004-scouting-reference-preview/v1"
COMPLETION_SCHEMA = "p1-scene-004-scouting-completion/v1"


def session_document(session_id: str) -> dict[str, Any]:
    """The frozen session identity. Deterministic in `session_id` alone."""
    if not SESSION_ID_RE.fullmatch(session_id):
        raise ValueError("session id must be lowercase alphanumeric with dashes")
    geometry = _read_object(GEOMETRY_ARTIFACT)
    if geometry["status"] != "ENVELOPE_OK":
        raise ValueError("geometry artifact is not ENVELOPE_OK")
    return {
        "schema_version": SESSION_SCHEMA,
        "work_id": WORK_ID,
        "profile_id": PROFILE_ID,
        "session_id": session_id,
        "scenario_id": SCENARIO_ID,
        "non_measurement": True,
        "gimbal_driver": GIMBAL_DRIVER,
        "scenario_config_sha256": sha256_file(SCENARIO_CONFIG),
        "geometry_sha256": sha256_file(GEOMETRY_ARTIFACT),
        "loop_period_s": float(geometry["geometry"]["loop_period_s"]),
        "sample_hz": SAMPLE_HZ,
        "minimum_loops": MINIMUM_LOOPS,
        "detector_confidence_min": DETECTOR_CONFIDENCE_MIN,
        "detector_iou_min": DETECTOR_IOU_MIN,
        "gating_recall_min": GATING_RECALL_MIN,
    }


def _create_or_validate(path: Path, payload: bytes) -> None:
    """Create once; a repeat write is fine only if the bytes are identical."""
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"{path.name} differs from the frozen document")
        return
    _create_once(path, payload)


def _session_directory(runtime: Path, session_id: str) -> Path:
    if not SESSION_ID_RE.fullmatch(session_id):
        raise ValueError("session id must be lowercase alphanumeric with dashes")
    return Path(runtime) / SESSION_ROOT / session_id


def prepare_session(runtime: Path, session_id: str) -> dict[str, Any]:
    """Create the durable manifest and the active-session marker Unity reads."""
    runtime = Path(runtime)
    document = session_document(session_id)
    payload = _json_bytes(document)
    active = runtime / ACTIVE_SESSION_NAME
    if active.exists() and _read_object(active) != document:
        raise ValueError(
            "a different scout-3 session is already active; refusing to "
            "replace it"
        )
    directory = _session_directory(runtime, session_id)
    (directory / "truth").mkdir(parents=True, exist_ok=True)
    _create_or_validate(directory / "manifest.json", payload)
    _create_or_validate(active, payload)
    return document


def load_session(runtime: Path, session_id: str) -> tuple[dict[str, Any], Path]:
    directory = _session_directory(Path(runtime), session_id)
    manifest = _read_object(directory / "manifest.json")
    expected = session_document(session_id)
    if manifest != expected:
        raise ValueError("scout-3 manifest differs from the frozen contract")
    return manifest, directory


def preview_reference(runtime: Path, session_id: str) -> dict[str, Any]:
    """Freeze the first capture frame in the accepted [7,8) s init window."""
    runtime = Path(runtime)
    session, directory = load_session(runtime, session_id)
    candidates = [
        record
        for record in _frames(runtime)
        if INIT_WINDOW_S[0] <= record["simulation_time_s"] < INIT_WINDOW_S[1]
        and record["image_path"].is_file()
    ]
    if not candidates:
        raise ValueError("no complete scout-3 frame exists in [7,8) s")
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
    }
    _create_once(directory / "reference-preview.json", _json_bytes(document))
    return document


def bind_reference(
    runtime: Path,
    session_id: str,
    box_xywh_norm: Sequence[float],
) -> dict[str, Any]:
    """Bind the user-confirmed anchor box to the frozen preview frame."""
    runtime = Path(runtime)
    session, directory = load_session(runtime, session_id)
    preview = _read_object(directory / "reference-preview.json")
    if preview.get("schema_version") != REFERENCE_PREVIEW_SCHEMA:
        raise ValueError("reference preview is missing or invalid")
    image_path = directory / "reference-preview.jpg"
    if sha256_file(image_path) != preview["image_sha256"]:
        raise ValueError("reference preview image changed after the preview")
    box = normalize_box(box_xywh_norm)
    document = {
        "schema_version": REFERENCE_SCHEMA,
        "work_id": WORK_ID,
        "session_id": session["session_id"],
        "scenario_id": SCENARIO_ID,
        "frame_id": preview["frame_id"],
        "simulation_time_s": preview["simulation_time_s"],
        "box_xywh_norm": list(box),
        "image_sha256": preview["image_sha256"],
        "metadata_sha256": preview["metadata_sha256"],
    }
    _create_once(directory / "reference.json", _json_bytes(document))
    return document


def close_session(runtime: Path, session_id: str) -> dict[str, Any]:
    """Retire the active marker once a result exists; the manifest stays."""
    runtime = Path(runtime)
    session, directory = load_session(runtime, session_id)
    result_path = directory / "scouting-result.json"
    if not result_path.is_file():
        raise ValueError("cannot close a scout-3 session without a result")
    result = _read_object(result_path)
    document = {
        "schema_version": COMPLETION_SCHEMA,
        "work_id": WORK_ID,
        "session_id": session["session_id"],
        "result_sha256": sha256_file(result_path),
        "decision": result["decision"],
        "decision_reason": result["decision_reason"],
    }
    _create_once(directory / "completion.json", _json_bytes(document))
    active = runtime / ACTIVE_SESSION_NAME
    if active.exists():
        if _read_object(active) != session:
            raise ValueError("active marker does not match this session")
        active.unlink()
    return document


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", default=str(PROJECT_ROOT / "runtime"))
    parser.add_argument("--session-id", required=True)
    parser.add_argument(
        "command",
        choices=("prepare", "preview", "bind", "analyze", "close"),
    )
    parser.add_argument(
        "--box",
        nargs=4,
        type=float,
        help="reference box as normalised x y width height (bind only)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    arguments = build_argument_parser().parse_args(argv)
    runtime = Path(arguments.runtime)
    if arguments.command == "prepare":
        print(json.dumps(prepare_session(runtime, arguments.session_id)))
        return
    if arguments.command == "preview":
        print(json.dumps(preview_reference(runtime, arguments.session_id)))
        return
    if arguments.command == "bind":
        if arguments.box is None:
            raise SystemExit("bind requires --box x y width height")
        print(
            json.dumps(
                bind_reference(runtime, arguments.session_id, arguments.box)
            )
        )
        return
    if arguments.command == "close":
        print(json.dumps(close_session(runtime, arguments.session_id)))
        return
    result = analyze_session(runtime, session_id=arguments.session_id)
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "reason": result["decision_reason"],
                "strict_recall": result["recall"]["strict_value"],
                "accounting": result["accounting"]["counts"],
            }
        )
    )


if __name__ == "__main__":
    main()
