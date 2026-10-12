"""P1-ENG-FRAME-001 Part P (P3): offline kinematic replay and Play read-outs.

Proposal section 3.9 / 3.10, zero consumption:

* **Replay** (default mode). The real ``StandoffBodyPlanner`` (built by
  ``controller.track_loop.build_standoff_planner``), the real
  ``ThresholdBodyPlanner`` / ``HoldBodyPlanner`` and the real
  ``WorldEstimateFilter`` (frozen BODY-001 priors) are driven around the
  default route for two loops. The plant is a float32 mirror of
  ``TetheredDronePlant.Step`` in the matching tether mode (pinned to the
  Edit Mode golden vectors, AC-19). The gimbal points ideally at the target
  (45 deg limit clamp, ``TetheredGimbal`` geometry); the target box is the
  red car's oriented box (2.0 x 1.55 x 4.0 m) projected through the frame
  metadata pinhole model. Ground truth is used **only here**, offline, to
  synthesise observations and read-outs; it never reaches a runtime path.
  The pre-registered grid {C1, C2, C3, threshold, hold} x {25 m, 15 m} x
  {untethered, tethered} x {E0, E1, E2} is run with fixed seeds, the
  pre-registered rule selects the candidate (25 m / untethered / E1, second
  loop), and the evidence is written to
  ``docs/evidence/P1-ENG-FRAME-001-replay.{json,md}``. Re-running produces
  byte-identical files (``--check`` verifies that).
* **Play analysis** (``--analyze-run``). The same read-out functions applied
  to a Play run directory, the evaluator's offline truth sidecar and
  ``metrics.json`` (R-1 ... R-7 and the AC-23 safety read-outs; no gates).
  The ``--scenario`` file is bound to the run manifest's scenario sha256
  values and refused on any mismatch (section 3.11 entry 8).

There is no scenario default: the two scenario files of the grid are fixed
below (proposal section 3.11, entry 8).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller.body_planner import (  # noqa: E402
    BodyCommand,
    BodyPlanner,
    HoldBodyPlanner,
    PlatformState,
    ThresholdBodyPlanner,
    load_corridor_prisms,
)
from controller.geolocate import GeometryRejected  # noqa: E402
from controller.scenario_tether import (  # noqa: E402
    parse_tether_settings,
    safety_bounds as scenario_safety_bounds,
)
from controller.standoff_planner import (  # noqa: E402
    MAIN_TAGS,
    MODIFIERS,
    StandoffFixed,
    StandoffParams,
    split_reason,
)
from controller.trackers import clip_box_norm  # noqa: E402
from controller.track_loop import (  # noqa: E402
    _estimator_from_body_config,
    build_standoff_planner,
)

SCHEMA = "p1-eng-frame-001-replay/v1"
WORK_ID = "P1-ENG-FRAME-001"

UNTETHERED_SCENARIO = "config/scenario.untethered.json"
TETHERED_SCENARIO = "config/scenario.default.json"
BODY_001_CONFIG = "config/p1-m3-body-001.json"
EVIDENCE_JSON = "docs/evidence/P1-ENG-FRAME-001-replay.json"
EVIDENCE_MD = "docs/evidence/P1-ENG-FRAME-001-replay.md"

#: Proposal section 3.9, pre-registered candidates.
CANDIDATES: dict[str, dict[str, float]] = {
    "C1": {"d_star_m": 6.0, "band_w_m": 3.0, "t_lead_s": 2.0, "k_p_per_s": 0.5},
    "C2": {"d_star_m": 9.0, "band_w_m": 3.0, "t_lead_s": 2.0, "k_p_per_s": 0.5},
    "C3": {"d_star_m": 12.0, "band_w_m": 4.0, "t_lead_s": 2.5, "k_p_per_s": 0.4},
}
#: Proposal section 3.7 ``fixed`` block.
FIXED: dict[str, float] = {
    "v_max_mps": 4.0,
    "target_velocity_clamp_mps": 4.0,
    "d_plaus_m": 65.0,
    "obstacle_pad_m": 2.1,
    "corridor_pad_m": 1.0,
    "shorten_step_m": 0.05,
    "min_residual_speed_mps": 0.05,
}
POLICIES: tuple[str, ...] = ("C1", "C2", "C3", "threshold", "hold")
ALTITUDES_M: tuple[float, ...] = (25.0, 15.0)
TETHER_MODES: tuple[str, ...] = ("untethered", "tethered")
NOISE_CONDITIONS: tuple[str, ...] = ("E0", "E1", "E2")

#: Pre-registered selection rule (proposal section 3.9).
SELECTION_CELL = {"altitude_m": 25.0, "tether": "untethered", "noise": "E1", "window": "loop2"}
H1_MAX_GIMBAL_SATURATED_FRACTION = 0.005
H2_MIN_SHORT_SIDE_PX_P10 = 24.0
H3_MAX_BOUNDARY_OBSTACLE_MODIFIER_FRACTION = 0.01
H4_MAX_START_STOPS_PER_LOOP = 5
H5_MAX_STATIONARY_FRACTION = 0.10
TIE_PATH_RELATIVE = 0.03
STOP_SPEED_MPS = 0.2
GO_SPEED_MPS = 1.0
CENTER_ERROR_GATE_PX = 64.0

#: Red car (``TargetVisualFactory``): body 2 x 1 x 4 m + roof, local AABB
#: x [-1, 1], y [0, 1.55], z [-2, 2].
CAR_HALF_WIDTH_M = 1.0
CAR_HEIGHT_M = 1.55
CAR_HALF_LENGTH_M = 2.0
CAR_WIDTH_M = 2.0
#: ``TetheredGimbal`` reports saturation only above limit + 0.1 deg.
GIMBAL_SATURATION_DEADBAND_DEG = 0.1
PLANT_SUBSTEPS_PER_FRAME = 10
#: "Beyond the 35 m cable" read-out (AC-23): 3-D distance to the anchor
#: above 35 m plus 1 mm, so float32 positions on the sphere are not counted.
BEYOND_TETHER_M = 35.0 + 1e-3
BOUNDARY_MODIFIERS = tuple(MODIFIERS)


# ---------------------------------------------------------------------------
# float32 mirror of TetheredDronePlant (AC-19)
# ---------------------------------------------------------------------------

_FLOAT32 = struct.Struct("<f")


def r32(value: float) -> float:
    """Round to IEEE single precision (a store to a C# ``float``)."""
    return _FLOAT32.unpack(_FLOAT32.pack(value))[0]


# Rounding model (K2补跑, verified bit-exact against the Unity Edit Mode plant
# on every step of the nine golden sequences): Unity's Mono runtime evaluates
# ``float`` expression temporaries in double precision and rounds to float32
# only where a value is stored -- a ``float`` local, field, parameter, return
# value or ``Vector2``/``Vector3`` constructor argument. Python floats are
# IEEE doubles, so each C# expression below is written as one double
# expression wrapped in a single ``r32`` at its store.


#: ``Vector2.kEpsilon`` (0.00001F).
VECTOR2_EPSILON = r32(0.00001)


def _sqrt32(value: float) -> float:
    # C# ``(float)Math.Sqrt(x)`` / ``Mathf.Sqrt``: double sqrt, cast back.
    return r32(math.sqrt(value))


def _sqr_mag3(v: Sequence[float]) -> float:
    # ``float sqdist = x * x + y * y + z * z`` / ``Vector3.sqrMagnitude``.
    return r32(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def _magnitude3(v: Sequence[float]) -> float:
    # ``Vector3.magnitude``: ``(float)Math.Sqrt(x * x + y * y + z * z)``.
    return r32(math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]))


