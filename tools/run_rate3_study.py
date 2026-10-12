"""P1-M2-RATE-003 batch 2 coordinator.

Implements the accepted batch-2 scope on top of the batch-1 shared-clock
protocol (`controller/rate3_protocol.py`):

* the frozen 20-slot execution order — scouting 1, six
  `rs3-d{1|2}-p{1|2|3}-calib` HOLD calibrations (BC-DRB-4), the D2 probe
  and the twelve formal runs in the §4 slot order — with anti-cherry-pick
  ordering enforced by the orchestrator, not by the operator;
* per-slot `max_attempts = 3` **totals** and the BC-R3-2 batch-wide
  `batch_invalid_attempt_count` pause at 4;
* the BC-DRB-4/5 pairing anchor: both rates of one (difficulty, phase)
  must initialise from the same SHA-256-bound frozen calibration product,
  refused at startup before any side effect and re-verified at decision
  time, where a mismatch makes **both** runs of the pair non-admissible;
* the §10 four-quantity completion gate at 150.0 s and S1'-S3;
* the §5 D2 probe with A0 admissibility evaluated **before** B1-B3, and
  BC-DRB-6 attribution reading `c_geom`, `c_track` and `C_track|geom`;
* the §11 report-only measured lap period on the released span;
* the immutable `p1-rate3-decision/v1` artifact, whose rules live in
  `controller/rate3_decision.py`.

Ground truth reaches this tool only through the evaluator-produced
`evaluation_truth.jsonl` sidecar (offline analysis chain); nothing here
feeds the tracker, the controller or outbound sensor metadata.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

from controller import rate3_decision, rate3_protocol
from controller.rate2_protocol import (
    Rate2ProtocolError,
    atomic_bytes,
    atomic_json,
    create_once_json,
    identity_hashes,
    latest_frame_id,
    read_json_bytes,
    sha256_file,
)
from controller.run_log import read_frame_records
from controller.trackers import (
    DEFAULT_NANOTRACK_V2_MODEL_DIR,
    DEFAULT_NANOTRACK_V2_SPEC,
)
from tools.run_rate2_study import SLOT_DIRECTORIES, SLOT_FILES
from tools.run_rate_study import _render_box_overlay, _validate_box
from tools.run_track_experiment import PROJECT_ROOT, tracker_command

RUNTIME_DEFAULT = PROJECT_ROOT / "runtime"
CONFIG_ROOT = PROJECT_ROOT / "config"
AUTHORIZATIONS_PATH = PROJECT_ROOT / "docs" / "authorizations.md"
DEFAULT_REANCHOR_CONFIG = CONFIG_ROOT / "detector-reanchor.models.json"

STUDY_ID = rate3_protocol.STUDY_ID
TRACKER_ID = rate3_protocol.TRACKER_ID
PLANNED_DURATION_S = rate3_protocol.PLANNED_DURATION_S

CAMPAIGN_SCHEMA = "p1-rate3-campaign/v1"
RUN_GATES_SCHEMA = "p1-rate3-run-gates/v1"
SCOUTING_REPORT_SCHEMA = "p1-rate3-scouting/v1"
SCOUTING_FREEZE_SCHEMA = "p1-rate3-scouting-freeze/v1"
CALIBRATION_PREVIEW_SCHEMA = "p1-rate3-calibration-preview/v1"
CALIBRATION_SCHEMA = "p1-rate3-calibration/v1"
ATTEMPT_STATUS_SCHEMA = "p1-rate3-attempt-status/v1"
FAILED_ATTEMPT_SCHEMA = "p1-rate3-failed-attempt/v1"
LAP_PERIOD_SCHEMA = "p1-rate3-lap-period/v1"
DISPLACEMENT_SCHEMA = "p1-rate3-displacement/v1"
PROBE_SCHEMA = "p1-rate3-probe/v1"
D2_SELECTION_SCHEMA = "p1-rate3-d2-selection/v1"
COORDINATOR_FAILURE_SCHEMA = "p1-rate3-coordinator-failure/v1"
EVALUATION_TRUTH_SCHEMA = "p1-rate3-evaluation-truth/v1"

SCOUTING_SLOT = "rs3-scouting"
CALIBRATION_SLOTS = rate3_protocol.B1_CALIBRATION_RUN_IDS
PROBE_SLOT = rate3_protocol.B1_PROBE_RUN_ID
# §4 frozen table: the slot number *is* the execution order. Same-phase
# rates are adjacent; phase 2 flips the within-phase rate order.
FORMAL_SLOT_ORDER = (
    "rs3-d1-p1-r20",
    "rs3-d1-p1-r5",
    "rs3-d1-p2-r5",
    "rs3-d1-p2-r20",
    "rs3-d1-p3-r20",
    "rs3-d1-p3-r5",
    "rs3-d2-p1-r20",
    "rs3-d2-p1-r5",
    "rs3-d2-p2-r5",
    "rs3-d2-p2-r20",
    "rs3-d2-p3-r20",
    "rs3-d2-p3-r5",
)
# B3.1: every operator-discretion input is frozen before any measurement.
SESSION_ORDER = (
    SCOUTING_SLOT,
    *CALIBRATION_SLOTS,
    PROBE_SLOT,
    *FORMAL_SLOT_ORDER,
)
RESEARCH_SLOTS = frozenset(SESSION_ORDER)

MAX_ATTEMPTS_PER_SLOT = 3
BATCH_INVALID_ATTEMPT_PAUSE = 4

# The 0c run gate (BC-DRB-7): without this ledger entry no research-data
# session may start. The marker is the ledger heading written by the
# acceptance role; this tool only reads the ledger.
AUTHORIZATION_0C_MARKER = "P1-M2-RATE-003 — 授权 0c"

# Difficulty x rate scenario configs. Within one difficulty the two files
# differ only in the rate-scaled fields the accepted RATE protocol allows
# (design §3.6: `capture_hz`, `retained_frame_count`,
# `maximum_pending_frame_count`); across difficulties they differ only in
# `scenario_id` and `target.speed_mps`. `check_scenario_configs` proves both.
SCENARIO_CONFIGS: dict[tuple[str, int], Path] = {
    ("D1", 20): CONFIG_ROOT / "scenario.p1-scene-004.json",
    ("D1", 5): CONFIG_ROOT / "scenario.p1-scene-004-r5.json",
    ("D2", 20): CONFIG_ROOT / "scenario.p1-scene-004-d2.json",
    ("D2", 5): CONFIG_ROOT / "scenario.p1-scene-004-d2-r5.json",
}
RATE_SCALED_KEYS = (
    "sensor.capture_hz",
    "sensor.retained_frame_count",
    "evaluation.maximum_pending_frame_count",
)
DIFFICULTY_KEYS = ("scenario_id", "target.speed_mps")
DIFFICULTY_SPEED_MPS = {"D1": 2.0, "D2": 8.0}
D2_DOWNSHIFT_SPEED_MPS = 6.0

INIT_WINDOW_S = (7.0, 8.0)

# §5 probe: predicted 5 Hz displacement at 8.0 m/s is 21.75-25.52 px with a
# +/-25% tolerance.
PROBE_DISPLACEMENT_RANGE_PX = (16.3, 31.9)
PROBE_FLOOR_C_TRACK_GIVEN_GEOM = 0.15

# §10 completion gate.
EVALUATOR_CUTOFF_TOLERANCE_S = 0.5
DURATION_EPSILON_S = 1e-6
S2_COMPUTE_LATENCY_LIMIT_MS = 50.0
S1_RATE_FRACTION = 0.95

# §11 lap period (report only).
LAP_LATERAL_TOLERANCE_M = 1.5
LAP_MINIMUM_CROSSINGS = 4
LAP_DROPPED_FRACTION_LIMIT = 0.20
NOMINAL_D1_LOOP_PERIOD_S = 31.071067811865476
LAP_PERIOD_DEVIATION_FRACTION = 0.05

RELEASE_POLL_INTERVAL_S = 0.005
SESSION_FILE = "rate_study_session.json"
SCOUTING_REPORT_FILE = "rate3_scouting_qualification.json"
EVALUATION_TRUTH_FILE = "evaluation_truth.jsonl"


class Rate3StudyError(ValueError):
    """Batch-2 orchestration refusal (always fail-closed)."""


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Rate3StudyError(f"{label} must be finite")
    result = float(value)
    if not math.isfinite(result):
        raise Rate3StudyError(f"{label} must be finite")
    return result


def _read_object(path: Path) -> dict[str, Any]:
    _, value = read_json_bytes(Path(path))
    return value


def _flatten(value: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, item in value.items():
        label = f"{prefix}{key}"
        if isinstance(item, Mapping):
            flat.update(_flatten(item, f"{label}."))
        else:
            flat[label] = item
    return flat


def campaign_directory(runtime: Path) -> Path:
    return Path(runtime) / "rate-study" / STUDY_ID


def campaign_manifest_path(runtime: Path) -> Path:
    return campaign_directory(runtime) / "campaign.json"


def run_gates_path(runtime: Path) -> Path:
    return campaign_directory(runtime) / "run_gates.json"


def scouting_directory(runtime: Path) -> Path:
    return campaign_directory(runtime) / "scouting"


def calibration_directory(runtime: Path, slot: str) -> Path:
    if slot not in CALIBRATION_SLOTS:
        raise Rate3StudyError(f"{slot!r} is not a calibration slot")
    return campaign_directory(runtime) / "calibrations" / slot


def calibration_preview_path(runtime: Path, slot: str) -> Path:
    return campaign_directory(runtime) / "previews" / f"{slot}.json"


def failed_attempts_directory(runtime: Path, slot: str) -> Path:
    return campaign_directory(runtime) / "failed-attempts" / slot


def probe_path(runtime: Path) -> Path:
    """The **terminal** probe adjudication (B1/B2/B3 or `BLOCKED_PROBE`)."""

    return campaign_directory(runtime) / "probe.json"


def probe_attempt_path(runtime: Path, attempt_number: int) -> Path:
    """One A0 adjudication. §5 allows the slot to be rerun in place, so an
    `PROBE_ATTEMPT_INVALID` verdict belongs to its attempt, not to the
    campaign; only a terminal disposition freezes `probe.json`.
    """

    if attempt_number < 1:
        raise Rate3StudyError("attempt numbers start at 1")
    return (
        campaign_directory(runtime)
        / "probe-attempts"
        / f"attempt-{attempt_number}.json"
    )


def d2_selection_path(runtime: Path) -> Path:
    return campaign_directory(runtime) / "d2_selection.json"


def decision_path(runtime: Path) -> Path:
    return campaign_directory(runtime) / "decision.json"


# --------------------------------------------------------------------------
# slot identity
# --------------------------------------------------------------------------


def slot_identity(slot: str) -> dict[str, Any]:
    """Decode one frozen slot ID into its design coordinates."""

    if slot not in RESEARCH_SLOTS:
        raise Rate3StudyError(
            f"slot is not part of the frozen RATE-003 schedule: {slot!r}"
        )
    identity: dict[str, Any] = {
        "run_id": slot,
        "kind": None,
        "difficulty": None,
        "phase": None,
        "rate_hz": None,
        "session_order_index": SESSION_ORDER.index(slot),
        "formal_slot_number": None,
    }
    if slot == SCOUTING_SLOT:
        identity["kind"] = "scouting"
        return identity
    if slot == PROBE_SLOT:
        # §5: 5 Hz / D2 candidate / s*_1.
        identity.update(
            {"kind": "probe", "difficulty": "D2", "phase": 1, "rate_hz": 5}
        )
        return identity
    pieces = slot.split("-")
    difficulty = pieces[1].upper()
    phase = int(pieces[2][1:])
    if pieces[3] == "calib":
        identity.update(
            {"kind": "calibration", "difficulty": difficulty, "phase": phase}
        )
        return identity
    identity.update(
        {
            "kind": "formal",
            "difficulty": difficulty,
            "phase": phase,
            "rate_hz": int(pieces[3][1:]),
            "formal_slot_number": FORMAL_SLOT_ORDER.index(slot) + 1,
        }
    )
    return identity


def calibration_slot_for(difficulty: str, phase: int) -> str:
    return f"rs3-{difficulty.lower()}-p{phase}-calib"


# --------------------------------------------------------------------------
# scenario configs
# --------------------------------------------------------------------------


def check_scenario_configs() -> dict[str, Any]:
    """Prove the four frozen configs differ only where they are allowed to."""

    loaded = {
        key: json.loads(path.read_text(encoding="utf-8"))
        for key, path in SCENARIO_CONFIGS.items()
    }
    for (difficulty, rate), scenario in loaded.items():
        expected_id = "p1-scene-004" if difficulty == "D1" else "p1-scene-004-d2"
        if scenario.get("scenario_id") != expected_id:
            raise Rate3StudyError(
                f"{difficulty}/{rate} Hz config has scenario_id "
                f"{scenario.get('scenario_id')!r}, expected {expected_id!r}"
            )
        if float(scenario["sensor"]["capture_hz"]) != float(rate):
            raise Rate3StudyError(
                f"{difficulty}/{rate} Hz config has capture_hz "
                f"{scenario['sensor']['capture_hz']!r}"
            )
    for difficulty in ("D1", "D2"):
        fast = _flatten(loaded[(difficulty, 20)])
        slow = _flatten(loaded[(difficulty, 5)])
        differing = sorted(
            key
            for key in set(fast) | set(slow)
            if fast.get(key) != slow.get(key)
        )
        if differing != sorted(RATE_SCALED_KEYS):
            raise Rate3StudyError(
                f"{difficulty} rate variants differ in {differing}; only "
                f"{sorted(RATE_SCALED_KEYS)} may differ"
            )
    for rate in (20, 5):
        d1 = _flatten(loaded[("D1", rate)])
        d2 = _flatten(loaded[("D2", rate)])
        differing = sorted(
            key for key in set(d1) | set(d2) if d1.get(key) != d2.get(key)
        )
        if differing != sorted(DIFFICULTY_KEYS):
            raise Rate3StudyError(
                f"{rate} Hz difficulty variants differ in {differing}; only "
                f"{sorted(DIFFICULTY_KEYS)} may differ"
            )
    return {
        f"{difficulty}-r{rate}": {
            "path": str(path.relative_to(PROJECT_ROOT)),
            "sha256": sha256_file(path),
            "scenario_id": loaded[(difficulty, rate)]["scenario_id"],
            "capture_hz": loaded[(difficulty, rate)]["sensor"]["capture_hz"],
            "target_speed_mps": loaded[(difficulty, rate)]["target"]["speed_mps"],
        }
        for (difficulty, rate), path in SCENARIO_CONFIGS.items()
    }


def scenario_config_for(
    runtime: Path,
    difficulty: str,
    rate_hz: int,
) -> tuple[Path, dict[str, Any]]:
    """Resolve the frozen config, honouring an accepted 8 -> 6 m/s downshift."""

    if difficulty == "D2" and d2_selection_path(runtime).is_file():
        selection = load_d2_selection(runtime)
        path = Path(selection["configs"][f"r{rate_hz}"]["path"])
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if sha256_file(path) != selection["configs"][f"r{rate_hz}"]["sha256"]:
            raise Rate3StudyError(
                "frozen D2 config bytes changed after the 0b selection"
            )
        return path, json.loads(path.read_text(encoding="utf-8"))
    path = SCENARIO_CONFIGS[(difficulty, rate_hz)]
    return path, json.loads(path.read_text(encoding="utf-8"))


def install_config(runtime: Path, slot: str) -> dict[str, Any]:
    """Install the slot's frozen scenario config into the runtime bridge.

    Calibration is HOLD-only and its frozen product must be shared by both
    rates of the pair (BC-DRB-4/5), so calibration slots install the
    difficulty's 20 Hz config; the frozen reference frame content is
    rate-independent because the target does not move in HOLD.
    """

    identity = slot_identity(slot)
    if identity["kind"] == "scouting":
        difficulty, rate_hz = "D1", 20
    else:
        difficulty = str(identity["difficulty"])
        rate_hz = int(identity["rate_hz"] or 20)
    source, scenario = scenario_config_for(runtime, difficulty, rate_hz)
    destination = Path(runtime) / "scenario_config.json"
    atomic_bytes(destination, source.read_bytes())
    installed = sha256_file(destination)
    if installed != sha256_file(source):
        raise Rate3StudyError("installed scenario config hash mismatch")
    return {
        "run_id": slot,
        "difficulty": difficulty,
        "rate_hz": rate_hz,
        "scenario_id": scenario["scenario_id"],
        "config_path": str(destination),
        "config_sha256": installed,
    }


# --------------------------------------------------------------------------
# campaign and run gates
# --------------------------------------------------------------------------


def prepare_campaign(runtime: Path) -> dict[str, Any]:
    if campaign_manifest_path(runtime).is_file():
        return load_campaign(runtime)
    existing = sorted(
        path.name
        for path in (Path(runtime) / "runs").glob("rs3-*")
        if path.name != rate3_protocol.CLOCK_SMOKE_RUN_ID
    )
    if existing:
        raise FileExistsError(
            "campaign manifest must be frozen before any RATE-003 research "
            "run directory exists: " + ", ".join(existing)
        )
    manifest = {
        "schema_version": CAMPAIGN_SCHEMA,
        "study_id": STUDY_ID,
        "tracker_id": TRACKER_ID,
        "session_order": list(SESSION_ORDER),
        "formal_slot_order": list(FORMAL_SLOT_ORDER),
        "calibration_slots": list(CALIBRATION_SLOTS),
        "scouting_slot": SCOUTING_SLOT,
        "probe_slot": PROBE_SLOT,
        "planned_duration_s": PLANNED_DURATION_S,
        "evaluator_cutoff_tolerance_s": EVALUATOR_CUTOFF_TOLERANCE_S,
        "max_attempts_per_slot": MAX_ATTEMPTS_PER_SLOT,
        "batch_invalid_attempt_pause": BATCH_INVALID_ATTEMPT_PAUSE,
        "theta": rate3_decision.THETA,
        "theta_geom": rate3_decision.THETA_GEOM,
        "decision_rule_version": rate3_decision.RULE_VERSION,
        "difficulty_speed_mps": dict(DIFFICULTY_SPEED_MPS),
        "d2_downshift_speed_mps": D2_DOWNSHIFT_SPEED_MPS,
        "probe_displacement_range_px": list(PROBE_DISPLACEMENT_RANGE_PX),
        "probe_floor_c_track_given_geom": PROBE_FLOOR_C_TRACK_GIVEN_GEOM,
        "scenario_configs": check_scenario_configs(),
        "fixed_order_time_confound": (
            "D1 is measured before D2 and the slot order is frozen; the "
            "resulting time confound is disclosed per run and must not be "
            "attributed to frame rate"
        ),
        "created_unix_s": time.time(),
    }
    create_once_json(campaign_manifest_path(runtime), manifest)
    return _read_object(campaign_manifest_path(runtime))


def load_campaign(runtime: Path) -> dict[str, Any]:
    campaign = _read_object(campaign_manifest_path(runtime))
    expected = {
        "schema_version": CAMPAIGN_SCHEMA,
        "study_id": STUDY_ID,
        "tracker_id": TRACKER_ID,
        "session_order": list(SESSION_ORDER),
        "formal_slot_order": list(FORMAL_SLOT_ORDER),
        "planned_duration_s": PLANNED_DURATION_S,
        "max_attempts_per_slot": MAX_ATTEMPTS_PER_SLOT,
        "batch_invalid_attempt_pause": BATCH_INVALID_ATTEMPT_PAUSE,
        "theta": rate3_decision.THETA,
        "theta_geom": rate3_decision.THETA_GEOM,
    }
    for key, value in expected.items():
        if campaign.get(key) != value:
            raise Rate3StudyError(f"RATE-003 campaign {key} changed")
    # BC-B2-CQ1: the four frozen configs are bound into the campaign
    # provenance, and `check_scenario_configs()` re-proves the allowed
    # difference set on every startup, so post-freeze drift in any of the
    # four files fails closed here rather than at measurement time.
    if campaign.get("scenario_configs") != check_scenario_configs():
        raise Rate3StudyError(
            "frozen RATE-003 scenario configs no longer match the campaign "
            "manifest (BC-B2-CQ1)"
        )
    return campaign


def authorization_0c_recorded(
    ledger_path: Path = AUTHORIZATIONS_PATH,
) -> bool:
    """BC-DRB-7: no 0c ledger entry, no research-data session."""

    ledger_path = Path(ledger_path)
    if not ledger_path.is_file():
        return False
    return AUTHORIZATION_0C_MARKER in ledger_path.read_text(encoding="utf-8")


def record_run_gates(
    runtime: Path,
    *,
    qual3_pass_attributed: bool,
    dr_round3_passed: bool,
    clock_smoke_passed: bool,
    attribution: str,
    ledger_path: Path = AUTHORIZATIONS_PATH,
) -> dict[str, Any]:
    """Freeze the non-protocol run gates that precede every research session."""

    load_campaign(runtime)
    if run_gates_path(runtime).is_file():
        return load_run_gates(runtime, ledger_path=ledger_path)
    if not attribution.strip():
        raise Rate3StudyError("run-gate attribution text must not be empty")
    missing = [
        name
        for name, value in (
            ("qual3_pass_attributed", qual3_pass_attributed),
            ("dr_round3_passed", dr_round3_passed),
            ("clock_smoke_passed", clock_smoke_passed),
        )
        if not value
    ]
    if missing:
        raise Rate3StudyError(
            "every RATE-003 run gate must be satisfied before research "
            "sessions may start; missing: " + ", ".join(missing)
        )
    if not authorization_0c_recorded(ledger_path):
        raise Rate3StudyError(
            "acceptance criterion 0c is not in docs/authorizations.md; no "
            "scouting/calibration/probe/formal session may start (BC-DRB-7)"
        )
    gates = {
        "schema_version": RUN_GATES_SCHEMA,
        "study_id": STUDY_ID,
        "authorization_0c_recorded": True,
        "authorization_0c_marker": AUTHORIZATION_0C_MARKER,
        "authorization_ledger_path": str(Path(ledger_path)),
        "authorization_ledger_sha256": sha256_file(Path(ledger_path)),
        "qual3_pass_attributed": True,
        "dr_round3_passed": True,
        "clock_smoke_passed": True,
        "attribution": attribution.strip(),
        "recorded_unix_s": time.time(),
    }
    create_once_json(run_gates_path(runtime), gates)
    return load_run_gates(runtime, ledger_path=ledger_path)


def load_run_gates(
    runtime: Path,
    *,
    ledger_path: Path = AUTHORIZATIONS_PATH,
) -> dict[str, Any]:
    gates = _read_object(run_gates_path(runtime))
    if gates.get("schema_version") != RUN_GATES_SCHEMA:
        raise Rate3StudyError("invalid RATE-003 run-gate schema")
    if gates.get("study_id") != STUDY_ID:
        raise Rate3StudyError("run-gate study_id mismatch")
    for key in (
        "authorization_0c_recorded",
        "qual3_pass_attributed",
        "dr_round3_passed",
        "clock_smoke_passed",
    ):
        if gates.get(key) is not True:
            raise Rate3StudyError(f"run gate {key} is not satisfied")
    if not authorization_0c_recorded(ledger_path):
        raise Rate3StudyError(
            "acceptance criterion 0c is no longer present in the ledger"
        )
    return gates


# --------------------------------------------------------------------------
# attempts (per slot cap 3, BC-R3-2 batch counter)
# --------------------------------------------------------------------------


def _directory_hashes(directory: Path) -> dict[str, str]:
    return {
        str(path.relative_to(directory)): sha256_file(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def failed_attempt_count(runtime: Path, slot: str) -> int:
    directory = failed_attempts_directory(runtime, slot)
    receipts = sorted(directory.glob("attempt-*.json"))
    for expected_number, receipt_path in enumerate(receipts, start=1):
        receipt = _read_object(receipt_path)
        archive = directory / f"attempt-{expected_number}-run"
        if (
            receipt.get("schema_version") != FAILED_ATTEMPT_SCHEMA
            or receipt.get("study_id") != STUDY_ID
            or receipt.get("run_id") != slot
            or receipt.get("attempt_number") != expected_number
            or receipt.get("archived_directory") != str(archive)
            or receipt.get("file_sha256") != _directory_hashes(archive)
        ):
            raise Rate3StudyError(
                f"invalid failed-attempt receipt for {slot} attempt "
                f"{expected_number}"
            )
    return len(receipts)


def batch_invalid_attempt_count(runtime: Path) -> int:
    """BC-R3-2: monotone, never reset, across every research identity."""

    return sum(failed_attempt_count(runtime, slot) for slot in SESSION_ORDER)


def _archive_scouting_attempt(runtime: Path, archive: Path) -> list[str]:
    report = runtime / SCOUTING_REPORT_FILE
    if not report.is_file():
        raise FileNotFoundError(f"no scouting report to archive: {report}")
    shutil.move(str(report), str(archive / SCOUTING_REPORT_FILE))
    return [SCOUTING_REPORT_FILE]


def _archive_session_attempt(
    runtime: Path,
    slot: str,
    archive: Path,
) -> list[str]:
    """Receipt payload for an attempt that never produced a run directory.

    Calibration is HOLD-only and never launches the tracker; a formal or
    probe attempt can also fail in the §1.1(a) startup checks, which are
    deliberately ordered before the run directory exists. In both cases
    the attempt identity is the installed session file — written by
    `prepare_session` only after `authorize_session` passed — so its
    presence is exactly BC-R3-2's dividing line: a refusal before the
    session existed is not a counted attempt, and anything past that
    point is.
    """

    session_path = runtime / SESSION_FILE
    if not session_path.is_file():
        raise FileNotFoundError(
            f"no installed {slot} session to archive; a refusal before the "
            "attempt identity existed is not a counted attempt (BC-R3-2)"
        )
    installed = _read_object(session_path)
    if installed.get("run_id") != slot:
        raise Rate3StudyError(
            f"the installed session belongs to {installed.get('run_id')!r}, "
            f"not {slot!r}"
        )
    moved = [SESSION_FILE]
    shutil.move(str(session_path), str(archive / SESSION_FILE))
    preview_path = calibration_preview_path(runtime, slot)
    preview = _read_object(preview_path) if preview_path.is_file() else None
    for path in (preview_path, preview_path.with_suffix(".jpg")):
        if path.is_file():
            shutil.move(str(path), str(archive / path.name))
            moved.append(f"previews/{path.name}")
    reference_frame_id = (preview or {}).get("reference_frame_id")
    if isinstance(reference_frame_id, int) and not isinstance(
        reference_frame_id, bool
    ):
        stem = f"frame_{reference_frame_id:010d}"
        for suffix in (".jpg", ".json"):
            # Copied, not moved: `runtime/frames/` is Unity's live retained
            # buffer and this attempt is being abandoned, not replayed.
            source = runtime / "frames" / f"{stem}{suffix}"
            if source.is_file():
                shutil.copy2(source, archive / f"{stem}{suffix}")
                moved.append(f"frames/{stem}{suffix}")
    return moved


def _archive_run_attempt(
    runtime: Path,
    slot: str,
    archive: Path,
) -> list[str]:
    source = runtime / "runs" / slot
    if not source.is_dir():
        # The startup checks refuse before the run directory is created, so
        # a launched-but-refused attempt still owns a session identity.
        return _archive_session_attempt(runtime, slot, archive)
    status_path = source / "rate3-status.json"
    if status_path.is_file() and _read_object(status_path).get("admissible"):
        raise Rate3StudyError(
            f"{slot} finalized as admissible; an admissible run may not be "
            "archived as a failed attempt"
        )
    shutil.rmtree(archive)
    shutil.move(str(source), str(archive))
    moved = [f"runs/{slot}"]
    truth = runtime / EVALUATION_TRUTH_FILE
    if truth.is_file():
        shutil.move(str(truth), str(archive / EVALUATION_TRUTH_FILE))
        moved.append(EVALUATION_TRUTH_FILE)
    return moved


def archive_failed_attempt(
    runtime: Path,
    slot: str,
    reason: str,
) -> dict[str, Any]:
    """Archive one invalid attempt and increment the batch counter first.

    Every research identity has a real archivable payload: the scouting
    report, the calibration session/preview/reference frame, or the run
    directory. BC-DRB-4's per-slot cap and BC-R3-2's batch counter both
    read the resulting immutable receipts, so no slot may fail silently.
    """

    if not reason.strip():
        raise Rate3StudyError("failed attempt reason must not be empty")
    load_campaign(runtime)
    identity = slot_identity(slot)
    runtime = Path(runtime)
    # A slot that already produced its terminal artifact is complete; minting
    # a failure receipt for it would inflate the BC-R3-2 counter and orphan
    # the hashes the terminal artifact binds.
    terminal = {
        "scouting": scouting_directory(runtime) / "manifest.json",
        "calibration": (
            calibration_directory(runtime, slot) / "manifest.json"
            if identity["kind"] == "calibration"
            else None
        ),
        "probe": probe_path(runtime),
    }.get(str(identity["kind"]))
    if terminal is not None and terminal.is_file():
        raise Rate3StudyError(
            f"{slot} already has a terminal artifact ({terminal.name}); it "
            "cannot be archived as a failed attempt"
        )
    count = failed_attempt_count(runtime, slot)
    if count >= MAX_ATTEMPTS_PER_SLOT:
        raise Rate3StudyError(
            f"per-slot attempt limit is already exhausted for {slot}"
        )
    number = count + 1
    directory = failed_attempts_directory(runtime, slot)
    archive = directory / f"attempt-{number}-run"
    if archive.exists():
        raise FileExistsError(archive)
    directory.mkdir(parents=True, exist_ok=True)
    archive.mkdir(parents=True, exist_ok=False)
    kind = str(slot_identity(slot)["kind"])
    try:
        if kind == "scouting":
            moved = _archive_scouting_attempt(runtime, archive)
        elif kind == "calibration":
            moved = _archive_session_attempt(runtime, slot, archive)
        else:
            moved = _archive_run_attempt(runtime, slot, archive)
    except Exception:
        shutil.rmtree(archive, ignore_errors=True)
        raise
    receipt = {
        "schema_version": FAILED_ATTEMPT_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": slot,
        "attempt_number": number,
        "reason": reason.strip(),
        "archived_directory": str(archive),
        "archived_sources": moved,
        "file_sha256": _directory_hashes(archive),
        "archived_unix_s": time.time(),
    }
    create_once_json(directory / f"attempt-{number}.json", receipt)
    result = _read_object(directory / f"attempt-{number}.json")
    result["batch_invalid_attempt_count"] = batch_invalid_attempt_count(runtime)
    result["batch_paused"] = (
        result["batch_invalid_attempt_count"] >= BATCH_INVALID_ATTEMPT_PAUSE
    )
    for name in SLOT_FILES + (SESSION_FILE,):
        (runtime / name).unlink(missing_ok=True)
    for name in SLOT_DIRECTORIES:
        shutil.rmtree(runtime / name, ignore_errors=True)
    return result


# --------------------------------------------------------------------------
# scouting freeze (§4)
# --------------------------------------------------------------------------


def freeze_scouting(runtime: Path, *, confirmed: bool = True) -> dict[str, Any]:
    """Freeze the three deterministic phases from the Unity scouting table."""

    runtime = Path(runtime)
    load_campaign(runtime)
    load_run_gates(runtime)
    manifest_path = scouting_directory(runtime) / "manifest.json"
    if manifest_path.is_file():
        return load_scouting(runtime)
    if not confirmed:
        raise Rate3StudyError("scouting freeze requires an explicit confirmation")
    report_path = runtime / SCOUTING_REPORT_FILE
    report = _read_object(report_path)
    if report.get("schema_version") != SCOUTING_REPORT_SCHEMA:
        raise Rate3StudyError("invalid RATE-003 scouting report schema")
    if report.get("study_id") != STUDY_ID or report.get("run_id") != SCOUTING_SLOT:
        raise Rate3StudyError("scouting report identity mismatch")
    if report.get("status") != "QUALIFIED":
        raise Rate3StudyError(
            "INVALID_SCOUTING: "
            f"{report.get('validation_error') or report.get('status')}"
        )
    selected = report.get("selected_route_s_m")
    indices = report.get("selected_candidate_index")
    if (
        not isinstance(selected, list)
        or len(selected) != 3
        or not isinstance(indices, list)
        or len(indices) != 3
    ):
        raise Rate3StudyError("scouting report must select exactly three phases")
    phases = [_finite(value, "selected_route_s_m") for value in selected]
    if len(set(phases)) != 3:
        raise Rate3StudyError("the three scouting phases must be distinct")
    candidates = report.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise Rate3StudyError("scouting report must publish the candidate table")
    for position, index in enumerate(indices):
        candidate = candidates[int(index)]
        if not candidate.get("qualified"):
            raise Rate3StudyError(
                f"selected phase {position + 1} is not a qualified candidate"
            )
        if _finite(candidate.get("route_s_m"), "route_s_m") != phases[position]:
            raise Rate3StudyError(
                f"selected phase {position + 1} does not match its candidate"
            )
    directory = scouting_directory(runtime)
    directory.mkdir(parents=True, exist_ok=True)
    shutil.copy2(report_path, directory / SCOUTING_REPORT_FILE)
    manifest = {
        "schema_version": SCOUTING_FREEZE_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": SCOUTING_SLOT,
        "scenario_id": report.get("scenario_id"),
        "route_perimeter_m": report.get("route_perimeter_m"),
        "ideal_phase_s_m": report.get("ideal_phase_s_m"),
        "phase_route_s_m": phases,
        "phase_candidate_index": [int(value) for value in indices],
        "candidate_count": len(candidates),
        "qualified_candidate_count": sum(
            1 for candidate in candidates if candidate.get("qualified")
        ),
        "report_sha256": sha256_file(directory / SCOUTING_REPORT_FILE),
        "frozen_unix_s": time.time(),
    }
    create_once_json(manifest_path, manifest)
    return load_scouting(runtime)


def load_scouting(runtime: Path) -> dict[str, Any]:
    directory = scouting_directory(runtime)
    manifest = _read_object(directory / "manifest.json")
    if manifest.get("schema_version") != SCOUTING_FREEZE_SCHEMA:
        raise Rate3StudyError("invalid RATE-003 scouting freeze schema")
    if manifest.get("study_id") != STUDY_ID:
        raise Rate3StudyError("scouting freeze study_id mismatch")
    if manifest.get("report_sha256") != sha256_file(
        directory / SCOUTING_REPORT_FILE
    ):
        raise Rate3StudyError("frozen scouting report bytes changed")
    phases = manifest.get("phase_route_s_m")
    if not isinstance(phases, list) or len(phases) != 3:
        raise Rate3StudyError("scouting freeze must bind three phases")
    return manifest


def phase_route_s_m(runtime: Path, phase: int) -> float:
    if phase not in (1, 2, 3):
        raise Rate3StudyError(f"unknown phase {phase!r}")
    return float(load_scouting(runtime)["phase_route_s_m"][phase - 1])


# --------------------------------------------------------------------------
# sessions, calibration and the pairing anchor
# --------------------------------------------------------------------------


def nanotrack_identity(
    *,
    tracker_model_spec: Path = DEFAULT_NANOTRACK_V2_SPEC,
    tracker_model_dir: Path = DEFAULT_NANOTRACK_V2_MODEL_DIR,
) -> dict[str, Any]:
    from controller.trackers import create_tracker

    tracker = create_tracker(
        TRACKER_ID,
        nanotrack_spec_path=tracker_model_spec,
        nanotrack_model_dir=tracker_model_dir,
    )
    return dict(tracker.manifest_identity())


def build_session(
    *,
    run_id: str,
    init_frame_id: int,
    init_image_sha256: str,
    hold_route_s_m: float,
    tracker_identity: Mapping[str, Any],
) -> dict[str, Any]:
    tracker_hash, model_hash = identity_hashes(tracker_identity)
    session = {
        "schema_version": rate3_protocol.SESSION_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": run_id,
        "scenario_id": rate3_protocol.expected_scenario(run_id, STUDY_ID),
        "tracker_id": TRACKER_ID,
        "tracker_identity_sha256": tracker_hash,
        "model_identity_sha256": model_hash,
        "init_frame_id": int(init_frame_id),
        "init_image_sha256": init_image_sha256,
        "hold_route_s_m": _finite(hold_route_s_m, "hold_route_s_m"),
        "minimum_ready_seq": 20,
        "minimum_processed_frames": 20,
        "planned_duration_s": PLANNED_DURATION_S,
        "sensor_frame_schema": rate3_protocol.SENSOR_SCHEMA,
        "capture_monotonic_clock_id": rate3_protocol.CLOCK_ID,
    }
    return rate3_protocol.validate_session(session)


def calibration_preflight(
    runtime: Path,
    session: Mapping[str, Any],
) -> dict[str, Any] | None:
    """BC-DRB-4/5 startup preflight: refuse a mismatched frozen product.

    Runs before the session file is written, i.e. before the model is
    constructed, before the run directory exists and before any ready or
    release side effect.
    """

    identity = slot_identity(str(session["run_id"]))
    if identity["kind"] in {"scouting", "calibration"}:
        return None
    slot = calibration_slot_for(
        str(identity["difficulty"]), int(identity["phase"])
    )
    calibration = load_calibration(runtime, slot)
    if session["init_frame_id"] != calibration["reference_frame_id"]:
        raise Rate3StudyError(
            f"{session['run_id']} init frame does not match the frozen "
            f"{slot} calibration"
        )
    if session["init_image_sha256"] != calibration["reference_image_sha256"]:
        raise Rate3StudyError(
            f"{session['run_id']} init image does not match the frozen "
            f"{slot} calibration"
        )
    if calibration["scenario_id"] != session["scenario_id"]:
        raise Rate3StudyError(
            "calibration identity may not be reused across scenario_id "
            "(BC-DRB-4)"
        )
    return calibration


def prepare_session(
    runtime: Path,
    session: Mapping[str, Any],
) -> dict[str, Any]:
    runtime = Path(runtime)
    load_campaign(runtime)
    validated = rate3_protocol.validate_session(session)
    run_id = str(validated["run_id"])
    authorize_session(runtime, run_id)
    identity = slot_identity(run_id)
    if identity["kind"] != "scouting":
        expected_hold = phase_route_s_m(runtime, int(identity["phase"]))
        if abs(float(validated["hold_route_s_m"]) - expected_hold) > 1e-9:
            raise Rate3StudyError(
                f"{run_id} hold_route_s_m must equal the frozen phase "
                f"position {expected_hold}"
            )
    calibration_preflight(runtime, validated)
    stale = [name for name in SLOT_FILES if (runtime / name).exists()]
    stale.extend(
        f"{name}/" for name in SLOT_DIRECTORIES if (runtime / name).exists()
    )
    if (runtime / EVALUATION_TRUTH_FILE).exists():
        stale.append(EVALUATION_TRUTH_FILE)
    if stale:
        raise FileExistsError(
            "stale RATE-003 runtime slots must be archived before prepare: "
            + ", ".join(stale)
        )
    session_path = runtime / SESSION_FILE
    create_once_json(session_path, validated)
    return _read_object(session_path)


def _rate3_frame_candidates(
    runtime: Path,
    scenario_id: str,
    *,
    start_s: float = INIT_WINDOW_S[0],
    end_s: float = INIT_WINDOW_S[1],
) -> list[dict[str, Any]]:
    frames = Path(runtime) / "frames"
    candidates: list[dict[str, Any]] = []
    for metadata_path in frames.glob("frame_*.json"):
        metadata = _read_object(metadata_path)
        if metadata.get("scenario_id") != scenario_id:
            continue
        if metadata.get("schema_version") != rate3_protocol.SENSOR_SCHEMA:
            raise Rate3StudyError(
                f"{metadata_path.name} has sensor schema "
                f"{metadata.get('schema_version')!r}; RATE-003 requires "
                f"{rate3_protocol.SENSOR_SCHEMA!r}"
            )
        if metadata.get("capture_monotonic_clock_id") != rate3_protocol.CLOCK_ID:
            raise Rate3StudyError(
                f"INVALID_CLOCK_IDENTITY: {metadata_path.name} declares "
                f"{metadata.get('capture_monotonic_clock_id')!r}"
            )
        _finite(metadata.get("capture_monotonic_s"), "capture_monotonic_s")
        simulation_time_s = _finite(
            metadata.get("simulation_time_s"), "simulation_time_s"
        )
        if not start_s <= simulation_time_s < end_s:
            continue
        frame_id = int(metadata.get("frame_id", -1))
        image_path = frames / f"frame_{frame_id:010d}.jpg"
        if frame_id < 0 or not image_path.is_file():
            continue
        candidates.append(
            {
                "frame_id": frame_id,
                "simulation_time_s": simulation_time_s,
                "metadata_path": metadata_path,
                "image_path": image_path,
                "image_sha256": sha256_file(image_path),
                "metadata_sha256": sha256_file(metadata_path),
            }
        )
    candidates.sort(key=lambda item: (item["simulation_time_s"], item["frame_id"]))
    return candidates


def select_init_frame(runtime: Path, slot: str) -> dict[str, Any]:
    """Deterministic first complete frame in the frozen [7, 8) s window."""

    scenario_id = rate3_protocol.expected_scenario(slot, STUDY_ID)
    candidates = _rate3_frame_candidates(runtime, scenario_id)
    if not candidates:
        raise FileNotFoundError(
            "no complete v3 HOLD frame exists in simulation_time_s "
            f"[{INIT_WINDOW_S[0]}, {INIT_WINDOW_S[1]})"
        )
    return candidates[0]


def preview_calibration(
    runtime: Path,
    slot: str,
    box_norm: Sequence[float],
) -> dict[str, Any]:
    runtime = Path(runtime)
    if slot not in CALIBRATION_SLOTS:
        raise Rate3StudyError(f"{slot!r} is not a calibration slot")
    box = _validate_box(box_norm)
    _, installed = rate3_protocol.load_session(runtime)
    if installed["run_id"] != slot:
        raise Rate3StudyError(f"installed session must be {slot} for calibration")
    frame = select_init_frame(runtime, slot)
    preview_path = calibration_preview_path(runtime, slot)
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_path = preview_path.with_suffix(".jpg")
    pixel_box = _render_box_overlay(
        frame["image_path"],
        overlay_path,
        box,
        f"RATE-003 {slot} target",
    )
    identity = slot_identity(slot)
    preview = {
        "schema_version": CALIBRATION_PREVIEW_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": slot,
        "difficulty": identity["difficulty"],
        "phase": identity["phase"],
        "scenario_id": installed["scenario_id"],
        "hold_route_s_m": installed["hold_route_s_m"],
        "reference_frame_id": frame["frame_id"],
        "reference_simulation_time_s": frame["simulation_time_s"],
        "reference_image_sha256": frame["image_sha256"],
        "reference_metadata_sha256": frame["metadata_sha256"],
        "reference_box_xywh_norm": list(box),
        "reference_box_xywh_px": pixel_box,
        "overlay_path": str(overlay_path),
        "overlay_sha256": sha256_file(overlay_path),
    }
    atomic_json(preview_path, preview)
    return preview


def freeze_calibration(
    runtime: Path,
    slot: str,
    *,
    confirmed: bool,
) -> dict[str, Any]:
    if not confirmed:
        raise Rate3StudyError(
            "calibration freeze requires visual overlay confirmation"
        )
    runtime = Path(runtime)
    destination = calibration_directory(runtime, slot)
    if destination.exists():
        return load_calibration(runtime, slot)
    preview_path = calibration_preview_path(runtime, slot)
    preview = _read_object(preview_path)
    identity = slot_identity(slot)
    expected = {
        "schema_version": CALIBRATION_PREVIEW_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": slot,
        "difficulty": identity["difficulty"],
        "phase": identity["phase"],
        "scenario_id": rate3_protocol.expected_scenario(slot, STUDY_ID),
    }
    for key, value in expected.items():
        if preview.get(key) != value:
            raise Rate3StudyError(f"calibration preview {key} mismatch")
    frame_id = int(preview["reference_frame_id"])
    stem = f"frame_{frame_id:010d}"
    source_image = runtime / "frames" / f"{stem}.jpg"
    source_metadata = runtime / "frames" / f"{stem}.json"
    overlay_path = preview_path.with_suffix(".jpg")
    hashes = {
        "reference_image_sha256": sha256_file(source_image),
        "reference_metadata_sha256": sha256_file(source_metadata),
        "overlay_sha256": sha256_file(overlay_path),
    }
    for key, value in hashes.items():
        if preview.get(key) != value:
            raise Rate3StudyError(f"calibration preview {key} binding changed")
    destination.mkdir(parents=True, exist_ok=False)
    try:
        shutil.copy2(source_image, destination / "reference.jpg")
        shutil.copy2(source_metadata, destination / "reference.json")
        shutil.copy2(overlay_path, destination / "reference-box-preview.jpg")
        shutil.copy2(preview_path, destination / "reference-box-preview.json")
        manifest = {
            "schema_version": CALIBRATION_SCHEMA,
            "study_id": STUDY_ID,
            "run_id": slot,
            "difficulty": identity["difficulty"],
            "phase": identity["phase"],
            "scenario_id": expected["scenario_id"],
            "hold_route_s_m": preview["hold_route_s_m"],
            "reference_frame_id": frame_id,
            "reference_simulation_time_s": preview[
                "reference_simulation_time_s"
            ],
            "reference_image_sha256": hashes["reference_image_sha256"],
            "reference_metadata_sha256": hashes["reference_metadata_sha256"],
            "reference_box_xywh_norm": preview["reference_box_xywh_norm"],
            "reference_box_preview_sha256": hashes["overlay_sha256"],
            "frozen_unix_s": time.time(),
        }
        create_once_json(destination / "manifest.json", manifest)
        return load_calibration(runtime, slot)
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def load_calibration(runtime: Path, slot: str) -> dict[str, Any]:
    destination = calibration_directory(runtime, slot)
    manifest = _read_object(destination / "manifest.json")
    identity = slot_identity(slot)
    expected = {
        "schema_version": CALIBRATION_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": slot,
        "difficulty": identity["difficulty"],
        "phase": identity["phase"],
        "scenario_id": rate3_protocol.expected_scenario(slot, STUDY_ID),
        "reference_image_sha256": sha256_file(destination / "reference.jpg"),
        "reference_metadata_sha256": sha256_file(destination / "reference.json"),
        "reference_box_preview_sha256": sha256_file(
            destination / "reference-box-preview.jpg"
        ),
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise Rate3StudyError(f"RATE-003 calibration {key} mismatch")
    _validate_box(manifest.get("reference_box_xywh_norm", ()))
    manifest["manifest_sha256"] = sha256_file(destination / "manifest.json")
    return manifest


def calibration_binding_sha256(runtime: Path, slot: str) -> str:
    """The pairing anchor: frozen frame bytes + operator box, as one hash."""

    calibration = load_calibration(runtime, slot)
    return calibration["manifest_sha256"]


# --------------------------------------------------------------------------
# launch and release
# --------------------------------------------------------------------------


def rate3_tracker_command(
    *,
    python_executable: Path,
    runtime: Path,
    init_box: Sequence[float],
    ground_plane_y_m: float,
    reanchor_config: Path = DEFAULT_REANCHOR_CONFIG,
    tracker_model_spec: Path = DEFAULT_NANOTRACK_V2_SPEC,
    tracker_model_dir: Path = DEFAULT_NANOTRACK_V2_MODEL_DIR,
) -> list[str]:
    runtime = Path(runtime)
    _, session = rate3_protocol.load_session(runtime)
    run_id = str(session["run_id"])
    identity = slot_identity(run_id)
    if identity["kind"] == "calibration":
        raise Rate3StudyError("calibration slots do not launch the tracker")
    calibration = calibration_preflight(runtime, session)
    box = _validate_box(init_box)
    if calibration is not None and list(box) != calibration[
        "reference_box_xywh_norm"
    ]:
        raise Rate3StudyError(
            "launch box differs from the frozen calibration product"
        )
    _, scenario = scenario_config_for(
        runtime, str(identity["difficulty"]), int(identity["rate_hz"])
    )
    command = tracker_command(
        python_executable=python_executable,
        runtime=runtime.resolve(),
        init_frame=int(session["init_frame_id"]),
        init_box=box,
        track_id=scenario["target"]["track_id"],
        scenario_id=str(session["scenario_id"]),
        condition="follow",
        ground_plane_y_m=ground_plane_y_m,
        planned_duration_s=PLANNED_DURATION_S,
        run_id=run_id,
        tracker=TRACKER_ID,
        tracker_model_spec=tracker_model_spec,
        tracker_model_dir=tracker_model_dir,
    )
    command.append("--rate3-session")
    command.extend(("--reanchor-config", str(reanchor_config)))
    return command


def launch_tracker(
    *,
    python_executable: Path,
    runtime: Path,
    init_box: Sequence[float],
    ground_plane_y_m: float,
    reanchor_config: Path = DEFAULT_REANCHOR_CONFIG,
) -> subprocess.CompletedProcess[str]:
    command = rate3_tracker_command(
        python_executable=python_executable,
        runtime=runtime,
        init_box=init_box,
        ground_plane_y_m=ground_plane_y_m,
        reanchor_config=reanchor_config,
    )
    return subprocess.run(command, cwd=PROJECT_ROOT, text=True, check=False)


def _coordinator_failure(
    runtime: Path,
    session: Mapping[str, Any],
    *,
    stage: str,
    reason: str,
) -> None:
    atomic_json(
        Path(runtime) / "release_coordinator_failure.json",
        {
            "schema_version": COORDINATOR_FAILURE_SCHEMA,
            "study_id": session["study_id"],
            "run_id": session["run_id"],
            "stage": stage,
            "reason": reason,
            "failed_unix_s": time.time(),
        },
    )


def coordinate_release(
    runtime: Path,
    *,
    confirmed: bool,
    timeout_s: float = 10.0,
    poll_interval_s: float = RELEASE_POLL_INTERVAL_S,
    monotonic: Any = time.monotonic,
    sleeper: Any = time.sleep,
    command_id: str | None = None,
) -> dict[str, Any]:
    if not confirmed:
        raise Rate3StudyError("release requires completed operator confirmation")
    runtime = Path(runtime)
    _, session = rate3_protocol.load_session(runtime)
    if session["study_id"] != STUDY_ID:
        raise Rate3StudyError(
            "the batch-2 coordinator only drives research identities"
        )
    run_directory = runtime / "runs" / str(session["run_id"])
    if not (run_directory / "manifest.json").is_file():
        raise FileNotFoundError("tracker run manifest is not available")
    timeout = _finite(timeout_s, "timeout_s")
    poll = _finite(poll_interval_s, "poll_interval_s")
    if timeout <= 0.0 or poll <= 0.0:
        raise Rate3StudyError("timeout and poll interval must be positive")
    deadline = monotonic() + timeout
    previous_seq = -1
    ready_bytes: bytes | None = None
    last_error = "tracker_ready_unavailable"
    while monotonic() < deadline:
        try:
            candidate_bytes, ready, observed_frame_id = (
                rate3_protocol.read_consistent_ready(
                    runtime,
                    session,
                    previous_seq=previous_seq,
                    now_monotonic_s=monotonic(),
                )
            )
            ready_seq = int(ready["seq"])
            ready_frame_id = int(ready["last_processed_frame_id"])
            if previous_seq < 0:
                previous_seq = ready_seq
            elif (
                observed_frame_id == ready_frame_id
                and latest_frame_id(runtime) == ready_frame_id
            ):
                ready_bytes = candidate_bytes
                break
            else:
                previous_seq = ready_seq
                last_error = (
                    "tracker-ready has no zero-backlog command-transport budget"
                )
        except (FileNotFoundError, Rate2ProtocolError) as exception:
            last_error = f"{type(exception).__name__}:{exception}"
        sleeper(poll)
    if ready_bytes is None:
        _coordinator_failure(
            runtime, session, stage="ready_prefilter", reason=last_error
        )
        raise TimeoutError("no fresh advancing tracker-ready heartbeat")
    command_bytes = rate3_protocol.build_release_command(
        session,
        ready_bytes,
        command_id=command_id or f"rate3-release-{time.time_ns()}",
    )
    atomic_bytes(runtime / "experiment_control.json", command_bytes)
    deadline = monotonic() + timeout
    ack_path = runtime / "release_ack.json"
    accepted_path = runtime / "release_command.accepted.json"
    while monotonic() < deadline:
        if ack_path.is_file() and accepted_path.is_file():
            try:
                accepted_bytes = accepted_path.read_bytes()
                if accepted_bytes != command_bytes:
                    raise Rate2ProtocolError(
                        "Unity accepted command bytes differ from the "
                        "coordinator command"
                    )
                ack_bytes = ack_path.read_bytes()
                ack = rate3_protocol.validate_release_bundle(
                    command_bytes, ack_bytes, session
                )
                provenance = rate3_protocol.archive_release_provenance(
                    runtime, run_directory, session
                )
                return {
                    "run_id": session["run_id"],
                    "command_id": ack["command_id"],
                    "release_frame_id": ack["release_frame_id"],
                    "accepted_backlog_frames": ack["accepted_backlog_frames"],
                    "release_monotonic_s": ack["release_monotonic_s"],
                    "release_clock_id": ack["release_clock_id"],
                    "provenance": provenance,
                }
            except (OSError, ValueError, Rate2ProtocolError) as exception:
                _coordinator_failure(
                    runtime,
                    session,
                    stage="ack_validation",
                    reason=f"{type(exception).__name__}:{exception}",
                )
                raise
        sleeper(poll)
    _coordinator_failure(
        runtime, session, stage="ack_wait", reason="release_ack_timeout"
    )
    raise TimeoutError("Unity release ack did not arrive before timeout")


# --------------------------------------------------------------------------
# offline analysis of the evaluator truth stream (§5, §11)
# --------------------------------------------------------------------------


def read_evaluation_truth(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    text = Path(path).read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exception:
            raise Rate3StudyError(
                f"evaluation truth line {number} is not valid JSON"
            ) from exception
        if value.get("schema_version") != EVALUATION_TRUTH_SCHEMA:
            raise Rate3StudyError(
                f"evaluation truth line {number} has schema "
                f"{value.get('schema_version')!r}"
            )
        records.append(value)
    records.sort(key=lambda item: int(item["frame_id"]))
    return records


def collect_evaluation_truth(
    runtime: Path,
    run_directory: Path,
) -> Path | None:
    """Move the evaluator sidecar into the run directory (offline chain)."""

    source = Path(runtime) / EVALUATION_TRUTH_FILE
    destination = Path(run_directory) / EVALUATION_TRUTH_FILE
    if destination.is_file():
        return destination
    if not source.is_file():
        return None
    shutil.move(str(source), str(destination))
    return destination


def measure_displacement(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """§5: `d_k = ||c_k - c_{k-1}||_2` over adjacent published frame pairs."""

    samples: list[float] = []
    eligible_pairs = 0
    for previous, current in zip(records, records[1:]):
        if int(current["frame_id"]) != int(previous["frame_id"]) + 1:
            continue
        eligible_pairs += 1
        if not (
            previous.get("truth_box_available")
            and current.get("truth_box_available")
            and previous.get("geometrically_visible")
            and current.get("geometrically_visible")
        ):
            continue
        samples.append(
            math.hypot(
                _finite(current["truth_center_x_px"], "truth_center_x_px")
                - _finite(previous["truth_center_x_px"], "truth_center_x_px"),
                _finite(current["truth_center_y_px"], "truth_center_y_px")
                - _finite(previous["truth_center_y_px"], "truth_center_y_px"),
            )
        )
    summary: dict[str, Any] = {
        "schema_version": DISPLACEMENT_SCHEMA,
        "definition": (
            "L2 distance between the evaluation-domain projected truth box "
            "centres of adjacent published sensor frames, both sides "
            "physically visible"
        ),
        "adjacent_frame_pairs": eligible_pairs,
        "qualified_pair_count": len(samples),
        "median_px": None,
        "p05_px": None,
        "p95_px": None,
        "quantile_method": "type-7 linear interpolation",
    }
    if samples:
        summary["median_px"] = rate3_decision.quantile_type7(samples, 0.50)
        summary["p05_px"] = rate3_decision.quantile_type7(samples, 0.05)
        summary["p95_px"] = rate3_decision.quantile_type7(samples, 0.95)
    return summary


def measure_lap_period(
    records: Sequence[Mapping[str, Any]],
    *,
    route: Sequence[Mapping[str, Any]],
    release_simulation_s: float,
    difficulty: str,
) -> dict[str, Any]:
    """§11: directed start section on the released span. Report only."""

    origin = (float(route[0]["x"]), float(route[0]["z"]))
    following = (float(route[1]["x"]), float(route[1]["z"]))
    normal_x, normal_z = following[0] - origin[0], following[1] - origin[1]
    norm = math.hypot(normal_x, normal_z)
    if norm <= 0.0:
        raise Rate3StudyError("route[0] and route[1] must differ")
    normal = (normal_x / norm, normal_z / norm)
    tangent = (-normal[1], normal[0])

    def signed(record: Mapping[str, Any]) -> tuple[float, float, float]:
        dx = _finite(record["target_world_x_m"], "target_world_x_m") - origin[0]
        dz = _finite(record["target_world_z_m"], "target_world_z_m") - origin[1]
        elapsed = (
            _finite(record["simulation_time_s"], "simulation_time_s")
            - release_simulation_s
        )
        return (
            dx * normal[0] + dz * normal[1],
            dx * tangent[0] + dz * tangent[1],
            elapsed,
        )

    crossings: list[dict[str, Any]] = []
    gaps: list[tuple[float, float]] = []
    for previous, current in zip(records, records[1:]):
        before = signed(previous)
        after = signed(current)
        if int(current["frame_id"]) != int(previous["frame_id"]) + 1:
            gaps.append((before[2], after[2]))
            continue
        if not (before[0] < 0.0 <= after[0]):
            continue
        span = after[0] - before[0]
        fraction = 0.0 if span == 0.0 else (0.0 - before[0]) / span
        lateral = before[1] + fraction * (after[1] - before[1])
        if abs(lateral) > LAP_LATERAL_TOLERANCE_M:
            continue
        crossings.append(
            {
                "elapsed_s": before[2] + fraction * (after[2] - before[2]),
                "lateral_offset_m": lateral,
                "frame_id": int(current["frame_id"]),
                "capture_monotonic_s": current.get("capture_monotonic_s"),
            }
        )

    intervals: list[dict[str, Any]] = []
    dropped = 0
    for start, end in zip(crossings, crossings[1:]):
        overlapped = any(
            gap[0] < end["elapsed_s"] and gap[1] > start["elapsed_s"]
            for gap in gaps
        )
        if overlapped:
            dropped += 1
            continue
        intervals.append(
            {
                "start_elapsed_s": start["elapsed_s"],
                "end_elapsed_s": end["elapsed_s"],
                "period_s": end["elapsed_s"] - start["elapsed_s"],
            }
        )
    total_intervals = len(intervals) + dropped
    dropped_fraction = (
        dropped / total_intervals if total_intervals else 0.0
    )
    periods = [interval["period_s"] for interval in intervals]
    status = "MEASURED"
    if difficulty == "D1" and len(crossings) < LAP_MINIMUM_CROSSINGS:
        status = "LAP_MEASUREMENT_INSUFFICIENT"
    if not periods:
        status = "LAP_MEASUREMENT_INSUFFICIENT"
    elif dropped_fraction > LAP_DROPPED_FRACTION_LIMIT:
        status = "LAP_MEASUREMENT_INSUFFICIENT"
    median = (
        rate3_decision.quantile_type7(periods, 0.50) if periods else None
    )
    deviation_flag = None
    if difficulty == "D1" and median is not None:
        deviation_flag = (
            abs(median - NOMINAL_D1_LOOP_PERIOD_S) / NOMINAL_D1_LOOP_PERIOD_S
            > LAP_PERIOD_DEVIATION_FRACTION
        )
    return {
        "schema_version": LAP_PERIOD_SCHEMA,
        "status": status,
        "gating": False,
        "note": (
            "report only; never determines planned_duration_s and never "
            "feeds a completion gate (§11)"
        ),
        "difficulty": difficulty,
        "start_section": {
            "origin_world_m": {"x": origin[0], "z": origin[1]},
            "normal": {"x": normal[0], "z": normal[1]},
            "direction": "negative_to_positive_only",
            "lateral_tolerance_m": LAP_LATERAL_TOLERANCE_M,
        },
        "crossing_count": len(crossings),
        "crossings": crossings,
        "lap_intervals": intervals,
        "dropped_lap_intervals": dropped,
        "dropped_lap_interval_fraction": dropped_fraction,
        "median_period_s": median,
        "min_period_s": min(periods) if periods else None,
        "max_period_s": max(periods) if periods else None,
        "p05_period_s": (
            rate3_decision.quantile_type7(periods, 0.05) if periods else None
        ),
        "p95_period_s": (
            rate3_decision.quantile_type7(periods, 0.95) if periods else None
        ),
        "nominal_period_s": (
            NOMINAL_D1_LOOP_PERIOD_S if difficulty == "D1" else None
        ),
        "LAP_PERIOD_DEVIATION_FLAG": deviation_flag,
    }


# --------------------------------------------------------------------------
# finalize (§10 completion gate + S1'-S3)
# --------------------------------------------------------------------------


def _metrics(run_directory: Path) -> dict[str, Any]:
    metrics = _read_object(Path(run_directory) / "metrics.final.json")
    if metrics.get("schema_version") != "tethered-evaluation/v1":
        raise Rate3StudyError("invalid evaluator metrics schema")
    if not isinstance(metrics.get("aggregate"), Mapping):
        raise Rate3StudyError("metrics aggregate is missing")
    return metrics


def finalize_attempt(runtime: Path, run_id: str) -> dict[str, Any]:
    runtime = Path(runtime)
    load_campaign(runtime)
    identity = slot_identity(run_id)
    if identity["kind"] in {"scouting", "calibration"}:
        raise Rate3StudyError(f"{run_id} does not produce a measurement run")
    run_directory = runtime / "runs" / run_id
    status_path = run_directory / "rate3-status.json"
    if status_path.is_file():
        return _read_object(status_path)

    collect_evaluation_truth(runtime, run_directory)
    provenance = rate3_protocol.validate_provenance(run_directory)
    manifest = _read_object(run_directory / "manifest.json")
    summary = _read_object(run_directory / "summary.json")
    metrics = _metrics(run_directory)
    aggregate = metrics["aggregate"]
    if manifest.get("run_id") != run_id or provenance.get("run_id") != run_id:
        raise Rate3StudyError("run directory / manifest identity mismatch")
    if metrics.get("scenario_id") != manifest.get("scenario_id"):
        raise Rate3StudyError("metrics scenario identity mismatch")

    errors: list[str] = []
    planned = _finite(manifest.get("planned_duration_s"), "planned_duration_s")
    if abs(planned - PLANNED_DURATION_S) > 1e-9:
        errors.append("planned_duration_not_frozen")

    records, truncated = read_frame_records(run_directory / "frames.jsonl")
    if truncated:
        errors.append("frames_truncated")
    measurement = [
        record
        for record in records
        if record.get("record_kind", "frame") == "frame"
        and record.get("phase") == "measurement"
    ]
    release_monotonic_s = _finite(
        provenance.get("release_monotonic_s"), "release_monotonic_s"
    )
    release_simulation_s = _finite(
        provenance.get("release_simulation_s"), "release_simulation_s"
    )
    captures = [
        _finite(record.get("capture_monotonic_s"), "capture_monotonic_s")
        for record in measurement
        if record.get("capture_monotonic_s") is not None
    ]
    if len(captures) != len(measurement):
        errors.append("INVALID_CLOCK_missing_capture_monotonic")

    simulation_duration_s = _finite(
        summary.get("actual_duration_s"), "actual_duration_s"
    )
    wall_duration_s = (
        max(captures) - release_monotonic_s if captures else 0.0
    )
    evaluator_cutoff_s = _finite(
        metrics.get("elapsed_simulation_s"), "metrics.elapsed_simulation_s"
    )
    lost_records = int(summary.get("lost_records", 0))
    time_to_first_lost_s = _finite(
        summary.get("time_to_first_lost_s"), "time_to_first_lost_s"
    )
    right_censored = bool(summary.get("time_to_first_lost_right_censored"))

    if simulation_duration_s + DURATION_EPSILON_S < PLANNED_DURATION_S:
        errors.append("simulation_duration_not_reached")
    if wall_duration_s + DURATION_EPSILON_S < PLANNED_DURATION_S:
        errors.append("shared_host_wall_duration_not_reached")
    if evaluator_cutoff_s + DURATION_EPSILON_S < PLANNED_DURATION_S:
        errors.append("evaluator_cutoff_not_reached")
    if (
        abs(evaluator_cutoff_s - simulation_duration_s)
        > EVALUATOR_CUTOFF_TOLERANCE_S
    ):
        errors.append("evaluator_cutoff_delta_out_of_tolerance")
    if lost_records == 0:
        if not right_censored:
            errors.append("right_censored_flag_inconsistent")
        if abs(time_to_first_lost_s - PLANNED_DURATION_S) > 1e-9:
            errors.append("right_censored_lost_not_planned_duration")

    if summary.get("release_clock_id") != rate3_protocol.CLOCK_ID:
        errors.append("INVALID_CLOCK_IDENTITY_summary")
    event_counts = summary.get("event_counts")
    invalid_clock_events = (
        int(event_counts.get("INVALID_CLOCK", 0))
        if isinstance(event_counts, Mapping)
        else 0
    )
    if invalid_clock_events:
        errors.append("INVALID_CLOCK_events")
    cadence = summary.get("monotonic_capture_cadence_post_release")
    if not isinstance(cadence, Mapping):
        cadence = {}
        errors.append("monotonic_cadence_missing")
    if cadence.get("strictly_increasing") is not True:
        errors.append("INVALID_CLOCK_cadence_not_increasing")

    target_rate = int(identity["rate_hz"])
    wall_rate = cadence.get("rate_hz")
    s1 = (
        cadence.get("strictly_increasing") is True
        and isinstance(wall_rate, (int, float))
        and not isinstance(wall_rate, bool)
        and math.isfinite(float(wall_rate))
        and float(wall_rate) >= target_rate * S1_RATE_FRACTION
    )
    compute_p95 = (summary.get("compute_latency_ms") or {}).get("p95")
    s2 = (
        isinstance(compute_p95, (int, float))
        and not isinstance(compute_p95, bool)
        and math.isfinite(float(compute_p95))
        and float(compute_p95) < S2_COMPUTE_LATENCY_LIMIT_MS
    )
    backlog_p95 = (summary.get("backlog_count") or {}).get("p95")
    s3 = (
        isinstance(backlog_p95, (int, float))
        and not isinstance(backlog_p95, bool)
        and math.isfinite(float(backlog_p95))
        and float(backlog_p95) <= 1.0
        and int(summary.get("reinit_required_records", 0)) == 0
    )
    if not s1:
        errors.append("S1_RATE_UNSUSTAINABLE")
    if not s2:
        errors.append("S2_COMPUTE_LATENCY")
    if not s3:
        errors.append("S3_BACKLOG_OR_REINIT")

    calibration_slot = calibration_slot_for(
        str(identity["difficulty"]), int(identity["phase"])
    )
    try:
        calibration = load_calibration(runtime, calibration_slot)
        calibration_sha256: str | None = calibration["manifest_sha256"]
        rate3_identity = manifest.get("rate3")
        if not isinstance(rate3_identity, Mapping):
            errors.append("manifest_rate3_identity_missing")
        else:
            if rate3_identity.get("init_frame_id") != calibration[
                "reference_frame_id"
            ]:
                errors.append("calibration_init_frame_mismatch")
            if rate3_identity.get("init_image_sha256") != calibration[
                "reference_image_sha256"
            ]:
                errors.append("calibration_init_image_mismatch")
    except (FileNotFoundError, Rate3StudyError, Rate2ProtocolError):
        calibration_sha256 = None
        errors.append("frozen_calibration_product_unavailable")

    truth_path = run_directory / EVALUATION_TRUTH_FILE
    truth_records: list[dict[str, Any]] = []
    if truth_path.is_file():
        truth_records = read_evaluation_truth(truth_path)
        for record in truth_records:
            if record.get("run_id") != run_id:
                errors.append("evaluation_truth_run_identity_mismatch")
                break
            if int(record["frame_id"]) < int(provenance["release_frame_id"]):
                errors.append("evaluation_truth_precedes_release")
                break
    else:
        errors.append("evaluation_truth_stream_missing")

    _, scenario = scenario_config_for(
        runtime, str(identity["difficulty"]), target_rate
    )
    displacement = measure_displacement(truth_records)
    lap = (
        measure_lap_period(
            truth_records,
            route=scenario["target"]["route_world_m"],
            release_simulation_s=release_simulation_s,
            difficulty=str(identity["difficulty"]),
        )
        if truth_records
        else {
            "schema_version": LAP_PERIOD_SCHEMA,
            "status": "LAP_MEASUREMENT_INSUFFICIENT",
            "gating": False,
            "difficulty": identity["difficulty"],
            "median_period_s": None,
        }
    )
    atomic_json(run_directory / "lap_period.json", lap)

    status = {
        "schema_version": ATTEMPT_STATUS_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": run_id,
        "kind": identity["kind"],
        "difficulty": identity["difficulty"],
        "phase": identity["phase"],
        "rate_hz": identity["rate_hz"],
        "formal_slot_number": identity["formal_slot_number"],
        "admissible": not errors,
        "classification": "COMPLETE" if not errors else "INVALID",
        "errors": errors,
        "planned_duration_s": planned,
        "completion_gate": {
            "simulation_duration_s": simulation_duration_s,
            "shared_host_wall_duration_s": wall_duration_s,
            "evaluator_cutoff_s": evaluator_cutoff_s,
            "evaluator_cutoff_delta_s": abs(
                evaluator_cutoff_s - simulation_duration_s
            ),
            "evaluator_cutoff_tolerance_s": EVALUATOR_CUTOFF_TOLERANCE_S,
            "time_to_first_lost_s": time_to_first_lost_s,
            "time_to_first_lost_right_censored": right_censored,
        },
        "gates": {"S1": s1, "S2": s2, "S3": s3},
        "c_track_given_geom": _finite(
            aggregate.get("c_track_given_geom"), "aggregate.c_track_given_geom"
        ),
        "c_geom": _finite(aggregate.get("c_geom"), "aggregate.c_geom"),
        "c_track": _finite(aggregate.get("c_track"), "aggregate.c_track"),
        "matched_tracking_observations": int(
            aggregate.get("matched_tracking_observations", 0)
        ),
        "incorrect_tracking_observations": int(
            aggregate.get("incorrect_tracking_observations", 0)
        ),
        "release_unix_s": provenance["release_unix_s"],
        "release_monotonic_s": release_monotonic_s,
        "release_frame_id": provenance["release_frame_id"],
        "attempt_number": failed_attempt_count(runtime, run_id) + 1,
        "calibration_slot": calibration_slot,
        "calibration_sha256": calibration_sha256,
        "manifest_sha256": sha256_file(run_directory / "manifest.json"),
        "release_provenance_sha256": sha256_file(
            run_directory / "release_provenance.json"
        ),
        "summary_sha256": sha256_file(run_directory / "summary.json"),
        "metrics_sha256": sha256_file(run_directory / "metrics.final.json"),
        "evaluation_truth_sha256": (
            sha256_file(truth_path) if truth_path.is_file() else None
        ),
        "displacement": displacement,
        "lap_period_s": lap.get("median_period_s"),
        "lap_period_status": lap.get("status"),
        "lap_period_sha256": sha256_file(run_directory / "lap_period.json"),
        "finalized_unix_s": time.time(),
    }
    create_once_json(status_path, status)
    return _read_object(status_path)


def attempt_row(runtime: Path, run_id: str) -> dict[str, Any]:
    """Re-verified decision input for one finalized run."""

    run_directory = Path(runtime) / "runs" / run_id
    status = _read_object(run_directory / "rate3-status.json")
    if (
        status.get("schema_version") != ATTEMPT_STATUS_SCHEMA
        or status.get("run_id") != run_id
    ):
        raise Rate3StudyError(f"invalid attempt status for {run_id}")
    bindings = {
        "manifest_sha256": sha256_file(run_directory / "manifest.json"),
        "release_provenance_sha256": sha256_file(
            run_directory / "release_provenance.json"
        ),
        "summary_sha256": sha256_file(run_directory / "summary.json"),
        "metrics_sha256": sha256_file(run_directory / "metrics.final.json"),
    }
    if any(status.get(key) != value for key, value in bindings.items()):
        raise Rate3StudyError(f"{run_id} status artifact binding mismatch")
    aggregate = _metrics(run_directory)["aggregate"]
    # B1.1: the decision copies the authoritative unconditional values and
    # fails closed if they no longer match the run's own metrics.
    authoritative = {
        "c_geom": _finite(aggregate.get("c_geom"), "aggregate.c_geom"),
        "c_track": _finite(aggregate.get("c_track"), "aggregate.c_track"),
        "c_track_given_geom": _finite(
            aggregate.get("c_track_given_geom"), "aggregate.c_track_given_geom"
        ),
    }
    for key, value in authoritative.items():
        if status.get(key) != value:
            raise Rate3StudyError(
                f"{run_id} {key} no longer matches metrics.final.json"
            )
    identity = slot_identity(run_id)
    return {
        "run_id": run_id,
        "difficulty": identity["difficulty"],
        "phase": identity["phase"],
        "rate_hz": identity["rate_hz"],
        "formal_slot_number": identity["formal_slot_number"],
        "attempt_number": status.get("attempt_number"),
        "admissible": bool(status.get("admissible")),
        "errors": status.get("errors", []),
        **authoritative,
        "matched_tracking_observations": status.get(
            "matched_tracking_observations"
        ),
        "incorrect_tracking_observations": status.get(
            "incorrect_tracking_observations"
        ),
        "release_unix_s": status.get("release_unix_s"),
        "release_monotonic_s": status.get("release_monotonic_s"),
        "planned_duration_s": status.get("planned_duration_s"),
        "calibration_slot": status.get("calibration_slot"),
        "calibration_sha256": status.get("calibration_sha256"),
        "manifest_sha256": bindings["manifest_sha256"],
        "release_provenance_sha256": bindings["release_provenance_sha256"],
        "metrics_sha256": bindings["metrics_sha256"],
        "evaluation_truth_sha256": status.get("evaluation_truth_sha256"),
        "lap_period_s": status.get("lap_period_s"),
        "lap_period_status": status.get("lap_period_status"),
    }


# --------------------------------------------------------------------------
# probe (§5 + BC-DRB-6) and the D2 selection
# --------------------------------------------------------------------------


def build_probe(runtime: Path) -> dict[str, Any]:
    """§5: A0 admissibility is evaluated before B1-B3, always.

    An A0 verdict is an **attempt** verdict: §5 sends the slot back for an
    in-place rerun (total attempts <= 3), so it is written to the
    per-attempt artifact and `probe.json` stays unwritten. Only a terminal
    disposition — B1/B2/B3, or `BLOCKED_PROBE` once the attempt cap is
    exhausted — freezes the create-once campaign artifact.

    A call made before any adjudicable attempt exists is a **refusal**, not
    an adjudication, so a mis-timed CLI invocation cannot consume the
    campaign's probe verdict.
    """

    runtime = Path(runtime)
    load_campaign(runtime)
    if probe_path(runtime).is_file():
        return _read_object(probe_path(runtime))
    run_directory = runtime / "runs" / PROBE_SLOT
    try:
        status: dict[str, Any] = _read_object(
            run_directory / "rate3-status.json"
        )
    except (FileNotFoundError, ValueError) as exception:
        raise Rate3StudyError(
            "there is no adjudicable probe attempt: finalize a "
            f"{PROBE_SLOT} run first ({exception})"
        ) from exception
    attempt_number = failed_attempt_count(runtime, PROBE_SLOT) + 1
    attempt_path = probe_attempt_path(runtime, attempt_number)
    if attempt_path.is_file():
        return _read_object(attempt_path)

    a0_reasons: list[str] = []
    if not status.get("admissible"):
        a0_reasons.append(
            "probe session protocol invalid: " + ", ".join(status.get("errors", []))
        )
    displacement = status.get("displacement") or {}
    conditional = status.get("c_track_given_geom")
    c_geom = status.get("c_geom")
    c_track = status.get("c_track")
    if conditional is None:
        a0_reasons.append("primary endpoint C_track|geom is missing")
    if int(displacement.get("qualified_pair_count") or 0) < 1:
        a0_reasons.append("fewer than one qualified adjacent frame pair")
    for key in ("median_px", "p05_px", "p95_px"):
        value = displacement.get(key)
        if (
            value is None
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            a0_reasons.append(f"displacement {key} is not finite")

    lower, upper = PROBE_DISPLACEMENT_RANGE_PX
    exhausted = attempt_number >= MAX_ATTEMPTS_PER_SLOT
    if a0_reasons:
        branch = "A0"
        if exhausted:
            disposition = "BLOCKED_PROBE"
            outcome = (
                f"attempt {attempt_number} of {MAX_ATTEMPTS_PER_SLOT} is "
                "invalid and the per-slot cap is exhausted; the probe is "
                "blocked and no formal measurement may start"
            )
        else:
            disposition = "PROBE_ATTEMPT_INVALID"
            outcome = (
                f"attempt {attempt_number} of {MAX_ATTEMPTS_PER_SLOT} is "
                "invalid; archive it and rerun the same slot in place"
            )
        d2_speed = None
    else:
        median = float(displacement["median_px"])
        if not lower <= median <= upper:
            branch, disposition, outcome = (
                "B1",
                "PROBE_MODEL_INVALID",
                "the displacement model that justifies the D2 choice is "
                "falsified; stop and return to ideation/acceptance, do not "
                "downshift and do not measure",
            )
            d2_speed = None
        elif float(conditional) >= PROBE_FLOOR_C_TRACK_GIVEN_GEOM:
            branch, disposition, outcome = (
                "B2",
                "PROBE_CONFIRMS_D2",
                "D2 frozen at 8.0 m/s; the formal matrix may proceed",
            )
            d2_speed = DIFFICULTY_SPEED_MPS["D2"]
        else:
            branch, disposition, outcome = (
                "B3",
                "PROBE_TRIGGERS_DOWNSHIFT",
                "D2 := 6.0 m/s; acceptance criterion 0b must be completed "
                "before any formal measurement, and no second probe is run",
            )
            d2_speed = D2_DOWNSHIFT_SPEED_MPS

    probe = {
        "schema_version": PROBE_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": PROBE_SLOT,
        "branch": branch,
        "disposition": disposition,
        "outcome": outcome,
        "attempt_number": attempt_number,
        "max_attempts": MAX_ATTEMPTS_PER_SLOT,
        "terminal": disposition != "PROBE_ATTEMPT_INVALID",
        "prior_attempt_sha256": [
            sha256_file(probe_attempt_path(runtime, number))
            for number in range(1, attempt_number)
            if probe_attempt_path(runtime, number).is_file()
        ],
        "a0_findings": a0_reasons,
        "displacement": displacement,
        "displacement_allowed_range_px": list(PROBE_DISPLACEMENT_RANGE_PX),
        "floor_threshold": PROBE_FLOOR_C_TRACK_GIVEN_GEOM,
        # BC-DRB-6: attribution reads all three quantities, never the
        # conditional one alone.
        "c_track_given_geom": conditional,
        "c_geom": c_geom,
        "c_track": c_track,
        "selected_d2_speed_mps": d2_speed,
        "manifest_sha256": (status or {}).get("manifest_sha256"),
        "release_provenance_sha256": (status or {}).get(
            "release_provenance_sha256"
        ),
        "metrics_sha256": (status or {}).get("metrics_sha256"),
        "evaluation_truth_sha256": (status or {}).get(
            "evaluation_truth_sha256"
        ),
        "calibration_sha256": (status or {}).get("calibration_sha256"),
        "data_use": (
            "probe data never enters a formal cell, never tunes a parameter "
            "and never revises a frozen threshold"
        ),
        "generated_unix_s": time.time(),
    }
    # Every adjudication is recorded per attempt; only a terminal one also
    # freezes the campaign artifact the formal phase reads.
    create_once_json(attempt_path, probe)
    if probe["terminal"]:
        create_once_json(probe_path(runtime), probe)
        return _read_object(probe_path(runtime))
    return _read_object(attempt_path)


def select_d2(
    runtime: Path,
    *,
    speed_mps: float,
    r20_config: Path,
    r5_config: Path,
    difficulty_audit: Path,
    authorization_0b: str | None = None,
) -> dict[str, Any]:
    """Freeze the D2 configuration the formal matrix will measure."""

    runtime = Path(runtime)
    load_campaign(runtime)
    if d2_selection_path(runtime).is_file():
        return load_d2_selection(runtime)
    probe = _read_object(probe_path(runtime))
    expected = probe.get("selected_d2_speed_mps")
    if expected is None:
        raise Rate3StudyError(
            f"probe disposition {probe.get('disposition')!r} does not select "
            "a D2 speed"
        )
    if abs(float(speed_mps) - float(expected)) > 1e-9:
        raise Rate3StudyError(
            f"probe selected {expected} m/s, not {speed_mps} m/s"
        )
    if (
        abs(float(speed_mps) - D2_DOWNSHIFT_SPEED_MPS) <= 1e-9
        and not (authorization_0b or "").strip()
    ):
        raise Rate3StudyError(
            "the 6.0 m/s branch requires acceptance criterion 0b (user "
            "confirmation of the implemented config and its re-audited hash)"
        )
    audit = _read_object(Path(difficulty_audit))
    if audit.get("status") != "ENVELOPE_OK":
        raise Rate3StudyError(
            "difficulty envelope audit did not pass its must-pass gates"
        )
    configs = {}
    for label, path in (("r20", Path(r20_config)), ("r5", Path(r5_config))):
        scenario = json.loads(path.read_text(encoding="utf-8"))
        if abs(float(scenario["target"]["speed_mps"]) - float(speed_mps)) > 1e-9:
            raise Rate3StudyError(f"{path} does not carry {speed_mps} m/s")
        if scenario["scenario_id"] != "p1-scene-004-d2":
            raise Rate3StudyError(f"{path} has the wrong scenario_id")
        configs[label] = {
            "path": str(path),
            "sha256": sha256_file(path),
            "capture_hz": scenario["sensor"]["capture_hz"],
        }
    selection = {
        "schema_version": D2_SELECTION_SCHEMA,
        "study_id": STUDY_ID,
        "speed_mps": float(speed_mps),
        "probe_branch": probe.get("branch"),
        "probe_disposition": probe.get("disposition"),
        "configs": configs,
        "difficulty_audit_path": str(Path(difficulty_audit)),
        "difficulty_audit_sha256": sha256_file(Path(difficulty_audit)),
        "authorization_0b": (authorization_0b or "").strip() or None,
        "selected_unix_s": time.time(),
    }
    create_once_json(d2_selection_path(runtime), selection)
    return load_d2_selection(runtime)


def load_d2_selection(runtime: Path) -> dict[str, Any]:
    selection = _read_object(d2_selection_path(runtime))
    if selection.get("schema_version") != D2_SELECTION_SCHEMA:
        raise Rate3StudyError("invalid D2 selection schema")
    if selection.get("study_id") != STUDY_ID:
        raise Rate3StudyError("D2 selection study_id mismatch")
    return selection


# --------------------------------------------------------------------------
# decision artifact
# --------------------------------------------------------------------------


def build_decision(runtime: Path) -> dict[str, Any]:
    runtime = Path(runtime)
    load_campaign(runtime)
    if decision_path(runtime).is_file():
        return validate_decision(runtime)
    rows: list[dict[str, Any]] = []
    unavailable: list[str] = []
    for run_id in FORMAL_SLOT_ORDER:
        try:
            rows.append(attempt_row(runtime, run_id))
        except (FileNotFoundError, ValueError, Rate2ProtocolError) as exception:
            unavailable.append(f"{run_id}: {exception}")
    lap_medians: dict[str, Any] = {}
    for difficulty in rate3_decision.DIFFICULTIES:
        periods = [
            row["lap_period_s"]
            for row in rows
            if row["difficulty"] == difficulty
            and isinstance(row.get("lap_period_s"), (int, float))
            and not isinstance(row.get("lap_period_s"), bool)
            and math.isfinite(float(row["lap_period_s"]))
        ]
        lap_medians[difficulty] = (
            rate3_decision.quantile_type7(periods, 0.50) if periods else None
        )
    body = rate3_decision.build_decision_body(rows, lap_period_medians=lap_medians)
    scouting = load_scouting(runtime)
    probe = (
        _read_object(probe_path(runtime))
        if probe_path(runtime).is_file()
        else None
    )
    decision = {
        "schema_version": rate3_decision.DECISION_SCHEMA,
        "study_id": STUDY_ID,
        "run_ids": list(FORMAL_SLOT_ORDER),
        "runs": rows,
        "unavailable_runs": unavailable,
        "actual_session_order": [
            row["run_id"]
            for row in sorted(
                (row for row in rows if row.get("release_unix_s") is not None),
                key=lambda item: float(item["release_unix_s"]),
            )
        ],
        "frozen_session_order": list(SESSION_ORDER),
        "pairing_anchor": {
            "clause": "BC-DRB-4/BC-DRB-5",
            "findings": rate3_decision.pairing_findings(rows),
        },
        "scouting_freeze_sha256": sha256_file(
            scouting_directory(runtime) / "manifest.json"
        ),
        "phase_route_s_m": scouting["phase_route_s_m"],
        "probe_sha256": (
            sha256_file(probe_path(runtime)) if probe is not None else None
        ),
        "probe_disposition": (probe or {}).get("disposition"),
        "d2_speed_mps": (
            load_d2_selection(runtime)["speed_mps"]
            if d2_selection_path(runtime).is_file()
            else None
        ),
        "batch_invalid_attempt_count": batch_invalid_attempt_count(runtime),
        "fixed_order_time_confound": load_campaign(runtime)[
            "fixed_order_time_confound"
        ],
        **body,
        "generated_unix_s": time.time(),
    }
    create_once_json(decision_path(runtime), decision)
    return validate_decision(runtime)


def validate_decision(runtime: Path) -> dict[str, Any]:
    """Recompute every rule from the bound artifacts."""

    runtime = Path(runtime)
    decision = _read_object(decision_path(runtime))
    if decision.get("schema_version") != rate3_decision.DECISION_SCHEMA:
        raise Rate3StudyError("invalid RATE-003 decision schema")
    if decision.get("study_id") != STUDY_ID:
        raise Rate3StudyError("decision study_id mismatch")
    if decision.get("run_ids") != list(FORMAL_SLOT_ORDER):
        raise Rate3StudyError("decision run identities changed")
    if decision.get("final_action") not in rate3_decision.FINAL_ACTIONS:
        raise Rate3StudyError("decision final_action is outside the enum")
    if decision.get("theta") != rate3_decision.THETA:
        raise Rate3StudyError("decision theta changed")
    if decision.get("theta_geom") != rate3_decision.THETA_GEOM:
        raise Rate3StudyError("decision theta_geom changed")
    rows = decision.get("runs")
    if not isinstance(rows, list):
        raise Rate3StudyError("decision run rows are missing")
    for row in rows:
        current = attempt_row(runtime, str(row["run_id"]))
        for key in (
            "c_geom",
            "c_track",
            "c_track_given_geom",
            "admissible",
            "manifest_sha256",
            "release_provenance_sha256",
            "metrics_sha256",
            "calibration_sha256",
        ):
            if row.get(key) != current.get(key):
                raise Rate3StudyError(
                    f"decision input {key} for {row['run_id']} no longer "
                    "matches the archived artifacts"
                )
    recomputed = rate3_decision.build_decision_body(
        rows, lap_period_medians=decision.get("measured_lap_period_s")
    )
    for key in (
        "final_action",
        "dispositions",
        "ladder_premise_violated",
        "dr_referral_required",
        "heterogeneity_qualified",
        "cgeom_divergence_qualified",
        "CGEOM_DIVERGENCE_FLAG",
        "H2_DIVERGENCE_FLAG",
        "pseudo_ceiling_caveat_required",
    ):
        if decision.get(key) != recomputed.get(key):
            raise Rate3StudyError(f"decision {key} does not match its inputs")
    return decision


# --------------------------------------------------------------------------
# execution-order authorisation
# --------------------------------------------------------------------------


def authorize_session(runtime: Path, run_id: str) -> dict[str, Any]:
    """Every gate that must hold before a research-data session may start."""

    runtime = Path(runtime)
    load_campaign(runtime)
    load_run_gates(runtime)
    identity = slot_identity(run_id)
    if identity["kind"] != "scouting":
        run_directory = runtime / "runs" / run_id
        if run_directory.exists():
            raise FileExistsError(f"run directory already exists: {run_id}")
    if identity["kind"] == "scouting":
        if (scouting_directory(runtime) / "manifest.json").is_file():
            raise FileExistsError("scouting is already frozen")
    elif identity["kind"] == "calibration":
        # A frozen calibration product is terminal; re-attempting it would
        # mint a receipt that inflates the BC-R3-2 counter for work that
        # already succeeded.
        if (calibration_directory(runtime, run_id) / "manifest.json").is_file():
            raise FileExistsError(
                f"calibration product is already frozen: {run_id}"
            )
    attempts = failed_attempt_count(runtime, run_id)
    if attempts >= MAX_ATTEMPTS_PER_SLOT:
        raise PermissionError(
            f"per-slot attempt limit exhausted for {run_id} "
            f"({attempts}/{MAX_ATTEMPTS_PER_SLOT})"
        )
    batch_count = batch_invalid_attempt_count(runtime)
    if batch_count >= BATCH_INVALID_ATTEMPT_PAUSE:
        raise PermissionError(
            "BC-R3-2: batch_invalid_attempt_count is "
            f"{batch_count} >= {BATCH_INVALID_ATTEMPT_PAUSE}; pause, return "
            "to acceptance for failure attribution and obtain a new explicit "
            "user authorization before consuming another session"
        )
    position = SESSION_ORDER.index(run_id)
    for predecessor in SESSION_ORDER[:position]:
        _require_completed_predecessor(runtime, predecessor)
    if identity["kind"] == "formal" and identity["difficulty"] == "D2":
        selection = load_d2_selection(runtime)
        if selection["speed_mps"] != DIFFICULTY_SPEED_MPS["D2"] and not selection.get(
            "authorization_0b"
        ):
            raise PermissionError(
                "the downshifted D2 configuration needs acceptance criterion "
                "0b before any formal measurement"
            )
    return {
        "authorized": True,
        "run_id": run_id,
        "attempt_number": attempts + 1,
        "batch_invalid_attempt_count": batch_count,
        **identity,
    }


def _require_completed_predecessor(runtime: Path, predecessor: str) -> None:
    identity = slot_identity(predecessor)
    try:
        if identity["kind"] == "scouting":
            load_scouting(runtime)
            return
        if identity["kind"] == "calibration":
            load_calibration(runtime, predecessor)
            return
        if identity["kind"] == "probe":
            probe = _read_object(probe_path(runtime))
            if probe.get("disposition") not in {
                "PROBE_CONFIRMS_D2",
                "PROBE_TRIGGERS_DOWNSHIFT",
            }:
                raise Rate3StudyError(
                    f"probe disposition {probe.get('disposition')!r} does not "
                    "authorise formal measurement"
                )
            return
        row = attempt_row(runtime, predecessor)
        if not row["admissible"]:
            raise Rate3StudyError(f"{predecessor} is not admissible")
    except (
        FileNotFoundError,
        ValueError,
        PermissionError,
        Rate2ProtocolError,
    ) as exception:
        raise PermissionError(
            "the frozen RATE-003 execution order requires a completed "
            f"{predecessor}: {exception}"
        ) from exception


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="P1-M2-RATE-003 batch-2 coordinator"
    )
    parser.add_argument("--runtime", type=Path, default=RUNTIME_DEFAULT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("prepare-campaign")
    subparsers.add_parser("check-configs")

    gates = subparsers.add_parser("record-run-gates")
    gates.add_argument("--qual3-pass-attributed", action="store_true")
    gates.add_argument("--dr-round3-passed", action="store_true")
    gates.add_argument("--clock-smoke-passed", action="store_true")
    gates.add_argument("--attribution", required=True)

    install = subparsers.add_parser("install-config")
    install.add_argument("--run-id", required=True)

    scouting = subparsers.add_parser("freeze-scouting")
    scouting.add_argument("--confirmed", action="store_true")

    prepare = subparsers.add_parser("prepare-session")
    prepare.add_argument("--run-id", required=True)
    prepare.add_argument("--init-frame", type=int, required=True)
    prepare.add_argument("--init-image-sha256", required=True)

    preview = subparsers.add_parser("preview-calibration")
    preview.add_argument("--run-id", required=True)
    preview.add_argument("--box", type=float, nargs=4, required=True)

    freeze = subparsers.add_parser("freeze-calibration")
    freeze.add_argument("--run-id", required=True)
    freeze.add_argument("--confirmed", action="store_true")

    launch = subparsers.add_parser("launch")
    launch.add_argument("--box", type=float, nargs=4, required=True)
    launch.add_argument("--ground-plane-y-m", type=float, required=True)
    launch.add_argument("--python", type=Path, default=Path(sys.executable))
    launch.add_argument(
        "--reanchor-config", type=Path, default=DEFAULT_REANCHOR_CONFIG
    )

    release = subparsers.add_parser("release")
    release.add_argument("--confirmed", action="store_true")
    release.add_argument("--timeout-s", type=float, default=10.0)
    release.add_argument(
        "--poll-interval-s", type=float, default=RELEASE_POLL_INTERVAL_S
    )

    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--run-id", required=True)

    failed = subparsers.add_parser("archive-failed-attempt")
    failed.add_argument("--run-id", required=True)
    failed.add_argument("--reason", required=True)

    subparsers.add_parser("probe")

    select = subparsers.add_parser("select-d2")
    select.add_argument("--speed-mps", type=float, required=True)
    select.add_argument("--r20-config", type=Path, required=True)
    select.add_argument("--r5-config", type=Path, required=True)
    select.add_argument("--difficulty-audit", type=Path, required=True)
    select.add_argument("--authorization-0b", default=None)

    subparsers.add_parser("decision")
    subparsers.add_parser("validate-decision")
    subparsers.add_parser("batch-status")

    authorize = subparsers.add_parser("authorize")
    authorize.add_argument("--run-id", required=True)
    return parser


def batch_status(runtime: Path) -> dict[str, Any]:
    runtime = Path(runtime)
    load_campaign(runtime)
    counts = {slot: failed_attempt_count(runtime, slot) for slot in SESSION_ORDER}
    total = sum(counts.values())
    return {
        "study_id": STUDY_ID,
        "batch_invalid_attempt_count": total,
        "batch_invalid_attempt_pause": BATCH_INVALID_ATTEMPT_PAUSE,
        "batch_paused": total >= BATCH_INVALID_ATTEMPT_PAUSE,
        "per_slot_invalid_attempts": counts,
        "max_attempts_per_slot": MAX_ATTEMPTS_PER_SLOT,
    }


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    runtime = args.runtime.resolve()
    if args.command == "prepare-campaign":
        result: Any = prepare_campaign(runtime)
    elif args.command == "check-configs":
        result = check_scenario_configs()
    elif args.command == "record-run-gates":
        result = record_run_gates(
            runtime,
            qual3_pass_attributed=args.qual3_pass_attributed,
            dr_round3_passed=args.dr_round3_passed,
            clock_smoke_passed=args.clock_smoke_passed,
            attribution=args.attribution,
        )
    elif args.command == "install-config":
        result = install_config(runtime, args.run_id)
    elif args.command == "freeze-scouting":
        result = freeze_scouting(runtime, confirmed=args.confirmed)
    elif args.command == "prepare-session":
        identity = slot_identity(args.run_id)
        result = prepare_session(
            runtime,
            build_session(
                run_id=args.run_id,
                init_frame_id=args.init_frame,
                init_image_sha256=args.init_image_sha256,
                hold_route_s_m=phase_route_s_m(runtime, int(identity["phase"])),
                tracker_identity=nanotrack_identity(),
            ),
        )
    elif args.command == "preview-calibration":
        result = preview_calibration(runtime, args.run_id, args.box)
    elif args.command == "freeze-calibration":
        result = freeze_calibration(
            runtime, args.run_id, confirmed=args.confirmed
        )
    elif args.command == "launch":
        completed = launch_tracker(
            python_executable=args.python,
            runtime=runtime,
            init_box=args.box,
            ground_plane_y_m=args.ground_plane_y_m,
            reanchor_config=args.reanchor_config,
        )
        raise SystemExit(completed.returncode)
    elif args.command == "release":
        result = coordinate_release(
            runtime,
            confirmed=args.confirmed,
            timeout_s=args.timeout_s,
            poll_interval_s=args.poll_interval_s,
        )
    elif args.command == "finalize":
        result = finalize_attempt(runtime, args.run_id)
    elif args.command == "archive-failed-attempt":
        result = archive_failed_attempt(runtime, args.run_id, args.reason)
    elif args.command == "probe":
        result = build_probe(runtime)
    elif args.command == "select-d2":
        result = select_d2(
            runtime,
            speed_mps=args.speed_mps,
            r20_config=args.r20_config,
            r5_config=args.r5_config,
            difficulty_audit=args.difficulty_audit,
            authorization_0b=args.authorization_0b,
        )
    elif args.command == "decision":
        result = build_decision(runtime)
    elif args.command == "validate-decision":
        result = validate_decision(runtime)
    elif args.command == "batch-status":
        result = batch_status(runtime)
    elif args.command == "authorize":
        result = authorize_session(runtime, args.run_id)
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
