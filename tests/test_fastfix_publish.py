#!/usr/bin/env python3
"""P1-ENG-FASTFIX-001 AC-1（K1）分级门逐行与交叉用例、兼容 `_gate` 对照；AC-10（K1）门值与参数配置。

零模型：帧包由生产 `FixtureFramePublisher` 写入临时 runtime，帧环/快照仓/发布器全为生产类；时钟为假时钟
（monotonic 与 unix 分开推进，便于单独注入处理超时与采集年龄）。
"""

from __future__ import annotations

import ast
import dataclasses
import json
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import target_manager as tm  # noqa: E402
from controller.gated_publisher import (  # noqa: E402
    LEVEL_INTEGRITY,
    LEVEL_TEMPORAL,
    FrameSnapshotRing,
    GatedPublisher,
    SnapshotRepository,
)
from controller.language_loop import FixtureFramePublisher  # noqa: E402
from controller.track_loop import FrameRepository  # noqa: E402
from tools.eng_fastfix.common import base_source  # noqa: E402


class SplitClock:
    """monotonic 与 unix 各自推进（帧采集时刻取 unix）。"""

    def __init__(self):
        self.mono = 1000.0
        self.wall = 1_800_000_000.0

    def monotonic(self):
        return self.mono

    def unix(self):
        return self.wall


class Inner:
    def __init__(self):
        self.calls = []

    def observation(self, *args):
        self.calls.append(("observation", args[0]))
        return Path("tracking_observation.json")

    def look_at(self, point):
        self.calls.append(("look_at", tuple(point)))
        return Path("gimbal_command.json")

    def body_command(self, command):
        self.calls.append(("body_command", command.mode))
        return Path("body_command.json")

    def hold_body(self):
        self.calls.append(("hold_body", None))

    def set_nadir(self):
        self.calls.append(("set_nadir", None))


class GateRig:
    def __init__(self, case, *, classified=True, frames=3):
        directory = tempfile.TemporaryDirectory()
        case.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.clock = SplitClock()
        self.frames_pub = FixtureFramePublisher(root / "runtime", unix=self.clock.unix)
        self.ring = FrameSnapshotRing(root / "ring", capacity=16, decode=lambda p: p.read_bytes(),
                                      monotonic=self.clock.monotonic, unix=self.clock.unix)
        self.repository = SnapshotRepository(FrameRepository(root / "runtime", image_loader=self.ring.image_loader), self.ring)
        self.inner = Inner()
        self.receipts_path = root / "receipts.jsonl"
        self.publisher = GatedPublisher(
            self.inner, self.ring, frames_directory=root / "runtime" / "frames", receipts_path=self.receipts_path,
            k_pub=2, t_pub_s=0.4, t_stall_s=3.0, track_id="t", monotonic=self.clock.monotonic, unix=self.clock.unix,
            classified=classified, n_drop=3 if classified else None,
        )
        self.publisher.unmute()
        for _ in range(frames):
            self.frames_pub.publish(f"jpeg-{self.frames_pub.next_frame_id}".encode())
        self.frames_dir = root / "runtime" / "frames"

    def load(self, frame_id):
        return self.repository.load(frame_id)

    def receipts(self):
        return [json.loads(line) for line in self.receipts_path.read_text(encoding="utf-8").splitlines()]

    def last(self):
        return self.receipts()[-1]


def hit_reasons(receipt):
    return [(h["reason"], h["level"]) for h in receipt["detail"]["hits"]]


