"""D2 训练（合同 §3.2、AC-2；线 A：Mac `.venv-yoloe`，MPS）。

- 基座：官方 COCO `yolo11n.pt`（`BASE_URL`，§5 下载 ≤ 1 次；先扣账再下载，sha256 与字节数入账）。
- 导出：最终数据集索引 → ultralytics 目录（`outputs/eng-det/yolo/`，不入库）。
  训练 = T 保留帧按会话时间序每 2 帧取 1；训练期 val = V 每 5 帧取 1（只驱动库的 val 曲线）。
  §3.1.3：(ii)(iii)(iv) ignore 框在派生副本上用该图均值色填充（PNG 无损写出，原图不动）；(i) 不填充。
  实现读法 IR-3：填充后把落在正样本框内的像素还原（ignore 框与正样本框相交时不毁正样本）。
- run：每 run 先扣 `training_run`，再「计时 epoch」（epochs=1 独立目录）得 `t_epoch`，
  `epochs = min(40, floor(墙钟上限 / t_epoch))`，并收紧到「计时 + epochs × t_epoch ≤ 6 h」（IR-2）；
  随后从基座重新开训 `epochs` 轮，`patience=0`（库内 = 不早停）、`amp=False`、`flipud=0`、
  batch 16（OOM → 8 → 4，同一 run 内）、seed 20260926、`plots=False`（避免库下载字体）。
- 权重：每 run 取 `last.pt`（sha256 与字节数入账），不取 `best.pt`。
- 冻结后禁止训练：冻结文件存在即拒绝开 run（AC-13）。
"""

from __future__ import annotations

import datetime as _dt
import json
import math
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any, Mapping, Sequence

from tools.eng_det import common, dataset
from tools.eng_det.ledger import EnvelopeExceeded, Ledger

BASE_URL = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt"
BASE_BYTES_PUBLISHED = 5_613_764  # GitHub 发布 API 的 size（不公布 sha256）
WEIGHTS_DIR = common.OUT_ROOT / "weights"
BASE_WEIGHTS = WEIGHTS_DIR / "yolo11n.pt"
YOLO_DIR = common.OUT_ROOT / "yolo"
RUNS_DIR = common.OUT_ROOT / "runs"
TRAIN_EVIDENCE = common.evidence("train.json")
FREEZE_EVIDENCE = common.evidence("freeze.json")

SEED = 20260926
BATCH_LADDER = (16, 8, 4)
EPOCH_CAP = 40
FILL_WHY = ("ii_phantom", "iii_stratum", "iv_truth_invisible")
WORKERS = 4


class TrainingRefused(RuntimeError):
    """冻结后开 run、信封越界或前置条件缺失。"""


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_train_evidence() -> dict[str, Any]:
    if TRAIN_EVIDENCE.exists():
        return common.read_json(TRAIN_EVIDENCE)
    return {"work_id": common.WORK_ID, "schema_version": "p1-eng-fast-002-train/v1", "runs": []}


def save_train_evidence(document: Mapping[str, Any]) -> None:
    common.write_json(TRAIN_EVIDENCE, document)


# --- 基座权重 ---------------------------------------------------------------


