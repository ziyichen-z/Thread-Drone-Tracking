"""输入层（合同 §3.1、§3.2.1、AC-1）：帧/真值/目录联表、原子查表、参考库选择与身份清单。

全部只读：`runtime/` 下的帧、真值、S3 帧目录、S4 划分、S5 字段目录与 S1 清单；
SFT-002 的 609 行评估集与既有预测在 `outputs/eng-sft/`。缺失/不一致一律抛
`InputFailure`（fail-closed，无静默跳过）。

帧目录逐帧对象复用冻结适配器 `tools/eng_sft/adapters/unity_s3.adapt_frame`
（只导入、不改），因此候选/召回对象的类别、颜色与规则 ① 目标车框与 SFT-002
完全同源。
"""

from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
import glob
import gzip
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.eng_fast import common

# --- 输入闭集（§3.1）------------------------------------------------------

SCOUT1 = {
    "source": "scout-1",
    "frames_dir": "runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames",
    "session_dir": "runtime/p1-detect-scouting/p1-detect-001-scout-1",
    "truth_schemas": ("p1-detect-scouting-truth/v1", "p1-detect-scouting-truth/v2"),
    "legacy_result": "scouting-result-bbox-schema-v2.json",
    "legacy_expected": {"hits": 0, "denominator": 45},
}
SCOUT4 = {
    "source": "scout-4",
    "frames_dir": "runtime/test-results/p1-scene-004-scout-4-closed-exchange/frames",
    "session_dir": "runtime/p1-scene-004-scouting/p1-scene-004-scout-4",
    "truth_schemas": ("p1-detect-scouting-truth/v2",),
    "legacy_result": "scouting-result.json",
    "legacy_expected": {"hits": 172, "denominator": 187},
}
BODY_GLOB = "runtime/test-results/p1-m3-body-001-arm-*-post-run"
BODY_TRUTH_SCHEMA = "p1-m3-body-truth/v2"
BODY_EXPECTED_SEGMENTS = 9

CATALOG_MANIFEST = "runtime/dist-data/frames_catalog/attempt-2/frames_catalog.json"
CATALOG_ROOT = "runtime/dist-data/frames_catalog/attempt-2"
SPLITS_JSON = "runtime/dist-data/splits/attempt-2/splits.json"
FIELD_CATALOG_JSON = "runtime/dist-data/field_catalog/attempt-2/field_catalog.json"
INVENTORY_JSON = "runtime/dist-data/inventory/attempt-2/inventory.json"
CATALOG_EXPECTED_ROWS = 43535

SFT_ROOT = "outputs/eng-sft/P1-ENG-SFT-002"
EVAL_JSONL = f"{SFT_ROOT}/data/eval.jsonl"
UPLOAD_FRAMES = f"{SFT_ROOT}/upload"
PRED_BASE = f"{SFT_ROOT}/returned/sft-20260918T202551Z-bd1f5ebb/predictions/zero-shot.jsonl"
PRED_C2 = f"{SFT_ROOT}/returned/sft-20260918T223245Z-bd1f5ebb/predictions/eval-adapter.jsonl"
EVAL_EXPECTED_ROWS = 609

VEHICLE_BANK_MAX_FRAMES = 6
VEHICLE_BANK_MIN_SHORT_SIDE_PX = 64.0
PRIMITIVE_BANK_MIN_SHORT_SIDE_PX = 32.0
BANK_CLASSES: tuple[str, ...] = ("vehicle", "target-primitive")
CLASS_WORDS: tuple[str, ...] = (
    "ambulance",
    "bus",
    "car",
    "container truck",
    "pickup truck",
    "police car",
    "suv",
    "taxi",
    "truck",
)

CACHE_DIR = common.OUT_ROOT / "cache"
CATALOG_INDEX = CACHE_DIR / "catalog-index.jsonl.gz"
DYNAMIC_TARGET_ID = "dynamic-target"


class InputFailure(RuntimeError):
    """AC-1：任一必需输入缺失、sha 不符、查表失败或交集非空 → 整体失败。"""


# --- 数据结构 -------------------------------------------------------------


@dataclass(frozen=True)
class GTObject:
    object_id: str | None  # None = INSTANCE_UNKNOWN
    kind: str  # common.TARGET_KIND_*
    box: tuple[float, float, float, float]
    distance_m: float | None
    class_word: str | None = None
    color_word: str | None = None
    role: str = "catalog"  # target / distractor / catalog


