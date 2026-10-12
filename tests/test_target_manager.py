#!/usr/bin/env python3
"""P1-ENG-CAPTURE-001 AC-4/5/6/7/8/15（K2/K3）：目标管理器的 TaskSpec、连续性、收养、提交事务、授权与重放。

全部零模型：历史帧由 `resident_core` 生产数据结构（`HistoryEntry`/`TrackRow`/`KfSnapshot`/`RawDetection`）构造；
绑定端口用生产 `ResidentCore`（指针、coasting、快照三件套）。
"""

from __future__ import annotations

import ast
import importlib.util
from dataclasses import FrozenInstanceError, replace
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import target_manager as tm  # noqa: E402
from controller.resident_core import (  # noqa: E402
    KF_POSTERIOR,
    KF_PRIOR,
    LOST,
    TRACKED,
    UNCONFIRMED,
    HistoryEntry,
    RawDetection,
    ResidentCore,
    TrackRow,
    make_kf_snapshot,
)

W, H = 640, 480
QUAT_DOWN = [0.38268343, 0.0, 0.0, 0.92387953]  # 绕 x 轴 45°：前向朝下斜视（与 pose_gmc 约定一致）


def snap(frame_id, key, xywh, phase, cov=(25.0, 25.0), vel=(0.0, 0.0)):
    return make_kf_snapshot(frame_id, frame_id, key, phase, xywh, vel, ((cov[0], 0.0), (0.0, cov[1])))


