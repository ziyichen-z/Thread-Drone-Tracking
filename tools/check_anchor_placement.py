#!/usr/bin/env python3
"""P1-M3-BODY-001 batch 1a-alpha tool 1: main-loop anchor audit checker.

BC-M34-4 (c) is the one prerequisite of the three that had never been
performed: the main circuit has no anchor placement contract at all (only
SCENE-003 and SCENE-004 have one), so ``(132, 0.2, 117)`` has never passed a
support/clearance audit. BC-BODY1-3 makes it **hard gate 1** of the batch:
FAIL means ``ANCHOR_PLACEMENT_AUDIT_FAILED``, the whole batch stops and the
matter returns to the scene-design lane.

The audit itself needs the real scene graph, so it runs Editor-side
(``TetheredTracking.Editor.P1M3BodyAnchorEvidenceGenerator``). This module is
the **independent consumer-side check** of what that query published: it
re-derives every identity hash from the frozen bytes, recomputes the road
surface support predicate from ``config/road_data.json`` alone, recomputes
each blocker's three effective-volume booleans from the published per-blocker
domain values, and recomputes the verdict. A reviewer can run it without
Unity, and it fails closed on any disagreement.

What it deliberately does **not** re-derive: prefab support footprints and
obstacle world AABBs, which exist only in the scene graph. Those are checked
for internal consistency against the published domain values instead, which
is the same division the SCENE-006 artifact checkers use.

CLI:
    python3 tools/check_anchor_placement.py [artifact.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ARTIFACT_SCHEMA = "p1-m3-body-001-anchor-audit/v1"
CONTRACT_SCHEMA = "p1-m3-body-001-anchor-placement/v1"
WORK_ID = "P1-M3-BODY-001"

DEFAULT_ARTIFACT = (
    PROJECT_ROOT / "docs" / "evidence" / "P1-M3-BODY-001-anchor-audit.json"
)
CONTRACT_PATH = (
    PROJECT_ROOT / "config" / "p1-m3-body-001-anchor-placement.json"
)
SCENARIO_PATH = PROJECT_ROOT / "config" / "scenario.default.json"
ROAD_DATA_PATH = PROJECT_ROOT / "config" / "road_data.json"

STATUS_CLEAR = "CLEAR"
STATUS_FAILED = "ANCHOR_PLACEMENT_AUDIT_FAILED"

# `P1Scene003AnchorAuditor.GeometryEpsilon`, reproduced so the predicate is
# isomorphic rather than merely similar.
GEOMETRY_EPSILON = 1e-5
# The artifact carries C# `float` values printed by `JsonUtility`; this file
# recomputes in binary64 from the same frozen inputs. Metre-scale agreement
# is required to the geometry epsilon, which is also the tolerance the audit
# itself uses on every boundary.
COMPARE_TOLERANCE = 1e-5


class CheckFailure(AssertionError):
    """Raised on the first disagreement; the caller exits non-zero."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def _close(left: float, right: float, tolerance: float = COMPARE_TOLERANCE) -> bool:
    return math.isfinite(left) and math.isfinite(right) and abs(left - right) <= tolerance


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def strictly_inside_surface(
    point: tuple[float, float],
    surface: Mapping[str, Any],
) -> bool:
    """`P1Scene003AnchorAuditor.StrictlyInsideSurface`, line for line."""
    radians = -math.radians(float(surface["yaw_deg"]))
    cosine, sine = math.cos(radians), math.sin(radians)
    delta_x = point[0] - float(surface["center_x_m"])
    delta_z = point[1] - float(surface["center_z_m"])
    local_x = cosine * delta_x - sine * delta_z
    local_z = sine * delta_x + cosine * delta_z
    return (
        abs(local_x) < float(surface["half_extent_x_m"]) - GEOMETRY_EPSILON
        and abs(local_z) < float(surface["half_extent_z_m"]) - GEOMETRY_EPSILON
    )


def road_surface_support(
    point: tuple[float, float],
    road_data: Mapping[str, Any],
) -> list[tuple[str, float]]:
    """Every road surface that strictly contains the anchor point."""
    return [
        (str(surface["id"]), float(surface["surface_y_m"]))
        for surface in road_data["surfaces"]
        if strictly_inside_surface(point, surface)
    ]


