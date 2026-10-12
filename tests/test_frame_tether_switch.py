"""P1-ENG-FRAME-001 Part T: tether switch, untethered default and bounds.

Covers the Python half of the proposal's Part T acceptance items:

* AC-1  - the section 3.1 parser gives the same verdicts as Unity's
          ``ScenarioConfig`` on the closed fixture set (the Edit Mode half is
          ``ScenarioTetherSwitchTests``) and rejects a non-bool switch;
* AC-8  - the frozen threshold constructor is unchanged on a tethered
          scenario and refuses a tether-off scenario;
* AC-9  - ``config/scenario.untethered.json`` differs from the old default
          only in the section 3.1 key set;
* AC-10 - the effective safety bounds equal the section 3.4 table and are
          written into the run manifest identity;
* AC-29 - the Python-side effective scenario resolver uses Unity's order.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from controller.body_planner import (  # noqa: E402
    HoldBodyPlanner,
    PlatformState,
    ThresholdBodyPlanner,
    WorldEstimate,
    load_corridor_prisms,
)
from controller.scenario_tether import (  # noqa: E402
    UNTETHERED_SCENARIO_PATH,
    effective_scenario_path,
    parse_tether_settings,
    safety_bounds,
)
from controller.track_loop import _build_body_runtime  # noqa: E402

BODY_CONFIG_PATH = PROJECT_ROOT / "config" / "p1-m3-body-001.json"
FRAME_CONFIG_PATH = PROJECT_ROOT / "config" / "p1-eng-frame-001-body.json"
DEFAULT_SCENARIO_PATH = PROJECT_ROOT / "config" / "scenario.default.json"
UNTETHERED_PATH = PROJECT_ROOT / "config" / "scenario.untethered.json"
REPLAY_EVIDENCE_PATH = PROJECT_ROOT / "docs" / "evidence" / "P1-ENG-FRAME-001-replay.json"

VALID_FENCE = {"min_x": 110.0, "max_x": 190.0, "min_z": 50.0, "max_z": 130.0}
INVERTED_FENCE = {"min_x": 190.0, "max_x": 110.0, "min_z": 50.0, "max_z": 130.0}
FENCE_WITHOUT_HOME = {"min_x": 140.0, "max_x": 190.0, "min_z": 50.0, "max_z": 130.0}

#: Section 3.4 table for the untethered scenario (proposal AC-10).
SECTION_3_4_UNTETHERED = {
    "tether_enabled": False,
    "geofence_xz_m": VALID_FENCE,
    "tether_length_m": None,
    "reach_radius_at_initial_altitude_m": None,
    "altitude_hold_m": 25.0,
    "altitude_limits_m": [8.0, 32.0],
    "maximum_speed_mps": 4.0,
    "maximum_acceleration_mps2": 4.0,
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _default_document() -> dict:
    return json.loads(DEFAULT_SCENARIO_PATH.read_text(encoding="utf-8"))


def _with_drone(**extra) -> dict:
    document = _default_document()
    document["drone"].update(copy.deepcopy(extra))
    return document


def _closed_fixture_set() -> list[tuple[str, dict, bool, bool, bool]]:
    """Same names, inputs and verdicts as the Edit Mode
    ``ScenarioTetherSwitchTests.ClosedFixtureSet_VerdictsMatchThePythonParser``:
    ``(name, document, accepted, tether_enabled, has_fence)``."""
    return [
        ("missing", _default_document(), True, True, False),
        ("true", _with_drone(tether_enabled=True), True, True, False),
        ("true+fence", _with_drone(tether_enabled=True, geofence_xz_m=VALID_FENCE), True, True, True),
        ("false+fence", _with_drone(tether_enabled=False, geofence_xz_m=VALID_FENCE), True, False, True),
        ("false+no-fence", _with_drone(tether_enabled=False), False, False, False),
        (
            "false+inverted-fence",
            _with_drone(tether_enabled=False, geofence_xz_m=INVERTED_FENCE),
            False,
            False,
            False,
        ),
        (
            "false+fence-without-home",
            _with_drone(tether_enabled=False, geofence_xz_m=FENCE_WITHOUT_HOME),
            False,
            False,
            False,
        ),
    ]


DRONE_TAIL = '"maximum_acceleration_mps2": 4.0'
GIMBAL_TAIL = '"slew_rate_deg_per_second": 120.0'
VALID_FENCE_TEXT = (
    '"geofence_xz_m": { "min_x": 110.0, "max_x": 190.0, "min_z": 50.0, "max_z": 130.0 }'
)
ALL_NAN_FENCE_TEXT = (
    '"geofence_xz_m": { "min_x": NaN, "max_x": NaN, "min_z": NaN, "max_z": NaN }'
)


def _insert_after(text: str, tail: str, extra: str) -> str:
    if text.count(tail) != 1:
        raise AssertionError(f"insertion anchor {tail!r} must occur exactly once")
    return text.replace(tail, tail + ", " + extra)


def _default_text() -> str:
    return DEFAULT_SCENARIO_PATH.read_text(encoding="utf-8")


def _drone_text(extra: str) -> str:
    return _insert_after(_default_text(), DRONE_TAIL, extra)


def _fence_text(min_x: str, max_x: str, min_z: str, max_z: str) -> str:
    return (
        f'"geofence_xz_m": {{ "min_x": {min_x}, "max_x": {max_x}, '
        f'"min_z": {min_z}, "max_z": {max_z} }}'
    )


#: C1@K2返工 fixtures outside the AC-1 closed set, as JSON text (Python's
#: ``json`` reads ``NaN``/``Infinity`` and turns ``1e999`` into ``inf``).
#: Same names, inserted text and verdicts as the Edit Mode
#: ``ScenarioTetherSwitchTests.ExplicitValueFixtures`` /
#: ``KeyContextFixtures``; keep both tables in sync.
#: ``(name, text, accepted, tether_enabled, has_fence)``.
EXPLICIT_VALUE_FIXTURES: tuple[tuple[str, str, bool, bool, bool], ...] = (
    ("fence-all-nan", _drone_text(ALL_NAN_FENCE_TEXT), False, False, False),
    ("true+fence-all-nan", _drone_text('"tether_enabled": true, ' + ALL_NAN_FENCE_TEXT), False, False, False),
    ("false+fence-all-nan", _drone_text('"tether_enabled": false, ' + ALL_NAN_FENCE_TEXT), False, False, False),
    ("true+fence-one-nan", _drone_text('"tether_enabled": true, ' + _fence_text("NaN", "190.0", "50.0", "130.0")), False, False, False),
    ("true+fence-infinity", _drone_text('"tether_enabled": true, ' + _fence_text("110.0", "Infinity", "50.0", "130.0")), False, False, False),
    ("true+fence-negative-infinity", _drone_text('"tether_enabled": true, ' + _fence_text("110.0", "190.0", "-Infinity", "130.0")), False, False, False),
    ("true+fence-overflow", _drone_text('"tether_enabled": true, ' + _fence_text("110.0", "190.0", "50.0", "1e999")), False, False, False),
    ("true+fence-all-bool", _drone_text('"tether_enabled": true, ' + _fence_text("true", "true", "false", "false")), False, False, False),
    ("true+fence-string-bound", _drone_text('"tether_enabled": true, ' + _fence_text('"110"', "190.0", "50.0", "130.0")), False, False, False),
    ("true+fence-null-bound", _drone_text('"tether_enabled": true, ' + _fence_text("null", "190.0", "50.0", "130.0")), False, False, False),
    ("true+fence-null", _drone_text('"tether_enabled": true, "geofence_xz_m": null'), False, False, False),
    ("true+fence-array", _drone_text('"tether_enabled": true, "geofence_xz_m": [110.0, 190.0, 50.0, 130.0]'), False, False, False),
    ("true+fence-missing-bound", _drone_text('"tether_enabled": true, "geofence_xz_m": { "min_x": 110.0, "max_x": 190.0, "min_z": 50.0 }'), False, False, False),
    ("switch-number+fence", _drone_text('"tether_enabled": 0, ' + VALID_FENCE_TEXT), False, False, False),
    ("switch-string+fence", _drone_text('"tether_enabled": "false", ' + VALID_FENCE_TEXT), False, False, False),
    ("switch-null", _drone_text('"tether_enabled": null'), False, False, False),
    ("true+fence-integer-bounds", _drone_text('"tether_enabled": true, ' + _fence_text("110", "190", "50", "130")), True, True, True),
)

KEY_CONTEXT_FIXTURES: tuple[tuple[str, str, bool, bool, bool], ...] = (
    (
        "keys-in-another-object",
        _insert_after(_default_text(), GIMBAL_TAIL, '"tether_enabled": false, "geofence_xz_m": { "note": 1 }'),
        True,
        True,
        False,
    ),
    (
        "keys-nested-in-drone",
        _drone_text('"notes": { "tether_enabled": false, "geofence_xz_m": { "min_x": NaN } }'),
        True,
        True,
        False,
    ),
    (
        "keys-in-a-string",
        _drone_text(r'"notes": "\"tether_enabled\": false, \"geofence_xz_m\": {}"'),
        True,
        True,
        False,
    ),
    (
        "false+fence-in-another-object",
        _insert_after(_drone_text('"tether_enabled": false'), GIMBAL_TAIL, VALID_FENCE_TEXT),
        False,
        False,
        False,
    ),
)


class TetherSwitchParserTests(unittest.TestCase):
    """AC-1 (Python half)."""

    def _assert_text_fixture_verdicts(self, fixtures) -> None:
        for name, text, accepted, tether_enabled, has_fence in fixtures:
            with self.subTest(name):
                document = json.loads(text)
                if not accepted:
                    with self.assertRaises(ValueError):
                        parse_tether_settings(document)
                    continue
                settings = parse_tether_settings(document)
                self.assertIs(settings.tether_enabled, tether_enabled)
                self.assertEqual(settings.geofence is not None, has_fence)
                if has_fence:
                    self.assertEqual(settings.geofence.as_dict(), VALID_FENCE)

    def test_explicit_key_values_match_unity(self):
        """C1@K2返工: explicit non-finite/non-numeric geofences and non-bool
        switches are refused in both modes (Edit Mode
        ``ExplicitTetherKeyValues_AreRefusedLikeThePythonParser``)."""
        self._assert_text_fixture_verdicts(EXPLICIT_VALUE_FIXTURES)

    def test_keys_outside_the_drone_object_mean_missing(self):
        """C1@K2返工: only direct members of ``drone`` count (Edit Mode
        ``TetherKeysOutsideTheDroneObject_MeanMissing``)."""
        self._assert_text_fixture_verdicts(KEY_CONTEXT_FIXTURES)

    def test_text_fixture_names_are_unique_and_disjoint_from_the_closed_set(self):
        names = [fixture[0] for fixture in EXPLICIT_VALUE_FIXTURES + KEY_CONTEXT_FIXTURES]
        self.assertEqual(len(names), len(set(names)))
        closed = {fixture[0] for fixture in _closed_fixture_set()}
        self.assertFalse(closed & set(names))

    def test_closed_fixture_set_verdicts(self):
        for name, document, accepted, tether_enabled, has_fence in _closed_fixture_set():
            with self.subTest(name):
                if not accepted:
                    with self.assertRaises(ValueError):
                        parse_tether_settings(document)
                    continue
                settings = parse_tether_settings(document)
                self.assertIs(settings.tether_enabled, tether_enabled)
                self.assertEqual(settings.geofence is not None, has_fence)
                if has_fence:
                    self.assertEqual(settings.geofence.as_dict(), VALID_FENCE)

    def test_non_bool_switch_is_rejected(self):
        for value in ("false", "true", 0, 1, None, 0.0, [], {}):
            with self.subTest(value=value):
                document = _with_drone(tether_enabled=value, geofence_xz_m=VALID_FENCE)
                with self.assertRaises(ValueError):
                    parse_tether_settings(document)

    def test_malformed_fence_values_are_rejected(self):
        for key in VALID_FENCE:
            for bad in (float("nan"), float("inf"), "110", True, None):
                with self.subTest(key=key, bad=bad):
                    fence = dict(VALID_FENCE)
                    fence[key] = bad
                    with self.assertRaises(ValueError):
                        parse_tether_settings(
                            _with_drone(tether_enabled=False, geofence_xz_m=fence)
                        )
        fence = dict(VALID_FENCE)
        del fence["max_z"]
        with self.assertRaises(ValueError):
            parse_tether_settings(_with_drone(tether_enabled=False, geofence_xz_m=fence))

    def test_tether_off_altitude_band_is_not_capped_by_cable(self):
        settings = parse_tether_settings(
            _with_drone(
                tether_enabled=False,
                geofence_xz_m=VALID_FENCE,
                tether_length_m=10.0,
            )
        )
        self.assertEqual(settings.maximum_altitude_m, 32.0)
        tethered = parse_tether_settings(_with_drone(tether_length_m=10.0))
        self.assertEqual(tethered.maximum_altitude_m, 10.0)


def _platform(theta_deg: float, yaw_deg: float, position=(132.0, 25.2, 117.0)) -> PlatformState:
    tilt = math.radians(theta_deg)
    yaw = math.radians(yaw_deg)
    return PlatformState(
        frame_id=1,
        capture_monotonic_s=1.0,
        position_world_m=position,
        camera_forward_world=(
            math.sin(yaw) * math.sin(tilt),
            -math.cos(tilt),
            math.cos(yaw) * math.sin(tilt),
        ),
        gimbal_saturated=theta_deg >= 45.0,
        tether_saturated=False,
    )


def _estimate() -> WorldEstimate:
    return WorldEstimate(
        mean=(140.0, 100.0, 1.0, 0.0),
        covariance=tuple(
            tuple(1.0 if row == col else 0.0 for col in range(4)) for row in range(4)
        ),
        valid_at_monotonic_s=1.0,
    )


def _threshold_sequence() -> list[PlatformState]:
    states = []
    position = [132.0, 25.2, 117.0]
    for index in range(120):
        theta = 20.0 + 25.0 * math.sin(index / 9.0)
        yaw = (index * 7.0) % 360.0
        position[0] += 0.3 * math.sin(index / 5.0)
        position[2] -= 0.2 * math.cos(index / 7.0)
        states.append(_platform(theta, yaw, tuple(position)))
    return states


class ThresholdConstructorSwitchTests(unittest.TestCase):
    """AC-8: the threshold branch is unchanged when tethered, refused when not."""

    def _reference_planner(self) -> ThresholdBodyPlanner:
        # Pre-change construction, value for value (BODY-001 config +
        # the frozen scenario's gimbal limit and anchor).
        return ThresholdBodyPlanner(
            margin_trigger_deg=10.0,
            margin_release_deg=20.0,
            v_cmd_mps=4.0,
            expires_after_s=0.4,
            maximum_off_nadir_deg=45.0,
            anchor_world_m=(132.0, 0.2, 117.0),
            corridor_prisms=load_corridor_prisms(
                PROJECT_ROOT / "config" / "p1-m3-body-001-corridor-prisms.json"
            ),
            corridor_radius_m=1.0,
        )

    def _build(self, scenario_path: Path, policy: str = "threshold"):
        return _build_body_runtime(
            BODY_CONFIG_PATH,
            scenario_path,
            policy,
            scenario_id=json.loads(scenario_path.read_text())["scenario_id"],
            ground_plane_y_m=0.2,
        )

    def test_tethered_identity_and_decisions_are_unchanged(self):
        for label, document in (
            ("field missing", _default_document()),
            ("explicit true", _with_drone(tether_enabled=True)),
        ):
            with self.subTest(label), tempfile.TemporaryDirectory() as directory:
                scenario_path = Path(directory) / "scenario.json"
                if label == "field missing":
                    scenario_path = DEFAULT_SCENARIO_PATH
                else:
                    scenario_path.write_text(json.dumps(document), encoding="utf-8")
                planner, _, expires, identity = self._build(scenario_path)
                self.assertEqual(
                    identity,
                    {
                        "policy": "threshold",
                        "planner": "threshold-corridor-v1",
                        "contract_version": "body-planner-contract/v1",
                        "config_path": str(BODY_CONFIG_PATH),
                        "config_sha256": _sha256(BODY_CONFIG_PATH),
                        "scenario_config_sha256": _sha256(scenario_path),
                        "expires_after_s": 0.4,
                    },
                )
                self.assertEqual(expires, 0.4)
                reference = self._reference_planner()
                moving = 0
                for state in _threshold_sequence():
                    actual = planner.decide(state, _estimate(), 1.0)
                    expected = reference.decide(state, _estimate(), 1.0)
                    self.assertEqual(actual, expected)
                    moving += actual.mode == "velocity_world"
                self.assertGreater(moving, 0, "the sequence must exercise the moving branch")

    def test_tether_off_scenario_refuses_the_threshold_policy(self):
        with self.assertRaisesRegex(ValueError, "tethered scenario"):
            self._build(UNTETHERED_PATH)

    def test_hold_policy_is_unaffected_by_the_switch(self):
        for path in (DEFAULT_SCENARIO_PATH, UNTETHERED_PATH):
            with self.subTest(path.name):
                planner, _, _, identity = self._build(path, "hold")
                self.assertIsInstance(planner, HoldBodyPlanner)
                self.assertEqual(identity["policy"], "hold")
                self.assertNotIn("safety_bounds", identity)


class UntetheredScenarioDiffTests(unittest.TestCase):
    """AC-9: only the section 3.1 key set differs from the old default."""

    def test_difference_is_exactly_the_section_3_1_key_set(self):
        untethered = json.loads(UNTETHERED_PATH.read_text(encoding="utf-8"))
        default = _default_document()

        differences: list[str] = []

        def walk(a, b, prefix: str) -> None:
            if isinstance(a, dict) and isinstance(b, dict):
                for key in sorted(set(a) | set(b)):
                    path = f"{prefix}.{key}" if prefix else key
                    if key not in a or key not in b:
                        differences.append(path)
                    else:
                        walk(a[key], b[key], path)
            elif a != b or type(a) is not type(b):
                differences.append(prefix)

        walk(untethered, default, "")
        self.assertEqual(
            sorted(differences),
            ["drone.geofence_xz_m", "drone.tether_enabled", "scenario_id"],
        )
        self.assertEqual(untethered["scenario_id"], "deterministic-loop-untethered")
        self.assertIs(untethered["drone"]["tether_enabled"], False)
        self.assertEqual(untethered["drone"]["geofence_xz_m"], VALID_FENCE)


class SafetyBoundsTests(unittest.TestCase):
    """AC-10: effective bounds equal the section 3.4 table."""

    def test_untethered_bounds_equal_section_3_4(self):
        settings = parse_tether_settings(
            json.loads(UNTETHERED_PATH.read_text(encoding="utf-8"))
        )
        self.assertEqual(safety_bounds(settings), SECTION_3_4_UNTETHERED)

    def test_tethered_bounds_record_reach_circle_and_no_fence(self):
        bounds = safety_bounds(parse_tether_settings(_default_document()))
        self.assertIs(bounds["tether_enabled"], True)
        self.assertIsNone(bounds["geofence_xz_m"])
        self.assertAlmostEqual(
            bounds["reach_radius_at_initial_altitude_m"], math.sqrt(35.0**2 - 25.0**2)
        )

    def test_standoff_manifest_identity_carries_the_bounds(self):
        with tempfile.TemporaryDirectory() as runtime:
            _, _, _, identity = _build_body_runtime(
                FRAME_CONFIG_PATH,
                UNTETHERED_PATH,
                "standoff",
                scenario_id="deterministic-loop-untethered",
                ground_plane_y_m=0.2,
                runtime=Path(runtime),
            )
        bounds = identity["safety_bounds"]
        for key, value in SECTION_3_4_UNTETHERED.items():
            self.assertEqual(bounds[key], value, key)
        self.assertEqual(bounds["obstacle_pad_m"], 2.1)
        self.assertEqual(bounds["d_plaus_m"], 65.0)
        self.assertEqual(bounds["expires_after_s"], 0.4)
        self.assertEqual(bounds["command_v_max_mps"], 4.0)
        self.assertEqual(identity["effective_scenario_path"], str(UNTETHERED_SCENARIO_PATH))
        self.assertEqual(identity["effective_scenario_sha256"], _sha256(UNTETHERED_PATH))

    def test_replay_evidence_records_the_offline_clearance_check(self):
        evidence = json.loads(REPLAY_EVIDENCE_PATH.read_text(encoding="utf-8"))
        check = evidence["safety_bounds"]["obstacle_clearance"]
        self.assertEqual(check["fence_xz_m"], VALID_FENCE)
        self.assertAlmostEqual(check["obstacle_pad_m"], 2.1)
        at_25 = check["altitudes"]["25"]
        self.assertTrue(at_25["clear"])
        self.assertLess(
            check["max_prism_top_in_fence_m"] + 2.1, at_25["body_world_height_m"]
        )
        self.assertGreater(len(check["altitudes"]["15"]["conflicting_prisms"]), 0)


class EffectiveScenarioPathTests(unittest.TestCase):
    """AC-29: override first, else the versioned untethered default."""

    def test_without_override_resolves_to_untethered_default(self):
        with tempfile.TemporaryDirectory() as runtime:
            self.assertEqual(effective_scenario_path(Path(runtime)), UNTETHERED_PATH)
        self.assertEqual(UNTETHERED_SCENARIO_PATH, UNTETHERED_PATH)

    def test_existing_override_wins(self):
        with tempfile.TemporaryDirectory() as runtime:
            override = Path(runtime) / "scenario_config.json"
            override.write_bytes(DEFAULT_SCENARIO_PATH.read_bytes())
            self.assertEqual(effective_scenario_path(Path(runtime)), override)

    def test_resolver_does_not_use_language_loop(self):
        tree = ast.parse(
            (PROJECT_ROOT / "controller" / "scenario_tether.py").read_text(
                encoding="utf-8"
            )
        )
        imported = set()
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
            elif isinstance(node, (ast.Name, ast.Attribute)):
                names.add(node.id if isinstance(node, ast.Name) else node.attr)
        self.assertFalse(any("language_loop" in module for module in imported))
        self.assertNotIn("effective_scenario_document", names)


if __name__ == "__main__":
    unittest.main()
