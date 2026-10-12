#!/usr/bin/env python3
"""Tier-1 可逆语言工具链：ontology/v1、规范化 AST、renderer、parser、执行器。

提案 §2.11（BC-DIST-2 机械半边）与 §2.9（最小程序规则）。本模块纯离线、
零模型调用；renderer 词表即 Tier-1 闭包，折叠表 = 恒等 + 冻结别名表
（`contract.CANONICAL_ALIASES`，当前为空）。

**唯一性的 fail-closed 语义**（§2.3/§2.4）：执行域 = `blocking(f)`，其中
动态目标代理的视觉类别一律 `UNKNOWN`、phantom 的 AABB 不可恢复、
`UNVERIFIED` 对象没有可用颜色词。本模块把「属性未知」实现为**通配冲突**
——未知不能用来排除，因此这些对象**阻断**唯一性却**永不可指称**。
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any, Iterable, Sequence

from tools.dist_data import contract
from tools.dist_data.artifacts import DistDataError, canonical_json_bytes


class OntologyViolation(DistDataError):
    """程序不满足 ontology/v1 的闭集约束。"""


class ParseError(DistDataError):
    """表达无法被 Tier-1 parser 解析。"""


# --- Tier-1 表层语法（renderer 与 parser 共用同一张冻结表） ---------------
RELATION_SURFACE: dict[str, str] = {
    "nearest_to": "nearest to",
    "viewer_left_of": "to the viewer's left of",
    "viewer_right_of": "to the viewer's right of",
    "on_route_side": "on the same side of the route as",
}
_SURFACE_TO_RELATION: dict[str, str] = {v: k for k, v in RELATION_SURFACE.items()}


def _alternation(words: Iterable[str]) -> str:
    """最长优先的正则选择支——保证 `police car` 不被 `car` 抢走。"""
    ordered = sorted(set(words), key=lambda word: (-len(word), word))
    return "|".join(re.escape(word) for word in ordered)


_CLASS_ALT = _alternation(contract.CLASS_WORDS)
_COLOR_ALT = _alternation(contract.COLOR_WORDS)
_RELATION_ALT = _alternation(RELATION_SURFACE.values())
_EXPRESSION_RE = re.compile(
    rf"^the (?:(?P<tcolor>{_COLOR_ALT}) )?(?P<tclass>{_CLASS_ALT})"
    rf"(?: (?P<relation>{_RELATION_ALT}) the (?:(?P<rcolor>{_COLOR_ALT}) )?(?P<rclass>{_CLASS_ALT}))?$"
)


# --- ontology/v1 ----------------------------------------------------------
def _validate_noun(node: Any, *, where: str, verified_colors: set[str] | None) -> None:
    if not isinstance(node, dict):
        raise OntologyViolation(f"{where} 必须是对象")
    unknown = set(node) - {"class", "color"}
    if unknown:
        raise OntologyViolation(f"{where} 含闭集外字段 {sorted(unknown)}")
    class_word = node.get("class")
    if class_word not in contract.CLASS_WORDS:
        raise OntologyViolation(f"{where}.class={class_word!r} 不在 9 类闭集内")
    color = node.get("color")
    if color is None:
        return
    if color not in contract.COLOR_WORDS:
        raise OntologyViolation(f"{where}.color={color!r} 不在冻结颜色词表内")
    if verified_colors is not None and color not in verified_colors:
        raise OntologyViolation(f"{where}.color={color!r} 不在已验证字段闭包内")


def validate_program(program: Any, *, verified_colors: Iterable[str] | None = None) -> None:
    """schema 层校验：字段闭集、未验证字段与禁用（动态）关系一律拒绝。"""
    allowed_colors = None if verified_colors is None else set(verified_colors)
    if not isinstance(program, dict):
        raise OntologyViolation("program 必须是对象")
    unknown = set(program) - {"target", "relation"}
    if unknown:
        raise OntologyViolation(f"program 含闭集外字段 {sorted(unknown)}")
    if "target" not in program:
        raise OntologyViolation("program 缺 target")
    _validate_noun(program["target"], where="target", verified_colors=allowed_colors)
    relation = program.get("relation")
    if relation is None:
        return
    if not isinstance(relation, dict):
        raise OntologyViolation("relation 必须是对象")
    unknown = set(relation) - {"type", "ref"}
    if unknown:
        raise OntologyViolation(f"relation 含闭集外字段 {sorted(unknown)}")
    if relation.get("type") not in contract.RELATION_TYPES:
        raise OntologyViolation(
            f"relation.type={relation.get('type')!r} 不在静态关系闭集内"
            "（动态关系全批禁止，章程 U6/BC）"
        )
    _validate_noun(relation.get("ref"), where="relation.ref", verified_colors=allowed_colors)


def _canonical_noun(node: dict[str, Any]) -> dict[str, Any]:
    class_word = contract.CANONICAL_ALIASES.get(
        str(node["class"]).strip().lower(), str(node["class"]).strip().lower()
    )
    out: dict[str, Any] = {"class": class_word}
    color = node.get("color")
    if color is not None:
        lowered = str(color).strip().lower()
        out["color"] = contract.CANONICAL_ALIASES.get(lowered, lowered)
    return out


def canonical_ast(program: dict[str, Any]) -> dict[str, Any]:
    """规范化 AST：键排序（由序列化保证）、枚举小写、可选字段缺省化、别名折叠。

    幂等：`canon(canon(x)) == canon(x)`（性质测试覆盖）。
    """
    out: dict[str, Any] = {"target": _canonical_noun(program["target"])}
    relation = program.get("relation")
    if relation is not None:
        relation_type = str(relation["type"]).strip().lower()
        out["relation"] = {
            "type": contract.CANONICAL_ALIASES.get(relation_type, relation_type),
            "ref": _canonical_noun(relation["ref"]),
        }
    return out


def canonical_bytes(program: dict[str, Any]) -> bytes:
    """规范化 AST 的字节表示（verifier 的 `semantic_program` 载体）。"""
    return canonical_json_bytes(canonical_ast(program))


# --- renderer / parser（往返可逆） ---------------------------------------
def _render_noun(node: dict[str, Any]) -> str:
    color = node.get("color")
    return f"the {color} {node['class']}" if color else f"the {node['class']}"


def render(program: dict[str, Any]) -> str:
    """把程序渲染为 Tier-1 表达（closed vocabulary，确定性）。"""
    validate_program(program)
    text = _render_noun(program["target"])
    relation = program.get("relation")
    if relation is not None:
        text = f"{text} {RELATION_SURFACE[relation['type']]} {_render_noun(relation['ref'])}"
    return text


def parse(expression: str) -> dict[str, Any]:
    """Tier-1 parser：只接受 renderer 词表内的表达，其余 `ParseError`。"""
    if not isinstance(expression, str):
        raise ParseError("表达必须是字符串")
    match = _EXPRESSION_RE.match(expression.strip())
    if match is None:
        raise ParseError(f"不可解析的 Tier-1 表达：{expression!r}")
    program: dict[str, Any] = {"target": {"class": match.group("tclass")}}
    if match.group("tcolor"):
        program["target"]["color"] = match.group("tcolor")
    if match.group("relation"):
        ref: dict[str, Any] = {"class": match.group("rclass")}
        if match.group("rcolor"):
            ref["color"] = match.group("rcolor")
        program["relation"] = {
            "type": _SURFACE_TO_RELATION[match.group("relation")],
            "ref": ref,
        }
    return program


def enumerate_programs(
    *,
    classes: Sequence[str] | None = None,
    colors: Sequence[str] | None = None,
    relations: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Tier-1 程序全枚举（往返性质测试用）。"""
    classes = list(classes or contract.CLASS_WORDS)
    color_options: list[str | None] = [None, *(colors or contract.COLOR_WORDS)]
    relations = list(relations or contract.RELATION_TYPES)
    programs: list[dict[str, Any]] = []
    for class_word in classes:
        for color in color_options:
            target: dict[str, Any] = {"class": class_word}
            if color is not None:
                target["color"] = color
            programs.append({"target": dict(target)})
            for relation_type in relations:
                for ref_class in classes:
                    for ref_color in color_options:
                        ref: dict[str, Any] = {"class": ref_class}
                        if ref_color is not None:
                            ref["color"] = ref_color
                        programs.append(
                            {
                                "target": dict(target),
                                "relation": {"type": relation_type, "ref": ref},
                            }
                        )
    return programs


