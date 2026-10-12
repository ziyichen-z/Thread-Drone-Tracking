"""S4 切分：pHash 并簇、留出物体、test 全枚举、D3、dev、泄漏断言（§2.5，BC-DATA-2）。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import bind_layout, contract, make_splits  # noqa: E402


def gradient(size: int, offset: float = 0.0) -> list[list[float]]:
    return [[(row * size + column + offset) % 256 for column in range(size)] for row in range(size)]


def atom(
    atom_id: str,
    *,
    frames: int,
    layouts: list[str],
    families: list[str] | None = None,
    d3: bool = False,
    non_floor: int = 0,
) -> make_splits.AtomSummary:
    return make_splits.AtomSummary(
        atom_id=atom_id,
        families=families or [atom_id],
        layout_classes=layouts,
        floor_eligible_frames=[f"{atom_id}/f{index}" for index in range(frames)],
        non_floor_frames=[f"{atom_id}/n{index}" for index in range(non_floor)],
        station_keys=[f"{atom_id}-station"],
        object_ids=[f"{atom_id}-object"],
        d3_eligible=d3,
    )


class PhashTest(unittest.TestCase):
    def test_hash_is_sixty_four_bits(self) -> None:
        value = make_splits.phash(gradient(contract.PHASH_RESIZE))
        self.assertGreaterEqual(value, 0)
        self.assertLess(value, 1 << contract.PHASH_BITS)

    def test_identical_matrices_have_distance_zero(self) -> None:
        matrix = gradient(contract.PHASH_RESIZE)
        self.assertEqual(make_splits.hamming(make_splits.phash(matrix), make_splits.phash(matrix)), 0)

    def test_wrong_matrix_size_is_rejected(self) -> None:
        with self.assertRaises(make_splits.SplitError):
            make_splits.phash(gradient(8))

    def test_dct_is_separable_and_deterministic(self) -> None:
        matrix = gradient(8)
        self.assertEqual(make_splits.dct_2d(matrix), make_splits.dct_2d(matrix))


class AtomMergeTest(unittest.TestCase):
    def test_near_duplicates_merge_families(self) -> None:
        family_of = {"a1": "famA", "b1": "famB"}
        result = make_splits.merge_atoms(family_of, {"a1": 0b1010, "b1": 0b1011})
        self.assertEqual(len(result["atoms"]), 1)
        self.assertEqual(next(iter(result["atoms"].values())), ["famA", "famB"])
        self.assertEqual(result["near_duplicate_pair_count"], 1)

    def test_distant_hashes_stay_separate(self) -> None:
        family_of = {"a1": "famA", "b1": "famB"}
        far = int("1" * 40, 2)
        result = make_splits.merge_atoms(family_of, {"a1": 0, "b1": far})
        self.assertEqual(len(result["atoms"]), 2)
        self.assertEqual(result["near_duplicate_pair_count"], 0)

    def test_atom_id_is_hash_of_sorted_member_ids(self) -> None:
        expected = hashlib.sha256("famA famB".encode("utf-8")).hexdigest()
        self.assertEqual(make_splits.atom_id_for(["famB", "famA"]), expected)

    def test_same_family_pairs_do_not_merge(self) -> None:
        result = make_splits.merge_atoms({"a1": "famA", "a2": "famA"}, {"a1": 0, "a2": 1})
        self.assertEqual(result["near_duplicate_pair_count"], 0)


class HeldOutTest(unittest.TestCase):
    def test_real_catalog_yields_thirty_two_held_out_objects(self) -> None:
        """101 辆车 → 9 类合计 32 辆（§2.5 冻结数）。"""
        geometry = bind_layout.load_base_geometry(PROJECT_ROOT)
        object_ids = [
            instance["scene_object_name"]
            for instance in geometry["instances"]
            if contract.class_for_scene_object(instance["scene_object_name"])
        ]
        selection = make_splits.held_out_objects(object_ids)
        self.assertEqual(selection["total"], 32)
        self.assertEqual(
            sorted(selection["class_sizes"].values()), [5, 5, 6, 8, 9, 12, 13, 20, 23]
        )
        self.assertEqual(
            sorted(selection["per_class_counts"].values()), [2, 2, 2, 2, 3, 4, 4, 6, 7]
        )

    def test_selection_is_deterministic_and_order_independent(self) -> None:
        objects = [f"Vehicle_Taxi ({index})" for index in range(1, 14)]
        first = make_splits.held_out_objects(objects)
        second = make_splits.held_out_objects(list(reversed(objects)))
        self.assertEqual(first["held_out_object_ids"], second["held_out_object_ids"])

    def test_non_vehicles_are_ignored(self) -> None:
        selection = make_splits.held_out_objects(["Building Sky_big_color01"])
        self.assertEqual(selection["total"], 0)


class TestAssignmentTest(unittest.TestCase):
    def test_fewer_than_two_atoms_terminates(self) -> None:
        with self.assertRaises(make_splits.SplitTerminal) as caught:
            make_splits.choose_test_atoms([atom("a", frames=10, layouts=["default"])])
        self.assertEqual(caught.exception.terminal, "INSUFFICIENT_SYMBOLIC_GROUNDING_DATA")

    def test_more_than_twenty_atoms_fails_closed(self) -> None:
        atoms = [atom(f"a{index}", frames=1, layouts=["default"]) for index in range(21)]
        with self.assertRaises(make_splits.SplitTerminal) as caught:
            make_splits.choose_test_atoms(atoms)
        self.assertEqual(caught.exception.terminal, "SPLIT_ENUMERATION_LIMIT_EXCEEDED")

    def test_prefers_two_atoms_covering_both_layout_classes(self) -> None:
        atoms = [
            atom("a", frames=10, layouts=["default"]),
            atom("b", frames=10, layouts=["scene-004"]),
            atom("c", frames=30, layouts=["default"]),
        ]
        chosen = make_splits.choose_test_atoms(atoms)
        self.assertGreaterEqual(len(chosen), 2)
        covered = {layout for item in chosen for layout in item.layout_classes}
        self.assertEqual(covered, {"default", "scene-004"})

    def test_target_is_one_fifth_of_floor_frames(self) -> None:
        atoms = [
            atom("a", frames=20, layouts=["default"]),
            atom("b", frames=20, layouts=["scene-004"]),
            atom("c", frames=80, layouts=["default"]),
            atom("d", frames=80, layouts=["scene-004"]),
        ]
        chosen = make_splits.choose_test_atoms(atoms)
        test_frames = sum(item.floor_frame_count for item in chosen)
        self.assertEqual(test_frames, 40)  # 5×40 = 200 = 总 floor 帧

    def test_result_is_deterministic_under_input_permutation(self) -> None:
        atoms = [
            atom("a", frames=10, layouts=["default"]),
            atom("b", frames=10, layouts=["scene-004"]),
            atom("c", frames=30, layouts=["default"]),
        ]
        first = [item.atom_id for item in make_splits.choose_test_atoms(atoms)]
        second = [item.atom_id for item in make_splits.choose_test_atoms(list(reversed(atoms)))]
        self.assertEqual(first, second)


class D3AndDevTest(unittest.TestCase):
    def test_d3_picks_smallest_key_among_eligible(self) -> None:
        atoms = [
            atom("a", frames=10, layouts=["default"], d3=True),
            atom("b", frames=10, layouts=["default"], d3=True),
        ]
        chosen = make_splits.choose_d3_holdout(atoms)
        expected = min(atoms, key=lambda item: item.key)
        self.assertIs(chosen, expected)

    def test_d3_is_empty_when_no_atom_qualifies(self) -> None:
        atoms = [atom("a", frames=10, layouts=["default"])]
        self.assertIsNone(make_splits.choose_d3_holdout(atoms))

    def test_dev_is_shortest_prefix_reaching_fifteen_percent(self) -> None:
        atoms = [atom(f"a{index}", frames=10, layouts=["default"]) for index in range(10)]
        train, dev = make_splits.split_dev(atoms)
        self.assertEqual(len(dev), 2)  # 20 帧 / 100 帧 = 20% ≥ 15%，10 帧不够
        self.assertEqual(len(train), 8)

    def test_dev_uses_integer_comparison(self) -> None:
        atoms = [atom(f"a{index}", frames=1, layouts=["default"]) for index in range(20)]
        _, dev = make_splits.split_dev(atoms)
        self.assertEqual(len(dev), 3)  # 20·3 = 60 ≥ 3·20 = 60


class AssignmentIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.atoms = [
            atom("a", frames=20, layouts=["default"], non_floor=2),
            atom("b", frames=20, layouts=["scene-004"], non_floor=3, d3=True),
            atom("c", frames=40, layouts=["default"], non_floor=1, d3=True),
            atom("d", frames=40, layouts=["scene-004"]),
            atom("e", frames=40, layouts=["default"]),
        ]

    def test_four_blocks_are_pairwise_disjoint(self) -> None:
        result = make_splits.assign_splits(self.atoms, [])
        self.assertTrue(result["leakage_assertions"]["pairwise_disjoint"])
        ids = [
            set(result["atom_assignment"][split]) for split in make_splits.SPLITS
        ]
        for left in range(len(ids)):
            for right in range(left + 1, len(ids)):
                self.assertEqual(ids[left] & ids[right], set())

    def test_test_side_non_floor_frames_are_dropped_not_recycled(self) -> None:
        """连带规则：test/D3 原子的非 test 资格帧整体退出，不得回流训练侧。"""
        result = make_splits.assign_splits(self.atoms, [])
        test_atoms = set(result["atom_assignment"][make_splits.SPLIT_TEST])
        dropped = set(result["dropped_frames"])
        for atom_id in test_atoms:
            for frame in (f"{atom_id}/n0",):
                if frame in dropped:
                    self.assertNotIn(frame, result["frames"][make_splits.SPLIT_TRAIN])

    def test_leakage_assertion_raises_on_overlap(self) -> None:
        shared = atom("shared", frames=5, layouts=["default"])
        assignment = {
            make_splits.SPLIT_TRAIN: [shared],
            make_splits.SPLIT_DEV: [],
            make_splits.SPLIT_TEST: [shared],
            make_splits.SPLIT_D3: [],
        }
        frames = {split: [] for split in make_splits.SPLITS}
        with self.assertRaises(make_splits.SplitError):
            make_splits.assert_no_leakage(assignment, frames)

    def test_held_out_objects_never_become_training_referents(self) -> None:
        make_splits.assert_held_out_never_referenced(
            ["Vehicle_Taxi"], [{"object_id": "Vehicle_Bus_color01"}]
        )
        with self.assertRaises(make_splits.SplitError):
            make_splits.assert_held_out_never_referenced(
                ["Vehicle_Taxi"], [{"object_id": "Vehicle_Taxi"}]
            )


class ExposureTest(unittest.TestCase):
    def test_per_sample_roles_aggregate_to_four_sets(self) -> None:
        """BC-DATA-2：逐 (frame, object) 角色记录必须保留 dev/D3，不得省略。"""
        roles = [
            {"frame_id": "f1", "object_id": "o1", "split": "train", "role": "referent"},
            {"frame_id": "f2", "object_id": "o1", "split": "dev", "role": "distractor"},
            {"frame_id": "f3", "object_id": "o1", "split": "test", "role": "absent"},
            {"frame_id": "f4", "object_id": "o1", "split": "d3", "role": "referent"},
        ]
        table = make_splits.exposure_matrix(roles)
        entry = table["per_object"]["o1"]
        self.assertEqual(entry["train"]["referent"], 1)
        self.assertEqual(entry["dev"]["distractor"], 1)
        self.assertEqual(entry["test"]["absent"], 1)
        self.assertEqual(entry["d3"]["referent"], 1)
        self.assertEqual(table["sample_count"], 4)

    def test_frozen_wording_is_carried(self) -> None:
        table = make_splits.exposure_matrix([])
        self.assertIn("从未作为训练指称目标的对象", table["wording"])
        self.assertIn("禁止", table["wording"])

    def test_unknown_split_or_role_is_rejected(self) -> None:
        with self.assertRaises(make_splits.SplitError):
            make_splits.exposure_matrix(
                [{"frame_id": "f", "object_id": "o", "split": "eval", "role": "referent"}]
            )
        with self.assertRaises(make_splits.SplitError):
            make_splits.exposure_matrix(
                [{"frame_id": "f", "object_id": "o", "split": "train", "role": "hero"}]
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
