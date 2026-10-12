#!/usr/bin/env python3
"""P1-ENG-CAPTURE-001 AC-14（K1）：本机点击页、`InProcessSend` 退出码语义、`operator_web.py` 两处 diff 与 R1-5 回归。"""

from __future__ import annotations

import http.client
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS = Path(__file__).resolve().parent
for path in (PROJECT_ROOT, TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from controller import language_bridge as bridge  # noqa: E402
from controller.language_bridge import WriterBusy  # noqa: E402
from controller.language_loop import FixtureFramePublisher  # noqa: E402
from tools.eng_capture import click_web  # noqa: E402
from tools.eng_capture.common import accepted_base_commit  # noqa: E402
from tools.eng_loop2.operator_web import CliRunner, OpsLog, Submitter  # noqa: E402

SHA = "a" * 64


class Recorder:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = []

    def __call__(self, argv):
        self.calls.append(list(argv))
        return dict(self.outcome)


class ExplodingLog(OpsLog):
    """记录器自身在指定 kind 上抛异常（R1-5：日志失效时内存 seal 仍须完成）。"""

    def __init__(self, path, explode):
        super().__init__(path)
        self.explode = set(explode)

    def write(self, kind, **fields):
        if kind in self.explode:
            raise OSError(f"log write failed: {kind}")
        return super().write(kind, **fields)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        self.publisher = FixtureFramePublisher(self.runtime)

    def tearDown(self):
        self._tmp.cleanup()


class InProcessSendTests(Base):
    def argv(self, action="click", **extra):
        builder = click_web.ClickArgv(sys.executable, PROJECT_ROOT, self.runtime)
        fields = {"x_px": 1.0, "y_px": 2.0, "frame_id": 3, "image_sha256": SHA} if action == "click" else {}
        fields.update(extra)
        return builder.argv(action, "c1", "r1", **fields)

    def test_exit_zero_with_receipt(self):
        sent = []

        def send(runtime, **kwargs):
            sent.append(kwargs)
            return {"request_id": kwargs["request_id"], "receipt": {"outcome": "APPLIED"}}

        outcome = click_web.InProcessSend(send=send)(self.argv(page_latest_frame_id=3, page_click_unix_s=12.5))
        self.assertEqual(outcome["exit"], 0)
        self.assertEqual(json.loads(outcome["stdout"])["receipt"]["outcome"], "APPLIED")
        self.assertEqual(sent[0]["click"], {"x_px": 1.0, "y_px": 2.0, "frame_id": 3, "image_sha256": SHA,
                                            "page": {"latest_frame_id": 3, "click_received_unix_s": 12.5}})
        self.assertEqual(sent[0]["action"], "click")

    def test_exit_two_on_refusal_without_writing(self):
        called = []
        send = lambda runtime, **kwargs: called.append(kwargs) or {}
        self.assertEqual(click_web.InProcessSend(send=send)(self.argv(image_sha256="not-a-sha"))["exit"], 2)
        self.assertEqual(click_web.InProcessSend(send=send)(["python", "-m", "controller.language_loop", "click"])["exit"], 2)
        shared = click_web.ClickArgv(sys.executable, PROJECT_ROOT, PROJECT_ROOT / "runtime").argv(
            "stop", "c1", "r2")
        shared.remove("--allow-shared-runtime")
        self.assertEqual(click_web.InProcessSend(send=send)(shared)["exit"], 2)
        self.assertEqual(called, [])

    def test_exit_four_writer_busy_and_five_without_receipt(self):
        def busy(runtime, **kwargs):
            raise WriterBusy("held")

        self.assertEqual(click_web.InProcessSend(send=busy)(self.argv())["exit"], 4)
        unknown = click_web.InProcessSend(send=lambda runtime, **kwargs: {"request_id": "r1", "receipt": None})(self.argv())
        self.assertEqual(unknown["exit"], 5)

    def test_click_argv_closed_set(self):
        builder = click_web.ClickArgv(sys.executable, PROJECT_ROOT, self.runtime)
        with self.assertRaises(ValueError):
            builder.argv("ask", "c1", "r1", instruction="the bus")
        argv = builder.argv("click", "c1", "r1", x_px=1.5, y_px=2.0, frame_id=7, image_sha256=SHA)
        self.assertEqual(argv[2:5], ["controller.language_loop", "click", "--session-id"])
        self.assertIn("--image-sha256", argv)


class SubmitterDiffTests(Base):
    def test_existing_action_argv_byte_identical(self):
        recorder = Recorder({"exit": 0, "timeout": False, "stdout": json.dumps({"receipt": {"outcome": "APPLIED"}}), "stderr": ""})
        builder = CliRunner(sys.executable, PROJECT_ROOT, self.runtime)
        submitter = Submitter(recorder, builder, OpsLog(self.root / "ops.jsonl"))
        reply = submitter.submit(source="test", action="confirm", session_id="s1", binding={"k": 1}, binding_key="b1",
                                 token="tok", index=2)
        expected = builder.argv("confirm", "s1", reply["request_id"], token="tok", index=2)
        self.assertEqual(recorder.calls[0], expected)

    def test_operator_web_diff_is_exactly_two_places(self):
        base = accepted_base_commit()
        if base is None:
            self.skipTest("git history unavailable")
        diff = subprocess.run(["git", "diff", "-U0", base, "--", "tools/eng_loop2/operator_web.py"], cwd=PROJECT_ROOT,
                              capture_output=True, text=True, check=True).stdout
        added = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
        removed = [line[1:] for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
        hunks = re.findall(r"^@@ .* @@(.*)$", diff, flags=re.M)
        self.assertTrue(all("def submit" in h or "class Submitter" in h or h.strip() == "" for h in hunks), hunks)
        self.assertTrue(any("extra_argv" in line for line in added))
        self.assertTrue(any("record_reply_failed" in line for line in added))
        for line in removed:  # 被替换的只有原 argv 调用与原 on_reply 失败分支
            self.assertTrue(
                any(token in line for token in ("argv = self.argv_builder.argv(", "action, session_id, request_id,", "instruction=instruction",
                                                ")", "on_reply: Callable", "self.log.write(\"record_reply_failed\"")),
                line,
            )

    def test_click_on_reply_failure_seals(self):
        """R1-5 on_reply 子路径：on_reply 抛异常 → 内存 seal + unknown[request_id]（保留已发送事实），回复带 sealed/unknown。"""
        recorder = Recorder({"exit": 0, "timeout": False, "stdout": json.dumps({"receipt": {"outcome": "APPLIED"}}), "stderr": ""})
        log = OpsLog(self.root / "ops.jsonl")
        submitter = Submitter(recorder, click_web.ClickArgv(sys.executable, PROJECT_ROOT, self.runtime), log)

        def boom(_reply):
            raise RuntimeError("plan record failed")

        reply = submitter.submit(source="click_web", action="click", session_id="c1", binding={"x": 1}, binding_key="k1",
                                 on_reply=boom, extra_argv={"x_px": 1.0, "y_px": 2.0, "frame_id": 3, "image_sha256": SHA})
        self.assertTrue(reply["sealed"] and reply["unknown"])
        self.assertEqual(submitter.sealed_reason("c1"), "record_reply_failed")
        unknown = submitter.unknown_entries()
        self.assertEqual((unknown[0]["request_id"], unknown[0]["sent"]), (reply["request_id"], True))
        refused = submitter.submit(source="click_web", action="click", session_id="c1", binding={"x": 2}, binding_key="k2",
                                   extra_argv={"x_px": 1.0, "y_px": 2.0, "frame_id": 3, "image_sha256": SHA})
        self.assertTrue(refused.get("sealed"))
        kinds = [json.loads(line)["kind"] for line in (self.root / "ops.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertIn("record_reply_failed", kinds)

    def test_on_reply_and_log_failure_still_seals(self):
        recorder = Recorder({"exit": 0, "timeout": False, "stdout": json.dumps({"receipt": {"outcome": "APPLIED"}}), "stderr": ""})
        log = ExplodingLog(self.root / "ops.jsonl", {"record_reply_failed", "sealed"})
        submitter = Submitter(recorder, click_web.ClickArgv(sys.executable, PROJECT_ROOT, self.runtime), log)

        def boom(_reply):
            raise RuntimeError("plan record failed")

        reply = submitter.submit(source="click_web", action="click", session_id="c1", binding={"x": 1}, binding_key="k1",
                                 on_reply=boom, extra_argv={"x_px": 1.0, "y_px": 2.0, "frame_id": 3, "image_sha256": SHA})
        self.assertTrue(reply["sealed"] and reply["unknown"])
        self.assertEqual(submitter.sealed_reason("c1"), "record_reply_failed")
        self.assertEqual(submitter.unknown_entries()[0]["request_id"], reply["request_id"])


class ServerTests(Base):
    def start(self, app):
        server = click_web.build_server(app, port=0)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        return server

    def request(self, server, method, path, body=None, headers=None):
        port = server.server_address[1]
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        data = None if body is None else json.dumps(body).encode()
        connection.request(method, path, body=data, headers=dict(headers or {}))
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()

    def live_app(self, outcome=None):
        recorder = Recorder(outcome or {"exit": 0, "timeout": False, "stdout": json.dumps({"receipt": {"outcome": "APPLIED"}}), "stderr": ""})
        log = OpsLog(self.root / "click.jsonl")
        submitter = Submitter(recorder, click_web.ClickArgv(sys.executable, PROJECT_ROOT, self.runtime), log)
        clock = iter(range(100, 1000)).__next__
        return click_web.ClickApp(self.runtime, "c1", submitter, log, clock=lambda: float(clock())), recorder

    def test_listens_on_loopback_and_checks_host_nonce_origin(self):
        app, recorder = self.live_app()
        server = self.start(app)
        self.assertEqual(server.server_address[0], "127.0.0.1")
        port = server.server_address[1]
        host = {"Host": f"127.0.0.1:{port}"}
        body = {"frame_id": 0, "image_sha256": SHA, "x_px": 1.0, "y_px": 1.0}
        self.assertEqual(self.request(server, "GET", "/", headers={"Host": "evil.example"})[0], 403)
        self.assertEqual(self.request(server, "POST", "/api/click", body, {**host, "Content-Type": "application/json"})[0], 403)
        self.assertEqual(self.request(server, "POST", "/api/click", body, {**host, "X-Click-Nonce": app.nonce, "Origin": "http://evil.example"})[0], 403)
        self.assertEqual(recorder.calls, [])
        status, _headers, page = self.request(server, "GET", "/", headers=host)
        self.assertEqual(status, 200)
        self.assertIn(app.nonce.encode(), page)
        self.assertNotIn(b"instruction", page.lower())

    def test_frame_and_click_record_e2e_start_and_submit(self):
        frame_id = self.publisher.publish(b"jpeg-bytes-0")
        app, recorder = self.live_app()
        server = self.start(app)
        port = server.server_address[1]
        status, headers, data = self.request(server, "GET", "/frame", headers={"Host": f"127.0.0.1:{port}"})
        self.assertEqual((status, headers["X-Frame-Id"], data), (200, str(frame_id), b"jpeg-bytes-0"))
        self.publisher.publish(b"jpeg-bytes-1")  # 页面仍显示 0，latest 已到 1
        body = {"frame_id": frame_id, "image_sha256": click_web.sha256_bytes(data), "x_px": 10.5, "y_px": 20.25,
                "display": {"client_w": 960, "natural_w": 640}}
        status, _h, reply = self.request(server, "POST", "/api/click", body,
                                         {"Host": f"127.0.0.1:{port}", "X-Click-Nonce": app.nonce, "Origin": f"http://127.0.0.1:{port}"})
        reply = json.loads(reply)
        self.assertEqual((status, reply["ok"], reply["latest_frame_id_at_click"]), (200, True, 1))
        argv = recorder.calls[0]
        self.assertEqual(argv[argv.index("--frame-id") + 1], str(frame_id))
        self.assertEqual(argv[argv.index("--page-latest-frame-id") + 1], "1")
        log = [json.loads(line) for line in (self.root / "click.jsonl").read_text(encoding="utf-8").splitlines()]
        received = [r for r in log if r["kind"] == "click_received"][0]
        self.assertEqual((received["latest_frame_id_at_click"], received["frame_id"]), (1, frame_id))

    def test_unknown_result_seals_and_stop_once(self):
        app, recorder = self.live_app({"exit": 5, "timeout": False, "stdout": "", "stderr": ""})
        self.publisher.publish(b"x")
        reply = app.click({"frame_id": 0, "image_sha256": SHA, "x_px": 1.0, "y_px": 1.0})
        self.assertTrue(reply["unknown"])
        self.assertEqual(app.submitter.sealed_reason("c1"), "unknown_result")
        self.assertTrue(app.click({"frame_id": 0, "image_sha256": SHA, "x_px": 2.0, "y_px": 1.0}).get("sealed"))
        app.stop({})
        self.assertTrue(app.stop({})["refused"])
        self.assertEqual([c[3] for c in recorder.calls], ["click", "stop"])

    def test_fidelity_mode_marks_clicked_pixel_without_submitting(self):
        frames = self.root / "archive"
        frames.mkdir()
        try:
            from io import BytesIO  # noqa: PLC0415

            from PIL import Image  # noqa: PLC0415
        except ImportError:
            self.skipTest("Pillow unavailable")
        buffer = BytesIO()
        Image.new("RGB", (640, 480), (20, 20, 20)).save(buffer, format="JPEG")
        (frames / "frame_0000000005.jpg").write_bytes(buffer.getvalue())
        app = click_web.FidelityApp(frames, [5], self.root / "out", OpsLog(self.root / "out" / "log.jsonl"))
        self.assertFalse(app.click({"frame_id": 5, "image_sha256": SHA, "x_px": 1.0, "y_px": 1.0})["ok"])
        sample = app.click({"frame_id": 5, "image_sha256": click_web.sha256_bytes(buffer.getvalue()), "x_px": 320.0, "y_px": 100.0})["sample"]
        with Image.open(sample["png"]) as image:
            self.assertEqual(image.size, (640, 480))
            self.assertEqual(image.convert("RGB").getpixel((320 + 9, 100))[0], 255)  # 圆周落在所点像素周围


class EndToEndTests(Base):
    def test_click_page_binds_capture_session_in_process(self):
        from test_capture_session import CaptureHarness, steady  # noqa: PLC0415

        harness = CaptureHarness(self, steady())
        harness.publish(3)
        log = OpsLog(self.root / "click.jsonl")
        submitter = Submitter(click_web.InProcessSend(wait_s=5.0), click_web.ClickArgv(sys.executable, PROJECT_ROOT, harness.runtime), log)
        app = click_web.ClickApp(harness.runtime, "c1", submitter, log)
        result = {}
        data = (harness.runtime / "frames" / "frame_0000000002.jpg").read_bytes()
        thread = threading.Thread(target=lambda: result.update(app.click(
            {"frame_id": 2, "image_sha256": click_web.sha256_bytes(data), "x_px": 300.0, "y_px": 240.0})))
        thread.start()
        deadline = time.time() + 5.0
        while thread.is_alive() and time.time() < deadline:
            harness.tick(1)
            time.sleep(0.02)
        thread.join(1.0)
        self.assertTrue(result.get("ok"), result)
        self.assertEqual((harness.session.state, harness.session.target_manager.track_key), ("TRACKING", 1))
        received = harness.journal("click_received")[-1]
        self.assertEqual(received["page"]["latest_frame_id"], 2)


if __name__ == "__main__":
    unittest.main()
