"""P1-SCENE-004 Gate 0 — read-only near-field detectability probe.

The accepted proposal (revision 2, Codex round 2) makes this the first step
after acceptance and lets its result terminate the work item before any
scenario edit, profile creation or Unity capture happens.

What it does: replays the pinned YOLOE proposer and the pinned DINOv2
embedder over the *already frozen* `p1-detect-001-scout-1` capture, but on
the near-field samples (slant range in [25.0, 31.0] m) instead of the remote
tail that the DETECT-001 §8 gate measured. That band is the same geometry
SCENE-004 proposes, so the probe is the cheapest available prior on H1
(detector recall) and H2 (same-scale embedding separation).

Hard boundaries, all enforced below:

* `--capture-root` must not be the project `runtime/` tree — the probe only
  ever reads a sandbox byte-copy.
* Nothing is written into the capture root. The only output is the evidence
  document named by `--output`.
* No create-once identity is claimed or reused; the frozen scout-1 result,
  supersession and completion documents are never opened for writing.
* The pinned model config `config/detector-reanchor.models.json` is read and
  hash-recorded, never modified (BC5).

Pre-registered read, frozen before the first execution (BC4b):

* recall < 0.5  -> `PROBE_MODEL_SELECTION_BLOCK` (YOLOE unusable on this
  synthetic vehicle class; return to the user, do not implement)
* 0.5 <= recall < 0.7 -> `RETURN_TO_USER_BELOW_GATING_LINE` (the best
  available prior does not reach scout-3's own gating line, so the
  implementation batch and the Unity capture do not start on it)
* recall >= 0.7 -> `PROCEED_TO_IMPLEMENTATION`

The headline denominator is every near-field paired visible frame, which is
what the proposal names as the probe data set. A 2 Hz tick subset matching
the §8 sampling discipline is reported alongside as a consistency check and
is never the gating number. Cosine statistics exclude the frozen reference
frame and its immediate neighbours (BC4a), because the reference crop is
itself inside the probe band and would self-compare at ~1.0.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
from pathlib import Path
import statistics
from typing import Any, Mapping, Sequence

from controller.reanchor import load_reanchor_config
from controller.reanchor_models import DinoV2Embedder, YoloeProposer
from tools.run_detector_scouting import (
    DETECTOR_CONFIDENCE_MIN,
    DETECTOR_IOU_MIN,
    GIMBAL_DRIVER,
    REANCHOR_CONFIG,
    REFERENCE_SCHEMA,
    REID_MARGIN,
    REID_THRESHOLD,
    SAMPLE_HZ,
    SCENARIO_ID,
    TRUTH_SCHEMA,
    _cosine_or_none,
    _read_image,
    _read_object,
    _summary,
    intersection_over_union,
    normalize_box,
    sha256_file,
)
from tools.run_track_experiment import PROJECT_ROOT

WORK_ID = "P1-SCENE-004"
PROBE_SCHEMA = "p1-scene-004-gate0-probe/v1"
SESSION_ID = "p1-detect-001-scout-1"
SOURCE_WORK_ID = "P1-DETECT-001"

# Frozen probe band and read. Do not retune after seeing a result.
NEAR_SLANT_MIN_M = 25.0
NEAR_SLANT_MAX_M = 31.0
PROCEED_RECALL_MIN = 0.7
SELECTION_BLOCK_RECALL_MAX = 0.5
REFERENCE_EXCLUSION_RADIUS_FRAMES = 1

PROTECTED_ROOT = (PROJECT_ROOT / "runtime").resolve()


def _resolve_capture_root(raw: str) -> Path:
    root = Path(raw).resolve()
    if not root.is_dir():
        raise ValueError(f"capture root {root} does not exist")
    if root == PROTECTED_ROOT or PROTECTED_ROOT in root.parents:
        raise ValueError(
            "Gate 0 refuses to read the live runtime tree; pass a sandbox copy"
        )
    return root


def _frames(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((root / "frames").glob("frame_*.json")):
        value = _read_object(path)
        if value.get("schema_version") != "tethered-sensor-frame/v1":
            raise ValueError(f"{path.name} is not a sensor frame")
        if value.get("scenario_id") != SCENARIO_ID:
            raise ValueError(f"{path.name} has the wrong scenario")
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


def _truth(path: Path, *, frame_id: int, simulation_time_s: float) -> dict[str, Any]:
    value = _read_object(path)
    if (
        value.get("schema_version") != TRUTH_SCHEMA
        or value.get("work_id") != SOURCE_WORK_ID
        or value.get("session_id") != SESSION_ID
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


def _percentiles(values: Sequence[float]) -> dict[str, Any]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return {"count": 0}

    def at(fraction: float) -> float:
        return ordered[int(fraction * (len(ordered) - 1))]

    return {
        "count": len(ordered),
        "min": ordered[0],
        "p05": at(0.05),
        "p25": at(0.25),
        "median": statistics.median(ordered),
        "max": ordered[-1],
    }


def run_probe(
    capture_root: Path,
    *,
    proposer: Any | None = None,
    embedder: Any | None = None,
) -> dict[str, Any]:
    directory = capture_root / "p1-detect-scouting" / SESSION_ID
    manifest = _read_object(directory / "manifest.json")
    if manifest.get("session_id") != SESSION_ID:
        raise ValueError("sandbox manifest is not the scout-1 session")

    reference = _read_object(directory / "reference.json")
    if (
        reference.get("schema_version") != REFERENCE_SCHEMA
        or reference.get("session_id") != SESSION_ID
    ):
        raise ValueError("invalid scouting reference")
    reference_frame_id = int(reference["frame_id"])
    reference_image_path = directory / "reference-preview.jpg"
    if sha256_file(reference_image_path) != reference.get("image_sha256"):
        raise ValueError("reference image hash mismatch inside the sandbox")
    reference_metadata_path = (
        capture_root / "frames" / f"frame_{reference_frame_id:010d}.json"
    )
    if sha256_file(reference_metadata_path) != reference.get("metadata_sha256"):
        raise ValueError("reference metadata hash mismatch inside the sandbox")
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

    records = _frames(capture_root)
    times = [float(record["simulation_time_s"]) for record in records]
    tick_interval = 1.0 / SAMPLE_HZ
    tick_frame_ids: set[int] = set()
    if records:
        tick = times[0]
        while tick <= times[-1]:
            position = bisect.bisect_left(times, tick)
            if position < len(records) and times[position] < tick + tick_interval:
                tick_frame_ids.add(int(records[position]["frame_id"]))
            tick += tick_interval

    samples: list[dict[str, Any]] = []
    target_scores: list[float] = []
    distractor_scores: list[float] = []
    box_widths: list[float] = []
    box_heights: list[float] = []
    minimum_sides: list[float] = []
    hits = 0
    denominator = 0
    tick_hits = 0
    tick_denominator = 0
    unpaired_in_band = 0
    target_gate_passes = 0
    separation_opportunities = 0
    separation_gate_passes = 0
    excluded_reference_frames = 0

    for record in records:
        frame_id = int(record["frame_id"])
        truth_path = directory / "truth" / f"frame_{frame_id:010d}.json"
        image_path = Path(record["image_path"])
        if not truth_path.is_file():
            continue
        truth = _truth(
            truth_path,
            frame_id=frame_id,
            simulation_time_s=float(record["simulation_time_s"]),
        )
        range_m = float(truth.get("target_slant_range_m", float("nan")))
        if (
            not bool(truth.get("target_visible"))
            or not math.isfinite(range_m)
            or range_m < NEAR_SLANT_MIN_M
            or range_m > NEAR_SLANT_MAX_M
        ):
            continue
        target_box = truth.get("target_bbox_xywh_norm")
        if target_box is None or not image_path.is_file():
            unpaired_in_band += 1
            continue

        denominator += 1
        in_tick_subset = frame_id in tick_frame_ids
        if in_tick_subset:
            tick_denominator += 1

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
            if in_tick_subset:
                tick_hits += 1

        normalized_target = normalize_box(target_box)
        width_px = normalized_target[2] * 640.0
        height_px = normalized_target[3] * 480.0
        box_widths.append(width_px)
        box_heights.append(height_px)
        minimum_sides.append(min(width_px, height_px))

        excluded = (
            abs(frame_id - reference_frame_id) <= REFERENCE_EXCLUSION_RADIUS_FRAMES
        )
        if excluded:
            excluded_reference_frames += 1

        target_cosine, target_error = _cosine_or_none(
            embedder, reference_embedding, image, target_box
        )
        frame_distractor_scores: list[float] = []
        per_distractor: list[dict[str, Any]] = []
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
            if score is not None and not excluded:
                distractor_scores.append(score)
                frame_distractor_scores.append(score)
            per_distractor.append(
                {
                    "distractor_id": distractor.get("distractor_id"),
                    "cosine": score,
                    "error": error,
                }
            )

        if target_cosine is not None and not excluded:
            target_scores.append(target_cosine)
            if target_cosine >= REID_THRESHOLD:
                target_gate_passes += 1
            if frame_distractor_scores:
                separation_opportunities += 1
                if (
                    target_cosine >= REID_THRESHOLD
                    and target_cosine - max(frame_distractor_scores) >= REID_MARGIN
                ):
                    separation_gate_passes += 1

        samples.append(
            {
                "frame_id": frame_id,
                "simulation_time_s": record["simulation_time_s"],
                "target_slant_range_m": range_m,
                "target_box_width_px": width_px,
                "target_box_height_px": height_px,
                "proposal_count": len(batch.boxes_norm),
                "maximum_target_iou": maximum_iou,
                "recall_hit": hit,
                "in_tick_subset": in_tick_subset,
                "excluded_from_cosine_statistics": excluded,
                "target_cosine": target_cosine,
                "target_embedding_error": target_error,
                "distractors": per_distractor,
            }
        )

    if denominator == 0:
        raise ValueError("probe band contains no paired visible samples")

    recall = hits / denominator
    if recall < SELECTION_BLOCK_RECALL_MAX:
        decision = "PROBE_MODEL_SELECTION_BLOCK"
    elif recall < PROCEED_RECALL_MIN:
        decision = "RETURN_TO_USER_BELOW_GATING_LINE"
    else:
        decision = "PROCEED_TO_IMPLEMENTATION"

    return {
        "schema_version": PROBE_SCHEMA,
        "work_id": WORK_ID,
        "interpretation": "ORACLE_POINTED_DETECTABILITY_UPPER_BOUND",
        "closed_loop_recall_claimed": False,
        "source_capture": {
            "work_id": SOURCE_WORK_ID,
            "session_id": SESSION_ID,
            "scenario_id": SCENARIO_ID,
            "gimbal_driver": GIMBAL_DRIVER,
            "read_only_sandbox_copy": True,
            "reference_frame_id": reference_frame_id,
            "reference_simulation_time_s": reference["simulation_time_s"],
            "reference_box_xywh_norm": list(reference_box),
            "reference_image_sha256": reference["image_sha256"],
            "reference_metadata_sha256": reference["metadata_sha256"],
        },
        "model_identity": {
            "reanchor_config_path": str(REANCHOR_CONFIG),
            "reanchor_config_sha256": sha256_file(REANCHOR_CONFIG),
            "detector_weights_sha256": frozen_config.detector["sha256"],
            "appearance_weights_sha256": frozen_config.appearance["weights"]["sha256"],
            "appearance_source_sha256": frozen_config.appearance["source"][
                "archive_sha256"
            ],
            "minimum_crop_side_px": int(
                frozen_config.appearance["preprocessing"]["minimum_crop_side_px"]
            ),
        },
        "frozen_probe_protocol": {
            "near_slant_range_min_m": NEAR_SLANT_MIN_M,
            "near_slant_range_max_m": NEAR_SLANT_MAX_M,
            "detector_confidence_min": DETECTOR_CONFIDENCE_MIN,
            "detector_iou_min": DETECTOR_IOU_MIN,
            "reid_threshold": REID_THRESHOLD,
            "reid_margin": REID_MARGIN,
            "headline_denominator": "ALL_NEAR_FIELD_PAIRED_VISIBLE_FRAMES",
            "reference_exclusion_radius_frames": REFERENCE_EXCLUSION_RADIUS_FRAMES,
            "proceed_recall_min": PROCEED_RECALL_MIN,
            "selection_block_recall_max": SELECTION_BLOCK_RECALL_MAX,
        },
        "recall": {
            "hits": hits,
            "denominator": denominator,
            "value": recall,
            "unpaired_in_band": unpaired_in_band,
            "tick_subset_hits": tick_hits,
            "tick_subset_denominator": tick_denominator,
            "tick_subset_value": (
                tick_hits / tick_denominator if tick_denominator else None
            ),
        },
        "target_box_pixels": {
            "width": _percentiles(box_widths),
            "height": _percentiles(box_heights),
            "minimum_side": _percentiles(minimum_sides),
        },
        "embedding": {
            "excluded_reference_frames": excluded_reference_frames,
            "target_cosine": _summary(target_scores),
            "distractor_cosine": _summary(distractor_scores),
            "target_threshold_passes": target_gate_passes,
            "separation_opportunities": separation_opportunities,
            "separation_margin_passes": separation_gate_passes,
            "feasibility_decision": "REQUIRES_REVIEW",
        },
        "decision": decision,
        "samples": samples,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture-root",
        required=True,
        help="sandbox byte-copy of the capture tree (never the live runtime/)",
    )
    parser.add_argument(
        "--output", required=True, help="path of the probe evidence document"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    arguments = build_argument_parser().parse_args(argv)
    capture_root = _resolve_capture_root(arguments.capture_root)
    result = run_probe(capture_root)
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(
        f"decision={result['decision']} "
        f"recall={result['recall']['value']:.6f} "
        f"({result['recall']['hits']}/{result['recall']['denominator']})"
    )


if __name__ == "__main__":
    main()
