#!/usr/bin/env python3
"""P1-ENG-ACQ-001 Play D1 local operator page (CLARIFY「Play D1 本地操作页窄范围代码批次」, AC-22…24).

The page lives in ``docs/evidence/P1-ENG-ACQ-001-operator-web.py`` and is loaded by path. Everything runs
on temporary directories: the K receipt and its §2.7 report come from the real
``tools.eng_acq.candidates_preflight`` (adapter-only, no model, no image, no ID), journal lines from the
session's own ``LanguageSession._journal``, bridge files from ``controller.language_bridge``. The CLI is a
stub; no session, Unity, detector, weights or ``runtime/`` of the repository is touched.

``ACQ_OPERATOR_WEB_PATH`` may point at another page file (used once to record the pre-change red run
against the LOOP-001 page, see docs/evidence/P1-ENG-ACQ-001-K1K3-operator-redgreen.log).
"""
from __future__ import annotations

import contextlib
import hashlib
import http.client
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest import mock
import zlib

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from controller import language_bridge as bridge  # noqa: E402
from controller import language_loop as loop  # noqa: E402
from tools.eng_acq import candidates_preflight as preflight  # noqa: E402

PAGE_PATH = Path(os.environ.get("ACQ_OPERATOR_WEB_PATH", REPO / "docs/evidence/P1-ENG-ACQ-001-operator-web.py"))
SHEET = REPO / "docs/evidence/P1-ENG-ACQ-001-play-d1.md"
LOOP_RECEIPT = REPO / "docs/evidence/P1-ENG-LOOP-001-k-receipt.json"
SID = "acq-d1-2"
T0 = 1_800_000_000.0
CANDIDATES_MODEL = {"backend": "candidates", "model_form": "detector-tracks"}


def load_page():
    spec = importlib.util.spec_from_file_location("acq_operator_web_under_test", PAGE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


web = load_page()


class Clock:
    def __init__(self, now: float):
        self.now = now

    def __call__(self) -> float:
        return self.now


@contextlib.contextmanager
def production_clock(clock: Clock):
    """Run the real bridge writers with ``controller.protocol``'s clock pinned to ``clock``."""
    from controller import protocol
    original = protocol.time
    protocol.time = types.SimpleNamespace(time=clock, time_ns=lambda: int(clock() * 1e9))
    try:
        yield
    finally:
        protocol.time = original


def tiny_png(color: bytes = b"\xff\x00\x00") -> bytes:
    """A real 2x2 RGB PNG that any browser decodes."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    rows = b"".join(b"\x00" + color * 2 for _ in range(2))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def cand(index: int, box=(0.4, 0.4, 0.1, 0.1)) -> dict:
    x, y, w, h = box
    return {"index": index, "bbox_xywh_norm": list(box),
            "bbox_2d_1000": [int(x * 1000), int(y * 1000), int((x + w) * 1000), int((y + h) * 1000)],
            "clipped": False}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Env:
    """A temporary Play D1 layout written by production writers."""

    def __init__(self, root: Path, clock: Clock, *, sid: str = SID, retained: int = 1500,
                 receipt: bool = True, report_clock=None):
        self.root, self.clock, self.sid = Path(root), clock, sid
        self.runtime = self.root / "runtime"
        (self.runtime / "frames").mkdir(parents=True)
        self.play_root = self.root / "play-d1"
        self.session_dir = self.play_root / "sessions" / sid
        self.previews = self.session_dir / "previews"
        self.archive = self.play_root / sid / "unity-runtime"
        self.opdir = self.play_root / sid / "operator"
        self.receipt_dir = self.play_root / "k-receipt"
        self.receipt_path = self.receipt_dir / preflight.RECEIPT_NAME
        self.report_path = self.receipt_dir / preflight.REPORT_NAME
        self.set_retained(retained)
        if receipt:
            self.make_receipt(report_clock)
        self.sequence = 0
        self.writer = types.SimpleNamespace(
            results_path=self.session_dir / loop.RESULTS_FILE,
            journal_path=self.session_dir / loop.SESSION_JOURNAL, session_id=sid,
            state="IDLE", epoch=1, sequence=0, _unix=clock, _monotonic=time.monotonic)

    def set_retained(self, retained: int) -> None:
        document = json.loads((REPO / "config" / "scenario.default.json").read_text(encoding="utf-8"))
        document["sensor"]["retained_frame_count"] = retained
        (self.runtime / "scenario_config.json").write_text(json.dumps(document), encoding="utf-8")

    def make_receipt(self, report_clock=None) -> None:
        """§2.7 through the real preflight (adapter-only); ``report_clock`` fakes its timing clock."""
        if report_clock is None:
            with contextlib.redirect_stdout(io.StringIO()):
                code = preflight.run(self.runtime, self.receipt_dir, loop.CANDIDATES_MIN_SAMPLES)
            assert code == 0, code
            return
        report = preflight.build_report(self.runtime, loop.CANDIDATES_MIN_SAMPLES, clock=report_clock)
        self.receipt_dir.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        receipt = preflight.build_receipt(report, self.report_path.resolve())
        self.receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    def receipt_document(self) -> dict:
        return json.loads(self.receipt_path.read_text(encoding="utf-8"))

    def journal(self, kind: str, **fields) -> None:
        self.session_dir.mkdir(parents=True, exist_ok=True)
        loop.LanguageSession._journal(self.writer, kind, **fields)

    def start_session(self, payload: dict | None = None) -> None:
        """``LanguageSession.start``'s journal line with the receipt it was started with."""
        self.previews.mkdir(parents=True, exist_ok=True)
        if payload is None:
            payload = loop.KReceipt.from_document(self.receipt_document()).payload()
        self.journal("session_started", k_receipt=payload, scenario=loop.read_scenario(self.runtime),
                     diagnostic=False, body_planner=None)

    def lock(self, pid: int, sid: str | None = None) -> None:
        (self.runtime / bridge.SESSION_LOCK_FILE).write_text(json.dumps(
            {"pid": pid, "session_id": sid or self.sid, "created_unix_s": T0}), encoding="utf-8")

    def receipt(self, request_id: str, action: str, outcome: str = "APPLIED", detail=None) -> None:
        self.sequence += 1
        self.writer.sequence = self.sequence
        self.journal("receipt", receipt={"request_id": request_id, "action": action, "outcome": outcome,
                                         "at_sequence": self.sequence}, detail=detail)

    def terminal(self) -> None:
        self.writer.state = "TERMINAL"
        self.journal("state", state="TERMINAL", reason="operator_stop")

    def frame(self, frame_id: int) -> None:
        latest = {"frame_id": frame_id, "image_file": f"frame_{frame_id:010d}.jpg",
                  "metadata_file": f"frame_{frame_id:010d}.json"}
        (self.runtime / "frames" / f"frame_{frame_id:010d}.json").write_text(
            json.dumps({"frame_id": frame_id, "simulation_time_s": frame_id / 5.0}), encoding="utf-8")
        (self.runtime / "frames" / "latest.json").write_text(json.dumps(latest), encoding="utf-8")

    def state(self, name: str, **fields) -> None:
        self.sequence += 1
        fields.setdefault("epoch", 2)
        with production_clock(self.clock):
            bridge.write_tracker_state(self.runtime, bridge.tracker_state_payload(
                session_id=self.sid, state=name, sequence=self.sequence,
                publishing=name in {"TRACKING", "SUSPECTED"} and fields.get("track_id") is not None,
                **fields))

    def result(self, number: int, *, frame_id: int, query_unix_s: float, epoch: int = 2,
               candidates=None, preview: bool = True, preview_path: Path | None = None,
               preview_bytes: bytes | None = None, model=CANDIDATES_MODEL, k_ret=None,
               mutate=None) -> dict:
        candidates = [cand(0), cand(1, (0.6, 0.6, 0.1, 0.1))] if candidates is None else candidates
        query = f"{self.sid}-q{number}"
        path = None
        if preview:
            path = preview_path or self.previews / f"{frame_id}-{query}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(tiny_png() if preview_bytes is None else preview_bytes)
        if k_ret is None:
            k_ret = self.receipt_document()["k_ret"] if self.receipt_path.exists() else 3
        with production_clock(self.clock):
            payload = bridge.result_payload(
                query_id=query, result_id=f"{self.sid}-res{number}", request_id=None, epoch=epoch,
                segment_index=None, attempt=1, attempt_limit=3, purpose="designate",
                status="unique" if len(candidates) == 1 else "ambiguous", frame_id=frame_id,
                frame_sha256="0" * 64, capture_monotonic_s=1.0, capture_unix_s=1.0,
                query_unix_s=query_unix_s, candidates=candidates, model=model, k_ret=k_ret,
                preview_path=str(path) if path else None)
            if mutate:
                mutate(payload["result"])
            bridge.write_result(self.runtime, payload)
        loop.LanguageSession._append_result_line(self.writer, payload["result"])
        return payload["result"]

    def check(self, receipt_path: Path | None = None):
        return web.ReceiptCheck(loop, receipt_path or self.receipt_path, self.runtime)

    def monitor(self, bridge_module=bridge, receipt_path: Path | None = None):
        return web.Monitor(bridge_module, self.check(receipt_path), self.runtime, self.sid, self.session_dir,
                           self.archive, clock=self.clock)


class StubCli:
    def __init__(self):
        self.calls: list[list[str]] = []
        self.outcomes: list = []

    def __call__(self, argv):
        self.calls.append(list(argv))
        if self.outcomes:
            outcome = self.outcomes.pop(0)
            return outcome(argv) if callable(outcome) else outcome
        action = argv[3]
        request = argv[argv.index("--request-id") + 1]
        return {"exit": 0, "timeout": False, "stderr": "",
                "stdout": json.dumps({"request_id": request, "receipt": {
                    "request_id": request, "action": action.replace("-", "_"), "outcome": "APPLIED",
                    "at_sequence": 9}})}


class ReadOnlyBridge:
    """Only the read side of ``controller.language_bridge``; any writer or lock helper is missing."""

    ALLOWED = {"read_tracker_state", "read_result", "LanguageBridgeError", "INSTRUCTION_CLASSES",
               "INSTRUCTION_COLORS", "parse_instruction", "SESSION_LOCK_FILE", "default_is_alive"}

    def __init__(self):
        self.denied: list[str] = []

    def __getattr__(self, name):
        if name in self.ALLOWED:
            return getattr(bridge, name)
        self.denied.append(name)
        raise AttributeError(name)


def tree_digest(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): sha(path.read_bytes())
            for path in sorted(Path(root).rglob("*")) if path.is_file()}