def _magnitude2(x: float, y: float) -> float:
    # ``Vector2.magnitude``: ``(float)Math.Sqrt(x * x + y * y)``.
    return r32(math.sqrt(x * x + y * y))


def _clamp32(value: float, low: float, high: float) -> float:
    # ``Mathf.Clamp``.
    if value < low:
        return low
    if value > high:
        return high
    return value


def clamp_magnitude3(v: Sequence[float], max_length: float) -> tuple[float, float, float]:
    """``Vector3.ClampMagnitude``."""
    sqrmag = _sqr_mag3(v)
    if sqrmag > max_length * max_length:
        mag = _sqrt32(sqrmag)
        # Unity keeps the normalised components in float locals.
        normalized = (r32(v[0] / mag), r32(v[1] / mag), r32(v[2] / mag))
        return (
            r32(normalized[0] * max_length),
            r32(normalized[1] * max_length),
            r32(normalized[2] * max_length),
        )
    return (v[0], v[1], v[2])


def move_towards3(
    current: Sequence[float], target: Sequence[float], max_delta: float
) -> tuple[float, float, float]:
    """``Vector3.MoveTowards``."""
    to = (
        r32(target[0] - current[0]),
        r32(target[1] - current[1]),
        r32(target[2] - current[2]),
    )
    sqdist = _sqr_mag3(to)
    if sqdist == 0.0 or (max_delta >= 0.0 and sqdist <= max_delta * max_delta):
        return (target[0], target[1], target[2])
    dist = _sqrt32(sqdist)
    return (
        r32(current[0] + to[0] / dist * max_delta),
        r32(current[1] + to[1] / dist * max_delta),
        r32(current[2] + to[2] / dist * max_delta),
    )


class UnityPlantMirror:
    """Term-for-term float32 mirror of ``TetheredDronePlant`` (Part T).

    Tether on: velocity/acceleration clamps, cable sphere clamp and cable
    altitude cap (AC-2 vectors). Tether off: velocity/acceleration clamps,
    altitude band only, geofence rectangle (AC-4 vectors). A configured
    geofence also applies with the tether on. Yaw is not mirrored (it does
    not affect position).
    """

    def __init__(
        self,
        *,
        anchor: Sequence[float],
        tether_length: float,
        minimum_altitude: float,
        maximum_altitude: float,
        maximum_speed: float,
        maximum_acceleration: float,
        position: Sequence[float],
        tether_enabled: bool = True,
        geofence: Sequence[float] | None = None,
    ):
        self.anchor = tuple(r32(value) for value in anchor)
        self.tether_length = r32(tether_length)
        self.minimum_altitude = r32(minimum_altitude)
        self.maximum_altitude = r32(maximum_altitude)
        self.maximum_speed = r32(maximum_speed)
        self.maximum_acceleration = r32(maximum_acceleration)
        self.position = tuple(r32(value) for value in position)
        self.tether_enabled = bool(tether_enabled)
        self.geofence = None if geofence is None else tuple(r32(v) for v in geofence)
        self.commanded = (0.0, 0.0, 0.0)
        self.applied = (0.0, 0.0, 0.0)
        self.tether_saturated = False

    def set_velocity(self, velocity: Sequence[float]) -> None:
        self.commanded = clamp_magnitude3(
            tuple(r32(component) for component in velocity), self.maximum_speed
        )

    def hold(self) -> None:
        self.commanded = (0.0, 0.0, 0.0)

    def step(self, delta_time: float) -> None:
        dt = r32(delta_time)
        self.applied = move_towards3(
            self.applied, self.commanded, r32(self.maximum_acceleration * dt)
        )
        nxt = tuple(r32(self.position[i] + r32(self.applied[i] * dt)) for i in range(3))
        rel = tuple(r32(nxt[i] - self.anchor[i]) for i in range(3))
        if self.tether_enabled:
            self.tether_saturated = _magnitude3(rel) > self.tether_length
            vertical = _clamp32(rel[1], self.minimum_altitude, self.maximum_altitude)
            vertical = vertical if vertical < self.tether_length else self.tether_length
            hx, hz = rel[0], rel[2]
            # ``Mathf.Max(0f, L * L - v * v)``: one store at the parameter.
            inner = r32(self.tether_length * self.tether_length - vertical * vertical)
            maximum_horizontal = _sqrt32(0.0 if 0.0 > inner else inner)
            magnitude = _magnitude2(hx, hz)
            if magnitude > maximum_horizontal:
                if magnitude > VECTOR2_EPSILON:
                    nx, nz = r32(hx / magnitude), r32(hz / magnitude)
                else:
                    nx, nz = 0.0, 0.0
                hx, hz = r32(nx * maximum_horizontal), r32(nz * maximum_horizontal)
                self.tether_saturated = True
            nxt = (
                r32(self.anchor[0] + hx),
                r32(self.anchor[1] + vertical),
                r32(self.anchor[2] + hz),
            )
        else:
            self.tether_saturated = False
            vertical = _clamp32(rel[1], self.minimum_altitude, self.maximum_altitude)
            nxt = (
                r32(self.anchor[0] + rel[0]),
                r32(self.anchor[1] + vertical),
                r32(self.anchor[2] + rel[2]),
            )
        if self.geofence is not None:
            min_x, max_x, min_z, max_z = self.geofence
            nxt = (_clamp32(nxt[0], min_x, max_x), nxt[1], _clamp32(nxt[2], min_z, max_z))
        self.position = nxt


class XorShift32:
    """Same generator as the Edit Mode golden-vector tests."""

    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFF

    def next(self) -> int:
        x = self.state
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        self.state = x & 0xFFFFFFFF
        return self.state

    def next_unit(self) -> float:
        return (self.next() >> 8) * (1.0 / 16777216.0)


def random_plant_commands(seed: int, steps: int) -> list[tuple[float, float, float] | None]:
    """The seeded held-segment command list of the Edit Mode tests."""
    rng = XorShift32(seed)
    commands: list[tuple[float, float, float] | None] = []
    while len(commands) < steps:
        draw = rng.next_unit()
        command = None
        if not draw < r32(0.15):
            vx = r32(rng.next_unit() * 12.0 - 6.0)
            vy = r32(rng.next_unit() * 6.0 - 3.0)
            vz = r32(rng.next_unit() * 12.0 - 6.0)
            command = (vx, vy, vz)
        duration = 10 + int(rng.next_unit() * 50.0)
        for _ in range(duration):
            if len(commands) >= steps:
                break
            commands.append(command)
    return commands


# ---------------------------------------------------------------------------
# Shared read-out functions (replay and Play analysis use the same code)
# ---------------------------------------------------------------------------


def percentile(values: Sequence[float], fraction: float) -> float | None:
    """Linear-interpolated percentile; ``None`` for an empty sample."""
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    position = fraction * (len(ordered) - 1)
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[int(position)]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def start_stop_count(speeds: Sequence[float]) -> int:
    """H4: body speed first < 0.2 m/s, later > 1.0 m/s counts once."""
    if not speeds:
        return 0
    count = 0
    stopped = speeds[0] < STOP_SPEED_MPS
    for speed in speeds[1:]:
        if speed < STOP_SPEED_MPS:
            stopped = True
        elif stopped and speed > GO_SPEED_MPS:
            count += 1
            stopped = False
    return count


