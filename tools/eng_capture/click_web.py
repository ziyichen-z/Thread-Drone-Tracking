"""P1-ENG-CAPTURE-001 C7 / §3.5：本机点击页（捕获模式 `run --language off` 的唯一操作入口）。

* 只监听 `127.0.0.1`；POST 须带服务生成 nonce，Host/Origin 必须为本机（同 `tools/eng_loop2/operator_web.py` 口径）。
* 页面按 `runtime/frames/latest.json` 显示帧；浏览器对**实际取回并解码**的字节算 sha256，点击时提交该 sha 与该帧
  frame_id、按自然像素换算的 (x_px, y_px)。服务端收到点击先记 `click_received_unix_s` 与当刻 `latest.json` 的
  frame_id（e2e 起点），再经复用的 `Submitter`（单在途、seal/UNKNOWN）提交；`cli` = `InProcessSend`（进程内调
  `controller.language_loop.send_request`，退出码语义同 CLI：0 回执 / 2 拒绝 / 4 WRITER_BUSY / 5 无回执），
  `argv_builder` = `ClickArgv(CliRunner)`（只为 click/stop 组 argv 供记录）。另有「停止会话」按钮；
  无确认、无自由文本、无语言按钮。
* 保真模式（AC-27）：以归档准入帧显示，点击不提交，服务端在所点像素处画标记并另存样帧，供人眼核对
  「标记落在所点车上、像素坐标无缩放偏移」；样帧只写 `outputs/eng-capture/`。
* 六基预登记模式（AC-28）：只显示计划列出的六张原始 k−1 帧（不叠任何框），人逐张点目标车，写六基剧本。

本文件不读真值、评分产物或 `CoverageEvaluator` 输出（AC-16），不写桥文件/锁以外的任何 runtime 文件
（请求经 `send_request` 的写者锁与原子写）。
"""

from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import math
from pathlib import Path
import re
import secrets
import sys
import threading
import time
import uuid
from typing import Any, Callable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - 直接以脚本运行时
    sys.path.insert(0, str(REPO_ROOT))

from controller import language_bridge as bridge  # noqa: E402
from controller.language_bridge import LanguageBridgeError, WriterBusy  # noqa: E402
from controller.language_loop import RECEIPT_WAIT_S, build_parser, click_fields, resolves_to_shared_runtime, send_request  # noqa: E402
from tools.eng_loop2.operator_web import CliRunner, OpsLog, Submitter  # noqa: E402

HOST = "127.0.0.1"
DEFAULT_PORT = 8774
MAX_BODY = 4096
MAX_FRAME_BYTES = 8_000_000
CLICK_LOG = "click-web.jsonl"
CLICK_ACTIONS = frozenset({"click", "stop"})
FRAME_NAME = re.compile(r"^frame_[0-9]{10}\.jpg$")
SHA_HEX = re.compile(r"^[0-9a-f]{64}$")
#: AC-28 六基预登记（与 `tools/eng_capture/replay.py` 同名常量同值；本文件不导入 replay，AC-16）。
ROLL_PLAN_SCHEMA = "p1-eng-capture-001-roll-base-plan/v1"
ROLL_CLICK_SCHEMA = "p1-eng-capture-001-roll-click-script/v1"
ROLL_BASES = 6


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


# --- 提交通道（复用 `Submitter`，§2.5 两处 diff） -----------------------------------------


class ClickArgv(CliRunner):
    """只为 `click`/`stop` 组 `python -m controller.language_loop <action>` 的 argv（供记录与可复现）。"""

    def argv(  # type: ignore[override]
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
        x_px: float | None = None,
        y_px: float | None = None,
        frame_id: int | None = None,
        image_sha256: str | None = None,
        page_latest_frame_id: int | None = None,
        page_click_unix_s: float | None = None,
    ) -> list[str]:
        if action not in CLICK_ACTIONS:
            raise ValueError(f"action {action!r} outside the click page closed set")
        if any(v is not None for v in (token, index, instruction, intent, delay_s)):
            raise ValueError("the click page sends no token/index/instruction/intent/delay")
        argv = [
            self.python, "-m", "controller.language_loop", action,
            "--session-id", session_id, "--runtime", str(self.runtime),
            "--allow-shared-runtime", "--request-id", request_id,
        ]
        if action == "click":
            if x_px is None or y_px is None or frame_id is None or image_sha256 is None:
                raise ValueError("click needs x_px, y_px, frame_id and image_sha256")
            argv += ["--x-px", repr(float(x_px)), "--y-px", repr(float(y_px)), "--frame-id", str(int(frame_id)),
                     "--image-sha256", str(image_sha256)]
            if page_latest_frame_id is not None:
                argv += ["--page-latest-frame-id", str(int(page_latest_frame_id))]
            if page_click_unix_s is not None:
                argv += ["--page-click-unix-s", repr(float(page_click_unix_s))]
        return argv


