#!/usr/bin/env python3
"""输入清单、执行收据与写出边界（合同 §3「收据」段；仅标准库）。

本模块只从 `tools.eng_asset.receipts` 复用四个纯函数（`sha256_file`、
`utc_stamp`、`peak_rss_bytes`、`output_record`），其余一律本项自带：工作 ID、
schema 前缀、输出根、禁写闭集（ASSET-001 §3 再加 `runtime/eng-asset`、
`outputs/eng-asset`、`tools/eng_asset/`、`outputs/eng-sft3`）与失败原因闭集。

三件事与 ASSET-001 同构：

1. **输入清单**（`receipts/input-manifest.json`）：登记本次执行读过的每个文件
   的字节与 SHA-256 及来源，按阶段存 `before`/`after` 两份快照并逐条比较；
   `stages` 只追加（同一阶段多次执行按 `<stage>#<n>` 追加，不覆盖历史）。
2. **执行收据**：成功写 `receipts/run-<stage>-<utc>.json`，失败写
   `receipts/failure-<stage>-<utc>.json`（阶段 + 闭集原因 + 不符条目），
   失败不发布该次工件。
3. **写出边界**：`assert_output_allowed` 命中禁写闭集即 `OUTPUT_PATH_FORBIDDEN`。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import time
from typing import Any, Iterable

# 合同 §3「收据」：只复用这四个纯函数，不复用 ASSET-001 的清单/收据类。
from tools.eng_asset.receipts import (  # noqa: F401
    output_record,
    peak_rss_bytes,
    sha256_file,
    utc_stamp,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

WORK_ID = "P1-ENG-SFT-002"
SCHEMA_PREFIX = "p1-eng-sft-002"
# A2「工具输出」根（git 忽略）：`data/`、`upload/`、`panel/`、`returned/`。
LOCAL_ROOT = Path("outputs/eng-sft") / WORK_ID
# tokenizer 四文件（候选 1 信封的唯一下载项）落在工作项根之外的共享目录。
TOKENIZER_ROOT = Path("outputs/eng-sft/tokenizer")
RECEIPTS_DIRNAME = "receipts"
INPUT_MANIFEST_NAME = "input-manifest.json"
INPUT_MANIFEST_SCHEMA = f"{SCHEMA_PREFIX}/input-manifest/v1"
RUN_RECEIPT_SCHEMA = f"{SCHEMA_PREFIX}/run-receipt/v1"
FAILURE_RECEIPT_SCHEMA = f"{SCHEMA_PREFIX}/failure-receipt/v1"

# 合同 §3「收据」：输入清单阶段闭集，各写 before/after 快照，只追加。
STAGES: tuple[str, ...] = (
    "build",
    "precheck",
    "audit",
    "freeze",
    "package",
    "bundle",
    "return",
    "stop",
)

# 合同 §3「收据」失败原因闭集（19 项），不得新造 token。
FAILURE_REASONS: frozenset[str] = frozenset(
    {
        "MANIFEST_COUNT_MISMATCH",
        "SHARD_HASH_MISMATCH",
        "INPUT_HASH_CHANGED",
        "OUTPUT_PATH_FORBIDDEN",
        "HISTOGRAM_MISMATCH",
        "LEGACY_SOURCE_MISMATCH",
        "EVAL_GROUP_EMPTY",
        "CONSERVATION_MISMATCH",
        "FROZEN_FILE_DIRTY",
        "FROZEN_SET_MISMATCH",
        "PREDICTIONS_INCOMPLETE",
        "RETURN_HASH_MISMATCH",
        "IMAGE_GRID_MISMATCH",
        "GOLD_TOKEN_OVERFLOW",
        "SMOKE_FAILED",
        "PACKAGE_INCOMPLETE",
        "TOKENIZER_MISMATCH",
        "AUDIT_INCOMPLETE",
        "AUDIT_FINDING_OPEN",
    }
)

# 禁写闭集：ASSET-001 §3 的原件保护，再加本项合同点名的四项。`*` 语义见
# `is_forbidden_output`：前缀目录、同级同名前缀目录与字面文件都算。
FORBIDDEN_OUTPUT_PREFIXES: tuple[str, ...] = (
    "runtime/frames",
    "runtime/runs",
    "runtime/dist-data",
    "runtime/test-results",
    "runtime/rate-study",
    "runtime/p1-detect-scouting",
    "runtime/m3_body_truth",
    "runtime/eng-asset",
    "outputs/eng-asset",
    "outputs/eng-sft3",
    "config",
    "Assets",
    "controller",
    "tools/dist_data",
    "tools/eng_asset",
)
FORBIDDEN_OUTPUT_FILES: tuple[str, ...] = (
    "runtime/tracking_observation.json",
    "runtime/metrics.json",
)
# `runtime/*_command.json`（body/gimbal 桥文件）。
FORBIDDEN_OUTPUT_SUFFIXES: tuple[tuple[str, str], ...] = (("runtime/", "_command.json"),)


class EngSftError(RuntimeError):
    """本工作项的可归因失败；`reason` 取 `FAILURE_REASONS` 闭集之一。"""

    reason = "OUTPUT_PATH_FORBIDDEN"

    def __init__(self, message: str, offending: Iterable[Any] = ()) -> None:
        super().__init__(message)
        self.offending = list(offending)


def _error(name: str, reason: str) -> type[EngSftError]:
    return type(name, (EngSftError,), {"reason": reason})


OutputPathForbidden = _error("OutputPathForbidden", "OUTPUT_PATH_FORBIDDEN")
ManifestCountMismatch = _error("ManifestCountMismatch", "MANIFEST_COUNT_MISMATCH")
ShardHashMismatch = _error("ShardHashMismatch", "SHARD_HASH_MISMATCH")
InputHashChanged = _error("InputHashChanged", "INPUT_HASH_CHANGED")
HistogramMismatch = _error("HistogramMismatch", "HISTOGRAM_MISMATCH")
LegacySourceMismatch = _error("LegacySourceMismatch", "LEGACY_SOURCE_MISMATCH")
EvalGroupEmpty = _error("EvalGroupEmpty", "EVAL_GROUP_EMPTY")
ConservationMismatch = _error("ConservationMismatch", "CONSERVATION_MISMATCH")
FrozenFileDirty = _error("FrozenFileDirty", "FROZEN_FILE_DIRTY")
FrozenSetMismatch = _error("FrozenSetMismatch", "FROZEN_SET_MISMATCH")
PredictionsIncomplete = _error("PredictionsIncomplete", "PREDICTIONS_INCOMPLETE")
ImageGridMismatch = _error("ImageGridMismatch", "IMAGE_GRID_MISMATCH")
GoldTokenOverflow = _error("GoldTokenOverflow", "GOLD_TOKEN_OVERFLOW")
PackageIncomplete = _error("PackageIncomplete", "PACKAGE_INCOMPLETE")
TokenizerMismatch = _error("TokenizerMismatch", "TOKENIZER_MISMATCH")
AuditIncomplete = _error("AuditIncomplete", "AUDIT_INCOMPLETE")
AuditFindingOpen = _error("AuditFindingOpen", "AUDIT_FINDING_OPEN")


def relative_to_root(path: Path, repo_root: Path = PROJECT_ROOT) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    try:
        return candidate.resolve().relative_to(Path(repo_root).resolve()).as_posix()
    except ValueError:
        # 仓库外路径（T7 探针、测试临时目录）原样返回绝对路径；禁写闭集只覆盖仓库内。
        return candidate.resolve().as_posix()


def is_forbidden_output(rel_path: str) -> bool:
    if rel_path in FORBIDDEN_OUTPUT_FILES:
        return True
    for prefix, suffix in FORBIDDEN_OUTPUT_SUFFIXES:
        if rel_path.startswith(prefix) and rel_path.endswith(suffix):
            if "/" not in rel_path[len(prefix) :]:
                return True
    for prefix in FORBIDDEN_OUTPUT_PREFIXES:
        if rel_path == prefix or rel_path.startswith(prefix + "/"):
            return True
        # 同级同名前缀也是原件：`runtime/frames.arm-a-…/` 与 `runtime/frames` 同属禁写闭集。
        parent, _, leaf = prefix.rpartition("/")
        if parent:
            if not rel_path.startswith(parent + "/"):
                continue
            remainder = rel_path[len(parent) + 1 :]
        else:
            remainder = rel_path
        if remainder.split("/", 1)[0].startswith(leaf + "."):
            return True
    return False


def assert_output_allowed(path: Path, repo_root: Path = PROJECT_ROOT) -> Path:
    """写出前的包含检查；命中禁写闭集即 `OUTPUT_PATH_FORBIDDEN`。"""
    rel = relative_to_root(path, repo_root)
    if is_forbidden_output(rel):
        raise OutputPathForbidden(f"写出路径落入禁写闭集（原件保护）：{rel}", offending=[rel])
    return Path(path)


@dataclass
class InputEntry:
    path: str
    bytes: int
    sha256: str
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {"path": self.path, "bytes": self.bytes, "sha256": self.sha256, "source": self.source}


@dataclass
class InputManifest:
    """本次执行实际读取的输入清单（AC-1）。

    `record` 在读取点登记：传 `declared_sha256` 即对字节复核（不把「manifest
    未变」当作其引用文件未变）；`recompute` 在结束时重算，逐条比较。
    """

    repo_root: Path = PROJECT_ROOT
    entries: dict[str, InputEntry] = field(default_factory=dict)

    def record(
        self,
        path: Path,
        *,
        source: str,
        declared_sha256: str | None = None,
        precomputed_sha256: str | None = None,
    ) -> InputEntry:
        rel = relative_to_root(path, self.repo_root)
        absolute = Path(path) if Path(path).is_absolute() else self.repo_root / path
        size = absolute.stat().st_size
        actual = precomputed_sha256 or sha256_file(absolute)
        if declared_sha256 is not None and actual != declared_sha256:
            raise InputHashChanged(
                f"输入文件哈希与声明不符：{rel} 实测 {actual} 声明 {declared_sha256}",
                offending=[{"path": rel, "declared": declared_sha256, "actual": actual}],
            )
        entry = InputEntry(rel, size, actual, source)
        self.entries[rel] = entry
        return entry

    def recompute(self) -> dict[str, InputEntry]:
        after: dict[str, InputEntry] = {}
        for rel, entry in self.entries.items():
            absolute = Path(rel) if Path(rel).is_absolute() else self.repo_root / rel
            after[rel] = InputEntry(rel, absolute.stat().st_size, sha256_file(absolute), entry.source)
        return after

    def diff(self, after: dict[str, InputEntry]) -> list[dict[str, Any]]:
        mismatches: list[dict[str, Any]] = []
        for rel, before in self.entries.items():
            later = after.get(rel)
            if later is None:
                mismatches.append({"path": rel, "problem": "MISSING_AFTER"})
            elif (later.bytes, later.sha256) != (before.bytes, before.sha256):
                mismatches.append(
                    {
                        "path": rel,
                        "before": {"bytes": before.bytes, "sha256": before.sha256},
                        "after": {"bytes": later.bytes, "sha256": later.sha256},
                    }
                )
        for rel in after:
            if rel not in self.entries:
                mismatches.append({"path": rel, "problem": "UNEXPECTED_AFTER"})
        return mismatches


class ReceiptWriter:
    """把清单与收据落到本地输出根（git 忽略），并保护写出闭集。"""

    def __init__(self, local_root: Path | None = None, repo_root: Path = PROJECT_ROOT) -> None:
        self.repo_root = Path(repo_root)
        self.local_root = Path(local_root) if local_root is not None else self.repo_root / LOCAL_ROOT
        self.receipts_dir = self.local_root / RECEIPTS_DIRNAME

    def _write_json(self, path: Path, document: dict[str, Any]) -> Path:
        assert_output_allowed(path, self.repo_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        path.write_text(payload, encoding="utf-8")
        return path

    # --- 输入清单 ---------------------------------------------------------
    def manifest_path(self) -> Path:
        return self.receipts_dir / INPUT_MANIFEST_NAME

    def load_manifest_document(self) -> dict[str, Any]:
        path = self.manifest_path()
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
        return {
            "schema_version": INPUT_MANIFEST_SCHEMA,
            "work_id": WORK_ID,
            "stages": {},
            "union": {},
        }

    def save_input_manifest(
        self,
        stage: str,
        manifest: InputManifest,
        after: dict[str, InputEntry],
        mismatches: list[dict[str, Any]],
        *,
        successful: bool,
    ) -> Path:
        if stage not in STAGES:
            raise EngSftError(f"输入清单阶段不在闭集内：{stage!r}")
        if successful and mismatches:
            raise InputHashChanged("输入清单存在不符条目，不得保存为成功执行", offending=mismatches)
        document = self.load_manifest_document()
        document["schema_version"] = INPUT_MANIFEST_SCHEMA
        document["work_id"] = WORK_ID
        stages = document.setdefault("stages", {})
        # 只追加：同一阶段重跑写 `<stage>#2`、`#3`…，历史快照一行不改。
        key = stage
        serial = 1
        while key in stages:
            serial += 1
            key = f"{stage}#{serial}"
        stages[key] = {
            "stage": stage,
            "utc": utc_stamp(),
            "before": [e.as_dict() for e in sorted(manifest.entries.values(), key=lambda x: x.path)],
            "after": [e.as_dict() for e in sorted(after.values(), key=lambda x: x.path)],
            "equal": not mismatches,
            "mismatches": mismatches,
            "successful": successful,
        }
        if successful and not mismatches:
            union = document.setdefault("union", {})
            for rel, entry in manifest.entries.items():
                union[rel] = entry.as_dict()
        return self._write_json(self.manifest_path(), document)

    # --- 执行收据 ---------------------------------------------------------
    def write_run_receipt(
        self,
        stage: str,
        *,
        started: float,
        outputs: list[dict[str, Any]],
        extra: dict[str, Any] | None = None,
    ) -> Path:
        document: dict[str, Any] = {
            "schema_version": RUN_RECEIPT_SCHEMA,
            "work_id": WORK_ID,
            "stage": stage,
            "utc": utc_stamp(),
            "elapsed_s": round(time.monotonic() - started, 3),
            "peak_rss_bytes": peak_rss_bytes(),
            "outputs": outputs,
        }
        if extra:
            document.update(extra)
        return self._write_json(self.receipts_dir / f"run-{stage}-{document['utc']}.json", document)

    def write_failure_receipt(
        self, stage: str, reason: str, offending: Iterable[Any], *, message: str = ""
    ) -> Path:
        if reason not in FAILURE_REASONS:
            raise EngSftError(f"失败原因不在闭集内：{reason!r}")
        document = {
            "schema_version": FAILURE_RECEIPT_SCHEMA,
            "work_id": WORK_ID,
            "stage": stage,
            "utc": utc_stamp(),
            "reason": reason,
            "message": message,
            "offending": list(offending),
        }
        return self._write_json(self.receipts_dir / f"failure-{stage}-{document['utc']}.json", document)
