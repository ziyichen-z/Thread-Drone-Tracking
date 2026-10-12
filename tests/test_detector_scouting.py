import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from controller.reanchor_models import ProposalBatch
from tools.run_detector_scouting import (
    A3_ANALYSIS_ID,
    GIMBAL_DRIVER,
    RECALL_INTERPRETATION,
    REANALYSIS_RESULT_SCHEMA,
    RESULT_SCHEMA,
    SCENARIO_ID,
    TRUTH_SCHEMA,
    analyze_session,
    bind_reference,
    close_session,
    intersection_over_union,
    normalize_box,
    prepare_session,
    preview_reference,
    reanalyze_a3_session,
    sha256_file,
    validate_scouting_config,
    _frame_metadata,
)


TARGET_BOX = (0.2, 0.2, 0.2, 0.2)
DISTRACTOR_BOX = (0.7, 0.2, 0.2, 0.2)
REAL_TRUTH_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "p1_detect_scouting_truth_frame_0000000312.json"
)
REAL_TRUTH_FIXTURE_SHA256 = (
    "a661652b8003af2784a6d134fc7b6fa35ebcb8bdcb3d30c0a80eb8a09fb027a1"
)


class FakeProposer:
    def __init__(self, *, hit=True):
        self.hit = hit
        self.initialized = None

    def initialize(self, image, box):
        self.initialized = tuple(box)

    def propose(self, image):
        box = TARGET_BOX if self.hit else (0.0, 0.0, 0.1, 0.1)
        return ProposalBatch((box,), (0.9,), 1.0)


class FakeEmbedder:
    def embed(self, image, box):
        x = float(box[0])
        vector = (1.0 - x, x)
        norm = math.sqrt(sum(value * value for value in vector))
        return tuple(value / norm for value in vector)

    @staticmethod
    def cosine(left, right):
        return sum(a * b for a, b in zip(left, right))


