"""Local operator page for P1-ENG-ACQ-001 Play D1 (proposal「Play D1 本地操作页窄范围代码批次 CLARIFY」, AC-22…24).

Adapted from the reviewed ``docs/evidence/P1-ENG-LOOP-001-operator-web.py`` (left unchanged). It is a
browser front end for the ``controller.language_loop`` operator CLI and adds no perception, control,
model decision or automatic action. The server listens on 127.0.0.1 only, uses the Python standard
library and embeds its page (no download, no external asset). It only reads the bridge files in
``runtime/`` and the session directory; every button runs exactly one
``<this interpreter> -m controller.language_loop <action>`` with this repository as working directory
(the same CLI as operation sheet §4 T3). It never writes a bridge file, request or lock, never
confirms, stops or resends on its own, and writes only its own log
``<play-root>/<SID>/operator/operator-web.jsonl``.

Contract points (CLARIFY, AC-22…24):

* Actions: the nine-state table of the CLARIFY decides which buttons exist (``legal_actions``).
  ``ACQUIRING`` offers only ``stop``; ``TRACK_ENDED`` is a ``designation.result`` (not a state) and
  its automatic path ``ACQUIRING → TRACKING / LOST(acquire_failed)`` is only displayed.
  ``respecify`` appears only once the session has an instruction to reuse. ``backend_fatal``: stop only.
* K receipt: the ``candidates`` receipt the session started with. The page parses it with the session's
  own ``KReceipt``, checks the identity (host ``mac`` / ``candidates`` / ``detector-tracks``), the §2.7
  report through the session's own ``validate_measurement_sources``, the effective R/hz, and that the
  receipt payload equals ``session_started.k_receipt`` in the session journal. Any problem disables
  confirmation and is shown; the timing values always come from this receipt, never from a constant.
* Confirmation: the earlier of query time + ``T_ret`` + ``T_conf`` and first presentation + ``T_conf``
  (both written by the session), together with ``latest − N ≤ k_ret + k_conf``. Polling, reloading or
  restarting never renews them; the page's timing is a hint and the session checkpoint stays final.
  A confirm needs the preview bound to this ``result_id`` (``<frame_id>-<query_id>.png`` in this
  session's ``previews/``, a PNG whose bytes the page names by SHA-256), actually decoded by the
  browser, a contiguous candidate index list and an index on it; the server re-reads state, preview
  and token and refuses any change. ``APPLIED`` means accepted only, never bound.
* Session number: a used SID (retired ``acq-d1-1``, a closed or re-started session directory, an archive
  of the same number, a directory without a live session of this number) refuses the start; a second
  ``session_started``, an archive or activity after the close record disables every action at once,
  including the Play mark (server refuses it too) and every same-request_id retry.
* Retry of an unknown result (C2@K1K3 C2-1): sent only while the current view (state, epoch, token
  fields), the nine-state table, the argv token and — for confirm — the gates on the same preview bytes
  still admit it (``App.retry_block``); otherwise nothing is sent, the entry stays for its late receipt
  and the page shows why.
* Play clock: only the operator's explicit mark (persisted in the operator log, first mark wins) starts
  it; the page shows elapsed / remaining of 180 s and a notice at the limit, and never stops the
  session. An unreadable log means manual timing and no remaining time is shown.
* Every click, refusal, unknown result, retry, timer mark/notice and CLI receipt is appended to the
  operator log with the bound view, argv and times; the session journal is never written.

Usage (operation sheet ``docs/evidence/P1-ENG-ACQ-001-play-d1.md`` §4, T4):
  $PY docs/evidence/P1-ENG-ACQ-001-operator-web.py --sid $SID [--port 8772] [--open]
"""
from __future__ import annotations

import argparse
import hashlib
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
import urllib.parse
import uuid
import webbrowser
from pathlib import Path
from typing import Any, Callable

HOST = "127.0.0.1"
DEFAULT_PORT = 8772
POLL_S = 0.1
DUPLICATE_WINDOW_S = 1.5
CLI_TIMEOUT_S = 30.0
PRESENTATION_SKEW_S = 1.0     # result issued in the future by more than this -> untrusted
STALE_S = 1.0                 # snapshot older than this (10 polls) -> stale, no confirmation
MARK_SKEW_S = 5.0             # persisted Play mark in the future by more than this -> unreliable
PLAY_LIMIT_S = 180.0          # Play D1: each formal attempt ≤ 3 min (operation sheet §1)
PLAY_WARN_S = 150.0
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BODY = 4096
REPO = Path(__file__).resolve().parents[2]
PLAY_ROOT = REPO / "outputs" / "eng-acq" / "P1-ENG-ACQ-001" / "play-d1"
RECEIPT_NAME = "candidates-k-receipt.json"
LOG_NAME = "operator-web.jsonl"
SID_FORMAT = re.compile(r"^acq-d1-[1-9][0-9]*$")
#: CLARIFY「登记外 Play 裁定」: acq-d1-1 carried attempt 1 and the void unreleased Play; never reused.
RETIRED_SIDS = frozenset({"acq-d1-1"})
RECEIPT_IDENTITY = {"host": "mac", "backend": "candidates", "model_form": "detector-tracks"}
TRIGGER_VERDICT = {"lost": "none", "drift": "drift", "ambiguous": "ambiguous"}
TOKEN_FIELD = {"confirm": "result_id", "reject": "result_id", "confirm-lost": "suspect_id",
               "dismiss": "suspect_id", "release": "track_id"}
ACTIONS = ("ask", "confirm", "reject", "respecify", "verify", "confirm-lost", "dismiss",
           "release", "stop")
#: CLARIFY table: actions per state before the conditional ``respecify`` (added only with an instruction).
STATE_ACTIONS = {
    "IDLE": ("ask", "stop"),
    "QUERYING": ("ask", "stop"),
    "AWAITING_CONFIRMATION": ("confirm", "reject", "ask", "stop"),
    "TRACKING": ("ask", "verify", "release", "stop"),
    "SUSPECTED": ("ask", "verify", "confirm-lost", "dismiss", "stop"),
    "ACQUIRING": ("stop",),
    "LOST": ("ask", "stop"),
    "REINIT_REQUIRED": ("ask", "stop"),
}
RESPECIFY_STATES = frozenset({"IDLE", "QUERYING", "AWAITING_CONFIRMATION", "TRACKING", "SUSPECTED",
                              "LOST", "REINIT_REQUIRED"})
#: a receipt for ask/respecify with one of these outcomes means the session took an instruction
#: (``LanguageSession._begin_designate`` sets it before any such receipt is written)
INSTRUCTION_OUTCOMES = frozenset({"APPLIED", "PENDING_QUEUED"})
QUERY_SEQ = re.compile(r"-q(\d+)$")
PREVIEW_NAME = re.compile(r"^[0-9]+-[A-Za-z0-9._-]+\.png$")
SHA_HEX = re.compile(r"^[0-9a-f]{64}$")
VIEW_KEYS = ("session_id", "state", "reason", "epoch", "track_id", "suspect_id", "result_id")
SIDES = ("left", "right")
QUICK_INSTRUCTION = {"color": None, "class": "car"}     # operation sheet §5: ask "the car"


def legal_actions(state: dict | None, *, instruction_reusable: bool) -> list[str]:
    """Operator actions of the CLARIFY table in ``state``; unknown and ``TERMINAL`` states get none."""
    if not state:
        return []
    name, reason = state.get("state"), state.get("reason")
    if name not in STATE_ACTIONS:
        return []
    if name in {"LOST", "REINIT_REQUIRED"} and reason == "backend_fatal":
        return ["stop"]
    actions = list(STATE_ACTIONS[name])
    if instruction_reusable and name in RESPECIFY_STATES:
        actions.insert(actions.index("stop"), "respecify")
    return actions


