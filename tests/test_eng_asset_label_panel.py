"""P1-ENG-ASSET-001 AC-4：分层抽样、配额/上限、面板生成前置与判定统计。

不调用任何模型，也不解码真实图像：本文件只覆盖抽样规则、配额文件提交前置与
「只读 Unity 日志条目出统计」的口径。面板绘制需要 Pillow，属执行期依赖，
不进自动测试（合同 §4 释义：复核验证只用无模型夹具）。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data.artifacts import ArtifactStore  # noqa: E402
from tools.eng_asset import inventory, label_panel, receipts  # noqa: E402

try:  # 面板绘制需要图像库；缺失时只跳过像素级用例，几何契约仍由纯算术覆盖。
    from PIL import Image  # noqa: F401

    PILLOW = True
except ImportError:  # pragma: no cover
    PILLOW = False

OBJ_UNVERIFIED = "Vehicle_Car_color03"
OBJ_COLOR = "Vehicle_Car_color01"
OBJ_SMALL = "Vehicle_Bus_color03"
OBJ_LARGE = "Vehicle_Taxi_color01"

COLOR_STATUS = {
    OBJ_UNVERIFIED: "UNVERIFIED",
    OBJ_COLOR: "VERIFIED",
    OBJ_SMALL: "VERIFIED",
    OBJ_LARGE: "VERIFIED",
}


def _stub_draw(source, destination, row) -> None:
    """绘制桩：真实绘制需 Pillow，本文件的像素级契约另有具名回归覆盖。"""
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    Path(destination).write_bytes(b"drawn-" + Path(source).name.encode() + str(row["panel_index"]).encode())


def row(object_id: str, index: int, *, status: str, side: float) -> dict:
    return {
        "frame_id": f"runtime/frames.fx/frame_{index:010d}.jpg",
        "object_id": object_id,
        "split": "dev",
        "uniqueness_status": status,
        "surface": "the car" if status.startswith("UNIQUE") else None,
        "short_side_px": side,
        "visible_norm_xywh": [0.1, 0.1, 0.2, 0.2],
    }


def sample_rows() -> list[dict]:
    rows: list[dict] = []
    # S1 候选：颜色未验证，同时满足 S2（UNIQUE_CLASS_COLOR）与 S3（短边 < 32）
    # 的条件——优先序必须把它们全部归到 S1。
    rows += [row(OBJ_UNVERIFIED, i, status="UNIQUE_CLASS_COLOR", side=10.0) for i in range(1, 6)]
    # S2 候选：颜色已验证的 UNIQUE_CLASS_COLOR，短边大。
    rows += [row(OBJ_COLOR, i, status="UNIQUE_CLASS_COLOR", side=100.0) for i in range(11, 15)]
    # S3 候选：只有 1 行，配额 2 → 不足额留空、不回填。
    rows += [row(OBJ_SMALL, 21, status="UNIQUE_CLASS", side=10.0)]
    # S4 候选：单一对象 6 行，配额 3 → 每对象每层上限 2 生效。
    rows += [row(OBJ_LARGE, i, status="UNIQUE_CLASS", side=100.0) for i in range(31, 37)]
    # 不入层：UNIQUE_CLASS、颜色已验证、短边介于 32 与 64 之间。
    rows += [row(OBJ_LARGE, 41, status="UNIQUE_CLASS", side=48.0)]
    return rows


class LabelPanelTests(unittest.TestCase):
    def test_stratum_priority_quota_and_per_object_cap(self) -> None:
        quotas = {"S1": 2, "S2": 2, "S3": 2, "S4": 3}
        plan = label_panel.plan_sample(sample_rows(), COLOR_STATUS, seed="seed-a", quotas=quotas)

        self.assertEqual(plan.denominators, {"S1": 5, "S2": 4, "S3": 1, "S4": 6})
        taken = plan.taken
        self.assertEqual(taken["S1"], 2, "配额封顶")
        self.assertEqual(taken["S2"], 2)
        self.assertEqual(taken["S3"], 1, "不足额留空不回填")
        self.assertEqual(taken["S4"], 2, "每对象每层 ≤ 2")
        self.assertEqual(len(plan.selected), 7)
        self.assertLessEqual(len(plan.selected), label_panel.MAX_PANELS)

        # 优先序：颜色未验证的行即使同时命中 S2/S3 也只归 S1。
        self.assertTrue(all(item["object_id"] == OBJ_UNVERIFIED for item in plan.selected if item["stratum"] == "S1"))
        self.assertFalse(any(item["object_id"] == OBJ_UNVERIFIED for item in plan.selected if item["stratum"] != "S1"))
        # 不入层的行不得被抽中。
        self.assertNotIn(48.0, [item["short_side_px"] for item in plan.selected])
        # panel_index 连续、层序稳定；同一种子重跑逐字相同。
        self.assertEqual([item["panel_index"] for item in plan.selected], list(range(1, 8)))
        self.assertEqual(
            [item["frame_id"] for item in plan.selected],
            [item["frame_id"] for item in label_panel.plan_sample(sample_rows(), COLOR_STATUS, seed="seed-a", quotas=quotas).selected],
        )
        # 换种子换样本（抽样键真的参与排序）。
        other = label_panel.plan_sample(sample_rows(), COLOR_STATUS, seed="seed-b", quotas=quotas)
        self.assertNotEqual(
            [item["frame_id"] for item in plan.selected], [item["frame_id"] for item in other.selected]
        )
        # 层内按 SHA-256(seed‖frame_id‖object_id) 升序。
        for stratum in label_panel.STRATA:
            keys = [item["sample_key"] for item in plan.selected if item["stratum"] == stratum]
            self.assertEqual(keys, sorted(keys))

    def test_panel_generation_refuses_uncommitted_quota_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            evidence = repo / "docs" / "evidence"
            evidence.mkdir(parents=True)
            audit = evidence / label_panel.AUDIT_FILENAME
            audit.write_text(
                label_panel.SEED_LINE.format(seed="seed-a") + "\n" + label_panel.QUOTA_LINE.format(quotas="20/15/15/10") + "\n",
                encoding="utf-8",
            )
            local = repo / "local"
            panels_root = repo / "outputs-root"

            with self.assertRaises(receipts.QuotaFileDirty):
                label_panel.stage_panels(
                    repo_root=repo,
                    artifact_root=repo / "dist-data",
                    local_root=local,
                    evidence_dir=evidence,
                    panel_root=panels_root,
                )

            failures = list((local / "receipts").glob("failure-panel-*.json"))
            self.assertEqual(len(failures), 1)
            document = json.loads(failures[0].read_text(encoding="utf-8"))
            self.assertEqual(document["reason"], "QUOTA_FILE_DIRTY")
            self.assertFalse((panels_root / "panel").exists(), "未通过前置不得生成任何面板")
            self.assertFalse((local / "panel").exists(), "旧落点也不得再被写入")
            self.assertFalse((local / label_panel.PANEL_RECEIPT_NAME).exists())

    def _plan(self) -> label_panel.SamplePlan:
        return label_panel.SamplePlan(
            seed="seed-a",
            quotas={"S1": 2, "S2": 1, "S3": 0, "S4": 1},
            denominators={"S1": 2, "S2": 1, "S3": 0, "S4": 1},
            denominator_objects={"S1": 1, "S2": 1, "S3": 0, "S4": 1},
            selected=[
                {"panel_index": 1, "stratum": "S1", "frame_id": "f1", "object_id": OBJ_UNVERIFIED,
                 "split": "dev", "uniqueness_status": "UNIQUE_CLASS", "surface": "the car",
                 "short_side_px": 40.0, "visible_norm_xywh": [0, 0, 1, 1], "sample_key": "a"},
                {"panel_index": 2, "stratum": "S1", "frame_id": "f2", "object_id": OBJ_UNVERIFIED,
                 "split": "dev", "uniqueness_status": "UNIQUE_CLASS", "surface": "the car",
                 "short_side_px": 40.0, "visible_norm_xywh": [0, 0, 1, 1], "sample_key": "b"},
                {"panel_index": 3, "stratum": "S2", "frame_id": "f3", "object_id": OBJ_COLOR,
                 "split": "test", "uniqueness_status": "UNIQUE_CLASS_COLOR", "surface": "the red car",
                 "short_side_px": 90.0, "visible_norm_xywh": [0, 0, 1, 1], "sample_key": "c"},
                {"panel_index": 4, "stratum": "S4", "frame_id": "f4", "object_id": OBJ_LARGE,
                 "split": "test", "uniqueness_status": "UNIQUE_CLASS", "surface": "the taxi",
                 "short_side_px": 90.0, "visible_norm_xywh": [0, 0, 1, 1], "sample_key": "d"},
            ],
        )

    def _log(self, tmp: Path, rows: str, *, state: str = "COMPLETE", entry_twice: bool = False,
             schema: str = label_panel.VERDICT_SCHEMA_LINE) -> Path:
        entry = "\n".join(
            [
                f"## {label_panel.UNITY_LOG_ENTRY}",
                "",
                schema,
                label_panel.VERDICT_STATUS_LINE,
                f"{label_panel.VERDICT_STATE_PREFIX} {state}",
                label_panel.VERDICT_MANIFEST_LINE,
                "",
                label_panel.VERDICT_TABLE_SECTION,
                "",
                label_panel.VERDICT_TABLE_HEADER,
                label_panel.VERDICT_TABLE_RULE,
                rows,
                "",
                label_panel.VERDICT_FREETEXT_SECTION,
                "",
                "（原话；解析器不读本节）| 1 | 对 | 对 | 对 | |",
                "",
            ]
        )
        text = "# Unity test log\n\n## UT-P1-OTHER-001 别的条目\n\n| 1 | 对 | 对 | 对 | |\n\n" + entry
        if entry_twice:
            text += "\n" + entry
        path = tmp / "unity-test-log.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_statistics_read_only_from_unity_log_entry(self) -> None:
        plan = self._plan()
        rows = "\n".join(
            [
                "| 1 | 对 | 错 | 对 | 颜色错 |",
                "| 2 | 对 | 不确定 | 不确定 |  |",
                "| 3 | 错 | 对 | 错 | 类别错、框不紧或截断 |",
                "| 4 | 对 | 对 | 对 |  |",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            log = self._log(Path(tmp), rows)
            before = log.read_bytes()
            verdicts = label_panel.read_unity_verdicts(
                log, expected_indices=[row["panel_index"] for row in plan.selected]
            )
            self.assertEqual(log.read_bytes(), before, "统计只读，不得改写 Unity 日志")

        self.assertEqual([item["panel_index"] for item in verdicts], [1, 2, 3, 4])
        stats = label_panel.statistics(plan, verdicts)
        s1 = stats["per_stratum"]["S1"]
        self.assertEqual(s1["judged"], 2)
        self.assertEqual(s1["unjudged"], 0)
        self.assertEqual(s1["aspects"]["class"]["对"], 2)
        self.assertEqual(s1["aspects"]["color"], {"对": 0, "错": 1, "不确定": 1})
        self.assertEqual(s1["aspects"]["box"]["不确定"], 1, "「不确定」单独计数，不计为对")
        s2 = stats["per_stratum"]["S2"]
        self.assertEqual(s2["error_types"]["类别错"], 1)
        self.assertEqual(s2["error_types"]["框不紧或截断"], 1)
        self.assertEqual(s2["error_types"]["遮挡误判"], 0)
        self.assertTrue(stats["per_stratum"]["S3"]["empty_stratum"], "空层不计为通过")
        block = label_panel.render_statistics_block(stats)
        self.assertIn(label_panel.UNITY_LOG_ENTRY, block)
        self.assertIn("空层不计为通过", block)

    def _legal_env(self, repo: Path, *, render_fix: bool = True) -> dict:
        """一套可让生产 `stage_stats` 成功走完的环境。

        **全部派生工件由生产写入器产出**（COORD-007 R3 (1)；R1@K4 N2）：
        工件用 `ArtifactStore`、指令逐行用 `inventory._write_instructions`、清单用
        `stage_plan`、`panel-receipt.json` 与叠加图用 `stage_panels`、
        `run-render-fix-*.json` 与当前叠加图用 `stage_render_fix`。只有绘制本身用桩替身
        （真实绘制需 Pillow，另有像素级具名回归覆盖），git 提交门用桩替身（另有专门用例）。
        """
        local = repo / "local"
        evidence = repo / "docs" / "evidence"
        artifacts = repo / "dist-data"
        panels_root = repo / "outputs-root"
        frames = repo / "frames"
        evidence.mkdir(parents=True)
        local.mkdir(parents=True)
        frames.mkdir()
        archived = frames / "a.jpg"
        archived.write_bytes(b"archived-frame-a")

        store = ArtifactStore(artifacts, root=".")
        store.write(
            "field_catalog",
            "attempt-t1",
            {
                "stage": 5,
                "objects": {
                    OBJ_UNVERIFIED: {
                        "object_id": OBJ_UNVERIFIED,
                        "class": "car",
                        "class_verified": True,
                        "color": None,
                        "color_status": "UNVERIFIED",
                    }
                },
                "dual_verified_object_ids": [],
                "verified_color_vocabulary": [],
                "groups": {},
            },
            stage=5,
        )
        store.write(
            "inventory",
            "attempt-t1",
            {
                "stage": 1,
                "records": [
                    {"path": "frames/a.jpg", "kind": "image", "decision": "INCLUDED",
                     "sha256": receipts.sha256_file(archived), "bytes": archived.stat().st_size}
                ],
            },
            stage=1,
        )
        instructions = local / "instructions.ndjson.gz"
        inventory._write_instructions(
            instructions,
            iter([dict(row(OBJ_UNVERIFIED, 1, status="UNIQUE_CLASS", side=40.0),
                       frame_id="frames/a.jpg")]),
        )

        common = dict(repo_root=repo, artifact_root=artifacts, attempt="attempt-t1",
                      local_root=local, evidence_dir=evidence)
        label_panel.stage_plan(seed="seed-a", quotas={"S1": 1, "S2": 0, "S3": 0, "S4": 0}, **common)

        original_draw, original_commit = label_panel.draw_panel, label_panel.quota_file_commit
        label_panel.draw_panel = _stub_draw
        label_panel.quota_file_commit = lambda audit_path, repo_root: "0" * 40
        try:
            label_panel.stage_panels(panel_root=panels_root, **common)
            if render_fix:
                label_panel.stage_render_fix(panel_root=panels_root, **common)
        finally:
            label_panel.draw_panel, label_panel.quota_file_commit = original_draw, original_commit

        audit = evidence / label_panel.AUDIT_FILENAME
        overlay = panels_root / "panel" / "panel-001.jpg"
        log = self._log(repo, "| 1 | 对 | 错 | 不确定 | 颜色错 |")
        return {"local": local, "evidence": evidence, "artifacts": artifacts,
                "audit": audit, "log": log, "panels_root": panels_root,
                "overlay": overlay, "overlay_sha": receipts.sha256_file(overlay),
                "instructions": instructions, "archived": archived, "common": common}

    def _stats(self, repo: Path, env: dict, **overrides):
        return label_panel.stage_stats(
            repo_root=repo,
            artifact_root=env["artifacts"],
            attempt="attempt-t1",
            local_root=env["local"],
            evidence_dir=env["evidence"],
            unity_log=env["log"],
            panel_root=env["panels_root"],
            **overrides,
        )

    def test_plan_publishes_manifest_only_after_input_verification(self) -> None:
        """C1-1：`stage_plan` 的输入核验必须先于发布；失败时既有清单原样保留。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = self._legal_env(repo)
            before = env["audit"].read_text(encoding="utf-8")
            receipts_before = {item.name for item in (env["local"] / "receipts").glob("run-panel-plan-*.json")}
            original_plan_sample = label_panel.plan_sample

            def mutating_plan_sample(*args, **kwargs):
                result = original_plan_sample(*args, **kwargs)
                # 计划算完、清单写出之前，不变输入被改动。
                env["instructions"].write_bytes(env["instructions"].read_bytes() + b"\x00")
                return result

            label_panel.plan_sample = mutating_plan_sample
            try:
                with self.assertRaises(receipts.InputHashChanged):
                    label_panel.stage_plan(
                        repo_root=repo,
                        artifact_root=env["artifacts"],
                        attempt="attempt-t1",
                        local_root=env["local"],
                        evidence_dir=env["evidence"],
                        seed="seed-a",
                        quotas={"S1": 1, "S2": 0, "S3": 0, "S4": 0},
                    )
            finally:
                label_panel.plan_sample = original_plan_sample

            self.assertEqual(env["audit"].read_text(encoding="utf-8"), before,
                             "输入核验失败时既有清单必须原样保留")
            self.assertEqual(
                {item.name for item in (env["local"] / "receipts").glob("run-panel-plan-*.json")},
                receipts_before,
                "失败不得新增成功收据",
            )

    def test_panels_publish_nothing_when_a_later_source_hash_mismatches(self) -> None:
        """C1-1：第 2 张源图哈希不符时，第 1 张也不得留在正式落点。

        绘制本身用桩替身（真实绘制需 Pillow，另有像素级具名回归覆盖）；本用例走的是
        `stage_panels` 的生产入口与其 staging→核验→发布次序。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = self._legal_env(repo)
            frames = repo / "frames"
            good, bad = env["archived"], frames / "b.jpg"
            bad.write_bytes(b"frame-b")
            store = ArtifactStore(env["artifacts"], root=".")
            store.write(
                "inventory",
                "attempt-t2",
                {
                    "stage": 1,
                    "records": [
                        {"path": "frames/a.jpg", "kind": "image", "decision": "INCLUDED",
                         "sha256": receipts.sha256_file(good), "bytes": good.stat().st_size},
                        # 声明哈希与实际字节不符：读到第 2 张时才发现。
                        {"path": "frames/b.jpg", "kind": "image", "decision": "INCLUDED",
                         "sha256": "f" * 64, "bytes": bad.stat().st_size},
                    ],
                },
                stage=1,
            )
            ArtifactStore(env["artifacts"], root=".").write(
                "field_catalog", "attempt-t2",
                json.loads((env["artifacts"] / "field_catalog" / "attempt-t1" / "field_catalog.json")
                           .read_text(encoding="utf-8"))["payload"],
                stage=5,
            )
            inventory._write_instructions(
                env["instructions"],
                iter([
                    dict(row(OBJ_UNVERIFIED, 1, status="UNIQUE_CLASS", side=40.0), frame_id="frames/a.jpg"),
                    dict(row(OBJ_UNVERIFIED, 2, status="UNIQUE_CLASS", side=40.0), frame_id="frames/b.jpg"),
                ]),
            )
            # 配额放到 2，两张都要画；stage_panels 从清单解析种子/配额。
            env["audit"].write_text(
                env["audit"].read_text(encoding="utf-8").replace(
                    label_panel.QUOTA_LINE.format(quotas="1/0/0/0"),
                    label_panel.QUOTA_LINE.format(quotas="2/0/0/0"),
                ),
                encoding="utf-8",
            )
            panel_dir = env["panels_root"] / "panel"
            existing = {item.name: item.read_bytes() for item in panel_dir.glob("*.jpg")}

            original_draw, original_commit = label_panel.draw_panel, label_panel.quota_file_commit
            label_panel.draw_panel = lambda source, destination, row: (
                destination.parent.mkdir(parents=True, exist_ok=True),
                destination.write_bytes(b"drawn-" + Path(source).name.encode()),
            )
            label_panel.quota_file_commit = lambda audit_path, repo_root: "0" * 40
            try:
                with self.assertRaises(receipts.InputHashChanged):
                    label_panel.stage_panels(
                        repo_root=repo,
                        artifact_root=env["artifacts"],
                        attempt="attempt-t2",
                        local_root=env["local"],
                        evidence_dir=env["evidence"],
                        panel_root=env["panels_root"],
                    )
            finally:
                label_panel.draw_panel, label_panel.quota_file_commit = original_draw, original_commit

            self.assertEqual(
                {item.name: item.read_bytes() for item in panel_dir.glob("*.jpg")},
                existing,
                "后一张源图哈希不符时，前一张不得留在正式落点、既有面板不得被改",
            )
            self.assertEqual(
                {item.name for item in (panel_dir / "original").glob("*.jpg")},
                {"panel-001-original.jpg"},
                "原图副本同样不得抢先发布（只应保留夹具已发布的那一张）",
            )
            self.assertFalse(list((env["panels_root"]).glob(".staging-panel/**/*.jpg")),
                             "staging 必须被清理")

    def test_stats_fails_closed_when_verdict_log_changes_midrun(self) -> None:
        """R1@K4 F1：日志是不变输入——解析后被改动即失败退出，不得用新字节写成功收据。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = self._legal_env(repo)
            before = env["audit"].read_text(encoding="utf-8")
            original_reader = label_panel.read_unity_verdicts

            def mutating_reader(*args, **kwargs):
                result = original_reader(*args, **kwargs)
                # 解析之后、写出之前，代录条目被改动。
                env["log"].write_text(
                    env["log"].read_text(encoding="utf-8") + "\n<!-- 事后追加 -->\n",
                    encoding="utf-8",
                )
                return result

            label_panel.read_unity_verdicts = mutating_reader
            try:
                with self.assertRaises(receipts.InputHashChanged) as caught:
                    self._stats(repo, env)
            finally:
                label_panel.read_unity_verdicts = original_reader

            changed = [item["path"] for item in caught.exception.offending]
            self.assertIn(receipts.relative_to_root(env["log"], repo), changed,
                          "日志变化必须被核验发现")
            failures = list((env["local"] / "receipts").glob("failure-stats-*.json"))
            self.assertEqual(len(failures), 1)
            self.assertEqual(json.loads(failures[0].read_text(encoding="utf-8"))["reason"],
                             "INPUT_HASH_CHANGED")
            self.assertFalse(list((env["local"] / "receipts").glob("run-stats-*.json")),
                             "失败不得写成功收据")
            self.assertEqual(env["audit"].read_text(encoding="utf-8"), before,
                             "既有统计/清单必须原样保留")

    def test_stats_refuses_placeholder_overlay_identity_in_manifest(self) -> None:
        """R1@K4 F2：清单的 overlay_sha256 是占位/缺失时不得放行。

        走生产路径制造占位：重跑 `stage_plan` 会把清单 §3 回到 `(pending)`，叠加图仍在盘上。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = self._legal_env(repo)
            label_panel.stage_plan(seed="seed-a", quotas={"S1": 1, "S2": 0, "S3": 0, "S4": 0},
                                   **env["common"])
            reset = env["audit"].read_text(encoding="utf-8")
            self.assertIn(label_panel.PENDING, reset, "夹具前提：清单已回到占位状态")
            self.assertTrue(env["overlay"].is_file(), "叠加图仍在盘上")

            with self.assertRaises(receipts.InputHashChanged) as caught:
                self._stats(repo, env)
            problems = [item.get("problem") for item in caught.exception.offending]
            self.assertIn("MANIFEST_OVERLAY_SHA_MISSING_OR_PLACEHOLDER", problems)
            self.assertFalse(list((env["local"] / "receipts").glob("run-stats-*.json")))
            self.assertEqual(env["audit"].read_text(encoding="utf-8"), reset, "失败不得改写清单")

    def test_plan_failure_does_not_write_closed_set_failure_receipt(self) -> None:
        """R1@K4 F3：闭集外的前置失败不得借用闭集 reason 写失败收据。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = self._legal_env(repo)
            env["instructions"].unlink()  # 先跑 plan 后跑 inventory 的次序错误
            before = {item.name for item in (env["local"] / "receipts").glob("failure-*.json")}

            with self.assertRaises(label_panel.PanelError):
                label_panel.stage_plan(seed="seed-a", quotas={"S1": 1, "S2": 0, "S3": 0, "S4": 0},
                                       **env["common"])

            new_failures = [
                item for item in (env["local"] / "receipts").glob("failure-*.json")
                if item.name not in before
            ]
            self.assertFalse(new_failures, "闭集外病因不得写失败收据")
            self.assertNotIsInstance(label_panel.PanelError("x"), receipts.EngAssetError,
                                     "PanelError 不得继承携带闭集 reason 的基类")
            self.assertFalse(hasattr(label_panel.PanelError("x"), "reason"),
                             "PanelError 不得携带闭集 token")

    def test_forbidden_panel_root_is_refused_without_touching_its_contents(self) -> None:
        """R1@K4 F5：拒绝禁写根时，不得清理该根下已存在的同名 staging 目录。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = self._legal_env(repo)
            forbidden = repo / "runtime" / "dist-data" / "eng-asset"
            keep = forbidden / ".staging-panel" / "keep.txt"
            keep.parent.mkdir(parents=True)
            keep.write_bytes(b"original-bytes")

            original_commit = label_panel.quota_file_commit
            label_panel.quota_file_commit = lambda audit_path, repo_root: "0" * 40
            try:
                with self.assertRaises(receipts.OutputPathForbidden):
                    label_panel.stage_panels(panel_root=forbidden, **env["common"])
            finally:
                label_panel.quota_file_commit = original_commit

            self.assertTrue(keep.is_file(), "禁写根下的既有内容不得被 finally 清理")
            self.assertEqual(keep.read_bytes(), b"original-bytes")

    def test_stats_refuses_when_panel_identity_differs_from_manifest(self) -> None:
        """C1-2：数量相等但身份不同（样本被替换）时必须失败，不能把旧判定套到新对象。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = self._legal_env(repo)
            before = env["audit"].read_text(encoding="utf-8")
            # 指令文件被同数量替换：对象换成另一辆车，索引仍是 1。
            inventory._write_instructions(
                env["instructions"], iter([row(OBJ_COLOR, 9, status="UNIQUE_CLASS", side=40.0)])
            )
            ArtifactStore(env["artifacts"], root=".").write(
                "field_catalog",
                "attempt-t2",
                {
                    "stage": 5,
                    "objects": {OBJ_COLOR: {"object_id": OBJ_COLOR, "class": "car",
                                            "class_verified": True, "color": None,
                                            "color_status": "UNVERIFIED"}},
                    "dual_verified_object_ids": [],
                    "verified_color_vocabulary": [],
                    "groups": {},
                },
                stage=5,
            )
            with self.assertRaises(receipts.InputHashChanged) as caught:
                label_panel.stage_stats(
                    repo_root=repo, artifact_root=env["artifacts"], attempt="attempt-t2",
                    local_root=env["local"], evidence_dir=env["evidence"],
                    unity_log=env["log"], panel_root=env["panels_root"],
                )
            problems = [item.get("problem") for item in caught.exception.offending]
            self.assertIn("PANEL_IDENTITY_DIFFERS_FROM_MANIFEST", problems)
            failures = list((env["local"] / "receipts").glob("failure-stats-*.json"))
            self.assertEqual(len(failures), 1)
            self.assertEqual(env["audit"].read_text(encoding="utf-8"), before, "失败不得改写清单")
            self.assertFalse(list((env["local"] / "receipts").glob("run-stats-*.json")))

    def test_stats_refuses_when_overlay_bytes_differ_from_manifest(self) -> None:
        """C1-2：用户所看叠加图的实际字节必须与清单记录相等。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = self._legal_env(repo)
            env["overlay"].write_bytes(b"tampered")
            with self.assertRaises(receipts.InputHashChanged) as caught:
                self._stats(repo, env)
            problems = [item.get("problem") for item in caught.exception.offending]
            self.assertIn("OVERLAY_SHA_DIFFERS_FROM_MANIFEST", problems)
            self.assertFalse(list((env["local"] / "receipts").glob("run-stats-*.json")))

    def test_stats_success_binds_read_manifest_and_written_output(self) -> None:
        """AC-1 修订 1 / AC-4 修订 2：成功路径必须区分读入清单快照与合法输出，
        并在清单里保留所采用的重绘来源（接受侧 2026-09-09 回交的两项）。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = self._legal_env(repo)
            snapshot_before = env["audit"].read_text(encoding="utf-8")

            stats = self._stats(repo, env)

            self.assertEqual(stats["verdicts_found"], 1)
            written = env["audit"].read_text(encoding="utf-8")
            self.assertNotEqual(written, snapshot_before, "统计必须写进清单")

            # 问题 2：来源叙述必须指向实际采用 overlay SHA 的那份重绘收据。
            render_fix = sorted((env["local"] / "receipts").glob("run-render-fix-*.json"))[-1]
            self.assertIn(render_fix.name, written)
            self.assertNotIn("当前叠加图为首次生成版本", written)
            self.assertIn(env["overlay_sha"], written, "清单里的 overlay SHA 与实际叠加图字节相等")

            # 问题 1：改写自身清单不得被算成输入不符，但成功收据要同时绑定读入与写出。
            runs = list((env["local"] / "receipts").glob("run-stats-*.json"))
            self.assertEqual(len(runs), 1)
            receipt = json.loads(runs[0].read_text(encoding="utf-8"))
            self.assertNotEqual(
                receipt["panel_manifest_read"]["sha256"],
                receipt["panel_manifest_written"]["sha256"],
                "读入快照与写出工件是两件事，不能是同一条 before/after",
            )
            self.assertEqual(
                receipt["panel_manifest_read"]["sha256"],
                hashlib.sha256(snapshot_before.encode("utf-8")).hexdigest(),
            )
            self.assertEqual(receipt["overlay_source_receipt"],
                             receipts.relative_to_root(render_fix, repo))
            document = json.loads((env["local"] / "receipts" / "input-manifest.json").read_text(encoding="utf-8"))
            stage = document["stages"]["audit-stats"]
            self.assertTrue(stage["equal"])
            self.assertTrue(stage["successful"])
            # F1：Unity 日志必须与其它不变输入同列，且成功收据取登记值而非事后现算。
            log_rel = receipts.relative_to_root(env["log"], repo)
            logged = [item for item in stage["before"] if item["path"] == log_rel]
            self.assertEqual(len(logged), 1, "Unity 日志必须登记为本阶段不变输入")
            self.assertEqual(receipt["verdict_source"]["sha256"], logged[0]["sha256"])
            self.assertEqual(receipt["verdict_source"]["bytes"], logged[0]["bytes"])
            self.assertIn(log_rel, document["union"], "停点并集须含日志")
            self.assertNotIn(
                receipts.relative_to_root(env["audit"], repo),
                [item["path"] for item in stage["before"]],
                "清单本身是输出，不得混进不变输入集",
            )
            self.assertFalse(list((env["local"] / "receipts").glob("failure-stats-*.json")))

    def test_stats_fails_closed_when_input_changes_midrun(self) -> None:
        """输入在执行期间变化时只出失败收据，既有统计原样保留。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = self._legal_env(repo)
            before = env["audit"].read_text(encoding="utf-8")
            instructions = env["local"] / "instructions.ndjson.gz"
            original_reader = label_panel.read_unity_verdicts

            def mutating_reader(*args, **kwargs):
                result = original_reader(*args, **kwargs)
                # 解析之后、写出之前，不变输入被改动。
                instructions.write_bytes(instructions.read_bytes() + b"\x00")
                return result

            label_panel.read_unity_verdicts = mutating_reader
            try:
                with self.assertRaises(receipts.InputHashChanged):
                    self._stats(repo, env)
            finally:
                label_panel.read_unity_verdicts = original_reader

            failures = list((env["local"] / "receipts").glob("failure-stats-*.json"))
            self.assertEqual(len(failures), 1)
            document = json.loads(failures[0].read_text(encoding="utf-8"))
            self.assertEqual(document["reason"], "INPUT_HASH_CHANGED")
            self.assertFalse(list((env["local"] / "receipts").glob("run-stats-*.json")),
                             "输入变化不得写成功收据")
            self.assertEqual(env["audit"].read_text(encoding="utf-8"), before,
                             "既有统计/清单必须原样保留")
            manifest = json.loads((env["local"] / "receipts" / "input-manifest.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["stages"]["audit-stats"]["successful"])

    def test_verdict_table_format_mismatch_fails_closed(self) -> None:
        """AC-4 修订 3 的失败闭集：任一不符即抛错，绝不产出部分统计。"""
        plan = self._plan()
        expected = [row["panel_index"] for row in plan.selected]
        good = ["| 1 | 对 | 对 | 对 |  |", "| 2 | 对 | 对 | 对 |  |",
                "| 3 | 对 | 对 | 对 |  |", "| 4 | 对 | 对 | 对 |  |"]
        cases = {
            "PANEL_INDEX_SET_MISMATCH": ("\n".join(good[:3]), {}),
            "PANEL_INDEX_DUPLICATED": ("\n".join(good[:3] + ["| 3 | 对 | 对 | 对 |  |"]), {}),
            "PANEL_INDEX_NOT_ASCENDING": ("\n".join([good[1], good[0], good[2], good[3]]), {}),
            "PANEL_INDEX_MALFORMED": ("\n".join(["| 01 | 对 | 对 | 对 |  |"] + good[1:]), {}),
            "VERDICT_VALUE_INVALID": ("\n".join(["| 1 | 未判定 | 对 | 对 |  |"] + good[1:]), {}),
            "ROW_COLUMN_COUNT": ("\n".join(["| 1 | 对 | 对 | 对 |"] + good[1:]), {}),
            "BACKTICK_NOT_ALLOWED": ("\n".join(["| 1 | `对` | 对 | 对 |  |"] + good[1:]), {}),
            "ERROR_SEPARATOR_INVALID": ("\n".join(["| 1 | 错 | 对 | 对 | 类别错, 颜色错 |"] + good[1:]), {}),
            "ERROR_TYPE_UNKNOWN": ("\n".join(["| 1 | 错 | 对 | 对 | 别的错 |"] + good[1:]), {}),
            "ERROR_TYPE_ORDER": ("\n".join(["| 1 | 错 | 对 | 对 | 颜色错、类别错 |"] + good[1:]), {}),
            "ERROR_TYPE_DUPLICATED": ("\n".join(["| 1 | 错 | 对 | 对 | 颜色错、颜色错 |"] + good[1:]), {}),
            "JUDGMENT_STATE_NOT_COMPLETE": ("\n".join(good), {"state": "PENDING"}),
            "ENTRY_MISSING_OR_DUPLICATED": ("\n".join(good), {"entry_twice": True}),
            "REQUIRED_LINE_MISSING_OR_DUPLICATED": ("\n".join(good), {"schema": "Schema: wrong/v9"}),
        }
        for expected_problem, (rows, options) in cases.items():
            with self.subTest(problem=expected_problem), tempfile.TemporaryDirectory() as tmp:
                log = self._log(Path(tmp), rows, **options)
                with self.assertRaises(receipts.VerdictFormatMismatch) as caught:
                    label_panel.read_unity_verdicts(log, expected_indices=expected)
                problems = [item.get("problem") for item in caught.exception.offending]
                self.assertIn(expected_problem, problems)
                self.assertEqual(caught.exception.reason, "VERDICT_FORMAT_MISMATCH")

        # 缺条目：日志文件存在但没有本项条目。
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "unity-test-log.md"
            empty.write_text("# Unity test log\n\n## UT-OTHER\n", encoding="utf-8")
            with self.assertRaises(receipts.VerdictFormatMismatch):
                label_panel.read_unity_verdicts(empty, expected_indices=expected)

    def test_stats_writes_only_failure_receipt_on_bad_verdict_table(self) -> None:
        """AC-4 修订 3：失败只新增 failure-stats 收据，不写成功收据、不覆盖清单。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = self._legal_env(repo)
            before = env["audit"].read_text(encoding="utf-8")
            # 代录表的 panel_index 与清单不符（7 ≠ 1）。
            self._log(repo, "| 7 | 对 | 对 | 对 |  |")

            with self.assertRaises(receipts.VerdictFormatMismatch):
                self._stats(repo, env)

            failures = list((env["local"] / "receipts").glob("failure-stats-*.json"))
            self.assertEqual(len(failures), 1)
            document = json.loads(failures[0].read_text(encoding="utf-8"))
            self.assertEqual(document["reason"], "VERDICT_FORMAT_MISMATCH")
            self.assertTrue(document["offending"])
            self.assertFalse(list((env["local"] / "receipts").glob("run-stats-*.json")), "失败不得写成功收据")
            self.assertEqual(env["audit"].read_text(encoding="utf-8"), before, "失败不得覆盖清单")

    @unittest.skipUnless(PILLOW, "面板绘制需要 Pillow；几何契约另由 panel_layout 覆盖")
    def test_panel_preserves_source_frame_and_box_coordinates(self) -> None:
        """AC-4 修订 2：原帧整幅保留、不缩放不裁剪，框与原帧同步平移。"""
        from PIL import Image  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "frame.jpg"
            # 无模型合成图夹具：每个像素颜色由坐标唯一决定，覆盖即可被发现。
            # 16×16 色块：每块颜色唯一，覆盖/平移会立刻显形；低频内容让 JPEG
            # 二次编码的量化误差远小于判据阈值（高频噪声图会让 JPEG 本身失真到无法判别）。
            synthetic = Image.new("RGB", (64, 48))
            synthetic.putdata([
                (40 + 60 * (x // 16), 30 + 70 * (y // 16), 200 - 50 * ((x // 16 + y // 16) % 3))
                for y in range(48)
                for x in range(64)
            ])
            synthetic.save(source, format="JPEG", quality=100)
            expected_pixels = list(Image.open(source).convert("RGB").getdata())

            destination = Path(tmp) / "panel-001.jpg"
            box = [0.25, 0.5, 0.5, 0.25]
            label_panel.draw_panel(source, destination, {
                "panel_index": 1, "stratum": "S3", "object_id": OBJ_SMALL,
                "uniqueness_status": "UNIQUE_CLASS", "surface": "the bus",
                "visible_norm_xywh": box,
            })

            layout = label_panel.panel_layout(64, 48)
            band = layout["offset"][1]
            panel = Image.open(destination).convert("RGB")
            self.assertEqual(panel.size, (64, 48 + band), "原帧不得缩放或裁剪，只允许加边带")

            corners = label_panel.translated_box(box, 64, 48, layout["offset"])
            frame_region = list(panel.crop((0, band, 64, 48 + band)).getdata())
            # 框线本身**应当**画在原帧上（那正是交付物），只核对框线以外的像素未被改动：
            # 跳过矩形四条边 ±3 px 的带。JPEG 二次编码只留量化误差，覆盖会造成整块偏差。
            x0, y0, x1, y1 = corners[0], corners[1] - band, corners[2], corners[3] - band
            worst = 0
            for index, (pixel, want) in enumerate(zip(frame_region, expected_pixels)):
                px, py = index % 64, index // 64
                near_edge = (
                    (abs(px - x0) <= 3 or abs(px - x1) <= 3) and y0 - 3 <= py <= y1 + 3
                ) or ((abs(py - y0) <= 3 or abs(py - y1) <= 3) and x0 - 3 <= px <= x1 + 3)
                if near_edge:
                    continue
                worst = max(worst, max(abs(a - b) for a, b in zip(pixel, want)))
            self.assertLessEqual(worst, 16, "框线以外的原帧像素被覆盖或替换")

            self.assertEqual(corners, (16.0, 24.0 + band, 48.0, 36.0 + band))
            # 框落在原帧区域内、且相对原帧坐标未偏移。
            self.assertGreaterEqual(corners[1] - band, 0.0)
            self.assertAlmostEqual(corners[0], box[0] * 64)
            self.assertAlmostEqual(corners[1] - band, box[1] * 48)

    def test_panel_layout_keeps_frame_unscaled_without_image_library(self) -> None:
        """几何契约的纯算术核对（无需 Pillow，全套在系统 python3 上也执行）。"""
        layout = label_panel.panel_layout(640, 480)
        band = layout["offset"][1]
        self.assertEqual(layout["canvas"], (640, 480 + band))
        self.assertEqual(layout["frame_origin"], (0, band))
        self.assertGreater(band, 0, "标题必须落在原帧之外")
        corners = label_panel.translated_box([0.0, 0.0, 1.0, 1.0], 640, 480, layout["offset"])
        self.assertEqual(corners, (0.0, float(band), 640.0, 480.0 + band))


class RelocateTests(unittest.TestCase):
    """AC-4 修订 1：同批图片原字节迁移，逐文件核对后才删旧件。"""

    def _seed(self, repo: Path) -> tuple[Path, Path]:
        local = repo / "local"
        old_panel = local / "panel"
        (old_panel / "original").mkdir(parents=True)
        (old_panel / "panel-001.jpg").write_bytes(b"overlay-1")
        (old_panel / "panel-002.jpg").write_bytes(b"overlay-2")
        (old_panel / "original" / "panel-001-original.jpg").write_bytes(b"origin-1")
        (local / label_panel.PANEL_RECEIPT_NAME).write_text("{}", encoding="utf-8")
        return local, old_panel

    def test_relocate_preserves_bytes_and_clears_old_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            local, old_panel = self._seed(repo)
            before = {p.relative_to(old_panel).as_posix(): p.read_bytes() for p in old_panel.rglob("*.jpg")}
            evidence = repo / "docs" / "evidence"
            evidence.mkdir(parents=True)
            (evidence / label_panel.AUDIT_FILENAME).write_text(
                f"- 面板与原图副本落本地 `{receipts.LOCAL_ROOT.as_posix()}/panel/`（git 忽略）。\n",
                encoding="utf-8",
            )
            panels_root = repo / "outputs-root"

            result = label_panel.stage_relocate(
                repo_root=repo, local_root=local, panel_root=panels_root, evidence_dir=evidence
            )

            new_panel = panels_root / "panel"
            after = {p.relative_to(new_panel).as_posix(): p.read_bytes() for p in new_panel.rglob("*.jpg")}
            self.assertEqual(after, before, "迁移必须原字节保留，含 original 副本")
            self.assertEqual(result["moved"], 3)
            self.assertFalse(list((local).rglob("*.jpg")), "旧落点核对相等后必须清空 jpg")
            receipt = json.loads((repo / result["receipt"]).read_text(encoding="utf-8"))
            self.assertEqual(receipt["stage"], "relocate")
            self.assertFalse(receipt["resampled"])
            self.assertFalse(receipt["rerendered"])
            self.assertEqual(receipt["extra_viewing_rounds"], 0)
            self.assertEqual(len(receipt["mapping"]), 3)
            self.assertIn("迁移收据", (evidence / label_panel.AUDIT_FILENAME).read_text(encoding="utf-8"))

    def test_relocate_keeps_source_when_copy_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            local, old_panel = self._seed(repo)
            panels_root = repo / "outputs-root"
            original_copy = label_panel.shutil.copyfile

            def corrupting_copy(src, dst):
                original_copy(src, dst)
                Path(dst).write_bytes(Path(dst).read_bytes() + b"!")

            label_panel.shutil.copyfile = corrupting_copy
            try:
                with self.assertRaises(receipts.InputHashChanged):
                    label_panel.stage_relocate(repo_root=repo, local_root=local, panel_root=panels_root)
            finally:
                label_panel.shutil.copyfile = original_copy

            self.assertEqual(len(list(old_panel.rglob("*.jpg"))), 3, "核对不相等必须保留源副本")
            failures = list((local / "receipts").glob("failure-relocate-*.json"))
            self.assertEqual(len(failures), 1)
            self.assertEqual(
                json.loads(failures[0].read_text(encoding="utf-8"))["reason"], "INPUT_HASH_CHANGED"
            )


if __name__ == "__main__":
    unittest.main()
