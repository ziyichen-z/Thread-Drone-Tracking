"""P1-ENG-FASTFIX-001 §5.0 / AC-19：粗粒度阶段账本（不复用 `tools/eng_capture/ledger.py`，故 CAPTURE R1-4 不触发）。

一个阶段一份 JSON 账本：`envelope` 只列用户签发的少数总量维度（未列维度 = 0），`used` 为已耗量。规则：
- 每步启动前按剩余量拦截（`check_launch`）：余额不足即拒；申请未列维度即拒（缺项为 0）。
- 尝试即记、失败不返还（`record` 先核后记、原子写）；成功/失败/重试同账。
- 计量缺失或账本损坏 → UNKNOWN → 一切启动拒绝并停报（`LedgerUnknown`），不推余额。
- 全维校验：任一已耗量 > 其上限（含手改账本）→ 账本视为越界，启动拒绝（承接 CAPTURE R1-4 的教训，本账本自带）。
- 墙钟维 `wall_s` 按执行区间并集累计（重叠只计一次）；磁盘维 `disk_peak_bytes` 记峰值（取最大，不累加）。
本模块不导入 `controller`、不读真值。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any, Mapping, Sequence

SCHEMA = "p1-eng-fastfix-001-ledger/v1"
UNKNOWN = "UNKNOWN"
#: 计量方式：sum = 累加；union_s = 执行区间并集（秒）；peak = 取最大。
DIMENSION_KINDS: dict[str, str] = {
    "candidates": "sum",
    "yolo_loads": "sum",
    "wall_s": "union_s",
    "disk_peak_bytes": "peak",
    "git_new_bytes": "sum",
    "tx_bytes": "sum",
    "tx_count": "sum",
    "unity_play": "sum",
    "play_wall_s": "union_s",
    "session_ids": "sum",
    "run_ids": "sum",
    "scenario_ids": "sum",
}


class LedgerRefused(RuntimeError):
    """启动前拦截（S-BUDGET）：余额不足、未列维度或已越界。"""


class LedgerUnknown(LedgerRefused):
    """S-UNKNOWN：账本缺失/损坏/计量不可得；一切后续消耗拒绝。"""


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _body_sha(document: Mapping[str, Any]) -> str:
    body = {k: v for k, v in document.items() if k != "ledger_sha256"}
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()


def _write(path: Path, document: dict[str, Any]) -> None:
    document = dict(document)
    document["ledger_sha256"] = _body_sha(document)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".ledger-", suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    os.replace(temporary, path)


def create(path: Path, *, stage: str, envelope: Mapping[str, float], authorization: str) -> dict[str, Any]:
    """新建阶段账本；`envelope` 维度须在已知闭集内且为非负有限数（未列维度 = 0）。已存在即拒（不覆盖旧账）。"""
    if Path(path).exists():
        raise LedgerRefused(f"ledger {path} already exists; not overwritten")
    for dim, limit in envelope.items():
        if dim not in DIMENSION_KINDS:
            raise LedgerRefused(f"unknown ledger dimension {dim!r}")
        if isinstance(limit, bool) or not isinstance(limit, (int, float)) or not math.isfinite(float(limit)) or limit < 0:
            raise LedgerRefused(f"envelope {dim} must be a non-negative finite number")
    document = {
        "schema_version": SCHEMA,
        "stage": stage,
        "authorization": authorization,
        "envelope": dict(envelope),
        "used": {dim: 0 for dim in envelope},
        "intervals": {dim: [] for dim, kind in DIMENSION_KINDS.items() if kind == "union_s" and dim in envelope},
        "entries": [],
    }
    _write(Path(path), document)
    return read(path)


CARRIED_DIMS = ("candidates", "yolo_loads", "wall_s")


def create_continuation(path: Path, *, source: Path, authorization: str, disk_limit: float,
                        initial_disk_u: float, source_note: str) -> dict[str, Any]:
    """续做后继账本（「续做信封落实」§5）：只读校验来源账本（校验和不符/缺失 → UNKNOWN 拒建），完整承接
    `CARRIED_DIMS` 的上限、已用量、全部原 wall_s 区间与来源 entries（原样，含估计标签）；`disk_peak_bytes`
    改为独立续做维（上限 = 用户新签 `disk_limit`，初值 = 建账时已发生的整窗累计 `initial_disk_u`，不补 0），
    来源同名维的 UNKNOWN 只放在 `source` 元数据（历史偏差），不进 `used`。来源文件字节不变；已存在即拒。"""
    if Path(path).exists():
        raise LedgerRefused(f"ledger {path} already exists; not overwritten")
    raw = Path(source).read_bytes()
    origin = read(source)
    for dim in CARRIED_DIMS:
        if dim not in origin["envelope"] or origin["used"].get(dim) == UNKNOWN:
            raise LedgerUnknown(f"S-UNKNOWN: carried dimension {dim} missing or UNKNOWN in source")
    carried_wall = origin["intervals"].get("wall_s", [])
    if abs(_union_length(carried_wall) - float(origin["used"]["wall_s"])) > 1e-3:
        raise LedgerUnknown("S-UNKNOWN: source wall_s intervals do not reproduce used.wall_s")
    for value in (disk_limit, initial_disk_u):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
            raise LedgerRefused("continuation disk values must be non-negative finite numbers")
    document = {
        "schema_version": SCHEMA,
        "stage": f"{origin['stage']}-continuation",
        "authorization": authorization,
        "envelope": {**{dim: origin["envelope"][dim] for dim in CARRIED_DIMS}, "disk_peak_bytes": disk_limit},
        "used": {**{dim: origin["used"][dim] for dim in CARRIED_DIMS}, "disk_peak_bytes": initial_disk_u},
        "intervals": {"wall_s": [list(map(float, pair)) for pair in carried_wall]},
        "entries": [],
        "source": {
            "path": str(source),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "ledger_sha256": origin["ledger_sha256"],
            "used": origin["used"],
            "envelope": origin["envelope"],
            "carried_entries": [entry for entry in origin["entries"] if entry.get("dim") in CARRIED_DIMS],
            "note": source_note,
        },
    }
    _write(Path(path), document)
    if Path(source).read_bytes() != raw:
        raise LedgerUnknown("S-UNKNOWN: source ledger bytes changed during carry-over")
    return read(path)


def check_disk_window(document: Mapping[str, Any], current_u: float | None, step_need: float, reserve: float,
                      stop_fraction: float = 0.9) -> float:
    """续做磁盘维的启动核对（`check_launch` 之外）：当前整窗累计 U 不可得 → UNKNOWN；
    `current_u + step_need + reserve` 达停止线（上限 × stop_fraction）即拒（S-DISK）。返回停止线前余量。"""
    issues = problems(document)
    if any("UNKNOWN" in issue for issue in issues):
        raise LedgerUnknown("S-UNKNOWN: " + "; ".join(issues))
    if current_u is None or isinstance(current_u, bool) or not math.isfinite(float(current_u)) or current_u < 0:
        raise LedgerUnknown("S-UNKNOWN: current window U(t) unavailable")
    limit = float((document.get("envelope") or {}).get("disk_peak_bytes", 0))
    stop_line = limit * stop_fraction
    if float(current_u) < float(document["used"]["disk_peak_bytes"]) - 1e-6:
        raise LedgerUnknown("S-UNKNOWN: current U(t) below recorded cumulative peak (counter regressed?)")
    if float(current_u) + float(step_need) + float(reserve) >= stop_line:
        raise LedgerRefused(f"S-DISK: U {current_u} + need {step_need} + reserve {reserve} >= stop line {stop_line}")
    return stop_line - float(current_u)


def read(path: Path) -> dict[str, Any]:
    """读并校验：缺失、非 JSON、schema 不符、sha 不符 → `LedgerUnknown`（损坏 = UNKNOWN，不推余额）。"""
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LedgerUnknown(f"S-UNKNOWN: ledger unreadable ({error})") from error
    if not isinstance(document, dict) or document.get("schema_version") != SCHEMA:
        raise LedgerUnknown("S-UNKNOWN: ledger schema invalid")
    if document.get("ledger_sha256") != _body_sha(document):
        raise LedgerUnknown("S-UNKNOWN: ledger checksum mismatch (corrupted or hand-edited)")
    return document


def problems(document: Mapping[str, Any]) -> list[str]:
    """全维校验：每个已耗维度在信封内、数值合法、≤ 上限；任一 UNKNOWN 记为问题（UNKNOWN 一律停报）。"""
    found: list[str] = []
    envelope = document.get("envelope") or {}
    for dim, value in (document.get("used") or {}).items():
        if dim not in envelope:
            found.append(f"{dim}: used but not in envelope (unlisted = 0)")
            continue
        if value == UNKNOWN:
            found.append(f"{dim}: UNKNOWN")
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
            found.append(f"{dim}: invalid amount {value!r}")
            continue
        if float(value) > float(envelope[dim]) + 1e-9:
            found.append(f"{dim}: used {value} exceeds limit {envelope[dim]}")
    return found


def remaining(document: Mapping[str, Any], dim: str) -> float:
    envelope = document.get("envelope") or {}
    if dim not in envelope:
        return 0.0
    used = (document.get("used") or {}).get(dim, 0)
    if used == UNKNOWN:
        raise LedgerUnknown(f"S-UNKNOWN: {dim} is UNKNOWN")
    return float(envelope[dim]) - float(used)


def check_launch(document: Mapping[str, Any], needs: Mapping[str, float]) -> dict[str, float]:
    """每步启动前拦截：账本任一问题（越界/UNKNOWN）→ 拒；申请未列维度 → 拒；余额 < 申请量 → 拒（S-BUDGET）。"""
    issues = problems(document)
    if any("UNKNOWN" in issue for issue in issues):
        raise LedgerUnknown("S-UNKNOWN: " + "; ".join(issues))
    if issues:
        raise LedgerRefused("S-BUDGET: ledger already out of bounds: " + "; ".join(issues))
    balances: dict[str, float] = {}
    for dim, amount in needs.items():
        if dim not in (document.get("envelope") or {}):
            raise LedgerRefused(f"S-BUDGET: {dim} is not in the signed envelope (unlisted dimensions are 0)")
        balance = remaining(document, dim)
        if DIMENSION_KINDS.get(dim) == "peak":
            if float(amount) > float(document["envelope"][dim]) + 1e-9:
                raise LedgerRefused(f"S-BUDGET: {dim} planned peak {amount} > limit {document['envelope'][dim]}")
        elif float(amount) > balance + 1e-9:
            raise LedgerRefused(f"S-BUDGET: {dim} needs {amount}, remaining {balance}")
        balances[dim] = balance
    return balances


def _union_length(intervals: Sequence[Sequence[float]]) -> float:
    total = 0.0
    current: list[float] | None = None
    for start, end in sorted((float(a), float(b)) for a, b in intervals):
        if current is None or start > current[1]:
            if current is not None:
                total += current[1] - current[0]
            current = [start, end]
        else:
            current[1] = max(current[1], end)
    if current is not None:
        total += current[1] - current[0]
    return total


def record(path: Path, dim: str, amount: float | None = None, *, note: str, interval: Sequence[float] | None = None,
           unknown: bool = False) -> dict[str, Any]:
    """尝试即记（先核后记、原子写）：sum 维累加 `amount`；union_s 维加入执行区间 `[start_unix, end_unix]` 并按并集重算；
    peak 维取最大。`unknown=True` 把该维置 UNKNOWN（计量不可得，之后一切启动拒绝）。越上限仍落账（失败不返还）并抛
    `LedgerRefused`，供调用方停报。"""
    document = read(path)
    if dim not in document["envelope"]:
        raise LedgerRefused(f"S-BUDGET: {dim} is not in the signed envelope")
    entry: dict[str, Any] = {"at_unix_s": time.time(), "dim": dim, "note": note}
    kind = DIMENSION_KINDS[dim]
    if unknown:
        document["used"][dim] = UNKNOWN
        entry["unknown"] = True
    elif kind == "union_s":
        if interval is None or len(interval) != 2 or float(interval[1]) < float(interval[0]):
            raise LedgerRefused(f"{dim} needs a [start, end] interval")
        document["intervals"].setdefault(dim, []).append([float(interval[0]), float(interval[1])])
        if document["used"][dim] != UNKNOWN:
            document["used"][dim] = round(_union_length(document["intervals"][dim]), 3)
        entry["interval"] = [float(interval[0]), float(interval[1])]
    else:
        if amount is None or isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0:
            raise LedgerRefused(f"{dim} needs a non-negative amount")
        entry["amount"] = amount
        if document["used"][dim] != UNKNOWN:
            document["used"][dim] = max(document["used"][dim], amount) if kind == "peak" else document["used"][dim] + amount
    document["entries"].append(entry)
    _write(Path(path), {k: v for k, v in document.items() if k != "ledger_sha256"})
    issues = problems(read(path))
    if any("UNKNOWN" in issue for issue in issues):
        raise LedgerUnknown("S-UNKNOWN recorded; every further launch is refused: " + "; ".join(issues))
    if issues:
        raise LedgerRefused("recorded, but the ledger is now out of bounds: " + "; ".join(issues))
    return read(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-FASTFIX-001 粗粒度阶段账本")
    sub = parser.add_subparsers(dest="command", required=True)
    show = sub.add_parser("show")
    show.add_argument("ledger", type=Path)
    check = sub.add_parser("check")
    check.add_argument("ledger", type=Path)
    check.add_argument("--need", action="append", default=[], help="dim=amount")
    arguments = parser.parse_args(argv)
    try:
        document = read(arguments.ledger)
        if arguments.command == "check":
            needs = {item.split("=", 1)[0]: float(item.split("=", 1)[1]) for item in arguments.need}
            print(json.dumps({"ok": True, "balances": check_launch(document, needs)}, ensure_ascii=False))
            return 0
        print(json.dumps({"used": document["used"], "envelope": document["envelope"], "problems": problems(document)},
                         ensure_ascii=False))
        return 0
    except LedgerRefused as refusal:
        print(f"LEDGER_REFUSED: {refusal}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
