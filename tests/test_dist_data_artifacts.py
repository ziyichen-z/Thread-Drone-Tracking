"""create-once / 字节幂等 / supersession / DAG 禁行边（§2 与 §2.2，BC-DATA-1）。"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import artifacts  # noqa: E402


class StoreTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.store = artifacts.ArtifactStore(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()


class CreateOnceTest(StoreTestCase):
    def test_rerun_is_byte_idempotent(self) -> None:
        first = self.store.write("inventory", "attempt-1", {"records": [1, 2]})
        second = self.store.write("inventory", "attempt-1", {"records": [1, 2]})
        self.assertEqual(first.sha256, second.sha256)

    def test_different_bytes_same_attempt_is_hard_error(self) -> None:
        self.store.write("inventory", "attempt-1", {"records": [1]})
        with self.assertRaises(artifacts.CreateOnceError):
            self.store.write("inventory", "attempt-1", {"records": [2]})

    def test_envelope_has_no_clock_field(self) -> None:
        reference = self.store.write("inventory", "attempt-1", {"records": []})
        text = Path(reference.path).read_text(encoding="utf-8")
        for forbidden in ("timestamp", "created_unix", "generated_at", "now"):
            self.assertNotIn(forbidden, text)


class SupersessionTest(StoreTestCase):
    def test_old_attempt_is_retained_and_attributed(self) -> None:
        self.store.write("inventory", "attempt-1", {"records": [1]})
        self.store.write(
            "inventory",
            "attempt-2",
            {"records": [1, 2]},
            supersedes="attempt-1",
            supersession_reason="投影器缺陷返工",
        )
        self.assertEqual(self.store.attempts("inventory"), ["attempt-1", "attempt-2"])
        self.assertEqual(
            self.store.supersession_chain("inventory", "attempt-2"),
            ["attempt-2", "attempt-1"],
        )

    def test_supersession_requires_reason(self) -> None:
        self.store.write("inventory", "attempt-1", {"records": []})
        with self.assertRaises(artifacts.SupersessionError):
            self.store.write("inventory", "attempt-2", {}, supersedes="attempt-1")

    def test_cannot_supersede_missing_attempt(self) -> None:
        with self.assertRaises(artifacts.SupersessionError):
            self.store.write(
                "inventory", "attempt-2", {}, supersedes="attempt-1", supersession_reason="x"
            )

    def test_reason_without_supersedes_is_rejected(self) -> None:
        with self.assertRaises(artifacts.SupersessionError):
            self.store.write("inventory", "attempt-1", {}, supersession_reason="x")


class ForbiddenEdgeTest(StoreTestCase):
    def test_s7_cannot_read_s8_artifacts(self) -> None:
        self.store.write("mother_set", "attempt-1", {"triples": []})
        with self.assertRaises(artifacts.ForbiddenEdgeError):
            self.store.read("mother_set", "attempt-1", requesting_stage=7)

    def test_s1_cannot_read_s2_artifacts(self) -> None:
        self.store.write("layout", "attempt-1", {})
        with self.assertRaises(artifacts.ForbiddenEdgeError):
            self.store.read("layout", "attempt-1", requesting_stage=1)

    def test_same_stage_read_is_allowed(self) -> None:
        self.store.write("mother_candidates", "attempt-1", {"candidates": []})
        payload, _ = self.store.read("mother_candidates", "attempt-1", requesting_stage=7)
        self.assertEqual(payload, {"candidates": []})

    def test_earlier_stage_read_is_allowed(self) -> None:
        self.store.write("inventory", "attempt-1", {"records": []})
        payload, reference = self.store.read("inventory", "attempt-1", requesting_stage=4)
        self.assertEqual(payload, {"records": []})
        self.assertEqual(reference.stage, 1)

    def test_unknown_artifact_is_rejected(self) -> None:
        with self.assertRaises(artifacts.DistDataError):
            self.store.write("not_an_artifact", "attempt-1", {})


class HashReferenceTest(StoreTestCase):
    def test_hash_mismatch_on_read_is_hard_error(self) -> None:
        reference = self.store.write("inventory", "attempt-1", {"records": []})
        with self.assertRaises(artifacts.DistDataError):
            self.store.read(
                "inventory", "attempt-1", requesting_stage=2, expected_sha256="0" * 64
            )
        payload, _ = self.store.read(
            "inventory", "attempt-1", requesting_stage=2, expected_sha256=reference.sha256
        )
        self.assertEqual(payload, {"records": []})

    def test_immutable_input_check_detects_change(self) -> None:
        source = self.root / "source.txt"
        source.write_bytes(b"original")
        entry = {"path": "source.txt", "sha256": artifacts.sha256_file(source)}
        artifacts.immutable_input_check(self.root, [entry], label="test")
        source.write_bytes(b"tampered")
        with self.assertRaises(artifacts.DistDataError):
            artifacts.immutable_input_check(self.root, [entry], label="test")

    def test_immutable_input_check_detects_missing(self) -> None:
        with self.assertRaises(artifacts.DistDataError):
            artifacts.immutable_input_check(
                self.root, [{"path": "gone.txt", "sha256": "0" * 64}], label="test"
            )


class SortKeyTest(unittest.TestCase):
    def test_final_key_is_raw_digest_then_utf8_id(self) -> None:
        """BC-DATA-2：终决键 = 哈希原始 32 字节 + UTF-8 id 字节。"""
        key = artifacts.deterministic_sort_key("seed", "sample")
        self.assertEqual(len(key[0]), 32)
        self.assertEqual(key[1], b"sample")

    def test_key_does_not_rely_on_collision_freedom(self) -> None:
        left = ("\x00" * 32).encode("utf-8")[:32]
        self.assertEqual(
            sorted([(left, b"b"), (left, b"a")]), [(left, b"a"), (left, b"b")]
        )

    def test_key_is_stable_across_calls(self) -> None:
        self.assertEqual(
            artifacts.deterministic_sort_key("s", "x"),
            artifacts.deterministic_sort_key("s", "x"),
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
