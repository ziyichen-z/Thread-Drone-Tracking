"""接受轮 24 的具名回归（复核轮 6 F20 / F21 / F22）。

裁定：`docs/proposals/P1-VLM-DATA-001-grounding-data-foundation.md` §36
（`REVIEW_R6_FINDINGS_ACCEPTED / F20_F21_F22_ROUTED /
IMPLEMENTATION_REWORK_REQUIRED`，2026-09-01）；finding 原文见
`docs/reviews/P1-VLM-DATA-001.md` Round 6。

三条都落在**生产路径**上，且都拿「修前整表算法」当基准而不是拿流式实现
自证：

- F20 `test_streamed_g0_report_preserves_nonzero_f2_and_frames_by_split`
  走生产 `stage7_gate()`，夹具在修前整表语义下产出**非零** F2，逐字段比对
  正式写出的 g0_report `floors.F2`（含 `station_keys`）与
  `stratified_denominators.frames_by_split`。只比 `gate` / `unmet_floors`
  不合格——小夹具下修前同样四条 floor 全不达标，缺陷会整个穿过去。
- F21 `test_stage5_field_catalog_is_logically_identical_and_bounded_per_object`
  每对象给 16 条跨帧 observation（K=5），完整 payload 与修前整表算法逐字段
  相等，并在生产路径上以 `weakref` 证明任何时刻存活的 observation 不超过
  `object_count × K`（+1 = 正在传递中的那条）。只查最终候选数不合格。
- F22 `test_legacy_and_streaming_split_paths_share_assign_atoms`
  证明整表与流式两个生产函数**都**调用共享的 `assign_atoms()`，且各自的
  输出确实就是那一次共享计算的产物（对象同一性），不是同构复制。
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
import unittest.mock
import weakref

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import (  # noqa: E402
    build_catalog,
    contract,
    g0_report,
    make_splits,
)
from test_dist_data_driver import DriverCase, FAMILY_LAYOUT, FAMILY_UNIT, sidecar  # noqa: E402
from test_dist_data_splits import atom  # noqa: E402


class SplitSideChannelTest(DriverCase):
    """F20：S7 流式化后 `split` 侧信道必须逐次迭代重建，指标不得被静默归零。"""

    def _split_of_frame(self) -> dict[str, str]:
        manifest, _reference = self.store.composite_manifest(
            "splits", "attempt-1", requesting_stage=7
        )
        return {
            frame: split
            for split, frames in manifest["frames"].items()
            for frame in frames
        }

    def _legacy_decorated_entries(self) -> list[dict]:
        """修前语义：同一批 entry 对象**先打 split 键，再交给同一个计算函数**。

        entry 本身取自组合工件的行流——`test_streamed_consumers_match_legacy_
        small_fixture_s4_to_s8` 已经把它与修前整表构造逐字段钉死，所以这里
        物化它只是在造**基准**，不是在给生产路径背书。
        """
        entries = list(
            self.store.read_composite_rows(
                "frames_catalog", "attempt-1", requesting_stage=4
            )
        )
        split_of_frame = self._split_of_frame()
        for entry in entries:
            entry["split"] = split_of_frame.get(entry["frame_id"])
        return entries

    def test_streamed_g0_report_preserves_nonzero_f2_and_frames_by_split(self) -> None:
        self.driver.stage3_frames_catalog()
        self.driver.stage4_splits()
        self.driver.stage5_field_catalog()
        self._write_passing_audit()
        self.driver.stage7_gate()

        report = json.loads(
            self.store.path_for("g0_report", "attempt-1").read_bytes()
        )["payload"]

        entries = self._legacy_decorated_entries()
        expected_f2 = g0_report.compute_f2(entries)
        frozen, _ref = self.store.read(
            "mother_candidates", "attempt-1", requesting_stage=8
        )
        expected_denominators = g0_report.stratified_denominators(entries, frozen)

        # 夹具强度：修前语义下 F2 必须**非零**，否则本用例根本区分不出缺陷。
        self.assertGreater(expected_f2["global"], 0, "夹具须在修前语义下产出非零 F2")
        self.assertTrue(expected_f2["station_keys"], "夹具须有非空站位簇键")
        self.assertGreater(
            sum(expected_f2["per_split"].values()), 0, "夹具须有逐 split 的站位簇"
        )

        # F2：逐字段（数值 + station_keys），不是只比 passed。
        got_f2 = report["floors"]["F2"]
        for key in ("global", "per_split", "station_keys", "floor", "passed"):
            self.assertEqual(got_f2[key], expected_f2[key], f"floors.F2.{key}")
        self.assertEqual(got_f2, expected_f2)
        self.assertEqual(
            report["station_clustering"]["keys"], expected_f2["station_keys"],
            "station_clustering.keys 取自同一个 F2，不得各说各话",
        )

        # 分层分母：`frames_by_split` 必须是真实四集，不得整体落进 "None"。
        got_by_split = report["stratified_denominators"]["frames_by_split"]
        self.assertEqual(got_by_split, expected_denominators["frames_by_split"])
        self.assertNotIn(
            "None", got_by_split, "帧全部计入 None 即 split 侧信道被切断"
        )


class BoundedFieldCatalogTest(DriverCase):
    """F21：S5 逐对象只保留最小 K 条，逻辑输出与修前整表逐字段相等。"""

    FRAMES_PER_FAMILY = 16
    DEPTH_STEP_M = 1.5

    def _frame_paths(self) -> list[tuple[str, str]]:
        return [
            (family, f"{FAMILY_UNIT[family]}/frames/frame_{index:010d}.jpg")
            for family in FAMILY_LAYOUT
            for index in range(self.FRAMES_PER_FAMILY)
        ]

    def _write_frames(self) -> None:
        """每 4 帧一个深度档：`camera_depth_m` 有平局，平局由 frame_id 决出。

        这样最小 K 条既跨深度档又跨帧，任何「按帧序取前 K」或「不排序」的
        写法都会与修前整表算法产生不同的候选集。
        """
        for _family, relative in self._frame_paths():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"")  # driver 不解码，像素走注入的 stub
            index = int(target.stem.rsplit("_", 1)[-1])
            document = sidecar(index)
            document["camera_position_world_m"] = [
                (index % 4) * 3.0,
                10.0,
                (index // 4) * self.DEPTH_STEP_M,
            ]
            target.with_suffix(".json").write_text(
                json.dumps(document), encoding="utf-8"
            )

    def _layout(self) -> dict:
        layout = super()._layout()
        for partition in layout["scenario_partitions"].values():
            partition["frame_count"] = self.FRAMES_PER_FAMILY
        return layout

    # --- 修前整表基准 -------------------------------------------------------
    @staticmethod
    def _legacy_whole_table_field_catalog(
        object_ids, observations, pixels, *, relocated=()
    ) -> dict:
        """逐字转写自修前 `build_field_catalog`：先整表分组，再排序取前 K。

        下游的 crop / HSV / 组一致性 / 输出装配复用未改动的既有实现，改动的
        只有累积与选择这一段，所以基准把它整表做一遍。
        """
        relocated_set = set(relocated)
        by_object: dict[str, list] = {}
        for observation in observations:
            by_object.setdefault(observation.object_id, []).append(observation)

        per_object: dict[str, dict] = {}
        for object_id in sorted(object_ids):
            class_word = contract.class_for_scene_object(object_id)
            record: dict = {
                "object_id": object_id,
                "class": class_word,
                "class_verified": class_word is not None,
                "group_key": contract.color_group_key(object_id),
                "dynamic_state": "static",
                "relocated": object_id in relocated_set,
                "color": None,
                "color_status": "UNVERIFIED",
                "color_evidence": None,
            }
            candidates = sorted(
                by_object.get(object_id, []),
                key=lambda item: (item.camera_depth_m, item.frame_id),
            )[: contract.COLOR_SAMPLE_FRAME_COUNT]
            if candidates:
                sampled: list[tuple[int, int, int]] = []
                for candidate in candidates:
                    sampled.extend(
                        pixels.crop_rgb(
                            candidate.frame_id,
                            build_catalog._inset(
                                candidate.visible_px, contract.COLOR_BOX_INSET_FRACTION
                            ),
                        )
                    )
                estimate = build_catalog.estimate_color(sampled)
                record["color_evidence"] = {
                    "frames": [candidate.frame_id for candidate in candidates],
                    **estimate,
                }
                if estimate["color"] is not None:
                    record["color"] = estimate["color"]
                    record["color_status"] = "VERIFIED"
            per_object[object_id] = record

        groups: dict[str, list[str]] = {}
        for object_id, record in per_object.items():
            groups.setdefault(record["group_key"], []).append(object_id)
        group_report: dict[str, dict] = {}
        for group_key in sorted(groups):
            members = sorted(groups[group_key])
            words = {
                per_object[member]["color"]
                for member in members
                if per_object[member]["color"] is not None
            }
            consistent = len(words) <= 1
            if not consistent:
                for member in members:
                    per_object[member]["color"] = None
                    per_object[member]["color_status"] = "UNVERIFIED"
                    per_object[member]["color_downgrade_reason"] = "GROUP_INCONSISTENT"
            group_report[group_key] = {
                "members": members,
                "resolved_words": sorted(words),
                "consistent": consistent,
            }

        verified_colors = sorted(
            {
                record["color"]
                for record in per_object.values()
                if record["color_status"] == "VERIFIED" and record["color"]
            }
        )
        return {
            "stage": build_catalog.STAGE_FIELDS,
            "objects": {
                object_id: per_object[object_id] for object_id in sorted(per_object)
            },
            "groups": group_report,
            "verified_color_vocabulary": verified_colors,
            "dual_verified_object_ids": sorted(
                object_id
                for object_id, record in per_object.items()
                if record["class_verified"] and record["color_status"] == "VERIFIED"
            ),
        }

    def _whole_table_observations(self) -> tuple[list[str], list]:
        """测试侧才允许物化的整表 observation 集（基准输入）。"""
        object_ids: set[str] = set()
        observations = []
        for entry in self.driver._catalog_stream(requesting_stage=5):
            for item in entry["objects"]:
                if item["status"] != "OK" or item["visible_px"] is None:
                    continue
                object_ids.add(item["object_id"])
                observations.append(
                    build_catalog.ObjectObservation(
                        entry["frame_id"],
                        item["object_id"],
                        tuple(item["visible_px"]),
                        item["camera_depth_m"],
                    )
                )
        return sorted(object_ids), observations

    def test_stage5_field_catalog_is_logically_identical_and_bounded_per_object(
        self,
    ) -> None:
        self.driver.stage3_frames_catalog()
        self.driver.stage4_splits()

        alive: list[weakref.ref] = []
        peak = {"live": 0, "constructed": 0}

        class _TrackedObservation(build_catalog.ObjectObservation):
            """生产路径上真正被构造的那条 observation，可被 weakref 追踪。"""

            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                alive.append(weakref.ref(self))
                peak["constructed"] += 1
                live = sum(1 for reference in alive if reference() is not None)
                peak["live"] = max(peak["live"], live)

        with unittest.mock.patch.object(
            build_catalog, "ObjectObservation", _TrackedObservation
        ):
            self.driver.stage5_field_catalog()

        payload = json.loads(
            self.store.path_for("field_catalog", "attempt-1").read_bytes()
        )["payload"]

        object_ids, observations = self._whole_table_observations()
        expected = self._legacy_whole_table_field_catalog(
            object_ids, observations, self.pixels, relocated=[]
        )

        # 逻辑等价：完整 payload 逐字段与修前整表算法相等。
        for key in sorted(expected):
            self.assertEqual(payload[key], expected[key], key)
        self.assertEqual(payload, expected)

        # 夹具强度：每对象都必须**明显多于** K 条跨帧观测，否则有界性无从谈起。
        limit = contract.COLOR_SAMPLE_FRAME_COUNT
        per_object: dict[str, int] = {}
        for observation in observations:
            per_object[observation.object_id] = per_object.get(observation.object_id, 0) + 1
        self.assertTrue(per_object, "夹具须产出 observation")
        for object_id, count in sorted(per_object.items()):
            self.assertGreater(count, limit, f"{object_id} 只有 {count} 条观测")
        # 选择确实跨深度档：最小 K 条不等于「按 frame_id 取前 K 条」。
        for object_id in object_ids:
            frames = payload["objects"][object_id]["color_evidence"]["frames"]
            self.assertEqual(len(frames), limit)
            naive = sorted(
                observation.frame_id
                for observation in observations
                if observation.object_id == object_id
            )[:limit]
            self.assertNotEqual(sorted(frames), naive, "夹具须能区分排序语义")

        # 有界性：生产路径上任何时刻存活的 observation ≤ object_count × K + 1
        # （+1 = 刚构造、尚未被选择器决定去留的那一条）。整表物化必然突破它。
        object_count = len(payload["objects"])
        bound = object_count * limit + 1
        self.assertGreater(
            peak["constructed"], bound,
            "夹具构造的观测总数须远超上界，否则「有界」不可证伪",
        )
        self.assertLessEqual(
            peak["live"], bound,
            f"生产路径同时驻留 {peak['live']} 条 observation，超过 "
            f"object_count × K + 1 = {bound}；S5 疑似仍在物化全集",
        )


class SharedAtomAssignmentTest(unittest.TestCase):
    """F22：整表与流式两条生产路径必须共用同一份 atom 指派实现。"""

    def setUp(self) -> None:
        self.atoms = [
            atom("a", frames=20, layouts=["default"], non_floor=2),
            atom("b", frames=20, layouts=["scene-004"], non_floor=3, d3=True),
            atom("c", frames=40, layouts=["default"], non_floor=1, d3=True),
            atom("d", frames=40, layouts=["scene-004"]),
            atom("e", frames=40, layouts=["default"]),
        ]

    def test_legacy_and_streaming_split_paths_share_assign_atoms(self) -> None:
        original = make_splits.assign_atoms
        calls: list[dict] = []

        def _spy(atoms):
            result = original(atoms)
            calls.append(result)
            return result

        with unittest.mock.patch.object(make_splits, "assign_atoms", _spy):
            legacy = make_splits.assign_splits(self.atoms, [])
            summary_of, rows = make_splits.assign_splits_streaming(self.atoms, iter([]))
            list(rows)
            streaming = summary_of()

        self.assertEqual(
            len(calls), 2,
            "整表与流式两条生产路径各须调用一次共享 assign_atoms()；"
            f"实测 {len(calls)} 次，说明仍存在平行复制实现",
        )
        legacy_base, streaming_base = calls
        # 对象同一性：两条路的输出确实**就是**那一次共享计算的产物。
        self.assertIs(legacy["frames"], legacy_base["frames_by_split"])
        self.assertIs(legacy["leakage_assertions"], legacy_base["leakage"])
        self.assertIs(streaming["frames"], streaming_base["frames_by_split"])
        self.assertIs(streaming["leakage_assertions"], streaming_base["leakage"])
        # split 语义仍逐字段相同（既有等价回归保留，这里再钉一次非角色键）。
        for key in (
            "atom_assignment",
            "family_assignment",
            "frames",
            "frame_counts",
            "dropped_frames",
            "d3_holdout_empty",
            "leakage_assertions",
        ):
            self.assertEqual(legacy[key], streaming[key], key)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
