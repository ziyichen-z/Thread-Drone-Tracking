"""P1-VLM-DATA-002 的 DATA-001 合同增量回归（提案 §5 第 4 条）。

覆盖：附录 A 巡览行与两类 hold 的零重叠、`VALID_SURVEY` 闭集资格、S0
attempt-2 顶层键 allowlist 与六组常量逐字相同、`survey_sessions` 与 S1
枚举一致、逐帧 selection 只降不升、`write_composite` 的 supersession
envelope 与组合链 `supersession_chain`、attempt-3 的实际读取 ref，以及 S5
`inputs` 的精确合同。

夹具走生产路径：巡览归档由 `tools/run_grounding_survey.py` 的 `close` 真实
产出（见 `tests/test_survey_tool.py` 的 `build_closed_session`），不手工
mkdir、不手写 tree/selection/completion。
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools.dist_data import (  # noqa: E402
    artifacts,
    build_catalog,
    build_inventory,
    contract,
    g0_report,
    roots,
    run_pipeline,
)
from tools.dist_data.artifacts import SupersessionError  # noqa: E402

from test_dist_data_driver import DriverCase  # noqa: E402


class SurveyRootTableTest(unittest.TestCase):
    """附录 A 增量：三条 pattern 各恰一匹配，且两类 hold 零重叠。"""

    SURVEY_FRAME = (
        "runtime/test-results/p1-vlm-survey/"
        "p1-vlm-survey-a1-p1-c1-s1/frames/frame_0000000007.jpg"
    )
    DIAGNOSTIC_FRAME = (
        "runtime/frames.p1-vlm-survey-diagnostic-2-hold/frame_0000000007.jpg"
    )
    RESIDUE_FRAME = (
        "runtime/frames.p1-vlm-survey-a1-p1-c1-s1-foreign-residue-hold/"
        "frame_0000000007.jpg"
    )

    def test_each_survey_path_matches_exactly_one_pattern(self) -> None:
        for path in (self.SURVEY_FRAME, self.DIAGNOSTIC_FRAME, self.RESIDUE_FRAME):
            self.assertEqual(len(roots.matching_entries(path)), 1, path)

    def test_usage_classes(self) -> None:
        self.assertEqual(
            roots.matching_entries(self.SURVEY_FRAME)[0].usage_class, "VALID_SURVEY"
        )
        for path in (self.DIAGNOSTIC_FRAME, self.RESIDUE_FRAME):
            self.assertEqual(
                roots.matching_entries(path)[0].usage_class, "DIAGNOSTIC_HOLD", path
            )

    def test_family_placeholder_resolves_to_the_session_id(self) -> None:
        entry = roots.matching_entries(self.SURVEY_FRAME)[0]
        self.assertEqual(entry.family, roots.FAMILY_PLACEHOLDER_UNIT)
        self.assertEqual(
            roots.resolve_family(entry, self.SURVEY_FRAME), "p1-vlm-survey-a1-p1-c1-s1"
        )

    def test_valid_survey_is_floor_eligible_and_holds_are_not(self) -> None:
        self.assertIn("VALID_SURVEY", contract.FLOOR_USAGE_CLASSES)
        self.assertIn("VALID_SURVEY", contract.USAGE_CLASSES)
        self.assertEqual(roots.USAGE_DECISION["VALID_SURVEY"], "INCLUDED")
        self.assertTrue(roots.USAGE_ELIGIBILITY["VALID_SURVEY"]["floor"])
        self.assertFalse(roots.USAGE_ELIGIBILITY["DIAGNOSTIC_HOLD"]["mother"])

    def test_survey_unit_detection(self) -> None:
        unit = roots.source_unit_for(self.SURVEY_FRAME)
        self.assertTrue(roots.is_survey_unit(unit))
        self.assertFalse(roots.is_survey_unit(roots.source_unit_for(self.RESIDUE_FRAME)))
        self.assertFalse(roots.is_survey_unit(roots.SURVEY_ARCHIVE_ROOT))


class ContractAllowlistTest(unittest.TestCase):
    """§2.2 第 4 条 + BC-SURVEY-7：attempt-2 相对**冻结的 attempt-1 字节**
    只允许 allowlist 内的顶层键不同。

    「前」侧必须是存量正式 attempt-1 的逐字字节夹具——用当前
    `contract_document()` 同时生成两侧证明不了任何真实 supersession 边界
    （实测那样只会得到 `{survey_sessions}` 一个键）。
    """

    FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "p1-vlm-data-001-contract-attempt-1.json"
    FIXTURE_BYTES = 5014
    FIXTURE_SHA256 = "1d1cea17fbb5563d903de12996bc87ea788b355088e797f0ffaaa3e8eaef6ddf"
    FROZEN_TOP_LEVEL_KEYS = frozenset(
        {
            "audit", "base_geometry", "class_map", "class_words", "color",
            "cross_check", "dynamic_target", "floors", "gate_terminals",
            "inventory_decisions", "ontology_version", "projection", "relations",
            "schema_version", "splits", "station_bins", "usage_classes",
            "verifier", "work_id",
        }
    )

    def setUp(self) -> None:
        raw = self.FIXTURE.read_bytes()
        # 夹具本身先 fail-closed：漂移或被重新序列化过的夹具会悄悄弱化下面
        # 的差异断言。
        self.assertEqual(len(raw), self.FIXTURE_BYTES)
        self.assertEqual(artifacts.sha256_hex(raw), self.FIXTURE_SHA256)
        envelope = json.loads(raw.decode("utf-8"))
        self.assertEqual(envelope["artifact"], "contract")
        self.assertEqual(envelope["attempt"], "attempt-1")
        self.attempt1 = envelope["payload"]
        self.attempt2 = contract.contract_document(
            [
                {key: "x" for key in contract.SURVEY_SESSION_ROW_KEYS},
            ]
        )

    def test_attempt1_fixture_is_the_frozen_top_level_key_set(self) -> None:
        self.assertEqual(set(self.attempt1), self.FROZEN_TOP_LEVEL_KEYS)
        self.assertNotIn("root_manifest", self.attempt1)
        self.assertNotIn("survey_sessions", self.attempt1)

    def test_only_allowlisted_top_level_keys_differ(self) -> None:
        differing = {
            key
            for key in set(self.attempt1) | set(self.attempt2)
            if artifacts.canonical_json_bytes(self.attempt1.get(key))
            != artifacts.canonical_json_bytes(self.attempt2.get(key))
        }
        # BC-SURVEY-7 说「恰为」（子集断言在键被悄悄丢掉时同样通过）；
        # BC-SURVEY-14 在差异集合上取代它，把四键扩为五键。
        self.assertEqual(
            differing,
            {
                "root_manifest",
                "usage_classes",
                "dynamic_target",
                "survey_sessions",
                "survey_acquisition",
            },
        )
        self.assertEqual(
            differing, set(contract.CONTRACT_PAYLOAD_SUPERSESSION_ALLOWLIST)
        )

    def test_the_shape_the_driver_would_actually_publish_today(self) -> None:
        """零巡览归档是本批**当前**的真实状态，也是 driver 下一次真正发布的形状。
        BC-SURVEY-14 冻结「差异键恰为五键」，所以该形状必须也是五键——
        `survey_sessions` 写空表，而不是省略该键。"""
        without = contract.contract_document()
        self.assertIn("survey_sessions", without)
        self.assertEqual(without["survey_sessions"], [])
        differing = {
            key
            for key in set(self.attempt1) | set(without)
            if artifacts.canonical_json_bytes(self.attempt1.get(key))
            != artifacts.canonical_json_bytes(without.get(key))
        }
        self.assertEqual(
            differing, set(contract.CONTRACT_PAYLOAD_SUPERSESSION_ALLOWLIST)
        )
        self.assertEqual(len(differing), 5)

    def test_every_other_top_level_key_is_byte_identical(self) -> None:
        for key in sorted(set(self.attempt1) - set(contract.CONTRACT_PAYLOAD_SUPERSESSION_ALLOWLIST)):
            self.assertEqual(
                artifacts.canonical_json_bytes(self.attempt1[key]),
                artifacts.canonical_json_bytes(self.attempt2[key]),
                key,
            )

    def test_six_frozen_groups_are_unchanged(self) -> None:
        """FLOORS、θ_occ 与投影常量、站位分箱、pHash 与切分 seed、审计配额、
        颜色判定带六组逐字相同（§2.2 第 4 条点名）。"""
        for group in ("floors", "projection", "station_bins", "splits", "audit", "color"):
            self.assertEqual(
                artifacts.canonical_json_bytes(self.attempt1[group]),
                artifacts.canonical_json_bytes(self.attempt2[group]),
                group,
            )
        self.assertEqual(self.attempt1["projection"]["theta_occ"], contract.THETA_OCC)
        self.assertEqual(self.attempt1["floors"]["F1"]["min_objects"], 60)

    def test_attempt2_carries_the_new_keys(self) -> None:
        for key in ("survey_sessions", "root_manifest", "survey_acquisition"):
            self.assertIn(key, self.attempt2)

    def test_unconditional_keys_do_not_hang_off_survey_sessions(self) -> None:
        """生产 driver 传 `sessions or None`；零巡览归档时该参数即为 None。
        把 `root_manifest` 挂在它上面会让真实的 attempt-2 完全不带根清单。"""
        for document in (contract.contract_document(), contract.contract_document(None)):
            self.assertIn("root_manifest", document)
            self.assertIn("survey_acquisition", document)

    def test_dynamic_target_schema_closed_set_gains_target_parked(self) -> None:
        # 冻结的 attempt-1 里根本没有 schemas 子键——这正是差异真实存在的证明。
        self.assertNotIn("schemas", self.attempt1["dynamic_target"])
        schemas = self.attempt2["dynamic_target"]["schemas"]
        # BC-SURVEY-10 冻结了顺序，不只是集合。
        self.assertEqual(schemas, ["m3", "scouting", "sweep_proxy", "target_parked"])
        self.assertEqual(list(contract.DYNAMIC_TARGET_SCHEMAS), schemas)
        # 既有键逐字不变。
        for key in ("source_authority", "source_verified_fields", "referable"):
            self.assertEqual(
                self.attempt1["dynamic_target"][key],
                self.attempt2["dynamic_target"][key],
                key,
            )


class ParkedTargetSchemaTest(unittest.TestCase):
    """§2.2 第 3 条：`target_parked` 阻断体与恒 false 的 `target_unbounded`。"""

    def _camera(self) -> object:
        from tools.dist_data import project_boxes

        return project_boxes.Camera(
            position=(0.0, 20.0, 0.0),
            right=(1.0, 0.0, 0.0),
            up=(0.0, 0.0, 1.0),
            forward=(0.0, -1.0, 0.0),
            fx=415.6921938165305,
            fy=415.6921938165305,
            cx=320.0,
            cy=240.0,
            width=640,
            height=480,
        )

    def test_parked_bounds_use_the_frozen_extents(self) -> None:
        bounds = contract.parked_target_bounds((10.0, 0.2, 20.0))
        self.assertEqual(bounds["min_x_m"], 9.0)
        self.assertEqual(bounds["max_x_m"], 11.0)
        self.assertEqual(bounds["min_y_m"], 0.2)
        self.assertAlmostEqual(bounds["max_y_m"], 1.75)
        self.assertEqual(bounds["min_z_m"], 18.0)
        self.assertEqual(bounds["max_z_m"], 22.0)

    def test_blocker_is_produced_and_never_unbounded(self) -> None:
        row = build_catalog.parked_target_truth_row(
            [{"x": 0.0, "y": 0.2, "z": 0.0}, {"x": 0.0, "y": 0.2, "z": 1.0}]
        )
        box, unbounded = build_catalog.target_blocker_from_truth(
            row, contract.TARGET_SCHEMA_PARKED, self._camera()
        )
        self.assertIsNotNone(box)
        self.assertFalse(unbounded)

    def test_out_of_view_parked_target_is_absent_not_unknown(self) -> None:
        row = build_catalog.parked_target_truth_row(
            [{"x": 0.0, "y": 0.2, "z": 900.0}, {"x": 0.0, "y": 0.2, "z": 901.0}]
        )
        box, unbounded = build_catalog.target_blocker_from_truth(
            row, contract.TARGET_SCHEMA_PARKED, self._camera()
        )
        self.assertIsNone(box)
        self.assertFalse(unbounded)  # 位姿已知 → 不在画面内，不是「未知」

    def test_missing_parked_pose_is_fail_closed(self) -> None:
        with self.assertRaises(build_catalog.CatalogError):
            build_catalog.target_blocker_from_truth(
                {}, contract.TARGET_SCHEMA_PARKED, self._camera()
            )

    def test_schema_outside_the_closed_set_is_rejected(self) -> None:
        with self.assertRaises(build_catalog.CatalogError):
            build_catalog.target_blocker_from_truth({}, "made_up", self._camera())


class CompositeSupersessionTest(DriverCase):
    """§2.2 第 5 条：组合工件走与普通工件**同一条** supersession 协议。"""

    def _publish(self, attempt: str, **kwargs) -> artifacts.ArtifactRef:
        return self.store.write_composite(
            "frames_catalog",
            attempt,
            {"stage": 3, "frame_count": 1},
            iter([{"frame_id": "a", "value": 1}]),
            **kwargs,
        )

    def test_envelope_carries_supersedes_and_reason(self) -> None:
        self._publish("attempt-1")
        reference = self._publish(
            "attempt-2",
            supersedes="attempt-1",
            supersession_reason="P1-VLM-DATA-002 survey roots",
        )
        envelope = json.loads(Path(reference.path).read_bytes().decode("utf-8"))
        self.assertEqual(envelope["supersedes"], "attempt-1")
        self.assertEqual(
            envelope["supersession_reason"], "P1-VLM-DATA-002 survey roots"
        )

    def test_supersession_without_reason_is_rejected(self) -> None:
        self._publish("attempt-1")
        with self.assertRaises(SupersessionError):
            self._publish("attempt-2", supersedes="attempt-1")

    def test_reason_without_supersedes_is_rejected(self) -> None:
        with self.assertRaises(SupersessionError):
            self._publish("attempt-2", supersession_reason="无 supersedes 的归因")

    def test_missing_predecessor_is_rejected_before_any_bytes_are_written(self) -> None:
        with self.assertRaises(SupersessionError):
            self._publish(
                "attempt-2", supersedes="attempt-1", supersession_reason="不存在的前身"
            )
        self.assertFalse(self.store.path_for("frames_catalog", "attempt-2").exists())
        self.assertFalse(self.store.staging_dir("frames_catalog", "attempt-2").exists())

    def test_supersession_chain_walks_composite_manifests(self) -> None:
        self._publish("attempt-1")
        self._publish("attempt-2", supersedes="attempt-1", supersession_reason="r2")
        self._publish("attempt-3", supersedes="attempt-2", supersession_reason="r3")
        self.assertEqual(
            self.store.supersession_chain("frames_catalog", "attempt-3"),
            ["attempt-3", "attempt-2", "attempt-1"],
        )

    def test_supersession_chain_walks_ordinary_artifacts_too(self) -> None:
        self.store.write("field_catalog", "attempt-2", {"objects": []},
                         supersedes=None, supersession_reason=None)
        self.store.write(
            "field_catalog", "attempt-3", {"objects": [1]},
            supersedes="attempt-2", supersession_reason="r3",
        )
        self.assertEqual(
            self.store.supersession_chain("field_catalog", "attempt-3"),
            ["attempt-3", "attempt-2"],
        )


class Stage5LineageTest(DriverCase):
    """§2.2 第 6 条：S5 `inputs` = 本次实际读取的两个 ref，顺序固定。"""

    def test_stage5_inputs_are_actual_read_refs(self) -> None:
        self.driver.stage3_frames_catalog()
        self.driver.stage4_splits()
        self.driver.stage5_field_catalog()
        envelope = json.loads(
            self.store.path_for("field_catalog", "attempt-1").read_bytes().decode("utf-8")
        )
        inputs = envelope["inputs"]
        self.assertEqual(len(inputs), 2)
        self.assertEqual(
            [item["artifact"] for item in inputs], ["frames_catalog", "layout"]
        )
        for item in inputs:
            self.assertEqual(sorted(item), ["artifact", "attempt", "sha256"])
        # 「实际读取」而不是事后按路径合成：SHA 必须等于盘上工件的真实字节。
        catalog_sha = artifacts.sha256_file(
            self.store.path_for("frames_catalog", "attempt-1")
        )
        layout_sha = artifacts.sha256_file(self.store.path_for("layout", "attempt-1"))
        self.assertEqual(inputs[0]["sha256"], catalog_sha)
        self.assertEqual(inputs[1]["sha256"], layout_sha)

    def test_a_mismatched_ref_fails_closed_on_read(self) -> None:
        self.driver.stage3_frames_catalog()
        with self.assertRaises(artifacts.DistDataError):
            self.store.read(
                "layout", "attempt-1", requesting_stage=5, expected_sha256="0" * 64
            )


class SupersessionResolutionTest(DriverCase):
    """§2.2 第 4/5 条 + 复核 F1：前身按阶段从 store 解析为「最新已发布前身」。

    改写自 `Attempt3ReadRefTest.test_supersession_kwargs_skip_absent_predecessors`
    ——那条把「前身缺席就写 `supersedes: null`」固定成了期望值，而正式 attempt-1
    的 S0–S5 六件全部存在，前身从不缺席，`{}` 是断链不是「不伪造」。
    """

    REASON = "P1-VLM-DATA-002 survey roots"

    def _driver(self, attempt: str, reason: str | None = REASON):
        return run_pipeline.PipelineDriver(
            self.root, attempt, pixels=self.pixels, supersession_reason=reason
        )

    def test_attempt1_has_no_predecessor(self) -> None:
        driver = self._driver("attempt-1")
        self.assertIsNone(driver.resolve_predecessor("inventory"))
        self.assertEqual(driver._supersession_kwargs("inventory"), {})

    def test_predecessor_is_the_latest_published_before_the_current_attempt(self) -> None:
        # setUp 已发布 inventory@attempt-1。
        self.assertEqual(
            self._driver("attempt-2").resolve_predecessor("inventory"), "attempt-1"
        )
        self.store.write("inventory", "attempt-2", self._inventory())
        self.assertEqual(
            self._driver("attempt-3").resolve_predecessor("inventory"), "attempt-2"
        )

    def test_attempt3_falls_back_to_attempt1_when_attempt2_is_absent(self) -> None:
        """F1 闭合要求 (i)：attempt-2 缺席、attempt-1 存在时前身必须是 attempt-1。"""
        self.store.write_composite(
            "frames_catalog", "attempt-1",
            {"stage": 3, "frame_count": 1},
            iter([{"frame_id": "a"}]),
        )
        driver = self._driver("attempt-3")
        self.assertEqual(driver.resolve_predecessor("frames_catalog"), "attempt-1")
        self.assertEqual(
            driver._supersession_kwargs("frames_catalog"),
            {"supersedes": "attempt-1", "supersession_reason": self.REASON},
        )

    def test_an_unresolvable_predecessor_is_refused_not_silently_omitted(self) -> None:
        driver = self._driver("attempt-2")
        with self.assertRaises(run_pipeline.PipelineError) as caught:
            driver._supersession_kwargs("frames_catalog")  # 从未发布过
        self.assertIn("解析不到已发布前身", str(caught.exception))
        self.assertIn("断链", str(caught.exception))

    def test_a_missing_reason_is_refused(self) -> None:
        """F1 闭合要求 (ii)：attempt-2 未声明归因即拒绝写入。"""
        driver = self._driver("attempt-2", reason=None)
        with self.assertRaises(run_pipeline.PipelineError) as caught:
            driver._supersession_kwargs("inventory")
        self.assertIn("缺 supersession 归因", str(caught.exception))

    def test_the_written_envelope_carries_the_resolved_predecessor(self) -> None:
        driver = self._driver("attempt-2")
        # attempt-2 是新表示的首次正式执行，它的直接依赖是自己的 attempt-2 产物
        # （attempt-1 是旧表示基线，不进读取链）。
        self.store.write("inventory", "attempt-2", self._inventory())
        self.store.write("layout", "attempt-2", self._layout())
        self.store.write_composite(
            "frames_catalog", "attempt-1",
            {"stage": 3, "frame_count": 1},
            iter([{"frame_id": "a"}]),
        )
        driver.stage3_frames_catalog()
        envelope = json.loads(
            self.store.path_for("frames_catalog", "attempt-2")
            .read_bytes().decode("utf-8")
        )
        self.assertEqual(envelope["supersedes"], "attempt-1")
        self.assertEqual(envelope["supersession_reason"], self.REASON)


class RootManifestProjectionTest(unittest.TestCase):
    """BC-SURVEY-7：根清单投影的形状、顺序与排除项。"""

    def setUp(self) -> None:
        self.manifest = roots.root_manifest()

    def test_members_are_runtime_order_not_sorted(self) -> None:
        self.assertEqual(
            self.manifest["enumeration_roots"],
            ["runtime", "docs/evidence/P1-M3-BODY-001-1b"],
        )
        # 排序会把这个顺序悄悄改掉（sorted 会把 docs/... 排到前面）。
        self.assertNotEqual(
            self.manifest["enumeration_roots"],
            sorted(self.manifest["enumeration_roots"]),
        )
        self.assertEqual(
            self.manifest["root_excluded_prefixes"], list(roots.ROOT_EXCLUDED_PREFIXES)
        )
        self.assertEqual(
            self.manifest["must_be_empty_dirs"], list(roots.MUST_BE_EMPTY_DIRS)
        )

    def test_table_preserves_a1_a2_a3_declaration_order(self) -> None:
        self.assertEqual(len(self.manifest["table"]), len(roots.ROOT_TABLE))
        self.assertEqual(
            [row["pattern"] for row in self.manifest["table"]],
            [entry.pattern for entry in roots.ROOT_TABLE],
        )

    def test_manifest_omits_note_and_compiled_regex(self) -> None:
        expected = set(roots.ROOT_MANIFEST_ENTRY_FIELDS)
        for row in self.manifest["table"]:
            self.assertEqual(set(row), expected)
            self.assertNotIn("note", row)
            self.assertNotIn("regex", row)
        # 断言非空洞：表里确实有带 note 的条目，asdict 会泄漏它们。
        self.assertTrue(any(entry.note for entry in roots.ROOT_TABLE))

    def test_family_placeholder_is_projected_verbatim(self) -> None:
        survey_rows = [
            row for row in self.manifest["table"]
            if row["pattern"].startswith(roots.SURVEY_ARCHIVE_ROOT + "/")
        ]
        self.assertEqual(len(survey_rows), 1)
        self.assertEqual(survey_rows[0]["family"], roots.FAMILY_PLACEHOLDER_UNIT)
        hold_rows = [
            row for row in self.manifest["table"]
            if "foreign-residue-hold" in row["pattern"]
        ]
        self.assertEqual(len(hold_rows), 1)
        self.assertIsNone(hold_rows[0]["family"])
        self.assertIsNone(hold_rows[0]["layout_class"])

    def test_manifest_is_the_contract_key_verbatim(self) -> None:
        document = contract.contract_document()
        self.assertEqual(
            artifacts.canonical_json_bytes(document["root_manifest"]),
            artifacts.canonical_json_bytes(self.manifest),
        )


class RootManifestReconciliationTest(unittest.TestCase):
    """BC-SURVEY-7：S1 枚举前对账，不等即失败。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "runtime" / "frames").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _mutated(self) -> dict:
        manifest = roots.root_manifest()
        manifest["table"] = [dict(row) for row in manifest["table"]]
        manifest["table"][0]["pattern"] = manifest["table"][0]["pattern"] + "-MUTATED"
        return manifest

    def test_matching_manifest_is_asserted(self) -> None:
        payload = build_inventory.build_inventory(
            self.root, root_manifest=roots.root_manifest()
        )
        self.assertTrue(payload["root_manifest_audit"]["asserted"])
        self.assertEqual(
            payload["root_manifest_audit"]["entry_count"], len(roots.ROOT_TABLE)
        )

    def test_absent_declaration_is_a_reported_diagnostic_not_an_assertion(self) -> None:
        payload = build_inventory.build_inventory(self.root)
        self.assertFalse(payload["root_manifest_audit"]["asserted"])

    def test_s1_fails_when_the_declared_manifest_disagrees(self) -> None:
        with self.assertRaises(build_inventory.InventoryError) as caught:
            build_inventory.build_inventory(self.root, root_manifest=self._mutated())
        self.assertIn("table", str(caught.exception))
        self.assertIn("root_manifest", str(caught.exception))

    def test_a_dropped_member_is_caught(self) -> None:
        manifest = roots.root_manifest()
        manifest.pop("must_be_empty_dirs")
        with self.assertRaises(build_inventory.InventoryError):
            build_inventory.build_inventory(self.root, root_manifest=manifest)

    def test_reconciliation_precedes_enumeration(self) -> None:
        """`MUST_BE_EMPTY_DIRS` 本身是被投影的成员之一，所以对账必须早于
        `assert_empty_dirs`——否则空目录断言会在未对账的表下先行消费。"""
        (self.root / "runtime" / "frames" / "frame_0000000000.jpg").write_bytes(b"x")
        with self.assertRaises(build_inventory.InventoryError) as caught:
            build_inventory.build_inventory(self.root, root_manifest=self._mutated())
        message = str(caught.exception)
        self.assertIn("root_manifest", message)
        self.assertNotIn("应为空目录", message)