def _intervals_overlap(
    left_min: float,
    left_max: float,
    right_min: float,
    right_max: float,
) -> bool:
    """`P1Scene003AnchorAuditor.IntervalsOverlap`, line for line."""
    return (
        left_min <= right_max + GEOMETRY_EPSILON
        and left_max >= right_min - GEOMETRY_EPSILON
    )


def route_centerline_distance(
    point: tuple[float, float],
    route: Sequence[Mapping[str, Any]],
) -> float:
    """Shortest distance from the anchor to the closed route centreline."""
    best = math.inf
    count = len(route)
    for index in range(count):
        start = route[index]
        end = route[(index + 1) % count]
        start_xz = (float(start["x"]), float(start["z"]))
        end_xz = (float(end["x"]), float(end["z"]))
        delta = (end_xz[0] - start_xz[0], end_xz[1] - start_xz[1])
        length_squared = delta[0] * delta[0] + delta[1] * delta[1]
        if length_squared <= GEOMETRY_EPSILON:
            parameter = 0.0
        else:
            projection = (
                (point[0] - start_xz[0]) * delta[0]
                + (point[1] - start_xz[1]) * delta[1]
            ) / length_squared
            parameter = min(1.0, max(0.0, projection))
        closest = (
            start_xz[0] + parameter * delta[0],
            start_xz[1] + parameter * delta[1],
        )
        best = min(best, math.dist(point, closest))
    return best


def _check_identity(
    artifact: Mapping[str, Any],
    contract: Mapping[str, Any],
    scenario: Mapping[str, Any],
) -> None:
    _require(
        artifact.get("schema_version") == ARTIFACT_SCHEMA,
        f"artifact schema must be {ARTIFACT_SCHEMA}",
    )
    _require(artifact.get("work_id") == WORK_ID, f"artifact work_id must be {WORK_ID}")
    _require(
        contract.get("schema_version") == CONTRACT_SCHEMA
        and contract.get("work_id") == WORK_ID,
        "anchor placement contract identity is wrong",
    )
    _require(
        artifact.get("anchor_contract_sha256") == sha256_file(CONTRACT_PATH),
        "anchor_contract_sha256 does not match config/"
        "p1-m3-body-001-anchor-placement.json",
    )
    _require(
        artifact.get("source_scenario_sha256") == sha256_file(SCENARIO_PATH),
        "source_scenario_sha256 does not match config/scenario.default.json",
    )
    _require(
        artifact.get("source_scenario_id") == scenario["scenario_id"],
        "source_scenario_id does not match the scenario bytes",
    )
    road_sha = sha256_file(ROAD_DATA_PATH)
    _require(
        scenario["road_data_sha256"] == road_sha,
        "scenario road_data_sha256 does not match config/road_data.json",
    )
    _require(
        artifact.get("road_data_sha256") == road_sha,
        "artifact road_data_sha256 does not match config/road_data.json",
    )


def _check_geometry_inputs(
    artifact: Mapping[str, Any],
    contract: Mapping[str, Any],
    scenario: Mapping[str, Any],
) -> tuple[tuple[float, float, float], float]:
    audited = artifact["audited_anchor_world_m"]
    declared = contract["audited_anchor_world_m"]
    scenario_anchor = scenario["anchor_world_m"]
    anchor = tuple(float(audited[axis]) for axis in ("x", "y", "z"))
    for axis in ("x", "y", "z"):
        _require(
            _close(float(audited[axis]), float(declared[axis])),
            f"artifact anchor.{axis} differs from the contract",
        )
        _require(
            _close(float(audited[axis]), float(scenario_anchor[axis])),
            f"audited anchor.{axis} differs from the scenario anchor - the "
            "audit would be about a position nothing runs",
        )

    clearance = float(contract["clearance_margin_m"])
    for label, nominal_key in (
        ("anchor", "anchor_nominal_radius_m"),
        ("hover", "hover_nominal_radius_m"),
        ("corridor", "corridor_nominal_radius_m"),
    ):
        expected = float(contract[nominal_key]) + clearance
        _require(
            _close(float(artifact[f"{label}_effective_radius_m"]), expected),
            f"{label}_effective_radius_m is not nominal + clearance margin",
        )

    hover_offset = float(contract["hover_offset_y_m"])
    hover = artifact["hover_point_world_m"]
    _require(
        _close(float(hover["x"]), anchor[0])
        and _close(float(hover["z"]), anchor[2])
        and _close(float(hover["y"]), anchor[1] + hover_offset),
        "hover_point_world_m is not the anchor raised by hover_offset_y_m",
    )
    return anchor, hover_offset


