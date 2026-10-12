"""P1-ENG-ASSET-001 AC-1/2/3/6：对账、字段清单、指令候选与写出边界。

夹具由**生产路径**产出：迷你 attempt 用 `tools.dist_data.artifacts.ArtifactStore`
（S1–S5 的真实写入器）写进临时根，指令语义再由既有
`build_catalog.minimal_program_with_reference` 独立复算比对，不手写 JSON 造状态。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import build_catalog, tier1_lang  # noqa: E402
from tools.dist_data.artifacts import ArtifactStore  # noqa: E402
from tools.eng_asset import inventory, receipts  # noqa: E402

ATTEMPT = "attempt-t1"

BUS = "Vehicle_Bus_color03"
CAR_RED = "Vehicle_Car_color01"
CAR_GREY = "Vehicle_Car_color03"
CAR_RED2 = "Vehicle_Car_color02"
CAR_BLUE = "Vehicle_Car_color04"
TAXI = "Vehicle_Taxi_color01"
UNVERIFIED_CLASS = "Vehicle_Truck_color01"
# S5 目录里**根本没有条目**的布局车：`frame_world` 走 `elif record is None` 分支，
# class_word=None，按通配语义阻断同帧其他车的唯一性（AC-3 修订 3 的真实成因）。
NO_S5_ENTRY = "Vehicle_SUV_color03 (2)"
DYNAMIC = build_catalog.TARGET_BLOCKER_ID


def s5_objects() -> dict[str, dict]:
    return {
        BUS: {
            "object_id": BUS,
            "class": "bus",
            "class_verified": True,
            "color": "gray",
            "color_status": "VERIFIED",
            "group_key": "bus|color03",
            "dynamic_state": "static",
            "relocated": False,
        },
        CAR_RED: {
            "object_id": CAR_RED,
            "class": "car",
            "class_verified": True,
            "color": "red",
            "color_status": "VERIFIED",
            "group_key": "car|color01",
            "dynamic_state": "static",
            "relocated": False,
        },
        CAR_GREY: {
            "object_id": CAR_GREY,
            "class": "car",
            "class_verified": True,
            "color": None,
            "color_status": "UNVERIFIED",
            "color_downgrade_reason": "GROUP_INCONSISTENT",
            "group_key": "car|color03",
            "dynamic_state": "static",
            "relocated": False,
        },
        CAR_RED2: {
            "object_id": CAR_RED2,
            "class": "car",
            "class_verified": True,
            "color": "red",
            "color_status": "VERIFIED",
            "group_key": "car|color02",
            "dynamic_state": "static",
            "relocated": False,
        },
        CAR_BLUE: {
            "object_id": CAR_BLUE,
            "class": "car",
            "class_verified": True,
            "color": "blue",
            "color_status": "VERIFIED",
            "group_key": "car|color04",
            "dynamic_state": "static",
            "relocated": False,
        },
        TAXI: {
            "object_id": TAXI,
            "class": "taxi",
            "class_verified": True,
            "color": "yellow",
            "color_status": "VERIFIED",
            "group_key": "taxi|color01",
            "dynamic_state": "static",
            "relocated": False,
        },
        UNVERIFIED_CLASS: {
            "object_id": UNVERIFIED_CLASS,
            "class": None,
            "class_verified": False,
            "color": None,
            "color_status": "UNVERIFIED",
            "group_key": "truck|color01",
            "dynamic_state": "static",
            "relocated": False,
        },
    }


def obj(
    object_id: str,
    *,
    x: float = 0.2,
    side: float = 0.2,
    phantom: bool = False,
    referable: bool = True,
    status: str | None = None,
) -> dict:
    left, top = x * 640.0, 0.3 * 480.0
    width, height = side * 640.0, side * 480.0
    return {
        "object_id": object_id,
        "is_phantom": phantom,
        "referable": referable,
        "status": status or ("OK" if referable else "PHANTOM"),
        "blocks": True,
        "visible_px": [left, top, left + width, top + height],
        "visible_norm_xywh": [left / 640.0, top / 480.0, width / 640.0, height / 480.0],
        "amodal_px": None,
        "camera_depth_m": 20.0,
        "exposure": "occluder_only",
    }


def frame(
    frame_id: str,
    objects: list[dict],
    *,
    usage_class: str = "VALID_SURVEY",
    family: str = "fam-a",
    layout_class: str = "default",
    target_source_bound: bool = True,
    with_dynamic: bool = False,
    layout_binding_valid: bool = True,
    sidecar_complete: bool = True,
) -> dict:
    blocking = [item["object_id"] for item in objects]
    if with_dynamic:
        blocking.append(DYNAMIC)
    return {
        "frame_id": frame_id,
        "family": family,
        "layout_class": layout_class,
        "usage_class": usage_class,
        "layout_binding_valid": layout_binding_valid,
        "sidecar_complete": sidecar_complete,
        "objects": objects,
        "blocking": blocking,
        "referable": [item["object_id"] for item in objects if item["referable"] and not item["is_phantom"]],
        "co_visible_count": len(objects),
        "station_bin": {"key": "1:1:1:1", "x_bin": 1, "z_bin": 1, "azimuth_bin": 1, "elevation_band": 1},
        "status_histogram": {"OK": len(objects)},
        "target_blocker_px": [100.0, 100.0, 140.0, 140.0] if with_dynamic else None,
        "target_fields": {"class": "car", "color": "red"},
        "target_source_bound": target_source_bound,
        "target_sweep_area_px2": None,
        "target_unbounded": False,
    }


FRAMES: list[dict] = [
    # 单一车：class-only 唯一。
    frame("runtime/frames.fx/frame_0000000001.jpg", [obj(BUS)]),
    # 同类两车：红车颜色已验证但灰车颜色未验证（通配冲突）——红车判 AMBIGUOUS_SAME_CLASS、灰车判 COLOR_UNVERIFIED（表 C 第 6/7 行）。
    frame("runtime/frames.fx/frame_0000000002.jpg", [obj(CAR_RED, x=0.1), obj(CAR_GREY, x=0.6)]),
    # 未绑定动态目标：类别 UNKNOWN 通配阻断。
    frame(
        "runtime/frames.fx/frame_0000000003.jpg",
        [obj(CAR_RED, x=0.1)],
        target_source_bound=False,
        with_dynamic=True,
    ),
    # 幻影是别的类别：不得阻断已知类别的唯一性。
    frame(
        "runtime/frames.fx/frame_0000000004.jpg",
        [obj(CAR_RED, x=0.1), obj(f"phantom:{BUS}@1", x=0.7, phantom=True, referable=False)],
    ),
    # 类别未验证的对象。
    frame("runtime/frames.fx/frame_0000000005.jpg", [obj(UNVERIFIED_CLASS), obj(TAXI, x=0.7)]),
    # 小目标（短边 < 32 px）与 test split 的重叠对象。
    frame("runtime/frames.fx/frame_0000000006.jpg", [obj(BUS, x=0.5, side=0.03)], family="fam-b"),
    frame("runtime/frames.fx/frame_0000000007.jpg", [obj(TAXI, x=0.2)], family="fam-b"),
    # N1：同类两车颜色均已验证且不同 → class-only 不唯一、class+color 唯一（表 C 第 3 行）。
    frame(
        "runtime/frames.fx/frame_0000000010.jpg",
        [obj(CAR_RED, x=0.1), obj(CAR_BLUE, x=0.6)],
        family="fam-b",
    ),
    # N1：同类同色两车 + 唯一可指称参照 → 只能靠静态关系消歧（表 C 第 4 行）。
    frame(
        "runtime/frames.fx/frame_0000000011.jpg",
        [obj(CAR_RED, x=0.05), obj(CAR_RED2, x=0.80), obj(BUS, x=0.45)],
        family="fam-b",
    ),
    # AC-3 修订 3：blocking 含无 S5 条目的非幻影布局车 → 同帧可指称车判 WILDCARD。
    frame(
        "runtime/frames.fx/frame_0000000009.jpg",
        [obj(CAR_RED, x=0.1), obj(NO_S5_ENTRY, x=0.7, referable=False, status="TOO_SMALL")],
        family="fam-b",
    ),
    # 域外行：不入对账域，也不入指令逐行文件。
    frame(
        "runtime/frames.fx/frame_0000000008.jpg",
        [obj(BUS)],
        layout_binding_valid=False,
    ),
]

SPLIT_OF = {
    "runtime/frames.fx/frame_0000000001.jpg": "train",
    "runtime/frames.fx/frame_0000000002.jpg": "train",
    "runtime/frames.fx/frame_0000000003.jpg": "dev",
    "runtime/frames.fx/frame_0000000004.jpg": "dev",
    "runtime/frames.fx/frame_0000000005.jpg": "test",
    "runtime/frames.fx/frame_0000000006.jpg": "test",
    "runtime/frames.fx/frame_0000000007.jpg": "test",
}

EXPECTED = {
    "frames_catalog": {"frame_count": len(FRAMES), "shards": 1},
    "splits": {
        "train": sum(1 for v in SPLIT_OF.values() if v == "train"),
        "dev": sum(1 for v in SPLIT_OF.values() if v == "dev"),
        "test": sum(1 for v in SPLIT_OF.values() if v == "test"),
        "d3": 0,
        "shards": 1,
    },
    "field_catalog": {"objects": len(s5_objects()), "vehicles": len(s5_objects()), "dual_verified": 3},
}


def build_fixture(root: Path) -> None:
    """用生产写入器 `ArtifactStore` 造迷你 attempt（临时根，非仓库工件）。"""
    store = ArtifactStore(root, root=".")
    store.write("contract", ATTEMPT, {"stage": 0, "note": "fixture"}, stage=0)
    store.write(
        "inventory",
        ATTEMPT,
        {
            "stage": 1,
            "record_count": len(FRAMES),
            "image_count": len(FRAMES),
            "records": [
                {
                    "path": entry["frame_id"],
                    "kind": "image",
                    "decision": "INCLUDED",
                    "sha256": "0" * 64,
                    "bytes": 1,
                }
                for entry in FRAMES
            ],
        },
        stage=1,
    )
    store.write(
        "layout",
        ATTEMPT,
        {
            "stage": 2,
            "scenario_partitions": {
                "fixture|hash": {
                    "binding_status": "BOUND",
                    "family": "fam-a",
                    "layout_class": "default",
                    "instances": [
                        {"scene_object_name": name, "classification": "ground-obstacle", "group": "vehicle"}
                        # N1：布局里含一辆 S5 无条目的车，使 fields 走 NO_S5_ENTRY/UNUSABLE 分支。
                        for name in (*s5_objects(), NO_S5_ENTRY)
                    ],
                }
            },
            "families": {},
        },
        stage=2,
    )
    store.write_composite(
        "frames_catalog",
        ATTEMPT,
        {
            "stage": 3,
            "frame_count": len(FRAMES),
            "skipped_invalid_frames": 0,
            "skipped_unbound_frames": 0,
        },
        iter(FRAMES),
        stage=3,
    )
    splits_frames = {name: [] for name in ("train", "dev", "test", "d3")}
    for frame_id, split in SPLIT_OF.items():
        splits_frames[split].append(frame_id)
    store.write_composite(
        "splits",
        ATTEMPT,
        {
            "stage": 4,
            "frames": splits_frames,
            "frame_counts": {name: len(value) for name, value in splits_frames.items()},
            "dropped_frames": [entry["frame_id"] for entry in FRAMES if entry["frame_id"] not in SPLIT_OF],
            "held_out_objects": {"held_out_object_ids": [TAXI], "class_sizes": {"taxi": 1}},
        },
        iter([{"frame_id": frame_id, "split": split} for frame_id, split in sorted(SPLIT_OF.items())]),
        stage=4,
    )
    store.write(
        "field_catalog",
        ATTEMPT,
        {
            "stage": 5,
            "objects": s5_objects(),
            "dual_verified_object_ids": [BUS, CAR_RED, TAXI],
            "verified_color_vocabulary": ["blue", "gray", "green", "purple", "red", "yellow"],
            "groups": {},
        },
        stage=5,
    )


class FixtureCase(unittest.TestCase):
    """每个用例一份临时 attempt 与临时输出根；不触碰仓库原件。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.artifacts = self.root / "dist-data"
        self.local = self.root / "local"
        self.evidence = self.root / "evidence"
        build_fixture(self.artifacts)
        self.addCleanup(self._tmp.cleanup)

    def run_inventory(self) -> dict:
        return inventory.run(
            root=self.artifacts,
            attempt=ATTEMPT,
            repo_root=self.root,
            local_root=self.local,
            evidence_dir=self.evidence,
            expected=EXPECTED,
        )

    def instruction_rows(self, result: dict | None = None) -> list[dict]:
        if result is None:
            self.run_inventory()
        import gzip

        with gzip.open(self.local / "instructions.ndjson.gz", "rt", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle]