def stationary_fraction(speeds: Sequence[float]) -> float | None:
    """H5: share of samples with the body below 0.2 m/s (target moving)."""
    if not speeds:
        return None
    return sum(1 for speed in speeds if speed < STOP_SPEED_MPS) / len(speeds)


def path_length_xz(points: Sequence[Sequence[float]]) -> float:
    total = 0.0
    for start, end in zip(points, points[1:]):
        total += math.hypot(end[0] - start[0], end[2] - start[2])
    return total


def reason_read_outs(reasons: Sequence[str]) -> dict[str, Any]:
    """R-6: main-tag and modifier shares over decisions with a planner reason."""
    main_counts = {tag: 0 for tag in MAIN_TAGS}
    modifier_counts = {tag: 0 for tag in MODIFIERS}
    other: dict[str, int] = {}
    with_boundary = 0
    for reason in reasons:
        try:
            main, modifiers = split_reason(reason)
        except ValueError:
            other[reason] = other.get(reason, 0) + 1
            continue
        main_counts[main] += 1
        for tag in modifiers:
            modifier_counts[tag] += 1
        if any(tag in BOUNDARY_MODIFIERS for tag in modifiers):
            with_boundary += 1
    total = len(reasons)

    def share(count: int) -> float | None:
        return count / total if total else None

    return {
        "decisions": total,
        "main_fraction": {tag: share(count) for tag, count in main_counts.items()},
        "modifier_fraction": {tag: share(count) for tag, count in modifier_counts.items()},
        "boundary_obstacle_modifier_fraction": share(with_boundary),
        "other_reason_counts": dict(sorted(other.items())),
    }


def short_side_px(slant_range_m: float, fy_px: float) -> float:
    """R-5 estimate: 2.0 m car width at the slant range (proposal 8.1)."""
    return CAR_WIDTH_M * fy_px / slant_range_m


def summarize_window(samples: Sequence[Mapping[str, Any]], fy_px: float) -> dict[str, Any]:
    """R-1 ... R-6 over one window of per-frame samples.

    Each sample carries ``body`` (x, y, z), ``target`` (x, y, z, ground
    reference), ``body_speed_mps``, ``gimbal_saturated``,
    ``tether_saturated``, ``center_error_px`` (or ``None``), ``slant_range_m``
    and ``reason`` (or ``None`` when no planner decision was taken).
    """
    speeds = [float(s["body_speed_mps"]) for s in samples]
    errors = [float(s["center_error_px"]) for s in samples if s["center_error_px"] is not None]
    distances = [
        math.hypot(s["body"][0] - s["target"][0], s["body"][2] - s["target"][2])
        for s in samples
    ]
    slants = [float(s["slant_range_m"]) for s in samples]
    sides = [short_side_px(slant, fy_px) for slant in slants]
    reasons = [s["reason"] for s in samples if s.get("reason") is not None]
    n = len(samples)
    return {
        "frames": n,
        "R1_center_error_px": {
            "p50": percentile(errors, 0.5),
            "p90": percentile(errors, 0.9),
            "within_64px_fraction": (
                sum(1 for e in errors if e <= CENTER_ERROR_GATE_PX) / len(errors)
                if errors
                else None
            ),
            "frames_with_value": len(errors),
        },
        "R2_gimbal_saturated_fraction": (
            sum(1 for s in samples if s["gimbal_saturated"]) / n if n else None
        ),
        "R3_follow_distance_m": {
            "p50": percentile(distances, 0.5),
            "p90": percentile(distances, 0.9),
            "max": max(distances) if distances else None,
        },
        "R4_body_motion": {
            "path_length_m": path_length_xz([s["body"] for s in samples]),
            "start_stop_count": start_stop_count(speeds),
            "stationary_fraction": stationary_fraction(speeds),
        },
        "R5_range": {
            "slant_range_m_p10": percentile(slants, 0.1),
            "slant_range_m_p50": percentile(slants, 0.5),
            "short_side_px_p10": percentile(sides, 0.1),
            "short_side_px_p50": percentile(sides, 0.5),
        },
        "R6_reasons": reason_read_outs(reasons),
        "tether_saturated_frames": sum(1 for s in samples if s["tether_saturated"]),
    }


# ---------------------------------------------------------------------------
# Geometry: route, gimbal, projection
# ---------------------------------------------------------------------------


class ClosedRoute:
    def __init__(self, points: Sequence[Sequence[float]], speed_mps: float):
        self.points = [tuple(float(c) for c in p) for p in points]
        self.speed_mps = float(speed_mps)
        self.lengths = []
        for start, end in zip(self.points, self.points[1:] + self.points[:1]):
            self.lengths.append(math.dist(start, end))
        self.perimeter_m = sum(self.lengths)

    @property
    def loop_duration_s(self) -> float:
        return self.perimeter_m / self.speed_mps

    def sample(self, time_s: float) -> tuple[tuple[float, float, float], float]:
        """Position and heading (rad, Unity yaw) at ``time_s``."""
        s = (self.speed_mps * time_s) % self.perimeter_m
        for index, length in enumerate(self.lengths):
            if s <= length or index == len(self.lengths) - 1:
                start = self.points[index]
                end = self.points[(index + 1) % len(self.points)]
                fraction = min(1.0, s / length) if length > 0 else 0.0
                position = tuple(start[a] + (end[a] - start[a]) * fraction for a in range(3))
                heading = math.atan2(end[0] - start[0], end[2] - start[2])
                return position, heading  # type: ignore[return-value]
            s -= length
        raise AssertionError("unreachable")


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _rotate(vector: Sequence[float], axis_angle: Sequence[float]) -> tuple[float, float, float]:
    angle = math.sqrt(_dot(axis_angle, axis_angle))
    if angle <= 0.0:
        return tuple(vector)  # type: ignore[return-value]
    k = tuple(component / angle for component in axis_angle)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    cross = (
        k[1] * vector[2] - k[2] * vector[1],
        k[2] * vector[0] - k[0] * vector[2],
        k[0] * vector[1] - k[1] * vector[0],
    )
    kv = _dot(k, vector)
    return tuple(
        vector[i] * cos_a + cross[i] * sin_a + k[i] * kv * (1.0 - cos_a) for i in range(3)
    )  # type: ignore[return-value]


def gimbal_pose(
    camera: Sequence[float],
    aim: Sequence[float],
    maximum_off_nadir_deg: float,
    previous_yaw_deg: float,
) -> tuple[dict[str, tuple[float, float, float]], bool, float]:
    """``TetheredGimbal`` desired pose (ideal slew), Unity Euler(90-a, yaw, 0)."""
    delta = tuple(aim[i] - camera[i] for i in range(3))
    horizontal = math.hypot(delta[0], delta[2])
    height = max(0.1, -delta[1])
    requested = math.degrees(math.atan2(horizontal, height))
    applied = min(requested, maximum_off_nadir_deg)
    saturated = requested > maximum_off_nadir_deg + GIMBAL_SATURATION_DEADBAND_DEG
    yaw = math.degrees(math.atan2(delta[0], delta[2])) if horizontal > 0.001 else previous_yaw_deg
    theta = math.radians(applied)
    psi = math.radians(yaw)
    basis = {
        "forward": (math.sin(psi) * math.sin(theta), -math.cos(theta), math.cos(psi) * math.sin(theta)),
        "right": (math.cos(psi), 0.0, -math.sin(psi)),
        "up": (math.sin(psi) * math.cos(theta), math.sin(theta), math.cos(psi) * math.cos(theta)),
    }
    return basis, saturated, yaw