class InProcessSend:
    """`Submitter.cli` 的进程内实现：解析 `ClickArgv` 组的 argv（同一 `build_parser`），直接调 `send_request`。

    退出码语义同 CLI（`controller.language_loop.main`）：0 = 有回执；2 = 参数/守卫拒绝（未写请求）；
    4 = WRITER_BUSY（未写请求）；5 = 等待窗内无回执（结果未知）。避免子进程启动开销计入 e2e。"""

    def __init__(self, *, send: Callable[..., Mapping[str, Any]] = send_request, wait_s: float = RECEIPT_WAIT_S):
        self._send = send
        self._wait_s = wait_s
        self._parser = build_parser()

    def __call__(self, argv: Sequence[str]) -> dict[str, Any]:
        args = list(argv)
        try:
            index = args.index("controller.language_loop")
        except ValueError:
            return {"exit": 2, "timeout": False, "stdout": "", "stderr": "argv is not a language_loop command"}
        try:
            arguments = self._parser.parse_args(args[index + 1:])
        except SystemExit as exit_:  # argparse 拒绝 = CLI 退出码 2
            return {"exit": int(exit_.code or 2), "timeout": False, "stdout": "", "stderr": "argument error"}
        action = arguments.command.replace("-", "_")
        if action not in CLICK_ACTIONS:
            return {"exit": 2, "timeout": False, "stdout": "", "stderr": f"action {action!r} outside the click page closed set"}
        if resolves_to_shared_runtime(Path(arguments.runtime)) and not getattr(arguments, "allow_shared_runtime", False):
            return {"exit": 2, "timeout": False, "stdout": "", "stderr": "shared runtime refused"}
        click = click_fields(arguments) if action == "click" else None
        if click is not None:
            try:
                bridge.validate_click_fields(click)
            except LanguageBridgeError as exception:
                return {"exit": 2, "timeout": False, "stdout": "", "stderr": f"click_invalid: {exception}"}
        try:
            outcome = dict(self._send(
                Path(arguments.runtime),
                session_id=arguments.session_id,
                action=action,
                token=None,
                request_id=arguments.request_id,
                wait_s=self._wait_s,
                click=click,
            ))
        except WriterBusy:
            return {"exit": 4, "timeout": False, "stdout": "", "stderr": "WRITER_BUSY"}
        except LanguageBridgeError as exception:
            return {"exit": 2, "timeout": False, "stdout": "", "stderr": str(exception)}
        stdout = json.dumps(outcome, ensure_ascii=False, indent=2)
        return {"exit": 0 if outcome.get("receipt") else 5, "timeout": False, "stdout": stdout, "stderr": ""}


# --- 页面应用 ----------------------------------------------------------------------


