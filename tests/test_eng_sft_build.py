#!/usr/bin/env python3
"""P1-ENG-SFT-002 K4 构建器的具名回归（AC-1/2/3/5/6）。

全部在 `tests/fixtures/eng_sft/synth.py` 的合成小世界上跑**生产函数本身**：对账、
三态、取样、评估集、盲文件、预检、冻结、打包与写出边界共用一套代码，测试只替换
对账期望值与 tokenizer 计数器。
"""

from __future__ import annotations

import gzip
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
from tools.eng_sft import label_audit, prompt_v2, receipts  # noqa: E402
from tools.eng_sft.adapters import unity_s3  # noqa: E402
from tools.eng_sft.three_state import ObjectRecord, three_state  # noqa: E402


class FixtureCase(unittest.TestCase):
    """每个用例一份全新的小世界（互不污染）。"""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="eng-sft-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.world = synth.build_world(self.root)
        self.local = synth.local_root(self.root)

    def build(self):
        return synth.run_build(self.world)

    def read_jsonl(self, name: str) -> list[dict]:
        rows = []
        with open(self.local / build.DATA_DIRNAME / name, encoding="utf-8") as handle:
            for line in handle:
                rows.append(json.loads(line))
        return rows

    def receipts_dir(self) -> Path:
        return self.local / receipts.RECEIPTS_DIRNAME

    def failure_receipts(self) -> list[Path]:
        return sorted(self.receipts_dir().glob("failure-*.json"))