class Stage1ContractGateTest(unittest.TestCase):
    """BC-SURVEY-7：S1 必须拿到 S0 的 `root_manifest`，缺键即 fail-closed。

    自带干净临时根（附录 A 的枚举断言只认真实归档路径，`DriverCase` 的合成
    帧会先在「恰一匹配」上失败）。
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "runtime" / "frames").mkdir(parents=True)
        self.driver = run_pipeline.PipelineDriver(self.root)
        self.store = artifacts.ArtifactStore(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_stage1_rejects_an_s0_contract_without_root_manifest(self) -> None:
        payload = {
            key: value
            for key, value in contract.contract_document().items()
            if key != "root_manifest"
        }
        self.store.write("contract", "attempt-1", payload, stage=0)
        with self.assertRaises(run_pipeline.PipelineError) as caught:
            self.driver.stage1_inventory()
        self.assertIn("root_manifest", str(caught.exception))

    def test_stage1_passes_the_manifest_it_actually_read(self) -> None:
        self.driver.stage0_contract()
        self.driver.stage1_inventory()
        payload, _ref = self.store.read("inventory", "attempt-1", requesting_stage=1)
        self.assertTrue(payload["root_manifest_audit"]["asserted"])
        envelope = json.loads(
            self.store.path_for("inventory", "attempt-1").read_bytes().decode("utf-8")
        )
        self.assertEqual(
            [(item["artifact"], item["attempt"]) for item in envelope["inputs"]],
            [("contract", "attempt-1")],
        )


class UsageClassOrderTest(unittest.TestCase):
    """BC-SURVEY-11：唯一插入点，且既有类的相对顺序逐字不变。"""

    LEGACY_ORDER = (
        "VALID_FORMAL", "VALID_SCOUTING_CLOSED", "VALID_PARENT_HOLD",
        "PROTOCOL_INVALID", "VOID_TRIAL_HOLD", "SMOKE", "CALIBRATION",
        "DIAGNOSTIC_HOLD", "UNRELEASED_PLAY_HOLD", "PREVIEW", "DERIVED_OVERLAY",
        "DOC_COPY", "THIRD_PARTY_ASSET", "INVALID_RENDER_PROBE", "PROBE_TRUTH_ONLY",
    )

    def test_valid_survey_sits_between_parent_hold_and_protocol_invalid(self) -> None:
        classes = list(contract.USAGE_CLASSES)
        self.assertEqual(classes.count("VALID_SURVEY"), 1)
        index = classes.index("VALID_SURVEY")
        self.assertEqual(classes[index - 1], "VALID_PARENT_HOLD")
        self.assertEqual(classes[index + 1], "PROTOCOL_INVALID")

    def test_every_legacy_class_keeps_its_relative_order(self) -> None:
        remaining = tuple(
            name for name in contract.USAGE_CLASSES if name != "VALID_SURVEY"
        )
        self.assertEqual(remaining, self.LEGACY_ORDER)

    def test_table_order_is_the_lineage_primary_priority(self) -> None:
        ranks = [
            build_inventory._lineage_primary_rank(name)
            for name in contract.USAGE_CLASSES
        ]
        self.assertEqual(ranks, sorted(ranks))
        self.assertEqual(ranks, list(range(len(contract.USAGE_CLASSES))))


class SweepProxyNamingTest(unittest.TestCase):
    """BC-SURVEY-10：命名不得改变既有代理分支的判定与控制流。"""

    def test_closed_set_order_is_frozen(self) -> None:
        self.assertEqual(
            contract.DYNAMIC_TARGET_SCHEMAS,
            ("m3", "scouting", "sweep_proxy", "target_parked"),
        )

    def test_sweep_proxy_branch_is_still_selected_by_absent_schema(self) -> None:
        """代理分支仍由 `schema_family is None` 触发；给它命名没有把它变成一个
        可传入的 schema 值。"""
        with self.assertRaises(build_catalog.CatalogError) as caught:
            build_catalog.target_blocker_from_truth(None, None, object())
        self.assertIn("扫掠代理", str(caught.exception))

    def test_named_sweep_proxy_is_not_accepted_as_a_truth_schema(self) -> None:
        with self.assertRaises(build_catalog.CatalogError):
            build_catalog.target_blocker_from_truth(
                {}, contract.TARGET_SCHEMA_SWEEP_PROXY, object()
            )


class ViewIdSyntaxTest(unittest.TestCase):
    """BC-SURVEY-13：完整语法校验；前缀匹配、畸形与越界一律拒绝。"""

    LEGAL_SURVEY = ("s/C14/00", "s/C26/15", "s/R14-000/07", "s/W26/09")
    LEGAL_WITNESS = ("w/C14", "w/C26", "w/W26")
    ILLEGAL = (
        "w/", "w/C14x", "w/C1", "w/R14-000", "w/C14/00", "w/c14",
        "s/C14", "s/C14/0", "s/C14/16", "s/C14/007", "s/C14/00/x", "s//00",
        "s/C14/0a", "s/C14/-1", " s/C14/00", "s/C14/00 ", "", "x/C14",
        "S/C14/00", "W/C14",
    )
    NON_STRINGS = (None, True, False, 0, 16, 1.5, ["s/C14/00"], {"s": 0}, b"s/C14/00")

    def test_legal_values_parse(self) -> None:
        for value in self.LEGAL_SURVEY:
            kind, position, index = contract.parse_survey_view_id(value)
            self.assertEqual(kind, "survey")
            self.assertEqual(value, f"s/{position}/{index:02d}")
        for value in self.LEGAL_WITNESS:
            kind, position, index = contract.parse_survey_view_id(value)
            self.assertEqual(kind, "witness")
            self.assertIn(position, contract.SURVEY_WITNESS_POSITION_IDS)
            self.assertIsNone(index)

    def test_illegal_values_are_rejected(self) -> None:
        for value in self.ILLEGAL:
            with self.assertRaises(contract.SurveyContractError, msg=repr(value)):
                contract.parse_survey_view_id(value)

    def test_non_strings_are_rejected_without_coercion(self) -> None:
        for value in self.NON_STRINGS:
            with self.assertRaises(contract.SurveyContractError, msg=repr(value)):
                contract.parse_survey_view_id(value)

    def test_witness_set_is_exactly_three_values(self) -> None:
        self.assertEqual(contract.SURVEY_WITNESS_POSITION_IDS, ("C14", "C26", "W26"))
        accepted = [
            value
            for value in (f"w/{name}" for name in
                          ("C14", "C26", "W26", "R14-000", "C15", "W14"))
            if self._parses(value)
        ]
        self.assertEqual(accepted, ["w/C14", "w/C26", "w/W26"])

    def _parses(self, value: str) -> bool:
        try:
            contract.parse_survey_view_id(value)
            return True
        except contract.SurveyContractError:
            return False

    def test_minters_only_produce_parseable_values(self) -> None:
        for index in range(0, 16):
            contract.parse_survey_view_id(contract.survey_view_id("C14", index))
        for name in contract.SURVEY_WITNESS_POSITION_IDS:
            contract.parse_survey_view_id(contract.survey_witness_view_id(name))
        with self.assertRaises(contract.SurveyContractError):
            contract.survey_view_id("C14", 16)
        with self.assertRaises(contract.SurveyContractError):
            contract.survey_view_id("C14", True)
        with self.assertRaises(contract.SurveyContractError):
            contract.survey_witness_view_id("R14-000")

    def test_prefix_only_classifier_is_gone(self) -> None:
        self.assertFalse(hasattr(contract, "is_survey_witness_view"))

    def test_null_is_legal_only_for_protocol_invalid(self) -> None:
        legal = frozenset({"s/C14/00"})
        self.assertIsNone(
            contract.validate_selection_view_id(None, "PROTOCOL_INVALID", legal)
        )
        with self.assertRaises(contract.SurveyContractError):
            contract.validate_selection_view_id(None, "VALID_SURVEY", legal)

    def test_syntactically_valid_but_unplanned_id_is_rejected(self) -> None:
        legal = frozenset({"s/C14/00", "w/C14"})
        contract.validate_selection_view_id("w/C14", "VALID_SURVEY", legal)
        with self.assertRaises(contract.SurveyContractError) as caught:
            contract.validate_selection_view_id("w/C26", "VALID_SURVEY", legal)
        self.assertIn("已复核 plan", str(caught.exception))


class SurveyPlanViewIdsTest(unittest.TestCase):
    """BC-SURVEY-13：合法集合只来自 plan 的**保留**视角。"""

    def _plan(self) -> dict:
        return {
            "schema_version": contract.SURVEY_PLAN_SCHEMA,
            "plan_identity": "p1-vlm-survey-a1-p1-c1",
            "positions": [
                {
                    "position_id": "C14",
                    "views": [
                        {"kind": "survey", "view_id": "s/C14/00"},
                        {"kind": "witness", "view_id": "w/C14"},
                    ],
                }
            ],
            "dropped_positions": [
                {
                    "position_id": "R14-060",
                    "views": [{"kind": "survey", "view_id": "s/R14-060/00"}],
                }
            ],
            "witness_prediction": [
                {"kind": "witness", "view_id": "w/W26", "kept": False}
            ],
        }

    def test_only_kept_positions_contribute(self) -> None:
        survey_ids, witness_ids = contract.survey_plan_view_ids(self._plan())
        self.assertEqual(survey_ids, frozenset({"s/C14/00"}))
        self.assertEqual(witness_ids, frozenset({"w/C14"}))
        # 被丢弃的位置与被拒绝的证人预测都不得回流。
        self.assertNotIn("s/R14-060/00", survey_ids)
        self.assertNotIn("w/W26", witness_ids)

    def test_kind_mismatch_is_rejected(self) -> None:
        plan = self._plan()
        plan["positions"][0]["views"][0]["kind"] = "witness"
        with self.assertRaises(contract.SurveyContractError):
            contract.survey_plan_view_ids(plan)

    def test_position_mismatch_is_rejected(self) -> None:
        plan = self._plan()
        plan["positions"][0]["views"][0]["view_id"] = "s/C26/00"
        with self.assertRaises(contract.SurveyContractError):
            contract.survey_plan_view_ids(plan)

    def test_duplicate_view_id_is_rejected(self) -> None:
        plan = self._plan()
        plan["positions"][0]["views"].append(
            {"kind": "survey", "view_id": "s/C14/00"}
        )
        with self.assertRaises(contract.SurveyContractError):
            contract.survey_plan_view_ids(plan)


class SurveyAcquisitionProjectionTest(unittest.TestCase):
    """BC-SURVEY-14：采集协议投影必须收口全部受管常量。"""

    TOP_LEVEL_KEYS = frozenset({"schema_version", "work_id", "constants"})
    CONSTANT_COUNT = 89

    def test_top_level_closed_set_is_exactly_three_keys(self) -> None:
        """BC-SURVEY-17：顶层键闭集恰为 `{schema_version, work_id, constants}`。"""
        self.assertEqual(set(contract.survey_acquisition()), self.TOP_LEVEL_KEYS)

    def test_constants_closed_set_is_exactly_eighty_nine(self) -> None:
        """BC-SURVEY-17 逐字列出 89 项；数目与自动枚举必须一致。"""
        constants = contract.survey_acquisition()["constants"]
        self.assertEqual(len(constants), self.CONSTANT_COUNT)
        self.assertEqual(
            sorted(constants), list(contract.survey_acquisition_constant_names())
        )

    def test_every_public_survey_constant_is_projected(self) -> None:
        """「新增一个受管常量但漏投影会失败」的机检：投影是自动枚举的，
        所以本断言把模块的 `SURVEY_*` 名字与块内键逐一对齐。"""
        projected = set(contract.survey_acquisition()["constants"])
        declared = {
            name
            for name in dir(contract)
            if name.startswith("SURVEY_") and not callable(getattr(contract, name))
        }
        self.assertEqual(projected, declared)
        self.assertEqual(len(projected), self.CONSTANT_COUNT)

    def test_result_driving_constants_are_inside_the_hash_face(self) -> None:
        """§9 登记的那几组「改一个数就翻转已归档判定」的常量必须在块内。"""
        constants = contract.survey_acquisition()["constants"]
        for name in (
            "SURVEY_TETHER_LENGTH_M",
            "SURVEY_OBSTACLE_EXPANSION_XZ_M",
            "SURVEY_OBSTACLE_EXPANSION_TOP_M",
            "SURVEY_DETOUR_EXTRA_M",
            "SURVEY_WITNESS_MIN_DENOMINATOR",
            "SURVEY_WITNESS_MIN_SIDE_PX",
            "SURVEY_WITNESS_SATURATION_MIN",
            "SURVEY_WITNESS_VALUE_MIN",
            "SURVEY_POSITION_TOLERANCE_M",
            "SURVEY_BEARING_TOLERANCE_DEG",
            "SURVEY_MIN_ACHIEVEMENT_RATE",
            "SURVEY_WITNESS_CONNECTIVITY",
            "SURVEY_ANCHOR_TABLE",
            "SURVEY_BIRTH_HEIGHT_M",
            "SURVEY_MAX_FORMAL_PLAY",
        ):
            self.assertIn(name, constants, name)

    def test_anchor_table_is_projected_in_use_order(self) -> None:
        table = contract.survey_acquisition()["constants"]["SURVEY_ANCHOR_TABLE"]
        self.assertEqual([row[0] for row in table], list(range(1, 11)))
        self.assertEqual(table[0], [1, 206.0, 55.0])

    def test_pin_is_the_canonical_bytes_digest(self) -> None:
        import hashlib

        text = json.dumps(
            contract.survey_acquisition(),
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        )
        self.assertEqual(
            contract.survey_acquisition_sha256(),
            hashlib.sha256((text + "\n").encode("utf-8")).hexdigest(),
        )

    def test_a_drifted_pin_fails_closed(self) -> None:
        with self.assertRaises(contract.SurveyContractError) as caught:
            contract.assert_survey_acquisition_pin("0" * 64, where="用例")
        self.assertIn("采集协议已漂移", str(caught.exception))
        for bogus in (None, "", "abc", 0, True, ["x"]):
            with self.assertRaises(contract.SurveyContractError, msg=repr(bogus)):
                contract.assert_survey_acquisition_pin(bogus, where="用例")

    def test_a_mutated_constant_moves_the_pin(self) -> None:
        before = contract.survey_acquisition_sha256()
        original = contract.SURVEY_WITNESS_MIN_DENOMINATOR
        try:
            contract.SURVEY_WITNESS_MIN_DENOMINATOR = 5
            self.assertNotEqual(contract.survey_acquisition_sha256(), before)
        finally:
            contract.SURVEY_WITNESS_MIN_DENOMINATOR = original
        self.assertEqual(contract.survey_acquisition_sha256(), before)


class SurveyAcquisitionReconciliationTest(unittest.TestCase):
    """BC-SURVEY-14：S1 枚举前对账采集协议投影。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "runtime" / "frames").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_matching_projection_is_asserted(self) -> None:
        payload = build_inventory.build_inventory(
            self.root, survey_acquisition=contract.survey_acquisition()
        )
        self.assertTrue(payload["survey_acquisition_audit"]["asserted"])

    def test_a_drifted_projection_fails(self) -> None:
        declared = contract.survey_acquisition()
        declared["constants"].pop("SURVEY_TETHER_LENGTH_M")
        with self.assertRaises(build_inventory.InventoryError) as caught:
            build_inventory.build_inventory(self.root, survey_acquisition=declared)
        self.assertIn("SURVEY_TETHER_LENGTH_M", str(caught.exception))

    def test_a_non_object_declaration_is_a_domain_error(self) -> None:
        for bogus in ([], "x", 3, True):
            with self.assertRaises(build_inventory.InventoryError, msg=repr(bogus)):
                build_inventory.build_inventory(self.root, survey_acquisition=bogus)
            with self.assertRaises(build_inventory.InventoryError, msg=repr(bogus)):
                build_inventory.build_inventory(self.root, root_manifest=bogus)


