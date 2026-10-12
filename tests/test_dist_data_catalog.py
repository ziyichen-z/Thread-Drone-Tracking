"""S3 逐帧 catalog、S5 字段目录与最小程序规则（§2.3/§2.4/§2.6/§2.9）。"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import build_catalog, contract, project_boxes, tier1_lang  # noqa: E402


def make_sidecar(**overrides) -> dict:
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


def vehicle(name: str, x: float, z: float, *, phantom: bool = False) -> dict:
    body = {
        "scene_object_name": name,
        "min_x_m": x - 1.0,
        "max_x_m": x + 1.0,
        "min_y_m": 0.0,
        "max_y_m": 2.0,
        "min_z_m": z - 2.0,
        "max_z_m": z + 2.0,
    }
    if phantom:
        body["phantom"] = True
    return body


CAMERA = project_boxes.Camera.from_sidecar(make_sidecar())


class TargetTruthTest(unittest.TestCase):
    def test_m3_available_box_becomes_blocker(self) -> None:
        row = {
            "truth_box_available": True,
            "truth_box_x": 0.25,
            "truth_box_y": 0.4,
            "truth_box_width": 0.1,
            "truth_box_height": 0.15,
            "intersects_frustum": True,
        }
        box, unbounded = build_catalog.target_blocker_from_truth(row, "m3", CAMERA)
        self.assertFalse(unbounded)
        assert box is not None
        self.assertAlmostEqual(box[0], 0.25 * 640)

    def test_m3_in_frustum_without_box_is_target_unbounded(self) -> None:
        """`intersects_frustum=true` 而 `truth_box_available=false` → fail-closed。"""
        row = {"truth_box_available": False, "intersects_frustum": True}
        box, unbounded = build_catalog.target_blocker_from_truth(row, "m3", CAMERA)
        self.assertIsNone(box)
        self.assertTrue(unbounded)

    def test_m3_out_of_frustum_has_no_blocker(self) -> None:
        row = {
            "truth_box_available": False,
            "intersects_frustum": False,
            "geometrically_visible": False,
        }
        box, unbounded = build_catalog.target_blocker_from_truth(row, "m3", CAMERA)
        self.assertIsNone(box)
        self.assertFalse(unbounded)

    def test_missing_truth_row_is_target_unbounded(self) -> None:
        box, unbounded = build_catalog.target_blocker_from_truth(None, "m3", CAMERA)
        self.assertIsNone(box)
        self.assertTrue(unbounded)

    def test_scouting_visible_without_box_is_target_unbounded(self) -> None:
        row = {"target_visible": True, "target_bbox_xywh_norm": None}
        _, unbounded = build_catalog.target_blocker_from_truth(row, "scouting", CAMERA)
        self.assertTrue(unbounded)

    def test_scouting_not_in_frame_has_no_blocker(self) -> None:
        row = {
            "target_visible": False,
            "target_bbox_xywh_norm": None,
            "target_box_status": "NOT_IN_FRAME",
        }
        box, unbounded = build_catalog.target_blocker_from_truth(row, "scouting", CAMERA)
        self.assertIsNone(box)
        self.assertFalse(unbounded)

    def test_real_archived_scouting_truth_parses(self) -> None:
        fixture = PROJECT_ROOT / "tests" / "fixtures" / (
            "p1_detect_scouting_truth_frame_0000000312.json"
        )
        if not fixture.exists():
            self.skipTest("scouting 真值夹具不在本工作副本中")
        row = json.loads(fixture.read_text(encoding="utf-8"))
        box, unbounded = build_catalog.target_blocker_from_truth(row, "scouting", CAMERA)
        self.assertIsInstance(unbounded, bool)
        if row.get("target_bbox_xywh_norm"):
            self.assertIsNotNone(box)

    def test_unknown_schema_is_rejected(self) -> None:
        with self.assertRaises(build_catalog.CatalogError):
            build_catalog.target_blocker_from_truth({}, "unknown", CAMERA)


class SweepProxyTest(unittest.TestCase):
    def test_route_in_view_marks_target_unbounded(self) -> None:
        route = [{"x": -5.0, "y": 0.0, "z": 20.0}, {"x": 5.0, "y": 0.0, "z": 20.0}]
        unbounded, area = build_catalog.target_unbounded_from_sweep(
            CAMERA, route, (2.0, 1.0, 2.0)
        )
        self.assertTrue(unbounded)
        self.assertGreaterEqual(area, contract.TARGET_SWEEP_MIN_AREA_PX2)

    def test_route_behind_camera_does_not(self) -> None:
        route = [{"x": -5.0, "y": 0.0, "z": -20.0}, {"x": 5.0, "y": 0.0, "z": -20.0}]
        unbounded, area = build_catalog.target_unbounded_from_sweep(
            CAMERA, route, (2.0, 1.0, 2.0)
        )
        self.assertFalse(unbounded)
        self.assertEqual(area, 0.0)

    def test_envelope_uses_max_vehicle_dimensions(self) -> None:
        instances = [vehicle("Vehicle_Taxi", 0.0, 10.0), vehicle("Building A", 0.0, 10.0)]
        instances[1]["max_x_m"] = 50.0
        half = build_catalog.vehicle_envelope_half_extents(instances)
        self.assertAlmostEqual(half[0], 1.0)  # 非车辆不参与包络


class FrameEntryTest(unittest.TestCase):
    def _frame(self, **overrides) -> build_catalog.FrameInput:
        base = dict(
            frame_id="frame-1",
            sidecar=make_sidecar(),
            family="fam",
            layout_class="default",
            usage_class="VALID_FORMAL",
            layout_binding_valid=True,
            sidecar_complete=True,
        )
        base.update(overrides)
        return build_catalog.FrameInput(**base)

    def test_referable_and_blocking_sets(self) -> None:
        bodies = [vehicle("Vehicle_Taxi", 0.0, 20.0), vehicle("Vehicle_Bus_color01", 6.0, 20.0)]
        entry = build_catalog.build_frame_entry(self._frame(truth_schema=None), bodies, [], (1.0, 1.0, 1.0))
        self.assertEqual(entry["referable"], ["Vehicle_Bus_color01", "Vehicle_Taxi"])
        self.assertEqual(entry["blocking"], ["Vehicle_Bus_color01", "Vehicle_Taxi"])
        self.assertFalse(entry["target_unbounded"])

    def test_exposure_field_per_object(self) -> None:
        bodies = [vehicle("Vehicle_Taxi", 0.0, 20.0), vehicle("Vehicle_Bus_color01", 0.0, -50.0)]
        entry = build_catalog.build_frame_entry(self._frame(truth_schema=None), bodies, [], (1.0, 1.0, 1.0))
        exposure = {item["object_id"]: item["exposure"] for item in entry["objects"]}
        self.assertEqual(exposure["Vehicle_Taxi"], "referent")
        self.assertEqual(exposure["Vehicle_Bus_color01"], "absent")

    def test_truth_box_enters_blocking(self) -> None:
        bodies = [vehicle("Vehicle_Taxi", 0.0, 20.0)]
        frame = self._frame(
            truth_schema="m3",
            truth_row={
                "truth_box_available": True,
                "truth_box_x": 0.0,
                "truth_box_y": 0.0,
                "truth_box_width": 0.05,
                "truth_box_height": 0.05,
            },
        )
        entry = build_catalog.build_frame_entry(frame, bodies, [], (1.0, 1.0, 1.0))
        self.assertIn(build_catalog.TARGET_BLOCKER_ID, entry["blocking"])
        self.assertNotIn(build_catalog.TARGET_BLOCKER_ID, entry["referable"])

    def test_pre_split_floor_eligible_predicate(self) -> None:
        bodies = [vehicle("Vehicle_Taxi", 0.0, 20.0)]
        entry = build_catalog.build_frame_entry(self._frame(truth_schema=None), bodies, [], (1.0, 1.0, 1.0))
        self.assertTrue(build_catalog.pre_split_floor_eligible(entry))
        for override in (
            {"usage_class": "SMOKE"},
            {"layout_binding_valid": False},
            {"sidecar_complete": False},
        ):
            other = build_catalog.build_frame_entry(
                self._frame(truth_schema=None, **override), bodies, [], (1.0, 1.0, 1.0)
            )
            self.assertFalse(build_catalog.pre_split_floor_eligible(other), override)

    def test_target_unbounded_frame_is_not_floor_eligible(self) -> None:
        bodies = [vehicle("Vehicle_Taxi", 0.0, 20.0)]
        frame = self._frame(truth_schema="m3", truth_row={"intersects_frustum": True})
        entry = build_catalog.build_frame_entry(frame, bodies, [], (1.0, 1.0, 1.0))
        self.assertTrue(entry["target_unbounded"])
        self.assertFalse(build_catalog.pre_split_floor_eligible(entry))


class ColourTest(unittest.TestCase):
    def test_achromatic_bands(self) -> None:
        self.assertEqual(build_catalog.classify_pixel((0, 0, 0)), "black")
        self.assertEqual(build_catalog.classify_pixel((255, 255, 255)), "white")
        self.assertEqual(build_catalog.classify_pixel((128, 128, 128)), "gray")

    def test_brown_is_dark_orange(self) -> None:
        self.assertEqual(build_catalog.classify_pixel((255, 128, 0)), "orange")
        self.assertEqual(build_catalog.classify_pixel((110, 55, 0)), "brown")

    def test_unassigned_hue_returns_none(self) -> None:
        self.assertIsNone(build_catalog.classify_pixel((255, 0, 200)))

    def test_main_band_share_threshold(self) -> None:
        """主带占比 < 0.5 → 无主色；恰 0.5 且主带唯一时仍是主色。"""
        mixed = [(255, 0, 0)] * 4 + [(0, 0, 255)] * 6
        self.assertEqual(build_catalog.estimate_color(mixed)["color"], "blue")
        half_unique = [(255, 0, 0)] * 5 + [(0, 0, 255)] * 3 + [(0, 255, 0)] * 2
        self.assertEqual(build_catalog.estimate_color(half_unique)["color"], "red")
        below_half = [(255, 0, 0)] * 4 + [(0, 0, 255)] * 3 + [(0, 255, 0)] * 3
        self.assertIsNone(build_catalog.estimate_color(below_half)["color"])

    def test_tied_main_band_is_fail_closed(self) -> None:
        """并列时不存在唯一「主带」，判无主色（UNVERIFIED 的来源之一）。"""
        tied = [(255, 0, 0)] * 5 + [(0, 0, 255)] * 5
        estimate = build_catalog.estimate_color(tied)
        self.assertIsNone(estimate["color"])
        self.assertEqual(estimate["tied_bands"], ["blue", "red"])

    def test_empty_sample_has_no_colour(self) -> None:
        self.assertIsNone(build_catalog.estimate_color([])["color"])


class _StubPixels:
    def __init__(self, mapping: dict[str, list[tuple[int, int, int]]]) -> None:
        self.mapping = mapping

    def crop_rgb(self, frame_id, box_px):  # noqa: ANN001
        return self.mapping.get(frame_id, [])


class FieldCatalogTest(unittest.TestCase):
    def _observation(self, frame: str, object_id: str, depth: float = 10.0):
        return build_catalog.ObjectObservation(frame, object_id, (0.0, 0.0, 40.0, 40.0), depth)

    def test_class_and_colour_are_recorded(self) -> None:
        catalog = build_catalog.build_field_catalog(
            ["Vehicle_Taxi"],
            [self._observation("f1", "Vehicle_Taxi")],
            _StubPixels({"f1": [(255, 230, 0)] * 10}),
        )
        record = catalog["objects"]["Vehicle_Taxi"]
        self.assertEqual(record["class"], "taxi")
        self.assertEqual(record["color"], "yellow")
        self.assertEqual(record["color_status"], "VERIFIED")
        self.assertEqual(catalog["dual_verified_object_ids"], ["Vehicle_Taxi"])

    def test_group_inconsistency_downgrades_the_whole_group(self) -> None:
        """§2.6：同 (prefab, 皮肤) 组解析到不同颜色词 → 整组 UNVERIFIED。"""
        catalog = build_catalog.build_field_catalog(
            ["Vehicle_Bus_color02", "Vehicle_Bus_color02 (1)"],
            [
                self._observation("f1", "Vehicle_Bus_color02"),
                self._observation("f2", "Vehicle_Bus_color02 (1)"),
            ],
            _StubPixels({"f1": [(0, 0, 255)] * 10, "f2": [(255, 0, 0)] * 10}),
        )
        for object_id in ("Vehicle_Bus_color02", "Vehicle_Bus_color02 (1)"):
            self.assertEqual(catalog["objects"][object_id]["color_status"], "UNVERIFIED")
            self.assertEqual(
                catalog["objects"][object_id]["color_downgrade_reason"], "GROUP_INCONSISTENT"
            )
        self.assertEqual(catalog["dual_verified_object_ids"], [])

    def test_only_k_nearest_frames_are_sampled(self) -> None:
        observations = [
            self._observation(f"f{index}", "Vehicle_Taxi", depth=float(index))
            for index in range(10)
        ]
        pixels = {f"f{index}": [(255, 230, 0)] for index in range(10)}
        catalog = build_catalog.build_field_catalog(
            ["Vehicle_Taxi"], observations, _StubPixels(pixels)
        )
        frames = catalog["objects"]["Vehicle_Taxi"]["color_evidence"]["frames"]
        self.assertEqual(len(frames), contract.COLOR_SAMPLE_FRAME_COUNT)
        self.assertEqual(frames, ["f0", "f1", "f2", "f3", "f4"])

    def test_no_observation_stays_unverified(self) -> None:
        catalog = build_catalog.build_field_catalog(["Vehicle_Taxi"], [], _StubPixels({}))
        self.assertEqual(catalog["objects"]["Vehicle_Taxi"]["color_status"], "UNVERIFIED")

    def test_audit_downgrade_only_removes_fields(self) -> None:
        """BC-DATA-1：S6 只可把 S5 字段降级，不能新增字段或样本。"""
        catalog = build_catalog.build_field_catalog(
            ["Vehicle_Taxi"],
            [self._observation("f1", "Vehicle_Taxi")],
            _StubPixels({"f1": [(255, 230, 0)] * 10}),
        )
        downgraded = build_catalog.apply_audit_downgrades(
            catalog, ["Vehicle_Taxi|"]
        )
        self.assertEqual(downgraded["objects"]["Vehicle_Taxi"]["color_status"], "UNVERIFIED")
        self.assertEqual(downgraded["dual_verified_object_ids"], [])
        self.assertEqual(set(downgraded["objects"]), set(catalog["objects"]))
        self.assertEqual(catalog["objects"]["Vehicle_Taxi"]["color_status"], "VERIFIED")


class MinimalProgramTest(unittest.TestCase):
    def _catalog(self, colours: dict[str, str | None]) -> dict:
        objects = {}
        for object_id, colour in colours.items():
            objects[object_id] = {
                "object_id": object_id,
                "class": contract.class_for_scene_object(object_id),
                "class_verified": contract.class_for_scene_object(object_id) is not None,
                "group_key": contract.color_group_key(object_id),
                "color": colour,
                "color_status": "VERIFIED" if colour else "UNVERIFIED",
            }
        return {"objects": objects}

    def _world(self, objects) -> build_catalog.FrameWorld:
        return build_catalog.FrameWorld("frame-1", list(objects))

    def test_class_only_is_preferred(self) -> None:
        world = self._world(
            [
                tier1_lang.SceneObject("Vehicle_Taxi", "taxi", "yellow", True),
                tier1_lang.SceneObject("Vehicle_Bus_color01", "bus", "blue", True),
            ]
        )
        catalog = self._catalog({"Vehicle_Taxi": "yellow", "Vehicle_Bus_color01": "blue"})
        program = build_catalog.minimal_program(world, "Vehicle_Taxi", catalog)
        self.assertEqual(program, {"target": {"class": "taxi"}})

    def test_colour_is_used_when_class_is_ambiguous(self) -> None:
        world = self._world(
            [
                tier1_lang.SceneObject("Vehicle_Taxi", "taxi", "yellow", True),
                tier1_lang.SceneObject("Vehicle_Taxi (1)", "taxi", "white", True),
            ]
        )
        catalog = self._catalog({"Vehicle_Taxi": "yellow", "Vehicle_Taxi (1)": "white"})
        program = build_catalog.minimal_program(world, "Vehicle_Taxi", catalog)
        self.assertEqual(program, {"target": {"class": "taxi", "color": "yellow"}})

    def test_relation_is_last_resort(self) -> None:
        world = self._world(
            [
                tier1_lang.SceneObject(
                    "Vehicle_Taxi", "taxi", None, True, center_px=(10.0, 10.0), world_xz=(0.0, 0.0)
                ),
                tier1_lang.SceneObject(
                    "Vehicle_Taxi (1)", "taxi", None, True, center_px=(400.0, 10.0), world_xz=(60.0, 0.0)
                ),
                tier1_lang.SceneObject(
                    "Vehicle_Bus_color01", "bus", None, True, center_px=(200.0, 10.0), world_xz=(1.0, 0.0)
                ),
            ]
        )
        catalog = self._catalog(
            {"Vehicle_Taxi": None, "Vehicle_Taxi (1)": None, "Vehicle_Bus_color01": None}
        )
        program = build_catalog.minimal_program(world, "Vehicle_Taxi", catalog)
        self.assertIsNotNone(program)
        assert program is not None
        self.assertEqual(program["relation"]["type"], "nearest_to")
        self.assertEqual(program["relation"]["ref"], {"class": "bus"})

    def test_unresolvable_object_returns_none(self) -> None:
        world = self._world(
            [
                tier1_lang.SceneObject("Vehicle_Taxi", "taxi", None, True),
                tier1_lang.SceneObject("Vehicle_Taxi (1)", "taxi", None, True),
            ]
        )
        catalog = self._catalog({"Vehicle_Taxi": None, "Vehicle_Taxi (1)": None})
        self.assertIsNone(build_catalog.minimal_program(world, "Vehicle_Taxi", catalog))

    def test_source_unprovable_target_blocker_kills_every_program(self) -> None:
        """**源身份不可证**时的 fallback：逐字段 UNKNOWN → 与全部名词通配冲突。

        §17.3 (d)：本用例只代表源身份不可证的族，**不得**再表示现有冻结目标
        （后者按 BC-DATA-9 是 source-verified `car`/`red`，只挡 car 系名词，
        见 `tests/test_dist_data_round5.py`）。目标还必须构造成**可见**：
        不可见的代理会因缺位置而让关系自动不可用，恰好绕开真正要防的路径。
        """
        world = self._world(
            [
                tier1_lang.SceneObject(
                    "Vehicle_Taxi", "taxi", "yellow", True, center_px=(500.0, 100.0)
                ),
                tier1_lang.SceneObject(
                    build_catalog.TARGET_BLOCKER_ID,
                    None,
                    None,
                    False,
                    center_px=(100.0, 100.0),
                    world_xz=(0.0, 0.0),
                    route_side=1,
                ),
            ]
        )
        catalog = self._catalog({"Vehicle_Taxi": "yellow"})
        self.assertEqual(build_catalog._unique_reference_specs(world), [])
        self.assertIsNone(build_catalog.minimal_program(world, "Vehicle_Taxi", catalog))


class PredicateTest(unittest.TestCase):
    def _entry(self, **overrides) -> dict:
        entry = {
            "frame_id": "frame-1",
            "family": "fam",
            "layout_class": "default",
            "usage_class": "VALID_FORMAL",
            "layout_binding_valid": True,
            "sidecar_complete": True,
            "target_unbounded": False,
            "referable": ["Vehicle_Taxi"],
            "blocking": ["Vehicle_Taxi"],
            "station_bin": {"key": "1:2:3:1"},
        }
        entry.update(overrides)
        return entry

    def _world(self) -> build_catalog.FrameWorld:
        return build_catalog.FrameWorld(
            "frame-1", [tier1_lang.SceneObject("Vehicle_Taxi", "taxi", "yellow", True)]
        )

    def _catalog(self) -> dict:
        return {
            "objects": {
                "Vehicle_Taxi": {
                    "object_id": "Vehicle_Taxi",
                    "class": "taxi",
                    "class_verified": True,
                    "group_key": "Vehicle_Taxi|",
                    "color": "yellow",
                    "color_status": "VERIFIED",
                }
            }
        }

    def test_holds_for_a_clean_pair(self) -> None:
        candidate = build_catalog.prospective_mother_eligible(
            self._entry(), "Vehicle_Taxi", self._world(), self._catalog()
        )
        self.assertIsNotNone(candidate)
        assert candidate is not None
        self.assertEqual(candidate["program_kind"], "attribute")
        self.assertTrue(candidate["floor_usage"])
        self.assertTrue(candidate["pre_split_floor_eligible"])

    def test_train_augment_usage_is_eligible_but_not_floor(self) -> None:
        candidate = build_catalog.prospective_mother_eligible(
            self._entry(usage_class="SMOKE"), "Vehicle_Taxi", self._world(), self._catalog()
        )
        self.assertIsNotNone(candidate)
        assert candidate is not None
        self.assertFalse(candidate["floor_usage"])
        self.assertFalse(candidate["pre_split_floor_eligible"])

    def test_diagnostic_usage_never_qualifies(self) -> None:
        self.assertIsNone(
            build_catalog.prospective_mother_eligible(
                self._entry(usage_class="DIAGNOSTIC_HOLD"),
                "Vehicle_Taxi",
                self._world(),
                self._catalog(),
            )
        )

    def test_target_unbounded_blocks_the_predicate(self) -> None:
        self.assertIsNone(
            build_catalog.prospective_mother_eligible(
                self._entry(target_unbounded=True),
                "Vehicle_Taxi",
                self._world(),
                self._catalog(),
            )
        )

    def test_non_referable_object_is_rejected(self) -> None:
        self.assertIsNone(
            build_catalog.prospective_mother_eligible(
                self._entry(referable=[]), "Vehicle_Taxi", self._world(), self._catalog()
            )
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
