#!/usr/bin/env python3
"""P1-ENG-FAST-002 AC-5 / AC-8：`det-assoc-v1` 插件的具名反例与真值隔离。

- 规格/冻结文件校验、设备回退、工厂与 CLI 注册、真值隔离：不需要 ultralytics（注入假检测器与假关联器）。
- 绑定/丢失/不改绑与库 `frame_id` 语义：用**钉版库真实关联器**（ByteTrack/BoT-SORT）+ 脚本化检测，
  需要 `.venv-yoloe`（ultralytics 8.4.104 + lap），缺依赖时跳过并在证据日志中如实记录。
"""

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import det_assoc_tracker as dat  # noqa: E402
from controller.trackers import ScriptedTracker, TrackerResult, create_tracker, sha256_file  # noqa: E402

HAVE_LIBS = importlib.util.find_spec("ultralytics") is not None and importlib.util.find_spec("lap") is not None
W, H = 640, 480


class _Frame:
    """无 numpy 时的图像替身：插件只读 `shape` 并原样转交检测器/关联器。"""

    shape = (H, W, 3)


def _image():
    if not HAVE_LIBS:
        return _Frame()
    import numpy as np  # noqa: PLC0415

    return np.zeros((H, W, 3), dtype=np.uint8)


class _Rows(list):
    def tolist(self):
        return [list(row) for row in self]


class _Boxes:
    """无 ultralytics 时的最小 Boxes 替身（只供假关联器读取）。"""

    def __init__(self, rows):
        self.rows = rows

    def cpu(self):
        return self

    def numpy(self):
        return self


class _Result:
    def __init__(self, boxes):
        self.boxes = boxes


class ScriptedModel:
    """按调用顺序返回检测（像素 xyxy + score + cls）；`boxes_factory` 决定 Boxes 形态。"""

    def __init__(self, script, boxes_factory):
        self.script = list(script)
        self.boxes_factory = boxes_factory
        self.calls = 0
        self.kwargs = []

    def predict(self, source, **kwargs):
        self.kwargs.append(kwargs)
        rows = self.script[self.calls] if self.calls < len(self.script) else []
        self.calls += 1
        return [_Result(self.boxes_factory(rows))]


def library_boxes(rows):
    import torch  # noqa: PLC0415
    from ultralytics.engine.results import Boxes  # noqa: PLC0415

    tensor = torch.tensor(rows, dtype=torch.float32) if rows else torch.zeros((0, 6), dtype=torch.float32)
    return Boxes(tensor, orig_shape=(H, W))


class FakeAssociator:
    """无库时的假关联器：每个检测一个 track，id = 行号 + 1。"""

    def __init__(self):
        self.frame_id = 0
        self.lost_stracks = []

    def update(self, boxes, image):
        self.frame_id += 1
        return _Rows([[*row[:4], i + 1, row[4], row[5], i] for i, row in enumerate(boxes.rows)])


def library_args(algorithm="bytetrack", **overrides):
    from ultralytics.utils import YAML  # noqa: PLC0415
    from ultralytics.utils.checks import check_yaml  # noqa: PLC0415

    args = dict(YAML.load(check_yaml(f"{algorithm}.yaml")))
    args.update(overrides)
    return args


def default_args(algorithm="bytetrack", **overrides):
    args = {
        "tracker_type": algorithm,
        "track_high_thresh": 0.25,
        "track_low_thresh": 0.1,
        "new_track_thresh": 0.25,
        "track_buffer": 30,
        "match_thresh": 0.8,
        "fuse_score": True,
    }
    args.update(overrides)
    return args


class SpecFixture:
    """临时权重/冻结文件 + 与之匹配的规格文件（生产格式同 `config/det-assoc-v1.models.json`）。"""

    def __init__(self, tmp: Path, args=None, preferred="mps"):
        self.weights = tmp / "last.pt"
        self.weights.write_bytes(b"fake-weights-for-spec-tests")
        self.freeze = tmp / "freeze.json"
        self.freeze.write_text('{"frozen": true}\n', encoding="utf-8")
        self.spec = {
            "schema_version": "tethered-tracker-models/v1",
            "tracker": "det-assoc-v1",
            "ultralytics_version": "8.4.104",
            "weights": {"path": str(self.weights), "sha256": sha256_file(self.weights), "size_bytes": self.weights.stat().st_size},
            "freeze": {"path": str(self.freeze), "sha256": sha256_file(self.freeze)},
            "imgsz": 640,
            "conf": 0.25,
            "nms_iou": 0.7,
            "classes": {"0": "vehicle", "1": "target"},
            "device_policy": {"preferred": preferred, "fallback": "cpu"},
            "association": {"algorithm": (args or default_args())["tracker_type"], "args": args or default_args()},
        }
        self.path = tmp / "det-assoc-v1.models.json"
        self.write()

    def write(self):
        self.path.write_text(json.dumps(self.spec), encoding="utf-8")