def project_point(
    point: Sequence[float],
    camera: Sequence[float],
    basis: Mapping[str, Sequence[float]],
    intrinsics: Mapping[str, float],
) -> tuple[float, float] | None:
    d = tuple(point[i] - camera[i] for i in range(3))
    depth = _dot(d, basis["forward"])
    if depth <= 1e-6:
        return None
    u = intrinsics["cx"] + intrinsics["fx"] * _dot(d, basis["right"]) / depth
    v = intrinsics["cy"] - intrinsics["fy"] * _dot(d, basis["up"]) / depth
    return u, v


def car_corners(position: Sequence[float], heading: float) -> list[tuple[float, float, float]]:
    forward = (math.sin(heading), 0.0, math.cos(heading))
    right = (math.cos(heading), 0.0, -math.sin(heading))
    corners = []
    for side in (-CAR_HALF_WIDTH_M, CAR_HALF_WIDTH_M):
        for height in (0.0, CAR_HEIGHT_M):
            for length in (-CAR_HALF_LENGTH_M, CAR_HALF_LENGTH_M):
                corners.append(
                    tuple(
                        position[i] + right[i] * side + forward[i] * length + (height if i == 1 else 0.0)
                        for i in range(3)
                    )  # type: ignore[arg-type]
                )
    return corners


def car_box_px(
    position: Sequence[float],
    heading: float,
    camera: Sequence[float],
    basis: Mapping[str, Sequence[float]],
    intrinsics: Mapping[str, float],
    width: int,
    height: int,
) -> tuple[float, float, float, float] | None:
    """Clipped pixel box ``(u0, v0, u1, v1)`` of the car, or ``None``."""
    projected = []
    for corner in car_corners(position, heading):
        uv = project_point(corner, camera, basis, intrinsics)
        if uv is None:
            return None
        projected.append(uv)
    u0 = max(0.0, min(u for u, _ in projected))
    u1 = min(float(width), max(u for u, _ in projected))
    v0 = max(0.0, min(v for _, v in projected))
    v1 = min(float(height), max(v for _, v in projected))
    if u1 <= u0 or v1 <= v0:
        return None
    return u0, v0, u1, v1


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------


def _load(path: str) -> dict[str, Any]:
    return json.loads((PROJECT_ROOT / path).read_text(encoding="utf-8"))


def _sha256(path: str) -> str:
    return hashlib.sha256((PROJECT_ROOT / path).read_bytes()).hexdigest()


def _seed(cell_id: str) -> int:
    return int(hashlib.sha256(f"{WORK_ID}|replay|{cell_id}".encode()).hexdigest()[:16], 16)


def intrinsics_for(scenario: Mapping[str, Any]) -> tuple[dict[str, float], int, int]:
    sensor = scenario["sensor"]
    width = int(sensor["width"])
    height = int(sensor["height"])
    focal = 0.5 * height / math.tan(math.radians(float(sensor["vertical_fov_deg"])) * 0.5)
    return {"fx": focal, "fy": focal, "cx": width * 0.5, "cy": height * 0.5}, width, height


def build_planner(
    policy: str,
    scenario: Mapping[str, Any],
    body_config: Mapping[str, Any],
) -> BodyPlanner:
    if policy in CANDIDATES:
        return build_standoff_planner(
            body_config,
            scenario,
            StandoffParams(**CANDIDATES[policy]),
            StandoffFixed(**FIXED),
            project_root=PROJECT_ROOT,
        )
    expires = float(body_config["command"]["expires_after_s"])
    if policy == "hold":
        return HoldBodyPlanner(expires_after_s=expires)
    if policy == "threshold":
        settings = parse_tether_settings(scenario)
        corridor = body_config["corridor"]
        prisms = None
        radius = None
        if settings.tether_enabled:
            prisms = load_corridor_prisms(PROJECT_ROOT / corridor["artifact_path"])
            radius = float(corridor["corridor_nominal_radius_m"]) + float(
                corridor["clearance_margin_m"]
            )
        policy_values = body_config["policy"]
        return ThresholdBodyPlanner(
            margin_trigger_deg=float(policy_values["margin_trigger_deg"]),
            margin_release_deg=float(policy_values["margin_release_deg"]),
            v_cmd_mps=float(policy_values["v_cmd_mps"]),
            expires_after_s=expires,
            maximum_off_nadir_deg=float(scenario["gimbal"]["maximum_off_nadir_deg"]),
            anchor_world_m=settings.anchor_world_m,
            corridor_prisms=prisms,
            corridor_radius_m=radius,
        )
    raise ValueError(f"unknown policy {policy!r}")


def _inside_inflated_prism(point: Sequence[float], prisms, pad: float) -> bool:
    for prism in prisms:
        if all(prism[a] - pad < point[a] < prism[a + 3] + pad for a in range(3)):
            return True
    return False


