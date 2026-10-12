#!/usr/bin/env python3
"""表 A 三态派生（`unique` / `ambiguous` / `none` 与三类灰区）。

输入是适配器产出的**统一对象记录**（表 C 第一行），不是 S3 原行：本模块对
数据来源一无所知，Unity 与其他环境共用同一判定。名词短语的两个谓词逐字复用
`tools.dist_data.tier1_lang` 的 `_noun_conflicts`（通配冲突，未知不排除）与
`_noun_satisfies`（严格确证），**不改上游函数**。

规则 ①（合同 §3 表 A）：若 `dynamic-target` 落在冲突集 C 内、适配器标记
`definite = true` 且它确证满足该名词，则它并入确证集 M。这与
`P1-VLM-DATA-001` BC-DATA-8.3/9（动态目标永不可作 target/ref）**不同**——那是
研究指称唯一性合同，这里是工程数据合同：已绑定且框有效的目标车是可框选的
`car` 候选。上游 `SceneObject.referable` 对目标车恒为 False，故 M₀ 里永远没有
它，并入是集合并、不会重复计数。

判定按序、互斥（表 A 六行），灰区一律不产生训练/评估 gold。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from tools.dist_data import tier1_lang

# 表 A 状态闭集：前三个是三态协议输出，后三个是灰区（排除或只作诊断）。
STATE_UNIQUE = "unique"
STATE_AMBIGUOUS = "ambiguous"
STATE_NONE = "none"
STATE_GRAY_OVERFLOW = "gray_overflow"
STATE_GRAY_DEFINITE_PLUS_UNCERTAIN = "gray_definite_plus_uncertain"
STATE_GRAY_UNCERTAIN_NONE = "gray_uncertain_none"

STATES: tuple[str, ...] = (
    STATE_UNIQUE,
    STATE_AMBIGUOUS,
    STATE_NONE,
    STATE_GRAY_OVERFLOW,
    STATE_GRAY_DEFINITE_PLUS_UNCERTAIN,
    STATE_GRAY_UNCERTAIN_NONE,
)
# 三态协议本身的输出闭集（prompt v2 的三种 JSON 骨架与之一一对应）。
PROTOCOL_STATES: tuple[str, ...] = (STATE_UNIQUE, STATE_AMBIGUOUS, STATE_NONE)

# 表 A 第 3 行：ambiguous 上限 4 个候选；第 4 行 ≥ 5 即 `gray_overflow`。
AMBIGUOUS_MAX = 4
DYNAMIC_TARGET_ID = "dynamic-target"


@dataclass(frozen=True)
class ObjectRecord:
    """统一对象记录（表 C 第一行）。

    属性名与 `tier1_lang.SceneObject` 前四项一致，两个名词谓词可直接消费本记录
    （鸭子类型），不必把适配器输出再转回上游类型。
    """

    object_id: str
    class_word: str | None
    color_word: str | None
    referable: bool
    status: str
    visible_norm_xywh: list[float] | None = None
    definite: bool = False
    # 与 `tier1_lang.SceneObject` 同名的三个几何字段：G4 的关系程序要在**同一个**
    # 执行域上 `execute`，字段值逐字沿用上游 `frame_world` 的赋值，不另算一份。
    center_px: tuple[float, float] | None = None
    world_xz: tuple[float, float] | None = None
    route_side: int | None = None

    def as_dict(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "object_id": self.object_id,
            "class_word": self.class_word,
            "color_word": self.color_word,
            "referable": self.referable,
            "status": self.status,
            "visible_norm_xywh": self.visible_norm_xywh,
        }
        if self.object_id == DYNAMIC_TARGET_ID:
            record["definite"] = self.definite
        return record


@dataclass(frozen=True)
class ThreeStateResult:
    """一条 (帧, 名词) 的派生结果。

    `target_object_ids` 只在 `unique`/`ambiguous` 非空（ambiguous 按 `object_id`
    升序，落盘前再按框升序重排，见 `prompt_v2.gold_text`）；灰区 `definite_ids`
    保留 M 的成员供 G3′ 诊断取框，`conflict_ids` 保留 C 供披露。
    """

    state: str
    target_object_ids: tuple[str, ...]
    definite_ids: tuple[str, ...]
    conflict_ids: tuple[str, ...]


def _conflicts(objects: Sequence[ObjectRecord], noun: dict[str, Any]) -> list[ObjectRecord]:
    return [obj for obj in objects if tier1_lang._noun_conflicts(obj, noun)]


def three_state(objects: Iterable[ObjectRecord], noun: dict[str, Any]) -> ThreeStateResult:
    """表 A：在执行域 `objects` 上对名词短语 `noun` 派生三态。

    `noun` 是 `{"class": <九类之一>}` 或 `{"class": …, "color": …}`。
    """
    domain = list(objects)
    conflicting = _conflicts(domain, noun)
    definite = [
        obj for obj in conflicting if obj.referable and tier1_lang._noun_satisfies(obj, noun)
    ]
    # 规则 ①：已绑定且框有效的目标车并入确证集（集合并，不重复计数）。
    definite_ids = {obj.object_id for obj in definite}
    for obj in conflicting:
        if obj.object_id != DYNAMIC_TARGET_ID or not obj.definite:
            continue
        if obj.object_id in definite_ids:
            continue
        if tier1_lang._noun_satisfies(obj, noun):
            definite.append(obj)
            definite_ids.add(obj.object_id)

    conflict_ids = tuple(sorted(obj.object_id for obj in conflicting))
    members = tuple(sorted(obj.object_id for obj in definite))

    if not conflicting:  # 1
        return ThreeStateResult(STATE_NONE, (), (), ())
    if len(conflicting) == len(definite):
        if len(definite) == 1:  # 2
            return ThreeStateResult(STATE_UNIQUE, members, members, conflict_ids)
        if len(definite) <= AMBIGUOUS_MAX:  # 3
            return ThreeStateResult(STATE_AMBIGUOUS, members, members, conflict_ids)
        return ThreeStateResult(STATE_GRAY_OVERFLOW, (), members, conflict_ids)  # 4
    if definite:  # 5
        return ThreeStateResult(STATE_GRAY_DEFINITE_PLUS_UNCERTAIN, (), members, conflict_ids)
    return ThreeStateResult(STATE_GRAY_UNCERTAIN_NONE, (), (), conflict_ids)  # 6
