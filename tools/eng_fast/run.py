#!/usr/bin/env python3
"""P1-ENG-FAST-001 编排入口：按阶段执行、动作前扣额（§5 信封）、证据落盘。

用法（Mac 端一律用 `.venv-yoloe/bin/python -m tools.eng_fast.run <stage>`）：
`inputs` → `detect`（YOLOE 启动 1）→ `recall` → `margin`（DINOv2 启动 1）→ `replay`（需 `lap`）→
`armd`（DINOv2 启动 1）→ `pack` →（5060：`tools/eng_fast/vlm_remote.py run`）→ `score` →
`latency`（YOLOE 1 + DINOv2 1）→ `report`。每个模型阶段是一次独立进程启动。
"""

from __future__ import annotations

import os
import sys

sys.dont_write_bytecode = True  # 冻结 DINOv2 源码在 runtime/ 下：不得写 __pycache__（AC-9）
os.environ.setdefault("YOLO_AUTOINSTALL", "False")  # 不让 ultralytics 自动安装任何依赖（§5）
os.environ.setdefault("YOLO_OFFLINE", "True")

import argparse  # noqa: E402
from collections import defaultdict  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, Mapping, Sequence  # noqa: E402

from tools.eng_fast import common, inputs, ledger  # noqa: E402

CACHE = common.OUT_ROOT / "cache"
DET_DIR = CACHE / "detections"
STAGE_INPUTS = CACHE / "stage-inputs.json"
EVIDENCE = {
    name: common.EVIDENCE_DIR / f"{common.WORK_ID}-{name}"
    for name in ("inputs.json", "recall.json", "margin.json", "replay.json", "vlm-arms.json", "latency.json", "ledger.json", "report.md")
}
BANK_OF_SOURCE = {"scout-1": "a2", "body-armA": "a2", "scout-4": "td", "body-armB": "td", "catalog-448": "td"}


def source_key(sequence: inputs.Sequence_) -> str:
    if sequence.source != "body":
        return sequence.source
    return "body-armA" if "-arm-a-" in sequence.sequence else "body-armB"


# --- inputs ----------------------------------------------------------------


