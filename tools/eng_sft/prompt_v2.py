#!/usr/bin/env python3
"""表 B：prompt v2（逐字冻结）、坐标整数化与 gold 序列化（纯标准库）。

本模块是**冻结闭集**成员，也是 K3 代码束成员：本地构建/预检/评分与云端
训练/冒烟/预检调用同一个 `gold_text`，不在别处复制第二份序列化
（AC-4 修订 1）。

结构上不可见 gold：`build_prompt` 只接受 (图像路径, surface, g4 标志, 词表段名)
四个参数，没有任何 gold 通路；gold 序列化是另一条函数，两者不共享状态。

词表段 `{vocab}` 按数据集替换（Unity = `unity-v2`）；G4 行在词表段之后追加一段
关系方向释义（`G4_SEGMENT`）。三段的 SHA-256 各自导出，供冻结收据与云端
`FROZEN_SET_MISMATCH` 核对：`template_sha256()` 只覆盖不含词表段的模板骨架
（表 L (3) 的比较对象），`vocab_sha256()` 覆盖词表段本身。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

# --- 表 B 逐字文本 -------------------------------------------------------

HEAD_SEGMENT = (
    "You are given one aerial image taken by a drone camera. "
    "Locate the object described by the instruction.\n"
    "Instruction: {surface}"
)

VOCAB_PLACEHOLDER = "{vocab}"

VOCAB_SEGMENTS: dict[str, str] = {
    "unity-v2": (
        "Vehicle categories form a closed set of nine mutually exclusive labels: ambulance, bus, "
        "car, container truck, pickup truck, police car, suv, taxi, truck. Always use the most "
        'specific label: "car" means an ordinary passenger sedan or hatchback and never includes a '
        'taxi, police car, suv, pickup truck or ambulance; "truck" means a cargo truck that is '
        'neither a pickup truck nor a container truck; "container truck" is a truck carrying a '
        'shipping container; "suv" and "pickup truck" are never "car". When a color is given it is '
        "one of: blue, gray, green, purple, red, yellow."
    )
}

G4_SEGMENT = (
    "\"to the viewer's left of X\" means the described object appears further to the left in the "
    "image (smaller x) than the object X; \"to the viewer's right of X\" means further to the "
    "right (larger x)."
)

COORD_SEGMENT = (
    "Coordinates: bbox_2d = [x1, y1, x2, y2] are integers from 0 to 1000 relative to the image "
    "width and height, origin at the top-left corner, x increasing to the right and y increasing "
    "downward, with x1 < x2 and y1 < y2."
)

REPLY_SEGMENT = (
    "Reply with exactly one JSON object and nothing else:\n"
    '- exactly one object matches: {"status": "unique", "bbox_2d": [x1, y1, x2, y2]}\n'
    '- two or more objects match: {"status": "ambiguous", "candidates": [{"bbox_2d": [x1, y1, x2, '
    'y2]}, ...]} listing every matching object\n'
    '- no object matches: {"status": "none"}'
)

#: 模板骨架：词表段留占位符，G4 追加段在词表段之后（见 `build_prompt` 注释）。
PROMPT_TEMPLATE = "\n".join([HEAD_SEGMENT, VOCAB_PLACEHOLDER, COORD_SEGMENT, REPLY_SEGMENT])

# 表 B 的处理器设置：不缩放原图（Unity 640×480 → 断言 grid [1, 30, 40]）。
PROCESSOR_SIZE: dict[str, int] = {"shortest_edge": 65536, "longest_edge": 16777216}
UNITY_IMAGE_GRID_THW: tuple[int, int, int] = (1, 30, 40)

# 表 B 坐标域。
COORD_MAX = 1000


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def template_sha256() -> str:
    """不含词表段的模板骨架 SHA（表 L (3) 的逐字节比较对象）。"""
    return _sha256_text(PROMPT_TEMPLATE)


def vocab_sha256(vocab_name: str = "unity-v2") -> str:
    return _sha256_text(vocab_segment(vocab_name))


def g4_segment_sha256() -> str:
    return _sha256_text(G4_SEGMENT)


def vocab_segment(vocab_name: str) -> str:
    try:
        return VOCAB_SEGMENTS[vocab_name]
    except KeyError as exc:  # pragma: no cover - 词表段闭集由调用方保证
        raise KeyError(f"未知词表段：{vocab_name!r}（闭集 {sorted(VOCAB_SEGMENTS)}）") from exc


def build_prompt(
    image_path: str, surface: str, g4: bool = False, vocab_name: str = "unity-v2"
) -> dict[str, Any]:
    """表 B：装配一条 prompt v2。

    **结构上不可见 gold**：本函数只有这四个参数，没有 gold/框/状态的入口。
    返回消息结构（图像路径 + 文本）与文本本身的 SHA-256，供预测行记录
    `prompt_sha256`。

    G4 追加段的位置由 **AC-4 修订 2（接受角色 2026-09-14 裁定）** 固定：关系释义段接在
    词表段之后、Coordinates 段之前；非 G4 行不插入。表 B 原段文字、本函数的四参数边界与
    AC-4 修订 1 的 gold 隔离均不变。模板骨架、词表段与 G4 段的 SHA 各自导出，供冻结收据
    与云端 `FROZEN_SET_MISMATCH` 核对。
    """
    segments = [HEAD_SEGMENT.replace("{surface}", surface), vocab_segment(vocab_name)]
    if g4:
        segments.append(G4_SEGMENT)
    segments.extend([COORD_SEGMENT, REPLY_SEGMENT])
    text = "\n".join(segments)
    return {
        "image_path": image_path,
        "text": text,
        "prompt_sha256": _sha256_text(text),
        "vocab": vocab_name,
        "g4": bool(g4),
        "messages": [
            {
                "role": "user",
                "content": [{"type": "image", "image": image_path}, {"type": "text", "text": text}],
            }
        ],
    }


def fixed_prompt_chars(g4: bool = False, vocab_name: str = "unity-v2") -> int:
    """固定文本字符数（不含 surface）；§8 表 6a 的 1,226 即此值（非 G4、Unity 词表）。"""
    return len(build_prompt("", "", g4, vocab_name)["text"])


# --- 坐标整数化与 gold 序列化（表 B）-------------------------------------


def quantise(value: float) -> int:
    """`⌊v·1000 + 0.5⌋`，裁到 [0, 1000]。"""
    return max(0, min(COORD_MAX, int(value * COORD_MAX + 0.5)))


def bbox_2d_1000(box_norm: Sequence[float]) -> list[int]:
    """归一化 top-left xywh → 表 B 的整数 `[x1, y1, x2, y2]`。

    退化修正逐轴各做一次：`x2 ≤ x1` 时 `x2 = x1 + 1`，`x1` 已在 1000 时反向
    `x1 = x2 - 1`；y 轴同。
    """
    x, y, w, h = box_norm[0], box_norm[1], box_norm[2], box_norm[3]
    x1, y1 = quantise(x), quantise(y)
    x2, y2 = quantise(x + w), quantise(y + h)
    if x2 <= x1:
        if x1 < COORD_MAX:
            x2 = x1 + 1
        else:
            x1 = x2 - 1
    if y2 <= y1:
        if y1 < COORD_MAX:
            y2 = y1 + 1
        else:
            y1 = y2 - 1
    return [x1, y1, x2, y2]


def sorted_bboxes(boxes: Sequence[Sequence[float]]) -> list[list[int]]:
    """候选按 `(x1, y1, x2, y2)` 升序（表 B）。"""
    return sorted((bbox_2d_1000(box) for box in boxes), key=tuple)


def gold_text_from_state(state: str | None, boxes: Sequence[Sequence[float]]) -> str | None:
    """三种骨架逐字（`json.dumps` 缺省分隔符、键序、纯 ASCII）。

    `state` 为 None（灰区诊断行、LEGACY_ONLY）时没有 gold，返回 None。
    """
    if state is None:
        return None
    if state == "none":
        return json.dumps({"status": "none"}, ensure_ascii=True)
    ordered = sorted_bboxes(boxes)
    if state == "unique":
        if len(ordered) != 1:
            raise ValueError(f"unique gold 必须恰好一个框，收到 {len(ordered)}")
        return json.dumps({"status": "unique", "bbox_2d": ordered[0]}, ensure_ascii=True)
    if state == "ambiguous":
        if not 2 <= len(ordered) <= 4:
            raise ValueError(f"ambiguous gold 候选数须在 2…4，收到 {len(ordered)}")
        payload = {"status": "ambiguous", "candidates": [{"bbox_2d": box} for box in ordered]}
        return json.dumps(payload, ensure_ascii=True)
    raise ValueError(f"gold 状态不在三态闭集内：{state!r}")


def gold_text(sample: Mapping[str, Any]) -> str | None:
    """表 B 的 gold 序列化（训练标签、冒烟核对与本地评分共用这一个函数）。

    接受 sample 行（`state` / `target_boxes_norm_xywh`）或 eval-row
    （`gold_state` / `gold_boxes_norm_xywh`）。
    """
    if "gold_state" in sample:
        return gold_text_from_state(sample["gold_state"], sample.get("gold_boxes_norm_xywh") or [])
    return gold_text_from_state(sample.get("state"), sample.get("target_boxes_norm_xywh") or [])


def gold_function_source_sha256() -> str:
    """gold 函数源码 SHA（预检收据绑定项；本模块整文件字节）。"""
    from pathlib import Path

    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
