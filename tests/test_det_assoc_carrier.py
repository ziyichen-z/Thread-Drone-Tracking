#!/usr/bin/env python3
"""P1-ENG-FAST-002 AC-6（§3.6、AR2-2 释义）：`TrackLoop --tracker det-assoc-v1` 离线载体自测（口径 C）。

在临时 runtime 目录用归档帧（scout-1 一条子序列，帧与初始化框取自口径 B 同一次运行记录
`docs/evidence/P1-ENG-FAST-002-replay.json#carrier_reference`）驱动真实 `TrackLoop` + 真实插件：
- 初始化帧单独验证：发布用户框的 `placeholder` 观测、插件 `init` 为 True、关联器只调用一次（库 `frame_id=1`）；
- 从第一个 `update` 帧到子序列末帧，载体逐帧 `(state, box, reason)` 与口径 B 插件输出完全相同；
- 观测桥 schema 与字段集与既有插件路径相同、`confidence_source` 只在闭集内；
- `init=False` 走载体既有初始化失败路径；零写入临时目录之外（仓库 `runtime/` 与本项产物目录不变）。
真值只在口径 B 的评分中出现，不进载体输入。需要 `.venv-yoloe`、冻结规格/权重与数据根帧，缺任一则跳过。
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SPEC = PROJECT_ROOT / "config" / "det-assoc-v1.models.json"
REPLAY = PROJECT_ROOT / "docs" / "evidence" / "P1-ENG-FAST-002-replay.json"
DATA_ROOT = Path(os.environ.get("ENG_DET_DATA_ROOT", str(Path.home() / "TetheredDroneTracking-full")))
HAVE_LIBS = all(importlib.util.find_spec(m) is not None for m in ("ultralytics", "lap", "cv2"))


def _reference():
    if not REPLAY.exists():
        return None
    return json.loads(REPLAY.read_text(encoding="utf-8")).get("carrier_reference")


def _ready() -> bool:
    reference = _reference()
    if not (HAVE_LIBS and SPEC.exists() and reference):
        return False
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    weights = PROJECT_ROOT / spec["weights"]["path"]
    return weights.exists() and all((DATA_ROOT / f).exists() for f in reference["frames"][:2])


def metadata(frame_id: int) -> dict:
    return {
        "schema_version": "tethered-sensor-frame/v3",
        "scenario_id": "fast-002-carrier",
        "frame_id": frame_id,
        "simulation_time_s": frame_id * 0.2,
        "capture_unix_s": 1_800_000_000.0 + frame_id * 0.2,
        "capture_monotonic_s": 500.0 + frame_id * 0.2,
        "capture_monotonic_clock_id": "system-stopwatch/v1",
        "camera_position_world_m": [0.0, 30.0, 0.0],
        "camera_forward_world": [0.0, -1.0, 0.0],
        "camera_right_world": [1.0, 0.0, 0.0],
        "camera_up_world": [0.0, 0.0, 1.0],
        "width": 640,
        "height": 480,
        "intrinsics_px": {"fx": 500.0, "fy": 500.0, "cx": 320.0, "cy": 240.0},
    }


def stage(runtime: Path, sources: list[str]) -> None:
    frames = runtime / "frames"
    frames.mkdir(parents=True)
    for index, source in enumerate(sources):
        stem = f"frame_{index:010d}"
        (frames / f"{stem}.jpg").symlink_to(DATA_ROOT / source)
        (frames / f"{stem}.json").write_text(json.dumps(metadata(index)), encoding="utf-8")


def make_loop(runtime: Path, tracker, run_id: str):
    from controller.run_log import RunLogger  # noqa: PLC0415
    from controller.track_loop import FrameRepository, RuntimePublisher, TrackLoop  # noqa: PLC0415

    logger = RunLogger(runtime, run_id, {"condition": "follow"})
    loop = TrackLoop(
        FrameRepository(runtime),
        tracker,
        RuntimePublisher(runtime, 1.0),
        logger,
        track_id="target-0",
        condition="follow",
        ground_plane_y_m=0.0,
        maximum_ground_range_m=1000.0,
        planned_duration_s=10_000.0,
    )
    return loop, logger


def tree_snapshot(root: Path) -> dict[str, tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


def key_tree(value):
    if isinstance(value, dict):
        return {k: key_tree(v) for k, v in sorted(value.items())}
    return type(value).__name__ if value is not None else "null"


@unittest.skipUnless(_ready(), "需要 .venv-yoloe、冻结规格/权重、口径 B 记录与数据根帧")
class CarrierSelfTest(unittest.TestCase):
    def test_carrier_matches_caliber_b_from_first_update(self):
        from controller.det_assoc_tracker import DetAssocTracker  # noqa: PLC0415
        from controller.run_log import read_frame_records  # noqa: PLC0415
        from controller.trackers import clip_box_norm  # noqa: PLC0415

        reference = _reference()
        guarded = [PROJECT_ROOT / "runtime", PROJECT_ROOT / "outputs" / "eng-det", PROJECT_ROOT / "docs" / "evidence"]
        before = {str(root): tree_snapshot(root) for root in guarded}
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            stage(runtime, reference["frames"])
            tracker = DetAssocTracker(spec_path=SPEC, device="cpu")
            self.assertEqual(tracker.manifest_identity()["weights_sha256"], reference["plugin_manifest"]["weights_sha256"])
            loop, logger = make_loop(runtime, tracker, "carrier")
            try:
                loop.initialize(0, reference["init_box"])
                self.assertEqual(tracker.library_frame_id, 1)
                self.assertEqual(reference["library_frame_id_after_init"], 1)
                for frame_id in range(1, len(reference["frames"])):
                    loop.process_available(frame_id)
                self.assertEqual(tracker.library_frame_id, len(reference["frames"]))
                observation = json.loads((runtime / "tracking_observation.json").read_text(encoding="utf-8"))
            finally:
                logger.close()
            records, _ = read_frame_records(logger.frames_path)
        init = records[0]
        self.assertEqual((init["event"], init["state"], init["confidence_source"]), ("INIT", "TRACKING", "placeholder"))
        self.assertEqual(init["box_norm"], list(clip_box_norm(reference["init_box"])))
        carrier = [(r["state"], r["box_norm"], r["reason"]) for r in records[1:]]
        plugin = [(f["state"], f["box"], f["reason"]) for f in reference["per_frame"]]
        self.assertEqual(len(carrier), len(plugin))
        mismatches = [i for i, (a, b) in enumerate(zip(carrier, plugin)) if a != b]
        self.assertEqual(mismatches, [], f"首个不一致：{carrier[mismatches[0]] if mismatches else None} vs {plugin[mismatches[0]] if mismatches else None}")
        self.assertTrue({r["confidence_source"] for r in records} <= {"tracker", "placeholder", "none"})
        self.assertTrue(all(r["confidence_source"] == "tracker" for r in records[1:] if r["ok"]))
        self.assertEqual(observation["protocol"], "tethered-tracking-observation/v1")
        self.assertEqual(key_tree(observation), key_tree(self._baseline_observation()))
        after = {str(root): tree_snapshot(root) for root in guarded}
        self.assertEqual(before, after, "载体自测写到了临时目录之外")

    def _baseline_observation(self):
        """既有插件路径（脚本化 TrackerResult）在同一 TrackLoop 下产出的观测：字段集基线。"""
        from controller.trackers import ScriptedTracker, TrackerResult  # noqa: PLC0415

        reference = _reference()
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            stage(runtime, reference["frames"][:2])
            tracker = ScriptedTracker([TrackerResult((0.4, 0.4, 0.1, 0.1), True, 0.9, "tracker")])
            loop, logger = make_loop(runtime, tracker, "baseline")
            try:
                loop.initialize(0, reference["init_box"])
                loop.process_available(1)
                return json.loads((runtime / "tracking_observation.json").read_text(encoding="utf-8"))
            finally:
                logger.close()

    def test_init_false_uses_existing_failure_path(self):
        from controller.det_assoc_tracker import DetAssocTracker  # noqa: PLC0415

        reference = _reference()
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            stage(runtime, reference["frames"][:2])
            tracker = DetAssocTracker(spec_path=SPEC, device="cpu")
            loop, logger = make_loop(runtime, tracker, "init-false")
            try:
                with self.assertRaisesRegex(RuntimeError, "tracker rejected the exact initialization frame/box"):
                    loop.initialize(0, (0.0, 0.0, 0.01, 0.01))  # 左上角无检测 → 插件 init=False
                self.assertIsNone(loop.last_frame_id)
                self.assertFalse((runtime / "tracking_observation.json").exists())
            finally:
                logger.close()




# --- P1-ENG-ACQ-001 AC-6（AR1-3）：常驻载体 -------------------------------------------------

ACQ_FRAMES = 60


def _write_fixture_frame(runtime: Path, frame_id: int) -> None:
    frames = runtime / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    stem = f"frame_{frame_id:010d}"
    (frames / f"{stem}.jpg").write_bytes(b"jpeg-%d" % frame_id)
    (frames / f"{stem}.json").write_text(json.dumps(metadata(frame_id)), encoding="utf-8")


class SpyResident:
    """常驻替身：记录调用序列；`init`/`update` 一调即记为违规。"""

    name = "spy-resident"
    backend = "test"
    version = "1"
    mode = "resident"

    def __init__(self):
        self.calls: list[tuple[str, int | None]] = []

    def step(self, image, frame_id, metadata):
        self.calls.append(("step", frame_id))

    def pointer_result(self, frame_id):
        from controller.trackers import TrackerResult  # noqa: PLC0415

        self.calls.append(("pointer_result", frame_id))
        return TrackerResult((0.4, 0.4, 0.1, 0.1), True, 0.8, "tracker") if frame_id % 2 else TrackerResult.lost("no_pointer")

    def init(self, image, box):
        self.calls.append(("init", None))
        return True

    def update(self, image):
        self.calls.append(("update", None))

    def manifest_identity(self):
        return {"name": self.name}


class SpyLegacy:
    name = "spy-legacy"
    backend = "test"
    version = "1"

    def __init__(self):
        self.calls: list[tuple[str, int | None]] = []

    def init(self, image, box):
        self.calls.append(("init", None))
        return True

    def update(self, image):
        from controller.trackers import TrackerResult  # noqa: PLC0415

        self.calls.append(("update", None))
        return TrackerResult((0.4, 0.4, 0.1, 0.1), True, 0.8, "tracker")

    def manifest_identity(self):
        return {"name": self.name}


def _image_loader(path: Path):
    class Image:
        shape = (480, 640, 3)

    return Image()


def _loop(runtime: Path, tracker, run_id: str):
    from controller.run_log import RunLogger  # noqa: PLC0415
    from controller.track_loop import FrameRepository, RuntimePublisher, TrackLoop  # noqa: PLC0415

    logger = RunLogger(runtime, run_id, {"condition": "follow"})
    loop = TrackLoop(
        FrameRepository(runtime, _image_loader),
        tracker,
        RuntimePublisher(runtime, 1.0),
        logger,
        track_id="s1-t1",
        condition="follow",
        ground_plane_y_m=0.0,
        maximum_ground_range_m=1000.0,
        planned_duration_s=10_000.0,
    )
    return loop, logger


class ResidentCarrierCalls(unittest.TestCase):
    def test_resident_carrier_calls_step_once_per_frame_never_update(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for frame_id in range(7):
                _write_fixture_frame(runtime, frame_id)
            spy = SpyResident()
            loop, logger = _loop(runtime, spy, "resident")
            try:
                loop.start(0)
                loop.process_available(3)
                loop.process_available(6)
                loop.process_available(6)
                observation = json.loads((runtime / "tracking_observation.json").read_text(encoding="utf-8"))
            finally:
                logger.close()
        expected = [call for frame_id in range(7) for call in (("step", frame_id), ("pointer_result", frame_id))]
        self.assertEqual(spy.calls, expected)
        self.assertEqual(observation["protocol"], "tethered-tracking-observation/v1")
        self.assertIn('"s1-t1"', json.dumps(observation))  # 只含指针 track（载体唯一的对外 track_id）

    def test_legacy_carrier_call_sequence_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for frame_id in range(5):
                _write_fixture_frame(runtime, frame_id)
            spy = SpyLegacy()
            loop, logger = _loop(runtime, spy, "legacy")
            try:
                self.assertFalse(loop.resident)
                loop.initialize(0, (0.4, 0.4, 0.1, 0.1))
                loop.process_available(2)
                loop.process_available(4)
            finally:
                logger.close()
        self.assertEqual(spy.calls, [("init", None)] + [("update", None)] * 4)

    def test_compat_det_assoc_is_not_resident(self):
        from controller.track_loop import is_resident_tracker  # noqa: PLC0415

        class Compat:
            mode = "compat"

            def step(self, *args):  # pragma: no cover
                raise AssertionError

        self.assertFalse(is_resident_tracker(Compat()))
        self.assertTrue(is_resident_tracker(SpyResident()))
        self.assertFalse(is_resident_tracker(SpyLegacy()))


def _acq_ready() -> bool:
    return HAVE_LIBS and SPEC.exists() and (DATA_ROOT / "runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames").exists()


@unittest.skipUnless(_acq_ready(), "需要数据根 .venv-yoloe（ultralytics+lap）、冻结规格与数据根 scout-1 帧")
class ResidentCarrierReplay(unittest.TestCase):
    """AC-6：常驻 `TrackLoop` + `resident` 插件（缓存检测替身，零推理）在 scout-1 子序列上逐帧 `(state, box, reason)`
    与线束回放（同一 `ResidentCore`）完全一致。每次运行记 2 次部分序列回放（本项消耗账本）。"""

    def test_resident_carrier_matches_replay(self):
        import torch  # noqa: PLC0415
        from ultralytics.engine.results import Boxes  # noqa: PLC0415

        from controller import det_assoc_tracker as dat  # noqa: PLC0415
        from controller.resident_core import ResidentCore  # noqa: PLC0415
        from controller.track_loop import _publication_ready_result  # noqa: PLC0415
        from controller.run_log import read_frame_records  # noqa: PLC0415
        from tools.eng_acq import data, e2  # noqa: PLC0415

        frames = data.load_sequences(["scout-1"])["scout-1"][0][:ACQ_FRAMES]
        # 线束路径：同一 `rows_from_library` + `ResidentCore`。
        records = e2.replay_segment(frames, "pose", 30, None)
        k_index = next(i for i in range(5, 40) if frames[i].red is not None and any(
            t["state"] == "tracked" and self._iou(t["box_norm"], frames[i].red) >= 0.5 for t in records[i]["tracks"]))
        designate_at = k_index + 8
        box = list(frames[k_index].red)
        core = ResidentCore(128)
        harness = []
        for index, (frame, record) in enumerate(zip(frames, records)):
            core.record(frame.frame_id, frame.metadata, e2.rows_of(record, "tracked"), e2.rows_of(record, "lost"), record["removed_ids"], record["library_frame_id"])
            result = _publication_ready_result(core.pointer_result(frame.frame_id))
            harness.append(("TRACKING" if result.ok else "LOST", list(result.box_norm) if result.box_norm else None, result.reason))
            if index == designate_at:  # 与载体同时序：该帧处理完后指定，指针自下一帧生效
                harness_designation = core.designate(box, frames[k_index].frame_id, None)

        class CachedModel:
            def __init__(self):
                self.calls = 0

            def predict(self, source, **kwargs):
                dets = frames[self.calls].dets
                self.calls += 1
                rows = [[d[0] * 640, d[1] * 480, (d[0] + d[2]) * 640, (d[1] + d[3]) * 480, d[4], d[5]] for d in dets]
                tensor = torch.tensor(rows, dtype=torch.float32) if rows else torch.zeros((0, 6), dtype=torch.float32)

                class Result:
                    boxes = Boxes(tensor, orig_shape=(480, 640))

                return [Result()]

        model = CachedModel()
        plugin = dat.DetAssocTracker(spec_path=SPEC, device="cpu", model_loader=lambda path: model, mode="resident")
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "frames").mkdir()
            for frame in frames:
                stem = f"frame_{frame.frame_id:010d}"
                (runtime / "frames" / f"{stem}.jpg").symlink_to(DATA_ROOT / frame.path)
                meta = dict(frame.metadata)
                meta.update({"schema_version": "tethered-sensor-frame/v3", "capture_monotonic_s": 1000.0 + meta["simulation_time_s"], "capture_monotonic_clock_id": "system-stopwatch/v1"})
                (runtime / "frames" / f"{stem}.json").write_text(json.dumps(meta), encoding="utf-8")
            loop, logger = make_loop(runtime, plugin, "resident-carrier")
            try:
                loop.start(frames[0].frame_id)
                for index in range(1, len(frames)):
                    loop.process_available(frames[index].frame_id)
                    if index == designate_at:
                        carrier_designation = plugin.designate(box, frames[k_index].frame_id)
            finally:
                logger.close()
            carrier_records, _ = read_frame_records(logger.frames_path)
        carrier = [(r["state"], r["box_norm"], r["reason"]) for r in carrier_records]
        self.assertEqual((carrier_designation.result, carrier_designation.track_id), (harness_designation.result, harness_designation.track_id))
        self.assertEqual(carrier_designation.result, "BOUND")
        self.assertEqual(len(carrier), len(harness))
        mismatches = [i for i, (a, b) in enumerate(zip(carrier, harness)) if a != b]
        self.assertEqual(mismatches, [], f"首个不一致：{carrier[mismatches[0]] if mismatches else None} vs {harness[mismatches[0]] if mismatches else None}")
        self.assertTrue(any(state == "TRACKING" for state, _b, _r in carrier))
        self.assertEqual((model.calls, plugin.detect_calls), (len(frames), len(frames)))
        self.assertEqual(plugin.manifest_identity()["mode"], "resident")

    @staticmethod
    def _iou(a, b):
        from controller.resident_core import box_iou  # noqa: PLC0415

        return box_iou(a, b)


if __name__ == "__main__":
    unittest.main()
