"""SR (b) 真实应答器（合同 §2.1 SR (b)、§3.2、AC-5/AC-6；板上运行）。

真实 `controller.track_loop.TrackLoop` + 补跑D 方形 TRT FP16 `det-assoc-v1` 插件（经 `fastlayer_bench.make_plugin`
构造注入，规格/权重/关联参数一字不改；`controller/` 零改动）。

- **引擎身份**：路径与 sha256 由桌面机运行时从 `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1.engines.640.export」
  解析后传入（`engine_from_fastlayer`），板上开跑前复核；不符即不加载、记 `engine_identity_mismatch` 并退出（停该路径）。
- **init 框**：板上镜像收到的**首帧**上、检测器自身 `target` 类（规格 `classes` 中值为 `"target"` 的类号）**最高分框**
  （`select_init_box`）；不读真值、不用 S1/S2 的离线用户框替身。首帧无 `target` 类检测即记 `init_no_target_detection`、不初始化。
- **TrackLoop 构造**：照 `run_tracker` 的非会话分支（`condition follow`、`ground_plane_y_m 0.2`、`maximum_ground_range_m 1000`、
  `expires_after_s 1.0`；无 rate/qualification/reanchor/body planner）。驱动：镜像 `latest.json` 的 `frame_id` 变化即
  `process_available(latest)`；TrackLoop 终止（`GAP`/`REINIT_REQUIRED` 等）后**不重播种、不重启**，进程继续存活并记录到达的新帧
  （AC-6「TrackLoop 终止/继续语义」）。
- **记录**：`track-receipts.jsonl`（每次处理的 seen/done 时戳、`capture_age_s` = 板墙钟 − `capture_unix_s`、`load_elapsed_s` =
  观测写入 − 看到新帧（单调钟）、写桥时刻、终止事件）；TrackLoop 逐帧记录经注入的记录器写 `track-records.jsonl`，键 `state`
  改名 `loop_state`（避免与 AC-12 禁键 `"state"` 混淆，同 IR-12 (c) 先例；交接 IR-21 待裁定），其余键与值原样。
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable, Mapping, Sequence

from tools.eng_jet import common

TRACK_ID = "eng-jet-real"
CONDITION = "follow"
GROUND_PLANE_Y_M = 0.2
MAXIMUM_GROUND_RANGE_M = 1000.0
EXPIRES_AFTER_S = 1.0
POLL_S = 0.002
DEVICE = "cuda:0"
STATE_KEY_RENAMED = "loop_state"


def engine_from_fastlayer(path: Path | None = None, tag: str = "640") -> dict[str, Any]:
    """`-fastlayer.json`「S1.engines.<tag>.export」→ {engine, sha256, size_bytes}（运行时解析，不手写）。"""
    document = common.read_json(path or common.evidence("fastlayer.json"))
    export = document["S1"]["engines"][tag]["export"]
    return {"engine": export["engine"], "sha256": export["sha256"], "size_bytes": export.get("size_bytes"),
            "source": f"docs/evidence/P1-ENG-JET-001-fastlayer.json「S1.engines.{tag}.export」"}


def target_class_id(spec: Mapping[str, Any]) -> int:
    matches = [int(key) for key, name in spec.get("classes", {}).items() if str(name) == "target"]
    if len(matches) != 1:
        raise ValueError(f"规格 classes 中 target 类不唯一：{spec.get('classes')!r}")
    return matches[0]


def select_init_box(rows: Sequence[Sequence[float]], target_class: int) -> dict[str, Any] | None:
    """检测行 `[x, y, w, h, conf, cls]`（归一化 xywh）→ `target` 类最高分框；并列取先出现者；无则 None。"""
    best: tuple[int, Sequence[float]] | None = None
    for index, row in enumerate(rows):
        if int(row[5]) != target_class:
            continue
        if best is None or float(row[4]) > float(best[1][4]):
            best = (index, row)
    if best is None:
        return None
    index, row = best
    return {"box_norm": [float(v) for v in row[:4]], "score": float(row[4]), "class_id": int(row[5]), "row_index": index,
            "candidates_target_class": sum(1 for r in rows if int(r[5]) == target_class), "detections_total": len(rows)}


class RecordSink:
    """TrackLoop 注入记录器：逐帧记录写 JSONL（键 `state` → `loop_state`），并保留最近一条供终止事件读取。"""

    def __init__(self, path: Path):
        self.path = Path(path).expanduser()
        common.refuse_protected(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")
        self.last: dict[str, Any] | None = None
        self.count = 0

    def append(self, record: Mapping[str, Any]) -> None:
        row = {(STATE_KEY_RENAMED if key == "state" else key): value for key, value in record.items()}
        self.last = row
        self.count += 1
        self._handle.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()


def recording_publisher(runtime: Path, expires_after_s: float, sink: list[dict[str, Any]]) -> Any:
    """`RuntimePublisher` 子类：写桥函数不变，只在每次写入后记板墙钟/单调钟时刻（返回时延测量用）。"""
    from controller.track_loop import RuntimePublisher  # noqa: PLC0415

    class RecordingPublisher(RuntimePublisher):
        def _note(self, kind: str, **fields: Any) -> None:
            unix, mono = time.time(), time.monotonic()
            sink.append({"kind": kind, "written_unix": round(unix, 6), "written_mono": round(mono, 6), **fields})

        def hold_body(self) -> Path:
            path = super().hold_body()
            self._note("hold_body")
            return path

        def set_nadir(self) -> Path:
            path = super().set_nadir()
            self._note("set_nadir")
            return path

        def observation(self, frame_id: int, track_id: str, box_norm: Any, confidence: float) -> Path:
            path = super().observation(frame_id, track_id, box_norm, confidence)
            self._note("observation", frame_id=int(frame_id))
            return path

        def look_at(self, point_world_m: Sequence[float]) -> Path:
            path = super().look_at(point_world_m)
            self._note("look_at")
            return path

        def body_command(self, command: Any) -> Path:
            path = super().body_command(command)
            self._note("body_command")
            return path

    return RecordingPublisher(runtime, expires_after_s)


def default_factory(engine: Path, device: str = DEVICE) -> tuple[Any, Callable[[Any], list[list[float]]], dict[str, Any]]:
    """板上：`fastlayer_bench.make_plugin`（与 S1/S2 同一构造注入）+ 同一模型上的检测函数（与 frozen-V 同口径行）。"""
    from tools.eng_jet import fastlayer_bench  # noqa: PLC0415

    sink: dict[str, Any] = {}
    plugin = fastlayer_bench.make_plugin(Path(engine), device, sink)
    spec = common.read_json(fastlayer_bench.SPEC_PATH)

    def detect(image: Any) -> list[list[float]]:
        return fastlayer_bench.detection_rows(sink["model"]._model, image, int(spec["imgsz"]), float(spec["conf"]),
                                              float(spec["nms_iou"]), device)

    sink["runtime_stack"] = fastlayer_bench.runtime_stack()
    return plugin, detect, sink


def _pop_timers(sink: Mapping[str, Any]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    model = sink.get("model")
    out["t_detect_ms"] = round(model.predict.pop(), 4) if model is not None and hasattr(model.predict, "pop") else None
    for key in ("gmc", "assoc"):
        timer = sink.get(key)
        out[f"t_{key}_ms"] = round(timer.pop(), 4) if timer is not None and hasattr(timer, "pop") else None
    return out


class TrackResponder:
    def __init__(self, runtime: Path, log_dir: Path, engine: Path, engine_sha256: str, *,
                 factory: Callable[[Path], tuple[Any, Callable[[Any], list[list[float]]], dict[str, Any]]] | None = None,
                 spec_path: Path | None = None, image_loader: Callable[[Path], Any] | None = None, poll_s: float = POLL_S):
        from tools.eng_jet import relay  # noqa: PLC0415

        self.runtime = Path(runtime).expanduser()
        common.refuse_protected(self.runtime)
        (self.runtime / "frames").mkdir(parents=True, exist_ok=True)
        self.log_dir = Path(log_dir).expanduser()
        self.receipts = relay.Receipts(self.log_dir / "track-receipts.jsonl")
        self.records = RecordSink(self.log_dir / "track-records.jsonl")
        self.engine, self.engine_sha256 = Path(engine).expanduser(), engine_sha256
        self.factory = factory or default_factory
        self.spec_path = spec_path or (common.PROJECT_ROOT / "config" / "det-assoc-v1.models.json")
        self.image_loader = image_loader
        self.poll_s = poll_s
        self.writes: list[dict[str, Any]] = []
        self._terminal_seen: int | None = None
        self.counters = {"process_calls": 0, "frames_processed": 0, "observations": 0, "look_at": 0, "post_terminal_frames": 0,
                         "exceptions": 0}

    def _latest(self, repository: Any) -> int | None:
        try:
            return repository.latest_frame_id()
        except (OSError, ValueError, KeyError):
            return None

    def _capture_unix(self, frame_id: int) -> float | None:
        try:
            metadata = json.loads((self.runtime / "frames" / common.frame_name(frame_id, "json")).read_text(encoding="utf-8"))
            return float(metadata["capture_unix_s"])
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _drain_writes(self) -> list[dict[str, Any]]:
        out, self.writes[:] = list(self.writes), []
        for row in out:
            if row["kind"] == "observation":
                self.counters["observations"] += 1
            elif row["kind"] == "look_at":
                self.counters["look_at"] += 1
            self.receipts.write("bridge_write", **row)
        return out

    def run(self, duration_s: float) -> dict[str, Any]:
        from controller.track_loop import FrameRepository, TrackLoop  # noqa: PLC0415

        deadline = time.monotonic() + duration_s
        self.receipts.write("start", runtime=str(self.runtime), engine=str(self.engine), engine_sha256_expected=self.engine_sha256,
                            pid=os.getpid(), env={k: os.environ.get(k) for k in ("MPLCONFIGDIR", "YOLO_CONFIG_DIR", "CUDA_CACHE_PATH",
                                                                                 "YOLO_AUTOINSTALL", "YOLO_OFFLINE", "LD_LIBRARY_PATH")})
        try:
            actual = common.sha256_file(self.engine) if self.engine.is_file() else None
            if actual != self.engine_sha256:
                self.receipts.write("engine_identity_mismatch", expected=self.engine_sha256, actual=actual)
                return self._finish("ENGINE_IDENTITY_MISMATCH")
            self.receipts.write("engine_identity_ok", sha256=actual, bytes=self.engine.stat().st_size)
            load_started = time.monotonic()
            plugin, detect, sink = self.factory(self.engine)
            self.receipts.write("ready", model_load_s=round(time.monotonic() - load_started, 3),
                                manifest_identity=dict(plugin.manifest_identity()) if hasattr(plugin, "manifest_identity") else None,
                                runtime_stack=sink.get("runtime_stack"))
            repository = FrameRepository(self.runtime, image_loader=self.image_loader) if self.image_loader else FrameRepository(self.runtime)
            first = None
            while time.monotonic() < deadline and first is None:
                first = self._latest(repository)
                if first is None:
                    time.sleep(self.poll_s)
            if first is None:
                return self._finish("NO_FRAME")
            seen_unix, seen_mono = time.time(), time.monotonic()
            bundle = repository.load(first)
            rows = detect(bundle.image)
            detect_ms = (time.monotonic() - seen_mono) * 1000.0
            spec = common.read_json(self.spec_path)
            pick = select_init_box(rows, target_class_id(spec))
            self.receipts.write("init_detection", frame_id=first, rows=rows, pick=pick, t_detect_ms=round(detect_ms, 3),
                                init_source="检测器自身 target 类最高分框（板上首帧；非真值、非离线用户框替身）")
            _pop_timers(sink)
            if pick is None:
                self.receipts.write("init_no_target_detection", frame_id=first)
                self._idle_until(deadline, repository, None)
                return self._finish("INIT_NO_TARGET_DETECTION")
            publisher = recording_publisher(self.runtime, EXPIRES_AFTER_S, self.writes)
            loop = TrackLoop(repository, plugin, publisher, self.records, track_id=TRACK_ID, condition=CONDITION,
                             ground_plane_y_m=GROUND_PLANE_Y_M, maximum_ground_range_m=MAXIMUM_GROUND_RANGE_M,
                             planned_duration_s=max(1.0, duration_s))
            init_started = time.monotonic()
            loop.initialize(first, pick["box_norm"])
            init_done_unix, init_done_mono = time.time(), time.monotonic()
            writes = self._drain_writes()
            self.receipts.write("init", frame_id=first, box_norm=pick["box_norm"], t_init_ms=round((init_done_mono - init_started) * 1000.0, 3),
                                seen_unix=round(seen_unix, 6), seen_mono=round(seen_mono, 6), done_unix=round(init_done_unix, 6),
                                done_mono=round(init_done_mono, 6), capture_unix_s=self._capture_unix(first),
                                writes=[w["kind"] for w in writes], timers=_pop_timers(sink), loop_state=loop.state)
            self._drive(loop, repository, sink, deadline)
            return self._finish("TERMINAL" if loop.terminal else "COMPLETED", loop)
        except Exception as error:  # noqa: BLE001 — 如实记录后退出（停该路径，不变通）
            self.counters["exceptions"] += 1
            self.receipts.write("exception", type=type(error).__name__, message=str(error)[:2000])
            return self._finish("EXCEPTION")

    def _drive(self, loop: Any, repository: Any, sink: Mapping[str, Any], deadline: float) -> None:
        while time.monotonic() < deadline:
            latest = self._latest(repository)
            if latest is None or loop.terminal or latest == loop.last_frame_id:
                self._note_post_terminal(loop, latest)
                time.sleep(self.poll_s)
                continue
            seen_unix, seen_mono = time.time(), time.monotonic()
            capture_unix = self._capture_unix(latest)
            previous = loop.last_frame_id
            try:
                processed = loop.process_available(latest)
            except Exception as error:  # noqa: BLE001
                self.counters["exceptions"] += 1
                self.receipts.write("exception", type=type(error).__name__, message=str(error)[:2000], latest=latest)
                self._idle_until(deadline, repository, latest)
                return
            done_unix, done_mono = time.time(), time.monotonic()
            writes = self._drain_writes()
            observation = next((w for w in writes if w["kind"] == "observation" and w.get("frame_id") == latest), None)
            self.counters["process_calls"] += 1
            self.counters["frames_processed"] += int(processed)
            self.receipts.write("process", latest=latest, previous=previous, processed=int(processed),
                                seen_unix=round(seen_unix, 6), seen_mono=round(seen_mono, 6), done_unix=round(done_unix, 6),
                                done_mono=round(done_mono, 6), capture_unix_s=capture_unix,
                                capture_age_s=None if capture_unix is None else round(seen_unix - capture_unix, 6),
                                published_latest=observation is not None,
                                load_elapsed_s=None if observation is None else round(observation["written_mono"] - seen_mono, 6),
                                processing_elapsed_s=round(done_mono - seen_mono, 6), writes=[w["kind"] for w in writes],
                                loop_state=loop.state, terminal=loop.terminal, timers=_pop_timers(sink))
            if loop.terminal:
                last = self.records.last or {}
                self.receipts.write("terminal", latest=latest, previous=previous, loop_event=last.get("event"), reason=last.get("reason"),
                                    record_frame_id=last.get("frame_id"),
                                    semantics="TrackLoop 终止后本应答器不重播种、不重启，进程继续存活并只记录到达的新帧")
                self._terminal_seen = latest

    def _note_post_terminal(self, loop: Any, latest: int | None) -> None:
        if not loop.terminal or latest is None:
            return
        if self._terminal_seen is None or latest > self._terminal_seen:
            self._terminal_seen = latest
            self.counters["post_terminal_frames"] += 1
            self.receipts.write("post_terminal_frame", latest=latest)

    def _idle_until(self, deadline: float, repository: Any, last: int | None) -> None:
        while time.monotonic() < deadline:
            latest = self._latest(repository)
            if latest is not None and (last is None or latest > last):
                last = latest
                self.counters["post_terminal_frames"] += 1
                self.receipts.write("post_terminal_frame", latest=latest)
            time.sleep(max(self.poll_s, 0.01))

    def _finish(self, outcome: str, loop: Any | None = None) -> dict[str, Any]:
        result = {"outcome": outcome, **self.counters, "records": self.records.count,
                  "loop_state": None if loop is None else loop.state, "terminal": None if loop is None else loop.terminal}
        self.receipts.write("stop", **result)
        self.records.close()
        self.receipts.close()
        return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--engine-sha256", required=True)
    parser.add_argument("--duration-s", type=float, required=True)
    args = parser.parse_args(argv)
    result = TrackResponder(args.runtime, args.log_dir, args.engine, args.engine_sha256).run(args.duration_s)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["outcome"] in ("COMPLETED", "TERMINAL") else 2


if __name__ == "__main__":
    sys.exit(main())
