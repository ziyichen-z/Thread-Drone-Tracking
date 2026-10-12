"""编排入口的后半：臂 D、臂 B/C 打包、四臂评分、时延（由 `run.main` 注册）。"""

from __future__ import annotations

from collections import Counter, defaultdict
import platform
import shutil
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.eng_fast import common, inputs, ledger
from tools.eng_fast.run import (
    CACHE,
    EVIDENCE,
    STAGE_INPUTS,
    _Embedder,
    load_detections,
)

ARMD_CACHE = CACHE / "armd-predictions.json"
PACK_DIR = common.OUT_ROOT / "vlm-pack"
RETURN_DIR = common.OUT_ROOT / "vlm-return"
QUERY_CAPS = {"base_start": 4, "query_total": 1700, "query_retry": 183}


def _eval_frames() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, list[dict[str, Any]]]]:
    rows = inputs.load_eval_rows()
    _identity, index = inputs.load_catalog_index()
    candidates = {frame: inputs.candidate_set(index[frame]) for frame in sorted({r["frame_id"] for r in rows})}
    return rows, index, candidates


# --- 臂 D ---------------------------------------------------------------------


def stage_armd() -> dict[str, Any]:
    from tools.eng_fast import baseline, detect  # noqa: PLC0415

    rows, index, candidates = _eval_frames()
    splits = inputs.load_splits()
    pool = inputs.bank_pool(index, splits, splits.atoms_of_split["test"])
    field_catalog = common.read_json(inputs.FIELD_CATALOG_JSON)["payload"]
    vocabulary = set(field_catalog["verified_color_vocabulary"])
    verified_colors = {
        object_id: record["color"]
        for object_id, record in field_catalog["objects"].items()
        if record.get("color_status") == "VERIFIED" and record.get("color") in vocabulary
    }
    bank = baseline.bank_samples(pool)
    protos = baseline.prototype_samples(pool, verified_colors)
    ledger.Ledger().charge("mac_start_dinov2", stage="armd", note="臂 D 裁图库 + 候选嵌入，cpu")
    embed = _Embedder("cpu")
    bank_vectors = []
    for sample in bank:
        vector = embed(sample["frame_id"], sample["box"])
        if vector is not None:
            bank_vectors.append((sample["class_word"], vector, sample["object_id"]))
    histograms = []
    for sample in protos:
        crop = _crop(detect.read_bgr(sample["frame_id"]), sample["box"])
        if crop is not None:
            histograms.append((sample["color_word"], baseline.hue_histogram(crop)))
    prototypes = baseline.build_prototypes(histograms)
    bank_objects = {object_id for _label, _vector, object_id in bank_vectors}
    predictions: dict[str, list[dict[str, Any]]] = {}
    for frame, items in candidates.items():
        image = detect.read_bgr(frame)
        predicted = []
        for candidate in items:
            vector = embed(frame, candidate["box"])
            crop = _crop(image, candidate["box"])
            label, neighbours = (
                baseline.knn_class(vector, [(label, emb) for label, emb, _ in bank_vectors]) if vector is not None else (None, [])
            )
            predicted.append(
                {
                    **candidate,
                    "pred_class": label,
                    "pred_color": baseline.nearest_color(baseline.hue_histogram(crop), prototypes) if crop is not None else None,
                    "knn_top5": [[round(s, 6), c] for s, c in neighbours],
                    "same_instance_in_bank": candidate["object_id"] in bank_objects,
                    "crop_invalid": vector is None,
                }
            )
        predictions[frame] = predicted
    document = {
        "bank": {
            "samples": len(bank),
            "embedded": len(bank_vectors),
            "objects": len(bank_objects),
            "per_object_cap": baseline.BANK_PER_OBJECT,
            "min_short_side_px": baseline.BANK_MIN_SHORT_SIDE_PX,
            "class_counts": dict(Counter(label for label, _v, _o in bank_vectors)),
        },
        "prototypes": {
            "samples": len(protos),
            "histograms": len(histograms),
            "colors": {color: sum(1 for c, _ in histograms if c == color) for color in sorted(prototypes)},
            "vectors": prototypes,
        },
        "predictions": predictions,
    }
    common.write_json(ARMD_CACHE, document)
    flat = [c for items in predictions.values() for c in items]
    return {
        "bank": document["bank"],
        "proto_colors": document["prototypes"]["colors"],
        "candidate_class_acc": round(sum(c["pred_class"] == c["class_word"] for c in flat) / len(flat), 4),
        "candidate_color_acc_where_known": round(
            sum(c["pred_color"] == c["color_word"] for c in flat if c["color_word"]) / max(1, sum(1 for c in flat if c["color_word"])),
            4,
        ),
        "same_instance_rate": round(sum(c["same_instance_in_bank"] for c in flat) / len(flat), 4),
    }


