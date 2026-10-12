#!/usr/bin/env python3
"""表 J 标签语义抽查的具名回归（AC-14）。"""

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
from tools.eng_sft import label_audit, receipts  # noqa: E402


class AuditCase(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="eng-sft-audit-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.world = synth.build_world(self.root)
        self.local = synth.local_root(self.root)
        synth.run_build(self.world)

    def plan(self):
        return label_audit.run_plan(repo_root=self.root, local_root=self.local)


class SamplerTests(AuditCase):
    def test_layer_quotas_and_uniqueness_are_deterministic(self) -> None:
        plan = self.plan()
        again = label_audit.sample_panels(label_audit.load_candidates(self.local))
        self.assertEqual(
            [(p["panel_index"], p["key"]) for p in plan["panels"]],
            [(p["panel_index"], p["key"]) for p in again["panels"]],
        )
        panels = plan["panels"]
        user = [p for p in panels if p["share"] == "user"]
        prescreen = [p for p in panels if p["share"] == "prescreen"]
        # 配额：用户 ≤ 24、预筛 ≤ 36，逐层不超表 J 的配额。
        self.assertLessEqual(len(user), label_audit.USER_CAP)
        self.assertLessEqual(len(prescreen), label_audit.PRESCREEN_CAP)
        for layer, user_quota, prescreen_quota in label_audit.LAYER_QUOTAS:
            self.assertLessEqual(len([p for p in user if p["layer"] == layer]), user_quota)
            self.assertLessEqual(len([p for p in prescreen if p["layer"] == layer]), prescreen_quota)
        # 用户份额先取（panel_index 连续在前），层顺序按 J1→J7。
        self.assertEqual([p["panel_index"] for p in panels], list(range(1, len(panels) + 1)))
        user_layers = [p["layer"] for p in user]
        self.assertEqual(user_layers, sorted(user_layers))
        # 唯一性：同一帧全局 ≤ 1 行；同一 object_id 每层 ≤ 1 行。
        frames = [p["frame_id"] for p in panels]
        self.assertEqual(len(frames), len(set(frames)))
        per_layer: dict[str, list[str]] = {}
        for panel in panels:
            keys = panel["object_ids"] or [panel["surface"]]
            per_layer.setdefault(panel["layer"], []).extend(keys)
        for layer, keys in per_layer.items():
            self.assertEqual(len(keys), len(set(keys)), layer)
        # 层归属闭集（表 J）：J3 只收 class ambiguous；目标车 unique 一律落 J5；
        # color noun 的 ambiguous 不在表 J 任何一层，抽样域不收。
        self.assertEqual(label_audit._layer_of({"state": "ambiguous", "noun_type": "class"}, "train"), "J3")
        self.assertIsNone(label_audit._layer_of({"state": "ambiguous", "noun_type": "color"}, "train"))
        self.assertEqual(label_audit._layer_of({"state": "unique", "noun_type": "color"}, "train"), "J2")
        self.assertEqual(label_audit._layer_of({"state": "unique", "noun_type": "class"}, "train"), "J1")
        self.assertEqual(
            label_audit._layer_of(
                {"state": "unique", "noun_type": "color", "has_dynamic_target": True}, "eval"
            ),
            "J5",
        )
        self.assertEqual(label_audit._layer_of({"group": "G4", "state": "unique"}, "eval"), "J6")
        # C2-4：用**真实 `eval_record` 产出的行**验归层——评估行按表 C 不写 `noun_type`，
        # 直接读它会把 G2 归进 J1、G3/G3t 整个丢出抽样域。
        with open(self.local / build.DATA_DIRNAME / build.EVAL_JSONL, encoding="utf-8") as handle:
            eval_rows = [json.loads(line) for line in handle]
        self.assertTrue(eval_rows)
        self.assertFalse(any("noun_type" in row for row in eval_rows))
        expected_layer = {
            "G1": "J1", "G2": "J2", "G3": "J3", "G3t": "J3",
            "G1t": "J5", "G2t": "J5", "G5": "J4", "G4": "J6",
        }
        seen_groups = set()
        for row in eval_rows:
            group = row["group"]
            if group not in expected_layer:
                continue  # G3p / LEGACY_ONLY 不抽
            seen_groups.add(group)
            self.assertEqual(label_audit._layer_of(row, "eval"), expected_layer[group], row["row_id"])
        self.assertIn("G2", seen_groups)
        self.assertIn("G3", seen_groups)
        # 抽样域也必须真的收得到这些评估行。
        domain_sources = {
            (c.layer, c.source) for c in label_audit.load_candidates(self.local) if c.source == "eval"
        }
        self.assertIn(("J2", "eval"), domain_sources)
        self.assertIn(("J3", "eval"), domain_sources)
        self.assertEqual(label_audit.WEAK_CLASS_ORDER, ("car", "pickup truck", "truck", "suv"))
        for panel in panels:
            if panel["layer"] == "J3":
                self.assertEqual(panel["noun_type"], "class")
        # J7（AC-14 修订 2）：显示的 object_id / 框 / S5 颜色词指向**同一个**叠框对象，
        # 与触发排除的 counterexample 分列；同对象每层 ≤ 1 按叠框对象计。
        j7 = [p for p in panels if p["layer"] == "J7"]
        for panel in j7:
            self.assertEqual(len(panel["object_ids"]), 1)
            boxed = panel["object_ids"][0]
            self.assertTrue(panel["boxes_norm_xywh"], boxed)
            self.assertIsNotNone(panel["extra"]["s5_color"])
            self.assertIn("counterexample_object_ids", panel["extra"])
            self.assertNotIn("counterexample_object_ids", panel["object_ids"])
            self.assertTrue(panel["surface"].endswith(panel["class_word"]))
            self.assertIn(panel["extra"]["s5_color"], panel["surface"])
        self.assertEqual(len({p["object_ids"][0] for p in j7}), len(j7))
        # J4 用户份额覆盖不同类别；J3 优先含目标车；G3p / LEGACY_ONLY 不抽。
        j4 = [p["class_word"] for p in user if p["layer"] == "J4"]
        self.assertEqual(len(j4), len(set(j4)))
        self.assertFalse([p for p in panels if p["group"] in ("G3p", "LEGACY_ONLY")])
        # 不足额留空披露、不回填：实取写进文档的分层表。
        document = (self.root / label_audit.AUDIT_PATH).read_text(encoding="utf-8")
        self.assertIn("## 2. 层定义、分母与实取", document)
        for layer, _user_quota, _prescreen in label_audit.LAYER_QUOTAS:
            self.assertIn(f"| {layer} |", document)
        self.assertIn(build.SEED, document)


class ReceiptTests(AuditCase):
    def _precheck_and_commit(self) -> None:
        synth.copy_frozen_scripts(self.root)
        directory, encode = synth.stub_tokenizer(self.root)
        original = build._load_tokenizer
        build._load_tokenizer = lambda path: (encode, {"library": "stub", "version": "0"})
        try:
            build.run_precheck(repo_root=self.root, local_root=self.local, tokenizer_path=directory)
        finally:
            build._load_tokenizer = original
        synth.git_commit_all(self.root)

    def test_open_finding_blocks_freeze(self) -> None:
        plan = self.plan()
        wrong = plan["panels"][0]["panel_index"]
        synth.write_unity_verdicts(self.root, plan, wrong_panels=[wrong])
        self._precheck_and_commit()

        state = label_audit.audit_gate_state(repo_root=self.root, local_root=self.local)
        self.assertEqual(state["reason"], "AUDIT_FINDING_OPEN")
        self.assertIn(wrong, state["offending"])
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "AUDIT_FINDING_OPEN")
        # `stats` 写开放收据，并把统计块写进抽查文件。
        label_audit.run_stats(repo_root=self.root, local_root=self.local)
        receipt = self.local / receipts.RECEIPTS_DIRNAME / label_audit.FINDING_RECEIPT_NAME
        self.assertTrue(receipt.is_file())
        document = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertIn(wrong, document["panels"])
        self.assertIn("错误类型计数", (self.root / label_audit.AUDIT_PATH).read_text(encoding="utf-8"))

        # 未判定齐全（state=PENDING）→ AUDIT_INCOMPLETE，同样拒绝冻结。
        synth.write_unity_verdicts(self.root, plan, state="PENDING")
        self.assertEqual(
            label_audit.audit_gate_state(repo_root=self.root, local_root=self.local)["reason"],
            "AUDIT_INCOMPLETE",
        )
        # 复判后无「错」→ 放行（「不确定」不阻止冻结）。
        synth.write_unity_verdicts(self.root, plan)
        state = label_audit.audit_gate_state(repo_root=self.root, local_root=self.local)
        self.assertIsNone(state["reason"])
        build.run_freeze(repo_root=self.root, local_root=self.local)

    def test_closure_record_releases_only_ruled_panels(self) -> None:
        """AC-14 修订 3：具名裁定 → 闭合记录 → `freeze` 只放行记录里的那几张。"""
        plan = self.plan()
        user = [p for p in plan["panels"] if p["share"] == "user"]
        excluded = next(p["panel_index"] for p in user if p["layer"] == "J7")
        in_gold = next(p["panel_index"] for p in user if p["layer"] in ("J1", "J2", "J3"))
        synth.write_unity_verdicts(self.root, plan, wrong_panels=[excluded])
        self._precheck_and_commit()
        # 先跑 stats 产出原 `AUDIT_FINDING_OPEN` 收据——闭合记录要绑定它，不能跳过历史。
        label_audit.run_stats(repo_root=self.root, local_root=self.local)
        anchor = "AC-14 修订 3"
        proposal = self.root / label_audit.PROPOSAL_PATH
        proposal.parent.mkdir(parents=True, exist_ok=True)
        proposal.write_text(f"# 夹具提案\n\n| {anchor} | 表 J (ii) 上游标签缺陷 |\n", encoding="utf-8")
        synth.git_commit_all(self.root, "ruling")

        # 1. 裁定锚点必须真的出现在提案里。
        with self.assertRaises(receipts.EngSftError) as raised:
            label_audit.run_close(
                disposition="ii", ruling_anchor="不存在的裁定", repo_root=self.root, local_root=self.local
            )
        self.assertEqual(raised.exception.reason, "AUDIT_INCOMPLETE")
        # 2. 处置必须在表 J 闭集内。
        with self.assertRaises(receipts.EngSftError):
            label_audit.run_close(
                disposition="iv", ruling_anchor=anchor, repo_root=self.root, local_root=self.local
            )
        # 3. 正常闭合：绑定裁定出处、原收据 SHA、判定摘要与面板身份。
        document = label_audit.run_close(
            disposition="ii", ruling_anchor=anchor, repo_root=self.root, local_root=self.local
        )
        self.assertEqual([e["panel_index"] for e in document["panels"]], [excluded])
        entry = document["panels"][0]
        self.assertEqual(entry["layer"], "J7")
        self.assertEqual(len(entry["boxed_object_ids"]), 1)
        self.assertIsNotNone(entry["s5_color_word"])
        self.assertIn("counterexample_object_ids", entry)
        self.assertEqual(entry["user_error_types"], ["类别错"])
        for counts in entry["exclusion_evidence"].values():
            self.assertEqual(counts["surface_rows"], 0)  # 该 noun 确已排除
        self.assertEqual(document["ruling"]["anchor"], anchor)
        self.assertEqual(len(document["ruling"]["commit"]), 40)
        finding = self.local / receipts.RECEIPTS_DIRNAME / label_audit.FINDING_RECEIPT_NAME
        self.assertTrue(finding.is_file())  # 原收据保留，不删
        self.assertEqual(document["finding_receipt_sha256"], receipts.sha256_file(finding))
        state = label_audit.audit_gate_state(repo_root=self.root, local_root=self.local)
        self.assertIsNone(state["reason"])
        self.assertEqual(state["summary"]["closure"]["panels"], [excluded])
        build.run_freeze(repo_root=self.root, local_root=self.local)

        # 3b. C1-6：消费端复核闭合绑定——删掉原开放收据后，保留 closure 也不再放行。
        finding_backup = finding.read_bytes()
        finding.unlink()
        state = label_audit.audit_gate_state(repo_root=self.root, local_root=self.local)
        self.assertEqual(state["reason"], "AUDIT_FINDING_OPEN")
        self.assertIn("ORIGINAL_RECEIPT_MISSING", json.dumps(state["offending"], ensure_ascii=False))
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "AUDIT_FINDING_OPEN")
        finding.write_bytes(finding_backup)
        # 3c. 同编号换了面板（身份对不上）同样失效。
        plan_path = label_audit.plan_json_path(self.local)
        plan_document = json.loads(plan_path.read_text(encoding="utf-8"))
        for panel in plan_document["panels"]:
            if panel["panel_index"] == excluded:
                panel["frame_id"] = panel["frame_id"] + ".swapped"
        plan_path.write_text(json.dumps(plan_document, ensure_ascii=False), encoding="utf-8")
        state = label_audit.audit_gate_state(repo_root=self.root, local_root=self.local)
        self.assertEqual(state["reason"], "AUDIT_FINDING_OPEN")
        self.assertIn("frame_id", json.dumps(state["offending"], ensure_ascii=False))
        label_audit.run_plan(repo_root=self.root, local_root=self.local)  # 重抽复原计划
        plan_document = json.loads(plan_path.read_text(encoding="utf-8"))
        closure = json.loads(label_audit.closure_receipt_path(self.local).read_text(encoding="utf-8"))
        current = {p["panel_index"]: p for p in plan_document["panels"]}
        self.assertEqual(
            current[excluded]["frame_id"], closure["panels"][0]["frame_id"]
        )
        # 4. 判定表再变（另一张也判错）→ 摘要不符，闭合失效，freeze 重新被挡。
        synth.write_unity_verdicts(self.root, plan, wrong_panels=[excluded, in_gold])
        state = label_audit.audit_gate_state(repo_root=self.root, local_root=self.local)
        self.assertEqual(state["reason"], "AUDIT_FINDING_OPEN")
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "AUDIT_FINDING_OPEN")
        # 5. (ii) 要求该 noun 确已排除：仍在 gold 文件里的行不允许就地闭合。
        with self.assertRaises(receipts.EngSftError) as raised:
            label_audit.run_close(
                disposition="ii", ruling_anchor=anchor, repo_root=self.root, local_root=self.local
            )
        self.assertEqual(raised.exception.reason, "AUDIT_INCOMPLETE")
        self.assertIn("排除前提不成立", str(raised.exception))
        # 6. 删掉原收据也绕不过去：close 拒绝在无 AUDIT_FINDING_OPEN 历史时闭合。
        synth.write_unity_verdicts(self.root, plan, wrong_panels=[excluded])
        finding.unlink()
        with self.assertRaises(receipts.EngSftError) as raised:
            label_audit.run_close(
                disposition="ii", ruling_anchor=anchor, repo_root=self.root, local_root=self.local
            )
        self.assertEqual(raised.exception.reason, "AUDIT_INCOMPLETE")

    def _open_and_close(self, plan):
        """夹具：J7 一张判错 → stats 写原开放收据 → 具名裁定 → 闭合。返回 (错面板, 另一张用户面板, 锚点)。"""
        user = [p for p in plan["panels"] if p["share"] == "user"]
        excluded = next(p["panel_index"] for p in user if p["layer"] == "J7")
        other = next(p for p in user if p["layer"] in ("J1", "J2", "J3"))
        synth.write_unity_verdicts(self.root, plan, wrong_panels=[excluded])
        self._precheck_and_commit()
        label_audit.run_stats(repo_root=self.root, local_root=self.local)
        anchor = "AC-14 修订 3"
        proposal = self.root / label_audit.PROPOSAL_PATH
        proposal.parent.mkdir(parents=True, exist_ok=True)
        proposal.write_text(f"# 夹具提案\n\n| {anchor} | 表 J (ii) 上游标签缺陷 |\n", encoding="utf-8")
        synth.git_commit_all(self.root, "ruling")
        label_audit.run_close(disposition="ii", ruling_anchor=anchor, repo_root=self.root, local_root=self.local)
        self.assertIsNone(label_audit.audit_gate_state(repo_root=self.root, local_root=self.local)["reason"])
        return excluded, other, anchor

    def test_replanned_user_share_invalidates_closure(self) -> None:
        """R1@K4 F1 返工：计划重抽后，旧闭合记录不得继续放行 freeze（判定值恰好不变也不行）。"""
        plan = self.plan()
        _excluded, other, anchor = self._open_and_close(plan)
        finding = self.local / receipts.RECEIPTS_DIRNAME / label_audit.FINDING_RECEIPT_NAME

        # 一张**未判错**的用户面板换成了另一个样本；判定表一字未改，verdict_digest 不变。
        plan_path = label_audit.plan_json_path(self.local)
        replanned = json.loads(plan_path.read_text(encoding="utf-8"))
        for panel in replanned["panels"]:
            if panel["panel_index"] == other["panel_index"]:
                panel["key"] = panel["key"] + "-replanned"
                panel["frame_id"] = panel["frame_id"] + ".replanned"
        plan_path.write_text(json.dumps(replanned, ensure_ascii=False), encoding="utf-8")
        state = label_audit.audit_gate_state(repo_root=self.root, local_root=self.local)
        self.assertEqual(state["reason"], "AUDIT_FINDING_OPEN")
        self.assertIn("用户份额", state["message"])
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "AUDIT_FINDING_OPEN")
        # 叠加图重绘（样本身份不变、图字节变）同样使旧闭合失效。
        for panel in replanned["panels"]:
            if panel["panel_index"] == other["panel_index"]:
                panel["key"] = other["key"]
                panel["frame_id"] = other["frame_id"]
                panel["overlay_sha256"] = "0" * 64
        plan_path.write_text(json.dumps(replanned, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(
            label_audit.audit_gate_state(repo_root=self.root, local_root=self.local)["reason"],
            "AUDIT_FINDING_OPEN",
        )

        # 按新计划重新闭合：绑定新用户份额，原开放收据 SHA 不变 → 放行，freeze 记下摘要。
        document = label_audit.run_close(
            disposition="ii", ruling_anchor=anchor, repo_root=self.root, local_root=self.local
        )
        self.assertEqual(document["finding_receipt_sha256"], receipts.sha256_file(finding))
        self.assertEqual(document["user_share_digest"], label_audit.user_share_digest(replanned))
        state = label_audit.audit_gate_state(repo_root=self.root, local_root=self.local)
        self.assertIsNone(state["reason"])
        frozen = build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(frozen["audit"]["user_share_digest"], document["user_share_digest"])

    def test_rerun_stats_keeps_original_open_receipt(self) -> None:
        """AC-14 修订 3「保留原 AUDIT_FINDING_OPEN 历史」：重跑 stats 不改写原开放收据。"""
        plan = self.plan()
        excluded, other, _anchor = self._open_and_close(plan)
        receipts_dir = self.local / receipts.RECEIPTS_DIRNAME
        finding = receipts_dir / label_audit.FINDING_RECEIPT_NAME
        original_open = finding.read_bytes()

        # 判定表变了（一张改判「不确定」），「错」集合不变 → 闭合过期、需重绑，但原收据逐字节保留。
        log_path = self.root / label_audit.UNITY_LOG_PATH
        text = log_path.read_text(encoding="utf-8")
        row_prefix = f"| {other['panel_index']} | 对 |"
        self.assertIn(row_prefix, text)
        log_path.write_text(
            text.replace(row_prefix, f"| {other['panel_index']} | 不确定 |", 1), encoding="utf-8"
        )
        state = label_audit.run_stats(repo_root=self.root, local_root=self.local)
        self.assertEqual(state["reason"], "AUDIT_FINDING_OPEN")
        self.assertEqual(finding.read_bytes(), original_open)
        stats_runs = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(receipts_dir.glob("run-audit-*.json"))
        ]
        self.assertIn("preserved", [run.get("finding_receipt") for run in stats_runs])
        self.assertFalse(list(receipts_dir.glob("audit-finding-open.superseded-*.json")))

        # 「错」集合变了（新 finding）→ 旧收据原样另存，再写新收据；面板字段是序号。
        synth.write_unity_verdicts(self.root, plan, wrong_panels=[excluded, other["panel_index"]])
        label_audit.run_stats(repo_root=self.root, local_root=self.local)
        superseded = list(receipts_dir.glob("audit-finding-open.superseded-*.json"))
        self.assertEqual(len(superseded), 1)
        self.assertEqual(superseded[0].read_bytes(), original_open)
        renewed = json.loads(finding.read_text(encoding="utf-8"))
        self.assertEqual(renewed["panels"], sorted([excluded, other["panel_index"]]))

    def test_prescreen_table_is_disclosure_only(self) -> None:
        plan = self.plan()
        prescreen = [p for p in plan["panels"] if p["share"] == "prescreen"]
        self.assertTrue(prescreen)
        results = [
            {"panel_index": prescreen[0]["panel_index"], "状态": "错", "错误类型": ["类别错"]},
        ]
        path = self.root / "prescreen.json"
        path.write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")
        label_audit.run_prescreen(path, repo_root=self.root, local_root=self.local)
        document = (self.root / label_audit.AUDIT_PATH).read_text(encoding="utf-8")
        self.assertIn("## 6. 实现者预筛", document)
        self.assertIn("不计为语义核验", document)
        # 预筛里的「错」不写开放收据、不阻止冻结。
        synth.write_unity_verdicts(self.root, plan)
        state = label_audit.audit_gate_state(repo_root=self.root, local_root=self.local)
        self.assertIsNone(state["reason"])
        # 非预筛份额的面板不得出现在预筛表里。
        user_panel = next(p for p in plan["panels"] if p["share"] == "user")
        path.write_text(
            json.dumps([{"panel_index": user_panel["panel_index"], "状态": "对"}], ensure_ascii=False),
            encoding="utf-8",
        )
        with self.assertRaises(receipts.EngSftError) as raised:
            label_audit.run_prescreen(path, repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "AUDIT_INCOMPLETE")


class ReuseTests(AuditCase):
    def test_asset001_intersection_table(self) -> None:
        plan = self.plan()
        with_objects = [p for p in plan["panels"] if p["object_ids"]][:3]
        self.assertTrue(with_objects)
        pairs = [(p["frame_id"], p["object_ids"][0]) for p in with_objects]
        pairs.append(("runtime/frames.fixture/none/frame_0000009999.jpg", "Vehicle_Taxi (1)"))
        synth.write_asset001_audit(self.root, pairs)

        mapping = label_audit.asset001_panels(self.root)
        self.assertEqual(len(mapping), len(pairs))
        rows = label_audit.intersection_rows(plan["panels"], self.root)
        self.assertEqual(
            {(row["frame_id"], row["object_id"]) for row in rows}, set(pairs[:3])
        )
        for row in rows:
            self.assertEqual(
                row["asset001_panel_index"], mapping[(row["frame_id"], row["object_id"])]
            )
        # 交集表进抽查文件，并写明三态状态仍须本次判定、不构成 S6 审计。
        label_audit.run_plan(repo_root=self.root, local_root=self.local)
        document = (self.root / label_audit.AUDIT_PATH).read_text(encoding="utf-8")
        self.assertIn("## 4. 与 P1-ENG-ASSET-001 面板的交集", document)
        self.assertIn("三态状态仍须本次判定", document)
        self.assertIn("不构成 S6 审计", document)


if __name__ == "__main__":
    unittest.main()