def ensure_base_weights(ledger: Ledger | None = None) -> dict[str, Any]:
    """已下载则只核对；否则先扣 `download` 再下载一次（失败也已计数，§5「成功、失败、重试同扣」）。"""
    ledger = ledger or Ledger()
    if BASE_WEIGHTS.exists():
        size = BASE_WEIGHTS.stat().st_size
        return {"path": common.rel_project(BASE_WEIGHTS), "bytes": size, "sha256": common.sha256_file(BASE_WEIGHTS)}
    ledger.charge("download", 1, what="yolo11n.pt", url=BASE_URL)
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    partial = BASE_WEIGHTS.with_suffix(".part")
    result = subprocess.run(
        ["curl", "-fL", "--retry", "0", "-o", str(partial), BASE_URL], capture_output=True, text=True, timeout=600
    )
    if result.returncode != 0:
        ledger.note("download_failed", url=BASE_URL, stderr=result.stderr[-400:])
        raise TrainingRefused(f"yolo11n.pt 下载失败（已计 1 次）：{result.stderr[-200:]}")
    size = partial.stat().st_size
    digest = common.sha256_file(partial)
    partial.rename(BASE_WEIGHTS)
    ledger.note(
        "download_done",
        url=BASE_URL,
        bytes=size,
        sha256=digest,
        bytes_published=BASE_BYTES_PUBLISHED,
        bytes_match=size == BASE_BYTES_PUBLISHED,
    )
    if size != BASE_BYTES_PUBLISHED:
        raise TrainingRefused(f"yolo11n.pt 字节数 {size} ≠ 官方发布 {BASE_BYTES_PUBLISHED}")
    return {"path": common.rel_project(BASE_WEIGHTS), "bytes": size, "sha256": digest}


# --- ultralytics 目录导出 -----------------------------------------------------


def image_name(frame_id: str) -> str:
    return frame_id.replace("/", "__").rsplit(".", 1)[0]


def label_lines(row: Mapping[str, Any]) -> list[str]:
    lines = []
    for p in row["positives"]:
        x, y, w, h = p["box"]
        lines.append(f"{p['cls']} {x + w / 2:.6f} {y + h / 2:.6f} {w:.6f} {h:.6f}")
    return lines


def fill_regions(row: Mapping[str, Any]) -> list[list[float]]:
    return [i["box"] for i in row["ignores"] if i["why"] in FILL_WHY]


def filled_image(image: Any, fills: Sequence[Sequence[float]], positives: Sequence[Sequence[float]]) -> tuple[Any, int]:
    """均值色填充 ignore 矩形，再还原正样本框内像素（IR-3）。返回 (图, 与正样本相交的填充框数)。"""
    height, width = image.shape[:2]
    mean = image.reshape(-1, image.shape[2]).mean(axis=0).round().astype(image.dtype)
    out = image.copy()

    def px(box: Sequence[float]) -> tuple[int, int, int, int]:
        x1 = max(0, int(math.floor(box[0] * width)))
        y1 = max(0, int(math.floor(box[1] * height)))
        x2 = min(width, int(math.ceil((box[0] + box[2]) * width)))
        y2 = min(height, int(math.ceil((box[1] + box[3]) * height)))
        return x1, y1, x2, y2

    for box in fills:
        x1, y1, x2, y2 = px(box)
        out[y1:y2, x1:x2] = mean
    overlaps = 0
    for box in fills:
        if any(common.iou_xywh(box, p) > 0 for p in positives):
            overlaps += 1
    for box in positives:
        x1, y1, x2, y2 = px(box)
        out[y1:y2, x1:x2] = image[y1:y2, x1:x2]
    return out, overlaps


