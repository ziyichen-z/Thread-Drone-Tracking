"""P1-ENG-FRAME-001 Part P: the ``standoff-band-v1`` body planner.

Proposal section 3.6 (c-combination): the gimbal keeps the target centred
(unchanged), while the body keeps a horizontal stand-off distance band
around the *predicted* ground estimate:

1. contract fail-safes (``hold_no_platform``, ``hold_margin_unconstructible``,
   ``hold_no_estimate``) - the fallback may never override these;
2. estimate gate: position sigma above the band width or any non-finite
   component holds (``hold_estimate_uncertain``); a predicted point beyond
   the plausibility range holds (``hold_estimate_implausible``);
3. follow: lead the estimate by ``T_lead`` (estimate velocity clamped),
   latch on beyond ``d* + w`` and off at ``d*``, command
   ``min(v_max, k_p (d - d*))`` towards the predicted point; inside the
   band, or on the near side, hold (``in_band_hold``) - never back away;
4. fallback: an embedded, unmodified ``ThresholdBodyPlanner`` is called on
   every frame to keep its hysteresis; its velocity is adopted only when
   step 2/3 concluded ``hold`` (``fallback_margin``);
5. safety post-processing of every velocity, in a fixed order: reach-circle
   projection (tether on only) and geofence projection (when configured),
   body-segment obstacle shortening (both modes), anchor-corridor shortening
   (tether on only);
6. ``reason`` = one main tag plus modifiers from closed sets, modifiers in
   the fixed order above.

The module imports only the contract types of ``controller/body_planner.py``
(proposal AC-11): the embedded threshold planner is injected by the
caller, and the segment/prism slab test below repeats the frozen
algorithm. ``decide`` is pure in the BC-BODY1-19 (a) sense - no I/O, no
clock, no truth - and deterministic in its ordered input history from the
fixed initial state (latch off, a fresh fallback instance).

The loader at the bottom reads the work item's frozen config; it performs
file I/O but is never called from ``decide``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from .body_planner import (
    CONTRACT_VERSION,
    BodyCommand,
    BodyPlanner,
    PlatformState,
    WorldEstimate,
)

PLANNER_NAME = "standoff-band-v1"
CONFIG_SCHEMA = "p1-eng-frame-001-body/v1"
CONFIG_WORK_ID = "P1-ENG-FRAME-001"
BODY_001_CONFIG_SCHEMA = "p1-m3-body-001/v1"
FALLBACK_PLANNER_NAME = "threshold-corridor-v1"
CANDIDATE_IDS: tuple[str, ...] = ("C1", "C2", "C3")

#: Section 3.6 step 6, main tags (closed set).
MAIN_TAGS: tuple[str, ...] = (
    "follow_move",
    "in_band_hold",
    "fallback_margin",
    "hold_no_platform",
    "hold_margin_unconstructible",
    "hold_no_estimate",
    "hold_estimate_uncertain",
    "hold_estimate_implausible",
)

#: Section 3.6 step 5 modifiers, in their fixed concatenation order.
MODIFIERS: tuple[str, ...] = (
    "+tether_limited",
    "+geofence_limited",
    "+boundary_blocked",
    "+obstacle_shortened",
    "+obstacle_blocked",
    "+corridor_shortened",
    "+corridor_blocked",
)

PARAM_KEYS: tuple[str, ...] = ("d_star_m", "band_w_m", "t_lead_s", "k_p_per_s")
FIXED_KEYS: tuple[str, ...] = (
    "v_max_mps",
    "target_velocity_clamp_mps",
    "d_plaus_m",
    "obstacle_pad_m",
    "corridor_pad_m",
    "shorten_step_m",
    "min_residual_speed_mps",
)

#: Numerical inset applied to boundary projections so that a candidate
#: recomputed as ``body + v * expires_after_s`` stays inside the closed
#: boundary despite floating-point rounding (see the K2 handoff, IR list).
BOUNDARY_INSET_M = 1e-9

#: Output check tolerance for the reach circle (proposal AC-15 (a)); the
#: geofence output check is exact (closed rectangle, AC-15 (b)).
REACH_TOLERANCE_M = 1e-6

#: A body further than this outside an enabled boundary holds with
#: ``+boundary_blocked`` (the plant clamps make it unreachable in practice).
BODY_OUTSIDE_TOLERANCE_M = 1e-3

#: Grid cell used to pre-select prisms for the slab test (pure speed-up:
#: a prism outside every cell the inflated query box touches cannot
#: intersect the query segment).
_GRID_CELL_M = 8.0

Prism = tuple[float, float, float, float, float, float]


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def segment_hits_prism(
    start: Sequence[float],
    end: Sequence[float],
    prism: Prism,
    pad_m: float,
) -> bool:
    """Slab test, term for term the frozen ``segment_intersects_prism``."""
    t_enter, t_exit = 0.0, 1.0
    for axis in range(3):
        direction = end[axis] - start[axis]
        lower = prism[axis] - pad_m
        upper = prism[axis + 3] + pad_m
        if abs(direction) <= 1e-12:
            if start[axis] <= lower or start[axis] >= upper:
                return False
            continue
        t0 = (lower - start[axis]) / direction
        t1 = (upper - start[axis]) / direction
        if t0 > t1:
            t0, t1 = t1, t0
        t_enter = max(t_enter, t0)
        t_exit = min(t_exit, t1)
        if t_enter >= t_exit:
            return False
    return True


class PrismIndex:
    """Uniform x/z grid over the frozen prisms (exact pre-selection)."""

    def __init__(self, prisms: Sequence[Prism]):
        self.prisms: tuple[Prism, ...] = tuple(tuple(p) for p in prisms)  # type: ignore[misc]
        self._cells: dict[tuple[int, int], list[int]] = {}
        for index, prism in enumerate(self.prisms):
            for cell in self._cells_for(prism[0], prism[2], prism[3], prism[5]):
                self._cells.setdefault(cell, []).append(index)

    @staticmethod
    def _cells_for(min_x: float, min_z: float, max_x: float, max_z: float):
        x0 = math.floor(min_x / _GRID_CELL_M)
        x1 = math.floor(max_x / _GRID_CELL_M)
        z0 = math.floor(min_z / _GRID_CELL_M)
        z1 = math.floor(max_z / _GRID_CELL_M)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                yield (x, z)

    def blocked(self, start: Sequence[float], end: Sequence[float], pad_m: float) -> bool:
        if not all(math.isfinite(value) for value in (*start, *end)):
            return True
        min_x = min(start[0], end[0]) - pad_m
        max_x = max(start[0], end[0]) + pad_m
        min_z = min(start[2], end[2]) - pad_m
        max_z = max(start[2], end[2]) + pad_m
        seen: set[int] = set()
        for cell in self._cells_for(min_x, min_z, max_x, max_z):
            for index in self._cells.get(cell, ()):
                if index in seen:
                    continue
                seen.add(index)
                if segment_hits_prism(start, end, self.prisms[index], pad_m):
                    return True
        return False


@dataclass(frozen=True)
class StandoffParams:
    """One pre-registered candidate (proposal section 3.9)."""

    d_star_m: float
    band_w_m: float
    t_lead_s: float
    k_p_per_s: float

    def __post_init__(self) -> None:
        for key in PARAM_KEYS:
            value = _finite(getattr(self, key), key)
            if value <= 0.0:
                raise ValueError(f"{key} must be positive")

    @classmethod
    def from_mapping(cls, raw: Any) -> "StandoffParams":
        if not isinstance(raw, Mapping) or set(raw) != set(PARAM_KEYS):
            raise ValueError(f"params must hold exactly {list(PARAM_KEYS)}")
        return cls(**{key: _finite(raw[key], f"params.{key}") for key in PARAM_KEYS})

    def as_dict(self) -> dict[str, float]:
        return {key: getattr(self, key) for key in PARAM_KEYS}


@dataclass(frozen=True)
class StandoffFixed:
    """Section 3.7 ``fixed`` block (not candidate variables)."""

    v_max_mps: float
    target_velocity_clamp_mps: float
    d_plaus_m: float
    obstacle_pad_m: float
    corridor_pad_m: float
    shorten_step_m: float
    min_residual_speed_mps: float

    def __post_init__(self) -> None:
        for key in FIXED_KEYS:
            value = _finite(getattr(self, key), key)
            if value <= 0.0:
                raise ValueError(f"{key} must be positive")

    @classmethod
    def from_mapping(cls, raw: Any) -> "StandoffFixed":
        if not isinstance(raw, Mapping) or set(raw) != set(FIXED_KEYS):
            raise ValueError(f"fixed must hold exactly {list(FIXED_KEYS)}")
        return cls(**{key: _finite(raw[key], f"fixed.{key}") for key in FIXED_KEYS})

    def as_dict(self) -> dict[str, float]:
        return {key: getattr(self, key) for key in FIXED_KEYS}


@dataclass(frozen=True)
class StandoffGeometry:
    """Operator-declared geometry the post-processing enforces."""

    anchor_world_m: tuple[float, float, float]
    tether_enabled: bool
    tether_length_m: float
    #: ``(min_x, max_x, min_z, max_z)`` or ``None`` when not configured.
    geofence_xz_m: tuple[float, float, float, float] | None
    maximum_off_nadir_deg: float


def compose_reason(main: str, modifiers: set[str] | frozenset[str]) -> str:
    if main not in MAIN_TAGS:
        raise ValueError(f"unknown main tag {main!r}")
    unknown = set(modifiers) - set(MODIFIERS)
    if unknown:
        raise ValueError(f"unknown modifiers {sorted(unknown)!r}")
    return main + "".join(tag for tag in MODIFIERS if tag in modifiers)


def split_reason(reason: str) -> tuple[str, tuple[str, ...]]:
    """Inverse of :func:`compose_reason`; raises outside the closed sets."""
    main, _, rest = reason.partition("+")
    if main not in MAIN_TAGS:
        raise ValueError(f"unknown main tag {main!r}")
    modifiers = tuple("+" + part for part in rest.split("+")) if rest else ()
    order = [MODIFIERS.index(tag) for tag in modifiers if tag in MODIFIERS]
    if len(order) != len(modifiers) or order != sorted(set(order)):
        raise ValueError(f"modifiers out of the closed set or order: {reason!r}")
    return main, modifiers


class StandoffBodyPlanner(BodyPlanner):
    """Distance-band follower with a threshold fallback (section 3.6)."""

    name = PLANNER_NAME

    def __init__(
        self,
        *,
        params: StandoffParams,
        fixed: StandoffFixed,
        geometry: StandoffGeometry,
        expires_after_s: float,
        fallback: BodyPlanner,
        obstacle_prisms: Sequence[Prism],
        corridor_prisms: Sequence[Prism] | None,
    ):
        self.params = params
        self.fixed = fixed
        self.geometry = geometry
        self._expires_after_s = _finite(expires_after_s, "expires_after_s")
        if self._expires_after_s <= 0.0:
            raise ValueError("expires_after_s must be positive")
        if not isinstance(fallback, BodyPlanner) or fallback.name != FALLBACK_PLANNER_NAME:
            raise ValueError("the fallback must be a threshold-corridor-v1 planner")
        self._fallback = fallback
        anchor = tuple(geometry.anchor_world_m)
        if len(anchor) != 3:
            raise ValueError("anchor_world_m must be a three-element vector")
        self._anchor = tuple(_finite(v, "anchor_world_m") for v in anchor)
        self._maximum_off_nadir_deg = _finite(
            geometry.maximum_off_nadir_deg, "maximum_off_nadir_deg"
        )
        self._tether_length_m = _finite(geometry.tether_length_m, "tether_length_m")
        if geometry.tether_enabled:
            if self._tether_length_m <= 0.0:
                raise ValueError("tether_length_m must be positive")
            if corridor_prisms is None:
                raise ValueError("tether on: the anchor corridor prisms are required")
            self._corridor = PrismIndex(corridor_prisms)
        else:
            if corridor_prisms is not None:
                raise ValueError("tether off: no anchor corridor may be configured")
            if geometry.geofence_xz_m is None:
                raise ValueError("tether off: a geofence is required")
            self._corridor = None
        fence = geometry.geofence_xz_m
        if fence is not None:
            min_x, max_x, min_z, max_z = (_finite(v, "geofence") for v in fence)
            if not (min_x < max_x and min_z < max_z):
                raise ValueError("geofence must satisfy min < max")
            if not (min_x <= self._anchor[0] <= max_x and min_z <= self._anchor[2] <= max_z):
                raise ValueError("geofence must contain the home position")
            self._fence: tuple[float, float, float, float] | None = (
                min_x,
                max_x,
                min_z,
                max_z,
            )
        else:
            self._fence = None
        self._obstacles = PrismIndex(obstacle_prisms)
        self._following = False
        self._last_fallback: BodyCommand | None = None

    # -- read-only views for tests and the run log --------------------------

    @property
    def following(self) -> bool:
        return self._following

    @property
    def last_fallback_command(self) -> BodyCommand | None:
        """The embedded threshold planner's output on the latest frame."""
        return self._last_fallback

    @property
    def expires_after_s(self) -> float:
        return self._expires_after_s

    # -- contract ------------------------------------------------------------

    def decide(
        self,
        platform: PlatformState | None,
        estimate: WorldEstimate | None,
        now_monotonic_s: float,
    ) -> BodyCommand:
        # Step 4 precondition: the fallback runs every frame so its
        # hysteresis memory sees the same ordered history as a standalone
        # instance would.
        try:
            fallback: BodyCommand | None = self._fallback.decide(
                platform, estimate, now_monotonic_s
            )
        except (ValueError, TypeError, ArithmeticError):
            # Malformed (non-finite / mistyped) input: no fallback velocity;
            # step 1 below still returns the contract hold.
            fallback = None
        self._last_fallback = fallback

        # Step 1: contract fail-safes; the fallback can never override them.
        if platform is None or not all(
            math.isfinite(value) for value in platform.position_world_m
        ):
            return self._hold("hold_no_platform")
        try:
            margin_deg = platform.limit_margin_deg(self._maximum_off_nadir_deg)
        except (ValueError, OverflowError, TypeError):
            return self._hold("hold_margin_unconstructible")
        if not math.isfinite(margin_deg):
            return self._hold("hold_margin_unconstructible")
        if estimate is None:
            return self._hold("hold_no_estimate")

        main, velocity = self._follow_branch(platform, estimate)
        if velocity is None and fallback is not None and fallback.mode == "velocity_world":
            main = "fallback_margin"
            velocity = (fallback.velocity_world_mps[0], fallback.velocity_world_mps[2])
        if velocity is None:
            return self._hold(main)
        return self._post_process(platform, main, velocity)

    # -- steps 2 and 3 -------------------------------------------------------

    def _follow_branch(
        self, platform: PlatformState, estimate: WorldEstimate
    ) -> tuple[str, tuple[float, float] | None]:
        sigma = self._position_sigma(estimate)
        if sigma is None or sigma > self.params.band_w_m:
            return "hold_estimate_uncertain", None
        x, z, vx, vz = (float(value) for value in estimate.mean)
        speed = math.hypot(vx, vz)
        clamp = self.fixed.target_velocity_clamp_mps
        if speed > clamp:
            vx, vz = vx / speed * clamp, vz / speed * clamp
        lead = self.params.t_lead_s
        predicted = (x + lead * vx, z + lead * vz)
        body = platform.position_world_m
        dx = predicted[0] - body[0]
        dz = predicted[1] - body[2]
        distance = math.hypot(dx, dz)
        if not math.isfinite(distance):
            return "hold_estimate_uncertain", None
        if distance > self.fixed.d_plaus_m:
            return "hold_estimate_implausible", None
        d_star = self.params.d_star_m
        if distance > d_star + self.params.band_w_m:
            self._following = True
        elif distance <= d_star:
            self._following = False
        if not self._following:
            return "in_band_hold", None
        command_speed = min(
            self.fixed.v_max_mps, self.params.k_p_per_s * (distance - d_star)
        )
        return "follow_move", (dx / distance * command_speed, dz / distance * command_speed)

    @staticmethod
    def _position_sigma(estimate: WorldEstimate) -> float | None:
        try:
            mean = tuple(float(value) for value in estimate.mean)
            covariance = tuple(
                tuple(float(value) for value in row) for row in estimate.covariance
            )
        except (TypeError, ValueError):
            return None
        if len(mean) != 4 or len(covariance) != 4 or any(len(row) != 4 for row in covariance):
            return None
        if not all(math.isfinite(value) for value in mean):
            return None
        if not all(math.isfinite(value) for row in covariance for value in row):
            return None
        a = covariance[0][0]
        d = covariance[1][1]
        b = 0.5 * (covariance[0][1] + covariance[1][0])
        # ``math.hypot`` is the overflow-safe radius: a float ``**`` raises
        # OverflowError past the double range, so a huge but finite variance
        # would escape ``decide`` (AC-11 "finite inputs never raise"). Here it
        # yields a huge or infinite eigenvalue that the gate below holds on.
        largest = 0.5 * (a + d) + math.hypot(0.5 * (a - d), b)
        if not math.isfinite(largest):
            return None
        return math.sqrt(max(0.0, largest))

    # -- step 5 --------------------------------------------------------------

    def _post_process(
        self,
        platform: PlatformState,
        main: str,
        velocity: tuple[float, float],
    ) -> BodyCommand:
        modifiers: set[str] = set()
        horizon = self._expires_after_s
        body = tuple(float(value) for value in platform.position_world_m)
        candidate = (body[0] + velocity[0] * horizon, body[2] + velocity[1] * horizon)
        if not all(math.isfinite(value) for value in candidate):
            return self._hold(main, {"+boundary_blocked"})
        # A body already outside an enabled boundary (not reachable through
        # the plant clamps) cannot be given a candidate inside it without
        # exceeding v_max: hold fail-closed.
        if not self._inside_boundaries(
            (body[0], body[2]),
            body[1],
            reach_tolerance_m=BODY_OUTSIDE_TOLERANCE_M,
            fence_tolerance_m=BODY_OUTSIDE_TOLERANCE_M,
        ):
            return self._hold(main, {"+boundary_blocked"})

        # (1)(a) tether reach circle, tether on only.
        projected = False
        if self.geometry.tether_enabled:
            limited = self._project_circle(
                candidate, self._reach_radius(body[1]) - BOUNDARY_INSET_M
            )
            if limited != candidate:
                candidate = limited
                projected = True
                modifiers.add("+tether_limited")
        # (1)(b) geofence, whenever configured.
        if self._fence is not None:
            limited = self._project_fence(candidate, BOUNDARY_INSET_M)
            if limited != candidate:
                candidate = limited
                projected = True
                modifiers.add("+geofence_limited")
        displacement = math.hypot(candidate[0] - body[0], candidate[1] - body[2])
        if projected and displacement / horizon < self.fixed.min_residual_speed_mps:
            return self._hold(main, modifiers | {"+boundary_blocked"})
        if displacement <= 0.0:
            return self._hold(main, modifiers | {"+boundary_blocked"})
        direction = (
            (candidate[0] - body[0]) / displacement,
            (candidate[1] - body[2]) / displacement,
        )
        step = min(displacement, self.fixed.v_max_mps * horizon)

        # (2) body segment vs obstacle prisms, both modes.
        step, shortened = self._shorten(
            body, direction, step, start=body, index=self._obstacles,
            pad=self.fixed.obstacle_pad_m,
        )
        if step <= 0.0:
            return self._hold(main, modifiers | {"+obstacle_blocked"})
        if shortened:
            modifiers.add("+obstacle_shortened")

        # (3) anchor corridor, tether on only.
        if self._corridor is not None:
            step, shortened = self._shorten(
                body, direction, step, start=self._anchor, index=self._corridor,
                pad=self.fixed.corridor_pad_m,
            )
            if step <= 0.0:
                return self._hold(main, modifiers | {"+corridor_blocked"})
            if shortened:
                modifiers.add("+corridor_shortened")

        speed = step / horizon
        vx = direction[0] * speed
        vz = direction[1] * speed
        # Final guard with the exact recomputation a consumer would do.
        final = (body[0] + vx * horizon, body[2] + vz * horizon)
        if not self._inside_boundaries(
            final, body[1], reach_tolerance_m=REACH_TOLERANCE_M, fence_tolerance_m=0.0
        ):
            return self._hold(main, modifiers | {"+boundary_blocked"})
        return BodyCommand.velocity(
            vx, vz, self._expires_after_s, compose_reason(main, modifiers)
        )

    def _shorten(
        self,
        body: tuple[float, ...],
        direction: tuple[float, float],
        step: float,
        *,
        start: Sequence[float],
        index: PrismIndex,
        pad: float,
    ) -> tuple[float, bool]:
        shortened = False
        while step > 0.0:
            candidate = (
                body[0] + direction[0] * step,
                body[1],
                body[2] + direction[1] * step,
            )
            if not index.blocked(start, candidate, pad):
                return step, shortened
            shortened = True
            step -= self.fixed.shorten_step_m
        return 0.0, shortened

    def _reach_radius(self, body_y: float) -> float:
        height = body_y - self._anchor[1]
        length = self._tether_length_m
        return math.sqrt(max(0.0, length * length - height * height))

    def _project_circle(
        self, candidate: tuple[float, float], radius: float
    ) -> tuple[float, float]:
        radius = max(0.0, radius)
        dx = candidate[0] - self._anchor[0]
        dz = candidate[1] - self._anchor[2]
        distance = math.hypot(dx, dz)
        if distance <= radius:
            return candidate
        if distance <= 0.0:
            return (self._anchor[0], self._anchor[2])
        return (
            self._anchor[0] + dx / distance * radius,
            self._anchor[2] + dz / distance * radius,
        )

    def _project_fence(
        self, candidate: tuple[float, float], inset: float
    ) -> tuple[float, float]:
        assert self._fence is not None
        min_x, max_x, min_z, max_z = self._fence
        x = min(max(candidate[0], min_x + inset), max_x - inset)
        z = min(max(candidate[1], min_z + inset), max_z - inset)
        if min_x <= candidate[0] <= max_x and min_z <= candidate[1] <= max_z:
            # Already inside the closed fence: leave untouched (the inset
            # only applies to points that actually needed projecting).
            return candidate
        return (x, z)

    def _inside_boundaries(
        self,
        point: tuple[float, float],
        body_y: float,
        *,
        reach_tolerance_m: float,
        fence_tolerance_m: float,
    ) -> bool:
        if self.geometry.tether_enabled:
            dx = point[0] - self._anchor[0]
            dz = point[1] - self._anchor[2]
            if math.hypot(dx, dz) > self._reach_radius(body_y) + reach_tolerance_m:
                return False
        if self._fence is not None:
            min_x, max_x, min_z, max_z = self._fence
            if not (
                min_x - fence_tolerance_m <= point[0] <= max_x + fence_tolerance_m
                and min_z - fence_tolerance_m <= point[1] <= max_z + fence_tolerance_m
            ):
                return False
        return True

    def _hold(self, main: str, modifiers: set[str] | None = None) -> BodyCommand:
        return BodyCommand.hold(
            self._expires_after_s, compose_reason(main, modifiers or set())
        )