def read_latest(frames_directory: Path) -> tuple[int | None, Path | None]:
    try:
        manifest = json.loads((Path(frames_directory) / "latest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None
    frame_id = manifest.get("frame_id") if isinstance(manifest, dict) else None
    name = manifest.get("image_file") if isinstance(manifest, dict) else None
    if isinstance(frame_id, bool) or not isinstance(frame_id, int) or not isinstance(name, str) or not FRAME_NAME.match(name):
        return None, None
    return frame_id, Path(frames_directory) / name


class ClickApp:
    """实时模式：显示 `latest.json` 指向的帧；点击/停止经 `Submitter`（单在途、每会话 stop 至多一次、seal）。"""

    mode = "live"

    def __init__(self, runtime: Path, session_id: str, submitter: Submitter, log: OpsLog, *, clock: Callable[[], float] = time.time):
        self.runtime = Path(runtime)
        self.frames = self.runtime / "frames"
        self.session_id = session_id
        self.submitter = submitter
        self.log = log
        self.clock = clock
        self.nonce = secrets.token_hex(16)
        self.lock = threading.Lock()

    def frame(self, _query: Mapping[str, str]) -> tuple[bytes, int] | None:
        frame_id, path = read_latest(self.frames)
        if frame_id is None or path is None:
            return None
        try:
            data = path.read_bytes()
        except OSError:
            return None
        if len(data) > MAX_FRAME_BYTES:
            return None
        return data, frame_id

    def click(self, body: Mapping[str, Any]) -> dict[str, Any]:
        received = float(self.clock())
        latest, _path = read_latest(self.frames)
        frame_id, sha, x_px, y_px = body.get("frame_id"), body.get("image_sha256"), body.get("x_px"), body.get("y_px")
        # R1-3（AC-22 分母 = 全部发出的点击）：每次点击一个 click_id，写进 click_received 与提交绑定（submit_begin/refused/
        # submit_result 的 binding 都带它），提交返回后再补一行 click_submitted（click_id → request_id 或页面本地拒绝原因），
        # 读数按 click_id 配对，不按数组位置。
        click_id = uuid.uuid4().hex
        record = {"click_id": click_id, "click_received_unix_s": received, "latest_frame_id_at_click": latest, "frame_id": frame_id,
                  "image_sha256": sha, "x_px": x_px, "y_px": y_px, "display": body.get("display")}
        if (isinstance(frame_id, bool) or not isinstance(frame_id, int) or not isinstance(sha, str) or not SHA_HEX.match(sha)
                or not _finite(x_px) or not _finite(y_px)):
            self.log.write("click_refused", reason="malformed_click", **record)
            return {"ok": False, "refused": True, "message": "点击字段不完整，本次未发送"}
        self.log.write("click_received", **record)
        reply = self.submitter.submit(
            source="click_web",
            action="click",
            session_id=self.session_id,
            binding={"frame_id": frame_id, "image_sha256": sha, "x_px": float(x_px), "y_px": float(y_px), "click_id": click_id},
            binding_key=f"click:{click_id}",
            on_reply=self._record_reply,
            extra_argv={
                "x_px": float(x_px),
                "y_px": float(y_px),
                "frame_id": int(frame_id),
                "image_sha256": sha,
                "page_latest_frame_id": latest,
                "page_click_unix_s": received,
            },
        )
        self.log.write("click_submitted", click_id=click_id, request_id=reply.get("request_id"), ok=bool(reply.get("ok")),
                       refused=bool(reply.get("refused")), sealed=bool(reply.get("sealed")), unknown=bool(reply.get("unknown")),
                       message=reply.get("message"))
        return dict(reply, click_received_unix_s=received, latest_frame_id_at_click=latest)

    def _record_reply(self, reply: Mapping[str, Any]) -> None:
        self.log.write("click_reply", **dict(reply))
        if reply.get("unknown"):
            # W4：结果未知即封住本会话业务动作（之后只放行 stop 至多一次）。
            self.submitter.seal(self.session_id, "unknown_result")

    def stop(self, _body: Mapping[str, Any]) -> dict[str, Any]:
        return self.submitter.submit(
            source="click_web", action="stop", session_id=self.session_id,
            binding={"stop": True}, binding_key=f"stop:{self.session_id}",
            on_reply=lambda reply: self.log.write("stop_reply", **dict(reply)),
            extra_argv={},
        )

    def state(self) -> dict[str, Any]:
        try:
            document = bridge.read_tracker_state(self.runtime)
        except LanguageBridgeError:
            document = None
        tracker_state = (document or {}).get("tracker_state", {}) if document else {}
        return {
            "mode": self.mode,
            "session_id": self.session_id,
            "state": tracker_state.get("state"),
            "reason": tracker_state.get("reason"),
            "track_id": tracker_state.get("track_id"),
            "sealed": self.submitter.sealed_reason(self.session_id),
            "unknown": self.submitter.unknown_entries(),
        }


class FidelityApp:
    """AC-27 保真模式：以归档准入帧显示；点击不提交，服务端在所点像素处画十字与圆并另存样帧。"""

    mode = "fidelity"

    def __init__(self, frames_directory: Path, frame_ids: Sequence[int], output_directory: Path, log: OpsLog,
                 *, clock: Callable[[], float] = time.time, register_labels: Sequence[str] = (), registered_by: str | None = None):
        self.frames = Path(frames_directory)
        self.frame_ids = [int(v) for v in frame_ids]
        if not self.frame_ids:
            raise ValueError("fidelity mode needs at least one archived frame id")
        self.output = Path(output_directory)
        self.output.mkdir(parents=True, exist_ok=True)
        self.log = log
        self.clock = clock
        self.nonce = secrets.token_hex(16)
        self.samples: list[dict[str, Any]] = []
        self.lock = threading.Lock()
        #: AC-17 预登记：人只看准入原始帧，按给定标签顺序点击，即写剧本（不读真值）。
        self.register_labels = list(register_labels)
        self.registered_by = registered_by

    def _write_script(self) -> None:
        if not self.register_labels:
            return
        clicks = [
            {"label": label, "frame_id": sample["frame_id"], "x_px": sample["x_px"], "y_px": sample["y_px"],
             "image_sha256": sample["image_sha256"]}
            for label, sample in zip(self.register_labels, self.samples)
        ]
        script = {"schema_version": "p1-eng-capture-001-click-script/v1", "registered_by": self.registered_by,
                  "registered_at_unix_s": float(self.clock()), "method": "click_web fidelity（只看准入原始帧，不读真值）",
                  "clicks": clicks}
        (self.output / "click-script.json").write_text(json.dumps(script, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    def _path(self, frame_id: int) -> Path:
        return self.frames / f"frame_{int(frame_id):010d}.jpg"

    def frame(self, query: Mapping[str, str]) -> tuple[bytes, int] | None:
        try:
            position = int(query.get("i", "0"))
        except ValueError:
            return None
        if not 0 <= position < len(self.frame_ids):
            return None
        frame_id = self.frame_ids[position]
        try:
            return self._path(frame_id).read_bytes(), frame_id
        except OSError:
            return None

    def click(self, body: Mapping[str, Any]) -> dict[str, Any]:
        frame_id, sha, x_px, y_px = body.get("frame_id"), body.get("image_sha256"), body.get("x_px"), body.get("y_px")
        if (isinstance(frame_id, bool) or not isinstance(frame_id, int) or frame_id not in self.frame_ids
                or not _finite(x_px) or not _finite(y_px)):
            return {"ok": False, "message": "点击字段不完整"}
        data = self._path(frame_id).read_bytes()
        if sha != sha256_bytes(data):
            self.log.write("fidelity_refused", reason="sha_mismatch", frame_id=frame_id, image_sha256=sha)
            return {"ok": False, "message": "浏览器解码字节与归档帧 sha 不符"}
        with self.lock:
            index = len(self.samples) + 1
            png = self.output / f"click-fidelity-{index:02d}-frame{frame_id:04d}.png"
            drawn = draw_marker(data, float(x_px), float(y_px), png)
            sample = {"index": index, "frame_id": frame_id, "image_sha256": sha, "x_px": float(x_px), "y_px": float(y_px),
                      "display": body.get("display"), "png": str(png) if drawn else None, "at_unix_s": float(self.clock())}
            self.samples.append(sample)
        (self.output / "click-fidelity-samples.json").write_text(json.dumps(self.samples, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        self._write_script()
        self.log.write("fidelity_click", **sample)
        return {"ok": True, "sample": sample}

    def stop(self, _body: Mapping[str, Any]) -> dict[str, Any]:
        return {"ok": False, "message": "保真模式没有会话可停"}

    def state(self) -> dict[str, Any]:
        return {"mode": self.mode, "frames": len(self.frame_ids), "samples": list(self.samples)}


class RollRegisterApp(FidelityApp):
    """AC-28（IR-7 新增）六基点击预登记：只显示计划列出的六张准入原始 k−1 帧（不叠真值/模型框/评分），由人逐张点目标车；
    服务端核帧字节 sha（浏览器解码字节 = 归档原帧 = 计划记录），每张取最后一次点击（每次点击都进日志），六张齐后写
    `roll-click-script.json`。启动时计划内任一帧 sha 不符即拒绝启动。本类不读真值，计划只含帧号与帧字节 sha。"""

    mode = "register-roll"

    def __init__(self, frames_directory: Path, plan_path: Path, output_directory: Path, log: OpsLog, *, registered_by: str,
                 clock: Callable[[], float] = time.time):
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
        if plan.get("schema_version") != ROLL_PLAN_SCHEMA:
            raise ValueError("roll base plan schema mismatch")
        bases = plan.get("bases") or []
        if len(bases) != ROLL_BASES or len({int(b["base_k"]) for b in bases}) != ROLL_BASES:
            raise ValueError(f"roll base plan must list exactly {ROLL_BASES} distinct bases")
        if not registered_by:
            raise ValueError("register-roll needs --registered-by (the person who clicks)")
        super().__init__(frames_directory, [int(b["frame_id"]) for b in bases], output_directory, log, clock=clock,
                         registered_by=registered_by)
        self.plan_sha256 = sha256_bytes(Path(plan_path).read_bytes())
        self.bases = {int(b["frame_id"]): {"base_k": int(b["base_k"]), "image_sha256": str(b["image_sha256"])} for b in bases}
        for frame_id, entry in self.bases.items():
            if entry["base_k"] != frame_id + 1:
                raise ValueError(f"plan frame {frame_id} is not k−1 of base {entry['base_k']}")
            if sha256_bytes(self._path(frame_id).read_bytes()) != entry["image_sha256"]:
                raise ValueError(f"archived frame {frame_id} sha differs from the plan")
        self.points: dict[int, dict[str, Any]] = {}

    def click(self, body: Mapping[str, Any]) -> dict[str, Any]:
        frame_id, sha, x_px, y_px = body.get("frame_id"), body.get("image_sha256"), body.get("x_px"), body.get("y_px")
        if (isinstance(frame_id, bool) or not isinstance(frame_id, int) or frame_id not in self.bases
                or not _finite(x_px) or not _finite(y_px)):
            return {"ok": False, "message": "点击字段不完整"}
        if not (0 <= float(x_px) < 640 and 0 <= float(y_px) < 480):
            return {"ok": False, "message": "点击点不在画内"}
        data = self._path(frame_id).read_bytes()
        if sha != sha256_bytes(data) or sha != self.bases[frame_id]["image_sha256"]:
            self.log.write("roll_register_refused", reason="sha_mismatch", frame_id=frame_id, image_sha256=sha)
            return {"ok": False, "message": "浏览器解码字节与归档帧/计划 sha 不符"}
        base_k = self.bases[frame_id]["base_k"]
        with self.lock:
            png = self.output / f"roll-click-base{base_k:04d}-frame{frame_id:04d}.png"
            drawn = draw_marker(data, float(x_px), float(y_px), png)
            previous = self.points.get(frame_id)
            sample = {"base_k": base_k, "frame_id": frame_id, "image_sha256": sha, "x_px": float(x_px), "y_px": float(y_px),
                      "display": body.get("display"), "png": str(png) if drawn else None, "at_unix_s": float(self.clock())}
            self.points[frame_id] = sample
            ordered = [self.points[f] for f in sorted(self.points)]
            (self.output / "roll-click-samples.json").write_text(json.dumps(ordered, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            complete = len(self.points) == len(self.bases)
            if complete:
                self._write_roll_script(ordered)
        self.log.write("roll_click", replaces=None if previous is None else {"x_px": previous["x_px"], "y_px": previous["y_px"]}, **sample)
        return {"ok": True, "sample": sample, "registered": len(self.points), "of": len(self.bases), "script_written": complete}

    def _write_roll_script(self, ordered: Sequence[Mapping[str, Any]]) -> None:
        script = {
            "schema_version": ROLL_CLICK_SCHEMA,
            "registered_by": self.registered_by,
            "registered_at_unix_s": float(self.clock()),
            "method": "click_web register-roll（只看准入原始 k−1 帧，不叠真值/模型框/评分，不读真值）",
            "plan_sha256": self.plan_sha256,
            "clicks": [{"base_k": p["base_k"], "frame_id": p["frame_id"], "x_px": p["x_px"], "y_px": p["y_px"],
                        "image_sha256": p["image_sha256"]} for p in ordered],
        }
        (self.output / "roll-click-script.json").write_text(json.dumps(script, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    def state(self) -> dict[str, Any]:
        return {"mode": self.mode, "frames": len(self.frame_ids), "registered": sorted(self.points),
                "missing": sorted(set(self.bases) - set(self.points))}


def draw_marker(jpeg: bytes, x_px: float, y_px: float, destination: Path) -> bool:
    """在帧上于 (x_px, y_px)（自然像素）画红色十字与圆，存 PNG；无 Pillow 时返回 False（只记坐标）。"""
    try:
        from io import BytesIO  # noqa: PLC0415

        from PIL import Image, ImageDraw  # noqa: PLC0415
    except ImportError:
        return False
    with Image.open(BytesIO(jpeg)) as image:
        canvas = image.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    radius = 9
    draw.ellipse((x_px - radius, y_px - radius, x_px + radius, y_px + radius), outline=(255, 0, 0), width=2)
    draw.line((x_px - 16, y_px, x_px + 16, y_px), fill=(255, 0, 0), width=1)
    draw.line((x_px, y_px - 16, x_px, y_px + 16), fill=(255, 0, 0), width=1)
    draw.text((6, 6), f"click ({x_px:.1f}, {y_px:.1f}) px", fill=(255, 255, 0))
    canvas.save(destination)
    return True


PAGE = """<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><title>CAPTURE 点击页</title>
<style>
body{font-family:-apple-system,system-ui,sans-serif;margin:16px;background:#111;color:#eee}
#wrap{width:960px;max-width:100%;position:relative}
#frame{width:100%;height:auto;display:block;cursor:crosshair;border:0;padding:0}
#bar{margin:8px 0;display:flex;gap:12px;align-items:center}
button{font-size:15px;padding:6px 14px}
#status{font-family:ui-monospace,monospace;font-size:13px;white-space:pre-wrap}
</style></head><body>
<div id="bar"><strong>__MODE__</strong><button id="stop">停止会话</button><button id="prev">上一帧</button><button id="next">下一帧</button><span id="info"></span></div>
<div id="wrap"><img id="frame" alt="frame"></div>
<div id="status"></div>
<script>
const NONCE="__NONCE__", MODE="__MODE__";
let shown={frame_id:null,sha:null}, position=0, url=null;
async function sha256hex(buffer){const d=await crypto.subtle.digest("SHA-256",buffer);return [...new Uint8Array(d)].map(b=>b.toString(16).padStart(2,"0")).join("");}
async function load(){
  const r=await fetch("/frame?i="+position,{cache:"no-store"}); if(!r.ok) return;
  const id=parseInt(r.headers.get("X-Frame-Id")); const buf=await r.arrayBuffer();
  const sha=await sha256hex(buf); const blob=new Blob([buf],{type:"image/jpeg"}); const next=URL.createObjectURL(blob);
  const img=document.getElementById("frame"); const probe=new Image(); probe.src=next; await probe.decode();
  img.src=next; if(url) URL.revokeObjectURL(url); url=next; shown={frame_id:id,sha:sha};
  document.getElementById("info").textContent="frame "+id+"  sha "+sha.slice(0,12)+"…  natural "+probe.naturalWidth+"×"+probe.naturalHeight;
}
document.getElementById("frame").addEventListener("click",async(e)=>{
  const img=e.currentTarget; const rect=img.getBoundingClientRect();
  const x=(e.clientX-rect.left)*img.naturalWidth/rect.width, y=(e.clientY-rect.top)*img.naturalHeight/rect.height;
  const body={frame_id:shown.frame_id,image_sha256:shown.sha,x_px:x,y_px:y,
    display:{client_w:rect.width,client_h:rect.height,natural_w:img.naturalWidth,natural_h:img.naturalHeight}};
  const r=await fetch("/api/click",{method:"POST",headers:{"Content-Type":"application/json","X-Click-Nonce":NONCE},body:JSON.stringify(body)});
  document.getElementById("status").textContent=JSON.stringify(await r.json(),null,1);
});
document.getElementById("stop").addEventListener("click",async()=>{
  const r=await fetch("/api/stop",{method:"POST",headers:{"Content-Type":"application/json","X-Click-Nonce":NONCE},body:"{}"});
  document.getElementById("status").textContent=JSON.stringify(await r.json(),null,1);
});
document.getElementById("prev").addEventListener("click",()=>{position=Math.max(0,position-1);load();});
document.getElementById("next").addEventListener("click",()=>{position+=1;load();});
if(MODE==="live"){document.getElementById("prev").hidden=true;document.getElementById("next").hidden=true;setInterval(load,200);}else{document.getElementById("stop").hidden=true;}
load();
</script></body></html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "capture-click/1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    @property
    def app(self) -> Any:
        return self.server.app  # type: ignore[attr-defined]

    def _host_ok(self) -> bool:
        port = self.server.server_address[1]
        return self.headers.get("Host") in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def _send(self, code: int, body: bytes, content_type: str, extra: Mapping[str, str] | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' blob:; script-src 'unsafe-inline'; style-src 'unsafe-inline'")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: Mapping[str, Any]) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        if not self._host_ok():
            return self._send(403, b"forbidden", "text/plain")
        path, _, query = self.path.partition("?")
        params = dict(part.partition("=")[::2] for part in query.split("&") if part)
        if path == "/":
            page = PAGE.replace("__NONCE__", self.app.nonce).replace("__MODE__", self.app.mode)
            return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/api/state":
            return self._json(200, self.app.state())
        if path == "/frame":
            frame = self.app.frame(params)
            if frame is None:
                return self._send(404, b"not found", "text/plain")
            data, frame_id = frame
            return self._send(200, data, "image/jpeg", {"X-Frame-Id": str(frame_id)})
        return self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        port = self.server.server_address[1]
        origin = self.headers.get("Origin")
        if (
            not self._host_ok()
            or self.path not in {"/api/click", "/api/stop"}
            or self.headers.get("X-Click-Nonce") != self.app.nonce
            or (origin is not None and origin not in {f"http://127.0.0.1:{port}", f"http://localhost:{port}"})
        ):
            self.app.log.write("refused", reason="forbidden_request", path=self.path, origin=origin,
                               host=self.headers.get("Host"), nonce_ok=self.headers.get("X-Click-Nonce") == self.app.nonce)
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
        if self.path == "/api/stop":
            return self._json(200, self.app.stop(body))
        return self._json(200, self.app.click(body))


def build_server(app: Any, port: int = DEFAULT_PORT) -> http.server.ThreadingHTTPServer:
    server = http.server.ThreadingHTTPServer((HOST, port), Handler)
    server.app = app  # type: ignore[attr-defined]
    return server


def build_live_app(runtime: Path, session_id: str, log_path: Path, *, python: str = sys.executable) -> ClickApp:
    log = OpsLog(log_path)
    submitter = Submitter(InProcessSend(), ClickArgv(python, REPO_ROOT, runtime), log)
    return ClickApp(runtime, session_id, submitter, log)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-CAPTURE-001 本机点击页（只监听 127.0.0.1）")
    sub = parser.add_subparsers(dest="mode", required=True)
    live = sub.add_parser("live", help="捕获模式会话的点击/停止入口")
    live.add_argument("--runtime", type=Path, required=True)
    live.add_argument("--session-id", required=True)
    live.add_argument("--log", type=Path, required=True, help="点击页原流（JSONL）")
    live.add_argument("--port", type=int, default=DEFAULT_PORT)
    fidelity = sub.add_parser("fidelity", help="AC-27 保真：归档准入帧上点击并另存标记样帧（不提交）")
    fidelity.add_argument("--frames", type=Path, required=True)
    fidelity.add_argument("--frame-ids", type=int, nargs="+", required=True)
    fidelity.add_argument("--output", type=Path, required=True)
    fidelity.add_argument("--port", type=int, default=DEFAULT_PORT)
    fidelity.add_argument("--register-labels", nargs="*", default=[], help="AC-17 预登记：按点击顺序的标签（如 static_car red_car）")
    fidelity.add_argument("--registered-by", default=None)
    register = sub.add_parser("register-roll", help="AC-28 六基点击预登记：只显示计划内六张原始 k−1 帧，人逐张点目标车")
    register.add_argument("--frames", type=Path, required=True)
    register.add_argument("--plan", type=Path, required=True, help="`replay.py prepare-roll` 写出的计划")
    register.add_argument("--output", type=Path, required=True)
    register.add_argument("--registered-by", required=True)
    register.add_argument("--port", type=int, default=DEFAULT_PORT)
    arguments = parser.parse_args(argv)
    if arguments.mode == "live":
        app: Any = build_live_app(arguments.runtime, arguments.session_id, arguments.log)
    elif arguments.mode == "register-roll":
        app = RollRegisterApp(arguments.frames, arguments.plan, arguments.output, OpsLog(arguments.output / CLICK_LOG),
                              registered_by=arguments.registered_by)
    else:
        app = FidelityApp(arguments.frames, arguments.frame_ids, arguments.output, OpsLog(arguments.output / CLICK_LOG),
                          register_labels=arguments.register_labels, registered_by=arguments.registered_by)
    server = build_server(app, arguments.port)
    print(f"http://{HOST}:{server.server_address[1]}/  mode={app.mode}", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
