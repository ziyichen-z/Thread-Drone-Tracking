"""P1-ENG-LOOP-002 A2(b)：`llama-server`（OpenAI 兼容 chat completions）推理适配器。

* 请求体：prompt v2 逐字（`tools/eng_sft/prompt_v2.py::build_prompt`，词表 `unity-v2`）、
  `response_format` = `deploy_digest.response_format_object(入仓三态 schema)`、解码参数取自
  `deploy_digest.DECODE_CONFIG`（`temperature 0`、`max_tokens 160`、`cache_prompt false`）、
  图像为**原样字节**的 base64 data URI。
* 响应：取 `choices[0].message.content` 原文、`choices[0].finish_reason`、
  `usage.completion_tokens`，原样装进 `RawSelection`，由下游冻结 `parse.py`（经
  `controller.language_selector.interpret`）解析。**不洗掉失败**：内容不合 schema、
  `finish_reason == "length"` 照常返回，交下游记 `parse_failed`（`SCHEMA_ERROR`/`TRUNCATED`）。
* 传输失败映射到现行闭集（`REJECT_REASONS`）：连接失败 → `worker_died`；超时 → `timeout`；
  HTTP 非 2xx、响应体非 JSON 或结构缺 `choices` → `worker_died`（detail 带原因与 HTTP 码）。
* 只连 `127.0.0.1`，不走任何代理；本模块不落盘图像或响应。

本模块是板上部署闭集成员：只导入标准库、`controller.language_selector`、
`controller.language_bridge`、`tools.eng_sft.prompt_v2` 与 `tools.eng_loop2.deploy_digest`。
"""

from __future__ import annotations

import base64
import http.client
import json
from pathlib import Path
import socket
import time
from typing import Any, Callable, Mapping
import urllib.error
import urllib.parse
import urllib.request

from controller.language_bridge import LanguageBridgeError, validate_llama_identity
from controller.language_selector import RawSelection, SelectorError, _prompt_identity
from tools.eng_loop2 import deploy_digest
from tools.eng_sft import prompt_v2

#: A2(b)/(d)：解码配置——与 `deploy_digest.DECODE_CONFIG` 是**同一对象**，不另写数值。
DECODE_CONFIG = deploy_digest.DECODE_CONFIG
VOCAB_NAME = "unity-v2"
CHAT_COMPLETIONS_PATH = "/v1/chat/completions"
HEALTH_PATH = "/health"
#: 单请求超时缺省值：须小于服务端 `T_hard`（`language_serve.DEFAULT_T_HARD_S` = 60 s），
#: 让适配器先以 `timeout` 结束，而不是让单工运行时先判 `stuck`。
DEFAULT_REQUEST_TIMEOUT_S = 50.0
LOOPBACK_HOST = "127.0.0.1"

Opener = Callable[[urllib.request.Request, float], "tuple[int, bytes]"]

#: 显式空代理表：回环请求绝不经系统/环境代理转发。
_NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _default_opener(request: urllib.request.Request, timeout: float) -> tuple[int, bytes]:
    """返回 `(HTTP 码, 响应体字节)`；非 2xx 不抛，交调用方按码映射。"""
    try:
        with _NO_PROXY_OPENER.open(request, timeout=timeout) as response:
            return int(response.status), response.read()
    except urllib.error.HTTPError as error:
        with error:
            return int(error.code), error.read()


def _image_data_uri(image_bytes: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("ascii")


def _build(
    image_bytes: bytes, surface: str, g4: bool, response_format: Mapping[str, Any]
) -> tuple[dict[str, Any], str]:
    prompt = prompt_v2.build_prompt("", surface, bool(g4), VOCAB_NAME)
    body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": _image_data_uri(image_bytes)}},
                    {"type": "text", "text": prompt["text"]},
                ],
            }
        ],
        "response_format": response_format,
        "temperature": DECODE_CONFIG["temperature"],
        "max_tokens": DECODE_CONFIG["max_tokens"],
        "cache_prompt": DECODE_CONFIG["cache_prompt"],
    }
    return body, prompt["prompt_sha256"]


def build_request_body(
    image_bytes: bytes, surface: str, g4: bool, schema: Mapping[str, Any]
) -> dict[str, Any]:
    """A2(b)：一次 chat completions 请求体（prompt v2 逐字 + 入仓 schema + 解码常量 + 原样图像）。"""
    body, _ = _build(image_bytes, surface, g4, deploy_digest.response_format_object(schema))
    return body


def loopback_base_url(base_url: str) -> str:
    """只接受 `http://127.0.0.1:<port>`（无路径）；其余一律 `load_failure`。"""
    parts = urllib.parse.urlsplit(base_url)
    if (
        parts.scheme != "http"
        or parts.hostname != LOOPBACK_HOST
        or parts.port is None
        or parts.path not in {"", "/"}
        or parts.query
        or parts.fragment
    ):
        raise SelectorError(
            "load_failure", f"llama-server base url must be http://127.0.0.1:<port>, got {base_url!r}"
        )
    return f"http://{LOOPBACK_HOST}:{parts.port}"


