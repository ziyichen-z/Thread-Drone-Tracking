#!/usr/bin/env python3
"""P1-ENG-ACQ-001 AC-21（B2）：`candidates` 后端的 Unity 主机本地预检 → 单宿主 `mac` 报告 + K 收据。

只在**运行 Unity 与 Python 会话的那台 Mac** 上、由用户本人执行（角色不远程代跑）：

  <PY> -m tools.eng_acq.candidates_preflight --runtime runtime \\
      --out-dir outputs/eng-acq/P1-ENG-ACQ-001/play-d1/k-receipt

口径（提案「candidates 后端接线窄范围修复 CLARIFY」逐字）：

* 实测对象 = 适配器本身：对 `CandidatesBackend.predict_one` 用合成历史行做两组无模型调用——
  `none`（查询帧没有 `tracked` 行）与 `tracked`（查询帧恰 8 个 `tracked` 行，即候选上限），
  每组 ≥ 100 次，单调钟（`time.perf_counter`）端到端墙钟；每组取最近秩 p95，`p95_s` 取两组较大值；
* 帧路径是合成的合法 `frame_<id>.jpg` 名，**不读图**（适配器只解析文件名里的帧号）；
* 不读取或回放序列、不启动 Unity/会话、不建 scenario/session/run ID、不加载权重、不调检测器/VLM；
* `hz` 与 `retained_frame_count` 取 `--runtime` 下**实际生效**的场景配置（`runtime/scenario_config.json`
  存在即整份使用，否则 `config/scenario.default.json`）；R/hz/后端/身份或报告变化即重新预检、重生成收据；
* 该 p95 只覆盖适配器转换，**不是**在线检测或整体 Play 时延，也不是成功保证。

写入只落 `--out-dir`：`candidates-mac-report.json`，以及 `verdict=OK` 时的 `candidates-k-receipt.json`
（`source_reports` 只有 `mac` 一项：报告路径 + 字节 SHA-256）。退出码：0 = 收据已写；6 = 报告 `FAIL`、未写收据。
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller.language_bridge import CANDIDATES_BACKEND, CANDIDATES_MODEL_FORM  # noqa: E402
from controller.language_loop import (  # noqa: E402
    CANDIDATES_IDENTITY,
    CANDIDATES_MIN_SAMPLES,
    K_PUB,
    CandidatesBackend,
    build_k_receipt,
    k_conf_of,
    k_ret_of,
    machine_name,
    nearest_rank_p95,
    qualifies,
    read_scenario,
)
from controller.language_selector import interpret, sha256_file  # noqa: E402
from controller.resident_core import TRACKED, ResidentCore, TrackRow  # noqa: E402

WORK_ID = "P1-ENG-ACQ-001"
REPORT_NAME = "candidates-mac-report.json"
RECEIPT_NAME = "candidates-k-receipt.json"
TRACKED_ROWS = CandidatesBackend.MAX_CANDIDATES
#: 合成帧号起点（非 0、非连续起点，与传感器 `frame_id` 语义一致；只用于文件名与历史键）。
FIRST_FRAME_ID = 1000


def _synthetic_rows(count: int) -> list[TrackRow]:
    """`count` 个互不重叠的 `tracked` 行（面积各异，排序确定）。"""
    rows = []
    for index in range(count):
        size = 0.04 + 0.005 * index
        x = 0.02 + 0.11 * index
        rows.append(TrackRow(index + 1, (x, 0.3, size, size), 0.9, 2, TRACKED))
    return rows


def measure_group(
    name: str,
    tracked_rows: int,
    samples: int,
    *,
    clock: Callable[[], float] = time.perf_counter,
) -> dict[str, Any]:
    """一组 `samples` 次 `predict_one`：每次先把合成行记入真实 `ResidentCore` 历史（不计时），再计时调用。"""
    backend = CandidatesBackend()
    core = ResidentCore()
    backend.bind_history(core.history)
    rows = _synthetic_rows(tracked_rows)
    expected = "none" if tracked_rows == 0 else ("unique" if tracked_rows == 1 else "ambiguous")
    expected_count = 0 if expected == "none" else min(tracked_rows, TRACKED_ROWS)
    durations: list[float] = []
    mismatches = 0
    for index in range(samples):
        frame_id = FIRST_FRAME_ID + index
        core.record(frame_id, {}, rows, [], [], index + 1)
        image_path = Path(f"frame_{frame_id:010d}.jpg")  # 合成名；适配器不读图
        started = clock()
        raw = backend.predict_one(f"preflight-{name}-{index}", image_path, "the car", False)
        durations.append(max(0.0, float(clock() - started)))
        selection = interpret(raw)
        if selection.status != expected or len(selection.candidates) != expected_count:
            mismatches += 1
    return {
        "tracked_rows": tracked_rows,
        "expected_status": expected,
        "sample_count": len(durations),
        "status_mismatches": mismatches,
        "p50_s": sorted(durations)[len(durations) // 2],
        "p95_s": nearest_rank_p95(durations),
        "max_s": max(durations),
        "samples_s": durations,
    }


def _git_head() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout.strip() or None


def build_report(runtime: Path, samples: int, *, clock: Callable[[], float] = time.perf_counter) -> dict[str, Any]:
    if samples < CANDIDATES_MIN_SAMPLES:
        raise ValueError(f"--samples must be ≥ {CANDIDATES_MIN_SAMPLES}")
    scenario = read_scenario(runtime)
    hz = float(scenario["capture_hz"])
    retained = int(scenario["retained_frame_count"])
    groups = {
        "none": measure_group("none", 0, samples, clock=clock),
        "tracked": measure_group("tracked", TRACKED_ROWS, samples, clock=clock),
    }
    p95_s = max(group["p95_s"] for group in groups.values())
    reasons = []
    if sys.platform != "darwin":
        reasons.append("not_macos")
    if any(group["status_mismatches"] for group in groups.values()):
        reasons.append("adapter_output_mismatch")
    if not qualifies(p95_s, hz, retained):
        reasons.append("does_not_qualify")
    return {
        "work_id": WORK_ID,
        "kind": "candidates_adapter_preflight",
        "host": "mac",
        "machine_name": machine_name(),
        "backend": CANDIDATES_BACKEND,
        "model_form": CANDIDATES_MODEL_FORM,
        "model_identity": dict(CANDIDATES_IDENTITY),
        "hz": hz,
        "retained_frame_count": retained,
        "scenario_id": scenario.get("scenario_id"),
        "p95_s": p95_s,
        "p95_rule": "nearest-rank: sorted[ceil(0.95*n)-1] per group; p95_s = max over groups",
        "clock": "time.perf_counter (monotonic)",
        "boundary": "CandidatesBackend.predict_one call to return; synthetic frame names, no image read",
        "groups": groups,
        "k_ret": k_ret_of(p95_s, hz),
        "k_conf": k_conf_of(hz),
        "k_pub": K_PUB,
        "qualifies": qualifies(p95_s, hz, retained),
        "verdict": "FAIL" if reasons else "OK",
        "fail_reasons": reasons,
        "environment": {
            "python": sys.version.split()[0],
            "executable": sys.executable,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "git_head": _git_head(),
        },
        "consumption": {"ids": 0, "play": 0, "model_or_detector_calls": 0, "image_reads": 0, "sequence_replay": 0},
        "note": "adapter-only latency; not online detection or end-to-end Play latency; not a success guarantee",
    }


def build_receipt(report: dict[str, Any], report_path: Path) -> dict[str, Any]:
    receipt = build_k_receipt(
        hz=report["hz"],
        retained_frame_count=report["retained_frame_count"],
        p95_s=report["p95_s"],
        host="mac",
        backend=CANDIDATES_BACKEND,
        model_form=CANDIDATES_MODEL_FORM,
        model_identity=dict(report["model_identity"]),
        scenario_id=report.get("scenario_id"),
    )
    document = receipt.payload()
    document.update(
        {
            "work_id": WORK_ID,
            "decision": "mac",
            "decision_reason": "candidates_single_host",
            "source_reports": {"mac": {"path": str(report_path), "sha256": sha256_file(report_path)}},
        }
    )
    return document


def run(runtime: Path, out_dir: Path, samples: int) -> int:
    report = build_report(runtime, samples)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = (out_dir / REPORT_NAME).resolve()
    receipt_path = out_dir / RECEIPT_NAME
    stamp = time.strftime("%Y%m%dT%H%M%S")
    for old in (receipt_path, report_path):
        if old.exists():
            # 旧报告/收据不沿用：移走（不删除），避免新报告配旧收据。
            old.replace(old.with_name(f"{old.name}.superseded-{stamp}"))
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    summary = {key: report[key] for key in ("machine_name", "hz", "retained_frame_count", "p95_s", "qualifies", "verdict")}
    summary["group_p95_s"] = {name: group["p95_s"] for name, group in report["groups"].items()}
    summary["report"] = str(report_path)
    if report["verdict"] != "OK":
        summary["fail_reasons"] = report["fail_reasons"]
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 6
    receipt = build_receipt(report, report_path)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    summary["receipt"] = str(receipt_path.resolve())
    summary["receipt_sha256"] = sha256_file(receipt_path)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runtime", type=Path, default=PROJECT_ROOT / "runtime", help="读其生效场景配置（只读）")
    parser.add_argument(
        "--out-dir", type=Path, default=PROJECT_ROOT / "outputs/eng-acq/P1-ENG-ACQ-001/play-d1/k-receipt"
    )
    parser.add_argument("--samples", type=int, default=200, help=f"每组样本数（≥ {CANDIDATES_MIN_SAMPLES}）")
    arguments = parser.parse_args(argv)
    if arguments.samples < CANDIDATES_MIN_SAMPLES:
        parser.error(f"--samples must be ≥ {CANDIDATES_MIN_SAMPLES}")
    return run(arguments.runtime, arguments.out_dir, arguments.samples)


if __name__ == "__main__":
    raise SystemExit(main())