def _check_support(
    artifact: Mapping[str, Any],
    contract: Mapping[str, Any],
    road_data: Mapping[str, Any],
    anchor: tuple[float, float, float],
) -> None:
    published = artifact.get("support_matches") or []
    published_road = sorted(
        (str(item["id"]), float(item["surface_y_m"]))
        for item in published
        if item.get("source") == "road_surface"
    )
    recomputed = sorted(road_surface_support((anchor[0], anchor[2]), road_data))
    _require(
        [name for name, _ in published_road] == [name for name, _ in recomputed],
        "published road-surface support does not match the recomputation from "
        f"road_data.json: {published_road} vs {recomputed}",
    )
    for (_, published_y), (name, recomputed_y) in zip(published_road, recomputed):
        _require(
            _close(published_y, recomputed_y),
            f"support surface elevation for {name} disagrees with road_data.json",
        )

    status = artifact.get("support_status")
    _require(
        status in {"PASS", "FAIL", "NOT_EVALUATED"},
        f"unknown support_status {status!r}",
    )
    if status != "PASS":
        return

    _require(bool(published), "support_status is PASS with no support match")
    elevations = [float(item["surface_y_m"]) for item in published]
    minimum, maximum = min(elevations), max(elevations)
    _require(
        maximum - minimum <= GEOMETRY_EPSILON,
        "support surfaces disagree on elevation but support_status is PASS",
    )
    _require(
        _close(float(artifact["support_surface_y_m"]), minimum),
        "support_surface_y_m is not the minimum published support elevation",
    )
    error = anchor[1] - minimum
    _require(
        _close(float(artifact["support_height_error_m"]), error),
        "support_height_error_m is not anchor y minus the support elevation",
    )
    tolerance = float(contract["support_height_tolerance_m"])
    _require(
        abs(error) <= tolerance + GEOMETRY_EPSILON,
        f"support height error {error} exceeds the frozen tolerance {tolerance}",
    )


def _check_blockers(
    artifact: Mapping[str, Any],
    contract: Mapping[str, Any],
    anchor: tuple[float, float, float],
    hover_offset: float,
) -> None:
    blockers = artifact.get("blockers") or []
    _require(
        int(artifact.get("blocker_count", -1)) == len(blockers),
        "blocker_count does not match the published blocker list",
    )
    names = [str(item["scene_object_name"]) for item in blockers]
    _require(names == sorted(names), "blockers are not in ordinal name order")

    if artifact.get("support_status") != "PASS":
        return
    ground = float(artifact["support_surface_y_m"])
    hover_y = anchor[1] + hover_offset
    clearance = float(contract["clearance_margin_m"])
    anchor_radius = float(artifact["anchor_effective_radius_m"])
    hover_radius = float(artifact["hover_effective_radius_m"])
    corridor_radius = float(artifact["corridor_effective_radius_m"])

    for blocker in blockers:
        reason = str(blocker.get("reason"))
        if reason != "CLEARANCE_INTERSECTION":
            _require(
                reason in {"UNCLASSIFIED_OBSTACLE", "UNSUPPORTED_OBSTACLE_TRS"},
                f"unknown blocker reason {reason!r}",
            )
            continue
        horizontal = float(blocker["horizontal_distance_m"])
        obstacle_min = float(blocker["obstacle_min_y_m"])
        obstacle_max = float(blocker["obstacle_max_y_m"])
        expected_anchor = horizontal <= anchor_radius + GEOMETRY_EPSILON and (
            _intervals_overlap(obstacle_min, obstacle_max, ground, ground + clearance)
        )
        expected_corridor = horizontal <= corridor_radius + GEOMETRY_EPSILON and (
            _intervals_overlap(obstacle_min, obstacle_max, ground, hover_y)
        )
        if hover_y < obstacle_min:
            vertical = obstacle_min - hover_y
        elif hover_y > obstacle_max:
            vertical = hover_y - obstacle_max
        else:
            vertical = 0.0
        expected_hover = (
            horizontal * horizontal + vertical * vertical
            <= hover_radius * hover_radius + GEOMETRY_EPSILON
        )
        name = blocker["scene_object_name"]
        _require(
            bool(blocker["anchor_cylinder"]) == expected_anchor
            and bool(blocker["corridor_cylinder"]) == expected_corridor
            and bool(blocker["hover_sphere"]) == expected_hover,
            f"effective-volume booleans for {name} do not follow from its own "
            "published distances and the frozen radii",
        )
        _require(
            expected_anchor or expected_corridor or expected_hover,
            f"{name} is reported as a blocker but clears all three volumes",
        )


