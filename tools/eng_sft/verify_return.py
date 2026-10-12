#!/usr/bin/env python3
"""回传校验、本地选优与三份摘要（K3，本地专用；不进代码束）。

用户把云端 `returned/<job_id>/` 整个目录拷回本地
`outputs/eng-sft/P1-ENG-SFT-002/returned/<job_id>/` 之后，由实现角色依次运行：

1. `verify`：job-receipt 列出的每个文件逐个现算字节与 SHA，缺 / 多 / 不符 →
   `RETURN_HASH_MISMATCH`；收据里的两份清单 SHA 须等于本地 `package` / `bundle` 收据，
   `job_id` 的冻结收据前缀须等于本地冻结收据（表 K ⑦ 末句）。
2. `select`（作业 A 之后）：三个 adapter 的盲选层预测对本地 `select-eval.jsonl` 评分，
   按表 H 选优，结果写本地收据目录；再把作业 B 的命令告诉用户。
3. `summarise`（作业 B 之后）：用冻结的 `evaluate.py` 评分，写
   `docs/evidence/P1-ENG-SFT-002-{zero-shot-v2-summary,train-summary,eval-summary}.json`。

评分只在这里做，gold 文件（`select-eval.jsonl` / `eval.jsonl`）从不离开本机；本模块对这两份
文件先核对冻结收据里的 SHA 再用。跨环境分支按 AC-12 的签发日判定写
`NOT_RUN(SFT_003_NOT_DONE)`，不运行、不等待 003。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any, Iterable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_sft import cloud_runner, evaluate, receipts, train_lora  # noqa: E402

RETURNED_DIRNAME = "returned"
RETURNED_MAX_BYTES = 512 * 1024 * 1024
ADAPTER_MAX_BYTES = 200 * 1024 * 1024
LOCAL_ROOT_MAX_BYTES = 900 * 1024 * 1024
VERSIONED_FILE_MAX_BYTES = 2 * 1024 * 1024

EVIDENCE_DIR = Path("docs/evidence")
ZERO_SHOT_SUMMARY = EVIDENCE_DIR / f"{receipts.WORK_ID}-zero-shot-v2-summary.json"
TRAIN_SUMMARY = EVIDENCE_DIR / f"{receipts.WORK_ID}-train-summary.json"
EVAL_SUMMARY = EVIDENCE_DIR / f"{receipts.WORK_ID}-eval-summary.json"

SFT_003_NOT_DONE = "SFT_003_NOT_DONE"

ReturnHashMismatch = cloud_runner.ReturnHashMismatch


# --- 表 L：跨环境分支（本候选为签发日终态）---------------------------------------------


def transfer_decision(
    sft003_overall: str | None,
    sft003_freeze_receipt_present: bool,
    compatibility_problems: Sequence[str] = (),
) -> str:
    """表 L 的机械前置：003 未 DONE 或无冻结收据 → `NOT_RUN(SFT_003_NOT_DONE)`；
    兼容条件任一不满足 → `NOT_RUN(INCOMPATIBLE_EVAL_SCHEMA:<项>)`；否则 `RUN`。"""
    if sft003_overall != "DONE" or not sft003_freeze_receipt_present:
        return f"NOT_RUN({SFT_003_NOT_DONE})"
    if compatibility_problems:
        return "NOT_RUN(INCOMPATIBLE_EVAL_SCHEMA:" + ";".join(compatibility_problems) + ")"
    return "RUN"


def assert_transfer_frames_disjoint(
    transfer_frame_sha256: Iterable[str], train_select_frame_sha256: Iterable[str]
) -> None:
    """表 L (6)：跨环境帧 SHA ∩ 训练∪选层帧 SHA = ∅，否则拒绝（与 K4 泄漏断言同一原因）。"""
    leaked = sorted(set(transfer_frame_sha256) & set(train_select_frame_sha256))
    if leaked:
        raise receipts.ConservationMismatch(
            "跨环境评估帧进入了训练/选层集合", offending=leaked[:10]
        )


def package_frame_sha256(package_root: Path, names: Sequence[str] = ("train.jsonl", "select-eval.blind.jsonl")) -> set[str]:
    """数据包里训练与选层行引用的帧 SHA（文件名就是帧字节的 SHA）。"""
    shas: set[str] = set()
    for name in names:
        for row in train_lora.read_jsonl(Path(package_root) / "data" / name):
            shas.add(Path(row["frame_path"]).stem)
    return shas


# --- verify ------------------------------------------------------------------------


def _local(repo_root: Path, local_root: Path | None) -> Path:
    return Path(local_root) if local_root is not None else Path(repo_root) / receipts.LOCAL_ROOT


def verify_returned(
    job_dir: Path, *, repo_root: Path = PROJECT_ROOT, local_root: Path | None = None
) -> dict[str, Any]:
    """表 K ⑦ 末句 + AC-11：回传目录逐文件核对，并与本地 package / bundle 收据绑定。"""
    root = Path(repo_root)
    local = _local(root, local_root)
    job_dir = Path(job_dir)
    receipt_path = job_dir / cloud_runner.JOB_RECEIPT_NAME
    if not receipt_path.is_file():
        raise ReturnHashMismatch("回传目录缺 job-receipt.json", offending=[str(job_dir)])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    problems: list[dict[str, Any]] = []
    try:
        job_dir.resolve().relative_to((local / RETURNED_DIRNAME).resolve())
    except ValueError:
        problems.append({"problem": "RETURNED_OUTSIDE_LOCAL_ROOT", "path": str(job_dir)})
    if receipt.get("job_id") != job_dir.name:
        problems.append({"problem": "JOB_ID_DIR_MISMATCH", "job_id": receipt.get("job_id")})

    artifacts = receipt.get("artifacts") or {}
    on_disk = {
        path.relative_to(job_dir).as_posix(): path
        for path in sorted(job_dir.rglob("*"))
        if path.is_file() and path.name != cloud_runner.JOB_RECEIPT_NAME
    }
    for name in sorted(set(artifacts) - set(on_disk)):
        problems.append({"problem": "MISSING", "path": name})
    for name in sorted(set(on_disk) - set(artifacts)):
        problems.append({"problem": "EXTRA", "path": name})
    for name in sorted(set(artifacts) & set(on_disk)):
        path = on_disk[name]
        digest = receipts.sha256_file(path)
        if path.stat().st_size != artifacts[name].get("bytes") or digest != artifacts[name].get("sha256"):
            problems.append({"problem": "HASH_OR_SIZE_MISMATCH", "path": name,
                             "expected": artifacts[name].get("sha256"), "actual": digest})

    receipts_dir = local / receipts.RECEIPTS_DIRNAME
    freeze_path = receipts_dir / cloud_runner.FREEZE_RECEIPT_NAME
    package_path = receipts_dir / cloud_runner.PACKAGE_RECEIPT_NAME
    bundle_path = receipts_dir / cloud_runner.BUNDLE_RECEIPT_NAME
    for required in (freeze_path, package_path, bundle_path):
        if not required.is_file():
            problems.append({"problem": "LOCAL_RECEIPT_MISSING", "path": required.name})
    if not problems:
        freeze_sha = receipts.sha256_file(freeze_path)
        package_receipt = json.loads(package_path.read_text(encoding="utf-8"))
        bundle_receipt = json.loads(bundle_path.read_text(encoding="utf-8"))
        package = receipt.get("package") or {}
        if package.get("upload_manifest_sha256") != package_receipt.get("upload_manifest_sha256"):
            problems.append({"problem": "UPLOAD_MANIFEST_SHA", "returned": package.get("upload_manifest_sha256"),
                             "local": package_receipt.get("upload_manifest_sha256")})
        if package.get("code_manifest_sha256") != bundle_receipt.get("code_manifest_sha256"):
            problems.append({"problem": "CODE_MANIFEST_SHA", "returned": package.get("code_manifest_sha256"),
                             "local": bundle_receipt.get("code_manifest_sha256")})
        if not str(receipt.get("job_id", "")).endswith(f"-{freeze_sha[:8]}"):
            problems.append({"problem": "JOB_ID_FREEZE_PREFIX", "job_id": receipt.get("job_id")})
    returned_bytes = sum(path.stat().st_size for path in (local / RETURNED_DIRNAME).rglob("*") if path.is_file()) \
        if (local / RETURNED_DIRNAME).is_dir() else 0
    if returned_bytes > RETURNED_MAX_BYTES:
        problems.append({"problem": "RETURNED_OVER_512MB", "bytes": returned_bytes})
    for name, path in on_disk.items():
        if name.endswith("adapter_model.safetensors") and path.stat().st_size > ADAPTER_MAX_BYTES:
            problems.append({"problem": "ADAPTER_OVER_200MB", "path": name})
    if problems:
        raise ReturnHashMismatch("回传目录与作业收据或本地收据不符，拒绝评分", offending=problems[:20])
    return {
        "job_id": receipt["job_id"],
        "job_kind": receipt.get("job_kind"),
        "complete": bool(receipt.get("complete")),
        "outcome": receipt.get("outcome"),
        "job_receipt_sha256": receipts.sha256_file(receipt_path),
        "artifacts": len(artifacts),
        "returned_bytes": returned_bytes,
        "receipt": receipt,
    }


def _bound_gold(local: Path, name: str) -> tuple[Path, list[dict[str, Any]]]:
    """本地 gold 文件先核对冻结收据里的 SHA，再用来评分。"""
    path = local / "data" / name
    freeze = json.loads((local / receipts.RECEIPTS_DIRNAME / cloud_runner.FREEZE_RECEIPT_NAME)
                        .read_text(encoding="utf-8"))
    expected = freeze.get("jsonl", {}).get(name, {}).get("sha256")
    actual = receipts.sha256_file(path) if path.is_file() else None
    if actual is None or actual != expected:
        raise receipts.FrozenSetMismatch(
            f"本地 {name} 与冻结收据不符", offending=[{"file": name, "freeze": expected, "actual": actual}]
        )
    return path, train_lora.read_jsonl(path)


# --- select ------------------------------------------------------------------------


def select_adapter(
    job_a_dir: Path, *, repo_root: Path = PROJECT_ROOT, local_root: Path | None = None
) -> dict[str, Any]:
    """作业 A 回传后：盲选层预测本地评分 → 表 H 选优。"""
    started = time.monotonic()
    root = Path(repo_root)
    local = _local(root, local_root)
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    try:
        checked = verify_returned(job_a_dir, repo_root=root, local_root=local)
        receipt = checked["receipt"]
        if receipt.get("job_kind") != "A":
            raise ReturnHashMismatch("选优只消费作业 A 的回传", offending=[receipt.get("job_id")])
        _, gold_rows = _bound_gold(local, "select-eval.jsonl")
        scores: dict[str, Any] = {}
        missing: list[str] = []
        for config in train_lora.CANDIDATES:
            stage = (receipt.get("stages") or {}).get(config.name, {})
            path = Path(job_a_dir) / "runs" / config.name / "select-predictions.jsonl"
            if stage.get("status") != "succeeded" or not path.is_file():
                missing.append(config.name)
                continue
            scores[config.name] = train_lora.selection_score(gold_rows, train_lora.read_jsonl(path))
        choice = train_lora.select_best(scores)
        run = receipt["runs"][choice["chosen"]]
        document = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/selection/v1",
            "work_id": receipts.WORK_ID,
            "utc": receipts.utc_stamp(),
            "job_id": receipt["job_id"],
            "job_receipt_sha256": checked["job_receipt_sha256"],
            "scores": scores,
            "missing_runs": missing,
            "selection": choice,
            "chosen_adapter_sha256": run["adapter_sha256"],
            "select_eval_rows": len(gold_rows),
        }
        out = writer._write_json(writer.receipts_dir / f"selection-{receipt['job_id']}.json", document)
        writer.write_run_receipt(
            "return", started=started, outputs=[receipts.output_record(out)],
            extra={"stage_detail": "select", "job_id": receipt["job_id"], "chosen": choice["chosen"]},
        )
        return document
    except receipts.EngSftError as exc:
        writer.write_failure_receipt("return", exc.reason, exc.offending, message=str(exc))
        raise


# --- summarise ---------------------------------------------------------------------


def _write_evidence(root: Path, relative: Path, document: Mapping[str, Any]) -> dict[str, Any]:
    path = receipts.assert_output_allowed(root / relative, root)
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if len(payload.encode("utf-8")) > VERSIONED_FILE_MAX_BYTES:
        raise receipts.PackageIncomplete(
            f"受版本控制工件超过 2 MB：{relative}", offending=[str(relative)]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    return receipts.output_record(path)


def _model_ids(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    return sorted({str(row.get("model_id")) for row in rows})


FAILURE_CASE_LIMIT = 10
FAILURE_CASE_GROUPS: tuple[str, ...] = evaluate.SUCCESS_GROUPS + evaluate.SET_GROUPS + evaluate.NONE_GROUPS


def _row_failed(score: evaluate.RowScore) -> bool:
    """表 F 的行级结果：集合组看严格成功，其余看 Success / none；G3′ 诊断组没有失败定义。"""
    if score.group in evaluate.SET_GROUPS:
        return not score.strict_success
    return not score.success


def failure_cases(
    manifest_rows: Sequence[Mapping[str, Any]],
    predictions: Sequence[Mapping[str, Any]],
    *,
    gray_boxes: Mapping[str, Sequence[Sequence[float]]] | None = None,
    limit: int = FAILURE_CASE_LIMIT,
) -> dict[str, Any]:
    """AC-13：每个判定组 min(limit, 失败数) 条失败案例，按 `row_id` 升序取（确定性，不挑选）。

    图片指针相对本工作项本地根（`outputs/eng-sft/P1-ENG-SFT-002/`），`frame_id` 是原图路径。
    """
    scores = evaluate.score_rows(manifest_rows, predictions, gray_boxes=gray_boxes)
    rows = {row["row_id"]: row for row in manifest_rows}
    by_row = {row["row_id"]: row for row in predictions}
    output: dict[str, Any] = {}
    for group in FAILURE_CASE_GROUPS:
        failed = sorted((score for score in scores if score.group == group and _row_failed(score)),
                        key=lambda score: score.row_id)
        cases = []
        for score in failed[:limit]:
            row, prediction = rows[score.row_id], by_row[score.row_id]
            boxes = prediction.get("boxes_1000") or []
            gold = row.get("gold_boxes_norm_xywh") or []
            case = {
                "row_id": score.row_id,
                "surface": row.get("surface"),
                "gold_state": row.get("gold_state"),
                "gold_bbox_2d_1000": row.get("gold_bbox_2d_1000"),
                "status_pred": score.status_pred,
                "boxes_1000": boxes,
                "parse_error": score.parse_error,
                "raw_output": prediction.get("raw_output"),
                "stratum": score.stratum,
                "class": score.class_word,
                "seen_target": score.seen_target,
                "image": f"{cloud_runner.UPLOAD_DIRNAME}/{row['frame_path']}",
                "frame_id": row.get("frame_id"),
            }
            if group in evaluate.SET_GROUPS:
                case.update({"true_positive": score.true_positive, "false_positive": score.false_positive,
                             "false_negative": score.false_negative, "f1": score.f1})
            elif score.status_pred == "unique" and boxes and gold:
                case["iou"] = evaluate.iou(gold[0], boxes[0])
            cases.append(case)
        output[group] = {
            "rows": sum(1 for score in scores if score.group == group),
            "failures": len(failed),
            "shown": len(cases),
            "cases": cases,
        }
    return {"limit": limit, "order": "row_id ascending", "image_root": receipts.LOCAL_ROOT.as_posix(),
            "groups": output}


def _stage_accounting(receipts_by_job: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """各阶段启动/耗时与推理行数，对照信封（表 I「各阶段尝试与 GPU·h 账目」）。"""
    latest = receipts_by_job[-1].get("launches") or {}
    entries = latest.get("entries") or []
    per_kind: dict[str, dict[str, Any]] = {}
    rows_per_launch = {"zero_shot": 609, "smoke": 32, "train": 441, "eval": 609}
    for entry in entries:
        bucket = per_kind.setdefault(entry["kind"], {"launches": 0, "succeeded": 0, "elapsed_s": 0.0,
                                                     "statuses": []})
        bucket["launches"] += 1
        bucket["succeeded"] += 1 if entry.get("status") == "succeeded" else 0
        bucket["elapsed_s"] += float(entry.get("elapsed_s") or 0.0)
        bucket["statuses"].append(entry.get("status"))
    for kind, bucket in per_kind.items():
        bucket["limit"] = cloud_runner.STAGE_LIMITS.get(kind)
        bucket["inference_rows_upper_bound"] = bucket["launches"] * rows_per_launch.get(kind, 0)
    budgets = [job.get("budget") or {} for job in receipts_by_job]
    last_budget = budgets[-1] if budgets else {}
    return {
        "per_stage": per_kind,
        "total_launches": sum(bucket["launches"] for bucket in per_kind.values()),
        "total_launch_limit": cloud_runner.TOTAL_LAUNCH_LIMIT,
        "instance_hours_at_last_job_end": last_budget.get("elapsed_hours"),
        "estimated_usd_at_last_job_end": last_budget.get("estimated_usd"),
        "effective_cap_hours": last_budget.get("effective_cap_hours"),
        "cap_gpu_hours": cloud_runner.CAP_GPU_HOURS,
        "cap_usd": cloud_runner.CAP_USD,
        "inference_rows_envelope": 4264,
        "billing_note": "实例时长由 budget.json 起算；实际账单与费用由用户按 vast.ai 回填",
    }


def summarise(
    job_a_dir: Path,
    job_b_dir: Path | None = None,
    *,
    repo_root: Path = PROJECT_ROOT,
    local_root: Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """三份摘要：零样本（作业 A）、训练与选优（作业 A）、正式评估与表 G 判定（作业 B）。"""
    started = time.monotonic()
    root = Path(repo_root)
    local = _local(root, local_root)
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    try:
        checked_a = verify_returned(job_a_dir, repo_root=root, local_root=local)
        job_a = checked_a["receipt"]
        _, eval_rows = _bound_gold(local, "eval.jsonl")
        gray_boxes = evaluate.load_gray_boxes(eval_rows, repo_root=root, local_root=local)
        legacy = evaluate.load_legacy_predictions(local)
        zero_path = Path(job_a_dir) / "predictions" / "zero-shot.jsonl"
        zero_rows = train_lora.read_jsonl(zero_path)
        base_id = f"{train_lora.BASE_REPO}@{train_lora.BASE_REVISION}"
        if _model_ids(zero_rows) != [base_id]:
            raise ReturnHashMismatch("零样本预测不是 base 产出", offending=_model_ids(zero_rows))

        zero = evaluate.summarise(eval_rows, zero_rows, gray_boxes=gray_boxes, legacy_predictions=legacy)
        # 零样本是对照而非被测对象：非劣判定只在 eval-summary（微调 − 零样本）里成立。
        zero["verdict"].pop("vocabulary_non_inferiority", None)
        zero.update({
            "schema_version": f"{receipts.SCHEMA_PREFIX}/zero-shot-v2-summary/v1",
            "role": "prompt v2 zero-shot baseline (base model, no adapter)",
            "job_id": job_a["job_id"],
            "job_receipt_sha256": checked_a["job_receipt_sha256"],
            "predictions_sha256": receipts.sha256_file(zero_path),
            "model_id": base_id,
        })

        selection_path = local / receipts.RECEIPTS_DIRNAME / f"selection-{job_a['job_id']}.json"
        selection = json.loads(selection_path.read_text(encoding="utf-8")) if selection_path.is_file() else None
        # C1-K3-2：选优收据须绑定当前这份作业 A 回传（A 续跑后收据变了，旧选优作废，须重新 select）。
        if selection is not None and (selection.get("job_id") != job_a["job_id"]
                                      or selection.get("job_receipt_sha256") != checked_a["job_receipt_sha256"]):
            raise ReturnHashMismatch(
                "选优收据不是在当前作业 A 回传上做的：先对当前回传重新运行 select",
                offending=[{"selection_job_receipt_sha256": selection.get("job_receipt_sha256"),
                            "current_job_receipt_sha256": checked_a["job_receipt_sha256"]}],
            )
        env_path = Path(job_a_dir) / "env.json"
        runs = {}
        for name, run in sorted((job_a.get("runs") or {}).items()):
            runs[name] = {
                key: run.get(key) for key in (
                    "config", "steps", "warmup_steps", "epochs", "lr", "multiset_rows", "last_loss",
                    "elapsed_s", "peak_gpu_memory_bytes", "adapter_sha256", "adapter_bytes",
                    "train_log_sha256", "lora",
                )
            }
            runs[name]["select_predictions"] = (run.get("predictions") or {})
            if selection:
                runs[name]["selection_score"] = selection["scores"].get(name)
        smoke = (job_a.get("stages") or {}).get("smoke", {})
        train = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/train-summary/v1",
            "work_id": receipts.WORK_ID,
            "recipe": train_lora.recipe_document(),
            "job_a": {"job_id": job_a["job_id"], "job_receipt_sha256": checked_a["job_receipt_sha256"],
                      "outcome": job_a.get("outcome")},
            "environment_sha256": receipts.sha256_file(env_path) if env_path.is_file() else None,
            "gpu": job_a.get("gpu"),
            "pins": job_a.get("pins"),
            "base": {"repo": train_lora.BASE_REPO, "revision": train_lora.BASE_REVISION,
                     "files": len(((job_a.get("base") or {}).get("files")) or {})},
            "tokenizer_recheck": job_a.get("tokenizer_recheck"),
            "image_grid": job_a.get("image_grid"),
            "smoke": smoke,
            "runs": runs,
            "selection": selection,
        }

        eval_summary = None
        receipts_by_job = [job_a]
        if job_b_dir is not None:
            checked_b = verify_returned(job_b_dir, repo_root=root, local_root=local)
            job_b = checked_b["receipt"]
            receipts_by_job.append(job_b)
            if job_b.get("job_kind") != "B" or not job_b.get("complete"):
                raise ReturnHashMismatch("正式评估须是已完成的作业 B", offending=[job_b.get("job_id")])
            chosen = job_b.get("selected_adapter") or {}
            if selection is None or chosen.get("config") != selection["selection"]["chosen"] \
                    or chosen.get("adapter_sha256") != selection["chosen_adapter_sha256"] \
                    or chosen.get("from_job") != job_a["job_id"]:
                raise ReturnHashMismatch("作业 B 用的 adapter 不是本地选优结果", offending=[chosen])
            adapter_path = Path(job_b_dir) / "predictions" / "eval-adapter.jsonl"
            adapter_rows = train_lora.read_jsonl(adapter_path)
            if _model_ids(adapter_rows) != [chosen["adapter_sha256"]]:
                raise ReturnHashMismatch("正式评估预测不是被选 adapter 产出", offending=_model_ids(adapter_rows))
            eval_summary = evaluate.summarise(
                eval_rows, adapter_rows, baseline=zero_rows, gray_boxes=gray_boxes, legacy_predictions=legacy
            )
            eval_summary["verdict"]["transfer"] = evaluate.transfer_verdict(
                {}, None, not_run_reason=SFT_003_NOT_DONE
            )
            eval_summary["failure_cases"] = failure_cases(eval_rows, adapter_rows, gray_boxes=gray_boxes)
            eval_summary.update({
                "job_a": job_a["job_id"],
                "job_b": job_b["job_id"],
                "job_b_receipt_sha256": checked_b["job_receipt_sha256"],
                "predictions_sha256": receipts.sha256_file(adapter_path),
                "baseline_predictions_sha256": zero["predictions_sha256"],
                "selected_adapter": chosen,
            })
            run = (job_a.get("runs") or {}).get(chosen["config"], {})
            train["adapter_manifest"] = {
                "base": {"repo": train_lora.BASE_REPO, "revision": train_lora.BASE_REVISION},
                "adapter_sha256": chosen["adapter_sha256"],
                "adapter_bytes": chosen.get("adapter_bytes"),
                "lora": train_lora.recipe_document()["lora"],
                "seed": train_lora.SEED,
                "dataset_manifest_sha256": (job_a.get("package") or {}).get("upload_manifest_sha256"),
                "dataset_manifest_file_sha256": _dataset_manifest_sha(local),
                "steps": run.get("steps"),
                "epochs": run.get("epochs"),
                "selected_reason": selection["selection"]["reason"],
                "job_id": job_a["job_id"],
                "env_json_sha256": job_a.get("env_sha256"),
            }
        train["accounting"] = _stage_accounting(receipts_by_job)
        if eval_summary is not None:
            eval_summary["accounting"] = train["accounting"]

        outputs = []
        if write:
            outputs.append(_write_evidence(root, ZERO_SHOT_SUMMARY, zero))
            outputs.append(_write_evidence(root, TRAIN_SUMMARY, train))
            if eval_summary is not None:
                outputs.append(_write_evidence(root, EVAL_SUMMARY, eval_summary))
        local_bytes = sum(p.stat().st_size for p in local.rglob("*") if p.is_file())
        writer.write_run_receipt(
            "return", started=started, outputs=outputs,
            extra={"stage_detail": "summarise", "job_a": job_a["job_id"],
                   "job_b": None if job_b_dir is None else Path(job_b_dir).name,
                   "local_root_bytes": local_bytes, "local_root_within_0_9_gb": local_bytes <= LOCAL_ROOT_MAX_BYTES},
        )
        return {"zero_shot": zero, "train": train, "eval": eval_summary}
    except receipts.EngSftError as exc:
        writer.write_failure_receipt("return", exc.reason, exc.offending, message=str(exc))
        raise


def _dataset_manifest_sha(local: Path) -> str | None:
    path = local / cloud_runner.UPLOAD_DIRNAME / "manifests" / "dataset-manifest.json"
    return receipts.sha256_file(path) if path.is_file() else None


# --- CLI ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-SFT-002 回传校验、选优与摘要（本地）")
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--local-root", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--job", required=True)
    select = sub.add_parser("select")
    select.add_argument("--job-a", required=True)
    summary = sub.add_parser("summarise")
    summary.add_argument("--job-a", required=True)
    summary.add_argument("--job-b", default=None)
    args = parser.parse_args(argv)
    root = Path(args.repo_root)
    local = Path(args.local_root) if args.local_root else None
    try:
        if args.command == "verify":
            result = verify_returned(Path(args.job), repo_root=root, local_root=local)
            result.pop("receipt")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "select":
            document = select_adapter(Path(args.job_a), repo_root=root, local_root=local)
            chosen = document["selection"]["chosen"]
            print(json.dumps(document["selection"], ensure_ascii=False, indent=2))
            print(
                "作业 B 命令：python -B -m tools.eng_sft.cloud_runner job-b --package <包根> --work <工作目录> "
                f"--from-job {document['job_id']} --adapter {chosen}"
            )
        elif args.command == "summarise":
            result = summarise(Path(args.job_a), Path(args.job_b) if args.job_b else None,
                               repo_root=root, local_root=local)
            verdict = (result["eval"] or result["zero_shot"])["verdict"]
            print(json.dumps(verdict, ensure_ascii=False, indent=2))
    except receipts.EngSftError as exc:
        print(f"失败（{exc.reason}）：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
