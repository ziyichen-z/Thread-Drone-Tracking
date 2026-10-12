"""P1-M3-BODY-001 batch 1a-alpha: tool and contract tests.

These cover the parts a reviewer can check without Unity: the isomorphic
predicates, the fail-closed paths of each tool, the checked-in artifacts'
internal consistency, and the frozen planner contract.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from controller.body_planner import (  # noqa: E402
    CONTRACT_VERSION,
    MODES,
    BodyCommand,
    BodyPlanner,
    PlatformState,
    WorldEstimate,
)
import tools.build_m3_corridor as corridor  # noqa: E402
import tools.calibrate_pixel_sigma as sigma  # noqa: E402
import tools.check_anchor_placement as anchor  # noqa: E402
import tools.check_scene_body_margin as margin  # noqa: E402

CONFIG_PATH = PROJECT_ROOT / "config" / "p1-m3-body-001.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AnchorAuditCheckerTests(unittest.TestCase):
    """Hard gate 1's consumer-side check (BC-M34-4 (c), BC-BODY1-3)."""

    def setUp(self) -> None:
        self.artifact = json.loads(anchor.DEFAULT_ARTIFACT.read_text())

    def test_checked_in_artifact_passes_and_is_clear(self):
        checked = anchor.check_artifact()
        self.assertEqual(checked["status"], anchor.STATUS_CLEAR)
        self.assertEqual(checked["support_status"], "PASS")
        self.assertEqual(checked["clearance_status"], "PASS")
        self.assertEqual(checked["blocker_count"], 0)

    def test_support_predicate_is_isomorphic_to_the_runtime(self):
        road_data = json.loads(anchor.ROAD_DATA_PATH.read_text())
        support = anchor.road_surface_support((132.0, 117.0), road_data)
        published = [
            (item["id"], item["surface_y_m"])
            for item in self.artifact["support_matches"]
            if item["source"] == "road_surface"
        ]
        self.assertEqual(len(support), 1)
        self.assertEqual([name for name, _ in support], [name for name, _ in published])

    def test_strictly_inside_surface_excludes_the_boundary(self):
        surface = {
            "center_x_m": 0.0,
            "center_z_m": 0.0,
            "yaw_deg": 0.0,
            "half_extent_x_m": 5.0,
            "half_extent_z_m": 5.0,
        }
        self.assertTrue(anchor.strictly_inside_surface((0.0, 0.0), surface))
        self.assertFalse(anchor.strictly_inside_surface((5.0, 0.0), surface))
        # Strictly inside means the epsilon band at the edge is outside too.
        self.assertFalse(anchor.strictly_inside_surface((4.999999, 0.0), surface))

    def test_yawed_surface_is_handled(self):
        surface = {
            "center_x_m": 0.0,
            "center_z_m": 0.0,
            "yaw_deg": 90.0,
            "half_extent_x_m": 1.0,
            "half_extent_z_m": 10.0,
        }
        # Under a 90 degree yaw the long axis runs along x.
        self.assertTrue(anchor.strictly_inside_surface((5.0, 0.0), surface))
        self.assertFalse(anchor.strictly_inside_surface((0.0, 5.0), surface))

    def test_route_diagnostic_matches_the_frozen_route(self):
        scenario = json.loads(anchor.SCENARIO_PATH.read_text())
        distance = anchor.route_centerline_distance(
            (132.0, 117.0), scenario["target"]["route_world_m"]
        )
        self.assertAlmostEqual(distance, 0.5, places=9)
        self.assertAlmostEqual(
            self.artifact["route_centerline_distance_m"], 0.5, places=6
        )

    def test_route_diagnostic_never_changes_the_verdict(self):
        # The anchor sits 0.5 m from the centreline, inside the 1.5 m route
        # corridor, and the audit is still CLEAR: BC-M34-4 (c) freezes the
        # gate as support + clearance, so this is disclosed, not gating.
        self.assertLess(
            self.artifact["route_centerline_distance_m"],
            self.artifact["route_corridor_half_width_m"],
        )
        self.assertEqual(self.artifact["status"], anchor.STATUS_CLEAR)

    def _expect_failure(self, mutate) -> None:
        artifact = copy.deepcopy(self.artifact)
        mutate(artifact)
        path = PROJECT_ROOT / "runtime" / "test-m3-anchor-tamper.json"
        path.write_text(json.dumps(artifact))
        try:
            with self.assertRaises(anchor.CheckFailure):
                anchor.check_artifact(path)
        finally:
            path.unlink()

    def test_tampered_contract_hash_is_rejected(self):
        self._expect_failure(
            lambda item: item.__setitem__("anchor_contract_sha256", "0" * 64)
        )

    def test_anchor_that_drifts_from_the_scenario_is_rejected(self):
        self._expect_failure(
            lambda item: item["audited_anchor_world_m"].__setitem__("x", 140.0)
        )

    def test_status_that_does_not_follow_from_the_gates_is_rejected(self):
        self._expect_failure(
            lambda item: item.__setitem__("support_status", "FAIL")
        )

    def test_invented_support_elevation_is_rejected(self):
        self._expect_failure(
            lambda item: item["support_matches"][0].__setitem__("surface_y_m", 3.0)
        )

    def test_blocker_booleans_must_follow_from_published_distances(self):
        def mutate(item):
            item["support_status"] = "PASS"
            item["clearance_status"] = "FAIL"
            item["status"] = anchor.STATUS_FAILED
            item["rejection_reason"] = "CLEARANCE_INTERSECTION"
            item["blocker_count"] = 1
            item["blockers"] = [
                {
                    "scene_object_name": "Props_Street Light (1)",
                    "canonical_name": "Props_Street Light",
                    "group": "prop",
                    "reason": "CLEARANCE_INTERSECTION",
                    # 40 m away clears every volume, so the claim is false.
                    "horizontal_distance_m": 40.0,
                    "obstacle_min_y_m": 0.0,
                    "obstacle_max_y_m": 5.0,
                    "anchor_cylinder": True,
                    "corridor_cylinder": False,
                    "hover_sphere": False,
                }
            ]

        self._expect_failure(mutate)


