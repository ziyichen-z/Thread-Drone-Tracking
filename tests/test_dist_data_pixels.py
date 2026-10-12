"""像素适配器回归（接受轮 14 §26.2：adapter 金标 + 坏图 fail-closed）。

夹具消费**归档真实帧字节**（按真实相对路径复制进临时根）。需要 Pillow 的
用例在缺库解释器上 skip；fail-closed 与纯算术判据的用例**不依赖任何图像库**，
两个解释器都跑。
"""

from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import unittest.mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import contract, make_splits, pixel_source  # noqa: E402

try:  # 只用于 skip 判定，不参与被测逻辑
    from PIL import Image as _PIL_IMAGE  # noqa: N812
except ImportError:  # pragma: no cover - 取决于解释器环境
    _PIL_IMAGE = None

try:
    import numpy as _NUMPY
except ImportError:  # pragma: no cover
    _NUMPY = None

needs_pillow = unittest.skipUnless(_PIL_IMAGE is not None, "本解释器无 Pillow")

# 归档里的真实帧来源（S1 闭集内的 A.2 采集）。
ARCHIVE_FRAMES = (
    "runtime/test-results/"
    "p1-scene-004-scout-3-protocol-invalid-same-id-retry-20260729/frames"
)


def require_archive(case: unittest.TestCase) -> None:
    """消费归档真实字节的用例统一守卫。

    复核角色的一次性副本按纪律不带 `runtime/` 归档；缺守卫的用例会在**那个**
    环境里 IndexError 而不是 skip，使 focused 套件在规定的复核环境下 FAILED
    （复核轮 4 F19 实测）。凡 glob 归档目录的用例都必须先过这道守卫。
    """
    if not sorted((PROJECT_ROOT / ARCHIVE_FRAMES).glob("frame_*.jpg")):
        case.skipTest("真实归档不在本工作副本中")


class IndexRuleTest(unittest.TestCase):
    """取像素判据是纯算术，不需要任何图像库。"""

    def test_pixel_centre_containment_window(self) -> None:
        # 判据：像素中心 i + 0.5 ∈ [x0, x1) ⇔ i ∈ [x0 - 0.5, x1 - 0.5)
        self.assertEqual(pixel_source._ceil_index(-0.5), 0)  # x0 = 0.0
        self.assertEqual(pixel_source._last_index(2.5), 2)  # x1 = 3.0 → 含 2
        self.assertEqual(pixel_source._ceil_index(0.5), 1)  # x0 = 1.0
        self.assertEqual(pixel_source._last_index(0.5), 0)  # x1 = 1.0 → 只含 0
        # 恰落在中心上算含（左闭）；恰落在右端不算（右开）。
        self.assertEqual(pixel_source._ceil_index(1.0), 1)
        self.assertEqual(pixel_source._last_index(1.0), 0)

    def test_describe_pins_the_two_returned_degrees_of_freedom(self) -> None:
        described = pixel_source.describe()
        self.assertEqual(described["grayscale_coefficients"], [0.299, 0.587, 0.114])
        self.assertEqual(described["phash_resize"], contract.PHASH_RESIZE)
        self.assertIn("block mean", described["downscale"])
        self.assertIn("pixel centre", described["crop_rule"])