def stage_inputs() -> dict[str, Any]:
    sequences = inputs.load_sequences()
    identity, index = inputs.load_catalog_index()
    splits = inputs.load_splits()
    inventory = inputs.load_inventory_index()
    rows = inputs.load_eval_rows()
    if not splits.pairwise_disjoint:
        raise inputs.InputFailure("S4 leakage_assertions.pairwise_disjoint ≠ true")

    def verify_frame(path: str) -> str:
        if not common.absolute(path).is_file():
            raise inputs.InputFailure(f"帧缺失 {path}")
        actual = common.sha256_file(path)
        record = inventory.get(path)
        if record is not None and record[0] != actual:
            raise inputs.InputFailure(f"帧 sha 与 S1 清单不符 {path}")
        return actual

    sources: dict[str, dict[str, Any]] = {}
    evaluated_shas: dict[str, set[str]] = defaultdict(set)
    evaluated_atoms: dict[str, set[str]] = defaultdict(set)
    for sequence in sequences:
        key = source_key(sequence)
        frames = []
        for frame in sequence.frames:
            family = index.get(frame.path, {}).get("family")
            atom = splits.atom_of(frame.path, family)
            sha = verify_frame(frame.path)
            evaluated_shas[key].add(sha)
            evaluated_atoms[key].add(atom)
            frames.append({"path": frame.path, "sha256": sha, "frame_id": frame.frame_number, "has_truth": frame.has_truth})
        truth_files = sorted({f.truth_path for f in sequence.frames if f.truth_path})
        sources.setdefault(key, {"sequences": []})["sequences"].append(
            {
                "sequence": sequence.sequence,
                "truth_schema": sequence.truth_schema,
                "frames": len(sequence.frames),
                "paired": sum(1 for f in sequence.frames if f.has_truth),
                "visible_with_box": sum(1 for f in sequence.frames if f.visible),
                "unpaired_reasons": sequence.unpaired,
                "frame_sha256": frames,
                "truth_files_sha256": {path: common.sha256_file(path) for path in truth_files}
                if truth_files
                else {"m3_body_truth.jsonl": common.sha256_file(Path(sequence.frames[0].path).parent.parent / "m3_body_truth.jsonl")},
            }
        )
    catalog_frames = sorted({row["frame_id"] for row in rows})
    catalog_entries = []
    for frame_id in catalog_frames:
        row = index.get(frame_id)
        if row is None:
            raise inputs.InputFailure(f"评估帧不在 S3 目录：{frame_id}")
        atom = splits.atom_of(frame_id, row["family"])
        sha = verify_frame(frame_id)
        evaluated_shas["catalog-448"].add(sha)
        evaluated_atoms["catalog-448"].add(atom)
        catalog_entries.append({"path": frame_id, "sha256": sha, "family": row["family"], "atom": atom})
    upload_mismatch = [
        r["row_id"]
        for r in rows
        if common.sha256_file(Path(inputs.UPLOAD_FRAMES) / r["frame_path"]) != r["frame_sha256"]
        or r["frame_sha256"] not in evaluated_shas["catalog-448"]
    ]
    if upload_mismatch:
        raise inputs.InputFailure(f"609 行上传帧 sha 不符：{upload_mismatch[:5]}")
    sources["catalog-448"] = {"frames": len(catalog_entries), "frame_sha256": catalog_entries}

    sha_of = {frame_id: inventory[frame_id][0] for frame_id in index if frame_id in inventory}
    dev, test = splits.atoms_of_split["dev"], splits.atoms_of_split["test"]
    banks = {
        "a2": inputs.select_bank(inputs.bank_pool(index, splits, dev + test), sha_of),
        "td": inputs.select_bank(inputs.bank_pool(index, splits, test), sha_of),
    }
    for bank in banks.values():
        refs = list(bank["vehicle"]) + ([bank["target_primitive"]] if bank["target_primitive"] else [])
        for ref in refs:
            ref["sha256"] = verify_frame(ref["frame_id"])
    ref_shas = {
        ref["frame_id"]: ref["sha256"]
        for bank in banks.values()
        for ref in list(bank["vehicle"]) + ([bank["target_primitive"]] if bank["target_primitive"] else [])
    }
    assertions = {}
    for key, bank_name in BANK_OF_SOURCE.items():
        assertions[key] = {
            "bank": bank_name,
            "evaluated_atoms": sorted(evaluated_atoms[key]),
            **inputs.bank_assertions(banks[bank_name], evaluated_shas[key], evaluated_atoms[key], ref_shas),
        }
    document = {
        "work_id": common.WORK_ID,
        "catalog_index": identity,
        "splits_sha256": splits.sha256,
        "splits_pairwise_disjoint": splits.pairwise_disjoint,
        "atoms": splits.families_of_atom,
        "atoms_of_split": splits.atoms_of_split,
        "field_catalog_sha256": common.sha256_file(inputs.FIELD_CATALOG_JSON),
        "inventory_sha256": common.sha256_file(inputs.INVENTORY_JSON),
        "eval": {
            "path": inputs.EVAL_JSONL,
            "sha256": common.sha256_file(inputs.EVAL_JSONL),
            "rows": len(rows),
            "predictions": {
                "A_base": {"path": inputs.PRED_BASE, "sha256": common.sha256_file(inputs.PRED_BASE)},
                "A_C2": {"path": inputs.PRED_C2, "sha256": common.sha256_file(inputs.PRED_C2)},
            },
        },
        "sources": sources,
        "banks": banks,
        "bank_of_source": BANK_OF_SOURCE,
        "isolation_assertions": assertions,
    }
    common.write_json(STAGE_INPUTS, document)
    return {
        "sources": {k: v.get("frames", sum(s["frames"] for s in v.get("sequences", []))) for k, v in sources.items()},
        "banks": {k: (v["vehicle_status"], len(v["vehicle"]), v["target_primitive_status"]) for k, v in banks.items()},
        "assertions": {k: v["passed"] for k, v in assertions.items()},
    }


# --- detect ------------------------------------------------------------------


def _det_path(detector: str, source: str) -> Path:
    return DET_DIR / f"{detector}__{source}.jsonl.gz"


