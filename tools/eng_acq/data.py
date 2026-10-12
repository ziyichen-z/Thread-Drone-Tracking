"""三序列帧、sidecar、冻结检测缓存与真值索引（§3.9；账本 09-28 D.7：只用 scout-1、m3-armA、a7）。

- 帧：冻结缓存 `frozen-B`（scout-1 768 + m3-armA 7 段 × 128）与 `frozen-V`（a7 3,168）的帧列表，按帧目录分段
  （m3-armA 每段一个会话；E1 的解析帧 r 只在同段内找），段内按文件名帧号排序。
- 传感器帧号 = 文件名帧号（sidecar `frame_id` 必须相同，否则停）；时刻 = sidecar `simulation_time_s`
  （与 FAST-001 `catalog-sim-times` 相差 > 1 ms 即停）。
- 真值（只进样本构造与评分）：FAST-001 `catalog-index` 的 `OK` 静止车 `vehicles[]` 与 `dynamic` 红车
  （`definite` 且有框），`usable=false` 的帧视为无可见对象。
- JPEG 完整性：读取字节时与 FAST-002 数据集清单 `P1-ENG-FAST-002-dataset-frames.jsonl.gz` 的逐帧 sha256
  比对，不一致即停（H-2，AC-9）。
"""

from __future__ import annotations

from dataclasses import dataclass
import functools
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.eng_acq import common

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
RED_ID = "__red__"

CACHE_B = common.PROJECT_ROOT / "outputs" / "eng-det" / "dets" / "frozen-B.jsonl.gz"
CACHE_V = common.PROJECT_ROOT / "outputs" / "eng-det" / "dets" / "frozen-V.jsonl.gz"
SPEC = common.PROJECT_ROOT / "config" / "det-assoc-v1.models.json"
FREEZE = common.PROJECT_ROOT / "docs" / "evidence" / "P1-ENG-FAST-002-freeze.json"
DATASET_FRAMES = common.PROJECT_ROOT / "docs" / "evidence" / "P1-ENG-FAST-002-dataset-frames.jsonl.gz"
INDEX = "outputs/eng-fast/P1-ENG-FAST-001/cache/catalog-index.jsonl.gz"
SIM_TIMES = "outputs/eng-fast/P1-ENG-FAST-001/cache/catalog-sim-times.jsonl.gz"
NANOTRACK_DIR = "runtime/models/nanotrack-v2"

SCOUT1 = "runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames"
A7 = "runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames"
M3_ARM_A = (
    "runtime/test-results/p1-m3-body-001-arm-a-trial-1-attempt-4-post-run/frames",
    "runtime/test-results/p1-m3-body-001-arm-a-trial-2-attempt-2-post-run/frames",
    "runtime/test-results/p1-m3-body-001-arm-a-trial-3-post-run/frames",
    "runtime/test-results/p1-m3-body-001-arm-a-trial-4-post-run/frames",
    "runtime/test-results/p1-m3-body-001-arm-a-trial-5-post-run/frames",
    "runtime/frames.arm-a-trial-1-void-attempt-3-hold",
    "runtime/frames.arm-a-trial-2-void-attempt-1-hold",
)
SEQUENCES: dict[str, dict[str, Any]] = {
    "scout-1": {"segments": (SCOUT1,), "cache": "B", "tag": "TRAINED_ON_ATOM"},
    "m3-armA": {"segments": M3_ARM_A, "cache": "B", "tag": "TRAINED_ON_ATOM"},
    "a7": {"segments": (A7,), "cache": "V", "tag": "SELECTION_DOMAIN"},
}
SIM_TIME_TOLERANCE_S = 1e-3


class IntegrityStop(RuntimeError):
    """帧 sha / sidecar 帧号 / 时刻与来源不一致：停下并报告（H-2；不销账）。"""


@dataclass(frozen=True)
class Frame:
    sequence: str
    segment: str
    frame_id: int
    path: str  # 数据根相对路径（JPEG）
    sim_t: float
    metadata: Mapping[str, Any]
    dets: tuple[tuple[float, ...], ...]
    statics: tuple[tuple[str, tuple[float, float, float, float]], ...]
    red: tuple[float, float, float, float] | None
    jpeg_sha256: str | None

    def objects(self) -> dict[str, tuple[float, float, float, float]]:
        out = {object_id: box for object_id, box in self.statics}
        if self.red is not None:
            out[RED_ID] = self.red
        return out