class ClassifyRowTests(unittest.TestCase):
    """§3.1 逐行各一例（假时钟、零模型）。"""

    def observe(self, rig, frame_id):
        rig.publisher.observation(frame_id, "t", (0.1, 0.1, 0.2, 0.2), 0.9)
        return rig.last()

    def test_row1_snapshot_missing_is_integrity_and_terminates(self):
        rig = GateRig(self)
        receipt = self.observe(rig, 1)  # 从未加载
        self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_REJECTED", "bundle_missing"))
        self.assertEqual(hit_reasons(receipt), [("bundle_missing", LEVEL_INTEGRITY)])
        self.assertEqual(rig.publisher.fatal_reason, "bundle_missing")

    def test_row2_not_latest_loaded_is_temporal_drop(self):
        rig = GateRig(self)
        rig.load(1)
        rig.load(2)
        receipt = self.observe(rig, 1)
        self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_DROPPED", "catchup_stale"))
        self.assertEqual(receipt["detail"]["hits"][0]["stale_by"], "not_latest_loaded")
        self.assertIsNone(rig.publisher.fatal_reason)
        self.assertEqual(rig.inner.calls, [])

    def test_row3_identity_checks_are_integrity(self):
        for mutation, expected in (("image", "image_identity_changed"), ("metadata_bad_json", "metadata_invalid"),
                                   ("delete", "bundle_missing")):
            with self.subTest(mutation=mutation):
                rig = GateRig(self)
                rig.load(2)
                stem = rig.frames_dir / "frame_0000000002"
                if mutation == "image":
                    stem.with_suffix(".jpg").write_bytes(b"changed")
                elif mutation == "metadata_bad_json":
                    stem.with_suffix(".json").write_text("{", encoding="utf-8")
                else:
                    stem.with_suffix(".jpg").unlink()
                receipt = self.observe(rig, 2)
                self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_REJECTED", expected))
                self.assertEqual(rig.publisher.fatal_reason, expected)

    def test_row4a_latest_unreadable_is_integrity_and_terminates(self):
        rig = GateRig(self)
        rig.load(2)
        (rig.frames_dir / "latest.json").unlink()
        receipt = self.observe(rig, 2)
        self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_REJECTED", "bundle_missing"))
        self.assertNotIn("load_elapsed_s", receipt["detail"])  # 后续项无法求值，即刻结束

    def test_row4b_rollback_is_integrity(self):
        rig = GateRig(self)
        rig.load(2)
        rig.frames_pub.publish_pointer(0)
        receipt = self.observe(rig, 2)
        self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_REJECTED", "frame_rollback"))

    def test_row4c_frame_delta_is_temporal(self):
        rig = GateRig(self, frames=6)
        rig.load(2)
        receipt = self.observe(rig, 2)  # latest = 5，帧差 3 > K_pub = 2
        self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_DROPPED", "catchup_stale"))
        self.assertEqual(receipt["detail"]["hits"][0]["stale_by"], "frame_delta")
        self.assertIsNone(rig.publisher.fatal_reason)

    def test_row5a_negative_elapsed_is_integrity(self):
        rig = GateRig(self)
        rig.load(2)
        rig.clock.mono -= 0.25
        receipt = self.observe(rig, 2)
        self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_REJECTED", "publish_expired"))
        self.assertEqual(receipt["detail"]["hits"][0]["expired_by"], "negative_elapsed")

    def test_row5b_load_elapsed_over_t_pub_is_temporal(self):
        rig = GateRig(self)
        rig.load(2)
        rig.clock.mono += 0.5
        receipt = self.observe(rig, 2)
        self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_DROPPED", "publish_expired"))
        self.assertEqual(receipt["detail"]["hits"], [{"reason": "publish_expired", "level": LEVEL_TEMPORAL, "step": "5b",
                                                      "expired_by": "load_elapsed"}])
        self.assertAlmostEqual(receipt["detail"]["load_elapsed_s"], 0.5)
        self.assertIsNone(rig.publisher.fatal_reason)

    def test_row5c_missing_capture_unix_is_integrity(self):
        rig = GateRig(self)
        rig.load(2)
        snapshot = rig.ring.snapshot(2)
        rig.ring._snapshots[2] = dataclasses.replace(snapshot, capture_unix_s=None)  # noqa: SLF001 — 只注入信任根字段
        receipt = self.observe(rig, 2)
        self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_REJECTED", "metadata_invalid"))
        self.assertTrue(receipt["detail"]["hits"][0]["capture_unix_missing"])

    def test_row5d_future_capture_is_integrity(self):
        rig = GateRig(self)
        rig.load(2)
        rig.clock.wall -= 1.0
        receipt = self.observe(rig, 2)
        self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_REJECTED", "metadata_invalid"))
        self.assertTrue(receipt["detail"]["capture_age_negative"])

    def test_row5e_capture_age_over_stall_is_integrity(self):
        rig = GateRig(self)
        rig.load(2)
        rig.clock.wall += 3.5
        receipt = self.observe(rig, 2)
        self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_REJECTED", "publish_expired"))
        self.assertEqual(receipt["detail"]["hits"][0]["expired_by"], "capture_age")

    def test_no_hit_passes(self):
        rig = GateRig(self)
        rig.load(2)
        receipt = self.observe(rig, 2)
        self.assertEqual(receipt["outcome"], "WRITTEN")
        self.assertEqual(receipt["detail"]["hits"], [])


