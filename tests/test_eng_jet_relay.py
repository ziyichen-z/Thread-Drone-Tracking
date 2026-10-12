#!/usr/bin/env python3
"""P1-ENG-JET-001 AC-4（中继完整性/顺序/原子发布）、AC-5/AC-6 的实现侧行为：本机双进程回环，零硬件、零模型。

- `test_atomic_publish_order`：板侧中继、回声应答器、桌面机中继各为独立进程（127.0.0.1），回放器 10 Hz 发布；
  断言包完整率 100%、顺序零违反、板上 `latest.json` 从不指向不完整包、回程观测绑定同一 `frame_id` 回到桌面机。
- 进程内单元：板侧拒发不完整/乱序/越界路径/sha 不符的包；断链期间不缓存补发；四时戳对时算式；回放器只改帧号与时钟。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
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

from tools.eng_jet import common, relay, replay_publish  # noqa: E402

A7 = common.a7_frames_dir()


def free_port() -> int | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]
    except PermissionError:
        return None


def _manifest(frame_id: int) -> bytes:
    return json.dumps({"schema_version": "tethered-frame-manifest/v1", "frame_id": frame_id,
                       "image_file": common.frame_name(frame_id, "jpg"), "metadata_file": common.frame_name(frame_id, "json"),
                       "published_unix_s": time.time()}).encode("utf-8")


def _file_header(path: str, payload: bytes, *, sha: str | None = None) -> dict:
    return {"kind": "file", "path": path, "size": len(payload), "sha256": sha or common.sha256_bytes(payload), "seq": 1,
            "send_unix": time.time()}


@unittest.skipUnless((A7 / "frame_0000000000.jpg").is_file(), "a7 帧不在本机（只读源）")
class LoopbackTwoProcess(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="eng-jet-relay-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.port = free_port()
        if self.port is None:
            self.skipTest("环境拒绝 loopback 绑定（受限沙箱）")
        self.procs: list[subprocess.Popen] = []
        self.addCleanup(self._kill)

    def _kill(self):
        for proc in self.procs:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)

    def _spawn(self, *args: str) -> subprocess.Popen:
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        log = (self.tmp / f"{args[0]}.out").open("wb")
        self.addCleanup(log.close)
        proc = subprocess.Popen([sys.executable, "-m", "tools.eng_jet.relay", *args], cwd=PROJECT_ROOT, env=env,
                                stdout=log, stderr=subprocess.STDOUT)
        self.procs.append(proc)
        return proc

    def test_atomic_publish_order(self):
        board_rt, desk_rt = self.tmp / "board-rt", self.tmp / "desk-rt"
        board_log, desk_log = self.tmp / "board-log", self.tmp / "desk-log"
        replay_publish.reset_runtime(desk_rt)
        frames, hz = 25, 10.0
        board = self._spawn("board", "--runtime", str(board_rt), "--log-dir", str(board_log), "--port", str(self.port),
                            "--bind", "127.0.0.1", "--duration-s", "9")
        echo = self._spawn("echo", "--runtime", str(board_rt), "--log-dir", str(board_log), "--duration-s", "8")
        desk = self._spawn("desktop", "--runtime", str(desk_rt), "--log-dir", str(desk_log), "--host", "127.0.0.1",
                           "--port", str(self.port), "--duration-s", "7")
        time.sleep(1.0)
        receipts = self.tmp / "replay.jsonl"
        replay_publish.replay(A7, desk_rt, frames, hz, receipts, reset=False)
        for proc in (desk, echo, board):
            proc.wait(timeout=20)
        result = relay.analyze(desk_log, board_log, receipts)
        self.assertEqual(result["bundles_sent"], frames)
        self.assertEqual(result["completeness"], 1.0)
        self.assertEqual(result["order_violations"], 0)
        self.assertEqual(result["latest_pointing_to_incomplete_bundle"], 0)
        self.assertEqual(result["board_sha_mismatch"], 0)
        # 板上最终指针 = 最后一帧，成员与源字节一致。
        manifest = json.loads((board_rt / "frames" / "latest.json").read_text())
        self.assertEqual(manifest["frame_id"], frames - 1)
        source = {r["frame_id"]: r for r in common.read_jsonl(receipts)}
        self.assertEqual(common.sha256_file(board_rt / "frames" / manifest["image_file"]), source[frames - 1]["image_sha256"])
        # 发布顺序：每次 publish 之前两成员都已收到（按到达单调时钟），且 frame_id 严格递增。
        board_rows = common.read_jsonl(board_log / "relay-receipts.jsonl")
        seen: dict[int, set] = {}
        last = -1
        for row in board_rows:
            if row["ev"] == "recv_member":
                seen.setdefault(row["frame_id"], set()).add(row["path"].rsplit(".", 1)[1])
            elif row["ev"] == "publish":
                self.assertEqual(seen.get(row["frame_id"]), {"jpg", "json"})
                self.assertGreater(row["frame_id"], last)
                last = row["frame_id"]
        # 回程：桌面机收到绑定最后一帧的观测。
        observation = json.loads((desk_rt / "tracking_observation.json").read_text())
        self.assertEqual(observation["observation"]["frame_id"], frames - 1)
        self.assertEqual(result["return_echo"]["echoes"], frames)
        self.assertGreaterEqual(result["clock"]["samples"], 3)


    def test_clock_sync_recovers_after_stall(self):
        """冒烟轮缺陷回归：板侧进程停顿 4 s 后恢复，迟到的旧对时应答不得使请求/应答永久错位。"""
        board_rt, desk_rt = self.tmp / "board-rt", self.tmp / "desk-rt"
        replay_publish.reset_runtime(desk_rt)
        board = self._spawn("board", "--runtime", str(board_rt), "--log-dir", str(self.tmp / "board-log"), "--port", str(self.port),
                            "--bind", "127.0.0.1", "--duration-s", "16")
        desk = self._spawn("desktop", "--runtime", str(desk_rt), "--log-dir", str(self.tmp / "desk-log"), "--host", "127.0.0.1",
                           "--port", str(self.port), "--duration-s", "14")
        time.sleep(3.5)
        os.kill(board.pid, signal.SIGSTOP)
        time.sleep(4.0)
        resumed = time.time()
        os.kill(board.pid, signal.SIGCONT)
        desk.wait(timeout=30)
        board.wait(timeout=30)
        rows = common.read_jsonl(self.tmp / "desk-log" / "clock-sync.jsonl")
        after = [r for r in rows if r["ev"] == "sync" and r["t1"] > resumed + 1.0]
        self.assertGreaterEqual(len(after), 3, rows[-6:])
        self.assertGreater(sum(r.get("stale_discarded", 0) for r in rows if r["ev"] == "sync"), 0)


class SyncReplyMatching(unittest.TestCase):
    class FakeUDP:
        def __init__(self, replies):
            self.replies = list(replies)

        def settimeout(self, value):
            self.timeout = value

        def recvfrom(self, size):
            if not self.replies:
                raise socket.timeout("empty")
            return json.dumps(self.replies.pop(0)).encode("utf-8"), ("127.0.0.1", 1)

    def test_stale_replies_discarded(self):
        udp = self.FakeUDP([{"seq": 3, "t2": 1.0, "t3": 1.0}, {"seq": 4, "t2": 2.0, "t3": 2.0}, {"seq": 5, "t2": 3.0, "t3": 3.1}])
        reply, _t4, stale = relay.recv_matching(udp, 5, 1.0)
        self.assertEqual((reply["seq"], stale), (5, 2))

    def test_timeout_when_only_stale(self):
        with self.assertRaises(socket.timeout):
            relay.recv_matching(self.FakeUDP([{"seq": 1}, {"seq": 2}]), 7, 0.2)


class BoardRelayInProcess(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="eng-jet-board-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.board = relay.BoardRelay(self.tmp / "rt", self.tmp / "log", port=0)
        self.addCleanup(self.board.receipts.close)

    def _send(self, path: str, payload: bytes, **kw):
        self.board.handle_file(_file_header(path, payload, **kw), payload)

    def _bundle(self, frame_id: int, *, pointer: bool = True):
        self._send(f"frames/{common.frame_name(frame_id, 'jpg')}", b"jpeg-%d" % frame_id)
        self._send(f"frames/{common.frame_name(frame_id, 'json')}", b'{"frame_id": %d}' % frame_id)
        if pointer:
            self._send(relay.FORWARD_POINTER, _manifest(frame_id))

    def latest(self) -> int | None:
        path = self.tmp / "rt" / "frames" / "latest.json"
        return json.loads(path.read_text())["frame_id"] if path.exists() else None

    def test_pointer_refused_until_members_complete(self):
        self._send(f"frames/{common.frame_name(3, 'jpg')}", b"jpeg")
        self._send(relay.FORWARD_POINTER, _manifest(3))
        self.assertIsNone(self.latest())
        self.assertEqual(self.board.counters["refused_incomplete"], 1)
        self._send(f"frames/{common.frame_name(3, 'json')}", b"{}")
        self._send(relay.FORWARD_POINTER, _manifest(3))
        self.assertEqual(self.latest(), 3)

    def test_order_violation_not_published(self):
        self._bundle(5)
        self._bundle(4)
        self.assertEqual(self.latest(), 5)
        self.assertEqual(self.board.counters["order_violation"], 1)

    def test_sha_mismatch_and_paths_rejected(self):
        self._send(f"frames/{common.frame_name(1, 'jpg')}", b"jpeg", sha="0" * 64)
        self.assertFalse((self.tmp / "rt" / "frames" / common.frame_name(1, "jpg")).exists())
        for path in ("truth/frame_0000000001.json", "../escape.json", "frames/../../x.jpg", "language_request.json", "frames/frame_1.jpg"):
            self._send(path, b"x")
        self.assertEqual(self.board.counters["sha_mismatch"], 1)
        self.assertEqual(self.board.counters["rejected_path"], 5)
        self.assertFalse((self.tmp / "escape.json").exists())

    def test_retention_prunes_old_members(self):
        self.board.retain = 3
        for frame_id in range(6):
            self._bundle(frame_id)
        remaining = sorted(p.name for p in (self.tmp / "rt" / "frames").glob("frame_*.jpg"))
        self.assertEqual(remaining, [common.frame_name(i, "jpg") for i in (3, 4, 5)])


    def test_reconnect_resends_current_return_version(self):
        """复核 R1-1 回归（零模型、无套接字）：同一连接内回程按内容去重；新连接（`adopt_link`）清空去重状态，
        一轮内重发每个回程文件的当前版本（只发当前版本、不补发历史版本）。修补前 `_last_return` 跨连接保留，本例必失败。"""
        payload = b'{"frame_id": 7}'
        (self.tmp / "rt" / "tracking_observation.json").write_bytes(payload)
        first = FakeLink()
        self.board.adopt_link(first)
        self.assertEqual(self.board.return_once(), 1)
        self.assertEqual(self.board.return_once(), 0)
        self.assertEqual(self.board._last_return["tracking_observation.json"], common.sha256_bytes(payload))
        second = FakeLink()
        self.board.adopt_link(second)
        self.assertFalse(first.alive)
        self.assertEqual(self.board.members, {})
        self.assertEqual(self.board.return_once(), 1)
        self.assertEqual([(h["path"], body) for h, body in second.sent], [("tracking_observation.json", payload)])
        self.assertEqual(self.board.return_once(), 0)
        self.assertEqual(self.board.counters["returns_sent"], 2)

    def test_adopt_during_return_send_keeps_new_link_dedup_clean(self):
        """复核 R2-1 回归（零模型、无套接字）：旧连接 `send` 已返回、去重写回之前，accept 线程 `adopt_link(new)`
        换连接并清空去重状态；旧轮次的 digest 写回不得落进新连接的去重状态，新连接下一轮内收到当前版本。
        用在 `send` 返回前调用 `adopt_link` 的连接替身把该交错确定化。修补前写回覆盖清空，新连接一轮发 0，本例必失败。"""
        payload = b'{"frame_id": 9}'
        (self.tmp / "rt" / "tracking_observation.json").write_bytes(payload)
        board, new = self.board, FakeLink()

        class AdoptOnSendLink(FakeLink):
            def send(inner, header, payload=b""):
                head = FakeLink.send(inner, header, payload)
                if board.link is inner:
                    board.adopt_link(new)
                return head

        old = AdoptOnSendLink()
        board.adopt_link(old)
        self.assertEqual(board.return_once(), 1)
        self.assertEqual([h["path"] for h, _ in old.sent], ["tracking_observation.json"])
        self.assertFalse(old.alive)
        self.assertIs(board.link, new)
        self.assertNotIn("tracking_observation.json", board._last_return)
        self.assertEqual(board.return_once(), 1)
        self.assertEqual([(h["path"], body) for h, body in new.sent], [("tracking_observation.json", payload)])
        self.assertEqual(board._last_return["tracking_observation.json"], common.sha256_bytes(payload))
        self.assertEqual(board.return_once(), 0)
        board.receipts.close()
        sends = [json.loads(line) for line in (self.tmp / "log" / "relay-receipts.jsonl").read_text().splitlines()
                 if json.loads(line)["ev"] == "send_return"]
        self.assertEqual([e.get("link_replaced", False) for e in sends], [True, False])


class AnalyzeLinkEventsFull(unittest.TestCase):
    """复核 R1-2 回归（零模型，合成收据）：`analyze` 不截断 `link_events`，并给出全量计数 `link_events_total`。"""

    def test_more_than_fifty_link_events_kept(self):
        tmp = Path(tempfile.mkdtemp(prefix="eng-jet-analyze-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        desk, board = tmp / "desktop", tmp / "board"
        desk.mkdir()
        board.mkdir()
        events = [{"ev": "connect" if i % 2 == 0 else "disconnect", "unix": 1000.0 + i, "reason": None if i % 2 == 0 else "OSError"}
                  for i in range(61)]
        (desk / "relay-receipts.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
        (desk / "clock-sync.jsonl").write_text("")
        (board / "relay-receipts.jsonl").write_text("")
        (desk / "replay-receipts.jsonl").write_text("")
        out = relay.analyze(desk, board, desk / "replay-receipts.jsonl")
        self.assertEqual(out["link_events_total"], 61)
        self.assertEqual(len(out["link_events"]), 61)
        self.assertEqual(out["link_events"][-1]["unix"], 1060.0)


class FakeLink:
    def __init__(self):
        self.alive = True
        self.sent = []

    def send(self, header, payload=b""):
        head = {**header, "seq": len(self.sent) + 1, "send_unix": time.time(), "send_mono": time.monotonic(),
                "sha256": common.sha256_bytes(payload)}
        self.sent.append((head, payload))
        return head

    def close(self):
        self.alive = False


@unittest.skipUnless((A7 / "frame_0000000000.jpg").is_file(), "a7 帧不在本机（只读源）")
class DesktopNoBacklog(unittest.TestCase):
    def test_no_backlog_after_link_loss(self):
        tmp = Path(tempfile.mkdtemp(prefix="eng-jet-desk-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        rt = tmp / "rt"
        replay_publish.reset_runtime(rt)
        desk = relay.DesktopRelay(rt, tmp / "log", "127.0.0.1", 1)
        self.addCleanup(desk.sync_log.close)
        self.addCleanup(desk.receipts.close)
        meta = json.loads((A7 / "frame_0000000000.json").read_text())
        jpeg = (A7 / "frame_0000000000.jpg").read_bytes()
        for frame_id in range(3):  # 断链期间发布 3 帧：不发送、不排队
            replay_publish.publish_frame(rt, frame_id, jpeg, replay_publish.rewrite_metadata(meta, frame_id, time.time(), time.monotonic()))
            desk.forward_once()
        link = FakeLink()
        desk.link = link
        desk.forward_once()
        desk.forward_once()
        paths = [h["path"] for h, _ in link.sent]
        self.assertEqual(paths, [f"frames/{common.frame_name(2, 'jpg')}", f"frames/{common.frame_name(2, 'json')}", relay.FORWARD_POINTER])


class DesktopStalePointer(unittest.TestCase):
    """K1K3K4补跑F 返工回归（正式轮 f1-echo 的 RELAY_INTEGRITY）：运行目录残留的旧会话 `latest.json` 不得被转发；
    本会话新发布的帧（含与旧帧同号者）照常转发。"""

    def test_stale_pointer_from_previous_session_not_forwarded(self):
        tmp = Path(tempfile.mkdtemp(prefix="eng-jet-stale-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        rt = tmp / "rt"
        replay_publish.reset_runtime(rt)
        meta = json.loads((A7 / "frame_0000000000.json").read_text())
        jpeg = (A7 / "frame_0000000000.jpg").read_bytes()
        day_ago = time.time() - 86400.0
        replay_publish.publish_frame(rt, 7, jpeg, replay_publish.rewrite_metadata(meta, 7, day_ago, 1.0), now=lambda: day_ago)
        desk = relay.DesktopRelay(rt, tmp / "log", "127.0.0.1", 1)
        self.addCleanup(desk.sync_log.close)
        self.addCleanup(desk.receipts.close)
        link = FakeLink()
        desk.link = link
        desk.forward_once()
        self.assertEqual(link.sent, [])
        self.assertEqual(desk.counters["stale_pointers_skipped"], 1)
        for frame_id in (0, 7):
            replay_publish.publish_frame(rt, frame_id, jpeg, replay_publish.rewrite_metadata(meta, frame_id, time.time(), time.monotonic()))
            desk.forward_once()
        pointers = [json.loads(body)["frame_id"] for header, body in link.sent if header["path"] == relay.FORWARD_POINTER]
        self.assertEqual(pointers, [0, 7])


class ProtocolPieces(unittest.TestCase):
    def test_encode_roundtrip(self):
        try:
            left, right = socket.socketpair()
        except PermissionError:
            self.skipTest("环境拒绝 socketpair")
        with left, right:
            payload = os.urandom(70000)
            message = relay.encode({"kind": "file", "path": "frames/latest.json", "sha256": common.sha256_bytes(payload)}, payload)
            sender = threading.Thread(target=left.sendall, args=(message,), daemon=True)
            sender.start()
            right.settimeout(10)
            header, body = relay.recv_message(right)
            sender.join(timeout=10)
        self.assertEqual(body, payload)
        self.assertEqual(header["size"], len(payload))

    def test_clock_math(self):
        syncs = []
        for k in range(20):
            t1 = 1000.0 + k
            offset, one_way = 0.250 + 1e-6 * k, 0.010 + (0.05 if k % 4 == 0 else 0.0)
            t2 = t1 + one_way + offset
            t3 = t2 + 0.001
            t4 = t3 - offset + 0.010
            syncs.append({"t1": t1, "t2": t2, "t3": t3, "t4": t4, "offset_s": ((t2 - t1) + (t3 - t4)) / 2,
                          "delay_s": (t4 - t1) - (t3 - t2)})
        self.assertAlmostEqual(relay._offset_at(syncs, 1010.2), 0.250 + 1e-5, delta=1e-4)
        self.assertAlmostEqual(relay.drift_ppm([s for s in syncs if s["delay_s"] < 0.03]), 1.0, delta=0.01)

    def test_language_request_never_relayed(self):
        for name in relay.NEVER_RELAYED:
            self.assertFalse(relay.classify_return(name))
            self.assertEqual(relay.classify_forward(name)[0], "rejected")
        self.assertEqual(set(relay.RETURN_FILES), {"tracking_observation.json", "gimbal_command.json", "body_command.json",
                                                    "tracker_state.json", "language_result.json"})

    def test_parse_drops(self):
        self.assertEqual(relay.parse_drops("300:60,120:10"), [(120.0, 10.0), (300.0, 60.0)])
        self.assertEqual(relay.parse_drops(None), [])


@unittest.skipUnless((A7 / "frame_0000000000.jpg").is_file(), "a7 帧不在本机（只读源）")
class ReplayAndEcho(unittest.TestCase):
    def test_replay_rewrites_only_ids_and_clocks_and_echo_binds_frame(self):
        tmp = Path(tempfile.mkdtemp(prefix="eng-jet-replay-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        rt = tmp / "rt"
        receipts = tmp / "r.jsonl"
        writes = []
        original = common.atomic_write_bytes

        def spy(path, payload, roots=None, *, fsync=True):
            writes.append(Path(path).name)
            return original(path, payload, roots, fsync=fsync)

        common.atomic_write_bytes = spy
        try:
            replay_publish.replay(A7, rt, 3, 50.0, receipts, start_index=10)
        finally:
            common.atomic_write_bytes = original
        self.assertEqual(writes[:3], [common.frame_name(0, "jpg"), common.frame_name(0, "json"), "latest.json"])
        self.assertEqual((rt / "frames" / common.frame_name(0, "jpg")).read_bytes(), (A7 / common.frame_name(10, "jpg")).read_bytes())
        source = json.loads((A7 / common.frame_name(10, "json")).read_text())
        out = json.loads((rt / "frames" / common.frame_name(0, "json")).read_text())
        changed = {k for k in source if source[k] != out.get(k)}
        self.assertEqual(changed, {"frame_id", "capture_unix_s", "capture_monotonic_s"})
        self.assertEqual(out["capture_monotonic_clock_id"], source["capture_monotonic_clock_id"])
        echo = relay.EchoResponder(rt, tmp / "log")
        self.addCleanup(echo.receipts.close)
        self.assertTrue(echo.poll_once())
        self.assertFalse(echo.poll_once())
        packet = json.loads((rt / "tracking_observation.json").read_text())
        self.assertEqual(packet["protocol"], "tethered-tracking-observation/v1")
        self.assertEqual(packet["observation"]["frame_id"], 2)
        row = common.read_jsonl(tmp / "log" / "echo-receipts.jsonl")[0]
        self.assertGreaterEqual(row["load_elapsed_s"], 0.0)
        self.assertIsNotNone(row["capture_age_s"])


if __name__ == "__main__":
    unittest.main()