def _check_verdict(artifact: Mapping[str, Any]) -> None:
    status = artifact.get("status")
    _require(
        status in {STATUS_CLEAR, STATUS_FAILED},
        f"unknown audit status {status!r}",
    )
    support_pass = artifact.get("support_status") == "PASS"
    clearance_pass = artifact.get("clearance_status") == "PASS"
    blocker_free = int(artifact.get("blocker_count", 0)) == 0
    should_be_clear = support_pass and clearance_pass and blocker_free
    _require(
        (status == STATUS_CLEAR) == should_be_clear,
        "status does not follow from support_status, clearance_status and "
        "blocker_count",
    )
    reason = artifact.get("rejection_reason") or ""
    if status == STATUS_CLEAR:
        _require(reason == "", "a CLEAR audit must carry no rejection reason")
    else:
        _require(reason != "", "a failed audit must name its rejection reason")


def _check_route_diagnostic(
    artifact: Mapping[str, Any],
    scenario: Mapping[str, Any],
    anchor: tuple[float, float, float],
) -> None:
    route = scenario["target"]["route_world_m"]
    expected = route_centerline_distance((anchor[0], anchor[2]), route)
    _require(
        _close(float(artifact["route_centerline_distance_m"]), expected),
        "route_centerline_distance_m does not match the frozen route",
    )
    corridor = scenario["scene_adjustments"]["route_corridor"]
    expected_half_width = float(corridor["target_half_width_m"]) + float(
        corridor["clearance_margin_m"]
    )
    _require(
        _close(float(artifact["route_corridor_half_width_m"]), expected_half_width),
        "route_corridor_half_width_m does not match the frozen scenario",
    )


def check_artifact(path: Path = DEFAULT_ARTIFACT) -> dict[str, Any]:
    """Verify one anchor audit artifact; raise `CheckFailure` on any drift."""
    artifact = _load(path)
    contract = _load(CONTRACT_PATH)
    scenario = _load(SCENARIO_PATH)
    road_data = _load(ROAD_DATA_PATH)

    _check_identity(artifact, contract, scenario)
    anchor, hover_offset = _check_geometry_inputs(artifact, contract, scenario)
    _check_support(artifact, contract, road_data, anchor)
    _check_blockers(artifact, contract, anchor, hover_offset)
    _check_verdict(artifact)
    _check_route_diagnostic(artifact, scenario, anchor)
    return artifact


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", nargs="?", type=Path, default=DEFAULT_ARTIFACT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(argv)
    try:
        artifact = check_artifact(arguments.artifact)
    except CheckFailure as failure:
        print(f"anchor audit check FAILED: {failure}")
        return 1
    print(
        f"status={artifact['status']} "
        f"support={artifact['support_status']} "
        f"clearance={artifact['clearance_status']} "
        f"support_y={artifact['support_surface_y_m']} "
        f"height_error={artifact['support_height_error_m']} "
        f"roots={artifact['scene_root_count']} "
        f"audited_obstacles={artifact['audited_obstacle_count']} "
        f"blockers={artifact['blocker_count']} "
        f"route_centreline={artifact['route_centerline_distance_m']}m "
        f"(diagnostic, corridor half width "
        f"{artifact['route_corridor_half_width_m']}m)"
    )
    return 0 if artifact["status"] == STATUS_CLEAR else 2


if __name__ == "__main__":
    sys.exit(main())
