import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np

from tools.run_rate_study import (
    BOX_PREVIEW_SCHEMA,
    CALIBRATION_SCHEMA,
    CALIBRATION_STATUS_SCHEMA,
    SUMMARY_SCHEMA,
    capture_calibration,
    invalidate_calibration,
    invalidate_stage,
    invalidate_completed_run,
    launch_staged_run,
    prepare_session,
    preview_calibration_box,
    preview_init_frame,
    render_markdown,
    stage_run,
    summarize_runs,
    validate_rate_configs,
)


def write_frame(runtime, frame_id, simulation_time_s, scenario_id):
    frames = runtime / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    stem = f"frame_{frame_id:010d}"
    image = np.full((48, 64, 3), frame_id % 255, dtype=np.uint8)
    encoded, payload = cv2.imencode(".jpg", image)
    if not encoded:
        raise RuntimeError("test JPEG encoding failed")
    (frames / f"{stem}.jpg").write_bytes(payload.tobytes())
    (frames / f"{stem}.json").write_text(
        json.dumps(
            {
                "schema_version": "tethered-sensor-frame/v1",
                "scenario_id": scenario_id,
                "frame_id": frame_id,
                "simulation_time_s": simulation_time_s,
                "capture_unix_s": 1_800_000_000.0 + simulation_time_s,
            }
        ),
        encoding="utf-8",
    )


def write_attempt(
    runtime,
    rate_hz,
    condition,
    replicate,
    *,
    conditional_coverage=0.5,
    time_to_first_lost_s=120.0,
    wall_rate_hz=20.1,
    actual_duration_s=269.0,
    attempt_suffix=None,
):
    replicate_id = f"rate{rate_hz}-{condition}-r{replicate}"
    attempt_id = (
        replicate_id
        if attempt_suffix is None
        else f"{replicate_id}-{attempt_suffix}"
    )
    directory = runtime / "runs" / attempt_id
    directory.mkdir(parents=True)
    scenario_id = f"rate-study-{rate_hz}hz"
    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "p1-track-run/v1",
                "run_id": attempt_id,
                "scenario_id": scenario_id,
                "condition": condition,
                "planned_duration_s": 268.97056274847716,
                "rate_study": {
                    "rate_hz": rate_hz,
                    "replicate_index": replicate,
                    "replicate_id": replicate_id,
                    "attempt_id": attempt_id,
                    "loop_duration_s": 104.485,
                    "scenario_config_sha256": validate_rate_configs()[
                        "config_sha256"
                    ][str(rate_hz)],
                },
            }
        ),
        encoding="utf-8",
    )
    (directory / "rate-study-status.json").write_text(
        json.dumps(
            {
                "schema_version": "p1-rate-study-attempt-status/v1",
                "attempt_id": attempt_id,
                "replicate_id": replicate_id,
                "classification": "COMPLETE",
                "admissible": True,
            }
        ),
        encoding="utf-8",
    )
    (directory / "summary.json").write_text(
        json.dumps(
            {
                "schema_version": "p1-track-run/v1",
                "actual_duration_s": actual_duration_s,
                "compute_latency_ms": {"p50": 5.0, "p95": 10.0},
                "frame_age_ms": {"p50": 20.0, "p95": 30.0},
                "wall_clock_capture_cadence": {
                    "rate_hz": wall_rate_hz if rate_hz == 20 else 5.0,
                    "strictly_increasing": True,
                    "interval_s": {"p50": 1.0 / rate_hz, "p95": 1.0 / rate_hz},
                },
                "wall_clock_capture_cadence_post_launch": {
                    "rate_hz": wall_rate_hz if rate_hz == 20 else 5.0,
                    "strictly_increasing": True,
                    "interval_s": {"p50": 1.0 / rate_hz, "p95": 1.0 / rate_hz},
                },
                "wall_clock_capture_window": {
                    "cutoff_source": "manifest.created_unix_s",
                    "not_before_unix_s": 1_800_000_000.0,
                    "eligible_samples": 100,
                    "excluded_prelaunch_samples": 1,
                    "first_eligible_frame_id": 1,
                    "first_eligible_capture_unix_s": 1_800_000_000.1,
                },
                "simulation_time_cadence": {
                    "rate_hz": float(rate_hz),
                    "strictly_increasing": True,
                    "interval_s": {"p50": 1.0 / rate_hz, "p95": 1.0 / rate_hz},
                },
                "backlog_count": {"p50": 0.0, "p95": 0.0},
                "time_to_first_lost_s": time_to_first_lost_s,
                "time_to_first_lost_right_censored": False,
                "lost_records": 1,
                "gap_events": 0,
                "geo_reject_events": 0,
                "reinit_required_records": 0,
            }
        ),
        encoding="utf-8",
    )
    (directory / "metrics.final.json").write_text(
        json.dumps(
            {
                "schema_version": "tethered-evaluation/v1",
                "scenario_id": scenario_id,
                "aggregate": {
                    "c_track": conditional_coverage * 0.5,
                    "c_geom": 0.5,
                    "c_track_given_geom": conditional_coverage,
                    "matched_tracking_observations": 10,
                    "incorrect_tracking_observations": 2,
                    "unmatched_tracking_observations": 1,
                },
            }
        ),
        encoding="utf-8",
    )


