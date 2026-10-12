from __future__ import annotations

import json
import math
import os
from pathlib import Path
import platform
import re
import tempfile
import time
from typing import Any, Iterable, Mapping

from .rate2_protocol import Rate2ProtocolError, validate_provenance


SCHEMA_VERSION = "p1-track-run/v1"
_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def validate_run_id(run_id: str) -> str:
    if not _RUN_ID.fullmatch(run_id):
        raise ValueError(
            "run_id must be 1-128 safe characters: letters, digits, dot, dash, underscore"
        )
    return run_id


def host_information() -> dict[str, str]:
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "machine": platform.machine(),
    }


def _atomic_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_frame_records(path: Path) -> tuple[list[dict[str, Any]], int]:
    if not path.is_file():
        raise FileNotFoundError(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    records: list[dict[str, Any]] = []
    truncated_tail_lines = 0
    nonempty_indices = [index for index, line in enumerate(lines) if line.strip()]
    last_nonempty = nonempty_indices[-1] if nonempty_indices else -1
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            if index != last_nonempty:
                raise ValueError(f"invalid JSONL before tail at line {index + 1}")
            truncated_tail_lines = 1
            break
        if not isinstance(value, dict):
            raise ValueError(f"frame record {index + 1} must be an object")
        records.append(value)
    return records, truncated_tail_lines


def _percentile(values: Iterable[float], percentile: float) -> float | None:
    finite_values = sorted(
        float(value) for value in values if math.isfinite(float(value))
    )
    if not finite_values:
        return None
    if len(finite_values) == 1:
        return finite_values[0]
    rank = (len(finite_values) - 1) * percentile
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return finite_values[lower]
    fraction = rank - lower
    return (
        finite_values[lower] * (1.0 - fraction)
        + finite_values[upper] * fraction
    )


def _cadence(values: Iterable[float]) -> dict[str, Any]:
    finite_values = [
        float(value) for value in values if math.isfinite(float(value))
    ]
    intervals = [
        current - previous
        for previous, current in zip(finite_values, finite_values[1:])
    ]
    strictly_increasing = all(interval > 0.0 for interval in intervals)
    rate_hz = None
    if len(finite_values) >= 2 and strictly_increasing:
        elapsed = finite_values[-1] - finite_values[0]
        if elapsed > 0.0:
            rate_hz = (len(finite_values) - 1) / elapsed
    return {
        "samples": len(finite_values),
        "strictly_increasing": strictly_increasing,
        "rate_hz": rate_hz,
        "interval_s": {
            "p50": _percentile(
                (interval for interval in intervals if interval > 0.0), 0.50
            ),
            "p95": _percentile(
                (interval for interval in intervals if interval > 0.0), 0.95
            ),
        },
    }


def _post_launch_capture_window(
    records: list[dict[str, Any]],
    not_before_unix_s: float | None,
    cutoff_source: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    cutoff = (
        float(not_before_unix_s)
        if isinstance(not_before_unix_s, (int, float))
        and not isinstance(not_before_unix_s, bool)
        and math.isfinite(float(not_before_unix_s))
        else None
    )
    finite_records = [
        record
        for record in records
        if isinstance(record.get("capture_unix_s"), (int, float))
        and math.isfinite(float(record["capture_unix_s"]))
    ]
    eligible = (
        [
            record
            for record in finite_records
            if float(record["capture_unix_s"]) >= cutoff
        ]
        if cutoff is not None
        else []
    )
    first = eligible[0] if eligible else None
    return (
        _cadence(float(record["capture_unix_s"]) for record in eligible),
        {
            "cutoff_source": cutoff_source,
            "not_before_unix_s": cutoff,
            "eligible_samples": len(eligible),
            "excluded_prelaunch_samples": len(finite_records) - len(eligible),
            "first_eligible_frame_id": (
                int(first["frame_id"])
                if first is not None
                and isinstance(first.get("frame_id"), int)
                else None
            ),
            "first_eligible_capture_unix_s": (
                float(first["capture_unix_s"]) if first is not None else None
            ),
        },
    )


def build_summary(
    records: list[dict[str, Any]],
    truncated_tail_lines: int,
    *,
    post_launch_not_before_unix_s: float | None = None,
    post_launch_cutoff_source: str = "manifest.created_unix_s",
    planned_duration_s: float | None = None,
    release_monotonic_s: float | None = None,
    release_clock_id: str | None = None,
) -> dict[str, Any]:
    invalid_record_kinds = {
        record.get("record_kind")
        for record in records
        if record.get("record_kind", "frame") not in {"frame", "event"}
    }
    if invalid_record_kinds:
        raise ValueError(
            "invalid record_kind values: "
            f"{sorted(repr(value) for value in invalid_record_kinds)!r}"
        )
    frame_records = [
        record for record in records if record.get("record_kind", "frame") == "frame"
    ]
    event_records = [
        record for record in records if record.get("record_kind", "frame") == "event"
    ]
    measurement_records = [
        record
        for record in frame_records
        if record.get("phase", "measurement") == "measurement"
    ]
    compute_latencies = [
        record["compute_latency_ms"]
        for record in measurement_records
        if isinstance(record.get("compute_latency_ms"), (int, float))
        and record.get("compute_stage") != "init"
    ]
    initialization_latencies = [
        float(record["compute_latency_ms"])
        for record in measurement_records
        if isinstance(record.get("compute_latency_ms"), (int, float))
        and record.get("compute_stage") == "init"
    ]
    frame_ages = [
        record["frame_age_ms"]
        for record in measurement_records
        if isinstance(record.get("frame_age_ms"), (int, float))
    ]
    simulation_times = [
        float(record["simulation_time_s"])
        for record in measurement_records
        if isinstance(record.get("simulation_time_s"), (int, float))
        and math.isfinite(float(record["simulation_time_s"]))
    ]
    capture_times = [
        float(record["capture_unix_s"])
        for record in measurement_records
        if isinstance(record.get("capture_unix_s"), (int, float))
        and math.isfinite(float(record["capture_unix_s"]))
    ]
    backlog_counts = [
        float(record["backlog_count"])
        for record in measurement_records
        if isinstance(record.get("backlog_count"), (int, float))
        and math.isfinite(float(record["backlog_count"]))
    ]
    event_counts: dict[str, int] = {}
    for record in records:
        if record.get("phase", "measurement") != "measurement":
            continue
        event = record.get("event")
        if isinstance(event, str) and event:
            event_counts[event] = event_counts.get(event, 0) + 1
    measurement_elapsed = [
        float(record["measurement_elapsed_s"])
        for record in measurement_records
        if isinstance(record.get("measurement_elapsed_s"), (int, float))
        and not isinstance(record.get("measurement_elapsed_s"), bool)
        and math.isfinite(float(record["measurement_elapsed_s"]))
    ]
    actual_duration_s = (
        max(measurement_elapsed)
        if measurement_elapsed
        else (
            max(simulation_times) - min(simulation_times)
            if len(simulation_times) >= 2
            else 0.0
        )
    )
    first_lost_elapsed_s = next(
        (
            float(record["measurement_elapsed_s"])
            for record in measurement_records
            if record.get("state") == "LOST"
            and isinstance(record.get("measurement_elapsed_s"), (int, float))
            and not isinstance(record.get("measurement_elapsed_s"), bool)
            and math.isfinite(float(record["measurement_elapsed_s"]))
        ),
        None,
    )
    if first_lost_elapsed_s is None and simulation_times:
        first_lost_simulation_time_s = next(
            (
                float(record["simulation_time_s"])
                for record in measurement_records
                if record.get("state") == "LOST"
                and isinstance(record.get("simulation_time_s"), (int, float))
                and not isinstance(record.get("simulation_time_s"), bool)
                and math.isfinite(float(record["simulation_time_s"]))
            ),
            None,
        )
        if first_lost_simulation_time_s is not None:
            first_lost_elapsed_s = max(
                0.0,
                first_lost_simulation_time_s - simulation_times[0],
            )
    time_to_first_lost_s = (
        float(planned_duration_s)
        if planned_duration_s is not None
        else actual_duration_s
    )
    first_lost_right_censored = True
    if first_lost_elapsed_s is not None:
        time_to_first_lost_s = max(0.0, first_lost_elapsed_s)
        first_lost_right_censored = False
    post_launch_cadence, post_launch_window = _post_launch_capture_window(
        measurement_records,
        post_launch_not_before_unix_s,
        post_launch_cutoff_source,
    )
    monotonic_capture_times = [
        float(record["capture_monotonic_s"])
        for record in measurement_records
        if isinstance(record.get("capture_monotonic_s"), (int, float))
        and not isinstance(record.get("capture_monotonic_s"), bool)
        and math.isfinite(float(record["capture_monotonic_s"]))
    ]
    monotonic_cadence = _cadence(monotonic_capture_times)
    if release_clock_id is not None:
        for record in measurement_records:
            if record.get("capture_monotonic_clock_id") != release_clock_id:
                raise ValueError(
                    "INVALID_CLOCK_IDENTITY: measurement frame clock "
                    f"{record.get('capture_monotonic_clock_id')!r} does not "
                    f"match release clock {release_clock_id!r}"
                )
    if release_monotonic_s is not None:
        release_monotonic_s = float(release_monotonic_s)
        if not math.isfinite(release_monotonic_s):
            raise ValueError("release_monotonic_s must be finite")
        if len(monotonic_capture_times) != len(measurement_records):
            raise ValueError("INVALID_CLOCK: measurement frame lacks monotonic capture time")
        if monotonic_capture_times and monotonic_capture_times[0] < release_monotonic_s:
            raise ValueError("INVALID_CLOCK: measurement frame precedes release epoch")
        if not monotonic_cadence["strictly_increasing"]:
            raise ValueError("INVALID_CLOCK: monotonic capture times are not increasing")
    return {
        "schema_version": SCHEMA_VERSION,
        "total_frame_records": len(frame_records),
        "total_event_records": len(event_records),
        "hold_frame_records": len(frame_records) - len(measurement_records),
        "measurement_frame_records": len(measurement_records),
        "published_observations": sum(
            bool(record.get("published_observation"))
            for record in measurement_records
        ),
        "published_gimbal_commands": sum(
            bool(record.get("published_gimbal_command"))
            for record in measurement_records
        ),
        "lost_records": sum(
            record.get("state") == "LOST" for record in measurement_records
        ),
        "gap_events": event_counts.get("GAP", 0),
        "geo_reject_events": sum(
            record.get("event") == "GEO_REJECT"
            or isinstance(record.get("geo_reject_reason"), str)
            for record in frame_records
        ),
        "reinit_required_records": sum(
            record.get("state") == "ERROR_REINIT_REQUIRED" for record in frame_records
        ),
        "event_counts": event_counts,
        "skipped_publications": sum(
            int(record.get("skipped_count", 0)) for record in frame_records
        ),
        "compute_latency_ms": {
            "p50": _percentile(compute_latencies, 0.50),
            "p95": _percentile(compute_latencies, 0.95),
        },
        "initialization_latency_ms": (
            initialization_latencies[0] if initialization_latencies else None
        ),
        "frame_age_ms": {
            "p50": _percentile(frame_ages, 0.50),
            "p95": _percentile(frame_ages, 0.95),
        },
        "wall_clock_capture_cadence": _cadence(capture_times),
        "wall_clock_capture_cadence_post_launch": post_launch_cadence,
        "wall_clock_capture_window": post_launch_window,
        "monotonic_capture_cadence_post_release": monotonic_cadence,
        "release_monotonic_s": release_monotonic_s,
        "release_clock_id": release_clock_id,
        "simulation_time_cadence": _cadence(simulation_times),
        "backlog_count": {
            "p50": _percentile(backlog_counts, 0.50),
            "p95": _percentile(backlog_counts, 0.95),
        },
        "time_to_first_lost_s": time_to_first_lost_s,
        "time_to_first_lost_right_censored": first_lost_right_censored,
        "actual_duration_s": actual_duration_s,
        "actual_wall_duration_s": (
            max(monotonic_capture_times) - min(monotonic_capture_times)
            if release_monotonic_s is not None
            and len(monotonic_capture_times) >= 2
            else (
                max(capture_times) - min(capture_times)
                if len(capture_times) >= 2
                else 0.0
            )
        ),
        "actual_capture_unix_duration_s": (
            max(capture_times) - min(capture_times)
            if len(capture_times) >= 2
            else 0.0
        ),
        "truncated_tail_lines": truncated_tail_lines,
        "finalized_unix_s": time.time(),
    }


def finalize_run(runtime: Path, run_id: str) -> tuple[Path, dict[str, Any]]:
    safe_run_id = validate_run_id(run_id)
    run_directory = Path(runtime) / "runs" / safe_run_id
    records, truncated = read_frame_records(run_directory / "frames.jsonl")
    manifest = json.loads(
        (run_directory / "manifest.json").read_text(encoding="utf-8")
    )
    created_unix_s = (
        manifest.get("created_unix_s")
        if isinstance(manifest, dict)
        else None
    )
    rate2 = manifest.get("rate2") if isinstance(manifest, dict) else None
    rate3 = manifest.get("rate3") if isinstance(manifest, dict) else None
    qualification_release = (
        manifest.get("qualification_release")
        if isinstance(manifest, dict)
        else None
    )
    protocol_count = sum(
        isinstance(value, Mapping)
        for value in (rate2, rate3, qualification_release)
    )
    if protocol_count > 1:
        raise ValueError("INVALID_RELEASE: multiple release protocols in manifest")
    provenance = None
    provenance_kind = None
    if isinstance(rate2, Mapping):
        try:
            provenance = validate_provenance(run_directory)
        except (FileNotFoundError, Rate2ProtocolError) as exception:
            raise ValueError(f"INVALID_RELEASE: {exception}") from exception
        provenance_kind = "rate2"
    elif isinstance(rate3, Mapping):
        from .rate3_protocol import (
            validate_provenance as validate_rate3_provenance,
        )

        try:
            provenance = validate_rate3_provenance(run_directory)
        except (FileNotFoundError, Rate2ProtocolError) as exception:
            raise ValueError(f"INVALID_RELEASE: {exception}") from exception
        provenance_kind = "rate3"
    elif isinstance(qualification_release, Mapping):
        from .qualification_protocol import (
            QualificationProtocolError,
            validate_provenance as validate_qualification_provenance,
        )

        try:
            provenance = validate_qualification_provenance(run_directory)
        except (FileNotFoundError, QualificationProtocolError) as exception:
            raise ValueError(f"INVALID_RELEASE: {exception}") from exception
        provenance_kind = "qualification"
    summary = build_summary(
        records,
        truncated,
        post_launch_not_before_unix_s=(
            provenance.get("release_unix_s")
            if provenance_kind == "qualification"
            else created_unix_s
        ),
        post_launch_cutoff_source=(
            "qualification_release.release_unix_s"
            if provenance_kind == "qualification"
            else "manifest.created_unix_s"
        ),
        planned_duration_s=(
            manifest.get("planned_duration_s")
            if provenance is not None
            else None
        ),
        release_monotonic_s=(
            provenance.get("release_monotonic_s")
            if provenance is not None
            else None
        ),
        release_clock_id=(
            provenance.get("release_clock_id")
            if provenance is not None
            else None
        ),
    )
    summary["metrics_snapshot_present"] = (
        run_directory / "metrics.final.json"
    ).is_file()
    destination = run_directory / "summary.json"
    _atomic_json(destination, summary)
    return destination, summary


class RunLogger:
    def __init__(
        self,
        runtime: Path,
        run_id: str,
        manifest: Mapping[str, Any],
    ):
        self.run_id = validate_run_id(run_id)
        self.run_directory = Path(runtime) / "runs" / self.run_id
        self.run_directory.mkdir(parents=True, exist_ok=False)
        manifest_data = dict(manifest)
        manifest_data["schema_version"] = SCHEMA_VERSION
        manifest_data["run_id"] = self.run_id
        manifest_data.setdefault("created_unix_s", time.time())
        manifest_data.setdefault("host", host_information())
        _atomic_json(self.run_directory / "manifest.json", manifest_data)
        self._frames_path = self.run_directory / "frames.jsonl"
        self._frames = self._frames_path.open("a", encoding="utf-8")
        self._closed = False

    @property
    def frames_path(self) -> Path:
        return self._frames_path

    def append(self, record: Mapping[str, Any]) -> None:
        if self._closed:
            raise RuntimeError("run logger is closed")
        json.dump(dict(record), self._frames, sort_keys=True, allow_nan=False)
        self._frames.write("\n")
        self._frames.flush()

    def snapshot_json(self, name: str, data: Mapping[str, Any]) -> Path:
        if Path(name).name != name or not name.endswith(".json"):
            raise ValueError("snapshot name must be a plain .json filename")
        destination = self.run_directory / name
        _atomic_json(destination, data)
        return destination

    def close(self) -> None:
        if self._closed:
            return
        self._frames.flush()
        os.fsync(self._frames.fileno())
        self._frames.close()
        self._closed = True

    def finalize(self) -> tuple[Path, dict[str, Any]]:
        self.close()
        return finalize_run(self.run_directory.parents[1], self.run_id)

    def __enter__(self) -> "RunLogger":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
