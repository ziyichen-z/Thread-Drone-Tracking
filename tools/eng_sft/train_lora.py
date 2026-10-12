#!/usr/bin/env python3
"""表 H 训练配方、冒烟、三配置、盲预测与选优（K3 代码束成员）。

云端由 `cloud_runner` 调用；本地只用其中的纯函数（配方、批计划、学习率调度、损失
掩码、选优、预检复核）。torch / transformers / peft / PIL 只在真正加载模型的函数里
延迟导入，所以本模块在没有这些库的机器上也能 import，无 GPU 单元测试直接测纯函数。

配方（D3 接受时冻结）逐项写成常量。合同没有写明、由实现期补全的训练细节（优化器、
梯度裁剪、批的切分与洗牌、冒烟学习率等）集中在 `IMPLEMENTATION_FILLS`，逐项列入 K3 报告
§5（P-K3-1…3，请接受角色转入提案「待裁定」），答复前不上云。

gold 与 prompt 只走冻结模块：训练标签 = `prompt_v2.gold_text(sample)`，prompt =
`prompt_v2.build_prompt(...)`，生成文本 = `parse.parse_prediction(...)` 解析；本模块不复制
第二份序列化或解析（AC-4 修订 1）。
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
import math
from pathlib import Path
import random
import statistics
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

from tools.eng_sft import parse, prompt_v2, receipts

# --- 表 H：base 与 LoRA -----------------------------------------------------

BASE_REPO = "Qwen/Qwen3-VL-2B-Instruct"
BASE_REVISION = "89644892e4d85e24eaac8bacfd4f463576704203"
BASE_DTYPE = "bfloat16"
ATTN_IMPLEMENTATION = "sdpa"

LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LORA_TARGET_PROJECTIONS: tuple[str, ...] = (
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
)
# 只命中 LLM 各层的七个投影；ViT 与 merger 冻结（它们的模块名本来就不同，正则再限定一层）。
LORA_TARGET_REGEX = (
    r"^model\.language_model\.layers\.\d+\."
    r"(?:self_attn\.(?:q_proj|k_proj|v_proj|o_proj)|mlp\.(?:gate_proj|up_proj|down_proj))$"
)

# --- 表 H：固定项 -----------------------------------------------------------

SEED = 20260912
EFFECTIVE_BATCH = 16
WARMUP_RATIO = 0.03
SCHEDULE = "cosine"
GRADIENT_CHECKPOINTING = True
MAX_NEW_TOKENS = 160
INFERENCE_BATCH = 1
LOSS_SCOPE = "assistant_tokens_only"
VOCAB = "unity-v2"

# 表 B / 表 H：Unity 行每张断言 `image_grid_thw == [1, 30, 40]`；SynDrone 行按表 L (4)
# 取其 manifest 的期望值（本候选 AC-12 = NOT_RUN，不会出现 SynDrone 行）。
UNITY_DATASET = "unity"
EXPECTED_GRID: dict[str, tuple[int, int, int]] = {UNITY_DATASET: prompt_v2.UNITY_IMAGE_GRID_THW}


@dataclass(frozen=True)
class CandidateConfig:
    name: str
    epochs: int
    lr: float


# 表 H：候选配置闭集与顺序唯一（≤ 3 run）。
CANDIDATES: tuple[CandidateConfig, ...] = (
    CandidateConfig("C1", 2, 1e-4),
    CandidateConfig("C2", 3, 1e-4),
    CandidateConfig("C3", 2, 5e-5),
)

# 表 H 冒烟：32 条、≤ 60 优化步、末步 loss < 0.05 且 32/32 greedy 状态正确。
SMOKE_ROWS = 32
SMOKE_MAX_STEPS = 60
SMOKE_LOSS_MAX = 0.05

# 表 H 选优：三态状态级 macro 准确率；差 ≤ 0.5 pp 并列 → epoch 少者 → lr 低者。
SELECTION_STATES: tuple[str, ...] = ("unique", "ambiguous", "none")
SELECTION_TIE_PP = Fraction(1, 2)

# 表 H token 预检：152 只是拒绝阈值，不截断、不扩预算。
GOLD_TOKEN_MAX = 152
RECOUNT_FILES: tuple[str, ...] = ("train.jsonl", "smoke.jsonl")
RECOUNT_FIELDS: tuple[str, ...] = (
    "gold_rows",
    "rows_without_gold",
    "token_max",
    "token_p50",
    "token_total",
)

# 实现期补全（合同未写明；K3 报告 §5 P-K3-1…3，接受角色答复前不上云）。
OPTIMIZER = {"name": "torch.optim.AdamW", "betas": [0.9, 0.999], "eps": 1e-8, "weight_decay": 0.0}
MAX_GRAD_NORM = 1.0
IMPLEMENTATION_FILLS: dict[str, Any] = {
    "optimizer": OPTIMIZER,
    "max_grad_norm": MAX_GRAD_NORM,
    "warmup_steps": "ceil(0.03 × 总优化步数)",
    "cosine_floor": 0.0,
    "steps_per_epoch": "ceil(多重集行数 / 16)，末批不足 16 保留",
    "shuffle": "每 epoch 用 random.Random(f'{seed}:{epoch}') 洗牌展开后的多重集",
    "micro_batch": "有效批 16 按 micro-batch 切分梯度累积（5090 初值 8×2）；只影响显存，不改步数与归一分母，"
                   "不保证与其他切分逐位相同；显存不够时同一步折半重做并逐步记录",
    "loss_normalisation": "有效批内全部 assistant token 的交叉熵之和 / 这些 token 总数",
    "assistant_tokens": "gold 文本 token + <|im_end|>（不含其后的换行）",
    "lora_dtype": "LoRA 参数 fp32（peft 自动上转），base bf16",
    "smoke_lr": "取 C1 的 1e-4；60 步 = 32 条 × 30 epoch（每 epoch 2 步）；同一 cosine/warmup 规则",
    "smoke_last_loss": "第 60 步更新前该有效批 assistant token 平均交叉熵",
    "smoke_status_correct": "冒烟 32 条盲预测解析后 status_pred == state；解析失败记错",
    "selection_macro_accuracy": "三个 gold 状态各自的 (status_pred == gold 状态) 比例的算术平均",
}


def recipe_document() -> dict[str, Any]:
    """表 H 配方 + 实现期补全，写进 adapter manifest 与 train-summary。"""
    return {
        "base": {"repo": BASE_REPO, "revision": BASE_REVISION, "dtype": BASE_DTYPE},
        "attn_implementation": ATTN_IMPLEMENTATION,
        "lora": {
            "r": LORA_R,
            "alpha": LORA_ALPHA,
            "dropout": LORA_DROPOUT,
            "target_projections": list(LORA_TARGET_PROJECTIONS),
            "target_regex": LORA_TARGET_REGEX,
            "frozen": ["vision tower", "merger", "embeddings", "lm_head"],
        },
        "fixed": {
            "seed": SEED,
            "effective_batch": EFFECTIVE_BATCH,
            "warmup_ratio": WARMUP_RATIO,
            "schedule": SCHEDULE,
            "gradient_checkpointing": GRADIENT_CHECKPOINTING,
            "max_new_tokens": MAX_NEW_TOKENS,
            "decoding": "greedy",
            "inference_batch": INFERENCE_BATCH,
            "loss_scope": LOSS_SCOPE,
            "processor_size": dict(prompt_v2.PROCESSOR_SIZE),
        },
        "candidates": [
            {"name": c.name, "epochs": c.epochs, "lr": c.lr} for c in CANDIDATES
        ],
        "smoke": {
            "rows": SMOKE_ROWS,
            "max_steps": SMOKE_MAX_STEPS,
            "loss_max": SMOKE_LOSS_MAX,
            "lr": CANDIDATES[0].lr,
        },
        "selection": {
            "metric": "three-state macro accuracy",
            "states": list(SELECTION_STATES),
            "tie_pp": float(SELECTION_TIE_PP),
            "tie_break": ["fewer epochs", "lower lr"],
        },
        "implementation_fills": IMPLEMENTATION_FILLS,
    }


# --- 失败类型（原因取合同闭集，不新造 token）---------------------------------

SmokeFailed = receipts._error("SmokeFailed", "SMOKE_FAILED")


class BudgetStop(RuntimeError):
    """预算守卫要求停止：先触及 8 GPU·h 或租金上限即停（账本 2026-09-18）。

    不是合同失败原因；由 `cloud_runner` 记成 `stop` 收据与 job-receipt 的
    `budget_guard` 字段，部分产物作废。
    """


# --- 批计划与学习率调度（纯函数）---------------------------------------------


def expand_multiset(rows: Sequence[Mapping[str, Any]]) -> list[int]:
    """表 E7：训练多重集按 `oversample_copies` 展开（文件顺序，返回行下标）。"""
    indices: list[int] = []
    for index, row in enumerate(rows):
        copies = int(row.get("oversample_copies") or 1)
        if copies < 1:
            raise ValueError(f"oversample_copies 须 ≥ 1：{row.get('sample_id')}")
        indices.extend([index] * copies)
    return indices


def epoch_order(indices: Sequence[int], seed: int, epoch: int) -> list[int]:
    """每 epoch 的洗牌顺序（与 torch 无关，可在无 GPU 机器上复现）。"""
    order = list(indices)
    random.Random(f"{seed}:{epoch}").shuffle(order)
    return order


def steps_per_epoch(count: int, batch: int = EFFECTIVE_BATCH) -> int:
    return math.ceil(count / batch) if count else 0


def plan_batches(
    indices: Sequence[int], epochs: int, *, seed: int = SEED, batch: int = EFFECTIVE_BATCH
) -> list[list[int]]:
    """全部优化步的有效批（epoch = 一次完整遍历；末批不足 16 保留）。"""
    plan: list[list[int]] = []
    for epoch in range(epochs):
        order = epoch_order(indices, seed, epoch)
        for start in range(0, len(order), batch):
            plan.append(order[start : start + batch])
    return plan


def warmup_steps(total_steps: int, ratio: float = WARMUP_RATIO) -> int:
    return math.ceil(total_steps * ratio)


def lr_factor(step: int, total_steps: int, warmup: int) -> float:
    """线性 warmup + cosine 衰减到 0（与 HF `get_cosine_schedule_with_warmup` 同式）。"""
    if step < warmup:
        return float(step) / float(max(1, warmup))
    progress = float(step - warmup) / float(max(1, total_steps - warmup))
    return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))


def next_micro_batch(size: int) -> int | None:
    """显存不够时的下一档 micro-batch（折半）；已经是 1 就没有下一档。

    只改变有效批 16 的切分方式与梯度累积次数，不改变步数、数据顺序或损失归一分母
    （AC-10 修订 2）；实际使用的值逐步记录。
    """
    return None if size <= 1 else max(1, size // 2)


def micro_batches(batch: Sequence[int], size: int) -> list[list[int]]:
    if size < 1:
        raise ValueError("micro-batch 须 ≥ 1")
    return [list(batch[start : start + size]) for start in range(0, len(batch), size)]


def smoke_epochs(rows: int = SMOKE_ROWS, max_steps: int = SMOKE_MAX_STEPS) -> int:
    """冒烟跑满 60 步所需的 epoch 数（32 条 → 每 epoch 2 步 → 30 epoch）。"""
    per_epoch = steps_per_epoch(rows)
    return max(1, max_steps // per_epoch) if per_epoch else 0


# --- 模板与损失掩码（纯函数）---------------------------------------------------

ASSISTANT_HEADER = "<|im_start|>assistant\n"
IM_END = "<|im_end|>"
IGNORE_INDEX = -100


def build_training_text(rendered_prompt: str, gold: str) -> str:
    """生成提示（`add_generation_prompt=True` 的渲染结果）+ gold + `<|im_end|>`。"""
    if not rendered_prompt.endswith(ASSISTANT_HEADER):
        raise receipts.TokenizerMismatch(
            "chat 模板渲染结果不以 assistant 头结尾，无法定位 assistant token",
            offending=[rendered_prompt[-40:]],
        )
    return rendered_prompt + gold + IM_END


def _last_subsequence(sequence: Sequence[int], pattern: Sequence[int]) -> int:
    width = len(pattern)
    for start in range(len(sequence) - width, -1, -1):
        if list(sequence[start : start + width]) == list(pattern):
            return start
    return -1


def assistant_label_mask(
    input_ids: Sequence[int], header_ids: Sequence[int], im_end_id: int
) -> list[int]:
    """只给 assistant 段（gold + `<|im_end|>`）打标签，其余全是 `IGNORE_INDEX`。

    assistant 段 = 最后一个 assistant 头之后，直到其后第一个 `<|im_end|>`（含）。
    头、用户段、图像 token 与右侧 padding 都不计损失。找不到头或 `<|im_end|>` 即拒绝
    （模板与分词器不一致，按 `TOKENIZER_MISMATCH` 处理）。
    """
    if not header_ids:
        raise receipts.TokenizerMismatch("assistant 头 token 为空", offending=[])
    start = _last_subsequence(input_ids, header_ids)
    if start < 0:
        raise receipts.TokenizerMismatch("输入中找不到 assistant 头", offending=[list(header_ids)])
    first = start + len(header_ids)
    end = -1
    for position in range(first, len(input_ids)):
        if input_ids[position] == im_end_id:
            end = position
            break
    if end < 0 or end == first:
        raise receipts.TokenizerMismatch(
            "assistant 段为空或缺 <|im_end|>", offending=[{"header_at": start}]
        )
    labels = [IGNORE_INDEX] * len(input_ids)
    for position in range(first, end + 1):
        labels[position] = int(input_ids[position])
    return labels


def labelled_count(labels: Sequence[int]) -> int:
    return sum(1 for value in labels if value != IGNORE_INDEX)


# --- 图像网格断言（表 H / AC-8）----------------------------------------------


def check_grid(
    grid: Sequence[int],
    dataset: str,
    expected_by_dataset: Mapping[str, Sequence[int]] | None = None,
    *,
    row_id: str | None = None,
) -> None:
    """按**数据集**断言 `image_grid_thw`：Unity `[1, 30, 40]`；其他数据集取其 manifest 期望值。

    期望值缺失即不满足（表 L (4)）；不符 → `IMAGE_GRID_MISMATCH`，不截断、不缩放补救。
    """
    table = dict(EXPECTED_GRID)
    if expected_by_dataset:
        table.update({key: tuple(value) for key, value in expected_by_dataset.items()})
    expected = table.get(dataset)
    if expected is None:
        raise receipts.ImageGridMismatch(
            f"数据集 {dataset!r} 没有 image_grid_thw 期望值", offending=[{"dataset": dataset}]
        )
    actual = tuple(int(value) for value in grid)
    if actual != tuple(expected):
        raise receipts.ImageGridMismatch(
            f"image_grid_thw 不符：{actual} ≠ {tuple(expected)}",
            offending=[{"dataset": dataset, "row_id": row_id, "actual": list(actual),
                        "expected": list(expected)}],
        )


# --- 云端 tokenizer 复核（表 H / AC-8）-----------------------------------------


def recount_gold_tokens(path: Path, encode: Callable[[str], int]) -> dict[str, Any]:
    """对一份 gold 文件逐条重算 token 数（与本地预检同一口径：不加特殊 token、不套模板）。"""
    counts: list[int] = []
    total_rows = 0
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            total_rows += 1
            text = prompt_v2.gold_text(json.loads(line))
            if text is not None:
                counts.append(int(encode(text)))
    return {
        "gold_rows": len(counts),
        "rows_without_gold": total_rows - len(counts),
        "token_max": max(counts) if counts else None,
        "token_p50": int(statistics.median(counts)) if counts else None,
        "token_total": sum(counts),
    }


def compare_recount(
    precheck_receipt: Mapping[str, Any], recounts: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """逐文件比对云端重算与本地预检收据；超阈值先拒（不截断），不等即停。"""
    overflow = [
        {"file": name, "max": entry["token_max"], "threshold": GOLD_TOKEN_MAX}
        for name, entry in sorted(recounts.items())
        if entry.get("token_max") is not None and entry["token_max"] > GOLD_TOKEN_MAX
    ]
    if overflow:
        raise receipts.GoldTokenOverflow(
            "gold token 超过拒绝阈值（不截断、不扩预算）", offending=overflow
        )
    local = precheck_receipt.get("gold_files", {})
    mismatches: list[dict[str, Any]] = []
    for name, entry in sorted(recounts.items()):
        expected = local.get(name)
        if expected is None:
            mismatches.append({"file": name, "problem": "NOT_IN_PRECHECK_RECEIPT"})
            continue
        for field in RECOUNT_FIELDS:
            if entry.get(field) != expected.get(field):
                mismatches.append(
                    {"file": name, "field": field, "cloud": entry.get(field), "local": expected.get(field)}
                )
    if mismatches:
        raise receipts.TokenizerMismatch("云端 tokenizer 复核与本地预检收据不等", offending=mismatches)
    return {
        "files": {name: dict(entry) for name, entry in sorted(recounts.items())},
        "matches_precheck_receipt": True,
        "token_max_threshold": GOLD_TOKEN_MAX,
    }


# --- 预测行（表 C `prediction`）--------------------------------------------------


def finish_reason_of(new_ids: Sequence[int], eos_ids: Iterable[int], max_new_tokens: int) -> str:
    eos = set(int(value) for value in eos_ids)
    if new_ids and int(new_ids[-1]) in eos:
        return "stop"
    if len(new_ids) >= max_new_tokens:
        return "length"
    return "stop"


def prediction_record(
    *,
    row_id: str,
    model_id: str,
    prompt_sha256: str,
    image_grid_thw: Sequence[int],
    raw_output: str,
    finish_reason: str,
    gen_tokens: int,
    latency_ms: float,
) -> dict[str, Any]:
    """一条预测行：解析字段一律来自冻结的 `parse.parse_prediction`。"""
    parsed = parse.parse_prediction(raw_output, finish_reason=finish_reason)
    return {
        "row_id": row_id,
        "model_id": model_id,
        "prompt_sha256": prompt_sha256,
        "image_grid_thw": [int(value) for value in image_grid_thw],
        **parsed,
        "gen_tokens": int(gen_tokens),
        "finish_reason": finish_reason,
        "latency_ms": round(float(latency_ms), 3),
    }


def blind_rows_from_samples(samples: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """冒烟用：把带标签的 sample 行变成盲行形态（prompt 只看得到这五个字段）。"""
    return [
        {
            "row_id": sample["sample_id"],
            "frame_path": sample["frame_path"],
            "surface": sample["surface"],
            "g4": False,
            "vocab": VOCAB,
        }
        for sample in samples
    ]


# --- 冒烟判定与选优（纯函数）---------------------------------------------------


def smoke_verdict(
    last_loss: float | None,
    samples: Sequence[Mapping[str, Any]],
    predictions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """表 H：末步 loss < 0.05 且 32/32 greedy 状态正确才通过。"""
    by_row = {row["row_id"]: row for row in predictions}
    wrong: list[dict[str, Any]] = []
    for sample in samples:
        prediction = by_row.get(sample["sample_id"])
        status = None if prediction is None else prediction.get("status_pred")
        if status != sample["state"]:
            wrong.append({"row_id": sample["sample_id"], "gold": sample["state"], "pred": status,
                          "parse_error": None if prediction is None else prediction.get("parse_error")})
    correct = len(samples) - len(wrong)
    loss_ok = last_loss is not None and last_loss < SMOKE_LOSS_MAX
    status_ok = len(samples) == SMOKE_ROWS and not wrong
    return {
        "passed": bool(loss_ok and status_ok),
        "last_loss": last_loss,
        "loss_max": SMOKE_LOSS_MAX,
        "status_correct": correct,
        "rows": len(samples),
        "wrong": wrong,
    }


def selection_score(
    gold_rows: Sequence[Mapping[str, Any]], predictions: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """选层子集上的三态状态级 macro 准确率（分数用有理数，比较不受浮点误差影响）。

    选层 gold 行是 sample 形态（`sample_id` / `state`），盲行 `row_id = sample_id`；
    预测文件与 gold 行必须一一对应，否则整次 `PREDICTIONS_INCOMPLETE`。
    """
    expected = [row["sample_id"] for row in gold_rows]
    actual = [row["row_id"] for row in predictions]
    duplicates = sorted({row for row in actual if actual.count(row) > 1})
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if duplicates or missing or extra:
        raise receipts.PredictionsIncomplete(
            "选层预测与选层子集不一一对应",
            offending=[{"duplicates": duplicates[:10], "missing": missing[:10], "extra": extra[:10]}],
        )
    by_row = {row["row_id"]: row for row in predictions}
    per_state: dict[str, dict[str, Any]] = {}
    fractions: list[Fraction] = []
    for state in SELECTION_STATES:
        rows = [row for row in gold_rows if row["state"] == state]
        correct = sum(1 for row in rows if by_row[row["sample_id"]].get("status_pred") == state)
        accuracy = Fraction(correct, len(rows)) if rows else None
        per_state[state] = {
            "rows": len(rows),
            "correct": correct,
            "accuracy": None if accuracy is None else float(accuracy),
        }
        if accuracy is not None:
            fractions.append(accuracy)
    macro = sum(fractions, Fraction(0)) / len(fractions) if fractions else Fraction(0)
    return {
        "per_state": per_state,
        "macro_accuracy": float(macro),
        "macro_accuracy_exact": f"{macro.numerator}/{macro.denominator}",
        "rows": len(gold_rows),
    }


def _exact(score: Mapping[str, Any]) -> Fraction:
    numerator, denominator = score["macro_accuracy_exact"].split("/")
    return Fraction(int(numerator), int(denominator))


def select_best(scores: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """表 H 选优：最高分；与最高分差 ≤ 0.5 pp 的都算并列 → epoch 少者 → lr 低者。"""
    configs = {config.name: config for config in CANDIDATES}
    unknown = sorted(set(scores) - set(configs))
    if unknown:
        raise ValueError(f"候选不在闭集内：{unknown}")
    if not scores:
        raise ValueError("没有可选的候选（全部 run 失败或未运行）")
    exact = {name: _exact(score) for name, score in scores.items()}
    best = max(exact.values())
    tied = [config for config in CANDIDATES
            if config.name in exact and (best - exact[config.name]) * 100 <= SELECTION_TIE_PP]
    order = {config.name: position for position, config in enumerate(CANDIDATES)}
    chosen = sorted(tied, key=lambda c: (c.epochs, c.lr, order[c.name]))[0]
    if len(tied) == 1:
        reason = "highest three-state macro accuracy"
    else:
        reason = (
            f"tie within {float(SELECTION_TIE_PP)} pp among {[c.name for c in tied]}: "
            "fewer epochs, then lower lr"
        )
    return {
        "chosen": chosen.name,
        "chosen_config": {"epochs": chosen.epochs, "lr": chosen.lr},
        "tied": [config.name for config in tied],
        "best_macro_accuracy": float(best),
        "scores": {name: float(value) for name, value in sorted(exact.items())},
        "reason": reason,
    }


# --- JSONL 写出（部分文件作废不续跑）----------------------------------------------


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl_atomic(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    """逐行写到 `.partial`，全部成功才改名；中途任何异常都删掉部分文件（表 H「中断/失败」）。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    count = 0
    try:
        with open(partial, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")
                handle.flush()
                count += 1
        partial.replace(path)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    return count


# --- 以下需要 torch / transformers / peft（延迟导入）-------------------------------


@dataclass
class LoadedModel:
    model: Any
    processor: Any
    device: str
    header_ids: list[int]
    im_end_id: int
    eos_ids: list[int]
    model_id: str


def load_image(path: Path):
    from PIL import Image  # noqa: PLC0415

    with Image.open(path) as image:
        image.load()
        return image.convert("RGB")


def load_model(
    source: str | Path,
    *,
    revision: str | None = None,
    device: str = "cuda",
    adapter_dir: Path | None = None,
    trainable: bool = False,
    local_files_only: bool = True,
) -> LoadedModel:
    """加载 base（bf16）与处理器；`trainable` 时挂新 LoRA，`adapter_dir` 时加载已训 adapter。"""
    import torch  # noqa: PLC0415
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration  # noqa: PLC0415

    kwargs: dict[str, Any] = {"local_files_only": local_files_only}
    if revision:
        kwargs["revision"] = revision
    processor = AutoProcessor.from_pretrained(str(source), **kwargs)
    processor.tokenizer.padding_side = "right"
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        str(source), dtype=torch.bfloat16, attn_implementation=ATTN_IMPLEMENTATION, **kwargs
    )
    model.to(device)
    model_id = f"{BASE_REPO}@{revision or BASE_REVISION}"
    if trainable:
        from peft import LoraConfig, get_peft_model  # noqa: PLC0415

        torch.manual_seed(SEED)
        model.enable_input_require_grads()
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        config = LoraConfig(
            r=LORA_R,
            lora_alpha=LORA_ALPHA,
            lora_dropout=LORA_DROPOUT,
            target_modules=LORA_TARGET_REGEX,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, config)
    elif adapter_dir is not None:
        from peft import PeftModel  # noqa: PLC0415

        model = PeftModel.from_pretrained(model, str(adapter_dir), is_trainable=False)
        model_id = receipts.sha256_file(Path(adapter_dir) / "adapter_model.safetensors")
    tokenizer = processor.tokenizer
    header_ids = list(tokenizer.encode(ASSISTANT_HEADER, add_special_tokens=False))
    im_end_id = int(tokenizer.convert_tokens_to_ids(IM_END))
    eos = model.generation_config.eos_token_id
    eos_ids = [int(value) for value in (eos if isinstance(eos, (list, tuple)) else [eos]) if value is not None]
    if im_end_id not in eos_ids:
        eos_ids.append(im_end_id)
    return LoadedModel(model, processor, device, header_ids, im_end_id, eos_ids, model_id)


