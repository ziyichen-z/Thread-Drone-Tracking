from __future__ import annotations

import json
import math
from pathlib import Path
import re
import time
from typing import Any, Callable, Mapping
import uuid

from .rate2_protocol import (
    Rate2ProtocolError,
    create_once_json,
    read_json_bytes,
    sha256_bytes,
)


READY_SCHEMA = "p1-detect-qualification-ready/v1"
RELEASE_COMMAND_SCHEMA = "p1-detect-qualification-release-command/v1"
RELEASE_ACK_SCHEMA = "p1-detect-qualification-release-ack/v1"
ACTIVE_SCHEMA = "p1-detect-qualification-active/v1"
PROVENANCE_SCHEMA = "p1-detect-qualification-release-provenance/v1"
PROTOCOL_ID = "host-monotonic-first-live-frame/v1"
MANIFEST_KEY = "qualification_release"
READY_FILE = "qualification-release-ready.json"
COMMAND_FILE = "qualification-release-command.json"
ACK_FILE = "qualification-release-ack.json"
ACTIVE_FILE = "qualification-release-active.json"
ACTIVE_POINTER_FILE = "p1_detect_qualification_release.json"
PROVENANCE_FILE = "qualification-release-provenance.json"
QUALIFICATION_RUN_ID = re.compile(r"^p1-detect-001-qual-[1-9][0-9]*$")


class QualificationProtocolError(ValueError):
    pass


def manifest_identity() -> dict[str, str]:
    return {
        "protocol_id": PROTOCOL_ID,
        "ready_schema": READY_SCHEMA,
        "release_command_schema": RELEASE_COMMAND_SCHEMA,
        "release_ack_schema": RELEASE_ACK_SCHEMA,
        "active_schema": ACTIVE_SCHEMA,
        "provenance_schema": PROVENANCE_SCHEMA,
    }


def _read_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    try:
        return read_json_bytes(path)
    except (OSError, Rate2ProtocolError) as exception:
        raise QualificationProtocolError(str(exception)) from exception


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise QualificationProtocolError(f"{label} must be finite")
    try:
        result = float(value)
    except (TypeError, ValueError) as exception:
        raise QualificationProtocolError(f"{label} must be finite") from exception
    if not math.isfinite(result) or result < 0.0:
        raise QualificationProtocolError(
            f"{label} must be finite and non-negative"
        )
    return result


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise QualificationProtocolError(
            f"{label} must be a non-negative integer"
        )
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise QualificationProtocolError(f"{label} must be a non-empty string")
    return value


def _sha256(value: Any, label: str) -> str:
    result = _string(value, label)
    if not re.fullmatch(r"[0-9a-f]{64}", result):
        raise QualificationProtocolError(
            f"{label} must be a lowercase SHA-256"
        )
    return result


def _run_directory(runtime: Path, run_id: str) -> Path:
    if not QUALIFICATION_RUN_ID.fullmatch(run_id):
        raise QualificationProtocolError(
            "qualification run_id must match p1-detect-001-qual-N"
        )
    return Path(runtime) / "runs" / run_id


def _manifest(run_directory: Path) -> tuple[bytes, dict[str, Any]]:
    payload, value = _read_json(run_directory / "manifest.json")
    run_id = _string(value.get("run_id"), "manifest.run_id")
    if run_directory.name != run_id:
        raise QualificationProtocolError("manifest/run directory identity mismatch")
    if value.get(MANIFEST_KEY) != manifest_identity():
        raise QualificationProtocolError(
            "run manifest does not enable the exact qualification release protocol"
        )
    if value.get("scenario_id") != "p1-scene-004":
        raise QualificationProtocolError(
            "qualification release requires scenario p1-scene-004"
        )
    return payload, value