def health_attempt(
    base_url: str, *, timeout_s: float = 2.0, opener: Opener | None = None
) -> tuple[int | None, str | None]:
    """一次 `GET /health` 尝试的结局：`(HTTP 码, None)`，或连不上/超时时 `(None, 原因)`。

    P1-ENG-LOOP-002 AC-7 修订 2(b)：就绪轮询每次尝试（成功与失败）都要有可落账的终点。"""
    request = urllib.request.Request(f"{loopback_base_url(base_url)}{HEALTH_PATH}", method="GET")
    try:
        status, _ = (opener or _default_opener)(request, timeout_s)
    except (OSError, http.client.HTTPException, ValueError) as exception:
        kind = "timeout" if _is_timeout(exception) else "error"
        return None, f"{kind}: {type(exception).__name__}: {exception}"
    return status, None


def health_status(
    base_url: str, *, timeout_s: float = 2.0, opener: Opener | None = None
) -> int | None:
    """`GET /health` 的 HTTP 码；连不上或超时返回 `None`。"""
    return health_attempt(base_url, timeout_s=timeout_s, opener=opener)[0]


def _is_timeout(exception: BaseException) -> bool:
    if isinstance(exception, (TimeoutError, socket.timeout)):
        return True
    if isinstance(exception, urllib.error.URLError):
        return isinstance(exception.reason, (TimeoutError, socket.timeout))
    return False


class LlamaServerAdapter:
    """`InferenceAdapter` 实现：同步 POST 到本机 `llama-server` 的 `/v1/chat/completions`。"""

    def __init__(
        self,
        base_url: str,
        *,
        schema: Mapping[str, Any],
        weights_sha256: str,
        mmproj_sha256: str,
        runtime_binary_sha256: str,
        runtime_build: str,
        quantization: str,
        request_timeout_s: float = DEFAULT_REQUEST_TIMEOUT_S,
        opener: Opener | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        self.base_url = loopback_base_url(base_url)
        if not float(request_timeout_s) > 0.0:
            raise SelectorError("load_failure", "request timeout must be positive")
        self.request_timeout_s = float(request_timeout_s)
        self._opener = opener or _default_opener
        self._monotonic = monotonic
        #: 实际随每个请求发送的 `response_format` 对象；`response_format_sha256` 对它本身求值。
        self._response_format = deploy_digest.response_format_object(schema)
        self.weights_sha256 = weights_sha256
        identity: dict[str, Any] = {
            "backend": "http",
            "model_form": "c2-merged",
            "base_repo_revision": None,
            "weights_sha256": weights_sha256,
            "device": "cuda",
            **_prompt_identity(False),
            "mmproj_sha256": mmproj_sha256,
            "runtime_binary_sha256": runtime_binary_sha256,
            "runtime_build": runtime_build,
            "quantization": quantization,
            "response_format_sha256": deploy_digest.canonical_sha256(self._response_format),
            "decode_config_sha256": deploy_digest.canonical_sha256(dict(DECODE_CONFIG)),
        }
        try:
            checked = validate_llama_identity(identity)
        except LanguageBridgeError as exc:
            raise SelectorError("load_failure", f"invalid llama identity: {exc}") from exc
        if not checked:
            raise SelectorError("load_failure", "llama identity keys missing")
        self.identity: dict[str, Any] = identity

    def predict_one(
        self, query_id: str, image_path: Path, surface: str, g4: bool
    ) -> RawSelection:
        try:
            image_bytes = Path(image_path).read_bytes()
        except OSError as exc:
            raise SelectorError("worker_died", f"cannot read query image: {exc}") from exc
        body, prompt_sha256 = _build(image_bytes, surface, g4, self._response_format)
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{CHAT_COMPLETIONS_PATH}", data=payload, method="POST"
        )
        request.add_header("Content-Type", "application/json")
        started = float(self._monotonic())
        try:
            status, response_bytes = self._opener(request, self.request_timeout_s)
        except SelectorError:
            raise
        except Exception as exc:  # noqa: BLE001 — 逐类映射到闭集，未知异常也不吞
            if _is_timeout(exc):
                raise SelectorError(
                    "timeout", f"llama-server request exceeded {self.request_timeout_s:g} s"
                ) from exc
            if isinstance(exc, (OSError, http.client.HTTPException)):
                raise SelectorError(
                    "worker_died", f"llama-server unreachable: {type(exc).__name__}: {exc}"
                ) from exc
            raise
        latency_ms = (float(self._monotonic()) - started) * 1000.0
        if not 200 <= int(status) < 300:
            snippet = response_bytes[:200].decode("utf-8", errors="replace")
            raise SelectorError("worker_died", f"llama-server HTTP {int(status)}: {snippet}")
        try:
            document = json.loads(response_bytes.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise SelectorError(
                "worker_died", f"llama-server HTTP {int(status)}: non-JSON response body"
            ) from exc
        choice = None
        if isinstance(document, dict):
            choices = document.get("choices")
            if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                choice = choices[0]
        if choice is None:
            raise SelectorError(
                "worker_died", f"llama-server HTTP {int(status)}: response lacks choices[0]"
            )
        message = choice.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise SelectorError(
                "worker_died", f"llama-server HTTP {int(status)}: choices[0].message.content missing"
            )
        finish_reason = choice.get("finish_reason")
        usage = document.get("usage")
        gen_tokens = usage.get("completion_tokens") if isinstance(usage, dict) else None
        return RawSelection(
            raw_output=content,
            finish_reason=finish_reason if isinstance(finish_reason, str) else None,
            gen_tokens=gen_tokens if isinstance(gen_tokens, int) and not isinstance(gen_tokens, bool) else None,
            latency_ms=latency_ms,
            prompt_sha256=prompt_sha256,
            model_id=self.weights_sha256,
        )
