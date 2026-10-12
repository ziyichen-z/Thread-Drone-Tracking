#!/usr/bin/env python3
"""合成的最小归档世界（S1/S3/S4/S5 + 指令逐行 + 探针清单），供 K4 构建器的具名回归使用。

上游归档（S3/S4/S5/S1）的字节格式由 `tools/dist_data` 的既有 stage 产出，本仓库
的测试不重跑那条管线；本模块按同一 schema 写出一个**几十帧**的小世界，而所有
**派生**内容一律由生产函数现算：指令逐行的七值与最小程序取
`tools.eng_asset.inventory.classify_uniqueness`、摘要直方图由同一次分类聚合、
gold 文本取 `tools.eng_sft.prompt_v2.gold_text`。因此夹具里没有手写的三态、
七值或 gold。

场景库（`_LAYOUTS`）覆盖表 A′ 的每一行：OK / 非 OK 目录车、未知类别阻断体、
phantom、颜色未验证、#27 反例、目标车已绑定（definite）与三种整帧通配
（未绑定 / 缺框 / 裁剪后退化）。
"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import build_catalog, contract, tier1_lang  # noqa: E402
from tools.eng_asset import inventory as asset_inventory  # noqa: E402

FRAME_ROOT = "runtime/frames.fixture"
WIDTH, HEIGHT = 640, 480

# S5 目录（class_verified 全真；颜色按 color_status 区分）。
OBJECTS: dict[str, dict[str, Any]] = {
    "Vehicle_Car_color01 (1)": {"class": "car", "color": "red", "color_status": "VERIFIED"},
    "Vehicle_Car_color02 (2)": {"class": "car", "color": "blue", "color_status": "VERIFIED"},
    "Vehicle_Taxi (1)": {"class": "taxi", "color": "yellow", "color_status": "VERIFIED"},
    "Vehicle_Taxi (2)": {"class": "taxi", "color": "yellow", "color_status": "VERIFIED"},
    "Vehicle_Truck_color02 (3)": {"class": "truck", "color": "gray", "color_status": "UNVERIFIED"},
    "Vehicle_Bus_color03 (1)": {"class": "bus", "color": "green", "color_status": "VERIFIED"},
    "Vehicle_SUV_color01 (1)": {"class": "suv", "color": "purple", "color_status": "VERIFIED"},
    "Vehicle_Pick up Truck_color01 (1)": {
        "class": "pickup truck",
        "color": "blue",
        "color_status": "VERIFIED",
    },
}
# 未知类别阻断体：不在 S5 里（class_word = None，全帧 noun 灰区）。
UNKNOWN_BLOCKER = "Vehicle_Unknown_color09 (7)"
PHANTOM_ID = "phantom:Vehicle_Taxi@3"

BOXES: dict[str, list[float]] = {
    "Vehicle_Car_color01 (1)": [40, 40, 160, 130],
    "Vehicle_Car_color02 (2)": [300, 60, 420, 150],
    "Vehicle_Taxi (1)": [60, 250, 150, 320],
    "Vehicle_Taxi (2)": [420, 250, 520, 330],
    "Vehicle_Truck_color02 (3)": [200, 300, 330, 400],
    "Vehicle_Bus_color03 (1)": [80, 150, 300, 240],
    "Vehicle_SUV_color01 (1)": [430, 120, 520, 190],
    "Vehicle_Pick up Truck_color01 (1)": [250, 180, 340, 250],
    UNKNOWN_BLOCKER: [520, 330, 600, 400],
    PHANTOM_ID: [10, 400, 60, 440],
}

# 每个布局：目录对象 (object_id, status) + 目标车模式。
# 目标车模式：none / bound（definite）/ unbound / missing_box / degenerate。
_LAYOUTS: dict[str, dict[str, Any]] = {
    "L1": {"objects": [("Vehicle_Car_color01 (1)", "OK"), ("Vehicle_Taxi (1)", "OK")], "target": "none"},
    "L2": {
        "objects": [("Vehicle_Car_color01 (1)", "OK"), ("Vehicle_Car_color02 (2)", "OK")],
        "target": "none",
    },
    "L3": {
        "objects": [("Vehicle_Car_color01 (1)", "OK"), ("Vehicle_Truck_color02 (3)", "OK")],
        "target": "none",
    },
    "L4": {
        "objects": [("Vehicle_Bus_color03 (1)", "OK"), ("Vehicle_Car_color02 (2)", "OK")],
        "target": "none",
    },
    "L5": {
        "objects": [("Vehicle_SUV_color01 (1)", "TRUNCATED"), ("Vehicle_Taxi (1)", "OK")],
        "target": "none",
    },
    "L6": {"objects": [("Vehicle_Car_color01 (1)", "OK")], "target": "bound"},
    "L7": {
        "objects": [
            ("Vehicle_Taxi (1)", "OK"),
            ("Vehicle_Taxi (2)", "OK"),
            ("Vehicle_Car_color01 (1)", "OK"),
        ],
        "target": "none",
    },
    "L8": {"objects": [("Vehicle_Car_color02 (2)", "OK"), (UNKNOWN_BLOCKER, "OK")], "target": "none"},
    "L9": {"objects": [("Vehicle_Taxi (1)", "OK"), (PHANTOM_ID, "OK")], "target": "none"},
    "L10": {"objects": [("Vehicle_Car_color01 (1)", "OK")], "target": "unbound"},
    "L11": {"objects": [("Vehicle_Car_color01 (1)", "OK")], "target": "missing_box"},
    "L12": {"objects": [("Vehicle_Car_color01 (1)", "OK")], "target": "degenerate"},
    # L14：视野里只有目标车（definite）→ `the car` / `the red car` 的 unique 目标是
    # 目标车本身，用来覆盖 G1t / G2t 与训练的 `has_dynamic_target` unique。
    "L14": {"objects": [("Vehicle_Taxi (2)", "OK")], "target": "bound"},
    "L13": {
        "objects": [
            ("Vehicle_Pick up Truck_color01 (1)", "OK"),
            ("Vehicle_SUV_color01 (1)", "OK"),
        ],
        "target": "none",
    },
}

FAMILIES: tuple[tuple[str, str, int], ...] = (
    # (family, split, frames)
    ("p1-vlm-survey-a2-p1-c1-s1", "train", 52),
    ("detect-scout1", "dev", 52),
    ("m3-armA", "dev", 52),
    ("m3-armB", "test", 78),
    ("qual-leftover", "unassigned", 13),
)
LAYOUT_CYCLE: tuple[str, ...] = tuple(_LAYOUTS)


def _norm(box: list[float]) -> list[float]:
    return [box[0] / WIDTH, box[1] / HEIGHT, (box[2] - box[0]) / WIDTH, (box[3] - box[1]) / HEIGHT]


def _object_item(object_id: str, status: str) -> dict[str, Any]:
    box = BOXES[object_id]
    visible = status in {"OK", "TRUNCATED"}
    return {
        "object_id": object_id,
        "is_phantom": object_id.startswith("phantom:"),
        "referable": status == "OK" and not object_id.startswith("phantom:"),
        "status": status,
        "visible_px": list(box) if visible else None,
        "visible_norm_xywh": _norm(box) if visible else None,
        "amodal_px": list(box) if visible else None,
        "blocks": True,
        "camera_depth_m": 40.0,
        "exposure": "vehicle",
    }


def _target_fields(mode: str) -> tuple[bool, list[float] | None]:
    if mode == "bound":
        return True, [280.0, 300.0, 400.0, 400.0]
    if mode == "unbound":
        return False, [280.0, 300.0, 400.0, 400.0]
    if mode == "missing_box":
        return True, None
    if mode == "degenerate":
        # 裁剪到画幅后面积为 0（整幅在画幅右外）。
        return True, [660.0, 300.0, 700.0, 400.0]
    return True, None


def frame_entry(family: str, index: int, layout_name: str) -> dict[str, Any]:
    layout = _LAYOUTS[layout_name]
    items = [_object_item(object_id, status) for object_id, status in layout["objects"]]
    blocking = [item["object_id"] for item in items]
    referable = [item["object_id"] for item in items if item["referable"]]
    bound, target_box = _target_fields(layout["target"])
    entry: dict[str, Any] = {
        "frame_id": f"{FRAME_ROOT}/{family}/frame_{index:010d}.jpg",
        "family": family,
        "layout_class": "default",
        "usage_class": "MOTHER_POOL",
        "layout_binding_valid": True,
        "sidecar_complete": True,
        "station_bin": {"key": f"10:20:{index % 8}:1", "x_bin": 10, "z_bin": 20,
                        "azimuth_bin": index % 8, "elevation_band": 1, "elevation_deg": 45.0},
        "objects": items,
        "blocking": list(blocking),
        "referable": referable,
        "co_visible_count": len(items),
        "status_histogram": {},
        "target_blocker_px": target_box,
        "target_source_bound": bound,
        "target_sweep_area_px2": 0.0,
        "target_unbounded": False,
    }
    if layout["target"] != "none":
        entry["blocking"] = list(blocking) + [build_catalog.TARGET_BLOCKER_ID]
    return entry


def build_world(root: Path, *, families: Iterable[tuple[str, str, int]] = FAMILIES) -> dict[str, Any]:
    """在 `root` 下写出一个完整的小归档世界，返回关键路径与统计。"""
    root = Path(root)
    entries: list[dict[str, Any]] = []
    split_frames: dict[str, list[str]] = {"train": [], "dev": [], "test": [], "d3": []}
    for family, split, count in families:
        for index in range(1, count + 1):
            layout = LAYOUT_CYCLE[(index - 1) % len(LAYOUT_CYCLE)]
            entry = frame_entry(family, index, layout)
            entries.append(entry)
            if split != "unassigned":
                split_frames[split].append(entry["frame_id"])

    # 帧文件（字节唯一即可；SHA 绑定只核对字节与 S1 记录）。
    records = []
    for entry in entries:
        path = root / entry["frame_id"]
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = b"\xff\xd8\xff\xe0fixture:" + entry["frame_id"].encode("utf-8")
        path.write_bytes(payload)
        records.append(
            {
                "path": entry["frame_id"],
                "kind": "image",
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "family": entry["family"],
            }
        )

    field_catalog = {
        "stage": 5,
        "objects": {
            object_id: {
                "object_id": object_id,
                "class": value["class"],
                "class_verified": True,
                "color": value["color"],
                "color_status": value["color_status"],
                "color_evidence": {},
                "dynamic_state": "static",
                "group_key": f"{object_id}|",
                "relocated": False,
            }
            for object_id, value in OBJECTS.items()
        },
        "dual_verified_object_ids": sorted(
            object_id for object_id, value in OBJECTS.items() if value["color_status"] == "VERIFIED"
        ),
        "verified_color_vocabulary": sorted(contract.COLOR_WORDS),
        "groups": {},
    }

    archive = root / "runtime/dist-data"
    (archive / "contract/attempt-2").mkdir(parents=True, exist_ok=True)
    (archive / "frames_catalog/attempt-2/shards").mkdir(parents=True, exist_ok=True)
    (archive / "splits/attempt-2/shards").mkdir(parents=True, exist_ok=True)
    (archive / "field_catalog/attempt-2").mkdir(parents=True, exist_ok=True)
    (archive / "inventory/attempt-2").mkdir(parents=True, exist_ok=True)

    # S0：本项只用它做「词表/关系闭集常量核对」，故夹具照真实归档的字段形状写出这几项。
    (archive / "contract/attempt-2/contract.json").write_text(
        json.dumps(
            {
                "payload": {
                    "stage": 0,
                    "class_words": sorted(contract.CLASS_WORDS),
                    "relations": {
                        "types": list(contract.RELATION_TYPES),
                        "viewer_side_min_separation_px": contract.VIEWER_SIDE_MIN_SEPARATION_PX,
                        "nearest_to_dominance_ratio": contract.NEAREST_TO_DOMINANCE_RATIO,
                    },
                    "dynamic_target": {"referable": contract.DYNAMIC_TARGET_REFERABLE},
                }
            }
        ),
        encoding="utf-8",
    )
    (archive / "field_catalog/attempt-2/field_catalog.json").write_text(
        json.dumps({"payload": field_catalog}), encoding="utf-8"
    )
    (archive / "inventory/attempt-2/inventory.json").write_text(
        json.dumps({"payload": {"stage": 1, "records": records, "record_count": len(records)}}),
        encoding="utf-8",
    )

    # S3 分片（两片）+ manifest。
    shards_meta = []
    half = len(entries) // 2 or len(entries)
    for shard_index, chunk in enumerate((entries[:half], entries[half:])):
        if not chunk:
            continue
        relative = f"shards/{shard_index:05d}.ndjson.gz"
        path = archive / "frames_catalog/attempt-2" / relative
        with gzip.open(path, "wt", compresslevel=9) as handle:
            for entry in chunk:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        data = path.read_bytes()
        shards_meta.append(
            {
                "index": f"{shard_index:05d}",
                "path": relative,
                "lines": len(chunk),
                "compressed_bytes": len(data),
                "uncompressed_bytes": 0,
                "sha256": hashlib.sha256(data).hexdigest(),
                "first_frame_id": chunk[0]["frame_id"],
                "last_frame_id": chunk[-1]["frame_id"],
            }
        )
    (archive / "frames_catalog/attempt-2/frames_catalog.json").write_text(
        json.dumps(
            {
                "payload": {
                    "stage": 3,
                    "frame_count": len(entries),
                    "row_count": len(entries),
                    "shards": shards_meta,
                }
            }
        ),
        encoding="utf-8",
    )

    splits_shard = archive / "splits/attempt-2/shards/00000.ndjson.gz"
    with gzip.open(splits_shard, "wt", compresslevel=9) as handle:
        handle.write(json.dumps({"stage": 4}) + "\n")
    (archive / "splits/attempt-2/splits.json").write_text(
        json.dumps(
            {
                "payload": {
                    "stage": 4,
                    "frames": split_frames,
                    "frame_counts": {key: len(value) for key, value in split_frames.items()},
                    "shards": [
                        {
                            "index": "00000",
                            "path": "shards/00000.ndjson.gz",
                            "sha256": hashlib.sha256(splits_shard.read_bytes()).hexdigest(),
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    instructions, summary = _instructions(entries, field_catalog, split_frames)
    instructions_path = root / "runtime/eng-asset/P1-ENG-ASSET-001/instructions.ndjson.gz"
    instructions_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(instructions_path, "wt", compresslevel=9) as handle:
        for row in instructions:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary_path = root / "docs/evidence/P1-ENG-ASSET-001-instructions-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    probe_root = root / "probe"
    _probe(
        probe_root,
        entries,
        field_catalog,
        split_frames,
        instructions_path,
        archive / "field_catalog/attempt-2/field_catalog.json",
    )
    return {
        "root": root,
        "probe_root": probe_root,
        "entries": entries,
        "instructions": instructions,
        "field_catalog": field_catalog,
        "split_frames": split_frames,
    }


def _instructions(
    entries: list[dict[str, Any]], field_catalog: dict[str, Any], split_frames: dict[str, list[str]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """指令逐行与摘要直方图：两者都由 `classify_uniqueness` 现算，不手写。"""
    split_by_frame = {
        frame_id: split for split, frames in split_frames.items() for frame_id in frames
    }
    rows: list[dict[str, Any]] = []
    histogram: dict[str, dict[str, dict[str, int]]] = {}
    for entry in entries:
        world = build_catalog.frame_world(entry, field_catalog)
        split = split_by_frame.get(entry["frame_id"], "unassigned")
        mother = entry["usage_class"] in contract.MOTHER_USAGE_CLASSES
        usage_key = "mother_usage" if mother else "non_mother_usage"
        for object_id in entry["referable"]:
            status, program, reference = asset_inventory.classify_uniqueness(
                world, object_id, field_catalog
            )
            bucket = histogram.setdefault(split, {}).setdefault(usage_key, {})
            bucket[status] = bucket.get(status, 0) + 1
            rows.append(
                {
                    "frame_id": entry["frame_id"],
                    "object_id": object_id,
                    "split": split,
                    "family": entry["family"],
                    "layout_class": entry["layout_class"],
                    "usage_class": entry["usage_class"],
                    "mother_usage": mother,
                    "uniqueness_status": status,
                    "program": program,
                    "surface": tier1_lang.render(program) if program else None,
                    "resolved_reference_object_id": reference,
                    "visible_norm_xywh": next(
                        (
                            item["visible_norm_xywh"]
                            for item in entry["objects"]
                            if item["object_id"] == object_id
                        ),
                        None,
                    ),
                    "short_side_px": 60.0,
                    "target_unbounded": False,
                    "prospective_mother_eligible": program is not None,
                }
            )
    summary = {
        "work_id": "P1-ENG-ASSET-001",
        "attempt": "attempt-2",
        "schema_version": "p1-eng-asset-001/instructions-summary/v1",
        "uniqueness_status_histogram": histogram,
    }
    return rows, summary


def _probe(
    probe_root: Path,
    entries: list[dict[str, Any]],
    field_catalog: dict[str, Any],
    split_frames: dict[str, list[str]],
    instructions_path: Path,
    field_catalog_path: Path,
) -> None:
    """探针清单：从 test 帧取若干 (frame, surface) 作 legacy 行，含一对重复键。"""
    from tools.eng_sft.adapters import unity_s3
    from tools.eng_sft.three_state import three_state

    test_frames = set(split_frames["test"])
    rows: list[dict[str, Any]] = []
    for entry in entries:
        if entry["frame_id"] not in test_frames or len(rows) >= 24:
            continue
        record = unity_s3.adapt_frame(entry, field_catalog)
        if record.frame_wildcard:
            continue
        for class_word in sorted(contract.CLASS_WORDS):
            result = three_state(record.objects, {"class": class_word})
            if result.state not in ("unique", "ambiguous", "gray_definite_plus_uncertain"):
                continue
            ids = result.target_object_ids or result.definite_ids
            box = record.box_of(ids[0]) if ids else None
            rows.append(
                {
                    "row_id": f"v1-{len(rows):04d}",
                    "group": "G1_CLASS" if result.state == "unique" else "G3_AMBIGUOUS",
                    "stratum": "M",
                    "frame_path": entry["frame_id"],
                    "frame_index": int(entry["frame_id"].rsplit("_", 1)[-1].split(".")[0]),
                    "family": entry["family"],
                    "split": "test",
                    "object_id": ids[0] if ids else None,
                    "class": class_word,
                    "surface": f"the {class_word}",
                    "gold_xywh_norm": list(box) if box else None,
                    "same_class_visible": len(ids),
                    "short_side_px": 60.0,
                }
            )
            break
    # 重复键：同 (frame_path, surface) 再挂一条 legacy 行。
    if rows:
        duplicate = dict(rows[0])
        duplicate["row_id"] = "v1-dup0"
        rows.append(duplicate)
    probe_root.mkdir(parents=True, exist_ok=True)
    (probe_root / "manifest-default.json").write_text(
        json.dumps(
            {
                "schema": "probe/manifest/v1",
                "seed": "fixture",
                "n_rows": len(rows),
                "rows": rows,
                "source": {
                    "instructions": str(instructions_path),
                    "instructions_sha256": hashlib.sha256(instructions_path.read_bytes()).hexdigest(),
                    "field_catalog": str(field_catalog_path),
                    "field_catalog_sha256": hashlib.sha256(
                        field_catalog_path.read_bytes()
                    ).hexdigest(),
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    outputs = probe_root / "outputs/qwen3vl-2b-default-20260912"
    outputs.mkdir(parents=True, exist_ok=True)
    (outputs / "predictions.jsonl").write_text(
        "\n".join(
            json.dumps(v1_prediction(index, row), ensure_ascii=False) for index, row in enumerate(rows)
        )
        + "\n",
        encoding="utf-8",
    )


# 旧探针 v1 输出的四种形态，按行序轮转（R1@K4 §4 第 2 条：夹具行携带真实 schema 字段，
# `invalid_output` / `reported_ambiguity` / `parsed.bbox_2d` / `success` / `iou`）。
V1_KINDS: tuple[str, ...] = ("invalid", "ambiguous", "unique", "none")


def v1_prediction(index: int, row: dict[str, Any]) -> dict[str, Any]:
    kind = V1_KINDS[index % len(V1_KINDS)]
    record: dict[str, Any] = {
        "row_id": row["row_id"],
        "model": "fixture/v1",
        "raw_output": "{}",
        "parsed": None,
        "predicted_xyxy_norm": None,
        "iou": None,
        "success": False,
        "reported_ambiguity": False,
        "invalid_output": False,
    }
    if kind == "invalid":
        record.update(raw_output="not json", invalid_output=True)
    elif kind == "ambiguous":
        record.update(raw_output='{"ambiguous": true}', parsed={"ambiguous": True}, reported_ambiguity=True)
    elif kind == "unique":
        record.update(
            raw_output='{"bbox_2d": [100, 100, 300, 300]}',
            parsed={"bbox_2d": [100, 100, 300, 300], "label": row["class"]},
            predicted_xyxy_norm=[0.1, 0.1, 0.3, 0.3],
            iou=0.72,
            success=True,
        )
    else:
        record.update(parsed={"label": row["class"]})
    return record


def v1_expected_status(index: int) -> str | None:
    """`evaluate.map_v1_output` 对第 index 行应得的三态（`invalid` → None）。"""
    kind = V1_KINDS[index % len(V1_KINDS)]
    return None if kind == "invalid" else kind


# --- 测试用编排 -----------------------------------------------------------


def expectations(world: dict[str, Any]):
    """夹具世界对应的 AC-1 期望值（同一套对账代码，只换期望值）。"""
    from tools.eng_sft import build_sft_data as build

    return build.ReconcileExpectations(
        s3_frames=len(world["entries"]),
        s3_shards=2,
        s4_frame_counts={key: len(value) for key, value in world["split_frames"].items()},
        s5_objects=len(world["field_catalog"]["objects"]),
        s5_class_verified=len(world["field_catalog"]["objects"]),
        s5_dual_verified=len(world["field_catalog"]["dual_verified_object_ids"]),
        instruction_rows=len(world["instructions"]),
    )


def local_root(root: Path) -> Path:
    return Path(root) / "outputs/eng-sft/P1-ENG-SFT-002"


def run_build(world: dict[str, Any], **kwargs):
    from tools.eng_sft import build_sft_data as build

    root = world["root"]
    return build.run_build(
        repo_root=root,
        probe_root=world["probe_root"],
        local_root=local_root(root),
        expected=expectations(world),
        **kwargs,
    )


def copy_frozen_scripts(root: Path) -> None:
    """把冻结闭集的四份脚本复制进夹具仓库，供 `freeze` 的跟踪/干净检查。"""
    import shutil

    destination = Path(root) / "tools/eng_sft"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "__init__.py").write_text("", encoding="utf-8")
    for name in ("three_state.py", "prompt_v2.py", "parse.py", "evaluate.py"):
        shutil.copy2(PROJECT_ROOT / "tools/eng_sft" / name, destination / name)


def git_commit_all(root: Path, message: str = "fixture") -> str:
    """在夹具根初始化一个 git 仓库并提交全部内容，返回 HEAD。"""
    import subprocess

    root = Path(root)
    env = {
        "GIT_AUTHOR_NAME": "fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "PATH": __import__("os").environ.get("PATH", ""),
        "HOME": str(root),
    }
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=root, check=True, env=env)
        (root / ".gitignore").write_text("/outputs/\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", message], cwd=root, check=True, env=env)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True, env=env
    ).stdout.strip()


def write_unity_verdicts(
    root: Path, plan: dict[str, Any], *, wrong_panels: Iterable[int] = (), state: str = "COMPLETE"
) -> Path:
    """按代录机读格式 v1 写一份 Unity 日志条目（测试替代接受/辅助角色的代录）。"""
    from tools.eng_sft import label_audit

    wrong = set(wrong_panels)
    lines = [
        "# Unity 测试日志（夹具）",
        "",
        f"## {label_audit.UNITY_LOG_ENTRY}",
        "",
        label_audit.VERDICT_SCHEMA_LINE,
        label_audit.VERDICT_STATUS_LINE,
        f"{label_audit.VERDICT_STATE_PREFIX} {state}",
        "",
        "### 结构化判定",
        "",
        label_audit.VERDICT_TABLE_HEADER,
        "|---|---|---|---|---|---|",
    ]
    for panel in plan["panels"]:
        if panel["share"] != "user":
            continue
        layer = panel["layer"]
        fields = label_audit.JUDGED_FIELDS[layer]
        verdict = "错" if panel["panel_index"] in wrong else "对"
        row = {name: (verdict if name in fields else "NA") for name in
               ("状态", "候选完整", "颜色", "关系方向")}
        errors = "类别错" if panel["panel_index"] in wrong else ""
        lines.append(
            f"| {panel['panel_index']} | {row['状态']} | {row['候选完整']} | {row['颜色']} | "
            f"{row['关系方向']} | {errors} |"
        )
    lines += ["", "### 用户判定原文", "", "（夹具）", ""]
    path = Path(root) / "docs/unity-test-log.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def stub_tokenizer(root: Path):
    """写四个占位 tokenizer 文件并返回一个按字符数计数的 encode（无网络、无权重）。"""
    from tools.eng_sft import build_sft_data as build
    from tools.eng_sft import receipts

    directory = Path(root) / receipts.TOKENIZER_ROOT / build.TOKENIZER_REVISION
    directory.mkdir(parents=True, exist_ok=True)
    for name in build.TOKENIZER_FILES:
        (directory / name).write_text(f'{{"fixture": "{name}"}}', encoding="utf-8")

    def encode(text: str) -> int:
        return max(1, len(text) // 4)

    return directory, encode


def git_untrack(root: Path, relative: str) -> None:
    """把一个已跟踪文件移出索引（内容保留在工作区）→ 该文件变成未跟踪。"""
    import os
    import subprocess

    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(root),
        "GIT_AUTHOR_NAME": "fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
    }
    subprocess.run(["git", "rm", "-q", "--cached", relative], cwd=root, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "untrack"], cwd=root, check=True, env=env)


def write_asset001_audit(root: Path, pairs: list[tuple[str, str]]) -> Path:
    """写一份 ASSET-001 形态的面板清单（只含交集表要用的那几列）。"""
    lines = [
        "# P1-ENG-ASSET-001 — 分层标签抽查（AC-4）",
        "",
        "## 3. 面板清单",
        "",
        "| panel_index | stratum | split | frame_id | object_id | uniqueness_status | short_side_px | surface | overlay_sha256 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for index, (frame_id, object_id) in enumerate(pairs, start=1):
        lines.append(
            f"| {index} | S1 | dev | `{frame_id}` | `{object_id}` | UNIQUE_CLASS | 60.0 | the car | `deadbeef` |"
        )
    path = Path(root) / "docs/evidence/P1-ENG-ASSET-001-label-audit.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