def _validate_ready(
    value: Mapping[str, Any],
    *,
    run_directory: Path,
    manifest_sha256: str,
) -> dict[str, Any]:
    if value.get("schema_version") != READY_SCHEMA:
        raise QualificationProtocolError("invalid qualification ready schema")
    if value.get("protocol_id") != PROTOCOL_ID:
        raise QualificationProtocolError("invalid qualification ready protocol")
    if value.get("run_id") != run_directory.name:
        raise QualificationProtocolError("qualification ready run_id mismatch")
    if value.get("scenario_id") != "p1-scene-004":
        raise QualificationProtocolError("qualification ready scenario mismatch")
    if value.get("manifest_sha256") != manifest_sha256:
        raise QualificationProtocolError("qualification ready manifest hash mismatch")
    _integer(value.get("init_frame_id"), "ready.init_frame_id")
    _finite(value.get("init_simulation_s"), "ready.init_simulation_s")
    _finite(value.get("init_capture_unix_s"), "ready.init_capture_unix_s")
    _finite(value.get("init_capture_monotonic_s"), "ready.init_capture_monotonic_s")
    _finite(value.get("ready_unix_s"), "ready.ready_unix_s")
    _finite(value.get("ready_monotonic_s"), "ready.ready_monotonic_s")
    return dict(value)


def _validate_command(
    value: Mapping[str, Any],
    *,
    run_directory: Path,
    manifest_sha256: str,
    ready_sha256: str,
    ready: Mapping[str, Any],
) -> dict[str, Any]:
    if value.get("schema_version") != RELEASE_COMMAND_SCHEMA:
        raise QualificationProtocolError(
            "invalid qualification release command schema"
        )
    if value.get("protocol_id") != PROTOCOL_ID:
        raise QualificationProtocolError(
            "invalid qualification release command protocol"
        )
    if value.get("run_id") != run_directory.name:
        raise QualificationProtocolError(
            "qualification release command run_id mismatch"
        )
    if value.get("scenario_id") != "p1-scene-004":
        raise QualificationProtocolError(
            "qualification release command scenario mismatch"
        )
    _string(value.get("command_id"), "command.command_id")
    if value.get("manifest_sha256") != manifest_sha256:
        raise QualificationProtocolError(
            "qualification release command manifest hash mismatch"
        )
    if value.get("ready_sha256") != ready_sha256:
        raise QualificationProtocolError(
            "qualification release command ready hash mismatch"
        )
    issued_unix_s = _finite(value.get("issued_unix_s"), "command.issued_unix_s")
    not_before_monotonic_s = _finite(
        value.get("not_before_capture_monotonic_s"),
        "command.not_before_capture_monotonic_s",
    )
    if issued_unix_s <= float(ready["ready_unix_s"]):
        raise QualificationProtocolError(
            "qualification release command does not follow ready wall time"
        )
    if not_before_monotonic_s <= float(ready["ready_monotonic_s"]):
        raise QualificationProtocolError(
            "qualification release command does not follow ready monotonic time"
        )
    return dict(value)


def _active_value(
    *,
    run_directory: Path,
    command: Mapping[str, Any],
    manifest_sha256: str,
    ready_sha256: str,
    command_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": ACTIVE_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "run_id": run_directory.name,
        "scenario_id": "p1-scene-004",
        "command_id": command["command_id"],
        "manifest_sha256": manifest_sha256,
        "ready_sha256": ready_sha256,
        "release_command_sha256": command_sha256,
        "command_relative_path": (
            f"runs/{run_directory.name}/{COMMAND_FILE}"
        ),
        "not_before_capture_monotonic_s": float(
            command["not_before_capture_monotonic_s"]
        ),
    }


def _validate_active(
    value: Mapping[str, Any],
    *,
    run_directory: Path,
    command: Mapping[str, Any],
    manifest_sha256: str,
    ready_sha256: str,
    command_sha256: str,
) -> dict[str, Any]:
    expected = _active_value(
        run_directory=run_directory,
        command=command,
        manifest_sha256=manifest_sha256,
        ready_sha256=ready_sha256,
        command_sha256=command_sha256,
    )
    if dict(value) != expected:
        raise QualificationProtocolError(
            "qualification active marker content mismatch"
        )
    return dict(value)


def _publish_active(
    runtime: Path,
    run_directory: Path,
    command: Mapping[str, Any],
    *,
    manifest_sha256: str,
    ready_sha256: str,
    command_sha256: str,
) -> dict[str, Any]:
    active = _active_value(
        run_directory=run_directory,
        command=command,
        manifest_sha256=manifest_sha256,
        ready_sha256=ready_sha256,
        command_sha256=command_sha256,
    )
    create_once_json(run_directory / ACTIVE_FILE, active)
    try:
        create_once_json(Path(runtime) / ACTIVE_POINTER_FILE, active)
    except FileExistsError as exception:
        raise QualificationProtocolError(
            "another qualification active marker occupies the runtime slot"
        ) from exception
    return active


