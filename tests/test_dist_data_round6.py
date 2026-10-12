"""接受轮 6 的具名回归（BC-DATA-10 / BC-DATA-11 / BC-DATA-12）。

裁定：`docs/proposals/P1-VLM-DATA-001-grounding-data-foundation.md` §18
（`STOP_POINT_NOT_CONFIRMED / IMPLEMENTATION_REWORK_REQUIRED`，2026-08-26）。

轮 6 驳回了实现侧「潜伏、当前不触发」的降格提议：三项都违反 §2.3 的
same-class proxy 与归档字节 fail-closed 合同，**不能因今天的归档恰未触发而
降格为停点后风险**。

§18.3 (b) 点名的五条分支，逐条对应一个测试类：

1. unknown-class phantom 硬失败                  → `UnknownClassPhantomTest`
2. known-class 空集合硬失败                       → `EmptySameClassPhantomTest`
3. 根级可变 config 单独存在时仍 unbound           → `MutableRootConfigTest`
4. 可变 config 与有效 manifest 同时存在时走 manifest → `MutableRootConfigTest`
5. 合法 run 内嵌快照仍优先                        → `LegitimateSnapshotTest`
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import bind_layout, roots  # noqa: E402

SHA_A = "a" * 64


def instance(name: str, x: float = 0.0, z: float = 0.0, size: float = 1.0) -> dict:
    return {
        "scene_object_name": name,
        "min_x_m": x - size,
        "max_x_m": x + size,
        "min_y_m": 0.0,
        "max_y_m": 2.0 * size,
        "min_z_m": z - size,
        "max_z_m": z + size,
    }


def phantom_candidate(prefab: str, x: float = 50.0, z: float = 50.0) -> dict:
    return {"prefab_name": prefab, "original_xz_m": {"x": x, "z": z}}


# --- BC-DATA-10：未知类别的 phantom 必须在代理构造前硬失败 -----------------
class UnknownClassPhantomTest(unittest.TestCase):
    """分支 1。缺口：`None == None` 的同类筛选会把 building/prop 当同类。"""

    def test_unknown_class_phantom_raises_before_any_proxy_is_built(self) -> None:
        # 场景里只有非车辆实例：它们的 class 也是 None，旧实现会把它们当「同类」。
        instances = [
            instance("Building Sky_big_color01", size=12.0),
            instance("Tree_color02 (3)", size=6.0),
        ]
        with self.assertRaises(bind_layout.LayoutError) as caught:
            bind_layout.apply_layout(
                instances, [], [phantom_candidate("Prop_TrafficCone")]
            )
        self.assertIn("Prop_TrafficCone", str(caught.exception))

    def test_no_building_sized_envelope_is_ever_borrowed(self) -> None:
        """缺口的直接症状：旧实现会产出一个 12 m 半长的「车辆」代理。"""
        instances = [instance("Building Sky_big_color01", size=12.0)]
        try:
            derived = bind_layout.apply_layout(
                instances, [], [phantom_candidate("Prop_TrafficCone")]
            )
        except bind_layout.LayoutError:
            return  # 合同要求的行为
        self.fail(
            "未知类别的 phantom 必须硬失败，实测却产出了代理："
            f"{[p['scene_object_name'] for p in derived['phantoms']]}"
        )

    def test_known_class_phantom_still_works(self) -> None:
        """修复不得把正常路径一起封死。"""
        instances = [instance("Vehicle_Container_color01", size=2.0)]
        derived = bind_layout.apply_layout(
            instances, [], [phantom_candidate("Vehicle_Container_color02")]
        )
        self.assertEqual(len(derived["phantoms"]), 1)
        proxy = derived["phantoms"][0]
        self.assertEqual(proxy["class_word"], "container truck")
        self.assertAlmostEqual(proxy["max_x_m"] - proxy["min_x_m"], 4.0)


# --- BC-DATA-11：类别已知但同类实例为空同样硬失败 -------------------------
class EmptySameClassPhantomTest(unittest.TestCase):
    """分支 2。缺口：三个半长置 0 不是 fail-closed，必须删除。"""

    def test_known_class_without_surviving_instance_raises(self) -> None:
        instances = [instance("Vehicle_Taxi", size=2.0)]  # 场内没有任何 container truck
        with self.assertRaises(bind_layout.LayoutError) as caught:
            bind_layout.apply_layout(
                instances, [], [phantom_candidate("Vehicle_Container_color02")]
            )
        message = str(caught.exception)
        self.assertIn("container truck", message)

    def test_zero_volume_proxy_is_never_produced(self) -> None:
        """零面积体不得继续参与遮挡、唯一性或 F 计算。"""
        instances = [instance("Vehicle_Taxi", size=2.0)]
        try:
            derived = bind_layout.apply_layout(
                instances, [], [phantom_candidate("Vehicle_Container_color02")]
            )
        except bind_layout.LayoutError:
            return
        degenerate = [
            p
            for p in derived["phantoms"]
            if p["max_x_m"] - p["min_x_m"] == 0.0 or p["max_z_m"] - p["min_z_m"] == 0.0
        ]
        self.fail(f"同类为空时必须硬失败，实测产出了零体积代理：{degenerate}")

    def test_envelope_uses_per_axis_max_of_surviving_instances(self) -> None:
        """代理尺寸只允许来自该冻结类别在目标布局中**仍存在**实例的逐轴最大半长。"""
        instances = [
            instance("Vehicle_Container_color01", x=0.0, size=2.0),
            instance("Vehicle_Container_color03", x=20.0, size=3.5),
        ]
        derived = bind_layout.apply_layout(
            instances, [], [phantom_candidate("Vehicle_Container_color02")]
        )
        proxy = derived["phantoms"][0]
        self.assertAlmostEqual(proxy["max_x_m"] - proxy["min_x_m"], 7.0)
        self.assertAlmostEqual(proxy["max_z_m"] - proxy["min_z_m"], 7.0)


# --- BC-DATA-12：内嵌快照必须属于归档提供者闭集 ---------------------------
class _ScenarioTreeCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _frame(self, relative_dir: str, name: str = "frame_0.jpg") -> str:
        directory = self.root / relative_dir
        directory.mkdir(parents=True, exist_ok=True)
        (directory / name).write_bytes(b"x")
        return f"{relative_dir}/{name}"

    def _write(self, relative_path: str, document: dict) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document), encoding="utf-8")


class MutableRootConfigTest(_ScenarioTreeCase):
    """分支 3 与 4：可变的根级 `runtime/scenario_config.json` 永久禁止。"""

    def test_mutable_root_config_alone_still_yields_unbound(self) -> None:
        frame = self._frame("runtime/orphan-archive/frames")
        self._write("runtime/scenario_config.json", {"scenario_id": "whatever-is-loaded-now"})
        resolution = bind_layout.resolve_frame_scenario(self.root, frame, {})
        self.assertEqual(resolution["status"], bind_layout.BINDING_UNBOUND)
        self.assertNotEqual(resolution["source"], "embedded_snapshot")
        self.assertNotEqual(resolution["path"], "runtime/scenario_config.json")

    def test_mutable_root_config_does_not_shadow_a_valid_manifest(self) -> None:
        """不合格候选**既不绑定也不遮蔽下一优先级**。"""
        frame = self._frame("runtime/orphan-archive/frames")
        self._write("runtime/scenario_config.json", {"scenario_id": "whatever-is-loaded-now"})
        self._write(
            "runtime/orphan-archive/manifest.json", {"scenario_config_sha256": SHA_A}
        )
        resolution = bind_layout.resolve_frame_scenario(
            self.root, frame, {SHA_A: ["config/scenario.default.json"]}
        )
        self.assertEqual(resolution["status"], bind_layout.BINDING_BOUND)
        self.assertEqual(resolution["source"], "manifest_sha_match")
        self.assertEqual(resolution["sha256"], SHA_A)

    def test_root_config_is_barred_even_if_provider_patterns_widen(self) -> None:
        """裁定：该精确路径永久禁止，即使未来 pattern 放宽也不得命中。"""
        self.assertIn("runtime/scenario_config.json", bind_layout.FORBIDDEN_SNAPSHOT_PATHS)

    def test_config_json_never_becomes_a_snapshot_by_ancestry(self) -> None:
        """`config/*.json` 只能在 manifest 声明 SHA 与字节相等时作 provider。"""
        frame = self._frame("config/nested/frames")
        self._write("config/scenario.default.json", {"scenario_id": "default"})
        resolution = bind_layout.resolve_frame_scenario(self.root, frame, {})
        self.assertNotEqual(resolution["source"], "embedded_snapshot")


class LegitimateSnapshotTest(_ScenarioTreeCase):
    """分支 5：合法的 run 内嵌快照仍优先于 manifest。"""

    def test_run_embedded_snapshot_still_wins(self) -> None:
        frame = self._frame("runtime/runs/p1-demo-run/frames")
        self._write("runtime/runs/p1-demo-run/scenario.json", {"scenario_id": "demo"})
        self._write(
            "runtime/runs/p1-demo-run/manifest.json", {"scenario_config_sha256": SHA_A}
        )
        resolution = bind_layout.resolve_frame_scenario(
            self.root, frame, {SHA_A: ["config/scenario.default.json"]}
        )
        self.assertEqual(resolution["status"], bind_layout.BINDING_BOUND)
        self.assertEqual(resolution["source"], "embedded_snapshot")
        self.assertEqual(resolution["path"], "runtime/runs/p1-demo-run/scenario.json")

    def test_archive_embedded_scenario_config_is_accepted(self) -> None:
        frame = self._frame("runtime/test-results/ut-demo/pass/frames")
        self._write(
            "runtime/test-results/ut-demo/pass/scenario_config.json", {"scenario_id": "d"}
        )
        resolution = bind_layout.resolve_frame_scenario(self.root, frame, {})
        self.assertEqual(resolution["source"], "embedded_snapshot")

    def test_non_provider_snapshot_is_skipped_for_a_deeper_allowed_one(self) -> None:
        """不合格候选不得遮蔽——须继续寻找**最近的允许**内嵌快照。"""
        frame = self._frame("runtime/runs/p1-demo-run/frames")
        self._write("runtime/runs/p1-demo-run/scenario.json", {"scenario_id": "run"})
        self._write("runtime/scenario_config.json", {"scenario_id": "mutable"})
        resolution = bind_layout.resolve_frame_scenario(self.root, frame, {})
        self.assertEqual(resolution["path"], "runtime/runs/p1-demo-run/scenario.json")

    def test_candidate_must_actually_be_an_ancestor(self) -> None:
        """匹配 pattern 还不够，候选必须确为该帧祖先。"""
        frame = self._frame("runtime/runs/p1-demo-run/frames")
        self._write("runtime/runs/p1-other-run/scenario.json", {"scenario_id": "other"})
        resolution = bind_layout.resolve_frame_scenario(self.root, frame, {})
        self.assertEqual(resolution["status"], bind_layout.BINDING_UNBOUND)


class ProviderClosureTest(unittest.TestCase):
    def test_allowed_snapshot_predicate_matches_the_frozen_provider_set(self) -> None:
        for pattern, sample in (
            ("runtime/runs/*/scenario.json", "runtime/runs/p1-demo/scenario.json"),
            (
                "runtime/test-results/**/scenario_config.json",
                "runtime/test-results/a/b/scenario_config.json",
            ),
        ):
            self.assertIn(pattern, roots.SCENARIO_BYTE_PROVIDERS)
            self.assertTrue(bind_layout.is_allowed_embedded_snapshot(sample), sample)

    def test_mutable_and_unlisted_paths_are_rejected(self) -> None:
        for sample in (
            "runtime/scenario_config.json",
            "runtime/scenario.json",
            "runtime/orphan/scenario_config.json",
            "config/scenario.default.json",
        ):
            self.assertFalse(bind_layout.is_allowed_embedded_snapshot(sample), sample)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
