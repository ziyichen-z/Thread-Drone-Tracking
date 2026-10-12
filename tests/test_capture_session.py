#!/usr/bin/env python3
"""P1-ENG-CAPTURE-001 AC-3/9/10/11/12/13（K1/K2/K3）：捕获模式会话（`--language off`）与兼容模式回归。

全部零模型：常驻插件替身 `FakeCaptureResident` 由生产 `ResidentCore` 记录历史（含原始检测、两阶段 KF 快照）；
帧包经生产 `FixtureFramePublisher` 写入临时 runtime；机身接冻结阈值规划器（与既有会话测试同一配置）。
兼容模式「与修改前代码逐条一致」：把本提案 `ACCEPTED` 裁定提交上的 `controller/` 由 git 导出为独立包，
同一脚本分别驱动新旧两套会话，比较指针、纪元、coasting、状态与原因序列。
"""

from __future__ import annotations

import importlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import language_bridge as bridge  # noqa: E402
from controller import target_manager as tm  # noqa: E402
from controller.language_loop import FixtureFramePublisher, LanguageSession, SessionConfig, sha256_bytes  # noqa: E402
from controller.resident_core import (  # noqa: E402
    KF_POSTERIOR,
    KF_PRIOR,
    LOST,
    TRACKED,
    UNCONFIRMED,
    RawDetection,
    ResidentCore,
    ResolverConfig,
    TrackRow,
    make_kf_snapshot,
)
from controller.trackers import TrackerResult  # noqa: E402
from tools.eng_capture.common import accepted_base_commit, export_controller  # noqa: E402

W, H = 640, 480
BODY_PLANNER_CONFIG = PROJECT_ROOT / "config" / "p1-m3-body-001.json"
BODY_SCENARIO_CONFIG = PROJECT_ROOT / "config" / "scenario.default.json"


class FakeClock:
    def __init__(self):
        self.unix_s = 1_800_000_000.0
        self.monotonic_s = 500.0

    def advance(self, seconds):
        self.unix_s += seconds
        self.monotonic_s += seconds

    def unix(self):
        return self.unix_s

    def monotonic(self):
        return self.monotonic_s


def box_px(cx, cy, w=60.0, h=40.0):
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


class FakeCaptureResident:
    """常驻插件替身：每帧按 `plan(frame_id)` → [(key, state, 像素 xyxy, prior 像素中心或 None, prior 协方差)]
    由生产 `ResidentCore.record` 写历史（原始检测、未确认行、matched_det_index、prior/post 快照）。"""

    name = "fake-capture"
    backend = "test"
    version = "1"
    mode = "resident"

    def __init__(self, plan):
        # IR-1：捕获入口显式启用增强历史视图（与生产 `CAPTURE_HISTORY_VIEW` 同值）。
        self.core = ResidentCore(128, ResolverConfig(), history_view="capture")
        self.plan = plan
        self.steps = []
        self.priors_available = True

    def step(self, image, frame_id, metadata):
        self.steps.append(frame_id)
        tracked, lost, unconfirmed, dets, priors, posts = [], [], [], [], [], []
        for item in self.plan(frame_id):
            key, state, xyxy = item[0], item[1], item[2]
            prior_center = item[3] if len(item) > 3 and item[3] is not None else None
            prior_cov = item[4] if len(item) > 4 else 25.0
            x1, y1, x2, y2 = xyxy
            w, h = x2 - x1, y2 - y1
            center = ((x1 + x2) / 2, (y1 + y2) / 2)
            index = -1
            if state != LOST:
                index = len(dets)
                dets.append(RawDetection(index, tuple(float(v) for v in xyxy), 0.9, 0))
            pc = prior_center or center
            priors.append(make_kf_snapshot(frame_id, len(self.steps), key, KF_PRIOR, (pc[0], pc[1], w, h), (0.0, 0.0), ((prior_cov, 0.0), (0.0, prior_cov))))
            post = make_kf_snapshot(frame_id, len(self.steps), key, KF_POSTERIOR if index >= 0 else KF_PRIOR, (center[0], center[1], w, h), (0.0, 0.0), ((prior_cov, 0.0), (0.0, prior_cov)))
            posts.append(post)
            row = TrackRow(key, (x1 / W, y1 / H, w / W, h / H), 0.9, 0, state, index, False, post, None)
            {TRACKED: tracked, LOST: lost, UNCONFIRMED: unconfirmed}[state].append(row)
        return self.core.record(
            frame_id, metadata, tracked, lost, [], len(self.steps),
            unconfirmed_rows=unconfirmed, raw_detections=dets, prior_snapshots=priors if self.priors_available else (),
            post_snapshots=posts, priors_available=self.priors_available,
        )

    def pointer_result(self, frame_id):
        return self.core.pointer_result(frame_id)

    def history(self, frame_id):
        return self.core.history(frame_id)

    def follow(self, track_id):
        self.core.follow(track_id)

    def pointer(self):
        return self.core.pointer()

    def manifest_identity(self):
        return {"name": self.name, "mode": "resident"}


class CaptureHarness:
    def __init__(self, case, plan, *, body=True, language=False, **overrides):
        directory = tempfile.TemporaryDirectory()
        case.addCleanup(directory.cleanup)
        self.case = case
        self.root = Path(directory.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        self.clock = FakeClock()
        self.publisher = FixtureFramePublisher(self.runtime, unix=self.clock.unix)
        self.tracker = FakeCaptureResident(plan)
        config = dict(
            session_id="c1",
            session_root=self.root / "sessions",
            runtime=self.runtime,
            receipt=None,
            adapter=None,
            tracker_name="det-assoc-v1",
            tracker_factory=lambda: self.tracker,
            resident=True,
            language=language,
            decode=lambda path: path.read_bytes(),
            monotonic=self.clock.monotonic,
            unix=self.clock.unix,
            planned_duration_s=100_000.0,
            pid=4242,
            is_alive=lambda pid: True,
            ground_plane_y_m=0.2 if body else 0.0,
            body_planner_config=BODY_PLANNER_CONFIG if body else None,
            body_scenario_config=BODY_SCENARIO_CONFIG if body else None,
        )
        config.update(overrides)
        self.session = LanguageSession(SessionConfig(**config))
        self.session.start()
        case.addCleanup(self.session.close)
        self.sequence = 0

    def publish(self, count=1, *, tick=True):
        frame_id = -1
        for _ in range(count):
            frame_id = self.publisher.publish(f"jpeg-{self.publisher.next_frame_id}".encode())
            if tick:
                self.tick()
        return frame_id

    def tick(self, count=1, advance_s=0.05):
        for _ in range(count):
            self.clock.advance(advance_s)
            self.session.tick()

    def request(self, action, ticks=1, **kwargs):
        self.sequence += 1
        request_id = kwargs.pop("request_id", f"r{self.sequence}")
        holder = bridge.acquire_writer_lock(self.runtime, request_id=request_id, pid=4243, now=self.clock.unix())
        bridge.write_request(self.runtime, session_id="c1", request_id=request_id, action=action, **kwargs)
        self.tick(ticks)
        bridge.release_writer_lock(self.runtime, request_id=request_id, pid=4243)
        return self.session.last_request or {}

    def session_tracker(self):
        return self.session.loop.tracker

    def session_loop_publisher(self):
        return self.session.loop.publisher

    def image_sha(self, frame_id):
        return sha256_bytes((self.runtime / "frames" / f"frame_{frame_id:010d}.jpg").read_bytes())

    def click(self, x, y, frame_id, *, sha=None, ticks=1):
        return self.request(
            "click", ticks=ticks,
            click={"x_px": float(x), "y_px": float(y), "frame_id": int(frame_id), "image_sha256": sha or self.image_sha(frame_id)},
        )

    def receipts(self):
        path = self.session.receipts_path
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.is_file() else []

    def journal(self, kind=None):
        rows = [json.loads(line) for line in self.session.journal_path.read_text(encoding="utf-8").splitlines()]
        return [r for r in rows if kind is None or r["kind"] == kind]

    def written(self, channel, frame_id=None):
        return [r for r in self.receipts() if r["channel"] == channel and r["outcome"] == "WRITTEN" and (frame_id is None or r["frame_id"] == frame_id)]

    def authorizations(self):
        return {r["frame_id"]: r for r in self.journal("authorization")}


def compat_harness(case):
    """兼容模式（语言开启）的常驻会话：K 收据由生产 `build_k_receipt` 生成，适配器为脚本替身。"""
    from controller.language_loop import build_k_receipt  # noqa: PLC0415
    from controller.language_selector import ScriptedAdapter  # noqa: PLC0415

    adapter = ScriptedAdapter([])
    receipt = build_k_receipt(hz=5.0, retained_frame_count=128, p95_s=2.0, host="test", backend="replay",
                              model_form="c2-adapter", model_identity=dict(adapter.identity), scenario_id="deterministic-loop-default")
    return CaptureHarness(case, steady(), language=True, receipt=receipt, adapter=adapter, body=False)


def steady(key=1, cx=300.0, cy=240.0):
    return lambda frame_id: [(key, TRACKED, box_px(cx, cy))]


class Script:
    """按帧号区间给计划：[(起始帧, 计划函数)]（取最后一个起始帧 ≤ frame_id 的计划）。"""

    def __init__(self, *segments):
        self.segments = sorted(segments, key=lambda item: item[0])

    def __call__(self, frame_id):
        plan = [p for start, p in self.segments if start <= frame_id][-1]
        return plan(frame_id) if callable(plan) else plan


def bound_harness(case, plan, **kwargs):
    """帧 0–2 稳定，点击 k=1（中心 300,240）→ 绑定 1 号。"""
    harness = CaptureHarness(case, plan, **kwargs)
    harness.publish(3)
    receipt = harness.click(300, 240, 1)
    case.assertEqual(receipt.get("outcome"), "APPLIED", receipt)
    case.assertEqual(harness.session.state, "TRACKING")
    return harness


class LanguageOffTests(unittest.TestCase):
    def test_language_off_reads_no_receipt_builds_no_adapter_or_worker(self):
        harness = CaptureHarness(self, steady())
        self.assertIsNone(harness.session.worker)
        self.assertIsNone(harness.session.config.adapter)
        self.assertEqual(harness.session.receipt.payload()["language"], "off")
        started = harness.journal("session_started")[0]
        self.assertEqual(started["language"], "off")
        with self.assertRaises(Exception):
            CaptureHarness(self, steady(), receipt=object())

    def test_language_actions_rejected_language_disabled(self):
        harness = bound_harness(self, steady())
        for action, kwargs in (
            ("ask", {"instruction": bridge.parse_instruction("the bus")}),
            ("respecify", {}),
            ("verify", {}),
            ("confirm", {"candidate_index": 0, "token": "t"}),
        ):
            with self.subTest(action=action):
                state = harness.session.state
                receipt = harness.request(action, **kwargs)
                self.assertEqual((receipt["outcome"], harness.session.state), ("REQUEST_INVALID", state))
                detail = [r for r in harness.journal("receipt") if r["receipt"]["request_id"] == receipt["request_id"]][0]["detail"]
                self.assertEqual(detail, "language_disabled")

    def test_language_worker_class_has_no_diff(self):
        base = accepted_base_commit()
        if base is None:
            self.skipTest("git history unavailable")
        source = subprocess.run(["git", "show", f"{base}:controller/language_loop.py"], cwd=PROJECT_ROOT,
                                capture_output=True, text=True, check=True).stdout
        import ast  # noqa: PLC0415

        def worker_source(text):
            tree = ast.parse(text)
            node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "LanguageWorker")
            return ast.get_source_segment(text, node)

        current = (PROJECT_ROOT / "controller" / "language_loop.py").read_text(encoding="utf-8")
        self.assertEqual(worker_source(current), worker_source(source))


