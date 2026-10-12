#!/usr/bin/env python3
"""P1-ENG-ACQ-001 离线线束命令行（§3.9；解释器 = 数据根 `.venv-yoloe`）。

  verify                          资产散列与三序列完整性（AC-11、H-2）→ `-assets.json`
  replay [--seq S] [--gmc G] [--buffer B]   常驻关联回放（每个 序列×gmc×buffer 计 1 次序列回放）→ 记录流 + E2 分表
  e2-report                       E2 汇总 + 位姿自检表（零回放）→ `-e2.json`
  e1 --perturb none|c2_quantiles [--run N]  E1 解析（读 buffer 30 记录流；第二级 NanoTrack）→ outputs 分臂结果
  e1-merge                        合并两臂、核对两次运行字节一致 → `-e1.json`
  ledger-note --kind K --label L --wall S [--replays N]   记入线束外的本机 CPU 工作（测试等）
  cleanup-inventory               H-5 清单（只读盘点）→ `-cleanup.json`
  cleanup-apply                   清单提交后移动所列本地 `runtime/hold-diag-loopb-*` 到废纸篓（可恢复）并记结果

每个会消耗的命令先过信封守卫（回放次数 ≤ 40、全部本机 CPU 墙钟 ≤ 3 h，先到者即停），成功、失败都记账。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import os  # noqa: E402

os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")  # NanoTrack 每次构造的 DNN 目标告警不入日志

from tools.eng_acq import common, data  # noqa: E402

E1_ARMS = ("none", "c2_quantiles")


def _cmd(argv: list[str]) -> str:
    return "tools/eng_acq/run.py " + " ".join(argv)


# --- verify -------------------------------------------------------------------------


def cmd_verify(argv: list[str]) -> int:
    with common.charged("verify", "assets+integrity", sequence_replays=0, cmd=_cmd(argv)):
        spec = common.read_json(data.SPEC)
        sequences = data.load_sequences()
        jpeg = data.verify_all_jpegs(sequences)
        nano_spec = common.read_json(common.PROJECT_ROOT / "config" / "nanotrack-v2.models.json")
        items = []

        def item(label: str, path: Path, expected: str | None, source: str, prefix_suffix: tuple[str, str] | None = None) -> None:
            actual = common.sha256_file(path)
            ok = actual == expected if expected else (actual.startswith(prefix_suffix[0]) and actual.endswith(prefix_suffix[1]) if prefix_suffix else None)
            items.append({"label": label, "path": common.rel(path), "sha256": actual, "size_bytes": path.stat().st_size, "expected": expected or (f"{prefix_suffix[0]}…{prefix_suffix[1]}" if prefix_suffix else None), "source": source, "match": ok})

        item("detector weights last.pt", common.PROJECT_ROOT / spec["weights"]["path"], spec["weights"]["sha256"], "config/det-assoc-v1.models.json weights.sha256（提案事实 3）")
        item("freeze.json", data.FREEZE, spec["freeze"]["sha256"], "config/det-assoc-v1.models.json freeze.sha256（提案事实 3）")
        item("frozen-B.jsonl.gz", data.CACHE_B, None, "提案事实 10（本会话前由构思角色只读复核）", ("412592fb", "da5c"))
        item("frozen-V.jsonl.gz", data.CACHE_V, None, "提案事实 10", ("783ec7e2", "c41"))
        item("catalog-index.jsonl.gz", common.data_path(data.INDEX), None, "提案事实 11（FAST-001 缓存；无既存散列记录，本次记录供后续比对）")
        item("catalog-sim-times.jsonl.gz", common.data_path(data.SIM_TIMES), None, "提案事实 11（同上）")
        item("P1-ENG-FAST-002-dataset-frames.jsonl.gz", data.DATASET_FRAMES, None, "逐帧 JPEG sha 参照（FAST-002 数据集清单，已入库）")
        for role in ("backbone", "neckhead"):
            model = nano_spec["models"][role]
            item(f"nanotrack-v2 {role}", common.data_path(data.NANOTRACK_DIR) / model["filename"], model["sha256"], "config/nanotrack-v2.models.json（提案事实 17）")
        weights_size_ok = (common.PROJECT_ROOT / spec["weights"]["path"]).stat().st_size == spec["weights"]["size_bytes"]
        frames = {name: {"segments": len(segs), "frames": sum(len(s) for s in segs), "static_pairs": sum(len(f.statics) for s in segs for f in s), "red_frames": sum(1 for s in segs for f in s if f.red is not None), "tag": data.SEQUENCES[name]["tag"]} for name, segs in sequences.items()}
        payload = {
            "work_id": common.WORK_ID,
            "assets": items,
            "weights_size_matches_spec": weights_size_ok,
            "sequences": frames,
            "frame_integrity": {**jpeg, "sidecar_frame_id_and_time_checked": sum(v["frames"] for v in frames.values()), "sim_time_tolerance_s": data.SIM_TIME_TOLERANCE_S},
            "all_match": all(i["match"] in (True, None) for i in items) and weights_size_ok,
            "unverifiable_without_prior_record": [i["label"] for i in items if i["match"] is None],
        }
        common.write_json(common.evidence("assets.json"), payload)
        print(json.dumps({"assets": len(items), "all_match": payload["all_match"], "jpeg_checked": jpeg["jpeg_sha_checked"]}))
    return 0


# --- replay -------------------------------------------------------------------------


def cmd_replay(argv: list[str]) -> int:
    from tools.eng_acq import e2  # noqa: PLC0415

    parser = argparse.ArgumentParser(prog="replay")
    parser.add_argument("--seq", action="append", choices=tuple(data.SEQUENCES))
    parser.add_argument("--gmc", action="append", choices=e2.GMC_SOURCES)
    parser.add_argument("--buffer", action="append", type=int, choices=e2.BUFFERS)
    parser.add_argument("--skip-done", action="store_true", help="跳过账本已记 ok 且产物存在的格（不重复消耗）")
    args = parser.parse_args(argv)
    seqs = args.seq or list(data.SEQUENCES)
    gmcs = args.gmc or list(e2.GMC_SOURCES)
    buffers = args.buffer or list(e2.BUFFERS)
    jobs = [(s, g, b) for s in seqs for g in gmcs for b in buffers]
    if args.skip_done:
        done = {e["label"] for e in common.load_ledger()["entries"] if e.get("kind") == "sequence_replay" and e.get("status") == "ok"}
        jobs = [(s, g, b) for s, g, b in jobs if not (f"{s}/{g}/b{b}" in done and e2.records_path(s, g, b).exists() and (common.OUT_DIR / "e2" / f"{s}-{g}-b{b}.json").exists())]
    common.require_budget(len(jobs))
    sequences = data.load_sequences(seqs)
    images = data.ImageCache(capacity=4)
    for sequence, gmc, buffer in jobs:
        guard = common.WallGuard()
        with common.charged("sequence_replay", f"{sequence}/{gmc}/b{buffer}", sequence_replays=1, cmd=_cmd(argv)) as extra:
            started = time.monotonic()
            segments = sequences[sequence]
            records = [e2.replay_segment(frames, gmc, buffer, images, guard) for frames in segments]
            per_segment = [e2.segment_metrics(frames, recs, buffer) for frames, recs in zip(segments, records)]
            summary = e2.summarize(sequence, gmc, buffer, per_segment)
            summary["frames"] = sum(len(s) for s in segments)
            summary["tag"] = data.SEQUENCES[sequence]["tag"]
            sha = e2.write_records(e2.records_path(sequence, gmc, buffer), {"sequence": sequence, "gmc_source": gmc, "track_buffer": buffer, "segments": [{"segment": s[0].segment, "frames": r} for s, r in zip(segments, records)]})
            summary["records_sha256"] = sha
            common.write_json(common.OUT_DIR / "e2" / f"{sequence}-{gmc}-b{buffer}.json", summary)
            extra["frames"] = summary["frames"]
            extra["jpeg_decodes"] = images.decodes
            print(json.dumps({"replay": f"{sequence}/{gmc}/b{buffer}", "s": round(time.monotonic() - started, 2), "retention": (summary["red_retention_13s_caliber_A"] or {}).get("retention")}), flush=True)
    return 0


def cmd_e2_report(argv: list[str]) -> int:
    from tools.eng_acq import e2  # noqa: PLC0415

    with common.charged("e2_report", "E2 汇总 + 位姿自检（零回放）", sequence_replays=0, cmd=_cmd(argv)):
        cells = []
        missing = []
        for sequence in data.SEQUENCES:
            for gmc in e2.GMC_SOURCES:
                for buffer in e2.BUFFERS:
                    path = common.OUT_DIR / "e2" / f"{sequence}-{gmc}-b{buffer}.json"
                    if path.exists():
                        cells.append(common.read_json(path))
                    else:
                        missing.append(f"{sequence}/{gmc}/b{buffer}")
        sequences = data.load_sequences()
        selfcheck = {name: e2.pose_selfcheck(segs) for name, segs in sequences.items()}
        payload = {
            "work_id": common.WORK_ID,
            "grid": {"sequences": list(data.SEQUENCES), "gmc_sources": list(e2.GMC_SOURCES), "track_buffer_calls": list(e2.BUFFERS)},
            "cells": cells,
            "missing_cells": missing,
            "h_sequences_used": False,
            "caliber": "FAST-001 R4 口径 A（red target, 13 s window, window_summary 七类结局与守恒式逐字复用）+ H-9 空窗断言",
            "pose_warp_selfcheck": {"primary": "a7", "min_rotation_deg": e2.SELFCHECK_MIN_ROTATION_DEG, "by_sequence": selfcheck},
            "descriptive_only": True,
        }
        common.write_json(common.evidence("e2.json"), payload)
        print(json.dumps({"cells": len(cells), "missing": missing, "a7_selfcheck": selfcheck["a7"]["center_error_px_pose_homography"]}))
    return 0


# --- e1 -----------------------------------------------------------------------------


def cmd_e1(argv: list[str]) -> int:
    from controller.trackers import NanoTrackV2Tracker  # noqa: PLC0415
    from tools.eng_acq import e1, e2  # noqa: PLC0415

    parser = argparse.ArgumentParser(prog="e1")
    parser.add_argument("--perturb", required=True, choices=("none", "c2_quantiles", "uniform"))
    parser.add_argument("--run", type=int, default=1)
    parser.add_argument("--seq", action="append", choices=tuple(data.SEQUENCES))
    args = parser.parse_args(argv)
    if args.perturb == "uniform":
        raise SystemExit("uniform is not selected by the user (§7 (i) → c2_quantiles); not executed")
    seqs = args.seq or list(data.SEQUENCES)
    guard = common.WallGuard()
    with common.charged("e1_resolution", f"E1 arm={args.perturb} run={args.run}", sequence_replays=0, cmd=_cmd(argv)) as extra:
        started = time.monotonic()
        sequences = data.load_sequences(seqs)
        images = data.ImageCache(capacity=256)
        model_dir = common.data_path(data.NANOTRACK_DIR)

        def sot_factory():
            return NanoTrackV2Tracker(model_dir=model_dir)

        layers: list[dict[str, Any]] = []
        budget: dict[str, Any] = {}
        realized_all: list[float] = []
        realized_by_sequence: dict[str, Any] = {}
        sot_runs = sot_frames = 0
        timing: dict[str, Any] = {}
        for sequence in seqs:
            segments = sequences[sequence]
            samples, realized = e1.build_samples(sequence, segments, args.perturb)
            realized_all.extend(realized)
            if realized:
                realized_by_sequence[sequence] = e1.realized_quantiles(realized)
            prefixes: dict[int, Any] = {}

            def prefix_for(segment_index: int, _segments=segments, _prefixes=prefixes):
                if segment_index not in _prefixes:
                    _prefixes[segment_index] = e1.PrefixSot(
                        _segments[segment_index], sot_factory, images.get, t_replay_s=2.0, maximum_source_age_s=128 / 5.0,
                        frame_cap=e1.frame_cap(sequence),
                    )
                return _prefixes[segment_index]

            for gmc in e2.GMC_SOURCES:
                loaded = e2.read_records(e2.records_path(sequence, gmc, 30))
                records = [segment["frames"] for segment in loaded["segments"]]
                if [len(r) for r in records] != [len(s) for s in segments]:
                    raise data.IntegrityStop(f"records for {sequence}/{gmc} do not match frames")
                tic = time.monotonic()
                combo = e1.run_combo(sequence, segments, records, samples, gmc, args.perturb, prefix_for, e2.rows_of, guard)
                timing[f"{sequence}/{gmc}"] = round(time.monotonic() - tic, 3)
                layers.extend(e1.aggregate(sequence, data.SEQUENCES[sequence]["tag"], samples, combo, gmc, args.perturb))
                unrun_cap = sum(1 for v in combo["outcomes"].values() if v.get("not_run") == "frame_cap")
                budget[f"{sequence}/{gmc}/{args.perturb}"] = {
                    "samples_k_o": len(samples),
                    "level2_triggered_k_o": combo["triggered"],
                    "level2_selected_k_o": combo["selected"],
                    "LEVEL2_SUBSAMPLED": combo["subsampled"],
                    "level2_designate_calls": combo["level2_calls"],
                    "not_run_frame_cap_k_o_delta": unrun_cap,
                    "cap_k_o": e1.level2_cap(sequence) if e1.level2_cap(sequence) is not None else "full_sample",
                    "cap_frames_per_k_o": e1.frame_cap(sequence),
                }
            for prefix in prefixes.values():
                sot_runs += prefix.sot_runs
                sot_frames += prefix.sot_frames
                if prefix.frame_cap != e1.frame_cap(sequence) or any(run.frames_computed > e1.frame_cap(sequence) for run in prefix.cache.values()):
                    raise AssertionError(f"SOT prefix exceeded {e1.frame_cap(sequence)} frames for {sequence}")
        for row in layers:
            if not e1.conservation_ok(row):
                raise AssertionError(f"conservation failed: {row}")
        perturbed = None
        if args.perturb == "c2_quantiles":
            achieved = e1.realized_quantiles(realized_all)
            differences = {key: round(abs(achieved[key] - e1.C2_QUANTILES[key]), 6) for key in e1.C2_QUANTILES}
            perturbed = {
                "model": "c2_quantiles",
                "source": e1.C2_SOURCE,
                "source_rows": 347,
                "source_quantiles": e1.C2_QUANTILES,
                "realized_quantiles": achieved,
                "realized_by_sequence": realized_by_sequence,
                "abs_differences": differences,
                "tolerance": e1.QUANTILE_TOLERANCE,
                "within_tolerance": all(v <= e1.QUANTILE_TOLERANCE for v in differences.values()),
                "seed": e1.PERTURB_SEED,
                "knots": [list(k) for k in e1.PERTURB_KNOTS],
                "reads_c2_prediction_file": False,
                "replays_h_frames": False,
            }
        payload = {
            "work_id": common.WORK_ID,
            "arm": args.perturb,
            "sequences": seqs,
            "deltas_s": list(e1.DELTAS_S),
            "buckets": list(e1.BUCKETS),
            "correct_iou": e1.CORRECT_IOU,
            "subsample_seed": e1.SUBSAMPLE_SEED,
            "resolver": {"tau": 0.5, "margin": 0.2, "backup": "track_center_inside_designated_box", "t_replay_s": 2.0, "history_depth": 128},
            "level2_budget": budget,
            "perturbed_arm": perturbed,
            "layers": layers,
        }
        out = common.OUT_DIR / "e1" / f"e1-{args.perturb}-run{args.run}.json"
        sha = common.write_json(out, payload)
        common.write_json(common.OUT_DIR / "e1" / f"e1-{args.perturb}-run{args.run}.timing.json", {"wall_s": round(time.monotonic() - started, 3), "combo_s": timing, "sot_runs": sot_runs, "sot_frames": sot_frames, "jpeg_decodes": images.decodes})
        extra.update({"level2_sot_runs": sot_runs, "level2_sot_frames": sot_frames, "output_sha256": sha, "jpeg_decodes": images.decodes})
        print(json.dumps({"arm": args.perturb, "run": args.run, "sha256": sha, "layers": len(layers), "sot_runs": sot_runs, "sot_frames": sot_frames, "s": round(time.monotonic() - started, 1)}), flush=True)
    return 0


def cmd_e1_merge(argv: list[str]) -> int:
    with common.charged("e1_merge", "E1 两臂合并与复现核对", sequence_replays=0, cmd=_cmd(argv)):
        arms: dict[str, Any] = {}
        reproducibility: dict[str, Any] = {}
        for arm in E1_ARMS:
            runs = sorted((common.OUT_DIR / "e1").glob(f"e1-{arm}-run*.json"))
            runs = [p for p in runs if not p.name.endswith(".timing.json")]
            if not runs:
                arms[arm] = None
                reproducibility[arm] = {"runs": 0, "status": "NOT_RUN"}
                continue
            digests = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in runs}
            reproducibility[arm] = {"runs": len(runs), "sha256": digests, "byte_identical": len(set(digests.values())) == 1 and len(runs) >= 2}
            arms[arm] = common.read_json(runs[0])
        clean = arms.get("none")
        perturbed = arms.get("c2_quantiles")
        layers = (clean or {}).get("layers", []) + (perturbed or {}).get("layers", [])
        statuses: dict[str, int] = {}
        for row in layers:
            statuses[row["status"]] = statuses.get(row["status"], 0) + 1
        payload = {
            "work_id": common.WORK_ID,
            "deltas_s": (clean or perturbed or {}).get("deltas_s"),
            "buckets": (clean or perturbed or {}).get("buckets"),
            "clean_arm": {k: v for k, v in (clean or {}).items() if k != "layers"} or None,
            "perturbed_arm": (perturbed or {}).get("perturbed_arm") if perturbed else {"status": "NOT_RUN"},
            "perturbed_arm_budget": (perturbed or {}).get("level2_budget"),
            "reproducibility": reproducibility,
            "layer_status_counts": statuses,
            "layers": layers,
            "descriptive_only": True,
        }
        common.write_json(common.evidence("e1.json"), payload)
        print(json.dumps({"layers": len(layers), "statuses": statuses, "repro": {k: v.get("byte_identical") for k, v in reproducibility.items()}}))
    return 0


# --- 账本备注与清理清单 -----------------------------------------------------------------


def cmd_ledger_note(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="ledger-note")
    parser.add_argument("--kind", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--wall", required=True, type=float)
    parser.add_argument("--replays", type=int, default=0)
    parser.add_argument("--note", default="")
    parser.add_argument("--status", default="ok")
    args = parser.parse_args(argv)
    common.require_budget(args.replays)
    common.append_entry(
        {"kind": args.kind, "label": args.label, "cmd": args.note, "started_utc": None, "ended_utc": common.utc_now(), "wall_s": round(args.wall, 3), "sequence_replays": args.replays, "status": args.status, "recorded_by": "ledger-note（外部计时，/usr/bin/time 或起止时间戳）"}
    )
    print(json.dumps(common.totals(common.load_ledger())))
    return 0


def cmd_cleanup_inventory(argv: list[str]) -> int:
    from tools.eng_acq import cleanup  # noqa: PLC0415

    with common.charged("cleanup_inventory", "H-5 只读盘点", sequence_replays=0, cmd=_cmd(argv)):
        payload = cleanup.inventory()
        common.write_json(common.evidence("cleanup.json"), payload)
        print(json.dumps({"entries": len(payload["entries"]), "delete_candidates": len(payload["delete_candidates"])}))
    return 0


def cmd_cleanup_apply(argv: list[str]) -> int:
    """AC-16 修订 1：清单已入证据（已提交且无未提交改动）后，才移动清单所列本地 hold 目录（可恢复）。"""
    import subprocess  # noqa: PLC0415

    from tools.eng_acq import cleanup  # noqa: PLC0415

    path = common.evidence("cleanup.json")
    relative = common.rel(path)
    committed = subprocess.run(["git", "log", "--oneline", "-1", "--", relative], cwd=common.PROJECT_ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", relative], cwd=common.PROJECT_ROOT, capture_output=True, text=True).stdout.strip()
    if not committed or dirty:
        raise SystemExit("清单须先提交入证据（AC-16 修订 1：先记后删）")
    payload = common.read_json(path)
    if payload.get("status") != "INVENTORY_WRITTEN_BEFORE_DELETION" or payload.get("deletion") is not None:
        raise SystemExit("清单状态不允许删除（已执行或非盘点态）")
    with common.charged("cleanup_apply", "H-5 本地 hold 目录移入废纸篓", sequence_replays=0, cmd=_cmd(argv)):
        payload["deletion"] = cleanup.apply(payload)
        payload["deletion"]["inventory_commit"] = committed
        payload["status"] = "DELETION_APPLIED_AFTER_INVENTORY"
        common.write_json(path, payload)
        print(json.dumps(payload["deletion"], ensure_ascii=False))
    return 0


COMMANDS = {
    "verify": cmd_verify,
    "replay": cmd_replay,
    "e2-report": cmd_e2_report,
    "e1": cmd_e1,
    "e1-merge": cmd_e1_merge,
    "ledger-note": cmd_ledger_note,
    "cleanup-inventory": cmd_cleanup_inventory,
    "cleanup-apply": cmd_cleanup_apply,
}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in COMMANDS:
        print(__doc__)
        return 2
    return COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
