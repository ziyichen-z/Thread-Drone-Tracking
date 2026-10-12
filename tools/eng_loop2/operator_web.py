"""P1-ENG-LOOP-002 OpsK1K2K3K4：本机操作网页（W1–W5，AC-5 修订 1 / AC-10 修订 3 / AC-11 修订 1）。

合同来源：同名提案「OPS九题答复落实」§2（W1–W5）与 §3（逐文件闭集）。参照
`docs/evidence/P1-ENG-LOOP-001-operator-web.py` 的做法（只读、不启动旧载体、不继承其动作与预算）。

要点（逐条对应合同，不放宽）：

* **W1 载体与动作闭集**：只监听 `127.0.0.1`，纯标准库，页面/脚本/样式内嵌，无外部资源。按钮闭集
  = 当前计划步骤的「发送」「跳过（不在画面）」、逐候选「确认序号」、「拒绝」、安全中止「停止会话」、
  收尾「通过/失败/受阻」。没有自由指令/Δ/intent/顺序编辑、verify、confirm-lost、dismiss、任意路径
  或重试按钮。release 只由 runner（`play_ops`）按计划发；停止会话不代按 Unity 停止。
* **W2 画面与令牌绑定**：呈现快照绑定 session/状态/reason/epoch/query_id/result_id/源 frame_id/
  request_id、候选序号与预览图身份（文件名 + 字节 sha256）。浏览器解码成功后先回报「已显示」，确认时
  提交所看图身份；服务端重读字节核 sha、核与当时快照一致，旧页面不能重绑新结果。同一 result_id 的
  预览字节或呈现时刻在两次读取间变化 → 该结果永久不可确认（不用后到结果替换原图）。
* **W3 原时窗倒计时**：截止 = min(`query_unix_s` + T_ret + T_conf, 结果信封 `issued_unix_s` + T_conf)，
  另示 `latest − 源帧 ≤ K_ret + K_conf`。数据缺失/非有限/回退/不一致即「不可确认」；轮询/刷新/
  重开页不续期；到期只禁确认，不造事件、不默认任何动作。会话自己的检查点仍是终判。
* **W4 防重复与未知结果**：全局同时只允许一条在途提交（runner 与网页共用 `Submitter`）；同一绑定
  已提交过即拒绝（旧视图/刷新重放/多标签页）。每次调用前先落 request_id 与绑定；超时、WRITER_BUSY
  或缺回执一律记 UNKNOWN、停依赖推进（由调度器处理），不换 id 重发、不自动重试；迟到回执只按原 id
  核清并记录，不借此恢复流程。stop 每个会话至多发一次（计划停止与中止按钮竞态也只发一次）。
  STOP/故障/中断/结果未知一发生，`Submitter.seal` 即在同一把锁内**不可逆**封住该会话的业务动作
  （发送/跳过/确认/拒绝/release；runner 与网页同一通道），此后只放行原合法 stop（至多一次）与状态读取；
  迟到回执或状态不解封（C6@OpsK1K2K3K4 C6-1）。
* **W5 原流与本机访问**：`ops-web.jsonl` 逐条记呈现快照、浏览器显示成功、点击/绑定/时间、实际 CLI
  argv/退出码/stdout/stderr/request_id/回执、计划步骤与跳过/未执行原因。只读本机 runtime 与会话
  目录，不访问板端 `/status`。POST 须带服务生成 nonce、Host/Origin 为本机；预览只从本会话 `previews/`
  按绑定文件名读，实时画面只从 `runtime/frames/` 按 `latest.json` 指向读。

本文件不读真值、评分产物或几何，不导入评分/几何工具（AC-9 修订 1）；不写桥文件/锁，所有动作走
`python -m controller.language_loop <action>` 原 CLI（AC-5 修订 1）。
"""

from __future__ import annotations

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
import uuid
from pathlib import Path
from typing import Any, Callable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - 直接以脚本运行时
    sys.path.insert(0, str(REPO_ROOT))

from controller import language_bridge as bridge  # noqa: E402
from controller.language_loop import (  # noqa: E402
    RESULTS_FILE,
    SESSION_JOURNAL,
    T_CONF_S,
    KReceipt,
)

HOST = "127.0.0.1"
DEFAULT_PORT = 8772
POLL_S = 0.1
STALE_S = 1.0
CLI_TIMEOUT_S = 30.0
PRESENTATION_SKEW_S = 1.0
MAX_BODY = 4096
MAX_PREVIEW_BYTES = 8_000_000
MAX_FRAME_BYTES = 8_000_000
FEEDBACK_TEXT_MAX = 2000
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"
OPS_LOG = "ops-web.jsonl"
FEEDBACK_LABELS = {"PASS": "通过", "FAIL": "失败", "BLOCKED": "受阻"}
#: W1 按钮闭集（页面与服务端同一份）。
BUTTONS = ("send", "skip", "confirm", "reject", "stop", "feedback")
#: 语言会话原 CLI 动作（本工具只会用到其中 ask/respecify/confirm/reject/release/stop）。
CLI_ACTIONS = frozenset({"ask", "respecify", "confirm", "reject", "release", "stop"})
PREVIEW_NAME = re.compile(r"^[0-9]+-[A-Za-z0-9._-]+\.png$")
FRAME_NAME = re.compile(r"^frame_[0-9]{10}\.jpg$")
SHA_HEX = re.compile(r"^[0-9a-f]{64}$")

#: 常驻会话 `_action_ask` / `_action_respecify` 允许的状态（controller/language_loop.py 原表；只读引用）。
ASK_STATES = frozenset({"IDLE", "QUERYING", "AWAITING_CONFIRMATION", "LOST", "REINIT_REQUIRED", "TRACKING", "SUSPECTED"})
RESPECIFY_STATES = frozenset(
    {"IDLE", "QUERYING", "AWAITING_CONFIRMATION", "SUSPECTED", "LOST", "REINIT_REQUIRED", "TRACKING"}
)
#: CLI 退出码中能证明「未写请求」的两种（language_loop.main：2 = 参数/守卫拒绝，4 = WRITER_BUSY）。
NOT_WRITTEN_EXITS = frozenset({2, 4})


# --- 小工具 -------------------------------------------------------------------


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    return str(value)


def png_dimensions(data: bytes) -> tuple[int, int] | None:
    """PNG 签名 + 非零尺寸 IHDR（浏览器仍须实际解码成功）。"""
    if len(data) < 24 or data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return (width, height) if width > 0 and height > 0 else None


def legal_session_actions(state: Mapping[str, Any] | None) -> set[str]:
    """会话原表允许的 CLI 动作子集（本工具闭集内）；`backend_fatal` 只留 stop，TERMINAL 为空。"""
    if not state:
        return set()
    name, reason = state.get("state"), state.get("reason")
    if name == "TERMINAL":
        return set()
    if reason == "backend_fatal":
        return {"stop"}
    legal = {"stop"}
    if name in ASK_STATES:
        legal.add("ask")
    if name in RESPECIFY_STATES:
        legal.add("respecify")
    if name == "AWAITING_CONFIRMATION":
        legal.update({"confirm", "reject"})
    if name == "TRACKING":
        legal.add("release")
    return legal


def load_receipt(path: Path) -> dict[str, float]:
    """K 收据经生产 `KReceipt.from_document` 校验后取门值（不手抄）。"""
    receipt = KReceipt.from_document(json.loads(Path(path).read_text(encoding="utf-8")))
    return {
        "hz": receipt.hz,
        "k_ret": receipt.k_ret,
        "k_conf": receipt.k_conf,
        "t_ret_s": receipt.t_ret_s,
        "t_conf_s": T_CONF_S,
    }


def read_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


class JsonlTail:
    """只追加 JSONL 的增量读者；未写完的末行等下次。"""

    def __init__(self, path: Path):
        self.path, self.offset, self.partial = Path(path), 0, b""

    def read(self) -> list[dict[str, Any]]:
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


