#!/usr/bin/env python3
"""P1-ENG-CAPTURE-001 AC-17/18/19/22…25/27 的工具口径（零模型）：合成滚转几何与删失、断轨/误跟、Wilson 区间、
新臂逐帧判据、现象门、启动前守卫（保真/剧本/账本）、准入核对、新臂端到端（假检测器 + 钉版库关联器）与 Play 读数。"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import target_manager as tm  # noqa: E402
from controller.pose_gmc import map_point  # noqa: E402
from tools.eng_capture import analyze_play, replay  # noqa: E402
from tools.eng_capture.common import ADMITTED_FRAMES  # noqa: E402

HAVE_LIBS = importlib.util.find_spec("ultralytics") is not None and importlib.util.find_spec("lap") is not None
META = {
    "camera_rotation_xyzw": [0.7071068286895752, 0.0, 0.0, 0.7071068286895752],
    "camera_position_world_m": [132.0, 25.2, 117.0],
    "intrinsics_px": {"fx": 415.69219970703127, "fy": 415.69219970703127, "cx": 320.0, "cy": 240.0},
    "width": 640, "height": 480, "frame_id": 0, "simulation_time_s": 0.0, "capture_monotonic_s": 1.0, "capture_unix_s": 1.0,
}
TRUTH = {"truth_box_available": True, "geometrically_visible": True, "truth_box_x": 0.4, "truth_box_y": 0.4, "truth_box_width": 0.1, "truth_box_height": 0.1}
TRUTH_BOX = (0.4, 0.4, 0.1, 0.1)


class RollGeometryTests(unittest.TestCase):
    def test_schedule_turns_then_holds(self):
        self.assertEqual(replay.roll_schedule(25.0, 120.0, 1)[:6], [25.0, 50.0, 75.0, 100.0, 120.0, 120.0])
        self.assertEqual(replay.roll_schedule(15.0, 60.0, -1)[-1], -60.0)
        self.assertEqual(len(replay.roll_schedule(20.0, 60.0, 1)), replay.ROLL_FRAMES)

    def test_roll_is_rotation_about_principal_point(self):
        for roll in (25.0, -120.0):
            h = replay.roll_homography(META, roll)
            cx, cy = map_point(h, 320.0, 240.0)
            self.assertAlmostEqual(cx, 320.0, places=6)
            self.assertAlmostEqual(cy, 240.0, places=6)
            x, y = map_point(h, 420.0, 240.0)
            self.assertAlmostEqual(math.hypot(x - 320.0, y - 240.0), 100.0, places=6)
            self.assertAlmostEqual(abs(math.degrees(math.atan2(y - 240.0, x - 320.0))), abs(roll), places=4)

    def test_truth_geometry_and_censoring(self):
        plain = replay.score_truth_geometry(TRUTH, None)
        self.assertFalse(plain["censored"])
        self.assertEqual(plain["center"], [0.45 * 640, 0.45 * 480])
        edge = dict(TRUTH, truth_box_x=0.97)
        self.assertTrue(replay.score_truth_geometry(edge, None)["censored"])  # 画内面积 < 50%
        rolled = replay.score_truth_geometry(TRUTH, replay.roll_homography(META, 90.0))
        self.assertEqual(len(rolled["polygon"]), 4)
        self.assertIsNone(replay.score_truth_geometry({"truth_box_available": False}, None))

    def test_sequence_break_misfollow_and_right_censor(self):
        params = tm.CaptureParams()
        geometry = {"censored": False, "polygon": [(0, 0), (10, 0), (10, 10), (0, 10)]}
        on = {"valid": True, "center": (5, 5)}
        off = {"valid": False, "center": None}
        self.assertFalse(replay.score_roll_sequence([on] * 4 + [off] * 4 + [on], [geometry] * 9, params)["broken"])
        self.assertTrue(replay.score_roll_sequence([on] + [off] * 5 + [on], [geometry] * 7, params)["broken"])
        miss = replay.score_roll_sequence([on, {"valid": True, "center": (50, 50)}], [geometry] * 2, params)
        self.assertTrue(miss["broken"] and miss["misfollow"])
        tail = replay.score_roll_sequence([on, off, off], [geometry] * 3, params)
        self.assertEqual((tail["broken"], tail["right_censored_gap"]), (False, True))
        censored = replay.score_roll_sequence([on] + [off] * 6, [geometry] + [{"censored": True}] * 6, params)
        self.assertFalse(censored["broken"])

    def test_cells_wilson_and_non_inferiority(self):
        seq = lambda b, n, ev=True: {"omega": 25.0, "theta": 120.0, "evaluable": ev, "baseline": {"broken": b}, "new": {"broken": n}}
        cells = replay.score_roll_cells([seq(True, False), seq(True, True), seq(False, False), seq(True, False, ev=False)])
        self.assertEqual((cells[0]["baseline"]["n"], cells[0]["baseline"]["broken"], cells[0]["new"]["broken"]), (3, 2, 1))
        self.assertTrue(cells[0]["non_inferior"])
        low, high = replay.wilson_interval(2, 3)
        self.assertTrue(0 < low < 2 / 3 < high < 1)
        self.assertIsNone(replay.wilson_interval(0, 0))


def trace_of(rows):
    trace = replay.NewArmTrace()
    trace.frames = rows
    return trace


class ScoringTests(unittest.TestCase):
    def test_new_arm_window_verdicts(self):
        params = tm.CaptureParams()
        truth = {557: TRUTH, 558: TRUTH, 559: TRUTH}
        effect = lambda f: {"frame_id": f, "version": 1}  # noqa: E731 — 同帧同版本效果（C1-3 一致性前提）
        good = [{"frame_id": 557, "continuity": tm.SUPPORTED, "observation": tm.OBSERVED, "age": 0, "observed_box_norm": [0.4, 0.4, 0.1, 0.1], "track_key": 1, "version": 1, "effect": effect(557)},
                {"frame_id": 558, "continuity": tm.TENTATIVE, "observation": tm.PREDICTED, "age": 1, "observed_box_norm": None, "track_key": 1, "version": 1, "effect": effect(558)},
                {"frame_id": 559, "continuity": tm.SUPPORTED, "observation": tm.OBSERVED, "age": 0, "observed_box_norm": [0.41, 0.4, 0.1, 0.1], "track_key": 1, "version": 1, "effect": effect(559)}]
        self.assertEqual(replay.score_new_arm_window(trace_of(good), truth, params)["verdict"], "PASS")
        bad = [dict(good[0]), dict(good[1], continuity=tm.BROKEN), dict(good[2], observed_box_norm=[0.0, 0.0, 0.05, 0.05])]
        scored = replay.score_new_arm_window(trace_of(bad), truth, params)
        self.assertEqual((scored["verdict"], scored["broken_frames"], scored["misbound_frames"]), ("FAIL", 1, 1))

    def test_provisional_readings(self):
        """AC-17 另报暂定读数（零模型）：R-1 下界只计可评缺口；P_center 残差取效果瞄准点；点击帧（pre_click）与非本帧效果
        不计；进入 TENTATIVE 且真值可见计为误 TENTATIVE。"""
        truth_row = dict(TRUTH, target_world_x_m=10.0, target_world_y_m=0.2, target_world_z_m=20.0)
        truth = {557: truth_row, 558: truth_row, 559: truth_row, 560: dict(truth_row, truth_box_available=False)}
        meta = dict(META, camera_right_world=[1.0, 0.0, 0.0], camera_up_world=[0.0, 0.0, 1.0], camera_forward_world=[0.0, -1.0, 0.0])
        effect = lambda f, x: {"frame_id": f, "gimbal": "observed", "aim_point_world_m": [x, 0.975, 20.0]}  # noqa: E731
        frames = [
            {"frame_id": 557, "observation": tm.OBSERVED, "continuity": tm.SUPPORTED, "observed_box_norm": [0.4, 0.4, 0.1, 0.1],
             "effect": effect(557, 99.0), "pre_click": {"track_key": 1}},
            {"frame_id": 558, "observation": tm.OBSERVED, "continuity": tm.SUPPORTED, "observed_box_norm": [0.4, 0.4, 0.1, 0.1], "effect": effect(558, 13.0)},
            {"frame_id": 559, "observation": tm.PREDICTED, "continuity": tm.TENTATIVE, "observed_box_norm": None, "effect": effect(558, 13.0)},
            {"frame_id": 560, "observation": tm.PREDICTED, "continuity": tm.TENTATIVE, "observed_box_norm": None, "effect": None},
        ]
        ac18 = {"delete_m1_repair": {"gap": 1, "iou_verdict": "PASS", "iou": 0.8}, "delete_m2_repair": {"gap": 2, "iou_verdict": "FAIL", "iou": 0.1},
                "delete_m4_repair": {"gap": 4, "iou_verdict": "NOT_EVALUABLE", "iou": None},
                "delete_m6_repair_off": {"gap": 6, "iou_verdict": "PASS", "iou": 0.9}}
        readings = replay.score_provisional_readings(frames, ac18, truth, {f: dict(meta, frame_id=f) for f in truth})
        self.assertEqual((readings["R-1"]["lower_bound_frames"], readings["R-1"]["n_evaluable_gaps"]), (1, 2))
        residuals = readings["measurement_point_residuals"]
        self.assertEqual([r["frame_id"] for r in residuals["rows"]], [558])
        self.assertAlmostEqual(residuals["p_center"]["median_m"], 3.0)
        self.assertEqual(residuals["bottom_center"]["n"], 1)
        self.assertEqual((readings["tentative"]["entries"], readings["tentative"]["entries_truth_visible"]), ([559], [559]))

    def test_phenomenon_gate(self):
        truth = {f: TRUTH for f in range(555, 570)}
        records = [{"frame_id": f, "ok": f != 561} for f in range(555, 570)]
        self.assertEqual(replay.score_phenomenon_gate(records, truth)["pointer_not_ok_truth_visible_frames"], [561])
        self.assertFalse(replay.score_phenomenon_gate([{"frame_id": f, "ok": True} for f in range(555, 570)], truth)["reproduced"])

    def test_injection_iou_and_not_evaluable(self):
        params = tm.CaptureParams()
        truth = {f: TRUTH for f in range(559, 570)}
        target_px = [0.4 * 640, 0.4 * 480, 0.5 * 640, 0.5 * 480]
        frames = [
            {"frame_id": 560, "track_key": 1, "observation": tm.OBSERVED, "continuity": tm.SUPPORTED, "observed_box_norm": [0.4, 0.4, 0.1, 0.1],
             "raw_detections_px": [[*target_px, 0.9, 0.0]], "priors_xywh_px": {"1": [288.0, 216.0, 64.0, 48.0]}, "effect": {"gimbal": "observed", "authorization_row": 6}},
            {"frame_id": 561, "track_key": 1, "observation": tm.PREDICTED, "continuity": tm.TENTATIVE, "observed_box_norm": None,
             "raw_detections_px": [], "priors_xywh_px": {"1": [288.0, 216.0, 64.0, 48.0]}, "effect": {"gimbal": "predicted", "authorization_row": 7}},
            {"frame_id": 562, "track_key": 1, "observation": tm.OBSERVED, "continuity": tm.SUPPORTED, "observed_box_norm": [0.4, 0.4, 0.1, 0.1],
             "raw_detections_px": [[*target_px, 0.9, 0.0]], "priors_xywh_px": {"1": [0.45 * 640, 0.45 * 480, 64.0, 48.0]},
             "effect": {"gimbal": "observed", "authorization_row": 6}},
        ]
        result = replay.score_injection(trace_of(frames), truth, params, start=561, gap=1)
        self.assertEqual((result["iou_verdict"], result["all_row7_have_look_at"]), ("PASS", True))
        lonely = replay.score_injection(trace_of(frames[:2]), truth, params, start=561, gap=1)
        self.assertEqual((lonely["iou_verdict"], lonely["not_evaluable_reason"]), ("NOT_EVALUABLE", "no_detection_matching_truth_within_t_repair"))

    # --- C1返工 C1-2（AC-18 检测判据）与 C1-3（同帧状态/效果一致）的具名回归 -----------------------------

    @staticmethod
    def _px(box_norm):
        x, y, w, h = box_norm
        return [x * 640, y * 480, (x + w) * 640, (y + h) * 480]

    def test_c1_2_next_observation_is_raw_detection_even_without_accepted_observation(self):
        """AC-18：下一次真实观测 = 缺口后首个与真值 IoU ≥ 0.5 的**检测**（策略后原始检测），不是被接受的 OBSERVED；
        BROKEN 不表示检测不存在。修前按 accepted OBSERVED 找下一观测，m=4 类缺口一律 NOT_EVALUABLE。"""
        params = tm.CaptureParams()
        truth = {f: TRUTH for f in range(559, 572)}
        target_px = self._px(TRUTH_BOX)
        prior_ok = [288.0, 216.0, 64.0, 48.0]
        frames = [{"frame_id": 560, "track_key": 11, "observation": tm.OBSERVED, "continuity": tm.SUPPORTED, "observed_box_norm": list(TRUTH_BOX),
                   "raw_detections_px": [[*target_px, 0.9, 0.0]], "priors_xywh_px": {"11": prior_ok}, "effect": {"gimbal": "observed", "authorization_row": 6}}]
        for f in range(561, 565):
            frames.append({"frame_id": f, "track_key": 11, "observation": tm.PREDICTED, "continuity": tm.TENTATIVE, "observed_box_norm": None,
                           "raw_detections_px": [], "priors_xywh_px": {"11": prior_ok}, "effect": {"gimbal": "predicted", "authorization_row": 7}})
        frames.append({"frame_id": 565, "track_key": 11, "observation": tm.PREDICTED, "continuity": tm.BROKEN, "observed_box_norm": None,
                       "prior_xywh_px": None, "raw_detections_px": [[*target_px, 0.9, 0.0]], "priors_xywh_px": {"11": prior_ok},
                       "effect": {"gimbal": "none", "authorization_row": 3}})
        result = replay.score_injection(trace_of(frames), truth, params, start=561, gap=4)
        self.assertEqual((result["iou_verdict"], result["next_observation_frame"], result["original_key"]), ("PASS", 565, 11))
        self.assertAlmostEqual(result["iou"], 1.0)
        no_detection = [dict(r, raw_detections_px=[]) if r["frame_id"] >= 561 else r for r in frames]
        self.assertEqual(replay.score_injection(trace_of(no_detection), truth, params, start=561, gap=4)["iou_verdict"], "NOT_EVALUABLE")

    def test_c1_2_prediction_is_original_key_prior_not_repaired_key(self):
        """修复后不能换为新绑定键自己的 prior：预测框取注入前原绑定键在下一观测帧的同帧 prior。
        修前取该帧记录里新绑定键（修复后）的 prior。"""
        params = tm.CaptureParams()
        truth = {f: TRUTH for f in range(559, 570)}
        target_px = self._px(TRUTH_BOX)
        good, bad = [288.0, 216.0, 64.0, 48.0], [100.0, 100.0, 40.0, 30.0]
        frames = [
            {"frame_id": 560, "track_key": 11, "observation": tm.OBSERVED, "continuity": tm.SUPPORTED, "observed_box_norm": list(TRUTH_BOX),
             "raw_detections_px": [[*target_px, 0.9, 0.0]], "priors_xywh_px": {"11": good}, "effect": {"gimbal": "observed", "authorization_row": 6}},
            {"frame_id": 561, "track_key": 11, "observation": tm.PREDICTED, "continuity": tm.TENTATIVE, "observed_box_norm": None,
             "raw_detections_px": [], "priors_xywh_px": {"11": good}, "effect": {"gimbal": "predicted", "authorization_row": 7}},
            {"frame_id": 562, "track_key": 13, "observation": tm.OBSERVED, "continuity": tm.SUPPORTED, "observed_box_norm": list(TRUTH_BOX),
             "prior_xywh_px": bad, "raw_detections_px": [[*target_px, 0.9, 0.0]], "priors_xywh_px": {"11": good, "13": bad},
             "effect": {"gimbal": "observed", "authorization_row": 6}},
        ]
        result = replay.score_injection(trace_of(frames), truth, params, start=561, gap=1)
        self.assertEqual((result["iou_verdict"], result["original_key"]), ("PASS", 11))

    def test_ir_c2_5_injection_missing_original_prior_is_evidence_missing(self):
        """IR-C2-5（用户 2026-10-10 裁定：缺原键 prior 记证据缺失，不扩 NOT_EVALUABLE、不从分母去掉、不计通过）：
        下一真实观测帧上原键无同帧 prior → `iou_verdict = EVIDENCE_MISSING`（原因单列），不是删失口径的 NOT_EVALUABLE。"""
        params = tm.CaptureParams()
        truth = {f: TRUTH for f in range(559, 570)}
        target_px = self._px(TRUTH_BOX)
        good = [288.0, 216.0, 64.0, 48.0]
        frames = [
            {"frame_id": 560, "track_key": 11, "observation": tm.OBSERVED, "continuity": tm.SUPPORTED, "observed_box_norm": list(TRUTH_BOX),
             "raw_detections_px": [[*target_px, 0.9, 0.0]], "priors_xywh_px": {"11": good}, "effect": {"gimbal": "observed", "authorization_row": 6}},
            {"frame_id": 561, "track_key": 11, "observation": tm.PREDICTED, "continuity": tm.TENTATIVE, "observed_box_norm": None,
             "raw_detections_px": [], "priors_xywh_px": {"11": good}, "effect": {"gimbal": "predicted", "authorization_row": 7}},
            {"frame_id": 562, "track_key": 13, "observation": tm.OBSERVED, "continuity": tm.SUPPORTED, "observed_box_norm": list(TRUTH_BOX),
             "raw_detections_px": [[*target_px, 0.9, 0.0]], "priors_xywh_px": {"13": good}, "effect": {"gimbal": "observed", "authorization_row": 6}},
        ]
        result = replay.score_injection(trace_of(frames), truth, params, start=561, gap=1)
        self.assertEqual((result["iou_verdict"], result["not_evaluable_reason"], result["iou"], result["next_observation_frame"]),
                         ("EVIDENCE_MISSING", "original_key_same_frame_prior_missing", None, 562))

    def test_c1_3_window_requires_same_frame_state_and_effect(self):
        """RR-1：按同一提交后状态/效果评分——记录的效果须是本帧、同版本的效果；状态与效果混记的帧不判 PASS。
        修前只看记录状态，提交前效果混入提交后状态时照判 PASS。"""
        params = tm.CaptureParams()
        truth = {557: TRUTH}
        record = {"frame_id": 557, "continuity": tm.SUPPORTED, "observation": tm.OBSERVED, "age": 0, "observed_box_norm": list(TRUTH_BOX),
                  "track_key": 11, "version": 5, "effect": {"frame_id": 557, "version": 4, "gimbal": "observed", "body": "FOLLOW"}}
        mixed = replay.score_new_arm_window(trace_of([record]), truth, params)
        self.assertEqual((mixed["verdict"], mixed["rows"][0]["verdict"]), ("FAIL", "STATE_EFFECT_INCONSISTENT"))
        consistent = dict(record, effect=dict(record["effect"], version=5))
        self.assertEqual(replay.score_new_arm_window(trace_of([consistent]), truth, params)["verdict"], "PASS")


class LaunchGuardTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_fidelity_confirmation_required(self):
        with self.assertRaises(replay.LaunchRefused):
            replay.load_fidelity_confirmation(None)
        roll_png, click_png = self.root / "roll.png", self.root / "click.png"
        roll_png.write_bytes(b"roll-sample")
        click_png.write_bytes(b"click-sample")
        samples = [{"kind": "synthetic_roll", "path": str(roll_png), "sha256": replay.sha256_file(roll_png)},
                   {"kind": "click_page", "path": "click.png", "sha256": replay.sha256_file(click_png)}]
        path = self.root / "f.json"
        base = {"schema_version": replay.FIDELITY_SCHEMA, "conclusion": "consistent", "confirmed_by": "user"}
        path.write_text(json.dumps({**base, "samples": samples[:1]}), encoding="utf-8")
        with self.assertRaises(replay.LaunchRefused):
            replay.load_fidelity_confirmation(path, root=self.root)
        path.write_text(json.dumps({**base, "samples": samples}), encoding="utf-8")
        self.assertEqual(replay.load_fidelity_confirmation(path, root=self.root)["confirmed_by"], "user")
        click_png.write_bytes(b"changed after the human looked")  # 被确认的样帧被改 → 拒绝
        with self.assertRaises(replay.LaunchRefused):
            replay.load_fidelity_confirmation(path, root=self.root)
        path.write_text(json.dumps({**base, "samples": [dict(samples[0]), {"kind": "click_page"}]}), encoding="utf-8")
        with self.assertRaises(replay.LaunchRefused):
            replay.load_fidelity_confirmation(path, root=self.root)

    def test_repository_confirmation_matches_ledger_samples(self):
        """AC-27：仓内确认文件（据账本 2026-10-10 条）结构合法；样帧在本机时现核 sha。"""
        path = PROJECT_ROOT / "docs" / "evidence" / "P1-ENG-CAPTURE-001-fidelity-confirmation.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual((document["schema_version"], document["conclusion"], document["confirmed_by"]),
                         (replay.FIDELITY_SCHEMA, "consistent", "ziyichen-z"))
        self.assertEqual(sorted({s["kind"] for s in document["samples"]}), ["click_page", "synthetic_roll"])
        if all((PROJECT_ROOT / s["path"]).is_file() for s in document["samples"]):
            replay.load_fidelity_confirmation(path)

    def test_click_script_requires_preregistered_red_car_at_557(self):
        path = self.root / "s.json"
        script = {"schema_version": replay.CLICK_SCRIPT_SCHEMA, "registered_by": "user",
                  "clicks": [{"label": "static_car", "frame_id": 500, "x_px": 1, "y_px": 1}, {"label": "red_car", "frame_id": 556, "x_px": 1, "y_px": 1}]}
        path.write_text(json.dumps(script), encoding="utf-8")
        with self.assertRaises(replay.LaunchRefused):
            replay.load_click_script(path)
        script["clicks"][1]["frame_id"] = 557
        path.write_text(json.dumps(script), encoding="utf-8")
        document, sha = replay.load_click_script(path)
        self.assertEqual((len(document["clicks"]), len(sha)), (2, 64))

    def test_ledger_balance_refuses_over_budget(self):
        ledger = json.loads(replay.LEDGER.read_text(encoding="utf-8"))
        # 夹具取仓库账本的信封与结构，但消耗归零（不随真实账本的已用量漂移）。
        ledger["counters"] = {k: 0 for k in ledger["counters"]}
        ledger["counters"]["candidates_started"] = 1  # C1-5：只有已开始（有归因）的候选可消耗
        ledger["events"] = [{"at": "2026-10-10T00:00:00Z", "counter": "candidates_started", "amount": 1, "candidate": 1, "note": "fixture"}]
        path = self.root / "ledger.json"
        path.write_text(json.dumps(ledger), encoding="utf-8")
        self.assertTrue(all(replay.ledger_balance(path, candidate=1, loads=1, frames=3962).values()))
        with self.assertRaises(replay.LaunchRefused):
            replay.ledger_balance(path, candidate=1, loads=1, frames=5501)
        with self.assertRaises(replay.LaunchRefused):
            replay.ledger_balance(path, candidate=1, loads=3, frames=10)
        path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(replay.LaunchRefused):
            replay.ledger_balance(path, candidate=1, loads=1, frames=10)
        self.assertEqual(replay.planned_inference_frames(829, 72), 3962)

    # --- C1返工 C1-5（AR1-6：逐帧共账与启动门）的具名回归 ----------------------------------------------

    def zeroed_ledger(self, **counters):
        ledger = json.loads(replay.LEDGER.read_text(encoding="utf-8"))
        ledger["counters"] = {k: 0 for k in ledger["counters"]}
        ledger["counters"]["candidates_started"] = 2
        ledger["counters"].update(counters)
        ledger["events"] = [{"at": "2026-10-10T00:00:00Z", "counter": "candidates_started", "amount": 2, "candidate": 2,
                             "note": "fixture"}] + [{"at": "2026-10-10T00:00:00Z", "counter": k, "amount": v, "candidate": 2, "note": "fixture"}
                                                    for k, v in counters.items() if k != "candidates_started" and v]
        path = self.root / "ledger.json"
        path.write_text(json.dumps(ledger), encoding="utf-8")
        return path, ledger

    def test_c1_5_counting_model_persists_each_submitted_frame_before_inference(self):
        """逐帧共账：每帧在交给模型**之前**落盘计入（崩溃不丢已提交帧、失败不返还），账上留 in_flight 事件直至结算；
        越过每候选上限的那一帧在推理前拒绝。修前 `CountingModel` 只在内存计数，整段返回后才记账，中途失败全丢。"""
        from tools.eng_capture import ledger as capture_ledger  # noqa: PLC0415

        path, _ledger = self.zeroed_ledger()
        calls = []

        class Model:
            def predict(self, source=None, **_kw):
                calls.append(source)
                if len(calls) == 3:
                    raise RuntimeError("crash inside inference")
                return [source]

        counter = capture_ledger.InflightCounter.open(path, "replay_inference_frames", candidate=2, note="fixture stage")
        model = replay.CountingModel(lambda _p: Model(), counter=counter)
        model.load(Path("weights.pt"))
        model.predict("a")
        model.predict("b")
        with self.assertRaises(RuntimeError):
            model.predict("c")
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["counters"]["replay_inference_frames"], 3)
        inflight = [e for e in on_disk["events"] if e.get("status") == "in_flight"]
        self.assertEqual((len(inflight), inflight[0]["amount"]), (1, 3))
        with self.assertRaises(replay.LaunchRefused):  # 未结算的 in_flight → 不推余额
            replay.ledger_balance(path, candidate=2, loads=1, frames=10)
        capture_ledger.settle_inflight(path, reason="crash recorded")
        self.assertTrue(all(replay.ledger_balance(path, candidate=2, loads=1, frames=10).values()))
        near_cap, _ = self.zeroed_ledger(replay_inference_frames=5499)
        counter = capture_ledger.InflightCounter.open(near_cap, "replay_inference_frames", candidate=2, note="cap")
        model = replay.CountingModel(lambda _p: Model(), counter=counter)
        model.load(Path("weights.pt"))
        calls.clear()
        model.predict("x")
        with self.assertRaises(capture_ledger.LedgerRefused):
            model.predict("y")  # 第 5,501 帧：推理前拒绝
        self.assertEqual(len(calls), 1)

    def test_c1_5_ledger_balance_refuses_unattributed_unknown_inconsistent(self):
        """启动门逐维拒绝：候选超上限/未开始（无归因）、零维度非 0、缺字段、UNKNOWN 用量、计数与事件不符、未结算
        in_flight → `LaunchRefused`（不抛 KeyError、不推余额）。修前只核加载/推理/磁盘五项，缺字段直接 KeyError。"""
        path, ledger = self.zeroed_ledger()
        self.assertTrue(all(replay.ledger_balance(path, candidate=2, loads=1, frames=3962).values()))
        mutations = {
            "candidate_over_cap": (lambda d: None, 4),
            "candidate_not_started": (lambda d: None, 3),
            "candidate_exhausted_older": (lambda d: None, 1),
            "zero_dimension_nonzero": (lambda d: (d["counters"].__setitem__("unity_play", 1), d["events"].append({"counter": "unity_play", "amount": 1, "candidate": 2})), 2),
            "missing_counter": (lambda d: d["counters"].pop("replay_yolo_loads"), 2),
            "unknown_amount": (lambda d: d["events"].append({"counter": "mini_new_disk_bytes", "amount": "UNKNOWN", "candidate": 2}), 2),
            "counters_disagree_with_events": (lambda d: d["counters"].__setitem__("replay_inference_frames", 7), 2),
            "unsettled_in_flight": (lambda d: d["events"].append({"counter": "replay_inference_frames", "amount": 0, "candidate": 2, "status": "in_flight"}), 2),
            "envelope_field_missing": (lambda d: d["envelope"].pop("replay_inference_frames_total"), 2),
        }
        for name, (mutate, candidate) in mutations.items():
            with self.subTest(name=name):
                document = json.loads(json.dumps(ledger))
                mutate(document)
                path.write_text(json.dumps(document), encoding="utf-8")
                with self.assertRaises(replay.LaunchRefused):
                    replay.ledger_balance(path, candidate=candidate, loads=1, frames=10)

    # --- R1返工 R1-2（AR1-6：STOP 收尾写盘照记磁盘账）与墙钟收尾判定的具名回归 ----------------------------------

    def test_r1_2_input_stop_records_output_disk_bytes(self):
        """R1-2：`formal_run.run` 走 S-A-INPUT 早退（准入核对不过，AC-17/18/19 `NOT_RUN`）时写出的 input-check.json 与
        replay-report.json 须按输出目录实测字节记 `mini_new_disk_bytes`（临时账本副本）。修前早退直接 `return 3`，
        账上无该磁盘事件。不加载模型、不推理（早退在权重身份核对与加载之前）。"""
        from types import SimpleNamespace  # noqa: PLC0415
        from unittest import mock  # noqa: PLC0415

        from tools.eng_capture import formal_run  # noqa: PLC0415

        path, _ledger = self.zeroed_ledger()
        output = self.root / "out"
        preconditions = {"click_script": {"clicks": []}, "click_script_sha256": "0" * 64, "roll_plan": {},
                         "roll_click_script": {"clicks": []}, "roll_click_script_sha256": "0" * 64}

        def loader(_path):
            raise AssertionError("S-A-INPUT must stop before any model load")

        with mock.patch.object(formal_run.replay, "LEDGER", path), \
                mock.patch.object(formal_run.replay, "check_input", lambda: {"ok": False, "problems": ["fixture: sha mismatch"]}):
            code = formal_run.run(SimpleNamespace(candidate=2, output=str(output)), preconditions=preconditions,
                                  model_loader=loader, decode=lambda p: None, frame_ids=[])
        self.assertEqual(code, 3)
        report = json.loads((output / "replay-report.json").read_text(encoding="utf-8"))
        self.assertEqual((report["stop"], report["AC-17"], report["AC-18"], report["AC-19"]), ("S-A-INPUT", "NOT_RUN", "NOT_RUN", "NOT_RUN"))
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        disk = [e for e in on_disk["events"] if e["counter"] == "mini_new_disk_bytes"]
        measured = formal_run.output_bytes(output)
        self.assertGreater(measured, 0)
        self.assertEqual([(e["amount"], e["candidate"]) for e in disk], [(measured, 2)])
        self.assertEqual(on_disk["counters"]["mini_new_disk_bytes"], measured)
        self.assertEqual(on_disk["counters"]["replay_yolo_loads"], 0)

    def test_r1_2_final_wall_clock_judged_before_report(self):
        """复核附注（AR1-6 每次回放 ≤ 30 min）：最后一次推理之后的评分/落盘阶段也受核——写报告前补一次墙钟判定；
        超限照写报告、记 S-A-BUDGET 偏差（不冒充在限内），未超限记 within_limit。"""
        from tools.eng_capture import formal_run  # noqa: PLC0415

        report = {}
        self.assertTrue(formal_run.final_wall_check(report, started=100.0, limit_s=1800.0, now=1899.0))
        self.assertEqual(report["wall_clock"], {"elapsed_s": 1799.0, "limit_s": 1800.0, "within_limit": True,
                                                "judged": "before_writing_report"})
        self.assertNotIn("stop", report)
        report = {"stop": "S-A-REPRO"}
        self.assertFalse(formal_run.final_wall_check(report, started=100.0, limit_s=1800.0, now=1900.5))
        self.assertEqual((report["wall_clock"]["within_limit"], report["stop"]), (False, "S-A-REPRO"))
        self.assertEqual(report["budget_deviation"], "S-A-BUDGET: replay wall clock 1800.5 s > 1800.0 s (judged before writing the report)")

    def test_run_refuses_without_fidelity_before_any_load(self):
        code = replay.main(["run", "--fidelity-confirmation", str(self.root / "missing.json"), "--click-script", str(self.root / "s.json"),
                            "--roll-click-script", str(self.root / "r.json"), "--candidate", "1"])
        self.assertEqual(code, 4)


@unittest.skipUnless(HAVE_LIBS and (PROJECT_ROOT / "outputs" / "eng-det" / "runs" / "run-1" / "weights" / "last.pt").is_file(),
                     "需要钉版库与本机权重文件（只核文件身份，不加载模型）")
class BaselinePackageTests(unittest.TestCase):
    def test_exported_baseline_tracker_constructs_with_spec_relative_files(self):
        """阶段A回放窄修：导出包的 `PROJECT_ROOT` = 导出根，规格里相对路径的权重/冻结文件须可解析（只读符号链接指回原件），
        否则基线臂在正式回放加载模型之后才崩（修前 `FileNotFoundError: det-assoc-v1 weights is missing`）。替身加载器，零模型。"""
        from tools.eng_capture import baseline_runner  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as tmp:
            root, identity = baseline_runner.prepare_baseline_package(Path(tmp) / "baseline-source")
            self.assertEqual(identity["equivalent"], "controller/ byte-identical")
            loaded = []
            for name in [m for m in sys.modules if m == baseline_runner.PACKAGE or m.startswith(baseline_runner.PACKAGE + ".")]:
                del sys.modules[name]
            modules = baseline_runner.load_baseline_modules(root)
            try:
                tracker = modules["det_assoc_tracker"].DetAssocTracker(
                    spec_path=replay.SPEC, device="cpu", model_loader=lambda p: loaded.append(p) or object(), mode="resident",
                    gmc_source="pose")
                self.assertIsNotNone(tracker)
                self.assertTrue(str(Path(modules["det_assoc_tracker"].__file__)).startswith(str(root)))
                for relative in ("outputs/eng-det/runs/run-1/weights/last.pt", "docs/evidence/P1-ENG-FAST-002-freeze.json"):
                    self.assertTrue((root / relative).is_symlink(), relative)
            finally:
                for name in [m for m in sys.modules if m == baseline_runner.PACKAGE or m.startswith(baseline_runner.PACKAGE + ".")]:
                    del sys.modules[name]

    def test_formal_run_hands_the_verified_weights_file_to_the_loader(self):
        """阶段A回放窄修：正式回放交给加载器的必须是规格所指、身份已核的权重文件（修前交的是规格 JSON，首次正式加载被
        ultralytics 拒绝）。替身加载器记录路径后抛出、账本写入打桩，零模型、不碰真实账本。"""
        from types import SimpleNamespace  # noqa: PLC0415
        from unittest import mock  # noqa: PLC0415

        from tools.eng_capture import formal_run  # noqa: PLC0415

        seen = []

        class Stop(Exception):
            pass

        def loader(path):
            seen.append(Path(path))
            raise Stop

        preconditions = {"click_script": {"clicks": []}, "click_script_sha256": "0" * 64, "roll_plan": {},
                         "roll_click_script": {"clicks": []}, "roll_click_script_sha256": "0" * 64}
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(formal_run.replay, "check_input", lambda: {"ok": True}):
            # 账本用同结构临时副本（C1-5 启动门与逐帧共账都写账本；测试绝不触碰真实账本）。
            ledger = json.loads(replay.LEDGER.read_text(encoding="utf-8"))
            ledger["counters"] = {k: 0 for k in ledger["counters"]}
            ledger["counters"]["candidates_started"] = 1
            ledger["events"] = [{"at": "2026-10-10T00:00:00Z", "counter": "candidates_started", "amount": 1, "candidate": 1, "note": "fixture"}]
            temporary_ledger = Path(tmp) / "ledger.json"
            temporary_ledger.write_text(json.dumps(ledger), encoding="utf-8")
            stack = mock.patch.object(formal_run.replay, "LEDGER", temporary_ledger)
            stack.start()
            self.addCleanup(stack.stop)
            arguments = SimpleNamespace(candidate=1, output=str(Path(tmp) / "out"))
            with self.assertRaises(Stop):
                formal_run.run(arguments, preconditions=preconditions, model_loader=loader, decode=lambda p: None,
                               frame_ids=[min(replay.admitted_frame_ids())] if ADMITTED_FRAMES.is_dir() else [])
            on_disk = json.loads(temporary_ledger.read_text(encoding="utf-8"))
            self.assertEqual(on_disk["counters"]["replay_yolo_loads"], 1)  # 尝试即记（加载失败不返还）
        spec = json.loads(replay.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(seen, [PROJECT_ROOT / spec["weights"]["path"]])
        self.assertEqual(seen[0].suffix, ".pt")


def _jpeg(path: Path, shade: int) -> None:
    from PIL import Image  # noqa: PLC0415

    Image.new("RGB", (640, 480), (shade % 256, 40, 90)).save(path, format="JPEG")


def _truth_inside():
    return {"truth_box_available": True, "geometrically_visible": True, "truth_box_x": 0.4, "truth_box_y": 0.4,
            "truth_box_width": 0.1, "truth_box_height": 0.1}


HAVE_PIL = importlib.util.find_spec("PIL") is not None


@unittest.skipUnless(HAVE_PIL, "需要 Pillow（.venv-yoloe）")
class RollPreregistrationTests(unittest.TestCase):
    """AC-28（IR-7）：六基固定规则、预登记计划、点击页登记、启动前缺点/错帧/sha 校验（零模型、零真值进选择输入）。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.frames = Path(self._tmp.name) / "frames"
        self.frames.mkdir()
        self.out = Path(self._tmp.name) / "out"

    def tearDown(self):
        self._tmp.cleanup()

    def make_frames(self, ids):
        for f in ids:
            _jpeg(replay.frame_paths(f, self.frames)[0], f)
            replay.frame_paths(f, self.frames)[1].write_text(json.dumps(dict(META, frame_id=f)), encoding="utf-8")

    def test_base_rule_contiguity_floor_index_and_exactly_six(self):
        truth = {f: _truth_inside() for f in range(60)}
        ids = list(range(60))
        eligible = list(range(8, 45))
        self.assertEqual(replay.score_roll_bases(truth, ids), [eligible[(i + 1) * len(eligible) // 7] for i in range(6)])
        gapped = [f for f in ids if f != 30]  # [k−8, k+15] 含 30 的 k 全不合格
        eligible = [k for k in range(8, 45) if not k - 8 <= 30 <= k + 15]
        self.assertEqual(replay.score_roll_bases(truth, gapped), [eligible[(i + 1) * len(eligible) // 7] for i in range(6)])
        outside = {**truth, 12: dict(_truth_inside(), truth_box_x=0.95)}  # [k−8,k] 有出画真值的 k 不合格
        self.assertNotIn(12, [k for k in replay.score_roll_bases(outside, ids)])
        self.make_frames(range(28))  # 合格 k = 8…12（n=5）→ 位次重复，不足六个互异
        with self.assertRaises(replay.RollBaseError):
            replay.roll_base_plan({f: _truth_inside() for f in range(28)}, list(range(28)), frames=self.frames)

    def registered(self, plan, **override):
        clicks = [{"base_k": b["base_k"], "frame_id": b["frame_id"], "x_px": 300.0, "y_px": 240.0, "image_sha256": b["image_sha256"]}
                  for b in plan["bases"]]
        document = {"schema_version": replay.ROLL_CLICK_SCHEMA, "registered_by": "user", "clicks": clicks, **override}
        path = self.out / "roll-click-script.json"
        self.out.mkdir(exist_ok=True)
        path.write_text(json.dumps(document), encoding="utf-8")
        return path, document

    def test_launch_validation_refuses_missing_wrong_frame_sha_and_out_of_frame(self):
        self.make_frames(range(60))
        plan = replay.roll_base_plan({f: _truth_inside() for f in range(60)}, list(range(60)), frames=self.frames)
        self.assertEqual([b["frame_id"] for b in plan["bases"]], [b["base_k"] - 1 for b in plan["bases"]])
        path, document = self.registered(plan)
        loaded, sha = replay.load_roll_click_script(path, plan, frames=self.frames)
        self.assertEqual((len(loaded["clicks"]), len(sha)), (6, 64))
        self.assertEqual(sorted(replay.roll_clicks_by_base(loaded)), [b["base_k"] for b in plan["bases"]])
        bad_cases = {
            "missing": lambda d: d["clicks"].pop(),
            "duplicate": lambda d: d["clicks"].__setitem__(1, dict(d["clicks"][0])),
            "wrong_frame": lambda d: d["clicks"][0].update(frame_id=d["clicks"][0]["base_k"]),
            "sha": lambda d: d["clicks"][2].update(image_sha256="0" * 64),
            "out_of_frame": lambda d: d["clicks"][3].update(x_px=640.0),
            "registrant": lambda d: d.update(registered_by=""),
        }
        for name, mutate in bad_cases.items():
            with self.subTest(name=name):
                doc = json.loads(json.dumps(document))
                mutate(doc)
                path.write_text(json.dumps(doc), encoding="utf-8")
                with self.assertRaises(replay.LaunchRefused):
                    replay.load_roll_click_script(path, plan, frames=self.frames)
        with self.assertRaises(replay.LaunchRefused):
            replay.load_roll_click_script(self.out / "absent.json", plan, frames=self.frames)
        _jpeg(replay.frame_paths(plan["bases"][0]["frame_id"], self.frames)[0], 999)  # 原帧被换 → 计划与剧本 sha 均不符
        path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(replay.LaunchRefused):
            replay.load_roll_click_script(path, plan, frames=self.frames)

    def test_register_page_writes_script_only_from_human_clicks(self):
        from tools.eng_capture import click_web  # noqa: PLC0415
        from tools.eng_loop2.operator_web import OpsLog  # noqa: PLC0415

        self.make_frames(range(60))
        plan = replay.roll_base_plan({f: _truth_inside() for f in range(60)}, list(range(60)), frames=self.frames)
        plan_path = Path(self._tmp.name) / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        app = click_web.RollRegisterApp(self.frames, plan_path, self.out, OpsLog(self.out / "log.jsonl"), registered_by="user",
                                        clock=lambda: 1.0)
        self.assertEqual(app.frame_ids, [b["frame_id"] for b in plan["bases"]])
        self.assertTrue(app.frame({"i": "0"})[0].startswith(b"\xff\xd8"))  # 原图字节原样（无叠框）
        for i, b in enumerate(plan["bases"]):
            data = replay.frame_paths(b["frame_id"], self.frames)[0].read_bytes()
            self.assertFalse(app.click({"frame_id": b["frame_id"], "image_sha256": "0" * 64, "x_px": 1.0, "y_px": 1.0})["ok"])
            reply = app.click({"frame_id": b["frame_id"], "image_sha256": click_web.sha256_bytes(data), "x_px": 100.0 + i, "y_px": 200.0})
            self.assertTrue(reply["ok"], reply)
            self.assertEqual(reply["script_written"], i == len(plan["bases"]) - 1)
        loaded, _sha = replay.load_roll_click_script(self.out / "roll-click-script.json", plan, frames=self.frames)
        self.assertEqual([c["x_px"] for c in loaded["clicks"]], [100.0 + i for i in range(6)])
        self.assertEqual(loaded["registered_by"], "user")
        _jpeg(replay.frame_paths(plan["bases"][0]["frame_id"], self.frames)[0], 999)
        with self.assertRaises(ValueError):  # 计划内原帧 sha 不符 → 拒绝启动登记页
            click_web.RollRegisterApp(self.frames, plan_path, self.out, OpsLog(self.out / "log.jsonl"), registered_by="user")
        with self.assertRaises(ValueError):
            click_web.RollRegisterApp(self.frames, plan_path, self.out, OpsLog(self.out / "log.jsonl"), registered_by="")


class RollSelectionInputTests(unittest.TestCase):
    """AC-28：两臂每基 12 种滚转复用同一预登记点；改变评分真值不改变送入两臂的选择输入。"""

    def run_roll(self, truth, roll_clicks):
        from unittest import mock  # noqa: PLC0415

        from tools.eng_capture import formal_run  # noqa: PLC0415

        seen = {"baseline": [], "new": []}

        def baseline(modules, frames, *, spec_path, model_loader, clicks):
            seen["baseline"].append(json.loads(json.dumps(clicks)))
            return [{"ok": False, "box_norm": None} for _ in frames]

        def new(frames, *, model_loader, params, config_sha256, clicks, **_kw):
            seen["new"].append(json.loads(json.dumps(clicks)))
            trace = replay.NewArmTrace()
            trace.frames = [{"observation": None, "observed_box_norm": None} for _ in frames]
            return trace

        frames = [replay.ReplayFrame(f, None, dict(META, frame_id=f), f"{f:064x}") for f in range(0, 60)]
        caches = {p: {"cache": {}, "key": lambda sha: ("k", sha)} for p in ("per_class", "unify_vehicle")}
        with mock.patch.object(formal_run.baseline_runner, "run_baseline_arm", baseline), \
                mock.patch.object(formal_run.replay, "run_new_arm", new), \
                mock.patch.object(formal_run.replay, "warp_image", lambda image, h: image):
            result = formal_run.run_roll(frames, caches, truth, tm.CaptureParams(), "0" * 64, None, None, roll_clicks=roll_clicks)
        return result, seen

    def test_truth_change_does_not_change_selection_inputs(self):
        roll_clicks = {20: {"frame_id": 19, "x_px": 111.0, "y_px": 222.0, "label": "roll_base_20"},
                       40: {"frame_id": 39, "x_px": 333.0, "y_px": 144.0, "label": "roll_base_40"}}
        truth = {f: _truth_inside() for f in range(60)}
        moved = {f: dict(_truth_inside(), truth_box_x=0.1 + 0.01 * (f % 7), truth_box_y=0.2) for f in range(60)}
        result_a, seen_a = self.run_roll(truth, roll_clicks)
        result_b, seen_b = self.run_roll(moved, roll_clicks)
        self.assertEqual((result_a["sequences"], result_a["inference_frames_per_arm"]), (24, 24 * replay.ROLL_FRAMES))
        self.assertEqual(seen_a, seen_b)  # 真值改变 → 选择输入逐字不变
        self.assertEqual(seen_a["baseline"], seen_a["new"])  # 两臂同点
        expected = [[{"frame_id": c["frame_id"], "x_px": c["x_px"], "y_px": c["y_px"], "label": c["label"]}]
                    for base, c in sorted(roll_clicks.items()) for _ in range(12)]
        self.assertEqual(seen_a["new"], expected)  # 每基 12 种滚转复用该点
        with self.assertRaises(ValueError):  # 点击不在原始热身末帧 k−1 → 拒绝
            self.run_roll(truth, {20: dict(roll_clicks[20], frame_id=20)})


@unittest.skipUnless(ADMITTED_FRAMES.is_dir(), "准入原件不在本机")
class AdmittedInputTests(unittest.TestCase):
    def test_check_input_matches_sums_and_alignment(self):
        report = replay.check_input()
        self.assertTrue(report["ok"], {k: v for k, v in report.items() if k != "listing"})
        self.assertEqual((report["frames"], report["files"]), (829, 1659))

    def test_roll_bases_deterministic(self):
        truth = replay.score_truth_rows()
        bases = replay.score_roll_bases(truth, replay.admitted_frame_ids())
        self.assertEqual(len(set(bases)), replay.ROLL_BASES)
        self.assertEqual(bases, replay.score_roll_bases(truth, replay.admitted_frame_ids()))
        plan = replay.roll_base_plan(truth, replay.admitted_frame_ids())
        self.assertEqual([b["base_k"] for b in plan["bases"]], bases)
        self.assertEqual([b["frame_id"] for b in plan["bases"]], [k - 1 for k in bases])


@unittest.skipUnless(HAVE_LIBS, "需要 .venv-yoloe（ultralytics 8.4.104 + lap）")
class NewArmEndToEndTests(unittest.TestCase):
    """新臂端到端：真实 DetAssocTracker（unify_vehicle + pose-center，钉版库 BoT-SORT）+ 缓存检测（零模型加载）。"""

    def test_click_binds_and_gap_is_predicted_then_regained(self):
        rows = {}
        frames = []
        for f in range(12):
            cx = 300.0 + 2 * f
            dets = [] if f in (7, 8) else [[cx - 30, 220.0, cx + 30, 260.0, 0.9, 1.0], [500.0, 100.0, 560.0, 140.0, 0.9, 0.0]]
            key = ("k", f)
            rows[key] = [[*d[:5], 0.0] for d in dets]  # 缓存的是策略后检测（cls 置 0）
            frames.append(replay.ReplayFrame(f, replay.CacheFrame(key), dict(META, frame_id=f), f"{f:064x}"))
        model = replay.CachedOrLiveModel(rows, None, replay.library_boxes)
        trace = replay.run_new_arm(frames, model_loader=lambda _p: model, params=tm.CaptureParams(), config_sha256="0" * 64,
                                   clicks=[{"frame_id": 4, "x_px": 308.0, "y_px": 240.0, "label": "red_car"}])
        by = {r["frame_id"]: r for r in trace.frames}
        self.assertEqual(by[4]["clicks"][0]["result"], "BOUND")
        self.assertEqual((by[5]["observation"], by[5]["continuity"]), (tm.OBSERVED, tm.SUPPORTED))
        self.assertEqual((by[7]["observation"], by[7]["effect"]["gimbal"]), (tm.PREDICTED, "predicted"))
        self.assertEqual(by[9]["observation"], tm.OBSERVED)
        self.assertEqual(model.hits, 12)

    def test_c1_3_click_frame_state_and_effect_are_post_commit_and_consistent(self):
        """C1-3 / RR-1：点击提交帧按 §3.3 ①→⑤ 先处理替换请求再授权——提交帧（= 本帧）的记录状态与效果同属新绑定
        （同帧、同版本、FOLLOW + 观测云台瞄新绑定框中心），不再有「提交前效果 + 提交后状态」的混记（不另存 `pre_click`）。
        修前本帧先授权（旧 episode 效果）再提交，记录被改写为提交后状态而效果仍属旧版本。"""
        rows, frames = {}, []
        for f in range(10):
            red = [300.0 + 2 * f - 30, 220.0, 300.0 + 2 * f + 30, 260.0, 0.9, 0.0]
            static = [500.0, 100.0, 560.0, 140.0, 0.9, 0.0]
            key = ("p", f)
            rows[key] = [red, static] if f < 3 or f >= 6 else [red]  # 静止车 3–5 帧消失 → 旧 episode 非 OBSERVED
            frames.append(replay.ReplayFrame(f, replay.CacheFrame(key), dict(META, frame_id=f), f"{f:064x}"))
        model = replay.CachedOrLiveModel(rows, None, replay.library_boxes)
        trace = replay.run_new_arm(frames, model_loader=lambda _p: model, params=tm.CaptureParams(), config_sha256="0" * 64,
                                   clicks=[{"frame_id": 1, "x_px": 530.0, "y_px": 120.0, "label": "static_car"},
                                           {"frame_id": 5, "x_px": 310.0, "y_px": 240.0, "label": "red_car"}])
        by = {r["frame_id"]: r for r in trace.frames}
        self.assertTrue(by[5]["clicks"][0]["accepted"])
        self.assertNotIn("pre_click", by[5])
        self.assertEqual((by[5]["observation"], by[5]["continuity"], by[5]["age"]), (tm.OBSERVED, tm.SUPPORTED, 0))
        self.assertEqual(by[5]["track_key"], by[6]["track_key"])
        self.assertNotEqual(by[4]["track_key"], by[5]["track_key"])
        effect = by[5]["effect"]
        self.assertEqual((effect["frame_id"], effect["version"]), (5, by[5]["version"]))
        self.assertEqual((effect["body"], effect["gimbal"]), ("FOLLOW", "observed"))
        self.assertAlmostEqual(effect["aim_center_px"][0], 310.0, delta=3.0)
        self.assertAlmostEqual(by[5]["observed_box_norm"][0] * replay.WIDTH, 280.0, delta=3.0)
        scored = replay.score_new_arm_window(trace, {f: TRUTH for f in range(10)}, tm.CaptureParams(), window=(5, 5))
        self.assertNotEqual(scored["rows"][0]["verdict"], "STATE_EFFECT_INCONSISTENT")

    def exclusion_runs(self, target_conf_in_gap, jump=0.0):
        rows, frames = {}, []
        for f in range(12):
            cx = 300.0 + 2 * f + (jump if f >= 5 else 0.0)
            conf = target_conf_in_gap if f in (5, 6) else 0.9
            dets = [[cx - 30, 220.0, cx + 30, 260.0, conf, 0.0], [500.0, 100.0, 560.0, 140.0, 0.9, 0.0]]
            key = ("x", f)
            rows[key] = dets
            frames.append(replay.ReplayFrame(f, replay.CacheFrame(key), dict(META, frame_id=f), f"{f:064x}"))
        clicks = [{"frame_id": 2, "x_px": 304.0, "y_px": 240.0, "label": "red_car"}]

        def run(exclusion=None):
            model = replay.CachedOrLiveModel(rows, None, replay.library_boxes)
            return replay.run_new_arm(frames, model_loader=lambda _p: model, params=tm.CaptureParams(), config_sha256="0" * 64,
                                      clicks=clicks, association_exclusion=exclusion)

        unperturbed = run(lambda f: set())
        old_key = {r["frame_id"]: r for r in unperturbed.frames}[5]["track_key"]
        self.assertIsNotNone(old_key)
        return unperturbed, run(lambda f: {old_key} if f in (5, 6) else set()), old_key

    def test_force_new_track_first_round_forms_new_active_key(self):
        """IR-8：首轮关联排除原键 → 原键 lost 且同帧 prior 在；目标检测由另一库键接走并成为活跃 tracked；注入退出后不再排除。
        （目标在缺口帧横移 12 px：未注入时原键照常匹配（IoU≈0.67），但新键与原键预测框 IoU < 0.85，不被库去重吞掉。）"""
        unperturbed, trace, old_key = self.exclusion_runs(0.9, jump=12.0)
        self.assertEqual({r["frame_id"]: r for r in unperturbed.frames}[5]["exclusion"]["rows"][str(old_key)]["state"], "tracked")
        by = {r["frame_id"]: r for r in trace.frames}
        for f in (5, 6):
            self.assertEqual(by[f]["exclusion"]["excluded"], [old_key])
            self.assertEqual(by[f]["exclusion"]["rows"][str(old_key)]["state"], "lost")
            self.assertTrue(by[f]["exclusion"]["excluded_prior_present"][str(old_key)])
        self.assertEqual(by[7]["exclusion"]["excluded"], [])
        report = replay.force_new_track_report(trace, unperturbed, start=5, frames=2)
        self.assertTrue(report["established"], report)
        self.assertTrue(report["exclusion_lifted_after"])
        self.assertNotIn(str(old_key), report["new_keys_activated"])
        self.assertEqual(by[5]["exclusion"]["rows"][report["new_keys"][0]]["state"], "unconfirmed")

    def test_force_new_track_swallowed_by_library_dedup_is_not_established(self):
        """IR-8：原键 lost 预测框与新检测 IoU > 0.85 时库内去重删掉较短命的新键 → 没形成新键，只记「注入未成立」。"""
        unperturbed, trace, old_key = self.exclusion_runs(0.9)
        report = replay.force_new_track_report(trace, unperturbed, start=5, frames=2)
        self.assertEqual((report["established"], report["status"], report["new_keys"]), (False, "INJECTION_NOT_ESTABLISHED", []))
        self.assertEqual([p["old_key_row"]["state"] for p in report["per_frame"]], ["lost", "lost"])

    def test_force_new_track_low_confidence_second_round_also_excluded(self):
        """IR-8：低置信度第二轮（库内直接 `iou_distance`）同样不得给原键量测更新。"""
        _unperturbed, trace, old_key = self.exclusion_runs(0.15)
        by = {r["frame_id"]: r for r in trace.frames}
        for f in (5, 6):
            self.assertEqual(by[f]["exclusion"]["rows"][str(old_key)]["state"], "lost", f)
            self.assertTrue(by[f]["exclusion"]["excluded_prior_present"][str(old_key)])
        self.assertEqual(by[7]["exclusion"]["rows"][str(old_key)]["state"], "tracked")  # 注入退出后原键可再匹配
        report = replay.force_new_track_report(trace, _unperturbed, start=5, frames=2)
        self.assertFalse(report["established"])  # 低分检测不建新轨：只记「注入未成立」
        self.assertEqual(report["status"], "INJECTION_NOT_ESTABLISHED")


class AnalyzePlayTests(unittest.TestCase):
    def test_click_latency_counts_every_click(self):
        clicks = [
            {"kind": "click_received", "click_id": "c-a", "latest_frame_id_at_click": 10, "frame_id": 10},
            {"kind": "submit_begin", "action": "click", "request_id": "a", "binding": {"click_id": "c-a"}},
            {"kind": "submit_result", "request_id": "a", "receipt": {"outcome": "APPLIED"}, "unknown": False},
            {"kind": "click_received", "click_id": "c-b", "latest_frame_id_at_click": 20, "frame_id": 20},
            {"kind": "submit_begin", "action": "click", "request_id": "b", "binding": {"click_id": "c-b"}},
            {"kind": "submit_result", "request_id": "b", "receipt": None, "unknown": True},
        ]
        journal = [{"kind": "binding_committed", "origin": "click", "frame_id": 11, "evidence": {"request_id": "a"}},
                   {"kind": "click_received", "request_id": "a", "page": {"head_at_consume": 11}}]
        result = analyze_play.click_latency(clicks, journal)
        self.assertEqual((result["denominator"], result["verdict"]), (2, "FAIL"))
        self.assertEqual((result["rows"][0]["e2e_frames"], result["rows"][0]["verdict"], result["rows"][1]["verdict"]), (1, "PASS", "FAIL"))

    def test_c1_2_prediction_windows_use_raw_detections_and_original_prior(self):
        """AC-24 按 AC-18 原检测定义（预复核关注项）：窗口后下一次真实观测 = T_repair 内首个与真值 IoU ≥ 0.5 的策略后检测，
        预测框 = 窗口原绑定键在该帧的同帧 prior；不要求该检测被接受为 OBSERVED。修前按 accepted OBSERVED 找下一观测。"""
        params = tm.CaptureParams()
        truth = {f: TRUTH for f in range(9, 20)}
        target_px = [0.4 * 640, 0.4 * 480, 0.5 * 640, 0.5 * 480]
        prior = [288.0, 216.0, 64.0, 48.0]
        per_frame = [{"frame_id": 10, "row": 6, "observation": tm.OBSERVED, "continuity": tm.SUPPORTED, "age": 0, "track_key": 1,
                      "observed_box_norm": list(TRUTH_BOX), "prior_xywh_px": prior, "raw_detections_px": [[*target_px, 0.9, 0.0]], "priors_xywh_px": {"1": prior}}]
        for f in (11, 12):
            per_frame.append({"frame_id": f, "row": 7, "observation": tm.PREDICTED, "continuity": tm.TENTATIVE, "age": f - 10, "track_key": 1,
                              "observed_box_norm": None, "prior_xywh_px": prior, "raw_detections_px": [], "priors_xywh_px": {"1": prior}})
        per_frame.append({"frame_id": 13, "row": 8, "observation": tm.PREDICTED, "continuity": tm.TENTATIVE, "age": 3, "track_key": 1,
                          "observed_box_norm": None, "prior_xywh_px": None, "raw_detections_px": [[*target_px, 0.9, 0.0]], "priors_xywh_px": {"1": prior}})
        receipts = [{"channel": "predicted_look_at", "outcome": "WRITTEN", "frame_id": f} for f in (11, 12)]
        result = analyze_play.score_prediction_windows(per_frame, receipts, truth, params)
        self.assertEqual((result["verdict"], result["rows"][0]["next_observation_frame"]), ("PASS", 13))

    def test_c1_3_per_frame_binding_follows_event_order_not_frame_label(self):
        """同帧状态/效果一致：某帧授权之后才发生、标该帧号的提交（会话在已授权历史头提交点击）不改写该帧的绑定键。
        修前按「提交帧号 ≤ 该帧」取键，把提交前已发出的效果记到新绑定名下。"""
        journal = [
            {"kind": "binding_committed", "frame_id": 10, "event_seq": 1, "new_track_key": 1},
            {"kind": "authorization", "frame_id": 20, "event_seq": 5, "inputs": {"continuity": "SUPPORTED", "observation": "OBSERVED", "age": 0}, "result": {"row": 6}},
            {"kind": "binding_committed", "frame_id": 20, "event_seq": 6, "new_track_key": 2},
            {"kind": "authorization", "frame_id": 21, "event_seq": 9, "inputs": {"continuity": "SUPPORTED", "observation": "OBSERVED", "age": 0}, "result": {"row": 6}},
        ]
        inputs = [{"kind": "frame", "frame_id": f, "history": {"tracks": [{"track_id": 1, "box_norm": [0.1, 0.1, 0.1, 0.1]}, {"track_id": 2, "box_norm": [0.5, 0.5, 0.1, 0.1]}],
                                                              "raw_detections": [], "prior_snapshots": [], "frame_id": f, "library_frame_id": f}} for f in (20, 21)]
        rows = {r["frame_id"]: r for r in analyze_play.per_frame_from_logs(journal, inputs)}
        self.assertEqual((rows[20]["track_key"], rows[21]["track_key"]), (1, 2))
        self.assertEqual(rows[20]["observed_box_norm"], [0.1, 0.1, 0.1, 0.1])

    def test_body_band_entry_hold_and_not_evaluable(self):
        formula = {"band_m": [10.0, 14.0], "v_max_mps": 4.0, "v_target_mps": 2.0, "t_lead_s": 2.5, "slack_s": 2.0, "not_evaluable_below_m": 10.0}
        truth = {f: {"target_world_x_m": 0.0, "target_world_z_m": 0.0, "body_world_x_m": max(12.0, 20.0 - f), "body_world_z_m": 0.0} for f in range(40)}
        result = analyze_play.score_body_band(truth, 0, 39, range(0, 40), formula)
        self.assertEqual((result["entry"], result["hold"]), ("PASS", "PASS"))
        self.assertEqual(result["N_s"], 3 + 4.5)
        near = {0: {"target_world_x_m": 0.0, "target_world_z_m": 0.0, "body_world_x_m": 5.0, "body_world_z_m": 0.0}}
        self.assertEqual(analyze_play.score_body_band(near, 0, None, [], formula)["verdict"], "NOT_EVALUABLE")

    def test_ir_c2_5_prediction_window_missing_prior_stays_in_denominator(self):
        """IR-C2-5 / AC-24（与 AC-18 同口径）：某窗口下一真实观测帧上原键无同帧 prior → 该窗 EVIDENCE_MISSING，仍在可评分母内，
        总判不为 PASS；无匹配检测才是 NOT_EVALUABLE。修前该窗记 NOT_EVALUABLE 并从分母去掉，另一窗 PASS 即总判 PASS。"""
        params = tm.CaptureParams()
        truth = {f: TRUTH for f in range(9, 40)}
        target_px = [0.4 * 640, 0.4 * 480, 0.5 * 640, 0.5 * 480]
        prior = [288.0, 216.0, 64.0, 48.0]

        def record(f, row, key=1, priors=None, dets=True):
            return {"frame_id": f, "row": row, "observation": tm.OBSERVED if row == 6 else tm.PREDICTED, "continuity": tm.SUPPORTED,
                    "age": 0, "track_key": key, "observed_box_norm": None, "prior_xywh_px": prior,
                    "raw_detections_px": [[*target_px, 0.9, 0.0]] if dets else [], "priors_xywh_px": {"1": prior} if priors is None else priors}

        per_frame = [record(10, 6), record(11, 7, dets=False), record(12, 6),
                     record(20, 6), record(21, 7, dets=False), record(22, 6, key=2, priors={"2": prior})]
        receipts = [{"channel": "predicted_look_at", "outcome": "WRITTEN", "frame_id": f} for f in (11, 21)]
        result = analyze_play.score_prediction_windows(per_frame, receipts, truth, params)
        self.assertEqual([r["verdict"] for r in result["rows"]], ["PASS", "EVIDENCE_MISSING"])
        self.assertEqual(result["rows"][1]["not_evaluable_reason"], "original_key_same_frame_prior_missing")
        self.assertEqual((result["verdict"], result["n_windows"], result["n_evaluable"]), ("EVIDENCE_MISSING", 2, 2))

    # --- R1返工 R1-3（AC-22/23/25 评分口径）的具名回归：夹具由生产点击页/提交器/捕获会话写出 ---------------------------

    @staticmethod
    def _harness_module():
        tests_dir = str(PROJECT_ROOT / "tests")
        if tests_dir not in sys.path:
            sys.path.insert(0, tests_dir)
        import test_capture_session  # noqa: PLC0415

        return test_capture_session

    def test_r1_3_refused_click_is_its_own_row_and_later_clicks_pair_by_request(self):
        """R1-3(a)(b)：点击页本地拒绝（上一提交在途 / 会话已封）只记 `refused`、不记 `submit_begin`；被拒点击须单独成行
        （分母含被拒），其后点击按自身 request_id 配对，且已绑定行记墙钟（描述）。夹具 = 生产 `ClickApp` + 真实 `Submitter`
        + 进程内发送到真实捕获会话写出的 click-web.jsonl 与会话日志。修前按数组位置配对：第 1 行（被拒）被记上第 2 次的
        request_id/提交帧，第 2 行无 request_id；`wall_s` 恒 None。"""
        import threading  # noqa: PLC0415
        import time  # noqa: PLC0415

        from tools.eng_capture import click_web  # noqa: PLC0415
        from tools.eng_loop2.operator_web import OpsLog, Submitter  # noqa: PLC0415

        harness = self._harness_module().CaptureHarness(self, self._harness_module().steady())
        harness.publish(3)
        log_path = harness.root / click_web.CLICK_LOG
        log = OpsLog(log_path)
        submitter = Submitter(click_web.InProcessSend(wait_s=5.0), click_web.ClickArgv(sys.executable, PROJECT_ROOT, harness.runtime), log)
        app = click_web.ClickApp(harness.runtime, "c1", submitter, log, clock=harness.clock.unix)
        data = (harness.runtime / "frames" / "frame_0000000002.jpg").read_bytes()
        body = {"frame_id": 2, "image_sha256": click_web.sha256_bytes(data), "x_px": 300.0, "y_px": 240.0}
        self.assertTrue(submitter.in_flight.acquire(blocking=False))  # 上一条提交仍在途
        try:
            self.assertTrue(app.click(dict(body))["refused"])
        finally:
            submitter.in_flight.release()
        result = {}
        thread = threading.Thread(target=lambda: result.update(app.click(dict(body))))
        thread.start()
        deadline = time.time() + 5.0
        while thread.is_alive() and time.time() < deadline:
            harness.tick(1)
            time.sleep(0.02)
        thread.join(1.0)
        self.assertTrue(result.get("ok"), result)
        submitter.seal("c1", "fixture_sealed")
        self.assertTrue(app.click(dict(body)).get("refused"))
        clicks = analyze_play.read_jsonl(log_path)
        journal = harness.journal()
        begins = [r for r in clicks if r["kind"] == "submit_begin"]
        self.assertEqual((len([r for r in clicks if r["kind"] == "click_received"]), len(begins)), (3, 1))
        latency = analyze_play.click_latency(clicks, journal)
        rows = latency["rows"]
        self.assertEqual(latency["denominator"], 3)
        self.assertEqual([r["request_id"] for r in rows], [None, begins[0]["request_id"], None])
        self.assertEqual([r["refused"] for r in rows], [True, False, True])
        committed = [e for e in journal if e["kind"] == "binding_committed" and e.get("origin") == "click"]
        self.assertEqual(len(committed), 1)
        self.assertEqual((rows[1]["commit_head"], rows[1]["bound"]), (committed[0]["frame_id"], True))
        self.assertEqual(rows[1]["e2e_frames"], committed[0]["frame_id"] - 2)
        self.assertAlmostEqual(rows[1]["wall_s"], committed[0]["at_unix_s"] - rows[1]["click_received_unix_s"])
        self.assertEqual([r["commit_head"] for r in (rows[0], rows[2])], [None, None])
        self.assertEqual([r["verdict"] for r in (rows[0], rows[2])], ["FAIL", "FAIL"])
        self.assertEqual(latency["verdict"], "FAIL")

    def _two_car_session(self):
        """生产捕获会话：S1 点静止车（键 1），S2 点红车（键 2），之后继续跟红车。"""
        module = self._harness_module()
        from controller.resident_core import TRACKED  # noqa: PLC0415

        harness = module.CaptureHarness(self, lambda f: [(1, TRACKED, module.box_px(300.0, 240.0)), (2, TRACKED, module.box_px(500.0, 300.0))])
        harness.publish(3)
        self.assertEqual(harness.click(300, 240, 1).get("outcome"), "APPLIED")
        harness.publish(5)
        self.assertEqual(harness.click(500, 300, harness.publisher.next_frame_id - 1).get("outcome"), "APPLIED")
        harness.publish(8)
        journal = harness.journal()
        inputs = analyze_play.read_jsonl(harness.session.session_dir / tm.INPUTS_FILE)
        commits = [e for e in journal if e["kind"] == "binding_committed" and e.get("origin") == "click"]
        self.assertEqual([c["new_track_key"] for c in commits], [1, 2])
        return harness, journal, inputs, commits[-1]["frame_id"]

    def test_r1_3_red_car_loop_counts_only_the_red_car_segment(self):
        """R1-3(d)：AC-23 只在红车段 [S2 提交帧, S4 首次点击帧) 内统计；S1 静止车阶段确认跟踪静止车的帧不算「被跟实例不是
        红车」。夹具 = 生产捕获会话的会话日志与 tm_inputs（`per_frame_from_logs`），真值 = 红车框。修前无段参数、全程统计。"""
        harness, journal, inputs, s2 = self._two_car_session()
        s2_commit = [e for e in journal if e["kind"] == "binding_committed" and e.get("origin") == "click"][-1]
        red = (470.0 / 640, 280.0 / 480, 60.0 / 640, 40.0 / 480)
        truth = {f: {"truth_box_available": True, "geometrically_visible": True, "truth_box_x": red[0], "truth_box_y": red[1],
                     "truth_box_width": red[2], "truth_box_height": red[3]} for f in range(harness.publisher.next_frame_id)}
        per_frame = analyze_play.per_frame_from_logs(journal, inputs)
        events = [r for r in journal if r.get("kind") in ("tm_event", "tm_transition", "binding_committed")]
        params = tm.CaptureParams()
        start = analyze_play.red_car_segment_start(per_frame, s2, s2_commit["event_seq"])
        # 本夹具点击在消费时 k 已处理：提交帧已发效果仍属旧绑定（IR-C2-1），红车段从下一授权帧起。
        self.assertEqual(start, s2 + 1)
        self.assertEqual({r["track_key"] for r in per_frame if r["frame_id"] >= start}, {2})
        whole = analyze_play.score_red_car_loop(per_frame, events, truth, params, segment=(None, None))
        self.assertGreater(whole["supported_frames_not_red_car_count"], 0)
        self.assertTrue(all(f < start for f in whole["supported_frames_not_red_car"]))
        loop = analyze_play.score_red_car_loop(per_frame, events, truth, params, segment=(start, None))
        self.assertEqual((loop["supported_frames_not_red_car_count"], loop["segment"]), (0, [start, None]))
        self.assertGreater(loop["frames_in_segment"], 0)
        self.assertTrue(loop["all_losses_on_time"])
        end = start + 3
        bounded = analyze_play.score_red_car_loop(per_frame, events, truth, params, segment=(start, end))
        self.assertEqual(bounded["frames_in_segment"], len([r for r in per_frame if start <= r["frame_id"] < end]))

    def test_r1_3_body_band_missing_truth_not_in_band_and_non_follow_counted(self):
        """R1-3(c)：AC-25 授权 FOLLOW 而缺真值的帧不计入带内（列为证据缺失，保持项不判 PASS），另输出合同要求的
        「非 FOLLOW 帧数」。FOLLOW/授权帧取自生产捕获会话日志。修前 `inside = len(follow) − len(outside)` 把缺真值帧算进
        带内（比例 1.0），且无非 FOLLOW 帧数。"""
        harness, journal, _inputs, s2 = self._two_car_session()
        authorizations = {r["frame_id"]: r for r in journal if r["kind"] == "authorization"}
        follow = sorted(f for f, r in authorizations.items() if r["result"]["body"] == tm.FOLLOW and f >= s2)
        non_follow = sorted(f for f, r in authorizations.items() if r["result"]["body"] != tm.FOLLOW and f >= s2)
        self.assertGreaterEqual(len(follow), 4)
        formula = {"band_m": [10.0, 14.0], "v_max_mps": 4.0, "v_target_mps": 2.0, "t_lead_s": 2.5, "slack_s": 2.0, "not_evaluable_below_m": 10.0}
        with_truth = set(follow[: len(follow) // 2]) | {s2}
        truth = {f: {"target_world_x_m": 0.0, "target_world_z_m": 0.0, "body_world_x_m": 12.0, "body_world_z_m": 0.0} for f in with_truth}
        result = analyze_play.score_body_band(truth, s2, None, follow, formula, authorized_frames=authorizations)
        missing = sorted(f for f in follow if f not in truth)
        self.assertTrue(missing)
        self.assertEqual(result["follow_frames_without_truth"], missing)
        self.assertEqual(result["outside_frames"], [])
        self.assertAlmostEqual(result["in_band_fraction"], (len(follow) - len(missing)) / len(follow))
        self.assertEqual((result["entry"], result["hold"], result["verdict"]), ("PASS", "EVIDENCE_MISSING", "EVIDENCE_MISSING"))
        self.assertEqual(result["non_follow_frames"], len([f for f in non_follow if f >= result["entered_frame"]]))
        full = {f: dict(truth[s2]) for f in set(follow) | {s2}}
        complete = analyze_play.score_body_band(full, s2, None, follow, formula, authorized_frames=authorizations)
        self.assertEqual((complete["hold"], complete["verdict"], complete["in_band_fraction"]), ("PASS", "PASS", 1.0))

    def test_velocity_only_on_observed_supported(self):
        receipts = [{"channel": "body_command", "outcome": "WRITTEN", "frame_id": 5}, {"channel": "body_command", "outcome": "WRITTEN", "frame_id": 6}]
        auth = {5: {"result": {"row": 6}}, 6: {"result": {"row": 7}}}
        self.assertEqual(analyze_play.velocity_only_on_supported(receipts, auth)["violations"], [6])


if __name__ == "__main__":
    unittest.main()
