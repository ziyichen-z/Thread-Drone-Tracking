"""公共件：路径、原子写、几何、分桶口径与 bootstrap（纯标准库）。

分桶口径逐字取自已接受合同 §3.1：短边 S <32 / M 32–64 / L ≥64 px（与
`tools/eng_sft/build_sft_data.stratum_of` 同式）；距离档 `<35` / `35–50` /
`50–65` / `≥65` m，斜距表与轴向深度表各用同一组边界但分表；IoU 口径并列
≥0.30 与 ≥0.50。
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
import tempfile
from typing import Any, Iterable, Iterator, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_fast import WORK_ID  # noqa: E402

OUT_ROOT = PROJECT_ROOT / "outputs" / "eng-fast" / WORK_ID
EVIDENCE_DIR = PROJECT_ROOT / "docs" / "evidence"
RUNTIME_ROOT = PROJECT_ROOT / "runtime"

FRAME_WIDTH = 640
FRAME_HEIGHT = 480

IOU_THRESHOLDS: tuple[float, ...] = (0.30, 0.50)
DETECTOR_CONFIDENCE_MIN = 0.25  # DETECT-001 冻结阈值（§2.2-5 不调参）
DISTANCE_BINS: tuple[str, ...] = ("<35", "35-50", "50-65", ">=65")
STRATA: tuple[str, ...] = ("S", "M", "L")
BOOTSTRAP_ROUNDS = 2000
BOOTSTRAP_SEED = 20260923

TARGET_KIND_CATALOG = "catalog_vehicle"
TARGET_KIND_PRIMITIVE = "red_primitive"


# --- 路径与 IO ------------------------------------------------------------


def rel(path: Path | str) -> str:
    """仓库相对路径（POSIX）；仓库外的路径原样返回绝对值。"""
    candidate = Path(path)
    if not candidate.is_absolute():
        return candidate.as_posix()
    try:
        return candidate.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return candidate.as_posix()


def absolute(path: Path | str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with open(absolute(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode(
        "utf-8"
    )


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path = absolute(path)
    _refuse_runtime(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def write_json(path: Path, value: Any) -> str:
    payload = json_bytes(value)
    atomic_write_bytes(path, payload)
    return sha256_bytes(payload)


def read_json(path: Path | str) -> Any:
    return json.loads(absolute(path).read_text(encoding="utf-8"))


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    path = absolute(path)
    opener = gzip.open if path.suffix == ".gz" else open
    rows: list[dict[str, Any]] = []
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> str:
    lines = [json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) for row in rows]
    payload = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    if absolute(path).suffix == ".gz":
        payload = gzip.compress(payload, mtime=0)
    atomic_write_bytes(path, payload)
    return sha256_bytes(payload)


def _refuse_runtime(path: Path) -> None:
    """AC-9：本包任何写入都不得落在 `runtime/` 下（结构性拒绝，不靠事后比对）。"""
    resolved = path.resolve() if path.exists() else path.parent.resolve() / path.name
    try:
        resolved.relative_to(RUNTIME_ROOT.resolve())
    except ValueError:
        return
    raise PermissionError(f"runtime/ 只读（AC-9）：拒绝写入 {path}")


# --- 几何 -----------------------------------------------------------------


def xywh_to_xyxy(box: Sequence[float]) -> tuple[float, float, float, float]:
    return (float(box[0]), float(box[1]), float(box[0]) + float(box[2]), float(box[1]) + float(box[3]))


def xyxy_to_xywh(box: Sequence[float]) -> tuple[float, float, float, float]:
    return (float(box[0]), float(box[1]), float(box[2]) - float(box[0]), float(box[3]) - float(box[1]))


def iou_xywh(left: Sequence[float], right: Sequence[float]) -> float:
    ax1, ay1, ax2, ay2 = xywh_to_xyxy(left)
    bx1, by1, bx2, by2 = xywh_to_xyxy(right)
    ix1, iy1, ix2, iy2 = max(ax1, bx1), max(ay1, by1), min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    intersection = (ix2 - ix1) * (iy2 - iy1)
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - intersection
    return intersection / union if union > 0 else 0.0


def box_from_truth(value: Any) -> tuple[float, float, float, float] | None:
    """真值框两种 schema：`{x,y,width,height}` 对象或四元序列；非有限/非正面积 → None。"""
    if value is None:
        return None
    if isinstance(value, Mapping):
        if set(value) != {"x", "y", "width", "height"}:
            raise ValueError(f"truth box keys {sorted(value)}")
        raw = (value["x"], value["y"], value["width"], value["height"])
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) == 4:
        raw = tuple(value)
    else:
        raise ValueError(f"unsupported truth box {value!r}")
    box = tuple(float(item) for item in raw)
    if not all(math.isfinite(item) for item in box) or box[2] <= 0 or box[3] <= 0:
        return None
    return box  # type: ignore[return-value]


def short_side_px(box_norm: Sequence[float], width: int = FRAME_WIDTH, height: int = FRAME_HEIGHT) -> float:
    return min(float(box_norm[2]) * width, float(box_norm[3]) * height)


def stratum_of(px: float | None) -> str:
    if px is None:
        return "NA"
    if px < 32:
        return "S"
    if px < 64:
        return "M"
    return "L"


def distance_bin(metres: float | None) -> str:
    if metres is None or not math.isfinite(metres):
        return "NA"
    if metres < 35.0:
        return "<35"
    if metres < 50.0:
        return "35-50"
    if metres < 65.0:
        return "50-65"
    return ">=65"


# --- 统计 -----------------------------------------------------------------


def bootstrap_ci(
    outcomes: Sequence[bool | int], rounds: int = BOOTSTRAP_ROUNDS, seed: int = BOOTSTRAP_SEED
) -> list[float] | None:
    """二值序列均值的百分位 bootstrap 95% 区间（描述性，§6.1-7）。"""
    values = [1 if bool(item) else 0 for item in outcomes]
    n = len(values)
    if n == 0:
        return None
    rng = random.Random(seed)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(rounds))
    low = means[int(math.floor(0.025 * (rounds - 1)))]
    high = means[int(math.ceil(0.975 * (rounds - 1)))]
    return [round(low, 6), round(high, 6)]


def quantiles(values: Sequence[float], points: Sequence[float] = (0.05, 0.5, 0.95)) -> dict[str, float | None]:
    ordered = sorted(float(value) for value in values)
    result: dict[str, float | None] = {}
    for point in points:
        key = f"p{int(round(point * 100))}"
        if not ordered:
            result[key] = None
            continue
        position = point * (len(ordered) - 1)
        low, high = int(math.floor(position)), int(math.ceil(position))
        fraction = position - low
        result[key] = round(ordered[low] + (ordered[high] - ordered[low]) * fraction, 6)
    return result


def iter_chunks(items: Sequence[Any], size: int) -> Iterator[Sequence[Any]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]
