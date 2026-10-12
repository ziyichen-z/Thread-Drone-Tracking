"""Local operator page for P1-ENG-LOOP-001 stage-B Plays (operation sheet C, AC-18).

A browser front end for the reviewed operator CLI; it adds no perception, control,
model decision or automatic confirmation. The server listens on 127.0.0.1 only,
uses the Python standard library, and embeds its page (no download, no external
asset). It reads the session's bridge files and session directory, and every button
runs exactly one ``python -m controller.language_loop <action>`` of the capture
worktree (the same CLI as ``lc``); it never writes a bridge file, request or lock.

Contract points (proposal Pending rulings R-B5, AC-18):

* Legal actions only: the §3.4 state table with AC-17 修订1 (``backend_fatal``:
  stop and status only) decides which buttons exist; TERMINAL shows none.
* Identity binding: each button posts the view it was rendered with (session,
  state, reason, epoch, track, suspect, candidate result). The server re-reads the
  bridge and runs the CLI only if that view is still current, with the token taken
  from the posted view; an old page can never be re-bound to a newer token.
* Confirmation needs a preview bound to the candidate (``<frame_id>-<query_id>.png``
  in the session's ``previews/``, a PNG with a non-empty header), that the browser has
  actually displayed (the page posts the name of the image it loaded and decoded; the
  server refuses a confirm without it), fresh data and readable timing; otherwise the
  page says the candidate cannot be confirmed. The countdown is the earlier of query time +
  ``T_ret`` + ``T_conf`` (``query_unix_s``) and first presentation + ``T_conf``
  (``issued_unix_s`` of the result file, written just before the session starts its
  presentation clock), shown with the cumulative frame-difference gate
  ``latest − N ≤ K_ret + K_conf``. All come from session-written data, so polling,
  reloading or redrawing never renews them. The page's timing is a hint: when it
  runs out the confirm buttons are disabled, nothing is sent and no event is made;
  the session's own checkpoint stays final for every confirm that is sent.
* Alert previews keep the R3 F5 binding: a verify-raised alert is bound to
  ``verification.last_query_id`` of the first SUSPECTED state carrying the new
  ``suspect_id`` and shown only if that result's verdict matches the alert kind;
  every other verify is labelled by when it was queried: before the alert (reference
  only, e.g. the old verify under a ``tracker_failure`` alert) or after it.
* Freshness: the page keeps polling while a click waits for its receipt, shows when
  the data was last read and when the frame / published frame last moved, and marks
  stale or unreadable data; stale data disables confirmation.
* One click at a time; an identical click right after a completed one is refused.
  A CLI result without receipt (exit 5 or the outer timeout, "结果未知") is kept per
  ``request_id`` (several may be pending at once); nothing is resent automatically,
  the same action on the same view is refused while one of them is pending, and the
  operator's retry of a given entry reuses its ``request_id`` and token (AC-1 修订1).
  A receipt that arrives later is matched by ``request_id`` from the session journal
  and shown. The unknown state is recorded before the click is logged, and captured
  output is logged as text (the outer timeout hands it back as bytes). ``APPLIED`` is shown as "accepted",
  never as seeded or published.
* Every click, refusal and retry is appended to ``<opdir>/operator-web.jsonl`` with
  the bound view, argv, exit code, stdout, stderr and receipt.

Usage (operation sheet C §3; ``lc_web`` in P1-ENG-LOOP-001-operator.sh):
  <python> P1-ENG-LOOP-001-operator-web.py --runtime <repo>/runtime --session-id <S> \
      --session-dir <session root>/<S> --opdir <operator dir> --worktree <capture worktree> \
      --k-receipt <worktree>/docs/evidence/P1-ENG-LOOP-001-k-receipt.json [--port 8771] [--open]
"""
from __future__ import annotations

import argparse
import http.server
import json
import math
import re
import secrets
import struct
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from pathlib import Path
from typing import Any, Callable

HOST = "127.0.0.1"
DEFAULT_PORT = 8771
POLL_S = 0.1
DUPLICATE_WINDOW_S = 1.5
CLI_TIMEOUT_S = 30.0
PRESENTATION_SKEW_S = 1.0     # result issued in the future by more than this -> untrusted
STALE_S = 1.0                 # snapshot older than this (10 polls) -> stale, no confirmation
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
WARN_QUERIES = 36             # per-Play cap is 40 query rows
WARN_SIM_S = 280.0            # per-Play cap is 300 s simulation time
MAX_BODY = 4096
TRIGGER_VERDICT = {"lost": "none", "drift": "drift", "ambiguous": "ambiguous"}
TOKEN_FIELD = {"confirm": "result_id", "reject": "result_id", "confirm-lost": "suspect_id",
               "dismiss": "suspect_id", "release": "track_id"}
ACTIONS = ("ask", "confirm", "reject", "respecify", "verify", "confirm-lost", "dismiss",
           "release", "stop")
QUERY_SEQ = re.compile(r"-q(\d+)$")
PREVIEW_NAME = re.compile(r"^[0-9]+-[A-Za-z0-9._-]+\.png$")
VIEW_KEYS = ("session_id", "state", "reason", "epoch", "track_id", "suspect_id", "result_id")
SIDES = ("left", "right")


def legal_actions(state: dict | None, *, instruction_reusable: bool) -> list[str]:
    """Operator actions the §3.4 table accepts in ``state`` (AC-17 修订1 for backend_fatal)."""
    if not state:
        return []
    name, reason = state.get("state"), state.get("reason")
    if name == "TERMINAL":
        return []
    if name in {"LOST", "REINIT_REQUIRED"} and reason == "backend_fatal":
        return ["stop"]
    table = {
        "IDLE": ["ask", "respecify", "stop"] if instruction_reusable else ["ask", "stop"],
        "QUERYING": ["ask", "respecify", "stop"],
        "AWAITING_CONFIRMATION": ["confirm", "reject", "ask", "respecify", "stop"],
        "TRACKING": ["verify", "release", "stop"],
        "SUSPECTED": ["confirm-lost", "dismiss", "respecify", "verify", "stop"],
        "LOST": ["ask", "respecify", "stop"],
        "REINIT_REQUIRED": ["ask", "respecify", "stop"],
    }
    return list(table.get(name, []))


def load_receipt(path: Path) -> dict[str, float]:
    """The K receipt values the confirmation gates use (read, never hand-copied)."""
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    hz, k_ret, k_conf = float(document["hz"]), int(document["k_ret"]), int(document["k_conf"])
    t_conf = float(document["t_conf_s"])
    if not (hz > 0 and k_ret >= 0 and k_conf >= 0 and t_conf > 0):
        raise ValueError("K receipt values out of range")
    t_ret = k_ret / hz
    if "t_ret_s" in document and abs(float(document["t_ret_s"]) - t_ret) > 1e-9:
        raise ValueError("K receipt t_ret_s differs from k_ret/hz")
    return {"hz": hz, "k_ret": k_ret, "k_conf": k_conf, "t_ret_s": t_ret, "t_conf_s": t_conf}