def _crop(image: Any, box: Sequence[float]) -> Any:
    height, width = image.shape[:2]
    left, top = max(0, int(box[0] * width)), max(0, int(box[1] * height))
    right, bottom = min(width, int(round((box[0] + box[2]) * width))), min(height, int(round((box[1] + box[3]) * height)))
    if right - left < 2 or bottom - top < 2:
        return None
    return image[top:bottom, left:right]


# --- 臂 B/C 打包 --------------------------------------------------------------


def stage_pack() -> dict[str, Any]:
    import cv2  # noqa: PLC0415

    from tools.eng_fast import detect, vlm_arms, vlm_remote  # noqa: PLC0415

    rows, _index, candidates = _eval_frames()
    if PACK_DIR.exists():
        shutil.rmtree(PACK_DIR)
    (PACK_DIR / "images").mkdir(parents=True)
    smoke_rows = [row["row_id"] for row in rows][: vlm_arms.SMOKE_ROWS]
    rendered: dict[tuple[str, str, int], tuple[str, str]] = {}
    files: dict[str, str] = {}
    queries = []
    prompts: dict[str, str] = {}
    k0_rows = []
    for row in rows:
        items = candidates[row["frame_id"]]
        if not items:
            k0_rows.append(row["row_id"])
            continue
        g4 = row["group"] == "G4"
        for arm in vlm_arms.ARMS_INDEXED:
            page_list = vlm_arms.pages(items) if arm == "B" else [list(items)]
            for page_number, page in enumerate(page_list):
                key = (row["frame_id"], arm, page_number)
                if key not in rendered:
                    image = detect.read_bgr(row["frame_id"])
                    canvas = vlm_arms.render_grid(image, page) if arm == "B" else vlm_arms.render_marks(image, page)
                    ok, encoded = cv2.imencode(".jpg", canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                    if not ok:
                        raise RuntimeError(f"JPEG 编码失败 {key}")
                    payload = encoded.tobytes()
                    sha = common.sha256_bytes(payload)
                    relative = f"images/{arm}-{sha}.jpg"
                    common.atomic_write_bytes(PACK_DIR / relative, payload)
                    files[relative] = sha
                    rendered[key] = (relative, sha)
                relative, sha = rendered[key]
                surface = row["surface"]
                text = vlm_arms.build_prompt_text(arm, surface, g4)
                prompt_sha = common.sha256_text(text)
                prompts[prompt_sha] = text
                queries.append(
                    {
                        "query_id": f"{arm}:{row['row_id']}:{page_number}",
                        "arm": arm,
                        "row_id": row["row_id"],
                        "page": page_number,
                        "image": relative,
                        "prompt_sha256": prompt_sha,
                        "allowed": [c["index"] for c in page],
                    }
                )
    header = {
        "work_id": common.WORK_ID,
        "caps": QUERY_CAPS,
        "model": f"{vlm_remote.BASE_REPO}@{vlm_remote.BASE_REVISION}",
        "max_new_tokens": vlm_remote.MAX_NEW_TOKENS,
        "smoke_row_ids": smoke_rows,
        "k0_rows": k0_rows,
        "queries": len(queries),
        "prompts": prompts,
    }
    import json  # noqa: PLC0415

    lines = [json.dumps({"header": header}, sort_keys=True, ensure_ascii=False)]
    lines += [json.dumps(q, sort_keys=True, ensure_ascii=False) for q in queries]
    index_bytes = ("\n".join(lines) + "\n").encode("utf-8")
    common.atomic_write_bytes(PACK_DIR / "index.jsonl", index_bytes)
    files["index.jsonl"] = common.sha256_bytes(index_bytes)
    script = Path(vlm_remote.__file__).read_bytes()
    common.atomic_write_bytes(PACK_DIR / "vlm_remote.py", script)
    files["vlm_remote.py"] = common.sha256_bytes(script)
    common.write_json(PACK_DIR / "manifest.json", {"files": files})
    sizes = {
        "images_bytes": sum((PACK_DIR / f).stat().st_size for f in files if f.startswith("images/")),
        "code_and_manifests_bytes": sum((PACK_DIR / f).stat().st_size for f in ("index.jsonl", "vlm_remote.py", "manifest.json")),
    }
    return {
        "queries": len(queries),
        "by_arm": dict(Counter(q["arm"] for q in queries)),
        "images": sum(1 for f in files if f.startswith("images/")),
        "k0_rows": len(k0_rows),
        **sizes,
        "manifest_sha256": common.sha256_file(PACK_DIR / "manifest.json"),
    }


# --- 评分 ---------------------------------------------------------------------


def _load_returned() -> tuple[dict[tuple[str, int], dict[str, Any]], dict[str, Any]]:
    from tools.eng_fast import vlm_remote  # noqa: PLC0415

    results = vlm_remote.done_results(RETURN_DIR / "results.jsonl")
    state = common.read_json(RETURN_DIR / "state.json") if (RETURN_DIR / "state.json").exists() else {"stopped_arms": {}}
    budget = common.read_json(RETURN_DIR / "budget.json")
    return results, {"state": state, "budget": budget}


def stage_score() -> dict[str, Any]:
    from tools.eng_fast import baseline, vlm_arms, vlm_remote  # noqa: PLC0415

    rows, _index, candidates = _eval_frames()
    header, queries = vlm_remote.load_index(PACK_DIR)
    results, remote = _load_returned()
    stopped = remote["state"].get("stopped_arms", {})
    by_row: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for query in queries:
        by_row[(query["arm"], query["row_id"])].append(query)
    # 解析在 Mac 复算一遍，与 5060 记录逐条比对（同一解析器，结果必须一致）。
    reparse_mismatch = []
    for (query_id, attempt), row in results.items():
        again = vlm_remote.parse_index_reply(
            row["raw_output"], next(q["allowed"] for q in queries if q["query_id"] == query_id), row["finish_reason"]
        )
        if again != row["parse"]:
            reparse_mismatch.append([query_id, attempt])
    outcomes: dict[str, dict[str, dict[str, Any]]] = {}
    arm_rows: dict[str, dict[str, Any]] = {}
    for arm in vlm_arms.ARMS_INDEXED:
        arm_out: dict[str, dict[str, Any]] = {}
        for row in rows:
            items = candidates[row["frame_id"]]
            number_to_id = {c["index"]: c["object_id"] for c in items}
            if not items:
                merged = vlm_arms.merge_pages(0, [])
            elif arm in stopped:
                merged = {"status": "NOT_RUN", "indices": [], "flag": f"NOT_RUN({stopped[arm]})"}
            else:
                page_queries = sorted(by_row[(arm, row["row_id"])], key=lambda q: q["page"])
                finals = [
                    vlm_arms.final_page_result(results.get((q["query_id"], 0)), results.get((q["query_id"], 1)))
                    for q in page_queries
                ]
                merged = vlm_arms.merge_pages(len(items), finals)
                if merged["status"] == "NOT_RUN":
                    merged["flag"] = "NOT_RUN(BUDGET)"
            selection = {
                "status": merged["status"],
                "object_ids": [number_to_id[i] for i in merged["indices"]],
                "flag": merged.get("flag"),
            }
            arm_out[row["row_id"]] = {**vlm_arms.row_outcome(row, selection), "selection": selection}
        outcomes[arm] = arm_out
    for label, path in (("A_base", inputs.PRED_BASE), ("A_C2", inputs.PRED_C2)):
        predictions = {p["row_id"]: p for p in common.read_jsonl(path)}
        if set(predictions) != {r["row_id"] for r in rows}:
            raise inputs.InputFailure(f"{label} 预测行与评估集不一一对应")
        arm_out = {}
        for row in rows:
            selection = vlm_arms.arm_a_selection(predictions[row["row_id"]], candidates[row["frame_id"]])
            arm_out[row["row_id"]] = {**vlm_arms.row_outcome(row, selection), "selection": selection}
        outcomes[label] = arm_out
    armd = common.read_json(ARMD_CACHE)["predictions"]
    arm_out = {}
    for row in rows:
        selection = baseline.decide(row, armd[row["frame_id"]])
        arm_out[row["row_id"]] = {**vlm_arms.row_outcome(row, selection), "selection": selection}
    outcomes["D"] = arm_out
    dets = load_detections("T0-bank-td", "catalog-448")
    from tools.eng_fast import recall  # noqa: PLC0415

    det_hit = {
        row["row_id"]: recall.max_iou(row["gold_boxes_norm_xywh"][0], dets[row["frame_id"]]) >= 0.30
        for row in rows
        if row["group"] in vlm_arms.SUCCESS_GROUPS
    }
    scores = {arm: vlm_arms.score_arm(rows, outcomes[arm]) for arm in ("A_base", "A_C2", "B", "C", "D")}
    paired = {arm: vlm_arms.paired_diagnostic(rows, outcomes[arm], det_hit) for arm in ("A_base", "A_C2", "B", "C", "D")}
    query_rows = []
    prompts: dict[str, str] = {}
    for (query_id, attempt), row in sorted(results.items()):
        query = next(q for q in queries if q["query_id"] == query_id)
        prompts[query["prompt_sha256"]] = header["prompts"][query["prompt_sha256"]]
        query_rows.append(
            {
                "query_id": query_id,
                "attempt": attempt,
                "arm": row["arm"],
                "row_id": row["row_id"],
                "prompt_sha256": row["prompt_sha256"],
                "image_sha256": row["image_sha256"],
                "input_tokens": row["input_tokens"],
                "gen_tokens": row["gen_tokens"],
                "finish_reason": row["finish_reason"],
                "latency_ms": row["latency_ms"],
                "image_grid_thw": row["image_grid_thw"],
                "raw_output": row["raw_output"],
                "parse": row["parse"],
            }
        )
    counts = Counter((r["arm"], r["attempt"]) for r in query_rows)
    evidence = {
        "work_id": common.WORK_ID,
        "candidate_set_reading": "IR-1：OK 目录车辆（适配器执行域）∪ 帧级已绑定动态目标（规则 ① 有框）",
        "k0_rows": sum(1 for r in rows if not candidates[r["frame_id"]]),
        "decoding": {"model": header["model"], "dtype": "bfloat16", "greedy": True, "max_new_tokens": header["max_new_tokens"], "image_resize": "none (PROCESSOR_SIZE)"},
        "prompts_by_sha256": prompts,
        "queries": {
            "baseline": {arm: counts[(arm, 0)] for arm in ("B", "C")},
            "retry": {arm: counts[(arm, 1)] for arm in ("B", "C")},
            "total": len(query_rows),
            "planned_baseline": dict(Counter(q["arm"] for q in queries)),
            "remote_budget": remote["budget"],
            "stopped_arms": stopped,
            "smoke": remote["state"].get("smoke", {}),
            "reparse_mismatch": reparse_mismatch,
        },
        "latency_ms": {arm: common.quantiles([r["latency_ms"] for r in query_rows if r["arm"] == arm]) for arm in ("B", "C")},
        "tokens": {
            arm: {
                "input": common.quantiles([r["input_tokens"] for r in query_rows if r["arm"] == arm]),
                "generated": common.quantiles([r["gen_tokens"] for r in query_rows if r["arm"] == arm]),
            }
            for arm in ("B", "C")
        },
        "scores": scores,
        "paired_diagnostic": paired,
        "paired_diagnostic_note": "同一行上两种独立测量的交集（det_hit = T0-bank-td cpu 对 gold 对象 max IoU ≥ 0.3）；不是任何链路的成功率或上界；B/C 的候选来自 oracle，检测器候选下的 VLM 成绩未测量",
        "arm_a_reference_sft002": "SFT-002 原 IoU 口径成绩原样引用见 docs/reviews/P1-ENG-SFT-002-stage-summary.md §4–§5（不重算）",
        "armd_disclosure": {
            key: value for key, value in common.read_json(ARMD_CACHE).items() if key != "predictions"
        },
        "row_outcomes": {arm: {rid: {k: v for k, v in out.items()} for rid, out in outcomes[arm].items()} for arm in outcomes},
        "query_rows": query_rows,
    }
    common.write_json(EVIDENCE["vlm-arms.json"], evidence)
    return {
        arm: {g: {k: (v["k"], v["n"]) for k, v in e.items() if isinstance(v, dict) and "k" in v} for g, e in s["groups"].items() if not e.get("excluded")}
        for arm, s in scores.items()
    }


# --- 时延 ---------------------------------------------------------------------


def stage_latency() -> dict[str, Any]:
    import torch  # noqa: PLC0415
    import ultralytics  # noqa: PLC0415

    from tools.eng_fast import detect, replay  # noqa: PLC0415

    document = common.read_json(STAGE_INPUTS)
    sequences = inputs.load_sequences()
    scout1 = next(s for s in sequences if s.source == "scout-1")
    frames = [f.path for f in scout1.frames][:320]
    crops = [(f.path, f.target_box) for f in scout1.frames if f.visible][:300]
    unity = subprocess.run(["pgrep", "-fl", "Unity"], capture_output=True, text=True).stdout.strip()
    editor = unity_editor_running(unity)
    ld = ledger.Ledger()
    ld.charge("mac_start_yoloe", stage="latency", note="T0-bank-a2 cpu+mps 同进程")
    ld.charge("mac_start_dinov2", stage="latency", note="DINOv2 cpu+mps 同进程")
    config = detect.frozen_config()
    images = [detect.read_bgr(p) for p in frames]
    detection: dict[str, Any] = {}
    boxes_by_device: dict[str, list[list[list[float]]]] = {}
    for device in ("cpu", "mps"):
        detector = detect.build_t0_bank(document["banks"]["a2"], device=device, config=config)
        for image in images[:5]:
            detector.detect(image)
        timings, outputs = [], []
        for image in images:
            dets, elapsed = detector.detect(image)
            timings.append(elapsed)
            outputs.append(dets)
        boxes_by_device[device] = outputs
        detection[device] = {"frames": len(timings), "warmup_frames": 5, **common.quantiles(timings, (0.5, 0.95)), "max": round(max(timings), 3)}
    diffs = []
    count_mismatch = 0
    for cpu_dets, mps_dets in zip(boxes_by_device["cpu"], boxes_by_device["mps"]):
        if len(cpu_dets) != len(mps_dets):
            count_mismatch += 1
            continue
        for a, b in zip(sorted(cpu_dets), sorted(mps_dets)):
            diffs.append(max(abs(x - y) for x, y in zip(a[:5], b[:5])))
    dino: dict[str, Any] = {}
    for device in ("cpu", "mps"):
        embed = _Embedder(device)
        loaded = {p: detect.read_bgr(p) for p, _ in crops[:5]}
        for path, box in crops[:5]:
            embed.embedder.embed(loaded[path], box)
        timings = []
        for path, box in crops:
            image = detect.read_bgr(path)
            started = time.perf_counter()
            embed.embedder.embed(image, box)
            timings.append((time.perf_counter() - started) * 1000.0)
        dino[device] = {"crops": len(timings), **common.quantiles(timings, (0.5, 0.95))}
    dets = load_detections("T0-bank-a2", "scout-1")
    tracker = replay.make_tracker("bytetrack")
    update_ms = []
    for frame in scout1.frames:
        boxes = replay.as_boxes(dets[frame.path], 640, 480)
        started = time.perf_counter()
        tracker.update(boxes, None)
        update_ms.append((time.perf_counter() - started) * 1000.0)
    chip = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
    evidence = {
        "work_id": common.WORK_ID,
        "host": {"chip": chip, "platform": platform.platform(), "torch": torch.__version__, "ultralytics": ultralytics.__version__},
        "unity_running_same_host": editor,
        "unity_processes": unity,
        "unity_rule": "只认 Unity 编辑器进程（…/Unity.app/Contents/MacOS/Unity）；Unity Hub 不算",
        "detector": "T0-bank-a2（scout-1 前 320 帧，imgsz 640，conf 0.25；含预处理，不含读盘）",
        "detection_ms": detection,
        "cpu_mps_box_consistency": {"frames": len(frames), "count_mismatch_frames": count_mismatch, "max_abs_coord_or_score_diff": round(max(diffs), 6) if diffs else None},
        "dinov2_single_crop_ms": dino,
        "bytetrack_update_ms_cpu": {"calls": len(update_ms), **common.quantiles(update_ms, (0.5, 0.95))},
        "scope_note": "只报 Mac 桌面数字；不含任何 Jetson/TensorRT/5060 检测时延（§2.2-3）",
    }
    common.write_json(EVIDENCE["latency.json"], evidence)
    return {k: evidence[k] for k in ("detection_ms", "dinov2_single_crop_ms", "bytetrack_update_ms_cpu", "cpu_mps_box_consistency")}


def unity_editor_running(pgrep_output: str) -> bool:
    """同机是否运行 Unity 编辑器（Unity Hub 及其辅助进程不算）。"""
    return any(
        "Unity.app/Contents/MacOS/Unity" in line and "Unity Hub" not in line for line in pgrep_output.splitlines()
    )


def stage_report() -> dict[str, Any]:
    from tools.eng_fast import report  # noqa: PLC0415

    return report.build()


STAGES = {
    "armd": stage_armd,
    "pack": stage_pack,
    "score": stage_score,
    "latency": stage_latency,
    "report": stage_report,
}
