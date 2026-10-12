"""Tests for tools/scene006_trace_hash.py (P1-SCENE-006 F1)."""

import json
import os
import struct
import unittest

from tools.scene006_trace_hash import (
    canonical_bytes,
    main,
    recompute_sha256,
    verify_artifact,
)

FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "scene006-trace-v2-sample.json"
)


class Scene006TraceHashTest(unittest.TestCase):
    def test_fixture_recomputes_recorded_sha256(self):
        result = verify_artifact(FIXTURE)
        self.assertTrue(result["match"], result)
        self.assertEqual(3, result["state_count"])

    def test_canonical_layout_matches_independent_construction(self):
        with open(FIXTURE, "r", encoding="utf-8") as handle:
            artifact = json.load(handle)
        # Independent byte construction: int32-LE k, then each 8-hex
        # uint32 emitted little-endian, in the documented field order.
        expected = bytearray()
        for k, state in enumerate(artifact["states"]):
            expected += struct.pack("<i", k)
            for field in (
                "px_bits", "py_bits", "pz_bits",
                "qx_bits", "qy_bits", "qz_bits", "qw_bits",
            ):
                expected += struct.pack("<I", int(state[field], 16))
        self.assertEqual(
            bytes(expected), canonical_bytes(artifact["states"]))

    def test_negative_zero_bit_pattern_is_preserved(self):
        with open(FIXTURE, "r", encoding="utf-8") as handle:
            artifact = json.load(handle)
        # state 0 py is negative zero: the float text would normalize to
        # -0.0/0.0, but the bit pattern must stay 0x80000000.
        self.assertEqual("80000000", artifact["states"][0]["py_bits"])
        recomputed = recompute_sha256(artifact["states"])
        tampered = json.loads(json.dumps(artifact))
        tampered["states"][0]["py_bits"] = "00000000"
        self.assertNotEqual(recomputed, recompute_sha256(tampered["states"]))

    def test_cli_verify_ok_and_mismatch(self):
        self.assertEqual(0, main(["verify", FIXTURE]))
        with open(FIXTURE, "r", encoding="utf-8") as handle:
            artifact = json.load(handle)
        artifact["states"][1]["qx_bits"] = "deadbeef"
        path = os.path.join(
            os.path.dirname(__file__), "fixtures", ".tmp-mismatch.json")
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(artifact, handle)
            self.assertEqual(1, main(["verify", path]))
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_verify_rejects_wrong_schema(self):
        with open(FIXTURE, "r", encoding="utf-8") as handle:
            artifact = json.load(handle)
        artifact["schema_version"] = "p1-scene-006-trace/v1"
        path = os.path.join(
            os.path.dirname(__file__), "fixtures", ".tmp-wrong-schema.json")
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(artifact, handle)
            with self.assertRaises(ValueError):
                verify_artifact(path)
        finally:
            if os.path.exists(path):
                os.unlink(path)


if __name__ == "__main__":
    unittest.main()
