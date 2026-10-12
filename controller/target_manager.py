"""P1-ENG-CAPTURE-001 C4/C5/C6/C8：目标管理器（纯 Python；无 ultralytics、无真值）。

一个 reducer 管 TaskSpec、BindingRecord、连续性与观测状态、按帧计的截止、修复证据缓冲、授权函数与事件日志
（同名提案 §3.2–§3.5，终局裁定 AR1-2/AR1-3 的 binding clarifications 照字面）。

- 捕获模式（`run --language off`）：会话每帧把常驻历史喂给 `on_frame`，按 §3.3 同帧顺序 ①–⑤ 处理；⑤ 只对本批
  最新帧求值并产生效果（B7）。连续性只由 `transition` 写；授权只由 `derive_authorization` 定（§3.4 八行、AR1-2 可达域）。
- 兼容模式（`run --language on`）：只承担单写者（`commit_binding`/`release_binding` 是会话内唯一设/清指针入口）与
  日志；连续性修复、预测 look_at、新报告均关闭，不调用授权函数。
- 落盘 reducer 输入（`tm_inputs.jsonl`，§3.8 + AR1-2）：每行带自身 sha256；`replay_tm_inputs` 只读落盘输入与配置
  文件重放，事件序列逐条相同（AC-15）；篡改或缺引用即拒。

真值隔离（AC-16）：本模块只读常驻历史（检测、关联、KF 快照、平台位姿）与参数文件；不导入 `tools.*`、不读评分产物。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .pose_gmc import jacobian, map_point, pose_homography, rotation_matrix
from .resident_core import (
    KF_POSTERIOR,
    KF_PRIOR,
    LOST,
    TRACKED,
    UNCONFIRMED,
    FullKfState,
    HistoryEntry,
    KfSnapshot,
    RawDetection,
    TrackRow,
    make_kf_snapshot,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CAPTURE_CONFIG = PROJECT_ROOT / "config" / "p1-eng-capture-001.json"
CONFIG_SCHEMA = "p1-eng-capture-001/v1"
INPUTS_FILE = "tm_inputs.jsonl"
INPUTS_SCHEMA = "p1-eng-capture-001-tm-inputs/v1"
#: P1-ENG-FASTFIX-001 AC-13（R2-2 承接）：捕获会话落盘输入加行间链式引用（每行 `prev_line_sha256` = 上一行的
#: `line_sha256`）与帧连续性；v1（CAPTURE 旧工件、兼容模式内存输入）按原规则重放，不改判。
INPUTS_SCHEMA_V2 = "p1-eng-fastfix-001-tm-inputs/v2"
INPUTS_SCHEMAS: tuple[str, ...] = (INPUTS_SCHEMA, INPUTS_SCHEMA_V2)
DEFAULT_FASTFIX_CONFIG = PROJECT_ROOT / "config" / "p1-eng-fastfix-001.json"
FASTFIX_SCHEMA = "p1-eng-fastfix-001/v1"

# --- 闭集 -------------------------------------------------------------------

MODES: tuple[str, ...] = ("capture", "compat")
CAPTURE = "capture"
COMPAT = "compat"

PHASES: tuple[str, ...] = ("ACQUIRING", "TRACKING", "CANCELED")
#: P1-ENG-FASTFIX-001 §3.3：`REBUILD_REACQUIRE` 只在闭集末尾追加（既有成员与位次不变）。
RELATIONS: tuple[str, ...] = ("INITIAL", "CONTINUITY_REPAIR", "USER_RESELECT", "REBUILD_REACQUIRE")
#: P1-ENG-FASTFIX-001 §3.3：`reacquire`（时序升级重建后的自动重捕）只在闭集末尾追加。
ORIGINS: tuple[str, ...] = ("click", "repair", "lang_confirm", "lang_acquire", "reacquire")
#: 每种模式允许的提交来源（§3.5 路径表）；FASTFIX §3.3 只给捕获模式加入 `reacquire`（兼容模式不变）。
MODE_ORIGINS: dict[str, frozenset[str]] = {
    CAPTURE: frozenset({"click", "repair", "reacquire"}),
    COMPAT: frozenset({"lang_confirm", "lang_acquire"}),
}

BINDING_MODES: tuple[str, ...] = ("INSTANCE", "DESCRIPTION")
ACTIVATIONS: tuple[str, ...] = ("NOW", "WAIT", "REARM")
ON_AMBIGUITY: tuple[str, ...] = ("ASK",)
ON_LOSS: tuple[str, ...] = ("ASK",)

OBSERVED = "OBSERVED"
PREDICTED = "PREDICTED"
STALE = "STALE"
OBSERVATION_STATUSES: tuple[str, ...] = (OBSERVED, PREDICTED, STALE)

SUPPORTED = "SUPPORTED"
TENTATIVE = "TENTATIVE"
DISPUTED = "DISPUTED"
BROKEN = "BROKEN"
CONTINUITY_STATUSES: tuple[str, ...] = (SUPPORTED, TENTATIVE, DISPUTED, BROKEN)
TERMINAL_CONTINUITY = frozenset({DISPUTED, BROKEN})

UNKNOWN = "UNKNOWN"
CONTRADICTED = "CONTRADICTED"

#: `transition` 的事件闭集与合法边（§3.3）。DISPUTED/BROKEN 是当前 episode 的终点，不互转、不恢复。
BIND = "bind"
MISS = "miss"
REGAIN = "regain"
REPAIR = "repair"
DISPUTE = "dispute"
EXPIRE = "expire"
TRANSITIONS: dict[tuple[str | None, str], str] = {
    (None, BIND): SUPPORTED,
    (SUPPORTED, MISS): TENTATIVE,
    (TENTATIVE, MISS): TENTATIVE,
    (SUPPORTED, REGAIN): SUPPORTED,
    (TENTATIVE, REGAIN): SUPPORTED,
    (TENTATIVE, REPAIR): SUPPORTED,
    (SUPPORTED, DISPUTE): DISPUTED,
    (TENTATIVE, DISPUTE): DISPUTED,
    (SUPPORTED, EXPIRE): BROKEN,
    (TENTATIVE, EXPIRE): BROKEN,
}

# 授权（§3.4）
FOLLOW = "FOLLOW"
HOLD = "HOLD"
GIMBAL_OBSERVED = "observed"
GIMBAL_PREDICTED = "predicted"
GIMBAL_NONE = "none"
BODY_RANK = {HOLD: 0, FOLLOW: 1}
GIMBAL_RANK = {GIMBAL_NONE: 0, GIMBAL_PREDICTED: 1, GIMBAL_OBSERVED: 2}
TASK_AXIS: tuple[str, ...] = ("none", "ACTIVE", "CANCELED", "stopped")
WATCHDOG_AXIS: tuple[str, ...] = ("fresh", "stale")
SEMANTIC_AXIS: tuple[str, ...] = (UNKNOWN, CONTRADICTED)
GEOMETRY_AXIS: tuple[str, ...] = ("valid", "invalid")
OBSERVATION_AXIS: tuple[str, ...] = (OBSERVED, PREDICTED)
COVARIANCE_AXIS: tuple[str, ...] = ("within", "exceeds", "kf_invalid")
AGE_BANDS: tuple[str, ...] = ("0", "pred", "gap", "expired")
#: 授权原因码闭集（`authorization` 事件逐帧记录）。
AUTH_REASONS: tuple[str, ...] = (
    "NO_TASK",
    "STALE",
    "CONTINUITY_TERMINAL",
    "SEMANTIC_CONTRADICTED",
    "GEO_REJECT",
    "OBSERVED_SUPPORTED",
    "PREDICTION_WINDOW",
    "HOLD_DEFAULT",
    "authorization_input_inconsistent",
    "CONTROL_LIMITED",
)

#: 会话 state/reason 投影（§3.6）里的新原因（语言桥 `STATE_REASONS` 末尾追加同名）。
REASON_PREDICTING = "predicting"
REASON_NO_NEW_OBSERVATION = "no_new_observation"
REASON_REPAIRED = "continuity_repaired"
REASON_BROKEN = "continuity_broken"
REASON_DISPUTED = "continuity_disputed"
REASON_SUPERSEDED = "superseded_by_click"
REASON_ROLLBACK_FAILED = "binding_rollback_failed"
#: P1-ENG-FASTFIX-001 §3.2/§3.3（语言桥 `STATE_REASONS` 末尾追加同名）。
REASON_PUBLISH_DEGRADED = "publish_degraded"
REASON_REACQUIRING = "reacquiring"
REASON_REACQUIRE_FAILED = "reacquire_failed"
REASON_REACQUIRE_AMBIGUOUS = "reacquire_ambiguous"
REASON_REBUILD_REACQUIRED = "rebuild_reacquired"

#: P1-ENG-FASTFIX-001 §3.3：合成先验的阶段常量（不并入库 `KF_PHASES` 闭集、不冒充 `KF_PRIOR`）。
REACQ_PRIOR = "reacq_prior"
#: 提示跳过原因闭集（`reacquire_skipped.cause`）。
REACQUIRE_SKIP_CAUSES: tuple[str, ...] = (
    "not_timing_escalation",
    "auto_reacquire_off",
    "no_binding",
    "task_stopped",
    "continuity_terminal",
    "no_qualified_observation",
    "hint_stale",
    "hint_invalid",
)

# 点击解析结果（与 `resident_core` 六值闭集同名的三值 + 绑定）。
NO_TRACK_AT_K = "NO_TRACK_AT_K"
AMBIGUOUS = "AMBIGUOUS"
FRAME_NOT_IN_HISTORY = "FRAME_NOT_IN_HISTORY"


class CaptureConfigInvalid(ValueError):
    """参数文件不合 §3.3 结构约束或类别闭集：拒绝加载（AC-6）。"""


class TaskSpecInvalid(ValueError):
    """不合法的 TaskSpec 构造（AC-4；v3 §14 #11/#12）。"""


class TransitionInvalid(ValueError):
    """`transition` 遇到闭集外的边（程序错误，不静默吸收）。"""


class ReplayRejected(ValueError):
    """落盘输入行 sha 不符、缺引用或配置不符：拒绝重放（AC-15）。"""


class ReplayInputIncomplete(ReplayRejected):
    """重放中某次端口调用在落盘输入里没有对应的、同种类的下一条记录（删行/截断/乱序），或该输入行的端口记录未被
    恰好用完（多出/重复）：输入不完整，拒绝重放（R1-1），绝不默认成功或退回本地模型。"""


# --- 参数（§3.7；类别按 v3.1 B9） ------------------------------------------------

PARAM_CATEGORIES: tuple[str, ...] = ("known_constraint", "design_budget", "to_calibrate", "vendor", "formula", "config_axis")
REQUIRED_PARAMS: dict[str, str] = {
    "delta_t_s": "known_constraint",
    "t_report_frames": "design_budget",
    "n_adopt_frames": "design_budget",
    "rho_click": "design_budget",
    "t_pred_frames": "to_calibrate",
    "t_repair_frames": "to_calibrate",
    "g_motion": "to_calibrate",
    "g_size": "to_calibrate",
    "r_gate_max_px": "to_calibrate",
    "m_nis": "to_calibrate",
    "r_jump_diag": "to_calibrate",
    "sigma_p": "vendor",
    "h_c_m": "known_constraint",
    "auto_repair": "config_axis",
}


@dataclass(frozen=True)
class CaptureParams:
    delta_t_s: float = 0.2
    t_report: int = 3
    n_adopt: int = 2
    rho_click: float = 1.5
    t_pred: int = 4
    t_repair: int = 5
    g_motion: float = 9.21
    g_size: float = 0.5
    r_gate_max_px: float = 80.0
    m_nis: float = 4.6
    r_jump_diag: float = 0.5
    sigma_p: float = 1.0 / 20.0
    h_c_m: float = 0.775
    auto_repair: bool = True

    def __post_init__(self) -> None:
        validate_structure(self)

    def as_record(self) -> dict[str, Any]:
        return {
            "delta_t_s": self.delta_t_s,
            "t_report": self.t_report,
            "n_adopt": self.n_adopt,
            "rho_click": self.rho_click,
            "t_pred": self.t_pred,
            "t_repair": self.t_repair,
            "g_motion": self.g_motion,
            "g_size": self.g_size,
            "r_gate_max_px": self.r_gate_max_px,
            "m_nis": self.m_nis,
            "r_jump_diag": self.r_jump_diag,
            "sigma_p": self.sigma_p,
            "h_c_m": self.h_c_m,
            "auto_repair": self.auto_repair,
        }


