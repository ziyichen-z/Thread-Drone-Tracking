"""AC-7 时延（G-7）：Mac 上插件 `update`（检测 + 关联）在 CPU 与 MPS（可用时）各 ≥ 300 帧的 p50/p95。

帧取 V（a7）子序列（选择域，不触碰 H），两设备同一帧序、同一初始化框；每次 `update` 用 perf_counter
计墙钟（含预处理、推理、NMS 与关联）。判门：每个已测设备 p95 ≤ 200 ms；MPS 不可用记
`N/A(DEVICE_UNAVAILABLE)`（不影响 CPU）。另报 CPU/MPS 逐帧插件框差与检测层框差（≤ 1e-3）。
全部帧计入分位数（不剔除预热帧；预热前 10 帧另列）。
"""

from __future__ import annotations

import json
import time
from typing import Any, Sequence

from tools.eng_det import common, dataset, evaluate
from tools.eng_det.ledger import Ledger
from tools.eng_det.select import V_FAMILIES

SPEC_PATH = common.PROJECT_ROOT / "config" / "det-assoc-v1.models.json"
LATENCY_EVIDENCE = common.evidence("latency.json")
MIN_FRAMES = 300
TARGET_FRAMES = 320
P95_LIMIT_MS = 200.0
WARMUP = 10


def frames_for_latency() -> tuple[list[dict[str, Any]], list[float]]:
    frozen = common.read_json(common.evidence("freeze.json"))
    _identity, rows = dataset.load_index()
    pieces = []
    for _session, items in evaluate.sessions([r for r in rows if r["domain"] == "V"], V_FAMILIES).items():
        kept, _info = evaluate.split_subsequences(items, int(frozen["association"]["track_buffer"]))
        pieces.extend(kept)
    for piece in sorted(pieces, key=len, reverse=True):
        truths = [evaluate.target_truth(r) for r in piece]
        start = next((i for i, t in enumerate(truths) if t is not None), None)
        if start is not None and len(piece) - start - 1 >= TARGET_FRAMES:
            return list(piece[start : start + TARGET_FRAMES + 1]), list(truths[start])
    raise RuntimeError("V 中没有 ≥ 321 帧且含可见起点的子序列")


def measure(device: str, frames: Sequence[dict[str, Any]], init_box: Sequence[float], ledger: Ledger) -> dict[str, Any]:
    from controller.det_assoc_tracker import DetAssocTracker  # noqa: PLC0415

    ledger.charge("model_start", 1, label=f"latency-{device}", device=device)
    plugin = DetAssocTracker(spec_path=SPEC_PATH, device=device)
    images = [evaluate.read_image(f["frame_id"]) for f in frames]
    if not plugin.init(images[0], init_box):
        return {"device": device, "init": "INIT_REJECTED"}
    times, outputs = [], []
    for image in images[1:]:
        started = time.perf_counter()
        result = plugin.update(image)
        times.append((time.perf_counter() - started) * 1000.0)
        outputs.append((bool(result.ok), list(result.box_norm) if result.box_norm else None, result.reason))
    detections = [plugin._detect(image) for image in images[:50]]  # noqa: SLF001 — 检测层框差
    det_rows = []
    for boxes in detections:
        xyxyn = boxes.xyxyn.tolist() if len(boxes) else []
        det_rows.append(sorted([[round(v, 7) for v in b] + [round(float(c), 6)] for b, c in zip(xyxyn, boxes.conf.tolist())]))
    ordered = sorted(times)
    q = common.quantiles(times, (0.5, 0.95))
    return {
        "device": device,
        "manifest": dict(plugin.manifest_identity()),
        "frames_measured": len(times),
        "p50_ms": q.get("p50") if isinstance(q, dict) else None,
        "quantiles_ms": q,
        "max_ms": round(ordered[-1], 3),
        "warmup_first_10_ms": [round(t, 3) for t in times[:WARMUP]],
        "outputs": outputs,
        "detections_first_50": det_rows,
    }


def compare(cpu: dict[str, Any], mps: dict[str, Any]) -> dict[str, Any]:
    state_mismatch = 0
    box_diff = 0.0
    for (ok_c, box_c, _), (ok_m, box_m, _) in zip(cpu["outputs"], mps["outputs"]):
        if ok_c != ok_m:
            state_mismatch += 1
        elif ok_c and box_c and box_m:
            box_diff = max(box_diff, max(abs(a - b) for a, b in zip(box_c, box_m)))
    det_diff = 0.0
    count_mismatch = 0
    for rows_c, rows_m in zip(cpu["detections_first_50"], mps["detections_first_50"]):
        if len(rows_c) != len(rows_m):
            count_mismatch += 1
            continue
        for a, b in zip(rows_c, rows_m):
            det_diff = max(det_diff, max(abs(x - y) for x, y in zip(a[:4], b[:4])))
    return {
        "plugin_state_mismatch_frames": state_mismatch,
        "plugin_box_max_abs_diff_norm": round(box_diff, 8),
        "detection_count_mismatch_frames_first_50": count_mismatch,
        "detection_box_max_abs_diff_norm_first_50": round(det_diff, 8),
        "limit": 1e-3,
        "within_limit": box_diff <= 1e-3 and det_diff <= 1e-3 and state_mismatch == 0 and count_mismatch == 0,
    }


def run() -> dict[str, Any]:
    ledger = Ledger()
    frames, init_box = frames_for_latency()
    results = {"cpu": measure("cpu", frames, init_box, ledger)}
    try:
        import torch  # noqa: PLC0415

        mps_ok = bool(torch.backends.mps.is_available())
    except Exception:  # noqa: BLE001
        mps_ok = False
    results["mps"] = measure("mps", frames, init_box, ledger) if mps_ok else {"device": "mps", "verdict": "N/A(DEVICE_UNAVAILABLE)"}
    cells = {}
    for device, result in results.items():
        if "quantiles_ms" not in result:
            cells[device] = {"verdict": result.get("verdict", "N/A(INIT_REJECTED)")}
            continue
        p95 = result["quantiles_ms"]["p95"]
        n = result["frames_measured"]
        verdict = f"N/A(INSUFFICIENT_N={n})" if n < MIN_FRAMES else ("MET" if p95 <= P95_LIMIT_MS else "GATE_NOT_MET")
        cells[device] = {"n": n, "p50_ms": result["quantiles_ms"]["p50"], "p95_ms": p95, "threshold_ms": P95_LIMIT_MS, "verdict": verdict}
    measured = {d: c for d, c in cells.items() if not c["verdict"].startswith("N/A(DEVICE_UNAVAILABLE")}
    gate = evaluate.gate(measured)
    document = {
        "work_id": common.WORK_ID,
        "frames": {"domain": "V", "first": frames[0]["frame_id"], "count_updates": len(frames) - 1, "init_box": init_box},
        "cells": cells,
        "G-7": gate,
        "cpu_vs_mps": compare(results["cpu"], results["mps"]) if "outputs" in results.get("mps", {}) and "outputs" in results["cpu"] else None,
        "per_device": {d: {k: v for k, v in r.items() if k not in ("outputs", "detections_first_50")} for d, r in results.items()},
        "note": "单进程离线，无 Unity 同机负载；不推断 Play 机或 Jetson",
    }
    common.write_json(LATENCY_EVIDENCE, document)
    return document


def main(argv: Sequence[str] | None = None) -> None:
    document = run()
    print(json.dumps({"cells": document["cells"], "G-7": document["G-7"]["verdict"], "cpu_vs_mps": document["cpu_vs_mps"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
