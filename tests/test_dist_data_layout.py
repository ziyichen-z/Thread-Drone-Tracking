"""S2 布局绑定：逆施/正施、phantom、removal 双向语义、交叉验证（§2.3，BC-DATA-3）。

夹具由生产路径产出：基础几何是复核链内产出的
`docs/evidence/P1-M3-BODY-001-scene-geometry.json`（S0 哈希钉死），
relocations 直接来自归档 scenario 字节，均不手写。
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import bind_layout, contract, project_boxes, roots  # noqa: E402


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
        "intrinsics_px": {
            "fx": 415.6921938165305,
            "fy": 415.6921938165305,
            "cx": 320.0,
            "cy": 240.0,
        },
    }
    document.update(overrides)
    return document

DEFAULT_SCENARIO = PROJECT_ROOT / "config" / "scenario.default.json"
S004_SCENARIO = PROJECT_ROOT / "runtime" / "scenario_config.p1-scene-004.hold.json"


def _relocations(path: Path) -> list[dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return document.get("scene_adjustments", {}).get("vehicle_relocations", [])


class BaseGeometryTest(unittest.TestCase):
    def test_pinned_bytes_and_shape(self) -> None:
        geometry = bind_layout.load_base_geometry(PROJECT_ROOT)
        self.assertEqual(len(geometry["instances"]), contract.BASE_GEOMETRY_INSTANCE_COUNT)
        vehicles = [
            instance
            for instance in geometry["instances"]
            if contract.class_for_scene_object(instance["scene_object_name"])
        ]
        self.assertEqual(len(vehicles), contract.BASE_GEOMETRY_VEHICLE_COUNT)

    def test_byte_change_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / contract.BASE_GEOMETRY_PATH
            target.parent.mkdir(parents=True)
            target.write_text("{}", encoding="utf-8")
            with self.assertRaises(bind_layout.LayoutError):
                bind_layout.load_base_geometry(root)


class RelocationTest(unittest.TestCase):
    def setUp(self) -> None:
        if not DEFAULT_SCENARIO.exists():
            self.skipTest("default scenario 字节不在本工作副本中")
        self.geometry = bind_layout.load_base_geometry(PROJECT_ROOT)
        self.default_relocations = _relocations(DEFAULT_SCENARIO)
        self.unadjusted, self.phantom_candidates = bind_layout.unadjusted_base(
            self.geometry["instances"], self.default_relocations
        )

    def test_inverse_then_forward_reproduces_base_geometry(self) -> None:
        """逆施 default 再正施 default 必须逐字节回到已调整基础几何。"""
        derived = bind_layout.apply_layout(
            self.unadjusted, self.default_relocations, self.phantom_candidates
        )
        original = sorted(
            self.geometry["instances"], key=lambda item: item["scene_object_name"]
        )
        self.assertEqual(len(derived["instances"]), len(original))
        for produced, expected in zip(derived["instances"], original):
            self.assertEqual(produced["scene_object_name"], expected["scene_object_name"])
            for axis in ("min_x_m", "max_x_m", "min_y_m", "max_y_m", "min_z_m", "max_z_m"):
                self.assertAlmostEqual(produced[axis], expected[axis], places=6, msg=axis)

    def test_default_removals_become_phantom_candidates(self) -> None:
        self.assertEqual(len(self.phantom_candidates), 3)
        self.assertEqual(
            sorted(item["prefab_name"] for item in self.phantom_candidates),
            ["Vehicle_Car_color03", "Vehicle_Container_color02", "Vehicle_Police Car"],
        )

    def test_default_layout_registers_no_phantom(self) -> None:
        """§2.3 (a)：phantom 只登记在**其他**布局类；default 自身该实例不存在。"""
        derived = bind_layout.apply_layout(
            self.unadjusted, self.default_relocations, self.phantom_candidates
        )
        self.assertEqual(derived["phantoms"], [])

    def test_scene004_registers_three_phantoms(self) -> None:
        if not S004_SCENARIO.exists():
            self.skipTest("scene-004 归档字节不在本工作副本中")
        derived = bind_layout.apply_layout(
            self.unadjusted, _relocations(S004_SCENARIO), self.phantom_candidates
        )
        self.assertEqual(len(derived["phantoms"]), 3)
        for phantom in derived["phantoms"]:
            self.assertTrue(phantom["phantom"])
            self.assertGreater(phantom["max_x_m"] - phantom["min_x_m"], 0.0)
            self.assertIn(phantom["class_word"], contract.CLASS_WORDS)

    def test_scene004_relocations_land_on_archived_positions(self) -> None:
        if not S004_SCENARIO.exists():
            self.skipTest("scene-004 归档字节不在本工作副本中")
        relocations = _relocations(S004_SCENARIO)
        derived = bind_layout.apply_layout(
            self.unadjusted, relocations, self.phantom_candidates
        )
        by_name = {item["scene_object_name"]: item for item in derived["instances"]}
        for entry in relocations:
            moved = [
                name
                for name in derived["relocation_marks"]
                if contract.prefab_base_name(name) == entry["prefab_name"]
            ]
            self.assertTrue(moved, entry["prefab_name"])
            centre = bind_layout.xz_center(by_name[moved[0]])
            tolerance = bind_layout.match_tolerance(
                entry, [by_name[moved[0]]]
            )
            self.assertLessEqual(
                ((centre[0] - entry["new_position_m"]["x"]) ** 2
                 + (centre[1] - entry["new_position_m"]["z"]) ** 2) ** 0.5,
                tolerance,
            )

    def test_ambiguous_match_is_a_hard_error(self) -> None:
        """恰一个候选落入 T_match；多个即硬错误（§2.3 匹配合同）。"""
        twins = [
            {
                "scene_object_name": "Vehicle_Taxi",
                "min_x_m": -1.0, "max_x_m": 1.0,
                "min_y_m": 0.0, "max_y_m": 1.0,
                "min_z_m": -1.0, "max_z_m": 1.0,
            },
            {
                "scene_object_name": "Vehicle_Taxi (1)",
                "min_x_m": -1.1, "max_x_m": 0.9,
                "min_y_m": 0.0, "max_y_m": 1.0,
                "min_z_m": -1.0, "max_z_m": 1.0,
            },
        ]
        entry = {
            "prefab_name": "Vehicle_Taxi",
            "original_xz_m": {"x": 0.0, "z": 0.0},
            "match_tolerance_m": 0.1,
            "new_position_m": {"x": 5.0, "y": 0.0, "z": 5.0},
        }
        with self.assertRaises(bind_layout.LayoutError):
            bind_layout.apply_layout(twins, [entry], [])

    def test_layout_own_removal_deletes_the_instance(self) -> None:
        """§2.3 (b)：布局类自身移除存在的实例 → 从目录与遮挡体一并移除，不是代理。"""
        instances = [
            {
                "scene_object_name": "Vehicle_Bus_color01",
                "min_x_m": -1.0, "max_x_m": 1.0,
                "min_y_m": 0.0, "max_y_m": 1.0,
                "min_z_m": -1.0, "max_z_m": 1.0,
            }
        ]
        entry = {
            "prefab_name": "Vehicle_Bus_color01",
            "original_xz_m": {"x": 0.0, "z": 0.0},
            "match_tolerance_m": 0.1,
            "remove_from_scene": True,
        }
        derived = bind_layout.apply_layout(instances, [entry], [])
        self.assertEqual(derived["instances"], [])
        self.assertEqual(derived["removed"], ["Vehicle_Bus_color01"])
        self.assertEqual(derived["phantoms"], [])


class RoadDataTest(unittest.TestCase):
    def test_hash_equal_current_config_may_serve_as_byte_provider(self) -> None:
        if not DEFAULT_SCENARIO.exists():
            self.skipTest("default scenario 字节不在本工作副本中")
        document = json.loads(DEFAULT_SCENARIO.read_text(encoding="utf-8"))
        result = bind_layout.resolve_road_data(PROJECT_ROOT, document)
        self.assertTrue(result["available"])
        self.assertEqual(result["sha256"], document["road_data_sha256"])

    def test_unmatched_hash_reports_unavailable_without_crashing(self) -> None:
        result = bind_layout.resolve_road_data(
            PROJECT_ROOT, {"road_data_sha256": "0" * 64}
        )
        self.assertFalse(result["available"])

    def test_missing_declaration_is_unavailable(self) -> None:
        self.assertFalse(bind_layout.resolve_road_data(PROJECT_ROOT, {})["available"])


class CrossValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.camera = project_boxes.Camera.from_sidecar(make_sidecar())
        # BC-DATA-24 (1) 后，比较域是 viewport 裁剪后的预测框，所以夹具的实例
        # 必须**真的在画面里**——原来那排 x = -1+i…1+i 有 40/60 完全落在视口外，
        # 它们在旧的 amodal 域里靠「预测框 = 真值框」互相抵消而侥幸通过。
        # 现改为 12 列 × 5 排的网格，全部在视锥内（`setUp` 末尾断言）。
        self.instances = [
            {
                "scene_object_name": f"Vehicle_Taxi ({index})",
                "min_x_m": -11.0 + (index % 12) * 2.0,
                "max_x_m": -9.0 + (index % 12) * 2.0,
                "min_y_m": 0.0, "max_y_m": 2.0,
                "min_z_m": 20.0 + (index // 12) * 8.0,
                "max_z_m": 24.0 + (index // 12) * 8.0,
            }
            for index in range(60)
        ]
        visible = [
            instance
            for instance in self.instances
            if self._clipped(instance) is not None
        ]
        self.assertEqual(len(visible), 60, "夹具实例必须全部在视口内")

    def _clipped(self, instance: dict):
        """归档真值框的语义：AABB 投影后**裁到 viewport 内**（BC-DATA-24 (1)）。"""
        projected = project_boxes.project_aabb(self.camera, instance)
        if projected is None:
            return None
        return project_boxes.intersect(projected, self.camera.viewport())

    def _samples(self, count: int, *, perfect: bool) -> list[dict]:
        samples = []
        for index in range(count):
            instance = self.instances[index]
            clipped = self._clipped(instance)
            assert clipped is not None
            # 完美情形的「归档真值」= 裁剪框，与归档 `bbox_xywh_norm` 同域。
            box = clipped if perfect else (0.0, 0.0, 1.0, 1.0)
            samples.append(
                {
                    "frame_id": f"frame-{index}",
                    "camera": self.camera,
                    "pairs": [{"object_id": instance["scene_object_name"], "box_px": box}],
                }
            )
        return samples

    def test_fewer_than_fifty_pairs_is_invalid(self) -> None:
        result = bind_layout.cross_validate_layout(self.instances, self._samples(10, perfect=True))
        self.assertEqual(result["status"], bind_layout.BINDING_INVALID)
        self.assertIn("不以动态 target 补数", result["reason"])

    def test_matching_boxes_pass(self) -> None:
        result = bind_layout.cross_validate_layout(self.instances, self._samples(55, perfect=True))
        self.assertEqual(result["status"], bind_layout.BINDING_BOUND)
        self.assertEqual(result["pair_count"], contract.CROSSCHECK_MIN_PAIRS)
        self.assertGreaterEqual(result["center_hit_ratio"], 0.9)

    def test_shifted_boxes_fail(self) -> None:
        result = bind_layout.cross_validate_layout(self.instances, self._samples(55, perfect=False))
        self.assertEqual(result["status"], bind_layout.BINDING_INVALID)

    def test_unmapped_distractor_ids_are_dropped(self) -> None:
        samples = self._samples(55, perfect=True)
        for sample in samples:
            sample["pairs"] = [{"object_id": "not-in-catalog", "box_px": (0, 0, 1, 1)}]
        result = bind_layout.cross_validate_layout(self.instances, samples)
        self.assertEqual(result["status"], bind_layout.BINDING_INVALID)
        self.assertEqual(result["pair_count"], 0)

    def test_selection_is_deterministic(self) -> None:
        samples = self._samples(55, perfect=True)
        first = bind_layout.cross_validate_layout(self.instances, samples)
        second = bind_layout.cross_validate_layout(self.instances, list(reversed(samples)))
        self.assertEqual(first["center_hit_ratio"], second["center_hit_ratio"])
        self.assertEqual(first["iou_median"], second["iou_median"])


class TargetWorldCheckTest(unittest.TestCase):
    def test_only_center_hit_ratio_is_computed(self) -> None:
        """BC-DATA-3：m3 动态 target 的世界坐标只做中心落框率，不进静态 IoU。"""
        camera = project_boxes.Camera.from_sidecar(make_sidecar())
        pixel = camera.project_camera_point(camera.to_camera_space((0.0, 0.0, 20.0)))
        inside = (pixel[0] - 10, pixel[1] - 10, pixel[0] + 10, pixel[1] + 10)
        outside = (0.0, 0.0, 5.0, 5.0)
        samples = [
            {"camera": camera, "target_world_m": (0.0, 0.0, 20.0), "truth_box_px": inside}
            for _ in range(9
                           )
        ] + [
            {"camera": camera, "target_world_m": (0.0, 0.0, 20.0), "truth_box_px": outside}
        ]
        result = bind_layout.target_world_center_hit_ratio(samples)
        self.assertEqual(result["sample_count"], 10)
        self.assertAlmostEqual(result["center_hit_ratio"], 0.9)
        self.assertTrue(result["passed"])
        self.assertNotIn("iou_median", result)


class ScenarioResolutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_embedded_snapshot_wins(self) -> None:
        frames = self.root / "runtime" / "runs" / "demo" / "frames"
        frames.mkdir(parents=True)
        (frames / "frame_0.jpg").write_bytes(b"x")
        snapshot = self.root / "runtime" / "runs" / "demo" / "scenario.json"
        snapshot.write_text('{"scenario_id":"demo"}', encoding="utf-8")
        resolution = bind_layout.resolve_frame_scenario(
            self.root, "runtime/runs/demo/frames/frame_0.jpg", {}
        )
        self.assertEqual(resolution["status"], bind_layout.BINDING_BOUND)
        self.assertEqual(resolution["source"], "embedded_snapshot")

    def test_manifest_sha_match_is_second_priority(self) -> None:
        frames = self.root / "runtime" / "runs" / "demo" / "frames"
        frames.mkdir(parents=True)
        (frames / "frame_0.jpg").write_bytes(b"x")
        manifest = self.root / "runtime" / "runs" / "demo" / "manifest.json"
        manifest.write_text('{"scenario_config_sha256":"' + "a" * 64 + '"}', encoding="utf-8")
        resolution = bind_layout.resolve_frame_scenario(
            self.root,
            "runtime/runs/demo/frames/frame_0.jpg",
            {"a" * 64: ["config/scenario.default.json"]},
        )
        self.assertEqual(resolution["status"], bind_layout.BINDING_BOUND)
        self.assertEqual(resolution["source"], "manifest_sha_match")

    def test_unmatched_manifest_sha_is_unbound(self) -> None:
        frames = self.root / "runtime" / "runs" / "demo" / "frames"
        frames.mkdir(parents=True)
        (frames / "frame_0.jpg").write_bytes(b"x")
        manifest = self.root / "runtime" / "runs" / "demo" / "manifest.json"
        manifest.write_text('{"scenario_config_sha256":"' + "b" * 64 + '"}', encoding="utf-8")
        resolution = bind_layout.resolve_frame_scenario(
            self.root, "runtime/runs/demo/frames/frame_0.jpg", {}
        )
        self.assertEqual(resolution["status"], bind_layout.BINDING_UNBOUND)

    def test_no_binding_at_all(self) -> None:
        frames = self.root / "runtime" / "orphan"
        frames.mkdir(parents=True)
        (frames / "frame_0.jpg").write_bytes(b"x")
        resolution = bind_layout.resolve_frame_scenario(
            self.root, "runtime/orphan/frame_0.jpg", {}
        )
        self.assertEqual(resolution["status"], bind_layout.BINDING_UNBOUND)
        self.assertEqual(resolution["source"], "no_scenario_binding")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
