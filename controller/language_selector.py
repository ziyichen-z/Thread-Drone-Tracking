"""P1-ENG-LOOP-001 §3.5：统一推理适配与三个后端（`local-hf` / `http` / `replay`）。

一条查询 = **一行** rows `{row_id, frame_path, surface, g4, vocab}`。`local-hf` 与
`http` 服务端都调既有的 `tools.eng_sft.train_lora.predict_rows`，不写第二份推理
代码；解析统一走冻结的 `tools.eng_sft.parse.parse_prediction`。`tools/eng_sft/`
零改动，selector 只接收图像路径、指令表面形与 `g4` 标志，没有 gold 通路。

`replay` 用 SFT-002 的盲索引（无 gold）与预测文件按 `row_id` 连接，只用于测试与
`replay-demo`；加载时核对两份 sha256，不符即 `replay_identity_mismatch`。
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import time
from typing import Any, Callable, Iterable, Mapping, Protocol, Sequence
import urllib.error
import urllib.request

from .language_bridge import (
    REJECT_REASONS,
    RESULT_STATUS,
    LanguageBridgeError,
    validate_llama_identity,
)
from .trackers import clip_box_norm

PROJECT_ROOT = Path(__file__).resolve().parents[1]

#: §3.5 等价判定阈值（AC-10 修订 1 冻结）。
MERGE_EQUIVALENCE_IOU = 0.9
#: §3.6 核验一致阈值（AC-10 修订 1 冻结）。
VERIFY_IOU = 0.5

VOCAB_NAME = "unity-v2"


class SelectorError(LanguageBridgeError):
    """后端层面的失败。

    `reason` 必须是 `language_bridge.REJECT_REASONS` 的成员；`status` 是它在
    §3.2(b) 里对应的结果状态（后端问题一律 `backend_error`），两者一起构成结果包
    的 `status` / `reject_reason`。
    """

    def __init__(self, reason: str, detail: str = "", *, status: str = "backend_error"):
        if reason not in REJECT_REASONS:
            raise LanguageBridgeError(f"unknown selector reason {reason!r}")
        if status not in RESULT_STATUS:
            raise LanguageBridgeError(f"unknown selector status {status!r}")
        super().__init__(f"{reason}{': ' + detail if detail else ''}")
        self.reason = reason
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class RawSelection:
    """一次推理的原始产出（§3.5 的 `RawSelection`）。"""

    raw_output: str
    finish_reason: str | None
    gen_tokens: int | None
    latency_ms: float | None
    prompt_sha256: str | None
    model_id: str | None


@dataclass(frozen=True)
class Candidate:
    index: int
    bbox_xywh_norm: tuple[float, float, float, float]
    bbox_2d_1000: tuple[int, int, int, int]
    clipped: bool

    def payload(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "bbox_xywh_norm": list(self.bbox_xywh_norm),
            "bbox_2d_1000": list(self.bbox_2d_1000),
            "clipped": self.clipped,
        }


@dataclass(frozen=True)
class Selection:
    """解析后的三态结果；`parse_failed` 时 `candidates` 为空。"""

    status: str
    candidates: tuple[Candidate, ...]
    raw: RawSelection
    parse_error: str | None


class InferenceAdapter(Protocol):
    identity: Mapping[str, Any]

    def predict_one(
        self, query_id: str, image_path: Path, surface: str, g4: bool
    ) -> RawSelection:
        ...


# --- 框转换与解析 ----------------------------------------------------------


def box_1000_to_norm_xywh(box: Sequence[int]) -> tuple[tuple[float, float, float, float], bool]:
    """1000 制 `[x1,y1,x2,y2]` → 归一化 `xywh`；返回 (框, 是否被裁剪过)。"""
    x1, y1, x2, y2 = (float(value) / 1000.0 for value in box)
    raw = (x1, y1, x2 - x1, y2 - y1)
    clipped = clip_box_norm(raw)
    if clipped is None:
        raise SelectorError("load_failure", "degenerate candidate box")
    changed = any(
        abs(left - right) > 1e-12 for left, right in zip(raw, clipped)
    )
    return clipped, changed


def interpret(raw: RawSelection) -> Selection:
    """用冻结解析器把生成文本变成三态；任何 `parse_error` 即 `parse_failed`。"""
    from tools.eng_sft.parse import parse_prediction  # 惰性：避免无谓的导入开销

    parsed = parse_prediction(raw.raw_output or "", finish_reason=raw.finish_reason)
    if parsed["parse_error"] is not None or parsed["status_pred"] is None:
        return Selection("parse_failed", (), raw, parsed["parse_error"])
    status = parsed["status_pred"]
    candidates: list[Candidate] = []
    for index, box in enumerate(parsed["boxes_1000"]):
        norm, clipped = box_1000_to_norm_xywh(box)
        candidates.append(
            Candidate(
                index=index,
                bbox_xywh_norm=norm,
                bbox_2d_1000=tuple(int(value) for value in box),
                clipped=clipped,
            )
        )
    return Selection(status, tuple(candidates), raw, None)


def iou_norm_xywh(left: Sequence[float], right: Sequence[float]) -> float:
    ax1, ay1 = float(left[0]), float(left[1])
    ax2, ay2 = ax1 + float(left[2]), ay1 + float(left[3])
    bx1, by1 = float(right[0]), float(right[1])
    bx2, by2 = bx1 + float(right[2]), by1 + float(right[3])
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    intersection = (ix2 - ix1) * (iy2 - iy1)
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - intersection
    return intersection / union if union > 0.0 else 0.0


def _iou_1000(left: Sequence[int], right: Sequence[int]) -> float:
    ax1, ay1, ax2, ay2 = (float(value) for value in left)
    bx1, by1, bx2, by2 = (float(value) for value in right)
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    intersection = (ix2 - ix1) * (iy2 - iy1)
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - intersection
    return intersection / union if union > 0.0 else 0.0


def boxes_match_one_to_one(
    left: Sequence[Sequence[int]],
    right: Sequence[Sequence[int]],
    threshold: float = MERGE_EQUIVALENCE_IOU,
) -> bool:
    """穷举一对一完美匹配（同 `evaluate.max_cardinality_matching` 口径，阈值另取）。"""
    if len(left) != len(right):
        return False
    if not left:
        return True
    edges = [[_iou_1000(a, b) >= threshold for b in right] for a in left]
    for assignment in itertools.permutations(range(len(right))):
        if all(edges[index][assignment[index]] for index in range(len(left))):
            return True
    return False


def selections_equivalent(left: Selection, right: Selection) -> tuple[bool, str]:
    """AC-9：逐行等价判定；返回 (是否等价, 理由)。"""
    if left.parse_error is not None or right.parse_error is not None:
        return False, "parse_error"
    if left.status != right.status:
        return False, "status"
    if left.status == "none":
        return True, "equivalent"
    if left.status == "unique":
        matched = _iou_1000(
            left.candidates[0].bbox_2d_1000, right.candidates[0].bbox_2d_1000
        )
        return (
            matched >= MERGE_EQUIVALENCE_IOU,
            "equivalent" if matched >= MERGE_EQUIVALENCE_IOU else "unique_iou",
        )
    if len(left.candidates) != len(right.candidates):
        return False, "candidate_count"
    ok = boxes_match_one_to_one(
        [candidate.bbox_2d_1000 for candidate in left.candidates],
        [candidate.bbox_2d_1000 for candidate in right.candidates],
    )
    return ok, "equivalent" if ok else "ambiguous_match"


def _prompt_identity(g4: bool) -> dict[str, Any]:
    from tools.eng_sft import prompt_v2

    return {
        "prompt_template_sha256": prompt_v2.template_sha256(),
        "vocab_sha256": prompt_v2.vocab_sha256(VOCAB_NAME),
        "g4_segment_sha256": prompt_v2.g4_segment_sha256() if g4 else None,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --- `replay` 后端 ---------------------------------------------------------


class ReplayAdapter:
    """盲索引 + 预测文件按 `row_id` 连接；键 `(帧字节 sha, surface, g4)`。

    重复键（§8：一组 4 行、一组 2 行）要求各行 `(raw_output, finish_reason)` 相同，
    取最小 `row_id`；不同即 `replay_conflict`；无匹配即 `replay_miss`。
    """

    def __init__(
        self,
        blind_path: Path,
        predictions_path: Path,
        *,
        expected_blind_sha256: str | None = None,
        expected_predictions_sha256: str | None = None,
        model_form: str = "c2-adapter",
        base_repo_revision: str | None = None,
        device: str = "replay",
    ):
        self.blind_path = Path(blind_path)
        self.predictions_path = Path(predictions_path)
        blind_sha = sha256_file(self.blind_path)
        predictions_sha = sha256_file(self.predictions_path)
        if expected_blind_sha256 is not None and blind_sha != expected_blind_sha256:
            raise SelectorError("replay_identity_mismatch", "blind index sha256")
        if (
            expected_predictions_sha256 is not None
            and predictions_sha != expected_predictions_sha256
        ):
            raise SelectorError("replay_identity_mismatch", "predictions sha256")
        self.blind_sha256 = blind_sha
        self.predictions_sha256 = predictions_sha
        self._predictions = {
            row["row_id"]: row for row in _read_jsonl(self.predictions_path)
        }
        self._index: dict[tuple[str, str, bool], list[str]] = {}
        for row in _read_jsonl(self.blind_path):
            if "gold" in row or "gold_state" in row or "gold_boxes_norm_xywh" in row:
                raise SelectorError("replay_identity_mismatch", "blind index carries gold")
            key = (
                Path(row["frame_path"]).stem,
                str(row["surface"]),
                bool(row["g4"]),
            )
            self._index.setdefault(key, []).append(str(row["row_id"]))
        model_id = None
        for row in self._predictions.values():
            model_id = row.get("model_id")
            break
        self.identity: dict[str, Any] = {
            "backend": "replay",
            "model_form": model_form,
            "base_repo_revision": base_repo_revision,
            "weights_sha256": model_id,
            "device": device,
            "replay_blind_sha256": self.blind_sha256,
            "replay_predictions_sha256": self.predictions_sha256,
            **_prompt_identity(False),
        }

    def row_ids_for(self, frame_sha256: str, surface: str, g4: bool) -> list[str]:
        return sorted(self._index.get((frame_sha256, surface, bool(g4)), []))

    def predict_one(
        self, query_id: str, image_path: Path, surface: str, g4: bool
    ) -> RawSelection:
        frame_sha = sha256_file(image_path)
        row_ids = self.row_ids_for(frame_sha, surface, g4)
        if not row_ids:
            raise SelectorError("replay_miss", f"{frame_sha[:12]} / {surface}")
        rows = [self._predictions[row_id] for row_id in row_ids if row_id in self._predictions]
        if not rows:
            raise SelectorError("replay_miss", "no prediction row for the blind key")
        signatures = {
            (row.get("raw_output"), row.get("finish_reason")) for row in rows
        }
        if len(signatures) > 1:
            raise SelectorError("replay_conflict", ",".join(row_ids))
        row = self._predictions[row_ids[0]]
        return RawSelection(
            raw_output=str(row.get("raw_output", "")),
            finish_reason=row.get("finish_reason"),
            gen_tokens=row.get("gen_tokens"),
            latency_ms=row.get("latency_ms"),
            prompt_sha256=row.get("prompt_sha256"),
            model_id=row.get("model_id"),
        )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


class ScriptedAdapter:
    """测试替身：按 `(surface, g4)` 或调用顺序给出预先写好的原始输出。"""

    def __init__(
        self,
        responses: Iterable[RawSelection | SelectorError],
        *,
        identity: Mapping[str, Any] | None = None,
        on_call: Callable[[str], None] | None = None,
    ):
        self._responses = list(responses)
        self._position = 0
        self.calls: list[tuple[str, Path, str, bool]] = []
        self._on_call = on_call
        self.identity = dict(
            identity
            or {
                "backend": "replay",
                "model_form": "c2-adapter",
                "base_repo_revision": None,
                "weights_sha256": "scripted",
                "device": "test",
                **_prompt_identity(False),
            }
        )

    def predict_one(
        self, query_id: str, image_path: Path, surface: str, g4: bool
    ) -> RawSelection:
        self.calls.append((query_id, Path(image_path), surface, bool(g4)))
        if self._on_call is not None:
            self._on_call(query_id)
        if self._position >= len(self._responses):
            raise SelectorError("backend_error", "scripted adapter exhausted")
        response = self._responses[self._position]
        self._position += 1
        if isinstance(response, SelectorError):
            raise response
        return response


# --- `local-hf` 后端 -------------------------------------------------------


def inference_engine():
    """Import the frozen engine on Windows without inventing a Unix RSS value."""
    if sys.platform == "win32":
        try:
            import resource  # noqa: F401
        except ImportError:
            import types

            shim = types.ModuleType("resource")
            shim.RUSAGE_SELF = 0

            def unavailable(_who):
                raise OSError("Unix getrusage is unavailable on Windows")

            shim.getrusage = unavailable
            sys.modules["resource"] = shim
    from tools.eng_sft import train_lora
    return train_lora


class LocalHfAdapter:
    """把一次查询包成一行 rows 调 `train_lora.predict_rows`（`tools/eng_sft/` 零改动）。"""

    def __init__(
        self,
        loaded: Any,
        *,
        output_directory: Path,
        model_form: str,
        weights_sha256: str | None,
        base_repo_revision: str | None,
        device: str,
    ):
        self._loaded = loaded
        self._output_directory = Path(output_directory)
        self._output_directory.mkdir(parents=True, exist_ok=True)
        self.identity: dict[str, Any] = {
            "backend": "local-hf",
            "model_form": model_form,
            "base_repo_revision": base_repo_revision,
            "weights_sha256": weights_sha256,
            "device": device,
            **_prompt_identity(False),
        }

    def predict_one(
        self, query_id: str, image_path: Path, surface: str, g4: bool
    ) -> RawSelection:
        train_lora = inference_engine()

        image_path = Path(image_path)
        out_path = self._output_directory / f"{query_id}.jsonl"
        rows = [
            {
                "row_id": query_id,
                "frame_path": image_path.name,
                "surface": surface,
                "g4": bool(g4),
                "vocab": VOCAB_NAME,
            }
        ]
        try:
            train_lora.predict_rows(
                self._loaded,
                rows,
                package_root=image_path.parent,
                out_path=out_path,
            )
        except Exception as exception:  # 适配器边界的普通异常：保留类型与消息
            raise SelectorError(
                "worker_died", f"{type(exception).__name__}: {exception}"
            ) from exception
        records = _read_jsonl(out_path)
        if len(records) != 1:
            # `backend_error` 是 `RESULT_STATUS` 成员而不是 `REJECT_REASONS` 成员；
            # 这里的 reason 必须取闭集值，否则 SelectorError 自己先抛契约错。
            raise SelectorError("worker_died", "predict_rows produced no record")
        record = records[0]
        return RawSelection(
            raw_output=str(record.get("raw_output", "")),
            finish_reason=record.get("finish_reason"),
            gen_tokens=record.get("gen_tokens"),
            latency_ms=record.get("latency_ms"),
            prompt_sha256=record.get("prompt_sha256"),
            model_id=record.get("model_id"),
        )


def load_local_adapter(
    *,
    source: Path,
    adapter_dir: Path | None,
    device: str,
    model_form: str,
    output_directory: Path,
    revision: str | None = None,
) -> LocalHfAdapter:
    """加载最终形态的模型；加载失败即 `load_failure`（宿主分档记 `FAIL`）。"""
    train_lora = inference_engine()

    try:
        loaded = train_lora.load_model(
            source,
            revision=revision,
            device=device,
            adapter_dir=adapter_dir,
        )
    except Exception as exception:
        raise SelectorError("load_failure", f"{type(exception).__name__}: {exception}") from exception
    weights_sha = None
    if adapter_dir is not None:
        candidate = Path(adapter_dir) / "adapter_model.safetensors"
        if candidate.is_file():
            weights_sha = sha256_file(candidate)
    else:
        weights = sorted(p for p in Path(source).glob("*.safetensors") if not p.name.startswith("."))
        if len(weights) == 1:
            weights_sha = sha256_file(weights[0])
        elif weights:
            # 分片权重按文件名排序，哈希绑定名称及每片内容，不依赖本机路径。
            manifest = {p.name: sha256_file(p) for p in weights}
            weights_sha = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
        else:
            raise SelectorError("load_failure", "no safetensors weights for model identity")
    return LocalHfAdapter(
        loaded,
        output_directory=output_directory,
        model_form=model_form,
        weights_sha256=weights_sha,
        base_repo_revision=revision or train_lora.BASE_REVISION,
        device=device,
    )


# --- `http` 后端（提交/轮询式单工客户端，AD3-2 / AC-8 修订 1） ------------

#: 单次 I/O 截止（AC-8 修订 1：`≤ min(5 s, 本次剩余等待)`）。
HTTP_IO_DEADLINE_S = 5.0

#: P1-ENG-LOOP-002 AC-7 修订 3（IR-N1 / CHANGE:5，用户选 A）：已绑定 A2(d) 六键 llama 身份的路径使用
#: 有界长轮询 `GET /result/<query_id>?wait_s=<w>`。`w = min(4.0 s, 本次 T_ret 剩余, 本次 T_hard 剩余)`，
#: 须为有限正数且 ≤ 4 s；每 query 至多 16 次 result 尝试（失败也计），禁止第 17 次、HTTP 错误重试或
#: 回退短轮询。服务端（`tools/language_serve.py` llama 分支）同用这两个常数。4 s 与 16 次是已选执行
#: 边界，不是目标设备性能通过线；`ceil(min(T_ret, T_hard)/4)` 不是实际计量或完成保证。
LONG_POLL_MAX_WAIT_S = 4.0
LONG_POLL_MAX_RESULT_ATTEMPTS = 16
#: 长轮询查询参数名（服务端分离 query_id 与参数；回包回显实际采用的 `wait_s`）。
LONG_POLL_PARAM = "wait_s"


def long_poll_wait_text(wait_s: float) -> str | None:
    """把本次等待截到整毫秒（向下取整，不越过任一剩余截止）；不足 1 ms 视为无正剩余 → `None`。"""
    if not math.isfinite(wait_s) or wait_s <= 0.0:
        return None
    millis = min(int(math.floor(wait_s * 1000.0)), int(LONG_POLL_MAX_WAIT_S * 1000.0))
    if millis < 1:
        return None
    return f"{millis / 1000.0:.3f}"


class HttpAdapter:
    """单工提交/轮询客户端。

    AC-8 修订 1 的三条硬性：① 每次 HTTP I/O 有 `≤ min(5 s, 剩余等待)` 的截止；
    ② 从首次提交起以本机 monotonic 计总等待 `≤ T_hard`，断联或无法确认 idle 到期
    一律 `backend_fatal`；③ `T_ret` 到期后不接纳该 `query_id` 的结果、不重入服务端，
    直到 `GET /status` 报 idle。
    """

    def __init__(
        self,
        base_url: str,
        *,
        t_ret_s: float,
        t_hard_s: float,
        poll_interval_s: float = 0.2,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        opener: Callable[[urllib.request.Request, float], bytes] | None = None,
        model_form: str = "c2-merged",
        weights_sha256: str | None = None,
        base_repo_revision: str | None = None,
        device: str = "cuda",
    ):
        self.base_url = base_url.rstrip("/")
        self.t_ret_s = float(t_ret_s)
        self.t_hard_s = float(t_hard_s)
        self.poll_interval_s = float(poll_interval_s)
        self._monotonic = monotonic
        self._sleep = sleep
        self._opener = opener or _default_opener
        #: 服务端确认 idle 之前不得再提交（客户端放弃 ≠ 服务端结束）。
        self.awaiting_idle = False
        self.fatal = False
        #: AC-8 修订 1/2：断联或无法确认 idle 的**起点**（本机 monotonic）。
        #: 从这一刻起累计超过 `T_hard` 即 `backend_fatal`，不能靠普通重试无限绕。
        self._unconfirmed_since: float | None = None
        #: 当前在途任务的原提交时刻；总截止以它为起点，不被软超时/重试推后。
        self._in_flight_since: float | None = None
        self._expected_identity: dict[str, Any] | None = None
        #: P1-ENG-LOOP-002 AC-7 修订 3：只在 `bind_identity` 绑定了六键 llama 身份后为真；
        #: 旧 HF/candidates/replay 与未绑定路径保持 `poll_interval_s` 短轮询，逐字不变。
        self.long_poll = False
        #: P1-ENG-LOOP-002 AC-7 修订 2(b)：服务端（llama-server 分支）每个回包附带的两批共用
        #: 累计账快照；旧服务端不带该字段时为 `None`，客户端行为逐字不变。
        self.http_budget: dict[str, int] | None = None
        self.identity: dict[str, Any] = {
            "backend": "http",
            "model_form": model_form,
            "base_repo_revision": base_repo_revision,
            "weights_sha256": weights_sha256,
            "device": device,
            **_prompt_identity(False),
        }

    # -- 传输 --

    def _budget_guard(self, kind: str) -> None:
        """AC-7 修订 2(b)：下一请求**发出前**按最近一次服务端快照核预算，不足即停、不发送。

        `business`（`/result` 轮询、恢复用 `/status`）：非推理已用 + 1 + 本批预留 ≤ 上限；
        `necessary`（启动身份 `/status`，由预留覆盖）：非推理已用 + 1 ≤ 上限；
        `inference`（`POST /query`）：推理尝试已用 + 1 ≤ 上限，且之后至少还能发一次业务轮询。
        无快照（旧服务端，或进程内首个必需请求）时不拦；服务端另有同判据的 429 兜底。"""
        budget = self.http_budget
        if budget is None:
            return
        used = budget["non_inference_used"]
        limit = budget["non_inference_limit"]
        reserve = budget["reserve"]
        if kind == "inference":
            ok = budget["inference_used"] + 1 <= budget["inference_limit"] and used + 1 + reserve <= limit
        elif kind == "business":
            ok = used + 1 + reserve <= limit
        elif kind == "necessary":
            ok = used + 1 <= limit
        else:  # pragma: no cover - 调用方闭集
            raise ValueError(f"unknown budget kind {kind!r}")
        if not ok:
            self.fatal = True
            raise SelectorError(
                "worker_stuck",
                f"S_ENVELOPE: next {kind} request would exceed the signed HTTP budget "
                f"(non-inference {used}/{limit}, reserve {reserve}, "
                f"inference {budget['inference_used']}/{budget['inference_limit']})",
            )

    def _take_budget(self, document: Mapping[str, Any]) -> None:
        snapshot = document.get("http_budget")
        if snapshot is None:
            return
        keys = ("non_inference_used", "non_inference_limit", "reserve", "inference_used", "inference_limit")
        if not isinstance(snapshot, dict) or not all(
            isinstance(snapshot.get(key), int) and not isinstance(snapshot.get(key), bool) for key in keys
        ):
            self._mark_unconfirmed()
            raise SelectorError("worker_died", "malformed http_budget in server response")
        self.http_budget = {key: int(snapshot[key]) for key in keys}

    def _call(self, method: str, path: str, deadline_s: float, body: bytes | None = None,
              content_type: str | None = None, *, budget_kind: str = "necessary") -> dict[str, Any]:
        self._budget_guard(budget_kind)
        if deadline_s <= 0.0:
            # 与其它 `worker_stuck` 出口一致：到期即 fatal，之后只许重启，
            # 否则这是唯一一条 stuck 之后仍能被再次提交的路径。
            self.fatal = True
            self._mark_unconfirmed()
            raise SelectorError("worker_stuck", "no budget left for the request")
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=body, method=method
        )
        if content_type is not None:
            request.add_header("Content-Type", content_type)
        try:
            payload = self._opener(request, min(HTTP_IO_DEADLINE_S, deadline_s))
        except SelectorError:
            raise
        except (urllib.error.URLError, OSError, TimeoutError) as exception:
            self._mark_unconfirmed()
            raise SelectorError(
                "worker_died", f"{type(exception).__name__}: {exception}"
            ) from exception
        try:
            document = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exception:
            self._mark_unconfirmed()
            raise SelectorError("worker_died", "unparseable server response") from exception
        if not isinstance(document, dict):
            self._mark_unconfirmed()
            raise SelectorError("worker_died", "server response must be an object")
        self._take_budget(document)
        if document.get("error") == "S_ENVELOPE":
            # 服务端兜底拒绝（429）：本请求已入账；此后不再发任何请求。
            self.fatal = True
            raise SelectorError("worker_stuck", f"S_ENVELOPE: server refused a {document.get('kind')!r} request")
        if self._expected_identity is not None:
            actual = document.get("model_identity")
            if not isinstance(actual, dict) or actual != self._expected_identity:
                self.fatal = True
                raise SelectorError("worker_stuck", "MODEL_IDENTITY_MISMATCH: restart with a matching K receipt")
        return document

    def bind_identity(self, expected: Mapping[str, Any]) -> None:
        """Verify the live service before creating a session; keep checking every reply."""
        identity = dict(expected)
        if identity.get("backend") != "http" or not identity.get("weights_sha256"):
            raise SelectorError("load_failure", "K receipt lacks a bound HTTP model identity")
        try:
            # P1-ENG-LOOP-002 A2(d)：六个 llama 身份键条件必需；逐键比较照旧由 `_call` 对整块完成。
            llama_keys = validate_llama_identity(identity)
        except LanguageBridgeError as exc:
            raise SelectorError("load_failure", f"invalid llama identity block: {exc}") from exc
        self._expected_identity = identity
        self.status()
        self.identity = identity
        # AC-7 修订 3：身份经 `/status` 逐键核过之后才启用长轮询（只限六键 llama 身份）。
        self.long_poll = bool(llama_keys)

    def _mark_unconfirmed(self) -> None:
        """记下「服务端可用性不明」的起点，并禁止在确认 idle 之前再提交。

        U-A-1：只记时是不够的——提交已被接纳而响应丢失时，服务端可能正在跑；
        下一次 `predict_one` 必须先 `GET /status` 确认 idle，不能直接 POST。
        起点取**本次在途任务的原提交时刻**（`self._in_flight_since`），这样总截止
        算的是同一个在途任务，不会被软超时或重试一次次往后推。
        """
        self.awaiting_idle = True
        if self._unconfirmed_since is None:
            self._unconfirmed_since = (
                self._in_flight_since
                if self._in_flight_since is not None
                else float(self._monotonic())
            )

    def _confirmed(self) -> None:
        self._unconfirmed_since = None

    def _unconfirmed_remaining(self) -> float:
        """距**原在途任务**总截止的剩余等待；没有未确认锚点时给满额。

        U-A-1：AC-8 修订 1 的「每次 I/O ≤ min(5 s, 本次剩余等待)」对恢复用的
        `GET /status` 同样成立——否则一次 5 s 的确认请求能整整越过 `T_hard`。
        """
        if self._unconfirmed_since is None:
            return self.t_hard_s
        return self.t_hard_s - (float(self._monotonic()) - self._unconfirmed_since)

    def _check_unconfirmed_deadline(self) -> None:
        """断联/无法确认 idle 超过 `T_hard` → `backend_fatal`（须重启，不许重试）。"""
        if self._unconfirmed_since is None:
            return
        if float(self._monotonic()) - self._unconfirmed_since > self.t_hard_s:
            self.fatal = True
            self.awaiting_idle = True
            raise SelectorError("worker_stuck", "idle unconfirmed past T_hard")

    def health_check(self) -> None:
        """会话每轮调用的有界退出钩子（U-A-1）。

        持续无法确认服务端可用、而操作者又不再发起新查询时，光靠
        `predict_one` 的入口检查永远不会到期。会话在 `tick()` 里调本方法，
        于是「不再 ask」也仍然有界地落到 `backend_fatal`。
        """
        if self.fatal:
            raise SelectorError("worker_stuck", "server needs a restart")
        self._check_unconfirmed_deadline()

    def status_document(self, deadline_s: float = HTTP_IO_DEADLINE_S) -> dict[str, Any]:
        """P1-ENG-LOOP-002 §3.2：`GET /status` 原文（服务端自算身份、`serve_code_sha256`、`machine`）。

        身份已绑定时 `_call` 照常逐键核对 `model_identity`；本方法不改 idle/在途记账。"""
        return dict(self._call("GET", "/status", deadline_s))

    def status(self, deadline_s: float = HTTP_IO_DEADLINE_S, *, budget_kind: str = "necessary") -> str:
        document = self._call("GET", "/status", deadline_s, budget_kind=budget_kind)
        state = document.get("state")
        if state not in {"idle", "busy", "stuck"}:
            self._mark_unconfirmed()
            raise SelectorError("worker_died", f"unknown server state {state!r}")
        if state == "idle":
            # U-A-1：确认来得再晚也不能抹掉原在途任务的总截止——**先核实再清零**。
            # 否则「`T_hard`=60、原提交 t=0、t=59 重试、`GET /status` 在 t=62 才回
            # idle」能靠一次迟到的确认躲过到期，重新变成一次合法提交。
            self._check_unconfirmed_deadline()
            self.awaiting_idle = False
            self._in_flight_since = None
            self._confirmed()
        if state == "stuck":
            self.fatal = True
            raise SelectorError("worker_stuck", "server reported stuck")
        return state

    def predict_one(
        self, query_id: str, image_path: Path, surface: str, g4: bool
    ) -> RawSelection:
        if self.fatal:
            raise SelectorError("worker_stuck", "server needs a restart")
        self._check_unconfirmed_deadline()
        if self.awaiting_idle:
            # 上一次放弃的查询还没确认结束：不重入服务端。确认请求本身也按
            # **原在途任务**的剩余等待收缩截止（U-A-1）。
            try:
                state = self.status(self._unconfirmed_remaining(), budget_kind="business")
            except SelectorError:
                self._check_unconfirmed_deadline()
                raise
            if state != "idle":
                self._mark_unconfirmed()
                self._check_unconfirmed_deadline()
                raise SelectorError("timeout", "server has not returned to idle")
            if self.fatal:
                # 这次 GET 期间，会话线程的 `health_check()` 可能已判定
                # `backend_fatal`（AC-8 修订 1/2、AC-17 修订 1：此后只许重启）。
                # 不在提交前再看一眼，恢复线程就会把已判死的后端重新叫起来。
                raise SelectorError("worker_stuck", "server needs a restart")
        started = float(self._monotonic())
        self._in_flight_since = started

        def remaining_hard() -> float:
            return self.t_hard_s - (float(self._monotonic()) - started)

        fields = {"surface": surface, "g4": "1" if g4 else "0", "query_id": query_id}
        if self._expected_identity is not None:
            fields["expected_model_identity"] = json.dumps(self._expected_identity, sort_keys=True)
        body, content_type = _multipart(Path(image_path), fields)
        document = self._call(
            "POST", "/query", remaining_hard(), body=body, content_type=content_type,
            budget_kind="inference",
        )
        accepted = document.get("accepted")
        if accepted is not True:
            if document.get("error") in {"SERVER_BUSY", "SERVER_STUCK"}:
                # AC-8：忙/卡住都不重入，直到 `GET /status` 报 idle。
                self.awaiting_idle = True
                self._mark_unconfirmed()
                if document.get("error") == "SERVER_STUCK":
                    self.fatal = True
                    raise SelectorError("worker_stuck", "server reported stuck")
                raise SelectorError("timeout", "SERVER_BUSY")
            raise SelectorError("worker_died", "server refused the submission")
        if self.long_poll:
            return self._long_poll_result(query_id, started, remaining_hard)
        while True:
            elapsed = float(self._monotonic()) - started
            if elapsed > self.t_hard_s:
                self.fatal = True
                self.awaiting_idle = True
                self._mark_unconfirmed()
                raise SelectorError("worker_stuck", "T_hard exceeded")
            if elapsed > self.t_ret_s:
                # AC-8 修订 1：到期即放弃该 query_id，且在 idle 之前不重入。
                self.awaiting_idle = True
                self._mark_unconfirmed()
                raise SelectorError("timeout", "T_ret exceeded")
            document = self._call(
                "GET", f"/result/{query_id}", remaining_hard(), budget_kind="business"
            )
            state = document.get("state")
            if state == "done":
                self.awaiting_idle = False
                self._in_flight_since = None
                self._confirmed()
                record = document.get("record")
                if not isinstance(record, dict):
                    raise SelectorError("worker_died", "done without a record")
                return RawSelection(
                    raw_output=str(record.get("raw_output", "")),
                    finish_reason=record.get("finish_reason"),
                    gen_tokens=record.get("gen_tokens"),
                    latency_ms=record.get("latency_ms"),
                    prompt_sha256=record.get("prompt_sha256"),
                    model_id=record.get("model_id"),
                )
            if state == "failed":
                self.awaiting_idle = False
                self._in_flight_since = None
                self._confirmed()
                error = str(document.get("error", ""))
                detail = str(document.get("detail") or error)
                raise SelectorError(
                    error if error in REJECT_REASONS else "worker_died", detail
                )
            if state == "stuck":
                self.fatal = True
                self.awaiting_idle = True
                self._mark_unconfirmed()
                raise SelectorError("worker_stuck", "server reported stuck")
            if state not in {"pending", "busy"}:
                self._mark_unconfirmed()
                raise SelectorError("worker_died", f"unknown result state {state!r}")
            self._sleep(self.poll_interval_s)

    def _abandon_after_t_ret(self, detail: str) -> SelectorError:
        """AC-8 修订 1 ③：到期即放弃该 query_id，且在 `GET /status` 报 idle 之前不重入。"""
        self.awaiting_idle = True
        self._mark_unconfirmed()
        return SelectorError("timeout", detail)

    def _fatal_after_t_hard(self, detail: str) -> SelectorError:
        self.fatal = True
        self.awaiting_idle = True
        self._mark_unconfirmed()
        return SelectorError("worker_stuck", detail)

    def _long_poll_result(
        self, query_id: str, started: float, remaining_hard: Callable[[], float]
    ) -> RawSelection:
        """P1-ENG-LOOP-002 AC-7 修订 3：六键 llama 路径的有界长轮询（不 sleep、不回退短轮询）。

        (a) 每次 `w = min(4 s, T_ret 剩余, T_hard 剩余)`，截到整毫秒，无正剩余即停、不发请求；
        (b) 每 query 至多 16 次 result 尝试（失败也计），任何时间/次数/预算边界先到即停，HTTP 错误
            不重试；下一请求前仍由 `_call` → `_budget_guard("business")` 核 200 共账与预留；
        (c) 单次 I/O 截止仍为 `min(5 s, T_hard 剩余)`（`_call`）；回包后重核 T_ret/T_hard，不接纳逾期
            `done`；服务端未回显 `wait_s`（不支持该参数）即失败，不默默回退。"""
        attempts = 0
        while True:
            elapsed = float(self._monotonic()) - started
            hard_left = self.t_hard_s - elapsed
            ret_left = self.t_ret_s - elapsed
            if hard_left <= 0.0:
                raise self._fatal_after_t_hard("T_hard exceeded")
            if ret_left <= 0.0:
                raise self._abandon_after_t_ret("T_ret exceeded")
            if attempts >= LONG_POLL_MAX_RESULT_ATTEMPTS:
                raise self._abandon_after_t_ret(
                    f"long-poll result attempt limit {LONG_POLL_MAX_RESULT_ATTEMPTS} reached"
                )
            wait_text = long_poll_wait_text(min(LONG_POLL_MAX_WAIT_S, ret_left, hard_left))
            if wait_text is None:
                # 剩余不足 1 ms：等同到期（T_ret 先到者按放弃处理，T_hard 先到者按 fatal）。
                if hard_left <= ret_left:
                    raise self._fatal_after_t_hard("T_hard exceeded (no positive wait left)")
                raise self._abandon_after_t_ret("T_ret exceeded (no positive wait left)")
            attempts += 1
            document = self._call(
                "GET",
                f"/result/{query_id}?{LONG_POLL_PARAM}={wait_text}",
                remaining_hard(),
                budget_kind="business",
            )
            echoed = document.get(LONG_POLL_PARAM)
            if (
                document.get("query_id") != query_id
                or isinstance(echoed, bool)
                or not isinstance(echoed, (int, float))
                or abs(float(echoed) - float(wait_text)) > 1e-9
            ):
                # 服务端不识别 `wait_s`（例如旧服务把整个尾串当 query_id）：不默默回退短轮询。
                self._mark_unconfirmed()
                raise SelectorError(
                    "worker_died", f"server did not honour {LONG_POLL_PARAM}={wait_text} for {query_id!r}"
                )
            state = document.get("state")
            if state == "done":
                after = float(self._monotonic()) - started
                if after > self.t_hard_s:
                    raise self._fatal_after_t_hard("T_hard exceeded before done arrived (late done not accepted)")
                if after > self.t_ret_s:
                    raise self._abandon_after_t_ret("T_ret exceeded before done arrived (late done not accepted)")
                self.awaiting_idle = False
                self._in_flight_since = None
                self._confirmed()
                record = document.get("record")
                if not isinstance(record, dict):
                    raise SelectorError("worker_died", "done without a record")
                return RawSelection(
                    raw_output=str(record.get("raw_output", "")),
                    finish_reason=record.get("finish_reason"),
                    gen_tokens=record.get("gen_tokens"),
                    latency_ms=record.get("latency_ms"),
                    prompt_sha256=record.get("prompt_sha256"),
                    model_id=record.get("model_id"),
                )
            if state == "failed":
                self.awaiting_idle = False
                self._in_flight_since = None
                self._confirmed()
                error = str(document.get("error", ""))
                detail = str(document.get("detail") or error)
                raise SelectorError(
                    error if error in REJECT_REASONS else "worker_died", detail
                )
            if state == "stuck":
                raise self._fatal_after_t_hard("server reported stuck")
            if state not in {"pending", "busy"}:
                self._mark_unconfirmed()
                raise SelectorError("worker_died", f"unknown result state {state!r}")
            # pending/busy 且本次 w 到期：不 sleep，直接进入下一次（受上面的时间/次数/预算边界约束）。


def _default_opener(request: urllib.request.Request, timeout: float) -> bytes:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as response:
        # 服务端用 409/400 表达「未接纳」；正文仍是闭集 JSON，读完再关。
        with response:
            return response.read()


_BOUNDARY = "p1englooP001boundary"


def _multipart(image_path: Path, fields: Mapping[str, str]) -> tuple[bytes, str]:
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{_BOUNDARY}\r\n".encode("utf-8"))
        chunks.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8")
        )
        chunks.append(f"{value}\r\n".encode("utf-8"))
    chunks.append(f"--{_BOUNDARY}\r\n".encode("utf-8"))
    chunks.append(
        (
            'Content-Disposition: form-data; name="image"; '
            f'filename="{image_path.name}"\r\n'
            "Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8")
    )
    chunks.append(image_path.read_bytes())
    chunks.append(b"\r\n")
    chunks.append(f"--{_BOUNDARY}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={_BOUNDARY}"


def parse_multipart(body: bytes, content_type: str) -> tuple[bytes, dict[str, str]]:
    """服务端侧的最小解析：取回图像字节与文本字段。"""
    marker = "boundary="
    if marker not in content_type:
        raise ValueError("missing multipart boundary")
    boundary = content_type.split(marker, 1)[1].strip().strip('"')
    separator = f"--{boundary}".encode("utf-8")
    fields: dict[str, str] = {}
    image = b""
    for part in body.split(separator):
        if not part.strip() or part.strip() == b"--":
            continue
        head, _, payload = part.partition(b"\r\n\r\n")
        headers = head.decode("utf-8", errors="replace")
        if 'name="' not in headers:
            continue
        name = headers.split('name="', 1)[1].split('"', 1)[0]
        payload = payload[:-2] if payload.endswith(b"\r\n") else payload
        if name == "image":
            image = payload
        else:
            fields[name] = payload.decode("utf-8", errors="replace")
    return image, fields