class ReconciliationTests(FixtureCase):
    def test_shard_hash_mismatch_writes_failure_receipt_only(self) -> None:
        shard = next((self.artifacts / "frames_catalog" / ATTEMPT / "shards").glob("*.ndjson.gz"))
        shard.write_bytes(shard.read_bytes() + b"\x00")

        with self.assertRaises(receipts.ShardHashMismatch):
            self.run_inventory()

        failures = list((self.local / "receipts").glob("failure-inventory-*.json"))
        self.assertEqual(len(failures), 1, "分片哈希不符必须留且只留失败收据")
        document = json.loads(failures[0].read_text(encoding="utf-8"))
        self.assertEqual(document["reason"], "SHARD_HASH_MISMATCH")
        self.assertFalse(list((self.local / "receipts").glob("run-inventory-*.json")))
        self.assertFalse((self.local / "instructions.ndjson.gz").exists())
        self.assertFalse(self.evidence.exists() and list(self.evidence.iterdir()))

    def test_input_manifest_reverified_after_run(self) -> None:
        self.run_inventory()
        document = json.loads((self.local / "receipts" / "input-manifest.json").read_text(encoding="utf-8"))
        stage = document["stages"]["inventory"]
        self.assertTrue(stage["equal"])
        self.assertEqual(stage["before"], stage["after"])
        self.assertTrue(stage["successful"])
        self.assertIn("union", document)

        # 同一机制对被改动的输入必须报不符（INPUT_HASH_CHANGED 的判据）。
        manifest = receipts.InputManifest(repo_root=self.root)
        target = self.artifacts / "field_catalog" / ATTEMPT / "field_catalog.json"
        manifest.record(target, source="首次读取现算")
        target.write_bytes(target.read_bytes() + b" ")
        self.assertTrue(manifest.diff(manifest.recompute()))


