import hashlib
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

from controller.trackers import (
    DEFAULT_NANOTRACK_V2_MODEL_DIR,
    DEFAULT_NANOTRACK_V2_SPEC,
    CsrtTracker,
    NanoTrackV2Tracker,
    TrackerResult,
    clip_box_norm,
    create_tracker,
    create_csrt_backend,
    load_nanotrack_v2_spec,
    norm_to_csrt_pixels,
    norm_to_pixels,
    pixels_to_norm,
)


class ImageStub:
    shape = (100, 200, 3)


class BackendStub:
    def __init__(self, update_result=(True, (180.0, 90.0, 40.0, 20.0))):
        self.initial_box = None
        self.update_result = update_result

    def init(self, image, box):
        self.initial_box = box
        return None

    def update(self, image):
        return self.update_result


class Cv2Stub:
    __version__ = "test-version"

    def __init__(self, backend):
        self.backend = backend

    def TrackerCSRT_create(self):
        return self.backend


class LegacyCv2Stub:
    class Legacy:
        def __init__(self, backend):
            self.backend = backend

        def TrackerCSRT_create(self):
            return self.backend

    def __init__(self, backend):
        self.legacy = self.Legacy(backend)


class NanoBackendStub:
    def __init__(
        self,
        *,
        update_result=(True, (20.0, 20.0, 60.0, 40.0)),
        score=0.75,
        init_error=None,
        update_error=None,
        score_error=None,
    ):
        self.update_result = update_result
        self.score = score
        self.init_error = init_error
        self.update_error = update_error
        self.score_error = score_error
        self.initial_box = None

    def init(self, image, box):
        if self.init_error is not None:
            raise self.init_error
        self.initial_box = box
        return None

    def update(self, image):
        if self.update_error is not None:
            raise self.update_error
        return self.update_result

    def getTrackingScore(self):
        if self.score_error is not None:
            raise self.score_error
        return self.score


class NanoCv2Stub:
    __version__ = "5.0.0"

    class Dnn:
        DNN_BACKEND_DEFAULT = 0
        DNN_TARGET_CPU = 0

    dnn = Dnn()


def write_nanotrack_fixture(
    directory,
    *,
    backbone=b"backbone",
    neckhead=b"neckhead",
    backbone_hash=None,
    neckhead_hash=None,
):
    root = Path(directory)
    model_dir = root / "models"
    model_dir.mkdir()
    (model_dir / "backbone.onnx").write_bytes(backbone)
    (model_dir / "neckhead.onnx").write_bytes(neckhead)
    spec = {
        "schema_version": "tethered-tracker-models/v1",
        "tracker": "nanotrack-v2",
        "source": {
            "repository": "https://example.invalid/upstream",
            "commit": "a" * 40,
            "tree_url": "https://example.invalid/tree",
            "license_spdx": "Apache-2.0",
            "license_path": "NanoTrack/LICENSE",
            "license_url": "https://example.invalid/license",
            "license_sha256": "b" * 64,
        },
        "opencv": {
            "tested_version": "5.0.0",
            "package_pin": "opencv-contrib-python==5.0.0.93",
            "dnn_backend": "DNN_BACKEND_DEFAULT",
            "dnn_target": "DNN_TARGET_CPU",
        },
        "preprocessing": {"id": "test-preprocessing"},
        "models": {
            "backbone": {
                "filename": "backbone.onnx",
                "url": "https://example.invalid/backbone",
                "sha256": backbone_hash or hashlib.sha256(backbone).hexdigest(),
                "size_bytes": len(backbone),
            },
            "neckhead": {
                "filename": "neckhead.onnx",
                "url": "https://example.invalid/neckhead",
                "sha256": neckhead_hash or hashlib.sha256(neckhead).hexdigest(),
                "size_bytes": len(neckhead),
            },
        },
    }
    spec_path = root / "models.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    return spec_path, model_dir


def make_nanotrack(directory, backend):
    spec_path, model_dir = write_nanotrack_fixture(directory)
    return NanoTrackV2Tracker(
        spec_path=spec_path,
        model_dir=model_dir,
        cv2_module=NanoCv2Stub(),
        backend_factory=lambda *_args: backend,
    )


