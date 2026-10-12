"""D1 数据集构建（合同 §3.1、§3.1.1、§3.1.3、AC-1）。

S3 帧目录（数据根，只读）→ 每帧两类标签（`0 vehicle` / `1 target`）+ ignore 集 + 三域清单。

- 正样本：`Vehicle_*` 目录车，状态 ∈ {OK, TRUNCATED, EXCLUDED_OCCLUDED, TOO_SMALL} 且
  `visible_px` 裁剪到画幅后短边 ≥ 12 px，且其层（类别 × 状态 × 短边档）不在
  `STRATUM_IGNORED` 集；目标车 = `dynamic-target`，框 = `unity_s3.cropped_target_box`（同一函数）。
- ignore：(i) 纳入状态但裁剪后短边 < 12 px；(ii) `PHANTOM` 且带框；(iii) `STRATUM_IGNORED` 层对象。
- 整帧排除：`unity_s3.wildcard_reason(entry)` 非空（目标车在视野内但无可用框）；
  Q-1 CLARIFY（2026-09-28）另加 `target_unbounded=true` 的帧（原因 `TARGET_UNBOUNDED`）。
- Q-2 CLARIFY（2026-09-28）：仅演示路线会话（`DEMO_ROUTE_FLAG_FAMILIES`），经既有真值 join
  （`tools.dist_data.roots.truth_source_for`）取逐帧可见性标志——scout `target_visible`、BODY
  `geometrically_visible`；标志逐字为 `False` 的目标框转 ignore（`iv_truth_invisible`，训练填充 +
  评估 IoA 过滤，同 §3.1.3 (ii)(iii)）。标志缺失/非 bool 的帧沿原规则。该标志只进离线派生标签、
  抽查与评分（AC-8），不进插件、控制器或任何运行时通道。
- 三域（§3.1.1）按族 → 原子：T = train 原子 ∪ dev 原子内 {a1-s2, scout-1, m3-armA, rate, scene-val}；
  V = dev 原子内 {a7}；H = test 两原子。断言见 `assert_domains`。

输出：`outputs/eng-det/dataset/index.jsonl.gz`（逐帧标签，不入库）、
`docs/evidence/P1-ENG-FAST-002-dataset-frames.jsonl.gz`（逐帧 sha/族/原子/域/状态计数）、
`docs/evidence/P1-ENG-FAST-002-dataset.json`（汇总、计数、断言与来源 sha）。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.eng_det import common

CATALOG_MANIFEST = "runtime/dist-data/frames_catalog/attempt-2/frames_catalog.json"
CATALOG_ROOT = "runtime/dist-data/frames_catalog/attempt-2"
SPLITS_JSON = "runtime/dist-data/splits/attempt-2/splits.json"
INVENTORY_JSON = "runtime/dist-data/inventory/attempt-2/inventory.json"
EVAL_JSONL = "outputs/eng-sft/P1-ENG-SFT-002/data/eval.jsonl"
CATALOG_EXPECTED_ROWS = 43535
EVAL_EXPECTED_ROWS = 609
DYNAMIC_TARGET_ID = "dynamic-target"

#: Q-2：有逐帧真值可见性标志的演示路线会话（LOOP-001 演示路线：scout-1、M3 arm A/B）。
#: s004-scout 同有 scouting 标志但不属演示路线；实测其 4,836 帧标志全为 True（`-dataset.json`
#: `q2_visibility_flags` 另记），故此边界对标签零数值影响。
DEMO_ROUTE_FLAG_FAMILIES = ("detect-scout1", "m3-armA", "m3-armB")
FLAG_FIELD_OF_SCHEMA = {"scouting": "target_visible", "m3": "geometrically_visible"}
EXCLUSION_TARGET_UNBOUNDED = "TARGET_UNBOUNDED"

DATASET_DIR = common.OUT_ROOT / "dataset"
INDEX_PATH = DATASET_DIR / "index.jsonl.gz"
PRELIM_INDEX_PATH = DATASET_DIR / "index-prelim.jsonl.gz"

#: §3.1.2 族组（闭集；键 = S3 `family`）。
FAMILY_GROUP: dict[str, str] = {
    "p1-vlm-survey-a2-p1-c1-s1": "a2",
    "p1-vlm-survey-a1-p1-c1-s2": "survey-dev",
    "detect-scout1": "demo-route",
    "m3-armA": "demo-route",
    "rate": "rate",
    "scene-val": "scene-val",
    "p1-vlm-survey-a7-p1-c1-s1": "a7",
    "m3-armB": "m3-armB",
    "p1-vlm-survey-a3-p1-c1-s1": "survey-H",
    "p1-vlm-survey-a4-p1-c1-s1": "survey-H",
    "p1-vlm-survey-a6-p1-c1-s1": "survey-H",
    "p1-vlm-survey-a9-p1-c1-s1": "survey-H",
    "s004-qual": "s004",
    "s004-scout": "s004",
    "s004-smoke": "s004",
}
#: §3.1.1 三域（族级；原子一致性由 `assert_domains` 对 `splits.json` 复核）。
DOMAIN_OF_FAMILY: dict[str, str] = {
    "p1-vlm-survey-a2-p1-c1-s1": "T",
    "p1-vlm-survey-a1-p1-c1-s2": "T",
    "detect-scout1": "T",
    "m3-armA": "T",
    "rate": "T",
    "scene-val": "T",
    "p1-vlm-survey-a7-p1-c1-s1": "V",
    "m3-armB": "H",
    "p1-vlm-survey-a3-p1-c1-s1": "H",
    "p1-vlm-survey-a4-p1-c1-s1": "H",
    "p1-vlm-survey-a6-p1-c1-s1": "H",
    "p1-vlm-survey-a9-p1-c1-s1": "H",
    "s004-qual": "H",
    "s004-scout": "H",
    "s004-smoke": "H",
}
DOMAINS = ("T", "V", "H")
TRAIN_STRIDE = 2  # §3.1：训练帧按时间序每 2 帧取 1
VAL_STRIDE = 5  # §3.2：训练期 val = V 每 5 帧取 1


class DatasetFailure(RuntimeError):
    """AC-1：输入缺失、sha 不符、交集非空或规则冲突 → 整体失败（fail-closed）。"""


# --- 逐帧标签（纯函数，可合成反例）-------------------------------------------


def stratum_key(cls_name: str, status: str, side: str, group: str) -> str:
    return f"{cls_name}|{status}|{side}|{group}"


def layer_of(cls_name: str, status: str, side: str) -> str:
    """跨族组的层（`STRATUM_IGNORED` 的作用单位）：类别 × 状态 × 短边档。"""
    return f"{cls_name}|{status}|{side}"


def wildcard_reason(entry: Mapping[str, Any]) -> str | None:
    from tools.eng_sft.adapters import unity_s3  # noqa: PLC0415

    return unity_s3.wildcard_reason(dict(entry))


def target_box(entry: Mapping[str, Any]) -> list[float] | None:
    from tools.eng_sft.adapters import unity_s3  # noqa: PLC0415

    if DYNAMIC_TARGET_ID not in set(entry.get("blocking", ())):
        return None
    if not entry.get("target_source_bound"):
        return None
    return unity_s3.cropped_target_box(dict(entry))


def exclusion_reason(entry: Mapping[str, Any]) -> str | None:
    """整帧排除原因：既有 `wildcard_reason` 优先；否则 Q-1 的 `target_unbounded=true`。"""
    reason = wildcard_reason(entry)
    if reason is None and entry.get("target_unbounded") is True:
        reason = EXCLUSION_TARGET_UNBOUNDED
    return reason


def label_entry(
    entry: Mapping[str, Any],
    group: str,
    ignored_layers: Iterable[str] = (),
    target_visible_flag: bool | None = None,
) -> dict[str, Any]:
    """一条 S3 记录 → `{excluded, exclusion_reason, positives, ignores, status_counts}`。

    `target_visible_flag`：Q-2 离线真值可见性标志（仅演示路线会话由调用方给出；其他为 None）。
    只有逐字 `False` 才把目标框转 ignore；None 沿原规则。
    """
    ignored = set(ignored_layers)
    reason = exclusion_reason(entry)
    positives: list[dict[str, Any]] = []
    ignores: list[dict[str, Any]] = []
    counts: Counter = Counter()
    for obj in entry.get("objects", ()):
        object_id = str(obj.get("object_id"))
        status = obj.get("status")
        if status == "PHANTOM":
            if obj.get("visible_px"):
                box = common.xyxy_px_to_norm(obj["visible_px"])
                if box is not None:
                    ignores.append({"box": box, "why": "ii_phantom", "object_id": object_id})
                    counts["PHANTOM|ignore_ii"] += 1
                    continue
            counts["PHANTOM|no_box"] += 1
            continue
        if not object_id.startswith("Vehicle_"):
            continue
        if status == "NOT_IN_VIEW":
            counts["NOT_IN_VIEW|none"] += 1
            continue
        if status not in common.POSITIVE_STATUSES:
            raise DatasetFailure(f"{entry.get('frame_id')}: 未知状态 {status!r}")
        box = common.xyxy_px_to_norm(obj["visible_px"]) if obj.get("visible_px") else None
        if box is None:
            counts[f"{status}|no_box"] += 1
            continue
        side = common.short_side_px(box)
        if side < common.MIN_SIDE_PX:
            ignores.append({"box": box, "why": "i_small", "object_id": object_id})
            counts[f"{status}|ignore_i"] += 1
            continue
        bin_ = common.side_bin(side)
        if layer_of("vehicle", status, bin_) in ignored:
            ignores.append({"box": box, "why": "iii_stratum", "object_id": object_id})
            counts[f"{status}|ignore_iii"] += 1
            continue
        positives.append(
            {
                "cls": common.CLASS_VEHICLE,
                "object_id": object_id,
                "status": status,
                "box": box,
                "side_px": round(side, 4),
                "side_bin": bin_,
                "stratum": stratum_key("vehicle", status, bin_, group),
                "depth_m": obj.get("camera_depth_m"),
            }
        )
        counts[f"{status}|positive"] += 1
    t_box = target_box(entry) if reason is None else None
    if t_box is not None:
        side = common.short_side_px(t_box)
        if target_visible_flag is False:
            ignores.append({"box": t_box, "why": "iv_truth_invisible", "object_id": DYNAMIC_TARGET_ID})
            counts["TARGET|ignore_iv"] += 1
        elif side < common.MIN_SIDE_PX:
            ignores.append({"box": t_box, "why": "i_small", "object_id": DYNAMIC_TARGET_ID})
            counts["TARGET|ignore_i"] += 1
        elif layer_of("target", "-", common.side_bin(side)) in ignored:
            ignores.append({"box": t_box, "why": "iii_stratum", "object_id": DYNAMIC_TARGET_ID})
            counts["TARGET|ignore_iii"] += 1
        else:
            bin_ = common.side_bin(side)
            positives.append(
                {
                    "cls": common.CLASS_TARGET,
                    "object_id": DYNAMIC_TARGET_ID,
                    "status": "-",
                    "box": t_box,
                    "side_px": round(side, 4),
                    "side_bin": bin_,
                    "stratum": stratum_key("target", "-", bin_, group),
                    "depth_m": None,
                }
            )
            counts["TARGET|positive"] += 1
    return {
        "excluded": reason is not None,
        "exclusion_reason": reason,
        "positives": positives if reason is None else [],
        "ignores": ignores if reason is None else [],
        "status_counts": dict(sorted(counts.items())),
    }


# --- 域与断言 ---------------------------------------------------------------


def load_splits() -> dict[str, Any]:
    document = common.read_json(common.data_path(SPLITS_JSON))
    payload = document["payload"]
    atoms = payload["atoms"]["atoms"]
    atom_of_family = {family: atom for atom, families in atoms.items() for family in families}
    split_of_atom = {atom: split for split, values in payload["atom_assignment"].items() for atom in values}
    split_of_frame = {frame: split for split, frames in payload["frames"].items() for frame in frames}
    return {
        "atom_of_family": atom_of_family,
        "split_of_atom": split_of_atom,
        "split_of_frame": split_of_frame,
        "sha256": common.sha256_file(common.data_path(SPLITS_JSON)),
        "pairwise_disjoint": bool(payload["leakage_assertions"]["pairwise_disjoint"]),
    }


def expected_domain(split: str, family: str) -> str:
    """§3.1.1 由 (split, 族) 推出的域：train → T；dev → a7 为 V、其余 T；test → H。"""
    if split == "train":
        return "T"
    if split == "dev":
        return "V" if family == "p1-vlm-survey-a7-p1-c1-s1" else "T"
    if split == "test":
        return "H"
    raise DatasetFailure(f"族 {family} 所在 split {split!r} 不在三域定义内")


def assert_domains(frames: Sequence[Mapping[str, Any]], eval_shas: set[str], eval_ids: set[str]) -> dict[str, Any]:
    """AC-1 断言：T∩H、V∩H（帧 sha 与原子）、T∩V（帧 sha 与族）为空；609 行评估帧 ⊂ H。"""
    sha = {d: {f["sha256"] for f in frames if f["domain"] == d} for d in DOMAINS}
    atoms = {d: {f["atom"] for f in frames if f["domain"] == d} for d in DOMAINS}
    families = {d: {f["family"] for f in frames if f["domain"] == d} for d in DOMAINS}
    ids_h = {f["frame_id"] for f in frames if f["domain"] == "H"}
    # Q-1 重建后：评估集帧还须落在 H 的保留帧（非整帧排除）内，否则 H 评估用不到它。
    sha_h_kept = {f["sha256"] for f in frames if f["domain"] == "H" and not f.get("excluded", False)}
    ids_h_kept = {f["frame_id"] for f in frames if f["domain"] == "H" and not f.get("excluded", False)}
    result = {
        "T_H_sha": sorted(sha["T"] & sha["H"]),
        "V_H_sha": sorted(sha["V"] & sha["H"]),
        "T_V_sha": sorted(sha["T"] & sha["V"]),
        "T_H_atom": sorted(atoms["T"] & atoms["H"]),
        "V_H_atom": sorted(atoms["V"] & atoms["H"]),
        "T_V_family": sorted(families["T"] & families["V"]),
        "eval_sha_not_in_H": sorted(eval_shas - sha["H"]),
        "eval_frame_ids_not_in_H": sorted(eval_ids - ids_h),
        "eval_sha_not_in_H_retained": sorted(eval_shas - sha_h_kept),
        "eval_frame_ids_not_in_H_retained": sorted(eval_ids - ids_h_kept),
    }
    result["passed"] = not any(result[key] for key in result)
    if not result["passed"]:
        raise DatasetFailure(f"三域断言失败：{ {k: v[:3] for k, v in result.items() if v and k != 'passed'} }")
    return result


# --- 扫描 -------------------------------------------------------------------


_TRUTH_CACHE: dict[str, dict[int, dict[str, Any]]] = {}


def truth_visibility_flag(
    frame_id: str, family: str, families: Sequence[str] = DEMO_ROUTE_FLAG_FAMILIES
) -> tuple[bool | None, str]:
    """Q-2：演示路线帧的既有逐帧真值可见性标志（离线只读；AC-8）。

    返回 `(flag, provenance)`；flag 只取 bool 值，缺行/缺键/非 bool 一律 None（沿原规则）。
    """
    if family not in families:
        return None, "not_demo_route"
    from tools.dist_data import roots  # noqa: PLC0415

    source = roots.truth_source_for(frame_id)
    if source is None:
        return None, "no_truth_join"
    path, schema = source
    field_name = FLAG_FIELD_OF_SCHEMA.get(schema)
    if field_name is None:
        return None, f"schema_{schema}_no_flag"
    absolute = common.data_path(path)
    if schema == "scouting":
        if not absolute.is_file():
            return None, "truth_missing"
        row = json.loads(absolute.read_text(encoding="utf-8"))
        if Path(frame_id).stem != f"frame_{int(row['frame_id']):010d}":
            raise DatasetFailure(f"{frame_id}: scout 真值 frame_id 不符")
    else:
        rows = _TRUTH_CACHE.get(path)
        if rows is None:
            rows = {}
            with open(absolute, encoding="utf-8") as handle:
                for line in handle:
                    item = json.loads(line)
                    rows[int(item["frame_id"])] = item
            _TRUTH_CACHE[path] = rows
        row = rows.get(int(Path(frame_id).stem.split("_")[1]))
        if row is None:
            return None, "truth_row_missing"
    value = row.get(field_name)
    if not isinstance(value, bool):
        return None, f"{field_name}_not_bool"
    return value, field_name


def _scan_shard(args: tuple[str, list[str]]) -> list[dict[str, Any]]:
    shard_path, ignored_layers = args
    rows = []
    with gzip.open(shard_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            entry = json.loads(line)
            family = entry["family"]
            group = FAMILY_GROUP.get(family)
            if group is None:
                raise DatasetFailure(f"未知族 {family}")
            usable = bool(entry.get("layout_binding_valid")) and bool(entry.get("sidecar_complete"))
            flag, flag_source = truth_visibility_flag(entry["frame_id"], family) if usable else (None, "unusable")
            labels = label_entry(entry, group, ignored_layers, flag) if usable else {
                "excluded": True,
                "exclusion_reason": "UNUSABLE_ENTRY",
                "positives": [],
                "ignores": [],
                "status_counts": {},
            }
            image = common.data_path(entry["frame_id"])
            sidecar = image.with_suffix(".json")
            meta = json.loads(sidecar.read_text(encoding="utf-8"))
            rows.append(
                {
                    "frame_id": entry["frame_id"],
                    "family": family,
                    "group": group,
                    "session": str(Path(entry["frame_id"]).parent.as_posix()),
                    "sim_t": float(meta["simulation_time_s"]),
                    "sha256": common.sha256_file(image),
                    "target_unbounded": entry.get("target_unbounded") is True,
                    "target_visible_flag": flag,
                    "target_visible_flag_source": flag_source,
                    # 仅报告：非演示路线但有 scouting 标志的 s004-scout，其标志不进标签（Q-2 字面）。
                    "target_visible_flag_shadow": (
                        truth_visibility_flag(entry["frame_id"], family, ("s004-scout",))[0]
                        if usable and family == "s004-scout"
                        else None
                    ),
                    **labels,
                }
            )
    return rows


def scan(ignored_layers: Sequence[str] = (), workers: int = 6) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest = common.read_json(common.data_path(CATALOG_MANIFEST))["payload"]
    shards = manifest["shards"]
    for shard in shards:
        path = common.data_path(CATALOG_ROOT) / shard["path"]
        if common.sha256_file(path) != shard["sha256"]:
            raise DatasetFailure(f"S3 分片 sha 不符：{shard['path']}")
    jobs = [(str(common.data_path(CATALOG_ROOT) / s["path"]), list(ignored_layers)) for s in shards]
    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for part in pool.map(_scan_shard, jobs):
            rows.extend(part)
    if len(rows) != CATALOG_EXPECTED_ROWS or len({r["frame_id"] for r in rows}) != len(rows):
        raise DatasetFailure(f"S3 行数 {len(rows)} ≠ {CATALOG_EXPECTED_ROWS} 或帧 ID 重复")
    identity = {
        "data_root": str(common.DATA_ROOT),
        "catalog_manifest": CATALOG_MANIFEST,
        "catalog_manifest_sha256": common.sha256_file(common.data_path(CATALOG_MANIFEST)),
        "shards": len(shards),
        "rows": len(rows),
    }
    return rows, identity


def build(ignored_layers: Sequence[str] = (), *, prelim: bool = False, spotcheck_sha256: str | None = None) -> dict[str, Any]:
    rows, identity = scan(ignored_layers)
    splits = load_splits()
    if not splits["pairwise_disjoint"]:
        raise DatasetFailure("S4 leakage_assertions.pairwise_disjoint ≠ true")
    inventory = common.read_json(common.data_path(INVENTORY_JSON))
    inventory_sha = {r["path"]: r["sha256"] for r in inventory.get("payload", inventory)["records"] if r.get("kind") == "image"}
    mismatches = []
    split_conflicts = []
    for row in rows:
        atom = splits["atom_of_family"].get(row["family"])
        if atom is None:
            raise DatasetFailure(f"族 {row['family']} 不在任何原子")
        split = splits["split_of_atom"][atom]
        frame_split = splits["split_of_frame"].get(row["frame_id"])
        if frame_split is not None and frame_split != split:
            split_conflicts.append(row["frame_id"])
        domain = expected_domain(split, row["family"])
        if domain != DOMAIN_OF_FAMILY[row["family"]]:
            raise DatasetFailure(f"族 {row['family']} 的域 {domain} 与 §3.1.1 表不符")
        row["atom"] = atom
        row["split"] = split
        row["domain"] = domain
        recorded = inventory_sha.get(row["frame_id"])
        if recorded is None or recorded != row["sha256"]:
            mismatches.append(row["frame_id"])
    if mismatches:
        raise DatasetFailure(f"帧 sha 与 S1 清单不符或缺登记：{len(mismatches)}（{mismatches[:3]}）")
    if split_conflicts:
        raise DatasetFailure(f"帧级 split 与族级原子 split 冲突：{split_conflicts[:3]}")
    eval_rows = common.read_jsonl(common.data_path(EVAL_JSONL))
    if len(eval_rows) != EVAL_EXPECTED_ROWS:
        raise DatasetFailure(f"评估集行数 {len(eval_rows)} ≠ {EVAL_EXPECTED_ROWS}")
    assertions = assert_domains(rows, {r["frame_sha256"] for r in eval_rows}, {r["frame_id"] for r in eval_rows})
    rows.sort(key=lambda r: (r["domain"], r["session"], r["sim_t"], r["frame_id"]))
    index_path = PRELIM_INDEX_PATH if prelim else INDEX_PATH
    index_sha = common.write_jsonl(index_path, [{"identity": identity}] + rows)
    summary = summarize(rows)
    document = {
        "work_id": common.WORK_ID,
        "stage": "prelim（抽查前，无 STRATUM_IGNORED）" if prelim else "final",
        "identity": identity,
        "splits_sha256": splits["sha256"],
        "inventory_sha256": common.sha256_file(common.data_path(INVENTORY_JSON)),
        "eval_jsonl_sha256": common.sha256_file(common.data_path(EVAL_JSONL)),
        "label_rules": {
            "classes": {"0": "vehicle（object_id 以 Vehicle_ 开头）", "1": "target（dynamic-target，target_blocker_px 裁剪到画幅）"},
            "box": "visible_px 裁剪到画幅后归一化 top-left xywh",
            "positive_statuses": list(common.POSITIVE_STATUSES),
            "min_short_side_px": common.MIN_SIDE_PX,
            "ignore": {
                "i_small": "纳入状态但短边 < 12 px",
                "ii_phantom": "PHANTOM 且带框",
                "iii_stratum": "STRATUM_IGNORED 层",
                "iv_truth_invisible": "Q-2：演示路线会话既有真值可见性标志为 False 的目标框（训练填充、评估 IoA 过滤）",
            },
            "frame_exclusion": "unity_s3.wildcard_reason 非空（目标车在视野内但无可用框）；Q-1：target_unbounded=true（TARGET_UNBOUNDED）",
            "q2_flag_families": list(DEMO_ROUTE_FLAG_FAMILIES),
            "q2_flag_fields": FLAG_FIELD_OF_SCHEMA,
            "clarify_source": "提案「Q-1/Q-2 用户选 (a) 后的 AC-n 合同修订（CLARIFY，2026-09-28）」AC-1 两行",
            "stratum_ignored_layers": sorted(ignored_layers),
            "spotcheck_sha256": spotcheck_sha256,
        },
        "family_group": FAMILY_GROUP,
        "domain_of_family": DOMAIN_OF_FAMILY,
        "domain_assertions": assertions,
        "summary": summary,
        "q2_visibility_flags": visibility_flag_counts(rows),
        "index": {"path": common.rel_project(index_path), "sha256": index_sha, "in_repo": False},
    }
    if not prelim:
        frames_sha = common.write_jsonl(common.evidence("dataset-frames.jsonl.gz"), [frame_manifest_row(r) for r in rows])
        document["frames_manifest"] = {"path": common.rel_project(common.evidence("dataset-frames.jsonl.gz")), "sha256": frames_sha}
        common.write_json(common.evidence("dataset.json"), document)
    else:
        common.write_json(DATASET_DIR / "dataset-prelim.json", document)
    return document


def visibility_flag_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Q-2 标志的逐族计数（仅保留帧、且带目标框时才影响标签）。"""
    out: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        if r["family"] not in DEMO_ROUTE_FLAG_FAMILIES and r["family"] != "s004-scout":
            continue
        has_target = any(i["object_id"] == DYNAMIC_TARGET_ID for i in r["ignores"]) or any(p["cls"] == 1 for p in r["positives"])
        state = "excluded" if r["excluded"] else ("target_box" if has_target else "no_target_box")
        flag = r["target_visible_flag"] if r["family"] in DEMO_ROUTE_FLAG_FAMILIES else f"shadow:{r.get('target_visible_flag_shadow')}"
        out[r["family"]][f"{state}|flag={flag}"] += 1
    return {family: dict(sorted(counter.items())) for family, counter in sorted(out.items())}


