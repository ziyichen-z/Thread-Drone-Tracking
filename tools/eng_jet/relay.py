"""桌面机 ↔ Jetson 文件桥中继（合同 §3.2、SR、AC-4…6；纯标准库，两端各一进程）。

文件字段零改动；中继是 Unity 文件桥与控制器之外的搬运者，引入的 TCP 搬运通道与两机时间语义属 K1 检查对象。

- **前向**（桌面机 → 板）：桌面机轮询 `<runtime>/frames/latest.json`，仅当指针更新且两成员文件齐全时，按
  「先成员、后 `latest.json`」把 `frame_<id>.jpg`、`frame_<id>.json`、`latest.json` 推到板上镜像 `<runtime>`；
  板侧逐文件核 sha256、写临时文件后 `rename` 原子发布；`latest.json` 只在其两成员已在本连接内完整收到且盘上 sha
  复核一致、且 `frame_id` 严格递增时才发布（否则拒发并记收据）。
- **回程**（板 → 桌面机）：板侧轮询 `tracking_observation.json`、`gimbal_command.json`、`body_command.json`、
  `tracker_state.json`、`language_result.json`，内容变化即逐文件推回、桌面机原子写入。**不中继**
  `language_request.json` 与其 O_EXCL 锁。
- **传输**：TCP 长度前缀消息（4 字节大端头长 + 头 JSON + 负载）；头含路径、字节数、sha256、发送端 unix/monotonic；
  接收端记到达时戳；所有收据写各端 `relay-receipts.jsonl`。双向 0.5 s 心跳，3 s 无消息判链路断开。
  断链：发送端阻塞重连（指数退避 ≤ 2 s），**不缓存补发**（恢复后只发当前 `latest.json` 指向的包；回程同理只发当前版本）。
- **对时**：UDP 每 1 s 一次四时戳往返（NTP 式）：offset = ((t2−t1)+(t3−t4))/2（板 − 桌面），delay = (t4−t1)−(t3−t2)。
- **回声应答器**（`echo`，零模型）：板侧监视镜像 `latest.json`，新帧即经 `controller.tracking_entry.observation`
  写绑定同 `frame_id` 的 `tracking_observation.json`（占位框、`track_id=eng-jet-echo`），并记 `capture_age_s`
  （板墙钟 − `capture_unix_s`）与 `load_elapsed`。

子命令：`board`、`desktop`、`echo`、`analyze`。
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import socket
import struct
import sys
import threading
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

from tools.eng_jet import common

MAGIC_HB = "hb"
HEADER = struct.Struct(">I")
MAX_HEADER = 64 * 1024
MAX_PAYLOAD = 16 * 1024 * 1024
HEARTBEAT_S = 0.5
DEAD_AFTER_S = 3.0
BACKOFF_MAX_S = 2.0
POLL_S = 0.005
SYNC_PERIOD_S = 1.0
SYNC_TIMEOUT_S = 0.8
T_STALL_S = 3.0
T_PUB_S = 0.4
DEFAULT_PORT = 47811
RETAIN = 128
STALE_POINTER_GRACE_S = 5.0

FORWARD_MEMBER = re.compile(r"^frames/frame_(\d{10})\.(jpg|json)$")
FORWARD_POINTER = "frames/latest.json"
RETURN_FILES = ("tracking_observation.json", "gimbal_command.json", "body_command.json", "tracker_state.json", "language_result.json")
NEVER_RELAYED = ("language_request.json", "language_request.lock")


def now_pair() -> tuple[float, float]:
    return time.time(), time.monotonic()


# --- 消息帧 ------------------------------------------------------------------


def encode(header: Mapping[str, Any], payload: bytes = b"") -> bytes:
    head = dict(header)
    head["size"] = len(payload)
    raw = json.dumps(head, sort_keys=True).encode("utf-8")
    if len(raw) > MAX_HEADER:
        raise ValueError("header too large")
    return HEADER.pack(len(raw)) + raw + payload


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks, remaining = [], size
    while remaining:
        chunk = sock.recv(min(remaining, 1 << 20))
        if not chunk:
            raise ConnectionError("peer closed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_message(sock: socket.socket) -> tuple[dict[str, Any], bytes]:
    (length,) = HEADER.unpack(recv_exact(sock, HEADER.size))
    if length <= 0 or length > MAX_HEADER:
        raise ConnectionError(f"bad header length {length}")
    header = json.loads(recv_exact(sock, length).decode("utf-8"))
    size = int(header.get("size", 0))
    if size < 0 or size > MAX_PAYLOAD:
        raise ConnectionError(f"bad payload size {size}")
    return header, recv_exact(sock, size) if size else b""


def classify_forward(path: str) -> tuple[str, int | None]:
    """前向白名单：只收 `frames/frame_<10位>.jpg|json` 与 `frames/latest.json`；其余（含 `truth/`、越界路径）拒收。"""
    if path == FORWARD_POINTER:
        return "pointer", None
    match = FORWARD_MEMBER.match(path)
    if match:
        return "member", int(match.group(1))
    return "rejected", None


def classify_return(path: str) -> bool:
    return path in RETURN_FILES


class Receipts:
    """线程安全 JSONL 收据（每行落盘即 flush）。"""

    def __init__(self, path: Path):
        self.path = Path(path).expanduser()
        common.refuse_protected(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")
        self._lock = threading.Lock()
        self.closed = False

    def write(self, event: str, **fields: Any) -> None:
        unix, mono = now_pair()
        row = {"ev": event, "unix": round(unix, 6), "mono": round(mono, 6), **fields}
        with self._lock:
            if self.closed:
                return
            self._handle.write(json.dumps(row, sort_keys=True) + "\n")
            self._handle.flush()

    def close(self) -> None:
        with self._lock:
            self.closed = True
            self._handle.close()


class Link:
    """一条 TCP 连接的发送端（加锁）+ 存活状态。"""

    def __init__(self, sock: socket.socket):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.settimeout(DEAD_AFTER_S)
        self.sock = sock
        self.alive = True
        self._lock = threading.Lock()
        self._seq = 0

    def send(self, header: Mapping[str, Any], payload: bytes = b"") -> dict[str, Any]:
        with self._lock:
            if not self.alive:
                raise ConnectionError("link down")
            self._seq += 1
            unix, mono = now_pair()
            head = {**header, "seq": self._seq, "send_unix": unix, "send_mono": mono}
            if payload or header.get("kind") == "file":
                head["sha256"] = common.sha256_bytes(payload)
            try:
                self.sock.sendall(encode(head, payload))
            except OSError:
                self.close()
                raise
            return head

    def close(self) -> None:
        self.alive = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass


def heartbeat(link: Link, stop: threading.Event) -> None:
    while not stop.is_set() and link.alive:
        try:
            link.send({"kind": MAGIC_HB})
        except (OSError, ConnectionError):
            return
        stop.wait(HEARTBEAT_S)


# --- 板侧 --------------------------------------------------------------------


class BoardRelay:
    """板侧：TCP 服务端（一次一个连接，新连接替换旧连接）+ UDP 对时应答 + 回程监视。"""

    def __init__(self, runtime: Path, log_dir: Path, port: int = DEFAULT_PORT, bind: str = "0.0.0.0", retain: int = RETAIN):
        self.runtime = Path(runtime).expanduser()
        common.refuse_protected(self.runtime)
        (self.runtime / "frames").mkdir(parents=True, exist_ok=True)
        self.receipts = Receipts(Path(log_dir) / "relay-receipts.jsonl")
        self.port, self.bind, self.retain = port, bind, retain
        self.stop = threading.Event()
        self.link: Link | None = None
        self._link_lock = threading.Lock()
        self.members: dict[int, dict[str, str]] = {}
        self.last_published = -1
        self.counters = {"files_ok": 0, "sha_mismatch": 0, "rejected_path": 0, "published": 0, "refused_incomplete": 0,
                         "order_violation": 0, "returns_sent": 0}
        self._last_return: dict[str, str] = {}

    # 前向接收 ---------------------------------------------------------------
    def handle_file(self, header: Mapping[str, Any], payload: bytes) -> None:
        arrive_unix, arrive_mono = now_pair()
        path = str(header.get("path", ""))
        kind, frame_id = classify_forward(path)
        sha_ok = common.sha256_bytes(payload) == header.get("sha256") and len(payload) == int(header.get("size", -1))
        base = {"path": path, "seq": header.get("seq"), "bytes": len(payload), "sha_ok": sha_ok, "send_unix": header.get("send_unix"),
                "arrive_unix": round(arrive_unix, 6), "arrive_mono": round(arrive_mono, 6), "bundle": header.get("bundle")}
        if kind == "rejected":
            self.counters["rejected_path"] += 1
            self.receipts.write("reject_path", **base)
            return
        if not sha_ok:
            self.counters["sha_mismatch"] += 1
            self.receipts.write("sha_mismatch", **base)
            return
        if kind == "member":
            common.atomic_write_bytes(self.runtime / path, payload, fsync=False)
            self.members.setdefault(int(frame_id), {})[path.rsplit(".", 1)[1]] = header["sha256"]
            self.counters["files_ok"] += 1
            self.receipts.write("recv_member", frame_id=frame_id, **base)
            return
        self.counters["files_ok"] += 1
        self.publish_pointer(payload, base)

    def publish_pointer(self, payload: bytes, base: Mapping[str, Any]) -> None:
        try:
            manifest = json.loads(payload.decode("utf-8"))
            frame_id = int(manifest["frame_id"])
            names = (Path(manifest["image_file"]).name, Path(manifest["metadata_file"]).name)
        except (ValueError, KeyError, TypeError):
            self.counters["refused_incomplete"] += 1
            self.receipts.write("refuse_pointer", reason="bad_manifest", **base)
            return
        have = self.members.get(frame_id, {})
        complete = {"jpg", "json"} <= set(have)
        if complete:
            for suffix, name in zip(("jpg", "json"), names):
                disk = self.runtime / "frames" / name
                if not disk.is_file() or common.sha256_file(disk) != have[suffix]:
                    complete = False
        if not complete:
            self.counters["refused_incomplete"] += 1
            self.receipts.write("refuse_pointer", reason="incomplete_bundle", frame_id=frame_id, **base)
            return
        if frame_id <= self.last_published:
            self.counters["order_violation"] += 1
            self.receipts.write("refuse_pointer", reason="order_violation", frame_id=frame_id, last=self.last_published, **base)
            return
        common.atomic_write_bytes(self.runtime / FORWARD_POINTER, payload, fsync=False)
        pub_unix, pub_mono = now_pair()
        self.last_published = frame_id
        self.counters["published"] += 1
        self.receipts.write("publish", frame_id=frame_id, published_unix_desktop=manifest.get("published_unix_s"),
                            pub_unix=round(pub_unix, 6), pub_mono=round(pub_mono, 6), **base)
        self._prune(frame_id)

    def _prune(self, newest: int) -> None:
        for old in [k for k in self.members if k <= newest - self.retain]:
            for suffix in ("jpg", "json"):
                (self.runtime / "frames" / common.frame_name(old, suffix)).unlink(missing_ok=True)
            self.members.pop(old, None)

    # 回程发送 ---------------------------------------------------------------
    def return_once(self) -> int:
        """回程一轮：对当前连接逐文件发送内容有变化的当前版本；返回本轮发送数。去重状态 `_last_return` 只在同一连接内有效
        （新连接由 `adopt_link` 清空，R1-1）。去重写回与 `adopt_link` 的换连接/清空同在 `_link_lock` 内，且仅当本轮快照的
        连接仍是当前连接时写回：`send` 返回后、写回前若已换连接，旧轮次的 digest 不落进新连接的去重状态（复核 R2-1）；
        该次发送已 `sendall` 入旧连接，照常计入 `returns_sent` 与收据，收据注明 `link_replaced: true`，随即结束本轮。"""
        link = self.link
        if link is None or not link.alive:
            return 0
        sent = 0
        for name in RETURN_FILES:
            path = self.runtime / name
            try:
                payload = path.read_bytes()
            except OSError:
                continue
            digest = common.sha256_bytes(payload)
            if self._last_return.get(name) == digest:
                continue
            try:
                head = link.send({"kind": "file", "path": name}, payload)
            except (OSError, ConnectionError):
                break
            with self._link_lock:
                replaced = self.link is not link
                if not replaced:
                    self._last_return[name] = digest
            self.counters["returns_sent"] += 1
            sent += 1
            extra = {"link_replaced": True} if replaced else {}
            self.receipts.write("send_return", path=name, seq=head["seq"], bytes=len(payload), sha256=digest,
                                send_unix=head["send_unix"], send_mono=head["send_mono"], content_frame_id=_content_frame_id(payload),
                                **extra)
            if replaced:
                break
        return sent

    def return_watch(self) -> None:
        while not self.stop.is_set():
            self.return_once()
            self.stop.wait(POLL_S)

    # 连接与对时 -------------------------------------------------------------
    def serve_connection(self, link: Link, peer: Any) -> None:
        hb_stop = threading.Event()
        threading.Thread(target=heartbeat, args=(link, hb_stop), daemon=True).start()
        self.receipts.write("accept", peer=str(peer))
        try:
            while not self.stop.is_set():
                header, payload = recv_message(link.sock)
                if header.get("kind") == "file":
                    self.handle_file(header, payload)
        except (OSError, ConnectionError, ValueError) as error:
            self.receipts.write("close", peer=str(peer), reason=type(error).__name__)
        finally:
            hb_stop.set()
            link.close()

    def sync_responder(self, sock: socket.socket) -> None:
        sock.settimeout(0.5)
        while not self.stop.is_set():
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            t2 = time.time()
            try:
                request = json.loads(data.decode("utf-8"))
            except ValueError:
                continue
            reply = {"seq": request.get("seq"), "t1": request.get("t1"), "t2": t2, "t3": time.time()}
            try:
                sock.sendto(json.dumps(reply).encode("utf-8"), addr)
            except OSError:
                continue

    def adopt_link(self, link: Any) -> None:
        """新连接替换旧连接：关闭旧连接、清空前向成员表与回程去重状态。清空 `_last_return` 使重连后重发每个回程文件的当前版本
        （断链前已 `sendall` 入内核缓冲但随连接重置丢失的版本不会因去重而永不重发；仍只发当前版本、不补发历史版本，§3.2；
        复核 R1-1 具名补丁）。`return_once` 的去重写回同在 `_link_lock` 内并核对连接未被替换，清空不会被旧轮次写回覆盖（复核 R2-1）。"""
        with self._link_lock:
            if self.link is not None:
                self.link.close()
            self.link = link
            self.members.clear()
            self._last_return.clear()

    def run(self, duration_s: float | None = None) -> dict[str, Any]:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.bind, self.port))
        server.listen(2)
        server.settimeout(0.5)
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.bind((self.bind, self.port))
        threads = [threading.Thread(target=self.sync_responder, args=(udp,), daemon=True),
                   threading.Thread(target=self.return_watch, daemon=True)]
        for thread in threads:
            thread.start()
        self.receipts.write("start", port=self.port, runtime=str(self.runtime))
        deadline = None if duration_s is None else time.monotonic() + duration_s
        try:
            while not self.stop.is_set() and (deadline is None or time.monotonic() < deadline):
                try:
                    sock, peer = server.accept()
                except socket.timeout:
                    continue
                self.adopt_link(Link(sock))
                serving = threading.Thread(target=self.serve_connection, args=(self.link, peer), daemon=True)
                serving.start()
                threads.append(serving)
        finally:
            self.stop.set()
            if self.link is not None:
                self.link.close()
            server.close()
            udp.close()
            for thread in threads:
                thread.join(timeout=DEAD_AFTER_S)
            self.receipts.write("stop", **self.counters)
            self.receipts.close()
        return dict(self.counters)


def _content_frame_id(payload: bytes) -> int | None:
    try:
        value = json.loads(payload.decode("utf-8"))
    except ValueError:
        return None
    for holder in (value.get("observation") if isinstance(value, dict) else None, value):
        if isinstance(holder, dict) and isinstance(holder.get("frame_id"), int):
            return holder["frame_id"]
    return None


# --- 桌面机侧 ------------------------------------------------------------------


def recv_matching(udp: Any, seq: int, timeout_s: float) -> tuple[dict[str, Any], float, int]:
    """收对时应答直到 `seq` 匹配；丢弃链路恢复后迟到的旧应答（否则请求/应答永久错位，冒烟轮发现的缺陷）。

    返回 (应答, t4, 丢弃的旧应答数)；超时抛 `socket.timeout`。"""
    deadline = time.monotonic() + timeout_s
    stale = 0
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise socket.timeout("sync reply timeout")
        udp.settimeout(remaining)
        data, _addr = udp.recvfrom(4096)
        t4 = time.time()
        reply = json.loads(data.decode("utf-8"))
        if isinstance(reply, dict) and reply.get("seq") == seq:
            return reply, t4, stale
        stale += 1


def parse_drops(spec: str | None) -> list[tuple[float, float]]:
    """`"120:10,300:60"` → [(120, 10), (300, 60)]：开始后第 t 秒软件断链 d 秒（两通道与对时同时中断）。"""
    if not spec:
        return []
    drops = []
    for item in spec.split(","):
        start, _, length = item.partition(":")
        drops.append((float(start), float(length)))
    return sorted(drops)


class DesktopRelay:
    def __init__(self, runtime: Path, log_dir: Path, host: str, port: int = DEFAULT_PORT, drops: Sequence[tuple[float, float]] = ()):
        self.runtime = Path(runtime).expanduser()
        common.refuse_protected(self.runtime)
        self.receipts = Receipts(Path(log_dir) / "relay-receipts.jsonl")
        self.sync_log = Receipts(Path(log_dir) / "clock-sync.jsonl")
        self.host, self.port, self.drops = host, port, list(drops)
        self.stop = threading.Event()
        self.link: Link | None = None
        self.last_sent = -1
        self.blocked_until = 0.0
        self.t0 = time.monotonic()
        self.deadline = math.inf
        self.threads: list[threading.Thread] = []
        self.counters = {"bundles_sent": 0, "bundles_skipped_missing": 0, "send_failures": 0, "connects": 0, "returns_ok": 0,
                         "returns_bad": 0, "stale_pointers_skipped": 0}
        #: K1K3K4补跑F 返工（RELAY_INTEGRITY，正式轮 f1-echo）：启动时运行目录里残留的、本会话之前发布的 `latest.json`
        #: （`published_unix_s` 早于本进程启动 `STALE_POINTER_GRACE_S` 以上）不转发——否则板侧把它当作最新帧发布，
        #: 其后本会话从 0 起的新帧全部按顺序违反被拒。只比较桌面机自身墙钟，不改文件字段。
        self.started_unix = time.time()
        self._stale_skip: tuple[int, Any] | None = None

    def _blocked(self) -> bool:
        return time.monotonic() < self.blocked_until

    def connect(self) -> Link | None:
        backoff = 0.1
        while not self.stop.is_set() and time.monotonic() < self.deadline:
            self._maybe_drop()
            if self._blocked():
                self.stop.wait(min(0.1, self.blocked_until - time.monotonic()))
                continue
            try:
                sock = socket.create_connection((self.host, self.port), timeout=DEAD_AFTER_S)
            except OSError as error:
                self.receipts.write("connect_fail", reason=type(error).__name__, backoff_s=backoff)
                self.stop.wait(backoff)
                backoff = min(BACKOFF_MAX_S, backoff * 2)
                continue
            link = Link(sock)
            self.counters["connects"] += 1
            self.receipts.write("connect")
            hb_stop = threading.Event()
            threading.Thread(target=heartbeat, args=(link, hb_stop), daemon=True).start()
            reader = threading.Thread(target=self.reader, args=(link, hb_stop), daemon=True)
            reader.start()
            self.threads.append(reader)
            return link
        return None

    def reader(self, link: Link, hb_stop: threading.Event) -> None:
        try:
            while not self.stop.is_set():
                header, payload = recv_message(link.sock)
                if header.get("kind") != "file":
                    continue
                arrive_unix, arrive_mono = now_pair()
                path = str(header.get("path", ""))
                ok = classify_return(path) and common.sha256_bytes(payload) == header.get("sha256")
                if ok:
                    common.atomic_write_bytes(self.runtime / path, payload, fsync=False)
                    self.counters["returns_ok"] += 1
                else:
                    self.counters["returns_bad"] += 1
                self.receipts.write("recv_return", path=path, ok=ok, seq=header.get("seq"), bytes=len(payload),
                                    send_unix=header.get("send_unix"), arrive_unix=round(arrive_unix, 6), arrive_mono=round(arrive_mono, 6),
                                    content_frame_id=_content_frame_id(payload))
        except (OSError, ConnectionError, ValueError) as error:
            self.receipts.write("disconnect", reason=type(error).__name__)
        finally:
            hb_stop.set()
            link.close()

    def sync_loop(self) -> None:
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        seq = 0
        while not self.stop.is_set():
            if not self._blocked():
                seq += 1
                t1 = time.time()
                try:
                    udp.sendto(json.dumps({"seq": seq, "t1": t1}).encode("utf-8"), (self.host, self.port))
                    reply, t4, stale = recv_matching(udp, seq, SYNC_TIMEOUT_S)
                    offset = ((reply["t2"] - t1) + (reply["t3"] - t4)) / 2.0
                    delay = (t4 - t1) - (reply["t3"] - reply["t2"])
                    self.sync_log.write("sync", seq=seq, t1=t1, t2=reply["t2"], t3=reply["t3"], t4=t4,
                                        offset_s=offset, delay_s=delay, stale_discarded=stale)
                except (OSError, ValueError, KeyError, TypeError):
                    self.sync_log.write("sync_lost", seq=seq)
            self.stop.wait(SYNC_PERIOD_S)
        udp.close()

    def _maybe_drop(self) -> None:
        elapsed = time.monotonic() - self.t0
        while self.drops and elapsed >= self.drops[0][0]:
            start, length = self.drops.pop(0)
            self.blocked_until = time.monotonic() + length
            self.receipts.write("drop_start", planned_at_s=start, length_s=length)
            if self.link is not None:
                self.link.close()
            self.link = None

    def forward_once(self) -> None:
        frames = self.runtime / "frames"
        try:
            pointer = (frames / "latest.json").read_bytes()
            manifest = json.loads(pointer.decode("utf-8"))
            frame_id = int(manifest["frame_id"])
        except (OSError, ValueError, KeyError):
            return
        if frame_id == self.last_sent:
            return
        published_unix = manifest.get("published_unix_s")
        if isinstance(published_unix, (int, float)) and published_unix < self.started_unix - STALE_POINTER_GRACE_S:
            if self._stale_skip != (frame_id, published_unix):
                self._stale_skip = (frame_id, published_unix)
                self.counters["stale_pointers_skipped"] += 1
                self.receipts.write("skip_stale_pointer", frame_id=frame_id, published_unix_s=published_unix,
                                    relay_started_unix=round(self.started_unix, 6))
            return
        try:
            image = (frames / Path(manifest["image_file"]).name).read_bytes()
            metadata = (frames / Path(manifest["metadata_file"]).name).read_bytes()
        except OSError:
            self.counters["bundles_skipped_missing"] += 1
            self.receipts.write("skip_missing", frame_id=frame_id)
            self.last_sent = frame_id
            return
        link = self.link
        if link is None or not link.alive:
            return
        try:
            heads = []
            for path, payload, role in ((f"frames/{Path(manifest['image_file']).name}", image, "member"),
                                        (f"frames/{Path(manifest['metadata_file']).name}", metadata, "member"),
                                        (FORWARD_POINTER, pointer, "pointer")):
                heads.append(link.send({"kind": "file", "path": path, "role": role, "bundle": frame_id}, payload))
        except (OSError, ConnectionError) as error:
            self.counters["send_failures"] += 1
            self.receipts.write("send_fail", frame_id=frame_id, reason=type(error).__name__)
            return
        self.last_sent = frame_id
        self.counters["bundles_sent"] += 1
        self.receipts.write("send_bundle", frame_id=frame_id, published_unix_s=manifest.get("published_unix_s"),
                            seqs=[h["seq"] for h in heads], sha256=[h["sha256"] for h in heads], bytes=[len(image), len(metadata), len(pointer)],
                            send_unix_first=heads[0]["send_unix"], send_unix_last=heads[-1]["send_unix"])

    def run(self, duration_s: float) -> dict[str, Any]:
        self.t0 = time.monotonic()
        self.started_unix = time.time()
        self.receipts.write("start", host=self.host, port=self.port, runtime=str(self.runtime))
        threading.Thread(target=self.sync_loop, daemon=True).start()
        deadline = self.deadline = self.t0 + duration_s
        try:
            while time.monotonic() < deadline and not self.stop.is_set():
                self._maybe_drop()
                if (self.link is None or not self.link.alive) and not self._blocked():
                    if self.link is not None:
                        self.receipts.write("link_down")
                    self.link = None
                    self.link = self.connect()
                    if self.link is not None and self.blocked_until:
                        self.receipts.write("reconnected_after_drop")
                if self.link is not None and self.link.alive:
                    self.forward_once()
                time.sleep(POLL_S)
        finally:
            self.stop.set()
            if self.link is not None:
                self.link.close()
            for thread in self.threads:
                thread.join(timeout=DEAD_AFTER_S)
            self.receipts.write("stop", **self.counters)
            self.receipts.close()
            self.sync_log.close()
        return dict(self.counters)


# --- 回声应答器 ----------------------------------------------------------------


class EchoResponder:
    """零模型回声：镜像 `latest.json` 指向新帧即写绑定同 `frame_id` 的 `tracking_observation.json`。"""

    BOX = (0.45, 0.45, 0.1, 0.1)

    def __init__(self, runtime: Path, log_dir: Path):
        self.runtime = Path(runtime).expanduser()
        common.refuse_protected(self.runtime)
        self.receipts = Receipts(Path(log_dir) / "echo-receipts.jsonl")
        self.last = -1

    def poll_once(self) -> bool:
        try:
            manifest = json.loads((self.runtime / "frames" / "latest.json").read_text(encoding="utf-8"))
            frame_id = int(manifest["frame_id"])
        except (OSError, ValueError, KeyError):
            return False
        if frame_id <= self.last:
            return False
        seen_unix, seen_mono = now_pair()
        try:
            metadata = json.loads((self.runtime / "frames" / Path(manifest["metadata_file"]).name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.receipts.write("bundle_missing", frame_id=frame_id)
            self.last = frame_id
            return False
        from controller.tracking_entry import observation  # noqa: PLC0415 — 板上代码束内的同一写桥函数

        observation(frame_id, *self.BOX, track_id="eng-jet-echo", confidence=1.0, expires_after_s=2.0, runtime=self.runtime)
        written_unix, written_mono = now_pair()
        self.last = frame_id
        capture_unix = metadata.get("capture_unix_s")
        self.receipts.write("echo", frame_id=frame_id, seen_unix=round(seen_unix, 6), seen_mono=round(seen_mono, 6),
                            written_unix=round(written_unix, 6), written_mono=round(written_mono, 6), capture_unix_s=capture_unix,
                            capture_age_s=None if capture_unix is None else round(seen_unix - float(capture_unix), 6),
                            load_elapsed_s=round(written_mono - seen_mono, 6))
        return True

    def run(self, duration_s: float) -> int:
        deadline = time.monotonic() + duration_s
        count = 0
        while time.monotonic() < deadline:
            count += int(self.poll_once())
            time.sleep(0.002)
        self.receipts.write("stop", echoed=count)
        self.receipts.close()
        return count


# --- 分析（桌面机，读两端收据）-----------------------------------------------------


def _offset_at(syncs: Sequence[Mapping[str, Any]], unix: float, window: int = 5) -> float | None:
    """板 − 桌面偏差估计：取时间上最近的 `window` 个样本中 delay 最小者的 offset（NTP 式最小延迟过滤）。"""
    if not syncs:
        return None
    nearest = sorted(syncs, key=lambda s: abs(s["t1"] - unix))[:window]
    return min(nearest, key=lambda s: s["delay_s"])["offset_s"]


def drift_ppm(syncs: Sequence[Mapping[str, Any]]) -> float | None:
    """偏差随时间的最小二乘斜率（ppm）；只用往返延迟 ≤ 中位数的样本（NTP 式最小延迟过滤）。"""
    if not syncs:
        return None
    median_delay = common.nearest_rank([s["delay_s"] for s in syncs], 0.5)
    points = [(s["t1"], s["offset_s"]) for s in syncs if s["delay_s"] <= median_delay]
    if len(points) < 3:
        return None
    mx = sum(p[0] for p in points) / len(points)
    my = sum(p[1] for p in points) / len(points)
    den = sum((p[0] - mx) ** 2 for p in points)
    return None if den == 0 else round(1e6 * sum((p[0] - mx) * (p[1] - my) for p in points) / den, 3)


#: AC-6「恢复后 60 s 内到达时延回到稳态」的读法（K1K3K4补跑F 预注册，正式断链轮运行前写定）：稳态基线 = 断链开始前 60 s 内
#: 桌面机发布、且不落在更早断链扰动窗 [断链开始, 重连 + 10 s] 内的帧的偏差校正到达时延；稳态阈值 = 基线 p95（nearest-rank，附 n）；
#: 恢复时刻 = 重连后首个满足「自该帧起连续 10 个板上发布帧（5 Hz 约 2 s）到达时延均 ≤ 阈值」的帧的桌面机发布时刻；回稳时间 = 恢复时刻 − 重连时刻。
RECOVERY_BASELINE_S = 60.0
RECOVERY_CONSECUTIVE = 10
RECOVERY_LIMIT_S = 60.0
RECOVERY_DISTURBED_TAIL_S = 10.0


def _arrivals(publishes: Mapping[int, Mapping[str, Any]], published: Mapping[int, Mapping[str, Any]],
              syncs: Sequence[Mapping[str, Any]]) -> dict[int, dict[str, float]]:
    """每个板上发布帧：桌面机发布时刻（桌面钟）、板上发布时刻（板钟）、偏差校正到达时延（ms）。"""
    out: dict[int, dict[str, float]] = {}
    for fid, pub in publishes.items():
        desktop_pub = published.get(fid, {}).get("published_unix_s") or pub.get("published_unix_desktop")
        if desktop_pub is None:
            continue
        offset = _offset_at(syncs, float(desktop_pub))
        row = {"desktop_pub": float(desktop_pub), "board_pub": float(pub["pub_unix"]),
               "raw_ms": (pub["pub_unix"] - float(desktop_pub)) * 1000.0}
        if offset is not None:
            row["offset_s"] = offset
            row["ms"] = (pub["pub_unix"] - float(desktop_pub) - offset) * 1000.0
        out[fid] = row
    return out


def recovery_after(arrivals: Mapping[int, Mapping[str, float]], reconnect_unix: float, threshold_ms: float | None,
                   consecutive: int = RECOVERY_CONSECUTIVE) -> dict[str, Any]:
    """按预注册读法求回稳：重连后按桌面机发布时刻排序的板上发布帧，首个起连续 `consecutive` 帧到达时延均 ≤ 阈值的帧。"""
    after = sorted((row["desktop_pub"], fid, row.get("ms")) for fid, row in arrivals.items() if row["desktop_pub"] >= reconnect_unix - 1.0)
    after = [item for item in after if item[2] is not None]
    # 重连后第一个板上发布帧（含重连瞬间补发的当前 latest；其桌面机发布时刻可早于重连 ≤ 1 帧间隔）。
    first = next(iter(after), None)
    first_bundle = None if first is None else {"frame_id": first[1], "arrival_ms": round(first[2], 3),
                                               "desktop_pub_minus_reconnect_s": round(first[0] - reconnect_unix, 3)}
    if threshold_ms is None:
        return {"recovered": None, "reason": "无稳态基线", "first_bundle_after_reconnect": first_bundle}
    for index in range(len(after) - consecutive + 1):
        window = after[index:index + consecutive]
        if all(ms <= threshold_ms for _t, _fid, ms in window):
            t, fid, _ms = window[0]
            seconds = max(0.0, t - reconnect_unix)
            return {"recovered": True, "frame_id": fid, "recovery_s": round(seconds, 3), "within_limit": seconds <= RECOVERY_LIMIT_S,
                    "first_bundle_after_reconnect": first_bundle}
    return {"recovered": False, "recovery_s": None, "within_limit": False, "first_bundle_after_reconnect": first_bundle}


def disconnect_analysis(desk: Sequence[Mapping[str, Any]], board: Sequence[Mapping[str, Any]], syncs: Sequence[Mapping[str, Any]],
                        replay: Sequence[Mapping[str, Any]], arrivals: Mapping[int, Mapping[str, float]],
                        track: Sequence[Mapping[str, Any]] = (), echoes: Sequence[Mapping[str, Any]] = ()) -> list[dict[str, Any]]:
    """AC-6：每次有意断链（桌面机 `drop_start`）——两侧存活、断链期间板侧写桥次数、恢复后 frame_id 缺口、latest 帧差、
    TrackLoop 终止/继续语义、回稳时间（预注册读法见 `RECOVERY_*`）、不补发过期帧核查。时刻换算：板钟 = 桌面钟 + 偏差。"""
    drops = [e for e in desk if e["ev"] == "drop_start"]
    connects = sorted(e["unix"] for e in desk if e["ev"] == "connect")
    sent_ids = {e["frame_id"] for e in desk if e["ev"] == "send_bundle"}
    pub_rows = sorted((e for e in board if e["ev"] == "publish"), key=lambda e: e["pub_unix"])
    disturbed: list[tuple[float, float]] = []
    out = []
    for index, drop in enumerate(drops):
        t_drop = float(drop["unix"])
        t_reconnect = next((t for t in connects if t > t_drop), None)
        off = _offset_at(syncs, t_drop) or 0.0
        end = t_reconnect if t_reconnect is not None else t_drop + float(drop.get("length_s", 0))
        b0, b1 = t_drop + off, end + off
        in_window = lambda t: b0 <= float(t) <= b1  # noqa: E731
        board_close = next((e for e in board if e["ev"] == "close" and float(e["unix"]) >= b0 - 0.5), None)
        board_accept = next((e for e in board if e["ev"] == "accept" and float(e["unix"]) > b0), None)
        before = [e["frame_id"] for e in pub_rows if e["pub_unix"] < b0]
        after = [e["frame_id"] for e in pub_rows if e["pub_unix"] > b1]
        last_before, first_after = (before[-1] if before else None), (after[0] if after else None)
        window_published = [r["frame_id"] for r in replay if t_drop <= float(r["published_unix_s"]) <= end]
        window_sent = sorted(f for f in window_published if f in sent_ids)
        baseline_from = t_drop - RECOVERY_BASELINE_S
        baseline = [row["ms"] for row in arrivals.values() if "ms" in row and baseline_from <= row["desktop_pub"] < t_drop
                    and not any(a <= row["desktop_pub"] <= b for a, b in disturbed)]
        threshold = common.nearest_rank(baseline, 0.95) if baseline else None
        terminal = [e for e in track if e["ev"] == "terminal"]
        terminal_before = [e for e in terminal if float(e["unix"]) < b0]
        terminal_after = [e for e in terminal if float(e["unix"]) >= b0 and (index + 1 >= len(drops) or float(e["unix"]) < float(drops[index + 1]["unix"]) + off)]
        out.append({
            "planned_at_s": drop.get("planned_at_s"), "planned_length_s": drop.get("length_s"),
            "drop_start_unix_desktop": round(t_drop, 6), "reconnect_unix_desktop": None if t_reconnect is None else round(t_reconnect, 6),
            "actual_disconnect_s": None if t_reconnect is None else round(t_reconnect - t_drop, 3),
            "board_detected_close_after_s": None if board_close is None else round(float(board_close["unix"]) - b0, 3),
            "board_accept_after_drop_start_s": None if board_accept is None else round(float(board_accept["unix"]) - b0, 3),
            "board_bridge_writes_during_disconnect": {
                "recv_member": sum(1 for e in board if e["ev"] == "recv_member" and in_window(e["arrive_unix"])),
                "publish_latest": sum(1 for e in board if e["ev"] == "publish" and in_window(e["pub_unix"])),
                "send_return": sum(1 for e in board if e["ev"] == "send_return" and in_window(e["send_unix"])),
                "track_bridge_writes": sum(1 for e in track if e["ev"] == "bridge_write" and in_window(e["written_unix"])),
                "echo_writes": sum(1 for e in echoes if in_window(e["written_unix"])),
                "window_board_clock": [round(b0, 6), round(b1, 6)]},
            "last_published_before": last_before, "first_published_after": first_after,
            "frame_id_gap_after_recovery": None if None in (last_before, first_after) else first_after - last_before - 1,
            "latest_frame_diff": None if None in (last_before, first_after) else first_after - last_before,
            "replay_frames_published_during_disconnect": len(window_published),
            "of_which_sent": window_sent,
            "no_backfill": len(window_sent) <= 1 and (not window_sent or window_sent[-1] == max(window_published)),
            "pointer_refusals_incomplete_in_window": sum(1 for e in board if e["ev"] == "refuse_pointer" and e.get("reason") == "incomplete_bundle"
                                                         and b0 - 1.0 <= float(e["arrive_unix"]) <= b1 + 5.0),
            "trackloop": {"terminal_before_this_drop": [{k: e.get(k) for k in ("unix", "latest", "loop_event", "reason")} for e in terminal_before],
                          "terminal_after_this_drop": [{k: e.get(k) for k in ("unix", "latest", "previous", "loop_event", "reason")} for e in terminal_after],
                          "responder": "track" if track else ("echo" if echoes else None)},
            "steady_baseline_ms": {**common.summary(baseline), "window_desktop_unix": [round(baseline_from, 3), round(t_drop, 3)]},
            "steady_threshold_ms": None if threshold is None else round(threshold, 3),
            "recovery": recovery_after(arrivals, t_reconnect, threshold) if t_reconnect is not None else {"recovered": False, "reason": "未重连"},
            "rule": "回稳读法预注册（relay.RECOVERY_*）：基线 = 断链前 60 s（剔除更早断链扰动窗）偏差校正到达时延 p95；连续 10 帧 ≤ 阈值即回稳；限 60 s",
        })
        if t_reconnect is not None:
            disturbed.append((t_drop, t_reconnect + RECOVERY_DISTURBED_TAIL_S))
    return out


def analyze(desktop_dir: Path, board_dir: Path, replay_receipts: Path) -> dict[str, Any]:
    desk = common.read_jsonl(Path(desktop_dir) / "relay-receipts.jsonl")
    board = common.read_jsonl(Path(board_dir) / "relay-receipts.jsonl")
    syncs = [s for s in common.read_jsonl(Path(desktop_dir) / "clock-sync.jsonl") if s["ev"] == "sync"]
    echo_path = Path(board_dir) / "echo-receipts.jsonl"
    echoes = [e for e in common.read_jsonl(echo_path) if e["ev"] == "echo"] if echo_path.exists() else []
    track_path = Path(board_dir) / "track-receipts.jsonl"
    track = common.read_jsonl(track_path) if track_path.exists() else []
    records_path = Path(board_dir) / "track-records.jsonl"
    records = common.read_jsonl(records_path) if records_path.exists() else []
    replay = common.read_jsonl(replay_receipts)
    published = {r["frame_id"]: r for r in replay}

    sent = [e for e in desk if e["ev"] == "send_bundle"]
    sent_ids = [e["frame_id"] for e in sent]
    board_recv: dict[int, dict[str, Any]] = {}
    member_arrivals: dict[int, dict[str, list[float]]] = {}
    for e in board:
        if e["ev"] == "recv_member" and e["sha_ok"]:
            suffix = e["path"].rsplit(".", 1)[1]
            board_recv.setdefault(e["frame_id"], {})[suffix] = e
            member_arrivals.setdefault(e["frame_id"], {}).setdefault(suffix, []).append(e["arrive_mono"])
    publishes = {e["frame_id"]: e for e in board if e["ev"] == "publish"}
    refusals = [e for e in board if e["ev"] == "refuse_pointer"]
    complete = 0
    for e in sent:
        fid = e["frame_id"]
        members = board_recv.get(fid, {})
        src = published.get(fid, {})
        sha_match = (members.get("jpg", {}).get("sha_ok") and members.get("json", {}).get("sha_ok") and fid in publishes
                     and (not src or (src.get("image_sha256") == e["sha256"][0] and src.get("metadata_sha256") == e["sha256"][1])))
        complete += int(bool(sha_match))
    # 独立复算「latest.json 指向不完整包」：每次发布前，两成员须已在板上以 sha 一致收到（按到达单调时钟；同号帧多次到达时
    # 取任一早于该次发布的到达——旧会话残留指针与本会话同号帧并存时不误判，K1K3K4补跑F f1-echo）。
    pointing_incomplete = 0
    for fid, pub in publishes.items():
        arrivals_of = member_arrivals.get(fid, {})
        if not all(any(t <= pub["arrive_mono"] for t in arrivals_of.get(k, ())) for k in ("jpg", "json")):
            pointing_incomplete += 1
    # 在途整包丢失：已发出、板上无任何成员也无发布（链路故障时内核缓冲内的数据随连接重置丢失；不缓存补发）。
    link_downs = sorted(e["unix"] for e in desk if e["ev"] in ("disconnect", "send_fail", "drop_start"))
    lost_in_flight = []
    for e in sent:
        fid = e["frame_id"]
        if fid in publishes or fid in board_recv:
            continue
        following = next((t for t in link_downs if t >= e["unix"]), None)
        lost_in_flight.append({"frame_id": fid, "send_unix": e["unix"],
                               "next_link_event_after_s": None if following is None else round(following - e["unix"], 3)})
    partial = sorted(fid for fid in board_recv if fid not in publishes and fid in set(sent_ids))
    order = [e["frame_id"] for e in board if e["ev"] == "publish"]
    order_violations = sum(1 for a, b in zip(order, order[1:]) if b <= a) + sum(1 for e in refusals if e.get("reason") == "order_violation")
    incomplete_pointer = sum(1 for e in refusals if e.get("reason") == "incomplete_bundle")

    arrivals = _arrivals(publishes, published, syncs)
    arrival = [row["ms"] for row in arrivals.values() if "ms" in row]
    arrival_raw = [row["raw_ms"] for row in arrivals.values()]

    returns = [e for e in desk if e["ev"] == "recv_return" and e["ok"]]
    echo_by_frame = {e["frame_id"]: e for e in echoes}
    return_ms, e2e_ms = [], []
    track_obs = {e["frame_id"]: e for e in track if e["ev"] == "bridge_write" and e.get("kind") == "observation"}
    track_return_ms, track_e2e_ms = [], []
    for e in returns:
        fid = e.get("content_frame_id")
        if fid is None or e["path"] != "tracking_observation.json":
            continue
        offset = _offset_at(syncs, e["arrive_unix"])
        echo = echo_by_frame.get(fid)
        if echo is not None:
            if offset is not None:
                return_ms.append((e["arrive_unix"] - (echo["written_unix"] - offset)) * 1000.0)
            if fid in published:
                e2e_ms.append((e["arrive_unix"] - published[fid]["published_unix_s"]) * 1000.0)
        written = track_obs.get(fid)
        if written is not None:
            if offset is not None:
                track_return_ms.append((e["arrive_unix"] - (written["written_unix"] - offset)) * 1000.0)
            if fid in published:
                track_e2e_ms.append((e["arrive_unix"] - published[fid]["published_unix_s"]) * 1000.0)
    processes = [e for e in track if e["ev"] == "process"]
    if echoes:
        age_rows = [(e["capture_age_s"], e["seen_unix"]) for e in echoes if e.get("capture_age_s") is not None]
        loads = [e["load_elapsed_s"] for e in echoes]
    else:
        age_rows = [(e["capture_age_s"], e["seen_unix"]) for e in processes if e.get("capture_age_s") is not None]
        loads = [e["load_elapsed_s"] for e in processes if e.get("load_elapsed_s") is not None]
    ages = [a for a, _t in age_rows]
    ages_corrected = [a - off for a, t in age_rows if (off := _offset_at(syncs, t)) is not None]
    offsets = [s["offset_s"] * 1000.0 for s in syncs]
    gaps = [b - a - 1 for a, b in zip(order, order[1:]) if b - a > 1]
    connects = [e for e in desk if e["ev"] in ("connect", "drop_start", "disconnect", "link_down", "reconnected_after_drop")]
    result = {
        "responder": "track" if track else ("echo" if echoes else None),
        "replay_frames_published": len(replay),
        "bundles_sent": len(sent),
        "bundles_complete_on_board": complete,
        "completeness": None if not sent else round(complete / len(sent), 6),
        "order_violations": order_violations,
        "latest_pointing_to_incomplete_bundle": pointing_incomplete,
        "pointer_refusals_incomplete": incomplete_pointer,
        "bundles_lost_in_flight": {"count": len(lost_in_flight), "items": lost_in_flight},
        "bundles_partial_on_board_unpublished": partial,
        "board_sha_mismatch": sum(1 for e in board if e["ev"] == "sha_mismatch"),
        "board_rejected_paths": sum(1 for e in board if e["ev"] == "reject_path"),
        "arrival_latency_ms_offset_corrected": common.summary(arrival),
        "arrival_latency_ms_raw_unix_difference": common.summary(arrival_raw),
        "clock": {"samples": len(syncs), "span_s": round(syncs[-1]["t1"] - syncs[0]["t1"], 1) if syncs else 0.0,
                  "offset_ms_board_minus_desktop": common.summary(offsets),
                  "rtt_ms": common.summary([s["delay_s"] * 1000.0 for s in syncs]), "drift_ppm": drift_ppm(syncs)},
        "return_echo": {"return_latency_ms": common.summary(return_ms), "end_to_end_ms": common.summary(e2e_ms),
                        "echoes": len(echoes), "returns_received": len(returns)},
        "capture_age_s": {**common.summary(ages, 4), "over_T_STALL_S": sum(1 for a in ages if a > T_STALL_S), "T_STALL_S": T_STALL_S,
                          "basis": "板侧墙钟（看到新帧时刻）− capture_unix_s（桌面机墙钟），未校正两机偏差"},
        "capture_age_s_offset_corrected": {**common.summary(ages_corrected, 4),
                                           "over_T_STALL_S": sum(1 for a in ages_corrected if a > T_STALL_S)},
        "load_elapsed_s": {**common.summary(loads, 5), "over_T_pub": sum(1 for v in loads if v > T_PUB_S), "T_pub_s": T_PUB_S},
        "frame_id_gaps_on_board": {"count": len(gaps), "frames_missing": sum(gaps)},
        # 全量保留（复核 R1-2：原 `[:50]` 截断使派生的传输中事件计数可能少计）；`link_events_total` 供分列函数核对未截断。
        "link_events": [{k: e.get(k) for k in ("ev", "unix", "reason", "length_s")} for e in connects],
        "link_events_total": len(connects),
        "sent_frame_id_range": [min(sent_ids), max(sent_ids)] if sent_ids else None,
        "returns_by_path": {name: sum(1 for e in returns if e["path"] == name) for name in RETURN_FILES},
        "process_stops": {"desktop_relay": next((e for e in desk if e["ev"] == "stop"), None) is not None,
                          "board_relay": next((e for e in board if e["ev"] == "stop"), None) is not None,
                          "responder": (next((e for e in track if e["ev"] == "stop"), None) is not None) if track else None},
    }
    if track:
        frame_ages = [r["frame_age_ms"] for r in records if r.get("frame_age_ms") is not None]
        frame_ages_corrected = [r["frame_age_ms"] - 1000.0 * off for r in records if r.get("frame_age_ms") is not None
                                and (off := _offset_at(syncs, float(r["capture_unix_s"]))) is not None]
        stop = next((e for e in track if e["ev"] == "stop"), {})
        init = next((e for e in track if e["ev"] == "init"), None)
        result["return_track"] = {
            "return_latency_ms": common.summary(track_return_ms), "end_to_end_ms": common.summary(track_e2e_ms),
            "observations_written": len(track_obs), "returns_received_tracking_observation": result["returns_by_path"]["tracking_observation.json"],
            "init_detection": next(({k: e.get(k) for k in ("frame_id", "pick", "t_detect_ms", "init_source")} for e in track
                                    if e["ev"] == "init_detection"), None),
            "init": None if init is None else {k: init.get(k) for k in ("frame_id", "box_norm", "t_init_ms", "writes", "loop_state")},
            "process_calls": len(processes), "frames_processed": sum(int(e["processed"]) for e in processes),
            "batches_over_1": sum(1 for e in processes if int(e["processed"]) > 1),
            "processing_elapsed_s": common.summary([e["processing_elapsed_s"] for e in processes], 5),
            "frame_age_ms": {**common.summary(frame_ages), "over_T_stall_ms": sum(1 for v in frame_ages if v > T_STALL_S * 1000.0),
                             "ratio_over_T_stall": None if not frame_ages else round(sum(1 for v in frame_ages if v > T_STALL_S * 1000.0) / len(frame_ages), 6),
                             "basis": "TrackLoop 逐帧记录 frame_age_ms = 板墙钟 − capture_unix_s（桌面机墙钟），未校正"},
            "frame_age_ms_offset_corrected": {**common.summary(frame_ages_corrected),
                                              "over_T_stall_ms": sum(1 for v in frame_ages_corrected if v > T_STALL_S * 1000.0)},
            "loop_states": {s: sum(1 for r in records if r.get("loop_state") == s) for s in sorted({str(r.get("loop_state")) for r in records})},
            "events": {ev: sum(1 for r in records if r.get("event") == ev) for ev in sorted({str(r.get("event")) for r in records if r.get("event")})},
            "terminal": [{k: e.get(k) for k in ("unix", "latest", "previous", "loop_event", "reason")} for e in track if e["ev"] == "terminal"],
            "post_terminal_frames": sum(1 for e in track if e["ev"] == "post_terminal_frame"),
            "exceptions": [{k: e.get(k) for k in ("type", "message")} for e in track if e["ev"] == "exception"],
            "outcome": stop.get("outcome"),
        }
    if any(e["ev"] == "drop_start" for e in desk):
        result["disconnects"] = disconnect_analysis(desk, board, syncs, replay, arrivals, track, echoes)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    b = sub.add_parser("board")
    b.add_argument("--runtime", type=Path, default=Path(os.path.expanduser(f"{common.BOARD_ROOT}/runtime")))
    b.add_argument("--log-dir", type=Path, required=True)
    b.add_argument("--port", type=int, default=DEFAULT_PORT)
    b.add_argument("--bind", default="0.0.0.0")
    b.add_argument("--duration-s", type=float, required=True)
    d = sub.add_parser("desktop")
    d.add_argument("--runtime", type=Path, default=common.RUNTIME_DESKTOP)
    d.add_argument("--log-dir", type=Path, required=True)
    d.add_argument("--host", required=True)
    d.add_argument("--port", type=int, default=DEFAULT_PORT)
    d.add_argument("--duration-s", type=float, required=True)
    d.add_argument("--drops", default=None)
    e = sub.add_parser("echo")
    e.add_argument("--runtime", type=Path, default=Path(os.path.expanduser(f"{common.BOARD_ROOT}/runtime")))
    e.add_argument("--log-dir", type=Path, required=True)
    e.add_argument("--duration-s", type=float, required=True)
    a = sub.add_parser("analyze")
    a.add_argument("--desktop-log", type=Path, required=True)
    a.add_argument("--board-log", type=Path, required=True)
    a.add_argument("--replay-receipts", type=Path, required=True)
    a.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.action == "board":
        result: Any = BoardRelay(args.runtime, args.log_dir, args.port, args.bind).run(args.duration_s)
    elif args.action == "desktop":
        result = DesktopRelay(args.runtime, args.log_dir, args.host, args.port, parse_drops(args.drops)).run(args.duration_s)
    elif args.action == "echo":
        result = EchoResponder(args.runtime, args.log_dir).run(args.duration_s)
    else:
        result = analyze(args.desktop_log, args.board_log, args.replay_receipts)
        if args.out:
            common.write_json(args.out, result)
    print(json.dumps(result, ensure_ascii=False, default=str)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