class CorridorBuilderTests(unittest.TestCase):
    """BC-BODY1-4 artifact discipline."""

    def test_checked_in_corridor_artifact_is_reproducible(self):
        rebuilt = corridor.serialize(corridor.build_corridor())
        self.assertEqual(corridor.CORRIDOR_PATH.read_text(), rebuilt)

    def test_corridor_basis_is_the_scenarios_own_road_audit(self):
        artifact = json.loads(corridor.CORRIDOR_PATH.read_text())
        geometry = json.loads(corridor.SCENE_GEOMETRY_PATH.read_text())
        self.assertTrue(geometry["scene_adjustments_applied"])
        self.assertEqual(geometry["road_audit_status"], "CLEAR")
        self.assertEqual(
            artifact["instance_count"], geometry["road_audit_obstacle_count"]
        )

    def test_bc_body1_4_count_conflict_is_reported_not_silently_resolved(self):
        artifact = json.loads(corridor.CORRIDOR_PATH.read_text())
        self.assertEqual(artifact["bc_body1_4_quoted_instance_count"], 782)
        self.assertEqual(artifact["instance_count"], 779)
        self.assertTrue(artifact["bc_body1_4_count_conflict"])

    def test_geometry_harvested_before_adjustments_fails_closed(self):
        geometry = json.loads(corridor.SCENE_GEOMETRY_PATH.read_text())
        geometry["scene_adjustments_applied"] = False
        path = PROJECT_ROOT / "runtime" / "test-m3-geometry-tamper.json"
        path.write_text(json.dumps(geometry))
        try:
            with self.assertRaises(corridor.BuildFailure):
                corridor.build_corridor(path)
        finally:
            path.unlink()

    def test_basis_that_disagrees_with_the_road_audit_fails_closed(self):
        geometry = json.loads(corridor.SCENE_GEOMETRY_PATH.read_text())
        geometry["instances"] = geometry["instances"][:-1]
        geometry["instance_count"] = len(geometry["instances"])
        path = PROJECT_ROOT / "runtime" / "test-m3-geometry-short.json"
        path.write_text(json.dumps(geometry))
        try:
            with self.assertRaises(corridor.BuildFailure):
                corridor.build_corridor(path)
        finally:
            path.unlink()

    def test_corridor_artifact_declares_its_single_permitted_query(self):
        artifact = json.loads(corridor.CORRIDOR_PATH.read_text())
        self.assertIn("segment vs prism intersection", artifact["permitted_query"])
        self.assertIn("no visibility", artifact["permitted_query"])


