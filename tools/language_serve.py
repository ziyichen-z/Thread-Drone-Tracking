#!/usr/bin/env python3
"""P1-ENG-LOOP-001 §3.5：5060 薄 HTTP 服务（**单工、提交/轮询式**）。

三个端点：

* `POST /query`（multipart：JPEG + `surface` + `g4` + `query_id`）——空闲时立即
  返回 `{"accepted": true}`，忙时返回 `{"accepted": false, "error": "SERVER_BUSY"}`
  （**不排队**），`stuck` 后一律拒绝直到重启。
* `GET /status` —— `{"state": "idle" | "busy" | "stuck", ...}`。AC-8 修订 1：状态
  更新与 `POST` 接纳互斥，**模型真正结束前不得报 idle**。
* `GET /result/<query_id>` —— 取完成结果；只保留最近一次完成。客户端放弃的查询
  照常跑完，服务端不知道也不承诺不返回（AC-8 修订 1 删去该隐含承诺），有界性由
  客户端自己的 `T_ret` / `T_hard` 承担。

推理走同一个 `InferenceAdapter`，服务端不写第二份推理代码。

P1-ENG-LOOP-002 A2(a)：`--backend llama-server` 分支（缺省 `local-hf`，旧参数与行为不变）。
该分支启动前自算 GGUF / mmproj / 二进制三者 sha256、以 `<llama-bin> --version` 取构建号，
与 `--expect-assets` 逐键比对，任一不符即拒启（不起 `llama-server` 子进程）；随后以子进程
启动只绑 `127.0.0.1` 的 `llama-server`、轮询 `/health` 就绪，再起本服务。所有回包另带
`serve_code_sha256`（部署闭集摘要，`tools/eng_loop2/deploy_digest.py`）与 `machine`；逐请求
向 `--access-log` 追加一行字节计量（不记正文）；单次推理结束即删 scratch 图像。只在前台运行：
SIGINT/SIGTERM 或 `llama-server` 退出 → 关服务、停子进程，两个端口一并释放。

退出码（llama-server 分支）：0 正常停止；2 参数错（argparse）；3 拒启（资产/构建号/身份/
部署闭集不符，或 `--http-ledger` 不可读/损坏/与前一批上限不一致）；4 `llama-server` 未就绪
（load_failure）；5 服务期间 `llama-server` 退出；6 非推理 HTTP 预算不足（`S-ENVELOPE`：启动前
已无一次健康轮询的余量，或就绪等待中下一次健康轮询会越过「已用 + 1 + 预留 ≤ 上限」）。

AC-7 修订 3（IR-N1 / CHANGE:5，用户选 A）：llama-server 分支的 `GET /result/<query_id>?wait_s=<w>`
有界长轮询——服务端分离 query_id 与参数（只认一个 `wait_s`，有限正数且 ≤ 4 s，否则 400），同 query_id
完成/失败/stuck 时立即回复，仍 pending/busy 则在本次 w 到期时回复；回包回显实际采用的 `wait_s`。
不带参数时照旧即时回复。local-hf 分支不启用长轮询，路径解析与回包逐字不变。

AC-7 修订 2（CHANGE:1/2）：`llama-server` 命令行逐字固定十项资源旗标（`LLAMA_RESOURCE_FLAGS`）；
非推理 HTTP（每次 loopback `/health`、Air→板 `/status`、`/result/*` 与其他非推理请求，成功与失败
均计）和推理尝试（每个 `POST /query`）记入两服务批次共用的 `--http-ledger` 累计账，每个回包附
`http_budget` 快照；下一次业务性请求（健康轮询、`/result`）须满足「已用 + 1 + 本批预留 ≤ 上限」。
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Callable, Mapping
import urllib.parse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller.language_selector import (  # noqa: E402
    LONG_POLL_MAX_WAIT_S,
    LONG_POLL_PARAM,
    RawSelection,
    SelectorError,
    parse_multipart,
)

#: 服务端在途硬限（AC-10 修订 1 冻结常数）。
DEFAULT_T_HARD_S = 60.0
#: AC-7 修订 3：长轮询等待期间重核 stuck（时间判据）的最长间隔；完成/失败由条件变量立即唤醒。
LONG_POLL_RECHECK_S = 0.05


@dataclass
class CompletedQuery:
    query_id: str
    record: dict[str, Any] | None
    error: str | None
    #: AC-8 修订 2：异常的类型与消息随回包上线路，客户端据此留诊断。
    detail: str | None = None


class SingleFlightRuntime:
    """服务端状态机：至多一个在途查询，只保留最近一次完成。"""

    def __init__(
        self,
        adapter: Any,
        *,
        scratch_directory: Path,
        t_hard_s: float = DEFAULT_T_HARD_S,
        monotonic: Callable[[], float] = time.monotonic,
        delete_images_after_run: bool = False,
    ):
        self._adapter = adapter
        #: P1-ENG-LOOP-002 AC-7：llama-server 分支单次推理结束即删 scratch 图像（缺省关，
        #: local-hf 行为不变）。
        self._delete_images_after_run = bool(delete_images_after_run)
        self._scratch = Path(scratch_directory)
        self._scratch.mkdir(parents=True, exist_ok=True)
        self.t_hard_s = float(t_hard_s)
        self._monotonic = monotonic
        self._lock = threading.Lock()
        #: AC-7 修订 3：查询结束（完成/失败）时唤醒长轮询等待者；与 `_lock` 同一把锁。
        self._changed = threading.Condition(self._lock)
        self._in_flight: str | None = None
        self._started_at: float | None = None
        self._stuck = False
        self._last: CompletedQuery | None = None
        self._thread: threading.Thread | None = None

    # --- 状态 -------------------------------------------------------------

    def model_identity(self) -> dict[str, Any]:
        # HTTP is the measured client backend; the server uses local-hf internally.
        return dict(getattr(self._adapter, "identity", {}), backend="http")

    def _refresh_stuck_locked(self) -> None:
        if self._in_flight is None or self._started_at is None:
            return
        if self._monotonic() - self._started_at > self.t_hard_s:
            # 线程不可中断：只标 stuck，之后一律拒绝接单直到重启。
            self._stuck = True

    def status(self) -> dict[str, Any]:
        with self._lock:
            self._refresh_stuck_locked()
            if self._stuck:
                return {"state": "stuck", "query_id": self._in_flight}
            if self._in_flight is not None:
                return {
                    "state": "busy",
                    "query_id": self._in_flight,
                    "since": self._started_at,
                }
            return {"state": "idle", "query_id": None}

    def submit(
        self, query_id: str, image_bytes: bytes, surface: str, g4: bool,
        expected_model_identity: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            if expected_model_identity is not None and expected_model_identity != self.model_identity():
                return {"accepted": False, "error": "MODEL_IDENTITY_MISMATCH"}
            self._refresh_stuck_locked()
            if self._stuck:
                return {"accepted": False, "error": "SERVER_STUCK"}
            if self._in_flight is not None:
                return {"accepted": False, "error": "SERVER_BUSY"}
            image_path = self._scratch / f"{query_id}.jpg"
            image_path.write_bytes(image_bytes)
            self._in_flight = query_id
            self._started_at = float(self._monotonic())
            thread = threading.Thread(
                target=self._run,
                args=(query_id, image_path, surface, bool(g4)),
                daemon=True,
                name=f"language-serve-{query_id}",
            )
            self._thread = thread
        thread.start()
        return {"accepted": True, "query_id": query_id}

    def _run(self, query_id: str, image_path: Path, surface: str, g4: bool) -> None:
        record: dict[str, Any] | None = None
        error: str | None = None
        detail: str | None = None
        raw = None
        # AC-8 修订 2：try 只圈适配器的执行边界；`_record_of` 是服务端程序代码，
        # 它抛出的异常不得被记成 `worker_died` 回给客户端。
        try:
            raw = self._adapter.predict_one(query_id, image_path, surface, g4)
        except SelectorError as exception:
            error = exception.reason
            detail = exception.detail or exception.reason
        except Exception as exception:
            error = "worker_died"
            detail = f"{type(exception).__name__}: {exception}"
        finally:
            if self._delete_images_after_run:
                image_path.unlink(missing_ok=True)
        if raw is not None:
            record = _record_of(raw)
        with self._lock:
            self._last = CompletedQuery(query_id, record, error, detail)
            # AC-8 修订 1：模型真正结束之后才离开 busy。
            self._in_flight = None
            self._started_at = None
            self._changed.notify_all()

    def result(self, query_id: str) -> dict[str, Any]:
        with self._lock:
            return self._result_locked(query_id)

    def result_wait(self, query_id: str, wait_s: float) -> dict[str, Any]:
        """AC-7 修订 3：同 query_id 完成/失败/stuck 即回；仍 pending/busy 则在 `wait_s` 到期时回。"""
        deadline = time.monotonic() + float(wait_s)
        with self._changed:
            while True:
                document = self._result_locked(query_id)
                if document["state"] not in {"pending", "busy"}:
                    return document
                remaining = deadline - time.monotonic()
                if remaining <= 0.0:
                    return document
                self._changed.wait(min(remaining, LONG_POLL_RECHECK_S))

    def _result_locked(self, query_id: str) -> dict[str, Any]:
        """调用方持 `_lock`。"""
        self._refresh_stuck_locked()
        if self._stuck and self._in_flight == query_id:
            return {"state": "stuck", "query_id": query_id}
        if self._in_flight == query_id:
            return {"state": "busy", "query_id": query_id}
        last = self._last
        if last is not None and last.query_id == query_id:
            if last.error is not None:
                return {
                    "state": "failed",
                    "query_id": query_id,
                    "error": last.error,
                    "detail": last.detail,
                }
            return {"state": "done", "query_id": query_id, "record": last.record}
        if self._stuck:
            return {"state": "stuck", "query_id": query_id}
        return {"state": "pending", "query_id": query_id}

    def join(self, timeout: float | None = None) -> None:
        thread = self._thread
        if thread is not None:
            thread.join(timeout)


def _record_of(raw: RawSelection) -> dict[str, Any]:
    return {
        "raw_output": raw.raw_output,
        "finish_reason": raw.finish_reason,
        "gen_tokens": raw.gen_tokens,
        "latency_ms": raw.latency_ms,
        "prompt_sha256": raw.prompt_sha256,
        "model_id": raw.model_id,
    }


#: P1-ENG-LOOP-002 §5.2：计量模式下，响应发出后为计数读走客户端已声明而未读的请求体时的套接字超时。
ACCESS_DRAIN_TIMEOUT_S = 10.0
#: 计量模式下单个请求体的读取上限（远大于一帧 JPEG 的 multipart；超出即按未读完记录并关连接）。
ACCESS_MAX_BODY_BYTES = 64 * 1024 * 1024
_DRAIN_CHUNK_BYTES = 64 * 1024


# --- P1-ENG-LOOP-002 AC-7 修订 2(b)：非推理 HTTP / 推理尝试的两批共用累计账 ----------

#: 已签上限（账本 2026-10-07 B-main 完整表）：非推理 HTTP ≤ 200（Air↔板 `/status`、`/result/*`、
#: 其他非推理请求与板内 loopback `/health`，成功与失败一律计），推理尝试 ≤ 335（`POST /query`
#: 每次计 1，含被拒/失败；与其板内 chat 关联为同一次，不重复计）。CLI 只许调低（夹具用）。
NON_INFERENCE_HTTP_LIMIT = 200
INFERENCE_ATTEMPT_LIMIT = 335
#: 账行 `kind` 闭集：前四者计非推理，`query` 计推理尝试，`batch_start` 只是批次起点。
LEDGER_NON_INFERENCE_KINDS: tuple[str, ...] = ("loopback_health", "status", "result", "other")
LEDGER_INFERENCE_KIND = "query"
#: 需在「累计已用 + 本次 1 + 本批预留 ≤ 上限」下才可发生的业务性非推理请求；其余非推理
#: （`status` 等本阶段必需请求）只需「累计已用 + 本次 1 ≤ 上限」，由预留覆盖。
LEDGER_BUSINESS_KINDS: tuple[str, ...] = ("loopback_health", "result")
#: 回包里的预算快照键（只在 llama-server 分支出现）。
HTTP_BUDGET_FIELD = "http_budget"
#: 预算不足时的回包错误码（HTTP 429；请求本身已到达，照常入账）。
ENVELOPE_ERROR = "S_ENVELOPE"


class LedgerRefused(Exception):
    """`--http-ledger` 不可读/损坏/与前一批上限不一致：拒启（退出码 3）。"""


class HttpBudgetLedger:
    """AC-7 修订 2(b)：两服务批次共用的 JSONL 累计账（板端 `--http-ledger`）。

    启动时读入既有行累计已用（上一批次的健康轮询、Air 请求与推理尝试全部带入），写一行
    `batch_start`；此后每个实际请求尝试（loopback 健康轮询的每一次、Air→板每个请求）结束时
    追加一行，带结局（HTTP 码 / 错误 / 超时）与累计值。计数在请求**发生时**完成（回包快照已含
    本次），行在结束时落盘。
    """

    def __init__(
        self,
        path: Path,
        *,
        non_inference_limit: int = NON_INFERENCE_HTTP_LIMIT,
        inference_limit: int = INFERENCE_ATTEMPT_LIMIT,
        reserve: int,
        clock: Callable[[], float] = time.time,
    ):
        self.path = Path(path)
        self.non_inference_limit = int(non_inference_limit)
        self.inference_limit = int(inference_limit)
        self.reserve = int(reserve)
        self._clock = clock
        self._lock = threading.Lock()
        self._seq = 0
        prior_non_inference, prior_inference, batches = self._read_prior()
        self.non_inference_used = prior_non_inference
        self.inference_used = prior_inference
        self.batch = batches + 1
        self._write(
            {
                "kind": "batch_start",
                "batch": self.batch,
                "pid": os.getpid(),
                "started_unix_s": self._clock(),
                "non_inference_limit": self.non_inference_limit,
                "inference_limit": self.inference_limit,
                "reserve": self.reserve,
                "prior_non_inference_used": prior_non_inference,
                "prior_inference_used": prior_inference,
            }
        )

    def _read_prior(self) -> tuple[int, int, int]:
        non_inference = inference = batches = 0
        try:
            text = self.path.read_text(encoding="utf-8") if self.path.exists() else ""
        except OSError as exc:
            raise LedgerRefused(f"--http-ledger unreadable: {exc}") from exc
        for number, line in enumerate(text.splitlines(), start=1):
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise LedgerRefused(f"--http-ledger line {number} is not JSON: {exc}") from exc
            kind = row.get("kind") if isinstance(row, dict) else None
            if kind == "batch_start":
                batches += 1
                if (
                    row.get("non_inference_limit") != self.non_inference_limit
                    or row.get("inference_limit") != self.inference_limit
                ):
                    raise LedgerRefused(
                        "--http-ledger was started with other limits "
                        f"({row.get('non_inference_limit')}/{row.get('inference_limit')}); "
                        "both service batches share one account"
                    )
            elif kind in LEDGER_NON_INFERENCE_KINDS:
                non_inference += 1
            elif kind == LEDGER_INFERENCE_KIND:
                inference += 1
            else:
                raise LedgerRefused(f"--http-ledger line {number} has unknown kind {kind!r}")
        return non_inference, inference, batches

    def _write(self, row: Mapping[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._snapshot_locked()

    def _snapshot_locked(self) -> dict[str, Any]:
        return {
            "batch": self.batch,
            "non_inference_used": self.non_inference_used,
            "non_inference_limit": self.non_inference_limit,
            "reserve": self.reserve,
            "inference_used": self.inference_used,
            "inference_limit": self.inference_limit,
        }

    def business_room(self) -> bool:
        """下一次业务性非推理请求（健康轮询 / `/result`）可否发生：已用 + 1 + 预留 ≤ 上限。"""
        with self._lock:
            return self.non_inference_used + 1 + self.reserve <= self.non_inference_limit

    def admit(self, kind: str, *, method: str | None = None, path: str | None = None,
              query_id: str | None = None) -> dict[str, Any]:
        """一个已发生的请求尝试入账（计数立即生效）；返回待 `record` 的账行。

        `allowed` 是该请求在预算判据下是否应被服务（Air 请求已到达，不服务也照计）。"""
        if kind not in LEDGER_NON_INFERENCE_KINDS and kind != LEDGER_INFERENCE_KIND:
            raise ValueError(f"unknown ledger kind {kind!r}")
        with self._lock:
            used, inferred = self.non_inference_used, self.inference_used
            if kind == LEDGER_INFERENCE_KIND:
                allowed = (
                    inferred + 1 <= self.inference_limit
                    and used + 1 + self.reserve <= self.non_inference_limit
                )
                self.inference_used += 1
            else:
                room = self.reserve if kind in LEDGER_BUSINESS_KINDS else 0
                allowed = used + 1 + room <= self.non_inference_limit
                self.non_inference_used += 1
            self._seq += 1
            return {
                "kind": kind,
                "batch": self.batch,
                "seq": self._seq,
                "method": method,
                "path": path,
                "query_id": query_id,
                "allowed": bool(allowed),
                "over_limit": (
                    self.inference_used > self.inference_limit
                    if kind == LEDGER_INFERENCE_KIND
                    else self.non_inference_used > self.non_inference_limit
                ),
                "started_unix_s": self._clock(),
                "budget_after": self._snapshot_locked(),
            }

    def record(self, entry: Mapping[str, Any], **outcome: Any) -> None:
        row = dict(entry, finished_unix_s=self._clock(), **outcome)
        with self._lock:
            self._write(row)


class BadResultRequest(ValueError):
    """长轮询 `/result` 请求的 query_id 或参数不合（400 `BAD_REQUEST`）。"""


def parse_result_target(path: str) -> tuple[str, float | None]:
    """AC-7 修订 3：把 `/result/<query_id>[?wait_s=<w>]` 分成 query_id 与等待秒数。

    只认一个 `wait_s`（有限正数且 ≤ `LONG_POLL_MAX_WAIT_S`）；其余参数、重复参数、空 query_id 一律
    `BadResultRequest`。无查询串 → `(query_id, None)`（即时回复，与旧语义相同）。"""
    split = urllib.parse.urlsplit(path)
    if not split.path.startswith("/result/") or split.fragment:
        raise BadResultRequest("not a result target")
    query_id = split.path[len("/result/") :]
    if not query_id:
        raise BadResultRequest("empty query_id")
    if not split.query:
        return query_id, None
    try:
        params = urllib.parse.parse_qs(split.query, keep_blank_values=True, strict_parsing=True)
    except ValueError as exc:
        raise BadResultRequest(f"unparseable query: {exc}") from exc
    if set(params) != {LONG_POLL_PARAM} or len(params[LONG_POLL_PARAM]) != 1:
        raise BadResultRequest(f"only one {LONG_POLL_PARAM} parameter is accepted")
    try:
        wait_s = float(params[LONG_POLL_PARAM][0])
    except ValueError as exc:
        raise BadResultRequest(f"{LONG_POLL_PARAM} is not a number") from exc
    if not math.isfinite(wait_s) or not 0.0 < wait_s <= LONG_POLL_MAX_WAIT_S:
        raise BadResultRequest(f"{LONG_POLL_PARAM} must be finite and in (0, {LONG_POLL_MAX_WAIT_S:g}]")
    return query_id, wait_s


def _result_query_id(path: str | None) -> str | None:
    """账行里的 `/result` query_id：去掉查询串（与其 `POST /query` 按同一 query_id 关联）。"""
    if not isinstance(path, str) or not path.startswith("/result/"):
        return None
    return urllib.parse.urlsplit(path).path[len("/result/") :] or None


def _ledger_kind(method: str | None, path: str | None) -> str:
    """Air→板请求的账行分类：`POST /query` = 推理尝试，其余一律非推理。"""
    if method == "POST" and path == "/query":
        return LEDGER_INFERENCE_KIND
    if method == "GET" and path == "/status":
        return "status"
    if method == "GET" and isinstance(path, str) and path.startswith("/result/"):
        return "result"
    return "other"


class _CountingReader:
    """`rfile` 的计数包装：数实际从套接字消费的字节（不保存正文）。

    R1-1（IR-15：异常调用已传输的部分字节不按 0 计）：`BufferedReader.read(n)`/`readline()`
    在底层读超时/断连时会把本次已取回的部分块连同异常一起丢弃。这里一律以至多一次底层读的
    `read1`/`peek` 逐块取数、取到即计，底层读抛错时此前取到的字节都已入账。
    """

    def __init__(self, raw: Any):
        self._raw = raw
        self.count = 0

    def read1(self, size: int = -1) -> bytes:
        data = self._raw.read1(size)
        self.count += len(data)
        return data

    def read(self, size: int | None = -1) -> bytes:
        parts: list[bytes] = []
        if size is None or size < 0:
            while True:
                chunk = self.read1(_DRAIN_CHUNK_BYTES)
                if not chunk:
                    break
                parts.append(chunk)
            return b"".join(parts)
        remaining = size
        while remaining > 0:
            chunk = self.read1(remaining)
            if not chunk:
                break
            parts.append(chunk)
            remaining -= len(chunk)
        return b"".join(parts)

    def readline(self, size: int | None = -1) -> bytes:
        parts: list[bytes] = []
        total = 0
        while size is None or size < 0 or total < size:
            peeked = self._raw.peek(1)  # 缓冲为空时至多一次底层读；抛错时本行此前取到的已入账
            if not peeked:
                break
            window = len(peeked) if size is None or size < 0 else min(len(peeked), size - total)
            newline = peeked.find(b"\n", 0, window)
            take = newline + 1 if newline >= 0 else window
            chunk = self.read1(take)  # take ≤ 缓冲中已有字节：不触发底层读
            parts.append(chunk)
            total += len(chunk)
            if newline >= 0 or not chunk:
                break
        return b"".join(parts)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._raw, name)


class _CountingSocketWriter(io.BufferedIOBase):
    """计量模式的 `wfile`：直接对套接字逐次 `send()`，按每次返回值累加计数。

    R1-1（IR-15）：`socket.sendall` 在部分字节已交给内核后抛 `BrokenPipeError`/
    `ConnectionResetError` 时不报告已发字节数；这里逐次 `send` 取到即计，抛错时
    `count` 即实际交给套接字的字节。语义与 `socketserver._SocketWriter`（`wbufsize=0`）
    相同：无缓冲、`write` 返回写出的全部长度、`close` 不关套接字。
    """

    def __init__(self, sock: Any):
        self._sock = sock
        self.count = 0

    def writable(self) -> bool:
        return True

    def write(self, data: Any) -> int:
        with memoryview(data) as view, view.cast("B") as octets:
            total = len(octets)
            sent = 0
            while sent < total:
                sent_now = self._sock.send(octets[sent:])
                sent += sent_now
                self.count += sent_now
            return total

    def fileno(self) -> int:
        return self._sock.fileno()


class LanguageRequestHandler(BaseHTTPRequestHandler):
    server_version = "P1EngLoopLanguageServe/1"
    runtime: SingleFlightRuntime  # 由 `build_server` 注入到子类
    #: P1-ENG-LOOP-002：llama-server 分支的附加回包字段（`serve_code_sha256`、`machine`）；
    #: `None` 时回包与旧版逐字相同。
    extra_reply_fields: Mapping[str, Any] | None = None
    #: P1-ENG-LOOP-002 §5.2 / AC-7：逐请求双向字节计量日志（JSONL，不记正文）；`None` 不记，
    #: 且旧 local-hf 分支的读写与回包语义逐字不变。
    access_log: Path | None = None
    #: P1-ENG-LOOP-002 AC-7 修订 2(b)：两批共用的非推理 HTTP / 推理尝试累计账（只在 llama-server
    #: 分支、且与 `access_log` 同时注入）；`None` 时回包与计量语义逐字不变。
    budget: HttpBudgetLedger | None = None
    #: P1-ENG-LOOP-002 AC-7 修订 3：只在 llama-server 分支为真（`/result` 分离参数、有界长轮询）。
    long_poll: bool = False
    _budget_entry: dict[str, Any] | None = None
    _access_lock = threading.Lock()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # 默认实现写 stderr；服务日志由操作单负责，测试里保持安静。
        return

    # --- §5.2 逐请求计量（C1-AC7：坏请求行/未支持方法/提前拒绝/异常路径一律入账） ---

    def setup(self) -> None:
        super().setup()
        if self.access_log is not None:
            self.rfile = _CountingReader(self.rfile)
            self.wfile = _CountingSocketWriter(self.connection)

    def handle_one_request(self) -> None:
        if self.access_log is None:
            super().handle_one_request()
            return
        self._access_begin()
        error: str | None = None
        try:
            super().handle_one_request()
        except BaseException as exc:
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            self._access_finish(error)

    def _access_begin(self) -> None:
        self._access_started_unix_s = time.time()
        self._access_read_start = self.rfile.count
        self._access_write_start = self.wfile.count
        self._access_head_read_end: int | None = None
        self._access_head_write_end: int | None = None
        self._access_status: int | None = None
        self._access_declared: int | None = None
        self._access_declared_valid = False
        self._access_body_read = 0
        self._access_drain_error: str | None = None
        self._budget_entry: dict[str, Any] | None = None
        self.command = None  # type: ignore[assignment]
        self.path = None  # type: ignore[assignment]

    def parse_request(self) -> bool:
        ok = super().parse_request()
        if self.access_log is not None:
            self._access_head_read_end = self.rfile.count
            if ok:
                raw = self.headers.get("Content-Length")
                if raw is None or raw == "":
                    self._access_declared, self._access_declared_valid = 0, True
                else:
                    try:
                        value = int(raw)
                    except ValueError:
                        value = -1
                    if value >= 0:
                        self._access_declared, self._access_declared_valid = value, True
            if ok and self.budget is not None:
                # 计数在请求发生时生效，回包快照已含本次；行在 `_access_finish` 落盘。
                kind = _ledger_kind(self.command, self.path)
                self._budget_entry = self.budget.admit(
                    kind,
                    method=self.command,
                    path=self.path,
                    query_id=(_result_query_id(self.path) if kind == "result" else None),
                )
        return ok

    def send_response(self, code: int, message: str | None = None) -> None:
        if self.access_log is not None:
            self._access_status = int(code)
        super().send_response(code, message)

    def end_headers(self) -> None:
        super().end_headers()
        if self.access_log is not None:
            self._access_head_write_end = self.wfile.count

    def _read_request_body(self, length: int) -> bytes:
        body = self.rfile.read(length)
        if self.access_log is not None:
            self._access_body_read += len(body)
        return body

    def _drain_declared_body(self) -> None:
        """响应发出后：客户端已声明而本请求未读的正文按实际收到的字节读走计数（有界、有超时）。"""
        if not self._access_declared_valid or self._access_declared is None:
            return
        remaining = self._access_declared - self._access_body_read
        if remaining <= 0 or self._access_declared > ACCESS_MAX_BODY_BYTES:
            return
        previous = self.connection.gettimeout()
        try:
            self.connection.settimeout(ACCESS_DRAIN_TIMEOUT_S)
            while remaining > 0:
                chunk = self.rfile.read(min(remaining, _DRAIN_CHUNK_BYTES))
                if not chunk:
                    break
                self._access_body_read += len(chunk)
                remaining -= len(chunk)
        except (OSError, ValueError) as exc:
            self._access_drain_error = f"{type(exc).__name__}: {exc}"
        finally:
            try:
                self.connection.settimeout(previous)
            except OSError:
                pass

    def _access_finish(self, error: str | None) -> None:
        read_total = self.rfile.count - self._access_read_start
        if read_total == 0 and self._access_status is None and error is None:
            return  # 连接上没有任何请求字节（空连接/保活结束）：不是一个请求
        if error is None:
            self._drain_declared_body()
        read_total = self.rfile.count - self._access_read_start
        written_total = self.wfile.count - self._access_write_start
        head_read = (
            read_total
            if self._access_head_read_end is None
            else self._access_head_read_end - self._access_read_start
        )
        head_written = (
            written_total
            if self._access_head_write_end is None
            else self._access_head_write_end - self._access_write_start
        )
        complete = bool(
            self._access_declared_valid
            and self._access_declared is not None
            and self._access_body_read == self._access_declared
        )
        finished = time.time()
        if self.budget is not None:
            entry = self._budget_entry
            if entry is None:
                # 请求行/头没解析成功（坏请求行、头过多等）：同样是一次实际的非推理请求尝试。
                entry = self.budget.admit("other", method=self.command, path=self.path)
            self.budget.record(
                entry,
                status=self._access_status,
                error=error if error is not None else self._access_drain_error,
                request_body_bytes=int(read_total - head_read),
                response_body_bytes=int(written_total - head_written),
            )
        line = json.dumps(
            {
                "method": self.command,
                "path": self.path,
                "status": self._access_status,
                "request_head_bytes": int(head_read),
                "request_body_bytes": int(read_total - head_read),
                "request_declared_body_bytes": self._access_declared if self._access_declared_valid else None,
                "request_body_complete": complete,
                "response_head_bytes": int(head_written),
                "response_body_bytes": int(written_total - head_written),
                "error": error if error is not None else self._access_drain_error,
                "started_unix_s": self._access_started_unix_s,
                "finished_unix_s": finished,
            },
            sort_keys=True,
        )
        with self._access_lock, Path(self.access_log).open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    # --- 端点 ---

    def _reply(self, status: int, document: dict[str, Any]) -> None:
        if self.extra_reply_fields:
            document = dict(document, **self.extra_reply_fields)
        document = dict(document, model_identity=self.runtime.model_identity())
        if self.budget is not None:
            entry = self._budget_entry
            document[HTTP_BUDGET_FIELD] = (
                dict(entry["budget_after"]) if entry is not None else self.budget.snapshot()
            )
        payload = json.dumps(document).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _budget_refused(self) -> bool:
        """AC-7 修订 2(b) 服务端兜底：本请求在预算判据下不应发生 → 429 `S_ENVELOPE`（已照计）。"""
        entry = self._budget_entry
        if self.budget is None or entry is None or entry["allowed"]:
            return False
        self._reply(429, {"accepted": False, "error": ENVELOPE_ERROR, "kind": entry["kind"]})
        return True

    def do_GET(self) -> None:  # noqa: N802
        if self._budget_refused():
            return
        if self.path == "/status":
            self._reply(200, self.runtime.status())
            return
        if self.path.startswith("/result/"):
            if self.long_poll:
                try:
                    query_id, wait_s = parse_result_target(self.path)
                except BadResultRequest as exc:
                    self._reply(400, {"error": "BAD_REQUEST", "detail": str(exc)})
                    return
                if wait_s is None:
                    self._reply(200, self.runtime.result(query_id))
                    return
                document = self.runtime.result_wait(query_id, wait_s)
                self._reply(200, dict(document, **{LONG_POLL_PARAM: wait_s}))
                return
            query_id = self.path[len("/result/") :]
            self._reply(200, self.runtime.result(query_id))
            return
        self._reply(404, {"error": "unknown endpoint"})

    def do_POST(self) -> None:  # noqa: N802
        if self.access_log is not None:
            # 计量模式：Content-Length 不可解析 → 400 并关连接（实际收到的正文无从界定，记
            # `request_body_complete: false`）；超上限同样不读；其余先按声明长度读入正文再分派，
            # 未知路径的正文也计入实际字节。
            if not self._access_declared_valid or self._access_declared is None or self._access_declared > ACCESS_MAX_BODY_BYTES:
                self.close_connection = True
                self._reply(400, {"accepted": False, "error": "BAD_REQUEST"})
                return
            body = self._read_request_body(self._access_declared)
            if self._budget_refused():
                return
            if self.path != "/query":
                self._reply(404, {"error": "unknown endpoint"})
                return
        else:
            if self.path != "/query":
                self._reply(404, {"error": "unknown endpoint"})
                return
            length = int(self.headers.get("Content-Length", "0") or 0)
            body = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")
        try:
            image, fields = parse_multipart(body, content_type)
            expected = json.loads(fields["expected_model_identity"]) if "expected_model_identity" in fields else None
            if expected is not None and not isinstance(expected, dict):
                raise ValueError("expected_model_identity must be an object")
        except ValueError:
            self._reply(400, {"accepted": False, "error": "BAD_REQUEST"})
            return
        query_id = fields.get("query_id", "")
        if self._budget_entry is not None:
            # 推理尝试与其后 `/result/<query_id>` 轮询在账上按 `query_id` 关联。
            self._budget_entry["query_id"] = query_id or None
        surface = fields.get("surface", "")
        if not query_id or not surface or not image:
            self._reply(400, {"accepted": False, "error": "BAD_REQUEST"})
            return
        outcome = self.runtime.submit(
            query_id, image, surface, fields.get("g4", "0") == "1", expected
        )
        self._reply(200 if outcome.get("accepted") else 409, outcome)


def build_server(
    runtime: SingleFlightRuntime,
    *,
    host: str = "127.0.0.1",
    port: int = 0,
    extra_reply_fields: Mapping[str, Any] | None = None,
    access_log: Path | None = None,
    budget: HttpBudgetLedger | None = None,
    long_poll: bool = False,
) -> HTTPServer:
    if budget is not None and access_log is None:
        raise ValueError("budget ledger requires the access log (metering mode)")
    attributes: dict[str, Any] = {"runtime": runtime}
    if long_poll:
        attributes["long_poll"] = True
    if extra_reply_fields is not None:
        attributes["extra_reply_fields"] = dict(extra_reply_fields)
    if access_log is not None:
        attributes["access_log"] = Path(access_log)
    if budget is not None:
        attributes["budget"] = budget
    handler = type("BoundLanguageRequestHandler", (LanguageRequestHandler,), attributes)
    return HTTPServer((host, port), handler)


# --- P1-ENG-LOOP-002 A2(a)：`--backend llama-server` 分支 -----------------------

EXIT_REFUSED = 3
EXIT_LOAD_FAILURE = 4
EXIT_LLAMA_EXITED = 5
EXIT_ENVELOPE = 6
#: `<llama-bin> --version` 的子进程上限（不加载模型）。
VERSION_TIMEOUT_S = 30.0
#: 缺省就绪等待上限与其硬上限（有界；Jetson 冷加载 Q4 GGUF 预留余量）。
DEFAULT_LLAMA_READY_TIMEOUT_S = 300.0
MAX_LLAMA_READY_TIMEOUT_S = 1800.0
#: 停子进程：terminate 后等待上限，过时 kill。
CHILD_TERMINATE_WAIT_S = 10.0
#: A2(a)：构建号解析式（多行模式）——旧整数格式 `version: <整数> …`（原式不变）。
VERSION_PATTERN = re.compile(r"^version: (\d+) ", re.MULTILINE)
#: AC-7 修订 5：语义版本格式 `version: <语义版本> (build <整数>, commit <文本>)`，整行为界，取括号内 build。
SEMVER_VERSION_PATTERN = re.compile(
    r"^version: [0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)? "
    r"\(build ([0-9]+), commit [^\s(),]+\)\Z"
)
#: 版本身份候选行：行首 `version:`（两种格式都须恰好一行；缺行/重复/冲突一律拒启）。
VERSION_LINE_PREFIX = "version:"
#: runtime_build 值域 `^b[0-9]{1,7}$` 的构建号部分（与 `controller.language_bridge` 同域）。
BUILD_NUMBER_PATTERN = re.compile(r"^[0-9]{1,7}$")
#: `--expect-assets` 必须给出的键（AC-16 资产核实产物的子集；其余键不读）。
EXPECT_ASSET_KEYS: tuple[str, ...] = (
    "weights_sha256",
    "mmproj_sha256",
    "runtime_binary_sha256",
    "runtime_build",
    "quantization",
)
_LLAMA_ONLY_OPTIONS: tuple[tuple[str, str], ...] = (
    ("--llama-bin", "llama_bin"),
    ("--weights", "weights"),
    ("--mmproj", "mmproj"),
    ("--llama-port", "llama_port"),
    ("--expect-assets", "expect_assets"),
    ("--access-log", "access_log"),
    ("--http-ledger", "http_ledger"),
    ("--non-inference-reserve", "non_inference_reserve"),
    ("--llama-ready-timeout-s", "llama_ready_timeout_s"),
    ("--llama-request-timeout-s", "llama_request_timeout_s"),
    ("--non-inference-limit", "non_inference_limit"),
    ("--inference-limit", "inference_limit"),
)
#: llama-server 分支必需的选项（`_LLAMA_ONLY_OPTIONS` 的前缀）。
_LLAMA_REQUIRED_COUNT = 8
_LOCAL_HF_ONLY_OPTIONS: tuple[tuple[str, str], ...] = (
    ("--model-source", "model_source"),
    ("--adapter-dir", "adapter_dir"),
    ("--model-form", "model_form"),
)


class StartRefused(Exception):
    """llama-server 分支启动前核对不过：拒启，且不起 `llama-server` 子进程。"""


class _Terminate(BaseException):
    """SIGTERM → 跳出服务循环（继承 BaseException：不被 socketserver 的 `except Exception` 吞掉）。"""


def _raise_terminate(signum: int, frame: Any) -> None:  # noqa: ARG001
    raise _Terminate()


@dataclass
class LlamaPreflight:
    adapter: Any
    serve_code_sha256: str
    machine: str


#: AC-7 修订 2(a)（CHANGE:1，用户选 A）：llama 分支逐字固定的十项资源旗标（完整闭集，不删成
#: 子集；与唯一既有板上原读数的显式执行栈同一组）。原读数只覆盖该配置，不证明本代码/板端已可运行。
LLAMA_RESOURCE_FLAGS: tuple[str, ...] = (
    "--parallel", "1",
    "--ctx-size", "2048",
    "--n-gpu-layers", "99",
    "--fit", "off",
    "--no-warmup",
    "--no-webui",
    "--no-cache-prompt",
    "--cache-ram", "0",
    "--cache-reuse", "0",
    "--offline",
)


def llama_server_command(
    llama_bin: Path, weights: Path, mmproj: Path, port: int
) -> list[str]:
    """集中构造 `llama-server` 命令行（只绑 127.0.0.1）。

    原 `-m`/`--mmproj`/`--host 127.0.0.1`/`--port` 保留，其后逐字接 AC-7 修订 2(a) 的十项资源旗标；
    prompt/schema/decode、三文件身份与 local-hf 路径不受影响。
    """
    return [
        str(llama_bin),
        "-m",
        str(weights),
        "--mmproj",
        str(mmproj),
        "--host",
        "127.0.0.1",
        "--port",
        str(int(port)),
        *LLAMA_RESOURCE_FLAGS,
    ]


def parse_runtime_build(output: str) -> str:
    """AC-7 修订 5：从 `--version` 原流取 `b<构建号>`；任一不符即 `StartRefused`（无缺省值）。

    只认行首 `version:` 的版本身份行，且必须恰好一行：旧整数格式 `version: <整数> …` 取该整数；
    语义版本格式 `version: <语义版本> (build <整数>, commit <文本>)` 整行匹配时取括号内 build 整数
    （原文本、版本号、commit 不改写，commit 不作源码认证）。缺行、重复或冲突行、缺明确 build、
    构建号超出 `^b[0-9]{1,7}$` 值域一律拒启。
    """
    lines = [line for line in output.splitlines() if line.startswith(VERSION_LINE_PREFIX)]
    if not lines:
        raise StartRefused("--version output has no 'version:' line")
    if len(lines) > 1:
        raise StartRefused(f"--version output has {len(lines)} 'version:' lines (duplicate or conflicting)")
    line = lines[0]
    legacy = VERSION_PATTERN.match(line)
    semver = SEMVER_VERSION_PATTERN.match(line)
    if legacy is not None:
        build = legacy.group(1)
    elif semver is not None:
        build = semver.group(1)
    else:
        raise StartRefused(
            f"--version line {line!r} is neither 'version: <n> ' nor "
            "'version: <semver> (build <n>, commit <text>)'"
        )
    if BUILD_NUMBER_PATTERN.match(build) is None:
        raise StartRefused(f"--version build {build!r} outside ^b[0-9]{{1,7}}$")
    return f"b{build}"


def read_runtime_build(llama_bin: Path, *, timeout_s: float = VERSION_TIMEOUT_S) -> str:
    """以子进程跑 `<llama-bin> --version`（不加载模型），按 `parse_runtime_build` 取 `b<数字>`。"""
    try:
        completed = subprocess.run(
            [str(llama_bin), "--version"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_s,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise StartRefused(f"cannot run {llama_bin} --version: {type(exc).__name__}: {exc}") from exc
    output = completed.stdout.decode("utf-8", errors="replace")
    if completed.returncode != 0:
        raise StartRefused(f"{llama_bin} --version exited with {completed.returncode}")
    try:
        return parse_runtime_build(output)
    except StartRefused as exc:
        raise StartRefused(f"{llama_bin} {exc}") from exc


def _read_expect_assets(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StartRefused(f"--expect-assets unreadable: {exc}") from exc
    if not isinstance(document, dict):
        raise StartRefused("--expect-assets must be a JSON object")
    missing = [key for key in EXPECT_ASSET_KEYS if key not in document]
    if missing:
        raise StartRefused(f"--expect-assets lacks {missing}")
    return document


def llama_preflight(arguments: argparse.Namespace) -> LlamaPreflight:
    """A2(a)：启动 `llama-server` 之前的全部核对；任一不符即 `StartRefused`。"""
    from controller.language_bridge import QUANTIZATIONS
    from tools.eng_loop2 import deploy_digest, llama_adapter

    actual: dict[str, str] = {}
    for key, path in (
        ("weights_sha256", arguments.weights),
        ("mmproj_sha256", arguments.mmproj),
        ("runtime_binary_sha256", arguments.llama_bin),
    ):
        try:
            actual[key] = deploy_digest.sha256_path(Path(path))
        except OSError as exc:
            raise StartRefused(f"cannot hash {key} source {path}: {exc}") from exc
    actual["runtime_build"] = read_runtime_build(Path(arguments.llama_bin))
    expected = _read_expect_assets(arguments.expect_assets)
    for key in ("weights_sha256", "mmproj_sha256", "runtime_binary_sha256", "runtime_build"):
        if expected[key] != actual[key]:
            raise StartRefused(
                f"{key} mismatch: computed {actual[key]!r}, --expect-assets {expected[key]!r}"
            )
    quantization = expected["quantization"]
    if quantization not in QUANTIZATIONS:
        raise StartRefused(f"quantization {quantization!r} not in {list(QUANTIZATIONS)}")
    try:
        schema = deploy_digest.load_schema(PROJECT_ROOT)
        serve_code_sha256 = deploy_digest.deploy_digest(PROJECT_ROOT)
    except (deploy_digest.DeployDigestError, OSError, ValueError) as exc:
        raise StartRefused(f"deploy closed set invalid under {PROJECT_ROOT}: {exc}") from exc
    try:
        adapter = llama_adapter.LlamaServerAdapter(
            f"http://127.0.0.1:{int(arguments.llama_port)}",
            schema=schema,
            weights_sha256=actual["weights_sha256"],
            mmproj_sha256=actual["mmproj_sha256"],
            runtime_binary_sha256=actual["runtime_binary_sha256"],
            runtime_build=actual["runtime_build"],
            quantization=quantization,
            request_timeout_s=arguments.llama_request_timeout_s,
        )
    except SelectorError as exc:
        raise StartRefused(f"model identity invalid: {exc}") from exc
    return LlamaPreflight(adapter, serve_code_sha256, platform.node())


class ReadyFailure(Exception):
    """就绪失败：`envelope=False` → 退出码 4（load_failure），`True` → 退出码 6（S-ENVELOPE）。"""

    def __init__(self, reason: str, *, envelope: bool = False):
        super().__init__(reason)
        self.reason = reason
        self.envelope = envelope


def _wait_llama_ready(
    child: subprocess.Popen,
    base_url: str,
    timeout_s: float,
    *,
    poll_s: float = 0.25,
    budget: HttpBudgetLedger | None = None,
) -> None:
    """轮询 `/health` 到 200；不就绪抛 `ReadyFailure`。

    AC-7 修订 2(b)：每次健康轮询**发出前**核「已用 + 1 + 本批预留 ≤ 上限」，不足即停（S-ENVELOPE，
    不发预算外请求）；每次实际尝试（200 / 非 200 / 连接失败 / 超时）各记一行结局。就绪上限与间隔
    仍是现行 `DEFAULT_LLAMA_READY_TIMEOUT_S`/0.25 s；预算可使等待更早结束。"""
    from tools.eng_loop2 import llama_adapter

    deadline = time.monotonic() + timeout_s
    while True:
        if child.poll() is not None:
            raise ReadyFailure(f"llama-server exited with {child.returncode} before ready")
        remaining = deadline - time.monotonic()
        if remaining <= 0.0:
            raise ReadyFailure(f"llama-server not ready within {timeout_s:g} s")
        if budget is not None and not budget.business_room():
            snapshot = budget.snapshot()
            raise ReadyFailure(
                f"{ENVELOPE_ERROR}: next health poll would exceed non-inference HTTP "
                f"{snapshot['non_inference_used']}+1+reserve {snapshot['reserve']} > "
                f"{snapshot['non_inference_limit']}",
                envelope=True,
            )
        entry = (
            budget.admit("loopback_health", method="GET", path=llama_adapter.HEALTH_PATH)
            if budget is not None
            else None
        )
        status, error = llama_adapter.health_attempt(base_url, timeout_s=min(2.0, remaining))
        if entry is not None:
            budget.record(entry, status=status, error=error)
        if status == 200:
            return
        time.sleep(min(poll_s, max(0.0, deadline - time.monotonic())))


def _stop_child(child: subprocess.Popen) -> None:
    if child.poll() is not None:
        return
    child.terminate()
    try:
        child.wait(CHILD_TERMINATE_WAIT_S)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait(CHILD_TERMINATE_WAIT_S)


def _refuse(message: str, code: int) -> int:
    print(f"language-serve: {message}", file=sys.stderr, flush=True)
    return code


def _main_llama(parser: argparse.ArgumentParser, arguments: argparse.Namespace) -> int:
    given_local = [flag for flag, name in _LOCAL_HF_ONLY_OPTIONS if getattr(arguments, name) is not None]
    if given_local:
        parser.error(f"{', '.join(given_local)} only apply to --backend local-hf")
    missing = [
        flag
        for flag, name in _LLAMA_ONLY_OPTIONS[:_LLAMA_REQUIRED_COUNT]
        if getattr(arguments, name) is None
    ]
    if missing:
        parser.error("the following arguments are required: " + ", ".join(missing))
    ready_timeout = (
        DEFAULT_LLAMA_READY_TIMEOUT_S
        if arguments.llama_ready_timeout_s is None
        else float(arguments.llama_ready_timeout_s)
    )
    if not 0.0 < ready_timeout <= MAX_LLAMA_READY_TIMEOUT_S:
        parser.error(f"--llama-ready-timeout-s must be in (0, {MAX_LLAMA_READY_TIMEOUT_S:g}]")
    from tools.eng_loop2 import llama_adapter

    if arguments.llama_request_timeout_s is None:
        arguments.llama_request_timeout_s = llama_adapter.DEFAULT_REQUEST_TIMEOUT_S
    if not 0.0 < float(arguments.llama_request_timeout_s) < float(arguments.t_hard_s):
        parser.error("--llama-request-timeout-s must be in (0, --t-hard-s)")
    if not 0 < int(arguments.llama_port) < 65536:
        parser.error("--llama-port must be in 1..65535")
    if int(arguments.llama_port) == int(arguments.port):
        parser.error("--llama-port must differ from --port")
    non_inference_limit = (
        NON_INFERENCE_HTTP_LIMIT if arguments.non_inference_limit is None else int(arguments.non_inference_limit)
    )
    inference_limit = (
        INFERENCE_ATTEMPT_LIMIT if arguments.inference_limit is None else int(arguments.inference_limit)
    )
    if not 1 <= non_inference_limit <= NON_INFERENCE_HTTP_LIMIT:
        parser.error(f"--non-inference-limit must be in 1..{NON_INFERENCE_HTTP_LIMIT} (may only be lowered)")
    if not 1 <= inference_limit <= INFERENCE_ATTEMPT_LIMIT:
        parser.error(f"--inference-limit must be in 1..{INFERENCE_ATTEMPT_LIMIT} (may only be lowered)")
    if not 0 <= int(arguments.non_inference_reserve) < non_inference_limit:
        parser.error("--non-inference-reserve must be in 0..(--non-inference-limit - 1)")

    try:
        preflight = llama_preflight(arguments)
        access_log = Path(arguments.access_log)
        try:
            access_log.parent.mkdir(parents=True, exist_ok=True)
            access_log.open("a", encoding="utf-8").close()
        except OSError as exc:
            raise StartRefused(f"--access-log not writable: {exc}") from exc
        try:
            Path(arguments.http_ledger).parent.mkdir(parents=True, exist_ok=True)
            budget = HttpBudgetLedger(
                Path(arguments.http_ledger),
                non_inference_limit=non_inference_limit,
                inference_limit=inference_limit,
                reserve=int(arguments.non_inference_reserve),
            )
        except LedgerRefused as exc:
            raise StartRefused(str(exc)) from exc
        except OSError as exc:
            raise StartRefused(f"--http-ledger not writable: {exc}") from exc
    except StartRefused as exc:
        return _refuse(f"refused to start: {exc}", EXIT_REFUSED)
    if not budget.business_room():
        # 起 `llama-server`（= 一次 GGUF 加载）之前就没有一次健康轮询的余量：不加载，直接 S-ENVELOPE。
        snapshot = budget.snapshot()
        return _refuse(
            f"{ENVELOPE_ERROR}: no room for one health poll before loading "
            f"({snapshot['non_inference_used']}+1+reserve {snapshot['reserve']} > {snapshot['non_inference_limit']})",
            EXIT_ENVELOPE,
        )

    if arguments.scratch is not None:
        Path(arguments.scratch).mkdir(parents=True, exist_ok=True)
    images = Path(
        tempfile.mkdtemp(
            prefix="language-serve-images-",
            dir=str(arguments.scratch) if arguments.scratch is not None else None,
        )
    )
    base_url = f"http://127.0.0.1:{int(arguments.llama_port)}"
    child: subprocess.Popen | None = None
    server: HTTPServer | None = None
    previous_sigterm = signal.signal(signal.SIGTERM, _raise_terminate)
    try:
        # 前台子进程（同进程组，不 daemon 化/后台化）；输出直通本进程的终端。
        child = subprocess.Popen(
            llama_server_command(
                arguments.llama_bin, arguments.weights, arguments.mmproj, arguments.llama_port
            ),
            stdin=subprocess.DEVNULL,
        )
        try:
            _wait_llama_ready(child, base_url, ready_timeout, budget=budget)
        except ReadyFailure as failure:
            if failure.envelope:
                return _refuse(failure.reason, EXIT_ENVELOPE)
            return _refuse(f"load_failure: {failure.reason}", EXIT_LOAD_FAILURE)
        runtime = SingleFlightRuntime(
            preflight.adapter,
            scratch_directory=images,
            t_hard_s=arguments.t_hard_s,
            delete_images_after_run=True,
        )
        server = build_server(
            runtime,
            host=arguments.host,
            port=arguments.port,
            extra_reply_fields={
                "serve_code_sha256": preflight.serve_code_sha256,
                "machine": preflight.machine,
            },
            access_log=Path(arguments.access_log),
            budget=budget,
            long_poll=True,
        )
        server.timeout = 0.5
        print(
            f"language-serve listening on http://{arguments.host}:{server.server_port}"
            f" (llama-server pid {child.pid} on 127.0.0.1:{int(arguments.llama_port)})",
            flush=True,
        )
        while True:
            if child.poll() is not None:
                return _refuse(
                    f"llama-server exited with {child.returncode} while serving", EXIT_LLAMA_EXITED
                )
            server.handle_request()
    except (KeyboardInterrupt, _Terminate):
        return 0
    finally:
        if server is not None:
            server.server_close()
        if child is not None:
            _stop_child(child)
        shutil.rmtree(images, ignore_errors=True)
        signal.signal(signal.SIGTERM, previous_sigterm)


# --- 入口 --------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="P1-ENG-LOOP-001 单工语言选框推理服务（5060 侧）"
    )
    parser.add_argument(
        "--backend",
        choices=("local-hf", "llama-server"),
        default="local-hf",
        help="local-hf（缺省，P1-ENG-LOOP-001 旧路径）或 llama-server（P1-ENG-LOOP-002 A2）",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument(
        "--model-source",
        type=Path,
        default=None,
        help="合并模型目录，或 base 权重目录（配 --adapter-dir）；local-hf 必需",
    )
    parser.add_argument("--adapter-dir", type=Path, default=None)
    parser.add_argument(
        "--model-form", choices=("c2-merged", "c2-adapter", "base"), default=None,
        help="local-hf 必需",
    )
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--scratch", type=Path, default=None,
        help="local-hf 必需；llama-server 可选（单次推理图像的临时目录父级，结束即删）",
    )
    parser.add_argument("--t-hard-s", type=float, default=DEFAULT_T_HARD_S)
    llama = parser.add_argument_group("llama-server 分支（P1-ENG-LOOP-002 A2(a)）")
    llama.add_argument("--llama-bin", type=Path, default=None)
    llama.add_argument("--weights", type=Path, default=None, help="GGUF 权重")
    llama.add_argument("--mmproj", type=Path, default=None, help="mmproj GGUF")
    llama.add_argument("--llama-port", type=int, default=None)
    llama.add_argument("--expect-assets", type=Path, default=None)
    llama.add_argument("--access-log", type=Path, default=None)
    llama.add_argument("--llama-ready-timeout-s", type=float, default=None)
    llama.add_argument("--llama-request-timeout-s", type=float, default=None)
    llama.add_argument(
        "--http-ledger", type=Path, default=None,
        help="两服务批次共用的非推理 HTTP / 推理尝试累计账（JSONL；AC-7 修订 2(b)）",
    )
    llama.add_argument(
        "--non-inference-reserve", type=int, default=None,
        help="本批为必需 /status 等预留、业务性请求（健康轮询、/result）不得占用的非推理 HTTP 次数",
    )
    llama.add_argument("--non-inference-limit", type=int, default=None, help="只许调低（缺省 200）")
    llama.add_argument("--inference-limit", type=int, default=None, help="只许调低（缺省 335）")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.backend == "llama-server":
        return _main_llama(parser, arguments)
    given_llama = [flag for flag, name in _LLAMA_ONLY_OPTIONS if getattr(arguments, name) is not None]
    if given_llama:
        parser.error(f"{', '.join(given_llama)} only apply to --backend llama-server")
    missing = [
        flag
        for flag, value in (
            ("--model-source", arguments.model_source),
            ("--model-form", arguments.model_form),
            ("--scratch", arguments.scratch),
        )
        if value is None
    ]
    if missing:
        parser.error("the following arguments are required: " + ", ".join(missing))

    from controller.language_selector import load_local_adapter

    adapter = load_local_adapter(
        source=arguments.model_source,
        adapter_dir=arguments.adapter_dir,
        device=arguments.device,
        model_form=arguments.model_form,
        output_directory=arguments.scratch / "queries",
    )
    runtime = SingleFlightRuntime(
        adapter,
        scratch_directory=arguments.scratch / "images",
        t_hard_s=arguments.t_hard_s,
    )
    server = build_server(runtime, host=arguments.host, port=arguments.port)
    print(f"language-serve listening on http://{arguments.host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