def lora_module_count(loaded: LoadedModel) -> dict[str, Any]:
    """挂载后核对：只有 LLM 层的七个投影带 LoRA，数量 = 层数 × 7。"""
    names = [name for name, _ in loaded.model.named_modules() if name.endswith(".lora_A")]
    text_config = getattr(loaded.model.config, "text_config", loaded.model.config)
    layers = int(getattr(text_config, "num_hidden_layers", 0))
    trainable = sum(p.numel() for p in loaded.model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in loaded.model.parameters())
    visual = [name for name in names if ".visual." in name]
    return {
        "lora_modules": len(names),
        "expected": layers * len(LORA_TARGET_PROJECTIONS),
        "visual_lora_modules": len(visual),
        "trainable_params": int(trainable),
        "total_params": int(total),
    }


def _encode_batch(loaded: LoadedModel, texts: list[str], images: list[Any]):
    return loaded.processor(
        text=texts,
        images=images,
        images_kwargs={"size": dict(prompt_v2.PROCESSOR_SIZE)},
        padding=True,
        return_tensors="pt",
    )


def predict_rows(
    loaded: LoadedModel,
    rows: Sequence[Mapping[str, Any]],
    package_root: Path,
    out_path: Path,
    *,
    dataset: str = UNITY_DATASET,
    should_stop: Callable[[], bool] | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    """盲行逐条 greedy 预测（batch 1、max_new_tokens 160），写表 C `prediction` 行。"""
    import torch  # noqa: PLC0415

    model = loaded.model
    model.eval()
    if hasattr(model, "gradient_checkpointing_disable"):
        try:
            model.gradient_checkpointing_disable()
        except ValueError:
            pass
    tokenizer = loaded.processor.tokenizer
    started = time.monotonic()
    latencies: list[float] = []

    def generate() -> Iterable[dict[str, Any]]:
        for position, row in enumerate(rows):
            if should_stop is not None and should_stop():
                raise BudgetStop(f"预算守卫：第 {position} 行前停止")
            begin = time.monotonic()
            prompt = prompt_v2.build_prompt(row["frame_path"], row["surface"], bool(row["g4"]), row["vocab"])
            image = load_image(Path(package_root) / row["frame_path"])
            text = loaded.processor.apply_chat_template(
                prompt["messages"], tokenize=False, add_generation_prompt=True
            )
            inputs = _encode_batch(loaded, [text], [image])
            grid = [int(value) for value in inputs["image_grid_thw"][0].tolist()]
            check_grid(grid, dataset, row_id=row["row_id"])
            inputs = inputs.to(loaded.device)
            with torch.inference_mode():
                output = model.generate(
                    **inputs,
                    max_new_tokens=MAX_NEW_TOKENS,
                    do_sample=False,
                    temperature=None,
                    top_p=None,
                    top_k=None,
                )
            new_ids = output[0, inputs["input_ids"].shape[1] :].tolist()
            raw = tokenizer.decode(new_ids, skip_special_tokens=True)
            latency = (time.monotonic() - begin) * 1000.0
            latencies.append(latency)
            if progress is not None:
                progress(position + 1, len(rows))
            yield prediction_record(
                row_id=row["row_id"],
                model_id=loaded.model_id,
                prompt_sha256=prompt["prompt_sha256"],
                image_grid_thw=grid,
                raw_output=raw,
                finish_reason=finish_reason_of(new_ids, loaded.eos_ids, MAX_NEW_TOKENS),
                gen_tokens=len(new_ids),
                latency_ms=latency,
            )

    written = write_jsonl_atomic(out_path, generate())
    return {
        "rows": written,
        "elapsed_s": round(time.monotonic() - started, 3),
        "latency_ms_p50": round(statistics.median(latencies), 3) if latencies else None,
        "latency_ms_max": round(max(latencies), 3) if latencies else None,
        "prediction_sha256": receipts.sha256_file(out_path),
    }


def _training_batch(
    loaded: LoadedModel, samples: Sequence[Mapping[str, Any]], package_root: Path
) -> tuple[Any, Any, int]:
    """一个 micro-batch：渲染模板、拼 gold、编码、只给 assistant 段打标签。"""
    import torch  # noqa: PLC0415

    texts: list[str] = []
    images: list[Any] = []
    gold_token_counts: list[int] = []
    tokenizer = loaded.processor.tokenizer
    for sample in samples:
        prompt = prompt_v2.build_prompt(sample["frame_path"], sample["surface"], False, VOCAB)
        rendered = loaded.processor.apply_chat_template(
            prompt["messages"], tokenize=False, add_generation_prompt=True
        )
        gold = prompt_v2.gold_text(sample)
        if gold is None:
            raise receipts.FrozenSetMismatch(
                f"训练行没有 gold：{sample.get('sample_id')}", offending=[sample.get("sample_id")]
            )
        texts.append(build_training_text(rendered, gold))
        images.append(load_image(Path(package_root) / sample["frame_path"]))
        gold_token_counts.append(len(tokenizer.encode(gold, add_special_tokens=False)))
    encoded = _encode_batch(loaded, texts, images)
    for index, grid in enumerate(encoded["image_grid_thw"].tolist()):
        check_grid(grid, UNITY_DATASET, row_id=samples[index].get("sample_id"))
    label_rows: list[list[int]] = []
    for index, ids in enumerate(encoded["input_ids"].tolist()):
        labels = assistant_label_mask(ids, loaded.header_ids, loaded.im_end_id)
        # assistant 段 = gold token + `<|im_end|>`；与独立计数不等说明模板内切分变了。
        if labelled_count(labels) != gold_token_counts[index] + 1:
            raise receipts.TokenizerMismatch(
                "模板内 gold token 数与独立计数不等",
                offending=[{"sample_id": samples[index].get("sample_id"),
                            "labelled": labelled_count(labels),
                            "gold_plus_im_end": gold_token_counts[index] + 1}],
            )
        label_rows.append(labels)
    labels_tensor = torch.tensor(label_rows, dtype=torch.long)
    return encoded, labels_tensor, int((labels_tensor != IGNORE_INDEX).sum().item())


def _assistant_loss_sum(model: Any, encoded: Any, labels: Any, device: str):
    """只在 assistant 位置上算交叉熵之和（fp32），避免整段 logits 上转。"""
    import torch  # noqa: PLC0415
    import torch.nn.functional as functional  # noqa: PLC0415

    inputs = {key: value.to(device) for key, value in encoded.items()}
    labels = labels.to(device)
    output = model(**inputs, use_cache=False)
    logits = output.logits[:, :-1, :]
    targets = labels[:, 1:]
    mask = targets != IGNORE_INDEX
    selected = logits[mask].float()
    return functional.cross_entropy(selected, targets[mask], reduction="sum")


def train_candidate(
    loaded: LoadedModel,
    samples: Sequence[Mapping[str, Any]],
    package_root: Path,
    *,
    lr: float,
    epochs: int,
    out_dir: Path,
    micro_batch: int,
    expand: bool = True,
    max_steps: int | None = None,
    should_stop: Callable[[], bool] | None = None,
    log: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """表 H：一次 LoRA run（冒烟与 C1…C3 共用）。返回末步 loss、步数与 adapter 身份。"""
    import torch  # noqa: PLC0415

    torch.manual_seed(SEED)
    indices = expand_multiset(samples) if expand else list(range(len(samples)))
    plan = plan_batches(indices, epochs)
    if max_steps is not None:
        plan = plan[:max_steps]
    total = len(plan)
    warmup = warmup_steps(total)
    model = loaded.model
    model.train()
    parameters = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(
        parameters, lr=lr, betas=tuple(OPTIMIZER["betas"]), eps=OPTIMIZER["eps"],
        weight_decay=OPTIMIZER["weight_decay"],
    )
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer, lambda step: lr_factor(step, total, warmup)
    )
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "train-log.jsonl"
    started = time.monotonic()
    last_loss: float | None = None
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    current_micro = micro_batch
    micro_changes: list[dict[str, Any]] = []

    def accumulate(batch: Sequence[int], size: int) -> tuple[float, int]:
        """一个有效批的前向/反向（按 size 切 micro-batch 累积梯度），返回 (CE 总和, assistant token 数)。"""
        prepared = [_training_batch(loaded, [samples[i] for i in part], package_root)
                    for part in micro_batches(batch, size)]
        tokens = sum(count for _, _, count in prepared)
        total = 0.0
        for encoded, labels, _count in prepared:
            loss_sum = _assistant_loss_sum(model, encoded, labels, loaded.device)
            (loss_sum / tokens).backward()
            total += float(loss_sum.detach().item())
        return total, tokens

    with open(log_path, "w", encoding="utf-8") as log_handle:
        for step, batch in enumerate(plan):
            if should_stop is not None and should_stop():
                raise BudgetStop(f"预算守卫：第 {step} 步前停止")
            current_lr = scheduler.get_last_lr()[0]
            while True:
                try:
                    loss_total, label_tokens = accumulate(batch, current_micro)
                    break
                except torch.cuda.OutOfMemoryError:
                    # 这一步的半截梯度作废，折半 micro-batch 重做同一步；有效批与数据不变。
                    optimizer.zero_grad(set_to_none=True)
                    torch.cuda.empty_cache()
                    smaller = next_micro_batch(current_micro)
                    if smaller is None:
                        raise
                    micro_changes.append({"step": step + 1, "from": current_micro, "to": smaller})
                    current_micro = smaller
            grad_norm = torch.nn.utils.clip_grad_norm_(parameters, MAX_GRAD_NORM)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)
            last_loss = loss_total / label_tokens
            entry = {
                "step": step + 1,
                "epoch": step // max(1, steps_per_epoch(len(indices))),
                "loss": last_loss,
                "lr": current_lr,
                "grad_norm": float(grad_norm),
                "label_tokens": label_tokens,
                "rows": len(batch),
                "micro_batch": current_micro,
                "elapsed_s": round(time.monotonic() - started, 3),
            }
            log_handle.write(json.dumps(entry, sort_keys=True) + "\n")
            log_handle.flush()
            if log is not None:
                log(entry)
    adapter_dir = out_dir / "adapter"
    model.save_pretrained(str(adapter_dir))
    weights = adapter_dir / "adapter_model.safetensors"
    peak = int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else None
    return {
        "steps": total,
        "warmup_steps": warmup,
        "epochs": epochs,
        "lr": lr,
        "multiset_rows": len(indices),
        "micro_batch_initial": micro_batch,
        "micro_batch_final": current_micro,
        "micro_batch_changes": micro_changes,
        "last_loss": last_loss,
        "elapsed_s": round(time.monotonic() - started, 3),
        "peak_gpu_memory_bytes": peak,
        "adapter_sha256": receipts.sha256_file(weights),
        "adapter_bytes": weights.stat().st_size,
        "train_log_sha256": receipts.sha256_file(log_path),
    }
