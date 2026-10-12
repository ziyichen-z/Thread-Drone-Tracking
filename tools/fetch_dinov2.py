from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
from typing import Mapping
from urllib.request import urlopen

from controller.reanchor import (
    DEFAULT_CONFIG,
    _resolve_project_path,
    load_reanchor_config,
    verify_file,
)
from controller.reanchor_models import verify_extracted_source


def _fetch(url: str, destination: Path, identity: Mapping[str, object], label: str) -> None:
    if destination.is_file():
        verify_file(
            destination,
            size_bytes=int(identity["size_bytes"]),
            sha256=str(identity["sha256"]),
            label=label,
        )
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".download",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as output, urlopen(url, timeout=60) as response:
            shutil.copyfileobj(response, output)
            output.flush()
            os.fsync(output.fileno())
        verify_file(
            temporary,
            size_bytes=int(identity["size_bytes"]),
            sha256=str(identity["sha256"]),
            label=label,
        )
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def fetch(config_path: Path) -> tuple[Path, Path, Path]:
    config = load_reanchor_config(config_path)
    source = config.appearance["source"]
    weights = config.appearance["weights"]
    archive = _resolve_project_path(source["archive_path"], "appearance.source.archive_path")
    source_dir = _resolve_project_path(source["directory"], "appearance.source.directory")
    weight = _resolve_project_path(weights["path"], "appearance.weights.path")
    _fetch(
        str(source["archive_url"]),
        archive,
        {
            "size_bytes": source["archive_size_bytes"],
            "sha256": source["archive_sha256"],
        },
        "DINOv2 source archive",
    )
    _fetch(str(weights["url"]), weight, weights, "DINOv2 weights")
    if not source_dir.exists():
        source_dir.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, mode="r:gz") as handle:
            handle.extractall(source_dir.parent, filter="data")
    verify_extracted_source(archive, source_dir)
    license_path = source_dir / str(source["license_path"])
    verify_file(
        license_path,
        size_bytes=int(source["license_size_bytes"]),
        sha256=str(source["license_sha256"]),
        label="DINOv2 LICENSE",
    )
    return archive, source_dir, weight


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch the user-authorized, hash-pinned P1-DETECT-001 DINOv2 artifacts."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--authorized",
        action="store_true",
        help="confirm that the user explicitly authorized this download",
    )
    args = parser.parse_args()
    if not args.authorized:
        parser.error("download requires an explicit user authorization and --authorized")
    for path in fetch(args.config):
        print(path)


if __name__ == "__main__":
    main()
