"""桌面机 5 Hz 回放器（合同 §3.2「运行目录」、SR）：把 a7 帧按 v3 合同重发布到独立运行目录。

- 源帧只读（数据根或本机主树同一相对路径的 a7 `frames/`）；JPEG 字节不改；
- 元数据：逐字沿用原 sidecar，只改写 `frame_id`（从 0 递增）、`capture_unix_s` 与 `capture_monotonic_s`
  （取桌面机当下 `time.time()` / `time.monotonic()`）；`capture_monotonic_clock_id` 逐字沿用；
- 发布顺序与 Unity 侧同语义：先两成员（各自临时文件 + rename），后原子发布 `frames/latest.json`
  （`tethered-frame-manifest/v1`，`published_unix_s` 取桌面机墙钟）；
- 保留最近 `retain` 帧（缺省 128，对齐 `config/scenario.default.json` `retained_frame_count`），更旧成员删除；
- 运行目录只能在 `outputs/eng-jet/` 下（主树 `runtime/` 与数据根结构性拒绝，AC-12）。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import time
from typing import Any, Callable, Sequence

from tools.eng_jet import common

MANIFEST_SCHEMA = "tethered-frame-manifest/v1"
FRAME_SCHEMA = "tethered-sensor-frame/v3"
RETAIN = 128


def _safe_runtime(runtime: Path) -> Path:
    runtime = Path(runtime).expanduser()
    common.refuse_protected(runtime)
    return runtime


def reset_runtime(runtime: Path) -> None:
    """清空本回放器自己的运行目录（只允许 `outputs/eng-jet/` 下或测试临时目录；受保护根拒绝）。"""
    runtime = common.require_scratch(runtime)
    if runtime.exists():
        shutil.rmtree(runtime)
    (runtime / "frames").mkdir(parents=True, exist_ok=True)


def rewrite_metadata(source: dict[str, Any], frame_id: int, capture_unix_s: float, capture_monotonic_s: float) -> dict[str, Any]:
    if source.get("schema_version") != FRAME_SCHEMA:
        raise ValueError(f"源帧不是 v3：{source.get('schema_version')!r}")
    out = dict(source)
    out["frame_id"] = int(frame_id)
    out["capture_unix_s"] = round(float(capture_unix_s), 6)
    out["capture_monotonic_s"] = round(float(capture_monotonic_s), 6)
    return out


def publish_frame(runtime: Path, frame_id: int, jpeg: bytes, metadata: dict[str, Any], *, fsync: bool = False,
                  now: Callable[[], float] = time.time) -> dict[str, Any]:
    frames = _safe_runtime(runtime) / "frames"
    image_name, meta_name = common.frame_name(frame_id, "jpg"), common.frame_name(frame_id, "json")
    meta_bytes = (json.dumps(metadata, indent=4) + "\n").encode("utf-8")
    common.atomic_write_bytes(frames / image_name, jpeg, fsync=fsync)
    common.atomic_write_bytes(frames / meta_name, meta_bytes, fsync=fsync)
    published = now()
    manifest = {"schema_version": MANIFEST_SCHEMA, "frame_id": int(frame_id), "image_file": image_name,
                "metadata_file": meta_name, "published_unix_s": round(published, 6)}
    manifest_bytes = (json.dumps(manifest, indent=4) + "\n").encode("utf-8")
    common.atomic_write_bytes(frames / "latest.json", manifest_bytes, fsync=fsync)
    return {"frame_id": int(frame_id), "published_unix_s": manifest["published_unix_s"], "image_sha256": common.sha256_bytes(jpeg),
            "metadata_sha256": common.sha256_bytes(meta_bytes), "manifest_sha256": common.sha256_bytes(manifest_bytes),
            "image_bytes": len(jpeg), "metadata_bytes": len(meta_bytes), "manifest_bytes": len(manifest_bytes)}


def prune(runtime: Path, newest_frame_id: int, retain: int = RETAIN) -> int:
    frames = _safe_runtime(runtime) / "frames"
    removed = 0
    oldest = newest_frame_id - retain
    if oldest < 0:
        return 0
    for suffix in ("jpg", "json"):
        path = frames / common.frame_name(oldest, suffix)
        if path.exists():
            path.unlink()
            removed += 1
    return removed


def replay(source_dir: Path, runtime: Path, count: int, hz: float, receipts: Path, *, start_index: int = 0,
           retain: int = RETAIN, reset: bool = True, sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """按 `t0 + k/hz` 节拍发布 `count` 帧；逐帧收据（源帧号、桌面机发布时刻、节拍滞后）写 `receipts`。"""
    source_dir = Path(source_dir)
    if reset:
        reset_runtime(runtime)
    common.refuse_protected(receipts)
    late = []
    t0_mono = time.monotonic()
    for k in range(count):
        due = t0_mono + k / hz
        delay = due - time.monotonic()
        if delay > 0:
            sleep(delay)
        src = start_index + k
        jpeg = (source_dir / common.frame_name(src, "jpg")).read_bytes()
        source_meta = json.loads((source_dir / common.frame_name(src, "json")).read_text(encoding="utf-8"))
        capture_unix, capture_mono = time.time(), time.monotonic()
        metadata = rewrite_metadata(source_meta, k, capture_unix, capture_mono)
        receipt = publish_frame(runtime, k, jpeg, metadata)
        lag_ms = (time.monotonic() - due) * 1000.0
        late.append(lag_ms)
        prune(runtime, k, retain)
        common.append_jsonl(receipts, {**receipt, "source_index": src, "capture_unix_s": metadata["capture_unix_s"],
                                       "capture_monotonic_s": metadata["capture_monotonic_s"], "lag_ms": round(lag_ms, 3)})
    return {"frames": count, "hz": hz, "lag_ms": common.summary(late)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=None, help="a7 frames 目录（缺省：数据根或本机主树同一相对路径）")
    parser.add_argument("--runtime", type=Path, default=common.RUNTIME_DESKTOP)
    parser.add_argument("--count", type=int, default=1500)
    parser.add_argument("--hz", type=float, default=5.0)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--delay-start-s", type=float, default=0.0)
    args = parser.parse_args(argv)
    if args.delay_start_s > 0:
        time.sleep(args.delay_start_s)
    source = args.source or common.a7_frames_dir()
    print(json.dumps(replay(source, args.runtime, args.count, args.hz, args.receipts, start_index=args.start_index)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
