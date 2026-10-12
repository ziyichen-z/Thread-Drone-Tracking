"""Focused tests for tools/analyze_m3_body.py (P1-M3-BODY-001 batch 1c
rework round 3, Acceptance round 13 §B — including the §B.5 falsification
list)."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import tools.analyze_m3_body as analyze  # noqa: E402


SQUARE = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
MODEL_HASHES = {"backbone": "a" * 64, "neckhead": "b" * 64}


def _point_at(mileage: float) -> tuple[float, float]:
    """Walk the 40 m unit square; 1 m per unit mileage from (0,0)."""
    remaining = mileage % 40.0
    for index, vertex in enumerate(SQUARE):
        nxt = SQUARE[(index + 1) % 4]
        length = math.dist(vertex, nxt)
        if remaining <= length:
            ratio = remaining / length
            return (
                vertex[0] + (nxt[0] - vertex[0]) * ratio,
                vertex[1] + (nxt[1] - vertex[1]) * ratio,
            )
        remaining -= length
    raise AssertionError("unreachable")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _patch_frames(fixture, mutate, *, stages: tuple[str, ...]):
    """Rewrite only the ``frames.jsonl`` rows whose original
    ``compute_stage`` is in ``stages`` (round 15 §B.3: counterexamples must
    stay isolated to the branch they claim to lock)."""
    frames_path = fixture.run_dir / "frames.jsonl"
    lines = []
    touched = 0
    for line in frames_path.read_text().splitlines():
        record = json.loads(line)
        if record.get("compute_stage") in stages:
            record = mutate(record)
            touched += 1
        lines.append(json.dumps(record))
    if touched == 0:
        raise AssertionError(f"no frame record with compute_stage in {stages}")
    frames_path.write_text("\n".join(lines) + "\n")


def replay_loop_target(
    vertices: list[tuple[float, float, float]],
    speed: float,
    dt: float,
    frames: int,
):
    """Line-equivalent Python port of the production
    ``LoopTargetVehicle.Step`` (Assets/TetheredTracking/Scripts/
    LoopTargetVehicle.cs:65-81): switch waypoint when the planar distance
    is < 0.5 m and do not move on that frame; otherwise move straight
    toward the current waypoint. This replays the real corner-cutting
    trajectory, not an ideal polyline interpolation."""
    positions = []
    position = (vertices[0][0], vertices[0][2])
    waypoint_index = 1
    for _ in range(frames):
        positions.append(position)
        destination = vertices[waypoint_index]
        dx = destination[0] - position[0]
        dz = destination[2] - position[1]
        distance = math.hypot(dx, dz)
        if distance < 0.5:
            waypoint_index = (waypoint_index + 1) % len(vertices)
            continue  # the switch frame does not move (production line 75)
        position = (
            position[0] + dx / distance * speed * dt,
            position[1] + dz / distance * speed * dt,
        )
    return positions


class MileageMathTests(unittest.TestCase):
    def test_route_mileage_projects_onto_closed_polyline(self):
        vertices = [(x, 0.2, z) for x, z in SQUARE]
        cumulative, perimeter = analyze._cumulative_lengths(vertices)
        self.assertEqual(perimeter, 40.0)
        mileage, off_route = analyze.route_mileage((5.0, 0.1), vertices, cumulative)
        self.assertAlmostEqual(mileage, 5.0)
        self.assertAlmostEqual(off_route, 0.1)

    def test_unwrap_mileage_crosses_seam_once(self):
        unwrapped = analyze._unwrap_mileage([38.0, 39.0, 0.5, 1.5], 40.0)
        self.assertEqual(unwrapped, [38.0, 39.0, 40.5, 41.5])

    def test_trapezoidal_weights_cover_domain_endpoints(self):
        weights = analyze.trapezoidal_weights([0.2, 1.0, 1.8], 0.0, 2.0)
        self.assertAlmostEqual(sum(weights), 2.0)
        self.assertAlmostEqual(weights[0], (1.0 - 0.2) / 2 + 0.2)
        self.assertAlmostEqual(weights[-1], (1.8 - 1.0) / 2 + 0.2)

    def test_weighted_median_respects_weights(self):
        self.assertEqual(
            analyze.weighted_median([1.0, 2.0, 100.0], [1.0, 1.0, 0.0]), 1.0
        )
        self.assertEqual(analyze.percentile([1.0, 2.0, 3.0], 0.9), 2.8)

    def test_replay_cuts_corners_like_production(self):
        # The replayed Step trajectory must deviate from the ideal
        # polyline near corners (production semantics) but stay strictly
        # inside the derived 0.5 m switch bound.
        vertices = [(x, 0.2, z) for x, z in SQUARE]
        cumulative, _ = analyze._cumulative_lengths(vertices)
        positions = replay_loop_target(vertices, 2.0, 0.2, 200)
        deviations = [
            analyze.route_mileage(position, vertices, cumulative)[1]
            for position in positions
        ]
        self.assertGreater(max(deviations), 0.01)  # corner cutting exists
        self.assertLess(max(deviations), 0.5)  # strictly below the bound


class PredecessorHolds:
    """Stand-in predecessor void holds for both acquisition IDs.

    Round 30 §C.3 explicitly allows a stand-in hold whose real bytes the
    expected SHAs are patched to, so the gates are exercised end to end
    without shipping void bytes; round 42 §B (BC-BODY1-27) adds A2's
    ten-file hold on the same pattern."""

    def __init__(self, runtime: Path):
        a1 = runtime / "runs" / analyze.A1_PREDECESSOR_HOLD_DIR_NAME
        a1.mkdir(parents=True, exist_ok=True)
        (a1 / "frames.jsonl").write_text('{"void": "frames"}\n')
        (a1 / "manifest.json").write_text('{"void": "manifest"}\n')
        a2 = runtime / "runs" / analyze.A2_PREDECESSOR_HOLD_DIR_NAME
        a2.mkdir(parents=True, exist_ok=True)
        for name in analyze.A2_PREDECESSOR_HOLD_FILES:
            (a2 / name).write_text(json.dumps({"void": name}) + "\n")
        self.a1_dir = a1
        self.a2_dir = a2
        self.shas = {
            "A1_PREDECESSOR_VOID_FRAMES_SHA256": _sha(a1 / "frames.jsonl"),
            "A1_PREDECESSOR_VOID_MANIFEST_SHA256": _sha(a1 / "manifest.json"),
            "A2_PREDECESSOR_VOID_FRAMES_SHA256": _sha(a2 / "frames.jsonl"),
            "A2_PREDECESSOR_VOID_MANIFEST_SHA256": _sha(a2 / "manifest.json"),
            "A2_PREDECESSOR_VOID_TRUTH_SHA256": _sha(
                a2 / analyze.TRUTH_FILE_NAME
            ),
        }

    def run(self, call):
        """Call ``call`` with the shipped SHA constants pointed at this
        stand-in hold's real bytes, restoring them afterwards."""
        saved = {name: getattr(analyze, name) for name in self.shas}
        for name, value in self.shas.items():
            setattr(analyze, name, value)
        try:
            return call()
        finally:
            for name, value in saved.items():
                setattr(analyze, name, value)


class TrialFixture:
    """Synthetic one-loop trial: 1 m/frame around the 40 m square for
    46 frames (final mileage 45, exactly one closure). No frame metadata
    files are written at all - the analysis must not depend on the
    128-frame sensor-metadata retention (round 12 §A.2/§B.2)."""

    def __init__(
        self,
        root: Path,
        run_id: str = "p1-m3-body-001-arm-a-trial-1-attempt-4",
        pause_gap_at: int | None = None,
        occluded_boxed_frames: tuple[int, ...] = (),
    ):
        self.runtime = root / "runtime"
        self.run_id = run_id
        self.run_dir = self.runtime / "runs" / run_id
        self.run_dir.mkdir(parents=True)
        self.pause_gap_at = pause_gap_at
        self.occluded_boxed_frames = occluded_boxed_frames
        self.scenario_path = root / "scenario.json"
        self.margin_path = root / "margin.json"
        self.body_config_path = root / "body.json"
        self.reanchor_path = root / "reanchor.json"
        self.model_spec_path = root / "models.json"
        self.reanchor_path.write_text('{"carrier": "test"}')
        self.model_spec_path.write_text(
            json.dumps(
                {
                    "models": {
                        name: {"sha256": value}
                        for name, value in MODEL_HASHES.items()
                    }
                }
            )
        )
        self._write_predecessor_hold()
        self._write_configs()
        self._write_truth()
        self._write_run()

    def _write_predecessor_hold(self):
        """Round 30 §C.3 / round 42 §B: the A1 and A2 acquisitions bind to
        their real void holds; fixtures stand those holds in."""
        self.holds = PredecessorHolds(self.runtime)
        self.hold_dir = self.holds.a1_dir
        self.a2_hold_dir = self.holds.a2_dir
        self.hold_frames_sha = self.holds.shas[
            "A1_PREDECESSOR_VOID_FRAMES_SHA256"
        ]
        self.hold_manifest_sha = self.holds.shas[
            "A1_PREDECESSOR_VOID_MANIFEST_SHA256"
        ]

    def _monotonic(self, frame_id: int) -> float:
        value = frame_id * 0.2
        if self.pause_gap_at is not None and frame_id >= self.pause_gap_at:
            value += 300.0  # one manual pause: host stopwatch keeps running
        return value

    def _write_configs(self):
        scenario = {
            "scenario_id": "deterministic-loop-default",
            "target": {
                "track_id": "target-0",
                "route_world_m": [
                    {"x": x, "y": 0.2, "z": z} for x, z in SQUARE
                ],
                "speed_mps": 2.0,
            },
            "sensor": {"width": 640, "height": 480},
            "evaluation": {"tracking_iou_threshold": 0.3},
        }
        self.scenario_path.write_text(json.dumps(scenario))
        margin = {
            "identity": {
                "scenario_id": "deterministic-loop-default",
                "scenario_sha256": _sha(self.scenario_path),
            },
            "visible_arc": {
                "measurement_window_m": [0.0, 15.0],
                "sha256": "f" * 64,
            },
        }
        self.margin_path.write_text(json.dumps(margin))
        # Round 17 §B.2: the body config carries the same two real pins the
        # production config does; a fixture that omitted them would evade the
        # F1 gate instead of exercising it.
        self.body_config_path.write_text(
            json.dumps(
                {
                    "calibration": {"sigma_px": 2.866112},
                    "measurement_window": {
                        "route_sample_spacing_m": 0.5,
                        "artifact_sha256": _sha(self.margin_path),
                        "visible_arc_sha256": margin["visible_arc"]["sha256"],
                    },
                }
            )
        )

    def _truth_record(self, frame_id: int) -> dict:
        mileage = float(frame_id)  # 1 m per frame
        x, z = _point_at(mileage)
        visible = mileage < 25.0 and frame_id not in self.occluded_boxed_frames
        boxed = mileage < 25.0
        moving = frame_id in (5, 6)
        return {
            "schema_version": analyze.TRUTH_SCHEMA,
            "scenario_id": "deterministic-loop-default",
            "frame_id": frame_id,
            "simulation_time_s": frame_id * 0.2,
            "capture_monotonic_s": self._monotonic(frame_id),
            "capture_monotonic_clock_id": "system-stopwatch/v1",
            "target_world_x_m": x,
            "target_world_y_m": 0.2,
            "target_world_z_m": z,
            "body_world_x_m": 132.0 + 0.2 * min(max(frame_id - 4, 0), 2),
            "body_world_y_m": 25.0,
            "body_world_z_m": 117.0,
            "applied_velocity_x_mps": 1.0 if moving else 0.0,
            "applied_velocity_y_mps": 0.0,
            "applied_velocity_z_mps": 0.0,
            "intersects_frustum": visible,
            "has_unoccluded_sample": visible,
            "geometrically_visible": visible,
            "visible_sample_fraction": 1.0 if visible else 0.0,
            "truth_box_available": boxed,
            "truth_box_x": 0.4 if boxed else -1.0,
            "truth_box_y": 0.4 if boxed else -1.0,
            "truth_box_width": 0.05 if boxed else -1.0,
            "truth_box_height": 0.05 if boxed else -1.0,
            "truth_center_x_px": 272.0 if boxed else -1.0,
            "truth_center_y_px": 204.0 if boxed else -1.0,
            "target_bbox_area_px": 768.0 if boxed else 0.0,
            "target_center_error_px": 5.0 if boxed else 0.0,
            "gimbal_saturated": frame_id < 5,
            "tether_saturated": False,
            "evaluation_aspect_width_over_height": 640.0 / 480.0,
        }

    def _write_truth(self):
        with (self.runtime / analyze.TRUTH_FILE_NAME).open("w") as handle:
            for frame_id in range(46):
                handle.write(json.dumps(self._truth_record(frame_id)) + "\n")

    def _frame_record(self, frame_id: int) -> dict:
        tracking = frame_id < 10
        mode = "hold"
        requested = [0.0, 0.0, 0.0]
        if frame_id in (5, 6):
            mode = "velocity_world"
            # Requested 4 m/s vs applied 1 m/s in the truth record: effort
            # must follow the plant's applied velocity (round 12 §B.5).
            requested = [4.0, 0.0, 0.0]
        return {
            "frame_id": frame_id,
            "capture_monotonic_s": self._monotonic(frame_id),
            "simulation_time_s": frame_id * 0.2,
            "ok": tracking,
            "box_norm": [0.4, 0.4, 0.05, 0.05] if tracking else None,
            "state": "TRACKING" if tracking else "LOST",
            "compute_stage": "init" if frame_id == 0 else "update",
            # Production always records both counters; a single-frame batch
            # is `backlog_count=0 / skipped_count=0` (round 17 §B.4).
            "backlog_count": 0,
            "skipped_count": 0,
            "body_planner": {
                "name": "hold-v1",
                "mode": mode,
                "published": True,
                "published_mode": mode,
                "velocity_world_mps": requested,
            },
            "world_estimate": {
                "step": "fused" if tracking else "predict_only",
                "mean": [
                    _point_at(float(frame_id))[0] + 0.1,
                    _point_at(float(frame_id))[1] + 0.1,
                    0.0,
                    0.0,
                ],
                "covariance": [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ],
                "nis": 0.5,
            },
        }

    def _write_run(self):
        manifest = {
            "schema_version": analyze.MANIFEST_SCHEMA,
            "run_id": self.run_id,
            "scenario_id": "deterministic-loop-default",
            "cli_args": {
                "body_policy": "hold",
                "tracker": "nanotrack-v2",
                "condition": "follow",
                "track_id": "target-0",
                "ground_plane_y_m": 0.2,
                "reanchor_config": str(self.reanchor_path),
                "tracker_model_spec": str(self.model_spec_path),
            },
            "init": {"frame_id": 0, "box_norm": [0.4, 0.4, 0.05, 0.05]},
            "tracker": {
                "name": "nanotrack-v2",
                "backend": "opencv-dnn",
                "pinned_version": "test-pin",
                "model_sha256": dict(MODEL_HASHES),
            },
            "reanchor": {"config_sha256": _sha(self.reanchor_path)},
            "body_planner": {
                "policy": "hold",
                "planner": "hold-v1",
                "config_sha256": _sha(self.body_config_path),
                "scenario_config_sha256": _sha(self.scenario_path),
            },
        }
        (self.run_dir / "manifest.json").write_text(json.dumps(manifest))
        with (self.run_dir / "frames.jsonl").open("w") as handle:
            for frame_id in range(46):
                handle.write(json.dumps(self._frame_record(frame_id)) + "\n")
        metrics = {
            "schema_version": "tethered-evaluation/v1",
            "evaluation_projection": {
                "sensor_width_px": 640,
                "sensor_height_px": 480,
                "aspect_width_over_height": 640.0 / 480.0,
            },
            "aggregate": {"sensor_frames": 46, "c_geom": 0.5},
        }
        (self.run_dir / "metrics.final.json").write_text(json.dumps(metrics))

    def analyze(self, verify: bool = False):
        # Patch only the expected predecessor SHAs to this fixture's holds
        # (round 30 §C.3 explicitly allows this); every other gate is real.
        return self.holds.run(
            lambda: analyze.analyze_trial(
                self.runtime,
                self.run_id,
                self.scenario_path,
                self.margin_path,
                self.body_config_path,
                verify=verify,
            )
        )


