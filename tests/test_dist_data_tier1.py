"""Tier-1 可逆语言工具链：ontology、规范化 AST、往返、执行器（§2.11 / §2.9）。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import contract, tier1_lang  # noqa: E402

SO = tier1_lang.SceneObject


class OntologyTest(unittest.TestCase):
    def test_rejects_field_outside_closed_set(self) -> None:
        with self.assertRaises(tier1_lang.OntologyViolation):
            tier1_lang.validate_program({"target": {"class": "taxi", "size": "big"}})

    def test_rejects_unknown_class(self) -> None:
        with self.assertRaises(tier1_lang.OntologyViolation):
            tier1_lang.validate_program({"target": {"class": "tractor"}})

    def test_rejects_dynamic_relation(self) -> None:
        """动态关系全批禁止（章程 U6/BC），schema 层拒绝。"""
        with self.assertRaises(tier1_lang.OntologyViolation):
            tier1_lang.validate_program(
                {
                    "target": {"class": "taxi"},
                    "relation": {"type": "moving_towards", "ref": {"class": "bus"}},
                }
            )

    def test_rejects_unverified_colour(self) -> None:
        program = {"target": {"class": "taxi", "color": "yellow"}}
        tier1_lang.validate_program(program, verified_colors=["yellow"])
        with self.assertRaises(tier1_lang.OntologyViolation):
            tier1_lang.validate_program(program, verified_colors=["blue"])


class CanonicalAstTest(unittest.TestCase):
    def test_canon_is_idempotent_over_full_enumeration(self) -> None:
        for program in tier1_lang.enumerate_programs(classes=contract.CLASS_WORDS[:3]):
            once = tier1_lang.canonical_ast(program)
            self.assertEqual(tier1_lang.canonical_ast(once), once)

    def test_canon_lowercases_and_drops_absent_optionals(self) -> None:
        canonical = tier1_lang.canonical_ast({"target": {"class": "TAXI", "color": None}})
        self.assertEqual(canonical, {"target": {"class": "taxi"}})

    def test_canonical_bytes_are_key_sorted(self) -> None:
        payload = tier1_lang.canonical_bytes(
            {
                "relation": {"type": "nearest_to", "ref": {"class": "bus"}},
                "target": {"class": "taxi"},
            }
        )
        self.assertTrue(payload.decode("utf-8").startswith('{"relation"'))


class RoundTripTest(unittest.TestCase):
    def test_full_program_enumeration_round_trips(self) -> None:
        """`parse(render(p)) ≡ p` 在 Tier-1 全枚举上成立（39,303 个程序）。"""
        programs = tier1_lang.enumerate_programs()
        self.assertEqual(len(programs), 39303)
        for program in programs:
            text = tier1_lang.render(program)
            self.assertEqual(
                tier1_lang.canonical_ast(tier1_lang.parse(text)),
                tier1_lang.canonical_ast(program),
                text,
            )

    def test_multiword_classes_are_not_shadowed(self) -> None:
        self.assertEqual(
            tier1_lang.parse("the police car")["target"]["class"], "police car"
        )
        self.assertEqual(
            tier1_lang.parse("the container truck")["target"]["class"], "container truck"
        )
        self.assertEqual(tier1_lang.parse("the truck")["target"]["class"], "truck")

    def test_free_text_is_unparseable(self) -> None:
        for text in ("taxi", "the yellow cab", "the taxi near the bus", ""):
            with self.assertRaises(tier1_lang.ParseError):
                tier1_lang.parse(text)


class ExecutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.taxi = SO("taxi-1", "taxi", "yellow", True, center_px=(100.0, 100.0), world_xz=(0.0, 0.0), route_side=1)
        self.other_taxi = SO("taxi-2", "taxi", "white", True, center_px=(300.0, 100.0), world_xz=(30.0, 0.0), route_side=-1)
        self.bus = SO("bus-1", "bus", "blue", True, center_px=(200.0, 100.0), world_xz=(5.0, 0.0), route_side=1)

    def test_class_only_unique(self) -> None:
        result = tier1_lang.execute({"target": {"class": "bus"}}, [self.taxi, self.bus])
        self.assertTrue(result.unique)
        self.assertEqual(result.selected_object_ids, ("bus-1",))

    def test_unknown_class_blocker_destroys_uniqueness(self) -> None:
        """动态目标类别 UNKNOWN 与任何类别表达冲突（§2.3 fail-closed）。"""
        unknown = SO("dynamic-target:UNKNOWN", None, None, False)
        result = tier1_lang.execute({"target": {"class": "bus"}}, [self.bus, unknown])
        self.assertFalse(result.unique)
        self.assertEqual(len(result.selected_object_ids), 2)

    def test_unverified_colour_object_blocks_colour_program(self) -> None:
        unverified = SO("taxi-3", "taxi", None, True)
        result = tier1_lang.execute(
            {"target": {"class": "taxi", "color": "yellow"}}, [self.taxi, unverified]
        )
        self.assertFalse(result.unique)

    def test_nearest_to_requires_dominance(self) -> None:
        near = SO("taxi-a", "taxi", None, True, world_xz=(1.0, 0.0))
        tie = SO("taxi-b", "taxi", None, True, world_xz=(1.05, 0.0))
        program = {
            "target": {"class": "taxi"},
            "relation": {"type": "nearest_to", "ref": {"class": "bus"}},
        }
        result = tier1_lang.execute(program, [near, tie, self.bus])
        self.assertFalse(result.unique)
        self.assertFalse(result.relation_available)

        far = SO("taxi-c", "taxi", None, True, world_xz=(100.0, 0.0))
        dominant = tier1_lang.execute(program, [near, far, self.bus])
        self.assertTrue(dominant.unique)
        self.assertEqual(dominant.selected_object_ids, ("taxi-a",))

    def test_viewer_side_needs_forty_pixels(self) -> None:
        program = {
            "target": {"class": "taxi"},
            "relation": {"type": "viewer_left_of", "ref": {"class": "bus"}},
        }
        result = tier1_lang.execute(program, [self.taxi, self.bus])
        self.assertEqual(result.selected_object_ids, ("taxi-1",))

        close = SO("taxi-close", "taxi", None, True, center_px=(180.0, 100.0))
        near_result = tier1_lang.execute(program, [close, self.bus])
        self.assertEqual(near_result.selected_object_ids, ())

    def test_viewer_right_of_is_mirror(self) -> None:
        program = {
            "target": {"class": "taxi"},
            "relation": {"type": "viewer_right_of", "ref": {"class": "bus"}},
        }
        result = tier1_lang.execute(program, [self.other_taxi, self.bus])
        self.assertEqual(result.selected_object_ids, ("taxi-2",))

    def test_on_route_side_matches_same_sign(self) -> None:
        program = {
            "target": {"class": "taxi"},
            "relation": {"type": "on_route_side", "ref": {"class": "bus"}},
        }
        result = tier1_lang.execute(program, [self.taxi, self.other_taxi, self.bus])
        self.assertEqual(result.selected_object_ids, ("taxi-1",))

    def test_ambiguous_reference_disables_relation(self) -> None:
        second_bus = SO("bus-2", "bus", None, True, world_xz=(9.0, 0.0), route_side=1)
        program = {
            "target": {"class": "taxi"},
            "relation": {"type": "nearest_to", "ref": {"class": "bus"}},
        }
        result = tier1_lang.execute(program, [self.taxi, self.bus, second_bus])
        self.assertFalse(result.relation_available)
        self.assertEqual(result.selected_object_ids, ())

    def test_hits_expected_target(self) -> None:
        result = tier1_lang.execute({"target": {"class": "bus"}}, [self.taxi, self.bus])
        self.assertTrue(tier1_lang.hits_expected_target(result, "bus-1"))
        self.assertFalse(tier1_lang.hits_expected_target(result, "taxi-1"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