def read_json(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def finite(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def png_ok(path: Path) -> bool:
    """A PNG signature and an IHDR with non-zero size (the browser still has to decode it)."""
    try:
        with Path(path).open("rb") as handle:
            head = handle.read(24)
    except OSError:
        return False
    if len(head) < 24 or head[:8] != PNG_SIGNATURE or head[12:16] != b"IHDR":
        return False
    width, height = struct.unpack(">II", head[16:24])
    return width > 0 and height > 0


class JsonlTail:
    """Incremental reader of an append-only JSONL file; an incomplete last line waits."""

    def __init__(self, path: Path):
        self.path, self.offset, self.partial = Path(path), 0, b""

    def read(self) -> list[dict]:
        try:
            with self.path.open("rb") as handle:
                handle.seek(self.offset)
                chunk = handle.read()
        except OSError:
            return []
        self.offset += len(chunk)
        lines = (self.partial + chunk).split(b"\n")
        self.partial = lines.pop()
        records = []
        for line in lines:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict):
                records.append(record)
        return records


class Monitor:
    """Read-only view of one session: bridge files, the session's results log, latest frame.

    ``poll`` is called by a background thread and before every action. It keeps the
    F5 alert binding and the first published frame of each track in memory.
    """

    def __init__(self, bridge, runtime: Path, session_id: str, session_dir: Path,
                 receipt: dict, *, clock: Callable[[], float] = time.time):
        self.bridge = bridge
        self.runtime = Path(runtime)
        self.session_id = session_id
        self.session_dir = Path(session_dir)
        self.previews = self.session_dir / "previews"
        self.receipt = receipt
        self.clock = clock
        self.lock = threading.Lock()
        self.alerts: dict[str, dict] = {}         # suspect_id -> {"kind", "query_id", "since_unix_s"}
        self.first_published: dict[str, int] = {}
        self.results: dict[str, dict] = {}        # query_id -> result record (results.jsonl)
        self.verify_order: list[str] = []
        self.receipts: dict[str, dict] = {}       # request_id -> journal receipt record
        self.designated = False
        self.max_seq = 0
        self.results_tail = JsonlTail(self.session_dir / "results.jsonl")
        self.journal_tail = JsonlTail(self.session_dir / "language-session.jsonl")
        self.frame_seen: tuple | None = None      # (latest frame id, first seen unix)
        self.published_seen: tuple | None = None  # ((track, last_published), first seen unix)
        self.poll_error: str | None = None
        self.snapshot: dict = {"session_id": session_id, "state": None, "legal": [], "view": None,
                               "note": "尚未读取", "polled_unix_s": None}

    # --- readers ------------------------------------------------------------------

    def _read_state(self):
        try:
            document = self.bridge.read_tracker_state(self.runtime)
        except self.bridge.LanguageBridgeError as error:
            return None, f"tracker_state 无法校验：{error}"
        state = (document or {}).get("tracker_state")
        if not isinstance(state, dict):
            return None, "等待会话写出 tracker_state"
        if state.get("session_id") != self.session_id:
            return None, f"tracker_state 不是本会话（{state.get('session_id')}）"
        return state, None

    def _read_result(self):
        """Latest result body and its envelope ``issued_unix_s`` from one validated read."""
        try:
            document = self.bridge.read_result(self.runtime)
        except (self.bridge.LanguageBridgeError, OSError, ValueError):
            return None, None
        body = (document or {}).get("result")
        if not isinstance(body, dict) or not str(body.get("query_id") or "").startswith(
                f"{self.session_id}-q"):
            return None, None
        issued = document.get("issued_unix_s")
        return body, (float(issued) if finite(issued) else None)

    def _read_logs(self) -> None:
        for record in self.journal_tail.read():
            receipt = record.get("receipt")
            if (record.get("kind") == "receipt" and record.get("session_id") == self.session_id
                    and isinstance(receipt, dict) and receipt.get("request_id")):
                # IGNORED_DUPLICATE only echoes a same-id retry: the original receipt stays the
                # answer for that request_id (R5@K1K3 F7 / note 1)
                if receipt.get("outcome") == "IGNORED_DUPLICATE" and receipt["request_id"] in self.receipts:
                    continue
                self.receipts[receipt["request_id"]] = {"receipt": receipt, "detail": record.get("detail"),
                                                        "at_unix_s": record.get("at_unix_s")}
        for record in self.results_tail.read():
            query_id = str(record.get("query_id") or "")
            if not query_id.startswith(f"{self.session_id}-q"):
                continue
            match = QUERY_SEQ.search(query_id)
            if match:
                self.max_seq = max(self.max_seq, int(match.group(1)))
            if record.get("purpose") == "designate":
                self.designated = True
            if record.get("purpose") == "verify" and isinstance(record.get("verify"), dict):
                self.results[query_id] = record
                self.verify_order.append(query_id)

    def _read_frames(self):
        """Latest frame id, its simulation time and its capture wall time (when the metadata has it)."""
        latest = read_json(self.runtime / "frames" / "latest.json")
        if not isinstance(latest, dict) or not isinstance(latest.get("frame_id"), int):
            return None, None, None
        metadata = read_json(self.runtime / "frames" / f"frame_{latest['frame_id']:010d}.json")
        metadata = metadata if isinstance(metadata, dict) else {}
        sim, captured = metadata.get("simulation_time_s"), metadata.get("capture_unix_s")
        return (latest["frame_id"], float(sim) if finite(sim) else None,
                float(captured) if finite(captured) else None)

    # --- building the snapshot ------------------------------------------------------

    def preview_name(self, record: dict | None) -> tuple[str | None, str | None]:
        """Preview file name if it is bound to this record's frame and query, else a reason."""
        if not record:
            return None, "无结果"
        path = record.get("preview_path")
        if not path:
            return None, "预览缺失（preview_path 为空）"
        expected = f"{record.get('frame_id')}-{record.get('query_id')}.png"
        candidate = Path(path)
        if candidate.name != expected:
            return None, f"预览与帧/查询不符（{candidate.name} ≠ {expected}）"
        try:
            if candidate.resolve().parent != self.previews.resolve() or not candidate.is_file():
                return None, "预览不在本会话 previews/ 或文件不存在"
        except OSError:
            return None, "预览无法读取"
        if not png_ok(candidate):
            return None, "预览文件不是可显示的 PNG（空、损坏或未写完）"
        return expected, None

    def _candidate(self, state: dict, result: dict | None, issued: float | None,
                   latest: int | None) -> dict:
        receipt = self.receipt
        block = {"result_id": None, "query_id": None, "frame_id": None, "candidates": [],
                 "status": None, "preview": None, "confirmable": False, "why_not": None,
                 "query_deadline_unix_s": None, "presented_deadline_unix_s": None,
                 "frames_delta": None, "frames_limit": receipt["k_ret"] + receipt["k_conf"],
                 "t_ret_s": receipt["t_ret_s"], "t_conf_s": receipt["t_conf_s"]}
        if (not result or result.get("purpose") != "designate"
                or result.get("status") not in {"unique", "ambiguous"}
                or result.get("epoch") != state.get("epoch") or not result.get("candidates")):
            block["why_not"] = "结果槽里还不是本次候选（等待刷新）"
            return block
        block.update(result_id=result["result_id"], query_id=result["query_id"],
                     frame_id=result.get("frame_id"), status=result["status"],
                     candidates=[{"index": c.get("index"), "xywh": c.get("bbox_xywh_norm"),
                                  "clipped": c.get("clipped")} for c in result["candidates"]])
        name, problem = self.preview_name(result)
        block["preview"] = name
        if problem:
            block["why_not"] = f"不可确认：{problem}"
            return block
        query_unix = result.get("query_unix_s")
        now = self.clock()
        if not (finite(query_unix) and finite(issued) and isinstance(block["frame_id"], int)
                and latest is not None):
            block["why_not"] = "不可确认：取不到查询时刻、结果呈现时刻或最新帧"
            return block
        if issued < query_unix or issued > now + PRESENTATION_SKEW_S:
            block["why_not"] = "不可确认：结果时刻与查询时刻/本机时钟不一致"
            return block
        block["query_deadline_unix_s"] = query_unix + receipt["t_ret_s"] + receipt["t_conf_s"]
        block["presented_deadline_unix_s"] = issued + receipt["t_conf_s"]
        block["frames_delta"] = latest - block["frame_id"]
        block["confirmable"] = True
        return block

    def _alert(self, state: dict) -> dict | None:
        if state.get("state") != "SUSPECTED" or not state.get("suspect_id"):
            return None
        suspect, kind = state["suspect_id"], state.get("suspect_kind")
        if suspect not in self.alerts:   # F5: bind at the first SUSPECTED state with this id
            trigger = None
            if kind in TRIGGER_VERDICT:
                trigger = (state.get("verification") or {}).get("last_query_id")
            since = state.get("since_unix_s")
            self.alerts[suspect] = {"kind": kind, "query_id": trigger,
                                    "since_unix_s": float(since) if finite(since) else self.clock()}
        bound = self.alerts[suspect]
        block = {"suspect_id": suspect, "kind": bound["kind"], "query_id": bound["query_id"],
                 "since_unix_s": bound["since_unix_s"], "preview": None, "frame_id": None,
                 "verdict": None, "message": None}
        if bound["kind"] not in TRIGGER_VERDICT:
            block["message"] = "无触发核验：先点「立即核验」，按告警后的那次核验判丢或解除"
            return block
        record = self.results.get(bound["query_id"])
        if record is None:
            block["message"] = f"等待触发核验 q={bound['query_id']} 的结果"
            return block
        verdict = (record.get("verify") or {}).get("verdict")
        block.update(frame_id=record.get("frame_id"), verdict=verdict)
        if verdict != TRIGGER_VERDICT[bound["kind"]]:
            block["message"] = (f"告警绑定不一致：q={bound['query_id']} verdict={verdict} 与 "
                                f"{bound['kind']} 不符，不显示；用 lc status 核对")
            return block
        name, problem = self.preview_name(record)
        block["preview"] = name
        block["message"] = problem
        return block

    def _verify_view(self, record: dict, alert: dict | None) -> dict:
        """One verify result for display, labelled by its relation to the current alert."""
        name, problem = self.preview_name(record)
        verify = record.get("verify") or {}
        query_id, queried = record.get("query_id"), record.get("query_unix_s")
        relation = None
        if alert:
            if alert.get("query_id") == query_id:
                relation = "trigger"
            elif finite(queried) and queried >= alert["since_unix_s"]:
                relation = "after_alert"
            else:
                relation = "before_alert"   # queried before the alert: reference only
        return {"query_id": query_id, "frame_id": record.get("frame_id"), "preview": name,
                "problem": problem, "verdict": verify.get("verdict"), "iou": verify.get("iou"),
                "inconclusive_reason": verify.get("inconclusive_reason"),
                "query_unix_s": queried if finite(queried) else None,
                "is_trigger": relation == "trigger", "relation": relation}

    def _latest_verify(self, state: dict, alert: dict | None, *, after_alert: bool = False) -> dict | None:
        segment = state.get("segment_index")
        for query_id in reversed(self.verify_order):
            record = self.results[query_id]
            if record.get("segment_index") != segment:
                continue
            view = self._verify_view(record, alert)
            if after_alert and view["relation"] != "after_alert":
                continue
            return view
        return None

    def poll(self) -> dict:
        state, note = self._read_state()
        result, issued = self._read_result()
        latest, sim, captured = self._read_frames()
        with self.lock:
            now = self.clock()
            self._read_logs()             # after the state: the trigger result is already logged
            if latest is not None and (self.frame_seen is None or self.frame_seen[0] != latest):
                self.frame_seen = (latest, now)
            snap = {"session_id": self.session_id, "polled_unix_s": now, "state": state,
                    "note": note, "legal": [], "view": None, "candidate": None, "alert": None,
                    "verify": None, "verify_after_alert": None, "verify_in_flight": None,
                    "frames": {"latest_frame_id": latest, "sim_t": sim, "capture_unix_s": captured,
                               "changed_unix_s": captured if captured is not None
                               else (self.frame_seen[1] if self.frame_seen else None),
                               "changed_from": "capture" if captured is not None else "first_seen"},
                    "queries": {"max_seq": self.max_seq, "warn": self.max_seq >= WARN_QUERIES},
                    "sim_warn": sim is not None and sim >= WARN_SIM_S, "published": None}
            if state is not None:
                snap["legal"] = legal_actions(state, instruction_reusable=self.designated)
                if state.get("state") == "AWAITING_CONFIRMATION":
                    snap["candidate"] = self._candidate(state, result, issued, latest)
                snap["alert"] = self._alert(state)
                if state.get("state") in {"TRACKING", "SUSPECTED"}:
                    snap["verify"] = self._latest_verify(state, snap["alert"])
                    if snap["alert"]:
                        snap["verify_after_alert"] = self._latest_verify(state, snap["alert"], after_alert=True)
                    snap["verify_in_flight"] = (state.get("verification") or {}).get("in_flight_query_id")
                track, published = state.get("track_id"), state.get("last_published_frame_id")
                if track and published is not None and track not in self.first_published:
                    self.first_published[track] = published
                if self.published_seen is None or self.published_seen[0] != (track, published):
                    self.published_seen = ((track, published), now)
                snap["published"] = {"track_id": track, "last_published": published,
                                     "first_published": self.first_published.get(track),
                                     "changed_unix_s": self.published_seen[1]}
                candidate = snap["candidate"] or {}
                snap["view"] = {"session_id": self.session_id, "state": state.get("state"),
                                "reason": state.get("reason"), "epoch": state.get("epoch"),
                                "track_id": state.get("track_id"),
                                "suspect_id": state.get("suspect_id"),
                                "result_id": candidate.get("result_id")}
            self.poll_error = None
            self.snapshot = snap
            return snap

    def fail(self, error: Exception) -> None:
        """A poll failed: keep the last snapshot but mark it; confirmation is then disabled."""
        with self.lock:
            self.poll_error = f"{type(error).__name__}: {error}"
            self.snapshot = dict(self.snapshot, note=f"读取出错：{self.poll_error}")

    def public(self, now: float) -> dict:
        """The snapshot with the confirmation gates evaluated at ``now`` (never stored)."""
        with self.lock:
            snap = json.loads(json.dumps(self.snapshot))
            error = self.poll_error
        polled = snap.get("polled_unix_s")
        snap["age_s"] = None if polled is None else now - polled
        snap["stale"] = bool(error) or polled is None or now - polled > STALE_S
        snap["poll_error"] = error
        candidate = snap.get("candidate")
        if candidate and candidate.get("confirmable") and snap["stale"]:
            candidate["confirmable"] = False
            candidate["why_not"] = ("页面数据过期（读取出错或超过 1 s 未刷新）：不能用旧画面确认；"
                                    "等数据恢复，或用终端 lc 后备")
        if candidate and candidate.get("confirmable"):
            deadline = min(candidate["query_deadline_unix_s"], candidate["presented_deadline_unix_s"])
            candidate["remaining_s"] = deadline - now
            candidate["deadline_from"] = ("查询起" if candidate["query_deadline_unix_s"] <= candidate[
                "presented_deadline_unix_s"] else "结果出现起")
            late = candidate["frames_delta"]
            if late is None or late < 0 or late > candidate["frames_limit"]:
                candidate["confirmable"] = False
                candidate["why_not"] = (f"已过帧差门（{late}/{candidate['frames_limit']}）：会话会拒绝确认；"
                                        "可驳回或重新指定")
            elif deadline - now <= 0:
                candidate["confirmable"] = False
                candidate["why_not"] = "已过截止：会话会拒绝确认；可驳回或重新指定"
        snap["now_unix_s"] = now
        return snap


def compose_instruction(bridge, parts: dict) -> str:
    """Closed-grammar instruction text from the page's drop-downs (§3.7); raises ValueError."""
    color, klass = parts.get("color") or None, parts.get("class")
    side, reference = parts.get("side") or None, parts.get("ref") or None
    if klass not in bridge.INSTRUCTION_CLASSES:
        raise ValueError("类别不在闭集")
    if color is not None and color not in bridge.INSTRUCTION_COLORS:
        raise ValueError("颜色不在闭集")
    if side is not None:
        if color is not None or side not in SIDES or reference not in bridge.INSTRUCTION_CLASSES:
            raise ValueError("左右关系句只接受「类别 + 方向 + 参照类别」")
        text = f"the {klass} to the viewer's {side} of the {reference}"
    else:
        text = f"the {color} {klass}" if color else f"the {klass}"
    parsed = bridge.parse_instruction(text)    # raises InstructionUnsupported (a ValueError)
    return parsed.surface


class CliRunner:
    """Runs one operator CLI call of the capture worktree and returns its outcome."""

    def __init__(self, python: str, worktree: Path, runtime: Path, session_id: str):
        self.python, self.worktree = python, Path(worktree)
        self.runtime, self.session_id = Path(runtime), session_id

    def argv(self, action: str, request_id: str, *, token: str | None = None,
             index: int | None = None, instruction: str | None = None) -> list[str]:
        argv = [self.python, "-m", "controller.language_loop", action, "--session-id", self.session_id,
                "--runtime", str(self.runtime), "--allow-shared-runtime", "--request-id", request_id]
        if token is not None:
            argv += ["--token", token]
        if index is not None:
            argv.append(str(index))
        if instruction is not None:
            argv.append(instruction)
        return argv

    def __call__(self, argv: list[str]) -> dict:
        try:
            done = subprocess.run(argv, cwd=self.worktree, capture_output=True, text=True,
                                  timeout=CLI_TIMEOUT_S, check=False)
        except subprocess.TimeoutExpired as expired:
            # the partial output of a timed-out child is bytes even with text=True
            return {"exit": None, "timeout": True, "stdout": as_text(expired.stdout),
                    "stderr": as_text(expired.stderr)}
        return {"exit": done.returncode, "timeout": False, "stdout": as_text(done.stdout),
                "stderr": as_text(done.stderr)}


def as_text(value) -> str:
    """CLI output as text for the page and the click log (bytes decoded, None as empty)."""
    if value is None:
        return ""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    return str(value)


#: CLI exits that prove no request was written (language_loop.main: 2 = argument/guard refusal
#: before send_request, 4 = WRITER_BUSY); every other exit without a receipt leaves the result unknown
NOT_WRITTEN_EXITS = frozenset({2, 4})


def interpret(outcome: dict) -> tuple[dict | None, str]:
    """(receipt or None, one-line meaning) of a CLI outcome; never claims seeding/publishing."""
    if outcome.get("timeout"):
        return None, "CLI 超时被终止：结果未知，可能稍后执行；不会自动重发"
    code = outcome.get("exit")
    if code == 0:
        try:
            receipt = json.loads(outcome.get("stdout") or "").get("receipt")
        except (ValueError, AttributeError):
            receipt = None
        if isinstance(receipt, dict):
            meaning = {"APPLIED": "会话已受理（不等于播种或写出成功，看状态与 last_published）",
                       "REQUEST_INVALID": "会话拒绝：请求在当前状态/令牌下不合法，状态未变",
                       "PENDING_QUEUED": "已排队：在途查询结束后执行",
                       "SUPERSEDED": "已受理，但被后来的请求替换，不会执行",
                       "IGNORED_DUPLICATE": "同一 request_id 已处理过：本次不表示动作执行",
                       "IGNORED_TERMINAL": "会话已结束：未执行",
                       "IGNORED_FOREIGN_SESSION": "不是本会话的请求：未执行"}.get(
                receipt.get("outcome"), f"回执 {receipt.get('outcome')}")
            return receipt, meaning
        return None, "CLI 退出 0 但读不到回执：结果未知"
    if code == 5:
        return None, "结果未知，可能稍后执行（5 s 无回执）；不会自动重发"
    if code == 4:
        return None, "写者锁忙：另一个 CLI 正在写请求，本次未写入"
    if code == 2:
        return None, "CLI 拒绝（参数/指令/运行时守卫），未写请求"
    return None, f"CLI 退出码 {code}：结果未知（请求可能已写入），不会自动重发"


class App:
    def __init__(self, monitor: Monitor, runner: Callable[[list[str]], dict], argv_builder: CliRunner,
                 opdir: Path, bridge, *, clock: Callable[[], float] = time.time):
        self.monitor, self.runner, self.argv_builder = monitor, runner, argv_builder
        self.bridge, self.clock = bridge, clock
        self.opdir = Path(opdir)
        self.opdir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.opdir / "operator-web.jsonl"
        self.nonce = secrets.token_hex(16)
        self.busy = threading.Lock()
        self.last_done: tuple | None = None       # (click key, finished_at)
        self.last_click: dict | None = None
        # request_id -> {"request_id", "argv", "action", "view", ...}: every request whose result is
        # unknown, in click order; each keeps its own retry and late-receipt match (C3@K1K3 C3-2)
        self.unknowns: dict[str, dict] = {}
        # request_id -> the late-receipt message that resolved it (R5@K1K3 F7: a retry answered or
        # refused after its request was resolved says so instead of hiding that receipt)
        self.late_messages: dict[str, str] = {}
        self.pending_lock = threading.Lock()

    def log(self, **fields) -> None:
        record = dict(fields, at_unix_s=self.clock())
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, default=as_text) + "\n")

    def pending(self) -> list[dict]:
        with self.pending_lock:
            return [dict(entry) for entry in self.unknowns.values()]

    def resolve_late_receipts(self) -> None:
        """Unknown requests whose receipts later show up in the session journal, each by its id."""
        with self.pending_lock:
            waiting = list(self.unknowns)
        if not waiting:
            return
        with self.monitor.lock:
            found = {request_id: self.monitor.receipts.get(request_id) for request_id in waiting}
        for request_id, record in found.items():
            if not record:
                continue
            receipt, meaning = interpret({"exit": 0, "stdout": json.dumps({"receipt": record["receipt"]})})
            detail = f"（detail={record['detail']}）" if record.get("detail") else ""
            message = f"迟到回执（同一 request_id）：{meaning}{detail}"
            with self.pending_lock:
                pending = self.unknowns.pop(request_id, None)
                if pending is not None:
                    self.late_messages[request_id] = message
            if pending is None:
                continue
            self.last_click = {"ok": True, "action": pending["action"], "request_id": request_id,
                               "outcome": receipt.get("outcome"), "message": message, "stderr": ""}
            self.log(kind="late_receipt", action=pending["action"], request_id=request_id,
                     view=pending["view"], receipt=receipt, detail=record.get("detail"),
                     journal_at_unix_s=record.get("at_unix_s"))

    def state(self) -> dict:
        self.resolve_late_receipts()
        snap = self.monitor.public(self.clock())
        snap["busy"] = self.busy.locked()
        snap["last_click"] = self.last_click
        snap["unknowns"] = self.pending()
        snap["vocab"] = {"classes": list(self.bridge.INSTRUCTION_CLASSES),
                         "colors": list(self.bridge.INSTRUCTION_COLORS), "sides": list(SIDES)}
        return snap

    def refuse(self, reason: str, **fields) -> dict:
        self.log(kind="refused", reason=reason, **fields)
        self.last_click = {"ok": False, "action": fields.get("action"), "message": reason}
        return {"ok": False, "message": reason}

    def click(self, body: dict) -> dict:
        if not self.busy.acquire(blocking=False):
            return self.refuse("上一个点击仍在处理，本次未发送", action=body.get("action"))
        try:
            if body.get("retry_request_id"):
                return self._retry(body["retry_request_id"])
            return self._click(body)
        finally:
            self.busy.release()

    def _click(self, body: dict) -> dict:
        action, view = body.get("action"), body.get("view")
        if action not in ACTIONS or not isinstance(view, dict):
            return self.refuse("未知动作或缺少页面身份", action=action)
        index = body.get("index")
        instruction = None
        if action in {"ask", "respecify"} and body.get("instruction") is not None:
            try:
                instruction = compose_instruction(self.bridge, body["instruction"])
            except (ValueError, TypeError, AttributeError) as error:
                return self.refuse(f"指令不合文法：{error}", action=action)
        if action == "ask" and instruction is None:
            return self.refuse("指定需要一条指令", action=action)
        key = (action, index, instruction, json.dumps(view, sort_keys=True))
        if self.last_done and self.last_done[0] == key and self.clock() - self.last_done[1] < DUPLICATE_WINDOW_S:
            return self.refuse("重复点击：同一动作刚刚已发送", action=action, view=view)
        self.resolve_late_receipts()
        same = [entry for entry in self.pending() if entry["action"] == action
                and {k: entry["view"].get(k) for k in VIEW_KEYS} == {k: view.get(k) for k in VIEW_KEYS}]
        if same:
            return self.refuse("同一动作上次结果未知：请点该条的「用同一 request_id 重试」或等状态变化，"
                               "不要重新发起（会生成新请求）", action=action, view=view,
                               pending_request_id=same[0]["request_id"])
        try:
            current = self.monitor.poll()
        except Exception as error:  # an unreadable bridge must not be acted on
            self.monitor.fail(error)
            return self.refuse(f"读取会话状态失败，本次未发送：{type(error).__name__}: {error}",
                               action=action, view=view)
        now_view = current.get("view")
        if now_view is None or {k: view.get(k) for k in VIEW_KEYS} != now_view:
            return self.refuse("页面已过期：状态或令牌已变，请看新画面后再点", action=action,
                               view=view, current_view=now_view)
        if action not in current.get("legal", []):
            return self.refuse(f"{action} 在 {now_view['state']} 下不合法", action=action, view=view)
        token = view.get(TOKEN_FIELD[action]) if action in TOKEN_FIELD else None
        if action in TOKEN_FIELD and not token:
            return self.refuse("缺少令牌", action=action, view=view)
        if action == "confirm":
            gates = self.monitor.public(self.clock()).get("candidate") or {}
            count = len(gates.get("candidates") or [])
            if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < count:
                return self.refuse("候选编号不在本次候选内", action=action, view=view, index=index)
            if not gates.get("confirmable"):
                return self.refuse(gates.get("why_not") or "不可确认", action=action, view=view)
            if body.get("preview_seen") != gates.get("preview"):
                return self.refuse("页面尚未显示这次候选的预览（加载中、失败或已换候选），不能确认",
                                   action=action, view=view, preview_seen=body.get("preview_seen"))
        else:
            index = None
        request_id = f"{self.monitor.session_id}-web-{uuid.uuid4().hex[:8]}"
        argv = self.argv_builder.argv(action, request_id, token=token, index=index,
                                      instruction=instruction)
        return self._run(action=action, view=view, argv=argv, request_id=request_id, key=key,
                         index=index, instruction=instruction, kind="click")

    def _retry(self, request_id: str) -> dict:
        # read the session journal first: a receipt that already arrived answers the request,
        # and the retry is not sent (R5@K1K3 note 1)
        try:
            self.monitor.poll()
        except Exception as error:  # an unreadable bridge must not be acted on
            self.monitor.fail(error)
            return self.refuse(f"读取会话状态失败，本次未重试：{type(error).__name__}: {error}",
                               action="retry", request_id=request_id)
        self.resolve_late_receipts()
        with self.pending_lock:
            pending = dict(self.unknowns[request_id]) if request_id in self.unknowns else None
            late = self.late_messages.get(request_id)
        if pending is None:
            if late is not None:
                return self.refuse(f"不再重试，原请求已有回执——{late}", action="retry", request_id=request_id)
            return self.refuse("没有这个结果未知的请求可重试", action="retry", request_id=request_id)
        reply = self._run(action=pending["action"], view=pending["view"], argv=pending["argv"],
                          request_id=request_id, key=None, index=pending.get("index"),
                          instruction=pending.get("instruction"), kind="retry_same_request_id")
        if (reply.get("receipt") or {}).get("outcome") == "IGNORED_DUPLICATE":
            # the session consumed the original just before this retry: its own receipt is in the
            # journal already (written before the duplicate's), so show that one
            try:
                self.monitor.poll()
            except Exception as error:  # the entry stays; the background poll resolves it later
                self.monitor.fail(error)
            self.resolve_late_receipts()
            with self.pending_lock:
                late = self.late_messages.get(request_id)
            if late is not None:
                reply = dict(reply, message=f"{reply['message']}；{late}")
        return reply

    def _run(self, *, action, view, argv, request_id, key, index, instruction, kind) -> dict:
        started = self.clock()
        outcome = self.runner(argv)
        stdout, stderr = as_text(outcome.get("stdout")), as_text(outcome.get("stderr"))
        receipt, meaning = interpret(dict(outcome, stdout=stdout, stderr=stderr))
        finished = self.clock()
        # record the unknown state first, so a later logging problem can never lose it (C3-3)
        with self.pending_lock:
            if kind == "retry_same_request_id":
                # a same-id retry never forgets the original (R5@K1K3 F7): only a receipt that answers
                # the request removes it. WRITER_BUSY and every other exit wrote nothing new, a timeout
                # is unknown again, IGNORED_DUPLICATE means the original was consumed and its own
                # receipt comes from the journal. A retry never re-adds an entry resolved meanwhile.
                entry = self.unknowns.get(request_id)
                if receipt is not None and receipt.get("outcome") != "IGNORED_DUPLICATE":
                    self.unknowns.pop(request_id, None)
                elif entry is not None:
                    entry["last_retry"] = {"exit": outcome.get("exit"), "timeout": bool(outcome.get("timeout")),
                                           "message": meaning, "at_unix_s": finished}
                    if receipt is None:
                        meaning = f"{meaning}；原请求结果仍未知，保留在「结果未知」框"
                elif request_id in self.late_messages:     # resolved by its late receipt while this ran
                    meaning = f"{meaning}；原请求已有回执——{self.late_messages[request_id]}"
            elif receipt is None and outcome.get("exit") not in NOT_WRITTEN_EXITS:
                # without a receipt only 2 (refused before writing) and 4 (WRITER_BUSY) prove that
                # nothing was written; 0/5, a timeout and any unexpected exit are unknown (user, R5 F7 rework)
                self.unknowns[request_id] = {"request_id": request_id, "argv": argv, "action": action,
                                             "view": view, "index": index, "instruction": instruction,
                                             "since_unix_s": finished}
        self.log(kind=kind, action=action, view=view, index=index, instruction=instruction,
                 request_id=request_id, argv=argv, exit_code=outcome.get("exit"),
                 timeout=outcome.get("timeout"), stdout=stdout, stderr=stderr, receipt=receipt,
                 meaning=meaning, started_unix_s=started)
        if key is not None:
            self.last_done = (key, finished)
        label = action + (f" {index}" if index is not None else "") + (f" “{instruction}”" if instruction else "")
        self.last_click = {"ok": receipt is not None, "action": label, "request_id": request_id,
                           "outcome": (receipt or {}).get("outcome"), "message": meaning,
                           "stderr": stderr.strip()[-400:]}
        print(f"{time.strftime('%H:%M:%S')} {kind} {label} request_id={request_id} "
              f"exit={outcome.get('exit')} outcome={(receipt or {}).get('outcome')} — {meaning}",
              flush=True)
        return {"ok": receipt is not None, "message": meaning, "receipt": receipt,
                "request_id": request_id}


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "loop-operator/1"

    def log_message(self, format, *args):  # noqa: A002 - keep the terminal for click lines
        return

    @property
    def app(self) -> App:
        return self.server.app

    def _host_ok(self) -> bool:
        port = self.server.server_address[1]
        return self.headers.get("Host") in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: dict) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self):  # noqa: N802
        if not self._host_ok():
            return self._send(403, b"forbidden", "text/plain")
        if self.path == "/":
            page = PAGE.replace("__NONCE__", self.app.nonce).replace(
                "__SESSION__", self.app.monitor.session_id)
            return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        if self.path == "/api/state":
            return self._json(200, self.app.state())
        if self.path.startswith("/preview/"):
            name = self.path[len("/preview/"):]
            if not PREVIEW_NAME.match(name):
                return self._send(404, b"not found", "text/plain")
            path = self.app.monitor.previews / name
            try:
                data = path.read_bytes()
            except OSError:
                return self._send(404, b"not found", "text/plain")
            return self._send(200, data, "image/png")
        return self._send(404, b"not found", "text/plain")

    def do_POST(self):  # noqa: N802
        port = self.server.server_address[1]
        origin = self.headers.get("Origin")
        if (not self._host_ok() or self.path != "/api/action"
                or self.headers.get("X-Operator-Nonce") != self.app.nonce
                or (origin is not None and origin not in {f"http://127.0.0.1:{port}",
                                                          f"http://localhost:{port}"})):
            return self._send(403, b"forbidden", "text/plain")
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            return self._send(400, b"bad request", "text/plain")
        try:
            body = json.loads(self.rfile.read(length))
        except ValueError:
            return self._send(400, b"bad request", "text/plain")
        if not isinstance(body, dict):
            return self._send(400, b"bad request", "text/plain")
        return self._json(200, self.app.click(body))