def simulate_cell(
    policy: str,
    altitude_m: float,
    tether: str,
    noise: str,
    *,
    duration_s: float | None = None,
    scenarios: Mapping[str, Mapping[str, Any]] | None = None,
    body_config: Mapping[str, Any] | None = None,
    prisms=None,
) -> dict[str, Any]:
    """Run one grid cell; returns the per-frame samples and the read-outs."""
    scenarios = scenarios or {
        "untethered": _load(UNTETHERED_SCENARIO),
        "tethered": _load(TETHERED_SCENARIO),
    }
    body_config = body_config or _load(BODY_001_CONFIG)
    if prisms is None:
        prisms = load_corridor_prisms(PROJECT_ROOT / body_config["corridor"]["artifact_path"])
    scenario = scenarios[tether]
    settings = parse_tether_settings(scenario)
    cell_id = f"{policy}|{altitude_m:g}|{tether}|{noise}"
    rng = random.Random(_seed(cell_id))
    intrinsics, width, height = intrinsics_for(scenario)
    capture_hz = float(scenario["sensor"]["capture_hz"])
    frame_dt = 1.0 / capture_hz
    sigma_px = float(body_config["calibration"]["sigma_px"])
    sigma_att_deg = float(body_config["estimator"]["sigma_att_deg"])
    ground_y = float(scenario["target"]["route_world_m"][0]["y"])
    route = ClosedRoute(
        [(p["x"], p["y"], p["z"]) for p in scenario["target"]["route_world_m"]],
        float(scenario["target"]["speed_mps"]),
    )
    loop_s = route.loop_duration_s
    total_s = 2.0 * loop_s if duration_s is None else float(duration_s)
    anchor = settings.anchor_world_m
    fence = settings.geofence
    plant = UnityPlantMirror(
        anchor=anchor,
        tether_length=settings.tether_length_m,
        minimum_altitude=settings.minimum_altitude_m,
        maximum_altitude=settings.maximum_altitude_m,
        maximum_speed=settings.maximum_speed_mps,
        maximum_acceleration=settings.maximum_acceleration_mps2,
        position=(anchor[0], r32(r32(anchor[1]) + r32(altitude_m)), anchor[2]),
        tether_enabled=settings.tether_enabled,
        geofence=(
            (fence.min_x, fence.max_x, fence.min_z, fence.max_z) if fence is not None else None
        ),
    )
    planner = build_planner(policy, scenario, body_config)
    estimator = _estimator_from_body_config(body_config, PROJECT_ROOT)
    max_off_nadir = float(scenario["gimbal"]["maximum_off_nadir_deg"])
    obstacle_pad = FIXED["obstacle_pad_m"]
    yaw_deg = 0.0
    samples: list[dict[str, Any]] = []
    frame = 0
    while frame * frame_dt < total_s - 1e-9:
        now = frame * frame_dt
        target, heading = route.sample(now)
        aim = (target[0], target[1] + 0.5 * CAR_HEIGHT_M, target[2])
        camera = plant.position
        basis, gimbal_saturated, yaw_deg = gimbal_pose(camera, aim, max_off_nadir, yaw_deg)
        box = car_box_px(target, heading, camera, basis, intrinsics, width, height)
        centre = project_point(aim, camera, basis, intrinsics)
        center_error = (
            math.hypot(centre[0] - intrinsics["cx"], centre[1] - intrinsics["cy"])
            if centre is not None
            else None
        )
        reported = dict(basis)
        observation = None
        if box is not None:
            u0, v0, u1, v1 = box
            shift_sigma = {"E0": 0.0, "E1": sigma_px, "E2": 2.0 * sigma_px}[noise]
            du = rng.gauss(0.0, shift_sigma) if shift_sigma > 0 else 0.0
            dv = rng.gauss(0.0, shift_sigma) if shift_sigma > 0 else 0.0
            observation = clip_box_norm(
                ((u0 + du) / width, (v0 + dv) / height, (u1 - u0) / width, (v1 - v0) / height)
            )
        if noise == "E2":
            sigma = math.radians(sigma_att_deg)
            omega_components = (rng.gauss(0.0, sigma), rng.gauss(0.0, sigma), rng.gauss(0.0, sigma))
            omega = tuple(
                basis["right"][i] * omega_components[0]
                + basis["up"][i] * omega_components[1]
                + basis["forward"][i] * omega_components[2]
                for i in range(3)
            )
            reported = {key: _rotate(vector, omega) for key, vector in basis.items()}
        metadata = {
            "camera_position_world_m": list(camera),
            "camera_forward_world": list(reported["forward"]),
            "camera_right_world": list(reported["right"]),
            "camera_up_world": list(reported["up"]),
            "width": width,
            "height": height,
            "intrinsics_px": dict(intrinsics),
            "gimbal_saturated": gimbal_saturated,
            "tether_saturated": plant.tether_saturated,
        }
        reason = None
        command: BodyCommand
        expires = float(body_config["command"]["expires_after_s"])
        if frame == 0:
            command = BodyCommand.hold(expires, "initialize")
        else:
            estimate = None
            try:
                if not estimator.initialized:
                    if observation is not None:
                        estimate = estimator.initialize(observation, metadata, ground_y, now)
                elif observation is not None:
                    try:
                        estimate = estimator.update(observation, metadata, ground_y, now)
                    except GeometryRejected:
                        estimate = estimator.advance(now)
                else:
                    estimate = estimator.advance(now)
            except (ValueError, GeometryRejected):
                estimate = None
            if observation is None:
                command = BodyCommand.hold(expires, "no_observation")
            else:
                platform = PlatformState(
                    frame_id=frame,
                    capture_monotonic_s=now,
                    position_world_m=tuple(camera),
                    camera_forward_world=tuple(reported["forward"]),
                    gimbal_saturated=gimbal_saturated,
                    tether_saturated=plant.tether_saturated,
                )
                command = planner.decide(platform, estimate, now)
                reason = command.reason
        slant = math.dist(camera, aim)
        body_speed = math.hypot(plant.applied[0], plant.applied[2])
        samples.append(
            {
                "t": now,
                "body": tuple(camera),
                "target": tuple(target),
                "body_speed_mps": body_speed,
                "gimbal_saturated": gimbal_saturated,
                "tether_saturated": plant.tether_saturated,
                "center_error_px": center_error,
                "slant_range_m": slant,
                "reason": reason if policy in CANDIDATES else None,
                "planner_reason": command.reason,
                "command_speed_mps": math.hypot(
                    command.velocity_world_mps[0], command.velocity_world_mps[2]
                ),
                "command_vy_mps": command.velocity_world_mps[1],
                "fence_violation": (
                    fence is not None and not fence.contains(camera[0], camera[2])
                ),
                "inside_inflated_prism": _inside_inflated_prism(camera, prisms, obstacle_pad),
                "beyond_35m": math.dist(camera, anchor) > BEYOND_TETHER_M,
            }
        )
        if command.mode == "velocity_world":
            plant.set_velocity(command.velocity_world_mps)
        else:
            plant.hold()
        for _ in range(PLANT_SUBSTEPS_PER_FRAME):
            plant.step(frame_dt / PLANT_SUBSTEPS_PER_FRAME)
        frame += 1
    windows = {
        "loop2": [s for s in samples if loop_s <= s["t"] < 2.0 * loop_s],
        "all": samples,
    }
    read_outs = {}
    for name, window in windows.items():
        summary = summarize_window(window, intrinsics["fy"])
        summary["fence_violation_frames"] = sum(1 for s in window if s["fence_violation"])
        summary["inside_inflated_prism_frames"] = sum(
            1 for s in window if s["inside_inflated_prism"]
        )
        summary["beyond_35m_from_anchor_frames"] = sum(1 for s in window if s["beyond_35m"])
        summary["command_speed_max_mps"] = max(
            (s["command_speed_mps"] for s in window), default=None
        )
        summary["command_vy_max_abs_mps"] = max(
            (abs(s["command_vy_mps"]) for s in window), default=None
        )
        read_outs[name] = summary
    return {
        "cell": {"policy": policy, "altitude_m": altitude_m, "tether": tether, "noise": noise},
        "seed": _seed(cell_id),
        "read_outs": read_outs,
        "samples": samples,
    }


def hard_checks(loop2: Mapping[str, Any]) -> dict[str, Any]:
    """H1 ... H5 on a second-loop read-out (proposal section 3.9)."""
    h1 = loop2["R2_gimbal_saturated_fraction"]
    h2 = loop2["R5_range"]["short_side_px_p10"]
    h3_frames = loop2["fence_violation_frames"] + loop2["inside_inflated_prism_frames"]
    h3_fraction = loop2["R6_reasons"]["boundary_obstacle_modifier_fraction"]
    h4 = loop2["R4_body_motion"]["start_stop_count"]
    h5 = loop2["R4_body_motion"]["stationary_fraction"]
    checks = {
        "H1": {"value": h1, "limit": H1_MAX_GIMBAL_SATURATED_FRACTION,
               "pass": h1 is not None and h1 <= H1_MAX_GIMBAL_SATURATED_FRACTION},
        "H2": {"value": h2, "limit": H2_MIN_SHORT_SIDE_PX_P10,
               "pass": h2 is not None and h2 >= H2_MIN_SHORT_SIDE_PX_P10},
        "H3": {"violation_frames": h3_frames, "modifier_fraction": h3_fraction,
               "limit": H3_MAX_BOUNDARY_OBSTACLE_MODIFIER_FRACTION,
               "pass": h3_frames == 0 and h3_fraction is not None
               and h3_fraction <= H3_MAX_BOUNDARY_OBSTACLE_MODIFIER_FRACTION},
        "H4": {"value": h4, "limit": H4_MAX_START_STOPS_PER_LOOP,
               "pass": h4 <= H4_MAX_START_STOPS_PER_LOOP},
        "H5": {"value": h5, "limit": H5_MAX_STATIONARY_FRACTION,
               "pass": h5 is not None and h5 <= H5_MAX_STATIONARY_FRACTION},
    }
    checks["all_pass"] = all(checks[key]["pass"] for key in ("H1", "H2", "H3", "H4", "H5"))
    return checks