@dataclass
class FrameRec:
    source: str
    sequence: str
    frame_number: int
    path: str  # 仓库相对 jpg 路径（与 S3/S4 的 frame_id 同式）
    sim_t: float
    has_truth: bool
    visible: bool
    target_box: tuple[float, float, float, float] | None
    objects: list[GTObject] = field(default_factory=list)
    truth_path: str | None = None
    distance_axis: str = "slant"


@dataclass
class Sequence_:
    source: str
    sequence: str
    frames: list[FrameRec]
    truth_schema: str
    unpaired: dict[str, int]


# --- scout / BODY 序列 ----------------------------------------------------


def _sidecars(frames_dir: str) -> list[tuple[int, float, str, str]]:
    records = []
    for path in sorted(glob.glob(str(common.absolute(frames_dir) / "frame_*.json"))):
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        frame_id = int(document["frame_id"])
        stem = f"frame_{frame_id:010d}"
        if Path(path).stem != stem:
            raise InputFailure(f"{path} frame_id 与文件名不符")
        jpg = Path(path).with_suffix(".jpg")
        records.append((frame_id, float(document["simulation_time_s"]), common.rel(jpg), common.rel(path)))
    records.sort(key=lambda item: (item[1], item[0]))
    return records


def load_scout(spec: Mapping[str, Any]) -> Sequence_:
    source = spec["source"]
    sidecars = _sidecars(spec["frames_dir"])
    if not sidecars:
        raise InputFailure(f"{source}: 无帧")
    truth_dir = common.absolute(spec["session_dir"]) / "truth"
    frames: list[FrameRec] = []
    unpaired: dict[str, int] = defaultdict(int)
    schemas: set[str] = set()
    for frame_id, sim_t, jpg, _sidecar in sidecars:
        if not common.absolute(jpg).is_file():
            unpaired["IMAGE_MISSING"] += 1
            raise InputFailure(f"{source}: 帧图缺失 {jpg}")
        truth_path = truth_dir / f"frame_{frame_id:010d}.json"
        if not truth_path.is_file():
            unpaired["TRUTH_MISSING"] += 1
            frames.append(FrameRec(source, source, frame_id, jpg, sim_t, False, False, None))
            continue
        truth = json.loads(truth_path.read_text(encoding="utf-8"))
        schema = truth.get("schema_version")
        if schema not in spec["truth_schemas"]:
            raise InputFailure(f"{source}: 真值 schema {schema!r} 不在 {spec['truth_schemas']}")
        schemas.add(schema)
        if int(truth["frame_id"]) != frame_id or not math.isclose(
            float(truth["simulation_time_s"]), sim_t, abs_tol=1e-4
        ):
            raise InputFailure(f"{source}: 真值与帧身份不符 {truth_path.name}")
        box = common.box_from_truth(truth.get("target_bbox_xywh_norm"))
        if truth.get("target_box_status", "VALID") != "VALID":
            box = None
        visible = bool(truth.get("target_visible")) and box is not None
        range_m = truth.get("target_slant_range_m")
        range_m = float(range_m) if range_m is not None and math.isfinite(float(range_m)) else None
        objects: list[GTObject] = []
        if visible:
            objects.append(GTObject("target-0", common.TARGET_KIND_PRIMITIVE, box, range_m, "car", "red", "target"))
        for distractor in truth.get("distractors") or []:
            if distractor.get("box_status", "VALID") != "VALID":
                continue
            d_box = common.box_from_truth(distractor.get("bbox_xywh_norm"))
            if d_box is None:
                continue
            objects.append(
                GTObject(
                    str(distractor.get("distractor_id")),
                    common.TARGET_KIND_CATALOG,
                    d_box,
                    None,
                    None,
                    None,
                    "distractor",
                )
            )
        frames.append(
            FrameRec(source, source, frame_id, jpg, sim_t, True, visible, box, objects, common.rel(truth_path))
        )
    if len(schemas) != 1:
        raise InputFailure(f"{source}: 真值 schema 不唯一 {schemas}")
    return Sequence_(source, source, frames, schemas.pop(), dict(unpaired))


