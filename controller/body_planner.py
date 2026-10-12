"""P1-M3-BODY-001: the frozen body planner interface and the v1 policies.

BC-M34-7 makes the versioned command contract its own stop point, ahead of
any M3' policy implementation and any M4' consumer. This module is that
contract's executable half: the types a planner sees, the command it returns,
and the abstract it must implement. The prose half, the M4' three-use-case
pre-review and the waypoint deferral live in
``docs/evidence/P1-M3-BODY-001-planner-contract.md``.

Batch 1a-alpha froze only the interface. Batch 1a-beta added the two v1
policies below the contract types: :class:`HoldBodyPlanner` (the arm-A
behaviour expressed as a planner) and :class:`ThresholdBodyPlanner` (the
proposal section 3.5 threshold allocation with the tether-corridor check).
The threshold policy reads the published limit margin and bearing only -
never the estimator, never truth (BC-M34-3, BC-BODY1-8) - and never reads
the saturation flag (BC-BODY1-6, review note N3).

Three fail-safe rules are part of the contract, not of any policy that
implements it (proposal section 5.3):

1. :meth:`BodyPlanner.decide` is pure in the precise BC-BODY1-19 (a) sense:
   no file or network I/O, no wall-clock reads, no truth or visibility-prior
   access and no external side effects. This does **not** forbid the frozen
   section 3.5 hysteresis memory: a policy is a deterministic function of
   its ordered input history from a fixed initial state, so replaying a run
   log in order through a fresh instance reproduces the same commands;
2. an absent estimate or an unconstructible platform state must produce
   ``hold``;
3. no alternative decision owner or bypass may publish a body command
   (BC-BODY1-19 (b)).

Rule 3 is why this module exposes no writer. A planner performs no I/O
itself; the actual writes happen only in ``controller/body_entry.py`` at the
existing ``initialize()`` hold and at the single mapping point in
``TrackLoop._body_step`` that turns a planner's return value (or its
fail-closed fallback) into a packet. Any other publish call is a contract
violation. The receiver's expiry fallback and a planner's ``hold`` remain
two independent safety nets (BC-BODY1-8): neither may be implemented as if
the other existed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Literal, Sequence

#: Bumped whenever any field, unit, mode or timing rule below changes.
#: ``waypoint`` mode is deliberately absent from v1 and is deferred to v2 (see
#: the contract document, section "waypoint deferral").
CONTRACT_VERSION = "body-planner-contract/v1"

#: The only two modes v1 admits. ``controller/body_entry.py`` already speaks
#: both; no runtime protocol byte changes in this batch.
BodyCommandMode = Literal["hold", "velocity_world"]

MODES: tuple[str, ...] = ("hold", "velocity_world")


def _finite(value: float, label: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    return value


@dataclass(frozen=True)
class PlatformState:
    """Published platform quantities, in the world frame, metres and seconds.

    Every field comes from the ``tethered-sensor-frame/v3`` frame packet. No
    estimator output and no ground truth may enter this type - BC-M34-3
    freezes the threshold trigger as a *published* platform quantity, and
    BC-BODY1-8 makes "zero truth reference on the online path" a mechanical
    review check.
    """

    frame_id: int
    capture_monotonic_s: float
    position_world_m: tuple[float, float, float]
    camera_forward_world: tuple[float, float, float]
    gimbal_saturated: bool
    tether_saturated: bool

    @property
    def theta_applied_deg(self) -> float:
        """Off-nadir angle of the applied camera direction (BC-BODY1-6)."""
        forward_y = min(1.0, max(-1.0, -self.camera_forward_world[1]))
        return math.degrees(math.acos(forward_y))

    def limit_margin_deg(self, maximum_off_nadir_deg: float) -> float:
        """Gimbal limit margin: the frozen BC-M34-3 trigger quantity.

        ``maximum_off_nadir_deg`` is read from the frozen scenario
        (``gimbal.maximum_off_nadir_deg``); it is never duplicated in this
        work item's own config.

        The margin is *not* equivalent to ``gimbal_saturated``:
        ``TetheredGimbal`` clamps the applied angle at the limit but only
        raises the flag above ``limit + 0.1`` (:37-38), so there is a 0.1 deg
        dead band in which the margin is zero and the flag is false. A policy
        may read this margin; it may not read the flag, and no evidence text
        may claim the two are equivalent (BC-BODY1-6).
        """
        return _finite(maximum_off_nadir_deg, "maximum_off_nadir_deg") - (
            self.theta_applied_deg
        )

    @property
    def bearing_deg(self) -> float:
        """Horizontal bearing of the applied camera direction (BC-BODY1-6)."""
        return math.degrees(
            math.atan2(self.camera_forward_world[0], self.camera_forward_world[2])
        )


@dataclass(frozen=True)
class WorldEstimate:
    """Ground-frame target estimate: mean, covariance and its timestamp.

    Batch 1 does not consume this - the threshold policy reads published
    platform state only (BC-M34-3). It is frozen now so batch 2's lexicographic
    policy and M4' consume the same shape.
    """

    #: ``[x, z, vx, vz]`` in the ground frame, metres and metres per second.
    mean: tuple[float, float, float, float]
    #: Row-major 4x4 covariance of ``mean``.
    covariance: tuple[tuple[float, float, float, float], ...]
    #: Monotonic capture time the estimate is valid at.
    valid_at_monotonic_s: float


@dataclass(frozen=True)
class BodyCommand:
    """What a planner returns. Not a wire format - see the contract document.

    ``velocity_world_mps`` is in the world frame, metres per second, and its
    ``y`` component is zero for the whole of batch 1 (horizontal motion only,
    proposal section 3.5). ``expires_after_s`` is the frozen
    ``2 / capture_hz``; the receiver falls back to ``Hold()`` past it.
    """

    mode: BodyCommandMode
    velocity_world_mps: tuple[float, float, float]
    expires_after_s: float
    reason: str

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"unsupported body command mode {self.mode!r}")
        for axis, label in zip(self.velocity_world_mps, ("x", "y", "z")):
            _finite(axis, f"velocity_world_mps.{label}")
        if _finite(self.expires_after_s, "expires_after_s") <= 0.0:
            raise ValueError("expires_after_s must be positive")
        if self.mode == "hold" and any(self.velocity_world_mps):
            raise ValueError("a hold command must carry zero velocity")

    @classmethod
    def hold(cls, expires_after_s: float, reason: str) -> "BodyCommand":
        return cls("hold", (0.0, 0.0, 0.0), expires_after_s, reason)

    @classmethod
    def velocity(
        cls,
        vx: float,
        vz: float,
        expires_after_s: float,
        reason: str,
        vy: float = 0.0,
    ) -> "BodyCommand":
        return cls("velocity_world", (vx, vy, vz), expires_after_s, reason)


class BodyPlanner(ABC):
    """The interface M3' policies implement and M4' consumes.

    Implementations must keep :meth:`decide` pure in the BC-BODY1-19 (a)
    sense (no I/O, no wall clock, no truth, no external side effects). The
    stated contract is that a planner is a deterministic function of its
    **ordered input history from a fixed initial state** - the frozen
    hysteresis memory is part of that state - so a reviewer can replay a run
    log in order through a fresh instance and get the same commands back.
    """

    #: Implementations set this to a stable identifier for the run log.
    name: str = "abstract"

    @abstractmethod
    def decide(
        self,
        platform: PlatformState | None,
        estimate: WorldEstimate | None,
        now_monotonic_s: float,
    ) -> BodyCommand:
        """Return the body command for this frame.

        Must return ``hold`` when ``platform`` is ``None`` or when the limit
        margin cannot be constructed. Must not raise for any finite input;
        exception paths belong to the caller, which holds and records them
        (proposal section 2's branch table, BC-BODY1-8).
        """


# ---------------------------------------------------------------------------
# Batch 1a-beta: the corridor artifact reader and the two v1 policies.
# ---------------------------------------------------------------------------

#: Schema of the frozen corridor artifact (BC-BODY1-4). The artifact is built
#: offline by ``tools/build_m3_corridor.py`` and pinned by SHA-256 in
#: ``config/p1-m3-body-001.json``; the runtime side reads this file and nothing
#: else, and the only query below is the permitted "anchor -> candidate body
#: position segment vs prism intersection" plus the proposal section 3.5
#: shorten/hold rule.
CORRIDOR_ARTIFACT_SCHEMA = "p1-m3-body-001-corridor-prisms/v1"

#: Step used by the section 3.5 shorten rule, matching tool 2's frozen
#: quasi-static reduction R4.
CORRIDOR_SHORTEN_STEP_M = 0.05

#: World-axis-aligned prism: ``(min_x, min_y, min_z, max_x, max_y, max_z)``.
CorridorPrism = tuple[float, float, float, float, float, float]


def load_corridor_prisms(path: Path) -> tuple[CorridorPrism, ...]:
    """Load the frozen corridor artifact, failing closed on any deviation.

    The schema, the declared instance count and every coordinate are
    validated; a hand-edited or truncated artifact raises instead of
    silently weakening the corridor check.
    """
    artifact = json.loads(Path(path).read_text(encoding="utf-8"))
    if artifact.get("schema_version") != CORRIDOR_ARTIFACT_SCHEMA:
        raise ValueError(
            f"unsupported corridor artifact schema "
            f"{artifact.get('schema_version')!r}"
        )
    prisms_raw = artifact.get("prisms")
    if not isinstance(prisms_raw, list):
        raise ValueError("corridor artifact prisms must be a list")
    if artifact.get("instance_count") != len(prisms_raw):
        raise ValueError("corridor artifact instance_count does not match prisms")
    prisms: list[CorridorPrism] = []
    for index, entry in enumerate(prisms_raw):
        try:
            prism = tuple(
                _finite(entry[key], f"prisms[{index}].{key}")
                for key in (
                    "min_x_m",
                    "min_y_m",
                    "min_z_m",
                    "max_x_m",
                    "max_y_m",
                    "max_z_m",
                )
            )
        except (TypeError, KeyError) as exception:
            raise ValueError(f"corridor prism {index} is malformed") from exception
        if any(prism[axis] > prism[axis + 3] for axis in range(3)):
            raise ValueError(f"corridor prism {index} has inverted bounds")
        prisms.append(prism)  # type: ignore[arg-type]
    return tuple(prisms)


def segment_intersects_prism(
    start_world_m: Sequence[float],
    end_world_m: Sequence[float],
    prism: CorridorPrism,
    *,
    pad_m: float,
) -> bool:
    """Slab test of a finite segment against a prism inflated by ``pad_m``.

    The inflation is the conservative Minkowski box growth the corridor
    contract uses (it overstates blocking at box corners - the safe
    direction for a clearance check).
    """
    t_enter, t_exit = 0.0, 1.0
    for axis in range(3):
        direction = end_world_m[axis] - start_world_m[axis]
        lower = prism[axis] - pad_m
        upper = prism[axis + 3] + pad_m
        if abs(direction) <= 1e-12:
            if start_world_m[axis] <= lower or start_world_m[axis] >= upper:
                return False
            continue
        t0 = (lower - start_world_m[axis]) / direction
        t1 = (upper - start_world_m[axis]) / direction
        if t0 > t1:
            t0, t1 = t1, t0
        t_enter = max(t_enter, t0)
        t_exit = min(t_exit, t1)
        if t_enter >= t_exit:
            return False
    return True


class HoldBodyPlanner(BodyPlanner):
    """Arm A expressed as a planner: every frame decides ``hold``.

    This is the proposal's "current ``hold_body()`` behaviour" made explicit
    so both arms run through the same per-frame wiring and differ only in the
    planner (proposal section 5.1's pairing clause).
    """

    name = "hold-v1"

    def __init__(self, *, expires_after_s: float):
        self._expires_after_s = _finite(expires_after_s, "expires_after_s")
        if self._expires_after_s <= 0.0:
            raise ValueError("expires_after_s must be positive")

    def decide(
        self,
        platform: PlatformState | None,
        estimate: WorldEstimate | None,
        now_monotonic_s: float,
    ) -> BodyCommand:
        return BodyCommand.hold(self._expires_after_s, "arm_a_hold")


class ThresholdBodyPlanner(BodyPlanner):
    """Proposal section 3.5: threshold body allocation with hysteresis.

    Trigger and direction derive only from the published
    ``camera_forward_world`` (BC-M34-3, BC-BODY1-6): the policy reads the
    limit margin, never the saturation flag, never the estimator and never
    truth. Before a velocity is emitted, the anchor -> candidate body
    position segment is checked against the frozen corridor prisms
    (BC-BODY1-4); on intersection the displacement is shortened along the
    bearing in ``CORRIDOR_SHORTEN_STEP_M`` steps until clear, and if no
    positive displacement clears, the policy holds.

    Hysteresis memory is the single boolean ``_moving`` (BC-BODY1-19 (a)):
    ``False`` at construction, one fresh instance per process/trial, and
    ``decide`` is a deterministic function of its ordered input history from
    that fixed initial state, so replaying a run log in order through a
    fresh instance reproduces the same commands.
    """

    name = "threshold-corridor-v1"

    def __init__(
        self,
        *,
        margin_trigger_deg: float,
        margin_release_deg: float,
        v_cmd_mps: float,
        expires_after_s: float,
        maximum_off_nadir_deg: float,
        anchor_world_m: Sequence[float],
        corridor_prisms: tuple[CorridorPrism, ...] | None = None,
        corridor_radius_m: float | None = None,
    ):
        self._margin_trigger_deg = _finite(margin_trigger_deg, "margin_trigger_deg")
        self._margin_release_deg = _finite(margin_release_deg, "margin_release_deg")
        self._v_cmd_mps = _finite(v_cmd_mps, "v_cmd_mps")
        self._expires_after_s = _finite(expires_after_s, "expires_after_s")
        self._maximum_off_nadir_deg = _finite(
            maximum_off_nadir_deg, "maximum_off_nadir_deg"
        )
        if not 0.0 < self._margin_trigger_deg < self._margin_release_deg:
            raise ValueError("margin_trigger_deg must be below margin_release_deg")
        if self._margin_release_deg >= self._maximum_off_nadir_deg:
            raise ValueError("margin_release_deg must be below the gimbal limit")
        if self._v_cmd_mps <= 0.0 or self._expires_after_s <= 0.0:
            raise ValueError("v_cmd_mps and expires_after_s must be positive")
        anchor = tuple(anchor_world_m)
        if len(anchor) != 3:
            raise ValueError("anchor_world_m must be a three-element vector")
        self._anchor_world_m = tuple(
            _finite(anchor[axis], f"anchor_world_m[{axis}]") for axis in range(3)
        )
        if corridor_prisms is not None and corridor_radius_m is None:
            raise ValueError("corridor prisms require corridor_radius_m")
        if corridor_radius_m is not None:
            corridor_radius_m = _finite(corridor_radius_m, "corridor_radius_m")
            if corridor_radius_m <= 0.0:
                raise ValueError("corridor_radius_m must be positive")
        self._corridor_prisms = corridor_prisms
        self._corridor_radius_m = corridor_radius_m
        self._moving = False

    def decide(
        self,
        platform: PlatformState | None,
        estimate: WorldEstimate | None,
        now_monotonic_s: float,
    ) -> BodyCommand:
        if platform is None:
            return BodyCommand.hold(self._expires_after_s, "no_platform_state")
        if estimate is None:
            # Contract fail-safe (b): an absent estimate must produce hold,
            # even though this policy never reads the estimate (BC-M34-3).
            return BodyCommand.hold(self._expires_after_s, "no_estimate")
        del estimate  # BC-M34-3: the threshold trigger is a platform quantity.
        try:
            margin_deg = platform.limit_margin_deg(self._maximum_off_nadir_deg)
        except (ValueError, OverflowError):
            return BodyCommand.hold(self._expires_after_s, "margin_unconstructible")
        if not math.isfinite(margin_deg):
            return BodyCommand.hold(self._expires_after_s, "margin_unconstructible")

        if margin_deg < self._margin_trigger_deg:
            self._moving = True
            reason = "margin_below_trigger"
        elif margin_deg > self._margin_release_deg:
            self._moving = False
            reason = "margin_above_release"
        else:
            reason = "within_hysteresis_band"
        if not self._moving:
            return BodyCommand.hold(self._expires_after_s, reason)

        bearing = math.radians(platform.bearing_deg)
        direction = (math.sin(bearing), math.cos(bearing))  # world x, z
        step_m = self._v_cmd_mps * self._expires_after_s
        if self._corridor_prisms is not None:
            assert self._corridor_radius_m is not None
            shortened = False
            while step_m > 0.0:
                candidate = (
                    platform.position_world_m[0] + direction[0] * step_m,
                    platform.position_world_m[1],
                    platform.position_world_m[2] + direction[1] * step_m,
                )
                if not self._corridor_blocked(candidate):
                    break
                shortened = True
                step_m -= CORRIDOR_SHORTEN_STEP_M
            else:
                step_m = 0.0
            if step_m <= 0.0:
                return BodyCommand.hold(
                    self._expires_after_s, reason + "+corridor_blocked"
                )
            if shortened:
                reason += "+corridor_shortened"
        speed = step_m / self._expires_after_s
        return BodyCommand.velocity(
            direction[0] * speed,
            direction[1] * speed,
            self._expires_after_s,
            reason,
        )

    def _corridor_blocked(self, candidate_world_m: Sequence[float]) -> bool:
        assert self._corridor_prisms is not None
        assert self._corridor_radius_m is not None
        for prism in self._corridor_prisms:
            if segment_intersects_prism(
                self._anchor_world_m,
                candidate_world_m,
                prism,
                pad_m=self._corridor_radius_m,
            ):
                return True
        return False
