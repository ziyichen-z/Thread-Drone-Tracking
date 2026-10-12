"""Tests for tools/scene006_candidate_check.py (P1-SCENE-006 batch 1b)."""

import json
import os
from pathlib import Path
import tempfile
import unittest

from tools.scene006_candidate_check import (
    ALTITUDES,
    VFOVS,
    CheckFailure,
    check_p1,
    check_p2,
    check_route_audit,
    quantile_type7,
)

CAPTURE = {
    "capture_commit": "abc123",
    "tool_commit": "abc123",
    "git_status_porcelain": "",
    "scene_state_sha256": "deadbeef",
    "scene_file_sha256_before": "cafe",
    "scene_file_sha256_after": "cafe",
    "scene_saved": False,
}

GRID_ANCHORS = [(150.0, 108.0), (148.0, 108.0)]


def _candidate(x, z, legal):
    return {
        "rank": 0,
        "x_m": x,
        "y_m": 0.0,
        "z_m": z,
        "center_distance_m": 0.0,
        "support_ids": ["grass"],
        "support_surface_y_m": 0.0,
        "support_status": "PASS",
        "clearance_status": "PASS" if legal else "FAIL",
        "scene003_rejection_reason": "",
        "blocking_object": "",
        "route_distance_m": 8.0,
        "route_gate_status": "PASS",
        "rejection_reason": "" if legal else "CLEARANCE_INTERSECTION",
        "legal": legal,
    }


def _p1_artifact(legal_altitudes=(20.0,)):
    grid = []
    for ax, az in GRID_ANCHORS:
        grid.append({
            "x_m": ax,
            "z_m": az,
            "support_y_m": 0.0,
            "legal_altitudes_m": list(legal_altitudes),
        })
    altitudes = []
    for altitude in ALTITUDES:
        candidates = []
        for index in range(1257):
            ax, az = GRID_ANCHORS[index % 2]
            legal = index < 2 and altitude in legal_altitudes
            candidates.append(_candidate(
                ax if index < 2 else 140.0 + index * 0.001, az, legal))
        legal_count = sum(1 for c in candidates if c["legal"])
        altitudes.append({
            "altitude_m": altitude,
            "report": {
                "mode": "candidate_preflight",
                "status": "CANDIDATES_AVAILABLE",
                "candidate_count": len(candidates),
                "support_rejection_count": 0,
                "clearance_rejection_count": len(candidates) - legal_count,
                "route_rejection_count": 0,
                "legal_candidate_count": legal_count,
                "candidates": candidates,
            },
        })
    return {
        "schema_version": "p1-scene-006-p1/v1",
        "family": "A",
        "status": "P1_OK",
        "capture": dict(CAPTURE),
        "grid_anchors": grid,
        "altitudes": altitudes,
    }


def _cell(altitude, vfov, domain, l_point, l_occ):
    c_frustum = 1.0 - l_point
    c_geom = c_frustum - l_occ
    total = 1.0 - c_geom
    t2 = 0.10 <= l_point <= 0.50
    t3 = 0.05 <= l_occ <= 0.40 and 0.15 <= total <= 0.60
    t1 = bool(domain) and quantile_type7(domain, 0.05) >= 25.0
    return {
        "family": "A",
        "anchor_x_m": 150.0,
        "anchor_z_m": 108.0,
        "support_y_m": 0.0,
        "initial_altitude_m": altitude,
        "vertical_fov_deg": vfov,
        "s_init": 24.5,
        "trace_sha256": "aa",
        "trace_artifact": "trace.json",
        "trace_first_lap_steps": 482,
        "terminal": "",
        "t1_domain_count": len(domain),
        "t1_min_side_p05_px": quantile_type7(domain, 0.05) if domain else float("nan"),
        "t1_min_side_median_px": quantile_type7(domain, 0.5) if domain else float("nan"),
        "t1_min_side_min_px": min(domain) if domain else float("nan"),
        "t1_min_side_max_px": max(domain) if domain else float("nan"),
        "t1_domain_min_sides_px": domain,
        "c_frustum": c_frustum,
        "l_point": l_point,
        "t2_gate": "PASS" if t2 else "FAIL",
        "c_geom": c_geom,
        "l_occ": l_occ,
        "total_loss": total,
        "t3_gate": "PASS" if t3 else "FAIL",
        "gates_in_band": t1 and t2 and t3,
        "occluded_ticks": [
            {"k": 7, "t_s": 1.4, "frustum_sample_count": 15,
             "visible_sample_count": 9, "blocking_roots": ["Building_X"]},
        ] if l_occ > 0 else [],
    }


