"""P1-ENG-FRAME-001 Part T: the scenario tether switch and its safety bounds.

The proposal's section 3.1 adds two optional keys under ``drone`` to the
``tethered-scenario/v1`` schema:

* ``tether_enabled`` (bool). A missing key means the tether is **on**, which
  is the exact pre-existing behaviour, so every existing scenario file,
  frozen artifact and historical result keeps its meaning.
* ``geofence_xz_m`` (``{min_x, max_x, min_z, max_z}``, Unity world metres).
  Whenever it is present it must be finite, satisfy ``min < max`` on both
  axes and contain the home position (the ``anchor_world_m`` x/z). With the
  tether off it is mandatory.

The rules mirror ``ScenarioConfig.FromJsonStrict`` (which reads both keys
from the direct members of the ``drone`` object only) and
``ScenarioConfig.Normalize`` on the Unity side; the AC-1 fixture tests (the
closed set plus the explicit-value and key-context tables) pin both sides to
the same verdicts, including the refusal of a non-bool ``tether_enabled``
and of an explicitly written non-finite or non-numeric geofence bound.

This module also owns the Python-side resolution of the scenario Unity
actually loads (proposal section 3.11, entry 6): the runtime override
``runtime/scenario_config.json`` wins when it exists, otherwise the
versioned default ``config/scenario.untethered.json``. That is the same
order as ``ScenarioConfig.Load()``. ``controller/language_loop.py`` keeps its
own, older resolver untouched (proposal AC-18/AC-29).

Nothing here reads evaluator output or the target's path; the module only
parses operator-declared scenario settings (proposal AC-22).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]

#: Versioned no-override fallback (proposal section 3.11, entries 1 and 6).
UNTETHERED_SCENARIO_PATH = PROJECT_ROOT / "config" / "scenario.untethered.json"

#: Runtime override file name, identical to ``ScenarioConfig.Load()``.
RUNTIME_OVERRIDE_NAME = "scenario_config.json"

GEOFENCE_KEYS: tuple[str, ...] = ("min_x", "max_x", "min_z", "max_z")


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


@dataclass(frozen=True)
class Geofence:
    """Axis-aligned horizontal operating area, world x/z metres."""

    min_x: float
    max_x: float
    min_z: float
    max_z: float

    def contains(self, x: float, z: float) -> bool:
        return self.min_x <= x <= self.max_x and self.min_z <= z <= self.max_z

    def as_dict(self) -> dict[str, float]:
        return {
            "min_x": self.min_x,
            "max_x": self.max_x,
            "min_z": self.min_z,
            "max_z": self.max_z,
        }


@dataclass(frozen=True)
class TetherSettings:
    """Parsed tether switch and the drone limits the plant enforces."""

    tether_enabled: bool
    geofence: Geofence | None
    anchor_world_m: tuple[float, float, float]
    tether_length_m: float
    initial_altitude_m: float
    minimum_altitude_m: float
    maximum_altitude_m: float
    maximum_speed_mps: float
    maximum_acceleration_mps2: float

    def reach_radius_m(self, height_above_home_m: float) -> float | None:
        """Horizontal tether reach at a height, ``sqrt(L^2 - h^2)``.

        ``None`` with the tether off: the reach circle is not a constraint
        in that mode (proposal section 3.4, per-row modes).
        """
        if not self.tether_enabled:
            return None
        length = self.tether_length_m
        return math.sqrt(max(0.0, length * length - height_above_home_m ** 2))


def parse_geofence(raw: Any, anchor_world_m: tuple[float, float, float]) -> Geofence:
    if not isinstance(raw, Mapping):
        raise ValueError("drone.geofence_xz_m must be an object")
    missing = [key for key in GEOFENCE_KEYS if key not in raw]
    if missing:
        raise ValueError(f"drone.geofence_xz_m is missing {missing}")
    values = {
        key: _number(raw[key], f"drone.geofence_xz_m.{key}") for key in GEOFENCE_KEYS
    }
    fence = Geofence(**values)
    if not (fence.min_x < fence.max_x and fence.min_z < fence.max_z):
        raise ValueError("drone.geofence_xz_m must satisfy min < max on both axes")
    if not fence.contains(anchor_world_m[0], anchor_world_m[2]):
        raise ValueError(
            "drone.geofence_xz_m must contain the home (anchor_world_m) position"
        )
    return fence


def parse_tether_settings(scenario: Mapping[str, Any]) -> TetherSettings:
    """Apply the section 3.1 rules to a ``tethered-scenario/v1`` document.

    Raises ``ValueError`` on every rejected fixture of AC-1: a non-bool
    switch, a malformed geofence, or the tether off without a geofence.
    """
    if scenario.get("schema_version") != "tethered-scenario/v1":
        raise ValueError(
            f"unsupported scenario schema {scenario.get('schema_version')!r}"
        )
    anchor_raw = scenario.get("anchor_world_m")
    if not isinstance(anchor_raw, Mapping):
        raise ValueError("scenario anchor_world_m must be an object")
    anchor = tuple(
        _number(anchor_raw.get(axis), f"anchor_world_m.{axis}")
        for axis in ("x", "y", "z")
    )
    drone = scenario.get("drone")
    if not isinstance(drone, Mapping):
        raise ValueError("scenario drone must be an object")
    if "tether_enabled" in drone:
        tether_enabled = drone["tether_enabled"]
        if not isinstance(tether_enabled, bool):
            raise ValueError("drone.tether_enabled must be a JSON boolean")
    else:
        tether_enabled = True
    geofence = None
    if "geofence_xz_m" in drone:
        geofence = parse_geofence(drone["geofence_xz_m"], anchor)  # type: ignore[arg-type]
    elif not tether_enabled:
        raise ValueError(
            "drone.geofence_xz_m is required when drone.tether_enabled is false"
        )

    def positive(key: str) -> float:
        value = _number(drone.get(key), f"drone.{key}")
        if value <= 0.0:
            raise ValueError(f"drone.{key} must be positive")
        return value

    tether_length = positive("tether_length_m")
    minimum = positive("minimum_altitude_m")
    maximum = positive("maximum_altitude_m")
    initial = _number(drone.get("initial_altitude_m"), "drone.initial_altitude_m")
    # Same clamps as ScenarioConfig.Normalize: the tether caps the altitude
    # band only while it is enabled.
    if tether_enabled:
        minimum = min(max(minimum, 0.1), tether_length)
        maximum = min(max(maximum, minimum), tether_length)
    else:
        minimum = max(0.1, minimum)
        maximum = max(minimum, maximum)
    initial = min(max(initial, minimum), maximum)
    return TetherSettings(
        tether_enabled=tether_enabled,
        geofence=geofence,
        anchor_world_m=anchor,  # type: ignore[arg-type]
        tether_length_m=tether_length,
        initial_altitude_m=initial,
        minimum_altitude_m=minimum,
        maximum_altitude_m=maximum,
        maximum_speed_mps=positive("maximum_speed_mps"),
        maximum_acceleration_mps2=positive("maximum_acceleration_mps2"),
    )


def safety_bounds(settings: TetherSettings) -> dict[str, Any]:
    """Plant-side safety bounds in force for a scenario (proposal 3.4).

    With the tether on, the identity records the reach radius at the
    initial altitude and no fence (unless the file declares one); with the
    tether off it records the fence and no reach circle (AC-10).
    """
    initial = settings.initial_altitude_m
    return {
        "tether_enabled": settings.tether_enabled,
        "geofence_xz_m": (
            settings.geofence.as_dict() if settings.geofence is not None else None
        ),
        "tether_length_m": (
            settings.tether_length_m if settings.tether_enabled else None
        ),
        "reach_radius_at_initial_altitude_m": settings.reach_radius_m(initial),
        "altitude_hold_m": initial,
        "altitude_limits_m": [
            settings.minimum_altitude_m,
            settings.maximum_altitude_m,
        ],
        "maximum_speed_mps": settings.maximum_speed_mps,
        "maximum_acceleration_mps2": settings.maximum_acceleration_mps2,
    }


def effective_scenario_path(runtime: Path) -> Path:
    """The scenario file Unity's ``ScenarioConfig.Load()`` will use.

    ``runtime/scenario_config.json`` when it exists, otherwise the
    versioned default ``config/scenario.untethered.json`` (same order as
    Unity; proposal section 3.11 entry 6, AC-29).
    """
    override = Path(runtime) / RUNTIME_OVERRIDE_NAME
    if override.is_file():
        return override
    return UNTETHERED_SCENARIO_PATH


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