# ---------------------------------------------------------------------------
# Frozen config loader (proposal section 3.7, AC-17). File I/O lives here,
# never in ``decide``.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FrameBodyConfig:
    path: Path
    sha256: str
    selected_candidate: str
    params: StandoffParams
    fixed: StandoffFixed
    body_001_config_path: Path
    body_001_config_sha256: str
    body_001_config: Mapping[str, Any]
    replay_evidence_path: Path
    replay_evidence_sha256: str


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pinned(raw: Any, label: str, project_root: Path) -> tuple[Path, str]:
    if not isinstance(raw, Mapping) or set(raw) != {"path", "sha256"}:
        raise ValueError(f"{label} must hold exactly path and sha256")
    relative = raw["path"]
    digest = raw["sha256"]
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError(f"{label}.path must be a project-relative path")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(f"{label}.sha256 must be a SHA-256 hex digest")
    path = (project_root / relative).resolve()
    if _sha256_file(path) != digest:
        raise ValueError(f"{label} hash does not match {relative}")
    return path, digest


def load_frame_body_config(path: Path, *, project_root: Path) -> FrameBodyConfig:
    """Load ``config/p1-eng-frame-001-body.json``, failing closed.

    Missing fields, extra fields, non-finite numbers, a schema mismatch or
    any pinned hash mismatch raise ``ValueError``. There is deliberately no
    way to override a value from the command line.
    """
    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "schema_version",
        "work_id",
        "planner",
        "selected_candidate",
        "params",
        "fixed",
        "body_001_config",
        "replay_evidence",
    }
    if not isinstance(raw, Mapping) or set(raw) != expected:
        raise ValueError(f"FRAME body config must hold exactly {sorted(expected)}")
    if raw["schema_version"] != CONFIG_SCHEMA:
        raise ValueError(f"unsupported FRAME body config schema {raw['schema_version']!r}")
    if raw["work_id"] != CONFIG_WORK_ID:
        raise ValueError("FRAME body config work_id mismatch")
    if raw["planner"] != PLANNER_NAME:
        raise ValueError("FRAME body config planner mismatch")
    if raw["selected_candidate"] not in CANDIDATE_IDS:
        raise ValueError("selected_candidate must be one of C1/C2/C3")
    params = StandoffParams.from_mapping(raw["params"])
    fixed = StandoffFixed.from_mapping(raw["fixed"])
    body_path, body_sha = _pinned(raw["body_001_config"], "body_001_config", project_root)
    replay_path, replay_sha = _pinned(raw["replay_evidence"], "replay_evidence", project_root)
    body_config = json.loads(body_path.read_text(encoding="utf-8"))
    if body_config.get("schema_version") != BODY_001_CONFIG_SCHEMA:
        raise ValueError("pinned BODY-001 config has the wrong schema")
    command = body_config.get("command")
    if not isinstance(command, Mapping) or command.get("contract_version") != CONTRACT_VERSION:
        raise ValueError("pinned BODY-001 config contract version mismatch")
    return FrameBodyConfig(
        path=path,
        sha256=_sha256_file(path),
        selected_candidate=raw["selected_candidate"],
        params=params,
        fixed=fixed,
        body_001_config_path=body_path,
        body_001_config_sha256=body_sha,
        body_001_config=body_config,
        replay_evidence_path=replay_path,
        replay_evidence_sha256=replay_sha,
    )
