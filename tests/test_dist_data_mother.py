"""S8 母集物化、逐 id 等价断言与模板表达（§2.9，BC-DATA-1）。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import g0_report, gen_mother_templates, make_splits  # noqa: E402

BOX = [0.1, 0.2, 0.3, 0.4]


def frozen_set(pairs) -> dict:
    candidates = []
    split_of = {}
    atom_of = {}
    for frame, object_id, split, program in pairs:
        candidates.append(
            {
                "frame_id": frame,
                "object_id": object_id,
                "program": program,
                "program_kind": "attribute" if "relation" not in program else "relational",
                "usage_class": "VALID_FORMAL",
                "family": "fam",
                "layout_class": "default",
                "station_key": "1:1:1:1",
                "floor_usage": True,
                "pre_split_floor_eligible": True,
            }
        )
        split_of[frame] = split
        atom_of[frame] = f"atom-{split}"
    return g0_report.freeze_mother_candidates(candidates, split_of, atom_of, [])


OPEN_REPORT = {"gate": g0_report.GATE_OPEN, "unmet_floors": []}
CLOSED_REPORT = {"gate": g0_report.GATE_INSUFFICIENT, "unmet_floors": ["F4"]}


class GatePreconditionTest(unittest.TestCase):
    def test_s8_never_runs_when_the_gate_is_closed(self) -> None:
        frozen = frozen_set([("f1", "Vehicle_Taxi", "train", {"target": {"class": "taxi"}})])
        with self.assertRaises(gen_mother_templates.MotherSetError) as caught:
            gen_mother_templates.materialize_mother_set(
                frozen, CLOSED_REPORT, {"f1|Vehicle_Taxi": BOX}
            )
        self.assertIn("S8 永不执行", str(caught.exception))


class EquivalenceAssertionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.frozen = frozen_set(
            [
                ("f1", "Vehicle_Taxi", "train", {"target": {"class": "taxi"}}),
                ("f2", "Vehicle_Bus_color01", "test", {"target": {"class": "bus"}}),
            ]
        )
        self.boxes = {"f1|Vehicle_Taxi": BOX, "f2|Vehicle_Bus_color01": BOX}

    def test_matching_materialisation_passes(self) -> None:
        mother = gen_mother_templates.materialize_mother_set(
            self.frozen, OPEN_REPORT, self.boxes
        )
        self.assertEqual(mother["count"], 2)

    def test_one_extra_candidate_is_a_hard_error(self) -> None:
        """注入一条偏差即报错（§5.3 的必失败测试）。"""
        materialized = [
            {
                "candidate_id": item["candidate_id"],
                "frame_id": item["frame_id"],
                "object_id": item["object_id"],
                "split": item["split"],
                "atom_id": item["atom_id"],
                "usage_class": item["usage_class"],
                "program": item["program"],
            }
            for item in self.frozen["candidates"]
        ]
        materialized.append({**materialized[0], "candidate_id": "f9|Vehicle_Taxi"})
        materialized.sort(key=lambda item: item["candidate_id"])
        with self.assertRaises(gen_mother_templates.MotherSetError) as caught:
            gen_mother_templates.assert_candidate_equivalence(self.frozen, materialized)
        self.assertIn("没有增删改任何候选的权力", str(caught.exception))

    def test_one_missing_candidate_is_a_hard_error(self) -> None:
        with self.assertRaises(gen_mother_templates.MotherSetError):
            gen_mother_templates.materialize_mother_set(
                self.frozen, OPEN_REPORT, {"f1|Vehicle_Taxi": BOX}
            )

    def test_altered_program_bytes_are_a_hard_error(self) -> None:
        materialized = [
            {
                "candidate_id": item["candidate_id"],
                "frame_id": item["frame_id"],
                "object_id": item["object_id"],
                "split": item["split"],
                "atom_id": item["atom_id"],
                "usage_class": item["usage_class"],
                "program": item["program"],
            }
            for item in self.frozen["candidates"]
        ]
        materialized[0]["program"] = {"target": {"class": "car"}}
        with self.assertRaises(gen_mother_templates.MotherSetError) as caught:
            gen_mother_templates.assert_candidate_equivalence(self.frozen, materialized)
        self.assertIn("最小程序字节", str(caught.exception))

    def test_altered_split_is_a_hard_error(self) -> None:
        materialized = [
            {
                "candidate_id": item["candidate_id"],
                "frame_id": item["frame_id"],
                "object_id": item["object_id"],
                "split": "train",
                "atom_id": item["atom_id"],
                "usage_class": item["usage_class"],
                "program": item["program"],
            }
            for item in self.frozen["candidates"]
        ]
        with self.assertRaises(gen_mother_templates.MotherSetError):
            gen_mother_templates.assert_candidate_equivalence(self.frozen, materialized)


class TemplateExpressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.frozen = frozen_set(
            [
                ("f1", "Vehicle_Taxi", "train", {"target": {"class": "taxi"}}),
                ("f2", "Vehicle_Bus_color01", "dev", {"target": {"class": "bus", "color": "blue"}}),
                ("f3", "Vehicle_Car_color01", "test", {"target": {"class": "car"}}),
                ("f4", "Vehicle_SUV_color01", "d3", {"target": {"class": "suv"}}),
            ]
        )
        self.boxes = {item["candidate_id"]: BOX for item in self.frozen["candidates"]}
        self.mother = gen_mother_templates.materialize_mother_set(
            self.frozen, OPEN_REPORT, self.boxes
        )

    def test_only_train_and_dev_receive_expressions(self) -> None:
        expressions = gen_mother_templates.build_template_expressions(self.mother)
        self.assertEqual(expressions["count"], 2)
        self.assertEqual(
            sorted(item["expression"] for item in expressions["expressions"]),
            ["the blue bus", "the taxi"],
        )
        self.assertEqual(expressions["teacher_calls"], 0)

    def test_test_side_never_reaches_training_expressions(self) -> None:
        expressions = gen_mother_templates.build_template_expressions(self.mother)
        gen_mother_templates.assert_test_side_never_trained(self.mother, expressions)
        polluted = {
            "expressions": expressions["expressions"]
            + [{"candidate_id": "f3|Vehicle_Car_color01"}]
        }
        with self.assertRaises(gen_mother_templates.MotherSetError):
            gen_mother_templates.assert_test_side_never_trained(self.mother, polluted)

    def test_held_out_object_cannot_be_a_training_referent(self) -> None:
        mother = dict(self.mother)
        mother["triples"] = [
            {**triple, "held_out_object": triple["split"] == "train"}
            for triple in self.mother["triples"]
        ]
        with self.assertRaises(gen_mother_templates.MotherSetError) as caught:
            gen_mother_templates.build_template_expressions(mother)
        self.assertIn("机械封禁", str(caught.exception))

    def test_cluster_statistics_report_all_four_splits(self) -> None:
        statistics = gen_mother_templates.cluster_statistics(self.mother)
        self.assertEqual(set(statistics["per_split"]), set(make_splits.SPLITS))
        self.assertEqual(statistics["per_split"]["train"]["sample_count"], 1)

    def test_reservations_carry_the_handwritten_range(self) -> None:
        reservations = gen_mother_templates.reservation_lists(
            self.mother, ["Vehicle_Car_color01"]
        )
        self.assertEqual(
            reservations["handwritten_expression_reservation"]["target_count_range"], [50, 100]
        )
        self.assertEqual(
            reservations["test_held_out_units"],
            [{"object_id": "Vehicle_Car_color01", "frame_id": "f3"}],
        )
        self.assertIn("永不进入训练", reservations["mechanical_assertion"])

    def test_build_d0_ties_it_together(self) -> None:
        payload = gen_mother_templates.build_d0(
            self.frozen, OPEN_REPORT, self.boxes, ["Vehicle_Car_color01"]
        )
        self.assertEqual(payload["stage"], 8)
        self.assertEqual(payload["mother_set"]["count"], 4)
        self.assertEqual(payload["template_expressions"]["count"], 2)
        self.assertIn("reservations", payload)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
