"""接受轮 29 的具名回归（SP29-1 / BC-DATA-26：近重复闭包的有界证明表示）。

裁定：`docs/proposals/P1-VLM-DATA-001-grounding-data-foundation.md` §41
（`IMPLEMENTATION_REWORK_REQUIRED / S4_MANIFEST_SCALE`，2026-09-01）。真实归档
实测：S4 manifest 515,074,557 B，其中全量 `near_duplicate_pairs` 2,663,282 对占
512,888,211 B，随合格 pair 数二次增长，违反 BC-DATA-25 §33.2(4)(5)。

两条都落在**生产路径**上，且都拿「修前算法」当基准而不是拿新实现自证：

- `test_archive_scale_near_duplicates_keep_s4_summary_bounded`：大量同 pHash 帧下
  合格 pair 数按帧数二次增长，而保留的 union witnesses 仍受 family 数上界约束、
  manifest 摘要不含 `near_duplicate_pairs` 且体积不随 pair 数增长；再经生产
  `stage4_splits()` 证明正式写出的 S4 manifest 同样如此。修前生产代码在
  「全量列表 / 上界」断言处必红。
- `test_union_witnesses_replay_exact_atoms_and_preserve_pair_count`：小夹具（含冗余
  合格 pair 与传递并簇）上 `near_duplicate_pair_count`、分量与 `atom_id` 与修前
  `merge_atoms` 的逐行转写逐字相等；witnesses 恰为同序遍历中首次连接两个不同分量
  的 pair，按同顺序重放重建完全相同的 family→atom 分量，冗余/同族 witness 被
  fail-closed 拒绝。
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
import random
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import (  # noqa: E402
    artifacts,
    bind_layout,
    contract,
    make_splits,
    run_pipeline,
)
from test_dist_data_driver import LAYOUTS, DriverCase, body, sidecar  # noqa: E402


def _legacy_merge_atoms(
    family_of_frame: dict[str, str], phash_of_frame: dict[str, int]
) -> dict:
    """修前 `merge_atoms` 的逐行转写（接受轮 28 候选上的生产实现）。

    它把每一对合格 pair 都 `append` 进列表并整份写出——这正是 SP29-1 的成因；
    这里只用它做 count / 分量 / atom_id 的等价基准。
    """
    families = sorted(set(family_of_frame.values()))
    union = make_splits._UnionFind(families)
    frames = sorted(phash_of_frame)
    near_duplicate_pairs: list[tuple[str, str]] = []
    for left, right in itertools.combinations(frames, 2):
        family_left = family_of_frame[left]
        family_right = family_of_frame[right]
        if family_left == family_right:
            continue
        if (
            make_splits.hamming(phash_of_frame[left], phash_of_frame[right])
            <= contract.PHASH_NEAR_DUPLICATE_HAMMING
        ):
            union.union(family_left, family_right)
            near_duplicate_pairs.append((left, right))
    components: dict[str, list[str]] = {}
    for family in families:
        components.setdefault(union.find(family), []).append(family)
    atoms = {
        make_splits.atom_id_for(members): sorted(members) for members in components.values()
    }
    return {
        "atoms": {atom: atoms[atom] for atom in sorted(atoms)},
        "near_duplicate_pair_count": len(near_duplicate_pairs),
        "near_duplicate_pairs": [list(pair) for pair in near_duplicate_pairs],
    }


def _first_connecting_pairs(
    family_of_frame: dict[str, str], pairs: list[list[str]]
) -> list[list[str]]:
    """从修前的全量合格 pair 列表（同序）机械取出「首次连接两个不同分量」的子序列。"""
    union = make_splits._UnionFind(sorted(set(family_of_frame.values())))
    witnesses: list[list[str]] = []
    for left, right in pairs:
        family_left, family_right = family_of_frame[left], family_of_frame[right]
        if union.find(family_left) != union.find(family_right):
            union.union(family_left, family_right)
            witnesses.append([left, right])
    return witnesses


def _same_phash_world(families: int, frames_per_family: int) -> tuple[dict, dict]:
    """`families` 个复制族，每族 `frames_per_family` 帧，全部同一 pHash。"""
    family_of: dict[str, str] = {}
    phash_of: dict[str, int] = {}
    for index in range(families):
        family = f"fam{index:02d}"
        for frame in range(frames_per_family):
            frame_id = f"runtime/synthetic/{family}/frames/frame_{frame:010d}.jpg"
            family_of[frame_id] = family
            phash_of[frame_id] = 0
    return family_of, phash_of


def _cross_family_pairs(families: int, frames_per_family: int) -> int:
    total = families * frames_per_family
    return total * (total - 1) // 2 - families * frames_per_family * (frames_per_family - 1) // 2


def _max_list_length(document) -> int:
    """摘要里任何列表成员的最大长度（递归）。"""
    if isinstance(document, list):
        return max([len(document), *(_max_list_length(item) for item in document)])
    if isinstance(document, dict):
        return max([0, *(_max_list_length(value) for value in document.values())])
    return 0


THREE_FAMILIES = {"famA": "default", "famB": "scene-004", "famC": "default"}
THREE_UNITS = {family: f"runtime/synthetic/{family}" for family in THREE_FAMILIES}
FRAMES_PER_FAMILY = 40


class _MergingStubPixels:
    """famA 与 famB 全部帧同一签名（并簇），famC 远离（独立原子）。"""

    def __init__(self) -> None:
        self.phash_calls = 0

    def crop_rgb(self, frame_id, box_px):  # noqa: ANN001
        centre = (box_px[0] + box_px[2]) / 2.0
        return [(255, 0, 0) if centre < 320.0 else (0, 0, 255)] * 8

    def gray_matrix(self, frame_id, size):  # noqa: ANN001
        raise AssertionError("driver 应通过 phash() 取近重复签名")

    def phash(self, frame_id):  # noqa: ANN001
        self.phash_calls += 1
        return (2**64 - 1) if "famC" in frame_id else 0


class ArchiveScaleNearDuplicateTest(DriverCase):
    """SP29-1：合格 pair 数二次增长，manifest 摘要仍受 family 数上界约束。"""

    def setUp(self) -> None:
        super().setUp()
        # 基类已用两族世界装好 S1/S2；换成三族、每族 40 帧、famA≈famB 的 stub。
        self.pixels = _MergingStubPixels()
        self.driver = run_pipeline.PipelineDriver(self.root, pixels=self.pixels)

    def _frame_paths(self) -> list[tuple[str, str]]:
        return [
            (family, f"{THREE_UNITS[family]}/frames/frame_{index:010d}.jpg")
            for family in THREE_FAMILIES
            for index in range(FRAMES_PER_FAMILY)
        ]

    def _inventory(self) -> dict:
        records = []
        for family, relative in self._frame_paths():
            records.append(
                {
                    "path": relative,
                    "kind": "image",
                    "decision": "INCLUDED",
                    "family": family,
                    "layout_class": THREE_FAMILIES[family],
                    "usage_class": "VALID_FORMAL",
                    "sidecar_join": {"present": True, "complete": True},
                    "truth_join": {"source": None, "schema_family": None},
                }
            )
        return {"stage": 1, "records": records, "record_count": len(records)}

    def _layout(self) -> dict:
        partitions = {}
        for family, layout_class in THREE_FAMILIES.items():
            partitions[f"{family}|sha"] = {
                "partition_id": f"{family}|sha",
                "family": family,
                "layout_class": layout_class,
                "binding_status": "BOUND",
                "source_units": [THREE_UNITS[family]],
                "frame_count": FRAMES_PER_FAMILY,
                "instances": [body(name, x, z) for name, x, z in LAYOUTS[layout_class]],
                "phantoms": [],
                "relocation_marks": {},
                "route_world_m": [],
            }
        return {
            "stage": 2,
            "scenario_partitions": partitions,
            "families": {},
            "cross_validation": {
                identifier: {
                    "mode": "none",
                    "status": bind_layout.CROSSCHECK_NOT_APPLICABLE,
                    "reason": "合成世界无归档逐帧真值",
                    "pair_count": 0,
                    "sample_count": 0,
                }
                for identifier in partitions
            },
        }

    def test_archive_scale_near_duplicates_keep_s4_summary_bounded(self) -> None:
        # --- (1) 函数级：pair 数按帧数二次增长，摘要不随之增长 -----------------
        small = _same_phash_world(4, 50)
        large = _same_phash_world(4, 300)
        merged_small = make_splits.merge_atoms(*small)
        merged_large = make_splits.merge_atoms(*large)
        expected_small = _cross_family_pairs(4, 50)
        expected_large = _cross_family_pairs(4, 300)
        self.assertEqual(merged_small["near_duplicate_pair_count"], expected_small)
        self.assertEqual(merged_large["near_duplicate_pair_count"], expected_large)
        # 帧数 ×6 → 合格 pair 数恰 ×36：全对比较仍逐对计数，且是二次增长。
        self.assertEqual(
            merged_large["near_duplicate_pair_count"],
            36 * merged_small["near_duplicate_pair_count"],
        )
        # 修前生产代码在此必红：全量 pair 列表不得进入 S4 摘要。
        # （用 assertFalse 而不是 assertNotIn：修前失败时不回显 54 万对的容器。）
        self.assertFalse(
            "near_duplicate_pairs" in merged_large,
            "S4 摘要仍携带全量 near_duplicate_pairs（随合格 pair 数二次增长的成员；"
            f"修前实测 {merged_large['near_duplicate_pair_count']} 对被整份驻留并写出）",
        )
        for merged, world in ((merged_small, small), (merged_large, large)):
            family_count = len(set(world[0].values()))
            witnesses = merged["near_duplicate_union_witnesses"]
            self.assertEqual(len(merged["atoms"]), 1, "全部同签名 → 并成一个原子")
            self.assertEqual(
                len(witnesses), family_count - len(merged["atoms"]),
                "witness 数必须恰为 family_count − atom_count",
            )
            self.assertLessEqual(
                _max_list_length(merged), max(family_count, 2),
                "摘要中不得有任何按合格 pair 数增长的列表成员",
            )
            self.assertEqual(
                make_splits.replay_union_witnesses(world[0], witnesses), merged["atoms"]
            )
        # 体积上界：从 15,000 对到 540,000 对，摘要字节只允许 count 的位数变化。
        bytes_small = artifacts.canonical_json_bytes(merged_small)
        bytes_large = artifacts.canonical_json_bytes(merged_large)
        self.assertLessEqual(
            len(bytes_large), len(bytes_small) + 8,
            f"摘要体积随合格 pair 数增长：{len(bytes_small)} → {len(bytes_large)} B",
        )

        # --- (2) 生产路径：`stage4_splits()` 正式写出的 manifest 同样有界 ----------
        catalog = self.driver.stage3_frames_catalog()
        self.assertEqual(catalog["frames"], 3 * FRAMES_PER_FAMILY)
        result = self.driver.stage4_splits()
        self.assertNotIn("terminal", result, result)
        self.assertEqual(result["atoms"], 2, "famA+famB 并簇、famC 独立 → 2 个原子")
        self.assertEqual(self.pixels.phash_calls, 3 * FRAMES_PER_FAMILY)
        manifest, _ref = self.store.composite_manifest(
            "splits", "attempt-1", requesting_stage=4
        )
        summary = manifest["atoms"]
        self.assertFalse(
            "near_duplicate_pairs" in summary,
            "正式写出的 S4 manifest 仍携带全量 near_duplicate_pairs",
        )
        self.assertEqual(
            summary["near_duplicate_pair_count"], FRAMES_PER_FAMILY * FRAMES_PER_FAMILY,
            "famA×famB 的每一对合格 pair 仍逐对计数",
        )
        self.assertEqual(len(summary["atoms"]), 2)
        self.assertEqual(
            len(summary["near_duplicate_union_witnesses"]), len(THREE_FAMILIES) - 2
        )
        family_of = {
            entry["frame_id"]: entry["family"]
            for entry in self.store.read_composite_rows(
                "frames_catalog", "attempt-1", requesting_stage=4
            )
        }
        self.assertEqual(
            make_splits.replay_union_witnesses(
                family_of, summary["near_duplicate_union_witnesses"]
            ),
            summary["atoms"],
        )
        self.assertLess(
            len(artifacts.canonical_json_bytes(summary)), 4096,
            "1,600 对合格 pair 下 S4 manifest 的 atoms 摘要仍须是小型摘要",
        )
        self.assertLessEqual(_max_list_length(summary), len(THREE_FAMILIES))


class UnionWitnessReplayTest(unittest.TestCase):
    """BC-DATA-26 (3)：witnesses 与修前全量 pair 路径的 count / 分量逐字等价并可重放。"""

    def setUp(self) -> None:
        far = int("1" * 40, 2)
        self.family_of = {
            "a1": "famA", "a2": "famA",
            "b1": "famB", "b2": "famB",
            "c1": "famC",
            "d1": "famD",
            "e1": "famE",
            "f1": "famF",
        }
        self.phash_of = {
            "a1": 0b0, "a2": 0b1,
            "b1": 0b11, "b2": 0b111,
            "c1": 0b1111,          # 与 famA、famB 都合格 → 传递并簇 + 冗余 pair
            "d1": far,
            "e1": far ^ 0b11,      # 只与 famD 合格
            "f1": 0xFFFFFFFF00000000,  # 与两组都远
        }

    def test_union_witnesses_replay_exact_atoms_and_preserve_pair_count(self) -> None:
        legacy = _legacy_merge_atoms(self.family_of, self.phash_of)
        merged = make_splits.merge_atoms(self.family_of, self.phash_of)

        # count / 分量 / atom_id 与修前逐字相等。
        self.assertEqual(legacy["near_duplicate_pair_count"], 9, "夹具须含冗余合格 pair")
        self.assertEqual(merged["near_duplicate_pair_count"], legacy["near_duplicate_pair_count"])
        self.assertEqual(merged["atoms"], legacy["atoms"])
        self.assertEqual(
            sorted(legacy["atoms"].values()),
            [["famA", "famB", "famC"], ["famD", "famE"], ["famF"]],
        )
        self.assertTrue(
            "near_duplicate_union_witnesses" in merged,
            "S4 摘要缺少 near_duplicate_union_witnesses（修前生产代码只有全量 pair 列表）",
        )
        self.assertFalse("near_duplicate_pairs" in merged, "S4 摘要仍携带全量 near_duplicate_pairs")

        # witnesses = 同序遍历中首次连接两个不同分量的 pair；受 family 数约束。
        witnesses = merged["near_duplicate_union_witnesses"]
        self.assertEqual(len(witnesses), 6 - 3)
        self.assertEqual(
            witnesses, _first_connecting_pairs(self.family_of, legacy["near_duplicate_pairs"])
        )
        legacy_pairs = {tuple(pair) for pair in legacy["near_duplicate_pairs"]}
        for left, right in witnesses:
            self.assertIn((left, right), legacy_pairs, "witness 必须本身是合格 pair")
            self.assertNotEqual(self.family_of[left], self.family_of[right])
            self.assertLessEqual(
                make_splits.hamming(self.phash_of[left], self.phash_of[right]),
                contract.PHASH_NEAR_DUPLICATE_HAMMING,
            )

        # 按同顺序重放必须重建完全相同的 family→atom 分量。
        self.assertEqual(
            make_splits.replay_union_witnesses(self.family_of, witnesses), legacy["atoms"]
        )
        # 输入字典的插入顺序不影响任何输出（确定性）。
        for seed in range(5):
            order = list(self.family_of)
            random.Random(seed).shuffle(order)
            shuffled = make_splits.merge_atoms(
                {k: self.family_of[k] for k in order}, {k: self.phash_of[k] for k in order}
            )
            self.assertEqual(shuffled, merged)
        # 与写盘同款的 canonical 字节也逐字节相同。
        self.assertEqual(
            artifacts.canonical_json_bytes(shuffled), artifacts.canonical_json_bytes(merged)
        )

        # 重放 fail-closed：冗余 witness（已在同一分量）或同族 pair 一律拒绝。
        with self.assertRaises(make_splits.SplitError):
            make_splits.replay_union_witnesses(
                self.family_of, [*witnesses, ["a2", "b2"]]
            )
        with self.assertRaises(make_splits.SplitError):
            make_splits.replay_union_witnesses(self.family_of, [["a1", "a2"]])
        with self.assertRaises(make_splits.SplitError):
            make_splits.replay_union_witnesses(self.family_of, [["a1", "zz"]])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
