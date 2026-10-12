from __future__ import annotations

from collections import deque
import base64
import json
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from controller.rate2_protocol import (
    RELEASE_ACK_SCHEMA,
    READY_SCHEMA,
    Rate2ProtocolError,
    Rate2TrackerLifecycle,
    archive_release_provenance,
    atomic_bytes,
    atomic_json,
    build_release_command,
    canonical_json_bytes,
    identity_hashes,
    read_consistent_ready,
    sha256_bytes,
    sha256_file,
    validate_provenance,
    validate_release_bundle,
    validate_session,
)
from controller.run_log import RunLogger, build_summary, read_frame_records
from controller.geolocate import box_ground_intersection
from controller.track_loop import FrameRepository, RuntimePublisher, TrackLoop
from controller.trackers import TrackerResult
from tools.run_rate2_study import (
    authorize_session,
    attempt_row,
    archive_failed_attempt,
    build_decision_a,
    build_session,
    campaign_directory,
    coordinate_release,
    finalize_attempt,
    freeze_calibration,
    load_calibration,
    prepare_campaign,
    prepare_session,
    preview_calibration,
    qualify_pilot,
    validate_decision_a,
)
from tools.run_rate_study import _frame_candidates


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


def session(run_id="rs2-pilot", *, init_frame_id=0, init_hash="c" * 64):
    return build_session(
        run_id=run_id,
        init_frame_id=init_frame_id,
        init_image_sha256=init_hash,
        hold_route_s_m=2.5,
        tracker_identity=tracker_identity(),
    )