def _read_cache(path: Path) -> tuple[dict[str, Any], dict[str, list[list[float]]]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        header = json.loads(handle.readline())["header"]
        rows = {}
        for line in handle:
            item = json.loads(line)
            rows[item["frame_id"]] = item["dets"]
    return header, rows


def frame_number(path: str) -> int:
    return int(Path(path).stem.split("_")[1])


@functools.lru_cache(maxsize=1)
def _manifest_shas() -> dict[str, str]:
    with gzip.open(DATASET_FRAMES, "rt", encoding="utf-8") as handle:
        return {row["frame_id"]: row["sha256"] for row in map(json.loads, handle)}


def _read_index(frame_ids: set[str]) -> tuple[dict[str, Any], dict[str, float]]:
    index: dict[str, Any] = {}
    with gzip.open(common.data_path(INDEX), "rt", encoding="utf-8") as handle:
        handle.readline()
        for line in handle:
            row = json.loads(line)
            if row["frame_id"] in frame_ids:
                index[row["frame_id"]] = row
    times: dict[str, float] = {}
    with gzip.open(common.data_path(SIM_TIMES), "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("frame_id") in frame_ids:
                times[row["frame_id"]] = float(row["t"])
    return index, times


def _truth(row: Mapping[str, Any] | None) -> tuple[tuple[tuple[str, tuple[float, ...]], ...], tuple[float, ...] | None]:
    if not row or not row.get("usable"):
        return (), None
    statics = tuple(sorted((v["object_id"], tuple(float(x) for x in v["box"])) for v in row.get("vehicles", [])))
    dynamic = row.get("dynamic")
    red = tuple(float(x) for x in dynamic["box"]) if dynamic and dynamic.get("definite") and dynamic.get("box") else None
    return statics, red  # type: ignore[return-value]


def load_sequences(names: Iterable[str] = tuple(SEQUENCES)) -> dict[str, list[list[Frame]]]:
    """→ {序列: [段: [Frame…]]}；任一完整性不符即 `IntegrityStop`。"""
    spec = common.read_json(SPEC)
    weights_sha = spec["weights"]["sha256"]
    caches = {}
    for key, path in (("B", CACHE_B), ("V", CACHE_V)):
        header, rows = _read_cache(path)
        if header.get("weights_sha256") != weights_sha or float(header.get("conf")) != 0.25 or int(header.get("imgsz")) != 640:
            raise IntegrityStop(f"cache {path.name} header does not match frozen spec: {header}")
        caches[key] = rows
    names = tuple(names)
    wanted = {fid for name in names for fid in caches[SEQUENCES[name]["cache"]] if any(fid.startswith(seg + "/") for seg in SEQUENCES[name]["segments"])}
    index, times = _read_index(wanted)
    shas = _manifest_shas()
    result: dict[str, list[list[Frame]]] = {}
    for name in names:
        config = SEQUENCES[name]
        rows = caches[config["cache"]]
        segments: list[list[Frame]] = []
        for segment in config["segments"]:
            ids = sorted((fid for fid in rows if fid.startswith(segment + "/")), key=frame_number)
            if not ids:
                raise IntegrityStop(f"segment {segment} has no cached frames")
            frames: list[Frame] = []
            for fid in ids:
                number = frame_number(fid)
                sidecar_path = common.data_path(fid).with_suffix(".json")
                metadata = json.loads(sidecar_path.read_text(encoding="utf-8"))
                if int(metadata.get("frame_id", -1)) != number:
                    raise IntegrityStop(f"{fid}: sidecar frame_id {metadata.get('frame_id')} ≠ file number {number}")
                sim_t = float(metadata["simulation_time_s"])
                if fid not in times or abs(times[fid] - sim_t) > SIM_TIME_TOLERANCE_S:
                    raise IntegrityStop(f"{fid}: sidecar simulation_time_s {sim_t} ≠ catalog {times.get(fid)}")
                if fid not in index:
                    raise IntegrityStop(f"{fid}: missing from catalog index")
                statics, red = _truth(index[fid])
                frames.append(
                    Frame(name, segment, number, fid, sim_t, metadata, tuple(tuple(float(v) for v in d) for d in rows[fid]), statics, red, shas.get(fid))
                )
            for left, right in zip(frames, frames[1:]):
                if right.frame_id <= left.frame_id or right.sim_t <= left.sim_t:
                    raise IntegrityStop(f"{segment}: frame ids/times not strictly increasing at {right.path}")
            segments.append(frames)
        result[name] = segments
    return result


def read_jpeg_bytes(frame: Frame) -> bytes:
    payload = common.data_path(frame.path).read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    if frame.jpeg_sha256 is None or actual != frame.jpeg_sha256:
        raise IntegrityStop(f"{frame.path}: JPEG sha256 {actual} ≠ manifest {frame.jpeg_sha256}")
    return payload


class ImageCache:
    """按帧路径解码（先核 sha 再解码）；LRU 限制驻留帧数。"""

    def __init__(self, capacity: int = 192):
        self.capacity = capacity
        self._items: dict[str, Any] = {}
        self.decodes = 0

    def get(self, frame: Frame) -> Any:
        if frame.path in self._items:
            image = self._items.pop(frame.path)
            self._items[frame.path] = image
            return image
        import cv2  # noqa: PLC0415
        import numpy as np  # noqa: PLC0415

        payload = read_jpeg_bytes(frame)
        image = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise IntegrityStop(f"{frame.path}: JPEG could not be decoded")
        self.decodes += 1
        self._items[frame.path] = image
        while len(self._items) > self.capacity:
            self._items.pop(next(iter(self._items)))
        return image


def verify_all_jpegs(sequences: Mapping[str, Sequence[Sequence[Frame]]]) -> dict[str, Any]:
    checked = 0
    for segments in sequences.values():
        for frames in segments:
            for frame in frames:
                read_jpeg_bytes(frame)
                checked += 1
    return {"jpeg_sha_checked": checked, "mismatches": 0}


def short_side_px(box: Sequence[float]) -> float:
    return min(float(box[2]) * FRAME_WIDTH, float(box[3]) * FRAME_HEIGHT)


def size_bin(box: Sequence[float]) -> str:
    """k 帧真值框短边：S < 32 / M 32–63 / L ≥ 64 px（§3.9）。"""
    side = short_side_px(box)
    if side < 32:
        return "S"
    if side < 64:
        return "M"
    return "L"
