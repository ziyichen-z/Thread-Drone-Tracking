#!/usr/bin/env python3
"""P1-ENG-ACQ-001 AC-5：位姿单应 H = K·R_Δ·K⁻¹ 的合成纯旋转检验与施加方式择定（纯 Python）。"""

from __future__ import annotations

import math
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import pose_gmc  # noqa: E402
from controller.reanchor import _rotate_quaternion  # noqa: E402


def quaternion(axis, angle_deg):
    norm = math.sqrt(sum(a * a for a in axis))
    half = math.radians(angle_deg) / 2.0
    s = math.sin(half) / norm
    return [axis[0] * s, axis[1] * s, axis[2] * s, math.cos(half)]


def compose(a, b):
    """a ∘ b（先 b 后 a），四元数 xyzw。"""
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return [
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    ]


# 数据根 a7 首帧的真实取向（相机朝下，right=+x、up=+z）与内参。
NADIR = [0.7071068286895752, 0.0, 0.0, 0.7071068286895752]
INTRINSICS = {"fx": 415.69219970703127, "fy": 415.69219970703127, "cx": 320.0, "cy": 240.0}


def metadata(q, position=(182.0, 25.2, 25.0)):
    return {"camera_rotation_xyzw": list(q), "camera_position_world_m": list(position), "intrinsics_px": dict(INTRINSICS)}


def world_points(meta, count=40):
    """在 meta 相机前方 20–80 m 撒点（反投影像素网格 → 世界）。"""
    r = pose_gmc.rotation_matrix(meta)
    position = meta["camera_position_world_m"]
    points = []
    for i in range(count):
        u = 20 + (i * 97) % 600
        v = 20 + (i * 53) % 440
        depth = 20 + (i * 7) % 60
        x = (u - 320.0) / INTRINSICS["fx"] * depth
        y = -(v - 240.0) / INTRINSICS["fy"] * depth
        camera = (x, y, depth)
        points.append([position[row] + sum(r[row][col] * camera[col] for col in range(3)) for row in range(3)])
    return points