def ready_document(value, *, frame_id=20, seq=20, published=100.0):
    return {
        "schema_version": READY_SCHEMA,
        "state": "TRACKING",
        **{
            key: value[key]
            for key in (
                "study_id",
                "run_id",
                "scenario_id",
                "tracker_id",
                "tracker_identity_sha256",
                "model_identity_sha256",
                "init_frame_id",
                "init_image_sha256",
            )
        },
        "last_processed_frame_id": frame_id,
        "processed_frame_count": seq,
        "seq": seq,
        "publisher_monotonic_s": published,
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
        **{
            key: value[key]
            for key in (
                "study_id",
                "run_id",
                "scenario_id",
                "tracker_id",
                "tracker_identity_sha256",
                "model_identity_sha256",
                "init_frame_id",
                "init_image_sha256",
            )
        },
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


def write_frame(runtime, frame_id, *, schema="tethered-sensor-frame/v2"):
    frames = runtime / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    stem = f"frame_{frame_id:010d}"
    image = frames / f"{stem}.jpg"
    image.write_bytes(b"image-" + str(frame_id).encode())
    metadata = {
        "schema_version": schema,
        "scenario_id": "rate-study-20hz",
        "frame_id": frame_id,
        "simulation_time_s": 7.0 + frame_id * 0.05,
        "capture_unix_s": 1_800_000_000.0 + frame_id * 0.05,
        "capture_monotonic_s": 499.0 + frame_id * 0.05,
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


def make_run_artifacts(
    runtime,
    run_id,
    *,
    conditional=0.4,
    ratio=0.1,
    lost=None,
    planned=268.97056274847716,
    matched=10,
    c_geom=1.0,
):
    value = session(run_id)
    run_directory = runtime / "runs" / run_id
    run_directory.mkdir(parents=True)
    manifest = {
        "schema_version": "p1-track-run/v1",
        "run_id": run_id,
        "scenario_id": value["scenario_id"],
        "condition": "follow",
        "planned_duration_s": planned,
        "rate2": {
            key: value[key]
            for key in (
                "study_id",
                "run_id",
                "scenario_id",
                "tracker_id",
                "tracker_identity_sha256",
                "model_identity_sha256",
                "init_frame_id",
                "init_image_sha256",
                "hold_route_s_m",
            )
        },
    }
    atomic_json(run_directory / "manifest.json", manifest)
    ready_bytes = canonical_json_bytes(ready_document(value))
    command_bytes = build_release_command(
        value, ready_bytes, command_id=f"release-{run_id}"
    )
    ack_bytes = canonical_json_bytes(ack_document(value, command_bytes))
    atomic_bytes(runtime / "release_command.accepted.json", command_bytes)
    atomic_bytes(runtime / "release_ack.json", ack_bytes)
    archive_release_provenance(runtime, run_directory, value)
    atomic_json(
        run_directory / "summary.json",
        {
            "schema_version": "p1-track-run/v1",
            "actual_duration_s": planned,
            "time_to_first_lost_s": (
                lost if lost is not None else planned
            ),
            "time_to_first_lost_right_censored": lost is None,
            "lost_records": 0 if lost is None else 1,
            "gap_events": 0,
            "reinit_required_records": 0,
            "compute_latency_ms": {"p95": 5.0},
            "backlog_count": {"p95": 0.0},
            "monotonic_capture_cadence_post_release": {
                "strictly_increasing": True,
                "rate_hz": 20.0,
            },
        },
    )
    incorrect = round(ratio * matched)
    atomic_json(
        run_directory / "metrics.final.json",
        {
            "schema_version": "tethered-evaluation/v1",
            "scenario_id": value["scenario_id"],
            "elapsed_simulation_s": planned,
            "aggregate": {
                "c_track": conditional,
                "c_geom": c_geom,
                "c_track_given_geom": conditional,
                "matched_tracking_observations": matched,
                "incorrect_tracking_observations": incorrect,
                "unmatched_tracking_observations": 0,
            },
        },
    )
    bindings = {
        "manifest_sha256": sha256_file(run_directory / "manifest.json"),
        "release_provenance_sha256": sha256_file(
            run_directory / "release_provenance.json"
        ),
        "summary_sha256": sha256_file(run_directory / "summary.json"),
        "metrics_sha256": sha256_file(run_directory / "metrics.final.json"),
    }
    atomic_json(
        run_directory / "rate2-status.json",
        {
            "schema_version": "p1-rate2-attempt-status/v1",
            "study_id": value["study_id"],
            "run_id": run_id,
            "admissible": True,
            "classification": "COMPLETE",
            "gates": {"S1": True, "S2": True, "S3": True},
            **bindings,
        },
    )
    return run_directory


class RecordingTracker:
    name = "nanotrack-v2"
    backend = "test"
    version = "5.0.0"

    def __init__(self):
        self.results = deque([TrackerResult((0.4, 0.3, 0.2, 0.2), True, 1.0, "tracker")] * 3)

    def init(self, image, box):
        return True

    def update(self, image):
        return self.results.popleft()

    def manifest_identity(self):
        return tracker_identity()


class Rate2ProtocolTests(unittest.TestCase):
    def test_batch_and_tracker_identity_fail_closed(self):
        value = session()
        for key, invalid in (
            ("study_id", "other-study"),
            ("tracker_id", "csrt"),
            ("scenario_id", "rate-study-5hz"),
            ("tracker_identity_sha256", "not-a-hash"),
        ):
            changed = dict(value)
            changed[key] = invalid
            with self.subTest(key=key), self.assertRaises(Rate2ProtocolError):
                validate_session(changed)

    def test_prepare_session_rejects_stale_slots_and_is_create_once(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            prepare_campaign(runtime)
            value = session("rs2-r20-calib")
            (runtime / "gimbal_command.json").write_text("{}\n")
            with self.assertRaisesRegex(FileExistsError, "gimbal_command"):
                prepare_session(runtime, value)
            (runtime / "gimbal_command.json").unlink()
            self.assertEqual(prepare_session(runtime, value), value)
            self.assertEqual(prepare_session(runtime, value), value)
            changed = dict(value)
            changed["init_image_sha256"] = "d" * 64
            with self.assertRaises(FileExistsError):
                prepare_session(runtime, changed)

    def test_calibration_overlay_freezes_v2_reference_and_gates_pilot_session(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            prepare_campaign(runtime)
            calibration_session = session("rs2-r20-calib")
            prepare_session(runtime, calibration_session)
            reference_image = write_frame(runtime, 0)
            self.assertTrue(
                cv2.imwrite(
                    str(reference_image),
                    np.zeros((100, 200, 3), dtype=np.uint8),
                )
            )
            preview = preview_calibration(
                runtime,
                20,
                (0.4, 0.3, 0.2, 0.2),
            )
            self.assertTrue(Path(preview["overlay_path"]).is_file())
            calibration = freeze_calibration(runtime, 20, confirmed=True)
            self.assertEqual(
                calibration["reference_image_sha256"],
                sha256_file(reference_image),
            )
            self.assertEqual(load_calibration(runtime, 20), calibration)
            (runtime / "rate_study_session.json").unlink()
            pilot_session = session(
                "rs2-pilot",
                init_frame_id=calibration["reference_frame_id"],
                init_hash=calibration["reference_image_sha256"],
            )
            self.assertEqual(
                prepare_session(runtime, pilot_session)["run_id"],
                "rs2-pilot",
            )

    def test_real_frame_consumers_accept_v2_and_reject_v1_in_rate2_context(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            write_frame(runtime, 0)
            repository = FrameRepository(
                runtime,
                image_loader=lambda path: path.name,
                expected_frame_schema="tethered-sensor-frame/v2",
            )
            self.assertEqual(repository.load(0).frame_id, 0)
            self.assertEqual(
                _frame_candidates(
                    runtime,
                    "rate-study-20hz",
                    7.0,
                    8.0,
                    expected_sensor_schema="tethered-sensor-frame/v2",
                )[0]["frame_id"],
                0,
            )
            write_frame(runtime, 1, schema="tethered-sensor-frame/v1")
            with self.assertRaisesRegex(ValueError, "expected 'tethered-sensor-frame/v2'"):
                repository.load(1)
            with self.assertRaisesRegex(ValueError, "expected 'tethered-sensor-frame/v2'"):
                _frame_candidates(
                    runtime,
                    "rate-study-20hz",
                    7.0,
                    8.0,
                    expected_sensor_schema="tethered-sensor-frame/v2",
                )

    def test_geolocation_tolerates_v2_monotonic_field_without_contract_change(self):
        metadata = {
            "schema_version": "tethered-sensor-frame/v2",
            "capture_monotonic_s": 123.0,
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
        result = box_ground_intersection(
            (0.4, 0.3, 0.2, 0.2),
            metadata,
            ground_plane_y_m=0.0,
            maximum_distance_m=1000.0,
        )
        self.assertAlmostEqual(result.point_world_m[1], 0.0)

    def test_heartbeat_advances_and_consistent_read_rejects_stale_or_backlogged(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = session()
            write_latest(runtime, 21)
            atomic_json(runtime / "tracker_ready.json", ready_document(value, frame_id=20))
            payload, ready, latest = read_consistent_ready(
                runtime, value, previous_seq=19, now_monotonic_s=101.0
            )
            self.assertEqual(latest, 21)
            self.assertEqual(ready["seq"], 20)
            self.assertEqual(json.loads(payload)["last_processed_frame_id"], 20)
            with self.assertRaisesRegex(Rate2ProtocolError, "did not advance"):
                read_consistent_ready(
                    runtime, value, previous_seq=20, now_monotonic_s=101.0
                )
            with self.assertRaisesRegex(Rate2ProtocolError, "stale"):
                read_consistent_ready(
                    runtime, value, previous_seq=19, now_monotonic_s=103.0
                )
            with self.assertRaisesRegex(Rate2ProtocolError, "future"):
                read_consistent_ready(
                    runtime, value, previous_seq=19, now_monotonic_s=99.0
                )
            write_latest(runtime, 22)
            with self.assertRaisesRegex(Rate2ProtocolError, "outside"):
                read_consistent_ready(
                    runtime, value, previous_seq=19, now_monotonic_s=101.0
                )

    def test_exact_release_chain_and_provenance_are_immutable_and_tamper_evident(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = session()
            run_directory = runtime / "runs" / value["run_id"]
            run_directory.mkdir(parents=True)
            atomic_json(
                run_directory / "manifest.json",
                {
                    "schema_version": "p1-track-run/v1",
                    "run_id": value["run_id"],
                    "scenario_id": value["scenario_id"],
                    "planned_duration_s": 30.0,
                    "rate2": {
                        **{
                            key: value[key]
                            for key in (
                                "study_id",
                                "run_id",
                                "scenario_id",
                                "tracker_id",
                                "tracker_identity_sha256",
                                "model_identity_sha256",
                                "init_frame_id",
                                "init_image_sha256",
                                "hold_route_s_m",
                            )
                        }
                    },
                },
            )
            ready_bytes = canonical_json_bytes(ready_document(value))
            command_bytes = build_release_command(
                value, ready_bytes, command_id="release-1"
            )
            ack_bytes = canonical_json_bytes(ack_document(value, command_bytes))
            validate_release_bundle(command_bytes, ack_bytes, value)
            atomic_bytes(runtime / "release_command.accepted.json", command_bytes)
            atomic_bytes(runtime / "release_ack.json", ack_bytes)
            first = archive_release_provenance(runtime, run_directory, value)
            second = archive_release_provenance(runtime, run_directory, value)
            self.assertEqual(first, second)
            self.assertEqual(validate_provenance(run_directory)["command_id"], "release-1")
            command_archive = run_directory / "release-command.json"
            command_archive.write_bytes(command_archive.read_bytes() + b" ")
            with self.assertRaises(Rate2ProtocolError):
                validate_provenance(run_directory)

    def test_coordinator_reserves_transport_frame_then_archives_ack(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            value = session()
            prepare_campaign(runtime)
            atomic_json(runtime / "rate_study_session.json", value)
            run_directory = runtime / "runs" / value["run_id"]
            run_directory.mkdir(parents=True)
            atomic_json(
                run_directory / "manifest.json",
                {
                    "schema_version": "p1-track-run/v1",
                    "run_id": value["run_id"],
                    "scenario_id": value["scenario_id"],
                    "planned_duration_s": 30.0,
                    "rate2": {
                        key: value[key]
                        for key in (
                            "study_id",
                            "run_id",
                            "scenario_id",
                            "tracker_id",
                            "tracker_identity_sha256",
                            "model_identity_sha256",
                            "init_frame_id",
                            "init_image_sha256",
                            "hold_route_s_m",
                        )
                    },
                },
            )
            with self.assertRaises(PermissionError):
                authorize_session(runtime, "rs2-r20-follow-2")
            write_latest(runtime, 20)
            atomic_json(runtime / "tracker_ready.json", ready_document(value))
            state = {"sleep": 0, "command_ready_frame": None}

            def sleeper(_):
                state["sleep"] += 1
                if state["sleep"] == 1:
                    write_latest(runtime, 21)
                    atomic_json(
                        runtime / "tracker_ready.json",
                        ready_document(
                            value,
                            frame_id=20,
                            seq=21,
                            published=100.0,
                        ),
                    )
                elif state["sleep"] == 2:
                    atomic_json(
                        runtime / "tracker_ready.json",
                        ready_document(
                            value,
                            frame_id=21,
                            seq=22,
                            published=100.0,
                        ),
                    )
                control = runtime / "experiment_control.json"
                if control.is_file() and not (runtime / "release_ack.json").is_file():
                    command_bytes = control.read_bytes()
                    command = json.loads(command_bytes)
                    ready = json.loads(
                        base64.b64decode(command["ready_json_base64"])
                    )
                    state["command_ready_frame"] = ready[
                        "last_processed_frame_id"
                    ]
                    atomic_bytes(
                        runtime / "release_command.accepted.json",
                        command_bytes,
                    )
                    atomic_json(
                        runtime / "release_ack.json",
                        ack_document(
                            value,
                            command_bytes,
                            release_frame=22,
                        ),
                    )

            result = coordinate_release(
                runtime,
                confirmed=True,
                timeout_s=2.0,
                poll_interval_s=0.01,
                monotonic=lambda: 100.0,
                sleeper=sleeper,
                command_id="coordinated-release",
            )
            self.assertEqual(result["command_id"], "coordinated-release")
            self.assertEqual(state["command_ready_frame"], 21)
            self.assertEqual(result["accepted_backlog_frames"], 1)
            self.assertTrue((run_directory / "release_provenance.json").is_file())

    def test_track_loop_holds_controls_then_uses_release_phase(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            init_image = write_frame(runtime, 0)
            write_frame(runtime, 1)
            init_hash = sha256_file(init_image)
            value = session(init_hash=init_hash)
            lifecycle = Rate2TrackerLifecycle(
                runtime,
                value,
                tracker_identity(),
                init_frame_id=0,
                init_image_sha256=init_hash,
                scenario_id=value["scenario_id"],
                run_id=value["run_id"],
                monotonic=lambda: 100.0,
            )
            logger = RunLogger(runtime, value["run_id"], {"condition": "follow"})
            loop = TrackLoop(
                FrameRepository(
                    runtime,
                    image_loader=lambda path: path,
                    expected_frame_schema="tethered-sensor-frame/v2",
                ),
                RecordingTracker(),
                RuntimePublisher(runtime, 1.0),
                logger,
                track_id="target-vehicle-red",
                condition="follow",
                ground_plane_y_m=0.0,
                maximum_ground_range_m=1000.0,
                planned_duration_s=0.05,
                rate2_lifecycle=lifecycle,
            )
            try:
                loop.initialize(0, (0.4, 0.3, 0.2, 0.2))
                loop.process_available(1)
                self.assertFalse((runtime / "gimbal_command.json").exists())
                self.assertFalse((runtime / "body_command.json").exists())
                heartbeat = json.loads((runtime / "tracker_ready.json").read_text())
                self.assertEqual((heartbeat["seq"], heartbeat["processed_frame_count"]), (2, 2))
                records, _ = read_frame_records(logger.frames_path)
                self.assertEqual([record["phase"] for record in records], ["hold", "hold"])
                self.assertEqual(loop.elapsed_simulation_s, 0.0)

                ready_bytes = canonical_json_bytes(
                    ready_document(value, frame_id=1, seq=20)
                )
                command_bytes = build_release_command(
                    value, ready_bytes, command_id="loop-release"
                )
                atomic_bytes(
                    runtime / "release_command.accepted.json", command_bytes
                )
                atomic_json(
                    runtime / "release_ack.json",
                    ack_document(
                        value,
                        command_bytes,
                        release_frame=1,
                        release_mono=499.075,
                        release_simulation=7.075,
                    ),
                )
                write_frame(runtime, 2)
                loop.process_available(2)
                self.assertTrue((runtime / "gimbal_command.json").is_file())
                records, _ = read_frame_records(logger.frames_path)
                self.assertEqual(records[-1]["phase"], "measurement")
                self.assertAlmostEqual(records[-1]["measurement_elapsed_s"], 0.025)
                self.assertAlmostEqual(loop.elapsed_simulation_s, 0.025)
                self.assertFalse(loop.complete)
                write_frame(runtime, 3)
                loop.process_available(3)
                self.assertAlmostEqual(loop.elapsed_simulation_s, 0.075)
                self.assertTrue(loop.complete)
            finally:
                logger.close()

    def test_long_hold_is_excluded_from_all_measurement_outcomes(self):
        records = [
            {
                "frame_id": 1,
                "phase": "hold",
                "simulation_time_s": 1.0,
                "capture_unix_s": 1.0,
                "capture_monotonic_s": 1.0,
                "measurement_elapsed_s": None,
                "state": "LOST",
                "event": "LOST",
                "compute_stage": "update",
                "compute_latency_ms": 999.0,
                "backlog_count": 99,
            },
            {
                "frame_id": 1201,
                "phase": "measurement",
                "simulation_time_s": 61.1,
                "capture_unix_s": 61.1,
                "capture_monotonic_s": 500.1,
                "measurement_elapsed_s": 0.1,
                "state": "TRACKING",
                "event": None,
                "compute_stage": "update",
                "compute_latency_ms": 5.0,
                "backlog_count": 0,
            },
            {
                "frame_id": 1400,
                "phase": "measurement",
                "simulation_time_s": 71.0,
                "capture_unix_s": 71.0,
                "capture_monotonic_s": 510.0,
                "measurement_elapsed_s": 10.0,
                "state": "TRACKING",
                "event": None,
                "compute_stage": "update",
                "compute_latency_ms": 5.0,
                "backlog_count": 0,
            },
        ]
        summary = build_summary(
            records,
            0,
            planned_duration_s=10.0,
            release_monotonic_s=500.0,
        )
        self.assertEqual(summary["hold_frame_records"], 1)
        self.assertEqual(summary["measurement_frame_records"], 2)
        self.assertEqual(summary["lost_records"], 0)
        self.assertEqual(summary["backlog_count"]["p95"], 0.0)
        self.assertEqual(summary["actual_duration_s"], 10.0)
        self.assertEqual(summary["time_to_first_lost_s"], 10.0)
        self.assertTrue(summary["time_to_first_lost_right_censored"])
        records[2]["capture_monotonic_s"] = 500.05
        with self.assertRaisesRegex(ValueError, "INVALID_CLOCK"):
            build_summary(
                records,
                0,
                planned_duration_s=10.0,
                release_monotonic_s=500.0,
            )

    def test_attempt_finalization_binds_all_artifacts_and_evaluator_cutoff(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            run_directory = make_run_artifacts(runtime, "rs2-r20-follow-1")
            (run_directory / "rate2-status.json").unlink()
            status = finalize_attempt(run_directory)
            self.assertTrue(status["admissible"])
            self.assertEqual(
                status["metrics_elapsed_simulation_s"],
                status["planned_duration_s"],
            )
            metrics_path = run_directory / "metrics.final.json"
            metrics = json.loads(metrics_path.read_text())
            metrics["elapsed_simulation_s"] = 1.0
            atomic_json(metrics_path, metrics)
            with self.assertRaisesRegex(ValueError, "binding mismatch"):
                finalize_attempt(run_directory)

    def test_zero_matched_or_zero_geometry_use_conservative_rule_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            zero_matched = make_run_artifacts(
                runtime,
                "rs2-r20-follow-1",
                conditional=0.9,
                matched=0,
            )
            row = attempt_row(zero_matched)
            self.assertEqual(row["c_track_given_geom"], 0.0)
            self.assertEqual(row["incorrect_over_matched"], 1.0)
            zero_geom = make_run_artifacts(
                runtime,
                "rs2-r20-follow-2",
                conditional=0.9,
                c_geom=0.0,
            )
            self.assertEqual(
                attempt_row(zero_geom)["c_track_given_geom"],
                0.0,
            )

    def test_decision_a_is_data_driven_create_once_and_gates_remaining_sessions(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            prepare_campaign(runtime)
            make_run_artifacts(
                runtime,
                "rs2-pilot",
                conditional=0.5,
                ratio=0.1,
                planned=30.0,
            )
            qualify_pilot(runtime)
            for index, conditional in enumerate((0.4, 0.2, 0.3), start=1):
                make_run_artifacts(
                    runtime,
                    f"rs2-r20-follow-{index}",
                    conditional=conditional,
                    ratio=(0.1, 0.6, 0.2)[index - 1],
                    lost=50.0 if index == 1 else None,
                )
            decision = build_decision_a(runtime)
            self.assertFalse(decision["triggered"])
            self.assertEqual(
                decision["final_action"], "CONTINUE_REMAINING_CELLS"
            )
            before = (campaign_directory(runtime) / "decision_a.json").read_bytes()
            self.assertEqual(build_decision_a(runtime), decision)
            self.assertEqual(
                (campaign_directory(runtime) / "decision_a.json").read_bytes(),
                before,
            )
            authorize_session(runtime, "rs2-r20-nadir-1")
            with self.assertRaisesRegex(
                PermissionError,
                "rs2-r20-nadir-1",
            ):
                authorize_session(runtime, "rs2-r20-nadir-2")
            with self.assertRaisesRegex(
                PermissionError,
                "rs2-r20-nadir-1",
            ):
                authorize_session(runtime, "rs2-r5-calib")
            for run_id in (
                "rs2-r20-nadir-1",
                "rs2-r20-nadir-2",
                "rs2-r20-nadir-3",
            ):
                authorize_session(runtime, run_id)
                make_run_artifacts(runtime, run_id)
            authorize_session(runtime, "rs2-r5-calib")
            for run_id in (
                "rs2-r5-follow-1",
                "rs2-r5-follow-2",
                "rs2-r5-follow-3",
                "rs2-r5-nadir-1",
                "rs2-r5-nadir-2",
                "rs2-r5-nadir-3",
            ):
                authorize_session(runtime, run_id)
                if run_id != "rs2-r5-nadir-3":
                    make_run_artifacts(runtime, run_id)
            self.assertEqual(validate_decision_a(runtime), decision)

    def test_decision_a_trigger_and_invalid_cell_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            prepare_campaign(runtime)
            with self.assertRaises(RuntimeError):
                build_decision_a(runtime)
            for run_id in ("rs2-r20-follow-2", "rs2-r20-follow-3"):
                make_run_artifacts(runtime, run_id)
            for attempt_number in (1, 2, 3):
                failed_run = runtime / "runs" / "rs2-r20-follow-1"
                failed_run.mkdir(parents=True)
                (failed_run / "failure.txt").write_text(
                    f"failure {attempt_number}\n"
                )
                archive_failed_attempt(
                    runtime,
                    "rs2-r20-follow-1",
                    f"synthetic failure {attempt_number}",
                )
            blocked = build_decision_a(runtime, invalid_cell_exhausted=True)
            self.assertIsNone(blocked["triggered"])
            self.assertEqual(blocked["final_action"], "BLOCKED_INVALID_CELL")
            with self.assertRaises(PermissionError):
                authorize_session(runtime, "rs2-r20-nadir-1")
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            prepare_campaign(runtime)
            for index in (1, 2, 3):
                make_run_artifacts(
                    runtime,
                    f"rs2-r20-follow-{index}",
                    conditional=0.1,
                    ratio=0.1,
                )
            triggered = build_decision_a(runtime)
            self.assertTrue(triggered["triggered"])
            self.assertEqual(
                triggered["final_action"], "TERMINATED_AT_DECISION_A"
            )
            self.assertEqual(triggered["m2_status"], "M2_NOT_CLOSABLE")
            with self.assertRaises(PermissionError):
                authorize_session(runtime, "rs2-r5-calib")


if __name__ == "__main__":
    unittest.main()
