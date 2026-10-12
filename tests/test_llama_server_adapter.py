"""P1-ENG-LOOP-002 AC-7：`LlamaServerAdapter` 与 `language_serve --backend llama-server`。

全部只在 127.0.0.1 回环上跑：一个线程内的假 OpenAI 兼容服务，以及测试在临时目录写出的假
`llama-bin`（`--version` 打印 `version: 11381 (deadbeef)`；否则按 `--port` 起假 `/health` 与
`/v1/chat/completions`）。不加载模型、不下载、不写仓库 `runtime/`；子进程一律有超时并在
`addCleanup` 里 kill。

本文件不从 `tests.*` 导入夹具（`.venv-yoloe` 的 site-packages 有同名 `tests` 包）。
"""

from __future__ import annotations

import ast
import base64
import contextlib
import hashlib
import io
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from pathlib import Path
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from controller.language_bridge import validate_llama_identity  # noqa: E402
from controller.language_selector import (  # noqa: E402
    HttpAdapter,
    RawSelection,
    SelectorError,
    _multipart,
    _prompt_identity,
    interpret,
)
from tools import language_serve  # noqa: E402
from tools.eng_loop2 import deploy_digest, llama_adapter  # noqa: E402
from tools.eng_sft import prompt_v2  # noqa: E402

SCHEMA = deploy_digest.load_schema(REPO_ROOT)
HEX_W = "1" * 64
HEX_M = "2" * 64
HEX_B = "3" * 64
UNIQUE = '{"status": "unique", "bbox_2d": [100, 200, 300, 400]}'
AMBIGUOUS = (
    '{"status": "ambiguous", "candidates": [{"bbox_2d": [10, 20, 30, 40]}, '
    '{"bbox_2d": [500, 500, 600, 700]}]}'
)
NONE = '{"status": "none"}'
SUBPROCESS_TIMEOUT_S = 30.0


def _completion(content: str, finish_reason: str | None = "stop", completion_tokens: int = 17) -> bytes:
    return json.dumps(
        {
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": finish_reason,
                }
            ],
            "usage": {"completion_tokens": completion_tokens, "prompt_tokens": 900},
        }
    ).encode("utf-8")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _port_open(port: int) -> bool:
    try:
        socket.create_connection(("127.0.0.1", port), timeout=1.0).close()
    except OSError:
        return False
    return True


def _image_bytes() -> bytes:
    # 含全部 256 个字节值：base64 原样往返才算「图像原样字节」。
    return b"\xff\xd8\xff\xe0" + bytes(range(256)) * 3 + b"\xff\xd9"


# --- 线程内假 OpenAI 兼容服务 -------------------------------------------------


class _FakeOpenAI:
    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.reply: tuple[int, bytes] = (200, _completion(NONE))
        self.delay_s = 0.0
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):  # noqa: A002
                return

            def _send(self, code: int, payload: bytes) -> None:
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def do_GET(self):  # noqa: N802
                self._send(200 if self.path == "/health" else 404, b'{"status":"ok"}')

            def do_POST(self):  # noqa: N802
                body = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
                fake.requests.append(
                    {"path": self.path, "content_type": self.headers.get("Content-Type"), "body": body}
                )
                if fake.delay_s:
                    time.sleep(fake.delay_s)
                try:
                    self._send(*fake.reply)
                except OSError:
                    pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)


class _AdapterCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fake = _FakeOpenAI()
        self.addCleanup(self.fake.close)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)
        self.image = self.tmp / "frame.jpg"
        self.image.write_bytes(_image_bytes())

    def _adapter(self, base_url: str | None = None, **overrides) -> llama_adapter.LlamaServerAdapter:
        options = dict(
            schema=SCHEMA,
            weights_sha256=HEX_W,
            mmproj_sha256=HEX_M,
            runtime_binary_sha256=HEX_B,
            runtime_build="b11381",
            quantization="Q4_K_M",
            request_timeout_s=5.0,
        )
        options.update(overrides)
        return llama_adapter.LlamaServerAdapter(base_url or self.fake.base_url, **options)


# --- AC-7 (1)：请求体 --------------------------------------------------------


class RequestBodyTests(_AdapterCase):
    def test_request_body_prompt_v2_verbatim_schema_decode_and_original_image_base64(self) -> None:
        self.fake.reply = (200, _completion(NONE))
        adapter = self._adapter()
        for g4, surface in ((False, "the red car"), (True, "the suv to the viewer's right of the bus")):
            raw = adapter.predict_one("q", self.image, surface, g4)
            sent = self.fake.requests[-1]
            self.assertEqual(sent["path"], "/v1/chat/completions")
            self.assertEqual(sent["content_type"], "application/json")
            body = json.loads(sent["body"])
            self.assertEqual(
                set(body), {"messages", "response_format", "temperature", "max_tokens", "cache_prompt"}
            )
            prompt = prompt_v2.build_prompt("", surface, g4, "unity-v2")
            image_part, text_part = body["messages"][0]["content"]
            self.assertEqual(body["messages"][0]["role"], "user")
            self.assertEqual(text_part, {"type": "text", "text": prompt["text"]})
            self.assertEqual(raw.prompt_sha256, prompt["prompt_sha256"])
            self.assertEqual(image_part["type"], "image_url")
            prefix = "data:image/jpeg;base64,"
            url = image_part["image_url"]["url"]
            self.assertTrue(url.startswith(prefix))
            self.assertEqual(base64.b64decode(url[len(prefix):], validate=True), _image_bytes())
            self.assertEqual(body["response_format"], deploy_digest.response_format_object(SCHEMA))
            self.assertEqual(body["response_format"]["json_schema"]["schema"], SCHEMA)
            self.assertIs(type(body["temperature"]), int)
            self.assertEqual(body["temperature"], 0)
            self.assertEqual(body["max_tokens"], 160)
            self.assertIs(body["cache_prompt"], False)
            self.assertEqual(body, llama_adapter.build_request_body(_image_bytes(), surface, g4, SCHEMA))

    def test_decode_config_is_the_deploy_digest_object(self) -> None:
        self.assertIs(llama_adapter.DECODE_CONFIG, deploy_digest.DECODE_CONFIG)

    def test_identity_carries_six_llama_keys_hashed_from_what_is_sent(self) -> None:
        adapter = self._adapter()
        identity = adapter.identity
        self.assertTrue(validate_llama_identity(identity))
        self.assertEqual(identity["backend"], "http")
        self.assertEqual(identity["model_form"], "c2-merged")
        self.assertIsNone(identity["base_repo_revision"])
        self.assertEqual(identity["device"], "cuda")
        for key, value in _prompt_identity(False).items():
            self.assertEqual(identity[key], value)
        adapter.predict_one("q", self.image, "the red car", False)
        sent_format = json.loads(self.fake.requests[-1]["body"])["response_format"]
        self.assertEqual(identity["response_format_sha256"], deploy_digest.canonical_sha256(sent_format))
        self.assertEqual(identity["response_format_sha256"], deploy_digest.response_format_sha256(SCHEMA))
        self.assertEqual(identity["decode_config_sha256"], deploy_digest.decode_config_sha256())

    def test_invalid_identity_or_non_loopback_url_is_load_failure(self) -> None:
        for overrides in (
            {"quantization": "Q8_0"},
            {"runtime_build": "11381"},
            {"mmproj_sha256": "XYZ"},
            {"weights_sha256": ""},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(SelectorError) as caught:
                self._adapter(**overrides)
            self.assertEqual(caught.exception.reason, "load_failure")
        for url in ("http://localhost:8080", "http://10.0.0.2:8080", "https://127.0.0.1:8080", "http://127.0.0.1"):
            with self.subTest(url=url), self.assertRaises(SelectorError) as caught:
                self._adapter(url)
            self.assertEqual(caught.exception.reason, "load_failure")


# --- AC-7 (2)：响应 → parse.py 与失败映射 -------------------------------------


class ResponseMappingTests(_AdapterCase):
    def _predict(self, reply: tuple[int, bytes], **overrides) -> RawSelection:
        self.fake.reply = reply
        return self._adapter(**overrides).predict_one("q", self.image, "the red car", False)

    def test_three_states_parse_and_pass_through_finish_reason_raw_text_gen_tokens(self) -> None:
        for content, status, count in ((UNIQUE, "unique", 1), (AMBIGUOUS, "ambiguous", 2), (NONE, "none", 0)):
            with self.subTest(status=status):
                raw = self._predict((200, _completion(content, "stop", 23)))
                self.assertEqual(raw.raw_output, content)
                self.assertEqual(raw.finish_reason, "stop")
                self.assertEqual(raw.gen_tokens, 23)
                self.assertEqual(raw.model_id, HEX_W)
                self.assertIsInstance(raw.latency_ms, float)
                selection = interpret(raw)
                self.assertEqual(selection.status, status)
                self.assertIsNone(selection.parse_error)
                self.assertEqual(len(selection.candidates), count)
        self.assertEqual(os.listdir(self.tmp), ["frame.jpg"])  # 适配器不落盘任何文件

    def test_schema_mismatch_is_returned_and_parses_to_schema_error(self) -> None:
        content = '{"status": "unique"}'
        raw = self._predict((200, _completion(content)))
        self.assertEqual(raw.raw_output, content)
        selection = interpret(raw)
        self.assertEqual(selection.status, "parse_failed")
        self.assertEqual(selection.parse_error, "SCHEMA_ERROR")

    def test_finish_reason_length_is_returned_and_parses_to_truncated(self) -> None:
        content = '{"status": "ambiguous", "candidates": [{"bbox_2d": [1, 2'
        raw = self._predict((200, _completion(content, "length", 160)))
        self.assertEqual((raw.raw_output, raw.finish_reason, raw.gen_tokens), (content, "length", 160))
        selection = interpret(raw)
        self.assertEqual(selection.status, "parse_failed")
        self.assertEqual(selection.parse_error, "TRUNCATED")

    def test_non_json_body_is_worker_died(self) -> None:
        with self.assertRaises(SelectorError) as caught:
            self._predict((200, b"<html>oops</html>"))
        self.assertEqual((caught.exception.reason, caught.exception.status), ("worker_died", "backend_error"))
        self.assertIn("HTTP 200", caught.exception.detail)
        self.assertIn("non-JSON", caught.exception.detail)

    def test_missing_choices_is_worker_died(self) -> None:
        for payload in (b'{"error": "x"}', b'{"choices": []}', b'{"choices": [{"message": {}}]}', b"[1]"):
            with self.subTest(payload=payload), self.assertRaises(SelectorError) as caught:
                self._predict((200, payload))
            self.assertEqual(caught.exception.reason, "worker_died")

    def test_http_error_status_is_worker_died_with_code(self) -> None:
        # S-RECEIPT 前置：`response_format` 被服务拒绝（4xx）也照实报告，不吞。
        with self.assertRaises(SelectorError) as caught:
            self._predict((400, b'{"error": {"message": "response_format unsupported"}}'))
        self.assertEqual(caught.exception.reason, "worker_died")
        self.assertIn("HTTP 400", caught.exception.detail)
        self.assertIn("response_format unsupported", caught.exception.detail)

    def test_request_timeout_is_timeout(self) -> None:
        self.fake.delay_s = 2.0
        started = time.monotonic()
        with self.assertRaises(SelectorError) as caught:
            self._predict((200, _completion(NONE)), request_timeout_s=0.3)
        self.assertEqual(caught.exception.reason, "timeout")
        self.assertLess(time.monotonic() - started, 1.8)

    def test_connection_refused_when_llama_server_absent_is_worker_died(self) -> None:
        adapter = self._adapter(f"http://127.0.0.1:{_free_port()}")
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("q", self.image, "the red car", False)
        self.assertEqual(caught.exception.reason, "worker_died")
        self.assertIn("unreachable", caught.exception.detail)

    def test_single_flight_runtime_keeps_every_row_and_deletes_scratch_images(self) -> None:
        cases = (
            ((200, _completion(UNIQUE)), "done", None),
            ((200, _completion('{"status": "unique"}')), "done", None),
            ((200, _completion("{", "length")), "done", None),
            ((200, b"not json"), "failed", "worker_died"),
            ((502, b"bad gateway"), "failed", "worker_died"),
        )
        scratch = self.tmp / "scratch"
        runtime = language_serve.SingleFlightRuntime(
            self._adapter(), scratch_directory=scratch, delete_images_after_run=True
        )
        for index, (reply, state, error) in enumerate(cases):
            with self.subTest(index=index):
                self.fake.reply = reply
                query_id = f"q{index}"
                self.assertTrue(runtime.submit(query_id, _image_bytes(), "the red car", False)["accepted"])
                runtime.join(10)
                result = runtime.result(query_id)
                self.assertEqual(result["state"], state)
                if error is not None:
                    self.assertEqual(result["error"], error)
                else:
                    self.assertEqual(result["record"]["raw_output"], json.loads(reply[1])["choices"][0]["message"]["content"])
                    self.assertIn("finish_reason", result["record"])
                self.assertEqual(list(scratch.iterdir()), [])

    def test_local_hf_default_keeps_scratch_images_and_reply_fields(self) -> None:
        scratch = self.tmp / "scratch"
        runtime = language_serve.SingleFlightRuntime(self._adapter(), scratch_directory=scratch)
        runtime.submit("q1", _image_bytes(), "the red car", False)
        runtime.join(10)
        self.assertEqual([path.name for path in scratch.iterdir()], ["q1.jpg"])
        server = language_serve.build_server(runtime, port=0)
        self.addCleanup(server.server_close)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), thread.join(5)))
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/status", timeout=5) as response:
            document = json.loads(response.read())
        self.assertEqual(set(document), {"state", "query_id", "model_identity"})


