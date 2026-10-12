#!/usr/bin/env python3
"""P1-ENG-LOOP-001 §3.5：时延测量、合并等价判定与 K 收据（AC-9 / AC-10 的产出器）。

测量口径逐条照合同实现，**不在别处再写一份**：

* 每台宿主、**最终运行形态**：3 次预热（单列，不进统计）+ 32 次计时（smoke 集，
  顺序固定）；
* 边界 = `predict_one` 调用到返回（含图像读取、编码、生成；`http` 含传输）；
* `p95` = 32 个样本升序的**第 31 个**（下标 30）；
* 任一样本异常/超时 → 该样本失败、该轮 `INVALID`，允许重跑 1 轮，
  **第二轮仍 `INVALID` → 该宿主 `FAIL`**；加载失败/OOM 直接 `FAIL`；
* 报告：p50/p95/max、每 token ms、峰值内存、失败数、环境版本、`hz`/`R`、
  `K_ret`/`K_conf`/`K_pub`、资格与分档。

K 收据由两份时延报告按 §3.3 的「先资格后分档」决策表生成；两宿主都不合格即
`HOST_UNDECIDED`，不冻结、上交用户（AC-10 修订 1）。本模块不虚填任何实机数字：
没有测量就没有报告。

P1-ENG-LOOP-002 §3.2（A8）新增 **jetson 单宿主生产路径**，旧两宿主路径逐字不变：

* `measure --host jetson --backend http --server-url <url>`：身份只从服务 `/status` 读取（不接受用户
  传入 sha），要求非空 `weights_sha256` 与六个 llama 键；报告另写 `transport.endpoint`、
  `environment.git_head`/`dirty`（客户端整个工作树）、服务 `serve_code_sha256` 与 `machine`、逐请求
  状态（含解析/约束失败，失败行不过滤）。
* `k-receipt --single-host jetson --report <r>`：生成前以本机干净工作树重算 `response_format`/
  `decode`/`prompt` 身份与部署摘要，与报告逐键比较。退出码：0 = 已生成且合格；6 = 报告缺失/不全/
  身份或部署摘要与重算不符/六键类型值域不合（不生成）；8 = 已生成但不合格。
"""

from __future__ import annotations

import argparse
import gc
from dataclasses import dataclass
import json
from pathlib import Path
import platform
import statistics
import sys
import threading
import time
from typing import Any, Callable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller.language_bridge import LanguageBridgeError, validate_llama_identity  # noqa: E402
from controller.language_loop import (  # noqa: E402
    JETSON_HOST,
    K_PUB,
    KReceipt,
    build_k_receipt,
    code_git_state,
    decide_host,
    host_tier,
    k_conf_of,
    k_ret_of,
    qualifies,
    read_scenario,
)
from controller.language_selector import (  # noqa: E402
    SelectorError,
    _prompt_identity,
    interpret,
    selections_equivalent,
    sha256_file,
)
from tools.eng_loop2 import deploy_digest  # noqa: E402

#: §3.2：jetson 单宿主收据的退出码（0 / 6 沿用；8 = 已生成但不合格）。
EXIT_NOT_QUALIFIED = 8
EXIT_REPORT_REJECTED = 6
#: `measure` 非 OK 的退出码（现行；jetson 路径的身份探针失败同样落报告后以此退出）。
EXIT_MEASURE_NOT_OK = 7
#: P1-ENG-LOOP-002 AC-15 修订 1(a)：jetson 生产入口只测一轮（收据 35 = 3 预热 + 32 计时，收据重测 0）；
#: 首轮 INVALID/FAIL 不新建第二轮适配器、不再 bind/status、不再推理。其他宿主沿 `measure_host` 缺省两轮。
JETSON_MAX_ROUNDS = 1

WARMUP_ROUNDS = 3
TIMED_SAMPLES = 32
#: `p95` 的位置：32 个样本升序的第 31 个。
P95_INDEX = 30


def _percentile_p95(samples: Sequence[float]) -> float:
    ordered = sorted(float(value) for value in samples)
    if len(ordered) != TIMED_SAMPLES:
        raise ValueError(
            f"p95 只在 {TIMED_SAMPLES} 个样本上有定义；收到 {len(ordered)} 个"
        )
    return ordered[P95_INDEX]


