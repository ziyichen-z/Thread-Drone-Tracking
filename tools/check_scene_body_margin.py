#!/usr/bin/env python3
"""P1-M3-BODY-001 batch 1a-alpha tool 2: scene/body suitability recompute.

Discharges BC-M34-4 (a) and (b) mechanically on the frozen main-loop carrier,
and produces the measurement window BC-BODY1-2 freezes:

* ``C_geom`` upper bound (frustum only) and lower bound (frustum + box-level
  occlusion), over the **whole loop** - BC-BODY1-2 puts H1's domain on the
  full trial including the occluded arc;
* the **visible-arc intervals** in route mileage, SHA-256 frozen, plus the
  ``route[0]``-in-arc check the same clarification requires;
* occlusion attribution by obstacle instance and canonical name;
* the ``C_quality`` projection for arm A (gimbal-only) and arm B (threshold
  allocation), inside the measurement window only.

The visibility predicate is isomorphic to the runtime, line for line:
``CoverageEvaluator.EvaluateVisibility`` (:727-764), ``BoundsCorners``
(:814-825), ``VisibilitySamples`` (:827-841), ``ProjectBounds`` (:781-812),
``TetheredGimbal.LateUpdate`` (:27-46) and ``TargetVisualFactory``
(:71-90). Every constant is read from frozen bytes or reproduced from the
named source line; nothing is tuned.

Pre-registered reductions, stated here **before** any number is read, so a
reviewer can see what the projection is and is not (BC-BODY1-6 forbids
adjusting anything after the tool runs; the only legal move on disagreement
is to return to Acceptance):

R1. Route domain is the frozen scenario polyline sampled every 0.5 m, the
    step the proposal section 3.3 states. Target heading is the segment
    direction.
R2. The gimbal aims at the target's ground point ``(x, 0.2, z)`` - the
    zero-tracker-error limit of ``track_loop.py:615``'s
    ``look_at(intersection.point_world_m)``.
R3. Arm A holds the body at the hover point above the anchor for the whole
    loop. This is the current ``hold_body()`` behaviour.
R4. Arm B is a **quasi-static** projection of the section 3.5 policy: at each
    route position the body sits at the smallest horizontal displacement from
    the anchor, along the target bearing, that brings the off-nadir angle to
    the policy's release threshold (25 deg, i.e. margin 20 deg). Altitude is
    held at ``altitude_hold_m``. The displacement is clamped by the tether
    sphere and then shortened, in 0.05 m steps, until the anchor -> body
    segment clears every obstacle prism inflated by the 1.0 m corridor
    radius; if no positive displacement clears, the arm holds. It ignores the
    4 m/s body dynamics and the 120 deg/s gimbal slew on purpose - those are
    what the batch 1c run measures, and section 3.2 already states that this
    projection is geometry, not a measurement.
R5. Offline occluders are the 779 road-audit obstacle instances as world
    AABBs. Two disclosed modelling gaps in known directions: AABBs
    over-estimate blocking against the runtime's non-convex mesh colliders
    (this is what makes the occluded result a *lower* bound on ``C_geom``),
    and road surfaces are not occluders here although they are at run time
    (a downward ray ending 0.05 m short of a point >= 0.2 m above the road
    plane cannot hit it, so the expected effect is nil, but it is recorded
    rather than assumed).

CLI:
    python3 tools/check_scene_body_margin.py [--output PATH] [--spacing M]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ARTIFACT_SCHEMA = "p1-m3-body-001-scene-body-margin/v1"
SCENE_GEOMETRY_SCHEMA = "p1-m3-body-001-scene-geometry/v1"
WORK_ID = "P1-M3-BODY-001"

SCENARIO_PATH = PROJECT_ROOT / "config" / "scenario.default.json"
SCENE_GEOMETRY_PATH = (
    PROJECT_ROOT / "docs" / "evidence" / "P1-M3-BODY-001-scene-geometry.json"
)
ANCHOR_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "evidence" / "P1-M3-BODY-001-anchor-audit.json"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "docs" / "evidence" / "P1-M3-BODY-001-scene-body-margin.json"
)

# Proposal section 3.3: the occlusion structure was resolved at a 0.5 m step.
ROUTE_SAMPLE_SPACING_M = 0.5

# `TargetVisualFactory.AddTargetVisual` (:71-90), the single production
# construction source for the target visual. Local centre and full scale.
TARGET_CUBES = (
    ((0.0, 0.5, 0.0), (2.0, 1.0, 4.0)),
    ((0.0, 1.2, -0.2), (1.7, 0.7, 2.0)),
)

# `CoverageEvaluator.HasClearLineOfSight` (:766-779) shortens the ray.
RAYCAST_BACKOFF_M = 0.05
# `TetheredGimbal.LateUpdate` (:38) saturation dead band.
GIMBAL_SATURATION_DEAD_BAND_DEG = 0.1

# Section 3.5 pre-registered policy values (BC-BODY1-6 freezes them; the tool
# may not adjust them after producing output).
MARGIN_TRIGGER_DEG = 10.0
MARGIN_RELEASE_DEG = 20.0
ALTITUDE_HOLD_M = 25.0
CORRIDOR_NOMINAL_RADIUS_M = 0.5
CORRIDOR_CLEARANCE_MARGIN_M = 0.5
CORRIDOR_SHORTEN_STEP_M = 0.05

# BC-BODY1-1 pre-registers the third `C_quality` component's threshold.
MIN_SIDE_FLOOR_PX = 20.0


class MarginFailure(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise MarginFailure(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


# --------------------------------------------------------------------------
# Route geometry
# --------------------------------------------------------------------------


def _perimeter(vertices: Sequence[tuple[float, float]]) -> float:
    return sum(
        math.dist(vertices[index], vertices[(index + 1) % len(vertices)])
        for index in range(len(vertices))
    )


def sample_route(
    vertices: Sequence[tuple[float, float]],
    spacing: float,
) -> list[tuple[float, tuple[float, float], tuple[float, float]]]:
    """(mileage, position, unit heading) every `spacing` metres, closed."""
    perimeter = _perimeter(vertices)
    count = int(math.ceil(perimeter / spacing))
    samples = []
    for index in range(count):
        mileage = index * spacing
        remaining = mileage
        for vertex in range(len(vertices)):
            start = vertices[vertex]
            end = vertices[(vertex + 1) % len(vertices)]
            length = math.dist(start, end)
            if remaining <= length or vertex == len(vertices) - 1:
                parameter = 0.0 if length == 0.0 else min(1.0, remaining / length)
                position = (
                    start[0] + parameter * (end[0] - start[0]),
                    start[1] + parameter * (end[1] - start[1]),
                )
                heading = (
                    ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
                    if length > 0.0
                    else (1.0, 0.0)
                )
                samples.append((mileage, position, heading))
                break
            remaining -= length
    return samples


# --------------------------------------------------------------------------
# Target bounds: `Renderer.bounds` is the world AABB of the rotated cube, and
# `EvaluateVisibility` encapsulates both renderers before sampling.
# --------------------------------------------------------------------------


def target_world_bounds(
    position: tuple[float, float],
    plane_y: float,
    heading: tuple[float, float],
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    # Unity `LookRotation(direction)` with direction in the XZ plane is a pure
    # yaw, so the world AABB half extent of an axis-aligned local box is
    # |R| @ half_extent with R the yaw matrix.
    sine, cosine = heading[0], heading[1]
    minimum = [math.inf] * 3
    maximum = [-math.inf] * 3
    for local_center, scale in TARGET_CUBES:
        half = (scale[0] / 2.0, scale[1] / 2.0, scale[2] / 2.0)
        center = (
            position[0] + cosine * local_center[0] + sine * local_center[2],
            plane_y + local_center[1],
            position[1] - sine * local_center[0] + cosine * local_center[2],
        )
        extent = (
            abs(cosine) * half[0] + abs(sine) * half[2],
            half[1],
            abs(sine) * half[0] + abs(cosine) * half[2],
        )
        for axis in range(3):
            minimum[axis] = min(minimum[axis], center[axis] - extent[axis])
            maximum[axis] = max(maximum[axis], center[axis] + extent[axis])
    return tuple(minimum), tuple(maximum)  # type: ignore[return-value]


def bounds_corners(
    minimum: tuple[float, float, float],
    maximum: tuple[float, float, float],
) -> list[tuple[float, float, float]]:
    """`CoverageEvaluator.BoundsCorners` (:814-825), same order."""
    return [
        (minimum[0], minimum[1], minimum[2]),
        (minimum[0], minimum[1], maximum[2]),
        (minimum[0], maximum[1], minimum[2]),
        (minimum[0], maximum[1], maximum[2]),
        (maximum[0], minimum[1], minimum[2]),
        (maximum[0], minimum[1], maximum[2]),
        (maximum[0], maximum[1], minimum[2]),
        (maximum[0], maximum[1], maximum[2]),
    ]


def visibility_samples(
    minimum: tuple[float, float, float],
    maximum: tuple[float, float, float],
    corners: Sequence[tuple[float, float, float]],
) -> list[tuple[float, float, float]]:
    """`CoverageEvaluator.VisibilitySamples` (:827-841): 8 corners + 7."""
    center = tuple((minimum[axis] + maximum[axis]) / 2.0 for axis in range(3))
    extents = tuple((maximum[axis] - minimum[axis]) / 2.0 for axis in range(3))
    return list(corners) + [
        center,
        (center[0], center[1] + extents[1], center[2]),
        (center[0], center[1] - extents[1], center[2]),
        (center[0] + extents[0], center[1], center[2]),
        (center[0] - extents[0], center[1], center[2]),
        (center[0], center[1], center[2] + extents[2]),
        (center[0], center[1], center[2] - extents[2]),
    ]


# --------------------------------------------------------------------------
# Gimbal and camera
# --------------------------------------------------------------------------


def gimbal_pose(
    camera_position: tuple[float, float, float],
    aim_point: tuple[float, float, float],
    maximum_off_nadir_deg: float,
) -> dict[str, Any]:
    """`TetheredGimbal.LateUpdate` (:27-46), converged (no slew lag)."""
    delta = tuple(aim_point[axis] - camera_position[axis] for axis in range(3))
    horizontal = math.hypot(delta[0], delta[2])
    height = max(0.1, -delta[1])
    requested = math.degrees(math.atan2(horizontal, height))
    applied = min(requested, maximum_off_nadir_deg)
    saturated = requested > maximum_off_nadir_deg + GIMBAL_SATURATION_DEAD_BAND_DEG
    yaw = math.degrees(math.atan2(delta[0], delta[2])) if horizontal > 0.001 else 0.0
    return {
        "requested_off_nadir_deg": requested,
        "applied_off_nadir_deg": applied,
        "saturated": saturated,
        "yaw_deg": yaw,
    }


def camera_basis(
    applied_off_nadir_deg: float,
    yaw_deg: float,
) -> tuple[tuple[float, float, float], ...]:
    """Basis of `Quaternion.Euler(90 - applied, yaw, 0)` (right, up, forward).

    Unity composes Euler angles as ``Ry * Rx * Rz``; with roll zero this is
    ``Ry(yaw) * Rx(90 - applied)``.
    """
    pitch = math.radians(90.0 - applied_off_nadir_deg)
    yaw = math.radians(yaw_deg)
    sin_p, cos_p = math.sin(pitch), math.cos(pitch)
    sin_y, cos_y = math.sin(yaw), math.cos(yaw)
    right = (cos_y, 0.0, -sin_y)
    up = (sin_y * sin_p, cos_p, cos_y * sin_p)
    forward = (sin_y * cos_p, -sin_p, cos_y * cos_p)
    return right, up, forward


def world_to_viewport(
    point: tuple[float, float, float],
    camera_position: tuple[float, float, float],
    basis: tuple[tuple[float, float, float], ...],
    half_width_tangent: float,
    half_height_tangent: float,
) -> tuple[float, float, float]:
    """Unity `Camera.WorldToViewportPoint`; z is the distance along forward."""
    right, up, forward = basis
    delta = tuple(point[axis] - camera_position[axis] for axis in range(3))
    depth = sum(delta[axis] * forward[axis] for axis in range(3))
    if depth == 0.0:
        return (0.0, 0.0, 0.0)
    lateral = sum(delta[axis] * right[axis] for axis in range(3))
    vertical = sum(delta[axis] * up[axis] for axis in range(3))
    return (
        0.5 + (lateral / depth) / (2.0 * half_width_tangent),
        0.5 + (vertical / depth) / (2.0 * half_height_tangent),
        depth,
    )


def project_bounds(
    corners: Sequence[tuple[float, float, float]],
    camera_position: tuple[float, float, float],
    basis: tuple[tuple[float, float, float], ...],
    half_width_tangent: float,
    half_height_tangent: float,
) -> tuple[float, float, float, float] | None:
    """`CoverageEvaluator.ProjectBounds` (:781-812): clipped top-left xywh."""
    minimum_x = minimum_y = math.inf
    maximum_x = maximum_y = -math.inf
    has_front_point = False
    for corner in corners:
        viewport = world_to_viewport(
            corner, camera_position, basis, half_width_tangent, half_height_tangent
        )
        if viewport[2] <= 0.0:
            continue
        has_front_point = True
        minimum_x = min(minimum_x, viewport[0])
        minimum_y = min(minimum_y, viewport[1])
        maximum_x = max(maximum_x, viewport[0])
        maximum_y = max(maximum_y, viewport[1])
    if not has_front_point:
        return None
    clipped_min_x = min(1.0, max(0.0, minimum_x))
    clipped_max_x = min(1.0, max(0.0, maximum_x))
    clipped_min_y = min(1.0, max(0.0, minimum_y))
    clipped_max_y = min(1.0, max(0.0, maximum_y))
    if clipped_max_x <= clipped_min_x or clipped_max_y <= clipped_min_y:
        return None
    return (
        clipped_min_x,
        1.0 - clipped_max_y,
        clipped_max_x - clipped_min_x,
        clipped_max_y - clipped_min_y,
    )


# --------------------------------------------------------------------------
# Occlusion: segment vs world AABB
# --------------------------------------------------------------------------


class PrismIndex:
    """Broad-phase over the frozen obstacle prisms (XZ cell buckets)."""

    CELL_M = 8.0

    def __init__(self, instances: Sequence[Mapping[str, Any]]):
        self.boxes = [
            (
                float(item["min_x_m"]),
                float(item["min_y_m"]),
                float(item["min_z_m"]),
                float(item["max_x_m"]),
                float(item["max_y_m"]),
                float(item["max_z_m"]),
                str(item["scene_object_name"]),
                str(item["canonical_name"]),
            )
            for item in instances
        ]
        self.cells: dict[tuple[int, int], list[int]] = {}
        for index, box in enumerate(self.boxes):
            for cell_x in range(
                int(math.floor(box[0] / self.CELL_M)),
                int(math.floor(box[3] / self.CELL_M)) + 1,
            ):
                for cell_z in range(
                    int(math.floor(box[2] / self.CELL_M)),
                    int(math.floor(box[5] / self.CELL_M)) + 1,
                ):
                    self.cells.setdefault((cell_x, cell_z), []).append(index)

    def candidates(
        self,
        start: tuple[float, float, float],
        end: tuple[float, float, float],
        pad: float = 0.0,
    ) -> set[int]:
        minimum_x = min(start[0], end[0]) - pad
        maximum_x = max(start[0], end[0]) + pad
        minimum_z = min(start[2], end[2]) - pad
        maximum_z = max(start[2], end[2]) + pad
        found: set[int] = set()
        for cell_x in range(
            int(math.floor(minimum_x / self.CELL_M)),
            int(math.floor(maximum_x / self.CELL_M)) + 1,
        ):
            for cell_z in range(
                int(math.floor(minimum_z / self.CELL_M)),
                int(math.floor(maximum_z / self.CELL_M)) + 1,
            ):
                found.update(self.cells.get((cell_x, cell_z), ()))
        return found


def segment_hits_box(
    start: tuple[float, float, float],
    direction: tuple[float, float, float],
    length: float,
    box: Sequence[float],
    pad: float = 0.0,
) -> bool:
    """Slab test for a ray of finite length against an (inflated) AABB."""
    near, far = 0.0, length
    for axis in range(3):
        low = box[axis] - pad
        high = box[axis + 3] + pad
        if abs(direction[axis]) < 1e-12:
            if start[axis] < low or start[axis] > high:
                return False
            continue
        inverse = 1.0 / direction[axis]
        first = (low - start[axis]) * inverse
        second = (high - start[axis]) * inverse
        if first > second:
            first, second = second, first
        near = max(near, first)
        far = min(far, second)
        if near > far:
            return False
    return True


def blocking_instances(
    origin: tuple[float, float, float],
    point: tuple[float, float, float],
    index: PrismIndex,
) -> list[int]:
    """Every prism that blocks the shortened camera -> sample segment."""
    delta = tuple(point[axis] - origin[axis] for axis in range(3))
    distance = math.sqrt(sum(component * component for component in delta))
    if distance <= RAYCAST_BACKOFF_M:
        return []
    direction = tuple(component / distance for component in delta)
    length = distance - RAYCAST_BACKOFF_M
    return [
        candidate
        for candidate in index.candidates(origin, point)
        if segment_hits_box(origin, direction, length, index.boxes[candidate])
    ]


def corridor_is_clear(
    anchor: tuple[float, float, float],
    body: tuple[float, float, float],
    index: PrismIndex,
    radius: float,
) -> bool:
    """Anchor -> body tether segment inflated by `radius` clears every prism.

    Inflating the box rather than sweeping a true capsule over-estimates
    blocking at the box corners; that is the conservative direction for a
    safety check and is recorded as such.
    """
    delta = tuple(body[axis] - anchor[axis] for axis in range(3))
    distance = math.sqrt(sum(component * component for component in delta))
    if distance <= 0.0:
        return True
    direction = tuple(component / distance for component in delta)
    for candidate in index.candidates(anchor, body, pad=radius):
        if segment_hits_box(
            anchor, direction, distance, index.boxes[candidate], pad=radius
        ):
            return False
    return True


# --------------------------------------------------------------------------
# Per-sample evaluation
# --------------------------------------------------------------------------


def evaluate_sample(
    camera_position: tuple[float, float, float],
    target_position: tuple[float, float],
    heading: tuple[float, float],
    plane_y: float,
    sensor: Mapping[str, Any],
    maximum_off_nadir_deg: float,
    minimum_visible_fraction: float,
    index: PrismIndex,
    occlusion: bool,
) -> dict[str, Any]:
    minimum, maximum = target_world_bounds(target_position, plane_y, heading)
    corners = bounds_corners(minimum, maximum)
    samples = visibility_samples(minimum, maximum, corners)
    aim = (target_position[0], plane_y, target_position[1])
    pose = gimbal_pose(camera_position, aim, maximum_off_nadir_deg)
    basis = camera_basis(pose["applied_off_nadir_deg"], pose["yaw_deg"])

    width, height = int(sensor["width"]), int(sensor["height"])
    half_height_tangent = math.tan(math.radians(float(sensor["vertical_fov_deg"])) / 2.0)
    half_width_tangent = half_height_tangent * width / height

    in_frustum = 0
    visible = 0
    blockers: dict[int, int] = {}
    for point in samples:
        viewport = world_to_viewport(
            point, camera_position, basis, half_width_tangent, half_height_tangent
        )
        if not (
            viewport[2] > 0.0
            and 0.0 <= viewport[0] <= 1.0
            and 0.0 <= viewport[1] <= 1.0
        ):
            continue
        in_frustum += 1
        if not occlusion:
            visible += 1
            continue
        hits = blocking_instances(camera_position, point, index)
        if hits:
            for hit in hits:
                blockers[hit] = blockers.get(hit, 0) + 1
        else:
            visible += 1

    box = project_bounds(
        corners, camera_position, basis, half_width_tangent, half_height_tangent
    )
    if box is None:
        area_pixels = 0.0
        center_error = 0.0
        minimum_side = 0.0
    else:
        area_pixels = box[2] * box[3] * width * height
        center_error = math.hypot(
            (box[0] + box[2] / 2.0 - 0.5) * width,
            (box[1] + box[3] / 2.0 - 0.5) * height,
        )
        minimum_side = min(box[2] * width, box[3] * height)
    visible_fraction = visible / len(samples)
    return {
        "in_frustum_count": in_frustum,
        "visible_count": visible,
        "visible_fraction": visible_fraction,
        "geometrically_visible": visible_fraction >= minimum_visible_fraction,
        "area_px": area_pixels,
        "center_error_px": center_error,
        "minimum_side_px": minimum_side,
        "gimbal_saturated": pose["saturated"],
        "requested_off_nadir_deg": pose["requested_off_nadir_deg"],
        "blockers": blockers,
    }


def arm_b_body_position(
    anchor: tuple[float, float, float],
    hover_y: float,
    target_position: tuple[float, float],
    plane_y: float,
    tether_length_m: float,
    maximum_off_nadir_deg: float,
    index: PrismIndex,
    corridor_radius: float,
) -> tuple[tuple[float, float, float], float]:
    """Reduction R4: the quasi-static threshold-allocation body position."""
    bearing_x = target_position[0] - anchor[0]
    bearing_z = target_position[1] - anchor[2]
    horizontal = math.hypot(bearing_x, bearing_z)
    hover = (anchor[0], hover_y, anchor[2])
    if horizontal <= 1e-9:
        return hover, 0.0
    drop = hover_y - plane_y
    # Displacement that brings the off-nadir angle down to the release
    # threshold; zero when the policy would already be released.
    release_angle = math.radians(maximum_off_nadir_deg - MARGIN_RELEASE_DEG)
    allowed_horizontal = drop * math.tan(release_angle)
    required = horizontal - allowed_horizontal
    if required <= 0.0:
        return hover, 0.0
    # Tether sphere: the plant clamps the horizontal radius at this altitude.
    reach = tether_length_m * tether_length_m - drop * drop
    maximum_displacement = math.sqrt(reach) if reach > 0.0 else 0.0
    displacement = min(required, maximum_displacement)
    unit = (bearing_x / horizontal, bearing_z / horizontal)
    steps = int(math.floor(displacement / CORRIDOR_SHORTEN_STEP_M))
    for step in range(steps, -1, -1):
        candidate_distance = step * CORRIDOR_SHORTEN_STEP_M
        body = (
            anchor[0] + unit[0] * candidate_distance,
            hover_y,
            anchor[2] + unit[1] * candidate_distance,
        )
        if corridor_is_clear(anchor, body, index, corridor_radius):
            return body, candidate_distance
    return hover, 0.0


# --------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------


def _intervals_from_flags(
    mileages: Sequence[float],
    flags: Sequence[bool],
    spacing: float,
    perimeter: float,
) -> list[dict[str, Any]]:
    """Maximal contiguous visible runs on the **closed** loop.

    A run that spans the seam is one interval whose ``end_m`` exceeds the
    perimeter, not two: the loop has no start, and splitting the run at the
    seam would misreport a single visible arc as two and would make the
    ``route[0]``-in-arc check BC-BODY1-2 requires come out false whenever the
    arc happens to contain the seam - which on this carrier it does.
    """
    count = len(flags)
    if not any(flags):
        return []
    if all(flags):
        return [
            {
                "start_m": 0.0,
                "end_m": perimeter,
                "length_m": perimeter,
                "wraps": False,
            }
        ]
    starts = [
        index
        for index in range(count)
        if flags[index] and not flags[(index - 1) % count]
    ]
    intervals = []
    for start in starts:
        length = 0
        while flags[(start + length) % count] and length < count:
            length += 1
        begin = mileages[start]
        intervals.append(
            {
                "start_m": begin,
                "end_m": begin + length * spacing,
                "length_m": length * spacing,
                "wraps": begin + length * spacing > perimeter + 1e-9,
            }
        )
    intervals.sort(key=lambda item: item["start_m"])
    return intervals


def _interval_contains(
    interval: Mapping[str, Any],
    mileage: float,
    perimeter: float,
) -> bool:
    start, end = float(interval["start_m"]), float(interval["end_m"])
    return start <= mileage < end or start <= mileage + perimeter < end


def _quality(values: Sequence[float]) -> dict[str, Any]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return {"count": 0}

    def at(fraction: float) -> float:
        return ordered[int(fraction * (len(ordered) - 1))]

    return {
        "count": len(ordered),
        "min": ordered[0],
        "p10": at(0.10),
        "median": statistics.median(ordered),
        "max": ordered[-1],
    }


def build_margin(
    spacing: float = ROUTE_SAMPLE_SPACING_M,
) -> dict[str, Any]:
    scenario = _load(SCENARIO_PATH)
    geometry = _load(SCENE_GEOMETRY_PATH)
    anchor_audit = _load(ANCHOR_AUDIT_PATH)

    _require(
        geometry.get("schema_version") == SCENE_GEOMETRY_SCHEMA,
        f"scene geometry schema must be {SCENE_GEOMETRY_SCHEMA}",
    )
    _require(
        geometry.get("source_scenario_sha256") == sha256_file(SCENARIO_PATH),
        "scene geometry was built from different scenario bytes",
    )
    # Hard gate 1 governs everything downstream (BC-BODY1-3).
    _require(
        anchor_audit.get("status") == "CLEAR",
        "the anchor audit is not CLEAR; batch 1a-alpha stops at tool 1",
    )

    anchor = (
        float(scenario["anchor_world_m"]["x"]),
        float(scenario["anchor_world_m"]["y"]),
        float(scenario["anchor_world_m"]["z"]),
    )
    route = scenario["target"]["route_world_m"]
    vertices = [(float(point["x"]), float(point["z"])) for point in route]
    plane_y = float(route[0]["y"])
    _require(
        all(abs(float(point["y"]) - plane_y) <= 1e-9 for point in route),
        "route vertices must share one ground plane",
    )
    drone = scenario["drone"]
    sensor = scenario["sensor"]
    maximum_off_nadir_deg = float(scenario["gimbal"]["maximum_off_nadir_deg"])
    minimum_visible_fraction = float(
        scenario["evaluation"]["minimum_visible_sample_fraction"]
    )
    hover_y = anchor[1] + float(drone["initial_altitude_m"])
    _require(
        abs(float(drone["initial_altitude_m"]) - ALTITUDE_HOLD_M) <= 1e-9,
        "scenario altitude disagrees with the pre-registered altitude hold",
    )

    index = PrismIndex(geometry["instances"])
    corridor_radius = CORRIDOR_NOMINAL_RADIUS_M + CORRIDOR_CLEARANCE_MARGIN_M
    samples = sample_route(vertices, spacing)
    perimeter = _perimeter(vertices)
    hover = (anchor[0], hover_y, anchor[2])

    arm_a: list[dict[str, Any]] = []
    arm_a_frustum: list[bool] = []
    arm_b: list[dict[str, Any]] = []
    displacements: list[float] = []
    blocker_counts: dict[int, int] = {}
    blocked_point_samples = 0

    for _, position, heading in samples:
        frustum_only = evaluate_sample(
            hover,
            position,
            heading,
            plane_y,
            sensor,
            maximum_off_nadir_deg,
            minimum_visible_fraction,
            index,
            occlusion=False,
        )
        arm_a_frustum.append(frustum_only["geometrically_visible"])
        occluded = evaluate_sample(
            hover,
            position,
            heading,
            plane_y,
            sensor,
            maximum_off_nadir_deg,
            minimum_visible_fraction,
            index,
            occlusion=True,
        )
        for instance, count in occluded["blockers"].items():
            blocker_counts[instance] = blocker_counts.get(instance, 0) + count
        blocked_point_samples += (
            frustum_only["in_frustum_count"] - occluded["visible_count"]
        )
        arm_a.append(occluded)

        body, displacement = arm_b_body_position(
            anchor,
            hover_y,
            position,
            plane_y,
            float(drone["tether_length_m"]),
            maximum_off_nadir_deg,
            index,
            corridor_radius,
        )
        displacements.append(displacement)
        arm_b.append(
            evaluate_sample(
                body,
                position,
                heading,
                plane_y,
                sensor,
                maximum_off_nadir_deg,
                minimum_visible_fraction,
                index,
                occlusion=True,
            )
        )

    mileages = [sample[0] for sample in samples]
    visible_flags = [entry["geometrically_visible"] for entry in arm_a]
    intervals = _intervals_from_flags(mileages, visible_flags, spacing, perimeter)
    route_zero_interval = next(
        (
            interval
            for interval in intervals
            if _interval_contains(interval, 0.0, perimeter)
        ),
        None,
    )
    _require(
        (route_zero_interval is not None) == bool(visible_flags and visible_flags[0]),
        "the visible-arc interval list disagrees with the route[0] sample flag",
    )
    # A window that starts at route[0] and ends where the target first enters
    # the occluded arc (proposal section 3.3 point 4: one Play = one trial).
    if visible_flags and visible_flags[0]:
        end_index = next(
            (index_ for index_, flag in enumerate(visible_flags) if not flag),
            len(visible_flags),
        )
        measurement_window = [0.0, end_index * spacing]
    else:
        measurement_window = None

    def window_slice(entries: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        if measurement_window is None:
            return []
        return [
            entry
            for mileage, entry in zip(mileages, entries)
            if measurement_window[0] <= mileage < measurement_window[1]
            and entry["geometrically_visible"]
        ]

    def quality(entries: Sequence[dict[str, Any]]) -> dict[str, Any]:
        return {
            "sample_count": len(entries),
            "area_px": _quality([entry["area_px"] for entry in entries]),
            "center_error_px": _quality(
                [entry["center_error_px"] for entry in entries]
            ),
            "minimum_side_px": _quality(
                [entry["minimum_side_px"] for entry in entries]
            ),
            "minimum_side_at_or_above_floor_fraction": (
                sum(
                    1
                    for entry in entries
                    if entry["minimum_side_px"] >= MIN_SIDE_FLOOR_PX
                )
                / len(entries)
                if entries
                else 0.0
            ),
            "gimbal_saturated_fraction": (
                sum(1 for entry in entries if entry["gimbal_saturated"]) / len(entries)
                if entries
                else 0.0
            ),
        }

    attribution = sorted(
        (
            {
                "scene_object_name": index.boxes[instance][6],
                "canonical_name": index.boxes[instance][7],
                "blocking_point_samples": count,
            }
            for instance, count in blocker_counts.items()
        ),
        key=lambda item: (-item["blocking_point_samples"], item["scene_object_name"]),
    )
    by_name: dict[str, int] = {}
    for entry in attribution:
        by_name[entry["canonical_name"]] = (
            by_name.get(entry["canonical_name"], 0) + entry["blocking_point_samples"]
        )

    c_geom_upper = sum(1 for flag in arm_a_frustum if flag) / len(arm_a_frustum)
    c_geom_lower = sum(1 for flag in visible_flags if flag) / len(visible_flags)
    arm_b_lower = sum(
        1 for entry in arm_b if entry["geometrically_visible"]
    ) / len(arm_b)

    interval_digest = hashlib.sha256(
        json.dumps(
            {
                "spacing_m": spacing,
                "perimeter_m": perimeter,
                "visible_arc_intervals_m": intervals,
                "measurement_window_m": measurement_window,
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()

    return {
        "schema_version": ARTIFACT_SCHEMA,
        "work_id": WORK_ID,
        "identity": {
            "scenario_sha256": sha256_file(SCENARIO_PATH),
            "scenario_id": scenario["scenario_id"],
            "scene_geometry_sha256": sha256_file(SCENE_GEOMETRY_PATH),
            "anchor_audit_sha256": sha256_file(ANCHOR_AUDIT_PATH),
            "obstacle_instance_count": int(geometry["instance_count"]),
        },
        "carrier": {
            "anchor_world_m": {"x": anchor[0], "y": anchor[1], "z": anchor[2]},
            "hover_point_world_m": {"x": hover[0], "y": hover[1], "z": hover[2]},
            "target_plane_y_m": plane_y,
            "vertical_drop_m": hover_y - plane_y,
            "perimeter_m": perimeter,
            "route_sample_spacing_m": spacing,
            "route_sample_count": len(samples),
            "maximum_off_nadir_deg": maximum_off_nadir_deg,
            "minimum_visible_sample_fraction": minimum_visible_fraction,
        },
        "c_geom": {
            "domain": "whole loop including the occluded arc (BC-BODY1-2)",
            "upper_bound_frustum_only": c_geom_upper,
            "lower_bound_with_box_occlusion": c_geom_lower,
            "arm_b_lower_bound_with_box_occlusion": arm_b_lower,
            "gap_from_saturation": 1.0 - c_geom_lower,
        },
        "visible_arc": {
            "intervals_m": intervals,
            "interval_count": len(intervals),
            "route_zero_interval_m": route_zero_interval,
            "route_zero_inside_arc": route_zero_interval is not None,
            "longest_interval_length_m": (
                max(interval["length_m"] for interval in intervals)
                if intervals
                else 0.0
            ),
            "measurement_window_m": measurement_window,
            "measurement_window_note": (
                "one Play = one trial; the window starts at route[0] (the "
                "position Configure always sets) and ends where the target "
                "first enters the occluded arc, so it is the *remaining* part "
                "of the visible arc, not its full length"
            ),
            "measurement_window_length_m": (
                None if measurement_window is None
                else measurement_window[1] - measurement_window[0]
            ),
            "sha256": interval_digest,
        },
        "occlusion_attribution": {
            "blocked_point_samples": blocked_point_samples,
            "by_instance": attribution,
            "by_canonical_name": [
                {"canonical_name": name, "blocking_point_samples": count}
                for name, count in sorted(
                    by_name.items(), key=lambda item: (-item[1], item[0])
                )
            ],
        },
        "c_quality_projection": {
            "basis": (
                "measurement-window samples that are geometrically visible; "
                "uniform route-mileage sampling makes plain statistics "
                "mileage-weighted (BC-BODY1-2)"
            ),
            "minimum_side_floor_px": MIN_SIDE_FLOOR_PX,
            "arm_a_gimbal_only": quality(window_slice(arm_a)),
            "arm_b_threshold_allocation": quality(window_slice(arm_b)),
            "arm_b_body_displacement_m": _quality(displacements),
        },
        "pre_registered_reductions": {
            "R1_route_domain": (
                "frozen scenario polyline sampled every "
                f"{spacing} m; heading is the segment direction"
            ),
            "R2_gimbal_aim": "target ground point, the zero-tracker-error limit",
            "R3_arm_a": "body held at the hover point above the anchor",
            "R4_arm_b": (
                "quasi-static: smallest displacement along the target bearing "
                f"reaching the {MARGIN_RELEASE_DEG} deg release margin, "
                "clamped by the tether sphere, then shortened in "
                f"{CORRIDOR_SHORTEN_STEP_M} m steps until the corridor is "
                "clear, else hold; ignores body and gimbal dynamics"
            ),
            "R5_occluders": (
                "779 road-audit obstacle instances as world AABBs; AABBs "
                "over-estimate blocking, road surfaces are not occluders here"
            ),
        },
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--spacing", type=float, default=ROUTE_SAMPLE_SPACING_M)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(argv)
    try:
        artifact = build_margin(arguments.spacing)
    except MarginFailure as failure:
        print(f"scene body margin FAILED: {failure}")
        return 1
    Path(arguments.output).write_text(
        json.dumps(artifact, indent=1, sort_keys=True) + "\n"
    )
    geom = artifact["c_geom"]
    arc = artifact["visible_arc"]
    quality_a = artifact["c_quality_projection"]["arm_a_gimbal_only"]
    quality_b = artifact["c_quality_projection"]["arm_b_threshold_allocation"]
    print(
        f"C_geom upper={geom['upper_bound_frustum_only']:.6f} "
        f"lower={geom['lower_bound_with_box_occlusion']:.6f} "
        f"(arm B lower={geom['arm_b_lower_bound_with_box_occlusion']:.6f}) | "
        f"visible arcs={arc['intervals_m']} "
        f"route0_in_arc={arc['route_zero_inside_arc']} "
        f"window={arc['measurement_window_m']} | "
        f"area median A={quality_a['area_px'].get('median')} "
        f"B={quality_b['area_px'].get('median')} | "
        f"centre error median A={quality_a['center_error_px'].get('median')} "
        f"B={quality_b['center_error_px'].get('median')}"
    )
    if not arc["route_zero_inside_arc"]:
        print(
            "route[0] is NOT inside the visible arc: BC-BODY1-2 requires "
            "returning to Acceptance before any collection."
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