class PageCase(unittest.TestCase):
    """A started session with a bound receipt, a stub CLI and the page's App."""

    def report_clock(self):
        return None                       # the real preflight clock

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.clock = Clock(T0)
        self.env = Env(Path(self._tmp.name), self.clock, report_clock=self.report_clock())
        self.env.start_session()
        self.env.frame(100)
        self.bridge = bridge
        self.stub = StubCli()
        quiet = mock.patch.object(web, "print", create=True)      # the page's terminal click lines
        quiet.start()
        self.addCleanup(quiet.stop)
        self.make_app()

    def make_app(self, bridge_module=None):
        bridge_module = bridge_module or self.bridge
        self.monitor = self.env.monitor(bridge_module)
        self.builder = web.CliRunner(sys.executable, REPO, self.env.runtime, SID)
        self.app = web.App(self.monitor, self.stub, self.builder, self.env.opdir, bridge_module, clock=self.clock)

    def tearDown(self):
        self._tmp.cleanup()

    def view(self):
        return self.monitor.poll()["view"]

    def snap(self):
        """What the page's /api/state returns right after the background poll."""
        self.monitor.poll()
        return self.app.state()

    def click(self, action, **extra):
        before = len(self.stub.calls)
        view = extra.pop("view", None) or self.view()
        reply = self.app.click(dict({"action": action, "view": view}, **extra))
        return reply, self.stub.calls[before:]

    def log_records(self) -> list[dict]:
        path = self.env.opdir / "operator-web.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def awaiting(self, *, query_at=1.0, issued_at=4.0, latest=110, **result):
        """QUERYING at T0+query_at, result presented at T0+issued_at, AWAITING_CONFIRMATION."""
        self.clock.now = T0 + query_at
        self.env.state("QUERYING")
        self.clock.now = T0 + issued_at
        record = self.env.result(result.pop("number", 1), frame_id=100, query_unix_s=T0 + query_at, **result)
        self.env.state("AWAITING_CONFIRMATION")
        self.env.frame(latest)
        return record

    def seen(self):
        candidate = self.snap()["candidate"]
        return {"name": candidate["preview"], "sha256": candidate["preview_sha256"]}


# --- AC-22：九态动作闭集、CLI 唯一出口、写入边界 -------------------------------------------------

CLARIFY_TABLE = {
    "IDLE": ["ask", "stop"],
    "QUERYING": ["ask", "stop"],
    "AWAITING_CONFIRMATION": ["confirm", "reject", "ask", "stop"],
    "TRACKING": ["ask", "verify", "release", "stop"],
    "SUSPECTED": ["ask", "verify", "confirm-lost", "dismiss", "stop"],
    "ACQUIRING": ["stop"],
    "LOST": ["ask", "stop"],
    "REINIT_REQUIRED": ["ask", "stop"],
}


class LegalActionTableTests(unittest.TestCase):
    def test_nine_state_closed_table_per_state(self):
        for name, base in CLARIFY_TABLE.items():
            for reusable in (False, True):
                want = set(base) | ({"respecify"} if reusable and name != "ACQUIRING" else set())
                got = web.legal_actions({"state": name, "reason": None}, instruction_reusable=reusable)
                self.assertEqual(set(got), want, (name, reusable))
                self.assertEqual(len(got), len(want), (name, reusable))
        self.assertEqual(set(CLARIFY_TABLE) | {"TERMINAL"}, set(bridge.SESSION_STATES))

    def test_tracking_allows_ask(self):
        self.assertIn("ask", web.legal_actions({"state": "TRACKING"}, instruction_reusable=False))
        self.assertIn("ask", web.legal_actions({"state": "SUSPECTED", "suspect_id": "s"}, instruction_reusable=False))

    def test_acquiring_offers_only_stop(self):
        for reusable in (False, True):
            self.assertEqual(web.legal_actions({"state": "ACQUIRING"}, instruction_reusable=reusable), ["stop"])

    def test_every_non_terminal_state_has_stop(self):
        for name in bridge.SESSION_STATES:
            if name == "TERMINAL":
                continue
            for reason in (None, "acquire_failed", "backend_fatal", "operator_release"):
                self.assertIn("stop", web.legal_actions({"state": name, "reason": reason},
                                                        instruction_reusable=True), (name, reason))

    def test_backend_fatal_only_stop(self):
        for name in ("LOST", "REINIT_REQUIRED"):
            self.assertEqual(web.legal_actions({"state": name, "reason": "backend_fatal"},
                                               instruction_reusable=True), ["stop"])

    def test_terminal_unknown_and_missing_state_have_no_action(self):
        self.assertEqual(web.legal_actions({"state": "TERMINAL", "reason": "operator_stop"}, instruction_reusable=True), [])
        self.assertEqual(web.legal_actions({"state": "TRACK_ENDED"}, instruction_reusable=True), [])
        self.assertEqual(web.legal_actions(None, instruction_reusable=True), [])


