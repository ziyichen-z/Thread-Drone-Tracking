#!/usr/bin/env python3
"""S7 `mother_candidates` 冻结、F1–F4 计算与 G0 门判定（§2.8 / §5，BC-DATA-1）。

S7 **只读**冻结的 S1–S6 工件：F3/F4 由 `prospective_mother_eligible` 的
最终外延与 `mother_candidates@attempt-k` 派生，**不读任何 S8 产物**；F1–F4
的数值与全部分母在 round 3 已冻结，任何实测结果、审计失败或 atom 合并
均不得回调。
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from tools.dist_data import contract, make_splits
from tools.dist_data.artifacts import DistDataError

STAGE = 7

GATE_OPEN = "OPEN"
GATE_INSUFFICIENT = "INSUFFICIENT_SYMBOLIC_GROUNDING_DATA"

TRAIN_DEV: tuple[str, ...] = (make_splits.SPLIT_TRAIN, make_splits.SPLIT_DEV)
# BC-DATA-19：连带退出帧的显式标记（不是第五个 split，只是冻结外延里的标签）。
SPLIT_DROPPED = "dropped"


class GateError(DistDataError):
    """S7 门计算失败。"""


def floor_eligible(entry: dict[str, Any], split: str | None) -> bool:
    """§5.1 floor-eligible 帧：`pre_split_floor_eligible` ∧ 属于对应 split。"""
    from tools.dist_data.build_catalog import pre_split_floor_eligible

    if not pre_split_floor_eligible(entry):
        return False
    return split is not None and entry.get("split") == split


def freeze_mother_candidates(
    candidates: Sequence[dict[str, Any]],
    split_of_frame: dict[str, str],
    atom_of_frame: dict[str, str],
    held_out_object_ids: Iterable[str],
    dropped_frames: Iterable[str] = (),
) -> dict[str, Any]:
    """把谓词全外延连同逐对最小程序、用途类、split、floor 资格标记冻结。

    S8 不得重算或偏离本外延（§2.9 逐 id 等价断言）。
    """
    held_out = set(held_out_object_ids)
    dropped = set(dropped_frames)
    frozen: list[dict[str, Any]] = []
    for candidate in candidates:
        frame_id = candidate["frame_id"]
        split = split_of_frame.get(frame_id)
        split_reason = None
        if split is None:
            # BC-DATA-19：因 test/D3 连带规则整体退出的帧，其候选写显式
            # `dropped` 标记与原因，不抛 split 缺失错误——否则谓词全外延
            # 在真实归档上根本无法冻结（复核 F6）。
            if frame_id not in dropped:
                raise GateError(f"候选帧未获 split 指派：{frame_id}")
            split = SPLIT_DROPPED
            split_reason = "dropped by test/D3 carry-over rule (§2.5 连带规则)"
        atom_id = atom_of_frame.get(frame_id)
        if atom_id is None:
            raise GateError(f"候选帧未获 atom 指派：{frame_id}")
        floor = (
            split != SPLIT_DROPPED
            and bool(candidate.get("pre_split_floor_eligible"))
            and candidate.get("floor_usage", False)
        )
        frozen.append(
            {
                **candidate,
                "candidate_id": f"{frame_id}|{candidate['object_id']}",
                "split": split,
                "split_reason": split_reason,
                "atom_id": atom_id,
                "floor_eligible": floor,
                "held_out_object": candidate["object_id"] in held_out,
                # BC-DATA-17：**在 S7 重新派生**，不信 S4 阶段可能以默认空集
                # 打上的标记——谓词的 held_out 参数有默认值，生产驱动很容易
                # 漏传，那样留出物体会一路走到训练表达文本里。
                "held_out_reference": bool(
                    candidate.get("resolved_reference_object_id") in held_out
                    and candidate.get("resolved_reference_object_id") is not None
                ),
                "train_augment_only": candidate["usage_class"]
                in contract.TRAIN_AUGMENT_USAGE_CLASSES,
            }
        )
    frozen.sort(key=lambda item: item["candidate_id"])
    ids = [item["candidate_id"] for item in frozen]
    if len(set(ids)) != len(ids):
        raise GateError("候选 id 重复：(帧, 对象) 必须唯一")
    return {
        "stage": STAGE,
        "candidate_count": len(frozen),
        "candidate_ids": ids,
        "candidates": frozen,
    }


# --- F1–F4 -----------------------------------------------------------------
def compute_f1(field_catalog: dict[str, Any]) -> dict[str, Any]:
    """F1：class+color 双验证对象数 / 101，且 ≥6 类各有 ≥1 双验证实例。"""
    dual = sorted(field_catalog.get("dual_verified_object_ids", []))
    classes = sorted(
        {
            field_catalog["objects"][object_id]["class"]
            for object_id in dual
            if field_catalog["objects"][object_id]["class"]
        }
    )
    floors = contract.FLOORS["F1"]
    passed = (
        len(dual) >= floors["min_objects"]
        and len(classes) >= floors["min_classes_with_dual_verified"]
    )
    return {
        "value": len(dual),
        "denominator": floors["object_denominator"],
        "classes_with_dual_verified": classes,
        "floor": {
            "min_objects": floors["min_objects"],
            "min_classes": floors["min_classes_with_dual_verified"],
        },
        "passed": passed,
        "dual_verified_object_ids": dual,
    }


def compute_f2(entries: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """F2：floor-eligible 帧上的站位簇（全局分箱键的非空箱，跨族自动合并）。"""
    from tools.dist_data.build_catalog import pre_split_floor_eligible

    global_keys: set[str] = set()
    per_split: dict[str, set[str]] = {split: set() for split in make_splits.SPLITS}
    for entry in entries:
        if not pre_split_floor_eligible(entry):
            continue
        key = entry["station_bin"]["key"]
        if key is None:
            continue
        split = entry.get("split")
        if split not in make_splits.SPLITS:
            continue
        global_keys.add(key)
        per_split[split].add(key)
    floors = contract.FLOORS["F2"]
    test_count = len(per_split[make_splits.SPLIT_TEST])
    passed = len(global_keys) >= floors["min_global"] and test_count >= floors["min_test"]
    return {
        "global": len(global_keys),
        "per_split": {split: len(keys) for split, keys in sorted(per_split.items())},
        "floor": {"min_global": floors["min_global"], "min_test": floors["min_test"]},
        "passed": passed,
        "station_keys": sorted(global_keys),
    }


def compute_f3(
    frozen: dict[str, Any], station_of_frame: dict[str, str | None]
) -> dict[str, Any]:
    """F3：属性唯一单元 (对象, 站位簇)；同单元任意多帧计 1。"""
    units: dict[str, set[tuple[str, str]]] = {"train_dev": set(), "test": set()}
    held_out_test_units: set[tuple[str, str]] = set()
    classes: dict[str, set[str]] = {"train_dev": set(), "test": set()}
    for candidate in frozen["candidates"]:
        if not candidate["floor_eligible"] or candidate["program_kind"] != "attribute":
            continue
        station = station_of_frame.get(candidate["frame_id"])
        if station is None:
            continue
        unit = (candidate["object_id"], station)
        class_word = candidate["program"]["target"]["class"]
        if candidate["split"] in TRAIN_DEV:
            units["train_dev"].add(unit)
            classes["train_dev"].add(class_word)
        elif candidate["split"] == make_splits.SPLIT_TEST:
            units["test"].add(unit)
            classes["test"].add(class_word)
            if candidate["held_out_object"]:
                held_out_test_units.add(unit)
    floors = contract.FLOORS["F3"]
    passed = (
        len(units["train_dev"]) >= floors["min_train_dev"]
        and len(units["test"]) >= floors["min_test"]
        and len(held_out_test_units) >= floors["min_test_heldout_units"]
        and len(classes["train_dev"]) >= floors["min_train_classes"]
        and len(classes["test"]) >= floors["min_test_classes"]
    )
    return {
        "train_dev": len(units["train_dev"]),
        "test": len(units["test"]),
        "test_held_out_units": len(held_out_test_units),
        "train_dev_classes": sorted(classes["train_dev"]),
        "test_classes": sorted(classes["test"]),
        "floor": dict(floors),
        "passed": passed,
    }


def compute_f4(frozen: dict[str, Any]) -> dict[str, Any]:
    """F4：统计簇 (atom_id, 对象)；lineage 键 = §2.5 并簇后最终原子。"""
    clusters: dict[str, set[tuple[str, str]]] = {"train_dev": set(), "test": set()}
    for candidate in frozen["candidates"]:
        if not candidate["floor_eligible"]:
            continue
        cluster = (candidate["atom_id"], candidate["object_id"])
        if candidate["split"] in TRAIN_DEV:
            clusters["train_dev"].add(cluster)
        elif candidate["split"] == make_splits.SPLIT_TEST:
            clusters["test"].add(cluster)
    floors = contract.FLOORS["F4"]
    passed = (
        len(clusters["train_dev"]) >= floors["min_train_dev"]
        and len(clusters["test"]) >= floors["min_test"]
    )
    return {
        "train_dev": len(clusters["train_dev"]),
        "test": len(clusters["test"]),
        "floor": dict(floors),
        "passed": passed,
        "resampling_unit": "(atom_id, object_id)（BC-DIST-3 的重采样单位不得细于此）",
    }


def stratified_denominators(
    entries: Sequence[dict[str, Any]], frozen: dict[str, Any]
) -> dict[str, Any]:
    """§2.8 同表分层分母：逐 split / 对象 / 站位 / 布局类 / 用途类。"""

    def _count(items: Iterable[Any]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            key = str(item)
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    candidates = frozen["candidates"]
    return {
        "frames_by_split": _count(entry.get("split") for entry in entries),
        "frames_by_layout_class": _count(entry["layout_class"] for entry in entries),
        "frames_by_usage_class": _count(entry["usage_class"] for entry in entries),
        "frames_by_station": _count(
            entry["station_bin"]["key"] for entry in entries if entry["station_bin"]["key"]
        ),
        "candidates_by_split": _count(item["split"] for item in candidates),
        "candidates_by_object": _count(item["object_id"] for item in candidates),
        "candidates_by_layout_class": _count(item["layout_class"] for item in candidates),
        "candidates_by_usage_class": _count(item["usage_class"] for item in candidates),
        "candidates_by_program_kind": _count(item["program_kind"] for item in candidates),
    }


def exclusion_histogram(entries: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """排除原因直方图（含 `TARGET_UNBOUNDED` 帧数）与逐对象状态汇总。"""
    statuses = {status: 0 for status in contract.OBJECT_STATUSES}
    target_unbounded = 0
    for entry in entries:
        if entry["target_unbounded"]:
            target_unbounded += 1
        for status, count in entry["status_histogram"].items():
            statuses[status] = statuses.get(status, 0) + count
    return {
        "object_status_totals": dict(sorted(statuses.items())),
        "target_unbounded_frames": target_unbounded,
        "frame_total": len(entries),
        "registered_risk": (
            "nature/prop 的巨大 AABB 过包围会把画家序遮挡判得偏严，压低 eligible "
            "计数（方向 = 少算不多算）；下限不因此回调。"
        ),
    }


def co_visibility_distribution(entries: Sequence[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        key = str(entry["co_visible_count"])
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: int(item[0])))


def build_g0_report(
    *,
    entries: Sequence[dict[str, Any]],
    frozen: dict[str, Any],
    field_catalog: dict[str, Any],
    splits_payload: dict[str, Any],
    layout_payload: dict[str, Any],
    audit_results: dict[str, Any],
    relation_availability: dict[str, Any],
) -> dict[str, Any]:
    """`g0_report@attempt-k`：F1–F4 + 全部分层分母 + 门判定。

    exposure 汇总**只能**取自同一份 `splits_payload`（复核轮 2 F11），交叉验证
    结果**只能**取自同一份 `layout_payload`（BC-DATA-23，复核轮 4 F16）：独立的
    `exposure` / `cross_validation` 参数都已删除，报告与 S2/S4 工件因此不可能
    各说各话。缺任一成员即 KeyError 硬失败，不静默补空表。
    """
    exposure = splits_payload["exposure_matrix"]
    # BC-DATA-23 (5)：交叉验证结果同样只能取自同一份 S2 载荷的**必有成员**，
    # 缺成员 KeyError 硬失败——「从未验证」绝不得静默成空表。
    cross_validation = layout_payload["cross_validation"]
    station_of_frame = {
        entry["frame_id"]: entry["station_bin"]["key"] for entry in entries
    }
    f1 = compute_f1(field_catalog)
    f2 = compute_f2(entries)
    f3 = compute_f3(frozen, station_of_frame)
    f4 = compute_f4(frozen)
    floors_passed = all(item["passed"] for item in (f1, f2, f3, f4))
    unmet = [
        name for name, item in (("F1", f1), ("F2", f2), ("F3", f3), ("F4", f4))
        if not item["passed"]
    ]
    return {
        "stage": STAGE,
        "floors": {"F1": f1, "F2": f2, "F3": f3, "F4": f4},
        "gate": GATE_OPEN if floors_passed else GATE_INSUFFICIENT,
        "unmet_floors": unmet,
        "gate_note": (
            "全部下限达标 → S8 启动；任一下限不达 → 本 work item 以 "
            "INSUFFICIENT_SYMBOLIC_GROUNDING_DATA 收束，S1–S7 工件与报告全部保全，"
            "S8 永不执行；采集补数只能由用户另立消耗性 work item 授权。"
        ),
        "stratified_denominators": stratified_denominators(entries, frozen),
        "exclusion_histogram": exclusion_histogram(entries),
        "co_visibility_distribution": co_visibility_distribution(entries),
        "station_clustering": {
            "keys": f2["station_keys"],
            "bin_definition": "位置 (⌊x/2⌋, ⌊z/2⌋) × 方位 15° × 俯角带 3",
        },
        "relation_availability": relation_availability,
        "exposure_matrix": exposure,
        "cross_validation": cross_validation,
        "audit_results": audit_results,
        "splits": {
            "atom_assignment": splits_payload["atom_assignment"],
            "frame_counts": splits_payload["frame_counts"],
            "d3_holdout_empty": splits_payload["d3_holdout_empty"],
            "dropped_frames": len(splits_payload["dropped_frames"]),
        },
        "mother_candidates": {
            "count": frozen["candidate_count"],
            "floor_eligible": sum(
                1 for item in frozen["candidates"] if item["floor_eligible"]
            ),
            "train_augment_only": sum(
                1 for item in frozen["candidates"] if item["train_augment_only"]
            ),
        },
    }
