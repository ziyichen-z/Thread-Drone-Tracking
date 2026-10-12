#!/usr/bin/env python3
"""create-once 工件存储、S0–S9 单向 DAG 禁行边与 supersession 协议。

提案 §2（禁行边）、§2.2（create-once / 字节幂等 / supersession）、
BC-DATA-1（S7 只读冻结的 S1–S6，S8 只作物化与等价断言）。

工件落在 `runtime/dist-data/<artifact>/<attempt>/<artifact>.json`
（`runtime/**` 已 gitignored）。工件信封内**没有任何时钟字段**——重跑必须
字节幂等，时间戳会破坏该性质。
"""

from __future__ import annotations

from dataclasses import dataclass
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

from tools.dist_data import contract

ENVELOPE_VERSION = "p1-vlm-data-001-artifact/v1"

# S0–S9 单向 DAG 的阶段号（提案 §2）。同阶段工件之间允许引用（如 S7 的
# g0_report 读同为 S7 的 mother_candidates）；**读取序号更大的阶段一律
# 硬错误**，这就是「S7 不存在母集/模板」与「S8 不得反向影响门值」的机检。
STAGES: dict[str, int] = {
    "contract": 0,
    "inventory": 1,
    "layout": 2,
    "frames_catalog": 3,
    "splits": 4,
    "field_catalog": 5,
    "audit": 6,
    "mother_candidates": 7,
    "g0_report": 7,
    "mother_set": 8,
    "template_expressions": 8,
    "stop_point": 9,
}


class DistDataError(RuntimeError):
    """本工具包的合同违反基类（全部 fail-closed）。"""


class ForbiddenEdgeError(DistDataError):
    """违反 §2 禁行边：读取了序号更大阶段的工件。"""


class CreateOnceError(DistDataError):
    """违反 create-once：同一 attempt 重写出不同字节。"""


class SupersessionError(DistDataError):
    """违反 §2.2 supersession 协议。"""


class IncompleteCompositeArtifactError(DistDataError):
    """BC-DATA-25 (6)：发现孤立 staging 或残缺分片；不自动删除、重用或续传。"""


# --- BC-DATA-25：高基数行集的单一逻辑工件 + 有界流式存储 -------------------
COMPOSITE_STORAGE_VERSION = "p1-vlm-data-001-composite/v1"
# 每个 shard 的**未压缩** canonical 行字节上限；单行自身超限时独占一 shard。
SHARD_MAX_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
SHARD_DIRNAME = "shards"
STAGING_DIRNAME = ".staging"
# gzip 必须字节幂等：固定 mtime 与压缩级别。CPython 在 `mtime=0` 下写出的
# OS 字节即 255（实测），与合同要求一致。
GZIP_MTIME = 0
GZIP_COMPRESSLEVEL = 9
GZIP_OS_BYTE = 255


def _gzip_bytes(payload: bytes) -> bytes:
    """确定性 gzip：同输入必得同字节。"""
    buffer = io.BytesIO()
    with gzip.GzipFile(
        fileobj=buffer, mode="wb", compresslevel=GZIP_COMPRESSLEVEL, mtime=GZIP_MTIME
    ) as handle:
        handle.write(payload)
    blob = buffer.getvalue()
    if blob[9] != GZIP_OS_BYTE:  # pragma: no cover - 防御性，实测恒为 255
        blob = blob[:9] + bytes([GZIP_OS_BYTE]) + blob[10:]
    return blob


def canonical_json_bytes(document: Any) -> bytes:
    """确定性 JSON 字节：键排序、无多余空白、UTF-8、结尾换行。"""
    text = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (text + "\n").encode("utf-8")


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seeded_digest(seed: str, sample_id: str) -> bytes:
    """BC-DATA-2 / §2.5 的 SHA-256(seed ‖ "/" ‖ id) 原始 32 字节。"""
    return hashlib.sha256(f"{seed}/{sample_id}".encode("utf-8")).digest()


def deterministic_sort_key(seed: str, sample_id: str) -> tuple[bytes, bytes]:
    """BC-DATA-2 终决键：哈希原始 32 字节，继以 UTF-8 sample/atom id 字节。

    第二分量使排序不依赖「哈希无碰撞」假设。
    """
    return (seeded_digest(seed, sample_id), sample_id.encode("utf-8"))


@dataclass(frozen=True)
class ArtifactRef:
    """一个 create-once 工件的可复算引用。"""

    artifact: str
    attempt: str
    stage: int
    sha256: str
    path: str

    def as_reference(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact,
            "attempt": self.attempt,
            "sha256": self.sha256,
        }


