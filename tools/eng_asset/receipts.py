#!/usr/bin/env python3
"""输入清单、执行收据与写出边界（AC-1 / AC-6 的机制底座；仅标准库）。

三件事：

1. **输入清单**（`receipts/input-manifest.json`）：记录本次执行实际读取的
   每个文件的字节数与 SHA-256 及其来源（S3/S4 manifest 引用、S1
   `records[].sha256`、首次读取现算）。同一文件内按执行阶段保存
   `before`/`after` 两份并逐条比较；`union` 累积历次**成功**执行读过的输入，
   供停点自证复核（合同 §3 表 B）。
2. **执行收据**：成功写 `receipts/run-<stage>-<utc>.json`（耗时、峰值 RSS、
   输出文件行数/字节/SHA-256）；失败写 `receipts/failure-<stage>-<utc>.json`
   （阶段、闭集原因、不符条目），且**不发布该次成功工件**。
3. **写出边界**：`assert_output_allowed` 对禁写闭集做包含检查，命中即
   `OUTPUT_PATH_FORBIDDEN` 拒绝运行。

失败原因是闭集（合同 §3 表 B 末行），不得新造 token。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import resource
import time
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

WORK_ID = "P1-ENG-ASSET-001"
LOCAL_ROOT = Path("runtime/eng-asset") / WORK_ID
RECEIPTS_DIRNAME = "receipts"
INPUT_MANIFEST_NAME = "input-manifest.json"
INPUT_MANIFEST_SCHEMA = "p1-eng-asset-001/input-manifest/v1"
RUN_RECEIPT_SCHEMA = "p1-eng-asset-001/run-receipt/v1"
FAILURE_RECEIPT_SCHEMA = "p1-eng-asset-001/failure-receipt/v1"

# 合同 §3 表 B 末行的失败原因闭集。
FAILURE_REASONS: frozenset[str] = frozenset(
    {
        "MANIFEST_COUNT_MISMATCH",
        "SHARD_HASH_MISMATCH",
        "INPUT_HASH_CHANGED",
        "OUTPUT_PATH_FORBIDDEN",
        "QUOTA_FILE_DIRTY",
        # AC-4 修订 3（2026-09-08 补充裁定）追加：代录条目缺失/重复/未完成/
        # 格式或取值错误/索引与清单不符时，stats 失败退出并只写失败收据。
        "VERDICT_FORMAT_MISMATCH",
    }
)

# 合同 §3「禁写闭集（原件保护）」：写出路径落入任一根即拒绝。`*` 前缀项按
# 「同名文件或同名前缀目录」处理（`runtime/frames` 与 `runtime/frames.xxx`
# 都算），其余按目录前缀或字面路径。
FORBIDDEN_OUTPUT_PREFIXES: tuple[str, ...] = (
    "runtime/frames",
    "runtime/runs",
    "runtime/dist-data",
    "runtime/test-results",
    "runtime/rate-study",
    "runtime/p1-detect-scouting",
    "runtime/m3_body_truth",
    "config",
    "Assets",
    "controller",
    "tools/dist_data",
)
FORBIDDEN_OUTPUT_FILES: tuple[str, ...] = (
    "runtime/tracking_observation.json",
    "runtime/metrics.json",
)
# `runtime/*_command.json`（body/gimbal 桥文件）。
FORBIDDEN_OUTPUT_SUFFIXES: tuple[tuple[str, str], ...] = (("runtime/", "_command.json"),)


class EngAssetError(RuntimeError):
    """本工作项的可归因失败；`reason` 取 `FAILURE_REASONS` 闭集之一。"""

    reason = "OUTPUT_PATH_FORBIDDEN"

    def __init__(self, message: str, offending: Iterable[Any] = ()) -> None:
        super().__init__(message)
        self.offending = list(offending)


class OutputPathForbidden(EngAssetError):
    reason = "OUTPUT_PATH_FORBIDDEN"


class ManifestCountMismatch(EngAssetError):
    reason = "MANIFEST_COUNT_MISMATCH"


class ShardHashMismatch(EngAssetError):
    reason = "SHARD_HASH_MISMATCH"


class InputHashChanged(EngAssetError):
    reason = "INPUT_HASH_CHANGED"


class QuotaFileDirty(EngAssetError):
    reason = "QUOTA_FILE_DIRTY"


class VerdictFormatMismatch(EngAssetError):
    """代录机读格式 v1 不满足；统计一律不产出（AC-4 修订 3）。"""

    reason = "VERDICT_FORMAT_MISMATCH"


def utc_stamp() -> str:
    """收据文件名与时间戳统一用 UTC，不用民用时钟本地化形式。"""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path, *, chunk_bytes: int = 1 << 20) -> str:
    """分块求文件 SHA-256（1.6 GiB 分片也只驻留 1 MiB）。"""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk_bytes)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def peak_rss_bytes() -> int:
    """本进程峰值 RSS（字节）。macOS 的 `ru_maxrss` 是字节，Linux 是 KiB。"""
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(raw) if platform.system() == "Darwin" else int(raw) * 1024


def relative_to_root(path: Path, repo_root: Path = PROJECT_ROOT) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    try:
        return candidate.resolve().relative_to(Path(repo_root).resolve()).as_posix()
    except ValueError:
        # 仓库外路径（例如测试临时目录）原样返回绝对路径，禁写闭集只覆盖仓库内。
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
        # 同级同名前缀也是原件：`runtime/frames.arm-a-…/`、
        # `runtime/m3_body_truth.….jsonl` 与 `runtime/frames` 同属禁写闭集。
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
        raise OutputPathForbidden(
            f"写出路径落入禁写闭集（原件保护）：{rel}", offending=[rel]
        )
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

    `record` 在读取点登记；`recompute` 在执行结束（或停点自证）时重算，两份
    逐条比较，任一不等即 `INPUT_HASH_CHANGED`。
    """

    repo_root: Path = PROJECT_ROOT
    entries: dict[str, InputEntry] = field(default_factory=dict)

    def record(
        self,
        path: Path,
        *,
        source: str,
        sha256: str | None = None,
        precomputed_sha256: str | None = None,
    ) -> InputEntry:
        """登记一个被读文件。

        `sha256` 是**声明值**（S3/S4 manifest 或 S1 `records[].sha256`），登记时
        即对字节复核，不把「manifest 未变」当作其引用文件未变（AR1-3）。
        `precomputed_sha256` 供调用方传入本次已经算过的实测值，避免同一文件在
        一次执行里被重复哈希（语义等价，省一遍 I/O）。
        """
        rel = relative_to_root(path, self.repo_root)
        absolute = Path(path) if Path(path).is_absolute() else self.repo_root / path
        size = absolute.stat().st_size
        digest = sha256 if sha256 is not None else (precomputed_sha256 or sha256_file(absolute))
        if sha256 is not None:
            actual = precomputed_sha256 or sha256_file(absolute)
            if actual != digest:
                raise InputHashChanged(
                    f"输入文件哈希与声明不符：{rel} 实测 {actual} 声明 {digest}",
                    offending=[{"path": rel, "declared": digest, "actual": actual}],
                )
        entry = InputEntry(rel, size, digest, source)
        self.entries[rel] = entry
        return entry

    def recompute(self) -> dict[str, InputEntry]:
        after: dict[str, InputEntry] = {}
        for rel, entry in self.entries.items():
            absolute = self.repo_root / rel if not Path(rel).is_absolute() else Path(rel)
            after[rel] = InputEntry(
                rel, absolute.stat().st_size, sha256_file(absolute), entry.source
            )
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
    """把清单与收据落到本地目录（git 忽略），并保护写出闭集。"""

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
        return {"schema_version": INPUT_MANIFEST_SCHEMA, "work_id": WORK_ID, "stages": {}, "union": {}}

    def save_input_manifest(
        self,
        stage: str,
        manifest: InputManifest,
        after: dict[str, InputEntry],
        mismatches: list[dict[str, Any]],
        *,
        successful: bool,
    ) -> Path:
        if successful and mismatches:
            # 机制层 fail-closed：带不符条目的执行不得被记成成功（接受侧 2026-09-09
            # 只读检查指出 stage_stats 曾无条件 successful=True）。
            raise InputHashChanged(
                "输入清单存在不符条目，不得保存为成功执行", offending=mismatches
            )
        document = self.load_manifest_document()
        document["schema_version"] = INPUT_MANIFEST_SCHEMA
        document["work_id"] = WORK_ID
        stages = document.setdefault("stages", {})
        stages[stage] = {
            "utc": utc_stamp(),
            "before": [entry.as_dict() for entry in sorted(manifest.entries.values(), key=lambda e: e.path)],
            "after": [entry.as_dict() for entry in sorted(after.values(), key=lambda e: e.path)],
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
        document = {
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
            raise EngAssetError(f"失败原因不在闭集内：{reason!r}")
        document = {
            "schema_version": FAILURE_RECEIPT_SCHEMA,
            "work_id": WORK_ID,
            "stage": stage,
            "utc": utc_stamp(),
            "reason": reason,
            "message": message,
            "offending": list(offending),
        }
        return self._write_json(
            self.receipts_dir / f"failure-{stage}-{document['utc']}.json", document
        )


def output_record(path: Path, *, lines: int | None = None) -> dict[str, Any]:
    """派生工件的行数/字节/SHA-256（AC-6 的交付记录）。"""
    absolute = Path(path)
    record: dict[str, Any] = {
        "path": relative_to_root(absolute),
        "bytes": absolute.stat().st_size,
        "sha256": sha256_file(absolute),
    }
    if lines is not None:
        record["lines"] = lines
    return record
