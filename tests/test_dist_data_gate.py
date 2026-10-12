"""S7 候选冻结、F1–F4 与 G0 门判定（§2.8 / §5，BC-DATA-1）。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import contract, g0_report, make_splits  # noqa: E402


def candidate(
    frame: str,
    object_id: str,
    *,
    program=None,
    usage="VALID_FORMAL",
    floor=True,
    station="1:1:1:1",
):
    return {
        "frame_id": frame,
        "object_id": object_id,
        "program": program or {"target": {"class": "taxi"}},
        "program_kind": "attribute" if program is None or "relation" not in program else "relational",
        "usage_class": usage,
        "family": "fam",
        "layout_class": "default",
        "station_key": station,
        "floor_usage": usage in contract.FLOOR_USAGE_CLASSES,
        "pre_split_floor_eligible": floor,
    }


def entry(frame: str, *, split="train", station="1:1:1:1", usage="VALID_FORMAL", unbounded=False):
    return {
        "frame_id": frame,
        "family": "fam",
        "layout_class": "default",
        "usage_class": usage,
        "layout_binding_valid": True,
        "sidecar_complete": True,
        "target_unbounded": unbounded,
        "split": split,
        "station_bin": {"key": station},
        "referable": [],
        "blocking": [],
        "co_visible_count": 1,
        "objects": [],
        "status_histogram": {status: 0 for status in contract.OBJECT_STATUSES},
    }


class FreezeTest(unittest.TestCase):
    def test_candidates_get_split_atom_and_floor_marks(self) -> None:
        frozen = g0_report.freeze_mother_candidates(
            [candidate("f1", "Vehicle_Taxi")],
            {"f1": "train"},
            {"f1": "atom-1"},
            ["Vehicle_Bus_color01"],
        )
        item = frozen["candidates"][0]
        self.assertEqual(item["candidate_id"], "f1|Vehicle_Taxi")
        self.assertEqual(item["split"], "train")
        self.assertEqual(item["atom_id"], "atom-1")
        self.assertTrue(item["floor_eligible"])
        self.assertFalse(item["held_out_object"])
        self.assertFalse(item["train_augment_only"])

    def test_train_augment_usage_is_marked_and_never_floor(self) -> None:
        frozen = g0_report.freeze_mother_candidates(
            [candidate("f1", "Vehicle_Taxi", usage="SMOKE", floor=False)],
            {"f1": "train"},
            {"f1": "atom-1"},
            [],
        )
        item = frozen["candidates"][0]
        self.assertTrue(item["train_augment_only"])
        self.assertFalse(item["floor_eligible"])

    def test_missing_split_or_atom_is_a_hard_error(self) -> None:
        with self.assertRaises(g0_report.GateError):
            g0_report.freeze_mother_candidates(
                [candidate("f1", "Vehicle_Taxi")], {}, {"f1": "atom-1"}, []
            )
        with self.assertRaises(g0_report.GateError):
            g0_report.freeze_mother_candidates(
                [candidate("f1", "Vehicle_Taxi")], {"f1": "train"}, {}, []
            )

    def test_duplicate_pairs_are_rejected(self) -> None:
        with self.assertRaises(g0_report.GateError):
            g0_report.freeze_mother_candidates(
                [candidate("f1", "Vehicle_Taxi"), candidate("f1", "Vehicle_Taxi")],
                {"f1": "train"},
                {"f1": "atom-1"},
                [],
            )

    def test_candidate_ids_are_sorted(self) -> None:
        frozen = g0_report.freeze_mother_candidates(
            [candidate("f2", "b"), candidate("f1", "a")],
            {"f1": "train", "f2": "train"},
            {"f1": "atom-1", "f2": "atom-1"},
            [],
        )
        self.assertEqual(frozen["candidate_ids"], ["f1|a", "f2|b"])


class FloorTest(unittest.TestCase):
    def test_f1_counts_dual_verified_objects_and_classes(self) -> None:
        objects = {}
        for index in range(60):
            objects[f"o{index}"] = {"class": contract.CLASS_WORDS[index % 6]}
        catalog = {"objects": objects, "dual_verified_object_ids": sorted(objects)}
        result = g0_report.compute_f1(catalog)
        self.assertEqual(result["value"], 60)
        self.assertEqual(len(result["classes_with_dual_verified"]), 6)
        self.assertTrue(result["passed"])

    def test_f1_fails_below_sixty(self) -> None:
        objects = {f"o{index}": {"class": contract.CLASS_WORDS[index % 6]} for index in range(59)}
        catalog = {"objects": objects, "dual_verified_object_ids": sorted(objects)}
        self.assertFalse(g0_report.compute_f1(catalog)["passed"])

    def test_f1_fails_below_six_classes(self) -> None:
        objects = {f"o{index}": {"class": contract.CLASS_WORDS[index % 5]} for index in range(70)}
        catalog = {"objects": objects, "dual_verified_object_ids": sorted(objects)}
        self.assertFalse(g0_report.compute_f1(catalog)["passed"])

    def test_f2_counts_non_empty_station_bins(self) -> None:
        entries = [
            entry(f"f{index}", split="train", station=f"{index}:0:0:0") for index in range(40)
        ] + [entry(f"t{index}", split="test", station=f"t{index}:0:0:0") for index in range(8)]
        result = g0_report.compute_f2(entries)
        self.assertEqual(result["global"], 48)
        self.assertEqual(result["per_split"]["test"], 8)
        self.assertTrue(result["passed"])

    def test_f2_ignores_frames_without_a_station_key(self) -> None:
        entries = [entry("f1", station=None)]
        self.assertEqual(g0_report.compute_f2(entries)["global"], 0)

    def test_f2_excludes_target_unbounded_frames(self) -> None:
        entries = [entry("f1", station="a", unbounded=True)]
        self.assertEqual(g0_report.compute_f2(entries)["global"], 0)

    def test_f3_counts_object_station_units_once(self) -> None:
        candidates = [
            candidate(f"f{index}", "Vehicle_Taxi", station="1:1:1:1") for index in range(5)
        ]
        frozen = g0_report.freeze_mother_candidates(
            candidates,
            {f"f{index}": "train" for index in range(5)},
            {f"f{index}": "atom-1" for index in range(5)},
            [],
        )
        stations = {f"f{index}": "1:1:1:1" for index in range(5)}
        result = g0_report.compute_f3(frozen, stations)
        self.assertEqual(result["train_dev"], 1)  # 同单元多帧计 1

    def test_f3_ignores_relational_programs(self) -> None:
        relational = candidate(
            "f1",
            "Vehicle_Taxi",
            program={
                "target": {"class": "taxi"},
                "relation": {"type": "nearest_to", "ref": {"class": "bus"}},
            },
        )
        frozen = g0_report.freeze_mother_candidates(
            [relational], {"f1": "train"}, {"f1": "atom-1"}, []
        )
        result = g0_report.compute_f3(frozen, {"f1": "1:1:1:1"})
        self.assertEqual(result["train_dev"], 0)

    def test_f4_counts_atom_object_clusters(self) -> None:
        candidates = [
            candidate("f1", "Vehicle_Taxi"),
            candidate("f2", "Vehicle_Taxi"),
            candidate("f3", "Vehicle_Bus_color01"),
        ]
        frozen = g0_report.freeze_mother_candidates(
            candidates,
            {"f1": "train", "f2": "train", "f3": "train"},
            {"f1": "atom-1", "f2": "atom-1", "f3": "atom-2"},
            [],
        )
        result = g0_report.compute_f4(frozen)
        self.assertEqual(result["train_dev"], 2)
        self.assertIn("(atom_id, object_id)", result["resampling_unit"])


class GateDecisionTest(unittest.TestCase):
    def _report(self, catalog, entries, frozen):
        return g0_report.build_g0_report(
            entries=entries,
            frozen=frozen,
            field_catalog=catalog,
            splits_payload={
                "atom_assignment": {split: [] for split in make_splits.SPLITS},
                "frame_counts": {split: 0 for split in make_splits.SPLITS},
                "d3_holdout_empty": True,
                "dropped_frames": [],
                "exposure_matrix": {"per_object": {}},
            },
            layout_payload={"cross_validation": {}},
            audit_results={},
            relation_availability={},
        )

    def test_gate_closes_when_any_floor_is_unmet(self) -> None:
        frozen = g0_report.freeze_mother_candidates(
            [candidate("f1", "Vehicle_Taxi")], {"f1": "train"}, {"f1": "atom-1"}, []
        )
        report = self._report(
            {"objects": {}, "dual_verified_object_ids": []}, [entry("f1")], frozen
        )
        self.assertEqual(report["gate"], g0_report.GATE_INSUFFICIENT)
        self.assertEqual(report["unmet_floors"], ["F1", "F2", "F3", "F4"])

    def test_report_carries_every_stratified_denominator(self) -> None:
        frozen = g0_report.freeze_mother_candidates(
            [candidate("f1", "Vehicle_Taxi")], {"f1": "train"}, {"f1": "atom-1"}, []
        )
        report = self._report(
            {"objects": {}, "dual_verified_object_ids": []}, [entry("f1")], frozen
        )
        for key in (
            "frames_by_split",
            "frames_by_layout_class",
            "frames_by_usage_class",
            "frames_by_station",
            "candidates_by_split",
            "candidates_by_object",
            "candidates_by_usage_class",
            "candidates_by_program_kind",
        ):
            self.assertIn(key, report["stratified_denominators"])
        self.assertIn("target_unbounded_frames", report["exclusion_histogram"])
        self.assertIn("registered_risk", report["exclusion_histogram"])
        self.assertIn("co_visibility_distribution", report)

    def test_gate_note_states_the_terminal(self) -> None:
        frozen = g0_report.freeze_mother_candidates([], {}, {}, [])
        report = self._report(
            {"objects": {}, "dual_verified_object_ids": []}, [], frozen
        )
        self.assertIn("INSUFFICIENT_SYMBOLIC_GROUNDING_DATA", report["gate_note"])
        self.assertIn("S8 永不执行", report["gate_note"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
