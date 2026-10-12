"""S0–S8 单向 DAG 的端到端组合（合成世界；不触碰真实归档，不生成正式工件）。

本用例把每个阶段的载荷经 `ArtifactStore` 落成 create-once 工件，验证：
阶段间只允许「读更早或同阶段」、重跑字节幂等、门不达下限时 S8 拒绝执行。
合成世界规模远小于 §5.2 的冻结下限，因此门**应当**关闭——这正是要断言的
行为，不是缺陷。
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dist_data import (  # noqa: E402
    artifacts,
    audit_tool,
    build_catalog,
    contract,
    g0_report,
    gen_mother_templates,
    make_splits,
    tier1_lang,
)


def make_sidecar(position, forward) -> dict:
    return {
        "camera_position_world_m": list(position),
        "camera_right_world": [1.0, 0.0, 0.0],
        "camera_up_world": [0.0, forward[2], -forward[1]],
        "camera_forward_world": list(forward),
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


LAYOUTS = {
    "default": [body("Vehicle_Taxi", 0.0, 20.0), body("Vehicle_Bus_color01", 8.0, 24.0)],
    "scene-004": [
        body("Vehicle_Car_color01", 0.0, 20.0),
        body("Vehicle_SUV_color01", 8.0, 24.0),
    ],
}
FAMILY_LAYOUT = {"famA": "default", "famB": "scene-004"}


class _StubPixels:
    COLOURS = {
        "Vehicle_Taxi": (255, 230, 0),
        "Vehicle_Bus_color01": (0, 0, 255),
        "Vehicle_Car_color01": (255, 0, 0),
        "Vehicle_SUV_color01": (0, 200, 0),
    }

    def crop_rgb(self, frame_id, box_px):  # noqa: ANN001
        return [self.COLOURS[frame_id.split("@", 1)[1]]] * 10


class PipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.store = artifacts.ArtifactStore(self.root)
        self.entries = self._build_entries()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # --- S3 -----------------------------------------------------------------
    def _build_entries(self) -> list[dict]:
        entries: list[dict] = []
        for family, layout_class in FAMILY_LAYOUT.items():
            for index in range(4):
                frame = build_catalog.FrameInput(
                    frame_id=f"{family}/frame-{index}",
                    sidecar=make_sidecar((index * 3.0, 10.0, 0.0), (0.0, -0.5, 0.8660254)),
                    family=family,
                    layout_class=layout_class,
                    usage_class="VALID_FORMAL",
                    layout_binding_valid=True,
                    sidecar_complete=True,
                    truth_schema="m3",
                    truth_row={
                        "truth_box_available": False,
                        "intersects_frustum": False,
                        "geometrically_visible": False,
                    },
                )
                entries.append(
                    build_catalog.build_frame_entry(
                        frame, LAYOUTS[layout_class], [], (1.0, 1.0, 2.0)
                    )
                )
        return entries

    def test_s3_entries_are_create_once_and_idempotent(self) -> None:
        payload = {"stage": 3, "entries": self.entries}
        first = self.store.write("frames_catalog", "attempt-1", payload)
        second = self.store.write("frames_catalog", "attempt-1", payload)
        self.assertEqual(first.sha256, second.sha256)

    def test_s3_cannot_read_s4(self) -> None:
        self.store.write("splits", "attempt-1", {"stage": 4})
        with self.assertRaises(artifacts.ForbiddenEdgeError):
            self.store.read("splits", "attempt-1", requesting_stage=3)

    # --- S4 -----------------------------------------------------------------
    def _splits(self) -> dict:
        atoms = []
        for family, layout_class in FAMILY_LAYOUT.items():
            frames = [
                entry["frame_id"]
                for entry in self.entries
                if entry["family"] == family
                and build_catalog.pre_split_floor_eligible(entry)
            ]
            atoms.append(
                make_splits.AtomSummary(
                    atom_id=make_splits.atom_id_for([family]),
                    families=[family],
                    layout_classes=[layout_class],
                    floor_eligible_frames=frames,
                )
            )
        # S4 从 catalog 记录内部装配逐 sample 角色，驱动无从漏传（F11）。
        return make_splits.assign_splits(atoms, self.entries)

    def test_s4_assignment_is_leak_free_and_persisted(self) -> None:
        payload = self._splits()
        self.assertTrue(payload["leakage_assertions"]["pairwise_disjoint"])
        reference = self.store.write("splits", "attempt-1", payload)
        stored, _ = self.store.read("splits", "attempt-1", requesting_stage=7)
        self.assertEqual(stored["atom_assignment"], payload["atom_assignment"])
        self.assertEqual(len(reference.sha256), 64)

    # --- F11（复核轮 2）：角色装配必须在唯一端到端驱动上真的生效 -------------
    def test_splits_artifact_carries_assembled_sample_roles(self) -> None:
        """catalog 非空时 splits 工件必须自带逐 sample 角色与四集 exposure 汇总。

        BC-DATA-2 / BC-DATA-19：成员名存在不等于生产路径上被装配。本用例断言的是
        **本文件这条唯一端到端驱动**的落盘载荷，不是装配器的单测。
        """
        self.assertTrue(self.entries, "前提：合成 catalog 非空")
        payload = self._splits()
        self.assertTrue(
            payload["sample_roles"],
            "catalog 非空时 sample_roles 不得为空（BC-DATA-2/19）",
        )
        self.assertTrue(
            payload["exposure_matrix"]["per_object"],
            "catalog 非空时 exposure_matrix.per_object 不得为空（BC-DATA-2/19）",
        )
        for record in payload["sample_roles"]:
            self.assertIn(record["split"], make_splits.SPLITS)
            self.assertIn(record["role"], ("referent", "distractor", "absent"))
        # 落盘后仍在载荷里：不靠 G0 报告补。
        self.store.write("splits", "attempt-1", payload)
        stored, _ = self.store.read("splits", "attempt-1", requesting_stage=7)
        self.assertEqual(stored["sample_roles"], payload["sample_roles"])
        self.assertEqual(stored["exposure_matrix"], payload["exposure_matrix"])

    def test_g0_report_exposure_comes_from_the_splits_payload(self) -> None:
        """G0 报告的 exposure 必须来自同一 splits 载荷，不是旁路构造的空表。"""
        splits = self._splits()
        _, report = self._frozen_and_report()
        self.assertTrue(report["exposure_matrix"]["per_object"])
        self.assertEqual(report["exposure_matrix"], splits["exposure_matrix"])

    # --- S5 / S6 ------------------------------------------------------------
    def _field_catalog(self) -> dict:
        observations = []
        object_ids: set[str] = set()
        for entry in self.entries:
            for item in entry["objects"]:
                if item["status"] != "OK":
                    continue
                object_ids.add(item["object_id"])
                observations.append(
                    build_catalog.ObjectObservation(
                        f"{entry['frame_id']}@{item['object_id']}",
                        item["object_id"],
                        tuple(item["visible_px"]),
                        item["camera_depth_m"],
                    )
                )
        return build_catalog.build_field_catalog(
            sorted(object_ids), observations, _StubPixels()
        )

    def test_s5_verifies_class_and_colour(self) -> None:
        catalog = self._field_catalog()
        self.assertTrue(catalog["objects"])
        for record in catalog["objects"].values():
            self.assertTrue(record["class_verified"])
        self.assertTrue(catalog["dual_verified_object_ids"])

    def test_s6_downgrade_only_removes_fields(self) -> None:
        catalog = self._field_catalog()
        first_object = sorted(catalog["objects"])[0]
        group = catalog["objects"][first_object]["group_key"]
        downgraded = build_catalog.apply_audit_downgrades(catalog, [group])
        self.assertNotIn(first_object, downgraded["dual_verified_object_ids"])
        self.assertEqual(set(downgraded["objects"]), set(catalog["objects"]))
        result = audit_tool.evaluate_a1(0, [True] * 20, [True] * 25, [group])
        self.assertEqual(result["verdict"], "PASS")  # 组级降级是数据结论，不是失败

    # --- S7 -----------------------------------------------------------------
    def _frozen_and_report(self):
        splits = self._splits()
        catalog = self._field_catalog()
        split_of_frame = {
            frame: split
            for split, frames in splits["frames"].items()
            for frame in frames
        }
        atom_of_frame = {
            entry["frame_id"]: make_splits.atom_id_for([entry["family"]])
            for entry in self.entries
        }
        candidates = []
        for entry in self.entries:
            entry["split"] = split_of_frame.get(entry["frame_id"])
            world = build_catalog.frame_world(entry, catalog)
            for object_id in entry["referable"]:
                candidate = build_catalog.prospective_mother_eligible(
                    entry, object_id, world, catalog
                )
                if candidate is not None:
                    candidates.append(candidate)
        frozen = g0_report.freeze_mother_candidates(
            candidates, split_of_frame, atom_of_frame, []
        )
        report = g0_report.build_g0_report(
            entries=self.entries,
            frozen=frozen,
            field_catalog=catalog,
            splits_payload=splits,
            # BC-DATA-23 (5)：交叉验证结果是 layout 的必有成员；合成世界无归档
            # 逐帧真值，故状态是 NOT_APPLICABLE 而不是「空表」。
            layout_payload={
                "cross_validation": {
                    "synthetic|sha": {
                        "mode": "none",
                        "status": "NOT_APPLICABLE_NO_ARCHIVED_FRAME_TRUTH",
                        "reason": "合成世界无归档逐帧真值",
                        "pair_count": 0,
                        "sample_count": 0,
                    }
                }
            },
            audit_results={},
            relation_availability={},
        )
        return frozen, report

    def test_s7_freezes_candidates_and_closes_the_gate(self) -> None:
        frozen, report = self._frozen_and_report()
        self.assertGreater(frozen["candidate_count"], 0)
        # 合成世界远小于冻结下限 → 门必须关闭，且不得因实测结果回调下限。
        self.assertEqual(report["gate"], g0_report.GATE_INSUFFICIENT)
        self.assertTrue(report["unmet_floors"])
        self.assertEqual(report["floors"]["F1"]["floor"]["min_objects"], 60)

    def test_s7_artifacts_persist_and_forbid_reading_s8(self) -> None:
        frozen, report = self._frozen_and_report()
        self.store.write("mother_candidates", "attempt-1", frozen)
        self.store.write("g0_report", "attempt-1", report)
        self.store.write("mother_set", "attempt-1", {"stage": 8})
        # S7 可以读同阶段的 mother_candidates，但绝不能读 S8。
        self.store.read("mother_candidates", "attempt-1", requesting_stage=7)
        with self.assertRaises(artifacts.ForbiddenEdgeError):
            self.store.read("mother_set", "attempt-1", requesting_stage=7)

    # --- S8 -----------------------------------------------------------------
    def test_s8_refuses_to_run_behind_a_closed_gate(self) -> None:
        frozen, report = self._frozen_and_report()
        boxes = {item["candidate_id"]: [0.0, 0.0, 0.1, 0.1] for item in frozen["candidates"]}
        with self.assertRaises(gen_mother_templates.MotherSetError):
            gen_mother_templates.build_d0(frozen, report, boxes, [])

    def test_s8_materialises_when_the_gate_is_open(self) -> None:
        frozen, _ = self._frozen_and_report()
        boxes = {item["candidate_id"]: [0.0, 0.0, 0.1, 0.1] for item in frozen["candidates"]}
        payload = gen_mother_templates.build_d0(
            frozen, {"gate": g0_report.GATE_OPEN, "unmet_floors": []}, boxes, []
        )
        self.assertEqual(payload["mother_set"]["count"], frozen["candidate_count"])
        for expression in payload["template_expressions"]["expressions"]:
            self.assertEqual(
                tier1_lang.canonical_ast(tier1_lang.parse(expression["expression"])),
                expression["canonical_ast"],
            )
        reference = self.store.write("mother_set", "attempt-1", payload["mother_set"])
        self.assertEqual(
            reference.sha256,
            self.store.write("mother_set", "attempt-1", payload["mother_set"]).sha256,
        )

    # --- S0 -----------------------------------------------------------------
    def test_contract_artifact_is_stable(self) -> None:
        first = contract.write_contract(self.root)
        second = contract.write_contract(self.root)
        self.assertEqual(first.sha256, second.sha256)
        payload, _ = self.store.read("contract", "attempt-1", requesting_stage=8)
        self.assertEqual(payload["floors"]["F4"]["min_test"], 10)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