def export_yolo() -> dict[str, Any]:
    import cv2  # noqa: PLC0415

    identity, rows = dataset.load_index()
    train_rows = [r for r in dataset.subsample([r for r in rows if r["domain"] == "T"], dataset.TRAIN_STRIDE)]
    val_rows = [r for r in dataset.subsample([r for r in rows if r["domain"] == "V"], dataset.VAL_STRIDE)]
    if YOLO_DIR.exists():
        shutil.rmtree(YOLO_DIR)
    stats: dict[str, Any] = {}
    label_digest_parts = []
    for split, subset in (("train", train_rows), ("val", val_rows)):
        image_dir = YOLO_DIR / "images" / split
        label_dir = YOLO_DIR / "labels" / split
        image_dir.mkdir(parents=True)
        label_dir.mkdir(parents=True)
        filled = linked = overlap_boxes = fill_boxes = 0
        positives = {"vehicle": 0, "target": 0}
        for row in subset:
            name = image_name(row["frame_id"])
            lines = label_lines(row)
            (label_dir / f"{name}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
            label_digest_parts.append(f"{split}|{name}|" + ";".join(lines))
            for p in row["positives"]:
                positives[common.CLASS_NAMES[p["cls"]]] += 1
            fills = fill_regions(row)
            source = common.data_path(row["frame_id"])
            if fills:
                image = cv2.imread(str(source), cv2.IMREAD_COLOR)
                if image is None:
                    raise TrainingRefused(f"无法读取 {row['frame_id']}")
                out, overlaps = filled_image(image, fills, [p["box"] for p in row["positives"]])
                cv2.imwrite(str(image_dir / f"{name}.png"), out)
                filled += 1
                fill_boxes += len(fills)
                overlap_boxes += overlaps
            else:
                (image_dir / f"{name}.jpg").symlink_to(source)
                linked += 1
        stats[split] = {
            "images": len(subset),
            "filled_png": filled,
            "symlinked_original": linked,
            "fill_boxes": fill_boxes,
            "fill_boxes_overlapping_positive_restored": overlap_boxes,
            "positives": positives,
            "families": dict(sorted({r["family"]: 0 for r in subset}.items())),
        }
        for r in subset:
            stats[split]["families"][r["family"]] += 1
    data_yaml = YOLO_DIR / "data.yaml"
    data_yaml.write_text(
        f"path: {YOLO_DIR}\ntrain: images/train\nval: images/val\nnames:\n  0: vehicle\n  1: target\n", encoding="utf-8"
    )
    return {
        "at": _now(),
        "index_sha256": common.sha256_file(dataset.INDEX_PATH),
        "catalog_manifest_sha256": identity["catalog_manifest_sha256"],
        "train_stride": dataset.TRAIN_STRIDE,
        "val_stride": dataset.VAL_STRIDE,
        "fill_why": list(FILL_WHY),
        "fill_color": "该图逐通道均值（四舍五入）",
        "labels_sha256": common.sha256_text("\n".join(label_digest_parts)),
        "data_yaml": common.rel_project(data_yaml),
        "splits": stats,
    }


# --- run --------------------------------------------------------------------


def _train_once(model_path: str, *, name: str, epochs: int, imgsz: int, batch: int, device: str) -> tuple[Path, float]:
    from ultralytics import YOLO  # noqa: PLC0415

    started = time.perf_counter()
    model = YOLO(model_path)
    model.train(
        data=str(YOLO_DIR / "data.yaml"),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        seed=SEED,
        deterministic=True,
        device=device,
        amp=False,
        patience=0,
        flipud=0.0,
        plots=False,
        workers=WORKERS,
        project=str(RUNS_DIR),
        name=name,
        exist_ok=False,
        verbose=False,
    )
    return RUNS_DIR / name, time.perf_counter() - started


def _is_oom(exc: BaseException) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    return "out of memory" in text or "mps backend out of memory" in text


def run(run_id: str, imgsz: int, reason: str, device: str = "mps") -> dict[str, Any]:
    if FREEZE_EVIDENCE.exists():
        raise TrainingRefused("冻结文件已存在：本项内禁止任何训练（AC-13）")
    ledger = Ledger()
    base = ensure_base_weights(ledger)
    document = load_train_evidence()
    if any(r["run_id"] == run_id for r in document["runs"]):
        raise TrainingRefused(f"{run_id} 已存在（run 只增不改）")
    if "dataset_export" not in document:
        raise TrainingRefused("先 export")
    remaining = ledger.remaining_training_wall_s()
    ledger.charge("training_run", 1, run_id=run_id, imgsz=imgsz, reason=reason)
    record: dict[str, Any] = {
        "run_id": run_id,
        "reason": reason,
        "imgsz": imgsz,
        "seed": SEED,
        "device": device,
        "amp": False,
        "base_weights": base,
        "started_at": _now(),
        "status": "RUNNING",
        "wall_cap_s": remaining,
        "batch_attempts": [],
    }
    document["runs"].append(record)
    save_train_evidence(document)
    run_started = time.perf_counter()

    def persist() -> None:
        doc = load_train_evidence()
        doc["runs"] = [record if r["run_id"] == run_id else r for r in doc["runs"]]
        save_train_evidence(doc)

    try:
        batch = None
        timing_wall = None
        for candidate in BATCH_LADDER:
            name = f"{run_id}-timing-b{candidate}"
            try:
                _dir, timing_wall = _train_once(str(BASE_WEIGHTS), name=name, epochs=1, imgsz=imgsz, batch=candidate, device=device)
                record["batch_attempts"].append({"phase": "timing", "batch": candidate, "result": "ok", "wall_s": round(timing_wall, 3)})
                batch = candidate
                break
            except Exception as exc:  # noqa: BLE001
                record["batch_attempts"].append({"phase": "timing", "batch": candidate, "result": f"{type(exc).__name__}: {str(exc)[:300]}"})
                persist()
                if not _is_oom(exc):
                    raise
        if batch is None or timing_wall is None:
            raise TrainingRefused("batch 16/8/4 均 OOM：停下回用户（§3.2）")
        t_epoch = timing_wall
        literal = min(EPOCH_CAP, math.floor(remaining / t_epoch))
        tightened = min(literal, math.floor((remaining - timing_wall) / t_epoch))
        record.update({"batch": batch, "t_epoch_s": round(t_epoch, 3), "epochs_literal": literal, "epochs": tightened})
        persist()
        if tightened < 5:
            raise TrainingRefused(f"epochs {tightened} < 5：停下回用户（§6.2）")
        run_dir, main_wall = _train_once(str(BASE_WEIGHTS), name=run_id, epochs=tightened, imgsz=imgsz, batch=batch, device=device)
        last = run_dir / "weights" / "last.pt"
        record.update(
            {
                "status": "DONE",
                "run_dir": common.rel_project(run_dir),
                "main_wall_s": round(main_wall, 3),
                "last_pt": {"path": common.rel_project(last), "bytes": last.stat().st_size, "sha256": common.sha256_file(last)},
                "results_csv_sha256": common.sha256_file(run_dir / "results.csv") if (run_dir / "results.csv").exists() else None,
            }
        )
    except BaseException as exc:
        record["status"] = f"FAILED: {type(exc).__name__}: {str(exc)[:300]}"
        raise
    finally:
        wall = time.perf_counter() - run_started
        record["ended_at"] = _now()
        record["wall_s"] = round(wall, 3)
        persist()
        try:
            ledger.add_training_wall(wall, run_id=run_id)
        except EnvelopeExceeded:
            record["status"] += " | TOTAL_WALL_EXCEEDED"
            persist()
            raise
        common.write_json(RUNS_DIR / f"{run_id}.record.json", record)
    if record["wall_s"] > record["wall_cap_s"]:
        record["status"] = "DONE_OVER_WALL_CAP"
        persist()
    return record


def main(argv: Sequence[str] | None = None) -> None:
    import argparse  # noqa: PLC0415

    parser = argparse.ArgumentParser(description="P1-ENG-FAST-002 训练")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("base")
    sub.add_parser("export")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--run", required=True)
    run_parser.add_argument("--imgsz", type=int, required=True)
    run_parser.add_argument("--reason", required=True)
    run_parser.add_argument("--device", default="mps")
    args = parser.parse_args(argv)
    if args.mode == "base":
        print(json.dumps(ensure_base_weights(), ensure_ascii=False))
    elif args.mode == "export":
        if FREEZE_EVIDENCE.exists():
            raise TrainingRefused("冻结后不得重导出")
        spot = __import__("tools.eng_det.spotcheck", fromlist=["load_decision"]).load_decision()
        export = export_yolo()
        export["spotcheck_sha256"] = spot["sha256"]
        document = load_train_evidence()
        if document["runs"]:
            raise TrainingRefused("已有 run：训练数据导出不得在 run 之后改动")
        document["dataset_export"] = export
        save_train_evidence(document)
        print(json.dumps(export["splits"], ensure_ascii=False))
    else:
        print(json.dumps(run(args.run, args.imgsz, args.reason, args.device), ensure_ascii=False))


if __name__ == "__main__":
    main()
