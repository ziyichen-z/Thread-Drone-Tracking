import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from controller.reanchor_models import ProposalBatch
from tools.run_detector_scouting import (
    GIMBAL_DRIVER,
    REFERENCE_SCHEMA,
    SCENARIO_ID,
    TRUTH_SCHEMA,
)
from tools.run_scene004_gate0_probe import (
    NEAR_SLANT_MAX_M,
    NEAR_SLANT_MIN_M,
    PROBE_SCHEMA,
    SESSION_ID,
    SOURCE_WORK_ID,
    _percentiles,
    _resolve_capture_root,
    run_probe,
)
from tools.run_track_experiment import PROJECT_ROOT

MARKER_STEP = 20
REFERENCE_FRAME_ID = 5
REFERENCE_BOX = [0.4, 0.4, 0.1, 0.15]


class StubProposer:
    """Proposes the exact truth box on the frames listed in ``hit_frames``."""

    def __init__(self, hit_boxes):
        self.hit_boxes = hit_boxes
        self.initialized_with = None
        self.seen = []

    def initialize(self, image, box_norm):
        self.initialized_with = tuple(box_norm)

    def propose(self, image):
        # JPEG round-trip is lossy, so frames are marked in widely spaced steps.
        index = int(round(float(image[0, 0, 0]) / MARKER_STEP))
        self.seen.append(index)
        box = self.hit_boxes.get(index)
        if box is None:
            return ProposalBatch((), (), 1.0)
        return ProposalBatch((tuple(box),), (0.9,), 1.0)


class StubEmbedder:
    def __init__(self, scores=None):
        self.scores = scores or {}

    def embed(self, image, box_norm):
        return (float(box_norm[0]), float(box_norm[1]))

    @staticmethod
    def cosine(left, right):
        return float(abs(right[0] - left[0]) < 1e-9) * 0.9 + 0.05


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1) + "\n")


def _build_capture(root: Path, frames):
    """frames: list of (frame_id, time_s, slant_m, visible, box, distractor_box)."""
    directory = root / "p1-detect-scouting" / SESSION_ID
    (root / "frames").mkdir(parents=True, exist_ok=True)
    (directory / "truth").mkdir(parents=True, exist_ok=True)
    _write_json(directory / "manifest.json", {"session_id": SESSION_ID})

    for frame_id, time_s, slant_m, visible, box, distractor_box in frames:
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        image[:, :, 0] = frame_id * MARKER_STEP
        cv2.imwrite(str(root / "frames" / f"frame_{frame_id:010d}.jpg"), image)
        _write_json(
            root / "frames" / f"frame_{frame_id:010d}.json",
            {
                "schema_version": "tethered-sensor-frame/v1",
                "scenario_id": SCENARIO_ID,
                "frame_id": frame_id,
                "simulation_time_s": time_s,
            },
        )
        truth = {
            "schema_version": TRUTH_SCHEMA,
            "work_id": SOURCE_WORK_ID,
            "session_id": SESSION_ID,
            "scenario_id": SCENARIO_ID,
            "gimbal_driver": GIMBAL_DRIVER,
            "frame_id": frame_id,
            "simulation_time_s": time_s,
            "target_visible": visible,
            "target_slant_range_m": slant_m,
            "distractors": (
                [{"distractor_id": "stub", "bbox_xywh_norm": distractor_box}]
                if distractor_box
                else []
            ),
        }
        if box is not None:
            truth["target_bbox_xywh_norm"] = {
                "x": box[0],
                "y": box[1],
                "width": box[2],
                "height": box[3],
            }
        _write_json(directory / "truth" / f"frame_{frame_id:010d}.json", truth)

    reference_image = np.zeros((480, 640, 3), dtype=np.uint8)
    reference_image[:, :, 0] = REFERENCE_FRAME_ID * MARKER_STEP
    cv2.imwrite(str(directory / "reference-preview.jpg"), reference_image)
    metadata_path = root / "frames" / f"frame_{REFERENCE_FRAME_ID:010d}.json"
    _write_json(
        directory / "reference.json",
        {
            "schema_version": REFERENCE_SCHEMA,
            "session_id": SESSION_ID,
            "frame_id": REFERENCE_FRAME_ID,
            "simulation_time_s": 5.0,
            "box_xywh_norm": REFERENCE_BOX,
            "image_sha256": hashlib.sha256(
                (directory / "reference-preview.jpg").read_bytes()
            ).hexdigest(),
            "metadata_sha256": hashlib.sha256(
                metadata_path.read_bytes()
            ).hexdigest(),
        },
    )
    return directory


