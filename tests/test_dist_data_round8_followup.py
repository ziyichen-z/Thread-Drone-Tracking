"""实现侧自查（候选 4 提交后）：四条阻断缺陷的回归。

来源不是 §20.3 的点名清单，而是本角色在提交候选 4 后自跑的独立核验——四条
都已用生产路径实测复现，性质与复核 F1 同类：**成员/分支存在不等于它在生产
路径上真的生效**。

1. `default_inverse_premise` 把唯一性判在**路径条数**上，真实归档同一 sha 有
   12 条同字节副本 → `build_layout` 在 partition 循环前直接崩，S2 一个
   partition 也派生不出来；
2. BC-DATA-13 (v) 的歧义硬失败被**更远祖先**的合法快照掩盖（两趟遍历所致）；
3. `held_out_reference` 在 S4 由默认空集打标，S7 从不重新派生 → 留出物体作
   关系 ref 渲进训练表达文本；
4. `splits` 的 `sample_roles` / `exposure_matrix` 有成员名但无装配器，实际恒空。
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
    bind_layout,
    build_catalog,
    g0_report,
    gen_mother_templates,
    make_splits,
    project_boxes,
    tier1_lang,
)

SO = tier1_lang.SceneObject
M3_SNAPSHOT = "runtime/runs/p1-m3-body-001-arm-a-trial-3/scenario.json"


class DefaultPremiseTest(unittest.TestCase):
    """缺陷 1：唯一性必须判在字节上，不是路径条数。"""

    def test_premise_resolves_when_one_sha_has_many_identical_copies(self) -> None:
        provider_index = {"a" * 64: [f"runtime/runs/r{i}/scenario.json" for i in range(12)]}
        resolved = bind_layout.default_inverse_premise(provider_index, "a" * 64)
        self.assertEqual(resolved, "runtime/runs/r0/scenario.json")

    def test_premise_still_fails_closed_when_no_provider_exists(self) -> None:
        with self.assertRaises(bind_layout.LayoutError):
            bind_layout.default_inverse_premise({}, "0" * 64)

    def test_real_archive_premise_is_resolvable(self) -> None:
        """真实归档上必须可解析——这正是候选 4 从未测过的确定输出。"""
        if not (PROJECT_ROOT / M3_SNAPSHOT).exists():
            self.skipTest("真实归档不在本工作副本中")
        geometry = bind_layout.load_base_geometry(PROJECT_ROOT)
        providers = bind_layout.build_provider_index(PROJECT_ROOT)
        resolved = bind_layout.default_inverse_premise(
            providers, geometry["source_scenario_sha256"]
        )
        self.assertTrue(resolved)
        self.assertIn(
            geometry["source_scenario_sha256"], providers, "provider index 应含该 sha"
        )
        self.assertGreater(len(providers[geometry["source_scenario_sha256"]]), 1)


class AmbiguityNotMaskedTest(unittest.TestCase):
    """缺陷 2：更近的歧义 manifest 必须先于更远祖先的快照触发。"""

    def setUp(self) -> None:
        if not (PROJECT_ROOT / M3_SNAPSHOT).exists():
            self.skipTest("真实归档不在本工作副本中")
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_genuine_ancestor_snapshot_cannot_mask_a_nearer_ambiguous_manifest(
        self,
    ) -> None:
        frames = self.root / "runtime/runs/demo-parent/demo-unit/frames"
        frames.mkdir(parents=True)
        (frames / "frame_0.jpg").write_bytes(b"x")
        (self.root / "runtime/runs/demo-parent/demo-unit/manifest.json").write_text(
            json.dumps(
                {
                    "a": {"scenario_config_sha256": "a" * 64},
                    "b": {"scenario_config_sha256": "b" * 64},
                }
            ),
            encoding="utf-8",
        )
        # **真** 祖先（不是兄弟目录）放一份合法快照。
        shutil.copy2(
            PROJECT_ROOT / M3_SNAPSHOT,
            self.root / "runtime/runs/demo-parent/scenario.json",
        )
        with self.assertRaises(bind_layout.LayoutError):
            bind_layout.resolve_frame_scenario(
                self.root, "runtime/runs/demo-parent/demo-unit/frames/frame_0.jpg", {}
            )

    def test_search_does_not_escape_the_source_unit(self) -> None:
        """BC-DATA-13 (c)：只读自身归档树，祖先扫描不得越出 source unit。"""
        frames = self.root / "runtime/runs/demo-unit/frames"
        frames.mkdir(parents=True)
        (frames / "frame_0.jpg").write_bytes(b"x")
        # 越出 unit 的祖先处放一份合法快照——不得被采用。
        shutil.copy2(
            PROJECT_ROOT / M3_SNAPSHOT, self.root / "runtime/runs/scenario.json"
        )
        resolution = bind_layout.resolve_frame_scenario(
            self.root, "runtime/runs/demo-unit/frames/frame_0.jpg", {}
        )
        self.assertEqual(resolution["status"], bind_layout.BINDING_UNBOUND)

    def test_snapshot_inside_the_unit_subtree_is_read(self) -> None:
        """自身归档树包含子树：快照放在 unit 子目录里同样算。"""
        frames = self.root / "runtime/test-results/demo-unit/frames"
        frames.mkdir(parents=True)
        (frames / "frame_0.jpg").write_bytes(b"x")
        nested = self.root / "runtime/test-results/demo-unit/nested"
        nested.mkdir(parents=True)
        shutil.copy2(PROJECT_ROOT / M3_SNAPSHOT, nested / "scenario_config.json")
        resolution = bind_layout.resolve_frame_scenario(
            self.root, "runtime/test-results/demo-unit/frames/frame_0.jpg", {}
        )
        self.assertEqual(resolution["status"], bind_layout.BINDING_BOUND)
        self.assertEqual(resolution["source"], "unit_subtree_snapshot")


class HeldOutReferenceOnProductionPathTest(unittest.TestCase):
    """缺陷 3：留出禁令必须在**生产路径**上生效，不能依赖 S4 的可选参数。"""

    def _drive(self, held_out: list[str]):
        bus = SO("Vehicle_Bus_color01", "bus", None, True, world_xz=(1.0, 0.0))
        near = SO("Vehicle_Taxi", "taxi", None, True, world_xz=(2.0, 0.0))
        far = SO("Vehicle_Taxi (1)", "taxi", None, True, world_xz=(90.0, 0.0))
        world = build_catalog.FrameWorld("f", [bus, near, far])
        catalog = {
            "objects": {
                name: {
                    "object_id": name,
                    "class": "bus" if "Bus" in name else "taxi",
                    "class_verified": True,
                    "group_key": name,
                    "color": None,
                    "color_status": "UNVERIFIED",
                }
                for name in ("Vehicle_Bus_color01", "Vehicle_Taxi", "Vehicle_Taxi (1)")
            }
        }
        entry = {
            "frame_id": "f",
            "family": "fam",
            "layout_class": "default",
            "usage_class": "VALID_FORMAL",
            "layout_binding_valid": True,
            "sidecar_complete": True,
            "target_unbounded": False,
            "referable": ["Vehicle_Taxi"],
            "blocking": ["Vehicle_Taxi"],
            "station_bin": {"key": "1:1:1:1"},
        }
        # 生产驱动**不传** held_out（谓词该参数有默认值）——S7 必须自己派生。
        candidate = build_catalog.prospective_mother_eligible(
            entry, "Vehicle_Taxi", world, catalog
        )
        frozen = g0_report.freeze_mother_candidates(
            [candidate], {"f": "train"}, {"f": "atom-1"}, held_out
        )
        mother = gen_mother_templates.materialize_mother_set(
            frozen,
            {"gate": g0_report.GATE_OPEN, "unmet_floors": []},
            {frozen["candidates"][0]["candidate_id"]: [0.0, 0.0, 0.1, 0.1]},
        )
        return frozen, mother

    def test_held_out_reference_is_rederived_at_s7(self) -> None:
        frozen, _ = self._drive(["Vehicle_Bus_color01"])
        self.assertEqual(
            frozen["candidates"][0]["resolved_reference_object_id"],
            "Vehicle_Bus_color01",
        )
        self.assertTrue(frozen["candidates"][0]["held_out_reference"])

    def test_held_out_bus_never_reaches_a_training_expression(self) -> None:
        _, mother = self._drive(["Vehicle_Bus_color01"])
        with self.assertRaises(gen_mother_templates.MotherSetError):
            gen_mother_templates.build_template_expressions(mother)

    def test_a_non_held_out_reference_still_renders(self) -> None:
        _, mother = self._drive([])
        expressions = gen_mother_templates.build_template_expressions(mother)
        self.assertEqual(
            [item["expression"] for item in expressions["expressions"]],
            ["the taxi nearest to the bus"],
        )


class SplitsRolesAreActuallyPopulatedTest(unittest.TestCase):
    """缺陷 4：`splits` 的成员必须真被装配，不能只有成员名。"""

    def _entry(self, frame_id: str) -> dict:
        return {
            "frame_id": frame_id,
            "objects": [
                {"object_id": "Vehicle_Taxi", "exposure": "referent"},
                {"object_id": "Vehicle_Bus_color01", "exposure": "distractor"},
                {"object_id": "Building Sky_big_color01", "exposure": "occluder_only"},
            ],
        }

    def test_assembler_bridges_catalog_entries_to_roles(self) -> None:
        roles = make_splits.sample_roles_from_entries(
            [self._entry("A/f0"), self._entry("B/f0")]
        )
        self.assertEqual(len(roles), 4)  # 每帧 2 个语言域对象
        # BC-DATA-16：occluder_only 不进 exposure。
        self.assertNotIn(
            "Building Sky_big_color01", {item["object_id"] for item in roles}
        )

    def test_splits_payload_carries_populated_roles_and_exposure(self) -> None:
        atoms = [
            make_splits.AtomSummary(
                atom_id=make_splits.atom_id_for([name]),
                families=[name],
                layout_classes=[layout],
                floor_eligible_frames=[f"{name}/f0"],
            )
            for name, layout in (("A", "default"), ("B", "scene-004"))
        ]
        payload = make_splits.assign_splits(
            atoms, [self._entry("A/f0"), self._entry("B/f0")]
        )
        self.assertTrue(payload["sample_roles"], "sample_roles 不得为空")
        self.assertTrue(
            payload["exposure_matrix"]["per_object"], "exposure 汇总不得为空"
        )
        self.assertIn("Vehicle_Taxi", payload["exposure_matrix"]["per_object"])
        for record in payload["sample_roles"]:
            self.assertIn(record["split"], make_splits.SPLITS)


class TruthEvidenceValueTest(unittest.TestCase):
    """m3 可见性证据按**取值**判定，不是「键在不在」。"""

    CAMERA = project_boxes.Camera.from_sidecar(
        {
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
    )

    def _unbounded(self, row: dict) -> bool:
        return build_catalog.target_blocker_from_truth(row, "m3", self.CAMERA)[1]

    def test_null_valued_evidence_keys_are_unknown_not_invisible(self) -> None:
        self.assertTrue(
            self._unbounded({"intersects_frustum": None, "geometrically_visible": None})
        )

    def test_has_unoccluded_sample_counts_as_in_view_evidence(self) -> None:
        self.assertTrue(self._unbounded({"has_unoccluded_sample": True}))

    def test_all_evidence_false_is_genuinely_invisible(self) -> None:
        self.assertFalse(
            self._unbounded(
                {
                    "intersects_frustum": False,
                    "geometrically_visible": False,
                    "has_unoccluded_sample": False,
                }
            )
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
