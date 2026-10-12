#!/usr/bin/env python3
"""S0 冻结常量（提案 §2.1）。

提案 §2.3–§2.7、§2.11、§5 的全部数值与词表即合同本体；本模块把它们逐字
落为 `runtime/dist-data/contract.json` 并 SHA-256 冻结。任何常量改动 =
提案修订 + 重新接受，实现侧没有「实现时再定」的自由参数。

BC-DATA-1：§5.2 的 F1–F4 数值与全部分母自 round 3 起冻结，任何实测结果、
审计失败或 atom 合并均不得回调——本模块是该冻结的唯一权威副本。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.dist_data import roots

CONTRACT_VERSION = "p1-vlm-data-001-contract/v1"
WORK_ID = "P1-VLM-DATA-001"
ONTOLOGY_VERSION = "ontology/v1"

# --- §2.6 class 冻结映射表（prefab 前缀 → Tier-1 类别词） -----------------
CLASS_MAP: dict[str, str] = {
    "Ambulance": "ambulance",
    "Bus": "bus",
    "Car": "car",
    "Container": "container truck",
    "Pick up Truck": "pickup truck",
    "Police Car": "police car",
    "SUV": "suv",
    "Taxi": "taxi",
    "Truck": "truck",
}
# 实例名按 prefab 前缀机械归类；前缀求值按长度降序，避免 "Car" 抢
# "Container"/"Police Car"、"Truck" 抢 "Pick up Truck"。
CLASS_PREFIX_ORDER: tuple[str, ...] = tuple(
    sorted(CLASS_MAP, key=lambda prefix: (-len(prefix), prefix))
)
CLASS_WORDS: tuple[str, ...] = tuple(sorted(set(CLASS_MAP.values())))
VEHICLE_NAME_PREFIX = "Vehicle_"

# --- §2.6 color 冻结词表与判定带 -----------------------------------------
COLOR_WORDS: tuple[str, ...] = (
    "white",
    "black",
    "gray",
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "purple",
    "brown",
)
# 无彩判定（HSV，S/V ∈ [0,1]）。
COLOR_ACHROMATIC = {
    "black_value_below": 0.15,
    "white_saturation_below": 0.15,
    "white_value_above": 0.85,
    "gray_saturation_below": 0.15,
}
# 色相带，单位度，[lo, hi) 半开；red 带跨 360°/0° 环绕。
COLOR_HUE_BANDS: tuple[tuple[str, float, float], ...] = (
    ("red", 345.0, 15.0),
    ("orange", 15.0, 45.0),
    ("yellow", 45.0, 70.0),
    ("green", 70.0, 170.0),
    ("blue", 170.0, 260.0),
    ("purple", 260.0, 300.0),
)
# BC-DATA-8.4（接受轮 4 冻结）：ref 名词短语的颜色词按**升序**枚举。
# `COLOR_WORDS` 是 §2.6 的词表序（判定带顺序），两者不同，不可混用。
COLOR_WORDS_ASCENDING: tuple[str, ...] = tuple(sorted(COLOR_WORDS))
COLOR_BROWN_FROM_ORANGE_VALUE_BELOW = 0.55
COLOR_MAIN_BAND_MIN_SHARE = 0.5
COLOR_SAMPLE_FRAME_COUNT = 5  # K=5 最近观测帧
COLOR_BOX_INSET_FRACTION = 0.2  # visible 框每边内缩 20%

# --- §2.4 投影合同常量 ----------------------------------------------------
NEAR_CLIP_Z_M = 0.3
MIN_VISIBLE_SIDE_PX = 12
TRUNCATION_VISIBLE_AREA_RATIO = 0.25
THETA_OCC = 0.5
PROJECTION_FOCAL_TOLERANCE_PX = 0.5
OBJECT_STATUSES: tuple[str, ...] = (
    "OK",
    "NOT_IN_VIEW",
    "TOO_SMALL",
    "TRUNCATED",
    "EXCLUDED_OCCLUDED",
    "PHANTOM",
)

# --- §2.4 站位簇分箱（F2/F3 的全局键） ------------------------------------
STATION_POSITION_BIN_M = 2.0
STATION_AZIMUTH_BIN_DEG = 15.0
STATION_ELEVATION_BANDS: tuple[tuple[float, float], ...] = (
    (0.0, 30.0),
    (30.0, 60.0),
    (60.0, 90.0),
)

# --- §2.3 历史布局交叉验证阈值 -------------------------------------------
CROSSCHECK_MIN_PAIRS = 50
CROSSCHECK_CENTER_HIT_MIN_RATIO = 0.90
CROSSCHECK_IOU_MEDIAN_MIN = 0.5
# 无逐帧目标真值族：扫掠代理区投影与视口交面积 ≥ (12 px)² 即 TARGET_UNBOUNDED。
TARGET_SWEEP_MIN_AREA_PX2 = float(MIN_VISIBLE_SIDE_PX * MIN_VISIBLE_SIDE_PX)

# --- §2.5 切分常量 --------------------------------------------------------
PHASH_RESIZE = 32
PHASH_DCT_KEEP = 8
PHASH_BITS = 64
PHASH_NEAR_DUPLICATE_HAMMING = 8
HELDOUT_SEED = "P1-VLM-DATA-001/heldout/v1"
SPLIT_SEED = "P1-VLM-DATA-001/split/v1"
AUDIT_SEED_TEMPLATE = "P1-VLM-DATA-001/audit/{audit}/panel-{panel}"
SPLIT_MIN_ATOMS = 2
SPLIT_MAX_ATOMS = 20
SPLIT_TEST_FRAME_TARGET_DENOMINATOR = 5  # |5·test 帧 − 总 floor-eligible 帧|
DEV_FRACTION_NUMERATOR = 3  # 20·dev_frames ≥ 3·total（15%）
DEV_FRACTION_DENOMINATOR = 20

# --- §2.6 static relations 族定义 -----------------------------------------
RELATION_TYPES: tuple[str, ...] = (
    "nearest_to",
    "viewer_left_of",
    "viewer_right_of",
    "on_route_side",
)
NEAREST_TO_DOMINANCE_RATIO = 0.8  # d1 ≤ 0.8·d2 才有效
VIEWER_SIDE_MIN_SEPARATION_PX = 40.0

# --- §2.7 审计协议（BC-DATA-5） -------------------------------------------
AUDIT_PANEL_COUNT = 3
AUDIT_MAX_ATTEMPTS = 3
AUDIT_MAX_CATALOG_SUPERSESSIONS = 2
AUDIT_A1_CLASS_MAP_CHECKLIST = 9  # 固定穷举，不属三互斥 panel
AUDIT_A1_CLASS_MAP_MAX_FAILURES = 0
AUDIT_A1_CLASS_CROPS = 20
AUDIT_A1_CLASS_CROPS_MIN_PER_CLASS = 2
AUDIT_A1_CLASS_CROP_MAX_FAILURES = 1
AUDIT_A1_INSTANCE_COLOR_CROPS = 25
AUDIT_A1_INSTANCE_COLOR_MAX_FAILURES = 1
AUDIT_A2_PANEL_SAMPLES = 200
AUDIT_A2_STRATUM_BASE = 16
AUDIT_A2_STRATUM_REMAINDER = 8
AUDIT_A2_REJECT_RATE = 0.05  # ≤ floor(0.05 × 实际样本数)
AUDIT_A2_FALSE_INCLUDE_RATE = 0.02  # ≤ floor(0.02 × panel 内 OK 样本数)
AUDIT_A2_OVERSHOOT_TOLERANCE = 0.35  # 人工 gold 规则 (ii)
AUDIT_A3_PANEL_SAMPLES = 100
AUDIT_A3_STRATUM_BASE = 25
AUDIT_A3_MAX_FAILURES = 0
AUDIT_TERMINALS: tuple[str, ...] = (
    "AUDIT_EXHAUSTED_FAIL",
    "AUDIT_PANEL_CAPACITY_INSUFFICIENT",
)

# --- §2.2 用途类闭集与资格（附录 A 表） -----------------------------------
USAGE_CLASSES: tuple[str, ...] = (
    "VALID_FORMAL",
    "VALID_SCOUTING_CLOSED",
    "VALID_PARENT_HOLD",
    # P1-VLM-DATA-002 §2.2 第 1 条：巡览采集的新用途类。与其余 floor 类
    # 相邻，故本行插入不改变任何既有类之间的相对表序（= lineage primary
    # 优先级）。
    "VALID_SURVEY",
    "PROTOCOL_INVALID",
    "VOID_TRIAL_HOLD",
    "SMOKE",
    "CALIBRATION",
    "DIAGNOSTIC_HOLD",
    "UNRELEASED_PLAY_HOLD",
    "PREVIEW",
    "DERIVED_OVERLAY",
    "DOC_COPY",
    "THIRD_PARTY_ASSET",
    # BC-DATA-6（接受轮 4）：SCENE-006 旧探针 jpg 渲染的是已由 F23 否定保真的
    # 灰色替身，只盘点。表序即 lineage primary 优先级，故排在全部 mother/floor
    # 类之后、与提案 §2.2 表行序一致。
    "INVALID_RENDER_PROBE",
    "PROBE_TRUTH_ONLY",
)
# 计 F 下限 / 可进 test 侧的用途类（§5.1 floor-eligible 的用途类条件）。
FLOOR_USAGE_CLASSES: frozenset[str] = frozenset(
    {"VALID_FORMAL", "VALID_SCOUTING_CLOSED", "VALID_PARENT_HOLD", "VALID_SURVEY"}
)
# 可进训练母集（含 train/dev 扩增），但不计 F 下限、不进 test 侧。
TRAIN_AUGMENT_USAGE_CLASSES: frozenset[str] = frozenset(
    {"PROTOCOL_INVALID", "VOID_TRIAL_HOLD", "SMOKE", "CALIBRATION"}
)
MOTHER_USAGE_CLASSES: frozenset[str] = FLOOR_USAGE_CLASSES | TRAIN_AUGMENT_USAGE_CLASSES

INVENTORY_DECISIONS: tuple[str, ...] = (
    "INCLUDED",
    "INVENTORY_ONLY",
    "EXCLUDED_UNBOUND_SCENARIO",
    "EXCLUDED_NO_POSE",
    "EXCLUDED_THIRD_PARTY",
    "EXCLUDED_DERIVED",
    "EXCLUDED_DIAGNOSTIC_CHANNEL",
    "EXCLUDED_UNRELEASED",
)

# --- §5.2 预注册下限（BC-DATA-1 冻结，不因任何实测结果回调） ---------------
FLOORS: dict[str, Any] = {
    "F1": {
        "definition": "class+color 双验证对象数 / 101（对象级；验证 = S5 判定 + A1 通过）",
        "min_objects": 60,
        "min_classes_with_dual_verified": 6,
        "object_denominator": 101,
    },
    "F2": {
        "definition": "站位簇总数（floor-eligible）",
        "min_global": 40,
        "min_test": 8,
    },
    "F3": {
        "definition": "属性唯一单元 (对象, 站位簇)",
        "min_train_dev": 60,
        "min_test": 25,
        "min_test_heldout_units": 8,
        "min_train_classes": 5,
        "min_test_classes": 4,
    },
    "F4": {
        "definition": "统计簇 (atom_id, 对象)",
        "min_train_dev": 25,
        "min_test": 10,
    },
}

# --- §2.8 / BC-DATA-2 终态闭集 --------------------------------------------
GATE_TERMINALS: tuple[str, ...] = (
    "INSUFFICIENT_SYMBOLIC_GROUNDING_DATA",
    "SPLIT_ENUMERATION_LIMIT_EXCEEDED",
)

# --- §2.11 verifier 合同闭集 ----------------------------------------------
VERIFIER_TIERS: tuple[str, ...] = ("mechanical", "model")
VERIFIER_VERDICTS: tuple[str, ...] = ("PASS", "REJECT")
VERIFIER_REJECT_REASONS: tuple[str, ...] = (
    "UNPARSEABLE",
    "ONTOLOGY_VIOLATION",
    "AST_MISMATCH",
    "EXECUTION_NOT_UNIQUE",
    "EXECUTION_WRONG_TARGET",
    "FORMAT",
)
# Tier-1 闭词表同义折叠：折叠表 = 恒等 + 冻结的别名表（当前别名表为空，
# renderer 词表即闭包；新增别名 = 提案修订）。
CANONICAL_ALIASES: dict[str, str] = {}

# --- BC-DATA-9（接受轮 5）：动态目标的版本化冻结构造源权威 -----------------
# 目标不在场景文件中，而由 `TetheredScenarioBootstrap.CreateTarget` 的单一
# 运行时构造链生成；F23 后 `TargetVisualFactory` 的几何与红色字面量由独立
# EditMode/分析器 oracle 冻结，git 历史证明 M0 至今字面量等价，再加用户逐字
# 事实认定「这是一辆纯色的红车」。这是**已版本化的构造源权威**，不是 AR2-3
# 所禁的读当前 Unity 场景/config。
DYNAMIC_TARGET_SOURCE_AUTHORITY = (
    "TetheredScenarioBootstrap.CreateTarget → AddCarVisual → "
    "TargetVisualFactory.AddTargetVisual（F23 冻结构造源 + 独立 oracle + "
    "M0 至今字面量历史等价 + 用户逐字认定）"
)
DYNAMIC_TARGET_SOURCE_VERIFIED_FIELDS: dict[str, str] = {"class": "car", "color": "red"}
# --- 动态目标 schema 闭集（P1-VLM-DATA-002 §2.2 第 3 条） ------------------
# 既有三种逐字不变：`m3` / `scouting` 是附录 A 逐帧真值 join 的两个 schema
# 族（`roots.TRUTH_JOIN` 第三列），`sweep_proxy` 是「无逐帧目标真值的族」
# 走全路线扫掠代理的分支（`build_catalog` 内 `schema_family is None`，
# 此前只有分支没有名字，这里给它一个名字，判定逻辑一字未改）。
# `target_parked` 为本批新增：目标零速停放，位姿由归档场景字节的
# `route_world_m[0]` 与冻结的 +z 朝向精确派生，不需要逐帧真值文件。
TARGET_SCHEMA_M3 = "m3"
TARGET_SCHEMA_SCOUTING = "scouting"
TARGET_SCHEMA_SWEEP_PROXY = "sweep_proxy"
TARGET_SCHEMA_PARKED = "target_parked"
DYNAMIC_TARGET_SCHEMAS: tuple[str, ...] = (
    TARGET_SCHEMA_M3,
    TARGET_SCHEMA_SCOUTING,
    TARGET_SCHEMA_SWEEP_PROXY,
    TARGET_SCHEMA_PARKED,
)
# §2.1(f) 冻结构造 AABB 的局部半长/偏移（目标前向 = 世界 +z，旋转恒为单位
# 四元数，故局部框直接就是世界轴对齐框）。
PARKED_TARGET_LOCAL_X_M: tuple[float, float] = (-1.0, 1.0)
PARKED_TARGET_LOCAL_Y_M: tuple[float, float] = (0.0, 1.55)
PARKED_TARGET_LOCAL_Z_M: tuple[float, float] = (-2.0, 2.0)
PARKED_TARGET_FORWARD_WORLD: tuple[float, float, float] = (0.0, 0.0, 1.0)
# 目标永不属于目录、永不可指称，也**不计入 F1 的 101 个对象**。
DYNAMIC_TARGET_REFERABLE = False


def dynamic_target_fields(source_bound: bool) -> dict[str, str | None]:
    """源身份可证绑定到同一冻结构造合同时继承 `car`/`red`，否则逐字段 `UNKNOWN`。

    BC-DATA-9.1：任一字段无法绑定时该字段单独退回 `UNKNOWN` 通配冲突，
    **不得**用路径名、当前场景或当前 config 补齐。
    """
    if source_bound:
        return dict(DYNAMIC_TARGET_SOURCE_VERIFIED_FIELDS)
    return {"class": None, "color": None}


# --- S0 钉死的外部基础几何 -------------------------------------------------
BASE_GEOMETRY_PATH = "docs/evidence/P1-M3-BODY-001-scene-geometry.json"
BASE_GEOMETRY_SHA256 = (
    "77834bd3e52e6ed937b1f54f05195f5585fc4104ca98389d9bd28f4d02ef9c13"
)
BASE_GEOMETRY_SCHEMA = "p1-m3-body-001-scene-geometry/v1"
BASE_GEOMETRY_INSTANCE_COUNT = 779
BASE_GEOMETRY_VEHICLE_COUNT = 101

# 工件根（gitignored）。
ARTIFACT_ROOT = "runtime/dist-data"


def class_for_scene_object(scene_object_name: str) -> str | None:
    """按 §2.6 冻结映射表把实例名机械归类；非车辆返回 None。

    `_colorNN` 是资产皮肤代号，不是颜色（章程 R2C-6），此处不参与归类。
    """
    if not scene_object_name.startswith(VEHICLE_NAME_PREFIX):
        return None
    remainder = scene_object_name[len(VEHICLE_NAME_PREFIX) :]
    for prefix in CLASS_PREFIX_ORDER:
        if remainder == prefix or remainder.startswith(prefix + "_") or remainder.startswith(
            prefix + " "
        ):
            return CLASS_MAP[prefix]
    return None


def skin_code_for_scene_object(scene_object_name: str) -> str:
    """取实例的 (prefab, 皮肤代号) 组键中的皮肤代号部分。

    形如 `Vehicle_Bus_color02 (1)` → `color02`；无皮肤代号者返回空串。
    """
    if not scene_object_name.startswith(VEHICLE_NAME_PREFIX):
        return ""
    remainder = scene_object_name[len(VEHICLE_NAME_PREFIX) :]
    base = remainder.split(" (")[0]
    if "_color" in base:
        return base.split("_")[-1]
    return ""


def prefab_base_name(scene_object_name: str) -> str:
    """去掉 Unity 的 ` (n)` 实例后缀，得到 prefab 基名。"""
    return scene_object_name.split(" (")[0]


def color_group_key(scene_object_name: str) -> str:
    """§2.6 一致性约束的组键 = (prefab, 皮肤代号)。"""
    return f"{prefab_base_name(scene_object_name)}|{skin_code_for_scene_object(scene_object_name)}"


def held_out_count(class_instance_count: int) -> int:
    """§2.5 留出物体整数算术 `k_c = max(1, (3·n_c + 5) // 10)`。"""
    if class_instance_count <= 0:
        return 0
    return max(1, (3 * class_instance_count + 5) // 10)


def hue_band(hue_deg: float) -> str | None:
    """按 §2.6 色相带返回带名；落在未分配区间返回 None。"""
    hue = hue_deg % 360.0
    for name, low, high in COLOR_HUE_BANDS:
        if low <= high:
            if low <= hue < high:
                return name
        elif hue >= low or hue < high:  # red 带环绕 360°/0°
            return name
    return None


# --- P1-VLM-DATA-002 §2.2 第 4 条：S0 attempt-2 顶层键 allowlist ------------
# 信封侧允许不同的键（`ArtifactStore.write` 的 envelope，不是 payload）。
SUPERSESSION_ENVELOPE_KEYS: tuple[str, ...] = (
    "attempt",
    "supersedes",
    "supersession_reason",
)
# payload 侧允许与 attempt-1 canonical bytes 不同的**全部**顶层键，逐字列出
# （§2.2 第 4 条：「键名以 contract.json 实际顶层键为准，实现逐字列出」）：
#   - `root_manifest`：附录 A 运行根清单的 canonical 投影，attempt-1 无此键；
#   - `usage_classes`：用途类闭集键，新增 `VALID_SURVEY`；
#   - `dynamic_target`：目标 schema 闭集键，新增 `target_parked`；
#   - `survey_sessions`：S0 会话表，attempt-1 无此键；
#   - `survey_acquisition`：BC-SURVEY-14 的采集协议投影，attempt-1 无此键。
# BC-SURVEY-7 裁定了「根清单键」：它**必须**是独立顶层键，不得以
# `usage_classes` 代替根 pattern/映射的哈希冻结。差异键集合恰为本元组，
# 由 `ContractAllowlistTest` 以冻结的 attempt-1 字节夹具逐键比对。
# BC-SURVEY-14 在差异集合上取代 BC-SURVEY-7：差异键恰为**五**个。
CONTRACT_PAYLOAD_SUPERSESSION_ALLOWLIST: tuple[str, ...] = (
    "root_manifest",
    "usage_classes",
    "dynamic_target",
    "survey_sessions",
    "survey_acquisition",
)

SURVEY_SESSION_ROW_KEYS: tuple[str, ...] = (
    "session_id",
    "plan_identity",
    "archive_root",
    "tree_sha256",
    "selection_sha256",
    "manifest_sha256",
    "scenario_sha256",
    "plan_sha256",
    "frame_count",
    "close_terminal",
)


# --- BC-SURVEY-14：完整采集协议的 canonical 投影 ---------------------------
# 投影是**自动枚举**的：本模块每一个公开 `SURVEY_*` 名字都进块。新增一个受管
# 常量却漏投影因此不可能发生——除非把它命名成别的前缀，而
# `test_every_public_survey_constant_is_projected` 正是为此把 `SURVEY_*` 与块内
# 键逐一对齐。可调用对象与私有名不进块。
SURVEY_ACQUISITION_VERSION = "p1-vlm-data-002-acquisition/v1"


def _jsonable(value: Any) -> Any:
    """把常量转成 canonical JSON 可写的形状（元组/frozenset → 有序列表）。"""
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, frozenset):
        return sorted(_jsonable(item) for item in value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    raise SurveyContractError(
        f"采集协议常量不可 canonical 投影：{type(value).__name__}"
    )


def survey_acquisition_constant_names() -> tuple[str, ...]:
    """本模块全部公开、非可调用的 `SURVEY_*` 常量名（升序）。"""
    names = []
    for name, value in sorted(globals().items()):
        if not name.startswith("SURVEY_") or name.startswith("_"):
            continue
        if callable(value):
            continue
        names.append(name)
    return tuple(names)


def survey_acquisition() -> dict[str, Any]:
    """BC-SURVEY-14：采集协议的 canonical 投影，写进 S0 并逐环钉住。"""
    return {
        "schema_version": SURVEY_ACQUISITION_VERSION,
        "work_id": SURVEY_WORK_ID,
        "constants": {
            name: _jsonable(globals()[name])
            for name in survey_acquisition_constant_names()
        },
    }


def survey_acquisition_sha256() -> str:
    """当前采集协议投影的 canonical bytes 摘要（plan/manifest 钉的就是它）。"""
    import hashlib
    import json as _json

    text = _json.dumps(
        survey_acquisition(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256((text + "\n").encode("utf-8")).hexdigest()


def assert_survey_acquisition_pin(declared: Any, *, where: str) -> str:
    """核对一个钉子与**当前**投影；漂移即 fail-closed。"""
    current = survey_acquisition_sha256()
    if not isinstance(declared, str) or len(declared) != 64:
        raise SurveyContractError(
            f"{where}：采集协议钉子不是 64 位十六进制：{declared!r}"
        )
    if declared != current:
        raise SurveyContractError(
            f"{where}：采集协议已漂移——钉住 {declared}，当前投影 {current}。"
            "受管常量改动后必须重新发布 plan/manifest/S0，不得在旧钉子下继续。"
        )
    return current


def contract_document(survey_sessions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """S0 合同文档：全部冻结常量的可哈希快照。

    `survey_sessions` **无条件写入**（缺省为空表）。BC-SURVEY-14 冻结「相对
    attempt-1 的差异键恰为五键」，把该键挂在「有没有巡览归档」上会让零归档时
    的真实 attempt-2 只差四键，直接违反该条。

    BC-SURVEY-7 起本函数**不再能复现 attempt-1 的字节**：`root_manifest`
    是无条件写入的顶层键。这是设计使然——attempt-1 的既有字节由 create-once
    与 `tests/fixtures/p1-vlm-data-001-contract-attempt-1.json` 冻结，
    正因如此 allowlist 回归必须拿那份夹具做「前」侧，而不是拿本函数生成两侧。
    `root_manifest` 不得挂在 `survey_sessions is not None` 上：生产 driver 传
    `sessions or None`，零巡览归档时该参数即为 `None`，挂上去会让真实的
    attempt-2 完全不带根清单。
    """
    document: dict[str, Any] = {
        "schema_version": CONTRACT_VERSION,
        "work_id": WORK_ID,
        "ontology_version": ONTOLOGY_VERSION,
        "class_map": dict(CLASS_MAP),
        "class_words": list(CLASS_WORDS),
        "color": {
            "words": list(COLOR_WORDS),
            "words_ascending": list(COLOR_WORDS_ASCENDING),
            "achromatic": dict(COLOR_ACHROMATIC),
            "hue_bands": [
                {"name": name, "low_deg": low, "high_deg": high}
                for name, low, high in COLOR_HUE_BANDS
            ],
            "brown_from_orange_value_below": COLOR_BROWN_FROM_ORANGE_VALUE_BELOW,
            "main_band_min_share": COLOR_MAIN_BAND_MIN_SHARE,
            "sample_frame_count": COLOR_SAMPLE_FRAME_COUNT,
            "box_inset_fraction": COLOR_BOX_INSET_FRACTION,
        },
        "projection": {
            "near_clip_z_m": NEAR_CLIP_Z_M,
            "min_visible_side_px": MIN_VISIBLE_SIDE_PX,
            "truncation_visible_area_ratio": TRUNCATION_VISIBLE_AREA_RATIO,
            "theta_occ": THETA_OCC,
            "focal_tolerance_px": PROJECTION_FOCAL_TOLERANCE_PX,
            "object_statuses": list(OBJECT_STATUSES),
        },
        "station_bins": {
            "position_bin_m": STATION_POSITION_BIN_M,
            "azimuth_bin_deg": STATION_AZIMUTH_BIN_DEG,
            "elevation_bands_deg": [list(band) for band in STATION_ELEVATION_BANDS],
        },
        "cross_check": {
            "min_pairs": CROSSCHECK_MIN_PAIRS,
            "center_hit_min_ratio": CROSSCHECK_CENTER_HIT_MIN_RATIO,
            "iou_median_min": CROSSCHECK_IOU_MEDIAN_MIN,
            "target_sweep_min_area_px2": TARGET_SWEEP_MIN_AREA_PX2,
        },
        "splits": {
            "phash": {
                "resize": PHASH_RESIZE,
                "dct_keep": PHASH_DCT_KEEP,
                "bits": PHASH_BITS,
                "near_duplicate_hamming": PHASH_NEAR_DUPLICATE_HAMMING,
            },
            "heldout_seed": HELDOUT_SEED,
            "split_seed": SPLIT_SEED,
            "min_atoms": SPLIT_MIN_ATOMS,
            "max_atoms": SPLIT_MAX_ATOMS,
            "test_frame_target_denominator": SPLIT_TEST_FRAME_TARGET_DENOMINATOR,
            "dev_fraction": [DEV_FRACTION_NUMERATOR, DEV_FRACTION_DENOMINATOR],
        },
        "relations": {
            "types": list(RELATION_TYPES),
            "nearest_to_dominance_ratio": NEAREST_TO_DOMINANCE_RATIO,
            "viewer_side_min_separation_px": VIEWER_SIDE_MIN_SEPARATION_PX,
        },
        "audit": {
            "seed_template": AUDIT_SEED_TEMPLATE,
            "panel_count": AUDIT_PANEL_COUNT,
            "max_attempts": AUDIT_MAX_ATTEMPTS,
            "max_catalog_supersessions": AUDIT_MAX_CATALOG_SUPERSESSIONS,
            "a1": {
                "class_map_checklist": AUDIT_A1_CLASS_MAP_CHECKLIST,
                "class_map_max_failures": AUDIT_A1_CLASS_MAP_MAX_FAILURES,
                "class_crops": AUDIT_A1_CLASS_CROPS,
                "class_crops_min_per_class": AUDIT_A1_CLASS_CROPS_MIN_PER_CLASS,
                "class_crop_max_failures": AUDIT_A1_CLASS_CROP_MAX_FAILURES,
                "instance_color_crops": AUDIT_A1_INSTANCE_COLOR_CROPS,
                "instance_color_max_failures": AUDIT_A1_INSTANCE_COLOR_MAX_FAILURES,
            },
            "a2": {
                "panel_samples": AUDIT_A2_PANEL_SAMPLES,
                "stratum_base": AUDIT_A2_STRATUM_BASE,
                "stratum_remainder": AUDIT_A2_STRATUM_REMAINDER,
                "reject_rate": AUDIT_A2_REJECT_RATE,
                "false_include_rate": AUDIT_A2_FALSE_INCLUDE_RATE,
                "overshoot_tolerance": AUDIT_A2_OVERSHOOT_TOLERANCE,
            },
            "a3": {
                "panel_samples": AUDIT_A3_PANEL_SAMPLES,
                "stratum_base": AUDIT_A3_STRATUM_BASE,
                "max_failures": AUDIT_A3_MAX_FAILURES,
            },
            "terminals": list(AUDIT_TERMINALS),
        },
        # BC-SURVEY-7：附录 A 运行根清单的 canonical 投影，无条件写入。
        "root_manifest": roots.root_manifest(),
        # BC-SURVEY-14：完整采集协议的 canonical 投影，无条件写入。
        "survey_acquisition": survey_acquisition(),
        "usage_classes": {
            "closed_set": list(USAGE_CLASSES),
            "floor": sorted(FLOOR_USAGE_CLASSES),
            "train_augment": sorted(TRAIN_AUGMENT_USAGE_CLASSES),
            "mother": sorted(MOTHER_USAGE_CLASSES),
        },
        "inventory_decisions": list(INVENTORY_DECISIONS),
        "floors": FLOORS,
        "gate_terminals": list(GATE_TERMINALS),
        "verifier": {
            "tiers": list(VERIFIER_TIERS),
            "verdicts": list(VERIFIER_VERDICTS),
            "reject_reasons": list(VERIFIER_REJECT_REASONS),
            "canonical_aliases": dict(CANONICAL_ALIASES),
        },
        "dynamic_target": {
            "source_authority": DYNAMIC_TARGET_SOURCE_AUTHORITY,
            "source_verified_fields": dict(DYNAMIC_TARGET_SOURCE_VERIFIED_FIELDS),
            "referable": DYNAMIC_TARGET_REFERABLE,
            "unbound_fallback": "per-field UNKNOWN",
            # P1-VLM-DATA-002 §2.2 第 3 条：动态目标 schema 闭集。
            "schemas": list(DYNAMIC_TARGET_SCHEMAS),
            "parked": {
                "local_x_m": list(PARKED_TARGET_LOCAL_X_M),
                "local_y_m": list(PARKED_TARGET_LOCAL_Y_M),
                "local_z_m": list(PARKED_TARGET_LOCAL_Z_M),
                "forward_world": list(PARKED_TARGET_FORWARD_WORLD),
            },
        },
        "base_geometry": {
            "path": BASE_GEOMETRY_PATH,
            "sha256": BASE_GEOMETRY_SHA256,
            "schema_version": BASE_GEOMETRY_SCHEMA,
            "instance_count": BASE_GEOMETRY_INSTANCE_COUNT,
            "vehicle_count": BASE_GEOMETRY_VEHICLE_COUNT,
        },
    }
    document["survey_sessions"] = list(survey_sessions or [])
    return document


def write_contract(
    repo_root: Path,
    attempt: str = "attempt-1",
    *,
    survey_sessions: list[dict[str, Any]] | None = None,
    supersedes: str | None = None,
    supersession_reason: str | None = None,
):
    """把 S0 合同写成 create-once 工件 `contract@attempt-k`。"""
    from tools.dist_data import artifacts

    store = artifacts.ArtifactStore(repo_root)
    return store.write(
        "contract",
        attempt,
        contract_document(survey_sessions),
        stage=0,
        supersedes=supersedes,
        supersession_reason=supersession_reason,
    )


# --- P1-VLM-DATA-002 §2.1(h)/§2.2 第 4 条：巡览归档树与 S0 会话表 ----------
# 归档树的成员域与摘要是本批的**合同**，故与其余 S0 常量同住本模块：
# `tools/run_grounding_survey.py` 的 `close`/`verify` 与这里的会话表构建
# 共用同一实现，两处不可能各算各的（层次方向始终是 tool → dist_data）。
SURVEY_MANIFEST_SCHEMA = "p1-vlm-survey-manifest/v1"
SURVEY_SELECTION_SCHEMA = "p1-vlm-survey-selection/v1"
SURVEY_TREE_SCHEMA = "p1-vlm-survey-tree/v1"
SURVEY_COMPLETION_SCHEMA = "p1-vlm-survey-completion/v1"
SURVEY_WORK_ID = "P1-VLM-DATA-002"

# §2.1(h)：`tree.json` 自身不属成员域；`completion.json` 在归档外。
SURVEY_TREE_EXCLUDED_NAMES: frozenset[str] = frozenset({"tree.json"})

# §2.1(e)：逐帧用途类闭集（`selection.json` 的 `class` 列）。
SURVEY_FRAME_CLASSES: tuple[str, ...] = ("VALID_SURVEY", "PROTOCOL_INVALID")

# §2.1(h)：`close` 终态闭集。
SURVEY_CLOSE_TERMINALS: tuple[str, ...] = (
    "CLOSED_OK",
    "CLOSED_PROTOCOL_INVALID",
    "CLOSED_ZERO_FRAMES",
    "CLOSE_INCOMPLETE_STAGING",
    "CLOSE_RESIDUE_RECOVERED",
    "CLOSE_TREE_MISMATCH",
)

class SurveyContractError(RuntimeError):
    """巡览归档合同违反（一律 fail-closed）。"""


# --- BC-SURVEY-14：驱动器侧会影响正式结果的常量，全部收进合同 ---------------
# 「不得留下由当前模块字面量静默决定正式结果的旁路」：身份、资源信封、安全、
# 计划、逐帧分类与证人/S2 判定所依赖的每一个数都必须住在这里，并被
# `survey_acquisition()` 投影进 S0 的哈希面。
SURVEY_DRIVE_LOG_SCHEMA = "p1-vlm-survey-drive-log/v1"
SURVEY_ACTIVE_MARKER_SCHEMA = "p1-vlm-survey-active/v1"
SURVEY_CONTROL_PROTOCOL = "tethered-drone-control/v1"
SURVEY_FRAME_MANIFEST_SCHEMA = "tethered-frame-manifest/v1"
SURVEY_SENSOR_FRAME_SCHEMA = "tethered-sensor-frame/v3"
SURVEY_ROAD_AUDIT_SCHEMA = "p1-scene-road-audit/v1"
SURVEY_ROAD_AUDIT_CLEAR_STATUS = "CLEAR"
SURVEY_DEFAULT_SCENARIO_PATH = "config/scenario.default.json"
SURVEY_ACTIVE_MARKER_FILENAME = "p1-vlm-survey-active.json"
SURVEY_RUNTIME_OVERRIDE_FILENAME = "scenario_config.json"
# §6 授权 #1/#2 的信封上限（BC-SURVEY-6：缺项按 0，越界回用户）。
SURVEY_MAX_FORMAL_PLAY = 10
SURVEY_MAX_PLAN_IDENTITIES = 10
SURVEY_MAX_DIAGNOSTIC_PLAY = 3
# §8 表 2：BC-SURVEY-9 只冻结坐标、序号与使用顺序。
SURVEY_ANCHOR_TABLE: tuple[tuple[int, float, float], ...] = (
    (1, 206.0, 55.0),
    (2, 41.0, 58.0),
    (3, 194.0, 163.0),
    (4, 38.0, 163.0),
    (5, 95.0, -2.0),
    (6, 113.0, 163.0),
    (7, 182.0, 25.0),
    (8, -10.0, -2.0),
    (9, 62.0, 79.0),
    (10, 191.0, 193.0),
)
SURVEY_ANCHOR_Y_M = 0.2
SURVEY_ANCHOR_CANDIDATE_GRID_M = 3.0
SURVEY_ANCHOR_COVERAGE_RADIUS_M = 55.0
SURVEY_BIRTH_HEIGHT_M = 25.0
# BC-SURVEY-12 的连通性住在合同里，并由 `red_components` **实际读取**。
SURVEY_WITNESS_CONNECTIVITY = 4
# §2.1(b)：专用配置唯一可改的五个字段。
SURVEY_MUTABLE_SCENARIO_FIELDS: tuple[str, ...] = (
    "scenario_id",
    "anchor_world_m",
    "target.route_world_m",
    "target.speed_mps",
    "sensor.retained_frame_count",
)

# §2.1(c)(e) + BC-SURVEY-13：视角身份语法与**唯一**合法值来源。
# 巡览视角 `s/<position_id>/<00..15>`，证人视角**有且仅有** `w/C14`、
# `w/C26`、`w/W26`，窗外帧为 `null`。合法性不是前缀问题：非 `null` 值必须
# 同时通过完整语法解析**和**该会话 manifest 所钉、字节哈希相符的已复核
# plan 的成员校验。前缀判定（旧 `is_survey_witness_view`）已按 BC-SURVEY-13
# 删除——它让任何以 `w/` 起头的未绑定标签进入证人分母。
SURVEY_VIEW_ID_SURVEY_PREFIX = "s/"
SURVEY_VIEW_ID_WITNESS_PREFIX = "w/"
SURVEY_WITNESS_POSITION_IDS: tuple[str, ...] = ("C14", "C26", "W26")
SURVEY_VIEW_INDEX_MAX = 15
SURVEY_PLAN_DIRECTORY = "config/p1-vlm-survey-plans"
SURVEY_PLAN_SCHEMA = "p1-vlm-survey-plan/v1"


def survey_plan_path(plan_identity: str) -> str:
    """计划身份 → 版本控制内的 plan 路径（BC-SURVEY-5）。"""
    return f"{SURVEY_PLAN_DIRECTORY}/{plan_identity}/plan.json"


def survey_view_id(position_id: str, index: int) -> str:
    """铸造巡览视角 id；越界索引即拒绝，绝不铸出消费侧必须拒绝的值。"""
    if isinstance(index, bool) or not isinstance(index, int):
        raise SurveyContractError(f"巡览视角索引必须是整数：{index!r}")
    if not 0 <= index <= SURVEY_VIEW_INDEX_MAX:
        raise SurveyContractError(
            f"巡览视角索引越界（0..{SURVEY_VIEW_INDEX_MAX}）：{index}"
        )
    if not position_id or "/" in position_id:
        raise SurveyContractError(f"位置 id 不合式：{position_id!r}")
    return f"{SURVEY_VIEW_ID_SURVEY_PREFIX}{position_id}/{index:02d}"


def survey_witness_view_id(position_id: str) -> str:
    """铸造证人视角 id；位置必须在冻结三元组内。"""
    if position_id not in SURVEY_WITNESS_POSITION_IDS:
        raise SurveyContractError(
            f"证人位置不在冻结集合 {SURVEY_WITNESS_POSITION_IDS}：{position_id!r}"
        )
    return f"{SURVEY_VIEW_ID_WITNESS_PREFIX}{position_id}"


def parse_survey_view_id(value: Any) -> tuple[str, str, int | None]:
    """完整语法校验；→ `(kind, position_id, index|None)`，任何偏差即拒绝。

    只接受精确的 `str`。不做大小写归一、不做补零归一、不接受前后空白，
    `w/` 单独出现、`w/C1`、`w/C14x`、`w/R14-000`、`s/C14`、`s/C14/0`、
    `s/C14/16`、`s/C14/007` 一律拒绝。
    """
    if not isinstance(value, str):
        raise SurveyContractError(f"view_id 必须是字符串：{value!r}")
    parts = value.split("/")
    if parts[0] == "w":
        if len(parts) != 2 or parts[1] not in SURVEY_WITNESS_POSITION_IDS:
            raise SurveyContractError(
                f"证人 view_id 只能是 "
                f"{[SURVEY_VIEW_ID_WITNESS_PREFIX + p for p in SURVEY_WITNESS_POSITION_IDS]}："
                f"{value!r}"
            )
        return ("witness", parts[1], None)
    if parts[0] == "s":
        if len(parts) != 3:
            raise SurveyContractError(f"巡览 view_id 不合式：{value!r}")
        position_id, index_text = parts[1], parts[2]
        if not position_id:
            raise SurveyContractError(f"巡览 view_id 的位置段为空：{value!r}")
        if len(index_text) != 2 or not index_text.isdigit() or not index_text.isascii():
            raise SurveyContractError(
                f"巡览 view_id 的索引必须是两位十进制数字：{value!r}"
            )
        index = int(index_text)
        if index > SURVEY_VIEW_INDEX_MAX:
            raise SurveyContractError(
                f"巡览 view_id 索引越界（0..{SURVEY_VIEW_INDEX_MAX}）：{value!r}"
            )
        return ("survey", position_id, index)
    raise SurveyContractError(f"view_id 前缀不在闭集 {{s/, w/}}：{value!r}")


def load_pinned_survey_plan(
    repo_root: Path, manifest_path: Path, *, session_id: str
) -> dict[str, Any]:
    """按会话 manifest 的钉死项加载**已复核** plan，任何不符即 fail-closed。

    plan 从版本控制内的仓库路径读（BC-SURVEY-5 把它纳入版本控制），不是从
    归档读——归档成员域不含 plan.json，而复核角色的新鲜 worktree 里
    `runtime/` 是 gitignored 的。
    """
    import hashlib
    import json as _json

    manifest_path = Path(manifest_path)
    if not manifest_path.is_file():
        raise SurveyContractError(f"缺会话 manifest：{manifest_path}")
    try:
        manifest = _json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SurveyContractError(f"manifest 不可解析：{manifest_path}（{exc}）") from exc
    if manifest.get("schema_version") != SURVEY_MANIFEST_SCHEMA:
        raise SurveyContractError(
            f"manifest schema 不符：{manifest_path} 实测 "
            f"{manifest.get('schema_version')!r}"
        )
    if manifest.get("work_id") != SURVEY_WORK_ID:
        raise SurveyContractError(f"manifest work_id 不符：{manifest_path}")
    if manifest.get("session_id") != session_id:
        raise SurveyContractError(
            f"manifest 声明的会话 {manifest.get('session_id')!r} 不是 {session_id!r}"
        )
    expected_identity = survey_plan_identity(session_id)
    if manifest.get("plan_identity") != expected_identity:
        raise SurveyContractError(
            f"manifest 的计划身份 {manifest.get('plan_identity')!r} 不是 "
            f"{expected_identity!r}"
        )
    expected_path = survey_plan_path(expected_identity)
    if manifest.get("plan_path") != expected_path:
        raise SurveyContractError(
            f"manifest 的 plan_path {manifest.get('plan_path')!r} 不是 "
            f"{expected_path!r}；不得按 manifest 提供的路径直接拼接"
        )
    declared_sha = manifest.get("plan_sha256")
    if (
        not isinstance(declared_sha, str)
        or len(declared_sha) != 64
        or any(char not in "0123456789abcdef" for char in declared_sha)
    ):
        raise SurveyContractError(
            f"manifest 的 plan_sha256 不是 64 位小写十六进制：{declared_sha!r}"
        )
    plan_file = Path(repo_root) / expected_path
    if not plan_file.is_file():
        raise SurveyContractError(f"manifest 所钉的 plan 不存在：{plan_file}")
    raw = plan_file.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != declared_sha:
        raise SurveyContractError(
            f"plan 字节与 manifest 所钉哈希不符：{plan_file} 实测 {actual_sha}，"
            f"manifest {declared_sha}"
        )
    try:
        plan = _json.loads(raw.decode("utf-8"))
    except ValueError as exc:
        raise SurveyContractError(f"plan 不可解析：{plan_file}（{exc}）") from exc
    if plan.get("schema_version") != SURVEY_PLAN_SCHEMA:
        raise SurveyContractError(
            f"plan schema 不符：{plan_file} 实测 {plan.get('schema_version')!r}"
        )
    if plan.get("plan_identity") != expected_identity:
        raise SurveyContractError(
            f"plan 自称身份 {plan.get('plan_identity')!r} 不是 {expected_identity!r}"
        )
    # BC-SURVEY-14：manifest 与 plan 各自的采集协议钉子都必须等于**当前**投影。
    assert_survey_acquisition_pin(
        manifest.get("survey_acquisition_sha256"),
        where=f"会话 {session_id} 的 manifest",
    )
    assert_survey_acquisition_pin(
        plan.get("survey_acquisition_sha256"),
        where=f"会话 {session_id} 所钉的 plan",
    )
    return plan


def survey_plan_view_ids(plan: dict[str, Any]) -> tuple[frozenset[str], frozenset[str]]:
    """已复核 plan 的合法 `(巡览 id 集, 证人 id 集)`。

    **只**走 `plan["positions"][*]["views"][*]`。绝不走
    `dropped_positions`（其中整条位置记录连 `views` 一并保留）或
    `witness_prediction`（含被丢弃的预测项）——那会把 plan 明确剔除的视角
    重新放行，方向 fail-open。
    """
    survey_ids: set[str] = set()
    witness_ids: set[str] = set()
    for position in plan.get("positions", []):
        position_id = position.get("position_id")
        for view in position.get("views", []):
            view_id = view.get("view_id")
            kind, parsed_position, _index = parse_survey_view_id(view_id)
            if kind != view.get("kind"):
                raise SurveyContractError(
                    f"plan 视角 {view_id!r} 的语法类别 {kind!r} 与 kind "
                    f"{view.get('kind')!r} 不符"
                )
            if parsed_position != position_id:
                raise SurveyContractError(
                    f"plan 视角 {view_id!r} 的位置段与所属位置 {position_id!r} 不符"
                )
            target = witness_ids if kind == "witness" else survey_ids
            if view_id in survey_ids or view_id in witness_ids:
                raise SurveyContractError(f"plan 内 view_id 重复：{view_id!r}")
            target.add(view_id)
    return frozenset(survey_ids), frozenset(witness_ids)


def validate_selection_view_id(
    value: Any,
    frame_class: Any,
    legal_ids: frozenset[str],
) -> str | None:
    """`selection.json` 单行的 `view_id` 校验（S1/S2 共用）。

    `None` 只在该帧被判 `PROTOCOL_INVALID` 时合法（窗外帧）；其余情形先过
    完整语法，再过已复核 plan 的成员校验。
    """
    if value is None:
        if frame_class != "PROTOCOL_INVALID":
            raise SurveyContractError(
                f"view_id 为 null 却不是 PROTOCOL_INVALID（class={frame_class!r}）"
            )
        return None
    parse_survey_view_id(value)
    if value not in legal_ids:
        raise SurveyContractError(
            f"view_id {value!r} 不在该会话已复核 plan 的视角集合内"
        )
    return value


# §2.1(f)：证人结论闭集。
SURVEY_WITNESS_VERDICTS: tuple[str, ...] = (
    "WITNESS_PASS",
    "WITNESS_FAIL",
    "INSUFFICIENT_WITNESS_FRAMES",
)


def survey_tree_members(archive_root: Path) -> list[dict[str, Any]]:
    """归档根下的成员域：除 `tree.json` 外的**全部常规文件**，按相对名升序。"""
    import hashlib

    archive_root = Path(archive_root)
    members: list[dict[str, Any]] = []
    for path in sorted(archive_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(archive_root).as_posix()
        if relative in SURVEY_TREE_EXCLUDED_NAMES:
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        members.append(
            {"path": relative, "sha256": digest.hexdigest(), "bytes": path.stat().st_size}
        )
    return members


def survey_tree_sha256(members: list[dict[str, Any]]) -> str:
    """成员域 → 逻辑树摘要：canonical JSON 的 SHA-256（与工件同款字节规则）。"""
    import hashlib
    import json as _json

    text = _json.dumps(
        [
            {"path": member["path"], "sha256": member["sha256"], "bytes": member["bytes"]}
            for member in members
        ],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256((text + "\n").encode("utf-8")).hexdigest()


def survey_plan_identity(session_id: str) -> str:
    """会话身份 → 计划身份：去掉末尾的 `-s<n>` 段。"""
    head, separator, tail = session_id.rpartition("-s")
    if not separator or not tail.isdigit():
        raise SurveyContractError(
            f"会话身份不合式（应以 `-s<n>` 收尾）：{session_id!r}"
        )
    return head


def build_survey_sessions(repo_root: Path) -> list[dict[str, Any]]:
    """枚举全部巡览会话归档，产出 §2.2 第 4 条的 S0 `survey_sessions` 表。

    逐会话**重算**树摘要并与该会话 `tree.json` 声明比对，不符即硬错误；
    终态取自归档外的 `completion.json`（create-once 发布点）。
    """
    import hashlib
    import json as _json
    from tools.dist_data import roots as _roots

    repo_root = Path(repo_root)
    base = repo_root / _roots.SURVEY_ARCHIVE_ROOT
    if not base.is_dir():
        return []

    def _file_sha(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    rows: list[dict[str, Any]] = []
    for child in sorted(base.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        session_id = child.name
        tree_path = child / "tree.json"
        selection_path = child / "selection.json"
        manifest_path = child / "session" / "manifest.json"
        scenario_path = child / "session" / "scenario_config.json"
        for required in (tree_path, manifest_path, scenario_path):
            if not required.is_file():
                raise SurveyContractError(f"巡览归档缺成员：{required}")
        members = survey_tree_members(child)
        recomputed = survey_tree_sha256(members)
        declared = _json.loads(tree_path.read_text(encoding="utf-8"))
        if declared.get("tree_sha256") != recomputed:
            raise SurveyContractError(
                f"归档树摘要不符：{tree_path} 声明 {declared.get('tree_sha256')}，"
                f"重算 {recomputed}"
            )
        # BC-SURVEY-13：manifest 是 plan 的钉子，所以会话行只能建立在**已验证**
        # 的钉死关系上；`manifest.get("plan_sha256")` 会让「钉子缺席」自己满足
        # 自己（S1 随后拿 None 比 None 也相等）。
        plan = load_pinned_survey_plan(repo_root, manifest_path, session_id=session_id)
        manifest = _json.loads(manifest_path.read_text(encoding="utf-8"))
        completion_path = (
            repo_root / _roots.SURVEY_STATE_ROOT / session_id / "completion.json"
        )
        if not completion_path.is_file():
            raise SurveyContractError(f"巡览会话缺 completion：{completion_path}")
        completion = _json.loads(completion_path.read_text(encoding="utf-8"))
        terminal = completion.get("terminal")
        if terminal not in SURVEY_CLOSE_TERMINALS:
            raise SurveyContractError(
                f"终态不在闭集：{terminal!r}（{completion_path}）"
            )
        if completion.get("tree_sha256") != recomputed:
            raise SurveyContractError(
                f"completion 记录的树摘要与归档不符：{completion_path}"
            )
        frame_count = sum(
            1 for member in members if member["path"].startswith("frames/")
            and member["path"].endswith(".jpg")
        )
        rows.append(
            {
                "session_id": session_id,
                "plan_identity": plan["plan_identity"],
                "archive_root": child.relative_to(repo_root).as_posix(),
                "tree_sha256": recomputed,
                "selection_sha256": (
                    _file_sha(selection_path) if selection_path.is_file() else None
                ),
                "manifest_sha256": _file_sha(manifest_path),
                "scenario_sha256": _file_sha(scenario_path),
                "plan_sha256": manifest["plan_sha256"],
                "frame_count": frame_count,
                "close_terminal": terminal,
            }
        )
    return rows


# --- P1-VLM-DATA-002 §2.1(c)(d)：冻结采集几何与净空谓词 --------------------
# 常量与谓词住在 S0 合同模块，是因为**两个消费者必须共用同一份实现**：
# `tools/run_grounding_survey.py` 的 `plan`（事前排除位置/转场段）与
# `bind_layout` 的 S2 事后净空核验（§2.2 第 2 条）。两处各写一份就会出现
# 「计划说合法、事后说违规」的漂移。
SURVEY_TETHER_LENGTH_M = 35.0
SURVEY_TETHER_CONTROL_MARGIN_M = 2.0
# 33 m = 35 m 系留减 2 m 控制余量（§2.1(c)）。
SURVEY_MAX_TETHER_RADIUS_M = (
    SURVEY_TETHER_LENGTH_M - SURVEY_TETHER_CONTROL_MARGIN_M
)
# BC-SURVEY-1：`B'` 已含原障碍顶面 +3 m；水平各 +3 m。
SURVEY_OBSTACLE_EXPANSION_XZ_M = 3.0
SURVEY_OBSTACLE_EXPANSION_TOP_M = 3.0
# BC-SURVEY-1：绕行安全世界高度 = 相交 `B'.max_y` 再加 1 m（**不是** +4）。
SURVEY_DETOUR_EXTRA_M = 1.0
SURVEY_MIN_HEIGHT_M = 8.0
SURVEY_MAX_HEIGHT_M = 30.0
SURVEY_HEIGHT_STEP_M = 2.0
SURVEY_HEIGHTS_M: tuple[float, ...] = (14.0, 26.0)
SURVEY_RING_COEFFICIENT = 0.75
SURVEY_RING_AZIMUTHS_DEG: tuple[float, ...] = (0.0, 60.0, 120.0, 180.0, 240.0, 300.0)
SURVEY_OFF_NADIR_DEG: tuple[float, ...] = (20.0, 44.0)
SURVEY_VIEW_AZIMUTHS_DEG: tuple[float, ...] = (
    0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0,
)
SURVEY_WITNESS_AZIMUTH_QUANTUM_DEG = 15.0
SURVEY_GROUND_LOOK_AT_Y_M = 0.2
# §2.1(c)：计划有效条件。
SURVEY_MIN_KEPT_SURVEY_POSITIONS = 10
SURVEY_MIN_WITNESS_VIEWS = 3
# §2.1(e)：稳定/停留时长与逐帧有效性容差。
SURVEY_SETTLE_S = 0.5
SURVEY_DWELL_S = 1.2
SURVEY_WITNESS_DWELL_S = 4.0
SURVEY_POSITION_TOLERANCE_M = 1.0
SURVEY_BEARING_TOLERANCE_DEG = 3.0
SURVEY_MIN_VALID_FRAMES_PER_VIEW = 3
SURVEY_MIN_VALID_FRAMES_PER_WITNESS_VIEW = 10
SURVEY_MIN_ACHIEVEMENT_RATE = 0.90
# §2.1(f)：停放点候选与证人判据。
SURVEY_PARKED_SURFACE_INSET_M = 1.5
SURVEY_PARKED_ANCHOR_DISTANCE_M: tuple[float, float] = (4.0, 26.0)
SURVEY_PARKED_MIN_CATALOG_VEHICLE_M = 8.0
SURVEY_PARKED_OBSTACLE_MARGIN_M = 4.0
SURVEY_PARKED_SEGMENT_M = 1.0
SURVEY_WITNESS_PREDICT_MAX_OFF_NADIR_DEG = 40.0
SURVEY_WITNESS_PREDICT_MIN_SIDE_PX = 16
SURVEY_WITNESS_PREDICT_FRAMES_PER_VIEW = 20
SURVEY_WITNESS_PREDICT_MIN_FRAMES = 60
SURVEY_WITNESS_MIN_SIDE_PX = 12
SURVEY_WITNESS_MIN_DENOMINATOR = 50
SURVEY_WITNESS_SATURATION_MIN = 0.5
SURVEY_WITNESS_VALUE_MIN = 0.35
# §2.1(g)：驱动器时限与速度。
SURVEY_DRIVE_TICK_S = 0.2
SURVEY_DRIVE_GAIN = 1.0
SURVEY_DRIVE_MAX_SPEED_MPS = 3.0
SURVEY_COMMAND_LEASE_S = 1.0
SURVEY_ARRIVAL_DISTANCE_M = 0.3
SURVEY_ARRIVAL_SPEED_MPS = 0.3
SURVEY_WAYPOINT_TIMEOUT_S = 30.0
SURVEY_VIEW_SETTLE_TIMEOUT_S = 5.0
SURVEY_NO_FRAME_TIMEOUT_S = 10.0
SURVEY_SESSION_TIMEOUT_S = 900.0
SURVEY_RETAINED_FRAME_COUNT = 10000
# §2.1(c)：位置丢弃/不可达原因码闭集。
SURVEY_PLAN_DROP_REASONS: tuple[str, ...] = (
    "PLAN_POSITION_DROPPED",
    "PLAN_POSITION_UNREACHABLE",
)
# §2.1(g)：`drive` 终态闭集。
SURVEY_DRIVE_TERMINALS: tuple[str, ...] = (
    "DRIVE_COMPLETE",
    "DRIVE_COMPLETE_WITH_SKIPS",
    "DRIVE_REFUSED_AUDIT",
    "ABORTED_NO_FRAMES",
    "ABORTED_TIMEOUT",
)

Vec3f = tuple[float, float, float]


def expanded_obstacle_boxes(instances: Any) -> list[dict[str, float]]:
    """全部**非车辆**实例的闭集扩展框 `B'`（§2.1(c)）。

    `B' = [min_x−3, max_x+3] × [min_y, max_y+3] × [min_z−3, max_z+3]`；
    底面不下扩，顶面 +3 m。车辆实例不是障碍（它们是被拍摄对象）。
    """
    boxes: list[dict[str, float]] = []
    for instance in instances:
        if str(instance.get("group")) == "vehicle":
            continue
        boxes.append(
            {
                "scene_object_name": instance["scene_object_name"],
                "min_x_m": float(instance["min_x_m"]) - SURVEY_OBSTACLE_EXPANSION_XZ_M,
                "max_x_m": float(instance["max_x_m"]) + SURVEY_OBSTACLE_EXPANSION_XZ_M,
                "min_y_m": float(instance["min_y_m"]),
                "max_y_m": float(instance["max_y_m"]) + SURVEY_OBSTACLE_EXPANSION_TOP_M,
                "min_z_m": float(instance["min_z_m"]) - SURVEY_OBSTACLE_EXPANSION_XZ_M,
                "max_z_m": float(instance["max_z_m"]) + SURVEY_OBSTACLE_EXPANSION_XZ_M,
            }
        )
    return boxes


def parked_target_bounds(position_world_m: Any) -> dict[str, float]:
    """停放目标的世界轴对齐 AABB（§2.1(f) 冻结构造 + 前向 +z ⇒ 零转动）。

    旋转恒为单位四元数（`LookRotation(+z)` 作用于 `(0,0,1)`），所以局部框
    直接就是世界框，不需要任何朝向变换——这正是提案把停放段写成 `+z` 方向
    的目的。S2 的证人判定与 S3 的图像面阻断体共用本函数。
    """
    x, y, z = (float(value) for value in position_world_m)
    return {
        "min_x_m": x + PARKED_TARGET_LOCAL_X_M[0],
        "max_x_m": x + PARKED_TARGET_LOCAL_X_M[1],
        "min_y_m": y + PARKED_TARGET_LOCAL_Y_M[0],
        "max_y_m": y + PARKED_TARGET_LOCAL_Y_M[1],
        "min_z_m": z + PARKED_TARGET_LOCAL_Z_M[0],
        "max_z_m": z + PARKED_TARGET_LOCAL_Z_M[1],
    }


def point_inside_box(point: Vec3f, box: dict[str, float]) -> bool:
    """闭集包含判定（§2.1(c)：位置必须在所有 `B'` 之外，**严格**在外）。"""
    return (
        box["min_x_m"] <= point[0] <= box["max_x_m"]
        and box["min_y_m"] <= point[1] <= box["max_y_m"]
        and box["min_z_m"] <= point[2] <= box["max_z_m"]
    )


def boxes_containing(point: Vec3f, boxes: Any) -> list[str]:
    """点落入的全部 `B'` 名称（空列表 = 净空通过）。"""
    return [box["scene_object_name"] for box in boxes if point_inside_box(point, box)]


def segment_intersects_box(start: Vec3f, end: Vec3f, box: dict[str, float]) -> bool:
    """线段 / AABB **精确**相交（slab 法，闭集边界）——不采样（BC-SURVEY-1）。

    退化线段（起点 = 终点）退化为点包含判定。
    """
    lower = (box["min_x_m"], box["min_y_m"], box["min_z_m"])
    upper = (box["max_x_m"], box["max_y_m"], box["max_z_m"])
    enter = 0.0
    exit_ = 1.0
    for axis in range(3):
        origin = start[axis]
        direction = end[axis] - start[axis]
        if direction == 0.0:
            if origin < lower[axis] or origin > upper[axis]:
                return False
            continue
        t0 = (lower[axis] - origin) / direction
        t1 = (upper[axis] - origin) / direction
        if t0 > t1:
            t0, t1 = t1, t0
        enter = max(enter, t0)
        exit_ = min(exit_, t1)
        if enter > exit_:
            return False
    return True


def segment_intersecting_boxes(start: Vec3f, end: Vec3f, boxes: Any) -> list[dict[str, float]]:
    """线段命中的全部 `B'`（供绕行高度取 `max(max_y) + 1`）。"""
    return [box for box in boxes if segment_intersects_box(start, end, box)]