def _default_frames():
    box = [0.4, 0.4, 0.1, 0.15]
    distractor = [0.7, 0.2, 0.1, 0.1]
    return [
        # in band, paired, visible
        (4, 4.0, 26.0, True, box, distractor),
        (5, 5.0, 27.0, True, box, distractor),  # reference frame
        (6, 6.0, 28.0, True, box, distractor),
        (7, 7.0, 29.0, True, box, distractor),
        (8, 8.0, 30.0, True, box, distractor),
        # out of band on both sides
        (9, 9.0, NEAR_SLANT_MIN_M - 0.5, True, box, distractor),
        (10, 10.0, NEAR_SLANT_MAX_M + 0.5, True, box, distractor),
        # in band but not visible
        (11, 11.0, 27.5, False, box, distractor),
    ]


class Scene004Gate0ProbeTests(unittest.TestCase):
    def test_live_runtime_root_is_refused(self):
        with self.assertRaises(ValueError) as context:
            _resolve_capture_root(str(PROJECT_ROOT / "runtime"))
        self.assertIn("sandbox copy", str(context.exception))

        with self.assertRaises(ValueError):
            _resolve_capture_root(str(PROJECT_ROOT / "runtime" / "frames"))

    def test_band_and_visibility_select_the_denominator(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_capture(root, _default_frames())
            result = run_probe(
                root,
                proposer=StubProposer({}),
                embedder=StubEmbedder(),
            )
        # Only the five in-band, visible, paired frames count.
        self.assertEqual(result["recall"]["denominator"], 5)
        self.assertEqual(result["recall"]["hits"], 0)
        self.assertEqual(result["decision"], "PROBE_MODEL_SELECTION_BLOCK")
        self.assertEqual(result["schema_version"], PROBE_SCHEMA)
        self.assertFalse(result["closed_loop_recall_claimed"])

    def test_decision_bands_follow_the_frozen_read(self):
        box = [0.4, 0.4, 0.1, 0.15]
        cases = {
            0: "PROBE_MODEL_SELECTION_BLOCK",
            2: "PROBE_MODEL_SELECTION_BLOCK",
            3: "RETURN_TO_USER_BELOW_GATING_LINE",
            4: "PROCEED_TO_IMPLEMENTATION",
            5: "PROCEED_TO_IMPLEMENTATION",
        }
        for hit_count, expected in cases.items():
            with self.subTest(hits=hit_count):
                hit_boxes = {
                    frame_id: box for frame_id in (4, 5, 6, 7, 8)[:hit_count]
                }
                with tempfile.TemporaryDirectory() as raw:
                    root = Path(raw)
                    _build_capture(root, _default_frames())
                    result = run_probe(
                        root,
                        proposer=StubProposer(hit_boxes),
                        embedder=StubEmbedder(),
                    )
                self.assertEqual(result["recall"]["hits"], hit_count)
                self.assertEqual(result["decision"], expected)

    def test_reference_frame_and_neighbours_leave_cosine_statistics(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_capture(root, _default_frames())
            result = run_probe(
                root,
                proposer=StubProposer({}),
                embedder=StubEmbedder(),
            )
        # Frames 4, 5 and 6 surround the reference frame and are excluded.
        self.assertEqual(result["embedding"]["excluded_reference_frames"], 3)
        self.assertEqual(result["embedding"]["target_cosine"]["count"], 2)
        self.assertEqual(result["embedding"]["distractor_cosine"]["count"], 2)
        self.assertEqual(result["embedding"]["feasibility_decision"], "REQUIRES_REVIEW")
        excluded = [
            sample["frame_id"]
            for sample in result["samples"]
            if sample["excluded_from_cosine_statistics"]
        ]
        self.assertEqual(excluded, [4, 5, 6])

    def test_pinned_model_identity_is_recorded_unchanged(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_capture(root, _default_frames())
            result = run_probe(
                root,
                proposer=StubProposer({}),
                embedder=StubEmbedder(),
            )
        identity = result["model_identity"]
        self.assertEqual(identity["minimum_crop_side_px"], 2)
        self.assertEqual(len(identity["detector_weights_sha256"]), 64)
        self.assertEqual(len(identity["reanchor_config_sha256"]), 64)

    def test_missing_truth_sidecar_is_not_a_probe_sample(self):
        frames = _default_frames()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            directory = _build_capture(root, frames)
            (directory / "truth" / "frame_0000000007.json").unlink()
            result = run_probe(
                root,
                proposer=StubProposer({}),
                embedder=StubEmbedder(),
            )
        self.assertEqual(result["recall"]["denominator"], 4)
        self.assertEqual(result["recall"]["unpaired_in_band"], 0)

    def test_percentiles_are_index_stable(self):
        self.assertEqual(_percentiles([])["count"], 0)
        summary = _percentiles([float(value) for value in range(1, 101)])
        self.assertEqual(summary["count"], 100)
        self.assertEqual(summary["min"], 1.0)
        self.assertEqual(summary["max"], 100.0)
        self.assertEqual(summary["p05"], 5.0)
        self.assertEqual(summary["p25"], 25.0)
        self.assertEqual(summary["median"], 50.5)


if __name__ == "__main__":
    unittest.main()
