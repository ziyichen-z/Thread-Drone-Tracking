#!/usr/bin/env python3
"""P1-SCENE-006 F1: externally recomputable trace_sha256 (schema v2).

The v2 trace artifact publishes every float32 bit pattern as an 8-digit hex
string next to the float value. This module rebuilds the canonical hash
input from those fields alone — int32 little-endian k, then the float32
little-endian bit patterns of px, py, pz, qx, qy, qz, qw per state — and
recomputes the SHA-256, so any third party can verify the recorded
``sha256`` without Unity.

CLI:
    python3 tools/scene006_trace_hash.py verify <artifact.json> [...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys

SCHEMA = "p1-scene-006-trace/v2"
BIT_FIELDS = (
    "px_bits",
    "py_bits",
    "pz_bits",
    "qx_bits",
    "qy_bits",
    "qz_bits",
    "qw_bits",
)


def _decode_bits(value: str, field: str) -> int:
    if not isinstance(value, str) or len(value) != 8:
        raise ValueError(f"trace bit field {field} must be 8 hex digits")
    return int(value, 16)


def canonical_bytes(states: list[dict]) -> bytes:
    """Rebuild the canonical hash input from serialized state records."""
    out = bytearray()
    for k, state in enumerate(states):
        if state["k"] != k:
            raise ValueError("trace state records must be ordered by k")
        out += struct.pack("<i", k)
        for field in BIT_FIELDS:
            out += struct.pack("<I", _decode_bits(state[field], field))
    return bytes(out)


def recompute_sha256(states: list[dict]) -> str:
    return hashlib.sha256(canonical_bytes(states)).hexdigest()


def verify_artifact(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        artifact = json.load(handle)
    if artifact.get("schema_version") != SCHEMA:
        raise ValueError(
            f"{path}: unsupported schema {artifact.get('schema_version')!r}"
        )
    recomputed = recompute_sha256(artifact["states"])
    recorded = artifact["sha256"]
    return {
        "path": path,
        "recorded": recorded,
        "recomputed": recomputed,
        "match": recomputed == recorded,
        "state_count": len(artifact["states"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("artifacts", nargs="+")
    args = parser.parse_args(argv)

    if args.command == "verify":
        failed = False
        for path in args.artifacts:
            result = verify_artifact(path)
            status = "OK" if result["match"] else "MISMATCH"
            print(
                f"{status} {result['path']}: states={result['state_count']} "
                f"recorded={result['recorded'][:16]}… "
                f"recomputed={result['recomputed'][:16]}…"
            )
            failed |= not result["match"]
        return 1 if failed else 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