class ReconciliationTests(FixtureCase):
    def test_shard_hash_mismatch_writes_failure_receipt_only(self) -> None:
        shard = self.root / "runtime/dist-data/frames_catalog/attempt-2/shards/00000.ndjson.gz"
        with gzip.open(shard, "rt") as handle:
            lines = handle.readlines()
        with gzip.open(shard, "wt", compresslevel=1) as handle:  # 同内容不同字节 → SHA 变化
            handle.writelines(lines)
        with self.assertRaises(receipts.EngSftError) as raised:
            self.build()
        self.assertEqual(raised.exception.reason, "SHARD_HASH_MISMATCH")
        failures = self.failure_receipts()
        self.assertEqual(len(failures), 1)
        document = json.loads(failures[0].read_text(encoding="utf-8"))
        self.assertEqual(document["reason"], "SHARD_HASH_MISMATCH")
        # 失败即不发布工件：四份冻结 JSON 与 jsonl 一个都不许出现。
        self.assertFalse((self.root / build.DATASET_MANIFEST).exists())
        self.assertFalse((self.local / build.DATA_DIRNAME / build.TRAIN_JSONL).exists())

    def test_late_binding_failure_publishes_nothing(self) -> None:
        """C1-1：晚期核验（帧 SHA 绑定）失败时同样只写失败收据，不留下半成品工件。"""
        inventory = json.loads(
            (self.root / "runtime/dist-data/inventory/attempt-2/inventory.json").read_text("utf-8")
        )
        train_family = "p1-vlm-survey-a2-p1-c1-s1"
        touched = 0
        for record in inventory["payload"]["records"]:
            if f"/{train_family}/" in record["path"]:
                path = self.root / record["path"]
                path.write_bytes(path.read_bytes() + b"x")  # 字节变了，S1 记录没变
                touched += 1
        self.assertGreater(touched, 0)
        with self.assertRaises(receipts.EngSftError) as raised:
            self.build()
        self.assertEqual(raised.exception.reason, "INPUT_HASH_CHANGED")
        failures = self.failure_receipts()
        self.assertEqual(len(failures), 1)
        self.assertEqual(
            json.loads(failures[0].read_text(encoding="utf-8"))["reason"], "INPUT_HASH_CHANGED"
        )
        # 七份 jsonl、legacy 副本与四份冻结 JSON 一个都不许出现。
        data_dir = self.local / build.DATA_DIRNAME
        for name in (
            build.TRAIN_JSONL,
            build.SMOKE_JSONL,
            build.SELECT_EVAL_JSONL,
            build.SELECT_EVAL_BLIND,
            build.EVAL_JSONL,
            build.EVAL_BLIND,
            build.AUDIT_J7_JSONL,
        ):
            self.assertFalse((data_dir / name).exists(), name)
        self.assertFalse((data_dir / build.LEGACY_DIRNAME).exists())
        for path in build.FROZEN_JSON_FILES:
            self.assertFalse((self.root / path).exists(), path)
        # 输入清单以「未成功」保存，不进 union。
        document = json.loads((self.receipts_dir() / receipts.INPUT_MANIFEST_NAME).read_text("utf-8"))
        self.assertFalse(any(stage["successful"] for stage in document["stages"].values()))
        self.assertFalse(document["union"])

    def test_second_build_publish_failure_restores_replaced_files(self) -> None:
        """C2-1（R1@K4 §4 第 3 条）：第二次 build 在发布段中途失败，被覆盖的旧文件逐份按原字节还原。"""
        first = self.build()
        published = [(self.root / record["path"]).resolve() for record in first["outputs"]]
        self.assertTrue(all(path.is_file() for path in published))
        # 让「上一次发布」的字节与本次将写的字节可区分，还原与否才看得出来。
        before: dict[Path, bytes] = {}
        for path in published:
            path.write_bytes(path.read_bytes() + b"\n#previous-build\n")
            before[path] = path.read_bytes()
        # 删掉一份，使本次发布同时走「新建」分支（失败后应删掉，而不是留下新字节）。
        created = (self.root / build.LEAKAGE_REPORT).resolve()
        created.unlink()
        del before[created]

        original_write = build._write_bytes
        failing = (self.root / build.LEGACY_CONSERVATION).resolve()  # 计划里最后写的一份

        def flaky_write(path: Path, payload: bytes) -> None:
            if Path(path).resolve() == failing:
                Path(path).write_bytes(payload[: len(payload) // 2])  # 写到一半
                raise OSError("fixture: disk full while publishing")
            original_write(path, payload)

        build._write_bytes = flaky_write
        try:
            with self.assertRaises(OSError):
                self.build()
        finally:
            build._write_bytes = original_write

        for path, payload in before.items():
            self.assertEqual(path.read_bytes(), payload, path)
        self.assertFalse(created.exists())
        # I/O 失败没有合同内的失败原因 token：不编造失败收据，输入清单记为未成功。
        self.assertEqual(self.failure_receipts(), [])
        document = json.loads((self.receipts_dir() / receipts.INPUT_MANIFEST_NAME).read_text("utf-8"))
        build_stages = [stage for key, stage in document["stages"].items() if key.startswith("build")]
        self.assertEqual([stage["successful"] for stage in build_stages], [True, False])

    def test_shard_line_count_and_s0_constants_are_verified(self) -> None:
        """关注项 4：分片行数按实数比对、S0 常量与执行时常量必须一致。"""
        # 1. manifest 自报行数被改大 → 实数比对拆穿（不靠自报值通过）。
        manifest_path = self.root / "runtime/dist-data/frames_catalog/attempt-2/frames_catalog.json"
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        document["payload"]["shards"][0]["lines"] += 1
        document["payload"]["frame_count"] += 1
        document["payload"]["row_count"] += 1
        manifest_path.write_text(json.dumps(document), encoding="utf-8")
        expectations = synth.expectations(self.world)
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_build(
                repo_root=self.root,
                probe_root=self.world["probe_root"],
                local_root=self.local,
                expected=build.ReconcileExpectations(
                    s3_frames=expectations.s3_frames + 1,
                    s3_shards=expectations.s3_shards,
                    s4_frame_counts=expectations.s4_frame_counts,
                    s5_objects=expectations.s5_objects,
                    s5_class_verified=expectations.s5_class_verified,
                    s5_dual_verified=expectations.s5_dual_verified,
                    instruction_rows=expectations.instruction_rows,
                ),
            )
        self.assertEqual(raised.exception.reason, "MANIFEST_COUNT_MISMATCH")
        self.assertFalse((self.root / build.DATASET_MANIFEST).exists())
        document["payload"]["shards"][0]["lines"] -= 1
        document["payload"]["frame_count"] -= 1
        document["payload"]["row_count"] -= 1
        manifest_path.write_text(json.dumps(document), encoding="utf-8")
        # 2. S0 的词表/关系常量与执行时常量不一致 → 拒绝（归档与代码语义对不上）。
        contract_path = self.root / "runtime/dist-data/contract/attempt-2/contract.json"
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
        payload["payload"]["relations"]["viewer_side_min_separation_px"] = 1.0
        contract_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(receipts.EngSftError) as raised:
            self.build()
        self.assertEqual(raised.exception.reason, "INPUT_HASH_CHANGED")
        self.assertFalse((self.root / build.DATASET_MANIFEST).exists())

    def test_histogram_mismatch_fails_closed(self) -> None:
        path = self.root / "docs/evidence/P1-ENG-ASSET-001-instructions-summary.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        split = next(iter(summary["uniqueness_status_histogram"]))
        usage = next(iter(summary["uniqueness_status_histogram"][split]))
        status = next(iter(summary["uniqueness_status_histogram"][split][usage]))
        summary["uniqueness_status_histogram"][split][usage][status] += 1
        path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(receipts.EngSftError) as raised:
            self.build()
        self.assertEqual(raised.exception.reason, "HISTOGRAM_MISMATCH")
        self.assertFalse((self.root / build.DATASET_MANIFEST).exists())


class ReceiptTests(FixtureCase):
    def test_input_manifest_phases_append_only(self) -> None:
        self.build()
        self.build()
        document = json.loads((self.receipts_dir() / receipts.INPUT_MANIFEST_NAME).read_text("utf-8"))
        self.assertIn("build", document["stages"])
        self.assertIn("build#2", document["stages"])
        self.assertEqual(document["stages"]["build"]["stage"], "build")
        self.assertTrue(document["stages"]["build"]["successful"])
        self.assertTrue(document["union"])
        for stage in document["stages"].values():
            self.assertTrue(stage["equal"], stage["mismatches"])


class AdapterTests(FixtureCase):
    def _entry(self, layout: str) -> dict:
        return synth.frame_entry("m3-armB", 7, layout)

    def test_table_a_prime_cases_including_three_wildcard_inputs(self) -> None:
        catalog = self.world["field_catalog"]
        # 1. OK 目录车 referable；非 OK 目录车在 C 内但不在 M；未知类别阻断体 class=None。
        record = unity_s3.adapt_frame(self._entry("L5"), catalog)
        statuses = {obj.object_id: obj for obj in record.objects}
        self.assertTrue(statuses["Vehicle_Taxi (1)"].referable)
        self.assertFalse(statuses["Vehicle_SUV_color01 (1)"].referable)
        self.assertEqual(three_state(record.objects, {"class": "suv"}).state, "gray_uncertain_none")
        unknown = unity_s3.adapt_frame(self._entry("L8"), catalog)
        self.assertIsNone({o.object_id: o for o in unknown.objects}[synth.UNKNOWN_BLOCKER].class_word)
        self.assertEqual(three_state(unknown.objects, {"class": "car"}).state, "gray_definite_plus_uncertain")
        # 2. phantom：类别已知、颜色 None、不可指称。
        phantom = unity_s3.adapt_frame(self._entry("L9"), catalog)
        ghost = {o.object_id: o for o in phantom.objects}[synth.PHANTOM_ID]
        self.assertEqual((ghost.class_word, ghost.color_word, ghost.referable), ("taxi", None, False))
        # 3. #27 反例：该帧 bus 颜色指令整帧排除。
        counterexample = unity_s3.adapt_frame(self._entry("L4"), catalog)
        self.assertEqual(set(counterexample.excluded_color_classes), {"bus"})
        # 4. 目标车已绑定且裁剪后正面积 → definite，框来自裁剪后归一化。
        bound = unity_s3.adapt_frame(self._entry("L6"), catalog)
        self.assertTrue(bound.dynamic_target_definite)
        self.assertFalse(bound.frame_wildcard)
        self.assertEqual(
            bound.box_of("dynamic-target"), [280 / 640, 300 / 480, 120 / 640, 100 / 480]
        )
        # 5. 三种整帧通配输入各自核对。
        for layout, reason in (
            ("L10", unity_s3.WILDCARD_UNBOUND),
            ("L11", unity_s3.WILDCARD_MISSING_BOX),
            ("L12", unity_s3.WILDCARD_DEGENERATE_AFTER_CROP),
        ):
            wildcard = unity_s3.adapt_frame(self._entry(layout), catalog)
            self.assertTrue(wildcard.frame_wildcard, layout)
            self.assertEqual(wildcard.wildcard_reason, reason)
            self.assertFalse(wildcard.dynamic_target_definite)
        # 6. 类别未验证（有 S5 条目但 `class_verified=False`）→ class_word=None，全帧 noun 灰区。
        catalog_unverified = json.loads(json.dumps(catalog))
        catalog_unverified["objects"]["Vehicle_Taxi (1)"]["class_verified"] = False
        unverified = unity_s3.adapt_frame(self._entry("L1"), catalog_unverified)
        taxi = {o.object_id: o for o in unverified.objects}["Vehicle_Taxi (1)"]
        self.assertIsNone(taxi.class_word)
        self.assertEqual(three_state(unverified.objects, {"class": "taxi"}).state, "gray_uncertain_none")
        self.assertEqual(three_state(unverified.objects, {"class": "car"}).state, "gray_definite_plus_uncertain")
        # phantom 的类别来自 prefab 名而非 S5 记录，不受该字段影响。
        phantom_unverified = unity_s3.adapt_frame(self._entry("L9"), catalog_unverified)
        self.assertEqual(
            {o.object_id: o for o in phantom_unverified.objects}[synth.PHANTOM_ID].class_word, "taxi"
        )
        # 7. #27 匹配按实例名去后缀逐字相等：同 prefab 的 `(n)` 实例命中，异名不命中。
        self.assertEqual(unity_s3.instance_base("Vehicle_Bus_color03 (1)"), "Vehicle_Bus_color03")
        self.assertEqual(unity_s3.instance_base("Vehicle_Bus_color03"), "Vehicle_Bus_color03")
        self.assertEqual(unity_s3.instance_base("Vehicle_Bus_color03x"), "Vehicle_Bus_color03x")
        self.assertNotEqual(
            unity_s3.instance_base("Vehicle_Bus_color03x"), unity_s3.COLOR_COUNTEREXAMPLE_OBJECT
        )
        # 8. 目标车不在视野 → 不在执行域、无通配。
        absent = unity_s3.adapt_frame(self._entry("L1"), catalog)
        self.assertNotIn("dynamic-target", absent.object_ids())
        self.assertFalse(absent.frame_wildcard)

    def test_wildcard_frames_produce_no_samples(self) -> None:
        self.build()
        wildcard_frames = {
            entry["frame_id"]
            for entry in self.world["entries"]
            if unity_s3.wildcard_reason(entry) is not None
        }
        self.assertTrue(wildcard_frames)
        produced = {row["frame_id"] for row in self.read_jsonl(build.TRAIN_JSONL)}
        produced |= {row["frame_id"] for row in self.read_jsonl(build.EVAL_JSONL)}
        self.assertFalse(produced & wildcard_frames)


class ThreeStateTests(FixtureCase):
    def test_unique_class_equivalence_on_production_slice(self) -> None:
        """生产切片上 `UNIQUE_CLASS` ⇔ unique 且 M = {该对象}（§8 表 2 的等价关系）。"""
        catalog = self.world["field_catalog"]
        instructions = {
            (row["frame_id"], row["object_id"]): row["uniqueness_status"]
            for row in self.world["instructions"]
        }
        checked = 0
        for entry in self.world["entries"]:
            record = unity_s3.adapt_frame(entry, catalog)
            if record.frame_wildcard:
                continue
            for object_id in entry["referable"]:
                stored = catalog["objects"].get(object_id)
                if stored is None:
                    continue
                result = three_state(record.objects, {"class": stored["class"]})
                unique_self = result.state == "unique" and result.target_object_ids == (object_id,)
                self.assertEqual(
                    instructions[(entry["frame_id"], object_id)] == "UNIQUE_CLASS",
                    unique_self,
                    f"{entry['frame_id']} / {object_id}",
                )
                checked += 1
        self.assertGreater(checked, 100)


class SplitTests(FixtureCase):
    def test_quota_roundrobin_and_copies_are_deterministic(self) -> None:
        first = self.build()["dataset_manifest"]
        rows_first = self.read_jsonl(build.TRAIN_JSONL)
        second = synth.run_build(self.world)["dataset_manifest"]
        rows_second = self.read_jsonl(build.TRAIN_JSONL)
        self.assertEqual(rows_first, rows_second)
        self.assertEqual(first["steps"], second["steps"])
        steps = first["steps"]
        # E1：训练族闭集 = 七族去掉选层族；选层族只进选层集。
        self.assertEqual(steps["E1"]["selection_family"], build.SELECTION_FAMILY)
        families = {row["family"] for row in rows_first}
        self.assertNotIn(build.SELECTION_FAMILY, families)
        # E3/E4：配额与对象上限不被突破。
        self.assertTrue(all(count <= build.CLASS_QUOTA for count in steps["E3"]["per_class"].values()))
        self.assertTrue(
            all(count <= build.AMBIGUOUS_KEY_QUOTA for count in
                _counter(row["thin_key"] for row in rows_first if row["state"] == "ambiguous").values())
        )
        # E5：none 轮转按类别名字典序、每类 ≤ ⌈N/9⌉，实取 ≤ N_none。
        self.assertLessEqual(steps["E5"]["kept"], steps["E5"]["n_none_target"])
        self.assertTrue(
            all(count <= steps["E5"]["per_class_cap"] for count in steps["E5"]["per_class"].values())
        )
        # E6：复制系数写进 manifest，且逐行 `oversample_copies` 与之一致。
        copies = steps["E6"]["copies"]
        self.assertGreaterEqual(copies, 1)
        self.assertLessEqual(copies, build.COPY_MAX)
        for row in rows_first:
            self.assertEqual(row["oversample_copies"], copies if row["state"] == "ambiguous" else 1)
        self.assertEqual(
            steps["E7"]["multiset_samples"],
            sum(row["oversample_copies"] for row in rows_first),
        )

    def test_table_d_prime_stratum_key_hash_and_tie_order(self) -> None:
        make = _sample_factory
        # 层：< 32 S、< 64 M、≥ 64 L、无框 NA（短边 = min(w·640, h·480)）。
        self.assertEqual(build.stratum_of(31.9), "S")
        self.assertEqual(build.stratum_of(32.0), "M")
        self.assertEqual(build.stratum_of(64.0), "L")
        self.assertEqual(build.stratum_of(None), "NA")
        self.assertAlmostEqual(unity_s3.short_side_px([0, 0, 0.1, 0.1]), 48.0)
        # 键：unique → object_id；ambiguous → 候选升序 `|` 连接；none → surface。
        self.assertEqual(build.thin_key(make(state="unique", ids=("b",))), "b")
        self.assertEqual(build.thin_key(make(state="ambiguous", ids=("b", "a"))), "b|a")
        self.assertEqual(build.thin_key(make(state="none", ids=())), "the car")
        # 哈希：sha256(seed|frame_id|key)；并列次序 (h, frame_id, key, noun_type, surface)。
        sample = make(state="unique", ids=("b",))
        self.assertEqual(
            build.hash_of(sample),
            build._digest(build.SEED, sample.frame_id, "b"),
        )
        left = make(state="unique", ids=("b",), noun_type="class", surface="the car")
        right = make(state="unique", ids=("b",), noun_type="color", surface="the red car")
        self.assertEqual(build.hash_of(left), build.hash_of(right))
        self.assertLess(build.hash_order(left), build.hash_order(right))
        # E2 稀疏间隔：ambiguous 2、none 5、unique 弱类或 S 层 2、其余 5。
        self.assertEqual(build.gap_of(make(state="ambiguous", ids=("a", "b"))), 2)
        self.assertEqual(build.gap_of(make(state="none", ids=())), 5)
        self.assertEqual(build.gap_of(make(state="unique", ids=("a",), class_word="car")), 2)
        self.assertEqual(build.gap_of(make(state="unique", ids=("a",), class_word="bus", px=20)), 2)
        self.assertEqual(build.gap_of(make(state="unique", ids=("a",), class_word="bus", px=80)), 5)
        kept = build.thin(
            [make(state="unique", ids=("a",), class_word="bus", px=80, index=i) for i in range(12)]
        )
        self.assertEqual([s.frame_index for s in kept], [0, 5, 10])


class EvalSetTests(FixtureCase):
    def test_conservation_sums_to_405_and_keeps_per_row_gold(self) -> None:
        """守恒单位是原始 legacy `row_id`（真实输入为 405 条，夹具为其行数）。"""
        result = self.build()
        legacy_rows = json.loads(
            (self.world["probe_root"] / "manifest-default.json").read_text(encoding="utf-8")
        )["rows"]
        document = json.loads((self.root / build.LEGACY_CONSERVATION).read_text(encoding="utf-8"))
        self.assertEqual(len(document["rows"]), len(legacy_rows))
        self.assertEqual(document["totals"]["rows"], len(legacy_rows))
        self.assertEqual(
            {row["row_id"] for row in document["rows"]}, {row["row_id"] for row in legacy_rows}
        )
        eval_ids = {row["row_id"] for row in self.read_jsonl(build.EVAL_JSONL)}
        for row in document["rows"]:
            self.assertIn(row["disposition"], ("ADMITTED", "LEGACY_ONLY"))
            self.assertIsNotNone(row["eval_row_id"])
            self.assertIn(row["eval_row_id"], eval_ids)
        self.assertEqual(result["conservation"]["totals"]["rows"], len(legacy_rows))

    def test_g4_and_target_subgroups_in_same_selection(self) -> None:
        self.build()
        rows = self.read_jsonl(build.EVAL_JSONL)
        by_group = _group(rows)
        self.assertTrue(by_group["G4"], "G4 应由同一次试选产出")
        for row in by_group["G4"]:
            self.assertIn("relation_program", row)
            self.assertEqual(row["gold_state"], "unique")
            self.assertFalse(row["gate_row"])
        for group in ("G1t", "G2t", "G3t"):
            self.assertTrue(by_group[group], f"{group} 子组应单列")
            for row in by_group[group]:
                self.assertTrue(row["has_dynamic_target"])
                self.assertFalse(row["gate_row"])
        for row in by_group["G1"] + by_group["G2"] + by_group["G3"]:
            self.assertFalse(row["has_dynamic_target"])
            self.assertTrue(row["gate_row"])

    def test_admit_gap_legacy_priority_and_stratum_rotation(self) -> None:
        self.build()
        rows = self.read_jsonl(build.EVAL_JSONL)
        by_group = _group(rows)
        # 准入：同 (组, 键, 族) ≤ 4 行且帧序号间隔 ≥ 30。
        for group, group_rows in by_group.items():
            if group == build.LEGACY_ONLY_GROUP:
                continue  # LEGACY_ONLY 恰恰是被准入规则拒下来的行，不受同键上限约束
            buckets: dict[tuple, list[int]] = {}
            for row in group_rows:
                key = (group, _thin_key_of(row), row["family"])
                buckets.setdefault(key, []).append(row["frame_index"])
            for key, indices in buckets.items():
                self.assertLessEqual(len(indices), build.ADMIT_KEY_MAX, key)
                ordered = sorted(indices)
                for left, right in zip(ordered, ordered[1:]):
                    self.assertGreaterEqual(right - left, build.ADMIT_MIN_INDEX_GAP, key)
        # G5 每类 ≤ 12。
        counts = _counter(row["noun"]["class"] for row in by_group["G5"])
        self.assertTrue(all(value <= build.G5_CLASS_MAX for value in counts.values()), counts)
        # legacy 优先：有 legacy 的行先被准入（被拒的落 LEGACY_ONLY，不会消失）。
        conservation = json.loads(
            (self.root / build.LEGACY_CONSERVATION).read_text(encoding="utf-8")
        )["rows"]
        self.assertTrue(any(row["disposition"] == "ADMITTED" for row in conservation))
        # 层轮转：G5 全部为 NA 层；带框组的层取值落在闭集内。
        self.assertEqual({row["stratum"] for row in by_group["G5"]}, {"NA"})
        self.assertTrue({row["stratum"] for row in by_group["G1"]} <= set(build.STRATA_ORDER))

    def test_legacy_only_rows_carry_duplicate_key_probe_entries(self) -> None:
        self.build()
        rows = self.read_jsonl(build.EVAL_JSONL)
        legacy_only = [row for row in rows if row["group"] == build.LEGACY_ONLY_GROUP]
        self.assertTrue(legacy_only)
        for row in legacy_only:
            self.assertFalse(row["gate_row"])
            self.assertTrue(row["legacy_probe"])
            if row["gold_state"] is None:
                self.assertEqual(row["gold_boxes_norm_xywh"], [])
                self.assertIsNone(row["gold_text_len"])
        # 重复键：同一评估行承载两条 legacy 行，两条都留自己的 v1 gold。
        duplicates = [row for row in rows if len(row["legacy_probe"]) >= 2]
        self.assertTrue(duplicates, "夹具里有一对重复键 legacy 行")
        for row in duplicates:
            ids = [entry["row_id"] for entry in row["legacy_probe"]]
            self.assertEqual(len(ids), len(set(ids)))
            for entry in row["legacy_probe"]:
                self.assertIn("gold_v1_xywh", entry)
        total = sum(len(row["legacy_probe"]) for row in rows)
        legacy_rows = json.loads(
            (self.world["probe_root"] / "manifest-default.json").read_text(encoding="utf-8")
        )["rows"]
        self.assertEqual(total, len(legacy_rows))

    def test_leakage_assertions_fail_on_injected_test_frame(self) -> None:
        """把一帧 test 帧塞进训练族 → 泄漏断言必须失败（而不是静默通过）。"""
        self.build()
        report = json.loads((self.root / build.LEAKAGE_REPORT).read_text(encoding="utf-8"))
        self.assertEqual(report["train_select_cap_eval_frame_sha256"], [])
        self.assertTrue(report["assertions"]["train_select_disjoint_from_eval_by_sha"])

        # 注入：把训练族每一帧的字节换成某个评估帧的字节（S1 记录同步更新），
        # 于是「训练∪选层 ∩ 评估」在帧 SHA 上必然相交 —— 断言必须失败。
        eval_frame = self.read_jsonl(build.EVAL_JSONL)[0]["frame_id"]
        payload = (self.root / eval_frame).read_bytes()
        digest = __import__("hashlib").sha256(payload).hexdigest()
        inventory_path = self.root / "runtime/dist-data/inventory/attempt-2/inventory.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        train_family = "p1-vlm-survey-a2-p1-c1-s1"
        for record in inventory["payload"]["records"]:
            if f"/{train_family}/" in record["path"]:
                (self.root / record["path"]).write_bytes(payload)
                record["bytes"] = len(payload)
                record["sha256"] = digest
        inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
        with self.assertRaises(receipts.EngSftError) as raised:
            synth.run_build(self.world)
        self.assertEqual(raised.exception.reason, "CONSERVATION_MISMATCH")
        self.assertTrue(self.failure_receipts())

        # 同一帧同时落在两个 split 也是 fail-open 的口子：对账阶段直接拒绝。
        splits_path = self.root / "runtime/dist-data/splits/attempt-2/splits.json"
        document = json.loads(splits_path.read_text(encoding="utf-8"))
        document["payload"]["frames"]["train"].append(document["payload"]["frames"]["test"][0])
        splits_path.write_text(json.dumps(document), encoding="utf-8")
        expectations = synth.expectations(self.world)
        counts = dict(expectations.s4_frame_counts)
        counts["train"] += 1
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_build(
                repo_root=self.root,
                probe_root=self.world["probe_root"],
                local_root=self.local,
                expected=build.ReconcileExpectations(
                    s3_frames=expectations.s3_frames,
                    s3_shards=expectations.s3_shards,
                    s4_frame_counts=counts,
                    s5_objects=expectations.s5_objects,
                    s5_class_verified=expectations.s5_class_verified,
                    s5_dual_verified=expectations.s5_dual_verified,
                    instruction_rows=expectations.instruction_rows,
                ),
            )
        self.assertEqual(raised.exception.reason, "MANIFEST_COUNT_MISMATCH")

    def test_empty_key_group_fails_closed(self) -> None:
        """G1/G3/G5 任一为空 → `EVAL_GROUP_EMPTY`，不产出评估集。"""
        world = self.world
        entries = world["entries"]
        # 把 test 帧全部换成只含未知类别阻断体的布局：三态一律灰区，G1/G3/G5 皆空。
        test_frames = set(world["split_frames"]["test"])
        archive = self.root / "runtime/dist-data/frames_catalog/attempt-2"
        shard_meta = json.loads((archive / "frames_catalog.json").read_text(encoding="utf-8"))
        for shard in shard_meta["payload"]["shards"]:
            path = archive / shard["path"]
            with gzip.open(path, "rt") as handle:
                rows = [json.loads(line) for line in handle]
            for row in rows:
                if row["frame_id"] in test_frames:
                    for item in row["objects"]:
                        item["object_id"] = synth.UNKNOWN_BLOCKER
                        item["referable"] = False
                    row["referable"] = []
                    row["blocking"] = [synth.UNKNOWN_BLOCKER]
            with gzip.open(path, "wt", compresslevel=9) as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            data = path.read_bytes()
            shard["sha256"] = __import__("hashlib").sha256(data).hexdigest()
            shard["compressed_bytes"] = len(data)
        (archive / "frames_catalog.json").write_text(json.dumps(shard_meta), encoding="utf-8")
        expectations = synth.expectations(self.world)
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_build(
                repo_root=self.root,
                probe_root=self.world["probe_root"],
                local_root=self.local,
                expected=build.ReconcileExpectations(
                    s3_frames=expectations.s3_frames,
                    s3_shards=expectations.s3_shards,
                    s4_frame_counts=expectations.s4_frame_counts,
                    s5_objects=expectations.s5_objects,
                    s5_class_verified=expectations.s5_class_verified,
                    s5_dual_verified=expectations.s5_dual_verified,
                    instruction_rows=expectations.instruction_rows - _test_instruction_rows(world),
                ),
            )
        self.assertIn(raised.exception.reason, ("EVAL_GROUP_EMPTY", "HISTOGRAM_MISMATCH"))
        self.assertFalse((self.root / build.EVAL_MANIFEST).exists())


class BlindTests(FixtureCase):
    def test_blind_rows_have_no_gold_fields_and_package_relative_frame_path(self) -> None:
        self.build()
        gold_fields = {
            "gold_state",
            "gold_boxes_norm_xywh",
            "gold_bbox_2d_1000",
            "gold_text_len",
            "target_boxes_norm_xywh",
            "target_bbox_2d_1000",
            "state",
            "noun",
            "definite_ids",
            "legacy_probe",
        }
        for blind_name, source_name, key in (
            (build.EVAL_BLIND, build.EVAL_JSONL, "row_id"),
            (build.SELECT_EVAL_BLIND, build.SELECT_EVAL_JSONL, "sample_id"),
        ):
            blind = self.read_jsonl(blind_name)
            source = self.read_jsonl(source_name)
            self.assertEqual(len(blind), len(source))
            self.assertEqual([row["row_id"] for row in blind], [row[key] for row in source])
            for row in blind:
                self.assertEqual(set(row), {"row_id", "frame_path", "surface", "g4", "vocab"})
                self.assertFalse(set(row) & gold_fields)
                self.assertTrue(row["frame_path"].startswith("frames/"))
                self.assertTrue(row["frame_path"].endswith(".jpg"))
        # `frame_path` 在 build 时即写定为包内路径，且 SHA 取自 S1 记录。
        inventory = json.loads(
            (self.root / "runtime/dist-data/inventory/attempt-2/inventory.json").read_text("utf-8")
        )["payload"]["records"]
        index = {record["path"]: record["sha256"] for record in inventory}
        for row in self.read_jsonl(build.EVAL_JSONL):
            self.assertEqual(row["frame_path"], f"frames/{index[row['frame_id']]}.jpg")
            self.assertEqual(row["frame_sha256"], index[row["frame_id"]])
        # `smoke.jsonl` 由 build 产出并入 dataset-manifest。
        manifest = json.loads((self.root / build.DATASET_MANIFEST).read_text(encoding="utf-8"))
        smoke = self.read_jsonl(build.SMOKE_JSONL)
        self.assertEqual(manifest["smoke"]["rows"], len(smoke))
        self.assertEqual(len(smoke), 32)
        self.assertEqual(manifest["files"][build.SMOKE_JSONL]["lines"], 32)


class _ChainCase(FixtureCase):
    """build → plan → 代录 → precheck → 提交 → freeze → package 的完整链。"""

    def chain(self, *, wrong_panels=(), skip_precheck=False, commit=True):
        self.build()
        plan = label_audit.run_plan(repo_root=self.root, local_root=self.local)
        synth.write_unity_verdicts(self.root, plan, wrong_panels=wrong_panels)
        synth.copy_frozen_scripts(self.root)
        if not skip_precheck:
            directory, encode = synth.stub_tokenizer(self.root)
            original = build._load_tokenizer
            build._load_tokenizer = lambda path: (encode, {"library": "stub", "version": "0"})
            try:
                build.run_precheck(
                    repo_root=self.root, local_root=self.local, tokenizer_path=directory
                )
            finally:
                build._load_tokenizer = original
        if commit:
            synth.git_commit_all(self.root)
        return plan


class PrecheckTests(_ChainCase):
    def test_precheck_receipt_binds_gold_files_function_and_tokenizer(self) -> None:
        self.build()
        directory, encode = synth.stub_tokenizer(self.root)
        original = build._load_tokenizer
        build._load_tokenizer = lambda path: (encode, {"library": "stub", "version": "0"})
        try:
            document = build.run_precheck(
                repo_root=self.root, local_root=self.local, tokenizer_path=directory
            )
        finally:
            build._load_tokenizer = original
        self.assertEqual(set(document["gold_files"]), set(build.GOLD_FILES))
        for name, entry in document["gold_files"].items():
            path = self.local / build.DATA_DIRNAME / name
            self.assertEqual(entry["sha256"], receipts.sha256_file(path))
            self.assertIsNotNone(entry["token_max"])
        self.assertEqual(
            document["gold_function"]["source_sha256"], prompt_v2.gold_function_source_sha256()
        )
        self.assertEqual(document["tokenizer"]["revision"], build.TOKENIZER_REVISION)
        self.assertEqual(set(document["tokenizer"]["files"]), set(build.TOKENIZER_FILES))
        for name, entry in document["tokenizer"]["files"].items():
            self.assertEqual(entry["sha256"], receipts.sha256_file(directory / name))
        self.assertEqual(document["counting"], {"add_special_tokens": False, "chat_template_applied": False})
        self.assertIn("assistant_header", document["template_overhead_tokens"])
        self.assertLessEqual(document["observed_token_max"], build.GOLD_TOKEN_MAX)
        # 灰区/LEGACY_ONLY 行没有 gold，不进预检，只披露计数。
        self.assertGreater(document["gold_files"][build.EVAL_JSONL]["rows_without_gold"], 0)

    def test_overflow_is_refused_without_truncation(self) -> None:
        self.build()
        directory, _encode = synth.stub_tokenizer(self.root)
        original = build._load_tokenizer
        build._load_tokenizer = lambda path: (lambda text: len(text) * 2, {"library": "stub", "version": "0"})
        try:
            with self.assertRaises(receipts.EngSftError) as raised:
                build.run_precheck(
                    repo_root=self.root, local_root=self.local, tokenizer_path=directory
                )
        finally:
            build._load_tokenizer = original
        self.assertEqual(raised.exception.reason, "GOLD_TOKEN_OVERFLOW")
        self.assertFalse((self.local / receipts.RECEIPTS_DIRNAME / build.PRECHECK_RECEIPT_NAME).exists())


class FreezeTests(_ChainCase):
    def test_dirty_or_untracked_frozen_file_is_refused(self) -> None:
        self.chain()
        build.run_freeze(repo_root=self.root, local_root=self.local)  # 干净时可冻结
        (self.root / build.DATASET_MANIFEST).write_text("{}\n", encoding="utf-8")
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "FROZEN_FILE_DIRTY")
        # 未跟踪同样拒绝（把一份冻结 JSON 移出索引，内容仍在工作区）。
        synth.git_commit_all(self.root, "restore")
        synth.git_untrack(self.root, build.EVAL_MANIFEST.as_posix())
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "FROZEN_FILE_DIRTY")

    def test_freeze_requires_complete_audit_and_precheck_receipt(self) -> None:
        # 1. 无预检收据 → 拒绝。
        self.chain(skip_precheck=True)
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "FROZEN_SET_MISMATCH")
        # 2. 用户份额未判定齐全 → `AUDIT_INCOMPLETE`。
        plan = json.loads((self.local / receipts.RECEIPTS_DIRNAME / "audit-plan.json").read_text("utf-8"))
        synth.write_unity_verdicts(self.root, plan, state="PENDING")
        directory, encode = synth.stub_tokenizer(self.root)
        original = build._load_tokenizer
        build._load_tokenizer = lambda path: (encode, {"library": "stub", "version": "0"})
        try:
            build.run_precheck(repo_root=self.root, local_root=self.local, tokenizer_path=directory)
        finally:
            build._load_tokenizer = original
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "AUDIT_INCOMPLETE")
        # 3. 判定齐全且无「错」→ 冻结收据成立，绑定 HEAD 与冻结闭集。
        synth.write_unity_verdicts(self.root, plan)
        document = build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(len(document["head"]), 40)
        self.assertEqual(
            set(document["frozen_set"]),
            {path.as_posix() for path in build.FROZEN_JSON_FILES + build.FROZEN_SCRIPT_FILES},
        )
        self.assertEqual(
            document["jsonl"][build.TRAIN_JSONL]["sha256"],
            receipts.sha256_file(self.local / build.DATA_DIRNAME / build.TRAIN_JSONL),
        )
        # 3b. C1-4：预检收据的绑定成员必须是合同闭集——删掉一条绑定即拒绝冻结。
        precheck_path = self.local / receipts.RECEIPTS_DIRNAME / build.PRECHECK_RECEIPT_NAME
        original_precheck = precheck_path.read_text(encoding="utf-8")
        for drop in (("gold_files", build.SELECT_EVAL_JSONL), ("tokenizer", "merges.txt")):
            document = json.loads(original_precheck)
            if drop[0] == "gold_files":
                document["gold_files"].pop(drop[1])
            else:
                document["tokenizer"]["files"].pop(drop[1])
            precheck_path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(receipts.EngSftError) as raised:
                build.run_freeze(repo_root=self.root, local_root=self.local)
            self.assertEqual(raised.exception.reason, "FROZEN_SET_MISMATCH", drop)
        precheck_path.write_text(original_precheck, encoding="utf-8")
        # 3c. C1-4：被绑定的 gold 文件缺失时按合同记收据，不抛原生异常
        # （AC-5 修订 1：缺收据 = FROZEN_SET_MISMATCH，已绑定输入变化 = INPUT_HASH_CHANGED）。
        gold_path = self.local / build.DATA_DIRNAME / build.SELECT_EVAL_JSONL
        gold_bytes = gold_path.read_bytes()
        gold_path.unlink()
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "INPUT_HASH_CHANGED")
        gold_path.write_bytes(gold_bytes)
        # 盲文件不在预检绑定里，缺失按「冻结集不全」拒绝。
        blind_path = self.local / build.DATA_DIRNAME / build.SELECT_EVAL_BLIND
        blind_bytes = blind_path.read_bytes()
        blind_path.unlink()
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "FROZEN_SET_MISMATCH")
        blind_path.write_bytes(blind_bytes)
        # 3d. 关注项 2：六份 jsonl 的 SHA 必须等于已提交 manifest 记录值。
        manifest_path = self.root / build.DATASET_MANIFEST
        original_manifest = manifest_path.read_text(encoding="utf-8")
        document = json.loads(original_manifest)
        document["files"][build.TRAIN_JSONL]["sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        synth.git_commit_all(self.root, "tampered manifest")  # 提交后冻结闭集是干净的
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "FROZEN_SET_MISMATCH")
        manifest_path.write_text(original_manifest, encoding="utf-8")
        synth.git_commit_all(self.root, "restore manifest")
        build.run_freeze(repo_root=self.root, local_root=self.local)
        # 4. 预检收据过期（gold 文件字节变了）→ `INPUT_HASH_CHANGED`。
        path = self.local / build.DATA_DIRNAME / build.TRAIN_JSONL
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_freeze(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "INPUT_HASH_CHANGED")