class PredictionTests(unittest.TestCase):
    def lost_plan(self, lost_from, *, recover_at=None, extra=None, prior_cov=25.0):
        def plan(frame_id):
            if frame_id < lost_from or (recover_at is not None and frame_id >= recover_at):
                rows = [(1, TRACKED, box_px(300, 240))]
            else:
                rows = [(1, LOST, box_px(300, 240), None, prior_cov)]
            return rows + list(extra(frame_id) if extra else [])
        return plan

    def test_prediction_window_look_at_and_explicit_hold(self):
        harness = bound_harness(self, self.lost_plan(5))
        harness.publish(2)  # 3, 4 观测
        observed_frame = 4
        self.assertTrue(harness.written("look_at", observed_frame))
        harness.publish(6)  # 5..10：age 1..6
        auth = harness.authorizations()
        for frame_id in range(5, 9):  # age 1..4 = 行 7
            self.assertEqual(auth[frame_id]["result"]["row"], 7, frame_id)
            self.assertTrue(harness.written("predicted_look_at", frame_id), frame_id)
            self.assertTrue([r for r in harness.receipts() if r["channel"] == "body_safety_hold" and r["outcome"] == "WRITTEN"])
        for frame_id in (9, 10):  # age 5 = T_repair（BROKEN）、6
            self.assertNotEqual(auth[frame_id]["result"]["gimbal"], "predicted")
            self.assertFalse(harness.written("predicted_look_at", frame_id))
        # 预测 look_at 指向内部预测中心的 P_center（经 servo_clamp；此处无限速触发）。
        expected, _reason = tm.center_aim_point((300.0, 240.0), harness.tracker.core.history(5), 0.2 + 0.775, 400.0)
        predicted = harness.written("predicted_look_at", 5)[0]["detail"]["point_world_m"]
        for got, want in zip(predicted, expected):
            self.assertAlmostEqual(got, want, places=6)
        velocity = [r for r in harness.receipts() if r["channel"] == "body_command" and r["outcome"] == "WRITTEN"]
        for receipt in velocity:
            self.assertEqual(auth[receipt["frame_id"]]["result"]["row"], 6)
        # IR-9：预测云台收据走单列通道（闭集末尾追加），不混入观测 look_at。
        from controller.gated_publisher import RECEIPT_CHANNELS  # noqa: PLC0415

        self.assertEqual(RECEIPT_CHANNELS[-1], "predicted_look_at")
        self.assertTrue({r["channel"] for r in harness.receipts()} <= set(RECEIPT_CHANNELS))
        self.assertFalse([r for r in harness.written("look_at") if 5 <= r["frame_id"] <= 8])

    def test_counterexamples_have_no_predicted_look_at(self):
        cases = {
            "early_recovery": dict(plan=self.lost_plan(5, recover_at=6), frames=[5, 6]),
            "covariance_exceeds": dict(plan=self.lost_plan(5, prior_cov=4000.0), frames=[5, 6]),
        }
        for name, spec in cases.items():
            with self.subTest(name=name):
                harness = bound_harness(self, spec["plan"])
                harness.publish(2)
                harness.publish(2)
                auth = harness.authorizations()
                if name == "early_recovery":
                    self.assertTrue(harness.written("predicted_look_at", 5))
                    self.assertFalse(harness.written("predicted_look_at", 6))
                    self.assertEqual(auth[6]["result"]["row"], 6)
                else:
                    for frame_id in spec["frames"]:
                        self.assertFalse(harness.written("predicted_look_at", frame_id))
                        self.assertEqual(auth[frame_id]["inputs"]["covariance"], "exceeds")

    def test_disputed_and_kf_invalid_and_geometry_rejected(self):
        disputed = bound_harness(self, self.lost_plan(5, extra=lambda f: [(7, UNCONFIRMED, box_px(301, 240)), (8, UNCONFIRMED, box_px(299, 240))] if f >= 5 else []))
        disputed.publish(3)
        auth = disputed.authorizations()
        self.assertEqual(disputed.session.state, "SUSPECTED")
        self.assertFalse([f for f in range(5, 6) if disputed.written("predicted_look_at", f) and auth[f]["result"]["row"] != 7])
        kf = bound_harness(self, self.lost_plan(5))
        kf.publish(2)
        kf.tracker.priors_available = False
        original_plan = kf.tracker.plan

        def broken_post(frame_id):
            return [(1, LOST, box_px(300, 240), None, float("nan"))] if frame_id >= 5 else original_plan(frame_id)

        kf.tracker.plan = broken_post
        kf.publish(1)
        self.assertFalse(kf.written("predicted_look_at", 5))
        self.assertEqual(kf.authorizations()[5]["inputs"]["covariance"], "kf_invalid")
        geo = bound_harness(self, self.lost_plan(5))
        geo.publish(2)
        geo.publisher.camera_rotation_xyzw = (0.0, 0.0, 0.0, 1.0)  # 前向水平：中心射线不与平面相交
        geo.publish(1)
        self.assertFalse(geo.written("predicted_look_at", 5))
        self.assertEqual(geo.authorizations()[5]["result"]["row"], 5)

    def test_c1_1_missing_prior_with_valid_post_has_no_gimbal_and_holds(self):
        """C1-1（会话层）：原键 lost、本帧 prior 未提供但 post 有效 → 云台不发（无预测/观测 look_at WRITTEN）、
        授权 HOLD/不发、无速度命令；修前预测中心取 post，行 7 照发 `predicted_look_at`。"""
        harness = bound_harness(self, self.lost_plan(5))
        harness.publish(2)
        harness.tracker.priors_available = False
        harness.publish(1)
        auth = harness.authorizations()[5]
        self.assertEqual((auth["result"]["body"], auth["result"]["gimbal"]), ("HOLD", "none"))
        self.assertFalse(harness.written("predicted_look_at", 5))
        self.assertFalse(harness.written("look_at", 5))
        self.assertFalse(harness.written("body_command", 5))

    def test_observed_frames_aim_center_and_estimator_uses_bottom_center(self):
        harness = bound_harness(self, steady())
        loop = harness.session.loop
        calls = []
        original = loop._body_step

        def spy(bundle, result):
            calls.append((bundle.frame_id, result.ok, result.box_norm))
            return original(bundle, result)

        loop._body_step = spy
        harness.publish(1)
        frame_id = harness.publisher.next_frame_id - 1
        written = harness.written("look_at", frame_id)[0]
        entry = harness.tracker.core.history(frame_id)
        expected, _ = tm.center_aim_point((300.0, 240.0), entry, 0.2 + 0.775, 400.0)
        point = json.loads((harness.runtime / "gimbal_command.json").read_text(encoding="utf-8"))
        self.assertTrue(written)
        self.assertEqual(calls[-1][0], frame_id)
        self.assertTrue(calls[-1][1])
        x, y, w, h = calls[-1][2]
        self.assertAlmostEqual(x * W, 270.0, places=4)
        self.assertAlmostEqual((y + h) * H, 260.0, places=4)  # 机身估计器量测仍取框底中点（框原样交 `_body_step`）
        self.assertIsNotNone(expected)


class ReportTests(unittest.TestCase):
    def test_boundary_columns(self):
        harness = bound_harness(self, PredictionTests().lost_plan(5))
        harness.publish(2)
        seen = []
        for _ in range(6):
            harness.publish(1)
            seen.append((harness.session.state, harness.session.reason))
        self.assertEqual(
            seen,
            [("TRACKING", "predicting"), ("TRACKING", "predicting"), ("TRACKING", "no_new_observation"),
             ("TRACKING", "no_new_observation"), ("SUSPECTED", "continuity_broken"), ("SUSPECTED", "continuity_broken")],
        )
        reports = [r for r in harness.journal("tm_event") if r.get("type") == "report"]
        self.assertEqual([r["frame_id"] for r in reports], [7])
        # FASTFIX §3.2/§3.3 在其后末尾再追加 5 个：CAPTURE 的 11 个位次不变（[26:37]）。
        self.assertIn("continuity_broken", bridge.STATE_REASONS[26:37])

    def test_wall_delay_does_not_change_frame_deadlines(self):
        results = []
        for advance in (0.05, 2.5):
            harness = bound_harness(self, PredictionTests().lost_plan(5))
            harness.publish(2)
            states = []
            for _ in range(6):
                harness.publisher.publish(f"jpeg-{harness.publisher.next_frame_id}".encode())
                harness.tick(1, advance_s=advance)
                states.append((harness.session.state, harness.session.reason))
            results.append(states)
        self.assertEqual(results[0], results[1])

    def test_backlog_frames_emit_no_commands(self):
        harness = bound_harness(self, steady())
        before = len(harness.receipts())
        for _ in range(2):
            harness.publish(1, tick=False)
        harness.tick(1)
        new = harness.receipts()[before:]
        frames = {r["frame_id"] for r in new if r["frame_id"] is not None}
        self.assertEqual(frames, {harness.publisher.next_frame_id - 1})
        auth = harness.authorizations()
        self.assertNotIn(harness.publisher.next_frame_id - 2, auth)


class StopTests(unittest.TestCase):
    def test_stop_writes_hold_first_and_drops_late_effects(self):
        harness = bound_harness(self, steady())
        harness.publish(2)
        manager = harness.session.target_manager
        entry = harness.tracker.core.history(harness.publisher.next_frame_id - 1)
        effect = manager.on_frame(entry, newest=False)  # 只为构造一个 FrameEffect 的对照
        self.assertIsNone(effect.effect)
        last = manager._effects(entry, True)
        self.assertTrue(manager.effect_current(last, frame_id=entry.frame_id))
        before = len(harness.receipts())
        harness.request("stop")
        self.assertEqual(harness.session.state, "TERMINAL")
        self.assertFalse(manager.effect_current(last, frame_id=entry.frame_id))
        new = harness.receipts()[before:]
        self.assertTrue(new)
        self.assertEqual((new[0]["channel"], new[0]["outcome"], new[0]["detail"]["reason"]), ("body_safety_hold", "WRITTEN", "operator_stop"))
        self.assertFalse([r for r in new if r["channel"] == "body_command"])
        harness.publish(2)
        self.assertEqual(len(harness.receipts()), len(new) + before)

    def test_no_new_frames_goes_stale_and_holds(self):
        harness = bound_harness(self, steady())
        harness.publish(1)
        before = len(harness.receipts())
        harness.tick(1, advance_s=3.5)
        self.assertEqual((harness.session.state, harness.session.reason), ("REINIT_REQUIRED", "frame_stall"))
        new = harness.receipts()[before:]
        self.assertEqual([(r["channel"], r["detail"].get("reason")) for r in new], [("body_safety_hold", "frame_stall")])
        watchdog = [r for r in harness.journal("tm_event") if r.get("type") == "watchdog"]
        self.assertEqual(watchdog[-1]["reason"], "stale")


