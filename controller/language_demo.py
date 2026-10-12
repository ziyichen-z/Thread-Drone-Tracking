"""P1-ENG-LOOP-001 §3.8 `replay-demo`：夹具帧发布器 + 回放桩的可运行示例。

阶段 A 的「可运行示例」：不碰 Unity、不跑模型、不建正式 ID，只用

* `FixtureFramePublisher` 把 SFT-002 冻结评估集里的**真实帧字节**按
  `tethered-sensor-frame/v3` 发布进一个临时 runtime；
* `ReplayAdapter` 用同一批帧的**真实模型输出**（C2 `eval-adapter.jsonl`，截断样本取
  base `zero-shot.jsonl`）回答查询；

走一遍 P1/P2 的协议路径：designate 的四条出口（`unique` / `ambiguous` / `none` →
`retry_exhausted` / `parse_failed` → `retry_exhausted`）与 verify 的五种 verdict
（`consistent` / `drift` / `none` / `ambiguous` / `inconclusive`）。

**演示口径**（逐条写进 `demo-report.json`，不作证据）：① 用虚拟时钟推进，
`T_v` 取命令行值（缺省 1.0 s）而不是冻结的 10 s，好让走查在一秒内跑完；
② 演示索引是从冻结资产派生的子集，每行记录来源文件与原 `row_id`；
③ 演示不产生任何 AC-13…15 的 Play 证据。
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
import shutil
from typing import Any, Iterable, Mapping, Sequence

from . import language_bridge as bridge
from .gated_publisher import sha256_bytes
from .language_loop import (
    FixtureFramePublisher,
    LanguageSession,
    SessionConfig,
    build_k_receipt,
    inline_spawn,
    render_preview,
)
from .language_selector import ReplayAdapter, interpret
from .trackers import ScriptedTracker, TrackerResult

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_SURFACE = "the suv"


class DemoClock:
    """虚拟时钟：`monotonic` 与 `unix` 同步推进，演示因此瞬时且可复现。"""

    def __init__(self, start_unix_s: float = 1_800_000_000.0):
        self.unix_s = float(start_unix_s)
        self.monotonic_s = 1_000.0

    def advance(self, seconds: float) -> None:
        self.unix_s += float(seconds)
        self.monotonic_s += float(seconds)

    def unix(self) -> float:
        return self.unix_s

    def monotonic(self) -> float:
        return self.monotonic_s


@dataclass
class DemoAssets:
    root: Path
    blind_path: Path
    predictions_path: Path
    manifest_path: Path
    surface: str
    images: dict[str, Path] = field(default_factory=dict)
    boxes: dict[str, list[list[int]]] = field(default_factory=dict)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_demo_assets(
    *,
    frames_dir: Path,
    blind_path: Path,
    adapter_predictions: Path,
    base_predictions: Path | None,
    destination: Path,
    surface: str = DEMO_SURFACE,
) -> DemoAssets:
    """从冻结资产挑出一条指令的四种真实答案，写成演示自己的盲索引与预测文件。"""
    destination.mkdir(parents=True, exist_ok=True)
    blind = {row["row_id"]: row for row in _read_jsonl(blind_path)}
    adapter_rows = {row["row_id"]: row for row in _read_jsonl(adapter_predictions)}
    base_rows = (
        {row["row_id"]: row for row in _read_jsonl(base_predictions)}
        if base_predictions is not None and Path(base_predictions).is_file()
        else {}
    )
    chosen: dict[str, tuple[dict[str, Any], dict[str, Any], str]] = {}
    for row_id, row in blind.items():
        if row["surface"] != surface or row["g4"]:
            continue
        record = adapter_rows.get(row_id)
        if record is None:
            continue
        status = record.get("status_pred")
        if status in {"unique", "ambiguous", "none"} and status not in chosen:
            chosen[status] = (row, record, Path(adapter_predictions).name)
    for row_id, record in base_rows.items():
        if record.get("parse_error") == "TRUNCATED" and "parse_failed" not in chosen:
            row = blind.get(row_id)
            if row is not None:
                chosen["parse_failed"] = (row, record, Path(base_predictions).name)
    missing = {"unique", "ambiguous", "none"} - set(chosen)
    if missing:
        raise RuntimeError(f"冻结资产里没有 {surface!r} 的 {sorted(missing)} 样本")
    # 索引外的一帧：用来演示 `replay_miss` → 核验 `inconclusive`。
    spare = next(
        path
        for path in sorted(Path(frames_dir).glob("*.jpg"))
        if path.stem not in {Path(row["frame_path"]).stem for row, _, _ in chosen.values()}
    )

    demo_frames = destination / "frames"
    demo_frames.mkdir(parents=True, exist_ok=True)
    images: dict[str, Path] = {}
    manifest_rows: list[dict[str, Any]] = []
    blind_out: list[dict[str, Any]] = []
    predictions_out: list[dict[str, Any]] = []
    boxes: dict[str, list[list[int]]] = {}
    for status, (row, record, source) in sorted(chosen.items()):
        source_frame = Path(frames_dir) / Path(row["frame_path"]).name
        target = demo_frames / source_frame.name
        shutil.copy2(source_frame, target)
        images[status] = target
        blind_out.append(
            {
                "row_id": row["row_id"],
                "frame_path": f"frames/{source_frame.name}",
                "surface": row["surface"],
                "g4": row["g4"],
                "vocab": row["vocab"],
            }
        )
        predictions_out.append(record)
        boxes[status] = [list(box) for box in record.get("boxes_1000", [])]
        manifest_rows.append(
            {
                "demo_status": status,
                "row_id": row["row_id"],
                "surface": row["surface"],
                "frame_sha256": source_frame.stem,
                "source_predictions": source,
            }
        )
    spare_target = demo_frames / spare.name
    shutil.copy2(spare, spare_target)
    images["unindexed"] = spare_target

    blind_file = destination / "demo.blind.jsonl"
    predictions_file = destination / "demo.predictions.jsonl"
    blind_file.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in blind_out),
        encoding="utf-8",
    )
    predictions_file.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in predictions_out),
        encoding="utf-8",
    )
    manifest = {
        "work_id": "P1-ENG-LOOP-001",
        "purpose": "replay-demo（协议走查，不是证据）",
        "surface": surface,
        "rows": manifest_rows,
        "unindexed_frame_sha256": spare.stem,
        "source_blind": str(blind_path),
        "source_adapter_predictions": str(adapter_predictions),
        "source_base_predictions": str(base_predictions) if base_predictions else None,
    }
    manifest_path = destination / "demo-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return DemoAssets(
        root=destination,
        blind_path=blind_file,
        predictions_path=predictions_file,
        manifest_path=manifest_path,
        surface=surface,
        images=images,
        boxes=boxes,
    )


def _box_norm(box_1000: Sequence[int]) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = (float(value) / 1000.0 for value in box_1000)
    return (x1, y1, x2 - x1, y2 - y1)


def _far_box(box_1000: Sequence[int]) -> tuple[float, float, float, float]:
    """放在离模型框最远的角落：核验必判 `drift`（构造后当场核对 IoU < 0.5）。"""
    from .language_selector import VERIFY_IOU, iou_norm_xywh

    x, y, width, height = _box_norm(box_1000)
    size = 0.1
    # 与框心相对的那个角，且留出 1% 边距免得触发贴边核验。
    left = 0.02 if (x + width / 2.0) > 0.5 else 1.0 - size - 0.02
    top = 0.02 if (y + height / 2.0) > 0.5 else 1.0 - size - 0.02
    candidate = (left, top, size, size)
    overlap = iou_norm_xywh(candidate, (x, y, width, height))
    if overlap >= VERIFY_IOU:  # pragma: no cover - 构造上不可能
        raise RuntimeError(f"演示的漂移框与模型框 IoU={overlap:.3f}，不满足 < 0.5")
    return candidate


def _tracker_result(box: Sequence[float]) -> TrackerResult:
    return TrackerResult(tuple(float(value) for value in box), True, 1.0, "placeholder")


class DemoDriver:
    """把一次走查的动作、发布与断言集中在一处。"""

    def __init__(self, session: LanguageSession, publisher: FixtureFramePublisher,
                 clock: DemoClock, assets: DemoAssets):
        self.session = session
        self.publisher = publisher
        self.clock = clock
        self.assets = assets
        self.steps: list[dict[str, Any]] = []

    def tick(self, count: int = 1, advance_s: float = 0.05) -> None:
        for _ in range(count):
            self.clock.advance(advance_s)
            self.session.tick()

    def publish(self, key: str, *, frames: int = 1, hz: float = 5.0) -> None:
        payload = self.assets.images[key].read_bytes()
        for _ in range(frames):
            self.publisher.publish(payload)
            self.tick(1, advance_s=1.0 / hz)

    def request(self, action: str, **kwargs: Any) -> dict[str, Any]:
        request_id = f"demo-req-{len(self.steps) + 1}"
        holder = bridge.acquire_writer_lock(
            self.session.runtime, request_id=request_id, now=self.clock.unix()
        )
        bridge.write_request(
            self.session.runtime,
            session_id=self.session.session_id,
            request_id=request_id,
            action=action,
            **kwargs,
        )
        self.tick(2)
        bridge.release_writer_lock(
            self.session.runtime, request_id=request_id, pid=holder.pid
        )
        receipt = self.session.last_request or {}
        return receipt

    def record(self, label: str, **fields: Any) -> None:
        self.steps.append(
            {
                "step": len(self.steps) + 1,
                "label": label,
                "state": self.session.state,
                "reason": self.session.reason,
                "track_id": self.session.track_id,
                "last_verdict": self.session.last_verdict,
                "consecutive_alert": self.session.consecutive_alert,
                **fields,
            }
        )


class DemoRequiresPillow(RuntimeError):
    """AC-5 修订 1 之后没有预览就不能确认播种，所以走查必须在有 Pillow 的环境跑。"""


def require_preview_renderer() -> None:
    try:
        import PIL  # noqa: F401
    except ImportError as exception:
        raise DemoRequiresPillow(
            "replay-demo 需要 Pillow：AC-5 修订 1 规定没有生成预览时 confirm 必须"
            "REQUEST_INVALID，走查因此到不了播种。请用钉了 pillow==12.3.0 的环境跑"
            "（阶段 A 的 .venv-language，或本机已有同版 Pillow 的 .venv-yoloe）。"
        ) from exception


def run_demo(
    *,
    assets: DemoAssets,
    session_root: Path,
    verify_interval_s: float = 1.0,
) -> dict[str, Any]:
    require_preview_renderer()
    clock = DemoClock()
    runtime = Path(session_root) / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    publisher = FixtureFramePublisher(runtime, unix=clock.unix)
    adapter = ReplayAdapter(assets.blind_path, assets.predictions_path)
    receipt = build_k_receipt(
        hz=5.0,
        retained_frame_count=128,
        p95_s=2.0,
        host="demo",
        backend="replay",
        model_form="c2-adapter",
        model_identity=dict(adapter.identity),
        scenario_id="deterministic-loop-default",
    )
    unique_box = assets.boxes["unique"][0]
    ambiguous_box = assets.boxes["ambiguous"][1]
    # 每批发布的帧数 = 每帧一次 `update`，所以跟踪器脚本按批对齐：
    # 批 A 跟住模型框（`consistent`）、批 B 跑到角落（`drift`）、批 C 回到模型框
    # 但配的是 `none` 帧，于是 drift 与 none 交替累计到 2 → `SUSPECTED(lost)`。
    batch = max(1, int(verify_interval_s * 5) + 1)
    consistent = _tracker_result(_box_norm(unique_box))
    drifted = _tracker_result(_far_box(unique_box))
    ambiguous_result = _tracker_result(_box_norm(ambiguous_box))
    plans = [
        [consistent] * batch + [drifted] * batch + [consistent] * (batch + 8),
        [ambiguous_result] * (batch * 2 + 8),
    ]

    def tracker_factory() -> ScriptedTracker:
        return ScriptedTracker(plans.pop(0) if plans else [])

    session = LanguageSession(
        SessionConfig(
            session_id="demo-replay",
            session_root=Path(session_root),
            runtime=runtime,
            receipt=receipt,
            adapter=adapter,
            tracker_name="scripted",
            tracker_factory=tracker_factory,
            verify_interval_s=verify_interval_s,
            decode=lambda path: path.read_bytes(),
            worker_spawn=inline_spawn,
            # 用真实的 Pillow 渲染器：走查要证明预览门真的能通过，不用桩。
            preview=render_preview,
            monotonic=clock.monotonic,
            unix=clock.unix,
            planned_duration_s=10_000.0,
        )
    )
    session.start()
    driver = DemoDriver(session, publisher, clock, assets)
    instruction = bridge.parse_instruction(assets.surface)
    try:
        # (1) designate `unique` → 必须人工确认 → 播种。
        driver.publish("unique")
        driver.request("ask", instruction=instruction)
        driver.tick(3)
        driver.record("designate_unique", candidates=len(session.candidates))
        driver.request("confirm", candidate_index=0, token=session.candidate_result_id)
        driver.tick(2)
        driver.record("seeded")

        # (2) 核验 `consistent` → `drift` → `none`（none/drift 交替累计到 2）。
        for key, label in (("unique", "verify_consistent"), ("unique", "verify_drift"),
                           ("none", "verify_none")):
            driver.publish(key, frames=batch)
            driver.tick(3)
            driver.record(label)

        # (3) 人工判丢 → 重新指定（`ambiguous` → 选一）。
        driver.request("confirm_lost", token=session.suspect_id)
        driver.tick(2)
        driver.record("confirm_lost")
        driver.publish("ambiguous")
        driver.request("respecify", instruction=instruction)
        driver.tick(3)
        driver.record("designate_ambiguous", candidates=len(session.candidates))
        driver.request("confirm", candidate_index=1, token=session.candidate_result_id)
        driver.tick(2)
        driver.record("reseeded")

        # (4) 核验 `ambiguous` → 立即疑似 → 人工驳回。
        driver.publish("ambiguous", frames=batch)
        driver.tick(3)
        driver.record("verify_ambiguous")
        driver.request("dismiss", token=session.suspect_id)
        driver.tick(2)
        driver.record("dismissed")

        # (5) 索引外的帧 → `replay_miss` → 核验 `inconclusive`。
        driver.publish("unindexed", frames=batch)
        driver.tick(3)
        driver.record("verify_inconclusive")

        # (6) 人工 `release` → `LOST`。
        driver.request("release", token=session.track_id)
        driver.tick(2)
        driver.record("released")

        # (7) designate `none` 的有界重试 → `retry_exhausted`。
        driver.publish("none")
        driver.request("respecify", instruction=instruction)
        for _ in range(3):
            driver.publish("none")
            driver.tick(3)
        driver.record("designate_none_exhausted")

        # (8) designate `parse_failed`（base 的截断样本）→ `retry_exhausted`。
        parse_row = json.loads(assets.manifest_path.read_text(encoding="utf-8"))
        truncated = next(
            (row for row in parse_row["rows"] if row["demo_status"] == "parse_failed"),
            None,
        )
        if truncated is not None:
            driver.publish("parse_failed")
            driver.request(
                "ask", instruction=bridge.parse_instruction(truncated["surface"])
            )
            for _ in range(3):
                driver.publish("parse_failed")
                driver.tick(3)
            driver.record("designate_parse_failed_exhausted")

        driver.request("stop")
        driver.tick(2)
        driver.record("stopped")
    finally:
        if session.state != "TERMINAL":
            session.stop()
        session.close()

    results = [
        json.loads(line)
        for line in session.results_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    verdicts = sorted(
        {
            row["verify"]["verdict"]
            for row in results
            if isinstance(row.get("verify"), dict)
        }
    )
    statuses = sorted(
        {row["status"] for row in results if row.get("purpose") == "designate"}
    )
    written = [
        json.loads(line)
        for line in session.receipts_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {
        "work_id": "P1-ENG-LOOP-001",
        "demo": "replay-demo",
        "caveats": [
            "虚拟时钟；T_v 取命令行值而非冻结的 10 s",
            "演示索引是冻结资产的派生子集（见 demo-manifest.json）",
            "不产生 AC-13…15 的 Play 证据，不创建正式 scenario/session/run ID",
        ],
        "session_dir": str(session.session_dir),
        "steps": driver.steps,
        "designate_statuses": statuses,
        "verify_verdicts": verdicts,
        "retired_track_ids": session.retired_track_ids,
        "publish_receipts": {
            "total": len(written),
            "written": sum(1 for row in written if row["outcome"] == "WRITTEN"),
            "rejected": sum(1 for row in written if row["outcome"] == "PUBLISH_REJECTED"),
            "muted": sum(1 for row in written if row["outcome"] == "MUTED_DROPPED"),
        },
        "final_state": session.state,
    }


def run_replay_demo(arguments: argparse.Namespace) -> int:
    try:
        require_preview_renderer()
    except DemoRequiresPillow as exception:
        print(str(exception))
        return 8
    session_root = Path(arguments.session_root)
    session_root.mkdir(parents=True, exist_ok=True)
    assets = build_demo_assets(
        frames_dir=Path(arguments.frames),
        blind_path=Path(arguments.replay_blind),
        adapter_predictions=Path(arguments.replay_predictions),
        base_predictions=getattr(arguments, "base_predictions", None),
        destination=session_root / "demo-assets",
    )
    report = run_demo(assets=assets, session_root=session_root)
    destination = session_root / "demo-report.json"
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n报告：{destination}")
    return 0
