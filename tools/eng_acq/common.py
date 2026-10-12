"""公共件：路径、受保护写入（AC-9）、规范 JSON、消耗账本与信封守卫（账本 09-28 §5 阶段 1+2 信封）。

信封（`docs/authorizations.md`「2026-09-28 P1-ENG-ACQ-001 — 用户签发 §5 阶段 1+2 执行信封…」，经 2026-09-29「用户批准
实现角色追加申请 SUB:1 … 与 SUB:2 …」修订）：CPU 序列回放 ≤ 40 次（+ E1 解析）；第二级 NanoTrack：a7 全样本，其他序列每
（序列 × gmc_source × 臂）≤ 600 个 (k, o)；每 (k, o) scout-1 ≤ 87 帧、a7 与 m3-armA ≤ 66 帧（同日 SUB:3 再修订）；
本机全部 CPU 工作墙钟 ≤ 3 h，与回放次数上限先到者即停；成功、失败、重试全部计入同一上限。
其余维度（ID/Play/API/VLM/GPU/检测推理/YOLO 权重加载/下载/pip/远端访问）= 0。
"""

from __future__ import annotations

import contextlib
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any, Iterator, Mapping

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_acq import WORK_ID  # noqa: E402

DATA_ROOT = Path(os.environ.get("ENG_DET_DATA_ROOT", str(Path.home() / "TetheredDroneTracking-full"))).resolve()
OUT_DIR = PROJECT_ROOT / "outputs" / "eng-acq" / WORK_ID
EVIDENCE_DIR = PROJECT_ROOT / "docs" / "evidence"
LEDGER_PATH = EVIDENCE_DIR / f"{WORK_ID}-ledger.json"
PROTECTED_ROOTS: tuple[Path, ...] = (PROJECT_ROOT / "runtime", DATA_ROOT)

ENVELOPE: dict[str, Any] = {
    "source": "docs/authorizations.md「2026-09-28 P1-ENG-ACQ-001 — 用户签发 §5 阶段 1+2 执行信封（序列回放 ≤40、本机 CPU 墙钟 ≤3 h）并答复 §7 (g)(h)(i)（supervisor 会话代录）」",
    "sequence_replays_max": 40,
    "cpu_wall_s_max": 3 * 3600,
    "revised_by": [
        "docs/authorizations.md「2026-09-29 P1-ENG-ACQ-001 — 用户批准实现角色追加申请 SUB:1（a7 第二级全样本）与 SUB:2（每 (k,o) SOT 帧上限 ≤66），修订 §5 阶段 1+2 执行信封（supervisor 会话代录）」；提案决策记录「信封修订 SUB:1/SUB:2 落实（2026-09-29；CLARIFY）」",
        "docs/authorizations.md「2026-09-29 P1-ENG-ACQ-001 — 用户批准实现角色追加申请 SUB:3（scout-1 第二级每 (k,o) SOT 帧上限 ≤87），修订 §5 阶段 1+2 执行信封（supervisor 会话代录）」；提案决策记录「信封修订 SUB:3 落实（2026-09-29；CLARIFY）」",
    ],
    "level2_k_o_per_combo_max": 600,
    "level2_full_sample_sequences": ["a7"],
    "level2_frames_per_k_o_max": 66,
    "level2_frames_per_k_o_max_by_sequence": {"scout-1": 87},
    "superseded_values": {"level2_k_o_per_combo_max_a7": 600, "level2_frames_per_k_o_max": 65, "level2_frames_per_k_o_max_scout-1": 66},
    "zero_dimensions": [
        "scenario_session_run_ids",
        "unity_play",
        "api_vlm_queries",
        "training_gpu_h",
        "detection_inference",
        "yolo_weight_loads",
        "downloads",
        "pip_installs",
        "remote_access_5060_or_other",
    ],
    "local_writes": ["outputs/eng-acq/", "docs/evidence/", "code and tests"],
}


class EnvelopeExhausted(RuntimeError):
    """信封余额不足：立即停下（不自行追加；SUB 不启用）。"""


def evidence(name: str) -> Path:
    return EVIDENCE_DIR / f"{WORK_ID}-{name}"


def rel(path: Path | str) -> str:
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        try:
            return "~/" + candidate.resolve().relative_to(Path.home()).as_posix()
        except ValueError:
            return candidate.as_posix()


def data_path(relative: str | Path) -> Path:
    candidate = Path(relative)
    return candidate if candidate.is_absolute() else DATA_ROOT / candidate


def refuse_protected(path: Path | str, roots: tuple[Path, ...] | None = None) -> None:
    """AC-9：数据根与 `runtime/` 只读（结构性拒绝写入，不靠事后比对）。"""
    target = Path(path)
    resolved = target.resolve() if target.exists() else target.parent.resolve() / target.name
    for root in roots if roots is not None else PROTECTED_ROOTS:
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            continue
        raise PermissionError(f"只读根（AC-9）：拒绝写入 {path}")


