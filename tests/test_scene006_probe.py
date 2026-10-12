import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

import cv2
import numpy as np

from controller.reanchor_models import ProposalBatch
from tools.run_scene006_probe import (
    COLOR_COMPONENT_TOLERANCE,
    EXPECTED_TICKS,
    IDENTITY_ECHO_FIELDS,
    TARGET_APPEARANCE_CONTRACT,
    _default_path_resolver,
    read_strict_json,
    run_probe,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SELECTION_ARTIFACT_PATH = (
    PROJECT_ROOT / "docs/evidence/P1-SCENE-006-prompt-selection-p2.json"
)

MARKER_STEP = 2
K_STAR = 3
PROMPT_MARKER_INDEX = 125
TARGET_BOX = (0.4, 0.4, 0.1, 0.15)
DISTRACTOR_BOX = (0.7, 0.2, 0.1, 0.1)

PROBE_ID = "scene006-probe-test"
SCENARIO_ID = "p1-scene-006-test"
SCENARIO_SHA = "a" * 64
ROAD_SHA = "b" * 64
TRACE_SHA = "c" * 64

SAME_BOX_COSINE = 0.9 + 0.05
OTHER_BOX_COSINE = 0.05


class StubProposer:
    """Proposes the exact truth box on the tick indices in ``hit_indices``."""

    def __init__(self, hit_indices):
        self.hit_indices = set(hit_indices)
        self.initialized_with = None

    def initialize(self, image, box_norm):
        self.initialized_with = tuple(box_norm)

    def propose(self, image):
        # JPEG round-trip is lossy, so frames are marked in spaced steps.
        index = int(round(float(image[0, 0, 0]) / MARKER_STEP))
        if index in self.hit_indices:
            return ProposalBatch((TARGET_BOX,), (0.9,), 1.0)
        return ProposalBatch((), (), 1.0)


class StubEmbedder:
    def embed(self, image, box_norm):
        return (float(box_norm[0]), float(box_norm[1]))

    @staticmethod
    def cosine(left, right):
        return float(abs(right[0] - left[0]) < 1e-9) * 0.9 + 0.05


def _box_dict(box):
    return {"x": box[0], "y": box[1], "width": box[2], "height": box[3]}


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_frame(path: Path, marker_index: int) -> None:
    image = np.zeros((48, 64, 3), dtype=np.uint8)
    image[:, :, 0] = marker_index * MARKER_STEP
    cv2.imwrite(str(path), image)


def _distractor(tick: int, ok: bool = True):
    return {
        "distractor_id": f"distractor-{tick}",
        "kind": "rate_study_distractor",
        "box_status": "OK" if ok else "NOT_IN_FRAME",
        "bbox_xywh_norm": _box_dict(DISTRACTOR_BOX) if ok else None,
    }


def _sidecar(tick_k, *, visible=True, box_status="OK", box=TARGET_BOX, distractors=None):
    return {
        "schema_version": "p1-scene-006-probe-truth/v1",
        "work_id": "P1-SCENE-006",
        "probe_id": PROBE_ID,
        "scenario_id": SCENARIO_ID,
        "scenario_sha256": SCENARIO_SHA,
        "trace_sha256": TRACE_SHA,
        "tick_k": tick_k,
        "simulation_time_s": tick_k / 20.0,
        "camera_position": {"x": 0.0, "y": 50.0, "z": 0.0},
        "camera_rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        "frustum_sample_count": 100,
        "visible_sample_count": 100 if visible else 0,
        "visible_sample_fraction": 1.0 if visible else 0.0,
        "frustum_visible": True,
        "geometrically_visible": visible,
        "target_slant_range_m": 42.0,
        "target_box_status": box_status,
        "target_bbox_xywh_norm": _box_dict(box) if box is not None else None,
        "target_min_side_px": 12.0,
        "distractors": distractors if distractors is not None else [],
    }


def _build_probe(
    root: Path,
    *,
    visible_ticks=None,
    distractors_ok=True,
    unprojectable_ticks=(),
    null_box_ticks=(),
):
    """Build a synthetic probe capture directory; returns the manifest path."""
    frames = root / "frames"
    truth_dir = root / "truth"
    frames.mkdir(parents=True)
    truth_dir.mkdir(parents=True)
    visible = set(EXPECTED_TICKS if visible_ticks is None else visible_ticks)
    for index, tick in enumerate(EXPECTED_TICKS):
        _write_frame(frames / f"frame_{tick:06d}.jpg", index)
        if tick not in visible:
            sidecar = _sidecar(
                tick, visible=False, box_status="TARGET_NOT_VISIBLE", box=None
            )
        elif tick in unprojectable_ticks:
            sidecar = _sidecar(
                tick,
                box_status="TARGET_VISIBLE_UNPROJECTABLE",
                box=None,
                distractors=[_distractor(tick, ok=distractors_ok)],
            )
        elif tick in null_box_ticks:
            sidecar = _sidecar(
                tick,
                box_status="OK",
                box=None,
                distractors=[_distractor(tick, ok=distractors_ok)],
            )
        else:
            sidecar = _sidecar(
                tick, distractors=[_distractor(tick, ok=distractors_ok)]
            )
        _write_json(truth_dir / f"frame_{tick:06d}.json", sidecar)

    prompt_image = frames / f"prompt_{K_STAR:06d}.jpg"
    prompt_truth = truth_dir / f"prompt_{K_STAR:06d}.json"
    _write_frame(prompt_image, PROMPT_MARKER_INDEX)
    _write_json(prompt_truth, _sidecar(K_STAR, distractors=[]))
    manifest = {
        "schema_version": "p1-scene-006-probe-manifest/v1",
        "work_id": "P1-SCENE-006",
        "probe_id": PROBE_ID,
        "scenario_id": SCENARIO_ID,
        "scenario_sha256": SCENARIO_SHA,
        "road_data_sha256": ROAD_SHA,
        "trace_sha256": TRACE_SHA,
        "s_init": K_STAR,
        "k_star": K_STAR,
        "vertical_fov_deg": 60.0,
        "image_width": 64,
        "image_height": 48,
        "jpeg_quality": 95,
        "anchor_world_m": {"x": 0.0, "y": 0.0, "z": 0.0},
        "support_y_m": 0.0,
        "ground_plane_y_m": 0.0,
        "hover_height_m": 50.0,
        "p_hover_world_m": {"x": 0.0, "y": 50.0, "z": 0.0},
        "ticks": list(EXPECTED_TICKS),
        "tick_count": len(EXPECTED_TICKS),
        "prompt": {
            "tick_k": K_STAR,
            "image_file": f"frames/prompt_{K_STAR:06d}.jpg",
            "truth_file": f"truth/prompt_{K_STAR:06d}.json",
            "image_sha256": _sha256(prompt_image),
            "truth_sha256": _sha256(prompt_truth),
        },
        "pairing_rule": "frame_%06d.jpg pairs truth/frame_%06d.json by tick_k",
        "weights_binding_detector_config": "config/detector-reanchor.models.json",
        "weights_binding_tracker_config": "config/nanotrack-v2.models.json",
        "created_by": "test_scene006_probe stub",
    }
    manifest_path = root / "manifest.json"
    _write_json(manifest_path, manifest)
    return manifest_path


class Scene006ProbeTests(unittest.TestCase):
    def test_happy_path_awaits_embedding_review(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_probe(root)
            result = run_probe(
                root,
                proposer=StubProposer(range(len(EXPECTED_TICKS))),
                embedder=StubEmbedder(),
            )
        self.assertEqual(result["schema_version"], "p1-scene-006-probe-result/v1")
        self.assertEqual(result["work_id"], "P1-SCENE-006")
        self.assertEqual(
            result["tool_state"], "AWAITING_EMBEDDING_FEASIBILITY_REVIEW"
        )
        self.assertIsNone(result["fail_reason"])
        self.assertIsNone(result["gate_state"])
        self.assertEqual(result["gate_state_owner"], "acceptance")

        recall = result["recall"]
        self.assertEqual(recall["hits"], 106)
        self.assertEqual(recall["denominator"], 106)
        self.assertEqual(recall["value"], 1.0)
        self.assertFalse(recall["closed_loop_recall_claimed"])

        embedding = result["embedding"]
        self.assertTrue(embedding["report_only"])
        self.assertEqual(embedding["target_cosine"]["count"], 106)
        self.assertAlmostEqual(embedding["target_cosine"]["p05"], SAME_BOX_COSINE)
        self.assertAlmostEqual(
            embedding["target_cosine"]["median"], SAME_BOX_COSINE
        )
        self.assertEqual(embedding["max_distractor_cosine"]["count"], 106)
        self.assertAlmostEqual(
            embedding["max_distractor_cosine"]["p95"], OTHER_BOX_COSINE
        )
        self.assertEqual(embedding["margin"]["count"], 106)
        self.assertAlmostEqual(
            embedding["margin"]["p25"], SAME_BOX_COSINE - OTHER_BOX_COSINE
        )
        self.assertEqual(
            embedding["gate_fraction"],
            {"evaluable_frames": 106, "passing_frames": 106, "value": 1.0},
        )

        self.assertEqual(len(result["samples"]), 106)
        sample = result["samples"][0]
        self.assertEqual(sample["tick_k"], 15)
        self.assertEqual(sample["frame_file"], "frames/frame_000015.jpg")
        self.assertEqual(sample["maximum_target_iou"], 1.0)
        self.assertTrue(sample["recall_hit"])
        self.assertAlmostEqual(sample["target_cosine"], SAME_BOX_COSINE)
        self.assertIsNone(sample["target_embedding_error"])
        self.assertAlmostEqual(
            sample["max_distractor_cosine"], OTHER_BOX_COSINE
        )
        self.assertAlmostEqual(
            sample["margin"], SAME_BOX_COSINE - OTHER_BOX_COSINE
        )
        self.assertEqual(
            sample["distractors"][0]["distractor_id"], "distractor-15"
        )

        identity = result["model_identity"]
        self.assertEqual(len(identity["reanchor_config_sha256"]), 64)
        self.assertEqual(len(identity["detector_weights_sha256"]), 64)
        self.assertEqual(len(identity["appearance_weights_sha256"]), 64)
        self.assertEqual(len(identity["appearance_source_sha256"]), 64)
        self.assertEqual(len(identity["nanotrack_config_sha256"]), 64)
        self.assertEqual(
            identity["nanotrack_backbone_sha256"],
            "530bdd0cd00f19afab79a863e71ba71e3312395a5dc9151af675082bdaaa2fc4",
        )
        self.assertEqual(
            identity["nanotrack_neckhead_sha256"],
            "0d8c0637be849f092cc7236cae02e55c8b9455ebe37ba50601d6115db4247cd9",
        )
        self.assertEqual(
            result["weight_verification"], {"verified": True, "error": None}
        )
        self.assertEqual(
            result["sample_counts"],
            {"target_samples": 106, "distractor_samples": 106},
        )
        self.assertEqual(result["completeness"]["visible_tick_count"], 106)
        self.assertEqual(result["completeness"]["missing_inputs"], [])
        self.assertEqual(result["fidelity_contradictions"], [])
        protocol = result["frozen_protocol"]
        self.assertEqual(protocol["detector_confidence_min"], 0.25)
        self.assertEqual(protocol["detector_iou_min"], 0.30)
        self.assertEqual(protocol["reid_threshold"], 0.5)
        self.assertEqual(protocol["reid_margin"], 0.1)
        self.assertEqual(protocol["minimum_target_samples"], 40)
        self.assertEqual(protocol["minimum_distractor_samples"], 40)
        self.assertEqual(protocol["recall_fail_max"], 0.85)
        self.assertEqual(protocol["recall_proceed_min"], 0.90)
        self.assertEqual(result["probe"]["k_star"], K_STAR)
        self.assertEqual(result["probe"]["tick_count"], 106)
        self.assertEqual(len(result["probe"]["manifest_sha256"]), 64)

    def test_missing_visible_image_is_probe_incomplete(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_probe(root)
            (root / "frames" / "frame_000015.jpg").unlink()
            result = run_probe(
                root,
                proposer=StubProposer(range(len(EXPECTED_TICKS))),
                embedder=StubEmbedder(),
            )
        self.assertEqual(result["tool_state"], "PROBE_INCOMPLETE")
        self.assertEqual(result["fail_reason"], "MISSING_TICK_IMAGE_OR_TRUTH")
        self.assertEqual(
            result["completeness"]["missing_inputs"],
            [{"tick_k": 15, "missing": "image"}],
        )
        self.assertIsNone(result["recall"])
        self.assertIsNone(result["embedding"])
        self.assertEqual(result["samples"], [])
        self.assertIsNone(result["gate_state"])

    def test_missing_truth_sidecar_is_probe_incomplete(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_probe(root)
            (root / "truth" / "frame_000020.json").unlink()
            result = run_probe(
                root,
                proposer=StubProposer(range(len(EXPECTED_TICKS))),
                embedder=StubEmbedder(),
            )
        self.assertEqual(result["tool_state"], "PROBE_INCOMPLETE")
        self.assertEqual(
            result["completeness"]["missing_inputs"],
            [{"tick_k": 20, "missing": "truth_sidecar"}],
        )
        self.assertIsNone(result["recall"])

    def test_unprojectable_visible_tick_is_fidelity_contradiction(self):
        cases = (
            {"unprojectable_ticks": {25}},
            {"null_box_ticks": {25}},
        )
        for kwargs in cases:
            with self.subTest(**kwargs):
                with tempfile.TemporaryDirectory() as raw:
                    root = Path(raw)
                    _build_probe(root, **kwargs)
                    result = run_probe(
                        root,
                        proposer=StubProposer(range(len(EXPECTED_TICKS))),
                        embedder=StubEmbedder(),
                    )
                self.assertEqual(
                    result["tool_state"], "PROBE_FIDELITY_CONTRADICTION"
                )
                self.assertEqual(
                    result["fail_reason"], "VISIBLE_TICK_UNPROJECTABLE"
                )
                self.assertEqual(
                    result["fidelity_contradictions"][0]["tick_k"], 25
                )
                self.assertIsNone(result["recall"])
                self.assertEqual(result["samples"], [])

    def test_sample_floors_are_enforced(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_probe(root, distractors_ok=False)
            result = run_probe(
                root,
                proposer=StubProposer(range(len(EXPECTED_TICKS))),
                embedder=StubEmbedder(),
            )
        self.assertEqual(result["tool_state"], "INCONCLUSIVE")
        self.assertEqual(
            result["fail_reason"], "INSUFFICIENT_TARGET_OR_DISTRACTOR_SAMPLES"
        )
        self.assertEqual(result["sample_counts"]["target_samples"], 106)
        self.assertEqual(result["sample_counts"]["distractor_samples"], 0)
        self.assertIsNone(result["recall"])

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_probe(root, visible_ticks=set(list(EXPECTED_TICKS)[:30]))
            result = run_probe(
                root,
                proposer=StubProposer(range(len(EXPECTED_TICKS))),
                embedder=StubEmbedder(),
            )
        self.assertEqual(result["tool_state"], "INCONCLUSIVE")
        self.assertEqual(result["sample_counts"]["target_samples"], 30)
        self.assertIsNone(result["recall"])

    def test_invisible_tick_image_is_not_required(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_probe(root, visible_ticks=set(EXPECTED_TICKS) - {540})
            (root / "frames" / "frame_000540.jpg").unlink()
            result = run_probe(
                root,
                proposer=StubProposer(range(len(EXPECTED_TICKS))),
                embedder=StubEmbedder(),
            )
        self.assertEqual(
            result["tool_state"], "AWAITING_EMBEDDING_FEASIBILITY_REVIEW"
        )
        self.assertEqual(result["completeness"]["missing_inputs"], [])
        self.assertEqual(result["recall"]["denominator"], 105)
        self.assertEqual(result["recall"]["value"], 1.0)

    def test_recall_bands_follow_the_frozen_chain(self):
        cases = (
            # one miss -> 105/106 ~= 0.9906, still AWAITING
            (set(range(1, 106)), 105, "AWAITING_EMBEDDING_FEASIBILITY_REVIEW", None),
            # 12 misses -> 94/106 ~= 0.8868, inside [0.85, 0.90)
            (set(range(12, 106)), 94, "INCONCLUSIVE", "RECALL_IN_INCONCLUSIVE_BAND"),
            # 20 misses -> 86/106 ~= 0.8113, below 0.85
            (set(range(20, 106)), 86, "FAIL", "RECALL_BELOW_FAIL_MAX"),
        )
        for hit_indices, expected_hits, expected_state, expected_reason in cases:
            with self.subTest(hits=expected_hits):
                with tempfile.TemporaryDirectory() as raw:
                    root = Path(raw)
                    _build_probe(root)
                    result = run_probe(
                        root,
                        proposer=StubProposer(hit_indices),
                        embedder=StubEmbedder(),
                    )
                self.assertEqual(result["recall"]["hits"], expected_hits)
                self.assertEqual(result["recall"]["denominator"], 106)
                self.assertAlmostEqual(
                    result["recall"]["value"], expected_hits / 106, places=12
                )
                self.assertEqual(result["tool_state"], expected_state)
                self.assertEqual(result["fail_reason"], expected_reason)
                # Embedding evidence is report-only and still computed.
                self.assertIsNotNone(result["embedding"])
                self.assertEqual(len(result["samples"]), 106)

    def test_weight_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_probe(root)
            tampered = root / "tampered-yoloe-11s-seg.pt"
            tampered.write_bytes(b"tampered detector weights")

            def resolver(value):
                if str(value) == "runtime/yoloe/yoloe-11s-seg.pt":
                    return tampered
                return _default_path_resolver(value)

            result = run_probe(
                root,
                proposer=StubProposer(range(len(EXPECTED_TICKS))),
                embedder=StubEmbedder(),
                path_resolver=resolver,
            )
        self.assertEqual(result["tool_state"], "FAIL")
        self.assertEqual(result["fail_reason"], "FAIL_WEIGHT_HASH")
        self.assertFalse(result["weight_verification"]["verified"])
        self.assertIn("YOLOE weights", result["weight_verification"]["error"])
        self.assertIsNone(result["recall"])
        self.assertIsNone(result["embedding"])
        self.assertEqual(result["samples"], [])
        self.assertIsNone(result["model_identity"])
        self.assertIsNone(result["gate_state"])

    def test_unloadable_reanchor_config_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_probe(root)
            result = run_probe(
                root,
                proposer=StubProposer(range(len(EXPECTED_TICKS))),
                embedder=StubEmbedder(),
                reanchor_config_path=root / "missing-config.json",
            )
        self.assertEqual(result["tool_state"], "FAIL")
        self.assertEqual(result["fail_reason"], "FAIL_WEIGHT_HASH")
        self.assertIsNone(result["recall"])

    def test_manifest_ticks_contract_is_enforced(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest_path = _build_probe(root)
            manifest = json.loads(manifest_path.read_text())
            manifest["ticks"] = list(EXPECTED_TICKS)[:-1]
            manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")
            with self.assertRaises(ValueError):
                run_probe(
                    root,
                    proposer=StubProposer(set()),
                    embedder=StubEmbedder(),
                )

    def test_prompt_image_hash_is_enforced(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _build_probe(root)
            _write_frame(
                root / "frames" / f"prompt_{K_STAR:06d}.jpg",
                PROMPT_MARKER_INDEX + 1,
            )
            with self.assertRaises(ValueError):
                run_probe(
                    root,
                    proposer=StubProposer(set()),
                    embedder=StubEmbedder(),
                )


V2_BINDING_FIELDS = {
    "baseline_scenario_sha256": "d" * 64,
    "candidate_config_path": "config/scenario.p1-scene-006.json",
    "expected_k_star": K_STAR,
    "k_star_binding_artifact": "docs/evidence/P1-SCENE-006-p3-finalist.json",
    "k_star_binding_artifact_sha256": "e" * 64,
    "capture_commit": "f" * 40,
    "tool_commit": "a" * 40,
    "frozen_tool_paths": [
        "Assets/TetheredTracking/Editor/Scene006",
        "tools/run_scene006_probe.py",
    ],
    "tool_path_zero_diff_verified": True,
    "git_status_porcelain": "",
    "scene_file_sha256_before": "c" * 64,
    "scene_file_sha256_after": "c" * 64,
}


def _upgrade_manifest_to_v2(manifest_path: Path, drop=(), **overrides) -> None:
    """Rewrite a v1 fixture manifest as a v2 (candidate-probe) manifest."""
    manifest = json.loads(manifest_path.read_text())
    manifest["schema_version"] = "p1-scene-006-probe-manifest/v2"
    manifest.update(V2_BINDING_FIELDS)
    manifest.update(overrides)
    for key in drop:
        manifest.pop(key, None)
    manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")


class Scene006CandidateManifestTests(unittest.TestCase):
    """BC-B2-5 binding fields of the v2 (batch-2 candidate) manifest."""

    def test_v2_happy_path_reaches_embedding_review(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest_path = _build_probe(root)
            _upgrade_manifest_to_v2(manifest_path)
            result = run_probe(
                root,
                proposer=StubProposer(range(len(EXPECTED_TICKS))),
                embedder=StubEmbedder(),
            )
        self.assertEqual(
            result["tool_state"], "AWAITING_EMBEDDING_FEASIBILITY_REVIEW"
        )
        self.assertIsNone(result["gate_state"])
        self.assertEqual(result["probe"]["k_star"], K_STAR)
        self.assertEqual(len(result["probe"]["manifest_sha256"]), 64)

    def test_v2_binding_violations_fail_closed(self):
        cases = [
            ("missing-baseline-sha", ("baseline_scenario_sha256",), {}),
            ("short-baseline-sha", (), {"baseline_scenario_sha256": "d" * 63}),
            ("empty-config-path", (), {"candidate_config_path": ""}),
            ("k-star-mismatch", (), {"expected_k_star": K_STAR + 1}),
            ("bool-k-star", (), {"expected_k_star": True}),
            (
                "missing-artifact-sha",
                ("k_star_binding_artifact_sha256",),
                {},
            ),
            ("empty-artifact-path", (), {"k_star_binding_artifact": ""}),
            ("short-capture-commit", (), {"capture_commit": "f" * 39}),
            ("short-tool-commit", (), {"tool_commit": "f" * 39}),
            ("non-hex-capture-commit", (), {"capture_commit": "g" * 40}),
            ("non-hex-tool-commit", (), {"tool_commit": "G" * 40}),
            ("missing-frozen-paths", ("frozen_tool_paths",), {}),
            ("empty-frozen-paths", (), {"frozen_tool_paths": []}),
            (
                "non-list-frozen-paths",
                (),
                {"frozen_tool_paths": "Assets/TetheredTracking/Editor"},
            ),
            ("blank-frozen-path", (), {"frozen_tool_paths": ["tools", ""]}),
            (
                "unverified-zero-diff",
                (),
                {"tool_path_zero_diff_verified": False},
            ),
            (
                "non-bool-zero-diff",
                (),
                {"tool_path_zero_diff_verified": "true"},
            ),
            ("missing-zero-diff", ("tool_path_zero_diff_verified",), {}),
            ("dirty-porcelain", (), {"git_status_porcelain": " M x"}),
            ("missing-porcelain", ("git_status_porcelain",), {}),
            (
                "scene-file-drift",
                (),
                {"scene_file_sha256_after": "d" * 64},
            ),
            (
                "missing-scene-hash-before",
                ("scene_file_sha256_before",),
                {},
            ),
            ("short-scene-hash-after", (), {"scene_file_sha256_after": "c" * 63}),
        ]
        for name, drop, overrides in cases:
            with self.subTest(name):
                with tempfile.TemporaryDirectory() as raw:
                    root = Path(raw)
                    manifest_path = _build_probe(root)
                    _upgrade_manifest_to_v2(
                        manifest_path, drop=drop, **overrides
                    )
                    with self.assertRaises(ValueError):
                        run_probe(
                            root,
                            proposer=StubProposer(set()),
                            embedder=StubEmbedder(),
                        )


SELECTION_ARTIFACT = "docs/evidence/P1-SCENE-006-prompt-selection-p2.json"
SELECTION_SHA = "9" * 64
DOMAIN_COUNT = len(EXPECTED_TICKS)

V3_BINDING_FIELDS = {
    "t1prime_protocol": 2,
    "baseline_scenario_sha256": "d" * 64,
    "candidate_config_path": "config/scenario.p1-scene-006.json",
    "expected_k_star_p2": K_STAR,
    "selection_artifact": SELECTION_ARTIFACT,
    "selection_artifact_sha256": SELECTION_SHA,
    "capture_commit": "f" * 40,
    "tool_commit": "a" * 40,
    "frozen_tool_paths": [
        "Assets/TetheredTracking/Editor/Scene006",
        "Assets/TetheredTracking/Scripts",
    ],
    "tool_path_zero_diff_verified": True,
    "git_status_porcelain": "",
    "scene_file_sha256_before": "c" * 64,
    "scene_file_sha256_after": "c" * 64,
    "detector_models_config_sha256": "1" * 64,
    "tracker_models_config_sha256": "2" * 64,
}


def _band(metric, unit, q05, q95, count=DOMAIN_COUNT):
    return {
        "metric": metric,
        "unit": unit,
        "quantile_method": "type-7",
        "computed": True,
        "count": count,
        "q05": q05,
        "q95": q95,
    }


def _f32(value):
    """What Unity actually writes for a C# `float` literal."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _appearance_block():
    """A manifest block as the Unity renderer would produce it.

    TRS travels through single precision, so the fixture quantizes it the
    same way; the analyzer's constants stay the author's decimals.
    """
    cubes = []
    for cube in TARGET_APPEARANCE_CONTRACT:
        copy = dict(cube)
        for key in ("local_position", "local_rotation", "local_scale"):
            copy[key] = {
                axis: _f32(value) for axis, value in copy[key].items()
            }
        cubes.append(copy)
    return {"source": "test stub", "cubes": cubes}


def _prompt_eligibility(count=DOMAIN_COUNT):
    return {
        "selection_artifact": SELECTION_ARTIFACT,
        "selection_artifact_sha256": SELECTION_SHA,
        "status": "SELECTION_OK",
        "selected_tick": K_STAR,
        "diagnostic_tick": 275,
        "d_v_visible_count": count,
        "d_v_all_members_box_ok": True,
        "d_v_denominator_assertion_count": count,
        "truncation_margin_px": 2.0,
        "off_nadir_definition": "gimbal-law applied angle",
        "min_side_band": _band("min_side_px", "px", 35.0, 90.0, count),
        "off_nadir_band": _band(
            "applied_off_nadir_deg", "deg", 45.0, 45.0, count
        ),
        "warmup_ticks": [
            {"k": 0, "eligible": False, "first_failed_clause": "a_visible"},
            {"k": 1, "eligible": False, "first_failed_clause": "a_visible"},
            {"k": 2, "eligible": False, "first_failed_clause": "c_untruncated"},
            {"k": K_STAR, "eligible": True, "first_failed_clause": ""},
        ],
    }


def _upgrade_manifest_to_v3(manifest_path: Path, drop=(), **overrides) -> None:
    """Rewrite a v1 fixture manifest as a v3 (parity-redirection) manifest."""
    manifest = json.loads(manifest_path.read_text())
    manifest["schema_version"] = "p1-scene-006-probe-manifest/v3"
    manifest.update(V3_BINDING_FIELDS)
    manifest["target_appearance"] = _appearance_block()
    manifest["prompt_eligibility"] = _prompt_eligibility()
    manifest.update(overrides)
    for key in drop:
        manifest.pop(key, None)
    manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")


class Scene006CandidateManifestP2Tests(unittest.TestCase):
    """v3 manifest: appearance parity, prompt-law v2 binding and F20."""

    def test_v3_happy_path_echoes_identity_and_eligibility(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest_path = _build_probe(root)
            _upgrade_manifest_to_v3(manifest_path)
            result = run_probe(
                root,
                proposer=StubProposer(range(len(EXPECTED_TICKS))),
                embedder=StubEmbedder(),
            )
        self.assertEqual(
            result["tool_state"], "AWAITING_EMBEDDING_FEASIBILITY_REVIEW"
        )
        self.assertIsNone(result["gate_state"])
        self.assertEqual(result["target_appearance_differences"], [])

        identity = result["capture_identity"]
        for field in IDENTITY_ECHO_FIELDS:
            self.assertIn(field, identity)
            if field in V3_BINDING_FIELDS:
                self.assertEqual(identity[field], V3_BINDING_FIELDS[field])
        self.assertEqual(identity["scenario_sha256"], SCENARIO_SHA)
        self.assertEqual(identity["trace_sha256"], TRACE_SHA)
        self.assertEqual(len(identity["manifest_sha256"]), 64)

        eligibility = result["prompt_eligibility"]
        self.assertEqual(eligibility["selected_tick"], K_STAR)
        self.assertEqual(eligibility["d_v_visible_count"], DOMAIN_COUNT)
        self.assertEqual(eligibility["min_side_band"]["quantile_method"], "type-7")
        self.assertEqual(result["recall"]["denominator"], DOMAIN_COUNT)

    def test_appearance_mismatch_is_a_fidelity_contradiction(self):
        mutations = [
            ("grey-body", 0, "color_r", 0.5),
            ("dark-roof", 1, "color_b", 0.0),
            ("wrong-shader", 0, "shader_name", "Standard"),
            ("wrong-mesh", 1, "mesh_name", "Sphere"),
        ]
        for name, index, key, value in mutations:
            with self.subTest(name):
                with tempfile.TemporaryDirectory() as raw:
                    root = Path(raw)
                    manifest_path = _build_probe(root)
                    block = _appearance_block()
                    block["cubes"][index][key] = value
                    _upgrade_manifest_to_v3(
                        manifest_path, target_appearance=block
                    )
                    result = run_probe(
                        root,
                        proposer=StubProposer(range(len(EXPECTED_TICKS))),
                        embedder=StubEmbedder(),
                    )
                self.assertEqual(
                    result["tool_state"], "PROBE_FIDELITY_CONTRADICTION"
                )
                self.assertEqual(
                    result["fail_reason"], "TARGET_APPEARANCE_MISMATCH"
                )
                self.assertIsNone(result["recall"])
                self.assertTrue(result["target_appearance_differences"])

    def test_resized_target_is_caught_field_by_field(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest_path = _build_probe(root)
            block = _appearance_block()
            block["cubes"][0]["local_scale"]["z"] = 4.5
            block["cubes"][1]["local_position"]["y"] = 1.3
            _upgrade_manifest_to_v3(manifest_path, target_appearance=block)
            result = run_probe(
                root,
                proposer=StubProposer(set()),
                embedder=StubEmbedder(),
            )
        self.assertEqual(result["tool_state"], "PROBE_FIDELITY_CONTRADICTION")
        self.assertEqual(len(result["target_appearance_differences"]), 2)

    def test_v3_binding_violations_fail_closed(self):
        eligibility_cases = {
            "eligibility-tick-mismatch": {"selected_tick": K_STAR + 1},
            "eligibility-status": {"status": "T1P2_PROMPT_LAW_UNSATISFIABLE"},
            "eligibility-other-artifact": {
                "selection_artifact_sha256": "8" * 64
            },
            "eligibility-non-ok-domain": {"d_v_all_members_box_ok": False},
            "eligibility-zero-domain": {"d_v_visible_count": 0},
            "eligibility-denominator-drift": {
                "d_v_denominator_assertion_count": DOMAIN_COUNT - 1
            },
            "eligibility-domain-drift": {
                "d_v_visible_count": DOMAIN_COUNT - 1,
                "d_v_denominator_assertion_count": DOMAIN_COUNT - 1,
            },
            "eligibility-uncomputed-band": {
                "min_side_band": dict(
                    _band("min_side_px", "px", 35.0, 90.0), computed=False
                )
            },
            "eligibility-wrong-quantile": {
                "off_nadir_band": dict(
                    _band("applied_off_nadir_deg", "deg", 45.0, 45.0),
                    quantile_method="nearest-rank",
                )
            },
            "eligibility-partial-band": {
                "min_side_band": _band(
                    "min_side_px", "px", 35.0, 90.0, DOMAIN_COUNT - 1
                )
            },
            "eligibility-selected-not-eligible": {
                "warmup_ticks": [{"k": K_STAR, "eligible": False}]
            },
            "eligibility-earlier-eligible": {
                "warmup_ticks": [
                    {"k": 1, "eligible": True},
                    {"k": K_STAR, "eligible": True},
                ]
            },
            "eligibility-empty-warmup": {"warmup_ticks": []},
        }
        cases = [
            ("wrong-protocol", (), {"t1prime_protocol": 1}),
            ("missing-protocol", ("t1prime_protocol",), {}),
            ("k-star-mismatch", (), {"expected_k_star_p2": K_STAR + 1}),
            ("legacy-k-star-present", (), {"expected_k_star": K_STAR}),
            ("empty-selection-path", (), {"selection_artifact": ""}),
            ("short-selection-sha", (), {"selection_artifact_sha256": "9" * 63}),
            ("missing-detector-sha", ("detector_models_config_sha256",), {}),
            ("missing-tracker-sha", ("tracker_models_config_sha256",), {}),
            ("missing-eligibility", ("prompt_eligibility",), {}),
            ("missing-appearance", ("target_appearance",), {}),
            ("missing-identity-field", ("capture_commit",), {}),
            ("dirty-porcelain", (), {"git_status_porcelain": " M x"}),
            ("scene-file-drift", (), {"scene_file_sha256_after": "d" * 64}),
        ]
        for name, overrides in eligibility_cases.items():
            eligibility = _prompt_eligibility()
            eligibility.update(overrides)
            cases.append((name, (), {"prompt_eligibility": eligibility}))

        for name, drop, overrides in cases:
            with self.subTest(name):
                with tempfile.TemporaryDirectory() as raw:
                    root = Path(raw)
                    manifest_path = _build_probe(root)
                    _upgrade_manifest_to_v3(
                        manifest_path, drop=drop, **overrides
                    )
                    with self.assertRaises(ValueError):
                        run_probe(
                            root,
                            proposer=StubProposer(set()),
                            embedder=StubEmbedder(),
                        )

    def test_domain_assertion_is_reverified_against_the_capture(self):
        """A capture whose V=1 count differs from |D| cannot be analyzed."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest_path = _build_probe(
                root, visible_ticks=EXPECTED_TICKS[:50]
            )
            _upgrade_manifest_to_v3(manifest_path)
            with self.assertRaises(ValueError):
                run_probe(
                    root,
                    proposer=StubProposer(set()),
                    embedder=StubEmbedder(),
                )

            eligibility = _prompt_eligibility(count=50)
            _upgrade_manifest_to_v3(
                manifest_path, prompt_eligibility=eligibility
            )
            result = run_probe(
                root,
                proposer=StubProposer(set()),
                embedder=StubEmbedder(),
            )
        # Matching |D| lets the chain proceed; the stub proposer hits
        # nothing, so the recall step reports the honest 0/50.
        self.assertEqual(result["tool_state"], "FAIL")
        self.assertEqual(result["sample_counts"]["target_samples"], 50)
        self.assertEqual(result["recall"]["denominator"], 50)


class Scene006StrictJsonTests(unittest.TestCase):
    """BC-P2-10: the committed evidence boundary is standard JSON."""

    def test_committed_selection_artifact_parses_strictly(self):
        self.assertTrue(
            SELECTION_ARTIFACT_PATH.is_file(),
            "the committed prompt-law v2 selection artifact must exist",
        )
        artifact = read_strict_json(SELECTION_ARTIFACT_PATH)
        self.assertEqual(
            artifact["schema_version"], "p1-scene-006-prompt-selection-p2/v1"
        )
        # Unavailable numbers are null, never a bare NaN and never a finite
        # sentinel that would read as a measurement.
        invisible = [
            tick
            for tick in artifact["warmup_ticks"]
            if not tick["geometrically_visible"]
        ]
        self.assertTrue(invisible)
        for tick in invisible:
            self.assertIsNone(tick["min_side_px"])
            self.assertIsNone(tick["margin_left_px"])
        self.assertNotIn("NaN", SELECTION_ARTIFACT_PATH.read_text())

    def test_strict_reader_rejects_the_json_utility_dialect(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "dialect.json"
            for text in (
                '{"a": NaN}',
                '{"a": Infinity}',
                '{"a": -Infinity}',
            ):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    read_strict_json(path)
            path.write_text('{"a": null, "note": "NaN"}')
            self.assertEqual(
                read_strict_json(path), {"a": None, "note": "NaN"}
            )

    def test_v3_capture_is_read_and_written_strictly(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest_path = _build_probe(root)
            _upgrade_manifest_to_v3(manifest_path)
            sidecar = root / "truth" / f"frame_{EXPECTED_TICKS[0]:06d}.json"
            sidecar.write_text(
                sidecar.read_text().replace('"target_min_side_px": 12.0', '"target_min_side_px": NaN')
            )
            with self.assertRaises(ValueError):
                run_probe(
                    root,
                    proposer=StubProposer(set()),
                    embedder=StubEmbedder(),
                )

    def test_manifest_with_a_bare_nan_is_rejected_before_analysis(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest_path = _build_probe(root)
            _upgrade_manifest_to_v3(manifest_path)
            manifest_path.write_text(
                manifest_path.read_text().replace(
                    '"truncation_margin_px": 2.0',
                    '"truncation_margin_px": NaN',
                )
            )
            with self.assertRaises(ValueError):
                run_probe(
                    root,
                    proposer=StubProposer(set()),
                    embedder=StubEmbedder(),
                )

    def test_emitted_gate_artifact_parses_strictly(self):
        """The analyzer's own write is the other half of the boundary."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest_path = _build_probe(root)
            _upgrade_manifest_to_v3(manifest_path)
            result = run_probe(
                root,
                proposer=StubProposer(range(len(EXPECTED_TICKS))),
                embedder=StubEmbedder(),
            )
            output = root / "gate.json"
            output.write_text(
                json.dumps(result, indent=1, sort_keys=True, allow_nan=False)
                + "\n"
            )
            self.assertEqual(
                read_strict_json(output)["tool_state"],
                "AWAITING_EMBEDDING_FEASIBILITY_REVIEW",
            )


class Scene006AppearanceToleranceTests(unittest.TestCase):
    """BC-P2-9: RGBA absorbs the Unity round trip and nothing more."""

    UNITY_ROUND_TRIP = {
        # Observed on Unity 6000.4.1f1, URP Lit, Linear colour space.
        "color_r": 0.9,
        "color_g": 0.119999953,
        "color_b": 0.09999997,
    }

    def _run(self, mutate):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest_path = _build_probe(root)
            block = _appearance_block()
            mutate(block)
            _upgrade_manifest_to_v3(manifest_path, target_appearance=block)
            return run_probe(
                root,
                proposer=StubProposer(range(len(EXPECTED_TICKS))),
                embedder=StubEmbedder(),
            )

    def test_real_unity_round_trip_values_pass(self):
        def mutate(block):
            block["cubes"][0].update(self.UNITY_ROUND_TRIP)
            block["cubes"][1].update(
                {"color_g": 0.07999996, "color_b": 0.06999998}
            )

        result = self._run(mutate)
        self.assertEqual(result["target_appearance_differences"], [])
        self.assertEqual(
            result["tool_state"], "AWAITING_EMBEDDING_FEASIBILITY_REVIEW"
        )
        for field, value in self.UNITY_ROUND_TRIP.items():
            expected = TARGET_APPEARANCE_CONTRACT[0][field]
            self.assertLessEqual(abs(value - expected), COLOR_COMPONENT_TOLERANCE)

    def test_deviation_beyond_the_tolerance_is_caught_per_component(self):
        for cube_index in (0, 1):
            for field in ("color_r", "color_g", "color_b", "color_a"):
                with self.subTest(cube=cube_index, field=field):
                    base = TARGET_APPEARANCE_CONTRACT[cube_index][field]

                    result = self._run(
                        lambda block, i=cube_index, f=field, b=base: block[
                            "cubes"
                        ][i].update({f: b + 5e-7})
                    )
                    self.assertEqual(
                        result["target_appearance_differences"],
                        [],
                        "inside the bound must stay clean",
                    )

                    result = self._run(
                        lambda block, i=cube_index, f=field, b=base: block[
                            "cubes"
                        ][i].update({f: b + 2e-6})
                    )
                    self.assertEqual(
                        result["tool_state"], "PROBE_FIDELITY_CONTRADICTION"
                    )
                    self.assertEqual(
                        len(result["target_appearance_differences"]), 1
                    )

    def test_trs_stays_exact(self):
        """No tolerance leaks into geometry: one ULP of scale is a defect."""
        result = self._run(
            lambda block: block["cubes"][0]["local_scale"].update(
                {"z": 4.000001}
            )
        )
        self.assertEqual(result["tool_state"], "PROBE_FIDELITY_CONTRADICTION")
        self.assertEqual(len(result["target_appearance_differences"]), 1)


if __name__ == "__main__":
    unittest.main()