# --- 执行器 ---------------------------------------------------------------
@dataclass(frozen=True)
class SceneObject:
    """执行域中的一个可见体（目录对象 / phantom / 动态目标代理）。

    `class_word is None` = 类别 UNKNOWN（动态目标），`color_word is None` =
    颜色未验证或不可恢复；两者都按**通配冲突**处理：未知不能用来排除。
    `referable` 只对 §2.4 状态 `OK` 的目录对象为真。
    """

    object_id: str
    class_word: str | None
    color_word: str | None
    referable: bool
    center_px: tuple[float, float] | None = None
    world_xz: tuple[float, float] | None = None
    route_side: int | None = None


@dataclass(frozen=True)
class ExecutionResult:
    selected_object_ids: tuple[str, ...]
    unique: bool
    relation_available: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "selected_object_ids": list(self.selected_object_ids),
            "unique": self.unique,
            "relation_available": self.relation_available,
        }


def _noun_conflicts(obj: SceneObject, node: dict[str, Any]) -> bool:
    """对象是否可能满足名词短语（未知属性 = 通配，fail-closed）。"""
    if obj.class_word is not None and obj.class_word != node["class"]:
        return False
    color = node.get("color")
    if color is not None and obj.color_word is not None and obj.color_word != color:
        return False
    return True