def _p2_artifact(legal_altitudes=(20.0,), domain=None, l_point=0.3,
                 l_occ=0.2):
    domain = domain if domain is not None else [30.0] * 400
    cells = [
        _cell(altitude, vfov, domain, l_point, l_occ)
        for altitude in legal_altitudes
        for vfov in VFOVS
    ]
    in_band = sum(1 for c in cells if c["gates_in_band"])
    return {
        "schema_version": "p1-scene-006-p2/v1",
        "family": "A",
        "status": "P2_OK" if in_band else "BLOCKED_GEOMETRY_INFEASIBLE",
        "capture": dict(CAPTURE),
        "in_band_cell_count": in_band,
        "evaluated_cell_count": len(cells),
        "anchors": [
            {
                "anchor_x_m": 150.0,
                "anchor_z_m": 108.0,
                "support_y_m": 0.0,
                "s_init": 24.5,
                "s_init_altitude_consistent": True,
                "trace_artifact": "trace.json",
                "trace_sha256": "aa",
                "trace_first_lap_steps": 482,
                "first_lap_status": "MEASURED",
                "legal_altitudes_m": list(legal_altitudes),
                "cells": cells,
            },
        ],
    }


def _route_audit(status="CLEAR"):
    row = {
        "prefab_name": "Vehicle_Taxi",
        "recompute_match": True,
        "landing_road_coverage": True,
        "landing_static_clearance": True,
    }
    return {
        "schema_version": "p1-scene-006-familyb-route-audit/v1",
        "status": status,
        "capture": dict(CAPTURE),
        "relocations": [dict(row) for _ in range(5)],
        "road_violation_count": 0,
        "obstacle_violation_count": 0,
        "corridor_violation_count": 0,
    }


