"""公共件：路径（仓库根 / 只读数据根 / 产物根）、受保护写入、分层键与复用 FAST-001 纯函数。

数据根：S3 帧目录、划分、清单与 FAST-001 缓存位于用户的完整数据副本（账本 2026-09-27
「数据位于 `~/TetheredDroneTracking-full`」）；环境变量 `ENG_DET_DATA_ROOT` 可覆盖。
数据根整体只读：本包任何写入落在数据根或任一 `runtime/` 下都结构性拒绝（AC-9）。

几何、IO、分桶（S <32 / M 32–63 / L ≥64 px）与 bootstrap 逐字复用 `tools.eng_fast.common`
（只导入、零字节改动，合同事实 10）。
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path
import sys
from typing import Any, Iterable, Iterator, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_det import WORK_ID  # noqa: E402
from tools.eng_fast import common as fast_common  # noqa: E402

DATA_ROOT = Path(os.environ.get("ENG_DET_DATA_ROOT", str(Path.home() / "TetheredDroneTracking-full"))).resolve()
OUT_ROOT = PROJECT_ROOT / "outputs" / "eng-det"
EVIDENCE_DIR = PROJECT_ROOT / "docs" / "evidence"
PROTECTED_ROOTS: tuple[Path, ...] = (PROJECT_ROOT / "runtime", DATA_ROOT)

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
MIN_SIDE_PX = 12.0  # = tools/dist_data/contract.MIN_VISIBLE_SIDE_PX（§3.1）

CLASS_VEHICLE = 0
CLASS_TARGET = 1
CLASS_NAMES = ("vehicle", "target")
POSITIVE_STATUSES = ("OK", "TRUNCATED", "EXCLUDED_OCCLUDED", "TOO_SMALL")

# 分层短边档（§3.1.2）与评估分桶（§3.3，复用 FAST-001 口径）是两套边界，不混用。
SIDE_BINS = ("12-31", "32-63", ">=64")

# 复用件（逐字导入）。
iou_xywh = fast_common.iou_xywh
xywh_to_xyxy = fast_common.xywh_to_xyxy
stratum_of = fast_common.stratum_of
distance_bin = fast_common.distance_bin
bootstrap_ci = fast_common.bootstrap_ci
quantiles = fast_common.quantiles
sha256_file = fast_common.sha256_file
sha256_bytes = fast_common.sha256_bytes
sha256_text = fast_common.sha256_text
json_bytes = fast_common.json_bytes
read_json = fast_common.read_json
read_jsonl = fast_common.read_jsonl
DISTANCE_BINS = fast_common.DISTANCE_BINS
STRATA = fast_common.STRATA


def evidence(name: str) -> Path:
    return EVIDENCE_DIR / f"{WORK_ID}-{name}"


def data_path(relative: str | Path) -> Path:
    candidate = Path(relative)
    return candidate if candidate.is_absolute() else DATA_ROOT / candidate


def rel_project(path: Path | str) -> str:
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return candidate.as_posix()


def refuse_protected(path: Path | str) -> None:
    """AC-9：数据根与 `runtime/` 只读（结构性拒绝，不靠事后比对）。"""
    target = Path(path)
    resolved = target.resolve() if target.exists() else target.parent.resolve() / target.name
    for root in PROTECTED_ROOTS:
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            continue
        raise PermissionError(f"只读根（AC-9）：拒绝写入 {path}")


def atomic_write_bytes(path: Path | str, payload: bytes) -> None:
    refuse_protected(path)
    fast_common.atomic_write_bytes(Path(path), payload)


def write_json(path: Path | str, value: Any) -> str:
    payload = json_bytes(value)
    atomic_write_bytes(path, payload)
    return sha256_bytes(payload)


def write_jsonl(path: Path | str, rows: Iterable[Mapping[str, Any]]) -> str:
    refuse_protected(path)
    return fast_common.write_jsonl(Path(path), rows)


def side_bin(short_px: float) -> str:
    if short_px < MIN_SIDE_PX:
        raise ValueError("short side below 12 px has no stratum (ignore)")
    if short_px < 32:
        return "12-31"
    if short_px < 64:
        return "32-63"
    return ">=64"


def short_side_px(box_norm: Sequence[float]) -> float:
    return min(float(box_norm[2]) * FRAME_WIDTH, float(box_norm[3]) * FRAME_HEIGHT)


def xyxy_px_to_norm(box: Sequence[float]) -> list[float] | None:
    """像素 xyxy 裁剪到画幅后归一化 top-left xywh；退化 → None。"""
    x1 = max(0.0, float(box[0]))
    y1 = max(0.0, float(box[1]))
    x2 = min(float(FRAME_WIDTH), float(box[2]))
    y2 = min(float(FRAME_HEIGHT), float(box[3]))
    if x2 <= x1 or y2 <= y1:
        return None
    return [x1 / FRAME_WIDTH, y1 / FRAME_HEIGHT, (x2 - x1) / FRAME_WIDTH, (y2 - y1) / FRAME_HEIGHT]


def ioa_xywh(det: Sequence[float], region: Sequence[float]) -> float:
    """交集 / 检测面积（§3.1.3 ignore 丢弃判据）。"""
    ax1, ay1, ax2, ay2 = xywh_to_xyxy(det)
    bx1, by1, bx2, by2 = xywh_to_xyxy(region)
    ix1, iy1, ix2, iy2 = max(ax1, bx1), max(ay1, by1), min(ax2, bx2), min(ay2, by2)
    area = (ax2 - ax1) * (ay2 - ay1)
    if ix2 <= ix1 or iy2 <= iy1 or area <= 0:
        return 0.0
    return (ix2 - ix1) * (iy2 - iy1) / area


@contextlib.contextmanager
def fast001_data_root() -> Iterator[None]:
    """临时把 `tools.eng_fast.common.PROJECT_ROOT` 指向数据根，以原样复用 FAST-001 的
    scout/BODY 序列加载器（其相对路径 `runtime/...` 均相对仓库根解析）。只读调用；退出即还原。"""
    original = fast_common.PROJECT_ROOT
    fast_common.PROJECT_ROOT = DATA_ROOT
    try:
        yield
    finally:
        fast_common.PROJECT_ROOT = original


def disk_usage_bytes(root: Path = OUT_ROOT) -> int:
    total = 0
    if not root.exists():
        return 0
    for directory, _dirs, files in os.walk(root):
        for name in files:
            path = Path(directory) / name
            if not path.is_symlink():
                total += path.stat().st_size
    return total
