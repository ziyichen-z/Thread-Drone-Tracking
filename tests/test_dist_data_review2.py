"""复核轮 2 的具名回归（`docs/reviews/P1-VLM-DATA-001.md` Round 2）。

本文件收 **F13** 与 **F12** 的具名回归；F11 的具名回归按复核原文落在唯一
端到端驱动 `tests/test_dist_data_pipeline.py`（断言管线自己的 splits 工件），
F14 是 `NOT_MECHANIZABLE` 的定点复看，无可写断言。

F13 与 round 1 的 F5(a) 完全同构：`unadjusted_base` 的逆施侧已按 BC-DATA-18
禁止「加类内半对角线让邻居冒充被移除实例」，但 `apply_layout` 的
`_self_removed`（正施侧）仍在用同一个被禁掉的容差，方向同样 fail-open——
邻居冒充自移除实例会静默吞掉 §2.3 (a) 必登记的 phantom。

F12 按接受轮 10 的 **BC-DATA-20**（提案 §22.2）闭合：BC-DATA-13 (b) 的
「任何已有 manifest/快照」检查域 = 该 source unit **自身归档子树**内任意深度的
`manifest.json` 与合格内嵌快照，根级/祖先/最近文件没有覆盖旁支矛盾的优先权；
任一显式证人不一致或不可读，(b) 关联即不成立，且不得再由 sidecar/点名 provider/
父级/邻居回退。夹具全部**消费归档真实字节**（按真实相对路径复制进临时根），
经生产入口 `resolve_frame_scenario` 求值，不手写 JSON 状态。
"""

from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import bind_layout, contract, roots  # noqa: E402

# A.2 点名 provider 与 scout-3 的真实 source unit（复核轮 2 F12 的原始现场）。
SCENE004_PROVIDER = "runtime/scenario_config.p1-scene-004.hold.json"
SCOUT3_UNIT = (
    "runtime/test-results/"
    "p1-scene-004-scout-3-protocol-invalid-same-id-retry-20260729"
)
SCOUT3_FRAMES = f"{SCOUT3_UNIT}/frames"
SCOUT3_NESTED_MANIFEST = f"{SCOUT3_UNIT}/session/manifest.json"
# 另一份**真实归档、字节不改写**、声明不同 scenario SHA 的 manifest。
FOREIGN_MANIFEST = "runtime/runs/rate20-calib/manifest.json"
# 另一份真实归档场景字节，SHA 与 A.2 provider 不同（用于子树快照矛盾）。
FOREIGN_SCENARIO = "config/scenario.default.json"


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


def removal(x: float, z: float, prefab: str = "Vehicle_Taxi", tolerance: float = 0.1) -> dict:
    return {
        "prefab_name": prefab,
        "original_xz_m": {"x": x, "z": z},
        "match_tolerance_m": tolerance,
        "remove_from_scene": True,
    }


class SelfRemovedToleranceTest(unittest.TestCase):
    """F13：`_self_removed` 只能用条目自带容差，不得再加类内半对角线。

    场景：`Vehicle_Taxi` 的一个实例在基础几何里位于 `(2, 0)`，default 字节
    声明在 `(0, 0)` 移除了**另一个** `Vehicle_Taxi` 实例。逆施侧按 BC-DATA-18
    只用条目容差 `0.1 m`，`(2, 0)` 的邻居不冒充 → `(0, 0)` 成为 phantom 候选。
    另一布局类随后移除 `(2, 0)` 的那个实例。两者相距 `2 m`：**大于**条目容差
    `0.1 m`、**小于**该 prefab 类的 XZ 半对角线 `2.121320 m`。
    """

    # 同类存活实例（不同 prefab 基名，故不参与 prefab 级匹配），只供 BC-DATA-11
    # 的包络证明；否则 phantom 构造会因「本布局类无同类存活实例」硬失败，
    # 掩盖本用例要测的取消判据。
    SURVIVOR = "Vehicle_Taxi_color02"

    def setUp(self) -> None:
        self.base_instances = [
            body("Vehicle_Taxi", 2.0, 0.0, half=1.5),
            body(self.SURVIVOR, 40.0, 40.0, half=1.0),
        ]
        self.unadjusted, self.phantom_candidates = bind_layout.unadjusted_base(
            self.base_instances, [removal(0.0, 0.0)]
        )

    def test_fixture_separation_is_between_entry_tolerance_and_half_diagonal(self) -> None:
        """夹具前提：2 m 落在「条目容差 < d < 类内半对角线」区间内。"""
        self.assertEqual(len(self.phantom_candidates), 1, self.phantom_candidates)
        half_diagonal = bind_layout.xz_half_diagonal(
            body("Vehicle_Taxi", 2.0, 0.0, half=1.5)
        )
        self.assertAlmostEqual(half_diagonal, 2.1213203435596424, places=9)
        self.assertLess(0.1, 2.0)
        self.assertLess(2.0, half_diagonal)
        self.assertEqual(contract.class_for_scene_object(self.SURVIVOR), "taxi")

    def test_neighbour_removal_cannot_cancel_phantom_registration(self) -> None:
        """布局类移除 `(2, 0)` 的邻居时，`(0, 0)` 的 phantom 必须仍然登记。"""
        derived = bind_layout.apply_layout(
            self.unadjusted, [removal(2.0, 0.0)], self.phantom_candidates
        )
        self.assertEqual(derived["removed"], ["Vehicle_Taxi"])
        self.assertEqual(
            len(derived["phantoms"]),
            1,
            "邻居实例被本布局类移除，不得取消另一位置的 phantom 登记（fail-open）",
        )
        phantom = derived["phantoms"][0]
        self.assertTrue(phantom["phantom"])
        self.assertEqual(phantom["class_word"], "taxi")
        self.assertAlmostEqual(
            (phantom["min_x_m"] + phantom["max_x_m"]) / 2.0, 0.0, places=9
        )
        self.assertAlmostEqual(
            (phantom["min_z_m"] + phantom["max_z_m"]) / 2.0, 0.0, places=9
        )

    def test_self_removal_at_the_same_original_still_cancels_the_phantom(self) -> None:
        """对照组：布局类移除的就是该 phantom 自身原位时，登记照常取消。"""
        derived = bind_layout.apply_layout(
            self.unadjusted, [removal(0.0, 0.0)], self.phantom_candidates
        )
        self.assertEqual(derived["phantoms"], [])


