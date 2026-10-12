"""P1-ENG-LOOP-002 OpsK1K2K3K4：本机操作网页 W1–W5（AC-5 修订 1 / AC-10 修订 3 / AC-11 修订 1 / AC-14 修订 1）。

临时目录替身：桥文件由生产写函数（`language_bridge.tracker_state_payload/write_tracker_state/result_payload/
write_result`）写出，帧由生产 `FixtureFramePublisher` 写出，K 收据由生产 `build_k_receipt` 生成；CLI 用
记录型替身（另有一例用真实 `controller.language_loop` CLI 子进程 + 回执应答线程）。零模型、不写实际 runtime/。
"""

from __future__ import annotations

import http.client
import json
import struct
import sys
import tempfile
import threading
import time
import unittest
import zlib
from pathlib import Path
from typing import Any

from controller import language_bridge as bridge
from controller.language_loop import SESSION_JOURNAL, FixtureFramePublisher, build_k_receipt
from tools.eng_loop2 import operator_web as web

SESSION = "loop2-p1"
HZ = 5.0


def png_bytes(seed: int = 0, size: int = 2) -> bytes:
    raw = b"".join(b"\x00" + bytes([(seed * 7 + y) % 256, 10, 20]) * size for y in range(size))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


class Clock:
    def __init__(self, now: float):
        self.now = now

    def __call__(self) -> float:
        return self.now


class FakeCli:
    """记录 argv；按 `outcomes` 队列回执（缺省 APPLIED）。"""

    def __init__(self, delay_s: float = 0.0):
        self.calls: list[list[str]] = []
        self.outcomes: list[dict[str, Any]] = []
        self.delay_s = delay_s
        self.lock = threading.Lock()

    def __call__(self, argv: list[str]) -> dict[str, Any]:
        with self.lock:
            self.calls.append(list(argv))
            planned = self.outcomes.pop(0) if self.outcomes else None
        if self.delay_s:
            time.sleep(self.delay_s)
        request_id = argv[argv.index("--request-id") + 1]
        action = argv[3]
        if planned is not None and planned.get("raw") is not None:
            return planned["raw"]
        outcome = (planned or {}).get("outcome", "APPLIED")
        receipt = {"request_id": request_id, "action": action, "outcome": outcome, "at_sequence": len(self.calls)}
        return {"exit": 0, "timeout": False, "stdout": json.dumps({"request_id": request_id, "receipt": receipt}), "stderr": ""}


class FakeScheduler:
    def __init__(self) -> None:
        self.step = {"step_id": "P1-1", "kind": "designate", "action": "ask", "instruction": "the suv",
                     "intent": "Vehicle_SUV_color01 (1)", "delay_s": None, "description": "the suv", "attempt": SESSION}
        self.phase = "await_send"
        self.sent: list[Any] = []
        self.skipped: list[Any] = []
        self.decisions: list[Any] = []
        self.stops: list[Any] = []
        self.block: str | None = None
        self.request_id: str | None = None

    def snapshot(self) -> dict[str, Any]:
        current = dict(self.step, phase=self.phase)
        return {"playbook": "P1", "attempt": SESSION, "plan_sha256": "f" * 64, "current": current,
                "decision_step": "P1-1" if self.phase == "await_decision" else None, "steps": []}

    def blocked(self) -> str | None:
        return self.block

    def current_send_step(self, step_id: Any) -> dict[str, Any] | None:
        return dict(self.step) if self.phase == "await_send" and step_id == self.step["step_id"] else None

    def decision_step(self, request_id: Any) -> str | None:
        return "P1-1" if self.phase == "await_decision" and request_id and request_id == self.request_id else None

    def record_send(self, step_id: str, reply: Any) -> None:
        self.sent.append((step_id, reply))
        if reply.get("unknown"):
            self.block = "UNKNOWN"
        else:
            self.phase = "await_result"

    def record_skip(self, step_id: str, at: float) -> None:
        self.skipped.append((step_id, at))
        self.phase = "done"

    def record_decision(self, step_id: str, action: str, reply: Any) -> None:
        self.decisions.append((step_id, action, reply))
        if reply.get("unknown"):
            self.block = "UNKNOWN"

    def record_operator_stop(self, reply: Any) -> None:
        self.stops.append(reply)


