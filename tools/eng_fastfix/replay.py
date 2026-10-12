"""P1-ENG-FASTFIX-001 §3.8 / AC-7（K3/K4）：离线重捕回放（Mac mini，FASTFIX:A:1 内）。

输入只限 USER-4A 同批原始帧/位姿（七题答复 SOURCE 限用途扩至本项 AC-7；`common.ADMITTED_FRAMES`），真值不进本模块
（评分只在 `score.py` 的 `score_*`，本模块不导入它、不打开真值路径）。剧本由实现角色只看原始帧登记，运行前提交、sha 入证据。

一次运行：
1. 前置（零模型）：剧本校验（schema、登记人、点击帧字节 sha、像素在画内）、准入帧对 `SHA256SUMS` 现算核对、账本按剩余量拦截；
2. 每候选一次 live 推理建检测缓存（`CountingModel` 计加载与推理帧；缓存键 = `DetAssocTracker.detection_cache_key`）；
3. 基线（无注入）：点击帧前 `warmup` 帧起喂缓存帧，点击帧 k 处理后提交（历史头 = k，与 `run_new_arm` 同序）；
4. 逐注入、两臂（`auto_reacquire = on/off`）：注入帧 = 绑定提交帧 + {20, 40, …}（≤ 12 次，越过末帧即止）；注入帧系统状态
   （非真值：管理器有绑定且本帧 OBSERVED）不满足 → `not_applicable`。满足则从头重放到注入帧，调用与会话同一的
   `prepare_reacquire_hint`/`release_binding`/`on_teardown`，新建 `DetAssocTracker` 常驻实例，跳过 3 帧模拟重建，
   就绪帧 = 注入帧 + 4（`resident_loop_started` 等价），开窗后从缓存续喂（`live=None`，未命中即报错，零推理）；
5. 逐注入输出：`committed | failed | ambiguous | canceled | skipped(cause) | not_applicable | invalid_input`、提交用时（帧）、
   证据帧、缺失证据项；提交后另记 10 帧被跟实例框（供 `score.py` 算真值 IoU）。

会话时钟在回放中取帧元数据 `capture_monotonic_s`（处理零延迟的等价时钟；每帧都是本批最新帧、无发布门 → 结算按
PUBLISHED 记提示候选）。
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(REPO_ROOT))

from controller import target_manager as tm  # noqa: E402
from controller.resident_core import full_kf_state_from_associator, library_kf_predictor  # noqa: E402
from tools.eng_capture.replay import CacheFrame, CachedOrLiveModel, CountingModel, boxes_rows, library_boxes  # noqa: E402
from tools.eng_fastfix import ledger as fastfix_ledger  # noqa: E402
from tools.eng_fastfix.common import ADMITTED_FRAMES, ADMITTED_SUMS, OUTPUT_ROOT, PROJECT_ROOT  # noqa: E402

SCRIPT_SCHEMA = "p1-eng-fastfix-001-ac7-script/v1"
OUTPUT_SCHEMA = "p1-eng-fastfix-001-ac7-replay/v1"
SPEC = PROJECT_ROOT / "config" / "det-assoc-v1.models.json"
WIDTH, HEIGHT = 640, 480
SEG_END = "publish_expired"
HZ = 5.0
OUTCOMES = ("committed", "failed", "ambiguous", "canceled", "skipped", "not_applicable", "invalid_input")


class LaunchRefused(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frame_paths(frame_id: int, frames: Path = ADMITTED_FRAMES) -> tuple[Path, Path]:
    stem = f"frame_{int(frame_id):010d}"
    return Path(frames) / f"{stem}.jpg", Path(frames) / f"{stem}.json"


def admitted_frame_ids(frames: Path = ADMITTED_FRAMES) -> list[int]:
    return sorted(int(p.stem.split("_")[1]) for p in Path(frames).glob("frame_*.jpg"))


# --- 前置（零模型） ----------------------------------------------------------------------------


def check_input(frames: Path = ADMITTED_FRAMES, sums_path: Path = ADMITTED_SUMS, *, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """准入帧 jpg/json 现算 sha 对 `SHA256SUMS` 对应行（只核帧，不读真值）；不符即 STOP（S-ORIG）。"""
    sums: dict[str, str] = {}
    for line in Path(sums_path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, _, name = line.partition("  ")
            sums[name.strip()] = digest.strip()
    mismatches: list[str] = []
    files = 0
    for frame_id in admitted_frame_ids(frames):
        for path in frame_paths(frame_id, frames):
            relative = str(Path(path).resolve().relative_to(Path(root).resolve()))
            files += 1
            if sums.get(relative) != sha256_file(path):
                mismatches.append(relative)
    return {"check": "S-ORIG", "files": files, "frames": len(admitted_frame_ids(frames)), "sha_mismatches": mismatches,
            "ok": files > 0 and not mismatches}


def load_script(path: Path, *, frames: Path = ADMITTED_FRAMES) -> tuple[dict[str, Any], str]:
    """剧本启动前校验：schema/登记人、点击帧存在且帧字节 sha 一致、像素有限且在画内、注入规则字段齐全。"""
    if path is None or not Path(path).is_file():
        raise LaunchRefused("AC-7: the preregistered script is missing")
    data = Path(path).read_bytes()
    try:
        document = json.loads(data.decode("utf-8"))
    except ValueError as error:
        raise LaunchRefused(f"AC-7: script unreadable ({error})") from error
    if document.get("schema_version") != SCRIPT_SCHEMA or not document.get("registered_by"):
        raise LaunchRefused("AC-7: script schema/registrant invalid")
    click = document.get("click") or {}
    try:
        frame_id, x_px, y_px = int(click["frame_id"]), float(click["x_px"]), float(click["y_px"])
    except (KeyError, TypeError, ValueError) as error:
        raise LaunchRefused(f"AC-7: malformed click {click!r}") from error
    image = frame_paths(frame_id, frames)[0]
    if not image.is_file() or click.get("image_sha256") != sha256_file(image):
        raise LaunchRefused(f"AC-7: click frame {frame_id} image sha mismatch")
    if not (math.isfinite(x_px) and math.isfinite(y_px) and 0 <= x_px < WIDTH and 0 <= y_px < HEIGHT):
        raise LaunchRefused("AC-7: click point out of frame")
    rule = document.get("injection_rule") or {}
    for key in ("offset_step", "max_injections", "rebuild_skip_frames", "warmup_frames", "follow_frames_after_commit"):
        if not isinstance(rule.get(key), int) or rule[key] < 0:
            raise LaunchRefused(f"AC-7: injection_rule.{key} must be a non-negative integer")
    return document, hashlib.sha256(data).hexdigest()


# --- 帧与缓存 ---------------------------------------------------------------------------------


@dataclasses.dataclass
class ReplayFrame:
    frame_id: int
    image: Any
    metadata: dict[str, Any]
    image_sha256: str


def load_frames(frame_ids: Sequence[int], *, frames: Path = ADMITTED_FRAMES, decode: Callable[[Path], Any] | None = None) -> list[ReplayFrame]:
    out = []
    for frame_id in frame_ids:
        image_path, json_path = frame_paths(frame_id, frames)
        data = image_path.read_bytes()
        image = decode(image_path) if decode is not None else None
        out.append(ReplayFrame(frame_id, image, json.loads(json_path.read_text(encoding="utf-8")), hashlib.sha256(data).hexdigest()))
    return out


def build_cache(frames: Sequence[ReplayFrame], model: Any, *, tracker_factory: Callable[..., Any]) -> tuple[dict, Callable[[str], tuple]]:
    """捕获策略（`unify_vehicle`）对所需帧各推理一次（共用一次加载的模型）；缓存键含帧 sha、权重 sha、推理参数。"""
    detector = tracker_factory(spec_path=SPEC, device=None, model_loader=lambda _p: model, mode="resident", class_policy="unify_vehicle")
    cache: dict = {}
    for frame in frames:
        boxes = detector._detect(frame.image)  # noqa: SLF001 — 与会话 `step` 同一检测调用
        cache[detector.detection_cache_key(frame.image_sha256)] = boxes_rows(boxes)
    return cache, (lambda sha, d=detector: d.detection_cache_key(sha))


def cached(frames: Sequence[ReplayFrame], key: Callable[[str], tuple]) -> list[ReplayFrame]:
    return [dataclasses.replace(frame, image=CacheFrame(key(frame.image_sha256))) for frame in frames]


# --- 回放运行体 ---------------------------------------------------------------------------------


class CaptureRun:
    """一条捕获链：常驻 `DetAssocTracker`（`unify_vehicle` + `pose-center` + 捕获历史视图）+ 捕获模式 `TargetManager`。"""

    def __init__(self, model_loader: Callable[[Path], Any], params: tm.CaptureParams, fastfix: tm.FastfixParams,
                 config_sha256: str, fastfix_sha256: str, *, tracker_factory: Callable[..., Any] | None = None,
                 ground_plane_y_m: float = 0.2):
        from controller.det_assoc_tracker import DetAssocTracker  # noqa: PLC0415

        self._factory = tracker_factory or DetAssocTracker
        self._model_loader = model_loader
        self.manager = tm.TargetManager(params, mode="capture", config_sha256=config_sha256,
                                        inputs=tm.InputsLog(None, chain=True), fastfix=fastfix,
                                        fastfix_config_sha256=fastfix_sha256, ground_plane_y_m=ground_plane_y_m)
        self.tracker = self.new_tracker()
        self.manager.attach_port(self.tracker.core)
        self.candidates: list[tm.HintCandidate] = []
        self.predictor: Any = None
        self.reacq_prior_reasons: list[dict[str, Any]] = []

    def new_tracker(self) -> Any:
        return self._factory(spec_path=SPEC, device="cpu", model_loader=self._model_loader, mode="resident",
                             class_policy="unify_vehicle", gmc_source="pose-center", history_view="capture")

    def feed(self, frame: ReplayFrame, *, click: Mapping[str, Any] | None = None) -> Any:
        self.tracker.step(frame.image, frame.frame_id, frame.metadata)
        entry = self.tracker.history(frame.frame_id)
        if click is not None:
            # §3.3 ① 替换请求：本帧已入历史、尚未授权；提交帧（历史头）= 本帧（与 `run_new_arm` 同序）。
            self.manager.click(request_id=str(click.get("label") or "red_car"), x_px=float(click["x_px"]), y_px=float(click["y_px"]),
                               frame_id=frame.frame_id, image_sha256=frame.image_sha256, actual_image_sha256=frame.image_sha256,
                               history=self.tracker.core.history, head_frame_id=frame.frame_id, ended_ids=self.tracker.core.ended_ids)
        reacq = None
        if self.manager.reacquire_open and self.manager.binding is None:
            reacq = dict(self.manager.reacquire_prior_for(entry, self.predictor) or {})
            reacq["at_monotonic_s"] = float(frame.metadata["capture_monotonic_s"])
            if reacq.get("prior") is None:
                self.reacq_prior_reasons.append({"frame_id": frame.frame_id, "reason": reacq.get("prior_reason")})
        outcome = self.manager.on_frame(entry, newest=True, reacq=reacq)
        self._note_candidate(entry)
        return outcome

    def _note_candidate(self, entry: Any) -> None:
        """与会话 `_note_hint_candidate` 同判据：管理器本帧已接受观测 → 深复制绑定键完整 KF；回放无发布门，结算记 PUBLISHED。"""
        manager = self.manager
        if manager.binding is None or manager.belief is None:
            return
        f = int(entry.frame_id)
        if manager.belief.observation_status != tm.OBSERVED or manager.belief.t0 != f:
            return
        key = manager.binding.track_key
        state = full_kf_state_from_associator(self.tracker.associator, key, sensor_frame_id=f,
                                              library_frame_id=int(entry.library_frame_id))
        self.candidates.append(tm.HintCandidate(f, key, state, tm.pose_metadata_of(entry), "PUBLISHED"))
        del self.candidates[: -(manager.fastfix.t_reacq + 2)]  # type: ignore[union-attr]

    def observed_at(self, frame_id: int) -> bool:
        belief = self.manager.belief
        return (self.manager.binding is not None and belief is not None and belief.observation_status == tm.OBSERVED
                and belief.t0 == int(frame_id))

    def bound_box(self, frame_id: int) -> list[float] | None:
        binding = self.manager.binding
        entry = self.tracker.history(frame_id)
        if binding is None or entry is None:
            return None
        row = entry.row(binding.track_key)
        return None if row is None else [float(v) for v in row.box_norm]

    def escalate(self, escalation_frame: int, *, auto_reacquire: bool) -> tm.ReacquireHint | None:
        """与会话同一路径：提示生成 → `release_binding`（有提示不取消任务）→ `on_teardown` → 新载体（新 `DetAssocTracker`）。"""
        hint = self.manager.prepare_reacquire_hint(seg_end=SEG_END, timing_escalation=True, escalation_frame=escalation_frame,
                                                   auto_reacquire=auto_reacquire, candidates=list(self.candidates))
        if hint is not None:
            self.predictor = library_kf_predictor(self.tracker.associator, hint.track_key)
        self.manager.release_binding(SEG_END, cancel_task=hint is None)
        self.manager.on_teardown(SEG_END)
        self.tracker = self.new_tracker()
        self.manager.attach_port(self.tracker.core)
        self.candidates = []
        return hint


def run_base(frames: Sequence[ReplayFrame], click: Mapping[str, Any], factory: Callable[[], CaptureRun]) -> list[dict[str, Any]]:
    run = factory()
    trace = []
    for frame in frames:
        run.feed(frame, click=click if frame.frame_id == int(click["frame_id"]) else None)
        trace.append({"frame_id": frame.frame_id, "observed": run.observed_at(frame.frame_id),
                      "track_key": run.manager.track_key, "box_norm": run.bound_box(frame.frame_id)})
    return trace


def run_injection(frames: Sequence[ReplayFrame], click: Mapping[str, Any], f_inj: int, arm: str,
                  factory: Callable[[], CaptureRun], rule: Mapping[str, Any]) -> dict[str, Any]:
    """一次注入、一臂：从头重放到注入帧 → 升级拆载体 → 跳过 `rebuild_skip_frames` 帧 → 就绪帧开窗 → 续喂到窗口结束
    （提交后再记 `follow_frames_after_commit` 帧被跟实例框）。"""
    by_id = {frame.frame_id: frame for frame in frames}
    run = factory()
    record: dict[str, Any] = {"f_inj": f_inj, "arm": arm}
    for frame in frames:
        if frame.frame_id > f_inj:
            break
        run.feed(frame, click=click if frame.frame_id == int(click["frame_id"]) else None)
    if not run.observed_at(f_inj):
        record.update(outcome="not_applicable", cause="not_tracking_observed_at_injection")
        return record
    record["escalated_track_key"] = run.manager.track_key
    hint = run.escalate(f_inj, auto_reacquire=arm == "on")
    f_ready = f_inj + 1 + int(rule["rebuild_skip_frames"])
    record["f_ready"] = f_ready
    record["f_last"] = None if hint is None else hint.f_last
    if f_ready not in by_id:
        record.update(outcome="invalid_input", cause="ready_frame_beyond_input")
        return record
    run.feed(by_id[f_ready])  # 新载体起点帧（窗口事件之前处理，与会话 `loop.start` 同序）
    if hint is None:
        skipped = [e for e in run.manager.events if e["kind"] == "reacquire_skipped"]
        record.update(outcome="skipped", cause=skipped[-1]["reason"] if skipped else None)
        # 对照臂：窗口长度内续喂，核零自动提交。
        for frame_id in range(f_ready + 1, f_ready + run.manager.fastfix.t_reacq + 1):  # type: ignore[union-attr]
            if frame_id in by_id:
                run.feed(by_id[frame_id])
        record["auto_commits"] = len([e for e in run.manager.events if e["kind"] == "reacquired_after_rebuild"])
        record["binding_after_window"] = run.manager.track_key
        return record
    run.manager.open_reacquire_window(f_ready=f_ready, m_ready=float(by_id[f_ready].metadata["capture_monotonic_s"]), hz=HZ)
    result = None
    frame_id = f_ready
    while result is None:
        frame_id += 1
        if frame_id not in by_id:
            record.update(outcome="invalid_input", cause="window_beyond_input")
            break
        run.feed(by_id[frame_id])
        result = run.manager.take_reacquire_result()
    record["missing_evidence"] = list(run.reacq_prior_reasons)
    evidence = [e for e in run.manager.events if e["kind"] == "tm_event" and e.get("type") == "reacquire_evidence"]
    record["evidence_events"] = [{"frame_id": e["frame_id"], "accepted": e["accepted"], "reason": e.get("reason"),
                                  "candidates": e.get("candidates")} for e in evidence]
    if result is None:
        return record
    kind = result.get("result")
    if kind == "committed":
        commit_frame = int(result["frame_id"])
        done = [e for e in run.manager.events if e["kind"] == "reacquired_after_rebuild"][-1]
        record.update(outcome="committed", commit_frame=commit_frame, track_key=result["track_key"],
                      latency_frames_from_escalation=commit_frame - f_inj, latency_frames_from_ready=commit_frame - f_ready,
                      evidence_frames=done.get("evidence_frames"))
        follow = [{"frame_id": commit_frame, "box_norm": run.bound_box(commit_frame), "observed": run.observed_at(commit_frame)}]
        for later in range(commit_frame + 1, commit_frame + 1 + int(rule["follow_frames_after_commit"])):
            if later not in by_id:
                break
            run.feed(by_id[later])
            follow.append({"frame_id": later, "box_norm": run.bound_box(later), "observed": run.observed_at(later),
                           "track_key": run.manager.track_key})
        record["followed"] = follow
    elif kind == "ambiguous":
        record.update(outcome="ambiguous", cause=result.get("cause"), frame_id=result.get("frame_id"))
    elif kind == "canceled":
        record.update(outcome="canceled", cause=result.get("cause"))
    else:
        record.update(outcome="failed", cause=result.get("cause"), frame_id=result.get("frame_id"))
    return record


def injection_frames(commit_frame: int, last_frame: int, rule: Mapping[str, Any]) -> list[int]:
    step, limit = int(rule["offset_step"]), int(rule["max_injections"])
    return [commit_frame + step * i for i in range(1, limit + 1) if commit_frame + step * i <= last_frame]


def run_ac7(frames: Sequence[ReplayFrame], script: Mapping[str, Any], factory: Callable[[], CaptureRun]) -> dict[str, Any]:
    click = dict(script["click"])
    rule = script["injection_rule"]
    base = run_base(frames, click, factory)
    commits = [row for row in base if row["frame_id"] == int(click["frame_id"]) and row["track_key"] is not None]
    report: dict[str, Any] = {"base": base, "injections": []}
    if not commits:
        report["bind"] = {"committed": False}
        return report
    commit_frame = commits[0]["frame_id"]
    report["bind"] = {"committed": True, "commit_frame": commit_frame, "track_key": commits[0]["track_key"]}
    last = frames[-1].frame_id
    for f_inj in injection_frames(commit_frame, last, rule):
        for arm in ("on", "off"):
            report["injections"].append(run_injection(frames, click, f_inj, arm, factory, rule))
    return report


def summarize(report: Mapping[str, Any]) -> dict[str, Any]:
    """无真值读数：逐臂结果计数、提交用时分布（带 n）。"""
    out: dict[str, Any] = {}
    for arm in ("on", "off"):
        rows = [r for r in report.get("injections", []) if r["arm"] == arm]
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["outcome"]] = counts.get(row["outcome"], 0) + 1
        latencies = [r["latency_frames_from_escalation"] for r in rows if r["outcome"] == "committed"]
        out[arm] = {"n_injected": len(rows), "counts": counts, "n_committed": counts.get("committed", 0),
                    "commit_latency_frames": sorted(latencies)}
    out["off_arm_auto_commits"] = sum(r.get("auto_commits", 0) for r in report.get("injections", []) if r["arm"] == "off") + \
        len([r for r in report.get("injections", []) if r["arm"] == "off" and r["outcome"] == "committed"])
    return out


def output_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in Path(root).rglob("*") if p.is_file() and not p.is_symlink())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-FASTFIX-001 AC-7 离线重捕回放")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check-input")
    check.add_argument("--output", type=Path, default=None)
    run = sub.add_parser("run")
    run.add_argument("--script", type=Path, required=True)
    run.add_argument("--candidate", type=int, required=True)
    run.add_argument("--ledger", type=Path, required=True)
    run.add_argument("--output", type=Path, default=None)
    arguments = parser.parse_args(argv)
    if arguments.command == "check-input":
        report = check_input()
        if arguments.output is not None:
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            arguments.output.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report["ok"] else 3
    os.environ.setdefault("YOLO_OFFLINE", "True")
    os.environ.setdefault("YOLO_AUTOINSTALL", "False")
    started_unix, started = time.time(), time.monotonic()
    try:
        script, script_sha = load_script(arguments.script)
        input_report = check_input()
        if not input_report["ok"]:
            raise LaunchRefused(f"S-ORIG: admitted frames differ from SHA256SUMS: {input_report['sha_mismatches'][:5]}")
        fastfix_ledger.check_launch(fastfix_ledger.read(arguments.ledger), {"yolo_loads": 1, "wall_s": 600})
    except (LaunchRefused, fastfix_ledger.LedgerRefused) as refusal:
        print(f"LAUNCH_REFUSED: {refusal}", file=sys.stderr)
        return 4
    from controller.det_assoc_tracker import DetAssocTracker, _default_model_loader, _verify_file  # noqa: PLC0415
    import cv2  # noqa: PLC0415

    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = Path(arguments.output or OUTPUT_ROOT / "replay" / f"candidate{arguments.candidate}-{stamp}")
    output.mkdir(parents=True, exist_ok=False)
    params, config_sha, _ = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)
    fastfix, fastfix_sha, _ = tm.load_fastfix_config(tm.DEFAULT_FASTFIX_CONFIG, params, HZ)
    click_frame = int(script["click"]["frame_id"])
    ids = [f for f in admitted_frame_ids() if f >= click_frame - int(script["injection_rule"]["warmup_frames"])]
    frames = load_frames(ids, decode=lambda path: cv2.imread(str(path)))
    weights = json.loads(SPEC.read_text(encoding="utf-8"))["weights"]
    weights_path = PROJECT_ROOT / weights["path"]
    _verify_file(weights_path, weights["sha256"], int(weights["size_bytes"]), "weights")  # 加载前核身份（不符即拒，不记加载）
    fastfix_ledger.record(arguments.ledger, "yolo_loads", 1, note=f"AC-7 回放候选 {arguments.candidate} 真实构造（尝试即记，失败不返还）")
    counting = CountingModel(_default_model_loader)
    model = counting.load(weights_path)
    cache, key = build_cache(frames, model, tracker_factory=DetAssocTracker)
    cache_rows = {"|".join(str(part) for part in k): v for k, v in cache.items()}
    (output / "detections.json").write_text(json.dumps(cache_rows) + "\n", encoding="utf-8")
    wrapped = CachedOrLiveModel(cache, None, library_boxes)  # 注入运行全部取缓存（零推理，未命中即报错）
    replay_frames = cached(frames, key)

    def factory() -> CaptureRun:
        return CaptureRun(lambda _p: wrapped, params, fastfix, config_sha, fastfix_sha, tracker_factory=DetAssocTracker)

    report = run_ac7(replay_frames, script, factory)
    finished = time.monotonic()
    meta = {
        "schema_version": OUTPUT_SCHEMA,
        "candidate": arguments.candidate,
        "script_sha256": script_sha,
        "script": script,
        "weights_sha256": weights["sha256"],
        "capture_config_sha256": config_sha,
        "fastfix_config_sha256": fastfix_sha,
        "frames": [ids[0], ids[-1], len(ids)],
        "model_loads": counting.loads,
        "inference_frames": counting.inferences,
        "cache_hits": wrapped.hits,
        "input_check": input_report,
        "started_unix_s": started_unix,
        "wall_s": round(finished - started, 3),
        "summary": summarize(report),
    }
    (output / "replay-output.json").write_text(json.dumps({**meta, **report}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    meta["output_bytes"] = output_bytes(output)
    print(json.dumps({k: v for k, v in meta.items() if k not in ("script", "input_check")} | {"output": str(output)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