class CliExitTests(PageCase):
    def test_argv_same_interpreter_same_worktree_language_loop_cli(self):
        parser = loop.build_parser()
        cases = [("confirm", dict(token="res1", index=1), {"index": 1, "token": "res1"}),
                 ("ask", dict(instruction="the car"), {"instruction": "the car"}),
                 ("respecify", {}, {"instruction": None}), ("confirm-lost", dict(token="s1"), {"token": "s1"}),
                 ("reject", dict(token="res1"), {"token": "res1"}), ("release", dict(token="t1"), {"token": "t1"}),
                 ("dismiss", dict(token="s1"), {"token": "s1"}), ("verify", {}, {}), ("stop", {}, {})]
        for action, kwargs, fields in cases:
            argv = self.builder.argv(action, "r1", **kwargs)
            self.assertEqual(argv[:4], [sys.executable, "-m", "controller.language_loop", action])
            parsed = parser.parse_args(argv[3:])
            self.assertEqual((parsed.command, parsed.session_id, parsed.runtime, parsed.request_id),
                             (action, SID, str(self.env.runtime), "r1"))
            self.assertTrue(parsed.allow_shared_runtime)
            for key, value in fields.items():
                self.assertEqual(getattr(parsed, key), value, (action, key))
        with self.assertRaises(ValueError):
            self.builder.argv("confirm_lost", "r1")
        seen = {}

        def fake_run(argv, **kwargs):
            seen.update(argv=argv, **kwargs)
            return types.SimpleNamespace(returncode=0, stdout="{}", stderr="")

        with mock.patch.object(web.subprocess, "run", fake_run):
            self.builder(self.builder.argv("stop", "r9"))
        self.assertEqual(Path(seen["cwd"]).resolve(), REPO.resolve())
        self.assertEqual(seen["argv"][0], sys.executable)
        self.assertFalse(seen.get("shell", False))

    def test_main_uses_this_interpreter_and_repository(self):
        source = PAGE_PATH.read_text(encoding="utf-8")
        self.assertIn("CliRunner(sys.executable, REPO, runtime, sid)", source)
        self.assertEqual(web.REPO.resolve(), REPO.resolve())
        self.assertNotIn("--python", {a for action in web.build_parser()._actions for a in action.option_strings})

    def test_actions_outside_table_do_not_run_cli(self):
        self.env.receipt("r-ask", "ask")
        self.env.state("ACQUIRING", designation={"designation_id": 1, "frame_id_k": 100, "result": "TRACK_ENDED",
                                                 "acquire": {"status": "SLEWING"}})
        view = self.view()
        for action in ("ask", "respecify", "confirm", "reject", "verify", "confirm-lost", "dismiss", "release"):
            extra = {"instruction": {"class": "car"}} if action == "ask" else {}
            reply, calls = self.click(action, view=view, index=0, **extra)
            self.assertFalse(reply["ok"], action)
            self.assertEqual(calls, [], action)
        reply, calls = self.click("bogus", view=view)
        self.assertEqual(calls, [])
        reply, calls = self.click("stop", view=view)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][3], "stop")

    def test_instruction_known_only_from_accepted_ask(self):
        self.env.state("LOST", reason="operator_release")
        self.assertNotIn("respecify", self.monitor.poll()["legal"])
        self.env.receipt("r1", "ask", "REQUEST_INVALID", detail="ask_in_ACQUIRING")
        self.assertNotIn("respecify", self.monitor.poll()["legal"])
        self.env.receipt("r2", "ask", "APPLIED")
        self.assertIn("respecify", self.monitor.poll()["legal"])

    def test_track_ended_acquiring_path_shows_only_automatic_progress(self):
        self.env.receipt("r-ask", "ask")
        self.awaiting()
        reply, calls = self.click("confirm", index=1, preview_seen=self.seen())
        self.assertTrue(reply["ok"])
        self.assertEqual(calls[0][calls[0].index("--token") + 1], f"{SID}-res1")
        self.assertEqual(calls[0][-1], "1")
        self.assertNotIn("BOUND", reply["message"])
        self.assertIn("不等于绑定", reply["message"])
        designation = {"designation_id": 1, "frame_id_k": 100, "head_frame_id": 112, "result": "TRACK_ENDED",
                       "acquire": {"status": "SLEWING"}}
        self.env.state("ACQUIRING", designation=designation)
        before = len(self.stub.calls)
        for _ in range(5):
            snap = self.monitor.poll()
            state = self.app.state()
        self.assertEqual(snap["legal"], ["stop"])
        self.assertEqual(state["designation"]["result"], "TRACK_ENDED")
        self.assertEqual(state["designation"]["acquire_status"], "SLEWING")
        self.assertNotIn("TRACK_ENDED", web.STATE_ACTIONS)
        self.env.state("LOST", reason="acquire_failed",
                       designation=dict(designation, acquire={"status": "ACQUIRE_FAILED"}))
        snap = self.monitor.poll()
        self.assertEqual(snap["legal"], ["ask", "respecify", "stop"])
        self.assertEqual(snap["designation"]["acquire_status"], "ACQUIRE_FAILED")
        self.env.state("TRACKING", track_id=f"{SID}-t1",
                       designation=dict(designation, track_id=7, acquire={"status": "ADOPTED"}))
        self.assertEqual(self.monitor.poll()["legal"], ["ask", "verify", "release", "respecify", "stop"])
        self.assertEqual(len(self.stub.calls), before)     # the automatic path sent nothing

    def test_no_automatic_confirmation_or_action_while_polling(self):
        self.awaiting()
        for step in range(40):
            self.clock.now = T0 + 4.0 + step * 0.5
            self.monitor.poll()
            self.app.state()
        self.assertEqual(self.stub.calls, [])

    def test_page_never_writes_bridge_request_or_lock(self):
        readonly = ReadOnlyBridge()
        self.make_app(readonly)
        self.env.receipt("r-ask", "ask")
        self.awaiting()
        runtime_before = tree_digest(self.env.runtime)
        session_before = tree_digest(self.env.session_dir)
        self.click("confirm", index=0, preview_seen=self.seen())
        self.click("reject")
        self.app.mark_play_start()
        self.clock.now += 400
        for _ in range(3):
            self.app.state()
        self.assertEqual(readonly.denied, [])
        self.assertEqual(tree_digest(self.env.runtime), runtime_before)
        self.assertEqual(tree_digest(self.env.session_dir), session_before)
        written = {str(p.relative_to(self.env.root)) for p in self.env.root.rglob("*") if p.is_file()}
        self.assertIn(f"play-d1/{SID}/operator/operator-web.jsonl", written)
        source = PAGE_PATH.read_text(encoding="utf-8")
        for writer in ("write_request", "write_result", "write_tracker_state", "acquire_writer_lock",
                       "acquire_session_lock", "send_request", "release_session_lock"):
            self.assertNotIn(writer, source, writer)