class Fixture:
    """临时 runtime + 会话目录；生产写函数写桥文件与帧。"""

    def __init__(self, root: Path, clock: Clock):
        self.root = root
        self.runtime = root / "runtime"
        self.runtime.mkdir()
        self.session_dir = root / "sessions" / SESSION
        (self.session_dir / "previews").mkdir(parents=True)
        self.clock = clock
        self.frames = FixtureFramePublisher(self.runtime, scenario_id="deterministic-loop-untethered", unix=clock)
        receipt = build_k_receipt(hz=HZ, retained_frame_count=1500, p95_s=2.6, host="jetson", backend="http", model_form="c2-merged")
        self.receipt_path = root / "k-receipt.json"
        self.receipt_path.write_text(json.dumps(receipt.payload()), encoding="utf-8")
        self.receipt = web.load_receipt(self.receipt_path)
        self.sequence = 0

    def publish_frames(self, count: int) -> int:
        last = 0
        for _ in range(count):
            last = self.frames.publish(b"\xff\xd8\xff\xe0fakejpeg")
        return last

    def state(self, state: str, *, epoch: int = 1, reason: str | None = None, track_id: str | None = None,
              last_request: dict[str, Any] | None = None) -> None:
        self.sequence += 1
        payload = bridge.tracker_state_payload(session_id=SESSION, state=state, sequence=self.sequence, epoch=epoch,
                                               publishing=False, reason=reason, track_id=track_id, last_request=last_request)
        bridge.write_tracker_state(self.runtime, payload)

    def result(self, *, frame_id: int, query_unix_s: float, epoch: int = 1, n: int = 2, seq: int = 1,
               request_id: str = "loop2-p1-ops-aaaa0001", preview: bytes | None = None, issued: float | None = None) -> dict[str, Any]:
        query_id = f"{SESSION}-q{seq}"
        name = f"{frame_id}-{query_id}.png"
        path = self.session_dir / "previews" / name
        if preview is not None:
            path.write_bytes(preview)
        candidates = [{"index": i, "bbox_xywh_norm": [0.1 * i, 0.1, 0.1, 0.1], "bbox_2d_1000": [1, 2, 3, 4], "clipped": False} for i in range(n)]
        payload = bridge.result_payload(
            query_id=query_id, result_id=f"{SESSION}-res{seq}", request_id=request_id, epoch=epoch, segment_index=None,
            attempt=1, attempt_limit=3, purpose="designate", status="unique" if n == 1 else "ambiguous",
            frame_id=frame_id, frame_sha256="0" * 64, capture_monotonic_s=1.0, capture_unix_s=query_unix_s - 0.1,
            query_unix_s=query_unix_s, candidates=candidates, preview_path=str(path),
        )
        # 呈现时刻按生产写盘路径取信封 `issued_unix_s`；替身用同一假时钟（缺省 = 现在）。
        payload["issued_unix_s"] = self.clock() if issued is None else issued
        bridge.write_result(self.runtime, payload)
        return payload

    def journal(self, **record: Any) -> None:
        with (self.session_dir / SESSION_JOURNAL).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"session_id": SESSION, "at_unix_s": self.clock(), **record}) + "\n")


class WebTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.clock = Clock(1_800_000_000.0)
        self.fx = Fixture(Path(self.tmp.name), self.clock)
        self.cli = FakeCli()
        self.log = web.OpsLog(Path(self.tmp.name) / "ops" / web.OPS_LOG, clock=self.clock)
        builder = web.CliRunner("python3", Path(self.tmp.name), self.fx.runtime)
        self.submitter = web.Submitter(self.cli, builder, self.log)
        self.scheduler = FakeScheduler()
        self.app = web.App(
            monitor_factory=lambda sid, sdir: web.Monitor(self.fx.runtime, sid, sdir, self.fx.receipt, clock=self.clock),
            submitter=self.submitter, log=self.log, scheduler=self.scheduler,
            feedback_path=Path(self.tmp.name) / "ops" / "feedback.jsonl", clock=self.clock,
        )
        self.monitor = self.app.bind_session(SESSION, self.fx.session_dir)

    def log_kinds(self) -> list[str]:
        return [json.loads(l)["kind"] for l in self.log.path.read_text(encoding="utf-8").splitlines()]

    def present(self, *, n: int = 2, preview: bytes | None = None, query_offset: float = 1.0, issued_offset: float = 0.0,
                frames: int = 5) -> dict[str, Any]:
        frame_id = self.fx.publish_frames(frames)
        self.scheduler.phase = "await_decision"
        self.scheduler.request_id = "loop2-p1-ops-aaaa0001"
        payload = self.fx.result(frame_id=frame_id, query_unix_s=self.clock.now - query_offset, n=n,
                                 preview=png_bytes(1) if preview is None else preview, issued=self.clock.now - issued_offset)
        self.fx.state("AWAITING_CONFIRMATION")
        self.monitor.poll()
        return payload

    def decide_view(self) -> dict[str, Any]:
        snap = self.app.state()
        block = snap["session"]["presentation"]
        state = snap["session"]["state"]
        return {"session_id": SESSION, "state": state["state"], "reason": state["reason"], "epoch": state["epoch"],
                "result_id": block["result_id"], "query_id": block["query_id"], "request_id": block["request_id"],
                "frame_id": block["frame_id"], "step_id": snap["plan"]["decision_step"]}

    def display(self) -> dict[str, Any]:
        block = self.app.state()["session"]["presentation"]
        preview = block["preview"]
        return self.app.displayed_preview({"result_id": block["result_id"], "name": preview["name"], "sha256": preview["sha256"]})

    def confirm(self, index: int = 0, **override: Any) -> dict[str, Any]:
        block = self.app.state()["session"]["presentation"]
        seen = {"name": block["preview"]["name"], "sha256": block["preview"]["sha256"]} if block.get("preview") else {}
        body = {"button": "confirm", "view": self.decide_view(), "index": index, "preview_seen": seen}
        body.update(override)
        return self.app.action(body)


class LegalActionTests(unittest.TestCase):
    def test_table_terminal_backend_fatal_and_states(self) -> None:
        self.assertEqual(web.legal_session_actions({"state": "TERMINAL", "reason": "operator_stop"}), set())
        self.assertEqual(web.legal_session_actions({"state": "LOST", "reason": "backend_fatal"}), {"stop"})
        self.assertEqual(web.legal_session_actions({"state": "AWAITING_CONFIRMATION"}) >= {"confirm", "reject", "ask", "respecify", "stop"}, True)
        self.assertIn("release", web.legal_session_actions({"state": "TRACKING"}))
        self.assertNotIn("confirm", web.legal_session_actions({"state": "QUERYING"}))
        self.assertEqual(web.legal_session_actions({"state": "ACQUIRING"}), {"stop"})

    def test_buttons_closed_set_has_no_free_text_verify_or_retry(self) -> None:
        self.assertEqual(web.BUTTONS, ("send", "skip", "confirm", "reject", "stop", "feedback"))
        self.assertEqual(web.CLI_ACTIONS, frozenset({"ask", "respecify", "confirm", "reject", "release", "stop"}))
        for forbidden in ("verify", "confirm-lost", "dismiss", "retry"):
            self.assertNotIn(forbidden, web.BUTTONS)
            self.assertNotIn(f'"{forbidden}"', web.PAGE)

    def test_cli_argv_is_accepted_by_production_parser(self) -> None:
        from controller.language_loop import build_parser

        builder = web.CliRunner("python3", Path("."), Path("runtime"))
        argv = builder.argv("ask", SESSION, "rid-1", instruction="the red car", intent="red_car", delay_s=2.0)
        parsed = build_parser().parse_args(argv[3:])
        self.assertEqual((parsed.command, parsed.instruction, parsed.intent, parsed.delay_s, parsed.request_id),
                         ("ask", "the red car", "red_car", 2.0, "rid-1"))
        argv = builder.argv("confirm", SESSION, "rid-2", token="loop2-p1-res1", index=1)
        parsed = build_parser().parse_args(argv[3:])
        self.assertEqual((parsed.index, parsed.token, parsed.allow_shared_runtime), (1, "loop2-p1-res1", True))
        with self.assertRaises(ValueError):
            builder.argv("verify", SESSION, "rid-3")


