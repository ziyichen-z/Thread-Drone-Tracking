"""P1-ENG-FRAME-001 Part P: ``standoff-band-v1`` planner tests.

Acceptance items covered (proposal section 4): AC-11 contract and purity,
AC-12 distance band, AC-13 estimate gate, AC-14 fallback, AC-15 safety
post-processing (method names are the contract's), AC-16 closed reason set,
AC-17 frozen config loading, AC-22 truth isolation (static).

The prism oracle in the property tests is the frozen
``controller.body_planner.segment_intersects_prism``; the planner carries
its own copy of the slab test, so the oracle is independent of it.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import math
from pathlib import Path
import random
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from controller import standoff_planner as standoff_module  # noqa: E402
from controller.body_planner import (  # noqa: E402
    BodyCommand,
    PlatformState,
    ThresholdBodyPlanner,
    WorldEstimate,
    load_corridor_prisms,
    segment_intersects_prism,
)
from controller.standoff_planner import (  # noqa: E402
    MAIN_TAGS,
    MODIFIERS,
    StandoffBodyPlanner,
    StandoffFixed,
    StandoffParams,
    compose_reason,
    load_frame_body_config,
    split_reason,
)
from controller.track_loop import (  # noqa: E402
    _estimator_from_body_config,
    build_argument_parser,
    build_standoff_planner,
)

BODY_CONFIG_PATH = PROJECT_ROOT / "config" / "p1-m3-body-001.json"
FRAME_CONFIG_PATH = PROJECT_ROOT / "config" / "p1-eng-frame-001-body.json"
DEFAULT_SCENARIO_PATH = PROJECT_ROOT / "config" / "scenario.default.json"
UNTETHERED_PATH = PROJECT_ROOT / "config" / "scenario.untethered.json"
PRISMS_PATH = PROJECT_ROOT / "config" / "p1-m3-body-001-corridor-prisms.json"

BODY_CONFIG = json.loads(BODY_CONFIG_PATH.read_text(encoding="utf-8"))
DEFAULT_SCENARIO = json.loads(DEFAULT_SCENARIO_PATH.read_text(encoding="utf-8"))
UNTETHERED_SCENARIO = json.loads(UNTETHERED_PATH.read_text(encoding="utf-8"))
PRISMS = load_corridor_prisms(PRISMS_PATH)
ANCHOR = (132.0, 0.2, 117.0)
FENCE = (110.0, 190.0, 50.0, 130.0)
FIXED = StandoffFixed(
    v_max_mps=4.0,
    target_velocity_clamp_mps=4.0,
    d_plaus_m=65.0,
    obstacle_pad_m=2.1,
    corridor_pad_m=1.0,
    shorten_step_m=0.05,
    min_residual_speed_mps=0.05,
)
C2 = StandoffParams(d_star_m=9.0, band_w_m=3.0, t_lead_s=2.0, k_p_per_s=0.5)


def _both_scenario() -> dict:
    """F-both: default geometry, tether explicitly on, plus the 3.4 fence."""
    document = copy.deepcopy(DEFAULT_SCENARIO)
    document["drone"]["tether_enabled"] = True
    document["drone"]["geofence_xz_m"] = {
        "min_x": FENCE[0],
        "max_x": FENCE[1],
        "min_z": FENCE[2],
        "max_z": FENCE[3],
    }
    return document


def _planner(scenario=None, params: StandoffParams = C2) -> StandoffBodyPlanner:
    return build_standoff_planner(
        BODY_CONFIG,
        UNTETHERED_SCENARIO if scenario is None else scenario,
        params,
        FIXED,
        project_root=PROJECT_ROOT,
    )


def _forward(theta_deg: float, yaw_deg: float) -> tuple[float, float, float]:
    tilt = math.radians(theta_deg)
    yaw = math.radians(yaw_deg)
    return (
        math.sin(yaw) * math.sin(tilt),
        -math.cos(tilt),
        math.cos(yaw) * math.sin(tilt),
    )


def _platform(position=(150.0, 25.2, 90.0), theta_deg=20.0, yaw_deg=0.0) -> PlatformState:
    return PlatformState(
        frame_id=1,
        capture_monotonic_s=1.0,
        position_world_m=tuple(position),
        camera_forward_world=_forward(theta_deg, yaw_deg),
        gimbal_saturated=theta_deg > 45.1,
        tether_saturated=False,
    )


def _estimate(x, z, vx=0.0, vz=0.0, variance=0.25, variance_z=None) -> WorldEstimate:
    position_variance = (variance, variance if variance_z is None else variance_z)
    covariance = tuple(
        tuple(
            (position_variance[row] if row == col and row < 2 else (0.1 if row == col else 0.0))
            for col in range(4)
        )
        for row in range(4)
    )
    return WorldEstimate(mean=(x, z, vx, vz), covariance=covariance, valid_at_monotonic_s=1.0)


def _position_covariance(xx: float, zz: float = 1.0, xz: float = 0.0):
    """A 4x4 covariance with the given position block and unit velocity block."""
    return tuple(
        tuple(
            (xx if (row, col) == (0, 0) else zz if (row, col) == (1, 1)
             else xz if {row, col} == {0, 1} else 1.0 if row == col else 0.0)
            for col in range(4)
        )
        for row in range(4)
    )


def _horizontal(command: BodyCommand) -> tuple[float, float]:
    return command.velocity_world_mps[0], command.velocity_world_mps[2]


def _speed(command: BodyCommand) -> float:
    return math.hypot(*_horizontal(command))


class _RaisingPlatform(PlatformState):
    def limit_margin_deg(self, maximum_off_nadir_deg):  # noqa: D401
        raise ValueError("unconstructible")


class _NanPlatform(PlatformState):
    def limit_margin_deg(self, maximum_off_nadir_deg):
        return float("nan")


class StandoffContractTests(unittest.TestCase):
    """AC-11."""

    def test_contract_holds(self):
        planner = _planner()
        self.assertEqual(planner.decide(None, _estimate(150, 60), 1.0).reason, "hold_no_platform")
        raising = _RaisingPlatform(**_platform().__dict__)
        command = planner.decide(raising, _estimate(150, 60), 1.0)
        self.assertEqual(command.reason, "hold_margin_unconstructible")
        nan_platform = _NanPlatform(**_platform().__dict__)
        command = planner.decide(nan_platform, _estimate(150, 60), 1.0)
        self.assertEqual(command.reason, "hold_margin_unconstructible")
        # A frame where the threshold fallback alone would move (gimbal near
        # its limit) still holds without an estimate: contract (b).
        near_limit = _platform(theta_deg=44.0)
        command = planner.decide(near_limit, None, 1.0)
        self.assertEqual(command.mode, "hold")
        self.assertEqual(command.reason, "hold_no_estimate")
        for command in (planner.decide(None, None, 1.0),):
            self.assertEqual(command.mode, "hold")

    def test_finite_inputs_never_raise_and_keep_contract_fields(self):
        rng = random.Random(11)
        # R1@K2 R1-1: the candidates include 1e200, drawn independently for
        # x and z so that a huge finite variance also meets a small one.
        variances = (1e-6, 0.25, 4.0, 1e6, 1e200)
        for planner in (_planner(), _planner(DEFAULT_SCENARIO), _planner(_both_scenario())):
            for _ in range(1500):
                body = (
                    rng.uniform(60.0, 220.0),
                    ANCHOR[1] + rng.uniform(0.0, 60.0),
                    rng.uniform(20.0, 180.0),
                )
                platform = _platform(body, rng.uniform(0.0, 89.0), rng.uniform(-180.0, 180.0))
                estimate = _estimate(
                    rng.uniform(-1e4, 1e4),
                    rng.uniform(-1e4, 1e4),
                    rng.uniform(-50.0, 50.0),
                    rng.uniform(-50.0, 50.0),
                    variance=rng.choice(variances),
                    variance_z=rng.choice(variances),
                )
                command = planner.decide(platform, estimate, 1.0)
                self.assertEqual(command.velocity_world_mps[1], 0.0)
                self.assertEqual(command.expires_after_s, 0.4)
                self.assertLessEqual(_speed(command), 4.0 + 1e-9)

    def test_large_finite_covariance_holds_without_raising(self):
        """R1@K2 R1-1: a huge but finite covariance holds, it never raises."""
        covariances = {
            "diag(1e155,1,1,1)": _position_covariance(1e155),
            "diag(1e200,1,1,1)": _position_covariance(1e200),
            "diag(float_max,1,1,1)": _position_covariance(sys.float_info.max),
            "off-diagonal 1e200 (symmetric)": _position_covariance(1.0, 1.0, 1e200),
        }
        # Platform 25 m above the anchor with the gimbal far from its limit
        # (no fallback velocity); the estimate is 10 m away.
        platform = _platform(position=(ANCHOR[0], ANCHOR[1] + 25.0, ANCHOR[2]), theta_deg=20.0)
        planners = {
            "untethered": _planner(),
            "default": _planner(DEFAULT_SCENARIO),
            "F-both": _planner(_both_scenario()),
        }
        for scenario_name, planner in planners.items():
            for label, covariance in covariances.items():
                estimate = WorldEstimate(
                    mean=(ANCHOR[0] + 10.0, ANCHOR[2], 0.0, 0.0),
                    covariance=covariance,
                    valid_at_monotonic_s=1.0,
                )
                with self.subTest(scenario=scenario_name, covariance=label):
                    command = planner.decide(platform, estimate, 1.0)
                    self.assertEqual(command.mode, "hold")
                    self.assertEqual(split_reason(command.reason)[0], "hold_estimate_uncertain")
                    self.assertEqual(command.velocity_world_mps[1], 0.0)
                    self.assertEqual(command.expires_after_s, 0.4)

    def test_ordered_replay_through_a_fresh_instance_reproduces_commands(self):
        rng = random.Random(5)
        sequence = []
        for index in range(400):
            body = (130.0 + 30 * math.sin(index / 30), 25.2, 90.0 + 25 * math.cos(index / 40))
            sequence.append(
                (
                    _platform(body, 20.0 + 26.0 * math.sin(index / 13.0), index * 3.0),
                    None if index % 37 == 0 else _estimate(
                        150 + 40 * math.sin(index / 25), 90 + 35 * math.cos(index / 25),
                        rng.uniform(-2, 2), rng.uniform(-2, 2),
                    ),
                )
            )
        first = _planner()
        second = _planner()
        outputs = [first.decide(p, e, 1.0) for p, e in sequence]
        replayed = [second.decide(p, e, 1.0) for p, e in sequence]
        self.assertEqual(outputs, replayed)
        self.assertGreater(sum(c.mode == "velocity_world" for c in outputs), 50)

    def test_decide_path_does_no_io_clock_or_truth(self):
        source = inspect.getsource(StandoffBodyPlanner)
        for token in (
            "open(",
            "json.",
            "read_text",
            "Path(",
            "time.",
            "datetime",
            "input(",
            "metrics.json",
            "m3_body_truth",
            "route_world_m",
            "random",
        ):
            self.assertNotIn(token, source, token)

    def test_module_imports_only_contract_types_from_body_planner(self):
        tree = ast.parse(Path(standoff_module.__file__).read_text(encoding="utf-8"))
        allowed_stdlib = {"__future__", "dataclasses", "hashlib", "json", "math", "pathlib", "typing"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level == 1:
                    self.assertEqual(node.module, "body_planner")
                    self.assertTrue(
                        {alias.name for alias in node.names}
                        <= {"CONTRACT_VERSION", "BodyCommand", "BodyPlanner", "PlatformState", "WorldEstimate"},
                        [alias.name for alias in node.names],
                    )
                else:
                    self.assertIn(node.module, allowed_stdlib)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name, allowed_stdlib)


class DistanceBandTests(unittest.TestCase):
    """AC-12 (C2: d* = 9, w = 3, T_lead = 2, k_p = 0.5)."""

    BODY = (150.0, 25.2, 90.0)

    def test_far_target_latches_and_commands_proportional_speed(self):
        planner = _planner()
        # Static target 15 m east: d = 15 > d* + w = 12.
        command = planner.decide(_platform(self.BODY), _estimate(165.0, 90.0), 1.0)
        self.assertEqual(command.reason, "follow_move")
        self.assertAlmostEqual(_speed(command), 0.5 * (15.0 - 9.0))
        vx, vz = _horizontal(command)
        self.assertAlmostEqual(vz, 0.0)
        self.assertGreater(vx, 0.0)
        self.assertTrue(planner.following)

    def test_speed_is_clamped_to_v_max(self):
        planner = _planner()
        command = planner.decide(_platform(self.BODY), _estimate(150.0, 50.0), 1.0)
        self.assertEqual(command.reason, "follow_move")
        self.assertAlmostEqual(_speed(command), 4.0)

    def test_latch_hysteresis_band(self):
        planner = _planner()
        body = _platform(self.BODY)
        # In band from the unlatched initial state: hold.
        self.assertEqual(planner.decide(body, _estimate(160.5, 90.0), 1.0).reason, "in_band_hold")
        # Beyond d* + w: latch on.
        self.assertEqual(planner.decide(body, _estimate(163.0, 90.0), 1.0).reason, "follow_move")
        # Back inside the band (still > d*): stays latched and keeps following.
        command = planner.decide(body, _estimate(160.5, 90.0), 1.0)
        self.assertEqual(command.reason, "follow_move")
        self.assertAlmostEqual(_speed(command), 0.5 * 1.5)
        # At or inside d*: latch off, hold.
        self.assertEqual(planner.decide(body, _estimate(159.0, 90.0), 1.0).reason, "in_band_hold")
        self.assertFalse(planner.following)
        self.assertEqual(planner.decide(body, _estimate(160.5, 90.0), 1.0).reason, "in_band_hold")

    def test_lead_uses_the_clamped_estimate_velocity(self):
        planner = _planner()
        # Target 8 m east moving east at 2 m/s: predicted 8 + 2*2 = 12 m.
        command = planner.decide(_platform(self.BODY), _estimate(158.0, 90.0, 2.0, 0.0), 1.0)
        self.assertEqual(command.reason, "in_band_hold")
        planner = _planner()
        # 10 m/s is clamped to 4 m/s: predicted 8 + 2*4 = 16 m -> 3.5 m/s.
        command = planner.decide(_platform(self.BODY), _estimate(158.0, 90.0, 10.0, 0.0), 1.0)
        self.assertEqual(command.reason, "follow_move")
        self.assertAlmostEqual(_speed(command), 0.5 * (16.0 - 9.0))

    def test_near_side_never_backs_away(self):
        planner = _planner()
        for x, z, vx, vz in (
            (150.0, 90.0, 0.0, 0.0),
            (153.0, 92.0, -2.0, -1.0),
            (148.0, 88.0, 2.0, 2.0),
            (155.0, 90.0, -2.0, 0.0),
        ):
            command = planner.decide(_platform(self.BODY), _estimate(x, z, vx, vz), 1.0)
            self.assertEqual(command.mode, "hold", (x, z, vx, vz))
            self.assertEqual(command.reason, "in_band_hold")

    def test_turning_target_is_led_towards_the_predicted_point(self):
        planner = _planner()
        # Target 14 m east, heading north (+z) at 2 m/s: predicted point
        # (164, 94); the command points there, not at the current position.
        command = planner.decide(_platform(self.BODY), _estimate(164.0, 90.0, 0.0, 2.0), 1.0)
        self.assertEqual(command.reason, "follow_move")
        vx, vz = _horizontal(command)
        self.assertAlmostEqual(math.atan2(vz, vx), math.atan2(4.0, 14.0))


class EstimateGateTests(unittest.TestCase):
    """AC-13."""

    BODY = _platform((150.0, 25.2, 90.0))

    def test_sigma_above_band_width_holds(self):
        planner = _planner()
        command = planner.decide(self.BODY, _estimate(170.0, 90.0, variance=3.1**2), 1.0)
        self.assertEqual(command.reason, "hold_estimate_uncertain")
        command = planner.decide(self.BODY, _estimate(170.0, 90.0, variance=2.9**2), 1.0)
        self.assertEqual(command.reason, "follow_move")

    def test_correlated_covariance_uses_the_largest_eigenvalue(self):
        planner = _planner()
        covariance = (
            (5.0, 4.5, 0.0, 0.0),
            (4.5, 5.0, 0.0, 0.0),
            (0.0, 0.0, 0.1, 0.0),
            (0.0, 0.0, 0.0, 0.1),
        )  # eigenvalues 9.5 / 0.5 -> sigma 3.08 > 3
        estimate = WorldEstimate(mean=(170.0, 90.0, 0.0, 0.0), covariance=covariance, valid_at_monotonic_s=1.0)
        self.assertEqual(planner.decide(self.BODY, estimate, 1.0).reason, "hold_estimate_uncertain")

    def test_non_finite_components_hold(self):
        planner = _planner()
        for mean in ((float("nan"), 90.0, 0.0, 0.0), (170.0, 90.0, float("inf"), 0.0)):
            estimate = WorldEstimate(mean=mean, covariance=_estimate(0, 0).covariance, valid_at_monotonic_s=1.0)
            self.assertEqual(planner.decide(self.BODY, estimate, 1.0).reason, "hold_estimate_uncertain")
        covariance = [list(row) for row in _estimate(0, 0).covariance]
        covariance[3][2] = float("nan")
        estimate = WorldEstimate(
            mean=(170.0, 90.0, 0.0, 0.0),
            covariance=tuple(tuple(row) for row in covariance),
            valid_at_monotonic_s=1.0,
        )
        self.assertEqual(planner.decide(self.BODY, estimate, 1.0).reason, "hold_estimate_uncertain")

    def test_implausible_predicted_distance_holds(self):
        planner = _planner()
        command = planner.decide(self.BODY, _estimate(150.0, 90.0 - 65.5), 1.0)
        self.assertEqual(command.reason, "hold_estimate_implausible")
        command = planner.decide(self.BODY, _estimate(150.0, 90.0 - 64.5), 1.0)
        self.assertEqual(command.reason, "follow_move")
        # The lead counts: 60 m now, 2 s at 4 m/s more -> 68 m predicted.
        planner = _planner()
        command = planner.decide(self.BODY, _estimate(150.0, 30.0, 0.0, -4.0), 1.0)
        self.assertEqual(command.reason, "hold_estimate_implausible")


class FallbackTests(unittest.TestCase):
    """AC-14."""

    def _independent(self, tethered: bool) -> ThresholdBodyPlanner:
        return ThresholdBodyPlanner(
            margin_trigger_deg=10.0,
            margin_release_deg=20.0,
            v_cmd_mps=4.0,
            expires_after_s=0.4,
            maximum_off_nadir_deg=45.0,
            anchor_world_m=ANCHOR,
            corridor_prisms=PRISMS if tethered else None,
            corridor_radius_m=1.0 if tethered else None,
        )

    def _sequence(self, tethered: bool):
        rng = random.Random(3 if tethered else 4)
        sequence = []
        for index in range(500):
            if tethered:
                angle = index / 40.0
                radius = 10.0 + 12.0 * abs(math.sin(index / 70.0))
                body = (ANCHOR[0] + radius * math.cos(angle), 25.2, ANCHOR[2] + radius * math.sin(angle))
            else:
                body = (150.0 + 30 * math.sin(index / 50), 25.2, 90.0 + 30 * math.cos(index / 60))
            theta = 25.0 + 20.0 * math.sin(index / 11.0)
            estimate = None if index % 41 == 0 else _estimate(
                body[0] + rng.uniform(-10, 10), body[2] + rng.uniform(-10, 10)
            )
            sequence.append((_platform(body, theta, rng.uniform(-180, 180)), estimate))
        return sequence

    def test_embedded_fallback_runs_every_frame_like_a_standalone_instance(self):
        for tethered, scenario in ((False, UNTETHERED_SCENARIO), (True, DEFAULT_SCENARIO)):
            with self.subTest(tethered=tethered):
                planner = _planner(scenario)
                independent = self._independent(tethered)
                moved = 0
                for platform, estimate in self._sequence(tethered):
                    planner.decide(platform, estimate, 1.0)
                    expected = independent.decide(platform, estimate, 1.0)
                    self.assertEqual(planner.last_fallback_command, expected)
                    moved += expected.mode == "velocity_world"
                    if not tethered:
                        self.assertNotIn("+corridor", planner.last_fallback_command.reason)
                self.assertGreater(moved, 20)

    def test_embedded_instance_corridor_by_mode(self):
        untethered = _planner(UNTETHERED_SCENARIO)._fallback
        self.assertIsNone(untethered._corridor_prisms)
        self.assertIsNone(untethered._corridor_radius_m)
        tethered = _planner(DEFAULT_SCENARIO)._fallback
        self.assertEqual(tethered._corridor_prisms, PRISMS)
        self.assertEqual(tethered._corridor_radius_m, 1.0)
        self.assertEqual(tethered._margin_trigger_deg, 10.0)
        self.assertEqual(tethered._margin_release_deg, 20.0)
        self.assertEqual(tethered._v_cmd_mps, 4.0)
        self.assertEqual(tethered._expires_after_s, 0.4)

    def test_fallback_velocity_is_adopted_only_when_following_holds(self):
        body = (150.0, 25.2, 90.0)
        near_limit = _platform(body, theta_deg=40.0, yaw_deg=90.0)
        # In band (target 10 m east) + margin 5 deg < 10 deg trigger.
        planner = _planner()
        independent = self._independent(False)
        command = planner.decide(near_limit, _estimate(160.0, 90.0), 1.0)
        expected = independent.decide(near_limit, _estimate(160.0, 90.0), 1.0)
        self.assertEqual(expected.mode, "velocity_world")
        self.assertEqual(command.reason, "fallback_margin")
        self.assertAlmostEqual(command.velocity_world_mps[0], expected.velocity_world_mps[0])
        self.assertAlmostEqual(command.velocity_world_mps[2], expected.velocity_world_mps[2])
        # Uncertain estimate + margin below trigger: fallback adopted too.
        planner = _planner()
        command = planner.decide(near_limit, _estimate(170.0, 90.0, variance=16.0), 1.0)
        self.assertEqual(command.reason, "fallback_margin")
        # Following wins when the band says move.
        planner = _planner()
        command = planner.decide(near_limit, _estimate(150.0, 70.0), 1.0)
        self.assertEqual(command.reason, "follow_move")
        self.assertLess(command.velocity_world_mps[2], 0.0)

    def test_tethered_fallback_matches_the_corridor_threshold(self):
        planner = _planner(DEFAULT_SCENARIO)
        independent = self._independent(True)
        platform = _platform((140.0, 25.2, 110.0), theta_deg=40.0, yaw_deg=45.0)
        estimate = _estimate(148.0, 115.0)
        planner.decide(platform, estimate, 1.0)
        self.assertEqual(planner.last_fallback_command, independent.decide(platform, estimate, 1.0))


def _segment_hits(start, end, prisms, pad) -> bool:
    lo = [min(start[a], end[a]) - pad for a in range(3)]
    hi = [max(start[a], end[a]) + pad for a in range(3)]
    for prism in prisms:
        if any(prism[a] > hi[a] or prism[a + 3] < lo[a] for a in range(3)):
            continue
        if segment_intersects_prism(start, end, prism, pad_m=pad):
            return True
    return False


class SafetyPostprocessPropertyTests(unittest.TestCase):
    """AC-15: three seeded fixtures, assertions by the enabled constraints."""

    def _run(self, scenario, count: int, seed: int, sample_body):
        planner = _planner(scenario)
        rng = random.Random(seed)
        outputs = []
        for _ in range(count):
            body = sample_body(rng)
            angle = rng.uniform(-math.pi, math.pi)
            radius = rng.uniform(0.0, 80.0)
            estimate = _estimate(
                body[0] + radius * math.cos(angle),
                body[2] + radius * math.sin(angle),
                rng.uniform(-3.0, 3.0),
                rng.uniform(-3.0, 3.0),
                variance=rng.choice((0.04, 0.25, 1.0, 4.0)),
            )
            platform = _platform(body, rng.uniform(0.0, 50.0), rng.uniform(-180.0, 180.0))
            outputs.append((body, planner.decide(platform, estimate, 1.0)))
        counts: dict[str, int] = {}
        for _, command in outputs:
            main, modifiers = split_reason(command.reason)
            key = command.mode + ":" + main
            counts[key] = counts.get(key, 0) + 1
            for tag in modifiers:
                counts[tag] = counts.get(tag, 0) + 1
        print(f"\nAC-15 fixture seed={seed} n={count} counts={json.dumps(counts, sort_keys=True)}")
        return outputs

    @staticmethod
    def _candidate(body, command):
        return (
            body[0] + command.velocity_world_mps[0] * 0.4,
            body[1],
            body[2] + command.velocity_world_mps[2] * 0.4,
        )

    @staticmethod
    def _reach(body) -> float:
        h = body[1] - ANCHOR[1]
        return math.sqrt(max(0.0, 35.0**2 - h * h))

    def _sample_disc(self, rng):
        angle = rng.uniform(-math.pi, math.pi)
        radius = 60.0 * math.sqrt(rng.random())
        return (
            ANCHOR[0] + radius * math.cos(angle),
            ANCHOR[1] + rng.uniform(8.0, 32.0),
            ANCHOR[2] + radius * math.sin(angle),
        )

    def _sample_fence_box(self, rng):
        return (
            rng.uniform(FENCE[0] - 20.0, FENCE[1] + 20.0),
            ANCHOR[1] + rng.uniform(8.0, 32.0),
            rng.uniform(FENCE[2] - 20.0, FENCE[3] + 20.0),
        )

    def _assert_tethered(self, outputs, *, fence_allowed: bool, min_velocities: int):
        velocities = 0
        for body, command in outputs:
            if command.mode != "velocity_world":
                continue
            velocities += 1
            candidate = self._candidate(body, command)
            self.assertLessEqual(
                math.hypot(candidate[0] - ANCHOR[0], candidate[2] - ANCHOR[2]),
                self._reach(body) + 1e-6,
            )
            self.assertFalse(_segment_hits(ANCHOR, candidate, PRISMS, 1.0))
            if not fence_allowed:
                self.assertNotIn("+geofence_limited", command.reason)
        if not fence_allowed:
            self.assertFalse(any("+geofence_limited" in c.reason for _, c in outputs))
        # Sanity: enough non-hold outputs for the assertions to bite.
        self.assertGreaterEqual(velocities, min_velocities)

    def _assert_fence(self, outputs):
        for body, command in outputs:
            if command.mode != "velocity_world":
                continue
            candidate = self._candidate(body, command)
            self.assertTrue(FENCE[0] <= candidate[0] <= FENCE[1], candidate)
            self.assertTrue(FENCE[2] <= candidate[2] <= FENCE[3], candidate)

    def test_tethered_reach_circle_and_corridor(self):
        outputs = self._run(DEFAULT_SCENARIO, 10_000, 1501, self._sample_disc)
        self._assert_tethered(outputs, fence_allowed=False, min_velocities=500)

    def test_untethered_fence_without_reach_circle(self):
        outputs = self._run(UNTETHERED_SCENARIO, 10_000, 1502, self._sample_fence_box)
        self._assert_fence(outputs)
        beyond_reach = 0
        for body, command in outputs:
            self.assertNotIn("+tether_limited", command.reason)
            self.assertNotIn("+corridor_", command.reason)
            if command.mode != "velocity_world":
                continue
            candidate = self._candidate(body, command)
            if math.hypot(candidate[0] - ANCHOR[0], candidate[2] - ANCHOR[2]) > self._reach(body):
                beyond_reach += 1
        self.assertGreaterEqual(beyond_reach, 100)

    def test_fence_stacks_on_tether(self):
        outputs = self._run(_both_scenario(), 1_000, 1503, self._sample_disc)
        self._assert_tethered(outputs, fence_allowed=True, min_velocities=50)
        self._assert_fence(outputs)

    def test_obstacle_clearance_all_fixtures(self):
        fixtures = (
            (DEFAULT_SCENARIO, 10_000, 1501, self._sample_disc),
            (UNTETHERED_SCENARIO, 10_000, 1502, self._sample_fence_box),
            (_both_scenario(), 1_000, 1503, self._sample_disc),
        )
        for scenario, count, seed, sampler in fixtures:
            blocked = 0
            for body, command in self._run(scenario, count, seed, sampler):
                if command.mode == "velocity_world":
                    self.assertFalse(
                        _segment_hits(body, self._candidate(body, command), PRISMS, 2.1),
                        (seed, body, command),
                    )
                elif "+obstacle_blocked" in command.reason:
                    blocked += 1
            print(f"AC-15 (d) seed={seed} obstacle_blocked_holds={blocked}")


class ReasonClosedSetTests(unittest.TestCase):
    """AC-16."""

    def test_compose_orders_modifiers_and_rejects_unknown_tags(self):
        self.assertEqual(
            compose_reason("follow_move", {"+corridor_shortened", "+tether_limited", "+obstacle_shortened"}),
            "follow_move+tether_limited+obstacle_shortened+corridor_shortened",
        )
        with self.assertRaises(ValueError):
            compose_reason("moving", set())
        with self.assertRaises(ValueError):
            compose_reason("follow_move", {"+fence"})

    def test_split_rejects_out_of_order_or_unknown(self):
        self.assertEqual(split_reason("in_band_hold"), ("in_band_hold", ()))
        for bad in (
            "follow_move+obstacle_shortened+tether_limited",
            "follow_move+unknown",
            "margin_below_trigger",
            "follow_move+tether_limited+tether_limited",
        ):
            with self.assertRaises(ValueError):
                split_reason(bad)

    def test_every_output_reason_is_in_the_closed_set(self):
        rng = random.Random(16)
        for scenario in (UNTETHERED_SCENARIO, DEFAULT_SCENARIO, _both_scenario()):
            planner = _planner(scenario)
            seen = set()
            for _ in range(3000):
                body = (rng.uniform(90, 210), ANCHOR[1] + rng.uniform(8, 32), rng.uniform(30, 150))
                estimate = None if rng.random() < 0.05 else _estimate(
                    body[0] + rng.uniform(-70, 70), body[2] + rng.uniform(-70, 70),
                    rng.uniform(-5, 5), rng.uniform(-5, 5),
                    variance=rng.choice((0.25, 16.0)),
                )
                platform = None if rng.random() < 0.02 else _platform(body, rng.uniform(0, 60), rng.uniform(-180, 180))
                command = planner.decide(platform, estimate, 1.0)
                main, modifiers = split_reason(command.reason)
                self.assertIn(main, MAIN_TAGS)
                self.assertTrue(set(modifiers) <= set(MODIFIERS))
                seen.add(main)
            self.assertTrue({"follow_move", "in_band_hold", "hold_no_estimate"} <= seen, seen)


class FrameConfigLoaderTests(unittest.TestCase):
    """AC-17."""

    def _write(self, directory: Path, document: dict) -> Path:
        path = directory / "frame.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def test_checked_in_config_loads_and_pins_body_001(self):
        frame = load_frame_body_config(FRAME_CONFIG_PATH, project_root=PROJECT_ROOT)
        raw = json.loads(FRAME_CONFIG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            set(raw),
            {"schema_version", "work_id", "planner", "selected_candidate", "params", "fixed",
             "body_001_config", "replay_evidence"},
        )
        self.assertEqual(raw["schema_version"], "p1-eng-frame-001-body/v1")
        self.assertEqual(raw["planner"], "standoff-band-v1")
        self.assertEqual(raw["body_001_config"]["path"], "config/p1-m3-body-001.json")
        self.assertEqual(
            raw["body_001_config"]["sha256"],
            hashlib.sha256(BODY_CONFIG_PATH.read_bytes()).hexdigest(),
        )
        self.assertEqual(frame.fixed, FIXED)
        self.assertEqual(frame.body_001_config, BODY_CONFIG)

    def test_built_runtime_reuses_body_001_values_verbatim(self):
        frame = load_frame_body_config(FRAME_CONFIG_PATH, project_root=PROJECT_ROOT)
        planner = build_standoff_planner(
            frame.body_001_config, UNTETHERED_SCENARIO, frame.params, frame.fixed,
            project_root=PROJECT_ROOT,
        )
        self.assertEqual(planner.expires_after_s, BODY_CONFIG["command"]["expires_after_s"])
        fallback = planner._fallback
        policy = BODY_CONFIG["policy"]
        self.assertEqual(fallback._margin_trigger_deg, policy["margin_trigger_deg"])
        self.assertEqual(fallback._margin_release_deg, policy["margin_release_deg"])
        self.assertEqual(fallback._v_cmd_mps, policy["v_cmd_mps"])
        estimator = _estimator_from_body_config(frame.body_001_config, PROJECT_ROOT)
        self.assertEqual(estimator.sigma_px, BODY_CONFIG["calibration"]["sigma_px"])
        self.assertEqual(estimator.q_accel_mps2, BODY_CONFIG["estimator"]["q_accel_mps2"])
        self.assertEqual(estimator.sigma_att_deg, BODY_CONFIG["estimator"]["sigma_att_deg"])
        self.assertEqual(estimator.sigma_y_m, BODY_CONFIG["estimator"]["sigma_y_m"])
        self.assertEqual(
            estimator.initial_velocity_sigma_mps,
            BODY_CONFIG["estimator"]["initial_velocity_sigma_mps"],
        )

    def test_tampering_is_rejected(self):
        raw = json.loads(FRAME_CONFIG_PATH.read_text(encoding="utf-8"))

        def mutated(change):
            document = copy.deepcopy(raw)
            change(document)
            return document

        cases = {
            "schema": mutated(lambda d: d.__setitem__("schema_version", "p1-eng-frame-001-body/v2")),
            "body sha": mutated(lambda d: d["body_001_config"].__setitem__("sha256", "0" * 64)),
            "replay sha": mutated(lambda d: d["replay_evidence"].__setitem__("sha256", "1" * 64)),
            "missing field": mutated(lambda d: d.pop("fixed")),
            "extra field": mutated(lambda d: d.__setitem__("override", 1)),
            "missing param": mutated(lambda d: d["params"].pop("k_p_per_s")),
            "non-finite param": mutated(lambda d: d["params"].__setitem__("d_star_m", float("nan"))),
            "non-positive fixed": mutated(lambda d: d["fixed"].__setitem__("d_plaus_m", 0.0)),
            "bool param": mutated(lambda d: d["params"].__setitem__("band_w_m", True)),
            "candidate": mutated(lambda d: d.__setitem__("selected_candidate", "C4")),
            "planner": mutated(lambda d: d.__setitem__("planner", "threshold-corridor-v1")),
            "absolute path": mutated(lambda d: d["body_001_config"].__setitem__("path", str(BODY_CONFIG_PATH))),
        }
        with tempfile.TemporaryDirectory() as directory:
            for name, document in cases.items():
                with self.subTest(name):
                    path = Path(directory) / f"{name.replace(' ', '_')}.json"
                    path.write_text(json.dumps(document), encoding="utf-8")
                    with self.assertRaises((ValueError, KeyError)):
                        load_frame_body_config(path, project_root=PROJECT_ROOT)

    def test_no_cli_override_of_planner_values(self):
        options = {
            option
            for action in build_argument_parser()._actions
            for option in action.option_strings
        }
        for token in ("d-star", "band", "t-lead", "k-p", "v-max", "standoff-param"):
            self.assertFalse(any(token in option for option in options), token)


class TruthIsolationTests(unittest.TestCase):
    """AC-22 (static): runtime modules read no evaluator output or truth."""

    def test_runtime_modules_name_no_truth_source(self):
        for name in ("standoff_planner.py", "scenario_tether.py"):
            source = (PROJECT_ROOT / "controller" / name).read_text(encoding="utf-8")
            for token in ("metrics.json", "m3_body_truth", "route_world_m"):
                self.assertNotIn(token, source, f"{name}: {token}")

    def test_standoff_construction_path_reads_no_route_or_evaluator_output(self):
        """AC-22 修订 1 (CLARIFY): pin only the new standoff construction path.

        ``_build_standoff_runtime`` and the helpers this work item added to
        ``controller/track_loop.py`` must not touch the target route (or any
        evaluator output); the ground plane comes only from the explicit
        ``ground_plane_y_m``. The frozen ``_build_body_runtime`` hold/threshold
        path is deliberately not scanned (proposal 待裁定, AC-22 修订 1).
        """
        from controller import track_loop

        functions = (
            track_loop._build_standoff_runtime,
            track_loop.build_standoff_planner,
            track_loop._estimator_from_body_config,
        )
        for function in functions:
            source = inspect.getsource(function)
            for token in (
                "route",
                "target",
                "metrics.json",
                "m3_body_truth",
                "truth",
                "evaluator",
            ):
                self.assertFalse(token in source, f"{function.__name__} names {token!r}")

    def test_scenario_tether_imports_only_stdlib(self):
        tree = ast.parse((PROJECT_ROOT / "controller" / "scenario_tether.py").read_text(encoding="utf-8"))
        allowed = {"__future__", "dataclasses", "hashlib", "math", "pathlib", "typing"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0)
                self.assertIn(node.module, allowed)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name, allowed)


if __name__ == "__main__":
    unittest.main()