UNKNOWN_OUTCOME = {"exit": 5, "timeout": False, "stdout": "", "stderr": "no receipt"}


class RetryStateTransitionTests(PageCase):
    """C2@K1K3 C2-1 (AC-22): a same-request_id retry re-checks state, view, table and token before any CLI."""

    def unknown(self, action, **extra):
        self.stub.outcomes.append(dict(UNKNOWN_OUTCOME))
        reply, calls = self.click(action, **extra)
        self.assertEqual((reply["ok"], len(calls)), (False, 1))
        self.assertEqual([u["request_id"] for u in self.app.state()["unknowns"]], [reply["request_id"]])
        return reply["request_id"], calls[0]

    def retry(self, request_id):
        before = len(self.stub.calls)
        reply = self.app.click({"retry_request_id": request_id})
        return reply, self.stub.calls[before:]

    def entry(self, request_id):
        return next(u for u in self.snap()["unknowns"] if u["request_id"] == request_id)

    def assert_refused_without_cli(self, request_id, reply, calls, fragment):
        self.assertEqual((reply["ok"], calls), (False, []))
        self.assertIn(fragment, reply["message"])
        entry = self.entry(request_id)                  # kept for its late receipt, but not retryable
        self.assertFalse(entry["retry_allowed"])
        self.assertIn(fragment, entry["retry_block"])
        last = self.log_records()[-1]
        self.assertEqual((last["kind"], last["action"], last["request_id"]), ("refused", "retry", request_id))
        self.assertIn("current_view", last)

    def test_ask_unknown_then_acquiring_retry_sends_nothing(self):
        self.env.state("IDLE")
        request_id, _ = self.unknown("ask", instruction={"class": "car"})
        self.env.state("ACQUIRING", designation={"designation_id": 1, "frame_id_k": 100, "result": "TRACK_ENDED",
                                                 "acquire": {"status": "SLEWING"}})
        reply, calls = self.retry(request_id)
        self.assert_refused_without_cli(request_id, reply, calls, "状态或令牌已变")

    def test_confirm_unknown_then_terminal_retry_sends_nothing(self):
        self.awaiting()
        request_id, _ = self.unknown("confirm", index=0, preview_seen=self.seen())
        self.env.terminal()
        self.env.state("TERMINAL", reason="operator_stop")
        reply, calls = self.retry(request_id)
        self.assert_refused_without_cli(request_id, reply, calls, "状态或令牌已变")

    def test_release_unknown_then_backend_fatal_retry_sends_nothing(self):
        self.env.state("TRACKING", track_id=f"{SID}-t1")
        request_id, _ = self.unknown("release")
        self.env.state("REINIT_REQUIRED", reason="backend_fatal")
        reply, calls = self.retry(request_id)
        self.assert_refused_without_cli(request_id, reply, calls, "状态或令牌已变")

    def test_confirm_unknown_then_new_result_token_retry_sends_nothing(self):
        self.awaiting()
        request_id, _ = self.unknown("confirm", index=0, preview_seen=self.seen())
        self.awaiting(number=2, query_at=5.0, issued_at=6.0)      # same state, new result_id token
        reply, calls = self.retry(request_id)
        self.assert_refused_without_cli(request_id, reply, calls, "状态或令牌已变")

    def test_confirm_unknown_past_deadline_retry_sends_nothing(self):
        self.awaiting()
        request_id, _ = self.unknown("confirm", index=0, preview_seen=self.seen())
        candidate = self.snap()["candidate"]
        self.clock.now = min(candidate["query_deadline_unix_s"], candidate["presented_deadline_unix_s"]) + 0.01
        reply, calls = self.retry(request_id)
        self.assert_refused_without_cli(request_id, reply, calls, "截止")

    def test_confirm_unknown_preview_replaced_retry_sends_nothing(self):
        self.awaiting()
        request_id, _ = self.unknown("confirm", index=0, preview_seen=self.seen())
        preview = self.env.previews / f"100-{SID}-q1.png"
        preview.write_bytes(tiny_png(b"\x00\xff\x00"))
        reply, calls = self.retry(request_id)
        self.assert_refused_without_cli(request_id, reply, calls, "预览已换")

    def test_unchanged_view_retry_resends_the_same_request(self):
        self.awaiting()
        request_id, first = self.unknown("confirm", index=1, preview_seen=self.seen())
        self.assertTrue(self.entry(request_id)["retry_allowed"])
        reply, calls = self.retry(request_id)
        self.assertEqual(calls, [first])                 # same argv: same request_id, token and index
        self.assertTrue(reply["ok"])
        self.assertEqual(self.log_records()[-1]["kind"], "retry_same_request_id")


class PageScriptButtonTests(PageCase):
    """C2@K1K3 C2-1/C2-2: the page script's ``paintButtons`` on real ``/api/state`` snapshots (node, no browser)."""

    HARNESS = """
const els = {};
global.document = {getElementById: (id) => (id in els ? els[id] : null)};
global.window = {confirm: () => true};
global.fetch = () => new Promise(() => {});
global.setInterval = () => 0;
__SCRIPT__
const out = {};
for (const [name, s] of Object.entries(__CASES__)) {
  snap = s; rendered = {key: "k", view: s.view}; sending = false; fetchFailed = false;
  const retry = (s.unknowns || []).map((u) => ({disabled: false, dataset: {requestId: u.request_id}}));
  els.buttons = {querySelectorAll: () => []};
  els.unknown = {querySelectorAll: () => retry};
  els["c-send"] = null;
  els.mark = {disabled: false};
  paintButtons();
  out[name] = {mark_disabled: els.mark.disabled, retry_disabled: retry.map((r) => r.disabled)};
}
console.log(JSON.stringify(out));
"""

    def paint(self, cases: dict) -> dict:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node not installed: page script not exercised")
        script = re.search(r"<script>(.*)</script>", web.PAGE, re.S).group(1)
        program = self.HARNESS.replace("__SCRIPT__", script).replace(
            "__CASES__", json.dumps(cases, ensure_ascii=False, default=str))
        path = Path(self._tmp.name) / "paint.js"
        path.write_text(program, encoding="utf-8")
        done = subprocess.run([node, str(path)], capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout.strip().splitlines()[-1])

    def test_retry_button_follows_current_state_table(self):
        self.env.state("IDLE")
        self.stub.outcomes.append(dict(UNKNOWN_OUTCOME))
        self.click("ask", instruction={"class": "car"})
        cases = {"same": self.snap()}
        self.env.state("ACQUIRING", designation={"designation_id": 1, "frame_id_k": 100, "result": "TRACK_ENDED",
                                                 "acquire": {"status": "SLEWING"}})
        cases["moved"] = self.snap()
        painted = self.paint(cases)
        self.assertEqual(painted["same"]["retry_disabled"], [False])
        self.assertEqual(painted["moved"]["retry_disabled"], [True])

    def test_mark_button_disabled_on_same_number_block(self):
        self.env.state("IDLE")
        cases = {"free": self.snap()}
        self.env.start_session()                          # a second session_started: same number reused
        cases["blocked"] = self.snap()
        painted = self.paint(cases)
        self.assertFalse(painted["free"]["mark_disabled"])
        self.assertTrue(painted["blocked"]["mark_disabled"])