class BindingTests(WebTestBase):
    def test_confirm_needs_browser_display_then_sends_bound_token_and_index(self) -> None:
        self.present()
        refused = self.confirm(1)
        self.assertFalse(refused["ok"])
        self.assertIn("尚未显示", refused["message"])
        self.assertEqual(self.cli.calls, [])
        self.assertTrue(self.display()["ok"])
        reply = self.confirm(1)
        self.assertTrue(reply["ok"], reply)
        argv = self.cli.calls[0]
        self.assertEqual(argv[3], "confirm")
        self.assertEqual(argv[argv.index("--token") + 1], f"{SESSION}-res1")
        self.assertEqual(argv[-1], "1")
        self.assertEqual(self.scheduler.decisions[0][1], "confirm")
        self.assertIn("preview_displayed", self.log_kinds())
        self.assertIn("presentation_snapshot", self.log_kinds())

    def test_refused_confirm_still_allows_reject_but_not_a_second_confirm(self) -> None:
        self.present()
        self.display()
        self.cli.outcomes.append({"outcome": "REQUEST_INVALID"})
        reply = self.confirm(0)
        self.assertEqual(reply["receipt"]["outcome"], "REQUEST_INVALID")
        self.assertFalse(self.confirm(1)["ok"])  # 同一结果同一动作只提交一次
        self.assertTrue(self.app.action({"button": "reject", "view": self.decide_view()})["ok"])
        self.assertEqual([c[3] for c in self.cli.calls], ["confirm", "reject"])

    def test_display_report_for_other_image_is_not_recorded(self) -> None:
        self.present()
        block = self.app.state()["session"]["presentation"]
        reply = self.app.displayed_preview({"result_id": block["result_id"], "name": block["preview"]["name"], "sha256": "0" * 64})
        self.assertFalse(reply["ok"])
        self.assertFalse(self.confirm(0)["ok"])

    def test_stale_view_new_epoch_and_wrong_result_refused(self) -> None:
        self.present()
        self.display()
        view = self.decide_view()
        self.fx.state("AWAITING_CONFIRMATION", epoch=2)
        self.monitor.poll()
        reply = self.app.action({"button": "reject", "view": view})
        self.assertFalse(reply["ok"])
        self.assertIn("过期", reply["message"])
        wrong = dict(view, result_id=f"{SESSION}-res9")
        self.assertFalse(self.app.action({"button": "reject", "view": wrong})["ok"])
        self.assertEqual(self.cli.calls, [])

    def test_preview_bytes_changing_between_reads_disables_confirmation_forever(self) -> None:
        payload = self.present()
        self.display()
        Path(payload["result"]["preview_path"]).write_bytes(png_bytes(9))
        self.monitor.poll()
        block = self.app.state()["session"]["presentation"]
        self.assertFalse(block["confirmable"])
        self.assertIn("不一致", block["why_not"])
        self.assertFalse(self.confirm(0)["ok"])
        self.assertEqual(self.cli.calls, [])

    def test_missing_or_corrupt_preview_cannot_be_confirmed(self) -> None:
        self.present(preview=b"not a png")
        block = self.app.state()["session"]["presentation"]
        self.assertFalse(block["confirmable"])
        self.assertIn("PNG", block["why_not"])
        self.assertFalse(self.confirm(0)["ok"])

    def test_index_out_of_range_refused(self) -> None:
        self.present(n=2)
        self.display()
        self.assertIn("候选序号", self.confirm(5)["message"])
        self.assertIn("候选序号", self.confirm(True)["message"])
        self.assertEqual(self.cli.calls, [])

    def test_pending_delta_presentation_is_not_confirmable(self) -> None:
        frame_id = self.fx.publish_frames(3)
        self.fx.result(frame_id=frame_id, query_unix_s=self.clock.now - 1, preview=png_bytes(1))
        self.fx.state("QUERYING")  # Δ 挂起：结果已到、尚未呈现
        self.monitor.poll()
        snap = self.app.state()
        self.assertIsNone(snap["session"]["presentation"])
        self.assertNotIn("confirm", snap["session"]["legal"])

    def test_cross_file_mismatch_result_epoch_differs_from_state(self) -> None:
        frame_id = self.fx.publish_frames(3)
        self.fx.result(frame_id=frame_id, query_unix_s=self.clock.now - 1, preview=png_bytes(1), epoch=3)
        self.fx.state("AWAITING_CONFIRMATION", epoch=4)
        self.monitor.poll()
        block = self.app.state()["session"]["presentation"]
        self.assertFalse(block["confirmable"])
        self.assertIsNone(block["result_id"])


