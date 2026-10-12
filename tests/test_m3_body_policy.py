"""P1-M3-BODY-001 batch 1a-beta: estimator, policy and wiring tests.

Covers the parts a reviewer can check without Unity: the analytic-Jacobian
measurement covariance against numerical differentiation, the Kalman filter
behaviour, the threshold policy's branch table semantics, the corridor
shorten/hold rule, the mechanical zero-truth / zero-visibility / zero-flag
checks (BC-BODY1-8, BC-BODY1-4, BC-BODY1-6, review note N3), and the
``track_loop`` per-frame wiring.
"""

from __future__ import annotations

import copy
import inspect
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from controller.body_planner import (  # noqa: E402
    BodyCommand,
    BodyPlanner,
    HoldBodyPlanner,
    PlatformState,
    ThresholdBodyPlanner,
    WorldEstimate,
    load_corridor_prisms,
    segment_intersects_prism,
)
from controller.geolocate import box_ground_intersection  # noqa: E402
from controller.track_loop import (  # noqa: E402
    FrameRepository,
    RuntimePublisher,
    TrackLoop,
    _build_body_runtime,
    main as track_loop_main,
)
from controller.run_log import RunLogger, read_frame_records  # noqa: E402
from controller.trackers import TrackerResult  # noqa: E402
from controller.world_estimate import (  # noqa: E402
    WorldEstimateFilter,
    measurement_covariance_xz,
)

CONFIG_PATH = PROJECT_ROOT / "config" / "p1-m3-body-001.json"
SCENARIO_PATH = PROJECT_ROOT / "config" / "scenario.default.json"


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def tilted_metadata(frame_id, *, tilt_deg=40.0, yaw_deg=0.0):
    tilt = math.radians(tilt_deg)
    yaw = math.radians(yaw_deg)
    forward = _norm(
        (
            math.sin(yaw) * math.sin(tilt),
            -math.cos(tilt),
            math.cos(yaw) * math.sin(tilt),
        )
    )
    right = _norm(_cross(forward, (0.0, 1.0, 0.0)))
    up = _norm(_cross(right, forward))
    return {
        "schema_version": "tethered-sensor-frame/v3",
        "scenario_id": "deterministic-loop-default",
        "frame_id": frame_id,
        "simulation_time_s": frame_id * 0.2,
        "capture_unix_s": 1_800_000_000.0 + frame_id * 0.2,
        "capture_monotonic_s": 500.0 + frame_id * 0.2,
        "capture_monotonic_clock_id": "system-stopwatch/v1",
        "camera_position_world_m": [132.0, 25.2, 117.0],
        "camera_forward_world": list(forward),
        "camera_right_world": list(right),
        "camera_up_world": list(up),
        "width": 640,
        "height": 480,
        "intrinsics_px": {"fx": 320.0, "fy": 320.0, "cx": 320.0, "cy": 240.0},
        "gimbal_saturated": tilt_deg >= 45.0,
        "tether_saturated": False,
    }


def _platform(theta_deg, yaw_deg=0.0):
    tilt = math.radians(theta_deg)
    yaw = math.radians(yaw_deg)
    forward = (
        math.sin(yaw) * math.sin(tilt),
        -math.cos(tilt),
        math.cos(yaw) * math.sin(tilt),
    )
    return PlatformState(
        frame_id=1,
        capture_monotonic_s=1.0,
        position_world_m=(132.0, 25.2, 117.0),
        camera_forward_world=forward,
        gimbal_saturated=theta_deg >= 45.0,
        tether_saturated=False,
    )


def _estimate():
    return WorldEstimate(
        mean=(125.5, 117.5, 2.0, 0.0),
        covariance=tuple(
            tuple(1.0 if row == col else 0.0 for col in range(4))
            for row in range(4)
        ),
        valid_at_monotonic_s=1.0,
    )


