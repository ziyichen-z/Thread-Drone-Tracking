"""S0 环境核验（合同 §2.1 S0、AC-1）：只读、零模型；桌面机经 `ssh Jetson` 逐条执行并保存读数原文。

用法（桌面机）：
    python -m tools.eng_jet.env_probe collect      # 逐条只读命令 → outputs/eng-jet/P1-ENG-JET-001/s0/probe-raw.json
    python -m tools.eng_jet.env_probe tegrastats-start   # 板上 nohup `timeout 300 tegrastats --interval 1000`
    python -m tools.eng_jet.env_probe tegrastats-fetch   # 取回 5 min 空闲日志
    python -m tools.eng_jet.env_probe build        # 解析 + 预注册判定 → docs/evidence/P1-ENG-JET-001-env.json

不做的事（§2.2、§7.3 (k)(l)(m)）：不 `sudo`、不 `nvpmodel -m`、不 `systemctl isolate`、不 `jetson_clocks`、
不改任何系统设置。合同写作 `sudo nvpmodel -q` / `dmesg | grep -i nvmap` 的两条读数，本机无免密 sudo、
`kernel.dmesg_restrict = 1`，按派发要求取非 root 只读来源并在 `source_note` 写明实际命令（等价性交接受裁定）。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.eng_jet import common

S0_DIR = common.OUT_DIR / "s0"
RAW_PATH = S0_DIR / "probe-raw.json"
TEGRA_LOCAL = S0_DIR / "s0-tegrastats.log"
TEGRA_BOARD = f"{common.BOARD_ROOT}/logs/s0-tegrastats.log"
TEGRA_SECONDS = 300

GPU_DEVFREQ = "/sys/class/devfreq/17000000.gpu"
GPU_MAX_HZ_LINE = 1_020_000_000
CPU_MAX_KHZ_LINE = 1_700_000
IDLE_RAM_MB_LINE = 1200
POWER_MODE_LINE = "MAXN_SUPER"

#: 合同读数 → 实际只读命令（全部非 root）。`contract` 逐字对应 §2.1 S0「内容」列。
PROBES: tuple[dict[str, str], ...] = (
    {"key": "nvpmodel_q", "contract": "sudo nvpmodel -q", "command": "nvpmodel -q",
     "source_note": "无免密 sudo；非 root `nvpmodel -q` 读当前模式（只读查询，不改模式）"},
    {"key": "nv_boot_control", "contract": "cat /etc/nv_boot_control.conf", "command": "cat /etc/nv_boot_control.conf"},
    {"key": "gpu_devfreq", "contract": "GPU 最高频率（devfreq sysfs）",
     "command": f"for f in max_freq min_freq cur_freq available_frequencies governor; do echo \"$f=$(cat {GPU_DEVFREQ}/$f 2>&1)\"; done"},
    {"key": "cpu_cpufreq", "contract": "CPU 最高频率（cpufreq sysfs）",
     "command": "for c in /sys/devices/system/cpu/cpu[0-9]*; do n=$(basename $c); echo \"$n online=$(cat $c/online 2>/dev/null || echo 1) "
                "cpuinfo_max_freq=$(cat $c/cpufreq/cpuinfo_max_freq 2>&1) scaling_max_freq=$(cat $c/cpufreq/scaling_max_freq 2>&1) "
                "scaling_governor=$(cat $c/cpufreq/scaling_governor 2>&1)\"; done"},
    {"key": "default_target", "contract": "systemctl get-default", "command": "systemctl get-default"},
    {"key": "display_manager", "contract": "display-manager 状态",
     "command": "echo is-active=$(systemctl is-active display-manager 2>&1); echo is-enabled=$(systemctl is-enabled display-manager 2>&1); "
                "for u in gdm gdm3 lightdm sddm; do echo $u=$(systemctl is-active $u 2>&1); done; "
                "echo gui_procs=$(ps -eo comm= | grep -c -E '^(Xorg|Xwayland|gnome-shell|gdm-session-wor)$')"},
    {"key": "dmesg_nvmap", "contract": "dmesg | grep -i nvmap",
     "command": "echo '# dmesg (non-root):'; dmesg 2>&1 | head -1; echo '# journalctl -k -b 0 | grep -i nvmap:'; "
                "journalctl -k -b 0 --no-pager 2>&1 | grep -i nvmap; echo journal_kernel_lines=$(journalctl -k -b 0 --no-pager 2>/dev/null | wc -l); "
                "echo journal_first=\"$(journalctl -k -b 0 --no-pager 2>/dev/null | head -2 | tail -1 | cut -c1-80)\"; "
                "echo kern_log_nvmap_lines=$(grep -ci nvmap /var/log/kern.log 2>&1)",
     "source_note": "`kernel.dmesg_restrict=1`、无免密 sudo：非 root `dmesg` 被拒（原文首行保留）；以 adm 组可读的 "
                    "`journalctl -k -b 0`（本次启动全部内核日志）替代，另记 `/var/log/kern.log` 命中行数"},
    {"key": "free_m", "contract": "free -m", "command": "free -m"},
    {"key": "swap", "contract": "swap 配置", "command": "swapon --show --bytes 2>&1; echo '# /proc/swaps'; cat /proc/swaps; echo '# zramctl'; zramctl 2>&1"},
    {"key": "disk", "contract": "磁盘余量", "command": "df -B1 / $HOME"},
    {"key": "nvcc_version", "contract": "nvcc --version", "command": "/usr/local/cuda/bin/nvcc --version",
     "source_note": "非登录 ssh 的 PATH 不含 /usr/local/cuda/bin，取绝对路径"},
    {"key": "python_import_tensorrt_torch", "contract": "python3 -c \"import tensorrt, torch\"",
     "command": "python3 -c \"import tensorrt, torch; print(tensorrt.__version__, torch.__version__)\" 2>&1; echo rc=$?; "
                "python3 -c \"import tensorrt; print('tensorrt', tensorrt.__version__)\" 2>&1; "
                "python3 -c \"import torch; print('torch', torch.__version__, torch.cuda.is_available())\" 2>&1 | tail -1"},
    # 以下为上下文读数（不进 verdict）。
    {"key": "platform", "contract": "（上下文）板型/版本", "command": "tr -d '\\0' < /proc/device-tree/model; echo; cat /etc/nv_tegra_release | head -1; uname -r; "
                "python3 --version; dpkg-query -W -f='${Package} ${Version}\\n' nvidia-l4t-core tensorrt cuda-toolkit-13-2 2>&1 | head -5"},
    {"key": "torch_availability", "contract": "（上下文）板上 torch 来源",
     "command": "python3 -m pip --version 2>&1 | tail -1; ls -d /usr/lib/python3*/dist-packages/torch /usr/local/lib/python3*/dist-packages/torch 2>&1; "
                "docker image ls --format '{{.Repository}}:{{.Tag}} {{.Size}}' 2>&1; "
                "docker image inspect nvcr.io/nvidia/pytorch:25.08-py3 --format '{{range .Config.Env}}{{println .}}{{end}}' 2>&1 | "
                "grep -E '^(TRT_VERSION|CUDA_VERSION|PYTORCH_VERSION|NVIDIA_PYTORCH_VERSION)='"},
    {"key": "load_idle", "contract": "（上下文）空闲负载", "command": "uptime; ps -eo pid,comm,%cpu,rss --sort=-rss | head -8"},
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ssh(command: str, host: str = common.BOARD_HOST, timeout: float = 120.0) -> dict[str, Any]:
    started = utc_now()
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", host, command],
                            capture_output=True, text=True, timeout=timeout)
    return {"started_utc": started, "ended_utc": utc_now(), "rc": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def collect(host: str = common.BOARD_HOST) -> dict[str, Any]:
    readings = {}
    for probe in PROBES:
        readings[probe["key"]] = {**probe, **ssh(probe["command"], host)}
    document = {"work_id": common.WORK_ID, "host": host, "collected_utc": utc_now(), "readings": readings}
    common.write_json(RAW_PATH, document)
    return document


# --- 解析 --------------------------------------------------------------------

_RAM = re.compile(r"\bRAM (\d+)/(\d+)MB")
_SWAP = re.compile(r"\bSWAP (\d+)/(\d+)MB")
_CPU = re.compile(r"\bCPU \[([^\]]*)\]")
_GR3D = re.compile(r"\bGR3D_FREQ (\d+)%(?:@\[?(\d+)\]?)?")
_TEMP = re.compile(r"\b(cpu|gpu|tj|soc0|soc1|soc2)@(-?[\d.]+)C")
_STAMP = re.compile(r"^(\d\d-\d\d-\d{4} \d\d:\d\d:\d\d)")


def parse_tegrastats(lines: Sequence[str]) -> list[dict[str, Any]]:
    """tegrastats 行 → {stamp, ram_used_mb, ram_total_mb, swap_used_mb, cpu_pct, cpu_mhz, gr3d_pct, gr3d_mhz, temps}。"""
    samples = []
    for line in lines:
        ram = _RAM.search(line)
        if not ram:
            continue
        sample: dict[str, Any] = {"ram_used_mb": int(ram.group(1)), "ram_total_mb": int(ram.group(2))}
        stamp = _STAMP.search(line)
        sample["stamp"] = stamp.group(1) if stamp else None
        swap = _SWAP.search(line)
        sample["swap_used_mb"] = int(swap.group(1)) if swap else None
        cpu = _CPU.search(line)
        pcts, mhz = [], []
        if cpu:
            for item in cpu.group(1).split(","):
                item = item.strip()
                if item == "off":
                    pcts.append(None)
                    mhz.append(None)
                    continue
                match = re.match(r"(\d+)%@(\d+)", item)
                if match:
                    pcts.append(int(match.group(1)))
                    mhz.append(int(match.group(2)))
        sample["cpu_pct"], sample["cpu_mhz"] = pcts, mhz
        gr3d = _GR3D.search(line)
        sample["gr3d_pct"] = int(gr3d.group(1)) if gr3d else None
        sample["gr3d_mhz"] = int(gr3d.group(2)) if gr3d and gr3d.group(2) else None
        sample["temps_c"] = {name: float(value) for name, value in _TEMP.findall(line)}
        samples.append(sample)
    return samples


def _kv(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


def parse_cpu(text: str) -> list[dict[str, Any]]:
    cores = []
    for line in text.splitlines():
        parts = line.split()
        if not parts or not parts[0].startswith("cpu"):
            continue
        fields = dict(part.split("=", 1) for part in parts[1:] if "=" in part)
        core = {"cpu": parts[0], "online": fields.get("online") == "1"}
        for key in ("cpuinfo_max_freq", "scaling_max_freq"):
            core[key] = int(fields[key]) if fields.get(key, "").isdigit() else None
        core["scaling_governor"] = fields.get("scaling_governor")
        cores.append(core)
    return cores


def parse_power_mode(text: str) -> str | None:
    match = re.search(r"NV Power Mode:\s*(\S+)", text)
    return match.group(1) if match else None


# --- 预注册判定（§2.1 S0「通过线」与「STOP」列；按表内顺序取第一个失败原因码）------------------------


def evaluate(readings: Mapping[str, Mapping[str, Any]], tegra: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    boot = readings["nv_boot_control"]["stdout"]
    checks.append({"criterion": "nv_boot_control.conf 含 super", "observed": [l for l in boot.splitlines() if "super" in l.lower()],
                   "pass": "super" in boot.lower(), "stop_code": "NOT_SUPER"})

    gpu = _kv(readings["gpu_devfreq"]["stdout"])
    gpu_max = int(gpu["max_freq"]) if gpu.get("max_freq", "").isdigit() else None
    available = [int(v) for v in gpu.get("available_frequencies", "").split() if v.isdigit()]
    gpu_top = max(available) if available else None
    gpu_ok = gpu_max is not None and gpu_max >= GPU_MAX_HZ_LINE and (gpu_top is None or gpu_top >= GPU_MAX_HZ_LINE)
    checks.append({"criterion": "GPU 上限 ≥ 1020 MHz（devfreq max_freq 与 available_frequencies 最大值）",
                   "observed": {"max_freq_hz": gpu_max, "available_max_hz": gpu_top, "governor": gpu.get("governor")},
                   "pass": gpu_ok, "stop_code": "FREQ_CAPPED"})

    cores = [c for c in parse_cpu(readings["cpu_cpufreq"]["stdout"]) if c["online"]]
    cpu_caps = [c["scaling_max_freq"] for c in cores]
    cpu_ok = bool(cores) and all(v is not None and v >= CPU_MAX_KHZ_LINE for v in cpu_caps)
    checks.append({"criterion": "CPU 上限 ≥ 1.7 GHz（全部在线核 scaling_max_freq）",
                   "observed": {"online_cores": len(cores), "scaling_max_freq_khz": sorted(set(v for v in cpu_caps if v is not None)),
                                "cpuinfo_max_freq_khz": sorted(set(c["cpuinfo_max_freq"] for c in cores if c["cpuinfo_max_freq"]))},
                   "pass": cpu_ok, "stop_code": "FREQ_CAPPED"})

    mode = parse_power_mode(readings["nvpmodel_q"]["stdout"])
    checks.append({"criterion": "nvpmodel -q 当前模式 = MAXN_SUPER（AR1-3：可选未选不算过）", "observed": mode,
                   "pass": mode == POWER_MODE_LINE, "stop_code": "POWER_MODE_NOT_MAXN_SUPER"})

    target = readings["default_target"]["stdout"].strip()
    dm = _kv(readings["display_manager"]["stdout"])
    headless = target == "multi-user.target" and dm.get("is-active") == "inactive"
    checks.append({"criterion": "get-default = multi-user.target 且 display-manager inactive",
                   "observed": {"default_target": target, **dm}, "pass": headless, "stop_code": "NOT_HEADLESS"})

    used = [s["ram_used_mb"] for s in tegra]
    duration = len(used)
    ram_ok = bool(used) and max(used) <= IDLE_RAM_MB_LINE
    checks.append({"criterion": "headless 空闲 RAM ≤ 1.2 GB（tegrastats 5 min 每秒样本的最大值 ≤ 1200 MB）",
                   "observed": {"samples": duration, **common.summary(used, 1), "unit": "MB（tegrastats 原文单位）"},
                   "pass": ram_ok, "stop_code": "IDLE_RAM_OVER"})

    failures = [c for c in checks if not c["pass"]]
    verdict = "PASS" if not failures else f"STOP({failures[0]['stop_code']})"
    return {"checks": checks, "verdict": verdict, "failing_codes": [c["stop_code"] for c in failures]}


def build(raw: Mapping[str, Any] | None = None, tegra_lines: Sequence[str] | None = None) -> dict[str, Any]:
    raw = raw if raw is not None else common.read_json(RAW_PATH)
    if tegra_lines is None:
        tegra_lines = TEGRA_LOCAL.read_text(encoding="utf-8").splitlines()
    tegra = parse_tegrastats(tegra_lines)
    readings = raw["readings"]
    result = evaluate(readings, tegra)
    temps = {k: common.summary([s["temps_c"].get(k) for s in tegra if k in s["temps_c"]], 2) for k in ("cpu", "gpu", "tj")}
    document = {
        "work_id": common.WORK_ID,
        "step": "S0",
        "verdict": result["verdict"],
        "verdict_is_reading_not_acceptance": True,
        "checks": result["checks"],
        "readings": {key: {k: value.get(k) for k in ("contract", "command", "source_note", "rc", "stdout", "stderr", "started_utc", "ended_utc")}
                     for key, value in readings.items()},
        "tegrastats_idle": {
            "command": f"nohup timeout {TEGRA_SECONDS} tegrastats --interval 1000",
            "samples": len(tegra),
            "first_stamp_board_local": tegra[0]["stamp"] if tegra else None,
            "last_stamp_board_local": tegra[-1]["stamp"] if tegra else None,
            "ram_used_mb": common.summary([s["ram_used_mb"] for s in tegra], 1),
            "ram_total_mb": tegra[0]["ram_total_mb"] if tegra else None,
            "gr3d_pct": common.summary([s["gr3d_pct"] for s in tegra if s["gr3d_pct"] is not None], 1),
            "temps_c": temps,
            "raw_log_sha256": common.sha256_bytes(("\n".join(tegra_lines) + "\n").encode("utf-8")) if tegra_lines else None,
            "raw_log_path": common.rel_project(TEGRA_LOCAL),
        },
        "not_executed": ["sudo（任何）", "nvpmodel -m", "systemctl isolate", "jetson_clocks", "任何系统设置改动"],
        "raw_path": common.rel_project(RAW_PATH),
        "raw_sha256": common.sha256_file(RAW_PATH) if RAW_PATH.exists() else None,
    }
    common.write_json(common.evidence("env.json"), document)
    return document


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("collect", "tegrastats-start", "tegrastats-fetch", "build"))
    parser.add_argument("--host", default=common.BOARD_HOST)
    args = parser.parse_args(argv)
    if args.action == "collect":
        document = collect(args.host)
        print(json.dumps({k: v["rc"] for k, v in document["readings"].items()}))
    elif args.action == "tegrastats-start":
        print(json.dumps(ssh(f"mkdir -p {common.BOARD_ROOT}/logs && (nohup timeout {TEGRA_SECONDS} tegrastats --interval 1000 "
                             f"> {TEGRA_BOARD} 2>&1 < /dev/null &)", args.host)))
    elif args.action == "tegrastats-fetch":
        S0_DIR.mkdir(parents=True, exist_ok=True)
        common.refuse_protected(TEGRA_LOCAL)
        subprocess.run(["scp", "-q", f"{args.host}:{TEGRA_BOARD}", str(TEGRA_LOCAL)], check=True)
        print(len(TEGRA_LOCAL.read_text(encoding="utf-8").splitlines()))
    else:
        document = build()
        print(json.dumps({"verdict": document["verdict"], "checks": [(c["criterion"][:24], c["pass"]) for c in document["checks"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