class TrackerAdapterTests(unittest.TestCase):
    def test_box_conversion_clips_partial_intersections(self):
        clipped = clip_box_norm((-0.1, 0.2, 0.4, 0.5))
        self.assertIsNotNone(clipped)
        for actual, expected in zip(clipped, (0.0, 0.2, 0.3, 0.5)):
            self.assertAlmostEqual(actual, expected)
        self.assertIsNone(clip_box_norm((1.1, 0.2, 0.4, 0.5)))
        for actual, expected in zip(
            norm_to_pixels((0.1, 0.2, 0.3, 0.4), 200, 100),
            (20.0, 20.0, 60.0, 40.0),
        ):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(
            norm_to_csrt_pixels((0.101, 0.202, 0.303, 0.404), 200, 100),
            (20, 20, 61, 41),
        )
        normalized = pixels_to_norm((180.0, 90.0, 40.0, 20.0), 200, 100)
        for actual, expected in zip(normalized, (0.9, 0.9, 0.1, 0.1)):
            self.assertAlmostEqual(actual, expected)

    def test_csrt_adapter_uses_placeholder_not_tracker_confidence(self):
        backend = BackendStub()
        tracker = CsrtTracker(Cv2Stub(backend))
        self.assertTrue(tracker.init(ImageStub(), (0.1, 0.2, 0.3, 0.4)))
        for actual, expected in zip(
            backend.initial_box, (20.0, 20.0, 60.0, 40.0)
        ):
            self.assertAlmostEqual(actual, expected)
        result = tracker.update(ImageStub())
        self.assertTrue(result.ok)
        for actual, expected in zip(result.box_norm, (0.9, 0.9, 0.1, 0.1)):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.confidence_source, "placeholder")

    def test_csrt_failure_and_invalid_box_are_lost(self):
        failure = CsrtTracker(Cv2Stub(BackendStub((False, (0.0, 0.0, 0.0, 0.0)))))
        failure.init(ImageStub(), (0.1, 0.2, 0.3, 0.4))
        self.assertEqual(failure.update(ImageStub()), TrackerResult.lost("tracker_reported_failure"))

        invalid = CsrtTracker(Cv2Stub(BackendStub((True, (250.0, 0.0, 10.0, 10.0)))))
        invalid.init(ImageStub(), (0.1, 0.2, 0.3, 0.4))
        self.assertEqual(invalid.update(ImageStub()), TrackerResult.lost("invalid_tracker_box"))

    def test_constructor_supports_root_and_legacy_bindings(self):
        root_backend = BackendStub()
        legacy_backend = BackendStub()
        self.assertIs(create_csrt_backend(Cv2Stub(root_backend)), root_backend)
        self.assertIs(create_csrt_backend(LegacyCv2Stub(legacy_backend)), legacy_backend)

    def test_nanotrack_requires_complete_local_model_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            spec_path, model_dir = write_nanotrack_fixture(directory)
            (model_dir / "backbone.onnx").unlink()
            with self.assertRaisesRegex(FileNotFoundError, "backbone model is missing"):
                NanoTrackV2Tracker(
                    spec_path=spec_path,
                    model_dir=model_dir,
                    cv2_module=NanoCv2Stub(),
                    backend_factory=lambda *_args: NanoBackendStub(),
                )

        with tempfile.TemporaryDirectory() as directory:
            spec_path, model_dir = write_nanotrack_fixture(directory)
            (model_dir / "backbone.onnx").write_bytes(b"short")
            with self.assertRaisesRegex(ValueError, "size mismatch"):
                NanoTrackV2Tracker(
                    spec_path=spec_path,
                    model_dir=model_dir,
                    cv2_module=NanoCv2Stub(),
                    backend_factory=lambda *_args: NanoBackendStub(),
                )

        with tempfile.TemporaryDirectory() as directory:
            spec_path, model_dir = write_nanotrack_fixture(
                directory,
                backbone_hash="0" * 64,
            )
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                NanoTrackV2Tracker(
                    spec_path=spec_path,
                    model_dir=model_dir,
                    cv2_module=NanoCv2Stub(),
                    backend_factory=lambda *_args: NanoBackendStub(),
                )

    def test_nanotrack_constructor_and_update_exceptions_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            spec_path, model_dir = write_nanotrack_fixture(directory)

            def fail_constructor(*_args):
                raise RuntimeError("bad graph")

            with self.assertRaisesRegex(RuntimeError, "constructor failed"):
                NanoTrackV2Tracker(
                    spec_path=spec_path,
                    model_dir=model_dir,
                    cv2_module=NanoCv2Stub(),
                    backend_factory=fail_constructor,
                )

        with tempfile.TemporaryDirectory() as directory:
            tracker = make_nanotrack(
                directory,
                NanoBackendStub(update_error=RuntimeError("update failed")),
            )
            self.assertTrue(tracker.init(ImageStub(), (0.1, 0.2, 0.3, 0.4)))
            self.assertEqual(
                tracker.update(ImageStub()),
                TrackerResult.lost("tracker_update_error:RuntimeError"),
            )

    def test_nanotrack_rejects_invalid_score_and_box_outputs(self):
        for score in (float("nan"), float("inf"), -0.01, 1.01):
            with self.subTest(score=score), tempfile.TemporaryDirectory() as directory:
                tracker = make_nanotrack(
                    directory,
                    NanoBackendStub(score=score),
                )
                tracker.init(ImageStub(), (0.1, 0.2, 0.3, 0.4))
                self.assertEqual(
                    tracker.update(ImageStub()),
                    TrackerResult.lost("invalid_tracker_confidence"),
                )

        with tempfile.TemporaryDirectory() as directory:
            tracker = make_nanotrack(
                directory,
                NanoBackendStub(update_result=(True, (0.0, 0.0, "bad", 10.0))),
            )
            tracker.init(ImageStub(), (0.1, 0.2, 0.3, 0.4))
            self.assertEqual(
                tracker.update(ImageStub()),
                TrackerResult.lost("invalid_tracker_box"),
            )

    def test_nanotrack_raw_score_and_manifest_identity_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            tracker = make_nanotrack(directory, NanoBackendStub(score=0.375))
            self.assertTrue(tracker.init(ImageStub(), (0.1, 0.2, 0.3, 0.4)))
            result = tracker.update(ImageStub())
            self.assertTrue(result.ok)
            self.assertEqual(result.confidence, 0.375)
            self.assertEqual(result.confidence_source, "tracker")
            identity = json.loads(json.dumps(tracker.manifest_identity()))
            self.assertEqual(identity["name"], "nanotrack-v2")
            self.assertEqual(identity["opencv_version"], "5.0.0")
            self.assertEqual(identity["score_threshold"], None)
            self.assertEqual(identity["threshold_source"], "none")
            self.assertEqual(identity["preprocessing_id"], "test-preprocessing")
            self.assertEqual(
                set(identity["model_sha256"]),
                {"backbone", "neckhead"},
            )

    def test_nanotrack_local_loading_does_not_open_network(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(
                socket,
                "socket",
                side_effect=AssertionError("network access attempted"),
            ):
                tracker = make_nanotrack(directory, NanoBackendStub())
            self.assertEqual(tracker.name, "nanotrack-v2")

    def test_tracker_selector_rejects_unknown_name(self):
        with self.assertRaisesRegex(ValueError, "unknown tracker"):
            create_tracker("not-a-tracker", cv2_module=Cv2Stub(BackendStub()))

    def test_frozen_spec_has_affirmative_artifact_identity(self):
        spec = load_nanotrack_v2_spec(DEFAULT_NANOTRACK_V2_SPEC)
        self.assertEqual(spec["source"]["license_spdx"], "Apache-2.0")
        self.assertEqual(
            spec["source"]["commit"],
            "248663fde6bf7c40190cf10ee396d5662919ecd3",
        )
        self.assertTrue(
            spec["models"]["backbone"]["url"].startswith(
                "https://raw.githubusercontent.com/"
            )
        )

    @unittest.skipIf(cv2 is None or np is None, "pinned track environment not active")
    def test_pinned_opencv_csrt_initializes_and_updates(self):
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        cv2.rectangle(image, (40, 30), (90, 70), (255, 255, 255), -1)
        tracker = CsrtTracker(cv2)
        self.assertTrue(tracker.init(image, (0.2, 0.3, 0.25, 0.4)))
        result = tracker.update(image.copy())
        self.assertTrue(result.ok)
        self.assertEqual(result.confidence_source, "placeholder")

    @unittest.skipIf(
        cv2 is None
        or np is None
        or not (
            DEFAULT_NANOTRACK_V2_MODEL_DIR
            / "nanotrack_backbone_sim.onnx"
        ).is_file(),
        "pinned NanoTrack-v2 models are unavailable",
    )
    def test_pinned_opencv_nanotrack_initializes_and_updates(self):
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(image, (240, 180), (400, 300), (0, 0, 255), -1)
        tracker = NanoTrackV2Tracker(cv2_module=cv2)
        self.assertTrue(tracker.init(image, (0.375, 0.375, 0.25, 0.25)))
        result = tracker.update(image.copy())
        self.assertTrue(result.ok, result.reason)
        self.assertEqual(result.confidence_source, "tracker")
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
