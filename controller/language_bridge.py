"""P1-ENG-LOOP-001 §3.2：三个语言闭环桥文件的 schema、闭集与原子读写。

本模块只负责**契约**：字段闭集、可空规则、原子发布、请求单槽与两把锁，以及
§3.7 的受限指令文法。会话状态机在 `controller.language_loop`，推理在
`controller.language_selector`，发布门在 `controller.gated_publisher`。

fail-closed（AC-1）：未知 `action` / `status` / `reason` / `verdict` 一律拒绝。
写入侧在写出前校验，读取侧在返回前校验；读请求例外——请求由外部 CLI 写入，
结构非法时不抛给会话，而是带 `invalid_reason` 返回，由会话写 `REQUEST_INVALID`
回执（AC-1 修订 1：非法参数不改变候选、段或 epoch）。

三个文件都沿用 `controller.protocol` 的 `command_id` / `issued_unix_s` /
`expires_after_s` 头与 `atomic_write` 原子发布。合同没有给这三个文件定义任何
过期判据，所以 `expires_after_s` 只是随头携带的来源信息，**任何读取方都不据它
丢弃内容**；请求的有界等待由 CLI 的 5 s 回执超时承担（AC-1 修订 1）。
"""

from __future__ import annotations

from dataclasses import dataclass
import errno
import json
import math
import os
from pathlib import Path
import re
import time
from typing import Any, Callable, Mapping, Sequence

from .protocol import atomic_write, packet
from .resident_core import RESULTS as DESIGNATION_RESULTS, is_level2_reason


# --- schema 与文件名 -------------------------------------------------------

LANGUAGE_REQUEST_SCHEMA = "tethered-language-request/v1"
LANGUAGE_RESULT_SCHEMA = "tethered-language-result/v1"
TRACKER_STATE_SCHEMA = "tethered-tracker-state/v1"

REQUEST_FILE = "language_request.json"
RESULT_FILE = "language_result.json"
TRACKER_STATE_FILE = "tracker_state.json"
REQUEST_LOCK_FILE = "language_request.lock"
SESSION_LOCK_FILE = "language_session.lock"

#: 头部 `expires_after_s` 的缺省值；见模块 docstring：只是来源信息，不是门。
BRIDGE_EXPIRES_AFTER_S = 2.0


# --- §3.2 闭集 -------------------------------------------------------------

ACTIONS: tuple[str, ...] = (
    "ask",
    "confirm",
    "reject",
    "respecify",
    "verify",
    "confirm_lost",
    "dismiss",
    "release",
    "stop",
    # P1-ENG-CAPTURE-001 C7（追加不重排）：图像点击入口（只在 `run --language off` 捕获模式受理）。
    "click",
)

#: AC-1 修订 1：回执 `outcome` 恰七值。
OUTCOMES: tuple[str, ...] = (
    "APPLIED",
    "PENDING_QUEUED",
    "SUPERSEDED",
    "REQUEST_INVALID",
    "IGNORED_DUPLICATE",
    "IGNORED_FOREIGN_SESSION",
    "IGNORED_TERMINAL",
)

RESULT_STATUS: tuple[str, ...] = (
    "unique",
    "ambiguous",
    "none",
    "parse_failed",
    "stale_rejected",
    "retry_exhausted",
    "backend_error",
    "no_new_frame",
    "instruction_unsupported",
)

#: `parse_prediction` 直接给出的三态；其余为闭环层状态，不落进观测。
MODEL_STATUS: tuple[str, ...] = ("unique", "ambiguous", "none")

REJECT_REASONS: tuple[str, ...] = (
    "frames_late_exceeded",
    "negative_frame_delta",
    "wall_deadline_exceeded",
    "bundle_missing",
    "image_identity_changed",
    "metadata_invalid",
    "replay_miss",
    "replay_conflict",
    "replay_identity_mismatch",
    "timeout",
    "load_failure",
    "worker_stuck",
    "worker_died",
)

PURPOSES: tuple[str, ...] = ("designate", "verify")

SESSION_STATES: tuple[str, ...] = (
    "IDLE",
    "QUERYING",
    "AWAITING_CONFIRMATION",
    "TRACKING",
    "SUSPECTED",
    "LOST",
    "REINIT_REQUIRED",
    "TERMINAL",
    # P1-ENG-ACQ-001 §3.6：`TRACK_ENDED` 经人确认后的世界点转向重捕（同一 designation_id 之内）。
    "ACQUIRING",
)

#: P1-ENG-ACQ-001 §3.6：常驻指针在 `QUERYING`/`AWAITING_CONFIRMATION` 期间保持发布（跟踪中指定）。
PUBLISHING_STATES: tuple[str, ...] = ("TRACKING", "SUSPECTED", "QUERYING", "AWAITING_CONFIRMATION")

SUSPECT_KINDS: tuple[str, ...] = ("lost", "drift", "ambiguous", "tracker_failure")

#: 告警计数器的类别（§3.6 表）；`ambiguous` 不累计，直接进 `SUSPECTED`。
ALERT_KINDS: tuple[str, ...] = ("lost", "drift")

TRACKER_RAW_STATES: tuple[str, ...] = ("TRACKING", "LOST")

STATE_REASONS: tuple[str, ...] = (
    "tracker_failure",
    "verify_none",
    "verify_drift",
    "verify_ambiguous",
    "operator_release",
    "operator_reject",
    "retry_exhausted",
    "candidate_expired",
    "frame_gap",
    "frame_rollback",
    "frame_stall",
    "metadata_invalid",
    "bundle_missing",
    "image_identity_changed",
    "catchup_stale",
    "publish_expired",
    "orphan_control",
    "tracker_rejected_init",
    "backend_fatal",
    "duration_reached",
    "operator_stop",
    # P1-ENG-ACQ-001 §3.6/§3.7：转向捕获失败（总因）与两个子因。
    "acquire_failed",
    "slew_timeout",
    "adopt_timeout",
    # P1-ENG-LOOP-002（追加不重排）：A5 常驻重建上限；A7 几何拒绝的转向捕获失败子因（ACQ R1-4 承接）。
    "rebuild_limit",
    "geometry_rejected",
    # P1-ENG-CAPTURE-001 §3.6（末尾追加不重排）：捕获模式报告、语言关闭、点击与提交回滚；AR1-2 授权一致性拒绝。
    "predicting",
    "no_new_observation",
    "continuity_repaired",
    "continuity_broken",
    "continuity_disputed",
    "language_disabled",
    "image_mismatch",
    "superseded_by_click",
    "click_unavailable",
    "binding_rollback_failed",
    "authorization_input_inconsistent",
    # P1-ENG-FASTFIX-001 §3.2/§3.3（末尾追加不重排）：发布降级、重捕中/失败/歧义、重建后重捕成功。
    "publish_degraded",
    "reacquiring",
    "reacquire_failed",
    "reacquire_ambiguous",
    "rebuild_reacquired",
)

