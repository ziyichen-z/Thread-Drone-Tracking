#!/usr/bin/env python3
"""S3 逐帧 eligible catalog（提案 §2.4）与 S5 字段验证目录（§2.6）。

包含三块可独立测试的纯逻辑：

1. **逐帧 catalog**：投影 + 遮挡 + 状态闭集 + `TARGET_UNBOUNDED` 判定 +
   站位簇分箱 + 逐对象 exposure 字段；
2. **S5 字段目录**：class 机械归类、color 的 K=5 帧 HSV 统计与
   (prefab, 皮肤) 组一致性约束、dynamic_state、static_relations 可用性；
3. **`prospective_mother_eligible`** 与 §2.9 最小程序规则。

BC-DATA-1：谓词求值只读冻结的 S1–S6 工件，**绝不读 S8**；S6 只可把 S5
字段降级，不能新增字段或样本。
"""

from __future__ import annotations

import bisect
import colorsys
from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol, Sequence

from tools.dist_data import contract, project_boxes, tier1_lang
from tools.dist_data.artifacts import DistDataError

STAGE_CATALOG = 3
STAGE_FIELDS = 5

TARGET_BLOCKER_ID = "dynamic-target"
# 动态目标只有图像面框，没有可用的三维位置（BC-DATA-3 禁止由 target_world_*
# 构造 AABB）。画家序里把它放在**最近**位置是 fail-closed 方向：它会遮挡
# 与之重叠的目录对象，压低 eligible 计数而非抬高。
TARGET_BLOCKER_DEPTH = float("-inf")


class CatalogError(DistDataError):
    """S3/S5 目录构建失败（一律 fail-closed）。"""


# --- 逐帧目标真值 → 阻断体 / `TARGET_UNBOUNDED`（§2.3，AR2-3 逐 schema） ---
def camera_forward_depth(camera: project_boxes.Camera, bounds: dict[str, Any]) -> float:
    """BC-DATA-15：`z_depth = dot(center_world − camera_world, camera_forward_world)`。

    画家序、S5 每实例最近 K=5 帧、A1/A2 距离三分位三处的「距离」统一取此值
    （米），**不是欧氏距离**——三者服务投影尺度/遮挡，z 才是针孔投影分母。
    """
    centre = (
        (bounds["min_x_m"] + bounds["max_x_m"]) / 2.0,
        (bounds["min_y_m"] + bounds["max_y_m"]) / 2.0,
        (bounds["min_z_m"] + bounds["max_z_m"]) / 2.0,
    )
    return camera.to_camera_space(centre)[2]