class OpsLog:
    """W5：操作原流（只追加）；写失败抛出，由调用方按失败处理。"""

    def __init__(self, path: Path, *, clock: Callable[[], float] = time.time):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self.lock = threading.Lock()

    def write(self, kind: str, **fields: Any) -> dict[str, Any]:
        record = {"kind": kind, "at_unix_s": self.clock(), **fields}
        line = json.dumps(record, ensure_ascii=False, sort_keys=True, default=as_text)
        with self.lock, self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return record


# --- 只读监视 -----------------------------------------------------------------


class Monitor:
    """一个会话的只读视图：桥文件、会话目录原流、最新帧；`poll` 由后台线程与每次动作前调用。"""

    def __init__(
        self,
        runtime: Path,
        session_id: str,
        session_dir: Path,
        receipt: Mapping[str, float],
        *,
        clock: Callable[[], float] = time.time,
    ):
        self.runtime = Path(runtime)
        self.session_id = session_id
        self.session_dir = Path(session_dir)
        self.previews = self.session_dir / "previews"
        self.receipt = dict(receipt)
        self.clock = clock
        self.lock = threading.Lock()
        self.journal_tail = JsonlTail(self.session_dir / SESSION_JOURNAL)
        self.results_tail = JsonlTail(self.session_dir / RESULTS_FILE)
        #: request_id → 首个（非 IGNORED_DUPLICATE）回执与其会话写盘时刻
        self.receipts: dict[str, dict[str, Any]] = {}
        #: request_id → 该请求的指定结果行（按到达顺序）
        self.designate_results: dict[str, list[dict[str, Any]]] = {}
        #: 会话原流事件（状态迁移、指定、疑似/丢失等）——供调度器锚点计时与收尾摘要核对
        self.events: list[dict[str, Any]] = []
        #: result_id → 首次读到的 (preview sha, issued_unix_s)，W2「不能用后到结果替换原图」
        self.first_seen: dict[str, tuple[str | None, float | None]] = {}
        self.inconsistent: dict[str, str] = {}
        self.poll_error: str | None = None
        self.snapshot: dict[str, Any] = {"session_id": session_id, "state": None, "polled_unix_s": None}

    # -- 读取 --

    def _read_state(self) -> tuple[dict[str, Any] | None, str | None]:
        try:
            document = bridge.read_tracker_state(self.runtime)
        except bridge.LanguageBridgeError as error:
            return None, f"tracker_state 无法校验：{error}"
        state = (document or {}).get("tracker_state")
        if not isinstance(state, dict):
            return None, "等待会话写出 tracker_state"
        if state.get("session_id") != self.session_id:
            return None, f"tracker_state 不是本会话（{state.get('session_id')}）"
        return state, None

    def _read_result(self) -> tuple[dict[str, Any] | None, float | None]:
        try:
            document = bridge.read_result(self.runtime)
        except (bridge.LanguageBridgeError, OSError, ValueError):
            return None, None
        body = (document or {}).get("result")
        if not isinstance(body, dict) or not str(body.get("query_id") or "").startswith(f"{self.session_id}-q"):
            return None, None
        issued = (document or {}).get("issued_unix_s")
        return body, (float(issued) if finite(issued) else None)

    def _read_logs(self) -> None:
        for record in self.journal_tail.read():
            if record.get("session_id") != self.session_id:
                continue
            kind = record.get("kind")
            receipt = record.get("receipt")
            if kind == "receipt" and isinstance(receipt, dict) and receipt.get("request_id"):
                if receipt.get("outcome") == "IGNORED_DUPLICATE" and receipt["request_id"] in self.receipts:
                    continue
                self.receipts.setdefault(
                    receipt["request_id"],
                    # IR-OPS-6：观察锚点 = 该 request_id 的会话 receipt 写盘时刻；纪元随原流一并绑定。
                    {"receipt": receipt, "detail": record.get("detail"), "at_unix_s": record.get("at_unix_s"),
                     "epoch": record.get("epoch")},
                )
            if kind in {"state", "designation", "suspect_raised", "pointer_bound", "result_presented", "backend_fatal"}:
                self.events.append(record)
        for record in self.results_tail.read():
            if record.get("purpose") != "designate":
                continue
            request_id = record.get("request_id")
            if request_id:
                self.designate_results.setdefault(str(request_id), []).append(record)

    def _read_frames(self) -> tuple[int | None, str | None, float | None]:
        latest = read_json(self.runtime / "frames" / "latest.json")
        if not isinstance(latest, dict) or not isinstance(latest.get("frame_id"), int):
            return None, None, None
        image = latest.get("image_file")
        image = image if isinstance(image, str) and FRAME_NAME.match(image) else None
        metadata = read_json(self.runtime / "frames" / f"frame_{latest['frame_id']:010d}.json")
        captured = (metadata or {}).get("capture_unix_s") if isinstance(metadata, dict) else None
        return latest["frame_id"], image, (float(captured) if finite(captured) else None)

    def preview_identity(self, record: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        """绑定本结果源帧与查询的预览：文件名、字节 sha、尺寸；否则返回原因。"""
        path = record.get("preview_path")
        if not path:
            return None, "预览缺失（preview_path 为空）"
        expected = f"{record.get('frame_id')}-{record.get('query_id')}.png"
        candidate = Path(str(path))
        if candidate.name != expected or not PREVIEW_NAME.match(expected):
            return None, f"预览与源帧/查询不符（{candidate.name} ≠ {expected}）"
        try:
            if candidate.resolve().parent != self.previews.resolve() or not candidate.is_file():
                return None, "预览不在本会话 previews/ 或不存在"
            if candidate.stat().st_size > MAX_PREVIEW_BYTES:
                return None, "预览文件过大"
            data = candidate.read_bytes()
        except OSError:
            return None, "预览无法读取"
        size = png_dimensions(data)
        if size is None:
            return None, "预览不是可显示的 PNG（空、损坏或未写完）"
        return {"name": expected, "sha256": sha256_bytes(data), "bytes": len(data), "width": size[0], "height": size[1]}, None

    # -- 快照 --

    def _presentation(
        self, state: Mapping[str, Any], result: Mapping[str, Any] | None, issued: float | None, latest: int | None
    ) -> dict[str, Any]:
        receipt = self.receipt
        block: dict[str, Any] = {
            "result_id": None,
            "query_id": None,
            "request_id": None,
            "frame_id": None,
            "status": None,
            "candidates": [],
            "preview": None,
            "confirmable": False,
            "why_not": None,
            "query_unix_s": None,
            "issued_unix_s": None,
            "query_deadline_unix_s": None,
            "presented_deadline_unix_s": None,
            "frames_delta": None,
            "frames_limit": int(receipt["k_ret"] + receipt["k_conf"]),
            "t_ret_s": receipt["t_ret_s"],
            "t_conf_s": receipt["t_conf_s"],
        }
        if (
            not result
            or result.get("purpose") != "designate"
            or result.get("status") not in {"unique", "ambiguous"}
            or result.get("epoch") != state.get("epoch")
            or not result.get("candidates")
        ):
            block["why_not"] = "结果槽与当前状态不一致或还不是本次候选（等待刷新）"
            return block
        block.update(
            result_id=result.get("result_id"),
            query_id=result.get("query_id"),
            request_id=result.get("request_id"),
            frame_id=result.get("frame_id"),
            status=result.get("status"),
            candidates=[
                {"index": c.get("index"), "xywh": c.get("bbox_xywh_norm"), "clipped": c.get("clipped")}
                for c in result.get("candidates") or []
            ],
        )
        identity, problem = self.preview_identity(result)
        block["preview"] = identity
        result_id = str(block["result_id"])
        seen = (identity or {}).get("sha256"), issued
        first = self.first_seen.setdefault(result_id, seen)
        if first != seen and result_id not in self.inconsistent:
            self.inconsistent[result_id] = f"同一结果两次读出不一致（首次 {first}，本次 {seen}）"
        if result_id in self.inconsistent:
            block["why_not"] = f"不可确认：{self.inconsistent[result_id]}"
            return block
        if problem:
            block["why_not"] = f"不可确认：{problem}"
            return block
        query_unix = result.get("query_unix_s")
        now = self.clock()
        if not (finite(query_unix) and finite(issued) and isinstance(block["frame_id"], int) and latest is not None):
            block["why_not"] = "不可确认：取不到查询时刻、结果呈现时刻或最新帧"
            return block
        if issued < query_unix or issued > now + PRESENTATION_SKEW_S:
            block["why_not"] = "不可确认：呈现时刻早于查询时刻或晚于本机时钟（回退/不一致）"
            return block
        block.update(
            query_unix_s=float(query_unix),
            issued_unix_s=float(issued),
            query_deadline_unix_s=float(query_unix) + receipt["t_ret_s"] + receipt["t_conf_s"],
            presented_deadline_unix_s=float(issued) + receipt["t_conf_s"],
            frames_delta=latest - int(block["frame_id"]),
            confirmable=True,
        )
        return block

    def poll(self) -> dict[str, Any]:
        state, note = self._read_state()
        result, issued = self._read_result()
        latest, image, captured = self._read_frames()
        with self.lock:
            now = self.clock()
            self._read_logs()
            snap: dict[str, Any] = {
                "session_id": self.session_id,
                "polled_unix_s": now,
                "state": state,
                "note": note,
                "legal": sorted(legal_session_actions(state)),
                "presentation": None,
                "frames": {"latest_frame_id": latest, "image_file": image, "capture_unix_s": captured},
            }
            if state is not None and state.get("state") == "AWAITING_CONFIRMATION":
                snap["presentation"] = self._presentation(state, result, issued, latest)
            self.poll_error = None
            self.snapshot = snap
            return json.loads(json.dumps(snap))

    def fail(self, error: BaseException) -> None:
        with self.lock:
            self.poll_error = f"{type(error).__name__}: {error}"
            self.snapshot = dict(self.snapshot, note=f"读取出错：{self.poll_error}")

    def public(self, now: float) -> dict[str, Any]:
        """在 `now` 求值的确认门（不保存）；数据过期即不可确认（W3：刷新不续期，只会更早禁用）。"""
        with self.lock:
            snap = json.loads(json.dumps(self.snapshot))
            error = self.poll_error
        polled = snap.get("polled_unix_s")
        snap["age_s"] = None if polled is None else now - polled
        snap["stale"] = bool(error) or polled is None or now - polled > STALE_S
        snap["poll_error"] = error
        block = snap.get("presentation")
        if block and block.get("confirmable"):
            deadline = min(block["query_deadline_unix_s"], block["presented_deadline_unix_s"])
            block["deadline_unix_s"] = deadline
            block["remaining_s"] = deadline - now
            late = block.get("frames_delta")
            if snap["stale"]:
                block["confirmable"] = False
                block["why_not"] = "页面数据过期（读取出错或超过 1 s 未刷新）：不能用旧画面确认"
            elif late is None or late < 0 or late > block["frames_limit"]:
                block["confirmable"] = False
                block["why_not"] = f"已过帧差门（{late}/{block['frames_limit']}）：不可确认（可拒绝）"
            elif deadline - now <= 0:
                block["confirmable"] = False
                block["why_not"] = "已过截止：不可确认（不自动拒绝、不重问；可拒绝）"
        snap["now_unix_s"] = now
        return snap

    def receipt_record(self, request_id: str) -> dict[str, Any] | None:
        with self.lock:
            record = self.receipts.get(request_id)
            return json.loads(json.dumps(record)) if record else None

    def results_for(self, request_id: str) -> list[dict[str, Any]]:
        with self.lock:
            return json.loads(json.dumps(self.designate_results.get(request_id, [])))

    def events_since(self, since_unix_s: float) -> list[dict[str, Any]]:
        with self.lock:
            return [
                json.loads(json.dumps(e))
                for e in self.events
                if finite(e.get("at_unix_s")) and float(e["at_unix_s"]) >= since_unix_s
            ]


# --- 原 CLI 与一次提交记录（W4） ------------------------------------------------


class CliRunner:
    """组装并执行一次 `python -m controller.language_loop <action>`；不写桥文件/锁。"""

    def __init__(self, python: str, code_root: Path, runtime: Path, *, timeout_s: float = CLI_TIMEOUT_S):
        self.python, self.code_root, self.runtime = python, Path(code_root), Path(runtime)
        self.timeout_s = timeout_s

    def argv(
        self,
        action: str,
        session_id: str,
        request_id: str,
        *,
        token: str | None = None,
        index: int | None = None,
        instruction: str | None = None,
        intent: str | None = None,
        delay_s: float | None = None,
    ) -> list[str]:
        if action not in CLI_ACTIONS:
            raise ValueError(f"action {action!r} outside the closed set")
        argv = [
            self.python, "-m", "controller.language_loop", action,
            "--session-id", session_id, "--runtime", str(self.runtime),
            "--allow-shared-runtime", "--request-id", request_id,
        ]
        if token is not None:
            argv += ["--token", token]
        if delay_s is not None:
            argv += ["--delay-s", repr(float(delay_s))]
        if intent is not None:
            argv += ["--intent", intent]
        if index is not None:
            argv.append(str(int(index)))
        if instruction is not None:
            argv.append(instruction)
        return argv

    def __call__(self, argv: list[str]) -> dict[str, Any]:
        try:
            done = subprocess.run(
                argv, cwd=self.code_root, capture_output=True, text=True, timeout=self.timeout_s, check=False
            )
        except subprocess.TimeoutExpired as expired:
            return {"exit": None, "timeout": True, "stdout": as_text(expired.stdout), "stderr": as_text(expired.stderr)}
        return {"exit": done.returncode, "timeout": False, "stdout": as_text(done.stdout), "stderr": as_text(done.stderr)}


def interpret(outcome: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str]:
    """(回执或 None, 一句话含义)；APPLIED 只表示受理，不表示播种/跟踪成功。"""
    if outcome.get("timeout"):
        return None, "CLI 超时被终止：结果未知（UNKNOWN），不自动重发"
    code = outcome.get("exit")
    if code == 0:
        try:
            receipt = json.loads(outcome.get("stdout") or "").get("receipt")
        except (ValueError, AttributeError):
            receipt = None
        if isinstance(receipt, dict):
            return receipt, f"会话回执 {receipt.get('outcome')}（APPLIED 仅表示受理）"
        return None, "CLI 退出 0 但读不到回执：结果未知（UNKNOWN）"
    if code == 5:
        return None, "5 s 内无回执：结果未知（UNKNOWN），不自动重发"
    if code == 4:
        return None, "WRITER_BUSY：本次未写入；按 W4 记录并停依赖推进"
    if code == 2:
        return None, "CLI 拒绝（参数/守卫），未写请求；按 W4 记录并停依赖推进"
    return None, f"CLI 退出码 {code}：结果未知（UNKNOWN），不自动重发"


class Submitter:
    """runner 与网页共用的唯一提交通道：全局互斥、一次提交记录、每会话 stop 至多一次（W4）。"""

    def __init__(self, cli: Callable[[list[str]], Mapping[str, Any]], argv_builder: CliRunner, log: OpsLog):
        self.cli, self.argv_builder, self.log = cli, argv_builder, log
        self.in_flight = threading.Lock()
        self.lock = threading.Lock()
        self.used_bindings: set[str] = set()
        self.stop_sent: dict[str, str] = {}
        #: request_id → {"action", "binding", "since_unix_s"}：结果未知，停依赖推进
        self.unknown: dict[str, dict[str, Any]] = {}
        self.records: dict[str, dict[str, Any]] = {}
        #: session_id → 封住原因（C6-1：STOP/故障/中断/结果未知后不可逆；之后只放行该会话至多一次的 stop）
        self.sealed: dict[str, str] = {}

    def seal(self, session_id: str, reason: str) -> None:
        """不可逆封住本会话的业务动作（发送/跳过/确认/拒绝/release）；迟到回执或状态不解封。"""
        with self.lock:
            if session_id in self.sealed:
                return
            self.sealed[session_id] = reason
        self.log.write("sealed", session_id=session_id, reason=reason, note="此后只允许该会话原合法 stop（至多一次）与状态读取")

    def sealed_reason(self, session_id: Any) -> str | None:
        with self.lock:
            return self.sealed.get(str(session_id)) if session_id is not None else None

    def binding_used(self, key: str) -> bool:
        with self.lock:
            return key in self.used_bindings

    def claim(self, key: str, session_id: Any = None) -> bool:
        """非 CLI 动作（跳过）占用一次提交记录；已占用或该会话已封住返回 False。"""
        with self.lock:
            if key in self.used_bindings or (session_id is not None and str(session_id) in self.sealed):
                return False
            self.used_bindings.add(key)
            return True

    def submit(
        self,
        *,
        source: str,
        action: str,
        session_id: str,
        binding: Mapping[str, Any],
        binding_key: str,
        token: str | None = None,
        index: int | None = None,
        instruction: str | None = None,
        intent: str | None = None,
        delay_s: float | None = None,
        on_reply: Callable[[dict[str, Any]], None] | None = None,
        extra_argv: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """返回 {"ok", "refused", "message", "request_id", "receipt", "unknown"}；从不重试。

        `on_reply`（已发送时）在**释放在途锁之前**把结果记入计划：收尾持有在途锁后读到的计划逐步记录必然已含
        这条提交（C6-3：已受理的请求不会因竞态被记成未执行）。
        """
        if not self.in_flight.acquire(blocking=False):
            self.log.write("refused", source=source, action=action, reason="in_flight", binding=dict(binding))
            return {"ok": False, "refused": True, "message": "上一条提交仍在途，本次未发送"}
        try:
            with self.lock:
                if action != "stop" and session_id in self.sealed:
                    self.log.write("refused", source=source, action=action, reason="sealed", binding=dict(binding),
                                   sealed_reason=self.sealed[session_id])
                    return {"ok": False, "refused": True, "sealed": True,
                            "message": f"本会话业务动作已封住（{self.sealed[session_id]}）：只允许停止会话，本次未发送"}
                if binding_key in self.used_bindings:
                    self.log.write("refused", source=source, action=action, reason="binding_already_submitted", binding=dict(binding))
                    return {"ok": False, "refused": True, "message": "同一绑定已提交过（旧视图/重放/重复点击），本次未发送"}
                if action == "stop" and session_id in self.stop_sent:
                    self.log.write("refused", source=source, action=action, reason="stop_already_sent", binding=dict(binding),
                                   first_stop_request_id=self.stop_sent[session_id])
                    return {"ok": False, "refused": True, "message": "本会话 stop 已发过一次，不再发送"}
                request_id = f"{session_id}-ops-{uuid.uuid4().hex[:8]}"
                self.used_bindings.add(binding_key)
                if action == "stop":
                    self.stop_sent[session_id] = request_id
            if extra_argv is None:
                argv = self.argv_builder.argv(
                    action, session_id, request_id, token=token, index=index,
                    instruction=instruction, intent=intent, delay_s=delay_s,
                )
            else:
                # P1-ENG-CAPTURE-001 §2.5 ①：仅关键字扩展（点击页的 click 字段）；为 None 时上一行原样调用。
                argv = self.argv_builder.argv(
                    action, session_id, request_id, token=token, index=index,
                    instruction=instruction, intent=intent, delay_s=delay_s, **dict(extra_argv),
                )
            # 先落 request_id 与绑定（W4：调用前保存），再调用。
            self.log.write("submit_begin", source=source, action=action, session_id=session_id,
                           request_id=request_id, binding=dict(binding), argv=argv)
            started = time.time()
            outcome = dict(self.cli(argv))
            stdout, stderr = as_text(outcome.get("stdout")), as_text(outcome.get("stderr"))
            receipt, meaning = interpret(dict(outcome, stdout=stdout, stderr=stderr))
            unknown = receipt is None
            if unknown:
                with self.lock:
                    self.unknown[request_id] = {"action": action, "binding": dict(binding), "since_unix_s": time.time(),
                                                "exit": outcome.get("exit"), "timeout": bool(outcome.get("timeout"))}
            record = {"source": source, "action": action, "session_id": session_id, "request_id": request_id,
                      "binding": dict(binding), "argv": argv, "exit_code": outcome.get("exit"),
                      "timeout": bool(outcome.get("timeout")), "stdout": stdout, "stderr": stderr,
                      "receipt": receipt, "meaning": meaning, "unknown": unknown,
                      "cli_started_unix_s": started, "cli_finished_unix_s": time.time()}
            with self.lock:
                self.records[request_id] = record
            self.log.write("submit_result", **record)
            reply = {"ok": receipt is not None, "refused": False, "message": meaning, "request_id": request_id,
                     "receipt": receipt, "unknown": unknown}
            if on_reply is not None:
                try:
                    on_reply(reply)
                except Exception as error:  # noqa: BLE001 - 记录失败照记，不吞掉已发送的事实
                    # P1-ENG-CAPTURE-001 §2.5 ②（R1-5 on_reply 子路径）：先在同一把锁内于内存 seal 该会话、
                    # 写 unknown[request_id]（保留 request_id 与「已发送」事实），再尝试写日志；记录器自身再抛
                    # 也不影响已完成的内存 seal。回复带 sealed/unknown。
                    failure = f"{type(error).__name__}: {error}"
                    with self.lock:
                        self.sealed.setdefault(session_id, "record_reply_failed")
                        self.unknown[request_id] = {"action": action, "binding": dict(binding), "since_unix_s": time.time(),
                                                    "sent": True, "record_reply_failed": failure}
                    reply = dict(reply, sealed=True, unknown=True)
                    try:
                        self.log.write("record_reply_failed", request_id=request_id, error=failure)
                        self.log.write("sealed", session_id=session_id, reason="record_reply_failed",
                                       note="on_reply 失败：内存已封住；此后只允许该会话原合法 stop（至多一次）与状态读取")
                    except Exception:  # noqa: BLE001 - 记录器自身失败：内存 seal 已完成，照常返回
                        pass
            return reply
        finally:
            self.in_flight.release()

    def resolve_late(self, monitor: Monitor) -> None:
        """迟到回执只按原 request_id 核清并记录；不恢复任何流程（W4）。"""
        with self.lock:
            waiting = list(self.unknown)
        for request_id in waiting:
            record = monitor.receipt_record(request_id)
            if not record:
                continue
            with self.lock:
                entry = self.unknown.get(request_id)
                if entry is None or entry.get("late_receipt"):
                    continue
                entry["late_receipt"] = record
            self.log.write("late_receipt", request_id=request_id, action=entry["action"], receipt=record["receipt"],
                           detail=record.get("detail"), journal_at_unix_s=record.get("at_unix_s"),
                           note="只核清原 id；流程保持停止，不自动恢复")

    def unknown_entries(self) -> list[dict[str, Any]]:
        with self.lock:
            return [dict(v, request_id=k) for k, v in self.unknown.items()]


# --- 页面应用 -----------------------------------------------------------------


def view_key(view: Mapping[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {k: view.get(k) for k in keys}


SEND_VIEW_KEYS = ("session_id", "state", "reason", "epoch", "step_id", "plan_sha256")
DECIDE_VIEW_KEYS = ("session_id", "state", "reason", "epoch", "result_id", "query_id", "request_id", "frame_id", "step_id")
STOP_VIEW_KEYS = ("session_id", "state", "epoch")


class App:
    """W1–W5 的服务端：所有按钮先过本类，再经 `Submitter`；调度器（play_ops）决定计划步骤。

    `scheduler` 接口（鸭子类型，由 `play_ops.PlanScheduler` 提供）：
    `snapshot() -> dict`、`current_send_step(step_id) -> dict | None`（可发送/跳过的当前步骤）、
    `record_send(step_id, reply)`、`record_skip(step_id, at_unix_s)`、`decision_step(request_id) -> str | None`、
    `record_decision(step_id, action, reply)`、`record_operator_stop(reply)`、`blocked() -> str | None`。
    """

    def __init__(
        self,
        *,
        monitor_factory: Callable[[str, Path], Monitor],
        submitter: Submitter,
        log: OpsLog,
        scheduler: Any,
        feedback_path: Path,
        clock: Callable[[], float] = time.time,
        banner: str | None = None,
    ):
        self.monitor_factory = monitor_factory
        #: 模式横幅（诊断：「诊断；不进证据链；不作任何门判定」）；只显示，不改任何动作或门。
        self.banner = banner
        self.submitter = submitter
        self.log = log
        self.scheduler = scheduler
        self.feedback_path = Path(feedback_path)
        self.clock = clock
        self.nonce = secrets.token_hex(16)
        self.lock = threading.Lock()
        self.monitor: Monitor | None = None
        self.displayed: dict[str, str] = {}  # result_id → 浏览器回报已显示的 preview sha
        self.logged_presentations: set[str] = set()
        self.summary: dict[str, Any] | None = None  # {"attempts": [...], "text": str}，收尾后由 play_ops 置入
        self.feedback_given: set[str] = set()

    # -- 会话绑定 --

    def bind_session(self, session_id: str, session_dir: Path) -> Monitor:
        with self.lock:
            self.monitor = self.monitor_factory(session_id, Path(session_dir))
            self.displayed.clear()
            self.log.write("bind_session", session_id=session_id, session_dir=str(session_dir))
            return self.monitor

    def set_summary(self, summary: Mapping[str, Any]) -> None:
        with self.lock:
            self.summary = json.loads(json.dumps(summary))
        self.log.write("summary_ready", attempts=[a.get("session_id") for a in summary.get("attempts", [])])

    def current_monitor(self) -> Monitor | None:
        with self.lock:
            return self.monitor

    # -- 状态 --

    def state(self) -> dict[str, Any]:
        monitor = self.current_monitor()
        now = self.clock()
        if monitor is not None:
            self.submitter.resolve_late(monitor)
        snap: dict[str, Any] = {"now_unix_s": now, "session": None, "plan": self.scheduler.snapshot(),
                                "unknown": self.submitter.unknown_entries(), "summary": None, "mode_banner": self.banner}
        if monitor is not None:
            session = monitor.public(now)
            snap["session"] = session
            block = session.get("presentation")
            if block and block.get("result_id") and block["result_id"] not in self.logged_presentations:
                self.logged_presentations.add(block["result_id"])
                self.log.write("presentation_snapshot", session_id=monitor.session_id,
                               **{k: block.get(k) for k in ("result_id", "query_id", "request_id", "frame_id", "status",
                                                            "candidates", "preview", "query_unix_s", "issued_unix_s",
                                                            "frames_limit", "why_not")})
        with self.lock:
            if self.summary is not None:
                snap["summary"] = dict(self.summary, feedback_given=sorted(self.feedback_given))
        snap["blocked"] = self.scheduler.blocked()
        return snap

    def refuse(self, reason: str, **fields: Any) -> dict[str, Any]:
        self.log.write("refused", reason=reason, **fields)
        return {"ok": False, "message": reason}

    # -- 动作入口 --

    def displayed_preview(self, body: Mapping[str, Any]) -> dict[str, Any]:
        """浏览器回报预览已实际加载解码（W2 显示门）；只记录与当前呈现一致的那一张。"""
        monitor = self.current_monitor()
        result_id, name, sha = body.get("result_id"), body.get("name"), body.get("sha256")
        if monitor is None:
            return self.refuse("无会话", what="displayed")
        block = (monitor.public(self.clock()).get("presentation") or {})
        preview = block.get("preview") or {}
        if result_id != block.get("result_id") or name != preview.get("name") or sha != preview.get("sha256"):
            return self.refuse("回报的已显示图与当前呈现不符，不记为已显示", what="displayed", posted=dict(body))
        with self.lock:
            self.displayed[str(result_id)] = str(sha)
        self.log.write("preview_displayed", session_id=monitor.session_id, result_id=result_id, name=name, sha256=sha)
        return {"ok": True, "message": "已记录浏览器显示成功"}

    def action(self, body: Mapping[str, Any]) -> dict[str, Any]:
        kind = body.get("button")
        view = body.get("view")
        if kind not in BUTTONS or not isinstance(view, dict):
            return self.refuse("未知按钮或缺少页面身份", button=kind)
        self.log.write("click", button=kind, view=view, index=body.get("index"), preview_seen=body.get("preview_seen"),
                       label=body.get("label"))
        if kind == "feedback":
            return self._feedback(body)
        monitor = self.current_monitor()
        if monitor is None:
            return self.refuse("尚未绑定会话", button=kind, view=view)
        try:
            monitor.poll()
        except Exception as error:  # 读不到就不动作
            monitor.fail(error)
            return self.refuse(f"读取会话状态失败，本次未发送：{type(error).__name__}: {error}", button=kind, view=view)
        current = monitor.public(self.clock())
        state = current.get("state")
        if state is None:
            return self.refuse("会话状态不可读，本次未发送", button=kind, view=view)
        if current.get("stale"):
            return self.refuse("会话数据过期，本次未发送", button=kind, view=view)
        now_view = {"session_id": monitor.session_id, "state": state.get("state"), "reason": state.get("reason"),
                    "epoch": state.get("epoch")}
        if view.get("session_id") != monitor.session_id:
            return self.refuse("页面属于另一个会话，本次未发送", button=kind, view=view)
        if kind == "stop":
            return self._stop(view, now_view, current)
        sealed = self.submitter.sealed_reason(monitor.session_id)
        if sealed:
            return self.refuse(f"流程已封住（{sealed}）：只允许停止会话", button=kind, view=view)
        blocked = self.scheduler.blocked()
        if blocked:
            return self.refuse(f"流程已停止推进（{blocked}）：只允许停止会话", button=kind, view=view)
        if kind in {"send", "skip"}:
            return self._send_or_skip(kind, view, now_view, current)
        return self._decide(kind, body, view, now_view, current)

    def _send_or_skip(self, kind: str, view: Mapping[str, Any], now_view: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
        plan = self.scheduler.snapshot()
        live = dict(now_view, step_id=(plan.get("current") or {}).get("step_id"), plan_sha256=plan.get("plan_sha256"))
        if view_key(view, SEND_VIEW_KEYS) != view_key(live, SEND_VIEW_KEYS):
            return self.refuse("页面已过期：会话状态或计划步骤已变，请看新画面后再点", button=kind, view=view, current=live)
        step = self.scheduler.current_send_step(view.get("step_id"))
        if step is None:
            return self.refuse("该步骤不是等待发送/跳过的当前步骤", button=kind, view=view)
        binding_key = json.dumps({"button": "send_or_skip", "step_id": step["step_id"], "attempt": step["attempt"]}, sort_keys=True)
        if self.submitter.binding_used(binding_key):
            return self.refuse("该步骤已经发送或跳过过，本次未执行", button=kind, view=view)
        if kind == "skip":
            if not self.submitter.claim(binding_key, now_view["session_id"]):
                return self.refuse("该步骤已经发送或跳过过，本次未执行", button=kind, view=view)
            at = self.clock()
            self.scheduler.record_skip(step["step_id"], at)
            self.log.write("skip", step_id=step["step_id"], view=dict(view), at_unix_s_click=at,
                           outcome="SKIPPED_NOT_IN_VIEW", note="本人点击跳过：不发请求、不成样本")
            return {"ok": True, "message": "已记 SKIPPED_NOT_IN_VIEW（未发请求）"}
        action = step["action"]
        if action not in legal_session_actions(current.get("state")):
            return self.refuse(f"{action} 在 {now_view['state']} 下不合法，本次未发送", button=kind, view=view)
        reply = self.submitter.submit(
            source="web", action=action, session_id=str(now_view["session_id"]), binding=dict(view),
            binding_key=binding_key, instruction=step["instruction"], intent=step.get("intent"),
            delay_s=step.get("delay_s"), on_reply=lambda r: self.scheduler.record_send(step["step_id"], r),
        )
        return reply

    def _decide(self, kind: str, body: Mapping[str, Any], view: Mapping[str, Any], now_view: Mapping[str, Any],
                current: Mapping[str, Any]) -> dict[str, Any]:
        block = current.get("presentation") or {}
        live = dict(now_view, result_id=block.get("result_id"), query_id=block.get("query_id"),
                    request_id=block.get("request_id"), frame_id=block.get("frame_id"),
                    step_id=self.scheduler.decision_step(block.get("request_id")))
        if view_key(view, DECIDE_VIEW_KEYS) != view_key(live, DECIDE_VIEW_KEYS) or not live["result_id"]:
            return self.refuse("页面已过期：呈现结果/令牌/状态已变，请看新画面后再点", button=kind, view=view, current=live)
        if live["step_id"] is None:
            return self.refuse("当前呈现不属于等待本人选择的计划步骤", button=kind, view=view)
        if kind not in legal_session_actions(current.get("state")):
            return self.refuse(f"{kind} 在 {now_view['state']} 下不合法", button=kind, view=view)
        index = None
        if kind == "confirm":
            index = body.get("index")
            count = len(block.get("candidates") or [])
            if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < count:
                return self.refuse("候选序号不在本次候选内", button=kind, view=view, index=index)
            if not block.get("confirmable"):
                return self.refuse(block.get("why_not") or "不可确认", button=kind, view=view)
            preview = block.get("preview") or {}
            seen = body.get("preview_seen") or {}
            with self.lock:
                displayed = self.displayed.get(str(live["result_id"]))
            if seen.get("name") != preview.get("name") or seen.get("sha256") != preview.get("sha256") or displayed != preview.get("sha256"):
                return self.refuse("浏览器尚未显示这次候选的预览（加载中、失败、已换图），不能确认", button=kind, view=view,
                                   preview_seen=seen)
            # 提交前重读字节：sha 须仍等于当时呈现的那一张（W2）。
            monitor = self.current_monitor()
            again, problem = monitor.preview_identity({"preview_path": str(monitor.previews / preview["name"]),
                                                       "frame_id": live["frame_id"], "query_id": live["query_id"]})
            if problem or (again or {}).get("sha256") != preview.get("sha256"):
                return self.refuse("预览字节已变或不可读，不能确认", button=kind, view=view)
        binding_key = json.dumps({"button": "decide", "action": kind, "result_id": live["result_id"], "session_id": live["session_id"]}, sort_keys=True)
        reply = self.submitter.submit(
            source="web", action=kind, session_id=str(now_view["session_id"]), binding=dict(view, index=index),
            binding_key=binding_key, token=str(live["result_id"]), index=index,
            on_reply=lambda r: self.scheduler.record_decision(live["step_id"], kind, r),
        )
        return reply

    def _stop(self, view: Mapping[str, Any], now_view: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
        if view_key(view, STOP_VIEW_KEYS) != view_key(now_view, STOP_VIEW_KEYS):
            return self.refuse("页面已过期：会话状态已变，请看新画面后再点停止", button="stop", view=view, current=dict(now_view))
        if "stop" not in legal_session_actions(current.get("state")):
            return self.refuse("会话已结束，无需停止", button="stop", view=view)
        binding_key = json.dumps({"button": "stop", "session_id": now_view["session_id"]}, sort_keys=True)
        reply = self.submitter.submit(source="web", action="stop", session_id=str(now_view["session_id"]),
                                      binding=dict(view), binding_key=binding_key, on_reply=self.scheduler.record_operator_stop)
        return reply

    def _feedback(self, body: Mapping[str, Any]) -> dict[str, Any]:
        with self.lock:
            summary = self.summary
        if summary is None:
            return self.refuse("收尾摘要尚未就绪：反馈按钮未启用", button="feedback")
        label = body.get("label")
        attempt = (body.get("view") or {}).get("attempt")
        attempts = {a.get("session_id") for a in summary.get("attempts", [])}
        if label not in FEEDBACK_LABELS or attempt not in attempts:
            return self.refuse("反馈标签或尝试身份不合法", button="feedback", label=label, attempt=attempt)
        text = body.get("text") or ""
        if not isinstance(text, str) or len(text) > FEEDBACK_TEXT_MAX:
            return self.refuse("补充文字过长或格式不对", button="feedback")
        with self.lock:
            if attempt in self.feedback_given:
                return self.refuse("该尝试已提交过最终反馈", button="feedback", attempt=attempt)
            self.feedback_given.add(attempt)
        record = {"attempt": attempt, "label": label, "button_text": FEEDBACK_LABELS[label], "text": text,
                  "clicked_unix_s": self.clock(), "summary_sha256": summary.get("summary_sha256"),
                  "note": "本人反馈与自动摘要分列；不等于 DONE 或门通过"}
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
        with self.feedback_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        self.log.write("feedback", **record)
        return {"ok": True, "message": f"已记录最终反馈：{FEEDBACK_LABELS[label]}"}

    # -- 文件服务（W5：限本会话 previews/ 与 runtime/frames/ 当前帧） --

    def preview_bytes(self, name: str, sha: str | None) -> bytes | None:
        monitor = self.current_monitor()
        if monitor is None or not PREVIEW_NAME.match(name) or not (sha and SHA_HEX.match(sha)):
            return None
        path = monitor.previews / name
        try:
            if path.resolve().parent != monitor.previews.resolve() or path.stat().st_size > MAX_PREVIEW_BYTES:
                return None
            data = path.read_bytes()
        except OSError:
            return None
        return data if sha256_bytes(data) == sha and png_dimensions(data) else None

    def frame_bytes(self) -> bytes | None:
        monitor = self.current_monitor()
        if monitor is None:
            return None
        latest = read_json(monitor.runtime / "frames" / "latest.json")
        name = (latest or {}).get("image_file") if isinstance(latest, dict) else None
        if not isinstance(name, str) or not FRAME_NAME.match(name):
            return None
        path = monitor.runtime / "frames" / name
        try:
            if path.stat().st_size > MAX_FRAME_BYTES:
                return None
            data = path.read_bytes()
        except OSError:
            return None
        return data if data.startswith(JPEG_SIGNATURE) else None


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "loop2-ops/1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - 终端只留操作行
        return

    @property
    def app(self) -> App:
        return self.server.app  # type: ignore[attr-defined]

    def _host_ok(self) -> bool:
        port = self.server.server_address[1]
        return self.headers.get("Host") in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: Mapping[str, Any]) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False, default=as_text).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        if not self._host_ok():
            return self._send(403, b"forbidden", "text/plain")
        path, _, query = self.path.partition("?")
        if path == "/":
            page = PAGE.replace("__NONCE__", self.app.nonce)
            return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/api/state":
            return self._json(200, self.app.state())
        if path.startswith("/preview/"):
            params = dict(part.partition("=")[::2] for part in query.split("&") if part)
            data = self.app.preview_bytes(path[len("/preview/"):], params.get("sha"))
            if data is None:
                return self._send(404, b"not found", "text/plain")
            return self._send(200, data, "image/png")
        if path == "/frame/latest.jpg":
            data = self.app.frame_bytes()
            if data is None:
                return self._send(404, b"not found", "text/plain")
            return self._send(200, data, "image/jpeg")
        return self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        port = self.server.server_address[1]
        origin = self.headers.get("Origin")
        if (
            not self._host_ok()
            or self.path not in {"/api/action", "/api/displayed"}
            or self.headers.get("X-Ops-Nonce") != self.app.nonce
            or (origin is not None and origin not in {f"http://127.0.0.1:{port}", f"http://localhost:{port}"})
        ):
            self.app.log.write("refused", reason="forbidden_request", path=self.path, origin=origin,
                               host=self.headers.get("Host"), nonce_ok=self.headers.get("X-Ops-Nonce") == self.app.nonce)
            return self._send(403, b"forbidden", "text/plain")
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length <= 0 or length > MAX_BODY:
            return self._send(400, b"bad request", "text/plain")
        try:
            body = json.loads(self.rfile.read(length))
        except ValueError:
            return self._send(400, b"bad request", "text/plain")
        if not isinstance(body, dict):
            return self._send(400, b"bad request", "text/plain")
        if self.path == "/api/displayed":
            return self._json(200, self.app.displayed_preview(body))
        return self._json(200, self.app.action(body))


def build_server(app: App, port: int = DEFAULT_PORT) -> http.server.ThreadingHTTPServer:
    server = http.server.ThreadingHTTPServer((HOST, port), Handler)
    server.daemon_threads = True
    server.app = app  # type: ignore[attr-defined]
    return server


def poll_forever(app: App, stop: threading.Event) -> None:
    while not stop.is_set():
        monitor = app.current_monitor()
        if monitor is not None:
            try:
                monitor.poll()
            except Exception as error:  # 继续轮询；页面标记数据过期
                monitor.fail(error)
        stop.wait(POLL_S)


# --- AC-11 修订 1 / OPS:PREVIEW:6：离线样帧人眼保真核对（只读；不接会话、不发任何命令） ----------------


class FidelityHandler(http.server.BaseHTTPRequestHandler):
    """把 ≥2 张既有离线候选预览按操作页同一 `<img>` 呈现方式显示，并让浏览器自算收到字节的 sha256。

    只读：无 POST、不写任何文件；只服务命令行给出的那几张 PNG（按序号 + sha 绑定）。结论由人眼执行人
    写入新候选证据（路径/确认人/外观语义结论），本工具不代判。
    """

    server_version = "loop2-ops-fidelity/1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        port = self.server.server_address[1]
        if self.headers.get("Host") not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
            return self._send(403, b"forbidden", "text/plain")
        samples = self.server.samples  # type: ignore[attr-defined]
        path, _, query = self.path.partition("?")
        if path == "/":
            listing = [{"index": i, "name": s["name"], "sha256": s["sha256"], "bytes": s["bytes"], "width": s["width"],
                        "height": s["height"], "source": s["source"]} for i, s in enumerate(samples)]
            page = FIDELITY_PAGE.replace("__SAMPLES__", json.dumps(listing, ensure_ascii=False))
            return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        match = re.fullmatch(r"/sample/([0-9]+)", path)
        params = dict(part.partition("=")[::2] for part in query.split("&") if part)
        if match and int(match.group(1)) < len(samples):
            sample = samples[int(match.group(1))]
            data = Path(sample["source"]).read_bytes()
            if params.get("sha") == sample["sha256"] == sha256_bytes(data):
                return self._send(200, data, "image/png")
        return self._send(404, b"not found", "text/plain")


def load_fidelity_samples(paths: list[Path]) -> list[dict[str, Any]]:
    if len(paths) < 2:
        raise ValueError("至少 2 张离线样帧（AC-11 修订 1）")
    samples = []
    for path in paths:
        data = Path(path).read_bytes()
        size = png_dimensions(data)
        if size is None or not PREVIEW_NAME.match(Path(path).name):
            raise ValueError(f"不是候选预览 PNG：{path}")
        samples.append({"name": Path(path).name, "source": str(Path(path).resolve()), "sha256": sha256_bytes(data),
                        "bytes": len(data), "width": size[0], "height": size[1]})
    return samples


def build_fidelity_server(paths: list[Path], port: int = 0) -> http.server.ThreadingHTTPServer:
    server = http.server.ThreadingHTTPServer((HOST, port), FidelityHandler)
    server.daemon_threads = True
    server.samples = load_fidelity_samples(paths)  # type: ignore[attr-defined]
    return server


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="operator_web", description="LOOP-002 操作页的离线样帧保真核对入口（正式会话页由 play_ops 启动）")
    sub = parser.add_subparsers(dest="command", required=True)
    fidelity = sub.add_parser("fidelity", help="≥2 张既有离线候选预览的人眼保真核对页（只读）")
    fidelity.add_argument("previews", nargs="+", type=Path)
    fidelity.add_argument("--port", type=int, default=DEFAULT_PORT + 1)
    arguments = parser.parse_args(argv)
    try:
        server = build_fidelity_server(arguments.previews, arguments.port)
    except (OSError, ValueError) as error:
        print(f"无法启动保真核对页：{error}", file=sys.stderr)
        return 2
    print(f"fidelity page http://{HOST}:{server.server_address[1]}/ samples=" +
          json.dumps([(s["name"], s["sha256"]) for s in server.samples], ensure_ascii=False), flush=True)  # type: ignore[attr-defined]
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


FIDELITY_PAGE = r"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><title>LOOP-002 离线样帧保真核对</title>
<style>body{font:14px/1.45 -apple-system,system-ui,sans-serif;margin:12px}.panel{border:1px solid #ccc;border-radius:6px;padding:8px;margin:8px 0;max-width:720px}
img{max-width:100%;border:1px solid #999}.ok{color:#060}.bad{color:#a00;font-weight:600}</style></head><body>
<h2>离线样帧人眼保真核对（只读；与操作页候选预览同一 &lt;img&gt; 呈现；结论由人眼执行人写入候选证据）</h2>
<div id="list"></div>
<script>
const SAMPLES=__SAMPLES__;
const hex=b=>Array.from(new Uint8Array(b)).map(x=>x.toString(16).padStart(2,"0")).join("");
for(const s of SAMPLES){const d=document.createElement("div");d.className="panel";
 d.innerHTML=`<div><b>${s.name}</b> ${s.width}×${s.height} ${s.bytes} B</div><div>服务端 sha256 ${s.sha256}</div><div class="r">浏览器校验中…</div>`;
 const img=document.createElement("img");d.appendChild(img);document.getElementById("list").appendChild(d);
 const url=`/sample/${s.index}?sha=${s.sha256}`;
 fetch(url).then(r=>r.arrayBuffer()).then(async buf=>{const got=hex(await crypto.subtle.digest("SHA-256",buf));
  const r=d.querySelector(".r");r.className=got===s.sha256?"ok":"bad";r.textContent=(got===s.sha256?"浏览器收到字节 sha256 一致：":"不一致：")+got;
  img.onload=async()=>{try{await img.decode();r.textContent+=` · 已解码 ${img.naturalWidth}×${img.naturalHeight}`}catch(e){r.className="bad";r.textContent+=" · 解码失败"}};img.src=url;});}
</script></body></html>
"""


PAGE = r"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LOOP-002 操作页</title>
<style>
body{font:14px/1.45 -apple-system,system-ui,sans-serif;margin:12px;background:#fafafa;color:#111}
h2{font-size:15px;margin:10px 0 4px} .row{display:flex;gap:12px;flex-wrap:wrap}
.panel{background:#fff;border:1px solid #ccc;border-radius:6px;padding:8px;flex:1;min-width:300px}
.warn{color:#a00;font-weight:600} .muted{color:#666} img{max-width:100%;border:1px solid #999}
button{font-size:14px;margin:2px;padding:4px 10px} button:disabled{opacity:.4}
table{border-collapse:collapse;font-size:12px} td,th{border:1px solid #ddd;padding:2px 4px}
.tag{display:inline-block;padding:0 6px;border-radius:4px;background:#eee}
</style></head><body>
<div id="top" class="muted">读取中…</div>
<div class="row">
 <div class="panel"><h2>实时画面（只用于本人判断是否「发送」或「跳过」）</h2>
  <img id="live" alt="实时画面"><div id="liveinfo" class="muted"></div></div>
 <div class="panel"><h2>计划下一步（预登记；不可编辑）</h2><div id="step"></div>
  <div><button id="send">发送</button><button id="skip">跳过（不在画面）</button></div>
  <div id="planprog" class="muted"></div></div>
</div>
<div class="row">
 <div class="panel"><h2>候选预览（绑定源帧；只用于按预登记描述选序号或拒绝）</h2>
  <div id="cand" class="muted">无呈现中的候选</div><img id="prev" alt="候选预览" style="display:none">
  <div id="candbtns"></div></div>
 <div class="panel"><h2>会话</h2><div id="sess"></div>
  <button id="stop">停止会话（安全中止；不代按 Unity 停止）</button>
  <div id="unknown" class="warn"></div><div id="msg"></div></div>
</div>
<div class="panel" id="sumpanel" style="display:none"><h2>收尾摘要与最终反馈（摘要就绪后才可点；反馈与摘要分列）</h2>
 <pre id="sumtext" style="white-space:pre-wrap"></pre><div id="fb"></div></div>
<script>
const NONCE="__NONCE__"; let S=null; let busy=false; let shown={};
function esc(s){return String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
async function post(path,body){const r=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json","X-Ops-Nonce":NONCE},body:JSON.stringify(body)});return r.json()}
async function act(button,extra){if(busy)return;busy=true;render();try{const r=await post("/api/action",Object.assign({button:button},extra));
 document.getElementById("msg").textContent=(r.ok?"✓ ":"✗ ")+(r.message||"")+(r.request_id?" request_id="+r.request_id:"");}
 catch(e){document.getElementById("msg").textContent="请求失败："+e} finally{busy=false;await refresh()}}
function sessView(){const st=S.session&&S.session.state||{};return {session_id:S.session&&S.session.session_id,state:st.state,reason:st.reason,epoch:st.epoch}}
function render(){if(!S)return;const sess=S.session||{};const st=sess.state||{};const plan=S.plan||{};const cur=plan.current||null;
 document.getElementById("top").innerHTML=(S.mode_banner?`<span class="warn">${esc(S.mode_banner)}</span> `:"")+`会话 <b>${esc(sess.session_id)}</b> 剧本 ${esc(plan.playbook)} 计划 sha ${esc((plan.plan_sha256||"").slice(0,12))} `+
  (sess.stale?'<span class="warn">数据过期</span>':`<span class="muted">数据 ${sess.age_s!=null?sess.age_s.toFixed(1):"?"} s 前</span>`)+(S.blocked?` <span class="warn">流程已停止推进：${esc(S.blocked)}</span>`:"");
 document.getElementById("sess").innerHTML=`状态 <span class="tag">${esc(st.state)}</span> reason=${esc(st.reason)} epoch=${esc(st.epoch)} track=${esc(st.track_id)} 最新帧 ${esc(sess.frames&&sess.frames.latest_frame_id)}`+(sess.note?`<div class="warn">${esc(sess.note)}</div>`:"");
 const legal=new Set(sess.legal||[]);
 document.getElementById("stop").disabled=busy||!legal.has("stop")||sess.stale;
 const canSend=cur&&cur.phase==="await_send"&&!S.blocked&&!busy&&!sess.stale;
 document.getElementById("step").innerHTML=cur?`<b>${esc(cur.step_id)}</b> ${esc(cur.action)} “${esc(cur.instruction)}” 意图标签 ${esc(cur.intent)} Δ=${esc(cur.delay_s)}<br>预登记描述：<b>${esc(cur.description)}</b><br>阶段：${esc(cur.phase_text||cur.phase)}`:"计划已无待执行步骤";
 document.getElementById("send").disabled=!canSend||!legal.has(cur&&cur.action);
 document.getElementById("skip").disabled=!canSend;
 document.getElementById("planprog").innerHTML="<table><tr><th>步骤</th><th>动作</th><th>结局</th><th>原因</th></tr>"+(plan.steps||[]).map(s=>`<tr><td>${esc(s.step_id)}</td><td>${esc(s.action)} ${esc(s.instruction||"")}</td><td>${esc(s.status)}</td><td>${esc(s.reason||"")}</td></tr>`).join("")+"</table>";
 const p=sess.presentation; const cand=document.getElementById("cand"); const img=document.getElementById("prev"); const cb=document.getElementById("candbtns");
 if(p&&p.result_id){const left=p.remaining_s!=null?p.remaining_s.toFixed(1)+" s":"—";
  cand.innerHTML=`结果 ${esc(p.result_id)}（${esc(p.status)}）源帧 ${esc(p.frame_id)} 帧差 ${esc(p.frames_delta)}/${esc(p.frames_limit)} 剩余 ${esc(left)}`+(p.why_not?`<div class="warn">${esc(p.why_not)}</div>`:"");
  const pv=p.preview; const key=pv?pv.name+"|"+pv.sha256:null;
  if(pv){const src="/preview/"+encodeURIComponent(pv.name)+"?sha="+pv.sha256; if(img.dataset.key!==key){img.dataset.key=key;img.style.display="";
    img.onload=async()=>{try{await img.decode();const r=await post("/api/displayed",{result_id:p.result_id,name:pv.name,sha256:pv.sha256});if(r.ok)shown[p.result_id]=pv.sha256;}catch(e){}};
    img.onerror=()=>{delete shown[p.result_id]};img.src=src;}}else{img.style.display="none";img.dataset.key="";}
  const view=Object.assign(sessView(),{result_id:p.result_id,query_id:p.query_id,request_id:p.request_id,frame_id:p.frame_id,step_id:plan.decision_step});
  const ok=p.confirmable&&pv&&shown[p.result_id]===pv.sha256&&!busy&&!S.blocked;
  const rejOk=!busy&&!S.blocked&&legal.has("reject");
  const sig=JSON.stringify([view,ok,rejOk,(p.candidates||[]).map(c=>c.index),pv&&pv.sha256]);
  if(cb.dataset.sig!==sig){cb.dataset.sig=sig;  // 只在绑定/可点状态变化时重建按钮（避免点击被重绘吞掉）
   cb.innerHTML=(p.candidates||[]).map(c=>`<button data-i="${c.index}" ${ok?"":"disabled"}>确认序号 ${c.index}</button>`).join("")+`<button id="rej" ${rejOk?"":"disabled"}>拒绝</button>`;
   cb.querySelectorAll("button[data-i]").forEach(b=>b.onclick=()=>act("confirm",{view:view,index:Number(b.dataset.i),preview_seen:{name:pv.name,sha256:pv.sha256}}));
   document.getElementById("rej").onclick=()=>act("reject",{view:view});}
 } else {cand.textContent="无呈现中的候选"; img.style.display="none"; img.dataset.key=""; cb.innerHTML=""; cb.dataset.sig="";}
 document.getElementById("unknown").innerHTML=(S.unknown||[]).map(u=>`结果未知 request_id=${esc(u.request_id)} 动作 ${esc(u.action)}${u.late_receipt?"（迟到回执已核清，流程仍停止）":""}`).join("<br>");
 const sp=document.getElementById("sumpanel"); if(S.summary){sp.style.display="";document.getElementById("sumtext").textContent=S.summary.text||"";
  const fb=document.getElementById("fb"); const given=S.summary.feedback_given||[];
  if(!fb.dataset.built){fb.dataset.built="1";  // 只建一次：输入框内容不被轮询重绘清掉
   fb.innerHTML=(S.summary.attempts||[]).map(a=>`<div>${esc(a.session_id)}：`+["PASS","FAIL","BLOCKED"].map(l=>`<button data-a="${esc(a.session_id)}" data-l="${l}">${{PASS:"通过",FAIL:"失败",BLOCKED:"受阻"}[l]}</button>`).join("")+` <input data-t="${esc(a.session_id)}" size="40" maxlength="2000" placeholder="补充文字（可空）"></div>`).join("");
   fb.querySelectorAll("button").forEach(b=>b.onclick=()=>{const t=fb.querySelector(`input[data-t="${b.dataset.a}"]`);act("feedback",{view:{attempt:b.dataset.a},label:b.dataset.l,text:t?t.value:""})});}
  fb.querySelectorAll("button").forEach(b=>{b.disabled=busy||given.includes(b.dataset.a)});}
}
document.getElementById("send").onclick=()=>{const c=S.plan.current;act("send",{view:Object.assign(sessView(),{step_id:c.step_id,plan_sha256:S.plan.plan_sha256})})};
document.getElementById("skip").onclick=()=>{const c=S.plan.current;act("skip",{view:Object.assign(sessView(),{step_id:c.step_id,plan_sha256:S.plan.plan_sha256})})};
document.getElementById("stop").onclick=()=>{if(confirm("停止会话？（只发一次 stop，不代按 Unity 停止）"))act("stop",{view:sessView()})};
async function refresh(){try{S=await (await fetch("/api/state")).json();render();}catch(e){document.getElementById("top").textContent="读取失败："+e}}
setInterval(refresh,300); setInterval(()=>{const l=document.getElementById("live");l.src="/frame/latest.jpg?t="+Date.now()},500); refresh();
</script></body></html>
"""


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
