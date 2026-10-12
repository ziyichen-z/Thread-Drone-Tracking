#!/usr/bin/env python3
"""S8 母集与模板表达（提案 §2.9；**仅门后**）。

母集 = §2.4 冻结候选集的**物化**：S8 按 `mother_candidates@attempt-k` 逐对
生成 (帧, target, amodal 框) 三元组，并对候选 id 集合做**逐 id 字节等价
断言**——物化集合与 S7 冻结外延差一条即硬错误（判定作废走 supersession）。
S8 **没有增删改任何候选的权力**，也不得反向影响门值（BC-DATA-1）。
"""

from __future__ import annotations

from typing import Any, Sequence

from tools.dist_data import contract, g0_report, make_splits, tier1_lang
from tools.dist_data.artifacts import DistDataError, canonical_json_bytes

STAGE = 8

TRAIN_SIDE: tuple[str, ...] = (make_splits.SPLIT_TRAIN, make_splits.SPLIT_DEV)


class MotherSetError(DistDataError):
    """S8 物化违反冻结外延或门前置。"""


def assert_gate_open(report: dict[str, Any]) -> None:
    """S7 任一下限不达 → S8 永不执行（§2 禁行边 + §2.8）。"""
    if report.get("gate") != g0_report.GATE_OPEN:
        raise MotherSetError(
            f"G0 门未开（{report.get('gate')}，未达下限 {report.get('unmet_floors')}）；"
            "S8 永不执行，S1–S7 工件与报告全部保全"
        )


def assert_candidate_equivalence(
    frozen: dict[str, Any], materialized: Sequence[dict[str, Any]]
) -> None:
    """逐 id 字节等价断言：差一条即硬错误。"""
    frozen_ids = list(frozen["candidate_ids"])
    materialized_ids = [item["candidate_id"] for item in materialized]
    if frozen_ids != materialized_ids:
        missing = sorted(set(frozen_ids) - set(materialized_ids))
        extra = sorted(set(materialized_ids) - set(frozen_ids))
        raise MotherSetError(
            "S8 物化集合与 S7 冻结外延不等："
            f"缺 {len(missing)}（前 3 {missing[:3]}）、多 {len(extra)}（前 3 {extra[:3]}）；"
            "S8 没有增删改任何候选的权力，判定作废走 supersession"
        )
    frozen_by_id = {item["candidate_id"]: item for item in frozen["candidates"]}
    for item in materialized:
        reference = frozen_by_id[item["candidate_id"]]
        for key in ("frame_id", "object_id", "split", "atom_id", "usage_class"):
            if item[key] != reference[key]:
                raise MotherSetError(
                    f"候选 {item['candidate_id']} 的 {key} 与冻结外延不符："
                    f"{item[key]!r} != {reference[key]!r}"
                )
        if canonical_json_bytes(item["program"]) != canonical_json_bytes(
            reference["program"]
        ):
            raise MotherSetError(
                f"候选 {item['candidate_id']} 的最小程序字节与冻结外延不符"
            )


def materialize_mother_set(
    frozen: dict[str, Any],
    report: dict[str, Any],
    amodal_box_of: dict[str, list[float]],
) -> dict[str, Any]:
    """逐对生成 (帧, target, amodal 框) 三元组并做等价断言。"""
    assert_gate_open(report)
    materialized: list[dict[str, Any]] = []
    for candidate in frozen["candidates"]:
        box = amodal_box_of.get(candidate["candidate_id"])
        if box is None:
            raise MotherSetError(
                f"候选 {candidate['candidate_id']} 缺 amodal 框；母集与未来真值框"
                "一律取 amodal-裁剪框（§2.4）"
            )
        materialized.append(
            {
                "candidate_id": candidate["candidate_id"],
                "frame_id": candidate["frame_id"],
                "object_id": candidate["object_id"],
                "split": candidate["split"],
                "atom_id": candidate["atom_id"],
                "usage_class": candidate["usage_class"],
                "program": candidate["program"],
                "amodal_box_norm_xywh": list(box),
                "train_augment_only": candidate["train_augment_only"],
                "held_out_object": candidate["held_out_object"],
                "held_out_reference": bool(candidate.get("held_out_reference")),
                "resolved_reference_object_id": candidate.get(
                    "resolved_reference_object_id"
                ),
                # BC-DATA-19：station_key 必须随三元组物化，否则 S8 工件内
                # 根本算不出 §5.1 的属性唯一单元。
                "station_key": candidate.get("station_key"),
                "floor_eligible": candidate["floor_eligible"],
            }
        )
    materialized.sort(key=lambda item: item["candidate_id"])
    assert_candidate_equivalence(frozen, materialized)
    return {"stage": STAGE, "triples": materialized, "count": len(materialized)}