def _metric_sections(result: dict) -> dict:
    return {
        key: result[key]
        for key in (
            "domains",
            "h1",
            "window",
            "c_quality",
            "c_quality_series",
            "tails",
            "saturation",
            "cost",
            "estimator",
        )
    }


# Cases whose failure must come from a named branch, not merely from some
# earlier check that happens to fire first (round 15 §A.2/§B.3).
EXPECTED_ERROR_PREFIX = {
    "no_single_loop": "trial_invalid_no_single_loop:",
    "update_frame_planner_mismatch": "update_frame_planner_mismatch:",
    "missing_compute_stage": "frame_compute_stage_invalid:",
    "unknown_compute_stage": "frame_compute_stage_invalid:",
    "no_init_frame_record": "init_frame_record_count:",
    "init_frame_id_differs_from_manifest": "init_frame_id_mismatch:",
    "margin_bytes_differ_from_pin": "margin_artifact_pin_mismatch:",
    "visible_arc_sha_differs_from_pin": "visible_arc_pin_mismatch:",
    "margin_pin_missing": "sha256_not_hex64:margin_artifact.pin",
    "decision_update_without_planner": "update_frame_planner_mismatch:",
    "catch_up_without_backlog": "catch_up_frame_backlog_invalid:",
    "catch_up_carries_planner": "catch_up_frame_carries_planner:",
    "unknown_skipped_count": "update_frame_skipped_count_invalid:",
    "non_integer_counter": "frame_counter_invalid:",
    "init_frame_counters_not_zero": "init_frame_counters_not_zero:",
    "every_update_is_catch_up": "no_decision_update_frame",
}