def read_json(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def finite(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def png_ok(data: bytes) -> bool:
    """A PNG signature and an IHDR with non-zero size (the browser still has to decode it)."""
    if len(data) < 24 or data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
        return False
    width, height = struct.unpack(">II", data[16:24])
    return width > 0 and height > 0


def read_journal(path: Path) -> list[dict] | None:
    """All complete records of a session journal; None when it cannot be read or a line is corrupt."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except OSError:
        return None
    lines = text.split("\n")
    lines.pop()                   # "" after the final newline, or a line still being written
    records = []
    for line in lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            return None
        if isinstance(record, dict):
            records.append(record)
    return records


def is_terminal_record(record: dict) -> bool:
    return record.get("kind") == "state" and record.get("state") == "TERMINAL"


def session_lock(runtime: Path, bridge) -> dict | None:
    document = read_json(Path(runtime) / bridge.SESSION_LOCK_FILE)
    return document if isinstance(document, dict) else None


def sid_usage(sid: str, session_dir: Path, archive_dir: Path, runtime: Path, bridge, *,
              is_alive: Callable[[int], bool] | None = None) -> str | None:
    """Why ``sid`` counts as used (the page then refuses to start), or None for a fresh or live session."""
    if sid in RETIRED_SIDS:
        return f"{sid} 已用于 attempt 1 与作废的登记外 Play"
    if Path(archive_dir).exists():
        return f"已有同号归档 {archive_dir}"
    session_dir = Path(session_dir)
    if not session_dir.exists():
        return None
    records = read_journal(session_dir / "language-session.jsonl")
    if records is None:
        return "会话目录已存在且会话日志无法完整读取"
    started = sum(1 for record in records if record.get("kind") == "session_started")
    if started == 0:
        return "会话目录已存在但日志里没有 session_started（中止的尝试也占号）"
    if started > 1:
        return f"会话日志已有 {started} 个 session_started"
    if any(is_terminal_record(record) for record in records):
        return "会话日志已有结束记录（TERMINAL）"
    lock = session_lock(runtime, bridge)
    alive = is_alive or bridge.default_is_alive
    pid = (lock or {}).get("pid")
    if (not lock or lock.get("session_id") != sid or not isinstance(pid, int) or isinstance(pid, bool)
            or pid <= 0 or not alive(pid)):
        return "会话目录已存在，但 runtime 里没有这个号的活会话（既往未正常结束的会话）"
    return None


class ReceiptCheck:
    """The session's ``candidates`` K receipt, checked with the session's own code on every poll."""

    def __init__(self, loop, receipt_path: Path, runtime: Path, *, machine: str | None = None):
        self.loop, self.path, self.runtime = loop, Path(receipt_path), Path(runtime)
        self.machine = machine

    def evaluate(self, session_started: dict | None, started_count: int) -> dict:
        loop, problems = self.loop, []
        values: dict[str, Any] = {"path": str(self.path)}
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
            receipt = loop.KReceipt.from_document(document)
        except (OSError, ValueError, loop.LanguageBridgeError) as error:
            return {"ok": False, "problems": [f"收据缺失或无效：{type(error).__name__}: {error}"],
                    "values": values}
        values.update(host=receipt.host, backend=receipt.backend, model_form=receipt.model_form,
                      hz=receipt.hz, retained_frame_count=receipt.retained_frame_count,
                      p95_s=receipt.p95_s, k_ret=receipt.k_ret, k_conf=receipt.k_conf,
                      t_ret_s=receipt.t_ret_s, t_conf_s=document.get("t_conf_s"))
        identity = {"host": receipt.host, "backend": receipt.backend, "model_form": receipt.model_form}
        if identity != RECEIPT_IDENTITY:
            problems.append(f"收据身份不是本项 candidates 单宿主：{identity}")
        if dict(receipt.model_identity) != dict(loop.CANDIDATES_IDENTITY):
            problems.append("收据 model_identity 不是 candidates 适配器身份")
        if not finite(document.get("t_conf_s")) or document["t_conf_s"] != loop.T_CONF_S:
            problems.append(f"收据 t_conf_s={document.get('t_conf_s')} 与会话 T_CONF_S={loop.T_CONF_S} 不符")
        if not finite(document.get("t_ret_s")) or abs(document["t_ret_s"] - receipt.t_ret_s) > 1e-9:
            problems.append("收据 t_ret_s 与 k_ret/hz 不符")
        try:
            report = loop.validate_measurement_sources(receipt, current_machine=self.machine)
            values["report_git_head"] = ((report or {}).get("environment") or {}).get("git_head")
            values["report_machine"] = (report or {}).get("machine_name")
        except (loop.LanguageBridgeError, OSError, ValueError, KeyError, TypeError) as error:
            problems.append(f"§2.7 报告缺失或与收据不符：{error}")
        try:
            scenario = loop.read_scenario(self.runtime)
            values["effective"] = {"hz": scenario["capture_hz"], "retained_frame_count": scenario["retained_frame_count"]}
            if (scenario["capture_hz"] != receipt.hz
                    or scenario["retained_frame_count"] != receipt.retained_frame_count):
                problems.append(f"生效配置 hz/R={scenario['capture_hz']}/{scenario['retained_frame_count']} "
                                f"与收据 {receipt.hz}/{receipt.retained_frame_count} 不符")
        except (OSError, ValueError, KeyError, TypeError) as error:
            problems.append(f"读不到生效场景配置：{error}")
        if started_count == 0 or session_started is None:
            problems.append("会话尚未写 session_started：收据还没和本次会话绑定")
        elif started_count > 1:
            problems.append("会话日志有多个 session_started")
        else:
            payload = json.loads(json.dumps(receipt.payload()))
            if session_started.get("k_receipt") != payload:
                problems.append("本次会话启动所用收据（session_started.k_receipt）与该收据文件不符")
            started_scenario = session_started.get("scenario") or {}
            if (started_scenario.get("capture_hz") != receipt.hz
                    or started_scenario.get("retained_frame_count") != receipt.retained_frame_count):
                problems.append("会话启动时的场景 hz/R 与收据不符")
        return {"ok": not problems, "problems": problems, "values": values}


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
    """Read-only view of one session: bridge files, the session's journal and results, latest frame."""

    def __init__(self, bridge, receipt_check: ReceiptCheck, runtime: Path, session_id: str,
                 session_dir: Path, archive_dir: Path, *, clock: Callable[[], float] = time.time):
        self.bridge, self.receipt_check = bridge, receipt_check
        self.runtime = Path(runtime)
        self.session_id = session_id
        self.session_dir = Path(session_dir)
        self.archive_dir = Path(archive_dir)
        self.previews = self.session_dir / "previews"
        self.clock = clock
        self.lock = threading.Lock()
        # R2@K1K3 K1K3-R2-1: polls (background, click, retry, Play mark) run one at a time, so the file
        # reads of a later poll never happen before those of an earlier one, and an older state read
        # can neither be judged after a newer journal read nor overwrite a newer snapshot.
        self.poll_lock = threading.Lock()
        self.alerts: dict[str, dict] = {}         # suspect_id -> {"kind", "query_id", "since_unix_s"}
        self.first_published: dict[str, int] = {}
        self.results: dict[str, dict] = {}        # query_id -> verify result record (results.jsonl)
        self.verify_order: list[str] = []
        self.receipts: dict[str, dict] = {}       # request_id -> journal receipt record
        self.instruction_known = False
        self.started_count = 0
        self.session_started: dict | None = None
        self.closed = False                       # a TERMINAL record was journaled
        self.closed_at: float | None = None       # at_unix_s of the first TERMINAL journal record
        self.terminal_state_seen = False          # a read of this session's tracker_state showed TERMINAL
        self.block: str | None = None             # sticky: SID reuse seen while running
        self.max_seq = 0
        self.results_tail = JsonlTail(self.session_dir / "results.jsonl")
        self.journal_tail = JsonlTail(self.session_dir / "language-session.jsonl")
        self.frame_seen: tuple | None = None
        self.published_seen: tuple | None = None
        self.poll_error: str | None = None
        self.snapshot: dict = {"session_id": session_id, "state": None, "legal": [], "view": None,
                               "note": "尚未读取", "polled_unix_s": None}

    # --- readers ------------------------------------------------------------------

    def _read_state(self):
        """(this session's tracker_state body, why it is missing, its envelope ``issued_unix_s``)."""
        try:
            document = self.bridge.read_tracker_state(self.runtime)
        except self.bridge.LanguageBridgeError as error:
            return None, f"tracker_state 无法校验：{error}", None
        state = (document or {}).get("tracker_state")
        if not isinstance(state, dict):
            return None, "等待会话写出 tracker_state", None
        if state.get("session_id") != self.session_id:
            return None, f"tracker_state 不是本会话（{state.get('session_id')}）", None
        issued = document.get("issued_unix_s")
        return state, None, (float(issued) if finite(issued) else None)

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
            if record.get("session_id") not in (None, self.session_id):
                continue
            kind = record.get("kind")
            if kind == "session_started":
                self.started_count += 1
                if self.session_started is None:
                    self.session_started = record
                if self.started_count > 1:
                    self.block = f"会话日志出现第 {self.started_count} 个 session_started：同号被复用"
                elif self.closed:
                    self.block = "会话结束后又出现 session_started：同号被复用"
            elif is_terminal_record(record):
                self.closed = True
                if self.closed_at is None and finite(record.get("at_unix_s")):
                    self.closed_at = float(record["at_unix_s"])
            receipt = record.get("receipt")
            if kind == "receipt" and isinstance(receipt, dict) and receipt.get("request_id"):
                if receipt.get("action") in {"ask", "respecify"} and receipt.get("outcome") in INSTRUCTION_OUTCOMES:
                    self.instruction_known = True
                # IGNORED_DUPLICATE only echoes a same-id retry: the original receipt stays the answer
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
            if record.get("purpose") == "verify" and isinstance(record.get("verify"), dict):
                self.results[query_id] = record
                self.verify_order.append(query_id)

    def _read_frames(self):
        latest = read_json(self.runtime / "frames" / "latest.json")
        if not isinstance(latest, dict) or not isinstance(latest.get("frame_id"), int):
            return None, None, None
        metadata = read_json(self.runtime / "frames" / f"frame_{latest['frame_id']:010d}.json")
        metadata = metadata if isinstance(metadata, dict) else {}
        sim, captured = metadata.get("simulation_time_s"), metadata.get("capture_unix_s")
        return (latest["frame_id"], float(sim) if finite(sim) else None,
                float(captured) if finite(captured) else None)

    # --- building the snapshot ------------------------------------------------------

    def preview_file(self, record: dict | None) -> tuple[str | None, str | None, str | None]:
        """(name, sha256, problem): the preview bound to this record's frame and query in this session."""
        if not record:
            return None, None, "无结果"
        path = record.get("preview_path")
        if not path:
            return None, None, "预览缺失（preview_path 为空）"
        expected = f"{record.get('frame_id')}-{record.get('query_id')}.png"
        candidate = Path(path)
        if candidate.name != expected:
            return None, None, f"预览与帧/查询不符（{candidate.name} ≠ {expected}）"
        try:
            if candidate.resolve().parent != self.previews.resolve() or not candidate.is_file():
                return None, None, "预览不在本会话 previews/ 或文件不存在"
            data = candidate.read_bytes()
        except OSError:
            return None, None, "预览无法读取"
        if not png_ok(data):
            return None, None, "预览文件不是可显示的 PNG（空、损坏或未写完）"
        return expected, hashlib.sha256(data).hexdigest(), None

    def _candidate(self, state: dict, result: dict | None, issued: float | None,
                   latest: int | None, receipt: dict) -> dict:
        values = receipt.get("values") or {}
        gates_known = receipt.get("ok")
        block = {"result_id": None, "query_id": None, "frame_id": None, "candidates": [],
                 "status": None, "preview": None, "preview_sha256": None, "confirmable": False,
                 "why_not": None, "query_deadline_unix_s": None, "presented_deadline_unix_s": None,
                 "frames_delta": None,
                 "frames_limit": values["k_ret"] + values["k_conf"] if gates_known else None,
                 "t_ret_s": values.get("t_ret_s") if gates_known else None,
                 "t_conf_s": values.get("t_conf_s") if gates_known else None}
        if (not result or result.get("purpose") != "designate"
                or result.get("status") not in {"unique", "ambiguous"}
                or result.get("epoch") != state.get("epoch") or not result.get("candidates")):
            block["why_not"] = "结果槽里还不是本次候选（等待刷新）"
            return block
        indexes = [c.get("index") for c in result["candidates"]]
        block.update(result_id=result["result_id"], query_id=result["query_id"],
                     frame_id=result.get("frame_id"), status=result["status"],
                     candidates=[{"index": c.get("index"), "xywh": c.get("bbox_xywh_norm"),
                                  "clipped": c.get("clipped")} for c in result["candidates"]])
        name, digest, problem = self.preview_file(result)
        block["preview"], block["preview_sha256"] = name, digest
        model = result.get("model") or {}
        if problem:
            block["why_not"] = f"不可确认：{problem}"
        elif indexes != list(range(len(indexes))):
            block["why_not"] = f"不可确认：候选 index 缺失或错位（{indexes}）"
        elif not gates_known:
            block["why_not"] = "不可确认：收据绑定未通过——" + "；".join(receipt.get("problems") or [])
        elif (model.get("backend"), model.get("model_form")) != ("candidates", "detector-tracks"):
            block["why_not"] = f"不可确认：结果不是 candidates 后端（{model.get('backend')}/{model.get('model_form')}）"
        elif result.get("k_ret") != values["k_ret"]:
            block["why_not"] = f"不可确认：结果 k_ret={result.get('k_ret')} 与收据 {values['k_ret']} 不符"
        if block["why_not"]:
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
        block["query_deadline_unix_s"] = query_unix + values["t_ret_s"] + values["t_conf_s"]
        block["presented_deadline_unix_s"] = issued + values["t_conf_s"]
        block["frames_delta"] = latest - block["frame_id"]
        block["confirmable"] = True
        return block

    def _alert(self, state: dict) -> dict | None:
        if state.get("state") != "SUSPECTED" or not state.get("suspect_id"):
            return None
        suspect, kind = state["suspect_id"], state.get("suspect_kind")
        if suspect not in self.alerts:   # bind at the first SUSPECTED state with this id (LOOP-001 R3 F5)
            trigger = None
            if kind in TRIGGER_VERDICT:
                trigger = (state.get("verification") or {}).get("last_query_id")
            since = state.get("since_unix_s")
            self.alerts[suspect] = {"kind": kind, "query_id": trigger,
                                    "since_unix_s": float(since) if finite(since) else self.clock()}
        bound = self.alerts[suspect]
        block = {"suspect_id": suspect, "kind": bound["kind"], "query_id": bound["query_id"],
                 "since_unix_s": bound["since_unix_s"], "preview": None, "preview_sha256": None,
                 "frame_id": None, "verdict": None, "message": None}
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
                                f"{bound['kind']} 不符，不显示；用终端 status 核对")
            return block
        name, digest, problem = self.preview_file(record)
        block.update(preview=name, preview_sha256=digest, message=problem)
        return block

    def _verify_view(self, record: dict, alert: dict | None) -> dict:
        name, digest, problem = self.preview_file(record)
        verify = record.get("verify") or {}
        query_id, queried = record.get("query_id"), record.get("query_unix_s")
        relation = None
        if alert:
            if alert.get("query_id") == query_id:
                relation = "trigger"
            elif finite(queried) and queried >= alert["since_unix_s"]:
                relation = "after_alert"
            else:
                relation = "before_alert"
        return {"query_id": query_id, "frame_id": record.get("frame_id"), "preview": name,
                "preview_sha256": digest, "problem": problem, "verdict": verify.get("verdict"),
                "iou": verify.get("iou"), "inconclusive_reason": verify.get("inconclusive_reason"),
                "query_unix_s": queried if finite(queried) else None, "relation": relation}

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

    @staticmethod
    def _designation(state: dict) -> dict | None:
        """The session's own ``designation`` (display only; the page never acts on it)."""
        designation = state.get("designation")
        if not isinstance(designation, dict):
            return None
        acquire = designation.get("acquire") if isinstance(designation.get("acquire"), dict) else {}
        return {"designation_id": designation.get("designation_id"), "result": designation.get("result"),
                "resolution_level": designation.get("resolution_level"),
                "track_id": designation.get("track_id"), "frame_id_k": designation.get("frame_id_k"),
                "acquire_status": acquire.get("status"), "candidates": designation.get("candidates")}

    def _activity_after_close(self, state: dict | None, issued: float | None) -> bool:
        """This session's tracker_state is provably newer than its end (R2@K1K3 K1K3-R2-1).

        A session journals TERMINAL first and rewrites tracker_state right after, so a poll between the
        two reads the old non-TERMINAL state: that alone is a normal end, not activity. It counts only
        when (a) an earlier poll already read tracker_state = TERMINAL (polls are serialized, so this
        read is later) or (b) the state's envelope was issued after the TERMINAL journal record.
        """
        if state is None:
            return False
        if state.get("state") == "TERMINAL":
            self.terminal_state_seen = True
            return False
        if self.terminal_state_seen:
            return True
        return self.closed and self.closed_at is not None and issued is not None and issued > self.closed_at

    def _block_reason(self, state: dict | None, issued: float | None = None) -> str | None:
        if self.session_id in RETIRED_SIDS:
            return f"{self.session_id} 已用，不可再发动作"
        if self.block:
            return self.block
        if self.archive_dir.exists():
            self.block = f"出现同号归档 {self.archive_dir}"
        elif self._activity_after_close(state, issued):
            self.block = "会话已结束后本号又有活动：同号被复用"
        return self.block

    def poll(self) -> dict:
        with self.poll_lock:
            return self._poll()

    def _poll(self) -> dict:
        state, note, state_issued = self._read_state()
        result, issued = self._read_result()
        latest, sim, captured = self._read_frames()
        with self.lock:
            now = self.clock()
            self._read_logs()             # after the state: the trigger result is already logged
            receipt = self.receipt_check.evaluate(self.session_started, self.started_count)
            block = self._block_reason(state, state_issued)
            if latest is not None and (self.frame_seen is None or self.frame_seen[0] != latest):
                self.frame_seen = (latest, now)
            snap = {"session_id": self.session_id, "polled_unix_s": now, "state": state,
                    "note": note, "legal": [], "view": None, "candidate": None, "alert": None,
                    "verify": None, "verify_after_alert": None, "verify_in_flight": None,
                    "receipt": receipt, "sid_block": block, "closed": self.closed,
                    "instruction_known": self.instruction_known, "designation": None,
                    "frames": {"latest_frame_id": latest, "sim_t": sim, "capture_unix_s": captured,
                               "changed_unix_s": captured if captured is not None
                               else (self.frame_seen[1] if self.frame_seen else None),
                               "changed_from": "capture" if captured is not None else "first_seen"},
                    "queries": {"max_seq": self.max_seq}, "published": None}
            if state is not None:
                if block is None and not self.closed:
                    snap["legal"] = legal_actions(state, instruction_reusable=self.instruction_known)
                if state.get("state") == "AWAITING_CONFIRMATION":
                    snap["candidate"] = self._candidate(state, result, issued, latest, receipt)
                snap["designation"] = self._designation(state)
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
                                    "等数据恢复，或用终端 CLI 后备")
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
    """Closed-grammar instruction text from the page's drop-downs; raises ValueError."""
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
    """Runs one ``controller.language_loop`` operator call with this interpreter in this worktree."""

    def __init__(self, python: str, worktree: Path, runtime: Path, session_id: str):
        self.python, self.worktree = python, Path(worktree)
        self.runtime, self.session_id = Path(runtime), session_id

    def argv(self, action: str, request_id: str, *, token: str | None = None,
             index: int | None = None, instruction: str | None = None) -> list[str]:
        if action not in ACTIONS:
            raise ValueError(f"not an operator action: {action}")
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
    if value is None:
        return ""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    return str(value)


