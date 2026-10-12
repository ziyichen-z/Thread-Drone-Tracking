#!/usr/bin/env python3
"""§2.11 Verifier 接口合同（BC-DIST-2 机械半边，AR1-7 / AR2-4 / BC-DATA-4）。

本批次**不调用任何教师/验证模型**：交付冻结的 `verifier_input/v1` 与
`verifier_output/v1` schema、语义等价判据与离线夹具。

BC-DATA-4：verdict 是「input + 被哈希引用字节」的**纯函数**。
`verifier_input/v1` 必须含 `tier`、`ontology_ref + sha256`、
`parser_ref + sha256`；所有 inventory/catalog/splits 引用同时带 attempt id
与工件 SHA-256。`tier=mechanical` 时 model evidence 必为 null；`tier=model`
时必须再带冻结的 raw-response artifact ref + SHA-256、model/version/prompt
SHA 与 response parser ref + SHA，缺一即 `REJECT(FORMAT)`。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

from tools.dist_data import contract, tier1_lang
from tools.dist_data.artifacts import DistDataError, canonical_json_bytes

INPUT_VERSION = "verifier_input/v1"
OUTPUT_VERSION = "verifier_output/v1"

REQUIRED_ARTIFACT_REFS: tuple[str, ...] = ("frame_ref", "catalog_ref", "splits_ref")
REQUIRED_CODE_REFS: tuple[str, ...] = ("ontology_ref", "parser_ref")
MODEL_EVIDENCE_KEYS: tuple[str, ...] = (
    "verifier_model_id",
    "model_version",
    "prompt_sha256",
    "response_raw_sha256",
)
MODEL_TIER_REQUIRED: tuple[str, ...] = (
    "response_artifact_ref",
    "response_parser_ref",
)

_SHA256_LENGTH = 64


class VerifierContractError(DistDataError):
    """verifier 合同违反（用于构造夹具时的自检，不用于 verdict 通道）。"""


@dataclass(frozen=True)
class Verdict:
    payload: dict[str, Any]

    @property
    def verdict(self) -> str:
        return self.payload["verdict"]

    @property
    def reject_reason(self) -> str | None:
        return self.payload.get("reject_reason")


def _is_ref(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("id"), str)
        and value["id"] != ""
        and isinstance(value.get("sha256"), str)
        and len(value["sha256"]) == _SHA256_LENGTH
    )


def _is_artifact_ref(value: Any) -> bool:
    return _is_ref(value) and isinstance(value.get("attempt"), str) and value["attempt"] != ""


def validate_input(document: Any) -> list[str]:
    """返回 FORMAT 违反清单（空 = 合规）。缺一即 `REJECT(FORMAT)`。"""
    problems: list[str] = []
    if not isinstance(document, dict):
        return ["verifier_input 必须是对象"]
    if document.get("schema_version") != INPUT_VERSION:
        problems.append(f"schema_version 必须是 {INPUT_VERSION}")
    if not isinstance(document.get("expression"), str):
        problems.append("缺 expression")
    if not isinstance(document.get("semantic_program"), str):
        problems.append("缺 semantic_program（规范化 AST 字节，UTF-8 文本）")
    if not isinstance(document.get("expected_target_id"), str):
        problems.append("缺 expected_target_id")
    if document.get("ontology_version") != contract.ONTOLOGY_VERSION:
        problems.append(f"ontology_version 必须是 {contract.ONTOLOGY_VERSION}")
    tier = document.get("tier")
    if tier not in contract.VERIFIER_TIERS:
        problems.append(f"tier 必须 ∈ {list(contract.VERIFIER_TIERS)}")
    for key in REQUIRED_CODE_REFS:
        if not _is_ref(document.get(key)):
            problems.append(f"{key} 必须带 id 与 64 位 sha256")
    for key in REQUIRED_ARTIFACT_REFS:
        if not _is_artifact_ref(document.get(key)):
            problems.append(f"{key} 必须同时带 attempt id 与工件 sha256")

    evidence = document.get("model_evidence")
    if tier == "mechanical":
        if evidence not in (None, {}):
            if not isinstance(evidence, dict) or any(
                evidence.get(key) is not None for key in MODEL_EVIDENCE_KEYS
            ):
                problems.append("tier=mechanical 时 model evidence 必为 null")
    elif tier == "model":
        if not isinstance(evidence, dict):
            problems.append("tier=model 缺 model_evidence")
        else:
            for key in MODEL_EVIDENCE_KEYS:
                value = evidence.get(key)
                if not isinstance(value, str) or not value:
                    problems.append(f"tier=model 缺 model_evidence.{key}")
            for key in MODEL_TIER_REQUIRED:
                if not _is_ref(evidence.get(key)):
                    problems.append(f"tier=model 缺 model_evidence.{key}（含 sha256）")
    return problems


def _output(
    *,
    tier: str,
    parse_status: str,
    canonical_ast: dict[str, Any] | None,
    ast_equivalent: bool | None,
    execution: dict[str, Any] | None,
    verdict: str,
    reject_reason: str | None,
    model_evidence: dict[str, Any] | None,
) -> dict[str, Any]:
    audit = {key: None for key in MODEL_EVIDENCE_KEYS}
    if tier == "model" and model_evidence:
        for key in MODEL_EVIDENCE_KEYS:
            audit[key] = model_evidence.get(key)
    return {
        "schema_version": OUTPUT_VERSION,
        "tier": tier,
        "parse_status": parse_status,
        "canonical_ast": canonical_ast,
        "ast_equivalent": ast_equivalent,
        "execution": execution,
        "verdict": verdict,
        "reject_reason": reject_reason,
        "audit": audit,
    }


def validate_output(document: dict[str, Any]) -> list[str]:
    """`verifier_output/v1` 的 nullable 规则（入 schema，机检）。"""
    problems: list[str] = []
    tier = document.get("tier")
    if tier not in contract.VERIFIER_TIERS:
        problems.append("tier 越界")
    if document.get("verdict") not in contract.VERIFIER_VERDICTS:
        problems.append("verdict 越界")
    reason = document.get("reject_reason")
    if document.get("verdict") == "REJECT":
        if reason not in contract.VERIFIER_REJECT_REASONS:
            problems.append("REJECT 必须带闭集内的 reject_reason")
    elif reason is not None:
        problems.append("PASS 不得带 reject_reason")
    audit = document.get("audit") or {}
    if tier == "mechanical":
        if any(audit.get(key) is not None for key in MODEL_EVIDENCE_KEYS):
            problems.append("tier=mechanical 时 audit 四字段必须为 null")
    elif tier == "model":
        if any(audit.get(key) is None for key in MODEL_EVIDENCE_KEYS):
            problems.append("tier=model 时 audit 四字段必须非 null")
    return problems


def verify(
    document: dict[str, Any],
    domain_resolver: Callable[[dict[str, Any]], Sequence[tier1_lang.SceneObject]],
    *,
    verified_colors: Sequence[str] | None = None,
) -> dict[str, Any]:
    """PASS ⇔ AST 等价 ∧ 执行唯一 ∧ 命中 `expected_target_id`。

    「当前帧碰巧命中同一对象」不得替代规范化程序等价：AST 不等价时
    verdict 恒为 `REJECT(AST_MISMATCH)`，即使执行选中同一对象。
    """
    tier = document.get("tier") if isinstance(document, dict) else None
    problems = validate_input(document)
    if problems:
        return _output(
            tier=tier if tier in contract.VERIFIER_TIERS else "mechanical",
            parse_status="NOT_ATTEMPTED",
            canonical_ast=None,
            ast_equivalent=None,
            execution=None,
            verdict="REJECT",
            reject_reason="FORMAT",
            model_evidence=document.get("model_evidence") if isinstance(document, dict) else None,
        )

    evidence = document.get("model_evidence")
    try:
        program = tier1_lang.parse(document["expression"])
    except tier1_lang.ParseError:
        return _output(
            tier=tier,
            parse_status="UNPARSEABLE",
            canonical_ast=None,
            ast_equivalent=None,
            execution=None,
            verdict="REJECT",
            reject_reason="UNPARSEABLE",
            model_evidence=evidence,
        )
    try:
        tier1_lang.validate_program(program, verified_colors=verified_colors)
    except tier1_lang.OntologyViolation:
        return _output(
            tier=tier,
            parse_status="PARSED",
            canonical_ast=None,
            ast_equivalent=None,
            execution=None,
            verdict="REJECT",
            reject_reason="ONTOLOGY_VIOLATION",
            model_evidence=evidence,
        )

    canonical = tier1_lang.canonical_ast(program)
    expected_bytes = document["semantic_program"].encode("utf-8")
    equivalent = canonical_json_bytes(canonical) == expected_bytes
    if not equivalent:
        return _output(
            tier=tier,
            parse_status="PARSED",
            canonical_ast=canonical,
            ast_equivalent=False,
            execution=None,
            verdict="REJECT",
            reject_reason="AST_MISMATCH",
            model_evidence=evidence,
        )

    domain = domain_resolver(document)
    result = tier1_lang.execute(program, domain)
    execution = {
        "selected_object_ids": list(result.selected_object_ids),
        "unique": result.unique,
        "hits_expected_target": tier1_lang.hits_expected_target(
            result, document["expected_target_id"]
        ),
    }
    if not result.unique:
        reason = "EXECUTION_NOT_UNIQUE"
    elif not execution["hits_expected_target"]:
        reason = "EXECUTION_WRONG_TARGET"
    else:
        reason = None
    return _output(
        tier=tier,
        parse_status="PARSED",
        canonical_ast=canonical,
        ast_equivalent=True,
        execution=execution,
        verdict="PASS" if reason is None else "REJECT",
        reject_reason=reason,
        model_evidence=evidence,
    )


# --- 离线夹具 -------------------------------------------------------------
def _ref(identifier: str, filler: str = "a") -> dict[str, Any]:
    return {"id": identifier, "sha256": filler * _SHA256_LENGTH}


def _artifact_ref(identifier: str, attempt: str = "attempt-1", filler: str = "b") -> dict[str, Any]:
    return {"id": identifier, "attempt": attempt, "sha256": filler * _SHA256_LENGTH}


def make_input(
    expression: str,
    program: dict[str, Any],
    expected_target_id: str,
    *,
    tier: str = "mechanical",
    model_evidence: dict[str, Any] | None = None,
    semantic_program: str | None = None,
) -> dict[str, Any]:
    """构造合规的 `verifier_input/v1`（夹具与调用方共用）。"""
    return {
        "schema_version": INPUT_VERSION,
        "tier": tier,
        "expression": expression,
        "semantic_program": semantic_program
        if semantic_program is not None
        else tier1_lang.canonical_bytes(program).decode("utf-8"),
        "expected_target_id": expected_target_id,
        "frame_ref": _artifact_ref("inventory:frame-0001"),
        "catalog_ref": _artifact_ref("frames_catalog"),
        "splits_ref": _artifact_ref("splits"),
        "ontology_ref": _ref(contract.ONTOLOGY_VERSION),
        "parser_ref": _ref("tools/dist_data/tier1_lang.py"),
        "ontology_version": contract.ONTOLOGY_VERSION,
        "model_evidence": model_evidence,
    }


def model_tier_evidence(complete: bool = True) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "verifier_model_id": "frozen-teacher-verifier",
        "model_version": "v0",
        "prompt_sha256": "c" * _SHA256_LENGTH,
        "response_raw_sha256": "d" * _SHA256_LENGTH,
        "response_artifact_ref": _ref("runtime/dist-data/verifier/raw-0001.json", "e"),
        "response_parser_ref": _ref("tools/dist_data/verifier_contract.py", "f"),
    }
    if not complete:
        evidence.pop("response_parser_ref")
    return evidence


def offline_fixtures() -> list[dict[str, Any]]:
    """每个 reject 路径 ≥ 2 条 + ≥ 2 条标准 PASS，含 §2.11 点名的两类。"""
    taxi = tier1_lang.SceneObject("Vehicle_Taxi", "taxi", "yellow", True)
    bus = tier1_lang.SceneObject("Vehicle_Bus_color01", "bus", "blue", True)
    second_taxi = tier1_lang.SceneObject("Vehicle_Taxi (1)", "taxi", "white", True)
    single = [taxi, bus]
    two_taxis = [taxi, second_taxi, bus]

    yellow_taxi = {"target": {"class": "taxi", "color": "yellow"}}
    plain_taxi = {"target": {"class": "taxi"}}
    plain_bus = {"target": {"class": "bus"}}

    fixtures: list[dict[str, Any]] = [
        {
            "name": "pass_class_only",
            "domain": single,
            "input": make_input("the taxi", plain_taxi, "Vehicle_Taxi"),
            "expected_verdict": "PASS",
            "expected_reason": None,
        },
        {
            "name": "pass_class_color",
            "domain": single,
            "input": make_input("the yellow taxi", yellow_taxi, "Vehicle_Taxi"),
            "expected_verdict": "PASS",
            "expected_reason": None,
        },
        {
            "name": "unparseable_free_text",
            "domain": single,
            "input": make_input("please find the yellow cab", plain_taxi, "Vehicle_Taxi"),
            "expected_verdict": "REJECT",
            "expected_reason": "UNPARSEABLE",
        },
        {
            "name": "unparseable_missing_article",
            "domain": single,
            "input": make_input("taxi", plain_taxi, "Vehicle_Taxi"),
            "expected_verdict": "REJECT",
            "expected_reason": "UNPARSEABLE",
        },
        {
            "name": "ontology_unverified_color",
            "domain": single,
            "input": make_input("the yellow taxi", yellow_taxi, "Vehicle_Taxi"),
            "verified_colors": ["blue"],
            "expected_verdict": "REJECT",
            "expected_reason": "ONTOLOGY_VIOLATION",
        },
        {
            "name": "ontology_unverified_ref_color",
            "domain": single,
            "input": make_input(
                "the taxi nearest to the blue bus",
                {
                    "target": {"class": "taxi"},
                    "relation": {"type": "nearest_to", "ref": {"class": "bus", "color": "blue"}},
                },
                "Vehicle_Taxi",
            ),
            "verified_colors": [],
            "expected_verdict": "REJECT",
            "expected_reason": "ONTOLOGY_VIOLATION",
        },
        {
            # §2.11 点名：当帧执行同选一个对象，但 AST 不等价。
            "name": "ast_mismatch_same_object",
            "domain": single,
            "input": make_input("the yellow taxi", plain_taxi, "Vehicle_Taxi"),
            "expected_verdict": "REJECT",
            "expected_reason": "AST_MISMATCH",
        },
        {
            "name": "ast_mismatch_other_class",
            "domain": single,
            "input": make_input("the bus", plain_taxi, "Vehicle_Bus_color01"),
            "expected_verdict": "REJECT",
            "expected_reason": "AST_MISMATCH",
        },
        {
            "name": "execution_not_unique_two_taxis",
            "domain": two_taxis,
            "input": make_input("the taxi", plain_taxi, "Vehicle_Taxi"),
            "expected_verdict": "REJECT",
            "expected_reason": "EXECUTION_NOT_UNIQUE",
        },
        {
            "name": "execution_not_unique_unknown_class_blocker",
            "domain": [
                taxi,
                bus,
                tier1_lang.SceneObject("dynamic-target:UNKNOWN", None, None, False),
            ],
            "input": make_input("the taxi", plain_taxi, "Vehicle_Taxi"),
            "expected_verdict": "REJECT",
            "expected_reason": "EXECUTION_NOT_UNIQUE",
        },
        {
            # §2.11 点名：AST 相等但执行命中非 expected target。
            "name": "execution_wrong_target",
            "domain": single,
            "input": make_input("the bus", plain_bus, "Vehicle_Taxi"),
            "expected_verdict": "REJECT",
            "expected_reason": "EXECUTION_WRONG_TARGET",
        },
        {
            "name": "execution_wrong_target_color",
            "domain": single,
            "input": make_input("the yellow taxi", yellow_taxi, "Vehicle_Bus_color01"),
            "expected_verdict": "REJECT",
            "expected_reason": "EXECUTION_WRONG_TARGET",
        },
        {
            "name": "format_missing_semantic_program",
            "domain": single,
            "input": {
                **make_input("the taxi", plain_taxi, "Vehicle_Taxi"),
                "semantic_program": None,
            },
            "expected_verdict": "REJECT",
            "expected_reason": "FORMAT",
        },
        {
            "name": "format_model_tier_missing_parser_ref",
            "domain": single,
            "input": make_input(
                "the taxi",
                plain_taxi,
                "Vehicle_Taxi",
                tier="model",
                model_evidence=model_tier_evidence(complete=False),
            ),
            "expected_verdict": "REJECT",
            "expected_reason": "FORMAT",
        },
        {
            "name": "format_mechanical_tier_with_model_evidence",
            "domain": single,
            "input": make_input(
                "the taxi",
                plain_taxi,
                "Vehicle_Taxi",
                model_evidence=model_tier_evidence(),
            ),
            "expected_verdict": "REJECT",
            "expected_reason": "FORMAT",
        },
        {
            "name": "pass_model_tier_schema_only",
            "domain": single,
            "input": make_input(
                "the taxi",
                plain_taxi,
                "Vehicle_Taxi",
                tier="model",
                model_evidence=model_tier_evidence(),
            ),
            "expected_verdict": "PASS",
            "expected_reason": None,
            "note": "只走 model-tier schema 夹具；本批次**不调用模型**（BC-DATA-4）",
        },
    ]
    return fixtures