class Frame:
    """一帧的构造器：行 = (key, state, 像素 xyxy, det_index)，检测 = 像素 xyxy 列表，prior/post = key → xywh。"""

    def __init__(self, frame_id):
        self.frame_id = frame_id
        self.rows = []
        self.dets = []
        self.priors = {}
        self.posts = {}
        self.removed = []
        self.priors_available = True

    def det(self, box):
        self.dets.append(RawDetection(len(self.dets), tuple(float(v) for v in box), 0.9, 0))
        return len(self.dets) - 1

    def row(self, key, state, box, *, detect=True, prior=None, post=None, prior_cov=(25.0, 25.0)):
        index = self.det(box) if detect and state != LOST else -1
        x1, y1, x2, y2 = box
        norm = (x1 / W, y1 / H, (x2 - x1) / W, (y2 - y1) / H)
        center = ((x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1)
        self.priors[key] = snap(self.frame_id, key, prior if prior is not None else center, KF_PRIOR, prior_cov)
        post_box = post if post is not None else center
        self.posts[key] = snap(self.frame_id, key, post_box, KF_POSTERIOR if index >= 0 else KF_PRIOR)
        self.rows.append((key, state, norm, index))
        return self

    def entry(self):
        rows = tuple(
            TrackRow(key, norm, 0.9, 0, state, index, False, self.posts.get(key), None) for key, state, norm, index in self.rows
        )
        return HistoryEntry(
            frame_id=self.frame_id,
            simulation_time_s=self.frame_id * 0.2,
            capture_monotonic_s=100.0 + self.frame_id * 0.2,
            camera_position_world_m=(0.0, 25.0, 0.0),
            camera_rotation_xyzw=tuple(QUAT_DOWN),
            intrinsics_px={"fx": 415.692, "fy": 415.692, "cx": 320.0, "cy": 240.0},
            library_frame_id=self.frame_id,
            tracks=rows,
            removed_ids=tuple(self.removed),
            width=W,
            height=H,
            raw_detections=tuple(self.dets),
            prior_snapshots=tuple(self.priors.values()) if self.priors_available else (),
            post_snapshots=tuple(self.posts.values()),
            priors_available=self.priors_available,
        )


def box_at(cx, cy, w=60.0, h=40.0):
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def manager(params=None, mode="capture", inputs=None, sink=None):
    m = tm.TargetManager(params or tm.CaptureParams(), mode=mode, config_sha256="0" * 64, inputs=inputs, sink=sink)
    core = ResidentCore(100)
    m.attach_port(core)
    return m, core


class History(dict):
    def __call__(self, frame_id):
        return self.get(frame_id)


def bind_by_click(m, history, key, k, head, x, y):
    return m.click(request_id=f"click-{k}-{head}", x_px=x, y_px=y, frame_id=k, image_sha256="a" * 64,
                   history=history, head_frame_id=head, actual_image_sha256="a" * 64)


def track_target(m, history, frames):
    """frames: [(frame_id, Frame)] → 逐帧 on_frame（每帧都是本批最新帧）。"""
    outcomes = []
    for f, frame in frames:
        entry = frame.entry()
        history[f] = entry
        outcomes.append(m.on_frame(entry, newest=True))
    return outcomes


def start_tracking(m, core, *, key=1, cx=300.0, cy=240.0, others=()):
    """帧 9–10 key 稳定 tracked，帧 10 点击绑定（k=9，提交帧 10）。"""
    history = History()
    for f in (9, 10):
        frame = Frame(f).row(key, TRACKED, box_at(cx, cy))
        for other_key, other_box in others:
            frame.row(other_key, TRACKED, other_box)
        history[f] = frame.entry()
    word, commit, _info = bind_by_click(m, history, key, 9, 10, cx, cy)
    assert word == "BOUND", (word, commit)
    return history


class TaskSpecTests(unittest.TestCase):
    def test_taskspec_immutable_and_click_legal_shape(self):
        spec = tm.TaskSpec.click(tm.ClickSelector(1.0, 2.0, 3, "a" * 64), 1)
        with self.assertRaises(FrozenInstanceError):
            spec.intent_revision = 5  # type: ignore[misc]
        with self.assertRaises(tm.TaskSpecInvalid):
            tm.TaskSpec(tm.ClickSelector(1.0, 2.0, 3, "a" * 64), "INSTANCE", "WAIT", "ASK", "ASK", 1, "pred")

    def test_taskspec_language_compat_only_from_compat_path(self):
        selector = tm.LanguageCompatSelector(1, (0.1, 0.1, 0.2, 0.2), 5)
        with self.assertRaises(tm.TaskSpecInvalid):
            tm.TaskSpec(selector, "INSTANCE", "NOW", "ASK", "ASK", 1)
        self.assertEqual(tm.TaskSpec._language_compat(selector, 1).selector, selector)

    def test_taskspec_rearm_and_wait_without_predicate_rejected(self):
        selector = tm.ClickSelector(1.0, 2.0, 3, "a" * 64)
        with self.assertRaises(tm.TaskSpecInvalid):
            tm.TaskSpec(selector, "INSTANCE", "REARM", "ASK", "ASK", 1)
        with self.assertRaises(tm.TaskSpecInvalid):
            tm.TaskSpec(selector, "INSTANCE", "WAIT", "ASK", "ASK", 1)
        with self.assertRaises(tm.TaskSpecInvalid):
            tm.TaskSpec(selector, "DESCRIPTION", "NOW", "ASK", "ASK", 1)

    def test_taskspec_counters_click_and_rejected_click(self):
        m, core = manager()
        history = start_tracking(m, core)
        self.assertEqual((m.intent_revision, m.episode_seq, m.binding.association_revision, m.binding.relation), (1, 1, 0, "INITIAL"))
        # 被拒点击（k 不在历史）：两者不变。
        word, _commit, _ = m.click(request_id="r", x_px=1.0, y_px=1.0, frame_id=99, image_sha256="b" * 64,
                                   history=history, head_frame_id=10)
        self.assertEqual(word, tm.FRAME_NOT_IN_HISTORY)
        self.assertEqual((m.intent_revision, m.episode_seq), (1, 1))
        # 重选成功：新 TaskSpec、新 episode、USER_RESELECT。
        frame = Frame(11).row(1, TRACKED, box_at(300, 240)).row(2, TRACKED, box_at(500, 300))
        history[11] = frame.entry()
        frame = Frame(12).row(1, TRACKED, box_at(300, 240)).row(2, TRACKED, box_at(500, 300))
        history[12] = frame.entry()
        word, _commit, _ = bind_by_click(m, history, 2, 11, 12, 500, 300)
        self.assertEqual(word, "BOUND")
        self.assertEqual((m.intent_revision, m.episode_seq, m.binding.relation, m.binding.track_key), (2, 2, "USER_RESELECT", 2))

    def test_taskspec_counter_matrix_compat_and_release(self):
        m, core = manager(mode="compat")
        selector = tm.LanguageCompatSelector(1, (0.1, 0.1, 0.2, 0.2), 5)
        result = m.commit_binding(origin="lang_confirm", track_key=4, expected_version=m.version, source_frame=5,
                                  commit_frame=6, selector=selector, coasting_designation_id=1)
        self.assertTrue(result.accepted)
        self.assertEqual((m.intent_revision, m.episode_seq, m.binding.association_revision), (1, 1, 0))
        self.assertEqual(core.coasting, {"designation_id": 1, "steps": 0})
        # TRACK_ENDED → acquire：intent +1，不分配 episode；旧绑定由 release 关闭（不重复关闭）。
        self.assertTrue(m.release_binding("operator_release", cancel_task=False))
        self.assertFalse(m.release_binding("operator_release", cancel_task=False))
        closes = [e for e in m.events if e["type"] == "episode_closed"]
        self.assertEqual(len(closes), 1)
        m.accept_language_task(tm.LanguageCompatSelector(2, (0.3, 0.3, 0.1, 0.1), 8), frame_id=8)
        self.assertEqual((m.intent_revision, m.episode_seq, m.binding), (2, 1, None))
        result = m.commit_binding(origin="lang_acquire", track_key=9, expected_version=m.version, source_frame=None, commit_frame=12)
        self.assertTrue(result.accepted)
        self.assertEqual((m.intent_revision, m.episode_seq, m.binding.association_revision, m.binding.origin), (2, 2, 0, "lang_acquire"))
        # 模式外 origin 被拒且零变化。
        version = m.version
        result = m.commit_binding(origin="click", track_key=3, expected_version=version, source_frame=1, commit_frame=1,
                                  selector=tm.ClickSelector(1.0, 1.0, 1, "c" * 64))
        self.assertEqual((result.accepted, result.reason, m.version, m.binding.track_key), (False, "origin_not_allowed_in_mode", version, 9))
        m.on_teardown("frame_stall")
        self.assertEqual((m.intent_revision, m.episode_seq, m.binding), (2, 2, None))


class ContinuityTests(unittest.TestCase):
    def test_only_transition_writes_continuity_static(self):
        """AC-5 静态检查：`continuity_status` 的写入（关键字参数或属性赋值）只出现在 `transition` 内。"""
        offenders = []
        for path in sorted((PROJECT_ROOT / "controller").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for inner in ast.walk(node):
                        hit = False
                        if isinstance(inner, ast.keyword) and inner.arg == "continuity_status":
                            hit = True
                        if isinstance(inner, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                            targets = inner.targets if isinstance(inner, ast.Assign) else [inner.target]
                            hit = hit or any(isinstance(t, ast.Attribute) and t.attr == "continuity_status" for t in targets)
                        if hit and not (path.name == "target_manager.py" and node.name == "transition"):
                            offenders.append(f"{path.name}:{node.name}:{inner.lineno}")
        self.assertEqual(offenders, [])

    def test_regain_within_window_one_frame(self):
        m, core = manager()
        history = start_tracking(m, core)
        track_target(m, history, [(11, Frame(11).row(1, LOST, box_at(300, 240)))])
        self.assertEqual((m.belief.continuity_status, m.belief.observation_status), (tm.TENTATIVE, tm.PREDICTED))
        outcome = track_target(m, history, [(12, Frame(12).row(1, TRACKED, box_at(302, 240)))])[0]
        self.assertEqual((m.belief.continuity_status, m.belief.observation_status, m.belief.t0), (tm.SUPPORTED, tm.OBSERVED, 12))
        self.assertEqual((outcome.effect.body, outcome.effect.gimbal), (tm.FOLLOW, tm.GIMBAL_OBSERVED))

    def test_dispute_locked_then_small_innovation_no_follow(self):
        """#1：锁存争议后原 ID 又以小创新匹配 → 不清争议、不恢复 FOLLOW。"""
        m, core = manager()
        history = start_tracking(m, core)
        frame = Frame(11).row(1, TRACKED, box_at(300, 240)).row(7, UNCONFIRMED, box_at(301, 240))
        outcome = track_target(m, history, [(11, frame)])[0]
        self.assertEqual(m.belief.continuity_status, tm.DISPUTED)
        self.assertEqual(outcome.projection, ("SUSPECTED", tm.REASON_DISPUTED))
        self.assertEqual(m.belief.t0, 10)  # 规范化为未接受该帧
        outcome = track_target(m, history, [(12, Frame(12).row(1, TRACKED, box_at(300, 240)))])[0]
        self.assertEqual(m.belief.continuity_status, tm.DISPUTED)
        self.assertEqual((outcome.effect.body, outcome.effect.gimbal), (tm.HOLD, tm.GIMBAL_NONE))

    def test_expired_then_original_reappears_not_followed(self):
        """#2：age ≥ T_repair 后原 ID 重现 → 不续跟。"""
        m, core = manager()
        history = start_tracking(m, core)
        frames = [(f, Frame(f).row(1, LOST, box_at(300, 240))) for f in range(11, 15)]
        track_target(m, history, frames)
        outcome = track_target(m, history, [(15, Frame(15).row(1, TRACKED, box_at(300, 240)))])[0]
        self.assertEqual(m.belief.continuity_status, tm.BROKEN)
        self.assertEqual(outcome.projection, ("SUSPECTED", tm.REASON_BROKEN))
        self.assertEqual((outcome.effect.body, outcome.effect.gimbal), (tm.HOLD, tm.GIMBAL_NONE))
        outcome = track_target(m, history, [(16, Frame(16).row(1, TRACKED, box_at(300, 240)))])[0]
        self.assertEqual((m.belief.continuity_status, outcome.effect.body), (tm.BROKEN, tm.HOLD))

    def test_posterior_close_but_prior_innovation_large_not_accepted(self):
        """AR1-2：匹配后 posterior 看似近、但同帧 prior 创新过大 → 不刷新 t0、不 FOLLOW。"""
        m, core = manager()
        history = start_tracking(m, core)
        frame = Frame(11).row(1, TRACKED, box_at(380, 240), prior=(300.0, 240.0, 60.0, 40.0), post=(379.0, 240.0, 60.0, 40.0))
        outcome = track_target(m, history, [(11, frame)])[0]
        self.assertEqual((m.belief.t0, m.belief.observation_status, m.belief.continuity_status), (10, tm.PREDICTED, tm.TENTATIVE))
        self.assertNotEqual(outcome.effect.body, tm.FOLLOW)

    def test_missing_prior_fail_closed(self):
        m, core = manager()
        history = start_tracking(m, core)
        frame = Frame(11).row(1, TRACKED, box_at(300, 240))
        frame.priors_available = False
        outcome = track_target(m, history, [(11, frame)])[0]
        self.assertEqual((m.belief.t0, m.belief.continuity_status), (10, tm.TENTATIVE))
        self.assertNotEqual(outcome.effect.body, tm.FOLLOW)

    # --- C1返工 C1-1（AR1-2 修订 1：KF 消费 fail-closed；修前必失败的具名回归） ---------------------------

    def assert_fail_closed_frame(self, outcome, m, *, t0=10):
        """本帧观测不被接受（不刷新 t0、非 OBSERVED）、云台不发（观测与预测都不发）、机身 HOLD。"""
        self.assertEqual(m.belief.t0, t0)
        self.assertNotEqual(m.belief.observation_status, tm.OBSERVED)
        self.assertEqual((outcome.effect.body, outcome.effect.gimbal), (tm.HOLD, tm.GIMBAL_NONE))
        self.assertIsNone(outcome.effect.aim_point_world_m)

    def test_c1_1_matched_original_with_misaligned_or_missing_prior_not_accepted(self):
        """原匹配成功路径：prior 错传感器帧/错库帧/错阶段/无效/缺失/整帧未提供 → 不接受、不刷新 t0、云台不发、HOLD。
        修前 `HistoryEntry.prior` 只核键、门只核 valid：错帧/错阶段 prior 照样过门并 FOLLOW；整帧缺 prior 时
        `_miss_original` 还可凭有效 post 发预测云台。"""
        cases = {
            "wrong_sensor_frame": lambda fr: fr.priors.__setitem__(1, make_kf_snapshot(10, 11, 1, KF_PRIOR, (300.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((25.0, 0.0), (0.0, 25.0)))),
            "wrong_library_frame": lambda fr: fr.priors.__setitem__(1, make_kf_snapshot(11, 3, 1, KF_PRIOR, (300.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((25.0, 0.0), (0.0, 25.0)))),
            "wrong_phase": lambda fr: fr.priors.__setitem__(1, make_kf_snapshot(11, 11, 1, KF_POSTERIOR, (300.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((25.0, 0.0), (0.0, 25.0)))),
            "invalid": lambda fr: fr.priors.__setitem__(1, make_kf_snapshot(11, 11, 1, KF_PRIOR, (300.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((1.0, 2.0), (2.0, 1.0)))),
            "missing_key": lambda fr: fr.priors.pop(1),
            "frame_without_priors": lambda fr: setattr(fr, "priors_available", False),
        }
        for name, corrupt in cases.items():
            with self.subTest(name=name):
                m, core = manager()
                history = start_tracking(m, core)
                frame = Frame(11).row(1, TRACKED, box_at(300, 240))
                corrupt(frame)
                outcome = track_target(m, history, [(11, frame)])[0]
                self.assert_fail_closed_frame(outcome, m)
                self.assertEqual(m.belief.continuity_status, tm.TENTATIVE)

    def test_c1_1_matched_original_with_invalid_or_missing_post_not_accepted(self):
        """原匹配成功但同帧 post 缺失/无效/错帧/非 posterior（AR1-2：post 无效同样不授权）→ 不接受、不刷新 t0、
        不 FOLLOW、云台不发。修前 `_accept_original` 在 post 缺失/无效时仍刷新 t0、标 OBSERVED，授权按 within 放行。"""
        cases = {
            "invalid": lambda fr: fr.posts.__setitem__(1, make_kf_snapshot(11, 11, 1, KF_POSTERIOR, (300.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((float("nan"), 0.0), (0.0, 25.0)))),
            "missing": lambda fr: fr.posts.pop(1),
            "wrong_frame": lambda fr: fr.posts.__setitem__(1, make_kf_snapshot(10, 10, 1, KF_POSTERIOR, (300.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((25.0, 0.0), (0.0, 25.0)))),
            "not_posterior": lambda fr: fr.posts.__setitem__(1, make_kf_snapshot(11, 11, 1, KF_PRIOR, (300.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((25.0, 0.0), (0.0, 25.0)))),
        }
        for name, corrupt in cases.items():
            with self.subTest(name=name):
                m, core = manager()
                history = start_tracking(m, core)
                frame = Frame(11).row(1, TRACKED, box_at(300, 240))
                corrupt(frame)
                outcome = track_target(m, history, [(11, frame)])[0]
                self.assert_fail_closed_frame(outcome, m)

    def test_c1_1_lost_original_without_valid_prior_has_no_predicted_gimbal(self):
        """lost 路径：原键同帧 prior 缺失/错帧/无效 → 云台不发（不得凭有效 post 发预测 look_at）、机身 HOLD；
        同帧有效 prior → 照常行 7 预测。修前缺 prior 时预测中心取 post，行 7 照发。"""
        cases = {
            "frame_without_priors": lambda fr: setattr(fr, "priors_available", False),
            "wrong_sensor_frame": lambda fr: fr.priors.__setitem__(1, make_kf_snapshot(10, 11, 1, KF_PRIOR, (300.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((25.0, 0.0), (0.0, 25.0)))),
            "invalid": lambda fr: fr.priors.__setitem__(1, make_kf_snapshot(11, 11, 1, KF_PRIOR, (300.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((1.0, 2.0), (2.0, 1.0)))),
        }
        for name, corrupt in cases.items():
            with self.subTest(name=name):
                m, core = manager()
                history = start_tracking(m, core)
                frame = Frame(11).row(1, LOST, box_at(300, 240))
                corrupt(frame)
                outcome = track_target(m, history, [(11, frame)])[0]
                self.assert_fail_closed_frame(outcome, m)
                self.assertIn(outcome.effect.authorization_row, (5, 8))  # 无有效预测中心：不落行 7
        with self.subTest(name="aligned_prior_predicts"):
            m, core = manager()
            history = start_tracking(m, core)
            outcome = track_target(m, history, [(11, Frame(11).row(1, LOST, box_at(300, 240)))])[0]
            self.assertEqual((outcome.effect.authorization_row, outcome.effect.gimbal), (7, tm.GIMBAL_PREDICTED))
            self.assertEqual((m.belief.predicted["sensor_frame_id"], m.belief.predicted["phase"]), (11, KF_PRIOR))

    def test_c1_1_click_with_invalid_head_post_rejected_keeps_old_target(self):
        """点击新实例以当前有效 post 初始化（AR1-2）：提交帧 post 无效/错帧 → 拒绝（零状态变化、旧目标继续）。
        修前照常提交，信念 OBSERVED 而 post 无效，授权仍按 within 放行 FOLLOW。"""
        for name in ("invalid", "wrong_frame"):
            with self.subTest(name=name):
                m, core = manager()
                history = start_tracking(m, core)
                frame = Frame(11).row(1, TRACKED, box_at(300, 240)).row(2, TRACKED, box_at(500, 300))
                if name == "invalid":
                    frame.posts[2] = make_kf_snapshot(11, 11, 2, KF_POSTERIOR, (500.0, 300.0, 60.0, 40.0), (0.0, 0.0), ((1.0, 2.0), (2.0, 1.0)))
                else:
                    frame.posts[2] = make_kf_snapshot(9, 9, 2, KF_POSTERIOR, (500.0, 300.0, 60.0, 40.0), (0.0, 0.0), ((25.0, 0.0), (0.0, 25.0)))
                history[11] = frame.entry()
                snapshot = m._business_snapshot()
                word, commit, _ = bind_by_click(m, history, 2, 11, 11, 500, 300)
                self.assertEqual((word, commit), ("kf_post_invalid", None))
                self.assertTrue(m._business_matches(snapshot))
                self.assertEqual((core.pointer(), m.binding.track_key), (1, 1))

    def _original_rematch(self, original_dx, competitor=None, *, params=None, others=(), configure=None):
        """原键 1 本帧 tracked、检测横移 `original_dx`；可选竞争键 (key, state, dx, detect)。prior 中心 (300,240)、
        P_pos = diag(16,16) → S = diag(25,20)（w=60,h=40）。返回 (outcome, m)。"""
        m, core = manager(params=params)
        history = start_tracking(m, core, others=others)
        frame = Frame(11).row(1, TRACKED, box_at(300 + original_dx, 240), prior=(300.0, 240.0, 60.0, 40.0), prior_cov=(16.0, 16.0))
        if competitor is not None:
            key, state, dx, detect = competitor
            frame.row(key, state, box_at(300 + dx, 240), detect=detect)
        if configure is not None:
            configure(frame)
        return track_target(m, history, [(11, frame)])[0], m

    def _nis(self, dx):
        prior = snap(11, 1, (300.0, 240.0, 60.0, 40.0), KF_PRIOR, (16.0, 16.0))
        return tm.motion_size_gate(prior, RawDetection(0, box_at(300 + dx, 240), 0.9, 0), tm.CaptureParams()).nis

    def assert_disputed_locked(self, outcome, m):
        self.assertEqual(m.belief.continuity_status, tm.DISPUTED)
        self.assertEqual(m.belief.t0, 10)  # 锁存时 t0 不刷新
        self.assertEqual((outcome.effect.body, outcome.effect.gimbal), (tm.HOLD, tm.GIMBAL_NONE))

    def assert_accepted(self, outcome, m):
        self.assertEqual((m.belief.continuity_status, m.belief.observation_status, m.belief.t0), (tm.SUPPORTED, tm.OBSERVED, 11))
        self.assertEqual(outcome.effect.body, tm.FOLLOW)

    def test_original_rematch_competition_margin_matrix(self):
        """IR-6：NIS_c − NIS_o < m_nis 即 DISPUTED（小于触发、等于不触发、大于不触发、负差也触发）。"""
        nis_o = self._nis(4.0)
        self.assertGreater(nis_o, 0.0)
        with self.subTest("less"):
            self.assert_disputed_locked(*self._original_rematch(4.0, (7, TRACKED, 6.0, True)))
        with self.subTest("greater"):
            self.assert_accepted(*self._original_rematch(4.0, (7, TRACKED, 13.0, True)))
        with self.subTest("equal"):
            margin = self._nis(12.0) - nis_o  # 以生产门函数算出的差作 m_nis：差恰等于裕度
            outcome, m = self._original_rematch(4.0, (7, TRACKED, 12.0, True), params=replace(tm.CaptureParams(), m_nis=margin))
            self.assert_accepted(outcome, m)
        with self.subTest("negative"):  # 竞争者明显更优（NIS_c < NIS_o）同样撤权
            self.assert_disputed_locked(*self._original_rematch(10.0, (7, TRACKED, 0.0, True)))
        with self.subTest("unconfirmed_competitor"):
            self.assert_disputed_locked(*self._original_rematch(4.0, (7, UNCONFIRMED, 5.0, True)))

    def test_original_rematch_competitor_exclusions(self):
        """IR-6：门 0 排除、无本帧匹配检测、removed/ended 的键不算竞争者；原键缺/失效 prior 不评竞争、不接受。"""
        with self.subTest("gate0"):
            m, core = manager()
            history = start_tracking(m, core, others=((7, box_at(330, 240)),))
            # 帧 11：7 号同帧 tracked（不过原键门，非竞争）→ 原键被接受、门 0 记 7 号同帧跟踪；帧 12：7 号移近（无跳变）仍排除。
            track_target(m, history, [(11, Frame(11).row(1, TRACKED, box_at(300, 240)).row(7, TRACKED, box_at(330, 240)))])
            frame = Frame(12).row(1, TRACKED, box_at(304, 240), prior=(300.0, 240.0, 60.0, 40.0), prior_cov=(16.0, 16.0))
            frame.row(7, TRACKED, box_at(305, 240))
            outcome = track_target(m, history, [(12, frame)])[0]
            self.assertEqual((m.belief.continuity_status, m.belief.t0, outcome.effect.body), (tm.SUPPORTED, 12, tm.FOLLOW))
        with self.subTest("no_detection"):
            self.assert_accepted(*self._original_rematch(4.0, (7, TRACKED, 5.0, False)))
        with self.subTest("removed"):
            self.assert_accepted(*self._original_rematch(4.0, (7, TRACKED, 5.0, True), configure=lambda fr: fr.removed.append(7)))
        with self.subTest("ended"):
            m, core = manager()
            history = start_tracking(m, core)
            core._ended_ids.add(7)  # 生产 ended 集（coasting 到期等）由端口提供
            frame = Frame(11).row(1, TRACKED, box_at(304, 240), prior=(300.0, 240.0, 60.0, 40.0), prior_cov=(16.0, 16.0))
            frame.row(7, TRACKED, box_at(305, 240))
            self.assert_accepted(track_target(m, history, [(11, frame)])[0], m)
        with self.subTest("invalid_prior"):
            def corrupt(fr):
                fr.priors[1] = make_kf_snapshot(11, 11, 1, KF_PRIOR, (300.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((1.0, 2.0), (2.0, 1.0)))
            outcome, m = self._original_rematch(4.0, (7, TRACKED, 5.0, True), configure=corrupt)
            self.assertEqual((m.belief.continuity_status, m.belief.t0), (tm.TENTATIVE, 10))
            self.assertNotEqual(outcome.effect.body, tm.FOLLOW)

    def test_report_fires_exactly_once_at_t_report(self):
        m, core = manager()
        history = start_tracking(m, core)
        frames = [(f, Frame(f).row(1, LOST, box_at(300, 240))) for f in range(11, 15)]
        outcomes = track_target(m, history, frames)
        reports = [e for e in m.events if e["type"] == "report" and e["reason"] == tm.REASON_NO_NEW_OBSERVATION]
        self.assertEqual([e["frame_id"] for e in reports], [13])
        self.assertEqual([o.projection[1] for o in outcomes], ["predicting", "predicting", "no_new_observation", "no_new_observation"])


class RepairTests(unittest.TestCase):
    def test_repair_after_one_empty_frame_and_activated_commit(self):
        """#3：一帧无候选后同一合格候选在 N_adopt 个连续新帧过门、提交帧已激活 → 修复；未确认帧只作证据。"""
        m, core = manager()
        history = start_tracking(m, core)
        track_target(m, history, [(11, Frame(11).row(1, LOST, box_at(300, 240)))])
        outcome = track_target(m, history, [(12, Frame(12).row(1, LOST, box_at(300, 240)).row(8, UNCONFIRMED, box_at(303, 240)))])[0]
        self.assertEqual((m.binding.track_key, outcome.projection), (1, ("TRACKING", "predicting")))
        outcome = track_target(m, history, [(13, Frame(13).row(1, LOST, box_at(300, 240)).row(8, TRACKED, box_at(305, 240)))])[0]
        self.assertEqual((m.binding.track_key, m.binding.relation, m.binding.association_revision), (8, "CONTINUITY_REPAIR", 1))
        self.assertEqual((m.episode_seq, m.intent_revision, core.pointer()), (1, 1, 8))
        self.assertEqual(outcome.projection, ("TRACKING", tm.REASON_REPAIRED))
        self.assertEqual((outcome.effect.body, outcome.effect.gimbal), (tm.FOLLOW, tm.GIMBAL_OBSERVED))

    def test_last_evidence_at_expiry_frame_rejected(self):
        """#4：第 N_adopt 份证据落在 age = T_repair 帧 → 先到期、拒绝。"""
        m, core = manager()
        history = start_tracking(m, core)
        frames = [(f, Frame(f).row(1, LOST, box_at(300, 240))) for f in (11, 12, 13)]
        frames.append((14, Frame(14).row(1, LOST, box_at(300, 240)).row(8, UNCONFIRMED, box_at(303, 240))))
        frames.append((15, Frame(15).row(1, LOST, box_at(300, 240)).row(8, TRACKED, box_at(305, 240))))
        track_target(m, history, frames)
        self.assertEqual((m.belief.continuity_status, m.binding.track_key, core.pointer()), (tm.BROKEN, 1, 1))

    def test_c1_1_repair_with_misaligned_original_prior_never_commits(self):
        """C1-1 修复相关路径：原键同帧 prior 错帧/错阶段 → 本帧不收证据、修复不提交、云台不发。
        修前修复门只核 `prior.valid`，错帧/错阶段 prior 照收证据并在 N_adopt 帧后提交。"""
        cases = {
            "wrong_sensor_frame": lambda fr: fr.priors.__setitem__(1, make_kf_snapshot(fr.frame_id - 1, fr.frame_id, 1, KF_PRIOR, (300.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((25.0, 0.0), (0.0, 25.0)))),
            "wrong_phase": lambda fr: fr.priors.__setitem__(1, make_kf_snapshot(fr.frame_id, fr.frame_id, 1, KF_POSTERIOR, (300.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((25.0, 0.0), (0.0, 25.0)))),
        }
        for name, corrupt in cases.items():
            with self.subTest(name=name):
                m, core = manager()
                history = start_tracking(m, core)
                track_target(m, history, [(11, Frame(11).row(1, LOST, box_at(300, 240)))])
                outcomes = []
                for f, state in ((12, UNCONFIRMED), (13, TRACKED)):
                    frame = Frame(f).row(1, LOST, box_at(300, 240)).row(8, state, box_at(303, 240))
                    corrupt(frame)
                    outcomes += track_target(m, history, [(f, frame)])
                self.assertEqual((m.binding.track_key, m.binding.association_revision, core.pointer()), (1, 0, 1))
                for outcome in outcomes:
                    self.assertEqual((outcome.effect.body, outcome.effect.gimbal), (tm.HOLD, tm.GIMBAL_NONE))
                rejected = [e for e in m.events if e["type"] == "repair_evidence" and e["accepted"] is False]
                self.assertEqual(len(rejected), 2)

    def test_c1_1_repair_commit_requires_valid_candidate_post(self):
        """修复提交帧候选键 post 无效 → 本帧不提交（不授权），绑定不变；修前照常提交并 FOLLOW。"""
        m, core = manager()
        history = start_tracking(m, core)
        track_target(m, history, [(11, Frame(11).row(1, LOST, box_at(300, 240)))])
        track_target(m, history, [(12, Frame(12).row(1, LOST, box_at(300, 240)).row(8, UNCONFIRMED, box_at(303, 240)))])
        frame = Frame(13).row(1, LOST, box_at(300, 240)).row(8, TRACKED, box_at(305, 240))
        frame.posts[8] = make_kf_snapshot(13, 13, 8, KF_POSTERIOR, (305.0, 240.0, 60.0, 40.0), (0.0, 0.0), ((1.0, 2.0), (2.0, 1.0)))
        outcome = track_target(m, history, [(13, frame)])[0]
        self.assertEqual((m.binding.track_key, core.pointer()), (1, 1))
        self.assertNotEqual(outcome.effect.body, tm.FOLLOW)
        self.assertNotEqual(outcome.projection, ("TRACKING", tm.REASON_REPAIRED))

    def test_unkeyed_detection_never_commits(self):
        m, core = manager()
        history = start_tracking(m, core)
        frames = []
        for f in range(11, 15):
            frame = Frame(f).row(1, LOST, box_at(300, 240))
            frame.det(box_at(302, 240))
            frames.append((f, frame))
        track_target(m, history, frames)
        self.assertEqual(m.binding.track_key, 1)
        diagnostics = [e for e in m.events if e["type"] == "repair_evidence" and e.get("unkeyed_detections")]
        self.assertTrue(diagnostics)

    def test_gate0_excludes_co_tracked_vehicle(self):
        m, core = manager()
        history = start_tracking(m, core, others=((5, box_at(330, 240)),))
        track_target(m, history, [(11, Frame(11).row(1, TRACKED, box_at(300, 240)).row(5, TRACKED, box_at(330, 240)))])
        frames = [(12, Frame(12).row(1, LOST, box_at(300, 240)).row(5, TRACKED, box_at(305, 240))),
                  (13, Frame(13).row(1, LOST, box_at(300, 240)).row(5, TRACKED, box_at(306, 240)))]
        track_target(m, history, frames)
        self.assertEqual(m.binding.track_key, 1)

    def test_two_candidates_close_nis_disputed(self):
        m, core = manager()
        history = start_tracking(m, core)
        track_target(m, history, [(11, Frame(11).row(1, LOST, box_at(300, 240)))])
        frame = Frame(12).row(1, LOST, box_at(300, 240)).row(8, UNCONFIRMED, box_at(303, 240)).row(9, UNCONFIRMED, box_at(297, 240))
        outcome = track_target(m, history, [(12, frame)])[0]
        self.assertEqual(m.belief.continuity_status, tm.DISPUTED)
        self.assertEqual(outcome.projection, ("SUSPECTED", tm.REASON_DISPUTED))

    def test_structure_constraints_reject_config(self):
        for kwargs in ({"t_pred": 5, "t_repair": 5}, {"n_adopt": 1}, {"t_report": 5}, {"t_repair": 4}, {"rho_click": 1.0}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(tm.CaptureConfigInvalid):
                    tm.CaptureParams(**kwargs)
        params, sha, text = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)
        self.assertEqual((params.t_report, params.n_adopt, params.rho_click, params.t_pred, params.t_repair), (3, 2, 1.5, 4, 5))
        document = json.loads(text)
        document["params"]["t_pred_frames"]["value"] = 5
        with self.assertRaises(tm.CaptureConfigInvalid):
            tm.params_from_document(document)
        document = json.loads(text)
        document["params"]["g_motion"]["category"] = "design_budget"
        with self.assertRaises(tm.CaptureConfigInvalid):
            tm.params_from_document(document)


class _FaultyCore(ResidentCore):
    """`follow(new)` 先改指针再抛（半改替身）；可另注入复原/恢复/读回失败。"""

    def __init__(self, fail_on, *, fail_old=False, fail_restore=False, mismatch=False):
        super().__init__(100)
        self.fail_on, self.fail_old, self.fail_restore, self.mismatch = fail_on, fail_old, fail_restore, mismatch
        self.faulted = False

    def follow(self, track_id):
        if track_id == self.fail_on:
            self._pointer = track_id
            self._coasting = None
            self.faulted = True
            raise RuntimeError("half-applied follow")
        if self.fail_old and self.faulted:
            raise RuntimeError("restore follow failed")
        super().follow(track_id)

    def restore_binding_state(self, snapshot):
        if self.fail_restore:
            raise RuntimeError("coasting restore failed")
        super().restore_binding_state(snapshot)

    def binding_state_matches(self, snapshot):
        return False if self.mismatch else super().binding_state_matches(snapshot)


def compat_with_coasting(core):
    m = tm.TargetManager(tm.CaptureParams(), mode="compat", config_sha256="0" * 64)
    m.attach_port(core)
    selector = tm.LanguageCompatSelector(1, (0.1, 0.1, 0.2, 0.2), 5)
    assert m.commit_binding(origin="lang_confirm", track_key=4, expected_version=0, source_frame=5, commit_frame=6,
                            selector=selector, coasting_designation_id=1).accepted
    core._coasting["steps"] = 3  # 旧 coasting 非空且 steps > 0
    return m


class CommitTests(unittest.TestCase):
    def test_resolve_designation_pure(self):
        core = ResidentCore(100)
        row = TrackRow(3, (0.4, 0.4, 0.1, 0.1), 0.9, 0, TRACKED)
        core.record(1, {}, [row], [], [], 1)
        before = core.snapshot_binding_state()
        designation = core.resolve_designation((0.4, 0.4, 0.1, 0.1), 1, None, 77)
        self.assertEqual((designation.result, designation.track_id, designation.designation_id), ("BOUND", 3, 77))
        self.assertTrue(core.binding_state_matches(before))

    def test_half_applied_follow_restores_full_state(self):
        core = _FaultyCore(fail_on=9)
        m = compat_with_coasting(core)
        business = m._business_snapshot()
        core_state = core.snapshot_binding_state()
        result = m.commit_binding(origin="lang_confirm", track_key=9, expected_version=m.version, source_frame=7,
                                  commit_frame=8, selector=tm.LanguageCompatSelector(2, (0.5, 0.5, 0.1, 0.1), 7))
        self.assertEqual((result.accepted, result.reason, result.fail_closed), (False, "follow_failed", False))
        self.assertTrue(core.binding_state_matches(core_state))
        self.assertEqual(core.coasting, {"designation_id": 1, "steps": 3})
        self.assertTrue(m._business_matches(business))
        self.assertEqual((core.pointer(), m.binding.track_key), (4, 4))

    def test_rollback_failures_fail_closed(self):
        for name, options in (("restore_follow", {"fail_old": True}), ("coasting", {"fail_restore": True}), ("readback", {"mismatch": True})):
            with self.subTest(name=name):
                core = _FaultyCore(fail_on=9, **options)
                m = compat_with_coasting(core)
                result = m.commit_binding(origin="lang_confirm", track_key=9, expected_version=m.version, source_frame=7,
                                          commit_frame=8, selector=tm.LanguageCompatSelector(2, (0.5, 0.5, 0.1, 0.1), 7))
                self.assertEqual((result.accepted, result.reason, result.fail_closed), (False, tm.REASON_ROLLBACK_FAILED, True))
                self.assertTrue(m.reinit_required)
                self.assertIsNone(m.binding)
                failed = [e for e in m.events if e["type"] == "commit" and e.get("reason") == tm.REASON_ROLLBACK_FAILED]
                self.assertEqual(len(failed), 1)
                self.assertIn(failed[0]["pointer_state"], ("cleared", "UNKNOWN"))

    def test_session_rollback_failure_holds_via_safety_channel(self):
        """IR-9：会话内提交回滚失败经机身安全通道 `BodyCommand.hold` 写 `body_safety_hold`（detail.reason =
        `binding_rollback_failed`），状态 `REINIT_REQUIRED`；其后无新的云台（观测/预测）与速度效果。"""
        spec = importlib.util.spec_from_file_location("_capture_session_harness", Path(__file__).with_name("test_capture_session.py"))
        cs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cs)
        harness = cs.bound_harness(self, lambda f: [(1, TRACKED, cs.box_px(300, 240)), (2, TRACKED, cs.box_px(500, 300))])
        core = harness.tracker.core
        original = core.follow

        def faulty(track_id):
            if track_id == 2:
                core._pointer = 2  # 半改：先改指针再抛
                raise RuntimeError("half-applied follow")
            if track_id == 1:
                raise RuntimeError("restore follow failed")
            original(track_id)

        core.follow = faulty
        frame = harness.publish(1)
        before = len(harness.receipts())
        harness.click(500, 300, frame)
        self.assertEqual((harness.session.state, harness.session.reason), ("REINIT_REQUIRED", tm.REASON_ROLLBACK_FAILED))
        new = harness.receipts()[before:]
        holds = [i for i, r in enumerate(new) if r["channel"] == "body_safety_hold" and r["outcome"] == "WRITTEN"
                 and r["detail"].get("reason") == tm.REASON_ROLLBACK_FAILED]
        self.assertEqual(len(holds), 1)
        harness.publish(3)
        later = harness.receipts()[before + holds[0] + 1:]
        self.assertEqual([r for r in later if r["outcome"] == "WRITTEN" and r["channel"] in ("look_at", "predicted_look_at", "body_command")], [])

    def test_rejected_reselect_keeps_old_target(self):
        m, core = manager()
        history = start_tracking(m, core)
        snapshot = m._business_snapshot()
        frame = Frame(11).row(1, TRACKED, box_at(300, 240)).row(2, TRACKED, box_at(500, 300))
        history[11] = frame.entry()
        history[12] = Frame(12).row(1, TRACKED, box_at(300, 240)).entry()  # 2 号车在 12 帧断链
        word, commit, _ = bind_by_click(m, history, 2, 11, 12, 500, 300)
        self.assertEqual(word, "evidence_chain_broken@12")
        self.assertTrue(m._business_matches(snapshot))
        self.assertEqual((core.pointer(), m.binding.track_key), (1, 1))

    def test_click_chain_break_does_not_substitute_nearby_track(self):
        """#5：首次点击证据链中间一帧断 → 拒绝，旧点附近唯一候选不补身份。"""
        m, core = manager()
        history = History()
        history[20] = Frame(20).row(3, TRACKED, box_at(200, 200)).entry()
        history[21] = Frame(21).row(4, TRACKED, box_at(203, 200)).entry()  # 3 号断，附近新 4 号
        history[22] = Frame(22).row(4, TRACKED, box_at(205, 200)).entry()
        word, commit, _ = bind_by_click(m, history, 3, 20, 22, 200, 200)
        self.assertEqual((word, commit, m.binding, core.pointer()), ("evidence_chain_broken@21", None, None, None))

    def test_reselect_closes_old_episode_after_success(self):
        m, core = manager()
        history = start_tracking(m, core)
        for f in (11, 12):
            history[f] = Frame(f).row(1, TRACKED, box_at(300, 240)).row(2, TRACKED, box_at(500, 300)).entry()
        bind_by_click(m, history, 2, 11, 12, 500, 300)
        kinds = [(e["kind"], e["type"]) for e in m.events]
        committed = [i for i, k in enumerate(kinds) if k == ("binding_committed", "commit")]
        closed = [i for i, e in enumerate(m.events) if e["type"] == "episode_closed" and e["reason"] == tm.REASON_SUPERSEDED]
        self.assertEqual(len(closed), 1)
        self.assertLess(committed[-1], closed[0])

    def test_follow_call_sites_closed_set(self):
        """AC-7：`follow(` 调用点与 §3.5 闭集一致；全 `controller/` 无 `getattr(…, "follow"/"designate")`；
        `language_loop.py` 零直接 follow；会话不调 designate。"""
        follow_allowed = {
            ("target_manager.py", "commit_binding"),
            ("target_manager.py", "_rollback"),
            ("target_manager.py", "_release"),
            ("resident_core.py", "designate"),
            ("det_assoc_tracker.py", "follow"),
        }
        designate_allowed = {("det_assoc_tracker.py", "designate")}
        found = []
        for path in sorted((PROJECT_ROOT / "controller").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for function in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
                for node in ast.walk(function):
                    if not isinstance(node, ast.Call):
                        continue
                    if isinstance(node.func, ast.Attribute) and node.func.attr in ("follow", "designate"):
                        found.append((path.name, function.name, node.func.attr))
                    if (isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 2
                            and isinstance(node.args[1], ast.Constant) and node.args[1].value in ("follow", "designate")):
                        found.append((path.name, function.name, f"getattr:{node.args[1].value}"))
        offenders = sorted(
            {item for item in found
             if not ((item[0], item[1]) in follow_allowed and item[2] == "follow")
             and not ((item[0], item[1]) in designate_allowed and item[2] == "designate")}
        )
        self.assertEqual(offenders, [])
        self.assertFalse([item for item in found if item[0] == "language_loop.py"])


def auth_params(t_pred=4):
    return tm.CaptureParams(t_pred=t_pred, t_repair=5)


def representative_age(band, params):
    return {"0": 0, "pred": 1, "gap": params.t_pred + 1, "expired": params.t_repair}[band]


def all_cells(params):
    for task, watchdog, continuity, semantic, geometry, observation, band, covariance in itertools.product(
        tm.TASK_AXIS, tm.WATCHDOG_AXIS, tm.CONTINUITY_STATUSES, tm.SEMANTIC_AXIS, tm.GEOMETRY_AXIS,
        tm.OBSERVATION_AXIS, tm.AGE_BANDS, tm.COVARIANCE_AXIS,
    ):
        if band == "gap" and params.t_pred + 1 >= params.t_repair:
            continue  # 该配置下 (T_pred, T_repair) 带为空
        yield tm.AuthInputs(task, watchdog, continuity, semantic, geometry, observation, representative_age(band, params), covariance, t0=100)


ROW_CONDITIONS = {
    1: lambda i, p: i.task != "ACTIVE",
    2: lambda i, p: i.watchdog == "stale",
    3: lambda i, p: i.continuity in (tm.DISPUTED, tm.BROKEN),
    4: lambda i, p: i.semantic == tm.CONTRADICTED,
    5: lambda i, p: i.geometry != "valid",
    6: lambda i, p: i.observation == tm.OBSERVED and i.continuity == tm.SUPPORTED and i.age == 0,
    7: lambda i, p: i.observation == tm.PREDICTED and i.continuity in (tm.SUPPORTED, tm.TENTATIVE) and 1 <= i.age <= p.t_pred and i.covariance == "within",
    8: lambda i, p: True,
}


class AuthorizationTests(unittest.TestCase):
    def test_full_table_first_hit_and_domain(self):
        """AC-8 修订 1：3,072 格（另加非空带配置）逐格区分一致性拒绝与八行首命中。"""
        counts = {}
        for params, expected_total in ((auth_params(4), 2304), (auth_params(2), 3072)):
            cells = list(all_cells(params))
            self.assertEqual(len(cells), expected_total)
            for inputs in cells:
                result = tm.derive_authorization(inputs, params)
                if not tm.in_reachable_domain(inputs, params):
                    self.assertEqual((result.consistent, result.body, result.gimbal), (False, tm.HOLD, tm.GIMBAL_NONE))
                    self.assertEqual(result.reason_codes, ("authorization_input_inconsistent",))
                    counts["inconsistent"] = counts.get("inconsistent", 0) + 1
                    continue
                self.assertTrue(ROW_CONDITIONS[result.row](inputs, params), (inputs, result))
                for earlier in range(1, result.row):
                    self.assertFalse(ROW_CONDITIONS[earlier](inputs, params), (inputs, result, earlier))
                if result.body == tm.FOLLOW:
                    self.assertEqual(result.row, 6)
                counts[result.row] = counts.get(result.row, 0) + 1
        self.assertGreater(counts.get(7, 0), 0)
        self.assertGreater(counts.get(6, 0), 0)
        self.assertGreater(counts["inconsistent"], 0)

    def test_monotone_on_legal_worsening_edges(self):
        params = auth_params(2)
        checked = 0
        for inputs in all_cells(params):
            if not tm.in_reachable_domain(inputs, params):
                continue
            before = tm.derive_authorization(inputs, params)
            for after in worsening(inputs, params):
                if not tm.in_reachable_domain(after, params):
                    continue
                self.assertTrue(tm.derive_authorization(after, params).at_most(before), (inputs, after))
                checked += 1
        self.assertGreater(checked, 500)

    def test_d2_counterexample_is_out_of_domain(self):
        params = auth_params(4)
        observed = tm.AuthInputs("ACTIVE", "fresh", tm.TENTATIVE, tm.UNKNOWN, "valid", tm.OBSERVED, 1, "within", 100)
        self.assertFalse(tm.in_reachable_domain(observed, params))
        self.assertEqual(tm.derive_authorization(observed, params).reason_codes, ("authorization_input_inconsistent",))

    def test_candidate_observation_never_drives_gimbal(self):
        m, core = manager()
        history = start_tracking(m, core)
        track_target(m, history, [(11, Frame(11).row(1, LOST, box_at(300, 240)))])
        outcome = track_target(m, history, [(12, Frame(12).row(1, LOST, box_at(300, 240)).row(8, UNCONFIRMED, box_at(330, 250)))])[0]
        self.assertEqual(outcome.effect.gimbal, tm.GIMBAL_PREDICTED)
        self.assertEqual(outcome.effect.aim_center_px, (300.0, 240.0))
        for event in [e for e in m.events if e["type"] == "authorization"]:
            if event["result"]["body"] == tm.FOLLOW:
                self.assertEqual(event["inputs"]["observation"], tm.OBSERVED)


def worsening(inputs, params):
    """AR1-2 列出的合法变差边与三个联动事件（只在 G 内取边）。"""
    from dataclasses import replace  # noqa: PLC0415

    edges = []
    if inputs.task == "ACTIVE":
        edges += [replace(inputs, task=t) for t in ("none", "CANCELED", "stopped")]
    if inputs.watchdog == "fresh":
        edges.append(replace(inputs, watchdog="stale"))
    if inputs.geometry == "valid":
        edges.append(replace(inputs, geometry="invalid"))
    expired = inputs.age >= params.t_repair
    if inputs.observation == tm.PREDICTED:
        order = tm.COVARIANCE_AXIS
        index = order.index(inputs.covariance)
        edges += [replace(inputs, covariance=c) for c in order[index + 1:]]
        if inputs.continuity == tm.SUPPORTED and not expired:
            edges.append(replace(inputs, continuity=tm.TENTATIVE))
        if inputs.continuity in (tm.SUPPORTED, tm.TENTATIVE) and not expired:
            for age in range(inputs.age + 1, params.t_repair):
                if tm.age_band(age, params) != tm.age_band(inputs.age, params):
                    edges.append(replace(inputs, age=age))
            edges.append(replace(inputs, continuity=tm.DISPUTED))
            edges.append(replace(inputs, continuity=tm.BROKEN, age=params.t_repair))
    if inputs.observation == tm.OBSERVED and inputs.continuity == tm.SUPPORTED and inputs.age == 0:
        edges.append(replace(inputs, observation=tm.PREDICTED, continuity=tm.TENTATIVE, age=1))
        edges.append(replace(inputs, observation=tm.PREDICTED, continuity=tm.DISPUTED, age=1))
    return edges


def scripted_session(m, core):
    """点击 → 跟踪 → 丢失 → 修复 → 丢失到期 → 重选 → 停止：覆盖转换/拒绝/绑定/效果。"""
    history = start_tracking(m, core)
    track_target(m, history, [(11, Frame(11).row(1, TRACKED, box_at(302, 240)))])
    track_target(m, history, [(12, Frame(12).row(1, LOST, box_at(304, 240)))])
    track_target(m, history, [(13, Frame(13).row(1, LOST, box_at(306, 240)).row(8, UNCONFIRMED, box_at(306, 240)))])
    track_target(m, history, [(14, Frame(14).row(1, LOST, box_at(308, 240)).row(8, TRACKED, box_at(308, 240)))])
    for f in range(15, 21):
        track_target(m, history, [(f, Frame(f).row(8, LOST, box_at(310, 240)).row(2, TRACKED, box_at(500, 300)))])
    m.click(request_id="bad", x_px=5.0, y_px=5.0, frame_id=20, image_sha256="d" * 64, history=history, head_frame_id=20,
            actual_image_sha256="d" * 64)
    m.click(request_id="mismatch", x_px=500.0, y_px=300.0, frame_id=19, image_sha256="f" * 64, history=history,
            head_frame_id=20, actual_image_sha256="0" * 64)
    m.click(request_id="good", x_px=500.0, y_px=300.0, frame_id=19, image_sha256="e" * 64, history=history, head_frame_id=20,
            actual_image_sha256="e" * 64)
    track_target(m, history, [(21, Frame(21).row(2, TRACKED, box_at(501, 300)))])
    m.on_watchdog(stale=True, at_monotonic_s=5.0)
    m.request_stop(request_id="stop-1")
    track_target(m, history, [(22, Frame(22).row(2, TRACKED, box_at(502, 300)))])


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def live(self):
        params, sha, text = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)
        inputs = tm.InputsLog(self.root / tm.INPUTS_FILE)
        m = tm.TargetManager(params, mode="capture", config_sha256=sha, config_text=text, inputs=inputs)
        core = ResidentCore(100)
        m.attach_port(core)
        scripted_session(m, core)
        return m

    def test_replay_from_disk_in_new_process_identical(self):
        """#10：只读落盘 tm_inputs.jsonl 与配置文件、在新进程重放 → 转换/拒绝/绑定/效果逐条相同。"""
        m = self.live()
        types = {e["type"] for e in m.events}
        self.assertTrue({"commit", "continuity", "authorization", "report", "stop", "click", "episode_closed"} <= types, types)
        done = subprocess.run(
            [sys.executable, "-m", "controller.target_manager", "replay", str(self.root / tm.INPUTS_FILE), str(tm.DEFAULT_CAPTURE_CONFIG)],
            cwd=PROJECT_ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        replayed = [json.loads(line) for line in done.stdout.splitlines()]
        self.assertEqual(replayed, json.loads(json.dumps(m.events)))

    def replay_new_process(self, path):
        done = subprocess.run(
            [sys.executable, "-m", "controller.target_manager", "replay", str(path), str(tm.DEFAULT_CAPTURE_CONFIG)],
            cwd=PROJECT_ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        return [json.loads(line) for line in done.stdout.splitlines()]

    def test_c1_4_control_limited_replayed_in_new_process(self):
        """C1-4：servo_clamp 触发的 `control_limited` 事件须可只凭落盘输入/配置在新进程重放（全字段，含其后 event_seq）。
        修前 `note_control_limited` 只发事件、不写输入，重放缺该事件，其后序号整体漂移。"""
        params, sha, text = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)
        m = tm.TargetManager(params, mode="capture", config_sha256=sha, config_text=text, inputs=tm.InputsLog(self.root / tm.INPUTS_FILE))
        core = ResidentCore(100)
        m.attach_port(core)
        history = start_tracking(m, core)
        outcome = track_target(m, history, [(11, Frame(11).row(1, TRACKED, box_at(302, 240)))])[0]
        m.note_control_limited(outcome.effect)  # 会话 `_capture_look_at` 在限速裁剪时的同一调用
        track_target(m, history, [(12, Frame(12).row(1, TRACKED, box_at(304, 240)))])
        self.assertIn("control_limited", [e["type"] for e in m.events])
        self.assertEqual(self.replay_new_process(self.root / tm.INPUTS_FILE), json.loads(json.dumps(m.events)))

    def test_rollback_failure_paths_replayed_in_new_process(self):
        """预复核关注项（AC-7/15）：半改 follow 成功复原、复原 follow 失败、coasting 恢复失败、读回不符四条路径，
        只凭落盘输入在新进程重放，转换/拒绝/绑定/效果逐条相同（端口每次调用的结果都是落盘外部输入）。
        修前恢复失败与读回不符没有落盘输入，重放端口按「成功复原」走，事件分叉。"""
        for name, options in (("half_applied_restored", {}), ("restore_follow", {"fail_old": True}),
                              ("coasting_restore", {"fail_restore": True}), ("readback", {"mismatch": True})):
            with self.subTest(name=name):
                path = self.root / f"{name}-{tm.INPUTS_FILE}"
                params, sha, text = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)
                m = tm.TargetManager(params, mode="compat", config_sha256=sha, config_text=text, inputs=tm.InputsLog(path))
                core = _FaultyCore(fail_on=9, **options)
                m.attach_port(core)
                selector = tm.LanguageCompatSelector(1, (0.1, 0.1, 0.2, 0.2), 5)
                self.assertTrue(m.commit_binding(origin="lang_confirm", track_key=4, expected_version=0, source_frame=5, commit_frame=6,
                                                 selector=selector, coasting_designation_id=1).accepted)
                core._coasting["steps"] = 3
                m.commit_binding(origin="lang_confirm", track_key=9, expected_version=m.version, source_frame=7, commit_frame=8,
                                 selector=tm.LanguageCompatSelector(2, (0.5, 0.5, 0.1, 0.1), 7))
                m.release_binding("operator_release", frame_id=9)
                self.assertEqual(self.replay_new_process(path), json.loads(json.dumps(m.events)))

    def test_tampered_line_rejected(self):
        self.live()
        path = self.root / tm.INPUTS_FILE
        lines = path.read_text(encoding="utf-8").splitlines()
        record = json.loads(lines[3])
        record["frame_id"] = int(record.get("frame_id") or 0) + 1
        lines[3] = json.dumps(record)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaises(tm.ReplayRejected):
            tm.replay_tm_inputs(path, tm.DEFAULT_CAPTURE_CONFIG)

    def test_missing_reference_rejected(self):
        self.live()
        path = self.root / tm.INPUTS_FILE
        lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        for record in lines:
            if record["kind"] == "frame":
                record.pop("history")
                record["line_sha256"] = tm.line_sha256(record)
                break
        path.write_text("".join(tm.canonical_json(r) + "\n" for r in lines), encoding="utf-8")
        with self.assertRaises(tm.ReplayRejected):
            tm.replay_tm_inputs(path, tm.DEFAULT_CAPTURE_CONFIG)

    # --- R1返工 R1-1（AC-15/AR1-2：缺行/截断即拒，不伪造、不洗白）的具名回归 -------------------------------------

    def production_logs(self):
        """生产路径夹具：真实 `TargetManager` 写出的 tm_inputs.jsonl（完整点击/跟踪/修复/重选/停止脚本 + 四种回滚失败）。"""
        self.live()
        logs = {"scripted_session": self.root / tm.INPUTS_FILE}
        for name, options in (("half_applied_restored", {}), ("restore_follow", {"fail_old": True}),
                              ("coasting_restore", {"fail_restore": True}), ("readback", {"mismatch": True})):
            path = self.root / f"{name}-{tm.INPUTS_FILE}"
            params, sha, text = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)
            m = tm.TargetManager(params, mode="compat", config_sha256=sha, config_text=text, inputs=tm.InputsLog(path))
            core = _FaultyCore(fail_on=9, **options)
            m.attach_port(core)
            m.commit_binding(origin="lang_confirm", track_key=4, expected_version=0, source_frame=5, commit_frame=6,
                             selector=tm.LanguageCompatSelector(1, (0.1, 0.1, 0.2, 0.2), 5), coasting_designation_id=1)
            core._coasting["steps"] = 3
            m.commit_binding(origin="lang_confirm", track_key=9, expected_version=m.version, source_frame=7, commit_frame=8,
                             selector=tm.LanguageCompatSelector(2, (0.5, 0.5, 0.1, 0.1), 7))
            m.release_binding("operator_release", frame_id=9)
            logs[name] = path
        for path in logs.values():  # 完整原件本身可重放（不因新校验误拒）
            tm.replay_tm_inputs(path, tm.DEFAULT_CAPTURE_CONFIG)
        return logs

    def test_r1_1_deleting_any_port_line_is_rejected(self):
        """R1-1：生产日志删去任一 `port` 行（其余行 sha 仍合法）→ `replay_tm_inputs` 抛 `ReplayRejected`。
        修前重放端口对缺行默认成功或退回本地模型：删 readback 行把在线 `binding_rollback_failed`（fail-closed）洗成
        `follow_failed`，删 pointer/follow 行照常重放，不拒绝。"""
        deleted = 0
        for name, path in self.production_logs().items():
            raw = path.read_bytes().splitlines(keepends=True)
            ports = [i for i, line in enumerate(raw) if json.loads(line)["kind"] == "port"]
            self.assertTrue(ports, name)
            for index in ports:
                call = json.loads(raw[index])["call"]
                with self.subTest(log=name, line=index, call=call):
                    damaged = self.root / f"damaged-{name}-{index}.jsonl"
                    damaged.write_bytes(b"".join(raw[:index] + raw[index + 1:]))
                    with self.assertRaises(tm.ReplayRejected):
                        tm.replay_tm_inputs(damaged, tm.DEFAULT_CAPTURE_CONFIG)
                    deleted += 1
        self.assertGreater(deleted, 10)

    def test_r1_1_truncated_after_click_request_is_rejected(self):
        """R1-1：捕获日志取到点击请求行为止的字节前缀（在线崩溃前尚未写端口行）→ 拒绝；修前重放照发
        `binding_committed`，伪造在线未必发生的绑定。另：取到读回端口行之前的前缀 → 拒绝（修前洗成 follow_failed）。"""
        logs = self.production_logs()
        raw = logs["scripted_session"].read_bytes()
        lines = raw.splitlines(keepends=True)
        records = [json.loads(line) for line in lines]
        # 在线随后写了端口行的点击（被受理、进入提交事务）；被拒点击不调端口，其后截断是合法前缀。
        clicks = [i for i, r in enumerate(records) if r.get("kind") == "request" and r.get("action") == "click"
                  and i + 1 < len(records) and records[i + 1]["kind"] == "port"]
        self.assertGreaterEqual(len(clicks), 2)
        for index in clicks:
            with self.subTest(click_line=index):
                prefix = self.root / f"prefix-click-{index}.jsonl"
                prefix.write_bytes(b"".join(lines[:index + 1]))
                with self.assertRaises(tm.ReplayRejected):
                    tm.replay_tm_inputs(prefix, tm.DEFAULT_CAPTURE_CONFIG)
        lines = logs["readback"].read_bytes().splitlines(keepends=True)
        readback = next(i for i, line in enumerate(lines) if json.loads(line).get("call") == "readback")
        prefix = self.root / "prefix-before-readback.jsonl"
        prefix.write_bytes(b"".join(lines[:readback]))
        with self.assertRaises(tm.ReplayRejected):
            tm.replay_tm_inputs(prefix, tm.DEFAULT_CAPTURE_CONFIG)

    def test_r1_1_port_lines_reordered_or_duplicated_are_rejected(self):
        """R1-1：端口记录必须按在线调用顺序逐条消费、恰好用完：交换相邻两条不同种类的端口行、或重复一条端口行 → 拒绝。"""
        path = self.production_logs()["readback"]
        lines = path.read_bytes().splitlines(keepends=True)
        kinds = [json.loads(line) for line in lines]
        pair = next(i for i in range(len(kinds) - 1)
                    if kinds[i]["kind"] == kinds[i + 1]["kind"] == "port" and kinds[i]["call"] != kinds[i + 1]["call"])
        swapped = lines[:pair] + [lines[pair + 1], lines[pair]] + lines[pair + 2:]
        duplicated = lines[:pair + 1] + [lines[pair]] + lines[pair + 1:]
        for name, content in (("swapped", swapped), ("duplicated", duplicated)):
            with self.subTest(name):
                damaged = self.root / f"{name}.jsonl"
                damaged.write_bytes(b"".join(content))
                with self.assertRaises(tm.ReplayRejected):
                    tm.replay_tm_inputs(damaged, tm.DEFAULT_CAPTURE_CONFIG)

    def test_events_carry_required_fields(self):
        m = self.live()
        for event in m.events:
            for key in ("event_seq", "accepted", "reason", "effect_seq", "config_sha256", "tm_inputs_line_sha256"):
                self.assertIn(key, event)
        self.assertEqual([e["event_seq"] for e in m.events], list(range(1, len(m.events) + 1)))



# --- P1-ENG-FASTFIX-001 AC-5/AC-6/AC-13（K3/K2）：时序升级重建后的自动重捕 -------------------------------------

from controller.resident_core import FullKfState, make_full_kf_state  # noqa: E402

FF = tm.FastfixParams(t_pub_s=0.4, k_pub=2, n_drop=3, t_reacq=10, auto_reacquire=True)


class ConstantVelocityKF:
    """测试用 KF（与库同形接口 `predict(mean, covariance)`）：恒速 8 维、Q = q·I（纯 Python）。"""

    def __init__(self, q=1.0, value=None):
        self.q = q
        self.value = value
        self.calls = 0

    def predict(self, mean, covariance):
        self.calls += 1
        if self.value is not None:
            return [self.value] * 8, [[self.value] * 8 for _ in range(8)]
        new_mean = list(mean)
        for i in range(4):
            new_mean[i] = mean[i] + mean[i + 4]
        f = [[1.0 if i == j else 0.0 for j in range(8)] for i in range(8)]
        for i in range(4):
            f[i][i + 4] = 1.0
        fp = [[sum(f[i][k] * covariance[k][j] for k in range(8)) for j in range(8)] for i in range(8)]
        fpf = [[sum(fp[i][k] * f[j][k] for k in range(8)) for j in range(8)] for i in range(8)]
        return new_mean, [[fpf[i][j] + (self.q if i == j else 0.0) for j in range(8)] for i in range(8)]


def full_state(frame_id, key, cx, cy, w=60.0, h=40.0, *, var=25.0, phase=KF_POSTERIOR, vel=(0.0, 0.0)):
    mean = [cx, cy, w, h, vel[0], vel[1], 0.0, 0.0]
    cov = [[(var if i < 4 else 1.0) if i == j else 0.0 for j in range(8)] for i in range(8)]
    return make_full_kf_state(frame_id, frame_id, key, phase, "xywh", mean, cov)


def pose_of(frame_id, quat=None):
    entry = Frame(frame_id).entry()
    pose = tm.pose_metadata_of(entry)
    if quat is not None:
        pose["camera_rotation_xyzw"] = list(quat)
    return pose


def ff_manager(params=None, fastfix=FF, inputs=None):
    m = tm.TargetManager(params or tm.CaptureParams(), mode="capture", config_sha256="0" * 64, inputs=inputs, fastfix=fastfix,
                         fastfix_config_sha256="1" * 64)
    core = ResidentCore(100)
    m.attach_port(core)
    return m, core


def escalate(m, history, *, f_last=12, escalation=12, state=None, candidates=None, timing=True, auto=True, seg_end="publish_expired"):
    """绑定后帧 11–f_last 被接受 → 生成提示 → release(cancel_task=False) → 拆除 → 新端口。"""
    for f in range(11, f_last + 1):
        track_target(m, history, [(f, Frame(f).row(1, TRACKED, box_at(300, 240)))])
    if candidates is None:
        candidates = [tm.HintCandidate(f_last, 1, state or full_state(f_last, 1, 300.0, 240.0), pose_of(f_last), "DROPPED")]
    hint = m.prepare_reacquire_hint(seg_end=seg_end, timing_escalation=timing, escalation_frame=escalation,
                                    auto_reacquire=auto, candidates=candidates)
    m.release_binding(seg_end, cancel_task=hint is None)
    m.on_teardown(seg_end)
    core = ResidentCore(100)
    m.attach_port(core)
    return hint, core


def window_frame(m, f, rows, *, predictor=None, at=None, f_ready=15, mutate=None):
    frame = Frame(f)
    for key, state, box in rows:
        frame.row(key, state, box)
    if mutate is not None:
        mutate(frame)
    entry = frame.entry()
    reacq = None
    if m.reacquire_open:
        reacq = dict(m.reacquire_prior_for(entry, predictor or ConstantVelocityKF()) or {})
        reacq["at_monotonic_s"] = 100.0 + (f - f_ready) * 0.2 if at is None else at
    return m.on_frame(entry, newest=True, reacq=reacq)


def events_of(m, kind):
    return [e for e in m.events if e["kind"] == kind]


class ReacquireHintTests(unittest.TestCase):
    """AC-5：提示生成/跳过各原因（升级标志、auto 轴、绑定、stopped、连续性终点、无合格观测、过期、无效状态）。"""

    def skipped(self, m):
        return [e["reason"] for e in events_of(m, "reacquire_skipped")]

    def test_hint_generated_releases_without_cancel_and_closes_old_episode_once(self):
        m, core = ff_manager()
        history = start_tracking(m, core)
        old_episode = m.binding.target_episode_id
        task = m.task
        hint, _core = escalate(m, history)
        self.assertIsNotNone(hint)
        self.assertEqual((hint.f_last, hint.track_key, hint.old_episode_id, hint.seg_end), (12, 1, old_episode, "publish_expired"))
        self.assertEqual((m.runtime.phase, m.binding, m.task, m.intent_revision), ("ACQUIRING", None, task, 1))
        self.assertTrue(m.reacquire_pending)
        closes = [e for e in m.events if e["type"] == "episode_closed"]
        self.assertEqual([(e["episode_id"], e["reason"]) for e in closes], [(old_episode, "publish_expired")])
        self.assertEqual(m.inputs.lines[-4]["kind"], "reacquire_hint")

    def test_skip_causes(self):
        def case(label, **kw):
            m, core = ff_manager(fastfix=kw.pop("fastfix", FF))
            history = start_tracking(m, core)
            before = kw.pop("before", None)
            if before is not None:
                before(m, history)
            hint, _ = escalate(m, history, **kw)
            self.assertIsNone(hint, label)
            self.assertEqual(m.runtime.phase if m.runtime else None, "CANCELED", label)
            return self.skipped(m)

        self.assertEqual(case("integrity", timing=False, seg_end="image_identity_changed"), ["not_timing_escalation"])
        self.assertEqual(case("stall", timing=False, seg_end="frame_stall"), ["not_timing_escalation"])
        self.assertEqual(case("off-axis", auto=False), ["auto_reacquire_off"])
        self.assertEqual(case("off-config", fastfix=tm.FastfixParams(auto_reacquire=False)), ["auto_reacquire_off"])
        self.assertEqual(case("stale", f_last=12, escalation=23), ["hint_stale"])
        self.assertEqual(case("invalid-phase", state=full_state(12, 1, 300.0, 240.0, phase=KF_PRIOR)), ["hint_invalid"])
        self.assertEqual(case("invalid-nonfinite", state=full_state(12, 1, float("nan"), 240.0)), ["hint_invalid"])
        self.assertEqual(case("invalid-none", candidates=[tm.HintCandidate(12, 1, None, pose_of(12), "PUBLISHED")]), ["hint_invalid"])
        self.assertEqual(case("no-candidate", candidates=[]), ["no_qualified_observation"])
        self.assertEqual(case("fatal-settle", candidates=[tm.HintCandidate(12, 1, full_state(12, 1, 300.0, 240.0), pose_of(12), "FATAL")]),
                         ["no_qualified_observation"])

        def stop_first(m, history):
            m.request_stop(request_id="s")

        m, core = ff_manager()
        history = start_tracking(m, core)
        stop_first(m, history)
        self.assertIsNone(escalate(m, history)[0])
        self.assertEqual(self.skipped(m), ["task_stopped"])

    def test_full_8x8_covariance_asymmetric_or_not_psd_is_hint_invalid(self):
        """R1 N-1（AC-5、§3.3）：8×8 完整协方差非对称 / 非半正定 → `hint_invalid`（不止 2×2 快照旧例）。"""
        mean = [300.0, 240.0, 60.0, 40.0, 0.0, 0.0, 0.0, 0.0]

        def diag():
            return [[(25.0 if i < 4 else 1.0) if i == j else 0.0 for j in range(8)] for i in range(8)]

        asymmetric = diag()
        asymmetric[1][6] = 0.5
        not_psd = diag()
        not_psd[0][5] = not_psd[5][0] = 10.0  # 25·1 − 10² < 0：对称但非半正定
        for label, cov, reason in (("asymmetric", asymmetric, "kf_cov_asymmetric"), ("not_psd", not_psd, "kf_cov_not_psd")):
            state = make_full_kf_state(12, 12, 1, KF_POSTERIOR, "xywh", mean, cov)
            self.assertEqual((state.valid, state.invalid_reason), (False, reason), label)
            m, core = ff_manager()
            history = start_tracking(m, core)
            hint, _ = escalate(m, history, state=state)
            self.assertIsNone(hint, label)
            self.assertEqual(self.skipped(m), ["hint_invalid"], label)
        sound = make_full_kf_state(12, 12, 1, KF_POSTERIOR, "xywh", mean, diag())
        self.assertTrue(sound.valid)

    def test_hint_state_is_a_deep_copy_of_library_track(self):
        """R1 N-1（AC-5「提示深复制」）：生产取数 `full_kf_state_from_associator` 取完整状态后原地改库轨迹
        `mean`/`covariance`，已取状态与由它生成的提示均不变。"""
        from controller.resident_core import full_kf_state_from_associator

        class LibTrack:
            def __init__(self):
                self.track_id = 1
                self.frame_id = 12
                self.mean = [300.0, 240.0, 60.0, 40.0, 1.0, 0.0, 0.0, 0.0]
                self.covariance = [[(25.0 if i < 4 else 1.0) if i == j else 0.0 for j in range(8)] for i in range(8)]

            def tlwh_to_xywh(self, tlwh):  # 布局标记：xywh
                return tlwh

        class Associator:
            def __init__(self, track):
                self.tracked_stracks = [track]
                self.lost_stracks = []

        track = LibTrack()
        state = full_kf_state_from_associator(Associator(track), 1, sensor_frame_id=12, library_frame_id=12)
        self.assertTrue(state.valid)
        before = (state.mean, state.covariance)
        m, core = ff_manager()
        history = start_tracking(m, core)
        hint, _ = escalate(m, history, state=state)
        self.assertIsNotNone(hint)
        track.mean[0] = 9999.0
        track.mean[4] = -50.0
        track.covariance[0][0] = -1.0
        track.covariance[2][7] = 123.0
        self.assertEqual((state.mean, state.covariance), before)
        self.assertEqual(state.mean[0], 300.0)
        self.assertEqual(state.covariance[0][0], 25.0)
        self.assertEqual((hint.state.mean, hint.state.covariance), before)

    def test_disputed_and_broken_do_not_revive(self):
        # BROKEN：原轨迹丢失至 T_repair 到期。
        m, core = ff_manager()
        history = start_tracking(m, core)
        for f in range(11, 17):
            track_target(m, history, [(f, Frame(f).row(1, LOST, box_at(300, 240)))])
        self.assertEqual(m.belief.continuity_status, tm.BROKEN)
        hint = m.prepare_reacquire_hint(seg_end="publish_expired", timing_escalation=True, escalation_frame=16, auto_reacquire=True,
                                        candidates=[tm.HintCandidate(10, 1, full_state(10, 1, 300.0, 240.0), pose_of(10), "PUBLISHED")])
        self.assertIsNone(hint)
        self.assertEqual(self.skipped(m), ["continuity_terminal"])
        # DISPUTED：两个竞争者同帧过门。
        m, core = ff_manager()
        history = start_tracking(m, core)
        track_target(m, history, [(11, Frame(11).row(1, TRACKED, box_at(300, 240)).row(2, TRACKED, box_at(301, 241)))])
        self.assertEqual(m.belief.continuity_status, tm.DISPUTED)
        hint = m.prepare_reacquire_hint(seg_end="publish_expired", timing_escalation=True, escalation_frame=11, auto_reacquire=True,
                                        candidates=[tm.HintCandidate(10, 1, full_state(10, 1, 300.0, 240.0), pose_of(10), "PUBLISHED")])
        self.assertIsNone(hint)
        self.assertEqual(self.skipped(m), ["continuity_terminal"])

    def test_no_binding_skips(self):
        m, _core = ff_manager()
        hint = m.prepare_reacquire_hint(seg_end="publish_expired", timing_escalation=True, escalation_frame=5, auto_reacquire=True,
                                        candidates=[])
        self.assertIsNone(hint)
        self.assertEqual(self.skipped(m), ["no_binding"])

    def test_f_last_falls_back_to_latest_qualified_candidate(self):
        m, core = ff_manager()
        history = start_tracking(m, core)
        candidates = [tm.HintCandidate(11, 1, full_state(11, 1, 300.0, 240.0), pose_of(11), "PUBLISHED"),
                      tm.HintCandidate(12, 1, full_state(12, 1, 300.0, 240.0), pose_of(12), "FATAL")]
        hint, _ = escalate(m, history, candidates=candidates)
        self.assertEqual(hint.f_last, 11)


class ReacquireWindowTests(unittest.TestCase):
    """AC-5：窗口起点、帧号/monotonic 双截止（含零轨迹、缺帧、零新帧）、截止帧当帧提交、事务与重放。"""

    def setUp(self):
        self.m, core = ff_manager(fastfix=tm.FastfixParams(t_reacq=4))
        history = start_tracking(self.m, core)
        self.old_episode = self.m.binding.target_episode_id
        self.task = self.m.task
        escalate(self.m, history)
        self.assertTrue(self.m.open_reacquire_window(f_ready=15, m_ready=100.0, hz=5.0))

    def test_window_started_event_and_bounds(self):
        started = events_of(self.m, "reacquire_started")[0]
        self.assertEqual((started["f_ready"], started["deadline_frame"], started["deadline_monotonic_s"]), (15, 18, 100.8))

    def test_commit_on_last_allowed_frame_and_transaction(self):
        window_frame(self.m, 16, [])  # 零轨迹帧照计
        window_frame(self.m, 17, [(7, TRACKED, box_at(300, 240))])
        outcome = window_frame(self.m, 18, [(7, TRACKED, box_at(300, 240))])  # 最后允许帧 = f_ready + T − 1
        m = self.m
        self.assertIsNotNone(m.binding)
        self.assertEqual((m.binding.track_key, m.binding.relation, m.binding.origin, m.binding.association_revision),
                         (7, "REBUILD_REACQUIRE", "reacquire", 0))
        self.assertEqual((m.episode_seq, m.binding.target_episode_id), (self.old_episode + 1, self.old_episode + 1))
        self.assertEqual((m.task, m.intent_revision, m.runtime.phase), (self.task, 1, "TRACKING"))
        evidence = m.binding.evidence_refs
        for key in ("hint_line_sha256", "f_last", "reacquired_from_episode", "seg_end", "evidence_frames", "nis", "states",
                    "tm_inputs_line_sha256"):
            self.assertIn(key, evidence)
        self.assertEqual((evidence["evidence_frames"], evidence["reacquired_from_episode"], evidence["f_last"]),
                         ([17, 18], self.old_episode, 12))
        done = events_of(m, "reacquired_after_rebuild")[0]
        self.assertEqual((done["frame_id"], done["latency_frames"]), (18, 3))
        self.assertEqual(outcome.projection, ("TRACKING", tm.REASON_REBUILD_REACQUIRED))
        self.assertEqual((outcome.effect.body, outcome.effect.gimbal), (tm.FOLLOW, tm.GIMBAL_OBSERVED))
        self.assertEqual(m.take_reacquire_result()["result"], "committed")
        # 下一帧恢复普通投影；旧 episode 只在拆载体时关闭一次。
        track = window_frame(m, 19, [(7, TRACKED, box_at(300, 240))])
        self.assertEqual(track.projection, ("TRACKING", None))
        self.assertEqual(len([e for e in m.events if e["type"] == "episode_closed"]), 1)

    def test_frame_strictly_over_deadline_fails_first_even_with_evidence(self):
        window_frame(self.m, 17, [(7, TRACKED, box_at(300, 240))])
        window_frame(self.m, 19, [(7, TRACKED, box_at(300, 240))])  # 缺帧照计：19 > 18
        self.assertIsNone(self.m.binding)
        failed = events_of(self.m, "reacquire_failed")[0]
        self.assertEqual((failed["cause"], failed["reason"]), ("deadline_frame", tm.REASON_REACQUIRE_FAILED))
        self.assertEqual(self.m.runtime.phase, "CANCELED")
        window_frame(self.m, 20, [(7, TRACKED, box_at(300, 240))])
        self.assertIsNone(self.m.binding)  # 不再自动尝试

    def test_monotonic_boundary_equal_commits_strictly_over_fails(self):
        window_frame(self.m, 16, [(7, TRACKED, box_at(300, 240))], at=100.2)
        window_frame(self.m, 17, [(7, TRACKED, box_at(300, 240))], at=100.8)  # 年龄恰 = T/hz
        self.assertIsNotNone(self.m.binding)
        m, core = ff_manager(fastfix=tm.FastfixParams(t_reacq=4))
        history = start_tracking(m, core)
        escalate(m, history)
        m.open_reacquire_window(f_ready=15, m_ready=100.0, hz=5.0)
        window_frame(m, 16, [(7, TRACKED, box_at(300, 240))], at=100.2)
        window_frame(m, 17, [(7, TRACKED, box_at(300, 240))], at=100.8001)
        self.assertIsNone(m.binding)
        self.assertEqual(events_of(m, "reacquire_failed")[0]["cause"], "deadline_monotonic")

    def test_zero_new_frame_tick_expires(self):
        self.assertFalse(self.m.expire_reacquire(at_monotonic_s=100.8))
        self.assertNotEqual(self.m.inputs.lines[-1]["kind"], "reacquire_expire")  # 未到期不落盘
        self.assertTrue(self.m.expire_reacquire(at_monotonic_s=100.81))
        self.assertEqual(self.m.inputs.lines[-1]["kind"], "reacquire_expire")
        self.assertEqual(events_of(self.m, "reacquire_failed")[0]["cause"], "deadline_monotonic")
        self.assertEqual(self.m.runtime.phase, "CANCELED")

    def test_window_hold_only_effects(self):
        outcome = window_frame(self.m, 16, [(7, TRACKED, box_at(300, 240))])
        self.assertEqual((outcome.effect.body, outcome.effect.gimbal, outcome.effect.observation_box_norm), (tm.HOLD, tm.GIMBAL_NONE, None))

    def test_ambiguity_latched(self):
        window_frame(self.m, 16, [(7, TRACKED, box_at(300, 240)), (8, TRACKED, box_at(302, 240))])
        failed = events_of(self.m, "reacquire_failed")[0]
        self.assertEqual((failed["cause"], failed["reason"]), ("ambiguous", tm.REASON_REACQUIRE_AMBIGUOUS))
        window_frame(self.m, 17, [(7, TRACKED, box_at(300, 240))])
        self.assertIsNone(self.m.binding)

    def test_unconfirmed_evidence_needs_tracked_commit_and_valid_post(self):
        window_frame(self.m, 16, [(7, UNCONFIRMED, box_at(300, 240))])
        window_frame(self.m, 17, [(7, UNCONFIRMED, box_at(300, 240))])
        self.assertIsNone(self.m.binding)  # 提交帧状态须 TRACKED
        window_frame(self.m, 18, [(7, TRACKED, box_at(300, 240))])
        self.assertEqual(self.m.binding.track_key, 7)

    def test_invalid_candidate_post_keeps_evidence(self):
        def bad_post(frame):
            frame.posts[7] = snap(frame.frame_id, 7, (300.0, 240.0, 60.0, 40.0), KF_PRIOR)

        window_frame(self.m, 16, [(7, TRACKED, box_at(300, 240))])
        window_frame(self.m, 17, [(7, TRACKED, box_at(300, 240))], mutate=bad_post)
        self.assertIsNone(self.m.binding)
        rejected = [e for e in self.m.events if e["type"] == "reacquire_commit"]
        self.assertEqual(rejected[0]["reason"], "kf_post_invalid")
        window_frame(self.m, 18, [(7, TRACKED, box_at(300, 240))])
        self.assertEqual(self.m.binding.track_key, 7)
        self.assertEqual(self.m.binding.evidence_refs["evidence_frames"], [16, 17, 18])

    def test_stop_release_click_cancel(self):
        self.m.request_stop(request_id="s1")
        canceled = events_of(self.m, "reacquire_canceled")[0]
        self.assertEqual(canceled["reason"], "operator_stop")
        window_frame(self.m, 16, [(7, TRACKED, box_at(300, 240))])
        window_frame(self.m, 17, [(7, TRACKED, box_at(300, 240))])
        self.assertIsNone(self.m.binding)

        m, core = ff_manager()
        history = start_tracking(m, core)
        escalate(m, history)
        m.open_reacquire_window(f_ready=15, m_ready=100.0, hz=5.0)
        m.release_binding("operator_release", cancel_task=True)
        self.assertEqual((events_of(m, "reacquire_canceled")[0]["reason"], m.runtime.phase), ("operator_release", "CANCELED"))

        m, core = ff_manager()
        history = start_tracking(m, core)
        escalate(m, history)
        m.open_reacquire_window(f_ready=15, m_ready=100.0, hz=5.0)
        self.assertTrue(m.cancel_reacquire("user_click"))
        self.assertEqual(m.runtime.phase, "ACQUIRING")  # 点击只作废提示与缓冲；任务阶段由随后的点击事务决定
        window_frame(m, 16, [(7, TRACKED, box_at(300, 240))])
        window_frame(m, 17, [(7, TRACKED, box_at(300, 240))])
        self.assertIsNone(m.binding)

    def test_follow_failure_rolls_back_and_rollback_failure_fails_closed(self):
        for label, core_factory, reason in (
            ("restored", lambda: _FaultyCore(7), "commit_rejected:follow_failed"),
            ("fail_closed", lambda: _FaultyCore(7, fail_restore=True), None),
        ):
            with self.subTest(label=label):
                m, core = ff_manager()
                history = start_tracking(m, core)
                escalate(m, history)
                m.attach_port(core_factory())
                m.open_reacquire_window(f_ready=15, m_ready=100.0, hz=5.0)
                window_frame(m, 16, [(7, TRACKED, box_at(300, 240))])
                window_frame(m, 17, [(7, TRACKED, box_at(300, 240))])
                self.assertIsNone(m.binding)
                failed = events_of(m, "reacquire_failed")[0]
                if reason is not None:
                    self.assertEqual(failed["cause"], reason)
                    self.assertEqual((m.runtime.phase, m.reinit_required), ("CANCELED", False))
                else:
                    self.assertEqual(failed["reason"], tm.REASON_ROLLBACK_FAILED)
                    self.assertTrue(m.reinit_required)
                    self.assertEqual(m.take_reacquire_result()["result"], "rollback_failed")
                window_frame(m, 18, [(7, TRACKED, box_at(300, 240))])
                self.assertIsNone(m.binding)

    def test_new_carrier_teardown_in_window_cancels_task(self):
        self.m.on_teardown("frame_gap")
        self.assertEqual((events_of(self.m, "reacquire_canceled")[0]["reason"], self.m.runtime.phase), ("teardown:frame_gap", "CANCELED"))


class ReacquireNegativeTests(unittest.TestCase):
    """AC-6：门只用合成先验；尺寸/运动不过、出画、大转映射、映射失败/非有限/S 奇异；`motion_size_gate` 不变。"""

    def window(self, f_last_pose=None, state=None, t_reacq=10):
        m, core = ff_manager(fastfix=tm.FastfixParams(t_reacq=t_reacq))
        history = start_tracking(m, core)
        candidates = [tm.HintCandidate(12, 1, state or full_state(12, 1, 300.0, 240.0), f_last_pose or pose_of(12), "PUBLISHED")]
        escalate(m, history, candidates=candidates)
        m.open_reacquire_window(f_ready=15, m_ready=100.0, hz=5.0)
        return m

    def run_frames(self, m, frames, **kw):
        for f, rows in frames:
            window_frame(m, f, rows, **kw)

    def test_size_and_motion_gate_rejections(self):
        for label, box in (("size", box_at(300, 240, 180.0, 120.0)), ("motion", box_at(420, 240))):
            with self.subTest(label=label):
                m = self.window(t_reacq=3)
                self.run_frames(m, [(16, [(7, TRACKED, box)]), (17, [(7, TRACKED, box)]), (18, [(7, TRACKED, box)])])
                self.assertIsNone(m.binding)
                self.assertEqual(events_of(m, "reacquire_failed")[0]["cause"], "deadline_frame")

    def test_target_out_of_frame_fails(self):
        m = self.window(t_reacq=3)
        self.run_frames(m, [(16, []), (17, [(9, TRACKED, box_at(80, 80))]), (18, [])])
        self.assertEqual(events_of(m, "reacquire_failed")[0]["reason"], tm.REASON_REACQUIRE_FAILED)

    def test_large_roll_is_mapped_before_gating(self):
        import math as _math  # noqa: PLC0415

        def roll_quat(deg):
            # 绕相机光轴（世界系中 QUAT_DOWN 的前向）滚转：q_roll(world) · q_down。
            down = QUAT_DOWN
            fx, fy, fz = 0.0, -_math.sqrt(0.5), _math.sqrt(0.5)  # QUAT_DOWN 的前向（绕 x 45°）
            half = _math.radians(deg) / 2.0
            r = (fx * _math.sin(half), fy * _math.sin(half), fz * _math.sin(half), _math.cos(half))
            x1, y1, z1, w1 = r
            x2, y2, z2, w2 = down
            return (w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                    w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2)

        from controller.pose_gmc import map_point, pose_homography  # noqa: PLC0415

        m = self.window()
        target = (420.0, 300.0)
        mapped = {}
        for f, deg in ((16, 100.0), (17, 125.0)):  # f − f_last = 4、5 帧，滚转 25°/帧
            h = pose_homography(pose_of(12), pose_of(f, roll_quat(deg)))
            mapped[f] = map_point(h, *target)
        m = self.window(state=full_state(12, 1, *target))

        def rolled(f, deg):
            def mutate(frame):
                pass
            return mutate

        for f, deg in ((16, 100.0), (17, 125.0)):
            frame = Frame(f).row(7, TRACKED, box_at(*mapped[f]))
            entry = frame.entry()
            entry = replace(entry, camera_rotation_xyzw=tuple(roll_quat(deg)))
            reacq = dict(m.reacquire_prior_for(entry, ConstantVelocityKF()) or {})
            reacq["at_monotonic_s"] = 100.0 + (f - 15) * 0.2
            prior = reacq["prior"]
            self.assertIsNotNone(prior, reacq.get("prior_reason"))
            self.assertEqual(prior.phase, tm.REACQ_PRIOR)
            self.assertAlmostEqual(prior.xywh_px[0], mapped[f][0], places=6)
            self.assertAlmostEqual(prior.xywh_px[1], mapped[f][1], places=6)
            m.on_frame(entry, newest=True, reacq=reacq)
        self.assertEqual(m.binding.track_key, 7)
        # 对照：候选留在未映射位置 → 运动门不过、不提交。
        m2 = self.window(state=full_state(12, 1, *target), t_reacq=3)
        for f, deg in ((16, 100.0), (17, 125.0)):
            entry = replace(Frame(f).row(7, TRACKED, box_at(*target)).entry(), camera_rotation_xyzw=tuple(roll_quat(deg)))
            reacq = dict(m2.reacquire_prior_for(entry, ConstantVelocityKF()) or {})
            reacq["at_monotonic_s"] = 100.0 + (f - 15) * 0.2
            m2.on_frame(entry, newest=True, reacq=reacq)
        self.assertIsNone(m2.binding)

    def test_mapping_failure_non_finite_and_singular_give_no_evidence(self):
        m = self.window()
        window_frame(m, 16, [(7, TRACKED, box_at(300, 240))])
        entry = replace(Frame(17).row(7, TRACKED, box_at(300, 240)).entry(), camera_rotation_xyzw=None)
        reacq = dict(m.reacquire_prior_for(entry, ConstantVelocityKF()))
        self.assertEqual((reacq["prior"], reacq["prior_reason"]), (None, "reacq_pose_missing"))
        reacq["at_monotonic_s"] = 100.4
        m.on_frame(entry, newest=True, reacq=reacq)
        self.assertEqual(m.reacq["buffer"], {})  # 证据缓冲清零重计
        window_frame(m, 18, [(7, TRACKED, box_at(300, 240))])
        self.assertIsNone(m.binding)  # 18 单帧证据 < N_adopt
        window_frame(m, 19, [(7, TRACKED, box_at(300, 240))])
        self.assertEqual(m.binding.evidence_refs["evidence_frames"], [18, 19])

        m = self.window()
        entry = Frame(16).row(7, TRACKED, box_at(300, 240)).entry()
        self.assertEqual(m.reacquire_prior_for(entry, ConstantVelocityKF(value=float("nan")))["prior_reason"],
                         "reacq_pose_center_unmappable")

        class InfCovariance(ConstantVelocityKF):
            def predict(self, mean, covariance):
                new_mean, _cov = super().predict(mean, covariance)
                return new_mean, [[float("inf")] * 8 for _ in range(8)]

        self.assertEqual(m.reacquire_prior_for(entry, InfCovariance())["prior_reason"], "reacq_prior_non_finite")
        self.assertEqual(m.reacquire_prior_for(entry, None)["prior_reason"], "reacq_predictor_unavailable")
        tiny = make_full_kf_state(12, 12, 1, KF_POSTERIOR, "xywh", [300.0, 240.0, 1e-6, 1e-6, 0, 0, 0, 0],
                                  [[0.0] * 8 for _ in range(8)])
        m = self.window(state=tiny)
        self.assertEqual(m.reacquire_prior_for(entry, ConstantVelocityKF(q=0.0))["prior_reason"], "reacq_gate_covariance_singular")
        # 位姿映射到相机背后（单应 w ≤ 0）→ 本帧无证据。
        behind = tm.pose_center_transform([300.0, 240.0, 60, 40, 0, 0, 0, 0], [[1.0 if i == j else 0.0 for j in range(8)] for i in range(8)],
                                          ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0)))
        self.assertIsNone(behind)

    def test_gate_uses_only_synthetic_prior(self):
        """反证（首次接受释义 2）：改变候选自身库 prior、保持合成先验与检测不变 → 结果不变。"""
        results = []
        for candidate_prior in (None, (120.0, 60.0, 10.0, 10.0)):
            m = self.window()

            def mutate(frame, candidate_prior=candidate_prior):
                if candidate_prior is not None:
                    frame.priors[7] = snap(frame.frame_id, 7, candidate_prior, KF_PRIOR, cov=(1e4, 1e4))

            window_frame(m, 16, [(7, TRACKED, box_at(300, 240))], mutate=mutate)
            window_frame(m, 17, [(7, TRACKED, box_at(300, 240))], mutate=mutate)
            results.append((m.binding.track_key, m.binding.evidence_refs["nis"]))
        self.assertEqual(results[0], results[1])

    def test_reacquire_gate_rejects_library_phases(self):
        det = RawDetection(0, box_at(300, 240), 0.9, 0)
        library_prior = snap(16, 7, (300.0, 240.0, 60.0, 40.0), KF_PRIOR)
        self.assertEqual(tm.reacquire_gate(library_prior, det, tm.CaptureParams()).reason, "prior_wrong_phase")
        self.assertEqual(tm.motion_size_gate(replace(library_prior, phase=tm.REACQ_PRIOR), det, tm.CaptureParams()).reason,
                         "prior_wrong_phase")
        self.assertTrue(tm.reacquire_gate(replace(library_prior, phase=tm.REACQ_PRIOR), det, tm.CaptureParams()).passed)
        self.assertNotIn(tm.REACQ_PRIOR, __import__("controller.resident_core", fromlist=["KF_PHASES"]).KF_PHASES)

    def test_motion_size_gate_unchanged_against_accepted_base(self):
        from tools.eng_fastfix.common import export_base_controller  # noqa: PLC0415
        import importlib  # noqa: PLC0415
        import random  # noqa: PLC0415

        try:
            with tempfile.TemporaryDirectory() as directory:
                package = Path(directory) / "fx_base_controller_tm"
                export_base_controller(package)
                sys.path.insert(0, directory)
                try:
                    base_tm = importlib.import_module("fx_base_controller_tm.target_manager")
                    base_core = importlib.import_module("fx_base_controller_tm.resident_core")
                finally:
                    sys.path.remove(directory)
        except RuntimeError:
            self.skipTest("git history unavailable")
        rng = random.Random(20261010)
        params = tm.CaptureParams()
        base_params = base_tm.CaptureParams()
        for _ in range(500):
            cx, cy, w, h = rng.uniform(0, 640), rng.uniform(0, 480), rng.uniform(5, 200), rng.uniform(5, 200)
            cov = rng.choice([1.0, 25.0, 400.0, 2000.0])
            phase = rng.choice([KF_PRIOR, KF_POSTERIOR])
            dx, dy = rng.gauss(0, 30), rng.gauss(0, 30)
            dw = rng.uniform(0.3, 3.0)
            box = (cx + dx - w * dw / 2, cy + dy - h / 2, cx + dx + w * dw / 2, cy + dy + h / 2)
            prior = make_kf_snapshot(1, 1, 3, phase, (cx, cy, w, h), (0.0, 0.0), ((cov, 0.0), (0.0, cov)))
            base_prior = base_core.make_kf_snapshot(1, 1, 3, phase, (cx, cy, w, h), (0.0, 0.0), ((cov, 0.0), (0.0, cov)))
            ours = tm.motion_size_gate(prior, RawDetection(0, box, 0.9, 0), params).as_record()
            theirs = base_tm.motion_size_gate(base_prior, base_core.RawDetection(0, box, 0.9, 0), base_params).as_record()
            self.assertEqual(ours, theirs)

    def test_pinned_library_kf_and_apply_pose_center_match(self):
        """首次接受释义 2：同一完整输入对照钉版库 `KalmanFilterXYWH.predict` 连推 n 步与 `apply_pose_center` 的均值/完整协方差。"""
        try:
            import numpy as np  # noqa: PLC0415
            from ultralytics.trackers.utils.kalman_filter import KalmanFilterXYWH  # noqa: PLC0415
        except ImportError:
            self.skipTest("pinned library not importable in this interpreter")
        from controller.det_assoc_tracker import apply_pose_center  # noqa: PLC0415
        from controller.pose_gmc import pose_homography  # noqa: PLC0415

        kf = KalmanFilterXYWH()
        state = full_state(12, 1, 410.0, 300.0, 64.0, 44.0, vel=(3.0, -1.5))
        for n in (1, 3, 6):
            mean, cov = tm.predict_full_state(kf, state.mean, state.covariance, n)
            ref_mean, ref_cov = np.array(state.mean), np.array(state.covariance)
            for _ in range(n):
                ref_mean, ref_cov = kf.predict(ref_mean, ref_cov)
            np.testing.assert_allclose(mean, ref_mean, rtol=0, atol=1e-9)
            np.testing.assert_allclose(cov, ref_cov, rtol=0, atol=1e-9)
            pose_a = pose_of(12)
            pose_b = pose_of(12 + n, (0.40, 0.05, -0.02, 0.9150))
            norm = sum(v * v for v in pose_b["camera_rotation_xyzw"]) ** 0.5
            pose_b["camera_rotation_xyzw"] = [v / norm for v in pose_b["camera_rotation_xyzw"]]
            h = pose_homography(pose_a, pose_b)
            ours = tm.pose_center_transform(mean, cov, h)

            class Track:
                pass

            track = Track()
            track.mean, track.covariance = np.array(ref_mean, dtype=float), np.array(ref_cov, dtype=float)
            self.assertEqual(apply_pose_center([track], h), 1)
            np.testing.assert_allclose(ours[0], track.mean, rtol=0, atol=1e-9)
            np.testing.assert_allclose(ours[1], track.covariance, rtol=0, atol=1e-7)


class ReacquireReplayTests(unittest.TestCase):
    """AC-5/AC-13：重捕全程（提示、窗口、逐帧合成先验、提交）由落盘输入重放，事件逐条相同。"""

    def test_replay_identical_including_reacquire(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            params, sha, text = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)
            fastfix, ff_sha, _ff_text = tm.load_fastfix_config(tm.DEFAULT_FASTFIX_CONFIG, params, 5.0)
            inputs = tm.InputsLog(root / tm.INPUTS_FILE, chain=True)
            m = tm.TargetManager(params, mode="capture", config_sha256=sha, config_text=text, inputs=inputs, fastfix=fastfix,
                                 fastfix_config_sha256=ff_sha)
            m.attach_port(ResidentCore(100))
            history = start_tracking(m, m._port)  # noqa: SLF001
            escalate(m, history)
            m.open_reacquire_window(f_ready=15, m_ready=100.0, hz=5.0)
            window_frame(m, 16, [(7, TRACKED, box_at(300, 240))])
            window_frame(m, 17, [(7, TRACKED, box_at(300, 240))])
            window_frame(m, 18, [(7, TRACKED, box_at(301, 240))])
            self.assertEqual(m.binding.relation, "REBUILD_REACQUIRE")
            replayed = tm.replay_tm_inputs(root / tm.INPUTS_FILE, tm.DEFAULT_CAPTURE_CONFIG, tm.DEFAULT_FASTFIX_CONFIG)
            self.assertEqual(json.loads(json.dumps(replayed)), json.loads(json.dumps(m.events)))
            kinds = {line["kind"] for line in tm.read_inputs(root / tm.INPUTS_FILE)}
            self.assertTrue({"reacquire_hint", "reacquire_window", "frame"} <= kinds)
            with self.assertRaises(tm.ReplayRejected):
                tm.replay_tm_inputs(root / tm.INPUTS_FILE, tm.DEFAULT_CAPTURE_CONFIG)  # FASTFIX 配置缺失即拒


def chained_session_inputs(root):
    """生产路径（`TargetManager` + 链式 `InputsLog`）写出的落盘输入：点击、逐帧、提示、窗口与重捕。"""
    params, sha, text = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)
    fastfix, ff_sha, _ = tm.load_fastfix_config(tm.DEFAULT_FASTFIX_CONFIG, params, 5.0)
    m = tm.TargetManager(params, mode="capture", config_sha256=sha, config_text=text,
                         inputs=tm.InputsLog(root / tm.INPUTS_FILE, chain=True), fastfix=fastfix, fastfix_config_sha256=ff_sha)
    m.attach_port(ResidentCore(100))
    history = start_tracking(m, m._port)  # noqa: SLF001
    escalate(m, history)
    m.open_reacquire_window(f_ready=15, m_ready=100.0, hz=5.0)
    for f in (16, 17, 18, 19):
        window_frame(m, f, [(7, TRACKED, box_at(300, 240))])
    return m


class R22ChainTests(unittest.TestCase):
    """AC-13（CAPTURE R2-2 承接）：行间链式引用与帧连续性——生产字节删去任一中间输入行即拒（含 `reacquire_hint` 行）。

    修前红：接受基线（v1，无链）对同类删行静默重放（`test_base_v1_silently_accepts_deleted_line`）；修后绿：v2 拒绝。"""

    def lines_of(self, path):
        return path.read_text(encoding="utf-8").splitlines()

    def test_deleting_any_middle_line_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            chained_session_inputs(root)
            path = root / tm.INPUTS_FILE
            original = self.lines_of(path)
            tm.replay_tm_inputs(path, tm.DEFAULT_CAPTURE_CONFIG, tm.DEFAULT_FASTFIX_CONFIG)  # 原样可重放
            kinds = [json.loads(line)["kind"] for line in original]
            targets = {"frame": kinds.index("frame", 5), "reacquire_hint": kinds.index("reacquire_hint"),
                       "reacquire_window": kinds.index("reacquire_window"), "teardown": kinds.index("teardown")}
            for label, index in targets.items():
                with self.subTest(deleted=label):
                    path.write_text("\n".join(original[:index] + original[index + 1:]) + "\n", encoding="utf-8")
                    with self.assertRaises(tm.ReplayRejected):
                        tm.replay_tm_inputs(path, tm.DEFAULT_CAPTURE_CONFIG, tm.DEFAULT_FASTFIX_CONFIG)
            with self.subTest(reordered=True):
                swapped = list(original)
                swapped[6], swapped[7] = swapped[7], swapped[6]
                path.write_text("\n".join(swapped) + "\n", encoding="utf-8")
                with self.assertRaises(tm.ReplayRejected):
                    tm.replay_tm_inputs(path, tm.DEFAULT_CAPTURE_CONFIG, tm.DEFAULT_FASTFIX_CONFIG)

    def test_frame_continuity_check(self):
        lines = [{"kind": "init", "prev_line_sha256": None}]
        for frame_id in (5, 6, 8):
            lines.append({"kind": "frame", "frame_id": frame_id})
        previous = None
        for line in lines:
            line["prev_line_sha256"] = previous
            line["line_sha256"] = tm.line_sha256(line)
            previous = line["line_sha256"]
        with self.assertRaisesRegex(tm.ReplayRejected, "frame continuity"):
            tm.check_chain(lines)

    def test_base_v1_silently_accepts_deleted_line(self):
        """修前红的生产对照：v1（无链，CAPTURE 现行格式）删去其后无端口记录的中间帧行，重放不拒（R2-2 原缺口，旧格式不改判）。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            params, sha, text = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)
            m = tm.TargetManager(params, mode="capture", config_sha256=sha, config_text=text, inputs=tm.InputsLog(root / tm.INPUTS_FILE))
            m.attach_port(ResidentCore(100))
            history = start_tracking(m, m._port)  # noqa: SLF001
            track_target(m, history, [(f, Frame(f).row(1, TRACKED, box_at(300, 240))) for f in (11, 12, 13)])
            path = root / tm.INPUTS_FILE
            original = self.lines_of(path)
            kinds = [json.loads(line)["kind"] for line in original]
            index = len(kinds) - 2  # 帧 12 的输入行
            self.assertEqual(kinds[index], "frame")
            path.write_text("\n".join(original[:index] + original[index + 1:]) + "\n", encoding="utf-8")
            tm.replay_tm_inputs(path, tm.DEFAULT_CAPTURE_CONFIG)  # 不抛：旧格式不改判


if __name__ == "__main__":
    unittest.main()
