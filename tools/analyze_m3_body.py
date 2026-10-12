"""P1-M3-BODY-001 batch 1c offline analysis and run binding (Acceptance
round 11 §B, round 12 §B, round 13 §B binding revisions).

Binds one formal trial run to the M3 offline truth/platform carrier
(``p1-m3-body-truth/v2``) and recomputes every quantity the batch-1
protocol froze. Current correction layer (round 13 §B) over the returned
round-2 tool:

* the off-route tolerance premise is the production
  ``LoopTargetVehicle.Step`` corner-cutting rule, not "ideal polyline";
* the H2 third component is the frozen ``1[min_side_px >= 20]`` indicator
  share, never raw pixel differences;
* first analysis collects the truth stream AND the raw bytes of the
  scenario, margin artifact, body config, re-anchor config and tracker
  model spec into the run directory (create-once); every later read,
  including ``--verify``, is run-directory-only and the receipt hashes
  only those run-bound copies (tracker binaries are represented by the
  manifest's recorded per-model SHA-256 identities, cross-checked against
  the collected spec);
* per-record truth ``scenario_id`` and the truth/tracker per-frame
  capture-clock binding are checked; manifest schema, tracker identity
  with both model SHA-256 values, re-anchor identity and the body
  policy/planner correspondence are all verified mechanically;
* the ten formal run IDs and their pairing order are frozen
  ten canonical slots (``p1-m3-body-001-arm-a-trial-1..5`` /
  ``-arm-b-trial-1..5``) acquired under ten acquisition IDs: A1 is acquired
  as ``p1-m3-body-001-arm-a-trial-1-attempt-4`` (round 29 §C.2, its original
  ID having been consumed by the attempt-3 void site), A2 as
  ``p1-m3-body-001-arm-a-trial-2-attempt-2`` (round 42 §B/BC-BODY1-26, its
  original ID having been consumed by the attempt-1 void site) and the other
  eight acquisition IDs equal their canonical slot;
  ``--compare`` enforces them, rejects duplicates/wrong arms/wrong order,
  requires a non-existent create-once ``--output`` path and hashes all
  ten analysis files into its output;
* the loop domain is admissible when the trial closed the route at least
  once (``final_mileage >= P``) *and* the unwrapped mileage series is
  domain-intact: never stepping backwards and never falling back below ``P``
  after the first closure (round 42 §A/BC-BODY1-23). "Exactly one closure"
  is carried by the ``[0, P)`` sample filter, not by how long the Play ran,
  so laps two and later neither enter H1 nor void the trial.

Retained from earlier rounds: the IoU threshold is read from
``evaluation.tracking_iou_threshold``; all per-frame inputs come from the
truth carrier (no 128-frame retention dependency); all metric weights are
frozen route-mileage trapezoidal weights with boundary completion;
``C_quality`` samples are geometrically-visible window frames only;
effort integrates the plant's applied velocity over simulation-time
deltas, never requested commands.

Tolerance provenance (round 13 §B.1, mechanically derived from checked-in
sources, not chosen): the production ``LoopTargetVehicle.Step``
(``Assets/TetheredTracking/Scripts/LoopTargetVehicle.cs:65-81``) switches
waypoints when the planar distance is ``< 0.5 m`` (line 72) *without*
snapping to the old waypoint, so the real trajectory cuts corners: after
a switch at distance ``d < 0.5 m`` the vehicle drives a straight chord
toward the next waypoint, and the chord's maximum distance from the ideal
polyline is strictly below ``d`` (for the perpendicular case it is
``d*L/(L+d) < d``). Hence ``OFF_ROUTE_TOL_M = 0.5 + 1e-3``: the frozen
0.5 m switch bound plus a float32 projection margin (at |coordinate|
<= 256 m one ulp is 2^-23 * 256 ~= 3.05e-5 m; 1e-3 m covers ~30 ulp).
``START_MILEAGE_TOL_M = 0.5`` = frozen capture cadence (1 / 5 Hz = 0.2 s)
x frozen target speed (2.0 m/s) = 0.4 m worst-case first-frame mileage,
pinned at the same frozen 0.5 m waypoint-switch granularity.

Ground truth flows one way only: the evaluator writes the truth stream,
this tool reads it. No controller, tracker or perception path ever reads
it. Fail-closed: any identity/coverage/closure inconsistency aborts with a
named error and writes nothing.

Usage:

    python3 tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
    python3 tools/analyze_m3_body.py --run-id <id> --verify
    python3 tools/analyze_m3_body.py --compare \
        --arm-a p1-m3-body-001-arm-a-trial-1-attempt-4,...,p1-m3-body-001-arm-a-trial-5 \
        --arm-b p1-m3-body-001-arm-b-trial-1,...,p1-m3-body-001-arm-b-trial-5 \
        --output <non-existent path>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller.reanchor import box_iou  # noqa: E402
from controller.run_log import read_frame_records  # noqa: E402

TRUTH_SCHEMA = "p1-m3-body-truth/v2"
ANALYSIS_SCHEMA = "p1-m3-body-analysis/v3"
COMPARE_SCHEMA = "p1-m3-body-compare/v3"
TRUTH_FILE_NAME = "m3_body_truth.jsonl"
ANALYSIS_FILE_NAME = "m3_body_analysis.json"

# Mechanically derived tolerances; see the module docstring (round 13 §B.1).
START_MILEAGE_TOL_M = 0.5
OFF_ROUTE_TOL_M = 0.5 + 1e-3
OFF_ROUTE_DERIVATION = (
    "LoopTargetVehicle.cs:72 switches waypoints at <0.5 m without "
    "snapping; the corner chord stays strictly within the switch "
    "distance of the polyline (perpendicular case d*L/sqrt(d^2+L^2) < d), so "
    "0.5 m (frozen switch bound) + 1e-3 m float32 projection margin "
    "(ulp 3.05e-5 m at |coord| <= 256 m, ~30 ulp)"
)
START_MILEAGE_DERIVATION = (
    "1/5 Hz capture cadence x 2.0 m/s frozen target speed = 0.4 m "
    "worst-case first-frame mileage, pinned at the frozen 0.5 m "
    "waypoint-switch granularity (LoopTargetVehicle.cs:72)"
)
# BC-BODY1-15 fail-closed branches for the arm-A full-loop C_geom.
H1_LOWER_BOUND = 0.5645
H1_CEILING = 0.95
# BC-BODY1-14 (a): minimum-box-side component threshold.
MIN_SIDE_PX = 20.0
# Frozen trial count per arm (BC-BODY1-13) and frozen run identities
# (round 13 §B.4): A1..A5/B1..B5, paired by index.
TRIALS_PER_ARM = 5
RUN_ID_TEMPLATE = "p1-m3-body-001-arm-{arm}-trial-{index}"
# Round 29 §C.2: attempt 3 created and then voided A1's original formal run
# directory, so that ID is permanently consumed. A1's next *and only*
# acquisition uses a distinct acquisition ID that maps back to the same
# canonical slot; the other nine identities are unchanged verbatim.
A1_CANONICAL_TRIAL_ID = "p1-m3-body-001-arm-a-trial-1"
A1_ACQUISITION_RUN_ID = "p1-m3-body-001-arm-a-trial-1-attempt-4"
A1_ATTEMPT_NUMBER = 4
A1_PREDECESSOR_VOID_MANIFEST_SHA256 = (
    "e5caa98276a48413f3d78d34228d8c41d8ad0b9e8b438c070d4925c4f14e8a65"
)
A1_PREDECESSOR_VOID_FRAMES_SHA256 = (
    "8f9f355186cf06d83dd30956552b9687cd4992454090f89ecc307f2b986016b5"
)
# Round 42 §B (BC-BODY1-26): arm A trial 2's first Play was ruled
# ``TRIAL_VOID_LOOP_DOMAIN_UPPER_BOUND_VIOLATION_POST_TRACKER_DWELL`` and its
# acquisition ID is consumed with the one-Play GO. Slot 2's next *and only*
# acquisition uses a distinct acquisition ID that maps back to the same
# canonical slot, so ``TRIALS_PER_ARM`` stays 5 (BC-BODY1-13). The remaining
# eight identities are unchanged verbatim.
A2_CANONICAL_TRIAL_ID = "p1-m3-body-001-arm-a-trial-2"
A2_ACQUISITION_RUN_ID = "p1-m3-body-001-arm-a-trial-2-attempt-2"
A2_ATTEMPT_NUMBER = 2
# Frozen arm policies (round 11 §B.1) and their planner identities.
ARM_A_POLICY = "hold"
ARM_B_POLICY = "threshold"
POLICY_PLANNER = {
    ARM_A_POLICY: "hold-v1",
    ARM_B_POLICY: "threshold-corridor-v1",
}
TRACKER_NAME = "nanotrack-v2"
MANIFEST_SCHEMA = "p1-track-run/v1"
# Run-bound input copies collected create-once on first analysis
# (round 13 §B.3); every later read is run-directory-only.
RUN_BOUND_INPUTS = (
    "scenario.json",
    "margin.json",
    "body_config.json",
    "reanchor_config.json",
    "tracker_model_spec.json",
)


class AnalysisError(Exception):
    """Named fail-closed abort; nothing is written when raised."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exception:
        raise AnalysisError(f"unreadable_json:{path}:{exception}") from exception