class FieldTableTests(FixtureCase):
    def test_object_table_sums_match_s3_referable_counts(self) -> None:
        result = self.run_inventory()
        rows = self.instruction_rows(result)
        fields = result["fields"]

        expected_pairs = {}
        expected_frames = 0
        for entry in FRAMES:
            if not (entry["layout_binding_valid"] and entry["sidecar_complete"]):
                continue
            expected_frames += 1
            split = SPLIT_OF.get(entry["frame_id"], inventory.UNASSIGNED)
            expected_pairs[split] = expected_pairs.get(split, 0) + len(entry["referable"])

        bucket_pairs: dict[str, int] = {}
        for bucket in fields["buckets"]:
            bucket_pairs[bucket["split"]] = bucket_pairs.get(bucket["split"], 0) + bucket["frame_vehicle_pairs"]
        self.assertEqual(bucket_pairs, expected_pairs)
        self.assertEqual(fields["domain"]["frames"], expected_frames)
        self.assertEqual(fields["domain"]["frame_vehicle_pairs"], sum(expected_pairs.values()))
        self.assertEqual(len(rows), sum(expected_pairs.values()), "指令逐行文件行数 = 各行 referable 之和")

        per_object = {row["object_id"]: row for row in fields["layout_vehicles"]}
        self.assertEqual(set(per_object), set(s5_objects()) | {NO_S5_ENTRY})
        for object_id, row in per_object.items():
            counted = sum(1 for item in rows if item["object_id"] == object_id)
            self.assertEqual(row["ok_frames_total"], counted, object_id)
        missing = [row for row in fields["layout_vehicles"] if not row["s5_entry"]]
        self.assertEqual([row["object_id"] for row in missing], [NO_S5_ENTRY])
        self.assertEqual(missing[0]["usability"], "UNUSABLE")
        self.assertEqual(missing[0]["usability_reason"], "NO_S5_ENTRY")
        classification = {(item["field"], item["classification"]): item["count"]
                          for item in fields["field_classification"]}
        self.assertEqual(classification[("布局车（无 S5 条目）", "UNUSABLE")], 1)


