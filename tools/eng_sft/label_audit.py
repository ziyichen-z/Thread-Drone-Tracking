#!/usr/bin/env python3
"""表 J：派生标签语义抽查（分层抽样、面板、收据、统计；纯离线、零 Play、零模型）。

四个阶段，顺序由合同固定：

1. `plan`   —— 在冻结前的最终集合上按表 J 的层与配额确定性抽样，把种子、层定义、
   分母与实取、面板清单、ASSET-001 交集表写进
   `docs/evidence/P1-ENG-SFT-002-label-audit.md`。
2. `panels` —— 生成面板与原图副本（`outputs/eng-sft/P1-ENG-SFT-002/panel/`），
   逐张回填 `overlay_sha256`，写 `panel-receipt.json`（HEAD、样本身份、原图 SHA、
   叠加图 SHA）。
3. `prescreen` —— 实现角色对预筛份额看图后把逐行结果写进「预筛」表；**预筛只作
   披露，不计为语义核验**，不改变任何冻结决定。
4. `stats` —— **只读** `docs/unity-test-log.md` 的 `UT-P1-ENG-SFT-002-label-audit`
   条目（判定原文由接受/辅助角色代录），统计逐层计数：「不确定」单列、不计为对；
   用户份额有未判定 → `AUDIT_INCOMPLETE`；出现任一「错」→ `AUDIT_FINDING_OPEN`
   收据，`freeze` 拒绝运行。

抽样域按 AC-14 修订 1：J1…J5 取训练 distinct ∪ 441 行选层 ∪ 评估中
G1/G1t/G2/G2t/G3/G3t/G5；J6 取 86 行 G4；J7 取 #27 在执行域且 bus 颜色指令被排除
的帧。G3p 与 LEGACY_ONLY 不抽。
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_sft import build_sft_data as build  # noqa: E402
from tools.eng_sft import receipts  # noqa: E402

AUDIT_FILENAME = f"{receipts.WORK_ID}-label-audit.md"
AUDIT_PATH = Path("docs/evidence") / AUDIT_FILENAME
ASSET_AUDIT_PATH = Path("docs/evidence/P1-ENG-ASSET-001-label-audit.md")
UNITY_LOG_PATH = Path("docs/unity-test-log.md")
UNITY_LOG_ENTRY = f"UT-{receipts.WORK_ID}-label-audit"
PANEL_RECEIPT_NAME = "panel-receipt.json"
FINDING_RECEIPT_NAME = "audit-finding-open.json"
# AC-14 修订 3：接受角色裁定后，实现角色写「闭合记录」把具名裁定与原判定/面板/排除证据
# 绑定起来；原 `AUDIT_FINDING_OPEN` 收据保留不删。`freeze` 只放行记录里已落实处置的面板，
# 新增「错」/未判定/未裁定仍拒绝——删掉原收据也绕不过去（闭合记录自己要校验判定摘要）。
CLOSURE_RECEIPT_NAME = "audit-finding-closure.json"
# 表 J 的处置闭集：(i) 规则缺陷 / (ii) 上游标签缺陷 / (iii) 显示问题。
RULING_DISPOSITIONS: tuple[str, ...] = ("i", "ii", "iii")
PROPOSAL_PATH = Path("docs/proposals/P1-ENG-SFT-002-lora-training-and-cloud-execution.md")

USER_CAP = 24
PRESCREEN_CAP = 36

# 表 J：层 → (用户判定行, 实现者预筛行)。
LAYER_QUOTAS: tuple[tuple[str, int, int], ...] = (
    ("J1", 4, 8),
    ("J2", 3, 4),
    ("J3", 4, 8),
    ("J4", 4, 8),
    ("J5", 3, 4),
    ("J6", 3, 4),
    ("J7", 2, 0),
)
LAYER_TITLES: dict[str, str] = {
    "J1": "class unique（目录车）",
    "J2": "color unique（`color_required` 优先）",
    "J3": "class ambiguous（候选集完整）",
    "J4": "none",
    "J5": "目标车 unique",
    "J6": "G4 关系行",
    "J7": "#27 排除帧（`Vehicle_Bus_color03`）",
}
JUDGED_FIELDS: dict[str, tuple[str, ...]] = {
    "J1": ("状态",),
    "J2": ("状态", "颜色"),
    "J3": ("状态", "候选完整"),
    "J4": ("状态",),
    "J5": ("状态", "颜色"),
    "J6": ("状态", "关系方向"),
    "J7": ("状态", "颜色"),
}
ERROR_TYPES: tuple[str, ...] = (
    "漏车",
    "多车",
    "类别错",
    "颜色错",
    "目标车框错",
    "关系方向错",
    "框不紧或截断",
    "其他",
)
VERDICT_VALUES: tuple[str, ...] = ("对", "错", "不确定", "NA")
VERDICT_SCHEMA_LINE = f"Schema: {receipts.SCHEMA_PREFIX}/verdicts/v1"
VERDICT_STATUS_LINE = "Status: OFFLINE_VISUAL_CHECK"
VERDICT_STATE_PREFIX = "Judgment state:"
VERDICT_TABLE_HEADER = "| panel_index | 状态 | 候选完整 | 颜色 | 关系方向 | 错误类型 |"

EVAL_LAYER_GROUPS: frozenset[str] = frozenset({"G1", "G1t", "G2", "G2t", "G3", "G3t", "G5"})
# 表 J 逐字的弱类顺序：{car, pickup truck, truck, suv}。
WEAK_CLASS_ORDER: tuple[str, ...] = ("car", "pickup truck", "truck", "suv")


class PanelError(receipts.EngSftError):
    reason = "OUTPUT_PATH_FORBIDDEN"


@dataclass
class Candidate:
    """抽样域里的一行（训练 / 选层 / 评估 / J7 候选统一形态）。"""

    key: str
    source: str
    layer: str
    frame_id: str
    surface: str
    state: str
    noun_type: str
    class_word: str | None
    object_ids: tuple[str, ...]
    boxes: tuple[tuple[float, ...], ...]
    has_dynamic_target: bool
    color_required: bool | None
    group: str | None
    stratum: str
    extra: dict[str, Any] = field(default_factory=dict)

    def hash_key(self) -> str:
        if self.state == "unique" and self.object_ids:
            thin = self.object_ids[0]
        elif self.state == "ambiguous" and self.object_ids:
            thin = "|".join(self.object_ids)
        else:
            thin = self.surface
        return hashlib.sha256(
            f"{build.SEED}|{self.frame_id}|{thin}".encode("utf-8")
        ).hexdigest()

    def order(self) -> tuple[str, str, str]:
        return (self.hash_key(), self.frame_id, self.surface)


def _class_of(row: dict[str, Any]) -> str | None:
    noun = row.get("noun")
    if isinstance(noun, dict):
        return noun.get("class")
    program = row.get("relation_program")
    if isinstance(program, dict):
        return program.get("target", {}).get("class")
    return None


def noun_type_of(row: dict[str, Any]) -> str | None:
    """取该行的 noun 类型：训练/选层行自带 `noun_type`，评估行按表 C 只写 `noun`。

    C2-4：评估行（`eval_record`）按表 C 的字段表**没有** `noun_type`，直接读它会让
    G2 的 color unique 落进 J1、G3/G3t 的 ambiguous 整个掉出抽样域。这里按实际 schema 推导：
    有 `relation_program` 的是关系行；否则看 `noun` 里有没有 `color`。
    """
    if row.get("relation_program") is not None:
        return "relation"
    stored = row.get("noun_type")
    if stored is not None:
        return stored
    noun = row.get("noun")
    if isinstance(noun, dict):
        return "color" if noun.get("color") else "class"
    return None


def _layer_of(row: dict[str, Any], source: str) -> str | None:
    """按 AC-14 修订 1 把一行归到唯一的层（目标车行一律落 J5）。"""
    if source == "j7":
        return "J7"
    group = row.get("group")
    if group == "G4":
        return "J6"
    state = row.get("state") or row.get("gold_state")
    noun_type = noun_type_of(row)
    if row.get("has_dynamic_target") and state == "unique":
        # 表 J：目标车 unique 一律落 J5（G1t/G2t 或训练 has_dynamic_target unique），
        # 不与 J1/J2 混算。
        return "J5"
    if state == "ambiguous":
        # J3 的定义是 **class** ambiguous（候选集完整）；color noun 的 ambiguous 行
        # 不在表 J 枚举的任何一层里，抽样域按闭集不收。
        return "J3" if noun_type == "class" else None
    if state == "none":
        return "J4"
    if state == "unique":
        return "J2" if noun_type == "color" else "J1"
    return None


def _candidate_from_row(row: dict[str, Any], source: str) -> Candidate | None:
    layer = _layer_of(row, source)
    if layer is None:
        return None
    if source == "j7":
        return Candidate(
            key=f"j7-{hashlib.sha256((row['frame_id'] + row['excluded_surface']).encode()).hexdigest()[:16]}",
            source=source,
            layer="J7",
            frame_id=row["frame_id"],
            surface=row["excluded_surface"],
            state="excluded",
            noun_type="color",
            class_word=row["excluded_class"],
            object_ids=(row["object_id"],),
            boxes=(tuple(row["box_norm_xywh"]),) if row.get("box_norm_xywh") else (),
            has_dynamic_target=False,
            color_required=None,
            group=None,
            stratum="NA",
            extra={"s5_color": row.get("s5_color"), "counterexample_object_ids": row.get("counterexample_object_ids", [])},
        )
    boxes = row.get("target_boxes_norm_xywh") or row.get("gold_boxes_norm_xywh") or []
    ids = row.get("target_object_ids") or row.get("definite_ids") or []
    return Candidate(
        key=row.get("sample_id") or row["row_id"],
        source=source,
        layer=layer,
        frame_id=row["frame_id"],
        surface=row["surface"],
        state=row.get("state") or row.get("gold_state") or "unknown",
        noun_type=noun_type_of(row) or "class",
        class_word=_class_of(row),
        object_ids=tuple(ids),
        boxes=tuple(tuple(box) for box in boxes),
        has_dynamic_target=bool(row.get("has_dynamic_target")),
        color_required=row.get("color_required"),
        group=row.get("group"),
        stratum=row.get("stratum", "NA"),
    )


def load_candidates(local_root: Path) -> list[Candidate]:
    """抽样域：训练 distinct ∪ 选层 441 ∪ 评估的七个组 ∪ J7 候选。"""
    data_dir = Path(local_root) / build.DATA_DIRNAME
    candidates: list[Candidate] = []
    for name, source in (
        (build.TRAIN_JSONL, "train"),
        (build.SELECT_EVAL_JSONL, "select"),
    ):
        for row in _read_jsonl(data_dir / name):
            candidate = _candidate_from_row(row, source)
            if candidate is not None:
                candidates.append(candidate)
    for row in _read_jsonl(data_dir / build.EVAL_JSONL):
        if row.get("group") not in EVAL_LAYER_GROUPS and row.get("group") != "G4":
            continue
        candidate = _candidate_from_row(row, "eval")
        if candidate is not None:
            candidates.append(candidate)
    for row in _read_jsonl(data_dir / build.AUDIT_J7_JSONL):
        candidate = _candidate_from_row(row, "j7")
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not Path(path).is_file():
        return []
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _layer_sort_key(layer: str, candidate: Candidate) -> tuple:
    """层内取样序（AC-14 修订 1）：先层专属优先级，再表 D′ 哈希序。"""
    base = candidate.order()
    if layer == "J2":
        return (0 if candidate.color_required else 1, *base)
    if layer == "J3":
        count = len(candidate.object_ids)
        return (0 if count >= 3 else 1, *base)
    return base


class _Picker:
    """同一 `object_id` 每层 ≤ 1 行、同一帧全局 ≤ 1 行。"""

    def __init__(self) -> None:
        self.used_frames: set[str] = set()
        self.used_objects: dict[str, set[str]] = defaultdict(set)

    def available(self, candidate: Candidate) -> bool:
        if candidate.frame_id in self.used_frames:
            return False
        keys = candidate.object_ids or (candidate.surface,)
        return not any(key in self.used_objects[candidate.layer] for key in keys)

    def take(self, candidate: Candidate) -> None:
        self.used_frames.add(candidate.frame_id)
        for key in candidate.object_ids or (candidate.surface,):
            self.used_objects[candidate.layer].add(key)


def sample_panels(candidates: Sequence[Candidate]) -> dict[str, Any]:
    """表 J 分层抽样；用户份额先按 J1→J7 取完，预筛再按 J1→J6 续取。"""
    by_layer: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        by_layer[candidate.layer].append(candidate)
    for layer, rows in by_layer.items():
        rows.sort(key=lambda c: _layer_sort_key(layer, c))

    picker = _Picker()
    user_rows: list[tuple[str, Candidate]] = []
    prescreen_rows: list[tuple[str, Candidate]] = []
    shortfalls: dict[str, dict[str, int]] = {}

    def take_from(layer: str, wanted: int, bucket: list[tuple[str, Candidate]], cap: int,
                  chooser=None) -> int:
        taken = 0
        pool = [c for c in by_layer.get(layer, []) if picker.available(c)]
        if chooser is not None:
            ordered = chooser(pool)
        else:
            ordered = pool
        for candidate in ordered:
            if taken >= wanted or len(bucket) >= cap:
                break
            if not picker.available(candidate):
                continue
            picker.take(candidate)
            bucket.append((layer, candidate))
            taken += 1
        return taken

    def j1_user(pool: list[Candidate]) -> list[Candidate]:
        """J1 用户份额：弱类 {car, pickup truck, suv, truck} 各取一行（按表 J 顺序）。"""
        ordered: list[Candidate] = []
        for class_word in WEAK_CLASS_ORDER:
            for candidate in pool:
                if candidate.class_word == class_word:
                    ordered.append(candidate)
                    break
        ordered.extend(c for c in pool if c not in ordered)
        return ordered

    def j3_user(pool: list[Candidate]) -> list[Candidate]:
        """J3 用户份额：先取含目标车的一行（若可得），其余按候选数 3–4 优先再哈希序。"""
        with_target = [c for c in pool if c.has_dynamic_target]
        ordered = with_target[:1]
        ordered.extend(c for c in pool if c not in ordered)
        return ordered

    def j4_user(pool: list[Candidate]) -> list[Candidate]:
        """J4：每类 ≤ 1，用户 4 张覆盖 4 个不同类别。"""
        seen: set[str | None] = set()
        ordered: list[Candidate] = []
        for candidate in pool:
            if candidate.class_word in seen:
                continue
            seen.add(candidate.class_word)
            ordered.append(candidate)
        return ordered

    choosers = {"J1": j1_user, "J3": j3_user, "J4": j4_user}
    for layer, user_quota, _prescreen_quota in LAYER_QUOTAS:
        taken = take_from(layer, user_quota, user_rows, USER_CAP, choosers.get(layer))
        shortfalls[layer] = {"user_quota": user_quota, "user_taken": taken}

    j4_classes: set[str | None] = {c.class_word for layer, c in prescreen_rows if layer == "J4"}

    def j4_prescreen(pool: list[Candidate]) -> list[Candidate]:
        used = {c.class_word for layer, c in user_rows if layer == "J4"} | j4_classes
        ordered = []
        for candidate in pool:
            if candidate.class_word in used:
                continue
            used.add(candidate.class_word)
            ordered.append(candidate)
        return ordered

    for layer, _user_quota, prescreen_quota in LAYER_QUOTAS:
        if prescreen_quota == 0:
            shortfalls[layer]["prescreen_quota"] = 0
            shortfalls[layer]["prescreen_taken"] = 0
            continue
        chooser = j4_prescreen if layer == "J4" else None
        taken = take_from(layer, prescreen_quota, prescreen_rows, PRESCREEN_CAP, chooser)
        shortfalls[layer]["prescreen_quota"] = prescreen_quota
        shortfalls[layer]["prescreen_taken"] = taken

    panels: list[dict[str, Any]] = []
    for index, (layer, candidate) in enumerate(user_rows + prescreen_rows, start=1):
        panels.append(
            {
                "panel_index": index,
                "layer": layer,
                "share": "user" if index <= len(user_rows) else "prescreen",
                "key": candidate.key,
                "source": candidate.source,
                "group": candidate.group,
                "frame_id": candidate.frame_id,
                "surface": candidate.surface,
                "state": candidate.state,
                "noun_type": candidate.noun_type,
                "class_word": candidate.class_word,
                "object_ids": list(candidate.object_ids),
                "boxes_norm_xywh": [list(box) for box in candidate.boxes],
                "has_dynamic_target": candidate.has_dynamic_target,
                "color_required": candidate.color_required,
                "stratum": candidate.stratum,
                "extra": candidate.extra,
            }
        )
    return {
        "panels": panels,
        "user_rows": len(user_rows),
        "prescreen_rows": len(prescreen_rows),
        "layer_stats": shortfalls,
        "domain_by_layer": {layer: len(rows) for layer, rows in sorted(by_layer.items())},
    }


# --- ASSET-001 交集表 -----------------------------------------------------

_ASSET_ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*(S\d)\s*\|\s*\w+\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|"
)


def asset001_panels(repo_root: Path = PROJECT_ROOT) -> dict[tuple[str, str], int]:
    """解析 ASSET-001 的 60 张面板清单 → `(frame_id, object_id) → panel_index`。"""
    path = Path(repo_root) / ASSET_AUDIT_PATH
    if not path.is_file():
        return {}
    mapping: dict[tuple[str, str], int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _ASSET_ROW_RE.match(line.strip())
        if match:
            mapping[(match.group(3), match.group(4))] = int(match.group(1))
    return mapping


def intersection_rows(panels: Sequence[dict[str, Any]], repo_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    """按 `(frame_id, object_id)` 与 ASSET-001 面板求交集（三态状态仍须本次判定）。"""
    asset = asset001_panels(repo_root)
    rows: list[dict[str, Any]] = []
    for panel in panels:
        for object_id in panel["object_ids"]:
            index = asset.get((panel["frame_id"], object_id))
            if index is not None:
                rows.append(
                    {
                        "panel_index": panel["panel_index"],
                        "layer": panel["layer"],
                        "frame_id": panel["frame_id"],
                        "object_id": object_id,
                        "asset001_panel_index": index,
                    }
                )
    return rows


# --- 文档 -----------------------------------------------------------------


def render_document(plan: dict[str, Any], *, repo_root: Path = PROJECT_ROOT) -> str:
    panels = plan["panels"]
    lines: list[str] = []
    lines.append(f"# {receipts.WORK_ID} — 派生标签语义抽查（表 J / AC-14）")
    lines.append("")
    lines.append(
        "本文件是表 J 的抽样契约与面板清单：**种子、层定义与配额先提交**，面板生成器"
        "在运行时解析本文件的 `git status --porcelain`（须为空）与 `git log -1 --format=%H`"
        "并写入 `panel-receipt.json`。本文件只存抽样参数、分层实取、面板清单、统计与实现者"
        "预筛表，**不复制用户判定原文**（原文由接受/辅助角色代录进 `docs/unity-test-log.md`"
        f" 的 `{UNITY_LOG_ENTRY}` 条目，标 `OFFLINE_VISUAL_CHECK`，零 Play）。"
    )
    lines.append("")
    lines.append("## 1. 抽样参数")
    lines.append("")
    lines.append(f"- 抽样种子（seed）：`{build.SEED}`（与表 D′ 同一 `h(s)`）")
    lines.append(f"- 用户判定上限：{USER_CAP} 张唯一图片；实现者预筛上限：{PRESCREEN_CAP} 张")
    lines.append("- 层内取样序：`h(s)` 升序，平局补 `frame_id`/`surface`；J2 先 `color_required`、"
                 "J3 先含目标车再候选数 3–4、J1 用户份额按弱类顺序各取一行、J4 每类 ≤ 1")
    lines.append("- 唯一性：同一 `object_id` 每层 ≤ 1 行、同一帧全局 ≤ 1 行；不足额留空披露、不回填")
    lines.append(f"- 实取：用户 {plan['user_rows']} 行 + 预筛 {plan['prescreen_rows']} 行 ="
                 f" {len(panels)} 张唯一图片")
    lines.append("")
    lines.append("## 2. 层定义、分母与实取")
    lines.append("")
    lines.append("| 层 | 定义 | 抽样域（行） | 用户配额 | 用户实取 | 预筛配额 | 预筛实取 |")
    lines.append("|---|---|---|---|---|---|---|")
    for layer, user_quota, prescreen_quota in LAYER_QUOTAS:
        stats = plan["layer_stats"].get(layer, {})
        lines.append(
            f"| {layer} | {LAYER_TITLES[layer]} | {plan['domain_by_layer'].get(layer, 0)} | "
            f"{user_quota} | {stats.get('user_taken', 0)} | {prescreen_quota} | "
            f"{stats.get('prescreen_taken', 0)} |"
        )
    lines.append("")
    lines.append("## 3. 面板清单")
    lines.append("")
    lines.append(
        "| panel_index | 层 | 份额 | 来源 | frame_id | object_ids | surface | 状态 | 层(px) | overlay_sha256 |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for panel in panels:
        objects = ", ".join(f"`{o}`" for o in panel["object_ids"]) or "（无框）"
        source = panel["group"] or panel["source"]
        overlay = panel.get("overlay_sha256")
        lines.append(
            f"| {panel['panel_index']} | {panel['layer']} | {panel['share']} | {source} | "
            f"`{panel['frame_id']}` | {objects} | {panel['surface']} | {panel['state']} | "
            f"{panel['stratum']} | " + (f"`{overlay}`" if overlay else "（待生成）") + " |"
        )
    lines.append("")
    j7 = [panel for panel in panels if panel["layer"] == "J7"]
    if j7:
        lines.append("**J7 身份披露（AC-14 修订 2）**：叠框对象、框与 S5 颜色词指向同一个对象；"
                     "触发整帧排除的 `#27` counterexample 另列，不与叠框对象混用。")
        lines.append("")
        lines.append("| panel_index | 叠框对象（判定对象） | S5 颜色词 | 被排除的 noun | 触发排除的 counterexample |")
        lines.append("|---|---|---|---|---|")
        for panel in j7:
            boxed = ", ".join(f"`{o}`" for o in panel["object_ids"]) or "（无）"
            extra = panel.get("extra", {})
            trigger = ", ".join(f"`{o}`" for o in extra.get("counterexample_object_ids", [])) or "（无）"
            lines.append(
                f"| {panel['panel_index']} | {boxed} | {extra.get('s5_color')} | "
                f"{panel['surface']} | {trigger} |"
            )
        lines.append("")
    lines.append("## 4. 与 P1-ENG-ASSET-001 面板的交集")
    lines.append("")
    rows = plan.get("intersection", [])
    if rows:
        lines.append("| 本次 panel_index | 层 | frame_id | object_id | ASSET-001 panel_index |")
        lines.append("|---|---|---|---|---|")
        for row in rows:
            lines.append(
                f"| {row['panel_index']} | {row['layer']} | `{row['frame_id']}` | "
                f"`{row['object_id']}` | {row['asset001_panel_index']} |"
            )
        lines.append("")
        lines.append(
            "交集行的类别/颜色/框判定可引用 ASSET-001 对应面板；**三态状态仍须本次判定**"
            "（旧抽查无此项），且本表不构成 S6 审计。"
        )
    else:
        lines.append("本次面板与 ASSET-001 的 60 张面板无 `(frame_id, object_id)` 交集。")
    lines.append("")
    lines.append("## 5. 用户判定统计")
    lines.append("")
    lines.append(plan.get("stats_block", "（待 `stats` 阶段填入；判定原文见 Unity 日志条目）"))
    lines.append("")
    lines.append("## 6. 实现者预筛（披露，不计为语义核验）")
    lines.append("")
    lines.append(plan.get("prescreen_block", "（待 `prescreen` 阶段填入）"))
    lines.append("")
    return "\n".join(lines)


def plan_path(repo_root: Path = PROJECT_ROOT) -> Path:
    return Path(repo_root) / AUDIT_PATH


def plan_json_path(local_root: Path) -> Path:
    return Path(local_root) / receipts.RECEIPTS_DIRNAME / "audit-plan.json"


def run_plan(
    *, repo_root: Path = PROJECT_ROOT, local_root: Path | None = None
) -> dict[str, Any]:
    """`plan`：抽样并写抽样契约文档（面板尚未生成）。"""
    started = time.monotonic()
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    manifest = receipts.InputManifest(repo_root=root)
    try:
        for name in (build.TRAIN_JSONL, build.SELECT_EVAL_JSONL, build.EVAL_JSONL, build.AUDIT_J7_JSONL):
            manifest.record(local / build.DATA_DIRNAME / name, source="build 产出（抽样域）")
        candidates = load_candidates(local)
        plan = sample_panels(candidates)
        plan["intersection"] = intersection_rows(plan["panels"], root)
        document = render_document(plan, repo_root=root)
        path = plan_path(root)
        receipts.assert_output_allowed(path, root)
        path.write_text(document, encoding="utf-8")
        writer._write_json(plan_json_path(local), plan)
        after = manifest.recompute()
        writer.save_input_manifest("audit", manifest, after, manifest.diff(after), successful=True)
        writer.write_run_receipt(
            "audit",
            started=started,
            outputs=[receipts.output_record(path)],
            extra={"stage_detail": "plan", "panels": len(plan["panels"])},
        )
        return plan
    except receipts.EngSftError as exc:
        writer.write_failure_receipt("audit", exc.reason, exc.offending, message=str(exc))
        raise


# --- 面板 -----------------------------------------------------------------

BOX_COLORS: tuple[tuple[int, int, int], ...] = (
    (255, 64, 0),
    (0, 200, 255),
    (255, 220, 0),
    (0, 255, 120),
)
CAPTION_BG = (0, 0, 0)
CAPTION_FG = (255, 255, 255)
CAPTION_HEIGHT = 16


def _load_pillow():
    try:
        from PIL import Image, ImageDraw  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - 依赖缺失路径
        raise PanelError(
            "面板生成需要 Pillow；本仓库已有 `.venv-yoloe`（Pillow 12.3.0）可用，例如 "
            "`.venv-yoloe/bin/python -m tools.eng_sft.label_audit panels`。本项不下载任何依赖。"
        ) from exc
    return Image, ImageDraw


def draw_panel(source: Path, destination: Path, panel: dict[str, Any]) -> None:
    """沿 ASSET-001 面板形态：原帧整幅不裁剪、标题置于帧外边带、框按同一偏移叠加。

    J3 叠加**全部** M 候选并编号；J4 只显示指令（无框）；J7 叠加该 bus 与其 S5 颜色字段。
    """
    from tools.eng_asset.label_panel import panel_layout, translated_box  # noqa: PLC0415

    Image, ImageDraw = _load_pillow()
    with Image.open(source) as handle:
        frame = handle.convert("RGB")
    width, height = frame.size
    layout = panel_layout(width, height, CAPTION_HEIGHT)
    canvas = Image.new("RGB", layout["canvas"], CAPTION_BG)
    canvas.paste(frame, layout["frame_origin"])
    draw = ImageDraw.Draw(canvas)
    caption = f"#{panel['panel_index']} [{panel['layer']}] {panel['state']} | {panel['surface']}"
    if panel["layer"] == "J7":
        caption += f" | S5 color={panel['extra'].get('s5_color')} (EXCLUDED)"
    draw.text((2, 2), caption, fill=CAPTION_FG)
    if panel["layer"] != "J4":
        for index, box in enumerate(panel["boxes_norm_xywh"]):
            corners = translated_box(box, width, height, layout["offset"])
            if corners is None:
                continue
            colour = BOX_COLORS[index % len(BOX_COLORS)]
            draw.rectangle(list(corners), outline=colour, width=2)
            if panel["layer"] == "J3":
                draw.text((corners[0] + 2, corners[1] + 2), str(index + 1), fill=colour)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format="JPEG", quality=95, subsampling=0)


def run_panels(
    *, repo_root: Path = PROJECT_ROOT, local_root: Path | None = None
) -> dict[str, Any]:
    """`panels`：抽样契约提交后生成面板与原图副本，回填 `overlay_sha256`。"""
    started = time.monotonic()
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    manifest = receipts.InputManifest(repo_root=root)
    panel_dir = local / build.PANEL_DIRNAME
    try:
        plan_file = plan_json_path(local)
        if not plan_file.is_file():
            raise receipts.AuditIncomplete("缺抽样计划，先跑 `plan`", offending=[str(plan_file)])
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
        audit_md = plan_path(root)
        status = build._git(["status", "--porcelain", "--", AUDIT_PATH.as_posix()], root).strip()
        tracked = build._git(["ls-files", "--", AUDIT_PATH.as_posix()], root).strip()
        if status or not tracked:
            raise receipts.FrozenFileDirty(
                f"抽样契约未提交或不干净：{AUDIT_PATH}（status={status or 'UNTRACKED'}）",
                offending=[{"path": AUDIT_PATH.as_posix(), "status": status, "tracked": bool(tracked)}],
            )
        head = build._git(["rev-parse", "HEAD"], root).strip()

        panel_dir.mkdir(parents=True, exist_ok=True)
        records: list[dict[str, Any]] = []
        for panel in plan["panels"]:
            source = root / panel["frame_id"]
            entry = manifest.record(source, source="原帧（面板读图）")
            original = panel_dir / f"panel-{panel['panel_index']:02d}-original.jpg"
            overlay = panel_dir / f"panel-{panel['panel_index']:02d}.jpg"
            receipts.assert_output_allowed(original, root)
            receipts.assert_output_allowed(overlay, root)
            shutil.copy2(source, original)
            draw_panel(source, overlay, panel)
            panel["overlay_sha256"] = receipts.sha256_file(overlay)
            records.append(
                {
                    "panel_index": panel["panel_index"],
                    "layer": panel["layer"],
                    "share": panel["share"],
                    "key": panel["key"],
                    "frame_id": panel["frame_id"],
                    "object_ids": panel["object_ids"],
                    "surface": panel["surface"],
                    "source_sha256": entry.sha256,
                    "original_copy_sha256": receipts.sha256_file(original),
                    "overlay_sha256": panel["overlay_sha256"],
                }
            )
        document = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/panel-receipt/v1",
            "work_id": receipts.WORK_ID,
            "utc": receipts.utc_stamp(),
            "head": head,
            "audit_document_sha256": receipts.sha256_file(audit_md),
            "panels": records,
        }
        receipt_path = writer._write_json(panel_dir / PANEL_RECEIPT_NAME, document)
        writer._write_json(plan_json_path(local), plan)
        (root / AUDIT_PATH).write_text(render_document(plan, repo_root=root), encoding="utf-8")
        panel_bytes = build._dir_bytes(panel_dir)
        if panel_bytes > build.PANEL_DIR_MAX_BYTES:
            raise receipts.EngSftError(f"`panel/` 超过 20 MB：{panel_bytes}")
        after = manifest.recompute()
        writer.save_input_manifest("audit", manifest, after, manifest.diff(after), successful=True)
        writer.write_run_receipt(
            "audit",
            started=started,
            outputs=[receipts.output_record(receipt_path)],
            extra={"stage_detail": "panels", "panels": len(records), "panel_bytes": panel_bytes},
        )
        return document
    except receipts.EngSftError as exc:
        writer.write_failure_receipt("audit", exc.reason, exc.offending, message=str(exc))
        raise


# --- 判定代录（只读 Unity 日志）------------------------------------------


@dataclass
class Verdict:
    panel_index: int
    values: dict[str, str]
    error_types: tuple[str, ...]


def _entry_body(text: str, entry: str) -> list[str]:
    lines = text.splitlines()
    heading = f"## {entry}"
    starts = [i for i, line in enumerate(lines) if line.strip() == heading]
    if len(starts) != 1:
        raise receipts.AuditIncomplete(
            f"Unity 日志条目缺失或重复：{entry}（{len(starts)} 处）", offending=[entry]
        )
    begin = starts[0]
    stop = len(lines)
    for index in range(begin + 1, len(lines)):
        stripped = lines[index].lstrip()
        if stripped.startswith("## ") or (stripped.startswith("# ") and not stripped.startswith("## ")):
            stop = index
            break
    return lines[begin + 1 : stop]


def read_unity_verdicts(
    path: Path, entry: str = UNITY_LOG_ENTRY
) -> tuple[dict[int, Verdict], str]:
    """严格解析代录机读格式 v1；格式不满足即 `AUDIT_INCOMPLETE`（不静默丢行）。"""
    if not Path(path).is_file():
        raise receipts.AuditIncomplete("Unity 日志不可读", offending=[str(path)])
    body = _entry_body(Path(path).read_text(encoding="utf-8"), entry)
    joined = "\n".join(body)
    for required in (VERDICT_SCHEMA_LINE, VERDICT_STATUS_LINE):
        if required not in joined:
            raise receipts.AuditIncomplete(f"代录缺行：{required}", offending=[required])
    state = "PENDING"
    for line in body:
        if line.strip().startswith(VERDICT_STATE_PREFIX):
            state = line.split(":", 1)[1].strip()
    verdicts: dict[int, Verdict] = {}
    for line in body:
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|---"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or not cells[0].isdigit():
            continue
        if len(cells) != 6:
            raise receipts.AuditIncomplete(
                f"代录表列数不是 6：{stripped}", offending=[stripped]
            )
        index = int(cells[0])
        values = {
            "状态": cells[1],
            "候选完整": cells[2],
            "颜色": cells[3],
            "关系方向": cells[4],
        }
        for name, value in values.items():
            if value not in VERDICT_VALUES:
                raise receipts.AuditIncomplete(
                    f"代录取值不在闭集：{name}={value!r}（panel {index}）",
                    offending=[{"panel_index": index, "field": name, "value": value}],
                )
        errors = tuple(
            token for token in re.split(r"[、,，/\s]+", cells[5]) if token and token != "-"
        )
        unknown = [token for token in errors if token not in ERROR_TYPES]
        if unknown:
            raise receipts.AuditIncomplete(
                f"错误类型不在闭集：{unknown}（panel {index}）", offending=unknown
            )
        if index in verdicts:
            raise receipts.AuditIncomplete(f"代录 panel_index 重复：{index}", offending=[index])
        verdicts[index] = Verdict(index, values, errors)
    return verdicts, state


def _gold_rows_matching(local_root: Path, frame_id: str, surface: str) -> dict[str, dict[str, int]]:
    """在四份 gold 文件里数该帧、以及该 (帧, surface) 的行数（排除证据用）。"""
    result: dict[str, dict[str, int]] = {}
    for name in build.GOLD_FILES:
        path = Path(local_root) / build.DATA_DIRNAME / name
        frame_rows = surface_rows = 0
        if path.is_file():
            with open(path, encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if row.get("frame_id") != frame_id:
                        continue
                    frame_rows += 1
                    if row.get("surface") == surface:
                        surface_rows += 1
        result[name] = {"frame_rows": frame_rows, "surface_rows": surface_rows}
    return result


def verdict_digest(verdicts: dict[int, Verdict]) -> str:
    """对结构化判定取摘要：判定一变（新增「错」、改判、加行），闭合记录即失效。"""
    payload = json.dumps(
        [
            [index, verdicts[index].values, list(verdicts[index].error_types)]
            for index in sorted(verdicts)
        ],
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def user_share_digest(plan: dict[str, Any]) -> str:
    """对当前计划的用户份额取摘要（样本身份 + 叠加图字节）。

    R1@K4 F1：判定表只按 `panel_index` 记值，计划重抽后同一序号可能已是另一张图，而判定值
    恰好相同时 `verdict_digest` 不变。闭合记录因此还要绑定写入时的整份用户份额——计划或
    面板一变，旧闭合即失效，不能把旧样本上的裁定带到新样本上。
    """
    payload = json.dumps(
        [
            [
                panel["panel_index"],
                panel["layer"],
                panel["key"],
                panel["frame_id"],
                panel["surface"],
                list(panel.get("object_ids", [])),
                panel.get("overlay_sha256"),
            ]
            for panel in sorted(plan["panels"], key=lambda p: p["panel_index"])
            if panel["share"] == "user"
        ],
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def closure_receipt_path(local_root: Path) -> Path:
    return Path(local_root) / receipts.RECEIPTS_DIRNAME / CLOSURE_RECEIPT_NAME


def load_closure(local_root: Path) -> dict[str, Any] | None:
    path = closure_receipt_path(local_root)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def wrong_panels(plan: dict[str, Any], verdicts: dict[int, Verdict]) -> list[int]:
    """用户份额里任一受判字段为「错」的面板序号（层决定判哪些字段）。"""
    user_panels = {p["panel_index"]: p for p in plan["panels"] if p["share"] == "user"}
    return sorted(
        index
        for index, verdict in verdicts.items()
        if index in user_panels
        and any(
            verdict.values.get(field) == "错" for field in JUDGED_FIELDS[user_panels[index]["layer"]]
        )
    )


def audit_gate_state(
    *, repo_root: Path = PROJECT_ROOT, local_root: Path | None = None
) -> dict[str, Any]:
    """`freeze` 的抽查前提：用户份额判定齐全且无「错」。

    返回 `reason`：None（放行）/ `AUDIT_INCOMPLETE` / `AUDIT_FINDING_OPEN`。
    「不确定」不阻止冻结，只在统计里单列。
    """
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    plan_file = plan_json_path(local)
    if not plan_file.is_file():
        return {
            "reason": "AUDIT_INCOMPLETE",
            "message": "缺表 J 抽样计划（未跑 plan/panels）",
            "offending": [str(plan_file)],
            "summary": {},
        }
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    user_panels = {p["panel_index"]: p for p in plan["panels"] if p["share"] == "user"}
    try:
        verdicts, state = read_unity_verdicts(root / UNITY_LOG_PATH)
    except receipts.AuditIncomplete as exc:
        return {
            "reason": "AUDIT_INCOMPLETE",
            "message": str(exc),
            "offending": exc.offending,
            "summary": {"user_panels": len(user_panels)},
        }
    unjudged = sorted(set(user_panels) - set(verdicts))
    if unjudged or state != "COMPLETE":
        return {
            "reason": "AUDIT_INCOMPLETE",
            "message": f"用户份额未判定齐全（未判定 {len(unjudged)} 张，state={state}）",
            "offending": unjudged[:20],
            "summary": {"user_panels": len(user_panels), "judged": len(verdicts), "state": state},
        }
    wrong = wrong_panels(plan, verdicts)
    digest = verdict_digest(verdicts)
    summary = {
        "user_panels": len(user_panels),
        "judged": len(verdicts),
        "state": state,
        "wrong": wrong,
        "uncertain": sorted(
            index
            for index, verdict in verdicts.items()
            if index in user_panels and "不确定" in verdict.values.values()
        ),
        "verdict_digest": digest,
        "user_share_digest": user_share_digest(plan),
    }
    if not wrong:
        return {"reason": None, "message": "用户份额判定齐全且无「错」", "offending": [], "summary": summary}

    # 有「错」：只有接受角色具名裁定并落成闭合记录后才放行，且只放行记录里的那几张。
    closure = load_closure(local)
    if closure is None:
        return {
            "reason": "AUDIT_FINDING_OPEN",
            "message": f"用户判定出现「错」：panel {wrong}（尚无闭合记录）",
            "offending": wrong,
            "summary": summary,
        }
    closed = sorted(int(entry["panel_index"]) for entry in closure.get("panels", []))
    summary["closure"] = {
        "panels": closed,
        "disposition": closure.get("disposition"),
        "ruling": closure.get("ruling"),
        "finding_receipt_sha256": closure.get("finding_receipt_sha256"),
    }
    if closure.get("verdict_digest") != digest:
        return {
            "reason": "AUDIT_FINDING_OPEN",
            "message": "闭合记录已过期：判定表在闭合后发生变化（新增/改判）",
            "offending": wrong,
            "summary": summary,
        }
    # C1-6：闭合记录不是一张免检票——消费端逐项复核它当初绑定的东西现在还成立。
    binding_problems: list[dict[str, Any]] = []
    finding_path = Path(local) / receipts.RECEIPTS_DIRNAME / FINDING_RECEIPT_NAME
    if not finding_path.is_file():
        binding_problems.append({"item": FINDING_RECEIPT_NAME, "problem": "ORIGINAL_RECEIPT_MISSING"})
    elif receipts.sha256_file(finding_path) != closure.get("finding_receipt_sha256"):
        binding_problems.append({"item": FINDING_RECEIPT_NAME, "problem": "ORIGINAL_RECEIPT_CHANGED"})
    by_index = {p["panel_index"]: p for p in plan["panels"]}
    for entry in closure.get("panels", []):
        index = int(entry["panel_index"])
        panel = by_index.get(index)
        if panel is None:
            binding_problems.append({"panel_index": index, "problem": "PANEL_GONE"})
            continue
        for field_name, recorded in (
            ("key", entry.get("key")),
            ("frame_id", entry.get("frame_id")),
            ("surface", entry.get("surface")),
            ("overlay_sha256", entry.get("overlay_sha256")),
        ):
            if panel.get(field_name) != recorded:
                binding_problems.append(
                    {"panel_index": index, "field": field_name,
                     "closure": recorded, "current": panel.get(field_name)}
                )
        if list(panel.get("object_ids", [])) != list(entry.get("boxed_object_ids", [])):
            binding_problems.append({"panel_index": index, "field": "object_ids"})
        # (ii) 的前提是该 noun 确已排除；现在若又出现在 gold 文件里，闭合即失效。
        current = _gold_rows_matching(local, entry["frame_id"], entry["surface"])
        leaked = {name: counts for name, counts in current.items() if counts["surface_rows"]}
        if leaked:
            binding_problems.append({"panel_index": index, "problem": "NOUN_BACK_IN_GOLD", "files": leaked})
    if binding_problems:
        summary["closure"]["binding_problems"] = binding_problems[:20]
        return {
            "reason": "AUDIT_FINDING_OPEN",
            "message": "闭合记录的绑定已不成立（原收据/面板身份/排除证据对不上）",
            "offending": binding_problems[:20],
            "summary": summary,
        }
    # R1@K4 F1：闭合记录只对写入时的那份用户份额有效；计划重抽或面板重绘（含未判错的面板）
    # 之后必须按新计划重新闭合，不能凭判定值恰好相同沿用旧记录。
    if closure.get("user_share_digest") != summary["user_share_digest"]:
        return {
            "reason": "AUDIT_FINDING_OPEN",
            "message": "闭合记录已过期：用户份额面板（样本身份或叠加图）在闭合后发生变化",
            "offending": wrong,
            "summary": summary,
        }

    unruled = [index for index in wrong if index not in closed]
    if unruled:
        return {
            "reason": "AUDIT_FINDING_OPEN",
            "message": f"仍有未裁定的「错」：panel {unruled}",
            "offending": unruled,
            "summary": summary,
        }
    return {
        "reason": None,
        "message": f"「错」panel {wrong} 已按表 J ({closure.get('disposition')}) 具名裁定并落实闭合记录",
        "offending": [],
        "summary": summary,
    }


def _counts_block(plan: dict[str, Any], verdicts: dict[int, Verdict]) -> str:
    rows: list[str] = []
    rows.append("| 层 | 用户面板 | 已判定 | 状态对 | 状态错 | 状态不确定 | 其他字段错 | 未判定 |")
    rows.append("|---|---|---|---|---|---|---|---|")
    for layer, _user_quota, _prescreen in LAYER_QUOTAS:
        panels = [p for p in plan["panels"] if p["share"] == "user" and p["layer"] == layer]
        judged = [verdicts[p["panel_index"]] for p in panels if p["panel_index"] in verdicts]
        counter = Counter(v.values["状态"] for v in judged)
        other_wrong = sum(
            1
            for v in judged
            if any(v.values.get(f) == "错" for f in JUDGED_FIELDS[layer] if f != "状态")
        )
        rows.append(
            f"| {layer} | {len(panels)} | {len(judged)} | {counter.get('对', 0)} | "
            f"{counter.get('错', 0)} | {counter.get('不确定', 0)} | {other_wrong} | "
            f"{len(panels) - len(judged)} |"
        )
    errors = Counter(token for v in verdicts.values() for token in v.error_types)
    rows.append("")
    rows.append(
        "错误类型计数："
        + ("、".join(f"{name} {count}" for name, count in sorted(errors.items())) or "（无）")
    )
    rows.append("")
    rows.append("「不确定」单列、不计为对；未判定行计 unjudged。判定原文见 Unity 日志条目 "
                f"`{UNITY_LOG_ENTRY}`。")
    return "\n".join(rows)


def run_close(
    *,
    disposition: str,
    ruling_anchor: str,
    repo_root: Path = PROJECT_ROOT,
    local_root: Path | None = None,
) -> dict[str, Any]:
    """AC-14 修订 3：把接受角色的具名裁定与原判定/面板/排除证据绑成闭合记录。

    只在**当前判定确有「错」**时可写；逐张绑定面板身份（叠框对象、框、S5 颜色词，与触发
    排除的 counterexample 分列）、原 `AUDIT_FINDING_OPEN` 收据的 SHA（收据保留不删）、
    裁定出处（提案路径 + 运行时解析的提交 + 逐字锚点）与判定表摘要。写完后
    `freeze` 只放行记录里的这几张；判定一变摘要即不符，闭合自动失效。
    """
    started = time.monotonic()
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    try:
        if disposition not in RULING_DISPOSITIONS:
            raise receipts.AuditIncomplete(
                f"处置不在表 J 闭集：{disposition!r}（{RULING_DISPOSITIONS}）", offending=[disposition]
            )
        plan = json.loads(plan_json_path(local).read_text(encoding="utf-8"))
        verdicts, state = read_unity_verdicts(root / UNITY_LOG_PATH)
        if state != "COMPLETE":
            raise receipts.AuditIncomplete(f"判定未齐全（state={state}），不得写闭合记录", offending=[state])
        wrong = wrong_panels(plan, verdicts)
        if not wrong:
            raise receipts.AuditIncomplete("当前判定没有「错」，无需闭合记录", offending=[])
        finding_path = writer.receipts_dir / FINDING_RECEIPT_NAME
        if not finding_path.is_file():
            raise receipts.AuditIncomplete(
                "缺原 `AUDIT_FINDING_OPEN` 收据（先跑 stats），不得跳过历史直接闭合",
                offending=[FINDING_RECEIPT_NAME],
            )

        proposal = root / PROPOSAL_PATH
        text = proposal.read_text(encoding="utf-8")
        if ruling_anchor not in text:
            raise receipts.AuditIncomplete(
                f"裁定锚点未出现在提案里：{ruling_anchor!r}", offending=[ruling_anchor]
            )
        ruling_commit = build._git(
            ["log", "-1", "--format=%H", "--", PROPOSAL_PATH.as_posix()], root
        ).strip()

        by_index = {p["panel_index"]: p for p in plan["panels"]}
        entries: list[dict[str, Any]] = []
        for index in wrong:
            panel = by_index[index]
            surface = panel["surface"]
            evidence = _gold_rows_matching(local, panel["frame_id"], surface)
            leaked = {name: counts for name, counts in evidence.items() if counts["surface_rows"]}
            if leaked:
                raise receipts.AuditIncomplete(
                    f"panel {index} 的 noun 仍出现在 gold 文件里，(ii) 的排除前提不成立",
                    offending=[{"panel_index": index, "files": leaked}],
                )
            verdict = verdicts[index]
            entries.append(
                {
                    "panel_index": index,
                    "layer": panel["layer"],
                    "key": panel["key"],
                    "frame_id": panel["frame_id"],
                    "surface": surface,
                    "boxed_object_ids": panel["object_ids"],
                    "boxes_norm_xywh": panel["boxes_norm_xywh"],
                    "s5_color_word": panel.get("extra", {}).get("s5_color"),
                    "counterexample_object_ids": panel.get("extra", {}).get(
                        "counterexample_object_ids", []
                    ),
                    "overlay_sha256": panel.get("overlay_sha256"),
                    "user_verdict": verdict.values,
                    "user_error_types": list(verdict.error_types),
                    "exclusion_evidence": evidence,
                }
            )

        document = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/audit-finding-closure/v1",
            "work_id": receipts.WORK_ID,
            "utc": receipts.utc_stamp(),
            "disposition": disposition,
            "ruling": {
                "source": PROPOSAL_PATH.as_posix(),
                "anchor": ruling_anchor,
                "commit": ruling_commit,
            },
            "finding_receipt": FINDING_RECEIPT_NAME,
            "finding_receipt_sha256": receipts.sha256_file(finding_path),
            "verdict_digest": verdict_digest(verdicts),
            "user_share_digest": user_share_digest(plan),
            "unity_log_entry": UNITY_LOG_ENTRY,
            "panels": entries,
        }
        path = writer._write_json(writer.receipts_dir / CLOSURE_RECEIPT_NAME, document)
        writer.write_run_receipt(
            "audit",
            started=started,
            outputs=[receipts.output_record(path)],
            extra={"stage_detail": "close", "panels": wrong, "disposition": disposition},
        )
        return document
    except receipts.EngSftError as exc:
        writer.write_failure_receipt("audit", exc.reason, exc.offending, message=str(exc))
        raise


def run_stats(
    *, repo_root: Path = PROJECT_ROOT, local_root: Path | None = None
) -> dict[str, Any]:
    """`stats`：只读 Unity 日志条目 → 统计块写进抽查文件；有「错」写开放收据。"""
    started = time.monotonic()
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    plan = json.loads(plan_json_path(local).read_text(encoding="utf-8"))
    state = audit_gate_state(repo_root=root, local_root=local)
    verdicts: dict[int, Verdict] = {}
    if state["reason"] != "AUDIT_INCOMPLETE":
        verdicts, _ = read_unity_verdicts(root / UNITY_LOG_PATH)
    plan["stats_block"] = _counts_block(plan, verdicts)
    writer._write_json(plan_json_path(local), plan)
    (root / AUDIT_PATH).write_text(render_document(plan, repo_root=root), encoding="utf-8")
    finding_action = None
    if state["reason"] == "AUDIT_FINDING_OPEN":
        finding_action = _record_open_finding(writer, state)
    writer.write_run_receipt(
        "audit",
        started=started,
        outputs=[receipts.output_record(root / AUDIT_PATH)],
        extra={
            "stage_detail": "stats",
            "gate": state["reason"] or "OPEN_OK",
            "summary": state["summary"],
            "finding_receipt": finding_action,
        },
    )
    return state


def _record_open_finding(writer: receipts.ReceiptWriter, state: dict[str, Any]) -> str:
    """AC-14 修订 3：原 `AUDIT_FINDING_OPEN` 收据是该 finding 的开放历史，重跑 `stats` 不改写它。

    「错」面板集合与原收据相同（例如计划重抽后闭合记录过期、只需重绑）→ 原收据逐字节保留；
    集合变了（新的 finding）→ 先把旧收据原样另存为 `audit-finding-open.superseded-<utc>.json`，
    再写新收据。收据里的 `panels` 始终是面板序号，不是闭合绑定问题的明细。
    """
    wrong = sorted(int(index) for index in state["summary"].get("wrong", []))
    path = writer.receipts_dir / FINDING_RECEIPT_NAME
    if path.is_file():
        existing = json.loads(path.read_text(encoding="utf-8"))
        recorded = existing.get("panels", [])
        if all(isinstance(index, int) for index in recorded) and sorted(recorded) == wrong:
            return "preserved"
        stamp = existing.get("utc") or receipts.utc_stamp()
        archived = writer.receipts_dir / f"audit-finding-open.superseded-{stamp}.json"
        receipts.assert_output_allowed(archived, writer.repo_root)
        archived.write_bytes(path.read_bytes())
    writer._write_json(
        path,
        {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/audit-finding-open/v1",
            "work_id": receipts.WORK_ID,
            "utc": receipts.utc_stamp(),
            "panels": wrong,
            "message": state["message"],
        },
    )
    return "written"


def run_prescreen(
    results_path: Path, *, repo_root: Path = PROJECT_ROOT, local_root: Path | None = None
) -> dict[str, Any]:
    """`prescreen`：把实现角色的看图预筛结果写进抽查文件（披露，不计为核验）。"""
    started = time.monotonic()
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    plan = json.loads(plan_json_path(local).read_text(encoding="utf-8"))
    allowed = {p["panel_index"]: p for p in plan["panels"] if p["share"] == "prescreen"}
    results = json.loads(Path(results_path).read_text(encoding="utf-8"))
    rows: list[str] = [
        "| panel_index | 层 | 状态 | 候选完整 | 颜色 | 关系方向 | 错误类型 | 备注 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    counter: Counter = Counter()
    for item in sorted(results, key=lambda r: r["panel_index"]):
        index = item["panel_index"]
        if index not in allowed:
            raise receipts.AuditIncomplete(
                f"预筛结果含非预筛份额面板：{index}", offending=[index]
            )
        layer = allowed[index]["layer"]
        values = {name: item.get(name, "NA") for name in ("状态", "候选完整", "颜色", "关系方向")}
        for name, value in values.items():
            if value not in VERDICT_VALUES:
                raise receipts.AuditIncomplete(
                    f"预筛取值不在闭集：{name}={value!r}（panel {index}）", offending=[index]
                )
        errors = item.get("错误类型") or []
        unknown = [token for token in errors if token not in ERROR_TYPES]
        if unknown:
            raise receipts.AuditIncomplete(f"预筛错误类型不在闭集：{unknown}", offending=unknown)
        counter[values["状态"]] += 1
        rows.append(
            f"| {index} | {layer} | {values['状态']} | {values['候选完整']} | {values['颜色']} | "
            f"{values['关系方向']} | {('、'.join(errors)) or '—'} | {item.get('备注', '')} |"
        )
    rows.append("")
    rows.append(
        f"预筛 {len(results)} 张（上限 {PRESCREEN_CAP}）：状态对 {counter.get('对', 0)}、"
        f"错 {counter.get('错', 0)}、不确定 {counter.get('不确定', 0)}。"
        "**预筛只作披露，不计为语义核验，不改变任何冻结决定。**"
    )
    plan["prescreen_block"] = "\n".join(rows)
    writer._write_json(plan_json_path(local), plan)
    (root / AUDIT_PATH).write_text(render_document(plan, repo_root=root), encoding="utf-8")
    writer.write_run_receipt(
        "audit",
        started=started,
        outputs=[receipts.output_record(root / AUDIT_PATH)],
        extra={"stage_detail": "prescreen", "rows": len(results)},
    )
    return {"rows": len(results), "counts": dict(counter)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-SFT-002 表 J 标签语义抽查")
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--local-root", default=None)
    subparsers = parser.add_subparsers(dest="stage", required=True)
    subparsers.add_parser("plan", help="分层抽样并写抽样契约")
    subparsers.add_parser("panels", help="生成面板与原图副本（需 Pillow）")
    prescreen = subparsers.add_parser("prescreen", help="写入实现者预筛表")
    prescreen.add_argument("--results", required=True)
    subparsers.add_parser("stats", help="只读 Unity 日志条目并统计")
    close = subparsers.add_parser("close", help="按接受角色的具名裁定写闭合记录（AC-14 修订 3）")
    close.add_argument("--disposition", required=True, choices=list(RULING_DISPOSITIONS))
    close.add_argument("--ruling-anchor", required=True, help="提案里该裁定的逐字锚点")
    subparsers.add_parser("state", help="打印冻结前提状态")

    args = parser.parse_args(argv)
    root = Path(args.repo_root)
    local = Path(args.local_root) if args.local_root else None
    try:
        if args.stage == "plan":
            plan = run_plan(repo_root=root, local_root=local)
            print(f"plan ok：用户 {plan['user_rows']} 张 + 预筛 {plan['prescreen_rows']} 张")
        elif args.stage == "panels":
            document = run_panels(repo_root=root, local_root=local)
            print(f"panels ok：{len(document['panels'])} 张，HEAD {document['head'][:12]}")
        elif args.stage == "prescreen":
            result = run_prescreen(Path(args.results), repo_root=root, local_root=local)
            print(f"prescreen ok：{result['rows']} 行 {result['counts']}")
        elif args.stage == "close":
            document = run_close(
                disposition=args.disposition,
                ruling_anchor=args.ruling_anchor,
                repo_root=root,
                local_root=local,
            )
            print(
                f"close ok：panel {[e['panel_index'] for e in document['panels']]} 按 "
                f"({document['disposition']}) 闭合，裁定 {document['ruling']['anchor']} @ "
                f"{document['ruling']['commit'][:12]}"
            )
        elif args.stage == "stats":
            state = run_stats(repo_root=root, local_root=local)
            print(f"stats ok：{state['reason'] or 'OPEN_OK'} — {state['message']}")
        else:
            state = audit_gate_state(repo_root=root, local_root=local)
            print(json.dumps(state, ensure_ascii=False, indent=2))
    except receipts.EngSftError as exc:
        print(f"{args.stage} 失败（{exc.reason}）：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
