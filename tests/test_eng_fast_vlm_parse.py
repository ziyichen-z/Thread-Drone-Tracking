#!/usr/bin/env python3
"""P1-ENG-FAST-001 AC-6：索引回复解析闭集、臂 B 分页合并闭集（含 INVALID）、臂 A 候选换算、
§3.5.1 评分口径、prompt 逐字段与臂 D 判定。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_fast import baseline, vlm_arms, vlm_remote  # noqa: E402
from tools.eng_fast.vlm_remote import INVALID, parse_index_reply  # noqa: E402
from tools.eng_sft import prompt_v2  # noqa: E402


def parsed(status: str, indices=()):
    return {"status": status, "indices": list(indices), "error": None}


class ParseReply(unittest.TestCase):
    def test_closed_set(self) -> None:
        allowed = [1, 2, 3]
        self.assertEqual(parse_index_reply('{"status": "unique", "index": 2}', allowed)["indices"], [2])
        self.assertEqual(parse_index_reply('```json\n{"status": "none"}\n```', allowed)["status"], "none")
        amb = parse_index_reply('{"status": "ambiguous", "indices": [3, 1]}', allowed)
        self.assertEqual((amb["status"], amb["indices"]), ("ambiguous", [1, 3]))
        cases = {
            "not json": "JSON_ERROR",
            '{"status": "unique"}': "SCHEMA_ERROR",
            '{"status": "unique", "index": true}': "SCHEMA_ERROR",
            '{"status": "unique", "index": 9}': "INDEX_OUT_OF_RANGE",
            '{"status": "ambiguous", "indices": [1, 1]}': "DUPLICATE_INDEX",
            '{"status": "ambiguous", "indices": [2]}': "AMBIGUOUS_FEWER_THAN_2",
            '{"status": "ambiguous", "indices": [2, 7]}': "INDEX_OUT_OF_RANGE",
            '{"status": "none", "index": 1}': "SCHEMA_ERROR",
            '{"status": "maybe"}': "SCHEMA_ERROR",
        }
        for raw, error in cases.items():
            with self.subTest(raw=raw):
                result = parse_index_reply(raw, allowed)
                self.assertEqual((result["status"], result["error"]), (INVALID, error))
        truncated = parse_index_reply('{"status": "none"}', allowed, finish_reason="length")
        self.assertEqual((truncated["status"], truncated["error"]), (INVALID, "TRUNCATED"))


class MergePages(unittest.TestCase):
    def test_closed_set_in_order(self) -> None:
        self.assertEqual(vlm_arms.merge_pages(0, [])["flag"], "K0")
        self.assertEqual(vlm_arms.merge_pages(20, [parsed("unique", [3]), None])["status"], "NOT_RUN")
        self.assertEqual(vlm_arms.merge_pages(20, [parsed(INVALID), parsed("unique", [18])])["status"], INVALID)
        both_amb = vlm_arms.merge_pages(20, [parsed("ambiguous", [1, 2]), parsed("unique", [17])])
        self.assertEqual((both_amb["status"], both_amb["indices"]), ("ambiguous", [1, 2, 17]))
        multi = vlm_arms.merge_pages(20, [parsed("unique", [4]), parsed("unique", [19])])
        self.assertEqual((multi["status"], multi["indices"]), ("ambiguous", [4, 19]))
        single = vlm_arms.merge_pages(20, [parsed("none"), parsed("unique", [19])])
        self.assertEqual((single["status"], single["indices"]), ("unique", [19]))
        self.assertEqual(vlm_arms.merge_pages(20, [parsed("none"), parsed("none")])["status"], "none")

    def test_retry_replaces_only_invalid_first_attempt(self) -> None:
        first_ok = {"parse": parsed("none")}
        first_bad = {"parse": parsed(INVALID)}
        retry = {"parse": parsed("unique", [2])}
        self.assertEqual(vlm_arms.final_page_result(first_ok, retry)["status"], "none")
        self.assertEqual(vlm_arms.final_page_result(first_bad, retry)["status"], "unique")
        self.assertEqual(vlm_arms.final_page_result(first_bad, None)["status"], INVALID)
        self.assertIsNone(vlm_arms.final_page_result(None, None))


CANDIDATES = [
    {"object_id": "a", "index": 1, "box": [0.1, 0.1, 0.2, 0.2]},
    {"object_id": "b", "index": 2, "box": [0.6, 0.6, 0.2, 0.2]},
]


class ArmA(unittest.TestCase):
    def test_candidate_matching(self) -> None:
        unique = vlm_arms.arm_a_selection({"status_pred": "unique", "boxes_1000": [[100, 100, 300, 300]]}, CANDIDATES)
        self.assertEqual((unique["object_ids"], unique["flag"]), (["a"], None))
        off = vlm_arms.arm_a_selection({"status_pred": "unique", "boxes_1000": [[0, 900, 50, 1000]]}, CANDIDATES)
        self.assertEqual((off["object_ids"], off["flag"]), ([], "NO_CANDIDATE_MATCH"))
        amb = vlm_arms.arm_a_selection(
            {"status_pred": "ambiguous", "boxes_1000": [[100, 100, 300, 300], [600, 600, 800, 800]]}, CANDIDATES
        )
        self.assertEqual(amb["object_ids"], ["a", "b"])
        self.assertEqual(vlm_arms.arm_a_selection({"status_pred": None}, CANDIDATES)["status"], INVALID)


class Scoring(unittest.TestCase):
    def test_row_outcomes_by_group(self) -> None:
        g1 = {"row_id": "r1", "group": "G1", "target_object_ids": ["a"], "stratum": "S"}
        self.assertTrue(vlm_arms.row_outcome(g1, {"status": "unique", "object_ids": ["a"], "flag": None})["success"])
        no_match = vlm_arms.row_outcome(g1, {"status": "unique", "object_ids": [], "flag": "NO_CANDIDATE_MATCH"})
        self.assertFalse(no_match["success"])
        self.assertTrue(vlm_arms.row_outcome(g1, {"status": "none", "object_ids": [], "flag": None})["false_none"])
        g3 = {"row_id": "r2", "group": "G3", "target_object_ids": ["a", "b"], "stratum": "M"}
        out = vlm_arms.row_outcome(g3, {"status": "ambiguous", "object_ids": ["a"], "flag": None})
        self.assertEqual((out["report"], out["strict"]), (True, False))
        g3p = {"row_id": "r3", "group": "G3p", "target_object_ids": [], "definite_ids": ["b"], "stratum": "L"}
        self.assertTrue(vlm_arms.row_outcome(g3p, {"status": "unique", "object_ids": ["b"], "flag": None})["any_member"])
        g5 = {"row_id": "r4", "group": "G5", "target_object_ids": [], "stratum": "NA"}
        self.assertTrue(vlm_arms.row_outcome(g5, {"status": "none", "object_ids": [], "flag": "K0"})["none"])

    def test_score_arm_denominators_and_exclusion(self) -> None:
        rows = [
            {"row_id": "r1", "group": "G1", "target_object_ids": ["a"], "stratum": "S"},
            {"row_id": "r2", "group": "G1", "target_object_ids": ["b"], "stratum": "M"},
            {"row_id": "r5", "group": "G5", "target_object_ids": [], "stratum": "NA"},
            {"row_id": "r9", "group": "LEGACY_ONLY", "target_object_ids": [], "stratum": "L"},
        ]
        outcomes = {
            "r1": vlm_arms.row_outcome(rows[0], {"status": "unique", "object_ids": ["a"], "flag": None}),
            "r5": vlm_arms.row_outcome(rows[2], {"status": "none", "object_ids": [], "flag": None}),
        }
        score = vlm_arms.score_arm(rows, outcomes)
        self.assertEqual((score["groups"]["G1"]["success"]["k"], score["groups"]["G1"]["success"]["n"]), (1, 2))
        self.assertEqual(score["groups"]["G1"]["success_by_stratum"]["S"]["k"], 1)
        self.assertNotIn("none_by_stratum", score["groups"]["G5"])
        self.assertTrue(score["groups"]["LEGACY_ONLY"]["excluded"])
        self.assertEqual(score["counts"]["missing"], 2)

    def test_paired_diagnostic_is_intersection_not_product(self) -> None:
        rows = [{"row_id": f"r{i}", "group": "G1", "target_object_ids": ["a"], "stratum": "S"} for i in range(4)]
        outcomes = {"r0": {"success": True}, "r1": {"success": True}, "r2": {"success": False}, "r3": {"success": False}}
        det = {"r0": True, "r1": False, "r2": True, "r3": False}
        table = vlm_arms.paired_diagnostic(rows, outcomes, det)["ALL_SUCCESS_GROUPS"]
        self.assertEqual(table["table"], {"det_hit__arm_ok": 1, "det_hit__arm_fail": 1, "det_miss__arm_ok": 1, "det_miss__arm_fail": 1})
        self.assertEqual(table["P_arm_ok_and_det_hit"], 0.25)
        self.assertEqual(table["P_arm_ok_given_det_hit"], 0.5)


class PromptAndArmD(unittest.TestCase):
    def test_prompt_reuses_v2_segments_verbatim(self) -> None:
        text = vlm_arms.build_prompt_text("C", "the red car", True)
        self.assertIn(prompt_v2.HEAD_SEGMENT.replace("{surface}", "the red car"), text)
        self.assertIn(prompt_v2.vocab_segment("unity-v2"), text)
        self.assertIn(prompt_v2.G4_SEGMENT, text)
        self.assertNotIn(prompt_v2.COORD_SEGMENT, text)
        self.assertNotIn(prompt_v2.REPLY_SEGMENT, text)
        self.assertIn(vlm_arms.REPLY_INDEX_SEGMENT, text)
        self.assertNotIn(prompt_v2.G4_SEGMENT, vlm_arms.build_prompt_text("B", "the bus", False))

    def test_remote_constants_match_frozen(self) -> None:
        self.assertEqual(vlm_remote.PROCESSOR_SIZE, prompt_v2.PROCESSOR_SIZE)
        from tools.eng_sft import train_lora  # noqa: PLC0415

        self.assertEqual(vlm_remote.BASE_REVISION, train_lora.BASE_REVISION)
        from tools.dist_data import contract  # noqa: PLC0415

        self.assertEqual(baseline.VIEWER_SIDE_MIN_SEPARATION_PX, contract.VIEWER_SIDE_MIN_SEPARATION_PX)

    def test_arm_d_decisions(self) -> None:
        cands = [
            {"object_id": "t1", "pred_class": "suv", "pred_color": "red", "box": [0.05, 0.4, 0.1, 0.1]},
            {"object_id": "r", "pred_class": "bus", "pred_color": "gray", "box": [0.45, 0.4, 0.1, 0.1]},
            {"object_id": "t2", "pred_class": "suv", "pred_color": "blue", "box": [0.8, 0.4, 0.1, 0.1]},
        ]
        self.assertEqual(baseline.decide({"noun": {"class": "suv"}}, cands)["status"], "ambiguous")
        self.assertEqual(baseline.decide({"noun": {"class": "suv", "color": "blue"}}, cands)["object_ids"], ["t2"])
        self.assertEqual(baseline.decide({"noun": {"class": "taxi"}}, cands)["status"], "none")
        left = {"relation_program": {"target": {"class": "suv"}, "relation": {"type": "viewer_left_of", "ref": {"class": "bus"}}}}
        self.assertEqual(baseline.decide(left, cands)["object_ids"], ["t1"])
        no_ref = {"relation_program": {"target": {"class": "suv"}, "relation": {"type": "viewer_left_of", "ref": {"class": "taxi"}}}}
        self.assertEqual(baseline.decide(no_ref, cands)["status"], "none")
        self.assertEqual(baseline.decide({"noun": {"class": "suv"}}, [])["flag"], "K0")

    def test_knn_majority_with_tie_break(self) -> None:
        bank = [("bus", (1.0, 0.0)), ("bus", (0.9, 0.1)), ("taxi", (0.95, 0.05)), ("taxi", (0.8, 0.2)), ("car", (0.0, 1.0))]
        label, top = baseline.knn_class((1.0, 0.0), bank, k=4)
        self.assertEqual(len(top), 4)
        self.assertEqual(label, "bus")  # 2:2 并列，取相似度和大者


if __name__ == "__main__":
    unittest.main()
