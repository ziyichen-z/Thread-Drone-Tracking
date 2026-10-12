from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

from .trackers import BoxNorm, clip_box_norm


Vector3 = tuple[float, float, float]


class GeometryRejected(ValueError):
    pass


@dataclass(frozen=True)
class GroundIntersection:
    point_world_m: Vector3
    ray_direction_world: Vector3
    distance_along_ray_m: float


def _finite(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _vector(metadata: Mapping[str, Any], key: str) -> Vector3:
    raw = metadata.get(key)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or len(raw) != 3:
        raise ValueError(f"{key} must be a three-element vector")
    return (
        _finite(raw[0], f"{key}[0]"),
        _finite(raw[1], f"{key}[1]"),
        _finite(raw[2], f"{key}[2]"),
    )


def _add(*vectors: Vector3) -> Vector3:
    return tuple(sum(vector[index] for vector in vectors) for index in range(3))  # type: ignore[return-value]


def _scale(vector: Vector3, factor: float) -> Vector3:
    return tuple(component * factor for component in vector)  # type: ignore[return-value]


def _normalize(vector: Vector3) -> Vector3:
    norm = math.sqrt(sum(component * component for component in vector))
    if not math.isfinite(norm) or norm <= 1e-12:
        raise GeometryRejected("degenerate_ray")
    return tuple(component / norm for component in vector)  # type: ignore[return-value]


def box_ground_intersection(
    box_norm: Sequence[float],
    metadata: Mapping[str, Any],
    ground_plane_y_m: float,
    maximum_distance_m: float = 1000.0,
) -> GroundIntersection:
    box: BoxNorm | None = clip_box_norm(box_norm)
    if box is None:
        raise GeometryRejected("invalid_box")

    width = int(metadata.get("width", 0))
    height = int(metadata.get("height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("metadata image dimensions must be positive")

    intrinsics = metadata.get("intrinsics_px")
    if not isinstance(intrinsics, Mapping):
        raise ValueError("intrinsics_px must be an object")
    fx = _finite(intrinsics.get("fx"), "intrinsics_px.fx")
    fy = _finite(intrinsics.get("fy"), "intrinsics_px.fy")
    cx = _finite(intrinsics.get("cx"), "intrinsics_px.cx")
    cy = _finite(intrinsics.get("cy"), "intrinsics_px.cy")
    if fx <= 0.0 or fy <= 0.0:
        raise ValueError("focal lengths must be positive")

    origin = _vector(metadata, "camera_position_world_m")
    right = _vector(metadata, "camera_right_world")
    up = _vector(metadata, "camera_up_world")
    forward = _vector(metadata, "camera_forward_world")

    x, y, box_width, box_height = box
    u = (x + box_width * 0.5) * width
    v = (y + box_height) * height
    ray = _normalize(
        _add(
            _scale(right, (u - cx) / fx),
            _scale(up, -(v - cy) / fy),
            forward,
        )
    )

    ground_y = _finite(ground_plane_y_m, "ground_plane_y_m")
    maximum_distance = _finite(maximum_distance_m, "maximum_distance_m")
    if maximum_distance <= 0.0:
        raise ValueError("maximum_distance_m must be positive")
    if ray[1] >= -1e-9:
        raise GeometryRejected("parallel_or_upward_ray")

    distance = (ground_y - origin[1]) / ray[1]
    if not math.isfinite(distance) or distance <= 0.0:
        raise GeometryRejected("non_positive_intersection")
    if distance > maximum_distance:
        raise GeometryRejected("intersection_beyond_maximum_distance")

    point = _add(origin, _scale(ray, distance))
    if not all(math.isfinite(component) for component in point):
        raise GeometryRejected("non_finite_intersection")
    return GroundIntersection(point, ray, distance)
