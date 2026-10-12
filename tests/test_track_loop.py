from collections import deque
from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

from controller.run_log import RunLogger, read_frame_records
from controller.qualification_protocol import (
    ACK_FILE as QUALIFICATION_ACK_FILE,
    QualificationReleaseLifecycle,
    manifest_identity as qualification_release_manifest_identity,
    request_release as request_qualification_release,
)
from controller.reanchor_runtime import RuntimeEvent
from controller.track_loop import FrameRepository, RuntimePublisher, TrackLoop, main
from controller.trackers import (
    DEFAULT_NANOTRACK_V2_MODEL_DIR,
    DEFAULT_NANOTRACK_V2_SPEC,
    TrackerResult,
)


class ImageStub:
    shape = (100, 200, 3)

    def __init__(self, frame_id):
        self.frame_id = frame_id


class RecordingTracker:
    name = "recording"
    backend = "test"
    version = "1"

    def __init__(self, results):
        self.results = deque(results)
        self.initialized_on = None
        self.update_frame_ids = []

    def init(self, image, box_norm):
        self.initialized_on = image.frame_id
        return True

    def update(self, image):
        self.update_frame_ids.append(image.frame_id)
        return self.results.popleft()


class RecordingReanchorRuntime:
    def __init__(self, replacement=None, *, fail_after_frame=False):
        self.replacement = replacement
        self.fail_after_frame = fail_after_frame
        self.initialize_calls = []
        self.before_calls = []
        self.after_calls = []
        self.poll_calls = 0
        self.fatal_reason = None
        self.events = []

    def initialize(self, bundle, box_norm):
        self.initialize_calls.append((bundle.frame_id, tuple(box_norm)))

    def before_update(self, frame_id, *, old_tracker_instance_id=None):
        self.before_calls.append((frame_id, old_tracker_instance_id))
        replacement, self.replacement = self.replacement, None
        return replacement

    def after_frame(self, bundle, result, *, released):
        self.after_calls.append((bundle.frame_id, result.ok, released))
        self.events.append(
            RuntimeEvent(bundle.frame_id, "TEST_REANCHOR_EVENT", {"released": released})
        )
        if self.fail_after_frame:
            self.fatal_reason = "synthetic_reanchor_failure"

    def poll(self):
        self.poll_calls += 1

    def drain_events(self):
        events = tuple(self.events)
        self.events.clear()
        return events


def valid_result(box=(0.4, 0.3, 0.2, 0.2)):
    return TrackerResult(box, True, 1.0, "placeholder")


def frame_metadata(
    frame_id,
    *,
    forward=(0.0, -1.0, 0.0),
    scenario_id="test-scenario",
):
    return {
        "schema_version": "tethered-sensor-frame/v3",
        "scenario_id": scenario_id,
        "frame_id": frame_id,
        "simulation_time_s": frame_id * 0.2,
        "capture_unix_s": 1_800_000_000.0 + frame_id * 0.2,
        "capture_monotonic_s": 500.0 + frame_id * 0.2,
        "capture_monotonic_clock_id": "system-stopwatch/v1",
        "camera_position_world_m": [0.0, 10.0, 0.0],
        "camera_forward_world": list(forward),
        "camera_right_world": [1.0, 0.0, 0.0],
        "camera_up_world": [0.0, 0.0, 1.0],
        "width": 200,
        "height": 100,
        "intrinsics_px": {
            "fx": 100.0,
            "fy": 100.0,
            "cx": 100.0,
            "cy": 50.0,
        },
    }


def write_frame(
    runtime,
    frame_id,
    *,
    forward=(0.0, -1.0, 0.0),
    scenario_id="test-scenario",
):
    frames = runtime / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    stem = f"frame_{frame_id:010d}"
    (frames / f"{stem}.jpg").write_bytes(b"test-image")
    (frames / f"{stem}.json").write_text(
        json.dumps(
            frame_metadata(
                frame_id,
                forward=forward,
                scenario_id=scenario_id,
            )
        ),
        encoding="utf-8",
    )


def image_loader(path):
    return ImageStub(int(path.stem.split("_")[1]))


def make_loop(
    runtime,
    tracker,
    *,
    condition="follow",
    run_id="test-run",
    reanchor_runtime=None,
):
    logger = RunLogger(runtime, run_id, {"condition": condition})
    loop = TrackLoop(
        FrameRepository(runtime, image_loader),
        tracker,
        RuntimePublisher(runtime, 1.0),
        logger,
        track_id="target-0",
        condition=condition,
        ground_plane_y_m=0.0,
        maximum_ground_range_m=1000.0,
        planned_duration_s=100.0,
        reanchor_runtime=reanchor_runtime,
    )
    return loop, logger