class DeadlineTests(WebTestBase):
    def test_earlier_of_two_deadlines_and_refresh_never_renews(self) -> None:
        # 查询起 30 s 前：查询截止 = q + T_ret + T_conf；呈现截止 = issued + T_conf（较早者生效）。
        self.present(query_offset=1.0, issued_offset=0.0)
        block = self.app.state()["session"]["presentation"]
        t_ret = self.fx.receipt["t_ret_s"]
        self.assertAlmostEqual(block["query_deadline_unix_s"], self.clock.now - 1.0 + t_ret + 10.0)
        self.assertAlmostEqual(block["presented_deadline_unix_s"], self.clock.now + 10.0)
        self.assertAlmostEqual(block["deadline_unix_s"], min(block["query_deadline_unix_s"], block["presented_deadline_unix_s"]))
        self.display()
        deadline = block["deadline_unix_s"]
        for _ in range(3):  # 轮询/刷新/重新开页
            self.clock.now += 3.0
            self.monitor.poll()
            again = self.app.state()["session"]["presentation"]
            self.assertAlmostEqual(again["deadline_unix_s"], deadline)
        self.clock.now = deadline + 0.01
        self.monitor.poll()
        after = self.app.state()["session"]["presentation"]
        self.assertFalse(after["confirmable"])
        self.assertIn("截止", after["why_not"])
        self.assertFalse(self.confirm(0)["ok"])
        # 到期不默认拒绝；本人仍可拒绝（会话原表合法）
        self.assertEqual(self.cli.calls, [])
        self.assertTrue(self.app.action({"button": "reject", "view": self.decide_view()})["ok"])
        self.assertEqual(self.cli.calls[0][3], "reject")

    def test_frame_difference_gate(self) -> None:
        self.present(frames=2)
        limit = self.fx.receipt["k_ret"] + self.fx.receipt["k_conf"]
        self.fx.publish_frames(limit + 1)
        self.monitor.poll()
        block = self.app.state()["session"]["presentation"]
        self.assertGreater(block["frames_delta"], limit)
        self.assertFalse(block["confirmable"])
        self.assertIn("帧差", block["why_not"])

    def test_presentation_time_before_query_time_is_untrusted(self) -> None:
        self.present(query_offset=1.0, issued_offset=5.0)
        block = self.app.state()["session"]["presentation"]
        self.assertFalse(block["confirmable"])
        self.assertIn("回退", block["why_not"])

    def test_stale_data_disables_confirmation(self) -> None:
        self.present()
        self.clock.now += 2.0  # 无新轮询
        block = self.monitor.public(self.clock.now)["presentation"]
        self.assertFalse(block["confirmable"])
        self.assertIn("过期", block["why_not"])


