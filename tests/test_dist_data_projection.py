"""S3 投影合同：相机、AABB、近裁剪、框口径、遮挡与站位簇（§2.4，AR1-5）。"""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import contract, project_boxes  # noqa: E402


def make_sidecar(**overrides) -> dict:
    """640×480 / vfov 60° 的合规 sidecar（与归档 v3 同字段）。"""
    document = {
        "camera_position_world_m": [0.0, 0.0, 0.0],
        "camera_right_world": [1.0, 0.0, 0.0],
        "camera_up_world": [0.0, 1.0, 0.0],
        "camera_forward_world": [0.0, 0.0, 1.0],
        "vertical_fov_deg": 60.0,
        "width": 640,
        "height": 480,
        "intrinsics_px": {"fx": 415.6921938165305, "fy": 415.6921938165305, "cx": 320.0, "cy": 240.0},
    }
    document.update(overrides)
    return document


def box(min_x, max_x, min_y, max_y, min_z, max_z, name="obj") -> dict:
    return {
        "scene_object_name": name,
        "min_x_m": min_x,
        "max_x_m": max_x,
        "min_y_m": min_y,
        "max_y_m": max_y,
        "min_z_m": min_z,
        "max_z_m": max_z,
    }


class CameraTest(unittest.TestCase):
    def test_intrinsics_consistency_is_enforced(self) -> None:
        project_boxes.Camera.from_sidecar(make_sidecar())
        bad = make_sidecar()
        bad["intrinsics_px"] = {"fx": 500.0, "fy": 500.0, "cx": 320.0, "cy": 240.0}
        with self.assertRaises(project_boxes.ProjectionError):
            project_boxes.Camera.from_sidecar(bad)

    def test_tolerance_is_half_a_pixel(self) -> None:
        sidecar = make_sidecar()
        exact = sidecar["intrinsics_px"]["fx"]
        sidecar["intrinsics_px"] = {
            "fx": exact + 0.49,
            "fy": exact + 0.49,
            "cx": 320.0,
            "cy": 240.0,
        }
        project_boxes.Camera.from_sidecar(sidecar)
        sidecar["intrinsics_px"] = {
            "fx": exact + 0.51,
            "fy": exact + 0.51,
            "cx": 320.0,
            "cy": 240.0,
        }
        with self.assertRaises(project_boxes.ProjectionError):
            project_boxes.Camera.from_sidecar(sidecar)

    def test_missing_pose_field_is_fail_closed(self) -> None:
        sidecar = make_sidecar()
        del sidecar["camera_up_world"]
        with self.assertRaises(project_boxes.ProjectionError):
            project_boxes.Camera.from_sidecar(sidecar)

    def test_pixel_convention_is_top_left_y_down(self) -> None:
        camera = project_boxes.Camera.from_sidecar(make_sidecar())
        above = camera.project_camera_point((0.0, 1.0, 10.0))
        below = camera.project_camera_point((0.0, -1.0, 10.0))
        self.assertLess(above[1], camera.cy)
        self.assertGreater(below[1], camera.cy)

    def test_real_archived_sidecar_projects(self) -> None:
        """归档 v3 sidecar 直接可构造相机（不从四元数重算基向量）。"""
        candidates = sorted(
            (PROJECT_ROOT / "runtime" / "frames.qual3-leftover-hold").glob("frame_*.json")
        )
        if not candidates:
            self.skipTest("归档 sidecar 不在本工作副本中")
        document = json.loads(candidates[0].read_text(encoding="utf-8"))
        camera = project_boxes.Camera.from_sidecar(document)
        self.assertEqual((camera.width, camera.height), (640, 480))


class ProjectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.camera = project_boxes.Camera.from_sidecar(make_sidecar())

    def test_all_corners_behind_near_plane_is_not_in_view(self) -> None:
        self.assertIsNone(
            project_boxes.project_aabb(self.camera, box(-1, 1, -1, 1, -10, -5))
        )

    def test_straddling_near_plane_is_clipped_not_dropped(self) -> None:
        rect = project_boxes.project_aabb(self.camera, box(-1, 1, -1, 1, -1.0, 5.0))
        self.assertIsNotNone(rect)
        self.assertGreater(project_boxes.area(rect), 0.0)

    def test_amodal_is_tight_bound_of_projected_corners(self) -> None:
        rect = project_boxes.project_aabb(self.camera, box(-1, 1, -1, 1, 10, 12))
        assert rect is not None
        # 近面（z=10）的角点比远面张得大，紧包围盒由近面决定。
        expected_half = self.camera.fx * 1.0 / 10.0
        self.assertAlmostEqual(rect[0], self.camera.cx - expected_half, places=6)
        self.assertAlmostEqual(rect[2], self.camera.cx + expected_half, places=6)

    def test_normalized_xywh_is_clipped_to_unit_square(self) -> None:
        rect = (-100.0, -50.0, 900.0, 700.0)
        x, y, w, h = project_boxes.normalized_xywh(rect, self.camera)
        self.assertEqual((x, y), (0.0, 0.0))
        self.assertEqual((w, h), (1.0, 1.0))

    def test_union_area_is_exact(self) -> None:
        self.assertEqual(project_boxes.union_area([(0, 0, 10, 10), (5, 0, 15, 10)]), 150.0)
        self.assertEqual(project_boxes.union_area([(0, 0, 10, 10), (0, 0, 10, 10)]), 100.0)
        self.assertEqual(project_boxes.union_area([]), 0.0)

    def test_iou_of_identical_boxes_is_one(self) -> None:
        self.assertEqual(project_boxes.iou((0, 0, 4, 4), (0, 0, 4, 4)), 1.0)
        self.assertEqual(project_boxes.iou((0, 0, 4, 4), (10, 10, 14, 14)), 0.0)


class StatusTest(unittest.TestCase):
    def setUp(self) -> None:
        self.camera = project_boxes.Camera.from_sidecar(make_sidecar())

    def _status(self, instances, extra=()) -> dict[str, str]:
        projected = project_boxes.project_instances(
            self.camera, instances, extra_blockers=extra
        )
        return {item.object_id: item.status for item in projected}

    def test_ok_for_a_clean_object(self) -> None:
        statuses = self._status([box(-1, 1, -1, 1, 10, 12, "near")])
        self.assertEqual(statuses["near"], "OK")

    def test_too_small_below_twelve_pixels(self) -> None:
        statuses = self._status([box(-0.05, 0.05, -0.05, 0.05, 100, 101, "far")])
        self.assertEqual(statuses["far"], "TOO_SMALL")

    def test_not_in_view_behind_camera(self) -> None:
        statuses = self._status([box(-1, 1, -1, 1, -20, -10, "behind")])
        self.assertEqual(statuses["behind"], "NOT_IN_VIEW")

    def test_truncated_when_visible_share_below_quarter(self) -> None:
        # 大部分张出视口右侧：visible/amodal < 0.25。
        statuses = self._status([box(4.0, 40.0, -2.0, 2.0, 6.0, 6.5, "edge")])
        self.assertEqual(statuses["edge"], "TRUNCATED")

    def test_occlusion_uses_theta_and_visible_denominator(self) -> None:
        statuses = self._status(
            [
                box(-1, 1, -1, 1, 20, 21, "far_object"),
                box(-2, 2, -2, 2, 5, 6, "near_blocker"),
            ]
        )
        self.assertEqual(statuses["near_blocker"], "OK")
        self.assertEqual(statuses["far_object"], "EXCLUDED_OCCLUDED")

    def test_partial_overlap_below_theta_stays_ok(self) -> None:
        statuses = self._status(
            [
                box(-1.0, 1.0, -1.0, 1.0, 20, 21, "far_object"),
                box(0.9, 3.0, -2.0, 2.0, 5, 6, "side_blocker"),
            ]
        )
        self.assertEqual(statuses["far_object"], "OK")

    def test_extra_blocker_occludes_but_is_never_listed(self) -> None:
        """动态目标真值框只作图像面阻断体，永不可指称。"""
        statuses = self._status(
            [box(-1, 1, -1, 1, 20, 21, "far_object")],
            extra=[("dynamic-target:UNKNOWN", (0.0, 0.0, 640.0, 480.0), float("-inf"))],
        )
        self.assertNotIn("dynamic-target:UNKNOWN", statuses)
        self.assertEqual(statuses["far_object"], "EXCLUDED_OCCLUDED")

    def test_phantom_status_is_reported_and_never_referable(self) -> None:
        instance = box(-1, 1, -1, 1, 10, 12, "phantom:Vehicle_Taxi@1,2")
        instance["phantom"] = True
        projected = project_boxes.project_instances(self.camera, [instance])
        self.assertEqual(projected[0].status, "PHANTOM")
        self.assertFalse(projected[0].referable)
        self.assertTrue(projected[0].blocks)

    def test_painter_order_tie_breaks_on_name(self) -> None:
        first = box(-1, 1, -1, 1, 10, 12, "aaa")
        second = box(-1, 1, -1, 1, 10, 12, "bbb")
        projected = project_boxes.project_instances(self.camera, [second, first])
        statuses = {item.object_id: item.status for item in projected}
        self.assertEqual(statuses["aaa"], "OK")
        self.assertEqual(statuses["bbb"], "EXCLUDED_OCCLUDED")