# --- 假 llama-bin 与 language_serve 子进程夹具 ---------------------------------

_FAKE_LLAMA = r'''#!{python}
"""假 llama-server（P1-ENG-LOOP-002 AC-7 测试夹具；仅标准库）。"""
import json, os, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer

CONFIG = {config!r}
STATE = {state!r}


def config():
    try:
        with open(CONFIG, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return {{}}


if "--version" in sys.argv[1:]:
    time.sleep(float(config().get("version_sleep_s", 0)))
    sys.stderr.write(config().get("version_text", "version: 11381 (deadbeef)\nbuilt with fake cc for test\n"))
    sys.exit(int(config().get("version_exit", 0)))

os.makedirs(STATE, exist_ok=True)
with open(os.path.join(STATE, "started.jsonl"), "a", encoding="utf-8") as handle:
    handle.write(json.dumps({{"pid": os.getpid(), "argv": sys.argv[1:]}}) + "\n")
arguments = sys.argv[1:]
host = arguments[arguments.index("--host") + 1]
port = int(arguments[arguments.index("--port") + 1])
if host != "127.0.0.1" or "-m" not in arguments or "--mmproj" not in arguments:
    sys.exit(9)
mode = config().get("mode", "serve")
if mode == "exit":
    sys.exit(7)
if mode == "no_listen":
    time.sleep(120)
    sys.exit(0)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def _send(self, code, payload):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            if mode == "slow_health":
                time.sleep(3.0)
            self._send(503 if mode == "never_ready" else 200, b'{{"status":"ok"}}')
        else:
            self._send(404, b"{{}}")

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
        with open(os.path.join(STATE, "requests.jsonl"), "ab") as handle:
            handle.write(body + b"\n")
        settings = config()
        payload = json.dumps({{
            "choices": [{{"index": 0, "message": {{"role": "assistant", "content": settings.get("content", '{{"status": "none"}}')}},
                         "finish_reason": settings.get("finish_reason", "stop")}}],
            "usage": {{"completion_tokens": 9}},
        }}).encode("utf-8")
        self._send(200, payload)


HTTPServer((host, port), Handler).serve_forever()
'''


def _write_fake_llama(bin_path: Path, config_path: Path, state_dir: Path) -> Path:
    bin_path.parent.mkdir(parents=True, exist_ok=True)
    bin_path.write_text(
        _FAKE_LLAMA.format(python=sys.executable, config=str(config_path), state=str(state_dir)),
        encoding="utf-8",
    )
    bin_path.chmod(0o755)
    return bin_path


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _copy_closed_set(destination: Path) -> list[str]:
    paths = deploy_digest.manifest_paths(REPO_ROOT)
    for relative in paths:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / relative, target)
    return paths


class _ServeFixture(unittest.TestCase):
    """临时目录：`root`（源码根，只放清单文件 + 假 bin + 假 GGUF）与 `work`（日志/配置/scratch）。"""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)
        self.root = self.tmp / "root"
        self.work = self.tmp / "work"
        self.work.mkdir()
        self.config_path = self.work / "fake_llama_config.json"
        self.state = self.work / "fake_llama_state"
        self.llama_bin = _write_fake_llama(self.root / "bin" / "llama-server", self.config_path, self.state)
        self.weights = self.root / "models" / "c2-q4_k_m.gguf"
        self.mmproj = self.root / "models" / "c2-mmproj.gguf"
        self.weights.parent.mkdir(parents=True, exist_ok=True)
        self.weights.write_bytes(b"GGUF\x03fake c2 q4 weights")
        self.mmproj.write_bytes(b"GGUF\x03fake mmproj")
        self.access_log = self.work / "logs" / "access.jsonl"
        self.http_ledger = self.work / "logs" / "http-ledger.jsonl"
        self.scratch = self.work / "scratch"
        self.llama_port = _free_port()
        self.addCleanup(self._kill_fake_children)

    def _kill_fake_children(self) -> None:
        started = self.state / "started.jsonl"
        if not started.exists():
            return
        for line in started.read_text(encoding="utf-8").splitlines():
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.kill(json.loads(line)["pid"], signal.SIGKILL)

    def _fake_started(self) -> bool:
        return (self.state / "started.jsonl").exists()

    def _assets(self, **overrides) -> Path:
        document = {
            "weights_sha256": _sha(self.weights),
            "mmproj_sha256": _sha(self.mmproj),
            "runtime_binary_sha256": _sha(self.llama_bin),
            "runtime_build": "b11381",
            "quantization": "Q4_K_M",
        }
        for key, value in overrides.items():
            if value is None:
                document.pop(key, None)
            else:
                document[key] = value
        path = self.work / "assets.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def _llama_arguments(
        self, assets: Path, *, port: str = "0", extra: tuple[str, ...] = (), reserve: int = 5
    ) -> list[str]:
        return [
            "--backend", "llama-server",
            "--port", port,
            "--llama-bin", str(self.llama_bin),
            "--weights", str(self.weights),
            "--mmproj", str(self.mmproj),
            "--llama-port", str(self.llama_port),
            "--expect-assets", str(assets),
            "--access-log", str(self.access_log),
            "--http-ledger", str(self.http_ledger),
            "--non-inference-reserve", str(reserve),
            "--scratch", str(self.scratch),
            *extra,
        ]

    def _start_serve(self, script: Path, arguments: list[str], *, isolated: bool) -> tuple[subprocess.Popen, int]:
        stdout = (self.work / "serve.out").open("wb")
        self.addCleanup(stdout.close)
        command = [sys.executable, *(["-I", "-S"] if isolated else []), str(script), *arguments]
        process = subprocess.Popen(
            command, stdout=stdout, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd=self.work
        )

        def kill() -> None:
            if process.poll() is None:
                process.kill()
                process.wait(10)

        self.addCleanup(kill)
        deadline = time.monotonic() + SUBPROCESS_TIMEOUT_S
        while time.monotonic() < deadline:
            text = (self.work / "serve.out").read_text(encoding="utf-8", errors="replace")
            match = re.search(r"listening on http://127\.0\.0\.1:(\d+)", text)
            if match:
                return process, int(match.group(1))
            if process.poll() is not None:
                self.fail(f"language_serve exited early ({process.returncode}): {text}")
            time.sleep(0.05)
        self.fail("language_serve did not start listening in time")

    def _main_in_process(self, arguments: list[str]) -> tuple[int, str]:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = language_serve.main(arguments)
        return code, stderr.getvalue()


def _recording_opener(log: list[dict]):
    no_proxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def opener(request: urllib.request.Request, timeout: float) -> bytes:
        try:
            with no_proxy.open(request, timeout=timeout) as response:
                status, payload = response.status, response.read()
        except urllib.error.HTTPError as error:
            with error:
                status, payload = error.code, error.read()
        split = urllib.parse.urlsplit(request.full_url)
        log.append(
            {
                "method": request.get_method(),
                # 请求目标原样（含 AC-7 修订 3 的 `?wait_s=`），与服务端访问日志 `path` 同口径。
                "path": split.path + (f"?{split.query}" if split.query else ""),
                "status": status,
                "request_body_bytes": len(request.data or b""),
                "response_body_bytes": len(payload),
            }
        )
        return payload

    return opener


ACCESS_LOG_KEYS = {
    "method", "path", "status", "request_head_bytes", "request_body_bytes", "request_declared_body_bytes",
    "request_body_complete", "response_head_bytes", "response_body_bytes", "error", "started_unix_s",
    "finished_unix_s",
}


class _IdleAdapter:
    """`SingleFlightRuntime` 的最小适配器：只给身份；本组用例不提交推理。"""

    identity = {"backend": "http", "model_form": "c2-merged"}

    def predict_one(self, query_id, image_path, surface, g4):  # pragma: no cover - 不会被调用
        raise AssertionError("no inference expected")