class PackageTests(_ChainCase):
    def test_data_package_excludes_code_gold_and_forbidden_files(self) -> None:
        self.chain()
        build.run_freeze(repo_root=self.root, local_root=self.local)
        build.run_package(repo_root=self.root, local_root=self.local)
        upload = self.local / build.UPLOAD_DIRNAME
        names = {path.relative_to(upload).as_posix() for path in upload.rglob("*") if path.is_file()}
        self.assertIn(f"data/{build.TRAIN_JSONL}", names)
        self.assertIn(f"data/{build.SMOKE_JSONL}", names)
        self.assertIn(f"data/{build.EVAL_BLIND}", names)
        self.assertIn("manifests/dataset-manifest.json", names)
        self.assertIn("manifest.json", names)
        # 不含代码、不含 gold 评估文件、不含 legacy/ 与泄漏报告。
        self.assertFalse([name for name in names if name.endswith(".py")])
        self.assertNotIn(f"data/{build.EVAL_JSONL}", names)
        self.assertNotIn(f"data/{build.SELECT_EVAL_JSONL}", names)
        self.assertFalse([name for name in names if name.startswith("legacy/")])
        self.assertFalse([name for name in names if "leakage-report" in name])
        self.assertFalse([name for name in names if "legacy-conservation" in name])
        self.assertFalse([name for name in names if name.endswith("audit-j7-candidates.jsonl")])
        # 打包不改任何 jsonl 字节。
        for name in build.PACKAGE_DATA_FILES:
            self.assertEqual(
                receipts.sha256_file(upload / "data" / name),
                receipts.sha256_file(self.local / build.DATA_DIRNAME / name),
            )

    def test_failed_package_leaves_previous_package_intact(self) -> None:
        """C2-1：打包失败不得毁掉已有的包——先校验、暂存成包、最后原子替换。"""
        self.chain()
        build.run_freeze(repo_root=self.root, local_root=self.local)
        build.run_package(repo_root=self.root, local_root=self.local)
        upload = self.local / build.UPLOAD_DIRNAME
        good = {
            path.relative_to(upload).as_posix(): receipts.sha256_file(path)
            for path in upload.rglob("*")
            if path.is_file()
        }
        self.assertTrue(good)
        # 让某份 data 成员与冻结收据不符（模拟冻结后被改动）。
        train = self.local / build.DATA_DIRNAME / build.TRAIN_JSONL
        original = train.read_bytes()
        train.write_bytes(original + b"{}\n")
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_package(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "PACKAGE_INCOMPLETE")
        after = {
            path.relative_to(upload).as_posix(): receipts.sha256_file(path)
            for path in upload.rglob("*")
            if path.is_file()
        }
        self.assertEqual(good, after)  # 旧包逐文件字节不变
        self.assertFalse((upload.parent / f"{upload.name}.staging").exists())  # 暂存目录已清
        train.write_bytes(original)

    def test_package_requires_freeze_receipt_and_lists_every_member_with_transport_map(self) -> None:
        self.chain()
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_package(repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "PACKAGE_INCOMPLETE")
        build.run_freeze(repo_root=self.root, local_root=self.local)
        document = build.run_package(repo_root=self.root, local_root=self.local)
        upload = self.local / build.UPLOAD_DIRNAME
        manifest = json.loads((upload / "manifest.json").read_text(encoding="utf-8"))
        on_disk = {
            path.relative_to(upload).as_posix()
            for path in upload.rglob("*")
            if path.is_file() and path.name != "manifest.json"
        }
        self.assertEqual(set(manifest["members"]), on_disk)  # 逐文件列出，且不含自身
        self.assertNotIn("manifest.json", manifest["members"])
        for name, entry in manifest["members"].items():
            self.assertEqual(entry["sha256"], receipts.sha256_file(upload / name))
        # 帧运输映射：包内路径 → **全部**源 frame_id（字节相同的帧合并成一个文件，
        # 映射必须逐个列出这些源帧，不能只留一个），文件名就是该帧字节的 SHA。
        frames = {name for name in manifest["members"] if name.startswith("frames/")}
        self.assertEqual(set(manifest["frame_transport_map"]), frames)
        source_ids = set()
        for package_path, frame_ids in manifest["frame_transport_map"].items():
            self.assertIsInstance(frame_ids, list)
            self.assertTrue(frame_ids)
            for frame_id in frame_ids:
                self.assertEqual(
                    Path(package_path).stem, receipts.sha256_file(self.root / frame_id)
                )
                source_ids.add(frame_id)
        self.assertEqual(manifest["frame_files"], len(frames))
        self.assertEqual(manifest["source_frame_ids"], len(source_ids))
        # 三份 jsonl 引用到的每个源帧都在映射里。
        referenced = set()
        for name in (build.TRAIN_JSONL, build.SELECT_EVAL_JSONL, build.EVAL_JSONL):
            for row in self.read_jsonl(name):
                referenced.add(row["frame_id"])
        self.assertEqual(source_ids, referenced)
        self.assertEqual(document["member_count"], len(manifest["members"]))
        self.assertEqual(
            document["upload_manifest_sha256"], receipts.sha256_file(upload / "manifest.json")
        )