#: CLI exits that prove no request was written (language_loop.main: 2 = argument/guard refusal
#: before the request is written, 4 = WRITER_BUSY); every other exit without a receipt leaves the result unknown
NOT_WRITTEN_EXITS = frozenset({2, 4})


def interpret(outcome: dict) -> tuple[dict | None, str]:
    """(receipt or None, one-line meaning) of a CLI outcome; never claims binding or publishing."""
    if outcome.get("timeout"):
        return None, "CLI 超时被终止：结果未知，可能稍后执行；不会自动重发"
    code = outcome.get("exit")
    if code == 0:
        try:
            receipt = json.loads(outcome.get("stdout") or "").get("receipt")
        except (ValueError, AttributeError):
            receipt = None
        if isinstance(receipt, dict):
            meaning = {"APPLIED": "会话已受理（只表示受理，不等于绑定、收养或写出；看指定结果与状态）",
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
        self.log_path = self.opdir / LOG_NAME
        self.nonce = secrets.token_hex(16)
        self.busy = threading.Lock()
        self.timer_lock = threading.Lock()
        self.last_done: tuple | None = None
        self.last_click: dict | None = None
        self.unknowns: dict[str, dict] = {}       # request_id -> request whose result is unknown
        self.late_messages: dict[str, str] = {}
        self.pending_lock = threading.Lock()
        self.log_lock = threading.Lock()          # clicks, timer notices and the mark may log concurrently
        self.play_start, self.timer_problem, self.deadline_logged = self._load_timer()
        self.opdir.mkdir(parents=True, exist_ok=True)

    # --- operator log and Play clock ---------------------------------------------------

    def log(self, **fields) -> None:
        record = dict(fields, at_unix_s=self.clock())
        with self.log_lock, self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, default=as_text) + "\n")

    def _load_timer(self) -> tuple[float | None, str | None, bool]:
        """(first persisted Play mark, why it cannot be trusted, deadline notice already logged)."""
        records = read_journal(self.log_path)
        if records is None:
            return None, "操作日志无法完整读取", False
        marks = [record for record in records if record.get("kind") == "play_start_marked"]
        noticed = any(record.get("kind") == "play_deadline_notice" for record in records)
        if not marks:
            return None, None, noticed
        start = marks[0].get("play_start_unix_s")
        if not finite(start):
            return None, "已有 Play 开始标记但时刻不可读", noticed
        if start > self.clock() + MARK_SKEW_S:
            return None, "已有 Play 开始标记但晚于本机时钟", noticed
        return float(start), None, noticed

    def timer(self, now: float) -> dict:
        with self.timer_lock:
            start, problem = self.play_start, self.timer_problem
            view = {"limit_s": PLAY_LIMIT_S, "warn_s": PLAY_WARN_S, "start_unix_s": start,
                    "elapsed_s": None, "remaining_s": None, "status": "unmarked", "message": None}
            if problem:
                view.update(status="unreliable", message=f"无法可靠读取 Play 起点（{problem}）：请手工计时")
                return view
            if start is None:
                view["message"] = "尚未标记 Play 开始：页面启动与会话启动时刻都不算 Play 开始"
                return view
            elapsed = now - start
            if elapsed < -MARK_SKEW_S:
                view.update(status="unreliable", message="Play 起点晚于本机时钟：请手工计时")
                return view
            view.update(elapsed_s=max(elapsed, 0.0), remaining_s=PLAY_LIMIT_S - elapsed,
                        status="due" if elapsed >= PLAY_LIMIT_S else "running")
            if view["status"] == "due":
                view["message"] = "已到 3 min：请立即点「停止会话」（或终端 stop）；页面不会自动停止"
                if not self.deadline_logged:
                    self.deadline_logged = True
                    self.log(kind="play_deadline_notice", play_start_unix_s=start, elapsed_s=elapsed,
                             note="notice only; no stop was sent")
            elif elapsed >= PLAY_WARN_S:
                view["message"] = "接近 3 min：准备停止"
            return view

    def mark_play_start(self) -> dict:
        # C2@K1K3 C2-2: the mark is a button like the others — a same-number block (second
        # session_started, archive of this number, activity after close, retired SID) disables it,
        # and an unreadable session state does not let it through.
        try:
            current = self.monitor.poll()
        except Exception as error:  # an unreadable bridge must not be acted on
            self.monitor.fail(error)
            return self.refuse(f"读取会话状态失败，未标记：{type(error).__name__}: {error}；请手工计时",
                               action="play_start_mark")
        if current.get("sid_block"):
            return self.refuse(f"同号不可复用：{current['sid_block']}；计时标记已停用，请手工计时",
                               action="play_start_mark")
        with self.timer_lock:
            if self.timer_problem:
                reason = f"不能标记：{self.timer_problem}；请手工计时"
            elif self.play_start is not None:
                reason = "Play 开始已标记过；计时依据首次标记，不能重设"
            else:
                now = self.clock()
                self.log(kind="play_start_marked", play_start_unix_s=now, source="operator_click")
                self.play_start = now
                self.last_click = {"ok": True, "action": "标记 Play 开始", "message": "已记录 Play 开始"}
                return {"ok": True, "message": "已记录 Play 开始（写入操作日志）"}
        return self.refuse(reason, action="play_start_mark")

    # --- clicks -------------------------------------------------------------------------

    def pending(self) -> list[dict]:
        with self.pending_lock:
            return [dict(entry) for entry in self.unknowns.values()]

    def resolve_late_receipts(self) -> None:
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
        now = self.clock()
        snap = self.monitor.public(now)
        snap["timer"] = self.timer(now)
        # C2@K1K3 C2-2: a same-number block disables the Play mark too (the server refuses it as well)
        snap["timer"]["mark_block"] = (f"同号不可复用：{snap['sid_block']}；计时标记已停用，请手工计时"
                                       if snap.get("sid_block") else None)
        snap["busy"] = self.busy.locked()
        snap["last_click"] = self.last_click
        unknowns = self.pending()
        for entry in unknowns:            # C2-1: the retry button follows the current table and view
            entry["retry_block"] = self.retry_block(entry, snap, now)
            entry["retry_allowed"] = entry["retry_block"] is None
        snap["unknowns"] = unknowns
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
        if current.get("sid_block"):
            return self.refuse(f"同号不可复用：{current['sid_block']}；全部动作已禁用", action=action, view=view)
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
            shown = [c.get("index") for c in gates.get("candidates") or []]
            if not isinstance(index, int) or isinstance(index, bool) or index not in shown:
                return self.refuse("候选编号不在本次显示的候选内", action=action, view=view, index=index)
            if not gates.get("confirmable"):
                return self.refuse(gates.get("why_not") or "不可确认", action=action, view=view, index=index)
            seen = body.get("preview_seen")
            if (not isinstance(seen, dict) or seen.get("name") != gates.get("preview")
                    or seen.get("sha256") != gates.get("preview_sha256")):
                return self.refuse("页面尚未显示并解码这次候选的预览（加载中、失败或已换图/换候选），不能确认",
                                   action=action, view=view, index=index, preview_seen=seen)
            preview = {"name": seen["name"], "sha256": seen["sha256"]}
        else:
            index, preview = None, None
        request_id = f"{self.monitor.session_id}-web-{uuid.uuid4().hex[:8]}"
        argv = self.argv_builder.argv(action, request_id, token=token, index=index,
                                      instruction=instruction)
        return self._run(action=action, view=view, argv=argv, request_id=request_id, key=key,
                         index=index, instruction=instruction, kind="click", preview=preview)

    def _retry(self, request_id: str) -> dict:
        try:
            current = self.monitor.poll()
        except Exception as error:  # an unreadable bridge must not be acted on
            self.monitor.fail(error)
            return self.refuse(f"读取会话状态失败，本次未重试：{type(error).__name__}: {error}",
                               action="retry", request_id=request_id)
        if current.get("sid_block"):
            return self.refuse(f"同号不可复用：{current['sid_block']}；不重试", action="retry",
                               request_id=request_id)
        self.resolve_late_receipts()
        with self.pending_lock:
            pending = dict(self.unknowns[request_id]) if request_id in self.unknowns else None
            late = self.late_messages.get(request_id)
        if pending is None:
            if late is not None:
                return self.refuse(f"不再重试，原请求已有回执——{late}", action="retry", request_id=request_id)
            return self.refuse("没有这个结果未知的请求可重试", action="retry", request_id=request_id)
        # C2@K1K3 C2-1: a retry is a CLI call like any click — the current state, view, closed table,
        # token and (confirm) gates must still admit it; otherwise nothing is sent and the entry stays
        # for its late receipt.
        blocked = self.retry_block(pending, current, self.clock())
        if blocked is not None:
            return self.refuse(blocked, action="retry", request_id=request_id,
                               retry_of=pending["action"], view=pending["view"],
                               current_view=current.get("view"), current_legal=current.get("legal"))
        reply = self._run(action=pending["action"], view=pending["view"], argv=pending["argv"],
                          request_id=request_id, key=None, index=pending.get("index"),
                          instruction=pending.get("instruction"), kind="retry_same_request_id")
        if (reply.get("receipt") or {}).get("outcome") == "IGNORED_DUPLICATE":
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

    def retry_block(self, pending: dict, current: dict, now: float) -> str | None:
        """Why a same-request_id retry of ``pending`` must not be sent against ``current`` (None = allowed).

        Same checks as a click (C2@K1K3 C2-1): no same-number block, the stored view still equals the
        current view (state, epoch, token fields), the action is in the current nine-state table, the
        token in the stored argv is the current one, and a confirm still passes its gates on the same
        preview bytes. The session's own request_id dedup stays the final word; this only stops the page
        from sending an action outside the current table.
        """
        if current.get("sid_block"):
            return f"同号不可复用：{current['sid_block']}；不重试"
        action, view = pending.get("action"), pending.get("view") or {}
        was = {k: view.get(k) for k in VIEW_KEYS}
        now_view = current.get("view")
        if now_view is None or was != now_view:
            return (f"状态或令牌已变（原 {was.get('state')} → 现 {(now_view or {}).get('state') or '无状态'}）："
                    "不按旧画面重试；先看状态与迟到回执，需要时按新画面重新操作或用终端 status 核对")
        if action not in current.get("legal", []):
            return f"{action} 在 {now_view['state']} 下不合法：不重试"
        if action in TOKEN_FIELD:
            argv = pending.get("argv") or []
            token = argv[argv.index("--token") + 1] if "--token" in argv[:-1] else None
            if not token or token != now_view.get(TOKEN_FIELD[action]):
                return "令牌与当前画面不符：不重试"
        if action == "confirm":
            gates = self.monitor.public(now).get("candidate") or {}
            shown = [c.get("index") for c in gates.get("candidates") or []]
            if pending.get("index") not in shown:
                return "候选编号不在当前显示的候选内：不重试"
            if not gates.get("confirmable"):
                return f"{gates.get('why_not') or '不可确认'}：不重试"
            seen = pending.get("preview") or {}
            if seen.get("name") != gates.get("preview") or seen.get("sha256") != gates.get("preview_sha256"):
                return "预览已换（不是原请求确认时显示的那张）：不重试"
        return None

    def _run(self, *, action, view, argv, request_id, key, index, instruction, kind,
             preview: dict | None = None) -> dict:
        started = self.clock()
        outcome = self.runner(argv)
        stdout, stderr = as_text(outcome.get("stdout")), as_text(outcome.get("stderr"))
        receipt, meaning = interpret(dict(outcome, stdout=stdout, stderr=stderr))
        finished = self.clock()
        # record the unknown state first, so a later logging problem can never lose it
        with self.pending_lock:
            if kind == "retry_same_request_id":
                entry = self.unknowns.get(request_id)
                if receipt is not None and receipt.get("outcome") != "IGNORED_DUPLICATE":
                    self.unknowns.pop(request_id, None)
                elif entry is not None:
                    entry["last_retry"] = {"exit": outcome.get("exit"), "timeout": bool(outcome.get("timeout")),
                                           "message": meaning, "at_unix_s": finished}
                    if receipt is None:
                        meaning = f"{meaning}；原请求结果仍未知，保留在「结果未知」框"
                elif request_id in self.late_messages:
                    meaning = f"{meaning}；原请求已有回执——{self.late_messages[request_id]}"
            elif receipt is None and outcome.get("exit") not in NOT_WRITTEN_EXITS:
                self.unknowns[request_id] = {"request_id": request_id, "argv": argv, "action": action,
                                             "view": view, "index": index, "instruction": instruction,
                                             "preview": preview, "since_unix_s": finished}
        unknown = receipt is None and (kind == "retry_same_request_id" or outcome.get("exit") not in NOT_WRITTEN_EXITS)
        self.log(kind=kind, action=action, view=view, index=index, instruction=instruction,
                 request_id=request_id, argv=argv, exit_code=outcome.get("exit"),
                 timeout=outcome.get("timeout"), stdout=stdout, stderr=stderr, receipt=receipt,
                 result_unknown=unknown, meaning=meaning, started_unix_s=started)
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
    server_version = "acq-operator/1"

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
        parts = urllib.parse.urlsplit(self.path)
        if parts.path == "/":
            page = PAGE.replace("__NONCE__", self.app.nonce).replace(
                "__SESSION__", self.app.monitor.session_id)
            return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        if parts.path == "/api/state":
            return self._json(200, self.app.state())
        if parts.path.startswith("/preview/"):
            name = parts.path[len("/preview/"):]
            wanted = (urllib.parse.parse_qs(parts.query).get("sha") or [""])[0]
            if not PREVIEW_NAME.match(name) or not SHA_HEX.match(wanted):
                return self._send(404, b"not found", "text/plain")
            try:
                data = (self.app.monitor.previews / name).read_bytes()
            except OSError:
                return self._send(404, b"not found", "text/plain")
            if hashlib.sha256(data).hexdigest() != wanted:   # the bytes changed: not the bound image
                return self._send(409, b"preview changed", "text/plain")
            return self._send(200, data, "image/png")
        return self._send(404, b"not found", "text/plain")

    def do_POST(self):  # noqa: N802
        port = self.server.server_address[1]
        origin = self.headers.get("Origin")
        path = urllib.parse.urlsplit(self.path).path
        if (not self._host_ok() or path not in {"/api/action", "/api/play-start"}
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
        if path == "/api/play-start":
            return self._json(200, self.app.mark_play_start())
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


def load_controller(worktree: Path):
    """This worktree's ``controller.language_bridge`` and ``controller.language_loop`` (no model is loaded)."""
    root = str(Path(worktree).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
    from controller import language_bridge, language_loop
    return language_bridge, language_loop


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="P1-ENG-ACQ-001 Play D1 本地操作页（只监听 127.0.0.1）")
    parser.add_argument("--sid", required=True, help="本次新会话号 acq-d1-<n>（同号不可复用）")
    parser.add_argument("--runtime", default=str(REPO / "runtime"))
    parser.add_argument("--play-root", default=str(PLAY_ROOT),
                        help="会话在 <play-root>/sessions/<SID>，操作日志在 <play-root>/<SID>/operator/")
    parser.add_argument("--k-receipt", default=None,
                        help=f"缺省 <play-root>/k-receipt/{RECEIPT_NAME}（§2.7 本机生成的那份）")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--open", action="store_true", help="用默认浏览器打开页面")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    sid = arguments.sid
    if not SID_FORMAT.match(sid):
        print(f"会话号须为 acq-d1-<n>（操作单 §4）：{sid!r}", file=sys.stderr)
        return 2
    play_root, runtime = Path(arguments.play_root), Path(arguments.runtime)
    session_dir = play_root / "sessions" / sid
    archive_dir = play_root / sid / "unity-runtime"
    opdir = play_root / sid / "operator"
    receipt_path = Path(arguments.k_receipt) if arguments.k_receipt else play_root / "k-receipt" / RECEIPT_NAME
    bridge, loop = load_controller(REPO)
    used = sid_usage(sid, session_dir, archive_dir, runtime, bridge)
    if used:
        print(f"同号不可复用：{used}。操作页未启动、未写任何文件；换新号 acq-d1-<n+1>（操作单 §4）。",
              file=sys.stderr)
        return 2
    check = ReceiptCheck(loop, receipt_path, runtime)
    monitor = Monitor(bridge, check, runtime, sid, session_dir, archive_dir)
    builder = CliRunner(sys.executable, REPO, runtime, sid)
    app = App(monitor, builder, builder, opdir, bridge)
    try:
        server = build_server(app, arguments.port)
    except OSError as error:
        print(f"操作页无法监听 {HOST}:{arguments.port}：{error}（端口被占用？先停掉残留的操作页）",
              file=sys.stderr)
        return 2
    url = f"http://{HOST}:{server.server_address[1]}/"
    initial = check.evaluate(None, 0)
    app.log(kind="server_start", url=url, session_id=sid, runtime=str(runtime),
            session_dir=str(session_dir), worktree=str(REPO), python=sys.executable,
            k_receipt=str(receipt_path), receipt_values=initial["values"],
            receipt_static_problems=[p for p in initial["problems"] if "session_started" not in p])
    stop = threading.Event()
    threading.Thread(target=poll_forever, args=(monitor, stop), daemon=True).start()
    print(f"operator page {url} session={sid} (Ctrl-C to stop; the §4 T3 CLI stays as fallback)", flush=True)
    for problem in initial["problems"]:
        print(f"  收据检查：{problem}", flush=True)
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
<title>Play D1 操作台 __SESSION__</title>
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
  .s-QUERYING, .s-ACQUIRING { background:#dbeafe; color:var(--info); }
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
  .note { color:var(--warn); } .muted { color:var(--muted); } .bad { color:var(--bad); font-weight:700; }
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
  #timer.due { border:2px solid var(--bad); background:#fff5f4; }
</style>
</head>
<body>
<div id="banner" class="banner" hidden></div>
<header>
  <b>Play D1 操作台</b><span>会话 <code>__SESSION__</code></span>
  <span id="state" class="pill">—</span><span id="track" class="muted"></span>
  <span id="frames" class="muted"></span><span id="published" class="muted"></span>
  <span id="fresh" class="muted"></span>
</header>
<main id="main">
  <section id="timer" class="view"></section>
  <section class="view"><div id="picture" class="empty">等待会话…</div>
    <div id="caption" class="caption"></div></section>
  <section id="status" class="view"></section>
  <section class="view"><div id="buttons" class="buttons"></div>
    <div id="composer" class="row" style="margin-top:10px"></div>
    <div id="unknown"></div>
    <div id="sending" class="note small" hidden>请求在途：等待会话回执（最长约 5 s）。这期间不能发下一个请求，停止也要等它结束（终端 CLI 同样要等写者锁）。</div>
    <div id="click" class="result caption"></div></section>
  <section id="second" class="view" hidden></section>
  <section id="receipt" class="view small"></section>
</main>
<script>
const NONCE = "__NONCE__";
let snap = null, rendered = null, sending = false, fetching = false, composerBuilt = false;
let lastOkAt = null, fetchFailed = false;
let shownPreview = null, previewProblem = null;   // {name, sha256} of the candidate preview actually decoded here
let pictureKey = null;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const img = (name, sha) => `<img alt="preview" src="/preview/${encodeURIComponent(name)}?sha=${encodeURIComponent(sha || "")}">`;
const ago = (unix, now) => unix == null || now == null ? "—" : `${Math.max(now - unix, 0).toFixed(1)} s 前`;
const clock = (unix) => unix == null ? "—" : new Date(unix * 1000).toLocaleTimeString();

async function post(path, body, confirmText) {
  if (sending) return;
  if (confirmText && !window.confirm(confirmText)) return;
  sending = true; $("sending").hidden = false; paintButtons();
  $("click").textContent = "发送中…";
  try {
    const response = await fetch(path, {method:"POST",
      headers:{"Content-Type":"application/json","X-Operator-Nonce":NONCE}, body:JSON.stringify(body)});
    const data = await response.json();
    $("click").textContent = (data.ok ? "✔ " : "✖ ") + data.message + (data.request_id ? `（request_id=${data.request_id}）` : "");
  } catch (error) { $("click").textContent = "✖ 页面与本机服务断开：" + error + "（结果未知；用终端 status 核对）"; }
  sending = false; $("sending").hidden = true; rendered = null; await refresh();
}
const send = (body, confirmText) => post("/api/action", body, confirmText);

function act(action, extra) { return () => send(Object.assign({action, view: rendered.view}, extra || {}),
  action === "stop" ? "确定停止本会话？停止后本次尝试不能再指定。" :
  action === "release" ? "确定释放当前跟踪（进入 LOST）？" : null); }

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

function previewShown(cand) {
  return !!cand && !!shownPreview && shownPreview.name === cand.preview && shownPreview.sha256 === cand.preview_sha256;
}

function confirmReady() {
  const cand = snap && snap.candidate;
  return !!cand && cand.confirmable && !snap.stale && !fetchFailed && !snap.sid_block && previewShown(cand);
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
  if (legal.has("ask")) specs.push({label:"指定：the car", cls: idle ? "primary big" : "", action:"ask",
    on:() => send({action:"ask", view:rendered.view, instruction:{color:null, class:"car"}})});
  if (legal.has("respecify")) specs.push({label:"重新指定（沿用上次指令）", action:"respecify", on:act("respecify")});
  if (legal.has("verify")) specs.push({label:"立即核验", action:"verify", on:act("verify")});
  if (legal.has("release")) specs.push({label:"释放跟踪…", cls:"danger", action:"release", on:act("release")});
  if (legal.has("stop")) specs.push({label:"停止会话…", cls:"danger", action:"stop", on:act("stop")});
  return specs;
}

function paintButtons() {
  const dead = sending || fetchFailed || !!(snap && snap.sid_block);
  $("buttons").querySelectorAll("button").forEach((b) => {
    const blocked = unknownBlocks(b.dataset.action);
    b.disabled = dead || blocked || (b.dataset.kind === "confirm" && !confirmReady());
    b.textContent = b.dataset.label + (blocked ? "（结果未知）" : "");
  });
  const c = $("c-send"); if (c) c.disabled = dead || !c.dataset.action || unknownBlocks("ask");
  $("unknown").querySelectorAll("button.retry").forEach((r) => { r.disabled = dead || !retryOk(r.dataset.requestId); });
  // the reason text may change every refresh (e.g. the frame-gap count); it is updated in place, not by a rebuild
  $("unknown").querySelectorAll("div.retry-why").forEach((n) => {
    const u = ((snap && snap.unknowns) || []).find((x) => x.request_id === n.dataset.requestId);
    if (u && u.retry_block) n.textContent = "不能重试：" + u.retry_block;
  });
  const m = $("mark"); if (m) m.disabled = dead || !!(snap && snap.timer && snap.timer.mark_block);
}

// C2@K1K3 C2-1: a retry is offered only while the server says the current state/view/table/token still
// admit it and the action is in the current legal set on the view this page shows (the server re-checks).
function retryOk(requestId) {
  const u = ((snap && snap.unknowns) || []).find((x) => x.request_id === requestId);
  return !!u && u.retry_allowed === true && (snap.legal || []).includes(u.action)
    && JSON.stringify(u.view) === JSON.stringify(rendered && rendered.view);
}

function timerHtml(t) {
  if (!t) return "";
  if (t.status === "unmarked")
    return `<div class="row"><button id="mark" class="primary">标记 Play 开始（按下 Unity Play 的同时点）</button>
      <span class="note">${esc(t.mark_block || t.message)}</span></div>`;
  if (t.status === "unreliable") return `<div class="bad">${esc(t.message)}</div>`;
  const remain = Math.max(t.remaining_s, 0).toFixed(0);
  return `<div class="count ${t.status === "due" || t.remaining_s <= t.limit_s - t.warn_s ? "low" : ""}">Play 已 ${t.elapsed_s.toFixed(0)} s · 剩余 ${remain} s / ${t.limit_s.toFixed(0)} s</div>` +
    `<div class="small muted">Play 开始（用户标记）${clock(t.start_unix_s)}；计时依据首次标记，刷新或重启页面不重置</div>` +
    (t.message ? `<div class="${t.status === "due" ? "bad" : "note"}">${esc(t.message)}</div>` : "");
}

function designationHtml(d, st) {
  if (!d) return "";
  let path = "";
  if (st && st.state === "ACQUIRING") path = "自动转向重捕中（TRACK_ENDED → ACQUIRING）：只观察进展，只可停止";
  else if (st && st.state === "LOST" && st.reason === "acquire_failed") path = "转向重捕失败：LOST(acquire_failed)，不自动重试";
  return `<div class="small">最近指定 #${esc(d.designation_id)}：<b>${esc(d.result)}</b>` +
    (d.resolution_level ? ` · 第 ${esc(d.resolution_level)} 级` : "") + (d.track_id != null ? ` · 轨迹 ${esc(d.track_id)}` : "") +
    (d.acquire_status ? ` · 重捕 ${esc(d.acquire_status)}` : "") + ` · 帧 k=${esc(d.frame_id_k)}</div>` +
    (path ? `<div class="note">${esc(path)}</div>` : "");
}

function statusHtml(s) {
  const st = s.state, cand = s.candidate;
  if (!st) return `<span class="note">${esc(s.note || "等待会话")}</span>`;
  let html = "";
  if (cand) {
    const ready = confirmReady();
    if (cand.confirmable && cand.remaining_s != null && previewShown(cand))
      html = `<div class="count ${cand.remaining_s < 3 ? "low" : ""}">剩余 ${Math.max(cand.remaining_s, 0).toFixed(1)} s</div>`;
    else html = `<div class="count low">不可确认</div>`;
    let why = cand.why_not;
    if (!why && s.stale) why = "页面数据过期：不能确认";
    if (!why && !previewShown(cand))
      why = previewProblem ? `预览没有显示成功（${previewProblem}）：不能确认；可驳回或重新指定` : "预览加载中：显示并解码成功后才能确认";
    html += (cand.t_conf_s != null ? `<div class="gates">截止取先到者：结果出现起 ≤${cand.t_conf_s} s、查询起 ≤${(cand.t_ret_s + cand.t_conf_s).toFixed(1)} s` +
      (cand.deadline_from ? `（当前由${cand.deadline_from}决定）` : "") +
      ` · 帧差 ${cand.frames_delta ?? "—"}/${cand.frames_limit}（三门取先到者；页面计时只是提示，会话检查为准）</div>` : "") +
      (!ready && why ? `<div class="note">${esc(why)}</div>` : "") +
      `<div class="small muted">${esc(cand.status)} · result_id=${esc(cand.result_id)} · q=${esc(cand.query_id)} · frame ${esc(cand.frame_id)} · ${cand.candidates.length} 个候选</div>`;
  } else if (s.alert) {
    const a = s.alert;
    html = `<div class="alert"><b>疑似（${esc(a.kind)}）</b> ${esc(a.suspect_id)} · 告警于 ${ago(a.since_unix_s, s.now_unix_s)}` +
      (a.query_id ? ` · 触发核验 q=${esc(a.query_id)} frame ${esc(a.frame_id)} verdict=${esc(a.verdict)}` : "") +
      (a.message ? `<div class="note">${esc(a.message)}</div>` : "") + `</div>`;
  } else if (st.state === "TRACKING") html = `跟踪中 · 发布 ${st.publishing ? "开" : "关"}`;
  else if (st.state === "QUERYING") html = "查询中：等候选…";
  else if (st.state === "ACQUIRING") html = "转向重捕中（自动）";
  else html = st.state === "TERMINAL" ? "会话已结束" : `${esc(st.state)}${st.reason ? "（" + esc(st.reason) + "）" : ""}`;
  html += designationHtml(s.designation, st);
  if (s.verify_in_flight) html += `<div class="small muted">核验进行中 q=${esc(s.verify_in_flight)}</div>`;
  if (s.last_click) html += `<div class="small muted">上次点击：${esc(s.last_click.action)} → ${esc(s.last_click.outcome || "")} ${esc(s.last_click.message)}</div>`;
  return html;
}

function receiptHtml(r) {
  if (!r) return "";
  const v = r.values || {};
  const line = `收据 ${esc(v.path)} · ${esc(v.host)}/${esc(v.backend)}/${esc(v.model_form)} · hz ${esc(v.hz)} · R ${esc(v.retained_frame_count)}` +
    ` · k_ret ${esc(v.k_ret)} · k_conf ${esc(v.k_conf)} · T_ret ${v.t_ret_s != null ? Number(v.t_ret_s).toFixed(1) : "—"} s · T_conf ${esc(v.t_conf_s)} s` +
    (v.report_git_head ? ` · 报告 git_head ${esc(v.report_git_head)}` : "");
  return (r.ok ? `<div>收据绑定：通过（与本次 session_started、§2.7 报告、生效 R/hz 一致）</div>`
               : `<div class="bad">收据绑定未通过：确认已停用</div><div class="note">${(r.problems || []).map(esc).join("<br>")}</div>`) +
    `<div class="muted">${line}</div>`;
}

function pictureFor(s) {
  const cand = s.candidate, a = s.alert, after = s.verify_after_alert, latest = s.verify;
  if (cand) return cand.preview ? {name: cand.preview, sha: cand.preview_sha256, candidate: true,
    caption: `候选预览 · frame ${cand.frame_id} · q=${cand.query_id} · result_id=${cand.result_id}（框上的编号 = 按钮编号）`} : {text: cand.why_not || "等待预览"};
  if (a && a.preview) return {name: a.preview, sha: a.preview_sha256, caption: `告警触发核验 q=${a.query_id} · frame ${a.frame_id}`};
  if (a && !a.query_id) return after && after.preview
    ? {name: after.preview, sha: after.preview_sha256, caption: `本次告警后核验 q=${after.query_id} · frame ${after.frame_id} · ${after.verdict}（按此判断）`}
    : {text: "等待本次告警后的核验：先点「立即核验」。"};
  if (a) return {text: a.message || "等待触发核验"};
  if (latest && latest.preview) return {name: latest.preview, sha: latest.preview_sha256, caption: `最近核验 q=${latest.query_id} · frame ${latest.frame_id} · ${latest.verdict}`};
  return {text: "（当前没有要看的预览）"};
}

function secondFor(s, main) {
  const v = s.alert && s.verify;
  if (!v || !v.preview || v.preview === main) return "";
  const cls = v.relation === "before_alert" ? "ref" : "";
  return `<div class="caption ${cls}"><b>${esc(v.relation || "最近核验")}</b> q=${esc(v.query_id)} · frame ${esc(v.frame_id)} · ${esc(v.verdict)} · 发起于 ${ago(v.query_unix_s, s.now_unix_s)}</div>` + img(v.preview, v.preview_sha256);
}

function render(s) {
  const st = s.state;
  $("main").className = (fetchFailed || s.stale) ? "stale" : "";
  const banner = s.sid_block ? `同号不可复用：${esc(s.sid_block)}；全部动作已禁用（换新号，按操作单 §4 重来）`
    : fetchFailed ? `本机服务未响应（最后成功读取 ${lastOkAt ? ((Date.now() - lastOkAt) / 1000).toFixed(1) + " s 前" : "—"}）：下面是旧数据，按钮已停用；用终端 CLI 后备`
    : (s.stale ? `页面数据过期：${esc(s.poll_error || ("最后读取 " + (s.age_s != null ? s.age_s.toFixed(1) + " s 前" : "—")))}；确认已停用` : "");
  $("banner").hidden = !banner; $("banner").textContent = banner;
  $("state").textContent = st ? st.state + (st.reason ? `（${st.reason}）` : "") + (st.suspect_kind ? ` ${st.suspect_kind}` : "") : "未连接";
  $("state").className = "pill" + (fetchFailed || s.stale ? " s-stale" : (st ? " s-" + st.state : ""));
  $("track").textContent = st && st.track_id ? `track ${st.track_id}` : "";
  const f = s.frames || {};
  const frameAge = f.changed_unix_s != null && s.now_unix_s != null ? s.now_unix_s - f.changed_unix_s : null;
  $("frames").innerHTML = `帧 ${f.latest_frame_id ?? "—"}（${f.changed_from === "capture" ? "采集于 " : "本页首见 "}${ago(f.changed_unix_s, s.now_unix_s)}）` +
    (frameAge != null && frameAge > 3 ? ' <b class="note">帧未前进 &gt;3 s</b>' : "") + ` · sim_t ${f.sim_t != null ? f.sim_t.toFixed(1) + " s" : "—"}` +
    ` · 查询序号 ${s.queries ? s.queries.max_seq : 0}`;
  const p = s.published;
  $("published").innerHTML = p && p.track_id ? (p.first_published != null
    ? `已写出观测：首见 frame ${p.first_published} · last_published ${p.last_published}（本页见其 ${ago(p.changed_unix_s, s.now_unix_s)}变化）`
    : "尚未写出观测") : "";
  $("fresh").textContent = fetchFailed
    ? `读取失败（最后成功 ${lastOkAt ? ((Date.now() - lastOkAt) / 1000).toFixed(1) + " s 前" : "—"}）`
    : `最后读取 ${clock(s.polled_unix_s)}（${s.age_s != null ? s.age_s.toFixed(1) + " s 前" : "—"}）`;
  $("timer").className = "view" + (s.timer && s.timer.status === "due" ? " due" : "");
  const timer = timerHtml(s.timer);
  if ($("timer").dataset.html !== timer) {    // rebuilt only on change, so the mark button stays clickable
    $("timer").dataset.html = timer; $("timer").innerHTML = timer;
    const mark = $("mark");
    if (mark) mark.addEventListener("click", () => post("/api/play-start", {mark: true},
      "现在按下 Unity Play 了吗？标记写入操作日志，之后不能重设。"));
  }
  $("status").innerHTML = statusHtml(s);
  $("receipt").innerHTML = receiptHtml(s.receipt);
  const main = pictureFor(s);
  const key = JSON.stringify([s.view, s.legal, s.sid_block, main.name || main.text, main.sha, s.alert && s.alert.query_id,
    s.verify && s.verify.query_id, s.verify_after_alert && s.verify_after_alert.query_id,
    (s.unknowns || []).map((u) => u.request_id + ":" + (u.last_retry ? u.last_retry.at_unix_s : "") + ":" + (u.retry_allowed ? "ok" : "blocked")).join(",")]);
  if (key === rendered?.key) { paintButtons(); return; }
  rendered = {key, view: s.view};
  $("caption").textContent = main.caption || "";
  const nextPicture = JSON.stringify([main.name || null, main.sha || null, main.text || null, !!main.candidate]);
  const picture = nextPicture === pictureKey ? null : document.createElement("div");
  if (picture) {
    pictureKey = nextPicture; shownPreview = null; previewProblem = null;
    $("picture").className = main.name ? "" : "empty";
    $("picture").innerHTML = main.name ? img(main.name, main.sha) : esc(main.text);
  }
  const image = picture && $("picture").querySelector("img");
  if (image && main.candidate) {
    const name = main.name, sha = main.sha;
    image.addEventListener("load", () => {
      if (image.naturalWidth > 0 && snap && snap.candidate && snap.candidate.preview === name && snap.candidate.preview_sha256 === sha)
        shownPreview = {name, sha256: sha};
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
    <button class="retry" data-request-id="${esc(u.request_id)}">用同一 request_id 重试</button>
    ${u.retry_allowed ? "" : `<div class="note retry-why" data-request-id="${esc(u.request_id)}">不能重试：${esc(u.retry_block)}</div>`}</div>`).join("");
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
    if (snap) render(snap); else { $("banner").hidden = false; $("banner").textContent = "本机服务未响应：用终端 CLI 后备"; }
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
