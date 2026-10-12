import contextlib
import hashlib
import io
import json
from pathlib import Path
import unittest

from tools.run_track_experiment import (
    DEFAULT_SCENARIO,
    PROJECT_ROOT,
    load_scenario,
    main as run_track_experiment_main,
    tracker_command,
    two_loop_duration_s,
)


class ExperimentRunnerTests(unittest.TestCase):
    def test_duration_is_computed_by_orchestration(self):
        duration = two_loop_duration_s(load_scenario(DEFAULT_SCENARIO))
        self.assertGreater(duration, 260.0)
        self.assertLess(duration, 280.0)

    def test_tracker_command_receives_only_scalar_orchestration_values(self):
        command = tracker_command(
            python_executable=Path("/python"),
            runtime=Path("/runtime"),
            init_frame=12,
            init_box=(0.1, 0.2, 0.3, 0.4),
            track_id="target-0",
            scenario_id="scenario-a",
            condition="follow",
            ground_plane_y_m=0.6,
            planned_duration_s=270.0,
            run_id="run-a",
            rate_study={
                "rate_hz": 20,
                "replicate_index": 2,
                "replicate_id": "rate20-follow-r2",
                "attempt_id": "rate20-follow-r2",
                "loop_duration_s": 105.0,
                "scenario_config_sha256": "a" * 64,
                "init_image_sha256": "b" * 64,
                "reference_image_sha256": "c" * 64,
                "reference_frame_id": 12,
                "reference_simulation_time_s": 3.2,
            },
        )
        joined = " ".join(command)
        self.assertIn("--scenario-id scenario-a", joined)
        self.assertIn("--planned-duration-s 270.0", joined)
        self.assertNotIn("route_world_m", joined)
        self.assertNotIn("speed_mps", joined)
        self.assertIn("--rate-study-rate-hz 20", joined)
        self.assertIn("--rate-study-replicate 2", joined)
        self.assertIn("--loop-duration-s 105.0", joined)
        self.assertIn("--tracker csrt", joined)

    def test_nanotrack_selector_and_model_paths_are_forwarded(self):
        command = tracker_command(
            python_executable=Path("/python"),
            runtime=Path("/runtime"),
            init_frame=12,
            init_box=(0.1, 0.2, 0.3, 0.4),
            track_id="target-0",
            scenario_id="scenario-a",
            condition="follow",
            ground_plane_y_m=0.6,
            planned_duration_s=30.0,
            run_id="pilot-a",
            tracker="nanotrack-v2",
            tracker_model_spec=Path("/identity/models.json"),
            tracker_model_dir=Path("/models/nanotrack-v2"),
        )
        joined = " ".join(command)
        self.assertIn("--tracker nanotrack-v2", joined)
        self.assertIn(
            "--tracker-model-spec /identity/models.json",
            joined,
        )
        self.assertIn(
            "--tracker-model-dir /models/nanotrack-v2",
            joined,
        )


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class DefaultScenarioEntryTests(unittest.TestCase):
    """P1-ENG-FRAME-001 AC-28: the harness default is the untethered file."""

    INIT_BOX = ("0.2765625", "0.40625", "0.1203125", "0.15208333333333332")

    def _print_only(self, *extra: str) -> str:
        argv = [
            "--print-only",
            "--tracker",
            "nanotrack-v2",
            "--init-frame",
            "0",
            "--init-box",
            *self.INIT_BOX,
            "--track-id",
            "target-0",
            "--condition",
            "follow",
            "--ground-plane-y-m",
            "0.2",
            "--python",
            "/python",
            "--runtime",
            "/runtime",
            *extra,
        ]
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            run_track_experiment_main(argv)
        return buffer.getvalue()

    def _expected_output(self, scenario_id: str, sha256: str) -> str:
        # Literal pre-change values of the two-loop timing for the shared
        # default route (both files carry the same route).
        planned = 272.97056274847716
        command = [
            "/python",
            "-m",
            "controller.track_loop",
            "--runtime",
            str(Path("/runtime").resolve()),
            "--tracker",
            "nanotrack-v2",
            "--init-frame",
            "0",
            "--init-box",
            *self.INIT_BOX,
            "--track-id",
            "target-0",
            "--scenario-id",
            scenario_id,
            "--condition",
            "follow",
            "--ground-plane-y-m",
            "0.2",
            "--planned-duration-s",
            str(planned),
            "--tracker-model-spec",
            str(PROJECT_ROOT / "config" / "nanotrack-v2.models.json"),
            "--tracker-model-dir",
            str(PROJECT_ROOT / "runtime" / "models" / "nanotrack-v2"),
        ]
        return (
            json.dumps(
                {
                    "scenario_id": scenario_id,
                    "condition": "follow",
                    "planned_duration_s": planned,
                    "loop_duration_s": 106.48528137423858,
                    "scenario_config_sha256": sha256,
                    "command": command,
                },
                indent=2,
            )
            + "\n"
        )

    def test_default_constant_is_the_untethered_scenario(self):
        self.assertEqual(
            DEFAULT_SCENARIO, PROJECT_ROOT / "config" / "scenario.untethered.json"
        )

    def test_default_print_only_reports_the_untethered_scenario(self):
        untethered = PROJECT_ROOT / "config" / "scenario.untethered.json"
        output = self._print_only()
        self.assertEqual(
            output,
            self._expected_output("deterministic-loop-untethered", _sha256(untethered)),
        )
        document = json.loads(output)
        self.assertEqual(document["scenario_id"], "deterministic-loop-untethered")
        self.assertEqual(document["scenario_config_sha256"], _sha256(untethered))

    def test_explicit_legacy_default_output_is_unchanged(self):
        legacy = PROJECT_ROOT / "config" / "scenario.default.json"
        output = self._print_only("--scenario-config", str(legacy))
        self.assertEqual(
            output,
            self._expected_output("deterministic-loop-default", _sha256(legacy)),
        )

    def test_harness_forwards_no_body_planner_arguments(self):
        document = json.loads(self._print_only())
        for token in document["command"]:
            self.assertFalse(token.startswith("--body-"), token)


if __name__ == "__main__":
    unittest.main()
