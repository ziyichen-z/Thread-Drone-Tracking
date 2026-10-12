"""附录 A 冻结根清单：glob 语义、互不重叠、用途类资格与真值 join。"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import contract, roots  # noqa: E402


class GlobSemanticsTest(unittest.TestCase):
    def test_star_does_not_cross_slash(self) -> None:
        regex = re.compile(roots.glob_to_regex("a/*/c.jpg"))
        self.assertTrue(regex.match("a/b/c.jpg"))
        self.assertFalse(regex.match("a/b/x/c.jpg"))

    def test_double_star_crosses_any_depth(self) -> None:
        regex = re.compile(roots.glob_to_regex("a/**/c.jpg"))
        self.assertTrue(regex.match("a/c.jpg"))
        self.assertTrue(regex.match("a/b/c.jpg"))
        self.assertTrue(regex.match("a/b/x/y/c.jpg"))

    def test_bracket_expression(self) -> None:
        regex = re.compile(roots.glob_to_regex("r20-follow-[12]/pass/f.jpg"))
        self.assertTrue(regex.match("r20-follow-1/pass/f.jpg"))
        self.assertTrue(regex.match("r20-follow-2/pass/f.jpg"))
        self.assertFalse(regex.match("r20-follow-3/pass/f.jpg"))

    def test_anchored_at_both_ends(self) -> None:
        regex = re.compile(roots.glob_to_regex("runtime/frames/f.jpg"))
        self.assertFalse(regex.match("x/runtime/frames/f.jpg"))
        self.assertFalse(regex.match("runtime/frames/f.jpg.bak"))


class RootTableTest(unittest.TestCase):
    def test_rt_macro_is_expanded(self) -> None:
        for entry in roots.ROOT_TABLE:
            self.assertNotIn("<RT>", entry.pattern)

    def test_usage_classes_are_inside_the_closed_set(self) -> None:
        for entry in roots.ROOT_TABLE:
            self.assertIn(entry.usage_class, contract.USAGE_CLASSES)
            self.assertIn(entry.usage_class, roots.USAGE_ELIGIBILITY)
            self.assertIn(entry.usage_class, roots.USAGE_DECISION)

    def test_layout_classes_are_closed(self) -> None:
        for entry in roots.ROOT_TABLE:
            if entry.layout_class is not None:
                self.assertIn(entry.layout_class, roots.LAYOUT_CLASSES)

    def test_floor_eligibility_matches_contract(self) -> None:
        for usage, eligibility in roots.USAGE_ELIGIBILITY.items():
            self.assertEqual(
                eligibility["floor"], usage in contract.FLOOR_USAGE_CLASSES, usage
            )
            self.assertEqual(
                eligibility["mother"], usage in contract.MOTHER_USAGE_CLASSES, usage
            )

    def test_diagnostic_and_unreleased_never_reach_the_mother_set(self) -> None:
        """COORD-005：诊断通道产物不进证据链；未释放 Play 未获归因。"""
        for usage in ("DIAGNOSTIC_HOLD", "UNRELEASED_PLAY_HOLD"):
            self.assertFalse(roots.USAGE_ELIGIBILITY[usage]["mother"])
            self.assertFalse(roots.USAGE_ELIGIBILITY[usage]["floor"])
            self.assertFalse(roots.USAGE_ELIGIBILITY[usage]["test"])

    def test_train_augment_classes_never_count_towards_floors(self) -> None:
        for usage in contract.TRAIN_AUGMENT_USAGE_CLASSES:
            self.assertTrue(roots.USAGE_ELIGIBILITY[usage]["mother"])
            self.assertFalse(roots.USAGE_ELIGIBILITY[usage]["floor"])
            self.assertFalse(roots.USAGE_ELIGIBILITY[usage]["test"])


class NonOverlapTest(unittest.TestCase):
    def test_representative_paths_match_exactly_one_pattern(self) -> None:
        samples = [
            "runtime/test-results/p1-m3-body-001-arm-a-trial-3-post-run/frames/frame_0000000001.jpg",
            "runtime/test-results/p1-m3-body-001-arm-b-trial-1-post-run/frames/frame_0000000001.jpg",
            "runtime/frames.arm-b-trial-3-shared-residue-hold/frame_0000000907.jpg",
            "runtime/frames.arm-a-trial-1-void-attempt-2-hold/frame_0000000010.jpg",
            "runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames/frame_0000000000.jpg",
            "runtime/test-results/ut-p1-m2-rate-002-b2-formal/r20-follow-1/pass/frames/frame_0000000001.jpg",
            "runtime/frames.qual3-leftover-hold/frame_0000005200.jpg",
            "runtime/rate-study/P1-M2-RATE-003-CLOCKSMOKE/smoke-1/frames/frame_0000000001.jpg",
            "runtime/runs/p1-detect-001-qual-1/init-frame-box-preview.jpg",
            "docs/evidence/P1-M3-BODY-001-1b/frame_0000000001.jpg",
        ]
        for sample in samples:
            matches = roots.matching_entries(sample)
            self.assertEqual(len(matches), 1, f"{sample} → {[m.pattern for m in matches]}")

    def test_root_excluded_prefixes(self) -> None:
        self.assertTrue(roots.is_root_excluded("runtime/models/nanotrack-v2/sample.jpg"))
        self.assertTrue(roots.is_root_excluded("runtime/yoloe/assets/bus.jpg"))
        self.assertFalse(roots.is_root_excluded("runtime/frames.1b-diagnostic-hold/frame_0.jpg"))

    def test_active_bridge_directory_must_be_empty(self) -> None:
        self.assertIn("runtime/frames", roots.MUST_BE_EMPTY_DIRS)


class TruthJoinTest(unittest.TestCase):
    def test_m3_post_run_joins_its_run_directory(self) -> None:
        source = roots.truth_source_for(
            "runtime/test-results/p1-m3-body-001-arm-a-trial-3-post-run/frames/frame_0000000012.jpg"
        )
        self.assertEqual(
            source, ("runtime/runs/p1-m3-body-001-arm-a-trial-3/m3_body_truth.jsonl", "m3")
        )

    def test_b3_residue_hold_joins_b3_run(self) -> None:
        source = roots.truth_source_for(
            "runtime/frames.arm-b-trial-3-shared-residue-hold/frame_0000000907.jpg"
        )
        self.assertEqual(
            source, ("runtime/runs/p1-m3-body-001-arm-b-trial-3/m3_body_truth.jsonl", "m3")
        )

    def test_void_hold_joins_root_level_truth(self) -> None:
        source = roots.truth_source_for(
            "runtime/frames.arm-a-trial-1-void-attempt-2-hold/frame_0000000005.jpg"
        )
        self.assertEqual(
            source,
            (
                "runtime/m3_body_truth.arm-a-trial-1-void-attempt-2-hold.jsonl",
                "m3",
            ),
        )

    def test_scouting_joins_per_frame_truth(self) -> None:
        source = roots.truth_source_for(
            "runtime/test-results/p1-scene-004-scout-4-closed-exchange/frames/frame_0000000042.jpg"
        )
        self.assertEqual(
            source,
            (
                "runtime/p1-scene-004-scouting/p1-scene-004-scout-4/truth/frame_0000000042.json",
                "scouting",
            ),
        )

    def test_families_without_per_frame_truth_return_none(self) -> None:
        """rate / scene-val / qual3-leftover / CLOCKSMOKE 走扫掠代理分支。"""
        for path in (
            "runtime/frames.qual3-leftover-hold/frame_0000005200.jpg",
            "runtime/test-results/ut-p1-scene-002-001-attempt3-pass/cleared-active/frames/frame_0000000001.jpg",
            "runtime/rate-study/P1-M2-RATE-003-CLOCKSMOKE/smoke-1/frames/frame_0000000001.jpg",
        ):
            self.assertIsNone(roots.truth_source_for(path))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