class RateStudyTests(unittest.TestCase):
    def test_checked_in_configs_match_only_accepted_rate_derivations(self):
        validation = validate_rate_configs()
        self.assertEqual(validation["rates_hz"], [5, 20])
        self.assertEqual(validation["replicates_per_cell"], 3)
        self.assertEqual(validation["init_window_simulation_s"], [7.0, 8.0])
        self.assertAlmostEqual(validation["planned_duration_s"], 272.9705627)

    def test_prepare_calibrate_stage_and_invalidate_preserve_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "runs" / "existing").mkdir(parents=True)
            (runtime / "runs" / "existing" / "keep").write_text("evidence")
            (runtime / "metrics.json").write_text("{}")
            write_frame(runtime, 1, 1.0, "old")

            preparation = prepare_session(5, runtime)
            self.assertEqual(preparation["scenario_id"], "rate-study-5hz")
            self.assertTrue((runtime / "runs" / "existing" / "keep").is_file())
            self.assertFalse((runtime / "metrics.json").exists())
            self.assertFalse((runtime / "frames").exists())

            write_frame(runtime, 9, 3.1, "rate-study-5hz")
            write_frame(runtime, 10, 7.4, "rate-study-5hz")
            write_frame(runtime, 11, 7.1, "rate-study-5hz")
            preview = preview_init_frame(runtime, 5)
            self.assertEqual(preview["frame_id"], 11)
            self.assertEqual(preview["simulation_time_s"], 7.1)
            self.assertTrue(Path(preview["preview_image"]).is_file())
            raw_preview_bytes = Path(preview["preview_image"]).read_bytes()
            box_preview = preview_calibration_box(
                runtime, 5, (0.1, 0.2, 0.3, 0.4)
            )
            self.assertEqual(box_preview["schema_version"], BOX_PREVIEW_SCHEMA)
            self.assertTrue(Path(box_preview["box_overlay_image"]).is_file())
            self.assertEqual(box_preview["box_xywh_norm"], [0.1, 0.2, 0.3, 0.4])
            self.assertEqual(
                box_preview["box_xywh_px"],
                {"x": 6, "y": 9, "width": 20, "height": 20},
            )
            self.assertNotEqual(
                Path(box_preview["box_overlay_image"]).read_bytes(),
                raw_preview_bytes,
            )
            self.assertEqual(
                Path(box_preview["raw_preview_image"]).read_bytes(),
                raw_preview_bytes,
            )
            with self.assertRaisesRegex(ValueError, "confirmation"):
                capture_calibration(
                    runtime,
                    5,
                    (0.1, 0.2, 0.3, 0.4),
                    False,
                )
            with self.assertRaisesRegex(ValueError, "box_xywh_norm mismatch"):
                capture_calibration(
                    runtime,
                    5,
                    (0.11, 0.2, 0.3, 0.4),
                    True,
                )
            calibration = capture_calibration(
                runtime, 5, (0.1, 0.2, 0.3, 0.4), True
            )
            self.assertEqual(calibration["schema_version"], CALIBRATION_SCHEMA)
            self.assertEqual(calibration["reference_frame_id"], 11)
            self.assertTrue(
                (
                    runtime
                    / "runs"
                    / "rate5-calib"
                    / "reference-box-preview.jpg"
                ).is_file()
            )
            invalid_calibration = invalidate_calibration(
                runtime,
                5,
                "invalid-a",
                "reference box did not tightly cover the target",
            )
            self.assertEqual(invalid_calibration.name, "rate5-calib-invalid-a")
            calibration_status = json.loads(
                (invalid_calibration / "calibration-status.json").read_text()
            )
            self.assertEqual(
                calibration_status["schema_version"],
                CALIBRATION_STATUS_SCHEMA,
            )
            self.assertEqual(calibration_status["classification"], "INVALID")
            preview_calibration_box(runtime, 5, (0.11, 0.2, 0.3, 0.4))
            revised_calibration = capture_calibration(
                runtime, 5, (0.11, 0.2, 0.3, 0.4), True
            )
            self.assertEqual(
                revised_calibration["reference_box_xywh_norm"],
                [0.11, 0.2, 0.3, 0.4],
            )

            prepare_session(5, runtime)
            write_frame(runtime, 20, 7.2, "rate-study-5hz")
            stage = stage_run(runtime, 5, "follow", 1)
            self.assertEqual(stage["attempt_id"], "rate5-follow-r1")
            self.assertEqual(
                stage["reference_box_xywh_norm"], [0.11, 0.2, 0.3, 0.4]
            )
            self.assertTrue(
                (
                    runtime
                    / stage["staged_init_box_preview"]
                ).is_file()
            )
            invalid = invalidate_stage(
                runtime,
                "rate5-follow-r1",
                "invalid-a",
                "visual box check failed",
            )
            self.assertEqual(invalid.name, "rate5-follow-r1-invalid-a")
            status = json.loads(
                (invalid / "rate-study-status.json").read_text()
            )
            self.assertEqual(status["classification"], "INVALID")
            self.assertFalse(status["admissible"])

            retry_stage = stage_run(runtime, 5, "follow", 1)
            self.assertEqual(retry_stage["attempt_id"], "rate5-follow-r1")

    def test_summary_uses_fixed_cell_medians_and_both_sot_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for rate in (5, 20):
                for condition in ("follow", "nadir"):
                    for replicate in (1, 2, 3):
                        conditional = (
                            (0.2, 0.3, 0.1)[replicate - 1]
                            if rate == 20 and condition == "follow"
                            else 0.5
                        )
                        first_lost = (
                            (50.0, 120.0, 60.0)[replicate - 1]
                            if rate == 20 and condition == "follow"
                            else 120.0
                        )
                        write_attempt(
                            runtime,
                            rate,
                            condition,
                            replicate,
                            conditional_coverage=conditional,
                            time_to_first_lost_s=first_lost,
                        )

            summary = summarize_runs(runtime)
            self.assertEqual(summary["schema_version"], SUMMARY_SCHEMA)
            follow = summary["cells"]["20hz-follow"]
            self.assertAlmostEqual(
                follow["c_track_given_geom"]["median"], 0.2
            )
            self.assertAlmostEqual(
                follow["time_to_first_lost_s"]["median"], 60.0
            )
            self.assertEqual(
                summary["decision"]["status"], "TRIGGER_P1_TRACK_002"
            )
            self.assertTrue(
                summary["decision"]["r1_conditional_coverage_below_25pct"]
            )
            self.assertTrue(
                summary["decision"]["r2_continuity_below_one_loop"]
            )
            self.assertEqual(
                summary["decision"]["threshold_sensitivity"],
                {"0.15": False, "0.25": True, "0.35": True},
            )

    def test_launch_requires_confirmation_and_archives_authoritative_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            launched_commands = []
            prepare_session(5, runtime)
            write_frame(runtime, 1, 7.1, "rate-study-5hz")
            preview_calibration_box(runtime, 5, (0.1, 0.2, 0.3, 0.4))
            capture_calibration(runtime, 5, (0.1, 0.2, 0.3, 0.4), True)
            prepare_session(5, runtime)
            write_frame(runtime, 2, 7.2, "rate-study-5hz")
            stage_run(runtime, 5, "nadir", 2)

            with self.assertRaisesRegex(ValueError, "visual box confirmation"):
                launch_staged_run(
                    runtime,
                    "rate5-nadir-r2",
                    Path(sys.executable),
                    0.6,
                    False,
                )

            def fake_tracker(command, **_kwargs):
                launched_commands.append(command)
                run_id = command[command.index("--run-id") + 1]
                scenario_id = command[command.index("--scenario-id") + 1]
                planned_duration_s = float(
                    command[command.index("--planned-duration-s") + 1]
                )
                run_directory = runtime / "runs" / run_id
                run_directory.mkdir(parents=True)
                (run_directory / "manifest.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "p1-track-run/v1",
                            "run_id": run_id,
                            "scenario_id": scenario_id,
                        }
                    )
                )
                (run_directory / "summary.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "p1-track-run/v1",
                            "actual_duration_s": planned_duration_s + 0.01,
                        }
                    )
                )
                (run_directory / "metrics.final.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "tethered-evaluation/v1",
                            "scenario_id": scenario_id,
                        }
                    )
                )
                return subprocess.CompletedProcess(command, 0)

            with patch(
                "tools.run_rate_study.subprocess.run",
                side_effect=fake_tracker,
            ):
                completed = launch_staged_run(
                    runtime,
                    "rate5-nadir-r2",
                    Path(sys.executable),
                    0.6,
                    True,
                    "nanotrack-v2",
                    Path("/identity/models.json"),
                    Path("/models/nanotrack-v2"),
                )
            self.assertEqual(completed.returncode, 0)
            launched = " ".join(launched_commands[0])
            self.assertIn("--tracker nanotrack-v2", launched)
            self.assertIn(
                "--tracker-model-spec /identity/models.json",
                launched,
            )
            self.assertIn(
                "--tracker-model-dir /models/nanotrack-v2",
                launched,
            )
            run_directory = runtime / "runs" / "rate5-nadir-r2"
            status = json.loads(
                (run_directory / "rate-study-status.json").read_text()
            )
            self.assertEqual(status["classification"], "COMPLETE")
            self.assertTrue(status["admissible"])
            self.assertTrue(status["duration_complete"])
            self.assertAlmostEqual(
                status["actual_duration_s"],
                status["planned_duration_s"] + 0.01,
            )
            self.assertTrue((run_directory / "init-frame.jpg").is_file())
            self.assertTrue(
                (run_directory / "init-frame-box-preview.jpg").is_file()
            )
            self.assertTrue((run_directory / "rate-study-stage.json").is_file())
            status_path = invalidate_completed_run(
                runtime,
                "rate5-nadir-r2",
                "operator stopped Play before verification",
            )
            invalid_status = json.loads(status_path.read_text())
            self.assertEqual(invalid_status["classification"], "INVALID")
            self.assertFalse(invalid_status["admissible"])

    def test_launch_marks_short_attempt_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            prepare_session(5, runtime)
            write_frame(runtime, 1, 7.1, "rate-study-5hz")
            preview_calibration_box(runtime, 5, (0.1, 0.2, 0.3, 0.4))
            capture_calibration(runtime, 5, (0.1, 0.2, 0.3, 0.4), True)
            prepare_session(5, runtime)
            write_frame(runtime, 2, 7.2, "rate-study-5hz")
            stage_run(runtime, 5, "follow", 1)

            def fake_tracker(command, **_kwargs):
                run_id = command[command.index("--run-id") + 1]
                scenario_id = command[command.index("--scenario-id") + 1]
                run_directory = runtime / "runs" / run_id
                run_directory.mkdir(parents=True)
                (run_directory / "manifest.json").write_text("{}")
                (run_directory / "summary.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "p1-track-run/v1",
                            "actual_duration_s": 10.0,
                        }
                    )
                )
                (run_directory / "metrics.final.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "tethered-evaluation/v1",
                            "scenario_id": scenario_id,
                        }
                    )
                )
                return subprocess.CompletedProcess(command, 0)

            with patch(
                "tools.run_rate_study.subprocess.run",
                side_effect=fake_tracker,
            ):
                launch_staged_run(
                    runtime,
                    "rate5-follow-r1",
                    Path(sys.executable),
                    0.6,
                    True,
                )
            status = json.loads(
                (
                    runtime
                    / "runs"
                    / "rate5-follow-r1"
                    / "rate-study-status.json"
                ).read_text()
            )
            self.assertEqual(status["classification"], "INVALID")
            self.assertFalse(status["admissible"])
            self.assertFalse(status["duration_complete"])
            self.assertIn(
                "planned_duration_not_reached", status["artifact_errors"]
            )

    def test_summary_rejects_short_attempt_even_if_status_claims_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for rate in (5, 20):
                for condition in ("follow", "nadir"):
                    for replicate in (1, 2, 3):
                        write_attempt(
                            runtime,
                            rate,
                            condition,
                            replicate,
                            actual_duration_s=(
                                10.0
                                if rate == 20
                                and condition == "follow"
                                and replicate == 1
                                else 269.0
                            ),
                        )
            with self.assertRaisesRegex(ValueError, "planned duration"):
                summarize_runs(runtime)

    def test_summary_rejects_duplicate_admissible_replicates(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for rate in (5, 20):
                for condition in ("follow", "nadir"):
                    for replicate in (1, 2, 3):
                        write_attempt(runtime, rate, condition, replicate)
            write_attempt(
                runtime,
                20,
                "follow",
                1,
                attempt_suffix="retry-a",
            )
            with self.assertRaisesRegex(ValueError, "duplicates="):
                summarize_runs(runtime)

    def test_summary_blocks_decision_when_20hz_is_unsustainable(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for rate in (5, 20):
                for condition in ("follow", "nadir"):
                    for replicate in (1, 2, 3):
                        write_attempt(
                            runtime,
                            rate,
                            condition,
                            replicate,
                            wall_rate_hz=(
                                18.0
                                if rate == 20
                                and condition == "follow"
                                and replicate == 1
                                else 20.1
                            ),
                        )
            summary = summarize_runs(runtime)
            self.assertEqual(
                summary["decision"]["status"],
                "BLOCKED_RATE_UNSUSTAINABLE",
            )

    def test_summary_fails_s1_closed_without_post_launch_cadence(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for rate in (5, 20):
                for condition in ("follow", "nadir"):
                    for replicate in (1, 2, 3):
                        write_attempt(runtime, rate, condition, replicate)
            summary_path = (
                runtime / "runs" / "rate20-follow-r1" / "summary.json"
            )
            value = json.loads(summary_path.read_text(encoding="utf-8"))
            value.pop("wall_clock_capture_cadence_post_launch")
            summary_path.write_text(json.dumps(value), encoding="utf-8")
            summary = summarize_runs(runtime)
            row = next(
                item
                for item in summary["runs"]
                if item["attempt_id"] == "rate20-follow-r1"
            )
            self.assertFalse(
                row["rate_sustainability"][
                    "s1_wall_capture_rate_ge_19hz"
                ]
            )
            self.assertEqual(
                summary["decision"]["status"],
                "BLOCKED_RATE_UNSUSTAINABLE",
            )

    def test_markdown_reports_raw_and_post_launch_wall_rates(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            write_attempt(
                runtime,
                20,
                "follow",
                1,
                wall_rate_hz=20.125,
            )
            summary = summarize_runs(runtime, strict=False)
            summary["runs"][0]["wall_clock_capture_cadence"][
                "rate_hz"
            ] = 14.625
            report = render_markdown(summary)
            self.assertIn("raw wall Hz", report)
            self.assertIn("S1 post-launch Hz", report)
            self.assertIn("14.625000 | 20.125000", report)


if __name__ == "__main__":
    unittest.main()