class ClickTests(unittest.TestCase):
    def test_click_rejections_and_results(self):
        plan = lambda f: [(1, TRACKED, box_px(300, 240)), (2, TRACKED, box_px(330, 240)), (3, TRACKED, box_px(500, 100))]
        harness = CaptureHarness(self, plan)
        harness.publish(3)
        self.assertEqual(harness.click(300, 240, 1, sha="0" * 64)["outcome"], "REQUEST_INVALID")
        details = lambda: [r["detail"] for r in harness.journal("receipt")]
        self.assertEqual(details()[-1], "image_mismatch")
        harness.publisher.publish(b"later", frame_id=200)
        harness.publisher.publish_pointer(2)
        self.assertEqual(harness.click(10, 10, 200)["outcome"], "APPLIED")
        self.assertEqual(details()[-1], "FRAME_NOT_IN_HISTORY")
        self.assertEqual(harness.click(10, 470, 1)["outcome"], "APPLIED")
        self.assertEqual(details()[-1], "NO_TRACK_AT_K")
        self.assertEqual(harness.click(315, 240, 1)["outcome"], "APPLIED")  # 1、2 号都包含，距离比 1 < ρ
        self.assertEqual(details()[-1], "AMBIGUOUS")
        self.assertEqual(harness.session.state, "IDLE")
        self.assertEqual(harness.click(500, 100, 1)["outcome"], "APPLIED")
        self.assertEqual((harness.session.state, harness.session.target_manager.track_key), ("TRACKING", 3))
        self.assertIsNone(details()[-1])

    def test_reselect_new_episode_and_old_closed_after_success(self):
        plan = lambda f: [(1, TRACKED, box_px(300, 240)), (3, TRACKED, box_px(500, 100))]
        harness = bound_harness(self, plan)
        first = harness.session.track_id
        harness.publish(1)
        harness.click(500, 100, harness.publisher.next_frame_id - 1)
        manager = harness.session.target_manager
        self.assertEqual((manager.binding.track_key, manager.binding.relation, manager.episode_seq), (3, "USER_RESELECT", 2))
        self.assertEqual(harness.session.retired_track_ids[-1]["track_id"], first)
        self.assertEqual(harness.session.retired_track_ids[-1]["retired_reason"], "superseded_by_click")
        closed = [r for r in harness.journal("tm_event") if r.get("type") == "episode_closed"]
        self.assertEqual(closed[-1]["reason"], "superseded_by_click")

    def test_chain_break_rejected_and_compat_click_unavailable(self):
        def plan(frame_id):
            rows = [(1, TRACKED, box_px(300, 240))]
            if frame_id != 2:
                rows.append((5, TRACKED, box_px(500, 100)))
            return rows

        harness = bound_harness(self, plan)
        harness.publish(1)
        harness.click(500, 100, 1)
        self.assertEqual(harness.session.target_manager.track_key, 1)  # 换目标被拒继续跟旧目标
        self.assertEqual([r["detail"] for r in harness.journal("receipt")][-1], "evidence_chain_broken@2")
        compat = compat_harness(self)
        compat.publish(2)
        receipt = compat.click(300, 240, 1)
        self.assertEqual(receipt["outcome"], "REQUEST_INVALID")
        self.assertEqual([r["detail"] for r in compat.journal("receipt")][-1], "click_unavailable")
        self.assertFalse(compat.session.capture)

    def test_acceptance_subsegment_and_zero_adapter_calls(self):
        harness = CaptureHarness(self, steady())
        harness.publish(3)
        harness.publisher.publish(b"unprocessed-3")  # 页面显示帧 3、会话尚未处理
        harness.click(300, 240, 3)
        received = harness.journal("click_received")[-1]
        committed = harness.journal("binding_committed")[-1]
        self.assertLessEqual(committed["frame_id"] - received["page"]["head_at_consume"], 1)
        self.assertIsNone(harness.session.worker)
        self.assertFalse(harness.journal("query_submitted"))

    def test_c1_3_catch_up_click_is_applied_before_that_frame_is_authorized(self):
        """C1-3 / RR-1（§3.3 ①→⑤）：点击消费时页面帧 k 尚未处理 → 追平处理 k 时先处理替换请求再授权：k 帧授权与
        效果属于新绑定（同帧状态、episode、版本一致），观测与云台以新纪元发出。修前追平先对 k 授权（无任务，行 1），
        提交后才改状态，k 帧的状态与发出的命令不一致。"""
        harness = CaptureHarness(self, steady())
        harness.publish(3)
        frame_id = harness.publisher.publish(b"unprocessed-3")
        harness.click(300, 240, frame_id)
        manager = harness.session.target_manager
        committed = harness.journal("binding_committed")[-1]
        self.assertEqual(committed["frame_id"], frame_id)
        auth = [r for r in harness.journal("authorization") if r["frame_id"] == frame_id]
        self.assertEqual(len(auth), 1)
        self.assertEqual((auth[0]["result"]["row"], auth[0]["result"]["body"], auth[0]["result"]["gimbal"]), (6, "FOLLOW", "observed"))
        self.assertGreater(auth[0]["event_seq"], committed["event_seq"])
        self.assertTrue(harness.written("look_at", frame_id))
        observation = json.loads((harness.runtime / "tracking_observation.json").read_text(encoding="utf-8"))
        self.assertEqual((observation["observation"]["frame_id"], observation["observation"]["track_id"]),
                         (frame_id, harness.session.track_id))
        self.assertEqual((harness.session.state, manager.binding.bound_frame_id), ("TRACKING", frame_id))


class BridgeIsolationTests(unittest.TestCase):
    def test_bridge_files_carry_no_internal_fields(self):
        harness = bound_harness(self, PredictionTests().lost_plan(5))
        harness.publish(4)
        for name in ("tracking_observation.json", "tracker_state.json", "gimbal_command.json"):
            text = (harness.runtime / name).read_text(encoding="utf-8")
            for forbidden in ("out_of_frame", "pos_cov_px2", "xywh_px", "box_px", "prior_snapshots", "kf"):
                self.assertNotIn(f'"{forbidden}"', text, (name, forbidden))
        observation = json.loads((harness.runtime / "tracking_observation.json").read_text(encoding="utf-8"))
        self.assertLessEqual(observation["observation"]["frame_id"], 4)  # 预测帧不发观测


# --- AC-13 兼容模式：与修改前代码在同一脚本输入上逐条一致 --------------------------------------------


BOX_A = (0.3, 0.3, 0.2, 0.2)
BOX_B = (0.01, 0.01, 0.07, 0.07)


class _LibraryLost:
    """库 lost 轨迹替身（`rows_from_library` 读 `.track_id/.xyxy/.score/.cls`）。"""

    def __init__(self, track_id, xyxy):
        self.track_id, self.xyxy, self.score, self.cls = track_id, list(xyxy), 0.8, 0.0


MODULES = ("language_loop", "language_bridge", "resident_core", "trackers", "reanchor", "language_selector")


def compat_script(pkg_root: Path | None, scenario: str):
    """在给定 `controller` 包（None = 当前工作树）上跑兼容模式脚本；返回逐步序列。"""
    if pkg_root is None:
        names = {k: importlib.import_module(f"controller.{k}") for k in MODULES}
    else:
        sys.path.insert(0, str(pkg_root))
        try:
            names = {k: importlib.import_module(f"controller_base.{k}") for k in MODULES}
        finally:
            sys.path.remove(str(pkg_root))
    ll, br, rc, tr, ra, ls = (names[k] for k in MODULES)

    class Fake:
        name, backend, version, mode = "fake-resident", "test", "1", "resident"

        def __init__(self):
            self.core = rc.ResidentCore(128, rc.ResolverConfig(coasting_limit=3))
            self.tracked = {1: BOX_A}
            self.lost = {}
            self.library_lost = {}
            self.removed = []

        def step(self, image, frame_id, metadata):
            tracked = [rc.TrackRow(i, b, 0.9, 0, "tracked") for i, b in sorted(self.tracked.items())]
            lost = [rc.TrackRow(i, b, 0.8, 0, "lost") for i, b in sorted(self.lost.items())]
            if self.library_lost:
                # IR-1：库形 lost 轨迹（像素 xyxy，可出画/退化）经生产 `rows_from_library` 转行，新旧代码各用自己的实现。
                lost = lost + rc.rows_from_library([], [_LibraryLost(i, xyxy) for i, xyxy in sorted(self.library_lost.items())], 640, 480)[1]
            removed, self.removed = list(self.removed), []
            return self.core.record(frame_id, metadata, tracked, lost, removed, frame_id + 1)

        def runner(self):
            def run(k, box, h):
                return ra.ReplayResult("RESEED_READY", None, k, h, h - k, 1.0, tr.TrackerResult((0.9, 0.9, 0.05, 0.05), True, 0.9, "tracker"))
            return run

        def designate(self, box, k):
            return self.core.designate(box, k, self.runner())

        def resolve_designation(self, box, k, designation_id):
            return self.core.resolve_designation(box, k, self.runner(), designation_id)

        def pointer_result(self, frame_id):
            return self.core.pointer_result(frame_id)

        def history(self, frame_id):
            return self.core.history(frame_id)

        def follow(self, track_id):
            self.core.follow(track_id)

        def pointer(self):
            return self.core.pointer()

        def manifest_identity(self):
            return {"name": self.name, "mode": "resident"}

    def Adapter(texts):
        return ls.ScriptedAdapter([
            ls.RawSelection(raw_output=text, finish_reason="stop", gen_tokens=30, latency_ms=800.0,
                            prompt_sha256="p" * 64, model_id="m" * 64)
            for text in texts
        ])

    responses = {
        "bound": ['{"status": "unique", "bbox_2d": [300, 300, 500, 500]}', '{"status": "unique", "bbox_2d": [10, 10, 80, 80]}'],
        "coasting": ['{"status": "unique", "bbox_2d": [10, 10, 80, 80]}'],
        "failure_then_success": ['{"status": "unique", "bbox_2d": [600, 600, 700, 700]}', '{"status": "unique", "bbox_2d": [300, 300, 500, 500]}'],
        "acquire": ['{"status": "unique", "bbox_2d": [300, 300, 500, 500]}'],
        "lost_out_of_frame": ['{"status": "unique", "bbox_2d": [10, 10, 80, 80]}'],
        "lost_degenerate": ['{"status": "unique", "bbox_2d": [10, 10, 80, 80]}'],
        "coasting_out_of_frame": ['{"status": "unique", "bbox_2d": [10, 10, 80, 80]}'],
    }[scenario]
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    clock = FakeClock()
    runtime = root / "runtime"
    runtime.mkdir()
    publisher = ll.FixtureFramePublisher(runtime, unix=clock.unix)
    fake = Fake()
    adapter = Adapter(responses)
    receipt = ll.build_k_receipt(hz=5.0, retained_frame_count=128, p95_s=2.0, host="test", backend="replay",
                                 model_form="c2-adapter", model_identity=dict(adapter.identity), scenario_id="deterministic-loop-default")
    session = ll.LanguageSession(ll.SessionConfig(
        session_id="s1", session_root=root / "sessions", runtime=runtime, receipt=receipt, adapter=adapter,
        tracker_name="fake-resident", tracker_factory=lambda: fake, resident=True, decode=lambda p: p.read_bytes(),
        preview=lambda source, destination, candidates, tracker_box=None: (destination.parent.mkdir(parents=True, exist_ok=True), destination.write_bytes(b"png"), destination)[2],
        worker_spawn=ll.inline_spawn, monotonic=clock.monotonic, unix=clock.unix, planned_duration_s=100_000.0,
        pid=4242, is_alive=lambda pid: True,
    ))
    session.start()
    sequence = []
    counter = [0]

    def snap(label):
        coasting = fake.core._coasting
        designation = session.designation or {}
        sequence.append({
            "label": label, "state": session.state, "reason": session.reason, "track_id": session.track_id,
            "pointer": fake.core.pointer(), "coasting": None if coasting is None else dict(coasting),
            "designation_id": designation.get("designation_id"), "result": designation.get("result"),
            "next_designation_id": fake.core._next_designation_id, "segment_index": session.segment_index,
            "retired": [dict(r) for r in session.retired_track_ids],
            "suspect": [getattr(session, "suspect_kind", None), getattr(session, "suspect_id", None), getattr(session, "suspect_reason", None)],
        })

    def tick(n=1):
        for _ in range(n):
            clock.advance(0.05)
            session.tick()

    def publish(n=1):
        for _ in range(n):
            publisher.publish(f"jpeg-{publisher.next_frame_id}".encode())
            tick()

    def request(action, **kwargs):
        counter[0] += 1
        rid = f"q{counter[0]}"
        br.acquire_writer_lock(runtime, request_id=rid, pid=4243, now=clock.unix())
        br.write_request(runtime, session_id="s1", request_id=rid, action=action, **kwargs)
        tick(2)
        br.release_writer_lock(runtime, request_id=rid, pid=4243)

    def ask_confirm(label):
        request("ask", instruction=br.parse_instruction("the red car"))
        tick(2)
        snap(label + ":presented")
        request("confirm", candidate_index=0, token=session.candidate_result_id)
        tick(1)
        snap(label + ":confirmed")

    try:
        publish(2)
        snap("start")
        if scenario == "bound":
            ask_confirm("first")
            fake.tracked[2] = BOX_B
            publish(1)
            ask_confirm("second")
            publish(2)
            snap("after")
        elif scenario == "coasting":
            fake.tracked = {1: BOX_A, 2: BOX_B}
            publish(1)
            request("ask", instruction=br.parse_instruction("the red car"))
            tick(2)
            snap("coasting:presented")
            fake.tracked = {1: BOX_A}
            fake.lost = {2: BOX_B}
            publish(1)
            request("confirm", candidate_index=0, token=session.candidate_result_id)
            tick(1)
            snap("coasting:confirmed")
            for i in range(6):
                publish(1)
                snap(f"coast{i}")
        elif scenario == "failure_then_success":
            ask_confirm("fail")
            ask_confirm("succeed")
        elif scenario in ("lost_out_of_frame", "lost_degenerate"):
            # 绑定 2 号后 2 号进 lost：先在画内（UNMATCHED），再出画/退化（旧代码丢弃该行 → REMOVED → tracker_failure）。
            fake.tracked = {1: BOX_A, 2: BOX_B}
            publish(1)
            ask_confirm("bind2")
            fake.tracked = {1: BOX_A}
            fake.library_lost = {2: (6.4, 4.8, 51.2, 38.4)}
            publish(1)
            snap("lost_in_frame")
            fake.library_lost = {2: (-90.0, 4.8, -20.0, 38.4) if scenario == "lost_out_of_frame" else (40.0, 4.8, 40.0, 38.4)}
            for i in range(4):
                publish(1)
                snap(f"gone{i}")
        elif scenario == "coasting_out_of_frame":
            # coasting 非空（BOUND_COASTING、steps > 0）时 lost 框出画：旧代码在该帧视为无行 → COASTING_TO_TRACK_ENDED(removed)。
            fake.tracked = {1: BOX_A, 2: BOX_B}
            publish(1)
            request("ask", instruction=br.parse_instruction("the red car"))
            tick(2)
            snap("coasting:presented")
            fake.tracked = {1: BOX_A}
            fake.library_lost = {2: (6.4, 4.8, 51.2, 38.4)}
            publish(1)
            request("confirm", candidate_index=0, token=session.candidate_result_id)
            tick(1)
            snap("coasting:confirmed")
            publish(1)
            snap("coast_step")
            fake.library_lost = {2: (-90.0, 4.8, -20.0, 38.4)}
            for i in range(4):
                publish(1)
                snap(f"coast_gone{i}")
        elif scenario == "acquire":
            fake.tracked = {1: BOX_A}
            publish(1)
            fake.tracked = {}
            fake.removed = [1]
            publish(1)
            ask_confirm("ended")
            for i in range(6):
                publish(1)
                snap(f"acq{i}")
    finally:
        session.close()
        tmp.cleanup()
    return sequence