def target_blocker_from_truth(
    truth_row: dict[str, Any] | None, schema_family: str | None, camera: project_boxes.Camera
) -> tuple[project_boxes.Rect | None, bool]:
    """返回 `(图像面阻断框, target_unbounded)`。

    边界 fail-closed：帧无可 join 真值行，或真值行示目标在视锥内/可见却无
    可用框 → `TARGET_UNBOUNDED`。二维框**不充当**三维位置。
    """
    if schema_family is None:
        raise CatalogError("无逐帧真值 schema 的族不得走本分支（应走扫掠代理）")
    if schema_family not in contract.DYNAMIC_TARGET_SCHEMAS:
        raise CatalogError(
            f"真值 schema 族 {schema_family!r} 不在闭集 "
            f"{contract.DYNAMIC_TARGET_SCHEMAS}"
        )
    if truth_row is None and schema_family != contract.TARGET_SCHEMA_PARKED:
        return None, True

    if schema_family == "m3":
        available = bool(truth_row.get("truth_box_available"))
        box_fields = (
            truth_row.get("truth_box_x"),
            truth_row.get("truth_box_y"),
            truth_row.get("truth_box_width"),
            truth_row.get("truth_box_height"),
        )
        if available and all(value is not None for value in box_fields):
            return (
                project_boxes.denormalize_xywh(
                    [float(value) for value in box_fields], camera
                ),
                False,
            )
        # BC-DATA-16：缺 join、或既无可见性证据又无可用框时是**未知**，不是
        # 不可见 —— 必须置 TARGET_UNBOUNDED，不得静默省略 blocker。
        evidence_keys = ("intersects_frustum", "geometrically_visible", "has_unoccluded_sample")
        # 「有这个键」不等于「有证据」：值为 null 同样是未知。三个键都必须按
        # bool 取值判定，且 `has_unoccluded_sample` 也算在场证据之一。
        evidence = {
            key: truth_row[key]
            for key in evidence_keys
            if isinstance(truth_row.get(key), bool)
        }
        if not evidence:
            return None, True
        return (None, True) if any(evidence.values()) else (None, False)

    if schema_family == contract.TARGET_SCHEMA_PARKED:
        # P1-VLM-DATA-002 §2.2 第 3 条：停放目标零速、朝向恒为世界 +z，位姿由
        # 归档场景字节的 `route_world_m[0]` 精确派生，**没有**逐帧真值文件与
        # 过渡帧。位姿已知，所以「投不出框」是「不在画面内」，不是「未知」——
        # `target_unbounded` 恒 false（提案 §2.1(f) 末条）。
        position = (truth_row or {}).get("parked_position_world_m")
        if position is None:
            raise CatalogError(
                "target_parked 帧缺 `parked_position_world_m`；停放位姿是该 schema"
                "的全部输入，不得以缺省或扫掠代理补齐"
            )
        amodal = project_boxes.project_aabb(
            camera, contract.parked_target_bounds(position)
        )
        if amodal is None:
            return None, False
        return project_boxes.intersect(amodal, camera.viewport()), False

    if schema_family == "scouting":
        box = truth_row.get("target_bbox_xywh_norm")
        status = truth_row.get("target_box_status")  # v2 才有
        if box:
            return project_boxes.denormalize_xywh(box, camera), False
        visible = bool(truth_row.get("target_visible"))
        if visible:
            return None, True
        if status is not None and status not in ("NOT_IN_FRAME",):
            return None, True
        return None, False

    raise CatalogError(f"未知真值 schema 族 {schema_family!r}")  # pragma: no cover


def parked_target_truth_row(route: Sequence[dict[str, float]]) -> dict[str, Any]:
    """由归档场景字节的两点停放段构造 `target_parked` 的「真值行」。

    只取 `route[0]`（= `P_k`）：`route[1] = P_k + (0,0,1)` 只用来把朝向钉成
    世界 +z，本身不是位姿。段长 1.0 m ≥ 0.5 m，航点索引永不翻转，所以停放
    位姿对每一帧精确成立。
    """
    if not route:
        raise CatalogError("停放段为空，无法构造 target_parked 真值行")
    point = route[0]
    return {
        "parked_position_world_m": [
            float(point["x"]),
            float(point.get("y", 0.0)),
            float(point["z"]),
        ]
    }


def target_unbounded_from_sweep(
    camera: project_boxes.Camera,
    route: Sequence[dict[str, float]],
    envelope_half_extents: tuple[float, float, float],
) -> tuple[bool, float]:
    """无逐帧目标真值族：扫掠代理区投影与视口交面积 ≥ (12 px)² 即整帧退出。"""
    rects = project_boxes.route_sweep_rects(camera, route, envelope_half_extents)
    total = project_boxes.union_area(rects)
    return total >= contract.TARGET_SWEEP_MIN_AREA_PX2, total


def vehicle_envelope_half_extents(
    instances: Iterable[dict[str, Any]]
) -> tuple[float, float, float]:
    """全体目录车辆 AABB 尺寸的最大包络半长（§2.3 扫掠代理构造用）。"""
    half = [0.0, 0.0, 0.0]
    for instance in instances:
        if contract.class_for_scene_object(instance["scene_object_name"]) is None:
            continue
        half[0] = max(half[0], (instance["max_x_m"] - instance["min_x_m"]) / 2.0)
        half[1] = max(half[1], (instance["max_y_m"] - instance["min_y_m"]) / 2.0)
        half[2] = max(half[2], (instance["max_z_m"] - instance["min_z_m"]) / 2.0)
    return (half[0], half[1], half[2])


