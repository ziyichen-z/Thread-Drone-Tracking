import json
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from controller.reanchor_models import ProposalBatch
from tools.build_scene004_geometry import build_geometry
from tools.run_detector_scouting import GIMBAL_DRIVER
from tools.run_scene004_scouting import (
    BOX_STATUS_NOT_VISIBLE,
    BOX_STATUS_UNPROJECTABLE,
    BOX_STATUS_VALID,
    CLASS_MISSING_PAIR,
    CLASS_NOT_VISIBLE,
    CLASS_PAIRED_VISIBLE,
    CLASS_UNPROJECTABLE,
    GATING_RECALL_MIN,
    MISSING_PAIR_RATE_MAX,
    PROFILE_ID,
    SCENARIO_ID,
    SESSION_SCHEMA,
    TRUTH_SCHEMA_V1,
    TRUTH_SCHEMA_V2,
    UNPROJECTABLE_RATE_MAX,
    analyze_session,
    classify_truth,
    _frames,
)
from tools.run_detector_scouting import sha256_file
from tools.run_scene004_scouting import (
    ACTIVE_SESSION_NAME,
    GEOMETRY_ARTIFACT,
    SCENARIO_CONFIG,
    SESSION_ROOT,
    bind_reference,
    close_session,
    prepare_session,
    preview_reference,
    session_document,
)

# Frame index is encoded across two channels because a single uint8 channel
# cannot hold 200 JPEG-robust markers.
MARKER_STEP = 15
MARKER_BASE = 16
BOX = {"x": 0.4, "y": 0.4, "width": 0.1, "height": 0.15}
DISTRACTOR_BOX = {"x": 0.7, "y": 0.2, "width": 0.1, "height": 0.1}


class StubProposer:
    def __init__(self, hit_frames):
        self.hit_frames = set(hit_frames)

    def initialize(self, image, box_norm):
        pass

    def propose(self, image):
        high = int(round(float(image[0, 0, 0]) / MARKER_STEP))
        low = int(round(float(image[0, 0, 1]) / MARKER_STEP))
        index = high * MARKER_BASE + low
        if index not in self.hit_frames:
            return ProposalBatch((), (), 1.0)
        return ProposalBatch(
            ((BOX["x"], BOX["y"], BOX["width"], BOX["height"]),), (0.9,), 1.0
        )


class StubEmbedder:
    def embed(self, image, box_norm):
        return (float(box_norm[0]), float(box_norm[1]))

    @staticmethod
    def cosine(left, right):
        return 0.9 if abs(left[0] - right[0]) < 1e-9 else 0.2


class ClassifyTruthTests(unittest.TestCase):
    def test_v2_status_drives_the_accounting_class(self):
        base = {"schema_version": TRUTH_SCHEMA_V2, "target_visible": True}
        self.assertEqual(
            classify_truth(
                {**base, "target_box_status": BOX_STATUS_VALID, "target_bbox_xywh_norm": BOX}
            ),
            CLASS_PAIRED_VISIBLE,
        )
        self.assertEqual(
            classify_truth({**base, "target_box_status": BOX_STATUS_UNPROJECTABLE}),
            CLASS_UNPROJECTABLE,
        )
        self.assertEqual(
            classify_truth(
                {
                    "schema_version": TRUTH_SCHEMA_V2,
                    "target_visible": False,
                    "target_box_status": BOX_STATUS_NOT_VISIBLE,
                }
            ),
            CLASS_NOT_VISIBLE,
        )

    def test_v2_visible_target_without_a_status_is_rejected(self):
        with self.assertRaises(ValueError):
            classify_truth(
                {
                    "schema_version": TRUTH_SCHEMA_V2,
                    "target_visible": True,
                    "target_bbox_xywh_norm": BOX,
                }
            )

    def test_legacy_v1_is_readable_and_conservative(self):
        self.assertEqual(
            classify_truth(
                {
                    "schema_version": TRUTH_SCHEMA_V1,
                    "target_visible": True,
                    "target_bbox_xywh_norm": BOX,
                }
            ),
            CLASS_PAIRED_VISIBLE,
        )
        # v1 cannot distinguish "no box" from "unprojectable", so it takes the
        # class that stays out of the gating denominator.
        self.assertEqual(
            classify_truth({"schema_version": TRUTH_SCHEMA_V1, "target_visible": True}),
            CLASS_UNPROJECTABLE,
        )

    def test_zeroed_box_with_unprojectable_status_is_not_gating(self):
        # Unity's JsonUtility writes a null object field as a zeroed object,
        # so an unprojectable v2 document arrives with a box present but
        # meaningless. The status, not the box, must decide the class.
        self.assertEqual(
            classify_truth(
                {
                    "schema_version": TRUTH_SCHEMA_V2,
                    "target_visible": True,
                    "target_box_status": BOX_STATUS_UNPROJECTABLE,
                    "target_bbox_xywh_norm": {
                        "x": 0.0,
                        "y": 0.0,
                        "width": 0.0,
                        "height": 0.0,
                    },
                }
            ),
            CLASS_UNPROJECTABLE,
        )

    def test_unknown_schema_fails_closed(self):
        with self.assertRaises(ValueError):
            classify_truth({"schema_version": "something/v9", "target_visible": True})