#: AC-13 修订 1 的协议错误闭集：只有这些 `seg_end` 原因算 `PROTOCOL_ABORT`。
PROTOCOL_ABORT_REASONS: tuple[str, ...] = (
    "frame_gap",
    "frame_rollback",
    "frame_stall",
    "metadata_invalid",
    "bundle_missing",
    "image_identity_changed",
    "catchup_stale",
    "publish_expired",
    "orphan_control",
    "backend_fatal",
)

VERIFY_VERDICTS: tuple[str, ...] = (
    "consistent",
    "none",
    "drift",
    "ambiguous",
    "inconclusive",
)

#: AC-16 修订 2（P-B-1，2026-09-20）：结果包里的 `inconclusive_reason` 闭集。
#: `same_frame` / `no_tracker_box` / `tracking_lag` 已**移出**——它们是**发起前**跳过，
#: 只进会话 JSONL，不产生结果包、不占 `query_id`、不调模型、不计完成核验。
INCONCLUSIVE_REASONS: tuple[str, ...] = (
    "stale",
    "frame_identity",
    "parse_failed",
    "backend_error",
)

#: 发起前跳过的原因闭集（只写会话 JSONL 的 `verify_skipped`，见 AC-16 修订 2）。
VERIFY_SKIP_REASONS: tuple[str, ...] = (
    "same_frame",
    "no_tracker_box",
    "tracking_lag",
)

#: AC-16 修订 3（P-B-2，2026-09-20）：核验**建立查询前**配对帧 P 不可用的原因闭集。
#: 与上面两个闭集互不重叠、互不扩充——它只写会话 JSONL 的
#: `kind=verify_pairing_unavailable`，不产结果包、不占 `query_id`、不调模型、
#: 不计完成核验。`snapshot_missing` = 帧环里没有该帧的加载时副本；
#: `bundle_missing` / `image_identity_changed` / `metadata_invalid` 逐字保留
#: `verify_frame_identity` 的返回值；`latest_unreadable` = `latest` 指针读不出。
PAIRING_UNAVAILABLE_REASONS: tuple[str, ...] = (
    "snapshot_missing",
    "image_identity_changed",
    "bundle_missing",
    "metadata_invalid",
    "latest_unreadable",
)

BACKENDS: tuple[str, ...] = ("local-hf", "http", "replay", "candidates")
MODEL_FORMS: tuple[str, ...] = ("c2-merged", "c2-adapter", "base", "detector-tracks")
#: P1-ENG-ACQ-001 AC-21（IR-17/B3）：`candidates` 后端（查询帧 N 的常驻 `tracked` 历史，零模型）
#: 与 `detector-tracks` 形态只能成对出现；三个 VLM 后端 × 三种 VLM 形态的原合法组合不变。
CANDIDATES_BACKEND = "candidates"
CANDIDATES_MODEL_FORM = "detector-tracks"

#: §3.3 发布最终门的拒绝原因（收据里的 `PUBLISH_REJECTED(...)`）。
PUBLISH_REJECT_REASONS: tuple[str, ...] = (
    "catchup_stale",
    "image_identity_changed",
    "bundle_missing",
    "frame_rollback",
    "publish_expired",
    "orphan_control",
)

#: §3.7 受限文法的闭集（与 SFT-002 prompt v2 词表同源，本项不扩表）。
INSTRUCTION_CLASSES: tuple[str, ...] = (
    "ambulance",
    "bus",
    "car",
    "container truck",
    "pickup truck",
    "police car",
    "suv",
    "taxi",
    "truck",
)
INSTRUCTION_COLORS: tuple[str, ...] = (
    "blue",
    "gray",
    "green",
    "purple",
    "red",
    "yellow",
)
INSTRUCTION_SIDES: tuple[str, ...] = ("left", "right")


class LanguageBridgeError(ValueError):
    """桥文件契约违例（未知闭集成员、可空规则不符、结构非法）。"""


class InstructionUnsupported(LanguageBridgeError):
    """§3.7：不合文法的指令；调用方据此产出 `instruction_unsupported`，不发查询。"""


class WriterBusy(LanguageBridgeError):
    """写者锁已被占用；CLI 据此报 `WRITER_BUSY` 并且不写请求。"""


class SessionSlotBusy(LanguageBridgeError):
    """会话锁已被活进程占用；启动据此拒绝 `SESSION_SLOT_BUSY`。"""


# --- 基础校验 --------------------------------------------------------------


def _require_member(value: Any, closed_set: Sequence[str], field: str) -> str:
    if not isinstance(value, str) or value not in closed_set:
        raise LanguageBridgeError(
            f"{field} must be one of {tuple(closed_set)!r}; received {value!r}"
        )
    return value


def _optional_member(
    value: Any, closed_set: Sequence[str], field: str
) -> str | None:
    if value is None:
        return None
    return _require_member(value, closed_set, field)


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LanguageBridgeError(f"{field} must be a non-empty string")
    return value


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field)


