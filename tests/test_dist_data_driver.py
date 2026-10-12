"""S0–S9 生产 driver 回归（接受轮 14 §26.2 点名的五类）。

合成世界：S1 的附录 A 闭集只认真实归档路径，所以本用例**直接落盘**合成的
`inventory` / `layout` 工件，再从 S3 起走 driver 的真实组合路径。这样测的是
driver 自己的接线（经 store 取数、禁行边、create-once、门未过拒绝 S8），
而不是重新测已被其它文件覆盖的阶段算法。

像素用注入的 stub：`pixel_source` 的真实适配器有自己的金标用例
（`tests/test_dist_data_pixels.py`），driver 只需证明它把 `PixelSource` /
`GraySource` 接到了 S4/S5 上。
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import (  # noqa: E402
    artifacts,
    bind_layout,
    contract,
    g0_report,
    gen_mother_templates,
    make_splits,
    project_boxes,
    run_pipeline,
)

def _formal_root_snapshot() -> dict[str, str]:
    """正式输出根的逐路径 SHA-256 快照（不存在时为空表）。"""
    import hashlib

    root = PROJECT_ROOT / contract.ARTIFACT_ROOT
    if not root.exists():
        return {}
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


FORMAL_ROOT_SNAPSHOT = _formal_root_snapshot()

LAYOUTS = {
    "default": [
        ("Vehicle_Taxi", 0.0, 20.0),
        ("Vehicle_Bus_color01", 8.0, 24.0),
    ],
    "scene-004": [
        ("Vehicle_Car_color01", 0.0, 20.0),
        ("Vehicle_SUV_color01", 8.0, 24.0),
    ],
}
FAMILY_LAYOUT = {"famA": "default", "famB": "scene-004"}
FAMILY_UNIT = {family: f"runtime/synthetic/{family}" for family in FAMILY_LAYOUT}


def body(name: str, x: float, z: float) -> dict:
    return {
        "scene_object_name": name,
        "min_x_m": x - 1.0,
        "max_x_m": x + 1.0,
        "min_y_m": 0.0,
        "max_y_m": 2.0,
        "min_z_m": z - 2.0,
        "max_z_m": z + 2.0,
    }


def sidecar(index: int) -> dict:
    return {
        "schema_version": "sensor-frame/v3",
        "scenario_id": "synthetic",
        "frame_id": index,
        "camera_position_world_m": [index * 3.0, 10.0, 0.0],
        "camera_right_world": [1.0, 0.0, 0.0],
        "camera_up_world": [0.0, 0.8660254, 0.5],
        "camera_forward_world": [0.0, -0.5, 0.8660254],
        "vertical_fov_deg": 60.0,
        "width": 640,
        "height": 480,
        "intrinsics_px": {
            "fx": 415.6921938165305,
            "fy": 415.6921938165305,
            "cx": 320.0,
            "cy": 240.0,
        },
    }


class _StubPixels:
    """注入式像素源。

    真实适配器只拿得到 `(frame_id, box_px)`——对象身份**不在** frame_id 里，
    而在框里（`ObjectObservation.frame_id` 就是帧路径本身）。本 stub 因此也
    只按框的水平中心分色，避免把「frame_id 里带对象名」这种 stub 专属约定
    当成生产合同。
    """

    def __init__(self) -> None:
        self.crop_calls = 0
        self.phash_calls = 0
        self.seen_frame_ids: set[str] = set()

    def crop_rgb(self, frame_id, box_px):  # noqa: ANN001
        self.crop_calls += 1
        self.seen_frame_ids.add(frame_id)
        centre = (box_px[0] + box_px[2]) / 2.0
        colour = (255, 0, 0) if centre < 320.0 else (0, 0, 255)
        return [colour] * 8

    def gray_matrix(self, frame_id, size):  # noqa: ANN001
        raise AssertionError("driver 应通过 phash() 取近重复签名")

    def phash(self, frame_id):  # noqa: ANN001
        self.phash_calls += 1
        # 每族一个签名：族内帧完全重合，族间 Hamming 远大于阈值 8。
        return 0 if "famA" in frame_id else (2**64 - 1)


class DriverCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.pixels = _StubPixels()
        self.driver = run_pipeline.PipelineDriver(self.root, pixels=self.pixels)
        self.store = artifacts.ArtifactStore(self.root)
        self._write_frames()
        self.store.write("inventory", "attempt-1", self._inventory())
        self.store.write("layout", "attempt-1", self._layout())

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # --- 合成归档 -----------------------------------------------------------
    def _frame_paths(self) -> list[tuple[str, str]]:
        return [
            (family, f"{FAMILY_UNIT[family]}/frames/frame_{index:010d}.jpg")
            for family in FAMILY_LAYOUT
            for index in range(4)
        ]

    def _write_frames(self) -> None:
        import json

        for _family, relative in self._frame_paths():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"")  # driver 不解码，像素走注入的 stub
            index = int(target.stem.rsplit("_", 1)[-1])
            target.with_suffix(".json").write_text(
                json.dumps(sidecar(index)), encoding="utf-8"
            )

    def _inventory(self) -> dict:
        records = []
        for family, relative in self._frame_paths():
            records.append(
                {
                    "path": relative,
                    "kind": "image",
                    "decision": "INCLUDED",
                    "family": family,
                    "layout_class": FAMILY_LAYOUT[family],
                    "usage_class": "VALID_FORMAL",
                    "sidecar_join": {"present": True, "complete": True},
                    "truth_join": {"source": None, "schema_family": None},
                }
            )
        return {"stage": 1, "records": records, "record_count": len(records)}

    def _layout(self) -> dict:
        partitions = {}
        for family, layout_class in FAMILY_LAYOUT.items():
            partitions[f"{family}|sha"] = {
                "partition_id": f"{family}|sha",
                "family": family,
                "layout_class": layout_class,
                "binding_status": "BOUND",
                "source_units": [FAMILY_UNIT[family]],
                "frame_count": 4,
                "instances": [body(name, x, z) for name, x, z in LAYOUTS[layout_class]],
                "phantoms": [],
                "relocation_marks": {},
                "route_world_m": [],
            }
        return {
            "stage": 2,
            "scenario_partitions": partitions,
            "families": {},
            # BC-DATA-23 (5)：`cross_validation` 是 layout 的必有成员。
            "cross_validation": {
                identifier: {
                    "mode": "none",
                    "status": bind_layout.CROSSCHECK_NOT_APPLICABLE,
                    "reason": "合成世界无归档逐帧真值",
                    "pair_count": 0,
                    "sample_count": 0,
                }
                for identifier in partitions
            },
        }

    def _run_to_field_catalog(self) -> None:
        self.driver.stage3_frames_catalog()
        self.driver.stage4_splits()
        self.driver.stage5_field_catalog()

    def _write_passing_audit(self) -> None:
        self.store.write(
            "audit",
            "attempt-1",
            {"stage": 6, "verdict": "PASS", "downgraded_group_keys": []},
        )


class CompositionTest(DriverCase):
    def test_driver_composes_s3_to_s7_and_closes_the_gate(self) -> None:
        catalog = self.driver.stage3_frames_catalog()
        self.assertEqual(catalog["frames"], 8)
        self.assertEqual(catalog["skipped_unbound_frames"], 0)

        splits = self.driver.stage4_splits()
        self.assertEqual(self.pixels.phash_calls, 8)  # S4 真的经 GraySource 取签名
        self.assertEqual(splits["atoms"], 2)  # 两族签名相距远，未并簇

        field_catalog = self.driver.stage5_field_catalog()
        self.assertGreater(self.pixels.crop_calls, 0)  # S5 真的经 PixelSource 取像素
        self.assertGreater(field_catalog["objects"], 0)

        self._write_passing_audit()
        gate = self.driver.stage7_gate()
        # 合成世界远小于 §5.2 冻结下限 → 门**必须**关闭，且不因规模回调。
        self.assertEqual(gate["gate"], g0_report.GATE_INSUFFICIENT)
        self.assertEqual(sorted(gate["unmet_floors"]), ["F1", "F2", "F3", "F4"])
        self.assertGreater(gate["candidates"], 0)

    def test_splits_artifact_carries_assembled_roles_on_the_driver_path(self) -> None:
        """F11 的不可绕过性在生产 driver 上同样成立。"""
        self.driver.stage3_frames_catalog()
        self.driver.stage4_splits()
        manifest, _ = self.store.composite_manifest(
            "splits", "attempt-1", requesting_stage=7
        )
        roles = list(
            self.store.read_composite_rows("splits", "attempt-1", requesting_stage=7)
        )
        self.assertTrue(roles, "BC-DATA-25 (4)：角色行进 shards，但必须非空")
        self.assertTrue(manifest["exposure_matrix"]["per_object"])
        self.assertEqual(manifest["exposure_matrix"]["sample_count"], len(roles))

    def test_rerunning_a_stage_is_byte_identical(self) -> None:
        first = self.driver.stage3_frames_catalog()
        second = self.driver.stage3_frames_catalog()
        self.assertEqual(first["sha256"], second["sha256"])

    def test_audit_strata_use_camera_forward_depth(self) -> None:
        """BC-DATA-15：A1/A2 三分位按相机前向深度，不是欧氏距离。"""
        self.driver.stage3_frames_catalog()
        strata = self.driver.audit_strata()
        self.assertGreater(strata["sample_count"], 0)
        self.assertEqual(sum(strata["counts"].values()), strata["sample_count"])
        depth_of = {
            f"{entry['frame_id']}@{item['object_id']}": item["camera_depth_m"]
            for entry in self.store.read_composite_rows(
                "frames_catalog", "attempt-1", requesting_stage=6
            )
            for item in entry["objects"]
            if item["status"] == "OK" and item["camera_depth_m"] is not None
        }
        near = [depth_of[s] for s in strata["stratum_of_sample"] if strata["stratum_of_sample"][s] == "near"]
        far = [depth_of[s] for s in strata["stratum_of_sample"] if strata["stratum_of_sample"][s] == "far"]
        if near and far:
            self.assertLessEqual(max(near), min(far))


class FailClosedTest(DriverCase):
    def test_stage7_refuses_without_the_human_audit_artifact(self) -> None:
        """F1 的定义是「S5 判定 + A1 通过」；没有审计工件不得当作通过。"""
        self._run_to_field_catalog()
        with self.assertRaises(run_pipeline.PipelineError) as caught:
            self.driver.stage7_gate()
        message = str(caught.exception)
        self.assertIn("audit", message)
        self.assertIn("A1", message)

    def test_missing_predecessor_artifact_is_a_clear_error(self) -> None:
        with self.assertRaises(run_pipeline.PipelineError):
            self.driver.stage4_splits()  # 还没有 frames_catalog

    def test_gate_closed_refuses_to_materialise_the_mother_set(self) -> None:
        self._run_to_field_catalog()
        self._write_passing_audit()
        self.driver.stage7_gate()
        with self.assertRaises(gen_mother_templates.MotherSetError):
            self.driver.stage8_mother_set()

    def test_closed_gate_records_a_stop_point_and_never_reaches_s8(self) -> None:
        """门未过 → 以 INSUFFICIENT 收束、保全工件、S8 永不执行（BC-DATA-2）。"""
        self._write_passing_audit()
        order = [
            ("frames_catalog", self.driver.stage3_frames_catalog),
            ("splits", self.driver.stage4_splits),
            ("field_catalog", self.driver.stage5_field_catalog),
            ("g0_report", self.driver.stage7_gate),
            ("mother_set", self.driver.stage8_mother_set),
        ]
        emitted: list[str] = []
        results = run_pipeline.run_stages(
            self.driver, order, through="mother_set", emit=emitted.append
        )
        self.assertEqual(list(results[-1]), ["stop_point"])
        payload, _ = self.store.read("stop_point", "attempt-1", requesting_stage=9)
        self.assertEqual(payload["outcome"], g0_report.GATE_INSUFFICIENT)
        # 循环在 g0_report 之后就收束了，mother_set 从未被调用。
        self.assertNotIn("mother_set", [name for entry in results for name in entry])
        self.assertFalse(self.store.path_for("mother_set", "attempt-1").exists())
        # 已有工件全部保全。
        for artifact in ("frames_catalog", "splits", "field_catalog", "g0_report"):
            self.assertTrue(self.store.path_for(artifact, "attempt-1").exists(), artifact)

    def test_split_terminal_also_stops_before_s8(self) -> None:
        """可指派 atom < 2 的收束终态同样写 S9、不进 S8。"""

        def _terminal() -> dict:
            raise make_splits.SplitTerminal("INSUFFICIENT_SYMBOLIC_GROUNDING_DATA", "1 个")

        def _splits() -> dict:
            try:
                _terminal()
            except make_splits.SplitTerminal as terminal:
                return {"artifact": "splits", "terminal": terminal.terminal,
                        "detail": terminal.detail}
            raise AssertionError

        results = run_pipeline.run_stages(
            self.driver,
            [("splits", _splits), ("g0_report", self.driver.stage7_gate)],
            through="g0_report",
            emit=lambda _line: None,
        )
        payload, _ = self.store.read("stop_point", "attempt-1", requesting_stage=9)
        self.assertEqual(payload["outcome"], "INSUFFICIENT_SYMBOLIC_GROUNDING_DATA")
        self.assertNotIn("g0_report", [name for entry in results for name in entry])

    def test_forbidden_edge_holds_on_the_production_read_path(self) -> None:
        """driver 的取数经 store，所以 §2 禁行边在生产路径上真的生效。"""
        self.store.write("mother_set", "attempt-1", {"stage": 8})
        with self.assertRaises(artifacts.ForbiddenEdgeError):
            self.driver._read("mother_set", requesting_stage=7)


class InvalidPartitionCase(DriverCase):
    """F17 夹具：一个 BOUND + 一个 `INVALID` partition（后者按 `build_layout`
    的异常分支形态，**不带** `instances`/`phantoms` 键）。"""

    def _layout(self) -> dict:
        payload = super()._layout()
        broken = payload["scenario_partitions"]["famB|sha"]
        payload["scenario_partitions"]["famB|sha"] = {
            "partition_id": broken["partition_id"],
            "family": broken["family"],
            "layout_class": broken["layout_class"],
            "binding_status": bind_layout.BINDING_INVALID,
            "reason": "逆施 default relocation 失败（合成）",
            "source_units": broken["source_units"],
            "frame_count": broken["frame_count"],
        }
        return payload

    def test_driver_skips_invalid_partition_and_preserves_bound_partition(self) -> None:
        """BC-DATA-18 的 partition 局域隔离必须在 S3 也成立。

        合同要求「只使该 partition INVALID、其帧退出」，而不是让一个派生失败
        的 partition 把**全部** partition 的 catalog 一起带走。
        """
        result = self.driver.stage3_frames_catalog()
        self.assertEqual(result["frames"], 4, "BOUND 侧 4 帧必须照常产出")
        self.assertEqual(result["skipped_invalid_frames"], 4)
        families = {
            entry["family"]
            for entry in self.store.read_composite_rows(
                "frames_catalog", "attempt-1", requesting_stage=4
            )
        }
        self.assertEqual(families, {"famA"})


class AuditDomainCase(DriverCase):
    """F18 夹具：混合世界（车辆 + 建筑），建筑同样可得 `status == "OK"`。"""

    BUILDING = "Building Sky_big_color01"

    def _layout(self) -> dict:
        payload = super()._layout()
        for partition in payload["scenario_partitions"].values():
            partition["instances"] = list(partition["instances"]) + [
                body(self.BUILDING, -6.0, 18.0)
            ]
        return payload

    def test_audit_strata_excludes_non_vehicle_occluders(self) -> None:
        """§2.7 的 A1/A2 样本域是目录车辆；建筑不得进三分位样本池。"""
        self.assertIsNone(contract.class_for_scene_object(self.BUILDING))
        self.driver.stage3_frames_catalog()
        statuses = {
            item["status"]
            for entry in self.store.read_composite_rows(
                "frames_catalog", "attempt-1", requesting_stage=6
            )
            for item in entry["objects"]
            if item["object_id"] == self.BUILDING
        }
        self.assertIn("OK", statuses, "夹具前提：建筑确实能取得 OK 状态")

        strata = self.driver.audit_strata()
        offenders = [
            sample_id
            for sample_id in strata["stratum_of_sample"]
            if sample_id.rsplit("@", 1)[-1] == self.BUILDING
        ]
        self.assertEqual(offenders, [], "非车辆不得进入 A1/A2 分层样本池")
        self.assertGreater(strata["sample_count"], 0)


SCOUT1_UNIT = "runtime/test-results/p1-detect-001-scout-1-closed-exchange"
SCOUT1_TRUTH = "runtime/p1-detect-scouting/p1-detect-001-scout-1/truth"
SCOUT1_SNAPSHOT = f"{SCOUT1_UNIT}/scenario_config.json"
M3_UNIT = "runtime/test-results/p1-m3-body-001-arm-a-trial-3-post-run"
M3_TRUTH = "runtime/runs/p1-m3-body-001-arm-a-trial-3/m3_body_truth.jsonl"
M3_SNAPSHOT = "runtime/runs/p1-m3-body-001-arm-a-trial-3/scenario.json"
SCENE004_HOLD = "runtime/scenario_config.p1-scene-004.hold.json"


class ArchiveS2Case(unittest.TestCase):
    """F16 夹具：把归档真实字节按原相对路径复制进临时根，走生产 S2。

    只有 `scenario_config.json` 这一格里放**哪一份归档字节**是变量——夹具从不
    手写 `cross_validation` / `binding_status`，那两者必须由生产 `build_layout`
    自己算出来（接受轮 16 §28.3 (1)）。
    """

    REQUIRED = (contract.BASE_GEOMETRY_PATH, "config/scenario.default.json")

    def setUp(self) -> None:
        for relative in self.REQUIRED:
            if not (PROJECT_ROOT / relative).is_file():
                self.skipTest(f"缺 {relative}")
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        for relative in self.REQUIRED:
            self._copy(relative)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _copy(self, relative: str, destination: str | None = None) -> None:
        target = self.root / (destination or relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT_ROOT / relative, target)

    def _place_frames(self, unit: str, truth_dir: str | None, limit: int) -> list[str]:
        """复制归档真实帧、sidecar 与（逐帧 schema 的）真值，返回帧相对路径。"""
        sources = sorted((PROJECT_ROOT / unit / "frames").glob("frame_*.jpg"))
        if not sources:
            self.skipTest(f"真实归档不在本工作副本中：{unit}")
        placed: list[str] = []
        for source in sources:
            if len(placed) >= limit:
                break
            relative = f"{unit}/frames/{source.name}"
            if truth_dir is not None:
                truth = PROJECT_ROOT / truth_dir / f"{source.stem}.json"
                if not truth.is_file():
                    continue  # 逐帧真值部分覆盖是归档常态
                self._copy(f"{truth_dir}/{source.stem}.json")
            self._copy(relative)
            self._copy(f"{unit}/frames/{source.stem}.json")
            placed.append(relative)
        return placed

    def _inventory(self, frames: list[str], family: str, layout_class: str) -> dict:
        return {
            "stage": 1,
            "record_count": len(frames),
            "records": [
                {
                    "path": relative,
                    "kind": "image",
                    "decision": "INCLUDED",
                    "family": family,
                    "layout_class": layout_class,
                    "usage_class": "VALID_FORMAL",
                    "sidecar_join": {"present": True, "complete": True},
                    "truth_join": {"source": None, "schema_family": None},
                }
                for relative in frames
            ],
        }

    def _build_layout(self, frames: list[str], family: str, layout_class: str) -> dict:
        return bind_layout.build_layout(
            self.root,
            "attempt-1",
            inventory=self._inventory(frames, family, layout_class),
        )


class CrossValidationTest(ArchiveS2Case):
    def test_s2_cross_validation_invalidates_shifted_static_layout_and_reports_it(
        self,
    ) -> None:
        """§2.3 的历史交叉验证必须在生产 S2 真的发生，并能否决整个 partition。

        两个变量只有 `scenario_config.json` 这一格的归档字节：放该采集**自己**的
        场景 → 几何与真值同源；放 scene-004 的 hold → 几何被整体改过。帧、
        sidecar、distractor 真值三者在两种情形下**逐字节相同**。
        """
        frames = self._place_frames(SCOUT1_UNIT, SCOUT1_TRUTH, limit=140)
        if len(frames) < 60:
            self.skipTest("归档帧不足以凑满 50 对")

        self._copy(SCENE004_HOLD, destination=SCOUT1_SNAPSHOT)
        shifted = self._build_layout(frames, "detect-scout1", "default")
        self.assertIn("cross_validation", shifted, "BC-DATA-23 (5)：必有成员")
        # partition id 含 scenario SHA，两次构建的 id 因此不同——正是
        # BC-DATA-23 (2)「决定单位 = 精确 (family, scenario_sha256)」的体现。
        (shifted_id,) = list(shifted["scenario_partitions"])
        entry = shifted["cross_validation"][shifted_id]
        self.assertEqual(entry["mode"], "scouting")
        self.assertEqual(entry["status"], bind_layout.BINDING_INVALID)
        self.assertTrue(entry["reason"])
        self.assertEqual(entry["pair_count"], 50)
        self.assertEqual(entry["center_hit_ratio"], 0.0)
        self.assertEqual(entry["iou_median"], 0.0)
        # 验证失败必须同步否决该 partition 的绑定状态。
        self.assertEqual(
            shifted["scenario_partitions"][shifted_id]["binding_status"],
            bind_layout.BINDING_INVALID,
        )

        # 换回同源场景：同一批帧/真值，几何一致，IoU 中位数应贴近 1。
        self._copy(SCOUT1_SNAPSHOT)
        matched = self._build_layout(frames, "detect-scout1", "default")
        (matched_id,) = list(matched["scenario_partitions"])
        self.assertNotEqual(matched_id, shifted_id)
        matched_entry = matched["cross_validation"][matched_id]
        self.assertEqual(matched_entry["mode"], "scouting")
        self.assertEqual(matched_entry["pair_count"], 50)
        self.assertGreater(matched_entry["iou_median"], 0.99)
        self.assertGreater(matched_entry["center_hit_ratio"], entry["center_hit_ratio"])

    def test_s2_cross_validation_clips_projection_to_archived_viewport_domain(
        self,
    ) -> None:
        """BC-DATA-24 (1)：同源几何在裁剪域必须通过，错配对照仍须 INVALID。

        归档真值框裁在图像内；跑出画面下沿的车辆，其 amodal 预测框中心会掉到
        裁剪真值框外，于是 IoU ≈ 0.99999 却被判 centre miss（证据 §16.5）。
        本用例走生产 S2、消费归档帧/sidecar/truth 字节副本，钉死这一域。
        """
        frames = self._place_frames(SCOUT1_UNIT, SCOUT1_TRUTH, limit=140)
        if len(frames) < 60:
            self.skipTest("归档帧不足以凑满 50 对")

        # 同源几何：裁剪域下必须通过，且样本里确实含下沿被截断的对。
        self._copy(SCOUT1_SNAPSHOT)
        matched = self._build_layout(frames, "detect-scout1", "default")
        (matched_id,) = list(matched["scenario_partitions"])
        entry = matched["cross_validation"][matched_id]
        self.assertEqual(entry["mode"], "scouting")
        self.assertEqual(entry["pair_count"], 50)
        self.assertEqual(entry["center_hit_ratio"], 1.0)
        self.assertGreater(entry["iou_median"], 0.99)
        self.assertEqual(entry["status"], bind_layout.BINDING_BOUND)
        self.assertEqual(
            matched["scenario_partitions"][matched_id]["binding_status"],
            bind_layout.BINDING_BOUND,
        )
        # 夹具里确有「amodal 超出下沿、裁剪后才同域」的样本——否则本用例
        # 会在一批完全在画面内的对上空过，证明不了裁剪。
        self.assertTrue(
            self._has_bottom_truncated_pair(frames, matched_id, matched),
            "夹具需含下沿截断样本，否则裁剪域未被真正检验",
        )

        # 错配几何对照：裁剪**不得**把真正的场景漂移救回来。
        self._copy(SCENE004_HOLD, destination=SCOUT1_SNAPSHOT)
        shifted = self._build_layout(frames, "detect-scout1", "default")
        (shifted_id,) = list(shifted["scenario_partitions"])
        shifted_entry = shifted["cross_validation"][shifted_id]
        self.assertEqual(shifted_entry["status"], bind_layout.BINDING_INVALID)
        self.assertEqual(shifted_entry["center_hit_ratio"], 0.0)
        self.assertEqual(shifted_entry["iou_median"], 0.0)

    def _has_bottom_truncated_pair(
        self, frames: list[str], identifier: str, layout: dict
    ) -> bool:
        """夹具里是否真有 amodal 框越过视口下沿的可检对。"""
        instances = layout["scenario_partitions"][identifier]["instances"]
        by_name = {item["scene_object_name"]: item for item in instances}
        for relative in frames:
            row, _schema = bind_layout.load_frame_truth(self.root, relative)
            if row is None:
                continue
            camera = bind_layout._camera_for_frame(self.root, relative)
            for item in row.get("distractors") or []:
                instance = by_name.get(item.get("distractor_id"))
                if instance is None:
                    continue
                amodal = project_boxes.project_aabb(camera, instance)
                if amodal is not None and amodal[3] > camera.viewport()[3]:
                    return True
        return False

    def test_s2_partial_truth_absence_skips_missing_frames_without_masking_corruption(
        self,
    ) -> None:
        """BC-DATA-24 (3)(4)：正常缺帧只是无观测；坏字节仍须 fail-closed。"""
        frames = self._place_frames(SCOUT1_UNIT, SCOUT1_TRUTH, limit=140)
        if len(frames) < 60:
            self.skipTest("归档帧不足以凑满 50 对")
        self._copy(SCOUT1_SNAPSHOT)

        # (3) 删掉一部分**逐帧真值文件**（帧与 sidecar 原样保留）：剩余样本仍
        # 满足冻结门时，partition 不得因缺席被否决，也不得降级成 NOT_APPLICABLE。
        truth_files = sorted((self.root / SCOUT1_TRUTH).glob("frame_*.json"))
        self.assertGreater(len(truth_files), 60)
        for path in truth_files[: len(truth_files) // 3]:
            path.unlink()
        partial = self._build_layout(frames, "detect-scout1", "default")
        (identifier,) = list(partial["scenario_partitions"])
        entry = partial["cross_validation"][identifier]
        self.assertEqual(entry["mode"], "scouting", "缺席不得变成 NOT_APPLICABLE")
        self.assertEqual(entry["pair_count"], 50)
        self.assertEqual(entry["status"], bind_layout.BINDING_BOUND)

        # (4) 把一个**实际存在**的归档 truth 字节副本破坏 → 必须 fail-closed。
        remaining = sorted((self.root / SCOUT1_TRUTH).glob("frame_*.json"))
        remaining[0].write_bytes(b"{not json")
        corrupted = self._build_layout(frames, "detect-scout1", "default")
        corrupted_entry = corrupted["cross_validation"][identifier]
        self.assertEqual(corrupted_entry["status"], bind_layout.BINDING_INVALID)
        self.assertIn("不可解析", corrupted_entry["reason"])
        self.assertEqual(
            corrupted["scenario_partitions"][identifier]["binding_status"],
            bind_layout.BINDING_INVALID,
        )

    def test_s2_m3_target_check_uses_center_ratio_without_static_pair_backfill(
        self,
    ) -> None:
        """m3 只走 `target_world_*_m` 中心落框率，且**不拿它补静态 50 对**。"""
        frames = self._place_frames(M3_UNIT, None, limit=40)
        if not (PROJECT_ROOT / M3_TRUTH).is_file():
            self.skipTest("m3 归档真值不在本工作副本中")
        self._copy(M3_TRUTH)
        self._copy(M3_SNAPSHOT)
        layout = self._build_layout(frames, "m3-armA", "default")
        (identifier,) = list(layout["scenario_partitions"])
        entry = layout["cross_validation"][identifier]
        self.assertEqual(entry["mode"], "m3", entry)
        # 关键：m3 分支**不产生**静态对，也不得用 target 去凑够 50。
        self.assertEqual(entry["pair_count"], 0)
        self.assertGreater(entry["sample_count"], 0)
        self.assertIsNone(entry["iou_median"], "m3 不算 target IoU")
        self.assertIsNotNone(entry["center_hit_ratio"])
        expected = (
            bind_layout.BINDING_BOUND
            if entry["center_hit_ratio"] >= 0.9
            else bind_layout.BINDING_INVALID
        )
        self.assertEqual(entry["status"], expected)


class PreflightTest(unittest.TestCase):
    """只读 preflight（接受轮 14 §26.2 (e)）：跑完整 S1 + S2，一个字节不写。"""

    @staticmethod
    def _seed(root: Path) -> None:
        """把 S0 钉死的基础几何与 default 前提字节按真实相对路径复制进临时根。"""
        for relative in (contract.BASE_GEOMETRY_PATH, "config/scenario.default.json"):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT_ROOT / relative, target)

    def test_preflight_runs_the_full_s2_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root)
            report = run_pipeline.PipelineDriver(root).preflight()
            self.assertTrue(report["wrote_nothing"])
            self.assertFalse(report["artifact_root_existed_before"])
            self.assertFalse(report["artifact_root_exists_after"])
            self.assertFalse((root / contract.ARTIFACT_ROOT).exists())
            # 空归档：零记录、零 partition，但 S2 的几何派生确实跑过了
            # （否则 `instances`/`phantoms` 只能是假精度的 0）。
            self.assertEqual(report["records"], 0)
            self.assertEqual(report["partitions"], [])

    def test_preflight_fails_closed_without_the_pinned_base_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(bind_layout.LayoutError):
                run_pipeline.PipelineDriver(root).preflight()
            self.assertFalse((root / contract.ARTIFACT_ROOT).exists())

    def test_tests_never_write_the_formal_artifact_root(self) -> None:
        """测试不得写正式输出根（接受轮 14 §26.2 点名）。

        接受轮 20 的限域执行之后该根**合法存在**（S0–S2 三件正式工件），因此
        判据从「根不存在」改为「本次测试进程没有增删改它一个字节」——
        `FORMAL_ROOT_SNAPSHOT` 在模块导入时拍摄，与此刻逐路径逐哈希比对。
        """
        self.assertEqual(_formal_root_snapshot(), FORMAL_ROOT_SNAPSHOT)

    def test_cli_defaults_to_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._seed(Path(tmp))
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = run_pipeline.main(["--repo-root", tmp])
            self.assertEqual(exit_code, 0)
            self.assertIn('"mode": "preflight"', captured.getvalue())
            self.assertFalse((Path(tmp) / contract.ARTIFACT_ROOT).exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