def select_candidate(per_candidate: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Pre-registered rule: all-pass candidates, shortest second-loop path;
    within 3 % of the shortest -> fewer start-stops -> lower candidate number."""
    passing = [cid for cid in sorted(per_candidate) if per_candidate[cid]["checks"]["all_pass"]]
    if not passing:
        return {"selected_candidate": None, "outcome": "NO_CANDIDATE_PASSES", "tied": []}
    shortest = min(per_candidate[cid]["path_length_m"] for cid in passing)
    tied = [
        cid for cid in passing
        if per_candidate[cid]["path_length_m"] <= shortest * (1.0 + TIE_PATH_RELATIVE)
    ]
    chosen = sorted(
        tied,
        key=lambda cid: (per_candidate[cid]["start_stop_count"], CANDIDATES_ORDER.index(cid)),
    )[0]
    return {"selected_candidate": chosen, "outcome": "SELECTED", "tied": tied}


CANDIDATES_ORDER = tuple(CANDIDATES)


def _clearance_check(prisms, fence: Mapping[str, float], anchor_y: float) -> dict[str, Any]:
    """AC-10 offline check: prisms meeting the fence vs the body height."""
    inside = [
        p for p in prisms
        if p[3] >= fence["min_x"] and p[0] <= fence["max_x"]
        and p[5] >= fence["min_z"] and p[2] <= fence["max_z"]
    ]
    top = max(p[4] for p in inside)
    pad = FIXED["obstacle_pad_m"]
    altitudes = {}
    for altitude in ALTITUDES_M:
        body_y = anchor_y + altitude
        conflicts = sorted(
            {round(p[4], 6) for p in inside if p[4] + pad >= body_y}
        )
        altitudes[f"{altitude:g}"] = {
            "body_world_height_m": body_y,
            "clear": top + pad < body_y,
            "conflicting_prisms": [
                {"max_y_m": round(p[4], 6), "min_x_m": round(p[0], 6), "max_x_m": round(p[3], 6),
                 "min_z_m": round(p[2], 6), "max_z_m": round(p[5], 6)}
                for p in sorted(inside, key=lambda q: (-q[4], q[0], q[2]))
                if p[4] + pad >= body_y
            ],
            "conflicting_top_heights_m": conflicts,
        }
    return {
        "fence_xz_m": dict(fence),
        "prisms_meeting_fence": len(inside),
        "max_prism_top_in_fence_m": top,
        "obstacle_pad_m": pad,
        "altitudes": altitudes,
    }


def _rounded(value: Any) -> Any:
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return round(value, 6)
    if isinstance(value, Mapping):
        return {str(k): _rounded(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_rounded(v) for v in value]
    return value


def run_replay(*, duration_s: float | None = None, policies: Sequence[str] = POLICIES) -> dict[str, Any]:
    scenarios = {"untethered": _load(UNTETHERED_SCENARIO), "tethered": _load(TETHERED_SCENARIO)}
    body_config = _load(BODY_001_CONFIG)
    prisms = load_corridor_prisms(PROJECT_ROOT / body_config["corridor"]["artifact_path"])
    grid = []
    selection_inputs: dict[str, dict[str, Any]] = {}
    for policy in policies:
        for altitude in ALTITUDES_M:
            for tether in TETHER_MODES:
                for noise in NOISE_CONDITIONS:
                    result = simulate_cell(
                        policy, altitude, tether, noise,
                        duration_s=duration_s, scenarios=scenarios,
                        body_config=body_config, prisms=prisms,
                    )
                    loop2 = result["read_outs"]["loop2"]
                    row = {
                        **result["cell"],
                        "seed": result["seed"],
                        "loop2": loop2,
                        "all": result["read_outs"]["all"],
                    }
                    grid.append(row)
                    is_selection_cell = (
                        policy in CANDIDATES
                        and altitude == SELECTION_CELL["altitude_m"]
                        and tether == SELECTION_CELL["tether"]
                        and noise == SELECTION_CELL["noise"]
                    )
                    if is_selection_cell:
                        selection_inputs[policy] = {
                            "checks": hard_checks(loop2),
                            "path_length_m": loop2["R4_body_motion"]["path_length_m"],
                            "start_stop_count": loop2["R4_body_motion"]["start_stop_count"],
                        }
    selection = select_candidate(selection_inputs) if selection_inputs else None
    untethered = parse_tether_settings(scenarios["untethered"])
    tethered = parse_tether_settings(scenarios["tethered"])
    route = scenarios["untethered"]["target"]
    loop = ClosedRoute([(p["x"], p["y"], p["z"]) for p in route["route_world_m"]], route["speed_mps"])
    evidence = {
        "schema_version": SCHEMA,
        "work_id": WORK_ID,
        "generator": "tools/frame_follow_replay.py",
        "inputs": {
            "untethered_scenario": {"path": UNTETHERED_SCENARIO, "sha256": _sha256(UNTETHERED_SCENARIO)},
            "tethered_scenario": {"path": TETHERED_SCENARIO, "sha256": _sha256(TETHERED_SCENARIO)},
            "body_001_config": {"path": BODY_001_CONFIG, "sha256": _sha256(BODY_001_CONFIG)},
            "corridor_artifact": {
                "path": body_config["corridor"]["artifact_path"],
                "sha256": body_config["corridor"]["artifact_sha256"],
            },
        },
        "model": {
            "route_perimeter_m": loop.perimeter_m,
            "loop_duration_s": loop.loop_duration_s,
            "simulated_duration_s": 2.0 * loop.loop_duration_s if duration_s is None else duration_s,
            "decision_hz": float(scenarios["untethered"]["sensor"]["capture_hz"]),
            "plant_substeps_per_frame": PLANT_SUBSTEPS_PER_FRAME,
            "plant": "float32 mirror of TetheredDronePlant.Step (AC-19 golden vectors)",
            "gimbal": "ideal pointing at the car box centre, 45 deg clamp, saturation above limit + 0.1 deg",
            "box": "oriented red-car box 2.0 x 1.55 x 4.0 m projected with the frame pinhole model, clipped",
            "estimator": "WorldEstimateFilter with the frozen BODY-001 priors and sigma_px",
            "frame_0": "initialisation frame, hold (track_loop initialize())",
            "noise": {
                "E0": "none",
                "E1": "box centre + N(0, sigma_px) px per axis",
                "E2": "box centre + N(0, 2 sigma_px) px per axis; reported camera attitude + N(0, sigma_att_deg) per axis",
            },
            "threshold_in_untethered_cells": "ThresholdBodyPlanner without corridor prisms (same as the embedded fallback)",
            "short_side_px": "2.0 m * fy / slant range to the car box centre",
            "loop2_window": "loop_duration_s <= t < 2 loop_duration_s",
        },
        "candidates": CANDIDATES,
        "fixed": FIXED,
        "selection_rule": {
            "cell": SELECTION_CELL,
            "H1_max_gimbal_saturated_fraction": H1_MAX_GIMBAL_SATURATED_FRACTION,
            "H2_min_short_side_px_p10": H2_MIN_SHORT_SIDE_PX_P10,
            "H3": "zero fence-violation and zero inside-inflated-prism (2.1 m) frames; boundary/obstacle modifier share <= 0.01",
            "H4_max_start_stops_per_loop": H4_MAX_START_STOPS_PER_LOOP,
            "H5_max_stationary_fraction": H5_MAX_STATIONARY_FRACTION,
            "tie_break": "shortest second-loop path; paths within 3 % are tied -> fewer start-stops -> lower candidate number",
            "no_pass": "no Play; back to Acceptance",
        },
        "selection": (
            None if selection is None else {
                **selection,
                "per_candidate": selection_inputs,
                "selected_params": (
                    CANDIDATES[selection["selected_candidate"]]
                    if selection["selected_candidate"] else None
                ),
            }
        ),
        "grid": grid,
        "safety_bounds": {
            "untethered_scenario": scenario_safety_bounds(untethered),
            "tethered_scenario": scenario_safety_bounds(tethered),
            "planner_side": {
                "command_v_max_mps": FIXED["v_max_mps"],
                "obstacle_pad_m": FIXED["obstacle_pad_m"],
                "corridor_pad_m_tethered_only": FIXED["corridor_pad_m"],
                "d_plaus_m": FIXED["d_plaus_m"],
                "expires_after_s": float(body_config["command"]["expires_after_s"]),
            },
            "obstacle_clearance": _clearance_check(
                prisms, untethered.geofence.as_dict(), untethered.anchor_world_m[1]
            ),
        },
    }
    return _rounded(evidence)


def evidence_bytes(evidence: Mapping[str, Any]) -> bytes:
    return (json.dumps(evidence, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def render_markdown(evidence: Mapping[str, Any]) -> str:
    lines = [
        "# P1-ENG-FRAME-001 离线运动学回放与预注册选参",
        "",
        "由 `tools/frame_follow_replay.py` 生成（与同名 `.json` 同一次运行；勿手改）。只支持「策略在几何上的行为」陈述：",
        "运动学 + 合成观测，不含渲染、检测与跟踪器失败；估计器先验未标定，E1/E2 只是预注册扰动（提案 §6）。",
        "",
        "## 选参（25 m / 系留关 / E1 / 第二圈）",
        "",
        "| 候选 | H1 饱和比例 | H2 短边 p10 (px) | H3 越界帧 / 修饰占比 | H4 起停 | H5 静止比例 | 全过 | 路程 (m) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    selection = evidence.get("selection") or {}
    for cid, item in sorted((selection.get("per_candidate") or {}).items()):
        c = item["checks"]
        lines.append(
            f"| {cid} | {_fmt(c['H1']['value'], 4)} | {_fmt(c['H2']['value'], 1)} | "
            f"{c['H3']['violation_frames']} / {_fmt(c['H3']['modifier_fraction'], 4)} | "
            f"{c['H4']['value']} | {_fmt(c['H5']['value'], 4)} | {'是' if c['all_pass'] else '否'} | "
            f"{_fmt(item['path_length_m'], 1)} |"
        )
    lines += [
        "",
        f"结果：`{selection.get('outcome')}`，选中 `{selection.get('selected_candidate')}`"
        f"（平手集 {selection.get('tied')}；规则：全过者取第二圈路程最短，3% 内平手比起停次数、再比编号）。",
        "",
        "## 网格读数（第二圈；描述量，不设门）",
        "",
        "| 策略 | 高度 | 系留 | 噪声 | 饱和 | 中心误差 p50/p90 (px) | 跟随距离 p50/max (m) | 短边 p10 (px) | 起停 | 静止 | 路程 (m) | 边界/避障修饰 | 越 35 m 帧 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in evidence["grid"]:
        l2 = row["loop2"]
        lines.append(
            f"| {row['policy']} | {row['altitude_m']:g} | {row['tether']} | {row['noise']} | "
            f"{_fmt(l2['R2_gimbal_saturated_fraction'], 3)} | "
            f"{_fmt(l2['R1_center_error_px']['p50'], 1)}/{_fmt(l2['R1_center_error_px']['p90'], 1)} | "
            f"{_fmt(l2['R3_follow_distance_m']['p50'], 1)}/{_fmt(l2['R3_follow_distance_m']['max'], 1)} | "
            f"{_fmt(l2['R5_range']['short_side_px_p10'], 1)} | {l2['R4_body_motion']['start_stop_count']} | "
            f"{_fmt(l2['R4_body_motion']['stationary_fraction'], 3)} | {_fmt(l2['R4_body_motion']['path_length_m'], 1)} | "
            f"{_fmt(l2['R6_reasons']['boundary_obstacle_modifier_fraction'], 3)} | {l2['beyond_35m_from_anchor_frames']} |"
        )
    clearance = evidence["safety_bounds"]["obstacle_clearance"]
    lines += [
        "",
        "## 安全边界离线核对（AC-10）",
        "",
        f"围栏 {clearance['fence_xz_m']} 内相交棱柱 {clearance['prisms_meeting_fence']} 个，顶高最大 "
        f"{_fmt(clearance['max_prism_top_in_fence_m'], 2)} m；膨胀 {clearance['obstacle_pad_m']} m。",
    ]
    for altitude, item in clearance["altitudes"].items():
        lines.append(
            f"- {altitude} m：机身世界高 {_fmt(item['body_world_height_m'], 2)} m，"
            f"{'无冲突' if item['clear'] else '冲突棱柱顶高 ' + str(item['conflicting_top_heights_m'])}。"
        )
    lines += [
        "",
        "说明：系留开（tethered）各行的「越 35 m 帧」应为 0；hold 行的 R-6 无规划器原因（不是 standoff），读数只描述几何。",
        "threshold 在系留关格不带走廊棱柱（与内嵌兜底一致）；15 m 与系留开读数只作描述，不参与选择。",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Play analysis (AC-21 / AC-23 read-outs; no gates)
# ---------------------------------------------------------------------------


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


#: ``body_planner`` identity keys that bind a run to its scenario (written by
#: ``controller.track_loop._build_standoff_runtime``; proposal section 3.8).
MANIFEST_SCENARIO_KEYS = (
    "scenario_config_path",
    "scenario_config_sha256",
    "effective_scenario_path",
    "effective_scenario_sha256",
)


def _manifest_scenario_binding(manifest: Mapping[str, Any]) -> dict[str, str]:
    """The run manifest's scenario identity; fails closed when it is absent."""
    planner = manifest.get("body_planner")
    if not isinstance(planner, Mapping):
        raise ValueError(
            "run manifest has no body_planner identity, so the analysed "
            "scenario cannot be bound to the run (section 3.11 entry 8)"
        )
    binding = {}
    for key in MANIFEST_SCENARIO_KEYS:
        value = planner.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"run manifest body_planner.{key} is missing")
        binding[key] = value
    return binding