def _int_param(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CaptureConfigInvalid(f"{label} must be an integer")
    return value


def _float_param(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise CaptureConfigInvalid(f"{label} must be a finite number")
    return float(value)


def validate_structure(params: CaptureParams) -> None:
    """§3.3 结构约束（AR1-1）：N_adopt ≥ 2；1 ≤ T_report ≤ T_repair−1；1 ≤ T_pred ≤ T_repair−1；
    1 + N_adopt + 1 ≤ T_repair − 1；另 ρ_click > 1、门值为正。不满足 → 拒绝启动。"""
    n_adopt = _int_param(params.n_adopt, "n_adopt")
    t_report = _int_param(params.t_report, "t_report")
    t_pred = _int_param(params.t_pred, "t_pred")
    t_repair = _int_param(params.t_repair, "t_repair")
    if n_adopt < 2:
        raise CaptureConfigInvalid("N_adopt must be ≥ 2")
    if not 1 <= t_report <= t_repair - 1:
        raise CaptureConfigInvalid("T_report must satisfy 1 ≤ T_report ≤ T_repair − 1")
    if not 1 <= t_pred <= t_repair - 1:
        raise CaptureConfigInvalid("T_pred must satisfy 1 ≤ T_pred ≤ T_repair − 1")
    if 1 + n_adopt + 1 > t_repair - 1:
        raise CaptureConfigInvalid("1 + N_adopt + 1 ≤ T_repair − 1 is violated")
    if _float_param(params.rho_click, "rho_click") <= 1.0:
        raise CaptureConfigInvalid("rho_click must be > 1")
    for label in ("g_motion", "g_size", "r_gate_max_px", "m_nis", "r_jump_diag", "sigma_p", "delta_t_s"):
        if _float_param(getattr(params, label), label) <= 0.0:
            raise CaptureConfigInvalid(f"{label} must be positive")
    _float_param(params.h_c_m, "h_c_m")
    if not isinstance(params.auto_repair, bool):
        raise CaptureConfigInvalid("auto_repair must be a boolean")


def params_from_document(document: Mapping[str, Any]) -> CaptureParams:
    if not isinstance(document, Mapping) or document.get("schema_version") != CONFIG_SCHEMA:
        raise CaptureConfigInvalid(f"capture config schema must be {CONFIG_SCHEMA}")
    values = document.get("params")
    if not isinstance(values, Mapping):
        raise CaptureConfigInvalid("capture config needs a params object")
    if set(values) != set(REQUIRED_PARAMS):
        raise CaptureConfigInvalid(f"capture config params must be exactly {sorted(REQUIRED_PARAMS)}")
    plain: dict[str, Any] = {}
    for name, category in REQUIRED_PARAMS.items():
        entry = values[name]
        if not isinstance(entry, Mapping) or "value" not in entry:
            raise CaptureConfigInvalid(f"param {name} must be an object with a value")
        if entry.get("category") not in PARAM_CATEGORIES or entry.get("category") != category:
            raise CaptureConfigInvalid(f"param {name} category must be {category!r}")
        plain[name] = entry["value"]
    return CaptureParams(
        delta_t_s=_float_param(plain["delta_t_s"], "delta_t_s"),
        t_report=_int_param(plain["t_report_frames"], "t_report_frames"),
        n_adopt=_int_param(plain["n_adopt_frames"], "n_adopt_frames"),
        rho_click=_float_param(plain["rho_click"], "rho_click"),
        t_pred=_int_param(plain["t_pred_frames"], "t_pred_frames"),
        t_repair=_int_param(plain["t_repair_frames"], "t_repair_frames"),
        g_motion=_float_param(plain["g_motion"], "g_motion"),
        g_size=_float_param(plain["g_size"], "g_size"),
        r_gate_max_px=_float_param(plain["r_gate_max_px"], "r_gate_max_px"),
        m_nis=_float_param(plain["m_nis"], "m_nis"),
        r_jump_diag=_float_param(plain["r_jump_diag"], "r_jump_diag"),
        sigma_p=_float_param(plain["sigma_p"], "sigma_p"),
        h_c_m=_float_param(plain["h_c_m"], "h_c_m"),
        auto_repair=plain["auto_repair"] if isinstance(plain["auto_repair"], bool) else _bool_error(),
    )


def _bool_error() -> bool:
    raise CaptureConfigInvalid("auto_repair must be a boolean")


def load_capture_config(path: Path = DEFAULT_CAPTURE_CONFIG) -> tuple[CaptureParams, str, str]:
    """→ (参数, 配置文件字节 sha256, 配置原文)。不合即 `CaptureConfigInvalid`（拒绝启动）。"""
    data = Path(path).read_bytes()
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exception:
        raise CaptureConfigInvalid(f"capture config is not JSON: {exception}") from exception
    return params_from_document(document), hashlib.sha256(data).hexdigest(), data.decode("utf-8")


# --- P1-ENG-FASTFIX-001 参数（§3.7；G3） ---------------------------------------------------

#: 类别闭集（§3.7）：合同继承（LOOP-001 AC-10 修订 1 移植限值）、设计预算（占位）、配置轴。
FASTFIX_CATEGORIES: tuple[str, ...] = ("contract_inherited", "design_budget", "config_axis")
FASTFIX_PARAMS: dict[str, str] = {
    "t_pub_s": "contract_inherited",
    "k_pub": "contract_inherited",
    "n_drop_frames": "design_budget",
    "t_reacq_frames": "design_budget",
    "auto_reacquire": "config_axis",
}
#: §3.4：门值只允许这两组（用户签）；首候选 = 现行常数 0.4 s / 2 帧。
GATE_VALUE_PAIRS: tuple[tuple[float, int], ...] = ((0.4, 2), (0.6, 3))


class FastfixConfigInvalid(ValueError):
    """`config/p1-eng-fastfix-001.json` 不合结构约束（§3.7）：拒绝启动。"""


@dataclass(frozen=True)
class FastfixParams:
    t_pub_s: float = 0.4
    k_pub: int = 2
    n_drop: int = 3
    t_reacq: int = 10
    auto_reacquire: bool = True

    def as_record(self) -> dict[str, Any]:
        return {
            "t_pub_s": self.t_pub_s,
            "k_pub": self.k_pub,
            "n_drop": self.n_drop,
            "t_reacq": self.t_reacq,
            "auto_reacquire": self.auto_reacquire,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "FastfixParams":
        return cls(float(record["t_pub_s"]), int(record["k_pub"]), int(record["n_drop"]), int(record["t_reacq"]),
                   bool(record["auto_reacquire"]))


def validate_fastfix(params: FastfixParams, capture: CaptureParams, hz: float) -> None:
    """§3.7 结构约束：`t_pub_s = k_pub/hz`、`k_pub ≥ 1`、门值 ∈ {0.4/2, 0.6/3}、`1 ≤ N_drop ≤ T_report`、
    `T_reacq ≥ N_adopt + 1`、`auto_reacquire` ∈ {on, off}。任一不满足 → `FastfixConfigInvalid`（拒绝启动）。"""
    if isinstance(params.k_pub, bool) or not isinstance(params.k_pub, int) or params.k_pub < 1:
        raise FastfixConfigInvalid("k_pub must be an integer ≥ 1")
    if isinstance(params.t_pub_s, bool) or not isinstance(params.t_pub_s, (int, float)) or not math.isfinite(float(params.t_pub_s)):
        raise FastfixConfigInvalid("t_pub_s must be a finite number")
    if not (isinstance(hz, (int, float)) and math.isfinite(float(hz)) and float(hz) > 0.0):
        raise FastfixConfigInvalid("scenario hz must be positive")
    if abs(float(params.t_pub_s) - params.k_pub / float(hz)) > 1e-9:
        raise FastfixConfigInvalid(f"t_pub_s {params.t_pub_s} must equal k_pub/hz = {params.k_pub / float(hz)}")
    if not any(abs(float(params.t_pub_s) - t) <= 1e-9 and params.k_pub == k for t, k in GATE_VALUE_PAIRS):
        raise FastfixConfigInvalid(f"(t_pub_s, k_pub) must be one of {GATE_VALUE_PAIRS}")
    for label in ("n_drop", "t_reacq"):
        value = getattr(params, label)
        if isinstance(value, bool) or not isinstance(value, int):
            raise FastfixConfigInvalid(f"{label} must be an integer")
    if not 1 <= params.n_drop <= capture.t_report:
        raise FastfixConfigInvalid("N_drop must satisfy 1 ≤ N_drop ≤ T_report")
    if params.t_reacq < capture.n_adopt + 1:
        raise FastfixConfigInvalid("T_reacq must satisfy T_reacq ≥ N_adopt + 1")
    if not isinstance(params.auto_reacquire, bool):
        raise FastfixConfigInvalid("auto_reacquire must be a boolean")


def fastfix_params_from_document(document: Mapping[str, Any]) -> FastfixParams:
    if not isinstance(document, Mapping) or document.get("schema_version") != FASTFIX_SCHEMA:
        raise FastfixConfigInvalid(f"fastfix config schema must be {FASTFIX_SCHEMA}")
    values = document.get("params")
    if not isinstance(values, Mapping):
        raise FastfixConfigInvalid("fastfix config needs a params object")
    if set(values) != set(FASTFIX_PARAMS):
        # 无 `rho_reacq`（D2 接受裁定批准删除）；多一项或少一项都拒绝。
        raise FastfixConfigInvalid(f"fastfix config params must be exactly {sorted(FASTFIX_PARAMS)}")
    plain: dict[str, Any] = {}
    for name, category in FASTFIX_PARAMS.items():
        entry = values[name]
        if not isinstance(entry, Mapping) or "value" not in entry:
            raise FastfixConfigInvalid(f"param {name} must be an object with a value")
        if entry.get("category") != category:
            raise FastfixConfigInvalid(f"param {name} category must be {category!r}")
        plain[name] = entry["value"]
    auto = plain["auto_reacquire"]
    if auto not in ("on", "off"):
        raise FastfixConfigInvalid("auto_reacquire must be 'on' or 'off'")
    return FastfixParams(
        t_pub_s=plain["t_pub_s"],
        k_pub=plain["k_pub"],
        n_drop=plain["n_drop_frames"],
        t_reacq=plain["t_reacq_frames"],
        auto_reacquire=auto == "on",
    )


def load_fastfix_config(path: Path, capture: CaptureParams, hz: float) -> tuple[FastfixParams, str, str]:
    """→ (参数, 配置文件字节 sha256, 原文)。加载即校验结构约束，不满足 → `FastfixConfigInvalid`（拒绝启动）。"""
    data = Path(path).read_bytes()
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exception:
        raise FastfixConfigInvalid(f"fastfix config is not JSON: {exception}") from exception
    params = fastfix_params_from_document(document)
    validate_fastfix(params, capture, hz)
    return params, hashlib.sha256(data).hexdigest(), data.decode("utf-8")


# --- 记录（§3.2） -----------------------------------------------------------------

_COMPAT_PATH = object()


@dataclass(frozen=True)
class ClickSelector:
    x_px: float
    y_px: float
    frame_id: int
    image_sha256: str

    def as_record(self) -> dict[str, Any]:
        return {"kind": "Click", "x_px": self.x_px, "y_px": self.y_px, "frame_id": self.frame_id, "image_sha256": self.image_sha256}


@dataclass(frozen=True)
class LanguageCompatSelector:
    designation_id: int
    box_k: tuple[float, ...]
    k: int

    def as_record(self) -> dict[str, Any]:
        return {"kind": "LanguageCompat", "designation_id": self.designation_id, "box_k": list(self.box_k), "k": self.k}


@dataclass(frozen=True)
class TaskSpec:
    """不可变任务说明（AC-4）。Click 只能 INSTANCE+NOW+ASK；LanguageCompat 只能经兼容路径构造；
    INSTANCE+REARM 与无谓词 WAIT 构造即拒。`intent_revision` 由管理器在被接受的提交时给出。"""

    selector: ClickSelector | LanguageCompatSelector
    binding_mode: str
    activation: str
    on_ambiguity: str
    on_loss: str
    intent_revision: int
    predicate: str | None = None
    _path: Any = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.binding_mode not in BINDING_MODES:
            raise TaskSpecInvalid(f"binding_mode {self.binding_mode!r} outside {BINDING_MODES}")
        if self.activation not in ACTIVATIONS:
            raise TaskSpecInvalid(f"activation {self.activation!r} outside {ACTIVATIONS}")
        if self.on_ambiguity not in ON_AMBIGUITY or self.on_loss not in ON_LOSS:
            raise TaskSpecInvalid("on_ambiguity/on_loss must be ASK")
        if self.binding_mode == "INSTANCE" and self.activation == "REARM":
            raise TaskSpecInvalid("INSTANCE + REARM is not a legal TaskSpec (v3 §14 #11)")
        if self.activation == "WAIT" and not self.predicate:
            raise TaskSpecInvalid("WAIT without a predicate is not a legal TaskSpec (v3 §14 #12)")
        if isinstance(self.selector, ClickSelector):
            if (self.binding_mode, self.activation, self.on_ambiguity) != ("INSTANCE", "NOW", "ASK"):
                raise TaskSpecInvalid("a Click TaskSpec must be INSTANCE + NOW + ASK")
        elif isinstance(self.selector, LanguageCompatSelector):
            if self._path is not _COMPAT_PATH:
                raise TaskSpecInvalid("a LanguageCompat TaskSpec is only built by the compat language path")
            if (self.binding_mode, self.activation, self.on_ambiguity) != ("INSTANCE", "NOW", "ASK"):
                raise TaskSpecInvalid("a LanguageCompat TaskSpec must be INSTANCE + NOW + ASK")
        else:
            raise TaskSpecInvalid("selector must be Click or LanguageCompat")
        if isinstance(self.intent_revision, bool) or not isinstance(self.intent_revision, int) or self.intent_revision < 1:
            raise TaskSpecInvalid("intent_revision must be a positive integer")

    @classmethod
    def click(cls, selector: ClickSelector, intent_revision: int) -> "TaskSpec":
        return cls(selector, "INSTANCE", "NOW", "ASK", "ASK", intent_revision)

    @classmethod
    def _language_compat(cls, selector: LanguageCompatSelector, intent_revision: int) -> "TaskSpec":
        return cls(selector, "INSTANCE", "NOW", "ASK", "ASK", intent_revision, None, _COMPAT_PATH)

    def as_record(self) -> dict[str, Any]:
        return {
            "selector": self.selector.as_record(),
            "binding_mode": self.binding_mode,
            "activation": self.activation,
            "on_ambiguity": self.on_ambiguity,
            "on_loss": self.on_loss,
            "intent_revision": self.intent_revision,
            "predicate": self.predicate,
        }


@dataclass(frozen=True)
class TaskRuntime:
    phase: str
    mode: str
    episode_id: int | None
    #: 以 frame_id 计的截止（预测窗口末帧、修复/到期帧）。
    deadlines: Mapping[str, int | None] = field(default_factory=dict)

    def as_record(self) -> dict[str, Any]:
        return {"phase": self.phase, "mode": self.mode, "episode_id": self.episode_id, "deadlines": dict(self.deadlines)}


@dataclass(frozen=True)
class BindingRecord:
    target_episode_id: int
    track_key: int
    association_revision: int
    relation: str
    origin: str
    bound_frame_id: int | None
    evidence_refs: Mapping[str, Any] = field(default_factory=dict)

    def as_record(self) -> dict[str, Any]:
        return {
            "target_episode_id": self.target_episode_id,
            "track_key": self.track_key,
            "association_revision": self.association_revision,
            "relation": self.relation,
            "origin": self.origin,
            "bound_frame_id": self.bound_frame_id,
            "evidence_refs": dict(self.evidence_refs),
        }


@dataclass(frozen=True)
class TargetBelief:
    """本轮子集（§3.2）。`continuity_status` 只由 `transition` 写（AC-5 静态检查）。"""

    t0: int
    last_box_px: tuple[float, float, float, float] | None
    last_track_key: int
    observation_status: str = OBSERVED
    continuity_status: str | None = None
    semantic_status: str = UNKNOWN
    predicted: Mapping[str, Any] | None = None
    reported_no_new_observation: bool = False

    def age(self, frame_id: int) -> int:
        return int(frame_id) - int(self.t0)

    def as_record(self) -> dict[str, Any]:
        return {
            "t0": self.t0,
            "last_box_px": None if self.last_box_px is None else list(self.last_box_px),
            "last_track_key": self.last_track_key,
            "observation_status": self.observation_status,
            "continuity_status": self.continuity_status,
            "semantic_status": self.semantic_status,
            "predicted": None if self.predicted is None else dict(self.predicted),
        }


def transition(belief: TargetBelief, event: str) -> TargetBelief:
    """**唯一**写 `continuity_status` 的函数（§3.3 合法边）；闭集外的边抛 `TransitionInvalid`。"""
    key = (belief.continuity_status, event)
    if key not in TRANSITIONS:
        raise TransitionInvalid(f"illegal continuity edge {belief.continuity_status!r} --{event}-->")
    return replace(belief, continuity_status=TRANSITIONS[key])


@dataclass
class RepairBuffer:
    """有界修复证据缓冲：键 → 连续证据帧（frame_id、状态、NIS）。中间缺帧即清零重计。"""

    streaks: dict[int, list[dict[str, Any]]] = field(default_factory=dict)

    def clear(self) -> None:
        self.streaks.clear()

    def as_record(self) -> dict[str, Any]:
        return {str(key): [dict(item) for item in value] for key, value in sorted(self.streaks.items())}


# --- 门与几何（§3.1/§3.3/C6） ----------------------------------------------------------


def gate_covariance(prior: KfSnapshot, sigma_p: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """S = P_pos + diag((w/20)², (h/20)²)（库 `project()` 位置块；厂商常数 σ_p = 1/20，未标定）。"""
    (a, b), (c, d) = prior.pos_cov_px2
    w, h = prior.xywh_px[2], prior.xywh_px[3]
    return ((a + (sigma_p * w) ** 2, b), (c, d + (sigma_p * h) ** 2))


def _inverse2(matrix: tuple[tuple[float, float], tuple[float, float]]) -> tuple[tuple[float, float], tuple[float, float]] | None:
    (a, b), (c, d) = matrix
    det = a * d - b * c
    if not math.isfinite(det) or det <= 1e-12:
        return None
    return ((d / det, -b / det), (-c / det, a / det))


def max_eigenvalue(matrix: tuple[tuple[float, float], tuple[float, float]]) -> float:
    (a, b), (c, d) = matrix
    half_trace = (a + d) / 2.0
    det = a * d - b * c
    return half_trace + math.sqrt(max(half_trace * half_trace - det, 0.0))


def gate_radius(prior: KfSnapshot, params: CaptureParams) -> float:
    return math.sqrt(params.g_motion * max_eigenvalue(gate_covariance(prior, params.sigma_p)))


@dataclass(frozen=True)
class GateResult:
    passed: bool
    reason: str | None
    nis: float | None
    size_log_ratio: float | None
    radius_px: float | None

    def as_record(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "reason": self.reason,
            "nis": None if self.nis is None else round(self.nis, 6),
            "size_log_ratio": None if self.size_log_ratio is None else round(self.size_log_ratio, 6),
            "radius_px": None if self.radius_px is None else round(self.radius_px, 6),
        }


def motion_size_gate(prior: KfSnapshot | None, detection: RawDetection | None, params: CaptureParams) -> GateResult:
    """运动门（NIS ≤ g_motion 且 √(g_motion·λmax(S)) ≤ r_gate_max）与尺寸门（|log(√(w′h′)/√(wh))| ≤ g_size）。

    `prior` 必须是**原绑定键同帧 prior**（AR1-2）；缺失/无效/S 不可逆 → 不过（fail-closed）。"""
    if prior is None:
        return GateResult(False, "prior_missing", None, None, None)
    if not prior.valid:
        return GateResult(False, f"prior_invalid:{prior.invalid_reason}", None, None, None)
    if prior.phase != KF_PRIOR:
        return GateResult(False, "prior_wrong_phase", None, None, None)
    if detection is None:
        return GateResult(False, "no_detection", None, None, None)
    return _motion_size_core(prior, detection, params)


def reacquire_gate(prior: KfSnapshot | None, detection: RawDetection | None, params: CaptureParams) -> GateResult:
    """P1-ENG-FASTFIX-001 §3.3：重捕候选门。判据、常数与 `motion_size_gate` 逐式相同（同一 `_motion_size_core`），
    只把阶段校验换成合成先验 `REACQ_PRIOR`；不接受库 prior/posterior（不以候选自身状态自证）。"""
    if prior is None:
        return GateResult(False, "prior_missing", None, None, None)
    if not prior.valid:
        return GateResult(False, f"prior_invalid:{prior.invalid_reason}", None, None, None)
    if prior.phase != REACQ_PRIOR:
        return GateResult(False, "prior_wrong_phase", None, None, None)
    if detection is None:
        return GateResult(False, "no_detection", None, None, None)
    return _motion_size_core(prior, detection, params)


def _motion_size_core(prior: KfSnapshot, detection: RawDetection, params: CaptureParams) -> GateResult:
    """运动门与尺寸门的公共式（`motion_size_gate` 与 `reacquire_gate` 共用；阶段与存在性校验由调用方完成）。"""
    s = gate_covariance(prior, params.sigma_p)
    inverse = _inverse2(s)
    if inverse is None:
        return GateResult(False, "gate_covariance_singular", None, None, None)
    radius = math.sqrt(params.g_motion * max_eigenvalue(s))
    zx, zy = detection.center_px
    dx, dy = zx - prior.xywh_px[0], zy - prior.xywh_px[1]
    nis = dx * (inverse[0][0] * dx + inverse[0][1] * dy) + dy * (inverse[1][0] * dx + inverse[1][1] * dy)
    w_det = detection.box_px[2] - detection.box_px[0]
    h_det = detection.box_px[3] - detection.box_px[1]
    if w_det <= 0.0 or h_det <= 0.0:
        return GateResult(False, "detection_degenerate", nis, None, radius)
    size = abs(math.log(math.sqrt(w_det * h_det) / math.sqrt(prior.xywh_px[2] * prior.xywh_px[3])))
    if radius > params.r_gate_max_px:
        return GateResult(False, "gate_radius_exceeds", nis, size, radius)
    if not math.isfinite(nis) or nis > params.g_motion:
        return GateResult(False, "motion_gate", nis, size, radius)
    if size > params.g_size:
        return GateResult(False, "size_gate", nis, size, radius)
    return GateResult(True, None, nis, size, radius)


def same_frame_prior(entry: HistoryEntry, track_key: int, params: CaptureParams) -> tuple[KfSnapshot | None, str | None]:
    """AR1-2 修订 1：原绑定键**同帧** prior —— 按 (sensor_frame_id, library_frame_id, track_key, phase) 对齐，
    phase 必为 prior、快照有效且 S 可逆；任一不满足 → (None, 原因)，消费方 fail-closed（观测不接受、修复不提交、
    云台不发、机身 HOLD）。不用 posterior、上帧快照或候选自己的 prior 替代（C1返工 C1-1）。"""
    if not entry.priors_available:
        return None, "prior_unavailable"
    snapshot = entry.prior(track_key)
    if snapshot is None:
        return None, "prior_missing"
    reason = _alignment_problem(snapshot, entry, track_key, KF_PRIOR, "prior")
    if reason is not None:
        return None, reason
    if _inverse2(gate_covariance(snapshot, params.sigma_p)) is None:
        return None, "prior_gate_covariance_singular"
    return snapshot, None


def same_frame_post(entry: HistoryEntry, track_key: int, phase: str = KF_POSTERIOR) -> tuple[KfSnapshot | None, str | None]:
    """AR1-2：接受观测/初始化新实例所用的同帧 post 快照（对齐键同上，phase 须为 `phase`、有效）；否则 (None, 原因)。"""
    snapshot = entry.post(track_key)
    if snapshot is None:
        return None, "post_missing"
    reason = _alignment_problem(snapshot, entry, track_key, phase, "post")
    return (None, reason) if reason is not None else (snapshot, None)


def _alignment_problem(snapshot: KfSnapshot, entry: HistoryEntry, track_key: int, phase: str, label: str) -> str | None:
    if int(snapshot.track_key) != int(track_key):
        return f"{label}_wrong_track_key"
    if int(snapshot.sensor_frame_id) != int(entry.frame_id):
        return f"{label}_wrong_sensor_frame"
    if int(snapshot.library_frame_id) != int(entry.library_frame_id):
        return f"{label}_wrong_library_frame"
    if snapshot.phase != phase:
        return f"{label}_wrong_phase"
    if not snapshot.valid:
        return f"{label}_invalid:{snapshot.invalid_reason}"
    return None


def center_aim_point(
    center_px: Sequence[float],
    entry: HistoryEntry,
    plane_y_m: float,
    maximum_distance_m: float,
) -> tuple[tuple[float, float, float] | None, str | None]:
    """C6 瞄准点 P_center = 框中心射线 ∩ 平面 y = `plane_y_m`（= `ground_plane_y_m` + h_c）。

    相机约定同 `controller.geolocate`：射线 = right·(u−cx)/fx + up·(−(v−cy)/fy) + forward（四元数列向量）。"""
    try:
        if entry.camera_rotation_xyzw is None or entry.camera_position_world_m is None or entry.intrinsics_px is None:
            return None, "pose_missing"
        rotation = rotation_matrix({"camera_rotation_xyzw": list(entry.camera_rotation_xyzw)})
        fx = float(entry.intrinsics_px["fx"])
        fy = float(entry.intrinsics_px["fy"])
        cx = float(entry.intrinsics_px["cx"])
        cy = float(entry.intrinsics_px["cy"])
    except (KeyError, TypeError, ValueError):
        return None, "pose_invalid"
    u, v = float(center_px[0]), float(center_px[1])
    if not (math.isfinite(u) and math.isfinite(v)) or fx <= 0.0 or fy <= 0.0:
        return None, "pixel_invalid"
    right = (rotation[0][0], rotation[1][0], rotation[2][0])
    up = (rotation[0][1], rotation[1][1], rotation[2][1])
    forward = (rotation[0][2], rotation[1][2], rotation[2][2])
    a, b = (u - cx) / fx, -(v - cy) / fy
    ray = tuple(right[i] * a + up[i] * b + forward[i] for i in range(3))
    norm = math.sqrt(sum(c * c for c in ray))
    if not math.isfinite(norm) or norm <= 1e-12:
        return None, "degenerate_ray"
    ray = tuple(c / norm for c in ray)
    if ray[1] >= -1e-9:
        return None, "parallel_or_upward_ray"
    origin = tuple(float(c) for c in entry.camera_position_world_m)
    distance = (float(plane_y_m) - origin[1]) / ray[1]
    if not math.isfinite(distance) or distance <= 0.0:
        return None, "non_positive_intersection"
    if distance > float(maximum_distance_m):
        return None, "intersection_beyond_maximum_distance"
    point = tuple(origin[i] + ray[i] * distance for i in range(3))
    if not all(math.isfinite(c) for c in point):
        return None, "non_finite_intersection"
    return point, None  # type: ignore[return-value]


# --- P1-ENG-FASTFIX-001 §3.3：重捕提示与合成先验（K3） ------------------------------------------------


def pose_metadata_of(entry: HistoryEntry) -> dict[str, Any] | None:
    """帧传感器元数据中的位姿/内参（非真值，取自常驻历史 = 帧环快照元数据）；缺即 None。"""
    if entry.camera_rotation_xyzw is None or entry.intrinsics_px is None:
        return None
    return {
        "camera_rotation_xyzw": [float(v) for v in entry.camera_rotation_xyzw],
        "intrinsics_px": {k: float(v) for k, v in dict(entry.intrinsics_px).items()},
        "width": entry.width,
        "height": entry.height,
    }


@dataclass(frozen=True)
class HintCandidate:
    """一个可作 `f_last` 的候选：本批最新帧、管理器已接受观测、同次门求值无完整性命中（PUBLISHED/DROPPED）；
    `state` 为该帧 `tracker.step` 返回后绑定键完整 KF 状态的深复制（拆载体时不现取，不冒充更早帧）。"""

    frame_id: int
    track_key: int
    state: FullKfState | None
    pose: Mapping[str, Any] | None
    settle: str

    def as_record(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "track_key": self.track_key,
            "state": None if self.state is None else self.state.as_record(),
            "pose": None if self.pose is None else _jsonable(dict(self.pose)),
            "settle": self.settle,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "HintCandidate":
        state = record.get("state")
        return cls(int(record["frame_id"]), int(record["track_key"]),
                   None if state is None else FullKfState.from_record(state), record.get("pose"), str(record["settle"]))


@dataclass(frozen=True)
class ReacquireHint:
    f_last: int
    escalation_frame: int | None
    seg_end: str
    track_key: int
    state: FullKfState
    pose_f_last: Mapping[str, Any]
    task: Mapping[str, Any]
    old_episode_id: int | None

    def as_record(self) -> dict[str, Any]:
        return {
            "f_last": self.f_last,
            "escalation_frame": self.escalation_frame,
            "seg_end": self.seg_end,
            "track_key": self.track_key,
            "state": self.state.as_record(),
            "pose_f_last": _jsonable(dict(self.pose_f_last)),
            "task": _jsonable(dict(self.task)),
            "old_episode_id": self.old_episode_id,
        }


def _matmul8(a: Sequence[Sequence[float]], b: Sequence[Sequence[float]]) -> list[list[float]]:
    n, m, k = len(a), len(b[0]), len(b)
    return [[sum(float(a[i][t]) * float(b[t][j]) for t in range(k)) for j in range(m)] for i in range(n)]


def pose_center_transform(mean: Sequence[float], covariance: Sequence[Sequence[float]], homography: Any
                          ) -> tuple[list[float], list[list[float]]] | None:
    """与 `det_assoc_tracker.apply_pose_center` 同式（纯 Python）：(xc, yc) ← H(xc, yc)；J = ∂H/∂(u,v)；(vx, vy) ← J·(vx, vy)；
    8×8 变换 T 在位置块与速度块放 J、其余单位，P ← T P Tᵀ。宽高与宽高速度不变；映射或 J 不可得 → None。"""
    xc, yc = float(mean[0]), float(mean[1])
    mapped = map_point(homography, xc, yc)
    jac = jacobian(homography, xc, yc)
    if mapped is None or jac is None:
        return None
    out = [float(v) for v in mean]
    out[0], out[1] = float(mapped[0]), float(mapped[1])
    vx, vy = float(mean[4]), float(mean[5])
    out[4] = jac[0][0] * vx + jac[0][1] * vy
    out[5] = jac[1][0] * vx + jac[1][1] * vy
    transform = [[1.0 if i == j else 0.0 for j in range(8)] for i in range(8)]
    for block in (0, 4):
        for i in range(2):
            for j in range(2):
                transform[block + i][block + j] = float(jac[i][j])
    transposed = [[transform[j][i] for j in range(8)] for i in range(8)]
    return out, _matmul8(_matmul8(transform, covariance), transposed)


def predict_full_state(predictor: Any, mean: Sequence[float], covariance: Sequence[Sequence[float]], steps: int
                       ) -> tuple[list[float], list[list[float]]]:
    """用钉版库同类、同常数的 KF（`predictor.predict(mean, covariance)`）连推 `steps` 步；不入库、不回写。"""
    current_mean = [float(v) for v in mean]
    current_cov = [[float(v) for v in row] for row in covariance]
    for _ in range(int(steps)):
        predicted_mean, predicted_cov = predictor.predict(current_mean, current_cov)
        current_mean = [float(v) for v in predicted_mean]
        current_cov = [[float(v) for v in row] for row in predicted_cov]
    return current_mean, current_cov


def synthesize_reacq_prior(hint: ReacquireHint, entry: HistoryEntry, predictor: Any, params: CaptureParams
                           ) -> tuple[KfSnapshot | None, str | None, dict[str, Any]]:
    """§3.3 合成先验（每帧 f 现算，不入库、不回写）：n = f − f_last ≥ 1；提示完整 8 维状态经库同类 KF 连推 n 步，再以
    `pose_homography(f_last 位姿, f 位姿)` 做 pose-center 变换（与库「预测后、关联前」同序）；取位置块得快照，phase =
    `REACQ_PRIOR`。映射为 None、J 不可得、非有限或 S 不可逆 → (None, 原因)（本帧无证据）。"""
    f = int(entry.frame_id)
    n = f - int(hint.f_last)
    detail: dict[str, Any] = {"n": n}
    if n < 1:
        return None, "reacq_prior_not_after_f_last", detail
    if predictor is None or not callable(getattr(predictor, "predict", None)):
        return None, "reacq_predictor_unavailable", detail
    pose_f = pose_metadata_of(entry)
    if pose_f is None:
        return None, "reacq_pose_missing", detail
    try:
        mean, covariance = predict_full_state(predictor, hint.state.mean, hint.state.covariance, n)
    except (ArithmeticError, TypeError, ValueError) as error:
        return None, f"reacq_predict_failed:{type(error).__name__}", detail
    try:
        homography = pose_homography(dict(hint.pose_f_last), pose_f)
    except (TypeError, ValueError, KeyError):
        return None, "reacq_pose_homography_unavailable", detail
    mapped = pose_center_transform(mean, covariance, homography)
    if mapped is None:
        return None, "reacq_pose_center_unmappable", detail
    mean, covariance = mapped
    detail["mean"] = [round(v, 9) if math.isfinite(v) else None for v in mean]
    detail["covariance"] = [[round(v, 9) if math.isfinite(v) else None for v in row] for row in covariance]
    if not all(math.isfinite(v) for v in [*mean, *(c for row in covariance for c in row)]):
        return None, "reacq_prior_non_finite", detail
    snapshot = make_kf_snapshot(f, entry.library_frame_id, hint.track_key, KF_PRIOR, mean[0:4], mean[4:6],
                                [covariance[0][0:2], covariance[1][0:2]])
    if not snapshot.valid:
        return None, f"reacq_prior_invalid:{snapshot.invalid_reason}", detail
    if _inverse2(gate_covariance(snapshot, params.sigma_p)) is None:
        return None, "reacq_gate_covariance_singular", detail
    return replace(snapshot, phase=REACQ_PRIOR), None, detail


def reacq_snapshot_from_record(record: Mapping[str, Any]) -> KfSnapshot:
    """落盘合成先验 → 快照（经库快照校验后把阶段换回 `REACQ_PRIOR`；不经 `KfSnapshot.from_record` 的库阶段闭集）。"""
    if record.get("phase") != REACQ_PRIOR:
        raise ReplayRejected("a logged reacquire prior must carry phase reacq_prior")
    base = make_kf_snapshot(
        int(record["sensor_frame_id"]), int(record["library_frame_id"]), int(record["track_key"]), KF_PRIOR,
        record.get("xywh_px"), record.get("vel_px_per_frame"), record.get("pos_cov_px2"),
        forced_invalid=None if record.get("valid", True) else (record.get("invalid_reason") or "kf_invalid"),
    )
    return replace(base, phase=REACQ_PRIOR)


def resolve_click(entry: HistoryEntry, x_px: float, y_px: float, rho_click: float) -> tuple[str, int | None, dict[str, Any]]:
    """纯；在 k 帧 **tracked** 行里找包含点的框：0 → NO_TRACK_AT_K；1 → j；≥ 2 → 取中心最近者，
    次近/最近距离比 < ρ_click 则 AMBIGUOUS（AC-12）。"""
    width = entry.width or 640
    height = entry.height or 480
    containing: list[tuple[float, int]] = []
    for row in entry.rows(TRACKED):
        if row.out_of_frame:
            continue
        x, y, w, h = row.box_norm
        x1, y1, x2, y2 = x * width, y * height, (x + w) * width, (y + h) * height
        if x1 <= x_px <= x2 and y1 <= y_px <= y2:
            distance = math.hypot((x1 + x2) / 2.0 - x_px, (y1 + y2) / 2.0 - y_px)
            containing.append((distance, row.track_id))
    containing.sort()
    info: dict[str, Any] = {"containing": [[track_id, round(distance, 6)] for distance, track_id in containing]}
    if not containing:
        return NO_TRACK_AT_K, None, info
    if len(containing) == 1:
        return "BOUND", containing[0][1], info
    nearest, second = containing[0][0], containing[1][0]
    ratio = math.inf if nearest <= 1e-9 else second / nearest
    info["distance_ratio"] = None if math.isinf(ratio) else round(ratio, 6)
    if ratio < rho_click:
        return AMBIGUOUS, None, info
    return "BOUND", containing[0][1], info


# --- 授权（§3.4 + AR1-2 可达域 G） ----------------------------------------------------


@dataclass(frozen=True)
class AuthInputs:
    task: str
    watchdog: str
    continuity: str
    semantic: str
    geometry: str
    observation: str
    age: int
    covariance: str
    t0: int | None = None

    def as_record(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "watchdog": self.watchdog,
            "continuity": self.continuity,
            "semantic": self.semantic,
            "geometry": self.geometry,
            "observation": self.observation,
            "age": self.age,
            "covariance": self.covariance,
            "t0": self.t0,
        }


@dataclass(frozen=True)
class Authorization:
    body: str
    gimbal: str
    valid_until_frame: int | None
    reason_codes: tuple[str, ...]
    row: int | None
    consistent: bool

    def as_record(self) -> dict[str, Any]:
        return {
            "body": self.body,
            "gimbal": self.gimbal,
            "valid_until_frame": self.valid_until_frame,
            "reason_codes": list(self.reason_codes),
            "row": self.row,
            "consistent": self.consistent,
        }

    def at_most(self, other: "Authorization") -> bool:
        """授权偏序：(b,g) ≤ (b′,g′) 当且仅当两分量都不高。"""
        return BODY_RANK[self.body] <= BODY_RANK[other.body] and GIMBAL_RANK[self.gimbal] <= GIMBAL_RANK[other.gimbal]


def age_band(age: int, params: CaptureParams) -> str:
    if age <= 0:
        return "0"
    if age <= params.t_pred:
        return "pred"
    if age < params.t_repair:
        return "gap"
    return "expired"


def in_reachable_domain(inputs: AuthInputs, params: CaptureParams) -> bool:
    """AR1-2 可达规范域 G：task≠ACTIVE 的 belief 字段不授权（总在 G 内，落行 1）；ACTIVE 时
    semantic=UNKNOWN；OBSERVED ⇒ SUPPORTED、age=0、协方差 within；PREDICTED ⇒ age ≥ 1，S/T 仅未到期，
    BROKEN 仅已到期，DISPUTED 可在 age ≥ 1 锁存。"""
    if inputs.task != "ACTIVE":
        return True
    if inputs.semantic != UNKNOWN:
        return False
    band = age_band(inputs.age, params)
    if inputs.observation == OBSERVED:
        return inputs.continuity == SUPPORTED and band == "0" and inputs.covariance == "within"
    if inputs.observation != PREDICTED or band == "0":
        return False
    if inputs.continuity in (SUPPORTED, TENTATIVE):
        return band != "expired"
    if inputs.continuity == BROKEN:
        return band == "expired"
    return inputs.continuity == DISPUTED


def derive_authorization(inputs: AuthInputs, params: CaptureParams) -> Authorization:
    """纯函数、全函数：先一致性（域外 → HOLD/不发 + `authorization_input_inconsistent`），再八行首命中。"""
    if not in_reachable_domain(inputs, params):
        return Authorization(HOLD, GIMBAL_NONE, None, ("authorization_input_inconsistent",), None, False)
    if inputs.task != "ACTIVE":
        return Authorization(HOLD, GIMBAL_NONE, None, ("NO_TASK",), 1, True)
    if inputs.watchdog == "stale":
        return Authorization(HOLD, GIMBAL_NONE, None, ("STALE",), 2, True)
    if inputs.continuity in TERMINAL_CONTINUITY:
        return Authorization(HOLD, GIMBAL_NONE, None, ("CONTINUITY_TERMINAL",), 3, True)
    if inputs.semantic == CONTRADICTED:
        return Authorization(HOLD, GIMBAL_NONE, None, ("SEMANTIC_CONTRADICTED",), 4, True)
    if inputs.geometry != "valid":
        return Authorization(HOLD, GIMBAL_NONE, None, ("GEO_REJECT",), 5, True)
    if inputs.observation == OBSERVED and inputs.continuity == SUPPORTED and inputs.age == 0:
        return Authorization(FOLLOW, GIMBAL_OBSERVED, None, ("OBSERVED_SUPPORTED",), 6, True)
    if (
        inputs.observation == PREDICTED
        and inputs.continuity in (SUPPORTED, TENTATIVE)
        and 1 <= inputs.age <= params.t_pred
        and inputs.covariance == "within"
    ):
        until = None if inputs.t0 is None else int(inputs.t0) + params.t_pred
        return Authorization(HOLD, GIMBAL_PREDICTED, until, ("PREDICTION_WINDOW",), 7, True)
    return Authorization(HOLD, GIMBAL_NONE, None, ("HOLD_DEFAULT",), 8, True)


# --- 效果与端口 --------------------------------------------------------------------


@dataclass(frozen=True)
class FrameEffect:
    """⑤ 的产物（只对本批最新帧）：发布前由 `TargetManager.effect_current` 复核版本与有效期。"""

    effect_seq: int
    frame_id: int
    version: int
    body: str
    gimbal: str
    aim_point_world_m: tuple[float, float, float] | None
    aim_center_px: tuple[float, float] | None
    observation_box_norm: tuple[float, float, float, float] | None
    observation_confidence: float | None
    valid_until_frame: int | None
    reason_codes: tuple[str, ...]
    authorization_row: int | None

    def as_record(self) -> dict[str, Any]:
        return {
            "effect_seq": self.effect_seq,
            "frame_id": self.frame_id,
            "version": self.version,
            "body": self.body,
            "gimbal": self.gimbal,
            "aim_point_world_m": None if self.aim_point_world_m is None else [round(v, 9) for v in self.aim_point_world_m],
            "aim_center_px": None if self.aim_center_px is None else [round(v, 6) for v in self.aim_center_px],
            "observation_box_norm": None if self.observation_box_norm is None else list(self.observation_box_norm),
            "valid_until_frame": self.valid_until_frame,
            "reason_codes": list(self.reason_codes),
            "authorization_row": self.authorization_row,
        }


@dataclass(frozen=True)
class FrameOutcome:
    frame_id: int
    projection: tuple[str, str | None] | None
    effect: FrameEffect | None
    events: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class CommitResult:
    accepted: bool
    reason: str | None
    relation: str | None = None
    episode_id: int | None = None
    fail_closed: bool = False


class ReplayedPortError(RuntimeError):
    """重放端口按落盘结果复现的失败；`text` 为在线时记录的原文（`类型名: 消息`），逐字复现。"""

    def __init__(self, text: str):
        super().__init__(text)
        self.text = text


def _error_text(error: BaseException) -> str:
    return error.text if isinstance(error, ReplayedPortError) else f"{type(error).__name__}: {error}"


#: 端口调用的落盘结果闭集（每次调用的结果都是 reducer 的外部输入；重放端口按调用种类逐条复现）。
PORT_CALLS: tuple[str, ...] = ("follow", "restore", "readback", "pointer")


class ReplayPort:
    """重放用绑定端口：`follow`/`restore_binding_state` 的成败、`binding_state_matches` 读回与 `pointer()` 读数
    全部取自落盘 `port` 输入行，不依赖进程内的核心对象（半改 follow、复原/读回失败只凭输入完整复现）。

    R1-1（AC-15/AR1-2「缺引用即拒」）：端口行按在线写出顺序归属于其前最近一条非端口输入行（该行处理期间的端口调用
    在线时紧随其后落盘）。重放处理每条输入行前装入它的端口段，每次端口调用必须按序消费到**同种类**的下一条记录，
    否则（缺行、截断、乱序）记违例并抛 `ReplayInputIncomplete`；该行处理完后端口段必须恰好用完（多出、重复即违例）。
    违例同时记入 `violations`，即使端口异常在事务回滚分支里被吞掉，`end_segment` 仍拒绝——不默认成功、不退回本地
    指针/coasting 模型。`begin_coasting`/`snapshot_binding_state` 不是外部读数（由已复现的 follow 结果确定），只用本地模型。"""

    def __init__(self) -> None:
        self._pointer: int | None = None
        self._coasting: dict[str, Any] | None = None
        self._segment: list[Mapping[str, Any]] = []
        self._where = "init"
        self.violations: list[str] = []

    def begin_segment(self, records: Sequence[Mapping[str, Any]], where: str) -> None:
        for record in records:
            if str(record.get("call")) not in PORT_CALLS:
                raise ReplayRejected(f"port line with unknown call {record.get('call')!r} after {where}")
        self._segment = [dict(record) for record in records]
        self._where = where

    def end_segment(self) -> None:
        if self._segment:
            self.violations.append(f"{len(self._segment)} unconsumed port record(s) after {self._where} "
                                   f"(first: {self._segment[0].get('call')!r}; extra/duplicated/reordered input)")
        self._segment = []
        if self.violations:
            raise ReplayInputIncomplete("tm_inputs incomplete: " + "; ".join(self.violations))

    def _next(self, call: str) -> Mapping[str, Any]:
        if not self._segment:
            message = f"port call {call!r} during {self._where} has no recorded outcome (missing or truncated input)"
        elif self._segment[0].get("call") != call:
            message = (f"port call {call!r} during {self._where} meets recorded {self._segment[0].get('call')!r} "
                       "(missing or reordered input)")
        else:
            return self._segment.pop(0)
        self.violations.append(message)
        raise ReplayInputIncomplete(message)

    def follow(self, track_id: int | None) -> None:
        outcome = self._next("follow")
        if not outcome.get("ok", True):
            raise ReplayedPortError(str(outcome.get("error") or "replayed follow failure"))
        new = None if track_id is None else int(track_id)
        if new != self._pointer:
            self._coasting = None
        self._pointer = new

    def pointer(self) -> int | None:
        value = self._next("pointer").get("value")
        return None if value is None else int(value)

    def begin_coasting(self, designation_id: int) -> None:
        self._coasting = {"designation_id": int(designation_id), "steps": 0}

    def snapshot_binding_state(self) -> dict[str, Any]:
        return {"pointer": self._pointer, "coasting": None if self._coasting is None else dict(self._coasting)}

    def restore_binding_state(self, snapshot: Mapping[str, Any]) -> None:
        outcome = self._next("restore")
        if not outcome.get("ok", True):
            raise ReplayedPortError(str(outcome.get("error") or "replayed restore failure"))
        self._pointer = snapshot["pointer"]
        self._coasting = None if snapshot["coasting"] is None else dict(snapshot["coasting"])

    def binding_state_matches(self, snapshot: Mapping[str, Any]) -> bool:
        outcome = self._next("readback")
        if not outcome.get("ok", True):
            raise ReplayedPortError(str(outcome.get("error") or "replayed readback failure"))
        return bool(outcome.get("value"))


# --- 落盘输入（§3.8 + AR1-2） --------------------------------------------------------


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def line_sha256(record: Mapping[str, Any]) -> str:
    """UTF-8、键排序、紧凑 JSON、禁 NaN 的原文（不含自身 sha 字段）的 sha256。"""
    body = {k: v for k, v in record.items() if k != "line_sha256"}
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def entry_input_record(entry: HistoryEntry) -> dict[str, Any]:
    """reducer 读到的历史子集（全部行：键、state、未裁剪框/归一化框、matched_det_index、out_of_frame、kf；
    原始检测；两阶段快照；removed_ids；位姿/内参/画幅）。"""
    return {
        "frame_id": entry.frame_id,
        "simulation_time_s": entry.simulation_time_s,
        "capture_monotonic_s": entry.capture_monotonic_s,
        "library_frame_id": entry.library_frame_id,
        "camera_position_world_m": None if entry.camera_position_world_m is None else list(entry.camera_position_world_m),
        "camera_rotation_xyzw": None if entry.camera_rotation_xyzw is None else list(entry.camera_rotation_xyzw),
        "intrinsics_px": None if entry.intrinsics_px is None else dict(entry.intrinsics_px),
        "width": entry.width,
        "height": entry.height,
        "tracks": [
            {
                "track_id": row.track_id,
                "box_norm": list(row.box_norm),
                "score": row.score,
                "cls": row.cls,
                "state": row.state,
                "matched_det_index": row.matched_det_index,
                "out_of_frame": row.out_of_frame,
                "kf": None if row.kf is None else row.kf.as_record(),
                "kf_invalid_reason": row.kf_invalid_reason,
            }
            for row in entry.tracks
        ],
        "removed_ids": list(entry.removed_ids),
        "raw_detections": [det.as_record() for det in entry.raw_detections],
        "prior_snapshots": [snap.as_record() for snap in entry.prior_snapshots],
        "post_snapshots": [snap.as_record() for snap in entry.post_snapshots],
        "silently_dropped_ids": list(entry.silently_dropped_ids),
        "priors_available": entry.priors_available,
    }


def entry_from_input_record(record: Mapping[str, Any]) -> HistoryEntry:
    rows = []
    for item in record["tracks"]:
        rows.append(
            TrackRow(
                int(item["track_id"]),
                tuple(float(v) for v in item["box_norm"]),  # type: ignore[arg-type]
                float(item["score"]),
                int(item["cls"]),
                str(item["state"]),
                int(item.get("matched_det_index", -1)),
                bool(item.get("out_of_frame", False)),
                None if item.get("kf") is None else KfSnapshot.from_record(item["kf"]),
                item.get("kf_invalid_reason"),
            )
        )
    return HistoryEntry(
        frame_id=int(record["frame_id"]),
        simulation_time_s=record.get("simulation_time_s"),
        capture_monotonic_s=record.get("capture_monotonic_s"),
        camera_position_world_m=None if record.get("camera_position_world_m") is None else tuple(record["camera_position_world_m"]),
        camera_rotation_xyzw=None if record.get("camera_rotation_xyzw") is None else tuple(record["camera_rotation_xyzw"]),
        intrinsics_px=record.get("intrinsics_px"),
        library_frame_id=int(record["library_frame_id"]),
        tracks=tuple(rows),
        removed_ids=tuple(int(v) for v in record["removed_ids"]),
        width=record.get("width"),
        height=record.get("height"),
        raw_detections=tuple(RawDetection.from_record(item) for item in record.get("raw_detections", [])),
        prior_snapshots=tuple(KfSnapshot.from_record(item) for item in record.get("prior_snapshots", [])),
        post_snapshots=tuple(KfSnapshot.from_record(item) for item in record.get("post_snapshots", [])),
        silently_dropped_ids=tuple(int(v) for v in record.get("silently_dropped_ids", [])),
        priors_available=bool(record.get("priors_available", False)),
    )


class InputsLog:
    """`tm_inputs.jsonl` 追加写者；`path=None` 时只在内存保留行（测试/兼容模式）。

    P1-ENG-FASTFIX-001 AC-13（R2-2 承接）：`chain=True`（捕获会话）时每行另带 `prev_line_sha256` = 上一行的
    `line_sha256`（首行为 None），计入本行 sha；重放逐行核链，删除/重排任一中间行即拒。缺省 False = 旧格式逐字不变。"""

    def __init__(self, path: Path | None, *, chain: bool = False):
        self.path = None if path is None else Path(path)
        self.chain = bool(chain)
        self.lines: list[dict[str, Any]] = []
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def reset_chain(self, previous_line_sha256: str | None) -> None:
        """重放用（v2）：把链头置为已落盘的上一行 sha，使重放中重算的端口记录与在线逐字同 sha（只在内存）。"""
        self.lines = [{"line_sha256": previous_line_sha256}]

    def append(self, record: Mapping[str, Any]) -> str:
        line = dict(record)
        if self.chain:
            line["prev_line_sha256"] = self.lines[-1]["line_sha256"] if self.lines else None
        line["line_sha256"] = line_sha256(line)
        self.lines.append(line)
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(canonical_json(line) + "\n")
        return line["line_sha256"]


# --- 管理器 ------------------------------------------------------------------------


EventSink = Callable[[str, Mapping[str, Any]], None]


class TargetManager:
    """单写者 reducer。会话（或重放）按消费顺序调用；全部方法串行（会话 tick 单线程）。"""

    def __init__(
        self,
        params: CaptureParams,
        *,
        mode: str,
        config_sha256: str,
        config_text: str | None = None,
        inputs: InputsLog | None = None,
        sink: EventSink | None = None,
        ground_plane_y_m: float = 0.0,
        maximum_ground_range_m: float = 400.0,
        record_init: bool = True,
        fastfix: FastfixParams | None = None,
        fastfix_config_sha256: str | None = None,
    ):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        validate_structure(params)
        self.params = params
        #: P1-ENG-FASTFIX-001 §3.7：重捕窗口参数（`T_reacq`、`auto_reacquire`）；None = 重捕不可用（旧路径不变）。
        self.fastfix = fastfix
        self.fastfix_config_sha256 = fastfix_config_sha256
        self.mode = mode
        self.config_sha256 = config_sha256
        self.inputs = inputs or InputsLog(None)
        self._sink = sink
        self.ground_plane_y_m = float(ground_plane_y_m)
        self.maximum_ground_range_m = float(maximum_ground_range_m)
        self._port: Any = None
        # 业务状态（AR1-3 计数初值 0）。
        self.task: TaskSpec | None = None
        self.runtime: TaskRuntime | None = None
        self.binding: BindingRecord | None = None
        self.belief: TargetBelief | None = None
        self.repair = RepairBuffer()
        self.intent_revision = 0
        self.episode_seq = 0
        self.stopped = False
        self.watchdog = "fresh"
        self.reinit_required = False
        self.version = 0
        self.event_seq = 0
        self.effect_seq = 0
        self.events: list[dict[str, Any]] = []
        self._gate0: dict[int, dict[str, Any]] = {}
        self._last_line_sha: str | None = None
        self._pending_projection_reason: str | None = None
        self._replaying_commit = False
        #: P1-ENG-FASTFIX-001 §3.3：重捕状态（None = 无提示）。键：status ∈ {pending, open, committed, failed,
        #: ambiguous, canceled}、hint、hint_line_sha256、f_ready、m_ready、hz、buffer（键 → 连续证据帧）。
        self.reacq: dict[str, Any] | None = None
        #: 最近一次重捕终局（会话读取后清空）：{"result": committed|failed|ambiguous|canceled, ...}。
        self.reacq_result: dict[str, Any] | None = None
        self._reacquired_frame: int | None = None
        if record_init:
            init: dict[str, Any] = {
                "schema_version": INPUTS_SCHEMA_V2 if self.inputs.chain else INPUTS_SCHEMA,
                "kind": "init",
                "mode": mode,
                "config_sha256": config_sha256,
                "config_text": config_text,
                "params": params.as_record(),
                "ground_plane_y_m": self.ground_plane_y_m,
                "maximum_ground_range_m": self.maximum_ground_range_m,
                "initial_state": self._business_snapshot_record(),
            }
            if fastfix is not None:
                init["fastfix_params"] = fastfix.as_record()
                init["fastfix_config_sha256"] = fastfix_config_sha256
            self._last_line_sha = self.inputs.append(init)

    # --- 端口 -----------------------------------------------------------------

    def attach_port(self, port: Any) -> None:
        """绑定端口 = 当前常驻载体的指针核心（`follow`/`pointer`/快照三件套/`begin_coasting`）。"""
        self._port = port

    def detach_port(self) -> None:
        self._port = None

    # --- 事件 -----------------------------------------------------------------

    def _emit(self, kind: str, event_type: str, *, frame_id: int | None, accepted: bool | None = None,
              reason: str | None = None, effect_seq: int | None = None, **fields: Any) -> dict[str, Any]:
        self.event_seq += 1
        record = {
            "event_seq": self.event_seq,
            "type": event_type,
            "frame_id": frame_id,
            "accepted": accepted,
            "reason": reason,
            "effect_seq": effect_seq,
            "config_sha256": self.config_sha256,
            "tm_inputs_line_sha256": self._last_line_sha,
            **fields,
        }
        self.events.append({"kind": kind, **record})
        if self._sink is not None:
            self._sink(kind, record)
        return record

    def _input(self, record: Mapping[str, Any]) -> str:
        self._last_line_sha = self.inputs.append(dict(record, config_sha256=self.config_sha256))
        return self._last_line_sha

    # --- 业务快照（AR1-3 事务） ----------------------------------------------------

    def _business_snapshot(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "runtime": self.runtime,
            "binding": self.binding,
            "belief": self.belief,
            "repair": {key: [dict(item) for item in value] for key, value in self.repair.streaks.items()},
            "intent_revision": self.intent_revision,
            "episode_seq": self.episode_seq,
            "stopped": self.stopped,
            "version": self.version,
            "gate0": {key: dict(value) for key, value in self._gate0.items()},
        }

    def _business_snapshot_record(self) -> dict[str, Any]:
        return {
            "task": None if self.task is None else self.task.as_record(),
            "runtime": None if self.runtime is None else self.runtime.as_record(),
            "binding": None if self.binding is None else self.binding.as_record(),
            "belief": None if self.belief is None else self.belief.as_record(),
            "intent_revision": self.intent_revision,
            "episode_seq": self.episode_seq,
        }

    def _restore_business(self, snapshot: Mapping[str, Any]) -> None:
        self.task = snapshot["task"]
        self.runtime = snapshot["runtime"]
        self.binding = snapshot["binding"]
        self.belief = snapshot["belief"]
        self.repair.streaks = {key: [dict(item) for item in value] for key, value in snapshot["repair"].items()}
        self.intent_revision = snapshot["intent_revision"]
        self.episode_seq = snapshot["episode_seq"]
        self.stopped = snapshot["stopped"]
        self.version = snapshot["version"]
        self._gate0 = {key: dict(value) for key, value in snapshot["gate0"].items()}

    def _business_matches(self, snapshot: Mapping[str, Any]) -> bool:
        return self._business_snapshot() == snapshot

    # --- 只读视图 ----------------------------------------------------------------

    @property
    def track_key(self) -> int | None:
        return None if self.binding is None else self.binding.track_key

    def task_axis(self) -> str:
        if self.stopped:
            return "stopped"
        if self.task is None or self.runtime is None:
            return "none"
        if self.runtime.phase == "CANCELED":
            return "CANCELED"
        return "ACTIVE"

    # --- 提交与释放（§3.5；AR1-3） --------------------------------------------------

    def commit_binding(
        self,
        *,
        origin: str,
        track_key: int,
        expected_version: int,
        source_frame: int | None,
        commit_frame: int | None,
        evidence: Mapping[str, Any] | None = None,
        selector: ClickSelector | LanguageCompatSelector | None = None,
        coasting_designation_id: int | None = None,
        post_snapshot: KfSnapshot | None = None,
        observed_box_px: tuple[float, float, float, float] | None = None,
    ) -> CommitResult:
        """唯一设指针入口。先校验版本/阶段/截止/origin → 不改状态算出新记录 → `follow(new)`；
        `follow` 抛异常 → `follow(old)` + 恢复完整核心与管理器快照 + 逐字段核对；复原失败 fail-closed。
        仅 `follow` 成功后才写新记录、关闭旧 episode、设 coasting。被拒零状态变化（换目标被拒继续跟旧目标）。"""
        evidence = dict(evidence or {})
        if origin in ("lang_confirm", "lang_acquire") and not self._replaying_commit:
            # 兼容路径的提交请求来自会话外部判据（旧解析/收养），原文落盘供重放。
            self._input(
                {
                    "kind": "commit_request",
                    "origin": origin,
                    "track_key": int(track_key),
                    "expected_version": expected_version,
                    "source_frame": source_frame,
                    "commit_frame": commit_frame,
                    "evidence": _jsonable(evidence),
                    "selector": None if selector is None else selector.as_record(),
                    "coasting_designation_id": coasting_designation_id,
                }
            )
        rejection = self._commit_precheck(origin, expected_version, commit_frame)
        if rejection is not None:
            self._emit("tm_event", "commit", frame_id=commit_frame, accepted=False, reason=rejection, origin=origin, track_key=track_key)
            return CommitResult(False, rejection)
        plan = self._plan_commit(origin, int(track_key), source_frame, commit_frame, evidence, selector, post_snapshot, observed_box_px)
        port = self._port
        if port is None:
            self._emit("tm_event", "commit", frame_id=commit_frame, accepted=False, reason="no_binding_port", origin=origin, track_key=track_key)
            return CommitResult(False, "no_binding_port")
        core_snapshot = port.snapshot_binding_state()
        business = self._business_snapshot()
        old_pointer = self._read_pointer(port)
        try:
            port.follow(int(track_key))
            self._record_port("follow", True, None)
        except Exception as error:  # noqa: BLE001 — 事务回滚分支
            self._record_port("follow", False, _error_text(error))
            return self._rollback(core_snapshot, business, old_pointer, origin, track_key, commit_frame, error)
        self._apply_plan(plan)
        if coasting_designation_id is not None:
            port.begin_coasting(int(coasting_designation_id))
        self.version += 1
        self._emit(
            "binding_committed",
            "commit",
            frame_id=commit_frame,
            accepted=True,
            origin=origin,
            relation=plan["binding"].relation if plan["binding"] is not None else None,
            old_track_key=None if plan["old_binding"] is None else plan["old_binding"].track_key,
            new_track_key=int(track_key),
            episode_id=None if plan["binding"] is None else plan["binding"].target_episode_id,
            association_revision=None if plan["binding"] is None else plan["binding"].association_revision,
            intent_revision=self.intent_revision,
            evidence=evidence,
        )
        if plan["close_old"] is not None:
            self._emit("tm_event", "episode_closed", frame_id=commit_frame, accepted=True, reason=plan["close_old"][1],
                       episode_id=plan["close_old"][0])
        return CommitResult(True, None, plan["binding"].relation, plan["binding"].target_episode_id)

    def _commit_precheck(self, origin: str, expected_version: int, commit_frame: int | None) -> str | None:
        if origin not in ORIGINS:
            return "origin_unknown"
        if origin not in MODE_ORIGINS[self.mode]:
            return "origin_not_allowed_in_mode"
        if self.stopped:
            return "task_stopped"
        if self.reinit_required:
            return "reinit_required"
        if expected_version != self.version:
            return "version_mismatch"
        if origin == "repair":
            if self.belief is None or self.binding is None or self.belief.continuity_status != TENTATIVE:
                return "repair_without_tentative_binding"
            if commit_frame is None or self.belief.age(commit_frame) > self.params.t_repair - 1:
                return "repair_deadline_passed"
        if origin == "lang_acquire" and (self.task is None or self.runtime is None or self.runtime.phase != "ACQUIRING"):
            return "acquire_without_task"
        if origin == "reacquire":
            # FASTFIX §3.3 预检：有效提示、窗口未到期（调用方逐帧先判截止）、ACQUIRING、看门狗 fresh。
            if self.reacq is None or self.reacq.get("status") != "open" or self.reacq.get("hint") is None:
                return "reacquire_without_open_window"
            if self.task is None or self.runtime is None or self.runtime.phase != "ACQUIRING" or self.binding is not None:
                return "reacquire_without_acquiring_task"
            if self.watchdog != "fresh":
                return "reacquire_watchdog_stale"
            if commit_frame is None or int(commit_frame) > int(self.reacq["f_ready"]) + self.fastfix.t_reacq - 1:  # type: ignore[union-attr]
                return "reacquire_deadline_passed"
        return None

    def _plan_commit(
        self,
        origin: str,
        track_key: int,
        source_frame: int | None,
        commit_frame: int | None,
        evidence: Mapping[str, Any],
        selector: Any,
        post_snapshot: KfSnapshot | None,
        observed_box_px: tuple[float, float, float, float] | None,
    ) -> dict[str, Any]:
        """在不改任何状态的前提下算出新记录（AR1-3 计数矩阵）。"""
        old_binding = self.binding
        intent = self.intent_revision
        episode_seq = self.episode_seq
        task, runtime = self.task, self.runtime
        close_old: tuple[int, str] | None = None
        if origin == "click":
            intent += 1
            episode_seq += 1
            task = TaskSpec.click(selector, intent)
            relation = "USER_RESELECT" if old_binding is not None else "INITIAL"
            binding = BindingRecord(episode_seq, track_key, 0, relation, origin, commit_frame, dict(evidence))
            runtime = TaskRuntime("TRACKING", self.mode, episode_seq, {})
            if old_binding is not None:
                close_old = (old_binding.target_episode_id, REASON_SUPERSEDED)
        elif origin == "repair":
            assert old_binding is not None
            binding = BindingRecord(
                old_binding.target_episode_id, track_key, old_binding.association_revision + 1,
                "CONTINUITY_REPAIR", origin, commit_frame, dict(evidence),
            )
        elif origin == "lang_confirm":
            intent += 1
            episode_seq += 1
            task = TaskSpec._language_compat(selector, intent)
            relation = "USER_RESELECT" if old_binding is not None else "INITIAL"
            binding = BindingRecord(episode_seq, track_key, 0, relation, origin, commit_frame, dict(evidence))
            runtime = TaskRuntime("TRACKING", self.mode, episode_seq, {})
            if old_binding is not None:
                close_old = (old_binding.target_episode_id, "operator_release")
        elif origin == "reacquire":
            # FASTFIX §3.3 / 首次接受释义 3：新 episode（episode_seq + 1、association_revision = 0）；TaskSpec 与
            # intent_revision 不变；旧 episode 已在拆载体时关闭一次，此处不再关闭。
            episode_seq += 1
            binding = BindingRecord(episode_seq, track_key, 0, "REBUILD_REACQUIRE", origin, commit_frame, dict(evidence))
            runtime = TaskRuntime("TRACKING", self.mode, episode_seq, {})
        else:  # lang_acquire
            episode_seq += 1
            binding = BindingRecord(episode_seq, track_key, 0, "INITIAL", origin, commit_frame, dict(evidence))
            runtime = TaskRuntime("TRACKING", self.mode, episode_seq, {})
        belief = self.belief
        if origin in ("click", "lang_confirm", "lang_acquire", "reacquire"):
            belief = transition(
                TargetBelief(
                    t0=int(commit_frame) if commit_frame is not None else 0,
                    last_box_px=observed_box_px,
                    last_track_key=track_key,
                    predicted=None if post_snapshot is None else _predicted_record(post_snapshot),
                ),
                BIND,
            )
        elif origin == "repair" and belief is not None:
            belief = replace(
                transition(belief, REPAIR),
                t0=int(commit_frame),  # type: ignore[arg-type]
                last_box_px=observed_box_px,
                last_track_key=track_key,
                observation_status=OBSERVED,
                predicted=None if post_snapshot is None else _predicted_record(post_snapshot),
                reported_no_new_observation=False,
            )
        return {
            "old_binding": old_binding,
            "binding": binding,
            "task": task,
            "runtime": runtime,
            "belief": belief,
            "intent_revision": intent,
            "episode_seq": episode_seq,
            "close_old": close_old,
            "new_episode": origin != "repair",
        }

    def _apply_plan(self, plan: Mapping[str, Any]) -> None:
        self.binding = plan["binding"]
        self.task = plan["task"]
        self.runtime = plan["runtime"]
        self.belief = plan["belief"]
        self.intent_revision = plan["intent_revision"]
        self.episode_seq = plan["episode_seq"]
        self.repair.clear()
        if plan["new_episode"]:
            self._gate0 = {}

    def _rollback(self, core_snapshot: Any, business: Mapping[str, Any], old_pointer: int | None, origin: str,
                  track_key: int, commit_frame: int | None, error: BaseException) -> CommitResult:
        port = self._port
        restored = False
        # 每一步端口调用的结果分别落盘（follow / restore / readback），重放端口逐条复现（AC-7/15）。
        try:
            port.follow(old_pointer)
            self._record_port("follow", True, None)
        except Exception as second:  # noqa: BLE001
            self._record_port("follow", False, _error_text(second))
        else:
            try:
                port.restore_binding_state(core_snapshot)
                self._record_port("restore", True, None)
            except Exception as third:  # noqa: BLE001
                self._record_port("restore", False, _error_text(third))
            else:
                self._restore_business(business)
                try:
                    matches = bool(port.binding_state_matches(core_snapshot))
                    self._record_port("readback", True, None, value=matches)
                except Exception as fourth:  # noqa: BLE001
                    matches = False
                    self._record_port("readback", False, _error_text(fourth), value=False)
                restored = matches and self._business_matches(business)
        if restored:
            self._emit("tm_event", "commit", frame_id=commit_frame, accepted=False, reason="follow_failed",
                       origin=origin, track_key=track_key, error=_error_text(error))
            return CommitResult(False, "follow_failed")
        # fail-closed：不继续旧/新跟随；HOLD、停云台新效果、作废在途效果、best-effort release。
        self.reinit_required = True
        self.version += 1
        pointer_state = "UNKNOWN"
        try:
            port.follow(None)
            self._record_port("follow", True, None)
            pointer_state = "cleared" if self._read_pointer(port) is None else "UNKNOWN"
        except Exception as fifth:  # noqa: BLE001
            self._record_port("follow", False, _error_text(fifth))
        self._close_episode(REASON_ROLLBACK_FAILED, commit_frame)
        self.binding = None
        self.belief = None
        self.repair.clear()
        self._emit("tm_event", "commit", frame_id=commit_frame, accepted=False, reason=REASON_ROLLBACK_FAILED,
                   origin=origin, track_key=track_key, pointer_state=pointer_state,
                   error=_error_text(error), fail_closed=True)
        return CommitResult(False, REASON_ROLLBACK_FAILED, fail_closed=True)

    def _record_port(self, call: str, ok: bool, error: str | None, *, value: Any = None) -> None:
        """端口调用结果是 reducer 的外部输入（重放端口按调用种类逐条复现；`PORT_CALLS` 闭集）。"""
        record: dict[str, Any] = {"kind": "port", "call": call, "ok": ok, "error": error}
        if call in ("readback", "pointer"):
            record["value"] = value
        self._input(record)

    def _read_pointer(self, port: Any) -> int | None:
        """读端口指针并把读数落盘（决策依赖的外部读数；重放端口按读数复现）。"""
        value = port.pointer()
        self._record_port("pointer", True, None, value=None if value is None else int(value))
        return value

    def release_binding(self, reason: str, *, frame_id: int | None = None, cancel_task: bool = True) -> bool:
        """唯一会话内清指针入口（`follow(None)`）；当前 episode 以 reason 关闭；重复释放无重复关闭。"""
        self._input({"kind": "release", "reason": reason, "frame_id": frame_id, "cancel_task": cancel_task})
        return self._release(reason, frame_id, cancel_task)

    def _release(self, reason: str, frame_id: int | None, cancel_task: bool) -> bool:
        if cancel_task and self._reacq_active():
            # FASTFIX §3.3 ①：release 取消原任务，提示作废。
            self._cancel_reacquire(reason, frame_id)
        had_binding = self.binding is not None
        port = self._port
        if port is not None and (had_binding or self._read_pointer(port) is not None):
            try:
                port.follow(None)
                self._record_port("follow", True, None)
            except Exception as error:  # noqa: BLE001
                self._record_port("follow", False, _error_text(error))
                self.reinit_required = True
                self._emit("tm_event", "release", frame_id=frame_id, accepted=False, reason="release_follow_failed",
                           pointer_state="UNKNOWN", error=_error_text(error))
        if not had_binding:
            if cancel_task and self.runtime is not None and self.runtime.phase != "CANCELED":
                self.runtime = replace(self.runtime, phase="CANCELED")
                self.version += 1
            return False
        self._close_episode(reason, frame_id)
        self.binding = None
        self.belief = None
        self.repair.clear()
        if self.runtime is not None:
            self.runtime = replace(self.runtime, phase="CANCELED" if cancel_task else "ACQUIRING", episode_id=None)
        self.version += 1
        return True

    def accept_language_task(self, selector: LanguageCompatSelector, *, frame_id: int | None) -> None:
        """lang_confirm 得 TRACK_ENDED 并按旧路径进入 acquire：确认任务已接受、尚未绑定（intent +1，不分配 episode）。"""
        self._input({"kind": "language_task", "selector": selector.as_record(), "frame_id": frame_id})
        self._accept_language_task(selector, frame_id)

    def _accept_language_task(self, selector: LanguageCompatSelector, frame_id: int | None) -> None:
        self.intent_revision += 1
        self.task = TaskSpec._language_compat(selector, self.intent_revision)
        self.runtime = TaskRuntime("ACQUIRING", self.mode, None, {})
        self.version += 1
        self._emit("tm_event", "task_accepted", frame_id=frame_id, accepted=True, intent_revision=self.intent_revision)

    def on_teardown(self, reason: str) -> None:
        """拆除（`_teardown_resident`）：关闭当前 episode，无 follow 调用（核心随载体丢弃）。"""
        self._input({"kind": "teardown", "reason": reason})
        self._teardown(reason)
        self._port = None

    def _teardown(self, reason: str) -> None:
        if self._reacq_active() and self.reacq.get("status") == "open":  # type: ignore[union-attr]
            # 重捕窗口内新载体再次拆除：提示作废、任务取消（不复活，不再自动尝试）。
            self._cancel_reacquire(f"teardown:{reason}", None)
            if self.runtime is not None and self.runtime.phase == "ACQUIRING":
                self.runtime = replace(self.runtime, phase="CANCELED")
                self.version += 1
        if self.binding is not None:
            self._close_episode(reason, None)
            self.binding = None
            self.belief = None
            self.repair.clear()
            if self.runtime is not None:
                self.runtime = replace(self.runtime, phase="CANCELED", episode_id=None)
            self.version += 1

    def _close_episode(self, reason: str, frame_id: int | None) -> None:
        if self.binding is None:
            return
        self._emit("tm_event", "episode_closed", frame_id=frame_id, accepted=True, reason=reason,
                   episode_id=self.binding.target_episode_id)

    # --- 非帧请求（①） --------------------------------------------------------------

    def request_stop(self, *, request_id: str | None = None, cause: str | None = None) -> None:
        """STOP 串行：任务置 stopped、版本 +1（在途效果作废），之后任何效果都是 HOLD/不发。

        FASTFIX：重捕提示在途时另落 `cause`（作废原因，如 `rebuild_limit`）；无提示时输入行逐字同旧格式。"""
        record: dict[str, Any] = {"kind": "request", "action": "stop", "request_id": request_id}
        if self._reacq_active() and cause is not None:
            record["cause"] = cause
        self._input(record)
        self._stop(request_id, record.get("cause"))

    def _stop(self, request_id: str | None, cause: str | None = None) -> None:
        self.stopped = True
        self.version += 1
        self._emit("tm_event", "stop", frame_id=None, accepted=True, request_id=request_id)
        if self._reacq_active():
            # FASTFIX §3.3 ①：stop 取消原任务（已 stopped），提示作废。
            self._cancel_reacquire(cause or "operator_stop", None)

    def on_watchdog(self, *, stale: bool, at_monotonic_s: float | None = None) -> None:
        self._input({"kind": "watchdog", "stale": bool(stale), "at_monotonic_s": at_monotonic_s})
        self._watchdog(bool(stale))

    def _watchdog(self, stale: bool) -> None:
        new = "stale" if stale else "fresh"
        if new != self.watchdog:
            self.watchdog = new
            self.version += 1
            self._emit("tm_event", "watchdog", frame_id=None, accepted=True, reason=new)

    # --- FASTFIX §3.3：时序升级重建后的自动重捕（G2；K3/K2） ---------------------------------------------

    def _reacq_active(self) -> bool:
        return self.reacq is not None and self.reacq.get("status") in ("pending", "open")

    @property
    def reacquire_open(self) -> bool:
        return self.reacq is not None and self.reacq.get("status") == "open"

    @property
    def reacquire_pending(self) -> bool:
        return self.reacq is not None and self.reacq.get("status") == "pending"

    def take_reacquire_result(self) -> dict[str, Any] | None:
        result, self.reacq_result = self.reacq_result, None
        return result

    def prepare_reacquire_hint(
        self,
        *,
        seg_end: str,
        timing_escalation: bool,
        escalation_frame: int | None,
        auto_reacquire: bool,
        candidates: Sequence[HintCandidate],
    ) -> ReacquireHint | None:
        """拆载体前（旧载体仍在）：只在「时序升级」+ `auto_reacquire=on` + 有绑定 + 连续性 ∉ {DISPUTED, BROKEN} + 未
        stopped 时生成提示；否则记 `reacquire_skipped(cause)`。输入（升级标志、候选完整状态与位姿）原文落盘，重放据此复现。"""
        sha = self._input(
            {
                "kind": "reacquire_hint",
                "seg_end": seg_end,
                "timing_escalation": bool(timing_escalation),
                "escalation_frame": escalation_frame,
                "auto_reacquire": bool(auto_reacquire),
                "candidates": [candidate.as_record() for candidate in candidates],
            }
        )
        return self._prepare_reacquire(seg_end, bool(timing_escalation), escalation_frame, bool(auto_reacquire),
                                       list(candidates), sha)

    def _prepare_reacquire(self, seg_end: str, timing_escalation: bool, escalation_frame: int | None,
                           auto_reacquire: bool, candidates: Sequence[HintCandidate], line_sha: str) -> ReacquireHint | None:
        cause: str | None = None
        chosen: HintCandidate | None = None
        if not timing_escalation:
            cause = "not_timing_escalation"
        elif not auto_reacquire or self.fastfix is None or not self.fastfix.auto_reacquire:
            cause = "auto_reacquire_off"
        elif self.binding is None or self.belief is None or self.task is None or self.runtime is None:
            cause = "no_binding"
        elif self.stopped or self.reinit_required:
            cause = "task_stopped"
        elif self.belief.continuity_status in TERMINAL_CONTINUITY:
            cause = "continuity_terminal"
        else:
            key = self.binding.track_key
            bound_frame = self.binding.bound_frame_id
            qualified = [
                c for c in candidates
                if c.track_key == key and c.settle in ("PUBLISHED", "DROPPED")
                and (bound_frame is None or c.frame_id >= int(bound_frame))
            ]
            if not qualified:
                cause = "no_qualified_observation"
            else:
                chosen = max(qualified, key=lambda c: c.frame_id)
                state = chosen.state
                if escalation_frame is not None and int(escalation_frame) - chosen.frame_id > self.fastfix.t_reacq:
                    cause = "hint_stale"
                elif (state is None or not state.valid or state.phase != KF_POSTERIOR or state.track_key != key
                      or state.sensor_frame_id != chosen.frame_id or chosen.pose is None):
                    cause = "hint_invalid"
        if cause is not None:
            self.reacq = None
            self._emit("reacquire_skipped", "reacquire", frame_id=escalation_frame, accepted=False, reason=cause,
                       seg_end=seg_end, f_last=None if chosen is None else chosen.frame_id)
            return None
        assert chosen is not None and chosen.state is not None and chosen.pose is not None
        assert self.binding is not None and self.task is not None
        hint = ReacquireHint(
            f_last=chosen.frame_id,
            escalation_frame=escalation_frame,
            seg_end=seg_end,
            track_key=self.binding.track_key,
            state=chosen.state,
            pose_f_last=dict(chosen.pose),
            task=self.task.as_record(),
            old_episode_id=self.binding.target_episode_id,
        )
        self.reacq = {"status": "pending", "hint": hint, "hint_line_sha256": line_sha, "buffer": {}}
        self._emit("tm_event", "reacquire_hint", frame_id=escalation_frame, accepted=True, seg_end=seg_end,
                   f_last=hint.f_last, track_key=hint.track_key, hint_line_sha256=line_sha)
        return hint

    def open_reacquire_window(self, *, f_ready: int, m_ready: float, hz: float) -> bool:
        """新载体 `resident_loop_started` 即开窗：f_ready = 该事件帧号，m_ready = 同源 monotonic。"""
        if not self.reacquire_pending:
            return False
        self._input({"kind": "reacquire_window", "f_ready": int(f_ready), "m_ready": float(m_ready), "hz": float(hz)})
        return self._open_reacquire_window(int(f_ready), float(m_ready), float(hz))

    def _open_reacquire_window(self, f_ready: int, m_ready: float, hz: float) -> bool:
        if not self.reacquire_pending:
            return False
        assert self.reacq is not None and self.fastfix is not None
        if self.stopped or self.runtime is None or self.runtime.phase != "ACQUIRING" or self.binding is not None:
            self._cancel_reacquire("task_not_acquiring", f_ready)
            return False
        t = self.fastfix.t_reacq
        self.reacq.update(status="open", f_ready=f_ready, m_ready=m_ready, hz=hz, buffer={})
        hint: ReacquireHint = self.reacq["hint"]
        self._emit("reacquire_started", "reacquire", frame_id=f_ready, accepted=True, f_ready=f_ready, m_ready=m_ready,
                   deadline_frame=f_ready + t - 1, deadline_monotonic_s=m_ready + t / hz, f_last=hint.f_last,
                   track_key=hint.track_key, hint_line_sha256=self.reacq["hint_line_sha256"])
        return True

    def reacquire_expired(self, *, frame_id: int | None = None, at_monotonic_s: float | None = None) -> str | None:
        """纯判定（不改状态）：帧号 > f_ready + T_reacq − 1 → `deadline_frame`；monotonic − m_ready > T_reacq/hz →
        `deadline_monotonic`；等于边界不算到期（首次接受释义 1）。"""
        if not self.reacquire_open:
            return None
        assert self.reacq is not None and self.fastfix is not None
        t = self.fastfix.t_reacq
        if frame_id is not None and int(frame_id) > int(self.reacq["f_ready"]) + t - 1:
            return "deadline_frame"
        if at_monotonic_s is not None and float(at_monotonic_s) - float(self.reacq["m_ready"]) > t / float(self.reacq["hz"]):
            return "deadline_monotonic"
        return None

    def expire_reacquire(self, *, at_monotonic_s: float) -> bool:
        """会话每 tick（零新帧亦然）的到期判定：到期才落盘输入并失败；未到期不改状态、不落盘。"""
        if self.reacquire_expired(at_monotonic_s=at_monotonic_s) is None:
            return False
        self._input({"kind": "reacquire_expire", "at_monotonic_s": float(at_monotonic_s)})
        return self._expire_reacquire(float(at_monotonic_s))

    def _expire_reacquire(self, at_monotonic_s: float) -> bool:
        cause = self.reacquire_expired(at_monotonic_s=at_monotonic_s)
        if cause is None:
            return False
        self._fail_reacquire(cause, None, "failed", at_monotonic_s=at_monotonic_s)
        return True

    def cancel_reacquire(self, cause: str, *, frame_id: int | None = None) -> bool:
        """人工点击（及其他会话外部取消）：只作废提示与证据缓冲，不改任务阶段（点击事务随后照现行执行）。"""
        if not self._reacq_active():
            return False
        self._input({"kind": "reacquire_cancel", "cause": cause, "frame_id": frame_id})
        self._cancel_reacquire(cause, frame_id)
        return True

    def _cancel_reacquire(self, cause: str, frame_id: int | None) -> None:
        assert self.reacq is not None
        self.reacq.update(status="canceled", buffer={})
        self.reacq_result = {"result": "canceled", "cause": cause, "frame_id": frame_id}
        self._emit("reacquire_canceled", "reacquire", frame_id=frame_id, accepted=True, reason=cause)

    def _fail_reacquire(self, cause: str, frame_id: int | None, result: str, **fields: Any) -> None:
        assert self.reacq is not None
        self.reacq.update(status=result, buffer={})
        if self.runtime is not None and self.runtime.phase == "ACQUIRING":
            self.runtime = replace(self.runtime, phase="CANCELED")
        self.version += 1
        reason = REASON_REACQUIRE_AMBIGUOUS if result == "ambiguous" else REASON_REACQUIRE_FAILED
        self.reacq_result = {"result": result, "reason": reason, "cause": cause, "frame_id": frame_id}
        self._emit("reacquire_failed", "reacquire", frame_id=frame_id, accepted=False, reason=reason, cause=cause, **fields)

    def reacquire_prior_for(self, entry: HistoryEntry, predictor: Any) -> dict[str, Any] | None:
        """会话侧：窗口开着时为本帧现算合成先验（纯计算，不改状态）；结果随帧输入落盘。"""
        if not self.reacquire_open or self.binding is not None:
            return None
        assert self.reacq is not None
        snapshot, reason, detail = synthesize_reacq_prior(self.reacq["hint"], entry, predictor, self.params)
        return {"prior": snapshot, "prior_reason": reason, "detail": detail}

    def _reacquire_frame(self, entry: HistoryEntry, ended: set[int], reacq: Mapping[str, Any]) -> None:
        """§3.3 窗口内一帧：先判截止（任一维严格越界即失败）→ 候选门（只用合成先验）→ 竞争 → 满足即提交。"""
        assert self.reacq is not None and self.fastfix is not None
        f = int(entry.frame_id)
        window = self.reacq
        expired = self.reacquire_expired(frame_id=f, at_monotonic_s=reacq.get("at_monotonic_s"))
        if expired is not None:
            self._fail_reacquire(expired, f, "failed", at_monotonic_s=reacq.get("at_monotonic_s"))
            return
        prior = reacq.get("prior")
        if prior is None:
            # 映射失败/非有限/S 不可逆：本帧无证据，缓冲清零重计。
            window["buffer"] = {}
            self._emit("tm_event", "reacquire_evidence", frame_id=f, accepted=False,
                       reason=reacq.get("prior_reason") or "reacq_prior_invalid")
            return
        passers: dict[int, dict[str, Any]] = {}
        keyed = {row.matched_det_index for row in entry.tracks if row.matched_det_index >= 0}
        for row in entry.tracks:
            if row.state not in (TRACKED, UNCONFIRMED) or row.track_id in entry.removed_ids or row.track_id in ended:
                continue
            gate = reacquire_gate(prior, self._candidate_detection(entry, row), self.params)
            if gate.passed:
                passers[row.track_id] = {"frame_id": f, "state": row.state, "nis": gate.nis}
        diagnostics = [
            {"det_index": det.det_index, "gate": reacquire_gate(prior, det, self.params).as_record(),
             "note": "no_library_key_never_committable"}
            for det in entry.raw_detections if det.det_index not in keyed
        ]
        streaks: dict[int, list[dict[str, Any]]] = {}
        for key, evidence in passers.items():
            previous = window["buffer"].get(key, [])
            streaks[key] = previous + [evidence] if previous and previous[-1]["frame_id"] == f - 1 else [evidence]
        window["buffer"] = streaks
        self._emit("tm_event", "reacquire_evidence", frame_id=f, accepted=bool(passers),
                   candidates={str(k): [round(e["nis"], 6) for e in v] for k, v in sorted(streaks.items())},
                   unkeyed_detections=diagnostics)
        if not streaks:
            return
        totals = sorted((sum(e["nis"] for e in v), key) for key, v in streaks.items())
        if len(totals) >= 2 and totals[1][0] - totals[0][0] < self.params.m_nis:
            self._fail_reacquire("ambiguous", f, "ambiguous",
                                 competition=[{"track_key": key, "cumulative_nis": round(total, 6)} for total, key in totals])
            return
        best_key = totals[0][1]
        streak = streaks[best_key]
        if len(streak) < self.params.n_adopt or streak[-1]["state"] != TRACKED:
            return
        candidate_post, post_reason = same_frame_post(entry, best_key)
        if candidate_post is None:
            # 候选同帧 post 无效 → 本帧不提交，证据保留。
            self._emit("tm_event", "reacquire_commit", frame_id=f, accepted=False, reason="kf_post_invalid",
                       track_key=best_key, detail=post_reason)
            return
        row = entry.row(best_key)
        assert row is not None
        width, height = entry.width or 640, entry.height or 480
        x, y, w, h = row.box_norm
        hint: ReacquireHint = window["hint"]
        evidence = {
            "hint_line_sha256": window["hint_line_sha256"],
            "f_last": hint.f_last,
            "reacquired_from_episode": hint.old_episode_id,
            "seg_end": hint.seg_end,
            "evidence_frames": [e["frame_id"] for e in streak],
            "nis": [round(e["nis"], 6) for e in streak],
            "states": [e["state"] for e in streak],
            "tm_inputs_line_sha256": self._last_line_sha,
        }
        commit = self.commit_binding(
            origin="reacquire",
            track_key=best_key,
            expected_version=self.version,
            source_frame=streak[0]["frame_id"],
            commit_frame=f,
            evidence=evidence,
            post_snapshot=candidate_post,
            observed_box_px=(x * width, y * height, (x + w) * width, (y + h) * height),
        )
        if commit.accepted:
            window.update(status="committed", buffer={})
            self._reacquired_frame = f
            self.reacq_result = {"result": "committed", "frame_id": f, "track_key": best_key, "episode_id": commit.episode_id}
            self._emit("reacquired_after_rebuild", "reacquire", frame_id=f, accepted=True, track_key=best_key,
                       episode_id=commit.episode_id, reacquired_from_episode=hint.old_episode_id,
                       evidence_frames=evidence["evidence_frames"], latency_frames=f - int(window["f_ready"]),
                       f_last=hint.f_last)
        elif commit.fail_closed:
            window.update(status="failed", buffer={})
            self.reacq_result = {"result": "rollback_failed", "reason": REASON_ROLLBACK_FAILED, "cause": commit.reason,
                                 "frame_id": f}
            self._emit("reacquire_failed", "reacquire", frame_id=f, accepted=False, reason=REASON_ROLLBACK_FAILED,
                       cause=commit.reason)
        else:
            self._fail_reacquire(f"commit_rejected:{commit.reason}", f, "failed")

    def click(
        self,
        *,
        request_id: str,
        x_px: float,
        y_px: float,
        frame_id: int,
        image_sha256: str,
        history: Callable[[int], HistoryEntry | None],
        head_frame_id: int | None,
        ended_ids: Iterable[int] = (),
        page: Mapping[str, Any] | None = None,
        actual_image_sha256: str | None = None,
    ) -> tuple[str, CommitResult | None, dict[str, Any]]:
        """C7：在 k 帧历史解析「包含点的框」，逐帧验证 k→当前证据链后经 `commit_binding` 绑定；不调 VLM、无确认。"""
        ended = sorted(int(v) for v in ended_ids)
        k = int(frame_id)
        frames = {}
        if head_frame_id is not None and k <= int(head_frame_id):
            for f in range(k, int(head_frame_id) + 1):
                entry = history(f)
                frames[f] = None if entry is None else entry_input_record(entry)
        self._input(
            {
                "kind": "request",
                "action": "click",
                "request_id": request_id,
                "x_px": x_px,
                "y_px": y_px,
                "frame_id": k,
                "image_sha256": image_sha256,
                "head_frame_id": head_frame_id,
                "ended_ids": ended,
                "chain_history": {str(f): v for f, v in frames.items()},
                "page": _jsonable(dict(page or {})),
                "actual_image_sha256": actual_image_sha256,
            }
        )
        return self._click_from_records(request_id, x_px, y_px, k, image_sha256, head_frame_id, ended, frames, page,
                                        actual_image_sha256)

    def _click_from_records(self, request_id: str, x_px: float, y_px: float, k: int, image_sha256: str,
                            head_frame_id: int | None, ended: Sequence[int], frames: Mapping[int, Any],
                            page: Mapping[str, Any] | None,
                            actual_image_sha256: str | None) -> tuple[str, CommitResult | None, dict[str, Any]]:
        info: dict[str, Any] = {"request_id": request_id, "k": k, "x_px": x_px, "y_px": y_px, "head_frame_id": head_frame_id}
        self._emit("click_received", "click", frame_id=k, accepted=None, request_id=request_id, k=k,
                   point=[x_px, y_px], image_sha256=image_sha256, consumed_head=head_frame_id, page=dict(page or {}))
        if self.mode != CAPTURE:
            self._emit("tm_event", "click", frame_id=k, accepted=False, reason="click_unavailable", request_id=request_id)
            return "click_unavailable", None, info
        record_k = frames.get(k)
        if head_frame_id is None or record_k is None:
            self._emit("tm_event", "click", frame_id=k, accepted=False, reason=FRAME_NOT_IN_HISTORY, request_id=request_id)
            return FRAME_NOT_IN_HISTORY, None, info
        if actual_image_sha256 != image_sha256:
            # `runtime/frames/frame_<k>.jpg` 当刻字节 sha ≠ 请求值（含读不到）→ REQUEST_INVALID(image_mismatch)。
            self._emit("tm_event", "click", frame_id=k, accepted=False, reason="image_mismatch", request_id=request_id,
                       actual_image_sha256=actual_image_sha256)
            return "image_mismatch", None, info
        entry_k = entry_from_input_record(record_k)
        if not (0.0 <= float(x_px) < float(entry_k.width or 640) and 0.0 <= float(y_px) < float(entry_k.height or 480)):
            self._emit("tm_event", "click", frame_id=k, accepted=False, reason="pixel_out_of_frame", request_id=request_id)
            return "pixel_out_of_frame", None, info
        result, track_key, resolve_info = resolve_click(entry_k, float(x_px), float(y_px), self.params.rho_click)
        info.update(resolve_info)
        if result != "BOUND":
            self._emit("tm_event", "click", frame_id=k, accepted=False, reason=result, request_id=request_id, **resolve_info)
            return result, None, info
        assert track_key is not None
        # 逐帧证据链：[k, 提交帧] 每个历史帧 j 为 tracked（已激活、非出画）、不在 removed/ended；缺帧即拒。
        for f in range(k, int(head_frame_id) + 1):
            record = frames.get(f)
            if record is None:
                reason = f"evidence_chain_missing@{f}"
                self._emit("tm_event", "click", frame_id=k, accepted=False, reason=reason, request_id=request_id, track_key=track_key)
                return reason, None, info
            entry = entry_from_input_record(record)
            row = entry.row(track_key)
            if row is None or row.state != TRACKED or row.out_of_frame or track_key in entry.removed_ids or track_key in ended:
                reason = f"evidence_chain_broken@{f}"
                self._emit("tm_event", "click", frame_id=k, accepted=False, reason=reason, request_id=request_id, track_key=track_key)
                return reason, None, info
        head_entry = entry_from_input_record(frames[int(head_frame_id)])
        head_row = head_entry.row(track_key)
        assert head_row is not None
        # AR1-2：点击新实例以提交帧（历史头）有效、对齐的 post 初始化；无效/错帧/非 posterior → 拒绝（零状态变化）。
        head_post, post_reason = same_frame_post(head_entry, track_key)
        if head_post is None:
            self._emit("tm_event", "click", frame_id=k, accepted=False, reason="kf_post_invalid", request_id=request_id,
                       track_key=track_key, detail=post_reason)
            return "kf_post_invalid", None, info
        width, height = head_entry.width or 640, head_entry.height or 480
        x, y, w, h = head_row.box_norm
        commit = self.commit_binding(
            origin="click",
            track_key=track_key,
            expected_version=self.version,
            source_frame=k,
            commit_frame=int(head_frame_id),
            evidence={"request_id": request_id, "k": k, "chain": [k, int(head_frame_id)], "resolve": resolve_info,
                      "tm_inputs_line_sha256": self._last_line_sha},
            selector=ClickSelector(float(x_px), float(y_px), k, str(image_sha256)),
            post_snapshot=head_post,
            observed_box_px=(x * width, y * height, (x + w) * width, (y + h) * height),
        )
        if commit.accepted:
            self._pending_projection_reason = None
        return ("BOUND" if commit.accepted else (commit.reason or "commit_rejected")), commit, info

    # --- 帧（①–⑤） ---------------------------------------------------------------

    def on_frame(self, entry: HistoryEntry, *, newest: bool, wall_unix_s: float | None = None,
                 reacq: Mapping[str, Any] | None = None) -> FrameOutcome:
        """§3.3 同帧顺序：② 到期 → ③ 原轨迹重匹配 → ④ 修复证据 → ⑤ 授权与效果（只对本批最新帧）。

        FASTFIX §3.3：重捕窗口开着时会话另给 `reacq`（本帧同源 monotonic 与合成先验/原因）；它作为非真值输入随帧行
        落盘（键 `reacq`，只在给出时出现，旧帧行格式不变），重放据此复现窗口判定。"""
        record: dict[str, Any] = {
            "kind": "frame",
            "frame_id": entry.frame_id,
            "simulation_time_s": entry.simulation_time_s,
            "capture_monotonic_s": entry.capture_monotonic_s,
            "wall_unix_s": wall_unix_s,
            "batch_position": "newest" if newest else "backlog",
            "history": entry_input_record(entry),
            "ended_ids": sorted(int(v) for v in (self._port_ended_ids())),
        }
        if reacq is not None:
            prior = reacq.get("prior")
            record["reacq"] = {
                "at_monotonic_s": reacq.get("at_monotonic_s"),
                "prior": None if prior is None else prior.as_record(),
                "prior_reason": reacq.get("prior_reason"),
                "detail": _jsonable(dict(reacq.get("detail") or {})),
            }
        self._input(record)
        return self._frame(entry, newest, ended=set(self._port_ended_ids()), reacq=reacq)

    def _port_ended_ids(self) -> Iterable[int]:
        ended = getattr(self._port, "ended_ids", None) if self._port is not None else None
        return () if ended is None else ended

    def _frame(self, entry: HistoryEntry, newest: bool, ended: set[int], reacq: Mapping[str, Any] | None = None) -> FrameOutcome:
        f = entry.frame_id
        before = len(self.events)
        repaired_now = False
        if self.mode == CAPTURE and self.binding is None and self.reacquire_open:
            # FASTFIX §3.3：窗口内先判截止与候选（③ 满足即提交，提交帧当帧按提交后状态授权）；缺 `reacq` 输入时
            # 只按帧号判截止（无证据）。
            self._reacquire_frame(entry, ended, reacq if reacq is not None else {"prior": None, "prior_reason": "reacq_input_missing"})
        if self.mode != CAPTURE or self.binding is None or self.belief is None:
            effect = self._effects(entry, newest) if self.mode == CAPTURE else None
            return FrameOutcome(f, None, effect, tuple(self.events[before:]))
        belief = self.belief
        o = self.binding.track_key
        committed_this_frame = (
            self.binding.bound_frame_id == f and belief.t0 == f
            and belief.observation_status == OBSERVED and belief.continuity_status == SUPPORTED
        )
        if committed_this_frame:
            # §3.3 ①（C1-3 / RR-1）：本帧的替换请求（点击）已在 ② 之前提交，提交本身就是本帧已接受的观测
            # （以提交帧有效 post 初始化）；②–④ 不再对同一帧重复求值，直接 ⑤ 按提交后状态授权与产生效果。
            pass
        elif belief.continuity_status in (SUPPORTED, TENTATIVE):
            # ② 到期先于同帧任何证据处理。
            if belief.age(f) >= self.params.t_repair:
                self.belief = transition(belief, EXPIRE)
                self.repair.clear()
                self.version += 1
                self._emit("tm_transition", "continuity", frame_id=f, accepted=True, reason=REASON_BROKEN,
                           old=belief.continuity_status, new=BROKEN, age=belief.age(f))
            else:
                # ③ 原轨迹重匹配（原绑定键同帧 prior；无竞争）。
                accepted, disputed, info = self._assess_original(entry, o, ended)
                if accepted:
                    self._accept_original(entry, o, belief, info)
                elif disputed:
                    self.belief = replace(transition(belief, DISPUTE), observation_status=PREDICTED)
                    self.repair.clear()
                    self.version += 1
                    self._emit("tm_transition", "continuity", frame_id=f, accepted=True, reason=REASON_DISPUTED,
                               old=belief.continuity_status, new=DISPUTED, age=belief.age(f), competition=info)
                else:
                    self._miss_original(entry, o, belief, info)
                    # ④ 修复证据（仅捕获模式、auto_repair、age ≤ T_repair − 1）。
                    if self.params.auto_repair and self.belief is not None and self.belief.continuity_status == TENTATIVE:
                        repaired_now = self._repair_step(entry, o, ended)
        if self.belief is not None and self.belief.continuity_status == SUPPORTED and self.belief.observation_status == OBSERVED and self.belief.t0 == f:
            self._update_gate0(entry)
        projection = self._projection(f, repaired_now)
        effect = self._effects(entry, newest)
        return FrameOutcome(f, projection, effect, tuple(self.events[before:]))

    def _candidate_detection(self, entry: HistoryEntry, row: TrackRow) -> RawDetection | None:
        return entry.detection(row.matched_det_index)

    def _excluded(self, key: int) -> bool:
        info = self._gate0.get(int(key))
        return bool(info and info.get("co_tracked") and not info.get("jumped"))

    def _assess_original(self, entry: HistoryEntry, o: int, ended: set[int]) -> tuple[bool, bool, dict[str, Any]]:
        """③ 原轨迹重匹配。C1-1（AR1-2 修订 1）：一律用原绑定键**同帧** prior（对齐键与阶段核验、有效、S 可逆）；
        接受还须同帧有效 posterior（post 无效同样不授权）。任一不满足 → 不接受、`kf_ok=False`（本帧云台不发、HOLD）。"""
        row = entry.row(o)
        prior, prior_reason = same_frame_prior(entry, o, self.params)
        info: dict[str, Any] = {"original_state": None if row is None else row.state, "kf_ok": prior is not None}
        if prior_reason is not None:
            info["prior_reason"] = prior_reason
        if row is None or row.state != TRACKED or row.out_of_frame or o in entry.removed_ids or o in ended:
            info["reason"] = "original_not_tracked"
            return False, False, info
        if prior is None:
            info["reason"] = prior_reason
            return False, False, info
        post, post_reason = same_frame_post(entry, o)
        if post is None:
            info["reason"] = post_reason
            info["kf_ok"] = False
            return False, False, info
        gate = motion_size_gate(prior, self._candidate_detection(entry, row), self.params)
        info["gate"] = gate.as_record()
        if not gate.passed:
            info["reason"] = gate.reason
            return False, False, info
        # IR-6：竞争者闭集 = 同帧 tracked/unconfirmed 的其他库键，未被门 0 排除、非 removed/ended、有本帧匹配检测，
        # 且对 o 的同帧有效 prior 过运动与尺寸门；NIS_c − NIS_o < m_nis 即锁 DISPUTED（不取绝对值，等于不触发）。
        competitors = []
        for other in entry.tracks:
            if (other.track_id == o or other.state not in (TRACKED, UNCONFIRMED) or self._excluded(other.track_id)
                    or other.track_id in entry.removed_ids or other.track_id in ended):
                continue
            detection = self._candidate_detection(entry, other)
            if detection is None:
                continue
            other_gate = motion_size_gate(prior, detection, self.params)
            if other_gate.passed and other_gate.nis is not None and gate.nis is not None and other_gate.nis - gate.nis < self.params.m_nis:
                competitors.append({"track_key": other.track_id, "nis": round(other_gate.nis, 6)})
        if competitors:
            info["competitors"] = competitors
            info["original_nis"] = gate.nis
            return False, True, info
        return True, False, info

    def _accept_original(self, entry: HistoryEntry, o: int, belief: TargetBelief, info: Mapping[str, Any]) -> None:
        f = entry.frame_id
        row = entry.row(o)
        assert row is not None
        width, height = entry.width or 640, entry.height or 480
        x, y, w, h = row.box_norm
        regained = belief.continuity_status == TENTATIVE
        new = transition(belief, REGAIN)
        post, _reason = same_frame_post(entry, o)  # `_assess_original` 已核同帧有效 posterior
        assert post is not None
        self.belief = replace(
            new,
            t0=f,
            last_box_px=(x * width, y * height, (x + w) * width, (y + h) * height),
            last_track_key=o,
            observation_status=OBSERVED,
            predicted=_predicted_record(post),
            reported_no_new_observation=False,
        )
        self.repair.clear()
        if regained:
            self.version += 1
            self._emit("tm_transition", "continuity", frame_id=f, accepted=True, reason="original_regained",
                       old=TENTATIVE, new=SUPPORTED, gate=info.get("gate"))

    def _miss_original(self, entry: HistoryEntry, o: int, belief: TargetBelief, info: Mapping[str, Any]) -> None:
        """原轨迹本帧未接受。预测中心 = 原绑定键**同帧 prior**（库「预测 → 本帧补偿」后的内部未裁剪状态）；
        C1-1：同帧 prior 缺失/错帧/无效/S 不可逆，或原键本帧 post 不合格（`kf_ok=False`）→ 无预测（云台不发、HOLD），
        不得凭 post 替代。"""
        f = entry.frame_id
        predicted = None
        if info.get("kf_ok"):
            prior, _reason = same_frame_prior(entry, o, self.params)
            predicted = None if prior is None else _predicted_record(prior)
        new = transition(belief, MISS)
        self.belief = replace(new, observation_status=PREDICTED, predicted=predicted)
        if belief.continuity_status == SUPPORTED:
            self.version += 1
            self._emit("tm_transition", "continuity", frame_id=f, accepted=True, reason=REASON_PREDICTING,
                       old=SUPPORTED, new=TENTATIVE, age=belief.age(f), detail=dict(info))
        age = belief.age(f)
        if age >= self.params.t_report and not self.belief.reported_no_new_observation:
            self.belief = replace(self.belief, reported_no_new_observation=True)
            self._emit("tm_event", "report", frame_id=f, accepted=True, reason=REASON_NO_NEW_OBSERVATION, age=age, t0=belief.t0)

    def _repair_step(self, entry: HistoryEntry, o: int, ended: set[int]) -> bool:
        f = entry.frame_id
        assert self.belief is not None and self.binding is not None
        age = self.belief.age(f)
        if age > self.params.t_repair - 1:
            return False
        prior, prior_reason = same_frame_prior(entry, o, self.params)
        if prior is None:
            # 缺失/错帧/错阶段/无效 prior 或 S 不可逆（C1-1）：本帧不收证据（连续性断开，缓冲清零重计）、修复不提交。
            if self.repair.streaks:
                self.repair.clear()
            self._emit("tm_event", "repair_evidence", frame_id=f, accepted=False, reason=prior_reason, age=age)
            return False
        passers: dict[int, dict[str, Any]] = {}
        diagnostics: list[dict[str, Any]] = []
        keyed = set()
        for row in entry.tracks:
            if row.matched_det_index >= 0:
                keyed.add(row.matched_det_index)
            if row.track_id == o or row.state not in (TRACKED, UNCONFIRMED):
                continue
            if self._excluded(row.track_id) or row.track_id in entry.removed_ids or row.track_id in ended:
                continue
            gate = motion_size_gate(prior, self._candidate_detection(entry, row), self.params)
            if gate.passed:
                passers[row.track_id] = {"frame_id": f, "state": row.state, "nis": gate.nis}
        for det in entry.raw_detections:
            if det.det_index not in keyed:
                gate = motion_size_gate(prior, det, self.params)
                diagnostics.append({"det_index": det.det_index, "gate": gate.as_record(), "note": "no_library_key_never_committable"})
        streaks: dict[int, list[dict[str, Any]]] = {}
        for key, evidence in passers.items():
            previous = self.repair.streaks.get(key, [])
            if previous and previous[-1]["frame_id"] == f - 1:
                streaks[key] = previous + [evidence]
            else:
                streaks[key] = [evidence]
        self.repair.streaks = streaks
        if diagnostics or passers:
            self._emit("tm_event", "repair_evidence", frame_id=f, accepted=bool(passers), age=age,
                       candidates={str(k): [round(e["nis"], 6) for e in v] for k, v in streaks.items()},
                       unkeyed_detections=diagnostics)
        if not streaks:
            return False
        totals = sorted((sum(e["nis"] for e in v), key) for key, v in streaks.items())
        if len(totals) >= 2 and totals[1][0] - totals[0][0] < self.params.m_nis:
            old = self.belief.continuity_status
            self.belief = replace(transition(self.belief, DISPUTE), observation_status=PREDICTED)
            self.repair.clear()
            self.version += 1
            self._emit("tm_transition", "continuity", frame_id=f, accepted=True, reason=REASON_DISPUTED, old=old, new=DISPUTED,
                       age=age, competition=[{"track_key": key, "cumulative_nis": round(total, 6)} for total, key in totals])
            return False
        best_key = totals[0][1]
        streak = streaks[best_key]
        if len(streak) < self.params.n_adopt or streak[-1]["state"] != TRACKED:
            return False
        candidate_post, post_reason = same_frame_post(entry, best_key)
        if candidate_post is None:
            # AR1-2：新键以提交帧有效 post 初始化；不合格 → 本帧不提交（不授权），证据保留、截止不变。
            self._emit("tm_event", "repair_commit", frame_id=f, accepted=False, reason="kf_post_invalid", age=age,
                       track_key=best_key, detail=post_reason)
            return False
        row = entry.row(best_key)
        assert row is not None
        width, height = entry.width or 640, entry.height or 480
        x, y, w, h = row.box_norm
        commit = self.commit_binding(
            origin="repair",
            track_key=best_key,
            expected_version=self.version,
            source_frame=streak[0]["frame_id"],
            commit_frame=f,
            evidence={"evidence_frames": [e["frame_id"] for e in streak], "nis": [round(e["nis"], 6) for e in streak],
                      "states": [e["state"] for e in streak], "tm_inputs_line_sha256": self._last_line_sha},
            post_snapshot=candidate_post,
            observed_box_px=(x * width, y * height, (x + w) * width, (y + h) * height),
        )
        return commit.accepted

    def _update_gate0(self, entry: HistoryEntry) -> None:
        """门 0（A1）：[绑定帧, t0] 内与原轨迹同帧 tracked、且自身中心无 > r_jump·对角线跳变的轨迹被排除。"""
        width, height = entry.width or 640, entry.height or 480
        o = self.binding.track_key if self.binding is not None else None
        for row in entry.rows(TRACKED):
            if row.track_id == o or row.out_of_frame:
                continue
            x, y, w, h = row.box_norm
            center = ((x + w / 2.0) * width, (y + h / 2.0) * height)
            diagonal = math.hypot(w * width, h * height)
            info = self._gate0.setdefault(row.track_id, {"co_tracked": True, "jumped": False, "center": None})
            if info.get("center") is not None and diagonal > 0.0:
                jump = math.hypot(center[0] - info["center"][0], center[1] - info["center"][1])
                if jump > self.params.r_jump_diag * diagonal:
                    info["jumped"] = True
            info["center"] = center

    # --- 投影与效果（§3.6、⑤） ----------------------------------------------------------

    def _projection(self, frame_id: int, repaired_now: bool) -> tuple[str, str | None] | None:
        belief = self.belief
        if self.binding is None or belief is None:
            return None
        if belief.continuity_status == BROKEN:
            return ("SUSPECTED", REASON_BROKEN)
        if belief.continuity_status == DISPUTED:
            return ("SUSPECTED", REASON_DISPUTED)
        if repaired_now:
            return ("TRACKING", REASON_REPAIRED)
        if self._reacquired_frame is not None and self._reacquired_frame == frame_id and belief.observation_status == OBSERVED:
            return ("TRACKING", REASON_REBUILD_REACQUIRED)
        if belief.observation_status == OBSERVED:
            return ("TRACKING", None)
        age = belief.age(frame_id)
        if age < self.params.t_report:
            return ("TRACKING", REASON_PREDICTING)
        return ("TRACKING", REASON_NO_NEW_OBSERVATION)

    def authorization_inputs(self, entry: HistoryEntry) -> tuple[AuthInputs, tuple[float, float] | None, tuple[float, float, float] | None, str | None]:
        f = entry.frame_id
        belief = self.belief
        task = self.task_axis()
        if belief is None or self.binding is None:
            return AuthInputs(task, self.watchdog, SUPPORTED, UNKNOWN, "invalid", PREDICTED, 0, "kf_invalid", None), None, None, None
        age = belief.age(f)
        center: tuple[float, float] | None = None
        covariance = "kf_invalid"
        if belief.observation_status == OBSERVED and belief.t0 == f and belief.last_box_px is not None:
            box = belief.last_box_px
            center = ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
            # 本帧已接受观测：接受本身要求同帧有效 prior 过门（或刚经提交、以有效 post 初始化）；C1-1：协方差只在
            # 信念所存快照是本帧、对齐、有效的 posterior 时按 within 计，否则 kf_invalid（域外 → 一致性拒绝 HOLD/不发）。
            covariance = "within" if _snapshot_record_aligned(belief.predicted, entry, KF_POSTERIOR) else "kf_invalid"
        elif _snapshot_record_aligned(belief.predicted, entry, KF_PRIOR):
            center = (float(belief.predicted["xc"]), float(belief.predicted["yc"]))
            covariance = "within" if predicted_gate_radius(belief.predicted, self.params) <= self.params.r_gate_max_px else "exceeds"
        observation = OBSERVED if (belief.observation_status == OBSERVED and belief.t0 == f) else PREDICTED
        point, geo_reason = (None, "no_aim_center")
        if center is not None:
            point, geo_reason = center_aim_point(center, entry, self.ground_plane_y_m + self.params.h_c_m, self.maximum_ground_range_m)
        inputs = AuthInputs(
            task=task,
            watchdog=self.watchdog,
            continuity=belief.continuity_status or SUPPORTED,
            semantic=belief.semantic_status,
            geometry="valid" if point is not None else "invalid",
            observation=observation,
            age=age,
            covariance=covariance,
            t0=belief.t0,
        )
        return inputs, center, point, geo_reason

    def _effects(self, entry: HistoryEntry, newest: bool) -> FrameEffect | None:
        if not newest:
            return None
        f = entry.frame_id
        inputs, center, point, geo_reason = self.authorization_inputs(entry)
        authorization = derive_authorization(inputs, self.params)
        self.effect_seq += 1
        observation_box = None
        confidence = None
        if authorization.body == FOLLOW and self.binding is not None:
            row = entry.row(self.binding.track_key)
            if row is not None:
                observation_box = tuple(row.box_norm)
                confidence = row.score
        effect = FrameEffect(
            effect_seq=self.effect_seq,
            frame_id=f,
            version=self.version,
            body=authorization.body,
            gimbal=authorization.gimbal,
            aim_point_world_m=point if authorization.gimbal != GIMBAL_NONE else None,
            aim_center_px=center if authorization.gimbal != GIMBAL_NONE else None,
            observation_box_norm=observation_box,  # type: ignore[arg-type]
            observation_confidence=confidence,
            valid_until_frame=authorization.valid_until_frame,
            reason_codes=authorization.reason_codes,
            authorization_row=authorization.row,
        )
        self._emit("authorization", "authorization", frame_id=f, accepted=True, effect_seq=effect.effect_seq,
                   inputs=inputs.as_record(), result=authorization.as_record(), geometry_reason=geo_reason)
        return effect

    def effect_current(self, effect: FrameEffect, *, frame_id: int | None = None) -> bool:
        """A12 发布前复核：版本未变、未停止、未要求重建，且（预测）未过有效期。"""
        if self.stopped or self.reinit_required or effect.version != self.version:
            return False
        if effect.valid_until_frame is not None and frame_id is not None and frame_id > effect.valid_until_frame:
            return False
        return True

    def note_control_limited(self, effect: FrameEffect) -> None:
        """到限位或被裁剪只记 `CONTROL_LIMITED`（§3.4）；C1-4：先把这一外部事实落盘为 reducer 输入，重放据此复现
        同一事件与其后序号（不删事件、不改效果）。"""
        self._input({"kind": "control_limited", "frame_id": int(effect.frame_id), "effect_seq": int(effect.effect_seq)})
        self._control_limited(int(effect.frame_id), int(effect.effect_seq))

    def _control_limited(self, frame_id: int, effect_seq: int) -> None:
        self._emit("tm_event", "control_limited", frame_id=frame_id, accepted=True, reason="CONTROL_LIMITED",
                   effect_seq=effect_seq)

    def projection(self, frame_id: int | None) -> tuple[str, str | None] | None:
        if frame_id is None:
            return None
        return self._projection(frame_id, False)


def _snapshot_record_aligned(record: Mapping[str, Any] | None, entry: HistoryEntry, phase: str) -> bool:
    """信念所存快照记录是否为本帧（传感器帧与库帧都对齐）、指定阶段、有效（C1-1）。"""
    return (
        record is not None
        and bool(record.get("valid"))
        and record.get("sensor_frame_id") == entry.frame_id
        and record.get("library_frame_id") == entry.library_frame_id
        and record.get("phase") == phase
    )


def _predicted_record(snapshot: KfSnapshot) -> dict[str, Any]:
    """内部未裁剪预测（中心、宽高、位置协方差）；只在进程内与会话日志，不进桥。"""
    return {
        "track_key": snapshot.track_key,
        "sensor_frame_id": snapshot.sensor_frame_id,
        "library_frame_id": snapshot.library_frame_id,
        "phase": snapshot.phase,
        "valid": snapshot.valid,
        "invalid_reason": snapshot.invalid_reason,
        "xc": snapshot.xywh_px[0],
        "yc": snapshot.xywh_px[1],
        "w": snapshot.xywh_px[2],
        "h": snapshot.xywh_px[3],
        "pos_cov_px2": [list(row) for row in snapshot.pos_cov_px2],
    }


def predicted_gate_radius(predicted: Mapping[str, Any], params: CaptureParams) -> float:
    """√(g_motion·λmax(S))，S = P_pos + diag((σ_p·w)², (σ_p·h)²)；无效 → ∞。"""
    if not predicted.get("valid"):
        return math.inf
    (a, b), (c, d) = predicted["pos_cov_px2"]
    s = ((a + (params.sigma_p * predicted["w"]) ** 2, b), (c, d + (params.sigma_p * predicted["h"]) ** 2))
    return math.sqrt(params.g_motion * max_eigenvalue(s))


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


# --- 重放（AC-15） --------------------------------------------------------------------


def read_inputs(path: Path) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for number, text in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not text.strip():
            continue
        try:
            record = json.loads(text)
        except json.JSONDecodeError as exception:
            raise ReplayRejected(f"tm_inputs line {number} is not JSON") from exception
        if record.get("line_sha256") != line_sha256(record):
            raise ReplayRejected(f"tm_inputs line {number} sha256 mismatch (tampered)")
        lines.append(record)
    return lines


def check_chain(lines: Sequence[Mapping[str, Any]]) -> None:
    """FASTFIX AC-13（R2-2 承接）：v2 输入逐行核链（`prev_line_sha256` = 上一行 `line_sha256`，首行为 None）与帧连续性
    （同一载体内帧行帧号逐一递增；跨 `teardown` 行只须严格递增）。任一不符 → `ReplayRejected`（删行/重排/截中段即拒）。"""
    previous_sha: str | None = None
    last_frame: int | None = None
    torn_down = False
    for number, line in enumerate(lines, start=1):
        if "prev_line_sha256" not in line or line.get("prev_line_sha256") != previous_sha:
            raise ReplayRejected(f"tm_inputs line {number} breaks the line chain (deleted, reordered or foreign line)")
        previous_sha = line["line_sha256"]
        kind = line.get("kind")
        if kind == "teardown":
            torn_down = True
        elif kind == "frame":
            frame_id = int(line["frame_id"])
            if last_frame is not None:
                if frame_id <= last_frame or (not torn_down and frame_id != last_frame + 1):
                    raise ReplayRejected(f"tm_inputs frame line {number} (frame {frame_id}) breaks frame continuity after {last_frame}")
            last_frame = frame_id
            torn_down = False


def replay_tm_inputs(inputs_path: Path, config_path: Path, fastfix_config_path: Path | None = None) -> list[dict[str, Any]]:
    """只读落盘 `tm_inputs.jsonl` 与配置文件重放 reducer（不重跑检测/KF、不读旧日志/真值/隐藏内存）；
    返回事件序列（与在线 `TargetManager.events` 逐条可比）。

    FASTFIX：v2 输入另核行间链与帧连续性；init 行带 `fastfix_params` 时须给出同一 FASTFIX 配置文件（sha 与参数逐值核对）。"""
    lines = read_inputs(inputs_path)
    if not lines or lines[0].get("kind") != "init" or lines[0].get("schema_version") not in INPUTS_SCHEMAS:
        raise ReplayRejected("tm_inputs must start with an init line")
    if lines[0].get("schema_version") == INPUTS_SCHEMA_V2:
        check_chain(lines)
    params, config_sha, config_text = load_capture_config(config_path)
    init = lines[0]
    if init.get("config_sha256") != config_sha:
        raise ReplayRejected("config file sha256 differs from the logged config_sha256")
    if params.as_record() != init.get("params"):
        raise ReplayRejected("config params differ from the logged params")
    fastfix: FastfixParams | None = None
    fastfix_sha: str | None = None
    if init.get("fastfix_params") is not None:
        if fastfix_config_path is None:
            raise ReplayRejected("tm_inputs carry FASTFIX params; the FASTFIX config file is required")
        data = Path(fastfix_config_path).read_bytes()
        fastfix_sha = hashlib.sha256(data).hexdigest()
        if fastfix_sha != init.get("fastfix_config_sha256"):
            raise ReplayRejected("FASTFIX config sha256 differs from the logged fastfix_config_sha256")
        fastfix = fastfix_params_from_document(json.loads(data.decode("utf-8")))
        if fastfix.as_record() != init.get("fastfix_params"):
            raise ReplayRejected("FASTFIX config params differ from the logged params")
    chained = init.get("schema_version") == INPUTS_SCHEMA_V2
    manager = TargetManager(
        params,
        mode=init["mode"],
        config_sha256=config_sha,
        config_text=config_text,
        inputs=InputsLog(None, chain=chained),
        ground_plane_y_m=float(init["ground_plane_y_m"]),
        maximum_ground_range_m=float(init["maximum_ground_range_m"]),
        record_init=False,
        fastfix=fastfix,
        fastfix_config_sha256=fastfix_sha,
    )
    manager._last_line_sha = init["line_sha256"]
    port = ReplayPort()
    manager.attach_port(port)
    # R1-1：端口行归属其前最近一条非端口输入行（在线时该行处理期间的端口调用紧随其后落盘）；init 之后直接出现的端口行
    # 没有可归属的调用 → 拒绝。
    segments: dict[int, list[Mapping[str, Any]]] = {0: []}
    owner = 0
    for index, line in enumerate(lines[1:], start=1):
        if line.get("kind") == "port":
            segments[owner].append(line)
        else:
            owner = index
            segments[owner] = []
    if segments[0]:
        raise ReplayInputIncomplete("port lines precede any input line that could have made those calls")
    for index, line in enumerate(lines[1:], start=1):
        kind = line.get("kind")
        if kind == "port":
            continue
        port.begin_segment(segments[index], f"input line {index + 1} ({kind})")
        manager._last_line_sha = line["line_sha256"]
        if chained:
            manager.inputs.reset_chain(line["line_sha256"])
        if line.get("config_sha256") not in (None, config_sha):
            raise ReplayRejected("tm_inputs line references a different config")
        if kind == "frame":
            history = line.get("history")
            if not isinstance(history, Mapping) or int(history.get("frame_id", -1)) != int(line["frame_id"]):
                raise ReplayRejected(f"frame line {line.get('frame_id')} lacks its history record")
            entry = entry_from_input_record(history)
            reacq_line = line.get("reacq")
            reacq_input = None
            if reacq_line is not None:
                prior_record = reacq_line.get("prior")
                reacq_input = {
                    "at_monotonic_s": reacq_line.get("at_monotonic_s"),
                    "prior": None if prior_record is None else reacq_snapshot_from_record(prior_record),
                    "prior_reason": reacq_line.get("prior_reason"),
                    "detail": reacq_line.get("detail"),
                }
            manager._frame(entry, line["batch_position"] == "newest", set(int(v) for v in line.get("ended_ids", [])),
                           reacq=reacq_input)
        elif kind == "request" and line.get("action") == "click":
            chain = line.get("chain_history")
            if not isinstance(chain, Mapping):
                raise ReplayRejected("click line lacks its chain history")
            frames = {int(key): value for key, value in chain.items()}
            manager._click_from_records(line["request_id"], line["x_px"], line["y_px"], int(line["frame_id"]),
                                        line["image_sha256"], line.get("head_frame_id"), line.get("ended_ids", []),
                                        frames, line.get("page"), line.get("actual_image_sha256"))
        elif kind == "request" and line.get("action") == "stop":
            manager._stop(line.get("request_id"), line.get("cause"))
        elif kind == "reacquire_hint":
            candidates = [HintCandidate.from_record(item) for item in line.get("candidates", [])]
            manager._prepare_reacquire(str(line["seg_end"]), bool(line.get("timing_escalation")), line.get("escalation_frame"),
                                       bool(line.get("auto_reacquire")), candidates, line["line_sha256"])
        elif kind == "reacquire_window":
            manager._open_reacquire_window(int(line["f_ready"]), float(line["m_ready"]), float(line["hz"]))
        elif kind == "reacquire_expire":
            manager._expire_reacquire(float(line["at_monotonic_s"]))
        elif kind == "reacquire_cancel":
            if manager._reacq_active():
                manager._cancel_reacquire(str(line["cause"]), line.get("frame_id"))
        elif kind == "watchdog":
            manager._watchdog(bool(line.get("stale")))
        elif kind == "release":
            manager._release(line["reason"], line.get("frame_id"), bool(line.get("cancel_task", True)))
        elif kind == "teardown":
            manager._teardown(line["reason"])
        elif kind == "language_task":
            selector = line["selector"]
            manager._accept_language_task(
                LanguageCompatSelector(int(selector["designation_id"]), tuple(selector["box_k"]), int(selector["k"])),
                line.get("frame_id"),
            )
        elif kind == "commit_request":
            selector = line.get("selector")
            manager._replaying_commit = True
            try:
                manager.commit_binding(
                    origin=line["origin"],
                    track_key=int(line["track_key"]),
                    expected_version=int(line["expected_version"]),
                    source_frame=line.get("source_frame"),
                    commit_frame=line.get("commit_frame"),
                    evidence=line.get("evidence"),
                    selector=None if selector is None else LanguageCompatSelector(
                        int(selector["designation_id"]), tuple(selector["box_k"]), int(selector["k"])
                    ),
                    coasting_designation_id=line.get("coasting_designation_id"),
                )
            finally:
                manager._replaying_commit = False
        elif kind == "control_limited":
            manager._control_limited(int(line["frame_id"]), int(line["effect_seq"]))
        else:
            raise ReplayRejected(f"unknown tm_inputs line kind {kind!r}")
        port.end_segment()
    return manager.events


def comparable_events(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """事件比较口径：全部字段（含 event_seq/effect_seq/所引输入行 sha）。"""
    return [dict(event) for event in events]


def main(argv: Sequence[str] | None = None) -> int:
    """`python -m controller.target_manager replay <tm_inputs.jsonl> <config.json>` → 事件 JSONL 到标准输出。"""
    import argparse  # noqa: PLC0415
    import sys  # noqa: PLC0415

    parser = argparse.ArgumentParser(description="P1-ENG-CAPTURE-001 AC-15：只读落盘输入重放目标管理器")
    sub = parser.add_subparsers(dest="command", required=True)
    replay_parser = sub.add_parser("replay")
    replay_parser.add_argument("inputs", type=Path)
    replay_parser.add_argument("config", type=Path)
    replay_parser.add_argument("fastfix_config", type=Path, nargs="?", default=None)
    arguments = parser.parse_args(argv)
    try:
        events = replay_tm_inputs(arguments.inputs, arguments.config, arguments.fastfix_config)
    except ReplayRejected as exception:
        print(f"REPLAY_REJECTED: {exception}", file=sys.stderr)
        return 3
    for event in events:
        sys.stdout.write(canonical_json(event) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