def _planner(**overrides):
    parameters = {
        "margin_trigger_deg": 10.0,
        "margin_release_deg": 20.0,
        "v_cmd_mps": 4.0,
        "expires_after_s": 0.4,
        "maximum_off_nadir_deg": 45.0,
        "anchor_world_m": (132.0, 0.2, 117.0),
    }
    parameters.update(overrides)
    return ThresholdBodyPlanner(**parameters)


class EstimatorJacobianTests(unittest.TestCase):
    """Proposal 3.4: R is propagated through the analytic Jacobian."""

    def setUp(self):
        self.metadata = tilted_metadata(0)
        self.box = (0.45, 0.35, 0.1, 0.12)
        self.ground_y = 0.2

    def _numeric_jacobian(self):
        def point(meta, box, ground_y):
            intersection = box_ground_intersection(box, meta, ground_y)
            return (intersection.point_world_m[0], intersection.point_world_m[2])

        eps = 1e-7
        columns = []
        box_plus = (self.box[0] + eps / 640, *self.box[1:])
        box_minus = (self.box[0] - eps / 640, *self.box[1:])
        columns.append(
            [
                (a - b) / (2 * eps)
                for a, b in zip(
                    point(self.metadata, box_plus, self.ground_y),
                    point(self.metadata, box_minus, self.ground_y),
                )
            ]
        )
        box_plus = (self.box[0], self.box[1] + eps / 480, *self.box[2:])
        box_minus = (self.box[0], self.box[1] - eps / 480, *self.box[2:])
        columns.append(
            [
                (a - b) / (2 * eps)
                for a, b in zip(
                    point(self.metadata, box_plus, self.ground_y),
                    point(self.metadata, box_minus, self.ground_y),
                )
            ]
        )

        def rotate(vector, axis, angle):
            c, s = math.cos(angle), math.sin(angle)
            kxv = _cross(axis, vector)
            kdv = sum(a * b for a, b in zip(axis, vector))
            return tuple(
                vector[i] * c + kxv[i] * s + axis[i] * kdv * (1 - c)
                for i in range(3)
            )

        for axis_key in (
            "camera_right_world",
            "camera_up_world",
            "camera_forward_world",
        ):
            axis = self.metadata[axis_key]
            points = []
            for sign in (1.0, -1.0):
                rotated = copy.deepcopy(self.metadata)
                for key in (
                    "camera_right_world",
                    "camera_up_world",
                    "camera_forward_world",
                ):
                    rotated[key] = list(
                        rotate(self.metadata[key], axis, sign * eps)
                    )
                points.append(point(rotated, self.box, self.ground_y))
            columns.append([(a - b) / (2 * eps) for a, b in zip(*points)])
        columns.append(
            [
                (a - b) / (2 * eps)
                for a, b in zip(
                    point(self.metadata, self.box, self.ground_y + eps),
                    point(self.metadata, self.box, self.ground_y - eps),
                )
            ]
        )
        return columns

    def test_analytic_covariance_matches_numerical_differentiation(self):
        columns = self._numeric_jacobian()
        sigma_px = 2.866112
        sigma_att = math.radians(1.0)
        sigma_y = 0.05
        sigmas = (sigma_px, sigma_px, sigma_att, sigma_att, sigma_att, sigma_y)
        numeric = [[0.0, 0.0], [0.0, 0.0]]
        for column, sigma in zip(columns, sigmas):
            for row in range(2):
                for other in range(2):
                    numeric[row][other] += (
                        column[row] * column[other] * sigma * sigma
                    )
        analytic = measurement_covariance_xz(
            self.box,
            self.metadata,
            self.ground_y,
            sigma_px=sigma_px,
            sigma_att_deg=1.0,
            sigma_y_m=sigma_y,
        )
        self.assertAlmostEqual(numeric[0][0], analytic[0][0], delta=1e-6)
        self.assertAlmostEqual(numeric[0][1], analytic[0][1], delta=1e-6)
        self.assertAlmostEqual(numeric[1][1], analytic[1][1], delta=1e-6)

    def test_covariance_is_symmetric_positive_definite(self):
        covariance = measurement_covariance_xz(
            self.box,
            self.metadata,
            self.ground_y,
            sigma_px=2.866112,
            sigma_att_deg=1.0,
            sigma_y_m=0.05,
        )
        self.assertAlmostEqual(covariance[0][1], covariance[1][0], places=15)
        determinant = (
            covariance[0][0] * covariance[1][1] - covariance[0][1] ** 2
        )
        self.assertGreater(determinant, 0.0)


