"""接受轮 4 的具名回归（BC-DATA-6 / BC-DATA-7 / BC-DATA-8.3 / BC-DATA-8.4）。

裁定：`docs/proposals/P1-VLM-DATA-001-grounding-data-foundation.md` §16
（`STOP_POINT_NOT_CONFIRMED / IMPLEMENTATION_REWORK_REQUIRED`，2026-08-26）。

本文件里每一条都是**修复前必失败**的回归：BC-DATA-6/-7 钉住冻结根闭集的
逐 pattern 计数与用途类，BC-DATA-8.3/8.4 钉住「永不可指称」与 ref 枚举序。
真实归档相关的断言全部**只读**，不创建任何工件、不消耗任何 ID。
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import build_catalog, contract, roots, tier1_lang  # noqa: E402

SO = tier1_lang.SceneObject

PROBE_BASELINE = "runtime/p1-scene-006/probe-baseline-vfov60/frames"
PROBE_CANDIDATE = "runtime/p1-scene-006/probe-candidate-vfov40/frames"
RS3_FRAMES = "runtime/test-results/rs3-clock-smoke/phase1-hold/frames"

ARM_A_VALID_TRUTH = (
    "runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4/m3_body_truth.jsonl",
    "runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2/m3_body_truth.jsonl",
    "runtime/runs/p1-m3-body-001-arm-a-trial-3/m3_body_truth.jsonl",
    "runtime/runs/p1-m3-body-001-arm-a-trial-4/m3_body_truth.jsonl",
    "runtime/runs/p1-m3-body-001-arm-a-trial-5/m3_body_truth.jsonl",
)
ARM_A_VOID_RUN_TRUTH = (
    "runtime/runs/p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold/m3_body_truth.jsonl"
)


def sole_entry(path: str, kind: str) -> roots.RootEntry:
    """断言该路径在**全表**上恰匹配一个同 kind 的 pattern，并返回它。

    走 `roots.matching_entries`（遍历每一行），因此不依赖表序，也不会被
    first-match-wins 掩盖重叠（BC-DATA-7 明令禁止依赖表序）。
    """
    matches = [entry for entry in roots.matching_entries(path) if entry.kind == kind]
    if len(matches) != 1:
        raise AssertionError(
            f"{path} 匹配 {len(matches)} 条 {kind} pattern："
            f"{[entry.pattern for entry in matches]}"
        )
    return matches[0]


# --- BC-DATA-6：探针 jpg 与 rs3 派生图的根闭集补正 -------------------------
class BcData6RootClosureTest(unittest.TestCase):
    def test_scene006_probe_frames_are_invalid_render_probe(self) -> None:
        """两个探针目录的 `frame_*.jpg` 各自恰匹配一条 `INVALID_RENDER_PROBE`。"""
        for directory in (PROBE_BASELINE, PROBE_CANDIDATE):
            entry = sole_entry(f"{directory}/frame_000015.jpg", roots.KIND_IMAGE)
            self.assertEqual(entry.usage_class, "INVALID_RENDER_PROBE", directory)
            self.assertIsNone(entry.family, directory)
            self.assertIsNone(entry.layout_class, directory)

    def test_scene006_prompt_jpg_is_covered_by_the_same_pattern(self) -> None:
        """每个探针目录含 1 张 `prompt_*.jpg`，故 pattern 必须是 `*.jpg`。

        写成 `frame_*.jpg` 会在真实归档上残留 2 个 zero-match。
        """
        for directory, name in (
            (PROBE_BASELINE, "prompt_000000.jpg"),
            (PROBE_CANDIDATE, "prompt_000002.jpg"),
        ):
            entry = sole_entry(f"{directory}/{name}", roots.KIND_IMAGE)
            self.assertEqual(entry.usage_class, "INVALID_RENDER_PROBE", name)

    def test_rs3_init_box_preview_is_derived_overlay_not_smoke(self) -> None:
        """派生图不得继承同目录 173 张原始帧的 `SMOKE` 资格。"""
        preview = sole_entry(f"{RS3_FRAMES}/init-box-preview.jpg", roots.KIND_IMAGE)
        self.assertEqual(preview.usage_class, "DERIVED_OVERLAY")
        self.assertIsNone(preview.family)
        self.assertIsNone(preview.layout_class)
        sibling = sole_entry(f"{RS3_FRAMES}/frame_0000000001.jpg", roots.KIND_IMAGE)
        self.assertEqual(sibling.usage_class, "SMOKE")
        self.assertEqual(sibling.family, "s004-smoke")

    def test_invalid_render_probe_is_in_every_closed_set(self) -> None:
        self.assertIn("INVALID_RENDER_PROBE", contract.USAGE_CLASSES)
        self.assertIn("INVALID_RENDER_PROBE", roots.USAGE_ELIGIBILITY)
        self.assertIn("INVALID_RENDER_PROBE", roots.USAGE_DECISION)
        self.assertEqual(roots.USAGE_DECISION["INVALID_RENDER_PROBE"], "INVENTORY_ONLY")
        self.assertEqual(
            roots.USAGE_ELIGIBILITY["INVALID_RENDER_PROBE"],
            {"mother": False, "floor": False, "test": False},
        )

    def test_invalid_render_probe_never_reaches_floor_or_training(self) -> None:
        """F23 已否定其外观保真：不得进 train/dev 扩增、F1–F4 或 test。"""
        self.assertNotIn("INVALID_RENDER_PROBE", contract.FLOOR_USAGE_CLASSES)
        self.assertNotIn("INVALID_RENDER_PROBE", contract.TRAIN_AUGMENT_USAGE_CLASSES)
        self.assertNotIn("INVALID_RENDER_PROBE", contract.MOTHER_USAGE_CLASSES)

    def test_no_new_inventory_reason_code_was_added(self) -> None:
        """裁定：`INVALID_RENDER_PROBE` 加入用途类闭集，但**不新增** inventory reason。"""
        self.assertEqual(
            contract.INVENTORY_DECISIONS,
            (
                "INCLUDED",
                "INVENTORY_ONLY",
                "EXCLUDED_UNBOUND_SCENARIO",
                "EXCLUDED_NO_POSE",
                "EXCLUDED_THIRD_PARTY",
                "EXCLUDED_DERIVED",
                "EXCLUDED_DIAGNOSTIC_CHANNEL",
                "EXCLUDED_UNRELEASED",
            ),
        )

    def test_usage_class_order_matches_proposal_section_2_2(self) -> None:
        """表序即 lineage primary 优先级：探针须排在全部 mother/floor 类之后。"""
        order = list(contract.USAGE_CLASSES)
        self.assertEqual(
            order[order.index("THIRD_PARTY_ASSET") + 1], "INVALID_RENDER_PROBE"
        )
        self.assertEqual(
            order[order.index("INVALID_RENDER_PROBE") + 1], "PROBE_TRUTH_ONLY"
        )
        for usage in contract.MOTHER_USAGE_CLASSES:
            self.assertLess(order.index(usage), order.index("INVALID_RENDER_PROBE"))


# --- BC-DATA-7：void run truth 从有效 truth 闭集中拆出 ---------------------
class BcData7TruthClosureTest(unittest.TestCase):
    def test_five_valid_arm_a_truths_are_valid_formal(self) -> None:
        for path in ARM_A_VALID_TRUTH:
            entry = sole_entry(path, roots.KIND_TRUTH)
            self.assertEqual(entry.usage_class, "VALID_FORMAL", path)
            self.assertEqual(entry.family, "m3-armA", path)
            self.assertEqual(entry.layout_class, roots.LAYOUT_DEFAULT, path)

    def test_void_run_truth_is_void_trial_hold_not_valid_formal(self) -> None:
        """R2 的复现点：这条以前被宽泛 pattern 写成 `VALID_FORMAL`。"""
        entry = sole_entry(ARM_A_VOID_RUN_TRUTH, roots.KIND_TRUTH)
        self.assertEqual(entry.usage_class, "VOID_TRIAL_HOLD")
        self.assertEqual(entry.family, "m3-armA")
        self.assertEqual(entry.layout_class, roots.LAYOUT_DEFAULT)

    def test_root_level_void_truth_pattern_is_unchanged(self) -> None:
        entry = sole_entry(
            "runtime/m3_body_truth.arm-a-trial-1-void-attempt-2-hold.jsonl",
            roots.KIND_TRUTH,
        )
        self.assertEqual(entry.usage_class, "VOID_TRIAL_HOLD")

    def test_the_broad_arm_a_truth_pattern_is_gone(self) -> None:
        """宽泛 pattern 必须删除，否则它会与三条精确 pattern 重叠。"""
        self.assertNotIn(
            "runtime/runs/p1-m3-body-001-arm-a-*/m3_body_truth.jsonl",
            [entry.pattern for entry in roots.ROOT_TABLE],
        )

    def test_arm_b_truth_pattern_is_untouched(self) -> None:
        entry = sole_entry(
            "runtime/runs/p1-m3-body-001-arm-b-trial-4/m3_body_truth.jsonl",
            roots.KIND_TRUTH,
        )
        self.assertEqual(entry.usage_class, "VALID_FORMAL")
        self.assertEqual(entry.family, "m3-armB")


# --- BC-DATA-8.3：「永不可指称」必须有机械实施点 ---------------------------
def _catalog(*object_ids: str) -> dict:
    objects = {}
    for object_id in object_ids:
        objects[object_id] = {
            "object_id": object_id,
            "class": contract.class_for_scene_object(object_id),
            "class_verified": contract.class_for_scene_object(object_id) is not None,
            "group_key": contract.color_group_key(object_id),
            "color": None,
            "color_status": "UNVERIFIED",
        }
    return {"objects": objects}


class BcData8NeverReferableTest(unittest.TestCase):
    """轮 5 后本类固定使用**源身份不可证**的 fallback 目标（§17.3 (d)）。

    现有冻结归档族的目标按 BC-DATA-9 是 source-verified `car`/`red`，只挡
    car 系名词——那条收窄语义由 `tests/test_dist_data_round5.py` 覆盖。这里
    要守的是另一半：无论字段已知与否，目标 `referable=False`，唯一命中它时
    ref 仍不可用。
    """

    def setUp(self) -> None:
        # 一辆可指称的目录车 + 一个**可见**、源身份不可证的动态目标代理。
        fields = contract.dynamic_target_fields(False)
        self.taxi = SO("Vehicle_Taxi", "taxi", None, True, center_px=(500.0, 100.0))
        self.target = SO(
            build_catalog.TARGET_BLOCKER_ID,
            fields["class"],
            fields["color"],
            contract.DYNAMIC_TARGET_REFERABLE,
            center_px=(100.0, 100.0),
        )
        self.world = build_catalog.FrameWorld("f1", [self.taxi, self.target])

    def test_source_unprovable_target_leaves_no_unique_reference(self) -> None:
        """通配对象仍参与唯一性分母，但**自己**永不可被选为 ref。"""
        self.assertEqual(build_catalog._unique_reference_specs(self.world), [])

    def test_source_unprovable_target_yields_no_minimal_program(self) -> None:
        """§5.2 轮 4 措辞（轮 5 对**已绑定**目标 supersede，此处仍适用 fallback）。"""
        self.assertIsNone(
            build_catalog.minimal_program(self.world, "Vehicle_Taxi", _catalog("Vehicle_Taxi"))
        )

    def test_resolve_ref_never_returns_a_non_referable_object(self) -> None:
        resolved = tier1_lang._resolve_ref(self.world.domain, {"class": "ambulance"})
        self.assertIsNone(resolved)

    def test_phantom_is_never_used_as_a_relation_reference(self) -> None:
        """phantom 同样「永不可指称」，只能作阻断体。"""
        phantom = SO(
            "phantom:Vehicle_Bus_color01@1,2", "bus", None, False, center_px=(100.0, 100.0)
        )
        taxi_a = SO("Vehicle_Taxi", "taxi", None, True, center_px=(500.0, 100.0))
        taxi_b = SO("Vehicle_Taxi (1)", "taxi", None, True, center_px=(520.0, 100.0))
        world = build_catalog.FrameWorld("f2", [taxi_a, taxi_b, phantom])
        self.assertIsNone(tier1_lang._resolve_ref(world.domain, {"class": "bus"}))
        self.assertNotIn({"class": "bus"}, build_catalog._unique_reference_specs(world))
        self.assertIsNone(
            build_catalog.minimal_program(
                world, "Vehicle_Taxi", _catalog("Vehicle_Taxi", "Vehicle_Taxi (1)")
            )
        )

    def test_referable_catalog_object_still_resolves(self) -> None:
        """修复不得把正常的可指称 ref 一起封死。"""
        bus = SO("Vehicle_Bus_color01", "bus", None, True, center_px=(100.0, 100.0))
        taxi = SO("Vehicle_Taxi", "taxi", None, True, center_px=(500.0, 100.0))
        world = build_catalog.FrameWorld("f3", [taxi, bus])
        resolved = tier1_lang._resolve_ref(world.domain, {"class": "bus"})
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.object_id, "Vehicle_Bus_color01")


# --- BC-DATA-8.4：ref 颜色词按升序枚举 -------------------------------------
class BcData8ReferenceOrderTest(unittest.TestCase):
    def test_contract_exposes_ascending_colour_order(self) -> None:
        self.assertEqual(
            list(contract.COLOR_WORDS_ASCENDING), sorted(contract.COLOR_WORDS)
        )

    def test_reference_specs_enumerate_class_then_colourless_then_colour_ascending(
        self,
    ) -> None:
        """冻结序：类别词升序 → 无色在前 → 颜色词升序。"""
        domain = [
            SO("Vehicle_Bus_color01", "bus", "blue", True),
            SO("Vehicle_Taxi", "taxi", "yellow", True),
        ]
        specs = build_catalog._unique_reference_specs(build_catalog.FrameWorld("f", domain))
        classes = [spec["class"] for spec in specs]
        self.assertEqual(classes, sorted(classes))
        bus_colours = [
            spec.get("color") for spec in specs if spec["class"] == "bus"
        ]
        self.assertIsNone(bus_colours[0])  # 无色在前
        named = [colour for colour in bus_colours if colour is not None]
        self.assertEqual(named, sorted(named))  # 颜色词升序


# --- 未知位置/边必须阻断唯一性，而不是被静默丢弃 ---------------------------
class UnknownPositionBlocksUniquenessTest(unittest.TestCase):
    """与 BC-DATA-8.3 同源：本模块自己的「未知即通配冲突」政策。"""

    REF = SO("Vehicle_Bus_color01", "bus", None, True, world_xz=(0.0, 0.0), center_px=(300.0, 100.0), route_side=1)

    def test_unknown_world_position_blocks_nearest_to(self) -> None:
        known = SO("A", "taxi", None, True, world_xz=(1.0, 0.0))
        unknown = SO("B", "taxi", None, True, world_xz=None)
        result = tier1_lang.execute(
            {"target": {"class": "taxi"}, "relation": {"type": "nearest_to", "ref": {"class": "bus"}}},
            [known, unknown, self.REF],
        )
        self.assertFalse(result.unique)
        self.assertFalse(result.relation_available)

    def test_unknown_pixel_centre_blocks_viewer_side(self) -> None:
        known = SO("A", "taxi", None, True, center_px=(500.0, 100.0))
        unknown = SO("B", "taxi", None, True, center_px=None)
        result = tier1_lang.execute(
            {
                "target": {"class": "taxi"},
                "relation": {"type": "viewer_right_of", "ref": {"class": "bus"}},
            },
            [known, unknown, self.REF],
        )
        self.assertFalse(result.unique)
        self.assertFalse(result.relation_available)

    def test_unknown_route_side_blocks_on_route_side(self) -> None:
        known = SO("A", "taxi", None, True, route_side=1)
        unknown = SO("B", "taxi", None, True, route_side=None)
        result = tier1_lang.execute(
            {
                "target": {"class": "taxi"},
                "relation": {"type": "on_route_side", "ref": {"class": "bus"}},
            },
            [known, unknown, self.REF],
        )
        self.assertFalse(result.unique)
        self.assertFalse(result.relation_available)

    def test_fully_known_domain_still_resolves(self) -> None:
        near = SO("A", "taxi", None, True, world_xz=(1.0, 0.0))
        far = SO("B", "taxi", None, True, world_xz=(100.0, 0.0))
        result = tier1_lang.execute(
            {"target": {"class": "taxi"}, "relation": {"type": "nearest_to", "ref": {"class": "bus"}}},
            [near, far, self.REF],
        )
        self.assertTrue(result.unique)
        self.assertEqual(result.selected_object_ids, ("A",))


# --- 只读真实归档断言（闭合 R1/R2 的 §16.3 (d)） --------------------------
class RealArchiveClosureTest(unittest.TestCase):
    """只读；不写任何工件、不创建 `runtime/dist-data/`、不消耗任何 ID。"""

    def setUp(self) -> None:
        if not (PROJECT_ROOT / PROBE_BASELINE).exists():
            self.skipTest("真实归档不在本工作副本中")

    def _images(self) -> list[str]:
        found: list[str] = []
        for root in roots.ENUMERATION_ROOTS:
            base = PROJECT_ROOT / root
            if not base.exists():
                continue
            for path in base.rglob("*.jpg"):
                relative = path.relative_to(PROJECT_ROOT).as_posix()
                if not roots.is_root_excluded(relative):
                    found.append(relative)
        return found

    def test_zero_unmatched_and_zero_multi_matched_jpg(self) -> None:
        """裁定要求 dry-run 报告 zero-match = 0、multi-match = 0。"""
        zero: list[str] = []
        multi: list[str] = []
        for relative in self._images():
            matches = [
                entry
                for entry in roots.matching_entries(relative)
                if entry.kind == roots.KIND_IMAGE
            ]
            if not matches:
                zero.append(relative)
            elif len(matches) > 1:
                multi.append(relative)
        self.assertEqual(zero[:5], [], f"zero-match {len(zero)}")
        self.assertEqual(multi[:5], [], f"multi-match {len(multi)}")

    def test_probe_and_preview_pattern_counts_are_107_107_1(self) -> None:
        expected = {
            f"{PROBE_BASELINE}/*.jpg": 107,
            f"{PROBE_CANDIDATE}/*.jpg": 107,
            f"{RS3_FRAMES}/init-box-preview.jpg": 1,
        }
        images = self._images()
        for pattern, count in expected.items():
            regex = re.compile(roots.glob_to_regex(pattern))
            self.assertEqual(
                sum(1 for relative in images if regex.match(relative)), count, pattern
            )

    def test_rs3_sibling_frames_still_number_173(self) -> None:
        regex = re.compile(roots.glob_to_regex(f"{RS3_FRAMES}/frame_*.jpg"))
        self.assertEqual(sum(1 for relative in self._images() if regex.match(relative)), 173)

    def test_arm_a_truth_patterns_cover_exactly_five_files(self) -> None:
        """「合计恰五份」不能靠枚举断言自证，必须显式计数。"""
        found = sorted(
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in (PROJECT_ROOT / "runtime" / "runs").glob("*/m3_body_truth.jsonl")
        )
        valid = [
            relative
            for relative in found
            if any(
                entry.kind == roots.KIND_TRUTH and entry.usage_class == "VALID_FORMAL"
                for entry in roots.matching_entries(relative)
            )
            and "arm-a" in relative
        ]
        self.assertEqual(valid, sorted(ARM_A_VALID_TRUTH))

    def test_void_run_truth_pattern_matches_exactly_one_file(self) -> None:
        """`trial-1-void-attempt-3-hold` 没有 truth 文件，所以是 1 不是 2。"""
        regex = re.compile(
            roots.glob_to_regex(
                "runtime/runs/p1-m3-body-001-arm-a-trial-*-void-attempt-*-hold/m3_body_truth.jsonl"
            )
        )
        found = sorted(
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in (PROJECT_ROOT / "runtime" / "runs").glob("*/m3_body_truth.jsonl")
            if regex.match(path.relative_to(PROJECT_ROOT).as_posix())
        )
        self.assertEqual(found, [ARM_A_VOID_RUN_TRUTH])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
