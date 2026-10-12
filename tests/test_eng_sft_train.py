#!/usr/bin/env python3
"""P1-ENG-SFT-002 K3 训练侧的无 GPU 具名回归（AC-8 / AC-10）。

只测 `train_lora` 的纯函数：配方冻结、批计划与学习率调度、模板渲染与 assistant-only
损失掩码、冒烟判定、选优与并列、云端 tokenizer 复核、按数据集的网格断言、预测行。
不 import torch / transformers / peft，系统 python3 即可运行。
"""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_sft import parse, prompt_v2, receipts, train_lora  # noqa: E402

# Qwen3-VL 分词器里的真实 id：<|im_start|>=151644、"assistant"=77091、"\n"=198、<|im_end|>=151645。
IM_START, ASSISTANT, NEWLINE, IM_END, PAD = 151644, 77091, 198, 151645, 151643
HEADER = [IM_START, ASSISTANT, NEWLINE]


def _sample(sample_id: str, state: str, boxes=None, copies: int = 1) -> dict:
    return {
        "sample_id": sample_id,
        "frame_path": f"frames/{sample_id}.jpg",
        "surface": "the taxi",
        "state": state,
        "target_boxes_norm_xywh": boxes or [],
        "oversample_copies": copies,
    }


class ConfigTests(unittest.TestCase):
    def test_only_three_candidates_in_order(self) -> None:
        self.assertEqual(
            [(c.name, c.epochs, c.lr) for c in train_lora.CANDIDATES],
            [("C1", 2, 1e-4), ("C2", 3, 1e-4), ("C3", 2, 5e-5)],
        )
        recipe = train_lora.recipe_document()
        self.assertEqual(recipe["base"]["repo"], "Qwen/Qwen3-VL-2B-Instruct")
        self.assertEqual(recipe["base"]["revision"], "89644892e4d85e24eaac8bacfd4f463576704203")
        self.assertEqual(recipe["base"]["dtype"], "bfloat16")
        self.assertEqual((recipe["lora"]["r"], recipe["lora"]["alpha"], recipe["lora"]["dropout"]), (16, 32, 0.05))
        self.assertEqual(
            recipe["lora"]["target_projections"],
            ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        )
        fixed = recipe["fixed"]
        self.assertEqual(fixed["seed"], 20260912)
        self.assertEqual(fixed["effective_batch"], 16)
        self.assertEqual(fixed["warmup_ratio"], 0.03)
        self.assertEqual(fixed["schedule"], "cosine")
        self.assertTrue(fixed["gradient_checkpointing"])
        self.assertEqual(fixed["max_new_tokens"], 160)
        self.assertEqual(fixed["decoding"], "greedy")
        self.assertEqual(fixed["inference_batch"], 1)
        self.assertEqual(fixed["loss_scope"], "assistant_tokens_only")
        self.assertEqual(fixed["processor_size"], {"shortest_edge": 65536, "longest_edge": 16777216})
        self.assertEqual(recipe["smoke"], {"rows": 32, "max_steps": 60, "loss_max": 0.05, "lr": 1e-4})

    def test_lora_targets_only_language_model_projections(self) -> None:
        pattern = re.compile(train_lora.LORA_TARGET_REGEX)
        hits = [
            "model.language_model.layers.0.self_attn.q_proj",
            "model.language_model.layers.27.self_attn.o_proj",
            "model.language_model.layers.3.mlp.down_proj",
        ]
        misses = [
            "model.visual.blocks.0.attn.qkv",
            "model.visual.blocks.0.mlp.linear_fc1",
            "model.visual.merger.linear_fc2",
            "model.visual.deepstack_merger_list.0.linear_fc1",
            "lm_head",
            "model.language_model.embed_tokens",
            "model.language_model.layers.0.self_attn.q_norm",
        ]
        for name in hits:
            self.assertIsNotNone(pattern.fullmatch(name), name)
        for name in misses:
            self.assertIsNone(pattern.fullmatch(name), name)


