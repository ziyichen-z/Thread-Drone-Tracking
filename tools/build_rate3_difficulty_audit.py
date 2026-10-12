"""P1-M2-RATE-003 Amendment DR-B B2: difficulty-config envelope audit.

The SCENE-004 envelope tool gates five quantities. Two of them
(`loop_period_s` and `distractor_opportunities`) are derived from
`target.speed_mps` and therefore cannot be satisfied by a difficulty
config *by construction* — D2 = 8.0 m/s gives a 7.7678 s loop against a
[30, 45] s gate that encodes the D1 scouting cadence, not a safety or
validity property.

BC-DRB-2/BC-DRB-3 partition the audit instead of exempting it:

* **must-pass** (speed independent): `max_slant_range_m`,
  `max_off_nadir_deg`, `predicted_min_side_p05_px` and the accepted
  SCENE-002 route-legality audit. Each must pass its own gate **and**
  equal the archived D1 baseline value for value.
* **record-only** (speed derived): `loop_period_s` and
  `distractor_opportunities`, reported as
  `{difficulty value, D1 baseline value, delta}` triples. They never
  enter the overall status.

Overall status is computed on the must-pass set only, reusing the
`ENVELOPE_OK` / `ENVELOPE_OUT_OF_BOUNDS` value domain.

Equality semantics are BC-DRB-2 verbatim: bit-equal when the recomputed
value keeps the same numeric type and serialised representation, with a
single degraded rule `abs(difficulty - archived_d1) <= 1e-9` for finite
floats. Integers, booleans, strings, enums, array lengths, key sets and
canonical order must match exactly, with no float fallback. Any missing
field or non-finite value fails closed.

The archived D1 baseline artifacts are read only; this tool never
regenerates or edits them.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

from tools.build_scene004_geometry import SCENARIO_PATH as D1_SCENARIO_PATH
from tools.build_scene004_geometry import build_geometry
from tools.run_detector_scouting import sha256_file
from tools.run_track_experiment import PROJECT_ROOT

WORK_ID = "P1-M2-RATE-003"
ARTIFACT_SCHEMA = "p1-rate3-difficulty-audit/v1"
ROAD_AUDIT_SCHEMA = "p1-scene-road-audit/v1"
D1_GEOMETRY_ARTIFACT_PATH = (
    PROJECT_ROOT / "docs" / "evidence" / "P1-SCENE-004-geometry.json"
)
D1_ROAD_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "evidence" / "P1-M2-RATE-003-d1-road-audit.json"
)

# BC-DRB-2: the only degraded rule, and only for finite floats.
FLOAT_ABS_TOLERANCE = 1e-9

MUST_PASS_GATES = (
    "max_slant_range_m",
    "max_off_nadir_deg",
    "predicted_min_side_p05_px",
)
RECORD_ONLY_GATES = ("loop_period_s", "distractor_opportunities")

# Speed-derived; excluded from the geometry value-equality sweep and
# reported as a record-only triple instead.
SPEED_DERIVED_GEOMETRY_KEYS = ("loop_period_s",)

# BC-DRB-3: the exact `p1-scene-road-audit/v1` field set compared against
# the archived D1 report. `scenario_id` is the sole exemption.
ROAD_AUDIT_COMPARED_FIELDS = (
    "schema_version",
    "status",
    "route_sample_count",
    "road_violation_count",
    "audited_obstacle_count",
    "overhead_exemption_count",
    "obstacle_violation_count",
    "vehicle_violation_count",
    "prop_violation_count",
    "nature_violation_count",
    "building_violation_count",
    "other_violation_count",
    "road_violations",
    "obstacle_violations",
)
ROAD_AUDIT_VIOLATION_COUNT_FIELDS = (
    "road_violation_count",
    "obstacle_violation_count",
    "vehicle_violation_count",
    "prop_violation_count",
    "nature_violation_count",
    "building_violation_count",
    "other_violation_count",
)
ROAD_AUDIT_VIOLATION_ARRAY_FIELDS = ("road_violations", "obstacle_violations")

# The declared difficulty-config difference (proposal "Inputs"): only the
# scenario identity and the target speed may differ from the D1 baseline.
DECLARED_CONFIG_DIFFERENCE_KEYS = ("scenario_id", "target.speed_mps")


class DifficultyAuditError(ValueError):
    """Raised when an audit input cannot be read at all."""


def _display_path(path: Path | None) -> str | None:
    """Repository-relative when possible, so the artifact stays portable.

    BC-B2-CQ2 requires the audit to be reproducible from the repository
    root; an absolute path baked into the committed artifact would differ
    on every checkout and make a reviewer's re-run look like a mismatch.
    """

    if path is None:
        return None
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DifficultyAuditError(f"{path} must contain a JSON object")
    return value


def _is_real_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _float_repr(value: float) -> str:
    # Python's float repr round-trips exactly, so equal reprs mean the two
    # doubles have the same bits (NaN/inf are rejected before this point).
    return repr(float(value))


def typed_equality_findings(
    difficulty: Any,
    baseline: Any,
    path: str = "",
    *,
    findings: list[str] | None = None,
) -> list[str]:
    """BC-DRB-2 typed equality; returns one finding per mismatch."""

    if findings is None:
        findings = []
    label = path or "<root>"

    if isinstance(difficulty, bool) or isinstance(baseline, bool):
        if not (isinstance(difficulty, bool) and isinstance(baseline, bool)):
            findings.append(f"{label}: boolean type mismatch")
        elif difficulty != baseline:
            findings.append(f"{label}: {difficulty!r} != {baseline!r}")
        return findings

    if _is_real_number(difficulty) or _is_real_number(baseline):
        if not (_is_real_number(difficulty) and _is_real_number(baseline)):
            findings.append(f"{label}: numeric type mismatch")
            return findings
        if isinstance(difficulty, int) and isinstance(baseline, int):
            if difficulty != baseline:
                findings.append(f"{label}: {difficulty!r} != {baseline!r}")
            return findings
        if isinstance(difficulty, int) != isinstance(baseline, int):
            # int vs float is a representation change, not a float recompute.
            findings.append(f"{label}: numeric representation changed")
            return findings
        if not math.isfinite(float(difficulty)) or not math.isfinite(
            float(baseline)
        ):
            findings.append(f"{label}: non-finite value fails closed")
            return findings
        if _float_repr(difficulty) == _float_repr(baseline):
            return findings
        if abs(float(difficulty) - float(baseline)) <= FLOAT_ABS_TOLERANCE:
            return findings
        findings.append(
            f"{label}: {difficulty!r} != {baseline!r} beyond "
            f"{FLOAT_ABS_TOLERANCE}"
        )
        return findings

    if isinstance(difficulty, str) or isinstance(baseline, str):
        if not (isinstance(difficulty, str) and isinstance(baseline, str)):
            findings.append(f"{label}: string type mismatch")
        elif difficulty != baseline:
            findings.append(f"{label}: {difficulty!r} != {baseline!r}")
        return findings

    if isinstance(difficulty, list) or isinstance(baseline, list):
        if not (isinstance(difficulty, list) and isinstance(baseline, list)):
            findings.append(f"{label}: array type mismatch")
            return findings
        if len(difficulty) != len(baseline):
            findings.append(
                f"{label}: array length {len(difficulty)} != {len(baseline)}"
            )
            return findings
        for index, (left, right) in enumerate(zip(difficulty, baseline)):
            typed_equality_findings(
                left, right, f"{label}[{index}]", findings=findings
            )
        return findings

    if isinstance(difficulty, Mapping) or isinstance(baseline, Mapping):
        if not (
            isinstance(difficulty, Mapping) and isinstance(baseline, Mapping)
        ):
            findings.append(f"{label}: object type mismatch")
            return findings
        if set(difficulty) != set(baseline):
            missing = sorted(set(baseline) - set(difficulty))
            extra = sorted(set(difficulty) - set(baseline))
            findings.append(
                f"{label}: key set mismatch missing={missing} extra={extra}"
            )
            return findings
        for key in sorted(difficulty):
            typed_equality_findings(
                difficulty[key],
                baseline[key],
                f"{label}.{key}" if path else str(key),
                findings=findings,
            )
        return findings

    if difficulty is None or baseline is None:
        if difficulty is not baseline:
            findings.append(f"{label}: {difficulty!r} != {baseline!r}")
        return findings

    findings.append(f"{label}: unsupported value type")
    return findings


def _flatten(value: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, item in value.items():
        label = f"{prefix}{key}"
        if isinstance(item, Mapping):
            flat.update(_flatten(item, f"{label}."))
        else:
            flat[label] = item
    return flat


def declared_config_difference(
    difficulty_scenario: Mapping[str, Any],
    baseline_scenario: Mapping[str, Any],
) -> dict[str, Any]:
    """Only `scenario_id` and `target.speed_mps` may differ (Inputs)."""

    difficulty_flat = _flatten(difficulty_scenario)
    baseline_flat = _flatten(baseline_scenario)
    findings: list[str] = []
    keys = sorted(set(difficulty_flat) | set(baseline_flat))
    differing: list[str] = []
    for key in keys:
        if key not in difficulty_flat or key not in baseline_flat:
            findings.append(f"{key}: key present in only one scenario config")
            continue
        if difficulty_flat[key] != baseline_flat[key]:
            differing.append(key)
    for key in differing:
        if key not in DECLARED_CONFIG_DIFFERENCE_KEYS:
            findings.append(
                f"{key}: undeclared config difference "
                f"({difficulty_flat[key]!r} vs {baseline_flat[key]!r})"
            )
    for key in DECLARED_CONFIG_DIFFERENCE_KEYS:
        if key not in differing:
            findings.append(f"{key}: expected to differ from the D1 baseline")
    return {
        "declared_difference_keys": list(DECLARED_CONFIG_DIFFERENCE_KEYS),
        "observed_difference_keys": differing,
        "passed": not findings,
        "findings": findings,
    }


def _gate_triple(
    name: str,
    difficulty_gates: Mapping[str, Any],
    baseline_gates: Mapping[str, Any],
) -> dict[str, Any]:
    difficulty_value = (difficulty_gates.get(name) or {}).get("value")
    baseline_value = (baseline_gates.get(name) or {}).get("value")
    delta: Any = None
    if _is_real_number(difficulty_value) and _is_real_number(baseline_value):
        delta = difficulty_value - baseline_value
    return {
        "difficulty_value": difficulty_value,
        "d1_baseline_value": baseline_value,
        "delta": delta,
        "gating": False,
        "note": "speed-derived; recorded only (BC-DRB-2 / B2.1)",
    }


def _per_distractor_triples(
    difficulty: Mapping[str, Any],
    baseline: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    findings: list[str] = []

    def keyed(report: Mapping[str, Any]) -> dict[tuple[Any, ...], Any]:
        entries: dict[tuple[Any, ...], Any] = {}
        for item in report.get("distractors", {}).get("per_distractor", []):
            position = item.get("position_world_m") or {}
            entries[
                (
                    item.get("prefab_name"),
                    position.get("x"),
                    position.get("z"),
                )
            ] = item
        return entries

    difficulty_entries = keyed(difficulty)
    baseline_entries = keyed(baseline)
    if set(difficulty_entries) != set(baseline_entries):
        findings.append(
            "distractor identity set differs from the D1 baseline"
        )
        return [], findings
    rows: list[dict[str, Any]] = []
    for key in sorted(difficulty_entries, key=lambda item: tuple(map(str, item))):
        left = difficulty_entries[key]
        right = baseline_entries[key]
        row: dict[str, Any] = {
            "prefab_name": left.get("prefab_name"),
            "position_world_m": left.get("position_world_m"),
        }
        for field in ("fully_in_frame_ticks", "tick_count"):
            difficulty_value = left.get(field)
            baseline_value = right.get(field)
            delta: Any = None
            if _is_real_number(difficulty_value) and _is_real_number(
                baseline_value
            ):
                delta = difficulty_value - baseline_value
            row[field] = {
                "difficulty_value": difficulty_value,
                "d1_baseline_value": baseline_value,
                "delta": delta,
            }
        rows.append(row)
    return rows, findings


def route_legality_section(
    difficulty_report: Mapping[str, Any] | None,
    baseline_report: Mapping[str, Any] | None,
    *,
    difficulty_path: Path | None,
    baseline_path: Path | None,
) -> dict[str, Any]:
    """Must-pass route legality: own gate **and** BC-DRB-3 field equality."""

    gate_findings: list[str] = []
    equality_findings: list[str] = []
    if difficulty_report is None:
        gate_findings.append(
            "difficulty route-legality report is missing; the accepted "
            "SCENE-002 audit must be re-run for the difficulty config"
        )
    if baseline_report is None:
        equality_findings.append(
            "archived D1 route-legality report is missing; BC-DRB-3 "
            "comparison cannot be evaluated"
        )
    if difficulty_report is not None:
        if difficulty_report.get("schema_version") != ROAD_AUDIT_SCHEMA:
            gate_findings.append(
                "difficulty route-legality report has the wrong schema"
            )
        if difficulty_report.get("status") != "CLEAR":
            gate_findings.append(
                f"route-legality status is {difficulty_report.get('status')!r}, "
                "expected 'CLEAR'"
            )
        for field in ROAD_AUDIT_VIOLATION_COUNT_FIELDS:
            value = difficulty_report.get(field)
            if value != 0:
                gate_findings.append(f"{field} is {value!r}, expected 0")
        for field in ROAD_AUDIT_VIOLATION_ARRAY_FIELDS:
            value = difficulty_report.get(field)
            if not isinstance(value, list) or value:
                gate_findings.append(f"{field} is not an empty array")
    if difficulty_report is not None and baseline_report is not None:
        for field in ROAD_AUDIT_COMPARED_FIELDS:
            if field not in difficulty_report or field not in baseline_report:
                equality_findings.append(f"{field}: field missing")
                continue
            typed_equality_findings(
                difficulty_report[field],
                baseline_report[field],
                field,
                findings=equality_findings,
            )
    return {
        "clause": "BC-DRB-3",
        "compared_fields": list(ROAD_AUDIT_COMPARED_FIELDS),
        "exempt_fields": ["scenario_id"],
        "difficulty_report_path": _display_path(difficulty_path),
        "difficulty_report_sha256": (
            sha256_file(difficulty_path)
            if difficulty_path is not None and difficulty_path.is_file()
            else None
        ),
        "d1_baseline_report_path": _display_path(baseline_path),
        "d1_baseline_report_sha256": (
            sha256_file(baseline_path)
            if baseline_path is not None and baseline_path.is_file()
            else None
        ),
        "gate_findings": gate_findings,
        "equality_findings": equality_findings,
        "gate_passed": not gate_findings,
        "equal_to_d1_baseline": (
            difficulty_report is not None
            and baseline_report is not None
            and not equality_findings
        ),
        "passed": not gate_findings and not equality_findings,
        "note": (
            "field equality never replaces the CLEAR / zero-violation gate"
        ),
    }


def build_difficulty_audit(
    *,
    difficulty_scenario_path: Path,
    difficulty_label: str,
    d1_geometry_artifact_path: Path = D1_GEOMETRY_ARTIFACT_PATH,
    d1_scenario_path: Path = D1_SCENARIO_PATH,
    difficulty_road_audit_path: Path | None = None,
    d1_road_audit_path: Path = D1_ROAD_AUDIT_PATH,
) -> dict[str, Any]:
    difficulty_scenario_path = Path(difficulty_scenario_path)
    d1_geometry_artifact_path = Path(d1_geometry_artifact_path)
    d1_scenario_path = Path(d1_scenario_path)
    d1_road_audit_path = Path(d1_road_audit_path)

    difficulty_scenario = _read_json(difficulty_scenario_path)
    d1_scenario = _read_json(d1_scenario_path)
    baseline = _read_json(d1_geometry_artifact_path)
    if baseline.get("schema_version") != "p1-scene-004-geometry/v1":
        raise DifficultyAuditError(
            "archived D1 baseline artifact has an unexpected schema"
        )
    difficulty = build_geometry(difficulty_scenario_path)

    difficulty_gates = difficulty["gates"]
    baseline_gates = baseline["gates"]

    gate_rows: dict[str, Any] = {}
    for name in MUST_PASS_GATES:
        equality_findings = typed_equality_findings(
            difficulty_gates.get(name),
            baseline_gates.get(name),
            name,
        )
        gate_rows[name] = {
            "difficulty": difficulty_gates.get(name),
            "d1_baseline": baseline_gates.get(name),
            "gate_passed": bool(
                (difficulty_gates.get(name) or {}).get("passed")
            ),
            "equal_to_d1_baseline": not equality_findings,
            "equality_findings": equality_findings,
            "passed": bool((difficulty_gates.get(name) or {}).get("passed"))
            and not equality_findings,
        }

    geometry_findings: list[str] = []
    difficulty_geometry = {
        key: value
        for key, value in difficulty["geometry"].items()
        if key not in SPEED_DERIVED_GEOMETRY_KEYS
    }
    baseline_geometry = {
        key: value
        for key, value in baseline["geometry"].items()
        if key not in SPEED_DERIVED_GEOMETRY_KEYS
    }
    typed_equality_findings(
        difficulty_geometry, baseline_geometry, "geometry", findings=geometry_findings
    )
    typed_equality_findings(
        difficulty["predicted_target_box_px"],
        baseline["predicted_target_box_px"],
        "predicted_target_box_px",
        findings=geometry_findings,
    )

    config_difference = declared_config_difference(
        difficulty_scenario, d1_scenario
    )

    difficulty_road_audit_path = (
        Path(difficulty_road_audit_path)
        if difficulty_road_audit_path is not None
        else None
    )
    difficulty_road_report = (
        _read_json(difficulty_road_audit_path)
        if difficulty_road_audit_path is not None
        and difficulty_road_audit_path.is_file()
        else None
    )
    baseline_road_report = (
        _read_json(d1_road_audit_path) if d1_road_audit_path.is_file() else None
    )
    route_legality = route_legality_section(
        difficulty_road_report,
        baseline_road_report,
        difficulty_path=difficulty_road_audit_path,
        baseline_path=d1_road_audit_path,
    )

    per_distractor, distractor_findings = _per_distractor_triples(
        difficulty, baseline
    )
    record_only: dict[str, Any] = {
        name: _gate_triple(name, difficulty_gates, baseline_gates)
        for name in RECORD_ONLY_GATES
    }
    record_only["per_distractor"] = per_distractor
    record_only["per_distractor_findings"] = distractor_findings

    failures: list[str] = []
    for name, row in gate_rows.items():
        if not row["gate_passed"]:
            failures.append(f"must_pass_gate_failed:{name}")
        for finding in row["equality_findings"]:
            failures.append(f"must_pass_gate_not_equal_to_d1:{finding}")
    for finding in geometry_findings:
        failures.append(f"geometry_not_equal_to_d1:{finding}")
    for finding in config_difference["findings"]:
        failures.append(f"undeclared_config_difference:{finding}")
    for finding in route_legality["gate_findings"]:
        failures.append(f"route_legality_gate_failed:{finding}")
    for finding in route_legality["equality_findings"]:
        failures.append(f"route_legality_not_equal_to_d1:{finding}")

    status = "ENVELOPE_OK" if not failures else "ENVELOPE_OUT_OF_BOUNDS"
    return {
        "schema_version": ARTIFACT_SCHEMA,
        "work_id": WORK_ID,
        "amendment": "DR-B B2 (acceptance round 4, BC-DRB-2/BC-DRB-3)",
        "partition_mode": (
            "must_pass_speed_independent_plus_record_only_speed_derived"
        ),
        "status": status,
        "status_scope": (
            "computed on the must-pass gate set only; record-only triples "
            "never enter the status"
        ),
        "difficulty": {
            "label": difficulty_label,
            "scenario_id": difficulty_scenario.get("scenario_id"),
            "target_speed_mps": difficulty_scenario.get("target", {}).get(
                "speed_mps"
            ),
            "scenario_path": _display_path(difficulty_scenario_path),
            "scenario_sha256": sha256_file(difficulty_scenario_path),
        },
        "d1_baseline": {
            "scenario_id": d1_scenario.get("scenario_id"),
            "target_speed_mps": d1_scenario.get("target", {}).get("speed_mps"),
            "scenario_path": _display_path(d1_scenario_path),
            "scenario_sha256": sha256_file(d1_scenario_path),
            "geometry_artifact_path": _display_path(d1_geometry_artifact_path),
            "geometry_artifact_sha256": sha256_file(d1_geometry_artifact_path),
            "regenerated": False,
        },
        "equality_rule": {
            "clause": "BC-DRB-2",
            "bit_equal_preferred": True,
            "float_abs_tolerance": FLOAT_ABS_TOLERANCE,
            "exact_types": [
                "int",
                "bool",
                "str",
                "enum",
                "array length",
                "key set",
                "canonical order",
            ],
        },
        "must_pass": {
            "gates": gate_rows,
            "geometry_value_equality": {
                "excluded_speed_derived_keys": list(
                    SPEED_DERIVED_GEOMETRY_KEYS
                ),
                "passed": not geometry_findings,
                "findings": geometry_findings,
            },
            "declared_config_difference": config_difference,
            "route_legality": route_legality,
        },
        "record_only": record_only,
        "failures": failures,
        "generated_unix_s": time.time(),
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--difficulty-label", default="D2")
    parser.add_argument(
        "--d1-geometry-artifact",
        type=Path,
        default=D1_GEOMETRY_ARTIFACT_PATH,
    )
    parser.add_argument("--d1-scenario", type=Path, default=D1_SCENARIO_PATH)
    parser.add_argument("--road-audit", type=Path, default=None)
    parser.add_argument("--d1-road-audit", type=Path, default=D1_ROAD_AUDIT_PATH)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    arguments = build_argument_parser().parse_args(argv)
    artifact = build_difficulty_audit(
        difficulty_scenario_path=arguments.scenario,
        difficulty_label=arguments.difficulty_label,
        d1_geometry_artifact_path=arguments.d1_geometry_artifact,
        d1_scenario_path=arguments.d1_scenario,
        difficulty_road_audit_path=arguments.road_audit,
        d1_road_audit_path=arguments.d1_road_audit,
    )
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(artifact, indent=1, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"status={artifact['status']} "
        f"difficulty={artifact['difficulty']['label']} "
        f"speed={artifact['difficulty']['target_speed_mps']} "
        f"failures={len(artifact['failures'])}"
    )
    if artifact["status"] != "ENVELOPE_OK":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
