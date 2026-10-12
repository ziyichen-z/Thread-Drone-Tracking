"""P1-M2-RATE-003 §6 + Amendment DR-B B1 decision function.

Pure, side-effect-free evaluation of the accepted totally defined
disposition function. `tools/run_rate3_study.py` collects the run rows and
persists the immutable `p1-rate3-decision/v1` artifact; everything that
decides *what the numbers mean* lives here so it can be tested directly
and recomputed by a reviewer.

Frozen constants (data-before freeze, acceptance rounds 3/4):

* `THETA = 0.05` — pre-registered practical-significance threshold, **not**
  a statistical equivalence bound.
* `THETA_GEOM = 0.05` (BC-DRB-1) — unconditional `c_geom` divergence flag.
* ceiling `>= 0.80`, floor `< 0.30`, dispersion/sign flags at `2*THETA`.
* every quantile is type-7 linear interpolation.

The diagnostic flags never change `final_action`; `final_action` is a
closed six-value enum with no suffixes (Round 2 requirement 4).
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

DECISION_SCHEMA = "p1-rate3-decision/v1"
RULE_VERSION = "p1-rate3-rules-difficulty-paired/v1"

THETA = 0.05
THETA_GEOM = 0.05
CEILING_MIN = 0.80
FLOOR_MAX = 0.30
DISPERSION_LIMIT = 2.0 * THETA
H2_LIMIT = 2.0 * THETA
SENSITIVITY_THETAS = (0.03, 0.05, 0.10)

DIFFICULTIES = ("D1", "D2")
PHASES = (1, 2, 3)
RATES = (20, 5)

DISPOSITIONS = (
    "BLOCKED_INCOMPLETE_CELL",
    "FLOOR",
    "CEILING",
    "RATE_EFFECT_POSITIVE",
    "RATE_EFFECT_INVERTED",
    "NO_EFFECT_DETECTED_MIDBAND",
)
FINAL_ACTIONS = (
    "BLOCKED_INCOMPLETE",
    "M2_RATE_CONTRAST_ESTABLISHED",
    "INVERTED_EFFECT_REPORTED",
    "H1_FALSIFIED_CEILING_AT_D2",
    "H1_FALSIFIED_FLOOR_AT_D2",
    "NO_EFFECT_DETECTED_AT_D2",
)

CLAIM_BEARING_ACTIONS = (
    "M2_RATE_CONTRAST_ESTABLISHED",
    "INVERTED_EFFECT_REPORTED",
)


class Rate3DecisionError(ValueError):
    """Raised when the decision inputs are structurally unusable."""


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Rate3DecisionError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise Rate3DecisionError(f"{label} must be a finite number")
    return result


def quantile_type7(values: Sequence[float], probability: float) -> float:
    """Type-7 linear interpolation (§6: `numpy.percentile(method='linear')`).

    `h = (n - 1) * p` in zero-based index space, then linear interpolation
    between the bracketing order statistics. Frozen so p05/p95 recompute
    identically across implementations.
    """

    if not 0.0 <= probability <= 1.0:
        raise Rate3DecisionError("probability must lie in [0, 1]")
    ordered = sorted(_finite(value, "quantile input") for value in values)
    if not ordered:
        raise Rate3DecisionError("quantile of an empty sample is undefined")
    if len(ordered) == 1:
        return ordered[0]
    virtual_index = probability * (len(ordered) - 1)
    previous_index = math.floor(virtual_index)
    next_index = min(previous_index + 1, len(ordered) - 1)
    gamma = virtual_index - previous_index
    lower = ordered[previous_index]
    upper = ordered[next_index]
    difference = upper - lower
    # NumPy's `_lerp` switches to the upper anchor once gamma >= 0.5, which
    # changes the last bit. §6 pins this function to `numpy.percentile(...,
    # method="linear")` value for value, so the branch is reproduced here.
    if gamma >= 0.5:
        return upper - difference * (1.0 - gamma)
    return lower + difference * gamma


def median_of_three(values: Sequence[float]) -> float:
    """Median of exactly three values: odd count, no interpolation (§6)."""

    if len(values) != 3:
        raise Rate3DecisionError("median_of_three requires exactly three values")
    return sorted(_finite(value, "median input") for value in values)[1]


def difficulty_disposition(
    *,
    c_20: float,
    c_5: float,
    delta: float,
    complete: bool,
) -> str:
    """§6 difficulty-level ordered rules; first hit terminates."""

    if not complete:
        return "BLOCKED_INCOMPLETE_CELL"
    for value, label in ((c_20, "C_20"), (c_5, "C_5"), (delta, "Delta")):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return "BLOCKED_INCOMPLETE_CELL"
        if not math.isfinite(float(value)):
            return "BLOCKED_INCOMPLETE_CELL"
    if c_20 < FLOOR_MAX and c_5 < FLOOR_MAX:
        return "FLOOR"
    if c_20 >= CEILING_MIN and c_5 >= CEILING_MIN and abs(delta) <= THETA:
        return "CEILING"
    if delta > THETA:
        return "RATE_EFFECT_POSITIVE"
    if delta < -THETA:
        return "RATE_EFFECT_INVERTED"
    return "NO_EFFECT_DETECTED_MIDBAND"


def research_final_action(
    *,
    d1_disposition: str,
    d2_disposition: str,
) -> str:
    """§6 research-level ordered rules; unique for any admissible input."""

    for disposition in (d1_disposition, d2_disposition):
        if disposition not in DISPOSITIONS:
            raise Rate3DecisionError(f"unknown disposition {disposition!r}")
    if "BLOCKED_INCOMPLETE_CELL" in (d1_disposition, d2_disposition):
        return "BLOCKED_INCOMPLETE"
    return {
        "RATE_EFFECT_POSITIVE": "M2_RATE_CONTRAST_ESTABLISHED",
        "RATE_EFFECT_INVERTED": "INVERTED_EFFECT_REPORTED",
        "CEILING": "H1_FALSIFIED_CEILING_AT_D2",
        "FLOOR": "H1_FALSIFIED_FLOOR_AT_D2",
        "NO_EFFECT_DETECTED_MIDBAND": "NO_EFFECT_DETECTED_AT_D2",
    }[d2_disposition]


def _row_key(row: Mapping[str, Any]) -> tuple[str, int, int]:
    return (
        str(row.get("difficulty")),
        int(row.get("phase")),
        int(row.get("rate_hz")),
    )


def _index_rows(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, int, int], Mapping[str, Any]]:
    indexed: dict[tuple[str, int, int], Mapping[str, Any]] = {}
    for row in rows:
        key = _row_key(row)
        if key in indexed:
            raise Rate3DecisionError(f"duplicate run row for {key}")
        indexed[key] = row
    return indexed


def pairing_findings(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, list[str]]:
    """BC-DRB-5: both runs of a mismatched pair are non-admissible.

    Returns the per-difficulty findings; a mismatch is an implementation
    defect (the startup preflight should have refused the run), so the
    caller must attribute it as such, not merely scrap a run.
    """

    indexed = _index_rows(rows)
    findings: dict[str, list[str]] = {name: [] for name in DIFFICULTIES}
    for difficulty in DIFFICULTIES:
        for phase in PHASES:
            pair = [indexed.get((difficulty, phase, rate)) for rate in RATES]
            if any(row is None for row in pair):
                continue
            hashes = [row.get("calibration_sha256") for row in pair]
            if hashes[0] is None or hashes[1] is None:
                findings[difficulty].append(
                    f"{difficulty} phase {phase}: missing calibration_sha256"
                )
            elif hashes[0] != hashes[1]:
                findings[difficulty].append(
                    f"{difficulty} phase {phase}: paired calibration SHA-256 "
                    f"mismatch ({hashes[0]} vs {hashes[1]}); both runs are "
                    "non-admissible (BC-DRB-5)"
                )
    return findings


def _pair_values(
    indexed: Mapping[tuple[str, int, int], Mapping[str, Any]],
    difficulty: str,
    field: str,
) -> list[dict[str, Any]] | None:
    values: list[dict[str, Any]] = []
    for phase in PHASES:
        try:
            fast = indexed[(difficulty, phase, 20)]
            slow = indexed[(difficulty, phase, 5)]
        except KeyError:
            return None
        try:
            fast_value = _finite(fast.get(field), f"{field}@20Hz")
            slow_value = _finite(slow.get(field), f"{field}@5Hz")
        except Rate3DecisionError:
            return None
        values.append(
            {
                "phase": phase,
                "rate_20_hz": fast_value,
                "rate_5_hz": slow_value,
                "difference": fast_value - slow_value,
            }
        )
    return values


def build_difficulty_cell(
    difficulty: str,
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """One difficulty cell: summaries, paired differences, flags, disposition."""

    if difficulty not in DIFFICULTIES:
        raise Rate3DecisionError(f"unknown difficulty {difficulty!r}")
    cell_rows = [row for row in rows if row.get("difficulty") == difficulty]
    indexed = _index_rows(cell_rows)
    blocking: list[str] = []

    expected = {
        (difficulty, phase, rate) for phase in PHASES for rate in RATES
    }
    missing = sorted(str(key) for key in expected - set(indexed))
    if missing:
        blocking.append(f"missing runs: {', '.join(missing)}")
    for key in sorted(set(indexed) & expected, key=str):
        if not indexed[key].get("admissible"):
            blocking.append(f"{indexed[key].get('run_id')} is not admissible")
    blocking.extend(pairing_findings(cell_rows)[difficulty])

    conditional = _pair_values(indexed, difficulty, "c_track_given_geom")
    geom = _pair_values(indexed, difficulty, "c_geom")
    track = _pair_values(indexed, difficulty, "c_track")
    if conditional is None:
        blocking.append("conditional endpoint C_track|geom is unavailable")
    if geom is None:
        blocking.append("unconditional c_geom is unavailable")
    if track is None:
        blocking.append("unconditional c_track is unavailable")

    complete = not blocking
    summary: dict[str, Any] = {
        "difficulty": difficulty,
        "complete": complete,
        "blocking_findings": blocking,
        "c_20": None,
        "c_5": None,
        "conditional_pairs": conditional,
        "delta_i": None,
        "delta": None,
        "c_20_minus_c_5": None,
        "c_geom_pairs": geom,
        "c_track_pairs": track,
        "delta_geom_i": None,
        "delta_track_i": None,
        "delta_track": None,
        "flags": {
            "CEILING_FLAG": None,
            "FLOOR_FLAG": None,
            "DISPERSION_FLAG": None,
            "SIGN_INCONSISTENT_FLAG": None,
            "CGEOM_DIVERGENCE_FLAG": None,
        },
        "cgeom_flag_unavailable_reason": None,
        "theta": THETA,
        "theta_geom": THETA_GEOM,
        "sensitivity": None,
        "disposition": "BLOCKED_INCOMPLETE_CELL",
    }
    if not complete:
        summary["cgeom_flag_unavailable_reason"] = (
            "difficulty cell is not complete; all six runs must be admissible"
        )
        return summary

    assert conditional is not None and geom is not None and track is not None
    c_20 = median_of_three([item["rate_20_hz"] for item in conditional])
    c_5 = median_of_three([item["rate_5_hz"] for item in conditional])
    delta_i = [item["difference"] for item in conditional]
    delta = median_of_three(delta_i)
    delta_geom_i = [item["difference"] for item in geom]
    delta_track_i = [item["difference"] for item in track]
    delta_track = median_of_three(delta_track_i)

    ceiling_flag = c_20 >= CEILING_MIN and c_5 >= CEILING_MIN
    floor_flag = c_20 < FLOOR_MAX and c_5 < FLOOR_MAX
    dispersion_flag = (max(delta_i) - min(delta_i)) > DISPERSION_LIMIT
    signs = {0 if value == 0.0 else (1 if value > 0.0 else -1) for value in delta_i}
    sign_inconsistent_flag = len(signs) > 1
    cgeom_flag = any(abs(value) > THETA_GEOM for value in delta_geom_i)

    summary.update(
        {
            "c_20": c_20,
            "c_5": c_5,
            "conditional_pairs": conditional,
            "delta_i": delta_i,
            "delta": delta,
            "c_20_minus_c_5": c_20 - c_5,
            "delta_geom_i": delta_geom_i,
            "delta_track_i": delta_track_i,
            "delta_track": delta_track,
            "flags": {
                "CEILING_FLAG": ceiling_flag,
                "FLOOR_FLAG": floor_flag,
                "DISPERSION_FLAG": dispersion_flag,
                "SIGN_INCONSISTENT_FLAG": sign_inconsistent_flag,
                "CGEOM_DIVERGENCE_FLAG": cgeom_flag,
            },
            "sensitivity": {
                f"{threshold}": {
                    "delta_gt_theta": delta > threshold,
                    "delta_lt_negative_theta": delta < -threshold,
                    "abs_delta_le_theta": abs(delta) <= threshold,
                }
                for threshold in SENSITIVITY_THETAS
            },
            "disposition": difficulty_disposition(
                c_20=c_20, c_5=c_5, delta=delta, complete=True
            ),
        }
    )
    return summary


def _format(value: float) -> str:
    return f"{value:.6f}"


def _heterogeneity_text(cell: Mapping[str, Any]) -> str:
    delta_i = list(cell["delta_i"])
    spread = max(delta_i) - min(delta_i)
    values = ", ".join(
        f"Delta_{index + 1}={_format(value)}"
        for index, value in enumerate(delta_i)
    )
    return (
        "Across the three registered design points the median paired "
        f"difference exceeds theta={THETA}, but the points disagree: "
        f"{values}; range={_format(spread)}. Report it as a per-point "
        "inconsistent result, never as an unqualified 'contrast "
        "established'."
    )


def _cgeom_text(cells: Mapping[str, Mapping[str, Any]]) -> str:
    parts: list[str] = []
    for difficulty in DIFFICULTIES:
        cell = cells[difficulty]
        if not cell.get("complete"):
            continue
        for index, phase in enumerate(PHASES):
            geom_pair = cell["c_geom_pairs"][index]
            parts.append(
                f"{difficulty} s*{phase}: c_geom(20Hz)="
                f"{_format(geom_pair['rate_20_hz'])} / c_geom(5Hz)="
                f"{_format(geom_pair['rate_5_hz'])}, delta_geom="
                f"{_format(geom_pair['difference'])}"
            )
        parts.append(
            f"{difficulty} conditional Delta={_format(cell['delta'])} vs "
            f"unconditional Delta^track={_format(cell['delta_track'])}"
        )
    return (
        "Unconditional geometric visibility diverges between the two rates "
        f"(|delta_geom_i| > theta_geom={THETA_GEOM}) on at least one design "
        "point. Report the conditional paired difference together with the "
        "unconditional one; their gap is carried mainly by geometric "
        "visibility divergence (delta_geom), and gimbal pointing failure is "
        "the candidate mechanism. Values: " + "; ".join(parts)
    )


def build_decision_body(
    rows: Sequence[Mapping[str, Any]],
    *,
    lap_period_medians: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate §6 + B1 over the twelve formal run rows."""

    cells = {
        difficulty: build_difficulty_cell(difficulty, rows)
        for difficulty in DIFFICULTIES
    }
    d1, d2 = cells["D1"], cells["D2"]
    final_action = research_final_action(
        d1_disposition=d1["disposition"],
        d2_disposition=d2["disposition"],
    )

    if d1["complete"] and d2["complete"]:
        h2_value = abs(d2["c_20"] - d1["c_5"])
        h2_flag: bool | None = h2_value > H2_LIMIT
        h2_reason = None
    else:
        h2_value = None
        h2_flag = None
        h2_reason = (
            "H2 needs both the D2 20 Hz and the D1 5 Hz cell summaries; at "
            "least one difficulty cell is incomplete"
        )

    cgeom_values = [cells[name]["flags"]["CGEOM_DIVERGENCE_FLAG"] for name in DIFFICULTIES]
    if any(value is None for value in cgeom_values):
        research_cgeom_flag: bool | None = None
        cgeom_reason = (
            "research-level CGEOM_DIVERGENCE_FLAG is null because at least "
            "one difficulty flag is null"
        )
    else:
        research_cgeom_flag = bool(cgeom_values[0] or cgeom_values[1])
        cgeom_reason = None

    ladder_premise_violated = d1["disposition"] != "CEILING"

    heterogeneity_qualified = bool(
        final_action in CLAIM_BEARING_ACTIONS
        and d2["complete"]
        and (
            d2["flags"]["DISPERSION_FLAG"]
            or d2["flags"]["SIGN_INCONSISTENT_FLAG"]
        )
    )
    qualifier_text = _heterogeneity_text(d2) if heterogeneity_qualified else None

    cgeom_divergence_qualified = research_cgeom_flag is True
    cgeom_qualifier_text = (
        _cgeom_text(cells) if cgeom_divergence_qualified else None
    )

    pseudo_ceiling_caveat = (
        final_action == "H1_FALSIFIED_CEILING_AT_D2"
        and d2["flags"]["CGEOM_DIVERGENCE_FLAG"] is True
    )

    dr_referral_required = bool(
        ladder_premise_violated
        or final_action
        in {"INVERTED_EFFECT_REPORTED", "NO_EFFECT_DETECTED_AT_D2"}
        or heterogeneity_qualified
        or cgeom_divergence_qualified
    )

    return {
        "rule_version": RULE_VERSION,
        "theta": THETA,
        "theta_geom": THETA_GEOM,
        "ceiling_minimum": CEILING_MIN,
        "floor_maximum": FLOOR_MAX,
        "quantile_method": "type-7 linear interpolation",
        "difficulties": {name: cells[name] for name in DIFFICULTIES},
        "dispositions": {
            name: cells[name]["disposition"] for name in DIFFICULTIES
        },
        "final_action": final_action,
        "ladder_premise_violated": ladder_premise_violated,
        "dr_referral_required": dr_referral_required,
        "heterogeneity_qualified": heterogeneity_qualified,
        "qualifier_text": qualifier_text,
        "cgeom_divergence_qualified": cgeom_divergence_qualified,
        "cgeom_qualifier_text": cgeom_qualifier_text,
        "pseudo_ceiling_caveat_required": pseudo_ceiling_caveat,
        "CGEOM_DIVERGENCE_FLAG": research_cgeom_flag,
        "cgeom_flag_unavailable_reason": cgeom_reason,
        "H2_DIVERGENCE_FLAG": h2_flag,
        "h2_value": h2_value,
        "h2_limit": H2_LIMIT,
        "h2_unavailable_reason": h2_reason,
        "measured_lap_period_s": dict(lap_period_medians or {}),
        "zero_effect_statement_rule": (
            "A null or ceiling result may only be written as 'no effect "
            f"above the pre-registered practical-significance threshold "
            f"theta={THETA} was detected at the three registered design "
            "points'; it must never be written as population equivalence or "
            "as 'frame rate has no influence'."
        ),
        "claim_rule": (
            "Whenever the research-level CGEOM_DIVERGENCE_FLAG is true, every "
            "rate-effect / no-effect / ceiling claim must report the "
            "conditional Delta and the unconditional Delta^track together; "
            "the conditional Delta may not stand alone as the effect size."
        ),
    }
