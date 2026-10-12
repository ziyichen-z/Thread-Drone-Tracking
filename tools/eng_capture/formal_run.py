"""P1-ENG-CAPTURE-001 正式回放执行体（只由 `replay.py run` 在保真确认、预登记剧本与账本余额三项前置满足后调用）。

一次 YOLO 加载（`CountingModel`，尝试启动即记账）：
1. S-A-INPUT 现算核对（不符即停，AC-17/18/19 `NOT_RUN`）；
2. 原始 829 帧 × {per_class, unify_vehicle} 检测缓存（缓存键 = `DetAssocTracker.detection_cache_key`）；
3. 基线臂（`baseline_runner`，导出的基线源，per_class + pose，零推理）→ 现象门（不过 = S-A-REPRO）；
4. 新臂（unify_vehicle + pose-center + 目标管理器，同一剧本）→ AC-17 逐帧判据；
5. 故障注入（新臂缓存，零推理）：红车 561 起删检测 m ∈ {1,2,4,6} 帧、强制对目标开新轨迹、`auto_repair=off` 对照；
6. 合成滚转 72 序列 × 2 臂（热身 8 帧复用缓存 + 变换 16 帧实推理；选择输入 = AC-28 六基预登记点击）→ 每格断轨率与 Wilson 区间。
C1-5（逐帧共账）：加载在尝试前记账（失败不返还）；推理帧经 `ledger.InflightCounter` 在**每帧交给模型之前**原子落盘，
超每候选/整批上限或回放墙钟上限（30 min）的那一帧在推理前拒绝；阶段正常结束才结算，异常退出留 in_flight（耗用照计、可追溯，
未结算前启动门拒绝）。产物只写 `outputs/eng-capture/`，结束时按实测字节记磁盘。
R1返工：STOP 收尾（S-A-INPUT 早退、S-A-REPRO）写出的文件同样按输出目录实测字节记磁盘（R1-2，AR1-6「零模型不等于零磁盘」）；
最后一次推理之后的评分/落盘阶段也受墙钟上限核——写报告前补一次墙钟判定（`final_wall_check`），超限照写报告并记
S-A-BUDGET 偏差、退出码 6（不冒充在限内）。
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import json
from pathlib import Path
import time
from typing import Any, Callable, Mapping, Sequence

from controller import target_manager as tm
from tools.eng_capture import baseline_runner, ledger, replay
from tools.eng_capture.common import ADMITTED_FRAMES, ADMITTED_TRUTH, OUTPUT_ROOT


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_ledger(counter: str, amount: int, candidate: int, note: str, ledger_path: Path | None = None) -> None:
    """先核（整体校验、候选归属、上限）后记，原子写（C1-5）；账本路径调用时解析（`replay.LEDGER`）。"""
    ledger.record(ledger_path or replay.LEDGER, counter, amount, candidate, note)


def output_bytes(root: Path) -> int:
    """输出目录实测字节（普通文件；符号链接不计）。"""
    return sum(p.stat().st_size for p in Path(root).rglob("*") if p.is_file() and not p.is_symlink())


def final_wall_check(report: dict[str, Any], *, started: float, limit_s: float, now: float | None = None) -> bool:
    """写报告前补一次墙钟判定（复核 R1 附注；AR1-6 每次回放 ≤ 30 min，`CountingModel` 只在每次推理前核）。
    结果写入 `report["wall_clock"]`；超限另记 `budget_deviation`（S-A-BUDGET 偏差，回用户），不改已得读数、不追认。"""
    elapsed = round((time.monotonic() if now is None else float(now)) - float(started), 3)
    within = elapsed <= float(limit_s)
    report["wall_clock"] = {"elapsed_s": elapsed, "limit_s": float(limit_s), "within_limit": within, "judged": "before_writing_report"}
    if not within:
        report["budget_deviation"] = f"S-A-BUDGET: replay wall clock {elapsed} s > {float(limit_s)} s (judged before writing the report)"
    return within


def spec_weights_path(spec_path: Path = replay.SPEC) -> Path:
    """规格 `weights.path`（相对仓库根）→ 权重文件路径，并按规格核体积与 sha256（与 `DetAssocTracker` 同一身份）。

    阶段A回放窄修：修前把规格 JSON 路径当权重交给加载器，首次正式加载在 ultralytics 内拒绝（`TypeError`）。"""
    from controller.det_assoc_tracker import _verify_file  # noqa: PLC0415
    from tools.eng_capture.common import PROJECT_ROOT  # noqa: PLC0415

    weights = json.loads(Path(spec_path).read_text(encoding="utf-8"))["weights"]
    path = Path(weights["path"])
    path = path if path.is_absolute() else PROJECT_ROOT / path
    _verify_file(path, weights["sha256"], int(weights["size_bytes"]), "weights")
    return path


def load_frames(frame_ids: Sequence[int], *, frames_dir: Path = ADMITTED_FRAMES, decode: Callable[[Path], Any] | None = None) -> list[replay.ReplayFrame]:
    out = []
    for frame_id in frame_ids:
        image_path, json_path = replay.frame_paths(frame_id, frames_dir)
        data = image_path.read_bytes()
        image = decode(image_path) if decode is not None else None
        out.append(replay.ReplayFrame(frame_id, image, json.loads(json_path.read_text(encoding="utf-8")), replay.hashlib.sha256(data).hexdigest()))
    return out


def build_caches(frames: Sequence[replay.ReplayFrame], model: Any, *, tracker_factory: Callable[..., Any]) -> dict[str, dict]:
    """两种策略各对 829 帧推理一次（共用一次加载的模型）；缓存键 = `detection_cache_key(帧字节 sha)`。"""
    caches: dict[str, dict] = {}
    for policy in ("per_class", "unify_vehicle"):
        detector = tracker_factory(spec_path=replay.SPEC, device=None, model_loader=lambda _p: model, mode="resident", class_policy=policy)
        cache: dict = {}
        for frame in frames:
            boxes = detector._detect(frame.image)  # noqa: SLF001 — 与会话 `step` 同一检测调用（策略、NMS、类别置 0）
            cache[detector.detection_cache_key(frame.image_sha256)] = replay.boxes_rows(boxes)
        caches[policy] = {"cache": cache, "key": lambda sha, d=detector: d.detection_cache_key(sha)}
    return caches


def cached_frames(frames: Sequence[replay.ReplayFrame], key: Callable[[str], tuple]) -> list[replay.ReplayFrame]:
    return [dataclasses.replace(f, image=replay.CacheFrame(key(f.image_sha256))) for f in frames]


def run(arguments: Any, *, preconditions: Mapping[str, Any] | None = None, model_loader: Callable[[Path], Any] | None = None,
        decode: Callable[[Path], Any] | None = None, frame_ids: Sequence[int] | None = None) -> int:
    from controller.det_assoc_tracker import DetAssocTracker, _default_model_loader  # noqa: PLC0415

    if preconditions is None:
        preconditions = replay.launch_preconditions(arguments)  # 未经 `replay.main` 时同样先过全部零模型前置
    candidate = int(arguments.candidate)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = Path(arguments.output or OUTPUT_ROOT / "replay" / f"candidate{candidate}-{stamp}")
    output.mkdir(parents=True, exist_ok=True)
    script, script_sha = preconditions["click_script"], preconditions["click_script_sha256"]
    roll_clicks = replay.roll_clicks_by_base(preconditions["roll_click_script"])
    started = time.monotonic()
    report: dict[str, Any] = {"candidate": candidate, "click_script_sha256": script_sha,
                              "roll_click_script_sha256": preconditions["roll_click_script_sha256"],
                              "roll_plan": preconditions["roll_plan"], "output": str(output)}

    input_report = replay.check_input()
    (output / "input-check.json").write_text(json.dumps(input_report, indent=1) + "\n", encoding="utf-8")
    if not input_report["ok"]:
        report["stop"] = "S-A-INPUT"
        report["AC-17"] = report["AC-18"] = report["AC-19"] = "NOT_RUN"
        (output / "replay-report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        # R1-2（AR1-6）：Z-A 收尾写入也计 A 磁盘——按输出目录实测字节入账，不留未记账的写盘。
        record_ledger("mini_new_disk_bytes", output_bytes(output), candidate, f"S-A-INPUT 收尾：输出目录 {output.name} 实测字节（零模型，未加载）")
        return 3

    if decode is None:
        import cv2  # noqa: PLC0415

        decode = lambda path: cv2.imread(str(path))  # noqa: E731
    ids = list(frame_ids) if frame_ids is not None else replay.admitted_frame_ids()
    frames = load_frames(ids, decode=decode)
    weights = spec_weights_path()  # 加载前核权重身份（不符即拒，不记加载）
    record_ledger("replay_yolo_loads", 1, candidate, "正式回放启动加载（尝试即记，失败不返还）")
    wall_limit_s = 60.0 * float(ledger.read(replay.LEDGER)["envelope"]["replay_wall_minutes_per_run"])
    stage = ledger.InflightCounter.open(replay.LEDGER, "replay_inference_frames", candidate=candidate,
                                        note="原始帧 × 两策略检测缓存（逐帧提交前落盘）")
    counting = replay.CountingModel(model_loader or _default_model_loader, counter=stage, deadline_monotonic=started + wall_limit_s)
    model = counting.load(weights)
    caches = build_caches(frames, model, tracker_factory=DetAssocTracker)
    report["inference_frames_cache"] = stage.settle()
    params, config_sha, _text = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)
    truth = replay.score_truth_rows(ADMITTED_TRUTH)

    def loader_for(policy: str, live: Any | None = None) -> Callable[[Path], Any]:
        wrapped = replay.CachedOrLiveModel(caches[policy]["cache"], live, replay.library_boxes)
        return lambda _p: wrapped

    # 3. 基线臂（导出的基线源）。
    base_root, identity = baseline_runner.prepare_baseline_package(output / "baseline-source")
    modules = baseline_runner.load_baseline_modules(base_root)
    clicks = script["clicks"]
    baseline = baseline_runner.run_baseline_arm(modules, cached_frames(frames, caches["per_class"]["key"]), spec_path=replay.SPEC,
                                                model_loader=loader_for("per_class"), clicks=clicks)
    gate = replay.score_phenomenon_gate(baseline, truth)
    report["baseline_source"] = identity
    report["phenomenon_gate"] = gate
    # 4. 新臂。
    new = replay.run_new_arm(cached_frames(frames, caches["unify_vehicle"]["key"]), model_loader=loader_for("unify_vehicle"),
                             params=params, config_sha256=config_sha, clicks=clicks, inputs_path=output / "new-arm-tm_inputs.jsonl")
    window = replay.score_new_arm_window(new, truth, params)
    report["AC-17"] = {"verdict": window["verdict"] if gate["reproduced"] else "VOID_S-A-REPRO", "window": {k: v for k, v in window.items() if k != "rows"}}
    (output / "baseline-arm.json").write_text(json.dumps(baseline, indent=1) + "\n", encoding="utf-8")
    (output / "new-arm.json").write_text(json.dumps({"frames": new.frames, "window_rows": window["rows"]}, indent=1, default=str) + "\n", encoding="utf-8")
    if not gate["reproduced"]:
        report["stop"] = "S-A-REPRO"
        final_wall_check(report, started=started, limit_s=wall_limit_s)
        (output / "replay-report.json").write_text(json.dumps(report, indent=1, default=str) + "\n", encoding="utf-8")
        record_ledger("mini_new_disk_bytes", output_bytes(output), candidate, f"S-A-REPRO 收尾：输出目录 {output.name} 实测字节")
        return 5
    # 5. 故障注入（零推理）。
    report["AC-18"] = run_injections(frames, caches, new, truth, params, config_sha, clicks)
    # 6. 合成滚转。
    counting.counter = ledger.InflightCounter.open(replay.LEDGER, "replay_inference_frames", candidate=candidate,
                                                   note="合成滚转实推理帧（两臂；逐帧提交前落盘）")
    report["AC-19"] = run_roll(frames, caches, truth, params, config_sha, counting, modules, roll_clicks=roll_clicks)
    report["inference_frames_roll"] = counting.counter.settle()
    report["inference_frames_total"] = counting.inferences
    report["model_loads"] = counting.loads
    report["wall_s"] = round(time.monotonic() - started, 3)
    within = final_wall_check(report, started=started, limit_s=wall_limit_s)
    (output / "replay-report.json").write_text(json.dumps(report, indent=1, default=str) + "\n", encoding="utf-8")
    record_ledger("mini_new_disk_bytes", output_bytes(output), candidate,
                  f"正式回放输出目录 {output.name} 实测字节（find 普通文件，符号链接不计）；启动/运行日志另记")
    return 0 if within else 6


def run_injections(frames, caches, unperturbed, truth, params, config_sha, clicks) -> dict[str, Any]:
    """AC-18：删红车（= 被绑定键的匹配检测，取自未扰动新臂；不读真值）检测 m 帧；强制开新轨迹；auto_repair=off 对照。"""
    by_frame = {r["frame_id"]: r for r in unperturbed.frames}
    key = caches["unify_vehicle"]["key"]
    results: dict[str, Any] = {}
    for gap in replay.INJECTION_GAPS:
        perturbed = {}
        for f in range(replay.INJECTION_START, replay.INJECTION_START + gap):
            record = by_frame.get(f) or {}
            index = record.get("matched_det_index")
            if index is None or index < 0:
                continue
            frame = next(x for x in frames if x.frame_id == f)
            k = key(frame.image_sha256)
            rows = list(caches["unify_vehicle"]["cache"][k])
            perturbed[k] = [row for i, row in enumerate(rows) if i != index]
        cache = dict(caches["unify_vehicle"]["cache"])
        cache.update(perturbed)
        for repair in (True, False):
            wrapped = replay.CachedOrLiveModel(cache, None, replay.library_boxes)
            trace = replay.run_new_arm(cached_frames(frames, key), model_loader=lambda _p, w=wrapped: w,
                                       params=dataclasses.replace(params, auto_repair=repair), config_sha256=config_sha,
                                       clicks=clicks)
            results[f"delete_m{gap}_{'repair' if repair else 'repair_off'}"] = dict(
                replay.score_injection(trace, truth, params, start=replay.INJECTION_START, gap=gap),
                frames=_window_frames(trace, replay.INJECTION_START - 1, replay.INJECTION_START + gap + params.t_repair))
    bound = (by_frame.get(replay.INJECTION_START) or {}).get("track_key")
    wrapped = replay.CachedOrLiveModel(caches["unify_vehicle"]["cache"], None, replay.library_boxes)
    trace = replay.run_new_arm(cached_frames(frames, key), model_loader=lambda _p: wrapped, params=params, config_sha256=config_sha,
                               clicks=clicks,
                               association_exclusion=lambda f: {bound} if bound is not None and replay.INJECTION_START <= f < replay.INJECTION_START + 2 else set())
    forced = replay.force_new_track_report(trace, unperturbed, start=replay.INJECTION_START, frames=2)
    if forced["established"]:
        results["force_new_track"] = {**replay.score_injection(trace, truth, params, start=replay.INJECTION_START, gap=2), "injection": forced,
                                      "frames": _window_frames(trace, replay.INJECTION_START - 1, replay.INJECTION_START + 2 + params.t_repair)}
    else:
        # IR-8：没形成新键只记「注入未成立」，不当作已完成用例、不自动再跑。
        results["force_new_track"] = {"iou_verdict": "INJECTION_NOT_ESTABLISHED", "injection": forced}
    return results


def _window_frames(trace, first: int, last: int) -> list[dict[str, Any]]:
    """注入评分窗口的落盘逐帧记录（策略后原始检测、各键同帧 prior、绑定与效果）：C1-2 独立评分可只读复算。"""
    return [r for r in trace.frames if first <= r["frame_id"] <= last]


def run_roll(frames, caches, truth, params, config_sha, counting, modules, *, roll_clicks: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    """AC-19：热身 8 帧复用原始检测 + 变换 16 帧（两臂各自实推理）。

    AC-28/IR-7：基帧与选择输入只来自已校验的六基预登记剧本（`roll_clicks`：k → 人在原始 k−1 帧上的点击）；
    两臂、每基 12 种滚转复用同一点。真值只进本函数之外的 `score_` 评分（变换后多边形/删失），不生成点击。"""
    by_id = {f.frame_id: f for f in frames}
    sequences = []
    for base in sorted(roll_clicks):
        click = dict(roll_clicks[base])
        for omega in replay.ROLL_OMEGAS:
            for theta in replay.ROLL_THETAS:
                for sign in (1, -1):
                    sequences.append(roll_sequence(by_id, base, omega, theta, sign, caches, truth, params, config_sha, counting, modules, click))
    return {"bases": sorted(roll_clicks), "sequences": len(sequences), "inference_frames_per_arm": len(sequences) * replay.ROLL_FRAMES,
            "cells": replay.score_roll_cells(sequences), "per_sequence": sequences}


def roll_sequence(by_id, base, omega, theta, sign, caches, truth, params, config_sha, counting, modules, click: Mapping[str, Any]) -> dict[str, Any]:
    schedule = replay.roll_schedule(omega, theta, sign)
    warm = [by_id[f] for f in range(base - replay.ROLL_WARMUP, base)]
    rolled = []
    geometries = []
    for i, roll in enumerate(schedule):
        frame = by_id[base + i]
        homography = replay.roll_homography(frame.metadata, roll)
        rolled.append(replay.ReplayFrame(frame.frame_id, replay.warp_image(frame.image, homography),
                                         replay.rolled_metadata(frame.metadata, roll), frame.image_sha256 + f"#roll{roll:+.1f}"))
        geometries.append(replay.score_truth_geometry(truth[frame.frame_id], homography))
    warm_geometry = [replay.score_truth_geometry(truth[f.frame_id], None) for f in warm]
    evaluable = all(g is not None and not g["censored"] for g in warm_geometry) and geometries[0] is not None and not geometries[0]["censored"]
    if int(click["frame_id"]) != warm[-1].frame_id:
        raise ValueError(f"roll click for base {base} must be on raw warm-up frame {warm[-1].frame_id}")
    clicks = [{"frame_id": int(click["frame_id"]), "x_px": float(click["x_px"]), "y_px": float(click["y_px"]), "label": click.get("label", f"roll_base_{base}")}]
    outcomes = {}
    for arm, policy in (("baseline", "per_class"), ("new", "unify_vehicle")):
        key = caches[policy]["key"]
        model = replay.CachedOrLiveModel(caches[policy]["cache"], counting, replay.library_boxes)
        sequence_frames = cached_frames(warm, key) + rolled
        if arm == "baseline":
            records = baseline_runner.run_baseline_arm(modules, sequence_frames, spec_path=replay.SPEC, model_loader=lambda _p, m=model: m, clicks=clicks)
            per = [{"valid": r["ok"], "center": None if r["box_norm"] is None else
                    ((r["box_norm"][0] + r["box_norm"][2] / 2) * replay.WIDTH, (r["box_norm"][1] + r["box_norm"][3] / 2) * replay.HEIGHT)}
                   for r in records[replay.ROLL_WARMUP:]]
        else:
            trace = replay.run_new_arm(sequence_frames, model_loader=lambda _p, m=model: m, params=params, config_sha256=config_sha, clicks=clicks)
            per = [{"valid": r["observation"] == tm.OBSERVED and r["observed_box_norm"] is not None, "center": None if r["observed_box_norm"] is None else
                    ((r["observed_box_norm"][0] + r["observed_box_norm"][2] / 2) * replay.WIDTH, (r["observed_box_norm"][1] + r["observed_box_norm"][3] / 2) * replay.HEIGHT)}
                   for r in trace.frames[replay.ROLL_WARMUP:]]
        outcomes[arm] = replay.score_roll_sequence(per, geometries, params)
    return {"base": base, "omega": omega, "theta": theta, "sign": sign, "click": clicks[0], "evaluable": evaluable, **outcomes}