class ArchiveCopyCase(unittest.TestCase):
    """把归档真实字节按**原相对路径**复制进临时根（workflow §4.4 的 fixture 规则）。"""

    def setUp(self) -> None:
        for required in (SCENE004_PROVIDER, SCOUT3_NESTED_MANIFEST, FOREIGN_MANIFEST):
            if not (PROJECT_ROOT / required).exists():
                self.skipTest(f"真实归档不在本工作副本中：{required}")
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def copy(self, relative: str, destination: str | None = None) -> Path:
        """复制归档字节；`destination` 只改放置位置，**字节一行不改**。"""
        target = self.root / (destination or relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT_ROOT / relative, target)
        return target

    def place_frame(self) -> str:
        source = sorted((PROJECT_ROOT / SCOUT3_FRAMES).glob("frame_*.jpg"))[0]
        target_dir = self.root / SCOUT3_FRAMES
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_dir / source.name)
        shutil.copy2(
            source.with_suffix(".json"), (target_dir / source.name).with_suffix(".json")
        )
        return f"{SCOUT3_FRAMES}/{source.name}"

    def resolve(self, frame: str) -> dict:
        return bind_layout.resolve_frame_scenario(
            self.root, frame, bind_layout.build_provider_index(self.root)
        )


class A2SubtreeConsistencyTest(ArchiveCopyCase):
    """F12 / BC-DATA-20：A.2 一致性检查域 = 该 source unit 自身归档子树。"""

    def test_fixture_reproduces_the_reported_side_branch_position(self) -> None:
        """夹具前提：真实旁支 manifest 既非帧祖先、也不在 unit 根、也不是快照。"""
        self.assertEqual(roots.source_unit_for(self.place_frame()), SCOUT3_UNIT)
        self.assertIn(bind_layout._family_of_unit(SCOUT3_UNIT), roots.SCENE004_FAMILIES)
        self.assertTrue(SCOUT3_NESTED_MANIFEST.startswith(f"{SCOUT3_UNIT}/session/"))
        self.assertNotEqual(
            SCOUT3_NESTED_MANIFEST, f"{SCOUT3_UNIT}/{bind_layout.MANIFEST_NAME}"
        )
        self.assertIsNone(roots.associated_run_directory(SCOUT3_UNIT))

    def test_a2_nested_manifest_consistency_is_enforced_across_unit_subtree(self) -> None:
        """旁支 manifest 声明异 SHA 时 (b) 关联必须不成立；同 SHA 时照常 BOUND。"""
        frame = self.place_frame()
        self.copy(SCENE004_PROVIDER)

        # 正例：scout-3 自己的真实旁支 manifest，声明恰等于 provider 实测 SHA。
        self.copy(SCOUT3_NESTED_MANIFEST)
        positive = self.resolve(frame)
        self.assertEqual(positive["status"], bind_layout.BINDING_BOUND, positive)
        self.assertEqual(positive["source"], "appendix_a2_archive_provider", positive)
        self.assertTrue(positive["sha256"].startswith("00c8802a"), positive)

        # 负例：换成**另一份真实归档、字节不改写**、声明不同 SHA 的 manifest，
        # 放在同一个旁支位置。前置 `scenario_id` 仍由帧 sidecar 提供，所以
        # 走的是同一条 (b) 分支——差别只在这份显式证人。
        self.copy(FOREIGN_MANIFEST, destination=SCOUT3_NESTED_MANIFEST)
        negative = self.resolve(frame)
        self.assertEqual(negative["status"], bind_layout.BINDING_UNBOUND, negative)
        self.assertEqual(
            negative["path"], SCOUT3_NESTED_MANIFEST, "须点名矛盾的见证路径"
        )
        self.assertTrue(negative["sha256"].startswith("4bddb2f2"), negative)
        self.assertIn(SCOUT3_NESTED_MANIFEST, negative["witnesses"])
        self.assertEqual(negative["witnesses"], sorted(negative["witnesses"]))

    def test_a2_subtree_snapshot_conflict_is_not_hidden_by_the_provider(self) -> None:
        """子树内合格快照字节矛盾时，A.2 fallback 不得把矛盾掩盖成 BOUND。

        两份快照字节不同 → `_unit_subtree_snapshot` 返回 None（既有 fail-closed），
        随后落到 (b)；BC-DATA-20 之前这里会直接 BOUND，矛盾被关联结果吞掉。
        """
        frame = self.place_frame()
        self.copy(SCENE004_PROVIDER)
        self.copy(
            SCENE004_PROVIDER, destination=f"{SCOUT3_UNIT}/session/scenario_config.json"
        )
        self.copy(
            FOREIGN_SCENARIO, destination=f"{SCOUT3_UNIT}/session-2/scenario_config.json"
        )
        self.assertIsNone(
            bind_layout._unit_subtree_snapshot(self.root, SCOUT3_UNIT),
            "夹具前提：子树快照字节不唯一，既有实现在此返回 None",
        )
        resolution = self.resolve(frame)
        self.assertEqual(
            resolution["status"],
            bind_layout.BINDING_UNBOUND,
            "子树快照矛盾不得被 A.2 点名 provider 掩盖",
        )
        self.assertEqual(
            resolution["path"], f"{SCOUT3_UNIT}/session-2/scenario_config.json"
        )

    def test_a2_unreadable_subtree_manifest_blocks_the_association(self) -> None:
        """§22.2 (4)：域内 manifest 不可读/不可解析同样使 (b) 关联不成立。

        用归档里的**真实 JPEG 字节**（一字节不改）占住那个 manifest 路径，
        `json.loads` 必然失败——不手写损坏的 JSON。
        """
        frame = self.place_frame()
        self.copy(SCENE004_PROVIDER)
        source = sorted((PROJECT_ROOT / SCOUT3_FRAMES).glob("frame_*.jpg"))[0]
        self.copy(
            source.relative_to(PROJECT_ROOT).as_posix(),
            destination=SCOUT3_NESTED_MANIFEST,
        )
        resolution = self.resolve(frame)
        self.assertEqual(resolution["status"], bind_layout.BINDING_UNBOUND, resolution)
        self.assertEqual(
            resolution["source"], "appendix_a2_subtree_manifest_unreadable", resolution
        )
        self.assertIsNone(resolution["sha256"])

    def test_a2_association_survives_when_the_subtree_has_no_explicit_witness(self) -> None:
        """对照组：域内无显式证人时，(b) 关联照常成立（§22.2 (5) 不放宽成功条件）。"""
        frame = self.place_frame()
        self.copy(SCENE004_PROVIDER)
        resolution = self.resolve(frame)
        self.assertEqual(resolution["status"], bind_layout.BINDING_BOUND, resolution)
        self.assertEqual(resolution["source"], "appendix_a2_archive_provider")

    def test_a2_consistency_domain_stops_at_the_source_unit(self) -> None:
        """对照组：兄弟 unit 的矛盾 manifest 不进本 unit 的检查域（不扩成全仓扫描）。"""
        frame = self.place_frame()
        self.copy(SCENE004_PROVIDER)
        self.copy(SCOUT3_NESTED_MANIFEST)
        self.copy(
            FOREIGN_MANIFEST,
            destination=f"{SCOUT3_UNIT}-sibling-unit/session/manifest.json",
        )
        resolution = self.resolve(frame)
        self.assertEqual(resolution["status"], bind_layout.BINDING_BOUND, resolution)
        self.assertEqual(resolution["source"], "appendix_a2_archive_provider")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
