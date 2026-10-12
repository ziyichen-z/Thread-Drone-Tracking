from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Sequence
from urllib.request import urlopen

from controller.trackers import (
    DEFAULT_NANOTRACK_V2_MODEL_DIR,
    DEFAULT_NANOTRACK_V2_SPEC,
    load_nanotrack_v2_spec,
    sha256_file,
)


def fetch_nanotrack_v2_models(
    spec_path: Path,
    model_dir: Path,
) -> list[Path]:
    spec = load_nanotrack_v2_spec(spec_path)
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    fetched: list[Path] = []
    for role in ("backbone", "neckhead"):
        model = spec["models"][role]
        destination = model_dir / model["filename"]
        if destination.is_file():
            if (
                destination.stat().st_size == model["size_bytes"]
                and sha256_file(destination) == model["sha256"]
            ):
                fetched.append(destination)
                continue
            raise ValueError(
                f"existing NanoTrack-v2 {role} model does not match "
                f"the frozen identity: {destination}"
            )

        partial = destination.with_suffix(destination.suffix + ".partial")
        try:
            with urlopen(model["url"], timeout=60) as response:
                with partial.open("wb") as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
            actual_size = partial.stat().st_size
            if actual_size != model["size_bytes"]:
                raise ValueError(
                    f"downloaded NanoTrack-v2 {role} size mismatch: "
                    f"expected {model['size_bytes']}, got {actual_size}"
                )
            actual_hash = sha256_file(partial)
            if actual_hash != model["sha256"]:
                raise ValueError(
                    f"downloaded NanoTrack-v2 {role} SHA-256 mismatch: "
                    f"expected {model['sha256']}, got {actual_hash}"
                )
            os.replace(partial, destination)
        except Exception:
            partial.unlink(missing_ok=True)
            raise
        fetched.append(destination)
    return fetched


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch the frozen, hash-verified NanoTrack-v2 ONNX pair."
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=DEFAULT_NANOTRACK_V2_SPEC,
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=DEFAULT_NANOTRACK_V2_MODEL_DIR,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    for path in fetch_nanotrack_v2_models(args.spec, args.model_dir):
        print(path)


if __name__ == "__main__":
    main(sys.argv[1:])