def body_segments() -> list[str]:
    segments = sorted(common.rel(path) for path in glob.glob(str(common.absolute(BODY_GLOB))))
    if len(segments) != BODY_EXPECTED_SEGMENTS:
        raise InputFailure(f"BODY-001 段数 {len(segments)} ≠ {BODY_EXPECTED_SEGMENTS}")
    return segments


def load_body(segment_dir: str) -> Sequence_:
    name = Path(segment_dir).name.replace("p1-m3-body-001-", "body-").replace("-post-run", "")
    sidecars = _sidecars(f"{segment_dir}/frames")
    truth_rows: dict[int, dict[str, Any]] = {}
    with open(common.absolute(segment_dir) / "m3_body_truth.jsonl", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("schema_version") != BODY_TRUTH_SCHEMA:
                raise InputFailure(f"{segment_dir}: 真值 schema {row.get('schema_version')!r}")
            truth_rows[int(row["frame_id"])] = row
    frames: list[FrameRec] = []
    unpaired: dict[str, int] = defaultdict(int)
    for frame_id, sim_t, jpg, _sidecar in sidecars:
        row = truth_rows.get(frame_id)
        if row is None:
            unpaired["TRUTH_MISSING"] += 1
            frames.append(FrameRec("body", name, frame_id, jpg, sim_t, False, False, None))
            continue
        if not math.isclose(float(row["simulation_time_s"]), sim_t, abs_tol=1e-4):
            raise InputFailure(f"{segment_dir}: 真值与帧时刻不符 frame {frame_id}")
        box = None
        if row.get("truth_box_available"):
            box = common.box_from_truth(
                [row["truth_box_x"], row["truth_box_y"], row["truth_box_width"], row["truth_box_height"]]
            )
        visible = bool(row.get("geometrically_visible")) and box is not None
        slant = math.dist(
            (row["target_world_x_m"], row["target_world_y_m"], row["target_world_z_m"]),
            (row["body_world_x_m"], row["body_world_y_m"], row["body_world_z_m"]),
        )
        objects = (
            [GTObject("target-0", common.TARGET_KIND_PRIMITIVE, box, slant, "car", "red", "target")] if visible else []
        )
        frames.append(FrameRec("body", name, frame_id, jpg, sim_t, True, visible, box, objects))
    return Sequence_("body", name, frames, BODY_TRUTH_SCHEMA, dict(unpaired))


def load_sequences() -> list[Sequence_]:
    sequences = [load_scout(SCOUT1), load_scout(SCOUT4)]
    sequences.extend(load_body(segment) for segment in body_segments())
    return sequences


# --- S3 帧目录索引（一次全扫描，缓存到 outputs/）---------------------------


def _index_shard(args: tuple[str, str]) -> list[dict[str, Any]]:
    shard_path, field_catalog_path = args
    from tools.eng_sft.adapters import unity_s3  # noqa: PLC0415

    field_catalog = common.read_json(field_catalog_path)["payload"]
    rows: list[dict[str, Any]] = []
    with gzip.open(shard_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            entry = json.loads(line)
            usable = unity_s3.is_usable_entry(entry)
            depth = {item["object_id"]: item.get("camera_depth_m") for item in entry["objects"]}
            ok_all = sum(1 for item in entry["objects"] if item.get("status") == "OK")
            record: dict[str, Any] = {
                "frame_id": entry["frame_id"],
                "family": entry["family"],
                "usable": usable,
                "ok_all_count": ok_all,
                "vehicles": [],
                "dynamic": None,
            }
            if usable:
                adapted = unity_s3.adapt_frame(entry, field_catalog)
                for obj in adapted.objects:
                    if obj.object_id == DYNAMIC_TARGET_ID:
                        record["dynamic"] = {
                            "definite": bool(obj.definite),
                            "box": obj.visible_norm_xywh,
                            "class_word": obj.class_word,
                            "color_word": obj.color_word,
                        }
                        continue
                    if obj.status != "OK" or not obj.visible_norm_xywh:
                        continue
                    record["vehicles"].append(
                        {
                            "object_id": obj.object_id,
                            "class_word": obj.class_word,
                            "color_word": obj.color_word,
                            "box": [float(v) for v in obj.visible_norm_xywh],
                            "depth_m": depth.get(obj.object_id),
                            "referable": bool(obj.referable),
                        }
                    )
                record["frame_wildcard"] = bool(adapted.frame_wildcard)
            rows.append(record)
    return rows


def build_catalog_index(workers: int = 6) -> dict[str, Any]:
    """扫描全部 S3 分片 → 紧凑索引；分片 sha 先按 manifest 核对（不符即失败）。"""
    manifest = common.read_json(CATALOG_MANIFEST)["payload"]
    shards = manifest["shards"]
    for shard in shards:
        path = common.absolute(CATALOG_ROOT) / shard["path"]
        if common.sha256_file(path) != shard["sha256"]:
            raise InputFailure(f"S3 分片 sha 不符：{shard['path']}")
    jobs = [(str(common.absolute(CATALOG_ROOT) / s["path"]), str(common.absolute(FIELD_CATALOG_JSON))) for s in shards]
    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for part in pool.map(_index_shard, jobs):
            rows.extend(part)
    if len(rows) != CATALOG_EXPECTED_ROWS or len({row["frame_id"] for row in rows}) != len(rows):
        raise InputFailure(f"S3 行数 {len(rows)} ≠ {CATALOG_EXPECTED_ROWS} 或帧 ID 重复")
    identity = {
        "manifest_sha256": common.sha256_file(CATALOG_MANIFEST),
        "field_catalog_sha256": common.sha256_file(FIELD_CATALOG_JSON),
        "shards": len(shards),
        "rows": len(rows),
    }
    common.write_jsonl(CATALOG_INDEX, [{"identity": identity}] + rows)
    return identity


def load_catalog_index() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    if not CATALOG_INDEX.exists():
        build_catalog_index()
    rows = common.read_jsonl(CATALOG_INDEX)
    identity = rows[0]["identity"]
    if identity["manifest_sha256"] != common.sha256_file(CATALOG_MANIFEST) or identity[
        "field_catalog_sha256"
    ] != common.sha256_file(FIELD_CATALOG_JSON):
        raise InputFailure("帧目录索引缓存与当前 S3/S5 身份不符；删除缓存后重建")
    return identity, {row["frame_id"]: row for row in rows[1:]}


# --- S4 划分与原子（§3.2.1，AR2-1）-----------------------------------------


@dataclass
class Splits:
    split_of: dict[str, str]
    atom_of_family: dict[str, str]
    atoms_of_split: dict[str, list[str]]
    families_of_atom: dict[str, list[str]]
    sha256: str
    pairwise_disjoint: bool

    def atom_of(self, frame_path: str, family: str | None) -> str:
        """被评帧的原子：先按 `payload.frames` 路径查 split，再按族落到原子；查不到即失败。"""
        split = self.split_of.get(frame_path)
        if split is None:
            raise InputFailure(f"SPLIT_LOOKUP_MISSING: {frame_path}")
        atoms = self.atoms_of_split.get(split, [])
        if family is not None and family in self.atom_of_family:
            atom = self.atom_of_family[family]
            if atom not in atoms:
                raise InputFailure(f"SPLIT_LOOKUP_MISSING: {frame_path} 族 {family} 的原子不在 split {split}")
            return atom
        if len(atoms) == 1:
            return atoms[0]
        raise InputFailure(f"SPLIT_LOOKUP_MISSING: {frame_path}（split {split} 有 {len(atoms)} 个原子且无族）")


def load_splits() -> Splits:
    document = common.read_json(SPLITS_JSON)
    payload = document["payload"]
    atoms = payload["atoms"]["atoms"]
    atom_of_family = {family: atom for atom, families in atoms.items() for family in families}
    split_of = {frame: split for split, frames in payload["frames"].items() for frame in frames}
    return Splits(
        split_of=split_of,
        atom_of_family=atom_of_family,
        atoms_of_split={split: list(value) for split, value in payload["atom_assignment"].items()},
        families_of_atom={atom: list(families) for atom, families in atoms.items()},
        sha256=common.sha256_file(SPLITS_JSON),
        pairwise_disjoint=bool(payload["leakage_assertions"]["pairwise_disjoint"]),
    )


def load_inventory_index() -> dict[str, tuple[str, int]]:
    inventory = common.read_json(INVENTORY_JSON)
    payload = inventory.get("payload", inventory)
    return {
        record["path"]: (record["sha256"], int(record["bytes"]))
        for record in payload["records"]
        if record.get("kind") != "truth"
    }


# --- 参考库选择（§3.2.1）----------------------------------------------------


@dataclass
class BankRef:
    path: str
    sha256: str
    family: str
    split: str
    atom: str
    boxes: list[dict[str, Any]]  # {object_id, class_word, bank_class, box}
    role: str  # vehicle / target-primitive


def _area(box: Sequence[float]) -> float:
    return float(box[2]) * float(box[3])


def select_bank(
    pool: Iterable[Mapping[str, Any]],
    sha_of: Mapping[str, str],
    *,
    max_frames: int = VEHICLE_BANK_MAX_FRAMES,
) -> dict[str, Any]:
    """§3.2.1 确定选择规则。`pool` 已按原子排除；每项需 frame_id/family/split/atom/vehicles/dynamic。

    返回 `{"vehicle": [...], "target_primitive": [...], "vehicle_classes_covered": k, "status": ...}`。
    """
    frames = list(pool)
    covered: set[str] = set()
    chosen: list[dict[str, Any]] = []
    chosen_ids: set[str] = set()

    def large_by_class(frame: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for vehicle in frame["vehicles"]:
            if vehicle.get("class_word") and common.short_side_px(vehicle["box"]) >= VEHICLE_BANK_MIN_SHORT_SIDE_PX:
                grouped[vehicle["class_word"]].append(vehicle)
        return grouped

    grouped_cache = {frame["frame_id"]: large_by_class(frame) for frame in frames}
    while len(covered) < len(CLASS_WORDS) and len(chosen) < max_frames:
        best_key = None
        best = None
        for frame in frames:
            if frame["frame_id"] in chosen_ids:
                continue
            new = set(grouped_cache[frame["frame_id"]]) - covered
            if not new:
                continue
            ok_count = sum(1 for vehicle in frame["vehicles"])
            key = (-len(new), -ok_count, sha_of[frame["frame_id"]])
            if best_key is None or key < best_key:
                best_key, best = key, frame
        if best is None:
            break
        grouped = grouped_cache[best["frame_id"]]
        new_classes = sorted(set(grouped) - covered)
        boxes = []
        for class_word in new_classes:
            biggest = max(grouped[class_word], key=lambda v: (_area(v["box"]), v["object_id"]))
            boxes.append(
                {
                    "object_id": biggest["object_id"],
                    "class_word": class_word,
                    "bank_class": "vehicle",
                    "box": list(biggest["box"]),
                }
            )
        covered |= set(new_classes)
        chosen_ids.add(best["frame_id"])
        chosen.append({"frame": best, "boxes": boxes})

    primitive = None
    primitive_key = None
    for frame in frames:
        dynamic = frame.get("dynamic")
        if not dynamic or not dynamic.get("definite") or not dynamic.get("box"):
            continue
        if common.short_side_px(dynamic["box"]) < PRIMITIVE_BANK_MIN_SHORT_SIDE_PX:
            continue
        key = (-_area(dynamic["box"]), sha_of[frame["frame_id"]])
        if primitive_key is None or key < primitive_key:
            primitive_key, primitive = key, frame

    status = "COMPLETE" if len(covered) == len(CLASS_WORDS) else (
        f"BANK_PARTIAL({len(covered)}/{len(CLASS_WORDS)})" if covered else "N/A(BANK_EMPTY)"
    )
    result = {
        "vehicle": [
            {
                "frame_id": item["frame"]["frame_id"],
                "family": item["frame"]["family"],
                "split": item["frame"]["split"],
                "atom": item["frame"]["atom"],
                "boxes": item["boxes"],
            }
            for item in chosen
        ],
        "vehicle_classes_covered": sorted(covered),
        "vehicle_status": status,
        "target_primitive": None,
        "target_primitive_status": "N/A(BANK_EMPTY)",
    }
    if primitive is not None:
        result["target_primitive"] = {
            "frame_id": primitive["frame_id"],
            "family": primitive["family"],
            "split": primitive["split"],
            "atom": primitive["atom"],
            "boxes": [
                {
                    "object_id": DYNAMIC_TARGET_ID,
                    "class_word": "car",
                    "bank_class": "target-primitive",
                    "box": list(primitive["dynamic"]["box"]),
                }
            ],
        }
        result["target_primitive_status"] = "COMPLETE"
    return result


def bank_pool(
    index: Mapping[str, Mapping[str, Any]], splits: Splits, excluded_atoms: Iterable[str]
) -> list[dict[str, Any]]:
    """参考池 = train∪dev 原子 − 被评原子（原子排除绝对优先）。"""
    excluded = set(excluded_atoms)
    allowed_atoms = {
        atom for split in ("train", "dev") for atom in splits.atoms_of_split.get(split, []) if atom not in excluded
    }
    pool = []
    for frame_id, row in index.items():
        if not row.get("usable"):
            continue
        split = splits.split_of.get(frame_id)
        if split not in ("train", "dev"):
            continue
        atom = splits.atom_of_family.get(row["family"])
        if atom not in allowed_atoms:
            continue
        pool.append({**row, "split": split, "atom": atom})
    pool.sort(key=lambda item: item["frame_id"])
    return pool


def bank_assertions(
    bank: Mapping[str, Any], evaluated_shas: set[str], evaluated_atoms: set[str], ref_shas: Mapping[str, str]
) -> dict[str, Any]:
    """AC-1 两条断言：评估帧∩参考帧 = ∅（sha）；参考帧原子∩{被评原子} = ∅（原子）。"""
    refs = list(bank["vehicle"]) + ([bank["target_primitive"]] if bank.get("target_primitive") else [])
    sha_overlap = sorted({ref_shas[ref["frame_id"]] for ref in refs} & evaluated_shas)
    atom_overlap = sorted({ref["atom"] for ref in refs} & evaluated_atoms)
    result = {
        "eval_ref_sha_intersection": sha_overlap,
        "ref_atom_eval_atom_intersection": atom_overlap,
        "passed": not sha_overlap and not atom_overlap,
    }
    if not result["passed"]:
        raise InputFailure(f"参考库隔离断言失败：sha∩={sha_overlap} atom∩={atom_overlap}")
    return result


# --- 609 行评估集与候选集（§3.5.1；IR-1）------------------------------------


def load_eval_rows() -> list[dict[str, Any]]:
    rows = common.read_jsonl(EVAL_JSONL)
    if len(rows) != EVAL_EXPECTED_ROWS or len({row["row_id"] for row in rows}) != len(rows):
        raise InputFailure(f"评估集行数 {len(rows)} ≠ {EVAL_EXPECTED_ROWS} 或 row_id 重复")
    return sorted(rows, key=lambda row: row["row_id"])


def candidate_set(index_row: Mapping[str, Any]) -> list[dict[str, Any]]:
    """IR-1：候选 = 该帧 `OK` 目录车辆（适配器执行域）∪ 帧级已绑定动态目标（规则 ① 有框）。

    编号按框左上角行优先（y 再 x，最后 object_id 定序），从 1 起。
    """
    candidates = [
        {
            "object_id": vehicle["object_id"],
            "class_word": vehicle["class_word"],
            "color_word": vehicle["color_word"],
            "box": list(vehicle["box"]),
            "depth_m": vehicle.get("depth_m"),
        }
        for vehicle in index_row["vehicles"]
    ]
    dynamic = index_row.get("dynamic")
    if dynamic and dynamic.get("definite") and dynamic.get("box"):
        candidates.append(
            {
                "object_id": DYNAMIC_TARGET_ID,
                "class_word": dynamic.get("class_word"),
                "color_word": dynamic.get("color_word"),
                "box": list(dynamic["box"]),
                "depth_m": None,
            }
        )
    candidates.sort(key=lambda c: (round(c["box"][1], 9), round(c["box"][0], 9), c["object_id"]))
    for number, candidate in enumerate(candidates, start=1):
        candidate["index"] = number
    return candidates


def catalog_frame_objects(index_row: Mapping[str, Any]) -> list[GTObject]:
    """P1-d 召回对象：全部 `OK` 目录车 ∪ 动态目标（§3.2.2 第 4 行）；距离轴 = 轴向深度。"""
    objects = [
        GTObject(
            vehicle["object_id"],
            common.TARGET_KIND_CATALOG,
            tuple(vehicle["box"]),
            vehicle.get("depth_m"),
            vehicle.get("class_word"),
            vehicle.get("color_word"),
            "catalog",
        )
        for vehicle in index_row["vehicles"]
    ]
    dynamic = index_row.get("dynamic")
    if dynamic and dynamic.get("definite") and dynamic.get("box"):
        objects.append(
            GTObject(DYNAMIC_TARGET_ID, common.TARGET_KIND_PRIMITIVE, tuple(dynamic["box"]), None, "car", "red", "target")
        )
    return objects