def load_detections(detector: str, source: str) -> dict[str, list[list[float]]]:
    return {row["path"]: row["dets"] for row in common.read_jsonl(_det_path(detector, source))}


def stage_detect() -> dict[str, Any]:
    from tools.eng_fast import detect  # noqa: PLC0415

    document = common.read_json(STAGE_INPUTS)
    sequences = inputs.load_sequences()
    paths: dict[str, list[str]] = defaultdict(list)
    for sequence in sequences:
        paths[source_key(sequence)].extend(frame.path for frame in sequence.frames)
    paths["catalog-448"] = [entry["path"] for entry in document["sources"]["catalog-448"]["frame_sha256"]]
    identity_path = CACHE / "detect-identity.json"
    identities: dict[str, Any] = common.read_json(identity_path) if identity_path.exists() else {}
    todo_banks = [
        name
        for name in ("a2", "td")
        if any(not _det_path(f"T0-bank-{name}", s).exists() for s, b in BANK_OF_SOURCE.items() if b == name)
    ]
    todo_oracles = [spec for spec in (inputs.SCOUT1, inputs.SCOUT4) if not _det_path("T0-oracle", spec["source"]).exists()]
    if not todo_banks and not todo_oracles:
        return {"status": "ALREADY_DONE"}
    ledger.Ledger().charge(
        "mac_start_yoloe", stage="detect", note=f"T0-bank {todo_banks} + T0-oracle {[s['source'] for s in todo_oracles]}，cpu"
    )
    config = detect.frozen_config()
    identities["config_sha256"] = config.sha256
    for bank_name in todo_banks:
        detector = detect.build_t0_bank(document["banks"][bank_name], device="cpu", config=config)
        identities[f"T0-bank-{bank_name}"] = detector.identity
        common.write_json(identity_path, identities)
        for source, bank_of in BANK_OF_SOURCE.items():
            if bank_of != bank_name or _det_path(f"T0-bank-{bank_name}", source).exists():
                continue
            rows = detect.run_frames(detector, paths[source])
            common.write_jsonl(_det_path(f"T0-bank-{bank_name}", source), rows)
            print(f"T0-bank-{bank_name} {source}: {len(rows)} 帧", flush=True)
    for spec in todo_oracles:
        reference = detect.scout_reference(spec)
        detector = detect.build_t0_oracle(reference, device="cpu", config=config)
        identities[f"T0-oracle-{spec['source']}"] = {**detector.identity, "reference": reference}
        common.write_json(identity_path, identities)
        rows = detect.run_frames(detector, paths[spec["source"]])
        common.write_jsonl(_det_path("T0-oracle", spec["source"]), rows)
        print(f"T0-oracle {spec['source']}: {len(rows)} 帧", flush=True)
    common.write_json(identity_path, identities)
    return {k: v.get("embedding_sha256") for k, v in identities.items() if isinstance(v, dict)}


# --- recall -----------------------------------------------------------------


def _bank_object_ids(bank: Mapping[str, Any]) -> set[str]:
    return {box["object_id"] for ref in bank["vehicle"] for box in ref["boxes"]}


def catalog_frames(document: Mapping[str, Any], index: Mapping[str, Any]) -> list[inputs.FrameRec]:
    frames = []
    for entry in document["sources"]["catalog-448"]["frame_sha256"]:
        row = index[entry["path"]]
        objects = inputs.catalog_frame_objects(row)
        frames.append(
            inputs.FrameRec("catalog-448", "catalog-448", -1, entry["path"], 0.0, True, bool(objects), None, objects, None, "axial")
        )
    return frames