class StationBinTest(unittest.TestCase):
    def test_position_bins_floor_at_two_metres(self) -> None:
        camera = project_boxes.Camera.from_sidecar(
            make_sidecar(camera_position_world_m=[132.0, 25.2, 117.0])
        )
        station = project_boxes.station_bin(camera)
        self.assertEqual(station["x_bin"], 66)
        self.assertEqual(station["z_bin"], 58)

    def test_elevation_band_from_forward_y(self) -> None:
        down = math.sin(math.radians(45.0))
        forward = [0.0, -down, math.cos(math.radians(45.0))]
        camera = project_boxes.Camera.from_sidecar(
            make_sidecar(camera_forward_world=forward)
        )
        station = project_boxes.station_bin(camera)
        self.assertEqual(station["elevation_band"], 1)
        self.assertAlmostEqual(station["elevation_deg"], 45.0, places=6)

    def test_nadir_is_top_band_inclusive(self) -> None:
        camera = project_boxes.Camera.from_sidecar(
            make_sidecar(camera_forward_world=[0.0, -1.0, 0.0])
        )
        station = project_boxes.station_bin(camera)
        self.assertEqual(station["elevation_band"], 2)
        self.assertIsNotNone(station["key"])

    def test_upward_camera_has_no_band(self) -> None:
        camera = project_boxes.Camera.from_sidecar(
            make_sidecar(camera_forward_world=[0.0, 1.0, 0.0])
        )
        station = project_boxes.station_bin(camera)
        self.assertIsNone(station["elevation_band"])
        self.assertIsNone(station["key"])

    def test_azimuth_bins_are_fifteen_degrees(self) -> None:
        camera = project_boxes.Camera.from_sidecar(
            make_sidecar(camera_forward_world=[1.0, 0.0, 0.0])
        )
        station = project_boxes.station_bin(camera)
        self.assertEqual(station["azimuth_bin"], int(90.0 // contract.STATION_AZIMUTH_BIN_DEG))


class RouteSweepTest(unittest.TestCase):
    def test_segment_sweep_covers_the_polyline(self) -> None:
        camera = project_boxes.Camera.from_sidecar(make_sidecar())
        route = [{"x": -5.0, "y": 0.0, "z": 20.0}, {"x": 5.0, "y": 0.0, "z": 20.0}]
        rects = project_boxes.route_sweep_rects(camera, route, (2.0, 1.0, 2.0))
        self.assertTrue(rects)
        self.assertGreater(project_boxes.union_area(rects), contract.TARGET_SWEEP_MIN_AREA_PX2)

    def test_route_behind_camera_projects_nothing(self) -> None:
        camera = project_boxes.Camera.from_sidecar(make_sidecar())
        route = [{"x": -5.0, "y": 0.0, "z": -20.0}, {"x": 5.0, "y": 0.0, "z": -20.0}]
        rects = project_boxes.route_sweep_rects(camera, route, (2.0, 1.0, 2.0))
        self.assertEqual(project_boxes.union_area(rects), 0.0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