class ClassifyCrossTests(unittest.TestCase):
    """交叉用例：完整性优先且致命，`detail.hits` 全列（AC-1）。"""

    def check(self, rig, frame_id, expected_reason, expected_hits):
        rig.publisher.observation(frame_id, "t", (0.1, 0.1, 0.2, 0.2), 0.9)
        receipt = rig.last()
        self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_REJECTED", expected_reason))
        self.assertEqual(hit_reasons(receipt), expected_hits)
        self.assertEqual(rig.publisher.fatal_reason, expected_reason)
        self.assertEqual(rig.inner.calls, [])

    def test_step2_plus_step3(self):
        rig = GateRig(self)
        rig.load(1)
        rig.load(2)
        (rig.frames_dir / "frame_0000000001.jpg").write_bytes(b"changed")
        self.check(rig, 1, "image_identity_changed",
                   [("catchup_stale", LEVEL_TEMPORAL), ("image_identity_changed", LEVEL_INTEGRITY)])

    def test_step4c_plus_step5e(self):
        rig = GateRig(self, frames=6)
        rig.load(2)
        rig.clock.wall += 3.5
        self.check(rig, 2, "publish_expired", [("catchup_stale", LEVEL_TEMPORAL), ("publish_expired", LEVEL_INTEGRITY)])

    def test_step5b_plus_step5d(self):
        rig = GateRig(self)
        rig.load(2)
        rig.clock.mono += 0.5
        rig.clock.wall -= 1.0
        self.check(rig, 2, "metadata_invalid", [("publish_expired", LEVEL_TEMPORAL), ("metadata_invalid", LEVEL_INTEGRITY)])

    def test_step5b_plus_step3(self):
        rig = GateRig(self)
        rig.load(2)
        rig.clock.mono += 0.5
        (rig.frames_dir / "frame_0000000002.jpg").write_bytes(b"changed")
        self.check(rig, 2, "image_identity_changed",
                   [("image_identity_changed", LEVEL_INTEGRITY), ("publish_expired", LEVEL_TEMPORAL)])

    def test_integrity_cannot_be_degraded_on_any_gated_channel(self):
        rig = GateRig(self)
        rig.load(2)
        rig.clock.wall -= 1.0
        rig.publisher.predicted_look_at(2, (1.0, 0.0, 1.0))
        self.assertEqual((rig.last()["channel"], rig.last()["outcome"]), ("predicted_look_at", "PUBLISH_REJECTED"))
        self.assertEqual(rig.publisher.fatal_reason, "metadata_invalid")


class CompatGateTests(unittest.TestCase):
    """兼容模式（`classified=False`）同注入 → `_gate` 首命中、首拒即致命；`_gate` 函数体 diff 为空。"""

    def test_same_injections_first_hit_and_fatal(self):
        cases = [
            ("step2+3", lambda rig: (rig.load(1), rig.load(2),
                                     (rig.frames_dir / "frame_0000000001.jpg").write_bytes(b"x")), 1, "catchup_stale"),
            ("step5b", lambda rig: (rig.load(2), setattr(rig.clock, "mono", rig.clock.mono + 0.5)), 2, "publish_expired"),
            ("step5b+5d", lambda rig: (rig.load(2), setattr(rig.clock, "mono", rig.clock.mono + 0.5),
                                       setattr(rig.clock, "wall", rig.clock.wall - 1.0)), 2, "publish_expired"),
            ("step4c", lambda rig: (rig.frames_pub.publish(b"a"), rig.frames_pub.publish(b"b"),
                                    rig.frames_pub.publish(b"c"), rig.load(2)), 2, "catchup_stale"),
        ]
        for label, inject, frame_id, reason in cases:
            with self.subTest(case=label):
                rig = GateRig(self, classified=False)
                inject(rig)
                rig.publisher.observation(frame_id, "t", (0.1, 0.1, 0.2, 0.2), 0.9)
                receipt = rig.last()
                self.assertEqual((receipt["outcome"], receipt["reason"]), ("PUBLISH_REJECTED", reason))
                self.assertNotIn("hits", receipt["detail"])
                self.assertEqual(rig.publisher.fatal_reason, reason)

    def test_compat_constructor_default_is_unclassified(self):
        rig = GateRig(self, classified=False)
        self.assertFalse(rig.publisher.classified)
        self.assertIsNone(rig.publisher.n_drop)

    def test_gate_function_body_has_no_diff(self):
        base = base_source("controller/gated_publisher.py")
        if base is None:
            self.skipTest("git history unavailable")

        def gate_source(text):
            tree = ast.parse(text)
            cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GatedPublisher")
            node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "_gate")
            return ast.get_source_segment(text, node)

        current = (PROJECT_ROOT / "controller" / "gated_publisher.py").read_text(encoding="utf-8")
        self.assertEqual(gate_source(current), gate_source(base))


def write_config(directory, **overrides):
    params = {
        "t_pub_s": {"value": 0.4, "category": "contract_inherited"},
        "k_pub": {"value": 2, "category": "contract_inherited"},
        "n_drop_frames": {"value": 3, "category": "design_budget"},
        "t_reacq_frames": {"value": 10, "category": "design_budget"},
        "auto_reacquire": {"value": "on", "category": "config_axis"},
    }
    for key, value in overrides.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = value
    path = Path(directory) / "fastfix.json"
    path.write_text(json.dumps({"schema_version": tm.FASTFIX_SCHEMA, "params": params}), encoding="utf-8")
    return path


