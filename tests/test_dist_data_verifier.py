"""§2.11 verifier 合同：input/output schema、语义等价判据与离线夹具（BC-DATA-4）。"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import contract, tier1_lang, verifier_contract  # noqa: E402


def resolver_for(domain):
    return lambda document: domain


class InputSchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.valid = verifier_contract.make_input(
            "the taxi", {"target": {"class": "taxi"}}, "Vehicle_Taxi"
        )

    def test_valid_input_has_no_problems(self) -> None:
        self.assertEqual(verifier_contract.validate_input(self.valid), [])

    def test_artifact_refs_need_attempt_and_sha(self) -> None:
        for key in verifier_contract.REQUIRED_ARTIFACT_REFS:
            broken = dict(self.valid)
            broken[key] = {"id": "x", "sha256": "a" * 64}  # 缺 attempt
            self.assertTrue(verifier_contract.validate_input(broken))

    def test_code_refs_need_sha(self) -> None:
        for key in verifier_contract.REQUIRED_CODE_REFS:
            broken = dict(self.valid)
            broken[key] = {"id": "x"}
            self.assertTrue(verifier_contract.validate_input(broken))

    def test_tier_is_required_and_closed(self) -> None:
        broken = dict(self.valid)
        broken["tier"] = "human"
        self.assertTrue(verifier_contract.validate_input(broken))

    def test_mechanical_tier_forbids_model_evidence(self) -> None:
        broken = dict(self.valid)
        broken["model_evidence"] = verifier_contract.model_tier_evidence()
        self.assertTrue(verifier_contract.validate_input(broken))

    def test_model_tier_requires_every_evidence_field(self) -> None:
        complete = verifier_contract.make_input(
            "the taxi",
            {"target": {"class": "taxi"}},
            "Vehicle_Taxi",
            tier="model",
            model_evidence=verifier_contract.model_tier_evidence(),
        )
        self.assertEqual(verifier_contract.validate_input(complete), [])
        for key in verifier_contract.MODEL_EVIDENCE_KEYS + verifier_contract.MODEL_TIER_REQUIRED:
            broken = dict(complete)
            evidence = dict(complete["model_evidence"])
            evidence.pop(key)
            broken["model_evidence"] = evidence
            self.assertTrue(verifier_contract.validate_input(broken), key)

    def test_ontology_version_is_pinned(self) -> None:
        broken = dict(self.valid)
        broken["ontology_version"] = "ontology/v2"
        self.assertTrue(verifier_contract.validate_input(broken))


class OutputSchemaTest(unittest.TestCase):
    def test_mechanical_tier_audit_fields_are_null(self) -> None:
        domain = [tier1_lang.SceneObject("Vehicle_Taxi", "taxi", None, True)]
        output = verifier_contract.verify(
            verifier_contract.make_input(
                "the taxi", {"target": {"class": "taxi"}}, "Vehicle_Taxi"
            ),
            resolver_for(domain),
        )
        self.assertEqual(output["verdict"], "PASS")
        self.assertEqual(verifier_contract.validate_output(output), [])
        for key in verifier_contract.MODEL_EVIDENCE_KEYS:
            self.assertIsNone(output["audit"][key])

    def test_model_tier_audit_fields_are_populated(self) -> None:
        domain = [tier1_lang.SceneObject("Vehicle_Taxi", "taxi", None, True)]
        output = verifier_contract.verify(
            verifier_contract.make_input(
                "the taxi",
                {"target": {"class": "taxi"}},
                "Vehicle_Taxi",
                tier="model",
                model_evidence=verifier_contract.model_tier_evidence(),
            ),
            resolver_for(domain),
        )
        self.assertEqual(verifier_contract.validate_output(output), [])
        for key in verifier_contract.MODEL_EVIDENCE_KEYS:
            self.assertIsNotNone(output["audit"][key])

    def test_output_validator_catches_nullable_violations(self) -> None:
        bad = {
            "tier": "mechanical",
            "verdict": "PASS",
            "reject_reason": None,
            "audit": {key: "x" for key in verifier_contract.MODEL_EVIDENCE_KEYS},
        }
        self.assertTrue(verifier_contract.validate_output(bad))

    def test_pass_must_not_carry_a_reason(self) -> None:
        bad = {
            "tier": "mechanical",
            "verdict": "PASS",
            "reject_reason": "FORMAT",
            "audit": {key: None for key in verifier_contract.MODEL_EVIDENCE_KEYS},
        }
        self.assertTrue(verifier_contract.validate_output(bad))


class SemanticEquivalenceTest(unittest.TestCase):
    def test_ast_mismatch_beats_a_coincidental_execution_hit(self) -> None:
        """「当前帧碰巧命中同一对象」不得替代规范化程序等价（§2.11）。"""
        domain = [tier1_lang.SceneObject("Vehicle_Taxi", "taxi", "yellow", True)]
        output = verifier_contract.verify(
            verifier_contract.make_input(
                "the yellow taxi", {"target": {"class": "taxi"}}, "Vehicle_Taxi"
            ),
            resolver_for(domain),
        )
        self.assertEqual(output["verdict"], "REJECT")
        self.assertEqual(output["reject_reason"], "AST_MISMATCH")
        self.assertIsNone(output["execution"])

    def test_pass_requires_all_three_conditions(self) -> None:
        program = {"target": {"class": "taxi"}}
        domain = [tier1_lang.SceneObject("Vehicle_Taxi", "taxi", None, True)]
        output = verifier_contract.verify(
            verifier_contract.make_input("the taxi", program, "Vehicle_Taxi"),
            resolver_for(domain),
        )
        self.assertTrue(output["ast_equivalent"])
        self.assertTrue(output["execution"]["unique"])
        self.assertTrue(output["execution"]["hits_expected_target"])
        self.assertEqual(output["verdict"], "PASS")


class OfflineFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = verifier_contract.offline_fixtures()

    def test_every_reject_path_has_at_least_two_fixtures(self) -> None:
        counts: dict[str, int] = {}
        for fixture in self.fixtures:
            if fixture["expected_reason"]:
                counts[fixture["expected_reason"]] = counts.get(fixture["expected_reason"], 0) + 1
        for reason in contract.VERIFIER_REJECT_REASONS:
            self.assertGreaterEqual(counts.get(reason, 0), 2, reason)

    def test_at_least_two_standard_passes(self) -> None:
        passes = [item for item in self.fixtures if item["expected_verdict"] == "PASS"]
        self.assertGreaterEqual(len(passes), 2)

    def test_named_fixtures_from_the_contract_are_present(self) -> None:
        names = {item["name"] for item in self.fixtures}
        self.assertIn("ast_mismatch_same_object", names)
        self.assertIn("execution_wrong_target", names)

    def test_all_fixtures_produce_their_expected_verdict(self) -> None:
        for fixture in self.fixtures:
            output = verifier_contract.verify(
                fixture["input"],
                resolver_for(fixture["domain"]),
                verified_colors=fixture.get("verified_colors"),
            )
            self.assertEqual(output["verdict"], fixture["expected_verdict"], fixture["name"])
            self.assertEqual(
                output["reject_reason"], fixture["expected_reason"], fixture["name"]
            )
            self.assertEqual(verifier_contract.validate_output(output), [], fixture["name"])

    def test_verdict_is_a_pure_function_of_input_and_domain(self) -> None:
        for fixture in self.fixtures:
            first = verifier_contract.verify(
                fixture["input"],
                resolver_for(fixture["domain"]),
                verified_colors=fixture.get("verified_colors"),
            )
            second = verifier_contract.verify(
                fixture["input"],
                resolver_for(fixture["domain"]),
                verified_colors=fixture.get("verified_colors"),
            )
            self.assertEqual(first, second, fixture["name"])

    def test_model_tier_fixture_makes_no_call(self) -> None:
        fixture = next(
            item for item in self.fixtures if item["name"] == "pass_model_tier_schema_only"
        )
        self.assertIn("不调用模型", fixture["note"])
        self.assertEqual(fixture["input"]["tier"], "model")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