class InstructionTests(FixtureCase):
    def test_status_derivation_matches_minimal_program_on_production_slice(self) -> None:
        result = self.run_inventory()
        rows = self.instruction_rows(result)
        catalog = {entry["frame_id"]: entry for entry in FRAMES}
        field_catalog = {
            "objects": s5_objects(),
            "dual_verified_object_ids": [],
            "verified_color_vocabulary": [],
        }
        self.assertTrue(rows)
        for row in rows:
            world = build_catalog.frame_world(catalog[row["frame_id"]], field_catalog)
            outcome = build_catalog.minimal_program_with_reference(
                world, row["object_id"], field_catalog
            )
            if outcome is None:
                self.assertEqual(row["uniqueness_status"], inventory.STATUS_NOT_CLASS_VERIFIED)
                self.assertIsNone(row["program"])
                self.assertIsNone(row["surface"])
                continue
            program, reference = outcome
            self.assertEqual(row["program"], program)
            self.assertEqual(row["resolved_reference_object_id"], reference)
            if program is None:
                self.assertIn(
                    row["uniqueness_status"],
                    {
                        inventory.STATUS_WILDCARD_UNKNOWN_CLASS,
                        inventory.STATUS_COLOR_UNVERIFIED,
                        inventory.STATUS_AMBIGUOUS_SAME_CLASS,
                    },
                )
                self.assertIsNone(row["surface"])
            else:
                self.assertEqual(row["surface"], tier1_lang.render(program))
                if "relation" in program:
                    self.assertEqual(row["uniqueness_status"], inventory.STATUS_UNIQUE_RELATION)
                elif "color" in program["target"]:
                    self.assertEqual(row["uniqueness_status"], inventory.STATUS_UNIQUE_CLASS_COLOR)
                else:
                    self.assertEqual(row["uniqueness_status"], inventory.STATUS_UNIQUE_CLASS)

    def test_unbound_dynamic_target_yields_wildcard_unknown_class(self) -> None:
        rows = self.instruction_rows()
        row = next(row for row in rows if row["frame_id"].endswith("frame_0000000003.jpg"))
        self.assertEqual(row["object_id"], CAR_RED)
        self.assertEqual(row["uniqueness_status"], inventory.STATUS_WILDCARD_UNKNOWN_CLASS)
        self.assertIsNone(row["program"])

    def test_missing_s5_blocker_yields_wildcard_unknown_class(self) -> None:
        """AC-3 修订 3：无 S5 条目的布局车作阻断体，也使执行域出现未知类别。

        走生产 `frame_world` + `minimal_program_with_reference` 路径，与「源身份未绑定
        的动态目标」是两条独立机制；本帧不含动态目标，`target_source_bound` 为真。
        """
        rows = self.instruction_rows()
        row = next(row for row in rows if row["frame_id"].endswith("frame_0000000009.jpg"))
        entry = next(item for item in FRAMES if item["frame_id"] == row["frame_id"])
        self.assertNotIn(DYNAMIC, entry["blocking"], "本用例的成因不是动态目标")
        self.assertTrue(entry["target_source_bound"])
        self.assertIn(NO_S5_ENTRY, entry["blocking"])
        self.assertNotIn(NO_S5_ENTRY, entry["referable"])

        self.assertEqual(row["object_id"], CAR_RED)
        self.assertEqual(row["uniqueness_status"], inventory.STATUS_WILDCARD_UNKNOWN_CLASS)
        self.assertIsNone(row["program"])
        self.assertIsNone(row["surface"])

        # 直接复算成因：该阻断体在执行域里 class_word 为 None。
        field_catalog = {
            "objects": s5_objects(),
            "dual_verified_object_ids": [],
            "verified_color_vocabulary": [],
        }
        world = build_catalog.frame_world(entry, field_catalog)
        blocker = world.by_id(NO_S5_ENTRY)
        self.assertIsNotNone(blocker)
        self.assertIsNone(blocker.class_word, "无 S5 记录 → class_word=None（通配）")
        self.assertFalse(blocker.referable)
        self.assertIsNone(
            build_catalog.minimal_program_with_reference(world, CAR_RED, field_catalog)[0]
        )

    def test_phantom_of_other_class_does_not_block(self) -> None:
        rows = self.instruction_rows()
        row = next(row for row in rows if row["frame_id"].endswith("frame_0000000004.jpg"))
        self.assertEqual(row["object_id"], CAR_RED)
        self.assertEqual(row["uniqueness_status"], inventory.STATUS_UNIQUE_CLASS)
        self.assertEqual(row["program"], {"target": {"class": "car"}})

    def test_per_object_programs_are_split_scoped(self) -> None:
        """C1-3（AC-3/表 B）：逐对象的程序集合必须逐 split 可查，不能只给跨划分并集。"""
        result = self.run_inventory()
        rows = self.instruction_rows(result)
        summary = result["summary"]

        expected: dict[str, dict[str, set[str]]] = {}
        for item in rows:
            if item["uniqueness_status"] not in inventory.UNIQUE_STATUSES:
                continue
            expected.setdefault(item["object_id"], {}).setdefault(item["split"], set()).add(
                item["surface"] or inventory.program_key(item["program"])
            )

        by_object = {entry["object_id"]: entry for entry in summary["per_object"]}
        self.assertEqual(set(by_object), set(expected))
        for object_id, per_split in expected.items():
            recorded = by_object[object_id]["programs_by_split"]
            self.assertEqual(
                {name: set(values) for name, values in recorded.items() if values},
                per_split,
                object_id,
            )
            # 并集仍保留，但不得替代逐 split 集合。
            self.assertEqual(set(by_object[object_id]["programs"]), set().union(*per_split.values()))

        # 至少有一个对象跨两个 split 出现，否则本用例证明不了「逐 split」这件事。
        self.assertTrue(
            any(len([s for s, v in per.items() if v]) >= 2 for per in expected.values()),
            "夹具需覆盖同一对象出现在多个 split 的情形",
        )

    def test_overlap_table_matches_per_object_rows(self) -> None:
        result = self.run_inventory()
        summary = result["summary"]
        overlap = summary["object_overlap"]

        def objects_in(split: str) -> set[str]:
            return {
                row["object_id"]
                for row in summary["per_object"]
                if row["unique_rows_by_split"][split] > 0
            }

        train, dev, test = objects_in("train"), objects_in("dev"), objects_in("test")
        self.assertEqual(set(overlap["train_inter_test"]), train & test)
        self.assertEqual(set(overlap["dev_inter_test"]), dev & test)
        self.assertEqual(set(overlap["test_only"]), test - train - dev)
        self.assertEqual(overlap["test_objects"], len(test))
        self.assertEqual(set(overlap["held_out_object_ids"]), {TAXI})
        self.assertIs(summary["frozen_evaluation_set"], False)