def request_release(
    runtime: Path,
    run_id: str,
    *,
    unix_time: Callable[[], float] = time.time,
    monotonic: Callable[[], float] = time.monotonic,
    command_id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
) -> tuple[Path, dict[str, Any]]:
    run_directory = _run_directory(runtime, run_id)
    manifest_bytes, manifest = _manifest(run_directory)
    manifest_sha256 = sha256_bytes(manifest_bytes)
    ready_bytes, ready_value = _read_json(run_directory / READY_FILE)
    _validate_ready(
        ready_value,
        run_directory=run_directory,
        manifest_sha256=manifest_sha256,
    )
    ready_sha256 = sha256_bytes(ready_bytes)
    command_path = run_directory / COMMAND_FILE
    if command_path.is_file():
        command_bytes, existing = _read_json(command_path)
        validated = _validate_command(
            existing,
            run_directory=run_directory,
            manifest_sha256=manifest_sha256,
            ready_sha256=ready_sha256,
            ready=ready_value,
        )
        if (run_directory / ACK_FILE).exists() or (
            run_directory / PROVENANCE_FILE
        ).exists():
            raise QualificationProtocolError(
                "qualification release was already acknowledged"
            )
        _publish_active(
            runtime,
            run_directory,
            validated,
            manifest_sha256=manifest_sha256,
            ready_sha256=ready_sha256,
            command_sha256=sha256_bytes(command_bytes),
        )
        return command_path, validated
    if (run_directory / ACK_FILE).exists() or (
        run_directory / PROVENANCE_FILE
    ).exists():
        raise QualificationProtocolError(
            "qualification release ack/provenance exists without its command"
        )
    command = {
        "schema_version": RELEASE_COMMAND_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "run_id": run_directory.name,
        "scenario_id": manifest["scenario_id"],
        "command_id": _string(command_id_factory(), "command_id"),
        "manifest_sha256": manifest_sha256,
        "ready_sha256": ready_sha256,
        "issued_unix_s": _finite(unix_time(), "issued_unix_s"),
        "not_before_capture_monotonic_s": _finite(
            monotonic(),
            "not_before_capture_monotonic_s",
        ),
    }
    _validate_command(
        command,
        run_directory=run_directory,
        manifest_sha256=manifest_sha256,
        ready_sha256=ready_sha256,
        ready=ready_value,
    )
    create_once_json(command_path, command)
    command_bytes = command_path.read_bytes()
    _publish_active(
        runtime,
        run_directory,
        command,
        manifest_sha256=manifest_sha256,
        ready_sha256=ready_sha256,
        command_sha256=sha256_bytes(command_bytes),
    )
    return command_path, command


