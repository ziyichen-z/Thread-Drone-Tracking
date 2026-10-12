"""复核轮 1 的十条 finding + 接受轮 8 的 BC-DATA-13…19 具名回归。

裁定：`docs/proposals/P1-VLM-DATA-001-grounding-data-foundation.md` §20
（Acceptance consumption of Review round 1）；finding 原文见
`docs/reviews/P1-VLM-DATA-001.md` Round 1。

§20.3 点名的十六条回归全部在此，命名逐字一致。F1 组的 fixture **消费归档
真实字节副本**（按真实相对路径复制进临时根），不手写 JSON 状态。
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import (  # noqa: E402
    audit_tool,
    bind_layout,
    build_catalog,
    contract,
    g0_report,
    gen_mother_templates,
    make_splits,
    project_boxes,
    tier1_lang,
)

SO = tier1_lang.SceneObject

SCENE004_PROVIDER = "runtime/scenario_config.p1-scene-004.hold.json"
SCOUT4_MANIFEST = "runtime/p1-scene-004-scouting/p1-scene-004-scout-4/manifest.json"
SCOUT4_FRAMES = "runtime/test-results/p1-scene-004-scout-4-closed-exchange/frames"
M3_RUN = "runtime/runs/p1-m3-body-001-arm-a-trial-3"
M3_ARCHIVE_FRAMES = (
    "runtime/test-results/p1-m3-body-001-arm-a-trial-3-post-run/frames"
)
RATE_UNITS = (
    "runtime/test-results/ut-p1-m2-rate-002-b2-formal/r20-follow-1/pass",
    "runtime/test-results/ut-p1-m2-rate-002-002-batch-b-integration/release-attempt",
)


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


def body(name: str, x: float, z: float, half: float = 1.0, height: float = 2.0) -> dict:
    return {
        "scene_object_name": name,
        "min_x_m": x - half,
        "max_x_m": x + half,
        "min_y_m": 0.0,
        "max_y_m": height,
        "min_z_m": z - half,
        "max_z_m": z + half,
    }


class ArchiveCopyCase(unittest.TestCase):
    """把归档真实字节按原相对路径复制进临时根（workflow §4.4）。"""

    def setUp(self) -> None:
        if not (PROJECT_ROOT / SCENE004_PROVIDER).exists():
            self.skipTest("真实归档不在本工作副本中")
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def copy(self, relative: str) -> Path:
        source = PROJECT_ROOT / relative
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return target

    def place_frame(self, frames_dir: str, source_frames_dir: str) -> str:
        """复制归档里的第一张真实帧及其 sidecar。"""
        source = sorted((PROJECT_ROOT / source_frames_dir).glob("frame_*.jpg"))[0]
        target_dir = self.root / frames_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_dir / source.name)
        sidecar = source.with_suffix(".json")
        if sidecar.exists():
            shutil.copy2(sidecar, (target_dir / source.name).with_suffix(".json"))
        return f"{frames_dir}/{source.name}"

    def providers(self) -> dict[str, list[str]]:
        return bind_layout.build_provider_index(self.root)


# --- F1 / BC-DATA-13：source unit + scenario partition --------------------
class ScenarioBindingTest(ArchiveCopyCase):
    def test_scout4_family_binds_via_family_manifest(self) -> None:
        """A.2 的 source unit 经族 manifest + 点名 provider 绑定，不因非祖先而退出。"""
        frame = self.place_frame(SCOUT4_FRAMES, SCOUT4_FRAMES)
        self.copy(SCOUT4_MANIFEST)
        self.copy(SCENE004_PROVIDER)
        resolution = bind_layout.resolve_frame_scenario(
            self.root, frame, self.providers()
        )
        self.assertEqual(resolution["status"], bind_layout.BINDING_BOUND, resolution)
        self.assertTrue(resolution["sha256"].startswith("00c8802a"), resolution)

    def test_m3_armA_family_binds_via_run_snapshot(self) -> None:
        """m3 post-run 归档经附录 A root 模板映射到对应 run 的内嵌快照。"""
        frame = self.place_frame(M3_ARCHIVE_FRAMES, M3_ARCHIVE_FRAMES)
        self.copy(f"{M3_RUN}/scenario.json")
        self.copy(f"{M3_RUN}/manifest.json")
        resolution = bind_layout.resolve_frame_scenario(
            self.root, frame, self.providers()
        )
        self.assertEqual(resolution["status"], bind_layout.BINDING_BOUND, resolution)
        self.assertTrue(resolution["sha256"].startswith("f9c92052"), resolution)

    def test_rate_family_partitions_by_scenario_sha(self) -> None:
        """同一 family 的多个合法 SHA 保留为多个 partition，不得整族退出。"""
        records = []
        for index, unit in enumerate(RATE_UNITS):
            frame = self.place_frame(f"{unit}/frames", f"{unit}/frames")
            self.copy(f"{unit}/scenario_config.json")
            records.append(
                {
                    "path": frame,
                    "kind": "image",
                    "family": "rate",
                    "layout_class": "default",
                    "decision": "INCLUDED",
                }
            )
        payload = {"records": records}
        families = bind_layout.bind_families(self.root, payload)
        partitions = families["rate"]["partitions"]
        self.assertGreaterEqual(len(partitions), 2, partitions)
        self.assertNotEqual(
            families["rate"]["binding_status"], bind_layout.BINDING_UNBOUND
        )
        for partition in partitions:
            self.assertEqual(partition["binding_status"], bind_layout.BINDING_BOUND)

    def test_ambiguous_manifest_hard_fails_without_parent_fallback(self) -> None:
        """单 manifest 内多个互异 SHA 是歧义硬失败，不得跳过继续父级搜索。"""
        frame = self.place_frame("runtime/runs/demo-unit/frames", M3_ARCHIVE_FRAMES)
        # 歧义 manifest 放在**更近**的一层（帧所在目录）。
        (self.root / "runtime/runs/demo-unit/frames/manifest.json").write_text(
            json.dumps(
                {
                    "a": {"scenario_config_sha256": "a" * 64},
                    "b": {"scenario_config_sha256": "b" * 64},
                }
            ),
            encoding="utf-8",
        )
        # **真祖先**（source unit 自身）放一份合法快照：绝不能掩盖更近的歧义。
        # 早先这条用的是兄弟目录，根本走不到该分支，等于没验证过。
        shutil.copy2(
            PROJECT_ROOT / M3_RUN / "scenario.json",
            self.root / "runtime/runs/demo-unit/scenario.json",
        )
        with self.assertRaises(bind_layout.LayoutError):
            bind_layout.resolve_frame_scenario(self.root, frame, self.providers())


# --- F2 / BC-DATA-16：遮挡几何域与语言对象域分离 --------------------------
class OccluderLanguageDomainTest(unittest.TestCase):
    def _entry(self, bodies):
        frame = build_catalog.FrameInput(
            frame_id="f1",
            sidecar=make_sidecar(),
            family="fam",
            layout_class="default",
            usage_class="VALID_FORMAL",
            layout_binding_valid=True,
            sidecar_complete=True,
            truth_schema=None,
        )
        return build_catalog.build_frame_entry(frame, bodies, [], (1.0, 1.0, 1.0))

    def test_non_vehicle_occluder_never_enters_language_domain(self) -> None:
        bodies = [
            body("Vehicle_Taxi", 0.0, 20.0),
            body("Building Sky_big_color01", 6.0, 24.0, half=3.0, height=20.0),
        ]
        entry = self._entry(bodies)
        self.assertNotIn("Building Sky_big_color01", entry["blocking"])
        self.assertNotIn("Building Sky_big_color01", entry["referable"])
        exposure = {o["object_id"]: o.get("exposure") for o in entry["objects"]}
        self.assertNotIn(exposure.get("Building Sky_big_color01"), ("referent", "distractor"))
        self.assertIn("Vehicle_Taxi", entry["referable"])

    def test_lone_vehicle_stays_unique_despite_a_visible_building(self) -> None:
        bodies = [
            body("Vehicle_Taxi", 0.0, 20.0),
            body("Building Sky_big_color01", 8.0, 26.0, half=3.0, height=20.0),
        ]
        entry = self._entry(bodies)
        catalog = {
            "objects": {
                "Vehicle_Taxi": {
                    "object_id": "Vehicle_Taxi",
                    "class": "taxi",
                    "class_verified": True,
                    "group_key": "Vehicle_Taxi|",
                    "color": None,
                    "color_status": "UNVERIFIED",
                }
            }
        }
        world = build_catalog.frame_world(entry, catalog)
        self.assertEqual(
            build_catalog.minimal_program(world, "Vehicle_Taxi", catalog),
            {"target": {"class": "taxi"}},
        )

    def test_building_still_occludes_a_vehicle(self) -> None:
        """建筑退出语言域，但必须仍参与画家序遮挡。"""
        bodies = [
            body("Vehicle_Taxi", 0.0, 40.0),
            body("Building Sky_big_color01", 0.0, 6.0, half=6.0, height=20.0),
        ]
        entry = self._entry(bodies)
        status = {o["object_id"]: o["status"] for o in entry["objects"]}
        self.assertEqual(status["Vehicle_Taxi"], "EXCLUDED_OCCLUDED")

    def test_malformed_truth_without_visibility_evidence_is_target_unbounded(self) -> None:
        """缺 join、或既无可见性证据又无可用框 → 未知，不是不可见。"""
        camera = project_boxes.Camera.from_sidecar(make_sidecar())
        row = {"schema_version": "p1-m3-body-truth/v2", "frame_id": 7}
        _, unbounded = build_catalog.target_blocker_from_truth(row, "m3", camera)
        self.assertTrue(unbounded)


# --- F3 / F4 / BC-DATA-17：ref 字段验证与留出禁令两侧对称 -----------------
class ReferenceSymmetryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.unverified_car = SO("Vehicle_Car_color02", "car", None, True, center_px=(100.0, 100.0))
        self.blue_car = SO("Vehicle_Car_color01", "car", "blue", True, center_px=(200.0, 100.0))
        self.taxi_a = SO("Vehicle_Taxi", "taxi", None, True, center_px=(400.0, 100.0))
        self.taxi_b = SO("Vehicle_Taxi (1)", "taxi", None, True, center_px=(500.0, 100.0))
        self.domain = [self.unverified_car, self.blue_car, self.taxi_a, self.taxi_b]
        self.world = build_catalog.FrameWorld("f", self.domain)

    def test_unverified_ref_color_cannot_resolve_or_enumerate(self) -> None:
        self.assertIsNone(
            tier1_lang._resolve_ref(self.domain, {"class": "car", "color": "red"})
        )
        # 该域内任何 spec 都至少被两个对象通配冲突 → 枚举必须为空。
        # （早先这里是对空列表的循环，恒真、等于没断言。）
        self.assertEqual(build_catalog._unique_reference_specs(self.world), [])

        # 非空对照：颜色已验证的 bus 可枚举，颜色 UNVERIFIED 的 car 只能以
        # 无色 `car` 出现，绝不能被枚举成任意颜色词。
        control = [
            SO("Vehicle_Car_color02", "car", None, True),
            SO("Vehicle_Bus_color01", "bus", "blue", True),
        ]
        specs = build_catalog._unique_reference_specs(
            build_catalog.FrameWorld("control", control)
        )
        self.assertIn({"class": "bus", "color": "blue"}, specs)
        self.assertIn({"class": "car"}, specs)
        for spec in specs:
            colour = spec.get("color")
            if colour is None:
                continue
            resolved = tier1_lang._resolve_ref(control, spec)
            self.assertIsNotNone(resolved, spec)
            self.assertEqual(resolved.color_word, colour, spec)
        self.assertFalse(
            [s for s in specs if s["class"] == "car" and s.get("color")],
            "UNVERIFIED 的 car 不得被枚举成任何颜色 ref",
        )

    def test_verified_ref_color_resolves_when_no_unverified_peer_blocks_it(self) -> None:
        """已验证颜色仍可作 ref——前提是没有 UNVERIFIED 同类在旁通配阻断。"""
        domain = [self.blue_car, self.taxi_a, self.taxi_b]
        resolved = tier1_lang._resolve_ref(domain, {"class": "car", "color": "blue"})
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.object_id, "Vehicle_Car_color01")

    def test_unverified_peer_still_blocks_a_verified_colour_ref(self) -> None:
        """BC-DATA-17：`UNVERIFIED` 仍按未知通配**阻断唯一性**（分母不变）。"""
        self.assertIsNone(
            tier1_lang._resolve_ref(self.domain, {"class": "car", "color": "blue"})
        )

    def test_held_out_reference_is_rejected_and_persisted(self) -> None:
        """train/dev 表达若 resolved ref 是留出物体，必须硬拒绝。"""
        triple = {
            "candidate_id": "f|Vehicle_Taxi",
            "frame_id": "f",
            "object_id": "Vehicle_Taxi",
            "split": make_splits.SPLIT_TRAIN,
            "atom_id": "atom-1",
            "usage_class": "VALID_FORMAL",
            "program": {
                "target": {"class": "taxi"},
                "relation": {"type": "nearest_to", "ref": {"class": "bus"}},
            },
            "amodal_box_norm_xywh": [0.0, 0.0, 0.1, 0.1],
            "train_augment_only": False,
            "held_out_object": False,
            "held_out_reference": True,
            "resolved_reference_object_id": "Vehicle_Bus_color01",
            "floor_eligible": True,
            "station_key": "1:1:1:1",
        }
        mother = {"stage": 8, "triples": [triple], "count": 1}
        with self.assertRaises(gen_mother_templates.MotherSetError):
            gen_mother_templates.build_template_expressions(mother)

    def test_leakage_assertion_checks_the_reference_side(self) -> None:
        with self.assertRaises(make_splits.SplitError):
            make_splits.assert_held_out_never_referenced(
                ["Vehicle_Bus_color01"],
                [
                    {
                        "object_id": "Vehicle_Taxi",
                        "resolved_reference_object_id": "Vehicle_Bus_color01",
                    }
                ],
            )

    def test_candidate_freezes_the_resolved_reference(self) -> None:
        bus = SO("Vehicle_Bus_color01", "bus", None, True, world_xz=(1.0, 0.0))
        near = SO("Vehicle_Taxi", "taxi", None, True, world_xz=(2.0, 0.0))
        far = SO("Vehicle_Taxi (1)", "taxi", None, True, world_xz=(90.0, 0.0))
        world = build_catalog.FrameWorld("f", [bus, near, far])
        catalog = {
            "objects": {
                name: {
                    "object_id": name,
                    "class": contract.class_for_scene_object(name),
                    "class_verified": True,
                    "group_key": contract.color_group_key(name),
                    "color": None,
                    "color_status": "UNVERIFIED",
                }
                for name in ("Vehicle_Bus_color01", "Vehicle_Taxi", "Vehicle_Taxi (1)")
            }
        }
        program, reference = build_catalog.minimal_program_with_reference(
            world, "Vehicle_Taxi", catalog
        )
        self.assertIsNotNone(program)
        self.assertEqual(reference, "Vehicle_Bus_color01")


# --- F5 / BC-DATA-18：removal 与布局前提继续 fail-closed ------------------
class RemovalFailClosedTest(unittest.TestCase):
    def test_neighbor_cannot_suppress_default_removal_phantom(self) -> None:
        """邻居落在类内半对角线内不得冒充被移除实例（容差只用条目自带值）。"""
        instances = [body("Vehicle_Taxi", 2.0, 0.0, half=1.5)]
        entry = {
            "prefab_name": "Vehicle_Taxi",
            "original_xz_m": {"x": 0.0, "z": 0.0},
            "match_tolerance_m": 0.1,
            "remove_from_scene": True,
        }
        _, phantoms = bind_layout.unadjusted_base(instances, [entry])
        self.assertEqual(len(phantoms), 1, phantoms)
        self.assertEqual(phantoms[0]["prefab_name"], "Vehicle_Taxi")

    def test_exact_removal_match_still_suppresses_the_phantom(self) -> None:
        instances = [body("Vehicle_Taxi", 0.0, 0.0, half=1.5)]
        entry = {
            "prefab_name": "Vehicle_Taxi",
            "original_xz_m": {"x": 0.0, "z": 0.0},
            "match_tolerance_m": 0.1,
            "remove_from_scene": True,
        }
        _, phantoms = bind_layout.unadjusted_base(instances, [entry])
        self.assertEqual(phantoms, [])

    def test_default_divergence_cannot_seed_other_layout(self) -> None:
        """default 逆施前提不可证时，不得从字典序首个文档派生其他 partition。"""
        self.assertTrue(
            hasattr(bind_layout, "default_inverse_premise"),
            "需要一个以基础几何 source_scenario_sha256 为唯一来源的前提解析器",
        )
        with self.assertRaises(bind_layout.LayoutError):
            bind_layout.default_inverse_premise({}, "0" * 64)


# --- F6 / F7 / BC-DATA-19：dropped、splits 与 S8 单位 ---------------------
class DroppedAndSplitsTest(unittest.TestCase):
    def _candidate(self, frame: str) -> dict:
        return {
            "frame_id": frame,
            "object_id": "Vehicle_Taxi",
            "program": {"target": {"class": "taxi"}},
            "program_kind": "attribute",
            "usage_class": "SMOKE",
            "family": "rate",
            "layout_class": "default",
            "station_key": "1:1:1:1",
            "floor_usage": False,
            "pre_split_floor_eligible": False,
        }

    def test_dropped_frame_candidate_freezes_with_dropped_marker(self) -> None:
        frozen = g0_report.freeze_mother_candidates(
            [self._candidate("dropped-frame")],
            {},  # 该帧被连带规则整体退出，不入任何 split
            {"dropped-frame": "atom-1"},
            [],
            dropped_frames={"dropped-frame"},
        )
        item = frozen["candidates"][0]
        self.assertEqual(item["split"], "dropped")
        self.assertFalse(item["floor_eligible"])
        self.assertIn("dropped", item.get("split_reason", "").lower())

    def test_unknown_split_without_dropped_marker_still_hard_fails(self) -> None:
        with self.assertRaises(g0_report.GateError):
            g0_report.freeze_mother_candidates(
                [self._candidate("mystery-frame")], {}, {"mystery-frame": "atom-1"}, []
            )

    def test_splits_persist_sample_roles_and_four_way_exposure(self) -> None:
        atoms = [
            make_splits.AtomSummary(
                atom_id=make_splits.atom_id_for([name]),
                families=[name],
                layout_classes=[layout],
                floor_eligible_frames=[f"{name}/f0", f"{name}/f1"],
            )
            for name, layout in (("famA", "default"), ("famB", "scene-004"))
        ]
        # 角色由 S4 内部从 catalog 记录派生（复核轮 2 F11），调用方只交记录。
        entries = [
            {
                "frame_id": "famA/f0",
                "objects": [{"object_id": "Vehicle_Taxi", "exposure": "referent"}],
            },
            {
                "frame_id": "famB/f0",
                "objects": [{"object_id": "Vehicle_Taxi", "exposure": "distractor"}],
            },
        ]
        payload = make_splits.assign_splits(atoms, entries)
        self.assertIn("sample_roles", payload)
        self.assertIn("exposure_matrix", payload)
        self.assertTrue(payload["sample_roles"])
        for record in payload["sample_roles"]:
            self.assertIn(record["split"], make_splits.SPLITS)
        self.assertIn("Vehicle_Taxi", payload["exposure_matrix"]["per_object"])


class S8UnitTest(unittest.TestCase):
    def test_s8_unit_count_is_object_station_not_object_frame(self) -> None:
        triples = [
            {
                "candidate_id": f"f{i}|Vehicle_Taxi",
                "frame_id": f"f{i}",
                "object_id": "Vehicle_Taxi",
                "split": make_splits.SPLIT_TRAIN,
                "atom_id": "atom-1",
                "usage_class": "VALID_FORMAL",
                "program": {"target": {"class": "taxi"}},
                "amodal_box_norm_xywh": [0.0, 0.0, 0.1, 0.1],
                "train_augment_only": False,
                "held_out_object": False,
                "held_out_reference": False,
                "resolved_reference_object_id": None,
                "floor_eligible": True,
                "station_key": "1:1:1:1",
            }
            for i in range(4)
        ]
        statistics = gen_mother_templates.cluster_statistics({"triples": triples})
        # 四帧同一 (对象, 站位簇) → §5.1 属性唯一单元恰 1，不是 4。
        self.assertEqual(statistics["per_split"][make_splits.SPLIT_TRAIN]["unit_count"], 1)


# --- F8 / F9 / BC-DATA-14 / BC-DATA-15 ------------------------------------
class FrozenFormulaTest(unittest.TestCase):
    def test_audit_panel_key_uses_frozen_slash_separator(self) -> None:
        """BC-DATA-14：`SHA-256(UTF8(seed) ‖ UTF8("/") ‖ UTF8(sample_id))`。"""
        import hashlib

        seed = audit_tool.panel_seed("A2", 1)
        expected = hashlib.sha256(
            seed.encode("utf-8") + b"/" + "sample-x".encode("utf-8")
        ).digest()
        self.assertEqual(audit_tool.sample_sort_key("A2", 1, "sample-x")[0], expected)

    def test_painter_order_uses_camera_forward_depth(self) -> None:
        """构造 z 序与欧氏序相反的两体：画家序必须按前向深度。"""
        camera = project_boxes.Camera.from_sidecar(make_sidecar())
        # A：z 深 10、横向 0；B：z 深 12、横向 40（欧氏更远但 z 也更远）→
        # 反转：A z=14 横向 0（欧氏 14），B z=12 横向 40（欧氏 41.8）。
        near_in_z = body("Vehicle_Bus_color01", 40.0, 12.0, half=1.0)
        far_in_z = body("Vehicle_Taxi", 0.0, 14.0, half=1.0)
        projected = project_boxes.project_instances(camera, [near_in_z, far_in_z])
        depths = {p.object_id: p.camera_depth_m for p in projected}
        self.assertLess(depths["Vehicle_Bus_color01"], depths["Vehicle_Taxi"])
        self.assertAlmostEqual(depths["Vehicle_Bus_color01"], 12.0, places=6)

    def test_color_and_audit_distance_use_camera_forward_depth(self) -> None:
        self.assertTrue(hasattr(build_catalog, "camera_forward_depth"))
        camera = project_boxes.Camera.from_sidecar(make_sidecar())
        depth = build_catalog.camera_forward_depth(camera, body("Vehicle_Taxi", 40.0, 12.0))
        self.assertAlmostEqual(depth, 12.0, places=6)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