class WriteBoundaryTests(FixtureCase):
    def test_package_entry_guards_forbidden_root_before_touching_it(self) -> None:
        """C1-5：`package` 在删目录/复制之前先守边界，不是最后写收据时才拒。"""
        self.build()
        forbidden = self.root / "runtime/dist-data/attempt-2-local"
        (forbidden / build.UPLOAD_DIRNAME).mkdir(parents=True, exist_ok=True)
        canary = forbidden / build.UPLOAD_DIRNAME / "canary.txt"
        canary.write_text("keep", encoding="utf-8")
        (forbidden / receipts.RECEIPTS_DIRNAME).mkdir(parents=True, exist_ok=True)
        (forbidden / receipts.RECEIPTS_DIRNAME / build.FREEZE_RECEIPT_NAME).write_text(
            json.dumps({"jsonl": {}}), encoding="utf-8"
        )
        with self.assertRaises(receipts.EngSftError) as raised:
            build.run_package(repo_root=self.root, local_root=forbidden)
        self.assertEqual(raised.exception.reason, "OUTPUT_PATH_FORBIDDEN")
        self.assertTrue(canary.is_file())  # 禁写根下的既有内容一个字节没动
        self.assertEqual(canary.read_text(encoding="utf-8"), "keep")

    def test_output_inside_forbidden_roots_is_refused(self) -> None:
        for relative in (
            "runtime/dist-data/attempt-2/x.json",
            "runtime/frames/x.jpg",
            "runtime/frames.arm-a-trial-1-void-attempt-1-hold/x.jpg",
            "runtime/eng-asset/P1-ENG-ASSET-001/x.json",
            "outputs/eng-asset/P1-ENG-ASSET-001/x.json",
            "outputs/eng-sft3/x.json",
            "tools/eng_asset/x.py",
            "tools/dist_data/x.py",
            "controller/x.py",
            "Assets/x.meta",
            "config/x.json",
            "runtime/body_command.json",
            "runtime/metrics.json",
        ):
            with self.assertRaises(receipts.EngSftError, msg=relative) as raised:
                receipts.assert_output_allowed(PROJECT_ROOT / relative)
            self.assertEqual(raised.exception.reason, "OUTPUT_PATH_FORBIDDEN")
        for relative in (
            "outputs/eng-sft/P1-ENG-SFT-002/data/train.jsonl",
            "outputs/eng-sft/tokenizer/x/tokenizer.json",
            "docs/evidence/P1-ENG-SFT-002-dataset-manifest.json",
        ):
            receipts.assert_output_allowed(PROJECT_ROOT / relative)

    def test_no_controller_imports(self) -> None:
        for path in sorted((PROJECT_ROOT / "tools/eng_sft").rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("import controller", source, path.name)
            self.assertNotIn("from controller", source, path.name)
            self.assertNotIn("tools.dist_data.artifacts", source, path.name)

    def test_directory_caps_split_by_root(self) -> None:
        self.build()
        report = build.directory_caps(self.root, self.local)
        self.assertEqual(set(report), {"data", "upload", "panel", "tokenizer"})
        self.assertEqual(report["data"]["cap_bytes"], 64 * 1024 * 1024)
        self.assertEqual(report["upload"]["cap_bytes"], 300 * 1024 * 1024)
        self.assertEqual(report["panel"]["cap_bytes"], 20 * 1024 * 1024)
        self.assertEqual(report["tokenizer"]["cap_bytes"], 20 * 1024 * 1024)
        self.assertTrue(all(entry["within_cap"] for entry in report.values()))
        self.assertGreater(report["data"]["bytes"], 0)
        # 受版本控制的 A2 工件各 ≤ 2 MB。
        for path in build.FROZEN_JSON_FILES:
            self.assertLessEqual((self.root / path).stat().st_size, build.VERSIONED_FILE_MAX_BYTES)


def _test_instruction_rows(world) -> int:
    test_frames = set(world["split_frames"]["test"])
    return sum(1 for row in world["instructions"] if row["frame_id"] in test_frames)


def _counter(values):
    counts: dict = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _group(rows):
    buckets: dict = {}
    for row in rows:
        buckets.setdefault(row["group"], []).append(row)
    return {group: buckets.get(group, []) for group in build.GROUP_ORDER + (build.LEGACY_ONLY_GROUP,)}


def _thin_key_of(row) -> str:
    if row["gold_state"] == "unique" and row["target_object_ids"]:
        return row["target_object_ids"][0]
    if row["gold_state"] == "ambiguous":
        return "|".join(row["target_object_ids"])
    if row["group"] == "G4":
        return row["definite_ids"][0]
    return row["surface"]


def _sample_factory(
    *, state, ids, noun_type="class", surface="the car", class_word="car", px=100.0, index=0
):
    return build.Sample(
        frame_id="runtime/frames.fixture/m/frame_0000000001.jpg",
        family="m3-armA",
        frame_index=index,
        split="dev",
        noun_type=noun_type,
        surface=surface,
        noun={"class": class_word},
        program=None,
        class_word=class_word,
        state=state,
        target_ids=tuple(ids),
        boxes=(),
        px=px,
        color_required=None,
        has_dynamic_target=False,
    )


if __name__ == "__main__":
    unittest.main()