class LanguageCompatTests(unittest.TestCase):
    """AC-13 修订 1：语言确认（BOUND/BOUND_COASTING）、失败→成功、coasting 超时转 acquire、acquire 收养/失败：
    经 commit/release 后的指针、纪元、coasting、状态与原因序列与修改前代码逐条一致。"""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        base = accepted_base_commit()
        cls.base_root = None
        if base is not None:
            cls.base_root = Path(cls._tmp.name)
            export_controller(base, cls.base_root / "controller_base")
            # 导出包的 PROJECT_ROOT = 临时根：只读链接仓库 config/（冻结场景与规划器配置）。
            (cls.base_root / "config").symlink_to(PROJECT_ROOT / "config")

    @classmethod
    def tearDownClass(cls):
        for name in list(sys.modules):
            if name == "controller_base" or name.startswith("controller_base."):
                del sys.modules[name]
        cls._tmp.cleanup()

    def compare(self, scenario):
        if self.base_root is None:
            self.skipTest("git history unavailable")
        new = compat_script(None, scenario)
        old = compat_script(self.base_root, scenario)
        self.assertEqual(new, old)
        return new

    def test_language_compat_bound_and_reselect(self):
        sequence = self.compare("bound")
        self.assertEqual(sequence[-1]["track_id"], "s1-t2")

    def test_language_compat_bound_coasting_and_timeout_to_acquire(self):
        sequence = self.compare("coasting")
        self.assertIn("BOUND_COASTING", [s["result"] for s in sequence] + ["TRACK_ENDED"])

    def test_language_compat_failure_then_success(self):
        sequence = self.compare("failure_then_success")
        ids = [s["next_designation_id"] for s in sequence]
        self.assertEqual(ids[-1], 3)  # 失败的解析尝试也占号

    def test_language_compat_track_ended_acquire(self):
        self.compare("acquire")

    def _tracker_failure_frames(self, sequence):
        return [s["label"] for s in sequence if s["suspect"][0] == "tracker_failure"]

    def test_language_compat_out_of_frame_lost_keeps_old_removed_semantics(self):
        """IR-1：出画 lost 行在兼容视图下视为无该行，`tracker_failure` 与修改前同帧发生（不等库删 ID）。"""
        sequence = self.compare("lost_out_of_frame")
        self.assertEqual(self._tracker_failure_frames(sequence)[:1], ["gone0"])

    def test_language_compat_degenerate_lost_keeps_old_removed_semantics(self):
        sequence = self.compare("lost_degenerate")
        self.assertEqual(self._tracker_failure_frames(sequence)[:1], ["gone0"])

    def test_language_compat_coasting_then_out_of_frame(self):
        """IR-1：coasting 非空（steps > 0）时 lost 框出画，coasting 记账、纪元与状态序列与修改前逐条一致。"""
        sequence = self.compare("coasting_out_of_frame")
        by = {s["label"]: s for s in sequence}
        self.assertEqual(by["coasting:confirmed"]["result"], "BOUND_COASTING")
        self.assertIsNotNone(by["coast_step"]["coasting"])
        self.assertGreater(by["coast_step"]["coasting"]["steps"], 0)
        self.assertIsNone(by["coast_gone0"]["coasting"])



# --- P1-ENG-FASTFIX-001（G1/G2/G5；K1/K2/K3）：捕获会话的发布降级、升级、积压、投影、逐阶段耗时与重建后重捕 ------------

from controller.gated_publisher import RECEIPT_OUTCOMES, BodyCommandNotWritten, GatedPublisher, FrameSnapshotRing  # noqa: E402
from controller.language_loop import FASTFIX_JOURNAL_KINDS, JOURNAL_KINDS  # noqa: E402


class SlowDecode:
    """帧解码替身：`delays[frame_id]` 秒（在 `m_L` 之后、门求值之前推进假时钟）；`mutate[frame_id]` 在读后改盘上字节
    （注入完整性命中）；`fail` 中的帧解码抛 ValueError。"""

    def __init__(self, default_s=0.0, *, wall=True):
        self.clock = None
        self.runtime = None
        #: False = 只推进 monotonic（处理慢但不推迟墙钟，隔离发布门时序与采集年龄）。
        self.wall = wall
        self.delays = {}
        self.mutate = set()
        self.fail = set()
        self.default_s = default_s

    def __call__(self, path):
        frame_id = int(path.stem.split("_")[1])
        if frame_id in self.fail:
            raise ValueError(f"decode failed for {frame_id}")
        data = path.read_bytes()
        seconds = self.delays.pop(frame_id, self.default_s)
        if seconds and self.clock is not None:
            if self.wall:
                self.clock.advance(seconds)
            else:
                self.clock.monotonic_s += seconds
        if frame_id in self.mutate:
            self.mutate.discard(frame_id)
            (self.runtime / "frames" / path.name).write_bytes(b"tampered-after-load")
        return data


def write_fastfix_config(directory, *, n_drop=3, t_reacq=10, auto="on", t_pub=0.4, k_pub=2):
    path = Path(directory) / f"fastfix-{n_drop}-{t_reacq}-{auto}.json"
    path.write_text(json.dumps({
        "schema_version": tm.FASTFIX_SCHEMA,
        "params": {
            "t_pub_s": {"value": t_pub, "category": "contract_inherited"},
            "k_pub": {"value": k_pub, "category": "contract_inherited"},
            "n_drop_frames": {"value": n_drop, "category": "design_budget"},
            "t_reacq_frames": {"value": t_reacq, "category": "design_budget"},
            "auto_reacquire": {"value": auto, "category": "config_axis"},
        },
    }), encoding="utf-8")
    return path


def fx_harness(case, plan=None, *, bound=True, decode=None, **overrides):
    decode = decode or SlowDecode()
    builder = bound_harness if bound else CaptureHarness
    harness = builder(case, plan or steady(), decode=decode, **overrides)
    decode.clock = harness.clock
    decode.runtime = harness.runtime
    harness.decode = decode
    return harness


def frame_groups(receipts):
    """收据按帧分组：带 frame_id 的收据开新组，其后不带帧号的（安全 hold）归入当前组。"""
    groups, current = {}, None
    for receipt in receipts:
        if receipt["frame_id"] is not None:
            current = receipt["frame_id"]
        groups.setdefault(current, []).append(receipt)
    return groups


def holds(group):
    return [r for r in group if r["channel"] == "body_safety_hold" and r["outcome"] == "WRITTEN"]


def manager_state(manager):
    return {
        "binding": None if manager.binding is None else manager.binding.as_record(),
        "belief": None if manager.belief is None else manager.belief.as_record(),
        "task": None if manager.task is None else manager.task.as_record(),
        "runtime": None if manager.runtime is None else manager.runtime.as_record(),
        "version": manager.version,
        "episode_seq": manager.episode_seq,
        "pointer": manager._port.pointer() if manager._port is not None else None,  # noqa: SLF001
    }


class VelocityPlanner:
    """测试规划器：每帧给速度（检验「观测与云台 WRITTEN 后速度越线」路径）。"""

    name = "test-velocity"

    def decide(self, platform, estimate, now_s):
        from controller.body_planner import BodyCommand  # noqa: PLC0415

        return BodyCommand.velocity(1.0, 0.0, 0.4, "test")


