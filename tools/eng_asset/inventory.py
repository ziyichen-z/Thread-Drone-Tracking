#!/usr/bin/env python3
"""AC-1/2/3：对账与输入清单、字段与样本清单、Tier-1 指令候选统计。

只读 `runtime/dist-data/{contract,inventory,layout,frames_catalog,splits,
field_catalog}/attempt-2`，派生工件只写合同 §3 表 A 的 A2 闭集。指令语义
**逐字复用**既有函数，不自写冲突判定：

- 执行域 = `build_catalog.frame_world(entry, field_catalog)`，调用形态与
  `run_pipeline` 的 S7 相同（不传 `world_xz` / `route_side`），因此
  `nearest_to` / `on_route_side` 恒为 `relation_available=False`，只有
  `viewer_left_of` / `viewer_right_of` 可判；
- 最小程序 = `build_catalog.minimal_program_with_reference(...)`，其确定性
  顺序原样沿用；
- 母集候选复算 = `build_catalog.prospective_mother_eligible(...)`。

`field_catalog` 取 S5 attempt-2 原样，**不调用** `apply_audit_downgrades`
（S6 审计从未执行，本项不伪造降级集）。

用法：

    python3 -m tools.eng_asset.inventory reconcile   # 仅 AC-1 对账（fail-closed）
    python3 -m tools.eng_asset.inventory run         # AC-1 + AC-2 + AC-3
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, field as dataclass_field
import gzip
import json
from pathlib import Path
import sys
import time
from typing import Any, Iterator

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import build_catalog, contract, tier1_lang  # noqa: E402
from tools.eng_asset import receipts  # noqa: E402
from tools.eng_asset.receipts import (  # noqa: E402
    InputManifest,
    ManifestCountMismatch,
    ReceiptWriter,
    ShardHashMismatch,
)

ATTEMPT = "attempt-2"
ARTIFACT_ROOT = Path("runtime/dist-data")
EVIDENCE_DIR = Path("docs/evidence")
WORK_ID = receipts.WORK_ID

# AC-1 的冻结对账目标（合同 §8 表 1 的只读试读读数）。
EXPECTED_COUNTS: dict[str, Any] = {
    "frames_catalog": {"frame_count": 43535, "shards": 151},
    "splits": {"train": 2523, "dev": 13144, "test": 8450, "d3": 0, "shards": 7},
    "field_catalog": {"objects": 690, "vehicles": 93, "dual_verified": 37},
}
# DATA-002 上界报告在 S7 语义下的冻结候选外延（AC-3 对照量，不是本项主张）。
DATA002_UPPER_BOUND_CANDIDATES = 27074

SIX_ARTIFACTS: tuple[str, ...] = (
    "contract",
    "inventory",
    "layout",
    "frames_catalog",
    "splits",
    "field_catalog",
)
COMPOSITE_ARTIFACTS: tuple[str, ...] = ("frames_catalog", "splits")

UNASSIGNED = "unassigned"
SPLIT_NAMES: tuple[str, ...] = ("train", "dev", "test", "d3", UNASSIGNED)

# 合同 §3 表 C：七值互斥，按优先序判定。
STATUS_NOT_CLASS_VERIFIED = "NOT_CLASS_VERIFIED"
STATUS_UNIQUE_CLASS = "UNIQUE_CLASS"
STATUS_UNIQUE_CLASS_COLOR = "UNIQUE_CLASS_COLOR"
STATUS_UNIQUE_RELATION = "UNIQUE_RELATION"
STATUS_WILDCARD_UNKNOWN_CLASS = "WILDCARD_UNKNOWN_CLASS"
STATUS_COLOR_UNVERIFIED = "COLOR_UNVERIFIED"
STATUS_AMBIGUOUS_SAME_CLASS = "AMBIGUOUS_SAME_CLASS"
UNIQUENESS_STATUSES: tuple[str, ...] = (
    STATUS_NOT_CLASS_VERIFIED,
    STATUS_UNIQUE_CLASS,
    STATUS_UNIQUE_CLASS_COLOR,
    STATUS_UNIQUE_RELATION,
    STATUS_WILDCARD_UNKNOWN_CLASS,
    STATUS_COLOR_UNVERIFIED,
    STATUS_AMBIGUOUS_SAME_CLASS,
)
UNIQUE_STATUSES: frozenset[str] = frozenset(
    {STATUS_UNIQUE_CLASS, STATUS_UNIQUE_CLASS_COLOR, STATUS_UNIQUE_RELATION}
)

FIELDS_SCHEMA = "p1-eng-asset-001/fields/v1"
INSTRUCTIONS_SCHEMA = "p1-eng-asset-001/instructions/v1"
SUMMARY_SCHEMA = "p1-eng-asset-001/instructions-summary/v1"


@dataclass
class Sources:
    """六件 attempt-2 工件的只读视图（inventory.json 只登记哈希，不解析）。"""

    root: Path
    attempt: str
    manifest: InputManifest
    payloads: dict[str, Any] = dataclass_field(default_factory=dict)
    artifact_sha256: dict[str, str] = dataclass_field(default_factory=dict)

    def manifest_path(self, artifact: str) -> Path:
        return self.root / artifact / self.attempt / f"{artifact}.json"

    def shard_dir(self, artifact: str) -> Path:
        return self.root / artifact / self.attempt / "shards"


def load_sources(
    root: Path,
    attempt: str,
    manifest: InputManifest,
    *,
    parse: tuple[str, ...] = ("contract", "layout", "frames_catalog", "splits", "field_catalog"),
) -> Sources:
    """登记六件工件的字节与 SHA-256；只解析需要的五件。

    `inventory.json`（50 MB）在盘点阶段只做完整性登记，其 `records[].sha256`
    索引留给面板阶段按需加载——AC-1 释义允许图像 SHA 取已核验的 S1 引用。
    """
    sources = Sources(root=Path(root), attempt=attempt, manifest=manifest)
    for artifact in SIX_ARTIFACTS:
        path = sources.manifest_path(artifact)
        if not path.is_file():
            raise ManifestCountMismatch(
                f"attempt 工件缺失：{path}", offending=[receipts.relative_to_root(path)]
            )
        entry = manifest.record(path, source="首次读取现算")
        sources.artifact_sha256[artifact] = entry.sha256
        if artifact in parse:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            if envelope.get("artifact") != artifact or envelope.get("attempt") != attempt:
                raise ManifestCountMismatch(
                    f"工件信封身份不符：{path}", offending=[receipts.relative_to_root(path)]
                )
            sources.payloads[artifact] = envelope["payload"]
    return sources


def verify_shards(sources: Sources, expected: dict[str, Any]) -> dict[str, Any]:
    """逐分片复核 SHA-256 与压缩字节（AC-1 的 151+7）。"""
    report: dict[str, Any] = {}
    for artifact in COMPOSITE_ARTIFACTS:
        payload = sources.payloads[artifact]
        shards = payload["shards"]
        declared = expected[artifact]["shards"]
        if len(shards) != declared:
            raise ManifestCountMismatch(
                f"{artifact} 分片数不符：manifest {len(shards)}，冻结期望 {declared}",
                offending=[{"artifact": artifact, "manifest": len(shards), "expected": declared}],
            )
        directory = sources.shard_dir(artifact)
        for record in shards:
            path = directory / Path(record["path"]).name
            if not path.is_file():
                raise ShardHashMismatch(
                    f"分片缺失：{path}", offending=[receipts.relative_to_root(path)]
                )
            digest = receipts.sha256_file(path)
            size = path.stat().st_size
            if digest != record["sha256"] or size != record["compressed_bytes"]:
                raise ShardHashMismatch(
                    f"分片哈希/字节不符：{path}",
                    offending=[
                        {
                            "path": receipts.relative_to_root(path),
                            "manifest_sha256": record["sha256"],
                            "actual_sha256": digest,
                            "manifest_bytes": record["compressed_bytes"],
                            "actual_bytes": size,
                        }
                    ],
                )
            sources.manifest.record(
                path,
                source=f"{artifact} manifest 引用",
                sha256=record["sha256"],
                precomputed_sha256=digest,
            )
        report[artifact] = {"shards": len(shards), "all_sha256_match": True}
    return report


def reconcile(sources: Sources, expected: dict[str, Any] = EXPECTED_COUNTS) -> dict[str, Any]:
    """AC-1：manifest 计数 + 分片 SHA-256；任一不符即抛异常（零派生工件）。"""
    catalog = sources.payloads["frames_catalog"]
    splits = sources.payloads["splits"]
    fields = sources.payloads["field_catalog"]

    mismatches: list[dict[str, Any]] = []

    def compare(name: str, actual: Any, want: Any) -> None:
        if actual != want:
            mismatches.append({"check": name, "actual": actual, "expected": want})

    compare("frames_catalog.frame_count", catalog["frame_count"], expected["frames_catalog"]["frame_count"])
    compare("frames_catalog.row_count", catalog["row_count"], expected["frames_catalog"]["frame_count"])
    for split in ("train", "dev", "test", "d3"):
        compare(f"splits.frame_counts.{split}", splits["frame_counts"][split], expected["splits"][split])
        compare(f"splits.frames.{split}", len(splits["frames"][split]), expected["splits"][split])
    objects = fields["objects"]
    vehicles = {k: v for k, v in objects.items() if k.startswith("Vehicle_")}
    compare("field_catalog.objects", len(objects), expected["field_catalog"]["objects"])
    compare("field_catalog.vehicles", len(vehicles), expected["field_catalog"]["vehicles"])
    compare(
        "field_catalog.dual_verified",
        len(fields["dual_verified_object_ids"]),
        expected["field_catalog"]["dual_verified"],
    )
    if mismatches:
        raise ManifestCountMismatch("manifest 计数与冻结期望不符", offending=mismatches)

    shard_report = verify_shards(sources, expected)
    return {
        "frames_catalog": {
            "frame_count": catalog["frame_count"],
            "row_count": catalog["row_count"],
            "skipped_invalid_frames": catalog["skipped_invalid_frames"],
            "skipped_unbound_frames": catalog["skipped_unbound_frames"],
            **shard_report["frames_catalog"],
        },
        "splits": {**splits["frame_counts"], "dropped_frames": len(splits["dropped_frames"]), **shard_report["splits"]},
        "field_catalog": {
            "objects": len(objects),
            "vehicles": len(vehicles),
            "dual_verified": len(fields["dual_verified_object_ids"]),
            "verified_color_vocabulary": list(fields["verified_color_vocabulary"]),
        },
        "artifact_sha256": dict(sources.artifact_sha256),
    }


def iter_catalog_rows(sources: Sources) -> Iterator[dict[str, Any]]:
    """按 manifest 顺序流式读 S3 行，逐分片复核行数、末尾复核总行数。"""
    payload = sources.payloads["frames_catalog"]
    directory = sources.shard_dir("frames_catalog")
    total = 0
    for record in payload["shards"]:
        path = directory / Path(record["path"]).name
        lines = 0
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                lines += 1
                total += 1
                yield json.loads(line)
        if lines != record["lines"]:
            raise ManifestCountMismatch(
                f"分片行数不符：{path} 实测 {lines} 清单 {record['lines']}",
                offending=[{"path": receipts.relative_to_root(path), "actual": lines, "manifest": record["lines"]}],
            )
    if total != payload["row_count"]:
        raise ManifestCountMismatch(
            f"S3 行总数不符：实测 {total} 清单 {payload['row_count']}",
            offending=[{"actual": total, "manifest": payload["row_count"]}],
        )


def split_index(splits_payload: dict[str, Any]) -> dict[str, str]:
    index: dict[str, str] = {}
    for split, frames in splits_payload["frames"].items():
        for frame_id in frames:
            index[frame_id] = split
    return index


def layout_vehicles(layout_payload: dict[str, Any]) -> dict[str, set[str]]:
    """按布局类列出布局车（`scene_object_name` 前缀 `Vehicle_`），只取 BOUND 分区。"""
    by_class: dict[str, set[str]] = defaultdict(set)
    for partition in layout_payload["scenario_partitions"].values():
        if partition.get("binding_status") != "BOUND":
            continue
        for instance in partition["instances"]:
            name = instance["scene_object_name"]
            if name.startswith("Vehicle_"):
                by_class[partition["layout_class"]].add(name)
    return {key: value for key, value in sorted(by_class.items())}


def short_side_px(visible_px: list[float] | None) -> float | None:
    if not visible_px:
        return None
    return min(visible_px[2] - visible_px[0], visible_px[3] - visible_px[1])


def classify_uniqueness(
    world: build_catalog.FrameWorld,
    object_id: str,
    field_catalog: dict[str, Any],
) -> tuple[str, dict[str, Any] | None, str | None]:
    """合同 §3 表 C 的七值互斥判定，全部由既有函数的返回派生。

    表 C 第 1 行先行：`minimal_program_with_reference` 在缺记录或
    `class_verified` 为假时**返回裸 None**（不是二元组），此处按首次接受释义
    先处理，其余情形再解包 `(program, ref)`。
    """
    record = field_catalog["objects"].get(object_id)
    result = build_catalog.minimal_program_with_reference(world, object_id, field_catalog)
    if result is None:
        return STATUS_NOT_CLASS_VERIFIED, None, None
    program, reference = result
    if program is not None:
        if "relation" in program:
            return STATUS_UNIQUE_RELATION, program, reference
        if "color" in program["target"]:
            return STATUS_UNIQUE_CLASS_COLOR, program, reference
        return STATUS_UNIQUE_CLASS, program, reference

    # 无程序：按表 C 第 5→6→7 序判定，冲突集用既有 `_noun_conflicts`。
    node = {"class": record["class"]}
    conflicts = [obj for obj in world.domain if tier1_lang._noun_conflicts(obj, node)]
    if any(obj.class_word is None for obj in conflicts):
        return STATUS_WILDCARD_UNKNOWN_CLASS, None, None
    if record["color_status"] != "VERIFIED" and len(conflicts) >= 2:
        return STATUS_COLOR_UNVERIFIED, None, None
    return STATUS_AMBIGUOUS_SAME_CLASS, None, None


def program_key(program: dict[str, Any] | None) -> str | None:
    return None if program is None else tier1_lang.canonical_bytes(program).decode("utf-8")


VERSIONED_FILE_MAX_BYTES = 2 * 1024 * 1024
LOCAL_DIR_MAX_BYTES = 32 * 1024 * 1024


@dataclass
class Aggregator:
    """一次流式扫描同时产出 AC-2 的清单与 AC-3 的指令统计。"""

    field_catalog: dict[str, Any]
    split_by_frame: dict[str, str]
    layout_by_class: dict[str, set[str]]
    held_out_object_ids: set[str]

    def __post_init__(self) -> None:
        self.buckets: dict[tuple[str, str, str, str], dict[str, int]] = defaultdict(
            lambda: {"frames": 0, "frames_with_referable_vehicles": 0, "frame_vehicle_pairs": 0}
        )
        self.domain_frames = 0
        self.domain_rows = 0
        self.skipped_rows = 0
        self.object_split_ok: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.object_best_short_side: dict[str, float] = {}
        self.status_hist: dict[tuple[str, bool, str], int] = defaultdict(int)
        self.split_pairs: dict[str, set[tuple[str, str]]] = defaultdict(set)
        self.split_unique_objects: dict[str, set[str]] = defaultdict(set)
        self.object_unique_rows: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # C1-3：程序集合必须逐 split 可查，不能只留跨划分的并集。
        self.object_programs: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self.mother_eligible_assigned = 0
        self.mother_eligible_domain = 0
        self.mother_eligible_by_split: dict[str, int] = defaultdict(int)

    def consume(self, entry: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """处理一条 S3 行；只有对账域内的行产出指令逐行记录。"""
        if not (entry["layout_binding_valid"] and entry["sidecar_complete"]):
            self.skipped_rows += 1
            return
        frame_id = entry["frame_id"]
        split = self.split_by_frame.get(frame_id, UNASSIGNED)
        bucket = self.buckets[(entry["layout_class"], entry["family"], split, entry["usage_class"])]
        bucket["frames"] += 1
        self.domain_frames += 1
        referable = list(entry["referable"])
        if referable:
            bucket["frames_with_referable_vehicles"] += 1
        bucket["frame_vehicle_pairs"] += len(referable)
        if not referable:
            return

        items = {item["object_id"]: item for item in entry["objects"]}
        world = build_catalog.frame_world(entry, self.field_catalog)
        mother_usage = entry["usage_class"] in contract.MOTHER_USAGE_CLASSES
        for object_id in referable:
            self.domain_rows += 1
            item = items[object_id]
            side = short_side_px(item.get("visible_px"))
            self.object_split_ok[object_id][split] += 1
            if side is not None:
                previous = self.object_best_short_side.get(object_id)
                if previous is None or side > previous:
                    self.object_best_short_side[object_id] = side
            status, program, reference = classify_uniqueness(world, object_id, self.field_catalog)
            surface = tier1_lang.render(program) if program is not None else None
            # 上游 `prospective_mother_eligible` 直接解包
            # `minimal_program_with_reference` 的返回值，而后者在「S5 无记录或
            # class_verified 为假」时返回**裸 None**，解包即 TypeError。本项不改
            # `tools/dist_data/`，故在调用侧 fail-closed 绕开：该情形按定义不可能
            # 成为母集候选（谓词要求最小程序存在），记 False 不调用上游。
            eligible = status != STATUS_NOT_CLASS_VERIFIED and (
                build_catalog.prospective_mother_eligible(
                    entry, object_id, world, self.field_catalog, self.held_out_object_ids
                )
                is not None
            )
            if eligible:
                self.mother_eligible_domain += 1
                self.mother_eligible_by_split[split] += 1
                if split != UNASSIGNED:
                    self.mother_eligible_assigned += 1
            self.status_hist[(split, mother_usage, status)] += 1
            if status in UNIQUE_STATUSES:
                key = program_key(program)
                assert key is not None  # UNIQUE_* 蕴含 program 非 null
                self.split_pairs[split].add((object_id, key))
                self.split_unique_objects[split].add(object_id)
                self.object_unique_rows[object_id][split] += 1
                self.object_programs[object_id][split].add(surface or key)
            yield {
                "frame_id": frame_id,
                "object_id": object_id,
                "split": split,
                "family": entry["family"],
                "layout_class": entry["layout_class"],
                "usage_class": entry["usage_class"],
                "mother_usage": mother_usage,
                "target_unbounded": bool(entry["target_unbounded"]),
                "program": program,
                "surface": surface,
                "resolved_reference_object_id": reference,
                "uniqueness_status": status,
                "visible_norm_xywh": item.get("visible_norm_xywh"),
                "short_side_px": side,
                "prospective_mother_eligible": eligible,
            }

    # --- AC-2 ------------------------------------------------------------
    def fields_document(self, sources: Sources, reconciliation: dict[str, Any]) -> dict[str, Any]:
        objects = self.field_catalog["objects"]
        dual_verified = set(self.field_catalog["dual_verified_object_ids"])
        all_layout_vehicles = sorted(set().union(*self.layout_by_class.values()))
        rows: list[dict[str, Any]] = []
        for object_id in all_layout_vehicles:
            record = objects.get(object_id)
            classes = sorted(k for k, v in self.layout_by_class.items() if object_id in v)
            split_counts = {
                name: self.object_split_ok.get(object_id, {}).get(name, 0) for name in SPLIT_NAMES
            }
            if record is None:
                usability, reason = "UNUSABLE", "NO_S5_ENTRY"
                evidence = (
                    "runtime/dist-data/field_catalog/attempt-2/field_catalog.json"
                    "（payload.objects 无该 object_id）；提案 §6「8 辆布局车在 S5 无条目」"
                )
                colour: dict[str, Any] = {
                    "class": None,
                    "class_verified": False,
                    "color": None,
                    "color_status": None,
                    "color_downgrade_reason": None,
                }
            else:
                colour = {
                    "class": record["class"],
                    "class_verified": bool(record["class_verified"]),
                    "color": record["color"],
                    "color_status": record["color_status"],
                    "color_downgrade_reason": record.get("color_downgrade_reason"),
                }
                if record["color_status"] == "VERIFIED":
                    usability, reason = "USABLE", "CLASS_AND_COLOR_VERIFIED"
                    evidence = "S5 记录 color_status=VERIFIED；dual_verified_object_ids 成员"
                else:
                    usability = "UNVERIFIED"
                    reason = record.get("color_downgrade_reason") or "NO_DOMINANT_COLOR"
                    evidence = (
                        "S5 记录 color_status=UNVERIFIED"
                        f"（downgrade_reason={record.get('color_downgrade_reason')}）；"
                        "P1-VLM-DATA-002 颜色诊断（状态板 2026-09-07 条目）"
                    )
            rows.append(
                {
                    "object_id": object_id,
                    "layout_classes": classes,
                    "s5_entry": record is not None,
                    "dual_verified": object_id in dual_verified,
                    **colour,
                    "split_ok_frames": split_counts,
                    "ok_frames_total": sum(split_counts.values()),
                    "best_short_side_px": self.object_best_short_side.get(object_id),
                    "usability": usability,
                    "usability_reason": reason,
                    "evidence": evidence,
                }
            )
        vehicles = {k: v for k, v in objects.items() if k.startswith("Vehicle_")}
        verified = [k for k, v in vehicles.items() if v["color_status"] == "VERIFIED"]
        inconsistent = [
            k
            for k, v in vehicles.items()
            if v["color_status"] != "VERIFIED" and v.get("color_downgrade_reason") == "GROUP_INCONSISTENT"
        ]
        no_dominant = [
            k
            for k, v in vehicles.items()
            if v["color_status"] != "VERIFIED" and v.get("color_downgrade_reason") != "GROUP_INCONSISTENT"
        ]
        missing = [row["object_id"] for row in rows if not row["s5_entry"]]
        classification = [
            {
                "field": "class（类别词）",
                "scope": f"S5 目录车 {len(vehicles)}/{len(vehicles)} class_verified",
                "classification": "USABLE",
                "count": len(vehicles),
                "evidence": "runtime/dist-data/field_catalog/attempt-2 payload.objects[*].class_verified",
            },
            {
                "field": "color（颜色词）",
                "scope": "color_status=VERIFIED",
                "classification": "USABLE",
                "count": len(verified),
                "evidence": "S5 color_status=VERIFIED；已验证词表 "
                + "/".join(self.field_catalog["verified_color_vocabulary"]),
            },
            {
                "field": "color（颜色词）",
                "scope": "GROUP_INCONSISTENT 降级",
                "classification": "UNVERIFIED",
                "count": len(inconsistent),
                "evidence": "S5 color_downgrade_reason=GROUP_INCONSISTENT；P1-VLM-DATA-002 颜色诊断"
                "（`docs/current-status.md` 2026-09-07 条目：补采不会移动 U_F1）",
            },
            {
                "field": "color（颜色词）",
                "scope": "无主色（无 color_evidence 主色）",
                "classification": "UNVERIFIED",
                "count": len(no_dominant),
                "evidence": "S5 color_status=UNVERIFIED 且无 GROUP_INCONSISTENT 降级理由",
            },
            {
                "field": "visible_norm_xywh（框）",
                "scope": "对账域全部 (帧, 车) 行",
                "classification": "UNVERIFIED",
                "count": self.domain_rows,
                "evidence": "S3 几何投影框，来源为 Unity 几何投影而非人工标注；"
                "语义正确性只有 AC-4 的 n≤60 描述性抽查，DATA-001 S6 人工审计从未执行"
                "（`docs/implementation-status.md` 工程继承清单）",
            },
            {
                "field": "布局车（无 S5 条目）",
                "scope": "layout ∖ S5",
                "classification": "UNUSABLE",
                "count": len(missing),
                "evidence": "从未以 OK 出现于任何 BOUND 帧；" + "、".join(missing),
            },
        ]
        buckets = [
            {
                "layout_class": key[0],
                "family": key[1],
                "split": key[2],
                "usage_class": key[3],
                **value,
            }
            for key, value in sorted(self.buckets.items())
        ]
        return {
            "schema_version": FIELDS_SCHEMA,
            "work_id": WORK_ID,
            "attempt": sources.attempt,
            "source_artifact_sha256": dict(sources.artifact_sha256),
            "reconciliation": reconciliation,
            "domain": {
                "definition": "S3 行中 layout_binding_valid ∧ sidecar_complete",
                "frames": self.domain_frames,
                "frame_vehicle_pairs": self.domain_rows,
                "excluded_rows": self.skipped_rows,
            },
            "buckets": buckets,
            "layout_vehicles": rows,
            "layout_vehicle_counts": {
                "total": len(all_layout_vehicles),
                "per_layout_class": {k: len(v) for k, v in self.layout_by_class.items()},
                "without_s5_entry": len(missing),
            },
            "field_classification": classification,
        }

    # --- AC-3 ------------------------------------------------------------
    def summary_document(self, sources: Sources) -> dict[str, Any]:
        histogram: dict[str, dict[str, dict[str, int]]] = {}
        for split in SPLIT_NAMES:
            per_usage: dict[str, dict[str, int]] = {}
            for mother_usage in (True, False):
                counts = {
                    status: self.status_hist.get((split, mother_usage, status), 0)
                    for status in UNIQUENESS_STATUSES
                }
                per_usage["mother_usage" if mother_usage else "non_mother_usage"] = counts
            histogram[split] = per_usage
        per_object = []
        for object_id in sorted(self.object_unique_rows):
            per_object.append(
                {
                    "object_id": object_id,
                    "unique_rows_by_split": {
                        name: self.object_unique_rows[object_id].get(name, 0) for name in SPLIT_NAMES
                    },
                    "programs_by_split": {
                        name: sorted(self.object_programs[object_id].get(name, set()))
                        for name in SPLIT_NAMES
                    },
                    "programs": sorted(
                        set().union(*self.object_programs[object_id].values())
                        if self.object_programs[object_id]
                        else set()
                    ),
                    "held_out_object": object_id in self.held_out_object_ids,
                }
            )
        train = self.split_unique_objects.get("train", set())
        dev = self.split_unique_objects.get("dev", set())
        test = self.split_unique_objects.get("test", set())
        overlap = {
            "domain": "各 split 的 UNIQUE_* 目标行（去重对象）",
            "train_objects": len(train),
            "dev_objects": len(dev),
            "test_objects": len(test),
            "train_inter_test": sorted(train & test),
            "dev_inter_test": sorted(dev & test),
            "test_only": sorted(test - train - dev),
            "held_out_object_ids": sorted(self.held_out_object_ids),
            "held_out_marked_in_test": sorted(test & self.held_out_object_ids),
            "note": "S4 held_out_objects 标记原样继承；本表只描述既有划分，"
            "两者都不得读作「对象从未出现在训练图像中」，也不构成正式评估集",
        }
        return {
            "schema_version": SUMMARY_SCHEMA,
            "work_id": WORK_ID,
            "attempt": sources.attempt,
            "source_artifact_sha256": dict(sources.artifact_sha256),
            "uniqueness_status_histogram": histogram,
            "per_split_dedup": {
                split: {
                    "object_program_pairs": len(self.split_pairs.get(split, set())),
                    "objects": len(self.split_unique_objects.get(split, set())),
                }
                for split in SPLIT_NAMES
            },
            "per_object": per_object,
            "object_overlap": overlap,
            "prospective_mother_eligible": {
                "assigned_frames_total": self.mother_eligible_assigned,
                "domain_total": self.mother_eligible_domain,
                "by_split": {name: self.mother_eligible_by_split.get(name, 0) for name in SPLIT_NAMES},
                "data002_upper_bound_report": DATA002_UPPER_BOUND_CANDIDATES,
                "difference_assigned_vs_report": self.mother_eligible_assigned
                - DATA002_UPPER_BOUND_CANDIDATES,
                "difference_domain_vs_report": self.mother_eligible_domain
                - DATA002_UPPER_BOUND_CANDIDATES,
                "difference_source": "AC-3 要求的复算域是 S4 已划分帧（train/dev/test/d3），"
                "而 DATA-002 上界报告的冻结候选外延覆盖对账域全部帧；两者之差恰为"
                "未入划分帧上的候选数，谓词本身逐字复用 build_catalog."
                "prospective_mother_eligible，未作任何放宽。",
            },
            "frozen_evaluation_set": False,
        }


def _write_instructions(path: Path, rows: Iterator[dict[str, Any]]) -> int:
    """流式写 gzip-NDJSON（确定性 gzip 头：mtime=0），返回行数。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(path, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as handle:
            for row in rows:
                handle.write(
                    (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
                )
                written += 1
    return written


def _write_json_document(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in Path(path).rglob("*") if item.is_file())


def run(
    *,
    root: Path = ARTIFACT_ROOT,
    attempt: str = ATTEMPT,
    repo_root: Path = PROJECT_ROOT,
    local_root: Path | None = None,
    evidence_dir: Path | None = None,
    expected: dict[str, Any] = EXPECTED_COUNTS,
    stage: str = "inventory",
) -> dict[str, Any]:
    """AC-1 + AC-2 + AC-3 的一次执行：对账 → 流式盘点 → 发布派生工件。

    发布点在输入清单 before/after 逐条相等**之后**：中途任何失败只留失败收据，
    不发布该次成功工件（AC-1/AC-6 首次接受释义）。
    """
    repo_root = Path(repo_root)
    artifact_root = Path(root) if Path(root).is_absolute() else repo_root / root
    local = Path(local_root) if local_root is not None else repo_root / receipts.LOCAL_ROOT
    evidence = Path(evidence_dir) if evidence_dir is not None else repo_root / EVIDENCE_DIR
    writer = ReceiptWriter(local, repo_root)
    manifest = InputManifest(repo_root=repo_root)
    started = time.monotonic()
    staging = local / ".staging"
    # C1-1：路径检查先于任何字节写入（含 staging 自身的创建/清理）。
    receipts.assert_output_allowed(local, repo_root)
    receipts.assert_output_allowed(staging, repo_root)
    try:
        if staging.exists():
            for item in sorted(staging.rglob("*"), reverse=True):
                item.unlink() if item.is_file() else item.rmdir()
        staging.mkdir(parents=True, exist_ok=True)

        sources = load_sources(artifact_root, attempt, manifest)
        reconciliation = reconcile(sources, expected)

        splits_payload = sources.payloads["splits"]
        aggregator = Aggregator(
            field_catalog=sources.payloads["field_catalog"],
            split_by_frame=split_index(splits_payload),
            layout_by_class=layout_vehicles(sources.payloads["layout"]),
            held_out_object_ids=set(splits_payload["held_out_objects"]["held_out_object_ids"]),
        )

        def rows() -> Iterator[dict[str, Any]]:
            for entry in iter_catalog_rows(sources):
                yield from aggregator.consume(entry)

        staged_instructions = staging / "instructions.ndjson.gz"
        line_count = _write_instructions(staged_instructions, rows())

        fields_document = aggregator.fields_document(sources, reconciliation)
        summary_document = aggregator.summary_document(sources)
        fields_document["instruction_row_count"] = line_count
        staged_fields = staging / f"{WORK_ID}-fields.json"
        staged_summary = staging / f"{WORK_ID}-instructions-summary.json"
        _write_json_document(staged_fields, fields_document)
        _write_json_document(staged_summary, summary_document)

        if line_count != aggregator.domain_rows:
            raise ManifestCountMismatch(
                f"指令逐行文件行数 {line_count} 与对账域 (帧,车) 对 {aggregator.domain_rows} 不符",
                offending=[{"lines": line_count, "domain_rows": aggregator.domain_rows}],
            )

        after = manifest.recompute()
        mismatches = manifest.diff(after)
        if mismatches:
            raise receipts.InputHashChanged("执行前后输入清单不符", offending=mismatches)

        publications = [
            (staged_instructions, local / "instructions.ndjson.gz"),
            (staged_fields, evidence / f"{WORK_ID}-fields.json"),
            (staged_summary, evidence / f"{WORK_ID}-instructions-summary.json"),
        ]
        # C1-1：先整体核验全部目的地，再逐件发布——逐个检查并立即 replace 会在后一个
        # 目的地被拒时留下已发布的前件。
        for _staged, final in publications:
            receipts.assert_output_allowed(final, repo_root)
        outputs: list[dict[str, Any]] = []
        for staged, final in publications:
            final.parent.mkdir(parents=True, exist_ok=True)
            staged.replace(final)
            record = receipts.output_record(final, lines=line_count if final.suffix == ".gz" else None)
            record["versioned"] = evidence in final.parents
            outputs.append(record)

        budget = {
            "versioned_max_bytes": VERSIONED_FILE_MAX_BYTES,
            "versioned_violations": [
                item["path"] for item in outputs if item["versioned"] and item["bytes"] > VERSIONED_FILE_MAX_BYTES
            ],
            "local_dir_bytes": directory_bytes(local),
            "local_dir_max_bytes": LOCAL_DIR_MAX_BYTES,
        }
        budget["local_dir_within_budget"] = budget["local_dir_bytes"] <= LOCAL_DIR_MAX_BYTES
        manifest_path = writer.save_input_manifest(stage, manifest, after, mismatches, successful=True)
        receipt = writer.write_run_receipt(
            stage,
            started=started,
            outputs=outputs,
            extra={
                "reconciliation": reconciliation,
                "domain": fields_document["domain"],
                "budget": budget,
                "input_manifest": receipts.relative_to_root(manifest_path, repo_root),
                "input_files": len(manifest.entries),
            },
        )
        return {
            "reconciliation": reconciliation,
            "fields": fields_document,
            "summary": summary_document,
            "outputs": outputs,
            "budget": budget,
            "receipt": receipts.relative_to_root(receipt, repo_root),
        }
    except receipts.EngAssetError as exc:
        after = manifest.recompute() if manifest.entries else {}
        writer.save_input_manifest(stage, manifest, after, manifest.diff(after), successful=False)
        writer.write_failure_receipt(stage, exc.reason, exc.offending, message=str(exc))
        raise
    finally:
        if staging.exists():
            for item in sorted(staging.rglob("*"), reverse=True):
                item.unlink() if item.is_file() else item.rmdir()
            staging.rmdir()


def sample(root: Path, attempt: str, shards: int, repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """诊断用：只扫前 N 个分片并打印统计，**不写任何文件、不作证据**。"""
    repo_root = Path(repo_root)
    artifact_root = Path(root) if Path(root).is_absolute() else repo_root / root
    manifest = InputManifest(repo_root=repo_root)
    sources = load_sources(artifact_root, attempt, manifest)
    splits_payload = sources.payloads["splits"]
    aggregator = Aggregator(
        field_catalog=sources.payloads["field_catalog"],
        split_by_frame=split_index(splits_payload),
        layout_by_class=layout_vehicles(sources.payloads["layout"]),
        held_out_object_ids=set(splits_payload["held_out_objects"]["held_out_object_ids"]),
    )
    directory = sources.shard_dir("frames_catalog")
    rows = 0
    for record in sources.payloads["frames_catalog"]["shards"][:shards]:
        with gzip.open(directory / Path(record["path"]).name, "rt", encoding="utf-8") as handle:
            for line in handle:
                for _row in aggregator.consume(json.loads(line)):
                    rows += 1
    return {
        "diagnostic_only": True,
        "shards": shards,
        "instruction_rows": rows,
        "domain_frames": aggregator.domain_frames,
        "status_histogram": {
            status: sum(v for k, v in aggregator.status_hist.items() if k[2] == status)
            for status in UNIQUENESS_STATUSES
        },
        "peak_rss_bytes": receipts.peak_rss_bytes(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("reconcile", "run", "sample"))
    parser.add_argument("--root", default=str(ARTIFACT_ROOT))
    parser.add_argument("--attempt", default=ATTEMPT)
    parser.add_argument("--shards", type=int, default=2, help="sample 子命令扫描的分片数")
    args = parser.parse_args(argv)

    if args.command == "sample":
        print(json.dumps(sample(Path(args.root), args.attempt, args.shards), ensure_ascii=False, indent=2))
        return 0
    if args.command == "reconcile":
        manifest = InputManifest()
        writer = ReceiptWriter()
        started = time.monotonic()
        try:
            sources = load_sources(PROJECT_ROOT / args.root, args.attempt, manifest)
            report = reconcile(sources)
        except receipts.EngAssetError as exc:
            writer.write_failure_receipt("reconcile", exc.reason, exc.offending, message=str(exc))
            print(f"对账失败（{exc.reason}）：{exc}", file=sys.stderr)
            return 1
        after = manifest.recompute()
        writer.save_input_manifest("reconcile", manifest, after, manifest.diff(after), successful=True)
        writer.write_run_receipt("reconcile", started=started, outputs=[], extra={"reconciliation": report})
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    result = run(root=Path(args.root), attempt=args.attempt)
    print(
        json.dumps(
            {
                "domain": result["fields"]["domain"],
                "outputs": result["outputs"],
                "budget": result["budget"],
                "receipt": result["receipt"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