def build_server(app: App, port: int) -> http.server.ThreadingHTTPServer:
    server = http.server.ThreadingHTTPServer((HOST, port), Handler)
    server.daemon_threads = True
    server.app = app
    return server


def poll_forever(monitor: Monitor, stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            monitor.poll()
        except Exception as error:  # keep polling; the page marks the data stale
            monitor.fail(error)
        stop.wait(POLL_S)


def load_bridge(worktree: Path):
    sys.path.insert(0, str(Path(worktree).resolve()))
    from controller import language_bridge
    return language_bridge


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--session-dir", required=True)
    parser.add_argument("--opdir", required=True)
    parser.add_argument("--worktree", required=True, help="capture worktree whose CLI every button runs")
    parser.add_argument("--k-receipt", required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--open", action="store_true", help="open the page in the default browser")
    arguments = parser.parse_args(argv)
    bridge = load_bridge(Path(arguments.worktree))
    receipt = load_receipt(Path(arguments.k_receipt))
    monitor = Monitor(bridge, Path(arguments.runtime), arguments.session_id,
                      Path(arguments.session_dir), receipt)
    builder = CliRunner(arguments.python, Path(arguments.worktree), Path(arguments.runtime),
                        arguments.session_id)
    app = App(monitor, builder, builder, Path(arguments.opdir), bridge)
    try:
        server = build_server(app, arguments.port)
    except OSError as error:
        print(f"操作页无法监听 {HOST}:{arguments.port}：{error}（端口被占用？先停掉残留的操作页）",
              file=sys.stderr)
        return 2
    url = f"http://{HOST}:{server.server_address[1]}/"
    app.log(kind="server_start", url=url, session_id=arguments.session_id,
            runtime=arguments.runtime, session_dir=arguments.session_dir,
            worktree=str(Path(arguments.worktree).resolve()), k_receipt=arguments.k_receipt,
            receipt=receipt, python=arguments.python)
    stop = threading.Event()
    threading.Thread(target=poll_forever, args=(monitor, stop), daemon=True).start()
    print(f"operator page {url} session={arguments.session_id} (Ctrl-C to stop; lc stays as fallback)",
          flush=True)
    if arguments.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
        app.log(kind="server_stop")
    return 0


PAGE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>操作台 __SESSION__</title>
<style>
  :root { --bg:#f6f7f9; --panel:#fff; --ink:#1d2330; --muted:#667085; --line:#d9dde5;
          --go:#1f7a3d; --warn:#b54708; --bad:#b42318; --info:#1d4ed8; }
  * { box-sizing: border-box; }
  body { margin:0; font:15px/1.45 -apple-system, "PingFang SC", "Helvetica Neue", sans-serif;
         background:var(--bg); color:var(--ink); }
  header { display:flex; flex-wrap:wrap; gap:6px 14px; align-items:baseline; padding:8px 12px;
           background:var(--panel); border-bottom:1px solid var(--line); }
  header b { font-size:18px; }
  .pill { padding:1px 8px; border-radius:10px; font-weight:600; background:#eef1f6; }
  .s-TRACKING { background:#dcfce7; color:var(--go); } .s-SUSPECTED { background:#fee4e2; color:var(--bad); }
  .s-AWAITING_CONFIRMATION { background:#fef0c7; color:var(--warn); }
  .s-QUERYING { background:#dbeafe; color:var(--info); }
  .s-stale { background:#e4e7ec; color:var(--muted); text-decoration:line-through; }
  main { padding:10px 12px; display:grid; gap:10px; }
  main.stale .view { opacity:.45; }
  .banner { padding:8px 12px; background:#fee4e2; color:var(--bad); font-weight:600; border-bottom:1px solid var(--bad); }
  .view { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:8px; }
  .view img { display:block; max-width:100%; max-height:52vh; width:auto; height:auto; margin:0 auto;
              border-radius:4px; background:#000; }
  #second img { max-height:30vh; }
  .caption { color:var(--muted); font-size:13px; margin:4px 2px 0; }
  .empty { padding:40px 10px; text-align:center; color:var(--muted); }
  .count { font-size:28px; font-weight:700; font-variant-numeric:tabular-nums; }
  .count.low { color:var(--bad); } .gates { color:var(--muted); font-size:13px; }
  .alert { border-left:4px solid var(--bad); padding:6px 10px; background:#fff5f4; }
  .ref { border-left:4px solid var(--muted); padding:4px 8px; background:#f2f4f7; }
  .pending { border:2px solid var(--warn); background:#fffaeb; border-radius:8px; padding:8px 10px; margin-top:10px; }
  .note { color:var(--warn); } .muted { color:var(--muted); }
  .buttons { display:flex; flex-wrap:wrap; gap:8px; }
  button { font:inherit; font-weight:600; padding:10px 14px; border-radius:8px; border:1px solid var(--line);
           background:#fff; cursor:pointer; min-width:120px; }
  button.primary { background:var(--go); color:#fff; border-color:var(--go); }
  button.danger { background:#fff; color:var(--bad); border-color:var(--bad); }
  button.retry { background:var(--warn); color:#fff; border-color:var(--warn); }
  button.big { font-size:18px; padding:14px 20px; }
  button:disabled { opacity:.45; cursor:not-allowed; }
  select { font:inherit; padding:8px; border-radius:6px; border:1px solid var(--line); }
  .row { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
  .small { font-size:13px; }
  .result { font-size:14px; }
</style>
</head>
<body>
<div id="banner" class="banner" hidden></div>
<header>
  <b>操作台</b><span>会话 <code>__SESSION__</code></span>
  <span id="state" class="pill">—</span><span id="track" class="muted"></span>
  <span id="frames" class="muted"></span><span id="published" class="muted"></span>
  <span id="fresh" class="muted"></span>
</header>
<main id="main">
  <section class="view"><div id="picture" class="empty">等待会话…</div>
    <div id="caption" class="caption"></div></section>
  <section id="status" class="view"></section>
  <section class="view"><div id="buttons" class="buttons"></div>
    <div id="composer" class="row" style="margin-top:10px"></div>
    <div id="unknown"></div>
    <div id="sending" class="note small" hidden>请求在途：等待会话回执（最长约 5 s）。这期间不能发下一个请求，停止也要等它结束（终端 lc stop 同样要等写者锁）。</div>
    <div id="click" class="result caption"></div></section>
  <section id="second" class="view" hidden></section>
</main>
<script>
const NONCE = "__NONCE__";
let snap = null, rendered = null, sending = false, fetching = false, composerBuilt = false;
let lastOkAt = null, fetchFailed = false;
let shownPreview = null, previewProblem = null;   // candidate preview actually displayed by this page
let pictureKey = null;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const img = (name) => `<img alt="preview" src="/preview/${encodeURIComponent(name)}">`;
const ago = (unix, now) => unix == null || now == null ? "—" : `${Math.max(now - unix, 0).toFixed(1)} s 前`;

async function send(body, confirmText) {
  if (sending) return;
  if (confirmText && !window.confirm(confirmText)) return;
  sending = true; $("sending").hidden = false; paintButtons();
  $("click").textContent = "发送中…";
  try {
    const response = await fetch("/api/action", {method:"POST",
      headers:{"Content-Type":"application/json","X-Operator-Nonce":NONCE}, body:JSON.stringify(body)});
    const data = await response.json();
    $("click").textContent = (data.ok ? "✔ " : "✖ ") + data.message + (data.request_id ? `（request_id=${data.request_id}）` : "");
  } catch (error) { $("click").textContent = "✖ 页面与本机服务断开：" + error + "（结果未知；用终端 lc status 核对）"; }
  sending = false; $("sending").hidden = true; rendered = null; await refresh();
}

function act(action, extra) { return () => send(Object.assign({action, view: rendered.view}, extra || {}),
  action === "stop" ? "确定停止本会话？停止后本次 Play 不能再指定。" :
  action === "release" ? "确定释放当前跟踪（段结束，进入 LOST）？" : null); }

function buildComposer(vocab) {
  const opt = (values, blank) => (blank ? `<option value="">${blank}</option>` : "") +
    values.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
  $("composer").innerHTML = `<span class="small muted">组合指令：</span>
    <select id="c-color">${opt(vocab.colors, "（无颜色）")}</select>
    <select id="c-class">${opt(vocab.classes)}</select>
    <select id="c-side"><option value="">（无左右关系）</option>${vocab.sides.map((v) =>
      `<option value="${esc(v)}">to the viewer's ${esc(v)} of</option>`).join("")}</select>
    <select id="c-ref">${opt(vocab.classes)}</select>
    <span id="c-text" class="small"></span>
    <button id="c-send">发送组合指令</button>`;
  const sync = () => {
    const side = $("c-side").value;
    $("c-color").disabled = !!side; $("c-ref").disabled = !side;
    if (side) $("c-color").value = "";
    const color = $("c-color").value, klass = $("c-class").value;
    $("c-text").textContent = side ? `the ${klass} to the viewer's ${side} of the ${$("c-ref").value}`
      : (color ? `the ${color} ${klass}` : `the ${klass}`);
  };
  ["c-color","c-class","c-side","c-ref"].forEach((id) => $(id).addEventListener("change", sync));
  $("c-send").addEventListener("click", () => { if (!$("c-send").dataset.action) return;
    send({action: $("c-send").dataset.action, view: rendered.view, instruction: {
      color: $("c-color").value || null, class: $("c-class").value,
      side: $("c-side").value || null, ref: $("c-side").value ? $("c-ref").value : null}}); });
  sync(); composerBuilt = true;
}

function unknownBlocks(action) {
  const current = JSON.stringify(rendered && rendered.view);
  return ((snap && snap.unknowns) || []).some((u) => u.action === action && JSON.stringify(u.view) === current);
}

function confirmReady() {
  const cand = snap && snap.candidate;
  return !!cand && cand.confirmable && !snap.stale && !fetchFailed && shownPreview === cand.preview;
}

function buttonSpecs(s) {
  const legal = new Set(s.legal || []), specs = [], cand = s.candidate;
  if (legal.has("confirm") && cand) for (const c of cand.candidates)
    specs.push({label:`确认候选 ${c.index}`, cls:"primary big", kind:"confirm", action:"confirm",
                on:() => send({action:"confirm", view:rendered.view, index:c.index, preview_seen:shownPreview})});
  if (legal.has("reject")) specs.push({label:"驳回候选", action:"reject", on:act("reject")});
  if (legal.has("confirm-lost")) specs.push({label:"判丢（目标已丢）", cls:"primary big", action:"confirm-lost", on:act("confirm-lost")});
  if (legal.has("dismiss")) specs.push({label:"解除疑似（误报）", cls:"big", action:"dismiss", on:act("dismiss")});
  const idle = ["IDLE", "LOST", "REINIT_REQUIRED"].includes(s.state && s.state.state);
  if (legal.has("ask")) specs.push({label:"指定：the red car", cls: idle ? "primary big" : "", action:"ask",
    on:() => send({action:"ask", view:rendered.view, instruction:{color:"red", class:"car"}})});
  if (legal.has("respecify")) specs.push({label:"重新指定（沿用上次指令）", action:"respecify", on:act("respecify")});
  if (legal.has("verify")) specs.push({label:"立即核验", action:"verify", on:act("verify")});
  if (legal.has("release")) specs.push({label:"释放跟踪…", cls:"danger", action:"release", on:act("release")});
  if (legal.has("stop")) specs.push({label:"停止会话…", cls:"danger", action:"stop", on:act("stop")});
  return specs;
}

function paintButtons() {
  const dead = sending || fetchFailed;
  $("buttons").querySelectorAll("button").forEach((b) => {
    const blocked = unknownBlocks(b.dataset.action);
    b.disabled = dead || blocked || (b.dataset.kind === "confirm" && !confirmReady());
    b.textContent = b.dataset.label + (blocked ? "（结果未知）" : "");
  });
  const c = $("c-send"); if (c) c.disabled = dead || !c.dataset.action || unknownBlocks("ask");
  $("unknown").querySelectorAll("button.retry").forEach((r) => { r.disabled = dead; });
}

function verifyLabel(v) {
  return {trigger:"告警触发核验", after_alert:"告警后核验（不是触发帧）",
          before_alert:"告警前参考（告警前发起的旧核验，不是本次检查）"}[v.relation] || "最近核验";
}

function statusHtml(s) {
  const st = s.state, cand = s.candidate;
  if (!st) return `<span class="note">${esc(s.note || "等待会话")}</span>`;
  let html = "";
  if (cand) {
    const ready = confirmReady();
    if (cand.confirmable && cand.remaining_s != null && shownPreview === cand.preview)
      html = `<div class="count ${cand.remaining_s < 3 ? "low" : ""}">剩余 ${Math.max(cand.remaining_s, 0).toFixed(1)} s</div>`;
    else html = `<div class="count low">不可确认</div>`;
    let why = cand.why_not;
    if (!why && s.stale) why = "页面数据过期：不能确认";
    if (!why && shownPreview !== cand.preview)
      why = previewProblem ? `预览没有显示成功（${previewProblem}）：不能确认；可驳回或重新指定` : "预览加载中：显示成功后才能确认";
    html += `<div class="gates">截止取先到者：结果出现起 ≤${cand.t_conf_s} s、查询起 ≤${(cand.t_ret_s + cand.t_conf_s).toFixed(0)} s` +
      (cand.deadline_from ? `（当前由${cand.deadline_from}决定）` : "") +
      ` · 帧差 ${cand.frames_delta ?? "—"}/${cand.frames_limit}（三门同时满足；页面计时只是提示，会话检查为准）</div>` +
      (!ready && why ? `<div class="note">${esc(why)}</div>` : "") +
      `<div class="small muted">${esc(cand.status)} · q=${esc(cand.query_id)} · frame ${esc(cand.frame_id)} · ${cand.candidates.length} 个候选</div>`;
  } else if (s.alert) {
    const a = s.alert;
    html = `<div class="alert"><b>疑似（${esc(a.kind)}）</b> ${esc(a.suspect_id)} · 告警于 ${ago(a.since_unix_s, s.now_unix_s)}` +
      (a.query_id ? ` · 触发核验 q=${esc(a.query_id)} frame ${esc(a.frame_id)} verdict=${esc(a.verdict)}` : "") +
      (a.message ? `<div class="note">${esc(a.message)}</div>` : "") + `</div>`;
  } else if (st.state === "TRACKING") html = `跟踪中 · 发布 ${st.publishing ? "开" : "关"}`;
  else if (st.state === "QUERYING") html = "查询中：等模型返回候选…";
  else html = st.state === "TERMINAL" ? "会话已结束" : `${esc(st.state)}`;
  if (s.verify_in_flight) html += `<div class="small muted">核验进行中 q=${esc(s.verify_in_flight)}</div>`;
  if (s.last_click) html += `<div class="small muted">上次点击：${esc(s.last_click.action)} → ${esc(s.last_click.outcome || "")} ${esc(s.last_click.message)}</div>`;
  return html;
}

function pictureFor(s) {
  // candidate preview; else the alert's evidence; else the latest verify of the segment
  const cand = s.candidate, a = s.alert, after = s.verify_after_alert, latest = s.verify;
  if (cand) return cand.preview ? {name: cand.preview, candidate: true,
    caption: `候选预览 · frame ${cand.frame_id} · q=${cand.query_id}（框上的编号 = 按钮编号）`} : {text: cand.why_not || "等待预览"};
  if (a && a.preview) return {name: a.preview, caption: `告警触发核验 q=${a.query_id} · frame ${a.frame_id}（绿=跟踪框，红=VLM 框）`};
  if (a && !a.query_id) return after && after.preview
    ? {name: after.preview, caption: `本次告警后核验 q=${after.query_id} · frame ${after.frame_id} · ${after.verdict}（按此判断）`}
    : {text: "等待本次告警后的核验：先点「立即核验」。下方的旧核验只是告警前参考。"};
  if (a) return {text: a.message || "等待触发核验"};
  if (latest && latest.preview) return {name: latest.preview, caption: `最近核验 q=${latest.query_id} · frame ${latest.frame_id} · ${latest.verdict}`};
  return {text: "（当前没有要看的预览）"};
}

function secondFor(s, main) {
  // under an alert, the latest verify when the main picture is not it, labelled by when it was queried
  const v = s.alert && s.verify;
  if (!v || !v.preview || v.preview === main) return "";
  const cls = v.relation === "before_alert" ? "ref" : "";
  return `<div class="caption ${cls}"><b>${verifyLabel(v)}</b> q=${esc(v.query_id)} · frame ${esc(v.frame_id)} · ${esc(v.verdict)} · 发起于 ${ago(v.query_unix_s, s.now_unix_s)}</div>` + img(v.preview);
}

function render(s) {
  const st = s.state;
  $("main").className = (fetchFailed || s.stale) ? "stale" : "";
  const banner = fetchFailed ? `本机服务未响应（最后成功读取 ${lastOkAt ? ((Date.now() - lastOkAt) / 1000).toFixed(1) + " s 前" : "—"}）：下面是旧数据，按钮已停用；用终端 lc 后备`
    : (s.stale ? `页面数据过期：${esc(s.poll_error || ("最后读取 " + (s.age_s != null ? s.age_s.toFixed(1) + " s 前" : "—")))}；确认已停用` : "");
  $("banner").hidden = !banner; $("banner").textContent = banner;
  $("state").textContent = st ? st.state + (st.reason ? `（${st.reason}）` : "") + (st.suspect_kind ? ` ${st.suspect_kind}` : "") : "未连接";
  $("state").className = "pill" + (fetchFailed || s.stale ? " s-stale" : (st ? " s-" + st.state : ""));
  $("track").textContent = st && st.track_id ? `track ${st.track_id}` : "";
  const f = s.frames || {};
  const frameAge = f.changed_unix_s != null && s.now_unix_s != null ? s.now_unix_s - f.changed_unix_s : null;
  $("frames").innerHTML = `帧 ${f.latest_frame_id ?? "—"}（${f.changed_from === "capture" ? "采集于 " : "本页首见 "}${ago(f.changed_unix_s, s.now_unix_s)}）` +
    (frameAge != null && frameAge > 3 ? ' <b class="note">帧未前进 &gt;3 s</b>' : "") + ` · sim_t ${f.sim_t != null ? f.sim_t.toFixed(1) + " s" : "—"}` +
    (s.sim_warn ? ' <b class="note">≥280 s：准备停止</b>' : "") + ` · 查询序号 ${s.queries ? s.queries.max_seq : 0}` +
    (s.queries && s.queries.warn ? ' <b class="note">≥36：准备停止</b>' : "");
  const p = s.published;
  $("published").innerHTML = p && p.track_id ? (p.first_published != null
    ? `已写出观测：本段首见 frame ${p.first_published} · last_published ${p.last_published}（本页见其 ${ago(p.changed_unix_s, s.now_unix_s)}变化）`
    : "本段尚未写出观测（播种瞬间为空属正常）") : "";
  $("fresh").textContent = fetchFailed
    ? `读取失败（最后成功 ${lastOkAt ? ((Date.now() - lastOkAt) / 1000).toFixed(1) + " s 前" : "—"}）`
    : `读取 ${s.age_s != null ? s.age_s.toFixed(1) + " s 前" : "—"}`;
  $("status").innerHTML = statusHtml(s);
  const main = pictureFor(s);
  const key = JSON.stringify([s.view, s.legal, main.name || main.text, s.alert && s.alert.query_id,
    s.verify && s.verify.query_id, s.verify_after_alert && s.verify_after_alert.query_id,
    (s.unknowns || []).map((u) => u.request_id + ":" + (u.last_retry ? u.last_retry.at_unix_s : "")).join(",")]);
  if (key === rendered?.key) { paintButtons(); return; }
  rendered = {key, view: s.view};
  // picture: rebuilt only when what it shows changes; the candidate image gates confirmation
  $("caption").textContent = main.caption || "";
  const nextPicture = JSON.stringify([main.name || null, main.text || null, !!main.candidate]);
  const picture = nextPicture === pictureKey ? null : document.createElement("div");
  if (picture) {
    pictureKey = nextPicture; shownPreview = null; previewProblem = null;
    $("picture").className = main.name ? "" : "empty";
    $("picture").innerHTML = main.name ? img(main.name) : esc(main.text);
  }
  const image = picture && $("picture").querySelector("img");
  if (image && main.candidate) {
    const name = main.name;
    image.addEventListener("load", () => {
      if (image.naturalWidth > 0 && snap && snap.candidate && snap.candidate.preview === name) shownPreview = name;
      else previewProblem = "图片为空或已换候选";
      $("status").innerHTML = statusHtml(snap); paintButtons();
    });
    image.addEventListener("error", () => { previewProblem = "加载或解码失败"; $("status").innerHTML = statusHtml(snap); paintButtons(); });
  }
  const second = secondFor(s, main.name);
  $("second").hidden = !second; $("second").innerHTML = second;
  const box = $("buttons"); box.innerHTML = "";
  for (const spec of buttonSpecs(s)) {
    const b = document.createElement("button");
    b.dataset.label = spec.label; b.textContent = spec.label; b.className = spec.cls || "";
    b.dataset.kind = spec.kind || ""; b.dataset.action = spec.action;
    b.addEventListener("click", spec.on); box.appendChild(b);
  }
  $("unknown").innerHTML = (s.unknowns || []).map((u) => `<div class="pending"><b>结果未知：${esc(u.action)}</b>（request_id=${esc(u.request_id)}，${ago(u.since_unix_s, s.now_unix_s)}）<br>
    ${u.last_retry ? `上次重试：${esc(u.last_retry.message)}（${ago(u.last_retry.at_unix_s, s.now_unix_s)}）<br>` : ""}
    会话可能稍后执行它，也可能没收到。<b>不要再点原按钮</b>（会生成新请求）；先看状态有没有变化，确需重试请点：
    <button class="retry" data-request-id="${esc(u.request_id)}">用同一 request_id 重试</button></div>`).join("");
  $("unknown").querySelectorAll("button.retry").forEach((r) =>
    r.addEventListener("click", () => send({retry_request_id: r.dataset.requestId})));
  if (!composerBuilt && s.vocab) buildComposer(s.vocab);
  const legal = new Set(s.legal || []);
  $("c-send").dataset.action = legal.has("ask") ? "ask" : "";
  $("composer").style.display = legal.has("ask") ? "" : "none";
  paintButtons();
}

async function refresh() {
  if (fetching) return;
  fetching = true;
  try {
    const response = await fetch("/api/state", {cache:"no-store"});
    if (!response.ok) throw new Error("HTTP " + response.status);
    snap = await response.json(); lastOkAt = Date.now(); fetchFailed = false; render(snap);
  } catch (error) {
    fetchFailed = true;
    if (snap) render(snap); else { $("banner").hidden = false; $("banner").textContent = "本机服务未响应：用终端 lc 后备"; }
  }
  fetching = false;
}
setInterval(refresh, 300);   // keeps refreshing while a click waits for its receipt
refresh();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