class DegradeTests(unittest.TestCase):
    """AC-2：§3.2 表逐路径；观测 WRITTEN 不回改；每个 DROPPED 帧恰一条 hold；无 orphan_control；管理器与未注入对照相同。"""

    def test_observation_time_hit_drops_frame_and_holds_exactly_once(self):
        control = fx_harness(self)
        injected = fx_harness(self)
        control.publish(3)
        frame_id = injected.publisher.next_frame_id + 1
        injected.decode.delays[frame_id] = 0.55  # 复现第 647 帧形态
        injected.publish(3)
        group = frame_groups(injected.receipts())[frame_id]
        self.assertEqual([(r["channel"], r["outcome"], r["reason"]) for r in group if r["channel"] != "body_safety_hold"],
                         [("observation", "PUBLISH_DROPPED", "publish_expired"), ("look_at", "PUBLISH_DROPPED", "dropped_with_frame")])
        self.assertEqual(len(holds(group)), 1)
        self.assertIsNone(injected.session.publisher.fatal_reason)
        self.assertEqual(injected.session.resident_rebuilds, 0)
        self.assertFalse([r for r in injected.receipts() if r["reason"] == "orphan_control"])
        self.assertEqual(manager_state(injected.session.target_manager), manager_state(control.session.target_manager))
        self.assertEqual(injected.session.target_manager.track_key, control.session.target_manager.track_key)
        # 下一帧 PUBLISHED、FOLLOW 恢复（授权行 6、观测与云台写出），streak 清零。
        nxt = frame_groups(injected.receipts())[frame_id + 1]
        self.assertEqual([(r["channel"], r["outcome"]) for r in nxt][:2], [("observation", "WRITTEN"), ("look_at", "WRITTEN")])
        self.assertEqual(injected.authorizations()[frame_id + 1]["result"]["body"], "FOLLOW")
        self.assertEqual(injected.session.publisher.drop_streak, 0)
        dropped = injected.journal("publish_dropped")
        self.assertEqual([(r["frame_id"], r["streak"], r["reasons"]) for r in dropped], [(frame_id, 1, ["publish_expired"])])
        self.assertEqual(dropped[0]["fastfix_config_sha256"], injected.session.fastfix_sha256)

    def test_predicted_look_at_time_hit(self):
        harness = fx_harness(self, PredictionTests().lost_plan(5))
        harness.publish(2)  # 3、4 观测
        harness.decode.delays[6] = 0.5
        harness.publish(3)  # 5、6、7 预测窗口
        group = frame_groups(harness.receipts())[6]
        self.assertEqual([(r["channel"], r["outcome"], r["reason"]) for r in group if r["channel"] != "body_safety_hold"],
                         [("predicted_look_at", "PUBLISH_DROPPED", "publish_expired")])
        self.assertEqual(len(holds(group)), 1)
        self.assertIsNone(harness.session.publisher.fatal_reason)
        self.assertTrue(harness.written("predicted_look_at", 7))

    def _mid_frame(self, channel, slow_after):
        harness = fx_harness(self)
        harness.publish(1)
        harness.session.loop.body_planner = VelocityPlanner()
        inner = harness.session.publisher._publisher  # noqa: SLF001
        target = harness.publisher.next_frame_id
        original = getattr(inner, slow_after)

        def slow(*args, **kwargs):
            result = original(*args, **kwargs)
            if harness.session.publisher._frame_ctx and harness.session.publisher._frame_ctx["frame_id"] == target:  # noqa: SLF001
                harness.clock.advance(0.5)
            return result

        setattr(inner, slow_after, slow)
        harness.publish(1)
        setattr(inner, slow_after, original)
        harness.publish(1)
        return harness, target

    def test_observation_written_then_gimbal_over_the_line(self):
        harness, target = self._mid_frame("look_at", "observation")
        group = frame_groups(harness.receipts())[target]
        rows = [(r["channel"], r["outcome"], r["reason"], r["detail"].get("partial_after_observation")) for r in group
                if r["channel"] != "body_safety_hold"]
        self.assertEqual(rows, [("observation", "WRITTEN", None, None),
                                ("look_at", "PUBLISH_DROPPED", "publish_expired", True),
                                ("body_command", "PUBLISH_DROPPED", "dropped_with_frame", True)])
        self.assertEqual(len(holds(group)), 1)
        observation = json.loads((harness.runtime / "tracking_observation.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(observation["observation"]["frame_id"], target)  # 已写观测不撤销
        self.assertIsNone(harness.session.publisher.fatal_reason)

    def test_observation_and_gimbal_written_then_velocity_over_the_line(self):
        harness, target = self._mid_frame("body_command", "look_at")
        group = frame_groups(harness.receipts())[target]
        rows = [(r["channel"], r["outcome"], r["reason"]) for r in group if r["channel"] != "body_safety_hold"]
        self.assertEqual(rows, [("observation", "WRITTEN", None), ("look_at", "WRITTEN", None),
                                ("body_command", "PUBLISH_DROPPED", "publish_expired")])
        self.assertTrue([r for r in group if r["channel"] == "body_command"][0]["detail"]["partial_after_observation"])
        self.assertEqual(len(holds(group)), 1)
        self.assertEqual(harness.journal("publish_dropped")[-1]["frame_id"], target)
        nxt = frame_groups(harness.receipts())[target + 1]
        self.assertTrue([r for r in nxt if r["channel"] == "body_command" and r["outcome"] == "WRITTEN"])

    def test_receipt_outcome_appended_last(self):
        self.assertEqual(RECEIPT_OUTCOMES[-1], "PUBLISH_DROPPED")
        self.assertEqual(RECEIPT_OUTCOMES[:4], ("WRITTEN", "PUBLISH_REJECTED", "MUTED_DROPPED", "WRITE_FAILED"))


class EscalateTests(unittest.TestCase):
    """AC-3：连续 N_drop 个 DROPPED 最新帧恰在第 N_drop 帧结算时升级；PUBLISHED 清零；完整性任意 streak 即致命。"""

    def off_harness(self, directory, **kw):
        return fx_harness(self, fastfix_config=write_fastfix_config(directory, auto="off"), **kw)

    def test_escalates_exactly_at_n_drop_with_reason_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            harness = self.off_harness(directory)
            start = harness.publisher.next_frame_id
            for offset in range(3):
                harness.decode.delays[start + offset] = 0.5
            harness.publish(2)
            self.assertEqual((harness.session.resident_rebuilds, harness.session.publisher.drop_streak), (0, 2))
            harness.publish(1)
            self.assertEqual(harness.session.resident_rebuilds, 1)
            escalated = harness.journal("publish_escalated")
            self.assertEqual([(r["frame_id"], r["reason"], r["streak"], r["n_drop"]) for r in escalated],
                             [(start + 2, "publish_expired", 3, 3)])
            self.assertEqual((harness.session.state, harness.session.reason), ("REINIT_REQUIRED", "publish_expired"))
            skipped = harness.journal("reacquire_skipped")
            self.assertEqual(skipped[-1]["reason"], "auto_reacquire_off")
            closed = harness.journal("resident_loop_closed")
            self.assertEqual(closed[-1]["reason"], "publish_expired")

    def test_published_frame_clears_streak(self):
        with tempfile.TemporaryDirectory() as directory:
            harness = self.off_harness(directory)
            start = harness.publisher.next_frame_id
            for frame_id in (start, start + 1, start + 3, start + 4):
                harness.decode.delays[frame_id] = 0.5
            harness.publish(5)
            self.assertEqual(harness.session.resident_rebuilds, 0)
            self.assertEqual(harness.session.publisher.drop_streak, 2)
            self.assertFalse(harness.journal("publish_escalated"))

    def test_integrity_hit_is_fatal_at_any_streak_and_not_degraded(self):
        with tempfile.TemporaryDirectory() as directory:
            harness = self.off_harness(directory)
            start = harness.publisher.next_frame_id
            harness.decode.delays[start] = 0.5
            harness.decode.delays[start + 1] = 0.5
            harness.decode.mutate.add(start + 2)
            harness.publish(3)
            receipts = harness.receipts()
            rejected = [r for r in receipts if r["outcome"] == "PUBLISH_REJECTED"]
            self.assertEqual((rejected[0]["frame_id"], rejected[0]["reason"]), (start + 2, "image_identity_changed"))
            self.assertFalse(harness.journal("publish_escalated"))
            self.assertEqual(harness.session.resident_rebuilds, 1)
            self.assertEqual(harness.journal("reacquire_skipped")[-1]["reason"], "not_timing_escalation")

    def test_dropped_frame_with_failed_hold_write_neither_counts_nor_escalates(self):
        """C1-2：生产路径降级帧（处理超时）+ 该帧 HOLD 底层写失败 → 结算 WRITE_FAILED，streak 不计不清、不升级；
        写失败照现行 fail-closed（不改安全处置）。修前：混合帧按 DROPPED 计数，第 N_drop 帧升级（红）。"""
        with tempfile.TemporaryDirectory() as directory:
            harness = self.off_harness(directory)
            start = harness.publisher.next_frame_id
            for offset in range(3):
                harness.decode.delays[start + offset] = 0.5
            harness.publish(2)
            publisher = harness.session.publisher
            self.assertEqual(publisher.drop_streak, 2)
            inner = publisher._publisher  # noqa: SLF001 — 底层桥写出器（故障注入点）
            original = inner.body_command
            calls = []

            def failing_body(command):
                calls.append(getattr(command, "mode", None))
                raise OSError("disk full")

            inner.body_command = failing_body
            try:
                harness.publish(1)
            except Exception:  # noqa: BLE001 — 现行 fail-closed 可上抛
                pass
            inner.body_command = original
            self.assertTrue(calls)
            settle = publisher.last_settle
            self.assertEqual(settle["frame_id"], start + 2)
            self.assertEqual(settle["outcome"], "WRITE_FAILED")
            self.assertTrue(settle["dropped"])
            self.assertFalse(settle["escalated"])
            self.assertEqual(publisher.drop_streak, 2)
            self.assertFalse(harness.journal("publish_escalated"))
            failed = [r for r in harness.receipts() if r["outcome"] == "WRITE_FAILED"]
            self.assertTrue(failed)
            self.assertTrue(all(r["channel"] == "body_safety_hold" for r in failed))
            dropped = [r for r in harness.receipts() if r["outcome"] == "PUBLISH_DROPPED" and r["frame_id"] == start + 2]
            self.assertTrue(dropped)

    def test_hold_no_attempt_and_write_failure_neither_count_nor_clear(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        rig_root = Path(directory.name)

        class Inner:
            fail_velocity = False

            def observation(self, *a):
                return Path("o")

            def look_at(self, p):
                return Path("g")

            def body_command(self, command):
                if self.fail_velocity and command.mode != "hold":
                    raise OSError("disk full")
                return Path("b")

            def hold_body(self):
                return Path("h")

        from controller.body_planner import BodyCommand  # noqa: PLC0415

        inner = Inner()
        publisher = GatedPublisher(inner, FrameSnapshotRing(rig_root / "ring", capacity=2), frames_directory=rig_root / "frames",
                                   receipts_path=rig_root / "r.jsonl", k_pub=2, t_pub_s=0.4, t_stall_s=3.0, track_id="t",
                                   classified=True, n_drop=3)
        publisher.unmute()
        publisher.drop_streak = 2
        publisher.begin_frame(10)
        publisher.body_command(BodyCommand.hold(0.4, "no_observation"))  # 只有安全 hold → NO_ATTEMPT
        self.assertEqual((publisher.settle_frame(10)["outcome"], publisher.drop_streak), ("NO_ATTEMPT", 2))
        publisher.begin_frame(11)
        publisher.hold_body("acquiring")
        self.assertEqual((publisher.settle_frame(11)["outcome"], publisher.drop_streak), ("NO_ATTEMPT", 2))
        publisher.begin_frame(12)
        publisher._frame_ctx["qualified_written"] = True  # noqa: SLF001 — 观测已写（门在帧级测试另证）
        publisher.accepted_frame_id = None
        inner.fail_velocity = True
        publisher._frame_ctx["write_failed"] = True  # noqa: SLF001
        self.assertEqual((publisher.settle_frame(12)["outcome"], publisher.drop_streak), ("WRITE_FAILED", 2))
        self.assertIsNone(publisher.settle_frame(99))  # 无上下文（旧帧）→ 不结算

    def test_write_failure_receipt_marks_frame(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        harness = fx_harness(self)
        harness.publish(1)
        harness.session.loop.body_planner = VelocityPlanner()
        inner = harness.session.publisher._publisher  # noqa: SLF001
        original = inner.body_command

        def failing(command):
            if command.mode != "hold":
                raise OSError("disk full")
            return original(command)

        inner.body_command = failing
        harness.session.publisher.drop_streak = 2
        harness.publish(1)
        self.assertEqual(harness.session.publisher.last_settle["outcome"], "WRITE_FAILED")
        self.assertEqual(harness.session.publisher.drop_streak, 2)
        self.assertEqual(harness.session.resident_rebuilds, 0)


class CompatUnchangedTests(unittest.TestCase):
    """AC-3/AC-12：兼容模式不启用分级门/帧结算/耗时标记/链式输入；与接受基线的发布器逐条收据相同。"""

    def test_compat_session_uses_current_paths(self):
        compat = compat_harness(self)
        compat.publish(3)
        self.assertFalse(compat.session.capture)
        self.assertFalse(compat.session.publisher.classified)
        self.assertIsNone(compat.session.publisher.n_drop)
        self.assertFalse(compat.session.ring.record_marks)
        self.assertIsNone(compat.session.loop.capture_hook)
        self.assertFalse(compat.session.target_manager.inputs.chain)
        self.assertIsNone(compat.session.fastfix)
        self.assertFalse([r for r in compat.journal() if r["kind"] in FASTFIX_JOURNAL_KINDS])

    def test_unclassified_publisher_receipts_match_accepted_base(self):
        from tools.eng_fastfix.common import export_base_controller  # noqa: PLC0415

        import importlib  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as directory:
            try:
                export_base_controller(Path(directory) / "fx_base_controller_gp")
            except RuntimeError:
                self.skipTest("git history unavailable")
            sys.path.insert(0, directory)
            try:
                base = importlib.import_module("fx_base_controller_gp.gated_publisher")
                base_lang = importlib.import_module("fx_base_controller_gp.language_loop")
                base_track = importlib.import_module("fx_base_controller_gp.track_loop")
                from controller import gated_publisher as current  # noqa: PLC0415
                from controller.language_loop import FixtureFramePublisher as CurrentFixture  # noqa: PLC0415
                from controller.track_loop import FrameRepository as CurrentRepository  # noqa: PLC0415

                def run(module, fixture_cls, repository_cls, root):
                    clock = FakeClock()
                    fixture = fixture_cls(root / "runtime", unix=clock.unix)
                    ring = module.FrameSnapshotRing(root / "ring", capacity=8, decode=lambda p: p.read_bytes(),
                                                    monotonic=clock.monotonic, unix=clock.unix)
                    repo = module.SnapshotRepository(repository_cls(root / "runtime", image_loader=ring.image_loader), ring)

                    class Inner:
                        def observation(self, *a):
                            return Path("o")

                        def look_at(self, p):
                            return Path("g")

                        def body_command(self, c):
                            return Path("b")

                        def hold_body(self):
                            return Path("h")

                    publisher = module.GatedPublisher(Inner(), ring, frames_directory=root / "runtime" / "frames",
                                                      receipts_path=root / "r.jsonl", k_pub=2, t_pub_s=0.4, t_stall_s=3.0,
                                                      track_id="t", monotonic=clock.monotonic, unix=clock.unix, hold_receipts=True)
                    publisher.unmute()
                    for _ in range(4):
                        fixture.publish(b"img")
                    repo.load(1)
                    publisher.observation(1, "t", (0.1, 0.1, 0.2, 0.2), 0.9)  # 帧差 2 → 通过
                    publisher.look_at((1.0, 0.0, 1.0))
                    repo.load(3)
                    clock.advance(0.5)
                    publisher.observation(3, "t", (0.1, 0.1, 0.2, 0.2), 0.9)  # 超时 → 首拒致命
                    publisher.hold_body("loop_start")
                    rows = [json.loads(line) for line in (root / "r.jsonl").read_text(encoding="utf-8").splitlines()]
                    return rows, publisher.fatal_reason

                left = run(base, base_lang.FixtureFramePublisher, base_track.FrameRepository, Path(directory) / "a")
                right = run(current, CurrentFixture, CurrentRepository, Path(directory) / "b")
                self.assertEqual(left, right)
            finally:
                sys.path.remove(directory)


class BacklogTests(unittest.TestCase):
    """AC-4：积压注入（10 帧 × 0.5 s）：只最新帧开上下文、结算与升级时刻按 §3.2。"""

    def test_backlog_only_newest_frame_settles(self):
        """处理慢（每帧 0.5 s monotonic）而采集年龄未越 `T_stall`：只最新帧开上下文与结算，第 3 个降级最新帧升级。"""
        with tempfile.TemporaryDirectory() as directory:
            harness = fx_harness(self, fastfix_config=write_fastfix_config(directory, auto="off"), decode=SlowDecode(wall=False))
            start = harness.publisher.next_frame_id
            for frame_id in range(start, start + 10):
                harness.decode.delays[frame_id] = 0.5
            harness.publish(10, tick=False)
            harness.tick()
            timing = [r for r in harness.journal("frame_timing") if r["frame_id"] >= start]
            self.assertEqual([r["batch_position"] for r in timing], ["backlog"] * 9 + ["newest"])
            self.assertEqual([r["publish_s"] for r in timing[:9]], [0.0] * 9)
            self.assertFalse(any(r["publish_attempted"] for r in timing[:9]))
            dropped = harness.journal("publish_dropped")
            self.assertEqual([(r["frame_id"], r["streak"]) for r in dropped], [(start + 9, 1)])
            framed = [r for r in harness.receipts() if r["frame_id"] is not None and r["frame_id"] >= start]
            self.assertEqual({r["frame_id"] for r in framed}, {start + 9})
            for count in (2, 3):
                harness.decode.delays[harness.publisher.next_frame_id] = 0.5
                harness.publish(1)
            self.assertEqual([(r["frame_id"], r["streak"]) for r in harness.journal("publish_escalated")], [(start + 11, 3)])

    def test_wall_clock_backlog_crosses_stall_and_is_integrity(self):
        """同一积压（10 帧 × 0.5 s）若墙钟同步推进：最新帧采集年龄 ≈ 5 s > T_stall → §3.1 步 5e 完整性致命（不降级）。"""
        with tempfile.TemporaryDirectory() as directory:
            harness = fx_harness(self, fastfix_config=write_fastfix_config(directory, auto="off"))
            start = harness.publisher.next_frame_id
            for frame_id in range(start, start + 10):
                harness.decode.delays[frame_id] = 0.5
            harness.publish(10, tick=False)
            harness.tick()
            rejected = [r for r in harness.receipts() if r["outcome"] == "PUBLISH_REJECTED"]
            self.assertEqual((rejected[0]["frame_id"], rejected[0]["reason"]), (start + 9, "publish_expired"))
            self.assertEqual(rejected[0]["detail"]["hits"][-1]["expired_by"], "capture_age")
            self.assertFalse(harness.journal("publish_dropped"))
            self.assertEqual(harness.session.resident_rebuilds, 1)


class ProjectionTests(unittest.TestCase):
    """AC-4：`TRACKING/publish_degraded` 与恢复；管理器其他原因优先；新名字只在闭集末尾追加。"""

    def test_degraded_projection_and_recovery(self):
        harness = fx_harness(self)
        harness.decode.delays[harness.publisher.next_frame_id] = 0.5
        harness.publish(1)
        self.assertEqual((harness.session.state, harness.session.reason), ("TRACKING", "publish_degraded"))
        document = json.loads((harness.runtime / "tracker_state.json").read_text(encoding="utf-8"))
        self.assertEqual(document["tracker_state"]["reason"], "publish_degraded")
        harness.publish(1)
        self.assertEqual((harness.session.state, harness.session.reason), ("TRACKING", None))

    def test_predicting_degrades_but_other_reasons_take_priority(self):
        harness = fx_harness(self, PredictionTests().lost_plan(5))
        harness.publish(2)
        harness.decode.delays[5] = 0.5
        harness.publish(1)  # 5：predicting + 降级
        self.assertEqual((harness.session.state, harness.session.reason), ("TRACKING", "publish_degraded"))
        harness.publish(2)  # 6、7：predicting 恢复（7 起 no_new_observation）
        harness.decode.delays[8] = 0.5
        harness.publish(1)  # 8：no_new_observation 优先，不改成降级
        self.assertEqual((harness.session.state, harness.session.reason), ("TRACKING", "no_new_observation"))

    def test_new_names_only_appended(self):
        from controller.target_manager import MODE_ORIGINS, ORIGINS, RELATIONS  # noqa: PLC0415
        from tools.eng_fastfix.common import base_source  # noqa: PLC0415
        import ast as _ast  # noqa: PLC0415

        self.assertEqual(ORIGINS[-1], "reacquire")
        self.assertEqual(RELATIONS[-1], "REBUILD_REACQUIRE")
        self.assertIn("reacquire", MODE_ORIGINS["capture"])
        self.assertNotIn("reacquire", MODE_ORIGINS["compat"])
        self.assertEqual(set(FASTFIX_JOURNAL_KINDS) <= JOURNAL_KINDS, True)
        sources = {name: base_source(f"controller/{name}.py") for name in ("target_manager", "gated_publisher", "language_loop")}
        if any(text is None for text in sources.values()):
            self.skipTest("git history unavailable")

        def literal(text, name):
            for node in _ast.parse(text).body:
                targets = node.targets if isinstance(node, _ast.Assign) else [node.target] if isinstance(node, _ast.AnnAssign) else []
                if any(isinstance(t, _ast.Name) and t.id == name for t in targets):
                    return _ast.literal_eval(node.value)
            raise LookupError(name)

        for module, name, current in (("target_manager", "ORIGINS", ORIGINS), ("target_manager", "RELATIONS", RELATIONS),
                                      ("gated_publisher", "RECEIPT_OUTCOMES", RECEIPT_OUTCOMES)):
            base = tuple(literal(sources[module], name))
            self.assertEqual(tuple(current[: len(base)]), base, name)
        tree = _ast.parse(sources["language_loop"])
        base_kinds = set()
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Constant) and isinstance(node.value, str):
                base_kinds.add(node.value)
        self.assertEqual(set(FASTFIX_JOURNAL_KINDS) & base_kinds, set())  # 本项名字在基线源中不存在（新追加）
        self.assertEqual(JOURNAL_KINDS - set(FASTFIX_JOURNAL_KINDS) <= base_kinds, True)


class FakeModel:
    def __init__(self, holder, seconds):
        self.holder = holder
        self.seconds = seconds

    def predict(self, **kwargs):
        self.holder["clock"].advance(self.seconds)
        return []


class TimedAssociator:
    """库关联器替身：`update` 推进「关联」耗时；`fail` 中的帧在关联中途抛错（检测已返回）。"""

    def __init__(self, holder, seconds):
        self.holder = holder
        self.seconds = seconds
        self.fail = set()
        self.frame = None

    def update(self, boxes, image):
        self.holder["clock"].advance(self.seconds)
        if self.frame in self.fail:
            raise RuntimeError("association failed")
        return []


class TimedResident(FakeCaptureResident):
    """逐阶段耗时用替身：与生产 `DetAssocTracker.step` 同序——首帧经 `_make_resident_tracker` 懒建关联器；
    经会话模型缓存（计时包装）调用模型 `predict`，再调关联器 `update`，最后做历史组装（`tail_s`，不属关联段）。"""

    def __init__(self, plan, holder, associate_s, tail_s=0.0):
        super().__init__(plan)
        self.holder = holder
        self.associate_s = associate_s
        self.tail_s = tail_s
        self._tracker = None
        self.fail_before_detect = set()
        self.assoc_fail = set()

    def _make_resident_tracker(self):
        return TimedAssociator(self.holder, self.associate_s)

    @property
    def associator(self):
        return self._tracker

    def step(self, image, frame_id, metadata):
        if self._tracker is None:
            self._tracker = self._make_resident_tracker()
        if frame_id in self.fail_before_detect:
            raise RuntimeError("homography failed before detection")
        model = self.holder["session"]._model_cache.load(Path("weights.pt"))  # noqa: SLF001
        model.predict(source=image)
        self._tracker.frame = frame_id
        self._tracker.fail = self.assoc_fail
        self._tracker.update([], image)
        self.holder["clock"].advance(self.tail_s)
        return super().step(image, frame_id, metadata)


class FrameTimingTests(unittest.TestCase):
    """AC-9：每个被处理帧恰一条 `frame_timing`；假时钟下段之和逐值 = total；`gate_eval_s` = 同次门 load_elapsed；
    `journal_prev_s` 单列；失败帧缺段带原因；桥文件无新字段。"""

    def timed_harness(self):
        holder = {}
        decode = SlowDecode(default_s=0.0625)
        harness = CaptureHarness(self, steady(), decode=decode,
                                 tracker_factory=lambda: TimedResident(steady(), holder, 0.03125),
                                 model_loader=lambda path: FakeModel(holder, 0.125))
        holder["clock"] = harness.clock
        holder["session"] = harness.session
        decode.clock = harness.clock
        harness.decode = decode
        harness.publish(3)
        harness.click(300, 240, 1)
        return harness

    def test_one_record_per_frame_and_segments_sum_to_total(self):
        harness = self.timed_harness()
        harness.publish(3)
        timing = harness.journal("frame_timing")
        frames = [r["frame_id"] for r in timing]
        self.assertEqual(frames, sorted(set(frames)))
        processed = sorted({f for record in harness.journal("frames_processed") for f in record["frame_ids"]} | {0})
        self.assertEqual(frames, processed)
        last = timing[-1]
        self.assertEqual((last["read_s"], last["decode_s"], last["detect_s"], last["associate_s"], last["tm_s"], last["publish_s"]),
                         (0.0, 0.0625, 0.125, 0.03125, 0.0, 0.0))
        self.assertEqual(last["total_s"], 0.21875)
        segments = ("read_s", "decode_s", "detect_s", "associate_s", "tm_s", "publish_s")
        for record in timing:
            self.assertEqual(sum(record[k] for k in segments), record["total_s"], record["frame_id"])
            self.assertNotIn("missing_reason", record)
            self.assertIn("journal_prev_s", record)
        # `gate_eval_s` 与同次门的 `load_elapsed_s` 同值（同源同起点）。
        receipts = [r for r in harness.receipts() if r["frame_id"] == last["frame_id"] and "load_elapsed_s" in r["detail"]]
        self.assertEqual(last["gate_eval_s"], [r["detail"]["load_elapsed_s"] for r in receipts])
        self.assertEqual(last["gate_eval_s"], [0.21875, 0.21875])
        self.assertEqual(timing[1]["journal_prev_frame_id"], timing[0]["frame_id"])
        self.assertEqual(last["journal_prev_s"], 0.0)

    def test_failed_frame_keeps_reached_marks_and_reasons(self):
        harness = self.timed_harness()
        failing = harness.publisher.next_frame_id
        harness.decode.fail.add(failing)
        harness.publish(1)
        record = [r for r in harness.journal("frame_timing") if r["frame_id"] == failing][0]
        self.assertTrue(record["failed"])
        self.assertEqual(record["read_s"], 0.0)
        self.assertIsNone(record["decode_s"])
        self.assertIsNone(record["total_s"])
        self.assertEqual(record["missing_reason"]["frame"], "load_failed:ValueError")
        self.assertEqual(harness.session.reason, "metadata_invalid")

    # --- C1-1（AC-9、§3.5、首次接受释义 4）：实际关联返回边界、异常帧已得段保留、旧检测标记不串帧 -------------

    def tail_harness(self, tail_s=0.25):
        holder = {}
        decode = SlowDecode(default_s=0.0625)
        harness = CaptureHarness(self, steady(), decode=decode,
                                 tracker_factory=lambda: TimedResident(steady(), holder, 0.03125, tail_s=tail_s),
                                 model_loader=lambda path: FakeModel(holder, 0.125))
        holder["clock"] = harness.clock
        holder["session"] = harness.session
        decode.clock = harness.clock
        harness.decode = decode
        harness.publish(3)
        harness.click(300, 240, 1)
        harness.publish(2)
        return harness

    def timing_of(self, harness, frame_id):
        rows = [r for r in harness.journal("frame_timing") if r["frame_id"] == frame_id]
        self.assertEqual(len(rows), 1, rows)
        return rows[0]

    def test_associate_segment_ends_at_associator_update_return_not_step_return(self):
        harness = self.tail_harness(tail_s=0.25)
        timing = harness.journal("frame_timing")
        for record in timing:
            self.assertEqual(record["associate_s"], 0.03125, record["frame_id"])
            self.assertNotIn("missing_reason", record)
        # 历史组装尾段（0.25 s）落在 tm 段（m_assoc → m_tm），不冒作关联段；段之和仍逐值 = total。
        self.assertEqual(timing[-1]["tm_s"], 0.25)
        self.assertEqual(timing[-1]["total_s"], 0.0625 + 0.125 + 0.03125 + 0.25)

    def test_association_exception_keeps_detect_mark_and_one_row(self):
        harness = self.tail_harness()
        failing = harness.publisher.next_frame_id
        harness.session_tracker().assoc_fail.add(failing)
        try:
            harness.publish(1)
        except RuntimeError:
            pass
        record = self.timing_of(harness, failing)
        self.assertTrue(record["failed"])
        self.assertEqual(record["detect_s"], 0.125)
        self.assertIsNone(record["associate_s"])
        self.assertIsNone(record["total_s"])
        self.assertEqual(record["missing_reason"]["frame"], "step_failed:RuntimeError")
        self.assertEqual(record["missing_reason"]["associate_s"], "mark_unavailable:m_assoc")

    def test_failure_before_detect_does_not_reuse_previous_frame_detect_mark(self):
        harness = self.tail_harness()
        failing = harness.publisher.next_frame_id
        harness.session_tracker().fail_before_detect.add(failing)
        try:
            harness.publish(1)
        except RuntimeError:
            pass
        record = self.timing_of(harness, failing)
        self.assertIsNone(record["marks"]["m_det"])
        self.assertIsNone(record["detect_s"])
        self.assertEqual(record["missing_reason"]["frame"], "step_failed:RuntimeError")

    def test_manager_exception_emits_one_row_with_reached_segments(self):
        harness = self.tail_harness()
        failing = harness.publisher.next_frame_id
        manager = harness.session.target_manager
        original = manager.on_frame

        def boom(entry, **kwargs):
            if int(entry.frame_id) == failing:
                raise ValueError("manager failed")
            return original(entry, **kwargs)

        manager.on_frame = boom
        try:
            harness.publish(1)
        except ValueError:
            pass
        record = self.timing_of(harness, failing)
        self.assertEqual((record["detect_s"], record["associate_s"]), (0.125, 0.03125))
        self.assertIsNone(record["tm_s"])
        self.assertEqual(record["missing_reason"]["frame"], "tm_failed:ValueError")

    def test_publish_exception_emits_one_row_with_tm_segment(self):
        harness = self.tail_harness()
        failing = harness.publisher.next_frame_id
        publisher = harness.session_loop_publisher()
        original = publisher.observation

        def boom(frame_id, *args, **kwargs):
            if int(frame_id) == failing:
                raise OSError("bridge write failed")
            return original(frame_id, *args, **kwargs)

        publisher.observation = boom
        try:
            harness.publish(1)
        except OSError:
            pass
        record = self.timing_of(harness, failing)
        self.assertEqual((record["detect_s"], record["associate_s"], record["tm_s"]), (0.125, 0.03125, 0.25))
        self.assertIsNone(record["publish_s"])
        self.assertEqual(record["missing_reason"]["frame"], "publish_failed:OSError")

    def _write_failure_after_real_gate(self, channel):
        """真实分级门放行后令底层写出器（`observation` 或云台 `look_at`）在本帧抛 OSError；返回（本帧计时行，
        本帧各次门 detail 读数）。"""
        # 尾段 0：本帧 load_elapsed 低于 t_pub，真实门放行（尾段 0.25 s 会越线成 DROP、到不了底层写）。
        harness = self.tail_harness(tail_s=0.0)
        failing = harness.publisher.next_frame_id
        gated = harness.session_loop_publisher()
        self.assertTrue(gated.classified)
        seen = []
        verdict = gated._classified_verdict

        def recording_verdict(frame_id):
            result = verdict(frame_id)
            if int(frame_id) == failing:
                seen.append(result)
            return result

        gated._classified_verdict = recording_verdict
        inner = gated._publisher
        original = getattr(inner, channel)

        def boom(*args, **kwargs):
            current = args[0] if channel == "observation" else gated.accepted_frame_id
            if current is not None and int(current) == failing:
                raise OSError("bridge write failed")
            return original(*args, **kwargs)

        setattr(inner, channel, boom)
        try:
            harness.publish(1)
        except OSError:
            pass
        self.assertTrue(seen)
        self.assertEqual({v for v, _, _ in seen}, {"PASS"})
        record = self.timing_of(harness, failing)
        self.assertTrue(record["failed"])
        self.assertIsNone(record["settle_outcome"])
        self.assertEqual(record["missing_reason"]["frame"], "publish_failed:OSError")
        self.assertEqual((record["detect_s"], record["associate_s"], record["tm_s"]), (0.125, 0.03125, 0.0))
        self.assertIsNone(record["publish_s"])
        return harness, failing, record, [detail["load_elapsed_s"] for _, _, detail in seen]

    def test_write_failure_after_real_gate_keeps_gate_eval(self):
        """R1-1（AC-9）：真实分级门放行后底层观测写出器抛 OSError（AC-2 的 fail-closed 上抛路径）——该帧恰一行
        `frame_timing`，`gate_eval_s` 保留本帧已读门读数（与门 detail 同值），已到达段照记；写失败照常上抛。"""
        harness, failing, record, readings = self._write_failure_after_real_gate("observation")
        self.assertEqual(len(readings), 1)
        self.assertEqual(record["gate_eval_s"], readings)
        self.assertFalse([r for r in harness.receipts() if r["frame_id"] == failing and r["channel"] == "observation"])

    def test_gimbal_write_failure_after_real_gate_keeps_gate_evals(self):
        """R1-1（AC-9）：观测已写、云台 `look_at` 门放行后底层写出器抛 OSError——`gate_eval_s` 保留本帧两次门读数。"""
        harness, failing, record, readings = self._write_failure_after_real_gate("look_at")
        self.assertEqual(len(readings), 2)
        self.assertEqual(record["gate_eval_s"], readings)
        observed = [r for r in harness.receipts() if r["frame_id"] == failing and r["channel"] == "observation"]
        self.assertEqual([r["outcome"] for r in observed], ["WRITTEN"])
        self.assertEqual(readings[0], observed[0]["detail"]["load_elapsed_s"])

    def test_bridge_files_carry_no_timing_fields(self):
        harness = self.timed_harness()
        harness.publish(2)
        for name in ("tracking_observation.json", "tracker_state.json", "gimbal_command.json", "body_command.json"):
            text = (harness.runtime / name).read_text(encoding="utf-8")
            for forbidden in ("frame_timing", "m_read0", "gate_eval_s", "journal_prev_s", "total_s", "drop_streak"):
                self.assertNotIn(forbidden, text, (name, forbidden))


# --- 重建后重捕（会话层） -------------------------------------------------------------------------


class FakeKF:
    def predict(self, mean, covariance):
        new_mean = list(mean)
        for i in range(4):
            new_mean[i] = mean[i] + mean[i + 4]
        cov = [[covariance[i][j] + (1.0 if i == j else 0.0) for j in range(8)] for i in range(8)]
        return new_mean, cov


class FakeLibTrack:
    shared_kalman = FakeKF()

    def __init__(self, key, xywh, frame_id):
        self.track_id = key
        self.mean = [xywh[0], xywh[1], xywh[2], xywh[3], 0.0, 0.0, 0.0, 0.0]
        self.covariance = [[(25.0 if i < 4 else 1.0) if i == j else 0.0 for j in range(8)] for i in range(8)]
        self.frame_id = frame_id
        self.kalman_filter = None

    def tlwh_to_xywh(self):  # 布局标记（BoT-SORT `BOTrack`）
        return None


class FakeAssociator:
    def __init__(self):
        self.tracked_stracks = []
        self.lost_stracks = []


class ReacqResident(FakeCaptureResident):
    """带库关联器替身（完整 KF 状态与 KF 预测器）的常驻替身；每次工厂调用 = 一个新载体（历史为空）。"""

    def __init__(self, plan):
        super().__init__(plan)
        self.associator = FakeAssociator()

    def step(self, image, frame_id, metadata):
        entry = super().step(image, frame_id, metadata)
        tracks = []
        for snap in entry.post_snapshots:
            library = entry.library_frame_id if snap.phase == KF_POSTERIOR else entry.library_frame_id - 1
            tracks.append(FakeLibTrack(snap.track_key, snap.xywh_px, library))
        self.associator.tracked_stracks = tracks
        return entry


def reacq_harness(case, plans, directory, *, auto="on", t_reacq=10, **kw):
    carriers = []

    def factory():
        tracker = ReacqResident(plans[min(len(carriers), len(plans) - 1)])
        carriers.append(tracker)
        return tracker

    harness = fx_harness(case, plans[0], tracker_factory=factory,
                         fastfix_config=write_fastfix_config(directory, auto=auto, t_reacq=t_reacq), **kw)
    harness.carriers = carriers
    return harness


def escalate_session(harness):
    """绑定后 3 个最新帧各超时 0.5 s → 第 3 帧结算升级（时序升级拆载体）。"""
    start = harness.publisher.next_frame_id
    for frame_id in range(start, start + 3):
        harness.decode.delays[frame_id] = 0.5
    harness.publish(3)
    return start + 2


class ReacquireSessionTests(unittest.TestCase):
    """AC-5（会话层）：时序升级 → 提示 → 新载体 → 窗口 → 唯一候选提交；窗口内零 look_at/速度、每最新帧恰一次 hold；
    同帧 stop > release > 点击 > 自动；零新帧 tick 到期；`tm_inputs` 重放事件逐条相同。"""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = directory.name

    def plans(self, second=None):
        return [steady(), second or steady(key=5)]

    def test_timing_escalation_rebuild_and_reacquire_commit(self):
        harness = reacq_harness(self, self.plans(), self.dir)
        manager = harness.session.target_manager
        old_episode = manager.binding.target_episode_id
        old_task = manager.task
        old_token = harness.session.track_id
        escalation_frame = escalate_session(harness)
        self.assertEqual((harness.session.state, harness.session.reason), ("REINIT_REQUIRED", "publish_expired"))
        self.assertEqual((manager.runtime.phase, manager.binding), ("ACQUIRING", None))
        hint_event = [r for r in harness.journal("tm_event") if r.get("type") == "reacquire_hint"][0]
        self.assertEqual(hint_event["f_last"], escalation_frame)
        before = len(harness.receipts())
        f_ready = harness.publish(1)  # 新载体就绪（帧号 = 本帧）
        started = harness.journal("resident_loop_started")[-1]
        self.assertEqual(started["reacquire_window"]["f_ready"], f_ready)
        window = harness.journal("reacquire_started")[0]
        self.assertEqual((window["f_ready"], window["m_ready"]), (f_ready, started["reacquire_window"]["m_ready"]))
        self.assertEqual((harness.session.state, harness.session.reason), ("REINIT_REQUIRED", "reacquiring"))
        harness.publish(1)
        commit_frame = harness.publish(1)
        done = harness.journal("reacquired_after_rebuild")
        self.assertEqual([(r["frame_id"], r["track_key"]) for r in done], [(commit_frame, 5)])
        self.assertEqual((harness.session.state, harness.session.reason), ("TRACKING", "rebuild_reacquired"))
        self.assertNotEqual(harness.session.track_id, old_token)
        self.assertEqual((manager.binding.relation, manager.binding.origin, manager.binding.target_episode_id),
                         ("REBUILD_REACQUIRE", "reacquire", old_episode + 1))
        self.assertEqual((manager.task, manager.intent_revision), (old_task, 1))
        self.assertEqual(harness.session.resident_rebuilds, 1)
        # 窗口内（就绪帧到提交帧之前）：零 look_at/预测云台/速度，每个最新帧恰一次 hold（载体起点显式 hold 另计）。
        after = harness.receipts()[before:]
        cut = next(i for i, r in enumerate(after) if r["frame_id"] == commit_frame)
        window_receipts = after[:cut]
        self.assertFalse([r for r in window_receipts if r["channel"] in ("look_at", "predicted_look_at", "body_command", "observation")])
        newest = [r["frame_id"] for r in harness.journal("frame_timing") if r["batch_position"] == "newest"
                  and f_ready <= r["frame_id"] < commit_frame]
        per_frame = [r for r in holds(window_receipts) if not r["detail"].get("explicit")]
        self.assertEqual(len(per_frame), len(newest))
        self.assertEqual(newest, list(range(f_ready, commit_frame)))
        self.assertTrue(harness.written("observation", commit_frame))
        harness.publish(1)
        self.assertEqual((harness.session.state, harness.session.reason), ("TRACKING", None))
        # 重放：只读落盘输入与两份配置，事件逐条相同（含提示、窗口、逐帧合成先验与提交）。
        replayed = tm.replay_tm_inputs(harness.session.session_dir / tm.INPUTS_FILE, tm.DEFAULT_CAPTURE_CONFIG,
                                       harness.session.config.fastfix_config)
        self.assertEqual(json.loads(json.dumps(replayed)), json.loads(json.dumps(manager.events)))

    def test_no_candidate_fails_on_frame_deadline_and_reports(self):
        harness = reacq_harness(self, [steady(), lambda f: []], self.dir, t_reacq=3)
        escalate_session(harness)
        harness.publish(4)
        failed = harness.journal("reacquire_failed")
        self.assertEqual(failed[0]["cause"], "deadline_frame")
        self.assertEqual((harness.session.state, harness.session.reason), ("REINIT_REQUIRED", "reacquire_failed"))
        self.assertEqual(harness.session.target_manager.runtime.phase, "CANCELED")

    def test_zero_new_frame_tick_expires_by_monotonic(self):
        harness = reacq_harness(self, [steady(), lambda f: []], self.dir)
        escalate_session(harness)
        harness.publish(1)
        self.assertTrue(harness.session.target_manager.reacquire_open)
        harness.tick(1, advance_s=2.5)
        failed = harness.journal("reacquire_failed")
        self.assertEqual(failed[0]["cause"], "deadline_monotonic")
        self.assertEqual(harness.session.reason, "reacquire_failed")

    def test_ambiguous_candidates_report(self):
        two = lambda f: [(5, TRACKED, box_px(300, 240)), (6, TRACKED, box_px(303, 240))]
        harness = reacq_harness(self, [steady(), two], self.dir)
        escalate_session(harness)
        harness.publish(3)
        self.assertEqual(harness.journal("reacquire_failed")[0]["reason"], "reacquire_ambiguous")
        self.assertEqual(harness.session.reason, "reacquire_ambiguous")

    def test_click_during_window_cancels_hint_then_runs_click(self):
        plan = lambda f: [(5, TRACKED, box_px(300, 240)), (9, TRACKED, box_px(500, 100))]
        harness = reacq_harness(self, [steady(), plan], self.dir)
        escalate_session(harness)
        f_ready = harness.publish(1)
        harness.publish(1, tick=False)
        receipt = harness.click(500, 100, f_ready)
        self.assertEqual(receipt["outcome"], "APPLIED")
        manager = harness.session.target_manager
        self.assertEqual(harness.journal("reacquire_canceled")[0]["reason"], "user_click")
        self.assertEqual((manager.binding.track_key, manager.binding.relation, manager.binding.origin), (9, "INITIAL", "click"))
        self.assertEqual((manager.runtime.phase, manager.intent_revision), ("TRACKING", 2))
        self.assertEqual(harness.session.state, "TRACKING")
        harness.publish(2)
        self.assertFalse(harness.journal("reacquired_after_rebuild"))

    def test_rejected_click_during_window_keeps_task_state(self):
        """C1-3（首次接受释义 1）：窗口内拒收点击只作废提示/缓冲，任务终态由现行拒收事务决定 = 零状态变化：
        TaskSpec、runtime、version、绑定、intent_revision、episode_seq 与点击前逐字段相同；不再自动重捕。
        修前：finally 中 `release_binding(cancel_task=True)` 把任务置 CANCELED、version 递增（红）。"""
        harness = reacq_harness(self, self.plans(), self.dir)
        escalate_session(harness)
        f_ready = harness.publish(1)
        manager = harness.session.target_manager

        def snapshot():
            return (manager.task, manager.runtime, manager.version, manager.binding, manager.intent_revision,
                    manager.episode_seq)

        before = snapshot()
        self.assertEqual(before[1].phase, "ACQUIRING")
        harness.click(5, 5, f_ready)  # NO_TRACK_AT_K
        self.assertEqual(snapshot(), before)
        self.assertEqual(harness.journal("reacquire_canceled")[-1]["reason"], "user_click")
        self.assertEqual((harness.session.state, harness.session.reason), ("REINIT_REQUIRED", "publish_expired"))
        harness.publish(3)
        self.assertFalse(harness.journal("reacquired_after_rebuild"))
        self.assertEqual(snapshot(), before)

    def test_stop_and_release_take_priority_over_auto(self):
        harness = reacq_harness(self, self.plans(), self.dir)
        token = harness.session.track_id
        escalate_session(harness)
        harness.publish(2)
        harness.publisher.publish(b"same-tick")
        receipt = harness.request("release", token=token)  # 请求先于本帧（同一 tick）
        self.assertEqual(receipt["outcome"], "APPLIED")
        self.assertEqual((harness.session.state, harness.session.reason), ("LOST", "operator_release"))
        self.assertEqual(harness.journal("reacquire_canceled")[0]["reason"], "operator_release")
        self.assertFalse(harness.journal("reacquired_after_rebuild"))

        harness = reacq_harness(self, self.plans(), self.dir)
        escalate_session(harness)
        harness.publish(2)
        harness.publisher.publish(b"same-tick")
        harness.request("stop")
        self.assertEqual(harness.session.state, "TERMINAL")
        self.assertEqual(harness.journal("reacquire_canceled")[0]["reason"], "operator_stop")
        self.assertFalse(harness.journal("reacquired_after_rebuild"))

    def test_release_token_mismatch_rejected(self):
        harness = reacq_harness(self, self.plans(), self.dir)
        escalate_session(harness)
        harness.publish(1)
        receipt = harness.request("release", token="wrong")
        self.assertEqual(receipt["outcome"], "REQUEST_INVALID")
        self.assertTrue(harness.session.target_manager.reacquire_open)

    def test_off_arm_and_non_timing_teardown_keep_current_path(self):
        harness = reacq_harness(self, self.plans(), self.dir, auto="off")
        escalate_session(harness)
        harness.publish(3)
        self.assertEqual(harness.journal("reacquire_skipped")[0]["reason"], "auto_reacquire_off")
        self.assertFalse(harness.journal("reacquire_started"))
        self.assertEqual((harness.session.state, harness.session.target_manager.runtime.phase), ("REINIT_REQUIRED", "CANCELED"))
        harness = reacq_harness(self, self.plans(), self.dir)
        harness.publish(1)
        harness.tick(1, advance_s=3.5)  # frame_stall 拆载体：不是时序升级
        self.assertEqual(harness.journal("reacquire_skipped")[0]["reason"], "not_timing_escalation")
        self.assertEqual(harness.session.reason, "frame_stall")

    def test_rebuild_limit_cancels_hint(self):
        harness = reacq_harness(self, [steady()], self.dir)
        harness.session.resident_rebuilds = 2  # 第 3 次需重建 → TERMINAL(rebuild_limit)
        escalate_session(harness)
        self.assertEqual((harness.session.state, harness.session.reason), ("TERMINAL", "rebuild_limit"))
        self.assertEqual(harness.journal("reacquire_canceled")[0]["reason"], "rebuild_limit")


if __name__ == "__main__":
    unittest.main()