class AccessLogEveryRequestTests(unittest.TestCase):
    """C1-AC7（IR-11 不接受漏记豁免）：坏请求行、未支持方法、未知 POST 路径、Content-Length
    不可解析、短正文与处理异常的请求，访问日志都逐请求记一行，字节为线路上实际读写的字节。"""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)
        self.log = self.tmp / "access.jsonl"
        self.runtime = language_serve.SingleFlightRuntime(
            _IdleAdapter(), scratch_directory=self.tmp / "scratch", delete_images_after_run=True
        )
        self.server = language_serve.build_server(self.runtime, port=0, access_log=self.log)
        self.addCleanup(self.server.server_close)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (self.server.shutdown(), thread.join(5)))

    def _exchange(self, head: bytes, body: bytes = b"", *, shut_write: bool = False) -> tuple[bytes, bytes]:
        """原始套接字发一次请求，返回（响应头含空行, 响应体）。"""
        with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=10) as sock:
            sock.sendall(head + body)
            if shut_write:
                sock.shutdown(socket.SHUT_WR)
            chunks = []
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
        data = b"".join(chunks)
        if not data.startswith(b"HTTP/"):
            return b"", data  # 请求行不可解析时 `BaseHTTPRequestHandler` 按 HTTP/0.9 只回正文、无头
        split = data.find(b"\r\n\r\n")
        self.assertGreaterEqual(split, 0, data)
        return data[: split + 4], data[split + 4 :]

    def _lines(self, expected: int) -> list[dict]:
        deadline = time.monotonic() + 5.0
        while True:
            lines = self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []
            if len(lines) >= expected or time.monotonic() > deadline:
                return [json.loads(line) for line in lines]
            time.sleep(0.02)

    def _assert_line(self, line: dict, head: bytes, body: bytes, response: tuple[bytes, bytes], **expected) -> None:
        self.assertEqual(set(line), ACCESS_LOG_KEYS)
        self.assertEqual(line["request_head_bytes"], len(head))
        self.assertEqual(line["request_body_bytes"], len(body))
        self.assertEqual(line["response_head_bytes"], len(response[0]))
        self.assertEqual(line["response_body_bytes"], len(response[1]))
        self.assertLessEqual(line["started_unix_s"], line["finished_unix_s"])
        for key, value in expected.items():
            self.assertEqual(line[key], value, key)

    def test_bad_request_line_is_logged_with_actual_bytes(self) -> None:
        for request_line, code in ((b"GARBAGE\r\n", 400), (b"GET /status HTTP/2.0\r\n", 505), (b"A B C\r\n", 400)):
            with self.subTest(request_line=request_line):
                self.log.unlink(missing_ok=True)
                response = self._exchange(request_line + b"\r\n")
                (line,) = self._lines(1)
                # 请求行不可解析：头部以服务端实际读到的字节计（读到第一行即拒），无可界定正文；
                # 此时按 HTTP/0.9 回包（无响应头），正文字节照实计。
                self.assertEqual(line["status"], code)
                self.assertEqual(line["request_head_bytes"], len(request_line))
                self.assertEqual(line["request_body_bytes"], 0)
                self.assertEqual((line["request_body_complete"], line["request_declared_body_bytes"]), (False, None))
                self.assertEqual(line["response_head_bytes"], len(response[0]))
                self.assertEqual(line["response_body_bytes"], len(response[1]))
                self.assertGreater(line["response_body_bytes"], 0)

    def test_too_many_headers_is_logged_with_response_head(self) -> None:
        head = b"GET /status HTTP/1.0\r\n" + b"".join(b"X-H%d: v\r\n" % i for i in range(120)) + b"\r\n"
        response = self._exchange(head)
        (line,) = self._lines(1)
        self.assertEqual(line["status"], 431)
        self.assertGreater(line["response_head_bytes"], 0)
        self.assertEqual(line["response_head_bytes"], len(response[0]))
        self.assertEqual(line["response_body_bytes"], len(response[1]))
        self.assertLessEqual(line["request_head_bytes"], len(head))
        self.assertEqual(line["request_body_bytes"], 0)
        self.assertFalse(line["request_body_complete"])

    def test_unsupported_method_body_is_drained_and_counted(self) -> None:
        body = b"x" * 3000
        head = b"PUT /query HTTP/1.0\r\nContent-Length: 3000\r\n\r\n"
        response = self._exchange(head, body)
        (line,) = self._lines(1)
        self._assert_line(line, head, body, response, method="PUT", path="/query", status=501,
                          request_body_complete=True, request_declared_body_bytes=3000, error=None)

    def test_unknown_post_path_counts_the_body(self) -> None:
        body = b"y" * 1234
        head = b"POST /nope HTTP/1.0\r\nContent-Length: 1234\r\n\r\n"
        response = self._exchange(head, body)
        (line,) = self._lines(1)
        self._assert_line(line, head, body, response, method="POST", path="/nope", status=404,
                          request_body_complete=True)

    def test_unparseable_content_length_is_logged_incomplete(self) -> None:
        head = b"POST /query HTTP/1.0\r\nContent-Length: abc\r\n\r\n"
        response = self._exchange(head, b"", shut_write=True)
        (line,) = self._lines(1)
        self._assert_line(line, head, b"", response, method="POST", status=400,
                          request_body_complete=False, request_declared_body_bytes=None)

    def test_short_body_counts_actual_not_declared_bytes(self) -> None:
        body = b"z" * 40
        head = b"POST /query HTTP/1.0\r\nContent-Type: multipart/form-data; boundary=b\r\nContent-Length: 100\r\n\r\n"
        response = self._exchange(head, body, shut_write=True)
        (line,) = self._lines(1)
        self._assert_line(line, head, body, response, status=400, request_body_complete=False,
                          request_declared_body_bytes=100)

    def test_malformed_multipart_and_get_status_and_unknown_get(self) -> None:
        body = b"--b\r\nnot a part\r\n--b--\r\n"
        head = (b"POST /query HTTP/1.0\r\nContent-Type: multipart/form-data; boundary=b\r\nContent-Length: "
                + str(len(body)).encode() + b"\r\n\r\n")
        first = self._exchange(head, body)
        status_head = b"GET /status HTTP/1.0\r\n\r\n"
        second = self._exchange(status_head)
        unknown_head = b"GET /elsewhere HTTP/1.0\r\n\r\n"
        third = self._exchange(unknown_head)
        lines = self._lines(3)
        self.assertEqual([line["status"] for line in lines], [400, 200, 404])
        self._assert_line(lines[0], head, body, first, request_body_complete=True)
        self._assert_line(lines[1], status_head, b"", second, request_body_complete=True, request_declared_body_bytes=0)
        self._assert_line(lines[2], unknown_head, b"", third, path="/elsewhere")

    def test_handler_exception_is_logged_with_error(self) -> None:
        def explode() -> dict:
            raise RuntimeError("status exploded")

        self.runtime.status = explode  # type: ignore[method-assign]
        head = b"GET /status HTTP/1.0\r\n\r\n"
        with contextlib.redirect_stderr(io.StringIO()):
            with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=10) as sock:
                sock.sendall(head)
                received = b""
                while True:
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    received += chunk
            (line,) = self._lines(1)
        self.assertEqual(received, b"")
        self.assertEqual((line["status"], line["response_head_bytes"], line["response_body_bytes"]), (None, 0, 0))
        self.assertEqual(line["request_head_bytes"], len(head))
        self.assertIn("RuntimeError: status exploded", line["error"])

    def test_r1_1_response_body_partial_send_counts_bytes_handed_to_socket(self) -> None:
        """R1-1（`R1@K1K2K3K4` §3 闭合绑定，写侧）：生产 `build_server` + 真实回环套接字，只把底层
        套接字换成「响应头整写、此后只再接受 10 B 即抛 `BrokenPipeError`」的透传代理；访问日志
        该行 `response_body_bytes` 必须等于实际交给套接字的 10 B（修前 `sendall` 抛错整次记 0）。"""
        accepted_after_head = 10

        class _BreakAfterHeadSocket:
            """透传代理：第 1 次写入（响应头）原样发出；之后累计只真实发送 10 B，再写即 `BrokenPipeError`。"""

            def __init__(self, real: socket.socket):
                self._real = real
                self._writes = 0
                self._budget = accepted_after_head

            def _take(self, data) -> bytes:
                view = memoryview(data).cast("B")
                self._writes += 1
                if self._writes == 1:
                    return bytes(view)
                if self._budget <= 0:
                    raise BrokenPipeError(32, "Broken pipe (injected after 10 B)")
                part = bytes(view[: self._budget])
                self._budget -= len(part)
                return part

            def send(self, data, *flags) -> int:
                part = self._take(data)
                return self._real.send(part, *flags)

            def sendall(self, data, *flags) -> None:
                total = len(memoryview(data).cast("B"))
                part = self._take(data)
                self._real.sendall(part, *flags)
                if len(part) < total:
                    raise BrokenPipeError(32, "Broken pipe (injected after 10 B)")

            def __getattr__(self, name: str):
                return getattr(self._real, name)

        bound = self.server.RequestHandlerClass

        class _ProxiedHandler(bound):  # type: ignore[misc, valid-type]
            def setup(self) -> None:
                self.request = _BreakAfterHeadSocket(self.request)
                super().setup()

        self.server.RequestHandlerClass = _ProxiedHandler
        head = b"GET /status HTTP/1.0\r\n\r\n"
        with contextlib.redirect_stderr(io.StringIO()):
            response = self._exchange(head)
            (line,) = self._lines(1)
        self.assertEqual(len(response[1]), accepted_after_head, response)
        self.assertEqual(line["status"], 200)
        self.assertEqual(line["response_head_bytes"], len(response[0]))
        self.assertEqual(line["response_body_bytes"], accepted_after_head)
        self.assertIsNotNone(line["error"])
        self.assertIn("BrokenPipeError", line["error"])

    def test_r1_1_drain_timeout_counts_partial_body_actually_received(self) -> None:
        """R1-1（`R1@K1K2K3K4` §3 闭合绑定，读侧）：客户端只发声明正文的一部分且保持连接不关，
        服务端回包后 drain 超时；`request_body_bytes` 必须等于客户端实际已发送的字节、
        `request_body_complete` 为 false、`error` 记超时（修前 `BufferedReader` 超时丢弃部分块记 0）。"""
        sent_body = b"q" * 30
        head = b"GET /status HTTP/1.0\r\nContent-Length: 100\r\n\r\n"
        original = language_serve.ACCESS_DRAIN_TIMEOUT_S
        language_serve.ACCESS_DRAIN_TIMEOUT_S = 0.5
        self.addCleanup(setattr, language_serve, "ACCESS_DRAIN_TIMEOUT_S", original)
        for split in (False, True):
            with self.subTest(body_in_separate_segment=split):
                self.log.unlink(missing_ok=True)
                with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=10) as sock:
                    if split:
                        sock.sendall(head)
                        time.sleep(0.05)
                        sock.sendall(sent_body)
                    else:
                        sock.sendall(head + sent_body)
                    # 不关写端：服务端只能等 drain 超时
                    (line,) = self._lines(1)
                self.assertEqual(line["status"], 200)
                self.assertEqual(line["request_head_bytes"], len(head))
                self.assertEqual(line["request_declared_body_bytes"], 100)
                self.assertEqual(line["request_body_bytes"], len(sent_body))
                self.assertFalse(line["request_body_complete"])
                self.assertIsNotNone(line["error"])
                self.assertIn("timeout", line["error"].lower())

    def test_local_hf_default_has_no_metering_and_old_semantics(self) -> None:
        server = language_serve.build_server(self.runtime, port=0)
        self.addCleanup(server.server_close)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), thread.join(5)))
        with socket.create_connection(("127.0.0.1", server.server_port), timeout=10) as sock:
            sock.sendall(b"POST /nope HTTP/1.0\r\nContent-Length: 5\r\n\r\nhello")
            data = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk
        self.assertTrue(data.startswith(b"HTTP/1.0 404"))
        self.assertFalse(self.log.exists(), "no access log without --access-log")


# --- AC-7 (3)：language_serve 自算资产/构建号与拒启 -----------------------------