class HttpBoundaryTests(PageCase):
    def setUp(self):
        super().setUp()
        self.server = web.build_server(self.app, 0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        super().tearDown()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        data = response.read()
        connection.close()
        return response.status, data

    def test_listens_on_loopback_only(self):
        self.assertEqual(web.HOST, "127.0.0.1")
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        status, data = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(self.app.nonce.encode(), data)
        status, _ = self.request("GET", "/api/state", headers={"Host": f"evil.example:{self.port}"})
        self.assertEqual(status, 403)

    def test_post_requires_nonce_and_same_origin(self):
        body = json.dumps({"action": "stop", "view": {}})
        self.assertEqual(self.request("POST", "/api/action", body)[0], 403)
        self.assertEqual(self.request("POST", "/api/action", body, {
            "X-Operator-Nonce": self.app.nonce, "Origin": "http://evil.example"})[0], 403)
        self.assertEqual(self.request("POST", "/api/play-start", "{}", {"Origin": f"http://127.0.0.1:{self.port}"})[0], 403)
        status, data = self.request("POST", "/api/action", body, {"X-Operator-Nonce": self.app.nonce,
                                                                  "Content-Type": "application/json"})
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(data)["ok"])
        self.assertEqual(self.stub.calls, [])

    def test_preview_endpoint_serves_only_the_bound_bytes(self):
        self.awaiting()
        candidate = self.snap()["candidate"]
        name, digest = candidate["preview"], candidate["preview_sha256"]
        status, data = self.request("GET", f"/preview/{name}?sha={digest}")
        self.assertEqual((status, sha(data)), (200, digest))
        self.assertEqual(self.request("GET", f"/preview/{name}?sha={'0' * 64}")[0], 409)
        self.assertEqual(self.request("GET", f"/preview/{name}")[0], 404)
        self.assertEqual(self.request("GET", f"/preview/..%2Fresults.jsonl?sha={digest}")[0], 404)


# --- AC-23：收据绑定、三重时效、预览/index/result_id 绑定 ---------------------------------------


class ReceiptBindingTests(PageCase):
    def evaluate(self, check=None):
        self.monitor.poll()
        return (check or self.env.check()).evaluate(self.monitor.session_started, self.monitor.started_count)

    def test_candidates_receipt_bound_to_session_and_config_ok(self):
        result = self.evaluate()
        self.assertTrue(result["ok"], result["problems"])
        document = self.env.receipt_document()
        values = result["values"]
        for key in ("hz", "retained_frame_count", "k_ret", "k_conf", "t_ret_s", "t_conf_s", "host", "backend",
                    "model_form"):
            self.assertEqual(values[key], document[key], key)
        self.assertEqual(values["retained_frame_count"], 1500)

    def test_old_loop001_receipt_refused_and_confirm_disabled(self):
        self.make_app()
        self.monitor.receipt_check = self.env.check(LOOP_RECEIPT)
        self.awaiting()
        snap = self.snap()
        self.assertFalse(snap["receipt"]["ok"])
        self.assertTrue(any(p.startswith("收据身份不是本项 candidates 单宿主") for p in snap["receipt"]["problems"]),
                        snap["receipt"]["problems"])
        self.assertFalse(snap["candidate"]["confirmable"])
        self.assertIsNone(snap["candidate"]["frames_limit"])
        reply, calls = self.click("confirm", index=0, preview_seen=self.seen())
        self.assertFalse(reply["ok"])
        self.assertEqual(calls, [])

    def test_missing_receipt_or_report_disables_confirm(self):
        missing = self.evaluate(self.env.check(self.env.root / "nope.json"))
        self.assertFalse(missing["ok"])
        self.assertIn("收据缺失", missing["problems"][0])
        self.env.report_path.unlink()
        self.awaiting()
        snap = self.snap()
        self.assertFalse(snap["receipt"]["ok"])
        self.assertTrue(any("§2.7 报告" in p for p in snap["receipt"]["problems"]))
        reply, calls = self.click("confirm", index=0, preview_seen=self.seen())
        self.assertEqual((reply["ok"], calls), (False, []))

    def test_report_bytes_changed_disables_confirm(self):
        with self.env.report_path.open("a", encoding="utf-8") as handle:
            handle.write(" ")
        result = self.evaluate()
        self.assertFalse(result["ok"])
        self.assertTrue(any("SHA" in p for p in result["problems"]))

    def test_effective_R_mismatch_disables_confirm(self):
        self.env.set_retained(128)
        self.awaiting()
        snap = self.snap()
        self.assertFalse(snap["receipt"]["ok"])
        self.assertTrue(any("生效配置" in p for p in snap["receipt"]["problems"]))
        self.assertFalse(snap["candidate"]["confirmable"])

    def test_session_started_with_other_receipt_disables_confirm(self):
        other = Env(self.env.root / "other", self.clock, report_clock=iter(float(i) for i in range(10_000)).__next__)
        payload = loop.KReceipt.from_document(other.receipt_document()).payload()
        with tempfile.TemporaryDirectory() as scratch:
            env = Env(Path(scratch), self.clock)
            env.start_session(payload)
            monitor = env.monitor()
            env.state("IDLE")
            snap = monitor.poll()
        self.assertFalse(snap["receipt"]["ok"])
        self.assertTrue(any("session_started.k_receipt" in p for p in snap["receipt"]["problems"]))

    def test_not_yet_started_session_is_unbound(self):
        with tempfile.TemporaryDirectory() as scratch:
            env = Env(Path(scratch), self.clock)
            result = env.check().evaluate(None, 0)
        self.assertFalse(result["ok"])
        self.assertTrue(any("session_started" in p for p in result["problems"]))


class ReceiptValuesTests(PageCase):
    """A receipt with p95 = 1 s (fake preflight clock): gates follow it, not LOOP-001's 6 s / 80."""

    def report_clock(self):
        return iter(float(i) for i in range(10_000)).__next__     # every sample takes exactly 1 s

    def test_gate_values_read_from_receipt_not_hand_copied(self):
        document = self.env.receipt_document()
        self.assertEqual(document["p95_s"], 1.0)
        self.awaiting(query_at=1.0, issued_at=4.0)
        candidate = self.snap()["candidate"]
        self.assertTrue(candidate["confirmable"], candidate["why_not"])
        self.assertEqual(candidate["t_ret_s"], document["k_ret"] / document["hz"])
        self.assertEqual(candidate["t_conf_s"], loop.T_CONF_S)
        self.assertEqual(candidate["frames_limit"], document["k_ret"] + document["k_conf"])
        self.assertEqual((document["k_ret"], document["k_conf"]), (7, 50))
        self.assertAlmostEqual(candidate["query_deadline_unix_s"], T0 + 1.0 + 1.4 + 10.0)


