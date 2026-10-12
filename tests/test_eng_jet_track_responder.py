#!/usr/bin/env python3
"""P1-ENG-JET-001 SR (b) 真实应答器（AC-5/AC-6）与断链分析：零硬件、零模型（插件与检测函数用注入的假件）。

- init 框只取首帧检测器自身 `target` 类最高分框（`select_init_box`），不读真值；
- 引擎身份不符即不加载（不调用插件工厂）；
- 真实 `TrackLoop` 绑定同一 `frame_id` 写观测，逐帧记录键 `state` 改名 `loop_state`（AC-12 禁键）；
- 帧缺口 → TrackLoop 终止（GAP），应答器不重播种、继续存活并记录新到帧；
- 本机进程内回环（板侧中继 + 真实应答器 + 桌面机中继 + 软件定时断链）→ `relay.analyze` 的回程与断链分析字段；
- 回稳读法（预注册）在合成收据上的计算。
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_jet import assets, common, evidence, relay, replay_publish, track_responder  # noqa: E402

A7 = common.a7_frames_dir()
ROWS = [[0.10, 0.10, 0.05, 0.05, 0.99, 0.0], [0.44, 0.70, 0.05, 0.15, 0.90, 1.0], [0.50, 0.50, 0.05, 0.05, 0.80, 1.0]]


def free_port() -> int | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]
    except PermissionError:
        return None


class FakePlugin:
    """compat 插件假件：init 记录框；update 在给定帧号集合上返回丢失，其余返回固定框。"""

    def __init__(self):
        from controller.trackers import TrackerResult  # noqa: PLC0415

        self.result = TrackerResult
        self.inits: list[list[float]] = []
        self.updates = 0

    def init(self, image, box):
        self.inits.append(list(box))
        return True

    def update(self, image):
        self.updates += 1
        return self.result((0.40, 0.40, 0.10, 0.10), True, 0.9, "tracker")

    def manifest_identity(self):
        return {"tracker": "fake"}


def fake_factory(rows=ROWS):
    calls = []

    def factory(engine):
        calls.append(engine)
        plugin = FakePlugin()
        factory.plugin = plugin
        return plugin, (lambda image: [list(r) for r in rows]), {}

    factory.calls = calls
    return factory


def publish(runtime: Path, frame_id: int, source_index: int) -> None:
    jpeg = (A7 / common.frame_name(source_index, "jpg")).read_bytes()
    meta = json.loads((A7 / common.frame_name(source_index, "json")).read_text(encoding="utf-8"))
    replay_publish.publish_frame(runtime, frame_id, jpeg, replay_publish.rewrite_metadata(meta, frame_id, time.time(), time.monotonic()))


class SelectInitBox(unittest.TestCase):
    def test_highest_target_class_only(self):
        pick = track_responder.select_init_box(ROWS, 1)
        self.assertEqual(pick["box_norm"], [0.44, 0.70, 0.05, 0.15])
        self.assertEqual((pick["score"], pick["class_id"], pick["candidates_target_class"], pick["detections_total"]), (0.90, 1, 2, 3))

    def test_none_without_target_class(self):
        self.assertIsNone(track_responder.select_init_box([[0.1, 0.1, 0.1, 0.1, 0.99, 0.0]], 1))

    def test_target_class_from_frozen_spec(self):
        spec = common.read_json(PROJECT_ROOT / "config" / "det-assoc-v1.models.json")
        self.assertEqual(track_responder.target_class_id(spec), 1)

    def test_engine_resolved_from_fastlayer_evidence(self):
        engine = track_responder.engine_from_fastlayer()
        evidence = common.read_json(common.evidence("fastlayer.json"))["S1"]["engines"]["640"]["export"]
        self.assertEqual((engine["engine"], engine["sha256"]), (evidence["engine"], evidence["sha256"]))


@unittest.skipUnless((A7 / "frame_0000000012.jpg").is_file(), "a7 帧不在本机（只读源）")
class ResponderInProcess(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="eng-jet-track-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.runtime, self.logs = self.tmp / "rt", self.tmp / "log"
        self.engine = self.tmp / "fake.engine"
        self.engine.write_bytes(b"engine-bytes")
        self.sha = common.sha256_file(self.engine)

    def _responder(self, factory, sha=None):
        return track_responder.TrackResponder(self.runtime, self.logs, self.engine, sha or self.sha, factory=factory,
                                              image_loader=lambda path: path.read_bytes(), poll_s=0.005)

    def _run(self, responder, duration, frames):
        result: dict = {}
        thread = threading.Thread(target=lambda: result.update(responder.run(duration)))
        thread.start()
        for fid, src, pause in frames:
            publish(self.runtime, fid, src)
            time.sleep(pause)
        thread.join(timeout=duration + 10)
        return result, common.read_jsonl(self.logs / "track-receipts.jsonl")

    def test_init_from_detector_and_observation_bound(self):
        factory = fake_factory()
        result, rows = self._run(self._responder(factory), 2.5, [(i, i, 0.1) for i in range(6)])
        self.assertEqual(result["outcome"], "COMPLETED")
        self.assertEqual([[round(v, 9) for v in box] for box in factory.plugin.inits], [[0.44, 0.70, 0.05, 0.15]])
        init = next(r for r in rows if r["ev"] == "init_detection")
        self.assertEqual(init["frame_id"], 0)
        self.assertIn("非真值", init["init_source"])
        observation = json.loads((self.runtime / "tracking_observation.json").read_text())
        self.assertEqual(observation["observation"]["frame_id"], 5)
        self.assertEqual(observation["observation"]["track_id"], track_responder.TRACK_ID)
        processes = [r for r in rows if r["ev"] == "process"]
        self.assertGreaterEqual(sum(r["processed"] for r in processes), 5)
        self.assertTrue(all(r["capture_age_s"] is not None and r["load_elapsed_s"] is not None for r in processes))
        written = {r["frame_id"] for r in rows if r["ev"] == "bridge_write" and r["kind"] == "observation"}
        self.assertTrue({r["latest"] for r in processes} <= written)
        records_text = (self.logs / "track-records.jsonl").read_text()
        self.assertNotRegex(records_text, assets.FORBIDDEN_KEY)
        records = common.read_jsonl(self.logs / "track-records.jsonl")
        self.assertEqual(records[0]["event"], "INIT")
        self.assertTrue(all("loop_state" in r and "frame_age_ms" in r for r in records))

    def test_gap_terminates_without_reseed(self):
        factory = fake_factory()
        frames = [(0, 0, 0.1), (1, 1, 0.1), (2, 2, 0.4)]
        result: dict = {}
        responder = self._responder(factory)
        thread = threading.Thread(target=lambda: result.update(responder.run(3.0)))
        thread.start()
        for fid, src, pause in frames:
            publish(self.runtime, fid, src)
            time.sleep(pause)
        frames_dir = self.runtime / "frames"
        publish(self.runtime, 9, 9)
        for gone in range(3, 9):  # 断链期间未送达的帧：板上不存在
            for suffix in ("jpg", "json"):
                (frames_dir / common.frame_name(gone, suffix)).unlink(missing_ok=True)
        time.sleep(0.4)
        publish(self.runtime, 10, 10)
        time.sleep(0.3)
        thread.join(timeout=10)
        rows = common.read_jsonl(self.logs / "track-receipts.jsonl")
        self.assertEqual(result["outcome"], "TERMINAL")
        self.assertEqual(len(factory.plugin.inits), 1)
        terminal = [r for r in rows if r["ev"] == "terminal"]
        self.assertEqual(len(terminal), 1)
        self.assertEqual((terminal[0]["loop_event"], terminal[0]["latest"]), ("GAP", 9))
        self.assertGreaterEqual(sum(1 for r in rows if r["ev"] == "post_terminal_frame"), 1)
        self.assertEqual(rows[-1]["ev"], "stop")

    def test_engine_identity_mismatch_does_not_load(self):
        factory = fake_factory()
        result, rows = self._run(self._responder(factory, sha="0" * 64), 0.5, [])
        self.assertEqual(result["outcome"], "ENGINE_IDENTITY_MISMATCH")
        self.assertEqual(factory.calls, [])
        self.assertTrue(any(r["ev"] == "engine_identity_mismatch" for r in rows))

    def test_no_target_detection_no_init(self):
        factory = fake_factory(rows=[[0.1, 0.1, 0.1, 0.1, 0.99, 0.0]])
        result, rows = self._run(self._responder(factory), 1.0, [(0, 0, 0.1), (1, 1, 0.1)])
        self.assertEqual(result["outcome"], "INIT_NO_TARGET_DETECTION")
        self.assertEqual(factory.plugin.inits, [])
        self.assertFalse((self.runtime / "tracking_observation.json").exists())


@unittest.skipUnless((A7 / "frame_0000000040.jpg").is_file(), "a7 帧不在本机（只读源）")
class LoopbackTrackWithDrop(unittest.TestCase):
    """进程内回环：板侧中继 + 真实应答器（假插件）+ 桌面机中继（软件定时断链 1.5 s）+ 回放器 10 Hz。"""

    def test_analyze_track_return_and_disconnect(self):
        port = free_port()
        if port is None:
            self.skipTest("环境拒绝 loopback 绑定（受限沙箱）")
        tmp = Path(tempfile.mkdtemp(prefix="eng-jet-trackloop-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        board_rt, desk_rt, board_log, desk_log = tmp / "board-rt", tmp / "desk-rt", tmp / "board-log", tmp / "desk-log"
        engine = tmp / "fake.engine"
        engine.write_bytes(b"x")
        replay_publish.reset_runtime(desk_rt)
        board = relay.BoardRelay(board_rt, board_log, port=port, bind="127.0.0.1")
        responder = track_responder.TrackResponder(board_rt, board_log, engine, common.sha256_file(engine), factory=fake_factory(),
                                                   image_loader=lambda path: path.read_bytes(), poll_s=0.005)
        desktop = relay.DesktopRelay(desk_rt, desk_log, "127.0.0.1", port, drops=[(2.0, 1.5)])
        threads = [threading.Thread(target=board.run, args=(9.0,)), threading.Thread(target=responder.run, args=(8.5,)),
                   threading.Thread(target=desktop.run, args=(7.5,))]
        for thread in threads:
            thread.start()
        time.sleep(0.5)
        receipts = tmp / "replay.jsonl"
        replay_publish.replay(A7, desk_rt, 60, 10.0, receipts, reset=False)
        for thread in threads:
            thread.join(timeout=20)
        result = relay.analyze(desk_log, board_log, receipts)
        self.assertEqual(result["responder"], "track")
        self.assertEqual(result["order_violations"], 0)
        self.assertEqual(result["latest_pointing_to_incomplete_bundle"], 0)
        track = result["return_track"]
        self.assertGreater(track["return_latency_ms"]["n"], 0)
        self.assertEqual(track["init_detection"]["pick"]["class_id"], 1)
        self.assertEqual([t["loop_event"] for t in track["terminal"]], ["GAP"])
        self.assertEqual(track["outcome"], "TERMINAL")
        self.assertEqual(result["process_stops"], {"desktop_relay": True, "board_relay": True, "responder": True})
        (drop,) = result["disconnects"]
        self.assertGreater(drop["frame_id_gap_after_recovery"], 5)
        self.assertEqual(drop["latest_frame_diff"], drop["frame_id_gap_after_recovery"] + 1)
        self.assertEqual(drop["board_bridge_writes_during_disconnect"]["publish_latest"], 0)
        self.assertTrue(drop["no_backfill"])
        self.assertEqual(len(drop["trackloop"]["terminal_after_this_drop"]), 1)
        self.assertIn("recovered", drop["recovery"])


class SrBundle(unittest.TestCase):
    def test_bundle_is_code_only_and_covers_trackloop_imports(self):
        files = set(assets.SR_CODE_FILES)
        self.assertIn("controller/track_loop.py", files)
        self.assertIn("tools/eng_jet/track_responder.py", files)
        for rel in files:
            self.assertTrue((PROJECT_ROOT / rel).is_file(), rel)
            self.assertIsNone(assets.FORBIDDEN_PATH.search(rel), rel)
            self.assertTrue(rel.startswith(("tools/eng_jet/", "controller/", "config/")), rel)
        probe = subprocess.run([sys.executable, "-c", "import sys, controller.track_loop, controller.det_assoc_tracker; "
                                "print('\\n'.join(sorted(m for m in sys.modules if m.startswith('controller.'))))"],
                               cwd=PROJECT_ROOT, capture_output=True, text=True, check=True)
        loaded = {f"controller/{name.split('.', 1)[1]}.py" for name in probe.stdout.split()}
        self.assertIn("controller/track_loop.py", loaded)
        self.assertEqual(loaded - files, set())


class SrForwardLine(unittest.TestCase):
    """§2.1 SR forward 通过线（AC-4 修订 1）：≥ 1,500 包、完整率 100%、顺序违反 0、指向不完整包 0、sha 不符 0。"""

    BASE = {"bundles_sent": 1500, "completeness": 1.0, "order_violations": 0, "latest_pointing_to_incomplete_bundle": 0, "board_sha_mismatch": 0}

    def test_pass_line(self):
        self.assertTrue(evidence._forward_ok(self.BASE))

    def test_each_component_fails(self):
        for key, value in (("bundles_sent", 1499), ("completeness", 0.999), ("order_violations", 1),
                           ("latest_pointing_to_incomplete_bundle", 1), ("board_sha_mismatch", 1)):
            self.assertFalse(evidence._forward_ok({**self.BASE, key: value}), key)


class RecoveryRule(unittest.TestCase):
    """回稳读法（预注册）：基线 = 断链前 60 s p95；连续 10 帧 ≤ 阈值即回稳。"""

    def _scenario(self):
        offset = 0.5
        replay, publishes, desk, board = [], {}, [], []
        t0 = 1000.0
        for fid in range(200):
            t = t0 + fid * 0.2
            replay.append({"frame_id": fid, "published_unix_s": t})
        syncs = [{"t1": t0 + k, "offset_s": offset, "delay_s": 0.001} for k in range(60)]
        drop_t, reconnect_t = t0 + 10.0, t0 + 14.1
        desk += [{"ev": "connect", "unix": t0 - 1}, {"ev": "drop_start", "unix": drop_t, "length_s": 4.0, "planned_at_s": 10.0},
                 {"ev": "connect", "unix": reconnect_t}]
        for fid in range(200):
            t = t0 + fid * 0.2
            if drop_t <= t < reconnect_t - 0.2:
                continue
            latency = 0.050 if fid < 70 else (0.300 if fid < 74 else 0.040)
            desk.append({"ev": "send_bundle", "frame_id": fid, "unix": t})
            publishes[fid] = {"frame_id": fid, "pub_unix": t + offset + latency, "arrive_unix": t + offset + latency}
            board.append({"ev": "publish", **publishes[fid]})
        return desk, board, syncs, replay, publishes

    def test_gap_backfill_and_recovery(self):
        desk, board, syncs, replay, publishes = self._scenario()
        arrivals = relay._arrivals(publishes, {r["frame_id"]: r for r in replay}, syncs)
        (drop,) = relay.disconnect_analysis(desk, board, syncs, replay, arrivals)
        self.assertEqual((drop["last_published_before"], drop["first_published_after"]), (49, 70))
        self.assertEqual((drop["frame_id_gap_after_recovery"], drop["latest_frame_diff"]), (20, 21))
        self.assertTrue(drop["no_backfill"])
        self.assertEqual(drop["of_which_sent"], [70])
        self.assertAlmostEqual(drop["steady_threshold_ms"], 50.0, places=3)
        self.assertEqual(drop["recovery"]["frame_id"], 74)
        self.assertTrue(drop["recovery"]["recovered"])
        self.assertTrue(drop["recovery"]["within_limit"])
        self.assertAlmostEqual(drop["recovery"]["recovery_s"], 0.7, places=3)

    def test_never_recovers(self):
        arrivals = {fid: {"desktop_pub": 100.0 + fid, "board_pub": 0.0, "raw_ms": 0.0, "ms": 500.0} for fid in range(30)}
        self.assertFalse(relay.recovery_after(arrivals, 100.0, 50.0)["recovered"])


if __name__ == "__main__":
    unittest.main()