def validate_provenance(run_directory: Path) -> dict[str, Any]:
    run_directory = Path(run_directory)
    manifest_bytes, _ = _manifest(run_directory)
    ready_bytes, ready = _read_json(run_directory / READY_FILE)
    command_bytes, command = _read_json(run_directory / COMMAND_FILE)
    active_bytes, active = _read_json(run_directory / ACTIVE_FILE)
    ack_bytes, ack = _read_json(run_directory / ACK_FILE)
    _, provenance = _read_json(run_directory / PROVENANCE_FILE)
    manifest_sha256 = sha256_bytes(manifest_bytes)
    ready_sha256 = sha256_bytes(ready_bytes)
    command_sha256 = sha256_bytes(command_bytes)
    ack_sha256 = sha256_bytes(ack_bytes)
    _validate_ready(
        ready,
        run_directory=run_directory,
        manifest_sha256=manifest_sha256,
    )
    _validate_command(
        command,
        run_directory=run_directory,
        manifest_sha256=manifest_sha256,
        ready_sha256=ready_sha256,
        ready=ready,
    )
    active_sha256 = sha256_bytes(active_bytes)
    _validate_active(
        active,
        run_directory=run_directory,
        command=command,
        manifest_sha256=manifest_sha256,
        ready_sha256=ready_sha256,
        command_sha256=command_sha256,
    )
    if ack.get("schema_version") != RELEASE_ACK_SCHEMA:
        raise QualificationProtocolError("invalid qualification release ack schema")
    if ack.get("protocol_id") != PROTOCOL_ID:
        raise QualificationProtocolError("invalid qualification release ack protocol")
    checks = {
        "run_id": run_directory.name,
        "scenario_id": "p1-scene-004",
        "command_id": command["command_id"],
        "manifest_sha256": manifest_sha256,
        "ready_sha256": ready_sha256,
        "release_command_sha256": command_sha256,
        "active_marker_sha256": active_sha256,
    }
    for key, expected in checks.items():
        if ack.get(key) != expected:
            raise QualificationProtocolError(
                f"qualification release ack {key} mismatch"
            )
    release_frame_id = _integer(ack.get("release_frame_id"), "ack.release_frame_id")
    release_unix_s = _finite(ack.get("release_unix_s"), "ack.release_unix_s")
    release_monotonic_s = _finite(
        ack.get("release_monotonic_s"),
        "ack.release_monotonic_s",
    )
    release_simulation_s = _finite(
        ack.get("release_simulation_s"),
        "ack.release_simulation_s",
    )
    if release_monotonic_s < float(command["not_before_capture_monotonic_s"]):
        raise QualificationProtocolError(
            "qualification release ack precedes command boundary"
        )
    if release_unix_s < float(command["issued_unix_s"]):
        raise QualificationProtocolError(
            "qualification release ack precedes command wall time"
        )
    if release_simulation_s < float(ready["init_simulation_s"]):
        raise QualificationProtocolError(
            "qualification release simulation time precedes initialization"
        )
    if release_frame_id <= int(ready["init_frame_id"]):
        raise QualificationProtocolError(
            "qualification release frame does not follow initialization"
        )
    if release_unix_s < float(ready["init_capture_unix_s"]):
        raise QualificationProtocolError(
            "qualification release wall time precedes initialization"
        )
    if release_monotonic_s < float(ready["init_capture_monotonic_s"]):
        raise QualificationProtocolError(
            "qualification release monotonic time precedes initialization"
        )
    expected_provenance = {
        "schema_version": PROVENANCE_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        **checks,
        "release_ack_sha256": ack_sha256,
        "release_frame_id": release_frame_id,
        "release_unix_s": release_unix_s,
        "release_monotonic_s": release_monotonic_s,
        "release_simulation_s": release_simulation_s,
    }
    if provenance != expected_provenance:
        raise QualificationProtocolError(
            "qualification release provenance content mismatch"
        )
    return dict(provenance)