class Scene006CandidateCheckTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.dir.cleanup()

    def _write(self, name, artifact):
        path = os.path.join(self.dir.name, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(artifact, handle)
        return path

    def test_quantile_type7_matches_reference_values(self):
        self.assertAlmostEqual(1.15, quantile_type7([1, 2, 3, 4], 0.05))
        self.assertAlmostEqual(2.5, quantile_type7([1, 2, 3, 4], 0.5))
        self.assertAlmostEqual(3.85, quantile_type7([1, 2, 3, 4], 0.95))
        self.assertEqual(7.0, quantile_type7([7], 0.05))

    def test_valid_p1_passes(self):
        summary = check_p1(self._write("p1.json", _p1_artifact()))
        self.assertEqual("P1_OK", summary["status"])
        self.assertEqual(2, summary["legal_pairs"])

    def test_p1_legal_boolean_must_match_empty_string_convention(self):
        artifact = _p1_artifact()
        # A legal candidate with a non-empty rejection reason violates F4.
        # altitudes[1] is 20.0, the legal altitude; candidates[0] is legal.
        bad = artifact["altitudes"][1]["report"]["candidates"][0]
        assert bad["legal"] is True
        bad["rejection_reason"] = "CLEARANCE_INTERSECTION"
        with self.assertRaises(CheckFailure):
            check_p1(self._write("p1.json", artifact))

    def test_p1_count_mismatch_fails(self):
        artifact = _p1_artifact()
        artifact["altitudes"][2]["report"]["legal_candidate_count"] = 99
        with self.assertRaises(CheckFailure):
            check_p1(self._write("p1.json", artifact))

    def test_valid_p2_passes_and_recomputes_gates(self):
        p1_path = self._write("p1.json", _p1_artifact())
        summary = check_p2(
            self._write("p2.json", _p2_artifact()), p1_path)
        self.assertEqual(5, summary["in_band"])
        self.assertEqual(5, summary["cells"])

    def test_p2_tampered_p05_fails(self):
        artifact = _p2_artifact()
        artifact["anchors"][0]["cells"][0]["t1_min_side_p05_px"] = 999.0
        with self.assertRaises(CheckFailure):
            check_p2(self._write("p2.json", artifact))

    def test_p2_tampered_gate_fails(self):
        artifact = _p2_artifact()
        artifact["anchors"][0]["cells"][0]["t2_gate"] = "FAIL"
        with self.assertRaises(CheckFailure):
            check_p2(self._write("p2.json", artifact))

    def test_p2_grid_divergence_from_p1_fails(self):
        p1_path = self._write("p1.json", _p1_artifact(
            legal_altitudes=(16.0, 20.0)))
        with self.assertRaises(CheckFailure):
            check_p2(self._write("p2.json", _p2_artifact()), p1_path)

    def test_route_audit_status_consistency(self):
        self.assertEqual(
            "CLEAR",
            check_route_audit(self._write("audit.json", _route_audit()))[
                "status"])
        mismatch = _route_audit(status="RELOCATION_RECOMPUTE_MISMATCH")
        mismatch["relocations"][2]["recompute_match"] = False
        self.assertEqual(
            "RELOCATION_RECOMPUTE_MISMATCH",
            check_route_audit(self._write("audit.json", mismatch))["status"])
        # CLEAR with a mismatching row must fail.
        bad = _route_audit()
        bad["relocations"][0]["recompute_match"] = False
        with self.assertRaises(CheckFailure):
            check_route_audit(self._write("audit.json", bad))

    def test_capture_identity_checked(self):
        artifact = _p2_artifact()
        artifact["capture"]["git_status_porcelain"] = " M dirty"
        with self.assertRaises(CheckFailure):
            check_p2(self._write("p2.json", artifact))

    def test_trace_artifact_requires_capture_identity(self):
        from tools.scene006_candidate_check import check
        fixture = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
            "scene006-trace-v2-sample.json",
        )
        with open(fixture, "r", encoding="utf-8") as handle:
            artifact = json.load(handle)
        # §5.6 (B1B-R1): a trace artifact without the capture identity
        # fails closed even when its hash recomputes.
        with self.assertRaises(CheckFailure):
            check(self._write("trace.json", artifact))
        artifact["capture"] = dict(CAPTURE)
        artifact["capture"]["capture_commit"] = "abc123"
        summary = check(self._write("trace.json", artifact))
        self.assertTrue(summary["match"])
        # capture_commit != tool_commit is rejected for batch 1b.
        artifact["capture"]["tool_commit"] = "def456"
        with self.assertRaises(CheckFailure):
            check(self._write("trace.json", artifact))

    @unittest.skipUnless(
        os.path.exists("docs/evidence/P1-SCENE-006-p2-familyA.json"),
        "batch-1b artifacts not captured yet",
    )
    def test_real_batch1b_artifacts_pass(self):
        from tools.scene006_candidate_check import check
        for name in os.listdir("docs/evidence"):
            if name.startswith("P1-SCENE-006-") and (
                "p1-family" in name
                or "p2-family" in name
                or "familyb-route-audit" in name
                or "trace-A" in name
                or "trace-B" in name
            ):
                if "p2-family" in name:
                    # F8(b): exercise the P1 cross-checks on real artifacts.
                    family = name.rsplit("family", 1)[1][0]
                    check(
                        os.path.join("docs/evidence", name),
                        p1_path=os.path.join(
                            "docs/evidence",
                            f"P1-SCENE-006-p1-family{family}.json",
                        ),
                    )
                else:
                    check(os.path.join("docs/evidence", name))


