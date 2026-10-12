"""P1-M2-RATE-003 batch 1: shared-clock v3 session/release protocol.

Active RATE-003 path.  The archived RATE-002 v2 path in
``controller/rate2_protocol.py`` stays frozen; this module mirrors its
structure but pins every cross-process monotonic value to
``system-stopwatch/v1`` (``CLOCK_ID``) and routes on the schema/study
declared by the session file, never on a global constant.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
import time
from typing import Any, Mapping

from .rate2_protocol import (
    IDENTITY_KEYS,
    SHA256_KEYS,
    Rate2ProtocolError,
    _finite,
    _integer,
    _sha256,
    _string,
    atomic_json,
    canonical_json_bytes,
    create_once_bytes,
    create_once_json,
    identity_hashes,
    latest_frame_id,
    read_json_bytes,
    sha256_bytes,
    sha256_file,
    validate_identity,
)
from .sensor_protocol import SENSOR_FRAME_SCHEMA_V3, SYSTEM_MONOTONIC_CLOCK_ID


STUDY_ID = "P1-M2-RATE-003-B1"
CLOCK_SMOKE_STUDY_ID = "P1-M2-RATE-003-CLOCKSMOKE"
CLOCK_SMOKE_RUN_ID = "rs3-clock-smoke"
TRACKER_ID = "nanotrack-v2"
SESSION_SCHEMA = "p1-rate3-session/v1"
READY_SCHEMA = "p1-rate3-tracker-ready/v1"
RELEASE_COMMAND_SCHEMA = "p1-rate3-release-command/v1"
RELEASE_ACK_SCHEMA = "p1-rate3-release-ack/v1"
ABORT_COMMAND_SCHEMA = "p1-rate3-abort-command/v1"
PROVENANCE_SCHEMA = "p1-rate3-release-provenance/v1"
SENSOR_SCHEMA = SENSOR_FRAME_SCHEMA_V3
CLOCK_ID = SYSTEM_MONOTONIC_CLOCK_ID
HEARTBEAT_INTERVAL_S = 1.0
HEARTBEAT_MAX_AGE_S = 2.0
PLANNED_DURATION_S = 150.0
# 非测量操作值：沿用 RATE-002 30 s pilot 先例，clock-smoke 不产出测量数据。
CLOCK_SMOKE_PLANNED_DURATION_S = 30.0

B1_PROBE_RUN_ID = "rs3-probe-d2"
# BC-DRB-4 (acceptance round 4) replaces the two `rs3-d{1|2}-calib` slots
# with six per-phase HOLD calibration slots, so that every
# (difficulty, phase) pair owns exactly one frozen initialisation product.
B1_CALIBRATION_RUN_IDS = tuple(
    f"rs3-d{difficulty}-p{phase}-calib"
    for difficulty in (1, 2)
    for phase in (1, 2, 3)
)
B1_PROBE_AND_CALIB_RUN_IDS = (B1_PROBE_RUN_ID, *B1_CALIBRATION_RUN_IDS)
B1_FORMAL_RUN_IDS = tuple(
    f"rs3-d{difficulty}-p{phase}-r{rate}"
    for difficulty in (1, 2)
    for phase in (1, 2, 3)
    for rate in (5, 20)
)
B1_RUN_IDS = frozenset((*B1_PROBE_AND_CALIB_RUN_IDS, *B1_FORMAL_RUN_IDS))


def _invalid_clock(message: str) -> Rate2ProtocolError:
    return Rate2ProtocolError(f"INVALID_CLOCK_IDENTITY: {message}")


def expected_scenario(run_id: str, study_id: str) -> str:
    if study_id == CLOCK_SMOKE_STUDY_ID:
        if run_id != CLOCK_SMOKE_RUN_ID:
            raise Rate2ProtocolError(
                f"clock-smoke study requires run_id {CLOCK_SMOKE_RUN_ID!r}"
            )
        return "p1-scene-004"
    if study_id == STUDY_ID:
        if run_id not in B1_RUN_IDS:
            raise Rate2ProtocolError(
                f"unsupported RATE-003 run_id: {run_id!r}"
            )
        return "p1-scene-004-d2" if "d2" in run_id else "p1-scene-004"
    raise Rate2ProtocolError(f"unsupported RATE-003 study_id: {study_id!r}")


def planned_duration_for(study_id: str) -> float:
    if study_id == CLOCK_SMOKE_STUDY_ID:
        return CLOCK_SMOKE_PLANNED_DURATION_S
    if study_id == STUDY_ID:
        return PLANNED_DURATION_S
    raise Rate2ProtocolError(f"unsupported RATE-003 study_id: {study_id!r}")


def validate_session(value: Mapping[str, Any]) -> dict[str, Any]:
    session = dict(value)
    if session.get("schema_version") != SESSION_SCHEMA:
        raise Rate2ProtocolError("invalid RATE-003 session schema")
    study_id = session.get("study_id")
    if study_id not in {STUDY_ID, CLOCK_SMOKE_STUDY_ID}:
        raise Rate2ProtocolError("invalid RATE-003 study_id")
    if session.get("tracker_id") != TRACKER_ID:
        raise Rate2ProtocolError("invalid RATE-003 tracker_id")
    run_id = _string(session.get("run_id"), "session.run_id")
    scenario_id = _string(session.get("scenario_id"), "session.scenario_id")
    if scenario_id != expected_scenario(run_id, str(study_id)):
        raise Rate2ProtocolError("RATE-003 run/scenario identity mismatch")
    for key in SHA256_KEYS:
        _sha256(session.get(key), f"session.{key}")
    _integer(session.get("init_frame_id"), "session.init_frame_id")
    _finite(session.get("hold_route_s_m"), "session.hold_route_s_m")
    if float(session["hold_route_s_m"]) < 0.0:
        raise Rate2ProtocolError("session.hold_route_s_m must be non-negative")
    if session.get("minimum_ready_seq") != 20:
        raise Rate2ProtocolError("session.minimum_ready_seq must equal 20")
    if session.get("minimum_processed_frames") != 20:
        raise Rate2ProtocolError("session.minimum_processed_frames must equal 20")
    planned = _finite(
        session.get("planned_duration_s"),
        "session.planned_duration_s",
    )
    expected_planned = planned_duration_for(str(study_id))
    if abs(planned - expected_planned) > 1e-9:
        raise Rate2ProtocolError(
            f"session.planned_duration_s must equal {expected_planned}"
        )
    if session.get("sensor_frame_schema") != SENSOR_SCHEMA:
        raise Rate2ProtocolError("session.sensor_frame_schema must be v3")
    if session.get("capture_monotonic_clock_id") != CLOCK_ID:
        raise _invalid_clock(
            "session.capture_monotonic_clock_id must be "
            f"{CLOCK_ID!r}; received {session.get('capture_monotonic_clock_id')!r}"
        )
    return session


def load_session(runtime: Path) -> tuple[bytes, dict[str, Any]]:
    payload, value = read_json_bytes(Path(runtime) / "rate_study_session.json")
    return payload, validate_session(value)


def validate_ready(
    value: Mapping[str, Any],
    session: Mapping[str, Any],
    *,
    now_monotonic_s: float | None = None,
    require_minimum: bool = True,
) -> dict[str, Any]:
    ready = dict(value)
    if ready.get("schema_version") != READY_SCHEMA:
        raise Rate2ProtocolError("invalid tracker-ready schema")
    validate_identity(ready, session, "ready")
    if ready.get("state") != "TRACKING":
        raise Rate2ProtocolError("tracker-ready state is not TRACKING")
    seq = _integer(ready.get("seq"), "ready.seq", 1)
    processed = _integer(
        ready.get("processed_frame_count"),
        "ready.processed_frame_count",
        1,
    )
    _integer(
        ready.get("last_processed_frame_id"),
        "ready.last_processed_frame_id",
    )
    published = _finite(
        ready.get("publisher_monotonic_s"),
        "ready.publisher_monotonic_s",
    )
    if published < 0.0:
        raise Rate2ProtocolError("ready.publisher_monotonic_s must be non-negative")
    if ready.get("publisher_clock_id") != CLOCK_ID:
        raise _invalid_clock(
            "tracker-ready publisher_clock_id must be "
            f"{CLOCK_ID!r}; received {ready.get('publisher_clock_id')!r}"
        )
    heartbeat_interval_s = _finite(
        ready.get("heartbeat_interval_s"),
        "ready.heartbeat_interval_s",
    )
    if heartbeat_interval_s <= 0.0 or heartbeat_interval_s > HEARTBEAT_INTERVAL_S:
        raise Rate2ProtocolError("ready heartbeat interval exceeds 1 s")
    if require_minimum:
        if seq < int(session["minimum_ready_seq"]):
            raise Rate2ProtocolError("tracker-ready seq is below warm-up minimum")
        if processed < int(session["minimum_processed_frames"]):
            raise Rate2ProtocolError(
                "tracker-ready processed count is below warm-up minimum"
            )
    if now_monotonic_s is not None:
        now = _finite(now_monotonic_s, "now_monotonic_s")
        age = now - published
        if age < 0.0:
            raise Rate2ProtocolError("tracker-ready monotonic timestamp is in the future")
        if age > HEARTBEAT_MAX_AGE_S:
            raise Rate2ProtocolError("tracker-ready heartbeat is stale")
    return ready


def read_consistent_ready(
    runtime: Path,
    session: Mapping[str, Any],
    *,
    previous_seq: int,
    now_monotonic_s: float | None = None,
) -> tuple[bytes, dict[str, Any], int]:
    current_frame_id = latest_frame_id(runtime)
    ready_bytes, ready_value = read_json_bytes(Path(runtime) / "tracker_ready.json")
    ready = validate_ready(
        ready_value,
        session,
        now_monotonic_s=(
            time.monotonic() if now_monotonic_s is None else now_monotonic_s
        ),
    )
    if int(ready["seq"]) <= previous_seq:
        raise Rate2ProtocolError("tracker-ready seq did not advance")
    backlog = current_frame_id - int(ready["last_processed_frame_id"])
    if backlog < 0 or backlog > 1:
        raise Rate2ProtocolError("tracker-ready backlog is outside [0, 1]")
    return ready_bytes, ready, current_frame_id


def build_release_command(
    session: Mapping[str, Any],
    ready_bytes: bytes,
    *,
    command_id: str,
) -> bytes:
    ready_value = json.loads(ready_bytes)
    if not isinstance(ready_value, dict):
        raise Rate2ProtocolError("ready bytes must contain an object")
    validate_ready(ready_value, session)
    command = {
        "schema_version": RELEASE_COMMAND_SCHEMA,
        "channel": "experiment_control",
        "command_type": "release",
        "command_id": _string(command_id, "command_id"),
        **{key: session[key] for key in IDENTITY_KEYS},
        "release_clock_id": CLOCK_ID,
        "ready_json_base64": base64.b64encode(ready_bytes).decode("ascii"),
        "ready_sha256": sha256_bytes(ready_bytes),
    }
    return canonical_json_bytes(command)


def validate_release_bundle(
    command_bytes: bytes,
    ack_bytes: bytes,
    session: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        command = json.loads(command_bytes)
        ack = json.loads(ack_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exception:
        raise Rate2ProtocolError("release command/ack is invalid JSON") from exception
    if not isinstance(command, dict) or not isinstance(ack, dict):
        raise Rate2ProtocolError("release command/ack must be objects")
    if command.get("schema_version") != RELEASE_COMMAND_SCHEMA:
        raise Rate2ProtocolError("invalid release command schema")
    if command.get("channel") != "experiment_control" or command.get("command_type") != "release":
        raise Rate2ProtocolError("invalid release command envelope")
    validate_identity(command, session, "command")
    if command.get("release_clock_id") != CLOCK_ID:
        raise _invalid_clock(
            "release command release_clock_id must be "
            f"{CLOCK_ID!r}; received {command.get('release_clock_id')!r}"
        )
    if ack.get("schema_version") != RELEASE_ACK_SCHEMA:
        raise Rate2ProtocolError("invalid release ack schema")
    validate_identity(ack, session, "ack")
    if ack.get("release_clock_id") != CLOCK_ID:
        raise _invalid_clock(
            "release ack release_clock_id must be "
            f"{CLOCK_ID!r}; received {ack.get('release_clock_id')!r}"
        )
    if ack.get("command_id") != command.get("command_id"):
        raise Rate2ProtocolError("release command_id mismatch")
    if ack.get("release_command_sha256") != sha256_bytes(command_bytes):
        raise Rate2ProtocolError("release command hash mismatch")
    ready_sha256 = _sha256(command.get("ready_sha256"), "command.ready_sha256")
    if ack.get("ready_sha256") != ready_sha256:
        raise Rate2ProtocolError("release ready hash mismatch")
    try:
        ready_bytes = base64.b64decode(
            _string(command.get("ready_json_base64"), "command.ready_json_base64"),
            validate=True,
        )
    except (ValueError, base64.binascii.Error) as exception:
        raise Rate2ProtocolError("release ready payload is not valid base64") from exception
    if sha256_bytes(ready_bytes) != ready_sha256:
        raise Rate2ProtocolError("embedded ready bytes/hash mismatch")
    ready_value = json.loads(ready_bytes)
    if not isinstance(ready_value, dict):
        raise Rate2ProtocolError("embedded ready payload must be an object")
    ready = validate_ready(ready_value, session)
    expected_pairs = {
        "ready_seq": ready["seq"],
        "processed_frame_count": ready["processed_frame_count"],
        "last_processed_frame_id": ready["last_processed_frame_id"],
    }
    for key, expected in expected_pairs.items():
        if ack.get(key) != expected:
            raise Rate2ProtocolError(f"ack.{key} does not match ready")
    current_frame_id = _integer(ack.get("current_frame_id"), "ack.current_frame_id")
    release_frame_id = _integer(ack.get("release_frame_id"), "ack.release_frame_id")
    if current_frame_id != release_frame_id:
        raise Rate2ProtocolError("ack release/current frame mismatch")
    backlog = current_frame_id - int(ready["last_processed_frame_id"])
    if backlog < 0 or backlog > 1 or ack.get("accepted_backlog_frames") != backlog:
        raise Rate2ProtocolError("ack backlog is invalid")
    release_unix_s = _finite(ack.get("release_unix_s"), "ack.release_unix_s")
    release_monotonic_s = _finite(
        ack.get("release_monotonic_s"),
        "ack.release_monotonic_s",
    )
    release_simulation_s = _finite(
        ack.get("release_simulation_s"),
        "ack.release_simulation_s",
    )
    if min(release_unix_s, release_monotonic_s, release_simulation_s) < 0.0:
        raise Rate2ProtocolError("release timestamps must be non-negative")
    return ack


def archive_release_provenance(
    runtime: Path,
    run_directory: Path,
    session: Mapping[str, Any],
) -> dict[str, Any]:
    runtime = Path(runtime)
    run_directory = Path(run_directory)
    command_bytes = (runtime / "release_command.accepted.json").read_bytes()
    ack_bytes = (runtime / "release_ack.json").read_bytes()
    ack = validate_release_bundle(command_bytes, ack_bytes, session)
    manifest_path = run_directory / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    create_once_bytes(run_directory / "release-command.json", command_bytes)
    create_once_bytes(run_directory / "release-ack.json", ack_bytes)
    provenance = {
        "schema_version": PROVENANCE_SCHEMA,
        "study_id": session["study_id"],
        "run_id": session["run_id"],
        "scenario_id": session["scenario_id"],
        "command_id": ack["command_id"],
        "tracker_id": session["tracker_id"],
        "tracker_identity_sha256": session["tracker_identity_sha256"],
        "model_identity_sha256": session["model_identity_sha256"],
        "init_frame_id": session["init_frame_id"],
        "init_image_sha256": session["init_image_sha256"],
        "manifest_sha256": sha256_file(manifest_path),
        "release_command_sha256": sha256_bytes(command_bytes),
        "ready_sha256": ack["ready_sha256"],
        "release_ack_sha256": sha256_bytes(ack_bytes),
        "release_frame_id": ack["release_frame_id"],
        "release_unix_s": ack["release_unix_s"],
        "release_monotonic_s": ack["release_monotonic_s"],
        "release_simulation_s": ack["release_simulation_s"],
        "release_clock_id": ack["release_clock_id"],
    }
    create_once_json(run_directory / "release_provenance.json", provenance)
    return provenance


def validate_provenance(
    run_directory: Path,
    *,
    session: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    run_directory = Path(run_directory)
    _, provenance = read_json_bytes(run_directory / "release_provenance.json")
    if provenance.get("schema_version") != PROVENANCE_SCHEMA:
        raise Rate2ProtocolError("invalid release provenance schema")
    if session is not None:
        validate_identity(provenance, session, "provenance")
    manifest_path = run_directory / "manifest.json"
    command_path = run_directory / "release-command.json"
    ack_path = run_directory / "release-ack.json"
    command_bytes = command_path.read_bytes()
    ack_bytes = ack_path.read_bytes()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise Rate2ProtocolError("run manifest must be an object")
    rate3 = manifest.get("rate3")
    if not isinstance(rate3, Mapping):
        raise Rate2ProtocolError("run manifest is missing rate3 identity")
    effective_session = dict(session) if session is not None else {
        key: rate3.get(key, manifest.get(key))
        for key in IDENTITY_KEYS
    }
    effective_session = validate_session(
        {
            "schema_version": SESSION_SCHEMA,
            **effective_session,
            "hold_route_s_m": rate3.get("hold_route_s_m"),
            "minimum_ready_seq": 20,
            "minimum_processed_frames": 20,
            "planned_duration_s": rate3.get("planned_duration_s"),
            "sensor_frame_schema": rate3.get("sensor_frame_schema"),
            "capture_monotonic_clock_id": rate3.get(
                "capture_monotonic_clock_id"
            ),
        }
    )
    validate_identity(provenance, effective_session, "provenance")
    ack = validate_release_bundle(command_bytes, ack_bytes, effective_session)
    checks = {
        "manifest_sha256": sha256_file(manifest_path),
        "release_command_sha256": sha256_bytes(command_bytes),
        "ready_sha256": ack["ready_sha256"],
        "release_ack_sha256": sha256_bytes(ack_bytes),
        "command_id": ack["command_id"],
        "release_frame_id": ack["release_frame_id"],
        "release_unix_s": ack["release_unix_s"],
        "release_monotonic_s": ack["release_monotonic_s"],
        "release_simulation_s": ack["release_simulation_s"],
        "release_clock_id": ack["release_clock_id"],
    }
    for key, expected in checks.items():
        if provenance.get(key) != expected:
            raise Rate2ProtocolError(f"release provenance {key} mismatch")
    return provenance


class Rate3TrackerLifecycle:
    """RATE-003 tracker lifecycle; same interface as Rate2TrackerLifecycle.

    Every cross-process monotonic value is pinned to ``CLOCK_ID``
    (``system-stopwatch/v1``).  ``requires_wall_completion`` tells the
    track loop that the run only completes when both the simulation and
    the shared-host monotonic wall durations reach the planned duration.
    """

    requires_wall_completion = True

    def __init__(
        self,
        runtime: Path,
        session: Mapping[str, Any],
        tracker_identity: Mapping[str, Any],
        *,
        init_frame_id: int,
        init_image_sha256: str,
        scenario_id: str,
        run_id: str,
        monotonic: Any = time.monotonic,
        monotonic_clock_id: str | None = None,
    ):
        if monotonic is time.monotonic:
            declared_clock_id = CLOCK_ID
        else:
            if monotonic_clock_id != CLOCK_ID:
                raise ValueError(
                    "non-default monotonic injection must explicitly declare "
                    f"monotonic_clock_id={CLOCK_ID!r}"
                )
            declared_clock_id = monotonic_clock_id
        self.monotonic_clock_id = declared_clock_id
        self.runtime = Path(runtime)
        self.session = validate_session(session)
        tracker_hash, model_hash = identity_hashes(tracker_identity)
        checks = {
            "run_id": run_id,
            "scenario_id": scenario_id,
            "init_frame_id": init_frame_id,
            "init_image_sha256": init_image_sha256,
            "tracker_identity_sha256": tracker_hash,
            "model_identity_sha256": model_hash,
        }
        for key, expected in checks.items():
            if self.session.get(key) != expected:
                raise Rate2ProtocolError(f"tracker/session {key} mismatch")
        self.monotonic = monotonic
        self.seq = 0
        self.processed_frame_count = 0
        self.phase = "hold"
        self.release_ack: dict[str, Any] | None = None

    def publish_ready(self, frame_id: int, state: str) -> Path:
        self.seq += 1
        self.processed_frame_count += 1
        ready = {
            "schema_version": READY_SCHEMA,
            "state": state,
            **{key: self.session[key] for key in IDENTITY_KEYS},
            "last_processed_frame_id": _integer(frame_id, "frame_id"),
            "processed_frame_count": self.processed_frame_count,
            "seq": self.seq,
            "publisher_monotonic_s": _finite(
                self.monotonic(),
                "publisher_monotonic_s",
            ),
            "publisher_clock_id": CLOCK_ID,
            "heartbeat_interval_s": HEARTBEAT_INTERVAL_S,
        }
        return atomic_json(self.runtime / "tracker_ready.json", ready)

    def poll_release_ack(self) -> dict[str, Any] | None:
        if self.release_ack is not None:
            return self.release_ack
        ack_path = self.runtime / "release_ack.json"
        command_path = self.runtime / "release_command.accepted.json"
        if not ack_path.is_file() or not command_path.is_file():
            return None
        ack = validate_release_bundle(
            command_path.read_bytes(),
            ack_path.read_bytes(),
            self.session,
        )
        self.release_ack = ack
        self.phase = "measurement"
        return ack

    def record_fields(self, metadata: Mapping[str, Any]) -> dict[str, Any]:
        capture_monotonic_s = _finite(
            metadata.get("capture_monotonic_s"),
            "capture_monotonic_s",
        )
        frame_phase = self.frame_phase(metadata)
        result: dict[str, Any] = {
            "phase": frame_phase,
            "capture_monotonic_s": capture_monotonic_s,
            "capture_monotonic_clock_id": metadata.get(
                "capture_monotonic_clock_id"
            ),
            "measurement_elapsed_s": None,
            "measurement_wall_elapsed_s": None,
        }
        if self.release_ack is not None and frame_phase == "measurement":
            release_monotonic_s = float(self.release_ack["release_monotonic_s"])
            release_simulation_s = float(self.release_ack["release_simulation_s"])
            simulation_time_s = _finite(
                metadata.get("simulation_time_s"),
                "simulation_time_s",
            )
            elapsed = simulation_time_s - release_simulation_s
            if elapsed < 0.0:
                raise Rate2ProtocolError(
                    "post-release frame simulation time precedes release"
                )
            wall_elapsed = capture_monotonic_s - release_monotonic_s
            if wall_elapsed < 0.0:
                raise Rate2ProtocolError(
                    "post-release frame monotonic capture precedes release"
                )
            result["measurement_elapsed_s"] = elapsed
            result["measurement_wall_elapsed_s"] = wall_elapsed
        return result

    def frame_phase(self, metadata: Mapping[str, Any]) -> str:
        if self.release_ack is None:
            return "hold"
        if metadata.get("capture_monotonic_clock_id") != CLOCK_ID:
            raise _invalid_clock(
                "frame capture_monotonic_clock_id must be "
                f"{CLOCK_ID!r}; received "
                f"{metadata.get('capture_monotonic_clock_id')!r}"
            )
        if self.release_ack.get("release_clock_id") != CLOCK_ID:
            raise _invalid_clock(
                "release ack release_clock_id must be "
                f"{CLOCK_ID!r}; received "
                f"{self.release_ack.get('release_clock_id')!r}"
            )
        capture_monotonic_s = _finite(
            metadata.get("capture_monotonic_s"),
            "capture_monotonic_s",
        )
        return (
            "measurement"
            if capture_monotonic_s >= float(self.release_ack["release_monotonic_s"])
            else "hold"
        )