def frame_manifest_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "frame_id": row["frame_id"],
        "sha256": row["sha256"],
        "family": row["family"],
        "atom": row["atom"],
        "domain": row["domain"],
        "excluded": row["excluded"],
        "exclusion_reason": row["exclusion_reason"],
        "target_visible_flag": row.get("target_visible_flag"),
        "status_counts": row["status_counts"],
        "positives": {"vehicle": sum(1 for p in row["positives"] if p["cls"] == 0), "target": sum(1 for p in row["positives"] if p["cls"] == 1)},
        "ignores": len(row["ignores"]),
    }


def summarize(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for domain in DOMAINS:
        subset = [r for r in rows if r["domain"] == domain]
        status: Counter = Counter()
        for r in subset:
            status.update(r["status_counts"])
        ignores: Counter = Counter(i["why"] for r in subset for i in r["ignores"])
        positives: Counter = Counter()
        for r in subset:
            for p in r["positives"]:
                positives[f"{common.CLASS_NAMES[p['cls']]}|{p['status']}|{common.stratum_of(p['side_px'])}"] += 1
        out[domain] = {
            "frames": len(subset),
            "excluded_frames": sum(1 for r in subset if r["excluded"]),
            "retained_frames": sum(1 for r in subset if not r["excluded"]),
            "target_unbounded_frames": sum(1 for r in subset if r.get("target_unbounded")),
            "exclusion_reasons": dict(Counter(r["exclusion_reason"] for r in subset if r["excluded"])),
            "frames_with_target": sum(1 for r in subset if any(p["cls"] == 1 for p in r["positives"])),
            "families": dict(sorted(Counter(r["family"] for r in subset).items())),
            "atoms": sorted({r["atom"] for r in subset}),
            "status_counts": dict(sorted(status.items())),
            "ignore_counts": dict(sorted(ignores.items())),
            "positives_by_class_status_stratum": dict(sorted(positives.items())),
        }
    return out


def load_index(path: Path = INDEX_PATH) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = common.read_jsonl(path)
    return rows[0]["identity"], rows[1:]


def sessions_in_time_order(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["session"]].append(row)
    for items in grouped.values():
        items.sort(key=lambda r: (r["sim_t"], r["frame_id"]))
    return dict(sorted(grouped.items()))


def subsample(rows: Iterable[Mapping[str, Any]], stride: int) -> list[Mapping[str, Any]]:
    """按会话、时间序每 `stride` 帧取 1（取第 0、stride、2·stride… 帧），再剔除整帧排除帧。"""
    chosen = []
    for items in sessions_in_time_order(rows).values():
        chosen.extend(item for position, item in enumerate(items) if position % stride == 0 and not item["excluded"])
    return chosen


def main(argv: Sequence[str] | None = None) -> None:
    import argparse  # noqa: PLC0415

    parser = argparse.ArgumentParser(description="P1-ENG-FAST-002 数据集构建")
    parser.add_argument("mode", choices=("prelim", "final"))
    args = parser.parse_args(argv)
    if args.mode == "prelim":
        document = build(prelim=True)
    else:
        from tools.eng_det import spotcheck  # noqa: PLC0415

        decision = spotcheck.load_decision()
        document = build(decision["stratum_ignored_layers"], spotcheck_sha256=decision["sha256"])
    print(json.dumps({d: {k: document["summary"][d][k] for k in ("frames", "excluded_frames", "frames_with_target")} for d in DOMAINS}, ensure_ascii=False))


if __name__ == "__main__":
    main()
