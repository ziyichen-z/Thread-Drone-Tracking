from __future__ import annotations

from collections import deque
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from controller import rate2_protocol, rate3_protocol
from controller.rate2_protocol import (
    IDENTITY_KEYS,
    Rate2ProtocolError,
    atomic_bytes,
    atomic_json,
    canonical_json_bytes,
    identity_hashes,
    sha256_bytes,
    sha256_file,
)
from controller.rate3_protocol import (
    CLOCK_ID,
    CLOCK_SMOKE_PLANNED_DURATION_S,
    CLOCK_SMOKE_RUN_ID,
    CLOCK_SMOKE_STUDY_ID,
    PLANNED_DURATION_S,
    READY_SCHEMA,
    RELEASE_ACK_SCHEMA,
    SENSOR_SCHEMA,
    SESSION_SCHEMA,
    STUDY_ID,
    Rate3TrackerLifecycle,
    archive_release_provenance,
    build_release_command,
    expected_scenario,
    planned_duration_for,
    validate_provenance,
    validate_ready,
    validate_release_bundle,
    validate_session,
)
from controller.run_log import RunLogger, build_summary, finalize_run, read_frame_records
from controller.track_loop import FrameRepository, RuntimePublisher, TrackLoop, main
from controller.trackers import (
    DEFAULT_NANOTRACK_V2_MODEL_DIR,
    DEFAULT_NANOTRACK_V2_SPEC,
    TrackerResult,
)
from controller.reanchor_runtime import ReanchorRuntime
from controller.reanchor import load_reanchor_config
from tools import run_rate3_clock_smoke as clock_smoke
from tools.run_rate2_study import attempt_row, validate_decision_a


def tracker_identity():
    return {
        "name": "nanotrack-v2",
        "backend": "test",
        "pinned_version": "5.0.0",
        "model_sha256": {"backbone": "a" * 64, "neckhead": "b" * 64},
        "score_threshold": None,
        "threshold_source": "none",
        "preprocessing_id": "test",
    }


def session(run_id=CLOCK_SMOKE_RUN_ID, study_id=CLOCK_SMOKE_STUDY_ID, **overrides):
    tracker_hash, model_hash = identity_hashes(tracker_identity())
    value = {
        "schema_version": SESSION_SCHEMA,
        "study_id": study_id,
        "run_id": run_id,
        "scenario_id": expected_scenario(run_id, study_id),
        "tracker_id": "nanotrack-v2",
        "tracker_identity_sha256": tracker_hash,
        "model_identity_sha256": model_hash,
        "init_frame_id": 0,
        "init_image_sha256": "c" * 64,
        "hold_route_s_m": 2.5,
        "minimum_ready_seq": 20,
        "minimum_processed_frames": 20,
        "planned_duration_s": planned_duration_for(study_id),
        "sensor_frame_schema": SENSOR_SCHEMA,
        "capture_monotonic_clock_id": CLOCK_ID,
    }
    value.update(overrides)
    return validate_session(value)


def ready_document(value, *, frame_id=20, seq=20, published=100.0):
    return {
        "schema_version": READY_SCHEMA,
        "state": "TRACKING",
        **{key: value[key] for key in IDENTITY_KEYS},
        "last_processed_frame_id": frame_id,
        "processed_frame_count": seq,
        "seq": seq,
        "publisher_monotonic_s": published,
        "publisher_clock_id": CLOCK_ID,
        "heartbeat_interval_s": 1.0,
    }


def ack_document(
    value,
    command_bytes,
    *,
    release_frame=20,
    release_mono=500.0,
    release_simulation=10.0,
):
    command = json.loads(command_bytes)
    ready_bytes = base64.b64decode(command["ready_json_base64"])
    ready = json.loads(ready_bytes)
    return {
        "schema_version": RELEASE_ACK_SCHEMA,
        "command_id": command["command_id"],
        **{key: value[key] for key in IDENTITY_KEYS},
        "release_clock_id": CLOCK_ID,
        "release_command_sha256": sha256_bytes(command_bytes),
        "ready_sha256": sha256_bytes(ready_bytes),
        "ready_seq": ready["seq"],
        "processed_frame_count": ready["processed_frame_count"],
        "current_frame_id": release_frame,
        "last_processed_frame_id": ready["last_processed_frame_id"],
        "accepted_backlog_frames": release_frame - ready["last_processed_frame_id"],
        "release_frame_id": release_frame,
        "release_unix_s": 1_800_000_000.0,
        "release_monotonic_s": release_mono,
        "release_simulation_s": release_simulation,
    }


def write_latest(runtime, frame_id):
    atomic_json(
        runtime / "frames" / "latest.json",
        {
            "schema_version": "tethered-frame-manifest/v1",
            "frame_id": frame_id,
            "image_file": f"frame_{frame_id:010d}.jpg",
            "metadata_file": f"frame_{frame_id:010d}.json",
        },
    )


