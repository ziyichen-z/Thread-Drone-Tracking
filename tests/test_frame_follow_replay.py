"""P1-ENG-FRAME-001 Part P (P3): replay tool, plant mirror and frozen choice.

Acceptance items covered (proposal section 4):

* AC-19 - the float32 plant mirror agrees with the golden vectors that the
  Edit Mode ``TetheredDronePlantTests.Step_TetheredGoldenVectors`` /
  ``Step_UntetheredGoldenVectors`` assert against the real Unity plant
  (same literals, <= 1e-5 m), and with the Unity-validated literals of the
  two pre-existing plant tests; a same-seed rerun is byte-identical; the
  checked-in evidence covers the full pre-registered grid and its
  selection follows the pre-registered rule;
* AC-20 - the frozen FRAME config equals the evidence's selection, pins the
  evidence by hash, and the Play operator sheet carries the section 3.11
  entry list.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.frame_follow_replay import (  # noqa: E402
    ALTITUDES_M,
    CANDIDATES,
    EVIDENCE_JSON,
    FIXED,
    NOISE_CONDITIONS,
    POLICIES,
    TETHER_MODES,
    UnityPlantMirror,
    analyze_run,
    evidence_bytes,
    hard_checks,
    percentile,
    random_plant_commands,
    run_replay,
    select_candidate,
    start_stop_count,
    stationary_fraction,
)

FRAME_CONFIG_PATH = PROJECT_ROOT / "config" / "p1-eng-frame-001-body.json"
UNTETHERED_SCENARIO_PATH = PROJECT_ROOT / "config" / "scenario.untethered.json"
DEFAULT_SCENARIO_PATH = PROJECT_ROOT / "config" / "scenario.default.json"
EVIDENCE_PATH = PROJECT_ROOT / EVIDENCE_JSON
PLAY_OPS_PATH = PROJECT_ROOT / "docs" / "evidence" / "P1-ENG-FRAME-001-play-ops.md"

#: Parameter sets shared with the Edit Mode golden-vector tests.
PARAMS = {
    "TP": dict(anchor=(0, 0, 0), tether_length=35, minimum_altitude=8, maximum_altitude=32,
               maximum_speed=4, maximum_acceleration=4, position=(0, 25, 0),
               tether_enabled=True, geofence=None),
    "UP": dict(anchor=(0, 0, 0), tether_length=10, minimum_altitude=8, maximum_altitude=32,
               maximum_speed=4, maximum_acceleration=4, position=(0, 25, 0),
               tether_enabled=False, geofence=(-22, 58, -67, 13)),
    "RT": dict(anchor=(0, 0, 0), tether_length=10, minimum_altitude=2, maximum_altitude=8,
               maximum_speed=4, maximum_acceleration=4, position=(0, 5, 0),
               tether_enabled=True, geofence=None),
    "RU": dict(anchor=(0, 0, 0), tether_length=3, minimum_altitude=2, maximum_altitude=8,
               maximum_speed=4, maximum_acceleration=4, position=(0, 5, 0),
               tether_enabled=False, geofence=(-6, 6, -4, 8)),
}

#: name -> (parameter set, commands): scripted segments or a random seed.
SEQUENCES = {
    "GT1": ("TP", [((4, 0, 0), 100)]),
    "GT2": ("TP", [((4, 0, 3), 2000)]),
    "GT3": ("TP", [((0, 4, 0), 500), ((0, -4, 0), 1000)]),
    "GT4": ("TP", [((4, 0, 0), 400), ((0, 0, 4), 400)]),
    "GT5": ("RT", 0x2545F491),
    "GU1": ("UP", [((4, 0, 0), 1000)]),
    "GU2": ("UP", [((0, 4, 0), 500), ((0, -4, 0), 1000)]),
    "GU3": ("UP", [((-3, 0, -4), 1500)]),
    "GU4": ("RU", 0x9E3779B9),
}

# Golden vectors: (step, position, applied velocity, tether saturated).
GOLDEN = {
    "GT1": [
        (10, (0.0879999846, 25, 0), (0.799999893, 0, 0), False),
        (20, (0.335999995, 25, 0), (1.60000014, 0, 0), False),
        (30, (0.743999958, 25, 0), (2.39999986, 0, 0), False),
        (40, (1.3119998, 25, 0), (3.19999909, 0, 0), False),
        (50, (2.03999949, 25, 0), (3.99999833, 0, 0), False),
        (60, (2.83999872, 25, 0), (4, 0, 0), False),
        (70, (3.63999796, 25, 0), (4, 0, 0), False),
        (80, (4.4399972, 25, 0), (4, 0, 0), False),
        (90, (5.23999643, 25, 0), (4, 0, 0), False),
        (100, (6.03999567, 25, 0), (4, 0, 0), False),
    ],
    "GT2": [
        (250, (14.4320173, 25, 10.8240108), (3.20000005, 0, 2.4000001), False),
        (500, (19.59589, 25, 14.6969757), (3.20000005, 0, 2.4000001), True),
        (750, (19.59589, 25, 14.6969757), (3.20000005, 0, 2.4000001), True),
        (1000, (19.59589, 25, 14.6969757), (3.20000005, 0, 2.4000001), True),
        (1250, (19.59589, 25, 14.6969757), (3.20000005, 0, 2.4000001), True),
        (1500, (19.59589, 25, 14.6969757), (3.20000005, 0, 2.4000001), True),
        (1750, (19.59589, 25, 14.6969757), (3.20000005, 0, 2.4000001), True),
        (2000, (19.59589, 25, 14.6969757), (3.20000005, 0, 2.4000001), True),
    ],
    "GT3": [
        (250, (0, 32, 0), (0, 4, 0), False),
        (500, (0, 32, 0), (0, 4, 0), False),
        (750, (0, 17.9600124, 0), (0, -4, 0), False),
        (1000, (0, 8, 0), (0, -4, 0), False),
        (1250, (0, 8, 0), (0, -4, 0), False),
        (1500, (0, 8, 0), (0, -4, 0), False),
    ],
    "GT4": [
        (100, (6.03999567, 25, 0), (4, 0, 0), False),
        (200, (14.0399885, 25, 0), (4, 0, 0), False),
        (300, (22.0399818, 25, 0), (4, 0, 0), False),
        (400, (24.4948978, 25, 0), (4, 0, 0), True),
        (500, (23.9620972, 25, 5.0811305), (0, 0, 4), True),
        (600, (21.3439598, 25, 12.0181236), (0, 0, 4), True),
        (700, (17.5433311, 25, 17.0947819), (0, 0, 4), True),
        (800, (13.6484098, 25, 20.3401318), (0, 0, 4), True),
    ],
    "GU1": [
        (100, (6.03999567, 25, 0), (4, 0, 0), False),
        (200, (14.0399885, 25, 0), (4, 0, 0), False),
        (300, (22.0399818, 25, 0), (4, 0, 0), False),
        (400, (30.0399742, 25, 0), (4, 0, 0), False),
        (500, (38.0401115, 25, 0), (4, 0, 0), False),
        (600, (46.0402946, 25, 0), (4, 0, 0), False),
        (700, (54.0404778, 25, 0), (4, 0, 0), False),
        (800, (58, 25, 0), (4, 0, 0), False),
        (900, (58, 25, 0), (4, 0, 0), False),
        (1000, (58, 25, 0), (4, 0, 0), False),
    ],
    "GU2": [
        (250, (0, 32, 0), (0, 4, 0), False),
        (500, (0, 32, 0), (0, 4, 0), False),
        (750, (0, 17.9600124, 0), (0, -4, 0), False),
        (1000, (0, 8, 0), (0, -4, 0), False),
        (1250, (0, 8, 0), (0, -4, 0), False),
        (1500, (0, 8, 0), (0, -4, 0), False),
    ],
    "GU3": [
        (250, (-10.8240108, 25, -14.4320173), (-2.4000001, 0, -3.20000005), False),
        (500, (-22, 25, -30.4318352), (-2.4000001, 0, -3.20000005), False),
        (750, (-22, 25, -46.4316292), (-2.4000001, 0, -3.20000005), False),
        (1000, (-22, 25, -62.4314232), (-2.4000001, 0, -3.20000005), False),
        (1250, (-22, 25, -67), (-2.4000001, 0, -3.20000005), False),
        (1500, (-22, 25, -67), (-2.4000001, 0, -3.20000005), False),
    ],
    "GT5": [
        (100, (0.519257009, 4.05134153, -4.60377693), (0.153559178, -0.433554888, -0.860100508), False),
        (200, (1.27687144, 2.5350132, -0.833194196), (-0.416952521, -0.667861342, 3.0893147), False),
        (300, (-0.334574133, 2, -1.31887376), (-0.303861678, -0.362520397, -1.04750013), False),
        (400, (4.44619226, 2, -3.60124016), (2.84949875, -1.02996123, -1.69780946), False),
        (500, (6.13281345, 2, -7.64124393), (0.215932488, -0.0979860201, -0.0370391011), True),
        (600, (7.4738431, 2, -5.89801025), (-0.285673857, -1.06080639, 1.8880918), False),
        (700, (6.85658503, 2, -5.77157831), (-0.84620893, -0.245325789, -2.74192381), False),
        (800, (4.56154537, 2.87072921, -8.42325497), (-1.65329504, 0.77787751, -2.63765621), True),
        (900, (1.22841585, 3.2162075, -9.38866329), (-0.523528695, -0.246588632, -2.35964012), True),
        (1000, (0.720393121, 3.69406033, -9.26471519), (0, 0, 0), False),
    ],
    "GU4": [
        (100, (3.66593957, 5.74986649, -3.29295897), (2.37924504, 1.63427246, -0.0278320611), False),
        (200, (3.48592257, 6.39644527, -3.58467913), (-2.44546962, 0.968946815, -0.113235362), False),
        (300, (-1.9059552, 8, -4), (-0.545584559, 1.13389969, -0.920637548), False),
        (400, (-0.357191235, 8, -3.82422161), (1.27530098, 0.647857368, 1.0493114), False),
        (500, (0.430335164, 8, -2.76775002), (-0.494385391, 0.661547244, 1.10971653), False),
        (600, (1.82742918, 8, -0.812999606), (-0.109506994, 0.392788291, 0.367884785), False),
        (700, (3.14223123, 7.82431364, -3.05586004), (-0.84871769, -0.46538192, -0.503107965), False),
        (800, (-0.337541521, 7.16489172, -4), (0, 0, 0), False),
        (900, (-0.342940629, 7.52480316, -4), (0, 0, 0), False),
        (1000, (-0.319679201, 6.51986837, -1.03227425), (-2.09782743, 0.332731903, 1.53960145), False),
    ],
}


def _commands(spec):
    if isinstance(spec, int):
        return random_plant_commands(spec, 1000)
    commands = []
    for velocity, steps in spec:
        commands.extend([velocity] * steps)
    return commands


def _run_mirror(name):
    key, spec = SEQUENCES[name]
    plant = UnityPlantMirror(**PARAMS[key])
    states = {}
    for index, command in enumerate(_commands(spec), start=1):
        if command is None:
            plant.hold()
        else:
            plant.set_velocity(command)
        plant.step(0.02)
        states[index] = (plant.position, plant.applied, plant.tether_saturated)
    return states


class PlantMirrorGoldenTests(unittest.TestCase):
    """AC-19: mirror vs the Edit Mode golden vectors (<= 1e-5 m)."""

    def _check(self, names):
        for name in names:
            states = _run_mirror(name)
            for step, position, applied, saturated in GOLDEN[name]:
                with self.subTest(sequence=name, step=step):
                    actual_position, actual_applied, actual_saturated = states[step]
                    for axis in range(3):
                        self.assertAlmostEqual(actual_position[axis], position[axis], delta=1e-5)
                        self.assertAlmostEqual(actual_applied[axis], applied[axis], delta=1e-5)
                    self.assertIs(actual_saturated, saturated)

    def test_tethered_mirror_matches_ac2_golden_vectors(self):
        self._check(("GT1", "GT2", "GT3", "GT4", "GT5"))

    def test_untethered_mirror_matches_ac4_golden_vectors(self):
        self._check(("GU1", "GU2", "GU3", "GU4"))

    def test_mirror_reproduces_the_unity_validated_existing_examples(self):
        # Literals of TetheredDronePlantTests.Step_ClampsCommandSpeedAndAcceleration
        # and Step_ClampsAltitudeAndTetherSphere (pre-existing, Unity-run).
        base = dict(anchor=(0, 0, 0), tether_length=10, minimum_altitude=2,
                    maximum_altitude=8, maximum_speed=4)
        plant = UnityPlantMirror(**base, maximum_acceleration=2, position=(0, 5, 0))
        plant.set_velocity((100, 0, 0))
        plant.step(0.5)
        self.assertAlmostEqual(plant.applied[0], 1.0, delta=1e-6)
        self.assertAlmostEqual(plant.position[0], 0.5, delta=1e-6)
        self.assertAlmostEqual(plant.position[1], 5.0, delta=1e-6)
        horizontal = UnityPlantMirror(**base, maximum_acceleration=100, position=(0, 8, 0))
        horizontal.set_velocity((4, 0, 0))
        horizontal.step(10)
        self.assertAlmostEqual(horizontal.position[0], 6.0, delta=1e-5)
        self.assertAlmostEqual(horizontal.position[1], 8.0, delta=1e-5)
        self.assertAlmostEqual(math.dist(horizontal.position, (0, 0, 0)), 10.0, delta=1e-5)
        self.assertTrue(horizontal.tether_saturated)
        low = UnityPlantMirror(**base, maximum_acceleration=100, position=(0, 5, 0))
        low.set_velocity((0, -4, 0))
        low.step(10)
        self.assertAlmostEqual(low.position[1], 2.0, delta=1e-5)
        high = UnityPlantMirror(**base, maximum_acceleration=100, position=(0, 5, 0))
        high.set_velocity((0, 4, 0))
        high.step(10)
        self.assertAlmostEqual(high.position[1], 8.0, delta=1e-5)

    def test_untethered_mode_differs_from_tethered_on_the_same_sequence(self):
        tethered = dict(PARAMS["UP"], tether_enabled=True, geofence=None)
        states_on = {}
        plant = UnityPlantMirror(**tethered)
        for index, command in enumerate(_commands(SEQUENCES["GU1"][1]), start=1):
            plant.set_velocity(command)
            plant.step(0.02)
            states_on[index] = plant.position
        self.assertLessEqual(math.dist(states_on[1000], (0, 0, 0)), 10.0 + 1e-4)
        self.assertGreater(math.dist(_run_mirror("GU1")[1000][0], (0, 0, 0)), 35.0)


class ReadOutFunctionTests(unittest.TestCase):
    def test_start_stop_counting(self):
        self.assertEqual(start_stop_count([0.0, 0.5, 1.5, 0.1, 0.15, 2.0, 0.0, 0.9, 1.1]), 3)
        self.assertEqual(start_stop_count([2.0, 2.0, 0.5, 2.0]), 0)
        self.assertEqual(start_stop_count([]), 0)

    def test_stationary_fraction_and_percentile(self):
        self.assertAlmostEqual(stationary_fraction([0.0, 0.1, 0.3, 2.0]), 0.5)
        self.assertIsNone(stationary_fraction([]))
        self.assertAlmostEqual(percentile([1, 2, 3, 4], 0.5), 2.5)
        self.assertAlmostEqual(percentile([4, 1, 3, 2], 0.1), 1.3)
        self.assertIsNone(percentile([], 0.5))


def _checks(h1=0.0, h2=30.0, frames=0, fraction=0.0, h4=2, h5=0.05):
    loop2 = {
        "R2_gimbal_saturated_fraction": h1,
        "R5_range": {"short_side_px_p10": h2},
        "fence_violation_frames": frames,
        "inside_inflated_prism_frames": 0,
        "R6_reasons": {"boundary_obstacle_modifier_fraction": fraction},
        "R4_body_motion": {"start_stop_count": h4, "stationary_fraction": h5},
    }
    return hard_checks(loop2)


class SelectionRuleTests(unittest.TestCase):
    def test_hard_check_limits(self):
        self.assertTrue(_checks()["all_pass"])
        self.assertFalse(_checks(h1=0.0051)["H1"]["pass"])
        self.assertTrue(_checks(h1=0.005)["H1"]["pass"])
        self.assertFalse(_checks(h2=23.99)["H2"]["pass"])
        self.assertFalse(_checks(frames=1)["H3"]["pass"])
        self.assertFalse(_checks(fraction=0.0101)["H3"]["pass"])
        self.assertTrue(_checks(h4=5)["H4"]["pass"])
        self.assertFalse(_checks(h4=6)["H4"]["pass"])
        self.assertFalse(_checks(h5=0.1001)["H5"]["pass"])

    def test_shortest_path_with_three_percent_ties(self):
        def entry(path, stops, ok=True):
            return {"checks": _checks() if ok else _checks(h1=1.0), "path_length_m": path, "start_stop_count": stops}

        chosen = select_candidate({"C1": entry(200, 1), "C2": entry(190, 3), "C3": entry(170, 4)})
        self.assertEqual(chosen["selected_candidate"], "C3")
        tie = select_candidate({"C1": entry(200, 1), "C2": entry(171, 2), "C3": entry(170, 4)})
        self.assertEqual(tie["selected_candidate"], "C2")
        self.assertEqual(tie["tied"], ["C2", "C3"])
        number = select_candidate({"C1": entry(170, 2), "C2": entry(171, 2), "C3": entry(170.5, 2)})
        self.assertEqual(number["selected_candidate"], "C1")
        none = select_candidate({"C1": entry(170, 1, ok=False)})
        self.assertIsNone(none["selected_candidate"])
        self.assertEqual(none["outcome"], "NO_CANDIDATE_PASSES")


class ReplayDeterminismTests(unittest.TestCase):
    def test_same_seed_rerun_is_byte_identical(self):
        first = evidence_bytes(run_replay(duration_s=6.0, policies=("C3", "hold")))
        second = evidence_bytes(run_replay(duration_s=6.0, policies=("C3", "hold")))
        self.assertEqual(first, second)


class ReplayEvidenceTests(unittest.TestCase):
    """AC-19: the checked-in evidence covers the grid and follows the rule."""

    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    def test_full_pre_registered_grid(self):
        cells = {
            (row["policy"], row["altitude_m"], row["tether"], row["noise"])
            for row in self.evidence["grid"]
        }
        expected = {
            (p, a, t, n)
            for p in POLICIES for a in ALTITUDES_M for t in TETHER_MODES for n in NOISE_CONDITIONS
        }
        self.assertEqual(cells, expected)
        self.assertEqual(len(self.evidence["grid"]), 60)
        self.assertEqual(len({row["seed"] for row in self.evidence["grid"]}), 60)
        self.assertEqual(self.evidence["candidates"], CANDIDATES)
        self.assertEqual(self.evidence["fixed"], FIXED)

    def test_inputs_are_the_current_files(self):
        for item in self.evidence["inputs"].values():
            digest = hashlib.sha256((PROJECT_ROOT / item["path"]).read_bytes()).hexdigest()
            self.assertEqual(digest, item["sha256"], item["path"])

    def test_selection_reapplies_to_the_recorded_cell(self):
        rows = {
            row["policy"]: row
            for row in self.evidence["grid"]
            if row["altitude_m"] == 25.0 and row["tether"] == "untethered" and row["noise"] == "E1"
            and row["policy"] in CANDIDATES
        }
        per_candidate = {
            cid: {
                "checks": hard_checks(row["loop2"]),
                "path_length_m": row["loop2"]["R4_body_motion"]["path_length_m"],
                "start_stop_count": row["loop2"]["R4_body_motion"]["start_stop_count"],
            }
            for cid, row in rows.items()
        }
        recomputed = select_candidate(per_candidate)
        selection = self.evidence["selection"]
        self.assertEqual(recomputed["selected_candidate"], selection["selected_candidate"])
        self.assertEqual(recomputed["tied"], selection["tied"])
        self.assertEqual(selection["outcome"], "SELECTED")
        self.assertEqual(
            selection["selected_params"], CANDIDATES[selection["selected_candidate"]]
        )


class FrozenParametersTests(unittest.TestCase):
    """AC-20: parameters frozen from the evidence before any Play."""

    def test_config_equals_the_replay_selection(self):
        config = json.loads(FRAME_CONFIG_PATH.read_text(encoding="utf-8"))
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(config["selected_candidate"], evidence["selection"]["selected_candidate"])
        self.assertEqual(config["params"], evidence["selection"]["selected_params"])
        self.assertEqual(config["fixed"], evidence["fixed"])
        self.assertEqual(config["replay_evidence"]["path"], EVIDENCE_JSON)
        self.assertEqual(
            config["replay_evidence"]["sha256"],
            hashlib.sha256(EVIDENCE_PATH.read_bytes()).hexdigest(),
        )

    def test_play_operator_sheet_lists_the_section_3_11_entries(self):
        sheet = PLAY_OPS_PATH.read_text(encoding="utf-8")
        for token in (
            "tools/run_track_experiment.py",
            "--print-only",
            "--body-policy standoff",
            "--body-planner-config config/p1-eng-frame-001-body.json",
            "--body-scenario-config config/scenario.untethered.json",
            "runtime/scenario_config.json",
            "runtime/hold-",
            "Loaded tethered scenario 'deterministic-loop-untethered' from",
            "config/scenario.untethered.json",
            "shasum -a 256 config/p1-eng-frame-001-body.json",
        ):
            self.assertIn(token, sheet, token)


class AnalyzeRunTests(unittest.TestCase):
    """The Play read-out mode runs the same summary code on run artifacts.

    The run directory comes from the production writers: the ``body_planner``
    identity is the fourth return value of ``controller.track_loop.
    _build_body_runtime(..., "standoff", ...)`` and ``manifest.json`` /
    ``frames.jsonl`` are written by ``controller.run_log.RunLogger`` (the same
    path ``track_loop`` uses). Only the evaluator truth sidecar, which Unity
    writes, is synthesised.
    """

    RUN_ID = "frame-test"

    def _production_run(self, runtime: Path, *, with_body_planner: bool = True):
        from controller.run_log import RunLogger
        from controller.track_loop import _build_body_runtime

        manifest = {"run_id": self.RUN_ID, "scenario_id": "deterministic-loop-untethered"}
        identity = None
        if with_body_planner:
            identity = _build_body_runtime(
                FRAME_CONFIG_PATH,
                UNTETHERED_SCENARIO_PATH,
                "standoff",
                scenario_id="deterministic-loop-untethered",
                ground_plane_y_m=0.2,
                runtime=runtime,
            )[3]
            manifest["body_planner"] = identity
        logger = RunLogger(runtime, self.RUN_ID, manifest=manifest)
        try:
            for record in self._frames():
                logger.append(record)
        finally:
            logger.close()
        return logger.run_directory, identity

    @staticmethod
    def _frames():
        return [
            {
                "record_kind": "frame",
                "frame_id": index,
                "body_planner": {
                    "reason": "follow_move" if index % 4 else "in_band_hold",
                    "velocity_world_mps": [1.0, 0.0, 0.5] if index % 4 else [0.0, 0.0, 0.0],
                },
            }
            for index in range(40)
        ]

    @staticmethod
    def _truth_records():
        return [
            {
                "frame_id": index,
                "simulation_time_s": index * 0.2,
                "body_world_x_m": 132.0 + index * 0.2,
                "body_world_y_m": 25.2,
                "body_world_z_m": 117.0,
                "target_world_x_m": 140.0 + index * 0.4,
                "target_world_y_m": 0.2,
                "target_world_z_m": 117.0,
                "applied_velocity_x_mps": 1.0,
                "applied_velocity_z_mps": 0.0,
                "gimbal_saturated": False,
                "tether_saturated": False,
                "truth_box_available": True,
                "truth_box_width": 0.05,
                "truth_box_height": 0.07,
                "target_center_error_px": 3.0,
            }
            for index in range(40)
        ]

    def _write_truth(self, runtime: Path) -> Path:
        truth_path = runtime / "m3_body_truth.jsonl"
        truth_path.write_text(
            "".join(json.dumps(r) + "\n" for r in self._truth_records()), encoding="utf-8"
        )
        return truth_path

    def test_analyze_run_refuses_a_scenario_that_differs_from_the_manifest(self):
        """R1@K2 R1-2 (section 3.11 entry 8): the analysis binds the manifest's scenario."""
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as bare:
            runtime = Path(directory)
            run, identity = self._production_run(runtime)
            truth_path = self._write_truth(runtime)
            # Red: the legacy tethered default is not the scenario the run used.
            with self.assertRaisesRegex(ValueError, "sha256"):
                analyze_run(run, truth_path, None, DEFAULT_SCENARIO_PATH)
            # Green: the scenario the manifest pins.
            result = analyze_run(run, truth_path, None, UNTETHERED_SCENARIO_PATH)
            binding = result["scenario_binding"]
            self.assertEqual(
                binding["analysed_scenario_sha256"],
                hashlib.sha256(UNTETHERED_SCENARIO_PATH.read_bytes()).hexdigest(),
            )
            self.assertEqual(binding["analysed_scenario_sha256"], identity["scenario_config_sha256"])
            self.assertEqual(binding["analysed_scenario_sha256"], identity["effective_scenario_sha256"])
            self.assertEqual(binding["effective_scenario_path"], identity["effective_scenario_path"])
            self.assertEqual(binding["scenario_config_path"], identity["scenario_config_path"])
            self.assertEqual(result["scenario_id"], "deterministic-loop-untethered")
            # A manifest without the body planner's scenario identity cannot
            # be bound at all, so it is refused too.
            bare_run, _ = self._production_run(Path(bare), with_body_planner=False)
            with self.assertRaisesRegex(ValueError, "body_planner"):
                analyze_run(bare_run, truth_path, None, UNTETHERED_SCENARIO_PATH)

    def test_synthetic_run_produces_read_outs(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            run, _ = self._production_run(runtime)
            truth_path = self._write_truth(runtime)
            metrics_path = runtime / "metrics.json"
            metrics_path.write_text(json.dumps({"summary": {"c_track": 0.75}}), encoding="utf-8")
            result = analyze_run(run, truth_path, metrics_path, UNTETHERED_SCENARIO_PATH)
        self._assert_read_outs(result)

    def test_r7_reads_archived_unity_aggregate_c_track(self):
        """AC-21: consume the preserved evaluator's actual metrics bytes."""
        metrics_bytes = (
            PROJECT_ROOT / "tests/fixtures/frame_follow_metrics_unity.json"
        ).read_bytes()
        metrics = json.loads(metrics_bytes)
        self.assertEqual(metrics["schema_version"], "tethered-evaluation/v1")
        result = self._analyze_metrics_bytes(metrics_bytes)
        self.assertEqual(result["R7_c_track"], round(metrics["aggregate"]["c_track"], 6))
        self.assertNotEqual(
            result["R7_c_track"], round(metrics["aggregate"]["c_track_given_geom"], 6)
        )

    def test_r7_preserves_legacy_precedence_null_zero_and_missing_values(self):
        cases = [
            ({"c_track": 0.125, "summary": {"c_track": 0.25},
              "aggregate": {"c_track": 0.5}}, 0.125),
            ({"summary": {"c_track": 0.25}, "aggregate": {"c_track": 0.5}}, 0.25),
            ({"c_track": None, "aggregate": {"c_track": 0.5}}, None),
            ({"summary": {"c_track": None}, "aggregate": {"c_track": 0.5}}, None),
            ({"c_track": 0.0, "aggregate": {"c_track": 0.5}}, 0.0),
            ({"summary": {"c_track": 0.0}, "aggregate": {"c_track": 0.5}}, 0.0),
            ({"aggregate": {"c_track": 0.0}}, 0.0),
            ({"aggregate": {}}, None),
            ({}, None),
        ]
        for metrics, expected in cases:
            with self.subTest(metrics=metrics):
                result = self._analyze_metrics_bytes(json.dumps(metrics).encode("utf-8"))
                self.assertEqual(result["R7_c_track"], expected)

    def test_r7_does_not_infer_a_metrics_file_when_path_is_omitted(self):
        self.assertIsNone(self._analyze_metrics_bytes(None)["R7_c_track"])

    def _analyze_metrics_bytes(self, metrics_bytes):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            run, _ = self._production_run(runtime)
            truth_path = self._write_truth(runtime)
            # A final snapshot must never silently replace the explicit input
            # or supply a metric when the caller requested no metrics.
            (run / "metrics.final.json").write_bytes(
                (PROJECT_ROOT / "tests/fixtures/frame_follow_metrics_unity.json").read_bytes()
            )
            metrics_path = None
            if metrics_bytes is not None:
                metrics_path = runtime / "metrics.json"
                metrics_path.write_bytes(metrics_bytes)
            return analyze_run(run, truth_path, metrics_path, UNTETHERED_SCENARIO_PATH)

    def _assert_read_outs(self, result):
        self.assertEqual(result["R7_c_track"], 0.75)
        safety = result["safety_read_outs"]
        self.assertEqual(safety["T_fence_violation_frames"], 0)
        self.assertEqual(safety["T_tether_saturated_frames"], 0)
        self.assertEqual(safety["T_altitude_outside_initial_pm_0_05_frames"], 0)
        self.assertAlmostEqual(safety["P_command_speed_max_mps"], math.hypot(1.0, 0.5), places=6)
        self.assertEqual(safety["P_command_vy_max_abs_mps"], 0.0)
        reasons = result["read_outs"]["all"]["R6_reasons"]
        self.assertEqual(reasons["decisions"], 40)
        self.assertAlmostEqual(reasons["main_fraction"]["in_band_hold"], 0.25)
        self.assertEqual(result["read_outs"]["all"]["R1_center_error_px"]["p50"], 3.0)


if __name__ == "__main__":
    unittest.main()