def _noun_satisfies(obj: SceneObject, node: dict[str, Any]) -> bool:
    """对象是否**确证**满足名词短语（严格；未知字段不算满足）。

    BC-DATA-17：带颜色的 ref spec 只有该 referent 自身 `color_status=VERIFIED`
    且词值相等时才可匹配/枚举——`SceneObject.color_word` 只在已验证时才非
    None，故此处的相等比较即该条款。与 `_noun_conflicts`（通配，用于唯一性
    分母）是两个不同判据，不可互换。
    """
    if obj.class_word != node["class"]:
        return False
    color = node.get("color")
    return color is None or obj.color_word == color


def _resolve_ref(domain: Sequence[SceneObject], node: dict[str, Any]) -> SceneObject | None:
    """ref 短语必须在执行域内唯一解析**到一个可指称对象**，否则关系不可用。

    BC-DATA-8.3（接受轮 4 冻结）：动态目标代理与 phantom **永不可指称**。
    唯一性的分母仍含通配对象——未知属性不能用来排除，所以它们照样阻断
    唯一性；但它们自己绝不能被选作 ref，否则表达会去指一个身份未知的车，
    正是 A3 审计零容忍的假唯一。
    """
    hits = [obj for obj in domain if _noun_conflicts(obj, node)]
    if len(hits) != 1:
        return None
    referent = hits[0]
    if not referent.referable:
        return None
    # BC-DATA-17：`UNVERIFIED` 仍按未知通配阻断唯一性（分母不变），但绝不能
    # 被选成任意颜色的 ref——否则未验证颜色会写进表达文本。
    return referent if _noun_satisfies(referent, node) else None


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def execute(program: dict[str, Any], domain: Sequence[SceneObject]) -> ExecutionResult:
    """在 `blocking(f)` 执行域上执行程序，返回命中集合与唯一性。

    唯一 = 恰一个命中（是否为 target 由调用方比对）。
    """
    validate_program(program)
    candidates = [obj for obj in domain if _noun_conflicts(obj, program["target"])]
    relation = program.get("relation")
    if relation is None:
        ids = tuple(sorted(obj.object_id for obj in candidates))
        return ExecutionResult(ids, len(ids) == 1, True)

    reference = _resolve_ref(domain, relation["ref"])
    if reference is None:
        return ExecutionResult((), False, False)
    candidates = [obj for obj in candidates if obj.object_id != reference.object_id]
    relation_type = relation["type"]

    if relation_type == "nearest_to":
        # 未知场景位置不能用来排除：任一候选缺 `world_xz` 即无法确立唯一性
        # （静默丢弃会把 phantom 这类未知位置体判成不存在，方向 fail-open）。
        if reference.world_xz is None or not candidates:
            return ExecutionResult((), False, False)
        if any(obj.world_xz is None for obj in candidates):
            return ExecutionResult((), False, False)
        ordered = sorted(
            candidates, key=lambda obj: (_distance(obj.world_xz, reference.world_xz), obj.object_id)
        )
        d1 = _distance(ordered[0].world_xz, reference.world_xz)
        if len(ordered) > 1:
            d2 = _distance(ordered[1].world_xz, reference.world_xz)
            if d1 > contract.NEAREST_TO_DOMINANCE_RATIO * d2:
                return ExecutionResult((), False, False)
        return ExecutionResult((ordered[0].object_id,), True, True)

    if relation_type in ("viewer_left_of", "viewer_right_of"):
        if reference.center_px is None:
            return ExecutionResult((), False, False)
        if any(obj.center_px is None for obj in candidates):
            return ExecutionResult((), False, False)  # 未知像素位置同样阻断唯一性
        selected = []
        for obj in candidates:
            delta = obj.center_px[0] - reference.center_px[0]
            if abs(delta) < contract.VIEWER_SIDE_MIN_SEPARATION_PX:
                continue
            if relation_type == "viewer_left_of" and delta < 0:
                selected.append(obj.object_id)
            elif relation_type == "viewer_right_of" and delta > 0:
                selected.append(obj.object_id)
        ids = tuple(sorted(selected))
        return ExecutionResult(ids, len(ids) == 1, True)

    if relation_type == "on_route_side":
        if reference.route_side is None:
            return ExecutionResult((), False, False)
        if any(obj.route_side is None for obj in candidates):
            return ExecutionResult((), False, False)  # 未知道路侧同样阻断唯一性
        ids = tuple(
            sorted(
                obj.object_id
                for obj in candidates
                if obj.route_side == reference.route_side
            )
        )
        return ExecutionResult(ids, len(ids) == 1, True)

    raise OntologyViolation(f"未知关系类型 {relation_type!r}")


def hits_expected_target(result: ExecutionResult, expected_target_id: str) -> bool:
    return result.unique and result.selected_object_ids == (expected_target_id,)
