#!/usr/bin/env python3
"""P1-ENG-FAST-001 AC-1：参考库确定选择规则、原子隔离断言（含反例）、原子查表与候选集口径。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_fast import inputs  # noqa: E402


def vehicle(object_id: str, class_word: str | None, side_px: float, x: float = 0.1, y: float = 0.1) -> dict:
    return {
        "object_id": object_id,
        "class_word": class_word,
        "color_word": None,
        "box": [x, y, side_px / 640.0, side_px / 480.0],
        "depth_m": 30.0,
        "referable": True,
    }


def frame(frame_id: str, vehicles: list, atom: str = "A-train", family: str = "fam", dynamic=None) -> dict:
    return {
        "frame_id": frame_id,
        "family": family,
        "split": "train",
        "atom": atom,
        "usable": True,
        "vehicles": vehicles,
        "dynamic": dynamic,
    }


class BankSelection(unittest.TestCase):
    def test_greedy_covers_classes_with_tie_breaks(self) -> None:
        pool = [
            frame("f1", [vehicle("v1", "bus", 80), vehicle("v2", "taxi", 70)]),
            frame("f2", [vehicle("v3", "bus", 90), vehicle("v4", "taxi", 65), vehicle("v5", "suv", 20)]),
            frame("f3", [vehicle("v6", "car", 64), vehicle("v7", "car", 100, 0.5, 0.5)]),
        ]
        sha = {"f1": "b" * 64, "f2": "c" * 64, "f3": "a" * 64}
        bank = inputs.select_bank(pool, sha)
        # 第一轮 f1/f2 都新增 2 类，并列取 OK 车辆数多者 f2；第二轮只有 f3 新增 car（取面积最大 v7）。
        self.assertEqual([ref["frame_id"] for ref in bank["vehicle"]], ["f2", "f3"])
        self.assertEqual([b["object_id"] for b in bank["vehicle"][0]["boxes"]], ["v3", "v4"])
        self.assertEqual([b["object_id"] for b in bank["vehicle"][1]["boxes"]], ["v7"])
        self.assertEqual(bank["vehicle_status"], "BANK_PARTIAL(3/9)")
        self.assertEqual(bank["target_primitive_status"], "N/A(BANK_EMPTY)")

    def test_sha_breaks_remaining_ties_and_frame_cap(self) -> None:
        pool = [frame(f"f{i}", [vehicle(f"v{i}", word, 70)]) for i, word in enumerate(inputs.CLASS_WORDS)]
        sha = {f"f{i}": f"{9 - i:064d}" for i in range(9)}
        bank = inputs.select_bank(pool, sha)
        self.assertEqual(len(bank["vehicle"]), inputs.VEHICLE_BANK_MAX_FRAMES)
        self.assertEqual(bank["vehicle"][0]["frame_id"], "f8")  # sha 字典序最小
        self.assertTrue(bank["vehicle_status"].startswith("BANK_PARTIAL(6/9)"))

    def test_primitive_largest_area_and_empty_pool(self) -> None:
        dyn_small = {"definite": True, "box": [0.1, 0.1, 40 / 640, 40 / 480]}
        dyn_big = {"definite": True, "box": [0.1, 0.1, 90 / 640, 90 / 480]}
        dyn_tiny = {"definite": True, "box": [0.1, 0.1, 20 / 640, 20 / 480]}
        pool = [frame("p1", [], dynamic=dyn_small), frame("p2", [], dynamic=dyn_big), frame("p3", [], dynamic=dyn_tiny)]
        bank = inputs.select_bank(pool, {"p1": "1" * 64, "p2": "2" * 64, "p3": "0" * 64})
        self.assertEqual(bank["target_primitive"]["frame_id"], "p2")
        empty = inputs.select_bank([], {})
        self.assertEqual(empty["vehicle_status"], "N/A(BANK_EMPTY)")
        self.assertEqual(empty["target_primitive_status"], "N/A(BANK_EMPTY)")


class AtomIsolation(unittest.TestCase):
    def splits(self) -> inputs.Splits:
        return inputs.Splits(
            split_of={"train/a.jpg": "train", "dev/b.jpg": "dev", "test/c.jpg": "test", "test/d.jpg": "test"},
            atom_of_family={"fa": "A-train", "fb": "A-dev", "fc": "A-test1", "fd": "A-test2"},
            atoms_of_split={"train": ["A-train"], "dev": ["A-dev"], "test": ["A-test1", "A-test2"]},
            families_of_atom={"A-train": ["fa"], "A-dev": ["fb"], "A-test1": ["fc"], "A-test2": ["fd"]},
            sha256="x",
            pairwise_disjoint=True,
        )

    def test_atom_lookup_and_missing(self) -> None:
        splits = self.splits()
        self.assertEqual(splits.atom_of("test/d.jpg", "fd"), "A-test2")
        self.assertEqual(splits.atom_of("dev/b.jpg", None), "A-dev")
        with self.assertRaisesRegex(inputs.InputFailure, "SPLIT_LOOKUP_MISSING"):
            splits.atom_of("nowhere.jpg", "fa")
        with self.assertRaisesRegex(inputs.InputFailure, "SPLIT_LOOKUP_MISSING"):
            splits.atom_of("test/c.jpg", None)  # test 有两个原子且无族 → 不猜

    def test_pool_excludes_evaluated_atom(self) -> None:
        splits = self.splits()
        index = {
            "train/a.jpg": {"frame_id": "train/a.jpg", "family": "fa", "usable": True, "vehicles": [], "dynamic": None},
            "dev/b.jpg": {"frame_id": "dev/b.jpg", "family": "fb", "usable": True, "vehicles": [], "dynamic": None},
            "test/c.jpg": {"frame_id": "test/c.jpg", "family": "fc", "usable": True, "vehicles": [], "dynamic": None},
        }
        self.assertEqual([f["frame_id"] for f in inputs.bank_pool(index, splits, ["A-dev", "A-test1", "A-test2"])], ["train/a.jpg"])
        self.assertEqual(
            [f["frame_id"] for f in inputs.bank_pool(index, splits, ["A-test1", "A-test2"])], ["dev/b.jpg", "train/a.jpg"]
        )

    def test_reference_from_evaluated_atom_fails(self) -> None:
        """AC-1 反例：参考帧来自被评原子 → 失败（帧 sha 不同也不能放行）。"""
        bank = {"vehicle": [{"frame_id": "dev/b.jpg", "atom": "A-dev", "boxes": []}], "target_primitive": None}
        with self.assertRaisesRegex(inputs.InputFailure, r"sha∩=\[\] atom∩=\['A-dev'\]"):
            inputs.bank_assertions(bank, {"eval-sha"}, {"A-dev"}, {"dev/b.jpg": "ref-sha"})
        with self.assertRaisesRegex(inputs.InputFailure, r"sha∩=\['ref-sha'\] atom∩=\[\]"):
            inputs.bank_assertions(bank, {"ref-sha"}, {"A-test1"}, {"dev/b.jpg": "ref-sha"})
        ok = inputs.bank_assertions(bank, {"eval-sha"}, {"A-test1"}, {"dev/b.jpg": "ref-sha"})
        self.assertTrue(ok["passed"])


class CandidateSet(unittest.TestCase):
    def test_vehicles_plus_frame_level_dynamic_target_row_major(self) -> None:
        row = {
            "vehicles": [vehicle("b", "bus", 40, 0.5, 0.2), vehicle("a", "taxi", 40, 0.1, 0.2), vehicle("c", "suv", 40, 0.0, 0.6)],
            "dynamic": {"definite": True, "box": [0.3, 0.1, 0.05, 0.05], "class_word": "car", "color_word": "red"},
        }
        candidates = inputs.candidate_set(row)
        self.assertEqual([c["object_id"] for c in candidates], ["dynamic-target", "a", "b", "c"])
        self.assertEqual([c["index"] for c in candidates], [1, 2, 3, 4])
        row["dynamic"]["definite"] = False
        self.assertNotIn("dynamic-target", [c["object_id"] for c in inputs.candidate_set(row)])
        self.assertEqual(inputs.candidate_set({"vehicles": [], "dynamic": None}), [])


class LatencyHostCheck(unittest.TestCase):
    def test_unity_hub_is_not_the_editor(self) -> None:
        from tools.eng_fast.run_more import unity_editor_running  # noqa: PLC0415

        hub = "2633 /Applications/Unity Hub.app/Contents/MacOS/Unity Hub\n2639 /Applications/Unity Hub.app/Contents/Frameworks/x"
        editor = "88 /Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity -projectPath p"
        self.assertFalse(unity_editor_running(hub))
        self.assertTrue(unity_editor_running(hub + "\n" + editor))
        self.assertFalse(unity_editor_running(""))


if __name__ == "__main__":
    unittest.main()