class Scene006P3CheckTests(unittest.TestCase):
    """P3 (batch-1c) artifact checks: selection recompute, BC-B1C-2 support
    binding, T5 recheck binding and T4/T6 gate arithmetic."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def _write(self, name, value):
        path = os.path.join(self.directory.name, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(value, handle)
        return path

    # The three reviewed batch-1b in-band cells (unrounded values from the
    # P2 artifact at 77595c8).
    CELLS = [
        {"anchor_x_m": 195.0, "anchor_z_m": 30.0,
         "initial_altitude_m": 20.0, "vertical_fov_deg": 40.0,
         "l_point": 0.33888888359069824, "l_occ": 0.0574074387550354,
         "total_loss": 0.39629632234573364,
         "t1_min_side_p05_px": 37.06139373779297},
        {"anchor_x_m": 197.0, "anchor_z_m": 30.0,
         "initial_altitude_m": 16.0, "vertical_fov_deg": 35.0,
         "l_point": 0.5, "l_occ": 0.05370369553565979,
         "total_loss": 0.5537036657333374,
         "t1_min_side_p05_px": 30.289955139160156},
        {"anchor_x_m": 197.0, "anchor_z_m": 30.0,
         "initial_altitude_m": 16.0, "vertical_fov_deg": 40.0,
         "l_point": 0.44074076414108276, "l_occ": 0.06481480598449707,
         "total_loss": 0.5055555701255798,
         "t1_min_side_p05_px": 35.14252471923828},
    ]

    def _p2_doc(self):
        cells = []
        for cell in self.CELLS:
            c_frustum = 1.0 - cell["l_point"]
            c_geom = c_frustum - cell["l_occ"]
            cells.append({
                "family": "B",
                "anchor_x_m": cell["anchor_x_m"],
                "anchor_z_m": cell["anchor_z_m"],
                "initial_altitude_m": cell["initial_altitude_m"],
                "vertical_fov_deg": cell["vertical_fov_deg"],
                "s_init": 184.22793579101562,
                "trace_sha256": "46036a6c" + "0" * 56,
                "trace_artifact": "docs/evidence/P1-SCENE-006-trace-B.json",
                "terminal": "",
                "t1_min_side_p05_px": cell["t1_min_side_p05_px"],
                "t1_min_side_median_px": 30.0,
                "c_frustum": c_frustum,
                "l_point": cell["l_point"],
                "c_geom": c_geom,
                "l_occ": cell["l_occ"],
                "total_loss": cell["total_loss"],
                "gates_in_band": True,
            })
        return {
            "schema_version": "p1-scene-006-p2/v1",
            "family": "B",
            "status": "P2_OK",
            "capture": dict(CAPTURE),
            "in_band_cell_count": 3,
            "anchors": [{
                "anchor_x_m": 195.0, "anchor_z_m": 30.0,
                "legal_altitudes_m": [16.0, 20.0],
                "cells": [cells[0]],
            }, {
                "anchor_x_m": 197.0, "anchor_z_m": 30.0,
                "legal_altitudes_m": [16.0, 20.0],
                "cells": [cells[1], cells[2]],
            }],
        }

    def _p1_doc(self):
        altitudes = []
        for altitude in (16.0, 20.0):
            candidates = []
            for ax, az in ((195.0, 30.0), (197.0, 30.0)):
                candidates.append({
                    "rank": 0, "x_m": ax, "y_m": 0.0, "z_m": az,
                    "support_ids": ["Natures_Grass Tile (3)"],
                    "support_surface_y_m": 0.0,
                    "support_status": "PASS", "clearance_status": "PASS",
                    "route_gate_status": "PASS", "rejection_reason": "",
                    "legal": True,
                })
            altitudes.append({
                "altitude_m": altitude,
                "report": {
                    "anchor_contract_sha256": "ab" * 32,
                    "candidates": candidates,
                },
            })
        return {
            "schema_version": "p1-scene-006-p1/v1",
            "family": "B",
            "status": "P1_OK",
            "capture": dict(CAPTURE),
            "grid_anchors": [
                {"x_m": 195.0, "z_m": 30.0,
                 "legal_altitudes_m": [16.0, 20.0]},
                {"x_m": 197.0, "z_m": 30.0,
                 "legal_altitudes_m": [16.0, 20.0]},
            ],
            "altitudes": altitudes,
        }

    def _p3_doc(self, p1_path, p2_path):
        from tools.scene006_candidate_check import (
            _score_cell_margins,
            _sha256_file,
        )
        ranking = []
        for cell in self.CELLS:
            margins = _score_cell_margins({
                "l_point": cell["l_point"], "l_occ": cell["l_occ"],
                "total_loss": cell["total_loss"],
                "t1_min_side_p05_px": cell["t1_min_side_p05_px"],
            })
            row = dict(cell)
            row.update({
                "family": "B",
                "s_init": 184.22793579101562,
                "trace_sha256": "46036a6c" + "0" * 56,
                "terminal": "",
                "anchor_rank": 0,
            })
            row.update(margins)
            ranking.append(row)
        ranking.sort(key=lambda row: -row["score"])
        for index, row in enumerate(ranking):
            row["rank"] = index
        finalist = ranking[0]
        finalist_cell = next(
            cell for cell in self.CELLS
            if cell["anchor_x_m"] == finalist["anchor_x_m"]
            and cell["initial_altitude_m"]
            == finalist["initial_altitude_m"]
            and cell["vertical_fov_deg"] == finalist["vertical_fov_deg"])
        c_geom = 1.0 - finalist_cell["total_loss"]
        stations = [
            {"index": 0, "height_agl_m": 20.0, "is_hover": True,
             "world_m": {"x": 197.0, "y": 16.0, "z": 30.0},
             "certificate": {"passed": True, "path_rejected": False,
                             "body_rejected": False, "tether_rejected": False,
                             "blocking_obstacle": None, "duration_s": 0.0,
                             "sample_count": 1},
             "c_station": 0.6},
            {"index": 1, "height_agl_m": 8.0, "is_hover": False,
             "world_m": {"x": 193.0, "y": 8.0, "z": 30.0},
             "certificate": {"passed": False, "path_rejected": False,
                             "body_rejected": True, "tether_rejected": False,
                             "blocking_obstacle": "Building_Factory",
                             "duration_s": 2.0, "sample_count": 33},
             "c_station": float("nan")},
        ]
        samples = [{
            "k": k,
            "frustum_visible": k == 0,
            "geometrically_visible": k == 0,
            "min_side_px": 40.0 if k == 0 else float("nan"),
        } for k in range(11)]
        return {
            "schema_version": "p1-scene-006-p3/v1",
            "work_id": "P1-SCENE-006",
            "batch": 12,
            "family": "B",
            "capture": dict(CAPTURE),
            "status": "P3_OK",
            "selection": {
                "p1_artifact": {"path": "p1.json",
                                "sha256": _sha256_file(p1_path)},
                "p2_artifact": {"path": "p2.json",
                                "sha256": _sha256_file(p2_path)},
                "ranking": ranking,
                "finalist": finalist,
                "f_count": 3,
            },
            "support_binding": [{
                "anchor_x_m": cell["anchor_x_m"],
                "anchor_z_m": cell["anchor_z_m"],
                "initial_altitude_m": cell["initial_altitude_m"],
                "p1_candidate_rank": 0,
                "p1_legal": True,
                "support_ids": ["Natures_Grass Tile (3)"],
                "single_support": True,
                "grass_allowlist_match": True,
                "p1_p2_binding_consistent": True,
                "ok": True,
                "mismatch": "",
            } for cell in self.CELLS],
            "finalist_trace_s_init": 184.22793579101562,
            "finalist_trace_sha256": "46036a6c" + "0" * 56,
            "finalist_trace_artifact":
                "docs/evidence/P1-SCENE-006-trace-B.json",
            "t5_recheck": {
                "equal": True,
                "divergence": "",
                "p1_contract_sha256": "ab" * 32,
                "recheck_contract_sha256": "ab" * 32,
            },
            "t4": {
                "c_hold_source": "p2_cell_c_geom",
                "c_hold": c_geom,
                "best_c_station": 0.6,
                "best_station_index": 0,
                "g_station": 0.6 - c_geom,
                "gate_threshold": 0.05,
                "gate": "PASS",
                "station_count": 2,
                "certificate_pass_count": 1,
                "body_rejection_count": 1,
                "tether_rejection_count": 0,
                "path_rejection_count": 0,
                "bound_support_instance": "Natures_Grass Tile (3)",
                "stations": stations,
            },
            "t6": {
                "k_acq": 10,
                "k_star": 0,
                "prompt_min_side_px": 40.0,
                "t1_domain_median_px": 30.0,
                "gate": "PASS",
                "samples": samples,
            },
        }

    def _write_all(self):
        p1_path = self._write("p1.json", self._p1_doc())
        p2_path = self._write("p2.json", self._p2_doc())
        p3_path = self._write("p3.json", self._p3_doc(p1_path, p2_path))
        return p1_path, p2_path, p3_path

    def test_valid_p3_ok_passes(self):
        from tools.scene006_candidate_check import check_p3
        p1_path, p2_path, p3_path = self._write_all()
        summary = check_p3(p3_path, p1_path, p2_path)
        self.assertEqual(summary["status"], "P3_OK")

    def test_tampered_margin_fails(self):
        from tools.scene006_candidate_check import check_p3
        p1_path, p2_path, p3_path = self._write_all()
        doc = json.loads(Path(p3_path).read_text())
        doc["selection"]["ranking"][0]["score"] += 0.1
        p3_path = self._write("p3b.json", doc)
        with self.assertRaises(CheckFailure):
            check_p3(p3_path, p1_path, p2_path)

    def test_wrong_finalist_fails(self):
        from tools.scene006_candidate_check import check_p3
        p1_path, p2_path, p3_path = self._write_all()
        doc = json.loads(Path(p3_path).read_text())
        doc["selection"]["finalist"] = doc["selection"]["ranking"][1]
        p3_path = self._write("p3c.json", doc)
        with self.assertRaises(CheckFailure):
            check_p3(p3_path, p1_path, p2_path)

    def test_support_record_lying_fails(self):
        from tools.scene006_candidate_check import check_p3
        p1_path, p2_path, p3_path = self._write_all()
        doc = json.loads(Path(p3_path).read_text())
        doc["support_binding"][0]["ok"] = False
        p3_path = self._write("p3d.json", doc)
        with self.assertRaises(CheckFailure):
            check_p3(p3_path, p1_path, p2_path)

    def test_status_gate_inconsistency_fails(self):
        from tools.scene006_candidate_check import check_p3
        p1_path, p2_path, p3_path = self._write_all()
        doc = json.loads(Path(p3_path).read_text())
        doc["status"] = "BLOCKED_FINALIST_AUDIT_FAILED"
        p3_path = self._write("p3e.json", doc)
        with self.assertRaises(CheckFailure):
            check_p3(p3_path, p1_path, p2_path)

    def test_dispatch_requires_input_paths(self):
        from tools.scene006_candidate_check import check
        p1_path, p2_path, p3_path = self._write_all()
        with self.assertRaises(CheckFailure):
            check(p3_path)
        summary = check(p3_path, p1_path=p1_path, p2_path=p2_path)
        self.assertEqual(summary["status"], "P3_OK")

    def test_pre_scene_terminal_allows_empty_scene_hash(self):
        # F11: SUPPORT_SEMANTICS_MISMATCH is produced before the scene
        # opens, so the capture legitimately carries an empty scene hash.
        from tools.scene006_candidate_check import check_p3
        p1 = self._p1_doc()
        # Give the (195,30) h=20 cell a road-surface support id so its
        # expected binding is not-ok.
        p1["altitudes"][1]["report"]["candidates"][0]["support_ids"] = [
            "Road Tile@210,30"
        ]
        p1_path = self._write("p1.json", p1)
        p2_path = self._write("p2.json", self._p2_doc())
        doc = self._p3_doc(p1_path, p2_path)
        doc["status"] = "SUPPORT_SEMANTICS_MISMATCH"
        doc["capture"]["scene_state_sha256"] = ""
        doc["support_binding"][0]["ok"] = False
        doc["support_binding"][0]["mismatch"] = (
            "support instance is not a grass-allowlist name"
        )
        p3_path = self._write("p3.json", doc)
        summary = check_p3(p3_path, p1_path, p2_path)
        self.assertEqual(summary["status"], "SUPPORT_SEMANTICS_MISMATCH")
        # A pre-scene status with a non-empty scene hash fails closed.
        doc["capture"]["scene_state_sha256"] = "deadbeef"
        p3_bad = self._write("p3_bad.json", doc)
        with self.assertRaises(CheckFailure):
            check_p3(p3_bad, p1_path, p2_path)
        # A scene-stage status with an empty scene hash fails closed.
        clean_p1 = self._write("p1_clean.json", self._p1_doc())
        ok_doc = self._p3_doc(clean_p1, p2_path)
        ok_doc["capture"]["scene_state_sha256"] = ""
        p3_bad2 = self._write("p3_bad2.json", ok_doc)
        with self.assertRaises(CheckFailure):
            check_p3(p3_bad2, clean_p1, p2_path)

    def test_ranking_keeps_terminal_labels(self):
        # F12: an in-band cell with a non-finite input appears in the
        # ranking table with its terminal label, never ranked.
        from tools.scene006_candidate_check import check_p3
        p1_path, p2_path, p3_path = self._write_all()
        p2 = json.loads(Path(p2_path).read_text())
        bad_cell = dict(p2["anchors"][1]["cells"][0])
        bad_cell["vertical_fov_deg"] = 25.0
        bad_cell["l_point"] = float("nan")
        p2["anchors"][1]["cells"].append(bad_cell)
        p2_path = self._write("p2.json", p2)
        doc = self._p3_doc(p1_path, p2_path)
        terminal_row = dict(doc["selection"]["ranking"][-1])
        terminal_row.update({
            "vertical_fov_deg": 25.0,
            "l_point": float("nan"),
            "m_t1": float("nan"), "m_t2": float("nan"),
            "m_t3a": float("nan"), "m_t3b": float("nan"),
            "score": float("nan"),
            "terminal": "SCORE_INPUT_NOT_FINITE",
            "rank": -1,
        })
        doc["selection"]["ranking"].append(terminal_row)
        doc["support_binding"].append({
            "anchor_x_m": 197.0,
            "anchor_z_m": 30.0,
            "initial_altitude_m": 16.0,
            "p1_candidate_rank": 0,
            "p1_legal": True,
            "support_ids": ["Natures_Grass Tile (3)"],
            "single_support": True,
            "grass_allowlist_match": True,
            "p1_p2_binding_consistent": True,
            "ok": True,
            "mismatch": "",
        })
        p3_path = self._write("p3.json", doc)
        summary = check_p3(p3_path, p1_path, p2_path)
        self.assertEqual(summary["status"], "P3_OK")
        # Dropping the terminal row must fail.
        doc["selection"]["ranking"] = doc["selection"]["ranking"][:-1]
        p3_bad = self._write("p3_bad.json", doc)
        with self.assertRaises(CheckFailure):
            check_p3(p3_bad, p1_path, p2_path)

    def test_t6_fidelity_contradiction_gate(self):
        # F13: a visible-but-unprojectable prompt maps to the named gate
        # and the audit-failed status.
        from tools.scene006_candidate_check import check_p3
        p1_path, p2_path, p3_path = self._write_all()
        doc = json.loads(Path(p3_path).read_text())
        doc["t6"]["samples"][0]["min_side_px"] = float("nan")
        doc["t6"]["prompt_min_side_px"] = float("nan")
        doc["t6"]["gate"] = "PROBE_FIDELITY_CONTRADICTION"
        doc["status"] = "BLOCKED_FINALIST_AUDIT_FAILED"
        p3_path = self._write("p3.json", doc)
        summary = check_p3(p3_path, p1_path, p2_path)
        self.assertEqual(summary["status"], "BLOCKED_FINALIST_AUDIT_FAILED")


if __name__ == "__main__":
    unittest.main()