class SubmissionTests(WebTestBase):
    def test_concurrent_clicks_from_two_tabs_send_exactly_once(self) -> None:
        self.cli.delay_s = 0.3
        self.present()
        self.display()
        view = self.decide_view()
        block = self.app.state()["session"]["presentation"]
        body = {"button": "confirm", "view": view, "index": 0,
                "preview_seen": {"name": block["preview"]["name"], "sha256": block["preview"]["sha256"]}}
        replies: list[dict[str, Any]] = []
        threads = [threading.Thread(target=lambda: replies.append(self.app.action(dict(body)))) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(self.cli.calls), 1)
        self.assertEqual(sorted(r["ok"] for r in replies), [False, True])
        # 刷新重放 / 旧视图再次点击
        self.assertFalse(self.app.action(dict(body))["ok"])
        self.assertEqual(len(self.cli.calls), 1)

    def test_unknown_result_blocks_progression_and_late_receipt_only_resolves_original(self) -> None:
        self.cli.outcomes.append({"raw": {"exit": 5, "timeout": False, "stdout": '{"receipt": null}', "stderr": ""}})
        self.fx.publish_frames(2)
        self.fx.state("IDLE")
        self.monitor.poll()
        view = {"session_id": SESSION, "state": "IDLE", "reason": None, "epoch": 1, "step_id": "P1-1", "plan_sha256": "f" * 64}
        reply = self.app.action({"button": "send", "view": view})
        self.assertTrue(reply["unknown"])
        self.assertEqual(self.scheduler.block, "UNKNOWN")
        request_id = reply["request_id"]
        self.assertEqual([u["request_id"] for u in self.submitter.unknown_entries()], [request_id])
        # 流程停止：发送/选择被拒，只剩停止会话
        self.assertIn("停止推进", self.app.action({"button": "send", "view": view})["message"])
        self.fx.journal(kind="receipt", receipt={"request_id": request_id, "action": "ask", "outcome": "APPLIED", "at_sequence": 3})
        self.monitor.poll()
        snap = self.app.state()
        self.assertTrue(snap["unknown"][0]["late_receipt"])
        self.assertEqual(snap["blocked"], "UNKNOWN")  # 迟到回执不恢复流程
        self.assertEqual(len(self.cli.calls), 1)  # 不换 id 重发
        self.assertIn("late_receipt", self.log_kinds())

    def test_writer_busy_is_recorded_unknown_and_blocks(self) -> None:
        self.cli.outcomes.append({"raw": {"exit": 4, "timeout": False, "stdout": "", "stderr": "WRITER_BUSY"}})
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.monitor.poll()
        view = {"session_id": SESSION, "state": "IDLE", "reason": None, "epoch": 1, "step_id": "P1-1", "plan_sha256": "f" * 64}
        reply = self.app.action({"button": "send", "view": view})
        self.assertTrue(reply["unknown"])
        self.assertEqual(self.scheduler.block, "UNKNOWN")
        record = [json.loads(l) for l in self.log.path.read_text(encoding="utf-8").splitlines() if '"submit_result"' in l][0]
        self.assertEqual((record["exit_code"], record["stderr"]), (4, "WRITER_BUSY"))

    def test_stop_is_sent_at_most_once_between_runner_and_button(self) -> None:
        self.fx.publish_frames(1)
        self.fx.state("TRACKING", track_id="t1")
        self.monitor.poll()
        key = json.dumps({"button": "stop", "session_id": SESSION}, sort_keys=True)
        runner = self.submitter.submit(source="runner", action="stop", session_id=SESSION, binding={"step_id": "P1-5"}, binding_key=key)
        self.assertTrue(runner["ok"])
        reply = self.app.action({"button": "stop", "view": {"session_id": SESSION, "state": "TRACKING", "epoch": 1}})
        self.assertFalse(reply["ok"])
        self.assertEqual(len(self.cli.calls), 1)

    def test_send_and_skip_bind_the_plan_step_once(self) -> None:
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.monitor.poll()
        view = {"session_id": SESSION, "state": "IDLE", "reason": None, "epoch": 1, "step_id": "P1-1", "plan_sha256": "f" * 64}
        self.assertFalse(self.app.action({"button": "send", "view": dict(view, plan_sha256="e" * 64)})["ok"])
        self.assertFalse(self.app.action({"button": "send", "view": dict(view, step_id="P1-2")})["ok"])
        reply = self.app.action({"button": "send", "view": view})
        self.assertTrue(reply["ok"])
        argv = self.cli.calls[0]
        self.assertEqual((argv[3], argv[-1], argv[argv.index("--intent") + 1]), ("ask", "the suv", "Vehicle_SUV_color01 (1)"))
        self.scheduler.phase = "await_send"  # 即使页面仍显示同一步骤，也不能再发/跳过
        self.assertFalse(self.app.action({"button": "skip", "view": view})["ok"])
        self.assertEqual(len(self.cli.calls), 1)

    def test_skip_sends_nothing_and_records_reason(self) -> None:
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.monitor.poll()
        view = {"session_id": SESSION, "state": "IDLE", "reason": None, "epoch": 1, "step_id": "P1-1", "plan_sha256": "f" * 64}
        reply = self.app.action({"button": "skip", "view": view})
        self.assertTrue(reply["ok"])
        self.assertEqual(self.cli.calls, [])
        self.assertEqual(self.scheduler.skipped[0][0], "P1-1")
        self.assertIn("skip", self.log_kinds())

    def test_terminal_and_backend_fatal_states(self) -> None:
        self.fx.publish_frames(1)
        self.fx.state("TERMINAL", reason="duration_reached")
        self.monitor.poll()
        view = {"session_id": SESSION, "state": "TERMINAL", "reason": "duration_reached", "epoch": 1, "step_id": "P1-1", "plan_sha256": "f" * 64}
        self.assertFalse(self.app.action({"button": "send", "view": view})["ok"])
        self.assertFalse(self.app.action({"button": "stop", "view": view})["ok"])
        self.fx.state("LOST", reason="backend_fatal")
        self.monitor.poll()
        view = dict(view, state="LOST", reason="backend_fatal")
        self.assertIn("不合法", self.app.action({"button": "send", "view": view})["message"])
        self.assertTrue(self.app.action({"button": "stop", "view": view})["ok"])
        self.assertEqual([c[3] for c in self.cli.calls], ["stop"])

    def test_sealed_session_refuses_every_business_action_but_allows_one_stop(self) -> None:
        """C6-1：封住后（STOP/故障/中断）网页业务一律拒绝，即使状态仍合法、视图仍新鲜；只放行至多一次 stop。"""
        self.present()
        self.display()
        decide = self.decide_view()
        self.submitter.seal(SESSION, "STOP1 test")
        self.assertIn("封住", self.confirm()["message"])
        self.assertIn("封住", self.app.action({"button": "reject", "view": decide})["message"])
        send_view = {"session_id": SESSION, "state": "AWAITING_CONFIRMATION", "reason": None, "epoch": 1, "step_id": "P1-1",
                     "plan_sha256": "f" * 64}
        self.assertIn("封住", self.app.action({"button": "send", "view": send_view})["message"])
        self.assertIn("封住", self.app.action({"button": "skip", "view": send_view})["message"])
        self.assertFalse(self.submitter.claim("any-skip-binding", SESSION))
        self.assertEqual((self.cli.calls, self.scheduler.decisions, self.scheduler.skipped), ([], [], []))
        stop_view = {"session_id": SESSION, "state": "AWAITING_CONFIRMATION", "epoch": 1}
        self.assertTrue(self.app.action({"button": "stop", "view": stop_view})["ok"])
        self.assertFalse(self.app.action({"button": "stop", "view": stop_view})["ok"])
        self.assertEqual([c[3] for c in self.cli.calls], ["stop"])
        self.assertIn("sealed", self.log_kinds())