class QualificationReleaseLifecycle:
    def __init__(
        self,
        runtime: Path,
        run_id: str,
        *,
        scenario_id: str,
        init_frame_id: int,
        unix_time: Callable[[], float] = time.time,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        self.run_directory = _run_directory(runtime, run_id)
        self.runtime = Path(runtime)
        manifest_bytes, manifest = _manifest(self.run_directory)
        if manifest.get("scenario_id") != scenario_id:
            raise QualificationProtocolError(
                "qualification lifecycle scenario mismatch"
            )
        init = manifest.get("init")
        if not isinstance(init, Mapping) or init.get("frame_id") != init_frame_id:
            raise QualificationProtocolError(
                "qualification lifecycle init frame mismatch"
            )
        self.manifest_sha256 = sha256_bytes(manifest_bytes)
        self.run_id = run_id
        self.scenario_id = scenario_id
        self.init_frame_id = init_frame_id
        self.unix_time = unix_time
        self.monotonic = monotonic
        self.command: dict[str, Any] | None = None
        self.release_ack: dict[str, Any] | None = None
        self.phase = "hold"

    def publish_ready(self, metadata: Mapping[str, Any]) -> Path:
        if _integer(metadata.get("frame_id"), "metadata.frame_id") != self.init_frame_id:
            raise QualificationProtocolError(
                "qualification ready frame differs from initialization"
            )
        if metadata.get("scenario_id") != self.scenario_id:
            raise QualificationProtocolError(
                "qualification ready frame scenario mismatch"
            )
        ready = {
            "schema_version": READY_SCHEMA,
            "protocol_id": PROTOCOL_ID,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "manifest_sha256": self.manifest_sha256,
            "init_frame_id": self.init_frame_id,
            "init_simulation_s": _finite(
                metadata.get("simulation_time_s"),
                "metadata.simulation_time_s",
            ),
            "init_capture_unix_s": _finite(
                metadata.get("capture_unix_s"),
                "metadata.capture_unix_s",
            ),
            "init_capture_monotonic_s": _finite(
                metadata.get("capture_monotonic_s"),
                "metadata.capture_monotonic_s",
            ),
            "ready_unix_s": _finite(self.unix_time(), "ready_unix_s"),
            "ready_monotonic_s": _finite(
                self.monotonic(),
                "ready_monotonic_s",
            ),
        }
        path = self.run_directory / READY_FILE
        create_once_json(path, ready)
        return path

    def poll_release_command(self) -> dict[str, Any] | None:
        if self.command is not None:
            return self.command
        command_path = self.run_directory / COMMAND_FILE
        if not command_path.is_file():
            return None
        ready_bytes, ready = _read_json(self.run_directory / READY_FILE)
        _validate_ready(
            ready,
            run_directory=self.run_directory,
            manifest_sha256=self.manifest_sha256,
        )
        command_bytes, command = _read_json(command_path)
        self.command = _validate_command(
            command,
            run_directory=self.run_directory,
            manifest_sha256=self.manifest_sha256,
            ready_sha256=sha256_bytes(ready_bytes),
            ready=ready,
        )
        active_bytes, active = _read_json(
            self.run_directory / ACTIVE_FILE
        )
        _validate_active(
            active,
            run_directory=self.run_directory,
            command=self.command,
            manifest_sha256=self.manifest_sha256,
            ready_sha256=sha256_bytes(ready_bytes),
            command_sha256=sha256_bytes(command_bytes),
        )
        pointer_bytes, pointer = _read_json(
            self.runtime / ACTIVE_POINTER_FILE
        )
        if pointer_bytes != active_bytes or pointer != active:
            raise QualificationProtocolError(
                "runtime qualification active marker differs from run artifact"
            )
        return self.command

    def _acknowledge(self, metadata: Mapping[str, Any]) -> dict[str, Any]:
        if self.command is None:
            raise QualificationProtocolError(
                "cannot acknowledge qualification before release command"
            )
        ready_bytes, _ = _read_json(self.run_directory / READY_FILE)
        command_bytes, _ = _read_json(self.run_directory / COMMAND_FILE)
        active_bytes, _ = _read_json(self.run_directory / ACTIVE_FILE)
        release_monotonic_s = _finite(
            metadata.get("capture_monotonic_s"),
            "metadata.capture_monotonic_s",
        )
        boundary = float(self.command["not_before_capture_monotonic_s"])
        if release_monotonic_s < boundary:
            raise QualificationProtocolError(
                "qualification release frame precedes command boundary"
            )
        ack = {
            "schema_version": RELEASE_ACK_SCHEMA,
            "protocol_id": PROTOCOL_ID,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "command_id": self.command["command_id"],
            "manifest_sha256": self.manifest_sha256,
            "ready_sha256": sha256_bytes(ready_bytes),
            "release_command_sha256": sha256_bytes(command_bytes),
            "active_marker_sha256": sha256_bytes(active_bytes),
            "release_frame_id": _integer(
                metadata.get("frame_id"),
                "metadata.frame_id",
            ),
            "release_unix_s": _finite(
                metadata.get("capture_unix_s"),
                "metadata.capture_unix_s",
            ),
            "release_monotonic_s": release_monotonic_s,
            "release_simulation_s": _finite(
                metadata.get("simulation_time_s"),
                "metadata.simulation_time_s",
            ),
        }
        ack_path = self.run_directory / ACK_FILE
        create_once_json(ack_path, ack)
        ack_bytes = ack_path.read_bytes()
        provenance = {
            "schema_version": PROVENANCE_SCHEMA,
            "protocol_id": PROTOCOL_ID,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "command_id": self.command["command_id"],
            "manifest_sha256": self.manifest_sha256,
            "ready_sha256": sha256_bytes(ready_bytes),
            "release_command_sha256": sha256_bytes(command_bytes),
            "active_marker_sha256": sha256_bytes(active_bytes),
            "release_ack_sha256": sha256_bytes(ack_bytes),
            "release_frame_id": ack["release_frame_id"],
            "release_unix_s": ack["release_unix_s"],
            "release_monotonic_s": ack["release_monotonic_s"],
            "release_simulation_s": ack["release_simulation_s"],
        }
        create_once_json(self.run_directory / PROVENANCE_FILE, provenance)
        self.release_ack = ack
        self.phase = "measurement"
        return ack

    def record_fields(self, metadata: Mapping[str, Any]) -> dict[str, Any]:
        capture_monotonic_s = _finite(
            metadata.get("capture_monotonic_s"),
            "metadata.capture_monotonic_s",
        )
        self.poll_release_command()
        if self.command is None or capture_monotonic_s < float(
            self.command["not_before_capture_monotonic_s"]
        ):
            return {
                "phase": "hold",
                "capture_monotonic_s": capture_monotonic_s,
                "measurement_elapsed_s": None,
                "measurement_wall_elapsed_s": None,
            }
        if self.release_ack is None:
            self._acknowledge(metadata)
        if self.release_ack is None:
            raise QualificationProtocolError(
                "qualification release acknowledgement was not latched"
            )
        simulation_time_s = _finite(
            metadata.get("simulation_time_s"),
            "metadata.simulation_time_s",
        )
        measurement_elapsed_s = simulation_time_s - float(
            self.release_ack["release_simulation_s"]
        )
        measurement_wall_elapsed_s = capture_monotonic_s - float(
            self.release_ack["release_monotonic_s"]
        )
        if measurement_elapsed_s < 0.0 or measurement_wall_elapsed_s < 0.0:
            raise QualificationProtocolError(
                "qualification measurement frame precedes release origin"
            )
        return {
            "phase": "measurement",
            "capture_monotonic_s": capture_monotonic_s,
            "measurement_elapsed_s": measurement_elapsed_s,
            "measurement_wall_elapsed_s": measurement_wall_elapsed_s,
        }

    def validate_metrics(
        self,
        metrics: Mapping[str, Any],
        *,
        planned_duration_s: float,
    ) -> None:
        if self.release_ack is None:
            raise QualificationProtocolError(
                "qualification metrics cannot be accepted before release"
            )
        identity = metrics.get("qualification_release")
        if not isinstance(identity, Mapping):
            raise QualificationProtocolError(
                "qualification metrics lack release identity"
            )
        expected = {
            "schema_version": "p1-detect-qualification-metrics-origin/v1",
            "protocol_id": PROTOCOL_ID,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "command_id": self.release_ack["command_id"],
            "release_command_sha256": self.release_ack[
                "release_command_sha256"
            ],
            "active_marker_sha256": self.release_ack[
                "active_marker_sha256"
            ],
            "release_frame_id": self.release_ack["release_frame_id"],
            "release_monotonic_s": self.release_ack[
                "release_monotonic_s"
            ],
            "release_simulation_s": self.release_ack[
                "release_simulation_s"
            ],
        }
        for key, value in expected.items():
            actual = identity.get(key)
            if isinstance(value, float):
                if (
                    isinstance(actual, bool)
                    or not isinstance(actual, (int, float))
                    or not math.isclose(
                        float(actual),
                        value,
                        rel_tol=0.0,
                        abs_tol=1e-6,
                    )
                ):
                    raise QualificationProtocolError(
                        f"qualification metrics {key} mismatch"
                    )
            elif actual != value:
                raise QualificationProtocolError(
                    f"qualification metrics {key} mismatch"
                )
        if set(identity) != set(expected):
            raise QualificationProtocolError(
                "qualification metrics release identity has unexpected fields"
            )
        elapsed_simulation_s = _finite(
            metrics.get("elapsed_simulation_s"),
            "metrics.elapsed_simulation_s",
        )
        if elapsed_simulation_s < _finite(
            planned_duration_s,
            "planned_duration_s",
        ):
            raise QualificationProtocolError(
                "qualification metrics duration is shorter than planned"
            )

    def clear_active_pointer(self) -> None:
        pointer_path = self.runtime / ACTIVE_POINTER_FILE
        if not pointer_path.exists():
            return
        pointer_bytes, pointer = _read_json(pointer_path)
        active_bytes, active = _read_json(
            self.run_directory / ACTIVE_FILE
        )
        if pointer_bytes != active_bytes or pointer != active:
            raise QualificationProtocolError(
                "refusing to clear a different qualification active marker"
            )
        pointer_path.unlink()
