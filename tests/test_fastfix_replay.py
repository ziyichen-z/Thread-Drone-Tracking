#!/usr/bin/env python3
"""P1-ENG-FASTFIX-001 AC-7 回放体（零模型）：合成检测缓存 + 准入原始帧元数据，核两臂、逐注入输出与评分口径。

只在装有钉版库的解释器（数据根 `.venv-yoloe`）里运行：`DetAssocTracker` 以注入替身模型构造（不加载权重模型、
不推理），关联器为钉版库 BoT-SORT；缓存未命中即报错（零推理）。准入帧缺失 → 跳过。
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import target_manager as tm  # noqa: E402
from tools.eng_fastfix.common import ADMITTED_FRAMES  # noqa: E402

FRAME_RANGE = range(0, 60)
CLICK = {"label": "red_car", "frame_id": 5, "x_px": 249.0, "y_px": 231.0}
RULE = {"offset_step": 20, "max_injections": 12, "rebuild_skip_frames": 3, "warmup_frames": 5, "follow_frames_after_commit": 10}


def library_ready() -> bool:
    try:
        import torch  # noqa: F401, PLC0415
        import ultralytics  # noqa: F401, PLC0415
    except ImportError:
        return False
    return all((ADMITTED_FRAMES / f"frame_{f:010d}.json").is_file() for f in FRAME_RANGE)


def synthetic_rows(frame_id, *, red=True):
    """合成检测（像素 xyxy、置信度、类别）：红车每帧右移 6.8 px；一辆静止车作干扰。"""
    rows = [[380.0, 103.0, 490.0, 153.0, 0.92, 0.0]]
    if red:
        cx = 249.0 + 6.8 * (frame_id - 5)
        rows.append([cx - 35.0, 213.0, cx + 35.0, 249.0, 0.9, 0.0])
    return rows


def build_fixture(frames_dir, *, drop_red_after=None):
    from controller.det_assoc_tracker import DetAssocTracker  # noqa: PLC0415
    from tools.eng_capture.replay import CachedOrLiveModel, library_boxes  # noqa: PLC0415
    from tools.eng_fastfix import replay  # noqa: PLC0415

    frames = replay.load_frames(list(FRAME_RANGE), frames=frames_dir)
    detector = DetAssocTracker(spec_path=replay.SPEC, device="cpu", model_loader=lambda _p: object(), mode="resident",
                               class_policy="unify_vehicle")
    cache = {detector.detection_cache_key(f.image_sha256): synthetic_rows(f.frame_id, red=drop_red_after is None or f.frame_id <= drop_red_after)
             for f in frames}
    wrapped = CachedOrLiveModel(cache, None, library_boxes)
    params, sha, _ = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)
    fastfix, ff_sha, _ = tm.load_fastfix_config(tm.DEFAULT_FASTFIX_CONFIG, params, replay.HZ)

    def factory():
        return replay.CaptureRun(lambda _p: wrapped, params, fastfix, sha, ff_sha, tracker_factory=DetAssocTracker)

    return replay.cached(frames, lambda s: detector.detection_cache_key(s)), factory, wrapped


@unittest.skipUnless(library_ready(), "pinned library or admitted frames unavailable")
class Ac7ReplayBodyTests(unittest.TestCase):
    def test_two_arms_and_outputs(self):
        from tools.eng_fastfix import replay  # noqa: PLC0415

        frames, factory, wrapped = build_fixture(ADMITTED_FRAMES)
        report = replay.run_ac7(frames, {"click": CLICK, "injection_rule": RULE}, factory)
        self.assertTrue(report["bind"]["committed"])
        self.assertEqual(report["bind"]["commit_frame"], 5)
        injected = sorted({r["f_inj"] for r in report["injections"]})
        self.assertEqual(injected, [25, 45])
        for record in report["injections"]:
            self.assertIn(record["outcome"], replay.OUTCOMES)
        on = [r for r in report["injections"] if r["arm"] == "on"]
        off = [r for r in report["injections"] if r["arm"] == "off"]
        self.assertEqual([r["outcome"] for r in off], ["skipped", "skipped"])
        self.assertEqual({r["cause"] for r in off}, {"auto_reacquire_off"})
        self.assertEqual(sum(r["auto_commits"] for r in off), 0)
        committed = [r for r in on if r["outcome"] == "committed"]
        self.assertTrue(committed, on)
        for record in committed:
            self.assertEqual(record["f_ready"], record["f_inj"] + 4)
            self.assertGreaterEqual(record["latency_frames_from_ready"], 2)
            self.assertTrue(record["followed"][0]["box_norm"])
        summary = replay.summarize(report)
        self.assertEqual(summary["off_arm_auto_commits"], 0)
        self.assertGreater(wrapped.hits, 0)

    def test_target_gone_fails_and_not_applicable(self):
        from tools.eng_fastfix import replay  # noqa: PLC0415

        frames, factory, _ = build_fixture(ADMITTED_FRAMES, drop_red_after=27)
        report = replay.run_ac7(frames, {"click": CLICK, "injection_rule": RULE}, factory)
        on = {r["f_inj"]: r for r in report["injections"] if r["arm"] == "on"}
        self.assertEqual(on[25]["outcome"], "failed")
        self.assertEqual(on[25]["cause"], "deadline_frame")
        self.assertEqual(on[45]["outcome"], "not_applicable")

    def test_scoring_never_vacuous(self):
        from tools.eng_fastfix import score  # noqa: PLC0415

        self.assertEqual(score.score_ac7({"injections": []}, {})["verdict"], "NO_SUCCESS_EVIDENCE")
        report = {"injections": [{"arm": "on", "outcome": "committed", "f_inj": 1, "commit_frame": 9, "track_key": 3,
                                  "followed": [{"frame_id": 9, "box_norm": [0.1, 0.1, 0.1, 0.1]}]}]}
        truth = {9: {"truth_box_available": True, "geometrically_visible": True, "truth_box_x": 0.1, "truth_box_y": 0.1,
                     "truth_box_width": 0.1, "truth_box_height": 0.1}}
        self.assertEqual(score.score_ac7(report, truth)["verdict"], "PASS")
        self.assertEqual(score.score_ac7(report, {})["verdict"], "FAIL")  # 提交帧真值缺失不空真
        truth[9]["truth_box_x"] = 0.5
        self.assertEqual(score.score_ac7(report, truth)["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
