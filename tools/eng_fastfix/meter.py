"""P1-ENG-FASTFIX-001 §3.6（G4）：采集计量工具——停令检查与磁盘采样分离，移出会话关键时序。

独立进程（启动即 `os.nice`）；两个线程：
- **停令线程**：节拍 ≤ 0.5 s，检查操作单给出的停令条件（停令文件出现、计量墙钟到限、采样发现新增磁盘达阈值、
  输出截断）；任一满足即置停止事件、写 `stop_condition` 行与告警文件。
- **采样线程**：只遍历操作单声明的输出根（`--root 名=路径`），不全仓遍历；每次采样记 `start/end` 的 monotonic 与 unix、
  总量与根级小计、相对首个采样的新增字节；遍历中每个条目检查停止事件，任何采样进行中停令延迟 ≤ 1 s。
输出：每次采样一行 JSONL；单文件上限（缺省 1 MB），将超限时写 `meter_truncated` 并停写，同时按「计量失联」停令收尾
（截断不得变成无监控继续，S-METER/S-UNKNOWN）。停令条件的数值全部取自命令行（操作单），工具不内置合同数字。
不读文件内容（只 `lstat` 取大小）、不读真值、不导入 `controller`。
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

SCHEMA = "p1-eng-fastfix-001-meter/v1"
STOP_TICK_S = 0.5
DEFAULT_INTERVAL_S = 30.0
DEFAULT_MAX_OUTPUT_BYTES = 1_000_000
#: 截断行与停令行的预留字节（保证 `meter_truncated` 一定写得下）。
RESERVE_BYTES = 512

Walker = Callable[[Path], Iterator[int]]


class SampleAborted(RuntimeError):
    """采样进行中停止事件被置位：放弃本次采样（不写半截读数）。"""


class MeterUnknown(RuntimeError):
    """C1-4：根/条目无法核读或采样/输出故障——读数不可得即 UNKNOWN（不写成 0、不当存活计量继续）。"""


def walk_sizes(root: Path) -> Iterator[int]:
    """只读遍历一个声明根：逐个普通文件 `lstat` 大小（不跟随符号链接、不读内容）。

    根本身不存在 → 无条目（登记为缺席根，0 B 是事实而非补 0）；遍历中途消失的条目（建删竞争）→ 跳过；
    其他任何不可读（PermissionError、条目 `stat`/`is_dir` 的 OSError、目录读失败）→ `MeterUnknown`（C1-4）。"""
    root = Path(root)
    if not os.path.lexists(root):
        return
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            yield entry.stat(follow_symlinks=False).st_size
                    except FileNotFoundError:
                        continue
                    except OSError as error:
                        raise MeterUnknown(f"unreadable entry {entry.path}: {error!r}") from error
        except FileNotFoundError:
            if current == root:
                continue
            continue
        except NotADirectoryError:
            if current == root:
                try:
                    yield os.lstat(root).st_size
                except OSError as error:
                    raise MeterUnknown(f"unreadable root {root}: {error!r}") from error
            continue
        except OSError as error:
            raise MeterUnknown(f"unreadable directory {current}: {error!r}") from error


class Meter:
    def __init__(
        self,
        roots: Mapping[str, Path],
        output: Path,
        *,
        interval_s: float = DEFAULT_INTERVAL_S,
        stop_file: Path | None = None,
        alert_file: Path | None = None,
        wall_limit_s: float | None = None,
        disk_limit_bytes: int | None = None,
        disk_stop_fraction: float = 0.9,
        max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
        walker: Walker = walk_sizes,
        stop_tick_s: float = STOP_TICK_S,
        monotonic: Callable[[], float] = time.monotonic,
        unix: Callable[[], float] = time.time,
    ):
        if not roots:
            raise ValueError("at least one declared root is required")
        if stop_tick_s > STOP_TICK_S:
            raise ValueError("stop check tick must be ≤ 0.5 s")
        self.roots = {name: Path(path) for name, path in roots.items()}
        self.output = Path(output)
        self.interval_s = float(interval_s)
        self.stop_file = None if stop_file is None else Path(stop_file)
        self.alert_file = None if alert_file is None else Path(alert_file)
        self.wall_limit_s = wall_limit_s
        self.disk_limit_bytes = disk_limit_bytes
        self.disk_stop_fraction = float(disk_stop_fraction)
        self.max_output_bytes = int(max_output_bytes)
        self.walker = walker
        self.stop_tick_s = float(stop_tick_s)
        self._monotonic = monotonic
        self._unix = unix
        self.stop_event = threading.Event()
        self.stop_reason: str | None = None
        self.stop_requested_monotonic: float | None = None
        self.baseline_bytes: int | None = None
        self.peak_new_bytes = 0
        self.samples = 0
        self.truncated = False
        self._lock = threading.Lock()
        self._written = self.output.stat().st_size if self.output.exists() else 0
        self._started = self._monotonic()
        self.walked_roots: list[Path] = []
        self.unknown_detail: str | None = None
        self._sampler_thread: threading.Thread | None = None

    # --- 输出 ---------------------------------------------------------------

    def _line(self, record: Mapping[str, Any], *, reserved: bool = False) -> bool:
        text = json.dumps(dict(record), ensure_ascii=False, sort_keys=True) + "\n"
        data = text.encode("utf-8")
        with self._lock:
            if self.truncated and not reserved:
                return False
            limit = self.max_output_bytes if reserved else self.max_output_bytes - RESERVE_BYTES
            if self._written + len(data) > limit:
                if not self.truncated:
                    self.truncated = True
                    marker = (json.dumps({"kind": "meter_truncated", "at_monotonic_s": self._monotonic(),
                                          "at_unix_s": self._unix(), "written_bytes": self._written},
                                         sort_keys=True) + "\n").encode("utf-8")
                    with self.output.open("ab") as handle:
                        handle.write(marker)
                    self._written += len(marker)
                    self._request_stop("meter_truncated", from_lock=True)
                return False
            try:
                with self.output.open("ab") as handle:
                    handle.write(data)
            except OSError as error:
                # C1-4：输出写失败 → 读数未留存即 UNKNOWN（停令；告警文件另写）。
                self.unknown_detail = f"output_write_failed:{error!r}"
                self._request_stop("S-UNKNOWN", from_lock=True)
                return False
            self._written += len(data)
            return True

    def _request_stop(self, reason: str, *, from_lock: bool = False) -> None:
        if self.stop_event.is_set():
            return
        self.stop_reason = reason
        self.stop_requested_monotonic = self._monotonic()
        self.stop_event.set()
        if self.alert_file is not None:
            try:
                self.alert_file.parent.mkdir(parents=True, exist_ok=True)
                self.alert_file.write_text(json.dumps({"stop_condition": reason, "at_unix_s": self._unix()}) + "\n",
                                           encoding="utf-8")
            except OSError:
                pass

    # --- 采样 ---------------------------------------------------------------

    def sample(self) -> dict[str, Any]:
        start_m, start_u = self._monotonic(), self._unix()
        roots: dict[str, int] = {}
        files = 0
        for name, root in self.roots.items():
            self.walked_roots.append(root)
            total = 0
            for size in self.walker(root):
                if self.stop_event.is_set():
                    raise SampleAborted(name)
                total += int(size)
                files += 1
            roots[name] = total
        total_bytes = sum(roots.values())
        if self.baseline_bytes is None:
            self.baseline_bytes = total_bytes
        new_bytes = total_bytes - self.baseline_bytes
        self.peak_new_bytes = max(self.peak_new_bytes, new_bytes)
        self.samples += 1
        return {
            "kind": "sample",
            "index": self.samples,
            "start_monotonic_s": start_m,
            "start_unix_s": start_u,
            "end_monotonic_s": self._monotonic(),
            "end_unix_s": self._unix(),
            "roots": roots,
            "files": files,
            "total_bytes": total_bytes,
            "new_bytes": new_bytes,
            "peak_new_bytes": self.peak_new_bytes,
        }

    def _unknown(self, detail: str) -> None:
        """C1-4：读数不可得 → 写 `stop_condition` S-UNKNOWN（预留字节）并停令；之后不再有存活计量。"""
        self.unknown_detail = detail
        try:
            self._line({"kind": "stop_condition", "code": "S-UNKNOWN", "detail": detail,
                        "at_monotonic_s": self._monotonic(), "at_unix_s": self._unix()}, reserved=True)
        except Exception:  # noqa: BLE001 — 输出也坏时只能靠停令与告警文件
            pass
        self._request_stop("S-UNKNOWN")

    def _sampler(self) -> None:
        try:
            self._sample_loop()
        except BaseException as error:  # noqa: BLE001 — 采样线程任何异常死亡都不能静默
            self._unknown(f"sampler_failed:{type(error).__name__}:{error}")

    def _sample_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                record = self.sample()
            except SampleAborted:
                return
            except MeterUnknown as error:
                self._unknown(f"unreadable:{error}")
                return
            if not self._line(record):
                if not self.stop_event.is_set():
                    self._unknown("sample_not_written")
                return
            if (self.disk_limit_bytes is not None
                    and record["new_bytes"] >= self.disk_stop_fraction * float(self.disk_limit_bytes)):
                self._line({"kind": "stop_condition", "code": "S-DISK", "new_bytes": record["new_bytes"],
                            "limit_bytes": self.disk_limit_bytes, "fraction": self.disk_stop_fraction}, reserved=True)
                self._request_stop("S-DISK")
                return
            if self.stop_event.wait(self.interval_s):
                return

    def _stop_checker(self) -> None:
        while not self.stop_event.is_set():
            sampler = self._sampler_thread
            if sampler is not None and not sampler.is_alive() and not self.stop_event.is_set():
                # C1-4：采样线程失联（无停令而退出）→ UNKNOWN 停令，不以「停令线程仍在」冒充存活计量。
                self._unknown("sampler_thread_lost")
                return
            if self.stop_file is not None and self.stop_file.exists():
                self._request_stop("stop_file")
                return
            if self.wall_limit_s is not None and self._monotonic() - self._started >= float(self.wall_limit_s):
                self._line({"kind": "stop_condition", "code": "WALL_LIMIT", "wall_limit_s": self.wall_limit_s}, reserved=True)
                self._request_stop("WALL_LIMIT")
                return
            self.stop_event.wait(self.stop_tick_s)

    def run(self) -> dict[str, Any]:
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self._line({"kind": "start", "schema_version": SCHEMA, "roots": {k: str(v) for k, v in self.roots.items()},
                    "interval_s": self.interval_s, "stop_tick_s": self.stop_tick_s, "wall_limit_s": self.wall_limit_s,
                    "disk_limit_bytes": self.disk_limit_bytes, "disk_stop_fraction": self.disk_stop_fraction,
                    "max_output_bytes": self.max_output_bytes, "pid": os.getpid(),
                    "at_monotonic_s": self._monotonic(), "at_unix_s": self._unix()}, reserved=True)
        checker = threading.Thread(target=self._stop_checker, name="meter-stop", daemon=True)
        sampler = threading.Thread(target=self._sampler, name="meter-sample", daemon=True)
        self._sampler_thread = sampler
        sampler.start()
        checker.start()
        checker.join()
        self.stop_event.set()
        sampler.join()
        stopped = self._monotonic()
        latency = None if self.stop_requested_monotonic is None else stopped - self.stop_requested_monotonic
        summary = {"kind": "stopped", "reason": self.stop_reason, "stop_latency_s": latency, "samples": self.samples,
                   "peak_new_bytes": self.peak_new_bytes, "truncated": self.truncated, "unknown": self.unknown_detail,
                   "at_monotonic_s": stopped, "at_unix_s": self._unix()}
        self._line(summary, reserved=True)
        return summary


def parse_roots(items: Iterable[str]) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for item in items:
        name, _, path = item.partition("=")
        if not name or not path:
            raise ValueError(f"--root must be NAME=PATH, got {item!r}")
        roots[name] = Path(path)
    return roots


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-FASTFIX-001 采集计量（停令与采样分离）")
    parser.add_argument("--root", action="append", required=True, help="声明的输出根 NAME=PATH（可多次）")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--interval-s", type=float, default=DEFAULT_INTERVAL_S)
    parser.add_argument("--stop-file", type=Path, default=None)
    parser.add_argument("--alert-file", type=Path, default=None)
    parser.add_argument("--wall-limit-s", type=float, default=None)
    parser.add_argument("--disk-limit-bytes", type=int, default=None)
    parser.add_argument("--disk-stop-fraction", type=float, default=0.9)
    parser.add_argument("--max-output-bytes", type=int, default=DEFAULT_MAX_OUTPUT_BYTES)
    parser.add_argument("--nice", type=int, default=10)
    arguments = parser.parse_args(argv)
    try:
        os.nice(arguments.nice)
    except OSError:
        pass
    meter = Meter(parse_roots(arguments.root), arguments.output, interval_s=arguments.interval_s, stop_file=arguments.stop_file,
                  alert_file=arguments.alert_file, wall_limit_s=arguments.wall_limit_s, disk_limit_bytes=arguments.disk_limit_bytes,
                  disk_stop_fraction=arguments.disk_stop_fraction, max_output_bytes=arguments.max_output_bytes)
    summary = meter.run()
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["reason"] == "stop_file" else 5


if __name__ == "__main__":
    raise SystemExit(main())