class StartupRefusalTests(_ServeFixture):
    def test_asset_or_build_mismatch_refuses_without_starting_llama_server(self) -> None:
        cases = {
            "weights": {"weights_sha256": "a" * 64},
            "mmproj": {"mmproj_sha256": "b" * 64},
            "binary": {"runtime_binary_sha256": "c" * 64},
            "build": {"runtime_build": "b11380"},
            "quantization": {"quantization": "Q8_0"},
            "missing_key": {"mmproj_sha256": None},
        }
        for name, overrides in cases.items():
            with self.subTest(case=name):
                code, stderr = self._main_in_process(self._llama_arguments(self._assets(**overrides)))
                self.assertEqual(code, language_serve.EXIT_REFUSED)
                self.assertIn("refused to start", stderr)
                self.assertFalse(self._fake_started())
                self.assertFalse(_port_open(self.llama_port))

    def test_unparseable_or_failing_version_refuses(self) -> None:
        for config in (
            {"version_text": "llama.cpp build 11381\n"},
            {"version_text": "version:11381 (x)\n"},
            {"version_text": "version: 11381 (deadbeef)\n", "version_exit": 1},
        ):
            with self.subTest(config=config):
                self.config_path.write_text(json.dumps(config), encoding="utf-8")
                code, stderr = self._main_in_process(self._llama_arguments(self._assets()))
                self.assertEqual(code, language_serve.EXIT_REFUSED, stderr)
                self.assertFalse(self._fake_started())

    def test_version_build_is_parsed_from_multiline_output(self) -> None:
        self.config_path.write_text(
            json.dumps({"version_text": "ggml_cuda_init: found 1 CUDA devices\nversion: 11381 (deadbeef)\nbuilt with gcc\n"}),
            encoding="utf-8",
        )
        self.assertEqual(language_serve.read_runtime_build(self.llama_bin), "b11381")

    def test_llama_server_exit_or_never_ready_is_load_failure_and_child_is_stopped(self) -> None:
        for mode in ("exit", "never_ready"):
            with self.subTest(mode=mode):
                self.config_path.write_text(json.dumps({"mode": mode}), encoding="utf-8")
                code, stderr = self._main_in_process(
                    self._llama_arguments(self._assets(), extra=("--llama-ready-timeout-s", "1.5"))
                )
                self.assertEqual(code, language_serve.EXIT_LOAD_FAILURE, stderr)
                self.assertIn("load_failure", stderr)
                self.assertTrue(self._fake_started())
                self.assertFalse(_port_open(self.llama_port))
                (self.state / "started.jsonl").unlink()

    def test_all_assets_match_serves_status_with_digest_machine_and_six_key_identity(self) -> None:
        process, port = self._start_serve(
            REPO_ROOT / "tools" / "language_serve.py", self._llama_arguments(self._assets()), isolated=False
        )
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/status", timeout=5) as response:
            status = json.loads(response.read())
        self.assertEqual(status["state"], "idle")
        self.assertRegex(status["serve_code_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(status["machine"], platform.node())
        identity = status["model_identity"]
        self.assertTrue(validate_llama_identity(identity))
        self.assertEqual(identity["weights_sha256"], _sha(self.weights))
        self.assertEqual(identity["mmproj_sha256"], _sha(self.mmproj))
        self.assertEqual(identity["runtime_binary_sha256"], _sha(self.llama_bin))
        self.assertEqual(identity["runtime_build"], "b11381")
        self.assertEqual(identity["quantization"], "Q4_K_M")
        self.assertEqual(identity["response_format_sha256"], deploy_digest.response_format_sha256(SCHEMA))
        self.assertEqual(identity["decode_config_sha256"], deploy_digest.decode_config_sha256())
        process.send_signal(signal.SIGTERM)
        self.assertEqual(process.wait(SUBPROCESS_TIMEOUT_S), 0)
        self.assertFalse(_port_open(port))
        self.assertFalse(_port_open(self.llama_port))


# --- AC-7 修订 5 / AC-16 修订 1（DIAG-VERSION-1）：语义版本行取 build ------------------

#: 诊断 `board/check.txt` 中 `--version` 的原样两行（同名提案「R4消费与诊断故障裁定」§2 引文逐字）。
SEMVER_VERSION_BYTES = b"version: 0.5.0-dev (build 0, commit unknown)\nbuilt with GNU 13.3.0 for Linux aarch64\n"


class SemverVersionParseTests(unittest.TestCase):
    """`parse_runtime_build` 纯函数：两种格式各自取值，其余一律 `StartRefused`、无缺省值。"""

    def test_accepted_forms_take_the_explicit_build_number(self) -> None:
        cases = {
            SEMVER_VERSION_BYTES.decode("ascii"): "b0",
            "version: 11381 (deadbeef)\nbuilt with gcc\n": "b11381",
            "ggml_cuda_init: found 1 CUDA devices\nversion: 0.5.0-dev (build 0, commit unknown)\n": "b0",
            "version: 1.2.3 (build 6543210, commit 0a1b2c3)\n": "b6543210",
            "version: 1.2.3+meta.1 (build 7, commit unknown)\n": "b7",
        }
        for output, expected in cases.items():
            with self.subTest(output=output):
                self.assertEqual(language_serve.parse_runtime_build(output), expected)

    def test_missing_duplicate_conflicting_or_out_of_domain_refuse(self) -> None:
        cases = {
            "no_line": "built with GNU 13.3.0 for Linux aarch64\n",
            "empty": "",
            "missing_build": "version: 0.5.0-dev (commit unknown)\n",
            "build_not_integer": "version: 0.5.0-dev (build x, commit unknown)\n",
            "missing_commit": "version: 0.5.0-dev (build 0)\n",
            "trailing_text": "version: 0.5.0-dev (build 0, commit unknown) extra\n",
            "not_semver": "version: 0.5 (build 0, commit unknown)\n",
            "no_space": "version:11381 (x)\n",
            "legacy_out_of_domain": "version: 12345678 (deadbeef)\n",
            "semver_out_of_domain": "version: 0.5.0-dev (build 12345678, commit unknown)\n",
            "non_ascii_digit": "version: \u0661\u0662 (deadbeef)\n",
            "duplicate_identical": SEMVER_VERSION_BYTES.decode("ascii") * 2,
            "conflicting_forms": "version: 11381 (deadbeef)\n" + SEMVER_VERSION_BYTES.decode("ascii"),
            "conflicting_builds": "version: 0.5.0-dev (build 0, commit unknown)\nversion: 0.5.0-dev (build 1, commit unknown)\n",
        }
        for name, output in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(language_serve.StartRefused):
                    language_serve.parse_runtime_build(output)


class SemverVersionPreflightTests(_ServeFixture):
    """生产路径（`main` → `llama_preflight` → `read_runtime_build`）：原样字节夹具修前拒启、修后 b0。"""

    def _use_version_bytes(self, raw: bytes, **extra) -> None:
        self.config_path.write_text(json.dumps({"version_text": raw.decode("ascii"), **extra}), encoding="utf-8")

    def test_fake_binary_emits_the_verbatim_fixture_bytes(self) -> None:
        self._use_version_bytes(SEMVER_VERSION_BYTES)
        completed = subprocess.run(
            [str(self.llama_bin), "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, timeout=SUBPROCESS_TIMEOUT_S, check=False,
        )
        self.assertEqual((completed.returncode, completed.stdout), (0, SEMVER_VERSION_BYTES))
        self.assertEqual(language_serve.read_runtime_build(self.llama_bin), "b0")

    def test_semver_bytes_with_b0_assets_serve_identity_runtime_build_b0(self) -> None:
        self._use_version_bytes(SEMVER_VERSION_BYTES)
        process, port = self._start_serve(
            REPO_ROOT / "tools" / "language_serve.py",
            self._llama_arguments(self._assets(runtime_build="b0")),
            isolated=False,
        )
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/status", timeout=5) as response:
            status = json.loads(response.read())
        identity = status["model_identity"]
        self.assertTrue(validate_llama_identity(identity))
        self.assertEqual(identity["runtime_build"], "b0")
        self.assertEqual(identity["runtime_binary_sha256"], _sha(self.llama_bin))
        process.send_signal(signal.SIGTERM)
        self.assertEqual(process.wait(SUBPROCESS_TIMEOUT_S), 0)
        self.assertFalse(_port_open(port))
        self.assertFalse(_port_open(self.llama_port))

    def test_semver_bytes_with_mismatched_expected_build_refuse_before_loading(self) -> None:
        self._use_version_bytes(SEMVER_VERSION_BYTES)
        for expected in ("b11381", "b00"):
            with self.subTest(expected=expected):
                code, stderr = self._main_in_process(self._llama_arguments(self._assets(runtime_build=expected)))
                self.assertEqual(code, language_serve.EXIT_REFUSED, stderr)
                self.assertIn("runtime_build mismatch: computed 'b0'", stderr)
                self.assertFalse(self._fake_started())
                self.assertFalse(_port_open(self.llama_port))

    def test_semver_refusal_branches_on_the_production_path(self) -> None:
        semver = SEMVER_VERSION_BYTES
        cases = {
            "missing_build": (b"version: 0.5.0-dev (commit unknown)\n", {}),
            "missing_line": (b"built with GNU 13.3.0 for Linux aarch64\n", {}),
            "duplicate": (semver + semver, {}),
            "conflicting": (b"version: 11381 (deadbeef)\n" + semver, {}),
            "out_of_domain": (b"version: 0.5.0-dev (build 12345678, commit unknown)\n", {}),
            "nonzero_exit": (semver, {"version_exit": 1}),
        }
        for name, (raw, extra) in cases.items():
            with self.subTest(case=name):
                self._use_version_bytes(raw, **extra)
                code, stderr = self._main_in_process(self._llama_arguments(self._assets(runtime_build="b0")))
                self.assertEqual(code, language_serve.EXIT_REFUSED, stderr)
                self.assertIn("refused to start", stderr)
                self.assertFalse(self._fake_started())
                self.assertFalse(_port_open(self.llama_port))

    def test_timeout_or_oserror_refuse(self) -> None:
        self._use_version_bytes(SEMVER_VERSION_BYTES, version_sleep_s=5)
        with self.assertRaises(language_serve.StartRefused) as caught:
            language_serve.read_runtime_build(self.llama_bin, timeout_s=0.5)
        self.assertIn("TimeoutExpired", str(caught.exception))
        with self.assertRaises(language_serve.StartRefused) as caught:
            language_serve.read_runtime_build(self.root / "bin" / "absent-llama-server")
        self.assertIn("cannot run", str(caught.exception))
        self.assertFalse(self._fake_started())


# --- AC-7 修订 2(a)：十项资源旗标逐字闭集 ------------------------------------------

#: 合同原文（同名提案「R3六题答复落实」§2 AC-7 修订 2(a)）逐字。
FROZEN_TEN_FLAGS = (
    "--parallel 1 --ctx-size 2048 --n-gpu-layers 99 --fit off --no-warmup --no-webui "
    "--no-cache-prompt --cache-ram 0 --cache-reuse 0 --offline"
)


class LlamaResourceFlagsTests(_ServeFixture):
    def test_command_is_original_four_plus_frozen_ten_flags_verbatim(self) -> None:
        command = language_serve.llama_server_command(Path("/b/llama-server"), Path("/m/w.gguf"), Path("/m/p.gguf"), 18081)
        self.assertEqual(
            command,
            ["/b/llama-server", "-m", "/m/w.gguf", "--mmproj", "/m/p.gguf", "--host", "127.0.0.1", "--port", "18081",
             *FROZEN_TEN_FLAGS.split(" ")],
        )
        self.assertEqual(" ".join(language_serve.LLAMA_RESOURCE_FLAGS), FROZEN_TEN_FLAGS)
        names = [token for token in language_serve.LLAMA_RESOURCE_FLAGS if token.startswith("--")]
        self.assertEqual(len(names), 10)
        self.assertEqual(len(set(names)), 10)

    def test_started_child_receives_exactly_the_frozen_command(self) -> None:
        process, port = self._start_serve(
            REPO_ROOT / "tools" / "language_serve.py", self._llama_arguments(self._assets()), isolated=False
        )
        started = [json.loads(line) for line in (self.state / "started.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(started), 1)
        self.assertEqual(
            started[0]["argv"],
            language_serve.llama_server_command(self.llama_bin, self.weights, self.mmproj, self.llama_port)[1:],
        )
        process.send_signal(signal.SIGTERM)
        self.assertEqual(process.wait(SUBPROCESS_TIMEOUT_S), 0)
        self.assertFalse(_port_open(port))
        self.assertFalse(_port_open(self.llama_port))


# --- AC-7 修订 2(b)：非推理 HTTP ≤ 200 两批共用累计账、下一请求前预算核对 ---------------


def _ledger_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def _counted(rows: list[dict]) -> tuple[int, int]:
    non_inference = sum(1 for row in rows if row["kind"] in language_serve.LEDGER_NON_INFERENCE_KINDS)
    inference = sum(1 for row in rows if row["kind"] == language_serve.LEDGER_INFERENCE_KIND)
    return non_inference, inference


class HealthPollLedgerTests(_ServeFixture):
    """就绪轮询：每次尝试（成功/非 200/连不上/超时）各一行结局；预算不足即 S-ENVELOPE（退出码 6）。"""

    def test_health_success_is_counted_with_outcome_and_reaches_status_snapshot(self) -> None:
        process, port = self._start_serve(
            REPO_ROOT / "tools" / "language_serve.py", self._llama_arguments(self._assets(), reserve=7), isolated=False
        )
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/status", timeout=5) as response:
            status = json.loads(response.read())
        process.send_signal(signal.SIGTERM)
        self.assertEqual(process.wait(SUBPROCESS_TIMEOUT_S), 0)
        rows = _ledger_rows(self.http_ledger)
        self.assertEqual(rows[0]["kind"], "batch_start")
        self.assertEqual((rows[0]["batch"], rows[0]["reserve"]), (1, 7))
        self.assertEqual((rows[0]["non_inference_limit"], rows[0]["inference_limit"]), (200, 335))
        health = [row for row in rows if row["kind"] == "loopback_health"]
        self.assertGreaterEqual(len(health), 1)
        self.assertEqual(health[-1]["status"], 200)
        self.assertIsNone(health[-1]["error"])
        self.assertTrue(all(row["allowed"] for row in rows[1:]))
        statuses = [row for row in rows if row["kind"] == "status"]
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0]["status"], 200)
        # 回包快照已含本次请求：健康轮询 + 本次 /status。
        self.assertEqual(
            status["http_budget"],
            {"batch": 1, "non_inference_used": len(health) + 1, "non_inference_limit": 200, "reserve": 7,
             "inference_used": 0, "inference_limit": 335},
        )

    def test_failed_health_attempts_each_have_an_outcome(self) -> None:
        cases = {"never_ready": "status", "no_listen": "error", "slow_health": "timeout"}
        for mode, outcome in cases.items():
            with self.subTest(mode=mode):
                self.config_path.write_text(json.dumps({"mode": mode}), encoding="utf-8")
                self.http_ledger.unlink(missing_ok=True)
                code, stderr = self._main_in_process(
                    self._llama_arguments(self._assets(), extra=("--llama-ready-timeout-s", "1.5"))
                )
                self.assertEqual(code, language_serve.EXIT_LOAD_FAILURE, stderr)
                health = [row for row in _ledger_rows(self.http_ledger) if row["kind"] == "loopback_health"]
                self.assertGreaterEqual(len(health), 1)
                # 每次尝试恰有一个终点：HTTP 码，或带类别前缀的错误（子进程尚未监听时是连不上）。
                for row in health:
                    self.assertIn("finished_unix_s", row)
                    self.assertTrue((row["status"] is None) != (row["error"] is None), row)
                    if row["error"] is not None:
                        self.assertRegex(row["error"], r"^(error|timeout): ")
                    else:
                        self.assertNotEqual(row["status"], 200)
                if outcome == "status":
                    self.assertIn(503, [row["status"] for row in health])
                else:
                    self.assertTrue(any(row["error"] and row["error"].startswith(f"{outcome}: ") for row in health), health)
                self._kill_fake_children()
                (self.state / "started.jsonl").unlink()
                self.assertFalse(_port_open(self.llama_port))

    def test_next_health_poll_beyond_budget_stops_with_envelope_and_never_sends_it(self) -> None:
        self.config_path.write_text(json.dumps({"mode": "never_ready"}), encoding="utf-8")
        code, stderr = self._main_in_process(
            self._llama_arguments(self._assets(), reserve=2, extra=("--non-inference-limit", "5"))
        )
        self.assertEqual(code, language_serve.EXIT_ENVELOPE, stderr)
        self.assertIn("S_ENVELOPE", stderr)
        rows = _ledger_rows(self.http_ledger)
        # 已用 + 1 + 预留 2 ≤ 5 → 恰 3 次健康轮询，第 4 次不发。
        self.assertEqual(_counted(rows), (3, 0))
        self.assertTrue(all(row["allowed"] and not row["over_limit"] for row in rows[1:]))
        self.assertFalse(_port_open(self.llama_port))

    def test_no_room_before_loading_refuses_without_starting_llama_server(self) -> None:
        self.http_ledger.parent.mkdir(parents=True, exist_ok=True)
        prior = [{"kind": "batch_start", "batch": 1, "non_inference_limit": 200, "inference_limit": 335, "reserve": 0}]
        prior += [{"kind": "result"}] * 196  # 196 + 1 + 预留 4 > 200
        self.http_ledger.write_text("".join(json.dumps(row) + "\n" for row in prior), encoding="utf-8")
        code, stderr = self._main_in_process(self._llama_arguments(self._assets(), reserve=4))
        self.assertEqual(code, language_serve.EXIT_ENVELOPE, stderr)
        self.assertFalse(self._fake_started())
        self.assertFalse(_port_open(self.llama_port))
        self.assertEqual(_ledger_rows(self.http_ledger)[-1]["kind"], "batch_start")


class TwoBatchLedgerTests(_ServeFixture):
    """收据批次与 Play 批次共用一本账：第二批启动读入第一批的全部计数；上限不一致/账损坏拒启。"""

    def _run_batch(self, reserve: int) -> dict:
        process, port = self._start_serve(
            REPO_ROOT / "tools" / "language_serve.py", self._llama_arguments(self._assets(), reserve=reserve),
            isolated=False,
        )
        for _ in range(2):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/status", timeout=5) as response:
                status = json.loads(response.read())
        process.send_signal(signal.SIGTERM)
        self.assertEqual(process.wait(SUBPROCESS_TIMEOUT_S), 0)
        self._kill_fake_children()
        (self.state / "started.jsonl").unlink()
        (self.work / "serve.out").unlink()
        return status["http_budget"]

    def test_second_batch_carries_the_first_batch_counts(self) -> None:
        first = self._run_batch(reserve=3)
        after_first = _counted(_ledger_rows(self.http_ledger))
        self.assertEqual(after_first[0], first["non_inference_used"])
        second = self._run_batch(reserve=9)
        rows = _ledger_rows(self.http_ledger)
        starts = [row for row in rows if row["kind"] == "batch_start"]
        self.assertEqual([row["batch"] for row in starts], [1, 2])
        self.assertEqual(starts[1]["prior_non_inference_used"], after_first[0])
        self.assertEqual(second["batch"], 2)
        self.assertEqual(second["reserve"], 9)
        self.assertEqual(second["non_inference_used"], _counted(rows)[0])
        self.assertGreater(second["non_inference_used"], after_first[0])

    def test_other_limits_or_corrupt_ledger_or_raised_limit_refuse(self) -> None:
        self.http_ledger.parent.mkdir(parents=True, exist_ok=True)
        self.http_ledger.write_text(
            json.dumps({"kind": "batch_start", "batch": 1, "non_inference_limit": 150, "inference_limit": 335}) + "\n",
            encoding="utf-8",
        )
        code, stderr = self._main_in_process(self._llama_arguments(self._assets()))
        self.assertEqual(code, language_serve.EXIT_REFUSED, stderr)
        self.assertIn("share one account", stderr)
        self.http_ledger.write_text("not json\n", encoding="utf-8")
        code, stderr = self._main_in_process(self._llama_arguments(self._assets()))
        self.assertEqual(code, language_serve.EXIT_REFUSED, stderr)
        self.http_ledger.write_text(json.dumps({"kind": "chat"}) + "\n", encoding="utf-8")
        code, stderr = self._main_in_process(self._llama_arguments(self._assets()))
        self.assertEqual(code, language_serve.EXIT_REFUSED, stderr)
        self.assertFalse(self._fake_started())
        for extra in (("--non-inference-limit", "201"), ("--inference-limit", "336"),
                      ("--non-inference-limit", "5", "--non-inference-reserve", "5")):
            with self.subTest(extra=extra), self.assertRaises(SystemExit) as raised, contextlib.redirect_stderr(io.StringIO()):
                language_serve.main(self._llama_arguments(self._assets(), extra=extra))
            self.assertEqual(raised.exception.code, 2)
        for missing in ("--http-ledger", "--non-inference-reserve"):
            arguments = self._llama_arguments(self._assets())
            index = arguments.index(missing)
            del arguments[index : index + 2]
            with self.subTest(missing=missing), self.assertRaises(SystemExit) as raised, contextlib.redirect_stderr(io.StringIO()):
                language_serve.main(arguments)
            self.assertEqual(raised.exception.code, 2)


class _SlowAdapter:
    """服务端适配器替身：每次推理耗时 `delay_s`，期间客户端持续 `/result` 轮询。"""

    def __init__(self, delay_s: float):
        self.delay_s = delay_s
        self.calls = 0
        self.identity = {"backend": "http", "model_form": "c2-merged", "weights_sha256": HEX_W}

    def predict_one(self, query_id, image_path, surface, g4):
        self.calls += 1
        time.sleep(self.delay_s)
        return RawSelection(raw_output=NONE, finish_reason="stop", gen_tokens=3, latency_ms=1.0,
                            prompt_sha256="p", model_id="m")


class ClientBudgetGuardTests(unittest.TestCase):
    """客户端在下一请求**发出前**按服务端快照核预算；不足即 S-ENVELOPE、不发送；推理与轮询按 query_id 关联。"""

    def _serve(self, *, limit: int, reserve: int, inference_limit: int = 335, delay_s: float = 0.0) -> tuple[str, Path, _SlowAdapter]:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        tmp = Path(directory.name)
        ledger_path = tmp / "http-ledger.jsonl"
        ledger = language_serve.HttpBudgetLedger(
            ledger_path, non_inference_limit=limit, inference_limit=inference_limit, reserve=reserve
        )
        adapter = _SlowAdapter(delay_s)
        runtime = language_serve.SingleFlightRuntime(
            adapter, scratch_directory=tmp / "scratch", delete_images_after_run=True
        )
        server = language_serve.build_server(runtime, port=0, access_log=tmp / "access.jsonl", budget=ledger)
        self.addCleanup(server.server_close)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), thread.join(5)))
        self.image = tmp / "frame.jpg"
        self.image.write_bytes(_image_bytes())
        self.addCleanup(runtime.join, 5)
        return f"http://127.0.0.1:{server.server_port}", ledger_path, adapter

    def _client(self, base: str, recorded: list[dict]) -> HttpAdapter:
        return HttpAdapter(base, t_ret_s=10.0, t_hard_s=30.0, poll_interval_s=0.02, opener=_recording_opener(recorded))

    def _wait_rows(self, path: Path, count: int) -> list[dict]:
        deadline = time.monotonic() + 5.0
        while True:
            rows = _ledger_rows(path)
            if len(rows) >= count or time.monotonic() > deadline:
                return rows
            time.sleep(0.02)

    def test_inference_and_its_result_polls_are_associated_and_counted(self) -> None:
        base, ledger, adapter = self._serve(limit=200, reserve=3, delay_s=0.15)
        recorded: list[dict] = []
        client = self._client(base, recorded)
        client.status()
        raw = client.predict_one("assoc-1", self.image, "the car", False)
        self.assertEqual(raw.raw_output, NONE)
        rows = self._wait_rows(ledger, 1 + len(recorded))[1:]
        self.assertEqual(len(rows), len(recorded))
        query = [row for row in rows if row["kind"] == "query"]
        results = [row for row in rows if row["kind"] == "result"]
        self.assertEqual(len(query), 1)
        self.assertEqual(query[0]["query_id"], "assoc-1")
        self.assertGreaterEqual(len(results), 2)
        self.assertEqual({row["query_id"] for row in results}, {"assoc-1"})
        self.assertEqual(adapter.calls, 1)
        self.assertEqual(client.http_budget["inference_used"], 1)
        self.assertEqual(client.http_budget["non_inference_used"], 1 + len(results))

    def test_next_result_poll_beyond_budget_stops_before_sending(self) -> None:
        base, ledger, _adapter = self._serve(limit=8, reserve=2, delay_s=1.0)
        recorded: list[dict] = []
        client = self._client(base, recorded)
        client.status()  # 必需请求：1
        with self.assertRaises(SelectorError) as caught:
            client.predict_one("budget-1", self.image, "the car", False)
        self.assertEqual(caught.exception.reason, "worker_stuck")
        self.assertTrue(caught.exception.detail.startswith("S_ENVELOPE"), caught.exception.detail)
        self.assertTrue(client.fatal)
        rows = self._wait_rows(ledger, 1 + len(recorded))[1:]
        self.assertEqual(len(rows), len(recorded))
        # 业务轮询只到「已用 + 1 + 预留 2 ≤ 8」：status 1 + result 5 = 6；第 7 个非推理请求不发。
        self.assertEqual(_counted(rows), (6, 1))
        self.assertTrue(all(row["allowed"] and not row["over_limit"] for row in rows))
        self.assertTrue(all(seen["status"] != 429 for seen in recorded))
        before = len(recorded)
        with self.assertRaises(SelectorError):
            client.predict_one("budget-2", self.image, "the car", False)
        self.assertEqual(len(recorded), before, "fatal client sends nothing more")

    def test_necessary_status_may_use_the_reserve_but_never_the_last_slot_beyond_limit(self) -> None:
        base, ledger, _adapter = self._serve(limit=3, reserve=2)
        recorded: list[dict] = []
        client = self._client(base, recorded)
        for _ in range(3):
            client.status()
        with self.assertRaises(SelectorError) as caught:
            client.status()
        self.assertTrue(caught.exception.detail.startswith("S_ENVELOPE"))
        self.assertEqual(len(recorded), 3)
        self.assertEqual(_counted(self._wait_rows(ledger, 4)[1:]), (3, 0))

    def test_inference_limit_and_missing_poll_headroom_stop_the_post(self) -> None:
        base, ledger, adapter = self._serve(limit=200, reserve=0, inference_limit=1)
        recorded: list[dict] = []
        client = self._client(base, recorded)
        client.status()
        client.predict_one("cap-1", self.image, "the car", False)
        sent = len(recorded)
        with self.assertRaises(SelectorError) as caught:
            client.predict_one("cap-2", self.image, "the car", False)
        self.assertTrue(caught.exception.detail.startswith("S_ENVELOPE"))
        self.assertEqual(len(recorded), sent)
        self.assertEqual(adapter.calls, 1)
        # 推理余额还在、但已无一次 /result 轮询的余量：同样不发 POST（否则模型白跑）。
        base, ledger, adapter = self._serve(limit=4, reserve=2)
        recorded = []
        client = self._client(base, recorded)
        client.status()
        client.status()
        with self.assertRaises(SelectorError) as caught:
            client.predict_one("room-1", self.image, "the car", False)
        self.assertTrue(caught.exception.detail.startswith("S_ENVELOPE"))
        self.assertEqual([seen["path"] for seen in recorded], ["/status", "/status"])
        self.assertEqual(adapter.calls, 0)

    def test_server_backstop_refuses_out_of_budget_requests_with_429_and_counts_them(self) -> None:
        base, ledger, adapter = self._serve(limit=3, reserve=2)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"{base}/status", timeout=5) as response:  # 必需请求：已用 1
            self.assertEqual(json.loads(response.read())["http_budget"]["non_inference_used"], 1)
        with self.assertRaises(urllib.error.HTTPError) as raised:
            opener.open(f"{base}/result/none", timeout=5)
        with raised.exception as error:
            self.assertEqual(error.code, 429)
            document = json.loads(error.read())
        self.assertEqual((document["error"], document["kind"]), ("S_ENVELOPE", "result"))
        self.assertEqual(document["http_budget"]["non_inference_used"], 2)
        rows = self._wait_rows(ledger, 3)[1:]
        self.assertEqual(
            [(row["kind"], row["allowed"], row["status"]) for row in rows],
            [("status", True, 200), ("result", False, 429)],
        )
        # 客户端收到 429 兜底：判 S_ENVELOPE 并停。
        client = self._client(base, [])
        client.http_budget = None
        client._expected_identity = None
        with self.assertRaises(SelectorError) as caught:
            client._call("GET", "/result/none", 5.0, budget_kind="business")
        self.assertTrue(caught.exception.detail.startswith("S_ENVELOPE"))
        self.assertTrue(client.fatal)
        self.assertEqual(adapter.calls, 0)

    def test_old_server_without_snapshot_keeps_old_client_behaviour(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        runtime = language_serve.SingleFlightRuntime(_SlowAdapter(0.0), scratch_directory=Path(directory.name))
        server = language_serve.build_server(runtime, port=0)
        self.addCleanup(server.server_close)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), thread.join(5)))
        image = Path(directory.name) / "f.jpg"
        image.write_bytes(_image_bytes())
        client = HttpAdapter(f"http://127.0.0.1:{server.server_port}", t_ret_s=10.0, t_hard_s=30.0, poll_interval_s=0.01)
        self.assertEqual(client.status(), "idle")
        self.assertEqual(client.predict_one("old-1", image, "the car", False).raw_output, NONE)
        self.assertIsNone(client.http_budget)
        with self.assertRaises(ValueError):
            language_serve.build_server(runtime, port=0, budget=language_serve.HttpBudgetLedger(
                Path(directory.name) / "l.jsonl", reserve=0))