class Stage1NullKeyTest(unittest.TestCase):
    """键**存在**不等于可对账：`null` 必须被拒绝，而不是走进诊断分支。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "runtime" / "frames").mkdir(parents=True)
        self.driver = run_pipeline.PipelineDriver(self.root)
        self.store = artifacts.ArtifactStore(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _publish(self, **overrides) -> None:
        payload = dict(contract.contract_document())
        payload.update(overrides)
        self.store.write("contract", "attempt-1", payload, stage=0)

    def test_null_root_manifest_is_rejected(self) -> None:
        self._publish(root_manifest=None)
        with self.assertRaises(run_pipeline.PipelineError) as caught:
            self.driver.stage1_inventory()
        self.assertIn("root_manifest", str(caught.exception))

    def test_null_survey_acquisition_is_rejected(self) -> None:
        self._publish(survey_acquisition=None)
        with self.assertRaises(run_pipeline.PipelineError) as caught:
            self.driver.stage1_inventory()
        self.assertIn("survey_acquisition", str(caught.exception))

    def test_non_object_values_are_rejected(self) -> None:
        for bogus in ([], "x", 7):
            self.store = artifacts.ArtifactStore(self.root)
            path = self.store.path_for("contract", "attempt-1")
            if path.exists():
                path.unlink()
            self._publish(root_manifest=bogus)
            with self.assertRaises(run_pipeline.PipelineError, msg=repr(bogus)):
                self.driver.stage1_inventory()


class RootManifestFieldSetTest(unittest.TestCase):
    """BC-SURVEY-7 的冻结面不能靠「有人恰好打了五个字段名」维持。"""

    def test_the_five_operational_fields_are_pinned_literally(self) -> None:
        self.assertEqual(
            roots.ROOT_MANIFEST_ENTRY_FIELDS,
            ("pattern", "kind", "usage_class", "family", "layout_class"),
        )

    def test_every_row_carries_all_five_literal_fields(self) -> None:
        expected = {"pattern", "kind", "usage_class", "family", "layout_class"}
        for row in roots.root_manifest()["table"]:
            self.assertEqual(set(row), expected)

    def test_a_usage_class_change_is_visible_to_reconciliation(self) -> None:
        """收窄字段集会让用途类改动对 S1 隐形——BC-SURVEY-7 明禁。"""
        declared = roots.root_manifest()
        declared["table"] = [dict(row) for row in declared["table"]]
        declared["table"][0]["usage_class"] = "PROTOCOL_INVALID"
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "runtime" / "frames").mkdir(parents=True)
            with self.assertRaises(build_inventory.InventoryError):
                build_inventory.build_inventory(root, root_manifest=declared)

    def test_a_kind_change_is_visible_to_reconciliation(self) -> None:
        declared = roots.root_manifest()
        declared["table"] = [dict(row) for row in declared["table"]]
        declared["table"][0]["kind"] = "truth"
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "runtime" / "frames").mkdir(parents=True)
            with self.assertRaises(build_inventory.InventoryError):
                build_inventory.build_inventory(root, root_manifest=declared)


class MixedAttemptReadTest(DriverCase):
    """BC-SURVEY-4 + 复核 F2：混合 attempt 的读取解析与**生产入口**的续跑。

    F2 判「BC-4 的混合读取路径只在测试里可达」——因为 `--run` 恒从 S0 起，
    会把已发布的阶段也重发成 attempt-3，回退于是永不触发。本类因此既测解析
    本身，也经 `run_stages` 的生产入口逐阶段验证续跑。
    """

    REASON = "P1-VLM-DATA-002 attempt-3 engineering retry"

    # S2 的阶段体要读冻结基础几何与 default 场景字节，故把这两份真实输入复制进
    # 临时根，让 `stage2_layout` 在生产入口下真的跑起来（复核 F2 要求 S2/S3/S4/S5
    # 各自作为首个未发布阶段被验证，而不是只验 S3）。
    REPO_INPUTS = (
        "config/scenario.default.json",
        "config/road_data.json",
        "docs/evidence/P1-M3-BODY-001-scene-geometry.json",
    )

    def setUp(self) -> None:
        super().setUp()
        import shutil

        for relative in self.REPO_INPUTS:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT_ROOT / relative, destination)
        (self.root / "runtime" / "frames").mkdir(parents=True, exist_ok=True)

    def _driver(self, attempt="attempt-3"):
        return run_pipeline.PipelineDriver(
            self.root, attempt, pixels=self.pixels, supersession_reason=self.REASON
        )

    def test_read_chain_prefers_the_newer_attempt_then_falls_back(self) -> None:
        self.assertEqual(
            run_pipeline.PipelineDriver(self.root, "attempt-1").read_chain(),
            ("attempt-1",),
        )
        self.assertEqual(
            run_pipeline.PipelineDriver(self.root, "attempt-2").read_chain(),
            ("attempt-2",),
        )
        self.assertEqual(
            run_pipeline.PipelineDriver(self.root, "attempt-3").read_chain(),
            ("attempt-3", "attempt-2"),
        )

    SYNTHETIC_STAGES = ("contract", "inventory", "layout")

    def _publish_through(self, attempt: str, last_stage: str) -> None:
        """把 `attempt` 发布到 `last_stage` 为止。

        `contract`/`inventory`/`layout` 直接写合成载荷（真实 S0–S2 要整个仓库），
        S3–S5 走 driver 的真实阶段函数——回退与 lineage 正是在那里被验证的。
        """
        driver = run_pipeline.PipelineDriver(
            self.root, attempt, pixels=self.pixels,
            supersession_reason=f"{attempt} synthetic run",
        )
        payloads = {
            "contract": {"stage": 0, "synthetic": attempt},
            "inventory": self._inventory(),
            "layout": self._layout(),
        }
        for name, step in run_pipeline.default_stage_order(driver):
            if name in ("g0_report", "mother_set"):
                return
            if name in self.SYNTHETIC_STAGES:
                self.store.write(
                    name, attempt, payloads[name],
                    **driver._supersession_kwargs(name),
                )
            else:
                step()
            if name == last_stage:
                return

    def _publish_attempt2_through(self, last_stage: str) -> None:
        """attempt-1 六件齐备（与真实归档一致），attempt-2 发布到 `last_stage`。"""
        self._publish_through("attempt-1", "field_catalog")
        self._publish_through("attempt-2", last_stage)

    def test_each_dependency_resolves_independently(self) -> None:
        self.store.write("inventory", "attempt-2", self._inventory())
        self.store.write("layout", "attempt-2", self._layout())
        layout3 = self._layout()
        layout3["marker"] = "attempt-3"
        self.store.write("layout", "attempt-3", layout3)
        driver = self._driver()
        self.assertEqual(driver.resolve_read_attempt("layout"), "attempt-3")
        self.assertEqual(driver.resolve_read_attempt("inventory"), "attempt-2")

    def test_a_dependency_published_in_neither_attempt_fails_closed(self) -> None:
        with self.assertRaises(run_pipeline.PipelineError) as caught:
            self._driver().resolve_read_attempt("inventory")
        message = str(caught.exception)
        self.assertIn("attempt-3", message)
        self.assertIn("attempt-2", message)
        self.assertIn("事后合成", message)

    def test_attempt1_is_not_part_of_the_mixed_route(self) -> None:
        self.assertNotIn("attempt-1", self._driver().read_chain())
        with self.assertRaises(run_pipeline.PipelineError):
            self._driver().resolve_read_attempt("inventory")  # 只有 attempt-1 存在

    # --- F2：生产入口的续跑，逐阶段作为「首个未发布阶段」 -------------------
    def _resume_and_capture(self, last_published: str) -> dict:
        """attempt-2 发布到 `last_published`，再经生产入口以 attempt-3 续跑。"""
        self._publish_attempt2_through(last_published)
        driver = self._driver()
        order = run_pipeline.default_stage_order(driver)
        start = run_pipeline.first_unpublished_stage(driver, order)
        emitted: list[str] = []
        run_pipeline.run_stages(
            driver, order, through="field_catalog", emit=emitted.append
        )
        envelopes = {}
        for name in ("layout", "frames_catalog", "splits", "field_catalog"):
            path = self.store.path_for(name, "attempt-3")
            if path.exists():
                envelopes[name] = json.loads(path.read_bytes().decode("utf-8"))
        return {"start": start, "envelopes": envelopes, "emitted": emitted}

    def test_resume_starts_at_layout_when_s2_is_first_unpublished(self) -> None:
        result = self._resume_and_capture("inventory")
        self.assertEqual(result["start"], "layout")
        # S2 的直接依赖 inventory 必须读 attempt-2（§2.2 第 5 条）。
        self.assertEqual(
            self.store.path_for("inventory", "attempt-3").exists(), False,
            "已发布阶段不得被重发",
        )
        inputs = result["envelopes"]["frames_catalog"]["inputs"]
        self.assertEqual(
            [(i["artifact"], i["attempt"]) for i in inputs],
            [("inventory", "attempt-2"), ("layout", "attempt-3")],
        )

    def test_resume_starts_at_frames_catalog_when_s3_is_first_unpublished(self) -> None:
        result = self._resume_and_capture("layout")
        self.assertEqual(result["start"], "frames_catalog")
        self.assertFalse(self.store.path_for("layout", "attempt-3").exists())
        inputs = result["envelopes"]["frames_catalog"]["inputs"]
        self.assertEqual(
            [(i["artifact"], i["attempt"]) for i in inputs],
            [("inventory", "attempt-2"), ("layout", "attempt-2")],
        )

    def test_resume_starts_at_splits_when_s4_is_first_unpublished(self) -> None:
        result = self._resume_and_capture("frames_catalog")
        self.assertEqual(result["start"], "splits")
        self.assertFalse(self.store.path_for("frames_catalog", "attempt-3").exists())
        inputs = result["envelopes"]["splits"]["inputs"]
        self.assertEqual(
            [(i["artifact"], i["attempt"]) for i in inputs],
            [("frames_catalog", "attempt-2")],
        )

    def test_resume_starts_at_field_catalog_when_s5_is_first_unpublished(self) -> None:
        result = self._resume_and_capture("splits")
        self.assertEqual(result["start"], "field_catalog")
        self.assertFalse(self.store.path_for("splits", "attempt-3").exists())
        inputs = result["envelopes"]["field_catalog"]["inputs"]
        self.assertEqual(
            [(i["artifact"], i["attempt"]) for i in inputs],
            [("frames_catalog", "attempt-2"), ("layout", "attempt-2")],
        )

    def test_resume_reports_the_skipped_published_stages(self) -> None:
        result = self._resume_and_capture("layout")
        payload = json.loads(result["emitted"][0])
        self.assertEqual(payload["resumed_from"], "frames_catalog")
        self.assertIn("layout", payload["skipped_published_stages"])
        self.assertIn("inventory", payload["skipped_published_stages"])

    def test_attempt2_runs_from_the_start(self) -> None:
        """attempt ≤ 2 没有可续跑的参照，仍从头跑。"""
        driver = run_pipeline.PipelineDriver(
            self.root, "attempt-2", pixels=self.pixels, supersession_reason="x"
        )
        self.assertIsNone(
            run_pipeline.first_unpublished_stage(
                driver, run_pipeline.default_stage_order(driver)
            )
        )

    # --- F5 / F6 / I17：接受角色 2026-09-05 裁定的三项「范围内必修」 --------
    #
    # 三条都必须经**生产入口**（`PipelineDriver` 构造 + `run_stages`）证明，
    # 且都以「零写入 / 发布前失败」为闭合条件——R2 的病灶正是「写了几件
    # create-once 工件再报错」。
    WRITE_POINTS = (
        "contract", "inventory", "layout", "frames_catalog", "splits",
        "field_catalog", "mother_candidates", "g0_report", "mother_set",
        "stop_point",
    )

    def _published(self, attempt: str) -> list[str]:
        """`attempt` 下实际存在的工件（用于断言「一件也没写」）。"""
        return [
            name
            for name in self.WRITE_POINTS
            if self.store.path_for(name, attempt).exists()
        ]

    def test_through_pointing_at_a_skipped_stage_runs_no_stage(self) -> None:
        """F5：停止界被续跑跳过时，一个阶段也不跑、一件工件也不写。

        操作员要求「跑到 S1 为止」，而 S1 已在 attempt-2 发布；修复前工具会
        越过这个停止界继续执行 S3/S4/S5，把三件**永不删除**的 create-once
        工件写进 attempt-3。
        """
        self._publish_attempt2_through("layout")
        driver = self._driver()
        order = run_pipeline.default_stage_order(driver)
        emitted: list[str] = []
        with self.assertRaises(run_pipeline.PipelineError) as caught:
            run_pipeline.run_stages(
                driver, order, through="inventory", emit=emitted.append
            )
        message = str(caught.exception)
        self.assertIn("inventory", message)
        self.assertIn("零阶段", message)
        self.assertEqual(self._published("attempt-3"), [])
        self.assertEqual(emitted, [], "拒绝时不得先发出续跑说明")

    def test_through_still_stops_at_the_named_stage_after_resume(self) -> None:
        """F5 的正对照：停止界落在会跑的阶段上时，仍旧只跑到那一阶段。"""
        self._publish_attempt2_through("layout")
        driver = self._driver()
        run_pipeline.run_stages(
            driver,
            run_pipeline.default_stage_order(driver),
            through="frames_catalog",
            emit=lambda _line: None,
        )
        self.assertEqual(self._published("attempt-3"), ["frames_catalog"])

    def test_malformed_attempt_is_refused_at_construction(self) -> None:
        """F6：不合式 attempt 在**构造**时就失败，一件工件也写不出。

        修复前 `--attempt attempt3` 会在 `attempt3/` 下写出整棵无 supersession、
        无前身校验的 create-once 工件树——正是 F1 要堵的断链形状，只是换了一个
        不合式的身份。
        """
        self._publish_attempt2_through("layout")
        for malformed in ("attempt3", "attempt-", "attempt-0", "attempt-01",
                          "attempt-2x", "ATTEMPT-3", "attempt-3 "):
            with self.subTest(attempt=malformed):
                with self.assertRaises(run_pipeline.PipelineError) as caught:
                    run_pipeline.PipelineDriver(
                        self.root, malformed, pixels=self.pixels,
                        supersession_reason=self.REASON,
                    )
                self.assertIn("不合式", str(caught.exception))
                self.assertFalse(
                    (self.root / "runtime" / "dist-data" / "inventory" / malformed).exists()
                )

    def test_wellformed_attempt_identities_are_unchanged(self) -> None:
        """F6 的正对照：`attempt-1` 与其它合式身份的既有行为一字不变。"""
        first = run_pipeline.PipelineDriver(self.root, "attempt-1", pixels=self.pixels)
        self.assertEqual(first.read_chain(), ("attempt-1",))
        self.assertEqual(first._supersession_kwargs("inventory"), {})
        self.assertIsNone(first.resolve_predecessor("inventory"))
        self.assertEqual(
            run_pipeline.PipelineDriver(self.root, "attempt-10").read_chain(),
            tuple(f"attempt-{n}" for n in range(10, 1, -1)),
        )

    def test_default_through_reads_splits_from_the_predecessor_attempt(self) -> None:
        """I17：生产默认停止点下，一致 lineage 跑得完。

        attempt-2 发布到 S4（splits）后 attempt-3 从 S5 续跑：S7 读的 `splits`
        必须解析到 attempt-2。修复前 S7 直接按写入 attempt 去找
        `splits@attempt-3`——那件工件既未发布，也**不该**发布（§2.2 第 5 条
        禁止重发已发布阶段），于是 attempt-3 在烧掉一件 field_catalog 之后
        永久卡死且无 S9 收束记录。
        """
        self._publish_attempt2_through("splits")
        self.store.write(
            "audit", "attempt-3",
            {"stage": 6, "verdict": "PASS", "downgraded_group_keys": []},
        )
        driver = self._driver()
        results = run_pipeline.run_stages(
            driver,
            run_pipeline.default_stage_order(driver),
            through="g0_report",  # 生产默认停止点
            emit=lambda _line: None,
        )
        self.assertEqual(list(results[-1]), ["stop_point"])
        stop, _ref = self.store.read("stop_point", "attempt-3", requesting_stage=9)
        self.assertEqual(stop["outcome"], g0_report.GATE_INSUFFICIENT)
        # 已发布阶段不重发：splits 仍只有 attempt-2 一份。
        self.assertFalse(self.store.path_for("splits", "attempt-3").exists())
        self.assertTrue(self.store.path_for("splits", "attempt-2").exists())
        self.assertTrue(self.store.path_for("field_catalog", "attempt-3").exists())

    def test_missing_audit_fails_before_publishing_any_attempt3_artifact(self) -> None:
        """I17：lineage 不一致时，在发布任何新 attempt 工件**之前**失败。

        attempt-2 已完整发布到 S5，attempt-3 因此从 S7 起跑。缺的是 S6 人工
        审计（`audit@attempt-3`），失败必须点名它；修复前失败点名的却是
        `splits@attempt-3`——一件续跑自己决定跳过、且合同禁止重发的工件。
        """
        self._publish_attempt2_through("field_catalog")
        driver = self._driver()
        with self.assertRaises(run_pipeline.PipelineError) as caught:
            run_pipeline.run_stages(
                driver,
                run_pipeline.default_stage_order(driver),
                through="g0_report",
                emit=lambda _line: None,
            )
        message = str(caught.exception)
        self.assertIn("audit", message)
        self.assertNotIn("splits", message)
        self.assertEqual(self._published("attempt-3"), [])

    def test_mixed_generation_splits_and_catalog_fail_before_any_write(self) -> None:
        """I17：跨代混用 `frames_catalog` 时，在写出任何工件前失败。

        BC-SURVEY-4 解绑的是读写 attempt，不是「各输入可以来自任意代」。
        attempt-2 完整发布到 S5、attempt-3 另有一份早先的 `frames_catalog` 时，
        S7 会读到 `frames_catalog@attempt-3` 却读到 `splits@attempt-2`——后者的
        行是按 attempt-2 那一份目录建的。没有这道门，G0 会静默地建立在对不上的
        帧集合上。
        """
        self._publish_attempt2_through("field_catalog")
        driver = self._driver()
        driver.stage3_frames_catalog()  # 早先的一次 `--through frames_catalog`
        self.store.write(
            "audit", "attempt-3",
            {"stage": 6, "verdict": "PASS", "downgraded_group_keys": []},
        )
        with self.assertRaises(run_pipeline.PipelineError) as caught:
            run_pipeline.run_stages(
                driver,
                run_pipeline.default_stage_order(driver),
                through="g0_report",
                emit=lambda _line: None,
            )
        message = str(caught.exception)
        self.assertIn("lineage 不一致", message)
        self.assertIn("零写入", message)
        # 门没有开、S9 没有收束，attempt-3 只剩那件早先就存在的 frames_catalog。
        self.assertEqual(self._published("attempt-3"), ["frames_catalog"])
