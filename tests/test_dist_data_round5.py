"""接受轮 5 的具名回归（BC-DATA-9：动态目标源字段、唯一性与 ref 禁令）。

裁定：`docs/proposals/P1-VLM-DATA-001-grounding-data-foundation.md` §17
（`ACCEPTED_WITH_BINDING_CLARIFICATIONS / BC-DATA-8.3_SUPERSEDED`，2026-08-26）。

要点：现有冻结归档族的动态目标字段是 **source-verified `class=car` /
`color=red`**（版本化冻结构造源权威，非 AR2-3 所禁的读当前场景）；BC-DATA-8.3
的「对全部名词通配」**收窄**为只适用于仍然未知的字段；目标始终
`referable=False`，唯一命中它时 ref 仍不可用；目标不计入 F1 的 101 个对象。

§17.3 (b) 点名的冲突矩阵在 `ConflictMatrixTest` 里逐格覆盖。
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import build_catalog, contract, g0_report, tier1_lang  # noqa: E402

SO = tier1_lang.SceneObject


def target(*, source_bound: bool = True, **kwargs) -> tier1_lang.SceneObject:
    fields = contract.dynamic_target_fields(source_bound)
    return SO(
        build_catalog.TARGET_BLOCKER_ID,
        fields["class"],
        fields["color"],
        contract.DYNAMIC_TARGET_REFERABLE,
        **kwargs,
    )


class SourceAuthorityTest(unittest.TestCase):
    def test_bound_family_inherits_car_red(self) -> None:
        self.assertEqual(
            contract.dynamic_target_fields(True), {"class": "car", "color": "red"}
        )

    def test_unbound_family_falls_back_per_field(self) -> None:
        self.assertEqual(
            contract.dynamic_target_fields(False), {"class": None, "color": None}
        )

    def test_frozen_fields_are_inside_the_frozen_vocabularies(self) -> None:
        self.assertIn(
            contract.DYNAMIC_TARGET_SOURCE_VERIFIED_FIELDS["class"], contract.CLASS_WORDS
        )
        self.assertIn(
            contract.DYNAMIC_TARGET_SOURCE_VERIFIED_FIELDS["color"], contract.COLOR_WORDS
        )

    def test_target_is_never_referable(self) -> None:
        self.assertFalse(contract.DYNAMIC_TARGET_REFERABLE)

    def test_authority_is_the_construction_chain_not_the_scene_file(self) -> None:
        """AR2-3 禁的是读当前 Unity 场景/config 推断历史 prefab。"""
        authority = contract.DYNAMIC_TARGET_SOURCE_AUTHORITY
        self.assertIn("TargetVisualFactory", authority)
        self.assertNotIn(".unity", authority)
        self.assertNotIn("config/", authority)

    def test_frame_entry_records_the_resolved_fields(self) -> None:
        frame = build_catalog.FrameInput(
            frame_id="f1",
            sidecar={
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
            },
            family="m3-armA",
            layout_class="default",
            usage_class="VALID_FORMAL",
            layout_binding_valid=True,
            sidecar_complete=True,
            truth_schema="m3",
            truth_row={
                "truth_box_available": True,
                "truth_box_x": 0.1,
                "truth_box_y": 0.1,
                "truth_box_width": 0.2,
                "truth_box_height": 0.2,
            },
        )
        entry = build_catalog.build_frame_entry(frame, [], [], (1.0, 1.0, 1.0))
        self.assertTrue(entry["target_source_bound"])
        self.assertEqual(entry["target_fields"], {"class": "car", "color": "red"})
        self.assertIn(build_catalog.TARGET_BLOCKER_ID, entry["blocking"])
        self.assertNotIn(build_catalog.TARGET_BLOCKER_ID, entry["referable"])


class ConflictMatrixTest(unittest.TestCase):
    """§17.3 (b) 点名的五格冲突矩阵，逐格断言。"""

    def setUp(self) -> None:
        self.target = target(center_px=(100.0, 100.0))

    def _conflicts(self, spec: dict) -> bool:
        return tier1_lang._noun_conflicts(self.target, spec)

    def test_colourless_car_conflicts(self) -> None:
        self.assertTrue(self._conflicts({"class": "car"}))

    def test_red_car_conflicts(self) -> None:
        self.assertTrue(self._conflicts({"class": "car", "color": "red"}))

    def test_verified_non_red_car_does_not_conflict(self) -> None:
        self.assertFalse(self._conflicts({"class": "car", "color": "blue"}))

    def test_non_car_class_does_not_conflict(self) -> None:
        for class_word in ("taxi", "bus", "suv", "police car"):
            self.assertFalse(self._conflicts({"class": class_word}), class_word)

    def test_unverified_colour_city_car_still_conflicts_with_red_car(self) -> None:
        """颜色 `UNVERIFIED` 的城市 `Car` 与动态目标一起冲突 `the red car`。"""
        unverified = SO("Vehicle_Car_color02", "car", None, True, center_px=(500.0, 100.0))
        result = tier1_lang.execute(
            {"target": {"class": "car", "color": "red"}}, [unverified, self.target]
        )
        self.assertFalse(result.unique)
        self.assertEqual(len(result.selected_object_ids), 2)

    def test_verified_non_red_city_car_is_excluded(self) -> None:
        """只有 S5 + S6/A1 最终验证为其他颜色的 `Car` 才可排除。"""
        blue = SO("Vehicle_Car_color02", "car", "blue", True, center_px=(500.0, 100.0))
        red = SO("Vehicle_Car_color01", "car", "red", True, center_px=(300.0, 100.0))
        result = tier1_lang.execute(
            {"target": {"class": "car", "color": "red"}}, [blue, red, self.target]
        )
        self.assertNotIn("Vehicle_Car_color02", result.selected_object_ids)
        self.assertFalse(result.unique)  # 红车 + 动态目标 = 2 命中


class NarrowedWildcardTest(unittest.TestCase):
    """BC-DATA-8.3 收窄后：目标只挡 car 系名词，不再挡住一切。"""

    def setUp(self) -> None:
        self.taxi = SO("Vehicle_Taxi", "taxi", "yellow", True, center_px=(500.0, 100.0))
        self.target = target(center_px=(100.0, 100.0))
        self.world = build_catalog.FrameWorld("f1", [self.taxi, self.target])

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

    def test_taxi_is_now_uniquely_referable_beside_the_target(self) -> None:
        """轮 4 语义下这里产不出程序；轮 5 收窄后 class-only 即唯一。"""
        program = build_catalog.minimal_program(self.world, "Vehicle_Taxi", self._catalog())
        self.assertEqual(program, {"target": {"class": "taxi"}})

    def test_a_car_target_is_still_blocked_by_the_dynamic_target(self) -> None:
        car = SO("Vehicle_Car_color01", "car", "red", True, center_px=(500.0, 100.0))
        world = build_catalog.FrameWorld("f2", [car, self.target])
        catalog = {
            "objects": {
                "Vehicle_Car_color01": {
                    "object_id": "Vehicle_Car_color01",
                    "class": "car",
                    "class_verified": True,
                    "group_key": "Vehicle_Car_color01|color01",
                    "color": "red",
                    "color_status": "VERIFIED",
                }
            }
        }
        self.assertIsNone(build_catalog.minimal_program(world, "Vehicle_Car_color01", catalog))

    def test_unbound_source_still_wildcards_everything(self) -> None:
        """§17.3 (d)：旧的「全名词通配」只保留为源身份不可证的 fallback。"""
        fallback = target(source_bound=False, center_px=(100.0, 100.0))
        world = build_catalog.FrameWorld("f3", [self.taxi, fallback])
        self.assertEqual(build_catalog._unique_reference_specs(world), [])
        self.assertIsNone(build_catalog.minimal_program(world, "Vehicle_Taxi", self._catalog()))


class NeverAReferenceTest(unittest.TestCase):
    """BC-DATA-9.3：唯一命中的若是动态目标，ref 仍不可用。"""

    def test_unique_hit_on_the_target_does_not_yield_a_reference(self) -> None:
        taxi_a = SO("Vehicle_Taxi", "taxi", None, True, center_px=(500.0, 100.0))
        taxi_b = SO("Vehicle_Taxi (1)", "taxi", None, True, center_px=(520.0, 100.0))
        world = build_catalog.FrameWorld(
            "f", [taxi_a, taxi_b, target(center_px=(100.0, 100.0))]
        )
        # `the car` / `the red car` 在域内恰一命中——但命中的是动态目标。
        self.assertIsNone(tier1_lang._resolve_ref(world.domain, {"class": "car"}))
        self.assertIsNone(
            tier1_lang._resolve_ref(world.domain, {"class": "car", "color": "red"})
        )
        for spec in build_catalog._unique_reference_specs(world):
            self.assertNotEqual(spec.get("class"), "car")

    def test_a_referable_city_car_still_works_as_a_reference(self) -> None:
        city_car = SO("Vehicle_Car_color02", "car", "blue", True, center_px=(300.0, 100.0))
        taxi = SO("Vehicle_Taxi", "taxi", None, True, center_px=(500.0, 100.0))
        world = build_catalog.FrameWorld(
            "f", [city_car, taxi, target(center_px=(100.0, 100.0))]
        )
        resolved = tier1_lang._resolve_ref(world.domain, {"class": "car", "color": "blue"})
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.object_id, "Vehicle_Car_color02")


class F1ExclusionTest(unittest.TestCase):
    def test_dynamic_target_is_not_one_of_the_101_objects(self) -> None:
        """BC-DATA-9.3：动态目标不计入 F1 的 101 个对象。"""
        catalog = {
            "objects": {
                "Vehicle_Car_color01": {"class": "car"},
            },
            "dual_verified_object_ids": ["Vehicle_Car_color01"],
        }
        result = g0_report.compute_f1(catalog)
        self.assertEqual(result["denominator"], 101)
        self.assertNotIn(build_catalog.TARGET_BLOCKER_ID, result["dual_verified_object_ids"])

    def test_the_target_never_enters_the_field_catalog(self) -> None:
        catalog = build_catalog.build_field_catalog(
            [build_catalog.TARGET_BLOCKER_ID], [], _NoPixels()
        )
        self.assertFalse(catalog["objects"][build_catalog.TARGET_BLOCKER_ID]["class_verified"])
        self.assertEqual(catalog["dual_verified_object_ids"], [])


class _NoPixels:
    def crop_rgb(self, frame_id, box_px):  # noqa: ANN001
        return []


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
