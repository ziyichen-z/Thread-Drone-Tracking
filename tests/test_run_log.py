import json
from pathlib import Path
import tempfile
import unittest

from controller.run_log import (
    RunLogger,
    build_summary,
    finalize_run,
    read_frame_records,
)


def record(frame_id, latency, age, *, event=None, published=False):
    return {
        "frame_id": frame_id,
        "simulation_time_s": float(frame_id),
        "capture_unix_s": 1_800_000_000.0 + frame_id * 0.2,
        "compute_latency_ms": latency,
        "frame_age_ms": age,
        "state": "TRACKING",
        "event": event,
        "compute_stage": "update",
        "backlog_count": 0,
        "skipped_count": 0,
        "published_observation": published,
        "published_gimbal_command": published,
    }


class RunLogTests(unittest.TestCase):
    def test_event_records_are_audited_without_entering_frame_denominators(self):
        records = [
            {
                "frame_id": 1,
                "phase": "measurement",
                "state": "TRACKING",
                "event": None,
                "capture_unix_s": 1.0,
                "capture_monotonic_s": 1.0,
                "simulation_time_s": 1.0,
                "measurement_elapsed_s": 0.0,
            },
            {
                "record_kind": "event",
                "frame_id": 1,
                "phase": "measurement",
                "state": "TRACKING",
                "event": "ROUND_STARTED",
                "capture_unix_s": None,
                "capture_monotonic_s": None,
                "simulation_time_s": None,
                "measurement_elapsed_s": 0.0,
            },
        ]
        summary = build_summary(
            records,
            0,
            release_monotonic_s=1.0,
        )
        self.assertEqual(summary["total_frame_records"], 1)
        self.assertEqual(summary["measurement_frame_records"], 1)
        self.assertEqual(summary["total_event_records"], 1)
        self.assertEqual(summary["event_counts"]["ROUND_STARTED"], 1)

    def test_manifest_frames_and_summary_are_versioned(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            logger = RunLogger(runtime, "follow-test", {"condition": "follow"})
            logger.append(record(1, 10.0, 30.0, published=True))
            logger.append(record(2, 20.0, 40.0, event="GEO_REJECT"))
            logger.snapshot_json("metrics.final.json", {"aggregate": {"c_track": 0.5}})
            summary_path, summary = logger.finalize()
            manifest = json.loads(
                (runtime / "runs" / "follow-test" / "manifest.json").read_text()
            )
            self.assertEqual(manifest["schema_version"], "p1-track-run/v1")
            self.assertEqual(summary["schema_version"], "p1-track-run/v1")
            self.assertEqual(summary["total_frame_records"], 2)
            self.assertEqual(summary["published_observations"], 1)
            self.assertEqual(summary["geo_reject_events"], 1)
            self.assertTrue(summary["metrics_snapshot_present"])
            self.assertEqual(summary["compute_latency_ms"]["p50"], 15.0)
            self.assertEqual(summary["actual_duration_s"], 1.0)
            self.assertAlmostEqual(summary["actual_wall_duration_s"], 0.2)
            self.assertAlmostEqual(
                summary["wall_clock_capture_cadence"]["rate_hz"],
                5.0,
                delta=1e-5,
            )
            self.assertEqual(summary["simulation_time_cadence"]["rate_hz"], 1.0)
            self.assertEqual(summary["backlog_count"]["p95"], 0.0)
            self.assertEqual(summary["time_to_first_lost_s"], 1.0)
            self.assertTrue(summary["time_to_first_lost_right_censored"])
            self.assertTrue(summary_path.is_file())

    def test_summary_reports_time_to_first_lost_and_backlog(self):
        first = record(10, 5.0, 10.0)
        first["simulation_time_s"] = 3.0
        first["capture_unix_s"] = 100.0
        first["backlog_count"] = 0
        lost = record(11, 7.0, 20.0, event="LOST")
        lost["simulation_time_s"] = 3.2
        lost["capture_unix_s"] = 100.2
        lost["backlog_count"] = 2
        lost["state"] = "LOST"
        tail = record(12, 6.0, 15.0)
        tail["simulation_time_s"] = 3.4
        tail["capture_unix_s"] = 100.4
        tail["backlog_count"] = 1
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            logger = RunLogger(runtime, "lost-summary", {})
            for value in (first, lost, tail):
                logger.append(value)
            _, summary = logger.finalize()
            self.assertAlmostEqual(summary["time_to_first_lost_s"], 0.2)
            self.assertFalse(summary["time_to_first_lost_right_censored"])
            self.assertEqual(summary["backlog_count"]["p95"], 1.9)
            self.assertAlmostEqual(
                summary["wall_clock_capture_cadence"]["rate_hz"], 5.0
            )

    def test_post_launch_cadence_excludes_only_prelaunch_records(self):
        records = []
        for frame_id, capture_unix_s in enumerate(
            (0.0, 0.05, 100.50, 100.55, 100.60)
        ):
            value = record(frame_id, 5.0, 10.0)
            value["capture_unix_s"] = capture_unix_s
            records.append(value)
        summary = build_summary(
            records,
            0,
            post_launch_not_before_unix_s=100.0,
        )
        self.assertLess(
            summary["wall_clock_capture_cadence"]["rate_hz"],
            1.0,
        )
        self.assertAlmostEqual(
            summary["wall_clock_capture_cadence_post_launch"]["rate_hz"],
            20.0,
        )
        self.assertEqual(
            summary["wall_clock_capture_window"]["excluded_prelaunch_samples"],
            2,
        )
        self.assertEqual(
            summary["wall_clock_capture_window"]["first_eligible_frame_id"],
            2,
        )

    def test_post_launch_cadence_retains_midrun_stall(self):
        records = []
        for frame_id, capture_unix_s in enumerate((100.10, 100.15, 101.15)):
            value = record(frame_id, 5.0, 10.0)
            value["capture_unix_s"] = capture_unix_s
            records.append(value)
        summary = build_summary(
            records,
            0,
            post_launch_not_before_unix_s=100.0,
        )
        cadence = summary["wall_clock_capture_cadence_post_launch"]
        self.assertAlmostEqual(cadence["rate_hz"], 2.0 / 1.05)
        self.assertAlmostEqual(cadence["interval_s"]["p95"], 0.9525)
        self.assertEqual(
            summary["wall_clock_capture_window"]["excluded_prelaunch_samples"],
            0,
        )

    def test_post_launch_cadence_fails_closed_without_eligible_span(self):
        value = record(1, 5.0, 10.0)
        value["capture_unix_s"] = 99.0
        summary = build_summary(
            [value],
            0,
            post_launch_not_before_unix_s=None,
        )
        cadence = summary["wall_clock_capture_cadence_post_launch"]
        self.assertIsNone(cadence["rate_hz"])
        self.assertEqual(cadence["samples"], 0)
        self.assertIsNone(
            summary["wall_clock_capture_window"]["not_before_unix_s"]
        )

    def test_post_launch_cadence_fails_closed_for_invalid_or_short_cutoff(self):
        value = record(1, 5.0, 10.0)
        value["capture_unix_s"] = 100.1
        for cutoff in (float("nan"), True):
            with self.subTest(cutoff=cutoff):
                summary = build_summary(
                    [value],
                    0,
                    post_launch_not_before_unix_s=cutoff,
                )
                self.assertIsNone(
                    summary[
                        "wall_clock_capture_cadence_post_launch"
                    ]["rate_hz"]
                )
                self.assertIsNone(
                    summary["wall_clock_capture_window"][
                        "not_before_unix_s"
                    ]
                )
        summary = build_summary(
            [value],
            0,
            post_launch_not_before_unix_s=100.0,
        )
        cadence = summary["wall_clock_capture_cadence_post_launch"]
        self.assertEqual(cadence["samples"], 1)
        self.assertIsNone(cadence["rate_hz"])
        self.assertEqual(
            summary["wall_clock_capture_window"]["eligible_samples"],
            1,
        )

    def test_finalize_tolerates_only_a_truncated_tail(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            logger = RunLogger(runtime, "truncated", {})
            logger.append(record(1, 10.0, 20.0))
            logger.close()
            with logger.frames_path.open("a", encoding="utf-8") as handle:
                handle.write('{"frame_id": 2')
            _, summary = finalize_run(runtime, "truncated")
            self.assertEqual(summary["total_frame_records"], 1)
            self.assertEqual(summary["truncated_tail_lines"], 1)

    def test_initialization_latency_and_geo_reject_are_reported_separately(self):
        initialization = record(0, 500.0, 20.0, event="INIT")
        initialization["compute_stage"] = "init"
        initialization["geo_reject_reason"] = "parallel_or_upward_ray"
        update = record(1, 10.0, 20.0)
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            logger = RunLogger(runtime, "latency-split", {})
            logger.append(initialization)
            logger.append(update)
            summary_path, summary = logger.finalize()
            self.assertEqual(summary["initialization_latency_ms"], 500.0)
            self.assertEqual(summary["compute_latency_ms"]["p95"], 10.0)
            self.assertEqual(summary["geo_reject_events"], 1)
            self.assertTrue(summary_path.is_file())

    def test_invalid_json_before_tail_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frames.jsonl"
            path.write_text('{"bad"\n{"frame_id": 2}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "before tail"):
                read_frame_records(path)


if __name__ == "__main__":
    unittest.main()
