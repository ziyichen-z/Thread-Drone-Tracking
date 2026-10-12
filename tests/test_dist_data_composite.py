"""BC-DATA-25 组合工件回归（接受轮 21 §33.3 点名的五条）。

判据都落在**生产路径**上：分片写读经 `ArtifactStore.write_composite` /
`read_composite_rows`，S3–S8 经 `PipelineDriver` 的既有 stage 方法。逻辑
schema 不变是本轮的核心承诺，所以每条等价断言都拿「修前整表算法」当基准，
而不是拿流式实现自证。
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
import unittest.mock
import weakref

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import (  # noqa: E402
    artifacts,
    build_catalog,
    make_splits,
)
from test_dist_data_driver import DriverCase  # noqa: E402


class _TrackedEntry(dict):
    """可被 weakref 追踪的 entry —— 用来证明消费后确实被释放。"""


class CompositeStorageTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.store = artifacts.ArtifactStore(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    @staticmethod
    def _rows(count: int, *, width: int = 40) -> list[dict]:
        return [
            {"frame_id": f"frame-{i:06d}", "object_id": f"obj-{i%7}", "blob": "x" * width}
            for i in range(count)
        ]

    def test_production_shard_cap_is_the_frozen_64_mib(self) -> None:
        """夹具会临时缩小上限，故先把生产常量本身钉死。"""
        self.assertEqual(artifacts.SHARD_MAX_UNCOMPRESSED_BYTES, 64 * 1024 * 1024)

    def test_streamed_frames_catalog_is_logically_identical_and_bounded_memory(self) -> None:
        """逐行逻辑等价 + 已消费 entry 必须被释放（跨多个 shard）。"""
        rows = self._rows(400)
        alive: list[weakref.ref] = []

        def _stream():
            for row in rows:
                tracked = _TrackedEntry(row)
                alive.append(weakref.ref(tracked))
                yield tracked

        with unittest.mock.patch.object(
            artifacts, "SHARD_MAX_UNCOMPRESSED_BYTES", 4096
        ):
            self.store.write_composite(
                "frames_catalog", "attempt-1", {"frame_count": len(rows)}, _stream()
            )
            manifest, _ = self.store.composite_manifest(
                "frames_catalog", "attempt-1", requesting_stage=3
            )
            self.assertGreater(len(manifest["shards"]), 1, "夹具须跨多个 shard")

        # 逻辑等价：读回的行序列与「修前整表」逐字段相同。
        got = list(
            self.store.read_composite_rows(
                "frames_catalog", "attempt-1", requesting_stage=4
            )
        )
        self.assertEqual(got, rows)
        self.assertEqual(manifest["row_count"], len(rows))

        # 有界性：绝大多数早期 entry 在写完后必须已被回收。若生产路径把全集
        # `list()` 化，这些 weakref 会全部存活，本断言必失败。
        released = sum(1 for reference in alive if reference() is None)
        self.assertGreater(
            released, len(rows) * 0.9,
            f"只释放了 {released}/{len(rows)} 个 entry；生产路径疑似驻留全集",
        )

    def test_composite_publish_is_atomic_and_orphan_staging_fails_closed(self) -> None:
        """分片中途失败：不得出现 artifact ref；孤立 staging 原样保留且阻止重用。"""
        rows = self._rows(300)

        def _explode():
            for index, row in enumerate(rows):
                if index == 200:
                    raise RuntimeError("模拟分片中断")
                yield row

        with unittest.mock.patch.object(
            artifacts, "SHARD_MAX_UNCOMPRESSED_BYTES", 4096
        ):
            with self.assertRaises(RuntimeError):
                self.store.write_composite(
                    "frames_catalog", "attempt-1", {"frame_count": 0}, _explode()
                )
        manifest_path = self.store.path_for("frames_catalog", "attempt-1")
        staging = self.store.staging_dir("frames_catalog", "attempt-1")
        self.assertFalse(manifest_path.exists(), "manifest 是唯一提交点，不得出现")
        self.assertEqual(self.store.attempts("frames_catalog"), [], "工件须视为缺席")
        self.assertTrue(staging.exists(), "孤立 staging 必须原样保留")
        staged_before = sorted(path.name for path in staging.iterdir())
        self.assertTrue(staged_before, "夹具须已落下部分 shard")

        # 重用/续传一律 fail-closed，且不得自动删除现场。
        with self.assertRaises(artifacts.IncompleteCompositeArtifactError):
            self.store.write_composite(
                "frames_catalog", "attempt-1", {"frame_count": len(rows)}, iter(rows)
            )
        self.assertEqual(sorted(path.name for path in staging.iterdir()), staged_before)

    def test_manifest_publish_failure_leaves_shards_and_fails_closed(self) -> None:
        """SP22-2：staging 已整体 rename、manifest 尚未 commit 的故障窗口。

        原实现在此只会以 `OSError: Directory not empty` 失败，并**新建**一个
        `.staging/` 改变现场（接受轮 22 实测）。合同要求：无 manifest 时既有
        `shards/` 与孤立 `.staging/` 同样算不完整组合工件，在写任何新字节前
        `IncompleteCompositeArtifactError`，且现场逐字节不变。
        """
        import hashlib

        rows = self._rows(200)
        with unittest.mock.patch.object(
            artifacts, "_atomic_publish", side_effect=OSError("模拟 manifest 发布失败")
        ):
            with self.assertRaises(OSError):
                self.store.write_composite(
                    "frames_catalog", "attempt-1", {"frame_count": len(rows)}, iter(rows)
                )

        attempt_dir = self.store.shard_dir("frames_catalog", "attempt-1").parent
        manifest_path = self.store.path_for("frames_catalog", "attempt-1")
        staging = self.store.staging_dir("frames_catalog", "attempt-1")
        shards = self.store.shard_dir("frames_catalog", "attempt-1")
        self.assertFalse(manifest_path.exists(), "manifest 未 commit")
        self.assertTrue(shards.exists(), "夹具须命中 rename 之后的故障窗口")
        self.assertFalse(staging.exists(), "该窗口下 staging 已被 rename 走")
        self.assertEqual(self.store.attempts("frames_catalog"), [], "工件须视为缺席")

        def _snapshot() -> dict[str, str]:
            return {
                str(path.relative_to(attempt_dir)): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in sorted(attempt_dir.rglob("*"))
                if path.is_file()
            }

        before = _snapshot()
        self.assertTrue(before, "夹具须已落下 final shard")
        with self.assertRaises(artifacts.IncompleteCompositeArtifactError):
            self.store.write_composite(
                "frames_catalog", "attempt-1", {"frame_count": len(rows)}, iter(rows)
            )
        self.assertEqual(_snapshot(), before, "现场必须逐字节不变")
        self.assertFalse(staging.exists(), "不得新增 staging 残留")

    def test_composite_tamper_and_create_once_are_rejected(self) -> None:
        rows = self._rows(300)
        with unittest.mock.patch.object(
            artifacts, "SHARD_MAX_UNCOMPRESSED_BYTES", 4096
        ):
            reference = self.store.write_composite(
                "frames_catalog", "attempt-1", {"frame_count": len(rows)}, iter(rows)
            )
            manifest, _ = self.store.composite_manifest(
                "frames_catalog", "attempt-1", requesting_stage=3
            )
            self.assertGreater(len(manifest["shards"]), 2)

            # 同输入重跑 → 幂等返回同 ref。
            again = self.store.write_composite(
                "frames_catalog", "attempt-1", {"frame_count": len(rows)}, iter(rows)
            )
            self.assertEqual(again.sha256, reference.sha256)

            # 异字节 → CreateOnceError。
            with self.assertRaises(artifacts.CreateOnceError):
                self.store.write_composite(
                    "frames_catalog", "attempt-1", {"frame_count": 1}, iter(rows)
                )

        directory = self.store.shard_dir("frames_catalog", "attempt-1")
        shards = sorted(directory.iterdir())

        def _expect_rejected(message: str) -> None:
            with self.assertRaises(artifacts.IncompleteCompositeArtifactError, msg=message):
                list(
                    self.store.read_composite_rows(
                        "frames_catalog", "attempt-1", requesting_stage=4
                    )
                )

        original = shards[1].read_bytes()
        # (a) 改 shard 字节
        payload = gzip.decompress(original).replace(b"obj-1", b"obj-9", 1)
        shards[1].write_bytes(artifacts._gzip_bytes(payload))
        _expect_rejected("改字节未被拒绝")
        shards[1].write_bytes(original)

        # (b) 丢 shard
        shards[1].unlink()
        _expect_rejected("丢 shard 未被拒绝")
        shards[1].write_bytes(original)

        # (c) 改顺序（把两个 shard 的字节对调）
        first = shards[0].read_bytes()
        shards[0].write_bytes(original)
        shards[1].write_bytes(first)
        _expect_rejected("乱序未被拒绝")
        shards[0].write_bytes(first)
        shards[1].write_bytes(original)

        # (d) 改行数：重压一个少一行的 shard，并同步其 sha 使清单「自洽」——
        #     行数与累积哈希仍须把它拦下。
        lines = gzip.decompress(original).splitlines(keepends=True)
        shards[1].write_bytes(artifacts._gzip_bytes(b"".join(lines[:-1])))
        _expect_rejected("改行数未被拒绝")
        shards[1].write_bytes(original)

        # 恢复后必须重新可读，证明上面每次拒绝都不是副作用造成的。
        self.assertEqual(
            len(list(self.store.read_composite_rows(
                "frames_catalog", "attempt-1", requesting_stage=4))),
            len(rows),
        )


class StreamedPipelineTest(DriverCase):
    """S3–S8 在合成小世界上的流式 vs 修前整表等价。"""

    def _legacy_entries(self) -> list[dict]:
        """用修前的做法把整表算出来，作为等价基准（不经组合工件）。"""
        layout = self._layout()
        inventory = self._inventory()
        from tools.dist_data import roots

        bound = {
            unit: partition
            for partition in layout["scenario_partitions"].values()
            for unit in partition["source_units"]
        }
        entries = []
        for record in inventory["records"]:
            partition = bound[roots.source_unit_for(record["path"])]
            document = json.loads(
                (self.root / record["path"]).with_suffix(".json").read_text()
            )
            frame = build_catalog.FrameInput(
                frame_id=record["path"],
                sidecar=document,
                family=record["family"],
                layout_class=record["layout_class"],
                usage_class=record["usage_class"],
                layout_binding_valid=True,
                sidecar_complete=True,
                truth_row=None,
                truth_schema=None,
            )
            entries.append(
                build_catalog.build_frame_entry(
                    frame,
                    list(partition["instances"]) + list(partition["phantoms"]),
                    partition.get("route_world_m", []),
                    build_catalog.vehicle_envelope_half_extents(partition["instances"]),
                )
            )
        return entries

    def test_streamed_splits_preserves_all_sample_roles_and_exposure_counts(self) -> None:
        """逐行角色、排序、split 归属、四集汇总与 `sample_count` 全部对等。"""
        self.driver.stage3_frames_catalog()
        self.driver.stage4_splits()
        manifest, _ = self.store.composite_manifest(
            "splits", "attempt-1", requesting_stage=7
        )
        streamed_roles = list(
            self.store.read_composite_rows("splits", "attempt-1", requesting_stage=7)
        )

        # 修前基准：整表 `assign_splits` 在同一批 atom / entry 上的结果。
        entries = list(
            self.store.read_composite_rows(
                "frames_catalog", "attempt-1", requesting_stage=4
            )
        )
        atoms = self._atoms_from(entries)
        legacy = make_splits.assign_splits(atoms, entries)

        self.assertEqual(streamed_roles, legacy["sample_roles"])
        self.assertEqual(
            manifest["exposure_matrix"], legacy["exposure_matrix"],
            "四集 exposure 汇总必须逐字段对等",
        )
        self.assertEqual(
            manifest["exposure_matrix"]["sample_count"], len(streamed_roles),
            "BC-DATA-25 (1)：sample_count 必须等于完整角色行数",
        )
        for key in ("atom_assignment", "family_assignment", "frames", "frame_counts",
                    "dropped_frames", "d3_holdout_empty", "leakage_assertions"):
            self.assertEqual(manifest[key], legacy[key], key)
        # 排序：逐 (frame_id, object_id) 升序。
        keys = [(row["frame_id"], row["object_id"]) for row in streamed_roles]
        self.assertEqual(keys, sorted(keys))

    @staticmethod
    def _atoms_from(entries: list[dict]) -> list[make_splits.AtomSummary]:
        family_of = {entry["frame_id"]: entry["family"] for entry in entries}
        phash_of = {
            entry["frame_id"]: 0 if "famA" in entry["frame_id"] else (2**64 - 1)
            for entry in entries
        }
        merged = make_splits.merge_atoms(family_of, phash_of)
        atom_of_family = {
            family: atom for atom, families in merged["atoms"].items() for family in families
        }
        buckets: dict[str, list[dict]] = {}
        for entry in entries:
            buckets.setdefault(atom_of_family[entry["family"]], []).append(entry)
        summaries = []
        for atom_id in sorted(buckets):
            members = buckets[atom_id]
            summaries.append(
                make_splits.AtomSummary(
                    atom_id=atom_id,
                    families=sorted(merged["atoms"][atom_id]),
                    layout_classes=sorted({e["layout_class"] for e in members}),
                    floor_eligible_frames=sorted(
                        e["frame_id"] for e in members
                        if build_catalog.pre_split_floor_eligible(e)
                    ),
                    non_floor_frames=sorted(
                        e["frame_id"] for e in members
                        if not build_catalog.pre_split_floor_eligible(e)
                    ),
                    station_keys=sorted(
                        {e["station_bin"]["key"] for e in members if e["station_bin"]["key"]}
                    ),
                    object_ids=sorted(
                        {i["object_id"] for e in members for i in e["objects"]}
                    ),
                )
            )
        return summaries

    def test_production_manifests_record_the_actual_input_artifact_refs(self) -> None:
        """SP22-1：S3/S4 的 manifest `inputs` 必须是**本次实际读取**的上游 ref。

        原实现两处 `write_composite` 都没传 `inputs`，信封写出 `[]`
        （接受轮 22 实测）。引用不得事后按路径伪造，故此处逐字段比对
        `ArtifactRef.as_reference()`。
        """
        inventory_ref = self.store.read(
            "inventory", "attempt-1", requesting_stage=3
        )[1]
        layout_ref = self.store.read("layout", "attempt-1", requesting_stage=3)[1]

        self.driver.stage3_frames_catalog()
        catalog_envelope = json.loads(
            self.store.path_for("frames_catalog", "attempt-1").read_bytes()
        )
        self.assertEqual(
            catalog_envelope["inputs"],
            [inventory_ref.as_reference(), layout_ref.as_reference()],
            "S3 manifest 须引用本次读取的 inventory 与 layout",
        )

        catalog_ref = self.store.composite_manifest(
            "frames_catalog", "attempt-1", requesting_stage=4
        )[1]
        self.driver.stage4_splits()
        splits_envelope = json.loads(
            self.store.path_for("splits", "attempt-1").read_bytes()
        )
        self.assertEqual(
            splits_envelope["inputs"],
            [catalog_ref.as_reference()],
            "S4 manifest 须引用本次读取的 frames_catalog",
        )
        # lineage 的 sha 必须真的指向盘上那份 manifest，而不是任意占位值。
        self.assertEqual(
            splits_envelope["inputs"][0]["sha256"],
            artifacts.sha256_hex(
                self.store.path_for("frames_catalog", "attempt-1").read_bytes()
            ),
        )

    def test_streamed_consumers_match_legacy_small_fixture_s4_to_s8(self) -> None:
        """S3 行流与修前整表逐字节一致；S4–S8 的输出/终态逐字义等价。"""
        self.driver.stage3_frames_catalog()
        streamed = list(
            self.store.read_composite_rows(
                "frames_catalog", "attempt-1", requesting_stage=4
            )
        )
        self.assertEqual(streamed, self._legacy_entries(), "S3 逻辑 entry 序列须一致")

        self.driver.stage4_splits()
        field_catalog = self.driver.stage5_field_catalog()
        self.assertGreater(field_catalog["objects"], 0)

        # S6 分层同样只经类型化迭代器。
        strata = self.driver.audit_strata()
        self.assertEqual(sum(strata["counts"].values()), strata["sample_count"])

        # S7 门与修前一致：合成世界必然关门，四条 floor 全不达标。
        self.store.write(
            "audit", "attempt-1",
            {"stage": 6, "verdict": "PASS", "downgraded_group_keys": []},
        )
        gate = self.driver.stage7_gate()
        from tools.dist_data import g0_report

        self.assertEqual(gate["gate"], g0_report.GATE_INSUFFICIENT)
        self.assertEqual(sorted(gate["unmet_floors"]), ["F1", "F2", "F3", "F4"])

        # S8 在关门时仍必须拒绝物化。
        from tools.dist_data import gen_mother_templates

        with self.assertRaises(gen_mother_templates.MotherSetError):
            self.driver.stage8_mother_set()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