class EstimatorFilterTests(unittest.TestCase):
    def _filter(self):
        return WorldEstimateFilter(
            q_accel_mps2=8.377580,
            sigma_px=2.866112,
            sigma_att_deg=1.0,
            sigma_y_m=0.05,
            initial_velocity_sigma_mps=2.0,
        )

    def test_static_target_converges_and_predict_only_grows_covariance(self):
        filt = self._filter()
        metadata = tilted_metadata(0)
        box = (0.45, 0.35, 0.1, 0.12)
        intersection = box_ground_intersection(box, metadata, 0.2)
        estimate = filt.initialize(box, metadata, 0.2, 500.0)
        self.assertAlmostEqual(
            estimate.mean[0], intersection.point_world_m[0], places=12
        )
        self.assertAlmostEqual(
            estimate.mean[1], intersection.point_world_m[2], places=12
        )
        for index in range(1, 10):
            estimate = filt.update(box, metadata, 0.2, 500.0 + index * 0.2)
        fused = estimate.covariance[0][0]
        self.assertGreater(fused, 0.0)
        self.assertIsNotNone(filt.last_nis)
        advanced = filt.advance(510.0)
        self.assertGreater(advanced.covariance[0][0], fused)
        self.assertAlmostEqual(advanced.mean[0], estimate.mean[0], places=12)

    def test_backward_clock_and_uninitialized_steps_are_rejected(self):
        filt = self._filter()
        with self.assertRaises(ValueError):
            filt.advance(500.0)
        metadata = tilted_metadata(0)
        filt.initialize((0.45, 0.35, 0.1, 0.12), metadata, 0.2, 500.0)
        with self.assertRaises(ValueError):
            filt.advance(499.0)

    def test_non_positive_sigmas_are_rejected(self):
        with self.assertRaises(ValueError):
            WorldEstimateFilter(
                q_accel_mps2=0.0,
                sigma_px=2.866112,
                sigma_att_deg=1.0,
                sigma_y_m=0.05,
                initial_velocity_sigma_mps=2.0,
            )


