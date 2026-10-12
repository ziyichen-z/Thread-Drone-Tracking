#!/usr/bin/env python3
"""K4 数据合同构建器：对账、三态派生、训练/选层/评估集、预检、冻结与打包。

阶段（表 K「生成先后」，各自一条 CLI 子命令，互不自引用）：

    build    → jsonl（含 smoke.jsonl）/ 盲文件 / 四份冻结 JSON
    precheck → 本地同版 tokenizer 对全部 gold 逐条实测的预检收据（表 H）
    audit    → 见 `label_audit.py`（表 J）
    freeze   → 冻结收据（提交后；前提：用户份额判定齐全、无未裁定「错」、预检收据在）
    package  → K4 数据包（帧 + data + manifests + upload/manifest.json；**不含代码**）

只读输入闭集见合同 §3；身份一律运行时解析并记入输入清单，不手写 SHA。任一不符
只写失败收据，不发布该次工件。取样常量与函数逐字按表 D′，训练/选层按表 E，冻结
评估集按表 D，序列化按表 C 与 AC-5 修订 1（UTF-8、`ensure_ascii=True`、紧凑分隔符、
每行一个 LF；gold 文本另按表 B 的缺省空格分隔符）。

本模块不进 K3 代码束（三态已在本地派生），也不 import `controller.*`。
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import glob
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
from typing import Any, Iterable, Iterator, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import build_catalog  # noqa: E402
from tools.dist_data import contract as dist_contract  # noqa: E402
from tools.dist_data import tier1_lang  # noqa: E402
from tools.eng_asset import inventory as asset_inventory  # noqa: E402
from tools.eng_sft import prompt_v2, receipts  # noqa: E402
from tools.eng_sft.adapters import unity_s3  # noqa: E402
from tools.eng_sft.three_state import (  # noqa: E402
    DYNAMIC_TARGET_ID,
    STATE_AMBIGUOUS,
    STATE_GRAY_DEFINITE_PLUS_UNCERTAIN,
    STATE_NONE,
    STATE_UNIQUE,
    three_state,
)

# --- 表 D′ / 表 E / 表 D 的冻结常量 --------------------------------------

SEED = "tdt-eng-sft-002-2026-09-13"
SELECTION_FAMILY = "detect-scout1"
WEAK_CLASSES: frozenset[str] = frozenset({"car", "pickup truck", "truck", "suv"})

# E2 稀疏间隔。
GAP_AMBIGUOUS = 2
GAP_NONE = 5
GAP_UNIQUE_WEAK_OR_SMALL = 2
GAP_UNIQUE_OTHER = 5
# E3/E4 配额。
CLASS_QUOTA = 700
OBJECT_QUOTA = 350
AMBIGUOUS_KEY_QUOTA = 60
# E5/E6。
NONE_SHARE = 0.10
AMBIGUOUS_SHARE = 0.15
COPY_MAX = 8
# E8 选层评估子集。
SELECT_UNIQUE_CAP = 300
SELECT_NONE_CAP = 100
# 表 D/D′ 评估准入。
ADMIT_KEY_MAX = 4
ADMIT_MIN_INDEX_GAP = 30
G5_CLASS_MAX = 12
EVAL_QUOTA: dict[str, int] = {"G3p": 50, "G5": 100}
GROUP_ORDER: tuple[str, ...] = ("G1", "G1t", "G2", "G2t", "G3", "G3t", "G3p", "G4", "G5")
GATE_GROUPS: frozenset[str] = frozenset({"G1", "G2", "G3", "G5"})
LEGACY_ONLY_GROUP = "LEGACY_ONLY"
# 任一为空即 `EVAL_GROUP_EMPTY`（AC-3）。
REQUIRED_NONEMPTY_GROUPS: tuple[str, ...] = ("G1", "G3", "G5")
# 表 H 冒烟 32 条：unique class 8 + unique color 8 + ambiguous 8 + none 8。
SMOKE_QUOTA: tuple[tuple[str, str | None, int], ...] = (
    (STATE_UNIQUE, "class", 8),
    (STATE_UNIQUE, "color", 8),
    (STATE_AMBIGUOUS, None, 8),
    (STATE_NONE, None, 8),
)
STRATA_ORDER: tuple[str, ...] = ("S", "M", "L", "NA")
VOCAB_NAME = "unity-v2"

# 表 E1 训练池的七族闭集（train 一族 + dev 六族）。
TRAIN_POOL_FAMILIES: tuple[str, ...] = (
    "p1-vlm-survey-a2-p1-c1-s1",
    "detect-scout1",
    "m3-armA",
    "p1-vlm-survey-a1-p1-c1-s2",
    "p1-vlm-survey-a7-p1-c1-s1",
    "rate",
    "scene-val",
)
TRAINING_FAMILIES: tuple[str, ...] = tuple(f for f in TRAIN_POOL_FAMILIES if f != SELECTION_FAMILY)
POOL_SPLITS: tuple[str, ...] = ("train", "dev")
EVAL_SPLIT = "test"
UNASSIGNED = "unassigned"

# AC-1 的对账常量（归档身份变化即视为输入变化，fail-closed）。
EXPECTED_S3_FRAMES = 43535
EXPECTED_S3_SHARDS = 151
EXPECTED_S4_FRAME_COUNTS: dict[str, int] = {"train": 2523, "dev": 13144, "test": 8450, "d3": 0}
EXPECTED_S5_OBJECTS = 690
EXPECTED_S5_CLASS_VERIFIED = 93
EXPECTED_S5_DUAL_VERIFIED = 37
EXPECTED_INSTRUCTION_ROWS = 57430

# --- 路径 -----------------------------------------------------------------

ARCHIVE_ROOT = Path("runtime/dist-data")
CONTRACT_JSON = ARCHIVE_ROOT / "contract/attempt-2/contract.json"
FRAMES_CATALOG_JSON = ARCHIVE_ROOT / "frames_catalog/attempt-2/frames_catalog.json"
FRAMES_CATALOG_SHARDS = ARCHIVE_ROOT / "frames_catalog/attempt-2/shards"
SPLITS_JSON = ARCHIVE_ROOT / "splits/attempt-2/splits.json"
SPLITS_SHARDS = ARCHIVE_ROOT / "splits/attempt-2/shards"
FIELD_CATALOG_JSON = ARCHIVE_ROOT / "field_catalog/attempt-2/field_catalog.json"
INVENTORY_JSON = ARCHIVE_ROOT / "inventory/attempt-2/inventory.json"
INSTRUCTIONS_NDJSON = Path("runtime/eng-asset/P1-ENG-ASSET-001/instructions.ndjson.gz")
INSTRUCTIONS_SUMMARY = Path("docs/evidence/P1-ENG-ASSET-001-instructions-summary.json")
DEFAULT_PROBE_ROOT = Path("/Volumes/T7/TDT-PROBE-DATA-2026-09-11-finish/probe")
PROBE_MANIFEST_RELATIVE = Path("manifest-default.json")
PROBE_PREDICTIONS_RELATIVE = Path("outputs/qwen3vl-2b-default-20260912/predictions.jsonl")

EVIDENCE_DIR = Path("docs/evidence")
DATASET_MANIFEST = EVIDENCE_DIR / f"{receipts.WORK_ID}-dataset-manifest.json"
EVAL_MANIFEST = EVIDENCE_DIR / f"{receipts.WORK_ID}-eval-manifest.json"
LEAKAGE_REPORT = EVIDENCE_DIR / f"{receipts.WORK_ID}-leakage-report.json"
LEGACY_CONSERVATION = EVIDENCE_DIR / f"{receipts.WORK_ID}-legacy-conservation.json"
FROZEN_JSON_FILES: tuple[Path, ...] = (
    DATASET_MANIFEST,
    EVAL_MANIFEST,
    LEAKAGE_REPORT,
    LEGACY_CONSERVATION,
)
FROZEN_SCRIPT_FILES: tuple[Path, ...] = (
    Path("tools/eng_sft/three_state.py"),
    Path("tools/eng_sft/prompt_v2.py"),
    Path("tools/eng_sft/parse.py"),
    Path("tools/eng_sft/evaluate.py"),
)

DATA_DIRNAME = "data"
UPLOAD_DIRNAME = "upload"
PANEL_DIRNAME = "panel"
LEGACY_DIRNAME = "legacy"
FREEZE_RECEIPT_NAME = "freeze-receipt.json"
PRECHECK_RECEIPT_NAME = "precheck-receipt.json"
PACKAGE_RECEIPT_NAME = "package-receipt.json"

TRAIN_JSONL = "train.jsonl"
SMOKE_JSONL = "smoke.jsonl"
SELECT_EVAL_JSONL = "select-eval.jsonl"
SELECT_EVAL_BLIND = "select-eval.blind.jsonl"
EVAL_JSONL = "eval.jsonl"
EVAL_BLIND = "eval.blind.jsonl"
# AC-5 修订 1：预检 gold 文件闭集。
GOLD_FILES: tuple[str, ...] = (TRAIN_JSONL, SMOKE_JSONL, SELECT_EVAL_JSONL, EVAL_JSONL)
# 表 J 的 J7 抽样域（被排除的 #27 bus 颜色指令；不进训练/评估，也不进数据包）。
AUDIT_J7_JSONL = "audit-j7-candidates.jsonl"
GOLD_TOKEN_MAX = 152

# AC-6 目录上限（字节）。
DATA_DIR_MAX_BYTES = 64 * 1024 * 1024
UPLOAD_DIR_MAX_BYTES = 300 * 1024 * 1024
PANEL_DIR_MAX_BYTES = 20 * 1024 * 1024
TOKENIZER_DIR_MAX_BYTES = 20 * 1024 * 1024
VERSIONED_FILE_MAX_BYTES = 2 * 1024 * 1024
PEAK_RSS_MAX_BYTES = 1024 * 1024 * 1024

# tokenizer 四文件（候选 1 信封唯一下载项；不下载权重）。
TOKENIZER_REPO = "Qwen/Qwen3-VL-2B-Instruct"
TOKENIZER_REVISION = "89644892e4d85e24eaac8bacfd4f463576704203"
TOKENIZER_FILES: tuple[str, ...] = (
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt",
)


# --- 小工具 ---------------------------------------------------------------


def _json_line(record: dict[str, Any]) -> str:
    """AC-5 修订 1 的落盘序列化：紧凑分隔符、纯 ASCII、行末一个 LF。"""
    return json.dumps(record, separators=(",", ":"), ensure_ascii=True) + "\n"


def _jsonl_bytes(rows: Sequence[dict[str, Any]]) -> bytes:
    """把若干行序列化成最终要落盘的字节（不写文件）。"""
    return "".join(_json_line(row) for row in rows).encode("utf-8")


def _json_bytes(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _record_for_bytes(path: Path, payload: bytes, lines: int | None = None) -> dict[str, Any]:
    """按「将要落盘的字节」预先给出交付记录，供先核验后发布（C1-1）。"""
    record: dict[str, Any] = {
        "path": receipts.relative_to_root(path),
        "bytes": len(payload),
        "sha256": _sha256_bytes(payload),
    }
    if lines is not None:
        record["lines"] = lines
    return record


def _write_bytes(path: Path, payload: bytes) -> None:
    receipts.assert_output_allowed(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _write_jsonl(path: Path, rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    receipts.assert_output_allowed(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        for row in rows:
            handle.write(_json_line(row))
    return receipts.output_record(path, lines=len(rows))


def _write_json(path: Path, document: dict[str, Any]) -> dict[str, Any]:
    receipts.assert_output_allowed(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipts.output_record(path)


def _load_payload(path: Path) -> dict[str, Any]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    return document.get("payload", document)


def _digest(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _line_stats(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"rows": 0, "total_bytes": 0, "line_max": None, "line_p50": None, "line_min": None}
    sizes = [len(_json_line(row).encode("utf-8")) for row in rows]
    return {
        "rows": len(rows),
        "total_bytes": sum(sizes),
        "line_max": max(sizes),
        "line_p50": int(statistics.median(sizes)),
        "line_min": min(sizes),
    }


def _dir_bytes(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            total += (Path(root) / name).stat().st_size
    return total


# --- 只读输入 -------------------------------------------------------------


@dataclass
class Archives:
    """§3 输入闭集的一次加载；每件的身份都登记进输入清单。"""

    repo_root: Path = PROJECT_ROOT
    probe_root: Path = DEFAULT_PROBE_ROOT
    manifest: receipts.InputManifest = field(default_factory=receipts.InputManifest)

    contract_payload: dict[str, Any] = field(default_factory=dict)
    frames_manifest: dict[str, Any] = field(default_factory=dict)
    splits: dict[str, Any] = field(default_factory=dict)
    field_catalog: dict[str, Any] = field(default_factory=dict)
    inventory_index: dict[str, tuple[str, int]] = field(default_factory=dict)
    instructions: dict[tuple[str, str], tuple[str, dict[str, Any] | None]] = field(
        default_factory=dict
    )
    instructions_summary: dict[str, Any] = field(default_factory=dict)
    legacy_rows: list[dict[str, Any]] = field(default_factory=list)
    legacy_sha256: str = ""
    legacy_predictions_sha256: str = ""
    split_by_frame: dict[str, str] = field(default_factory=dict)

    def load(self) -> "Archives":
        root = self.repo_root
        # 输入清单必须相对**本次执行的**仓库根记路径：默认工厂给的是 PROJECT_ROOT，
        # 夹具/复核 worktree 下会把路径记成绝对值，后续按相对键查绑定就查不到。
        self.manifest.repo_root = root
        self.contract_payload = _load_payload(root / CONTRACT_JSON)
        self.manifest.record(root / CONTRACT_JSON, source="S0 contract@attempt-2（现算）")

        self.frames_manifest = _load_payload(root / FRAMES_CATALOG_JSON)
        self.manifest.record(root / FRAMES_CATALOG_JSON, source="S3 manifest（现算）")

        self.splits = _load_payload(root / SPLITS_JSON)
        self.manifest.record(root / SPLITS_JSON, source="S4 splits（现算）")

        catalog = _load_payload(root / FIELD_CATALOG_JSON)
        self.field_catalog = catalog
        field_catalog_sha = receipts.sha256_file(root / FIELD_CATALOG_JSON)
        self.manifest.record(
            root / FIELD_CATALOG_JSON, source="S5 field_catalog（现算）", precomputed_sha256=field_catalog_sha
        )

        inventory = _load_payload(root / INVENTORY_JSON)
        self.manifest.record(root / INVENTORY_JSON, source="S1 inventory（现算）")
        self.inventory_index = {
            record["path"]: (record["sha256"], record["bytes"])
            for record in inventory["records"]
            if record.get("kind") != "truth"
        }
        del inventory

        instructions_sha = receipts.sha256_file(root / INSTRUCTIONS_NDJSON)
        self.manifest.record(
            root / INSTRUCTIONS_NDJSON,
            source="ASSET-001 指令逐行（现算）",
            precomputed_sha256=instructions_sha,
        )
        with gzip.open(root / INSTRUCTIONS_NDJSON, "rt") as handle:
            for line in handle:
                row = json.loads(line)
                self.instructions[(row["frame_id"], row["object_id"])] = (
                    row["uniqueness_status"],
                    row.get("program"),
                )

        self.instructions_summary = json.loads(
            (root / INSTRUCTIONS_SUMMARY).read_text(encoding="utf-8")
        )
        self.manifest.record(root / INSTRUCTIONS_SUMMARY, source="ASSET-001 指令摘要（受版本控制）")

        # 探针清单与预测（T7 只读；与摘要 `source` 的两个 SHA 相等是准入条件）。
        probe_manifest = Path(self.probe_root) / PROBE_MANIFEST_RELATIVE
        probe_predictions = Path(self.probe_root) / PROBE_PREDICTIONS_RELATIVE
        if not probe_manifest.is_file():
            raise receipts.LegacySourceMismatch(
                f"探针清单不可读（T7 未挂载？）：{probe_manifest}", offending=[str(probe_manifest)]
            )
        self.legacy_sha256 = receipts.sha256_file(probe_manifest)
        self.manifest.record(
            probe_manifest, source="探针清单（首次读取现算）", precomputed_sha256=self.legacy_sha256
        )
        probe = json.loads(probe_manifest.read_text(encoding="utf-8"))
        self.legacy_rows = probe["rows"]
        source = probe.get("source", {})
        if source.get("field_catalog_sha256") != field_catalog_sha:
            raise receipts.LegacySourceMismatch(
                "探针清单的 field_catalog SHA 与本次 S5 不符",
                offending=[{"probe": source.get("field_catalog_sha256"), "actual": field_catalog_sha}],
            )
        if source.get("instructions_sha256") != instructions_sha:
            raise receipts.LegacySourceMismatch(
                "探针清单的 instructions SHA 与本次指令逐行文件不符",
                offending=[{"probe": source.get("instructions_sha256"), "actual": instructions_sha}],
            )
        if probe_predictions.is_file():
            self.legacy_predictions_sha256 = receipts.sha256_file(probe_predictions)
            self.manifest.record(
                probe_predictions,
                source="探针预测（首次读取现算；v1 诊断附表来源）",
                precomputed_sha256=self.legacy_predictions_sha256,
            )

        self.split_by_frame = {
            frame_id: split
            for split, frames in self.splits["frames"].items()
            for frame_id in frames
        }
        return self

    def shard_paths(self) -> list[Path]:
        return sorted(
            Path(p) for p in glob.glob(str(self.repo_root / FRAMES_CATALOG_SHARDS / "*.ndjson.gz"))
        )

    def split_of(self, frame_id: str) -> str:
        return self.split_by_frame.get(frame_id, UNASSIGNED)


@dataclass(frozen=True)
class ReconcileExpectations:
    """AC-1 的对账期望值；默认是合同里的真实归档常量。

    具名回归在合成小世界上跑同一套对账代码，只替换这些期望值——判据与失败路径
    不另写一份。
    """

    s3_frames: int = EXPECTED_S3_FRAMES
    s3_shards: int = EXPECTED_S3_SHARDS
    s4_frame_counts: dict[str, int] = field(default_factory=lambda: dict(EXPECTED_S4_FRAME_COUNTS))
    s5_objects: int = EXPECTED_S5_OBJECTS
    s5_class_verified: int = EXPECTED_S5_CLASS_VERIFIED
    s5_dual_verified: int = EXPECTED_S5_DUAL_VERIFIED
    instruction_rows: int = EXPECTED_INSTRUCTION_ROWS


DEFAULT_EXPECTATIONS = ReconcileExpectations()


def reconcile(
    archives: Archives, expected: ReconcileExpectations = DEFAULT_EXPECTATIONS
) -> dict[str, Any]:
    """AC-1：逐件核对计数与分片 SHA；不符即 fail-closed（只写失败收据）。"""
    root = archives.repo_root
    manifest = archives.frames_manifest
    if manifest["frame_count"] != expected.s3_frames or len(manifest["shards"]) != expected.s3_shards:
        raise receipts.ManifestCountMismatch(
            "S3 帧数/分片数与合同不符",
            offending=[{"frames": manifest["frame_count"], "shards": len(manifest["shards"])}],
        )
    shard_lines = 0
    for shard in manifest["shards"]:
        path = root / ARCHIVE_ROOT / "frames_catalog/attempt-2" / shard["path"]
        actual_bytes = path.stat().st_size
        if actual_bytes != shard["compressed_bytes"]:
            raise receipts.ShardHashMismatch(
                f"S3 分片字节不符：{shard['path']}",
                offending=[{"path": shard["path"], "declared": shard["compressed_bytes"], "actual": actual_bytes}],
            )
        digest = receipts.sha256_file(path)
        if digest != shard["sha256"]:
            raise receipts.ShardHashMismatch(
                f"S3 分片 SHA 不符：{shard['path']}",
                offending=[{"path": shard["path"], "declared": shard["sha256"], "actual": digest}],
            )
        archives.manifest.record(
            path, source="S3 分片（manifest 声明值复核）", declared_sha256=shard["sha256"], precomputed_sha256=digest
        )
        shard_lines += shard["lines"]
    if shard_lines != expected.s3_frames:
        raise receipts.ManifestCountMismatch(
            "S3 分片行数之和与帧数不符", offending=[{"lines": shard_lines}]
        )

    counts = {key: len(value) for key, value in archives.splits["frames"].items()}
    if counts != expected.s4_frame_counts:
        raise receipts.ManifestCountMismatch("S4 划分帧数与合同不符", offending=[counts])
    # S4 自己声明 `leakage_assertions.pairwise_disjoint`；这里按字节核对该声明是否成立。
    # 一帧同时出现在两个 split 时，`split_by_frame` 只会留下最后一个赋值——那是 fail-open，
    # 必须在对账阶段就拒绝，而不是让它悄悄变成某一侧的成员。
    seen_frames: dict[str, str] = {}
    overlaps: list[dict[str, str]] = []
    for split, frames in archives.splits["frames"].items():
        for frame_id in frames:
            previous = seen_frames.get(frame_id)
            if previous is not None:
                overlaps.append({"frame_id": frame_id, "splits": f"{previous}+{split}"})
            else:
                seen_frames[frame_id] = split
    if overlaps:
        raise receipts.ManifestCountMismatch(
            "S4 划分不是两两不交（同一帧出现在多个 split）", offending=overlaps[:20]
        )
    for shard in archives.splits.get("shards", []):
        path = root / ARCHIVE_ROOT / "splits/attempt-2" / shard["path"]
        digest = receipts.sha256_file(path)
        if digest != shard["sha256"]:
            raise receipts.ShardHashMismatch(
                f"S4 分片 SHA 不符：{shard['path']}",
                offending=[{"path": shard["path"], "declared": shard["sha256"], "actual": digest}],
            )
        archives.manifest.record(
            path, source="S4 分片（只做 SHA 核对）", declared_sha256=shard["sha256"], precomputed_sha256=digest
        )

    objects = archives.field_catalog["objects"]
    class_verified = sum(1 for o in objects.values() if o.get("class_verified"))
    dual_verified = sum(
        1 for o in objects.values() if o.get("class_verified") and o.get("color_status") == "VERIFIED"
    )
    if (len(objects), class_verified, dual_verified) != (
        expected.s5_objects,
        expected.s5_class_verified,
        expected.s5_dual_verified,
    ):
        raise receipts.ManifestCountMismatch(
            "S5 目录计数与合同不符",
            offending=[{"objects": len(objects), "class_verified": class_verified, "dual_verified": dual_verified}],
        )
    # S0 的用途是「词表/关系闭集常量核对」：归档当初的常量必须等于本次执行真正用的常量，
    # 否则三态派生与 G4 关系执行的语义就和归档对不上（关注项 4）。
    payload = archives.contract_payload
    relations = payload.get("relations", {})
    contract_checks = {
        "class_words": (sorted(payload.get("class_words", [])), sorted(dist_contract.CLASS_WORDS)),
        "relation_types": (list(relations.get("types", [])), list(dist_contract.RELATION_TYPES)),
        "viewer_side_min_separation_px": (
            relations.get("viewer_side_min_separation_px"),
            dist_contract.VIEWER_SIDE_MIN_SEPARATION_PX,
        ),
        "nearest_to_dominance_ratio": (
            relations.get("nearest_to_dominance_ratio"),
            dist_contract.NEAREST_TO_DOMINANCE_RATIO,
        ),
        "dynamic_target_referable": (
            payload.get("dynamic_target", {}).get("referable"),
            dist_contract.DYNAMIC_TARGET_REFERABLE,
        ),
    }
    drifted = [
        {"item": name, "archive": archived, "runtime": runtime}
        for name, (archived, runtime) in contract_checks.items()
        if archived != runtime
    ]
    if drifted:
        raise receipts.InputHashChanged(
            "S0 合同常量与本次执行使用的常量不一致", offending=drifted
        )

    return {
        "s3": {"frames": manifest["frame_count"], "shards": len(manifest["shards"]), "shard_lines": shard_lines},
        "s0_constants_checked": sorted(contract_checks),
        "s3_declared_lines_by_shard": {
            shard["index"]: shard["lines"] for shard in manifest["shards"]
        },
        "s4": counts,
        "s5": {"objects": len(objects), "class_verified": class_verified, "dual_verified": dual_verified},
        "instructions_sha256": archives.manifest.entries[
            receipts.relative_to_root(root / INSTRUCTIONS_NDJSON, root)
        ].sha256,
        "field_catalog_sha256": archives.manifest.entries[
            receipts.relative_to_root(root / FIELD_CATALOG_JSON, root)
        ].sha256,
        "probe_manifest_sha256": archives.legacy_sha256,
        "probe_predictions_sha256": archives.legacy_predictions_sha256,
    }


def summary_histogram(summary: dict[str, Any]) -> dict[tuple[str, bool, str], int]:
    """把 ASSET-001 摘要的嵌套直方图摊平成 `(split, mother_usage, status) → 计数`。"""
    flat: dict[tuple[str, bool, str], int] = {}
    for split, usages in summary["uniqueness_status_histogram"].items():
        for usage, counts in usages.items():
            mother = usage == "mother_usage"
            for status, value in counts.items():
                flat[(split, mother, status)] = value
    return flat


# --- 扫描：三态样本 + AC-1 七值直方图（同一遍流式扫描）-------------------


@dataclass(slots=True)
class Sample:
    """一条 (帧, 名词) 的内部样本；落盘形态见 `sample_record` / `eval_record`。"""

    frame_id: str
    family: str
    frame_index: int
    split: str
    noun_type: str
    surface: str
    noun: dict[str, Any] | None
    program: dict[str, Any] | None
    class_word: str
    state: str
    target_ids: tuple[str, ...]
    boxes: tuple[tuple[float, ...], ...]
    px: float | None
    color_required: bool | None
    has_dynamic_target: bool
    legacy: tuple[dict[str, Any], ...] = ()


@dataclass
class ScanResult:
    samples: dict[str, list[Sample]]
    g4_rows: list[Sample]
    color_counterexample_rows: list[dict[str, Any]]
    station_key: dict[str, str]
    domain_ids: dict[str, tuple[str, ...]]
    frame_classes: dict[str, frozenset[str]]
    status_histogram: dict[tuple[str, bool, str], int]
    counters: Counter
    instruction_rows: int
    shard_lines: dict[str, int]


def stratum_of(px: float | None) -> str:
    """表 D′ 层：`< 32` S、`< 64` M、`≥ 64` L、无框 NA。"""
    if px is None:
        return "NA"
    if px < 32:
        return "S"
    if px < 64:
        return "M"
    return "L"


def thin_key(sample: Sample) -> str:
    """表 D′ 键：unique → 目标 `object_id`；ambiguous → 候选升序以 `|` 连接；其余 → surface。"""
    if sample.state == STATE_UNIQUE:
        return sample.target_ids[0]
    if sample.state == STATE_AMBIGUOUS:
        return "|".join(sample.target_ids)
    return sample.surface


def hash_of(sample: Sample) -> str:
    """表 D′ 哈希序 `h(s)`。"""
    return _digest(SEED, sample.frame_id, thin_key(sample))


def hash_order(sample: Sample) -> tuple[str, str, str, str, str]:
    """表 D′ 并列次序：`(h, frame_id, key, noun_type, surface)`。"""
    return (hash_of(sample), sample.frame_id, thin_key(sample), sample.noun_type, sample.surface)


def gap_of(sample: Sample) -> int:
    """表 D′ E2 稀疏间隔。"""
    if sample.state == STATE_AMBIGUOUS:
        return GAP_AMBIGUOUS
    if sample.state == STATE_NONE:
        return GAP_NONE
    if sample.class_word in WEAK_CLASSES or (sample.px is not None and sample.px < 32):
        return GAP_UNIQUE_WEAK_OR_SMALL
    return GAP_UNIQUE_OTHER


def thin(samples: Iterable[Sample]) -> list[Sample]:
    """E2 稀疏：按 `(族, 状态, noun_type, 键, 帧序号)` 升序遍历，保留间隔 ≥ gap 的行。"""
    kept: list[Sample] = []
    last: dict[tuple[str, str, str, str], int] = {}
    ordered = sorted(
        samples, key=lambda s: (s.family, s.state, s.noun_type, thin_key(s), s.frame_index)
    )
    for sample in ordered:
        key = (sample.family, sample.state, sample.noun_type, thin_key(sample))
        previous = last.get(key)
        if previous is None or sample.frame_index - previous >= gap_of(sample):
            last[key] = sample.frame_index
            kept.append(sample)
    return kept


def scan(archives: Archives) -> ScanResult:
    """一遍流式扫描：三态样本（assigned split）+ 七值直方图（全对账域）。"""
    classes = sorted(dist_contract.CLASS_WORDS)
    catalog = archives.field_catalog
    samples: dict[str, list[Sample]] = defaultdict(list)
    g4_rows: list[Sample] = []
    counterexample_rows: list[dict[str, Any]] = []
    station_key: dict[str, str] = {}
    domain_ids: dict[str, tuple[str, ...]] = {}
    frame_classes: dict[str, frozenset[str]] = {}
    histogram: dict[tuple[str, bool, str], int] = defaultdict(int)
    counters: Counter = Counter()
    instruction_rows = 0

    shard_lines: dict[str, int] = {}
    for shard in archives.shard_paths():
        seen_lines = 0
        with gzip.open(shard, "rt") as handle:
            for line in handle:
                seen_lines += 1
                entry = json.loads(line)
                if not unity_s3.is_usable_entry(entry):
                    counters["frames_skipped_unusable"] += 1
                    continue
                frame_id = entry["frame_id"]
                split = archives.split_of(frame_id)
                world = None

                # --- AC-1 七值直方图（对账域含 unassigned）---
                referable = list(entry["referable"])
                if referable:
                    world = build_catalog.frame_world(entry, catalog)
                    mother = entry["usage_class"] in dist_contract.MOTHER_USAGE_CLASSES
                    for object_id in referable:
                        instruction_rows += 1
                        status, _program, _ref = asset_inventory.classify_uniqueness(
                            world, object_id, catalog
                        )
                        histogram[(split, mother, status)] += 1

                counters["frames_in_domain"] += 1
                if split == UNASSIGNED:
                    counters["frames_unassigned"] += 1
                    continue

                record = unity_s3.adapt_frame(entry, catalog, world=world)
                station_key[frame_id] = record.station_key
                domain_ids[frame_id] = record.object_ids()
                # §8 表 8「混淆对暴露」用的逐帧类别集合（执行域内已知类别词）。
                frame_classes[frame_id] = frozenset(
                    obj.class_word for obj in record.objects if obj.class_word
                )
                if record.dynamic_target_present:
                    counters["frames_with_dynamic_target"] += 1
                if record.frame_wildcard:
                    counters[f"frame_wildcard_{record.wildcard_reason}"] += 1
                    counters["frames_wildcard"] += 1
                    continue

                objects = record.objects
                idx = record.frame_index
                family = entry["family"]

                for class_word in classes:
                    result = three_state(objects, {"class": class_word})
                    counters[(split, "class", result.state)] += 1
                    if result.state not in (
                        STATE_UNIQUE,
                        STATE_AMBIGUOUS,
                        STATE_NONE,
                        STATE_GRAY_DEFINITE_PLUS_UNCERTAIN,
                    ):
                        continue
                    ids = result.target_object_ids or result.definite_ids
                    boxes = tuple(
                        tuple(record.box_of(i)) for i in ids if record.box_of(i) is not None
                    )
                    px = min((unity_s3.short_side_px(b) for b in boxes), default=None)
                    samples[split].append(
                        Sample(
                            frame_id=frame_id,
                            family=family,
                            frame_index=idx,
                            split=split,
                            noun_type="class",
                            surface=f"the {class_word}",
                            noun={"class": class_word},
                            program=None,
                            class_word=class_word,
                            state=result.state,
                            target_ids=tuple(ids),
                            boxes=boxes,
                            px=px,
                            color_required=None,
                            has_dynamic_target=DYNAMIC_TARGET_ID in ids,
                        )
                    )

                seen_pairs: set[tuple[str, str]] = set()
                for obj in objects:
                    if obj.object_id == DYNAMIC_TARGET_ID:
                        pair = ("car", "red") if record.dynamic_target_definite else None
                    else:
                        stored = catalog["objects"].get(obj.object_id)
                        pair = (
                            (stored["class"], stored["color"])
                            if stored
                            and obj.referable
                            and stored.get("color_status") == "VERIFIED"
                            and stored.get("color")
                            else None
                        )
                    if pair is None or pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)
                    if pair[0] in record.excluded_color_classes:
                        counters[(split, "color", "excluded_color_counterexample")] += 1
                        # 表 J 的 J7 抽样域：被排除的 bus 颜色指令连同该 bus 的框
                        # 与 S5 颜色字段留作显示证据，**不进训练/评估**。
                        counterexample_rows.append(
                            {
                                "frame_id": frame_id,
                                "family": family,
                                "frame_index": idx,
                                "split": split,
                                "station_key": record.station_key,
                                "excluded_surface": f"the {pair[1]} {pair[0]}",
                                "excluded_class": pair[0],
                                "object_id": obj.object_id,
                                "s5_color": pair[1],
                                "box_norm_xywh": list(record.box_of(obj.object_id) or []),
                                "counterexample_object_ids": [
                                    other.object_id
                                    for other in objects
                                    if other.object_id.split(" (", 1)[0]
                                    == unity_s3.COLOR_COUNTEREXAMPLE_OBJECT
                                ],
                            }
                        )
                        continue
                    noun = {"class": pair[0], "color": pair[1]}
                    result = three_state(objects, noun)
                    class_result = three_state(objects, {"class": pair[0]})
                    color_required = not (
                        result.state == STATE_UNIQUE and class_result.state == STATE_UNIQUE
                    )
                    label = result.state if color_required else "unique_no_color_needed"
                    counters[(split, "color", label)] += 1
                    if result.state not in (STATE_UNIQUE, STATE_AMBIGUOUS):
                        continue
                    ids = result.target_object_ids
                    boxes = tuple(
                        tuple(record.box_of(i)) for i in ids if record.box_of(i) is not None
                    )
                    px = min((unity_s3.short_side_px(b) for b in boxes), default=None)
                    samples[split].append(
                        Sample(
                            frame_id=frame_id,
                            family=family,
                            frame_index=idx,
                            split=split,
                            noun_type="color",
                            surface=f"the {pair[1]} {pair[0]}",
                            noun=noun,
                            program=None,
                            class_word=pair[0],
                            state=result.state,
                            target_ids=tuple(ids),
                            boxes=boxes,
                            px=px,
                            color_required=color_required,
                            has_dynamic_target=DYNAMIC_TARGET_ID in ids,
                        )
                    )

                if split != EVAL_SPLIT:
                    continue
                # G4：旧 `UNIQUE_RELATION` 行在本帧执行域上 `execute` 唯一且命中目标。
                for object_id in referable:
                    stored = archives.instructions.get((frame_id, object_id))
                    if not stored or stored[0] != "UNIQUE_RELATION":
                        continue
                    program = stored[1]
                    result = tier1_lang.execute(program, objects)
                    if not tier1_lang.hits_expected_target(result, object_id):
                        continue
                    box = record.box_of(object_id)
                    boxes = (tuple(box),) if box else ()
                    g4_rows.append(
                        Sample(
                            frame_id=frame_id,
                            family=family,
                            frame_index=idx,
                            split=split,
                            noun_type="relation",
                            surface=tier1_lang.render(program),
                            noun=None,
                            program=program,
                            class_word=program["target"]["class"],
                            state=STATE_UNIQUE,
                            target_ids=(object_id,),
                            boxes=boxes,
                            px=unity_s3.short_side_px(box) if box else None,
                            color_required=None,
                            has_dynamic_target=False,
                        )
                    )
        shard_lines[shard.stem.split(".")[0]] = seen_lines

    return ScanResult(
        samples=dict(samples),
        g4_rows=g4_rows,
        color_counterexample_rows=counterexample_rows,
        station_key=station_key,
        domain_ids=domain_ids,
        frame_classes=frame_classes,
        status_histogram=dict(histogram),
        counters=counters,
        instruction_rows=instruction_rows,
        shard_lines=shard_lines,
    )


# --- 表 E：训练集与选层集 -------------------------------------------------


@dataclass
class TrainingSets:
    unique_kept: list[Sample]
    ambiguous_kept: list[Sample]
    none_kept: list[Sample]
    copies: int
    n_none_target: int
    select_eval: list[Sample]
    smoke: list[Sample]
    seen_object_ids: frozenset[str]
    train_frames: frozenset[str]
    select_frames: frozenset[str]
    steps: dict[str, Any]


def confusion_exposure(
    samples: Sequence[Sample], frame_classes: dict[str, frozenset[str]]
) -> dict[str, dict[str, int]]:
    """§8 表 8 的「混淆对暴露」：目标类为 a 的样本里，帧内同时出现类别 b 的样本数。"""
    matrix: dict[str, Counter] = defaultdict(Counter)
    for sample in samples:
        present = frame_classes.get(sample.frame_id, frozenset())
        for other in present:
            if other != sample.class_word:
                matrix[sample.class_word][other] += 1
    return {a: dict(sorted(counts.items())) for a, counts in sorted(matrix.items())}


def build_training_sets(scan_result: ScanResult) -> TrainingSets:
    """E1…E9（确定顺序；每一步的实取写进 manifest）。"""
    pool = [
        sample
        for split in POOL_SPLITS
        for sample in scan_result.samples.get(split, [])
        if sample.state in (STATE_UNIQUE, STATE_AMBIGUOUS, STATE_NONE)
    ]
    pre_thin_by_family = Counter(sample.family for sample in pool)
    train_pool = thin([s for s in pool if s.family != SELECTION_FAMILY])
    select_pool = thin([s for s in pool if s.family == SELECTION_FAMILY])

    uniques = [s for s in train_pool if s.state == STATE_UNIQUE]
    ambiguous = [s for s in train_pool if s.state == STATE_AMBIGUOUS]
    nones = [s for s in train_pool if s.state == STATE_NONE]

    # E3：unique 配额（class + color 合计），同一对象在类内 ≤ 350。
    unique_kept: list[Sample] = []
    per_class: Counter = Counter()
    per_object: Counter = Counter()
    for sample in sorted(uniques, key=hash_order):
        target = sample.target_ids[0]
        if per_class[sample.class_word] >= CLASS_QUOTA:
            continue
        if per_object[(sample.class_word, target)] >= OBJECT_QUOTA:
            continue
        per_class[sample.class_word] += 1
        per_object[(sample.class_word, target)] += 1
        unique_kept.append(sample)

    # E4：ambiguous 每候选集键 ≤ 60。
    ambiguous_kept: list[Sample] = []
    per_key: Counter = Counter()
    for sample in sorted(ambiguous, key=hash_order):
        key = thin_key(sample)
        if per_key[key] >= AMBIGUOUS_KEY_QUOTA:
            continue
        per_key[key] += 1
        ambiguous_kept.append(sample)

    # E5：none 按类别名字典序固定顺序逐类轮转。
    classes = sorted(dist_contract.CLASS_WORDS)
    n_none = int(NONE_SHARE * (len(unique_kept) + len(ambiguous_kept)) / (1.0 - NONE_SHARE))
    per_class_cap = -(-n_none // len(classes))
    queues = {
        class_word: iter(sorted([s for s in nones if s.class_word == class_word], key=hash_order))
        for class_word in classes
    }
    taken: Counter = Counter()
    none_kept: list[Sample] = []
    active = set(classes)
    while len(none_kept) < n_none and active:
        for class_word in classes:
            if class_word not in active or len(none_kept) >= n_none:
                continue
            if taken[class_word] >= per_class_cap:
                active.discard(class_word)
                continue
            try:
                sample = next(queues[class_word])
            except StopIteration:
                active.discard(class_word)
                continue
            taken[class_word] += 1
            none_kept.append(sample)

    # E6：复制系数。
    copies = 1
    while (
        len(ambiguous_kept) * copies
        < AMBIGUOUS_SHARE * (len(unique_kept) + len(none_kept) + len(ambiguous_kept) * copies)
        and copies < COPY_MAX
    ):
        copies += 1

    train_frames = frozenset(s.frame_id for s in unique_kept + ambiguous_kept + none_kept)
    seen = frozenset(
        object_id for frame_id in train_frames for object_id in scan_result.domain_ids[frame_id]
    )

    # E8：选层评估子集。
    select_unique = [s for s in select_pool if s.state == STATE_UNIQUE]
    select_ambiguous = [s for s in select_pool if s.state == STATE_AMBIGUOUS]
    select_none = [s for s in select_pool if s.state == STATE_NONE]
    select_eval = (
        select_ambiguous
        + sorted(select_unique, key=hash_order)[: min(SELECT_UNIQUE_CAP, len(select_unique))]
        + sorted(select_none, key=hash_order)[:SELECT_NONE_CAP]
    )
    select_frames = frozenset(s.frame_id for s in select_eval)

    # 表 H 冒烟 32 条：按表 D′ 哈希序取自训练 distinct 样本。
    smoke: list[Sample] = []
    for state, noun_type, count in SMOKE_QUOTA:
        if state == STATE_UNIQUE:
            candidates = [s for s in unique_kept if s.noun_type == noun_type]
        elif state == STATE_AMBIGUOUS:
            candidates = list(ambiguous_kept)
        else:
            candidates = list(none_kept)
        smoke.extend(sorted(candidates, key=hash_order)[:count])

    total = len(unique_kept) + len(none_kept) + len(ambiguous_kept) * copies
    steps = {
        "E1": {
            "train_pool_families": list(TRAIN_POOL_FAMILIES),
            "training_families": list(TRAINING_FAMILIES),
            "selection_family": SELECTION_FAMILY,
            "pre_thin_samples_by_family": dict(sorted(pre_thin_by_family.items())),
            "selection_thinned": {
                "unique": len(select_unique),
                "ambiguous": len(select_ambiguous),
                "none": len(select_none),
            },
        },
        "E2": {
            "thinned": {
                "unique": len(uniques),
                "ambiguous": len(ambiguous),
                "none": len(nones),
            },
            "thinned_by_family": {
                family: {
                    "unique": sum(
                        1 for s in train_pool if s.family == family and s.state == STATE_UNIQUE
                    ),
                    "ambiguous": sum(
                        1 for s in train_pool if s.family == family and s.state == STATE_AMBIGUOUS
                    ),
                    "none": sum(
                        1 for s in train_pool if s.family == family and s.state == STATE_NONE
                    ),
                }
                for family in TRAINING_FAMILIES
            },
            "gaps": {
                "ambiguous": GAP_AMBIGUOUS,
                "none": GAP_NONE,
                "unique_weak_or_small": GAP_UNIQUE_WEAK_OR_SMALL,
                "unique_other": GAP_UNIQUE_OTHER,
            },
        },
        "E3": {
            "kept": len(unique_kept),
            "class_quota": CLASS_QUOTA,
            "object_quota": OBJECT_QUOTA,
            "per_class": dict(sorted(per_class.items())),
            "dynamic_target_unique": sum(1 for s in unique_kept if s.has_dynamic_target),
        },
        "E4": {
            "kept": len(ambiguous_kept),
            "key_quota": AMBIGUOUS_KEY_QUOTA,
            "per_class": dict(sorted(Counter(s.class_word for s in ambiguous_kept).items())),
            "dynamic_target_ambiguous": sum(1 for s in ambiguous_kept if s.has_dynamic_target),
        },
        "E5": {
            "n_none_target": n_none,
            "kept": len(none_kept),
            "per_class_cap": per_class_cap,
            "per_class": dict(sorted(taken.items())),
        },
        "E6": {"copies": copies, "share": round(len(ambiguous_kept) * copies / total, 4)},
        "E7": {
            "multiset_samples": total,
            "distinct_samples": len(unique_kept) + len(ambiguous_kept) + len(none_kept),
            "frames": len(train_frames),
        },
        "E8": {"rows": len(select_eval), "frames": len(select_frames)},
        "E9": {"seen_objects": len(seen)},
        "strata_unique": dict(sorted(Counter(stratum_of(s.px) for s in unique_kept).items())),
        "confusion_exposure_unique_kept": confusion_exposure(unique_kept, scan_result.frame_classes),
    }
    return TrainingSets(
        unique_kept=unique_kept,
        ambiguous_kept=ambiguous_kept,
        none_kept=none_kept,
        copies=copies,
        n_none_target=n_none,
        select_eval=select_eval,
        smoke=smoke,
        seen_object_ids=seen,
        train_frames=train_frames,
        select_frames=select_frames,
        steps=steps,
    )


# --- 表 D：冻结评估集（legacy 优先 → 层轮转）-----------------------------


@dataclass
class EvalSets:
    picked: dict[str, list[Sample]]
    legacy_only: list[tuple[str, Sample]]
    conservation: dict[str, dict[str, Any]]
    eval_frames: frozenset[str]
    group_counts: dict[str, int]


class _Admitter:
    """表 D′ 准入：同键 ≤ 4 行、与已准入行帧序号间隔 ≥ 30；G5 另加每类 ≤ 12。"""

    def __init__(self, group: str) -> None:
        self.group = group
        self.indices: dict[tuple[str, str, str], list[int]] = defaultdict(list)
        self.counts: Counter = Counter()
        self.per_class: Counter = Counter()

    def admit(self, sample: Sample) -> bool:
        key = (
            self.group,
            sample.surface if sample.state == STATE_NONE else thin_key(sample),
            sample.family,
        )
        if self.counts[key] >= ADMIT_KEY_MAX:
            return False
        if any(abs(sample.frame_index - i) < ADMIT_MIN_INDEX_GAP for i in self.indices[key]):
            return False
        if self.group == "G5" and self.per_class[sample.class_word] >= G5_CLASS_MAX:
            return False
        self.indices[key].append(sample.frame_index)
        self.counts[key] += 1
        self.per_class[sample.class_word] += 1
        return True


def build_eval_sets(scan_result: ScanResult, archives: Archives) -> EvalSets:
    """表 D：十组冻结评估集，legacy 行按新状态先行纳入并逐 row_id 守恒。"""
    test = scan_result.samples.get(EVAL_SPLIT, [])
    groups: dict[str, list[Sample]] = {
        "G1": [s for s in test if s.noun_type == "class" and s.state == STATE_UNIQUE and not s.has_dynamic_target],
        "G1t": [s for s in test if s.noun_type == "class" and s.state == STATE_UNIQUE and s.has_dynamic_target],
        "G2": [
            s
            for s in test
            if s.noun_type == "color"
            and s.state == STATE_UNIQUE
            and s.color_required
            and not s.has_dynamic_target
        ],
        "G2t": [s for s in test if s.noun_type == "color" and s.state == STATE_UNIQUE and s.has_dynamic_target],
        "G3": [s for s in test if s.noun_type == "class" and s.state == STATE_AMBIGUOUS and not s.has_dynamic_target],
        "G3t": [s for s in test if s.noun_type == "class" and s.state == STATE_AMBIGUOUS and s.has_dynamic_target],
        "G3p": [s for s in test if s.noun_type == "class" and s.state == STATE_GRAY_DEFINITE_PLUS_UNCERTAIN],
        "G4": list(scan_result.g4_rows),
        "G5": [s for s in test if s.noun_type == "class" and s.state == STATE_NONE],
    }

    legacy_by: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in archives.legacy_rows:
        legacy_by[(row["frame_path"], row["surface"])].append(row)

    picked: dict[str, list[Sample]] = {}
    legacy_only: list[tuple[str, Sample]] = []
    conservation: dict[str, dict[str, Any]] = {}

    for group in GROUP_ORDER:
        items = groups[group]
        for sample in items:
            sample.legacy = tuple(legacy_by.get((sample.frame_id, sample.surface), ()))
        forced = [s for s in items if s.legacy]
        rest = [s for s in items if not s.legacy]
        admitter = _Admitter(group)
        chosen: list[Sample] = []

        # legacy 优先内次序：按该样本 legacy `row_id` 集合的最小值字符串升序。
        for sample in sorted(forced, key=lambda s: min(row["row_id"] for row in s.legacy)):
            admitted = admitter.admit(sample)
            if admitted:
                chosen.append(sample)
            else:
                legacy_only.append((group, sample))
            for row in sample.legacy:
                conservation[row["row_id"]] = {
                    "disposition": "ADMITTED" if admitted else LEGACY_ONLY_GROUP,
                    "group": group,
                    "sample": sample,
                }

        strata: dict[str, list[Sample]] = {name: [] for name in STRATA_ORDER}
        for sample in rest:
            strata[stratum_of(sample.px)].append(sample)
        for bucket in strata.values():
            bucket.sort(key=hash_order)
        order = [name for name in STRATA_ORDER if strata[name]]
        iterators = {name: iter(strata[name]) for name in order}
        active = set(order)
        quota = EVAL_QUOTA.get(group)
        while (quota is None or len(chosen) < quota) and active:
            for name in list(order):
                if name not in active:
                    continue
                try:
                    sample = next(iterators[name])
                except StopIteration:
                    active.discard(name)
                    continue
                if admitter.admit(sample):
                    chosen.append(sample)
                if quota is not None and len(chosen) >= quota:
                    break
        picked[group] = chosen

    for group in REQUIRED_NONEMPTY_GROUPS:
        if not picked[group]:
            raise receipts.EvalGroupEmpty(f"评估组为空：{group}", offending=[group])

    unmapped = {row["row_id"] for row in archives.legacy_rows} - set(conservation)
    if unmapped:
        raise receipts.ConservationMismatch(
            f"legacy 行未映射：{len(unmapped)} 条", offending=sorted(unmapped)[:20]
        )
    if len(conservation) != len(archives.legacy_rows):
        raise receipts.ConservationMismatch(
            "守恒表条数与探针清单行数不符",
            offending=[{"conservation": len(conservation), "legacy": len(archives.legacy_rows)}],
        )

    eval_frames = frozenset(
        [s.frame_id for rows in picked.values() for s in rows]
        + [s.frame_id for _group, s in legacy_only]
    )
    counts = {group: len(rows) for group, rows in picked.items()}
    counts[LEGACY_ONLY_GROUP] = len(legacy_only)
    return EvalSets(
        picked=picked,
        legacy_only=legacy_only,
        conservation=conservation,
        eval_frames=eval_frames,
        group_counts=counts,
    )


# --- 表 C：落盘 schema ----------------------------------------------------


def sample_id(sample: Sample) -> str:
    return "s-" + _digest(SEED, sample.frame_id, sample.surface)[:16]


def eval_row_id(group: str, sample: Sample) -> str:
    return f"{group}-" + _digest(SEED, sample.frame_id, sample.surface)[:16]


def frame_path_of(archives: Archives, frame_id: str) -> str:
    """包内路径 `frames/<sha256>.jpg`，`build` 时写定（SHA 取 S1 记录）。"""
    record = archives.inventory_index.get(frame_id)
    if record is None:
        raise receipts.InputHashChanged(
            f"S1 记录缺该帧：{frame_id}", offending=[{"frame_id": frame_id}]
        )
    return f"frames/{record[0]}.jpg"


def sample_record(
    sample: Sample, *, archives: Archives, scan_result: ScanResult, copies: int
) -> dict[str, Any]:
    boxes = [list(box) for box in sample.boxes]
    record = {
        "sample_id": sample_id(sample),
        "frame_id": sample.frame_id,
        "frame_path": frame_path_of(archives, sample.frame_id),
        "frame_sha256": archives.inventory_index[sample.frame_id][0],
        "split": sample.split,
        "family": sample.family,
        "station_key": scan_result.station_key[sample.frame_id],
        "frame_index": sample.frame_index,
        "noun_type": sample.noun_type,
        "surface": sample.surface,
        "noun": sample.noun,
        "state": sample.state,
        "color_required": sample.color_required,
        "target_object_ids": list(sample.target_ids),
        "target_boxes_norm_xywh": boxes,
        "target_bbox_2d_1000": prompt_v2.sorted_bboxes(boxes),
        "stratum": stratum_of(sample.px),
        "thin_key": thin_key(sample),
        "has_dynamic_target": sample.has_dynamic_target,
        "oversample_copies": copies,
    }
    return record


def eval_record(
    group: str,
    sample: Sample,
    *,
    archives: Archives,
    scan_result: ScanResult,
    seen: frozenset[str],
) -> dict[str, Any]:
    """表 C `eval-row`。

    灰区（G3p）与 LEGACY_ONLY 的 `gold_state` 为 null（AC-3 修订 1：不编造三态
    gold），两组仍保留 `definite_ids` 与 `legacy_probe`；`diagnostic` 先记灰区
    原因，其次才是去重排除——group 列已经写明该行属 LEGACY_ONLY。
    """
    gray = sample.state == STATE_GRAY_DEFINITE_PLUS_UNCERTAIN
    gold_state = None if gray else sample.state
    if gray:
        diagnostic = "GRAY_DEFINITE_PLUS_UNCERTAIN"
    elif group == LEGACY_ONLY_GROUP:
        diagnostic = "LEGACY_ONLY_DEDUPE_EXCLUDED"
    else:
        diagnostic = None
    boxes = [list(box) for box in sample.boxes]
    has_gold = gold_state in (STATE_UNIQUE, STATE_AMBIGUOUS)
    gold_text = prompt_v2.gold_text_from_state(gold_state, boxes)
    record: dict[str, Any] = {
        "row_id": eval_row_id(group, sample),
        "frame_id": sample.frame_id,
        "frame_path": frame_path_of(archives, sample.frame_id),
        "frame_sha256": archives.inventory_index[sample.frame_id][0],
        "family": sample.family,
        "frame_index": sample.frame_index,
        "station_key": scan_result.station_key[sample.frame_id],
        "group": group,
        "gate_row": group in GATE_GROUPS,
        "surface": sample.surface,
    }
    if sample.noun_type == "relation":
        record["relation_program"] = sample.program
    else:
        record["noun"] = sample.noun
    record.update(
        {
            "gold_state": gold_state,
            "diagnostic": diagnostic,
            "definite_ids": list(sample.target_ids),
            "target_object_ids": list(sample.target_ids) if has_gold else [],
            "gold_boxes_norm_xywh": boxes if has_gold else [],
            "gold_bbox_2d_1000": prompt_v2.sorted_bboxes(boxes) if has_gold else [],
            "stratum": stratum_of(sample.px),
            "gold_text_len": len(gold_text) if gold_text else None,
            "has_dynamic_target": sample.has_dynamic_target,
            "color_required": sample.color_required,
            "seen_target": all(i in seen for i in sample.target_ids) if sample.target_ids else None,
            "seen_candidates": [i in seen for i in sample.target_ids],
            "seen_all": all(i in seen for i in scan_result.domain_ids[sample.frame_id]),
            "legacy_probe": [
                {
                    "row_id": row["row_id"],
                    "group_v1": row["group"],
                    "object_id_v1": row["object_id"],
                    "gold_v1_xywh": row["gold_xywh_norm"],
                    "same_class_visible_v1": row.get("same_class_visible"),
                }
                for row in sample.legacy
            ],
        }
    )
    return record


def blind_record(row: dict[str, Any]) -> dict[str, Any]:
    """盲行：`row_id, frame_path, surface, g4, vocab`——无任何 gold 字段。"""
    return {
        "row_id": row["row_id"],
        "frame_path": row["frame_path"],
        "surface": row["surface"],
        "g4": row.get("group") == "G4",
        "vocab": VOCAB_NAME,
    }


def select_blind_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row["sample_id"],
        "frame_path": row["frame_path"],
        "surface": row["surface"],
        "g4": False,
        "vocab": VOCAB_NAME,
    }


def conservation_records(
    eval_sets: EvalSets, archives: Archives
) -> list[dict[str, Any]]:
    """`legacy-conservation`：405 条，逐 legacy `row_id` 记原 group/gold 与去向。"""
    group_v1 = {row["row_id"]: row["group"] for row in archives.legacy_rows}
    rows: list[dict[str, Any]] = []
    for row_id, entry in conservation_sorted(eval_sets.conservation):
        sample: Sample = entry["sample"]
        group = entry["group"]
        disposition = entry["disposition"]
        target_group = group if disposition == "ADMITTED" else LEGACY_ONLY_GROUP
        rows.append(
            {
                "row_id": row_id,
                "group_v1": group_v1[row_id],
                "frame_path": sample.frame_id,
                "surface": sample.surface,
                "new_state": sample.state,
                "eval_row_id": eval_row_id(target_group, sample),
                "group": group,
                "disposition": disposition,
            }
        )
    return rows


def conservation_sorted(conservation: dict[str, dict[str, Any]]):
    return sorted(conservation.items(), key=lambda item: item[0])


def bind_frames(archives: Archives, frames: Iterable[str]) -> dict[str, Any]:
    """逐张 SHA 绑定到 S1 记录；任一缺失或不符即 `INPUT_HASH_CHANGED`。"""
    bound = 0
    total_bytes = 0
    problems: list[dict[str, Any]] = []
    for frame_id in sorted(frames):
        record = archives.inventory_index.get(frame_id)
        path = archives.repo_root / frame_id
        if record is None or not path.is_file():
            problems.append({"frame_id": frame_id, "problem": "MISSING"})
            continue
        size = path.stat().st_size
        digest = receipts.sha256_file(path)
        total_bytes += size
        if size != record[1] or digest != record[0]:
            problems.append(
                {"frame_id": frame_id, "declared": record[0], "actual": digest}
            )
            continue
        bound += 1
    if problems:
        raise receipts.InputHashChanged(
            f"帧 SHA 绑定失败：{len(problems)} 张", offending=problems[:20]
        )
    return {"frames": bound, "bytes": total_bytes}


# --- build 阶段 -----------------------------------------------------------


def compare_histogram(
    actual: dict[tuple[str, bool, str], int], expected: dict[tuple[str, bool, str], int]
) -> list[dict[str, Any]]:
    """七值直方图逐值比较（缺键按 0）；返回不符条目。"""
    problems: list[dict[str, Any]] = []
    for key in sorted(set(actual) | set(expected)):
        left, right = actual.get(key, 0), expected.get(key, 0)
        if left != right:
            split, mother, status = key
            problems.append(
                {
                    "split": split,
                    "mother_usage": mother,
                    "status": status,
                    "recomputed": left,
                    "summary": right,
                }
            )
    return problems


def gold_length_stats(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    lengths = [row["gold_text_len"] for row in rows if row.get("gold_text_len")]
    skeletons = Counter(row["gold_state"] for row in rows)
    return {
        "rows": len(rows),
        "with_gold": len(lengths),
        "gold_chars_max": max(lengths) if lengths else None,
        "gold_chars_p50": int(statistics.median(lengths)) if lengths else None,
        "skeletons": dict(sorted((str(k), v) for k, v in skeletons.items())),
    }


def run_build(
    *,
    repo_root: Path = PROJECT_ROOT,
    probe_root: Path = DEFAULT_PROBE_ROOT,
    local_root: Path | None = None,
    expected: ReconcileExpectations = DEFAULT_EXPECTATIONS,
) -> dict[str, Any]:
    """`build`：对账 → 扫描 → 训练/选层/评估集 → jsonl/盲文件/四份冻结 JSON。"""
    started = time.monotonic()
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    archives = Archives(repo_root=root, probe_root=Path(probe_root))
    try:
        archives.load()
        reconciliation = reconcile(archives, expected)
        scan_result = scan(archives)
        if scan_result.instruction_rows != expected.instruction_rows:
            raise receipts.ManifestCountMismatch(
                "对账域指令行数与合同不符",
                offending=[{"rows": scan_result.instruction_rows, "expected": expected.instruction_rows}],
            )
        # 关注项 4：分片行数不能只信 manifest 自报——扫描时逐片实数，逐片比对。
        declared_lines = reconciliation["s3_declared_lines_by_shard"]
        line_drift = [
            {"shard": index, "declared": declared, "scanned": scan_result.shard_lines.get(index)}
            for index, declared in sorted(declared_lines.items())
            if scan_result.shard_lines.get(index) != declared
        ]
        if line_drift:
            raise receipts.ManifestCountMismatch(
                "S3 分片实数行数与 manifest 自报不符", offending=line_drift[:20]
            )

        problems = compare_histogram(
            scan_result.status_histogram, summary_histogram(archives.instructions_summary)
        )
        if problems:
            raise receipts.HistogramMismatch(
                "七值直方图与 ASSET-001 摘要不符", offending=problems[:20]
            )

        training = build_training_sets(scan_result)
        eval_sets = build_eval_sets(scan_result, archives)
        seen = training.seen_object_ids

        data_dir = local / DATA_DIRNAME
        train_rows = [
            sample_record(s, archives=archives, scan_result=scan_result, copies=1)
            for s in training.unique_kept + training.none_kept
        ] + [
            sample_record(s, archives=archives, scan_result=scan_result, copies=training.copies)
            for s in training.ambiguous_kept
        ]
        smoke_rows = [
            sample_record(s, archives=archives, scan_result=scan_result, copies=1)
            for s in training.smoke
        ]
        select_rows = [
            sample_record(s, archives=archives, scan_result=scan_result, copies=1)
            for s in training.select_eval
        ]
        eval_rows: list[dict[str, Any]] = []
        for group in GROUP_ORDER:
            for sample in eval_sets.picked[group]:
                eval_rows.append(
                    eval_record(group, sample, archives=archives, scan_result=scan_result, seen=seen)
                )
        for _group, sample in eval_sets.legacy_only:
            eval_rows.append(
                eval_record(
                    LEGACY_ONLY_GROUP, sample, archives=archives, scan_result=scan_result, seen=seen
                )
            )
        row_ids = [row["row_id"] for row in eval_rows]
        if len(set(row_ids)) != len(row_ids):
            raise receipts.ConservationMismatch(
                "评估行 row_id 重复", offending=[r for r, c in Counter(row_ids).items() if c > 1][:20]
            )

        select_blind = [select_blind_record(row) for row in select_rows]
        eval_blind = [blind_record(row) for row in eval_rows]
        conservation = conservation_records(eval_sets, archives)
        if len(conservation) != len(archives.legacy_rows):
            raise receipts.ConservationMismatch(
                "守恒表条数不等于 405", offending=[{"rows": len(conservation)}]
            )

        # C1-1：先按「将要落盘的字节」算出交付记录，**所有核验通过后才发布**。
        planned: list[tuple[Path, bytes]] = []
        outputs: list[dict[str, Any]] = []
        for name, rows in (
            (AUDIT_J7_JSONL, scan_result.color_counterexample_rows),
            (TRAIN_JSONL, train_rows),
            (SMOKE_JSONL, smoke_rows),
            (SELECT_EVAL_JSONL, select_rows),
            (SELECT_EVAL_BLIND, select_blind),
            (EVAL_JSONL, eval_rows),
            (EVAL_BLIND, eval_blind),
        ):
            payload = _jsonl_bytes(rows)
            path = data_dir / name
            receipts.assert_output_allowed(path, root)
            planned.append((path, payload))
            outputs.append(_record_for_bytes(path, payload, lines=len(rows)))

        # legacy/：探针清单与预测的本地副本（来源 SHA 已在输入清单登记）。
        legacy_dir = data_dir / LEGACY_DIRNAME
        for relative in (PROBE_MANIFEST_RELATIVE, PROBE_PREDICTIONS_RELATIVE):
            source = Path(archives.probe_root) / relative
            if source.is_file():
                destination = receipts.assert_output_allowed(legacy_dir / source.name, root)
                payload = source.read_bytes()
                planned.append((destination, payload))
                outputs.append(_record_for_bytes(destination, payload))

        union_frames = training.train_frames | training.select_frames | eval_sets.eval_frames
        binding = {
            "train": bind_frames(archives, training.train_frames),
            "select_eval": bind_frames(archives, training.select_frames),
            "eval": bind_frames(archives, eval_sets.eval_frames),
            "union": bind_frames(archives, union_frames),
        }

        # 泄漏断言（AC-3）。
        train_select_frames = training.train_frames | training.select_frames
        train_select_sha = {archives.inventory_index[f][0] for f in train_select_frames}
        eval_sha = {archives.inventory_index[f][0] for f in eval_sets.eval_frames}
        held_out_frames = {
            frame
            for frame, split in archives.split_by_frame.items()
            if split == EVAL_SPLIT
        } | {
            frame
            for frame in scan_result.domain_ids
            if archives.split_of(frame) == UNASSIGNED
        }
        leaked_eval = sorted(train_select_sha & eval_sha)
        leaked_split = sorted(train_select_frames & held_out_frames)
        if leaked_eval or leaked_split:
            raise receipts.ConservationMismatch(
                "泄漏断言失败：训练/选层与评估或留出集合相交",
                offending=(leaked_eval[:10] + leaked_split[:10]),
            )
        leakage = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/leakage-report/v1",
            "work_id": receipts.WORK_ID,
            "train_or_select_frames": len(train_select_frames),
            "eval_frames": len(eval_sets.eval_frames),
            "train_select_cap_eval_frame_sha256": leaked_eval,
            "train_select_cap_test_or_unassigned_frames": leaked_split,
            "assertions": {
                "train_select_disjoint_from_eval_by_sha": True,
                "train_select_disjoint_from_test_and_unassigned": True,
            },
            "seen": {
                "definition": "E9：对象出现在优化器实际见过的帧的执行域中",
                "objects": len(seen),
                "object_ids": sorted(seen),
            },
            "eval_rows_seen_target": Counter(str(row["seen_target"]) for row in eval_rows),
        }
        leakage["eval_rows_seen_target"] = dict(sorted(leakage["eval_rows_seen_target"].items()))

        state_counts = Counter(row["state"] for row in train_rows)
        dataset_manifest = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/dataset-manifest/v1",
            "work_id": receipts.WORK_ID,
            "seed": SEED,
            "vocab": VOCAB_NAME,
            "reconciliation": reconciliation,
            "scan_counters": {
                str(key): value for key, value in sorted(scan_result.counters.items(), key=str)
            },
            "steps": training.steps,
            "training": {
                "distinct_rows": len(train_rows),
                "multiset_samples": training.steps["E7"]["multiset_samples"],
                "state_counts": dict(sorted(state_counts.items())),
                "class_counts": dict(
                    sorted(Counter(row["noun"]["class"] for row in train_rows).items())
                ),
                "noun_type_counts": dict(
                    sorted(Counter(row["noun_type"] for row in train_rows).items())
                ),
                "stratum_counts": dict(sorted(Counter(row["stratum"] for row in train_rows).items())),
                "frames": len(training.train_frames),
            },
            "smoke": {
                "rows": len(smoke_rows),
                "composition": dict(
                    sorted(
                        Counter(f"{row['state']}/{row['noun_type']}" for row in smoke_rows).items()
                    )
                ),
            },
            "select_eval": {
                "rows": len(select_rows),
                "frames": len(training.select_frames),
                "state_counts": dict(sorted(Counter(row["state"] for row in select_rows).items())),
            },
            "files": {
                Path(record["path"]).name: {
                    "lines": record.get("lines"),
                    "bytes": record["bytes"],
                    "sha256": record["sha256"],
                }
                for record in outputs
                if record["path"].endswith(".jsonl")
            },
            "serialisation": {
                TRAIN_JSONL: _line_stats(train_rows),
                SMOKE_JSONL: _line_stats(smoke_rows),
                SELECT_EVAL_JSONL: _line_stats(select_rows),
                SELECT_EVAL_BLIND: _line_stats(select_blind),
            },
            "frame_binding": binding,
            "constants": {
                "class_quota": CLASS_QUOTA,
                "object_quota": OBJECT_QUOTA,
                "ambiguous_key_quota": AMBIGUOUS_KEY_QUOTA,
                "none_share": NONE_SHARE,
                "ambiguous_share": AMBIGUOUS_SHARE,
                "copy_max": COPY_MAX,
                "select_unique_cap": SELECT_UNIQUE_CAP,
                "select_none_cap": SELECT_NONE_CAP,
                "gold_token_max": GOLD_TOKEN_MAX,
                "prompt_template_sha256": prompt_v2.template_sha256(),
                "vocab_sha256": prompt_v2.vocab_sha256(VOCAB_NAME),
                "g4_segment_sha256": prompt_v2.g4_segment_sha256(),
            },
        }

        eval_manifest = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/eval-manifest/v1",
            "work_id": receipts.WORK_ID,
            "seed": SEED,
            "vocab": VOCAB_NAME,
            "rows": len(eval_rows),
            "gate_rows": sum(1 for row in eval_rows if row["gate_row"]),
            "group_counts": {
                group: sum(1 for row in eval_rows if row["group"] == group)
                for group in GROUP_ORDER + (LEGACY_ONLY_GROUP,)
            },
            "group_legacy_rows": {
                group: sum(len(row["legacy_probe"]) for row in eval_rows if row["group"] == group)
                for group in GROUP_ORDER + (LEGACY_ONLY_GROUP,)
            },
            "group_strata": {
                group: dict(
                    sorted(Counter(row["stratum"] for row in eval_rows if row["group"] == group).items())
                )
                for group in GROUP_ORDER + (LEGACY_ONLY_GROUP,)
            },
            "gold_lengths": {
                group: gold_length_stats([row for row in eval_rows if row["group"] == group])
                for group in GROUP_ORDER + (LEGACY_ONLY_GROUP,)
            },
            "serialisation": {EVAL_JSONL: _line_stats(eval_rows), EVAL_BLIND: _line_stats(eval_blind)},
            "frames": {"count": len(eval_sets.eval_frames), "binding": binding["eval"]},
            "union_frames": {"count": len(union_frames), "binding": binding["union"]},
            "files": {
                Path(record["path"]).name: {
                    "lines": record.get("lines"),
                    "bytes": record["bytes"],
                    "sha256": record["sha256"],
                }
                for record in outputs
                if Path(record["path"]).name in (EVAL_JSONL, EVAL_BLIND)
            },
            "legacy_probe_entries": sum(len(row["legacy_probe"]) for row in eval_rows),
            "legacy_manifest_sha256": archives.legacy_sha256,
        }

        conservation_document = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/legacy-conservation/v1",
            "work_id": receipts.WORK_ID,
            "legacy_manifest_sha256": archives.legacy_sha256,
            "rows": conservation,
            "totals": {
                "rows": len(conservation),
                "by_disposition": dict(
                    sorted(Counter(row["disposition"] for row in conservation).items())
                ),
                "admitted_by_group": dict(
                    sorted(
                        Counter(
                            row["group"] for row in conservation if row["disposition"] == "ADMITTED"
                        ).items()
                    )
                ),
                "legacy_only_by_group": dict(
                    sorted(
                        Counter(
                            row["group"]
                            for row in conservation
                            if row["disposition"] == LEGACY_ONLY_GROUP
                        ).items()
                    )
                ),
            },
        }

        for document, path in (
            (dataset_manifest, root / DATASET_MANIFEST),
            (eval_manifest, root / EVAL_MANIFEST),
            (leakage, root / LEAKAGE_REPORT),
            (conservation_document, root / LEGACY_CONSERVATION),
        ):
            payload = _json_bytes(document)
            receipts.assert_output_allowed(path, root)
            planned.append((path, payload))
            outputs.append(_record_for_bytes(path, payload))

        for record in outputs:
            if record["path"].startswith("docs/evidence/") and record["bytes"] > VERSIONED_FILE_MAX_BYTES:
                raise receipts.EngSftError(
                    f"受版本控制工件超过 2 MB：{record['path']}", offending=[record]
                )

        # 发布前最后一道：输入清单重算必须与登记值逐条相等（此前任何一步失败都还没落盘）。
        after = archives.manifest.recompute()
        mismatches = archives.manifest.diff(after)
        if mismatches:
            raise receipts.InputHashChanged(
                "发布前输入重算与登记值不符，不发布本次工件", offending=mismatches[:20]
            )

        # C1-1 / C2-1 发布阶段：先备份将被覆盖的旧字节，任一步失败（含写入期 OSError）即把
        # 新建文件删掉、被覆盖文件按原字节还原，不留下半新半旧、可被误当成功候选的产物。
        created: list[Path] = []
        replaced: dict[Path, bytes] = {}
        try:
            for path, payload in planned:
                if path.is_file():
                    replaced[path] = path.read_bytes()
                else:
                    created.append(path)
                _write_bytes(path, payload)
            for record, (path, payload) in zip(outputs, planned):
                actual = receipts.sha256_file(path)
                if actual != record["sha256"]:
                    raise receipts.InputHashChanged(
                        f"落盘字节与预算不符：{record['path']}",
                        offending=[{"path": record["path"], "planned": record["sha256"], "actual": actual}],
                    )
        except BaseException:
            for path in created:
                path.unlink(missing_ok=True)
            for path, original in replaced.items():
                path.write_bytes(original)
            raise

        writer.save_input_manifest("build", archives.manifest, after, mismatches, successful=True)
        receipt = writer.write_run_receipt(
            "build",
            started=started,
            outputs=outputs,
            extra={
                "data_dir_bytes": _dir_bytes(local / DATA_DIRNAME),
                "eval_rows": len(eval_rows),
                "train_rows": len(train_rows),
                "conservation_rows": len(conservation),
                "frame_binding": binding,
            },
        )
        return {
            "receipt": str(receipt),
            "dataset_manifest": dataset_manifest,
            "eval_manifest": eval_manifest,
            "leakage": leakage,
            "conservation": conservation_document,
            "outputs": outputs,
        }
    except receipts.EngSftError as exc:
        writer.write_failure_receipt("build", exc.reason, exc.offending, message=str(exc))
        after = archives.manifest.recompute() if archives.manifest.entries else {}
        writer.save_input_manifest(
            "build", archives.manifest, after, archives.manifest.diff(after), successful=False
        )
        raise
    except Exception:
        # 失败原因闭集（合同 §3）没有 I/O 类 token，造一个就越了闭集；这里只保证
        # **零残留**（发布段已回滚）并把异常原样抛出，不写不实的失败原因。
        after = archives.manifest.recompute() if archives.manifest.entries else {}
        writer.save_input_manifest(
            "build", archives.manifest, after, archives.manifest.diff(after), successful=False
        )
        raise


# --- precheck 阶段（表 H 本地 tokenizer 预检）-----------------------------


def tokenizer_dir(repo_root: Path = PROJECT_ROOT, revision: str = TOKENIZER_REVISION) -> Path:
    return Path(repo_root) / receipts.TOKENIZER_ROOT / revision


def _load_tokenizer(directory: Path):
    """同版 tokenizer 文件 → 计数器。

    优先 `transformers.AutoTokenizer`（与云端一致）；缺依赖时退回 `tokenizers`
    的 `Tokenizer.from_file`，两者对同一 `tokenizer.json` 的 BPE 切分相同。
    实际使用的库与版本写进预检收据，不含糊。
    """
    missing = [name for name in TOKENIZER_FILES if not (directory / name).is_file()]
    if missing:
        raise receipts.TokenizerMismatch(
            f"tokenizer 四文件不齐：{missing}（目录 {directory}）", offending=missing
        )
    try:
        from transformers import AutoTokenizer  # noqa: PLC0415

        import transformers  # noqa: PLC0415

        tokenizer = AutoTokenizer.from_pretrained(str(directory))

        def encode(text: str) -> int:
            return len(tokenizer(text, add_special_tokens=False)["input_ids"])

        return encode, {"library": "transformers", "version": transformers.__version__}
    except ImportError:
        from tokenizers import Tokenizer  # noqa: PLC0415

        import tokenizers  # noqa: PLC0415

        tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))

        def encode(text: str) -> int:
            return len(tokenizer.encode(text, add_special_tokens=False).ids)

        return encode, {"library": "tokenizers", "version": tokenizers.__version__}


def _gold_texts(path: Path) -> list[str]:
    texts: list[str] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            text = prompt_v2.gold_text(row)
            if text is not None:
                texts.append(text)
    return texts


def run_precheck(
    *,
    repo_root: Path = PROJECT_ROOT,
    local_root: Path | None = None,
    tokenizer_path: Path | None = None,
) -> dict[str, Any]:
    """`precheck`：用同版 tokenizer 对四份 gold 文件逐条实测并写绑定收据（表 H）。"""
    started = time.monotonic()
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    directory = Path(tokenizer_path) if tokenizer_path is not None else tokenizer_dir(root)
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    manifest = receipts.InputManifest(repo_root=root)
    data_dir = local / DATA_DIRNAME
    try:
        encode, library = _load_tokenizer(directory)
        tokenizer_files = {}
        for name in TOKENIZER_FILES:
            path = directory / name
            entry = manifest.record(path, source=f"tokenizer 文件（{TOKENIZER_REPO}@{TOKENIZER_REVISION}）")
            tokenizer_files[name] = {"bytes": entry.bytes, "sha256": entry.sha256}

        per_file: dict[str, Any] = {}
        overflow: list[dict[str, Any]] = []
        for name in GOLD_FILES:
            path = data_dir / name
            if not path.is_file():
                raise receipts.FrozenSetMismatch(
                    f"预检所需 gold 文件缺失：{name}（先跑 build）", offending=[name]
                )
            entry = manifest.record(path, source="本项 gold 文件（build 产出）")
            counts = [encode(text) for text in _gold_texts(path)]
            with open(path, encoding="utf-8") as handle:
                total_rows = sum(1 for _ in handle)
            rows_without_gold = total_rows - len(counts)
            per_file[name] = {
                "sha256": entry.sha256,
                "bytes": entry.bytes,
                "gold_rows": len(counts),
                "rows_without_gold": rows_without_gold,
                "token_max": max(counts) if counts else None,
                "token_p50": int(statistics.median(counts)) if counts else None,
                "token_total": sum(counts),
            }
            if counts and max(counts) > GOLD_TOKEN_MAX:
                overflow.append({"file": name, "max": max(counts), "threshold": GOLD_TOKEN_MAX})
        if overflow:
            raise receipts.GoldTokenOverflow(
                "gold token 超过拒绝阈值（不截断、不扩预算）", offending=overflow
            )

        template_overhead = {
            "assistant_header": encode("<|im_start|>assistant\n"),
            "im_end": encode("<|im_end|>"),
        }
        document = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/precheck-receipt/v1",
            "work_id": receipts.WORK_ID,
            "utc": receipts.utc_stamp(),
            "tokenizer": {
                "repo": TOKENIZER_REPO,
                "revision": TOKENIZER_REVISION,
                "directory": receipts.relative_to_root(directory, root),
                "files": tokenizer_files,
                **library,
            },
            "counting": {"add_special_tokens": False, "chat_template_applied": False},
            "gold_function": {
                "module": "tools/eng_sft/prompt_v2.py",
                "function": "gold_text",
                "source_sha256": prompt_v2.gold_function_source_sha256(),
            },
            "gold_files": per_file,
            "token_max_threshold": GOLD_TOKEN_MAX,
            "observed_token_max": max(
                (value["token_max"] for value in per_file.values() if value["token_max"]), default=None
            ),
            "template_overhead_tokens": template_overhead,
        }
        # C2-1：先做末次输入重算，确认这次读过的字节没变，再写成功专用收据。
        after = manifest.recompute()
        mismatches = manifest.diff(after)
        if mismatches:
            raise receipts.InputHashChanged(
                "预检期间输入发生变化，不写预检收据", offending=mismatches[:20]
            )
        receipt_path = writer._write_json(writer.receipts_dir / PRECHECK_RECEIPT_NAME, document)
        writer.save_input_manifest("precheck", manifest, after, mismatches, successful=True)
        writer.write_run_receipt(
            "precheck",
            started=started,
            outputs=[receipts.output_record(receipt_path)],
            extra={"observed_token_max": document["observed_token_max"]},
        )
        return document
    except receipts.EngSftError as exc:
        writer.write_failure_receipt("precheck", exc.reason, exc.offending, message=str(exc))
        after = manifest.recompute() if manifest.entries else {}
        writer.save_input_manifest(
            "precheck", manifest, after, manifest.diff(after), successful=False
        )
        raise


# --- freeze 阶段 ----------------------------------------------------------


def _git(args: Sequence[str], repo_root: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=str(repo_root), capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise receipts.FrozenFileDirty(
            f"git {' '.join(args)} 失败：{result.stderr.strip()}", offending=list(args)
        )
    return result.stdout


def frozen_set_state(repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """冻结闭集（四份 JSON + 四份脚本）的跟踪/干净状态与 SHA。"""
    state: dict[str, Any] = {}
    for path in FROZEN_JSON_FILES + FROZEN_SCRIPT_FILES:
        absolute = Path(repo_root) / path
        rel = path.as_posix()
        if not absolute.is_file():
            raise receipts.FrozenFileDirty(f"冻结闭集文件缺失：{rel}", offending=[rel])
        tracked = _git(["ls-files", "--", rel], repo_root).strip() != ""
        status = _git(["status", "--porcelain", "--", rel], repo_root).strip()
        if not tracked or status:
            raise receipts.FrozenFileDirty(
                f"冻结闭集文件未跟踪或不干净：{rel}（status={status or 'UNTRACKED'}）",
                offending=[{"path": rel, "tracked": tracked, "status": status}],
            )
        blob = _git(["rev-parse", f"HEAD:{rel}"], repo_root).strip()
        state[rel] = {"sha256": receipts.sha256_file(absolute), "git_blob": blob}
    return state


def run_freeze(
    *, repo_root: Path = PROJECT_ROOT, local_root: Path | None = None
) -> dict[str, Any]:
    """`freeze`：提交后生成冻结收据；前提 = 抽查判定齐全 + 无未裁定「错」+ 预检收据在。"""
    started = time.monotonic()
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    manifest = receipts.InputManifest(repo_root=root)
    try:
        from tools.eng_sft import label_audit  # noqa: PLC0415 - 避免与抽样模块循环导入

        audit_state = label_audit.audit_gate_state(repo_root=root, local_root=local)
        if audit_state["reason"] == "AUDIT_INCOMPLETE":
            raise receipts.AuditIncomplete(audit_state["message"], offending=audit_state["offending"])
        if audit_state["reason"] == "AUDIT_FINDING_OPEN":
            raise receipts.AuditFindingOpen(
                audit_state["message"], offending=audit_state["offending"]
            )

        precheck_path = writer.receipts_dir / PRECHECK_RECEIPT_NAME
        if not precheck_path.is_file():
            raise receipts.FrozenSetMismatch(
                "缺 tokenizer 预检收据，不得冻结", offending=[PRECHECK_RECEIPT_NAME]
            )
        precheck = json.loads(precheck_path.read_text(encoding="utf-8"))
        data_dir = local / DATA_DIRNAME
        # C1-4：先核成员闭集——只遍历收据自报的键，删掉一条绑定就等于不再检查那个文件。
        missing_members = []
        if set(precheck.get("gold_files", {})) != set(GOLD_FILES):
            missing_members.append(
                {
                    "item": "gold_files",
                    "receipt": sorted(precheck.get("gold_files", {})),
                    "contract": list(GOLD_FILES),
                }
            )
        if set(precheck.get("tokenizer", {}).get("files", {})) != set(TOKENIZER_FILES):
            missing_members.append(
                {
                    "item": "tokenizer.files",
                    "receipt": sorted(precheck.get("tokenizer", {}).get("files", {})),
                    "contract": list(TOKENIZER_FILES),
                }
            )
        if missing_members:
            raise receipts.FrozenSetMismatch(
                "预检收据的绑定成员与合同闭集不符（AC-5 修订 1 的四份 gold / 表 H 的四个 tokenizer 文件）",
                offending=missing_members,
            )
        stale: list[dict[str, Any]] = []
        for name, recorded in precheck["gold_files"].items():
            path = data_dir / name
            if not path.is_file():  # 缺文件按合同记收据，不抛原生异常
                stale.append({"file": name, "problem": "GOLD_FILE_MISSING"})
                continue
            current = receipts.sha256_file(path)
            if current != recorded["sha256"]:
                stale.append({"file": name, "receipt": recorded["sha256"], "actual": current})
        if precheck["gold_function"]["source_sha256"] != prompt_v2.gold_function_source_sha256():
            stale.append({"file": "tools/eng_sft/prompt_v2.py", "problem": "GOLD_FUNCTION_CHANGED"})
        for name, recorded in precheck["tokenizer"]["files"].items():
            path = Path(root) / precheck["tokenizer"]["directory"] / name
            if not path.is_file() or receipts.sha256_file(path) != recorded["sha256"]:
                stale.append({"file": name, "problem": "TOKENIZER_CHANGED"})
        if stale:
            raise receipts.InputHashChanged("预检收据已过期（绑定输入已变）", offending=stale)

        frozen = frozen_set_state(root)
        head = _git(["rev-parse", "HEAD"], root).strip()
        jsonl_state = {}
        for name in (
            TRAIN_JSONL,
            SMOKE_JSONL,
            SELECT_EVAL_JSONL,
            SELECT_EVAL_BLIND,
            EVAL_JSONL,
            EVAL_BLIND,
        ):
            path = data_dir / name
            if not path.is_file():
                raise receipts.FrozenSetMismatch(f"待冻结的 jsonl 缺失：{name}", offending=[name])
            entry = manifest.record(path, source="build 产出（冻结对象）")
            jsonl_state[name] = {"bytes": entry.bytes, "sha256": entry.sha256}
        # 关注项 2：本地这一份不是「现算就算数」——六份 jsonl 的 SHA 必须等于已提交的两份
        # manifest 里记录的值，否则冻结的就不是被核对过的那批字节。
        recorded_files: dict[str, dict[str, Any]] = {}
        for path in (root / DATASET_MANIFEST, root / EVAL_MANIFEST):
            document = json.loads(path.read_text(encoding="utf-8"))
            recorded_files.update(document.get("files", {}))
        drifted = []
        for name, state in jsonl_state.items():
            recorded = recorded_files.get(name)
            if recorded is None:
                drifted.append({"file": name, "problem": "NOT_IN_COMMITTED_MANIFEST"})
            elif recorded["sha256"] != state["sha256"]:
                drifted.append(
                    {"file": name, "manifest": recorded["sha256"], "actual": state["sha256"]}
                )
        if drifted:
            raise receipts.FrozenSetMismatch(
                "六份 jsonl 与已提交 manifest 记录的 SHA 不符", offending=drifted
            )
        manifest.record(precheck_path, source="本地预检收据")

        document = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/freeze-receipt/v1",
            "work_id": receipts.WORK_ID,
            "utc": receipts.utc_stamp(),
            "head": head,
            "frozen_set": frozen,
            "jsonl": jsonl_state,
            "precheck_receipt_sha256": receipts.sha256_file(precheck_path),
            "audit": audit_state["summary"],
        }
        after = manifest.recompute()
        mismatches = manifest.diff(after)
        if mismatches:
            raise receipts.InputHashChanged(
                "冻结期间被冻结的字节发生变化，不写冻结收据", offending=mismatches[:20]
            )
        receipt_path = writer._write_json(writer.receipts_dir / FREEZE_RECEIPT_NAME, document)
        writer.save_input_manifest("freeze", manifest, after, mismatches, successful=True)
        writer.write_run_receipt(
            "freeze", started=started, outputs=[receipts.output_record(receipt_path)], extra={"head": head}
        )
        return document
    except receipts.EngSftError as exc:
        writer.write_failure_receipt("freeze", exc.reason, exc.offending, message=str(exc))
        raise


# --- package 阶段（表 K 的 K4 数据包）------------------------------------

# 数据包成员（相对包根 `upload/`）：帧 + data + manifests；**不含代码**、不含
# gold 评估文件、不含 legacy/ 与泄漏报告。
PACKAGE_DATA_FILES: tuple[str, ...] = (TRAIN_JSONL, SMOKE_JSONL, SELECT_EVAL_BLIND, EVAL_BLIND)
PACKAGE_FORBIDDEN_NAMES: frozenset[str] = frozenset(
    {SELECT_EVAL_JSONL, EVAL_JSONL, "legacy-conservation.json", "leakage-report.json"}
)


def run_package(
    *, repo_root: Path = PROJECT_ROOT, local_root: Path | None = None
) -> dict[str, Any]:
    """`package`：冻结收据存在后复制帧与数据，写 `upload/manifest.json`。

    只复制字节，**不改写任何 jsonl**（jsonl 字节 = 冻结收据）；帧运输映射
    `frames/<sha>.jpg → 源 frame_id` 与两份 manifest/收据副本 SHA 一并记录。
    """
    started = time.monotonic()
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    manifest = receipts.InputManifest(repo_root=root)
    data_dir = local / DATA_DIRNAME
    upload_dir = local / UPLOAD_DIRNAME
    try:
        freeze_path = writer.receipts_dir / FREEZE_RECEIPT_NAME
        if not freeze_path.is_file():
            raise receipts.PackageIncomplete(
                "缺冻结收据，`package` 不得运行", offending=[FREEZE_RECEIPT_NAME]
            )
        freeze_document = json.loads(freeze_path.read_text(encoding="utf-8"))

        # C1-5：先守写出边界，再动目录——否则 `local_root` 指向禁写根时会先删后拒。
        receipts.assert_output_allowed(upload_dir, root)
        receipts.assert_output_allowed(upload_dir / "manifest.json", root)
        for sub in ("frames", "data", "manifests"):
            receipts.assert_output_allowed(upload_dir / sub, root)

        # C2-1：先把四份 data 成员与冻结收据逐份核对，**再**动已有的包；不合就地失败，
        # 旧包一个字节不改。
        for name in PACKAGE_DATA_FILES:
            source = data_dir / name
            if not source.is_file():
                raise receipts.PackageIncomplete(f"待打包的 jsonl 缺失：{name}", offending=[name])
            frozen_sha = freeze_document["jsonl"].get(name, {}).get("sha256")
            actual = receipts.sha256_file(source)
            if actual != frozen_sha:
                raise receipts.PackageIncomplete(
                    f"jsonl 字节与冻结收据不符：{name}",
                    offending=[{"file": name, "freeze": frozen_sha, "actual": actual}],
                )

        # 新包先建在暂存目录里，全部成员就位后再原子替换旧包：中途失败时旧包仍完整。
        staging = upload_dir.parent / f"{upload_dir.name}.staging"
        receipts.assert_output_allowed(staging, root)
        if staging.exists():
            shutil.rmtree(staging)
        build_dir = staging
        (build_dir / "frames").mkdir(parents=True, exist_ok=True)
        (build_dir / "data").mkdir(parents=True, exist_ok=True)
        (build_dir / "manifests").mkdir(parents=True, exist_ok=True)

        members: dict[str, dict[str, Any]] = {}
        transport: dict[str, list[str]] = {}

        # (a) 帧 JPEG：训练 ∪ 选层 ∪ 评估（含 LEGACY_ONLY 行帧）并集，复制而非符号链接。
        # 包内文件名是帧字节的 SHA-256，**字节相同的帧会合并成同一个文件**（本次实测
        # 3,968 个 frame_id → 2,327 个文件）。运输映射因此是 `包内路径 → 源 frame_id 列表`，
        # 每个源帧都逐个列出，不让重复帧在清单里消失。
        frame_paths: dict[str, set[str]] = defaultdict(set)
        for name in (TRAIN_JSONL, SELECT_EVAL_JSONL, EVAL_JSONL):
            with open(data_dir / name, encoding="utf-8") as handle:
                for line in handle:
                    row = json.loads(line)
                    frame_paths[row["frame_path"]].add(row["frame_id"])
        for package_path, frame_ids in sorted(frame_paths.items()):
            frame_id = sorted(frame_ids)[0]
            source = root / frame_id
            entry = manifest.record(source, source="帧 JPEG（打包复制）")
            expected_sha = Path(package_path).stem
            if entry.sha256 != expected_sha:
                raise receipts.PackageIncomplete(
                    f"帧字节与包内路径不符：{frame_id}",
                    offending=[{"frame_id": frame_id, "expected": expected_sha, "actual": entry.sha256}],
                )
            destination = build_dir / package_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            members[package_path] = {"bytes": entry.bytes, "sha256": entry.sha256}
            transport[package_path] = sorted(frame_ids)

        # (b)(c)(d) data/：训练标签 + 冒烟 + 两份盲文件（gold 评估文件不进包）。
        for name in PACKAGE_DATA_FILES:
            source = data_dir / name
            entry = manifest.record(source, source="build 产出（冻结 jsonl）")
            frozen_sha = freeze_document["jsonl"][name]["sha256"]
            if entry.sha256 != frozen_sha:
                raise receipts.PackageIncomplete(
                    f"jsonl 字节与冻结收据不符：{name}",
                    offending=[{"file": name, "freeze": frozen_sha, "actual": entry.sha256}],
                )
            destination = build_dir / "data" / name
            shutil.copy2(source, destination)
            members[f"data/{name}"] = {"bytes": entry.bytes, "sha256": entry.sha256}

        # (e) manifests/：两份 manifest（无 gold）+ 冻结收据 + 预检收据副本。
        copies: tuple[tuple[str, Path], ...] = (
            ("dataset-manifest.json", root / DATASET_MANIFEST),
            ("eval-manifest.json", root / EVAL_MANIFEST),
            (FREEZE_RECEIPT_NAME, freeze_path),
            (PRECHECK_RECEIPT_NAME, writer.receipts_dir / PRECHECK_RECEIPT_NAME),
        )
        for name, source in copies:
            entry = manifest.record(source, source="清单/收据副本")
            shutil.copy2(source, build_dir / "manifests" / name)
            members[f"manifests/{name}"] = {"bytes": entry.bytes, "sha256": entry.sha256}

        for name in PACKAGE_FORBIDDEN_NAMES:
            if (build_dir / "data" / name).exists() or (build_dir / "manifests" / name).exists():
                raise receipts.PackageIncomplete(
                    f"数据包含禁入成员：{name}", offending=[name]
                )

        upload_manifest = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/upload-manifest/v1",
            "work_id": receipts.WORK_ID,
            "stop_point": "K4",
            "package_root": receipts.relative_to_root(upload_dir, root),
            "members": dict(sorted(members.items())),
            "member_count": len(members),
            "total_bytes": sum(value["bytes"] for value in members.values()),
            "frame_transport_map": dict(sorted(transport.items())),
            "frame_files": len(transport),
            "source_frame_ids": sum(len(ids) for ids in transport.values()),
            "freeze_receipt_sha256": receipts.sha256_file(freeze_path),
            "precheck_receipt_sha256": receipts.sha256_file(
                writer.receipts_dir / PRECHECK_RECEIPT_NAME
            ),
            "contains_code": False,
        }
        manifest_path = build_dir / "manifest.json"
        receipts.assert_output_allowed(manifest_path, root)
        manifest_path.write_text(
            json.dumps(upload_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        # C2-1：先做末次输入重算（打包期间读过的帧与 data 成员），再替换旧包、再写收据。
        after = manifest.recompute()
        mismatches = manifest.diff(after)
        if mismatches:
            raise receipts.InputHashChanged(
                "打包期间输入发生变化，不替换已有数据包", offending=mismatches[:20]
            )

        # 全部成员就位且输入未变，才用新包替换旧包。
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
        staging.rename(upload_dir)
        manifest_path = upload_dir / "manifest.json"
        upload_bytes = _dir_bytes(upload_dir)
        if upload_bytes > UPLOAD_DIR_MAX_BYTES:
            raise receipts.PackageIncomplete(
                f"`upload/` 超过 0.3 GB：{upload_bytes}", offending=[{"bytes": upload_bytes}]
            )

        document = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/package-receipt/v1",
            "work_id": receipts.WORK_ID,
            "utc": receipts.utc_stamp(),
            "upload_manifest_sha256": receipts.sha256_file(manifest_path),
            "member_count": len(members),
            "upload_bytes": upload_bytes,
            "freeze_receipt_sha256": upload_manifest["freeze_receipt_sha256"],
        }
        receipt_path = writer._write_json(writer.receipts_dir / PACKAGE_RECEIPT_NAME, document)
        writer.save_input_manifest("package", manifest, after, mismatches, successful=True)
        writer.write_run_receipt(
            "package",
            started=started,
            outputs=[receipts.output_record(manifest_path), receipts.output_record(receipt_path)],
            extra={"upload_bytes": upload_bytes, "members": len(members)},
        )
        return document
    except receipts.EngSftError as exc:
        staging = upload_dir.parent / f"{upload_dir.name}.staging"
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        writer.write_failure_receipt("package", exc.reason, exc.offending, message=str(exc))
        raise
    except Exception:
        staging = upload_dir.parent / f"{upload_dir.name}.staging"
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise


def directory_caps(repo_root: Path = PROJECT_ROOT, local_root: Path | None = None) -> dict[str, Any]:
    """AC-6：分目录上限核对（`data/` / `upload/` / `panel/` / `tokenizer/`）。"""
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    checks = {
        "data": (local / DATA_DIRNAME, DATA_DIR_MAX_BYTES),
        "upload": (local / UPLOAD_DIRNAME, UPLOAD_DIR_MAX_BYTES),
        "panel": (local / PANEL_DIRNAME, PANEL_DIR_MAX_BYTES),
        "tokenizer": (root / receipts.TOKENIZER_ROOT, TOKENIZER_DIR_MAX_BYTES),
    }
    report: dict[str, Any] = {}
    for name, (path, cap) in checks.items():
        used = _dir_bytes(path) if path.exists() else 0
        report[name] = {"bytes": used, "cap_bytes": cap, "within_cap": used <= cap}
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-SFT-002 K4 数据合同构建器")
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--local-root", default=None)
    subparsers = parser.add_subparsers(dest="stage", required=True)

    build_parser = subparsers.add_parser("build", help="对账 + 三态 + 数据集 + 冻结 JSON")
    build_parser.add_argument("--probe-root", default=str(DEFAULT_PROBE_ROOT))

    precheck_parser = subparsers.add_parser("precheck", help="本地 tokenizer gold 预检")
    precheck_parser.add_argument("--tokenizer-dir", default=None)

    subparsers.add_parser("freeze", help="冻结收据（提交后）")
    subparsers.add_parser("package", help="K4 数据包")
    subparsers.add_parser("caps", help="分目录上限核对")

    args = parser.parse_args(argv)
    root = Path(args.repo_root)
    local = Path(args.local_root) if args.local_root else None
    try:
        if args.stage == "build":
            result = run_build(repo_root=root, probe_root=Path(args.probe_root), local_root=local)
            manifest = result["dataset_manifest"]
            print(
                f"build ok：训练 {manifest['training']['distinct_rows']} 行 / "
                f"{manifest['training']['multiset_samples']} 样本 / {manifest['training']['frames']} 帧；"
                f"选层 {manifest['select_eval']['rows']} 行；评估 {result['eval_manifest']['rows']} 行；"
                f"守恒 {result['conservation']['totals']['rows']} 条"
            )
        elif args.stage == "precheck":
            tokenizer_path = Path(args.tokenizer_dir) if args.tokenizer_dir else None
            document = run_precheck(repo_root=root, local_root=local, tokenizer_path=tokenizer_path)
            print(f"precheck ok：gold token max {document['observed_token_max']} ≤ {GOLD_TOKEN_MAX}")
        elif args.stage == "freeze":
            document = run_freeze(repo_root=root, local_root=local)
            print(f"freeze ok：HEAD {document['head'][:12]}")
        elif args.stage == "package":
            document = run_package(repo_root=root, local_root=local)
            print(f"package ok：{document['member_count']} 个成员 / {document['upload_bytes']} B")
        else:
            print(json.dumps(directory_caps(root, local), ensure_ascii=False, indent=2))
    except receipts.EngSftError as exc:
        print(f"{args.stage} 失败（{exc.reason}）：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def _declared_input_sha(local_root: Path, relative: str) -> str | None:
    """取 `build` 输入清单里该文件的登记 SHA（union 段），没有则 None。"""
    path = Path(local_root) / receipts.RECEIPTS_DIRNAME / receipts.INPUT_MANIFEST_NAME
    if not path.is_file():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    entry = document.get("union", {}).get(relative)
    return entry["sha256"] if entry else None


def load_definite_boxes(
    eval_rows: Sequence[dict[str, Any]],
    *,
    repo_root: Path = PROJECT_ROOT,
    local_root: Path | None = None,
    groups: Sequence[str] = ("G3p",),
) -> dict[str, list[list[float]]]:
    """G3′ 诊断取框（AC-3 修订 1）：按 `frame_id + definite_ids` 从已绑定 S3 取回 M 的原框。

    「已绑定」不是口号：本函数先把当前 S3 分片与 S5 的字节 SHA 与 `build` 输入清单
    （`receipts/input-manifest.json` 的 union 段）逐件比对，任一缺失或不符即
    `INPUT_HASH_CHANGED`，不取旧探针 v1 的单目标框代替 M，也不静默改用当前字节；
    缺源或缺框同样拒绝该次评分（调用方写失败收据），不剔除行、不改功能门定义。
    """
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    wanted = {row["row_id"]: row for row in eval_rows if row.get("group") in groups}
    frames = {row["frame_id"] for row in wanted.values()}

    catalog_path = root / FIELD_CATALOG_JSON
    shard_paths = sorted(Path(p) for p in glob.glob(str(root / FRAMES_CATALOG_SHARDS / "*.ndjson.gz")))
    binding_problems: list[dict[str, Any]] = []
    for path in [catalog_path, *shard_paths]:
        rel = receipts.relative_to_root(path, root)
        if not path.is_file():
            binding_problems.append({"path": rel, "problem": "SOURCE_MISSING"})
            continue
        declared = _declared_input_sha(local, rel)
        if declared is None:
            binding_problems.append({"path": rel, "problem": "NOT_IN_BUILD_INPUT_MANIFEST"})
            continue
        actual = receipts.sha256_file(path)
        if actual != declared:
            binding_problems.append({"path": rel, "declared": declared, "actual": actual})
    if binding_problems:
        raise receipts.InputHashChanged(
            "G3′ 取框的源未与 `build` 输入清单绑定（缺源 / 未登记 / 字节已变）",
            offending=binding_problems[:20],
        )
    catalog = _load_payload(catalog_path)
    found: dict[str, dict[str, list[float]]] = {}

    for shard in shard_paths:
        if not frames:
            break
        with gzip.open(shard, "rt") as handle:
            for line in handle:
                entry = json.loads(line)
                if entry["frame_id"] not in frames:
                    continue
                frames.discard(entry["frame_id"])
                record = unity_s3.adapt_frame(entry, catalog)
                found[entry["frame_id"]] = {
                    obj.object_id: list(obj.visible_norm_xywh)
                    for obj in record.objects
                    if obj.visible_norm_xywh
                }
    boxes: dict[str, list[list[float]]] = {}
    missing: list[dict[str, Any]] = []
    for row_id, row in wanted.items():
        frame_boxes = found.get(row["frame_id"])
        if frame_boxes is None:
            missing.append({"row_id": row_id, "problem": "FRAME_NOT_FOUND"})
            continue
        collected = []
        for object_id in row["definite_ids"]:
            box = frame_boxes.get(object_id)
            if box is None:
                missing.append({"row_id": row_id, "object_id": object_id, "problem": "BOX_MISSING"})
                continue
            collected.append(box)
        boxes[row_id] = collected
    if missing:
        raise receipts.InputHashChanged(
            "G3′ 诊断取框失败（缺源或缺框）", offending=missing[:20]
        )
    return boxes
