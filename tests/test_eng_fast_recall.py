#!/usr/bin/env python3
"""P1-ENG-FAST-001 AC-2/AC-3：分桶召回（双 IoU、斜距/轴向深度分表、实例标记、无单一总召回）、
FP/帧与旧数复算对照。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_fast import common, recall  # noqa: E402
from tools.eng_fast.inputs import FrameRec, GTObject  # noqa: E402

BOX = (0.40, 0.40, 0.10, 0.10)  # 64×48 px → M 层


def frame(path: str, objects: list, target_box=BOX) -> FrameRec:
    return FrameRec("scout-1", "scout-1", 1, path, 0.0, True, bool(objects), target_box, objects)


class Buckets(unittest.TestCase):
    def test_bins_and_strata(self) -> None:
        self.assertEqual(common.distance_bin(34.99), "<35")
        self.assertEqual(common.distance_bin(35.0), "35-50")
        self.assertEqual(common.distance_bin(64.99), "50-65")
        self.assertEqual(common.distance_bin(65.0), ">=65")
        self.assertEqual(common.distance_bin(None), "NA")
        self.assertEqual(common.stratum_of(31.9), "S")
        self.assertEqual(common.stratum_of(32.0), "M")
        self.assertEqual(common.stratum_of(64.0), "L")

    def test_double_iou_and_instance_rows(self) -> None:
        target = GTObject("target-0", common.TARGET_KIND_PRIMITIVE, BOX, 70.0, "car", "red", "target")
        in_bank = GTObject("Vehicle_Bus (1)", common.TARGET_KIND_CATALOG, (0.0, 0.0, 0.2, 0.2), None, "bus")
        unknown = GTObject(None, common.TARGET_KIND_CATALOG, (0.7, 0.7, 0.05, 0.05), 20.0, None)
        frames = [frame("a.jpg", [target, in_bank, unknown])]
        # 检测：与 target IoU = 0.4（只过 0.30）；与 in_bank 完全重合；unknown 漏检。
        dets = {"a.jpg": [[0.40, 0.40, 0.10, 0.04, 0.9, 1.0], [0.0, 0.0, 0.2, 0.2, 0.8, 0.0]]}
        outcomes = recall.object_outcomes(frames, dets, {"Vehicle_Bus (1)"})
        by_id = {o["object_id"]: o for o in outcomes}
        self.assertTrue(by_id["target-0"]["hit_030"])
        self.assertFalse(by_id["target-0"]["hit_050"])
        self.assertEqual(by_id["target-0"]["instance"], "same_instance_by_design")
        self.assertEqual(by_id["Vehicle_Bus (1)"]["instance"], "same_instance_in_bank")
        self.assertEqual(by_id[None]["instance"], "INSTANCE_UNKNOWN")
        table = recall.bucket_table(outcomes)
        self.assertEqual(
            sorted(table),
            ["catalog_vehicle|INSTANCE_UNKNOWN", "catalog_vehicle|same_instance_in_bank", "red_primitive|same_instance_by_design"],
        )
        cell = table["red_primitive|same_instance_by_design"]["stratum_x_distance"]["M|>=65"]
        self.assertEqual((cell["n"], cell["hit_030"], cell["hit_050"]), (1, 1, 0))
        # 不出现未分桶的单一总召回：顶层只有 种类|实例 键，每键只有分桶子表。
        for value in table.values():
            self.assertEqual(sorted(value), ["by_distance", "by_stratum", "stratum_x_distance"])

    def test_missing_detection_cache_fails(self) -> None:
        target = GTObject("target-0", common.TARGET_KIND_PRIMITIVE, BOX, 30.0)
        with self.assertRaises(KeyError):
            recall.object_outcomes([frame("missing.jpg", [target])], {}, set())

    def test_fp_per_frame_is_descriptive(self) -> None:
        target = GTObject("target-0", common.TARGET_KIND_PRIMITIVE, BOX, 30.0)
        frames = [frame("a.jpg", [target]), frame("b.jpg", [])]
        dets = {"a.jpg": [[0.40, 0.40, 0.10, 0.10, 0.9, 1.0], [0.9, 0.9, 0.05, 0.05, 0.5, 0.0]], "b.jpg": [[0.1, 0.1, 0.1, 0.1, 0.5, 0.0]]}
        fp = recall.fp_per_frame(frames, dets)
        self.assertEqual((fp["frames"], fp["detections"], fp["unmatched_detections"]), (2, 3, 2))
        self.assertEqual(fp["fp_per_frame"], 1.0)


class LegacyAlignment(unittest.TestCase):
    def test_alignment_and_missing_pair_policy(self) -> None:
        legacy = {
            "samples": [
                {"tick_index": 0, "status": "MISSING_IMAGE_TRUTH_PAIR", "recall_hit": False},
                {"tick_index": 1, "status": "REMOTE_VISIBLE", "frame_id": 7, "recall_hit": False, "maximum_target_iou": 0.1},
                {"tick_index": 2, "accounting_class": "PAIRED_VISIBLE", "frame_id": 8, "recall_hit": True, "maximum_target_iou": 1.0},
            ]
        }
        frames = {
            7: FrameRec("scout-1", "scout-1", 7, "7.jpg", 0.0, True, True, BOX, []),
            8: FrameRec("scout-1", "scout-1", 8, "8.jpg", 0.0, True, True, BOX, []),
        }
        dets = {"7.jpg": [[0.0, 0.0, 0.05, 0.05, 0.9, 0.0]], "8.jpg": [[0.40, 0.40, 0.10, 0.10, 0.9, 0.0]]}
        aligned = recall.legacy_alignment(legacy, frames, dets, expected={"hits": 1, "denominator": 3})
        self.assertTrue(aligned["aligned"])
        self.assertEqual(aligned["recomputed"], {"hits": 1, "denominator": 3})
        misaligned = recall.legacy_alignment(legacy, frames, dets, expected={"hits": 0, "denominator": 3})
        self.assertEqual(misaligned["disposition"], "MISALIGNED_STOP_CITING_LEGACY")
        flipped = {"7.jpg": dets["8.jpg"], "8.jpg": dets["7.jpg"]}
        per_tick = recall.legacy_alignment(legacy, frames, flipped, expected={"hits": 1, "denominator": 3})
        self.assertEqual(per_tick["per_tick_hit_mismatches"], [1, 2])
        self.assertFalse(per_tick["aligned"])


if __name__ == "__main__":
    unittest.main()