class ConfirmGateTests(PageCase):
    def test_three_deadlines_earliest_wins_from_session_times(self):
        document = self.env.receipt_document()
        t_ret = document["k_ret"] / document["hz"]
        self.awaiting(query_at=1.0, issued_at=4.0)
        candidate = self.snap()["candidate"]
        self.assertTrue(candidate["confirmable"], candidate["why_not"])
        self.assertAlmostEqual(candidate["query_deadline_unix_s"], T0 + 1.0 + t_ret + 10.0)
        self.assertAlmostEqual(candidate["presented_deadline_unix_s"], T0 + 14.0)
        self.assertEqual(candidate["deadline_from"], "查询起")
        self.assertEqual(candidate["frames_delta"], 10)
        self.assertEqual(candidate["frames_limit"], document["k_ret"] + document["k_conf"])
        with tempfile.TemporaryDirectory():
            self.awaiting(query_at=20.0, issued_at=20.1, number=2)
        candidate = self.snap()["candidate"]
        self.assertEqual(candidate["deadline_from"], "结果出现起")
        self.assertAlmostEqual(candidate["presented_deadline_unix_s"], T0 + 30.1)

    def test_poll_refresh_and_restart_never_renew_deadline(self):
        self.awaiting()
        first = self.snap()["candidate"]
        self.clock.now = T0 + 9.0
        for _ in range(5):
            self.monitor.poll()
        fresh = self.env.monitor()
        fresh.poll()
        for snap in (self.snap()["candidate"], fresh.public(self.clock.now)["candidate"]):
            self.assertEqual(snap["query_deadline_unix_s"], first["query_deadline_unix_s"])
            self.assertEqual(snap["presented_deadline_unix_s"], first["presented_deadline_unix_s"])

    def test_expired_deadline_refuses_without_cli(self):
        self.awaiting()
        seen = self.seen()
        candidate = self.snap()["candidate"]
        self.clock.now = min(candidate["query_deadline_unix_s"], candidate["presented_deadline_unix_s"]) + 0.01
        reply, calls = self.click("confirm", index=0, preview_seen=seen)
        self.assertEqual((reply["ok"], calls), (False, []))
        self.assertIn("截止", reply["message"])

    def test_frame_gate_exceeded_refuses_without_cli(self):
        document = self.env.receipt_document()
        self.awaiting(latest=100 + document["k_ret"] + document["k_conf"] + 1)
        reply, calls = self.click("confirm", index=0, preview_seen={"name": None, "sha256": None})
        self.assertEqual((reply["ok"], calls), (False, []))
        self.assertIn("帧差门", reply["message"])

    def test_stale_or_unreadable_snapshot_refuses(self):
        self.awaiting()
        seen = self.seen()
        stale = self.monitor.public(self.clock.now + 5.0)["candidate"]
        self.assertFalse(stale["confirmable"])
        view = self.monitor.snapshot["view"]
        with mock.patch.object(bridge, "read_tracker_state", side_effect=OSError("disk")):
            reply, calls = self.click("confirm", index=0, preview_seen=seen, view=view)
        self.assertEqual((reply["ok"], calls), (False, []))

    def test_wrong_index_refused(self):
        self.awaiting()
        seen = self.seen()
        for index in (2, -1, True, "0", None):
            reply, calls = self.click("confirm", index=index, preview_seen=seen)
            self.assertEqual((reply["ok"], calls), (False, []), index)

    def test_misaligned_index_not_confirmable(self):
        def shuffle(result):
            result["candidates"][0]["index"], result["candidates"][1]["index"] = 1, 0
        self.awaiting(mutate=shuffle)
        candidate = self.snap()["candidate"]
        self.assertFalse(candidate["confirmable"])
        self.assertIn("index", candidate["why_not"])

    def test_preview_not_displayed_or_other_image_refused(self):
        self.awaiting()
        seen = self.seen()
        for bad in (None, {}, {"name": seen["name"]}, {"name": seen["name"], "sha256": "0" * 64},
                    {"name": "1-x.png", "sha256": seen["sha256"]}, seen["name"]):
            reply, calls = self.click("confirm", index=0, preview_seen=bad)
            self.assertEqual((reply["ok"], calls), (False, []), bad)
        reply, calls = self.click("confirm", index=0, preview_seen=seen)
        self.assertTrue(reply["ok"])
        self.assertEqual(len(calls), 1)

    def test_preview_replaced_after_display_refused(self):
        self.awaiting()
        seen = self.seen()
        (self.env.previews / seen["name"]).write_bytes(tiny_png(b"\x00\xff\x00"))
        reply, calls = self.click("confirm", index=0, preview_seen=seen)
        self.assertEqual((reply["ok"], calls), (False, []))

    def test_corrupt_missing_or_cross_session_preview_not_confirmable(self):
        self.awaiting(preview_bytes=b"not a png")
        self.assertIn("PNG", self.snap()["candidate"]["why_not"])
        self.awaiting(preview=False, number=2)
        self.assertIn("预览缺失", self.snap()["candidate"]["why_not"])
        other = self.env.root / "other-session" / "previews" / f"100-{SID}-q3.png"
        self.awaiting(preview_path=other, number=3)
        candidate = self.snap()["candidate"]
        self.assertFalse(candidate["confirmable"])
        self.assertIn("本会话", candidate["why_not"])

    def test_old_token_view_refused(self):
        self.awaiting()
        old_view, seen = self.view(), self.seen()
        self.awaiting(number=2, query_at=5.0, issued_at=6.0)
        reply, calls = self.click("confirm", index=0, preview_seen=seen, view=old_view)
        self.assertEqual((reply["ok"], calls), (False, []))
        self.assertIn("过期", reply["message"])
        reply, calls = self.click("reject", view=old_view)
        self.assertEqual((reply["ok"], calls), (False, []))

    def test_non_candidates_result_or_other_k_ret_not_confirmable(self):
        self.awaiting(model={"backend": "http", "model_form": "c2-adapter"})
        self.assertIn("candidates", self.snap()["candidate"]["why_not"])
        self.awaiting(number=2, k_ret=999)
        self.assertIn("k_ret", self.snap()["candidate"]["why_not"])

    def test_applied_is_not_reported_as_bound(self):
        self.awaiting()
        reply, _ = self.click("confirm", index=0, preview_seen=self.seen())
        self.assertEqual(reply["receipt"]["outcome"], "APPLIED")
        receipt, meaning = web.interpret({"exit": 0, "stdout": json.dumps({"receipt": {"outcome": "APPLIED"}})})
        self.assertIn("不等于绑定", meaning)
        snap = self.snap()
        self.assertIsNone(snap["designation"])            # nothing claims a binding before the session says so


# --- AC-24：SID 复用、Play 计时、操作日志、操作单 §4 --------------------------------------------


class SidGuardTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.clock = Clock(T0)
        self.env = Env(Path(self._tmp.name), self.clock, receipt=False)

    def tearDown(self):
        self._tmp.cleanup()

    def run_main(self, sid):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), mock.patch.object(web, "build_server") as server:
            code = web.main(["--sid", sid, "--play-root", str(self.env.play_root),
                             "--runtime", str(self.env.runtime), "--port", "0"])
        return code, err.getvalue(), server

    def usage(self, sid=SID, alive=True):
        return web.sid_usage(sid, self.env.play_root / "sessions" / sid, self.env.play_root / sid / "unity-runtime",
                             self.env.runtime, bridge, is_alive=lambda pid: alive)

    def test_retired_acq_d1_1_refused_at_start(self):
        code, err, server = self.run_main("acq-d1-1")
        self.assertEqual(code, 2)
        self.assertIn("同号不可复用", err)
        server.assert_not_called()
        self.assertFalse((self.env.play_root / "acq-d1-1").exists())

    def test_sid_format_enforced(self):
        for sid in ("diag-1", "acq-d1-0", "acq-d1-2/../x", "acq-d1-"):
            code, _, server = self.run_main(sid)
            self.assertEqual(code, 2, sid)
            server.assert_not_called()

    def test_closed_session_directory_refused(self):
        self.env.start_session({"k": 1})
        self.env.terminal()
        self.env.lock(os.getpid())
        self.assertIn("TERMINAL", self.usage())
        code, err, server = self.run_main(SID)
        self.assertEqual(code, 2)
        server.assert_not_called()
        self.assertFalse(self.env.opdir.exists())

    def test_second_session_started_refused(self):
        self.env.start_session({"k": 1})
        self.env.start_session({"k": 1})
        self.env.lock(os.getpid())
        self.assertIn("2 个 session_started", self.usage())

    def test_archive_same_sid_refused(self):
        self.env.archive.mkdir(parents=True)
        self.assertIn("归档", self.usage())

    def test_directory_without_session_started_refused(self):
        self.env.session_dir.mkdir(parents=True)
        self.assertIn("没有 session_started", self.usage())

    def test_dead_or_foreign_lock_refused(self):
        self.env.start_session({"k": 1})
        self.assertIn("活会话", self.usage())
        self.env.lock(4242)
        self.assertIn("活会话", self.usage(alive=False))
        self.env.lock(4242, sid="acq-d1-9")
        self.assertIn("活会话", self.usage(alive=True))

    def test_active_session_or_fresh_number_allowed(self):
        self.assertIsNone(self.usage())
        self.env.start_session({"k": 1})
        self.env.lock(4242)
        self.assertIsNone(self.usage(alive=True))