# --- AC-7 修订 3（IR-N1 / CHANGE:5）：有界长轮询 --------------------------------------


class _BlockingAdapter:
    """服务端适配器替身：推理在 `release` 置位前一直阻塞（或按 `fail` 抛 SelectorError）。"""

    identity = {"backend": "http", "model_form": "c2-merged", "weights_sha256": HEX_W}

    def __init__(self, *, fail: bool = False):
        self.release = threading.Event()
        self.fail = fail

    def predict_one(self, query_id, image_path, surface, g4):
        self.release.wait(10.0)
        if self.fail:
            raise SelectorError("parse_failed", "injected failure")
        return RawSelection(raw_output=UNIQUE, finish_reason="stop", gen_tokens=3, latency_ms=1.0,
                            prompt_sha256="p", model_id="m")


def _llama_identity_block() -> dict:
    return {
        "backend": "http",
        "model_form": "c2-merged",
        "base_repo_revision": None,
        "weights_sha256": HEX_W,
        "device": "cuda",
        **_prompt_identity(False),
        "mmproj_sha256": HEX_M,
        "runtime_binary_sha256": HEX_B,
        "runtime_build": "b11381",
        "quantization": "Q4_K_M",
        "response_format_sha256": deploy_digest.response_format_sha256(SCHEMA),
        "decode_config_sha256": deploy_digest.decode_config_sha256(),
    }


