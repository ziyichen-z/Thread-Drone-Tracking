#!/usr/bin/env python3
"""表 B/F/G/L 的具名回归（AC-3 修订 1、AC-4、AC-12）。

评分与判定在夹具数据上跑生产函数；预测行由 `parse.parse_prediction` 产出，不手写
`status_pred`，所以解析口径与评分口径始终是同一条链。
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.fixtures.eng_sft import synth  # noqa: E402
from tools.eng_sft import build_sft_data as build  # noqa: E402
from tools.eng_sft import evaluate, parse, prompt_v2, receipts  # noqa: E402


def prediction(row_id: str, text: str, finish_reason: str | None = None) -> dict:
    parsed = parse.parse_prediction(text, finish_reason=finish_reason)
    parsed["row_id"] = row_id
    return parsed


def gold_prediction(row: dict) -> dict:
    """完全命中的预测：直接把 gold 序列化回读（同一 `gold_text` 函数）。"""
    text = prompt_v2.gold_text(row)
    return prediction(row["row_id"], text if text else '{"status": "none"}')


class MatchingTests(unittest.TestCase):
    def test_max_cardinality_one_to_one_matching(self) -> None:
        gold = [[0.1, 0.1, 0.2, 0.2], [0.5, 0.5, 0.2, 0.2], [0.8, 0.1, 0.1, 0.1]]
        exact = [[100, 100, 300, 300], [500, 500, 700, 700], [800, 100, 900, 200]]
        self.assertEqual(evaluate.max_cardinality_matching(gold, exact), 3)
        # 一对一：两个预测框都压在同一个 gold 上，只能匹配 1 个。
        overlapping = [[100, 100, 300, 300], [105, 105, 305, 305]]
        self.assertEqual(evaluate.max_cardinality_matching(gold[:1], overlapping), 1)
        self.assertEqual(evaluate.max_cardinality_matching(gold, overlapping), 1)
        # IoU < 0.5 的边不算：整体平移到几乎不相交。
        shifted = [[400, 400, 600, 600]]
        self.assertEqual(evaluate.max_cardinality_matching(gold[:1], shifted), 0)
        # 空集两侧都为 0。
        self.assertEqual(evaluate.max_cardinality_matching([], exact), 0)
        self.assertEqual(evaluate.max_cardinality_matching(gold, []), 0)
        # 最大基数：3 个 gold、2 个可匹配预测 → 2。
        self.assertEqual(evaluate.max_cardinality_matching(gold, exact[:2]), 2)

    def test_gray_diagnostic_uses_bound_s3_definite_boxes(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="eng-sft-eval-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        world = synth.build_world(root)
        synth.run_build(world)
        local = synth.local_root(root)
        with open(local / "data" / build.EVAL_JSONL, encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle]
        gray = [row for row in rows if row["group"] == "G3p"]
        self.assertTrue(gray)
        for row in gray:
            self.assertIsNone(row["gold_state"])  # 灰区不编造三态 gold
            self.assertEqual(row["gold_boxes_norm_xywh"], [])
            self.assertTrue(row["definite_ids"])

        boxes = build.load_definite_boxes(rows, repo_root=root, local_root=local)
        self.assertEqual(set(boxes), {row["row_id"] for row in gray})
        for row in gray:
            self.assertEqual(len(boxes[row["row_id"]]), len(row["definite_ids"]))

        # 命中判据用的是 M 的原框，不是旧探针 v1 的单目标框。
        target = gray[0]
        member_box = boxes[target["row_id"]][0]
        predictions = [
            prediction(row["row_id"], json.dumps({"status": "none"})) for row in rows
        ]
        hit = json.dumps({"status": "unique", "bbox_2d": prompt_v2.bbox_2d_1000(member_box)})
        predictions = [
            prediction(row["row_id"], hit) if row["row_id"] == target["row_id"] else pred
            for row, pred in zip(rows, predictions)
        ]
        scores = evaluate.score_rows(rows, predictions, gray_boxes=boxes)
        by_id = {score.row_id: score for score in scores}
        self.assertTrue(by_id[target["row_id"]].gray_hit)
        metrics = evaluate.group_metrics(scores, "G3p")
        self.assertEqual(metrics["unique_rows"], 1)
        self.assertEqual(metrics["any_member_hit_rate"], 1.0)

        # C1-3：**评分入口**自己接通取框——`main` 不再需要调用方手工传 gray_boxes。
        predictions_path = root / "predictions.jsonl"
        with open(predictions_path, "w", encoding="utf-8") as handle:
            for row, pred in zip(rows, predictions):
                handle.write(json.dumps({**pred, "row_id": row["row_id"]}, ensure_ascii=False) + "\n")
        out_path = root / "eval-summary.json"
        code = evaluate.main([
            "--repo-root", str(root), "--local-root", str(local),
            "--manifest", str(local / "data" / build.EVAL_JSONL),
            "--predictions", str(predictions_path), "--out", str(out_path),
        ])
        self.assertEqual(code, 0)
        summary = json.loads(out_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["metrics"]["G3p"]["unique_rows"], 1)
        self.assertEqual(summary["metrics"]["G3p"]["any_member_hit_rate"], 1.0)
        self.assertTrue(summary["v1_diagnostic_rows"])  # 表 F 的 v1 附表已接通
        receipts_dir = local / receipts.RECEIPTS_DIRNAME
        self.assertTrue(list(receipts_dir.glob("run-return-*.json")))
        # C1-5：`--out` 落在禁写根 → 入口拒绝并写失败收据，不先写再检查。
        code = evaluate.main([
            "--repo-root", str(root), "--local-root", str(local),
            "--manifest", str(local / "data" / build.EVAL_JSONL),
            "--predictions", str(predictions_path),
            "--out", str(root / "runtime/dist-data/attempt-2/summary.json"),
        ])
        self.assertEqual(code, 1)
        self.assertFalse((root / "runtime/dist-data/attempt-2/summary.json").exists())
        failures = sorted(receipts_dir.glob("failure-return-*.json"))
        self.assertTrue(failures)
        self.assertEqual(
            json.loads(failures[-1].read_text(encoding="utf-8"))["reason"], "OUTPUT_PATH_FORBIDDEN"
        )

        # 缺源/缺框 → `INPUT_HASH_CHANGED`，拒绝该次评分（不剔除行）。
        broken = [dict(row) for row in rows]
        for row in broken:
            if row["group"] == "G3p":
                row["definite_ids"] = ["does-not-exist"]
        with self.assertRaises(receipts.EngSftError) as raised:
            build.load_definite_boxes(broken, repo_root=root, local_root=local)
        self.assertEqual(raised.exception.reason, "INPUT_HASH_CHANGED")
        # C1-3：源字节变了（或没在 build 输入清单里登记）同样拒绝取框，不静默改用当前字节。
        catalog = root / build.FIELD_CATALOG_JSON
        catalog.write_text(catalog.read_text(encoding="utf-8") + " ", encoding="utf-8")
        with self.assertRaises(receipts.EngSftError) as raised:
            build.load_definite_boxes(rows, repo_root=root, local_root=local)
        self.assertEqual(raised.exception.reason, "INPUT_HASH_CHANGED")
        self.assertIn("输入清单", str(raised.exception))
        with self.assertRaises(receipts.EngSftError) as raised:
            evaluate.score_rows(rows, predictions, gray_boxes={})
        self.assertEqual(raised.exception.reason, "INPUT_HASH_CHANGED")
        # 源字节变了之后，评分入口整次失败并写 `INPUT_HASH_CHANGED` 失败收据。
        code = evaluate.main([
            "--repo-root", str(root), "--local-root", str(local),
            "--manifest", str(local / "data" / build.EVAL_JSONL),
            "--predictions", str(predictions_path), "--out", str(root / "eval-summary-2.json"),
        ])
        self.assertEqual(code, 1)
        self.assertFalse((root / "eval-summary-2.json").exists())
        failures = sorted((local / receipts.RECEIPTS_DIRNAME).glob("failure-return-*.json"))
        self.assertEqual(
            json.loads(failures[-1].read_text(encoding="utf-8"))["reason"], "INPUT_HASH_CHANGED"
        )


class CompletenessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = [
            {"row_id": "G1-a", "group": "G1", "gate_row": True, "stratum": "M",
             "gold_state": "unique", "gold_boxes_norm_xywh": [[0.1, 0.1, 0.2, 0.2]], "noun": {"class": "car"}},
            {"row_id": "G1-b", "group": "G1", "gate_row": True, "stratum": "M",
             "gold_state": "unique", "gold_boxes_norm_xywh": [[0.5, 0.5, 0.2, 0.2]], "noun": {"class": "car"}},
        ]

    def test_missing_or_duplicate_rows_invalidate_run(self) -> None:
        complete = [gold_prediction(row) for row in self.rows]
        evaluate.check_completeness(self.rows, complete)  # 一一对应时不抛
        for broken in (
            complete[:1],  # 缺行
            complete + [complete[0]],  # 重复 row_id
            complete + [prediction("G1-zzz", '{"status": "none"}')],  # 多余行
        ):
            with self.assertRaises(receipts.EngSftError) as raised:
                evaluate.score_rows(self.rows, broken)
            self.assertEqual(raised.exception.reason, "PREDICTIONS_INCOMPLETE")


class V1DiagnosticTests(unittest.TestCase):
    def test_v1_outputs_map_to_three_states_and_pair_with_current_run(self) -> None:
        """C2-3（R1@K4 §4 第 2 条）：评分入口读 `data/legacy/predictions.jsonl`，按真实 v1 字段映射三态再配对。"""
        root = Path(tempfile.mkdtemp(prefix="eng-sft-v1-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        world = synth.build_world(root)
        synth.run_build(world)
        local = synth.local_root(root)
        legacy_file = local / "data" / "legacy" / "predictions.jsonl"
        with open(legacy_file, encoding="utf-8") as handle:
            legacy = [json.loads(line) for line in handle]
        expected = {row["row_id"]: synth.v1_expected_status(index) for index, row in enumerate(legacy)}
        by_v1 = {row["row_id"]: row for row in legacy}
        self.assertEqual(set(expected.values()), {None, "ambiguous", "unique", "none"})

        with open(local / "data" / build.EVAL_JSONL, encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle]
        predictions_path = root / "predictions.jsonl"
        with open(predictions_path, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(prediction(row["row_id"], '{"status": "none"}'), ensure_ascii=False) + "\n")
        out_path = root / "eval-summary.json"
        code = evaluate.main([
            "--repo-root", str(root), "--local-root", str(local),
            "--manifest", str(local / "data" / build.EVAL_JSONL),
            "--predictions", str(predictions_path), "--out", str(out_path),
        ])
        self.assertEqual(code, 0)
        table = json.loads(out_path.read_text(encoding="utf-8"))["v1_diagnostic_rows"]
        entries = sum(len(row.get("legacy_probe") or []) for row in rows)
        self.assertEqual(len(table), entries)  # 每条 legacy 行一行，重复键两条各自成行
        seen = set()
        for item in table:
            v1_id = item["row_id_v1"]
            seen.add(v1_id)
            self.assertTrue(item["v1_prediction_present"], v1_id)
            self.assertEqual(item["status_v1"], expected[v1_id], v1_id)
            self.assertEqual(item["invalid_v1"], expected[v1_id] is None)
            self.assertEqual(item["success_v1"], by_v1[v1_id]["success"])
            self.assertEqual(item["iou_v1"], by_v1[v1_id]["iou"])
            self.assertEqual(item["status_pred"], "none")
            # 本次全答 none：只有 v1 也是 none 的行一致；v1 无效的行按「不一致」计，不是 None。
            self.assertEqual(item["status_agrees_with_v1"], expected[v1_id] == "none", v1_id)
        self.assertIn("v1-dup0", seen)
        self.assertEqual(
            {expected[v1_id] for v1_id in seen}, {None, "ambiguous", "unique", "none"}
        )


class VerdictTests(unittest.TestCase):
    """表 F 分母纪律 + 表 G 四层状态（在固定夹具预测上逐条核对）。"""

    def _rows(self):
        def row(row_id, group, state, boxes, cls="car"):
            return {
                "row_id": row_id,
                "group": group,
                "gate_row": group in evaluate.SUCCESS_GROUPS + evaluate.SET_GROUPS + evaluate.NONE_GROUPS,
                "stratum": "M",
                "seen_target": True,
                "noun": {"class": cls},
                "gold_state": state,
                "gold_boxes_norm_xywh": boxes,
            }

        box_a = [0.1, 0.1, 0.2, 0.2]
        box_b = [0.5, 0.5, 0.2, 0.2]
        rows = [row(f"G1-{i}", "G1", "unique", [box_a]) for i in range(8)]
        rows += [row(f"G2-{i}", "G2", "unique", [box_b]) for i in range(2)]
        rows += [row(f"G3-{i}", "G3", "ambiguous", [box_a, box_b]) for i in range(4)]
        rows += [row(f"G5-{i}", "G5", "none", []) for i in range(5)]
        return rows

    def test_layer_statuses_on_fixture_predictions(self) -> None:
        rows = self._rows()
        # 全对：功能门三条全过。
        good = [gold_prediction(row) for row in rows]
        summary = evaluate.summarise(rows, good, baseline=good)
        self.assertEqual(summary["verdict"]["functional_gate"]["status"], "GATE_MET")
        self.assertEqual(summary["metrics"]["G1"]["success_rate"], 1.0)
        self.assertEqual(summary["metrics"]["G3"]["strict_success_rate"], 1.0)
        self.assertEqual(summary["metrics"]["G5"]["none_rate"], 1.0)
        # 配对差为 0 → 非劣成立。
        self.assertEqual(summary["verdict"]["vocabulary_non_inferiority"]["status"], "NON_INFERIOR")
        self.assertEqual(summary["paired_difference_g1g2"]["point_estimate_pp"], 0.0)
        self.assertEqual(summary["paired_difference_g1g2"]["rows"], 10)

        # 解析失败不剔除分母：一行无效 → G1 Success 下降、无效率上升。
        broken = list(good)
        broken[0] = prediction(rows[0]["row_id"], "garbage")
        summary = evaluate.summarise(rows, broken)
        self.assertEqual(summary["metrics"]["G1"]["rows"], 8)
        self.assertAlmostEqual(summary["metrics"]["G1"]["success_rate"], 7 / 8)
        self.assertAlmostEqual(summary["metrics"]["G1"]["invalid_rate"], 1 / 8)

        # 误报歧义/误报 none 超阈值 → GATE_NOT_MET（b）。
        noisy = list(good)
        for index in range(2):
            noisy[index] = prediction(
                rows[index]["row_id"],
                '{"status": "ambiguous", "candidates": [{"bbox_2d": [100,100,300,300]}, {"bbox_2d": [500,500,700,700]}]}',
            )
        summary = evaluate.summarise(rows, noisy)
        gate = summary["verdict"]["functional_gate"]
        self.assertEqual(gate["status"], "GATE_NOT_MET")
        self.assertFalse(gate["checks"]["b_false_ambiguous"]["pass"])

        # G3 全部答 unique → 报告率 0，(a) 不过。
        silent = list(good)
        for index, row in enumerate(rows):
            if row["group"] == "G3":
                silent[index] = prediction(row["row_id"], '{"status": "unique", "bbox_2d": [100,100,300,300]}')
        summary = evaluate.summarise(rows, silent)
        self.assertEqual(summary["metrics"]["G3"]["report_rate"], 0.0)
        self.assertEqual(summary["verdict"]["functional_gate"]["status"], "GATE_NOT_MET")

        # G5 全部答 unique → none 率 0，(c) 不过。
        loud = list(good)
        for index, row in enumerate(rows):
            if row["group"] == "G5":
                loud[index] = prediction(row["row_id"], '{"status": "unique", "bbox_2d": [100,100,300,300]}')
        summary = evaluate.summarise(rows, loud)
        self.assertEqual(summary["metrics"]["G5"]["none_rate"], 0.0)
        self.assertFalse(summary["verdict"]["functional_gate"]["checks"]["c_g5_none_rate"]["pass"])

        # 非劣：微调比基线差 2 行（20 pp）→ INFERIOR。
        worse = list(good)
        for index in range(2):
            worse[index] = prediction(rows[index]["row_id"], '{"status": "none"}')
        summary = evaluate.summarise(rows, worse, baseline=good)
        self.assertEqual(summary["verdict"]["vocabulary_non_inferiority"]["status"], "INFERIOR")
        self.assertAlmostEqual(summary["paired_difference_g1g2"]["point_estimate_pp"], -20.0)
        self.assertEqual(len(summary["paired_difference_g1g2"]["ci_pp"]), 2)

    def test_set_group_paired_difference_uses_strict_success(self) -> None:
        """C2-2（R1@K4 §4 第 1 条）：G3/G3t 的逐组配对差按严格成功算，不再恒为 0 pp。"""
        rows = self._rows()
        good = [gold_prediction(row) for row in rows]
        g3 = [index for index, row in enumerate(rows) if row["group"] == "G3"]
        self.assertEqual(len(g3), 4)
        # 4 行 G3 里有 2 行答成 unique：严格成功、报告率与 macro F1 都比基线低。
        worse = list(good)
        for index in g3[:2]:
            worse[index] = prediction(rows[index]["row_id"], '{"status": "unique", "bbox_2d": [100,100,300,300]}')
        summary = evaluate.summarise(rows, worse, baseline=good)
        entry = summary["paired_difference_by_group"]["G3"]
        self.assertEqual(entry["outcome"], "strict_success")
        self.assertEqual(entry["rows"], 4)
        self.assertAlmostEqual(entry["point_estimate_pp"], -50.0)
        self.assertNotEqual(entry["ci_pp"], [0.0, 0.0])
        self.assertAlmostEqual(entry["report_rate_diff"]["point_estimate_pp"], -50.0)
        self.assertLess(entry["macro_f1_diff"]["point_estimate_pp"], 0.0)
        # 非集合组仍按 Success 配对，且本例里 G1/G2 不受影响。
        self.assertEqual(summary["paired_difference_by_group"]["G1"]["outcome"], "success")
        self.assertEqual(summary["paired_difference_by_group"]["G1"]["point_estimate_pp"], 0.0)
        self.assertNotIn("report_rate_diff", summary["paired_difference_by_group"]["G1"])
        # 反方向（微调比基线好）得到对称的正值。
        summary = evaluate.summarise(rows, good, baseline=worse)
        self.assertAlmostEqual(
            summary["paired_difference_by_group"]["G3"]["point_estimate_pp"], 50.0
        )


class PromptTests(unittest.TestCase):
    def test_prompt_builder_cannot_see_gold_and_vocab_is_frozen(self) -> None:
        import inspect

        signature = inspect.signature(prompt_v2.build_prompt)
        self.assertEqual(
            list(signature.parameters), ["image_path", "surface", "g4", "vocab_name"]
        )
        built = prompt_v2.build_prompt("frames/x.jpg", "the red car")
        text = built["text"]
        self.assertIn("Instruction: the red car", text)
        self.assertIn(prompt_v2.VOCAB_SEGMENTS["unity-v2"], text)
        self.assertNotIn("bbox_2d\": [", text.replace(prompt_v2.REPLY_SEGMENT, ""))
        # 结构上不可见 gold：模板里没有任何 gold 通路，且 prompt 文本不含 gold 序列化。
        gold = prompt_v2.gold_text({"state": "unique", "target_boxes_norm_xywh": [[0.1, 0.1, 0.2, 0.2]]})
        self.assertNotIn(gold, text)
        # 词表段冻结：模板骨架与词表段各自导出 SHA，G4 行追加关系释义。
        self.assertEqual(prompt_v2.template_sha256(), prompt_v2._sha256_text(prompt_v2.PROMPT_TEMPLATE))
        self.assertNotIn(prompt_v2.G4_SEGMENT, text)
        self.assertIn(prompt_v2.G4_SEGMENT, prompt_v2.build_prompt("f.jpg", "x", True)["text"])
        with self.assertRaises(KeyError):
            prompt_v2.build_prompt("f.jpg", "x", False, "no-such-vocab")
        # §8 表 6a：非 G4 固定文本 1,226 字符（含 `{surface}` 占位符 9 字符）。
        self.assertEqual(prompt_v2.fixed_prompt_chars() + len("{surface}"), 1226)
        # gold 序列化三种骨架逐字。
        self.assertEqual(prompt_v2.gold_text({"state": "none"}), '{"status": "none"}')
        self.assertEqual(
            prompt_v2.gold_text({"state": "unique", "target_boxes_norm_xywh": [[0.1, 0.2, 0.05, 0.04]]}),
            '{"status": "unique", "bbox_2d": [100, 200, 150, 240]}',
        )
        self.assertEqual(
            prompt_v2.gold_text(
                {"state": "ambiguous", "target_boxes_norm_xywh": [[0.5, 0.2, 0.05, 0.04], [0.1, 0.2, 0.05, 0.04]]}
            ),
            '{"status": "ambiguous", "candidates": [{"bbox_2d": [100, 200, 150, 240]}, '
            '{"bbox_2d": [500, 200, 550, 240]}]}',
        )
        # 退化框逐轴修正：零宽/零高各补 1，1000 处反向减 1。
        self.assertEqual(prompt_v2.bbox_2d_1000([0.5, 0.5, 0.0, 0.0]), [500, 500, 501, 501])
        self.assertEqual(prompt_v2.bbox_2d_1000([1.0, 1.0, 0.0, 0.0]), [999, 999, 1000, 1000])


class TransferTests(unittest.TestCase):
    def test_transfer_verdict_is_mechanical_with_na_rule(self) -> None:
        unity = {"m1": 12.0, "m6": -1.0}
        # 前置不成立 → NOT_RUN 终态。
        self.assertEqual(
            evaluate.transfer_verdict(unity, None)["status"], "NOT_RUN(SFT_003_NOT_DONE)"
        )
        self.assertTrue(
            evaluate.transfer_verdict(unity, {"m1": 20.0}, not_run_reason="INCOMPATIBLE_EVAL_SCHEMA:3")[
                "status"
            ].startswith("NOT_RUN(")
        )
        # 观察到迁移：d_U(m1) ≥ 10、d_S(m1) ≥ 10、d_S(m6) ≥ −5。
        observed = evaluate.transfer_verdict(unity, {"m1": 11.0, "m6": -2.0})
        self.assertEqual(observed["status"], "TRANSFER_OBSERVED")
        # 小分母：|d_U(m)| < 5.0 pp → NA(UNITY_DELTA_SMALL)，不算比值。
        self.assertEqual(observed["ratios"]["m6"], "NA(UNITY_DELTA_SMALL)")
        self.assertAlmostEqual(observed["ratios"]["m1"]["ratio"], 11.0 / 12.0)
        # d_U < 0 时比值只披露。
        disclosed = evaluate.transfer_verdict({"m1": -12.0}, {"m1": -6.0})
        self.assertTrue(disclosed["ratios"]["m1"]["disclosure_only"])
        self.assertEqual(disclosed["status"], "NOT_OBSERVED")
        # 阈值任一不成立 → NOT_OBSERVED。
        self.assertEqual(
            evaluate.transfer_verdict(unity, {"m1": 9.9, "m6": 0.0})["status"], "NOT_OBSERVED"
        )
        self.assertEqual(
            evaluate.transfer_verdict(unity, {"m1": 11.0, "m6": -6.0})["status"], "NOT_OBSERVED"
        )
        # 表 L (1)(2) schema 校验：缺字段 / 组越界 / 盲行带 gold 都能报出来。
        rows = [
            {
                "row_id": "r1",
                "frame_path": "frames/a.jpg",
                "group": "G1",
                "gate_row": True,
                "surface": "the car",
                "gold_state": "unique",
                "gold_boxes_norm_xywh": [[0.1, 0.1, 0.2, 0.2]],
                "stratum": "M",
            }
        ]
        blind = [{"row_id": "r1", "frame_path": "frames/a.jpg", "surface": "the car", "g4": False, "vocab": "syndrone"}]
        self.assertEqual(evaluate.validate_transfer_rows(rows, blind), [])
        self.assertTrue(evaluate.validate_transfer_rows([{**rows[0], "group": "G9"}], blind))
        self.assertTrue(evaluate.validate_transfer_rows(rows, [{**blind[0], "gold_state": "unique"}]))
        self.assertTrue(evaluate.validate_transfer_rows([{k: v for k, v in rows[0].items() if k != "stratum"}], blind))


if __name__ == "__main__":
    unittest.main()
