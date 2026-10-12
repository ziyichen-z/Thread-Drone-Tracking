#!/usr/bin/env python3
"""归档帧的只读像素适配器：`PixelSource` + `GraySource` 的具体实现。

提案 §2.4/§2.5 明定像素解码后的颜色统计与 pHash；接受轮 14（§26.2）授权
补这个具体 adapter，**只算代码**，不授权在真实归档上产出任何正式工件。

设计要点：

- **图像库只负责解码。** 灰度换算与 32×32 降采样都在本模块用显式算术完成，
  不调用 `Image.convert("L")` 或 `Image.resize()`——那两者的结果依赖 Pillow
  版本、SIMD 与重采样滤波器实现，会让 pHash 位随环境漂移，而 pHash 直接决定
  近重复并簇 → 原子 → 切分 → F3/F4。复核角色能用纯算术独立复算本模块的输出。
- **依赖缺失一律 fail-closed**：抛 `PixelError`，绝不静默降级成灰阶近似或
  跳过该帧（跳过会让颜色/近重复统计悄悄少算，方向 fail-open）。
- **`frame_id` = inventory 全局唯一路径**（提案 §20.2 第 7 条对 BC-DATA-3
  排序键的裁定），即仓库相对 POSIX 路径；本模块据此定位字节，不另立命名。

两处合同未给定、由本模块**显式取定并退回接受角色确认**的自由度，见
`docs/evidence/P1-VLM-DATA-001-implementation.md` 的返回事项：

1. `GRAYSCALE_COEFFICIENTS`：RGB → 灰度用 ITU-R 601-2 luma（与 Pillow
   `convert("L")` 的文档公式同系数），在 float 域计算、不做整数截断。
2. `crop_rgb` 的取像素判据：**像素中心落在框内**（`x0 ≤ i + 0.5 < x1`），
   再与图像边界求交。空集返回空序列——`estimate_color` 据此判 `UNVERIFIED`，
   是 fail-closed 方向。

降采样不是自由度：`PHASH_RESIZE` 为 32，而归档全部 24,152 张帧都是
640×480（实测），`640 % 32 == 480 % 32 == 0`，故块均值是**精确整除**的
块平均，无插值、无滤波器选择余地。尺寸不整除时硬失败，绝不回退到插值。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from tools.dist_data import contract, project_boxes
from tools.dist_data.artifacts import DistDataError

# ITU-R 601-2 luma。与 Pillow `convert("L")` 的文档公式同系数，但本模块在
# float 域计算，不复用其整数截断，故结果可由复核角色用纯算术复算。
GRAYSCALE_COEFFICIENTS: tuple[float, float, float] = (0.299, 0.587, 0.114)

# 解码缓存上限（帧数）。S5 对每个对象取最近 K=5 帧，同一帧会被多个对象命中。
DECODE_CACHE_FRAMES = 32


class PixelError(DistDataError):
    """像素读取失败（依赖缺失、字节损坏、尺寸不合同）——一律 fail-closed。"""


def _require_pillow():
    """惰性导入 Pillow；缺失时给出可执行的修复提示，不静默降级。"""
    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - 取决于解释器环境
        raise PixelError(
            "像素读取需要 Pillow，当前解释器没有安装。请改用钉死环境 "
            "`.venv-yoloe/bin/python`（接受轮 14 §26.2：不下载、不安装新包、"
            "不改依赖清单）。"
        ) from exc
    return Image


class ArchivePixelSource:
    """按仓库相对路径读取归档帧，兼作 `PixelSource` 与 `GraySource`。

    只读：本类不写任何文件，也不产生工件。
    """

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = Path(repo_root)
        # key = (相对路径, st_mtime_ns, st_size)：字节一变，缓存条目自然失效。
        # 不按路径单键缓存——陈旧缓存静默掩盖变化，正是复核轮 2/3 那一族
        # finding 的失败模式。
        self._cache: dict[tuple[str, int, int], tuple[int, int, bytes]] = {}
        self._order: list[tuple[str, int, int]] = []

    # --- 解码 ---------------------------------------------------------------
    def _resolve(self, frame_id: str) -> Path:
        path = self._repo_root / frame_id
        if not path.is_file():
            raise PixelError(f"帧字节不存在：{frame_id}")
        return path

    def _decode(self, frame_id: str) -> tuple[int, int, bytes]:
        """→ `(width, height, RGB 字节)`；同一帧在一次运行内只解码一次。"""
        path = self._resolve(frame_id)
        stat = path.stat()
        key = (frame_id, stat.st_mtime_ns, stat.st_size)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        image_module = _require_pillow()
        try:
            with image_module.open(path) as handle:
                converted = handle.convert("RGB")
                width, height = converted.size
                payload = converted.tobytes()
        except PixelError:
            raise
        except Exception as exc:  # 损坏字节、非图像、截断
            raise PixelError(f"帧解码失败：{frame_id}（{type(exc).__name__}）") from exc
        if width <= 0 or height <= 0 or len(payload) != width * height * 3:
            raise PixelError(
                f"帧解码结果不合法：{frame_id} {width}×{height} "
                f"字节 {len(payload)}（期望 {width * height * 3}）"
            )
        value = (width, height, payload)
        self._cache[key] = value
        self._order.append(key)
        while len(self._order) > DECODE_CACHE_FRAMES:
            self._cache.pop(self._order.pop(0), None)
        return value

    def dimensions(self, frame_id: str) -> tuple[int, int]:
        width, height, _ = self._decode(frame_id)
        return width, height

    # --- PixelSource --------------------------------------------------------
    def crop_rgb(
        self, frame_id: str, box_px: project_boxes.Rect
    ) -> Sequence[tuple[int, int, int]]:
        """框内像素的 RGB 列表；判据 = **像素中心落在框内**，再与图像边界求交。

        返回顺序按 (行, 列) 升序，确定性。空集返回空列表：`estimate_color`
        据此给出无主色 → `UNVERIFIED`，是 fail-closed 方向。
        """
        width, height, payload = self._decode(frame_id)
        x0, y0, x1, y1 = (float(value) for value in box_px)
        if not (x1 > x0 and y1 > y0):
            return []
        # 像素中心 i + 0.5 ∈ [x0, x1) → i ∈ [x0 - 0.5, x1 - 0.5)
        first_column = max(0, _ceil_index(x0 - 0.5))
        last_column = min(width - 1, _last_index(x1 - 0.5))
        first_row = max(0, _ceil_index(y0 - 0.5))
        last_row = min(height - 1, _last_index(y1 - 0.5))
        if last_column < first_column or last_row < first_row:
            return []
        pixels: list[tuple[int, int, int]] = []
        for row in range(first_row, last_row + 1):
            base = row * width * 3
            for column in range(first_column, last_column + 1):
                offset = base + column * 3
                pixels.append(
                    (payload[offset], payload[offset + 1], payload[offset + 2])
                )
        return pixels

    # --- GraySource ---------------------------------------------------------
    def gray_matrix(self, frame_id: str, size: int) -> Sequence[Sequence[float]]:
        """`size × size` 灰度矩阵：块内**整数**通道和 → 一次 luma → 除以块面积。

        不调用任何库的 `resize`：尺寸必须被 `size` 整除，块平均因此是确定的
        算术平均，与 Pillow 版本、滤波器与 SIMD 无关。不整除时硬失败——回退到
        插值会让 pHash 位随实现漂移，进而改变并簇、原子与切分。

        求值顺序刻意选成「先按通道求整数和，再算一次 luma」：luma 对 R/G/B
        是线性的，故 `mean(luma) == luma(mean)`，定义不变；但整数求和是**精确**
        的，浮点结合律不再参与，纯 Python 路径与 numpy 路径因此逐位相同
        （`test_gray_matrix_numpy_and_pure_python_paths_agree_bitwise` 钉死）。
        """
        if size <= 0:
            raise PixelError(f"灰度矩阵边长必须为正：{size}")
        width, height, payload = self._decode(frame_id)
        if width % size or height % size:
            raise PixelError(
                f"帧 {frame_id} 尺寸 {width}×{height} 不能被 {size} 整除，"
                "块平均不成立；本适配器不做插值重采样（会使 pHash 随实现漂移）"
            )
        sums = _channel_block_sums(payload, width, height, size)
        divisor = float((width // size) * (height // size))
        red_weight, green_weight, blue_weight = GRAYSCALE_COEFFICIENTS
        return [
            [
                (
                    red_weight * red + green_weight * green + blue_weight * blue
                )
                / divisor
                for red, green, blue in row
            ]
            for row in sums
        ]

    def phash(self, frame_id: str) -> int:
        """归档帧的 64 bit pHash（§2.5 冻结参数，算法在 `make_splits`）。"""
        from tools.dist_data import make_splits  # noqa: PLC0415 - 避免循环导入

        return make_splits.phash(self.gray_matrix(frame_id, contract.PHASH_RESIZE))


def _channel_block_sums(
    payload: bytes, width: int, height: int, size: int
) -> list[list[tuple[int, int, int]]]:
    """逐块的 `(ΣR, ΣG, ΣB)` **整数**和。numpy 在场时走它，结果逐位相同。"""
    block_width = width // size
    block_height = height // size
    try:
        import numpy  # noqa: PLC0415
    except ImportError:
        numpy = None
    if numpy is not None:
        array = numpy.frombuffer(payload, dtype=numpy.uint8).reshape(height, width, 3)
        # reshape 成 (行块, 块高, 列块, 块宽, 通道)，按 int64 精确求和。
        # `dtype=` 让累加直接在 int64 上做，不先物化一份 int64 副本。
        totals = array.reshape(size, block_height, size, block_width, 3).sum(
            axis=(1, 3), dtype=numpy.int64
        )
        return [
            [(int(cell[0]), int(cell[1]), int(cell[2])) for cell in row]
            for row in totals
        ]
    rows: list[list[tuple[int, int, int]]] = []
    for block_row in range(size):
        row_start = block_row * block_height
        row_totals: list[tuple[int, int, int]] = []
        for block_column in range(size):
            column_start = block_column * block_width
            red = green = blue = 0
            for row in range(row_start, row_start + block_height):
                base = row * width * 3
                for column in range(column_start, column_start + block_width):
                    offset = base + column * 3
                    red += payload[offset]
                    green += payload[offset + 1]
                    blue += payload[offset + 2]
            row_totals.append((red, green, blue))
        rows.append(row_totals)
    return rows


def _ceil_index(value: float) -> int:
    """最小的整数 i 使 i ≥ value。"""
    index = int(value)
    return index if index >= value else index + 1


def _last_index(bound: float) -> int:
    """最大的整数 i 使 i < bound。"""
    index = _ceil_index(bound) - 1
    return index


def describe() -> dict[str, Any]:
    """适配器的可复算参数（供实现者证据与复核角色对账，不入任何工件）。"""
    return {
        "grayscale_coefficients": list(GRAYSCALE_COEFFICIENTS),
        "grayscale_note": "ITU-R 601-2 luma，float 域，无整数截断",
        "downscale": "exact integer block mean; no interpolation, no resample filter",
        "crop_rule": "pixel centre inside the box: x0 <= i + 0.5 < x1, clipped to image",
        "phash_resize": contract.PHASH_RESIZE,
        "decode_cache_frames": DECODE_CACHE_FRAMES,
    }
