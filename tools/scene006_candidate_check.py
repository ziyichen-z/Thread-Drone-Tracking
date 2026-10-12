#!/usr/bin/env python3
"""P1-SCENE-006 amendment-1 batch-1b artifact checker.

Independent consumer-side verification of the P1/P2/route-audit artifacts
produced by Scene006CandidateGenerator. Covers the F4 "" no-value
convention (``legal`` is authoritative; ``rejection_reason``/``blocking_object``
use "" for none), count reconciliation, gate recomputation from the
published per-cell domain values, grid/pair consistency between P1 and P2,
trace-hash recomputation (F1, via tools/scene006_trace_hash.py) and the
capture-identity fields (§5.6 double commit fields, clean porcelain,
scene-file unsaved proof).

CLI:
    python3 tools/scene006_candidate_check.py check <artifact.json> [...]
"""

from __future__ import annotations

import argparse
import json
import math
import sys

from tools.scene006_trace_hash import verify_artifact as verify_trace

P1_SCHEMA = "p1-scene-006-p1/v1"
P2_SCHEMA = "p1-scene-006-p2/v1"
P3_SCHEMA = "p1-scene-006-p3/v1"
ROUTE_AUDIT_SCHEMA = "p1-scene-006-familyb-route-audit/v1"
ALTITUDES = (16.0, 20.0, 24.0, 28.0, 32.0)
VFOVS = (20.0, 25.0, 30.0, 35.0, 40.0)
T1_P05_MIN = 25.0
T2_INTERVAL = (0.10, 0.50)
T3_OCC_INTERVAL = (0.05, 0.40)
T3_TOTAL_INTERVAL = (0.15, 0.60)
TERMINALS = ("", "HORIZON_SHORT", "PROBE_FIDELITY_CONTRADICTION")
GRASS_ALLOWLIST = ("Natures_Grass Tile", "Natures_Grass Tile Small")
P3_STATUSES = (
    "P3_OK",
    "BLOCKED_GEOMETRY_INFEASIBLE",
    "SUPPORT_SEMANTICS_MISMATCH",
    "TRACE_BINDING_MISMATCH",
    "T5_RECHECK_DIVERGENCE",
    "BLOCKED_FINALIST_AUDIT_FAILED",
)
# §5.4 frozen scoring constants (binary64).
M_T2_NORM = 0.20
M_T3A_NORM = 0.175
M_T3B_NORM = 0.225
T4_GAIN_MIN = 0.05