def write_frame(
    runtime,
    frame_id,
    *,
    schema="tethered-sensor-frame/v3",
    clock_id=CLOCK_ID,
    scenario_id="p1-scene-004",
    capture_monotonic_s=None,
):
    frames = runtime / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    stem = f"frame_{frame_id:010d}"
    image = frames / f"{stem}.jpg"
    image.write_bytes(b"image-" + str(frame_id).encode())
    metadata = {
        "schema_version": schema,
        "scenario_id": scenario_id,
        "frame_id": frame_id,
        "simulation_time_s": 7.0 + frame_id * 0.05,
        "capture_unix_s": 1_800_000_000.0 + frame_id * 0.05,
        "capture_monotonic_s": (
            499.0 + frame_id * 0.05
            if capture_monotonic_s is None
            else capture_monotonic_s
        ),
        "capture_monotonic_clock_id": clock_id,
        "camera_position_world_m": [0.0, 10.0, 0.0],
        "camera_forward_world": [0.0, -1.0, 0.0],
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
    atomic_json(frames / f"{stem}.json", metadata)
    return image


def install_session(runtime, value):
    atomic_json(runtime / "rate_study_session.json", value)


def make_release_chain(runtime, value, *, release_mono=500.0, release_frame=20):
    ready_bytes = canonical_json_bytes(ready_document(value))
    command_bytes = build_release_command(
        value, ready_bytes, command_id=f"release-{value['run_id']}"
    )
    ack_bytes = canonical_json_bytes(
        ack_document(value, command_bytes, release_mono=release_mono,
                     release_frame=release_frame)
    )
    atomic_bytes(runtime / "release_command.accepted.json", command_bytes)
    atomic_bytes(runtime / "release_ack.json", ack_bytes)
    return command_bytes, ack_bytes


def make_run_directory(runtime, value, *, planned=None):
    run_directory = runtime / "runs" / value["run_id"]
    run_directory.mkdir(parents=True)
    atomic_json(
        run_directory / "manifest.json",
        {
            "schema_version": "p1-track-run/v1",
            "run_id": value["run_id"],
            "scenario_id": value["scenario_id"],
            "condition": "follow",
            "planned_duration_s": (
                planned
                if planned is not None
                else planned_duration_for(value["study_id"])
            ),
            "rate3": {
                key: value[key]
                for key in (
                    *IDENTITY_KEYS,
                    "hold_route_s_m",
                    "planned_duration_s",
                    "sensor_frame_schema",
                    "capture_monotonic_clock_id",
                )
            },
        },
    )
    return run_directory


class RecordingTracker:
    name = "nanotrack-v2"
    backend = "test"
    version = "5.0.0"

    def __init__(self, count=8):
        self.results = deque(
            [TrackerResult((0.4, 0.3, 0.2, 0.2), True, 1.0, "tracker")] * count
        )

    def init(self, image, box):
        return True

    def update(self, image):
        return self.results.popleft()

    def manifest_identity(self):
        return tracker_identity()


class Rate3SessionTests(unittest.TestCase):
    def test_clock_smoke_and_b1_sessions_validate(self):
        smoke = session()
        self.assertEqual(smoke["scenario_id"], "p1-scene-004")
        self.assertEqual(smoke["planned_duration_s"], 30.0)
        for run_id, scenario in (
            ("rs3-probe-d2", "p1-scene-004-d2"),
            # BC-DRB-4: six per-phase HOLD calibration slots replace the two
            # per-difficulty slots frozen by revision 3.
            ("rs3-d1-p1-calib", "p1-scene-004"),
            ("rs3-d2-p3-calib", "p1-scene-004-d2"),
            ("rs3-d1-p1-r5", "p1-scene-004"),
            ("rs3-d2-p3-r20", "p1-scene-004-d2"),
            ("rs3-d1-p2-r20", "p1-scene-004"),
        ):
            value = session(run_id, STUDY_ID)
            self.assertEqual(value["scenario_id"], scenario)
            self.assertEqual(value["planned_duration_s"], 150.0)

    def test_study_run_cross_pairing_fails_closed(self):
        with self.assertRaises(Rate2ProtocolError):
            session("rs3-d1-p1-r5", CLOCK_SMOKE_STUDY_ID)
        with self.assertRaises(Rate2ProtocolError):
            session(CLOCK_SMOKE_RUN_ID, STUDY_ID)
        with self.assertRaises(Rate2ProtocolError):
            session("rs3-unknown", STUDY_ID)
        # The superseded revision-3 calibration identities must not survive.
        with self.assertRaises(Rate2ProtocolError):
            session("rs3-d1-calib", STUDY_ID)
        with self.assertRaises(Rate2ProtocolError):
            session("rs3-d2-calib", STUDY_ID)
        with self.assertRaises(Rate2ProtocolError):
            session("rs3-clock-smoke", "P1-M2-RATE-002-B2")

    def test_planned_duration_and_clock_fields_are_frozen(self):
        with self.assertRaisesRegex(Rate2ProtocolError, "planned_duration_s"):
            session(planned_duration_s=150.0)
        with self.assertRaisesRegex(Rate2ProtocolError, "planned_duration_s"):
            session("rs3-d1-p1-r5", STUDY_ID, planned_duration_s=30.0)
        with self.assertRaisesRegex(Rate2ProtocolError, "planned_duration_s"):
            session("rs3-d1-p1-r5", STUDY_ID, planned_duration_s=150.0 + 1e-6)
        with self.assertRaisesRegex(Rate2ProtocolError, "sensor_frame_schema"):
            session(sensor_frame_schema="tethered-sensor-frame/v2")
        with self.assertRaisesRegex(Rate2ProtocolError, "INVALID_CLOCK_IDENTITY"):
            session(capture_monotonic_clock_id="unity-process-relative/v1")

    def test_scenario_mismatch_and_identity_fields_fail(self):
        with self.assertRaisesRegex(Rate2ProtocolError, "identity mismatch"):
            session("rs3-d2-p1-r5", STUDY_ID, scenario_id="p1-scene-004")
        for key, invalid in (
            ("tracker_id", "csrt"),
            ("tracker_identity_sha256", "not-a-hash"),
            ("minimum_ready_seq", 19),
            ("minimum_processed_frames", 21),
        ):
            with self.subTest(key=key), self.assertRaises(Rate2ProtocolError):
                session(**{key: invalid})


class Rate3ReadyTests(unittest.TestCase):
    def test_publisher_clock_id_is_mandatory(self):
        value = session()
        document = ready_document(value)
        self.assertEqual(validate_ready(document, value)["seq"], 20)
        missing = {key: item for key, item in document.items() if key != "publisher_clock_id"}
        with self.assertRaisesRegex(Rate2ProtocolError, "INVALID_CLOCK_IDENTITY"):
            validate_ready(missing, value)
        wrong = dict(document, publisher_clock_id="unity-process-relative/v1")
        with self.assertRaisesRegex(Rate2ProtocolError, "INVALID_CLOCK_IDENTITY"):
            validate_ready(wrong, value)

    def test_freshness_window_and_heartbeat_interval(self):
        value = session()
        document = ready_document(value)
        for now in (100.0, 101.0, 102.0):
            validate_ready(document, value, now_monotonic_s=now)
        with self.assertRaisesRegex(Rate2ProtocolError, "future"):
            validate_ready(document, value, now_monotonic_s=99.999)
        with self.assertRaisesRegex(Rate2ProtocolError, "stale"):
            validate_ready(document, value, now_monotonic_s=102.001)
        with self.assertRaisesRegex(Rate2ProtocolError, "exceeds 1 s"):
            validate_ready(dict(document, heartbeat_interval_s=2.0), value)
        with self.assertRaisesRegex(Rate2ProtocolError, "exceeds 1 s"):
            validate_ready(dict(document, heartbeat_interval_s=0.0), value)

    def test_minimum_warmup(self):
        value = session()
        document = ready_document(value, seq=19)
        with self.assertRaisesRegex(Rate2ProtocolError, "warm-up"):
            validate_ready(document, value)
        validate_ready(document, value, require_minimum=False)


class Rate3ReleaseBundleTests(unittest.TestCase):
    def test_release_clock_id_on_command_and_ack(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = session()
            ready_bytes = canonical_json_bytes(ready_document(value))
            command_bytes = build_release_command(
                value, ready_bytes, command_id="release-1"
            )
            ack_bytes = canonical_json_bytes(ack_document(value, command_bytes))
            ack = validate_release_bundle(command_bytes, ack_bytes, value)
            self.assertEqual(ack["release_clock_id"], CLOCK_ID)
            command = json.loads(command_bytes)
            self.assertEqual(command["release_clock_id"], CLOCK_ID)
            bad_command = dict(command, release_clock_id="unity-process-relative/v1")
            with self.assertRaisesRegex(Rate2ProtocolError, "INVALID_CLOCK_IDENTITY"):
                validate_release_bundle(
                    canonical_json_bytes(bad_command), ack_bytes, value
                )
            bad_ack = dict(json.loads(ack_bytes), release_clock_id=None)
            with self.assertRaisesRegex(Rate2ProtocolError, "INVALID_CLOCK_IDENTITY"):
                validate_release_bundle(
                    command_bytes, canonical_json_bytes(bad_ack), value
                )

    def test_hash_chain_and_backlog_match_rate2_behavior(self):
        value = session()
        ready_bytes = canonical_json_bytes(ready_document(value))
        command_bytes = build_release_command(
            value, ready_bytes, command_id="release-1"
        )
        ack_bytes = canonical_json_bytes(ack_document(value, command_bytes))
        validate_release_bundle(command_bytes, ack_bytes, value)
        with self.assertRaisesRegex(Rate2ProtocolError, "command hash mismatch"):
            validate_release_bundle(command_bytes + b" ", ack_bytes, value)
        bad_ack = dict(json.loads(ack_bytes), accepted_backlog_frames=7)
        with self.assertRaisesRegex(Rate2ProtocolError, "backlog"):
            validate_release_bundle(
                command_bytes, canonical_json_bytes(bad_ack), value
            )
        mismatched = dict(json.loads(ack_bytes), ready_seq=21)
        with self.assertRaisesRegex(Rate2ProtocolError, "does not match ready"):
            validate_release_bundle(
                command_bytes, canonical_json_bytes(mismatched), value
            )


class Rate3ProvenanceTests(unittest.TestCase):
    def test_provenance_round_trip_binds_release_clock_id(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = session()
            run_directory = make_run_directory(runtime, value)
            make_release_chain(runtime, value)
            provenance = archive_release_provenance(runtime, run_directory, value)
            self.assertEqual(provenance["release_clock_id"], CLOCK_ID)
            again = archive_release_provenance(runtime, run_directory, value)
            self.assertEqual(provenance, again)
            validated = validate_provenance(run_directory)
            self.assertEqual(validated["release_clock_id"], CLOCK_ID)
            self.assertEqual(
                validated["command_id"], f"release-{value['run_id']}"
            )
            ack_path = run_directory / "release-ack.json"
            ack_path.write_bytes(ack_path.read_bytes() + b" ")
            with self.assertRaises(Rate2ProtocolError):
                validate_provenance(run_directory)


class Rate3LifecycleTests(unittest.TestCase):
    def make_lifecycle(self, runtime, value, **kwargs):
        options = {
            "init_frame_id": value["init_frame_id"],
            "init_image_sha256": value["init_image_sha256"],
            "scenario_id": value["scenario_id"],
            "run_id": value["run_id"],
            "monotonic": lambda: 100.0,
            "monotonic_clock_id": CLOCK_ID,
        }
        options.update(kwargs)
        return Rate3TrackerLifecycle(
            runtime, value, tracker_identity(), **options
        )

    def test_publish_ready_declares_clock_and_interval(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = session()
            lifecycle = self.make_lifecycle(runtime, value)
            lifecycle.publish_ready(0, "TRACKING")
            ready = json.loads((runtime / "tracker_ready.json").read_text())
            self.assertEqual(ready["publisher_clock_id"], CLOCK_ID)
            self.assertEqual(ready["heartbeat_interval_s"], 1.0)
            self.assertEqual(ready["schema_version"], READY_SCHEMA)
            self.assertEqual(ready["publisher_monotonic_s"], 100.0)

    def test_non_default_monotonic_requires_explicit_clock_declaration(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = session()
            with self.assertRaisesRegex(ValueError, "monotonic_clock_id"):
                self.make_lifecycle(runtime, value, monotonic_clock_id=None)
            with self.assertRaisesRegex(ValueError, "monotonic_clock_id"):
                self.make_lifecycle(
                    runtime, value, monotonic_clock_id="wrong-clock/v9"
                )
            lifecycle = self.make_lifecycle(runtime, value)
            self.assertEqual(lifecycle.monotonic_clock_id, CLOCK_ID)
            default = Rate3TrackerLifecycle(
                runtime,
                value,
                tracker_identity(),
                init_frame_id=value["init_frame_id"],
                init_image_sha256=value["init_image_sha256"],
                scenario_id=value["scenario_id"],
                run_id=value["run_id"],
            )
            self.assertEqual(default.monotonic_clock_id, CLOCK_ID)
            self.assertTrue(Rate3TrackerLifecycle.requires_wall_completion)

    def test_frame_phase_switches_and_enforces_clock_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = session()
            make_release_chain(runtime, value, release_mono=499.025)
            lifecycle = self.make_lifecycle(runtime, value)
            self.assertEqual(
                lifecycle.frame_phase({"capture_monotonic_s": 600.0}), "hold"
            )
            ack = lifecycle.poll_release_ack()
            self.assertIsNotNone(ack)
            self.assertEqual(lifecycle.phase, "measurement")
            self.assertIs(lifecycle.poll_release_ack(), ack)
            before = {
                "capture_monotonic_s": 499.0,
                "capture_monotonic_clock_id": CLOCK_ID,
                "simulation_time_s": 7.0,
            }
            after = {
                "capture_monotonic_s": 499.05,
                "capture_monotonic_clock_id": CLOCK_ID,
                "simulation_time_s": 10.05,
            }
            self.assertEqual(lifecycle.frame_phase(before), "hold")
            self.assertEqual(lifecycle.frame_phase(after), "measurement")
            wrong_clock = dict(after, capture_monotonic_clock_id="other/v1")
            with self.assertRaisesRegex(Rate2ProtocolError, "INVALID_CLOCK_IDENTITY"):
                lifecycle.frame_phase(wrong_clock)

    def test_record_fields_reports_simulation_and_wall_elapsed(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = session()
            make_release_chain(
                runtime, value, release_mono=499.025, release_frame=20
            )
            lifecycle = self.make_lifecycle(runtime, value)
            hold_fields = lifecycle.record_fields(
                {
                    "capture_monotonic_s": 498.0,
                    "capture_monotonic_clock_id": CLOCK_ID,
                    "simulation_time_s": 6.0,
                }
            )
            self.assertEqual(hold_fields["phase"], "hold")
            self.assertIsNone(hold_fields["measurement_elapsed_s"])
            self.assertIsNone(hold_fields["measurement_wall_elapsed_s"])
            self.assertEqual(hold_fields["capture_monotonic_clock_id"], CLOCK_ID)
            lifecycle.poll_release_ack()
            fields = lifecycle.record_fields(
                {
                    "capture_monotonic_s": 499.075,
                    "capture_monotonic_clock_id": CLOCK_ID,
                    "simulation_time_s": 10.075,
                }
            )
            self.assertEqual(fields["phase"], "measurement")
            self.assertAlmostEqual(fields["measurement_elapsed_s"], 0.075)
            self.assertAlmostEqual(fields["measurement_wall_elapsed_s"], 0.05)


class Rate3VersionRoutingTests(unittest.TestCase):
    def rate2_session(self):
        tracker_hash, model_hash = identity_hashes(tracker_identity())
        return rate2_protocol.validate_session(
            {
                "schema_version": rate2_protocol.SESSION_SCHEMA,
                "study_id": rate2_protocol.STUDY_ID,
                "run_id": "rs2-pilot",
                "scenario_id": "rate-study-20hz",
                "tracker_id": "nanotrack-v2",
                "tracker_identity_sha256": tracker_hash,
                "model_identity_sha256": model_hash,
                "init_frame_id": 0,
                "init_image_sha256": "c" * 64,
                "hold_route_s_m": 2.5,
                "minimum_ready_seq": 20,
                "minimum_processed_frames": 20,
            }
        )

    def test_sessions_reject_cross_versions(self):
        v3 = session()
        v2 = self.rate2_session()
        with self.assertRaises(Rate2ProtocolError):
            validate_session(v2)
        with self.assertRaises(Rate2ProtocolError):
            rate2_protocol.validate_session(v3)

    def test_ready_rejects_cross_versions(self):
        v3_session = session()
        v2_session = self.rate2_session()
        v3_ready = ready_document(v3_session)
        v2_ready = {
            key: item
            for key, item in v3_ready.items()
            if key != "publisher_clock_id"
        }
        v2_ready["schema_version"] = rate2_protocol.READY_SCHEMA
        v2_ready.update({key: v2_session[key] for key in IDENTITY_KEYS})
        rate2_protocol.validate_ready(v2_ready, v2_session)
        with self.assertRaises(Rate2ProtocolError):
            validate_ready(v2_ready, v2_session)
        with self.assertRaises(Rate2ProtocolError):
            rate2_protocol.validate_ready(v3_ready, v3_session)

    def test_release_bundles_reject_cross_versions(self):
        v3_session = session()
        v2_session = self.rate2_session()
        v3_ready_bytes = canonical_json_bytes(ready_document(v3_session))
        v3_command = build_release_command(
            v3_session, v3_ready_bytes, command_id="cross-3"
        )
        v3_ack = canonical_json_bytes(ack_document(v3_session, v3_command))
        with self.assertRaises(Rate2ProtocolError):
            rate2_protocol.validate_release_bundle(v3_command, v3_ack, v2_session)
        v2_ready = {
            "schema_version": rate2_protocol.READY_SCHEMA,
            "state": "TRACKING",
            **{key: v2_session[key] for key in IDENTITY_KEYS},
            "last_processed_frame_id": 20,
            "processed_frame_count": 20,
            "seq": 20,
            "publisher_monotonic_s": 100.0,
            "heartbeat_interval_s": 1.0,
        }
        v2_ready_bytes = canonical_json_bytes(v2_ready)
        v2_command = rate2_protocol.build_release_command(
            v2_session, v2_ready_bytes, command_id="cross-2"
        )
        v2_command_value = json.loads(v2_command)
        v2_ack = canonical_json_bytes(
            {
                "schema_version": rate2_protocol.RELEASE_ACK_SCHEMA,
                "command_id": "cross-2",
                **{key: v2_session[key] for key in IDENTITY_KEYS},
                "release_command_sha256": sha256_bytes(v2_command),
                "ready_sha256": v2_command_value["ready_sha256"],
                "ready_seq": 20,
                "processed_frame_count": 20,
                "current_frame_id": 20,
                "last_processed_frame_id": 20,
                "accepted_backlog_frames": 0,
                "release_frame_id": 20,
                "release_unix_s": 1_800_000_000.0,
                "release_monotonic_s": 500.0,
                "release_simulation_s": 10.0,
            }
        )
        rate2_protocol.validate_release_bundle(v2_command, v2_ack, v2_session)
        with self.assertRaises(Rate2ProtocolError):
            validate_release_bundle(v2_command, v2_ack, v3_session)

    def test_frame_repository_rejects_cross_schema_frames(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            write_frame(runtime, 0, schema="tethered-sensor-frame/v2")
            write_frame(runtime, 1)
            loader = lambda path: path.name
            repository_v3 = FrameRepository(
                runtime,
                image_loader=loader,
                expected_frame_schema="tethered-sensor-frame/v3",
            )
            repository_v2 = FrameRepository(
                runtime,
                image_loader=loader,
                expected_frame_schema="tethered-sensor-frame/v2",
            )
            self.assertEqual(repository_v3.load(1).frame_id, 1)
            self.assertEqual(repository_v2.load(0).frame_id, 0)
            with self.assertRaisesRegex(ValueError, "unsupported schema"):
                repository_v3.load(0)
            with self.assertRaisesRegex(ValueError, "unsupported schema"):
                repository_v2.load(1)


class Rate3TrackLoopTests(unittest.TestCase):
    def make_loop(self, runtime, value, lifecycle, tracker=None):
        logger = RunLogger(runtime, value["run_id"], {"condition": "follow"})
        loop = TrackLoop(
            FrameRepository(
                runtime,
                image_loader=lambda path: path,
                expected_frame_schema=value["sensor_frame_schema"],
            ),
            tracker or RecordingTracker(),
            RuntimePublisher(runtime, 1.0),
            logger,
            track_id="target-0",
            condition="follow",
            ground_plane_y_m=0.0,
            maximum_ground_range_m=1000.0,
            planned_duration_s=value["planned_duration_s"],
            rate3_lifecycle=lifecycle,
        )
        return loop, logger

    def test_bad_clock_frame_terminates_run_without_side_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            init_image = write_frame(runtime, 0)
            write_frame(runtime, 1)
            write_frame(runtime, 2)
            value = session(init_image_sha256=sha256_file(init_image))
            lifecycle = Rate3TrackerLifecycle(
                runtime,
                value,
                tracker_identity(),
                init_frame_id=0,
                init_image_sha256=value["init_image_sha256"],
                scenario_id=value["scenario_id"],
                run_id=value["run_id"],
                monotonic=lambda: 100.0,
                monotonic_clock_id=CLOCK_ID,
            )
            loop, logger = self.make_loop(runtime, value, lifecycle)
            try:
                loop.initialize(0, (0.4, 0.3, 0.2, 0.2))
                self.assertEqual(loop.process_available(2), 2)
                self.assertFalse(loop.terminal)
                write_frame(
                    runtime,
                    3,
                    clock_id="unity-process-relative/v1",
                )
                self.assertEqual(loop.process_available(3), 0)
                self.assertTrue(loop.terminal)
                self.assertTrue(loop.complete)
                records, _ = read_frame_records(logger.frames_path)
                frame_records = [
                    record
                    for record in records
                    if record.get("record_kind", "frame") == "frame"
                ]
                self.assertEqual(
                    [record["frame_id"] for record in frame_records],
                    [0, 1, 2, 3],
                )
                terminal = frame_records[-1]
                self.assertEqual(terminal["event"], "INVALID_CLOCK")
                self.assertEqual(terminal["state"], "ERROR_REINIT_REQUIRED")
                self.assertIn("capture_monotonic_clock_id", terminal["reason"])
                self.assertFalse(terminal["published_observation"])
                self.assertIsNone(terminal["box_norm"])
                for record in frame_records[:3]:
                    self.assertEqual(record["state"], "TRACKING")
                    self.assertEqual(record["phase"], "hold")
                heartbeat = json.loads(
                    (runtime / "tracker_ready.json").read_text()
                )
                self.assertEqual(heartbeat["last_processed_frame_id"], 2)
            finally:
                logger.close()

    def test_session_validation_precedes_run_directory_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            write_frame(runtime, 0)
            invalid = session(planned_duration_s=30.0)
            invalid["planned_duration_s"] = 31.0
            atomic_json(runtime / "rate_study_session.json", invalid)
            with patch("controller.track_loop.create_tracker") as create:
                with self.assertRaisesRegex(ValueError, "planned_duration_s"):
                    main(
                        [
                            "--runtime",
                            str(runtime),
                            "--tracker",
                            "nanotrack-v2",
                            "--rate3-session",
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
                            "30.0",
                            "--run-id",
                            "rs3-clock-smoke",
                        ]
                    )
                create.assert_not_called()
            self.assertFalse((runtime / "runs").exists())

    def test_cli_planned_duration_must_match_frozen_session_value(self):
        # Review round 1 finding 1 (BC-R3-1): a mismatched CLI duration must
        # fail before model construction and before any run side effect.
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            install_session(runtime, session())
            with patch("controller.track_loop.create_tracker") as create:
                with self.assertRaisesRegex(
                    ValueError, "frozen planned_duration_s"
                ):
                    main(
                        [
                            "--runtime",
                            str(runtime),
                            "--tracker",
                            "nanotrack-v2",
                            "--rate3-session",
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
                            "60.0",
                            "--run-id",
                            "rs3-clock-smoke",
                        ]
                    )
                create.assert_not_called()
            self.assertFalse((runtime / "runs").exists())


class Rate3GuardTests(unittest.TestCase):
    def base_args(self, runtime):
        return [
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
            "p1-scene-004",
            "--condition",
            "follow",
            "--ground-plane-y-m",
            "0.0",
            "--planned-duration-s",
            "30.0",
            "--run-id",
            "rs3-clock-smoke",
        ]

    def test_rate2_reanchor_guard_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            with patch("controller.track_loop.create_tracker") as create:
                with self.assertRaisesRegex(ValueError, "incompatible with the RATE-002"):
                    main(
                        self.base_args(runtime)
                        + ["--rate2-session", "--reanchor-config", "unused.json"]
                    )
                create.assert_not_called()
            self.assertFalse((runtime / "runs").exists())

    def test_rate3_reanchor_combination_is_not_guarded_out(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            with self.assertRaises(FileNotFoundError):
                main(
                    self.base_args(runtime)
                    + ["--rate3-session", "--reanchor-config", "unused.json"]
                )
            self.assertFalse((runtime / "runs").exists())

    def test_rate2_and_rate3_sessions_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            with self.assertRaises(SystemExit):
                main(
                    self.base_args(runtime) + ["--rate2-session", "--rate3-session"]
                )
            self.assertFalse((runtime / "runs").exists())

    def test_rate3_reanchor_clock_mismatch_raises_defensively(self):
        import cv2
        import numpy as np

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            init_image = write_frame(runtime, 0)
            self.assertTrue(
                cv2.imwrite(
                    str(init_image),
                    np.zeros((100, 200, 3), dtype=np.uint8),
                )
            )
            value = session(init_image_sha256=sha256_file(init_image))
            install_session(runtime, value)

            class FakeConfig:
                tracker_factory = {
                    "spec": str(DEFAULT_NANOTRACK_V2_SPEC),
                    "model_dir": str(DEFAULT_NANOTRACK_V2_MODEL_DIR),
                }

            class WrongClockReanchor:
                def __init__(self, *args, **kwargs):
                    self.monotonic_clock_id = "unity-process-relative/v1"

            with (
                patch(
                    "controller.track_loop.create_tracker",
                    return_value=RecordingTracker(),
                ),
                patch(
                    "controller.track_loop.load_reanchor_config",
                    return_value=FakeConfig(),
                ),
                patch(
                    "controller.reanchor_runtime.ReanchorRuntime",
                    WrongClockReanchor,
                ),
            ):
                with self.assertRaisesRegex(ValueError, "clock identity"):
                    main(
                        self.base_args(runtime)
                        + ["--rate3-session", "--reanchor-config", "fake.json"]
                    )
            self.assertFalse((runtime / "runs").exists())


class Rate3RunLogTests(unittest.TestCase):
    def measurement_records(self, clock_id=CLOCK_ID):
        return [
            {
                "frame_id": 1,
                "phase": "measurement",
                "simulation_time_s": 10.1,
                "capture_unix_s": 1_800_000_000.1,
                "capture_monotonic_s": 500.1,
                "capture_monotonic_clock_id": clock_id,
                "measurement_elapsed_s": 0.1,
                "state": "TRACKING",
                "event": None,
                "compute_stage": "update",
                "compute_latency_ms": 5.0,
                "backlog_count": 0,
            },
            {
                "frame_id": 2,
                "phase": "measurement",
                "simulation_time_s": 10.2,
                "capture_unix_s": 1_800_000_000.2,
                "capture_monotonic_s": 500.2,
                "capture_monotonic_clock_id": clock_id,
                "measurement_elapsed_s": 0.2,
                "state": "TRACKING",
                "event": None,
                "compute_stage": "update",
                "compute_latency_ms": 5.0,
                "backlog_count": 0,
            },
        ]

    def test_build_summary_release_clock_id(self):
        summary = build_summary(
            self.measurement_records(),
            0,
            release_monotonic_s=500.0,
            release_clock_id=CLOCK_ID,
        )
        self.assertEqual(summary["release_clock_id"], CLOCK_ID)
        with self.assertRaisesRegex(ValueError, "INVALID_CLOCK_IDENTITY"):
            build_summary(
                self.measurement_records(clock_id="unity-process-relative/v1"),
                0,
                release_monotonic_s=500.0,
                release_clock_id=CLOCK_ID,
            )
        legacy = build_summary(
            self.measurement_records(),
            0,
            release_monotonic_s=500.0,
        )
        self.assertIsNone(legacy["release_clock_id"])

    def test_finalize_run_routes_rate3_provenance_and_clock(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = session()
            run_directory = make_run_directory(runtime, value)
            make_release_chain(runtime, value)
            archive_release_provenance(runtime, run_directory, value)
            with (run_directory / "frames.jsonl").open("w") as handle:
                for record in self.measurement_records():
                    handle.write(json.dumps(record, sort_keys=True) + "\n")
            _, summary = finalize_run(runtime, value["run_id"])
            self.assertEqual(summary["release_clock_id"], CLOCK_ID)
            self.assertEqual(summary["release_monotonic_s"], 500.0)
            self.assertTrue(
                summary["monotonic_capture_cadence_post_release"][
                    "strictly_increasing"
                ]
            )

    def test_finalize_run_rejects_multiple_release_protocols(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = session()
            run_directory = make_run_directory(runtime, value)
            manifest_path = run_directory / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["rate2"] = {"study_id": "P1-M2-RATE-002-B2"}
            atomic_json(manifest_path, manifest)
            (run_directory / "frames.jsonl").write_text("")
            with self.assertRaisesRegex(ValueError, "INVALID_RELEASE"):
                finalize_run(runtime, value["run_id"])


class ReanchorClockBindingTests(unittest.TestCase):
    def make_runtime(self, **kwargs):
        config = load_reanchor_config()
        options = {
            "proposer": object(),
            "embedder": object(),
        }
        options.update(kwargs)
        return ReanchorRuntime(config, lambda: RecordingTracker(), **options)

    def test_non_default_monotonic_requires_clock_declaration(self):
        with self.assertRaisesRegex(ValueError, "monotonic_clock_id"):
            self.make_runtime(monotonic=lambda: 0.0)
        with self.assertRaisesRegex(ValueError, "monotonic_clock_id"):
            self.make_runtime(
                monotonic=lambda: 0.0,
                monotonic_clock_id="wrong-clock/v9",
            )
        runtime = self.make_runtime(
            monotonic=lambda: 0.0,
            monotonic_clock_id=CLOCK_ID,
        )
        self.assertEqual(runtime.monotonic_clock_id, CLOCK_ID)

    def test_default_monotonic_declares_system_stopwatch(self):
        runtime = self.make_runtime()
        self.assertEqual(runtime.monotonic_clock_id, "system-stopwatch/v1")
        identity = runtime.manifest_identity()
        self.assertEqual(identity["monotonic_clock_id"], "system-stopwatch/v1")
        self.assertIn("config_sha256", identity)


class Rate2ArchiveRegressionTests(unittest.TestCase):
    @unittest.skipUnless(
        Path("runtime/rate-study/P1-M2-RATE-002-B2/decision_a.json").is_file(),
        "archived RATE-002 artifacts are not present on this machine",
    )
    def test_archived_decision_a_recomputes_identically(self):
        runtime = Path("runtime")
        decision = validate_decision_a(runtime)
        self.assertEqual(
            decision["rules"]["R1_prime"]["value"], 0.2496313750743866
        )
        self.assertEqual(
            decision["rules"]["R2_prime"]["value"], 0.8475073313782991
        )
        stable_fields = (
            "c_track_given_geom",
            "matched_tracking_observations",
            "incorrect_tracking_observations",
            "incorrect_over_matched",
            "time_to_first_lost_s",
            "time_to_first_lost_right_censored",
            "planned_duration_s",
        )
        for row in decision["runs"]:
            current = attempt_row(runtime / "runs" / row["run_id"])
            for key in stable_fields:
                self.assertEqual(row[key], current[key], f"{row['run_id']}:{key}")


class ClockSmokeToolTests(unittest.TestCase):
    def build_session(self, **overrides):
        options = {
            "init_frame_id": 0,
            "init_image_sha256": "c" * 64,
            "hold_route_s_m": 2.5,
            "tracker_identity": tracker_identity(),
        }
        options.update(overrides)
        return clock_smoke.build_clock_smoke_session(**options)

    def test_prepare_session_create_once_and_rejects_stale_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = self.build_session()
            prepared = clock_smoke.prepare_session(runtime, value)
            self.assertEqual(prepared, value)
            self.assertEqual(clock_smoke.prepare_session(runtime, value), value)
            changed = self.build_session(init_image_sha256="d" * 64)
            with self.assertRaises(FileExistsError):
                clock_smoke.prepare_session(runtime, changed)

    def test_prepare_session_rejects_stale_slot_files_and_run_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = self.build_session()
            (runtime / "tracker_ready.json").write_text("{}\n")
            with self.assertRaisesRegex(FileExistsError, "tracker_ready"):
                clock_smoke.prepare_session(runtime, value)
            (runtime / "tracker_ready.json").unlink()
            (runtime / "runs" / CLOCK_SMOKE_RUN_ID).mkdir(parents=True)
            with self.assertRaisesRegex(FileExistsError, "run directory"):
                clock_smoke.prepare_session(runtime, value)

    def test_prepare_session_rejects_research_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = self.build_session()
            research = session("rs3-d1-p1-r5", STUDY_ID)
            install_session(runtime, research)
            with self.assertRaisesRegex(FileExistsError, "mutually exclusive"):
                clock_smoke.prepare_session(runtime, value)
            (runtime / "rate_study_session.json").unlink()
            (runtime / "runs" / "rs3-d1-p1-r5").mkdir(parents=True)
            with self.assertRaisesRegex(FileExistsError, "mutually exclusive"):
                clock_smoke.prepare_session(runtime, value)

    def make_smoke_run(self, runtime, *, bad_clock=False):
        value = self.build_session()
        run_directory = make_run_directory(runtime, value)
        make_release_chain(runtime, value)
        archive_release_provenance(runtime, run_directory, value)
        records = [
            {
                "frame_id": 19,
                "phase": "hold",
                "capture_monotonic_s": 499.9,
                "capture_monotonic_clock_id": CLOCK_ID,
            },
            {
                "frame_id": 20,
                "phase": "measurement",
                "capture_monotonic_s": 500.1,
                "capture_monotonic_clock_id": (
                    "unity-process-relative/v1" if bad_clock else CLOCK_ID
                ),
            },
            {
                "frame_id": 21,
                "phase": "measurement",
                "capture_monotonic_s": 500.2,
                "capture_monotonic_clock_id": CLOCK_ID,
            },
        ]
        with (run_directory / "frames.jsonl").open("w") as handle:
            for record in records:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
        atomic_json(
            run_directory / "summary.json",
            {
                "schema_version": "p1-track-run/v1",
                "event_counts": {},
                "monotonic_capture_cadence_post_release": {
                    "strictly_increasing": True
                },
                "release_clock_id": CLOCK_ID,
            },
        )
        return run_directory

    def test_verify_passes_clean_run_and_never_reports_c_values(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            run_directory = self.make_smoke_run(runtime)
            result = clock_smoke.verify_run(run_directory)
            self.assertEqual(result["verdict"], "PASS")
            self.assertEqual(result["failures"], [])
            payload = json.dumps(result).lower()
            self.assertNotIn("c_track", payload)
            self.assertNotIn("c_geom", payload)

    def test_verify_detects_bad_clock_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            run_directory = self.make_smoke_run(runtime, bad_clock=True)
            result = clock_smoke.verify_run(run_directory)
            self.assertEqual(result["verdict"], "FAIL")
            self.assertTrue(
                any("capture_monotonic_clock_id" in item for item in result["failures"])
            )

    def test_verify_detects_non_increasing_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            run_directory = self.make_smoke_run(runtime)
            path = run_directory / "frames.jsonl"
            lines = path.read_text().splitlines()
            records = [json.loads(line) for line in lines]
            records[2]["capture_monotonic_s"] = 500.05
            path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
            )
            result = clock_smoke.verify_run(run_directory)
            self.assertEqual(result["verdict"], "FAIL")
            self.assertTrue(
                any("strictly increasing" in item for item in result["failures"])
            )


if __name__ == "__main__":
    unittest.main()