class SidDuringRunTests(PageCase):
    def test_second_session_started_disables_every_action(self):
        self.env.state("IDLE")
        self.assertEqual(self.monitor.poll()["legal"], ["ask", "stop"])
        self.env.start_session()
        snap = self.monitor.poll()
        self.assertEqual(snap["legal"], [])
        self.assertIn("session_started", snap["sid_block"])
        reply, calls = self.click("stop", view=snap["view"])
        self.assertEqual((reply["ok"], calls), (False, []))
        self.assertIn("同号不可复用", reply["message"])

    def test_archive_appearing_disables_every_action(self):
        self.env.state("TRACKING", track_id=f"{SID}-t1")
        self.env.archive.mkdir(parents=True)
        snap = self.monitor.poll()
        self.assertEqual(snap["legal"], [])
        self.assertIn("归档", snap["sid_block"])

    def test_activity_after_close_record_blocked(self):
        self.env.state("IDLE")
        self.env.terminal()
        self.env.state("TERMINAL", reason="operator_stop")
        self.assertEqual(self.monitor.poll()["legal"], [])
        self.env.state("IDLE", epoch=5)
        snap = self.monitor.poll()
        self.assertEqual(snap["legal"], [])
        self.assertTrue(snap["sid_block"])

    def assert_mark_refused(self):
        self.assertTrue(self.snap()["sid_block"])
        reply = self.app.mark_play_start()              # the server entrance, not only the button
        self.assertFalse(reply["ok"])
        self.assertIn("同号不可复用", reply["message"])
        records = self.log_records()
        self.assertFalse(any(r["kind"] == "play_start_marked" for r in records))
        self.assertEqual((records[-1]["kind"], records[-1]["action"]), ("refused", "play_start_mark"))
        snap = self.snap()
        self.assertEqual(snap["timer"]["status"], "unmarked")
        self.assertIn("同号不可复用", snap["timer"]["mark_block"])
        self.assertEqual(self.stub.calls, [])

    def test_second_session_started_disables_play_mark(self):
        self.env.state("IDLE")
        self.assertIsNone(self.snap()["timer"].get("mark_block"))
        self.env.start_session()
        self.assert_mark_refused()

    def test_archive_disables_play_mark(self):
        self.env.state("TRACKING", track_id=f"{SID}-t1")
        self.env.archive.mkdir(parents=True)
        self.assert_mark_refused()

    def test_activity_after_close_disables_play_mark(self):
        self.env.state("IDLE")
        self.env.terminal()
        self.env.state("TERMINAL", reason="operator_stop")
        self.assertIsNone(self.snap()["sid_block"])
        self.env.state("IDLE", epoch=5)                 # this number is active again after its end
        self.assert_mark_refused()

    # --- R2@K1K3 K1K3-R2-1: a normal end is not a reused number ------------------------------------

    def test_normal_end_between_journal_and_state_is_not_reuse(self):
        """K1K3-R2-1: the session journals TERMINAL before it rewrites tracker_state; a poll in between
        still reads the old state. That is the same session ending, not the number being reused."""
        self.clock.now = T0 + 1.0
        self.env.state("TRACKING", track_id=f"{SID}-t1")
        self.assertIn("stop", self.monitor.poll()["legal"])
        self.clock.now = T0 + 2.0
        self.env.terminal()                             # LanguageSession._journal("state", TERMINAL)
        snap = self.monitor.poll()                      # tracker_state is still the old TRACKING
        self.assertIsNone(snap["sid_block"])
        self.assertEqual(snap["legal"], [])             # ended: no action offered all the same
        self.env.state("TERMINAL", reason="operator_stop")   # bridge.write_tracker_state
        snap = self.snap()
        self.assertIsNone(snap["sid_block"])
        self.assertIsNone(snap["timer"]["mark_block"])
        reply = self.app.mark_play_start()
        self.assertNotIn("同号不可复用", reply["message"])
        self.assertFalse(any(r["kind"] == "refused" for r in self.log_records()))
        self.assertIsNone(self.monitor.poll()["sid_block"])
        self.assertEqual(self.stub.calls, [])

    def test_concurrent_poll_with_older_state_read_is_not_reuse(self):
        """K1K3-R2-1 second path: a poll that read tracker_state before the end must not judge (or
        overwrite the snapshot) after a later poll that already saw the TERMINAL journal record."""
        self.env.state("TRACKING", track_id=f"{SID}-t1")
        self.monitor.poll()
        read_done, go = threading.Event(), threading.Event()
        calls = []

        def slow_first_read(runtime):
            document = bridge.read_tracker_state(runtime)
            calls.append((document or {}).get("tracker_state", {}).get("state"))
            if len(calls) == 1:
                read_done.set()
                go.wait(5)
            return document

        monitor = self.env.monitor(types.SimpleNamespace(
            read_tracker_state=slow_first_read, read_result=bridge.read_result,
            LanguageBridgeError=bridge.LanguageBridgeError))
        first = threading.Thread(target=monitor.poll)       # e.g. the background poll
        first.start()
        self.assertTrue(read_done.wait(5))                   # it holds the old TRACKING read
        self.env.terminal()
        self.env.state("TERMINAL", reason="operator_stop")
        second = threading.Thread(target=monitor.poll)      # e.g. a click's poll, after the end
        second.start()
        second.join(0.3)
        go.set()
        first.join(5)
        second.join(5)
        self.assertEqual(calls, ["TRACKING", "TERMINAL"])
        snap = monitor.poll()
        self.assertIsNone(snap["sid_block"])
        self.assertEqual(snap["state"]["state"], "TERMINAL")

    def test_new_state_after_close_record_blocked_without_seeing_terminal_state(self):
        """Still a reuse when the page never saw the TERMINAL tracker_state: the new state was issued
        after the TERMINAL journal record."""
        self.env.state("IDLE")
        self.monitor.poll()
        self.clock.now = T0 + 1.0
        self.env.terminal()
        self.env.state("TERMINAL", reason="operator_stop")
        self.clock.now = T0 + 2.0
        self.env.state("IDLE", epoch=5)
        snap = self.monitor.poll()
        self.assertEqual(snap["legal"], [])
        self.assertIn("同号被复用", snap["sid_block"])

    def test_unreadable_state_does_not_let_the_mark_through(self):
        with mock.patch.object(self.monitor, "poll", side_effect=OSError("bridge gone")):
            reply = self.app.mark_play_start()
        self.assertFalse(reply["ok"])
        self.assertFalse(any(r["kind"] == "play_start_marked" for r in self.log_records()))

    def test_retired_number_never_gets_actions(self):
        monitor = web.Monitor(bridge, self.env.check(), self.env.runtime, "acq-d1-1", self.env.session_dir,
                              self.env.archive, clock=self.clock)
        with mock.patch.object(bridge, "read_tracker_state", return_value={"tracker_state": {
                "session_id": "acq-d1-1", "state": "IDLE", "epoch": 1}}):
            snap = monitor.poll()
        self.assertEqual(snap["legal"], [])
        self.assertTrue(snap["sid_block"])