class ScheduleTests(unittest.TestCase):
    def test_multiset_expansion_batches_and_schedule_are_deterministic(self) -> None:
        rows = [_sample("a", "unique", copies=1), _sample("b", "ambiguous", copies=2), _sample("c", "none")]
        self.assertEqual(train_lora.expand_multiset(rows), [0, 1, 1, 2])
        indices = list(range(5318))
        plan = train_lora.plan_batches(indices, 2)
        self.assertEqual(len(plan), 2 * 333)  # 5,318 / 16 → 333 步（末批 6 条保留）
        self.assertEqual(len(plan[332]), 5318 - 332 * 16)
        self.assertEqual(sorted(i for batch in plan[:333] for i in batch), indices)  # 每 epoch 完整遍历
        self.assertEqual(plan, train_lora.plan_batches(indices, 2))  # 同种子同顺序
        self.assertNotEqual(plan[0], plan[333])  # 不同 epoch 重新洗牌
        self.assertEqual(train_lora.warmup_steps(666), 20)
        self.assertEqual(train_lora.lr_factor(0, 666, 20), 0.0)
        self.assertAlmostEqual(train_lora.lr_factor(20, 666, 20), 1.0)
        self.assertAlmostEqual(train_lora.lr_factor(666, 666, 20), 0.0)
        self.assertLess(train_lora.lr_factor(400, 666, 20), train_lora.lr_factor(100, 666, 20))
        self.assertEqual(train_lora.micro_batches(list(range(16)), 8), [list(range(8)), list(range(8, 16))])
        # 显存不够时折半重做同一步：8 → 4 → 2 → 1 → 无下一档（有效批仍是 16）。
        self.assertEqual([train_lora.next_micro_batch(n) for n in (8, 4, 2, 1)], [4, 2, 1, None])
        self.assertEqual(sum(len(part) for part in train_lora.micro_batches(list(range(16)), 4)), 16)

    def test_smoke_runs_exactly_sixty_steps_on_thirty_two_rows(self) -> None:
        self.assertEqual(train_lora.smoke_epochs(32, 60), 30)
        plan = train_lora.plan_batches(list(range(32)), train_lora.smoke_epochs())[: train_lora.SMOKE_MAX_STEPS]
        self.assertEqual(len(plan), 60)
        self.assertTrue(all(len(batch) == 16 for batch in plan))


class TemplateTests(unittest.TestCase):
    def test_assistant_only_loss_mask(self) -> None:
        user = [IM_START, 872, NEWLINE, 151652, 151655, 151655, 151653, 1234, 5678, IM_END, NEWLINE]
        gold = [4913, 2829, 788, 330, 6697, 9207]
        ids = user + HEADER + gold + [IM_END] + [PAD, PAD]
        labels = train_lora.assistant_label_mask(ids, HEADER, IM_END)
        first = len(user) + len(HEADER)
        self.assertEqual(labels[:first], [train_lora.IGNORE_INDEX] * first)
        self.assertEqual(labels[first : first + len(gold) + 1], gold + [IM_END])
        self.assertEqual(labels[first + len(gold) + 1 :], [train_lora.IGNORE_INDEX] * 2)
        self.assertEqual(train_lora.labelled_count(labels), len(gold) + 1)
        # 头找不到 / assistant 段为空都拒绝（模板与分词器不一致）。
        with self.assertRaises(receipts.EngSftError) as raised:
            train_lora.assistant_label_mask(user + gold, HEADER, IM_END)
        self.assertEqual(raised.exception.reason, "TOKENIZER_MISMATCH")
        with self.assertRaises(receipts.EngSftError):
            train_lora.assistant_label_mask(user + HEADER + [IM_END], HEADER, IM_END)

    def test_training_text_appends_frozen_gold_after_generation_prompt(self) -> None:
        sample = {"state": "unique", "target_boxes_norm_xywh": [[0.1, 0.2, 0.3, 0.4]]}
        gold = prompt_v2.gold_text(sample)
        rendered = "<|im_start|>user\n<|vision_start|><|image_pad|><|vision_end|>text<|im_end|>\n<|im_start|>assistant\n"
        text = train_lora.build_training_text(rendered, gold)
        self.assertEqual(text, rendered + '{"status": "unique", "bbox_2d": [100, 200, 400, 600]}<|im_end|>')
        with self.assertRaises(receipts.EngSftError):
            train_lora.build_training_text(rendered + "x", gold)
        # 冒烟盲行只暴露 prompt 的五个字段，没有 gold。
        blind = train_lora.blind_rows_from_samples([_sample("s-1", "none")])[0]
        self.assertEqual(set(blind), {"row_id", "frame_path", "surface", "g4", "vocab"})
        self.assertEqual(blind["vocab"], "unity-v2")