def peak_memory() -> dict[str, Any]:
    """峰值内存：进程 RSS，外加（若有 torch）MPS 分配或 CUDA 峰值。"""
    report: dict[str, Any] = {"process_rss_bytes": None, "device_bytes": None,
                              "device_source": None}
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # macOS 报字节，Linux 报 KiB。
        report["process_rss_bytes"] = (
            int(usage) if sys.platform == "darwin" else int(usage) * 1024
        )
    except Exception:  # pragma: no cover - 平台特例
        pass
    try:
        import torch

        if torch.cuda.is_available():
            report["device_bytes"] = int(torch.cuda.max_memory_allocated())
            report["device_source"] = "torch.cuda.max_memory_allocated"
        elif getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            report["device_bytes"] = int(torch.mps.current_allocated_memory())
            report["device_source"] = "torch.mps.current_allocated_memory"
    except Exception:  # pragma: no cover - 没有 torch 的解释器
        pass
    return report


def environment() -> dict[str, Any]:
    versions: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
    }
    for name in ("torch", "transformers", "peft", "accelerate"):
        try:
            module = __import__(name)
            versions[name] = getattr(module, "__version__", "unknown")
        except Exception:
            versions[name] = None
    return versions


class MemorySampler:
    """MPS 无峰值分配 API：以 20ms 采样给出明确标注的分配峰值下界。"""
    def __init__(self):
        self.stop_event = threading.Event()
        self.mps_peak = None
        self.thread = None

    def start(self):
        torch = sys.modules.get("torch")
        if torch is None or not torch.backends.mps.is_available():
            return
        def sample():
            while not self.stop_event.is_set():
                value = int(torch.mps.current_allocated_memory())
                self.mps_peak = max(self.mps_peak or 0, value)
                self.stop_event.wait(0.02)
        self.thread = threading.Thread(target=sample, daemon=True)
        self.thread.start()

    def finish(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        report = peak_memory()
        if self.mps_peak is not None:
            report.update(device_bytes=max(report["device_bytes"] or 0, self.mps_peak),
                          device_source="torch.mps.current_allocated_memory sampled peak (20ms; lower bound)")
        return report


def read_smoke_rows(path: Path, package_root: Path) -> list[dict[str, Any]]:
    """smoke 集的固定顺序：按文件里的行序，不打乱、不采样。"""
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows.append(
            {
                "row_id": row.get("row_id", row.get("sample_id")),
                "image_path": Path(package_root) / row["frame_path"],
                "surface": row["surface"],
                "g4": bool(row.get("g4", False)),
            }
        )
        if not rows[-1]["row_id"]:
            raise ValueError("smoke row has no row_id or sample_id")
        if row.get("frame_sha256") and sha256_file(rows[-1]["image_path"]) != row["frame_sha256"]:
            raise ValueError(f"smoke image hash mismatch: {rows[-1]['row_id']}")
    return rows


@dataclass
class RoundResult:
    verdict: str
    samples: list[dict[str, Any]]
    warmup: list[dict[str, Any]]
    failures: list[dict[str, Any]]
    #: AC-15 修订 1(b)（只在 `stop_on_failure=True` 时有意义）：首个测量失败后停止本轮剩余调用。
    stop_on_failure: bool = False
    not_attempted: int = 0


def measure_round(
    adapter: Any,
    rows: Sequence[Mapping[str, Any]],
    *,
    warmup: int = WARMUP_ROUNDS,
    samples: int = TIMED_SAMPLES,
    monotonic: Callable[[], float] = time.monotonic,
    query_prefix: str = "measure",
    classify: bool = False,
    stop_on_failure: bool = False,
) -> RoundResult:
    """一轮测量：`warmup` 次预热（单列）+ `samples` 次计时，顺序固定。

    `classify=True`（jetson 路径）时每个成功样本另记解析后的三态 `status` 与 `parse_error`
    （解析/约束失败照记，不过滤）。

    `stop_on_failure=True`（P1-ENG-LOOP-002 AC-15 修订 1(b)，jetson 路径）：首个测量失败（`SelectorError`，
    或固定 60 s 测量截止失败）之后不再发起本轮剩余调用；已得原样本与失败原因原样保留，未发起的调用数
    记 `not_attempted`，本轮 `INVALID`（不足 32 个计时样本，不生成 p95）。正常返回的三态/`parse_error`
    不是失败，照常记录。"""
    if len(rows) < samples:
        raise ValueError(f"smoke 集需要至少 {samples} 行；收到 {len(rows)}")
    warmed: list[dict[str, Any]] = []
    timed: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    def call(row: Mapping[str, Any], label: str, index: int) -> dict[str, Any]:
        query_id = f"{query_prefix}-{label}-{index}"
        started = float(monotonic())
        try:
            raw = adapter.predict_one(
                query_id, Path(row["image_path"]), row["surface"], bool(row["g4"])
            )
        except SelectorError as exception:
            failures.append(
                {"query_id": query_id, "row_id": row.get("row_id"),
                 "reason": exception.reason, "detail": exception.detail}
            )
            return {"query_id": query_id, "row_id": row.get("row_id"), "failed": True}
        elapsed_ms = (float(monotonic()) - started) * 1000.0
        if elapsed_ms > 60_000.0:
            failures.append({"query_id": query_id, "row_id": row.get("row_id"),
                             "reason": "timeout", "detail": "predict_one exceeded fixed 60s measurement deadline"})
            return {"query_id": query_id, "row_id": row.get("row_id"), "failed": True,
                    "latency_ms": elapsed_ms}
        sample = {
            "query_id": query_id,
            "row_id": row.get("row_id"),
            "failed": False,
            "latency_ms": elapsed_ms,
            "gen_tokens": raw.gen_tokens,
            "finish_reason": raw.finish_reason,
            "raw_output": raw.raw_output,
            "model_id": raw.model_id,
            "prompt_sha256": raw.prompt_sha256,
        }
        if classify:
            selection = interpret(raw)
            sample.update(status=selection.status, parse_error=selection.parse_error)
        return sample

    planned = [("warmup", index, rows[index % len(rows)]) for index in range(warmup)]
    planned += [("timed", index, rows[index]) for index in range(samples)]
    not_attempted = 0
    for position, (label, index, row) in enumerate(planned):
        if stop_on_failure and failures:
            not_attempted = len(planned) - position
            break
        (warmed if label == "warmup" else timed).append(call(row, label, index))
    verdict = "OK" if not failures else "INVALID"
    return RoundResult(
        verdict=verdict, samples=timed, warmup=warmed, failures=failures,
        stop_on_failure=stop_on_failure, not_attempted=not_attempted,
    )


def summarize_round(result: RoundResult) -> dict[str, Any]:
    latencies = [
        float(sample["latency_ms"]) for sample in result.samples if not sample["failed"]
    ]
    tokens = [
        int(sample["gen_tokens"])
        for sample in result.samples
        if not sample["failed"] and isinstance(sample.get("gen_tokens"), int)
    ]
    per_token = [
        float(sample["latency_ms"]) / int(sample["gen_tokens"])
        for sample in result.samples
        if not sample["failed"]
        and isinstance(sample.get("gen_tokens"), int)
        and int(sample["gen_tokens"]) > 0
    ]
    summary: dict[str, Any] = {
        "verdict": result.verdict,
        "warmup_samples": len(result.warmup),
        "timed_samples": len(result.samples),
        "failures": result.failures,
        "p50_ms": statistics.median(latencies) if latencies else None,
        "p95_ms": (
            _percentile_p95(latencies) if len(latencies) == TIMED_SAMPLES else None
        ),
        "max_ms": max(latencies) if latencies else None,
        "per_token_ms_p50": statistics.median(per_token) if per_token else None,
        "gen_tokens_p50": statistics.median(tokens) if tokens else None,
        "warmup_latency_ms": [
            sample.get("latency_ms") for sample in result.warmup
        ],
        "latencies_ms": latencies,
        "samples": result.samples,
        "warmup": result.warmup,
    }
    if result.stop_on_failure:
        # AC-15 修订 1(b)：只在 jetson 路径出现；旧宿主报告的键集合不变。
        summary["stopped_after_first_failure"] = bool(result.failures)
        summary["not_attempted"] = result.not_attempted
    return summary


def measure_host(
    adapter_factory: Callable[[], Any],
    rows: Sequence[Mapping[str, Any]],
    *,
    host: str,
    backend: str,
    model_form: str,
    hz: float,
    retained_frame_count: int,
    max_rounds: int = 2,
    query_prefix: str | None = None,
    monotonic: Callable[[], float] = time.monotonic,
    classify: bool = False,
    stop_on_failure: bool = False,
) -> dict[str, Any]:
    """一台宿主的完整测量：最多 `max_rounds` 轮（缺省 2），末轮仍 `INVALID` → 该宿主 `FAIL`。

    jetson 生产入口以 `max_rounds=JETSON_MAX_ROUNDS`（1）与 `stop_on_failure=True` 调用（AC-15 修订 1）。"""
    rounds: list[dict[str, Any]] = []
    identity: Mapping[str, Any] = {}
    p95_s: float | None = None
    verdict = "FAIL"
    load_error: str | None = None
    memories = []
    for attempt in range(1, max_rounds + 1):
        try:
            adapter = adapter_factory()
        except SelectorError as exception:
            load_error = f"{exception.reason}: {exception.detail}"
            rounds.append({"round": attempt, "verdict": "FAIL", "load_error": load_error})
            break
        identity = dict(getattr(adapter, "identity", {}) or {})
        sampler = MemorySampler()
        sampler.start()
        try:
            result = measure_round(
                adapter,
                rows,
                monotonic=monotonic,
                query_prefix=f"{query_prefix or host}-r{attempt}",
                classify=classify,
                stop_on_failure=stop_on_failure,
            )
        finally:
            memories.append(sampler.finish())
        summary = summarize_round(result)
        summary["round"] = attempt
        rounds.append(summary)
        if summary["verdict"] == "OK":
            verdict = "OK"
            p95_s = float(summary["p95_ms"]) / 1000.0
            break
        del adapter
        gc.collect()
    tier = host_tier(p95_s, hz, retained_frame_count) if verdict == "OK" else "FAIL"
    return {
        "work_id": "P1-ENG-LOOP-001",
        "host": host,
        "backend": backend,
        "model_form": model_form,
        "verdict": verdict,
        "tier": tier,
        "p95_s": p95_s,
        "rounds": rounds,
        "load_error": load_error,
        "hz": hz,
        "retained_frame_count": retained_frame_count,
        "k_ret": k_ret_of(p95_s, hz) if p95_s is not None else None,
        "k_conf": k_conf_of(hz),
        "k_pub": K_PUB,
        "qualifies": qualifies(p95_s, hz, retained_frame_count) if p95_s is not None else False,
        "model_identity": dict(identity),
        "environment": environment(),
        "peak_memory": max(memories, key=lambda m: m["device_bytes"] or 0) if memories else peak_memory(),
        "measured_unix_s": time.time(),
    }


def merge_equivalence(
    merged_adapter: Any,
    adapter_adapter: Any,
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """AC-9：同设备、同 32 行 smoke、同 greedy 的逐行等价判定。"""
    comparisons: list[dict[str, Any]] = []
    equivalent = True
    for index, row in enumerate(rows[:TIMED_SAMPLES]):
        query_id = f"equiv-{index}"
        entry: dict[str, Any] = {"row_id": row.get("row_id"), "query_id": query_id}
        try:
            left = interpret(
                merged_adapter.predict_one(
                    f"{query_id}-merged", Path(row["image_path"]), row["surface"], bool(row["g4"])
                )
            )
            right = interpret(
                adapter_adapter.predict_one(
                    f"{query_id}-adapter", Path(row["image_path"]), row["surface"], bool(row["g4"])
                )
            )
        except SelectorError as exception:
            entry.update({"equivalent": False, "reason": exception.reason})
            comparisons.append(entry)
            equivalent = False
            continue
        ok, reason = selections_equivalent(left, right)
        entry.update(
            {
                "equivalent": ok,
                "reason": reason,
                "merged_status": left.status,
                "adapter_status": right.status,
                "merged_parse_error": left.parse_error,
                "adapter_parse_error": right.parse_error,
            }
        )
        comparisons.append(entry)
        equivalent = equivalent and ok
    return {
        "work_id": "P1-ENG-LOOP-001",
        "rows": len(comparisons),
        "equivalent": equivalent,
        "selected_model_form": "c2-merged" if equivalent else "c2-adapter",
        "merged_identity": dict(getattr(merged_adapter, "identity", {}) or {}),
        "adapter_identity": dict(getattr(adapter_adapter, "identity", {}) or {}),
        "comparisons": comparisons,
        "measured_unix_s": time.time(),
    }


def sequential_merge_equivalence(
    merged_factory: Callable[[], Any], adapter_factory: Callable[[], Any],
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """同设备顺序运行两形态；第二次加载前释放第一份，避免双模型占满 8GB GPU。"""
    if len(rows) != TIMED_SAMPLES:
        raise ValueError("equivalence requires exactly 32 frozen smoke rows")

    class RecordedAdapter:
        def __init__(self, identity, records):
            self.identity, self.records = identity, records

        def predict_one(self, query_id, *_args):
            record = self.records[query_id]
            if isinstance(record, SelectorError):
                raise record
            return record

    recordings = []
    evidence = {}
    for form, factory in (("merged", merged_factory), ("adapter", adapter_factory)):
        model = factory()
        identity = dict(model.identity)
        records = {}
        raw_records = []
        for index, row in enumerate(rows):
            query_id = f"equiv-{index}-{form}"
            try:
                raw = model.predict_one(query_id, Path(row["image_path"]), row["surface"], bool(row["g4"]))
                records[query_id] = raw
                raw_records.append({"row_id": row["row_id"], "query_id": query_id,
                                    "raw_output": raw.raw_output, "finish_reason": raw.finish_reason})
            except SelectorError as exc:
                records[query_id] = SelectorError(exc.reason, exc.detail)
                raw_records.append({"row_id": row["row_id"], "query_id": query_id,
                                    "reason": exc.reason, "detail": exc.detail})
        recordings.append(RecordedAdapter(identity, records))
        evidence[form] = raw_records
        del model
        gc.collect()
        if "torch" in sys.modules:
            torch = sys.modules["torch"]
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif torch.backends.mps.is_available():
                torch.mps.empty_cache()
    report = merge_equivalence(*recordings, rows)
    report["raw_records"] = evidence
    report["execution_order"] = ["merged", "adapter"]
    return report


def build_receipt_document(
    mac_report: Mapping[str, Any] | None,
    gpu_report: Mapping[str, Any] | None,
    *,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    """按 §3.3 决策表选宿主并组装 K 收据；两边都不合格 → `HOST_UNDECIDED`。"""
    if mac_report is None or gpu_report is None:
        return {"work_id": "P1-ENG-LOOP-001", "decision": "MEASUREMENT_INCOMPLETE",
                "missing_hosts": [name for name, report in (("mac", mac_report), ("5060", gpu_report))
                                  if report is None],
                "note": "缺测不冒充宿主 FAIL，不冻结 K 收据"}
    mac_tier = str(mac_report.get("tier", "FAIL")) if mac_report else "FAIL"
    gpu_tier = str(gpu_report.get("tier", "FAIL")) if gpu_report else "FAIL"
    mac_p95 = mac_report.get("p95_s") if mac_report else None
    gpu_p95 = gpu_report.get("p95_s") if gpu_report else None
    choice, why = decide_host(mac_tier, mac_p95, gpu_tier, gpu_p95)
    if choice == "HOST_UNDECIDED":
        return {
            "work_id": "P1-ENG-LOOP-001",
            "decision": "HOST_UNDECIDED",
            "reason": why,
            "mac": {"tier": mac_tier, "p95_s": mac_p95},
            "gpu_5060": {"tier": gpu_tier, "p95_s": gpu_p95},
            "note": "不冻结 K 收据，上交用户（AC-10 修订 1）",
        }
    source = mac_report if choice == "mac" else gpu_report
    assert source is not None
    receipt = build_k_receipt(
        hz=float(source["hz"]),
        retained_frame_count=int(source["retained_frame_count"]),
        p95_s=float(source["p95_s"]),
        host=choice,
        backend=str(source["backend"]),
        model_form=str(source["model_form"]),
        model_identity=dict(source.get("model_identity", {})),
        scenario_id=scenario_id,
    )
    document = receipt.payload()
    document.update(
        {
            "work_id": "P1-ENG-LOOP-001",
            "decision": choice,
            "decision_reason": why,
            "measurement_report": {
                "mac": {"tier": mac_tier, "p95_s": mac_p95},
                "gpu_5060": {"tier": gpu_tier, "p95_s": gpu_p95},
            },
        }
    )
    return document


# --- jetson 单宿主（P1-ENG-LOOP-002 §3.2 / A8） ---------------------------------


def jetson_status_identity(adapter: Any) -> dict[str, Any]:
    """从服务 `/status` 读出身份与部署摘要（不接受用户传入 sha）；六键与权重身份不全即 `load_failure`。"""
    document = adapter.status_document()
    identity = document.get("model_identity")
    if not isinstance(identity, dict) or not identity.get("weights_sha256"):
        raise SelectorError("load_failure", "/status lacks a weights-bound model_identity")
    try:
        llama = validate_llama_identity(identity)
    except LanguageBridgeError as exc:
        raise SelectorError("load_failure", f"/status identity invalid: {exc}") from exc
    if not llama:
        raise SelectorError("load_failure", "/status identity lacks the six llama keys")
    serve_code = document.get("serve_code_sha256")
    machine = document.get("machine")
    if not isinstance(serve_code, str) or not serve_code or not isinstance(machine, str) or not machine:
        raise SelectorError("load_failure", "/status lacks serve_code_sha256 or machine")
    return {"model_identity": dict(identity), "serve_code_sha256": serve_code, "machine": machine}


def jetson_adapter_factory(
    server_url: str,
    *,
    t_ret_s: float,
    t_hard_s: float,
    opener: Callable[..., bytes] | None = None,
) -> tuple[Callable[[], Any], dict[str, Any]]:
    """测量适配器：身份取自 `/status` 并 `bind_identity`（此后每次回包逐键核对）。"""
    from controller.language_selector import HttpAdapter  # noqa: PLC0415

    def build() -> Any:
        return HttpAdapter(
            server_url, t_ret_s=t_ret_s, t_hard_s=t_hard_s, model_form="c2-merged", opener=opener
        )

    probe = build()
    served = jetson_status_identity(probe)

    def factory() -> Any:
        adapter = build()
        adapter.bind_identity(served["model_identity"])
        return adapter

    return factory, served


def jetson_probe_failure_report(
    load_error: str, server_url: str, *, hz: float, retained_frame_count: int,
    code_root: Path = PROJECT_ROOT,
    git_state: Callable[[], tuple[str | None, bool]] | None = None,
) -> dict[str, Any]:
    """AC-15 修订 1(b)：`/status` 身份探针失败时的报告（零推理、`FAIL`，不能生成收据）。"""
    head, dirty = git_state() if git_state is not None else code_git_state(code_root)
    env = environment()
    env.update({"git_head": head, "dirty": bool(dirty)})
    return {
        "work_id": "P1-ENG-LOOP-002",
        "host": JETSON_HOST,
        "backend": "http",
        "model_form": "c2-merged",
        "verdict": "FAIL",
        "tier": "FAIL",
        "p95_s": None,
        "rounds": [{"round": 1, "verdict": "FAIL", "load_error": load_error}],
        "load_error": load_error,
        "hz": hz,
        "retained_frame_count": retained_frame_count,
        "qualifies": False,
        "model_identity": {},
        "transport": {"endpoint": server_url},
        "environment": env,
        "measured_unix_s": time.time(),
    }


def jetson_report_fields(
    served: Mapping[str, Any], server_url: str, code_root: Path = PROJECT_ROOT,
    git_state: Callable[[], tuple[str | None, bool]] | None = None,
) -> dict[str, Any]:
    head, dirty = git_state() if git_state is not None else code_git_state(code_root)
    return {
        "work_id": "P1-ENG-LOOP-002",
        "transport": {"endpoint": server_url},
        "serve_code_sha256": served["serve_code_sha256"],
        "machine": served["machine"],
        "environment_git": {"git_head": head, "dirty": bool(dirty)},
    }


class ReceiptRejected(ValueError):
    """报告缺失/不全/身份或部署摘要与重算不符/六键不合：退出码 6，不生成收据。"""


def build_single_host_receipt(
    report: Mapping[str, Any] | None,
    report_path: Path,
    *,
    scenario: Mapping[str, Any],
    code_root: Path = PROJECT_ROOT,
    git_state: Callable[[], tuple[str | None, bool]] | None = None,
) -> dict[str, Any]:
    """§3.2：由 jetson 报告生成单宿主 K 收据。任何不符抛 `ReceiptRejected`（退出码 6）。

    `k_ret = ⌈p95·hz⌉ + 2`、`k_conf`、`k_pub`、`R`、`scenario_id`、`model_identity` 全部来自报告与生效
    场景；生成前以本机干净工作树（HEAD == 报告 `git_head`、代码路径无改动）重算 `response_format`/
    `decode`/`prompt` 身份与部署摘要，与报告逐键比较。是否合格写进收据 `qualifies`，由调用方给退出码 8。
    """
    if report is None:
        raise ReceiptRejected("jetson report missing")
    try:
        if report.get("host") != JETSON_HOST:
            raise ReceiptRejected(f"report host {report.get('host')!r} is not 'jetson'")
        if report.get("verdict") != "OK" or report.get("p95_s") is None:
            raise ReceiptRejected("jetson report verdict is not OK (no qualifying measurement)")
        if report.get("backend") != "http" or report.get("model_form") != "c2-merged":
            raise ReceiptRejected("jetson report must be backend 'http' with model_form 'c2-merged'")
        endpoint = (report.get("transport") or {}).get("endpoint")
        if not isinstance(endpoint, str) or not endpoint:
            raise ReceiptRejected("jetson report lacks transport.endpoint")
        environment = report.get("environment") or {}
        if not isinstance(environment.get("git_head"), str) or not environment.get("git_head"):
            raise ReceiptRejected("jetson report lacks environment.git_head")
        if environment.get("dirty") is not False:
            raise ReceiptRejected("jetson report was measured from a dirty working tree")
        identity = dict(report.get("model_identity") or {})
        if not identity.get("weights_sha256"):
            raise ReceiptRejected("jetson report lacks weights_sha256")
        try:
            llama = validate_llama_identity(identity)
        except LanguageBridgeError as exc:
            raise ReceiptRejected(f"jetson identity invalid: {exc}") from exc
        if not llama:
            raise ReceiptRejected("jetson identity lacks the six llama keys")
        if not isinstance(report.get("machine"), str) or not report.get("machine"):
            raise ReceiptRejected("jetson report lacks the board machine name")
        head, dirty = git_state() if git_state is not None else code_git_state(code_root)
        if head != environment.get("git_head"):
            raise ReceiptRejected("desktop HEAD differs from the report git_head")
        if dirty:
            raise ReceiptRejected("desktop working tree is dirty; recompute needs a clean working tree")
        digests = deploy_digest.desktop_identity_digests(code_root)
        if report.get("serve_code_sha256") != digests["serve_code_sha256"]:
            raise ReceiptRejected("serve_code_sha256 differs from the desktop deploy digest")
        for key in ("response_format_sha256", "decode_config_sha256"):
            if identity.get(key) != digests[key]:
                raise ReceiptRejected(f"{key} differs from the desktop recomputation")
        if identity.get("prompt_template_sha256") != _prompt_identity(False)["prompt_template_sha256"]:
            raise ReceiptRejected("prompt_template_sha256 differs from the desktop recomputation")
        hz = float(report["hz"])
        retained = int(report["retained_frame_count"])
        if abs(hz - float(scenario["capture_hz"])) > 1e-9 or retained != int(scenario["retained_frame_count"]):
            raise ReceiptRejected("report hz/R differ from the effective scenario")
        receipt = build_k_receipt(
            hz=hz,
            retained_frame_count=retained,
            p95_s=float(report["p95_s"]),
            host=JETSON_HOST,
            backend="http",
            model_form="c2-merged",
            model_identity=identity,
            scenario_id=scenario.get("scenario_id"),
        )
    except (KeyError, TypeError, ValueError, OSError) as exc:
        if isinstance(exc, ReceiptRejected):
            raise
        raise ReceiptRejected(f"jetson report incomplete: {exc}") from exc
    document = receipt.payload()
    document.update(
        {
            "work_id": "P1-ENG-LOOP-002",
            "decision": JETSON_HOST,
            "decision_reason": "single_host_jetson",
            "source_reports": {
                JETSON_HOST: {"path": str(report_path), "sha256": sha256_file(Path(report_path))}
            },
            "serve_code_sha256": report["serve_code_sha256"],
            "machine": report["machine"],
            "git_head": environment["git_head"],
        }
    )
    return document


# --- CLI -------------------------------------------------------------------


def _adapter_factory(arguments: argparse.Namespace, model_form: str) -> Callable[[], Any]:
    from controller.language_selector import HttpAdapter, ReplayAdapter, load_local_adapter

    if arguments.backend == "replay":
        return lambda: ReplayAdapter(
            arguments.replay_blind,
            arguments.replay_predictions,
            model_form=model_form,
        )
    if arguments.backend == "http":
        return lambda: HttpAdapter(
            arguments.server_url,
            t_ret_s=arguments.t_ret_s,
            t_hard_s=arguments.t_hard_s,
            model_form=model_form,
        )
    source = arguments.merged_source if model_form == "c2-merged" else arguments.model_source
    adapter_dir = None if model_form == "c2-merged" else arguments.adapter_dir
    return lambda: load_local_adapter(
        source=source,
        adapter_dir=adapter_dir,
        device=arguments.device,
        model_form=model_form,
        output_directory=Path(arguments.scratch) / "queries",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)

    def common(command: argparse.ArgumentParser) -> None:
        command.add_argument("--backend", choices=("local-hf", "http", "replay"), required=True)
        command.add_argument("--smoke", type=Path, required=True)
        command.add_argument("--package-root", type=Path, required=True)
        command.add_argument("--model-source", type=Path)
        command.add_argument("--merged-source", type=Path)
        command.add_argument("--adapter-dir", type=Path)
        command.add_argument("--device", default="mps")
        command.add_argument("--server-url", default="http://127.0.0.1:8760")
        command.add_argument("--t-ret-s", type=float, default=60.0)
        command.add_argument("--t-hard-s", type=float, default=60.0)
        command.add_argument("--replay-blind", type=Path)
        command.add_argument("--replay-predictions", type=Path)
        command.add_argument("--scratch", type=Path, default=Path("outputs/eng-loop/scratch"))
        command.add_argument("--runtime", type=Path, default=PROJECT_ROOT / "runtime")

    measure = subparsers.add_parser("measure", help="一台宿主的时延测量")
    common(measure)
    measure.add_argument("--host", required=True)
    measure.add_argument("--model-form", choices=("c2-merged", "c2-adapter", "base"), required=True)
    measure.add_argument("--out", type=Path, required=True)

    equivalence = subparsers.add_parser("merge-equivalence", help="合并 vs 未合并的逐行等价")
    common(equivalence)
    equivalence.add_argument("--out", type=Path, required=True)

    receipt = subparsers.add_parser("k-receipt", help="由两份时延报告（或一份 jetson 报告）生成 K 收据")
    receipt.add_argument("--mac", type=Path)
    receipt.add_argument("--gpu", type=Path)
    receipt.add_argument(
        "--single-host",
        choices=(JETSON_HOST,),
        default=None,
        help="P1-ENG-LOOP-002：jetson 单宿主收据（需 --report，不与 --mac/--gpu 同用）",
    )
    receipt.add_argument("--report", type=Path, default=None)
    receipt.add_argument("--runtime", type=Path, default=PROJECT_ROOT / "runtime")
    receipt.add_argument("--out", type=Path, required=True)

    arguments = parser.parse_args(argv)

    if arguments.command == "k-receipt" and arguments.single_host is not None:
        if arguments.mac is not None or arguments.gpu is not None:
            parser.error("--single-host jetson does not take --mac/--gpu")
        if arguments.report is None:
            print("REPORT_REJECTED: --single-host jetson needs --report", file=sys.stderr)
            return EXIT_REPORT_REJECTED
        scenario = read_scenario(arguments.runtime)
        try:
            report = json.loads(arguments.report.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"REPORT_REJECTED: unreadable jetson report: {exc}", file=sys.stderr)
            return EXIT_REPORT_REJECTED
        try:
            document = build_single_host_receipt(report, arguments.report, scenario=scenario)
        except ReceiptRejected as exc:
            print(f"REPORT_REJECTED: {exc}", file=sys.stderr)
            return EXIT_REPORT_REJECTED
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(document, indent=2, sort_keys=True))
        return 0 if document["qualifies"] else EXIT_NOT_QUALIFIED

    if arguments.command == "k-receipt":
        if arguments.report is not None:
            parser.error("--report is only used with --single-host jetson")
        scenario = read_scenario(arguments.runtime)
        document = build_receipt_document(
            json.loads(arguments.mac.read_text(encoding="utf-8")) if arguments.mac else None,
            json.loads(arguments.gpu.read_text(encoding="utf-8")) if arguments.gpu else None,
            scenario_id=scenario.get("scenario_id"),
        )
        document["source_reports"] = {
            name: {"path": str(path), "sha256": sha256_file(path)}
            for name, path in (("mac", arguments.mac), ("5060", arguments.gpu))
            if path is not None
        }
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(document, indent=2, sort_keys=True))
        return 0 if document.get("decision") in {"mac", "5060"} else 6

    scenario = read_scenario(arguments.runtime)
    rows = read_smoke_rows(arguments.smoke, arguments.package_root)

    if arguments.command == "measure" and arguments.host == JETSON_HOST:
        if arguments.backend != "http" or arguments.model_form != "c2-merged":
            parser.error("--host jetson measures --backend http --model-form c2-merged")
        try:
            factory, served = jetson_adapter_factory(
                arguments.server_url, t_ret_s=arguments.t_ret_s, t_hard_s=arguments.t_hard_s
            )
        except SelectorError as exception:
            # AC-15 修订 1(b)：身份探针失败即停（不重试、不发 result/query 凑齐 35）；失败落报告、非 OK。
            report = jetson_probe_failure_report(
                f"{exception.reason}: {exception.detail}", arguments.server_url,
                hz=scenario["capture_hz"], retained_frame_count=scenario["retained_frame_count"],
            )
        else:
            report = measure_host(
                factory,
                rows,
                host=JETSON_HOST,
                backend="http",
                model_form="c2-merged",
                hz=scenario["capture_hz"],
                retained_frame_count=scenario["retained_frame_count"],
                max_rounds=JETSON_MAX_ROUNDS,
                classify=True,
                stop_on_failure=True,
            )
            extra = jetson_report_fields(served, arguments.server_url)
            report["environment"].update(extra.pop("environment_git"))
            report.update(extra)
        report["smoke_sha256"] = sha256_file(arguments.smoke)
        report["smoke_row_ids"] = [row["row_id"] for row in rows]
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(
            json.dumps(
                {key: report[key] for key in ("host", "verdict", "tier", "p95_s", "qualifies")},
                indent=2,
            )
        )
        return 0 if report["verdict"] == "OK" else EXIT_MEASURE_NOT_OK

    if arguments.command == "measure":
        report = measure_host(
            _adapter_factory(arguments, arguments.model_form),
            rows,
            host=arguments.host,
            backend=arguments.backend,
            model_form=arguments.model_form,
            hz=scenario["capture_hz"],
            retained_frame_count=scenario["retained_frame_count"],
        )
        report["smoke_sha256"] = sha256_file(arguments.smoke)
        report["smoke_row_ids"] = [row["row_id"] for row in rows]
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(
            json.dumps(
                {key: report[key] for key in ("host", "verdict", "tier", "p95_s", "qualifies")},
                indent=2,
            )
        )
        return 0 if report["verdict"] == "OK" else 7

    report = sequential_merge_equivalence(
        _adapter_factory(arguments, "c2-merged"),
        _adapter_factory(arguments, "c2-adapter"), rows,
    )
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "rows": report["rows"],
                "equivalent": report["equivalent"],
                "selected_model_form": report["selected_model_form"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
