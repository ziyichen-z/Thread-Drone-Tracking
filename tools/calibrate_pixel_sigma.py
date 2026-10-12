#!/usr/bin/env python3
"""P1-M3-BODY-001 batch 1a-alpha tool 3: offline sigma_px recalibration.

Revision 0 claimed the archive already held image/truth *box* pairs. It does
not: the scout-4 session directory has completion, manifest, reference and
truth only - no run log, so no tracker box was ever archived. sigma_px
therefore cannot be read out of the archive and has to be **re-measured** by
replaying the frozen NanoTrack-v2 over the archived frames and joining its
boxes to the archived truth by ``frame_id``.

Everything the aggregation does is pre-registered here, in the code and in
the artifact schema, **before** the tool is run (BC-BODY1-7):

P1. Initialisation: the tracker is initialised once, on the first frame that
    has a ``VALID`` truth box, using that truth box. This is an offline
    calibration activity and is allowed to read archived truth; its only
    path into the online side is the frozen scalar in
    ``config/p1-m3-body-001.json``.
P2. Per-frame residual: the signed pixel offset between the centre of the
    tracker box and the centre of the truth box, in image pixels, plus its
    Euclidean magnitude. Frames whose truth box is not ``VALID``, or where
    the tracker reports a loss, contribute no residual and are counted
    separately.
P3. Aggregation: sigma_px is the **root mean square** of the per-axis signed
    residuals pooled over both axes - the isotropic standard deviation the
    measurement Jacobian in the proposal section 3.4 expects. Median, p95 and
    max magnitudes are reported alongside as description.
P4. Drift and outliers: nothing is trimmed or rejected. A tracker that drifts
    onto another object inflates sigma_px, and inflating a conservative prior
    is the safe direction; a trimmed estimate would understate it. Frames
    after a reported loss keep contributing while the tracker still returns a
    box, and the loss count is published so a reviewer can see how much of
    the record is post-loss.
P5. The result is labelled a **conservative initial value**, not a
    measurement of the M3' carrier, and both extrapolation risks are recorded
    verbatim in the artifact (see EXTRAPOLATION_RISKS).

CLI:
    .venv-track/bin/python tools/calibrate_pixel_sigma.py [--limit N]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

ARTIFACT_SCHEMA = "p1-m3-body-001-sigma-px/v1"
WORK_ID = "P1-M3-BODY-001"

FRAME_DIR = (
    PROJECT_ROOT
    / "runtime"
    / "test-results"
    / "p1-scene-004-scout-4-closed-exchange"
    / "frames"
)
TRUTH_DIR = (
    PROJECT_ROOT
    / "runtime"
    / "p1-scene-004-scouting"
    / "p1-scene-004-scout-4"
    / "truth"
)
SESSION_MANIFEST = (
    PROJECT_ROOT
    / "runtime"
    / "p1-scene-004-scouting"
    / "p1-scene-004-scout-4"
    / "manifest.json"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "docs" / "evidence" / "P1-M3-BODY-001-sigma-px.json"
)

# BC-BODY1-7: both risks are recorded verbatim, not paraphrased.
EXTRAPOLATION_RISKS = (
    "the archive's `manifest.gimbal_driver = truth_directed_scouting`, i.e. "
    "these frames come from a truth-directed scouting sweep, not from a "
    "tracking loop",
    "SCENE-004 is a benign near-nadir geometry with a narrow slant-range "
    "band, while this batch's carrier is the main circuit at up to about "
    "70 degrees off-nadir; the calibration is extrapolated across that gap",
)


class CalibrationFailure(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CalibrationFailure(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _center_px(
    box: Mapping[str, Any],
    width: int,
    height: int,
) -> tuple[float, float]:
    return (
        (float(box["x"]) + float(box["width"]) / 2.0) * width,
        (float(box["y"]) + float(box["height"]) / 2.0) * height,
    )


def frame_ids(frame_dir: Path) -> list[int]:
    return sorted(
        int(path.stem.split("_")[1])
        for path in frame_dir.glob("frame_*.jpg")
    )


def calibrate(
    frame_dir: Path = FRAME_DIR,
    truth_dir: Path = TRUTH_DIR,
    limit: int | None = None,
) -> dict[str, Any]:
    import cv2

    from controller.trackers import NanoTrackV2Tracker

    _require(frame_dir.is_dir(), f"frame directory is missing: {frame_dir}")
    _require(truth_dir.is_dir(), f"truth directory is missing: {truth_dir}")
    manifest = _load(SESSION_MANIFEST)
    gimbal_driver = str(manifest.get("gimbal_driver", ""))
    _require(
        gimbal_driver == "truth_directed_scouting",
        "the archived session is not the truth-directed scouting sweep the "
        f"extrapolation risks describe (gimbal_driver={gimbal_driver!r})",
    )

    identifiers = frame_ids(frame_dir)
    if limit is not None:
        identifiers = identifiers[:limit]
    _require(bool(identifiers), "no archived frames found")

    tracker = NanoTrackV2Tracker()
    initialized_frame: int | None = None
    residual_x: list[float] = []
    residual_y: list[float] = []
    magnitudes: list[float] = []
    truth_missing = 0
    tracker_lost = 0
    first_loss_frame: int | None = None
    evaluated = 0

    for frame_id in identifiers:
        truth_path = truth_dir / f"frame_{frame_id:010d}.json"
        image_path = frame_dir / f"frame_{frame_id:010d}.jpg"
        if not truth_path.exists() or not image_path.exists():
            truth_missing += 1
            continue
        truth = _load(truth_path)
        box = truth.get("target_bbox_xywh_norm")
        if truth.get("target_box_status") != "VALID" or box is None:
            truth_missing += 1
            continue
        image = cv2.imread(str(image_path))
        _require(image is not None, f"unreadable frame image: {image_path}")
        height, width = image.shape[0], image.shape[1]

        if initialized_frame is None:
            # P1: one initialisation, on the first VALID truth box.
            _require(
                tracker.init(image, (box["x"], box["y"], box["width"], box["height"])),
                f"tracker initialisation failed on frame {frame_id}",
            )
            initialized_frame = frame_id
            continue

        result = tracker.update(image)
        evaluated += 1
        if not result.ok or result.box_norm is None:
            tracker_lost += 1
            if first_loss_frame is None:
                first_loss_frame = frame_id
            continue
        predicted = result.box_norm
        predicted_center = _center_px(
            {
                "x": predicted[0],
                "y": predicted[1],
                "width": predicted[2],
                "height": predicted[3],
            },
            width,
            height,
        )
        truth_center = _center_px(box, width, height)
        offset_x = predicted_center[0] - truth_center[0]
        offset_y = predicted_center[1] - truth_center[1]
        residual_x.append(offset_x)
        residual_y.append(offset_y)
        magnitudes.append(math.hypot(offset_x, offset_y))

    _require(
        initialized_frame is not None,
        "no frame carried a VALID truth box to initialise on",
    )
    _require(bool(magnitudes), "no residual could be measured")

    # P3: pooled per-axis RMS.
    pooled = residual_x + residual_y
    sigma_px = math.sqrt(sum(value * value for value in pooled) / len(pooled))
    ordered = sorted(magnitudes)

    def at(fraction: float) -> float:
        return ordered[int(fraction * (len(ordered) - 1))]

    return {
        "schema_version": ARTIFACT_SCHEMA,
        "work_id": WORK_ID,
        "label": "conservative initial value, not a carrier measurement",
        "source": {
            "frame_dir": str(frame_dir.relative_to(PROJECT_ROOT)),
            "truth_dir": str(truth_dir.relative_to(PROJECT_ROOT)),
            "session_manifest_sha256": sha256_file(SESSION_MANIFEST),
            "gimbal_driver": gimbal_driver,
            "tracker": tracker.manifest_identity(),
        },
        "pre_registered_policy": {
            "P1_initialisation": "first VALID truth box, one init, offline only",
            "P2_residual": "signed box-centre pixel offset, both axes",
            "P3_aggregation": "sigma_px = RMS of per-axis signed residuals",
            "P4_outliers": "nothing trimmed; drift inflates the conservative prior",
            "P5_label": "conservative initial value; both risks recorded",
        },
        "counts": {
            "frames_listed": len(identifiers),
            "initialised_on_frame": initialized_frame,
            "frames_evaluated": evaluated,
            "residual_samples": len(magnitudes),
            "truth_unavailable": truth_missing,
            "tracker_lost": tracker_lost,
            "first_loss_frame": first_loss_frame,
        },
        "sigma_px": sigma_px,
        "residual_magnitude_px": {
            "median": statistics.median(ordered),
            "p95": at(0.95),
            "max": ordered[-1],
        },
        "residual_axis_px": {
            "mean_x": statistics.fmean(residual_x),
            "mean_y": statistics.fmean(residual_y),
            "stdev_x": statistics.pstdev(residual_x),
            "stdev_y": statistics.pstdev(residual_y),
        },
        "extrapolation_risks": list(EXTRAPOLATION_RISKS),
        "batch_1c_obligation": (
            "batch 1c must report the measured residual distribution on the "
            "M3' carrier against this value; re-standardising Q or R requires "
            "returning to Acceptance (BC-BODY1-7)"
        ),
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="evaluate only the first N archived frames (smoke runs)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(argv)
    try:
        artifact = calibrate(limit=arguments.limit)
    except CalibrationFailure as failure:
        print(f"sigma_px calibration FAILED: {failure}")
        return 1
    Path(arguments.output).write_text(
        json.dumps(artifact, indent=1, sort_keys=True) + "\n"
    )
    counts = artifact["counts"]
    print(
        f"sigma_px={artifact['sigma_px']:.6f} px "
        f"(residual median {artifact['residual_magnitude_px']['median']:.4f}, "
        f"p95 {artifact['residual_magnitude_px']['p95']:.4f}, "
        f"max {artifact['residual_magnitude_px']['max']:.4f}) | "
        f"init frame {counts['initialised_on_frame']}, "
        f"{counts['residual_samples']}/{counts['frames_evaluated']} residuals, "
        f"{counts['tracker_lost']} lost, "
        f"{counts['truth_unavailable']} truth unavailable"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