class PlayTimerTests(PageCase):
    def test_unmarked_never_uses_page_or_session_start(self):
        self.env.state("IDLE")
        self.clock.now = T0 + 500
        timer = self.app.state()["timer"]
        self.assertEqual(timer["status"], "unmarked")
        self.assertIsNone(timer["remaining_s"])
        self.assertIsNone(timer["start_unix_s"])

    def test_mark_persisted_restart_and_refresh_do_not_reset(self):
        self.clock.now = T0 + 10
        self.assertTrue(self.app.mark_play_start()["ok"])
        self.clock.now = T0 + 110
        timer = self.app.state()["timer"]
        self.assertEqual((timer["status"], timer["elapsed_s"], timer["remaining_s"]), ("running", 100.0, 80.0))
        self.make_app()                                   # page restart reads the persisted first mark
        timer = self.app.state()["timer"]
        self.assertEqual((timer["start_unix_s"], timer["remaining_s"]), (T0 + 10, 80.0))
        self.clock.now = T0 + 120
        reply = self.app.mark_play_start()
        self.assertFalse(reply["ok"])
        self.assertEqual(self.app.state()["timer"]["start_unix_s"], T0 + 10)
        marks = [r for r in self.log_records() if r["kind"] == "play_start_marked"]
        self.assertEqual(len(marks), 1)
        self.assertTrue(any(r["kind"] == "refused" and r.get("action") == "play_start_mark" for r in self.log_records()))

    def test_deadline_only_prompts_no_auto_stop(self):
        self.env.state("TRACKING", track_id=f"{SID}-t1")
        self.app.mark_play_start()
        self.clock.now = T0 + web.PLAY_LIMIT_S + 1
        for _ in range(6):
            timer = self.app.state()["timer"]
        self.assertEqual(timer["status"], "due")
        self.assertIn("不会自动停止", timer["message"])
        self.assertEqual(self.stub.calls, [])
        self.assertIn("stop", self.monitor.poll()["legal"])
        notices = [r for r in self.log_records() if r["kind"] == "play_deadline_notice"]
        self.assertEqual(len(notices), 1)
        self.make_app()
        self.app.state()
        self.assertEqual(len([r for r in self.log_records() if r["kind"] == "play_deadline_notice"]), 1)

    def test_unreadable_log_means_manual_timing_without_remaining(self):
        self.env.opdir.mkdir(parents=True, exist_ok=True)
        (self.env.opdir / "operator-web.jsonl").write_text('{"kind": "play_start_marked"\n', encoding="utf-8")
        self.make_app()
        timer = self.app.state()["timer"]
        self.assertEqual(timer["status"], "unreliable")
        self.assertIsNone(timer["remaining_s"])
        self.assertIn("手工计时", timer["message"])
        self.assertFalse(self.app.mark_play_start()["ok"])


class OperatorLogTests(PageCase):
    def test_every_click_refusal_unknown_retry_and_timer_logged(self):
        self.env.state("IDLE")
        journal_before = (self.env.session_dir / loop.SESSION_JOURNAL).read_bytes()
        self.app.mark_play_start()
        ok, _ = self.click("ask", instruction={"class": "car"})
        refused, _ = self.click("verify")
        self.clock.now += 2
        self.stub.outcomes.append({"exit": 5, "timeout": False, "stdout": "", "stderr": "no receipt"})
        unknown, _ = self.click("stop")
        retry = self.app.click({"retry_request_id": unknown["request_id"]})
        kinds = [r["kind"] for r in self.log_records()]
        self.assertEqual(kinds, ["play_start_marked", "click", "refused", "click", "retry_same_request_id"])
        records = self.log_records()
        self.assertTrue(ok["ok"] and not refused["ok"] and not unknown["ok"] and retry["ok"])
        self.assertTrue(records[3]["result_unknown"])
        self.assertEqual(records[4]["request_id"], unknown["request_id"])
        for record in records[1:]:
            self.assertIn("at_unix_s", record)
        for record in (records[1], records[3], records[4]):
            for key in ("view", "argv", "exit_code", "stdout", "receipt", "started_unix_s"):
                self.assertIn(key, record)
        self.assertEqual(records[1]["argv"][-1], "the car")
        self.assertEqual((self.env.session_dir / loop.SESSION_JOURNAL).read_bytes(), journal_before)
        self.assertEqual(self.app.log_path, self.env.play_root / SID / "operator" / "operator-web.jsonl")


class OperationSheetSection4Tests(unittest.TestCase):
    def section(self) -> str:
        text = SHEET.read_text(encoding="utf-8")
        return text[text.index("## 4."):text.index("## 5.")]

    def commands(self, marker: str) -> list[list[str]]:
        """Arguments after ``marker`` (a script path or ``controller.language_loop``) in each code span."""
        found = []
        prose = re.sub(r"```.*?```", "", self.section(), flags=re.S)      # fenced blocks break span pairing
        for code in re.findall(r"`([^`]+)`", prose):
            code = code.replace("\\|", "|").split("|")[0].split(" 2>&1")[0]
            tokens = shlex.split(code.replace(";", " ; "))
            for position, token in enumerate(tokens):
                if token.endswith(marker):
                    rest = tokens[position + 1:]
                    rest = rest[:rest.index(";")] if ";" in rest else rest
                    if rest:                      # a bare path in prose is not a command
                        found.append(rest)
        return found

    def test_page_usage_documented_and_parses(self):
        section = self.section()
        for phrase in ("docs/evidence/P1-ENG-ACQ-001-operator-web.py", "operator-web.jsonl", "127.0.0.1",
                       "不会自动", "§3", "acq-d1-1", "回退"):
            self.assertIn(phrase, section, phrase)
        pages = self.commands("P1-ENG-ACQ-001-operator-web.py")
        self.assertTrue(pages)
        for argv in pages:
            parsed = web.build_parser().parse_args([a.replace("$SID", SID) for a in argv])
            self.assertEqual(parsed.sid, SID)

    def test_cli_fallback_commands_parse_with_the_real_cli(self):
        parser = loop.build_parser()
        seen = set()
        for argv in self.commands("controller.language_loop"):
            args = [a.replace("$SID", SID).replace("<index>", "0").replace("<last_result.result_id>", "r")
                    .replace("<result_id>", "r").replace("<track_id>", "t") for a in argv]
            parsed = parser.parse_args(args)
            seen.add(parsed.command)
        self.assertTrue({"run", "status", "ask", "confirm", "reject", "release", "stop"} <= seen, seen)


if __name__ == "__main__":
    unittest.main()