class FeedbackTests(WebTestBase):
    def test_feedback_only_after_summary_once_per_attempt(self) -> None:
        body = {"button": "feedback", "view": {"attempt": SESSION}, "label": "PASS", "text": "看起来跟上了"}
        self.assertIn("尚未就绪", self.app.action(body)["message"])
        self.app.set_summary({"attempts": [{"session_id": SESSION}], "text": "摘要", "summary_sha256": "a" * 64})
        self.assertFalse(self.app.action(dict(body, label="MAYBE"))["ok"])
        self.assertFalse(self.app.action(dict(body, view={"attempt": "other"}))["ok"])
        self.assertTrue(self.app.action(body)["ok"])
        self.assertFalse(self.app.action(dict(body, label="FAIL"))["ok"])
        record = json.loads(self.app.feedback_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual((record["label"], record["button_text"], record["text"], record["attempt"]), ("PASS", "通过", "看起来跟上了", SESSION))
        self.assertEqual(self.cli.calls, [])


class HttpTests(WebTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.server = web.build_server(self.app, 0)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, method: str, path: str, *, body: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        data = json.dumps(body).encode() if body is not None else None
        merged = {"Host": f"127.0.0.1:{self.port}", "Content-Type": "application/json"}
        merged.update(headers or {})
        connection.request(method, path, body=data, headers=merged)
        response = connection.getresponse()
        return response.status, response.read()

    def test_listens_on_loopback_only(self) -> None:
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_page_and_state_and_no_external_resources(self) -> None:
        status, page = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(self.app.nonce.encode(), page)
        for external in (b"http://", b"https://", b"//cdn", b"<link"):
            self.assertNotIn(external, page.replace(b"http://127.0.0.1", b""))
        status, _ = self.request("GET", "/api/state")
        self.assertEqual(status, 200)

    def test_post_requires_nonce_local_host_and_origin(self) -> None:
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.monitor.poll()
        body = {"button": "stop", "view": {"session_id": SESSION, "state": "IDLE", "epoch": 1}}
        self.assertEqual(self.request("POST", "/api/action", body=body)[0], 403)  # 缺 nonce
        good = {"X-Ops-Nonce": self.app.nonce}
        self.assertEqual(self.request("POST", "/api/action", body=body, headers=dict(good, Origin="http://evil.example"))[0], 403)
        self.assertEqual(self.request("POST", "/api/action", body=body, headers=dict(good, Host="evil.example"))[0], 403)
        self.assertEqual(self.request("GET", "/api/state", headers={"Host": "evil.example"})[0], 403)
        self.assertEqual(self.cli.calls, [])
        status, data = self.request("POST", "/api/action", body=body, headers=dict(good, Origin=f"http://127.0.0.1:{self.port}"))
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(data)["ok"])
        reasons = [json.loads(l).get("reason") for l in self.log.path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(reasons.count("forbidden_request"), 3)

    def test_preview_and_frame_paths_are_bound(self) -> None:
        self.present()
        block = self.app.state()["session"]["presentation"]
        name, sha = block["preview"]["name"], block["preview"]["sha256"]
        self.assertEqual(self.request("GET", f"/preview/{name}?sha={sha}")[0], 200)
        self.assertEqual(self.request("GET", f"/preview/{name}?sha={'0' * 64}")[0], 404)
        self.assertEqual(self.request("GET", f"/preview/..%2F..%2Fk-receipt.json?sha={sha}")[0], 404)
        self.assertEqual(self.request("GET", "/preview/../../k-receipt.json")[0], 404)
        status, data = self.request("GET", "/frame/latest.jpg")
        self.assertEqual(status, 200)
        self.assertTrue(data.startswith(b"\xff\xd8\xff"))
        self.assertEqual(self.request("GET", "/frame/../k-receipt.json")[0], 404)


class FidelityPageTests(unittest.TestCase):
    """AC-11 修订 1：离线样帧保真核对页只读、只服务给定 PNG（sha 绑定）、至少 2 张。"""

    def test_fidelity_page_serves_bound_samples_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i in range(2):
                path = Path(tmp) / f"{10 + i}-loop2-p1-q{i + 1}.png"
                path.write_bytes(png_bytes(i, size=4))
                paths.append(path)
            with self.assertRaises(ValueError):
                web.load_fidelity_samples(paths[:1])
            bad = Path(tmp) / "1-x-q1.png"
            bad.write_bytes(b"nope")
            with self.assertRaises(ValueError):
                web.load_fidelity_samples([paths[0], bad])
            server = web.build_fidelity_server(paths, 0)
            port = server.server_address[1]
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                def get(path: str, host: str | None = None) -> tuple[int, bytes]:
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                    connection.request("GET", path, headers={"Host": host or f"127.0.0.1:{port}"})
                    response = connection.getresponse()
                    return response.status, response.read()

                status, page = get("/")
                self.assertEqual(status, 200)
                sha = web.sha256_bytes(paths[1].read_bytes())
                self.assertIn(sha.encode(), page)
                self.assertEqual(get(f"/sample/1?sha={sha}"), (200, paths[1].read_bytes()))
                self.assertEqual(get(f"/sample/0?sha={sha}")[0], 404)
                self.assertEqual(get("/sample/5?sha=" + sha)[0], 404)
                self.assertEqual(get("/", host="evil.example")[0], 403)
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                connection.request("POST", "/", body=b"{}", headers={"Host": f"127.0.0.1:{port}"})
                self.assertEqual(connection.getresponse().status, 501)
            finally:
                server.shutdown()
                server.server_close()


class RealCliTests(unittest.TestCase):
    """真实 `controller.language_loop` CLI 子进程 + 回执应答线程（替身会话只写生产格式回执）。"""

    def test_cli_runner_round_trip_through_production_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            runtime.mkdir()
            payload = bridge.tracker_state_payload(session_id=SESSION, state="IDLE", sequence=1, epoch=1, publishing=False)
            bridge.write_tracker_state(runtime, payload)
            done = threading.Event()

            def responder() -> None:
                deadline = time.time() + 10
                while time.time() < deadline and not done.is_set():
                    envelope = bridge.read_request(runtime)
                    if envelope is not None and envelope.request_id:
                        receipt = {"request_id": envelope.request_id, "action": envelope.action, "outcome": "APPLIED", "at_sequence": 2}
                        bridge.write_tracker_state(runtime, bridge.tracker_state_payload(
                            session_id=SESSION, state="QUERYING", sequence=2, epoch=1, publishing=False, last_request=receipt))
                        return
                    time.sleep(0.02)

            thread = threading.Thread(target=responder)
            thread.start()
            repo = Path(__file__).resolve().parents[1]
            runner = web.CliRunner(sys.executable, repo, runtime, timeout_s=20)
            outcome = runner(runner.argv("ask", SESSION, f"{SESSION}-ops-real0001", instruction="the red car", intent="red_car", delay_s=0.0))
            done.set()
            thread.join()
            receipt, meaning = web.interpret(outcome)
            self.assertEqual(outcome["exit"], 0, outcome)
            self.assertEqual(receipt["outcome"], "APPLIED")
            self.assertIn("仅表示受理", meaning)


if __name__ == "__main__":
    unittest.main()