class ArtifactStore:
    """`runtime/dist-data/` 下的 create-once 工件仓。"""

    def __init__(self, repo_root: Path, root: str | None = None) -> None:
        self.repo_root = Path(repo_root)
        self.root = self.repo_root / (root or contract.ARTIFACT_ROOT)

    # --- 路径 -------------------------------------------------------------
    def artifact_dir(self, artifact: str) -> Path:
        self._require_known(artifact)
        return self.root / artifact

    def path_for(self, artifact: str, attempt: str) -> Path:
        return self.artifact_dir(artifact) / attempt / f"{artifact}.json"

    @staticmethod
    def _require_known(artifact: str) -> None:
        if artifact not in STAGES:
            raise DistDataError(f"未知工件类型 {artifact!r}；S0–S9 工件集是闭集")

    def _check_supersession(
        self, artifact: str, supersedes: str | None, supersession_reason: str | None
    ) -> None:
        """§2.2 supersession 前置校验；普通工件与组合工件**共用同一实现**。

        P1-VLM-DATA-002 §2.2 第 5 条要求组合工件（`frames_catalog`/`splits`）
        走同一协议，此前 `write_composite` 把 envelope 的两个字段写死为
        `null`，组合工件因此无法 supersede 前身。
        """
        if supersedes is not None:
            if supersession_reason is None:
                raise SupersessionError("supersession 必须记录原因（§2.2：禁止无归因重做）")
            previous = self.path_for(artifact, supersedes)
            if not previous.exists():
                raise SupersessionError(
                    f"被 supersede 的 attempt 不存在：{previous}；旧 attempt 必须原样保留"
                )
        elif supersession_reason is not None:
            raise SupersessionError("supersession_reason 只能与 supersedes 同时出现")

    # --- 写 ---------------------------------------------------------------
    def write(
        self,
        artifact: str,
        attempt: str,
        payload: Any,
        *,
        stage: int | None = None,
        supersedes: str | None = None,
        supersession_reason: str | None = None,
        inputs: list[dict[str, Any]] | None = None,
    ) -> ArtifactRef:
        """写 create-once 工件；同字节重跑幂等，异字节即 `CreateOnceError`。"""
        self._require_known(artifact)
        declared_stage = STAGES[artifact] if stage is None else stage
        if declared_stage != STAGES[artifact]:
            raise DistDataError(
                f"{artifact} 的阶段号被声明为 {declared_stage}，与 DAG 定义 {STAGES[artifact]} 不符"
            )
        self._check_supersession(artifact, supersedes, supersession_reason)

        envelope = {
            "schema_version": ENVELOPE_VERSION,
            "work_id": contract.WORK_ID,
            "artifact": artifact,
            "attempt": attempt,
            "stage": declared_stage,
            "supersedes": supersedes,
            "supersession_reason": supersession_reason,
            "inputs": inputs or [],
            "payload": payload,
        }
        data = canonical_json_bytes(envelope)
        path = self.path_for(artifact, attempt)
        if path.exists():
            existing = path.read_bytes()
            if existing != data:
                raise CreateOnceError(
                    f"create-once 违反：{path} 已存在且字节不同；"
                    "代码缺陷须走 supersession 新建 attempt，禁止覆盖后仍声称原哈希冻结"
                )
            return ArtifactRef(
                artifact, attempt, declared_stage, sha256_hex(existing), str(path)
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return ArtifactRef(artifact, attempt, declared_stage, sha256_hex(data), str(path))

    # --- 读 ---------------------------------------------------------------
    def read(
        self,
        artifact: str,
        attempt: str,
        *,
        requesting_stage: int,
        expected_sha256: str | None = None,
    ) -> tuple[Any, ArtifactRef]:
        """读工件；违反禁行边或哈希不符即硬错误。"""
        self._require_known(artifact)
        stage = STAGES[artifact]
        if stage > requesting_stage:
            raise ForbiddenEdgeError(
                f"禁行边：阶段 S{requesting_stage} 不得读取阶段 S{stage} 的工件 {artifact!r}"
            )
        path = self.path_for(artifact, attempt)
        if not path.exists():
            raise DistDataError(f"工件缺失：{path}")
        data = path.read_bytes()
        digest = sha256_hex(data)
        if expected_sha256 is not None and digest != expected_sha256:
            raise DistDataError(
                f"工件哈希不符：{path} 实测 {digest}，引用声明 {expected_sha256}"
            )
        envelope = json.loads(data.decode("utf-8"))
        if envelope.get("artifact") != artifact or envelope.get("attempt") != attempt:
            raise DistDataError(f"工件信封身份不符：{path}")
        return envelope["payload"], ArtifactRef(artifact, attempt, stage, digest, str(path))

    # --- BC-DATA-25 组合工件 ---------------------------------------------
    def shard_dir(self, artifact: str, attempt: str) -> Path:
        return self.artifact_dir(artifact) / attempt / SHARD_DIRNAME

    def staging_dir(self, artifact: str, attempt: str) -> Path:
        return self.artifact_dir(artifact) / attempt / STAGING_DIRNAME

    def write_composite(
        self,
        artifact: str,
        attempt: str,
        summary: dict[str, Any] | Callable[[], dict[str, Any]],
        rows: Iterable[Any],
        *,
        stage: int | None = None,
        supersedes: str | None = None,
        supersession_reason: str | None = None,
        inputs: list[dict[str, Any]] | None = None,
    ) -> ArtifactRef:
        """把有序行流写成 manifest + 有界 gzip-NDJSON shards 的**单一**逻辑工件。

        `rows` 必须是流（生成器）：本方法一次只在内存里持有一个 shard 的字节，
        绝不物化全集——这正是 BC-DATA-25 (5) 要求的有界消费。发布点是 manifest：
        它写成功之前，`attempts()` 与下游一律视为工件缺席。

        同输入重跑：manifest 已存在时逐字节复核 manifest 与全部 shard，一致则
        幂等返回，任一字节不同即 `CreateOnceError`（此路径不写任何文件）。
        """
        self._require_known(artifact)
        self._check_supersession(artifact, supersedes, supersession_reason)
        manifest_path = self.path_for(artifact, attempt)
        published = manifest_path.exists()
        staging = self.staging_dir(artifact, attempt)
        shards = self.shard_dir(artifact, attempt)
        if not published:
            # manifest 是唯一提交点，所以「无 manifest 却有分片残留」一律是
            # 不完整组合工件——**两种残留都算**：
            #   - `.staging/`：分片写到一半就中断；
            #   - `shards/`：staging 已整体 rename、manifest 尚未 commit 的
            #     故障窗口（接受轮 22 SP22-2 实测：原实现在此只会以
            #     `OSError: Directory not empty` 失败，且新建 `.staging/`
            #     改变了现场）。
            # 判定必须发生在**写任何新字节之前**：不删除、不重用、不续传、
            # 不新增残留。
            residue = [path for path in (staging, shards) if path.exists()]
            if residue:
                raise IncompleteCompositeArtifactError(
                    "发现分片残留且无 manifest："
                    + "、".join(str(path) for path in residue)
                    + f"（{artifact}@{attempt}）；BC-DATA-25 (6) 要求原样保留并返回"
                    " Acceptance，禁止自动删除、重用或续传"
                )

        shard_records: list[dict[str, Any]] = []
        stream_digest = hashlib.sha256()
        row_count = 0
        current = _ShardStream()
        target = staging if not published else None
        if target is not None:
            target.mkdir(parents=True, exist_ok=True)

        def _flush(shard: _ShardStream) -> None:
            """固化一个 shard 后**立即**释放它的字节：内存只持有当前一个。"""
            if not shard.rows:
                return
            record, blob = shard.finish(len(shard_records))
            shard_records.append(record)
            if target is not None:
                _write_shard(target, record, blob)
            # 幂等复核路径不写盘，只留 record 供逐 shard 比对；blob 在此出作用域。

        try:
            for row in rows:
                line = _canonical_row_bytes(row)
                stream_digest.update(line)
                row_count += 1
                if current.would_overflow(line):
                    _flush(current)
                    current = _ShardStream()
                current.add(line, str(row.get("frame_id", "")))
            _flush(current)

            # summary 可以是**流消费完之后**才成立的量（如 S4 的 exposure 汇总）：
            # 允许传一个零参可调用，在此处求值，从而一遍扫描既出行又出汇总。
            resolved_summary = summary() if callable(summary) else summary
            manifest_payload = {
                **resolved_summary,
                "storage": {
                    "schema_version": COMPOSITE_STORAGE_VERSION,
                    "codec": "gzip-ndjson",
                    "shard_max_uncompressed_bytes": SHARD_MAX_UNCOMPRESSED_BYTES,
                    "gzip": {
                        "mtime": GZIP_MTIME,
                        "compresslevel": GZIP_COMPRESSLEVEL,
                        "os_byte": GZIP_OS_BYTE,
                    },
                },
                "shards": shard_records,
                "row_count": row_count,
                "stream_sha256": stream_digest.hexdigest(),
            }
            envelope = {
                "schema_version": ENVELOPE_VERSION,
                "work_id": contract.WORK_ID,
                "artifact": artifact,
                "attempt": attempt,
                "stage": STAGES[artifact] if stage is None else stage,
                "supersedes": supersedes,
                "supersession_reason": supersession_reason,
                "inputs": inputs or [],
                "payload": manifest_payload,
            }
            data = canonical_json_bytes(envelope)

            if published:
                existing = manifest_path.read_bytes()
                if existing != data:
                    raise CreateOnceError(
                        f"create-once 违反：{manifest_path} 已存在且 manifest 字节不同；"
                        "代码缺陷须走 supersession 新建 attempt，禁止覆盖"
                    )
                self._verify_shards(artifact, attempt, shard_records)
                return ArtifactRef(
                    artifact, attempt, envelope["stage"], sha256_hex(existing),
                    str(manifest_path),
                )

            # 固化：staging 内逐 shard 复核字节身份，再整体搬到最终位置。
            self._verify_shards_in(staging, shard_records)
            final = shards
            final.parent.mkdir(parents=True, exist_ok=True)
            staging.rename(final)
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            _atomic_publish(manifest_path, data)
            return ArtifactRef(
                artifact, attempt, envelope["stage"], sha256_hex(data), str(manifest_path)
            )
        except Exception:
            # 中断时**不清理**：孤立 staging 必须留在原地供人工对账。
            raise

    def _verify_shards_in(self, directory: Path, records: list[dict[str, Any]]) -> None:
        for record in records:
            path = directory / _shard_name(int(record["index"]))
            if not path.is_file():
                raise IncompleteCompositeArtifactError(f"shard 缺失：{path}")
            blob = path.read_bytes()
            if sha256_hex(blob) != record["sha256"] or len(blob) != record["compressed_bytes"]:
                raise IncompleteCompositeArtifactError(f"shard 字节与清单不符：{path}")

    def _verify_shards(
        self, artifact: str, attempt: str, records: list[dict[str, Any]]
    ) -> None:
        self._verify_shards_in(self.shard_dir(artifact, attempt), records)

    def composite_manifest(
        self, artifact: str, attempt: str, *, requesting_stage: int
    ) -> tuple[dict[str, Any], ArtifactRef]:
        """读 manifest（复用 `read()` 的禁行边与信封身份校验）。"""
        payload, reference = self.read(artifact, attempt, requesting_stage=requesting_stage)
        if "shards" not in payload or "stream_sha256" not in payload:
            raise DistDataError(
                f"{artifact}@{attempt} 不是 BC-DATA-25 组合工件（manifest 缺 shards/stream_sha256）"
            )
        return payload, reference

    def read_composite_rows(
        self, artifact: str, attempt: str, *, requesting_stage: int
    ) -> Iterator[Any]:
        """类型化行迭代器：逐 shard 复核身份/行数/顺序，末尾复核累积哈希。

        下游只能经本迭代器取数，不得直接依赖 shard 路径，也不得把 shard 当作
        独立工件引用（BC-DATA-25 (4)）。
        """
        payload, _reference = self.composite_manifest(
            artifact, attempt, requesting_stage=requesting_stage
        )
        records = payload["shards"]
        indices = [record["index"] for record in records]
        if indices != [f"{i:05d}" for i in range(len(records))]:
            raise IncompleteCompositeArtifactError(
                f"{artifact}@{attempt} 的 shard 序号不连续或乱序：{indices[:5]}…"
            )
        directory = self.shard_dir(artifact, attempt)
        stream_digest = hashlib.sha256()
        total = 0
        for record in records:
            path = directory / _shard_name(int(record["index"]))
            if not path.is_file():
                raise IncompleteCompositeArtifactError(f"shard 缺失：{path}")
            blob = path.read_bytes()
            if sha256_hex(blob) != record["sha256"]:
                raise IncompleteCompositeArtifactError(f"shard 哈希不符：{path}")
            if len(blob) != record["compressed_bytes"]:
                raise IncompleteCompositeArtifactError(f"shard 压缩字节数不符：{path}")
            raw = gzip.decompress(blob)
            if len(raw) != record["uncompressed_bytes"]:
                raise IncompleteCompositeArtifactError(f"shard 未压缩字节数不符：{path}")
            lines = raw.splitlines(keepends=True)
            if len(lines) != record["lines"]:
                raise IncompleteCompositeArtifactError(
                    f"shard 行数不符：{path} 实测 {len(lines)} 清单 {record['lines']}"
                )
            for line in lines:
                stream_digest.update(line)
                total += 1
                yield json.loads(line)
        if total != payload["row_count"]:
            raise IncompleteCompositeArtifactError(
                f"{artifact}@{attempt} 行总数不符：实测 {total} 清单 {payload['row_count']}"
            )
        if stream_digest.hexdigest() != payload["stream_sha256"]:
            raise IncompleteCompositeArtifactError(
                f"{artifact}@{attempt} 有序行流累积哈希不符"
            )

    def attempts(self, artifact: str) -> list[str]:
        """按名称升序列出已存在的 attempt（旧 attempt 永不删除）。"""
        directory = self.artifact_dir(artifact)
        if not directory.exists():
            return []
        return sorted(
            child.name
            for child in directory.iterdir()
            if child.is_dir() and (child / f"{artifact}.json").exists()
        )

    def supersession_chain(self, artifact: str, attempt: str) -> list[str]:
        """从 attempt 逆推 supersession 链（最新在前），用于审计留痕。"""
        chain = [attempt]
        current = attempt
        seen = {attempt}
        while True:
            path = self.path_for(artifact, current)
            if not path.exists():
                break
            envelope = json.loads(path.read_bytes().decode("utf-8"))
            previous = envelope.get("supersedes")
            if not previous:
                break
            if previous in seen:
                raise SupersessionError(f"supersession 链成环：{artifact}/{previous}")
            seen.add(previous)
            chain.append(previous)
            current = previous
        return chain


def _shard_name(index: int) -> str:
    return f"{index:05d}.ndjson.gz"


class _ShardStream:
    """把有序行流切成有界 shard；一次只在内存里持有一个 shard 的字节。"""

    def __init__(self) -> None:
        self.rows: list[bytes] = []
        self.uncompressed = 0
        self.lines = 0
        self.first_frame_id: str | None = None
        self.last_frame_id: str | None = None

    def would_overflow(self, line: bytes) -> bool:
        return bool(self.rows) and self.uncompressed + len(line) > SHARD_MAX_UNCOMPRESSED_BYTES

    def add(self, line: bytes, frame_id: str) -> None:
        if self.first_frame_id is None:
            self.first_frame_id = frame_id
        self.last_frame_id = frame_id
        self.rows.append(line)
        self.uncompressed += len(line)
        self.lines += 1

    def finish(self, index: int) -> tuple[dict[str, Any], bytes]:
        payload = b"".join(self.rows)
        blob = _gzip_bytes(payload)
        record = {
            "index": f"{index:05d}",
            "path": f"{SHARD_DIRNAME}/{_shard_name(index)}",
            "sha256": sha256_hex(blob),
            "lines": self.lines,
            "uncompressed_bytes": self.uncompressed,
            "compressed_bytes": len(blob),
            "first_frame_id": self.first_frame_id,
            "last_frame_id": self.last_frame_id,
        }
        return record, blob


def _canonical_row_bytes(row: Any) -> bytes:
    """单行 NDJSON：与工件同款 canonical JSON，行尾换行。"""
    text = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (text + "\n").encode("utf-8")


def _write_shard(directory: Path, record: dict[str, Any], blob: bytes) -> None:
    path = directory / _shard_name(int(record["index"]))
    with path.open("wb") as handle:
        handle.write(blob)
        handle.flush()
        os.fsync(handle.fileno())


def _atomic_publish(path: Path, data: bytes) -> None:
    """不覆盖的原子发布：临时文件 → fsync → `os.link`（目标已存在即失败）。"""
    temporary = path.with_name(path.name + ".publishing")
    if temporary.exists():
        temporary.unlink()
    with temporary.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()


def immutable_input_check(
    repo_root: Path, entries: list[dict[str, Any]], *, label: str
) -> None:
    """§2.2 不可变输入：打开任何源文件前重算 SHA-256 并与 inventory 比对。

    不一致、缺失一律硬错误（新增文件由 S1 的枚举断言负责）。
    """
    problems: list[str] = []
    for entry in entries:
        path = Path(repo_root) / entry["path"]
        if not path.exists():
            problems.append(f"缺失：{entry['path']}")
            continue
        digest = sha256_file(path)
        if digest != entry["sha256"]:
            problems.append(
                f"字节改变：{entry['path']} 实测 {digest}，清单 {entry['sha256']}"
            )
    if problems:
        raise DistDataError(
            f"{label}：不可变输入核对失败（{len(problems)} 项）\n  " + "\n  ".join(problems)
        )
