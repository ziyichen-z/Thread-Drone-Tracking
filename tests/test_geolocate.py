import math
import unittest

from controller.geolocate import GeometryRejected, box_ground_intersection


def metadata(
    *,
    position=(0.0, 10.0, 0.0),
    forward=(0.0, -1.0, 0.0),
    right=(1.0, 0.0, 0.0),
    up=(0.0, 0.0, 1.0),
):
    return {
        "width": 200,
        "height": 100,
        "intrinsics_px": {"fx": 100.0, "fy": 100.0, "cx": 100.0, "cy": 50.0},
        "camera_position_world_m": list(position),
        "camera_forward_world": list(forward),
        "camera_right_world": list(right),
        "camera_up_world": list(up),
    }


class GeolocationTests(unittest.TestCase):
    def test_center_bottom_ray_hits_nadir_origin(self):
        result = box_ground_intersection((0.4, 0.3, 0.2, 0.2), metadata(), 0.0)
        self.assertAlmostEqual(result.point_world_m[0], 0.0)
        self.assertAlmostEqual(result.point_world_m[1], 0.0)
        self.assertAlmostEqual(result.point_world_m[2], 0.0)

    def test_top_left_image_y_sign_points_below_center_toward_negative_up(self):
        result = box_ground_intersection((0.4, 0.5, 0.2, 0.2), metadata(), 0.0)
        self.assertLess(result.point_world_m[2], 0.0)

    def test_rotated_camera_basis_is_used(self):
        root_half = math.sqrt(0.5)
        result = box_ground_intersection(
            (0.4, 0.3, 0.2, 0.2),
            metadata(
                forward=(0.0, -root_half, root_half),
                up=(0.0, root_half, root_half),
            ),
            0.0,
        )
        self.assertAlmostEqual(result.point_world_m[1], 0.0)
        self.assertAlmostEqual(result.point_world_m[2], 10.0)

    def test_parallel_upward_nonpositive_and_too_far_are_rejected(self):
        with self.assertRaisesRegex(GeometryRejected, "parallel_or_upward"):
            box_ground_intersection(
                (0.4, 0.3, 0.2, 0.2),
                metadata(forward=(0.0, 0.0, 1.0)),
                0.0,
            )
        with self.assertRaisesRegex(GeometryRejected, "parallel_or_upward"):
            box_ground_intersection(
                (0.4, 0.3, 0.2, 0.2),
                metadata(forward=(0.0, 1.0, 0.0)),
                0.0,
            )
        with self.assertRaisesRegex(GeometryRejected, "non_positive"):
            box_ground_intersection(
                (0.4, 0.3, 0.2, 0.2),
                metadata(),
                20.0,
            )
        with self.assertRaisesRegex(GeometryRejected, "beyond"):
            box_ground_intersection(
                (0.4, 0.3, 0.2, 0.2),
                metadata(),
                0.0,
                maximum_distance_m=5.0,
            )


if __name__ == "__main__":
    unittest.main()
