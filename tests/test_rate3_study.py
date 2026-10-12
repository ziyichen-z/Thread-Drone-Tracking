"""P1-M2-RATE-003 batch-2 orchestration tests.

Covers the frozen execution order, the per-slot and batch-wide attempt
guards (BC-R3-2), the BC-DRB-4/5 pairing anchor, the §10 completion gate,
the §5 probe branch order, the §11 report-only lap period and the
immutable `p1-rate3-decision/v1` artifact.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
import tempfile
import unittest

from controller import rate3_decision, rate3_protocol
from controller.rate2_protocol import (
    IDENTITY_KEYS,
    atomic_bytes,
    atomic_json,
    canonical_json_bytes,
    sha256_bytes,
    sha256_file,
)
from tools import run_rate3_study as study

STUDY_ID = rate3_protocol.STUDY_ID
CLOCK_ID = rate3_protocol.CLOCK_ID
PLANNED = rate3_protocol.PLANNED_DURATION_S
PHASE_S_M = (1.5, 21.5, 41.5)


def tracker_identity():
    return {
        "name": "nanotrack-v2",
        "backend": "test",
        "pinned_version": "5.0.0",
        "model_sha256": {"backbone": "a" * 64, "neckhead": "b" * 64},
        "score_threshold": None,
        "threshold_source": "none",
        "preprocessing_id": "test",
    }


def session_for(run_id, *, init_frame_id=0, init_image_sha256="c" * 64):
    identity = study.slot_identity(run_id)
    return study.build_session(
        run_id=run_id,
        init_frame_id=init_frame_id,
        init_image_sha256=init_image_sha256,
        hold_route_s_m=PHASE_S_M[int(identity["phase"]) - 1],
        tracker_identity=tracker_identity(),
    )


def ready_document(value, *, frame_id=20, seq=20, published=100.0):
    return {
        "schema_version": rate3_protocol.READY_SCHEMA,
        "state": "TRACKING",
        **{key: value[key] for key in IDENTITY_KEYS},
        "last_processed_frame_id": frame_id,
        "processed_frame_count": seq,
        "seq": seq,
        "publisher_monotonic_s": published,
        "publisher_clock_id": CLOCK_ID,
        "heartbeat_interval_s": 1.0,
    }


def ack_document(value, command_bytes, *, release_frame=20, release_mono=500.0):
    command = json.loads(command_bytes)
    ready = json.loads(base64.b64decode(command["ready_json_base64"]))
    return {
        "schema_version": rate3_protocol.RELEASE_ACK_SCHEMA,
        "command_id": command["command_id"],
        **{key: value[key] for key in IDENTITY_KEYS},
        "release_clock_id": CLOCK_ID,
        "release_command_sha256": sha256_bytes(command_bytes),
        "ready_sha256": command["ready_sha256"],
        "ready_seq": ready["seq"],
        "processed_frame_count": ready["processed_frame_count"],
        "current_frame_id": release_frame,
        "last_processed_frame_id": ready["last_processed_frame_id"],
        "accepted_backlog_frames": release_frame
        - ready["last_processed_frame_id"],
        "release_frame_id": release_frame,
        "release_unix_s": 1_800_000_000.0,
        "release_monotonic_s": release_mono,
        "release_simulation_s": 10.0,
    }


def write_ledger(directory: Path) -> Path:
    path = Path(directory) / "authorizations.md"
    path.write_text(
        "# ledger\n\n## 2026-07-31 "
        + study.AUTHORIZATION_0C_MARKER
        + " 的 20 次名义研究数据会话预算\n\n- 用户原话：\"同意授权\"\n",
        encoding="utf-8",
    )
    return path


def scouting_report(*, status="QUALIFIED", phases=PHASE_S_M):
    candidates = []
    for index in range(60):
        distance = index * 1.0 + 0.5
        candidates.append(
            {
                "index": index,
                "route_s_m": distance,
                "frame_margin": 0.2,
                "has_active_distractor": True,
                "nearest_distractor_center_distance_px": 90.0,
                "nearest_distractor_iou": 0.0,
                "qualified": distance in phases,
            }
        )
    selected = [
        next(item for item in candidates if item["route_s_m"] == value)
        for value in phases
    ]
    return {
        "schema_version": study.SCOUTING_REPORT_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": study.SCOUTING_SLOT,
        "scenario_id": "p1-scene-004",
        "status": status,
        "route_perimeter_m": 62.14213562373095,
        "spacing_m": 0.5,
        "required_margin": 0.15,
        "ideal_phase_s_m": [0.0, 20.714045207910317, 41.428090415820635],
        "selected_route_s_m": [item["route_s_m"] for item in selected],
        "selected_candidate_index": [item["index"] for item in selected],
        "candidates": candidates,
    }


class Rate3StudyFixture:
    """A fully frozen campaign in a throwaway runtime."""

    def __init__(self, directory: Path):
        self.runtime = Path(directory) / "runtime"
        self.runtime.mkdir(parents=True)
        self.ledger = write_ledger(directory)
        study.prepare_campaign(self.runtime)
        study.record_run_gates(
            self.runtime,
            qual3_pass_attributed=True,
            dr_round3_passed=True,
            clock_smoke_passed=True,
            attribution="test fixture",
            ledger_path=self.ledger,
        )
        self._patch_gates()

    def _patch_gates(self):
        # `load_run_gates` re-reads the real ledger by default; point every
        # later call at the fixture ledger.
        original = study.load_run_gates

        def patched(runtime, *, ledger_path=self.ledger):
            return original(runtime, ledger_path=ledger_path)

        study.load_run_gates = patched
        self._original_load_run_gates = original

    def close(self):
        study.load_run_gates = self._original_load_run_gates

    def freeze_scouting(self, **kwargs):
        atomic_json(
            self.runtime / study.SCOUTING_REPORT_FILE,
            scouting_report(**kwargs),
        )
        return study.freeze_scouting(self.runtime, confirmed=True)

    def freeze_calibration(self, slot, *, frame_id=None, image_sha=None):
        """Write a frozen calibration product without the Unity/cv2 path."""

        identity = study.slot_identity(slot)
        directory = study.calibration_directory(self.runtime, slot)
        directory.mkdir(parents=True, exist_ok=True)
        phase = int(identity["phase"])
        frame_id = phase if frame_id is None else frame_id
        (directory / "reference.jpg").write_bytes(
            (image_sha or f"reference-{slot}").encode()
        )
        (directory / "reference.json").write_text(
            json.dumps({"frame_id": frame_id}), encoding="utf-8"
        )
        (directory / "reference-box-preview.jpg").write_bytes(b"overlay")
        (directory / "reference-box-preview.json").write_text("{}\n")
        manifest = {
            "schema_version": study.CALIBRATION_SCHEMA,
            "study_id": STUDY_ID,
            "run_id": slot,
            "difficulty": identity["difficulty"],
            "phase": phase,
            "scenario_id": rate3_protocol.expected_scenario(slot, STUDY_ID),
            "hold_route_s_m": PHASE_S_M[phase - 1],
            "reference_frame_id": frame_id,
            "reference_simulation_time_s": 7.5,
            "reference_image_sha256": sha256_file(directory / "reference.jpg"),
            "reference_metadata_sha256": sha256_file(
                directory / "reference.json"
            ),
            "reference_box_xywh_norm": [0.4, 0.3, 0.2, 0.2],
            "reference_box_preview_sha256": sha256_file(
                directory / "reference-box-preview.jpg"
            ),
            "frozen_unix_s": 1_800_000_000.0,
        }
        atomic_json(directory / "manifest.json", manifest)
        return study.load_calibration(self.runtime, slot)

    def freeze_all_calibrations(self):
        return [
            self.freeze_calibration(slot) for slot in study.CALIBRATION_SLOTS
        ]

    def complete_probe(self, *, conditional=0.4, displacement=23.0):
        """Drive the probe slot to its terminal B2 adjudication."""

        self.make_run(
            study.PROBE_SLOT,
            conditional=conditional,
            truth_records=[
                truth_record(
                    study.PROBE_SLOT,
                    21 + index,
                    x=128.0,
                    z=116.0,
                    cx=100.0 + index * displacement,
                    cy=50.0,
                    elapsed=index,
                )
                for index in range(20)
            ],
        )
        study.finalize_attempt(self.runtime, study.PROBE_SLOT)
        return study.build_probe(self.runtime)

    def make_run(
        self,
        run_id,
        *,
        conditional=0.5,
        c_geom=0.9,
        c_track=0.45,
        simulation_duration_s=PLANNED,
        wall_duration_s=PLANNED,
        evaluator_cutoff_s=PLANNED,
        lost=False,
        truth_records=None,
        calibration_slot_override=None,
    ):
        identity = study.slot_identity(run_id)
        calibration = study.load_calibration(
            self.runtime,
            calibration_slot_override
            or study.calibration_slot_for(
                str(identity["difficulty"]), int(identity["phase"])
            ),
        )
        value = session_for(
            run_id,
            init_frame_id=calibration["reference_frame_id"],
            init_image_sha256=calibration["reference_image_sha256"],
        )
        run_directory = self.runtime / "runs" / run_id
        run_directory.mkdir(parents=True)
        atomic_json(
            run_directory / "manifest.json",
            {
                "schema_version": "p1-track-run/v1",
                "run_id": run_id,
                "scenario_id": value["scenario_id"],
                "condition": "follow",
                "planned_duration_s": PLANNED,
                "rate3": {
                    key: value[key]
                    for key in (
                        "study_id",
                        "run_id",
                        "scenario_id",
                        "tracker_id",
                        "tracker_identity_sha256",
                        "model_identity_sha256",
                        "init_frame_id",
                        "init_image_sha256",
                        "hold_route_s_m",
                        "planned_duration_s",
                        "sensor_frame_schema",
                        "capture_monotonic_clock_id",
                    )
                },
            },
        )
        ready_bytes = canonical_json_bytes(ready_document(value))
        command_bytes = rate3_protocol.build_release_command(
            value, ready_bytes, command_id=f"release-{run_id}"
        )
        ack_bytes = canonical_json_bytes(ack_document(value, command_bytes))
        atomic_bytes(
            self.runtime / "release_command.accepted.json", command_bytes
        )
        atomic_bytes(self.runtime / "release_ack.json", ack_bytes)
        rate3_protocol.archive_release_provenance(
            self.runtime, run_directory, value
        )
        (self.runtime / "release_command.accepted.json").unlink()
        (self.runtime / "release_ack.json").unlink()

        rate_hz = int(identity["rate_hz"])
        release_mono = 500.0
        lines = []
        step = wall_duration_s / 10.0
        for index in range(1, 11):
            lines.append(
                json.dumps(
                    {
                        "record_kind": "frame",
                        "frame_id": 20 + index,
                        "phase": "measurement",
                        "state": "OK",
                        "capture_monotonic_s": release_mono + index * step,
                        "capture_monotonic_clock_id": CLOCK_ID,
                        "simulation_time_s": 10.0 + index * step,
                        "measurement_elapsed_s": index * step,
                    }
                )
            )
        (run_directory / "frames.jsonl").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        atomic_json(
            run_directory / "summary.json",
            {
                "schema_version": "p1-track-run/v1",
                "actual_duration_s": simulation_duration_s,
                "time_to_first_lost_s": 12.0 if lost else PLANNED,
                "time_to_first_lost_right_censored": not lost,
                "lost_records": 1 if lost else 0,
                "gap_events": 0,
                "reinit_required_records": 0,
                "event_counts": {},
                "compute_latency_ms": {"p95": 5.0},
                "backlog_count": {"p95": 0.0},
                "release_clock_id": CLOCK_ID,
                "release_monotonic_s": release_mono,
                "monotonic_capture_cadence_post_release": {
                    "strictly_increasing": True,
                    "rate_hz": float(rate_hz),
                },
            },
        )
        atomic_json(
            run_directory / "metrics.final.json",
            {
                "schema_version": "tethered-evaluation/v1",
                "scenario_id": value["scenario_id"],
                "elapsed_simulation_s": evaluator_cutoff_s,
                "aggregate": {
                    "c_geom": c_geom,
                    "c_track": c_track,
                    "c_track_given_geom": conditional,
                    "matched_tracking_observations": 100,
                    "incorrect_tracking_observations": 10,
                    "unmatched_tracking_observations": 0,
                },
            },
        )
        records = (
            truth_records
            if truth_records is not None
            else default_truth_records(run_id)
        )
        (self.runtime / study.EVALUATION_TRUTH_FILE).write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )
        return run_directory


def truth_record(run_id, frame_id, *, x, z, cx, cy, visible=True, elapsed=0.0):
    return {
        "schema_version": study.EVALUATION_TRUTH_SCHEMA,
        "study_id": STUDY_ID,
        "run_id": run_id,
        "frame_id": frame_id,
        "release_frame_id": 20,
        "simulation_time_s": 10.0 + elapsed,
        "capture_monotonic_s": 500.0 + elapsed,
        "capture_monotonic_clock_id": CLOCK_ID,
        "geometrically_visible": visible,
        "truth_box_available": True,
        "truth_box_x": 0.4,
        "truth_box_y": 0.3,
        "truth_box_width": 0.1,
        "truth_box_height": 0.1,
        "truth_center_x_px": cx,
        "truth_center_y_px": cy,
        "target_world_x_m": x,
        "target_world_z_m": z,
    }


def default_truth_records(run_id, *, count=40, displacement=6.0):
    """Straight-line motion crossing the start section five times."""

    records = []
    for index in range(count):
        # A saw-tooth in x around route[0].x = 128.0 gives repeatable
        # negative -> positive crossings of the directed start section.
        cycle = index % 8
        x = 128.0 + (cycle - 4) * 0.5
        records.append(
            truth_record(
                run_id,
                21 + index,
                x=x,
                z=116.0,
                cx=100.0 + index * displacement,
                cy=50.0,
                elapsed=index * 1.0,
            )
        )
    return records


class CampaignAndGateTests(unittest.TestCase):
    def test_scenario_configs_only_differ_where_the_protocol_allows(self):
        summary = study.check_scenario_configs()
        self.assertEqual(len(summary), 4)
        self.assertEqual(summary["D1-r20"]["capture_hz"], 20.0)
        self.assertEqual(summary["D1-r5"]["capture_hz"], 5.0)
        self.assertEqual(summary["D2-r5"]["target_speed_mps"], 8.0)
        self.assertEqual(
            summary["D1-r20"]["scenario_id"], summary["D1-r5"]["scenario_id"]
        )

    def test_frozen_session_order_is_the_accepted_twenty_slot_schedule(self):
        self.assertEqual(len(study.SESSION_ORDER), 20)
        self.assertEqual(study.SESSION_ORDER[0], study.SCOUTING_SLOT)
        self.assertEqual(
            study.SESSION_ORDER[1:7], tuple(study.CALIBRATION_SLOTS)
        )
        self.assertEqual(study.SESSION_ORDER[7], study.PROBE_SLOT)
        self.assertEqual(study.SESSION_ORDER[8:], study.FORMAL_SLOT_ORDER)
        self.assertEqual(study.FORMAL_SLOT_ORDER[0], "rs3-d1-p1-r20")
        self.assertEqual(study.FORMAL_SLOT_ORDER[2], "rs3-d1-p2-r5")
        self.assertEqual(study.FORMAL_SLOT_ORDER[-1], "rs3-d2-p3-r5")

    def test_run_gates_require_the_0c_ledger_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            runtime.mkdir()
            study.prepare_campaign(runtime)
            empty = Path(directory) / "empty.md"
            empty.write_text("# no authorization here\n", encoding="utf-8")
            with self.assertRaisesRegex(study.Rate3StudyError, "0c"):
                study.record_run_gates(
                    runtime,
                    qual3_pass_attributed=True,
                    dr_round3_passed=True,
                    clock_smoke_passed=True,
                    attribution="x",
                    ledger_path=empty,
                )

    def test_run_gates_require_every_named_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            runtime.mkdir()
            study.prepare_campaign(runtime)
            ledger = write_ledger(Path(directory))
            with self.assertRaisesRegex(
                study.Rate3StudyError, "qual3_pass_attributed"
            ):
                study.record_run_gates(
                    runtime,
                    qual3_pass_attributed=False,
                    dr_round3_passed=True,
                    clock_smoke_passed=True,
                    attribution="x",
                    ledger_path=ledger,
                )

    def test_campaign_freezes_the_accepted_constants(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            runtime.mkdir()
            campaign = study.prepare_campaign(runtime)
            self.assertEqual(campaign["planned_duration_s"], 150.0)
            self.assertEqual(campaign["theta"], 0.05)
            self.assertEqual(campaign["theta_geom"], 0.05)
            self.assertEqual(campaign["max_attempts_per_slot"], 3)
            self.assertEqual(campaign["batch_invalid_attempt_pause"], 4)
            self.assertEqual(study.prepare_campaign(runtime), campaign)


class ScoutingTests(unittest.TestCase):
    def test_scouting_freeze_binds_three_distinct_qualified_phases(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                manifest = fixture.freeze_scouting()
                self.assertEqual(manifest["phase_route_s_m"], list(PHASE_S_M))
                self.assertEqual(
                    study.phase_route_s_m(fixture.runtime, 2), PHASE_S_M[1]
                )
                self.assertEqual(
                    study.freeze_scouting(fixture.runtime), manifest
                )
            finally:
                fixture.close()

    def test_invalid_scouting_report_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                with self.assertRaisesRegex(
                    study.Rate3StudyError, "INVALID_SCOUTING"
                ):
                    fixture.freeze_scouting(status="INVALID_SCOUTING")
            finally:
                fixture.close()

    def test_collapsed_phases_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                with self.assertRaisesRegex(study.Rate3StudyError, "distinct"):
                    fixture.freeze_scouting(phases=(1.5, 1.5, 41.5))
            finally:
                fixture.close()


class AttemptGuardTests(unittest.TestCase):
    """Attempt guards driven through the real production state.

    Calibration slots are HOLD-only and never create `runs/<slot>`, so a
    failed calibration attempt is reproduced the way the operator reaches
    it: authorise, install the session, then archive it.
    """

    def fail_calibration_attempt(self, fixture, slot, reason):
        study.prepare_session(fixture.runtime, session_for(slot))
        self.assertTrue((fixture.runtime / study.SESSION_FILE).is_file())
        return study.archive_failed_attempt(fixture.runtime, slot, reason)

    def test_batch_counter_pauses_at_four_across_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                first = "rs3-d1-p1-calib"
                for index in range(2):
                    result = self.fail_calibration_attempt(
                        fixture, first, f"operator rejected overlay {index}"
                    )
                    self.assertEqual(
                        result["batch_invalid_attempt_count"], index + 1
                    )
                # The slot eventually succeeds, so the campaign advances to
                # the next calibration slot with the counter still at 2.
                fixture.freeze_calibration(first)
                for index in range(2):
                    result = self.fail_calibration_attempt(
                        fixture, "rs3-d1-p2-calib", f"wrong HOLD window {index}"
                    )
                    self.assertEqual(
                        result["batch_invalid_attempt_count"], index + 3
                    )
                self.assertTrue(result["batch_paused"])
                status = study.batch_status(fixture.runtime)
                self.assertEqual(status["batch_invalid_attempt_count"], 4)
                self.assertTrue(status["batch_paused"])
                self.assertEqual(
                    status["per_slot_invalid_attempts"][first], 2
                )
                with self.assertRaisesRegex(PermissionError, "BC-R3-2"):
                    study.authorize_session(
                        fixture.runtime, "rs3-d1-p2-calib"
                    )
            finally:
                fixture.close()

    def test_per_slot_attempt_cap_is_three_totals(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                slot = "rs3-d1-p1-calib"
                for index in range(3):
                    self.fail_calibration_attempt(
                        fixture, slot, f"invalid {index}"
                    )
                self.assertEqual(
                    study.failed_attempt_count(fixture.runtime, slot), 3
                )
                with self.assertRaisesRegex(PermissionError, "attempt limit"):
                    study.authorize_session(fixture.runtime, slot)
                with self.assertRaisesRegex(
                    study.Rate3StudyError, "attempt limit"
                ):
                    study.archive_failed_attempt(
                        fixture.runtime, slot, "one too many"
                    )
            finally:
                fixture.close()

    def test_calibration_receipt_payload_is_the_real_attempt_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                slot = "rs3-d1-p1-calib"
                # A refusal before the session exists is not a counted
                # attempt (BC-R3-2's dividing line).
                with self.assertRaises(FileNotFoundError):
                    study.archive_failed_attempt(
                        fixture.runtime, slot, "nothing installed"
                    )
                self.assertEqual(
                    study.batch_invalid_attempt_count(fixture.runtime), 0
                )
                self.assertFalse(
                    study.failed_attempts_directory(fixture.runtime, slot)
                    .joinpath("attempt-1-run")
                    .exists()
                )

                receipt = self.fail_calibration_attempt(
                    fixture, slot, "operator rejected the overlay"
                )
                self.assertEqual(receipt["attempt_number"], 1)
                self.assertIn(study.SESSION_FILE, receipt["archived_sources"])
                archive = Path(receipt["archived_directory"])
                self.assertTrue((archive / study.SESSION_FILE).is_file())
                self.assertEqual(
                    receipt["file_sha256"],
                    {
                        str(path.relative_to(archive)): sha256_file(path)
                        for path in sorted(archive.rglob("*"))
                        if path.is_file()
                    },
                )
                # The stale session is cleared, so the slot can be rerun.
                self.assertFalse(
                    (fixture.runtime / study.SESSION_FILE).exists()
                )
                self.assertTrue(
                    study.authorize_session(fixture.runtime, slot)["authorized"]
                )
            finally:
                fixture.close()

    def test_a_startup_refused_run_slot_still_produces_a_receipt(self):
        """A formal attempt can fail before the run directory exists."""

        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                fixture.freeze_all_calibrations()
                fixture.complete_probe()
                slot = study.FORMAL_SLOT_ORDER[0]
                calibration = study.load_calibration(
                    fixture.runtime, "rs3-d1-p1-calib"
                )
                study.prepare_session(
                    fixture.runtime,
                    session_for(
                        slot,
                        init_frame_id=calibration["reference_frame_id"],
                        init_image_sha256=calibration[
                            "reference_image_sha256"
                        ],
                    ),
                )
                self.assertFalse(
                    (fixture.runtime / "runs" / slot).exists()
                )
                receipt = study.archive_failed_attempt(
                    fixture.runtime, slot, "tracker refused at startup"
                )
                self.assertEqual(receipt["attempt_number"], 1)
                self.assertIn(study.SESSION_FILE, receipt["archived_sources"])
                self.assertEqual(
                    study.batch_invalid_attempt_count(fixture.runtime), 1
                )
            finally:
                fixture.close()

    def test_an_admissible_run_cannot_be_archived_as_failed(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                fixture.freeze_all_calibrations()
                fixture.complete_probe()
                slot = study.FORMAL_SLOT_ORDER[0]
                fixture.make_run(slot)
                status = study.finalize_attempt(fixture.runtime, slot)
                self.assertTrue(status["admissible"])
                with self.assertRaisesRegex(
                    study.Rate3StudyError, "admissible"
                ):
                    study.archive_failed_attempt(
                        fixture.runtime, slot, "changed my mind"
                    )
                self.assertEqual(
                    study.batch_invalid_attempt_count(fixture.runtime), 0
                )
            finally:
                fixture.close()

    def test_a_frozen_calibration_cannot_be_reattempted(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                fixture.freeze_calibration("rs3-d1-p1-calib")
                with self.assertRaisesRegex(FileExistsError, "already frozen"):
                    study.authorize_session(
                        fixture.runtime, "rs3-d1-p1-calib"
                    )
                self.assertEqual(
                    study.batch_invalid_attempt_count(fixture.runtime), 0
                )
            finally:
                fixture.close()

    def test_scouting_attempts_archive_the_report_and_count(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                atomic_json(
                    fixture.runtime / study.SCOUTING_REPORT_FILE,
                    scouting_report(status="INVALID_SCOUTING"),
                )
                receipt = study.archive_failed_attempt(
                    fixture.runtime, study.SCOUTING_SLOT, "no candidate"
                )
                self.assertEqual(receipt["attempt_number"], 1)
                self.assertEqual(receipt["batch_invalid_attempt_count"], 1)
                self.assertFalse(
                    (fixture.runtime / study.SCOUTING_REPORT_FILE).exists()
                )
            finally:
                fixture.close()


class ExecutionOrderTests(unittest.TestCase):
    def test_formal_run_before_scouting_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                with self.assertRaisesRegex(
                    PermissionError, "rs3-scouting"
                ):
                    study.authorize_session(
                        fixture.runtime, "rs3-d1-p1-r20"
                    )
            finally:
                fixture.close()

    def test_probe_requires_all_six_calibrations_first(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                for slot in study.CALIBRATION_SLOTS[:5]:
                    fixture.freeze_calibration(slot)
                with self.assertRaisesRegex(
                    PermissionError, "rs3-d2-p3-calib"
                ):
                    study.authorize_session(fixture.runtime, study.PROBE_SLOT)
                fixture.freeze_calibration(study.CALIBRATION_SLOTS[5])
                authorized = study.authorize_session(
                    fixture.runtime, study.PROBE_SLOT
                )
                self.assertTrue(authorized["authorized"])
                self.assertEqual(authorized["kind"], "probe")
            finally:
                fixture.close()

    def test_prepare_session_binds_the_frozen_phase_position(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                slot = "rs3-d1-p1-calib"
                bad = study.build_session(
                    run_id=slot,
                    init_frame_id=1,
                    init_image_sha256="c" * 64,
                    hold_route_s_m=PHASE_S_M[1],
                    tracker_identity=tracker_identity(),
                )
                with self.assertRaisesRegex(
                    study.Rate3StudyError, "hold_route_s_m"
                ):
                    study.prepare_session(fixture.runtime, bad)
            finally:
                fixture.close()


class PairingAnchorTests(unittest.TestCase):
    def test_startup_preflight_refuses_a_mismatched_calibration(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                fixture.freeze_all_calibrations()
                calibration = study.load_calibration(
                    fixture.runtime, "rs3-d1-p1-calib"
                )
                good = session_for(
                    "rs3-d1-p1-r20",
                    init_frame_id=calibration["reference_frame_id"],
                    init_image_sha256=calibration["reference_image_sha256"],
                )
                self.assertIsNotNone(
                    study.calibration_preflight(fixture.runtime, good)
                )
                wrong_frame = session_for(
                    "rs3-d1-p1-r20",
                    init_frame_id=calibration["reference_frame_id"] + 1,
                    init_image_sha256=calibration["reference_image_sha256"],
                )
                with self.assertRaisesRegex(
                    study.Rate3StudyError, "init frame"
                ):
                    study.calibration_preflight(fixture.runtime, wrong_frame)
                self.assertFalse(
                    (fixture.runtime / "runs" / "rs3-d1-p1-r20").exists()
                )
                self.assertFalse(
                    (fixture.runtime / study.SESSION_FILE).exists()
                )
            finally:
                fixture.close()

    def test_paired_runs_share_one_calibration_binding_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                fixture.freeze_all_calibrations()
                first = study.calibration_binding_sha256(
                    fixture.runtime, "rs3-d1-p1-calib"
                )
                second = study.calibration_binding_sha256(
                    fixture.runtime, "rs3-d1-p2-calib"
                )
                self.assertNotEqual(first, second)
                self.assertEqual(
                    first,
                    study.calibration_binding_sha256(
                        fixture.runtime, "rs3-d1-p1-calib"
                    ),
                )
            finally:
                fixture.close()


class CompletionGateTests(unittest.TestCase):
    def finalize(self, fixture, run_id, **kwargs):
        fixture.make_run(run_id, **kwargs)
        return study.finalize_attempt(fixture.runtime, run_id)

    def test_a_conforming_run_is_admissible(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                fixture.freeze_all_calibrations()
                status = self.finalize(fixture, "rs3-d1-p1-r20")
                self.assertTrue(status["admissible"], status["errors"])
                self.assertEqual(status["errors"], [])
                self.assertEqual(status["c_geom"], 0.9)
                self.assertEqual(status["c_track"], 0.45)
                self.assertEqual(status["c_track_given_geom"], 0.5)
                self.assertEqual(
                    status["completion_gate"]["simulation_duration_s"], PLANNED
                )
                self.assertGreaterEqual(
                    status["completion_gate"]["shared_host_wall_duration_s"],
                    PLANNED,
                )
                self.assertIsNotNone(status["evaluation_truth_sha256"])
                self.assertFalse(
                    (fixture.runtime / study.EVALUATION_TRUTH_FILE).exists()
                )
            finally:
                fixture.close()

    def test_short_simulation_wall_or_cutoff_is_rejected(self):
        cases = (
            ({"simulation_duration_s": 149.0}, "simulation_duration_not_reached"),
            ({"wall_duration_s": 100.0}, "shared_host_wall_duration_not_reached"),
            ({"evaluator_cutoff_s": 149.0}, "evaluator_cutoff_not_reached"),
            (
                {"evaluator_cutoff_s": 151.0},
                "evaluator_cutoff_delta_out_of_tolerance",
            ),
        )
        for overrides, expected in cases:
            with self.subTest(expected=expected):
                with tempfile.TemporaryDirectory() as directory:
                    fixture = Rate3StudyFixture(Path(directory))
                    try:
                        fixture.freeze_scouting()
                        fixture.freeze_all_calibrations()
                        status = self.finalize(
                            fixture, "rs3-d1-p1-r20", **overrides
                        )
                        self.assertFalse(status["admissible"])
                        self.assertIn(expected, status["errors"])
                    finally:
                        fixture.close()

    def test_right_censored_lost_must_equal_the_planned_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                fixture.freeze_all_calibrations()
                status = self.finalize(fixture, "rs3-d1-p1-r20", lost=True)
                self.assertTrue(status["admissible"], status["errors"])
                self.assertFalse(
                    status["completion_gate"][
                        "time_to_first_lost_right_censored"
                    ]
                )
            finally:
                fixture.close()

    def test_status_is_create_once(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                fixture.freeze_all_calibrations()
                first = self.finalize(fixture, "rs3-d1-p1-r20")
                self.assertEqual(
                    study.finalize_attempt(fixture.runtime, "rs3-d1-p1-r20"),
                    first,
                )
            finally:
                fixture.close()


class DisplacementAndLapTests(unittest.TestCase):
    def test_displacement_uses_adjacent_visible_pairs_only(self):
        records = [
            truth_record("r", 21, x=0.0, z=0.0, cx=0.0, cy=0.0),
            truth_record("r", 22, x=0.0, z=0.0, cx=3.0, cy=4.0),
            # frame 24 is not adjacent to 22 -> not a sample
            truth_record("r", 24, x=0.0, z=0.0, cx=13.0, cy=4.0),
            truth_record(
                "r", 25, x=0.0, z=0.0, cx=23.0, cy=4.0, visible=False
            ),
        ]
        summary = study.measure_displacement(records)
        self.assertEqual(summary["adjacent_frame_pairs"], 2)
        self.assertEqual(summary["qualified_pair_count"], 1)
        self.assertAlmostEqual(summary["median_px"], 5.0, places=12)

    def test_displacement_reports_nothing_when_no_pair_qualifies(self):
        summary = study.measure_displacement([])
        self.assertEqual(summary["qualified_pair_count"], 0)
        self.assertIsNone(summary["median_px"])

    def test_lap_period_counts_one_directional_crossings_only(self):
        route = [{"x": 0.0, "z": 0.0}, {"x": 10.0, "z": 0.0}]
        records = []
        for index, x in enumerate((-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)):
            records.append(
                truth_record(
                    "r", 21 + index, x=x, z=0.0, cx=0.0, cy=0.0, elapsed=index
                )
            )
        lap = study.measure_lap_period(
            records, route=route, release_simulation_s=10.0, difficulty="D2"
        )
        # -1 -> +1 happens at indices 0->1, 2->3, 4->5: three crossings.
        self.assertEqual(lap["crossing_count"], 3)
        self.assertEqual(len(lap["lap_intervals"]), 2)
        self.assertFalse(lap["gating"])
        self.assertAlmostEqual(lap["median_period_s"], 2.0, places=12)

    def test_lap_period_rejects_crossings_outside_the_lateral_tolerance(self):
        route = [{"x": 0.0, "z": 0.0}, {"x": 10.0, "z": 0.0}]
        records = [
            truth_record("r", 21, x=-1.0, z=9.0, cx=0.0, cy=0.0, elapsed=0),
            truth_record("r", 22, x=1.0, z=9.0, cx=0.0, cy=0.0, elapsed=1),
        ]
        lap = study.measure_lap_period(
            records, route=route, release_simulation_s=10.0, difficulty="D2"
        )
        self.assertEqual(lap["crossing_count"], 0)

    def test_d1_needs_four_crossings(self):
        route = [{"x": 0.0, "z": 0.0}, {"x": 10.0, "z": 0.0}]
        records = []
        for index, x in enumerate((-1.0, 1.0, -1.0, 1.0)):
            records.append(
                truth_record(
                    "r", 21 + index, x=x, z=0.0, cx=0.0, cy=0.0, elapsed=index
                )
            )
        lap = study.measure_lap_period(
            records, route=route, release_simulation_s=10.0, difficulty="D1"
        )
        self.assertEqual(lap["crossing_count"], 2)
        self.assertEqual(lap["status"], "LAP_MEASUREMENT_INSUFFICIENT")


class ProbeTests(unittest.TestCase):
    def prepare(self, fixture):
        fixture.freeze_scouting()
        fixture.freeze_all_calibrations()

    def probe_truth(self, displacement):
        return [
            truth_record(
                study.PROBE_SLOT,
                21 + index,
                x=128.0,
                z=116.0,
                cx=100.0 + index * displacement,
                cy=50.0,
                elapsed=index,
            )
            for index in range(20)
        ]

    def test_a0_is_evaluated_before_b1_to_b3(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                self.prepare(fixture)
                # A protocol-invalid run whose displacement would also be out
                # of range must still land on A0, never on B1.
                fixture.make_run(
                    study.PROBE_SLOT,
                    simulation_duration_s=10.0,
                    truth_records=self.probe_truth(200.0),
                )
                study.finalize_attempt(fixture.runtime, study.PROBE_SLOT)
                probe = study.build_probe(fixture.runtime)
                self.assertEqual(probe["branch"], "A0")
                self.assertEqual(probe["disposition"], "PROBE_ATTEMPT_INVALID")
                self.assertTrue(probe["a0_findings"])
            finally:
                fixture.close()

    def test_premature_probe_call_is_a_refusal_not_an_adjudication(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                self.prepare(fixture)
                with self.assertRaisesRegex(
                    study.Rate3StudyError, "no adjudicable probe attempt"
                ):
                    study.build_probe(fixture.runtime)
                self.assertFalse(study.probe_path(fixture.runtime).exists())
            finally:
                fixture.close()

    def test_a0_does_not_freeze_the_campaign_probe_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                self.prepare(fixture)
                fixture.make_run(
                    study.PROBE_SLOT,
                    simulation_duration_s=10.0,
                    truth_records=self.probe_truth(23.0),
                )
                study.finalize_attempt(fixture.runtime, study.PROBE_SLOT)
                probe = study.build_probe(fixture.runtime)
                self.assertEqual(probe["disposition"], "PROBE_ATTEMPT_INVALID")
                self.assertEqual(probe["attempt_number"], 1)
                self.assertFalse(probe["terminal"])
                # The terminal artifact stays unwritten, so the accepted
                # in-place rerun is still reachable.
                self.assertFalse(study.probe_path(fixture.runtime).exists())
                self.assertTrue(
                    study.probe_attempt_path(fixture.runtime, 1).is_file()
                )
                # Re-adjudicating the same attempt is idempotent.
                self.assertEqual(study.build_probe(fixture.runtime), probe)
            finally:
                fixture.close()

    def test_an_a0_attempt_then_an_in_place_rerun_reaches_b2(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                self.prepare(fixture)
                fixture.make_run(
                    study.PROBE_SLOT,
                    simulation_duration_s=10.0,
                    truth_records=self.probe_truth(23.0),
                )
                study.finalize_attempt(fixture.runtime, study.PROBE_SLOT)
                self.assertEqual(
                    study.build_probe(fixture.runtime)["disposition"],
                    "PROBE_ATTEMPT_INVALID",
                )
                receipt = study.archive_failed_attempt(
                    fixture.runtime, study.PROBE_SLOT, "A0: short run"
                )
                self.assertEqual(receipt["attempt_number"], 1)

                fixture.make_run(
                    study.PROBE_SLOT,
                    conditional=0.4,
                    truth_records=self.probe_truth(23.0),
                )
                study.finalize_attempt(fixture.runtime, study.PROBE_SLOT)
                probe = study.build_probe(fixture.runtime)
                self.assertEqual(probe["branch"], "B2")
                self.assertEqual(probe["disposition"], "PROBE_CONFIRMS_D2")
                self.assertEqual(probe["attempt_number"], 2)
                self.assertTrue(probe["terminal"])
                self.assertEqual(len(probe["prior_attempt_sha256"]), 1)
                self.assertTrue(study.probe_path(fixture.runtime).is_file())
                # The formal phase is reachable again.
                authorized = study.authorize_session(
                    fixture.runtime, study.FORMAL_SLOT_ORDER[0]
                )
                self.assertTrue(authorized["authorized"])
            finally:
                fixture.close()

    def test_exhausting_the_probe_slot_blocks_the_probe_terminally(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                self.prepare(fixture)
                for attempt in range(1, 4):
                    fixture.make_run(
                        study.PROBE_SLOT,
                        simulation_duration_s=10.0,
                        truth_records=self.probe_truth(23.0),
                    )
                    study.finalize_attempt(fixture.runtime, study.PROBE_SLOT)
                    probe = study.build_probe(fixture.runtime)
                    self.assertEqual(probe["attempt_number"], attempt)
                    if attempt < study.MAX_ATTEMPTS_PER_SLOT:
                        self.assertEqual(
                            probe["disposition"], "PROBE_ATTEMPT_INVALID"
                        )
                        study.archive_failed_attempt(
                            fixture.runtime, study.PROBE_SLOT, f"A0 {attempt}"
                        )
                self.assertEqual(probe["disposition"], "BLOCKED_PROBE")
                self.assertTrue(probe["terminal"])
                self.assertTrue(study.probe_path(fixture.runtime).is_file())
                with self.assertRaisesRegex(
                    PermissionError, "rs3-probe-d2"
                ):
                    study.authorize_session(
                        fixture.runtime, study.FORMAL_SLOT_ORDER[0]
                    )
            finally:
                fixture.close()

    def test_b1_falsifies_the_displacement_model(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                self.prepare(fixture)
                fixture.make_run(
                    study.PROBE_SLOT, truth_records=self.probe_truth(50.0)
                )
                study.finalize_attempt(fixture.runtime, study.PROBE_SLOT)
                probe = study.build_probe(fixture.runtime)
                self.assertEqual(probe["branch"], "B1")
                self.assertEqual(probe["disposition"], "PROBE_MODEL_INVALID")
                self.assertIsNone(probe["selected_d2_speed_mps"])
            finally:
                fixture.close()

    def test_b2_confirms_d2_and_reads_all_three_quantities(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                self.prepare(fixture)
                fixture.make_run(
                    study.PROBE_SLOT,
                    conditional=0.4,
                    truth_records=self.probe_truth(23.0),
                )
                study.finalize_attempt(fixture.runtime, study.PROBE_SLOT)
                probe = study.build_probe(fixture.runtime)
                self.assertEqual(probe["branch"], "B2")
                self.assertEqual(probe["selected_d2_speed_mps"], 8.0)
                # BC-DRB-6
                self.assertEqual(probe["c_geom"], 0.9)
                self.assertEqual(probe["c_track"], 0.45)
                self.assertEqual(probe["c_track_given_geom"], 0.4)
            finally:
                fixture.close()

    def test_b3_triggers_the_single_downshift(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                self.prepare(fixture)
                fixture.make_run(
                    study.PROBE_SLOT,
                    conditional=0.10,
                    truth_records=self.probe_truth(23.0),
                )
                study.finalize_attempt(fixture.runtime, study.PROBE_SLOT)
                probe = study.build_probe(fixture.runtime)
                self.assertEqual(probe["branch"], "B3")
                self.assertEqual(
                    probe["disposition"], "PROBE_TRIGGERS_DOWNSHIFT"
                )
                self.assertEqual(probe["selected_d2_speed_mps"], 6.0)
                with self.assertRaisesRegex(study.Rate3StudyError, "0b"):
                    study.select_d2(
                        fixture.runtime,
                        speed_mps=6.0,
                        r20_config=study.SCENARIO_CONFIGS[("D2", 20)],
                        r5_config=study.SCENARIO_CONFIGS[("D2", 5)],
                        difficulty_audit=Path(directory) / "missing.json",
                    )
            finally:
                fixture.close()


class DecisionArtifactTests(unittest.TestCase):
    def build_all(self, fixture, conditional):
        fixture.freeze_scouting()
        fixture.freeze_all_calibrations()
        fixture.complete_probe()
        for run_id in study.FORMAL_SLOT_ORDER:
            identity = study.slot_identity(run_id)
            fixture.make_run(
                run_id,
                conditional=conditional(
                    str(identity["difficulty"]), int(identity["rate_hz"])
                ),
            )
            study.finalize_attempt(fixture.runtime, run_id)

    def test_decision_is_create_once_and_revalidates(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                self.build_all(
                    fixture,
                    lambda difficulty, rate: (
                        0.90
                        if difficulty == "D1"
                        else (0.70 if rate == 20 else 0.40)
                    ),
                )
                decision = study.build_decision(fixture.runtime)
                self.assertEqual(
                    decision["schema_version"], rate3_decision.DECISION_SCHEMA
                )
                self.assertEqual(
                    decision["final_action"], "M2_RATE_CONTRAST_ESTABLISHED"
                )
                self.assertEqual(decision["dispositions"]["D1"], "CEILING")
                self.assertEqual(len(decision["runs"]), 12)
                self.assertEqual(
                    decision["phase_route_s_m"], list(PHASE_S_M)
                )
                self.assertEqual(decision["batch_invalid_attempt_count"], 0)
                self.assertEqual(
                    study.build_decision(fixture.runtime), decision
                )
                self.assertEqual(
                    study.validate_decision(fixture.runtime), decision
                )
            finally:
                fixture.close()

    def test_decision_records_unconditional_fields_for_every_run(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                self.build_all(
                    fixture,
                    lambda difficulty, rate: 0.90 if rate == 20 else 0.85,
                )
                decision = study.build_decision(fixture.runtime)
                for row in decision["runs"]:
                    self.assertIn("c_geom", row)
                    self.assertIn("c_track", row)
                    self.assertIsNotNone(row["calibration_sha256"])
                    self.assertIsNotNone(row["evaluation_truth_sha256"])
            finally:
                fixture.close()

    def test_tampering_with_a_run_metric_fails_revalidation(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                self.build_all(
                    fixture,
                    lambda difficulty, rate: (
                        0.90
                        if difficulty == "D1"
                        else (0.70 if rate == 20 else 0.40)
                    ),
                )
                study.build_decision(fixture.runtime)
                metrics_path = (
                    fixture.runtime
                    / "runs"
                    / "rs3-d2-p1-r20"
                    / "metrics.final.json"
                )
                metrics = json.loads(metrics_path.read_text())
                metrics["aggregate"]["c_track_given_geom"] = 0.999
                metrics_path.write_text(json.dumps(metrics))
                with self.assertRaises(study.Rate3StudyError):
                    study.validate_decision(fixture.runtime)
            finally:
                fixture.close()

    def test_a_run_initialised_from_the_wrong_product_is_not_admissible(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                fixture.freeze_all_calibrations()
                fixture.make_run(
                    "rs3-d1-p1-r5",
                    calibration_slot_override="rs3-d1-p2-calib",
                )
                status = study.finalize_attempt(fixture.runtime, "rs3-d1-p1-r5")
                self.assertFalse(status["admissible"])
                self.assertIn("calibration_init_frame_mismatch", status["errors"])
                self.assertIn("calibration_init_image_mismatch", status["errors"])
            finally:
                fixture.close()

    def test_decision_time_pairing_backstop_blocks_the_difficulty_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                self.build_all(
                    fixture,
                    lambda difficulty, rate: (
                        0.90
                        if difficulty == "D1"
                        else (0.70 if rate == 20 else 0.40)
                    ),
                )
                # Depth defence: if the startup preflight ever let a pair
                # through with two different frozen products, the decision
                # must still refuse the whole cell (BC-DRB-5).
                status_path = (
                    fixture.runtime
                    / "runs"
                    / "rs3-d1-p1-r5"
                    / "rate3-status.json"
                )
                status = json.loads(status_path.read_text())
                status["calibration_sha256"] = "f" * 64
                status_path.write_text(json.dumps(status))
                decision = study.build_decision(fixture.runtime)
                self.assertEqual(decision["final_action"], "BLOCKED_INCOMPLETE")
                findings = decision["pairing_anchor"]["findings"]["D1"]
                self.assertTrue(findings)
                self.assertIn("BC-DRB-5", findings[0])
                self.assertEqual(
                    decision["dispositions"]["D1"], "BLOCKED_INCOMPLETE_CELL"
                )
                self.assertEqual(
                    decision["dispositions"]["D2"], "RATE_EFFECT_POSITIVE"
                )
            finally:
                fixture.close()


class LapPeriodIntegrationTests(unittest.TestCase):
    def test_finalize_writes_a_report_only_lap_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Rate3StudyFixture(Path(directory))
            try:
                fixture.freeze_scouting()
                fixture.freeze_all_calibrations()
                fixture.make_run("rs3-d1-p1-r20")
                status = study.finalize_attempt(fixture.runtime, "rs3-d1-p1-r20")
                lap_path = (
                    fixture.runtime / "runs" / "rs3-d1-p1-r20" / "lap_period.json"
                )
                self.assertTrue(lap_path.is_file())
                lap = json.loads(lap_path.read_text())
                self.assertFalse(lap["gating"])
                self.assertIn("start_section", lap)
                self.assertEqual(
                    status["lap_period_status"], lap["status"]
                )
                # The lap artifact never affects admissibility.
                self.assertTrue(status["admissible"], status["errors"])
            finally:
                fixture.close()


if __name__ == "__main__":
    unittest.main()