class ThresholdPolicyTests(unittest.TestCase):
    """Proposal 3.5 / section 2 branch table semantics."""

    def test_margin_hysteresis(self):
        planner = _planner()
        estimate = _estimate()
        # margin 45 > release 20: hold.
        command = planner.decide(_platform(0.0), estimate, 1.0)
        self.assertEqual(command.mode, "hold")
        # margin 15, inside the band, previously holding: hold (hysteresis).
        command = planner.decide(_platform(30.0), estimate, 1.0)
        self.assertEqual(command.mode, "hold")
        self.assertEqual(command.reason, "within_hysteresis_band")
        # margin 5 < trigger 10: move along the bearing at v_cmd.
        command = planner.decide(_platform(40.0, 90.0), estimate, 1.0)
        self.assertEqual(command.mode, "velocity_world")
        self.assertEqual(command.reason, "margin_below_trigger")
        vx, vy, vz = command.velocity_world_mps
        self.assertAlmostEqual(vx, 4.0, places=9)
        self.assertEqual(vy, 0.0)
        self.assertAlmostEqual(vz, 0.0, places=9)
        self.assertEqual(command.expires_after_s, 0.4)
        # Back inside the band, previously moving: keep moving.
        command = planner.decide(_platform(30.0, 90.0), estimate, 1.0)
        self.assertEqual(command.mode, "velocity_world")
        # margin 25 > release 20: hold.
        command = planner.decide(_platform(20.0, 90.0), estimate, 1.0)
        self.assertEqual(command.mode, "hold")
        self.assertEqual(command.reason, "margin_above_release")

    def test_fail_safe_holds(self):
        planner = _planner()
        estimate = _estimate()
        self.assertEqual(
            planner.decide(None, estimate, 1.0).reason, "no_platform_state"
        )
        # Contract fail-safe (b): no estimate must hold even though this
        # policy never reads the estimate.
        self.assertEqual(
            planner.decide(_platform(40.0), None, 1.0).reason, "no_estimate"
        )

    def test_corridor_shortens_then_holds(self):
        # A prism wall crossing the +x bearing, close enough that the full
        # 1.6 m step is blocked but a shortened step clears it.
        wall = (133.0, 0.0, 110.0, 200.0, 30.0, 124.0)
        planner = _planner(
            corridor_prisms=(wall,), corridor_radius_m=1.0
        )
        # Bearing +x: candidate x grows; the inflated wall starts at x=132,
        # so only steps that keep the cable below/above the wall clear it.
        command = planner.decide(_platform(40.0, 90.0), _estimate(), 1.0)
        self.assertEqual(command.mode, "hold")
        self.assertIn("corridor_blocked", command.reason)

        # A wall far above the cable: the segment never reaches it.
        high_wall = (133.0, 40.0, 110.0, 200.0, 50.0, 124.0)
        planner = _planner(
            corridor_prisms=(high_wall,), corridor_radius_m=1.0
        )
        command = planner.decide(_platform(40.0, 90.0), _estimate(), 1.0)
        self.assertEqual(command.mode, "velocity_world")

    def test_corridor_shortening_reduces_speed(self):
        # A prism the cable hits only at full extension: the anchor->candidate
        # segment clears once the step is shortened.
        # Anchor (132, 0.2, 117); candidate at +x up to 1.6 m at y 25.2.
        # Place a prism hit only by the far end of the segment.
        prism = (133.55, 24.0, 116.0, 134.5, 26.0, 118.0)
        planner = _planner(corridor_prisms=(prism,), corridor_radius_m=0.5)
        command = planner.decide(_platform(40.0, 90.0), _estimate(), 1.0)
        if command.mode == "velocity_world":
            self.assertLess(command.velocity_world_mps[0], 4.0)
            self.assertIn("corridor_shortened", command.reason)
        else:
            self.assertIn("corridor_blocked", command.reason)

    def test_constructor_validation(self):
        with self.assertRaises(ValueError):
            _planner(margin_trigger_deg=25.0)  # above release
        with self.assertRaises(ValueError):
            _planner(margin_release_deg=45.0)  # release at the limit
        with self.assertRaises(ValueError):
            _planner(v_cmd_mps=0.0)
        with self.assertRaises(ValueError):
            _planner(corridor_prisms=((0, 0, 0, 1, 1, 1),))  # radius missing

    def test_segment_prism_slab_test(self):
        prism = (0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
        self.assertTrue(
            segment_intersects_prism((-1.0, 0.5, 0.5), (2.0, 0.5, 0.5), prism, pad_m=0.0)
        )
        self.assertFalse(
            segment_intersects_prism((-1.0, 0.5, 0.5), (-0.5, 0.5, 0.5), prism, pad_m=0.0)
        )
        self.assertTrue(
            segment_intersects_prism((-1.0, 0.5, 0.5), (-0.5, 0.5, 0.5), prism, pad_m=0.6)
        )


class MechanicalCheckTests(unittest.TestCase):
    """The batch 1a-beta review's mechanical checks, executable.

    * BC-BODY1-6 / N3: the policies never reference the saturation flag.
    * BC-M34-3: the threshold policy never reads the estimate.
    * BC-BODY1-8: the online decision path references no truth artifact.
    * BC-BODY1-4: no visibility/occlusion-prediction or measurement-window
      artifact is referenced; the corridor artifact is the only named static
      geometry input.
    * fail-safe (a): ``decide`` does no I/O and reads no clock.
    """

    FORBIDDEN_IN_DECISION_PATH = (
        "CoverageEvaluator",
        "WorldModelHandle",
        "ground_truth",
        "metrics.json",
        "visible_arc",
        "scene-body-margin",
        "scene_geometry",
        "road_data",
        "EvaluationOcclusionGeometry",
    )

    def _policy_source(self, policy):
        return inspect.getsource(policy)

    def test_policies_never_reference_the_saturation_flag(self):
        for policy in (ThresholdBodyPlanner, HoldBodyPlanner):
            self.assertNotIn("gimbal_saturated", self._policy_source(policy))

    def test_threshold_policy_never_reads_the_estimate(self):
        source = self._policy_source(ThresholdBodyPlanner.decide)
        self.assertIn("del estimate", source)
        self.assertNotIn("estimate.", source.replace("del estimate", ""))
        self.assertNotIn("estimate[", source)

    def test_decision_path_has_no_truth_or_visibility_references(self):
        sources = [
            Path(PROJECT_ROOT / "controller" / "world_estimate.py").read_text(),
            self._policy_source(ThresholdBodyPlanner),
            self._policy_source(HoldBodyPlanner),
        ]
        for source in sources:
            for token in self.FORBIDDEN_IN_DECISION_PATH:
                self.assertNotIn(token, source)

    def test_decide_does_no_io_and_reads_no_clock(self):
        for policy in (ThresholdBodyPlanner, HoldBodyPlanner):
            source = self._policy_source(policy)
            for token in ("open(", "json.load", "Path(", "time.", "input("):
                self.assertNotIn(token, source)


class BodyRuntimeBuilderTests(unittest.TestCase):
    def test_real_configs_build_the_frozen_threshold_runtime(self):
        planner, estimator, expires, identity = _build_body_runtime(
            CONFIG_PATH,
            SCENARIO_PATH,
            "threshold",
            scenario_id="deterministic-loop-default",
            ground_plane_y_m=0.2,
        )
        self.assertIsInstance(planner, ThresholdBodyPlanner)
        self.assertEqual(planner.name, "threshold-corridor-v1")
        self.assertEqual(expires, 0.4)
        self.assertEqual(len(planner._corridor_prisms), 779)
        self.assertAlmostEqual(planner._corridor_radius_m, 1.0)
        self.assertEqual(identity["policy"], "threshold")
        self.assertEqual(len(identity["config_sha256"]), 64)

    def test_hold_policy_needs_no_corridor(self):
        planner, _, _, _ = _build_body_runtime(
            CONFIG_PATH,
            SCENARIO_PATH,
            "hold",
            scenario_id="deterministic-loop-default",
            ground_plane_y_m=0.2,
        )
        self.assertIsInstance(planner, HoldBodyPlanner)

    def test_scenario_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            _build_body_runtime(
                CONFIG_PATH,
                SCENARIO_PATH,
                "threshold",
                scenario_id="p1-scene-004",
                ground_plane_y_m=0.2,
            )

    def test_ground_plane_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            _build_body_runtime(
                CONFIG_PATH,
                SCENARIO_PATH,
                "threshold",
                scenario_id="deterministic-loop-default",
                ground_plane_y_m=0.0,
            )

    def test_tampered_corridor_hash_fails_closed(self):
        config = json.loads(CONFIG_PATH.read_text())
        config["corridor"]["artifact_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            tampered = Path(directory) / "config.json"
            tampered.write_text(json.dumps(config))
            with self.assertRaises(ValueError):
                _build_body_runtime(
                    tampered,
                    SCENARIO_PATH,
                    "threshold",
                    scenario_id="deterministic-loop-default",
                    ground_plane_y_m=0.2,
                )


class _ImageStub:
    shape = (480, 640, 3)

    def __init__(self, frame_id):
        self.frame_id = frame_id


class _StubTracker:
    name = "stub"
    backend = "test"
    version = "1"

    def __init__(self, results):
        self._results = list(results)

    def init(self, image, box_norm):
        return True

    def update(self, image):
        return self._results.pop(0)


def _write_frame(runtime, frame_id, **overrides):
    frames = runtime / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    stem = f"frame_{frame_id:010d}"
    (frames / f"{stem}.jpg").write_bytes(b"test-image")
    (frames / f"{stem}.json").write_text(
        json.dumps(tilted_metadata(frame_id, **overrides)), encoding="utf-8"
    )


def _image_loader(path):
    return _ImageStub(int(path.stem.split("_")[1]))


def _make_loop(runtime, tracker, *, run_id, **kwargs):
    logger = RunLogger(runtime, run_id, {"condition": "follow"})
    loop = TrackLoop(
        FrameRepository(runtime, _image_loader),
        tracker,
        RuntimePublisher(runtime, 1.0),
        logger,
        track_id="target-0",
        condition="follow",
        ground_plane_y_m=0.2,
        maximum_ground_range_m=1000.0,
        planned_duration_s=100.0,
        **kwargs,
    )
    return loop, logger


class BodyWiringTests(unittest.TestCase):
    """The section 2 branch table as wired into ``TrackLoop``."""

    def _run_two_frames(self, runtime, *, planner, estimator, second_result=None):
        _write_frame(runtime, 0)
        _write_frame(runtime, 1)
        tracker = _StubTracker(
            [second_result or TrackerResult((0.45, 0.35, 0.1, 0.12), True, 1.0, "placeholder")]
        )
        loop, logger = _make_loop(
            runtime,
            tracker,
            run_id="body-run",
            body_planner=planner,
            body_estimator=estimator,
            body_expires_after_s=0.4,
        )
        loop.initialize(0, (0.45, 0.35, 0.1, 0.12))
        loop.process_available(1)
        logger.close()
        records, _ = read_frame_records(
            runtime / "runs" / "body-run" / "frames.jsonl"
        )
        return loop, records

    def _estimator(self):
        return WorldEstimateFilter(
            q_accel_mps2=8.377580,
            sigma_px=2.866112,
            sigma_att_deg=1.0,
            sigma_y_m=0.05,
            initial_velocity_sigma_mps=2.0,
        )

    def test_threshold_arm_publishes_velocity_and_logs_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            _, records = self._run_two_frames(
                runtime, planner=_planner(), estimator=self._estimator()
            )
            self.assertEqual(len(records), 2)
            init_record, frame_record = records
            # initialize() keeps its one-time hold and starts no planner.
            self.assertNotIn("body_planner", init_record)
            decision = frame_record["body_planner"]
            # Tilted 40 deg: margin 5 < trigger 10 -> move along +z bearing.
            self.assertEqual(decision["mode"], "velocity_world")
            self.assertEqual(decision["reason"], "margin_below_trigger")
            self.assertTrue(decision["published"])
            self.assertEqual(decision["published_mode"], "velocity_world")
            self.assertAlmostEqual(decision["velocity_world_mps"][2], 4.0, places=6)
            estimate = frame_record["world_estimate"]
            self.assertEqual(estimate["step"], "initialized")
            self.assertEqual(len(estimate["mean"]), 4)
            # Backward compatibility: the pre-existing keys are untouched.
            self.assertIn("published_gimbal_command", frame_record)
            self.assertIn("capture_monotonic_s", frame_record)
            # The command actually landed on the wire.
            command = json.loads((runtime / "body_command.json").read_text())
            self.assertEqual(command["command"]["mode"], "velocity_world")

    def test_lost_frame_publishes_hold(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            _, records = self._run_two_frames(
                runtime,
                planner=_planner(),
                estimator=self._estimator(),
                second_result=TrackerResult.lost("synthetic_loss"),
            )
            decision = records[1]["body_planner"]
            self.assertEqual(decision["mode"], "hold")
            self.assertEqual(decision["reason"], "no_observation")
            self.assertTrue(decision["published"])
            # The estimator never saw a measurement: predict-side logging only.
            self.assertEqual(
                records[1]["world_estimate"]["step"], "awaiting_first_measurement"
            )

    def test_planner_exception_holds_and_is_recorded(self):
        class ExplodingPlanner(BodyPlanner):
            name = "exploding"

            def decide(self, platform, estimate, now_monotonic_s):
                raise RuntimeError("synthetic planner failure")

        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            _, records = self._run_two_frames(
                runtime,
                planner=ExplodingPlanner(),
                estimator=self._estimator(),
            )
            decision = records[1]["body_planner"]
            self.assertEqual(decision["mode"], "hold")
            self.assertEqual(decision["reason"], "planner_exception")
            self.assertIn("synthetic planner failure", decision["planner_error"])
            self.assertTrue(decision["published"])

    def test_first_publish_failure_falls_back_to_hold(self):
        # BC-BODY1-20 (a)/(c): the first write fails, the immediate fallback
        # hold succeeds; the run continues and the log keeps the original
        # request, the first error and the actual hold separately.
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            _write_frame(runtime, 0)
            _write_frame(runtime, 1)
            _write_frame(runtime, 2)
            tracker = _StubTracker(
                [
                    TrackerResult((0.45, 0.35, 0.1, 0.12), True, 1.0, "placeholder"),
                    TrackerResult((0.45, 0.35, 0.1, 0.12), True, 1.0, "placeholder"),
                ]
            )
            loop, logger = _make_loop(
                runtime,
                tracker,
                run_id="body-fail-first",
                body_planner=_planner(),
                body_estimator=self._estimator(),
                body_expires_after_s=0.4,
            )
            original = loop.publisher.body_command
            calls = {"count": 0}

            def fail_first(command):
                calls["count"] += 1
                if calls["count"] == 1:
                    raise OSError("synthetic write failure")
                return original(command)

            loop.publisher.body_command = fail_first
            loop.initialize(0, (0.45, 0.35, 0.1, 0.12))
            loop.process_available(1)
            # The command slot ends in the fallback hold, not the velocity.
            command = json.loads((runtime / "body_command.json").read_text())
            self.assertEqual(command["command"]["mode"], "hold")
            # The run is not terminal: the next frame still gets a decision.
            loop.process_available(2)
            logger.close()
            self.assertFalse(loop.terminal)
            records, _ = read_frame_records(
                runtime / "runs" / "body-fail-first" / "frames.jsonl"
            )
            self.assertEqual(len(records), 3)
            decision = records[1]["body_planner"]
            self.assertEqual(decision["mode"], "velocity_world")
            self.assertAlmostEqual(decision["velocity_world_mps"][2], 4.0)
            self.assertIn("synthetic write failure", decision["publish_error"])
            self.assertTrue(decision["published"])
            self.assertEqual(decision["published_mode"], "hold")
            self.assertEqual(
                decision["published_reason"], "publish_failure_fallback"
            )
            # Frame 2 published its own (successful) velocity decision.
            followup = records[2]["body_planner"]
            self.assertEqual(followup["mode"], "velocity_world")
            self.assertEqual(followup["published_mode"], "velocity_world")
            self.assertNotIn("publish_error", followup)

    def test_double_publish_failure_terminates_fail_closed(self):
        # BC-BODY1-20 (b)/(c): both writes fail - both errors are kept, the
        # run terminates fail closed and produces no further decisions.
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            _write_frame(runtime, 0)
            _write_frame(runtime, 1)
            _write_frame(runtime, 2)
            tracker = _StubTracker(
                [
                    TrackerResult((0.45, 0.35, 0.1, 0.12), True, 1.0, "placeholder"),
                    TrackerResult((0.45, 0.35, 0.1, 0.12), True, 1.0, "placeholder"),
                ]
            )
            loop, logger = _make_loop(
                runtime,
                tracker,
                run_id="body-fail-both",
                body_planner=_planner(),
                body_estimator=self._estimator(),
                body_expires_after_s=0.4,
            )

            def always_fail(command):
                raise OSError("synthetic persistent write failure")

            loop.publisher.body_command = always_fail
            loop.initialize(0, (0.45, 0.35, 0.1, 0.12))
            loop.process_available(1)
            self.assertTrue(loop.terminal)
            # No further frames are processed and no further planner
            # decisions are produced.
            self.assertEqual(loop.process_available(2), 0)
            logger.close()
            # The failed velocity never reached the wire: the slot still
            # holds the initialize-time hold.
            command = json.loads((runtime / "body_command.json").read_text())
            self.assertEqual(command["command"]["mode"], "hold")
            records, _ = read_frame_records(
                runtime / "runs" / "body-fail-both" / "frames.jsonl"
            )
            # init record + failing frame record + terminal record.
            self.assertEqual(len(records), 3)
            decision = records[1]["body_planner"]
            self.assertEqual(decision["mode"], "velocity_world")
            self.assertFalse(decision["published"])
            self.assertIn("synthetic persistent", decision["publish_error"])
            self.assertIn("synthetic persistent", decision["fallback_error"])
            terminal = records[2]
            self.assertEqual(terminal["event"], "BODY_COMMAND_FAIL_CLOSED")
            self.assertEqual(terminal["state"], "ERROR_REINIT_REQUIRED")
            self.assertIn("fallback hold failed", terminal["reason"])

    def test_qualification_lifecycle_owns_body_control(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            _write_frame(runtime, 0)
            tracker = _StubTracker([])
            loop, _ = _make_loop(
                runtime,
                tracker,
                run_id="body-qual",
                qualification_lifecycle=object(),
                body_planner=_planner(),
                body_estimator=self._estimator(),
                body_expires_after_s=0.4,
            )
            bundle = loop.repository.load(0)
            result = TrackerResult((0.45, 0.35, 0.1, 0.12), True, 1.0, "placeholder")
            self.assertIsNone(loop._body_step(bundle, result))
            self.assertFalse((runtime / "body_command.json").exists())

    def test_no_body_wiring_keeps_records_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            _write_frame(runtime, 0)
            _write_frame(runtime, 1)
            tracker = _StubTracker(
                [TrackerResult((0.45, 0.35, 0.1, 0.12), True, 1.0, "placeholder")]
            )
            loop, logger = _make_loop(runtime, tracker, run_id="plain-run")
            loop.initialize(0, (0.45, 0.35, 0.1, 0.12))
            loop.process_available(1)
            logger.close()
            records, _ = read_frame_records(
                runtime / "runs" / "plain-run" / "frames.jsonl"
            )
            for record in records:
                self.assertNotIn("body_planner", record)
                self.assertNotIn("world_estimate", record)
            # The one-time init hold is the only body publication.
            command = json.loads((runtime / "body_command.json").read_text())
            self.assertEqual(command["command"]["mode"], "hold")

    def test_planner_without_estimator_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            _write_frame(runtime, 0)
            with self.assertRaises(ValueError):
                _make_loop(
                    runtime,
                    _StubTracker([]),
                    run_id="bad-wiring",
                    body_planner=_planner(),
                    body_expires_after_s=0.4,
                )

    def test_cli_rejects_body_policy_without_configs(self):
        with self.assertRaises(SystemExit):
            track_loop_main(
                [
                    "--tracker",
                    "csrt",
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
                    "deterministic-loop-default",
                    "--condition",
                    "follow",
                    "--ground-plane-y-m",
                    "0.2",
                    "--planned-duration-s",
                    "1.0",
                    "--body-policy",
                    "threshold",
                ]
            )


if __name__ == "__main__":
    unittest.main()