def _require_int(value: Any, field: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise LanguageBridgeError(f"{field} must be an integer")
    if minimum is not None and value < minimum:
        raise LanguageBridgeError(f"{field} must be >= {minimum}")
    return value


def _optional_int(
    value: Any, field: str, *, minimum: int | None = None
) -> int | None:
    if value is None:
        return None
    return _require_int(value, field, minimum=minimum)


def _optional_float(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LanguageBridgeError(f"{field} must be numeric or null")
    result = float(value)
    if not math.isfinite(result):
        raise LanguageBridgeError(f"{field} must be finite")
    return result


def _require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise LanguageBridgeError(f"{field} must be a boolean")
    return value


# --- §3.7 受限指令文法 -----------------------------------------------------


@dataclass(frozen=True)
class Instruction:
    """一条受限语言指令；`surface` 是**重新序列化**的规范形，不是用户原文。"""

    surface: str
    target_class: str
    color: str | None = None
    side: str | None = None
    reference_class: str | None = None

    @property
    def g4(self) -> bool:
        return self.side is not None

    def payload(self) -> dict[str, Any]:
        relation = (
            {"side": self.side, "reference_class": self.reference_class}
            if self.side is not None
            else None
        )
        return {
            "surface": self.surface,
            "class": self.target_class,
            "color": self.color,
            "relation": relation,
        }


def _class_alternatives() -> str:
    # 多词类别（"container truck"）必须先于其后缀（"truck"）参与匹配。
    ordered = sorted(INSTRUCTION_CLASSES, key=len, reverse=True)
    return "|".join(re.escape(name) for name in ordered)


_G1_RE = re.compile(rf"^the ({_class_alternatives()})$")
_G2_RE = re.compile(
    rf"^the ({'|'.join(INSTRUCTION_COLORS)}) ({_class_alternatives()})$"
)
_G4_RE = re.compile(
    rf"^the ({_class_alternatives()}) to the viewer's "
    rf"({'|'.join(INSTRUCTION_SIDES)}) of the ({_class_alternatives()})$"
)


def parse_instruction(text: str) -> Instruction:
    """按 §3.7 文法解析并重新序列化；不合文法即 `InstructionUnsupported`。"""
    if not isinstance(text, str):
        raise InstructionUnsupported("instruction must be text")
    normalized = " ".join(text.strip().lower().split())
    if not normalized:
        raise InstructionUnsupported("instruction must not be empty")
    match = _G4_RE.match(normalized)
    if match is not None:
        target, side, reference = match.groups()
        return Instruction(
            surface=f"the {target} to the viewer's {side} of the {reference}",
            target_class=target,
            side=side,
            reference_class=reference,
        )
    match = _G2_RE.match(normalized)
    if match is not None:
        color, target = match.groups()
        return Instruction(
            surface=f"the {color} {target}",
            target_class=target,
            color=color,
        )
    match = _G1_RE.match(normalized)
    if match is not None:
        (target,) = match.groups()
        return Instruction(surface=f"the {target}", target_class=target)
    raise InstructionUnsupported(
        f"instruction {text!r} is outside the supported grammar (section 3.7)"
    )


def instruction_from_payload(payload: Any) -> Instruction:
    """从请求里的 `instruction` 对象还原；surface 必须与闭集字段自洽。"""
    if not isinstance(payload, Mapping):
        raise InstructionUnsupported("instruction must be an object")
    surface = payload.get("surface")
    if not isinstance(surface, str):
        raise InstructionUnsupported("instruction.surface must be text")
    instruction = parse_instruction(surface)
    declared_class = payload.get("class")
    if declared_class is not None and declared_class != instruction.target_class:
        raise InstructionUnsupported("instruction.class disagrees with surface")
    declared_color = payload.get("color")
    if declared_color is not None and declared_color != instruction.color:
        raise InstructionUnsupported("instruction.color disagrees with surface")
    relation = payload.get("relation")
    if relation is not None:
        if not isinstance(relation, Mapping):
            raise InstructionUnsupported("instruction.relation must be an object")
        if (
            relation.get("side") != instruction.side
            or relation.get("reference_class") != instruction.reference_class
        ):
            raise InstructionUnsupported(
                "instruction.relation disagrees with surface"
            )
    elif instruction.side is not None:
        raise InstructionUnsupported("G4 surface requires a relation object")
    return instruction


# --- (a) 请求 --------------------------------------------------------------


@dataclass(frozen=True)
class RequestEnvelope:
    """一条读到的请求。`invalid_reason` 非空表示结构非法（会话回 REQUEST_INVALID）。"""

    session_id: str | None
    request_id: str | None
    action: str | None
    instruction: Instruction | None
    candidate_index: int | None
    token: str | None
    command_id: int | None
    issued_unix_s: float | None
    invalid_reason: str | None
    raw: Mapping[str, Any]
    #: P1-ENG-CAPTURE-001 C7：`click` 动作的字段（x_px、y_px、frame_id、image_sha256，可选 page）；其余动作 None。
    click: Mapping[str, Any] | None = None

    @property
    def addressable(self) -> bool:
        """能否给这条请求写回执：需要可信的 `session_id` 与 `request_id`。"""
        return bool(self.session_id) and bool(self.request_id)


def request_payload(
    *,
    session_id: str,
    request_id: str,
    action: str,
    instruction: Instruction | None = None,
    candidate_index: int | None = None,
    token: str | None = None,
    expires_after_s: float = BRIDGE_EXPIRES_AFTER_S,
    click: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    _require_text(session_id, "session_id")
    _require_text(request_id, "request_id")
    _require_member(action, ACTIONS, "action")
    if action == "ask" and instruction is None:
        raise LanguageBridgeError("ask requires an instruction")
    if click is not None and action != "click":
        raise LanguageBridgeError("click fields go with the click action only")
    if click is not None:
        validate_click_fields(click)
    if action == "confirm" and candidate_index is None:
        raise LanguageBridgeError("confirm requires candidate_index")
    if candidate_index is not None:
        _require_int(candidate_index, "candidate_index", minimum=0)
    envelope = packet(
        "language_request",
        {},
        expires_after_s,
        protocol_name=LANGUAGE_REQUEST_SCHEMA,
    )
    envelope.pop("command")
    envelope["request"] = {
        "session_id": session_id,
        "request_id": request_id,
        "action": action,
        "instruction": instruction.payload() if instruction is not None else None,
        "candidate_index": candidate_index,
        "token": token,
    }
    if click is not None:
        # 只在 click 时出现（既有动作的请求字节逐字不变）。
        envelope["request"]["click"] = dict(click)
    return envelope


CLICK_FIELDS: tuple[str, ...] = ("x_px", "y_px", "frame_id", "image_sha256")


def validate_click_fields(value: Any) -> dict[str, Any]:
    """C7：x_px、y_px 为有限非负数，frame_id 为非负整数，image_sha256 为 64 位小写十六进制；
    可选 `page`（点击页记录的 e2e 起点：`latest_frame_id`、`click_received_unix_s`）。画幅范围由会话按该帧核。"""
    if not isinstance(value, Mapping):
        raise LanguageBridgeError("click must be an object")
    for key in CLICK_FIELDS:
        if key not in value:
            raise LanguageBridgeError(f"click.{key} is missing")
    for key in ("x_px", "y_px"):
        number = value[key]
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(float(number)) or float(number) < 0.0:
            raise LanguageBridgeError(f"click.{key} must be a finite non-negative number")
    _require_int(value["frame_id"], "click.frame_id", minimum=0)
    sha = value["image_sha256"]
    if not isinstance(sha, str) or len(sha) != 64 or any(ch not in "0123456789abcdef" for ch in sha):
        raise LanguageBridgeError("click.image_sha256 must be a lowercase SHA-256")
    page = value.get("page")
    if page is not None and not isinstance(page, Mapping):
        raise LanguageBridgeError("click.page must be an object")
    return dict(value)


def write_request(
    runtime: Path,
    *,
    session_id: str,
    request_id: str,
    action: str,
    instruction: Instruction | None = None,
    candidate_index: int | None = None,
    token: str | None = None,
    expires_after_s: float = BRIDGE_EXPIRES_AFTER_S,
    click: Mapping[str, Any] | None = None,
) -> Path:
    payload = request_payload(
        session_id=session_id,
        request_id=request_id,
        action=action,
        instruction=instruction,
        candidate_index=candidate_index,
        token=token,
        expires_after_s=expires_after_s,
        click=click,
    )
    return atomic_write(REQUEST_FILE, payload, runtime)


def _invalid_request(
    reason: str,
    raw: Mapping[str, Any],
    *,
    session_id: str | None = None,
    request_id: str | None = None,
    command_id: int | None = None,
    issued_unix_s: float | None = None,
) -> RequestEnvelope:
    return RequestEnvelope(
        session_id=session_id,
        request_id=request_id,
        action=None,
        instruction=None,
        candidate_index=None,
        token=None,
        command_id=command_id,
        issued_unix_s=issued_unix_s,
        invalid_reason=reason,
        raw=raw,
    )


def read_request(runtime: Path) -> RequestEnvelope | None:
    """读请求槽；不存在返回 None。结构问题不抛出，交会话写 `REQUEST_INVALID`。"""
    path = Path(runtime) / REQUEST_FILE
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError:
        return _invalid_request("unreadable", {})
    try:
        document = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return _invalid_request("malformed_json", {})
    if not isinstance(document, dict):
        return _invalid_request("malformed_json", {})
    if document.get("protocol") != LANGUAGE_REQUEST_SCHEMA:
        return _invalid_request("schema_mismatch", document)
    body = document.get("request")
    if not isinstance(body, dict):
        return _invalid_request("missing_request_body", document)
    session_id = body.get("session_id")
    request_id = body.get("request_id")
    session_id = session_id if isinstance(session_id, str) and session_id else None
    request_id = request_id if isinstance(request_id, str) and request_id else None
    if session_id is None or request_id is None:
        return _invalid_request(
            "missing_identity",
            document,
            session_id=session_id,
            request_id=request_id,
        )
    command_id = body.get("command_id", document.get("command_id"))
    command_id = command_id if isinstance(command_id, int) else None
    issued = document.get("issued_unix_s")
    issued = (
        float(issued)
        if isinstance(issued, (int, float)) and not isinstance(issued, bool)
        else None
    )

    def invalid(reason: str) -> RequestEnvelope:
        # 可寻址的非法请求同样带写入头：会话靠它区分槽内残留重读与同 id 重新写入。
        return _invalid_request(
            reason,
            document,
            session_id=session_id,
            request_id=request_id,
            command_id=command_id,
            issued_unix_s=issued,
        )

    action = body.get("action")
    if not isinstance(action, str) or action not in ACTIONS:
        return invalid("unknown_action")
    instruction: Instruction | None = None
    if body.get("instruction") is not None:
        try:
            instruction = instruction_from_payload(body["instruction"])
        except InstructionUnsupported:
            return invalid("instruction_unsupported")
    candidate_index = body.get("candidate_index")
    if candidate_index is not None:
        if isinstance(candidate_index, bool) or not isinstance(candidate_index, int):
            return invalid("invalid_candidate_index")
        if candidate_index < 0:
            return invalid("invalid_candidate_index")
    token = body.get("token")
    if token is not None and not isinstance(token, str):
        return invalid("invalid_token")
    if action == "ask" and instruction is None:
        return invalid("missing_instruction")
    if action == "confirm" and candidate_index is None:
        return invalid("missing_candidate_index")
    click = None
    if action == "click":
        try:
            click = validate_click_fields(body.get("click"))
        except LanguageBridgeError:
            return invalid("invalid_click")
    return RequestEnvelope(
        session_id=session_id,
        request_id=request_id,
        action=action,
        instruction=instruction,
        candidate_index=candidate_index,
        token=token,
        command_id=command_id,
        issued_unix_s=issued,
        invalid_reason=None,
        raw=document,
        click=click,
    )


# --- (b) 结果 --------------------------------------------------------------


def _validate_candidates(value: Any, status: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise LanguageBridgeError("candidates must be a list")
    if status == "unique":
        if len(value) != 1:
            raise LanguageBridgeError("unique results carry exactly one candidate")
    elif status == "ambiguous":
        if not 2 <= len(value) <= 8:
            raise LanguageBridgeError("ambiguous results carry 2..8 candidates")
    elif value:
        # §3.2(b)：其余状态（含 `none`）一律空数组。
        raise LanguageBridgeError(f"status {status!r} must carry no candidates")
    candidates: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise LanguageBridgeError("each candidate must be an object")
        if _require_int(item.get("index"), "candidate.index", minimum=0) != index:
            raise LanguageBridgeError("candidate index must match its position")
        box = item.get("bbox_xywh_norm")
        if not isinstance(box, Sequence) or isinstance(box, (str, bytes)):
            raise LanguageBridgeError("candidate.bbox_xywh_norm must be a sequence")
        if len(box) != 4:
            raise LanguageBridgeError("bbox_xywh_norm needs x, y, width, height")
        values = [float(_optional_float(entry, "bbox_xywh_norm")) for entry in box]
        raw_box = item.get("bbox_2d_1000")
        if not isinstance(raw_box, Sequence) or isinstance(raw_box, (str, bytes)):
            raise LanguageBridgeError("candidate.bbox_2d_1000 must be a sequence")
        if len(raw_box) != 4:
            raise LanguageBridgeError("bbox_2d_1000 needs x1, y1, x2, y2")
        candidates.append(
            {
                "index": index,
                "bbox_xywh_norm": values,
                "bbox_2d_1000": [_require_int(entry, "bbox_2d_1000") for entry in raw_box],
                "clipped": _require_bool(item.get("clipped"), "candidate.clipped"),
            }
        )
    return candidates


def _validate_verify_block(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise LanguageBridgeError("verify block must be an object")
    tracker_box = value.get("tracker_box_at_frame")
    if tracker_box is not None:
        if (
            not isinstance(tracker_box, Sequence)
            or isinstance(tracker_box, (str, bytes))
            or len(tracker_box) != 4
        ):
            raise LanguageBridgeError("tracker_box_at_frame needs four numbers")
        tracker_box = [float(_optional_float(item, "tracker_box")) for item in tracker_box]
    return {
        "paired_frame_id": _optional_int(
            value.get("paired_frame_id"), "paired_frame_id", minimum=0
        ),
        "tracker_box_at_frame": tracker_box,
        "iou": _optional_float(value.get("iou"), "iou"),
        "verdict": _require_member(value.get("verdict"), VERIFY_VERDICTS, "verdict"),
        "inconclusive_reason": _optional_member(
            value.get("inconclusive_reason"), INCONCLUSIVE_REASONS, "inconclusive_reason"
        ),
        "consecutive_alert": _require_int(
            value.get("consecutive_alert"), "consecutive_alert", minimum=0
        ),
        "alert_kind": _optional_member(
            value.get("alert_kind"), ALERT_KINDS, "alert_kind"
        ),
    }


def require_backend_model_form(backend: Any, model_form: Any) -> tuple[str, str]:
    """后端与模型形态的闭集与配对（AC-21）：`candidates` ⇔ `detector-tracks`。"""
    backend = _require_member(backend, BACKENDS, "backend")
    model_form = _require_member(model_form, MODEL_FORMS, "model_form")
    if (backend == CANDIDATES_BACKEND) != (model_form == CANDIDATES_MODEL_FORM):
        raise LanguageBridgeError(
            f"backend {backend!r} cannot pair with model_form {model_form!r}: "
            f"{CANDIDATES_BACKEND!r} and {CANDIDATES_MODEL_FORM!r} only pair with each other"
        )
    return backend, model_form


#: P1-ENG-LOOP-002 A2(d)：`model` 块六个**条件必需**身份键（全有或全无；全无 = 旧结果/报告照旧）。
LLAMA_IDENTITY_KEYS: tuple[str, ...] = (
    "mmproj_sha256",
    "runtime_binary_sha256",
    "runtime_build",
    "quantization",
    "response_format_sha256",
    "decode_config_sha256",
)
#: A2(d)：`quantization` 闭集。
QUANTIZATIONS: tuple[str, ...] = ("Q4_K_M",)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_RUNTIME_BUILD = re.compile(r"^b[0-9]{1,7}$")


def _require_hex64(value: Any, field: str) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise LanguageBridgeError(f"{field} must be 64 lowercase hex characters")
    return value


def validate_llama_identity(value: Mapping[str, Any]) -> dict[str, Any]:
    """A2(d) 条件必需校验：六键全无 → `{}`；任一出现 → 六键齐全且类型/值域合法，
    并要求 `backend == "http"`、`model_form == "c2-merged"`、`weights_sha256` 与
    `prompt_template_sha256` 同为 hex64。任何不符即 `LanguageBridgeError`（不再只做可选文本，F28）。

    「出现」按键存在判定（C1-AC6）：键在、值为 `null` 也算出现，随后按类型/值域拒绝；
    只有六键都不在块里才算「全无」。"""
    present = [key for key in LLAMA_IDENTITY_KEYS if key in value]
    if not present:
        return {}
    missing = [key for key in LLAMA_IDENTITY_KEYS if key not in value]
    if missing:
        raise LanguageBridgeError(
            f"model identity carries {present} but lacks {missing}: the six llama keys are all-or-none"
        )
    if value.get("backend") != "http":
        raise LanguageBridgeError("llama identity keys require backend 'http'")
    if value.get("model_form") != "c2-merged":
        raise LanguageBridgeError("llama identity keys require model_form 'c2-merged'")
    _require_hex64(value.get("weights_sha256"), "weights_sha256")
    _require_hex64(value.get("prompt_template_sha256"), "prompt_template_sha256")
    checked = {
        "mmproj_sha256": _require_hex64(value.get("mmproj_sha256"), "mmproj_sha256"),
        "runtime_binary_sha256": _require_hex64(
            value.get("runtime_binary_sha256"), "runtime_binary_sha256"
        ),
        "runtime_build": value.get("runtime_build"),
        "quantization": _require_member(value.get("quantization"), QUANTIZATIONS, "quantization"),
        "response_format_sha256": _require_hex64(
            value.get("response_format_sha256"), "response_format_sha256"
        ),
        "decode_config_sha256": _require_hex64(
            value.get("decode_config_sha256"), "decode_config_sha256"
        ),
    }
    build = checked["runtime_build"]
    if not isinstance(build, str) or _RUNTIME_BUILD.fullmatch(build) is None:
        raise LanguageBridgeError("runtime_build must match ^b[0-9]{1,7}$")
    return checked


def _validate_model_block(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise LanguageBridgeError("model block must be an object")
    backend, model_form = require_backend_model_form(
        value.get("backend"), value.get("model_form")
    )
    llama = validate_llama_identity(value)
    return {
        "backend": backend,
        "model_form": model_form,
        "base_repo_revision": _optional_text(
            value.get("base_repo_revision"), "base_repo_revision"
        ),
        "weights_sha256": _optional_text(
            value.get("weights_sha256"), "weights_sha256"
        ),
        "prompt_template_sha256": _optional_text(
            value.get("prompt_template_sha256"), "prompt_template_sha256"
        ),
        "vocab_sha256": _optional_text(value.get("vocab_sha256"), "vocab_sha256"),
        "g4_segment_sha256": _optional_text(
            value.get("g4_segment_sha256"), "g4_segment_sha256"
        ),
        "device": _optional_text(value.get("device"), "device"),
        "finish_reason": _optional_text(value.get("finish_reason"), "finish_reason"),
        "gen_tokens": _optional_int(value.get("gen_tokens"), "gen_tokens", minimum=0),
        "replay_blind_sha256": _optional_text(
            value.get("replay_blind_sha256"), "replay_blind_sha256"
        ),
        "replay_predictions_sha256": _optional_text(
            value.get("replay_predictions_sha256"), "replay_predictions_sha256"
        ),
        # 六键全无时不出现（旧结果字节形态不变）；全有时逐键已校验。
        **llama,
    }


def result_payload(
    *,
    query_id: str,
    result_id: str,
    request_id: str | None,
    epoch: int,
    segment_index: int | None,
    attempt: int,
    attempt_limit: int,
    purpose: str,
    status: str,
    frame_id: int | None = None,
    frame_sha256: str | None = None,
    capture_monotonic_s: float | None = None,
    capture_unix_s: float | None = None,
    query_unix_s: float | None = None,
    reject_reason: str | None = None,
    last_status: str | None = None,
    last_reject_reason: str | None = None,
    candidates: Sequence[Mapping[str, Any]] = (),
    verify: Mapping[str, Any] | None = None,
    model: Mapping[str, Any] | None = None,
    latency_ms: float | None = None,
    frames_late: int | None = None,
    k_ret: int | None = None,
    wall_elapsed_s: float | None = None,
    preview_path: str | None = None,
    raw_output: str | None = None,
    parse_error: str | None = None,
    expires_after_s: float = BRIDGE_EXPIRES_AFTER_S,
) -> dict[str, Any]:
    """按 §3.2(b) 组装一份结果；可空规则与闭集在此强制。"""
    _require_text(query_id, "query_id")
    _require_text(result_id, "result_id")
    _require_member(purpose, PURPOSES, "purpose")
    _require_member(status, RESULT_STATUS, "status")
    _require_int(epoch, "epoch", minimum=0)
    _require_int(attempt, "attempt", minimum=1)
    _require_int(attempt_limit, "attempt_limit", minimum=1)
    _optional_member(reject_reason, REJECT_REASONS, "reject_reason")
    if reject_reason is not None and status not in {"stale_rejected", "backend_error"}:
        raise LanguageBridgeError(
            "reject_reason only refines stale_rejected/backend_error"
        )
    if status == "stale_rejected" and reject_reason is None:
        raise LanguageBridgeError("stale_rejected requires a reject_reason")
    if status == "retry_exhausted":
        _require_member(last_status, RESULT_STATUS, "last_status")
        _optional_member(last_reject_reason, REJECT_REASONS, "last_reject_reason")
    elif last_status is not None or last_reject_reason is not None:
        raise LanguageBridgeError(
            "last_status/last_reject_reason belong to retry_exhausted only"
        )
    frame_fields = (frame_id, frame_sha256, capture_monotonic_s, capture_unix_s)
    if frame_id is None and any(field is not None for field in frame_fields[1:]):
        raise LanguageBridgeError("frame fields are all-or-nothing (section 3.2b)")
    if frame_id is None and frames_late is not None:
        raise LanguageBridgeError("frames_late must be null when no frame was taken")
    envelope = packet(
        "language_result",
        {},
        expires_after_s,
        protocol_name=LANGUAGE_RESULT_SCHEMA,
    )
    envelope.pop("command")
    envelope["result"] = {
        "query_id": query_id,
        "result_id": result_id,
        "request_id": _optional_text(request_id, "request_id"),
        "epoch": epoch,
        "segment_index": _optional_int(segment_index, "segment_index", minimum=0),
        "attempt": attempt,
        "attempt_limit": attempt_limit,
        "purpose": purpose,
        "frame_id": _optional_int(frame_id, "frame_id", minimum=0),
        "frame_sha256": _optional_text(frame_sha256, "frame_sha256"),
        "capture_monotonic_s": _optional_float(
            capture_monotonic_s, "capture_monotonic_s"
        ),
        "capture_unix_s": _optional_float(capture_unix_s, "capture_unix_s"),
        "query_unix_s": _optional_float(query_unix_s, "query_unix_s"),
        "status": status,
        "reject_reason": reject_reason,
        "last_status": last_status,
        "last_reject_reason": last_reject_reason,
        "candidates": _validate_candidates(list(candidates), status),
        "verify": _validate_verify_block(verify) if verify is not None else None,
        "model": _validate_model_block(model) if model is not None else None,
        "latency_ms": _optional_float(latency_ms, "latency_ms"),
        "frames_late": _optional_int(frames_late, "frames_late"),
        "k_ret": _optional_int(k_ret, "k_ret", minimum=0),
        "wall_elapsed_s": _optional_float(wall_elapsed_s, "wall_elapsed_s"),
        "preview_path": _optional_text(preview_path, "preview_path"),
        "raw_output": raw_output if isinstance(raw_output, str) else None,
        "parse_error": _optional_text(parse_error, "parse_error"),
    }
    if purpose == "verify" and envelope["result"]["verify"] is None:
        raise LanguageBridgeError("verify results require the verify block")
    if purpose == "designate" and envelope["result"]["verify"] is not None:
        raise LanguageBridgeError("designate results must not carry a verify block")
    return envelope


def write_result(runtime: Path, payload: Mapping[str, Any]) -> Path:
    """发布当前世代最近一份结果（§3.2(b)：桥文件只放最近一份）。"""
    document = dict(payload)
    if document.get("protocol") != LANGUAGE_RESULT_SCHEMA:
        raise LanguageBridgeError("result payload must carry the result schema")
    return atomic_write(RESULT_FILE, document, runtime)


def read_result(runtime: Path) -> dict[str, Any] | None:
    """读结果槽并 fail-closed 校验闭集；未知 `status`/`verdict` 即抛出。"""
    path = Path(runtime) / RESULT_FILE
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    if not isinstance(document, dict) or document.get("protocol") != LANGUAGE_RESULT_SCHEMA:
        raise LanguageBridgeError("unsupported language result document")
    body = document.get("result")
    if not isinstance(body, dict):
        raise LanguageBridgeError("language result is missing its body")
    _require_member(body.get("status"), RESULT_STATUS, "status")
    _require_member(body.get("purpose"), PURPOSES, "purpose")
    _optional_member(body.get("reject_reason"), REJECT_REASONS, "reject_reason")
    _optional_member(body.get("last_status"), RESULT_STATUS, "last_status")
    _optional_member(
        body.get("last_reject_reason"), REJECT_REASONS, "last_reject_reason"
    )
    if body.get("verify") is not None:
        _validate_verify_block(body["verify"])
    if body.get("model") is not None:
        _validate_model_block(body["model"])
    return document


# --- (c) 会话状态 ----------------------------------------------------------


def _validate_receipt(value: Any, field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise LanguageBridgeError(f"{field} must be an object")
    return {
        "request_id": _require_text(value.get("request_id"), f"{field}.request_id"),
        "action": _optional_member(value.get("action"), ACTIONS, f"{field}.action"),
        "outcome": _require_member(value.get("outcome"), OUTCOMES, f"{field}.outcome"),
        "at_sequence": _require_int(
            value.get("at_sequence"), f"{field}.at_sequence", minimum=0
        ),
    }


def _validate_pending(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise LanguageBridgeError("pending_request must be an object")
    return {
        "request_id": _require_text(
            value.get("request_id"), "pending_request.request_id"
        ),
        "action": _require_member(
            value.get("action"), ACTIONS, "pending_request.action"
        ),
        "at_sequence": _require_int(
            value.get("at_sequence"), "pending_request.at_sequence", minimum=0
        ),
    }


def _validate_retired(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise LanguageBridgeError("retired_track_ids must be a list")
    retired: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise LanguageBridgeError("each retired entry must be an object")
        retired.append(
            {
                "track_id": _require_text(item.get("track_id"), "track_id"),
                "from_frame_id": _optional_int(
                    item.get("from_frame_id"), "from_frame_id", minimum=0
                ),
                "to_frame_id": _optional_int(
                    item.get("to_frame_id"), "to_frame_id", minimum=0
                ),
                "retired_reason": _require_member(
                    item.get("retired_reason"), STATE_REASONS, "retired_reason"
                ),
            }
        )
    return retired


def _validate_designation(value: Any) -> dict[str, Any]:
    """§3.4：`designation {designation_id, frame_id_k, head_frame_id, result, resolution_level, track_id, level2}`；
    `result` 只取六值闭集，`level2.reason` 只取 §3.4.1 + AC-3 释义闭集。"""
    if not isinstance(value, Mapping):
        raise LanguageBridgeError("designation must be an object")
    level = value.get("resolution_level")
    if level is not None and level not in (1, 2):
        raise LanguageBridgeError("designation.resolution_level must be 1, 2 or null")
    level2 = value.get("level2")
    if level2 is not None:
        if not isinstance(level2, Mapping):
            raise LanguageBridgeError("designation.level2 must be an object")
        if level2.get("reason") is not None and not is_level2_reason(level2.get("reason")):
            raise LanguageBridgeError("designation.level2.reason outside the closed set")
    acquire = value.get("acquire")
    if acquire is not None and not isinstance(acquire, Mapping):
        raise LanguageBridgeError("designation.acquire must be an object")
    return {
        "designation_id": _require_int(value.get("designation_id"), "designation_id", minimum=1),
        "frame_id_k": _require_int(value.get("frame_id_k"), "frame_id_k", minimum=0),
        "head_frame_id": _optional_int(value.get("head_frame_id"), "head_frame_id", minimum=0),
        "result": _require_member(value.get("result"), DESIGNATION_RESULTS, "designation.result"),
        "resolution_level": level,
        "track_id": _optional_int(value.get("track_id"), "track_id", minimum=0),
        "level2": None if level2 is None else dict(level2),
        "candidates": [int(v) for v in value.get("candidates", [])],
        "acquire": None if acquire is None else dict(acquire),
    }


def _validate_verification(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise LanguageBridgeError("verification must be an object")
    return {
        "paired_frame_id": _optional_int(
            value.get("paired_frame_id"), "paired_frame_id", minimum=0
        ),
        "last_verdict": _optional_member(
            value.get("last_verdict"), VERIFY_VERDICTS, "last_verdict"
        ),
        "last_query_id": _optional_text(value.get("last_query_id"), "last_query_id"),
        "consecutive_alert": _require_int(
            value.get("consecutive_alert"), "consecutive_alert", minimum=0
        ),
        "alert_kind": _optional_member(
            value.get("alert_kind"), ALERT_KINDS, "alert_kind"
        ),
        "next_due_unix_s": _optional_float(
            value.get("next_due_unix_s"), "next_due_unix_s"
        ),
        "in_flight_query_id": _optional_text(
            value.get("in_flight_query_id"), "in_flight_query_id"
        ),
        "verify_epoch": _require_int(
            value.get("verify_epoch"), "verify_epoch", minimum=0
        ),
    }


def tracker_state_payload(
    *,
    session_id: str,
    state: str,
    sequence: int,
    epoch: int,
    publishing: bool,
    suspect_kind: str | None = None,
    suspect_id: str | None = None,
    tracker_raw_state: str | None = None,
    reason: str | None = None,
    track_id: str | None = None,
    segment_index: int | None = None,
    since_frame_id: int | None = None,
    since_unix_s: float | None = None,
    last_published_frame_id: int | None = None,
    last_progress_unix_s: float | None = None,
    retired_track_ids: Sequence[Mapping[str, Any]] = (),
    verification: Mapping[str, Any] | None = None,
    last_request: Mapping[str, Any] | None = None,
    pending_request: Mapping[str, Any] | None = None,
    expires_after_s: float = BRIDGE_EXPIRES_AFTER_S,
    designation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    _require_text(session_id, "session_id")
    _require_member(state, SESSION_STATES, "state")
    _require_int(sequence, "sequence", minimum=0)
    _require_int(epoch, "epoch", minimum=0)
    _require_bool(publishing, "publishing")
    _optional_member(suspect_kind, SUSPECT_KINDS, "suspect_kind")
    _optional_member(tracker_raw_state, TRACKER_RAW_STATES, "tracker_raw_state")
    _optional_member(reason, STATE_REASONS, "reason")
    if state == "SUSPECTED" and (suspect_kind is None or suspect_id is None):
        raise LanguageBridgeError("SUSPECTED requires suspect_kind and suspect_id")
    if state != "SUSPECTED" and (suspect_kind is not None or suspect_id is not None):
        raise LanguageBridgeError("suspect fields are non-null only in SUSPECTED")
    if state in {"LOST", "REINIT_REQUIRED", "TERMINAL"} and reason is None:
        raise LanguageBridgeError(f"{state} requires a reason")
    if publishing and state not in PUBLISHING_STATES:
        raise LanguageBridgeError("only an active segment or pointer may be publishing")
    envelope = packet(
        "tracker_state",
        {},
        expires_after_s,
        protocol_name=TRACKER_STATE_SCHEMA,
    )
    envelope.pop("command")
    envelope["tracker_state"] = {
        "session_id": session_id,
        "state": state,
        "suspect_kind": suspect_kind,
        "suspect_id": _optional_text(suspect_id, "suspect_id"),
        "tracker_raw_state": tracker_raw_state,
        "reason": reason,
        "track_id": _optional_text(track_id, "track_id"),
        "segment_index": _optional_int(segment_index, "segment_index", minimum=0),
        "publishing": publishing,
        "since_frame_id": _optional_int(since_frame_id, "since_frame_id", minimum=0),
        "since_unix_s": _optional_float(since_unix_s, "since_unix_s"),
        "last_published_frame_id": _optional_int(
            last_published_frame_id, "last_published_frame_id", minimum=0
        ),
        "last_progress_unix_s": _optional_float(
            last_progress_unix_s, "last_progress_unix_s"
        ),
        "retired_track_ids": _validate_retired(list(retired_track_ids)),
        "verification": _validate_verification(verification),
        "last_request": _validate_receipt(last_request, "last_request"),
        "pending_request": _validate_pending(pending_request),
        "epoch": epoch,
        "sequence": sequence,
    }
    if designation is not None:
        # P1-ENG-ACQ-001 §3.4：只在常驻会话写出（LOOP-001 段式会话的文档字段集不变）。
        envelope["tracker_state"]["designation"] = _validate_designation(designation)
    return envelope


def write_tracker_state(runtime: Path, payload: Mapping[str, Any]) -> Path:
    document = dict(payload)
    if document.get("protocol") != TRACKER_STATE_SCHEMA:
        raise LanguageBridgeError("tracker state payload must carry its schema")
    return atomic_write(TRACKER_STATE_FILE, document, runtime)


def read_tracker_state(runtime: Path) -> dict[str, Any] | None:
    path = Path(runtime) / TRACKER_STATE_FILE
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    if not isinstance(document, dict) or document.get("protocol") != TRACKER_STATE_SCHEMA:
        raise LanguageBridgeError("unsupported tracker state document")
    body = document.get("tracker_state")
    if not isinstance(body, dict):
        raise LanguageBridgeError("tracker state is missing its body")
    _require_member(body.get("state"), SESSION_STATES, "state")
    _optional_member(body.get("suspect_kind"), SUSPECT_KINDS, "suspect_kind")
    _optional_member(body.get("reason"), STATE_REASONS, "reason")
    _optional_member(
        body.get("tracker_raw_state"), TRACKER_RAW_STATES, "tracker_raw_state"
    )
    _validate_receipt(body.get("last_request"), "last_request")
    _validate_pending(body.get("pending_request"))
    _validate_verification(body.get("verification"))
    _validate_retired(body.get("retired_track_ids", []))
    if body.get("designation") is not None:
        _validate_designation(body["designation"])
    return document


# --- 两把锁（§3.2 单槽与写者锁；AC-1 修订 1 的持有者规则） ----------------


def default_is_alive(pid: int) -> bool:
    """`os.kill(pid, 0)`：`ProcessLookupError` 才算死；权限错误一律当活着。"""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as exception:  # pragma: no cover - 平台特例
        return exception.errno != errno.ESRCH
    return True


@dataclass(frozen=True)
class LockHolder:
    path: Path
    pid: int
    created_unix_s: float
    request_id: str | None = None
    session_id: str | None = None


def _read_lock(path: Path) -> LockHolder | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, ValueError, OSError):
        # 坏锁文件不可解释成「无人持有」：当成活锁，等人工处置。
        return LockHolder(path=path, pid=-1, created_unix_s=0.0)
    if not isinstance(document, dict):
        return LockHolder(path=path, pid=-1, created_unix_s=0.0)
    pid = document.get("pid")
    return LockHolder(
        path=path,
        pid=int(pid) if isinstance(pid, int) and not isinstance(pid, bool) else -1,
        created_unix_s=float(document.get("created_unix_s", 0.0) or 0.0),
        request_id=document.get("request_id"),
        session_id=document.get("session_id"),
    )


def _create_lock(path: Path, body: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(dict(body), handle, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_writer_lock(runtime: Path) -> LockHolder | None:
    return _read_lock(Path(runtime) / REQUEST_LOCK_FILE)


def acquire_writer_lock(
    runtime: Path,
    *,
    request_id: str,
    pid: int | None = None,
    now: float | None = None,
    is_alive: Callable[[int], bool] = default_is_alive,
    on_dead_lock_cleared: Callable[[LockHolder], None] | None = None,
) -> LockHolder:
    """O_EXCL 建写者锁；已被占用即 `WriterBusy`（CLI 报 `WRITER_BUSY` 且不写）。

    死写者锁（持有 pid 已不存在）在确认后清理，被清理的持有者当场交给
    `on_dead_lock_cleared` 记日志（AC-1 修订 1）——即使随后重建输给并发写者
    也已清理过，照样交出；活锁一律不夺。
    """
    path = Path(runtime) / REQUEST_LOCK_FILE
    holder = LockHolder(
        path=path,
        pid=int(pid if pid is not None else os.getpid()),
        created_unix_s=float(now if now is not None else time.time()),
        request_id=_require_text(request_id, "request_id"),
    )
    body = {
        "pid": holder.pid,
        "request_id": holder.request_id,
        "created_unix_s": holder.created_unix_s,
    }
    try:
        _create_lock(path, body)
        return holder
    except FileExistsError:
        pass
    existing = _read_lock(path)
    if existing is not None and existing.pid > 0 and not is_alive(existing.pid):
        path.unlink(missing_ok=True)
        if on_dead_lock_cleared is not None:
            on_dead_lock_cleared(existing)
        try:
            _create_lock(path, body)
        except FileExistsError as exception:
            raise WriterBusy("WRITER_BUSY") from exception
        return holder
    raise WriterBusy("WRITER_BUSY")


def release_writer_lock(
    runtime: Path, *, request_id: str, pid: int | None = None
) -> bool:
    """只有 pid/request_id 都匹配的持有者能释放（AC-1 修订 1）。"""
    path = Path(runtime) / REQUEST_LOCK_FILE
    holder = _read_lock(path)
    if holder is None:
        return False
    owner_pid = int(pid if pid is not None else os.getpid())
    if holder.pid != owner_pid or holder.request_id != request_id:
        return False
    path.unlink(missing_ok=True)
    return True


def clear_dead_writer_lock(
    runtime: Path, *, is_alive: Callable[[int], bool] = default_is_alive
) -> LockHolder | None:
    """确认 pid 已死后清理写者锁，返回被清理的持有者供日志记录。"""
    path = Path(runtime) / REQUEST_LOCK_FILE
    holder = _read_lock(path)
    if holder is None or holder.pid <= 0 or is_alive(holder.pid):
        return None
    path.unlink(missing_ok=True)
    return holder


def acquire_session_lock(
    runtime: Path,
    *,
    session_id: str,
    pid: int | None = None,
    now: float | None = None,
    is_alive: Callable[[int], bool] = default_is_alive,
) -> tuple[LockHolder, LockHolder | None]:
    """取会话锁；返回（本次持有者, 被替换的死锁）。活锁即 `SessionSlotBusy`。"""
    path = Path(runtime) / SESSION_LOCK_FILE
    holder = LockHolder(
        path=path,
        pid=int(pid if pid is not None else os.getpid()),
        created_unix_s=float(now if now is not None else time.time()),
        session_id=_require_text(session_id, "session_id"),
    )
    body = {
        "pid": holder.pid,
        "session_id": holder.session_id,
        "created_unix_s": holder.created_unix_s,
    }
    try:
        _create_lock(path, body)
        return holder, None
    except FileExistsError:
        pass
    existing = _read_lock(path)
    if existing is not None and existing.pid > 0 and not is_alive(existing.pid):
        path.unlink(missing_ok=True)
        try:
            _create_lock(path, body)
        except FileExistsError as exception:
            raise SessionSlotBusy("SESSION_SLOT_BUSY") from exception
        return holder, existing
    raise SessionSlotBusy("SESSION_SLOT_BUSY")


def release_session_lock(
    runtime: Path, *, session_id: str, pid: int | None = None
) -> bool:
    path = Path(runtime) / SESSION_LOCK_FILE
    holder = _read_lock(path)
    if holder is None:
        return False
    owner_pid = int(pid if pid is not None else os.getpid())
    if holder.pid != owner_pid or holder.session_id != session_id:
        return False
    path.unlink(missing_ok=True)
    return True
