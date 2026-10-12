#!/usr/bin/env python3
"""P1-ENG-CAPTURE-001 AC-2（K1）：`pose-center` 只移中心——合成纯旋转单应下中心 = H(中心)、宽高与宽高速度不变、
速度与位置/速度协方差块按 J 变换；H 不可映射时不改；`pose-aabb`/`pose` 与修改前 `apply_pose_warp` 逐元素一致。"""

from __future__ import annotations

import ast
import importlib.util
import math
from pathlib import Path
import subprocess
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

HAVE_NUMPY = importlib.util.find_spec("numpy") is not None
HAVE_LIBS = HAVE_NUMPY and importlib.util.find_spec("ultralytics") is not None and importlib.util.find_spec("lap") is not None

from controller import det_assoc_tracker as dat  # noqa: E402
from controller import pose_gmc  # noqa: E402
from tools.eng_capture.common import accepted_base_commit  # noqa: E402

K = ((415.69, 0.0, 320.0), (0.0, -415.69, 240.0), (0.0, 0.0, 1.0))


def roll_homography(deg):
    """绕光轴纯旋转 25°/帧：H = K Rz K⁻¹（像素系绕主点旋转）。"""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return ((c, -s, 320.0 - c * 320.0 + s * 240.0), (s, c, 240.0 - s * 320.0 - c * 240.0), (0.0, 0.0, 1.0))


def tilt_homography():
    """含透视行的单应（相机俯仰），检验雅可比与透视下的中心映射。"""
    meta1 = {"camera_rotation_xyzw": [0.7071068, 0.0, 0.0, 0.7071068], "intrinsics_px": {"fx": 415.69, "fy": 415.69, "cx": 320.0, "cy": 240.0}}
    raw = [0.70105738, 0.0, 0.09229596, 0.70105738]
    norm = math.sqrt(sum(v * v for v in raw))
    meta2 = dict(meta1, camera_rotation_xyzw=[v / norm for v in raw])
    return pose_gmc.pose_homography(meta1, meta2)


class _XywhTrack:
    """BoT-SORT `BOTrack` 形态替身（xywh 状态，有 `tlwh_to_xywh`）。"""

    def __init__(self, mean, covariance):
        import numpy as np  # noqa: PLC0415

        self.mean = np.asarray(mean, dtype=float)
        self.covariance = np.asarray(covariance, dtype=float)
        self.track_id = 7

    def tlwh_to_xywh(self, tlwh):  # pragma: no cover - 只作类型标记
        return tlwh


def make_track(seed=0.0):
    import numpy as np  # noqa: PLC0415

    mean = [300.0, 200.0, 60.0, 40.0, 3.0, -1.5, 0.7, -0.2]
    a = np.arange(64, dtype=float).reshape(8, 8) / 100.0 + seed
    return _XywhTrack(mean, a @ a.T + np.eye(8))


@unittest.skipUnless(HAVE_NUMPY, "需要 numpy")
class PoseCenterTests(unittest.TestCase):
    def check(self, homography):
        import numpy as np  # noqa: PLC0415

        track = make_track()
        before_mean, before_cov = track.mean.copy(), track.covariance.copy()
        self.assertEqual(dat.apply_pose_center([track], homography), 1)
        expected = pose_gmc.map_point(homography, before_mean[0], before_mean[1])
        self.assertLessEqual(abs(track.mean[0] - expected[0]), 1e-6)
        self.assertLessEqual(abs(track.mean[1] - expected[1]), 1e-6)
        for index in (2, 3, 6, 7):  # w, h, vw, vh 不变
            self.assertEqual(track.mean[index], before_mean[index])
        j = np.asarray(pose_gmc.jacobian(homography, before_mean[0], before_mean[1]))
        np.testing.assert_allclose(track.mean[4:6], j @ before_mean[4:6], atol=1e-9)
        transform = np.eye(8)
        transform[0:2, 0:2] = j
        transform[4:6, 4:6] = j
        np.testing.assert_allclose(track.covariance, transform @ before_cov @ transform.T, atol=1e-9)

    def test_pure_roll_25deg_per_frame(self):
        self.check(roll_homography(25.0))

    def test_perspective_homography(self):
        self.check(tilt_homography())

    def test_unmappable_point_left_unchanged(self):
        track = make_track()
        before = track.mean.copy()
        behind = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0))  # w ≤ 0：落到相机背后
        self.assertEqual(dat.apply_pose_center([track], behind), 0)
        self.assertTrue((track.mean == before).all())

    def test_pose_aabb_identical_to_pre_change_apply_pose_warp(self):
        """`pose`/`pose-aabb` 走未改动的 `apply_pose_warp`；与 ACCEPTED 裁定提交上的同名函数逐元素一致。"""
        import numpy as np  # noqa: PLC0415

        base = accepted_base_commit()
        if base is None:
            self.skipTest("git history unavailable")
        source = subprocess.run(["git", "show", f"{base}:controller/det_assoc_tracker.py"], cwd=PROJECT_ROOT,
                                capture_output=True, text=True, check=True).stdout
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "apply_pose_warp")
        namespace = {"warp_box_xyxy": pose_gmc.warp_box_xyxy, "jacobian": pose_gmc.jacobian, "Sequence": object, "Any": object}
        exec(compile(ast.Module([node], []), "base_apply_pose_warp", "exec"), namespace)  # noqa: S102 - 修改前函数原文
        for homography in (roll_homography(25.0), tilt_homography()):
            old, new = make_track(), make_track()
            namespace["apply_pose_warp"]([old], homography)
            dat.apply_pose_warp([new], homography)
            np.testing.assert_array_equal(old.mean, new.mean)
            np.testing.assert_array_equal(old.covariance, new.covariance)

    def test_gmc_source_closed_set_and_defaults(self):
        self.assertEqual(set(pose_gmc.GMC_SOURCES), {"pose", "pose-center", "pose-aabb", "optflow", "none"})
        self.assertTrue(all(pose_gmc.is_pose_source(s) for s in ("pose", "pose-center", "pose-aabb")))
        self.assertFalse(pose_gmc.is_pose_source("optflow"))


@unittest.skipUnless(HAVE_LIBS, "需要 .venv-yoloe（ultralytics 8.4.104 + lap）")
class ResidentAssociatorTests(unittest.TestCase):
    def test_sources_dispatch_and_capture_priors(self):
        import numpy as np  # noqa: PLC0415
        from ultralytics.utils import YAML  # noqa: PLC0415
        from ultralytics.utils.checks import check_yaml  # noqa: PLC0415

        args = dict(YAML.load(check_yaml("botsort.yaml")))
        for source in ("pose", "pose-aabb", "pose-center", "none", "optflow"):
            associator = dat.make_resident_associator("botsort", args, source)
            track = make_track()
            associator.set_pose_warp(roll_homography(25.0))
            associator._pre_first_associate([track], [], np.zeros((480, 640, 3), dtype=np.uint8), None)  # noqa: SLF001
            priors = associator.take_prior_snapshots()
            self.assertEqual(len(priors), 1)
            self.assertIsNone(associator.take_prior_snapshots())
            if source == "pose-center":
                self.assertEqual(priors[0]["xywh"][2:], [60.0, 40.0])
            if source in ("pose", "pose-aabb"):
                self.assertNotEqual(priors[0]["xywh"][2:], [60.0, 40.0])  # AABB 膨胀


if __name__ == "__main__":
    unittest.main()