def _write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1) + "\n")


def _build_capture(root: Path, session_id: str, ticks):
    """ticks: list of (visible, box_status, has_pair)."""
    directory = root / "p1-scene-004-scouting" / session_id
    (root / "frames").mkdir(parents=True, exist_ok=True)
    (directory / "truth").mkdir(parents=True, exist_ok=True)
    _write(
        directory / "manifest.json",
        {
            "schema_version": SESSION_SCHEMA,
            "work_id": "P1-SCENE-004",
            "profile_id": PROFILE_ID,
            "scenario_id": SCENARIO_ID,
            "session_id": session_id,
            "gimbal_driver": GIMBAL_DRIVER,
            "scenario_config_sha256": sha256_file(SCENARIO_CONFIG),
            "geometry_sha256": sha256_file(GEOMETRY_ARTIFACT),
        },
    )
    for index, (visible, status, has_pair) in enumerate(ticks):
        frame_id = index
        time_s = index * 0.5
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        image[:, :, 0] = (frame_id // MARKER_BASE) * MARKER_STEP
        image[:, :, 1] = (frame_id % MARKER_BASE) * MARKER_STEP
        cv2.imwrite(str(root / "frames" / f"frame_{frame_id:010d}.jpg"), image)
        _write(
            root / "frames" / f"frame_{frame_id:010d}.json",
            {
                "schema_version": "tethered-sensor-frame/v1",
                "scenario_id": SCENARIO_ID,
                "frame_id": frame_id,
                "simulation_time_s": time_s,
            },
        )
        if not has_pair:
            continue
        truth = {
            "schema_version": TRUTH_SCHEMA_V2,
            "work_id": "P1-DETECT-001",
            "session_id": session_id,
            "scenario_id": SCENARIO_ID,
            "gimbal_driver": GIMBAL_DRIVER,
            "frame_id": frame_id,
            "simulation_time_s": time_s,
            "target_visible": visible,
            "target_slant_range_m": 26.0 + (index % 5) * 0.8,
            "target_box_status": status,
            "distractors": [
                {
                    "distractor_id": "d0",
                    "bbox_xywh_norm": DISTRACTOR_BOX,
                    "box_status": BOX_STATUS_VALID,
                }
            ],
        }
        if status == BOX_STATUS_VALID:
            truth["target_bbox_xywh_norm"] = BOX
        _write(directory / "truth" / f"frame_{frame_id:010d}.json", truth)

    reference_image = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.imwrite(str(directory / "reference-preview.jpg"), reference_image)
    _write(
        directory / "reference.json",
        {
            "session_id": session_id,
            "frame_id": 0,
            "simulation_time_s": 0.0,
            "box_xywh_norm": [BOX["x"], BOX["y"], BOX["width"], BOX["height"]],
            "image_sha256": sha256_file(directory / "reference-preview.jpg"),
        },
    )
    return directory


def _ticks(total, *, unprojectable=0, missing=0, not_visible=0):
    ticks = []
    for index in range(total):
        if index < unprojectable:
            ticks.append((True, BOX_STATUS_UNPROJECTABLE, True))
        elif index < unprojectable + missing:
            ticks.append((True, BOX_STATUS_VALID, False))
        elif index < unprojectable + missing + not_visible:
            ticks.append((False, BOX_STATUS_NOT_VISIBLE, True))
        else:
            ticks.append((True, BOX_STATUS_VALID, True))
    return ticks


class Scene004ScoutingAccountingTests(unittest.TestCase):
    # 3 loops at 2 Hz over the frozen ~31.07 s period.
    TOTAL = 200

    def test_frame_reader_accepts_historical_v1_and_validated_v3(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            _build_capture(
                runtime,
                "reader",
                [(True, BOX_STATUS_VALID, True)],
            )
            self.assertEqual(_frames(runtime)[0]["frame_id"], 0)
            path = runtime / "frames" / "frame_0000000000.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value.update(
                {
                    "schema_version": "tethered-sensor-frame/v3",
                    "capture_monotonic_s": 501.0,
                    "capture_monotonic_clock_id": "system-stopwatch/v1",
                }
            )
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(_frames(runtime)[0]["frame_id"], 0)
            value["capture_monotonic_s"] = -1.0
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid system monotonic"):
                _frames(runtime)

    def _run(self, ticks, hit_fraction=1.0):
        valid = [
            index
            for index, (visible, status, has_pair) in enumerate(ticks)
            if visible and status == BOX_STATUS_VALID and has_pair
        ]
        hits = valid[: int(round(hit_fraction * len(valid)))]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_capture(root, "scout-3-fixture", ticks)
            return analyze_session(
                root,
                session_id="scout-3-fixture",
                proposer=StubProposer(hits),
                embedder=StubEmbedder(),
            )

    def test_unprojectable_ticks_stay_out_of_the_gating_denominator(self):
        result = self._run(_ticks(self.TOTAL, unprojectable=2))
        accounting = result["accounting"]
        self.assertEqual(accounting["counts"][CLASS_UNPROJECTABLE], 2)
        self.assertEqual(
            accounting["strict_denominator"],
            accounting["counts"][CLASS_PAIRED_VISIBLE],
        )
        self.assertEqual(
            accounting["conservative_denominator"],
            accounting["strict_denominator"]
            + accounting["counts"][CLASS_UNPROJECTABLE]
            + accounting["counts"][CLASS_MISSING_PAIR],
        )
        # A perfect detector still scores 1.0 on the strict denominator.
        self.assertEqual(result["recall"]["strict_value"], 1.0)
        self.assertLess(result["recall"]["conservative_value"], 1.0)
        self.assertEqual(result["recall"]["gated_on"], "strict_value")

    def test_missing_pairs_trip_the_health_gate_before_recall(self):
        # scout-1's failure mode: 40% missing pairs with a perfect detector.
        missing = int(0.4 * self.TOTAL)
        result = self._run(_ticks(self.TOTAL, missing=missing))
        self.assertEqual(result["decision"], "CAPTURE_INCOMPLETE")
        self.assertEqual(result["decision_reason"], "MISSING_PAIR_RATE_ABOVE_LIMIT")
        self.assertGreater(
            result["accounting"]["missing_pair_rate"], MISSING_PAIR_RATE_MAX
        )
        # The old accounting would have reported this as an envelope finding.
        self.assertLess(result["recall"]["conservative_value"], GATING_RECALL_MIN)
        self.assertEqual(result["recall"]["strict_value"], 1.0)

    def test_unprojectable_rate_has_its_own_gate(self):
        result = self._run(_ticks(self.TOTAL, unprojectable=20))
        self.assertEqual(result["decision"], "CAPTURE_INCOMPLETE")
        self.assertEqual(result["decision_reason"], "UNPROJECTABLE_RATE_ABOVE_LIMIT")
        self.assertGreater(
            result["accounting"]["unprojectable_rate"], UNPROJECTABLE_RATE_MAX
        )

    def test_healthy_capture_with_low_recall_is_an_envelope_finding(self):
        result = self._run(_ticks(self.TOTAL), hit_fraction=0.5)
        self.assertEqual(result["decision"], "BENIGN_ENVELOPE_INFEASIBLE")
        self.assertEqual(result["decision_reason"], "STRICT_RECALL_BELOW_GATE")
        self.assertLess(result["recall"]["strict_value"], GATING_RECALL_MIN)

    def test_healthy_capture_never_auto_approves(self):
        result = self._run(_ticks(self.TOTAL))
        self.assertEqual(result["decision"], "AWAITING_EMBEDDING_FEASIBILITY_REVIEW")
        self.assertEqual(result["embedding"]["feasibility_decision"], "REQUIRES_REVIEW")
        self.assertFalse(result["recall"]["closed_loop_recall_claimed"])
        self.assertEqual(
            result["recall"]["interpretation"],
            "ORACLE_POINTED_DETECTABILITY_UPPER_BOUND",
        )
        self.assertFalse(result["descriptive_upper_quartile"]["gating"])

    def test_result_is_create_once(self):
        ticks = _ticks(self.TOTAL)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            directory = _build_capture(root, "scout-3-fixture", ticks)
            valid = list(range(len(ticks)))
            analyze_session(
                root,
                session_id="scout-3-fixture",
                proposer=StubProposer(valid),
                embedder=StubEmbedder(),
            )
            self.assertTrue((directory / "scouting-result.json").is_file())
            with self.assertRaises(Exception):
                analyze_session(
                    root,
                    session_id="scout-3-fixture",
                    proposer=StubProposer(valid),
                    embedder=StubEmbedder(),
                )

    def test_short_capture_is_refused(self):
        with self.assertRaises(ValueError) as context:
            self._run(_ticks(20))
        self.assertIn("short of the required", str(context.exception))


class Scene004GeometryArtifactTests(unittest.TestCase):
    def test_frozen_scenario_passes_every_envelope_gate(self):
        artifact = build_geometry()
        self.assertEqual(artifact["status"], "ENVELOPE_OK")
        self.assertEqual(artifact["label"], "benign-coverage carrier development scenario")
        for name, gate in artifact["gates"].items():
            with self.subTest(gate=name):
                self.assertTrue(gate["passed"], f"{name} failed: {gate}")
                self.assertGreaterEqual(gate["margin"], 0.0)

    def test_ground_plane_stays_bound_to_the_driving_surface(self):
        # C7b: the anchor sits on grass at ~1.3e-6 m, the target drives on
        # asphalt at 0.2 m. The LOS ground plane must follow the target.
        artifact = build_geometry()
        geometry = artifact["geometry"]
        self.assertEqual(geometry["ground_plane_y_m_binding"], 0.2)
        self.assertEqual(geometry["target_plane_y_m"], 0.2)
        self.assertLess(geometry["anchor_world_m"]["y"], 1e-3)
        self.assertAlmostEqual(
            geometry["camera_y_m"],
            geometry["anchor_world_m"]["y"] + 25.0,
            places=9,
        )

    def test_distractor_precheck_reports_real_opportunities(self):
        artifact = build_geometry()
        distractors = artifact["distractors"]
        self.assertEqual(distractors["expected_count"], 2)
        self.assertGreaterEqual(distractors["total_opportunities"], 10)
        self.assertEqual(distractors["minimum_side_floor_px"], 16.0)
        for entry in distractors["per_distractor"]:
            with self.subTest(distractor=entry["prefab_name"]):
                self.assertGreater(entry["fully_in_frame_ticks"], 0)

    def test_pinned_model_crop_floor_is_untouched(self):
        # BC5: the 16 px precheck lives only in the geometry artifact.
        config = json.loads(
            Path("config/detector-reanchor.models.json").read_text()
        )
        self.assertEqual(
            config["appearance"]["preprocessing"]["minimum_crop_side_px"], 2
        )


if __name__ == "__main__":
    unittest.main()


class Scene004SessionLifecycleTests(unittest.TestCase):
    SESSION = "p1-scene-004-scout-3"

    def test_python_and_unity_agree_on_the_session_root(self):
        # Sonnet round 1 note 1: the writer's directory and the analyzer's
        # directory were independent literals, so a scout-3 capture would have
        # written every sidecar where nothing reads it and scored every tick
        # as a missing pair. Both sides must now name the same root.
        source = Path(
            "Assets/TetheredTracking/Scripts/P1Scene004Scouting.cs"
        ).read_text()
        self.assertIn(
            f'RuntimeSessionRoot = "{SESSION_ROOT}"',
            source,
            "the C# session root and the Python analyzer root have diverged",
        )
        self.assertIn(f'FileName = "{ACTIVE_SESSION_NAME}"', source)
        writer = Path(
            "Assets/TetheredTracking/Scripts/P1DetectScouting.cs"
        ).read_text()
        # The writer must derive its directory, never name one.
        self.assertIn("session.SessionRoot", writer)
        self.assertNotIn('Path.Combine(\n                runtimeRoot,\n                "p1-detect-scouting"', writer)

    def test_session_document_binds_the_frozen_scenario_and_geometry(self):
        document = session_document(self.SESSION)
        self.assertEqual(document["profile_id"], PROFILE_ID)
        self.assertEqual(document["scenario_id"], SCENARIO_ID)
        self.assertTrue(document["non_measurement"])
        self.assertEqual(
            document["scenario_config_sha256"], sha256_file(SCENARIO_CONFIG)
        )
        self.assertEqual(
            document["geometry_sha256"], sha256_file(GEOMETRY_ARTIFACT)
        )
        # The loop period comes from the artifact, never a restated literal.
        self.assertAlmostEqual(document["loop_period_s"], 31.0711, places=3)
        self.assertEqual(document["gating_recall_min"], GATING_RECALL_MIN)

    def test_session_id_is_validated(self):
        for bad in ("Scout3", "3-scout", "scout_3", "", "x" * 49):
            with self.subTest(session_id=bad):
                with self.assertRaises(ValueError):
                    session_document(bad)

    def test_prepare_is_create_once_and_refuses_a_second_session(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = prepare_session(root, self.SESSION)
            self.assertTrue((root / ACTIVE_SESSION_NAME).is_file())
            self.assertTrue(
                (root / SESSION_ROOT / self.SESSION / "manifest.json").is_file()
            )
            # Re-preparing the same session is idempotent.
            self.assertEqual(prepare_session(root, self.SESSION), first)
            # A different one must not silently take over the marker.
            rejected = "p1-scene-004-scout-3b"
            with self.assertRaises(ValueError):
                prepare_session(root, rejected)
            self.assertFalse(
                (root / SESSION_ROOT / rejected).exists(),
                "a refused prepare must not leave an orphaned session",
            )

    def test_reference_preview_bind_and_close_round_trip(self):
        # The reference lands at 7 s, so the capture needs 3 loops *after*
        # that; 200 ticks would be refused, which is itself correct.
        ticks = _ticks(220)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_capture(root, self.SESSION, ticks)
            # Let the real lifecycle own every document the fixture stubbed.
            for name in ("manifest.json", "reference.json", "reference-preview.jpg"):
                (root / SESSION_ROOT / self.SESSION / name).unlink()
            prepare_session(root, self.SESSION)

            preview = preview_reference(root, self.SESSION)
            # [7,8) s window: frames are 0.5 s apart, so frame 14 at 7.0 s.
            self.assertEqual(preview["frame_id"], 14)
            self.assertGreaterEqual(preview["simulation_time_s"], 7.0)
            self.assertLess(preview["simulation_time_s"], 8.0)

            reference = bind_reference(root, self.SESSION, [0.4, 0.4, 0.1, 0.15])
            self.assertEqual(reference["frame_id"], preview["frame_id"])
            self.assertEqual(reference["image_sha256"], preview["image_sha256"])

            # Closing before a result exists must fail.
            with self.assertRaises(ValueError):
                close_session(root, self.SESSION)

            analyze_session(
                root,
                session_id=self.SESSION,
                proposer=StubProposer(range(len(ticks))),
                embedder=StubEmbedder(),
            )
            completion = close_session(root, self.SESSION)
            self.assertEqual(
                completion["decision"], "AWAITING_EMBEDDING_FEASIBILITY_REVIEW"
            )
            self.assertFalse((root / ACTIVE_SESSION_NAME).exists())
            self.assertTrue(
                (root / SESSION_ROOT / self.SESSION / "completion.json").is_file()
            )
