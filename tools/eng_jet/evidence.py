"""§3.4 证据文件组装（桌面机）：S1/S2、SR、S3–S5 的 verdict 与读数从原始收据机器生成，不手抄数字。

    python -m tools.eng_jet.evidence fastlayer          # -fastlayer.json（S1/S2；容器路径 TRT 不支持 SM 87 → NOT_RUN）
    python -m tools.eng_jet.evidence container-stack --image-digest D   # -env.json 追加 s1s2_container_stack（与 S0 系统栈分列）
    python -m tools.eng_jet.evidence system-stack       # -env.json 追加 s1s2_system_stack（K1K3K4补跑B：系统 venv 构造与安装记录）
    python -m tools.eng_jet.evidence fastlayer-system   # -fastlayer.json（K1K3K4补跑B；前轮原文保留在 history）
    python -m tools.eng_jet.evidence system-stack-c     # -env.json 追加 s1s2_system_stack_c（K1K3K4补跑C：安装记录、verify、实跑栈）
    python -m tools.eng_jet.evidence fastlayer-system-c # -fastlayer.json（K1K3K4补跑C；前轮原文保留在 history）
    python -m tools.eng_jet.evidence system-stack-d     # -env.json 追加 s1s2_system_stack_d（K1K3K4补跑D：环境变量、装后清理、容器 venv 删除）
    python -m tools.eng_jet.evidence fastlayer-system-d # -fastlayer.json（K1K3K4补跑D：S1/S2 实跑读数；前轮原文保留在 history）
    python -m tools.eng_jet.evidence assets-d --manifest M --board-sha S --zero-write Z   # -assets.json 补跑D 更新
    python -m tools.eng_jet.evidence system-stack-e     # -env.json 追加 s2_system_stack_e（K1K3K4补跑E：AC-16、外部写入、容器 venv 删除）
    python -m tools.eng_jet.evidence fastlayer-system-e # -fastlayer.json（K1K3K4补跑E：S2 实跑，RESUMED_AFTER_USER_RULING(S1)）
    python -m tools.eng_jet.evidence assets-e --manifest M --board-sha S --zero-write Z   # -assets.json 补跑E 更新（AC-12 修订 2 分列）
    python -m tools.eng_jet.evidence assets-c --manifest M --code-bundle C --board-sha S --zero-write Z   # -assets.json 补跑C 更新
    python -m tools.eng_jet.evidence relay --smoke DIR  # -relay.json（forward/return/disconnect + tailscale_smoke）
    python -m tools.eng_jet.evidence relay-f            # -relay.json（K1K3K4补跑F 正式 SR；tailscale_smoke 原件逐字保留）
    python -m tools.eng_jet.evidence system-stack-f     # -env.json 追加 sr_system_stack_f（AC-16、外部写入、链路事件、对时）
    python -m tools.eng_jet.evidence assets-f --manifest M --board-sha S --zero-write Z --bundle B   # -assets.json 补跑F 更新
    python -m tools.eng_jet.evidence stage-b            # -vlm.json / -quant-equivalence.json / -coresidency.json（NOT_RUN）
    python -m tools.eng_jet.evidence assets --manifest M --bundle B --local L   # -assets.json（AC-11 + board_manifest）
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence

from tools.eng_jet import common

NOT_RUN_STAGE_B = "NOT_RUN(阶段 B 信封未签)"
NOT_RUN_H = "NOT_RUN(待用户 (h))"
NOT_RUN_TORCH = "NOT_RUN(PATH_UNAVAILABLE(system-torch))"


def torch_reading() -> dict[str, Any]:
    env = common.read_json(common.evidence("env.json"))
    reading = env["readings"]
    return {
        "source": "docs/evidence/P1-ENG-JET-001-env.json readings.python_import_tensorrt_torch / readings.torch_availability",
        "python_import_tensorrt_torch": reading["python_import_tensorrt_torch"]["stdout"],
        "torch_availability": reading["torch_availability"]["stdout"],
    }


S1S2_DIR = common.OUT_DIR / "s1s2"
CONTAINER_IMAGE = "nvcr.io/nvidia/pytorch:25.08-py3"
NOT_RUN_CONTAINER_TRT = "NOT_RUN(PATH_UNAVAILABLE(container-tensorrt-sm87))"


def _raw(name: str) -> dict[str, Any]:
    path = S1S2_DIR / name
    return {"file": common.rel_project(path), "sha256": common.sha256_file(path), "bytes": path.stat().st_size}


def _grep(name: str, *needles: str) -> list[str]:
    lines = (S1S2_DIR / name).read_text(encoding="utf-8", errors="replace").splitlines()
    return [line.replace("\x1b[34m\x1b[1m", "").replace("\x1b[0m", "").strip() for line in lines if any(n in line for n in needles)]


def container_stack(image_digest: str) -> dict[str, Any]:
    """AC-2 修订 2：S1/S2 容器实跑栈读数，与 S0 系统栈（`readings`）分列写入 -env.json `s1s2_container_stack`。"""
    stack = common.read_json(S1S2_DIR / "stack-summary.json")
    section = {
        "note": "S1/S2 执行栈 = 板上 NGC 容器实跑读数（`fastlayer_bench stack` 在容器内 import 实测），不代表 S0 的 JP7.2 系统栈"
                "（CUDA 13.2 / TensorRT 10.16，见本文件 readings）；二者分列不混记（提案决策记录「S1/S2 容器栈落实」）。",
        "image": CONTAINER_IMAGE, "image_digest": image_digest, "runtime": "docker 缺省 runtime = nvidia；--user 1000:1000 + video/render 组",
        "measured": stack, "raw": _raw("stack-summary.json"),
        "tensorrt_sm87": {"supported": False, "evidence": _grep("trtexec-onnx-sm87-check.log", "Compute Capability", "TensorRT version", "SM 87"),
                          "raw": _raw("trtexec-onnx-sm87-check.log")},
    }
    document = common.read_json(common.evidence("env.json"))
    document["s1s2_container_stack"] = section
    common.write_json(common.evidence("env.json"), document)
    return section


def fastlayer() -> dict[str, Any]:
    """S1/S2（K1K3K4补跑，容器路径）：本轮容器内导出方形 FP16 引擎时 TensorRT 10.13.2.6 拒绝 SM 87（Orin）→ 合同执行路径不可用。"""
    ledger_events = common.read_jsonl(common.OUT_DIR / "ledger-events.jsonl")
    pip = [e for e in ledger_events if e["kind"] == "board_pip"]
    exports = [e for e in ledger_events if e["kind"] == "engine_export"]
    reason = ("提案决策记录「S1/S2 容器栈落实」把 S1/S2 执行栈定为板上 NGC 容器 nvcr.io/nvidia/pytorch:25.08-py3。容器内 torch CUDA 可用"
              "（Orin，torch 2.8.0a0 / CUDA 13.0），冻结 .pt → ONNX 导出成功，但 TensorRT 10.13.2.6 建 FP16 引擎报 "
              "`Error Code 9: Target GPU SM 87 is not supported by this TensorRT release`；同一 ONNX 用容器自带 trtexec --fp16 复证同错。"
              "该镜像的 TensorRT 不支持 Orin 的 SM 87，§2.1/§3.1 要求的 TRT FP16 引擎无法在合同执行栈产出；按 §2.1「不自行修复环境」与派发"
              "「容器路径因运行时不可用而走不通时不变通」，S1/S2 记 NOT_RUN(PATH_UNAVAILABLE(container-tensorrt-sm87))（与 IR-3 已接受的形状同型），"
              "不改用宿主 TensorRT 10.16 拼接、不换镜像、不装其他包，路径选择交用户。")
    document = {
        "work_id": common.WORK_ID,
        "round": "K1K3K4补跑",
        "S1": {
            "verdict": NOT_RUN_CONTAINER_TRT,
            "reason": reason,
            "execution_stack": {"image": CONTAINER_IMAGE, "runtime_stack_ref": "docs/evidence/P1-ENG-JET-001-env.json s1s2_container_stack"},
            "engines_exported": [],
            "export_attempts": [{**e, "log": _raw("ej-export640.log"),
                                 "log_excerpt": _grep("ej-export640.log", "PyTorch:", "ONNX:", "starting export with TensorRT", "building FP16",
                                                      "Error Code 9", "export failure")} for e in exports],
            "export_args": {"format": "engine", "half": True, "imgsz": 640, "dynamic": False, "device": 0, "workspace": None, "simplify": False},
            "tensorrt_cross_check": {"command": "trtexec --onnx=<last.onnx> --fp16 --skipInference（容器 /opt/tensorrt/bin/trtexec）",
                                     "excerpt": _grep("trtexec-onnx-sm87-check.log", "Compute Capability", "TensorRT version", "Error[9]", "&&&& FAILED"),
                                     "raw": _raw("trtexec-onnx-sm87-check.log")},
            "rect_engine": "未尝试：方形引擎已在 TRT 建引擎阶段失败，同一镜像同一 SM 87 限制，矩形引擎（imgsz=480,640）不会不同；不重复消耗",
            "pt_sha256_after_attempt": "d6a0d6a9cdee06a0790f5d9812a1fe98db033520981c0ffafe786c3cbbe059c9（板上 sha256sum，与规格一致；未被改写）",
            "container_setup": {"venv": "~/eng-jet/venv（容器内 python3 -m venv --system-site-packages，复用镜像 torch/TensorRT，未重装 torch）",
                                "pip": [{k: e.get(k) for k in ("package", "version", "wheel_sha256", "wheel_bytes", "bytes", "status") if k in e} for e in pip],
                                "pip_logs": [_raw("pip-install.log"), _raw("pip-headless.log"), _raw("pip-install-report.json"), _raw("pip-headless-report.json")],
                                "board_only_shim": "~/eng-jet/code/tools/__init__.py（0 字节，仅板上）：镜像内 nvfuser egg 自带顶层 `tools` 普通包，遮蔽仓库的"
                                                   " `tools` 命名空间包导致 `python -m tools.eng_jet.fastlayer_bench` 找不到模块；加空 __init__ 使仓库 tools 优先，仓库未改"},
            "planned_protocol": {"frames": "a7 帧 0（init）+ 帧 1..320 update（n = 320，AC-2 修订 1 / IR-6）",
                                 "init_box": [0.4446039270172931, 0.7078459879432423, 0.0553960729827069, 0.16146109855182247],
                                 "init_box_source": "docs/evidence/P1-ENG-FAST-002-latency.json frames.init_box（G-7 离线用户框替身，AC-2 修订 1 / IR-5；"
                                                    "非检测器产出；不读不传真值）",
                                 "comparison": "frozen-V（MPS）：帧 0…49 计数不一致 = 0、帧 1…320 配对最大差 ≤ 1e-3、两侧未配对 0（AC-2 修订 1）"},
            "previous_round": {"verdict": NOT_RUN_TORCH, "board_torch_reading": torch_reading()},
        },
        "S2": {"verdict": NOT_RUN_CONTAINER_TRT, "reason": "依赖 S1 方形 TRT 引擎；同 S1。", "bins": []},
        "AC-2": "不满足（NOT_RUN 步骤对应 AC 不得记满足，§2.1）",
        "AC-3": "不满足（NOT_RUN）",
    }
    common.write_json(common.evidence("fastlayer.json"), document)
    return document


S1S2_SYSTEM_DIR = common.OUT_DIR / "s1s2-system"
ROUND_B = "K1K3K4补跑B"
NOT_RUN_SYSTEM_TORCH = NOT_RUN_TORCH
SUB1_STOP_REASON = (
    "提案决策记录「S1/S2 系统栈落实（B）」与「needs_user」题 4（CLARIFY-B2）：在板上系统 Python 的 --system-site-packages venv 中从官方 cu130 "
    "索引安装 torch 2.9.1+cu130 / torchvision 0.24.1，依赖从 PyPI 解析，SUB:1 额度 ≤ 32 包 / 下载 ≤ 3.5 GB / 新增磁盘 ≤ 8 GB。本轮先以 "
    "pip download --no-deps 取回两枚官方轮子（520,271,881 B，sha 与题 4 一致），再以 pip 24.0 `install --dry-run --report --no-cache-dir` "
    "解析依赖——该版 pip 干跑会把每个依赖的轮子体完整取回到临时目录后丢弃，22 个轮子共 2,318,455,950 B（含解析器选中的 PyPI 同名 "
    "torchvision 2,386,737 B）被取回且未留存。累计下载按保守口径（板上外网接口收包）3,093,609,695 B ≤ 3.5 GB；完成安装还须重新取回 "
    "21 个依赖轮子 2,316,069,213 B，合计约 5.4 GB（收包口径约 5.6 GB）> 3.5 GB。按派发「任一上限将超即停」停在安装之前：torch 未安装，"
    "题 4 的安装后先验证（get_arch_list / CUDA matmul / TensorRT 共存）未执行，S1/S2 未运行；未换源、未 --no-deps 变通、未 sudo/apt。")


def _raw_system(name: str) -> dict[str, Any]:
    path = S1S2_SYSTEM_DIR / name
    return {"file": common.rel_project(path), "sha256": common.sha256_file(path), "bytes": path.stat().st_size}


def system_stack() -> dict[str, Any]:
    """AC-2 修订 5：S1/S2 系统栈（板上系统 Python venv）构造与安装记录，与 S0 系统栈 `readings`、容器栈 `s1s2_container_stack` 分列。"""
    d = S1S2_SYSTEM_DIR
    fetched = common.read_json(d / "sub1-dryrun-fetched.json")
    section = {
        "round": ROUND_B,
        "note": "S1/S2 执行栈 = 板上系统 Python 3.12 的 --system-site-packages venv（复用系统 TensorRT 10.16）；本轮因 SUB:1 下载额度将超停在 "
                "torch 安装之前，torch/torchvision 未安装，故无实跑 torch/CUDA 读数（AC-2 修订 5 的实跑读数待安装完成后记录）。",
        "venv": {"path": common.SYSTEM_VENV, "command": "python3 -m venv --system-site-packages ~/eng-jet/sysvenv",
                 "pyvenv_cfg": (d / "sysvenv-pyvenv.cfg").read_text(encoding="utf-8"), "pip": "24.0（venv 自带，来自系统 python3-pip-whl，未联网）"},
        "python312_patch_change": {
            "dpkg_now": (d / "python312-dpkg.txt").read_text(encoding="utf-8").strip(),
            "s0_recorded": "3.12.3-1ubuntu0.15（S0 readings 原文不改写）",
            "source": "docs/authorizations.md 2026-10-02「P1-ENG-JET-001 — 用户选执行栈 B 的前置：经 Mac mini ssh 在板上 sudo 安装 "
                      "python3-pip/python3-venv（用户输入密码；supervisor 会话代录）」授权范围 (b)：用户本人 sudo apt 把 python3.12 由 "
                      "3.12.3-1ubuntu0.15 升至 0.17（提案「S1/S2 系统栈落实（B）」给实现角色的提示）"},
        "system_packages_visible": {"numpy": "1.26.4", "cv2": "4.8.0（系统）", "tensorrt": "10.16.2.10（/usr/lib/python3.12/dist-packages）",
                                    "PIL": "10.2.0", "yaml": "6.0.1", "matplotlib": "3.6.3", "scipy": "1.11.4", "sympy": "1.12", "jinja2": "3.1.2",
                                    "typing_extensions": "4.10.0", "mpmath": "1.2.1", "setuptools": "68.1.2",
                                    "missing": ["torch", "torchvision", "onnx", "protobuf", "filelock", "networkx", "fsspec", "psutil", "polars", "pynvml"],
                                    "source": "本轮 22:58Z 板上只读 import 探测"},
        "coexistence_baseline": {"ldconfig_cudss": (d / "ldconfig-cudss-baseline.txt").read_text(encoding="utf-8").strip(),
                                 "ld_library_path": "空（板上 ssh 会话）",
                                 "ldd_trtexec": (d / "ldd-trtexec.txt").read_text(encoding="utf-8").strip().splitlines(),
                                 "ldd_trtexec_note": "/usr/src/tensorrt/bin/trtexec 运行期 dlopen libnvinfer/CUDA，ldd 只列 C 运行库；进程级库来源待装好 "
                                                     "torch 后由 `fastlayer_bench verify` 读 /proc/self/maps 记录"},
        "sub1_install": {"downloaded_kept": ["torch-2.9.1+cu130-cp312-cp312-manylinux_2_28_aarch64.whl（512,448,274 B，sha 6e7f84cb…fe04051f）",
                                             "torchvision-0.24.1-cp312-cp312-manylinux_2_28_aarch64.whl（7,823,607 B，sha 89743dce…97586fec）"],
                         "dry_run_resolution": [{k: r[k] for k in ("package", "version", "wheel_bytes", "sha256", "source")} for r in fetched],
                         "dry_run_fetched_discarded_bytes": sum(r["wheel_bytes"] or 0 for r in fetched if r["source"] == "pypi"),
                         "installed": [], "verify": "NOT_RUN（torch 未安装）", "stop_reason": SUB1_STOP_REASON,
                         "raw": [_raw_system(n) for n in ("sub1-download-torch.log", "sub1-dryrun.log", "sub1-dryrun-report.json",
                                                          "sub1-dryrun-fetched.json", "netdev-0.txt", "netdev-1a.txt", "netdev-1b.txt",
                                                          "netdev-2a.txt", "netdev-2b.txt", "netdev-3.txt", "du-0.txt", "du-3.txt", "df-0.txt", "df-3.txt")]},
    }
    document = common.read_json(common.evidence("env.json"))
    document["s1s2_system_stack"] = section
    common.write_json(common.evidence("env.json"), document)
    return section


def fastlayer_system() -> dict[str, Any]:
    """S1/S2（K1K3K4补跑B，系统栈）：SUB:1 下载额度将超，torch 未装成 → NOT_RUN(PATH_UNAVAILABLE(system-torch))；前轮原文进 history。"""
    existing = common.read_json(common.evidence("fastlayer.json"))
    history = list(existing.get("history", []))
    if existing.get("round") != ROUND_B:
        history.append({k: v for k, v in existing.items() if k not in ("history", "work_id")})
    document = {
        "work_id": common.WORK_ID,
        "round": ROUND_B,
        "S1": {"verdict": NOT_RUN_SYSTEM_TORCH,
               "reason": SUB1_STOP_REASON,
               "execution_stack": {"venv": common.SYSTEM_VENV, "runtime_stack_ref": "docs/evidence/P1-ENG-JET-001-env.json s1s2_system_stack"},
               "engines_exported": [], "export_attempts": [], "verify": "NOT_RUN（torch 未安装）",
               "rect_engine": "未尝试（同一原因）",
               "planned_protocol": existing.get("S1", {}).get("planned_protocol"),
               "ledger_ref": "docs/evidence/P1-ENG-JET-001-ledger.json dimensions.sub1_torch"},
        "S2": {"verdict": NOT_RUN_SYSTEM_TORCH, "reason": "依赖 S1 方形 TRT 引擎；同 S1。", "bins": []},
        "AC-2": "不满足（NOT_RUN 步骤对应 AC 不得记满足，§2.1）",
        "AC-3": "不满足（NOT_RUN）",
        "history": history,
    }
    common.write_json(common.evidence("fastlayer.json"), document)
    return document


S1S2_SYSTEM_C_DIR = common.OUT_DIR / "s1s2-system-c"
ROUND_C = "K1K3K4补跑C"
VERIFY_STOP_REASON = (
    "提案「needs_user」题 4（CLARIFY-B2）与决策记录「SUB:3 落实与安装方式合同解释」装后顺序：先 `fastlayer_bench verify`——"
    "`torch.cuda.get_arch_list()` 输出含 `sm_87`、板上 CUDA matmul 读回核对、与系统 TensorRT 10.16 共存核对点——不可用即停回用户、"
    "不在信封内换源。K1K3K4补跑C 按合同方式（逐个 `pip download --no-deps` 哈希锁定、离线按文件安装）装好官方 cu130 torch 2.9.1+cu130 / "
    "torchvision 0.24.1 后 verify：`get_arch_list()` = sm_80, sm_90, sm_100, sm_110, sm_120, compute_120，**不含 sm_87**（设备算力 8.7）；"
    "CUDA matmul 读回（fp32/fp16/全 1 精确）、torch 与系统 TensorRT 同进程建引擎并推理、无 torch 干净进程建引擎三项均通过。第一项未过 → "
    "verify 判不通过，按「任一失败即停下回用户改来源」停在 S1 之前：引擎导出 0 次、S1/S2 未运行；未换源、未改判据、未以 sm_80 二进制兼容"
    "自行放行。附加只读诊断（cuDNN conv2d fp32/fp16、torchvision CUDA nms、逐元素归约）均通过，仅供裁定参考，不构成 verify 通过。")


def _raw_c(name: str) -> dict[str, Any]:
    path = S1S2_SYSTEM_C_DIR / name
    return {"file": common.rel_project(path), "sha256": common.sha256_file(path), "bytes": path.stat().st_size}


def _netdev_rx(name: str, interface: str = "wlP1p1s0") -> int:
    for line in (S1S2_SYSTEM_C_DIR / name).read_text(encoding="utf-8").splitlines():
        if f"{interface}:" in line:
            return int(line.split(":", 1)[1].split()[0])
    raise ValueError(f"{name} 无 {interface}")


def system_stack_c() -> dict[str, Any]:
    """K1K3K4补跑C：系统 venv 安装记录、verify 结果与实跑栈（AC-2 修订 5），写入 -env.json `s1s2_system_stack_c`（补跑B 段原文保留）。"""
    d = S1S2_SYSTEM_C_DIR
    verify = common.read_json(d / "results-c" / "verify-summary.json")
    fetch_rows = [line.split("\t") for line in (d / "sub1-fetch.log").read_text(encoding="utf-8").splitlines() if line.startswith("PKG")]
    fetched = []
    for row in fetch_rows:
        fields = dict(item.split("=", 1) for item in row[4:])
        fetched.append({"package": row[1], "version": row[2], "bytes": int(fields["bytes"]), "expected_bytes": int(fields["expected_bytes"]),
                        "sha_ok": fields["sha_ok"] == "1", "rx_delta": int(fields["rx_delta"]), "start": fields["start"], "end": fields["end"]})
    rx = {n: _netdev_rx(f"netdev-{n}.txt") for n in ("0", "1a", "1b", "2a", "2b", "3")}
    record_bytes = {}
    for line in (d / "install-summary.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("RECORD "):
            _tag, name, version, size = line.split()
            record_bytes[name] = {"version": version, "installed_bytes": int(size)}
    du3 = (d / "du-3.txt").read_text(encoding="utf-8").split()
    section = {
        "round": ROUND_C,
        "note": "S1/S2 执行栈 = 板上系统 Python 3.12 的 --system-site-packages venv ~/eng-jet/sysvenv（复用系统 TensorRT 10.16）；本轮装好 torch 栈后 "
                "verify 未过（arch list 不含 sm_87），按合同停在 S1 之前。下列 runtime_stack 是 verify 进程内的实跑读数（AC-2 修订 5），"
                "与 S0 `readings`、容器栈 `s1s2_container_stack`、补跑B `s1s2_system_stack` 分列。",
        "install_method": {
            "contract": "提案决策记录「SUB:3 落实与安装方式合同解释」：禁 dry-run/--report；逐个 pip download --no-deps 核 sha256；--no-index --find-links 离线按文件安装",
            "sub1_download": "sysvenv/bin/pip download --no-deps --only-binary=:all: --no-cache-dir --progress-bar off --index-url https://pypi.org/simple "
                             "-d wheels/sub1 -r <单包 name==ver --hash=sha256:…>（逐包循环，取回前按 SUB:3 上限做额度预检，见 sub1-fetch.sh）",
            "sub1_install": "sysvenv/bin/pip install --no-index --find-links wheels/sub1 --no-cache-dir <torch 官方 cu130 轮子文件> <torchvision 官方 cu130 轮子文件>",
            "existing_reinstall": "sysvenv/bin/pip install --no-index --no-deps --no-cache-dir <ultralytics/lap/ultralytics-thop/opencv-python-headless 板上已有轮子>",
            "onnx": "pip download --no-deps 哈希锁定 onnx==1.18.0 + protobuf==6.31.1 至 wheels/，再 --no-index --find-links wheels 离线安装（AC-10 修订 2）",
            "env": "unset LD_LIBRARY_PATH；运行一律 YOLO_AUTOINSTALL=false YOLO_OFFLINE=true",
            "reused_kept_wheels": ["torch-2.9.1+cu130（512,448,274 B，sha 6e7f84cb…fe04051f）", "torchvision-0.24.1 cu130（7,823,607 B，sha 89743dce…97586fec）"],
        },
        "sub1_fetched": fetched,
        "sub1_fetched_total_bytes": sum(r["bytes"] for r in fetched),
        "sub1_fetched_all_sha_ok": all(r["sha_ok"] and r["bytes"] == r["expected_bytes"] for r in fetched),
        "network_rx_wlP1p1s0": {"snapshots": rx, "sub1_window_1a_1b": rx["1b"] - rx["1a"], "onnx_protobuf_2a_2b": rx["2b"] - rx["2a"],
                                "round_total_0_3": rx["3"] - rx["0"]},
        "installed_sub1": (d / "pip-install-torch.log").read_text(encoding="utf-8").strip().splitlines()[-1],
        "installed_other": {"existing_no_new_count": (d / "pip-install-existing5.log").read_text(encoding="utf-8").strip().splitlines()[-1],
                            "board_pip_new": (d / "pip-install-onnx.log").read_text(encoding="utf-8").strip().splitlines()[-1],
                            "installed_record_bytes": record_bytes},
        "pip_check": (d / "pip-check.txt").read_text(encoding="utf-8").strip().splitlines(),
        "pip_check_note": "ultralytics 声明依赖 nvidia-ml-py/opencv-python/polars/psutil 未装属 IR-15 已接受读法（惰性导入，S1/S2 路径不触达；须复核轮核对）；"
                          "pynacl→cffi 为系统包既有状况，与本项无关",
        "disk": {"du_eng_jet_before": int((d / "du-0.txt").read_text(encoding="utf-8").split()[0]), "du_after": dict(zip(du3[1::2], map(int, du3[0::2]))),
                 "df_before": (d / "df-0.txt").read_text(encoding="utf-8").strip().splitlines()[-1],
                 "df_after": (d / "df-3.txt").read_text(encoding="utf-8").strip().splitlines()[-1]},
        "coexistence": {"ldconfig_cudss_count_before": (d / "ldconfig-cudss-baseline.txt").read_text(encoding="utf-8").strip(),
                        "ld_library_path": verify.get("ld_library_path"),
                        "libraries_torch_trt_process": verify.get("libraries_torch_trt_process"),
                        "trt_with_torch": verify.get("trt_with_torch"), "trt_clean_process": verify.get("trt_clean_process"),
                        "reading": "torch 进程的 CUDA 数学库取 venv 内 pip 轮子（nvidia/cu13、cudnn、nccl），TensorRT 与驱动取系统库（libnvinfer 10.16.2、"
                                   "l4t libcuda）；干净进程（未 import torch）只映射系统库与 /usr/local/cuda-13.2 的 libnvrtc。未设 LD_LIBRARY_PATH，无串扰迹象。"},
        "verify": {"torch": verify.get("torch"), "torch_cuda": verify.get("torch_cuda"), "arch_list": verify.get("arch_list"),
                   "device": verify.get("device"), "capability": verify.get("capability"), "cuda_is_available": verify.get("cuda_is_available"),
                   "matmul": verify.get("matmul"), "summary": verify.get("summary"),
                   "verdict": "FAIL（sm_87_in_arch_list = false；其余三项通过）"},
        "runtime_stack": verify.get("runtime_stack"),
        "diagnostic_sm80_compat": {**common.read_json(d / "diag-sm80-compat.json"),
                                   "note": "verify 失败后的附加只读诊断（零下载、零模型），不构成 verify 通过，仅供 IR-16/needs_user 裁定参考；"
                                           "CUDA 文档的同主版本二进制兼容（sm_80 cubin 可在 8.x≥8.0 设备运行）是解释，不是本项判据"},
        "outside_eng_jet_writes": {"raw": (d / "outside-eng-jet-writes.txt").read_text(encoding="utf-8").strip().splitlines(),
                                   "note": "import ultralytics 在 ~/.config/Ultralytics/ 新建 settings.json（482 B）；CUDA 驱动 JIT 缓存 ~/.nv/ComputeCache 新增 545 文件"
                                           "（26,215,934 B）。二者在 ~/eng-jet 之外、不含本项数据或真值，保留未删；后续轮可用 YOLO_CONFIG_DIR / CUDA_CACHE_PATH 指到 ~/eng-jet 下"},
        "raw": [_raw_c(n) for n in ("sub1-deps.tsv", "sub1-fetch.sh", "sub1-fetch.log", "sub1-fetch-pip.log", "pypi-meta-onnx-protobuf.txt",
                                    "req-onnx.txt", "onnx-download.log", "preinstall-sizes.txt", "pip-install-torch.log", "pip-install-existing5.log",
                                    "pip-install-onnx.log", "install-summary.txt", "pip-list.txt", "pip-check.txt", "verify.log",
                                    "results-c/verify-summary.json", "results-c/verify-trt-only-summary.json", "diag-sm80-compat.json",
                                    "diag-sm80-compat.err", "outside-eng-jet-writes.txt", "netdev-0.txt", "netdev-1a.txt", "netdev-1b.txt",
                                    "netdev-2a.txt", "netdev-2b.txt", "netdev-3.txt", "du-0.txt", "du-3.txt", "df-0.txt", "df-3.txt",
                                    "ldconfig-cudss-baseline.txt", "t-start.txt", "t-install-start.txt", "t-install-end.txt", "t-end.txt")],
    }
    document = common.read_json(common.evidence("env.json"))
    document["s1s2_system_stack_c"] = section
    common.write_json(common.evidence("env.json"), document)
    return section


def fastlayer_system_c() -> dict[str, Any]:
    """S1/S2（K1K3K4补跑C）：torch 栈已装但 verify 未过（arch list 不含 sm_87）→ 停在 S1 前；沿用 IR-14 形状，待 IR-16 确认；前轮原文进 history。"""
    existing = common.read_json(common.evidence("fastlayer.json"))
    history = list(existing.get("history", []))
    if existing.get("round") != ROUND_C:
        history.append({k: v for k, v in existing.items() if k not in ("history", "work_id")})
    document = {
        "work_id": common.WORK_ID,
        "round": ROUND_C,
        "S1": {"verdict": NOT_RUN_SYSTEM_TORCH,
               "verdict_shape_note": "沿用 IR-3/IR-14 已接受形状 PATH_UNAVAILABLE(system-torch)（不自造 STOP 码；STOP 闭集无对应码）；本轮具体停因 = 装后 verify 未过，"
                                     "形状是否另记见交接「待裁定（补跑C）」IR-16",
               "reason": VERIFY_STOP_REASON,
               "execution_stack": {"venv": common.SYSTEM_VENV, "runtime_stack_ref": "docs/evidence/P1-ENG-JET-001-env.json s1s2_system_stack_c.runtime_stack"},
               "verify_ref": "docs/evidence/P1-ENG-JET-001-env.json s1s2_system_stack_c.verify",
               "engines_exported": [], "export_attempts": [], "rect_engine": "未尝试（同一原因）",
               "planned_protocol": existing.get("S1", {}).get("planned_protocol"),
               "ledger_ref": "docs/evidence/P1-ENG-JET-001-ledger.json dimensions.sub1_torch / board_pip"},
        "S2": {"verdict": NOT_RUN_SYSTEM_TORCH, "reason": "依赖 S1 方形 TRT 引擎；同 S1（verify 未过，未导出引擎）。", "bins": []},
        "AC-2": "不满足（NOT_RUN 步骤对应 AC 不得记满足，§2.1）",
        "AC-3": "不满足（NOT_RUN）",
        "history": history,
    }
    common.write_json(common.evidence("fastlayer.json"), document)
    return document


def compact_listing(manifest: Mapping[str, Any], raw_path: Path | None = None, prefixes: Sequence[str] = ("venv/", "sysvenv/")) -> dict[str, Any]:
    """板上清单入证据前压缩：第三方包树（pip 安装件，来源 = 账本逐轮子 sha）逐文件条目改为按前缀汇总（文件数、字节）；其余条目逐文件保留。
    违规判定不受影响（`violations`/`third_party_name_hits` 由 `assets.scan_manifest` 对全量清单先行算出）；全量清单原文另存 outputs 并记 sha。"""
    out = {k: v for k, v in manifest.items() if k != "listing"}
    kept, summary = [], {}
    for item in manifest.get("listing", []):
        prefix = next((p for p in prefixes if item["path"].startswith(p)), None)
        if prefix is None:
            kept.append(item)
            continue
        cell = summary.setdefault(prefix, {"files": 0, "bytes": 0})
        cell["files"] += 1
        cell["bytes"] += item.get("bytes") or 0
    out["listing"] = kept
    out["third_party_tree_summary"] = summary
    if raw_path is not None:
        out["listing_full_raw"] = {"file": common.rel_project(raw_path), "sha256": common.sha256_file(raw_path), "files": len(manifest.get("listing", []))}
    return out


def assets_round(manifest: Path, code_bundle: Path, board_sha: Path, zero_write: Path, key: str, note: str) -> dict[str, Any]:
    """补跑轮通用：在既有 -assets.json 上更新板上清单（AC-12）、代码更新件与板上逐文件 sha 复核（写入 `key`）、本轮受保护根零写入；前轮读数保留。"""
    document = common.read_json(common.evidence("assets.json"))
    previous = document.get("protected_roots_zero_write_previous_round")
    rounds = list(previous) if isinstance(previous, list) else ([previous] if previous else [])
    if document.get("protected_roots_zero_write"):
        rounds.append(document["protected_roots_zero_write"])
    document["protected_roots_zero_write_previous_round"] = rounds
    document["protected_roots_zero_write"] = common.read_json(zero_write)
    document["board_manifest_previous_round"] = {k: v for k, v in document["board_manifest"].items() if k != "listing"}
    document["board_manifest"] = compact_listing(common.read_json(manifest), Path(manifest))
    document["board_manifest"]["ac12_clean"] = not document["board_manifest"]["violations"]
    document[key] = {**common.read_json(code_bundle), "board_sha_check": common.read_json(board_sha), "note": note}
    common.write_json(common.evidence("assets.json"), document)
    return document


S1S2_SYSTEM_D_DIR = common.OUT_DIR / "s1s2-system-d"
ROUND_D = "K1K3K4补跑D"
#: AC-2 修订 6「读数标注」：S1/S2 全部 torch 相关读数须注明。
BINARY_COMPAT_NOTE = ("官方 cu130 torch 2.9.1 无 sm_87 原生 SASS，按同主版本二进制兼容（sm_80 cubin）运行；检测推理走原生支持 SM 87 的系统 "
                      "TensorRT 10.16（AC-2 修订 6）")
ENGINE_TAGS = ("640", "480x640")
TEGRA_RAM = re.compile(r"\bRAM (\d+)/(\d+)MB")
TEGRA_GR3D = re.compile(r"GR3D_FREQ (\d+)%(?:@\[?(\d+)\]?)?")


def tegrastats_ram(lines: Sequence[str]) -> dict[str, Any]:
    """tegrastats 原文行 → RAM used（MB，原文单位）与 GR3D 占用摘要（nearest-rank）。统一内存：Orin 的 RAM 即 CPU/GPU 共享。"""
    used, total, gr3d = [], None, []
    for line in lines:
        match = TEGRA_RAM.search(line)
        if match:
            used.append(int(match.group(1)))
            total = int(match.group(2))
        g = TEGRA_GR3D.search(line)
        if g:
            gr3d.append(int(g.group(1)))
    return {"samples": len(used), "ram_used_mb": common.summary(used, 0), "ram_total_mb": total, "gr3d_pct": common.summary(gr3d, 0),
            "unit_note": "tegrastats 原文单位 MB；Orin 统一内存（CPU/GPU 共享）"}


def s2_plan(square_s1_p95_ms: float | None) -> dict[str, Any]:
    """§2.1 S2：15 Hz 必测；方形引擎 S1 `update` p95 ≤ 33 ms 时加测 30 Hz。"""
    import tools.eng_jet.fastlayer_bench as bench  # noqa: PLC0415

    need_30 = square_s1_p95_ms is not None and square_s1_p95_ms <= bench.S2_30HZ_IF_P95_LE_MS
    return {"rates_hz": [15.0, 30.0] if need_30 else [15.0], "square_s1_update_p95_ms": square_s1_p95_ms,
            "rule": f"S1 p95 ≤ {bench.S2_30HZ_IF_P95_LE_MS} ms 时加测 30 Hz（§2.1 S2 字面）", "add_30hz": need_30}


def s2_overall(runs: Mapping[str, Mapping[str, Any] | None], plan: Mapping[str, Any]) -> dict[str, Any]:
    """S2 步骤 verdict：按计划顺序逐档；任一档 STOP → 该 STOP（停全部后续，未跑档记 NOT_RUN）；任一档 verdict 为空（ruling_needed）→ 空、交回裁定；
    计划内档缺读数（且无先前 STOP）→ 空、列 `missing`；全部 PASS → PASS。"""
    per_rate, missing = {}, []
    for hz in plan["rates_hz"]:
        key = f"{int(hz)}hz"
        run = runs.get(key)
        if run is None:
            missing.append(key)
            per_rate[key] = None
            continue
        per_rate[key] = run["verdict"]["verdict"]
    stops = [v for v in per_rate.values() if v and v.startswith("STOP(")]
    if stops:
        verdict: str | None = stops[0]
    elif missing or any(v is None for v in per_rate.values()):
        verdict = None
    else:
        verdict = "PASS"
    return {"verdict": verdict, "per_rate": per_rate, "missing": missing}


def _raw_d(name: str) -> dict[str, Any]:
    path = S1S2_SYSTEM_D_DIR / name
    return {"file": common.rel_project(path), "sha256": common.sha256_file(path), "bytes": path.stat().st_size}


def _read_d(name: str) -> str:
    return (S1S2_SYSTEM_D_DIR / name).read_text(encoding="utf-8", errors="replace")


def _maybe_json(name: str) -> dict[str, Any] | None:
    path = S1S2_SYSTEM_D_DIR / name
    return common.read_json(path) if path.is_file() else None


def _tegra_window(name: str) -> dict[str, Any] | None:
    path = S1S2_SYSTEM_D_DIR / name
    return tegrastats_ram(path.read_text(encoding="utf-8", errors="replace").splitlines()) if path.is_file() else None


def _engine_record(tag: str) -> dict[str, Any]:
    export = _maybe_json(f"results-d/export-{tag}-summary.json")
    s1 = _maybe_json(f"results-d/s1-det-assoc-v1-fp16-{tag}-summary.json")
    trt = _maybe_json(f"results-d/trtexec-det-assoc-v1-fp16-{tag}-summary.json")
    return {"export": export, "s1": s1,
            "trtexec": None if trt is None else {k: trt[k] for k in ("command", "returncode", "plan_sha256", "parsed", "log", "log_sha256", "metadata")
                                                 if k in trt}}


def fastlayer_system_d() -> dict[str, Any]:
    """S1/S2（K1K3K4补跑D，系统栈，AC-2 修订 6）：两版引擎导出、320 帧计时四分项、frozen-V 一致性、trtexec GPU 时间与 S2 热稳态；前轮原文进 history。"""
    existing = common.read_json(common.evidence("fastlayer.json"))
    history = list(existing.get("history", []))
    if existing.get("round") != ROUND_D:
        history.append({k: v for k, v in existing.items() if k not in ("history", "work_id")})
    engines = {tag: _engine_record(tag) for tag in ENGINE_TAGS}
    square = engines["640"]["s1"]
    s1_verdict = square["verdict"]["verdict"] if square else None
    s1 = {"verdict": s1_verdict, "verdict_basis": "方形引擎（imgsz=640）两分量（AC-2 / AC-2 修订 1）；矩形引擎同口径单独报告、不进 verdict（§2.1、AC-2 修订 4）",
          "square": square["verdict"] if square else None,
          "rect_480x640_not_in_verdict": engines["480x640"]["s1"]["verdict"] if engines["480x640"]["s1"] else None,
          "binary_compat_note": BINARY_COMPAT_NOTE,
          "engines": engines,
          "tegrastats_s1_window": _tegra_window("s1-tegrastats.log"),
          "planned_protocol": existing.get("S1", {}).get("planned_protocol"),
          "execution_stack": {"venv": common.SYSTEM_VENV, "env": _read_d("env.sh").strip().splitlines(),
                              "runtime_stack_ref": "engines.640.s1.runtime_stack（实跑读数，AC-2 修订 5）"}}
    plan = s2_plan(square["verdict"]["latency"]["update_p95_ms"] if square else None)
    runs = {}
    for hz in plan["rates_hz"]:
        summary = _maybe_json(f"results-d/s2-det-assoc-v1-fp16-640-{int(hz)}hz-summary.json")
        if summary is not None:
            summary = {**summary, "tegrastats": _tegra_window(f"s2-{int(hz)}hz-tegrastats.log")}
        runs[f"{int(hz)}hz"] = summary
    if s1_verdict is None:
        s2 = {"verdict": None, "reason": "S1 无读数", "plan": plan, "runs": runs}
    elif s1_verdict != "PASS":
        s2 = {"verdict": f"NOT_RUN(S1 {s1_verdict.replace('(', ' ').rstrip(')')})", "plan": plan, "runs": {}}
    else:
        overall = s2_overall(runs, plan)
        s2 = {"verdict": overall["verdict"], "overall": overall, "plan": plan, "runs": runs, "binary_compat_note": BINARY_COMPAT_NOTE}
    document = {"work_id": common.WORK_ID, "round": ROUND_D, "S1": s1, "S2": s2,
                "AC-2": "见 S1.verdict 与交接「AC-n 逐条证据指针」（本文件不自判 AC）",
                "AC-3": "见 S2.verdict 与交接「AC-n 逐条证据指针」（本文件不自判 AC）",
                "raw": [_raw_d(p.relative_to(S1S2_SYSTEM_D_DIR).as_posix()) for p in sorted(S1S2_SYSTEM_D_DIR.rglob("*"))
                        if p.is_file() and p.suffix in (".log", ".txt", ".json", ".sh", ".tsv")],
                "history": history}
    common.write_json(common.evidence("fastlayer.json"), document)
    return document


def system_stack_d() -> dict[str, Any]:
    """K1K3K4补跑D：执行环境（IR-16 (c) 环境变量）、装后清理（IR-16 (d)）、容器 venv 删除（「S1/S2 系统栈落实（B）」）、磁盘与 `~/eng-jet` 之外写入核查，
    写入 -env.json `s1s2_system_stack_d`（前轮各段原文保留）。"""
    d = S1S2_SYSTEM_D_DIR
    cleanup = [line.split("\t") for line in _read_d("cleanup-sub1-list.tsv").splitlines() if line.strip()]
    du = {}
    for name in ("du-0.txt", "du-1a.txt", "du-1b.txt", "du-venv-a.txt", "du-venv-b.txt", "du-3.txt"):
        if (d / name).is_file():
            du[name] = [line.split("\t") for line in _read_d(name).splitlines() if line.strip()]
    section = {
        "round": ROUND_D,
        "note": "S1/S2 在 ~/eng-jet/sysvenv 实跑（torch 2.9.1+cu130 / torchvision 0.24.1 / 系统 TensorRT 10.16）；" + BINARY_COMPAT_NOTE +
                "。实跑栈逐进程读数见 -fastlayer.json engines.*.s1.runtime_stack 与 export.runtime_stack。",
        "env": {"file": _raw_d("env.sh"), "lines": _read_d("env.sh").strip().splitlines(),
                "ir16c": "YOLO_CONFIG_DIR、CUDA_CACHE_PATH 指到 ~/eng-jet/home/ 下（IR-16 (c)）；YOLO_AUTOINSTALL=false YOLO_OFFLINE=true（IR-15）"},
        "wheels_sub1_cleanup": {"basis": "IR-16 (d)：S1 引擎导出前删除 ~/eng-jet/wheels/sub1/ 下全部已安装轮子文件；只删轮子、不动 sysvenv（未 pip uninstall）",
                                "files": [{"name": n, "bytes": int(b)} for n, b in cleanup], "count": len(cleanup),
                                "bytes": sum(int(b) for _n, b in cleanup), "remaining_entries": _read_d("cleanup-sub1-nonwheel.txt").strip().splitlines(),
                                "t": [_read_d("t-cleanup-start.txt").strip(), _read_d("t-cleanup-end.txt").strip()]},
        "container_venv_delete": _maybe_json("container-venv-delete.json") or {
            "deleted": False, "path": "~/eng-jet/venv",
            "reason": "决策记录「S1/S2 系统栈落实（B）」的删除条件是「系统栈 S1/S2 有读数后」；本轮 S1 STOP(FP16_BOX_DIVERGENCE)，S2 按停止总则未运行、无读数 → 条件未全满足，保留（101,751,706 B 继续计入板上磁盘维度）"},
        "du": du,
        "df": {n: _read_d(n).strip().splitlines()[-1] for n in ("df-0.txt", "df-3.txt") if (d / n).is_file()},
        "outside_eng_jet": {"baseline": _read_d("outside-baseline.txt").strip().splitlines(),
                            "after": _read_d("outside-after.txt").strip().splitlines() if (d / "outside-after.txt").is_file() else None,
                            "newer_than_marker": _read_d("outside-newer.txt").strip().splitlines() if (d / "outside-newer.txt").is_file() else None},
        "nvpmodel_q": _read_d("nvpmodel-q.txt").strip().splitlines(),
    }
    document = common.read_json(common.evidence("env.json"))
    document["s1s2_system_stack_d"] = section
    common.write_json(common.evidence("env.json"), document)
    return section


def assets_round_d(manifest: Path, board_sha: Path, zero_write: Path) -> dict[str, Any]:
    """K1K3K4补跑D：无代码上板（板上 S1/S2 运行件与本机 HEAD 逐文件 sha 一致）；冻结资产与 a7 帧 0..320 使用前板上逐文件复核；板上清单与零写入更新。"""
    document = common.read_json(common.evidence("assets.json"))
    previous = document.get("protected_roots_zero_write_previous_round")
    rounds = list(previous) if isinstance(previous, list) else ([previous] if previous else [])
    if document.get("protected_roots_zero_write"):
        rounds.append(document["protected_roots_zero_write"])
    document["protected_roots_zero_write_previous_round"] = rounds
    document["protected_roots_zero_write"] = common.read_json(zero_write)
    document["board_manifest_previous_round"] = {k: v for k, v in document["board_manifest"].items() if k != "listing"}
    # CUDA 驱动 JIT 缓存（IR-16 (c) 把 CUDA_CACHE_PATH 指到 ~/eng-jet/home/cuda-cache）同第三方包树按前缀汇总；全量清单原文另存记 sha。
    document["board_manifest"] = compact_listing(common.read_json(manifest), Path(manifest), prefixes=("venv/", "sysvenv/", "home/cuda-cache/"))
    document["board_manifest"]["ac12_clean"] = not document["board_manifest"]["violations"]
    document["round_d_pre_use_check"] = {**common.read_json(board_sha),
                                         "note": "K1K3K4补跑D 使用前复核（AC-11）：S1/S2 用到的代码/规格/freeze/.pt/frozen-V 13 件对本机 HEAD 同名文件 sha，"
                                                 "a7 帧 0..320 对 P1-ENG-FAST-002-dataset-frames 参照 sha；本轮零到板传输"}
    common.write_json(common.evidence("assets.json"), document)
    return document


S2_SYSTEM_E_DIR = common.OUT_DIR / "s2-system-e"
ROUND_E = "K1K3K4补跑E"
#: §2.1：用户对 S1 STOP 作「记录偏差并继续」裁定后，后续步骤标此记号并指向账本条目标题（AC-13）。
RESUMED_S1 = "RESUMED_AFTER_USER_RULING(S1)"
ALPHA_LEDGER_TITLE = "2026-10-03 P1-ENG-JET-001 — 用户选题 7 (α)：S1 STOP 记录偏差、以方形 FP16 引擎继续（supervisor 会话代录）"
#: AC-12 修订 2 / IR-17：只覆盖 CUDA 驱动 JIT 缓存（`CUDA_CACHE_PATH` 重定向）自生索引这一具名文件名；不泛化为 `home/` 豁免。
NAMED_DRIVER_CACHE_FILES = ("home/cuda-cache/index",)
TEGRA_TS = re.compile(r"^(\d\d)-(\d\d)-(\d{4}) (\d\d):(\d\d):(\d\d) ")
TEGRA_POWER = re.compile(r"\b(VDD_[A-Z_]+) (\d+)mW/")
TEGRA_TEMP = re.compile(r"\b([a-z0-9]+)@(-?\d+(?:\.\d+)?)C/")


def parse_utc_offset(text: str) -> int:
    """`date +%z` 原文（如 `-0400`）→ 秒。"""
    text = text.strip()
    sign = -1 if text.startswith("-") else 1
    digits = text.lstrip("+-")
    return sign * (int(digits[:2]) * 3600 + int(digits[2:4]) * 60)


def tegrastats_bins(lines: Sequence[str], t0_unix: float, utc_offset_s: int, bin_s: float = 300.0, n_bins: int = 6) -> list[dict[str, Any]]:
    """tegrastats 原文行（行首为板本地时间 `MM-DD-YYYY HH:MM:SS`，本地 = UTC + `utc_offset_s`）按 S2 的 5 min 格分格：
    各 `VDD_*` 瞬时功耗（mW，原文每项斜杠前的当前值）p50/max、各温区最高温（°C）、GR3D 占用 p50、RAM used 最大（MB）。窗外行不计。"""
    import calendar  # noqa: PLC0415

    cells: list[dict[str, Any]] = [{"power": {}, "temps": {}, "gr3d": [], "ram": [], "n": 0} for _ in range(n_bins)]
    for line in lines:
        match = TEGRA_TS.match(line)
        if not match:
            continue
        month, day, year, hour, minute, second = (int(g) for g in match.groups())
        t = calendar.timegm((year, month, day, hour, minute, second)) - utc_offset_s - t0_unix
        index = int(t // bin_s) if t >= 0 else -1
        if not 0 <= index < n_bins:
            continue
        cell = cells[index]
        cell["n"] += 1
        for rail, value in TEGRA_POWER.findall(line):
            cell["power"].setdefault(rail, []).append(int(value))
        for zone, value in TEGRA_TEMP.findall(line):
            cell["temps"].setdefault(zone, []).append(float(value))
        gr3d = TEGRA_GR3D.search(line)
        if gr3d:
            cell["gr3d"].append(int(gr3d.group(1)))
        ram = TEGRA_RAM.search(line)
        if ram:
            cell["ram"].append(int(ram.group(1)))
    out = []
    for index, cell in enumerate(cells):
        out.append({"bin": index, "t_from_s": index * bin_s, "t_to_s": (index + 1) * bin_s, "samples": cell["n"],
                    "vdd_mw": {rail: {"p50": common.nearest_rank(values, 0.5), "max": max(values)} for rail, values in sorted(cell["power"].items())},
                    "temps_c_max": {zone: max(values) for zone, values in sorted(cell["temps"].items())},
                    "gr3d_pct_p50": common.nearest_rank(cell["gr3d"], 0.5) if cell["gr3d"] else None,
                    "ram_used_mb_max": max(cell["ram"]) if cell["ram"] else None})
    return out


def ac12_split(violations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """AC-12 修订 2 / IR-17：机械扫描违规分两列——具名驱动缓存文件名命中（仅 `NAMED_DRIVER_CACHE_FILES` 的路径名命中）与真正违规（其余全部，
    含内容禁键命中）。不改写原 `violations` 与 `ac12_clean`。"""
    named = [dict(v) for v in violations if v.get("why") == "forbidden_path" and v.get("path") in NAMED_DRIVER_CACHE_FILES]
    true = [dict(v) for v in violations if not (v.get("why") == "forbidden_path" and v.get("path") in NAMED_DRIVER_CACHE_FILES)]
    return {"basis": "AC-12 修订 2 / IR-17（提案「待裁定」IR-17 行）：具名驱动缓存文件名命中单列、不记真值隔离违规；内容禁键命中仍记违规；"
                     "原扫描 violations 与 ac12_clean 原样保留",
            "named_driver_cache_filename_hits": named, "true_violations": true, "true_violation_count": len(true)}


def _e(name: str) -> Path:
    return S2_SYSTEM_E_DIR / name


def _raw_e(path: Path) -> dict[str, Any]:
    return {"file": common.rel_project(path), "sha256": common.sha256_file(path), "bytes": path.stat().st_size}


def _read_e(name: str) -> str | None:
    path = _e(name)
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None


def _lines_e(name: str) -> list[str] | None:
    text = _read_e(name)
    return None if text is None else text.strip().splitlines()


def fastlayer_system_e() -> dict[str, Any]:
    """S2（K1K3K4补跑E，用户题 7 (α) 后续跑）：复用补跑D 方形 FP16 引擎 15 Hz / 30 min；S1 保持补跑D 的 `STOP`（不重跑），S2 标
    `RESUMED_AFTER_USER_RULING(S1)` 并指向账本条目；前轮 S2 记录原文进 history。"""
    existing = common.read_json(common.evidence("fastlayer.json"))
    history = list(existing.get("history", []))
    if existing.get("round") != ROUND_E:
        history.append({"round": existing.get("round"), "S2": existing.get("S2"),
                        "note": "补跑E 前的 S2 记录原文；S1 读数仍为当前 S1（补跑D），不重复入 history"})
    s1 = dict(existing["S1"])
    s1["readings_round"] = existing["S1"].get("readings_round") or existing.get("round")
    s1["kept_note"] = (f"S1 保持 {s1['verdict']}（用户题 7 (α)：记录偏差并继续，verdict 不改写）；本轮不重跑 S1、不重导出、不换矩形引擎作对象；"
                       f"账本：{ALPHA_LEDGER_TITLE}")
    p95 = s1["square"]["latency"]["update_p95_ms"] if s1.get("square") else None
    plan = s2_plan(p95)
    utc_offset = parse_utc_offset(_read_e("board-utc-offset.txt") or "+0000")
    runs: dict[str, Any] = {}
    for hz in plan["rates_hz"]:
        path = _e(f"results-e/s2-det-assoc-v1-fp16-640-{int(hz)}hz-summary.json")
        if not path.is_file():
            runs[f"{int(hz)}hz"] = None
            continue
        summary = common.read_json(path)
        tegra = _lines_e(f"s2-{int(hz)}hz-tegrastats.log") or []
        summary = {**summary, "tegrastats": tegrastats_ram(tegra),
                   "tegrastats_bins": tegrastats_bins(tegra, summary["t0_unix"], utc_offset),
                   "tegrastats_utc_offset_s": utc_offset}
        runs[f"{int(hz)}hz"] = summary
    overall = s2_overall(runs, plan)
    log = _lines_e("s2-15hz.log") or []
    s2 = {"verdict": overall["verdict"], "resumed": RESUMED_S1, "resumed_ledger_title": ALPHA_LEDGER_TITLE, "round": ROUND_E,
          "overall": overall, "plan": plan, "runs": runs, "binary_compat_note": BINARY_COMPAT_NOTE,
          "detection_path": "系统 TensorRT 10.16 方形 FP16 引擎（补跑D 导出，身份见 S1.engines.640.export；本轮使用前板上 sha 复核见 engine_identity_check）",
          "engine_identity_check": common.read_json(_e("board-sha-e.json")).get("engine") if _e("board-sha-e.json").is_file() else None,
          "engine_sha_at_start": _lines_e("engine-sha-at-start.txt"),
          "trt_log_warnings": [line for line in log if "[W]" in line or "[E]" in line],
          "no_kernel_image": any("no kernel image" in line.lower() for line in log),
          "rule_note": "§2.1 S2 三项合取（AC-3 修订 1）：热降频 → STOP(THERMAL_THROTTLE)；丢帧 → STOP(FRAME_DROP)；末/首 5 min p95 > 1.2 倍 → "
                       "STOP(LATENCY_OVER)；30 Hz 加测条件为 S1 方形 p95 ≤ 33 ms（未达，plan.add_30hz=false）"}
    document = {"work_id": common.WORK_ID, "round": ROUND_E, "S1": s1, "S2": s2,
                "AC-2": "见 S1.verdict 与交接「AC-n 逐条证据指针」（本文件不自判 AC）",
                "AC-3": "见 S2.verdict 与交接「AC-n 逐条证据指针」（本文件不自判 AC）",
                "raw": existing.get("raw", []),
                "raw_e": [_raw_e(p) for p in sorted(S2_SYSTEM_E_DIR.rglob("*"))
                          if p.is_file() and p.suffix in (".log", ".txt", ".json", ".sh", ".tsv", ".out")],
                "history": history}
    common.write_json(common.evidence("fastlayer.json"), document)
    return document


def netdev_rx(lines: Sequence[str]) -> dict[str, int]:
    """`/proc/net/dev` 原文 → 接口收包字节。"""
    out = {}
    for line in lines:
        if ":" not in line or "|" in line:
            continue
        name, _, rest = line.partition(":")
        fields = rest.split()
        if fields:
            out[name.strip()] = int(fields[0])
    return out


def system_stack_e() -> dict[str, Any]:
    """K1K3K4补跑E：执行环境（AC-16 MPLCONFIGDIR 与 IR-16 (c) 重定向）、`~/eng-jet` 之外写入核查、容器 venv 删除（IR-19）、
    磁盘/网卡/开机时刻与 TRT 告警诊断，写入 -env.json `s2_system_stack_e`（前轮各段原文保留）。"""
    env_actual = _lines_e("env-actual.txt") or []
    actual = dict(line.split("=", 1) for line in env_actual if "=" in line)
    expected_mpl = "/home/jetson/eng-jet/home/mpl"
    net0, net1 = netdev_rx(_lines_e("netdev-0.txt") or []), netdev_rx(_lines_e("netdev-3.txt") or [])
    section = {
        "round": ROUND_E,
        "note": "S2 在 ~/eng-jet/sysvenv 实跑（torch 2.9.1+cu130 / torchvision 0.24.1 / 系统 TensorRT 10.16）；" + BINARY_COMPAT_NOTE +
                f"。本轮为用户题 7 (α) 后续跑，标 {RESUMED_S1}（账本：{ALPHA_LEDGER_TITLE}）。实跑栈逐进程读数见 -fastlayer.json S2.runs.15hz.runtime_stack。",
        "env": {"file": _raw_e(_e("env.sh")) if _e("env.sh").is_file() else None, "lines": _lines_e("env.sh"), "actual": env_actual,
                "ac16": {"MPLCONFIGDIR_expected": expected_mpl, "MPLCONFIGDIR_actual": actual.get("MPLCONFIGDIR"),
                         "match": actual.get("MPLCONFIGDIR") == expected_mpl,
                         "basis": "AC-16（来源 IR-18）：板上本项 Python 进程启动前显式设 MPLCONFIGDIR=$HOME/eng-jet/home/mpl"},
                "ir16c": {"YOLO_CONFIG_DIR": actual.get("YOLO_CONFIG_DIR"), "CUDA_CACHE_PATH": actual.get("CUDA_CACHE_PATH")},
                "ld_library_path_unset": actual.get("LD_LIBRARY_PATH_set", "") == ""},
        "outside_eng_jet": {"baseline": _lines_e("outside-baseline.txt"), "after": _lines_e("outside-after.txt"),
                            "newer_than_marker": _lines_e("outside-newer.txt"),
                            "basis": "AC-16 外部新写入核查：marker-start（S2 启动前）之后 ~ 下除 ~/eng-jet 外的新文件；既有外部缓存不删除"},
        "container_venv_delete": common.read_json(_e("container-venv-delete.json")) if _e("container-venv-delete.json").is_file() else {
            "deleted": False, "reason": "S2 无读数，IR-19 条件未满足"},
        "du": {n: _lines_e(n) for n in ("du-0.txt", "du-1.txt", "du-3.txt") if _e(n).is_file()},
        "df": {n: (_lines_e(n) or [""])[-1] for n in ("df-0.txt", "df-1.txt", "df-3.txt") if _e(n).is_file()},
        "netdev_rx_delta_bytes": {k: net1[k] - net0[k] for k in net0 if k in net1},
        "nvpmodel_q": _lines_e("nvpmodel-q.txt"),
        "boot": {"uptime": _lines_e("uptime.txt"),
                 "note": "板子在补跑D（00:35Z 收尾）之后、本轮之前重启过（uptime -s 为板本地时间）；功耗模式仍为 MAXN_SUPER"},
        "trt_plan_device_warning": {"log_lines": [line for line in (_lines_e("s2-15hz.log") or []) if "[W]" in line],
                                    "diagnostic": common.read_json(_e("trt-warning-diag.json")) if _e("trt-warning-diag.json").is_file() else None},
    }
    document = common.read_json(common.evidence("env.json"))
    document["s2_system_stack_e"] = section
    common.write_json(common.evidence("env.json"), document)
    return section


def assets_round_e(manifest: Path, board_sha: Path, zero_write: Path) -> dict[str, Any]:
    """K1K3K4补跑E：无代码上板（只下发 env.sh/run-s2.sh 两个运行脚本）；S2 用到的代码/冻结资产/a7 帧与方形引擎使用前板上逐文件复核；
    板上清单（容器 venv 删除后）按 AC-12 修订 2 分列；本轮受保护根零写入。"""
    document = common.read_json(common.evidence("assets.json"))
    previous = document.get("protected_roots_zero_write_previous_round")
    rounds = list(previous) if isinstance(previous, list) else ([previous] if previous else [])
    if document.get("protected_roots_zero_write"):
        rounds.append(document["protected_roots_zero_write"])
    document["protected_roots_zero_write_previous_round"] = rounds
    document["protected_roots_zero_write"] = common.read_json(zero_write)
    before = {k: v for k, v in document["board_manifest"].items() if k != "listing"}
    history = document.get("board_manifest_rounds")
    history = list(history) if isinstance(history, list) else []
    if document.get("board_manifest_previous_round"):
        history.append(document["board_manifest_previous_round"])
    document["board_manifest_rounds"] = history
    document["board_manifest_previous_round"] = before
    document["board_manifest"] = compact_listing(common.read_json(manifest), Path(manifest), prefixes=("venv/", "sysvenv/", "home/cuda-cache/"))
    document["board_manifest"]["ac12_clean"] = not document["board_manifest"]["violations"]
    document["board_manifest"]["ac12_split"] = {**ac12_split(document["board_manifest"]["violations"]),
                                                "original_scan_pointer": "board_manifest_previous_round（K1K3K4补跑D 原扫描，ac12_clean: false 原样保留）",
                                                "round": ROUND_E}
    document["round_e_pre_use_check"] = {**common.read_json(board_sha),
                                         "note": "K1K3K4补跑E 使用前复核（AC-11）：S2 用到的代码/规格/freeze/.pt/frozen-V 13 件对本机 HEAD 同名文件 sha，"
                                                 "a7 帧 0..320 沿用补跑D 期望（FAST-002 dataset-frames 参照），方形引擎对 -fastlayer.json S1.engines.640.export.sha256"}
    common.write_json(common.evidence("assets.json"), document)
    return document


SR_F_DIR = common.OUT_DIR / "sr-f"
ROUND_F = "K1K3K4补跑F"
RESUMED_S2 = "RESUMED_AFTER_USER_RULING(S2)"
ALPHA_PRIME_LEDGER_TITLE = "2026-10-03 P1-ENG-JET-001 — 用户选 S2 STOP 处置 (α′)：S2 记录偏差并继续，做原范围正式 SR（supervisor 会话代录）"
IR8_D5_LEDGER_TITLE = "2026-10-02 P1-ENG-JET-001 — supervisor 代拍：IR-8 断链手段代选软件定时断链（10 s、60 s，双通道与对时同断）"
KNOWN_HOSTS_LEDGER_TITLE = ("2026-10-03 P1-ENG-JET-001 — 用户授权把 Jetson 有线地址主机密钥写入 Mac mini `~/.ssh/known_hosts`，"
                            "并指示接受收工后直接派实现跑 S2（supervisor 会话代录）")
#: 正式 SR 各轮（K1K3K4补跑F）：标签 → (应答器, 角色)。f1-echo 为 STOP(RELAY_INTEGRITY) 返工轮，原样保留、不进结论小节。
SR_F_ROUNDS = {"f1-echo": ("echo", "rework"), "f2-echo": ("echo", "forward_clean"), "f3-track": ("track", "forward_clean"),
               "f4-track-drops": ("track", "disconnect")}
IR20_NOTE = ("IR-20 / AC-2 修订 7：方形引擎加载时同一 TensorRT `[W]` 引擎计划跨设备告警仍出现（本轮每次加载各 1 条，见 environment.trt_warnings）；"
             "告警原因及其对性能的影响未核实，不宣称告警无影响或引擎可跨设备；全程无 CUDA/TRT 不兼容错误、反序列化/推理失败或身份不符")
AC2_COMPAT_NOTE = ("AC-2 修订 6：" + "官方 cu130 torch 2.9.1 无 sm_87 原生 SASS，按同主版本二进制兼容（sm_80 cubin）运行；检测推理走原生支持 SM 87 的系统 "
                   "TensorRT 10.16（方形 FP16 引擎，补跑D 导出）")


def _sr_round_dir(label: str) -> Path:
    return SR_F_DIR / label


def replay_frames_check(label: str) -> dict[str, Any]:
    """本轮实际发布的 JPEG 字节（回放收据 image_sha256）逐帧对 FAST-002 dataset-frames 参照（AC-11：SR 回放帧）。"""
    from tools.eng_jet import assets  # noqa: PLC0415

    ref = assets.frame_reference()
    rows = common.read_jsonl(_sr_round_dir(label) / "desktop" / "replay-receipts.jsonl")
    bad = [r["source_index"] for r in rows
           if ref.get(f"{common.A7_FRAMES_REL}/{common.frame_name(r['source_index'], 'jpg')}") != r["image_sha256"]]
    return {"frames": len(rows), "source_index_range": [rows[0]["source_index"], rows[-1]["source_index"]] if rows else None,
            "sha_mismatch": bad, "match": not bad and len(rows) == 1500}


def _rc(path: Path) -> str | None:
    return path.read_text(encoding="utf-8").strip() if path.is_file() else None


def sr_round_f(label: str) -> dict[str, Any]:
    from tools.eng_jet import relay  # noqa: PLC0415

    base = _sr_round_dir(label)
    analysis = relay.analyze(base / "desktop", base / "board", base / "desktop" / "replay-receipts.jsonl")
    files = {}
    for sub in ("desktop", "board"):
        for path in sorted((base / sub).glob("*")):
            if path.is_file():
                files[f"{sub}/{path.name}"] = {"sha256": common.sha256_file(path), "bytes": path.stat().st_size}
    times = {name: _rc(base / f"{name}.txt") for name in ("t-board-launch", "t-desktop-start", "t-desktop-end")}
    times.update({f"board_{name}": _rc(base / "board" / f"{name}.txt") for name in ("t-start", "t-end")})
    return {"label": label, "responder": SR_F_ROUNDS[label][0], "role": SR_F_ROUNDS[label][1],
            "exit_codes": {"desktop_relay": _rc(base / "desktop" / "desktop-relay-rc.txt"), "replay": _rc(base / "desktop" / "replay-rc.txt"),
                           "board_relay": _rc(base / "board" / "board-relay-rc.txt"), "responder": _rc(base / "board" / "responder-rc.txt")},
            "times_utc": times, "replay_frames_check": replay_frames_check(label),
            "board_env_actual": (_rc(base / "board" / "env-actual.txt") or "").splitlines(),
            "board_outside_newer_than_marker": (_rc(base / "board" / "outside-newer.txt") or "").splitlines(),
            "analysis": analysis, "raw_dir": common.rel_project(base), "raw_files": files}


def _forward_ok(analysis: Mapping[str, Any]) -> bool:
    return (analysis["bundles_sent"] >= 1500 and analysis["completeness"] == 1.0 and analysis["order_violations"] == 0
            and analysis["latest_pointing_to_incomplete_bundle"] == 0 and analysis["board_sha_mismatch"] == 0)


def _forward_section(analysis: Mapping[str, Any]) -> dict[str, Any]:
    keys = ("bundles_sent", "bundles_complete_on_board", "completeness", "order_violations", "latest_pointing_to_incomplete_bundle",
            "pointer_refusals_incomplete", "board_sha_mismatch", "board_rejected_paths", "bundles_lost_in_flight",
            "bundles_partial_on_board_unpublished", "frame_id_gaps_on_board", "arrival_latency_ms_offset_corrected",
            "arrival_latency_ms_raw_unix_difference", "clock", "link_events", "sent_frame_id_range")
    section = {k: analysis[k] for k in keys}
    if "link_events_total" in analysis:  # R1-2：补丁后分析器给出全量计数；补丁前原始分析无此键，不补造
        section["link_events_total"] = analysis["link_events_total"]
    return section


def disconnect_pass(drops: Mapping[str, Any], exit_codes: Mapping[str, Any]) -> bool:
    """AC-6 断链轮通过线（复核 R1-4：自 `relay_doc_f` 提为具名纯函数，判据逐字不变）：无不完整包指向、无 sha 不符、恰两次断链且
    均在限内回稳、四进程退出码均为 `rc=0`、三方进程均有 stop 收据。"""
    disconnects = drops.get("disconnects") or []
    return (drops["latest_pointing_to_incomplete_bundle"] == 0 and drops["board_sha_mismatch"] == 0
            and all(d["recovery"].get("within_limit") for d in disconnects)
            and all(v == "rc=0" for v in exit_codes.values())
            and all(drops["process_stops"].values()) and len(disconnects) == 2)


def relay_doc_f() -> dict[str, Any]:
    """K1K3K4补跑F 正式 SR（有线）：forward（全程零链路事件轮）/ return（回声、真实两模式）/ disconnect（有意断链轮）结论小节；
    `tailscale_smoke` 原件逐字保留、不重算；f1-echo 返工轮（STOP(RELAY_INTEGRITY)）原样列于 rework_rounds、不进结论。"""
    existing = common.read_json(common.evidence("relay.json"))
    rounds = {label: sr_round_f(label) for label in SR_F_ROUNDS}
    clean = [label for label, (_resp, role) in SR_F_ROUNDS.items() if role == "forward_clean"]
    forward_rounds = {label: {**_forward_section(rounds[label]["analysis"]), "responder": rounds[label]["responder"],
                              "pass_line_100_0_0": _forward_ok(rounds[label]["analysis"])} for label in clean}
    forward_ok = all(v["pass_line_100_0_0"] for v in forward_rounds.values())
    echo, track = rounds["f2-echo"]["analysis"], rounds["f3-track"]["analysis"]
    ret = {
        "echo": {"round": "f2-echo", **echo["return_echo"], "capture_age_s": echo["capture_age_s"],
                 "capture_age_s_offset_corrected": echo["capture_age_s_offset_corrected"], "load_elapsed_s": echo["load_elapsed_s"],
                 "returns_by_path": echo["returns_by_path"]},
        "track": {"round": "f3-track", **track["return_track"], "capture_age_s": track["capture_age_s"],
                  "capture_age_s_offset_corrected": track["capture_age_s_offset_corrected"], "load_elapsed_s": track["load_elapsed_s"],
                  "returns_by_path": track["returns_by_path"],
                  "init_source_basis": "init 框 = 板上首帧（frame 0）检测器自身 target 类（类号 1）最高分框；不读真值、不用 S1/S2 离线用户框替身（AC-5、IR-5）",
                  "note": "真实 TrackLoop 只在 ok 帧写观测：插件第 0…29 帧 TRACKING，第 30 帧起 bound_track_unmatched → bound_track_removed、compat 模式不改绑，"
                          "故回程观测 n = 29（不含 init 帧），统计力弱、只作描述；端到端含 init 冷启动追帧"},
        "T_STALL_S": 3.0, "T_pub_s": 0.4,
    }
    drops = rounds["f4-track-drops"]["analysis"]
    disconnect_ok = disconnect_pass(drops, rounds["f4-track-drops"]["exit_codes"])
    disconnect = {"round": "f4-track-drops", "responder": "track",
                  "method": f"软件定时断链（双通道 TCP 与对时 UDP 同断；DesktopRelay --drops 60:10,160:60），依据 IR-8 / D5 代拍：账本「{IR8_D5_LEDGER_TITLE}」；"
                            "未以停回放、暂停应答或杀进程替代",
                  "drops": drops["disconnects"], "process_stops": drops["process_stops"], "exit_codes": rounds["f4-track-drops"]["exit_codes"],
                  "forward_in_disconnect_round": _forward_section(drops),
                  "trackloop_semantics": drops["return_track"]["terminal"], "post_terminal_frames": drops["return_track"]["post_terminal_frames"],
                  "pass_line": "两侧不崩溃、无不完整包、恢复后 60 s 内到达时延回到稳态（回稳读法预注册 relay.RECOVERY_*）",
                  "pass_line_met": disconnect_ok,
                  "note": "完整率在本轮分列、不进 forward 结论（IR-8 / AC-4 修订 1）；断链期间不补发过期帧（of_which_sent 仅重连时的当前 latest）"}
    verdict = "PASS" if forward_ok and disconnect_ok else "STOP(RELAY_INTEGRITY)"
    tags = [RESUMED_S1, RESUMED_S2]
    document = {
        "work_id": common.WORK_ID, "step": "SR", "round": ROUND_F,
        "verdict": verdict, "verdict_basis": "§2.1 SR 通过线：forward 两轮（回声 f2、真实 f3）包完整率 100% / 顺序违反 0 / 指向不完整包 0；"
                                             "disconnect 轮两侧不崩溃、无不完整包、两次断链均 60 s 内回稳；时延只报告、不设门；capture_age_s 超 T_stall 不 STOP（K1 发现）",
        "resumed": tags, "resumed_ledger_titles": {RESUMED_S1: ALPHA_LEDGER_TITLE, RESUMED_S2: ALPHA_PRIME_LEDGER_TITLE},
        "kept_verdicts": {"S1": "STOP(FP16_BOX_DIVERGENCE)", "S2": "STOP(FRAME_DROP)", "note": "S1/S2 原 verdict 与负结果保留，未重跑"},
        "link": {"formal": "Mac mini 192.168.8.1 ↔ Jetson 192.168.8.2 有线直连（§7 (h) 答复；CLARIFY 表 10-02 设备行）",
                 "ssh": f"jetson@192.168.8.2，BatchMode=yes、StrictHostKeyChecking=yes（主机密钥依账本「{KNOWN_HOSTS_LEDGER_TITLE}」）",
                 "board_bind": "板侧中继 bind 192.168.8.2:47811",
                 "unexpected_link_events": {"board_kernel": (_rc(SR_F_DIR / "board-link-events.txt") or "").splitlines(),
                                            "note": "16:52:11–16:52:14Z 板侧 enP8p1s0 物理链路 down/up 一次（3 s），发生在 f3 板侧中继结束（16:52:04Z）之后、f4 开始之前，"
                                                    "不在任何 SR 数据窗内；同时段一次 ssh 连接超时。原因未查明（未改任何网络设置）"},
                 "board_time_sync": (_rc(SR_F_DIR / "board-timesync.txt") or "").splitlines()},
        "forward": {"verdict": "PASS" if forward_ok else "STOP(RELAY_INTEGRITY)", "rounds": forward_rounds,
                    "denominator": "发送端实际送出包数；分子 = 板端完整发布且 sha 一致的对应包数；不扣在途整包丢失（AC-4 修订 1）"},
        "return": ret,
        "disconnect": {**disconnect, "verdict": "PASS" if disconnect_ok else "STOP(RELAY_INTEGRITY)"},
        "rework_rounds": [{"label": "f1-echo", "verdict": "STOP(RELAY_INTEGRITY)",
                           "cause": "桌面机运行目录残留 10-02 冒烟会话的 latest.json（frame 1499），桌面机中继启动即转发；板侧发布后本会话帧 0…1499 全部按顺序违反被拒"
                                    "（板侧顺序守卫与不完整包守卫按设计生效，未发布不完整包）",
                           "rework": "DesktopRelay 跳过 published_unix_s 早于本进程启动 5 s 以上的指针（tests/test_eng_jet_relay.py DesktopStalePointer 修前红、修后绿）；"
                                     "编排在启动桌面机中继前清空运行目录",
                           "analysis_note": "分析器按 frame_id 汇总：旧会话同号指针被计为 1 个完整包，故 completeness 显示 1/1501；本会话帧实际完整发布 0/1500",
                           "summary": {k: rounds["f1-echo"]["analysis"][k] for k in ("bundles_sent", "bundles_complete_on_board", "completeness",
                                                                                     "order_violations", "latest_pointing_to_incomplete_bundle")},
                           "raw_dir": rounds["f1-echo"]["raw_dir"]}],
        "rounds_raw": {label: {k: v for k, v in r.items() if k != "analysis"} for label, r in rounds.items()},
        "environment": {"binary_compat_note": AC2_COMPAT_NOTE, "ir20": IR20_NOTE,
                        "trt_warnings": {label: [line for line in (_rc(_sr_round_dir(label) / "board" / "responder.out") or "").splitlines() if "[W]" in line]
                                         for label in SR_F_ROUNDS if SR_F_ROUNDS[label][0] == "track"},
                        "runtime_stack": next((json.loads(line)["runtime_stack"] for line in (_rc(_sr_round_dir("f3-track") / "board" / "track-receipts.jsonl") or "").splitlines()
                                               if '"ev": "ready"' in line), None),
                        "ac2_compat": "不据 SR 读数推定 5 Hz 无丢帧、合同或部署通过；15 Hz S2 丢帧结论不变"},
        "ac12_note": "真实 TrackLoop 写出的 gimbal_command.json 含冻结控制协议字段 target_world_m，命中 AC-12 内容禁键 target_*，按 IR-17 现行读法记真正违规，交 IR-22",
        "tailscale_smoke": existing["tailscale_smoke"],
        "implementation_test": "tests/test_eng_jet_relay.py::LoopbackTwoProcess::test_atomic_publish_order；tests/test_eng_jet_track_responder.py（进程内回环 + 软件定时断链）",
        "history": list(existing.get("history", [])) + [{"round": existing.get("round") or "K1K3K4（首派）", "verdict": existing.get("verdict"),
                                                        "forward": existing.get("forward"), "return": existing.get("return"), "disconnect": existing.get("disconnect"),
                                                        "note": "正式 SR 前的答复前记录原文（NOT_RUN(待用户 (h))）；保留为历史"}],
    }
    common.write_json(common.evidence("relay.json"), document)
    return document


def system_stack_f() -> dict[str, Any]:
    """K1K3K4补跑F：AC-16 环境（每轮板上 Python 进程启动前）、~/eng-jet 外新写入、板上读数、应答器预检。"""
    expected_mpl = "/home/jetson/eng-jet/home/mpl"
    rounds = {}
    for label in SR_F_ROUNDS:
        actual_lines = (_rc(_sr_round_dir(label) / "board" / "env-actual.txt") or "").splitlines()
        actual = dict(line.split("=", 1) for line in actual_lines if "=" in line)
        rounds[label] = {"actual": actual_lines, "MPLCONFIGDIR_match": actual.get("MPLCONFIGDIR") == expected_mpl,
                         "YOLO_CONFIG_DIR": actual.get("YOLO_CONFIG_DIR"), "CUDA_CACHE_PATH": actual.get("CUDA_CACHE_PATH"),
                         "yolo_offline": (actual.get("YOLO_AUTOINSTALL"), actual.get("YOLO_OFFLINE")),
                         "ld_library_path_unset": actual.get("LD_LIBRARY_PATH_set", "") == "",
                         "outside_newer_than_marker": (_rc(_sr_round_dir(label) / "board" / "outside-newer.txt") or "").splitlines()}
    section = {
        "round": ROUND_F,
        "note": "正式 SR：板侧中继/回声/真实应答器均以 ~/eng-jet/sysvenv/bin/python 运行（AC-16 环境由 env.sh 在每个进程启动前设定）；" + AC2_COMPAT_NOTE +
                f"；标 {RESUMED_S1}（账本：{ALPHA_LEDGER_TITLE}）与 {RESUMED_S2}（账本：{ALPHA_PRIME_LEDGER_TITLE}）。",
        "env_script": {"file": _raw_e(SR_F_DIR / "env.sh"), "run_script": _raw_e(SR_F_DIR / "run-sr.sh")},
        "ac16": {"MPLCONFIGDIR_expected": expected_mpl, "rounds": rounds,
                 "all_match": all(r["MPLCONFIGDIR_match"] and r["ld_library_path_unset"] for r in rounds.values()),
                 "outside_basis": "每轮 marker-start（板上 Python 进程启动前）之后 ~ 下除 ~/eng-jet 外的新文件；唯一命中 ~/.local/state/wireplumber/restore-stream "
                                  "为 ssh 登录启动的用户会话服务写入（IR-18 已记同一来源），非本项进程；既有外部缓存不删除"},
        "preflight": {"label": "应答器预检（引擎身份复核 + 加载，无帧，4 s）", "dir": "~/eng-jet/logs/sr-f/preflight",
                      "result": "engine_identity_ok；ready model_load_s 5.338；NO_FRAME（预期，未进入任何 SR 轮）"},
        "board_post": (_rc(SR_F_DIR / "board-post.txt") or "").splitlines(),
        "board_link_events": (_rc(SR_F_DIR / "board-link-events.txt") or "").splitlines(),
        "board_time_sync": (_rc(SR_F_DIR / "board-timesync.txt") or "").splitlines(),
    }
    document = common.read_json(common.evidence("env.json"))
    document["sr_system_stack_f"] = section
    common.write_json(common.evidence("env.json"), document)
    return section


def assets_round_f(manifest: Path, board_sha: Path, zero_write: Path, bundle: Path) -> dict[str, Any]:
    """K1K3K4补跑F：SR 到板件（逐文件 sha）、使用前板上 30 件复核（含方形引擎）、SR 回放帧逐帧参照复核、板上清单（AC-12 修订 2 分列）、受保护根零写入。"""
    document = common.read_json(common.evidence("assets.json"))
    previous = document.get("protected_roots_zero_write_previous_round")
    rounds = list(previous) if isinstance(previous, list) else ([previous] if previous else [])
    if document.get("protected_roots_zero_write"):
        rounds.append(document["protected_roots_zero_write"])
    document["protected_roots_zero_write_previous_round"] = rounds
    document["protected_roots_zero_write"] = common.read_json(zero_write)
    before = {k: v for k, v in document["board_manifest"].items() if k != "listing"}
    history = document.get("board_manifest_rounds")
    history = list(history) if isinstance(history, list) else []
    if document.get("board_manifest_previous_round"):
        history.append(document["board_manifest_previous_round"])
    document["board_manifest_rounds"] = history
    document["board_manifest_previous_round"] = before
    document["board_manifest"] = compact_listing(common.read_json(manifest), Path(manifest),
                                                 prefixes=("venv/", "sysvenv/", "home/cuda-cache/", "runtime/sr-f/"))
    document["board_manifest"]["summary_prefix_note"] = ("third_party_tree_summary 另含本轮正式 SR 板上镜像运行目录 runtime/sr-f/（中继镜像帧与回程文件，按前缀汇总；"
                                                         "违规判定已在全量清单上先行算出，全量原文见 listing_full_raw）。f1-echo 全部帧被拒发布、f4 断链前帧在重连后不再被修剪，"
                                                         "故镜像文件数多于 retain 128（中继修剪只覆盖当前连接内收到且已发布后的旧帧）")
    document["board_manifest"]["ac12_clean"] = not document["board_manifest"]["violations"]
    split = ac12_split(document["board_manifest"]["violations"])
    document["board_manifest"]["ac12_split"] = {
        **split, "original_scan_pointer": "board_manifest_previous_round（K1K3K4补跑E 扫描）与 board_manifest_rounds；ac12_clean: false 原样保留",
        "round": ROUND_F,
        "new_true_violations_note": "本轮新增的真正违规均为内容禁键命中：runtime/sr-f/{f3-track,f4-track-drops}/gimbal_command.json 的冻结控制协议字段 "
                                    "target_world_m（controller/gimbal_entry.look_at 写出的 look-at 世界点，由检测框几何求得，非真值）；按 IR-17「内容禁键命中仍记违规」"
                                    "现行读法如实记录，不删除、不改名绕扫描，读法交 IR-22"}
    document["bundle_sr_f"] = common.read_json(bundle)
    document["round_f_pre_use_check"] = {**common.read_json(board_sha),
                                         "note": "K1K3K4补跑F 使用前复核（AC-11）：SR 到板件 27 件对本机开工提交同名文件 sha、冻结 last.pt/freeze 2 件对本机、方形引擎对 "
                                                 "-fastlayer.json S1.engines.640.export.sha256（运行时解析）；真实应答器每轮开跑前另行复核引擎 sha（track-receipts engine_identity_ok）"}
    document["round_f_sr_frames"] = {label: replay_frames_check(label) for label in SR_F_ROUNDS}
    common.write_json(common.evidence("assets.json"), document)
    return document


def relay_doc(smoke_dir: Path | None) -> dict[str, Any]:
    from tools.eng_jet import relay  # noqa: PLC0415

    smoke: dict[str, Any] = {"run": False}
    if smoke_dir is not None:
        smoke_dir = Path(smoke_dir)
        analysis = relay.analyze(smoke_dir / "desktop", smoke_dir / "board", smoke_dir / "desktop" / "replay-receipts.jsonl")
        meta = common.read_json(smoke_dir / "smoke-meta.json") if (smoke_dir / "smoke-meta.json").exists() else {}
        files = {}
        for sub in ("desktop", "board"):
            for path in sorted((smoke_dir / sub).glob("*.jsonl")):
                files[f"{sub}/{path.name}"] = {"sha256": common.sha256_file(path), "bytes": path.stat().st_size}
        smoke = {"run": True, "mode": "TAILSCALE_SMOKE", "non_conclusion": True,
                 "note": "仅用于验证中继实现；读数不进 forward/return/disconnect 结论，不支撑 AC-4…6，不代表任何链路时延（§3.2、§6 不可推出）",
                 "responder": "(a) 回声（零模型）；(b) 真实 TrackLoop + TRT 插件未跑（S1 NOT_RUN(PATH_UNAVAILABLE(system-torch))）",
                 **meta, "analysis": analysis, "raw_receipts": files, "raw_dir": common.rel_project(smoke_dir)}
    document = {
        "work_id": common.WORK_ID,
        "step": "SR",
        "verdict": NOT_RUN_H,
        "forward": {"verdict": NOT_RUN_H, "reason": "§7 (h) 已答复为有线直连/同交换机 + 固定 IP，但 10-02 用户告知尚未接好；正式轮不在 Tailscale 上跑"},
        "return": {"verdict": NOT_RUN_H, "reason": "同 forward"},
        "disconnect": {"verdict": NOT_RUN_H, "reason": "同 forward"},
        "tailscale_smoke": smoke,
        "implementation_test": "tests/test_eng_jet_relay.py::LoopbackTwoProcess::test_atomic_publish_order（本机双进程回环，零硬件）",
    }
    common.write_json(common.evidence("relay.json"), document)
    return document


def stage_b() -> list[str]:
    written = []
    for name, step, ac in (("vlm.json", "S3", "AC-7"), ("quant-equivalence.json", "S4", "AC-8"), ("coresidency.json", "S5", "AC-9")):
        common.write_json(common.evidence(name), {
            "work_id": common.WORK_ID, "step": step, "verdict": NOT_RUN_STAGE_B, ac: "不满足（NOT_RUN）",
            "reason": "§7 (n) 答复「先签阶段 A」；阶段 B 全部维度 0：零下载、零上板 VLM、零 609 行、零量化（提案决策记录「§5 阶段 A 信封与 §7 (h)(n) 答复落实」）",
            "board_vlm_queries": 0, "model_downloads": 0})
        written.append(name)
    return written


def assets_doc(local: Path, bundle: Path, manifest: Path, zero_write: Path | None = None, bundle_s1s2: Path | None = None,
               zero_write_previous: Path | None = None) -> dict[str, Any]:
    document = {**common.read_json(local), "bundle": common.read_json(bundle), "board_manifest": common.read_json(manifest)}
    if bundle_s1s2 is not None:
        document["bundle_s1s2"] = common.read_json(bundle_s1s2)
    if zero_write is not None:
        document["protected_roots_zero_write"] = common.read_json(zero_write)
    if zero_write_previous is not None:
        document["protected_roots_zero_write_previous_round"] = common.read_json(zero_write_previous)
    violations = document["board_manifest"]["violations"]
    document["board_manifest"]["ac12_clean"] = not violations
    common.write_json(common.evidence("assets.json"), document)
    return document


def assets_round_b(manifest: Path, code_bundle: Path, board_sha: Path, zero_write: Path) -> dict[str, Any]:
    """K1K3K4补跑B：在既有 -assets.json 上更新板上清单（AC-12）、代码更新件与板上逐文件 sha 复核、本轮受保护根零写入；前轮读数保留。"""
    document = common.read_json(common.evidence("assets.json"))
    previous = document.get("protected_roots_zero_write_previous_round")
    rounds = list(previous) if isinstance(previous, list) else ([previous] if previous else [])
    if document.get("protected_roots_zero_write"):
        rounds.append(document["protected_roots_zero_write"])
    document["protected_roots_zero_write_previous_round"] = rounds
    document["protected_roots_zero_write"] = common.read_json(zero_write)
    document["board_manifest_previous_round"] = {k: v for k, v in document["board_manifest"].items() if k != "listing"}
    document["board_manifest"] = common.read_json(manifest)
    document["board_manifest"]["ac12_clean"] = not document["board_manifest"]["violations"]
    document["bundle_s1s2_code_round_b"] = {**common.read_json(code_bundle), "board_sha_check": common.read_json(board_sha),
                                            "note": "冻结资产（last.pt、frozen-V、a7 帧 0..320）沿用 bundle_s1s2 已上板件，未重传"}
    common.write_json(common.evidence("assets.json"), document)
    return document


ROUND_FULL_SUITE = "K1K3K4全套"
#: IR-22 / AC-12 修订 4：只覆盖本轮真实 TrackLoop 写出的 gimbal_command.json 中冻结 look_at_world 协议字段（具名路径运行时从
#: ac12_split.true_violations 解析，不手写；不泛化为 runtime/**、gimbal 文件全内容或全部 target_*）。
IR22_NAMED_FIELD = "command.target_world_m"
IR22_SOURCE = ("真实 TrackLoop（condition follow）据检测框、帧位姿与显式地平面 box_ground_intersection → BridgePublisher.look_at → "
               "controller/gimbal_entry.look_at 写出的 look-at 世界点（控制输出，冻结协议 tethered-drone-control/v1 的 look_at_world 有限 x/y/z），"
               "非 smoke target_* 真值；packet 顶层键 protocol/channel/command_id/issued_unix_s/expires_after_s/command 与 command 键 mode/"
               "target_world_m 均不含其他禁键；独立复核仍须核实来源")
_IR22_PATH = re.compile(r"^\./runtime/sr-f/(?P<label>[^/]+)/gimbal_command\.json$")


def ir22_named_protocol_split(true_violations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """IR-22：把 true_violations 中具名的两条控制协议内容命中（真实应答器轮的 gimbal_command.json，内容禁键）单列；
    其余（含路径不符、非真实应答器轮、非内容禁键）仍留在真正隔离违规列。不改原扫描、不改 ac12_clean。"""
    named, remaining = [], []
    for violation in true_violations:
        match = _IR22_PATH.match(str(violation.get("path", "")))
        label = match.group("label") if match else None
        if (violation.get("why") == "forbidden_json_key" and label in SR_F_ROUNDS and SR_F_ROUNDS[label][0] == "track"):
            named.append({**dict(violation), "round": label, "field": IR22_NAMED_FIELD})
        else:
            remaining.append(dict(violation))
    return {"named_protocol_content_hits": named, "named_protocol_content_hit_count": len(named),
            "true_isolation_violations_excluding_named": remaining,
            "true_isolation_violation_count_excluding_named": len(remaining)}


def ir21_track_records_check(labels: Sequence[str] | None = None) -> dict[str, Any]:
    """IR-21：本机取回的真实应答器逐帧记录（track-records.jsonl）键 `state` 已由 RecordSink 改名 `loop_state`；用 AC-12 内容禁键正则复核。"""
    from tools.eng_jet import assets  # noqa: PLC0415

    out: dict[str, Any] = {}
    for label in labels or [k for k, (resp, _role) in SR_F_ROUNDS.items() if resp == "track"]:
        path = _sr_round_dir(label) / "board" / "track-records.jsonl"
        if not path.is_file():
            out[label] = {"file": common.rel_project(path), "present": False}
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        hits = [i for i, line in enumerate(lines) if assets.FORBIDDEN_KEY.search(line)]
        out[label] = {"file": common.rel_project(path), "present": True, "sha256": common.sha256_file(path), "lines": len(lines),
                      "lines_with_loop_state": sum('"loop_state"' in line for line in lines), "forbidden_key_hit_lines": len(hits)}
    return out


#: 补丁前 `relay.analyze` 对 `link_events` 的截断长度（复核 R1-2）；只用于判断无 `link_events_total` 的旧分析结果是否可能被截断。
LEGACY_LINK_EVENTS_CAP = 50


def _link_event_split(link_events: Sequence[Mapping[str, Any]], total: int | None = None) -> dict[str, Any]:
    """AC-4 修订 2：收据中的启动 connect 与收工 disconnect 原样保留；其余（中途重连、link_down、send_fail 等）计为传输中事件。

    读全量列表（R1-2）。`total` = 分析器给出的全量事件数（`link_events_total`）：列表短于它即视为截断；无 `total` 的旧分析结果
    长度达到旧截断长度 50 时同样不能排除截断。可能截断时 `in_transfer_event_count` 记 None（不从截断列表派生计数）。"""
    events = list(link_events)
    if total is not None:
        truncated: bool | None = int(total) > len(events)
    else:
        truncated = None if len(events) >= LEGACY_LINK_EVENTS_CAP else False
    startup = [e for e in events[:1] if e.get("ev") == "connect"]
    shutdown = [e for e in events[-1:] if e.get("ev") == "disconnect" and len(events) > 1]
    in_transfer = events[len(startup):len(events) - len(shutdown)]
    return {"raw": events, "startup_connect": startup, "shutdown_disconnect": shutdown, "in_transfer_events": in_transfer,
            "in_transfer_event_count": len(in_transfer) if truncated is False else None,
            "raw_count": len(events), "declared_total": total, "truncated": truncated}


def _send_window(label: str) -> dict[str, Any]:
    path = _sr_round_dir(label) / "desktop" / "relay-receipts.jsonl"
    rows = common.read_jsonl(path)
    sends = [r for r in rows if r.get("ev") == "send_bundle"]
    stop = [r for r in rows if r.get("ev") in ("disconnect", "stop")]
    utc = lambda unix: (dt.datetime.fromtimestamp(float(unix), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # noqa: E731
                        if unix is not None else None)
    return {"receipts": common.rel_project(path), "sends": len(sends),
            "first_send_utc": utc(sends[0]["unix"]) if sends else None, "last_send_utc": utc(sends[-1]["unix"]) if sends else None,
            "shutdown_events_utc": [{"ev": r["ev"], "utc": utc(r.get("unix"))} for r in stop]}


def contract_readings_relay(relay_document: Mapping[str, Any]) -> dict[str, Any]:
    """AC-4 修订 2 / AC-5 修订 1：从既有 -relay.json 与原始收据派生的分母、链路事件分列与风险（不改原小节与 verdict）。"""
    forward = {}
    for label, section in relay_document["forward"]["rounds"].items():
        forward[label] = {"link_events": _link_event_split(section.get("link_events", []), section.get("link_events_total")),
                          "send_window": _send_window(label),
                          "bundles_sent": section.get("bundles_sent"), "bundles_counted": section.get("bundles_sent"),
                          "count_window_shortened": False}
    ret = relay_document["return"]
    n = lambda section, key: (section.get(key) or {}).get("n")  # noqa: E731
    denominators = {
        "echo": {key: n(ret["echo"], key) for key in ("return_latency_ms", "end_to_end_ms", "capture_age_s", "load_elapsed_s")},
        "track": {key: n(ret["track"], key) for key in ("return_latency_ms", "end_to_end_ms", "frame_age_ms", "capture_age_s",
                                                         "load_elapsed_s", "processing_elapsed_s")},
    }
    return {
        "round": ROUND_FULL_SUITE,
        "basis": "提案决策记录「SR 与补跑F记录核对（2026-10-03）」AC-4 修订 2 / AC-5 修订 1 与「SUB:2 落实：§5 Mac 与 IR-9」执行范围 1；"
                 "只追加读法，不改 forward/return/disconnect 原小节、verdict、阈值或分母",
        "ac4_rev2": {"forward_rounds": forward,
                     "reading": "零链路事件轮 = 传输中无中途重连/link_down/send_fail；启动 connect 与收工 disconnect（OSError/TimeoutError）原样保留、"
                                "全部 1,500 个送包与对应发布计数，计数窗不缩短、不挑好区间；任何传输中意外事件仍按修订 1 原样报告",
                     "between_rounds_board_link_event": {
                         "pointer": "-env.json.sr_system_stack_f.board_link_events；-relay.json.link.unexpected_link_events；报告 §2f",
                         "reading": "16:52:11–16:52:14Z 板侧 enP8p1s0 物理 down/up 与同时段 ssh 超时在 f3 板侧结束（16:52:04Z）之后、f4 开始之前，"
                                    "不是从正式窗内剔除的坏区间；原因未明，不能据 SR PASS 外推链路长期稳定"}},
        "ac5_rev1": {"denominators": denominators,
                     "reading": "回程观测时延与逐帧年龄分别带真实分母：真实 TrackLoop 回程/端到端 n 与逐帧 frame_age_ms n 分列，不把全帧 n 当作成功写桥的 n；"
                                "第 0…29 帧 TRACKING、第 30 帧起绑定目标丢失且 compat 不改绑，回程观测不含 init 帧；init 为首帧检测器自身 target 类最高分框、"
                                "不是真值；原 AC-5 无回程 ≥1,500 的门，不新增样本门、不把 n=29 包装成长段统计或持续跟踪通过；正式数据不混入 Tailscale 冒烟"},
        "kept": {"S1": "STOP(FP16_BOX_DIVERGENCE)", "S2": "STOP(FRAME_DROP)", "SR": relay_document.get("verdict"),
                 "resumed": relay_document.get("resumed"), "resumed_ledger_titles": relay_document.get("resumed_ledger_titles"),
                 "ir20": IR20_NOTE},
    }


def sync_full_suite_round() -> dict[str, Any]:
    """K1K3K4全套 步骤 1：按 IR-21/22（AC-12 修订 3/4）分列具名命中、按 AC-4 修订 2 / AC-5 修订 1 同步读法；保留全部原扫描与指针。"""
    assets_document = common.read_json(common.evidence("assets.json"))
    split = assets_document["board_manifest"]["ac12_split"]
    reading = ir22_named_protocol_split(split["true_violations"])
    split["ir21_ir22_reading"] = {
        "round": ROUND_FULL_SUITE,
        "basis": "提案「待裁定」IR-21（AC-12 修订 3）与 IR-22（AC-12 修订 4，解释修订 2）；只追加分列，不改原扫描",
        "kept_original": {"violations_pointer": "board_manifest.violations", "true_violation_count": split["true_violation_count"],
                          "ac12_clean": assets_document["board_manifest"]["ac12_clean"],
                          "original_scan_pointer": split.get("original_scan_pointer")},
        **reading,
        "named_source": IR22_SOURCE,
        "ir21_track_records": {"reading": "真实 TrackLoop 逐帧记录经 track_responder.RecordSink 把 state 改名 loop_state，仅此键改名、其他键值原样（IR-12 (c) 先例）；"
                                          "不豁免其他文件的 state 或真值字段",
                               "local_copies": ir21_track_records_check()},
        "claim_limit": "本分列不把 ac12_clean 改为 true、不宣称 AC-12 已验收；修订 1/2 的其他内容禁键仍按违规处理；隔离红线与受保护根零写入不变；"
                       "AC-12 是否满足由核对/独立复核判定",
    }
    common.write_json(common.evidence("assets.json"), assets_document)
    relay_document = common.read_json(common.evidence("relay.json"))
    relay_document["contract_readings_full_suite"] = contract_readings_relay(relay_document)
    common.write_json(common.evidence("relay.json"), relay_document)
    return {"named_protocol_content_hit_count": reading["named_protocol_content_hit_count"],
            "true_isolation_violation_count_excluding_named": reading["true_isolation_violation_count_excluding_named"],
            "true_violation_count_kept": split["true_violation_count"], "ac12_clean_kept": assets_document["board_manifest"]["ac12_clean"],
            "forward_in_transfer_events": {k: v["link_events"]["in_transfer_event_count"]
                                           for k, v in relay_document["contract_readings_full_suite"]["ac4_rev2"]["forward_rounds"].items()}}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("fastlayer")
    sub.add_parser("fastlayer-system")
    sub.add_parser("system-stack")
    sub.add_parser("system-stack-c")
    sub.add_parser("fastlayer-system-c")
    sub.add_parser("system-stack-d")
    sub.add_parser("fastlayer-system-d")
    sub.add_parser("system-stack-e")
    sub.add_parser("fastlayer-system-e")
    ae = sub.add_parser("assets-e")
    ae.add_argument("--manifest", type=Path, required=True)
    ae.add_argument("--board-sha", type=Path, required=True)
    ae.add_argument("--zero-write", type=Path, required=True)
    ad = sub.add_parser("assets-d")
    ad.add_argument("--manifest", type=Path, required=True)
    ad.add_argument("--board-sha", type=Path, required=True)
    ad.add_argument("--zero-write", type=Path, required=True)
    ac = sub.add_parser("assets-c")
    ac.add_argument("--manifest", type=Path, required=True)
    ac.add_argument("--code-bundle", type=Path, required=True)
    ac.add_argument("--board-sha", type=Path, required=True)
    ac.add_argument("--zero-write", type=Path, required=True)
    ab = sub.add_parser("assets-b")
    ab.add_argument("--manifest", type=Path, required=True)
    ab.add_argument("--code-bundle", type=Path, required=True)
    ab.add_argument("--board-sha", type=Path, required=True)
    ab.add_argument("--zero-write", type=Path, required=True)
    cs = sub.add_parser("container-stack")
    cs.add_argument("--image-digest", required=True)
    sub.add_parser("relay-f")
    sub.add_parser("sync-full-suite")
    sub.add_parser("system-stack-f")
    af = sub.add_parser("assets-f")
    af.add_argument("--manifest", type=Path, required=True)
    af.add_argument("--board-sha", type=Path, required=True)
    af.add_argument("--zero-write", type=Path, required=True)
    af.add_argument("--bundle", type=Path, required=True)
    r = sub.add_parser("relay")
    r.add_argument("--smoke", type=Path, default=None)
    sub.add_parser("stage-b")
    a = sub.add_parser("assets")
    a.add_argument("--local", type=Path, required=True)
    a.add_argument("--bundle", type=Path, required=True)
    a.add_argument("--manifest", type=Path, required=True)
    a.add_argument("--zero-write", type=Path, default=None)
    a.add_argument("--bundle-s1s2", type=Path, default=None)
    a.add_argument("--zero-write-previous", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.action == "fastlayer":
        result: Any = fastlayer()["S1"]["verdict"]
    elif args.action == "fastlayer-system":
        result = fastlayer_system()["S1"]["verdict"]
    elif args.action == "assets-b":
        doc = assets_round_b(args.manifest, args.code_bundle, args.board_sha, args.zero_write)
        result = {"ac12_clean": doc["board_manifest"]["ac12_clean"], "board_sha_all_match": doc["bundle_s1s2_code_round_b"]["board_sha_check"]["all_match"]}
    elif args.action == "system-stack-c":
        result = system_stack_c()["verify"]["summary"]
    elif args.action == "fastlayer-system-c":
        result = fastlayer_system_c()["S1"]["verdict"]
    elif args.action == "system-stack-d":
        result = {k: v for k, v in system_stack_d().items() if k in ("wheels_sub1_cleanup", "container_venv_delete")}
        result["wheels_sub1_cleanup"] = {k: result["wheels_sub1_cleanup"][k] for k in ("count", "bytes")}
    elif args.action == "fastlayer-system-d":
        doc = fastlayer_system_d()
        result = {"S1": doc["S1"]["verdict"], "S2": doc["S2"]["verdict"]}
    elif args.action == "system-stack-e":
        section = system_stack_e()
        result = {"ac16": section["env"]["ac16"], "container_venv_delete": {k: v for k, v in section["container_venv_delete"].items()
                                                                            if k in ("deleted", "files", "bytes", "reason")}}
    elif args.action == "fastlayer-system-e":
        doc = fastlayer_system_e()
        result = {"S1": doc["S1"]["verdict"], "S2": doc["S2"]["verdict"], "resumed": doc["S2"]["resumed"]}
    elif args.action == "assets-e":
        doc = assets_round_e(args.manifest, args.board_sha, args.zero_write)
        result = {"ac12_clean": doc["board_manifest"]["ac12_clean"], "true_violations": doc["board_manifest"]["ac12_split"]["true_violation_count"],
                  "board_sha_all_match": doc["round_e_pre_use_check"]["all_match"]}
    elif args.action == "assets-d":
        doc = assets_round_d(args.manifest, args.board_sha, args.zero_write)
        result = {"ac12_clean": doc["board_manifest"]["ac12_clean"], "board_sha_all_match": doc["round_d_pre_use_check"]["all_match"]}
    elif args.action == "assets-c":
        doc = assets_round(args.manifest, args.code_bundle, args.board_sha, args.zero_write, "bundle_s1s2_code_round_c",
                           "K1K3K4补跑C 代码更新件（开工提交）；冻结资产（last.pt、frozen-V、a7 帧 0..320）沿用 bundle_s1s2 已上板件，未重传；"
                           "本轮 verify 未过、S1 未运行，冻结资产未被读取")
        result = {"ac12_clean": doc["board_manifest"]["ac12_clean"], "board_sha_all_match": doc["bundle_s1s2_code_round_c"]["board_sha_check"]["all_match"]}
    elif args.action == "system-stack":
        result = system_stack()["sub1_install"]["dry_run_fetched_discarded_bytes"]
    elif args.action == "container-stack":
        result = container_stack(args.image_digest)["tensorrt_sm87"]
    elif args.action == "sync-full-suite":
        result = sync_full_suite_round()
    elif args.action == "relay-f":
        doc = relay_doc_f()
        result = {"verdict": doc["verdict"], "forward": doc["forward"]["verdict"], "disconnect": doc["disconnect"]["verdict"]}
    elif args.action == "system-stack-f":
        result = {"ac16_all_match": system_stack_f()["ac16"]["all_match"]}
    elif args.action == "assets-f":
        doc = assets_round_f(args.manifest, args.board_sha, args.zero_write, args.bundle)
        result = {"ac12_clean": doc["board_manifest"]["ac12_clean"], "true_violations": doc["board_manifest"]["ac12_split"]["true_violation_count"],
                  "board_sha_all_match": doc["round_f_pre_use_check"]["all_match"],
                  "sr_frames_match": {k: v["match"] for k, v in doc["round_f_sr_frames"].items()}}
    elif args.action == "relay":
        result = relay_doc(args.smoke)["tailscale_smoke"].get("analysis", {})
    elif args.action == "stage-b":
        result = stage_b()
    else:
        result = {"all_used_match": assets_doc(args.local, args.bundle, args.manifest, args.zero_write, args.bundle_s1s2,
                                                       args.zero_write_previous)["all_used_match"]}
    print(json.dumps(result, ensure_ascii=False)[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
