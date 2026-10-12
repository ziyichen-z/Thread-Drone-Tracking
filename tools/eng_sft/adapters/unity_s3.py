#!/usr/bin/env python3
"""表 A′：Unity S3 逐帧记录 → 统一对象记录（含 `definite` 与 `frame_wildcard`）。

S3 = `runtime/dist-data/frames_catalog/attempt-2`（只读）。目录对象、phantom 与
未知类别阻断体的字段赋值复用 `build_catalog.frame_world`（不改上游）；本适配器
在其之上做三件上游不做的事：

1. **目标车框**：`target_blocker_px` 裁剪到画幅后归一化，作为 `dynamic-target`
   的 `visible_norm_xywh`（规则 ① 的框来源）。
2. **`definite` 标记**：目标车在视野内 ∧ `target_source_bound` ∧ 裁剪后正面积。
3. **整帧通配 `frame_wildcard`**（AD3-3）：目标车在视野内但未绑定 / 缺框 /
   裁剪后退化时，该帧不产生任何 noun 的样本。这一判定**直接由本帧原始字段算出**
   （`blocking` 成员、`target_source_bound`、`target_blocker_px`），不依赖
   `frame_world` 对目标车字段的赋值。

`#27` 反例（`Vehicle_Bus_color03`）在域内时，该帧全部 `bus` 的 color noun 排除
（训练与评估都排除，不回写 S5），由 `excluded_color_classes` 交给构建器执行。
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Sequence

from tools.dist_data import build_catalog
from tools.eng_sft.three_state import DYNAMIC_TARGET_ID, ObjectRecord

# Unity 帧尺寸（表 D′ 的短边像素与目标框归一化都按这一对常量）。
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# 表 A′：已知颜色反例，所在帧的 `bus` 颜色指令整帧排除。
COLOR_COUNTEREXAMPLE_OBJECT = "Vehicle_Bus_color03"
COLOR_COUNTEREXAMPLE_CLASS = "bus"

WILDCARD_UNBOUND = "UNBOUND"
WILDCARD_MISSING_BOX = "MISSING_BOX"
WILDCARD_DEGENERATE_AFTER_CROP = "DEGENERATE_AFTER_CROP"

_FRAME_INDEX_RE = re.compile(r"frame_(\d+)\.jpg$")


@dataclass(frozen=True)
class FrameRecord:
    """一帧的统一记录：执行域对象 + 帧级标记。"""

    frame_id: str
    family: str
    frame_index: int
    station_key: str
    objects: tuple[ObjectRecord, ...]
    frame_wildcard: bool
    wildcard_reason: str | None
    dynamic_target_present: bool
    dynamic_target_definite: bool
    excluded_color_classes: frozenset[str]

    def box_of(self, object_id: str) -> list[float] | None:
        for obj in self.objects:
            if obj.object_id == object_id:
                return obj.visible_norm_xywh
        return None

    def object_ids(self) -> tuple[str, ...]:
        return tuple(obj.object_id for obj in self.objects)


def instance_base(object_id: str) -> str:
    """去掉 Unity 的实例后缀：`Vehicle_Bus_color03 (1)` → `Vehicle_Bus_color03`。"""
    return object_id.split(" (", 1)[0]


def frame_index(frame_id: str) -> int:
    match = _FRAME_INDEX_RE.search(frame_id)
    return int(match.group(1)) if match else -1


def is_usable_entry(entry: dict[str, Any]) -> bool:
    """S3 的可用性前提：布局绑定有效且 sidecar 完整（上游归档语义，不放宽）。"""
    return bool(entry.get("layout_binding_valid")) and bool(entry.get("sidecar_complete"))


def cropped_target_box(entry: dict[str, Any]) -> list[float] | None:
    """`target_blocker_px` 裁剪到画幅后的归一化 top-left xywh；退化返回 None。"""
    box: Sequence[float] | None = entry.get("target_blocker_px")
    if not box:
        return None
    x1 = max(0.0, float(box[0]))
    y1 = max(0.0, float(box[1]))
    x2 = min(float(FRAME_WIDTH), float(box[2]))
    y2 = min(float(FRAME_HEIGHT), float(box[3]))
    if x2 <= x1 or y2 <= y1:
        return None
    return [x1 / FRAME_WIDTH, y1 / FRAME_HEIGHT, (x2 - x1) / FRAME_WIDTH, (y2 - y1) / FRAME_HEIGHT]


def wildcard_reason(entry: dict[str, Any]) -> str | None:
    """表 A′ / AD3-3：目标车在视野内却不可用时的整帧通配原因（否则 None）。"""
    if DYNAMIC_TARGET_ID not in set(entry.get("blocking", ())):
        return None
    if not entry.get("target_source_bound"):
        return WILDCARD_UNBOUND
    if not entry.get("target_blocker_px"):
        return WILDCARD_MISSING_BOX
    if cropped_target_box(entry) is None:
        return WILDCARD_DEGENERATE_AFTER_CROP
    return None


def adapt_frame(
    entry: dict[str, Any],
    field_catalog: dict[str, Any],
    *,
    world: "build_catalog.FrameWorld | None" = None,
) -> FrameRecord:
    """把一条 S3 逐帧记录转成统一记录（表 A′ 逐行）。

    `world` 可由调用方传入已经算好的执行域（同一帧在一次扫描里也要用于七值对账，
    构造两次纯属重复计算）；不传则现算。
    """
    world = world if world is not None else build_catalog.frame_world(entry, field_catalog)
    statuses = {item["object_id"]: item.get("status") for item in entry["objects"]}
    boxes = {
        item["object_id"]: item.get("visible_norm_xywh")
        for item in entry["objects"]
        if item.get("visible_norm_xywh")
    }

    catalog_objects = field_catalog.get("objects", {})
    reason = wildcard_reason(entry)
    target_present = DYNAMIC_TARGET_ID in set(entry.get("blocking", ()))
    target_box = cropped_target_box(entry) if target_present else None
    definite = bool(target_present and entry.get("target_source_bound") and target_box is not None)

    objects: list[ObjectRecord] = []
    for obj in world.domain:
        if obj.object_id == DYNAMIC_TARGET_ID:
            objects.append(
                ObjectRecord(
                    object_id=obj.object_id,
                    class_word=obj.class_word,
                    color_word=obj.color_word,
                    referable=obj.referable,
                    status="DYNAMIC_TARGET",
                    visible_norm_xywh=target_box,
                    definite=definite,
                    center_px=obj.center_px,
                    world_xz=obj.world_xz,
                    route_side=obj.route_side,
                )
            )
            continue
        # 表 A′「类别未验证」：上游 `frame_world` 对存在的 S5 记录直接取 `record["class"]`，
        # 不看 `class_verified`。本适配层按表 A′ 把未验证类别清成 None（= 通配冲突），
        # 不改上游。当前输入上这一分支为空：执行域内 93 辆车全部 `class_verified=True`，
        # 另有 8 辆无 S5 条目（`frame_world` 已给 None），故本修正零行改变（见数据报告 §11）。
        stored = catalog_objects.get(obj.object_id)
        class_word = obj.class_word
        if not obj.object_id.startswith("phantom:") and stored is not None:
            if not stored.get("class_verified"):
                class_word = None
        objects.append(
            ObjectRecord(
                object_id=obj.object_id,
                class_word=class_word,
                color_word=obj.color_word,
                referable=obj.referable,
                status=statuses.get(obj.object_id, "UNKNOWN"),
                visible_norm_xywh=boxes.get(obj.object_id),
                center_px=obj.center_px,
                world_xz=obj.world_xz,
                route_side=obj.route_side,
            )
        )

    # #27 的匹配口径：Unity 的同一 prefab 在场景里以 `<名字>` 与 `<名字> (n)` 两种形式出现，
    # 二者是同一个 prefab 的实例，所以按「去掉实例后缀后逐字相等」匹配，而不是前缀包含——
    # `Vehicle_Bus_color03x` 之类不同名字不会被误命中（`instance_base` 只切 " (")。
    excluded: set[str] = set()
    for obj in objects:
        if instance_base(obj.object_id) == COLOR_COUNTEREXAMPLE_OBJECT:
            excluded.add(COLOR_COUNTEREXAMPLE_CLASS)
            break

    station = entry.get("station_bin") or {}
    return FrameRecord(
        frame_id=entry["frame_id"],
        family=entry["family"],
        frame_index=frame_index(entry["frame_id"]),
        station_key=station.get("key"),
        objects=tuple(objects),
        frame_wildcard=reason is not None,
        wildcard_reason=reason,
        dynamic_target_present=target_present,
        dynamic_target_definite=definite,
        excluded_color_classes=frozenset(excluded),
    )


def short_side_px(box_norm: Sequence[float]) -> float:
    """表 D′：框的短边像素 `min(w·640, h·480)`。"""
    return min(box_norm[2] * FRAME_WIDTH, box_norm[3] * FRAME_HEIGHT)
