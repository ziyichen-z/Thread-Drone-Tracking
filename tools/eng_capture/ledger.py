"""P1-ENG-CAPTURE-001 CAPTURE:A:1 资源账（C1返工 C1-5：逐帧共账与启动门；终局裁定 AR1-6、信封落实）。

账本 `docs/evidence/P1-ENG-CAPTURE-001-ledger.json` 是阶段 A 耗用的唯一记账处：
* **启动门**（`check_launch`）：先整体校验（必需字段齐全、计数/金额为非负整数、无 UNKNOWN、各计数 = 其事件金额之和、
  零维度恒 0、无未结算 in_flight 事件、已开始候选数不超上限），再核候选归属（只有已开始且有返工归因的**当前**候选可消耗；
  旧候选或未开始候选一律拒绝，不换号规避），再逐维核余额；任一不满足 → `LedgerRefused`，不推余额。
* **逐帧共账**（`InflightCounter`）：一个阶段先落一条 in_flight 事件；每帧在交给模型**之前**原子落盘 +1（崩溃不丢已提交帧、
  失败不返还），越过每候选/整批上限的那一帧在推理前拒绝；阶段正常结束才结算。异常退出留下的 in_flight 由 `settle_inflight`
  记录原因后结算（耗用照计，可追溯），未结算前启动门拒绝。
* 记一笔（`record`）也先过同一校验与上限核对，再原子写入。

命令行（零模型）：`python -m tools.eng_capture.ledger check|record|start-candidate|settle …`。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER = REPO_ROOT / "docs" / "evidence" / "P1-ENG-CAPTURE-001-ledger.json"

COUNTERS: tuple[str, ...] = (
    "board",
    "candidates_started",
    "cloud_gpu",
    "download_install",
    "focused_real_weight_loads",
    "mini_new_disk_bytes",
    "replay_inference_frames",
    "replay_yolo_loads",
    "run_id",
    "scenario_id",
    "session_id",
    "stop_suite_real_yolo_constructions",
    "stop_suite_runs",
    "unity_play",
    "vlm_api",
)
ENVELOPE_FIELDS: tuple[str, ...] = (
    "board",
    "candidates",
    "cloud_gpu",
    "download_install",
    "fault_injection_inference_frames",
    "focused_real_weight_loads_total",
    "mini_new_disk_bytes_total",
    "replay_inference_frames_per_candidate",
    "replay_inference_frames_total",
    "replay_wall_minutes_per_run",
    "replay_yolo_loads_per_candidate",
    "replay_yolo_loads_total",
    "run_id",
    "scenario_id",
    "session_id",
    "stop_suite_real_yolo_constructions_per_run",
    "stop_suite_real_yolo_constructions_total",
    "stop_suite_runs_per_candidate",
    "stop_suite_runs_total",
    "stop_suite_wall_minutes_per_run",
    "unity_play",
    "vlm_api",
)
#: 已签为 0 的维度：计数与信封都必须恒为 0（缺项视为 0，任何非 0 即拒绝）。
ZERO_DIMENSIONS: tuple[str, ...] = ("board", "cloud_gpu", "download_install", "run_id", "scenario_id", "session_id", "unity_play", "vlm_api")
#: 计数 → (每候选上限字段 | None, 整批上限字段)。
CAPS: dict[str, tuple[str | None, str]] = {
    "replay_yolo_loads": ("replay_yolo_loads_per_candidate", "replay_yolo_loads_total"),
    "replay_inference_frames": ("replay_inference_frames_per_candidate", "replay_inference_frames_total"),
    "stop_suite_runs": ("stop_suite_runs_per_candidate", "stop_suite_runs_total"),
    # 每候选仅一次全套，故每次全套的构造上限即每候选上限。
    "stop_suite_real_yolo_constructions": ("stop_suite_real_yolo_constructions_per_run", "stop_suite_real_yolo_constructions_total"),
    "focused_real_weight_loads": (None, "focused_real_weight_loads_total"),
    "mini_new_disk_bytes": (None, "mini_new_disk_bytes_total"),
    "candidates_started": (None, "candidates"),
}
IN_FLIGHT = "in_flight"


class LedgerRefused(RuntimeError):
    """账缺失/损坏/UNKNOWN/不一致、候选归属不合法或任一维将越界：拒绝（S-A-BUDGET），不推余额。"""


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def read(path: Path = LEDGER) -> dict[str, Any]:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exception:
        raise LedgerRefused(f"S-A-BUDGET: ledger unreadable ({exception})") from exception
    if not isinstance(document, dict):
        raise LedgerRefused("S-A-BUDGET: ledger is not an object")
    return document


def problems(ledger: Mapping[str, Any], *, allow_in_flight: bool = False) -> list[str]:
    """整体校验（不推余额）：返回问题清单，空 = 可用。"""
    found: list[str] = []
    counters, envelope, events = ledger.get("counters"), ledger.get("envelope"), ledger.get("events")
    if not isinstance(counters, Mapping) or not isinstance(envelope, Mapping) or not isinstance(events, list):
        return ["counters/envelope/events missing or wrong type"]
    for name in COUNTERS:
        if name not in counters:
            found.append(f"counter {name} missing")
        elif not _count(counters[name]):
            found.append(f"counter {name}={counters[name]!r} is not a non-negative integer (UNKNOWN does not yield a balance)")
    for name in sorted(set(counters) - set(COUNTERS)):
        found.append(f"counter {name} outside the closed set")
    for name in ENVELOPE_FIELDS:
        if name not in envelope:
            found.append(f"envelope field {name} missing")
        elif not _count(envelope[name]):
            found.append(f"envelope field {name}={envelope[name]!r} is not a non-negative integer")
    sums: dict[str, int] = {name: 0 for name in COUNTERS}
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            found.append(f"event #{index} is not an object")
            continue
        counter, amount = event.get("counter"), event.get("amount")
        if counter not in sums:
            found.append(f"event #{index} counter {counter!r} outside the closed set")
            continue
        if not _count(amount):
            found.append(f"event #{index} amount {amount!r} is not a non-negative integer (UNKNOWN)")
            continue
        if not _count(event.get("candidate")):
            found.append(f"event #{index} has no candidate attribution")
        if event.get("status") == IN_FLIGHT and not allow_in_flight:
            found.append(f"event #{index} ({counter}) is an unsettled in_flight stage")
        sums[counter] += amount
    for name in COUNTERS:
        if name in counters and _count(counters[name]) and counters[name] != sums[name]:
            found.append(f"counter {name}={counters[name]} differs from its events' sum {sums[name]}")
    for name in ZERO_DIMENSIONS:
        if counters.get(name) not in (0, None) or envelope.get(name) not in (0, None):
            found.append(f"zero dimension {name} is not 0")
    if _count(counters.get("candidates_started")) and _count(envelope.get("candidates")) and counters["candidates_started"] > envelope["candidates"]:
        found.append("candidates_started exceeds the envelope")
    return found


def validate(ledger: Mapping[str, Any], *, allow_in_flight: bool = False) -> None:
    found = problems(ledger, allow_in_flight=allow_in_flight)
    if found:
        raise LedgerRefused("S-A-BUDGET: ledger refused: " + "; ".join(found))


def candidate_used(ledger: Mapping[str, Any], counter: str, candidate: int) -> int:
    return sum(int(e["amount"]) for e in ledger["events"] if e.get("counter") == counter and e.get("candidate") == candidate)


def check_candidate(ledger: Mapping[str, Any], candidate: Any) -> int:
    """只有已开始（有返工归因事件）且是当前那一个的候选可消耗；超上限、未开始或旧候选一律拒绝。"""
    if not _count(candidate) or candidate < 1:
        raise LedgerRefused(f"S-A-BUDGET: candidate {candidate!r} is not a positive integer")
    cap = ledger["envelope"]["candidates"]
    started = ledger["counters"]["candidates_started"]
    if candidate > cap:
        raise LedgerRefused(f"S-A-BUDGET: candidate {candidate} exceeds the envelope ({cap})")
    if candidate != started:
        raise LedgerRefused(f"S-A-BUDGET: candidate {candidate} is not the current attributed candidate ({started}); "
                            "start a real rework candidate with its attribution first, older candidates do not consume")
    if not any(e.get("counter") == "candidates_started" and e.get("candidate") == candidate for e in ledger["events"]):
        raise LedgerRefused(f"S-A-BUDGET: candidate {candidate} has no start/attribution event")
    return candidate


def remaining(ledger: Mapping[str, Any], counter: str, candidate: int) -> dict[str, int | None]:
    per_field, total_field = CAPS[counter]
    envelope, counters = ledger["envelope"], ledger["counters"]
    out: dict[str, int | None] = {"total": envelope[total_field] - counters[counter], "candidate": None}
    if per_field is not None:
        out["candidate"] = envelope[per_field] - candidate_used(ledger, counter, candidate)
    return out


def check_launch(ledger: Mapping[str, Any], candidate: int, needs: Mapping[str, int]) -> dict[str, bool]:
    """启动门：整体校验 → 候选归属 → 逐维余额（`needs` = 本次启动将耗用的各维数量；磁盘可报 0 表示「仍有余量」）。"""
    validate(ledger)
    check_candidate(ledger, candidate)
    checks: dict[str, bool] = {}
    for counter, amount in needs.items():
        if counter not in CAPS or not _count(amount):
            raise LedgerRefused(f"S-A-BUDGET: need {counter}={amount!r} is not a known counter/non-negative integer")
        left = remaining(ledger, counter, candidate)
        if counter == "mini_new_disk_bytes" and amount == 0:
            checks["disk"] = left["total"] > 0
            continue
        checks[f"{counter}_total"] = amount <= left["total"]
        if left["candidate"] is not None:
            checks[f"{counter}_candidate"] = amount <= left["candidate"]
    if not all(checks.values()):
        raise LedgerRefused(f"S-A-BUDGET: {checks}")
    return checks


def write(path: Path, ledger: Mapping[str, Any]) -> None:
    """原子写（同目录临时文件 + `os.replace`）：任何时刻磁盘上只有完整的旧版或新版。"""
    path = Path(path)
    text = json.dumps(ledger, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    handle, temporary = tempfile.mkstemp(prefix=".ledger-", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def record(path: Path, counter: str, amount: int, candidate: int, note: str, **extra: Any) -> dict[str, Any]:
    """记一笔（先校验与上限核对再写；尝试即记、失败不返还由调用方在尝试之前调用来保证）。"""
    ledger = read(path)
    validate(ledger, allow_in_flight=True)
    if counter != "candidates_started":
        check_candidate(ledger, candidate)
    if counter not in CAPS and counter not in ZERO_DIMENSIONS:
        raise LedgerRefused(f"S-A-BUDGET: unknown counter {counter!r}")
    if counter in ZERO_DIMENSIONS and amount:
        raise LedgerRefused(f"S-A-BUDGET: {counter} is a signed-zero dimension")
    if counter in CAPS:
        left = remaining(ledger, counter, candidate)
        if amount > left["total"] or (left["candidate"] is not None and amount > left["candidate"]):
            raise LedgerRefused(f"S-A-BUDGET: recording {counter}+{amount} would exceed the envelope ({left})")
    event = {"at": _now(), "counter": counter, "amount": int(amount), "candidate": int(candidate),
             "balance_checked_before_start": True, "note": note, **extra}
    ledger["events"].append(event)
    ledger["counters"][counter] = int(ledger["counters"][counter]) + int(amount)
    write(path, ledger)
    return event


def start_candidate(path: Path, candidate: int, attribution: str) -> dict[str, Any]:
    """开始一个返工候选：编号必须恰为当前 +1、不超上限，并写明真实返工 diff 的归因（不换号规避共账）。"""
    ledger = read(path)
    validate(ledger)
    started = ledger["counters"]["candidates_started"]
    if candidate != started + 1 or candidate > ledger["envelope"]["candidates"]:
        raise LedgerRefused(f"S-A-BUDGET: next candidate must be {started + 1} (≤ {ledger['envelope']['candidates']}), got {candidate}")
    if not attribution.strip():
        raise LedgerRefused("S-A-BUDGET: a rework candidate needs its attribution")
    return record(path, "candidates_started", 1, candidate, attribution)


class InflightCounter:
    """逐帧共账：`open` 落一条 in_flight 事件；`add` 在每帧推理之前原子落盘 +n（越上限先拒绝）；`settle` 结算。"""

    def __init__(self, path: Path, counter: str, candidate: int, index: int):
        self.path, self.counter, self.candidate, self.index = Path(path), counter, candidate, index

    @classmethod
    def open(cls, path: Path, counter: str, *, candidate: int, note: str) -> "InflightCounter":
        ledger = read(path)
        validate(ledger)
        check_candidate(ledger, candidate)
        if counter not in CAPS:
            raise LedgerRefused(f"S-A-BUDGET: unknown counter {counter!r}")
        ledger["events"].append({"at": _now(), "counter": counter, "amount": 0, "candidate": int(candidate),
                                 "balance_checked_before_start": True, "status": IN_FLIGHT, "note": note})
        write(path, ledger)
        return cls(path, counter, candidate, len(ledger["events"]) - 1)

    def add(self, amount: int = 1) -> int:
        ledger = read(self.path)
        validate(ledger, allow_in_flight=True)
        event = ledger["events"][self.index]
        if event.get("status") != IN_FLIGHT or event.get("counter") != self.counter:
            raise LedgerRefused("S-A-BUDGET: in_flight stage event is missing or already settled")
        left = remaining(ledger, self.counter, self.candidate)
        if amount > left["total"] or (left["candidate"] is not None and amount > left["candidate"]):
            raise LedgerRefused(f"S-A-BUDGET: {self.counter}+{amount} would exceed the envelope ({left}); stopped before inference")
        event["amount"] = int(event["amount"]) + int(amount)
        event["last_at"] = _now()
        ledger["counters"][self.counter] = int(ledger["counters"][self.counter]) + int(amount)
        write(self.path, ledger)
        return int(event["amount"])

    def settle(self, note: str | None = None) -> int:
        ledger = read(self.path)
        event = ledger["events"][self.index]
        event["status"] = "settled"
        event["settled_at"] = _now()
        if note:
            event["settle_note"] = note
        write(self.path, ledger)
        return int(event["amount"])


def settle_inflight(path: Path, *, reason: str) -> list[int]:
    """把异常退出遗留的 in_flight 事件结算（耗用照计、不返还），记录原因；返回被结算的事件下标。"""
    ledger = read(path)
    settled = []
    for index, event in enumerate(ledger.get("events", [])):
        if isinstance(event, dict) and event.get("status") == IN_FLIGHT:
            event["status"] = "settled_after_interruption"
            event["settled_at"] = _now()
            event["settle_note"] = reason
            settled.append(index)
    write(path, ledger)
    return settled


def _needs(items: Sequence[str]) -> dict[str, int]:
    out = {}
    for item in items:
        name, _, value = item.partition("=")
        out[name] = int(value)
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-CAPTURE-001 CAPTURE:A:1 资源账（零模型）")
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="启动门：整体校验 + 候选归属 + 逐维余额")
    check.add_argument("--candidate", type=int, required=True)
    check.add_argument("--need", action="append", default=[], help="counter=amount（可多次）")
    rec = sub.add_parser("record", help="先核后记一笔")
    rec.add_argument("--counter", required=True)
    rec.add_argument("--amount", type=int, required=True)
    rec.add_argument("--candidate", type=int, required=True)
    rec.add_argument("--note", required=True)
    rec.add_argument("--cmd", default=None)
    rec.add_argument("--env", default=None)
    start = sub.add_parser("start-candidate", help="开始一个返工候选（须写归因）")
    start.add_argument("--candidate", type=int, required=True)
    start.add_argument("--attribution", required=True)
    settle = sub.add_parser("settle", help="结算异常退出遗留的 in_flight 事件（耗用照计）")
    settle.add_argument("--reason", required=True)
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "check":
            ledger = read(arguments.ledger)
            result: Any = check_launch(ledger, arguments.candidate, _needs(arguments.need))
            result = {"checks": result, "remaining": {c: remaining(ledger, c, arguments.candidate) for c in _needs(arguments.need)}}
        elif arguments.command == "record":
            extra = {k: v for k, v in (("cmd", arguments.cmd), ("env", arguments.env)) if v}
            result = record(arguments.ledger, arguments.counter, arguments.amount, arguments.candidate, arguments.note, **extra)
        elif arguments.command == "start-candidate":
            result = start_candidate(arguments.ledger, arguments.candidate, arguments.attribution)
        else:
            result = settle_inflight(arguments.ledger, reason=arguments.reason)
    except LedgerRefused as refusal:
        print(f"LEDGER_REFUSED: {refusal}", file=sys.stderr)
        return 4
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