def build_template_expressions(mother_set: dict[str, Any]) -> dict[str, Any]:
    """BC-DIST-1 的 template 侧：每个 train/dev target 恰一条 Tier-1 表达。

    test/D3 侧只按 §2.5 冻结对与预留，**不配训练表达**（本批次不生成任何
    确认性测试表达）。渲染经 §2.11 可逆 renderer，并当场做往返自检。
    """
    expressions: list[dict[str, Any]] = []
    for triple in mother_set["triples"]:
        if triple["split"] not in TRAIN_SIDE:
            continue
        if triple["held_out_object"]:
            raise MotherSetError(
                f"留出物体 {triple['object_id']} 出现在训练指称目标中（§2.5 机械封禁）"
            )
        # BC-DATA-17：target 与 resolved ref 两侧对称——留出物体也永不得出现在
        # 任何训练表达**文本**中，关系的 ref 名词同样算文本。
        if triple.get("held_out_reference"):
            raise MotherSetError(
                f"留出物体 {triple.get('resolved_reference_object_id')} 作为关系 ref "
                f"出现在训练表达文本中（候选 {triple['candidate_id']}，§2.5 机械封禁）"
            )
        text = tier1_lang.render(triple["program"])
        round_tripped = tier1_lang.parse(text)
        if tier1_lang.canonical_ast(round_tripped) != tier1_lang.canonical_ast(
            triple["program"]
        ):
            raise MotherSetError(f"renderer/parser 往返不一致：{text!r}")
        expressions.append(
            {
                "candidate_id": triple["candidate_id"],
                "frame_id": triple["frame_id"],
                "object_id": triple["object_id"],
                "split": triple["split"],
                "expression": text,
                "semantic_program_sha256_input": text,
                "canonical_ast": tier1_lang.canonical_ast(triple["program"]),
                "train_augment_only": triple["train_augment_only"],
            }
        )
    expressions.sort(key=lambda item: item["candidate_id"])
    targets = {item["candidate_id"] for item in expressions}
    if len(targets) != len(expressions):
        raise MotherSetError("同一 train/dev target 出现多于一条模板表达")
    return {
        "stage": STAGE,
        "expressions": expressions,
        "count": len(expressions),
        "tier": "Tier-1",
        "teacher_calls": 0,
    }


def cluster_statistics(mother_set: dict[str, Any]) -> dict[str, Any]:
    """按 §5 单位分层输出；5 Hz 近重复帧只作训练扩增，从不作独立统计单位。"""
    per_split: dict[str, dict[str, Any]] = {}
    for split in make_splits.SPLITS:
        triples = [item for item in mother_set["triples"] if item["split"] == split]
        per_split[split] = {
            "sample_count": len(triples),
            # BC-DATA-19：§5.1 属性唯一单元 = (对象, 站位簇)，**不是** (对象, 帧)。
            # 帧数 ≫ 站位簇数，用 frame id 会系统性虚高。
            "unit_count": len({(item["object_id"], item["station_key"]) for item in triples}),
            "cluster_count": len({(item["atom_id"], item["object_id"]) for item in triples}),
            "train_augment_only": sum(1 for item in triples if item["train_augment_only"]),
        }
    return {
        "per_split": per_split,
        "note": "统计单位见 §5.1；train-aug 对子进训练侧、不入 F 计数。",
    }


def reservation_lists(
    mother_set: dict[str, Any], held_out_object_ids: Sequence[str]
) -> dict[str, Any]:
    """留出物体单元清单 + 用户手写表达预留清单（§2.5，随母集一并冻结）。"""
    held_out = set(held_out_object_ids)
    test_units = sorted(
        {
            (item["object_id"], item["frame_id"])
            for item in mother_set["triples"]
            if item["split"] == make_splits.SPLIT_TEST and item["object_id"] in held_out
        }
    )
    return {
        "held_out_object_ids": sorted(held_out),
        "test_held_out_units": [
            {"object_id": object_id, "frame_id": frame_id}
            for object_id, frame_id in test_units
        ],
        "handwritten_expression_reservation": {
            "target_count_range": [50, 100],
            "units": [
                {"object_id": object_id, "frame_id": frame_id}
                for object_id, frame_id in test_units
            ],
            "note": (
                "本批次不生成任何确认性测试表达；表达来源（用户手写 50–100 条 + "
                "与训练生成器不相交的第三来源 + 盲抽审计）属 D2 前置批次。"
            ),
        },
        "mechanical_assertion": (
            "test 图像、crop、表达、改写与教师产物永不进入训练或模型选择。"
        ),
    }


def assert_test_side_never_trained(
    mother_set: dict[str, Any], template_expressions: dict[str, Any]
) -> None:
    """机械断言接口：test/D3 侧任何一条都不得出现在训练表达中。"""
    test_ids = {
        item["candidate_id"]
        for item in mother_set["triples"]
        if item["split"] in (make_splits.SPLIT_TEST, make_splits.SPLIT_D3)
    }
    offenders = sorted(
        item["candidate_id"]
        for item in template_expressions["expressions"]
        if item["candidate_id"] in test_ids
    )
    if offenders:
        raise MotherSetError(f"test/D3 侧样本进入训练表达：{offenders[:5]}")


def build_d0(
    frozen: dict[str, Any],
    report: dict[str, Any],
    amodal_box_of: dict[str, list[float]],
    held_out_object_ids: Sequence[str],
) -> dict[str, Any]:
    """S8 全量产物（母集 + 模板表达 + 统计 + 预留清单）。"""
    mother_set = materialize_mother_set(frozen, report, amodal_box_of)
    expressions = build_template_expressions(mother_set)
    assert_test_side_never_trained(mother_set, expressions)
    return {
        "stage": STAGE,
        "mother_set": mother_set,
        "template_expressions": expressions,
        "cluster_statistics": cluster_statistics(mother_set),
        "reservations": reservation_lists(mother_set, held_out_object_ids),
        "contract_version": contract.CONTRACT_VERSION,
    }
