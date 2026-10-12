#!/usr/bin/env python3
"""S3 投影合同（提案 §2.4，AR1-5）：相机、AABB 投影、近裁剪、框口径、
遮挡近似与站位簇分箱。

全部数值常量来自 `contract.py`（S0 冻结）；本模块**没有**可调参数，也
不读取任何 S4+ 工件。
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable, Sequence

from tools.dist_data import contract
from tools.dist_data.artifacts import DistDataError

Vec3 = tuple[float, float, float]
Rect = tuple[float, float, float, float]  # (x0, y0, x1, y1) 像素，top-left 原点


class ProjectionError(DistDataError):
    """投影合同违反（相机字节不自洽等），一律 fail-closed。"""


@dataclass(frozen=True)
class Camera:
    """由 sidecar 归档字节直接构造的相机（不从四元数重算基向量）。"""

    position: Vec3
    right: Vec3
    up: Vec3
    forward: Vec3
    fx: float
    fy: float
    cx: float
    cy: float
    width: int
    height: int

    @classmethod
    def from_sidecar(cls, sidecar: dict[str, Any]) -> "Camera":
        try:
            intrinsics = sidecar["intrinsics_px"]
            camera = cls(
                position=tuple(float(v) for v in sidecar["camera_position_world_m"]),  # type: ignore[arg-type]
                right=tuple(float(v) for v in sidecar["camera_right_world"]),  # type: ignore[arg-type]
                up=tuple(float(v) for v in sidecar["camera_up_world"]),  # type: ignore[arg-type]
                forward=tuple(float(v) for v in sidecar["camera_forward_world"]),  # type: ignore[arg-type]
                fx=float(intrinsics["fx"]),
                fy=float(intrinsics["fy"]),
                cx=float(intrinsics["cx"]),
                cy=float(intrinsics["cy"]),
                width=int(sidecar["width"]),
                height=int(sidecar["height"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProjectionError(f"sidecar 位姿/内参不齐或不可解析：{exc}") from exc
        camera.assert_intrinsics_consistent(float(sidecar["vertical_fov_deg"]))
        return camera

    def assert_intrinsics_consistent(self, vertical_fov_deg: float) -> None:
        """§2.4：按 `vertical_fov_deg` + 宽高重算焦距并断言 |Δf| ≤ 0.5 px。"""
        half = math.radians(vertical_fov_deg) / 2.0
        if half <= 0.0 or half >= math.pi / 2.0:
            raise ProjectionError(f"vertical_fov_deg={vertical_fov_deg} 越界")
        recomputed = (self.height / 2.0) / math.tan(half)
        tolerance = contract.PROJECTION_FOCAL_TOLERANCE_PX
        if abs(recomputed - self.fx) > tolerance or abs(recomputed - self.fy) > tolerance:
            raise ProjectionError(
                f"内参不一致：归档 fx={self.fx} fy={self.fy}，由 vfov 重算 {recomputed}"
                f"（容差 {tolerance} px）"
            )

    def to_camera_space(self, point: Vec3) -> Vec3:
        """世界点 → 相机系 `x=d·right, y=d·up, z=d·forward`。"""
        dx = point[0] - self.position[0]
        dy = point[1] - self.position[1]
        dz = point[2] - self.position[2]
        return (
            dx * self.right[0] + dy * self.right[1] + dz * self.right[2],
            dx * self.up[0] + dy * self.up[1] + dz * self.up[2],
            dx * self.forward[0] + dy * self.forward[1] + dz * self.forward[2],
        )

    def project_camera_point(self, point: Vec3) -> tuple[float, float]:
        """相机系点 → 像素（top-left 原点，y 向下）。"""
        x, y, z = point
        if z <= 0.0:
            raise ProjectionError("近平面之后的点不得直接投影")
        return (self.cx + self.fx * x / z, self.cy - self.fy * y / z)

    def viewport(self) -> Rect:
        return (0.0, 0.0, float(self.width), float(self.height))


def aabb_corners(bounds: dict[str, float]) -> list[Vec3]:
    """AABB 八角点，顺序确定（x→y→z 的字典序）。"""
    return [
        (x, y, z)
        for x in (bounds["min_x_m"], bounds["max_x_m"])
        for y in (bounds["min_y_m"], bounds["max_y_m"])
        for z in (bounds["min_z_m"], bounds["max_z_m"])
    ]


_EDGE_INDEX: tuple[tuple[int, int], ...] = (
    (0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
    (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7),
)


def _clip_edge_at_near(a: Vec3, b: Vec3, near: float) -> Vec3 | None:
    """把跨近平面的棱在 `z = near` 处裁剪，返回交点（相机系）。"""
    za, zb = a[2], b[2]
    if (za > near) == (zb > near):
        return None
    denominator = zb - za
    if denominator == 0.0:
        return None
    t = (near - za) / denominator
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), near)


def project_aabb(camera: Camera, bounds: dict[str, float]) -> Rect | None:
    """AABB → amodal 像素框；全部角点在近面之后返回 None（`NOT_IN_VIEW`）。"""
    near = contract.NEAR_CLIP_Z_M
    corners = [camera.to_camera_space(corner) for corner in aabb_corners(bounds)]
    kept = [corner for corner in corners if corner[2] > near]
    if not kept:
        return None
    points = list(kept)
    if len(kept) != len(corners):  # 有角点在近面之前 → 对 12 条棱做近平面裁剪
        for i, j in _EDGE_INDEX:
            crossing = _clip_edge_at_near(corners[i], corners[j], near)
            if crossing is not None:
                points.append(crossing)
    pixels = [camera.project_camera_point(point) for point in points]
    xs = [pixel[0] for pixel in pixels]
    ys = [pixel[1] for pixel in pixels]
    return (min(xs), min(ys), max(xs), max(ys))


def intersect(a: Rect, b: Rect) -> Rect | None:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return None
    return (x0, y0, x1, y1)


def area(rect: Rect | None) -> float:
    if rect is None:
        return 0.0
    return max(0.0, rect[2] - rect[0]) * max(0.0, rect[3] - rect[1])


def union_area(rects: Iterable[Rect]) -> float:
    """轴对齐矩形并集面积（坐标压缩，精确）。"""
    boxes = [rect for rect in rects if area(rect) > 0.0]
    if not boxes:
        return 0.0
    xs = sorted({value for rect in boxes for value in (rect[0], rect[2])})
    total = 0.0
    for left, right in zip(xs, xs[1:]):
        if right <= left:
            continue
        spans = sorted(
            (rect[1], rect[3]) for rect in boxes if rect[0] <= left and rect[2] >= right
        )
        covered = 0.0
        current_start: float | None = None
        current_end = 0.0
        for start, end in spans:
            if current_start is None:
                current_start, current_end = start, end
            elif start > current_end:
                covered += current_end - current_start
                current_start, current_end = start, end
            else:
                current_end = max(current_end, end)
        if current_start is not None:
            covered += current_end - current_start
        total += (right - left) * covered
    return total


def iou(a: Rect, b: Rect) -> float:
    overlap = area(intersect(a, b))
    denominator = area(a) + area(b) - overlap
    return 0.0 if denominator <= 0.0 else overlap / denominator


def normalized_xywh(rect: Rect, camera: Camera) -> tuple[float, float, float, float]:
    """visible 框 → 归一化 top-left `xywh`，裁剪到 `[0,1]`（项目框协议）。"""
    x0 = min(max(rect[0] / camera.width, 0.0), 1.0)
    y0 = min(max(rect[1] / camera.height, 0.0), 1.0)
    x1 = min(max(rect[2] / camera.width, 0.0), 1.0)
    y1 = min(max(rect[3] / camera.height, 0.0), 1.0)
    return (x0, y0, max(0.0, x1 - x0), max(0.0, y1 - y0))


def denormalize_xywh(box: dict[str, float] | Sequence[float], camera: Camera) -> Rect:
    """归档归一化 `xywh` → 像素 Rect（用于把真值框当作图像面阻断体）。"""
    if isinstance(box, dict):
        x, y, w, h = (
            float(box["x"]),
            float(box["y"]),
            float(box.get("width", box.get("w", 0.0))),
            float(box.get("height", box.get("h", 0.0))),
        )
    else:
        x, y, w, h = (float(value) for value in box)
    return (
        x * camera.width,
        y * camera.height,
        (x + w) * camera.width,
        (y + h) * camera.height,
    )


@dataclass(frozen=True)
class ProjectedObject:
    """单帧单对象的投影结果与 §2.4 闭集状态（恰一个）。"""

    object_id: str
    status: str
    amodal_px: Rect | None
    visible_px: Rect | None
    visible_norm_xywh: tuple[float, float, float, float] | None
    camera_depth_m: float
    is_phantom: bool

    @property
    def blocks(self) -> bool:
        """`blocking(f)` 成员资格 = visible 面积 > 0。"""
        return area(self.visible_px) > 0.0

    @property
    def referable(self) -> bool:
        """`referable(f)` 成员资格 = 状态 `OK` 的目录对象。"""
        return self.status == "OK" and not self.is_phantom

    def as_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "status": self.status,
            "amodal_px": list(self.amodal_px) if self.amodal_px else None,
            "visible_px": list(self.visible_px) if self.visible_px else None,
            "visible_norm_xywh": (
                list(self.visible_norm_xywh) if self.visible_norm_xywh else None
            ),
            "camera_depth_m": self.camera_depth_m,
            "is_phantom": self.is_phantom,
            "blocks": self.blocks,
            "referable": self.referable,
        }


def _aabb_center(bounds: dict[str, float]) -> Vec3:
    return (
        (bounds["min_x_m"] + bounds["max_x_m"]) / 2.0,
        (bounds["min_y_m"] + bounds["max_y_m"]) / 2.0,
        (bounds["min_z_m"] + bounds["max_z_m"]) / 2.0,
    )


def project_instances(
    camera: Camera,
    instances: Sequence[dict[str, Any]],
    *,
    extra_blockers: Sequence[tuple[str, Rect, float]] = (),
) -> list[ProjectedObject]:
    """对一帧的全部布局实例做投影 + 画家序遮挡近似（保守排除）。

    `extra_blockers` = 只有图像面框的阻断体（动态目标真值框 / 扫掠代理），
    形如 `(id, 像素框, 相机系深度)`；它们参与遮挡与唯一性，但不可指称。
    """
    viewport = camera.viewport()
    staged: list[dict[str, Any]] = []
    for instance in instances:
        name = instance["scene_object_name"]
        is_phantom = bool(instance.get("phantom", False))
        depth = camera.to_camera_space(_aabb_center(instance))[2]
        amodal = project_aabb(camera, instance)
        visible = intersect(amodal, viewport) if amodal else None
        staged.append(
            {
                "object_id": name,
                "amodal": amodal,
                "visible": visible,
                "depth": depth,
                "phantom": is_phantom,
                "sort_name": name,
            }
        )
    for blocker_id, rect, depth in extra_blockers:
        visible = intersect(rect, viewport)
        staged.append(
            {
                "object_id": blocker_id,
                "amodal": rect,
                "visible": visible,
                "depth": depth,
                "phantom": False,
                "sort_name": blocker_id,
                "blocker_only": True,
            }
        )

    # 画家序：相机系 AABB 中心距离升序，tie-break `scene_object_name` 字典序。
    order = sorted(staged, key=lambda item: (item["depth"], item["sort_name"]))

    results: list[ProjectedObject] = []
    for index, item in enumerate(order):
        visible = item["visible"]
        amodal = item["amodal"]
        if item.get("blocker_only"):
            continue
        if item["phantom"]:
            status = "PHANTOM"
        elif amodal is None or visible is None or area(visible) <= 0.0:
            status = "NOT_IN_VIEW"
        elif min(visible[2] - visible[0], visible[3] - visible[1]) < contract.MIN_VISIBLE_SIDE_PX:
            status = "TOO_SMALL"
        elif area(visible) / area(amodal) < contract.TRUNCATION_VISIBLE_AREA_RATIO:
            status = "TRUNCATED"
        else:
            status = "OK"
            for nearer in order[:index]:
                nearer_visible = nearer["visible"]
                if nearer_visible is None:
                    continue
                overlap = area(intersect(visible, nearer_visible))
                if overlap / area(visible) >= contract.THETA_OCC:
                    status = "EXCLUDED_OCCLUDED"
                    break
        results.append(
            ProjectedObject(
                object_id=item["object_id"],
                status=status,
                amodal_px=amodal,
                visible_px=visible,
                visible_norm_xywh=normalized_xywh(visible, camera) if visible else None,
                camera_depth_m=item["depth"],
                is_phantom=bool(item["phantom"]),
            )
        )
    results.sort(key=lambda projected: projected.object_id)
    return results


def route_sweep_rects(
    camera: Camera,
    route: Sequence[dict[str, float]],
    envelope_half_extents: Vec3,
) -> list[Rect]:
    """§2.3 无逐帧目标真值族的**全路线扫掠代理区域**投影框集合。

    构造：逐路线线段取「线段 ⊕ 全体目录车辆 AABB 尺寸最大包络」的 AABB
    （轴对齐线段上与精确 Minkowski 和重合，斜线段上是其外包围，方向保守），
    再逐段投影。无自由采样参数。
    """
    half_x, half_y, half_z = envelope_half_extents
    rects: list[Rect] = []
    points = [(float(p["x"]), float(p.get("y", 0.0)), float(p["z"])) for p in route]
    if not points:
        return rects
    segments = list(zip(points, points[1:] + points[:1])) if len(points) > 1 else [
        (points[0], points[0])
    ]
    for start, end in segments:
        bounds = {
            "min_x_m": min(start[0], end[0]) - half_x,
            "max_x_m": max(start[0], end[0]) + half_x,
            "min_y_m": min(start[1], end[1]) - half_y,
            "max_y_m": max(start[1], end[1]) + half_y,
            "min_z_m": min(start[2], end[2]) - half_z,
            "max_z_m": max(start[2], end[2]) + half_z,
        }
        projected = project_aabb(camera, bounds)
        if projected is None:
            continue
        clipped = intersect(projected, camera.viewport())
        if clipped is not None:
            rects.append(clipped)
    return rects


def station_bin(camera: Camera) -> dict[str, Any]:
    """§2.4 站位簇全局分箱键：位置 2 m 格 × 方位 15° 箱 × 俯角带。"""
    x_bin = math.floor(camera.position[0] / contract.STATION_POSITION_BIN_M)
    z_bin = math.floor(camera.position[2] / contract.STATION_POSITION_BIN_M)
    azimuth_deg = math.degrees(math.atan2(camera.forward[0], camera.forward[2])) % 360.0
    azimuth_bin = int(azimuth_deg // contract.STATION_AZIMUTH_BIN_DEG)
    forward_y = min(1.0, max(-1.0, camera.forward[1]))
    elevation_deg = -math.degrees(math.asin(forward_y))
    band: int | None = None
    for index, (low, high) in enumerate(contract.STATION_ELEVATION_BANDS):
        if low <= elevation_deg < high or (
            index == len(contract.STATION_ELEVATION_BANDS) - 1 and elevation_deg == high
        ):
            band = index
            break
    return {
        "x_bin": x_bin,
        "z_bin": z_bin,
        "azimuth_bin": azimuth_bin,
        "elevation_band": band,
        "elevation_deg": elevation_deg,
        "key": None if band is None else f"{x_bin}:{z_bin}:{azimuth_bin}:{band}",
    }