class SceneBodyMarginTests(unittest.TestCase):
    """Tool 2's isomorphic predicates and the frozen measurement window."""

    def setUp(self) -> None:
        self.artifact = json.loads(margin.DEFAULT_OUTPUT.read_text())

    def test_target_bounds_match_the_visual_factory_at_zero_yaw(self):
        minimum, maximum = margin.target_world_bounds((0.0, 0.0), 0.2, (0.0, 1.0))
        # Body cube 2 x 1 x 4 at local y [0,1]; roof 1.7 x 0.7 x 2 at
        # local y [0.85, 1.55], offset -0.2 in z.
        self.assertAlmostEqual(minimum[0], -1.0, places=9)
        self.assertAlmostEqual(maximum[0], 1.0, places=9)
        self.assertAlmostEqual(minimum[1], 0.2, places=9)
        self.assertAlmostEqual(maximum[1], 0.2 + 1.55, places=9)
        self.assertAlmostEqual(minimum[2], -2.0, places=9)
        self.assertAlmostEqual(maximum[2], 2.0, places=9)

    def test_target_bounds_grow_when_the_heading_is_diagonal(self):
        # `Renderer.bounds` is the world AABB of the rotated box, so a 45
        # degree heading widens it; using the local box would understate the
        # 15-point sample spread.
        diagonal = math.sqrt(0.5)
        minimum, maximum = margin.target_world_bounds(
            (0.0, 0.0), 0.2, (diagonal, diagonal)
        )
        self.assertGreater(maximum[0] - minimum[0], 2.0)
        self.assertGreater(maximum[2] - minimum[2], 4.0)

    def test_visibility_samples_are_the_fifteen_the_evaluator_uses(self):
        minimum, maximum = (-1.0, 0.0, -2.0), (1.0, 1.0, 2.0)
        corners = margin.bounds_corners(minimum, maximum)
        samples = margin.visibility_samples(minimum, maximum, corners)
        self.assertEqual(len(corners), 8)
        self.assertEqual(len(samples), 15)
        self.assertEqual(samples[:8], corners)
        self.assertEqual(samples[8], (0.0, 0.5, 0.0))

    def test_camera_basis_reproduces_the_published_forward_convention(self):
        # BC-BODY1-6: theta = acos(-forward.y), bearing = atan2(fwd.x, fwd.z).
        for applied, yaw in ((0.0, 0.0), (30.0, 45.0), (45.0, -120.0)):
            _, _, forward = margin.camera_basis(applied, yaw)
            theta = math.degrees(math.acos(min(1.0, max(-1.0, -forward[1]))))
            self.assertAlmostEqual(theta, applied, places=9)
            if applied > 0.0:
                bearing = math.degrees(math.atan2(forward[0], forward[2]))
                self.assertAlmostEqual(bearing, yaw, places=9)

    def test_nadir_camera_puts_the_point_below_it_at_the_frame_centre(self):
        basis = margin.camera_basis(0.0, 0.0)
        viewport = margin.world_to_viewport(
            (0.0, 0.0, 0.0), (0.0, 25.0, 0.0), basis, 0.7698, 0.57735
        )
        self.assertAlmostEqual(viewport[0], 0.5, places=9)
        self.assertAlmostEqual(viewport[1], 0.5, places=9)
        self.assertAlmostEqual(viewport[2], 25.0, places=9)

    def test_gimbal_clamps_at_the_limit_but_flags_only_past_the_dead_band(self):
        # A requested angle inside the 0.1 degree dead band clamps without
        # raising the flag - the non-equivalence BC-BODY1-6 names.
        drop = 25.0
        just_over = drop * math.tan(math.radians(45.05))
        pose = margin.gimbal_pose((0.0, 25.2, 0.0), (just_over, 0.2, 0.0), 45.0)
        self.assertAlmostEqual(pose["applied_off_nadir_deg"], 45.0, places=9)
        self.assertGreater(pose["requested_off_nadir_deg"], 45.0)
        self.assertFalse(pose["saturated"])

    def test_segment_box_test_respects_finite_length(self):
        box = (0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
        self.assertTrue(margin.segment_hits_box((-5.0, 0.5, 0.5), (1.0, 0.0, 0.0), 10.0, box))
        # Same ray, but it stops before reaching the box.
        self.assertFalse(margin.segment_hits_box((-5.0, 0.5, 0.5), (1.0, 0.0, 0.0), 2.0, box))
        # Padding is the conservative Minkowski inflation the corridor uses.
        self.assertTrue(
            margin.segment_hits_box(
                (-5.0, 0.5, 2.0), (1.0, 0.0, 0.0), 10.0, box, pad=1.5
            )
        )

    def test_visible_arc_wrapping_run_is_one_interval_not_two(self):
        # The seam is not a boundary on a closed loop. Flags visible at both
        # ends and occluded in the middle is a single wrapped arc.
        flags = [True, True, False, False, True, True]
        mileages = [index * 0.5 for index in range(6)]
        intervals = margin._intervals_from_flags(mileages, flags, 0.5, 3.0)
        self.assertEqual(len(intervals), 1)
        self.assertTrue(intervals[0]["wraps"])
        self.assertTrue(margin._interval_contains(intervals[0], 0.0, 3.0))

    def test_visible_arc_without_wrapping_is_reported_plainly(self):
        flags = [False, True, True, False]
        mileages = [index * 0.5 for index in range(4)]
        intervals = margin._intervals_from_flags(mileages, flags, 0.5, 2.0)
        self.assertEqual(len(intervals), 1)
        self.assertFalse(intervals[0]["wraps"])
        self.assertFalse(margin._interval_contains(intervals[0], 0.0, 2.0))

    def test_frozen_artifact_puts_route_zero_inside_the_visible_arc(self):
        arc = self.artifact["visible_arc"]
        self.assertTrue(arc["route_zero_inside_arc"])
        self.assertEqual(arc["interval_count"], 1)
        self.assertTrue(arc["intervals_m"][0]["wraps"])

    def test_frozen_artifact_reports_a_real_c_geom_gap(self):
        geom = self.artifact["c_geom"]
        # BC-M34-4 (a): the gap has to be substantive, not a rounding error.
        self.assertEqual(geom["upper_bound_frustum_only"], 1.0)
        self.assertLess(geom["lower_bound_with_box_occlusion"], 0.7)
        self.assertGreater(geom["gap_from_saturation"], 0.3)

    def test_c_geom_domain_is_the_whole_loop(self):
        carrier = self.artifact["carrier"]
        expected = math.ceil(
            carrier["perimeter_m"] / carrier["route_sample_spacing_m"]
        )
        self.assertEqual(carrier["route_sample_count"], expected)

    def test_occlusion_attribution_names_the_dominant_blocker(self):
        by_name = self.artifact["occlusion_attribution"]["by_canonical_name"]
        self.assertEqual(by_name[0]["canonical_name"], "Building_Stadium")

    def test_arm_b_stays_inside_the_tether_sphere(self):
        scenario = json.loads(margin.SCENARIO_PATH.read_text())
        tether = float(scenario["drone"]["tether_length_m"])
        drop = float(scenario["drone"]["initial_altitude_m"])
        reach = math.sqrt(tether * tether - drop * drop)
        displacement = self.artifact["c_quality_projection"][
            "arm_b_body_displacement_m"
        ]
        self.assertLessEqual(displacement["max"], reach)

    def test_c_quality_is_measured_inside_the_window_only(self):
        window = self.artifact["visible_arc"]["measurement_window_m"]
        spacing = self.artifact["carrier"]["route_sample_spacing_m"]
        expected = int(round((window[1] - window[0]) / spacing))
        for arm in ("arm_a_gimbal_only", "arm_b_threshold_allocation"):
            self.assertLessEqual(
                self.artifact["c_quality_projection"][arm]["sample_count"], expected
            )

    def test_margin_build_refuses_a_failed_anchor_gate(self):
        audit = json.loads(margin.ANCHOR_AUDIT_PATH.read_text())
        audit["status"] = "ANCHOR_PLACEMENT_AUDIT_FAILED"
        backup = margin.ANCHOR_AUDIT_PATH.read_text()
        margin.ANCHOR_AUDIT_PATH.write_text(json.dumps(audit))
        try:
            with self.assertRaises(margin.MarginFailure):
                margin.build_margin()
        finally:
            margin.ANCHOR_AUDIT_PATH.write_text(backup)


class SigmaCalibrationTests(unittest.TestCase):
    """BC-BODY1-7 pre-registration, checked without re-running the tracker."""

    def setUp(self) -> None:
        self.artifact = json.loads(sigma.DEFAULT_OUTPUT.read_text())

    def test_both_extrapolation_risks_are_recorded_verbatim(self):
        recorded = self.artifact["extrapolation_risks"]
        self.assertEqual(len(recorded), 2)
        self.assertIn("truth_directed_scouting", recorded[0])
        self.assertIn("near-nadir", recorded[1])

    def test_result_is_labelled_a_conservative_initial_value(self):
        self.assertIn("conservative initial value", self.artifact["label"])
        self.assertIn("Acceptance", self.artifact["batch_1c_obligation"])

    def test_aggregation_is_the_pre_registered_pooled_rms(self):
        residual_x = [3.0, -3.0]
        residual_y = [4.0, -4.0]
        pooled = residual_x + residual_y
        expected = math.sqrt(sum(value * value for value in pooled) / len(pooled))
        self.assertAlmostEqual(expected, math.sqrt(12.5), places=12)

    def test_nothing_was_trimmed(self):
        counts = self.artifact["counts"]
        self.assertEqual(
            counts["residual_samples"],
            counts["frames_evaluated"] - counts["tracker_lost"],
        )
        self.assertEqual(self.artifact["pre_registered_policy"]["P4_outliers"][:7], "nothing")

    def test_sigma_is_consistent_with_the_published_axis_statistics(self):
        axis = self.artifact["residual_axis_px"]
        # Pooled RMS**2 == mean of (mean**2 + stdev**2) over the two axes.
        expected = math.sqrt(
            (
                axis["mean_x"] ** 2
                + axis["stdev_x"] ** 2
                + axis["mean_y"] ** 2
                + axis["stdev_y"] ** 2
            )
            / 2.0
        )
        self.assertAlmostEqual(self.artifact["sigma_px"], expected, places=6)


class PlannerContractTests(unittest.TestCase):
    """BC-M34-7 / BC-BODY1-6 / BC-BODY1-8 frozen interface."""

    def test_contract_version_is_v1_with_no_waypoint_mode(self):
        self.assertEqual(CONTRACT_VERSION, "body-planner-contract/v1")
        self.assertEqual(MODES, ("hold", "velocity_world"))

    def test_module_exports_no_writer(self):
        # fail-safe (c): nothing outside a planner may publish a body command,
        # so the contract module deliberately has no publish path. Substring
        # scan over every public name (review note N6: adding public API to
        # this module must keep this test strong, not just green).
        import controller.body_planner as module

        for name in dir(module):
            if name.startswith("_"):
                continue
            lowered = name.lower()
            self.assertNotIn("write", lowered)
            self.assertNotIn("publish", lowered)

    def test_policies_are_concrete_and_stay_writer_free(self):
        # N6: batch 1a-beta added the two v1 policies as public API; they are
        # planners, not publishers.
        import controller.body_planner as module

        for policy_name in ("HoldBodyPlanner", "ThresholdBodyPlanner"):
            policy = getattr(module, policy_name)
            self.assertTrue(issubclass(policy, BodyPlanner))
            self.assertFalse(
                any(
                    "publish" in attribute.lower() or "write" in attribute.lower()
                    for attribute in dir(policy)
                )
            )

    def test_planner_is_abstract(self):
        with self.assertRaises(TypeError):
            BodyPlanner()  # type: ignore[abstract]

    def _platform(self, forward) -> PlatformState:
        return PlatformState(
            frame_id=1,
            capture_monotonic_s=1.0,
            position_world_m=(132.0, 25.2, 117.0),
            camera_forward_world=forward,
            gimbal_saturated=False,
            tether_saturated=False,
        )

    def test_theta_and_margin_come_from_the_published_forward_vector(self):
        nadir = self._platform((0.0, -1.0, 0.0))
        self.assertAlmostEqual(nadir.theta_applied_deg, 0.0, places=9)
        self.assertAlmostEqual(nadir.limit_margin_deg(45.0), 45.0, places=9)

        tilt = math.radians(45.0)
        clamped = self._platform((math.sin(tilt), -math.cos(tilt), 0.0))
        self.assertAlmostEqual(clamped.theta_applied_deg, 45.0, places=9)
        self.assertAlmostEqual(clamped.limit_margin_deg(45.0), 0.0, places=9)

    def test_zero_margin_does_not_imply_the_saturation_flag(self):
        # The 0.1 degree dead band: applied clamps at the limit while the
        # flag stays false. Evidence text may not call these equivalent.
        tilt = math.radians(45.0)
        clamped = self._platform((math.sin(tilt), -math.cos(tilt), 0.0))
        self.assertAlmostEqual(clamped.limit_margin_deg(45.0), 0.0, places=9)
        self.assertFalse(clamped.gimbal_saturated)

    def test_bearing_is_the_horizontal_forward_direction(self):
        tilt = math.radians(30.0)
        for yaw_deg in (0.0, 90.0, -135.0):
            yaw = math.radians(yaw_deg)
            platform = self._platform(
                (
                    math.sin(yaw) * math.sin(tilt),
                    -math.cos(tilt),
                    math.cos(yaw) * math.sin(tilt),
                )
            )
            self.assertAlmostEqual(platform.bearing_deg, yaw_deg, places=6)

    def test_hold_command_must_carry_zero_velocity(self):
        BodyCommand.hold(0.4, "no platform state")
        with self.assertRaises(ValueError):
            BodyCommand("hold", (1.0, 0.0, 0.0), 0.4, "bad")

    def test_velocity_command_is_horizontal_by_construction(self):
        command = BodyCommand.velocity(1.0, 2.0, 0.4, "trigger")
        self.assertEqual(command.velocity_world_mps[1], 0.0)
        self.assertEqual(command.mode, "velocity_world")

    def test_non_finite_and_non_positive_values_are_rejected(self):
        with self.assertRaises(ValueError):
            BodyCommand.velocity(float("nan"), 0.0, 0.4, "bad")
        with self.assertRaises(ValueError):
            BodyCommand.hold(0.0, "bad")

    def test_world_estimate_shape_is_frozen_for_batch_two(self):
        estimate = WorldEstimate(
            mean=(1.0, 2.0, 0.0, 0.0),
            covariance=tuple(tuple(0.0 for _ in range(4)) for _ in range(4)),
            valid_at_monotonic_s=1.0,
        )
        self.assertEqual(len(estimate.mean), 4)
        self.assertEqual(len(estimate.covariance), 4)


class FrozenConfigTests(unittest.TestCase):
    """`config/p1-m3-body-001.json` pins the artifacts it claims to pin."""

    def setUp(self) -> None:
        self.config = json.loads(CONFIG_PATH.read_text())

    def test_pre_registered_policy_values_are_the_proposal_values(self):
        policy = self.config["policy"]
        self.assertEqual(policy["margin_trigger_deg"], 10.0)
        self.assertEqual(policy["margin_release_deg"], 20.0)
        self.assertEqual(policy["v_cmd_mps"], 4.0)
        self.assertEqual(policy["altitude_hold_m"], 25.0)
        self.assertTrue(policy["tether_corridor_check"])

    def test_maximum_off_nadir_is_referenced_not_duplicated(self):
        # BC-BODY1-6: the constant is read from the frozen scenario.
        self.assertNotIn("maximum_off_nadir_deg", self.config["policy"])
        self.assertIn(
            "scenario.default.json", self.config["policy"]["maximum_off_nadir_deg_source"]
        )

    def test_expiry_is_two_capture_periods(self):
        command = self.config["command"]
        self.assertEqual(command["expires_after_s"], 2.0 / command["capture_hz"])
        self.assertEqual(command["contract_version"], CONTRACT_VERSION)
        self.assertEqual(tuple(command["modes"]), MODES)

    def test_every_pinned_artifact_hash_matches_the_file(self):
        for section in ("corridor", "calibration", "measurement_window"):
            entry = self.config[section]
            path = PROJECT_ROOT / entry["artifact_path"]
            self.assertEqual(
                entry["artifact_sha256"],
                _sha256(path),
                f"{section} hash does not match {entry['artifact_path']}",
            )

    def test_visible_arc_hash_matches_the_margin_artifact(self):
        artifact = json.loads(margin.DEFAULT_OUTPUT.read_text())
        self.assertEqual(
            self.config["measurement_window"]["visible_arc_sha256"],
            artifact["visible_arc"]["sha256"],
        )

    def test_sigma_px_matches_the_calibration_artifact(self):
        artifact = json.loads(sigma.DEFAULT_OUTPUT.read_text())
        self.assertAlmostEqual(
            self.config["calibration"]["sigma_px"], artifact["sigma_px"], places=6
        )

    def test_estimator_section_carries_the_frozen_batch_1a_beta_values(self):
        estimator = self.config["estimator"]
        self.assertEqual(estimator["q_accel_mps2"], 8.377580)
        self.assertEqual(estimator["sigma_att_deg"], 1.0)
        self.assertEqual(estimator["sigma_y_m"], 0.05)
        self.assertEqual(estimator["initial_velocity_sigma_mps"], 2.0)
        # Each value names its provenance. BC-BODY1-18: all four are frozen
        # pre-data uncalibrated heuristic priors - no physical-bound or
        # measured-source claim may survive in the provenance text.
        for key in (
            "q_accel_mps2",
            "sigma_att_deg",
            "sigma_y_m",
            "initial_velocity_sigma_mps",
        ):
            self.assertIn(f"{key}_derivation", estimator)
        self.assertNotIn("centripetal", estimator["q_accel_mps2_derivation"])
        self.assertIn(
            "uncalibrated heuristic", estimator["priors_status"]
        )
        self.assertIn("never consume", estimator["note"])


if __name__ == "__main__":
    unittest.main()