def make(fixture, script, *, library=False, device="cpu"):
    factory = library_boxes if library else _Boxes
    model = ScriptedModel(script, factory)
    kwargs = {}
    if not library:
        kwargs["tracker_factory"] = lambda algorithm, args: FakeAssociator()
    tracker = dat.DetAssocTracker(
        spec_path=fixture.path, device=device, model_loader=lambda path: model, check_library_version=False, **kwargs
    )
    return tracker, model


BOX = [256.0, 192.0, 320.0, 240.0]  # 像素 xyxy
INIT_NORM = (256 / W, 192 / H, 64 / W, 48 / H)


class SpecAndFactoryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fixture = SpecFixture(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_weights_sha_tamper_rejected(self):
        self.fixture.weights.write_bytes(b"XXXX-weights-for-spec-tests")  # 同长度不同内容 → sha 不符
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            make(self.fixture, [])

    def test_freeze_sha_mismatch_rejected(self):
        self.fixture.freeze.write_text('{"frozen": false}\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "freeze file SHA-256 mismatch"):
            make(self.fixture, [])

    def test_missing_or_wrong_fields_fail_closed(self):
        for mutate in (
            lambda s: s.pop("conf"),
            lambda s: s.update(tracker="nanotrack-v2"),
            lambda s: s.update(ultralytics_version="8.4.0"),
            lambda s: s["association"].update(algorithm="deepsort"),
            lambda s: s["association"]["args"].pop("track_buffer"),
            lambda s: s.update(classes={"0": "car"}),
        ):
            with self.subTest(mutate=mutate):
                fixture = SpecFixture(Path(self._tmp.name))
                mutate(fixture.spec)
                fixture.write()
                with self.assertRaises(ValueError):
                    make(fixture, [])

    def test_device_fallback_recorded_in_manifest(self):
        fake_torch = mock.MagicMock()
        fake_torch.backends.mps.is_available.return_value = False
        with mock.patch.dict(sys.modules, {"torch": fake_torch}):
            model = ScriptedModel([], _Boxes)
            tracker = dat.DetAssocTracker(
                spec_path=self.fixture.path,
                model_loader=lambda path: model,
                tracker_factory=lambda a, b: FakeAssociator(),
                check_library_version=False,
            )
        manifest = tracker.manifest_identity()
        self.assertEqual((manifest["device"], manifest["device_fallback"]), ("cpu", "mps_unavailable"))
        self.assertEqual((manifest["score_threshold"], manifest["threshold_source"]), (0.25, "spec"))
        self.assertEqual(manifest["weights_sha256"], sha256_file(self.fixture.weights))
        self.assertEqual(manifest["freeze_sha256"], sha256_file(self.fixture.freeze))

    def test_factory_registers_det_assoc_and_cli_default_unchanged(self):
        with mock.patch.object(dat, "_default_model_loader", lambda path: ScriptedModel([], _Boxes)), mock.patch.object(
            dat, "_default_tracker_factory", lambda a, b: FakeAssociator()
        ), mock.patch.dict(sys.modules, {"ultralytics": mock.MagicMock(__version__="8.4.104")}):
            tracker = create_tracker("det-assoc-v1", det_assoc_spec_path=self.fixture.path)
        self.assertEqual((tracker.name, tracker.backend, tracker.version), ("det-assoc-v1", "ultralytics", "8.4.104"))
        from controller import track_loop  # noqa: PLC0415

        parser_source = Path(track_loop.__file__).read_text(encoding="utf-8")
        self.assertIn('choices=("csrt", "nanotrack-v2", "det-assoc-v1"),\n        default="csrt",', parser_source)

    def test_update_before_init_is_lost_not_initialized(self):
        tracker, _model = make(self.fixture, [])
        self.assertEqual(tracker.update(_image()), TrackerResult.lost("tracker_not_initialized"))

    def test_init_calls_detector_and_associator_exactly_once(self):
        tracker, model = make(self.fixture, [[BOX + [0.9, 1.0]]])
        self.assertTrue(tracker.init(_image(), INIT_NORM))
        self.assertEqual((model.calls, tracker.library_frame_id), (1, 1))
        self.assertEqual(model.kwargs[0]["conf"], 0.25)


class TruthIsolation(unittest.TestCase):
    """AC-8：插件模块导入闭集；运行时不读 S3/S4、不导入 tools.* 或评估器。"""

    ALLOWED_TOP = {"__future__", "json", "math", "pathlib", "typing", "ultralytics", "torch", "numpy"}
    # P1-ENG-ACQ-001：常驻模式新增的两个纯几何/历史模块（自身只导入标准库与 .trackers/.reanchor）。
    ALLOWED_RELATIVE = {".trackers", ".resident_core", ".pose_gmc"}

    def test_import_closure(self):
        tree = ast.parse(Path(dat.__file__).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(("." * node.level) + (node.module or ""))
        for name in imported:
            if name.startswith("."):
                self.assertIn(name, self.ALLOWED_RELATIVE, name)
                continue
            self.assertIn(name.split(".")[0], self.ALLOWED_TOP, name)
        for forbidden in ("tools", "dist_data", "eng_sft", "eng_fast", "eng_det", "coverage", "evaluator"):
            self.assertFalse(any(forbidden in name for name in imported), forbidden)

    def test_runtime_import_pulls_no_tools_modules(self):
        code = (
            "import sys; sys.path.insert(0, %r); import controller.det_assoc_tracker; "
            "print(sorted(m for m in sys.modules if m.startswith('tools') or 'eng_' in m or 'dist_data' in m))"
        ) % str(PROJECT_ROOT)
        output = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(output, "[]")

    def test_source_names_no_truth_fields_or_catalog_paths(self):
        source = Path(dat.__file__).read_text(encoding="utf-8")
        for token in ("target_visible", "geometrically_visible", "frames_catalog", "splits.json", "truth", "blocker"):
            self.assertNotIn(token, source.replace("真值隔离", ""), token)


@unittest.skipUnless(HAVE_LIBS, "需要 .venv-yoloe（ultralytics 8.4.104 + lap）")
class LibrarySemantics(unittest.TestCase):
    """钉版库真实关联器 + 脚本化检测：K3 绑定/丢失/不改绑语义。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def tracker(self, script, algorithm="bytetrack", **overrides):
        fixture = SpecFixture(Path(self._tmp.name), args=library_args(algorithm, **overrides))
        return make(fixture, script, library=True)

    def test_init_box_without_match_returns_false(self):
        far = [[10.0, 10.0, 60.0, 50.0, 0.9, 1.0]]
        tracker, _ = self.tracker([far])
        self.assertFalse(tracker.init(_image(), INIT_NORM))
        self.assertIsNone(tracker.bound_track_id)
        self.assertEqual(tracker.update(_image()).reason, "tracker_not_initialized")

    def test_init_tie_prefers_higher_score(self):
        low = BOX + [0.5, 0.0]
        high = BOX + [0.95, 1.0]
        tracker, _ = self.tracker([[low, high], [high]], match_thresh=0.99)
        self.assertTrue(tracker.init(_image(), INIT_NORM))
        rows = tracker._tracker.tracked_stracks  # noqa: SLF001 — 读库状态核对绑定对象
        bound = [t for t in rows if int(t.track_id) == tracker.bound_track_id]
        self.assertEqual(len(bound), 1)
        self.assertAlmostEqual(float(bound[0].score), 0.95, places=5)

    def test_init_then_frame_id_is_one(self):
        tracker, model = self.tracker([[BOX + [0.9, 1.0]]])
        self.assertTrue(tracker.init(_image(), INIT_NORM))
        self.assertEqual((tracker.library_frame_id, model.calls), (1, 1))

    def test_buffer_unmatched_then_recovers_same_id(self):
        det = [BOX + [0.9, 1.0]]
        tracker, _ = self.tracker([det, det, [], [], det], track_buffer=5)
        self.assertTrue(tracker.init(_image(), INIT_NORM))
        bound = tracker.bound_track_id
        results = [tracker.update(_image()) for _ in range(4)]
        self.assertTrue(results[0].ok)
        self.assertEqual([r.reason for r in results[1:3]], ["bound_track_unmatched"] * 2)
        self.assertTrue(results[3].ok)
        self.assertEqual(results[3].confidence_source, "tracker")
        self.assertEqual(tracker.bound_track_id, bound)
        self.assertEqual(tracker.library_frame_id, 5)

    def test_removed_after_buffer_reports_removed(self):
        det = [BOX + [0.9, 1.0]]
        tracker, _ = self.tracker([det, det] + [[]] * 8, track_buffer=3)
        self.assertTrue(tracker.init(_image(), INIT_NORM))
        reasons = [tracker.update(_image()).reason for _ in range(9)]
        self.assertEqual(reasons[0], None)
        self.assertEqual(reasons[1], "bound_track_unmatched")
        self.assertEqual(reasons[-1], "bound_track_removed")

    def test_new_id_at_same_position_is_not_rebound(self):
        det = [BOX + [0.9, 1.0]]
        tracker, _ = self.tracker([det, det] + [[]] * 8 + [det, det, det], track_buffer=3)
        self.assertTrue(tracker.init(_image(), INIT_NORM))
        bound = tracker.bound_track_id
        results = [tracker.update(_image()) for _ in range(12)]
        self.assertTrue(all(not r.ok and r.reason == "bound_track_removed" for r in results[-3:]))
        self.assertEqual(tracker.bound_track_id, bound)
        new_ids = {int(t.track_id) for t in tracker._tracker.tracked_stracks}  # noqa: SLF001
        self.assertTrue(new_ids and bound not in new_ids)

    def test_two_runs_identical_output(self):
        script = [[BOX + [0.9, 1.0]]] + [[[BOX[0] + 4 * i, BOX[1], BOX[2] + 4 * i, BOX[3], 0.8, 1.0]] if i % 4 else [] for i in range(1, 15)]
        outputs = []
        for algorithm in ("bytetrack", "botsort"):
            for _ in range(2):
                tracker, _ = self.tracker(script, algorithm=algorithm)
                self.assertTrue(tracker.init(_image(), INIT_NORM))
                outputs.append([tracker.update(_image()) for _ in range(len(script) - 1)])
            self.assertEqual(outputs[-1], outputs[-2], algorithm)


# --- P1-ENG-ACQ-001：常驻协议（AC-1/AC-2/AC-3/AC-4/AC-19）---------------------------


class _LostTrack:
    def __init__(self, track_id, xyxy, score=0.8, cls=0.0):
        self.track_id, self.xyxy, self.score, self.cls = track_id, list(xyxy), score, cls


class ScriptedAssociator:
    """按帧脚本给出 tracked 行、lost 池与移除 ID（只供常驻协议测试；不跑任何库）。"""

    def __init__(self, script):
        self.script = list(script)
        self.frame_id = 0
        self.lost_stracks = []
        self.removed_stracks = []
        self.warps = []

    def set_pose_warp(self, homography):
        self.warps.append(homography)

    def update(self, boxes, image):
        frame = self.script[self.frame_id] if self.frame_id < len(self.script) else {}
        self.frame_id += 1
        self.lost_stracks = [_LostTrack(i, xyxy) for i, xyxy in frame.get("lost", [])]
        self.removed_stracks.extend(_LostTrack(i, [0, 0, 1, 1]) for i in frame.get("removed", []))
        return _Rows([[*xyxy, i, 0.9, 0.0, n] for n, (i, xyxy) in enumerate(frame.get("tracked", []))])


def resident(fixture, frames, **options):
    model = ScriptedModel([[] for _ in range(len(frames) + 5)], _Boxes)
    associators = []

    def factory(algorithm, args):
        associators.append(ScriptedAssociator(frames))
        return associators[-1]

    tracker = dat.DetAssocTracker(
        spec_path=fixture.path,
        device="cpu",
        model_loader=lambda path: model,
        tracker_factory=factory,
        check_library_version=False,
        mode="resident",
        **options,
    )
    return tracker, model, associators


def step_meta(frame_id):
    return {
        "frame_id": frame_id,
        "simulation_time_s": frame_id * 0.2,
        "capture_monotonic_s": 10.0 + frame_id * 0.2,
        "camera_position_world_m": [0.0, 25.0, 0.0],
        "camera_rotation_xyzw": [0.7071068, 0.0, 0.0, 0.7071068],
        "intrinsics_px": {"fx": 415.69, "fy": 415.69, "cx": 320.0, "cy": 240.0},
    }


PX_A = [64.0, 48.0, 128.0, 96.0]
PX_B = [320.0, 240.0, 384.0, 288.0]
NORM_A = (64 / W, 48 / H, 64 / W, 48 / H)
NORM_B = (320 / W, 240 / H, 64 / W, 48 / H)


class ResidentProtocol(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fixture = SpecFixture(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_resident_step_without_pointer(self):
        """AC-1：无指针也逐帧恰一次检测 + 关联并写历史；`pointer_result` = no_pointer。"""
        frames = [{"tracked": [(1, PX_A)]} for _ in range(6)]
        tracker, model, associators = resident(self.fixture, frames)
        for offset in range(6):
            tracker.step(_image(), 1000 + 3 * offset, step_meta(1000 + 3 * offset))  # 非连续起点与步长
            self.assertEqual(tracker.pointer_result(1000 + 3 * offset), TrackerResult.lost("no_pointer"))
        self.assertEqual((model.calls, tracker.detect_calls, len(associators)), (6, 6, 1))
        self.assertEqual(len(tracker.core), 6)

    def test_mode_methods_are_exclusive(self):
        tracker, model, _ = resident(self.fixture, [{}])
        for call in (lambda: tracker.init(_image(), INIT_NORM), lambda: tracker.update(_image())):
            with self.assertRaises(dat.ProtocolMisuse):
                call()
        self.assertEqual(model.calls, 0)
        compat, compat_model = make(self.fixture, [])
        self.assertEqual(compat.update(_image()), TrackerResult.lost("tracker_not_initialized"))
        for call in (
            lambda: compat.step(_image(), 1, step_meta(1)),
            lambda: compat.pointer_result(1),
            lambda: compat.designate(NORM_A, 1),
            lambda: compat.follow(1),
            lambda: compat.pointer(),
        ):
            with self.assertRaises(dat.ProtocolMisuse):
                call()
        self.assertIsNone(compat.history(1))
        self.assertEqual(compat_model.calls, 0)
        self.assertTrue(issubclass(dat.ProtocolMisuse, RuntimeError))
        self.assertEqual(compat.manifest_identity()["mode"], "compat")

    def test_step_repeated_or_rolled_back_frame_raises(self):
        tracker, model, _ = resident(self.fixture, [{}, {}, {}])
        tracker.step(_image(), 5, step_meta(5))
        for bad in (5, 4):
            with self.assertRaises(dat.ProtocolMisuse):
                tracker.step(_image(), bad, step_meta(bad))
        self.assertEqual(model.calls, 1)

    def test_history_keyed_by_sensor_frame_id(self):
        tracker, _, _ = resident(self.fixture, [{"tracked": [(1, PX_A)]}] * 3)
        for offset in range(3):
            tracker.step(_image(), 1000 + offset, step_meta(1000 + offset))
        self.assertIsNotNone(tracker.history(1000))
        self.assertIsNone(tracker.history(1))
        self.assertEqual([tracker.history(1000 + i).library_frame_id for i in range(3)], [1, 2, 3])

    def test_history_depth_eviction(self):
        tracker, _, _ = resident(self.fixture, [{}] * 105, history_depth=100)
        for frame_id in range(105):
            tracker.step(_image(), frame_id, step_meta(frame_id))
        self.assertIsNone(tracker.history(4))
        self.assertIsNotNone(tracker.history(5))
        default, _, _ = resident(self.fixture, [{}])
        manifest = default.manifest_identity()
        self.assertEqual((manifest["mode"], manifest["history_depth"], manifest["gmc_source"]), ("resident", 128, "pose"))
        self.assertEqual(manifest["level2"]["tracker"], "nanotrack-v2")
        with self.assertRaises(ValueError):
            resident(self.fixture, [{}], history_depth=99)

    def test_gmc_source_selectable_and_pose_warp_passed(self):
        for source in ("pose", "optflow", "none"):
            tracker, _, associators = resident(self.fixture, [{}] * 3, gmc_source=source)
            for frame_id in range(3):
                tracker.step(_image(), frame_id, step_meta(frame_id))
            self.assertEqual(tracker.manifest_identity()["gmc_source"], source)
            self.assertEqual(len(associators[0].warps), 2 if source == "pose" else 0)
        with self.assertRaises(ValueError):
            resident(self.fixture, [{}], gmc_source="orb")

    def test_designate_bound_coasting_and_ended(self):
        frames = [
            {"tracked": [(1, PX_A), (2, PX_B)]},
            {"tracked": [(2, PX_B)], "lost": [(1, PX_A)]},
            {"tracked": [(2, PX_B)], "removed": [1]},
        ]
        tracker, _, _ = resident(self.fixture, frames)
        tracker.step(_image(), 10, step_meta(10))
        tracker.step(_image(), 11, step_meta(11))
        self.assertEqual(tracker.designate(NORM_B, 10).result, "BOUND")
        self.assertEqual(tracker.designate(NORM_A, 10).result, "BOUND_COASTING")
        tracker.step(_image(), 12, step_meta(12))
        self.assertEqual(tracker.designate(NORM_A, 10).result, "TRACK_ENDED")

    def test_designate_no_track_ambiguous_and_out_of_history(self):
        """AC-3：插件层六值其余三值——NO_TRACK_AT_K（第二级 no_adoption）、AMBIGUOUS、FRAME_NOT_IN_HISTORY。"""
        near = [320.0 + 2.0, 240.0, 384.0 + 2.0, 288.0]
        frames = [{"tracked": [(1, PX_A), (2, PX_B), (3, near)]}] * 3
        far_sot = lambda: ScriptedTracker([TrackerResult((0.9, 0.9, 0.05, 0.05), True, 0.9, "tracker")] * 5)
        tracker, _, _ = resident(self.fixture, frames, level2_factory=far_sot)
        tracker.attach_frame_source(_Repo(range(0, 3)))
        for frame_id in range(3):
            tracker.step(_image(), frame_id, step_meta(frame_id))
        nothing_here = (0.80, 0.02, 0.05, 0.05)
        d = tracker.designate(nothing_here, 1)
        self.assertEqual((d.result, d.level2["reason"], tracker.pointer()), ("NO_TRACK_AT_K", "no_adoption", None))
        d = tracker.designate((321 / W, 240 / H, 64 / W, 48 / H), 1)
        self.assertEqual((d.result, d.candidates, tracker.pointer()), ("AMBIGUOUS", (2, 3), None))
        d = tracker.designate(NORM_A, 99)
        self.assertEqual(d.result, "FRAME_NOT_IN_HISTORY")

    def test_pointer_switch_keeps_associator(self):
        """AC-4：两次 designate→follow（一次经第二级）后关联器对象、库帧号单调、其他 ID 集合不变。"""
        frames = [{"tracked": [(1, PX_A)]}] + [{"tracked": [(1, PX_A), (2, PX_B)]}] * 4
        tracker, model, associators = resident(self.fixture, frames, level2_factory=lambda: ScriptedTracker([TrackerResult(NORM_B, True, 0.9, "tracker")] * 5))
        repo = _Repo(range(0, 5))
        tracker.attach_frame_source(repo)
        library = []
        for frame_id in range(3):
            tracker.step(_image(), frame_id, step_meta(frame_id))
            library.append(tracker.library_frame_id)
        associator = tracker.associator
        first = tracker.designate(NORM_A, 2)
        self.assertEqual((first.result, first.resolution_level, tracker.pointer()), ("BOUND", 1, 1))
        for frame_id in range(3, 5):
            tracker.step(_image(), frame_id, step_meta(frame_id))
            library.append(tracker.library_frame_id)
        second = tracker.designate(NORM_B, 0)  # k=0 帧 2 号车未被检测 → 第二级
        self.assertEqual((second.result, second.resolution_level, tracker.pointer()), ("BOUND", 2, 2))
        self.assertIs(tracker.associator, associator)
        self.assertEqual(len(associators), 1)
        self.assertEqual(library, sorted(library))
        self.assertEqual({r.track_id for r in tracker.history(4).tracks}, {1, 2})
        self.assertEqual(model.calls, 5)  # 只有 step 调检测，切换零检测

    def test_level2_replay_keeps_associator(self):
        """AC-4/AC-19：第二级 SOT 实例独立、只被工厂调用一次、回放后丢弃，常驻关联器与库帧号不变。"""
        sots = []

        def factory():
            sots.append(ScriptedTracker([TrackerResult(NORM_B, True, 0.9, "tracker")] * 5))
            return sots[-1]

        frames = [{}] + [{"tracked": [(7, PX_B)]}] * 3
        tracker, _, _ = resident(self.fixture, frames, level2_factory=factory)
        tracker.attach_frame_source(_Repo(range(0, 4)))
        for frame_id in range(4):
            tracker.step(_image(), frame_id, step_meta(frame_id))
        associator, library, ids = tracker.associator, tracker.library_frame_id, {r.track_id for r in tracker.history(3).tracks}
        result = tracker.designate(NORM_B, 0)
        self.assertEqual((result.result, result.resolution_level, result.track_id), ("BOUND", 2, 7))
        self.assertEqual(len(sots), 1)
        self.assertIsNot(sots[0], associator)
        self.assertEqual(len(sots[0].init_calls), 1)
        for got, want in zip(sots[0].init_calls[0], NORM_B):
            self.assertAlmostEqual(got, want, places=9)
        self.assertFalse(any(value is sots[0] for value in vars(tracker).values()))
        self.assertIs(tracker.associator, associator)
        self.assertEqual((tracker.library_frame_id, {r.track_id for r in tracker.history(3).tracks}), (library, ids))


class _Bundle:
    def __init__(self, frame_id):
        self.frame_id = frame_id
        self.image = _image()
        self.metadata = step_meta(frame_id)


class _Repo:
    def __init__(self, frame_ids):
        self.frame_ids = set(frame_ids)

    def load(self, frame_id):
        if frame_id not in self.frame_ids:
            raise FileNotFoundError(frame_id)
        return _Bundle(frame_id)


@unittest.skipUnless(HAVE_LIBS, "需要 .venv-yoloe（ultralytics 8.4.104 + lap）")
class ResidentLibrary(unittest.TestCase):
    """钉版库关联器 + 位姿补偿子类：`pose` 施加单应、`none` 不补偿、`optflow` 走库原路径。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def test_resident_associator_pose_warp_applied(self):
        from controller.pose_gmc import pose_homography  # noqa: PLC0415

        fixture = SpecFixture(Path(self._tmp.name), args=library_args("botsort"))
        det = [BOX + [0.9, 1.0]]
        model = ScriptedModel([det] * 4, library_boxes)
        tracker = dat.DetAssocTracker(
            spec_path=fixture.path, device="cpu", model_loader=lambda path: model, check_library_version=False, mode="resident"
        )
        metas = [step_meta(i) for i in range(4)]
        raw = [0.70105738, 0.0, 0.09229596, 0.70105738]
        norm = sum(v * v for v in raw) ** 0.5
        metas[2]["camera_rotation_xyzw"] = [v / norm for v in raw]  # 约 15° 转动
        for i in range(4):
            tracker.step(_image(), i, metas[i])
        self.assertEqual(tracker.associator.gmc_source, "pose")
        self.assertEqual((tracker.associator.pose_warps_applied, tracker.pose_warp_skipped), (3, 0))
        self.assertIsNotNone(pose_homography(metas[1], metas[2]))
        self.assertEqual(tracker.library_frame_id, 4)


# --- P1-ENG-CAPTURE-001 AC-1 / AC-3（K1/K3）：类别策略与只读 KF 快照 -----------------------------------


class _PolicyModel:
    """按 `agnostic_nms` 模拟 NMS：两类重叠框在按类 NMS 下都留下、类别无关 NMS 下只留高分一个。"""

    def __init__(self, boxes_factory):
        self.boxes_factory = boxes_factory
        self.kwargs = []

    def predict(self, source, **kwargs):
        self.kwargs.append(kwargs)
        rows = [[100.0, 100.0, 160.0, 140.0, 0.9, 1.0]]
        if not kwargs.get("agnostic_nms"):
            rows.append([102.0, 101.0, 161.0, 141.0, 0.8, 0.0])
        return [_Result(self.boxes_factory(rows))]


class _CapturingAssociator(FakeAssociator):
    def __init__(self):
        super().__init__()
        self.seen = []

    def update(self, boxes, image):
        self.seen.append([list(row) for row in boxes.rows])
        return super().update(boxes, image)


class ClassPolicyTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fixture = SpecFixture(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def build(self, **options):
        model = _PolicyModel(_Boxes)
        associators = []

        def factory(algorithm, args):
            associators.append(_CapturingAssociator())
            return associators[-1]

        tracker = dat.DetAssocTracker(spec_path=self.fixture.path, device="cpu", model_loader=lambda p: model,
                                      tracker_factory=factory, check_library_version=False, mode="resident", **options)
        return tracker, model, associators

    def test_defaults_unchanged_per_class_pose(self):
        tracker, model, _ = self.build()
        manifest = tracker.manifest_identity()
        self.assertEqual((tracker.class_policy, tracker.gmc_source), ("per_class", "pose"))
        self.assertEqual((manifest["class_policy"], manifest["agnostic_nms"], manifest["gmc_source"]), ("per_class", False, "pose"))
        tracker.step(_image(), 1, step_meta(1))
        self.assertNotIn("agnostic_nms", model.kwargs[0])  # per_class 调用逐字同修改前

    def test_unify_vehicle_one_box_class_zero(self):
        tracker, model, associators = self.build(class_policy="unify_vehicle", gmc_source="pose-center")
        tracker.step(_image(), 1, step_meta(1))
        self.assertTrue(model.kwargs[0]["agnostic_nms"])
        self.assertEqual(len(associators[0].seen[0]), 1)
        self.assertEqual(associators[0].seen[0][0][5], 0.0)
        entry = tracker.history(1)
        self.assertEqual([(d.det_index, d.cls) for d in entry.raw_detections], [(0, 0)])
        manifest = tracker.manifest_identity()
        self.assertEqual((manifest["class_policy"], manifest["agnostic_nms"], manifest["gmc_source"]), ("unify_vehicle", True, "pose-center"))

    def test_detection_cache_key_binds_policy(self):
        per_class, _, _ = self.build()
        unify, _, _ = self.build(class_policy="unify_vehicle")
        a, b = per_class.detection_cache_key("f" * 64), unify.detection_cache_key("f" * 64)
        self.assertNotEqual(a, b)
        self.assertEqual(a[1:3], ("per_class", False))
        self.assertEqual(b[1:3], ("unify_vehicle", True))
        self.assertEqual(a[-1], "f" * 64)
        with self.assertRaises(ValueError):
            self.build(class_policy="merge")

    def test_new_values_only_passed_by_capture_entry_points(self):
        """SOT 第二级、e1、兼容会话与其他离线工厂不传新值；只有捕获会话入口、`tools/eng_capture/` 与 P1-ENG-FASTFIX-001
        的捕获模式离线回放（`tools/eng_fastfix/`，AC-7 与会话同一捕获链）显式传。"""
        offenders = []
        for path in list((PROJECT_ROOT / "controller").glob("*.py")) + list((PROJECT_ROOT / "tools").rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for token in ('class_policy="unify_vehicle"', "class_policy=CAPTURE_CLASS_POLICY", 'gmc_source="pose-center"', "gmc_source=CAPTURE_GMC_SOURCE"):
                if (token in text and path.name != "language_loop.py" and "eng_capture" not in path.parts
                        and "eng_fastfix" not in path.parts):
                    offenders.append((str(path.relative_to(PROJECT_ROOT)), token))
        self.assertEqual(offenders, [])
        source = (PROJECT_ROOT / "controller" / "language_loop.py").read_text(encoding="utf-8")
        self.assertEqual(source.count("class_policy=CAPTURE_CLASS_POLICY"), 1)

    def test_no_controller_decision_on_class_one(self):
        import re  # noqa: PLC0415

        for path in (PROJECT_ROOT / "controller").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"cls\)?\s*==\s*1\b", text), path.name)

    def test_weights_spec_and_freeze_unchanged(self):
        from tools.eng_capture.common import accepted_base_commit  # noqa: PLC0415

        base = accepted_base_commit()
        if base is None:
            self.skipTest("git history unavailable")
        diff = subprocess.run(["git", "diff", "--stat", base, "--", "config/det-assoc-v1.models.json", "docs/evidence/P1-ENG-FAST-002-freeze.json"],
                              cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout
        self.assertEqual(diff.strip(), "")


@unittest.skipUnless(HAVE_LIBS, "需要 .venv-yoloe（ultralytics 8.4.104 + lap）")
class KfSnapshotTests(unittest.TestCase):
    """AR1-2：同帧 prior/post 分离（真实 BoT-SORT）；新建键无 prior；lost 行 post 记 prior；错帧/缺失返回 None。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fixture = SpecFixture(Path(self._tmp.name), args=library_args("botsort"))

    def tearDown(self):
        self._tmp.cleanup()

    def run_frames(self, script, gmc="pose-center", history_view="capture"):
        model = ScriptedModel(script, library_boxes)
        tracker = dat.DetAssocTracker(spec_path=self.fixture.path, device="cpu", model_loader=lambda p: model,
                                      check_library_version=False, mode="resident", gmc_source=gmc, class_policy="unify_vehicle",
                                      history_view=history_view)
        for frame_id in range(len(script)):
            tracker.step(_image(), 100 + frame_id, step_meta(100 + frame_id))
        return tracker

    def test_prior_and_post_separate_in_same_frame(self):
        moving = [[[100.0 + 8 * i, 100.0, 160.0 + 8 * i, 140.0, 0.9, 0.0]] for i in range(5)]
        tracker = self.run_frames(moving)
        entry = tracker.history(104)
        row = entry.rows("tracked")[0]
        prior = entry.prior(row.track_id)
        post = entry.post(row.track_id)
        self.assertEqual((prior.phase, post.phase, prior.sensor_frame_id, prior.library_frame_id), ("prior", "posterior", 104, 5))
        self.assertNotEqual(prior.xywh_px, post.xywh_px)
        self.assertIs(row.kf, post)
        self.assertEqual(row.matched_det_index, 0)
        self.assertEqual(tracker.prior_snapshots(104), entry.prior_snapshots)
        self.assertIsNone(tracker.prior_snapshots(999))
        first = tracker.history(100)
        self.assertEqual(first.prior_snapshots, ())  # 本帧新建键无更新前 prior（显式缺失）
        self.assertTrue(first.priors_available)

    def test_new_key_unconfirmed_and_lost_post_is_prior(self):
        script = [[[100.0, 100.0, 160.0, 140.0, 0.9, 0.0]]] * 3 + [[], [[100.0, 100.0, 160.0, 140.0, 0.9, 0.0], [400.0, 300.0, 460.0, 340.0, 0.9, 0.0]]]
        tracker = self.run_frames(script)
        lost_entry = tracker.history(103)
        lost = lost_entry.rows("lost")
        self.assertEqual(len(lost), 1)
        self.assertEqual(lost_entry.post(lost[0].track_id).phase, "prior")
        newest = tracker.history(104)
        unconfirmed = newest.rows("unconfirmed")
        self.assertEqual(len(unconfirmed), 1)
        self.assertIsNone(newest.prior(unconfirmed[0].track_id))
        self.assertGreaterEqual(unconfirmed[0].matched_det_index, 0)
        self.assertEqual(tracker.pointer_result(104).reason, "no_pointer")

    def test_history_view_default_compat_capture_only_when_explicit(self):
        """IR-1：构造器缺省为旧消费视图（不从 class_policy/GMC 推断）；未确认行只在显式捕获视图里出现。"""
        script = [[[100.0, 100.0, 160.0, 140.0, 0.9, 0.0]]] * 3 + [[], [[100.0, 100.0, 160.0, 140.0, 0.9, 0.0], [400.0, 300.0, 460.0, 340.0, 0.9, 0.0]]]
        default = dat.DetAssocTracker(spec_path=self.fixture.path, device="cpu", model_loader=lambda p: ScriptedModel(script, library_boxes),
                                      check_library_version=False, mode="resident")
        self.assertEqual(default.core.history_view, "compat")
        compat = self.run_frames(script, history_view="compat")
        self.assertEqual(compat.core.history_view, "compat")
        self.assertEqual(compat.history(104).rows("unconfirmed"), ())
        self.assertEqual(len(self.run_frames(script).history(104).rows("unconfirmed")), 1)


if __name__ == "__main__":
    unittest.main()