# --- 逐帧 catalog ---------------------------------------------------------
@dataclass(frozen=True)
class FrameInput:
    """S3 的单帧输入（全部来自冻结的 S1/S2 工件与源字节）。"""

    frame_id: str
    sidecar: dict[str, Any]
    family: str
    layout_class: str
    usage_class: str
    layout_binding_valid: bool
    sidecar_complete: bool
    truth_row: dict[str, Any] | None = None
    truth_schema: str | None = None
    # BC-DATA-9：该族的目标源身份是否可证绑定到冻结构造合同。
    target_source_bound: bool = True


def build_frame_entry(
    frame: FrameInput,
    layout_bodies: Sequence[dict[str, Any]],
    route: Sequence[dict[str, float]],
    envelope_half_extents: tuple[float, float, float],
) -> dict[str, Any]:
    """单帧 catalog 记录：逐对象状态 + eligible/blocking 集 + exposure + 站位簇。"""
    camera = project_boxes.Camera.from_sidecar(frame.sidecar)
    if frame.truth_schema is not None:
        target_box, unbounded = target_blocker_from_truth(
            frame.truth_row, frame.truth_schema, camera
        )
        sweep_area = None
    else:
        target_box = None
        unbounded, sweep_area = target_unbounded_from_sweep(
            camera, route, envelope_half_extents
        )

    extra_blockers: list[tuple[str, project_boxes.Rect, float]] = []
    if target_box is not None:
        extra_blockers.append((TARGET_BLOCKER_ID, target_box, TARGET_BLOCKER_DEPTH))

    projected = project_boxes.project_instances(
        camera, layout_bodies, extra_blockers=extra_blockers
    )
    # BC-DATA-16：遮挡几何域与语言对象域分离。`occluders(f)` 保留全部静态
    # AABB + phantom + 动态 blocker（已由 project_instances 的画家序消费）；
    # `blocking(f)` 只含 visible 的**九类车辆**目录对象 + phantom + 动态目标；
    # `referable(f)` 只含状态 OK 的九类车辆目录对象。building/nature/prop
    # 永不进入 blocking/referable/exposure，却仍能遮挡车辆。
    objects = []
    referable: list[str] = []
    blocking: list[str] = []
    for item in projected:
        in_language_domain = item.is_phantom or (
            contract.class_for_scene_object(item.object_id) is not None
        )
        if not in_language_domain:
            objects.append({**item.as_dict(), "exposure": "occluder_only"})
            continue
        is_referable = item.referable
        exposure = (
            "referent" if is_referable else ("distractor" if item.blocks else "absent")
        )
        objects.append({**item.as_dict(), "exposure": exposure})
        if is_referable:
            referable.append(item.object_id)
        if item.blocks:
            blocking.append(item.object_id)
    if target_box is not None and project_boxes.area(
        project_boxes.intersect(target_box, camera.viewport())
    ) > 0.0:
        blocking.append(TARGET_BLOCKER_ID)

    station = project_boxes.station_bin(camera)
    return {
        "frame_id": frame.frame_id,
        "family": frame.family,
        "layout_class": frame.layout_class,
        "usage_class": frame.usage_class,
        "layout_binding_valid": frame.layout_binding_valid,
        "sidecar_complete": frame.sidecar_complete,
        "target_unbounded": bool(unbounded),
        "target_sweep_area_px2": sweep_area,
        "target_blocker_px": list(target_box) if target_box else None,
        "target_source_bound": bool(frame.target_source_bound),
        "target_fields": contract.dynamic_target_fields(bool(frame.target_source_bound)),
        "station_bin": station,
        "objects": objects,
        "referable": sorted(referable),
        "blocking": sorted(blocking),
        "co_visible_count": len(referable),
        "status_histogram": _status_histogram(objects),
    }