def json_bytes(value: Any) -> bytes:
    """规范 JSON（键排序、缩进 1、UTF-8、无 NaN），用于字节一致性复现核对。"""
    return (json.dumps(value, sort_keys=True, indent=1, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def atomic_write_bytes(path: Path | str, payload: bytes, roots: tuple[Path, ...] | None = None) -> str:
    target = Path(path)
    refuse_protected(target, roots)
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
        os.replace(temporary, target)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary)
        raise
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path | str, value: Any) -> str:
    return atomic_write_bytes(path, json_bytes(value))


def read_json(path: Path | str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- 消耗账本 ---------------------------------------------------------------


def load_ledger(path: Path = LEDGER_PATH) -> dict[str, Any]:
    if path.exists():
        return read_json(path)
    return {"work_id": WORK_ID, "envelope": ENVELOPE, "entries": [], "totals": {}}


def totals(ledger: Mapping[str, Any]) -> dict[str, Any]:
    entries = ledger.get("entries", [])
    result: dict[str, Any] = {
        "sequence_replays": sum(int(e.get("sequence_replays", 0)) for e in entries),
        "cpu_wall_s": round(sum(float(e.get("wall_s", 0.0)) for e in entries), 3),
        "level2_sot_runs": sum(int(e.get("level2_sot_runs", 0)) for e in entries),
        "level2_sot_frames": sum(int(e.get("level2_sot_frames", 0)) for e in entries),
        "failed_entries": sum(1 for e in entries if e.get("status") != "ok"),
    }
    for dimension in ENVELOPE["zero_dimensions"]:
        result[dimension] = sum(int(e.get("zero_dimensions", {}).get(dimension, 0)) for e in entries)
    result["sequence_replays_remaining"] = ENVELOPE["sequence_replays_max"] - result["sequence_replays"]
    result["cpu_wall_s_remaining"] = round(ENVELOPE["cpu_wall_s_max"] - result["cpu_wall_s"], 3)
    return result


def append_entry(entry: Mapping[str, Any], path: Path = LEDGER_PATH) -> dict[str, Any]:
    ledger = load_ledger(path)
    record = dict(entry)
    record["index"] = len(ledger["entries"]) + 1
    record.setdefault("zero_dimensions", {dimension: 0 for dimension in ENVELOPE["zero_dimensions"]})
    ledger["entries"].append(record)
    ledger["envelope"] = ENVELOPE
    ledger["totals"] = totals(ledger)
    write_json(path, ledger)
    return ledger


def require_budget(planned_replays: int, path: Path = LEDGER_PATH) -> dict[str, Any]:
    """开工前守卫：已用 + 计划回放 ≤ 40，且墙钟尚有余额；否则 `EnvelopeExhausted`（先到者即停）。"""
    current = totals(load_ledger(path))
    if current["sequence_replays"] + planned_replays > ENVELOPE["sequence_replays_max"]:
        raise EnvelopeExhausted(
            f"sequence replays {current['sequence_replays']} + planned {planned_replays} > {ENVELOPE['sequence_replays_max']}"
        )
    if current["cpu_wall_s"] >= ENVELOPE["cpu_wall_s_max"]:
        raise EnvelopeExhausted(f"CPU wall {current['cpu_wall_s']} s ≥ {ENVELOPE['cpu_wall_s_max']} s")
    return current


class WallGuard:
    """运行中守卫：本进程墙钟 + 账本已用墙钟 ≥ 上限即抛 `EnvelopeExhausted`（先到者即停）。"""

    def __init__(self, path: Path = LEDGER_PATH):
        self.used_before = totals(load_ledger(path))["cpu_wall_s"]
        self.started = time.monotonic()

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started

    def check(self) -> None:
        if self.used_before + self.elapsed >= ENVELOPE["cpu_wall_s_max"]:
            raise EnvelopeExhausted(f"CPU wall budget exhausted after {self.elapsed:.1f} s in this process")


@contextlib.contextmanager
def charged(kind: str, label: str, *, sequence_replays: int, cmd: str, path: Path = LEDGER_PATH) -> Iterator[dict[str, Any]]:
    """一次本机 CPU 工作的记账包装：成功、失败都记（墙钟 = 本进程该段 monotonic 耗时）。"""
    require_budget(sequence_replays, path)
    extra: dict[str, Any] = {}
    started_utc = utc_now()
    started = time.monotonic()
    status = "ok"
    try:
        yield extra
    except BaseException as error:  # noqa: BLE001
        status = f"failed:{type(error).__name__}"
        raise
    finally:
        entry = {
            "kind": kind,
            "label": label,
            "cmd": cmd,
            "started_utc": started_utc,
            "ended_utc": utc_now(),
            "wall_s": round(time.monotonic() - started, 3),
            "sequence_replays": sequence_replays,
            "status": status,
        }
        entry.update(extra)
        append_entry(entry, path)
