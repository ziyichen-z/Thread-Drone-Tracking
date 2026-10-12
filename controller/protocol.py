from __future__ import annotations

import json
import math
import os
from pathlib import Path
import tempfile
import time
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME = PROJECT_ROOT / "runtime"


def finite(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def packet(
    channel: str,
    command: dict[str, Any],
    expires_after_s: float,
    protocol_name: str = "tethered-drone-control/v1",
) -> dict[str, Any]:
    return {
        "protocol": protocol_name,
        "channel": channel,
        "command_id": time.time_ns(),
        "issued_unix_s": time.time(),
        "expires_after_s": finite(expires_after_s, "expires_after_s"),
        "command": command,
    }


def atomic_write(
    name: str,
    data: dict[str, Any],
    runtime: Path | None = None,
) -> Path:
    runtime_directory = Path(runtime) if runtime is not None else RUNTIME
    runtime_directory.mkdir(parents=True, exist_ok=True)
    destination = runtime_directory / name
    descriptor, temp_name = tempfile.mkstemp(dir=runtime_directory, suffix=".tmp")
    temporary = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def latest_frame_bundle() -> tuple[int, Path, Path]:
    manifest_path = RUNTIME / "frames" / "latest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "tethered-frame-manifest/v1":
        raise ValueError(f"unsupported frame manifest: {manifest.get('schema_version')!r}")
    frame_id = int(manifest["frame_id"])
    frames_directory = manifest_path.parent
    image = frames_directory / Path(manifest["image_file"]).name
    metadata = frames_directory / Path(manifest["metadata_file"]).name
    if not image.is_file() or not metadata.is_file():
        raise FileNotFoundError(f"frame {frame_id} is not fully published")
    return frame_id, image, metadata