def _status_histogram(objects: Sequence[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in contract.OBJECT_STATUSES}
    for item in objects:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return counts


def pre_split_floor_eligible(entry: dict[str, Any]) -> bool:
    """BC-DATA-2 的 `pre_split_floor_eligible(f)`：§5.1 floor 资格去掉 split 条件。

    S4 的一切覆盖统计只从本谓词派生；`floor_eligible(f, split)` 只在 split
    落定后由 `make_splits` 生成。
    """
    return (
        entry["usage_class"] in contract.FLOOR_USAGE_CLASSES
        and bool(entry["layout_binding_valid"])
        and bool(entry["sidecar_complete"])
        and not entry["target_unbounded"]
    )


# --- S5 字段验证目录 ------------------------------------------------------
class PixelSource(Protocol):
    """按帧提供 RGB 像素的适配器（正式运行用图像库，单测直接注入）。"""

    def crop_rgb(
        self, frame_id: str, box_px: project_boxes.Rect
    ) -> Sequence[tuple[int, int, int]]:
        ...


def _inset(box: project_boxes.Rect, fraction: float) -> project_boxes.Rect:
    width = box[2] - box[0]
    height = box[3] - box[1]
    return (
        box[0] + width * fraction,
        box[1] + height * fraction,
        box[2] - width * fraction,
        box[3] - height * fraction,
    )


def classify_pixel(rgb: tuple[int, int, int]) -> str | None:
    """§2.6 冻结判定带：RGB → 颜色词（未分配色相区间返回 None）。"""
    red, green, blue = (channel / 255.0 for channel in rgb)
    hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
    bands = contract.COLOR_ACHROMATIC
    if value < bands["black_value_below"]:
        return "black"
    if saturation < bands["white_saturation_below"] and value > bands["white_value_above"]:
        return "white"
    if saturation < bands["gray_saturation_below"]:
        return "gray"
    band = contract.hue_band(hue * 360.0)
    if band is None:
        return None
    if band == "orange" and value < contract.COLOR_BROWN_FROM_ORANGE_VALUE_BELOW:
        return "brown"
    return band


def estimate_color(pixels: Sequence[tuple[int, int, int]]) -> dict[str, Any]:
    """主带占比 ≥ 0.5 才有主色；否则无主色（`UNVERIFIED` 的来源之一）。"""
    total = len(pixels)
    if total == 0:
        return {"color": None, "share": 0.0, "pixel_count": 0, "histogram": {}}
    histogram: dict[str, int] = {}
    for pixel in pixels:
        label = classify_pixel(pixel)
        if label is None:
            continue
        histogram[label] = histogram.get(label, 0) + 1
    if not histogram:
        return {"color": None, "share": 0.0, "pixel_count": total, "histogram": {}}
    top = max(histogram.values())
    leaders = sorted(label for label, count in histogram.items() if count == top)
    share = top / total
    # 主带必须唯一：并列时不存在「主带」，按 fail-closed 判无主色。
    resolved = (
        leaders[0]
        if len(leaders) == 1 and share >= contract.COLOR_MAIN_BAND_MIN_SHARE
        else None
    )
    return {
        "color": resolved,
        "share": share,
        "tied_bands": leaders if len(leaders) > 1 else [],
        "pixel_count": total,
        "histogram": dict(sorted(histogram.items())),
    }


@dataclass
class ObjectObservation:
    """S5 颜色统计的一条候选观测（状态 `OK` 的目录对象在某帧上的 visible 框）。"""

    frame_id: str
    object_id: str
    visible_px: project_boxes.Rect
    camera_depth_m: float


class BoundedObservationSelector:
    """逐对象只保留 `(camera_depth_m, frame_id)` 升序下最小的 K 条（复核轮 6 F21）。

    与「整表 append 后 `sorted(...)[:K]`」**逐条等价**：排序键在同一对象内
    唯一（一帧一对象至多一条观测），`insort` 又与 `sorted` 同为稳定插入，
    所以候选集与顺序都与修前一致。差别只在驻留：任何时刻保留量上界为
    `O(对象数 × K)`，与帧数解耦。
    """

    def __init__(self, limit: int) -> None:
        if limit <= 0:
            raise CatalogError(f"K 必须为正：{limit}")
        self._limit = limit
        self._by_object: dict[str, list[tuple[tuple[float, str], ObjectObservation]]] = {}

    def add(self, observation: ObjectObservation) -> None:
        kept = self._by_object.setdefault(observation.object_id, [])
        key = (observation.camera_depth_m, observation.frame_id)
        if len(kept) >= self._limit and key >= kept[-1][0]:
            return  # 已满且更远：直接丢弃，不进入驻留集
        bisect.insort(kept, (key, observation), key=lambda item: item[0])
        del kept[self._limit :]

    def candidates(self, object_id: str) -> list[ObjectObservation]:
        return [observation for _key, observation in self._by_object.get(object_id, [])]

    def residency(self) -> int:
        """当前保留的观测总数（诊断用；上界 = 对象数 × K）。"""
        return sum(len(kept) for kept in self._by_object.values())


def build_field_catalog(
    object_ids: Sequence[str],
    observations: Iterable[ObjectObservation],
    pixels: PixelSource,
    *,
    relocated: Iterable[str] = (),
) -> dict[str, Any]:
    """S5 逐实例 class/color/dynamic_state 目录（含组一致性约束）。

    `observations` 只被**迭代一次**且逐条经 `BoundedObservationSelector`
    收敛，因此调用方可以（也应该）传生成器：整条 S5 的观测驻留与帧数
    无关（BC-DATA-25 (5) 款首总则，复核轮 6 F21）。
    """
    relocated_set = set(relocated)
    selector = BoundedObservationSelector(contract.COLOR_SAMPLE_FRAME_COUNT)
    for observation in observations:
        selector.add(observation)

    per_object: dict[str, dict[str, Any]] = {}
    for object_id in sorted(object_ids):
        class_word = contract.class_for_scene_object(object_id)
        record: dict[str, Any] = {
            "object_id": object_id,
            "class": class_word,
            "class_verified": class_word is not None,
            "group_key": contract.color_group_key(object_id),
            "dynamic_state": "static",
            "relocated": object_id in relocated_set,
            "color": None,
            "color_status": "UNVERIFIED",
            "color_evidence": None,
        }
        candidates = selector.candidates(object_id)
        if candidates:
            sampled: list[tuple[int, int, int]] = []
            for candidate in candidates:
                sampled.extend(
                    pixels.crop_rgb(
                        candidate.frame_id,
                        _inset(candidate.visible_px, contract.COLOR_BOX_INSET_FRACTION),
                    )
                )
            estimate = estimate_color(sampled)
            record["color_evidence"] = {
                "frames": [candidate.frame_id for candidate in candidates],
                **estimate,
            }
            if estimate["color"] is not None:
                record["color"] = estimate["color"]
                record["color_status"] = "VERIFIED"
        per_object[object_id] = record

    # §2.6 一致性约束：同 (prefab, 皮肤代号) 组解析到不同颜色词 → 整组 UNVERIFIED。
    groups: dict[str, list[str]] = {}
    for object_id, record in per_object.items():
        groups.setdefault(record["group_key"], []).append(object_id)
    group_report: dict[str, Any] = {}
    for group_key in sorted(groups):
        members = sorted(groups[group_key])
        words = {
            per_object[member]["color"]
            for member in members
            if per_object[member]["color"] is not None
        }
        consistent = len(words) <= 1
        if not consistent:
            for member in members:
                per_object[member]["color"] = None
                per_object[member]["color_status"] = "UNVERIFIED"
                per_object[member]["color_downgrade_reason"] = "GROUP_INCONSISTENT"
        group_report[group_key] = {
            "members": members,
            "resolved_words": sorted(words),
            "consistent": consistent,
        }

    verified_colors = sorted(
        {
            record["color"]
            for record in per_object.values()
            if record["color_status"] == "VERIFIED" and record["color"]
        }
    )
    return {
        "stage": STAGE_FIELDS,
        "objects": {object_id: per_object[object_id] for object_id in sorted(per_object)},
        "groups": group_report,
        "verified_color_vocabulary": verified_colors,
        "dual_verified_object_ids": sorted(
            object_id
            for object_id, record in per_object.items()
            if record["class_verified"] and record["color_status"] == "VERIFIED"
        ),
    }


def apply_audit_downgrades(
    field_catalog: dict[str, Any], downgraded_groups: Iterable[str]
) -> dict[str, Any]:
    """BC-DATA-1：S6 只可把 S5 字段降级，不得新增字段或样本。"""
    catalog = {
        **field_catalog,
        "objects": {
            object_id: dict(record) for object_id, record in field_catalog["objects"].items()
        },
    }
    downgrades = set(downgraded_groups)
    for record in catalog["objects"].values():
        if record["group_key"] in downgrades:
            record["color"] = None
            record["color_status"] = "UNVERIFIED"
            record["color_downgrade_reason"] = "AUDIT_A1_GROUP_REJECTED"
    catalog["verified_color_vocabulary"] = sorted(
        {
            record["color"]
            for record in catalog["objects"].values()
            if record["color_status"] == "VERIFIED" and record["color"]
        }
    )
    catalog["dual_verified_object_ids"] = sorted(
        object_id
        for object_id, record in catalog["objects"].items()
        if record["class_verified"] and record["color_status"] == "VERIFIED"
    )
    catalog["audit_downgraded_groups"] = sorted(downgrades)
    return catalog


# --- 最小程序规则与 `prospective_mother_eligible`（§2.4 / §2.9） -----------
@dataclass
class FrameWorld:
    """一帧的执行域：`blocking(f)` 的 `SceneObject` 视图。"""

    frame_id: str
    domain: list[tier1_lang.SceneObject] = field(default_factory=list)

    def by_id(self, object_id: str) -> tier1_lang.SceneObject | None:
        for obj in self.domain:
            if obj.object_id == object_id:
                return obj
        return None


def frame_world(
    entry: dict[str, Any],
    field_catalog: dict[str, Any],
    *,
    world_xz: dict[str, tuple[float, float]] | None = None,
    route_side: dict[str, int] | None = None,
) -> FrameWorld:
    """由 catalog 记录与 S5 目录构造执行域（`blocking(f)`）。"""
    world_xz = world_xz or {}
    route_side = route_side or {}
    objects = []
    blocking = set(entry["blocking"])
    for item in entry["objects"]:
        if item["object_id"] not in blocking:
            continue
        record = field_catalog["objects"].get(item["object_id"])
        if item["is_phantom"]:
            # phantom：类别由归档条目的 prefab 名已知，颜色不可恢复（通配冲突）。
            class_word = contract.class_for_scene_object(
                item["object_id"].split("phantom:", 1)[-1].split("@", 1)[0]
            )
            color_word = None
        elif record is None:
            class_word = None
            color_word = None
        else:
            class_word = record["class"]
            color_word = record["color"] if record["color_status"] == "VERIFIED" else None
        visible = item["visible_px"]
        centre = (
            ((visible[0] + visible[2]) / 2.0, (visible[1] + visible[3]) / 2.0)
            if visible
            else None
        )
        objects.append(
            tier1_lang.SceneObject(
                object_id=item["object_id"],
                class_word=class_word,
                color_word=color_word,
                referable=bool(item["referable"]),
                center_px=centre,
                world_xz=world_xz.get(item["object_id"]),
                route_side=route_side.get(item["object_id"]),
            )
        )
    if TARGET_BLOCKER_ID in blocking:
        # BC-DATA-9：源身份可证绑定的族按 `car`/`red` 参与冲突判定，其余族
        # 逐字段 UNKNOWN 通配。无论哪种，目标 `referable=False`——它可以让
        # 城市车的 target/ref 名词不唯一，但自身绝不得被枚举为 ref。
        fields = contract.dynamic_target_fields(bool(entry.get("target_source_bound")))
        target_box = entry.get("target_blocker_px")
        centre = (
            ((target_box[0] + target_box[2]) / 2.0, (target_box[1] + target_box[3]) / 2.0)
            if target_box
            else None
        )
        objects.append(
            tier1_lang.SceneObject(
                object_id=TARGET_BLOCKER_ID,
                class_word=fields["class"],
                color_word=fields["color"],
                referable=contract.DYNAMIC_TARGET_REFERABLE,
                center_px=centre,
            )
        )
    objects.sort(key=lambda obj: obj.object_id)
    return FrameWorld(entry["frame_id"], objects)


def _unique_reference_specs(world: FrameWorld) -> list[dict[str, Any]]:
    """在执行域内**唯一解析到可指称对象**的名词短语，按冻结顺序枚举。

    BC-DATA-8.4：枚举序 = 类别词升序 → 无色在前 → 颜色词升序
    （`COLOR_WORDS_ASCENDING`，不是 §2.6 的判定带词表序）。
    BC-DATA-8.3：唯一性分母含通配对象，但通配对象自己永不可作 ref。
    """
    specs: list[dict[str, Any]] = []
    for class_word in sorted(contract.CLASS_WORDS):
        for color in (None, *contract.COLOR_WORDS_ASCENDING):
            spec: dict[str, Any] = {"class": class_word}
            if color is not None:
                spec["color"] = color
            if tier1_lang._resolve_ref(world.domain, spec) is not None:
                specs.append(spec)
    return specs


def minimal_program(
    world: FrameWorld, object_id: str, field_catalog: dict[str, Any]
) -> dict[str, Any] | None:
    """§2.9 最小程序规则（只返回程序；ref 解析结果见下一个函数）。"""
    return minimal_program_with_reference(world, object_id, field_catalog)[0]


def minimal_program_with_reference(
    world: FrameWorld, object_id: str, field_catalog: dict[str, Any]
) -> tuple[dict[str, Any] | None, str | None]:
    """§2.9 最小程序规则，返回 `(程序, resolved_reference_object_id)`。

    class-only 唯一 → 取之；否则 class+color（双验证）唯一 → 取之；否则
    class(+color)+**单一**静态关系唯一 → 取之；仍不唯一 → 该 (帧,对象)
    不入母集。关系与 ref 的枚举顺序是冻结的：关系按
    `contract.RELATION_TYPES`，ref 按 (类别词升序, 无色在前、颜色升序)。
    """
    record = field_catalog["objects"].get(object_id)
    if record is None or not record.get("class_verified"):
        return None
    target_specs: list[dict[str, Any]] = [{"class": record["class"]}]
    if record["color_status"] == "VERIFIED" and record["color"]:
        target_specs.append({"class": record["class"], "color": record["color"]})

    for spec in target_specs:
        program = {"target": dict(spec)}
        result = tier1_lang.execute(program, world.domain)
        if tier1_lang.hits_expected_target(result, object_id):
            return program, None

    references = _unique_reference_specs(world)
    for spec in target_specs:
        for relation_type in contract.RELATION_TYPES:
            for reference in references:
                program = {
                    "target": dict(spec),
                    "relation": {"type": relation_type, "ref": dict(reference)},
                }
                result = tier1_lang.execute(program, world.domain)
                if tier1_lang.hits_expected_target(result, object_id):
                    # BC-DATA-17：每个关系候选须冻结 resolved_reference_object_id，
                    # 否则 S8 无从执行留出物体在 ref 侧的封禁。
                    resolved = tier1_lang._resolve_ref(world.domain, reference)
                    return program, (resolved.object_id if resolved else None)
    return None, None


def prospective_mother_eligible(
    entry: dict[str, Any],
    object_id: str,
    world: FrameWorld,
    field_catalog: dict[str, Any],
    held_out_object_ids: Iterable[str] = (),
) -> dict[str, Any] | None:
    """§2.4 具名谓词；成立时返回 `(帧, 对象, 最小程序)` 候选记录，否则 None。

    谓词本身**不含**用途类/split 条件（那属于 §5.1 的 floor 资格）。
    """
    if entry["usage_class"] not in contract.MOTHER_USAGE_CLASSES:
        return None
    if not entry["layout_binding_valid"] or not entry["sidecar_complete"]:
        return None
    if entry["target_unbounded"]:
        return None
    if object_id not in entry["referable"]:
        return None
    program, reference = minimal_program_with_reference(world, object_id, field_catalog)
    if program is None:
        return None
    held_out = set(held_out_object_ids)
    return {
        "frame_id": entry["frame_id"],
        "object_id": object_id,
        "program": program,
        "resolved_reference_object_id": reference,
        "held_out_reference": reference in held_out if reference else False,
        "program_kind": "attribute" if "relation" not in program else "relational",
        "usage_class": entry["usage_class"],
        "family": entry["family"],
        "layout_class": entry["layout_class"],
        "station_key": entry["station_bin"]["key"],
        "floor_usage": entry["usage_class"] in contract.FLOOR_USAGE_CLASSES,
        "pre_split_floor_eligible": pre_split_floor_eligible(entry),
    }