def stage_recall() -> dict[str, Any]:
    from tools.eng_fast import recall  # noqa: PLC0415

    document = common.read_json(STAGE_INPUTS)
    _identity, index = inputs.load_catalog_index()
    detect_identity = common.read_json(CACHE / "detect-identity.json")
    sequences = inputs.load_sequences()
    frames_by_source: dict[str, list[inputs.FrameRec]] = defaultdict(list)
    for sequence in sequences:
        frames_by_source[source_key(sequence)].extend(sequence.frames)
    frames_by_source["catalog-448"] = catalog_frames(document, index)
    banks = document["banks"]
    outcomes: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(dict)
    tables: dict[str, Any] = {"slant_range": {}, "axial_depth": {}}
    fp: dict[str, Any] = {}
    for source, frames in frames_by_source.items():
        axis = "axial_depth" if source == "catalog-448" else "slant_range"
        bank_name = BANK_OF_SOURCE[source]
        bank = banks[bank_name]
        dets = load_detections(f"T0-bank-{bank_name}", source)
        items = recall.object_outcomes(frames, dets, _bank_object_ids(bank))
        outcomes[source]["T0-bank"] = items
        table = recall.bucket_table(items)
        for key in list(table):
            kind = key.split("|")[0]
            if kind == common.TARGET_KIND_CATALOG and bank["vehicle_status"] != "COMPLETE":
                table[key]["bank_status"] = bank["vehicle_status"]
            if kind == common.TARGET_KIND_PRIMITIVE and bank["target_primitive_status"] != "COMPLETE":
                table[key] = {"status": recall.BANK_EMPTY}
        tables[axis][f"{source}|T0-bank-{bank_name}"] = table
        fp[f"{source}|T0-bank-{bank_name}"] = recall.fp_per_frame(frames, dets)
        if source in ("scout-1", "scout-4"):
            oracle = load_detections("T0-oracle", source)
            items = recall.object_outcomes(frames, oracle, set())
            outcomes[source]["T0-oracle"] = items
            tables[axis][f"{source}|T0-oracle"] = recall.bucket_table(items)
            fp[f"{source}|T0-oracle"] = recall.fp_per_frame(frames, oracle)
        else:
            tables[axis][f"{source}|T0-oracle"] = {"status": recall.NO_SESSION_REFERENCE}
        tables[axis][f"{source}|T1a"] = {"status": recall.NOT_AUTHORIZED}
        tables[axis][f"{source}|T1b"] = {"status": recall.NOT_AUTHORIZED}
    # R1 聚合：默认几何（scout-1 + BODY 九段），两个 bank 池混合 → 如实标注。
    default_geometry = outcomes["scout-1"]["T0-bank"] + outcomes["body-armA"]["T0-bank"] + outcomes["body-armB"]["T0-bank"]
    tables["slant_range"]["default-geometry(scout-1+BODY)|T0-bank(a2 for scout-1/armA, td for armB)"] = recall.bucket_table(
        default_geometry
    )
    body_all = outcomes["body-armA"]["T0-bank"] + outcomes["body-armB"]["T0-bank"]
    tables["slant_range"]["body-all|T0-bank(a2 armA, td armB)"] = recall.bucket_table(body_all)
    legacy = {}
    for spec in (inputs.SCOUT1, inputs.SCOUT4):
        result = common.read_json(common.absolute(spec["session_dir"]) / spec["legacy_result"])
        frames = {frame.frame_number: frame for frame in frames_by_source[spec["source"]]}
        legacy[spec["source"]] = {
            "legacy_result": f"{spec['session_dir']}/{spec['legacy_result']}",
            "legacy_result_sha256": common.sha256_file(common.absolute(spec["session_dir"]) / spec["legacy_result"]),
            **recall.legacy_alignment(result, frames, load_detections("T0-oracle", spec["source"]), expected=spec["legacy_expected"]),
        }
    applicability = {
        source: {
            "T0-bank": f"✓（池 {BANK_OF_SOURCE[source]}）",
            "T0-oracle": "✓（reference.json）" if source in ("scout-1", "scout-4") else recall.NO_SESSION_REFERENCE,
            "T1a/T1b": recall.NOT_AUTHORIZED,
            "distance_table": "axial_depth" if source == "catalog-448" else "slant_range",
        }
        for source in frames_by_source
    }
    evidence = {
        "work_id": common.WORK_ID,
        "gold": "amodal 投影 AABB（UNVERIFIED）",
        "iou_thresholds": list(common.IOU_THRESHOLDS),
        "detector_threshold": common.DETECTOR_CONFIDENCE_MIN,
        "distance_bins_m": list(common.DISTANCE_BINS),
        "strata_px": {"S": "<32", "M": "32-64", "L": ">=64"},
        "bootstrap": {"rounds": common.BOOTSTRAP_ROUNDS, "seed": common.BOOTSTRAP_SEED},
        "applicability_matrix": applicability,
        "bank_status": {k: {"vehicle": v["vehicle_status"], "target_primitive": v["target_primitive_status"]} for k, v in banks.items()},
        "detector_identity": detect_identity,
        "tables": tables,
        "fp_per_frame": fp,
        "legacy_alignment": legacy,
        "no_unbucketed_total": True,
    }
    common.write_json(CACHE / "recall-outcomes.json", outcomes)
    common.write_json(EVIDENCE["recall.json"], evidence)
    return {k: (v["recomputed"], v["disposition"]) for k, v in legacy.items()}