class LongPollServerTests(unittest.TestCase):
    """服务端（真实 `build_server(long_poll=True)` + 计量/账）：分离 query_id 与参数、即时回复与到期回复。"""

    def _serve(self, adapter, *, t_hard_s: float = 60.0, long_poll: bool = True, budget: bool = True):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        tmp = Path(directory.name)
        self.ledger_path = tmp / "http-ledger.jsonl"
        ledger = language_serve.HttpBudgetLedger(self.ledger_path, reserve=0) if budget else None
        self.runtime = language_serve.SingleFlightRuntime(
            adapter, scratch_directory=tmp / "scratch", t_hard_s=t_hard_s, delete_images_after_run=True
        )
        server = language_serve.build_server(
            self.runtime, port=0, access_log=(tmp / "access.jsonl") if budget else None, budget=ledger,
            long_poll=long_poll,
        )
        self.addCleanup(server.server_close)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), thread.join(5)))
        self.addCleanup(self.runtime.join, 12)
        self.base = f"http://127.0.0.1:{server.server_port}"
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        return self.base

    def _get(self, target: str, timeout: float = 8.0) -> tuple[int, dict, float]:
        started = time.monotonic()
        try:
            with self.opener.open(f"{self.base}{target}", timeout=timeout) as response:
                code, body = response.status, response.read()
        except urllib.error.HTTPError as error:
            with error:
                code, body = error.code, error.read()
        return code, json.loads(body), time.monotonic() - started

    def _submit(self, query_id: str) -> None:
        outcome = self.runtime.submit(query_id, _image_bytes(), "the car", False)
        self.assertTrue(outcome["accepted"], outcome)

    def test_query_id_and_wait_are_separated_and_wait_is_echoed(self) -> None:
        adapter = _BlockingAdapter()
        self._serve(adapter)
        self._submit("lp-1")
        adapter.release.set()
        self.runtime.join(5)
        code, document, _ = self._get("/result/lp-1?wait_s=2.500")
        self.assertEqual(code, 200)
        self.assertEqual((document["state"], document["query_id"], document["wait_s"]), ("done", "lp-1", 2.5))
        rows = [json.loads(line) for line in self.ledger_path.read_text().splitlines()][1:]
        self.assertEqual([(row["kind"], row["query_id"]) for row in rows], [("result", "lp-1")])
        # 不带参数仍即时回复（旧语义），不回显 wait_s。
        code, document, _ = self._get("/result/lp-1")
        self.assertEqual((code, document["state"]), (200, "done"))
        self.assertNotIn("wait_s", document)

    def test_invalid_wait_or_extra_parameters_are_bad_requests(self) -> None:
        self._serve(_BlockingAdapter())
        for target in ("/result/q?wait_s=0", "/result/q?wait_s=-1", "/result/q?wait_s=4.001", "/result/q?wait_s=nan",
                       "/result/q?wait_s=inf", "/result/q?wait_s=abc", "/result/q?wait_s=", "/result/q?wait_s=1&x=2",
                       "/result/q?wait_s=1&wait_s=2", "/result/?wait_s=1", "/result/q?x=1"):
            with self.subTest(target=target):
                code, document, elapsed = self._get(target)
                self.assertEqual((code, document["error"]), (400, "BAD_REQUEST"))
                self.assertLess(elapsed, 1.0)
        self.assertEqual(language_serve.parse_result_target("/result/q?wait_s=4"), ("q", 4.0))

    def test_completion_and_failure_reply_immediately_not_at_wait_expiry(self) -> None:
        for fail in (False, True):
            with self.subTest(fail=fail):
                adapter = _BlockingAdapter(fail=fail)
                self._serve(adapter)
                self._submit("lp-now")
                threading.Timer(0.3, adapter.release.set).start()
                code, document, elapsed = self._get("/result/lp-now?wait_s=4.000")
                self.assertEqual(code, 200)
                self.assertEqual(document["state"], "failed" if fail else "done")
                self.assertGreaterEqual(elapsed, 0.25)
                self.assertLess(elapsed, 2.0, "woken by completion, not by the 4 s wait expiry")

    def test_stuck_replies_immediately(self) -> None:
        adapter = _BlockingAdapter()
        self._serve(adapter, t_hard_s=0.4)
        self._submit("lp-stuck")
        code, document, elapsed = self._get("/result/lp-stuck?wait_s=4.000")
        adapter.release.set()
        self.assertEqual((code, document["state"]), (200, "stuck"))
        self.assertGreaterEqual(elapsed, 0.3)
        self.assertLess(elapsed, 2.0)

    def test_pending_or_busy_replies_when_the_wait_expires(self) -> None:
        adapter = _BlockingAdapter()
        self._serve(adapter)
        self._submit("lp-busy")
        code, document, elapsed = self._get("/result/lp-busy?wait_s=0.400")
        self.assertEqual((code, document["state"], document["wait_s"]), (200, "busy", 0.4))
        self.assertGreaterEqual(elapsed, 0.39)
        self.assertLess(elapsed, 2.0)
        code, document, elapsed = self._get("/result/unknown?wait_s=0.300")
        self.assertEqual((document["state"], document["query_id"]), ("pending", "unknown"))
        self.assertGreaterEqual(elapsed, 0.29)
        adapter.release.set()

    def test_local_hf_server_keeps_the_old_target_parsing(self) -> None:
        self._serve(_BlockingAdapter(), long_poll=False, budget=False)
        code, document, elapsed = self._get("/result/q1?wait_s=4.000")
        self.assertEqual(code, 200)
        self.assertEqual(document["query_id"], "q1?wait_s=4.000")  # 旧行为：整个尾串当 query_id
        self.assertNotIn("wait_s", document)
        self.assertLess(elapsed, 1.0)


