from __future__ import annotations

import math
from typing import Any, Mapping


SENSOR_FRAME_SCHEMA_V1 = "tethered-sensor-frame/v1"
SENSOR_FRAME_SCHEMA_V2 = "tethered-sensor-frame/v2"
SENSOR_FRAME_SCHEMA_V3 = "tethered-sensor-frame/v3"
SYSTEM_MONOTONIC_CLOCK_ID = "system-stopwatch/v1"


def validate_system_monotonic_frame(
    metadata: Mapping[str, Any],
    *,
    context: str = "frame",
) -> float:
    schema = metadata.get("schema_version")
    if schema != SENSOR_FRAME_SCHEMA_V3:
        raise ValueError(
            f"{context} requires sensor frame schema "
            f"{SENSOR_FRAME_SCHEMA_V3!r}; received {schema!r}"
        )
    clock_id = metadata.get("capture_monotonic_clock_id")
    if clock_id != SYSTEM_MONOTONIC_CLOCK_ID:
        raise ValueError(
            f"{context} requires capture_monotonic_clock_id "
            f"{SYSTEM_MONOTONIC_CLOCK_ID!r}; received {clock_id!r}"
        )
    value = metadata.get("capture_monotonic_s")
    if isinstance(value, bool):
        raise ValueError(f"{context} capture_monotonic_s must be numeric")
    try:
        capture = float(value)
    except (TypeError, ValueError) as exception:
        raise ValueError(
            f"{context} capture_monotonic_s must be numeric"
        ) from exception
    if not math.isfinite(capture) or capture < 0.0:
        raise ValueError(
            f"{context} capture_monotonic_s must be finite and non-negative"
        )
    return capture