class ConfigTests(unittest.TestCase):
    """AC-10：参数读自 `config/p1-eng-fastfix-001.json`，违反结构约束拒绝启动；首候选 = 现行常数；无 `ρ_reacq`。"""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = directory.name
        self.capture, _sha, _text = tm.load_capture_config(tm.DEFAULT_CAPTURE_CONFIG)

    def test_shipped_config_equals_current_constants(self):
        from controller.language_loop import K_PUB  # noqa: PLC0415

        params, sha, _text = tm.load_fastfix_config(tm.DEFAULT_FASTFIX_CONFIG, self.capture, 5.0)
        self.assertEqual((params.t_pub_s, params.k_pub), (K_PUB / 5.0, K_PUB))
        self.assertEqual((params.n_drop, params.t_reacq, params.auto_reacquire), (3, 10, True))
        self.assertEqual(len(sha), 64)
        document = json.loads(tm.DEFAULT_FASTFIX_CONFIG.read_text(encoding="utf-8"))
        self.assertNotIn("rho_reacq", document["params"])
        self.assertEqual(set(document["params"]), set(tm.FASTFIX_PARAMS))

    def test_structural_violations_refuse_to_start(self):
        bad = {
            "t_pub_mismatch": {"t_pub_s": {"value": 0.5, "category": "contract_inherited"}},
            "pair_not_signed": {"t_pub_s": {"value": 0.8, "category": "contract_inherited"},
                                "k_pub": {"value": 4, "category": "contract_inherited"}},
            "k_pub_zero": {"k_pub": {"value": 0, "category": "contract_inherited"}},
            "n_drop_over_t_report": {"n_drop_frames": {"value": 4, "category": "design_budget"}},
            "n_drop_zero": {"n_drop_frames": {"value": 0, "category": "design_budget"}},
            "t_reacq_short": {"t_reacq_frames": {"value": 2, "category": "design_budget"}},
            "auto_bad": {"auto_reacquire": {"value": "maybe", "category": "config_axis"}},
            "wrong_category": {"n_drop_frames": {"value": 3, "category": "to_calibrate"}},
            "rho_present": {"rho_reacq": {"value": 1.5, "category": "design_budget"}},
            "missing": {"t_reacq_frames": None},
        }
        for label, overrides in bad.items():
            with self.subTest(label=label):
                with self.assertRaises(tm.FastfixConfigInvalid):
                    tm.load_fastfix_config(write_config(self.dir, **overrides), self.capture, 5.0)

    def test_signed_alternative_pair_is_accepted(self):
        path = write_config(self.dir, t_pub_s={"value": 0.6, "category": "contract_inherited"},
                            k_pub={"value": 3, "category": "contract_inherited"})
        params, _sha, _text = tm.load_fastfix_config(path, self.capture, 5.0)
        self.assertEqual((params.t_pub_s, params.k_pub), (0.6, 3))

    def test_frozen_constants_have_no_diff(self):
        base = base_source("controller/language_loop.py")
        if base is None:
            self.skipTest("git history unavailable")

        def literal(text, name):
            for node in ast.parse(text).body:
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
                    return ast.literal_eval(node.value)
            raise LookupError(name)

        current = (PROJECT_ROOT / "controller" / "language_loop.py").read_text(encoding="utf-8")
        for name in ("K_PUB", "T_STALL_S", "RESIDENT_REBUILD_LIMIT"):
            self.assertEqual(literal(current, name), literal(base, name), name)

    def test_capture_session_reads_config_and_refuses_bad_one(self):
        from controller.language_loop import ConfigMismatch, LanguageSession, SessionConfig  # noqa: PLC0415

        root = Path(self.dir)
        runtime = root / "runtime"
        runtime.mkdir()

        def config(**extra):
            return SessionConfig(session_id="cfg", session_root=root / "sessions", runtime=runtime, receipt=None, adapter=None,
                                 tracker_name="det-assoc-v1", tracker_factory=lambda: None, resident=True, language=False,
                                 pid=1, is_alive=lambda pid: True, **extra)

        session = LanguageSession(config())
        self.assertEqual((session.receipt.k_pub, session.receipt.t_pub_s), (2, 0.4))
        self.assertEqual(session.fastfix.n_drop, 3)
        with self.assertRaises(ConfigMismatch):
            LanguageSession(config(fastfix_config=write_config(self.dir, n_drop_frames={"value": 9, "category": "design_budget"})))


if __name__ == "__main__":
    unittest.main()