class _FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def monotonic(self) -> float:
        return self.now


class LongPollClientTests(unittest.TestCase):
    """客户端 `HttpAdapter`（已绑定六键 llama 身份）：w 上界、16 次硬限、不重试不回退、守账与期限。"""

    def _client(self, handler, *, t_ret_s: float = 10.0, t_hard_s: float = 60.0, bind: bool = True):
        self.clock = _FakeClock()
        self.calls: list[tuple[str, str, float]] = []
        self.sleeps: list[float] = []
        identity = _llama_identity_block()

        def opener(request, timeout):
            target = request.full_url.split("://", 1)[1].split("/", 1)[1]
            self.calls.append((request.get_method(), "/" + target, timeout))
            document = {"model_identity": identity}
            if target == "status":
                document["state"] = "idle"
            elif target == "query":
                document.update(accepted=True)
            else:
                document.update(handler(target))
            return json.dumps(document).encode("utf-8")

        client = HttpAdapter("http://board.test:18082", t_ret_s=t_ret_s, t_hard_s=t_hard_s, opener=opener,
                             monotonic=self.clock.monotonic, sleep=self.sleeps.append)
        if bind:
            client.bind_identity(identity)
        image = Path(tempfile.mkdtemp()) / "f.jpg"
        self.addCleanup(shutil.rmtree, image.parent, True)
        image.write_bytes(_image_bytes())
        self.image = image
        return client

    @staticmethod
    def _echo(target: str, **fields) -> dict:
        path, _, query = target.partition("?")
        document = {"query_id": path.split("/", 1)[1], **fields}
        if query:
            document["wait_s"] = float(query.split("=", 1)[1])
        return document

    def _results(self) -> list[tuple[str, str, float]]:
        return [call for call in self.calls if call[1].startswith("/result/")]

    def test_wait_is_min_of_4s_and_both_remaining_deadlines_and_io_tracks_t_hard(self) -> None:
        waits: list[float] = []

        def handler(target):
            waits.append(float(target.split("=", 1)[1]))
            self.clock.now += 1.25  # 每次 pending 回包耗时 1.25 s
            return self._echo(target, state="pending")

        client = self._client(handler, t_ret_s=3.0, t_hard_s=60.0)
        with self.assertRaises(SelectorError) as caught:
            client.predict_one("w-1", self.image, "the car", False)
        self.assertEqual(caught.exception.reason, "timeout")
        self.assertEqual(waits, [3.0, 1.75, 0.5])  # min(4, T_ret 剩余, T_hard 剩余)，毫秒向下取整
        self.assertTrue(all(0.0 < w <= language_serve.LONG_POLL_MAX_WAIT_S for w in waits))
        self.assertEqual(self.sleeps, [], "no extra 0.2 s client sleep")
        self.assertTrue(client.awaiting_idle)
        # T_hard 较小：w 与 I/O 截止一起随 T_hard 剩余收缩。
        waits.clear()
        client = self._client(handler, t_ret_s=50.0, t_hard_s=2.0)
        with self.assertRaises(SelectorError) as caught:
            client.predict_one("w-2", self.image, "the car", False)
        self.assertEqual(caught.exception.reason, "worker_stuck")
        self.assertTrue(client.fatal)
        self.assertEqual(waits, [2.0, 0.75])
        io_deadlines = [call[2] for call in self._results()]
        self.assertEqual(io_deadlines, [2.0, 0.75])
        self.assertTrue(all(timeout <= 5.0 for timeout in io_deadlines))

    def test_sixteen_result_attempts_at_most_then_stop_without_a_seventeenth(self) -> None:
        client = self._client(lambda target: self._echo(target, state="busy"), t_ret_s=600.0, t_hard_s=600.0)
        with self.assertRaises(SelectorError) as caught:
            client.predict_one("cap-1", self.image, "the car", False)
        self.assertEqual(caught.exception.reason, "timeout")
        self.assertIn("16", caught.exception.detail)
        self.assertEqual(len(self._results()), 16)
        self.assertTrue(all(call[1].endswith("?wait_s=4.000") for call in self._results()))
        self.assertTrue(client.awaiting_idle, "abandoned query: no re-entry before /status reports idle")

    def test_http_failure_is_not_retried_and_never_falls_back_to_short_polling(self) -> None:
        def failing(target):
            raise urllib.error.URLError("connection reset")

        client = self._client(lambda target: self._echo(target, state="busy"))
        original = client._opener

        def opener(request, timeout):
            if "/result/" in request.full_url:
                self.calls.append((request.get_method(), "/" + request.full_url.split("/", 3)[3], timeout))
                failing(request.full_url)
            return original(request, timeout)

        client._opener = opener
        with self.assertRaises(SelectorError) as caught:
            client.predict_one("err-1", self.image, "the car", False)
        self.assertEqual(caught.exception.reason, "worker_died")
        self.assertEqual(len(self._results()), 1)
        # 旧服务（不识别 wait_s，把整个尾串当 query_id、不回显）：一次即失败，不改发无参数短轮询。
        def old_server(target):
            return {"state": "pending", "query_id": target.split("/", 1)[1]}

        client = self._client(old_server)
        with self.assertRaises(SelectorError) as caught:
            client.predict_one("old-1", self.image, "the car", False)
        self.assertEqual(caught.exception.reason, "worker_died")
        self.assertIn("did not honour", caught.exception.detail)
        self.assertEqual([call[1] for call in self._results()], ["/result/old-1?wait_s=4.000"])
        self.assertTrue(client.awaiting_idle)

    def test_budget_is_checked_before_every_result_request(self) -> None:
        snapshots = iter(range(5, 100))

        def handler(target):
            used = next(snapshots)
            return self._echo(target, state="busy", http_budget={
                "non_inference_used": used, "non_inference_limit": 10, "reserve": 2,
                "inference_used": 1, "inference_limit": 335})

        client = self._client(handler, t_ret_s=600.0, t_hard_s=600.0)
        with self.assertRaises(SelectorError) as caught:
            client.predict_one("bud-1", self.image, "the car", False)
        self.assertTrue(caught.exception.detail.startswith("S_ENVELOPE"), caught.exception.detail)
        # 快照 used=5,6,7 之后：7 + 1 + 预留 2 = 10 ≤ 10 仍可发；8 + 1 + 2 > 10 → 第 5 次不发。
        self.assertEqual(len(self._results()), 4)
        self.assertTrue(client.fatal)

    def test_late_done_after_t_ret_or_t_hard_is_not_accepted(self) -> None:
        def late(seconds):
            def handler(target):
                self.clock.now += seconds
                return self._echo(target, state="done", record={"raw_output": UNIQUE, "finish_reason": "stop"})
            return handler

        client = self._client(late(3.5), t_ret_s=3.0, t_hard_s=60.0)
        with self.assertRaises(SelectorError) as caught:
            client.predict_one("late-1", self.image, "the car", False)
        self.assertEqual(caught.exception.reason, "timeout")
        self.assertIn("late done not accepted", caught.exception.detail)
        self.assertTrue(client.awaiting_idle)
        self.assertFalse(client.fatal)
        client = self._client(late(2.5), t_ret_s=30.0, t_hard_s=2.0)
        with self.assertRaises(SelectorError) as caught:
            client.predict_one("late-2", self.image, "the car", False)
        self.assertEqual(caught.exception.reason, "worker_stuck")
        self.assertTrue(client.fatal)
        # 期限内的 done 照常接纳。
        client = self._client(late(1.0), t_ret_s=3.0, t_hard_s=60.0)
        self.assertEqual(client.predict_one("ok-1", self.image, "the car", False).raw_output, UNIQUE)

    def test_completion_failure_and_stuck_states_map_as_before(self) -> None:
        # 与旧短轮询同一映射：闭集内原因原样，闭集外一律 worker_died。
        for error, reason in (("load_failure", "load_failure"), ("parse_failed", "worker_died")):
            client = self._client(lambda t, e=error: self._echo(t, state="failed", error=e, detail="x"))
            with self.assertRaises(SelectorError) as caught:
                client.predict_one("f-1", self.image, "the car", False)
            self.assertEqual(caught.exception.reason, reason)
            self.assertFalse(client.awaiting_idle)
        client = self._client(lambda t: self._echo(t, state="stuck"))
        with self.assertRaises(SelectorError) as caught:
            client.predict_one("s-1", self.image, "the car", False)
        self.assertEqual(caught.exception.reason, "worker_stuck")
        self.assertTrue(client.fatal)

    def test_unbound_or_non_llama_client_keeps_the_old_short_poll(self) -> None:
        polls = iter([{"state": "busy"}, {"state": "done", "record": {"raw_output": UNIQUE}}])
        client = self._client(lambda target: dict(next(polls), query_id=target.split("/", 1)[1]), bind=False)
        self.assertFalse(client.long_poll)
        self.assertEqual(client.predict_one("old-short", self.image, "the car", False).raw_output, UNIQUE)
        self.assertEqual([call[1] for call in self._results()], ["/result/old-short", "/result/old-short"])
        self.assertEqual(self.sleeps, [0.2])

    def test_end_to_end_one_long_poll_per_inference_on_the_real_server(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        tmp = Path(directory.name)
        adapter = _SlowAdapter(0.6)
        identity = _llama_identity_block()
        adapter.identity = {key: value for key, value in identity.items() if key != "backend"}
        runtime = language_serve.SingleFlightRuntime(adapter, scratch_directory=tmp / "s", delete_images_after_run=True)
        ledger = language_serve.HttpBudgetLedger(tmp / "l.jsonl", reserve=3)
        server = language_serve.build_server(runtime, port=0, access_log=tmp / "a.jsonl", budget=ledger, long_poll=True)
        self.addCleanup(server.server_close)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), thread.join(5)))
        self.addCleanup(runtime.join, 5)
        recorded: list[dict] = []
        sleeps: list[float] = []
        client = HttpAdapter(f"http://127.0.0.1:{server.server_port}", t_ret_s=10.0, t_hard_s=30.0,
                             opener=_recording_opener(recorded), sleep=sleeps.append)
        client.bind_identity(identity)
        image = tmp / "f.jpg"
        image.write_bytes(_image_bytes())
        started = time.monotonic()
        self.assertEqual(client.predict_one("e2e-1", image, "the car", False).raw_output, NONE)
        self.assertLess(time.monotonic() - started, 3.0)
        self.assertEqual([seen["path"] for seen in recorded],
                         ["/status", "/query", "/result/e2e-1?wait_s=4.000"])
        self.assertEqual(sleeps, [])
        self.assertEqual((client.http_budget["non_inference_used"], client.http_budget["inference_used"]), (2, 1))


# --- AC-7 (4)：部署摘要 --------------------------------------------------------


class DeployDigestTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name) / "root"

    def _rewrite_manifest(self, mutate) -> None:
        manifest = self.root / deploy_digest.MANIFEST_RELATIVE
        document = json.loads(manifest.read_text(encoding="utf-8"))
        mutate(document)
        manifest.write_text(json.dumps(document, indent=2), encoding="utf-8")

    def test_temp_source_root_digest_equals_repository_worktree(self) -> None:
        # 其他角色可能正并行改工作树文件：复制前后各算一次，取窗口内一致的一轮。
        for _ in range(3):
            before = deploy_digest.deploy_digest(REPO_ROOT)
            shutil.rmtree(self.root, ignore_errors=True)
            _copy_closed_set(self.root)
            after = deploy_digest.deploy_digest(REPO_ROOT)
            if before == after:
                break
        self.assertEqual(before, after, "repository closed set kept changing during the copy")
        self.assertEqual(deploy_digest.deploy_digest(self.root), before)

    def test_any_one_byte_change_changes_digest(self) -> None:
        paths = _copy_closed_set(self.root)
        baseline = deploy_digest.deploy_digest(self.root)
        for relative in paths:
            with self.subTest(path=relative):
                target = self.root / relative
                original = target.read_bytes()
                if relative == deploy_digest.MANIFEST_RELATIVE:
                    changed = original.replace(b"Board", b"board", 1)
                else:
                    changed = original[:-1] + bytes([original[-1] ^ 0x01])
                self.assertNotEqual(changed, original)
                self.assertEqual(len(changed), len(original))
                target.write_bytes(changed)
                self.assertNotEqual(deploy_digest.deploy_digest(self.root), baseline)
                target.write_bytes(original)
        self.assertEqual(deploy_digest.deploy_digest(self.root), baseline)

    def test_adding_or_removing_a_manifest_path_changes_digest(self) -> None:
        _copy_closed_set(self.root)
        self._rewrite_manifest(lambda document: None)  # 统一清单排版，之后的增删回到同一字节
        baseline = deploy_digest.deploy_digest(self.root)
        extra = "tools/eng_loop2/extra_module.py"
        (self.root / extra).write_text("# extra\n", encoding="utf-8")
        self.assertEqual(deploy_digest.deploy_digest(self.root), baseline)  # 未列入清单的文件不计
        self._rewrite_manifest(lambda document: document["paths"].append(extra))
        added = deploy_digest.deploy_digest(self.root)
        self.assertNotEqual(added, baseline)
        (self.root / extra).unlink()
        with self.assertRaises(deploy_digest.DeployDigestError):
            deploy_digest.deploy_digest(self.root)  # 清单列了但文件不在
        self._rewrite_manifest(lambda document: document["paths"].remove(extra))
        self.assertEqual(deploy_digest.deploy_digest(self.root), baseline)
        removed = "controller/trackers.py"
        self._rewrite_manifest(lambda document: document["paths"].remove(removed))
        (self.root / removed).unlink()
        self.assertNotIn(deploy_digest.deploy_digest(self.root), {baseline, added})

    def test_manifest_must_list_itself(self) -> None:
        _copy_closed_set(self.root)
        self._rewrite_manifest(lambda document: document["paths"].remove(deploy_digest.MANIFEST_RELATIVE))
        with self.assertRaises(deploy_digest.DeployDigestError):
            deploy_digest.deploy_digest(self.root)


# --- AC-7 (5)：隔离部署入口（AR1-6 释义：只摆清单文件、`-I -S`、显式引入临时根） ----


_FORBIDDEN_MODULE_PREFIXES = (
    "tools.eng_sft.train_lora",
    "tools.eng_jet",
    "tools.eng_loop2.analyze_play",
    "numpy",
    "torch",
    "cv2",
    "PIL",
    "transformers",
    "safetensors",
    "peft",
    "accelerate",
    "ultralytics",
    "scipy",
    "lap",
)


class IsolatedDeployEntryTests(_ServeFixture):
    def setUp(self) -> None:
        super().setUp()
        self.closed_set = _copy_closed_set(self.root)

    def test_isolated_root_serves_query_then_releases_ports_without_residue(self) -> None:
        self.config_path.write_text(json.dumps({"content": UNIQUE, "finish_reason": "stop"}), encoding="utf-8")
        process, port = self._start_serve(
            self.root / "tools" / "language_serve.py", self._llama_arguments(self._assets()), isolated=True
        )
        base = f"http://127.0.0.1:{port}"
        recorded: list[dict] = []
        opener = _recording_opener(recorded)
        status = json.loads(opener(urllib.request.Request(f"{base}/status", method="GET"), 5.0))
        self.assertEqual(status["state"], "idle")
        self.assertEqual(status["serve_code_sha256"], deploy_digest.deploy_digest(self.root))
        self.assertEqual(status["machine"], platform.node())
        self.assertTrue(validate_llama_identity(status["model_identity"]))

        image = self.work / "frame.jpg"
        image.write_bytes(_image_bytes())
        client = HttpAdapter(base, t_ret_s=10.0, t_hard_s=30.0, poll_interval_s=0.02, opener=opener)
        client.bind_identity(status["model_identity"])
        raw = client.predict_one("iso-q1", image, "the red car", False)
        self.assertEqual(raw.raw_output, UNIQUE)
        self.assertEqual(raw.finish_reason, "stop")
        self.assertEqual(raw.gen_tokens, 9)
        self.assertEqual(interpret(raw).status, "unique")
        sent = json.loads((self.state / "requests.jsonl").read_bytes().splitlines()[0])
        url = sent["messages"][0]["content"][0]["image_url"]["url"]
        self.assertEqual(base64.b64decode(url.split(",", 1)[1]), _image_bytes())
        self.assertEqual(sent["messages"][0]["content"][1]["text"], prompt_v2.build_prompt("", "the red car")["text"])
        # AC-7 修订 3：真实 llama 分支 + 已绑定六键身份的 HttpAdapter 走有界长轮询——即时完成时恰一次 result。
        self.assertTrue(client.long_poll)
        results = [seen["path"] for seen in recorded if seen["path"].startswith("/result/")]
        self.assertEqual(len(results), 1, results)
        self.assertRegex(results[0], r"^/result/iso-q1\?wait_s=\d\.\d{3}$")

        process.send_signal(signal.SIGTERM)
        self.assertEqual(process.wait(SUBPROCESS_TIMEOUT_S), 0)
        self.assertFalse(_port_open(port))
        self.assertFalse(_port_open(self.llama_port))
        with self.assertRaises(OSError):
            urllib.request.build_opener(urllib.request.ProxyHandler({})).open(f"{base}/status", timeout=2)

        # 不留图像/响应文件：scratch 下无任何文件；源码根只有清单文件、假 bin、假 GGUF 与字节码缓存。
        self.assertEqual([path for path in self.scratch.rglob("*") if path.is_file()], [])
        allowed = set(self.closed_set) | {"bin/llama-server", "models/c2-q4_k_m.gguf", "models/c2-mmproj.gguf"}
        leftovers = [
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        ]
        self.assertEqual(sorted(set(leftovers) - allowed), [])

        # 访问日志：逐请求一行，字节数与客户端实测一致（不记正文）。
        lines = [json.loads(line) for line in self.access_log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(lines), len(recorded))
        for line, seen in zip(lines, recorded):
            self.assertEqual(set(line), ACCESS_LOG_KEYS)
            for key, value in seen.items():
                self.assertEqual(line[key], value, (key, line, seen))
            self.assertTrue(line["request_body_complete"])
            self.assertIsNone(line["error"])
            self.assertLessEqual(line["started_unix_s"], line["finished_unix_s"])
        queries = [line for line in lines if line["path"] == "/query"]
        self.assertEqual(len(queries), 1)
        fields = {
            "surface": "the red car",
            "g4": "0",
            "query_id": "iso-q1",
            "expected_model_identity": json.dumps(status["model_identity"], sort_keys=True),
        }
        self.assertEqual(queries[0]["request_body_bytes"], len(_multipart(image, fields)[0]))

    def test_isolated_import_closure_of_llama_branch_is_stdlib_plus_closed_set(self) -> None:
        assets = self._assets()
        code = f"""
import json, sys
from pathlib import Path
sys.path.insert(0, {str(self.root)!r})
from tools import language_serve
arguments = language_serve.build_parser().parse_args({self._llama_arguments(assets)!r})
arguments.llama_request_timeout_s = 50.0
preflight = language_serve.llama_preflight(arguments)
runtime = language_serve.SingleFlightRuntime(
    preflight.adapter, scratch_directory=Path({str(self.work / 'closure-scratch')!r}), delete_images_after_run=True)
server = language_serve.build_server(
    runtime, port=0, extra_reply_fields={{"serve_code_sha256": preflight.serve_code_sha256, "machine": preflight.machine}},
    access_log=Path({str(self.work / 'closure.jsonl')!r}))
server.server_close()
print(json.dumps({{
    "modules": sorted(sys.modules),
    "files": sorted({{name: getattr(module, "__file__", None) for name, module in list(sys.modules.items())
                      if name.split(".")[0] in ("tools", "controller")}}.items()),
    "flags": [sys.flags.isolated, sys.flags.no_site],
    "path": sys.path,
    "adapter": type(preflight.adapter).__module__,
}}))
"""
        completed = subprocess.run(
            [sys.executable, "-I", "-S", "-c", code],
            capture_output=True, timeout=SUBPROCESS_TIMEOUT_S, cwd=self.work, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        report = json.loads(completed.stdout.decode("utf-8").splitlines()[-1])
        self.assertEqual(report["flags"], [1, 1])
        self.assertFalse([entry for entry in report["path"] if "site-packages" in entry])
        self.assertEqual(report["adapter"], "tools.eng_loop2.llama_adapter")
        self.assertFalse(self._fake_started())  # 闭包检查只跑 `--version`，不起 llama-server
        modules = report["modules"]
        for forbidden in _FORBIDDEN_MODULE_PREFIXES:
            self.assertFalse(
                [name for name in modules if name == forbidden or name.startswith(forbidden + ".")], forbidden
            )
        allowed_top = set(sys.stdlib_module_names) | {"__main__", "tools", "controller"}
        self.assertEqual(sorted({name.split(".")[0] for name in modules} - allowed_top), [])
        root = str(self.root.resolve())
        for name, path in report["files"]:
            if path is not None:
                self.assertTrue(str(Path(path).resolve()).startswith(root), (name, path))
                relative = Path(path).resolve().relative_to(root).as_posix()
                self.assertIn(relative, self.closed_set, name)


# --- AC-7/AC-9 (6)：真值隔离（AST） --------------------------------------------

_TRUTH_FRAGMENTS = (
    "eng_acq",
    "eng_fast",
    "eng_det",
    "dist_data",
    "eng_asset",
    "analyze_m3_body",
    "frame_follow_replay",
)
_ISOLATED_SOURCES = ("tools/eng_loop2/llama_adapter.py", "tools/language_serve.py")


def _imported_names(source: str) -> list[str]:
    names: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = ("." * node.level) + (node.module or "")
            names.append(module)
            names.extend(f"{module}.{alias.name}" for alias in node.names)
    return names


class TruthIsolationTests(unittest.TestCase):
    def test_adapter_and_serve_do_not_import_truth_or_scoring_modules(self) -> None:
        for relative in _ISOLATED_SOURCES:
            source = (REPO_ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(path=relative):
                names = _imported_names(source)
                self.assertTrue(names)
                for name in names:
                    parts = set(name.replace(".", " ").split())
                    self.assertFalse(parts & set(_TRUTH_FRAGMENTS), name)
                    self.assertFalse(name.startswith("tools.eng_loop2.analyze_play"), name)
                    self.assertNotEqual(name, "tools.eng_loop2.analyze_play")
                    self.assertFalse(name.startswith(("tools.eng_jet", "tools.eng_sft.train_lora")), name)
                self.assertNotIn("m3_body_truth", source)
                self.assertNotIn("CoverageEvaluator", source)

    def test_adapter_imports_only_stdlib_and_closed_set_modules(self) -> None:
        source = (REPO_ROOT / "tools/eng_loop2/llama_adapter.py").read_text(encoding="utf-8")
        allowed = {
            "controller.language_selector",
            "controller.language_bridge",
            "tools.eng_sft.prompt_v2",
            "tools.eng_sft.parse",
            "tools.eng_loop2.deploy_digest",
        }
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                modules = [base] if base not in {"tools.eng_sft", "tools.eng_loop2"} else [
                    f"{base}.{alias.name}" for alias in node.names
                ]
            else:
                continue
            for module in modules:
                top = module.split(".")[0]
                self.assertTrue(top in sys.stdlib_module_names or module in allowed, module)


if __name__ == "__main__":
    unittest.main()