class GridTests(unittest.TestCase):
    def test_grid_assertion_is_per_dataset(self) -> None:
        train_lora.check_grid([1, 30, 40], "unity")
        with self.assertRaises(receipts.EngSftError) as raised:
            train_lora.check_grid([1, 34, 46], "unity", row_id="r-1")
        self.assertEqual(raised.exception.reason, "IMAGE_GRID_MISMATCH")
        # 另一个数据集按它自己 manifest 的期望值断言，不套 Unity 的 [1, 30, 40]。
        expected = {"syndrone": [1, 34, 60]}
        train_lora.check_grid([1, 34, 60], "syndrone", expected)
        with self.assertRaises(receipts.EngSftError):
            train_lora.check_grid([1, 30, 40], "syndrone", expected)
        # 期望值缺失即不满足（表 L (4)）。
        with self.assertRaises(receipts.EngSftError) as missing:
            train_lora.check_grid([1, 34, 60], "syndrone")
        self.assertEqual(missing.exception.reason, "IMAGE_GRID_MISMATCH")


class PrecheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="eng-sft-train-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def _write(self, name: str, rows: list[dict]) -> Path:
        path = self.root / name
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return path

    def _receipt(self, recounts: dict) -> dict:
        return {"gold_files": {name: dict(entry, sha256="x", bytes=1) for name, entry in recounts.items()}}

    def test_overflow_fails_closed_without_truncation(self) -> None:
        boxes = [[0.1 * i, 0.1, 0.05, 0.05] for i in range(1, 5)]
        rows = [_sample("s-1", "ambiguous", boxes), _sample("s-2", "none")]
        path = self._write("train.jsonl", rows)
        before = path.read_bytes()
        counts = train_lora.recount_gold_tokens(path, lambda text: len(text))  # 按字符计：4 候选 > 152
        self.assertGreater(counts["token_max"], train_lora.GOLD_TOKEN_MAX)
        with self.assertRaises(receipts.EngSftError) as raised:
            train_lora.compare_recount(self._receipt({"train.jsonl": counts}), {"train.jsonl": counts})
        self.assertEqual(raised.exception.reason, "GOLD_TOKEN_OVERFLOW")
        self.assertEqual(path.read_bytes(), before)  # 不截断、不改写

    def test_cloud_recount_mismatch_stops(self) -> None:
        rows = [_sample("s-1", "unique", [[0.1, 0.2, 0.3, 0.4]]), _sample("s-2", "none"),
                {"sample_id": "g", "gold_state": None, "gold_boxes_norm_xywh": []}]
        path = self._write("smoke.jsonl", rows)
        encode = lambda text: max(1, len(text) // 4)  # noqa: E731
        counts = train_lora.recount_gold_tokens(path, encode)
        self.assertEqual((counts["gold_rows"], counts["rows_without_gold"]), (2, 1))
        receipt = self._receipt({"smoke.jsonl": counts})
        result = train_lora.compare_recount(receipt, {"smoke.jsonl": counts})
        self.assertTrue(result["matches_precheck_receipt"])
        drifted = dict(counts, token_total=counts["token_total"] + 1)
        with self.assertRaises(receipts.EngSftError) as raised:
            train_lora.compare_recount(receipt, {"smoke.jsonl": drifted})
        self.assertEqual(raised.exception.reason, "TOKENIZER_MISMATCH")
        with self.assertRaises(receipts.EngSftError):  # 收据里根本没有这份文件
            train_lora.compare_recount(receipt, {"train.jsonl": counts})


class SmokeTests(unittest.TestCase):
    def _predictions(self, samples, statuses):
        rows = []
        for sample, status in zip(samples, statuses):
            raw = {"none": '{"status": "none"}',
                   "unique": '{"status": "unique", "bbox_2d": [1, 2, 3, 4]}',
                   "ambiguous": '{"status": "ambiguous", "candidates": [{"bbox_2d": [1, 2, 3, 4]}, {"bbox_2d": [5, 6, 7, 8]}]}',
                   "bad": "not json"}[status]
            rows.append(train_lora.prediction_record(
                row_id=sample["sample_id"], model_id="m", prompt_sha256="p", image_grid_thw=[1, 30, 40],
                raw_output=raw, finish_reason="stop", gen_tokens=10, latency_ms=1.0))
        return rows

    def test_smoke_needs_low_last_loss_and_all_states_correct(self) -> None:
        states = ["unique"] * 16 + ["ambiguous"] * 8 + ["none"] * 8
        samples = [_sample(f"s-{i}", state) for i, state in enumerate(states)]
        good = self._predictions(samples, states)
        self.assertTrue(train_lora.smoke_verdict(0.01, samples, good)["passed"])
        self.assertFalse(train_lora.smoke_verdict(0.05, samples, good)["passed"])  # 严格小于 0.05
        self.assertFalse(train_lora.smoke_verdict(None, samples, good)["passed"])
        bad = self._predictions(samples, states[:-1] + ["bad"])
        verdict = train_lora.smoke_verdict(0.01, samples, bad)
        self.assertFalse(verdict["passed"])
        self.assertEqual(verdict["status_correct"], 31)
        self.assertEqual(verdict["wrong"][0]["parse_error"], "JSON_ERROR")

    def test_prediction_record_uses_frozen_parser_and_truncation(self) -> None:
        record = train_lora.prediction_record(
            row_id="r", model_id="m", prompt_sha256="p", image_grid_thw=(1, 30, 40),
            raw_output='{"status": "unique", "bbox_2d": [1, 2, 3, 4]}', finish_reason="length",
            gen_tokens=160, latency_ms=12.3456)
        self.assertEqual(record["parse_error"], parse.TRUNCATED)
        self.assertIsNone(record["status_pred"])
        self.assertEqual(record["image_grid_thw"], [1, 30, 40])
        self.assertEqual(train_lora.finish_reason_of([1, 2, IM_END], [IM_END, PAD], 160), "stop")
        self.assertEqual(train_lora.finish_reason_of([1] * 160, [IM_END], 160), "length")


class SelectionTests(unittest.TestCase):
    def _scores(self, macro: dict[str, Fraction]) -> dict:
        return {name: {"macro_accuracy_exact": f"{value.numerator}/{value.denominator}",
                       "macro_accuracy": float(value)} for name, value in macro.items()}

    def test_tie_break_prefers_fewer_epochs_then_lower_lr(self) -> None:
        # 明确最高者直接当选。
        result = train_lora.select_best(self._scores({"C1": Fraction(80, 100), "C2": Fraction(85, 100),
                                                       "C3": Fraction(70, 100)}))
        self.assertEqual(result["chosen"], "C2")
        self.assertEqual(result["tied"], ["C2"])
        # C2 最高但 C1 只差 0.5 pp（含等号）→ 并列 → epoch 少的 C1。
        result = train_lora.select_best(self._scores({"C1": Fraction(845, 1000), "C2": Fraction(850, 1000),
                                                       "C3": Fraction(700, 1000)}))
        self.assertEqual(result["chosen"], "C1")
        self.assertEqual(result["tied"], ["C1", "C2"])
        # 差 0.51 pp 不并列。
        result = train_lora.select_best(self._scores({"C1": Fraction(8449, 10000), "C2": Fraction(8500, 10000)}))
        self.assertEqual(result["chosen"], "C2")
        # C1 与 C3 同 epoch 并列 → lr 低的 C3。
        result = train_lora.select_best(self._scores({"C1": Fraction(90, 100), "C2": Fraction(80, 100),
                                                       "C3": Fraction(898, 1000)}))
        self.assertEqual(result["chosen"], "C3")
        with self.assertRaises(ValueError):
            train_lora.select_best(self._scores({"C4": Fraction(1)}))

    def test_selection_score_is_macro_over_three_gold_states(self) -> None:
        gold = ([{"sample_id": f"u{i}", "state": "unique"} for i in range(4)]
                + [{"sample_id": f"a{i}", "state": "ambiguous"} for i in range(2)]
                + [{"sample_id": "n0", "state": "none"}])
        predictions = ([{"row_id": f"u{i}", "status_pred": "unique"} for i in range(3)]
                       + [{"row_id": "u3", "status_pred": None}]
                       + [{"row_id": "a0", "status_pred": "ambiguous"}, {"row_id": "a1", "status_pred": "unique"}]
                       + [{"row_id": "n0", "status_pred": "none"}])
        score = train_lora.selection_score(gold, predictions)
        self.assertEqual(score["per_state"]["unique"]["correct"], 3)
        self.assertEqual(score["macro_accuracy_exact"], str((Fraction(3, 4) + Fraction(1, 2) + 1) / 3))
        with self.assertRaises(receipts.EngSftError) as raised:
            train_lora.selection_score(gold, predictions[:-1])
        self.assertEqual(raised.exception.reason, "PREDICTIONS_INCOMPLETE")


class ModuleBoundaryTests(unittest.TestCase):
    def test_train_module_imports_without_gpu_stack(self) -> None:
        source = (PROJECT_ROOT / "tools/eng_sft/train_lora.py").read_text(encoding="utf-8")
        top_level = [line for line in source.splitlines() if line.startswith(("import ", "from "))]
        for line in top_level:
            for heavy in ("torch", "transformers", "peft", "PIL", "controller", "tools.dist_data"):
                self.assertNotIn(heavy, line, line)


if __name__ == "__main__":
    unittest.main()