class WriteBoundaryTests(FixtureCase):
    def test_output_inside_input_roots_is_refused(self) -> None:
        for forbidden in (
            "runtime/dist-data/frames_catalog/attempt-2/x.json",
            "runtime/test-results/x.json",
            "runtime/frames.arm-a-trial-1-void-attempt-1-hold/x.jpg",
            "runtime/body_command.json",
            "config/scenario.default.json",
            "tools/dist_data/x.py",
            "controller/x.py",
            "Assets/x.cs",
        ):
            with self.assertRaises(receipts.OutputPathForbidden, msg=forbidden):
                receipts.assert_output_allowed(PROJECT_ROOT / forbidden, PROJECT_ROOT)

        writer = receipts.ReceiptWriter(PROJECT_ROOT / "runtime/dist-data/eng-asset", PROJECT_ROOT)
        with self.assertRaises(receipts.OutputPathForbidden):
            writer.write_failure_receipt("inventory", "OUTPUT_PATH_FORBIDDEN", [])

        receipts.assert_output_allowed(PROJECT_ROOT / "runtime/eng-asset/P1-ENG-ASSET-001/x.json", PROJECT_ROOT)
        receipts.assert_output_allowed(PROJECT_ROOT / "docs/evidence/P1-ENG-ASSET-001-fields.json", PROJECT_ROOT)

    def test_no_controller_runtime_imports(self) -> None:
        banned = {"controller.track_loop", "controller.run_log", "controller.trackers"}
        for name in ("__init__", "receipts", "inventory", "label_panel"):
            path = PROJECT_ROOT / "tools" / "eng_asset" / f"{name}.py"
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(alias.name, banned, f"{name}.py")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    self.assertNotIn(module, banned, f"{name}.py")
                    if module == "controller":
                        for alias in node.names:
                            self.assertNotIn(f"controller.{alias.name}", banned, f"{name}.py")
        # 在**干净子进程**里验证：全套运行时别的用例会把 controller.* 装进
        # sys.modules，直接查本进程的 sys.modules 只能反映别人的导入。
        probe = (
            "import sys;"
            "import tools.eng_asset.inventory, tools.eng_asset.label_panel, tools.eng_asset.receipts;"
            "banned={'controller.track_loop','controller.run_log','controller.trackers'};"
            "hit=sorted(banned & set(sys.modules));"
            "sys.exit('LOADED:' + ','.join(hit) if hit else 0)"
        )
        completed = subprocess.run(
            [sys.executable, "-c", probe], cwd=PROJECT_ROOT, capture_output=True, text=True
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.strip())


if __name__ == "__main__":
    unittest.main()
