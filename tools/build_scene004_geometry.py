"""P1-SCENE-004 acceptance-1 geometry artifact.

Derives the coverage envelope from the **frozen scenario bytes** and gates it
against the pre-registered envelope, so the numbers a reviewer checks come
from the same file the simulator will run, not from a design note.

Gates (accepted revision 2 plus Codex round 2 binding clarifications):

* max slant range <= 32 m
* max off-nadir <= 45 deg **and** margin >= 5 deg (BC2/B2 — the clamp that
  killed SCENE-001 and SCENE-003 is a gate here, not an assumption)
* loop period in [30, 45] s
* p05 of the predicted `min(width, height)` target box >= 25 px (BC1 — a
  pose-invariant percentile, not a box-height minimum: box aspect follows
  target heading and gimbal yaw, so a height gate fails on data it should
  admit)
* at least 10 distractor sample opportunities, each fully inside the frame
  with a minimum side >= 16 px (C8/BC5)

Every derived quantity is reported **with its margin** (BC6), including on
the failing path.

The pixel prediction uses the scale measured by the Gate 0 probe over 204
real near-field samples of the same target vehicle under the same sensor
contract; the constants are recorded in the artifact so a reviewer can see
what the prediction rests on. scout-3 measures the real thing.

BC5: this tool never touches `config/detector-reanchor.models.json`. Its
16 px distractor floor is a deliberately conservative *geometry-side*
precheck and is intentionally stricter than the analyzer's own
`minimum_crop_side_px = 2`, which stays byte-identical.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
from typing import Any, Mapping, Sequence

from tools.run_detector_scouting import sha256_file
from tools.run_track_experiment import PROJECT_ROOT

WORK_ID = "P1-SCENE-004"
ARTIFACT_SCHEMA = "p1-scene-004-geometry/v1"
SCENARIO_PATH = PROJECT_ROOT / "config" / "scenario.p1-scene-004.json"
ROAD_DATA_PATH = PROJECT_ROOT / "config" / "road_data.json"
ANCHOR_CONTRACT_PATH = (
    PROJECT_ROOT / "config" / "p1-scene-004-anchor-placement.json"
)
ANCHOR_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "evidence" / "P1-SCENE-004-anchor-audit.json"
)

# Envelope gates.
MAX_SLANT_RANGE_M = 32.0
MAX_OFF_NADIR_DEG = 45.0
OFF_NADIR_MARGIN_MIN_DEG = 5.0
LOOP_PERIOD_RANGE_S = (30.0, 45.0)
MIN_SIDE_P05_MIN_PX = 25.0
DISTRACTOR_MIN_SIDE_PX = 16.0
DISTRACTOR_MIN_OPPORTUNITIES = 10

# Measured by tools/run_scene004_gate0_probe.py over 204 real near-field
# samples (docs/evidence/P1-SCENE-004-gate0-probe.json): the product of a box
# dimension and the slant range is scale-invariant to first order.
MEASURED_MIN_SIDE_RANGE_PRODUCT_P05 = 920.3
MEASURED_MIN_SIDE_RANGE_PRODUCT_MEDIAN = 1086.4
MEASURED_HEIGHT_RANGE_PRODUCT_P05 = 1653.9
MEASURED_HEIGHT_RANGE_PRODUCT_MEDIAN = 1877.2
MEASURED_SCALE_SOURCE = "docs/evidence/P1-SCENE-004-gate0-probe.json"

ROUTE_SAMPLE_SPACING_M = 0.25
DISTRACTOR_SAMPLE_HZ = 2.0


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _vector_xz(value: Mapping[str, Any]) -> tuple[float, float]:
    return float(value["x"]), float(value["z"])


def _perimeter(vertices: Sequence[tuple[float, float]]) -> float:
    return sum(
        math.dist(vertices[index], vertices[(index + 1) % len(vertices)])
        for index in range(len(vertices))
    )


def _sample_circuit(
    vertices: Sequence[tuple[float, float]],
    spacing: float,
) -> list[tuple[float, float]]:
    samples: list[tuple[float, float]] = []
    for index in range(len(vertices)):
        start = vertices[index]
        end = vertices[(index + 1) % len(vertices)]
        length = math.dist(start, end)
        steps = max(1, math.ceil(length / spacing))
        for step in range(steps):
            t = step / steps
            samples.append(
                (
                    start[0] + t * (end[0] - start[0]),
                    start[1] + t * (end[1] - start[1]),
                )
            )
    return samples


def _position_at_arc_length(
    vertices: Sequence[tuple[float, float]],
    distance: float,
) -> tuple[float, float]:
    total = _perimeter(vertices)
    remaining = distance % total
    for index in range(len(vertices)):
        start = vertices[index]
        end = vertices[(index + 1) % len(vertices)]
        length = math.dist(start, end)
        if remaining <= length:
            t = 0.0 if length == 0.0 else remaining / length
            return (
                start[0] + t * (end[0] - start[0]),
                start[1] + t * (end[1] - start[1]),
            )
        remaining -= length
    return vertices[0]


def _normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    norm = math.sqrt(sum(component * component for component in vector))
    if norm <= 0.0:
        raise ValueError("cannot normalise a zero-length vector")
    return tuple(component / norm for component in vector)  # type: ignore[return-value]


def _cross(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _dot(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> float:
    return sum(a * b for a, b in zip(left, right))


def _camera_basis(
    camera: tuple[float, float, float],
    target: tuple[float, float, float],
) -> tuple[tuple[float, float, float], ...]:
    """Unity `LookRotation(forward, Vector3.up)` basis, matching the plant."""
    forward = _normalize(
        (target[0] - camera[0], target[1] - camera[1], target[2] - camera[2])
    )
    right = _normalize(_cross((0.0, 1.0, 0.0), forward))
    up = _cross(forward, right)
    return forward, right, up


def _project(
    point: tuple[float, float, float],
    camera: tuple[float, float, float],
    basis: tuple[tuple[float, float, float], ...],
    half_width_tangent: float,
    half_height_tangent: float,
) -> tuple[float, float] | None:
    forward, right, up = basis
    delta = (
        point[0] - camera[0],
        point[1] - camera[1],
        point[2] - camera[2],
    )
    depth = _dot(delta, forward)
    if depth <= 1e-6:
        return None
    return (
        0.5 + (_dot(delta, right) / depth) / (2.0 * half_width_tangent),
        0.5 - (_dot(delta, up) / depth) / (2.0 * half_height_tangent),
    )


def _box_corners(
    center_xz: tuple[float, float],
    footprint: Mapping[str, Any],
) -> list[tuple[float, float, float]]:
    corners: list[tuple[float, float, float]] = []
    for x in (footprint["full_min_x_m"], footprint["full_max_x_m"]):
        for y in (footprint["full_min_y_m"], footprint["full_max_y_m"]):
            for z in (footprint["full_min_z_m"], footprint["full_max_z_m"]):
                corners.append(
                    (center_xz[0] + float(x), float(y), center_xz[1] + float(z))
                )
    return corners


def _percentiles(values: Sequence[float]) -> dict[str, Any]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return {"count": 0}

    def at(fraction: float) -> float:
        return ordered[int(fraction * (len(ordered) - 1))]

    return {
        "count": len(ordered),
        "min": ordered[0],
        "p05": at(0.05),
        "median": statistics.median(ordered),
        "max": ordered[-1],
    }


def build_geometry(scenario_path: Path = SCENARIO_PATH) -> dict[str, Any]:
    """Derive the envelope artifact from one frozen scenario file.

    `scenario_path` is parameterised for `P1-M2-RATE-003` Amendment DR-B
    B2.3 (difficulty configs are audited with the same machinery). The
    default is the SCENE-004 D1 baseline, so the archived D1 artifact
    regenerates byte-identically; the D1 baseline is never re-run or
    retro-edited by the difficulty audit.
    """
    scenario_path = Path(scenario_path).resolve()
    scenario = _read_json(scenario_path)
    road_data = _read_json(ROAD_DATA_PATH)
    audit = _read_json(ANCHOR_AUDIT_PATH)

    road_sha = sha256_file(ROAD_DATA_PATH)
    if scenario["road_data_sha256"] != road_sha:
        raise ValueError("scenario road_data_sha256 does not match road_data.json")
    if audit["status"] != "CLEAR":
        raise ValueError("anchor audit is not CLEAR; no anchor to derive from")

    anchor = scenario["anchor_world_m"]
    selected = audit["selected_anchor_world_m"]
    for axis in ("x", "y", "z"):
        if not math.isclose(
            float(anchor[axis]), float(selected[axis]), rel_tol=0.0, abs_tol=1e-9
        ):
            raise ValueError(
                "scenario anchor differs from the audited anchor on axis " + axis
            )

    route = scenario["target"]["route_world_m"]
    vertices = [_vector_xz(point) for point in route]
    target_plane_y = float(route[0]["y"])
    if any(not math.isclose(float(p["y"]), target_plane_y) for p in route):
        raise ValueError("route vertices must share one ground plane")

    altitude = float(scenario["drone"]["initial_altitude_m"])
    camera_y = float(anchor["y"]) + altitude
    drop = camera_y - target_plane_y
    if drop <= 0.0:
        raise ValueError("camera must be above the target plane")
    camera = (float(anchor["x"]), camera_y, float(anchor["z"]))
    anchor_xz = (float(anchor["x"]), float(anchor["z"]))

    speed = float(scenario["target"]["speed_mps"])
    perimeter = _perimeter(vertices)
    loop_period = perimeter / speed

    samples = _sample_circuit(vertices, ROUTE_SAMPLE_SPACING_M)
    horizontal = [math.dist(sample, anchor_xz) for sample in samples]
    slants = [math.hypot(value, drop) for value in horizontal]
    off_nadirs = [math.degrees(math.atan2(value, drop)) for value in horizontal]
    max_slant, min_slant = max(slants), min(slants)
    max_off_nadir = max(off_nadirs)
    off_nadir_margin = MAX_OFF_NADIR_DEG - max_off_nadir
    slant_margin = MAX_SLANT_RANGE_M - max_slant

    predicted_min_side_p05 = MEASURED_MIN_SIDE_RANGE_PRODUCT_P05 / max_slant
    predicted_min_side_median = (
        MEASURED_MIN_SIDE_RANGE_PRODUCT_MEDIAN / max_slant
    )

    # Upper-tail descriptive sub-band (accepted revision 2): the hardest 25%
    # of the circuit by slant range. Descriptive only, never gating.
    tail_threshold = sorted(slants)[int(0.75 * (len(slants) - 1))]

    sensor = scenario["sensor"]
    width, height = int(sensor["width"]), int(sensor["height"])
    vertical_fov = float(sensor["vertical_fov_deg"])
    half_height_tangent = math.tan(math.radians(vertical_fov) / 2.0)
    half_width_tangent = half_height_tangent * width / height
    horizontal_fov = 2.0 * math.degrees(math.atan(half_width_tangent))

    footprints = {
        item["canonical_name"]: item for item in road_data["obstacle_footprints"]
    }
    distractors = [
        item
        for item in scenario["scene_adjustments"]["vehicle_relocations"]
        if item.get("mark_as_distractor")
    ]
    expected = int(scenario["scene_adjustments"]["expected_distractor_count"])
    if len(distractors) != expected:
        raise ValueError(
            "expected_distractor_count does not match the marked relocations"
        )

    tick_count = max(1, int(math.floor(loop_period * DISTRACTOR_SAMPLE_HZ)))
    distractor_reports: list[dict[str, Any]] = []
    total_opportunities = 0
    for distractor in distractors:
        name = distractor["prefab_name"]
        if name not in footprints:
            raise ValueError(f"no obstacle footprint for distractor {name}")
        position = distractor["new_position_m"]
        corners = _box_corners(
            (float(position["x"]), float(position["z"])), footprints[name]
        )
        opportunities = 0
        minimum_sides: list[float] = []
        for tick in range(tick_count):
            arc = speed * tick / DISTRACTOR_SAMPLE_HZ
            target_xz = _position_at_arc_length(vertices, arc)
            target = (target_xz[0], target_plane_y, target_xz[1])
            basis = _camera_basis(camera, target)
            projected = [
                _project(
                    corner, camera, basis, half_width_tangent, half_height_tangent
                )
                for corner in corners
            ]
            if any(value is None for value in projected):
                continue
            xs = [value[0] for value in projected]  # type: ignore[index]
            ys = [value[1] for value in projected]  # type: ignore[index]
            left, right = min(xs), max(xs)
            top, bottom = min(ys), max(ys)
            if left < 0.0 or top < 0.0 or right > 1.0 or bottom > 1.0:
                continue
            side = min((right - left) * width, (bottom - top) * height)
            if side < DISTRACTOR_MIN_SIDE_PX:
                continue
            opportunities += 1
            minimum_sides.append(side)
        total_opportunities += opportunities
        distractor_reports.append(
            {
                "prefab_name": name,
                "position_world_m": {
                    "x": float(position["x"]),
                    "z": float(position["z"]),
                },
                "fully_in_frame_ticks": opportunities,
                "tick_count": tick_count,
                "minimum_side_px": _percentiles(minimum_sides),
            }
        )

    gates = {
        "max_slant_range_m": {
            "value": max_slant,
            "limit": MAX_SLANT_RANGE_M,
            "margin": slant_margin,
            "passed": max_slant <= MAX_SLANT_RANGE_M,
        },
        "max_off_nadir_deg": {
            "value": max_off_nadir,
            "limit": MAX_OFF_NADIR_DEG,
            "margin": off_nadir_margin,
            "margin_minimum": OFF_NADIR_MARGIN_MIN_DEG,
            "passed": max_off_nadir <= MAX_OFF_NADIR_DEG
            and off_nadir_margin >= OFF_NADIR_MARGIN_MIN_DEG,
        },
        "loop_period_s": {
            "value": loop_period,
            "range": list(LOOP_PERIOD_RANGE_S),
            "margin": min(
                loop_period - LOOP_PERIOD_RANGE_S[0],
                LOOP_PERIOD_RANGE_S[1] - loop_period,
            ),
            "passed": LOOP_PERIOD_RANGE_S[0]
            <= loop_period
            <= LOOP_PERIOD_RANGE_S[1],
        },
        "predicted_min_side_p05_px": {
            "value": predicted_min_side_p05,
            "limit": MIN_SIDE_P05_MIN_PX,
            "margin": predicted_min_side_p05 - MIN_SIDE_P05_MIN_PX,
            "passed": predicted_min_side_p05 >= MIN_SIDE_P05_MIN_PX,
            "note": "pose-invariant percentile (BC1); scout-3 measures it",
        },
        "distractor_opportunities": {
            "value": total_opportunities,
            "limit": DISTRACTOR_MIN_OPPORTUNITIES,
            "margin": total_opportunities - DISTRACTOR_MIN_OPPORTUNITIES,
            "passed": total_opportunities >= DISTRACTOR_MIN_OPPORTUNITIES,
        },
    }
    status = (
        "ENVELOPE_OK"
        if all(gate["passed"] for gate in gates.values())
        else "ENVELOPE_OUT_OF_BOUNDS"
    )

    return {
        "schema_version": ARTIFACT_SCHEMA,
        "work_id": WORK_ID,
        "label": "benign-coverage carrier development scenario",
        "status": status,
        "identity": {
            "scenario_path": str(scenario_path.relative_to(PROJECT_ROOT)),
            "scenario_sha256": sha256_file(scenario_path),
            "road_data_sha256": road_sha,
            "anchor_contract_sha256": sha256_file(ANCHOR_CONTRACT_PATH),
            "anchor_audit_sha256": sha256_file(ANCHOR_AUDIT_PATH),
            "scenario_id": scenario["scenario_id"],
        },
        "geometry": {
            "anchor_world_m": {
                "x": float(anchor["x"]),
                "y": float(anchor["y"]),
                "z": float(anchor["z"]),
            },
            "camera_y_m": camera_y,
            "camera_y_semantics": "anchor_support_y + initial_altitude_m",
            "target_plane_y_m": target_plane_y,
            "ground_plane_y_m_binding": target_plane_y,
            "vertical_drop_m": drop,
            "circuit_vertices_world_m": [
                {"x": vertex[0], "z": vertex[1]} for vertex in vertices
            ],
            "perimeter_m": perimeter,
            "loop_period_s": loop_period,
            "route_sample_spacing_m": ROUTE_SAMPLE_SPACING_M,
            "horizontal_distance_m": {
                "min": min(horizontal),
                "max": max(horizontal),
            },
            "slant_range_m": {"min": min_slant, "max": max_slant},
            "off_nadir_deg": {"min": min(off_nadirs), "max": max_off_nadir},
            "upper_quartile_slant_threshold_m": tail_threshold,
            "sensor": {
                "width": width,
                "height": height,
                "vertical_fov_deg": vertical_fov,
                "horizontal_fov_deg": horizontal_fov,
            },
        },
        "predicted_target_box_px": {
            "measured_scale_source": MEASURED_SCALE_SOURCE,
            "min_side_range_product_p05": MEASURED_MIN_SIDE_RANGE_PRODUCT_P05,
            "min_side_range_product_median":
                MEASURED_MIN_SIDE_RANGE_PRODUCT_MEDIAN,
            "min_side_p05_at_max_slant": predicted_min_side_p05,
            "min_side_median_at_max_slant": predicted_min_side_median,
            "height_p05_at_max_slant": MEASURED_HEIGHT_RANGE_PRODUCT_P05
            / max_slant,
            "height_median_at_min_slant": MEASURED_HEIGHT_RANGE_PRODUCT_MEDIAN
            / min_slant,
        },
        "distractors": {
            "expected_count": expected,
            "minimum_side_floor_px": DISTRACTOR_MIN_SIDE_PX,
            "sample_hz": DISTRACTOR_SAMPLE_HZ,
            "total_opportunities": total_opportunities,
            "per_distractor": distractor_reports,
            "note": (
                "geometry-side precheck only; the pinned "
                "minimum_crop_side_px = 2 in config/detector-reanchor.models.json "
                "is unchanged (BC5)"
            ),
        },
        "gates": gates,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(
            PROJECT_ROOT / "docs" / "evidence" / "P1-SCENE-004-geometry.json"
        ),
    )
    parser.add_argument("--scenario", type=Path, default=SCENARIO_PATH)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    arguments = build_argument_parser().parse_args(argv)
    artifact = build_geometry(arguments.scenario)
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=1, sort_keys=True) + "\n")
    failed = [
        name for name, gate in artifact["gates"].items() if not gate["passed"]
    ]
    print(
        f"status={artifact['status']} "
        f"period={artifact['geometry']['loop_period_s']:.4f}s "
        f"max_slant={artifact['geometry']['slant_range_m']['max']:.4f}m "
        f"max_off_nadir={artifact['geometry']['off_nadir_deg']['max']:.4f}deg "
        f"distractor_opportunities={artifact['distractors']['total_opportunities']}"
        + (f" FAILED={failed}" if failed else "")
    )


if __name__ == "__main__":
    main()
