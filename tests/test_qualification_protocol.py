import json
from pathlib import Path
import tempfile
import unittest

from controller.qualification_protocol import (
    ACK_FILE,
    ACTIVE_FILE,
    ACTIVE_POINTER_FILE,
    COMMAND_FILE,
    QualificationProtocolError,
    QualificationReleaseLifecycle,
    manifest_identity,
    request_release,
    validate_provenance,
)
from controller.run_log import RunLogger


RUN_ID = "p1-detect-001-qual-99"
SCENARIO_ID = "p1-scene-004"


def metadata(
    frame_id,
    *,
    simulation_time_s,
    capture_unix_s,
    capture_monotonic_s,
):
    return {
        "schema_version": "tethered-sensor-frame/v3",
        "scenario_id": SCENARIO_ID,
        "frame_id": frame_id,
        "simulation_time_s": simulation_time_s,
        "capture_unix_s": capture_unix_s,
        "capture_monotonic_s": capture_monotonic_s,
        "capture_monotonic_clock_id": "system-stopwatch/v1",
    }


def create_run(runtime, *, planned_duration_s=1.5):
    return RunLogger(
        runtime,
        RUN_ID,
        {
            "scenario_id": SCENARIO_ID,
            "condition": "follow",
            "planned_duration_s": planned_duration_s,
            "init": {
                "frame_id": 0,
                "box_norm": [0.4, 0.3, 0.2, 0.2],
            },
            "qualification_release": manifest_identity(),
        },
    )