def _finite(value: Any, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise AnalysisError(f"non_finite_field:{name}")
    result = float(value)
    if not math.isfinite(result):
        raise AnalysisError(f"non_finite_field:{name}")
    return result


def _route_points(scenario: Mapping[str, Any]) -> list[tuple[float, float, float]]:
    route = scenario.get("target", {}).get("route_world_m")
    if not isinstance(route, list) or len(route) < 3:
        raise AnalysisError("scenario_route_missing")
    points = []
    for index, point in enumerate(route):
        points.append(
            (
                _finite(point.get("x"), f"route[{index}].x"),
                _finite(point.get("y"), f"route[{index}].y"),
                _finite(point.get("z"), f"route[{index}].z"),
            )
        )
    return points


def _cumulative_lengths(
    vertices: Sequence[tuple[float, float, float]],
) -> tuple[list[float], float]:
    cumulative = [0.0]
    for index, vertex in enumerate(vertices):
        nxt = vertices[(index + 1) % len(vertices)]
        cumulative.append(
            cumulative[-1] + math.hypot(nxt[0] - vertex[0], nxt[2] - vertex[2])
        )
    return cumulative, cumulative[-1]


def route_mileage(
    point: tuple[float, float],
    vertices: Sequence[tuple[float, float, float]],
    cumulative: Sequence[float],
) -> tuple[float, float]:
    """Nearest-point arc length of ``point`` on the closed route polyline.

    Returns ``(mileage_m, off_route_distance_m)``. Pure geometry on the
    frozen scenario route; no wall clock, no per-run tuning.
    """
    px, pz = point
    best_mileage = 0.0
    best_distance = float("inf")
    for index, vertex in enumerate(vertices):
        nxt = vertices[(index + 1) % len(vertices)]
        dx, dz = nxt[0] - vertex[0], nxt[2] - vertex[2]
        segment_length = math.hypot(dx, dz)
        if segment_length <= 0.0:
            continue
        t = ((px - vertex[0]) * dx + (pz - vertex[2]) * dz) / (
            segment_length * segment_length
        )
        t = min(max(t, 0.0), 1.0)
        cx, cz = vertex[0] + t * dx, vertex[2] + t * dz
        distance = math.hypot(px - cx, pz - cz)
        if distance < best_distance:
            best_distance = distance
            best_mileage = cumulative[index] + t * segment_length
    return best_mileage, best_distance


def _unwrap_mileage(
    mileages: Sequence[float], perimeter: float
) -> list[float]:
    """Unwrap closed-loop mileages into a nondecreasing lap-aware series."""
    if not mileages:
        return []
    unwrapped = [mileages[0]]
    lap = 0
    previous = mileages[0]
    for mileage in mileages[1:]:
        if mileage < previous - perimeter * 0.5:
            lap += 1
        elif mileage > previous + perimeter * 0.5:
            lap -= 1
        unwrapped.append(mileage + lap * perimeter)
        previous = mileage
    return unwrapped


def trapezoidal_weights(
    mileages: Sequence[float], lower: float, upper: float
) -> list[float]:
    """Trapezoidal mileage weights over the domain [lower, upper].

    Interior samples get half of each neighbour interval; the first sample
    also covers [lower, m_0] and the last also covers [m_n, upper], so the
    weights sum to exactly ``upper - lower`` - neither the first sample nor
    the trailing partial segment is dropped (round 12 §B.3).
    """
    count = len(mileages)
    if count == 0:
        return []
    if count == 1:
        return [upper - lower]
    weights = []
    for index, mileage in enumerate(mileages):
        if index == 0:
            weight = (mileages[1] - mileage) * 0.5 + (mileage - lower)
        elif index == count - 1:
            weight = (mileage - mileages[index - 1]) * 0.5 + (upper - mileage)
        else:
            weight = (mileages[index + 1] - mileages[index - 1]) * 0.5
        weights.append(max(weight, 0.0))
    return weights


def weighted_median(
    values: Sequence[float], weights: Sequence[float]
) -> float:
    pairs = sorted(
        (value, weight)
        for value, weight in zip(values, weights)
        if weight > 0.0
    )
    if not pairs:
        raise AnalysisError("weighted_median_empty")
    total = sum(weight for _, weight in pairs)
    midpoint = total * 0.5
    running = 0.0
    for value, weight in pairs:
        running += weight
        if running >= midpoint:
            return value
    return pairs[-1][0]


def percentile(values: Sequence[float], fraction: float) -> float:
    """Linear-interpolation percentile (numpy ``linear`` method)."""
    if not values:
        raise AnalysisError("percentile_empty")
    ordered = sorted(values)
    rank = fraction * (len(ordered) - 1)
    lower = int(math.floor(rank))
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def _read_truth(path: Path, expected_scenario_id: str) -> list[dict[str, Any]]:
    if not path.is_file():
        raise AnalysisError(f"missing_truth_file:{path}")
    records = []
    with path.open() as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exception:
                raise AnalysisError(
                    f"truth_parse_error:line {line_number}:{exception}"
                ) from exception
            if record.get("schema_version") != TRUTH_SCHEMA:
                raise AnalysisError(
                    f"truth_schema_mismatch:line {line_number}"
                )
            if record.get("scenario_id") != expected_scenario_id:
                raise AnalysisError(
                    f"truth_scenario_mismatch:line {line_number}"
                )
            records.append(record)
    if not records:
        raise AnalysisError("truth_file_empty")
    previous_id = None
    for record in records:
        frame_id = record.get("frame_id")
        if not isinstance(frame_id, int) or isinstance(frame_id, bool):
            raise AnalysisError("truth_frame_id_invalid")
        if previous_id is not None and frame_id != previous_id + 1:
            raise AnalysisError(
                f"truth_frame_sequence_break:{previous_id}->{frame_id}"
            )
        previous_id = frame_id
    return records


def _collect_inputs(
    runtime: Path,
    run_directory: Path,
    scenario_path: Path,
    margin_artifact_path: Path,
    body_config_path: Path,
) -> None:
    """Create-once collection of every analysis input into the run
    directory (round 13 §B.3). After collection the run directory is
    self-contained; later Plays or deleted shared files cannot affect
    this run's evidence."""
    truth_destination = run_directory / TRUTH_FILE_NAME
    if not truth_destination.exists():
        truth_source = runtime / TRUTH_FILE_NAME
        if not truth_source.is_file():
            raise AnalysisError(f"missing_truth_file:{truth_source}")
        shutil.copyfile(truth_source, truth_destination)
    manifest = _load_json(run_directory / "manifest.json")
    cli_args = manifest.get("cli_args", {})
    sources = {
        "scenario.json": scenario_path,
        "margin.json": margin_artifact_path,
        "body_config.json": body_config_path,
        "reanchor_config.json": cli_args.get("reanchor_config"),
        "tracker_model_spec.json": cli_args.get("tracker_model_spec"),
    }
    for name in RUN_BOUND_INPUTS:
        destination = run_directory / name
        if destination.exists():
            continue
        source = sources[name]
        if source is None or not Path(source).is_file():
            raise AnalysisError(f"missing_collect_source:{name}")
        shutil.copyfile(Path(source), destination)


A1_PREDECESSOR_HOLD_DIR_NAME = (
    "p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold"
)
A1_PREDECESSOR_HOLD_FILES = ("frames.jsonl", "manifest.json")


def _check_a1_predecessor_hold(runtime: Path) -> None:
    """Bind A1's attempt-4 analysis to the real attempt-3 void hold.

    Round 30 §C.3. Read-only and metric-free: it enumerates the hold's direct
    file names and hashes their raw bytes. It never parses void content and
    never computes any metric, so "do not analyse void artifacts" still holds.
    Declaring the predecessor SHAs in the receipt is not enough — a missing or
    rewritten hold must fail closed *before* anything is collected or written.
    """
    hold = runtime / "runs" / A1_PREDECESSOR_HOLD_DIR_NAME
    if not hold.is_dir():
        raise AnalysisError(f"a1_predecessor_hold_missing:{hold}")
    actual_files = sorted(entry.name for entry in hold.iterdir() if entry.is_file())
    if actual_files != sorted(A1_PREDECESSOR_HOLD_FILES):
        raise AnalysisError(
            f"a1_predecessor_hold_file_set_mismatch:{actual_files}"
        )
    if _sha256(hold / "frames.jsonl") != A1_PREDECESSOR_VOID_FRAMES_SHA256:
        raise AnalysisError("a1_predecessor_void_frames_sha256_mismatch")
    if _sha256(hold / "manifest.json") != A1_PREDECESSOR_VOID_MANIFEST_SHA256:
        raise AnalysisError("a1_predecessor_void_manifest_sha256_mismatch")


A2_PREDECESSOR_HOLD_DIR_NAME = (
    "p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold"
)
# Round 42 §B (BC-BODY1-27): the void attempt-1 site is a completed run
# directory, so its file set is the full ten - not A1's two. Three of them are
# pinned by SHA-256 (the frozen table in round 42 §B); the other seven only
# have to be present.
A2_PREDECESSOR_HOLD_FILES = (
    "frames.jsonl",
    "manifest.json",
    "m3_body_truth.jsonl",
    "metrics.final.json",
    "summary.json",
    "scenario.json",
    "margin.json",
    "body_config.json",
    "reanchor_config.json",
    "tracker_model_spec.json",
)
A2_PREDECESSOR_VOID_FRAMES_SHA256 = (
    "a7939b7ce0a54a52487859b3ed1e12d3f0b6526759ab5e77925c49980309fc54"
)
A2_PREDECESSOR_VOID_MANIFEST_SHA256 = (
    "d9774905aab324acf05c7616d0bf9e8a0ccf8f10c3855dd5c8c4ff1f9ea4a50c"
)
A2_PREDECESSOR_VOID_TRUTH_SHA256 = (
    "6f3e5238ef0057253f1228ec4aa9fdd53c2557dd00bc01d2df1782e90635f095"
)


def _check_a2_predecessor_hold(runtime: Path) -> None:
    """Bind A2's attempt-2 analysis to the real attempt-1 void hold.

    Round 42 §B (BC-BODY1-27), modelled on ``_check_a1_predecessor_hold``:
    read-only and metric-free. It enumerates the hold's direct file names and
    hashes the raw bytes of the three pinned files. It never parses void
    content and never computes any void metric, and it runs before anything is
    collected or written, so a missing or rewritten hold fails closed instead
    of yielding a passing attempt-2 analysis. It fires for the A2 acquisition
    only; the other nine runs never reach it.
    """
    hold = runtime / "runs" / A2_PREDECESSOR_HOLD_DIR_NAME
    if not hold.is_dir():
        raise AnalysisError(f"a2_predecessor_hold_missing:{hold}")
    actual_files = sorted(entry.name for entry in hold.iterdir() if entry.is_file())
    if actual_files != sorted(A2_PREDECESSOR_HOLD_FILES):
        raise AnalysisError(
            f"a2_predecessor_hold_file_set_mismatch:{actual_files}"
        )
    if _sha256(hold / "frames.jsonl") != A2_PREDECESSOR_VOID_FRAMES_SHA256:
        raise AnalysisError("a2_predecessor_void_frames_sha256_mismatch")
    if _sha256(hold / "manifest.json") != A2_PREDECESSOR_VOID_MANIFEST_SHA256:
        raise AnalysisError("a2_predecessor_void_manifest_sha256_mismatch")
    if _sha256(hold / TRUTH_FILE_NAME) != A2_PREDECESSOR_VOID_TRUTH_SHA256:
        raise AnalysisError("a2_predecessor_void_truth_sha256_mismatch")


COMPLETION_CONFIRMATION_WORD = "TRACKER_AUTO_COMPLETE_CONFIRMED"
COMPLETION_MINIMUM_DURATION_S = 130.0


def validate_completion(
    runtime: Path,
    run_id: str,
    tracker_exit_code: int,
    tracker_final_json: str,
) -> str:
    """Round 30 §C.4: the mechanical source of the completion word.

    Read-only and write-free. Every condition of the §C.3 handshake is an AND;
    any failure raises a named ``AnalysisError``. It never calls
    ``finalize_run`` and never creates or modifies a file, so it cannot turn an
    unfinished run into a finished one.
    """
    if tracker_exit_code != 0:
        raise AnalysisError(f"completion_tracker_exit_code_nonzero:{tracker_exit_code}")
    try:
        final = json.loads(tracker_final_json)
    except (TypeError, json.JSONDecodeError) as exception:
        raise AnalysisError(
            f"completion_final_json_unparseable:{exception}"
        ) from exception
    if not isinstance(final, dict):
        raise AnalysisError("completion_final_json_not_object")
    if final.get("run_id") != run_id:
        raise AnalysisError(f"completion_final_json_run_id_mismatch:{final.get('run_id')}")

    run_directory = (runtime / "runs" / run_id).resolve()
    summary_path = run_directory / "summary.json"
    metrics_final_path = run_directory / "metrics.final.json"

    declared_summary = final.get("summary")
    if not isinstance(declared_summary, str) or not declared_summary:
        raise AnalysisError("completion_final_json_summary_missing")
    if Path(declared_summary).resolve() != summary_path:
        raise AnalysisError(f"completion_summary_path_mismatch:{declared_summary}")

    if not summary_path.is_file():
        raise AnalysisError("completion_summary_file_missing")
    if not metrics_final_path.is_file():
        raise AnalysisError("completion_metrics_final_missing")

    manifest_path = run_directory / "manifest.json"
    if not manifest_path.is_file():
        raise AnalysisError("completion_manifest_missing")
    manifest = _load_json(manifest_path)
    if manifest.get("run_id") != run_id:
        raise AnalysisError(
            f"completion_manifest_run_id_mismatch:{manifest.get('run_id')}"
        )

    summary = _load_json(summary_path)
    if summary.get("metrics_snapshot_present") is not True:
        raise AnalysisError(
            f"completion_metrics_snapshot_absent:{summary.get('metrics_snapshot_present')}"
        )
    duration = summary.get("actual_duration_s")
    if not isinstance(duration, (int, float)) or isinstance(duration, bool):
        raise AnalysisError(f"completion_duration_not_numeric:{duration}")
    if not math.isfinite(float(duration)):
        raise AnalysisError(f"completion_duration_not_finite:{duration}")
    if float(duration) < COMPLETION_MINIMUM_DURATION_S:
        raise AnalysisError(f"completion_duration_below_watchdog:{duration}")
    return COMPLETION_CONFIRMATION_WORD


def canonical_trial_id(acquisition_run_id: str) -> str:
    """Map an admissible acquisition ID to its canonical trial slot.

    Round 29 §C.2, extended by round 42 §B (BC-BODY1-26). Exactly ten
    acquisition IDs are admissible: A1 is acquired under
    ``A1_ACQUISITION_RUN_ID`` and A2 under ``A2_ACQUISITION_RUN_ID``, each
    mapping to its canonical slot; the other eight are their own canonical
    slot. Both original IDs are permanently rejected — the attempt-3 and
    attempt-1 void sites consumed them — and every other attempt suffix is
    rejected outright, so a later attempt cannot silently claim the slot.
    """
    if acquisition_run_id == A1_ACQUISITION_RUN_ID:
        return A1_CANONICAL_TRIAL_ID
    if acquisition_run_id == A2_ACQUISITION_RUN_ID:
        return A2_CANONICAL_TRIAL_ID
    if acquisition_run_id in (A1_CANONICAL_TRIAL_ID, A2_CANONICAL_TRIAL_ID):
        raise AnalysisError(f"run_id_void_consumed:{acquisition_run_id}")
    for arm in ("a", "b"):
        for index in range(1, TRIALS_PER_ARM + 1):
            frozen = frozen_run_id(arm, index)
            if acquisition_run_id == frozen:
                return frozen
    raise AnalysisError(f"run_id_not_frozen_trial:{acquisition_run_id}")


def expected_acquisition_ids(arm: str) -> list[str]:
    """The frozen acquisition-ID sequence for one arm, in pairing order."""
    ids = [frozen_run_id(arm, index + 1) for index in range(TRIALS_PER_ARM)]
    if arm == "a":
        ids[0] = A1_ACQUISITION_RUN_ID
        ids[1] = A2_ACQUISITION_RUN_ID
    return ids


def _expected_policy(run_id: str) -> str:
    """Expected arm policy derived from the acquisition ID alone (round 14
    §B.2, extended by round 29 §C.2): the ID maps to exactly one canonical
    slot and that slot fixes the arm - A must be hold, B must be threshold."""
    canonical = canonical_trial_id(run_id)
    for arm, policy in ((("a"), ARM_A_POLICY), (("b"), ARM_B_POLICY)):
        for index in range(1, TRIALS_PER_ARM + 1):
            if canonical == frozen_run_id(arm, index):
                return policy
    raise AnalysisError(f"run_id_not_frozen_trial:{run_id}")


def _check_identity(
    manifest: Mapping[str, Any],
    run_id: str,
    scenario: Mapping[str, Any],
    scenario_sha256: str,
    body_config_sha256: str,
    reanchor_config_sha256: str,
    model_spec: Mapping[str, Any],
    expected_policy: str,
) -> dict[str, Any]:
    """Mechanical admissibility/identity checks (round 12 §B.5,
    round 13 §B.4, round 14 §B.2 three-layer arm identity)."""
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise AnalysisError("manifest_schema_mismatch")
    if manifest.get("run_id") != run_id:
        raise AnalysisError("manifest_run_id_mismatch")
    scenario_id = scenario.get("scenario_id")
    if manifest.get("scenario_id") != scenario_id:
        raise AnalysisError("manifest_scenario_mismatch")
    cli_args = manifest.get("cli_args", {})
    policy = cli_args.get("body_policy")
    if policy != expected_policy:
        raise AnalysisError(
            f"arm_policy_not_frozen_expectation:{policy}!={expected_policy}"
        )
    if cli_args.get("tracker") != TRACKER_NAME:
        raise AnalysisError("tracker_identity_mismatch")
    if cli_args.get("condition") != "follow":
        raise AnalysisError("condition_mismatch")
    expected_track = scenario.get("target", {}).get("track_id")
    if cli_args.get("track_id") != expected_track:
        raise AnalysisError("track_id_mismatch")
    route_y = scenario["target"]["route_world_m"][0]["y"]
    ground_plane = cli_args.get("ground_plane_y_m")
    if ground_plane is None or abs(float(ground_plane) - float(route_y)) > 1e-9:
        raise AnalysisError("ground_plane_mismatch")
    tracker_identity = manifest.get("tracker") or {}
    if tracker_identity.get("name") != TRACKER_NAME:
        raise AnalysisError("tracker_manifest_identity_mismatch")
    expected_models = {
        name: _finite_free_sha(model.get("sha256"), f"models.{name}")
        for name, model in (model_spec.get("models") or {}).items()
    }
    if not expected_models:
        raise AnalysisError("tracker_model_spec_models_missing")
    if tracker_identity.get("model_sha256") != expected_models:
        raise AnalysisError("tracker_model_sha256_mismatch")
    reanchor_identity = manifest.get("reanchor") or {}
    if reanchor_identity.get("config_sha256") != reanchor_config_sha256:
        raise AnalysisError("reanchor_config_hash_mismatch")
    body_identity = manifest.get("body_planner") or {}
    if not body_identity:
        raise AnalysisError("body_planner_identity_missing")
    if body_identity.get("policy") != expected_policy:
        raise AnalysisError(
            "manifest_policy_mismatch:"
            f"{body_identity.get('policy')}!={expected_policy}"
        )
    if body_identity.get("config_sha256") != body_config_sha256:
        raise AnalysisError("body_config_hash_mismatch")
    if body_identity.get("scenario_config_sha256") != scenario_sha256:
        raise AnalysisError("body_scenario_hash_mismatch")
    if body_identity.get("planner") != POLICY_PLANNER[expected_policy]:
        raise AnalysisError(
            f"policy_planner_mismatch:{expected_policy}->"
            f"{body_identity.get('planner')}"
        )
    init = manifest.get("init") or {}
    init_box = init.get("box_norm")
    if not isinstance(init_box, list) or len(init_box) != 4:
        raise AnalysisError("init_box_missing")
    # Round 15 §B.1: the manifest init frame ID is mandatory and must be a
    # plain non-negative integer. A missing field previously flowed into the
    # receipt as ``null``, which let a run claim an init identity it never
    # published.
    init_frame_id = init.get("frame_id")
    if (
        not isinstance(init_frame_id, int)
        or isinstance(init_frame_id, bool)
        or init_frame_id < 0
    ):
        raise AnalysisError(
            f"manifest_init_frame_id_invalid:{init_frame_id!r}"
        )
    return {
        "body_policy": policy,
        "body_planner_name": body_identity.get("planner"),
        "condition": cli_args.get("condition"),
        "track_id": cli_args.get("track_id"),
        "ground_plane_y_m": float(ground_plane),
        "tracker": cli_args.get("tracker"),
        "tracker_pinned_version": tracker_identity.get("pinned_version"),
        "tracker_backend": tracker_identity.get("backend"),
        "tracker_model_sha256": dict(expected_models),
        "reanchor_config_sha256": reanchor_config_sha256,
        "tracker_model_spec_sha256": None,  # filled by caller
        "init_box_norm": [float(value) for value in init_box],
        "init_frame_id": init_frame_id,
    }


_SHA256_HEX_CHARS = set("0123456789abcdef")


def _sha256_hex(value: Any, name: str) -> str:
    """A 64-character lowercase hex digest, or a named fail-closed abort."""
    if (
        not isinstance(value, str)
        or len(value) != 64
        or not set(value) <= _SHA256_HEX_CHARS
    ):
        raise AnalysisError(f"sha256_not_hex64:{name}")
    return value


def _counter(record: Mapping[str, Any], key: str) -> int:
    """Round 17 §B.3: ``backlog_count``/``skipped_count`` must be plain
    non-negative integers - they classify a row as planner decision or as
    legal catch-up, so a bool or float alias is not admissible."""
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise AnalysisError(
            f"frame_counter_invalid:{record.get('frame_id')}:{key}:{value!r}"
        )
    return value


def _require_pin_equal(actual: Any, expected: Any, name: str) -> str:
    """Round 17 §B.1: both sides must be hex-64 and equal (F1 hard gate)."""
    actual_hex = _sha256_hex(actual, f"{name}.actual")
    expected_hex = _sha256_hex(expected, f"{name}.pin")
    if actual_hex != expected_hex:
        raise AnalysisError(
            f"{name}_pin_mismatch:{actual_hex}!={expected_hex}"
        )
    return actual_hex


def _finite_free_sha(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise AnalysisError(f"model_sha_invalid:{name}")
    return value


def _domain(
    records: Sequence[Mapping[str, Any]],
    mileages: Sequence[float],
    lower: float,
    upper: float,
) -> tuple[list[Mapping[str, Any]], list[float], list[float]]:
    selected = [
        (record, mileage)
        for record, mileage in zip(records, mileages)
        if lower <= mileage <= upper
    ]
    domain_records = [record for record, _ in selected]
    domain_mileages = [mileage for _, mileage in selected]
    weights = trapezoidal_weights(domain_mileages, lower, upper)
    return domain_records, domain_mileages, weights


def _weighted_share(
    records: Sequence[Mapping[str, Any]],
    weights: Sequence[float],
    key: str,
) -> float:
    total = sum(weights)
    if total <= 0.0:
        raise AnalysisError(f"zero_mileage_domain:{key}")
    return (
        sum(weight for weight, record in zip(weights, records) if record[key])
        / total
    )


def _quality_samples(
    records: Sequence[Mapping[str, Any]],
    sensor_w: float,
    sensor_h: float,
) -> tuple[list[float], list[float], list[float]]:
    """C_quality sample triples, geometrically-visible frames only.

    An occluded target can still project a box; BC-BODY1-2 bars occluded
    frames from every denominator, so ``truth_box_available`` alone is not
    sufficient (round 12 §A.4(b)/§B.3).
    """
    areas, min_sides, center_errors = [], [], []
    for record in records:
        if not (record["geometrically_visible"] and record["truth_box_available"]):
            continue
        areas.append(
            record["truth_box_width"]
            * sensor_w
            * record["truth_box_height"]
            * sensor_h
        )
        min_sides.append(
            min(
                record["truth_box_width"] * sensor_w,
                record["truth_box_height"] * sensor_h,
            )
        )
        center_errors.append(
            _finite(record["target_center_error_px"], "target_center_error_px")
        )
    return areas, min_sides, center_errors


def _per_position_series(
    records: Sequence[Mapping[str, Any]],
    mileages: Sequence[float],
    sensor_w: float,
    sensor_h: float,
    grid: Sequence[float],
    half_spacing: float,
) -> dict[float, tuple[float, float, float]]:
    """Per-grid-point (area_px, min_side_ge20_indicator, center_error_px)
    for H2 pairing (round 13 §B.2: the third component is the frozen
    indicator, never raw pixels).

    Each grid point takes the nearest eligible (geometrically visible,
    boxed) sample within half the frozen grid spacing; otherwise the grid
    point is absent and drops out of both runs symmetrically.
    """
    eligible = [
        (mileage, record)
        for record, mileage in zip(records, mileages)
        if record["geometrically_visible"] and record["truth_box_available"]
    ]
    series: dict[float, tuple[float, float, float]] = {}
    for point in grid:
        best = None
        for mileage, record in eligible:
            distance = abs(mileage - point)
            if distance <= half_spacing and (
                best is None or distance < best[0]
            ):
                best = (distance, record)
        if best is None:
            continue
        record = best[1]
        min_side = min(
            record["truth_box_width"] * sensor_w,
            record["truth_box_height"] * sensor_h,
        )
        series[point] = (
            record["truth_box_width"]
            * sensor_w
            * record["truth_box_height"]
            * sensor_h,
            1.0 if min_side >= MIN_SIDE_PX else 0.0,
            record["target_center_error_px"],
        )
    return series


def analyze_trial(
    runtime: Path,
    run_id: str,
    scenario_path: Path,
    margin_artifact_path: Path,
    body_config_path: Path,
    verify: bool = False,
) -> dict[str, Any]:
    run_directory = runtime / "runs" / run_id
    if not run_directory.is_dir():
        raise AnalysisError(f"missing_run_directory:{run_directory}")
    expected_policy = _expected_policy(run_id)
    # Round 30 §C.3: for the A1 acquisition the predecessor void hold must be
    # bound to real bytes *before* anything is collected or written, so a
    # missing or rewritten hold can never yield a passing attempt-4 analysis.
    if run_id == A1_ACQUISITION_RUN_ID:
        _check_a1_predecessor_hold(runtime)
    # Round 42 §B (BC-BODY1-27): the same read-only, metric-free binding for
    # the A2 acquisition and its attempt-1 void hold.
    if run_id == A2_ACQUISITION_RUN_ID:
        _check_a2_predecessor_hold(runtime)
    if verify:
        for name in (*RUN_BOUND_INPUTS, TRUTH_FILE_NAME):
            if not (run_directory / name).is_file():
                raise AnalysisError(f"verify_requires_collected_inputs:{name}")
    else:
        _collect_inputs(
            runtime,
            run_directory,
            scenario_path,
            margin_artifact_path,
            body_config_path,
        )
    # Every read below is run-directory-only (round 13 §B.3).
    scenario = _load_json(run_directory / "scenario.json")
    scenario_sha256 = _sha256(run_directory / "scenario.json")
    margin_artifact = _load_json(run_directory / "margin.json")
    margin_sha256 = _sha256(run_directory / "margin.json")
    body_config = _load_json(run_directory / "body_config.json")
    body_config_sha256 = _sha256(run_directory / "body_config.json")
    reanchor_config_sha256 = _sha256(run_directory / "reanchor_config.json")
    model_spec = _load_json(run_directory / "tracker_model_spec.json")
    model_spec_sha256 = _sha256(run_directory / "tracker_model_spec.json")

    identity = margin_artifact.get("identity", {})
    if identity.get("scenario_sha256") != scenario_sha256:
        raise AnalysisError("scenario_hash_not_frozen_artifact")
    if identity.get("scenario_id") != scenario.get("scenario_id"):
        raise AnalysisError("scenario_id_not_frozen_artifact")
    # Round 17 §B.1 (Review F1): the margin artifact defines the measurement
    # window and the visible arc, so its bytes must equal the pins frozen in
    # the run-bound body config before the window is used for anything. A
    # pre-seeded or drifted margin previously passed the identity check and
    # silently redefined the primary metric domain.
    window_pins = body_config.get("measurement_window", {})
    _require_pin_equal(
        margin_sha256,
        window_pins.get("artifact_sha256"),
        "margin_artifact",
    )
    _require_pin_equal(
        (margin_artifact.get("visible_arc") or {}).get("sha256"),
        window_pins.get("visible_arc_sha256"),
        "visible_arc",
    )
    visible_arc = margin_artifact.get("visible_arc", {})
    window = visible_arc.get("measurement_window_m")
    if (
        not isinstance(window, list)
        or len(window) != 2
        or window[0] != 0.0
    ):
        raise AnalysisError("measurement_window_not_route_zero_based")
    window_length_m = _finite(window[1], "measurement_window_m[1]")

    manifest = _load_json(run_directory / "manifest.json")
    identity_fields = _check_identity(
        manifest,
        run_id,
        scenario,
        scenario_sha256,
        body_config_sha256,
        reanchor_config_sha256,
        model_spec,
        expected_policy,
    )
    identity_fields["tracker_model_spec_sha256"] = model_spec_sha256
    sigma_px = _finite(
        body_config.get("calibration", {}).get("sigma_px"), "sigma_px"
    )
    grid_spacing = _finite(
        body_config.get("measurement_window", {}).get(
            "route_sample_spacing_m"
        ),
        "route_sample_spacing_m",
    )

    frames_path = run_directory / "frames.jsonl"
    if not frames_path.is_file():
        raise AnalysisError("missing_frames_jsonl")
    raw_records, truncated_lines = read_frame_records(frames_path)
    if truncated_lines:
        raise AnalysisError("frames_jsonl_truncated_tail")
    frame_records = [
        record
        for record in raw_records
        if record.get("record_kind", "frame") == "frame"
    ]
    if not frame_records:
        raise AnalysisError("no_frame_records")

    truth_records = _read_truth(
        run_directory / TRUTH_FILE_NAME, scenario.get("scenario_id")
    )
    truth_by_frame = {record["frame_id"]: record for record in truth_records}
    missing = [
        record["frame_id"]
        for record in frame_records
        if record["frame_id"] not in truth_by_frame
    ]
    if missing:
        raise AnalysisError(f"truth_coverage_gap:{missing[:5]}")
    # Per-frame binding, stage partition and planner identity (round 13
    # §B.4, round 14 §B.1/§B.2, round 15 §B.1/§B.2): every tracker frame
    # record must carry a finite ``capture_monotonic_s`` matching the truth
    # record for the same frame (<= 1e-9 s); ``compute_stage`` is then
    # enumerated into exactly one ``init`` row - whose frame ID must equal
    # the manifest ``init.frame_id`` - and one or more ``update`` rows, with
    # no other value tolerated. Planner identity is only checked after that
    # trusted partition, so relabelling update rows as ``init`` can no longer
    # hide them from the planner check; update rows are then split into
    # planner decisions and legal catch-up by the recorded production
    # counters (round 17 §B.3). A foreign, shifted or mislabeled stream
    # fails here instead of being registered under the wrong arm.
    expected_planner = POLICY_PLANNER[expected_policy]
    manifest_init_frame_id = identity_fields["init_frame_id"]
    init_records: list[Mapping[str, Any]] = []
    update_records: list[Mapping[str, Any]] = []
    for record in frame_records:
        capture = record.get("capture_monotonic_s")
        if capture is None or isinstance(capture, bool) or not math.isfinite(
            float(capture)
            if isinstance(capture, (int, float))
            else float("nan")
        ):
            raise AnalysisError(
                f"tracker_capture_missing:{record.get('frame_id')}"
            )
        truth_capture = truth_by_frame[record["frame_id"]].get(
            "capture_monotonic_s"
        )
        if (
            truth_capture is None
            or isinstance(truth_capture, bool)
            or not isinstance(truth_capture, (int, float))
            or not math.isfinite(float(truth_capture))
            or abs(float(capture) - float(truth_capture)) > 1e-9
        ):
            raise AnalysisError(
                f"truth_frame_binding_mismatch:{record['frame_id']}"
            )
        stage = record.get("compute_stage")
        if stage == "init":
            init_records.append(record)
        elif stage == "update":
            update_records.append(record)
        else:
            raise AnalysisError(
                f"frame_compute_stage_invalid:{record['frame_id']}:{stage!r}"
            )
    if len(init_records) != 1:
        raise AnalysisError(f"init_frame_record_count:{len(init_records)}")
    init_record = init_records[0]
    if init_record["frame_id"] != manifest_init_frame_id:
        raise AnalysisError(
            "init_frame_id_mismatch:"
            f"{init_record['frame_id']}!={manifest_init_frame_id}"
        )
    if not update_records:
        raise AnalysisError("no_update_frame_with_expected_planner")
    if _counter(init_record, "backlog_count") != 0 or _counter(
        init_record, "skipped_count"
    ) != 0:
        raise AnalysisError(
            f"init_frame_counters_not_zero:{init_record['frame_id']}"
        )
    init_planner = init_record.get("body_planner")
    if init_planner is not None and (
        not isinstance(init_planner, Mapping)
        or init_planner.get("name") != expected_planner
    ):
        raise AnalysisError(
            f"init_frame_planner_mismatch:{init_record['frame_id']}"
        )
    # Round 17 §B.3 (Review F2): production runs ``_body_step`` only on the
    # latest frame of each batch (``track_loop.process_available``), so a
    # legal catch-up row carries ``skipped_count=1`` with a positive backlog
    # and deliberately no ``body_planner``. Classify by those two recorded
    # counters instead of demanding a planner on every update row - the
    # unconditional demand would have killed every real trial - and keep the
    # omission admissible *only* in that exact shape.
    decision_updates = 0
    for record in update_records:
        frame_id = record["frame_id"]
        backlog = _counter(record, "backlog_count")
        skipped = _counter(record, "skipped_count")
        planner = record.get("body_planner")
        if skipped == 0:
            if (
                not isinstance(planner, Mapping)
                or planner.get("name") != expected_planner
            ):
                raise AnalysisError(
                    f"update_frame_planner_mismatch:{frame_id}"
                )
            decision_updates += 1
        elif skipped == 1:
            if backlog < 1:
                raise AnalysisError(
                    f"catch_up_frame_backlog_invalid:{frame_id}:{backlog}"
                )
            if planner is not None:
                raise AnalysisError(
                    f"catch_up_frame_carries_planner:{frame_id}"
                )
        else:
            raise AnalysisError(
                f"update_frame_skipped_count_invalid:{frame_id}:{skipped}"
            )
    if decision_updates == 0:
        raise AnalysisError("no_decision_update_frame")

    vertices = _route_points(scenario)
    cumulative, perimeter = _cumulative_lengths(vertices)
    mileages = []
    for record in truth_records:
        mileage, off_route = route_mileage(
            (
                _finite(record["target_world_x_m"], "target_world_x_m"),
                _finite(record["target_world_z_m"], "target_world_z_m"),
            ),
            vertices,
            cumulative,
        )
        if off_route > OFF_ROUTE_TOL_M:
            raise AnalysisError(
                f"truth_off_route:frame {record['frame_id']}:{off_route:.6f}"
            )
        mileages.append(mileage)
    unwrapped = _unwrap_mileage(mileages, perimeter)
    if unwrapped[0] > START_MILEAGE_TOL_M:
        raise AnalysisError(
            f"trial_not_started_at_route_zero:{unwrapped[0]:.3f}"
        )
    final_mileage = max(unwrapped)
    if final_mileage < perimeter:
        raise AnalysisError(
            f"trial_invalid_no_single_loop:{final_mileage:.3f}"
        )
    # Round 42 §A (BC-BODY1-23): the ``>= 2.0 * perimeter`` admissibility arm
    # is retired. "Exactly one closure" is carried by the ``[0, P)`` sample
    # filter below, not by how far the Play ran, so laps two and later neither
    # enter H1 nor void the trial. Retiring an upper bound must not loosen the
    # domain, so two compensating domain-integrity gates take its place: the
    # unwrapped series may never step backwards, and no sample may fall back
    # below ``P`` once the loop has closed. Both are checked over the whole
    # series, and the post-closure gate runs first on purpose: a post-closure
    # sample below ``P`` is necessarily also a backward step, so testing
    # monotonicity first would make that branch unreachable.
    closure_index = next(
        (
            index
            for index, mileage in enumerate(unwrapped)
            if mileage >= perimeter
        ),
        None,
    )
    if closure_index is not None:
        for index in range(closure_index + 1, len(unwrapped)):
            if unwrapped[index] < perimeter:
                raise AnalysisError(
                    "loop_domain_sample_below_perimeter_after_closure:"
                    f"{index}:{unwrapped[index]:.3f}"
                )
    for index in range(1, len(unwrapped)):
        if unwrapped[index] < unwrapped[index - 1]:
            raise AnalysisError(
                "loop_domain_unwrapped_backward_step:"
                f"{index}:{unwrapped[index - 1]:.3f}->{unwrapped[index]:.3f}"
            )

    # The loop domain is [0, P): the first post-closure sample belongs to
    # the second lap and must not enter H1.
    loop_pairs = [
        (record, mileage)
        for record, mileage in zip(truth_records, unwrapped)
        if mileage < perimeter
    ]
    loop_records = [record for record, _ in loop_pairs]
    loop_mileages = [mileage for _, mileage in loop_pairs]
    loop_weights = trapezoidal_weights(loop_mileages, 0.0, perimeter)
    window_records, window_mileages, window_weights = _domain(
        truth_records, unwrapped, 0.0, window_length_m
    )
    if len(window_records) < 2:
        raise AnalysisError("measurement_window_empty")

    h1_c_geom = _weighted_share(
        loop_records, loop_weights, "geometrically_visible"
    )

    tracking_iou_threshold = _finite(
        scenario.get("evaluation", {}).get("tracking_iou_threshold"),
        "tracking_iou_threshold",
    )
    records_by_frame = {record["frame_id"]: record for record in frame_records}
    geom_weights = []
    track_weights = []
    for record, weight in zip(window_records, window_weights):
        if not record["geometrically_visible"]:
            continue
        geom_weights.append(weight)
        tracker = records_by_frame.get(record["frame_id"])
        success = False
        if (
            tracker is not None
            and tracker.get("ok")
            and tracker.get("box_norm") is not None
            and record["truth_box_available"]
        ):
            truth_box = [
                record["truth_box_x"],
                record["truth_box_y"],
                record["truth_box_width"],
                record["truth_box_height"],
            ]
            success = (
                box_iou(tracker["box_norm"], truth_box)
                >= tracking_iou_threshold
            )
        track_weights.append(weight if success else 0.0)
    geom_total = sum(geom_weights)
    if geom_total <= 0.0:
        raise AnalysisError("no_geometrically_visible_window_frames")
    c_track_given_geom = sum(track_weights) / geom_total
    c_track_window = sum(track_weights) / sum(window_weights)

    sensor_w = _finite(scenario.get("sensor", {}).get("width"), "sensor.width")
    sensor_h = _finite(
        scenario.get("sensor", {}).get("height"), "sensor.height"
    )
    areas, min_sides, center_errors = _quality_samples(
        window_records, sensor_w, sensor_h
    )
    sample_weights = [
        weight
        for record, weight in zip(window_records, window_weights)
        if record["geometrically_visible"] and record["truth_box_available"]
    ]
    if not areas or sum(sample_weights) <= 0.0:
        raise AnalysisError("c_quality_window_empty")
    c_quality = {
        "area_median_px": weighted_median(areas, sample_weights),
        "min_side_ge20_share": (
            sum(
                weight
                for side, weight in zip(min_sides, sample_weights)
                if side >= MIN_SIDE_PX
            )
            / sum(sample_weights)
        ),
        "center_error_median_px": weighted_median(center_errors, sample_weights),
    }
    tails = {
        "center_error_max_px": max(center_errors),
        "center_error_p90_px": percentile(center_errors, 0.9),
    }

    saturation = {
        "window_gimbal_saturated_share": _weighted_share(
            window_records, window_weights, "gimbal_saturated"
        ),
        "window_tether_saturated_share": _weighted_share(
            window_records, window_weights, "tether_saturated"
        ),
        "loop_gimbal_saturated_share": _weighted_share(
            loop_records, loop_weights, "gimbal_saturated"
        ),
        "loop_tether_saturated_share": _weighted_share(
            loop_records, loop_weights, "tether_saturated"
        ),
    }

    # Cost axis (round 12 §B.5): effort integrates the plant's applied
    # velocity over simulation-time deltas (pause-safe; requested/published
    # commands never enter), and the body path integrates actual positions.
    effort_m = 0.0
    body_path_length_m = 0.0
    previous_sim = None
    previous_body = None
    for record in loop_records:
        sim = _finite(record["simulation_time_s"], "simulation_time_s")
        body = (
            _finite(record["body_world_x_m"], "body_world_x_m"),
            _finite(record["body_world_y_m"], "body_world_y_m"),
            _finite(record["body_world_z_m"], "body_world_z_m"),
        )
        if previous_sim is not None:
            dt = max(sim - previous_sim, 0.0)
            applied = math.sqrt(
                _finite(record["applied_velocity_x_mps"], "applied_vx") ** 2
                + _finite(record["applied_velocity_y_mps"], "applied_vy") ** 2
                + _finite(record["applied_velocity_z_mps"], "applied_vz") ** 2
            )
            effort_m += applied * dt
            body_path_length_m += math.dist(previous_body, body)
        previous_sim = sim
        previous_body = body

    planner_switches = 0
    previous_mode = None
    for record in frame_records:
        planner = record.get("body_planner")
        if planner is None:
            continue
        mode = planner.get("mode")
        if previous_mode is not None and mode != previous_mode:
            planner_switches += 1
        previous_mode = mode

    mileage_by_frame = {
        record["frame_id"]: mileage
        for record, mileage in zip(truth_records, unwrapped)
    }
    nees_values = []
    nis_values = []
    residuals_px = []
    for record in frame_records:
        estimate = record.get("world_estimate")
        truth = truth_by_frame[record["frame_id"]]
        if estimate and estimate.get("step") == "fused":
            mean = estimate.get("mean")
            covariance = estimate.get("covariance")
            if mean and covariance:
                err_x = mean[0] - truth["target_world_x_m"]
                err_z = mean[1] - truth["target_world_z_m"]
                a, b = covariance[0][0], covariance[0][1]
                c, d = covariance[1][0], covariance[1][1]
                det = a * d - b * c
                if det > 0.0:
                    nees_values.append(
                        (d * err_x * err_x - (b + c) * err_x * err_z
                         + a * err_z * err_z)
                        / det
                    )
            if estimate.get("nis") is not None:
                nis_values.append(float(estimate["nis"]))
        if (
            record.get("ok")
            and record.get("box_norm") is not None
            and truth["truth_box_available"]
            and truth["geometrically_visible"]
            and mileage_by_frame[record["frame_id"]] <= window_length_m
        ):
            box = record["box_norm"]
            pred_cx = (box[0] + box[2] * 0.5) * sensor_w
            pred_cy = (box[1] + box[3] * 0.5) * sensor_h
            residuals_px.append(
                math.hypot(
                    pred_cx - truth["truth_center_x_px"],
                    pred_cy - truth["truth_center_y_px"],
                )
            )
    sigma_px_rms = (
        math.sqrt(sum(r * r for r in residuals_px) / len(residuals_px))
        if residuals_px
        else None
    )

    metrics_final_path = run_directory / "metrics.final.json"
    if not metrics_final_path.is_file():
        raise AnalysisError("missing_metrics_snapshot")
    metrics_final = _load_json(metrics_final_path)
    projection = metrics_final.get("evaluation_projection")
    if not projection:
        raise AnalysisError("metrics_projection_provenance_missing")
    aspect = _finite(
        projection.get("aspect_width_over_height"), "evaluation_projection"
    )
    if abs(aspect - sensor_w / sensor_h) > 1e-5:
        raise AnalysisError("metrics_projection_aspect_mismatch")
    online_sensor_frames = metrics_final.get("aggregate", {}).get(
        "sensor_frames"
    )

    # Per-position series for the H2 paired comparison (BC-BODY1-5): the
    # frozen grid is the body config's route_sample_spacing_m over the
    # window; cell centres keep both endpoints' half-cells symmetric. The
    # third component is the frozen 1[min_side >= 20 px] indicator
    # (round 13 §B.2).
    grid = [
        (index + 0.5) * grid_spacing
        for index in range(int(window_length_m / grid_spacing))
    ]
    series = _per_position_series(
        window_records, window_mileages, sensor_w, sensor_h, grid,
        grid_spacing * 0.5,
    )

    # Round 29 §C.2: the A1 acquisition run carries five extra binding fields
    # that tie it to its canonical slot and to the exact attempt-3 void site
    # it replaces. Round 42 §B (BC-BODY1-27) gives the A2 acquisition the same
    # conditional treatment, with the third pinned predecessor hash its void
    # site carries. These are acquisition-specific; the eight runs whose
    # acquisition ID equals their canonical slot never carry them, and no
    # other run's serialization changes.
    attempt_binding: dict[str, Any] = {}
    if run_id == A1_ACQUISITION_RUN_ID:
        attempt_binding = {
            "acquisition_run_id": A1_ACQUISITION_RUN_ID,
            "canonical_trial_id": A1_CANONICAL_TRIAL_ID,
            "attempt_number": A1_ATTEMPT_NUMBER,
            "predecessor_void_manifest_sha256": A1_PREDECESSOR_VOID_MANIFEST_SHA256,
            "predecessor_void_frames_sha256": A1_PREDECESSOR_VOID_FRAMES_SHA256,
        }
    elif run_id == A2_ACQUISITION_RUN_ID:
        attempt_binding = {
            "acquisition_run_id": A2_ACQUISITION_RUN_ID,
            "canonical_trial_id": A2_CANONICAL_TRIAL_ID,
            "attempt_number": A2_ATTEMPT_NUMBER,
            "predecessor_void_manifest_sha256": A2_PREDECESSOR_VOID_MANIFEST_SHA256,
            "predecessor_void_frames_sha256": A2_PREDECESSOR_VOID_FRAMES_SHA256,
            "predecessor_void_truth_sha256": A2_PREDECESSOR_VOID_TRUTH_SHA256,
        }

    analysis = {
        "schema_version": ANALYSIS_SCHEMA,
        "receipt": {
            "run_id": run_id,
            **attempt_binding,
            "scenario_id": scenario.get("scenario_id"),
            "scenario_sha256": scenario_sha256,
            "margin_artifact_sha256": margin_sha256,
            "visible_arc_sha256": visible_arc.get("sha256"),
            "body_config_sha256": body_config_sha256,
            **identity_fields,
            "first_frame_id": truth_records[0]["frame_id"],
            "last_frame_id": truth_records[-1]["frame_id"],
            "truth_record_count": len(truth_records),
            "frame_record_count": len(frame_records),
            "input_sha256": {
                "manifest_json": _sha256(run_directory / "manifest.json"),
                "frames_jsonl": _sha256(frames_path),
                "m3_body_truth_jsonl": _sha256(
                    run_directory / TRUTH_FILE_NAME
                ),
                "metrics_final_json": _sha256(metrics_final_path),
                "scenario_json": scenario_sha256,
                "margin_json": margin_sha256,
                "body_config_json": body_config_sha256,
                "reanchor_config_json": reanchor_config_sha256,
                "tracker_model_spec_json": model_spec_sha256,
            },
        },
        "tolerances": {
            "start_mileage_tol_m": START_MILEAGE_TOL_M,
            "start_mileage_derivation": START_MILEAGE_DERIVATION,
            "off_route_tol_m": OFF_ROUTE_TOL_M,
            "off_route_derivation": OFF_ROUTE_DERIVATION,
        },
        "domains": {
            "route_perimeter_m": perimeter,
            "final_unwrapped_mileage_m": final_mileage,
            "measurement_window_m": [0.0, window_length_m],
            "loop_frame_count": len(loop_records),
            "window_frame_count": len(window_records),
            "h2_grid_spacing_m": grid_spacing,
            "h2_grid_points": len(series),
        },
        "h1": {
            "full_loop_c_geom": h1_c_geom,
            "lower_bound": H1_LOWER_BOUND,
            "ceiling": H1_CEILING,
            "disposition": (
                "GEOMETRY_MODEL_REJECTED"
                if h1_c_geom < H1_LOWER_BOUND
                else "SCENE_DEGENERATE"
                if h1_c_geom >= H1_CEILING
                else "WITHIN_RANGE"
            ),
            "online_aggregate_c_geom_reference": metrics_final.get(
                "aggregate", {}
            ).get("c_geom"),
            "online_sensor_frames_reference": online_sensor_frames,
        },
        "window": {
            "c_track_given_geom": c_track_given_geom,
            "c_track": c_track_window,
            "tracking_iou_threshold": tracking_iou_threshold,
        },
        "c_quality": c_quality,
        "c_quality_series": {
            f"{point:.6f}": list(values) for point, values in series.items()
        },
        "tails": tails,
        "saturation": saturation,
        "cost": {
            "body_motion_effort_m": effort_m,
            "planner_switch_count": planner_switches,
            "body_path_length_m": body_path_length_m,
        },
        "estimator": {
            "nees_median": (
                weighted_median(nees_values, [1.0] * len(nees_values))
                if nees_values
                else None
            ),
            "nis_median": (
                weighted_median(nis_values, [1.0] * len(nis_values))
                if nis_values
                else None
            ),
            "fused_frame_count": len(nees_values),
            "sigma_px_frozen": sigma_px,
            "box_center_residual_rms_px": sigma_px_rms,
            "box_center_residual_ratio": (
                sigma_px_rms / sigma_px if sigma_px_rms is not None else None
            ),
        },
    }
    text = json.dumps(analysis, indent=2, sort_keys=True, allow_nan=False) + "\n"
    destination = run_directory / ANALYSIS_FILE_NAME
    if verify:
        if not destination.is_file():
            raise AnalysisError("verify_requires_existing_analysis")
        if destination.read_text() != text:
            raise AnalysisError("verify_rerun_not_byte_identical")
        return analysis
    if destination.exists():
        raise AnalysisError("analysis_already_exists_create_once")
    destination.write_text(text)
    return analysis


def frozen_run_id(arm: str, index: int) -> str:
    return RUN_ID_TEMPLATE.format(arm=arm, index=index)


def compare_arms(
    runtime: Path,
    arm_a_ids: Sequence[str],
    arm_b_ids: Sequence[str],
) -> dict[str, Any]:
    # Frozen identities and pairing order (round 13 §B.4, round 29 §C.2): the
    # exact ten acquisition IDs in trial order, with A1 acquired under its
    # attempt-4 ID. Duplicates, the consumed void ID, any other attempt
    # suffix, wrong arms and wrong order all fail here mechanically.
    expected_a = expected_acquisition_ids("a")
    expected_b = expected_acquisition_ids("b")
    if list(arm_a_ids) != expected_a:
        raise AnalysisError("arm_a_trial_ids_not_frozen_sequence")
    if list(arm_b_ids) != expected_b:
        raise AnalysisError("arm_b_trial_ids_not_frozen_sequence")
    # The canonical slots must still be the ten distinct frozen trials, so a
    # duplicated canonical slot cannot hide behind distinct acquisition IDs.
    canonical = [canonical_trial_id(run_id) for run_id in (*arm_a_ids, *arm_b_ids)]
    if len(set(canonical)) != 2 * TRIALS_PER_ARM:
        raise AnalysisError("duplicate_canonical_trial_slot")

    def _load(run_id: str) -> dict[str, Any]:
        path = runtime / "runs" / run_id / ANALYSIS_FILE_NAME
        if not path.is_file():
            raise AnalysisError(f"missing_trial_analysis:{run_id}")
        analysis = _load_json(path)
        if analysis.get("schema_version") != ANALYSIS_SCHEMA:
            raise AnalysisError(f"trial_analysis_schema_mismatch:{run_id}")
        # Content must belong to the frozen path's identity: copying one
        # trial's analysis into another trial's directory is a duplicate
        # trial, not a fifth run (round 14 §B.3).
        if analysis.get("receipt", {}).get("run_id") != run_id:
            raise AnalysisError(f"analysis_run_id_path_mismatch:{run_id}")
        return analysis

    arm_a = [_load(run_id) for run_id in arm_a_ids]
    arm_b = [_load(run_id) for run_id in arm_b_ids]
    analysis_hashes = {}
    for run_id in (*arm_a_ids, *arm_b_ids):
        analysis_hashes[run_id] = _sha256(
            runtime / "runs" / run_id / ANALYSIS_FILE_NAME
        )
    if len(set(analysis_hashes.values())) != 2 * TRIALS_PER_ARM:
        raise AnalysisError("duplicate_trial_analysis")

    # Cross-run identity (round 12 §B.5, round 13 §B.4): everything that
    # must be held constant across all ten trials, checked mechanically.
    identity_keys = (
        "scenario_sha256",
        "condition",
        "track_id",
        "ground_plane_y_m",
        "tracker",
        "tracker_pinned_version",
        "tracker_backend",
        "tracker_model_sha256",
        "reanchor_config_sha256",
        "tracker_model_spec_sha256",
        "init_box_norm",
        "init_frame_id",
        "body_config_sha256",
        # Round 17 §B.1 (Review F1): the measurement-window source must be
        # identical across all ten runs, not merely recorded per run.
        "margin_artifact_sha256",
        "visible_arc_sha256",
    )
    # Round 29 §C.2: the A1-only binding fields are verified on the A1
    # acquisition receipt alone. They are deliberately *not* in
    # ``identity_keys`` — requiring them across all ten runs would be wrong.
    a1_receipt = arm_a[0]["receipt"]
    for key, expected_value in (
        ("acquisition_run_id", A1_ACQUISITION_RUN_ID),
        ("canonical_trial_id", A1_CANONICAL_TRIAL_ID),
        ("attempt_number", A1_ATTEMPT_NUMBER),
        ("predecessor_void_manifest_sha256", A1_PREDECESSOR_VOID_MANIFEST_SHA256),
        ("predecessor_void_frames_sha256", A1_PREDECESSOR_VOID_FRAMES_SHA256),
    ):
        if a1_receipt.get(key) != expected_value:
            raise AnalysisError(f"a1_attempt_binding_mismatch:{key}")
    # Round 43 §C.1 (BC-BODY1-32): the same per-key check for the A2
    # acquisition receipt, including the third predecessor hash its ten-file
    # void hold carries. Symmetry with the A1 block above is the point - a gap
    # here would read as deliberately different treatment. These keys stay out
    # of ``identity_keys`` for the same reason A1's do: they are single-run
    # bindings, not a value the ten runs share.
    a2_receipt = arm_a[1]["receipt"]
    for key, expected_value in (
        ("acquisition_run_id", A2_ACQUISITION_RUN_ID),
        ("canonical_trial_id", A2_CANONICAL_TRIAL_ID),
        ("attempt_number", A2_ATTEMPT_NUMBER),
        ("predecessor_void_manifest_sha256", A2_PREDECESSOR_VOID_MANIFEST_SHA256),
        ("predecessor_void_frames_sha256", A2_PREDECESSOR_VOID_FRAMES_SHA256),
        ("predecessor_void_truth_sha256", A2_PREDECESSOR_VOID_TRUTH_SHA256),
    ):
        if a2_receipt.get(key) != expected_value:
            raise AnalysisError(f"a2_attempt_binding_mismatch:{key}")

    reference = arm_a[0]["receipt"]
    for analysis in arm_a + arm_b:
        receipt = analysis["receipt"]
        for key in identity_keys:
            if receipt.get(key) != reference.get(key):
                raise AnalysisError(
                    f"cross_run_identity_mismatch:{receipt.get('run_id')}:{key}"
                )
    for analysis in arm_a:
        receipt = analysis["receipt"]
        if receipt.get("body_policy") != ARM_A_POLICY:
            raise AnalysisError(
                f"arm_a_policy_mismatch:{receipt.get('run_id')}"
            )
        if receipt.get("body_planner_name") != POLICY_PLANNER[ARM_A_POLICY]:
            raise AnalysisError(
                f"arm_a_planner_mismatch:{receipt.get('run_id')}"
            )
    for analysis in arm_b:
        receipt = analysis["receipt"]
        if receipt.get("body_policy") != ARM_B_POLICY:
            raise AnalysisError(
                f"arm_b_policy_mismatch:{receipt.get('run_id')}"
            )
        if receipt.get("body_planner_name") != POLICY_PLANNER[ARM_B_POLICY]:
            raise AnalysisError(
                f"arm_b_planner_mismatch:{receipt.get('run_id')}"
            )

    h1_trials = [
        {
            "run_id": analysis["receipt"]["run_id"],
            "full_loop_c_geom": analysis["h1"]["full_loop_c_geom"],
            "disposition": analysis["h1"]["disposition"],
        }
        for analysis in arm_a
    ]

    # BC-BODY1-5/-14 true pairing (round 12 §B.4): per run pair, pair the
    # two per-position series at the same frozen route positions, take the
    # per-position improvement-signed differences, then the run pair's
    # mileage-grid median. Improvement-positive signs: area and the
    # min-side indicator share are larger-is-better (B - A); centre error
    # is smaller-is-better (A - B). "Median of B minus median of A" is not
    # this quantity. The second component is the frozen
    # 1[min_side >= 20 px] indicator share (round 13 §B.2).
    component_index = {
        "area_median_px": 0,
        "min_side_ge20_share": 1,
        "center_error_px": 2,
    }
    component_results = {}
    for name, index in component_index.items():
        sign = -1.0 if name == "center_error_px" else 1.0
        pair_medians = []
        for a_analysis, b_analysis in zip(arm_a, arm_b):
            a_series = a_analysis["c_quality_series"]
            b_series = b_analysis["c_quality_series"]
            common = sorted(set(a_series) & set(b_series))
            if not common:
                raise AnalysisError(
                    "paired_grid_empty:"
                    f"{a_analysis['receipt']['run_id']}x"
                    f"{b_analysis['receipt']['run_id']}"
                )
            diffs = [
                sign * (b_series[point][index] - a_series[point][index])
                for point in common
            ]
            pair_medians.append(
                weighted_median(diffs, [1.0] * len(diffs))
            )
        summary = weighted_median(pair_medians, [1.0] * len(pair_medians))
        component_results[name] = {
            "run_pair_medians": pair_medians,
            "summary_median_improvement": summary,
            "all_pairs_same_sign": all(median > 0.0 for median in pair_medians),
            "pass": summary > 0.0
            and all(median > 0.0 for median in pair_medians),
        }
    passed = [
        name for name, result in component_results.items() if result["pass"]
    ]
    if len(passed) == len(component_results):
        verdict = "H2_SUPPORTED"
    elif passed:
        verdict = "THRESHOLD_ALLOCATION_PARTIAL"
    else:
        verdict = "THRESHOLD_ALLOCATION_INEFFECTIVE"
    return {
        "schema_version": COMPARE_SCHEMA,
        "arm_a": list(arm_a_ids),
        "arm_b": list(arm_b_ids),
        "analysis_sha256": analysis_hashes,
        "h1_arm_a_trials": h1_trials,
        "h2": {
            "components": component_results,
            "passed_components": passed,
            "verdict": verdict,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, default=PROJECT_ROOT / "runtime")
    parser.add_argument(
        "--scenario",
        type=Path,
        default=PROJECT_ROOT / "config" / "scenario.default.json",
        help="first-analysis collect source; later reads are run-dir-only",
    )
    parser.add_argument(
        "--margin-artifact",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "evidence"
        / "P1-M3-BODY-001-scene-body-margin.json",
        help="first-analysis collect source; later reads are run-dir-only",
    )
    parser.add_argument(
        "--body-config",
        type=Path,
        default=PROJECT_ROOT / "config" / "p1-m3-body-001.json",
        help="first-analysis collect source; later reads are run-dir-only",
    )
    parser.add_argument("--run-id")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument(
        "--validate-completion",
        action="store_true",
        help="read-only completion handshake check (round 30 §C.4)",
    )
    parser.add_argument("--tracker-exit-code", type=int)
    parser.add_argument("--tracker-final-json")
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--arm-a")
    parser.add_argument("--arm-b")
    parser.add_argument(
        "--output",
        type=Path,
        help="required for --compare; must not exist (create-once)",
    )
    args = parser.parse_args(argv)
    try:
        if args.validate_completion:
            if not args.run_id:
                parser.error("--validate-completion requires --run-id")
            if args.tracker_exit_code is None:
                parser.error("--validate-completion requires --tracker-exit-code")
            if args.tracker_final_json is None:
                parser.error("--validate-completion requires --tracker-final-json")
            print(
                validate_completion(
                    args.runtime,
                    args.run_id,
                    args.tracker_exit_code,
                    args.tracker_final_json,
                )
            )
            return 0
        if args.compare:
            if not args.arm_a or not args.arm_b:
                parser.error("--compare requires --arm-a and --arm-b")
            if args.output is None:
                raise AnalysisError("compare_requires_create_once_output")
            if args.output.exists():
                raise AnalysisError("compare_output_create_once")
            result = compare_arms(
                args.runtime,
                args.arm_a.split(","),
                args.arm_b.split(","),
            )
            args.output.write_text(
                json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
                + "\n"
            )
            return 0
        if not args.run_id:
            parser.error("either --run-id or --compare is required")
        analysis = analyze_trial(
            args.runtime,
            args.run_id,
            args.scenario,
            args.margin_artifact,
            args.body_config,
            verify=args.verify,
        )
        print(
            json.dumps(
                {
                    "run_id": analysis["receipt"]["run_id"],
                    "verified": args.verify,
                    "full_loop_c_geom": analysis["h1"]["full_loop_c_geom"],
                    "disposition": analysis["h1"]["disposition"],
                    "window_c_track_given_geom": analysis["window"][
                        "c_track_given_geom"
                    ],
                },
                sort_keys=True,
            )
        )
        return 0
    except AnalysisError as exception:
        print(f"ANALYSIS_FAIL_CLOSED:{exception}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