def analyze_run(
    run_directory: Path,
    truth_path: Path,
    metrics_path: Path | None,
    scenario_path: Path,
) -> dict[str, Any]:
    """Section 3.10 read-outs for one Play (same functions as the replay).

    The geometry comes from ``scenario_path``, which must be byte-identical
    (sha256) to both the body scenario and the effective scenario recorded in
    the run manifest's ``body_planner`` identity; any mismatch, or a manifest
    without that identity, is refused (section 3.11 entry 8). The analysed
    file's sha and the manifest's source paths are written to the output.
    """
    manifest = json.loads((Path(run_directory) / "manifest.json").read_text(encoding="utf-8"))
    binding = _manifest_scenario_binding(manifest)
    scenario_bytes = Path(scenario_path).read_bytes()
    scenario_sha256 = hashlib.sha256(scenario_bytes).hexdigest()
    for key in ("scenario_config_sha256", "effective_scenario_sha256"):
        if scenario_sha256 != binding[key]:
            raise ValueError(
                f"scenario {str(scenario_path)!r} sha256 {scenario_sha256} does not "
                f"match the run manifest body_planner.{key} {binding[key]} "
                f"(effective scenario source {binding['effective_scenario_path']!r})"
            )
    scenario = json.loads(scenario_bytes.decode("utf-8"))
    settings = parse_tether_settings(scenario)
    intrinsics, width, height = intrinsics_for(scenario)
    frames = [
        r for r in _read_jsonl(Path(run_directory) / "frames.jsonl")
        if r.get("record_kind", "frame") == "frame"
    ]
    truth = _read_jsonl(truth_path)
    reasons_by_frame = {}
    commands = []
    for record in frames:
        planner = record.get("body_planner")
        if isinstance(planner, Mapping):
            reasons_by_frame[record.get("frame_id")] = planner.get("reason")
            commands.append(planner.get("velocity_world_mps") or [0.0, 0.0, 0.0])
    anchor = settings.anchor_world_m
    route = ClosedRoute(
        [(p["x"], p["y"], p["z"]) for p in scenario["target"]["route_world_m"]],
        float(scenario["target"]["speed_mps"]),
    )
    samples = []
    for record in truth:
        body = (record["body_world_x_m"], record["body_world_y_m"], record["body_world_z_m"])
        target = (record["target_world_x_m"], record["target_world_y_m"], record["target_world_z_m"])
        aim = (target[0], target[1] + 0.5 * CAR_HEIGHT_M, target[2])
        error = record.get("target_center_error_px") if record.get("truth_box_available") else None
        samples.append(
            {
                "t": float(record["simulation_time_s"]),
                "body": body,
                "target": target,
                "body_speed_mps": math.hypot(
                    record["applied_velocity_x_mps"], record["applied_velocity_z_mps"]
                ),
                "gimbal_saturated": bool(record["gimbal_saturated"]),
                "tether_saturated": bool(record["tether_saturated"]),
                "center_error_px": error,
                "slant_range_m": math.dist(body, aim),
                "reason": reasons_by_frame.get(record.get("frame_id")),
                "truth_short_side_px": (
                    min(record["truth_box_width"] * width, record["truth_box_height"] * height)
                    if record.get("truth_box_available") else None
                ),
            }
        )
    loop_s = route.loop_duration_s
    windows = {
        "all": samples,
        "loop2": [s for s in samples if loop_s <= s["t"] < 2.0 * loop_s],
    }
    read_outs = {}
    for name, window in windows.items():
        summary = summarize_window(window, intrinsics["fy"])
        truth_sides = [s["truth_short_side_px"] for s in window if s["truth_short_side_px"] is not None]
        summary["R5_range"]["truth_short_side_px_p10"] = percentile(truth_sides, 0.1)
        summary["R5_range"]["truth_short_side_px_p50"] = percentile(truth_sides, 0.5)
        read_outs[name] = summary
    fence = settings.geofence
    initial_y = anchor[1] + settings.initial_altitude_m
    safety = {
        "T_fence_violation_frames": (
            sum(1 for s in samples if not fence.contains(s["body"][0], s["body"][2]))
            if fence is not None else None
        ),
        "T_altitude_outside_initial_pm_0_05_frames": sum(
            1 for s in samples if abs(s["body"][1] - initial_y) > 0.05
        ),
        "T_tether_saturated_frames": sum(1 for s in samples if s["tether_saturated"]),
        "T_beyond_35m_from_anchor_frames": sum(
            1 for s in samples if math.dist(s["body"], anchor) > BEYOND_TETHER_M
        ),
        "P_command_speed_max_mps": max(
            (math.hypot(c[0], c[2]) for c in commands), default=None
        ),
        "P_command_vy_max_abs_mps": max((abs(c[1]) for c in commands), default=None),
        "P_reason_read_outs": reason_read_outs(
            [reason for reason in reasons_by_frame.values() if isinstance(reason, str)]
        ),
    }
    c_track = None
    if metrics_path is not None:
        metrics = json.loads(Path(metrics_path).read_text(encoding="utf-8"))
        c_track = metrics.get("c_track", metrics.get("summary", {}).get("c_track"))
        # Preserve legacy precedence, including explicit null/zero values.
        if "c_track" not in metrics and "c_track" not in metrics.get("summary", {}):
            c_track = metrics.get("aggregate", {}).get("c_track")
    return _rounded(
        {
            "schema_version": "p1-eng-frame-001-play-analysis/v1",
            "work_id": WORK_ID,
            "run_id": manifest.get("run_id"),
            "scenario_id": scenario.get("scenario_id"),
            "scenario_binding": {
                "analysed_scenario_path": str(scenario_path),
                "analysed_scenario_sha256": scenario_sha256,
                "scenario_config_path": binding["scenario_config_path"],
                "effective_scenario_path": binding["effective_scenario_path"],
            },
            "body_planner": manifest.get("body_planner"),
            "read_outs": read_outs,
            "R7_c_track": c_track,
            "safety_read_outs": safety,
        }
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="re-run the replay and verify the checked-in evidence byte for byte",
    )
    parser.add_argument("--analyze-run", type=Path, help="Play run directory (runtime/runs/<run_id>)")
    parser.add_argument("--truth", type=Path, help="evaluator m3_body_truth.jsonl copy for --analyze-run")
    parser.add_argument("--metrics", type=Path, help="metrics.json copy for --analyze-run")
    parser.add_argument(
        "--scenario",
        type=Path,
        help=(
            "scenario file of the analysed Play (required with --analyze-run; no default; "
            "its sha256 must equal the run manifest's body_planner scenario hashes)"
        ),
    )
    parser.add_argument("--output", type=Path, help="write the --analyze-run JSON here")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    if args.analyze_run is not None:
        if args.truth is None or args.scenario is None:
            parser.error("--analyze-run requires --truth and --scenario")
        result = analyze_run(args.analyze_run, args.truth, args.metrics, args.scenario)
        text = json.dumps(result, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
        if args.output is not None:
            args.output.write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0
    evidence = run_replay()
    data = evidence_bytes(evidence)
    markdown = render_markdown(evidence).encode("utf-8")
    json_path = PROJECT_ROOT / EVIDENCE_JSON
    md_path = PROJECT_ROOT / EVIDENCE_MD
    if args.check:
        same = json_path.read_bytes() == data and md_path.read_bytes() == markdown
        print("replay evidence " + ("matches" if same else "DIFFERS"))
        return 0 if same else 1
    json_path.write_bytes(data)
    md_path.write_bytes(markdown)
    selection = evidence.get("selection") or {}
    print(
        json.dumps(
            {
                "selected_candidate": selection.get("selected_candidate"),
                "outcome": selection.get("outcome"),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
