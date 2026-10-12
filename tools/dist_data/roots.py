#!/usr/bin/env python3
"""附录 A 冻结根清单：pattern → 用途类 / 采集族 / 布局类的闭集映射。

Pattern 语义（AR2-3）：POSIX glob，`*` 不跨 `/`、`**` 跨任意层；`<RT>` =
`runtime/test-results` 前缀宏。表按 A.1→A.2→A.3 顺序求值，pattern 设计为
互不重叠：S1 对每个被枚举文件断言**恰匹配一个** pattern，零匹配或多匹配
均硬错误（不静默纳入、不静默跳过）。
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable

RT = "runtime/test-results"

# P1-VLM-DATA-002 §2.1：巡览采集的归档根与会话状态根。
SURVEY_ARCHIVE_ROOT = f"{RT}/p1-vlm-survey"
SURVEY_STATE_ROOT = "runtime/p1-vlm-survey"
# 条目 family 占位：巡览族按 source unit 末段（会话 id）逐会话成族，
# 表里写不出字面量，故写占位并由 `resolve_family` 解析（AR2-3）。
FAMILY_PLACEHOLDER_UNIT = "<unit>"

LAYOUT_DEFAULT = "default"
LAYOUT_SCENE004 = "scene-004"
LAYOUT_CLASSES: tuple[str, ...] = (LAYOUT_DEFAULT, LAYOUT_SCENE004)

KIND_IMAGE = "image"
KIND_TRUTH = "truth"

# 枚举根：`runtime/**` 全部 jpg，加附录 A 点名的 docs/evidence 副本。
ENUMERATION_ROOTS: tuple[str, ...] = ("runtime", "docs/evidence/P1-M3-BODY-001-1b")
# 根级排除（不入行级枚举；附录 A.3 `THIRD_PARTY_ASSET`）。
ROOT_EXCLUDED_PREFIXES: tuple[str, ...] = ("runtime/models/", "runtime/yoloe/")
# 活动桥目录：S1 断言其为空，非空即错。
MUST_BE_EMPTY_DIRS: tuple[str, ...] = ("runtime/frames",)


@dataclass(frozen=True)
class RootEntry:
    """附录 A 的一行：一个 pattern 及其闭集属性。"""

    pattern: str
    kind: str
    usage_class: str
    family: str | None
    layout_class: str | None
    note: str = ""

    @property
    def regex(self) -> re.Pattern[str]:
        return _compiled(self.pattern)


def glob_to_regex(pattern: str) -> str:
    """POSIX glob → 正则；`*`/`?` 不跨 `/`，`**` 跨任意层。"""
    out: list[str] = ["^"]
    i = 0
    n = len(pattern)
    while i < n:
        char = pattern[i]
        if char == "*":
            if pattern.startswith("**", i):
                if pattern.startswith("**/", i):
                    out.append("(?:.*/)?")
                    i += 3
                    continue
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
            i += 1
        elif char == "?":
            out.append("[^/]")
            i += 1
        elif char == "[":
            end = i + 1
            if end < n and pattern[end] in "!^":
                end += 1
            if end < n and pattern[end] == "]":
                end += 1
            while end < n and pattern[end] != "]":
                end += 1
            if end >= n:  # 未闭合的 `[` 按字面处理
                out.append(re.escape(char))
                i += 1
                continue
            body = pattern[i + 1 : end]
            if body.startswith(("!", "^")):
                body = "^" + body[1:]
            out.append("[" + body.replace("\\", "\\\\") + "]")
            i = end + 1
        else:
            out.append(re.escape(char))
            i += 1
    out.append("$")
    return "".join(out)


_CACHE: dict[str, re.Pattern[str]] = {}


def _compiled(pattern: str) -> re.Pattern[str]:
    compiled = _CACHE.get(pattern)
    if compiled is None:
        compiled = re.compile(glob_to_regex(pattern))
        _CACHE[pattern] = compiled
    return compiled


def _entry(
    pattern: str,
    kind: str,
    usage_class: str,
    family: str | None,
    layout_class: str | None,
    note: str = "",
) -> RootEntry:
    return RootEntry(
        pattern.replace("<RT>", RT), kind, usage_class, family, layout_class, note
    )


# --- A.1 default 布局类帧归档 --------------------------------------------
_A1: tuple[RootEntry, ...] = (
    _entry(
        f"<RT>/p1-m3-body-001-arm-a-*-post-run/frames/frame_*.jpg",
        KIND_IMAGE,
        "VALID_FORMAL",
        "m3-armA",
        LAYOUT_DEFAULT,
    ),
    # BC-DATA-7（接受轮 4）：宽泛的 `arm-a-*` 会把 void run truth 一并吞成
    # VALID_FORMAL，故拆为三条零重叠的精确 pattern，合计恰五份。
    _entry(
        "runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4/m3_body_truth.jsonl",
        KIND_TRUTH,
        "VALID_FORMAL",
        "m3-armA",
        LAYOUT_DEFAULT,
        note="p1-m3-body-truth/v2 逐帧目标真值",
    ),
    _entry(
        "runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2/m3_body_truth.jsonl",
        KIND_TRUTH,
        "VALID_FORMAL",
        "m3-armA",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "runtime/runs/p1-m3-body-001-arm-a-trial-[345]/m3_body_truth.jsonl",
        KIND_TRUTH,
        "VALID_FORMAL",
        "m3-armA",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "runtime/runs/p1-m3-body-001-arm-a-trial-*-void-attempt-*-hold/m3_body_truth.jsonl",
        KIND_TRUTH,
        "VOID_TRIAL_HOLD",
        "m3-armA",
        LAYOUT_DEFAULT,
        note="BC-DATA-7：void run 目录内的 truth，与根级 void truth pattern 并列",
    ),
    _entry(
        "<RT>/p1-m3-body-001-arm-b-trial-*-post-run/frames/frame_*.jpg",
        KIND_IMAGE,
        "VALID_FORMAL",
        "m3-armB",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "runtime/frames.arm-b-trial-3-shared-residue-hold/frame_*.jpg",
        KIND_IMAGE,
        "VALID_PARENT_HOLD",
        "m3-armB",
        LAYOUT_DEFAULT,
        note="B3 残留台账 hold（B3 无 post-run 归档）",
    ),
    _entry(
        "runtime/runs/p1-m3-body-001-arm-b-trial-*/m3_body_truth.jsonl",
        KIND_TRUTH,
        "VALID_FORMAL",
        "m3-armB",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "runtime/frames.arm-a-trial-*-void-attempt-*-hold/frame_*.jpg",
        KIND_IMAGE,
        "VOID_TRIAL_HOLD",
        "m3-armA",
        LAYOUT_DEFAULT,
        note="m3-void 并入 armA 族",
    ),
    _entry(
        "runtime/m3_body_truth.arm-a-trial-*-void-attempt-*-hold.jsonl",
        KIND_TRUTH,
        "VOID_TRIAL_HOLD",
        "m3-armA",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/p1-detect-001-scout-1-closed-exchange/frames/frame_*.jpg",
        KIND_IMAGE,
        "VALID_SCOUTING_CLOSED",
        "detect-scout1",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "runtime/p1-detect-scouting/p1-detect-001-scout-1/truth/frame_*.json",
        KIND_TRUTH,
        "VALID_SCOUTING_CLOSED",
        "detect-scout1",
        LAYOUT_DEFAULT,
        note="p1-detect-scouting-truth/v1",
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-b2-formal/r20-follow-[12]/pass/frames/frame_*.jpg",
        KIND_IMAGE,
        "VALID_FORMAL",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-b2-formal/r20-follow-3/attempt-2-complete-admissible/frames/frame_*.jpg",
        KIND_IMAGE,
        "VALID_FORMAL",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-b2-formal/r20-follow-3/attempt-1-invalid-s1-pause-gap/frames/frame_*.jpg",
        KIND_IMAGE,
        "PROTOCOL_INVALID",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-002-rerun-stopped-scene-defect/frames/frame_*.jpg",
        KIND_IMAGE,
        "PROTOCOL_INVALID",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-001-case3-attempt1/frames/frame_*.jpg",
        KIND_IMAGE,
        "PROTOCOL_INVALID",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-002-b2-smoke/attempt1-backlog-race/frames/frame_*.jpg",
        KIND_IMAGE,
        "PROTOCOL_INVALID",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-track-002-001-b2-pilot/pass/frames/frame_*.jpg",
        KIND_IMAGE,
        "VALID_FORMAL",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-001-case3-4-rerun-pass/frames/frame_*.jpg",
        KIND_IMAGE,
        "VALID_FORMAL",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-002-b2-smoke/attempt2-pass/frames/frame_*.jpg",
        KIND_IMAGE,
        "SMOKE",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-002-batch-b-integration/release-attempt/frames/frame_*.jpg",
        KIND_IMAGE,
        "SMOKE",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-002-b2-smoke/calibration-hold/frames/frame_*.jpg",
        KIND_IMAGE,
        "CALIBRATION",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-002-batch-b-integration/calibration-hold/frames/frame_*.jpg",
        KIND_IMAGE,
        "CALIBRATION",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-002-rerun-prep/ordinary-frames-before-rerun/frame_*.jpg",
        KIND_IMAGE,
        "CALIBRATION",
        "rate",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "<RT>/ut-p1-scene-002-001-attempt3-pass/cleared-active/frames/frame_*.jpg",
        KIND_IMAGE,
        "VALID_FORMAL",
        "scene-val",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "runtime/frames.1b-diagnostic-hold/frame_*.jpg",
        KIND_IMAGE,
        "DIAGNOSTIC_HOLD",
        "1b-diag",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "runtime/frames.unreleased-play-20260820-hold/frame_*.jpg",
        KIND_IMAGE,
        "UNRELEASED_PLAY_HOLD",
        "unreleased-0820",
        LAYOUT_DEFAULT,
    ),
    _entry(
        "runtime/m3_body_truth.unreleased-play-20260820-hold.jsonl",
        KIND_TRUTH,
        "UNRELEASED_PLAY_HOLD",
        "unreleased-0820",
        LAYOUT_DEFAULT,
    ),
    # P1-VLM-DATA-002 §2.2 第 1 条：巡览采集归档。用途类先按 pattern 取
    # `VALID_SURVEY`，再由该会话 `selection.json` 逐帧**只降不升**为
    # `PROTOCOL_INVALID`（S1 实现）。family = source unit 末段 = 会话 id。
    _entry(
        f"<RT>/p1-vlm-survey/*/frames/frame_*.jpg",
        KIND_IMAGE,
        "VALID_SURVEY",
        FAMILY_PLACEHOLDER_UNIT,
        LAYOUT_DEFAULT,
        note="P1-VLM-DATA-002 巡览会话归档；逐会话成族",
    ),
)

# --- A.2 scene-004 布局类帧归档 ------------------------------------------
_A2: tuple[RootEntry, ...] = (
    _entry(
        "<RT>/p1-scene-004-scout-4-closed-exchange/frames/frame_*.jpg",
        KIND_IMAGE,
        "VALID_SCOUTING_CLOSED",
        "s004-scout",
        LAYOUT_SCENE004,
    ),
    _entry(
        "runtime/p1-scene-004-scouting/p1-scene-004-scout-4/truth/frame_*.json",
        KIND_TRUTH,
        "VALID_SCOUTING_CLOSED",
        "s004-scout",
        LAYOUT_SCENE004,
        note="p1-detect-scouting-truth/v2",
    ),
    _entry(
        "<RT>/p1-scene-004-scout-3-protocol-invalid-same-id-retry-20260729/frames/frame_*.jpg",
        KIND_IMAGE,
        "PROTOCOL_INVALID",
        "s004-scout",
        LAYOUT_SCENE004,
        note="scout-3 并入 scout-4 族",
    ),
    _entry(
        "<RT>/p1-scene-004-scout-3-protocol-invalid-same-id-retry-20260729/session/truth/frame_*.json",
        KIND_TRUTH,
        "PROTOCOL_INVALID",
        "s004-scout",
        LAYOUT_SCENE004,
    ),
    _entry(
        "runtime/frames.qual3-leftover-hold/frame_*.jpg",
        KIND_IMAGE,
        "VALID_PARENT_HOLD",
        "s004-qual",
        LAYOUT_SCENE004,
    ),
    _entry(
        "<RT>/p1-detect-001-qual-2-protocol-invalid-exchange/frames/frame_*.jpg",
        KIND_IMAGE,
        "PROTOCOL_INVALID",
        "s004-qual",
        LAYOUT_SCENE004,
    ),
    _entry(
        "<RT>/p1-detect-001-qual-1-premeasurement-exchange/frames/frame_*.jpg",
        KIND_IMAGE,
        "CALIBRATION",
        "s004-qual",
        LAYOUT_SCENE004,
    ),
    _entry(
        "runtime/rate-study/P1-M2-RATE-003-CLOCKSMOKE/smoke-*/frames/frame_*.jpg",
        KIND_IMAGE,
        "SMOKE",
        "s004-smoke",
        LAYOUT_SCENE004,
    ),
    _entry(
        "<RT>/rs3-clock-smoke/phase1-hold/frames/frame_*.jpg",
        KIND_IMAGE,
        "SMOKE",
        "s004-smoke",
        LAYOUT_SCENE004,
    ),
)

# --- A.3 inventory-only 与排除 pattern -----------------------------------
_A3: tuple[RootEntry, ...] = (
    _entry(
        "runtime/qual3-preview/frame159-overlay*.jpg",
        KIND_IMAGE,
        "DERIVED_OVERLAY",
        None,
        None,
    ),
    _entry("runtime/runs/*/init-frame*.jpg", KIND_IMAGE, "PREVIEW", None, None),
    _entry("runtime/runs/*/reference*.jpg", KIND_IMAGE, "PREVIEW", None, None),
    _entry("runtime/rate-study/staging/*/init*.jpg", KIND_IMAGE, "PREVIEW", None, None),
    _entry("runtime/rate-study/previews/*.jpg", KIND_IMAGE, "PREVIEW", None, None),
    _entry(
        "runtime/rate-study/P1-M2-RATE-002-B2/previews/*.jpg",
        KIND_IMAGE,
        "PREVIEW",
        None,
        None,
    ),
    _entry(
        "runtime/rate-study/P1-M2-RATE-002-B2/calibrations/rate20/reference*.jpg",
        KIND_IMAGE,
        "PREVIEW",
        None,
        None,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-002-batch-b-integration/campaign/**/reference*.jpg",
        KIND_IMAGE,
        "PREVIEW",
        None,
        None,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-002-batch-b-integration/campaign/**/previews/*.jpg",
        KIND_IMAGE,
        "PREVIEW",
        None,
        None,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-002-rerun-stopped-scene-defect/campaign/**/reference*.jpg",
        KIND_IMAGE,
        "PREVIEW",
        None,
        None,
    ),
    _entry(
        "<RT>/ut-p1-m2-rate-002-002-rerun-stopped-scene-defect/campaign/**/previews/*.jpg",
        KIND_IMAGE,
        "PREVIEW",
        None,
        None,
    ),
    _entry(
        "runtime/p1-detect-scouting/p1-detect-001-scout-1/reference*.jpg",
        KIND_IMAGE,
        "PREVIEW",
        None,
        None,
    ),
    _entry(
        "runtime/p1-scene-004-scouting/p1-scene-004-scout-4/reference-preview.jpg",
        KIND_IMAGE,
        "PREVIEW",
        None,
        None,
    ),
    _entry(
        "docs/evidence/P1-M3-BODY-001-1b/frame_*.jpg",
        KIND_IMAGE,
        "DOC_COPY",
        None,
        None,
        note="按内容哈希折叠入源 lineage",
    ),
    # BC-DATA-6（接受轮 4）：探针 jpg 用 `*.jpg` 而非 `frame_*.jpg`——每个目录
    # 各含 1 张 `prompt_*.jpg`，写窄会残留 zero-match。
    _entry(
        "runtime/p1-scene-006/probe-baseline-vfov60/frames/*.jpg",
        KIND_IMAGE,
        "INVALID_RENDER_PROBE",
        None,
        None,
        note="旧 baseline 探针 jpg 107 张；F23 已否定灰色替身外观保真",
    ),
    _entry(
        "runtime/p1-scene-006/probe-candidate-vfov40/frames/*.jpg",
        KIND_IMAGE,
        "INVALID_RENDER_PROBE",
        None,
        None,
        note="旧 candidate 探针 jpg 107 张；F23 已否定灰色替身外观保真",
    ),
    _entry(
        "<RT>/rs3-clock-smoke/phase1-hold/frames/init-box-preview.jpg",
        KIND_IMAGE,
        "DERIVED_OVERLAY",
        None,
        None,
        note="绿色初始化框派生图；不得继承同目录 173 张原始帧的 SMOKE 资格",
    ),
    _entry(
        "runtime/p1-scene-006/probe-*/truth/frame_*.json",
        KIND_TRUTH,
        "PROBE_TRUTH_ONLY",
        None,
        None,
        note="探针 truth sidecar；配套 jpg 按 INVALID_RENDER_PROBE 另行排除",
    ),
    # P1-VLM-DATA-002 §2.2 第 1 条：两类巡览 hold 均 inventory-only。
    # 零重叠靠命名段：诊断 hold 目录名以 `p1-vlm-survey-diagnostic-` 起头，
    # foreign 残留 hold 以 `-foreign-residue-hold` 收尾且中段是会话 id
    # （`a<k>-p<v>-c<j>-s<n>`，永不以 `diagnostic-` 起头）；`*` 不跨 `/`。
    _entry(
        "runtime/frames.p1-vlm-survey-diagnostic-*/frame_*.jpg",
        KIND_IMAGE,
        "DIAGNOSTIC_HOLD",
        None,
        None,
        note="COORD-005 诊断 Play 帧 hold；零 ID、不进证据链",
    ),
    _entry(
        "runtime/frames.p1-vlm-survey-*-foreign-residue-hold/frame_*.jpg",
        KIND_IMAGE,
        "DIAGNOSTIC_HOLD",
        None,
        None,
        note="§2.1(h) 重入时的 foreign 残留 hold；只盘点",
    ),
)

ROOT_TABLE: tuple[RootEntry, ...] = _A1 + _A2 + _A3

# --- BC-SURVEY-7：S0 哈希冻结的运行根清单投影 ------------------------------
# 只投影**操作字段**：`note` 是说明性文字、`regex` 是编译产物，二者都不进
# 冻结面。四个成员一律按**声明顺序**输出，绝不排序——`ROOT_TABLE` 的
# A.1→A.2→A.3 求值序是「恰一匹配」规则的承重结构，排序会把它悄悄改掉。
ROOT_MANIFEST_ENTRY_FIELDS: tuple[str, ...] = (
    "pattern",
    "kind",
    "usage_class",
    "family",
    "layout_class",
)


def root_manifest() -> dict[str, Any]:
    """附录 A 运行表的 canonical 投影（S0 冻结、S1 枚举前对账）。

    `family` 逐字输出：巡览行因此携带占位 `<unit>` 本身，而不是解析后的
    会话 id——占位字符串一旦改变也必须撞破冻结面。
    """
    return {
        "enumeration_roots": list(ENUMERATION_ROOTS),
        "root_excluded_prefixes": list(ROOT_EXCLUDED_PREFIXES),
        "must_be_empty_dirs": list(MUST_BE_EMPTY_DIRS),
        "table": [
            {field: getattr(entry, field) for field in ROOT_MANIFEST_ENTRY_FIELDS}
            for entry in ROOT_TABLE
        ],
    }

# 用途类 → 资格（提案 §2.2 表）。`inventory` 恒为真；后三列为闭集事实。
USAGE_ELIGIBILITY: dict[str, dict[str, bool]] = {
    "VALID_FORMAL": {"mother": True, "floor": True, "test": True},
    "VALID_SCOUTING_CLOSED": {"mother": True, "floor": True, "test": True},
    "VALID_PARENT_HOLD": {"mother": True, "floor": True, "test": True},
    "VALID_SURVEY": {"mother": True, "floor": True, "test": True},
    "PROTOCOL_INVALID": {"mother": True, "floor": False, "test": False},
    "VOID_TRIAL_HOLD": {"mother": True, "floor": False, "test": False},
    "SMOKE": {"mother": True, "floor": False, "test": False},
    "CALIBRATION": {"mother": True, "floor": False, "test": False},
    "DIAGNOSTIC_HOLD": {"mother": False, "floor": False, "test": False},
    "UNRELEASED_PLAY_HOLD": {"mother": False, "floor": False, "test": False},
    "PREVIEW": {"mother": False, "floor": False, "test": False},
    "DERIVED_OVERLAY": {"mother": False, "floor": False, "test": False},
    "DOC_COPY": {"mother": False, "floor": False, "test": False},
    "THIRD_PARTY_ASSET": {"mother": False, "floor": False, "test": False},
    "INVALID_RENDER_PROBE": {"mother": False, "floor": False, "test": False},
    "PROBE_TRUTH_ONLY": {"mother": False, "floor": False, "test": False},
}

# 用途类 → 纳入/排除原因码（§2.2 闭集）。
USAGE_DECISION: dict[str, str] = {
    "VALID_FORMAL": "INCLUDED",
    "VALID_SCOUTING_CLOSED": "INCLUDED",
    "VALID_PARENT_HOLD": "INCLUDED",
    "VALID_SURVEY": "INCLUDED",
    "PROTOCOL_INVALID": "INCLUDED",
    "VOID_TRIAL_HOLD": "INCLUDED",
    "SMOKE": "INCLUDED",
    "CALIBRATION": "INCLUDED",
    "DIAGNOSTIC_HOLD": "EXCLUDED_DIAGNOSTIC_CHANNEL",
    "UNRELEASED_PLAY_HOLD": "EXCLUDED_UNRELEASED",
    "PREVIEW": "EXCLUDED_DERIVED",
    "DERIVED_OVERLAY": "EXCLUDED_DERIVED",
    "DOC_COPY": "EXCLUDED_DERIVED",
    "THIRD_PARTY_ASSET": "EXCLUDED_THIRD_PARTY",
    # BC-DATA-6：加入用途类闭集，但**不新增** inventory reason code。
    "INVALID_RENDER_PROBE": "INVENTORY_ONLY",
    "PROBE_TRUTH_ONLY": "INVENTORY_ONLY",
}


def matching_entries(relative_path: str, table: Iterable[RootEntry] | None = None) -> list[RootEntry]:
    """返回该路径命中的全部 pattern 行（S1 断言恰为 1 行）。"""
    return [entry for entry in (table or ROOT_TABLE) if entry.regex.match(relative_path)]


def resolve_family(entry: RootEntry, relative_path: str) -> str | None:
    """条目 family 的占位解析（AR2-3）。

    `<unit>` 占位 → 该帧 source unit 目录的末段（巡览会话 id）；其余条目
    原样返回表内字面量。占位只在表里出现，绝不进入 inventory 记录。
    """
    if entry.family != FAMILY_PLACEHOLDER_UNIT:
        return entry.family
    return source_unit_for(relative_path).rsplit("/", 1)[-1]


def is_survey_unit(source_unit: str) -> bool:
    """source unit 是否是 P1-VLM-DATA-002 的巡览会话归档根。"""
    prefix = SURVEY_ARCHIVE_ROOT + "/"
    if not source_unit.startswith(prefix):
        return False
    return "/" not in source_unit[len(prefix) :]


def is_root_excluded(relative_path: str) -> bool:
    """根级排除（`THIRD_PARTY_ASSET`）：不入行级枚举。"""
    return any(relative_path.startswith(prefix) for prefix in ROOT_EXCLUDED_PREFIXES)


# --- 逐帧真值 join（附录 A 逐行配对的转录，闭集） -------------------------
# `(图像路径正则, 真值定位模板, 真值 schema 族)`；未命中任何一行的图像属
# §2.3「无逐帧目标真值的族」，走扫掠代理区域分支。
TRUTH_JOIN: tuple[tuple[str, str, str], ...] = (
    (
        r"^runtime/test-results/(?P<run>p1-m3-body-001-arm-[ab]-[^/]+)-post-run/frames/frame_\d+\.jpg$",
        "runtime/runs/{run}/m3_body_truth.jsonl",
        "m3",
    ),
    (
        r"^runtime/frames\.arm-b-trial-3-shared-residue-hold/frame_\d+\.jpg$",
        "runtime/runs/p1-m3-body-001-arm-b-trial-3/m3_body_truth.jsonl",
        "m3",
    ),
    (
        r"^runtime/frames\.arm-a-trial-(?P<trial>\d+)-void-attempt-(?P<attempt>\d+)-hold/frame_\d+\.jpg$",
        "runtime/m3_body_truth.arm-a-trial-{trial}-void-attempt-{attempt}-hold.jsonl",
        "m3",
    ),
    (
        r"^runtime/frames\.unreleased-play-20260820-hold/frame_\d+\.jpg$",
        "runtime/m3_body_truth.unreleased-play-20260820-hold.jsonl",
        "m3",
    ),
    (
        r"^runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames/(?P<frame>frame_\d+)\.jpg$",
        "runtime/p1-detect-scouting/p1-detect-001-scout-1/truth/{frame}.json",
        "scouting",
    ),
    (
        r"^runtime/test-results/p1-scene-004-scout-4-closed-exchange/frames/(?P<frame>frame_\d+)\.jpg$",
        "runtime/p1-scene-004-scouting/p1-scene-004-scout-4/truth/{frame}.json",
        "scouting",
    ),
    (
        r"^runtime/test-results/p1-scene-004-scout-3-protocol-invalid-same-id-retry-20260729/frames/(?P<frame>frame_\d+)\.jpg$",
        "runtime/test-results/p1-scene-004-scout-3-protocol-invalid-same-id-retry-20260729/session/truth/{frame}.json",
        "scouting",
    ),
)

_TRUTH_JOIN_COMPILED = tuple(
    (re.compile(pattern), template, schema) for pattern, template, schema in TRUTH_JOIN
)


def truth_source_for(relative_path: str) -> tuple[str, str] | None:
    """图像路径 → `(真值文件路径, schema 族)`；无逐帧目标真值时返回 None。"""
    for regex, template, schema in _TRUTH_JOIN_COMPILED:
        match = regex.match(relative_path)
        if match is not None:
            return template.format(**match.groupdict()), schema
    return None


# --- 采集族 → 归档场景字节提供者（§2.3 第 1/2 步的闭集候选） --------------
# 优先级固定：run 目录内嵌快照 → 族内归档 manifest 的 sha 匹配字节。
SCENARIO_BYTE_PROVIDERS: tuple[str, ...] = (
    "runtime/runs/*/scenario.json",
    "runtime/scenario_config.*.hold.json",
    "runtime/rate-study/**/scenario_config.json",
    "runtime/test-results/**/scenario_config.json",
    "runtime/test-results/**/scenario.json",
    "config/scenario.default.json",
    "config/scenario.p1-scene-004.json",
)

# `road_data.json` 字节提供者（§2.3；只在 sha 相等时采用）。
ROAD_DATA_PROVIDERS: tuple[str, ...] = (
    "runtime/**/road_data.json",
    "runtime/test-results/**/road_data.json",
    "config/road_data.json",
)


# --- BC-DATA-13：source unit → 归档场景字节的**闭集**关联 -------------------
# 附录 A 的 capture root 实例（拥有 `frames/` 的归档目录，或表中点名的 flat
# hold）到其场景字节的显式映射。禁止模糊名称匹配或全库最近匹配。
#
# (a) m3 post-run、B3 residue hold 与 arm-A void hold → 对应 run 目录；
# (b) 附录 A.2 的三个 family → 表头点名的 hold provider（须 scenario_id 相符）；
# (c) 其余 source unit 只读自身归档树，不借同 family 邻居补齐。
SOURCE_UNIT_RUN_ASSOCIATION: tuple[tuple[str, str], ...] = (
    (
        r"^runtime/test-results/(?P<run>p1-m3-body-001-arm-[ab]-[^/]+)-post-run$",
        "runtime/runs/{run}",
    ),
    (
        r"^runtime/frames\.arm-b-trial-3-shared-residue-hold$",
        "runtime/runs/p1-m3-body-001-arm-b-trial-3",
    ),
    (
        r"^runtime/frames\.arm-a-trial-(?P<trial>\d+)-void-attempt-(?P<attempt>\d+)-hold$",
        "runtime/runs/p1-m3-body-001-arm-a-trial-{trial}-void-attempt-{attempt}-hold",
    ),
)

# (b) 附录 A.2 表头点名的归档 provider 及其前提 scenario_id。
SCENE004_ARCHIVE_PROVIDER = "runtime/scenario_config.p1-scene-004.hold.json"
SCENE004_REQUIRED_SCENARIO_ID = "p1-scene-004"
SCENE004_FAMILIES: frozenset[str] = frozenset({"s004-scout", "s004-qual", "s004-smoke"})

_RUN_ASSOCIATION_COMPILED = tuple(
    (re.compile(pattern), template) for pattern, template in SOURCE_UNIT_RUN_ASSOCIATION
)


def source_unit_for(relative_path: str) -> str:
    """帧路径 → 其 capture root 实例（BC-DATA-13 的绑定域）。

    拥有 `frames/` 的归档目录即 source unit；flat hold 则是帧所在目录本身。
    """
    marker = "/frames/"
    if marker in relative_path:
        return relative_path[: relative_path.index(marker)]
    return relative_path.rsplit("/", 1)[0]


def associated_run_directory(source_unit: str) -> str | None:
    """(a) 按附录 A root 模板把 m3 归档/hold 映射到对应 run 目录。"""
    for regex, template in _RUN_ASSOCIATION_COMPILED:
        match = regex.match(source_unit)
        if match is not None:
            return template.format(**match.groupdict())
    return None