class QualificationProtocolTests(unittest.TestCase):
    def test_release_is_create_once_and_first_fresh_frame_is_the_only_origin(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            logger = create_run(runtime)
            lifecycle = QualificationReleaseLifecycle(
                runtime,
                RUN_ID,
                scenario_id=SCENARIO_ID,
                init_frame_id=0,
                unix_time=lambda: 100.1,
                monotonic=lambda: 500.1,
            )
            init = metadata(
                0,
                simulation_time_s=0.0,
                capture_unix_s=1.0,
                capture_monotonic_s=400.0,
            )
            lifecycle.publish_ready(init)
            command_path, command = request_release(
                runtime,
                RUN_ID,
                unix_time=lambda: 100.3,
                monotonic=lambda: 500.3,
                command_id_factory=lambda: "command-1",
            )
            command_bytes = command_path.read_bytes()
            repeated_path, repeated = request_release(
                runtime,
                RUN_ID,
                unix_time=lambda: 999.0,
                monotonic=lambda: 999.0,
                command_id_factory=lambda: "must-not-replace",
            )
            self.assertEqual(repeated_path, command_path)
            self.assertEqual(repeated, command)
            self.assertEqual(command_path.read_bytes(), command_bytes)

            stale = metadata(
                1,
                simulation_time_s=0.2,
                capture_unix_s=1.2,
                capture_monotonic_s=400.2,
            )
            self.assertEqual(lifecycle.record_fields(stale)["phase"], "hold")
            self.assertFalse((logger.run_directory / ACK_FILE).exists())

            release = metadata(
                2,
                simulation_time_s=1.0,
                capture_unix_s=101.0,
                capture_monotonic_s=500.4,
            )
            release_fields = lifecycle.record_fields(release)
            self.assertEqual(release_fields["phase"], "measurement")
            self.assertEqual(release_fields["measurement_elapsed_s"], 0.0)
            self.assertEqual(release_fields["measurement_wall_elapsed_s"], 0.0)

            later = metadata(
                3,
                simulation_time_s=2.6,
                capture_unix_s=102.6,
                capture_monotonic_s=502.0,
            )
            later_fields = lifecycle.record_fields(later)
            self.assertAlmostEqual(later_fields["measurement_elapsed_s"], 1.6)
            self.assertAlmostEqual(
                later_fields["measurement_wall_elapsed_s"],
                1.6,
            )
            provenance = validate_provenance(logger.run_directory)
            self.assertEqual(provenance["release_frame_id"], 2)
            self.assertEqual(provenance["release_monotonic_s"], 500.4)
            active = json.loads(
                (logger.run_directory / ACTIVE_FILE).read_text(
                    encoding="utf-8"
                )
            )
            metrics = {
                "elapsed_simulation_s": 1.6,
                "qualification_release": {
                    "schema_version": (
                        "p1-detect-qualification-metrics-origin/v1"
                    ),
                    "protocol_id": provenance["protocol_id"],
                    "run_id": RUN_ID,
                    "scenario_id": SCENARIO_ID,
                    "command_id": provenance["command_id"],
                    "release_command_sha256": provenance[
                        "release_command_sha256"
                    ],
                    "active_marker_sha256": provenance[
                        "active_marker_sha256"
                    ],
                    "release_frame_id": 2,
                    "release_monotonic_s": 500.4,
                    "release_simulation_s": 1.0,
                },
            }
            lifecycle.validate_metrics(metrics, planned_duration_s=1.5)
            lifecycle.clear_active_pointer()
            self.assertFalse((runtime / ACTIVE_POINTER_FILE).exists())
            self.assertEqual(
                json.loads(
                    (logger.run_directory / ACTIVE_FILE).read_text(
                        encoding="utf-8"
                    )
                ),
                active,
            )
            with self.assertRaisesRegex(
                QualificationProtocolError,
                "already acknowledged",
            ):
                request_release(runtime, RUN_ID)
            logger.close()

    def test_finalize_excludes_hold_and_binds_both_duration_origins(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            logger = create_run(runtime)
            lifecycle = QualificationReleaseLifecycle(
                runtime,
                RUN_ID,
                scenario_id=SCENARIO_ID,
                init_frame_id=0,
                unix_time=lambda: 100.1,
                monotonic=lambda: 500.1,
            )
            init = metadata(
                0,
                simulation_time_s=0.0,
                capture_unix_s=1.0,
                capture_monotonic_s=400.0,
            )
            lifecycle.publish_ready(init)
            request_release(
                runtime,
                RUN_ID,
                unix_time=lambda: 100.3,
                monotonic=lambda: 500.3,
                command_id_factory=lambda: "command-2",
            )
            values = [
                (
                    init,
                    {
                        "phase": "hold",
                        "capture_monotonic_s": 400.0,
                        "measurement_elapsed_s": None,
                        "measurement_wall_elapsed_s": None,
                    },
                ),
                (
                    metadata(
                        1,
                        simulation_time_s=0.2,
                        capture_unix_s=1.2,
                        capture_monotonic_s=400.2,
                    ),
                    None,
                ),
                (
                    metadata(
                        2,
                        simulation_time_s=1.0,
                        capture_unix_s=101.0,
                        capture_monotonic_s=500.4,
                    ),
                    None,
                ),
                (
                    metadata(
                        3,
                        simulation_time_s=2.6,
                        capture_unix_s=102.6,
                        capture_monotonic_s=502.0,
                    ),
                    None,
                ),
            ]
            for frame, fields in values:
                effective = fields or lifecycle.record_fields(frame)
                logger.append(
                    {
                        "frame_id": frame["frame_id"],
                        "capture_unix_s": frame["capture_unix_s"],
                        "simulation_time_s": frame["simulation_time_s"],
                        "compute_latency_ms": 5.0,
                        "compute_stage": "update",
                        "frame_age_ms": 1.0,
                        "backlog_count": 0,
                        "skipped_count": 0,
                        "published_observation": effective["phase"]
                        == "measurement",
                        "published_gimbal_command": effective["phase"]
                        == "measurement",
                        "state": "TRACKING",
                        "event": None,
                        **effective,
                    }
                )
            _, summary = logger.finalize()
            self.assertEqual(summary["hold_frame_records"], 2)
            self.assertEqual(summary["measurement_frame_records"], 2)
            self.assertAlmostEqual(summary["actual_duration_s"], 1.6)
            self.assertAlmostEqual(summary["actual_wall_duration_s"], 1.6)
            self.assertEqual(summary["release_monotonic_s"], 500.4)
            self.assertEqual(
                summary["wall_clock_capture_window"]["cutoff_source"],
                "qualification_release.release_unix_s",
            )
            self.assertEqual(
                summary["wall_clock_capture_window"]["first_eligible_frame_id"],
                2,
            )

    def test_request_refuses_missing_ready_and_tampered_command(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            logger = create_run(runtime)
            with self.assertRaisesRegex(
                QualificationProtocolError,
                "qualification-release-ready",
            ):
                request_release(runtime, RUN_ID)
            lifecycle = QualificationReleaseLifecycle(
                runtime,
                RUN_ID,
                scenario_id=SCENARIO_ID,
                init_frame_id=0,
                unix_time=lambda: 100.1,
                monotonic=lambda: 500.1,
            )
            lifecycle.publish_ready(
                metadata(
                    0,
                    simulation_time_s=0.0,
                    capture_unix_s=1.0,
                    capture_monotonic_s=400.0,
                )
            )
            with self.assertRaisesRegex(
                QualificationProtocolError,
                "does not follow ready",
            ):
                request_release(
                    runtime,
                    RUN_ID,
                    unix_time=lambda: 100.1,
                    monotonic=lambda: 500.1,
                    command_id_factory=lambda: "too-early",
                )
            self.assertFalse(
                (logger.run_directory / COMMAND_FILE).exists()
            )
            command_path, command = request_release(
                runtime,
                RUN_ID,
                unix_time=lambda: 100.3,
                monotonic=lambda: 500.3,
                command_id_factory=lambda: "command-3",
            )
            command["manifest_sha256"] = "0" * 64
            command_path.write_text(json.dumps(command), encoding="utf-8")
            with self.assertRaisesRegex(
                QualificationProtocolError,
                "manifest hash mismatch",
            ):
                lifecycle.poll_release_command()
            logger.close()

    def test_provenance_rejects_ack_hash_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            logger = create_run(runtime)
            lifecycle = QualificationReleaseLifecycle(
                runtime,
                RUN_ID,
                scenario_id=SCENARIO_ID,
                init_frame_id=0,
                unix_time=lambda: 100.1,
                monotonic=lambda: 500.1,
            )
            lifecycle.publish_ready(
                metadata(
                    0,
                    simulation_time_s=0.0,
                    capture_unix_s=1.0,
                    capture_monotonic_s=400.0,
                )
            )
            request_release(
                runtime,
                RUN_ID,
                unix_time=lambda: 100.3,
                monotonic=lambda: 500.3,
                command_id_factory=lambda: "command-4",
            )
            lifecycle.record_fields(
                metadata(
                    2,
                    simulation_time_s=1.0,
                    capture_unix_s=101.0,
                    capture_monotonic_s=500.4,
                )
            )
            ack_path = logger.run_directory / ACK_FILE
            ack = json.loads(ack_path.read_text(encoding="utf-8"))
            ack["release_frame_id"] = 7
            ack_path.write_text(json.dumps(ack), encoding="utf-8")
            with self.assertRaisesRegex(
                QualificationProtocolError,
                "provenance content mismatch",
            ):
                validate_provenance(logger.run_directory)
            logger.close()

    def test_metrics_fail_closed_without_matching_unity_release_origin(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            logger = create_run(runtime)
            lifecycle = QualificationReleaseLifecycle(
                runtime,
                RUN_ID,
                scenario_id=SCENARIO_ID,
                init_frame_id=0,
                unix_time=lambda: 100.1,
                monotonic=lambda: 500.1,
            )
            lifecycle.publish_ready(
                metadata(
                    0,
                    simulation_time_s=0.0,
                    capture_unix_s=1.0,
                    capture_monotonic_s=400.0,
                )
            )
            request_release(
                runtime,
                RUN_ID,
                unix_time=lambda: 100.3,
                monotonic=lambda: 500.3,
                command_id_factory=lambda: "command-5",
            )
            lifecycle.record_fields(
                metadata(
                    2,
                    simulation_time_s=1.0,
                    capture_unix_s=101.0,
                    capture_monotonic_s=500.4,
                )
            )
            with self.assertRaisesRegex(
                QualificationProtocolError,
                "lack release identity",
            ):
                lifecycle.validate_metrics(
                    {"elapsed_simulation_s": 2.0},
                    planned_duration_s=1.5,
                )
            logger.close()


if __name__ == "__main__":
    unittest.main()
