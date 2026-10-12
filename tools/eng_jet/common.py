"""公共件（纯标准库，板上与桌面机共用）：路径、受保护写入、哈希、nearest-rank 分位数、信封常量。

受保护写入（AC-12）：主树 `runtime/` 与数据根（缺省 `~/TetheredDroneTracking-full`，环境变量
`ENG_JET_DATA_ROOT` 可覆盖）结构性拒绝写入——本包对二者只读（a7 帧只读取）。桌面机运行目录是
`outputs/eng-jet/runtime-desktop/`，原始日志在 `outputs/eng-jet/P1-ENG-JET-001/`；板上只用 `~/eng-jet/`。

分位数一律 nearest-rank（合同 §2.1：p95 = 升序第 ⌈0.95·n⌉ 个值），每个分位数旁写分母 n。
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_jet import WORK_ID  # noqa: E402

DATA_ROOT = Path(os.environ.get("ENG_JET_DATA_ROOT", str(Path.home() / "TetheredDroneTracking-full"))).expanduser()
PROTECTED_ROOTS: tuple[Path, ...] = (PROJECT_ROOT / "runtime", DATA_ROOT)
OUT_ROOT = PROJECT_ROOT / "outputs" / "eng-jet"
OUT_DIR = OUT_ROOT / WORK_ID
RUNTIME_DESKTOP = OUT_ROOT / "runtime-desktop"
EVIDENCE_DIR = PROJECT_ROOT / "docs" / "evidence"

#: a7 序列的相对路径（事实 6）：数据根下；本机主树以同一相对路径只读存放（派发事实）。
A7_FRAMES_REL = "runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames"

BOARD_HOST = "Jetson"
#: 正式 SR 有线链路（提案「S2 处置选 (α′) 落实」：mini 192.168.8.1 ↔ Jetson 192.168.8.2）；主机密钥已由用户授权写入 known_hosts，
#: 一律 BatchMode + StrictHostKeyChecking=yes，不改 `~/.ssh/*`。
WIRED_BOARD_HOST = "jetson@192.168.8.2"
WIRED_BOARD_ADDR = "192.168.8.2"
SSH_OPTS = ("-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes")
BOARD_ROOT = "~/eng-jet"

#: §5 阶段 A 生效值（提案决策记录「§5 阶段 A 信封与 §7 (h)(n) 答复落实」）。
ENVELOPE_STAGE_A: dict[str, Any] = {
    "consuming": "no",
    "model_downloads": 0,
    "board_pip_packages_max": 8,
    "board_pip_bytes_max": 300 * 1000 * 1000,
    "quant_host_gpu_h": 0,
    "to_board_bytes_max": 100 * 1000 * 1000,
    "sr_round_bytes_max": 100 * 1000 * 1000,
    "sr_rounds_max": 5,
    "tailscale_smoke_rounds_max": 1,
    "board_wall_s_max": 8 * 3600,
    "engine_export_wall_s_max_each": 20 * 60,
    "board_vlm_queries": 0,
    "board_disk_bytes_max": 5 * 1000 * 1000 * 1000,
    "mac_pip": 0,
    "mac_models": 0,
    "mac_outputs_bytes_max": 2 * 1000 * 1000 * 1000,
    "system_settings": "read-only (no systemctl isolate, no nvpmodel -m, no jetson_clocks)",
    "unity_play": 0,
    "scenario_session_run_ids": 0,
    "training_gpu_h": 0,
    "model_api": 0,
    "public_release": "no",
}


#: SUB:1 追加额度（账本 2026-10-02「用户按申请值签发 torch/torchvision 下载与安装额度（官方 cu130 源；SUB:1…）」；
#: 提案「needs_user」题 4 CLARIFY-B2 版）：torch/torchvision 及其依赖，成功、失败与重试全部计入。板上磁盘维度生效值随之 ≤ 13 GB。
#: 下载字节上限经 SUB:3 由 ≤ 3.5 GB 改为 ≤ 6.5 GB（含已计；账本 2026-10-02「用户按推荐签发 SUB:3：torch 依赖下载上限 3.5 GB → 6.5 GB」；
#: 提案决策记录「SUB:3 落实与安装方式合同解释」），其余维度不变。
SUB1_REQUEST_ID = "P1-ENG-JET-001:b0a5f79c:SUB:1"
SUB3_REQUEST_ID = "P1-ENG-JET-001:b0a5f79c:SUB:3"
SUB3_LEDGER_TITLE = "2026-10-02 P1-ENG-JET-001 — 用户按推荐签发 SUB:3：torch 依赖下载上限 3.5 GB → 6.5 GB（supervisor 会话代录）"
SUB1_LEDGER_TITLE = ("2026-10-02 P1-ENG-JET-001 — 用户按申请值签发 torch/torchvision 下载与安装额度（官方 cu130 源；SUB:1；"
                     "supervisor 会话代录）")
ENVELOPE_SUB1: dict[str, Any] = {
    "source_index": "https://download.pytorch.org/whl/cu130",
    "deps_index": "https://pypi.org/simple",
    "pins": {"torch": "2.9.1+cu130", "torchvision": "0.24.1"},
    "packages_max": 32,
    "download_bytes_max": 6_500_000_000,
    "download_bytes_max_history": [{"value": 3_500_000_000, "source": "SUB:1 签发"}, {"value": 6_500_000_000, "source": "SUB:3 签发"}],
    "new_disk_bytes_max": 8_000_000_000,
    "board_disk_bytes_max_effective": 13_000_000_000,
}
#: SUB:2（提案决策记录「SUB:2 落实：§5 Mac 与 IR-9」，AC-10 修订 3）：仅 Mac mini 本机 CPU、停点全套一次内的模型加载；
#: 成功/失败/重试全部计入、各模型分别核对、不相互转用；未列名的模型（含 det-assoc 冻结检测器）为 0。
SUB2_REQUEST_ID = "P1-ENG-JET-001:b0a5f79c:SUB:2"
SUB2_LEDGER_TITLE = ("2026-10-03 P1-ENG-JET-001 — 用户按推荐签发 SUB:2：停点全套的 Mac 本机 CPU 模型额度（一次全套）"
                     "（supervisor 会话代录）")
ENVELOPE_SUB2: dict[str, Any] = {
    "machine": "Mac mini 本机 CPU",
    "full_suite_runs_max": 1,
    "model_loads_max": {"nanotrack": 4, "yoloe": 2, "dinov2": 2, "csrt": 2},
    "other_models_max": 0,
    "pip": 0,
    "downloads": 0,
    "new_models": 0,
    "not_covered": ["SR 重跑", "阶段 B", "§7 (i)–(m)", "S3–S5"],
}
#: SUB:5 A（提案决策记录「SUB:5 A 落实与 CPU 执行方案核对」AC-10 修订 5；「CPU-1 落实与下一实现范围」AC-10 修订 6）：在 SUB:2 同一次
#: （仍只一次）停点全套内追加 Mac mini 本机 CPU 的 det-assoc 冻结检测器加载/构造尝试 ≤ 2，`ResidentCarrierReplay` 两次零模型部分回放
#: 归本项（不扣 ACQ-001）；全套次数与 SUB:2 共用 `dimensions.mac.sub2.full_suite_runs`；不授权 MPS 推理。
SUB5_REQUEST_ID = "P1-ENG-JET-001:b0a5f79c:SUB:5"
SUB5_LEDGER_TITLE = ("2026-10-03 P1-ENG-JET-001 — 用户选 SUB:5 方案 A：停点全套内追加 det-assoc 检测器加载 ≤ 2 次、两次零模型部分回放归本项"
                     "（supervisor 会话代录）")
CPU1_LEDGER_TITLE = ("2026-10-03 P1-ENG-JET-001 — 用户选 SUB:5 CPU 执行方案 CPU-1：CarrierSelfTest 两例改用既存显式 CPU 构造参数"
                     "（supervisor 会话代录）")
ENVELOPE_SUB5: dict[str, Any] = {
    "machine": "Mac mini 本机 CPU（不授权 MPS 推理）",
    "det_assoc_loads_max": 2,
    "det_assoc_model": "config/det-assoc-v1.models.json 冻结 weights（ultralytics YOLO）",
    "partial_replays_max": 2,
    "partial_replay_frames_each": 60,
    "partial_replay_test": "tests/test_det_assoc_carrier.py::ResidentCarrierReplay::test_resident_carrier_matches_replay",
    "full_suite": "与 SUB:2 共用 dimensions.mac.sub2.full_suite_runs（≤ 1），不另立全套额度",
    "execution": "CPU-1：CarrierSelfTest 两例 DetAssocTracker(spec_path=SPEC, device=\"cpu\")",
    "acq_001": "两次部分回放不计入、不消费 P1-ENG-ACQ-001 信封，ACQ-001 暂停不变",
    "not_covered": ["MPS 推理", "第二次全套", "SR 重跑", "阶段 B", "§7 (i)–(m)", "S3–S5", "其他未列名模型"],
}
#: 系统栈 venv（提案决策记录「S1/S2 系统栈落实（B）」：`--system-site-packages` 复用系统 TensorRT 10.16）。
SYSTEM_VENV = f"{BOARD_ROOT}/sysvenv"
SYSTEM_TRTEXEC = "/usr/src/tensorrt/bin/trtexec"


def evidence(name: str) -> Path:
    return EVIDENCE_DIR / f"{WORK_ID}-{name}"


def rel_project(path: Path | str) -> str:
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return candidate.as_posix()


def _resolved(path: Path) -> Path:
    path = Path(path).expanduser()
    if path.exists():
        return path.resolve()
    parent = path.parent
    tail = [path.name]
    while not parent.exists() and parent != parent.parent:
        tail.insert(0, parent.name)
        parent = parent.parent
    return parent.resolve().joinpath(*tail)


def is_protected(path: Path | str, roots: Sequence[Path] | None = None) -> bool:
    target = _resolved(Path(path))
    for root in roots if roots is not None else PROTECTED_ROOTS:
        try:
            target.relative_to(_resolved(Path(root)))
        except ValueError:
            continue
        return True
    return False


def refuse_protected(path: Path | str, roots: Sequence[Path] | None = None) -> None:
    """AC-12：主树 `runtime/` 与数据根只读（结构性拒绝，不靠事后比对）。"""
    if is_protected(path, roots):
        raise PermissionError(f"只读根（AC-12）：拒绝写入 {path}")


def atomic_write_bytes(path: Path | str, payload: bytes, roots: Sequence[Path] | None = None, *, fsync: bool = True) -> Path:
    """临时文件（可选 fsync）+ `os.replace` 原子发布；受保护根拒绝。"""
    target = Path(path).expanduser()
    refuse_protected(target, roots)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    temporary = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            if fsync:
                os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_json(path: Path | str, value: Any) -> str:
    payload = json_bytes(value)
    atomic_write_bytes(path, payload)
    return sha256_bytes(payload)


def append_jsonl(path: Path | str, row: Mapping[str, Any]) -> None:
    target = Path(path).expanduser()
    refuse_protected(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    rows = []
    with Path(path).expanduser().open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_json(path: Path | str) -> Any:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).expanduser().open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nearest_rank(values: Iterable[float], q: float) -> float | None:
    """nearest-rank 分位数：升序第 ⌈q·n⌉ 个值（1 起）；空集 → None。"""
    ordered = sorted(float(v) for v in values)
    if not ordered:
        return None
    if not 0.0 < q <= 1.0:
        raise ValueError("q must lie in (0, 1]")
    rank = max(1, math.ceil(q * len(ordered) - 1e-12))
    return ordered[rank - 1]


def summary(values: Sequence[float], digits: int = 3) -> dict[str, Any]:
    """{n, p50, p95, max, min}（nearest-rank；n 为分母）。"""
    values = [float(v) for v in values]
    if not values:
        return {"n": 0, "p50": None, "p95": None, "max": None, "min": None}

    def r(x: float | None) -> float | None:
        return None if x is None else round(x, digits)

    return {
        "n": len(values),
        "p50": r(nearest_rank(values, 0.50)),
        "p95": r(nearest_rank(values, 0.95)),
        "max": r(max(values)),
        "min": r(min(values)),
    }


def a7_frames_dir(data_root: Path | None = None) -> Path:
    """a7 帧目录：数据根优先；本机无数据根时取主树同一相对路径（只读）。"""
    root = Path(data_root) if data_root is not None else DATA_ROOT
    candidate = root / A7_FRAMES_REL
    if candidate.is_dir():
        return candidate
    return PROJECT_ROOT / A7_FRAMES_REL


def require_scratch(path: Path | str) -> Path:
    """可清空的运行目录只允许在 `outputs/eng-jet/`、板上 `~/eng-jet/` 或系统临时目录下（且不在受保护根内）。"""
    target = _resolved(Path(path))
    refuse_protected(target)
    for root in (OUT_ROOT, Path(BOARD_ROOT), Path(tempfile.gettempdir())):
        try:
            target.relative_to(_resolved(Path(root)))
        except ValueError:
            continue
        if target != _resolved(Path(root)):
            return target
    raise PermissionError(f"运行目录只能在 outputs/eng-jet/、~/eng-jet/ 或临时目录下：{path}")


def frame_name(frame_id: int, suffix: str) -> str:
    return f"frame_{int(frame_id):010d}.{suffix}"


def disk_usage_bytes(root: Path) -> int:
    total = 0
    root = Path(root).expanduser()
    if not root.exists():
        return 0
    for directory, _dirs, files in os.walk(root):
        for name in files:
            path = Path(directory) / name
            if not path.is_symlink():
                total += path.stat().st_size
    return total