# --- margin -----------------------------------------------------------------


class _Embedder:
    """冻结 DinoV2Embedder 的缓存外壳：同一 (帧, 框) 只嵌一次；CROP_INVALID → None。"""

    def __init__(self, device: str = "cpu"):
        from controller.reanchor_models import DinoV2Embedder  # noqa: PLC0415
        from tools.eng_fast import detect  # noqa: PLC0415

        self.embedder = DinoV2Embedder(detect.frozen_config())
        if device != "cpu":
            self.embedder.model = self.embedder.model.to(device)
            self.embedder.device = device
        self.cache: dict[tuple[str, tuple[float, ...]], Any] = {}
        self.images: dict[str, Any] = {}
        self.read = detect.read_bgr

    def __call__(self, path: str, box: Sequence[float]) -> Sequence[float] | None:
        from controller.reanchor_models import CropInvalid  # noqa: PLC0415

        key = (path, tuple(round(float(v), 9) for v in box))
        if key not in self.cache:
            if path not in self.images:
                if len(self.images) > 64:
                    self.images.clear()
                self.images[path] = self.read(path)
            try:
                self.cache[key] = self.embedder.embed(self.images[path], box)
            except CropInvalid:
                self.cache[key] = None
        return self.cache[key]

    @staticmethod
    def cosine(left: Sequence[float], right: Sequence[float]) -> float:
        return max(-1.0, min(1.0, sum(a * b for a, b in zip(left, right))))


def stage_margin() -> dict[str, Any]:
    from tools.eng_fast import margin  # noqa: PLC0415

    _identity, index = inputs.load_catalog_index()
    usable = [frame for frame, row in index.items() if row.get("usable")]
    times = margin.load_sim_times(usable)
    eligible = {delta: margin.eligible_pairs(index, times, delta) for delta in margin.DELTAS_S}
    selected = [pair for delta in margin.DELTAS_S for pair in margin.select_pairs(eligible[delta])]
    ledger.Ledger().charge("mac_start_dinov2", stage="margin", note="P2a DINOv2 cpu")
    embed = _Embedder("cpu")
    scored = margin.score_pairs(selected, embed, _Embedder.cosine)
    config = common.read_json(common.PROJECT_ROOT / "config" / "detector-reanchor.models.json")
    evidence = {
        "work_id": common.WORK_ID,
        "embedder": {
            "name": config["appearance"]["name"],
            "weights_sha256": config["appearance"]["weights"]["sha256"],
            "source_archive_sha256": config["appearance"]["source"]["archive_sha256"],
            "verified_by": "controller.reanchor_models.DinoV2Embedder（构造器内核对源码/权重/许可 sha 与 torch 钉版）",
        },
        "deltas_s": list(margin.DELTAS_S),
        "tolerance_s": margin.TOLERANCE_S,
        "pair_cap_per_delta": margin.PAIR_CAP,
        "selection": "确定性哈希序 sha256(seed|Δ|anchor_frame|object_id) 取前 cap（IR-4）",
        "summary": margin.summarize(scored, {delta: len(pairs) for delta, pairs in eligible.items()}),
        "pairs": scored,
    }
    common.write_json(EVIDENCE["margin.json"], evidence)
    return {k: (v["eligible_pairs"], v["scored"], v["margin_ge_0_1_rate"], v["self_ge_0_5_rate"]) for k, v in evidence["summary"].items()}


# --- replay ------------------------------------------------------------------