class PoseHomography(unittest.TestCase):
    def test_rotation_matrix_matches_camera_basis_convention(self):
        q = compose(quaternion((0.3, 1.0, 0.2), 37.0), NADIR)
        r = pose_gmc.rotation_matrix(metadata(q))
        for column, axis in enumerate(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))):
            expected = _rotate_quaternion(axis, q)
            for row in range(3):
                self.assertAlmostEqual(r[row][column], expected[row], places=6)

    def test_synthetic_pure_rotation_maps_within_half_pixel(self):
        """AC-5：t−1 帧像素经 H 映射与 t 帧投影之差 ≤ 0.5 px（多种姿态差，含 a7 级 21–27° 扫视）。"""
        before = metadata(NADIR)
        cases = [((0.0, 0.0, 1.0), 1.0), ((1.0, 0.0, 0.0), 5.0), ((0.0, 1.0, 0.0), 12.0), ((0.4, 1.0, 0.3), 21.7), ((1.0, 0.2, 0.0), 26.7)]
        for axis, angle in cases:
            with self.subTest(axis=axis, angle=angle):
                after = metadata(compose(quaternion(axis, angle), NADIR))
                h = pose_gmc.pose_homography(before, after)
                checked = 0
                for point in world_points(before):
                    p1 = pose_gmc.project_world_point(point, before)
                    p2 = pose_gmc.project_world_point(point, after)
                    if p1 is None or p2 is None:
                        continue
                    mapped = pose_gmc.map_point(h, *p1)
                    self.assertIsNotNone(mapped)
                    self.assertLessEqual(math.dist(mapped, p2), 0.5)
                    checked += 1
                self.assertGreater(checked, 10)
                self.assertAlmostEqual(pose_gmc.rotation_angle_deg(before, after), angle, places=4)

    def test_identity_for_equal_pose(self):
        meta = metadata(NADIR)
        h = pose_gmc.pose_homography(meta, meta)
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(h[i][j], 1.0 if i == j else 0.0, places=9)

    def test_four_corner_aabb_selected_over_degenerate_affine(self):
        """择定依据：大角度下丢弃透视行的 2×3 误差 > 0.5 px，四角 3×3 ≤ 0.5 px。"""
        before = metadata(NADIR)
        after = metadata(compose(quaternion((1.0, 0.0, 0.3), 21.7), NADIR))  # 俯仰为主：透视项非零
        h = pose_gmc.pose_homography(before, after)
        affine = pose_gmc.affine_part(h)
        worst_full = worst_affine = 0.0
        for point in world_points(before):
            p1 = pose_gmc.project_world_point(point, before)
            p2 = pose_gmc.project_world_point(point, after)
            if p1 is None or p2 is None:
                continue
            worst_full = max(worst_full, math.dist(pose_gmc.map_point(h, *p1), p2))
            worst_affine = max(worst_affine, math.dist(pose_gmc.map_point_affine(affine, *p1), p2))
        self.assertLessEqual(worst_full, 0.5)
        self.assertGreater(worst_affine, 0.5)

    def test_warp_box_is_aabb_of_mapped_corners(self):
        before = metadata(NADIR)
        after = metadata(compose(quaternion((1.0, 0.0, 0.0), 8.0), NADIR))
        h = pose_gmc.pose_homography(before, after)
        box = (100.0, 120.0, 180.0, 200.0)
        warped = pose_gmc.warp_box_xyxy(h, box)
        corners = [pose_gmc.map_point(h, u, v) for u, v in ((100, 120), (180, 120), (100, 200), (180, 200))]
        self.assertEqual(warped, (min(c[0] for c in corners), min(c[1] for c in corners), max(c[0] for c in corners), max(c[1] for c in corners)))

    def test_jacobian_matches_finite_difference(self):
        before = metadata(NADIR)
        after = metadata(compose(quaternion((0.2, 1.0, 0.0), 15.0), NADIR))
        h = pose_gmc.pose_homography(before, after)
        j = pose_gmc.jacobian(h, 300.0, 200.0)
        eps = 1e-3
        base = pose_gmc.map_point(h, 300.0, 200.0)
        du = pose_gmc.map_point(h, 300.0 + eps, 200.0)
        dv = pose_gmc.map_point(h, 300.0, 200.0 + eps)
        self.assertAlmostEqual(j[0][0], (du[0] - base[0]) / eps, places=4)
        self.assertAlmostEqual(j[1][0], (du[1] - base[1]) / eps, places=4)
        self.assertAlmostEqual(j[0][1], (dv[0] - base[0]) / eps, places=4)
        self.assertAlmostEqual(j[1][1], (dv[1] - base[1]) / eps, places=4)

    def test_gmc_sources_closed_set(self):
        # P1-ENG-CAPTURE-001 §3.1：闭集扩为 {pose, pose-center, pose-aabb, optflow, none}（pose ≡ pose-aabb）；
        # 既有三值位次不变，新值只追加在末尾。
        self.assertEqual(pose_gmc.GMC_SOURCES, ("pose", "optflow", "none", "pose-center", "pose-aabb"))
        self.assertEqual(pose_gmc.POSE_SOURCES, ("pose", "pose-center", "pose-aabb"))
        # IR-3：旧完整前缀与接受基线运行时逐位比较（不手抄、不只检切片），其后恰为两个新值。
        from tools.eng_capture.common import accepted_base_literal  # noqa: PLC0415

        base = accepted_base_literal("controller/pose_gmc.py", "GMC_SOURCES")
        if base is None:
            self.skipTest("git history unavailable")
        self.assertEqual(pose_gmc.GMC_SOURCES, tuple(base) + ("pose-center", "pose-aabb"))

    def test_rejects_unnormalized_quaternion(self):
        with self.assertRaises(ValueError):
            pose_gmc.rotation_matrix(metadata([0.0, 0.0, 0.0, 2.0]))


if __name__ == "__main__":
    unittest.main()