def write_frame(
    runtime: Path,
    session_id: str,
    frame_id: int,
    simulation_time_s: float,
    *,
    remote_visible: bool,
    target_box: tuple[float, float, float, float] | None = TARGET_BOX,
    write_image: bool = True,
    write_truth: bool = True,
    box_schema: str = "sequence",
) -> None:
    frames = runtime / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    stem = f"frame_{frame_id:010d}"
    metadata = {
        "schema_version": "tethered-sensor-frame/v1",
        "scenario_id": SCENARIO_ID,
        "frame_id": frame_id,
        "simulation_time_s": simulation_time_s,
        "capture_unix_s": 1_800_000_000.0 + simulation_time_s,
    }
    (frames / f"{stem}.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )
    if write_image:
        image = np.full((32, 48, 3), frame_id % 255, dtype=np.uint8)
        encoded, payload = cv2.imencode(".jpg", image)
        if not encoded:
            raise RuntimeError("test JPEG encode failed")
        (frames / f"{stem}.jpg").write_bytes(payload.tobytes())
    if write_truth:
        if box_schema not in {"sequence", "object"}:
            raise ValueError("unsupported test box schema")

        def encoded_box(box):
            if box is None:
                return None
            if box_schema == "object":
                return dict(zip(("x", "y", "width", "height"), box))
            return list(box)

        truth_directory = (
            runtime / "p1-detect-scouting" / session_id / "truth"
        )
        truth_directory.mkdir(parents=True, exist_ok=True)
        truth = {
            "schema_version": TRUTH_SCHEMA,
            "work_id": "P1-DETECT-001",
            "session_id": session_id,
            "scenario_id": SCENARIO_ID,
            "gimbal_driver": GIMBAL_DRIVER,
            "frame_id": frame_id,
            "simulation_time_s": simulation_time_s,
            "target_track_id": "target-0",
            "target_visible": remote_visible,
            "target_visible_sample_fraction": 1.0 if remote_visible else 0.0,
            "target_slant_range_m": 70.0 if remote_visible else 40.0,
            "target_bbox_xywh_norm": encoded_box(target_box),
            "distractors": [
                {
                    "distractor_id": "Environment/Vehicle_Taxi",
                    "bbox_xywh_norm": encoded_box(DISTRACTOR_BOX),
                }
            ],
        }
        (truth_directory / f"{stem}.json").write_text(
            json.dumps(truth),
            encoding="utf-8",
        )


def complete_capture(
    runtime: Path,
    session_id: str,
    *,
    missing_truth_tick: int | None = None,
    box_schema: str = "sequence",
) -> None:
    for tick in range(214):
        write_frame(
            runtime,
            session_id,
            tick,
            7.0 + tick * 0.5,
            remote_visible=tick == 0,
            write_truth=tick != missing_truth_tick,
            box_schema=box_schema,
        )


class DetectorScoutingTests(unittest.TestCase):
    def test_scouting_reader_accepts_historical_v1_and_validated_v3(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            write_frame(
                runtime,
                "reader",
                1,
                7.1,
                remote_visible=False,
                write_truth=False,
            )
            self.assertEqual(_frame_metadata(runtime)[0]["frame_id"], 1)
            path = runtime / "frames" / "frame_0000000001.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value.update(
                {
                    "schema_version": "tethered-sensor-frame/v3",
                    "capture_monotonic_s": 501.0,
                    "capture_monotonic_clock_id": "system-stopwatch/v1",
                }
            )
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(_frame_metadata(runtime)[0]["frame_id"], 1)
            value["capture_monotonic_clock_id"] = "wrong/v1"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid system monotonic"):
                _frame_metadata(runtime)

    def test_checked_in_scouting_config_only_changes_capture_identity_and_retention(
        self,
    ):
        validation = validate_scouting_config()
        self.assertAlmostEqual(validation["loop_duration_s"], 106.485281, places=5)
        self.assertEqual(len(validation["scenario_config_sha256"]), 64)

    def test_prepare_is_create_once_and_refuses_measurement_or_old_frames(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            (runtime / "rate_study_session.json").write_text("{}")
            with self.assertRaisesRegex(RuntimeError, "non-measurement"):
                prepare_session(runtime, "scout-a")
            (runtime / "rate_study_session.json").unlink()
            (runtime / "frames").mkdir()
            (runtime / "frames" / "keep").write_text("evidence")
            with self.assertRaisesRegex(RuntimeError, "not empty"):
                prepare_session(runtime, "scout-a")
            (runtime / "frames" / "keep").unlink()
            (runtime / "frames").rmdir()

            prepared = prepare_session(runtime, "scout-a")
            self.assertTrue(prepared["non_measurement"])
            self.assertEqual(prepared["gimbal_driver"], GIMBAL_DRIVER)
            self.assertEqual(prepared["sample_hz"], 2.0)
            self.assertEqual(prepared["remote_slant_range_min_m"], 65.0)
            with self.assertRaises(FileExistsError):
                prepare_session(runtime, "scout-b")

    def test_reference_preview_and_binding_are_hash_bound_and_create_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            prepare_session(runtime, "scout-reference")
            write_frame(
                runtime,
                "scout-reference",
                10,
                7.1,
                remote_visible=False,
            )
            preview = preview_reference(runtime)
            self.assertEqual(preview["frame_id"], 10)
            reference = bind_reference(runtime, TARGET_BOX)
            self.assertEqual(reference["box_xywh_norm"], list(TARGET_BOX))
            self.assertTrue(Path(reference["box_preview_path"]).is_file())
            with self.assertRaises(FileExistsError):
                preview_reference(runtime)

    def test_iou_matches_frozen_hit_rule_geometry(self):
        self.assertEqual(intersection_over_union(TARGET_BOX, TARGET_BOX), 1.0)
        self.assertEqual(
            intersection_over_union(TARGET_BOX, DISTRACTOR_BOX),
            0.0,
        )
        self.assertAlmostEqual(
            intersection_over_union(TARGET_BOX, (0.3, 0.2, 0.2, 0.2)),
            1.0 / 3.0,
        )

    def test_box_parser_accepts_only_exact_object_or_four_number_sequence(self):
        object_box = {
            "x": TARGET_BOX[0],
            "y": TARGET_BOX[1],
            "width": TARGET_BOX[2],
            "height": TARGET_BOX[3],
        }
        self.assertEqual(normalize_box(object_box), TARGET_BOX)
        self.assertEqual(normalize_box(list(TARGET_BOX)), TARGET_BOX)
        self.assertEqual(intersection_over_union(object_box, TARGET_BOX), 1.0)

        invalid_values = (
            {**object_box, "extra": 0.0},
            {"x": 0.2, "y": 0.2, "width": 0.2},
            {"x": "0.2", "y": 0.2, "width": 0.2, "height": 0.2},
            {"x": True, "y": 0.2, "width": 0.2, "height": 0.2},
            [0.2, 0.2, 0.2],
            "0.2,0.2,0.2,0.2",
        )
        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    normalize_box(value)

    def test_real_capture_truth_fixture_is_byte_exact_and_object_parses(self):
        payload = REAL_TRUTH_FIXTURE.read_bytes()
        self.assertEqual(
            hashlib.sha256(payload).hexdigest(),
            REAL_TRUTH_FIXTURE_SHA256,
        )
        truth = json.loads(payload)
        self.assertEqual(truth["frame_id"], 312)
        self.assertEqual(
            normalize_box(truth["target_bbox_xywh_norm"]),
            (
                0.4806014895439148,
                0.08261549472808838,
                0.04428505897521973,
                0.04453420639038086,
            ),
        )
        self.assertIsNone(truth["distractors"][0]["bbox_xywh_norm"])

    def test_analyze_accepts_unity_object_box_schema_for_iou_and_embedding(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            session_id = "scout-object-box"
            prepare_session(runtime, session_id)
            complete_capture(runtime, session_id, box_schema="object")
            preview_reference(runtime)
            bind_reference(runtime, TARGET_BOX)
            result = analyze_session(
                runtime,
                proposer=FakeProposer(hit=True),
                embedder=FakeEmbedder(),
            )

            self.assertEqual(result["recall"]["hits"], 1)
            self.assertEqual(result["embedding"]["target_cosine"]["count"], 1)
            self.assertEqual(
                result["embedding"]["distractor_cosine"]["count"],
                1,
            )

    def test_analyze_counts_missing_pair_as_miss_and_filters_near_frames(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            session_id = "scout-analysis"
            prepare_session(runtime, session_id)
            complete_capture(runtime, session_id, missing_truth_tick=1)
            preview_reference(runtime)
            bind_reference(runtime, TARGET_BOX)
            proposer = FakeProposer(hit=True)
            result = analyze_session(
                runtime,
                proposer=proposer,
                embedder=FakeEmbedder(),
            )

            self.assertEqual(result["schema_version"], RESULT_SCHEMA)
            self.assertEqual(proposer.initialized, TARGET_BOX)
            self.assertEqual(result["recall"]["hits"], 1)
            self.assertEqual(result["recall"]["denominator"], 2)
            self.assertEqual(result["recall"]["missing_pair_misses"], 1)
            self.assertEqual(result["recall"]["value"], 0.5)
            self.assertEqual(
                result["recall"]["interpretation"],
                RECALL_INTERPRETATION,
            )
            self.assertFalse(result["recall"]["closed_loop_recall_claimed"])
            self.assertEqual(
                result["frozen_protocol"]["gimbal_driver"],
                GIMBAL_DRIVER,
            )
            self.assertEqual(
                result["recall"]["decision"],
                "GO_CURRENT_GEOMETRY",
            )
            self.assertEqual(
                result["overall_decision"],
                "AWAITING_EMBEDDING_FEASIBILITY_REVIEW",
            )
            self.assertEqual(
                result["embedding"]["feasibility_decision"],
                "REQUIRES_REVIEW",
            )
            self.assertEqual(result["embedding"]["target_cosine"]["count"], 1)
            self.assertEqual(
                result["embedding"]["distractor_cosine"]["count"],
                1,
            )
            with self.assertRaises(FileExistsError):
                analyze_session(
                    runtime,
                    proposer=FakeProposer(hit=True),
                    embedder=FakeEmbedder(),
                )
            completion = close_session(runtime)
            self.assertEqual(
                completion["overall_decision"],
                "AWAITING_EMBEDDING_FEASIBILITY_REVIEW",
            )
            self.assertFalse(
                (runtime / "p1_detect_scouting_session.json").exists()
            )
            self.assertTrue(
                (
                    runtime
                    / "p1-detect-scouting"
                    / session_id
                    / "manifest.json"
                ).is_file()
            )

    def test_recall_below_half_returns_to_user_without_tuning(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            session_id = "scout-return"
            prepare_session(runtime, session_id)
            complete_capture(runtime, session_id)
            preview_reference(runtime)
            bind_reference(runtime, TARGET_BOX)
            result = analyze_session(
                runtime,
                proposer=FakeProposer(hit=False),
                embedder=FakeEmbedder(),
            )
            self.assertEqual(result["recall"]["value"], 0.0)
            self.assertEqual(
                result["overall_decision"],
                "RETURN_TO_USER_OPTION_B",
            )
            self.assertEqual(
                result["frozen_protocol"]["reid_threshold"],
                0.5,
            )
            self.assertEqual(
                result["frozen_protocol"]["reid_margin"],
                0.1,
            )

    def test_a3_reanalysis_preserves_original_and_closes_versioned_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            session_id = "scout-a3"
            prepare_session(runtime, session_id)
            complete_capture(runtime, session_id, box_schema="object")
            preview_reference(runtime)
            bind_reference(runtime, TARGET_BOX)
            analyze_session(
                runtime,
                proposer=FakeProposer(hit=False),
                embedder=FakeEmbedder(),
            )
            directory = runtime / "p1-detect-scouting" / session_id
            original_path = directory / "scouting-result.json"
            original_payload = original_path.read_bytes()
            original_sha256 = sha256_file(original_path)

            with self.assertRaisesRegex(
                ValueError,
                "hash does not match",
            ):
                reanalyze_a3_session(
                    runtime,
                    supersedes_result_sha256="0" * 64,
                    proposer=FakeProposer(hit=True),
                    embedder=FakeEmbedder(),
                )
            self.assertFalse(
                (directory / f"reanalysis-{A3_ANALYSIS_ID}.json").exists()
            )

            reanalysis = reanalyze_a3_session(
                runtime,
                supersedes_result_sha256=original_sha256,
                proposer=FakeProposer(hit=True),
                embedder=FakeEmbedder(),
            )
            self.assertEqual(
                reanalysis["result"]["schema_version"],
                REANALYSIS_RESULT_SCHEMA,
            )
            self.assertEqual(
                reanalysis["result"]["analysis_identity"]["analysis_id"],
                A3_ANALYSIS_ID,
            )
            self.assertEqual(
                reanalysis["supersession"]["superseded_result_sha256"],
                original_sha256,
            )
            self.assertEqual(original_path.read_bytes(), original_payload)
            self.assertTrue(
                (directory / f"scouting-result-{A3_ANALYSIS_ID}.json").is_file()
            )
            self.assertTrue(
                (directory / f"supersession-{A3_ANALYSIS_ID}.json").is_file()
            )

            with self.assertRaisesRegex(
                RuntimeError,
                "canonical result cannot be closed",
            ):
                close_session(runtime)
            completion = close_session(runtime, analysis_id=A3_ANALYSIS_ID)
            self.assertEqual(completion["analysis_id"], A3_ANALYSIS_ID)
            self.assertEqual(
                completion["overall_decision"],
                "AWAITING_EMBEDDING_FEASIBILITY_REVIEW",
            )
            self.assertFalse(
                (runtime / "p1_detect_scouting_session.json").exists()
            )
            self.assertEqual(original_path.read_bytes(), original_payload)

    def test_analyze_rejects_truth_from_another_gimbal_driver(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            session_id = "scout-wrong-gimbal"
            prepare_session(runtime, session_id)
            complete_capture(runtime, session_id)
            truth_path = (
                runtime
                / "p1-detect-scouting"
                / session_id
                / "truth"
                / "frame_0000000000.json"
            )
            truth = json.loads(truth_path.read_text(encoding="utf-8"))
            truth["gimbal_driver"] = "controller_follow"
            truth_path.write_text(json.dumps(truth), encoding="utf-8")
            preview_reference(runtime)
            bind_reference(runtime, TARGET_BOX)

            with self.assertRaisesRegex(
                ValueError,
                "mismatched scouting truth identity",
            ):
                analyze_session(
                    runtime,
                    proposer=FakeProposer(hit=True),
                    embedder=FakeEmbedder(),
                )

    def test_visible_unprojectable_target_is_explicit_fail_closed_miss(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            session_id = "scout-null-target-box"
            prepare_session(runtime, session_id)
            complete_capture(runtime, session_id)
            write_frame(
                runtime,
                session_id,
                0,
                7.0,
                remote_visible=True,
                target_box=None,
            )
            preview_reference(runtime)
            bind_reference(runtime, TARGET_BOX)
            result = analyze_session(
                runtime,
                proposer=FakeProposer(hit=True),
                embedder=FakeEmbedder(),
            )

            self.assertEqual(result["recall"]["hits"], 0)
            self.assertEqual(result["recall"]["denominator"], 1)
            self.assertEqual(result["recall"]["missing_pair_misses"], 0)
            self.assertEqual(result["recall"]["value"], 0.0)
            self.assertEqual(result["samples"][0]["status"], "TARGET_BOX_MISSING")

    def test_truth_sidecar_is_not_referenced_by_controller_runtime(self):
        project_root = Path(__file__).resolve().parents[1]
        for path in (project_root / "controller").glob("*.py"):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("p1-detect-scouting", source, path.name)
            self.assertNotIn("p1_detect_scouting_session", source, path.name)
            self.assertNotIn("P1DetectScoutingTruth", source, path.name)
            self.assertNotIn("truth_directed_scouting", source, path.name)
            self.assertNotIn("gimbal_driver", source, path.name)

        # Truth may only be referenced by the evaluator and by scouting
        # profile files. `P1Scene004Scouting.cs` is the scout-3 session type,
        # so it joins the list; nothing on the controller or perception path
        # may ever be added here.
        allowed = {
            "CoverageEvaluator.cs",
            "P1DetectScouting.cs",
            "P1Scene004Scouting.cs",
        }
        for path in (
            project_root / "Assets" / "TetheredTracking" / "Scripts"
        ).glob("*.cs"):
            if path.name in allowed:
                continue
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("P1DetectScoutingTruth", source, path.name)
            self.assertNotIn("p1_detect_scouting_session", source, path.name)
            self.assertNotIn("truth_directed_scouting", source, path.name)
            self.assertNotIn("gimbal_driver", source, path.name)


if __name__ == "__main__":
    unittest.main()