def stage_replay() -> dict[str, Any]:
    from tools.eng_fast import detect, replay  # noqa: PLC0415

    try:
        lap_version = replay.require_lap()
    except replay.LapUnavailable as exc:
        evidence = {"work_id": common.WORK_ID, "status": "N/A(LAP_UNAVAILABLE)", "error": str(exc)}
        common.write_json(EVIDENCE["replay.json"], evidence)
        return evidence
    import ultralytics  # noqa: PLC0415

    sequences = inputs.load_sequences()
    document = common.read_json(STAGE_INPUTS)
    results: dict[str, Any] = {}
    for sequence in sequences:
        key = source_key(sequence)
        bank_name = BANK_OF_SOURCE[key]
        dets = load_detections(f"T0-bank-{bank_name}", key)
        times = [frame.sim_t for frame in sequence.frames]
        try:
            replay.check_timestamps(times)
        except replay.InvalidTimestamps:
            results[sequence.sequence] = {"status": "INVALID_TIMESTAMPS"}
            continue
        height, width = detect.read_bgr(sequence.frames[0].path).shape[:2]
        truth = [frame.target_box if frame.visible else None for frame in sequence.frames]
        start_bins = [
            common.distance_bin(frame.objects[0].distance_m) if frame.visible and frame.objects else "NA"
            for frame in sequence.frames
        ]
        per_algorithm = {}
        for algorithm in replay.ALGORITHMS:
            tracker = replay.make_tracker(algorithm)
            args = dict(vars(tracker.args))
            outputs = replay.run_sequence(
                tracker,
                [(dets[frame.path], (lambda path=frame.path: detect.read_bgr(path)), width, height) for frame in sequence.frames],
            )
            bindings = replay.bind(truth, outputs, width, height)
            buffer = int(tracker.max_frames_lost)
            per_algorithm[algorithm] = {
                "tracker_args": {k: v for k, v in args.items() if k != "device"},
                "frame_id_after": int(tracker.frame_id),
                "frames": len(sequence.frames),
                "one_update_per_frame": int(tracker.frame_id) == len(sequence.frames),
                "windows": {
                    f"{window:g}s": replay.window_summary(times, bindings, window, buffer, start_bins)
                    for window in replay.WINDOWS_S
                },
                "sequence": replay.sequence_metrics(times, bindings, buffer),
            }
        results[sequence.sequence] = {
            "source": key,
            "detector": f"T0-bank-{bank_name}（cpu，缓存检测）",
            "per_algorithm": per_algorithm,
        }
        print(f"replay {sequence.sequence} done", flush=True)
    evidence = {
        "work_id": common.WORK_ID,
        "status": "RUN",
        "lap_version": lap_version,
        "ultralytics_version": ultralytics.__version__,
        "interface": "BYTETracker(args)/BOTSORT(args)，args=IterableSimpleNamespace(**YAML.load(check_yaml(<algo>.yaml)))；无 frame_rate；每帧一次 update(Boxes(tensor[N,6]).cpu().numpy(), img)",
        "bind_iou": replay.BIND_IOU,
        "windows_s": list(replay.WINDOWS_S),
        "denominator": "D = KEPT + ID_SWITCH + LOST_BEYOND_BUFFER + UNRESOLVED_END_MISS",
        "missing_truth_frames_policy": "无真值文件的帧不在 V（按 INVISIBLE 调用帧处理；IR-5）",
        "sequences": results,
        "bank_of_source": BANK_OF_SOURCE,
        "banks": {k: v["vehicle_status"] for k, v in document["banks"].items()},
    }
    common.write_json(EVIDENCE["replay.json"], evidence)
    return {name: {a: {w: s["retention"] for w, s in r["per_algorithm"][a]["windows"].items()} for a in r["per_algorithm"]} for name, r in results.items() if "per_algorithm" in r}


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("stage")
    args = parser.parse_args(argv)
    from tools.eng_fast import run_more  # noqa: PLC0415

    stages = {
        "inputs": stage_inputs,
        "detect": stage_detect,
        "recall": stage_recall,
        "margin": stage_margin,
        "replay": stage_replay,
        **run_more.STAGES,
    }
    result = stages[args.stage]()
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
