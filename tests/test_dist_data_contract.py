"""S0 冻结常量与派生规则（P1-VLM-DATA-001 §2.1/§2.6/§5.2，BC-DATA-1）。"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import artifacts, contract  # noqa: E402


class ClassMappingTest(unittest.TestCase):
    def test_nine_classes_frozen(self) -> None:
        self.assertEqual(len(contract.CLASS_MAP), 9)
        self.assertEqual(
            sorted(contract.CLASS_MAP.values()),
            [
                "ambulance",
                "bus",
                "car",
                "container truck",
                "pickup truck",
                "police car",
                "suv",
                "taxi",
                "truck",
            ],
        )

    def test_prefix_resolution_is_longest_first(self) -> None:
        cases = {
            "Vehicle_Car_color01 (2)": "car",
            "Vehicle_Container_color02 (5)": "container truck",
            "Vehicle_Police Car (3)": "police car",
            "Vehicle_Truck_color03": "truck",
            "Vehicle_Pick up Truck_color02 (8)": "pickup truck",
            "Vehicle_SUV_color03 (7)": "suv",
            "Vehicle_Taxi (12)": "taxi",
            "Vehicle_Ambulance": "ambulance",
            "Vehicle_Bus_color02 (1)": "bus",
        }
        for name, expected in cases.items():
            self.assertEqual(contract.class_for_scene_object(name), expected, name)

    def test_non_vehicle_is_not_classified(self) -> None:
        self.assertIsNone(contract.class_for_scene_object("Building Sky_big_color01"))
        self.assertIsNone(contract.class_for_scene_object("Tree_color02 (3)"))

    def test_skin_code_is_not_a_colour(self) -> None:
        """`_colorNN` 是资产皮肤代号，不是颜色（章程 R2C-6）。"""
        self.assertEqual(contract.skin_code_for_scene_object("Vehicle_Bus_color02 (1)"), "color02")
        self.assertEqual(contract.skin_code_for_scene_object("Vehicle_Taxi (2)"), "")
        self.assertEqual(
            contract.color_group_key("Vehicle_Bus_color02 (1)"), "Vehicle_Bus_color02|color02"
        )
        self.assertNotIn("color02", contract.COLOR_WORDS)


class HeldOutFormulaTest(unittest.TestCase):
    def test_matches_frozen_table(self) -> None:
        """§2.5：23/20/13/12/9/8/6/5/5 → 7/6/4/4/3/2/2/2/2，合计 32。"""
        sizes = [23, 20, 13, 12, 9, 8, 6, 5, 5]
        expected = [7, 6, 4, 4, 3, 2, 2, 2, 2]
        actual = [contract.held_out_count(size) for size in sizes]
        self.assertEqual(actual, expected)
        self.assertEqual(sum(actual), 32)

    def test_small_class_still_holds_one(self) -> None:
        self.assertEqual(contract.held_out_count(1), 1)
        self.assertEqual(contract.held_out_count(0), 0)

    def test_integer_arithmetic_only(self) -> None:
        for size in range(1, 200):
            self.assertIsInstance(contract.held_out_count(size), int)


class HueBandTest(unittest.TestCase):
    def test_red_band_wraps_zero(self) -> None:
        self.assertEqual(contract.hue_band(0.0), "red")
        self.assertEqual(contract.hue_band(350.0), "red")
        self.assertEqual(contract.hue_band(14.9), "red")

    def test_band_boundaries_are_half_open(self) -> None:
        self.assertEqual(contract.hue_band(15.0), "orange")
        self.assertEqual(contract.hue_band(45.0), "yellow")
        self.assertEqual(contract.hue_band(70.0), "green")
        self.assertEqual(contract.hue_band(170.0), "blue")
        self.assertEqual(contract.hue_band(260.0), "purple")

    def test_unassigned_interval_returns_none(self) -> None:
        self.assertIsNone(contract.hue_band(300.0))
        self.assertIsNone(contract.hue_band(330.0))


class FrozenFloorsTest(unittest.TestCase):
    def test_f1_to_f4_match_acceptance_round_3(self) -> None:
        floors = contract.FLOORS
        self.assertEqual(floors["F1"]["min_objects"], 60)
        self.assertEqual(floors["F1"]["min_classes_with_dual_verified"], 6)
        self.assertEqual(floors["F2"]["min_global"], 40)
        self.assertEqual(floors["F2"]["min_test"], 8)
        self.assertEqual(floors["F3"]["min_train_dev"], 60)
        self.assertEqual(floors["F3"]["min_test"], 25)
        self.assertEqual(floors["F3"]["min_test_heldout_units"], 8)
        self.assertEqual(floors["F3"]["min_train_classes"], 5)
        self.assertEqual(floors["F3"]["min_test_classes"], 4)
        self.assertEqual(floors["F4"]["min_train_dev"], 25)
        self.assertEqual(floors["F4"]["min_test"], 10)

    def test_projection_and_audit_constants(self) -> None:
        self.assertEqual(contract.THETA_OCC, 0.5)
        self.assertEqual(contract.NEAR_CLIP_Z_M, 0.3)
        self.assertEqual(contract.MIN_VISIBLE_SIDE_PX, 12)
        self.assertEqual(contract.TRUNCATION_VISIBLE_AREA_RATIO, 0.25)
        self.assertEqual(contract.PHASH_NEAR_DUPLICATE_HAMMING, 8)
        self.assertEqual(contract.AUDIT_A2_PANEL_SAMPLES, 200)
        self.assertEqual(contract.AUDIT_A3_PANEL_SAMPLES, 100)
        self.assertEqual(contract.AUDIT_MAX_ATTEMPTS, 3)
        self.assertEqual(contract.AUDIT_MAX_CATALOG_SUPERSESSIONS, 2)
        self.assertEqual(contract.SPLIT_MIN_ATOMS, 2)
        self.assertEqual(contract.SPLIT_MAX_ATOMS, 20)


class ContractDocumentTest(unittest.TestCase):
    def test_document_is_deterministic_and_hashable(self) -> None:
        first = artifacts.canonical_json_bytes(contract.contract_document())
        second = artifacts.canonical_json_bytes(contract.contract_document())
        self.assertEqual(first, second)
        self.assertEqual(len(artifacts.sha256_hex(first)), 64)

    def test_document_carries_every_frozen_block(self) -> None:
        document = json.loads(
            artifacts.canonical_json_bytes(contract.contract_document()).decode("utf-8")
        )
        for key in (
            "class_map",
            "color",
            "projection",
            "station_bins",
            "cross_check",
            "splits",
            "relations",
            "audit",
            "usage_classes",
            "floors",
            "verifier",
            "base_geometry",
        ):
            self.assertIn(key, document)

    def test_base_geometry_pin_matches_disk(self) -> None:
        path = PROJECT_ROOT / contract.BASE_GEOMETRY_PATH
        self.assertTrue(path.exists())
        self.assertEqual(artifacts.sha256_file(path), contract.BASE_GEOMETRY_SHA256)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