class FailClosedTest(unittest.TestCase):
    """依赖缺失、字节损坏、尺寸不合同——全部硬失败，绝不静默降级。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.source = pixel_source.ArchivePixelSource(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_missing_frame_bytes_raise_before_any_library_import(self) -> None:
        """缺帧在导入图像库之前就硬失败，故两个解释器上行为一致。"""
        with self.assertRaises(pixel_source.PixelError) as caught:
            self.source.crop_rgb("frames/nope.jpg", (0.0, 0.0, 4.0, 4.0))
        self.assertIn("不存在", str(caught.exception))

    def test_non_positive_matrix_size_is_rejected(self) -> None:
        with self.assertRaises(pixel_source.PixelError):
            self.source.gray_matrix("frames/nope.jpg", 0)

    @needs_pillow
    def test_corrupt_bytes_fail_closed(self) -> None:
        """用归档里的真实 JSON sidecar 字节（不改一字节）冒充 jpg。"""
        require_archive(self)
        sidecar = sorted((PROJECT_ROOT / ARCHIVE_FRAMES).glob("frame_*.json"))[0]
        target = self.root / "frames" / "broken.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sidecar, target)
        with self.assertRaises(pixel_source.PixelError) as caught:
            self.source.crop_rgb("frames/broken.jpg", (0.0, 0.0, 4.0, 4.0))
        self.assertIn("解码失败", str(caught.exception))

    @needs_pillow
    def test_truncated_bytes_fail_closed(self) -> None:
        require_archive(self)
        source_frame = sorted((PROJECT_ROOT / ARCHIVE_FRAMES).glob("frame_*.jpg"))[0]
        target = self.root / "frames" / "truncated.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source_frame.read_bytes()[:512])
        with self.assertRaises(pixel_source.PixelError):
            self.source.gray_matrix("frames/truncated.jpg", contract.PHASH_RESIZE)


@needs_pillow
class ArchiveFrameTest(unittest.TestCase):
    """对归档真实帧的金标：每一项都由本用例用独立算术复算，不信适配器自述。"""

    def setUp(self) -> None:
        require_archive(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        frames = sorted((PROJECT_ROOT / ARCHIVE_FRAMES).glob("frame_*.jpg"))
        self.frame_ids = []
        for source in frames[:2]:
            target = self.root / ARCHIVE_FRAMES / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            self.frame_ids.append(f"{ARCHIVE_FRAMES}/{source.name}")
        self.source = pixel_source.ArchivePixelSource(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _reference_rgb(self, frame_id: str):
        with _PIL_IMAGE.open(self.root / frame_id) as handle:
            converted = handle.convert("RGB")
            return converted.size, converted.tobytes()

    def test_archive_frames_are_640x480_so_the_block_mean_is_exact(self) -> None:
        for frame_id in self.frame_ids:
            self.assertEqual(self.source.dimensions(frame_id), (640, 480))
        self.assertEqual(640 % contract.PHASH_RESIZE, 0)
        self.assertEqual(480 % contract.PHASH_RESIZE, 0)

    def test_crop_rgb_matches_an_independently_computed_window(self) -> None:
        frame_id = self.frame_ids[0]
        (width, _height), payload = self._reference_rgb(frame_id)
        box = (10.4, 20.6, 14.2, 23.1)
        produced = list(self.source.crop_rgb(frame_id, box))
        # 独立复算：直接按「像素中心落在框内」枚举，不调用被测的索引助手。
        expected = [
            (
                payload[(row * width + column) * 3],
                payload[(row * width + column) * 3 + 1],
                payload[(row * width + column) * 3 + 2],
            )
            for row in range(480)
            if box[1] <= row + 0.5 < box[3]
            for column in range(width)
            if box[0] <= column + 0.5 < box[2]
        ]
        self.assertEqual(produced, expected)
        # 窗口本身也钉一次，防止判据整体偏移仍与「同样偏移的复算」互相印证。
        columns = [i for i in range(width) if box[0] <= i + 0.5 < box[2]]
        rows = [j for j in range(480) if box[1] <= j + 0.5 < box[3]]
        self.assertEqual((columns[0], columns[-1]), (10, 13))
        self.assertEqual((rows[0], rows[-1]), (21, 22))
        self.assertEqual(len(produced), len(rows) * len(columns))

    def test_crop_rgb_clips_to_the_image_and_returns_empty_off_frame(self) -> None:
        frame_id = self.frame_ids[0]
        self.assertEqual(list(self.source.crop_rgb(frame_id, (-50.0, -50.0, -1.0, -1.0))), [])
        self.assertEqual(list(self.source.crop_rgb(frame_id, (5.0, 5.0, 5.0, 9.0))), [])
        clipped = self.source.crop_rgb(frame_id, (-3.0, -3.0, 2.0, 2.0))
        self.assertEqual(len(clipped), 4)  # 只剩图内的 2×2

    def test_gray_matrix_is_an_exact_block_mean(self) -> None:
        frame_id = self.frame_ids[0]
        size = contract.PHASH_RESIZE
        (width, _height), payload = self._reference_rgb(frame_id)
        produced = self.source.gray_matrix(frame_id, size)
        self.assertEqual(len(produced), size)
        self.assertTrue(all(len(row) == size for row in produced))
        # 独立复算左上与右下两个块：整数通道和 → 一次 luma → 除以块面积。
        block_width, block_height = width // size, 480 // size
        for block_row, block_column in ((0, 0), (size - 1, size - 1), (7, 19)):
            red = green = blue = 0
            for row in range(block_row * block_height, (block_row + 1) * block_height):
                for column in range(
                    block_column * block_width, (block_column + 1) * block_width
                ):
                    offset = (row * width + column) * 3
                    red += payload[offset]
                    green += payload[offset + 1]
                    blue += payload[offset + 2]
            expected = (0.299 * red + 0.587 * green + 0.114 * blue) / float(
                block_width * block_height
            )
            self.assertEqual(produced[block_row][block_column], expected)

    @unittest.skipUnless(_NUMPY is not None, "本解释器无 numpy")
    def test_gray_matrix_numpy_and_pure_python_paths_agree_bitwise(self) -> None:
        """两条求和路径必须逐位相同——否则 pHash 会随环境漂移。"""
        frame_id = self.frame_ids[0]
        size = contract.PHASH_RESIZE
        _dimensions, payload = self._reference_rgb(frame_id)
        with_numpy = pixel_source._channel_block_sums(payload, 640, 480, size)
        # 强制走纯 Python 分支：让模块内的 `import numpy` 抛 ImportError。
        with unittest.mock.patch.dict(sys.modules, {"numpy": None}):
            pure_python = pixel_source._channel_block_sums(payload, 640, 480, size)
        self.assertEqual(with_numpy, pure_python)

    def test_phash_is_deterministic_and_frame_distinct(self) -> None:
        first, second = self.frame_ids[0], self.frame_ids[1]
        self.assertEqual(self.source.phash(first), self.source.phash(first))
        self.assertEqual(
            self.source.phash(first),
            make_splits.phash(self.source.gray_matrix(first, contract.PHASH_RESIZE)),
        )
        distance = make_splits.hamming(self.source.phash(first), self.source.phash(second))
        self.assertLessEqual(distance, 64)
        self.assertGreaterEqual(distance, 0)

    def test_decode_cache_invalidates_when_the_bytes_change(self) -> None:
        """缓存按 (路径, mtime, 大小) 归键：字节一变必须重新解码。

        陈旧缓存静默掩盖变化，正是复核轮 2/3 那一族 finding 的失败模式。
        """
        frame_id = self.frame_ids[0]
        before = self.source.gray_matrix(frame_id, 8)
        other = self.root / self.frame_ids[1]
        target = self.root / frame_id
        target.write_bytes(other.read_bytes())
        after = self.source.gray_matrix(frame_id, 8)
        self.assertNotEqual(before, after)
        self.assertEqual(after, self.source.gray_matrix(self.frame_ids[1], 8))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