class TrackLoopTests(unittest.TestCase):
    def test_repository_rejects_legacy_and_wrong_monotonic_clocks(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            write_frame(runtime, 0)
            metadata_path = runtime / "frames" / "frame_0000000000.json"
            value = json.loads(metadata_path.read_text(encoding="utf-8"))

            value["schema_version"] = "tethered-sensor-frame/v1"
            metadata_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported schema"):
                FrameRepository(runtime, image_loader).load(0)

            value["schema_version"] = "tethered-sensor-frame/v3"
            value["capture_monotonic_clock_id"] = "unity-process-relative/v1"
            metadata_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError,
                "requires capture_monotonic_clock_id",
            ):
                FrameRepository(runtime, image_loader).load(0)

            value["capture_monotonic_clock_id"] = "system-stopwatch/v1"
            value["capture_monotonic_s"] = float("nan")
            metadata_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be finite"):
                FrameRepository(runtime, image_loader).load(0)

    def test_cli_rejects_legacy_init_frame_before_tracker_or_run_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            write_frame(runtime, 0)
            metadata_path = runtime / "frames" / "frame_0000000000.json"
            value = json.loads(metadata_path.read_text(encoding="utf-8"))
            value["schema_version"] = "tethered-sensor-frame/v1"
            metadata_path.write_text(json.dumps(value), encoding="utf-8")

            with patch("controller.track_loop.create_tracker") as create:
                with self.assertRaisesRegex(ValueError, "unsupported schema"):
                    main(
                        [
                            "--runtime",
                            str(runtime),
                            "--tracker",
                            "nanotrack-v2",
                            "--init-frame",
                            "0",
                            "--init-box",
                            "0.2",
                            "0.3",
                            "0.25",
                            "0.4",
                            "--track-id",
                            "target-0",
                            "--scenario-id",
                            "test-scenario",
                            "--condition",
                            "follow",
                            "--ground-plane-y-m",
                            "0.0",
                            "--planned-duration-s",
                            "1.0",
                            "--run-id",
                            "must-not-exist",
                        ]
                    )
                create.assert_not_called()
            self.assertFalse((runtime / "runs").exists())

    def test_cli_rejects_rate2_reanchor_before_runtime_or_model_access(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            with patch("controller.track_loop.create_tracker") as create:
                with self.assertRaisesRegex(ValueError, "incompatible with the RATE-002"):
                    main(
                        [
                            "--runtime",
                            str(runtime),
                            "--tracker",
                            "nanotrack-v2",
                            "--reanchor-config",
                            "unused.json",
                            "--rate2-session",
                            "--init-frame",
                            "0",
                            "--init-box",
                            "0.2",
                            "0.3",
                            "0.25",
                            "0.4",
                            "--track-id",
                            "target-0",
                            "--scenario-id",
                            "test-scenario",
                            "--condition",
                            "follow",
                            "--ground-plane-y-m",
                            "0.0",
                            "--planned-duration-s",
                            "1.0",
                        ]
                    )
                create.assert_not_called()
            self.assertFalse((runtime / "runs").exists())

    def test_reanchor_integration_swaps_before_update_and_audits_events(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for frame_id in range(3):
                write_frame(runtime, frame_id)
            original = RecordingTracker([])
            replacement = RecordingTracker([valid_result(), valid_result()])
            reanchor = RecordingReanchorRuntime(replacement)
            loop, logger = make_loop(
                runtime,
                original,
                reanchor_runtime=reanchor,
            )
            try:
                loop.initialize(0, (0.4, 0.3, 0.2, 0.2))
                self.assertEqual(loop.process_available(2), 2)
                self.assertEqual(reanchor.initialize_calls[0][0], 0)
                self.assertEqual(
                    [call[0] for call in reanchor.before_calls],
                    [0, 1],
                )
                self.assertEqual(original.update_frame_ids, [])
                self.assertEqual(replacement.update_frame_ids, [1, 2])
                self.assertEqual(
                    reanchor.after_calls,
                    [(1, True, True), (2, True, True)],
                )
                records, _ = read_frame_records(logger.frames_path)
                event_records = [
                    record
                    for record in records
                    if record.get("record_kind") == "event"
                ]
                self.assertEqual(len(event_records), 2)
                self.assertTrue(
                    all(
                        record["event"] == "TEST_REANCHOR_EVENT"
                        for record in event_records
                    )
                )
            finally:
                logger.close()

    def test_reanchor_fatal_reason_terminates_track_loop(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for frame_id in range(2):
                write_frame(runtime, frame_id)
            reanchor = RecordingReanchorRuntime(fail_after_frame=True)
            loop, logger = make_loop(
                runtime,
                RecordingTracker([valid_result()]),
                reanchor_runtime=reanchor,
            )
            try:
                loop.initialize(0, (0.4, 0.3, 0.2, 0.2))
                self.assertEqual(loop.process_available(1), 0)
                self.assertTrue(loop.terminal)
                self.assertEqual(loop.state, "ERROR_REINIT_REQUIRED")
                records, _ = read_frame_records(logger.frames_path)
                terminal = next(
                    record
                    for record in records
                    if record.get("event") == "REANCHOR_FAIL_CLOSED"
                )
                self.assertEqual(
                    terminal["reason"],
                    "synthetic_reanchor_failure",
                )
                self.assertTrue(
                    any(
                        record.get("event") == "TEST_REANCHOR_EVENT"
                        for record in records
                    )
                )
            finally:
                logger.close()

    def test_qualification_release_excludes_paused_backlog_from_all_origins(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for frame_id in range(4):
                write_frame(
                    runtime,
                    frame_id,
                    scenario_id="p1-scene-004",
                )
            run_id = "p1-detect-001-qual-99"
            logger = RunLogger(
                runtime,
                run_id,
                {
                    "scenario_id": "p1-scene-004",
                    "condition": "follow",
                    "planned_duration_s": 0.19,
                    "init": {
                        "frame_id": 0,
                        "box_norm": [0.4, 0.3, 0.2, 0.2],
                    },
                    "qualification_release": (
                        qualification_release_manifest_identity()
                    ),
                },
            )
            lifecycle = QualificationReleaseLifecycle(
                runtime,
                run_id,
                scenario_id="p1-scene-004",
                init_frame_id=0,
                unix_time=lambda: 1_800_000_000.1,
                monotonic=lambda: 500.1,
            )
            reanchor = RecordingReanchorRuntime()
            loop = TrackLoop(
                FrameRepository(runtime, image_loader),
                RecordingTracker(
                    [valid_result(), valid_result(), valid_result()]
                ),
                RuntimePublisher(runtime, 1.0),
                logger,
                track_id="target-0",
                condition="follow",
                ground_plane_y_m=0.0,
                maximum_ground_range_m=1000.0,
                planned_duration_s=0.19,
                reanchor_runtime=reanchor,
                qualification_lifecycle=lifecycle,
            )
            try:
                loop.initialize(0, (0.4, 0.3, 0.2, 0.2))
                self.assertFalse((runtime / "tracking_observation.json").exists())
                self.assertFalse((runtime / "gimbal_command.json").exists())
                self.assertEqual(loop.process_available(1), 1)
                self.assertFalse((runtime / "tracking_observation.json").exists())
                self.assertFalse(loop.complete)

                request_qualification_release(
                    runtime,
                    run_id,
                    unix_time=lambda: 1_800_000_000.3,
                    monotonic=lambda: 500.3,
                    command_id_factory=lambda: "track-loop-release",
                )
                self.assertEqual(loop.process_available(2), 1)
                observation = json.loads(
                    (runtime / "tracking_observation.json").read_text()
                )
                self.assertEqual(observation["observation"]["frame_id"], 2)
                self.assertTrue(
                    (logger.run_directory / QUALIFICATION_ACK_FILE).is_file()
                )
                self.assertFalse(loop.complete)

                self.assertEqual(loop.process_available(3), 1)
                self.assertTrue(loop.complete)
                self.assertEqual(
                    reanchor.after_calls,
                    [(1, True, False), (2, True, True), (3, True, True)],
                )
                records, _ = read_frame_records(logger.frames_path)
                frames = [
                    record
                    for record in records
                    if record.get("record_kind", "frame") == "frame"
                ]
                self.assertEqual(
                    [record["phase"] for record in frames],
                    ["hold", "hold", "measurement", "measurement"],
                )
                self.assertEqual(
                    [record["published_observation"] for record in frames],
                    [False, False, True, True],
                )
                self.assertEqual(
                    frames[2]["measurement_elapsed_s"],
                    0.0,
                )
                self.assertEqual(
                    frames[2]["measurement_wall_elapsed_s"],
                    0.0,
                )
            finally:
                logger.close()

    def test_backlog_updates_every_frame_and_publishes_only_latest(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for frame_id in range(4):
                write_frame(runtime, frame_id)
            tracker = RecordingTracker([valid_result(), valid_result(), valid_result()])
            loop, logger = make_loop(runtime, tracker)
            try:
                loop.initialize(0, (0.4, 0.3, 0.2, 0.2))
                self.assertEqual(loop.process_available(3), 3)
                observation = json.loads(
                    (runtime / "tracking_observation.json").read_text()
                )
                self.assertEqual(observation["observation"]["frame_id"], 3)
                self.assertEqual(tracker.update_frame_ids, [1, 2, 3])
                records, _ = read_frame_records(logger.frames_path)
                self.assertEqual(
                    [record["published_observation"] for record in records],
                    [True, False, False, True],
                )
                self.assertEqual(sum(record["skipped_count"] for record in records), 2)
                self.assertEqual(records[-1]["backlog_count"], 2)
            finally:
                logger.close()

    def test_forced_failure_writes_neither_slot_then_can_recover(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for frame_id in range(3):
                write_frame(runtime, frame_id)
            tracker = RecordingTracker(
                [TrackerResult.lost("forced_failure"), valid_result()]
            )
            loop, logger = make_loop(runtime, tracker)
            try:
                loop.initialize(0, (0.4, 0.3, 0.2, 0.2))
                observation_before = (runtime / "tracking_observation.json").read_bytes()
                gimbal_before = (runtime / "gimbal_command.json").read_bytes()
                loop.process_available(1)
                self.assertEqual(
                    (runtime / "tracking_observation.json").read_bytes(),
                    observation_before,
                )
                self.assertEqual(
                    (runtime / "gimbal_command.json").read_bytes(),
                    gimbal_before,
                )
                self.assertEqual(loop.state, "LOST")

                loop.process_available(2)
                observation = json.loads(
                    (runtime / "tracking_observation.json").read_text()
                )
                self.assertEqual(observation["observation"]["frame_id"], 2)
                self.assertEqual(loop.state, "TRACKING")
                records, _ = read_frame_records(logger.frames_path)
                self.assertEqual(records[1]["event"], "LOST")
                self.assertTrue(records[2]["recovered_from_lost"])
            finally:
                logger.close()

    def test_missing_retained_intermediate_frame_requires_reinit(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            write_frame(runtime, 0)
            write_frame(runtime, 2)
            tracker = RecordingTracker([valid_result()])
            loop, logger = make_loop(runtime, tracker)
            try:
                loop.initialize(0, (0.4, 0.3, 0.2, 0.2))
                observation_before = (runtime / "tracking_observation.json").read_bytes()
                self.assertEqual(loop.process_available(2), 0)
                self.assertTrue(loop.terminal)
                self.assertEqual(loop.state, "ERROR_REINIT_REQUIRED")
                self.assertEqual(tracker.update_frame_ids, [])
                self.assertEqual(
                    (runtime / "tracking_observation.json").read_bytes(),
                    observation_before,
                )
                records, _ = read_frame_records(logger.frames_path)
                self.assertEqual(records[-1]["event"], "GAP")
            finally:
                logger.close()

    def test_frame_id_rollback_requires_reinit(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            write_frame(runtime, 5)
            loop, logger = make_loop(runtime, RecordingTracker([]))
            try:
                loop.initialize(5, (0.4, 0.3, 0.2, 0.2))
                loop.process_available(4)
                self.assertTrue(loop.terminal)
                records, _ = read_frame_records(logger.frames_path)
                self.assertEqual(records[-1]["event"], "REINIT_REQUIRED")
                self.assertEqual(
                    records[-1]["reason"], "frame_id_reset_or_rollback"
                )
            finally:
                logger.close()

    def test_geometry_rejection_still_publishes_observation_not_gimbal(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            write_frame(runtime, 0)
            write_frame(runtime, 1, forward=(0.0, 1.0, 0.0))
            loop, logger = make_loop(runtime, RecordingTracker([valid_result()]))
            try:
                loop.initialize(0, (0.4, 0.3, 0.2, 0.2))
                gimbal_before = (runtime / "gimbal_command.json").read_bytes()
                loop.process_available(1)
                observation = json.loads(
                    (runtime / "tracking_observation.json").read_text()
                )
                self.assertEqual(observation["observation"]["frame_id"], 1)
                self.assertEqual(
                    (runtime / "gimbal_command.json").read_bytes(),
                    gimbal_before,
                )
                records, _ = read_frame_records(logger.frames_path)
                self.assertEqual(records[-1]["event"], "GEO_REJECT")
                self.assertFalse(records[-1]["published_gimbal_command"])
            finally:
                logger.close()

    def test_nadir_is_issued_once_and_updates_do_not_replace_it(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            write_frame(runtime, 0)
            write_frame(runtime, 1)
            loop, logger = make_loop(
                runtime,
                RecordingTracker([valid_result()]),
                condition="nadir",
            )
            try:
                loop.initialize(0, (0.4, 0.3, 0.2, 0.2))
                command_before = (runtime / "gimbal_command.json").read_bytes()
                loop.process_available(1)
                self.assertEqual(
                    (runtime / "gimbal_command.json").read_bytes(),
                    command_before,
                )
                command = json.loads(command_before)
                self.assertEqual(command["command"]["mode"], "nadir")
            finally:
                logger.close()

    def test_initialization_requires_exact_retained_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            loop, logger = make_loop(runtime, RecordingTracker([]))
            try:
                with self.assertRaisesRegex(FileNotFoundError, "exact retained"):
                    loop.initialize(7, (0.4, 0.3, 0.2, 0.2))
            finally:
                logger.close()

    def test_cli_has_no_implicit_ground_plane_default(self):
        errors = io.StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as raised:
            main(
                [
                    "--init-frame",
                    "0",
                    "--init-box",
                    "0.2",
                    "0.3",
                    "0.25",
                    "0.4",
                    "--track-id",
                    "target-0",
                    "--scenario-id",
                    "test-scenario",
                    "--condition",
                    "follow",
                    "--planned-duration-s",
                    "1.0",
                ]
            )
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("--ground-plane-y-m", errors.getvalue())

    def test_cli_qualification_barrier_rejects_missing_reanchor_before_access(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            with patch("controller.track_loop.create_tracker") as create:
                errors = io.StringIO()
                with redirect_stderr(errors), self.assertRaises(SystemExit) as raised:
                    main(
                        [
                            "--runtime",
                            str(runtime),
                            "--qualification-release-barrier",
                            "--tracker",
                            "nanotrack-v2",
                            "--init-frame",
                            "0",
                            "--init-box",
                            "0.2",
                            "0.3",
                            "0.25",
                            "0.4",
                            "--track-id",
                            "target-0",
                            "--scenario-id",
                            "p1-scene-004",
                            "--condition",
                            "follow",
                            "--ground-plane-y-m",
                            "0.0",
                            "--planned-duration-s",
                            "150",
                            "--run-id",
                            "p1-detect-001-qual-99",
                        ]
                    )
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("requires --reanchor-config", errors.getvalue())
                create.assert_not_called()
            self.assertFalse((runtime / "runs").exists())

    @unittest.skipIf(cv2 is None or np is None, "pinned track environment not active")
    def test_cli_runs_pinned_csrt_to_a_versioned_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            frames = runtime / "frames"
            frames.mkdir()
            for frame_id in (0, 1):
                image = np.zeros((100, 200, 3), dtype=np.uint8)
                cv2.rectangle(
                    image,
                    (40 + frame_id, 30),
                    (90 + frame_id, 70),
                    (255, 255, 255),
                    -1,
                )
                stem = f"frame_{frame_id:010d}"
                self.assertTrue(cv2.imwrite(str(frames / f"{stem}.jpg"), image))
                (frames / f"{stem}.json").write_text(
                    json.dumps(frame_metadata(frame_id)),
                    encoding="utf-8",
                )
            (frames / "latest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "tethered-frame-manifest/v1",
                        "frame_id": 1,
                        "image_file": "frame_0000000001.jpg",
                        "metadata_file": "frame_0000000001.json",
                    }
                ),
                encoding="utf-8",
            )
            (runtime / "metrics.json").write_text(
                json.dumps(
                    {
                        "schema_version": "tethered-evaluation/v1",
                        "scenario_id": "test-scenario",
                        "aggregate": {"c_track": 1.0},
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "controller.track_loop",
                    "--runtime",
                    str(runtime),
                    "--init-frame",
                    "0",
                    "--init-box",
                    "0.2",
                    "0.3",
                    "0.25",
                    "0.4",
                    "--track-id",
                    "target-0",
                    "--scenario-id",
                    "test-scenario",
                    "--condition",
                    "follow",
                    "--ground-plane-y-m",
                    "0.0",
                    "--planned-duration-s",
                    "0.2",
                    "--run-id",
                    "cli-integration",
                    "--rate-study-rate-hz",
                    "20",
                    "--rate-study-replicate",
                    "1",
                    "--rate-study-replicate-id",
                    "rate20-follow-r1",
                    "--rate-study-attempt-id",
                    "cli-integration",
                    "--loop-duration-s",
                    "104.5",
                    "--scenario-config-sha256",
                    "a" * 64,
                    "--init-image-sha256",
                    "b" * 64,
                    "--reference-image-sha256",
                    "c" * 64,
                    "--reference-frame-id",
                    "7",
                    "--reference-simulation-time-s",
                    "3.2",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(
                (
                    runtime
                    / "runs"
                    / "cli-integration"
                    / "summary.json"
                ).read_text()
            )
            self.assertEqual(summary["total_frame_records"], 2)
            self.assertEqual(summary["published_observations"], 2)
            self.assertTrue(summary["metrics_snapshot_present"])
            manifest = json.loads(
                (
                    runtime
                    / "runs"
                    / "cli-integration"
                    / "manifest.json"
                ).read_text()
            )
            self.assertEqual(manifest["rate_study"]["rate_hz"], 20)
            self.assertEqual(
                manifest["rate_study"]["replicate_id"],
                "rate20-follow-r1",
            )
            self.assertEqual(manifest["rate_study"]["loop_duration_s"], 104.5)
            self.assertEqual(manifest["tracker"]["name"], "csrt")

    @unittest.skipIf(
        cv2 is None
        or np is None
        or not (
            DEFAULT_NANOTRACK_V2_MODEL_DIR
            / "nanotrack_backbone_sim.onnx"
        ).is_file(),
        "pinned NanoTrack-v2 models are unavailable",
    )
    def test_cli_nanotrack_manifest_contains_frozen_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            frames = runtime / "frames"
            frames.mkdir()
            for frame_id in (0, 1):
                image = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.rectangle(
                    image,
                    (240 + frame_id, 180),
                    (400 + frame_id, 300),
                    (0, 0, 255),
                    -1,
                )
                stem = f"frame_{frame_id:010d}"
                self.assertTrue(cv2.imwrite(str(frames / f"{stem}.jpg"), image))
                metadata = frame_metadata(frame_id)
                metadata["width"] = 640
                metadata["height"] = 480
                metadata["intrinsics_px"] = {
                    "fx": 320.0,
                    "fy": 320.0,
                    "cx": 320.0,
                    "cy": 240.0,
                }
                (frames / f"{stem}.json").write_text(
                    json.dumps(metadata),
                    encoding="utf-8",
                )
            (frames / "latest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "tethered-frame-manifest/v1",
                        "frame_id": 1,
                        "image_file": "frame_0000000001.jpg",
                        "metadata_file": "frame_0000000001.json",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit) as raised:
                main(
                    [
                        "--runtime",
                        str(runtime),
                        "--tracker",
                        "nanotrack-v2",
                        "--tracker-model-spec",
                        str(DEFAULT_NANOTRACK_V2_SPEC),
                        "--tracker-model-dir",
                        str(DEFAULT_NANOTRACK_V2_MODEL_DIR),
                        "--init-frame",
                        "0",
                        "--init-box",
                        "0.375",
                        "0.375",
                        "0.25",
                        "0.25",
                        "--track-id",
                        "target-0",
                        "--scenario-id",
                        "test-scenario",
                        "--condition",
                        "nadir",
                        "--ground-plane-y-m",
                        "0.0",
                        "--planned-duration-s",
                        "0.2",
                        "--run-id",
                        "nanotrack-cli",
                    ]
                )
            self.assertEqual(raised.exception.code, 0)
            manifest = json.loads(
                (
                    runtime
                    / "runs"
                    / "nanotrack-cli"
                    / "manifest.json"
                ).read_text()
            )
            identity = manifest["tracker"]
            self.assertEqual(identity["name"], "nanotrack-v2")
            self.assertEqual(identity["opencv_version"], "5.0.0")
            self.assertEqual(
                identity["model_sha256"],
                {
                    "backbone": (
                        "530bdd0cd00f19afab79a863e71ba71e3"
                        "312395a5dc9151af675082bdaaa2fc4"
                    ),
                    "neckhead": (
                        "0d8c0637be849f092cc7236cae02e55c"
                        "8b9455ebe37ba50601d6115db4247cd9"
                    ),
                },
            )
            self.assertIsNone(identity["score_threshold"])
            self.assertEqual(identity["threshold_source"], "none")
            self.assertEqual(
                identity["preprocessing_id"],
                "opencv-tracker-nano-5.0.0-default-v1",
            )


if __name__ == "__main__":
    unittest.main()


# --- P1-ENG-ACQ-001 AC-15（§3.8）：常驻载体最小伺服 ------------------------------------


class _PointerTracker:
    """常驻替身：每帧给出指针 track 的框（按帧脚本）；只实现常驻方法集。"""

    name = "pointer-stub"
    backend = "test"
    version = "1"
    mode = "resident"

    def __init__(self, boxes):
        self.boxes = dict(boxes)
        self.steps = []
        self.pointer_calls = []

    def step(self, image, frame_id, metadata):
        self.steps.append(frame_id)

    def pointer_result(self, frame_id):
        self.pointer_calls.append(frame_id)
        box = self.boxes.get(frame_id)
        return TrackerResult(box, True, 0.9, "tracker") if box else TrackerResult.lost("no_pointer")

    def init(self, image, box):  # pragma: no cover
        raise AssertionError("init must not be called on a resident tracker")

    def update(self, image):  # pragma: no cover
        raise AssertionError("update must not be called on a resident tracker")

    def manifest_identity(self):
        return {"name": self.name}


class ResidentServoTests(unittest.TestCase):
    def loop(self, runtime, tracker, max_deg):
        logger = RunLogger(runtime, "servo", {"condition": "follow"})
        publisher = _RecordingPublisher()
        loop = TrackLoop(
            FrameRepository(runtime, image_loader),
            tracker,
            publisher,
            logger,
            track_id="s1-t1",
            condition="follow",
            ground_plane_y_m=0.0,
            maximum_ground_range_m=1000.0,
            planned_duration_s=100.0,
            servo_max_deg_per_frame=max_deg,
        )
        return loop, logger, publisher

    def test_servo_rate_clamp(self):
        """每个处理帧对指针 track 发一次 look_at；相邻指令视线角变化 ≤ ω_max/hz = 6°（合成大偏差）。"""
        from controller.track_loop import los_angle_deg  # noqa: PLC0415

        boxes = {i: (0.45, 0.45, 0.1, 0.1) for i in range(0, 3)}
        boxes.update({i: (0.0, 0.0, 0.1, 0.1) for i in range(3, 12)})  # 目标跳到画面角落（> 6°）
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for frame_id in range(12):
                write_frame(runtime, frame_id)
            tracker = _PointerTracker(boxes)
            loop, logger, publisher = self.loop(runtime, tracker, 6.0)
            try:
                loop.start(0)
                for frame_id in range(1, 12):
                    loop.process_available(frame_id)  # 每次一帧
                loop.process_available(11)
            finally:
                logger.close()
            self.assertEqual(tracker.steps, list(range(12)))
            self.assertEqual(tracker.pointer_calls, list(range(12)))
            points = publisher.look_ats
            self.assertEqual(len(points), 12)  # 每处理帧恰一次
            origin = frame_metadata(0)["camera_position_world_m"]
            angles = [los_angle_deg(origin, a, b) for a, b in zip(points, points[1:])]
            self.assertTrue(all(angle <= 6.0 + 1e-6 for angle in angles), angles)
            self.assertAlmostEqual(max(angles), 6.0, places=4)  # 大偏差时恰在上限
            # 红：不限速时相邻指令跳变 > 6°。
            tracker2 = _PointerTracker(boxes)
            runtime2 = runtime / "unclamped"
            for frame_id in range(12):
                write_frame(runtime2, frame_id)
            loop2, logger2, publisher2 = self.loop(runtime2, tracker2, None)
            try:
                loop2.start(0)
                loop2.process_available(11)
            finally:
                logger2.close()
            jumps = [los_angle_deg(origin, a, b) for a, b in zip(publisher2.look_ats, publisher2.look_ats[1:])]
            self.assertGreater(max(jumps), 6.0)

    def test_batch_publishes_every_processed_frame_and_body_only_latest(self):
        boxes = {i: (0.45, 0.45, 0.1, 0.1) for i in range(6)}
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for frame_id in range(6):
                write_frame(runtime, frame_id)
            tracker = _PointerTracker(boxes)
            loop, logger, publisher = self.loop(runtime, tracker, 6.0)
            try:
                loop.start(0)
                self.assertEqual(loop.process_available(5), 5)
            finally:
                logger.close()
            records, _ = read_frame_records(logger.frames_path)
        self.assertEqual(publisher.observations, list(range(6)))
        self.assertEqual(len(publisher.look_ats), 6)
        self.assertEqual([r["event"] for r in records][:1], ["RESIDENT_START"])

    def test_publish_window_skips_stale_backlog(self):
        boxes = {i: (0.45, 0.45, 0.1, 0.1) for i in range(8)}
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for frame_id in range(8):
                write_frame(runtime, frame_id)
            tracker = _PointerTracker(boxes)
            logger = RunLogger(runtime, "window", {"condition": "follow"})
            publisher = _RecordingPublisher()
            loop = TrackLoop(
                FrameRepository(runtime, image_loader), tracker, publisher, logger,
                track_id="s1-t1", condition="follow", ground_plane_y_m=0.0, maximum_ground_range_m=1000.0,
                planned_duration_s=100.0, resident_publish_window=2, servo_max_deg_per_frame=6.0,
            )
            try:
                loop.start(0)
                loop.process_available(7)
            finally:
                logger.close()
            records, _ = read_frame_records(logger.frames_path)
        self.assertEqual(tracker.steps, list(range(8)))  # 追平逐帧 step
        self.assertEqual(tracker.pointer_calls, list(range(8)))
        self.assertEqual(publisher.observations, [0, 5, 6, 7])  # 只发布 latest − frame_id ≤ 2 的帧
        # AC-15 修订 1：窗口内（指针有效、过门）每帧恰一次 look_at；窗口外旧帧不发令。
        self.assertEqual(publisher.look_at_frames, [0, 5, 6, 7])
        self.assertEqual(len(publisher.look_ats), 4)
        # 窗口外旧帧逐帧显式记录「因窗口外跳过发布」；窗口内帧无跳过原因。
        by_frame = {r["frame_id"]: r for r in records}
        self.assertEqual(sorted(by_frame), list(range(8)))
        for frame_id in range(8):
            record = by_frame[frame_id]
            self.assertEqual(record["resident_publish_window"], 2)
            if frame_id in (1, 2, 3, 4):
                self.assertEqual(record["publish_skip_reason"], "outside_resident_publish_window", frame_id)
                self.assertEqual(record["skipped_count"], 1)
                self.assertFalse(record["published_observation"])
                self.assertFalse(record["published_gimbal_command"])
                self.assertIsNone(record["look_at_world_m"])
            else:
                self.assertIsNone(record["publish_skip_reason"], frame_id)
                self.assertTrue(record["published_gimbal_command"], frame_id)

    def test_servo_baseline_is_last_written_look_at(self):
        """AC-15 修订 1：被发布门拒绝的 look_at 不算已发、不推进限速基准；相邻已发指令视线角变化 ≤ 6°。"""
        from controller.track_loop import los_angle_deg  # noqa: PLC0415

        boxes = {i: (0.45, 0.45, 0.1, 0.1) for i in range(0, 3)}
        boxes.update({i: (0.0, 0.0, 0.1, 0.1) for i in range(3, 10)})
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for frame_id in range(10):
                write_frame(runtime, frame_id)
            tracker = _PointerTracker(boxes)
            logger = RunLogger(runtime, "baseline", {"condition": "follow"})
            publisher = _ReceiptPublisher(reject_look_at_frames={3})
            loop = TrackLoop(
                FrameRepository(runtime, image_loader), tracker, publisher, logger,
                track_id="s1-t1", condition="follow", ground_plane_y_m=0.0, maximum_ground_range_m=1000.0,
                planned_duration_s=100.0, servo_max_deg_per_frame=6.0,
            )
            try:
                loop.start(0)
                for frame_id in range(1, 10):
                    loop.process_available(frame_id)
            finally:
                logger.close()
            records, _ = read_frame_records(logger.frames_path)
        written = [(frame_id, point) for frame_id, point, outcome in publisher.look_at_log if outcome == "WRITTEN"]
        self.assertEqual([frame_id for frame_id, _ in written], [0, 1, 2, 4, 5, 6, 7, 8, 9])
        origin = frame_metadata(0)["camera_position_world_m"]
        angles = [los_angle_deg(origin, a, b) for (_, a), (_, b) in zip(written, written[1:])]
        self.assertTrue(all(angle <= 6.0 + 1e-6 for angle in angles), angles)
        by_frame = {r["frame_id"]: r for r in records}
        self.assertFalse(by_frame[3]["published_gimbal_command"])
        self.assertIsNone(by_frame[3]["look_at_world_m"])
        self.assertTrue(by_frame[4]["published_gimbal_command"])

    def test_initialize_on_resident_tracker_is_protocol_misuse(self):
        from controller.resident_core import ProtocolMisuse  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            write_frame(runtime, 0)
            loop, logger, _ = self.loop(runtime, _PointerTracker({}), 6.0)
            try:
                with self.assertRaises(ProtocolMisuse):
                    loop.initialize(0, (0.4, 0.4, 0.1, 0.1))
            finally:
                logger.close()
            legacy, legacy_logger = make_loop(runtime, RecordingTracker([]))
            try:
                with self.assertRaises(ProtocolMisuse):
                    legacy.start(0)
            finally:
                legacy_logger.close()


class _RecordingPublisher:
    def __init__(self):
        self.look_ats = []
        self.look_at_frames = []
        self.observations = []
        self.holds = 0

    def hold_body(self):
        self.holds += 1

    def set_nadir(self):
        pass

    def observation(self, frame_id, track_id, box_norm, confidence):
        self.observations.append(frame_id)

    def look_at(self, point):
        self.look_ats.append(tuple(point))
        self.look_at_frames.append(self.observations[-1] if self.observations else None)

    def body_command(self, command):
        pass


class _Receipt:
    def __init__(self, channel, outcome):
        self.channel = channel
        self.outcome = outcome


class _ReceiptPublisher(_RecordingPublisher):
    """带收据表的门控发布器替身：指定帧的 look_at 记 `PUBLISH_REJECTED`（不写），其余 `WRITTEN`。"""

    def __init__(self, reject_look_at_frames=()):
        super().__init__()
        self.reject = set(reject_look_at_frames)
        self.receipts = []
        self.look_at_log = []

    def observation(self, frame_id, track_id, box_norm, confidence):
        super().observation(frame_id, track_id, box_norm, confidence)
        self.receipts.append(_Receipt("observation", "WRITTEN"))

    def look_at(self, point):
        frame_id = self.observations[-1]
        outcome = "PUBLISH_REJECTED" if frame_id in self.reject else "WRITTEN"
        self.receipts.append(_Receipt("look_at", outcome))
        self.look_at_log.append((frame_id, tuple(point), outcome))
        if outcome == "WRITTEN":
            super().look_at(point)
            return f"gimbal-{frame_id}"
        return None


class StandoffWiringTests(unittest.TestCase):
    """P1-ENG-FRAME-001 AC-18: ``--body-policy standoff`` wiring and checks."""

    PROJECT = Path(__file__).resolve().parents[1]
    FRAME_CONFIG = PROJECT / "config" / "p1-eng-frame-001-body.json"
    UNTETHERED = PROJECT / "config" / "scenario.untethered.json"
    LEGACY_DEFAULT = PROJECT / "config" / "scenario.default.json"

    def _argv(self, *body: str) -> list[str]:
        return [
            "--tracker", "csrt",
            "--init-frame", "0",
            "--init-box", "0.2", "0.3", "0.25", "0.4",
            "--track-id", "target-0",
            "--scenario-id", "deterministic-loop-untethered",
            "--condition", "follow",
            "--ground-plane-y-m", "0.2",
            "--planned-duration-s", "1.0",
            *body,
        ]

    def test_cli_accepts_standoff_and_has_no_body_defaults(self):
        from controller.track_loop import build_argument_parser

        parser = build_argument_parser()
        args = parser.parse_args(
            self._argv(
                "--body-policy", "standoff",
                "--body-planner-config", str(self.FRAME_CONFIG),
                "--body-scenario-config", str(self.UNTETHERED),
            )
        )
        self.assertEqual(args.body_policy, "standoff")
        defaults = parser.parse_args(self._argv())
        self.assertIsNone(defaults.body_policy)
        self.assertIsNone(defaults.body_planner_config)
        self.assertIsNone(defaults.body_scenario_config)

    def test_cli_rejects_standoff_without_either_config(self):
        for body in (
            ("--body-policy", "standoff"),
            ("--body-policy", "standoff", "--body-planner-config", str(self.FRAME_CONFIG)),
            ("--body-policy", "standoff", "--body-scenario-config", str(self.UNTETHERED)),
            ("--body-planner-config", str(self.FRAME_CONFIG), "--body-scenario-config", str(self.UNTETHERED)),
        ):
            stderr = io.StringIO()
            with self.subTest(body=body), redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    main(self._argv(*body))
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("--body-", stderr.getvalue())

    def _build(self, runtime: Path, scenario: Path, scenario_id: str):
        from controller.track_loop import _build_body_runtime

        return _build_body_runtime(
            self.FRAME_CONFIG,
            scenario,
            "standoff",
            scenario_id=scenario_id,
            ground_plane_y_m=0.2,
            runtime=runtime,
        )

    def test_effective_scenario_consistency_red_green(self):
        import hashlib

        from controller.standoff_planner import StandoffBodyPlanner

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            planner, estimator, expires, identity = self._build(
                runtime, self.UNTETHERED, "deterministic-loop-untethered"
            )
            self.assertIsInstance(planner, StandoffBodyPlanner)
            self.assertEqual(expires, 0.4)
            self.assertEqual(identity["planner"], "standoff-band-v1")
            self.assertEqual(identity["policy"], "standoff")
            self.assertEqual(
                identity["config_sha256"],
                hashlib.sha256(self.FRAME_CONFIG.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                identity["scenario_config_sha256"],
                hashlib.sha256(self.UNTETHERED.read_bytes()).hexdigest(),
            )
            self.assertEqual(identity["effective_scenario_path"], str(self.UNTETHERED))
            config = json.loads(self.FRAME_CONFIG.read_text(encoding="utf-8"))
            self.assertEqual(identity["selected_candidate"], config["selected_candidate"])
            self.assertEqual(identity["params"], config["params"])

            # Red: an ACQ-style override (copy of the legacy default) is present.
            override = runtime / "scenario_config.json"
            override.write_bytes(self.LEGACY_DEFAULT.read_bytes())
            with self.assertRaisesRegex(ValueError, "effective scenario"):
                self._build(runtime, self.UNTETHERED, "deterministic-loop-untethered")
            override.unlink()

            # Red: no override, but the body scenario is the legacy default.
            with self.assertRaisesRegex(ValueError, "effective scenario"):
                self._build(runtime, self.LEGACY_DEFAULT, "deterministic-loop-default")

            # The runtime directory is mandatory for standoff.
            from controller.track_loop import _build_body_runtime

            with self.assertRaises(ValueError):
                _build_body_runtime(
                    self.FRAME_CONFIG,
                    self.UNTETHERED,
                    "standoff",
                    scenario_id="deterministic-loop-untethered",
                    ground_plane_y_m=0.2,
                )

    def test_standoff_scenario_id_and_ground_plane_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                self._build(Path(directory), self.UNTETHERED, "deterministic-loop-default")
            from controller.track_loop import _build_body_runtime

            # AC-22 修订 1 (CLARIFY): a finite explicit calibration is never
            # checked against the route, so only a non-finite one fails closed
            # here (formerly 0.0 was expected to fail against route y = 0.2).
            with self.assertRaises(ValueError):
                _build_body_runtime(
                    self.FRAME_CONFIG,
                    self.UNTETHERED,
                    "standoff",
                    scenario_id="deterministic-loop-untethered",
                    ground_plane_y_m=float("nan"),
                    runtime=Path(directory),
                )

    def test_standoff_ground_plane_is_explicit_finite_and_route_independent(self):
        """AC-22 修订 1 (CLARIFY): the explicit ``ground_plane_y_m`` is the only
        calibration source of the standoff construction path.

        Finite explicit values (0.2 equals the route height, 0.0 does not)
        both construct through the real ``_build_body_runtime``; a missing or
        non-finite value is refused directly and on the CLI, with no default
        and no fill-in from the route or the home height.
        """
        from controller.track_loop import _build_body_runtime

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for ground_plane_y_m in (0.2, 0.0):
                with self.subTest(ground_plane_y_m=ground_plane_y_m):
                    planner, _, expires, identity = _build_body_runtime(
                        self.FRAME_CONFIG,
                        self.UNTETHERED,
                        "standoff",
                        scenario_id="deterministic-loop-untethered",
                        ground_plane_y_m=ground_plane_y_m,
                        runtime=runtime,
                    )
                    self.assertEqual(planner.name, "standoff-band-v1")
                    self.assertEqual(expires, 0.4)
                    self.assertEqual(identity["effective_scenario_path"], str(self.UNTETHERED))
            for ground_plane_y_m in (None, float("nan"), float("inf"), float("-inf")):
                with self.subTest(ground_plane_y_m=ground_plane_y_m):
                    with self.assertRaisesRegex(ValueError, "ground_plane_y_m"):
                        _build_body_runtime(
                            self.FRAME_CONFIG,
                            self.UNTETHERED,
                            "standoff",
                            scenario_id="deterministic-loop-untethered",
                            ground_plane_y_m=ground_plane_y_m,
                            runtime=runtime,
                        )
            self.assertEqual(list(runtime.iterdir()), [])

            base = [
                "--runtime", str(runtime),
                "--tracker", "csrt",
                "--init-frame", "0",
                "--init-box", "0.2", "0.3", "0.25", "0.4",
                "--track-id", "target-0",
                "--scenario-id", "deterministic-loop-untethered",
                "--condition", "follow",
                "--planned-duration-s", "1.0",
                "--body-policy", "standoff",
                "--body-planner-config", str(self.FRAME_CONFIG),
                "--body-scenario-config", str(self.UNTETHERED),
            ]
            for extra in (
                (),
                ("--ground-plane-y-m=nan",),
                ("--ground-plane-y-m=inf",),
                ("--ground-plane-y-m=-inf",),
            ):
                stderr = io.StringIO()
                with self.subTest(cli=extra), redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as raised:
                        main(base + list(extra))
                    self.assertEqual(raised.exception.code, 2)
                    self.assertRegex(stderr.getvalue(), "ground[-_]plane[-_]y[-_]m")
            self.assertEqual(list(runtime.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