class AnalyzeTrialTests(unittest.TestCase):
    def test_happy_path_recomputes_all_quantities(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TrialFixture(Path(tmp))
            result = fixture.analyze()
            receipt = result["receipt"]
            self.assertEqual(
                receipt["run_id"], "p1-m3-body-001-arm-a-trial-1-attempt-4"
            )
            self.assertEqual(receipt["first_frame_id"], 0)
            self.assertEqual(receipt["last_frame_id"], 45)
            self.assertEqual(receipt["truth_record_count"], 46)
            self.assertEqual(receipt["body_policy"], "hold")
            self.assertEqual(receipt["tracker"], "nanotrack-v2")
            self.assertEqual(receipt["init_box_norm"], [0.4, 0.4, 0.05, 0.05])
            self.assertEqual(receipt["tracker_model_sha256"], MODEL_HASHES)
            self.assertAlmostEqual(result["h1"]["full_loop_c_geom"], 24.5 / 40.0)
            self.assertEqual(result["h1"]["disposition"], "WITHIN_RANGE")
            self.assertEqual(result["domains"]["window_frame_count"], 16)
            self.assertEqual(result["domains"]["loop_frame_count"], 40)
            self.assertEqual(result["domains"]["h2_grid_points"], 30)
            self.assertAlmostEqual(
                result["window"]["c_track_given_geom"], 9.5 / 15.0
            )
            self.assertEqual(result["window"]["tracking_iou_threshold"], 0.3)
            self.assertAlmostEqual(result["c_quality"]["area_median_px"], 768.0)
            self.assertEqual(result["c_quality"]["min_side_ge20_share"], 1.0)
            self.assertEqual(result["tails"]["center_error_max_px"], 5.0)
            self.assertAlmostEqual(
                result["saturation"]["window_gimbal_saturated_share"], 4.5 / 15.0
            )
            # Applied (1 m/s x 0.2 s x 2), not requested (4 m/s).
            self.assertAlmostEqual(result["cost"]["body_motion_effort_m"], 0.4)
            self.assertEqual(result["cost"]["planner_switch_count"], 2)
            self.assertAlmostEqual(result["cost"]["body_path_length_m"], 0.4)
            self.assertAlmostEqual(result["estimator"]["nees_median"], 0.02)
            self.assertEqual(result["estimator"]["nis_median"], 0.5)
            self.assertAlmostEqual(
                result["estimator"]["box_center_residual_rms_px"], 0.0
            )
            # Run-bound input copies exist (self-containment, round 13 §B.3).
            for name in (*analyze.RUN_BOUND_INPUTS, analyze.TRUTH_FILE_NAME):
                self.assertTrue((fixture.run_dir / name).is_file(), name)
            self.assertEqual(
                result["tolerances"]["off_route_tol_m"], 0.5 + 1e-3
            )

    def test_pause_monotonic_gap_does_not_change_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _metric_sections(TrialFixture(Path(tmp) / "a").analyze())
        with tempfile.TemporaryDirectory() as tmp:
            gapped = _metric_sections(
                TrialFixture(Path(tmp) / "b", pause_gap_at=20).analyze()
            )
        base["h1"].pop("online_aggregate_c_geom_reference")
        gapped["h1"].pop("online_aggregate_c_geom_reference")
        self.assertEqual(base, gapped)

    def test_occluded_but_boxed_frames_enter_no_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TrialFixture(Path(tmp), occluded_boxed_frames=(3, 4))
            result = fixture.analyze()
            self.assertAlmostEqual(
                result["window"]["c_track_given_geom"], 7.5 / 13.0
            )
            self.assertAlmostEqual(
                result["c_quality"]["area_median_px"], 768.0
            )
            self.assertEqual(result["domains"]["h2_grid_points"], 26)

    def test_verify_is_run_directory_only(self):
        """Round 13 §B.3 acceptance method: after first analysis, delete
        every external dependency and the shared truth stream; --verify
        must still rerun byte-identically from the run directory alone."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = TrialFixture(root)
            first = fixture.analyze()
            (fixture.runtime / analyze.TRUTH_FILE_NAME).unlink()
            for path in (
                fixture.scenario_path,
                fixture.margin_path,
                fixture.body_config_path,
                fixture.reanchor_path,
                fixture.model_spec_path,
            ):
                path.unlink()
            verified = fixture.analyze(verify=True)
            self.assertEqual(verified, first)
            with self.assertRaises(analyze.AnalysisError):
                fixture.analyze()  # create-once

    def test_fail_closed_cases(self):
        cases = (
            "no_single_loop",
            "truth_gap",
            "not_at_route_zero",
            "missing_metrics",
            "aspect_mismatch",
            "scenario_hash_mismatch",
            "wrong_arm_policy",
            "tracker_mismatch",
            "ground_plane_mismatch",
            "missing_init_box",
            "foreign_truth_scenario",
            "tampered_model_sha",
            "tampered_reanchor_sha",
            "policy_planner_mismatch",
            "capture_binding_mismatch",
            "missing_tracker_capture",
            "arm_a_id_with_threshold_policy",
            "manifest_policy_differs_from_cli",
            "update_frame_planner_mismatch",
            "missing_compute_stage",
            "unknown_compute_stage",
            "no_init_frame_record",
            "init_frame_id_differs_from_manifest",
            "margin_bytes_differ_from_pin",
            "visible_arc_sha_differs_from_pin",
            "margin_pin_missing",
            "decision_update_without_planner",
            "catch_up_without_backlog",
            "catch_up_carries_planner",
            "unknown_skipped_count",
            "non_integer_counter",
            "init_frame_counters_not_zero",
            "every_update_is_catch_up",
        )
        for case in cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory() as tmp:
                    fixture = TrialFixture(Path(tmp))
                    self._break(fixture, case)
                    with self.assertRaises(analyze.AnalysisError) as ctx:
                        fixture.analyze()
                    prefix = EXPECTED_ERROR_PREFIX.get(case)
                    if prefix is not None:
                        self.assertTrue(
                            str(ctx.exception).startswith(prefix),
                            f"{case}: {ctx.exception}",
                        )
                    self.assertFalse(
                        (fixture.run_dir / analyze.ANALYSIS_FILE_NAME).exists()
                    )

    def test_extra_laps_neither_void_the_trial_nor_change_h1(self):
        """Round 42 §A (BC-BODY1-23/-25): the retired ``>= 2P`` arm used to
        void a trial that kept driving. Appending a second - and then a third -
        lap must now analyse without error and leave the ``[0, P)`` domain
        bit-identical, because "exactly one closure" is carried by the sample
        filter, not by how far the Play ran."""
        with tempfile.TemporaryDirectory() as tmp:
            single = TrialFixture(Path(tmp)).analyze()

        for extra_laps, last_frame in ((1, 85), (2, 125)):
            with self.subTest(extra_laps=extra_laps):
                with tempfile.TemporaryDirectory() as tmp:
                    fixture = TrialFixture(Path(tmp))
                    truth_path = fixture.runtime / analyze.TRUTH_FILE_NAME
                    with truth_path.open("a") as handle:
                        for frame_id in range(46, last_frame):
                            handle.write(
                                json.dumps(fixture._truth_record(frame_id))
                                + "\n"
                            )
                    extended = fixture.analyze()
                    self.assertEqual(
                        extended["h1"]["full_loop_c_geom"],
                        single["h1"]["full_loop_c_geom"],
                    )
                    self.assertEqual(
                        extended["domains"]["loop_frame_count"],
                        single["domains"]["loop_frame_count"],
                    )
                    self.assertEqual(extended["h1"], single["h1"])
                    # The extra laps are visible only in the recorded final
                    # mileage, which is a domain fact, not a metric.
                    self.assertGreater(
                        extended["domains"]["final_unwrapped_mileage_m"],
                        single["domains"]["final_unwrapped_mileage_m"],
                    )

    def test_two_frame_catch_up_batch_is_admissible(self):
        """Round 17 §B.4(a) (Review F2): the runbook's pause/lowest-frame
        start makes production emit catch-up batches - the first rows carry
        `skipped_count=1` with a positive backlog and no `body_planner`
        because `_body_step` only runs on the batch's latest frame. That real
        shape must analyse, and must not change any recomputed quantity."""
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TrialFixture(Path(tmp))
            baseline = fixture.analyze()
            (fixture.run_dir / analyze.ANALYSIS_FILE_NAME).unlink()

        with tempfile.TemporaryDirectory() as tmp:
            fixture = TrialFixture(Path(tmp))
            frames_path = fixture.run_dir / "frames.jsonl"
            lines = []
            for line in frames_path.read_text().splitlines():
                record = json.loads(line)
                if record["frame_id"] == 11:  # caught up with frame 12
                    record["backlog_count"] = 1
                    record["skipped_count"] = 1
                    del record["body_planner"]
                elif record["frame_id"] == 12:  # the batch's latest frame
                    record["backlog_count"] = 1
                    record["skipped_count"] = 0
                lines.append(json.dumps(record))
            frames_path.write_text("\n".join(lines) + "\n")
            result = fixture.analyze()
            self.assertEqual(_metric_sections(result), _metric_sections(baseline))

    def test_preseeded_margin_window_is_rejected(self):
        """Round 17 §B.2(a) (Review F1): a run directory pre-seeded with a
        scenario-identity-valid margin whose window is `[0, 10]` used to be
        adopted silently, redefining the primary metric domain."""
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TrialFixture(Path(tmp))
            margin = json.loads(fixture.margin_path.read_text())
            margin["visible_arc"]["measurement_window_m"] = [0.0, 10.0]
            (fixture.run_dir / "margin.json").write_text(json.dumps(margin))
            with self.assertRaises(analyze.AnalysisError) as ctx:
                fixture.analyze()
            self.assertTrue(
                str(ctx.exception).startswith("margin_artifact_pin_mismatch:"),
                str(ctx.exception),
            )
            self.assertFalse(
                (fixture.run_dir / analyze.ANALYSIS_FILE_NAME).exists()
            )

    def test_missing_manifest_init_frame_id_fails_closed(self):
        """Round 15 §B.3(a): a manifest without ``init.frame_id`` used to
        reach the receipt as ``null``; it must now fail closed."""
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TrialFixture(Path(tmp))
            manifest_path = fixture.run_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            del manifest["init"]["frame_id"]
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaises(analyze.AnalysisError) as ctx:
                fixture.analyze()
            self.assertTrue(
                str(ctx.exception).startswith("manifest_init_frame_id_invalid:"),
                str(ctx.exception),
            )
            self.assertFalse(
                (fixture.run_dir / analyze.ANALYSIS_FILE_NAME).exists()
            )

    def test_update_row_relabelled_init_fails_closed(self):
        """Round 15 §B.3(b): relabelling real update rows as ``init`` and
        dropping their planner must not hide them from the planner check."""
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TrialFixture(Path(tmp))
            frames_path = fixture.run_dir / "frames.jsonl"
            lines = []
            for line in frames_path.read_text().splitlines():
                record = json.loads(line)
                if record["frame_id"] in (7, 8):  # originally update rows
                    record["compute_stage"] = "init"
                    del record["body_planner"]
                lines.append(json.dumps(record))
            frames_path.write_text("\n".join(lines) + "\n")
            with self.assertRaises(analyze.AnalysisError) as ctx:
                fixture.analyze()
            self.assertTrue(
                str(ctx.exception).startswith("init_frame_record_count:"),
                str(ctx.exception),
            )
            self.assertFalse(
                (fixture.run_dir / analyze.ANALYSIS_FILE_NAME).exists()
            )

    def _break(self, fixture: TrialFixture, case: str):
        truth_path = fixture.runtime / analyze.TRUTH_FILE_NAME
        manifest_path = fixture.run_dir / "manifest.json"

        def patch_manifest(key, value):
            manifest = json.loads(manifest_path.read_text())
            manifest[key] = value
            manifest_path.write_text(json.dumps(manifest))

        if case == "no_single_loop":
            # Truncate the tracker stream with the truth stream, otherwise
            # this case fails on ``truth_coverage_gap`` and never reaches the
            # loop-domain branch it is named after (round 42 §B).
            lines = truth_path.read_text().splitlines()[:30]
            truth_path.write_text("\n".join(lines) + "\n")
            frames_path = fixture.run_dir / "frames.jsonl"
            frames_path.write_text(
                "\n".join(frames_path.read_text().splitlines()[:30]) + "\n"
            )
        elif case == "truth_gap":
            lines = truth_path.read_text().splitlines()
            del lines[20]
            truth_path.write_text("\n".join(lines) + "\n")
        elif case == "not_at_route_zero":
            lines = truth_path.read_text().splitlines()[10:]
            truth_path.write_text("\n".join(lines) + "\n")
        elif case == "missing_metrics":
            (fixture.run_dir / "metrics.final.json").unlink()
        elif case == "aspect_mismatch":
            path = fixture.run_dir / "metrics.final.json"
            metrics = json.loads(path.read_text())
            metrics["evaluation_projection"]["aspect_width_over_height"] = 1.777
            path.write_text(json.dumps(metrics))
        elif case == "scenario_hash_mismatch":
            scenario = json.loads(fixture.scenario_path.read_text())
            scenario["random_seed"] = 1
            fixture.scenario_path.write_text(json.dumps(scenario))
        elif case == "wrong_arm_policy":
            manifest = json.loads(manifest_path.read_text())
            manifest["cli_args"]["body_policy"] = None
            manifest_path.write_text(json.dumps(manifest))
        elif case == "tracker_mismatch":
            manifest = json.loads(manifest_path.read_text())
            manifest["cli_args"]["tracker"] = "csrt"
            manifest_path.write_text(json.dumps(manifest))
        elif case == "ground_plane_mismatch":
            manifest = json.loads(manifest_path.read_text())
            manifest["cli_args"]["ground_plane_y_m"] = 0.3
            manifest_path.write_text(json.dumps(manifest))
        elif case == "missing_init_box":
            patch_manifest("init", {"frame_id": 0, "box_norm": None})
        elif case == "foreign_truth_scenario":
            lines = []
            for line in truth_path.read_text().splitlines():
                record = json.loads(line)
                record["scenario_id"] = "foreign-play"
                lines.append(json.dumps(record))
            truth_path.write_text("\n".join(lines) + "\n")
        elif case == "tampered_model_sha":
            manifest = json.loads(manifest_path.read_text())
            manifest["tracker"]["model_sha256"]["backbone"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest))
        elif case == "tampered_reanchor_sha":
            patch_manifest("reanchor", {"config_sha256": "0" * 64})
        elif case == "policy_planner_mismatch":
            patch_manifest(
                "body_planner",
                {
                    "policy": "hold",
                    "planner": "threshold-corridor-v1",
                    "config_sha256": _sha(fixture.body_config_path),
                    "scenario_config_sha256": _sha(fixture.scenario_path),
                },
            )
        elif case == "capture_binding_mismatch":
            frames_path = fixture.run_dir / "frames.jsonl"
            lines = []
            for line in frames_path.read_text().splitlines():
                record = json.loads(line)
                record["capture_monotonic_s"] += 0.1
                lines.append(json.dumps(record))
            frames_path.write_text("\n".join(lines) + "\n")
        elif case == "missing_tracker_capture":
            frames_path = fixture.run_dir / "frames.jsonl"
            lines = []
            for line in frames_path.read_text().splitlines():
                record = json.loads(line)
                del record["capture_monotonic_s"]
                lines.append(json.dumps(record))
            frames_path.write_text("\n".join(lines) + "\n")
        elif case == "arm_a_id_with_threshold_policy":
            manifest = json.loads(manifest_path.read_text())
            manifest["cli_args"]["body_policy"] = "threshold"
            manifest_path.write_text(json.dumps(manifest))
        elif case == "manifest_policy_differs_from_cli":
            manifest = json.loads(manifest_path.read_text())
            manifest["body_planner"]["policy"] = "threshold"
            manifest_path.write_text(json.dumps(manifest))
        elif case == "update_frame_planner_mismatch":
            # Round 15 §B.3: only the update rows are corrupted; the init row
            # keeps its correct planner, so the failure must come from the
            # update branch and not from ``init_frame_planner_mismatch``.
            def mutate_update(record):
                record["body_planner"]["name"] = "threshold-corridor-v1"
                return record

            _patch_frames(fixture, mutate_update, stages=("update",))
        elif case == "missing_compute_stage":
            def drop_stage(record):
                del record["compute_stage"]
                return record

            _patch_frames(fixture, drop_stage, stages=("update",))
        elif case == "unknown_compute_stage":
            def rename_stage(record):
                record["compute_stage"] = "reinit"
                return record

            _patch_frames(fixture, rename_stage, stages=("update",))
        elif case == "no_init_frame_record":
            def demote_init(record):
                record["compute_stage"] = "update"
                return record

            _patch_frames(fixture, demote_init, stages=("init",))
        elif case == "init_frame_id_differs_from_manifest":
            patch_manifest(
                "init", {"frame_id": 3, "box_norm": [0.4, 0.4, 0.05, 0.05]}
            )
        elif case == "margin_bytes_differ_from_pin":
            # Same identity, different bytes: the pin is the only thing that
            # can catch it (round 17 §B.1).
            margin = json.loads(fixture.margin_path.read_text())
            margin["visible_arc"]["notes"] = "drifted"
            fixture.margin_path.write_text(json.dumps(margin))
        elif case == "visible_arc_sha_differs_from_pin":
            body = json.loads(fixture.body_config_path.read_text())
            body["measurement_window"]["visible_arc_sha256"] = "e" * 64
            fixture.body_config_path.write_text(json.dumps(body))
        elif case == "margin_pin_missing":
            body = json.loads(fixture.body_config_path.read_text())
            del body["measurement_window"]["artifact_sha256"]
            fixture.body_config_path.write_text(json.dumps(body))
        elif case == "decision_update_without_planner":
            def strip_planner(record):
                if record["skipped_count"] == 0:
                    del record["body_planner"]
                return record

            _patch_frames(fixture, strip_planner, stages=("update",))
        elif case == "catch_up_without_backlog":
            def zero_backlog_catch_up(record):
                record["skipped_count"] = 1
                record["backlog_count"] = 0
                record.pop("body_planner", None)
                return record

            _patch_frames(fixture, zero_backlog_catch_up, stages=("update",))
        elif case == "catch_up_carries_planner":
            def planner_carrying_catch_up(record):
                record["skipped_count"] = 1
                record["backlog_count"] = 1
                return record

            _patch_frames(
                fixture, planner_carrying_catch_up, stages=("update",)
            )
        elif case == "unknown_skipped_count":
            def odd_skipped(record):
                record["skipped_count"] = 2
                record["backlog_count"] = 2
                record.pop("body_planner", None)
                return record

            _patch_frames(fixture, odd_skipped, stages=("update",))
        elif case == "non_integer_counter":
            def bool_counter(record):
                record["skipped_count"] = False
                return record

            _patch_frames(fixture, bool_counter, stages=("update",))
        elif case == "init_frame_counters_not_zero":
            def dirty_init_counters(record):
                record["backlog_count"] = 1
                return record

            _patch_frames(fixture, dirty_init_counters, stages=("init",))
        elif case == "every_update_is_catch_up":
            # Individually legal catch-up rows, but no frame ever ran the
            # planner: the run carries no body decision at all.
            def all_catch_up(record):
                record["skipped_count"] = 1
                record["backlog_count"] = 1
                record.pop("body_planner", None)
                return record

            _patch_frames(fixture, all_catch_up, stages=("update",))
        else:
            raise AssertionError(case)


FROZEN_A = analyze.expected_acquisition_ids("a")
FROZEN_B = analyze.expected_acquisition_ids("b")


class CompareArmsTests(unittest.TestCase):
    def _receipt(self, run_id: str, policy: str, init_box=None,
                 init_frame_id: int = 0, margin_sha: str | None = None,
                 visible_arc_sha: str | None = None) -> dict:
        # Round 29 §C.2: the A1 acquisition receipt carries five extra
        # binding fields; the other nine deliberately do not.
        a1_binding = {}
        if run_id == analyze.A1_ACQUISITION_RUN_ID:
            a1_binding = {
                "acquisition_run_id": analyze.A1_ACQUISITION_RUN_ID,
                "canonical_trial_id": analyze.A1_CANONICAL_TRIAL_ID,
                "attempt_number": analyze.A1_ATTEMPT_NUMBER,
                "predecessor_void_manifest_sha256":
                    analyze.A1_PREDECESSOR_VOID_MANIFEST_SHA256,
                "predecessor_void_frames_sha256":
                    analyze.A1_PREDECESSOR_VOID_FRAMES_SHA256,
            }
        # Round 42 §B / round 43 §C.1: A2 carries the same block plus the
        # third predecessor hash, and ``--compare`` now checks it per key.
        elif run_id == analyze.A2_ACQUISITION_RUN_ID:
            a1_binding = {
                "acquisition_run_id": analyze.A2_ACQUISITION_RUN_ID,
                "canonical_trial_id": analyze.A2_CANONICAL_TRIAL_ID,
                "attempt_number": analyze.A2_ATTEMPT_NUMBER,
                "predecessor_void_manifest_sha256":
                    analyze.A2_PREDECESSOR_VOID_MANIFEST_SHA256,
                "predecessor_void_frames_sha256":
                    analyze.A2_PREDECESSOR_VOID_FRAMES_SHA256,
                "predecessor_void_truth_sha256":
                    analyze.A2_PREDECESSOR_VOID_TRUTH_SHA256,
            }
        return {
            "run_id": run_id,
            **a1_binding,
            "body_policy": policy,
            "body_planner_name": analyze.POLICY_PLANNER[policy],
            "scenario_sha256": "s" * 64,
            "condition": "follow",
            "track_id": "target-0",
            "ground_plane_y_m": 0.2,
            "tracker": "nanotrack-v2",
            "tracker_pinned_version": "test-pin",
            "tracker_backend": "opencv-dnn",
            "tracker_model_sha256": dict(MODEL_HASHES),
            "reanchor_config_sha256": "r" * 64,
            "tracker_model_spec_sha256": "m" * 64,
            "init_box_norm": init_box or [0.4, 0.4, 0.05, 0.05],
            "init_frame_id": init_frame_id,
            "body_config_sha256": "b" * 64,
            # Round 17 §B.1: the measurement-window source is part of the
            # cross-run identity, not just a recorded field.
            "margin_artifact_sha256": margin_sha or "c" * 64,
            "visible_arc_sha256": visible_arc_sha or "4" * 64,
        }

    def _write_analysis(
        self,
        runtime: Path,
        run_id: str,
        policy: str,
        series: dict[str, tuple[float, float, float]],
        init_box=None,
        init_frame_id: int = 0,
        margin_sha: str | None = None,
        visible_arc_sha: str | None = None,
    ):
        run_dir = runtime / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        analysis = {
            "schema_version": analyze.ANALYSIS_SCHEMA,
            "receipt": self._receipt(
                run_id, policy, init_box, init_frame_id,
                margin_sha, visible_arc_sha,
            ),
            "h1": {"full_loop_c_geom": 0.7, "disposition": "WITHIN_RANGE"},
            "c_quality_series": {
                point: list(values) for point, values in series.items()
            },
        }
        (run_dir / analyze.ANALYSIS_FILE_NAME).write_text(json.dumps(analysis))

    def _uniform_series(self, area, indicator, center) -> dict:
        return {
            f"{(index + 0.5) * 0.5:.6f}": (area, indicator, center)
            for index in range(30)
        }

    def _populate(self, runtime: Path, b_series, b_policy="threshold",
                  a_init_box=None):
        for index in range(5):
            self._write_analysis(
                runtime, FROZEN_A[index], "hold",
                self._uniform_series(100.0, 1.0, 10.0),
                init_box=a_init_box,
            )
            self._write_analysis(runtime, FROZEN_B[index], b_policy, b_series)

    def test_h2_supported_when_all_components_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            self._populate(runtime, self._uniform_series(110.0, 1.0, 8.0))
            # Arm A indicator 1.0 vs B 1.0 gives zero improvement on that
            # component, so use a worse A for the supported case instead.
            for index in range(5):
                self._write_analysis(
                    runtime, FROZEN_A[index], "hold",
                    self._uniform_series(100.0, 0.0, 10.0),
                )
            result = analyze.compare_arms(runtime, FROZEN_A, FROZEN_B)
            self.assertEqual(result["h2"]["verdict"], "H2_SUPPORTED")
            self.assertEqual(len(result["h2"]["passed_components"]), 3)
            self.assertEqual(len(result["h1_arm_a_trials"]), 5)
            self.assertEqual(len(result["analysis_sha256"]), 10)

    def test_partial_and_ineffective_verdicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            self._populate(runtime, self._uniform_series(110.0, 1.0, 10.0))
            result = analyze.compare_arms(runtime, FROZEN_A, FROZEN_B)
            self.assertEqual(
                result["h2"]["verdict"], "THRESHOLD_ALLOCATION_PARTIAL"
            )
            self.assertEqual(
                result["h2"]["passed_components"], ["area_median_px"]
            )
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            self._populate(runtime, self._uniform_series(90.0, 0.0, 12.0))
            result = analyze.compare_arms(runtime, FROZEN_A, FROZEN_B)
            self.assertEqual(
                result["h2"]["verdict"], "THRESHOLD_ALLOCATION_INEFFECTIVE"
            )

    def test_indicator_component_zero_improvement_21_to_22_px(self):
        """Round 13 §B.2 counterexample: A=21 px vs B=22 px raw min-side
        improvement gives indicator 1 -> 1 on both arms, so the frozen
        share improvement is exactly 0 and the component must NOT pass -
        even though a raw-pixel difference would be +1 px."""
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            # Indicators identical (both sides fully >= 20 px): B improves
            # area and centre error but NOT the indicator share.
            self._populate(runtime, self._uniform_series(110.0, 1.0, 8.0))
            result = analyze.compare_arms(runtime, FROZEN_A, FROZEN_B)
            component = result["h2"]["components"]["min_side_ge20_share"]
            self.assertEqual(component["summary_median_improvement"], 0.0)
            self.assertFalse(component["pass"])
            self.assertNotEqual(result["h2"]["verdict"], "H2_SUPPORTED")

    def test_true_pairing_rejects_naive_median_difference(self):
        """Round 12 §B.4 counterexample: per grid point A=[1,2,3],
        B=[0.5,2.5,2.5]. 'median(B) - median(A)' = +0.5 (naive pass), but
        the per-position paired differences [-0.5,+0.5,-0.5] have median
        -0.5, so the frozen paired rule must FAIL the component."""
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            a_series = {"0.5": (1.0, 1.0, 10.0), "1.5": (2.0, 1.0, 10.0),
                        "2.5": (3.0, 1.0, 10.0)}
            b_series = {"0.5": (0.5, 1.0, 8.0), "1.5": (2.5, 1.0, 8.0),
                        "2.5": (2.5, 1.0, 8.0)}
            for index in range(5):
                self._write_analysis(runtime, FROZEN_A[index], "hold", a_series)
                self._write_analysis(
                    runtime, FROZEN_B[index], "threshold", b_series
                )
            naive_b = analyze.weighted_median([2.5, 2.5, 0.5], [1, 1, 1])
            naive_a = analyze.weighted_median([1, 2, 3], [1, 1, 1])
            self.assertGreater(naive_b - naive_a, 0.0)  # naive would pass
            result = analyze.compare_arms(runtime, FROZEN_A, FROZEN_B)
            area = result["h2"]["components"]["area_median_px"]
            self.assertLess(area["summary_median_improvement"], 0.0)
            self.assertFalse(area["pass"])
            self.assertEqual(
                result["h2"]["verdict"], "THRESHOLD_ALLOCATION_PARTIAL"
            )

    def test_frozen_id_sequence_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            self._populate(runtime, self._uniform_series(110.0, 1.0, 8.0))
            # Duplicate ID (same A trial twice, dropping trial 5).
            duplicated = FROZEN_A[:4] + [FROZEN_A[0]]
            with self.assertRaises(analyze.AnalysisError):
                analyze.compare_arms(runtime, duplicated, FROZEN_B)
            # Wrong order (trials 1/2 swapped).
            reordered = [FROZEN_A[1], FROZEN_A[0], *FROZEN_A[2:]]
            with self.assertRaises(analyze.AnalysisError):
                analyze.compare_arms(runtime, reordered, FROZEN_B)
            # Wrong arm in the B list.
            with self.assertRaises(analyze.AnalysisError):
                analyze.compare_arms(runtime, FROZEN_A, FROZEN_A)

    def test_attempt_binding_mismatch_fails_closed(self):
        """Round 43 §C.1 (BC-BODY1-32): ``--compare`` checks the A2
        acquisition receipt's binding per key - all six, including
        ``predecessor_void_truth_sha256`` - exactly as it already did for A1.
        Tampering with any one key, or dropping it, must fail closed under its
        own name. The A1 half is coverage added alongside: that branch had
        shipped since round 29 with no test at all."""
        cases = (
            (1, "a2", "acquisition_run_id", "p1-m3-body-001-arm-a-trial-2"),
            (1, "a2", "canonical_trial_id", "p1-m3-body-001-arm-a-trial-3"),
            (1, "a2", "attempt_number", 1),
            (1, "a2", "predecessor_void_manifest_sha256", "0" * 64),
            (1, "a2", "predecessor_void_frames_sha256", "0" * 64),
            (1, "a2", "predecessor_void_truth_sha256", "0" * 64),
            (0, "a1", "acquisition_run_id", "p1-m3-body-001-arm-a-trial-1"),
            (0, "a1", "canonical_trial_id", "p1-m3-body-001-arm-a-trial-3"),
            (0, "a1", "attempt_number", 3),
            (0, "a1", "predecessor_void_manifest_sha256", "0" * 64),
            (0, "a1", "predecessor_void_frames_sha256", "0" * 64),
        )
        for slot, marker, key, wrong_value in cases:
            for mode in ("wrong_value", "missing"):
                with self.subTest(slot=marker, key=key, mode=mode):
                    with tempfile.TemporaryDirectory() as tmp:
                        runtime = Path(tmp) / "runtime"
                        self._populate(
                            runtime, self._uniform_series(110.0, 1.0, 8.0)
                        )
                        path = (
                            runtime / "runs" / FROZEN_A[slot]
                            / analyze.ANALYSIS_FILE_NAME
                        )
                        analysis = json.loads(path.read_text())
                        if mode == "missing":
                            del analysis["receipt"][key]
                        else:
                            analysis["receipt"][key] = wrong_value
                        path.write_text(json.dumps(analysis))
                        with self.assertRaises(analyze.AnalysisError) as caught:
                            analyze.compare_arms(runtime, FROZEN_A, FROZEN_B)
                        self.assertEqual(
                            str(caught.exception),
                            f"{marker}_attempt_binding_mismatch:{key}",
                        )

    def test_binding_keys_are_not_cross_run_identity(self):
        """BC-BODY1-32 explicitly keeps the six keys out of ``identity_keys``
        (round 29 §C.2's reasoning): they are single-run bindings, so the
        eight canonical-slot runs must stay free of them and an untampered
        ten-run set must compare cleanly."""
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            self._populate(runtime, self._uniform_series(110.0, 1.0, 8.0))
            result = analyze.compare_arms(runtime, FROZEN_A, FROZEN_B)
            self.assertEqual(len(result["h1_arm_a_trials"]), 5)
            self.assertEqual(result["arm_a"], list(FROZEN_A))
            binding_keys = {
                "acquisition_run_id",
                "canonical_trial_id",
                "attempt_number",
                "predecessor_void_manifest_sha256",
                "predecessor_void_frames_sha256",
                "predecessor_void_truth_sha256",
            }
            for run_id in (*FROZEN_A[2:], *FROZEN_B):
                receipt = json.loads(
                    (
                        runtime / "runs" / run_id / analyze.ANALYSIS_FILE_NAME
                    ).read_text()
                )["receipt"]
                self.assertFalse(binding_keys & set(receipt), run_id)

    def test_cross_run_identity_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            self._populate(
                runtime,
                self._uniform_series(110.0, 1.0, 8.0),
                a_init_box=[0.1, 0.1, 0.1, 0.1],
            )
            # A-trial receipts carry a different init box than B-trial
            # receipts: the frozen initial box must be identical across all
            # ten runs.
            with self.assertRaises(analyze.AnalysisError):
                analyze.compare_arms(runtime, FROZEN_A, FROZEN_B)

    def test_copied_analysis_is_a_duplicate_trial(self):
        """Round 14 §A.3/§B.3: A1's analysis bytes copied into A2's path
        must fail - the receipt's run_id does not match the frozen path,
        and identical content would also trip duplicate_trial_analysis."""
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            self._populate(runtime, self._uniform_series(110.0, 1.0, 8.0))
            source = (
                runtime / "runs" / FROZEN_A[0] / analyze.ANALYSIS_FILE_NAME
            ).read_bytes()
            (runtime / "runs" / FROZEN_A[1] / analyze.ANALYSIS_FILE_NAME
             ).write_bytes(source)
            with self.assertRaises(analyze.AnalysisError):
                analyze.compare_arms(runtime, FROZEN_A, FROZEN_B)

    def test_init_frame_id_enters_compare_identity(self):
        """Round 14 §A.4/§B.3: init_frame_id differs across arms -> the
        ten-run compare must fail even with identical init boxes."""
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            for index in range(5):
                self._write_analysis(
                    runtime, FROZEN_A[index], "hold",
                    self._uniform_series(100.0, 1.0, 10.0), init_frame_id=99,
                )
                self._write_analysis(
                    runtime, FROZEN_B[index], "threshold",
                    self._uniform_series(110.0, 1.0, 8.0), init_frame_id=0,
                )
            with self.assertRaises(analyze.AnalysisError):
                analyze.compare_arms(runtime, FROZEN_A, FROZEN_B)

    def test_margin_artifact_sha_enters_compare_identity(self):
        """Round 17 §B.2(b) (Review F1): one of the ten runs analysed a
        different margin artifact -> the measurement-window source is not
        shared, so the ten-run compare must fail."""
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            self._populate(runtime, self._uniform_series(110.0, 1.0, 8.0))
            self._write_analysis(
                runtime, FROZEN_A[3], "hold",
                self._uniform_series(100.0, 1.0, 10.0),
                margin_sha="9" * 64,
            )
            with self.assertRaises(analyze.AnalysisError):
                analyze.compare_arms(runtime, FROZEN_A, FROZEN_B)

    def test_visible_arc_sha_enters_compare_identity(self):
        """Round 17 §B.2(c) (Review F1): same margin bytes claim, different
        visible-arc digest in one run -> compare must still fail."""
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            self._populate(runtime, self._uniform_series(110.0, 1.0, 8.0))
            self._write_analysis(
                runtime, FROZEN_B[2], "threshold",
                self._uniform_series(110.0, 1.0, 8.0),
                visible_arc_sha="7" * 64,
            )
            with self.assertRaises(analyze.AnalysisError):
                analyze.compare_arms(runtime, FROZEN_A, FROZEN_B)

    def test_compare_requires_create_once_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            self._populate(runtime, self._uniform_series(110.0, 1.0, 8.0))
            base = ["--compare", "--runtime", str(runtime),
                    "--arm-a", ",".join(FROZEN_A),
                    "--arm-b", ",".join(FROZEN_B)]
            # No --output: not a formal success path.
            self.assertEqual(analyze.main(base), 2)
            output = Path(tmp) / "compare.json"
            self.assertEqual(analyze.main([*base, "--output", str(output)]), 0)
            self.assertTrue(output.is_file())
            # Existing output: create-once violation.
            self.assertEqual(analyze.main([*base, "--output", str(output)]), 2)


PRODUCTION_SCENARIO_PATH = PROJECT_ROOT / "config" / "scenario.default.json"
PRODUCTION_BODY_CONFIG_PATH = PROJECT_ROOT / "config" / "p1-m3-body-001.json"
PRODUCTION_MARGIN_PATH = (
    PROJECT_ROOT / "docs" / "evidence" / "P1-M3-BODY-001-scene-body-margin.json"
)
PRODUCTION_REANCHOR_PATH = (
    PROJECT_ROOT / "config" / "detector-reanchor.models.json"
)
PRODUCTION_MODEL_SPEC_PATH = PROJECT_ROOT / "config" / "nanotrack-v2.models.json"


class ProductionReplayRun:
    """A trial run built only from the real checked-in frozen inputs and the
    line-equivalent production ``LoopTargetVehicle.Step`` replay, corner
    cutting included (round 13 §B.1/§B.5).

    ``frame_count`` sets how far the Play ran at the frozen 5 Hz / 2.0 m/s.
    ``position_source`` may only *reorder* replayed positions - mapping a
    frame to another frame's real trajectory point - so a counterexample is
    still made of production coordinates rather than hand-authored ones
    (workflow §4.4 R3 condition (1))."""

    def __init__(
        self,
        root: Path,
        frame_count: int,
        run_id: str | None = None,
        position_source: dict[int, int] | None = None,
    ):
        self.frame_count = frame_count
        self.run_id = run_id or analyze.A1_ACQUISITION_RUN_ID
        self.scenario_path = PRODUCTION_SCENARIO_PATH
        self.margin_path = PRODUCTION_MARGIN_PATH
        self.body_config_path = PRODUCTION_BODY_CONFIG_PATH
        self.runtime = root / "runtime"
        self.run_dir = self.runtime / "runs" / self.run_id
        self.run_dir.mkdir(parents=True)

        self.scenario = json.loads(self.scenario_path.read_text())
        self.margin = json.loads(self.margin_path.read_text())
        self.model_spec = json.loads(PRODUCTION_MODEL_SPEC_PATH.read_text())
        self.vertices = [
            (p["x"], p["y"], p["z"])
            for p in self.scenario["target"]["route_world_m"]
        ]
        self.cumulative, self.perimeter = analyze._cumulative_lengths(
            self.vertices
        )
        self.capture_hz = self.scenario["sensor"]["capture_hz"]
        replayed = replay_loop_target(
            self.vertices,
            self.scenario["target"]["speed_mps"],
            1.0 / self.capture_hz,
            frame_count,
        )
        self.positions = [
            replayed[(position_source or {}).get(index, index)]
            for index in range(frame_count)
        ]
        self.mileages = [
            analyze.route_mileage(position, self.vertices, self.cumulative)[0]
            for position in self.positions
        ]
        self.unwrapped = analyze._unwrap_mileage(self.mileages, self.perimeter)
        self._write_truth()
        self._write_run()
        self.holds = PredecessorHolds(self.runtime)

    def _visible(self, mileage: float) -> bool:
        arc = self.margin["visible_arc"]["intervals_m"][0]
        wrapped = mileage % self.perimeter
        if arc["start_m"] <= wrapped <= min(arc["end_m"], self.perimeter):
            return True
        return arc["wraps"] and wrapped <= arc["end_m"] - self.perimeter

    def _write_truth(self):
        with (self.runtime / analyze.TRUTH_FILE_NAME).open("w") as handle:
            for frame_id, (x, z) in enumerate(self.positions):
                vis = self._visible(self.mileages[frame_id])
                handle.write(
                    json.dumps(
                        {
                            "schema_version": analyze.TRUTH_SCHEMA,
                            "scenario_id": self.scenario["scenario_id"],
                            "frame_id": frame_id,
                            "simulation_time_s": frame_id / self.capture_hz,
                            "capture_monotonic_s": frame_id / self.capture_hz,
                            "capture_monotonic_clock_id": "system-stopwatch/v1",
                            "target_world_x_m": x,
                            "target_world_y_m": 0.2,
                            "target_world_z_m": z,
                            "body_world_x_m": 132.0,
                            "body_world_y_m": 25.0,
                            "body_world_z_m": 117.0,
                            "applied_velocity_x_mps": 0.0,
                            "applied_velocity_y_mps": 0.0,
                            "applied_velocity_z_mps": 0.0,
                            "intersects_frustum": vis,
                            "has_unoccluded_sample": vis,
                            "geometrically_visible": vis,
                            "visible_sample_fraction": 1.0 if vis else 0.0,
                            "truth_box_available": vis,
                            "truth_box_x": 0.4 if vis else -1.0,
                            "truth_box_y": 0.4 if vis else -1.0,
                            "truth_box_width": 0.05 if vis else -1.0,
                            "truth_box_height": 0.05 if vis else -1.0,
                            "truth_center_x_px": 272.0 if vis else -1.0,
                            "truth_center_y_px": 204.0 if vis else -1.0,
                            "target_bbox_area_px": 768.0 if vis else 0.0,
                            "target_center_error_px": 5.0 if vis else 0.0,
                            "gimbal_saturated": False,
                            "tether_saturated": False,
                            "evaluation_aspect_width_over_height": 640.0 / 480.0,
                        }
                    )
                    + "\n"
                )

    def _write_run(self):
        expected_models = {
            name: model["sha256"]
            for name, model in self.model_spec["models"].items()
        }
        manifest = {
            "schema_version": analyze.MANIFEST_SCHEMA,
            "run_id": self.run_id,
            "scenario_id": self.scenario["scenario_id"],
            "cli_args": {
                "body_policy": "hold",
                "tracker": "nanotrack-v2",
                "condition": "follow",
                "track_id": self.scenario["target"]["track_id"],
                "ground_plane_y_m": 0.2,
                "reanchor_config": str(PRODUCTION_REANCHOR_PATH),
                "tracker_model_spec": str(PRODUCTION_MODEL_SPEC_PATH),
            },
            "init": {"frame_id": 0, "box_norm": [0.4, 0.4, 0.05, 0.05]},
            "tracker": {
                "name": "nanotrack-v2",
                "backend": "opencv-dnn",
                "pinned_version": "test-pin",
                "model_sha256": expected_models,
            },
            "reanchor": {"config_sha256": _sha(PRODUCTION_REANCHOR_PATH)},
            "body_planner": {
                "policy": "hold",
                "planner": "hold-v1",
                "config_sha256": _sha(self.body_config_path),
                "scenario_config_sha256": _sha(self.scenario_path),
            },
        }
        (self.run_dir / "manifest.json").write_text(json.dumps(manifest))
        # Round 17 §B.4: replay the real runbook startup. Frame 0 is the
        # manifest init row (counters zero, as the INIT path writes it).
        # The first poll after init then catches up the frames retained
        # while the operator paused: production sets
        # `backlog_count = len(processed) - 1` on *every* row of the batch
        # and `skipped_count = 0 if is_latest else 1`, and runs `_body_step`
        # only on the latest one - so frames 1-3 carry no `body_planner` at
        # all (track_loop.py:530-564). Frames 5+ are single-frame batches.
        catch_up_backlog = 3  # frames 1..4 processed in one batch
        with (self.run_dir / "frames.jsonl").open("w") as handle:
            for frame_id in range(self.frame_count):
                record = {
                    "frame_id": frame_id,
                    "capture_monotonic_s": frame_id / self.capture_hz,
                    "ok": True,
                    "box_norm": [0.4, 0.4, 0.05, 0.05],
                    "compute_stage": "init" if frame_id == 0 else "update",
                    "backlog_count": 0,
                    "skipped_count": 0,
                    "body_planner": {
                        "name": "hold-v1",
                        "mode": "hold",
                        "published": True,
                    },
                }
                if 1 <= frame_id <= 4:
                    record["backlog_count"] = catch_up_backlog
                    if frame_id < 4:
                        record["skipped_count"] = 1
                        del record["body_planner"]
                handle.write(json.dumps(record) + "\n")
        (self.run_dir / "metrics.final.json").write_text(
            json.dumps(
                {
                    "schema_version": "tethered-evaluation/v1",
                    "evaluation_projection": {
                        "sensor_width_px": 640,
                        "sensor_height_px": 480,
                        "aspect_width_over_height": 640.0 / 480.0,
                    },
                    "aggregate": {
                        "sensor_frames": self.frame_count,
                        "c_geom": 0.5,
                    },
                }
            )
        )

    def analyze(self, verify: bool = False):
        return self.holds.run(
            lambda: analyze.analyze_trial(
                self.runtime,
                self.run_id,
                self.scenario_path,
                self.margin_path,
                self.body_config_path,
                verify=verify,
            )
        )


class LoopDomainAdmissibilityTests(unittest.TestCase):
    """Round 42 §A/§B (BC-BODY1-23/-25): the admissibility criterion keeps
    only the ``< P`` lower bound, and two compensating domain-integrity gates
    replace the retired ``>= 2P`` arm. Every fixture here is the production
    replay over the real checked-in frozen inputs; counterexamples only
    reorder replayed positions."""

    # 5 Hz x 2.0 m/s over the frozen 212.9706 m route: the first sample at or
    # beyond one perimeter is frame 539.
    CLOSURE_FRAME = 539

    def _assert_fails_closed(self, run: ProductionReplayRun, prefix: str):
        with self.assertRaises(analyze.AnalysisError) as caught:
            run.analyze()
        self.assertTrue(
            str(caught.exception).startswith(prefix),
            f"expected {prefix!r}, got {caught.exception}",
        )
        self.assertFalse(
            (run.run_dir / analyze.ANALYSIS_FILE_NAME).exists(),
            "a failed loop-domain gate must write nothing",
        )

    def test_below_one_loop_fails_closed(self):
        """Retained lower bound: a Play that never closed the route."""
        with tempfile.TemporaryDirectory() as tmp:
            run = ProductionReplayRun(Path(tmp), 400)
            self.assertLess(max(run.unwrapped), run.perimeter)
            self._assert_fails_closed(run, "trial_invalid_no_single_loop:")

    def test_post_closure_sample_below_perimeter_fails_closed(self):
        """A second-lap sample that falls back into the ``[0, P)`` domain
        would smuggle a lap-two sample into H1."""
        with tempfile.TemporaryDirectory() as tmp:
            # Frame 600 (second lap) replays frame 520's position, whose route
            # mileage is high enough that the unwrap drops a lap.
            run = ProductionReplayRun(Path(tmp), 650, position_source={600: 520})
            self.assertGreaterEqual(run.unwrapped[self.CLOSURE_FRAME], run.perimeter)
            self.assertLess(run.unwrapped[600], run.perimeter)
            self._assert_fails_closed(
                run, "loop_domain_sample_below_perimeter_after_closure:600:"
            )

    def test_backward_unwrapped_step_fails_closed(self):
        """A backward step that stays above ``P`` never reaches the
        post-closure gate; monotonicity is what catches it."""
        with tempfile.TemporaryDirectory() as tmp:
            # Frame 600 replays frame 590's position: 4 m back, both laps deep
            # enough that every sample stays at or above one perimeter.
            run = ProductionReplayRun(Path(tmp), 650, position_source={600: 590})
            self.assertGreaterEqual(run.unwrapped[600], run.perimeter)
            self.assertLess(run.unwrapped[600], run.unwrapped[599])
            self._assert_fails_closed(
                run, "loop_domain_unwrapped_backward_step:600:"
            )

    def test_extra_laps_leave_the_loop_domain_bit_identical(self):
        """The real trial-2 shape: a Play that kept running past closure.
        Analysis must succeed and reproduce the one-loop domain exactly."""
        with tempfile.TemporaryDirectory() as tmp:
            short = ProductionReplayRun(Path(tmp), self.CLOSURE_FRAME + 1).analyze()
        with tempfile.TemporaryDirectory() as tmp:
            long_run = ProductionReplayRun(Path(tmp), 1700)
            self.assertGreater(max(long_run.unwrapped), 3.0 * long_run.perimeter)
            long_analysis = long_run.analyze()
        # ``h1`` also carries the online reference fields, which are per-Play
        # by construction; the recomputed loop domain is what must not move.
        self.assertEqual(
            long_analysis["h1"]["full_loop_c_geom"],
            short["h1"]["full_loop_c_geom"],
        )
        self.assertEqual(
            long_analysis["h1"]["disposition"], short["h1"]["disposition"]
        )
        self.assertEqual(
            long_analysis["domains"]["loop_frame_count"],
            short["domains"]["loop_frame_count"],
        )
        self.assertEqual(
            long_analysis["c_quality_series"], short["c_quality_series"]
        )


ARCHIVED_A1_RUN_DIR = (
    PROJECT_ROOT / "runtime" / "runs" / analyze.A1_ACQUISITION_RUN_ID
)
ARCHIVED_A1_HOLD_DIR = (
    PROJECT_ROOT / "runtime" / "runs" / analyze.A1_PREDECESSOR_HOLD_DIR_NAME
)


@unittest.skipUnless(
    ARCHIVED_A1_RUN_DIR.is_dir() and ARCHIVED_A1_HOLD_DIR.is_dir(),
    "archived A1 run is an untracked runtime/ asset; skipped when absent",
)
class ArchivedRunLoopDomainTests(unittest.TestCase):
    """The same three gates on a byte copy of the real archived A1 run
    (workflow §4.4 R3 condition (1), archived-real-run option).

    Nothing here touches the real site: every case works on a copy under a
    temporary directory, and the predecessor hold is the real one, so its
    shipped SHA constants are used unpatched. Counterexamples only truncate
    the stream or replay one record's coordinates onto another - no
    coordinate is invented."""

    FROZEN_C_GEOM = 0.5784550773737355

    def _copy(self, tmp: str):
        runtime = Path(tmp) / "runtime"
        (runtime / "runs").mkdir(parents=True)
        run_dir = runtime / "runs" / analyze.A1_ACQUISITION_RUN_ID
        shutil.copytree(ARCHIVED_A1_RUN_DIR, run_dir)
        shutil.copytree(
            ARCHIVED_A1_HOLD_DIR,
            runtime / "runs" / analyze.A1_PREDECESSOR_HOLD_DIR_NAME,
        )
        # The copy re-derives its own analysis (create-once).
        (run_dir / analyze.ANALYSIS_FILE_NAME).unlink()
        return runtime, run_dir

    def _analyze(self, runtime: Path):
        # All inputs are already collected in the copy, so these paths are
        # never read; they only satisfy the signature.
        return analyze.analyze_trial(
            runtime,
            analyze.A1_ACQUISITION_RUN_ID,
            PRODUCTION_SCENARIO_PATH,
            PRODUCTION_MARGIN_PATH,
            PRODUCTION_BODY_CONFIG_PATH,
        )

    def _mileages(self, run_dir: Path):
        scenario = json.loads((run_dir / "scenario.json").read_text())
        vertices = analyze._route_points(scenario)
        cumulative, perimeter = analyze._cumulative_lengths(vertices)
        records = [
            json.loads(line)
            for line in (run_dir / analyze.TRUTH_FILE_NAME)
            .read_text()
            .splitlines()
            if line.strip()
        ]
        raw = [
            analyze.route_mileage(
                (record["target_world_x_m"], record["target_world_z_m"]),
                vertices,
                cumulative,
            )[0]
            for record in records
        ]
        return records, raw, analyze._unwrap_mileage(raw, perimeter), perimeter

    def _write_truth(self, run_dir: Path, records):
        (run_dir / analyze.TRUTH_FILE_NAME).write_text(
            "".join(json.dumps(record) + "\n" for record in records)
        )

    def _assert_fails_closed(self, runtime: Path, run_dir: Path, prefix: str):
        with self.assertRaises(analyze.AnalysisError) as caught:
            self._analyze(runtime)
        self.assertTrue(
            str(caught.exception).startswith(prefix),
            f"expected {prefix!r}, got {caught.exception}",
        )
        self.assertFalse((run_dir / analyze.ANALYSIS_FILE_NAME).exists())

    def test_real_run_reproduces_and_is_domain_intact(self):
        """The archived 1.9385-lap run analyses to its frozen value, and its
        real series violates neither new gate (0 backward steps, 0
        post-closure samples below P)."""
        with tempfile.TemporaryDirectory() as tmp:
            runtime, run_dir = self._copy(tmp)
            _, _, unwrapped, perimeter = self._mileages(run_dir)
            closure = next(
                index
                for index, value in enumerate(unwrapped)
                if value >= perimeter
            )
            self.assertEqual(
                [
                    index
                    for index in range(1, len(unwrapped))
                    if unwrapped[index] < unwrapped[index - 1]
                ],
                [],
            )
            self.assertEqual(
                [
                    index
                    for index in range(closure + 1, len(unwrapped))
                    if unwrapped[index] < perimeter
                ],
                [],
            )
            self.assertGreater(max(unwrapped), perimeter)
            result = self._analyze(runtime)
            self.assertEqual(
                result["h1"]["full_loop_c_geom"], self.FROZEN_C_GEOM
            )
            self.assertEqual(result["h1"]["disposition"], "WITHIN_RANGE")

    def test_truncated_below_one_loop_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, run_dir = self._copy(tmp)
            records, _, unwrapped, perimeter = self._mileages(run_dir)
            keep = next(
                index
                for index, value in enumerate(unwrapped)
                if value >= perimeter
            )
            kept_ids = {record["frame_id"] for record in records[:keep]}
            self._write_truth(run_dir, records[:keep])
            frames_path = run_dir / "frames.jsonl"
            frames_path.write_text(
                "".join(
                    line + "\n"
                    for line in frames_path.read_text().splitlines()
                    if json.loads(line).get("frame_id") in kept_ids
                )
            )
            self._assert_fails_closed(
                runtime, run_dir, "trial_invalid_no_single_loop:"
            )

    def test_backward_step_on_real_bytes_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, run_dir = self._copy(tmp)
            records, _, unwrapped, perimeter = self._mileages(run_dir)
            target = len(records) - 1
            donor = next(
                index
                for index in range(target - 1, 0, -1)
                if unwrapped[index] < unwrapped[target] - 1.0
                and unwrapped[index] >= perimeter
            )
            for axis in ("target_world_x_m", "target_world_z_m"):
                records[target][axis] = records[donor][axis]
            self._write_truth(run_dir, records)
            self._assert_fails_closed(
                runtime,
                run_dir,
                f"loop_domain_unwrapped_backward_step:{target}:",
            )

    def test_post_closure_sample_below_perimeter_on_real_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, run_dir = self._copy(tmp)
            records, raw, unwrapped, perimeter = self._mileages(run_dir)
            closure = next(
                index
                for index, value in enumerate(unwrapped)
                if value >= perimeter
            )
            # The last sample of lap one has the largest wrapped mileage;
            # replaying it early in lap two makes the unwrap drop a lap, which
            # is exactly the second-lap sample the [0, P) filter must not see.
            donor = max(range(closure), key=lambda index: raw[index])
            target = next(
                index
                for index in range(closure + 1, len(records))
                if raw[donor] > raw[index - 1] + perimeter * 0.5
            )
            for axis in ("target_world_x_m", "target_world_z_m"):
                records[target][axis] = records[donor][axis]
            self._write_truth(run_dir, records)
            self._assert_fails_closed(
                runtime,
                run_dir,
                "loop_domain_sample_below_perimeter_after_closure:"
                f"{target}:",
            )


class ProductionReplayIntegrationTests(unittest.TestCase):
    """Round 13 §B.1/§B.5: real checked-in frozen inputs, 130 s at 5 Hz
    (650 frames), positions from the line-equivalent production Step
    replay (corner cutting included) - not ideal polyline interpolation."""

    def test_production_replay_650_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = ProductionReplayRun(Path(tmp), 650)  # 130 s at frozen 5 Hz
            self.assertAlmostEqual(run.perimeter, 212.9706, places=3)
            deviations = [
                analyze.route_mileage(
                    position, run.vertices, run.cumulative
                )[1]
                for position in run.positions
            ]
            # Production corner cutting exists and stays inside the derived
            # tolerance (the tolerance is exercised, not assumed).
            self.assertGreater(max(deviations), 0.01)
            self.assertLess(max(deviations), analyze.OFF_ROUTE_TOL_M)

            result = run.analyze()
            self.assertEqual(
                result["receipt"]["scenario_sha256"], _sha(run.scenario_path)
            )
            self.assertEqual(result["window"]["tracking_iou_threshold"], 0.3)
            self.assertEqual(result["h1"]["disposition"], "WITHIN_RANGE")
            self.assertEqual(
                result["domains"]["measurement_window_m"], [0.0, 62.5]
            )
            self.assertEqual(result["cost"]["body_motion_effort_m"], 0.0)
            # 650 truth frames with zero metadata files present.
            self.assertEqual(result["receipt"]["truth_record_count"], 650)
            self.assertEqual(run.analyze(verify=True), result)

    def test_beyond_bound_deviation_fails(self):
        """A trajectory point beyond the derived 0.5 m switch bound must
        fail closed (the tolerance is not a rubber stamp)."""
        vertices = [(x, 0.2, z) for x, z in SQUARE]
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TrialFixture(Path(tmp))
            truth_path = fixture.runtime / analyze.TRUTH_FILE_NAME
            lines = truth_path.read_text().splitlines()
            record = json.loads(lines[20])
            record["target_world_x_m"] += 0.6  # beyond 0.5 + 1e-3
            lines[20] = json.dumps(record)
            truth_path.write_text("\n".join(lines) + "\n")
            with self.assertRaises(analyze.AnalysisError) as ctx:
                fixture.analyze()
            self.assertIn("truth_off_route", str(ctx.exception))


class TruthOneWayFlowTests(unittest.TestCase):
    def test_no_controller_reads_m3_truth(self):
        offenders = []
        for path in (PROJECT_ROOT / "controller").glob("*.py"):
            if "m3_body_truth" in path.read_text():
                offenders.append(path.name)
        self.assertEqual(offenders, [])




class AttemptIdentityBindingTests(unittest.TestCase):
    """Round 29 §C.2/§C.6: the A1 acquisition ID maps to the canonical slot,
    the consumed void ID and every other attempt suffix are rejected, and the
    A1-only predecessor binding is mechanically enforced."""

    def test_a1_acquisition_id_maps_to_canonical_slot(self):
        self.assertEqual(
            analyze.canonical_trial_id(analyze.A1_ACQUISITION_RUN_ID),
            analyze.A1_CANONICAL_TRIAL_ID,
        )
        self.assertEqual(analyze._expected_policy(analyze.A1_ACQUISITION_RUN_ID),
                         analyze.ARM_A_POLICY)

    def test_a2_acquisition_id_maps_to_canonical_slot(self):
        """Round 42 §B (BC-BODY1-26): slot 2's substitute acquisition ID."""
        self.assertEqual(
            analyze.A2_ACQUISITION_RUN_ID,
            "p1-m3-body-001-arm-a-trial-2-attempt-2",
        )
        self.assertEqual(
            analyze.canonical_trial_id(analyze.A2_ACQUISITION_RUN_ID),
            analyze.A2_CANONICAL_TRIAL_ID,
        )
        self.assertEqual(
            analyze._expected_policy(analyze.A2_ACQUISITION_RUN_ID),
            analyze.ARM_A_POLICY,
        )
        # BC-BODY1-13's "exactly five per arm" survives the substitution.
        self.assertEqual(analyze.TRIALS_PER_ARM, 5)

    def test_consumed_void_id_is_permanently_rejected(self):
        for consumed in (
            "p1-m3-body-001-arm-a-trial-1",
            "p1-m3-body-001-arm-a-trial-2",
        ):
            with self.subTest(consumed=consumed):
                with self.assertRaises(analyze.AnalysisError) as caught:
                    analyze.canonical_trial_id(consumed)
                self.assertIn("run_id_void_consumed", str(caught.exception))
                with self.assertRaises(analyze.AnalysisError):
                    analyze._expected_policy(consumed)

    def test_other_attempt_suffixes_are_rejected(self):
        for bogus in (
            "p1-m3-body-001-arm-a-trial-1-attempt-3",
            "p1-m3-body-001-arm-a-trial-1-attempt-5",
            "p1-m3-body-001-arm-a-trial-2-attempt-4",
            "p1-m3-body-001-arm-b-trial-1-attempt-4",
        ):
            with self.subTest(bogus=bogus):
                with self.assertRaises(analyze.AnalysisError) as caught:
                    analyze.canonical_trial_id(bogus)
                self.assertIn("run_id_not_frozen_trial", str(caught.exception))

    def test_other_eight_ids_are_unchanged(self):
        """Round 42 §B: only slots A1 and A2 acquire under a substitute ID."""
        for index in range(3, 6):
            rid = analyze.frozen_run_id("a", index)
            self.assertEqual(analyze.canonical_trial_id(rid), rid)
        for index in range(1, 6):
            rid = analyze.frozen_run_id("b", index)
            self.assertEqual(analyze.canonical_trial_id(rid), rid)

    def test_expected_sequence_uses_acquisition_ids_at_a1_and_a2(self):
        seq_a = analyze.expected_acquisition_ids("a")
        self.assertEqual(seq_a[0], analyze.A1_ACQUISITION_RUN_ID)
        self.assertEqual(seq_a[1], analyze.A2_ACQUISITION_RUN_ID)
        self.assertEqual(seq_a[2:], [analyze.frozen_run_id("a", i) for i in range(3, 6)])
        self.assertEqual(
            analyze.expected_acquisition_ids("b"),
            [analyze.frozen_run_id("b", i) for i in range(1, 6)],
        )
        self.assertEqual(len(seq_a), analyze.TRIALS_PER_ARM)
        self.assertNotIn(analyze.A1_CANONICAL_TRIAL_ID, seq_a)
        self.assertNotIn(analyze.A2_CANONICAL_TRIAL_ID, seq_a)

    def test_receipt_carries_attempt_binding_only_for_a1_and_a2(self):
        keys = {
            "acquisition_run_id",
            "canonical_trial_id",
            "attempt_number",
            "predecessor_void_manifest_sha256",
            "predecessor_void_frames_sha256",
        }
        with tempfile.TemporaryDirectory() as tmp:
            fixture = TrialFixture(Path(tmp))
            analysis = fixture.analyze()
            receipt = analysis["receipt"]
            self.assertTrue(keys <= set(receipt))
            self.assertEqual(receipt["acquisition_run_id"],
                             analyze.A1_ACQUISITION_RUN_ID)
            self.assertEqual(receipt["canonical_trial_id"],
                             analyze.A1_CANONICAL_TRIAL_ID)
            self.assertEqual(receipt["attempt_number"], 4)
            # The receipt binds whatever the gate verified; under the fixture
            # those are the stand-in hold bytes.
            self.assertEqual(
                receipt["predecessor_void_manifest_sha256"],
                fixture.hold_manifest_sha,
            )
            self.assertEqual(
                receipt["predecessor_void_frames_sha256"],
                fixture.hold_frames_sha,
            )
        with tempfile.TemporaryDirectory() as tmp:
            # A2 carries its own binding block, including the third pinned
            # hash its ten-file void hold has.
            a2 = TrialFixture(Path(tmp), run_id=analyze.A2_ACQUISITION_RUN_ID)
            receipt = a2.analyze()["receipt"]
            self.assertTrue((keys | {"predecessor_void_truth_sha256"})
                            <= set(receipt))
            self.assertEqual(receipt["acquisition_run_id"],
                             analyze.A2_ACQUISITION_RUN_ID)
            self.assertEqual(receipt["canonical_trial_id"],
                             analyze.A2_CANONICAL_TRIAL_ID)
            self.assertEqual(receipt["attempt_number"], 2)
            for field, name in (
                ("predecessor_void_manifest_sha256", "manifest.json"),
                ("predecessor_void_frames_sha256", "frames.jsonl"),
                ("predecessor_void_truth_sha256", analyze.TRUTH_FILE_NAME),
            ):
                self.assertEqual(receipt[field], _sha(a2.a2_hold_dir / name))
        with tempfile.TemporaryDirectory() as tmp:
            # A3 is the same arm/policy as A1 and A2, so any leak here is
            # purely the acquisition-ID branch and not an arm difference.
            other = TrialFixture(Path(tmp), run_id=analyze.frozen_run_id("a", 3))
            receipt = other.analyze()["receipt"]
            self.assertFalse(
                (keys | {"predecessor_void_truth_sha256"}) & set(receipt),
                "attempt-binding fields leaked to a canonical-slot run",
            )

    def test_shipped_predecessor_constants_are_the_round29_values(self):
        """The frozen constants themselves must be attempt 3's real SHAs."""
        self.assertEqual(
            analyze.A1_PREDECESSOR_VOID_MANIFEST_SHA256,
            "e5caa98276a48413f3d78d34228d8c41d8ad0b9e8b438c070d4925c4f14e8a65",
        )
        self.assertEqual(
            analyze.A1_PREDECESSOR_VOID_FRAMES_SHA256,
            "8f9f355186cf06d83dd30956552b9687cd4992454090f89ecc307f2b986016b5",
        )
        self.assertEqual(
            analyze.A1_PREDECESSOR_HOLD_DIR_NAME,
            "p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold",
        )

    def test_shipped_a2_predecessor_constants_are_the_round42_values(self):
        """Round 42 §B's frozen table, verbatim: the ten-file hold name, the
        exact file set and the three pinned SHA-256 values."""
        self.assertEqual(
            analyze.A2_PREDECESSOR_HOLD_DIR_NAME,
            "p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold",
        )
        self.assertEqual(
            sorted(analyze.A2_PREDECESSOR_HOLD_FILES),
            sorted(
                (
                    "frames.jsonl",
                    "manifest.json",
                    "m3_body_truth.jsonl",
                    "metrics.final.json",
                    "summary.json",
                    "scenario.json",
                    "margin.json",
                    "body_config.json",
                    "reanchor_config.json",
                    "tracker_model_spec.json",
                )
            ),
        )
        self.assertEqual(
            analyze.A2_PREDECESSOR_VOID_FRAMES_SHA256,
            "a7939b7ce0a54a52487859b3ed1e12d3f0b6526759ab5e77925c49980309fc54",
        )
        self.assertEqual(
            analyze.A2_PREDECESSOR_VOID_MANIFEST_SHA256,
            "d9774905aab324acf05c7616d0bf9e8a0ccf8f10c3855dd5c8c4ff1f9ea4a50c",
        )
        self.assertEqual(
            analyze.A2_PREDECESSOR_VOID_TRUTH_SHA256,
            "6f3e5238ef0057253f1228ec4aa9fdd53c2557dd00bc01d2df1782e90635f095",
        )



class PredecessorHoldGateTests(unittest.TestCase):
    """Round 30 §C.3: the A1 acquisition must bind to the real attempt-3 void
    hold before anything is collected or written."""

    def _fixture(self, tmp):
        return TrialFixture(Path(tmp))

    def _assert_no_outputs(self, fixture):
        """A failed gate must not leave collected inputs or an analysis."""
        for name in (*analyze.RUN_BOUND_INPUTS, analyze.ANALYSIS_FILE_NAME):
            self.assertFalse(
                (fixture.run_dir / name).exists(),
                f"{name} was created despite a failed predecessor gate",
            )

    def test_missing_hold_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(tmp)
            for child in fixture.hold_dir.iterdir():
                child.unlink()
            fixture.hold_dir.rmdir()
            with self.assertRaises(analyze.AnalysisError) as caught:
                fixture.analyze()
            self.assertIn("a1_predecessor_hold_missing", str(caught.exception))
            self._assert_no_outputs(fixture)

    def test_extra_file_in_hold_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(tmp)
            (fixture.hold_dir / "summary.json").write_text("{}")
            with self.assertRaises(analyze.AnalysisError) as caught:
                fixture.analyze()
            self.assertIn(
                "a1_predecessor_hold_file_set_mismatch", str(caught.exception)
            )
            self._assert_no_outputs(fixture)

    def test_missing_file_in_hold_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(tmp)
            (fixture.hold_dir / "manifest.json").unlink()
            with self.assertRaises(analyze.AnalysisError) as caught:
                fixture.analyze()
            self.assertIn(
                "a1_predecessor_hold_file_set_mismatch", str(caught.exception)
            )
            self._assert_no_outputs(fixture)

    def test_frames_byte_mutation_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(tmp)
            (fixture.hold_dir / "frames.jsonl").write_text('{"void": "TAMPERED"}\n')
            with self.assertRaises(analyze.AnalysisError) as caught:
                fixture.analyze()
            self.assertIn(
                "a1_predecessor_void_frames_sha256_mismatch", str(caught.exception)
            )
            self._assert_no_outputs(fixture)

    def test_manifest_byte_mutation_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(tmp)
            (fixture.hold_dir / "manifest.json").write_text('{"void": "TAMPERED"}\n')
            with self.assertRaises(analyze.AnalysisError) as caught:
                fixture.analyze()
            self.assertIn(
                "a1_predecessor_void_manifest_sha256_mismatch", str(caught.exception)
            )
            self._assert_no_outputs(fixture)

    def test_gate_does_not_apply_to_the_other_eight(self):
        """A3 acquires under its canonical slot: no predecessor requirement
        for either hold."""
        with tempfile.TemporaryDirectory() as tmp:
            other = TrialFixture(Path(tmp), run_id=analyze.frozen_run_id("a", 3))
            for hold in (other.hold_dir, other.a2_hold_dir):
                for child in hold.iterdir():
                    child.unlink()
                hold.rmdir()
            self.assertEqual(other.analyze()["receipt"]["run_id"],
                             analyze.frozen_run_id("a", 3))


class A2PredecessorHoldGateTests(unittest.TestCase):
    """Round 42 §B (BC-BODY1-27): the A2 acquisition must bind to the real
    attempt-1 void hold - ten file names, three pinned hashes - before
    anything is collected or written."""

    def _fixture(self, tmp):
        return TrialFixture(Path(tmp), run_id=analyze.A2_ACQUISITION_RUN_ID)

    def _assert_fails_closed(self, fixture, marker):
        with self.assertRaises(analyze.AnalysisError) as caught:
            fixture.analyze()
        self.assertIn(marker, str(caught.exception))
        for name in (*analyze.RUN_BOUND_INPUTS, analyze.ANALYSIS_FILE_NAME):
            self.assertFalse(
                (fixture.run_dir / name).exists(),
                f"{name} was created despite a failed predecessor gate",
            )

    def test_missing_hold_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(tmp)
            for child in fixture.a2_hold_dir.iterdir():
                child.unlink()
            fixture.a2_hold_dir.rmdir()
            self._assert_fails_closed(fixture, "a2_predecessor_hold_missing")

    def test_file_set_deviations_fail_closed(self):
        for case in ("extra", "missing"):
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory() as tmp:
                    fixture = self._fixture(tmp)
                    if case == "extra":
                        (fixture.a2_hold_dir / "m3_body_analysis.json").write_text("{}")
                    else:
                        (fixture.a2_hold_dir / "summary.json").unlink()
                    self._assert_fails_closed(
                        fixture, "a2_predecessor_hold_file_set_mismatch"
                    )

    def test_pinned_byte_mutations_fail_closed(self):
        for name, marker in (
            ("frames.jsonl", "a2_predecessor_void_frames_sha256_mismatch"),
            ("manifest.json", "a2_predecessor_void_manifest_sha256_mismatch"),
            (analyze.TRUTH_FILE_NAME, "a2_predecessor_void_truth_sha256_mismatch"),
        ):
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmp:
                    fixture = self._fixture(tmp)
                    (fixture.a2_hold_dir / name).write_text(
                        '{"void": "TAMPERED"}\n'
                    )
                    self._assert_fails_closed(fixture, marker)

    def test_a1_hold_is_not_required_for_a2(self):
        """The two gates are independent: A2 never touches A1's hold."""
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(tmp)
            for child in fixture.hold_dir.iterdir():
                child.unlink()
            fixture.hold_dir.rmdir()
            self.assertEqual(
                fixture.analyze()["receipt"]["run_id"],
                analyze.A2_ACQUISITION_RUN_ID,
            )


class CompletionHandshakeTests(unittest.TestCase):
    """Round 30 §C.4/§C.5: every AND condition of the handshake, plus proof
    that the PASS path writes nothing."""

    RUN_ID = analyze.A1_ACQUISITION_RUN_ID

    def _run(self, tmp, *, summary=None, metrics=True, manifest_id=None,
             summary_present=True, duration=130.0, make_summary=True):
        runtime = Path(tmp) / "runtime"
        run_dir = runtime / "runs" / self.RUN_ID
        run_dir.mkdir(parents=True)
        (run_dir / "manifest.json").write_text(
            json.dumps({"run_id": manifest_id or self.RUN_ID})
        )
        if make_summary:
            payload = {"actual_duration_s": duration}
            if summary_present is not None:
                payload["metrics_snapshot_present"] = summary_present
            (run_dir / "summary.json").write_text(json.dumps(payload))
        if metrics:
            (run_dir / "metrics.final.json").write_text("{}")
        final = {
            "run_id": self.RUN_ID,
            "summary": summary if summary is not None
            else str(run_dir / "summary.json"),
        }
        return runtime, run_dir, json.dumps(final)

    def test_pass_path_returns_the_word_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, run_dir, final = self._run(tmp)
            before = sorted(p.name for p in run_dir.iterdir())
            before_hashes = {p.name: _sha(p) for p in run_dir.iterdir()}
            word = analyze.validate_completion(runtime, self.RUN_ID, 0, final)
            self.assertEqual(word, "TRACKER_AUTO_COMPLETE_CONFIRMED")
            self.assertEqual(sorted(p.name for p in run_dir.iterdir()), before)
            self.assertEqual(
                {p.name: _sha(p) for p in run_dir.iterdir()}, before_hashes
            )
            self.assertFalse((run_dir / analyze.ANALYSIS_FILE_NAME).exists())

    def test_nonzero_exit_code_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _, final = self._run(tmp)
            with self.assertRaises(analyze.AnalysisError) as caught:
                analyze.validate_completion(runtime, self.RUN_ID, 1, final)
            self.assertIn("completion_tracker_exit_code_nonzero", str(caught.exception))

    def test_malformed_and_non_object_json_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _, _ = self._run(tmp)
            with self.assertRaises(analyze.AnalysisError) as caught:
                analyze.validate_completion(runtime, self.RUN_ID, 0, "not json{")
            self.assertIn("completion_final_json_unparseable", str(caught.exception))
            with self.assertRaises(analyze.AnalysisError) as caught:
                analyze.validate_completion(runtime, self.RUN_ID, 0, "[1, 2]")
            self.assertIn("completion_final_json_not_object", str(caught.exception))

    def test_wrong_run_id_in_final_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, run_dir, _ = self._run(tmp)
            final = json.dumps({
                "run_id": "p1-m3-body-001-arm-b-trial-1",
                "summary": str(run_dir / "summary.json"),
            })
            with self.assertRaises(analyze.AnalysisError) as caught:
                analyze.validate_completion(runtime, self.RUN_ID, 0, final)
            self.assertIn("completion_final_json_run_id_mismatch", str(caught.exception))

    def test_wrong_or_escaping_summary_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, run_dir, _ = self._run(tmp)
            for bogus in (str(run_dir / "elsewhere.json"),
                          str(Path(tmp) / "outside" / "summary.json")):
                final = json.dumps({"run_id": self.RUN_ID, "summary": bogus})
                with self.assertRaises(analyze.AnalysisError) as caught:
                    analyze.validate_completion(runtime, self.RUN_ID, 0, final)
                self.assertIn("completion_summary_path_mismatch", str(caught.exception))

    def test_manifest_run_id_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _, final = self._run(tmp, manifest_id="p1-m3-body-001-arm-a-trial-2")
            with self.assertRaises(analyze.AnalysisError) as caught:
                analyze.validate_completion(runtime, self.RUN_ID, 0, final)
            self.assertIn("completion_manifest_run_id_mismatch", str(caught.exception))

    def test_each_terminal_artifact_missing_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, run_dir, final = self._run(tmp, make_summary=False)
            with self.assertRaises(analyze.AnalysisError) as caught:
                analyze.validate_completion(runtime, self.RUN_ID, 0, final)
            self.assertIn("completion_summary_file_missing", str(caught.exception))
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _, final = self._run(tmp, metrics=False)
            with self.assertRaises(analyze.AnalysisError) as caught:
                analyze.validate_completion(runtime, self.RUN_ID, 0, final)
            self.assertIn("completion_metrics_final_missing", str(caught.exception))

    def test_metrics_snapshot_not_true_fails_closed(self):
        for value in (False, None, "true"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                runtime, _, final = self._run(tmp, summary_present=value)
                with self.assertRaises(analyze.AnalysisError) as caught:
                    analyze.validate_completion(runtime, self.RUN_ID, 0, final)
                self.assertIn("completion_metrics_snapshot_absent", str(caught.exception))

    def test_duration_below_watchdog_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _, final = self._run(tmp, duration=125.3803)
            with self.assertRaises(analyze.AnalysisError) as caught:
                analyze.validate_completion(runtime, self.RUN_ID, 0, final)
            self.assertIn("completion_duration_below_watchdog", str(caught.exception))
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _, final = self._run(tmp, duration="130")
            with self.assertRaises(analyze.AnalysisError) as caught:
                analyze.validate_completion(runtime, self.RUN_ID, 0, final)
            self.assertIn("completion_duration_not_numeric", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