class CheckFailure(AssertionError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def quantile_type7(values: list[float], probability: float) -> float:
    """Type-7 quantile, bit-compatible with the frozen C# implementation."""
    if not values:
        raise ValueError("quantile of an empty sample is undefined")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    virtual_index = probability * (len(ordered) - 1)
    previous = int(virtual_index)
    following = min(previous + 1, len(ordered) - 1)
    gamma = virtual_index - previous
    lower, upper = ordered[previous], ordered[following]
    difference = upper - lower
    if gamma >= 0.5:
        return upper - difference * (1.0 - gamma)
    return lower + difference * gamma


def _check_capture(
    capture: dict, where: str, require_scene_state: bool = True
) -> None:
    _require(
        isinstance(capture, dict), f"{where}: capture identity missing")
    _require(bool(capture.get("capture_commit")), f"{where}: capture_commit missing")
    _require(
        capture["capture_commit"] == capture.get("tool_commit"),
        f"{where}: batch-1b capture_commit must equal tool_commit",
    )
    _require(
        capture.get("git_status_porcelain") == "",
        f"{where}: porcelain must be recorded empty",
    )
    if require_scene_state:
        _require(
            bool(capture.get("scene_state_sha256")), f"{where}: scene hash missing")
    else:
        _require(
            not capture.get("scene_state_sha256"),
            f"{where}: pre-scene terminal must carry an empty scene hash",
        )
    _require(
        capture.get("scene_file_sha256_before")
        and capture["scene_file_sha256_before"]
        == capture.get("scene_file_sha256_after"),
        f"{where}: scene file before/after hashes must match",
    )
    _require(capture.get("scene_saved") is False, f"{where}: scene_saved")


def check_p1(path: str) -> dict:
    artifact = _load(path)
    _require(artifact.get("schema_version") == P1_SCHEMA, f"{path}: schema")
    _check_capture(artifact["capture"], path)
    summary = {"path": path, "family": artifact["family"],
               "status": artifact["status"], "legal_pairs": 0}
    grid = {(a["x_m"], a["z_m"]): a for a in artifact["grid_anchors"]}
    seen_altitudes = []
    for altitude_report in artifact["altitudes"]:
        altitude = altitude_report["altitude_m"]
        seen_altitudes.append(altitude)
        report = altitude_report["report"]
        legal_count = 0
        for candidate in report["candidates"]:
            # F4: "" is the no-value convention; `legal` is authoritative.
            empty_reason = candidate["rejection_reason"] in ("", None)
            _require(
                candidate["legal"] == empty_reason,
                f"{path}: legal/rejection_reason mismatch at "
                f"({candidate['x_m']}, {candidate['z_m']}) h={altitude}",
            )
            if candidate["legal"]:
                legal_count += 1
            key = (candidate["x_m"], candidate["z_m"])
            if key in grid and candidate["legal"]:
                grid[key].setdefault("_seen", []).append(altitude)
        _require(
            legal_count == report["legal_candidate_count"],
            f"{path}: legal count mismatch at h={altitude}",
        )
        _require(
            report["candidate_count"] == len(report["candidates"]) == 1257,
            f"{path}: candidate count at h={altitude}",
        )
        _require(
            report["support_rejection_count"]
            == sum(1 for c in report["candidates"]
                   if c["support_status"] != "PASS"),
            f"{path}: support count at h={altitude}",
        )
        _require(
            report["route_rejection_count"]
            == sum(1 for c in report["candidates"]
                   if c["route_gate_status"] != "PASS"),
            f"{path}: route count at h={altitude}",
        )
        _require(
            report["clearance_rejection_count"]
            == sum(1 for c in report["candidates"]
                   if c["support_status"] == "PASS"
                   and c["clearance_status"] != "PASS"),
            f"{path}: clearance count at h={altitude}",
        )
    _require(
        sorted(seen_altitudes) == sorted(ALTITUDES),
        f"{path}: altitude set",
    )
    for anchor in artifact["grid_anchors"]:
        declared = sorted(anchor["legal_altitudes_m"])
        seen = sorted(anchor.pop("_seen", []))
        _require(
            declared == seen,
            f"{path}: grid anchor ({anchor['x_m']}, {anchor['z_m']}) "
            f"legal altitudes {declared} != candidate records {seen}",
        )
        summary["legal_pairs"] += len(declared)
    return summary


def check_p2(path: str, p1_path: str | None = None) -> dict:
    artifact = _load(path)
    _require(artifact.get("schema_version") == P2_SCHEMA, f"{path}: schema")
    _check_capture(artifact["capture"], path)
    summary = {"path": path, "family": artifact["family"],
               "status": artifact["status"], "in_band": 0, "cells": 0}
    if p1_path:
        p1 = _load(p1_path)
        _require(
            p1["capture"]["scene_state_sha256"]
            == artifact["capture"]["scene_state_sha256"],
            f"{path}: scene hash differs from {p1_path}",
        )
        p1_grid = {
            (a["x_m"], a["z_m"]): sorted(a["legal_altitudes_m"])
            for a in p1["grid_anchors"]
        }
        for anchor in artifact["anchors"]:
            key = (anchor["anchor_x_m"], anchor["anchor_z_m"])
            _require(
                sorted(anchor["legal_altitudes_m"]) == p1_grid.get(key),
                f"{path}: anchor {key} legal altitudes diverge from P1",
            )
    evaluated = 0
    in_band = 0
    for anchor in artifact["anchors"]:
        _require(
            anchor["s_init_altitude_consistent"] is True,
            f"{path}: s_init altitude drift",
        )
        expected_cells = len(anchor["legal_altitudes_m"]) * len(VFOVS)
        _require(
            len(anchor["cells"]) == expected_cells,
            f"{path}: cell count for anchor "
            f"({anchor['anchor_x_m']}, {anchor['anchor_z_m']})",
        )
        horizon_short = anchor["first_lap_status"] == "HORIZON_SHORT"
        for cell in anchor["cells"]:
            evaluated += 1
            _require(cell["terminal"] in TERMINALS, f"{path}: terminal")
            _require(
                cell["trace_sha256"] == anchor["trace_sha256"],
                f"{path}: cell trace binding",
            )
            if horizon_short:
                _require(
                    cell["terminal"] == "HORIZON_SHORT",
                    f"{path}: horizon terminal",
                )
                continue
            if cell["terminal"]:
                continue
            domain = cell["t1_domain_min_sides_px"]
            _require(
                len(domain) == cell["t1_domain_count"],
                f"{path}: domain count",
            )
            if domain:
                _require(
                    abs(quantile_type7(domain, 0.05)
                        - cell["t1_min_side_p05_px"]) < 1e-3,
                    f"{path}: p05 recompute",
                )
                _require(
                    abs(quantile_type7(domain, 0.5)
                        - cell["t1_min_side_median_px"]) < 1e-3,
                    f"{path}: median recompute",
                )
                _require(
                    abs(min(domain) - cell["t1_min_side_min_px"]) < 1e-6
                    and abs(max(domain) - cell["t1_min_side_max_px"]) < 1e-6,
                    f"{path}: min/max recompute",
                )
            _require(
                abs(cell["l_point"] - (1.0 - cell["c_frustum"])) < 1e-6
                and abs(cell["l_occ"] - (cell["c_frustum"] - cell["c_geom"])) < 1e-6
                and abs(cell["total_loss"] - (1.0 - cell["c_geom"])) < 1e-6,
                f"{path}: loss decomposition",
            )
            t2 = T2_INTERVAL[0] <= cell["l_point"] <= T2_INTERVAL[1]
            t3 = (T3_OCC_INTERVAL[0] <= cell["l_occ"] <= T3_OCC_INTERVAL[1]
                  and T3_TOTAL_INTERVAL[0] <= cell["total_loss"]
                  <= T3_TOTAL_INTERVAL[1])
            t1 = bool(domain) and cell["t1_min_side_p05_px"] >= T1_P05_MIN
            _require(
                cell["t2_gate"] == ("PASS" if t2 else "FAIL")
                and cell["t3_gate"] == ("PASS" if t3 else "FAIL"),
                f"{path}: gate recompute",
            )
            _require(
                cell["gates_in_band"] == (t1 and t2 and t3),
                f"{path}: in-band recompute",
            )
            for tick in cell["occluded_ticks"]:
                _require(
                    tick["frustum_sample_count"] > tick["visible_sample_count"],
                    f"{path}: occluded tick counts",
                )
                _require(
                    tick["blocking_roots"]
                    == sorted(set(tick["blocking_roots"])),
                    f"{path}: blocker list not sorted/distinct",
                )
            if cell["gates_in_band"]:
                in_band += 1
    _require(
        evaluated == artifact["evaluated_cell_count"]
        and in_band == artifact["in_band_cell_count"],
        f"{path}: cell totals",
    )
    summary["in_band"] = in_band
    summary["cells"] = evaluated
    return summary


def check_route_audit(path: str) -> dict:
    artifact = _load(path)
    _require(
        artifact.get("schema_version") == ROUTE_AUDIT_SCHEMA,
        f"{path}: schema",
    )
    _check_capture(artifact["capture"], path)
    status = artifact["status"]
    rows = artifact["relocations"]
    _require(len(rows) == 5, f"{path}: relocation row count")
    if status == "RELOCATION_NO_LEGAL_LANDING":
        _require(
            any(not r["recompute_match"] for r in rows),
            f"{path}: no-landing terminal without an unsolved row",
        )
    elif status == "RELOCATION_RECOMPUTE_MISMATCH":
        _require(
            any(not r["recompute_match"] for r in rows),
            f"{path}: mismatch terminal without a mismatching row",
        )
    elif status == "RELOCATION_LANDING_ILLEGAL":
        _require(
            all(r["recompute_match"] for r in rows)
            and any(
                not r["landing_road_coverage"]
                or not r["landing_static_clearance"] for r in rows),
            f"{path}: landing terminal without an illegal landing",
        )
    elif status == "ROUTE_LEGALITY_FAILED":
        _require(
            all(r["recompute_match"] for r in rows)
            and all(
                r["landing_road_coverage"] and r["landing_static_clearance"]
                for r in rows),
            f"{path}: legality terminal prerequisites",
        )
        _require(
            artifact["road_violation_count"]
            + artifact["obstacle_violation_count"]
            + artifact["corridor_violation_count"] > 0,
            f"{path}: legality terminal without violations",
        )
    elif status == "CLEAR":
        _require(
            all(r["recompute_match"] for r in rows)
            and all(
                r["landing_road_coverage"] and r["landing_static_clearance"]
                for r in rows),
            f"{path}: CLEAR requires matched rows and legal landings",
        )
        _require(
            artifact["road_violation_count"] == 0
            and artifact["obstacle_violation_count"] == 0
            and artifact["corridor_violation_count"] == 0,
            f"{path}: CLEAR requires zero violations",
        )
    else:
        raise CheckFailure(f"{path}: unknown status {status!r}")
    return {"path": path, "status": status}


def _sha256_file(path: str) -> str:
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical(name: str) -> str:
    if name.endswith(")"):
        marker = name.rfind(" (")
        if marker > 0 and name[marker + 2 : -1].isdigit():
            return name[:marker]
    return name


def _score_cell_margins(cell: dict) -> dict | None:
    """§5.4 margins in binary64; None when an input is not finite."""
    l_point = float(cell["l_point"])
    l_occ = float(cell["l_occ"])
    total = float(cell["total_loss"])
    p05 = float(cell["t1_min_side_p05_px"])
    inputs = (l_point, l_occ, total, p05)
    if any(not math.isfinite(value) for value in inputs):
        return None
    m_t2 = min(l_point - T2_INTERVAL[0], T2_INTERVAL[1] - l_point) / M_T2_NORM
    m_t3a = min(l_occ - T3_OCC_INTERVAL[0], T3_OCC_INTERVAL[1] - l_occ) / M_T3A_NORM
    m_t3b = (
        min(total - T3_TOTAL_INTERVAL[0], T3_TOTAL_INTERVAL[1] - total)
        / M_T3B_NORM
    )
    m_t1 = min((p05 - T1_P05_MIN) / T1_P05_MIN, 1.0)
    score = min(m_t1, m_t2, m_t3a, m_t3b)
    margins = {
        "m_t1": m_t1, "m_t2": m_t2, "m_t3a": m_t3a, "m_t3b": m_t3b,
        "score": score,
    }
    if any(not math.isfinite(value) for value in margins.values()):
        return None
    return margins


def _in_band_cells(p2: dict) -> list[dict]:
    return [
        cell
        for anchor in p2["anchors"]
        for cell in anchor["cells"]
        if cell["gates_in_band"]
    ]


def check_p3(path: str, p1_path: str, p2_path: str) -> dict:
    """Batch-1c P3 artifact checks (BC-B1C-1/2/5 and §5.4 recomputation)."""
    artifact = _load(path)
    _require(artifact.get("schema_version") == P3_SCHEMA, f"{path}: schema")
    status = artifact.get("status")
    _require(status in P3_STATUSES, f"{path}: unknown status {status!r}")
    capture = artifact.get("capture")
    # F11: the two pre-scene terminals legitimately carry an empty scene
    # state hash; scene-stage statuses must carry one.
    scene_stages = (
        "P3_OK",
        "BLOCKED_FINALIST_AUDIT_FAILED",
        "T5_RECHECK_DIVERGENCE",
        "TRACE_BINDING_MISMATCH",
    )
    _check_capture(
        capture, path, require_scene_state=status in scene_stages)

    p1 = _load(p1_path)
    p2 = _load(p2_path)
    _require(p1.get("schema_version") == P1_SCHEMA, f"{p1_path}: schema")
    _require(p2.get("schema_version") == P2_SCHEMA, f"{p2_path}: schema")

    selection = artifact.get("selection")
    _require(isinstance(selection, dict), f"{path}: selection missing")
    _require(
        selection["p1_artifact"]["sha256"] == _sha256_file(p1_path)
        and selection["p2_artifact"]["sha256"] == _sha256_file(p2_path),
        f"{path}: input artifact binding hashes differ",
    )

    # §5.4 selection recomputation over the reviewed in-band cells.
    cells = _in_band_cells(p2)
    ranking = selection.get("ranking")
    _require(
        isinstance(ranking, list) and len(ranking) == len(cells),
        f"{path}: ranking must cover every in-band cell with its "
        "terminal label",
    )
    expected_rows = []
    expected_terminals = []
    for cell in cells:
        margins = _score_cell_margins(cell)
        if margins is None:
            expected_terminals.append((cell, "SCORE_INPUT_NOT_FINITE"))
        else:
            expected_rows.append((cell, margins))
    _require(
        selection["f_count"] == len(expected_rows),
        f"{path}: f_count differs from the scored in-band cells",
    )

    # Frozen ordering: score desc (binary64 ==), vfov asc, altitude asc,
    # family ordinal, anchor lattice rank asc. The anchor rank only matters
    # on full ties; comparing the artifact's stored order to this sort.
    def sort_key(item):
        cell, margins = item
        return (
            -margins["score"],
            cell["vertical_fov_deg"],
            cell["initial_altitude_m"],
            cell["family"],
            (cell["anchor_x_m"] - (195.0 if cell["family"] == "B" else 150.0))
            ** 2
            + (cell["anchor_z_m"] - (30.0 if cell["family"] == "B" else 108.0))
            ** 2,
            cell["anchor_x_m"],
            cell["anchor_z_m"],
        )
    expected_rows.sort(key=sort_key)
    ranked_rows = ranking[: len(expected_rows)]
    terminal_rows = ranking[len(expected_rows):]
    for index, ((cell, margins), row) in enumerate(
        zip(expected_rows, ranked_rows)
    ):
        _require(
            row["family"] == cell["family"]
            and row["anchor_x_m"] == cell["anchor_x_m"]
            and row["anchor_z_m"] == cell["anchor_z_m"]
            and row["initial_altitude_m"] == cell["initial_altitude_m"]
            and row["vertical_fov_deg"] == cell["vertical_fov_deg"],
            f"{path}: ranking row {index} identity/order",
        )
        _require(
            row["terminal"] == "",
            f"{path}: ranked row {index} carries a terminal",
        )
        for key in ("m_t1", "m_t2", "m_t3a", "m_t3b", "score"):
            _require(
                abs(row[key] - margins[key]) < 1e-9,
                f"{path}: ranking row {index} {key} recompute",
            )
        _require(row["rank"] == index, f"{path}: ranking row {index} rank")
    # Terminal-labeled rows: membership, matching recomputed label, rank -1.
    remaining = list(expected_terminals)
    for row in terminal_rows:
        _require(
            row["terminal"] != "" and row["rank"] == -1,
            f"{path}: terminal row shape",
        )
        match = None
        for cell, terminal in remaining:
            if (
                row["family"] == cell["family"]
                and row["anchor_x_m"] == cell["anchor_x_m"]
                and row["anchor_z_m"] == cell["anchor_z_m"]
                and row["initial_altitude_m"] == cell["initial_altitude_m"]
                and row["vertical_fov_deg"] == cell["vertical_fov_deg"]
            ):
                match = (cell, terminal)
                break
        _require(match is not None, f"{path}: terminal row membership")
        _require(
            row["terminal"] == match[1],
            f"{path}: terminal row label recompute",
        )
        remaining.remove(match)
    _require(
        not remaining,
        f"{path}: terminal-labeled cells missing from the ranking table",
    )
    if expected_rows:
        finalist = selection.get("finalist")
        first_cell, _ = expected_rows[0]
        _require(
            finalist
            and finalist["anchor_x_m"] == first_cell["anchor_x_m"]
            and finalist["anchor_z_m"] == first_cell["anchor_z_m"]
            and finalist["initial_altitude_m"]
            == first_cell["initial_altitude_m"]
            and finalist["vertical_fov_deg"]
            == first_cell["vertical_fov_deg"],
            f"{path}: finalist is not the frozen first rank",
        )

    # BC-B1C-2 support binding records, recomputed from the P1 artifact.
    records = artifact.get("support_binding") or []
    if status == "BLOCKED_GEOMETRY_INFEASIBLE":
        _require(
            selection["f_count"] == 0,
            f"{path}: infeasible status with a non-empty F",
        )
        return {"path": path, "status": status}
    _require(
        len(records) == len(cells),
        f"{path}: support record count",
    )
    p1_grid = {
        (a["x_m"], a["z_m"]): a["legal_altitudes_m"]
        for a in p1["grid_anchors"]
    }
    all_ok = True
    for record, cell in zip(
        sorted(records, key=lambda r: (r["anchor_x_m"], r["anchor_z_m"],
                                       r["initial_altitude_m"])),
        sorted(cells, key=lambda c: (c["anchor_x_m"], c["anchor_z_m"],
                                     c["initial_altitude_m"])),
    ):
        _require(
            record["anchor_x_m"] == cell["anchor_x_m"]
            and record["anchor_z_m"] == cell["anchor_z_m"]
            and record["initial_altitude_m"]
            == cell["initial_altitude_m"],
            f"{path}: support record/cell binding",
        )
        expected_ok = False
        for altitude_report in p1["altitudes"]:
            if altitude_report["altitude_m"] != cell["initial_altitude_m"]:
                continue
            for candidate in altitude_report["report"]["candidates"]:
                if (candidate["x_m"] == cell["anchor_x_m"]
                        and candidate["z_m"] == cell["anchor_z_m"]):
                    ids = candidate.get("support_ids") or []
                    expected_ok = (
                        candidate["legal"]
                        and len(ids) == 1
                        and _canonical(ids[0]) in GRASS_ALLOWLIST
                        and cell["initial_altitude_m"]
                        in p1_grid.get(
                            (cell["anchor_x_m"], cell["anchor_z_m"]), [])
                    )
        _require(
            record["ok"] == expected_ok,
            f"{path}: support record ok mismatch for "
            f"({cell['anchor_x_m']}, {cell['anchor_z_m']}) "
            f"h={cell['initial_altitude_m']}",
        )
        all_ok = all_ok and record["ok"]
    if status == "SUPPORT_SEMANTICS_MISMATCH":
        _require(not all_ok, f"{path}: mismatch status with all-ok records")
        return {"path": path, "status": status}
    _require(all_ok, f"{path}: support mismatch but wrong status")

    # Trace + T5 recheck + T4/T6 sections for the scene-stage statuses.
    finalist = selection.get("finalist")
    _require(
        isinstance(finalist, dict),
        f"{path}: scene-stage status without a finalist",
    )
    finalist_cell = None
    for cell in cells:
        if (cell["anchor_x_m"] == finalist["anchor_x_m"]
                and cell["anchor_z_m"] == finalist["anchor_z_m"]
                and cell["initial_altitude_m"]
                == finalist["initial_altitude_m"]
                and cell["vertical_fov_deg"]
                == finalist["vertical_fov_deg"]):
            finalist_cell = cell
    _require(finalist_cell is not None, f"{path}: finalist cell missing")
    if status == "TRACE_BINDING_MISMATCH":
        _require(
            artifact["finalist_trace_sha256"]
            != finalist_cell["trace_sha256"],
            f"{path}: trace mismatch status with matching hashes",
        )
        return {"path": path, "status": status}
    _require(
        artifact["finalist_trace_sha256"]
        == finalist_cell["trace_sha256"],
        f"{path}: finalist trace binding",
    )
    recheck = artifact.get("t5_recheck")
    _require(isinstance(recheck, dict), f"{path}: t5_recheck missing")
    p1_contract = None
    for altitude_report in p1["altitudes"]:
        if altitude_report["altitude_m"] == finalist_cell["initial_altitude_m"]:
            p1_contract = altitude_report["report"]["anchor_contract_sha256"]
    if status == "T5_RECHECK_DIVERGENCE":
        _require(recheck.get("equal") is False, f"{path}: t5 status")
        return {"path": path, "status": status}
    _require(recheck.get("equal") is True, f"{path}: t5_recheck not equal")
    _require(
        recheck.get("p1_contract_sha256") == p1_contract
        and recheck.get("recheck_contract_sha256") == p1_contract,
        f"{path}: t5 contract hash binding",
    )

    t4 = artifact.get("t4")
    t6 = artifact.get("t6")
    _require(isinstance(t4, dict) and isinstance(t6, dict),
             f"{path}: t4/t6 missing")
    _require(
        abs(t4["c_hold"] - finalist_cell["c_geom"]) < 1e-6,
        f"{path}: t4 c_hold must be the P2 cell c_geom",
    )
    _require(
        abs(t6["t1_domain_median_px"] - finalist_cell["t1_min_side_median_px"])
        < 1e-3,
        f"{path}: t6 median must be the P2 cell median",
    )
    stations = t4["stations"]
    certified = [s for s in stations if s["certificate"]["passed"]]
    _require(
        t4["certificate_pass_count"] == len(certified)
        and t4["station_count"] == len(stations)
        and t4["body_rejection_count"]
        == sum(1 for s in stations if s["certificate"]["body_rejected"])
        and t4["tether_rejection_count"]
        == sum(1 for s in stations if s["certificate"]["tether_rejected"])
        and t4["path_rejection_count"]
        == sum(1 for s in stations if s["certificate"]["path_rejected"]),
        f"{path}: t4 counts",
    )
    if certified:
        best = max(s["c_station"] for s in certified)
        _require(
            abs(t4["best_c_station"] - best) < 1e-6
            and abs(t4["g_station"] - (best - t4["c_hold"])) < 1e-6,
            f"{path}: t4 gain recompute",
        )
    expected_t4_gate = (
        "PASS"
        if certified and t4["g_station"] >= T4_GAIN_MIN
        else "FAIL"
    )
    _require(t4["gate"] == expected_t4_gate, f"{path}: t4 gate")
    samples = t6["samples"]
    _require(len(samples) == 11, f"{path}: t6 window must be k=0..10")
    expected_k = next(
        (s["k"] for s in samples if s["geometrically_visible"]), -1)
    _require(t6["k_star"] == expected_k, f"{path}: t6 k_star")
    if expected_k >= 0:
        prompt_side = samples[expected_k]["min_side_px"]
        recorded_side = t6["prompt_min_side_px"]
        if math.isfinite(prompt_side):
            _require(
                abs(recorded_side - prompt_side) < 1e-6,
                f"{path}: t6 prompt min-side",
            )
            expected_t6_gate = (
                "PASS"
                if prompt_side >= t6["t1_domain_median_px"]
                else "FAIL"
            )
        else:
            # F13: a visible-but-unprojectable prompt is the named
            # fidelity-contradiction gate, never a PASS/FAIL mislabel.
            _require(
                not math.isfinite(recorded_side),
                f"{path}: t6 prompt min-side should be non-finite",
            )
            expected_t6_gate = "PROBE_FIDELITY_CONTRADICTION"
    else:
        expected_t6_gate = "FAIL"
    _require(t6["gate"] == expected_t6_gate, f"{path}: t6 gate")
    expected_status = (
        "P3_OK"
        if t4["gate"] == "PASS" and t6["gate"] == "PASS"
        else "BLOCKED_FINALIST_AUDIT_FAILED"
    )
    _require(status == expected_status, f"{path}: final status")
    return {"path": path, "status": status}


def check(path: str, p1_path: str | None = None,
          p2_path: str | None = None) -> dict:
    artifact = _load(path)
    schema = artifact.get("schema_version", "")
    if schema == P1_SCHEMA:
        return check_p1(path)
    if schema == P2_SCHEMA:
        return check_p2(path, p1_path=p1_path)
    if schema == P3_SCHEMA:
        if not p1_path or not p2_path:
            raise CheckFailure(
                f"{path}: P3 verification needs --p1-path and --p2-path")
        return check_p3(path, p1_path, p2_path)
    if schema == ROUTE_AUDIT_SCHEMA:
        return check_route_audit(path)
    if schema == "p1-scene-006-trace/v2":
        result = verify_trace(path)
        if not result["match"]:
            raise CheckFailure(f"{path}: trace sha256 mismatch")
        # §5.6 (B1B-R1): trace artifacts are independent artifacts and must
        # carry the same dual identity and zero-write proof as every other
        # candidate artifact.
        _check_capture(artifact.get("capture"), path)
        return result
    raise CheckFailure(f"{path}: unrecognized schema {schema!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("artifacts", nargs="+")
    check_parser.add_argument(
        "--p1-path", help="P1 artifact path (required for P3 checks)")
    check_parser.add_argument(
        "--p2-path", help="P2 artifact path (required for P3 checks)")
    args = parser.parse_args(argv)

    if args.command == "check":
        failed = False
        for path in args.artifacts:
            try:
                summary = check(
                    path, p1_path=args.p1_path, p2_path=args.p2_path)
            except (CheckFailure, ValueError, KeyError) as error:
                print(f"FAIL {path}: {error}")
                failed = True
            else:
                print(f"OK {path}: {summary}")
        return 1 if failed else 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
