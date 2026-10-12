"""S1 源清单：恰一匹配断言、lineage 折叠、join 状态与空目录断言（§2.2）。

夹具由**生产路径**产出：真实归档帧与 sidecar 按原相对路径复制进临时根，
不手写 JPEG 字节，也不手写 sidecar JSON。
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import build_inventory, roots  # noqa: E402

# 两个真实归档帧（不同用途类、不同布局类），S1 的最小可复算输入。
ARCHIVE_IMAGE = "runtime/frames.1b-diagnostic-hold"
QUAL_IMAGE = "runtime/frames.qual3-leftover-hold"
DOC_COPY_DIR = "docs/evidence/P1-M3-BODY-001-1b"


def _first_frame(directory: str) -> Path | None:
    base = PROJECT_ROOT / directory
    if not base.exists():
        return None
    frames = sorted(base.glob("frame_*.jpg"))
    return frames[0] if frames else None


class InventoryFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.source = _first_frame(ARCHIVE_IMAGE)
        if self.source is None:
            self.skipTest("归档帧不在本工作副本中")
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "runtime" / "frames").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _place(self, relative_directory: str, source: Path, name: str | None = None) -> str:
        target_dir = self.root / relative_directory
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / (name or source.name)
        shutil.copy2(source, target)
        sidecar = source.with_suffix(".json")
        if sidecar.exists():
            shutil.copy2(sidecar, target.with_suffix(".json"))
        return target.relative_to(self.root).as_posix()


class JpegDimensionTest(InventoryFixture):
    def test_reads_real_archive_frame(self) -> None:
        self.assertEqual(build_inventory.jpeg_dimensions(self.source), (640, 480))

    def test_non_jpeg_is_rejected(self) -> None:
        bogus = self.root / "not.jpg"
        bogus.write_bytes(b"not a jpeg at all")
        with self.assertRaises(build_inventory.InventoryError):
            build_inventory.jpeg_dimensions(bogus)


class EmptyBridgeTest(InventoryFixture):
    def test_active_bridge_must_be_empty(self) -> None:
        build_inventory.assert_empty_dirs(self.root)
        shutil.copy2(self.source, self.root / "runtime" / "frames" / self.source.name)
        with self.assertRaises(build_inventory.InventoryError):
            build_inventory.assert_empty_dirs(self.root)


class MatchAssertionTest(InventoryFixture):
    def test_unmatched_file_is_a_hard_error(self) -> None:
        """附录 A 是闭集：零匹配不得静默纳入或跳过。"""
        self._place("runtime/some-new-archive/frames", self.source)
        with self.assertRaises(build_inventory.InventoryError) as caught:
            build_inventory.build_inventory(self.root)
        self.assertIn("零匹配", str(caught.exception))

    def test_third_party_root_is_excluded_before_row_matching(self) -> None:
        self._place("runtime/models/nanotrack-v2", self.source)
        payload = build_inventory.build_inventory(self.root)
        self.assertEqual(payload["record_count"], 0)


class InventoryRecordTest(InventoryFixture):
    def test_records_carry_usage_class_and_decision(self) -> None:
        relative = self._place(ARCHIVE_IMAGE, self.source)
        payload = build_inventory.build_inventory(self.root)
        record = next(item for item in payload["records"] if item["path"] == relative)
        self.assertEqual(record["usage_class"], "DIAGNOSTIC_HOLD")
        self.assertEqual(record["decision"], "EXCLUDED_DIAGNOSTIC_CHANNEL")
        self.assertEqual(record["family"], "1b-diag")
        self.assertEqual(record["layout_class"], roots.LAYOUT_DEFAULT)
        self.assertEqual((record["width"], record["height"]), (640, 480))
        self.assertEqual(len(record["sha256"]), 64)

    def test_missing_sidecar_excludes_for_no_pose(self) -> None:
        target_dir = self.root / QUAL_IMAGE
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.source, target_dir / "frame_0000000001.jpg")  # 只放 jpg
        payload = build_inventory.build_inventory(self.root)
        record = payload["records"][0]
        self.assertEqual(record["usage_class"], "VALID_PARENT_HOLD")
        self.assertEqual(record["decision"], "EXCLUDED_NO_POSE")
        self.assertFalse(record["sidecar_join"]["complete"])

    def test_incomplete_sidecar_is_detected(self) -> None:
        relative = self._place(QUAL_IMAGE, self.source, name="frame_0000000002.jpg")
        sidecar = self.root / relative
        sidecar = sidecar.with_suffix(".json")
        if not sidecar.exists():
            self.skipTest("源帧无 sidecar")
        document = json.loads(sidecar.read_text(encoding="utf-8"))
        del document["intrinsics_px"]
        sidecar.write_text(json.dumps(document), encoding="utf-8")
        payload = build_inventory.build_inventory(self.root)
        record = next(item for item in payload["records"] if item["path"] == relative)
        self.assertEqual(record["decision"], "EXCLUDED_NO_POSE")
        self.assertIn("intrinsics_px", record["sidecar_join"]["missing_keys"])

    def test_truth_join_is_recorded_even_when_absent(self) -> None:
        relative = self._place(
            "runtime/test-results/p1-m3-body-001-arm-a-trial-3-post-run/frames",
            self.source,
            name="frame_0000000001.jpg",
        )
        payload = build_inventory.build_inventory(self.root)
        record = next(item for item in payload["records"] if item["path"] == relative)
        self.assertEqual(
            record["truth_join"]["source"],
            "runtime/runs/p1-m3-body-001-arm-a-trial-3/m3_body_truth.jsonl",
        )
        self.assertFalse(record["truth_join"]["present"])


class LineageTest(InventoryFixture):
    def test_identical_bytes_fold_into_one_lineage_group(self) -> None:
        """正式归档 / hold / 文档副本按内容哈希折叠，primary 由用途类表序定。"""
        formal = self._place(
            "runtime/test-results/p1-m3-body-001-arm-a-trial-3-post-run/frames",
            self.source,
            name="frame_0000000001.jpg",
        )
        doc_copy = self._place(DOC_COPY_DIR, self.source, name="frame_0000000001.jpg")
        payload = build_inventory.build_inventory(self.root)
        self.assertEqual(len(payload["lineage_groups"]), 1)
        group = payload["lineage_groups"][0]
        self.assertEqual(group["member_count"], 2)
        self.assertEqual(group["primary"], formal)
        self.assertEqual(group["duplicates"], [doc_copy])

    def test_distinct_bytes_stay_separate(self) -> None:
        other = _first_frame(QUAL_IMAGE)
        if other is None:
            self.skipTest("qual3 归档帧不在本工作副本中")
        self._place(ARCHIVE_IMAGE, self.source)
        self._place(QUAL_IMAGE, other)
        payload = build_inventory.build_inventory(self.root)
        self.assertEqual(len(payload["lineage_groups"]), 2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
