"""P1-ENG-FASTFIX-001 续做独占窗口计量（「续做信封落实」§4；FASTFIX-MINI-MUTEX 整窗 U(t)）。

只读 macOS 计数，不导入 `controller`、不读真值、不提权。整窗判限量
`U(t) = C(t) + E(t) + R(t)`（允许重复覆盖而偏大，不做扣减）：

- C(t)：Claude.app 资源联盟（t0 快照给定 pid/联盟号）自固定 t0 原值起的累计增量，四个写字段保守相加
  `byteswritten + logical_immediate_writes + logical_deferred_writes + logical_metadata_writes`
  （联盟计数含已退出成员；逻辑延迟写不因较大被略去；不扣 `logical_invalidated_writes`）。
- E(t)：联盟外已见写者。(1) 具名外部进程（如 pid 23472）自进程启动起的终身写量
  `ri_diskio_byteswritten + ri_logical_writes`（绝对值，覆盖 t0 前后，完整上界）；
  (2) 这些进程所在外部联盟自本工具首读起的四字段累计增量（首读前区间按预检节的归属读法处理）。
- R(t)：声明根并集 = 数据卷所在 APFS 容器占用（`statvfs` 总块 − 可用块）自首读基线的已见最大新增量
  （不因删除/清理下降；容器并集即对所有声明根精确去重）。

任何读取失败、联盟号变更、计数回退 → 置 `UNKNOWN` 旗标文件（不换 t0、不重置）；
U ≥ stop_at → `STOP_DISK`；U ≥ limit → `STOP_BUDGET`。停令文件存在即退出（节拍 = interval）。
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import json
import os
from pathlib import Path
import time

WRITE_FIELDS = ("byteswritten", "logical_immediate_writes", "logical_deferred_writes", "logical_metadata_writes")
CRU_FIELDS = (
    "tasks_started", "tasks_exited", "time_nonempty", "cpu_time", "interrupt_wakeups", "platform_idle_wakeups",
    "bytesread", "byteswritten", "gpu_time", "cpu_time_billed_to_me", "cpu_time_billed_to_others", "energy",
    "logical_immediate_writes", "logical_deferred_writes", "logical_invalidated_writes", "logical_metadata_writes",
)
CRU_PREFIX_SIZE = 8 * len(CRU_FIELDS)  # 128：经典 struct coalition_resource_usage 前缀
PROC_PIDCOALITIONINFO = 20
RUSAGE_INFO_V4 = 4
RU_FIELDS = (
    "user_time", "system_time", "pkg_idle_wkups", "interrupt_wkups", "pageins", "wired_size", "resident_size",
    "phys_footprint", "proc_start_abstime", "proc_exit_abstime", "child_user_time", "child_system_time",
    "child_pkg_idle_wkups", "child_interrupt_wkups", "child_pageins", "child_elapsed_abstime",
    "diskio_bytesread", "diskio_byteswritten", "cpu_time_qos_default", "cpu_time_qos_maintenance",
    "cpu_time_qos_background", "cpu_time_qos_utility", "cpu_time_qos_legacy", "cpu_time_qos_user_initiated",
    "cpu_time_qos_user_interactive", "billed_system_time", "serviced_system_time", "logical_writes",
)


class _PidCoal(ctypes.Structure):
    _fields_ = [("coalition_id", ctypes.c_uint64 * 2), ("r1", ctypes.c_uint64), ("r2", ctypes.c_uint64), ("r3", ctypes.c_uint64)]


class _CRU(ctypes.Structure):
    _fields_ = [(f, ctypes.c_uint64) for f in CRU_FIELDS] + [("_pad", ctypes.c_uint64 * 64)]


class _RU(ctypes.Structure):
    _fields_ = [("uuid", ctypes.c_uint8 * 16)] + [(f, ctypes.c_uint64) for f in RU_FIELDS] + [("_pad", ctypes.c_uint64 * 64)]


class MeterError(RuntimeError):
    pass


class MacReader:
    def __init__(self) -> None:
        self.lib = ctypes.CDLL(ctypes.util.find_library("System"), use_errno=True)
        self.lib.coalition_info_resource_usage.argtypes = [ctypes.c_uint64, ctypes.c_void_p, ctypes.c_size_t]

    def coalition_of(self, pid: int) -> int:
        pc = _PidCoal()
        n = self.lib.proc_pidinfo(pid, PROC_PIDCOALITIONINFO, ctypes.c_uint64(0), ctypes.byref(pc), ctypes.sizeof(pc))
        if n != ctypes.sizeof(pc):
            raise MeterError(f"proc_pidinfo(pid={pid}) returned {n}, errno={ctypes.get_errno()}")
        return int(pc.coalition_id[0])

    def coalition_usage(self, cid: int) -> dict:
        cru = _CRU()
        ret = self.lib.coalition_info_resource_usage(ctypes.c_uint64(cid), ctypes.byref(cru), CRU_PREFIX_SIZE)
        if ret != 0:
            raise MeterError(f"coalition_info_resource_usage({cid}) ret={ret} errno={ctypes.get_errno()}")
        return {f: int(getattr(cru, f)) for f in CRU_FIELDS}

    def pid_rusage(self, pid: int) -> dict:
        ru = _RU()
        ret = self.lib.proc_pid_rusage(pid, RUSAGE_INFO_V4, ctypes.byref(ru))
        if ret != 0:
            raise MeterError(f"proc_pid_rusage({pid}) ret={ret} errno={ctypes.get_errno()}")
        return {f: int(getattr(ru, f)) for f in ("diskio_byteswritten", "logical_writes", "proc_start_abstime")}

    def container_used(self, path: str) -> int:
        st = os.statvfs(path)
        return int((st.f_blocks - st.f_bavail) * st.f_frsize)


def write_sum(usage: dict) -> int:
    return sum(int(usage[f]) for f in WRITE_FIELDS)


class WindowMeter:
    """纯计算核：给定读数序列推 U(t) 与旗标；读取器可替换（测试用假读取器）。"""

    def __init__(self, reader, t0: dict, ext_pids: list[int], volume: str, stop_at: int, limit: int) -> None:
        self.reader = reader
        self.t0 = t0
        # 执行者联盟闭集：续做窗口 = t0 快照的 Claude.app 单联盟；B/C 操作单 = `snapshot()` 写出的多联盟
        # （Claude.app / Unity / 终端等具名执行者），各自固定起点累计、相加。
        members = t0.get("coalitions") or [
            {"pid": t0["claude_app_pid"], "coalition_id": t0["coalition_ids"][0], "raw": t0["raw"]}
        ]
        self.members = [(int(m["pid"]), int(m["coalition_id"]), {f: int(m["raw"][f]) for f in WRITE_FIELDS}) for m in members]
        self.claude_pid, self.claude_cid, self.c0 = self.members[0]
        self.member_prev: dict[int, dict] = {}
        self.ext_pids = list(ext_pids)
        self.volume = volume
        self.stop_at = int(stop_at)
        self.limit = int(limit)
        self.prev_claude: dict | None = None
        self.ext_base: dict[int, dict] = {}
        self.ext_prev: dict[int, dict] = {}
        self.ext_cid: dict[int, int] = {}
        self.named_prev: dict[int, int] = {}
        self.named_start: dict[int, int] = {}
        self.r_base: int | None = None
        self.r_max = 0
        self.flags: set[str] = set()
        self.reasons: list[str] = []

    def _unknown(self, why: str) -> None:
        self.flags.add("UNKNOWN")
        self.reasons.append(why)

    def sample(self) -> dict:
        rec: dict = {}
        c = e = r = None
        try:
            c = 0
            for index, (pid, member_cid, base) in enumerate(self.members):
                cid = self.reader.coalition_of(pid)
                if cid != member_cid:
                    raise MeterError(f"coalition of pid {pid} changed {member_cid}->{cid}")
                usage = self.reader.coalition_usage(cid)
                prev = self.member_prev.get(cid)
                if prev is not None and any(usage[f] < prev[f] for f in WRITE_FIELDS):
                    raise MeterError(f"coalition {cid} counter regressed")
                if any(usage[f] < base[f] for f in WRITE_FIELDS):
                    raise MeterError(f"coalition {cid} counter below t0")
                self.member_prev[cid] = usage
                c += sum(usage[f] - base[f] for f in WRITE_FIELDS)
                rec["claude_raw" if index == 0 else f"coal{cid}_raw"] = {f: usage[f] for f in WRITE_FIELDS}
        except Exception as exc:  # noqa: BLE001 — 任一异常即 UNKNOWN
            c = None
            self._unknown(f"C:{exc}")
        try:
            e = 0
            ext_raw = {}
            for pid in self.ext_pids:
                ru = self.reader.pid_rusage(pid)
                life = ru["diskio_byteswritten"] + ru["logical_writes"]
                if pid in self.named_start and ru["proc_start_abstime"] != self.named_start[pid]:
                    raise MeterError(f"external pid {pid} identity changed")
                if pid in self.named_prev and life < self.named_prev[pid]:
                    raise MeterError(f"external pid {pid} lifetime writes regressed")
                self.named_start[pid] = ru["proc_start_abstime"]
                self.named_prev[pid] = life
                e += life
                cid = self.reader.coalition_of(pid)
                if pid in self.ext_cid and self.ext_cid[pid] != cid:
                    raise MeterError(f"external pid {pid} coalition changed")
                self.ext_cid[pid] = cid
                ext_raw[str(pid)] = {"lifetime_writes": life, "coalition": cid}
            for cid in sorted(set(self.ext_cid.values()) - {m[1] for m in self.members}):
                usage = self.reader.coalition_usage(cid)
                if cid not in self.ext_base:
                    self.ext_base[cid] = usage
                prev = self.ext_prev.get(cid, usage)
                if any(usage[f] < prev[f] for f in WRITE_FIELDS):
                    raise MeterError(f"external coalition {cid} regressed")
                self.ext_prev[cid] = usage
                d = write_sum(usage) - write_sum(self.ext_base[cid])
                e += d
                ext_raw[f"coal{cid}"] = {"since_first_read": d}
            rec["ext"] = ext_raw
        except Exception as exc:  # noqa: BLE001
            e = None
            self._unknown(f"E:{exc}")
        try:
            used = self.reader.container_used(self.volume)
            if self.r_base is None:
                self.r_base = used
            self.r_max = max(self.r_max, used - self.r_base)
            r = self.r_max
            rec["container_used"] = used
        except Exception as exc:  # noqa: BLE001
            self._unknown(f"R:{exc}")
        u = None if None in (c, e, r) else c + e + r
        if u is not None:
            if u >= self.stop_at:
                self.flags.add("STOP_DISK")
            if u >= self.limit:
                self.flags.add("STOP_BUDGET")
        rec.update({"C": c, "E": e, "R": r, "U": u, "flags": sorted(self.flags)})
        return rec


def snapshot(reader, pids: list[int]) -> dict:
    """B/C 操作单的阶段起点 t0：读各具名执行者进程所在资源联盟的原始累计计数（同一时刻、先于任何阶段写入）。
    同一联盟只记一次；任一读取失败即抛错（不派生起点 → S-UNKNOWN）。"""
    seen: dict[int, dict] = {}
    for pid in pids:
        cid = reader.coalition_of(int(pid))
        if cid not in seen:
            seen[cid] = {"pid": int(pid), "coalition_id": cid, "raw": reader.coalition_usage(cid)}
    return {"t0_unix": time.time(), "t0_monotonic": time.monotonic(), "coalitions": list(seen.values())}


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        import sys  # noqa: PLC0415

        argv = sys.argv[1:]
    if argv and argv[0] == "snapshot":
        sp = argparse.ArgumentParser(description="写阶段 t0 快照（多联盟）")
        sp.add_argument("--pid", type=int, action="append", required=True)
        sp.add_argument("--out", required=True)
        a = sp.parse_args(argv[1:])
        out = Path(a.out)
        if out.exists():
            raise SystemExit(f"{out} exists; t0 is never replaced")
        out.write_text(json.dumps(snapshot(MacReader(), a.pid), sort_keys=True) + "\n", encoding="utf-8")
        return 0
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--t0-json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--flag-dir", required=True)
    ap.add_argument("--stop-file", required=True)
    ap.add_argument("--ext-pid", type=int, action="append", default=[])
    ap.add_argument("--volume", default="/System/Volumes/Data")
    ap.add_argument("--interval", type=float, default=0.4)
    ap.add_argument("--stop-at", type=int, required=True)
    ap.add_argument("--limit", type=int, required=True)
    ap.add_argument("--max-bytes", type=int, default=8_000_000)
    args = ap.parse_args(argv)
    if args.interval > 0.5:
        raise SystemExit("interval must be <= 0.5 s")
    t0 = json.loads(Path(args.t0_json).read_text())
    meter = WindowMeter(MacReader(), t0, args.ext_pid, args.volume, args.stop_at, args.limit)
    flag_dir = Path(args.flag_dir)
    flag_dir.mkdir(parents=True, exist_ok=True)
    out = Path(args.out)
    written = out.stat().st_size if out.exists() else 0
    with out.open("a", encoding="utf-8") as fh:
        while True:
            m0, u0 = time.monotonic(), time.time()
            rec = meter.sample()
            rec.update({"m": round(m0, 4), "unix": round(u0, 4)})
            line = json.dumps(rec, sort_keys=True) + "\n"
            if written + len(line) > args.max_bytes:
                meter._unknown("meter_truncated")
                (flag_dir / "UNKNOWN").write_text("meter_truncated\n")
                return 3
            fh.write(line)
            fh.flush()
            written += len(line)
            for flag in meter.flags:
                p = flag_dir / flag
                if not p.exists():
                    p.write_text(json.dumps({"unix": u0, "U": rec["U"], "reasons": meter.reasons[-3:]}) + "\n")
            if Path(args.stop_file).exists():
                return 0
            time.sleep(max(0.0, args.interval - (time.monotonic() - m0)))


if __name__ == "__main__":
    raise SystemExit(main())
