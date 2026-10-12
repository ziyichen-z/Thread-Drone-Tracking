"""P1-ENG-LOOP-002 AC-8：`tools/eng_loop2/analyze_play.py` 四类数字唯一算法（§3.5）。

全部夹具在 tempfile 临时目录合成（会话 JSONL、results.jsonl、publish-receipts.jsonl、段日志、
真值行、旁车、场景副本、迷你几何）；不读真实归档。

直接运行本文件 `--write-evidence <path>` 会对「全面夹具」跑 `score` 并写出
`docs/evidence/P1-ENG-LOOP-002-four-numbers-fixture.json`（生成命令写入 JSON）。
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
from typing import Any, Callable, Iterable
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.dist_data import bind_layout, project_boxes  # noqa: E402
from tools.eng_loop2 import analyze_play as ap  # noqa: E402

FOCAL = 240.0 / math.tan(math.radians(30.0))
STATIC = "Vehicle_Test_SUV (1)"
FAR_VEHICLE = "Vehicle_Taxi (9)"
RED_BOX = [0.72, 0.29, 0.08, 0.07]
RED_TARGET = (10.0, 0.2, 5.0)
BODY = (0.0, 25.0, 0.0)
MISSING = object()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mini_instances() -> list[dict[str, Any]]:
    return [
        {"scene_object_name": STATIC, "canonical_name": "Vehicle_Test_SUV", "group": "vehicle",
         "min_x_m": -2.0, "max_x_m": 2.0, "min_y_m": 0.0, "max_y_m": 1.5, "min_z_m": -1.0, "max_z_m": 1.0},
        {"scene_object_name": FAR_VEHICLE, "canonical_name": "Vehicle_Taxi", "group": "vehicle",
         "min_x_m": 60.0, "max_x_m": 64.0, "min_y_m": 0.0, "max_y_m": 1.5, "min_z_m": 60.0, "max_z_m": 62.0},
        {"scene_object_name": "Building_X", "canonical_name": "Building_X", "group": "building",
         "min_x_m": 100.0, "max_x_m": 110.0, "min_y_m": 0.0, "max_y_m": 20.0, "min_z_m": 100.0, "max_z_m": 110.0},
    ]


def base_sidecar(frame_id: int, time_s: float, scenario_id: str) -> dict[str, Any]:
    return {
        "schema_version": "tethered-sensor-frame/v3",
        "scenario_id": scenario_id,
        "frame_id": frame_id,
        "simulation_time_s": time_s,
        "camera_position_world_m": list(BODY),
        "camera_forward_world": [0.0, -1.0, 0.0],
        "camera_right_world": [1.0, 0.0, 0.0],
        "camera_up_world": [0.0, 0.0, 1.0],
        "vertical_fov_deg": 60.0,
        "width": 640,
        "height": 480,
        "intrinsics_px": {"fx": FOCAL, "fy": FOCAL, "cx": 320.0, "cy": 240.0},
    }


def static_box() -> list[float]:
    camera = project_boxes.Camera.from_sidecar(base_sidecar(0, 0.0, "x"))
    projected = {p.object_id: p for p in project_boxes.project_instances(camera, mini_instances())}
    assert projected[STATIC].status == "OK", projected[STATIC]
    return list(projected[STATIC].visible_norm_xywh)


STATIC_BOX = static_box()


class Fx:
    """会话 + Unity 侧合成归档（字段按 `controller/language_loop.py` 与本项新增契约）。"""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.session = self.root / "session"
        self.unity = self.root / "unity"
        self.rows: list[dict[str, Any]] = []
        self.results: list[dict[str, Any]] = []
        self.publish: list[dict[str, Any]] = []
        self.seg: list[dict[str, Any]] = []
        self.epoch = 0
        self.seq = 0
        self.qn = 0
        self.rn = 0
        self.dn = 0
        self.tn = 0
        self.next_frame = 0
        self.time_fn: Callable[[int], float] = lambda f: 0.2 * f + 0.1
        self.red_visible: Callable[[int], bool] = lambda f: True
        self.red_box: Callable[[int], list[float]] = lambda f: RED_BOX
        self.truth_missing: set[int] = set()
        self.sidecar_missing: set[int] = set()
        self.digest_null: set[int] = set()
        self.tamper: dict[int, Callable[[dict[str, Any]], None]] = {}
        self.copy_scenario_id = "deterministic-loop-untethered"
        self.reference = {"scenario_id": "deterministic-loop-default", "scene_adjustments": {"vehicle_relocations": [{"name": "a"}]}}
        self.copy_doc: dict[str, Any] | None = {"scenario_id": self.copy_scenario_id, "scene_adjustments": copy.deepcopy(self.reference["scene_adjustments"])}
        self.manifest_sha_override: str | None = None
        self.session_jpegs: dict[int, bytes] = {}

    # --- 会话 JSONL ---

    def j(self, kind: str, **fields: Any) -> dict[str, Any]:
        row = {
            "at_unix_s": 1000.0 + len(self.rows),
            "at_monotonic_s": 50.0 + len(self.rows),
            "session_id": "s",
            "kind": kind,
            "state": fields.pop("state", "QUERYING"),
            "epoch": fields.pop("epoch", self.epoch),
            "sequence": self.seq,
            **fields,
        }
        self.rows.append(row)
        return row

    def receipt(self, action: str | None, rid: str | None, outcome: str = "APPLIED", detail: str | None = None, **extra: Any) -> dict[str, Any]:
        self.seq += 1
        return self.j("receipt", receipt={"request_id": rid, "action": action, "outcome": outcome, "at_sequence": self.seq}, detail=detail, **extra)

    def accept(self, rid: str, *, action: str = "ask", intent: Any = MISSING, delay: float = 0.0, outcome: str = "APPLIED",
               detail: str | None = None, bump: bool = True, epoch: int | None = None) -> None:
        if bump:
            self.epoch += 1
        extra: dict[str, Any] = {"delay_s": delay}
        if intent is not MISSING:
            extra["intent"] = intent
        if epoch is not None:
            extra["epoch"] = epoch
        self.receipt(action, rid, outcome, detail, **extra)

    def submit(self, *, attempt: int = 1, epoch: int | None = None) -> str:
        self.qn += 1
        qid = f"s-q{self.qn}"
        self.j("query_submitted", query_id=qid, purpose="designate", frame_id=max(self.next_frame - 1, 0), attempt=attempt,
               epoch=self.epoch if epoch is None else epoch, queued=False)
        return qid

    def result(self, qid: str, status: str, *, request_id: str | None = None, attempt: int = 1, epoch: int | None = None,
               reject_reason: str | None = None, last_status: str | None = None, last_reject_reason: str | None = None,
               frame_id: int | None = None, frame_sha256: str | None = None) -> None:
        self.rn += 1
        self.results.append({
            "query_id": qid, "result_id": f"s-res{self.rn}", "request_id": request_id,
            "epoch": self.epoch if epoch is None else epoch, "attempt": attempt, "attempt_limit": 3, "purpose": "designate",
            "frame_id": frame_id, "frame_sha256": frame_sha256, "status": status, "reject_reason": reject_reason,
            "last_status": last_status, "last_reject_reason": last_reject_reason, "candidates": [],
            "model": {"finish_reason": "stop", "gen_tokens": 12}, "raw_output": "{}", "parse_error": None,
        })

    def present(self, qid: str, status: str = "unique", *, request_id: str | None = None, delay: float = 0.0) -> None:
        self.j("result_arrived", query_id=qid, status=status, head_frame_id=self.next_frame - 1, delay_s=delay, request_id=request_id)
        self.result(qid, status, request_id=request_id)
        self.j("result_presented", query_id=qid, result_id=f"s-res{self.rn}", status=status, delay_s=delay, head_frame_id=self.next_frame - 1)
        self.j("state", state="AWAITING_CONFIRMATION", reason=None)

    def ask_presented(self, rid: str, *, intent: Any = ap.RED_CAR, action: str = "ask") -> str:
        self.accept(rid, action=action, intent=intent)
        qid = self.submit()
        self.present(qid)
        return qid

    def designate(self, result: str, *, k: int | None = None, h: int | None = None, library: int = 7, did: int | None = None) -> tuple[int, str | None]:
        if did is None:
            self.dn += 1
            did = self.dn
        h = self.next_frame - 1 if h is None else h
        k = h - 2 if k is None else k
        self.j("designation", designation={"designation_id": did, "frame_id_k": k, "head_frame_id": h, "result": result,
                                           "resolution_level": 1, "track_id": library, "level1": {}, "level2": None, "candidates": []},
               candidate_index=0)
        track = None
        if result in {"BOUND", "BOUND_COASTING"}:
            track = self.bind(library, h)
        return did, track

    def bind(self, library: int, frame_id: int) -> str:
        self.tn += 1
        track = f"s-t{self.tn}"
        self.j("pointer_bound", track_id=track, library_track_id=library, frame_id=frame_id)
        return track

    def confirm_designate(self, result: str = "BOUND", **kw: Any) -> tuple[int, str | None]:
        self.receipt("confirm", f"c{len(self.rows)}")
        return self.designate(result, **kw)

    def stop(self, *, abandoned: list[str] | None = None) -> None:
        self.receipt("stop", f"stop{len(self.rows)}")
        self.epoch += 1
        if abandoned is not None:
            self.j("worker_abandoned", detail="join_timeout", query_ids=abandoned, model_calls_started=1)
        self.j("state", state="TERMINAL", reason="operator_stop")

    def terminal(self, reason: str) -> None:
        self.j("state", state="TERMINAL", reason=reason)

    # --- 帧 ---

    def sidecar_bytes(self, frame_id: int) -> bytes:
        return json.dumps(base_sidecar(frame_id, self.time_fn(frame_id), self.copy_scenario_id), sort_keys=True).encode("utf-8")

    def process(self, count: int, box: Any = None, *, published: bool = True) -> list[int]:
        frames = list(range(self.next_frame, self.next_frame + count))
        self.next_frame += count
        digests, reasons = [], []
        for frame_id in frames:
            value = box(frame_id) if callable(box) else box
            self.seg.append({
                "frame_id": frame_id, "ok": value is not None, "box_norm": value, "published_observation": bool(value is not None and published),
                "simulation_time_s": self.time_fn(frame_id), "capture_monotonic_s": 7.0 + frame_id, "state": "TRACKING" if value else "LOST",
            })
            if frame_id in self.digest_null:
                digests.append(None)
                reasons.append("metadata_unreadable")
            else:
                digests.append(_sha(self.sidecar_bytes(frame_id)))
                reasons.append(None)
        self.j("frames_processed", count=len(frames), frame_ids=frames, raw_states=["TRACKING"] * len(frames),
               metadata_sha256=digests, metadata_sha256_missing_reason=reasons)
        return frames

    # --- 落盘 ---

    def write(self) -> ap.ArchivePaths:
        self.session.mkdir(parents=True, exist_ok=True)
        (self.unity / "frames").mkdir(parents=True, exist_ok=True)
        run = self.unity / "runs" / "s-resident1"
        run.mkdir(parents=True, exist_ok=True)
        (self.session / "frames").mkdir(exist_ok=True)
        for name, rows in (("language-session.jsonl", self.rows), ("results.jsonl", self.results), ("publish-receipts.jsonl", self.publish)):
            (self.session / name).write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
        for frame_id, data in self.session_jpegs.items():
            (self.session / "frames" / f"frame_{frame_id:010d}.jpg").write_bytes(data)
        (run / "frames.jsonl").write_text("".join(json.dumps(r) + "\n" for r in self.seg), encoding="utf-8")
        last = max(self.next_frame, 1)
        truth_lines = []
        for frame_id in range(last):
            if frame_id in self.truth_missing:
                continue
            visible = self.red_visible(frame_id)
            red_box = self.red_box(frame_id)
            truth_lines.append(json.dumps({
                "schema_version": "p1-m3-body-truth/v2", "frame_id": frame_id, "simulation_time_s": self.time_fn(frame_id),
                "capture_monotonic_s": 7.0 + frame_id,
                "target_world_x_m": RED_TARGET[0], "target_world_y_m": RED_TARGET[1], "target_world_z_m": RED_TARGET[2],
                "body_world_x_m": BODY[0], "body_world_y_m": BODY[1], "body_world_z_m": BODY[2],
                "truth_box_available": visible, "truth_box_x": red_box[0], "truth_box_y": red_box[1],
                "truth_box_width": red_box[2], "truth_box_height": red_box[3],
            }) + "\n")
            if frame_id not in self.sidecar_missing:
                doc = json.loads(self.sidecar_bytes(frame_id))
                data = self.sidecar_bytes(frame_id)
                if frame_id in self.tamper:
                    self.tamper[frame_id](doc)
                    data = json.dumps(doc, sort_keys=True).encode("utf-8")
                (self.unity / "frames" / f"frame_{frame_id:010d}.json").write_bytes(data)
        (self.unity / "m3_body_truth.jsonl").write_text("".join(truth_lines), encoding="utf-8")
        reference = self.root / "scenario.default.json"
        reference.write_bytes(json.dumps(self.reference, sort_keys=True).encode("utf-8"))
        scenario_copy = self.session / "scenario_config.json"
        copy_sha = None
        if self.copy_doc is not None:
            data = json.dumps(self.copy_doc, sort_keys=True).encode("utf-8")
            scenario_copy.write_bytes(data)
            copy_sha = _sha(data)
        manifest = {"session_id": "s", "run_id": "s-resident1",
                    "body_planner": {"policy": "standoff", "effective_scenario_sha256": self.manifest_sha_override or copy_sha}}
        (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return ap.ArchivePaths(self.session, self.unity, None, scenario_copy if self.copy_doc is not None else None, reference)

    def geometry(self) -> dict[str, Any]:
        reference = json.dumps(self.reference, sort_keys=True).encode("utf-8")
        return {"schema_version": "mini", "source_scenario_sha256": _sha(reference), "scene_adjustments_applied": True,
                "instances": mini_instances()}

    def score(self) -> dict[str, Any]:
        paths = self.write()
        return ap.score_archive(paths, geometry=self.geometry())

    def scorer(self) -> ap.Scorer:
        paths = self.write()
        scorer = ap.Scorer(ap.Archive(paths, geometry=self.geometry()))
        scorer.run()
        return scorer


def funnel_of(report: dict[str, Any]) -> dict[str, str]:
    return {s["request_id"]: s["funnel"] for s in report["samples"]}


RED_SRC = "red_car_unity_truth"
STATIC_SRC = "static_vehicle_geometry_approx"
INVALID_SRC = "intent_not_valid"


def table(report: dict[str, Any], number: str, source: str = RED_SRC) -> dict[str, Any]:
    """§3.5.1 分列：取某数字在某真值来源下的表（报告不含合并表）。"""
    key = "funnel_scope_by_truth_source" if number == "explicit_report" else "by_truth_source"
    return report[number][key][source]


def raw_total(report: dict[str, Any], number: str) -> int:
    return report[number]["conservation"]["n_raw_total"]


def build_comprehensive(fx: Fx) -> None:
    """全面夹具：十二类终态各至少一例、respecify、两种无效意图、覆盖四表各类。"""
    on_red = lambda f: RED_BOX  # noqa: E731
    fx.process(20)
    # 1 BOUND_DIRECT(bound)：红车 ON，覆盖数字一/二/三、time-to-center 在画外（不居中）。
    fx.ask_presented("r-bound")
    fx.confirm_designate("BOUND")
    fx.process(80, on_red)
    # 2 respecify：静止车 BOUND，ON。
    fx.ask_presented("r-respecify", intent=STATIC, action="respecify")
    fx.confirm_designate("BOUND", library=8)
    fx.process(80, lambda f: STATIC_BOX)
    # 3 VLM_REPORTED(none)：前两次 none（request_id 为 null 的恢复重试行）、末次 retry_exhausted。无意图。
    fx.accept("r-none", intent=MISSING)
    for attempt in (1, 2):
        q = fx.submit(attempt=attempt)
        fx.result(q, "none", request_id="r-none" if attempt == 1 else None, attempt=attempt)
    q = fx.submit(attempt=3)
    fx.result(q, "retry_exhausted", attempt=3, last_status="none")
    fx.process(2)
    # 4 QUERY_FAILED(parse_failed)：未知意图键。
    fx.accept("r-parse", intent="Vehicle_Not_There")
    q = fx.submit(attempt=3)
    fx.result(q, "retry_exhausted", attempt=3, last_status="parse_failed")
    # 5 STALE_REJECTED(query)
    fx.accept("r-stale", intent=ap.RED_CAR)
    q = fx.submit(attempt=3)
    fx.result(q, "retry_exhausted", attempt=3, last_status="stale_rejected", last_reject_reason="frames_late_exceeded")
    # 6 OPERATOR_REJECTED（首次 none、第 2 次给候选，不入 VLM_REPORTED）
    fx.accept("r-reject", intent=ap.RED_CAR)
    q = fx.submit()
    fx.result(q, "none", request_id="r-reject")
    q = fx.submit(attempt=2)
    fx.present(q)
    fx.receipt("reject", "rej1")
    fx.process(2)
    # 7 UNCONFIRMED_SUPERSEDED
    fx.ask_presented("r-unconfirmed")
    # 8 SUPERSEDED(query_pending)
    fx.accept("r-pending", intent=ap.RED_CAR)
    fx.submit()
    # 9 DESIGNATE_REPORTED(AMBIGUOUS)
    fx.ask_presented("r-ambiguous")
    fx.confirm_designate("AMBIGUOUS")
    fx.process(2)
    # 10 INTERRUPTED(designation_unavailable, resident_loop_absent)
    fx.ask_presented("r-unavailable")
    fx.receipt("confirm", "c-unavail")
    fx.j("designation_unavailable", reason="resident_loop_absent", frame_id=fx.next_frame - 1)
    # 11 ACQUIRE_PATH(coasting_timeout)：BOUND_COASTING、重复 COASTING_TO_TRACK_ENDED 行、采纳后 ON。
    fx.ask_presented("r-coast")
    did, track = fx.confirm_designate("BOUND_COASTING", library=9)
    fx.process(5)
    fx.j("COASTING_TO_TRACK_ENDED", designation_id=did, track_id=9, frame_id=fx.next_frame - 1, cause="coasting_limit")
    fx.j("COASTING_TO_TRACK_ENDED", designation_id=did, track_id=9, frame_id=fx.next_frame - 1, cause="coasting_limit")
    fx.j("segment_retired", track_id=track, reason="operator_release", to_frame_id=fx.next_frame - 1)
    fx.j("acquire_started", designation_id=did)
    fx.process(3)
    fx.j("acquire_adopted", designation_id=did, track_id=11, frame_id=fx.next_frame - 1)
    fx.bind(11, fx.next_frame - 1)
    fx.process(80, on_red)
    # 12 BOUND_NO_PUBLISH：绑定后 40 帧无指针框。
    fx.ask_presented("r-nopublish")
    fx.confirm_designate("BOUND", library=12)
    fx.process(40)
    # 13 静默错误：红车意图、指针在静止车上（OFF）→ RESOLVED_WRONG 与 WRONG_CAPTURE 同时成立，只计 1。
    fx.ask_presented("r-wrong")
    fx.confirm_designate("BOUND", library=13)
    fx.process(80, lambda f: STATIC_BOX)
    # 14 ACQUIRE_PATH(track_ended) + ACQUIRE_FAILED(geometry_rejected)
    fx.ask_presented("r-acqfail")
    did, _ = fx.confirm_designate("TRACK_ENDED")
    fx.process(2)
    fx.j("acquire_failed", designation_id=did, cause="geometry_rejected", candidates=[])
    fx.process(2)
    # 15/16 C1：两个受理行同 request_id。
    fx.accept("r-dup", intent=ap.RED_CAR)
    fx.submit()
    fx.accept("r-dup", intent=ap.RED_CAR)
    fx.submit()
    # REQUEST_INVALID（含 instruction_unsupported）不成样本。
    fx.receipt("ask", "r-invalid", "REQUEST_INVALID", "instruction_unsupported")
    # 17 UNCONFIRMED_AT_END(operator_stop)
    fx.ask_presented("r-atend")
    fx.process(2)
    fx.stop()


class FunnelTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def fx(self, name: str = "a") -> Fx:
        return Fx(self.root / name)

    def test_twelve_classes_each_once_and_conservation(self) -> None:
        fx = self.fx()
        build_comprehensive(fx)
        report = fx.score()
        classes = report["funnel"]["classes"]
        for klass in ap.FUNNEL_CLASSES:
            self.assertGreaterEqual(classes[klass], 1, klass)
        self.assertEqual(sum(classes.values()), report["funnel"]["n_accepted"])
        self.assertEqual(sum(report["intent_status"].values()), report["funnel"]["n_accepted"])
        funnel = funnel_of(report)
        self.assertEqual(funnel["r-respecify"], "BOUND_DIRECT(bound)")
        self.assertEqual(funnel["r-unconfirmed"], "UNCONFIRMED_SUPERSEDED")
        self.assertEqual(funnel["r-atend"], "UNCONFIRMED_AT_END(operator_stop)")
        self.assertEqual(funnel["r-coast"], "ACQUIRE_PATH(coasting_timeout)")
        self.assertEqual(funnel["r-acqfail"], "ACQUIRE_PATH(track_ended)")
        self.assertEqual(funnel["r-unavailable"], "INTERRUPTED(designation_unavailable, resident_loop_absent)")
        self.assertEqual(funnel["r-ambiguous"], "DESIGNATE_REPORTED(AMBIGUOUS)")
        self.assertEqual(funnel["r-pending"], "SUPERSEDED(query_pending)")
        self.assertEqual(table(report, "number_one")["counts"].get("BOUND_NO_PUBLISH"), 1)
        cross = report["funnel_x_intent_status"]
        self.assertEqual(sum(sum(v.values()) for v in cross.values()), report["funnel"]["n_accepted"])
        self.assertNotIn("通过", json.dumps(report, ensure_ascii=False))

    def test_conservation_violation_raises(self) -> None:
        fx = self.fx()
        fx.ask_presented("r1")
        fx.stop()
        scorer = ap.Scorer(ap.Archive(fx.write(), geometry=fx.geometry()))
        scorer.build_samples()
        scorer.attribute()
        for sample in scorer.samples:
            scorer.classify(sample)
        scorer.samples[0].klass = "NOT_A_CLASS"
        with self.assertRaises(ap.ConservationError):
            scorer.report()

    def _pending_then(self, finish: Callable[[Fx], None], name: str) -> dict[str, str]:
        fx = self.fx(name)
        fx.process(3)
        fx.accept("r1", intent=ap.RED_CAR)
        fx.submit()
        finish(fx)
        report = fx.score()
        return {s["request_id"]: (s["funnel"], s["worker_abandoned"]) for s in report["samples"]}

    def test_query_pending_stop_with_worker_abandoned(self) -> None:
        out = self._pending_then(lambda fx: fx.stop(abandoned=["s-q1"]), "stop_ab")
        self.assertEqual(out["r1"], ("INTERRUPTED(query_pending, operator_stop)", True))

    def test_query_pending_stop_without_worker_abandoned(self) -> None:
        out = self._pending_then(lambda fx: fx.stop(), "stop_noab")
        self.assertEqual(out["r1"], ("INTERRUPTED(query_pending, operator_stop)", False))

    def test_query_pending_duration_reached(self) -> None:
        out = self._pending_then(lambda fx: fx.terminal("duration_reached"), "dur")
        self.assertEqual(out["r1"][0], "INTERRUPTED(query_pending, duration_reached)")

    def test_query_pending_backend_fatal_without_result_row(self) -> None:
        def finish(fx: Fx) -> None:
            fx.j("backend_fatal", reason="worker_stuck", detail="health")
            fx.terminal("backend_fatal")

        out = self._pending_then(finish, "fatal")
        self.assertEqual(out["r1"][0], "INTERRUPTED(query_pending, backend_fatal)")

    def test_query_pending_log_truncated_without_terminal(self) -> None:
        out = self._pending_then(lambda fx: fx.process(2), "trunc")
        self.assertEqual(out["r1"][0], "INTERRUPTED(query_pending, log_end)")

    def test_presentation_pending_stop_and_new_ask(self) -> None:
        fx = self.fx("pp_stop")
        fx.accept("r1", intent=ap.RED_CAR, delay=2.0)
        q = fx.submit()
        fx.j("result_arrived", query_id=q, status="unique", head_frame_id=0, delay_s=2.0, request_id="r1")
        fx.stop()
        self.assertEqual(funnel_of(fx.score())["r1"], "INTERRUPTED(presentation_pending, operator_stop)")
        fx = self.fx("pp_ask")
        fx.accept("r1", intent=ap.RED_CAR, delay=2.0)
        q = fx.submit()
        fx.j("result_arrived", query_id=q, status="ambiguous", head_frame_id=0, delay_s=2.0, request_id="r1")
        fx.accept("r2", intent=ap.RED_CAR)
        fx.j("presentation_discarded", query_id=q, reason="epoch_changed")
        fx.submit()
        report = fx.score()
        self.assertEqual(funnel_of(report)["r1"], "SUPERSEDED(presentation_pending)")
        self.assertEqual(report["attribution_conflicts"], {})

    def test_query_pending_superseded_in_flight_queued_and_waiting(self) -> None:
        # 在途：旧查询回包记 IGNORED_STALE_EPOCH（只带 query_id 与旧 epoch）。
        fx = self.fx("inflight")
        fx.accept("r1", intent=ap.RED_CAR)
        q = fx.submit()
        fx.accept("r2", intent=ap.RED_CAR)
        fx.submit()
        fx.results.append({"query_id": q, "status": "IGNORED_STALE_EPOCH", "epoch": 1, "current_epoch": 2, "purpose": "designate"})
        self.assertEqual(funnel_of(fx.score())["r1"], "SUPERSEDED(query_pending)")
        # 排队：被替换的 pending 写 SUPERSEDED 收据（action null）。
        fx = self.fx("queued")
        fx.accept("r1", intent=ap.RED_CAR, outcome="PENDING_QUEUED")
        fx.submit()
        fx.epoch += 1
        fx.receipt(None, "r1", "SUPERSEDED", "pending_superseded")
        fx.submit()
        fx.accept("r2", intent=ap.RED_CAR, outcome="PENDING_QUEUED", bump=False)
        report = fx.score()
        self.assertEqual(funnel_of(report)["r1"], "SUPERSEDED(query_pending)")
        self.assertEqual(report["funnel"]["n_accepted"], 2)
        # 等新帧：受理行 detail waiting_for_new_frame，期间无行。
        fx = self.fx("waiting")
        fx.accept("r1", intent=ap.RED_CAR, detail="waiting_for_new_frame")
        fx.accept("r2", intent=ap.RED_CAR)
        fx.submit()
        self.assertEqual(funnel_of(fx.score())["r1"], "SUPERSEDED(query_pending)")

    def test_designation_unavailable_interrupted(self) -> None:
        fx = self.fx()
        fx.process(3)
        fx.ask_presented("r1")
        fx.receipt("confirm", "c1")
        fx.j("designation_unavailable", reason="resident_loop_absent", frame_id=2)
        fx.stop()
        self.assertEqual(funnel_of(fx.score())["r1"], "INTERRUPTED(designation_unavailable, resident_loop_absent)")

    def test_retry_paths(self) -> None:
        fx = self.fx()
        # 首次 none、第 2 次给候选 → 不入 VLM_REPORTED。
        fx.accept("r-retry-ok", intent=ap.RED_CAR)
        q = fx.submit()
        fx.result(q, "none", request_id="r-retry-ok")
        q = fx.submit(attempt=2)
        fx.present(q)
        fx.receipt("reject", "rj")
        for rid, last, reason in (("r-none", "none", None), ("r-stale", "stale_rejected", "wall_deadline_exceeded"), ("r-parse", "parse_failed", None)):
            fx.accept(rid, intent=ap.RED_CAR)
            for attempt in (1, 2):
                q = fx.submit(attempt=attempt)
                fx.result(q, last, request_id=None, attempt=attempt, reject_reason=reason)
            q = fx.submit(attempt=3)
            fx.result(q, "retry_exhausted", attempt=3, last_status=last, last_reject_reason=reason)
        fx.accept("r-stuck", intent=ap.RED_CAR)
        q = fx.submit()
        fx.result(q, "backend_error", request_id="r-stuck", reject_reason="worker_stuck")
        fx.j("backend_fatal", reason="worker_stuck", detail=None)
        fx.terminal("backend_fatal")
        funnel = funnel_of(fx.score())
        self.assertEqual(funnel["r-retry-ok"], "OPERATOR_REJECTED")
        self.assertEqual(funnel["r-none"], "VLM_REPORTED(none)")
        self.assertEqual(funnel["r-stale"], "STALE_REJECTED(query, wall_deadline_exceeded)")
        self.assertEqual(funnel["r-parse"], "QUERY_FAILED(parse_failed)")
        self.assertEqual(funnel["r-stuck"], "QUERY_FAILED(backend_error)")

    def test_null_request_id_retry_and_confirm_request_id_stale_row_attributed(self) -> None:
        fx = self.fx()
        fx.process(3)
        fx.accept("r1", intent=ap.RED_CAR)
        q = fx.submit()
        fx.result(q, "stale_rejected", request_id="r1", reject_reason="frames_late_exceeded")
        q2 = fx.submit(attempt=2)  # `_resume_designate_retry` → request_id null
        fx.present(q2, request_id=None)
        fx.receipt("confirm", "c-late", detail="frames_late_exceeded", delay_injected_s=4.0)
        fx.result(q2, "stale_rejected", request_id="c-late", reject_reason="frames_late_exceeded", attempt=2)
        fx.stop()
        report = fx.score()
        self.assertEqual(funnel_of(report)["r1"], "STALE_REJECTED(confirm, frames_late_exceeded)")
        self.assertEqual(report["attribution_conflicts"], {})
        self.assertEqual(report["samples"][0]["delay_injected_s"], 4.0)

    def test_request_invalid_is_not_a_sample(self) -> None:
        fx = self.fx()
        fx.receipt("ask", "r-bad", "REQUEST_INVALID", "instruction_unsupported")
        fx.receipt("ask", "r-bad2", "REQUEST_INVALID", "missing_instruction")
        fx.stop()
        report = fx.score()
        self.assertEqual(report["funnel"]["n_accepted"], 0)
        self.assertEqual(report["command_invalid"]["ask:REQUEST_INVALID:instruction_unsupported"], 1)

    def test_unattributed_design_rows(self) -> None:
        fx = self.fx()
        fx.process(3)
        fx.j("designation", epoch=0, designation={"designation_id": 5, "frame_id_k": 0, "head_frame_id": 2, "result": "BOUND"}, candidate_index=0)
        fx.result("s-q99", "unique", epoch=77)
        fx.j("COASTING_TO_TRACK_ENDED", designation_id=42, track_id=1, frame_id=2, cause="removed")
        fx.stop()
        report = fx.score()
        self.assertEqual(report["unattributed_rows"].get("designation"), 1)
        self.assertEqual(report["unattributed_rows"].get("results:unique"), 1)
        self.assertEqual(report["unattributed_rows"].get("COASTING_TO_TRACK_ENDED"), 1)

    def test_duplicate_coasting_rows_counted_once(self) -> None:
        fx = self.fx()
        build_comprehensive(fx)
        report = fx.score()
        self.assertEqual(report["duplicate_event_rows_by_kind"].get("COASTING_TO_TRACK_ENDED"), 1)
        self.assertEqual(funnel_of(report)["r-coast"], "ACQUIRE_PATH(coasting_timeout)")


class ConflictTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _bound_pair(self, fx: Fx, rid: str) -> None:
        fx.ask_presented(rid)
        fx.confirm_designate("BOUND")
        fx.process(70, lambda f: RED_BOX)

    def _assert_conflict(self, report: dict[str, Any], code: str, rids: Iterable[str]) -> None:
        funnel = funnel_of(report)
        for rid in rids:
            self.assertTrue(funnel[rid].startswith("ATTRIBUTION_CONFLICT("), funnel[rid])
            self.assertIn(code, funnel[rid])
        # 冲突样本不进任何分母
        for number in ("number_one", "number_two", "number_three"):
            self.assertEqual(raw_total(report, number), 0, number)
        self.assertEqual(report["mislock"]["conservation"]["n_raw_total"], 0)
        for source in ap.TRUTH_SOURCES:
            self.assertEqual(table(report, "explicit_report", source)["ratio_explicit_over_explicit_plus_silent"]["denominator"], 0)
        self.assertGreaterEqual(report["attribution_conflicts"].get(code, 0), 1)

    def test_c1_duplicate_request_id(self) -> None:
        fx = Fx(self.root / "c1")
        fx.process(3)
        self._bound_pair(fx, "dup")
        self._bound_pair(fx, "dup")
        fx.stop()
        self._assert_conflict(fx.score(), "C1", ["dup"])

    def test_c2_same_epoch(self) -> None:
        fx = Fx(self.root / "c2")
        fx.process(3)
        self._bound_pair(fx, "a")
        fx.accept("b", intent=ap.RED_CAR, bump=False)
        fx.stop()
        self._assert_conflict(fx.score(), "C2", ["a", "b"])

    def test_c3_query_id_in_two_epochs(self) -> None:
        fx = Fx(self.root / "c3")
        fx.process(3)
        fx.ask_presented("a")
        fx.accept("b", intent=ap.RED_CAR)
        fx.result("s-q1", "none", epoch=fx.epoch)
        fx.stop()
        self._assert_conflict(fx.score(), "C3", ["a", "b"])

    def test_c4_foreign_request_id(self) -> None:
        fx = Fx(self.root / "c4")
        fx.process(3)
        fx.accept("a", intent=ap.RED_CAR)
        q = fx.submit()
        fx.result(q, "none", request_id="someone-else")
        fx.stop()
        self._assert_conflict(fx.score(), "C4", ["a"])

    def test_c5_two_terminal_rows(self) -> None:
        fx = Fx(self.root / "c5")
        fx.process(3)
        q = fx.ask_presented("a")
        fx.result("s-q50", "retry_exhausted", last_status="none", attempt=3)
        fx.stop()
        self._assert_conflict(fx.score(), "C5", ["a"])
        # 受理的 confirm 之后三者皆无，同为 C5。
        fx = Fx(self.root / "c5b")
        fx.process(3)
        fx.ask_presented("a")
        fx.receipt("confirm", "c1")
        fx.stop()
        self._assert_conflict(fx.score(), "C5", ["a"])
        del q

    def test_c6_designation_id_in_two_samples(self) -> None:
        fx = Fx(self.root / "c6")
        fx.process(3)
        fx.ask_presented("a")
        fx.confirm_designate("BOUND", did=3)
        fx.process(10, lambda f: RED_BOX)
        fx.ask_presented("b")
        fx.confirm_designate("BOUND", did=3)
        fx.process(10, lambda f: RED_BOX)
        fx.stop()
        self._assert_conflict(fx.score(), "C6", ["a", "b"])


class IntentAndNumberTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_no_intent_and_intent_unknown_in_funnel_not_in_denominators(self) -> None:
        fx = Fx(self.root / "intent")
        fx.process(3)
        for rid, intent in (("r-none", MISSING), ("r-unknown", "Vehicle_Missing (7)")):
            fx.ask_presented(rid, intent=intent)
            fx.confirm_designate("BOUND")
            fx.process(70, lambda f: STATIC_BOX)  # 对红车而言 OFF；若计入即会出现静默错误
        fx.stop()
        report = fx.score()
        funnel = funnel_of(report)
        self.assertEqual(funnel["r-none"], "BOUND_DIRECT(bound)")
        self.assertEqual(report["intent_status"], {"valid": 0, "no_intent": 1, "intent_unknown": 1})
        self.assertEqual(report["funnel_x_intent_status"]["BOUND_DIRECT"], {"valid": 0, "no_intent": 1, "intent_unknown": 1})
        one = table(report, "number_one", INVALID_SRC)
        self.assertEqual(one["counts"], {"NOT_EVALUABLE(intent_unknown)": 1, "NOT_EVALUABLE(no_intent)": 1})
        self.assertEqual(one["rates"]["overall"]["denominator"], 0)
        self.assertIn("ZERO_DENOMINATOR", one["rates"]["overall"]["flags"])
        for source in (RED_SRC, STATIC_SRC):
            self.assertEqual(table(report, "number_one", source)["n_raw"], 0)
        two = table(report, "number_two", INVALID_SRC)
        self.assertEqual(two["entry_gate"], {"NOT_EVALUABLE(intent_unknown)": 1, "NOT_EVALUABLE(no_intent)": 1})
        self.assertEqual(two["n_S"], 0)
        self.assertEqual(table(report, "number_three", INVALID_SRC)["rates"]["success"]["denominator"], 0)
        self.assertEqual(report["mislock"]["conservation"]["n_raw_total"], 0)
        explicit = table(report, "explicit_report", INVALID_SRC)
        self.assertEqual(explicit["ratio_explicit_over_explicit_plus_silent"]["denominator"], 0)
        self.assertEqual(explicit["set_aside"], {"intent:intent_unknown": 1, "intent:no_intent": 1})

    def test_silent_error_counted_once(self) -> None:
        fx = Fx(self.root / "silent")
        fx.process(3)
        fx.ask_presented("r-wrong")
        _did, track = fx.confirm_designate("BOUND")
        start = fx.next_frame
        fx.process(80, lambda f: STATIC_BOX)
        for frame_id in (start, start + 1, start + 2):
            for channel in ("observation", "body_command", "look_at"):
                fx.publish.append({"channel": channel, "outcome": "WRITTEN", "frame_id": frame_id, "track_id": track, "detail": {}})
        fx.publish.append({"channel": "observation", "outcome": "WRITTEN", "frame_id": start, "track_id": "other", "detail": {}})
        fx.publish.append({"channel": "body_safety_hold", "outcome": "WRITTEN", "frame_id": None, "track_id": None,
                           "detail": {"mode": "hold", "reason": "loop_start", "explicit": True}})
        fx.stop()
        report = fx.score()
        self.assertEqual(table(report, "number_one")["counts"], {"RESOLVED_WRONG": 1})
        self.assertEqual(table(report, "number_three")["counts"], {"WRONG_CAPTURE": 1})
        self.assertEqual(table(report, "explicit_report")["silent_error"], 1)
        self.assertEqual(table(report, "mislock")["mislock"], 1)
        duration = table(report, "mislock")["durations"][0]
        # [f_p, f_p + 13 s] 闭区间内 OFF 且已发布的帧：夹具时刻 0.2 f + 0.1 下 f_p+65 帧的时刻与
        # t0 + 13 的浮点比较按原判据（`t > 窗尾` 才出窗）照算，结果确定（不加容差）。
        f_p = next(s for s in report["samples"] if s["request_id"] == "r-wrong")["f_p"]
        t0 = 0.2 * f_p + 0.1
        expected = sum(1 for f in range(f_p, f_p + 80) if 0.2 * f + 0.1 <= t0 + 13.0)
        self.assertEqual(duration["off_published_frames"], expected)
        self.assertEqual(duration["duration_s"], duration["off_published_frames"] / 5.0)
        self.assertEqual(duration["written_receipts"], {"observation": 3, "body_command": 3})

    def test_rates_zero_denominator_and_insufficient_n(self) -> None:
        fx = Fx(self.root / "rates")
        fx.process(3)
        fx.ask_presented("r1")
        fx.confirm_designate("BOUND")
        fx.process(80, lambda f: RED_BOX)
        fx.stop()
        report = fx.score()
        captured = table(report, "number_three")["rates"]["success"]
        self.assertEqual((captured["numerator"], captured["denominator"], captured["value"]), (1, 1, 1.0))
        self.assertIn("INSUFFICIENT_N", captured["flags"])
        acq = report["explicit_report"]["acq_3_10_scope"]["explicit_over_designations"]
        self.assertEqual((acq["numerator"], acq["denominator"]), (0, 1))
        self.assertIn("INSUFFICIENT_N", acq["flags"])
        self.assertIn("INSUFFICIENT_N", table(report, "number_one")["by_delta_eff_bucket"]["[0,1)"]["flags"])
        empty = Fx(self.root / "empty")
        empty.stop()
        report = empty.score()
        for source in ap.TRUTH_SOURCES:
            for rate in (
                table(report, "number_one", source)["rates"]["overall"],
                table(report, "number_three", source)["rates"]["success"],
                table(report, "mislock", source)["mislock_rate"],
                table(report, "explicit_report", source)["ratio_explicit_over_explicit_plus_silent"],
            ):
                self.assertIsNone(rate["value"])
                self.assertIn("ZERO_DENOMINATOR", rate["flags"])
        self.assertNotIn("通过", json.dumps(report, ensure_ascii=False))

    def test_capture_timeout_and_acquire_failed(self) -> None:
        fx = Fx(self.root / "cap")
        fx.process(3)
        fx.ask_presented("r-late")
        fx.confirm_designate("BOUND")
        fx.process(60)
        fx.process(30, lambda f: RED_BOX)
        fx.ask_presented("r-fail")
        did, _ = fx.confirm_designate("TRACK_ENDED")
        fx.process(3)
        fx.j("acquire_failed", designation_id=did, cause="slew_timeout", candidates=[])
        fx.process(3)
        fx.stop()
        report = fx.score()
        self.assertEqual(table(report, "number_one")["counts"]["BOUND_NO_PUBLISH"], 1)
        self.assertEqual(table(report, "number_three")["counts"], {"ACQUIRE_FAILED(slew_timeout)": 1, "CAPTURE_TIMEOUT": 1})
        self.assertEqual(table(report, "explicit_report")["explicit"], 1)

    def test_no_pose_and_invisible_reported_separately(self) -> None:
        fx = Fx(self.root / "pose")
        fx.process(3)
        fx.ask_presented("r-nopose")
        fx.confirm_designate("BOUND")
        fx.truth_missing.add(fx.next_frame)
        fx.process(40, lambda f: RED_BOX)
        fx.ask_presented("r-invisible")
        fx.confirm_designate("BOUND")
        hidden = fx.next_frame
        fx.red_visible = lambda f: f != hidden
        fx.process(40, lambda f: RED_BOX)
        fx.stop()
        counts = table(fx.score(), "number_one")["counts"]
        self.assertEqual(counts["NOT_EVALUABLE(NO_POSE:no_truth)"], 1)
        self.assertEqual(counts["NOT_EVALUABLE(INVISIBLE:truth_box_unavailable)"], 1)


class SurvivalTests(unittest.TestCase):
    """§3.5.4 每条判定与「与 window_outcome 的差异」。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.n = 0

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_case(self, boxes: Callable[[int], Any], count: int, *, setup: Callable[[Fx, int], None] | None = None,
                 intent: Any = ap.RED_CAR) -> tuple[dict[str, Any], dict[str, Any]]:
        self.n += 1
        fx = Fx(self.root / f"s{self.n}")
        fx.process(3)
        fx.ask_presented("r1", intent=intent)
        fx.confirm_designate("BOUND")
        start = fx.next_frame
        if setup is not None:
            setup(fx, start)
        fx.process(count, lambda f: boxes(f - start))
        fx.stop()
        report = fx.score()
        return table(report, "number_two", RED_SRC if intent == ap.RED_CAR else STATIC_SRC)["windows"]["W_13s"], report

    def outcome(self, table: dict[str, Any]) -> str:
        (key,) = table["counts"].keys()
        return key

    def test_kept(self) -> None:
        table, _ = self.run_case(lambda i: RED_BOX, 80)
        self.assertEqual(self.outcome(table), "KEPT")
        self.assertEqual(table["survival_KEPT_over_D"]["value"], 1.0)

    def test_unbound_start_off(self) -> None:
        table, report = self.run_case(lambda i: STATIC_BOX if i == 0 else RED_BOX, 80)
        self.assertEqual(self.outcome(table), "UNBOUND_START")
        self.assertEqual(report["mislock"]["by_truth_source"][RED_SRC]["mislock"], 1)

    def test_censored_end(self) -> None:
        table, _ = self.run_case(lambda i: RED_BOX, 30)
        self.assertEqual(self.outcome(table), "CENSORED_END")

    def test_truth_gap_no_pose(self) -> None:
        table, _ = self.run_case(lambda i: RED_BOX, 80, setup=lambda fx, s: fx.truth_missing.add(s + 10))
        self.assertEqual(self.outcome(table), "TRUTH_GAP(no_pose)")

    def test_truth_gap_invisible(self) -> None:
        def setup(fx: Fx, s: int) -> None:
            fx.red_visible = lambda f: not (s + 5 <= f <= s + 36)

        table, _ = self.run_case(lambda i: RED_BOX, 80, setup=setup)
        self.assertEqual(self.outcome(table), "TRUTH_GAP(invisible)")

    def test_empty_window_excluded_not_raised(self) -> None:
        def setup(fx: Fx, s: int) -> None:
            fx.time_fn = lambda f: 0.2 * f + 0.1 + (9.0 if f > s + 2 else 0.0)

        table, _ = self.run_case(lambda i: RED_BOX, 80, setup=setup)
        self.assertEqual(self.outcome(table), "TRUTH_GAP(empty_window)")

    def test_id_switch(self) -> None:
        table, report = self.run_case(lambda i: STATIC_BOX if i == 20 else RED_BOX, 80)
        self.assertEqual(self.outcome(table), "ID_SWITCH")
        self.assertEqual(report["mislock"]["by_truth_source"][RED_SRC]["mislock"], 1)

    def test_lost_beyond_buffer(self) -> None:
        table, _ = self.run_case(lambda i: None if 5 <= i <= 40 else RED_BOX, 80)
        self.assertEqual(self.outcome(table), "LOST_BEYOND_BUFFER")

    def test_tail_extension_recovers_to_kept(self) -> None:
        # 漏检段跨窗口尾（W=13 s = 65 帧），窗口外以 ON 结束（段长 ≤ 30）→ KEPT。
        table, _ = self.run_case(lambda i: None if 55 <= i <= 75 else RED_BOX, 100)
        self.assertEqual(self.outcome(table), "KEPT")

    def test_tail_extension_lost_after_window(self) -> None:
        table, _ = self.run_case(lambda i: None if i >= 50 else RED_BOX, 100)
        self.assertEqual(self.outcome(table), "LOST_BEYOND_BUFFER")

    def test_tail_extension_unresolved_at_e(self) -> None:
        table, _ = self.run_case(lambda i: None if i >= 60 else RED_BOX, 75)
        self.assertEqual(self.outcome(table), "UNRESOLVED_END_MISS")

    def test_tail_no_pose_outside_window(self) -> None:
        table, _ = self.run_case(lambda i: None if i >= 60 else RED_BOX, 100, setup=lambda fx, s: fx.truth_missing.add(s + 70))
        self.assertEqual(self.outcome(table), "TRUTH_GAP(no_pose_ext)")

    def test_pointer_track_change_does_not_change_outcome(self) -> None:
        self.n += 1
        fx = Fx(self.root / "track")
        fx.process(3)
        fx.ask_presented("r1")
        did, track = fx.confirm_designate("BOUND", library=7)
        fx.process(20, lambda f: RED_BOX)
        fx.j("segment_retired", track_id=track, reason="operator_release", to_frame_id=fx.next_frame - 1)
        fx.j("acquire_adopted", designation_id=did, track_id=9, frame_id=fx.next_frame - 1)
        fx.bind(9, fx.next_frame - 1)
        fx.process(70, lambda f: RED_BOX)
        fx.stop()
        report = fx.score()
        window = table(report, "number_two")["windows"]["W_13s"]
        self.assertEqual(window["counts"], {"KEPT": 1})
        self.assertEqual(window["pointer_track_changed"], 1)

    def test_conservation_and_differences_listed(self) -> None:
        fx = Fx(self.root / "cons")
        build_comprehensive(fx)
        report = fx.score()
        number_two = report["number_two"]
        for source in ap.TRUTH_SOURCES:
            two = table(report, "number_two", source)
            gate_total = sum(two["entry_gate"].values()) + two["n_S"]
            self.assertEqual(gate_total, two["n_raw_bound_samples"])
            for window in two["windows"].values():
                d = window["survival_KEPT_over_D"]["denominator"]
                excluded = sum(v for k, v in window["counts"].items() if k in {"UNBOUND_START", "CENSORED_END"} or k.startswith("TRUTH_GAP"))
                self.assertEqual(window["n_S"], excluded + d)
        self.assertEqual(number_two["conservation"]["n_raw_total"], number_two["conservation"]["sum_by_truth_source"])
        self.assertEqual(len(number_two["differences_from_window_outcome"]), 5)


CENTER_BOX = [0.45, 0.45, 0.1, 0.1]  # 中心 (320, 240)


class ReworkC1AC8Tests(unittest.TestCase):
    """C1-AC8 (1)–(4) 与 PR-3/4/5 的回归（修前必失败）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def sample(self, report: dict[str, Any], rid: str) -> dict[str, Any]:
        return next(s for s in report["samples"] if s["request_id"] == rid)

    # (1) 时间轴唯一来源 = 真值行；段日志时刻不替代。

    def test_segment_time_never_substitutes_missing_truth_time(self) -> None:
        fx = Fx(self.root / "time")
        fx.process(3)
        fx.ask_presented("r1")
        fx.confirm_designate("BOUND")
        h = fx.next_frame - 1
        fx.truth_missing.add(h)  # h 帧无真值行（段日志仍有 simulation_time_s）
        fx.process(80, lambda f: RED_BOX)
        fx.stop()
        report = fx.score()
        record = self.sample(report, "r1")
        self.assertEqual(record["h"], h)
        self.assertIsNone(record["delta_eff_s"], "Δ_eff 不得用段日志时刻补算")
        self.assertIn("NO_POSE", table(report, "number_one")["by_delta_eff_bucket"])
        self.assertEqual(record["capture"]["outcome"], "CAPTURED")
        self.assertIsNone(record["capture"]["time_to_bind_s"], "time-to-bind 不得用段日志时刻补算")
        self.assertEqual(report["frame_time_source"]["frames_without_truth_time"], 1)
        self.assertEqual(report["frame_time_source"]["frames_without_truth_time_with_segment_time_diagnostic_only"], 1)
        self.assertIs(report["frame_time_source"]["segment_log_time_used_for_numbers"], False)
        self.assertNotIn("frame_time_fallback_to_segment_log", report)

    def test_end_frame_without_truth_time_is_not_censored_by_segment_time(self) -> None:
        fx = Fx(self.root / "end")
        fx.process(3)
        fx.ask_presented("r1")
        fx.confirm_designate("BOUND")
        fx.process(40, lambda f: RED_BOX)  # 不足 13 s；E = 最后一帧
        fx.truth_missing.add(fx.next_frame - 1)
        fx.stop()
        report = fx.score()
        # 旧实现以段日志时刻判 E → CENSORED_END；E 无真值时刻、其前无越过窗尾的已知帧 → 无法判定，按 NO_POSE 排除。
        self.assertEqual(self.sample(report, "r1")["survival"]["W_13s"], "TRUTH_GAP(no_pose)")
        self.assertEqual(table(report, "number_two")["windows"]["W_13s"]["counts"], {"TRUTH_GAP(no_pose)": 1})

    # (2) 指针 epoch 只取本样本自身（同 e_s、同常驻代）的 pointer_bound。

    def test_pointer_bound_is_not_borrowed_from_another_generation(self) -> None:
        fx = Fx(self.root / "borrow")
        fx.process(3)
        fx.ask_presented("r-a")
        fx.receipt("confirm", "c-a")
        h = fx.next_frame - 1
        fx.j("designation", designation={"designation_id": 1, "frame_id_k": h - 2, "head_frame_id": h, "result": "BOUND",
                                         "resolution_level": 1, "track_id": 7, "level1": {}, "level2": None, "candidates": []},
             candidate_index=0)  # 本样本没有自己的 pointer_bound
        fx.j("resident_loop_started", run_id="s-resident2")  # 同 epoch 内常驻重建：新一代
        fx.bind(9, fx.next_frame - 1)  # 新一代的指针（不属于 r-a）
        fx.process(80, lambda f: RED_BOX)
        fx.stop()
        report = fx.score()
        record = self.sample(report, "r-a")
        self.assertEqual(record["funnel"], "BOUND_DIRECT(bound)")
        self.assertEqual(record["pointer_epochs"], [])
        self.assertIsNone(record["f_p"])
        self.assertEqual(record["number_one"], "BOUND_NO_PUBLISH")
        self.assertEqual(report["unattributed_rows"].get("pointer_bound"), 1)

    def test_pointer_bound_after_other_sample_designation_is_not_borrowed(self) -> None:
        fx = Fx(self.root / "next")
        fx.process(3)
        fx.ask_presented("r-a")
        fx.receipt("confirm", "c-a")
        h = fx.next_frame - 1
        fx.j("designation", designation={"designation_id": 1, "frame_id_k": h - 2, "head_frame_id": h, "result": "BOUND",
                                         "resolution_level": 1, "track_id": 7, "level1": {}, "level2": None, "candidates": []},
             candidate_index=0)
        fx.process(5)
        fx.ask_presented("r-b")
        _did, track_b = fx.confirm_designate("BOUND", library=8, did=2)
        fx.process(80, lambda f: RED_BOX)
        fx.stop()
        report = fx.score()
        self.assertEqual(self.sample(report, "r-a")["pointer_epochs"], [])
        self.assertEqual([e["track_id"] for e in self.sample(report, "r-b")["pointer_epochs"]], [track_b])
        self.assertEqual(report["unattributed_rows"].get("pointer_bound"), None)

    def test_two_generations_reuse_designation_id_each_keep_own_pointer(self) -> None:
        fx = Fx(self.root / "gens")
        fx.process(3)
        fx.ask_presented("r-a")
        _did, track_a = fx.confirm_designate("BOUND", library=7, did=1)
        fx.process(20, lambda f: RED_BOX)
        fx.j("resident_loop_started", run_id="s-resident2")
        fx.ask_presented("r-b")
        _did, track_b = fx.confirm_designate("BOUND", library=7, did=1)
        fx.process(80, lambda f: RED_BOX)
        fx.stop()
        report = fx.score()
        self.assertEqual(report["attribution_conflicts"], {})
        self.assertEqual([e["track_id"] for e in self.sample(report, "r-a")["pointer_epochs"]], [track_a])
        self.assertEqual([e["track_id"] for e in self.sample(report, "r-b")["pointer_epochs"]], [track_b])
        self.assertEqual(report["pointer_bound_claim_conflicts"], 0)

    # (3) time-to-center 实际输出时长与三种结局。

    def test_time_to_center_durations_are_output(self) -> None:
        fx = Fx(self.root / "center")
        fx.time_fn = lambda f: 0.25 * f  # 二进制可精确表示：时长断言不受浮点影响
        fx.process(3)
        fx.ask_presented("r1")
        fx.confirm_designate("BOUND")
        h = fx.next_frame - 1
        start = fx.next_frame
        fx.red_box = lambda f: CENTER_BOX if f >= start + 3 else RED_BOX
        fx.process(80, lambda f: CENTER_BOX if f >= start + 3 else RED_BOX)
        fx.stop()
        report = fx.score()
        capture = self.sample(report, "r1")["capture"]
        self.assertEqual(capture["outcome"], "CAPTURED")
        self.assertEqual(capture["center"], "CENTERED")
        self.assertEqual(capture["center_run_start_frame"], start + 3)
        self.assertEqual(capture["time_to_center_from_f_p_s"], 0.75)
        self.assertEqual(capture["time_to_center_from_h_s"], 0.25 * (start + 3 - h))
        center = table(report, "number_three")["time_to_center"]
        self.assertEqual(center["outcomes"], {"CENTERED": 1, "CENTER_NOT_REACHED": 0, "CENTER_CENSORED": 0})
        self.assertEqual(center["time_to_center_from_f_p_s"]["values"], [0.75])
        self.assertEqual(center["time_to_center_from_f_p_s"]["median"], 0.75)
        self.assertEqual(center["time_to_center_from_h_s"]["values"], [0.25 * (start + 3 - h)])
        self.assertEqual(table(report, "number_three")["time_to_bind_s"]["values"], [capture["time_to_bind_s"]])

    def test_time_to_center_not_reached_and_censored(self) -> None:
        cases = {"not_reached": (80, "CENTER_NOT_REACHED"), "censored": (30, "CENTER_CENSORED")}
        for name, (count, expected) in cases.items():
            with self.subTest(case=name):
                fx = Fx(self.root / name)
                fx.process(3)
                fx.ask_presented("r1")
                fx.confirm_designate("BOUND")
                fx.process(count, lambda f: RED_BOX)  # 红车框在画面右上，不居中
                fx.stop()
                report = fx.score()
                capture = self.sample(report, "r1")["capture"]
                self.assertEqual((capture["outcome"], capture["center"]), ("CAPTURED", expected))
                self.assertIsNone(capture["time_to_center_from_f_p_s"])
                self.assertEqual(table(report, "number_three")["time_to_center"]["outcomes"][expected], 1)

    def test_center_window_closed_endpoint_is_deterministic(self) -> None:
        # PR-5：13 s 闭端点——居中连续段恰在 f_p + 13 s 那帧完成仍计 CENTERED；再晚一帧即 NOT_REACHED。
        for offset, expected in ((48, "CENTERED"), (49, "CENTER_NOT_REACHED")):
            with self.subTest(run_start_offset=offset):
                fx = Fx(self.root / f"edge{offset}")
                fx.time_fn = lambda f: 0.25 * f
                fx.process(3)
                fx.ask_presented("r1")
                fx.confirm_designate("BOUND")
                start = fx.next_frame
                fx.red_box = lambda f, s=start, o=offset: CENTER_BOX if f >= s + o else RED_BOX
                fx.process(80, lambda f, s=start, o=offset: CENTER_BOX if f >= s + o else RED_BOX)
                fx.stop()
                capture = self.sample(fx.score(), "r1")["capture"]
                # f_p = start；5 帧连续段末帧 = start + offset + 4；13 s = 52 帧。
                self.assertEqual(capture["center"], expected)

    # (4) 红车 Unity 真值与静止车几何近似分列，不出合并表。

    def test_red_car_and_static_numbers_are_reported_separately(self) -> None:
        fx = Fx(self.root / "split")
        build_comprehensive(fx)
        report = fx.score()
        for number in ("number_one", "number_two", "number_three", "mislock"):
            block = report[number]
            self.assertEqual(set(block["by_truth_source"]), set(ap.TRUTH_SOURCES), number)
            for merged in ("counts", "rates", "n_raw", "entry_gate", "n_S", "windows", "mislock_rate"):
                self.assertNotIn(merged, block, f"{number} 不得出合并表 {merged}")
            conservation = block["conservation"]
            self.assertEqual(conservation["n_raw_total"], conservation["sum_by_truth_source"])
        self.assertNotIn("funnel_scope", report["explicit_report"])
        one_red = table(report, "number_one", RED_SRC)["counts"]
        one_static = table(report, "number_one", STATIC_SRC)["counts"]
        self.assertEqual(table(report, "number_one", STATIC_SRC)["n_raw"], 1)  # r-respecify
        self.assertEqual(one_static, {"RESOLVED_CORRECT": 1})
        self.assertEqual(one_red.get("RESOLVED_WRONG"), 1)  # r-wrong（红车意图）只在红车表
        self.assertNotIn("RESOLVED_WRONG", one_static)
        self.assertEqual(
            sum(table(report, "number_one", s)["n_raw"] for s in ap.TRUTH_SOURCES),
            report["number_one"]["conservation"]["n_raw_total"],
        )
        by_source = report["truth_sources"]["samples_by_source"]
        self.assertEqual(sum(by_source.values()), report["funnel"]["n_accepted"])
        self.assertEqual({s["request_id"]: s["truth_source"] for s in report["samples"]}["r-respecify"], STATIC_SRC)

    # PR-3 / AC-8 修订 2：确认后追平途中终止（stop 先增 epoch）仍归原 e_s。

    def test_designation_unavailable_after_terminal_epoch_bump_keeps_sample(self) -> None:
        fx = Fx(self.root / "unavail")
        fx.process(3)
        fx.ask_presented("r1")
        fx.receipt("confirm", "c1")
        fx.epoch += 1  # stop()：先增 epoch
        fx.j("state", state="TERMINAL", reason="duration_reached")
        fx.j("designation_unavailable", state="TERMINAL", reason="session_terminal", frame_id=fx.next_frame - 1)
        report = fx.score()
        self.assertEqual(funnel_of(report)["r1"], "INTERRUPTED(designation_unavailable, session_terminal)")
        self.assertEqual(report["attribution_conflicts"], {})
        self.assertEqual(report["unattributed_rows"], {})
        self.assertEqual(report["designation_unavailable_reattributed_to_confirm_epoch"], 1)


class LayoutAndIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def static_fixture(self, name: str, mutate: Callable[[Fx], None] | None = None) -> Fx:
        fx = Fx(self.root / name)
        fx.process(3)
        fx.ask_presented("r1", intent=STATIC)
        fx.confirm_designate("BOUND")
        if mutate is not None:
            mutate(fx)
        fx.process(80, lambda f: STATIC_BOX)
        fx.stop()
        return fx

    def test_layout_bound_does_not_call_apply_layout(self) -> None:
        fx = self.static_fixture("bound")
        with mock.patch.object(bind_layout, "apply_layout", side_effect=AssertionError("apply_layout called")) as spy, \
                mock.patch.object(bind_layout, "unadjusted_base", side_effect=AssertionError("unadjusted_base called")) as inverse:
            report = fx.score()
        spy.assert_not_called()
        inverse.assert_not_called()
        self.assertEqual(report["layout_binding"]["status"], "BOUND")
        self.assertEqual(table(report, "number_one", STATIC_SRC)["counts"], {"RESOLVED_CORRECT": 1})

    def test_layout_copy_missing_unbound(self) -> None:
        fx = self.static_fixture("missing", lambda fx: setattr(fx, "copy_doc", None))
        report = fx.score()
        self.assertEqual(report["layout_binding"]["status"], "layout_unbound")
        self.assertEqual(table(report, "number_one", STATIC_SRC)["counts"], {"NOT_EVALUABLE(layout_unbound)": 1})

    def test_layout_sha_mismatch_unbound(self) -> None:
        fx = self.static_fixture("sha", lambda fx: setattr(fx, "manifest_sha_override", "0" * 64))
        report = fx.score()
        self.assertEqual((report["layout_binding"]["status"], report["layout_binding"]["detail"]), ("layout_unbound", "scenario_copy_sha_mismatch"))

    def test_layout_scene_adjustments_mismatch(self) -> None:
        def mutate(fx: Fx) -> None:
            fx.copy_doc = {"scenario_id": fx.copy_scenario_id, "scene_adjustments": {"vehicle_relocations": []}}

        with mock.patch.object(bind_layout, "apply_layout") as spy:
            report = self.static_fixture("adj", mutate).score()
        spy.assert_not_called()
        self.assertEqual(report["layout_binding"]["status"], "layout_mismatch")
        self.assertEqual(table(report, "number_three", STATIC_SRC)["counts"], {"NOT_EVALUABLE(layout_mismatch)": 1})

    def _tamper_case(self, name: str, tamper: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
        def mutate(fx: Fx) -> None:
            fx.tamper[fx.next_frame] = tamper  # f_p 帧

        return self.static_fixture(name, mutate).score()

    def test_h2_tamper_basis_vectors(self) -> None:
        def tamper(doc: dict[str, Any]) -> None:
            doc["camera_right_world"] = [0.99995, 0.0, 0.01]

        report = self._tamper_case("basis", tamper)
        self.assertEqual(report["frame_identity_mismatch"]["frames"], 1)
        self.assertEqual(report["frame_identity_mismatch"]["by_check"], {"1_metadata_sha256": 1})
        self.assertEqual(table(report, "number_one", STATIC_SRC)["counts"], {"NOT_EVALUABLE(NO_POSE:frame_identity_mismatch)": 1})

    def test_h2_tamper_intrinsics(self) -> None:
        def tamper(doc: dict[str, Any]) -> None:
            doc["intrinsics_px"]["fx"] = FOCAL + 0.3

        report = self._tamper_case("intr", tamper)
        self.assertEqual(report["frame_identity_mismatch"]["by_check"], {"1_metadata_sha256": 1})

    def test_h2_tamper_position_within_tolerance(self) -> None:
        def tamper(doc: dict[str, Any]) -> None:
            doc["camera_position_world_m"] = [0.0005, 25.0, 0.0]

        report = self._tamper_case("pos", tamper)
        self.assertEqual(report["frame_identity_mismatch"]["by_check"], {"1_metadata_sha256": 1})

    def test_h2_runtime_digest_null_is_metadata_unbound(self) -> None:
        def mutate(fx: Fx) -> None:
            fx.digest_null.add(fx.next_frame)

        report = self.static_fixture("null", mutate).score()
        self.assertEqual(report["frame_identity_mismatch"]["frames"], 0)
        self.assertEqual(table(report, "number_one", STATIC_SRC)["counts"], {"NOT_EVALUABLE(NO_POSE:metadata_unbound)": 1})

    def test_h2_result_frame_sha_against_session_ring(self) -> None:
        fx = Fx(self.root / "jpeg")
        fx.process(3)
        fx.session_jpegs = {1: b"jpeg-1", 2: b"jpeg-2"}
        fx.accept("r1", intent=ap.RED_CAR)
        fx.result("s-q1", "none", frame_id=1, frame_sha256=_sha(b"jpeg-1"))
        fx.result("s-q2", "retry_exhausted", last_status="none", frame_id=2, frame_sha256=_sha(b"other"))
        fx.stop()
        report = fx.score()
        self.assertEqual(report["result_frame_sha256_checks"], {"match": 1, "mismatch": 1})
        self.assertEqual(report["frame_identity_mismatch"]["result_frame_sha256_mismatch"], 1)

    def test_red_car_blocker_depth(self) -> None:
        fx = Fx(self.root / "blocker")
        fx.process(3)
        fx.ask_presented("r1", intent=STATIC)
        fx.confirm_designate("BOUND")
        hidden = fx.next_frame + 1
        fx.red_visible = lambda f: f != hidden
        fx.process(80, lambda f: STATIC_BOX)
        fx.stop()
        scorer = fx.scorer()
        calls = dict(scorer.blocker_calls)
        camera = project_boxes.Camera.from_sidecar(base_sidecar(0, 0.0, "x"))
        expected_depth = camera.to_camera_space(RED_TARGET)[2]
        first = calls[hidden - 1]
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0][0], "red_car")
        self.assertAlmostEqual(first[0][2], expected_depth)
        self.assertEqual(first[0][1], project_boxes.denormalize_xywh(RED_BOX, camera))
        self.assertEqual(calls[hidden], [])

    def test_score_cli_rejects_runtime_inputs(self) -> None:
        with self.assertRaises(ap.AnalyzeError):
            ap.main(["score", "--session-dir", str(REPO_ROOT / "runtime" / "x"), "--unity-dir", str(self.root)])


class DeriveBCTests(unittest.TestCase):
    def test_derive_bc_lt_2_status(self) -> None:
        scenario = {
            "anchor_world_m": {"x": 0.0, "y": 0.0, "z": 0.0},
            "drone": {"initial_altitude_m": 25.0},
            "gimbal": {"maximum_off_nadir_deg": 45.0},
            "sensor": {"width": 640, "height": 480, "vertical_fov_deg": 60.0},
        }
        geometry = {"instances": [dict(i, min_x_m=i["min_x_m"] + 3.0, max_x_m=i["max_x_m"] + 3.0) for i in mini_instances()]}
        result = ap.derive_bc(scenario, geometry)
        self.assertEqual(result["status"], "BC_DERIVATION_LT_2")
        self.assertEqual([row["scene_object_name"] for row in result["pool"]], [STATIC])
        self.assertEqual(result["B"]["description"], "the test suv")
        self.assertIsNone(result["C"])


class ArchiveDryrunSmokeTests(unittest.TestCase):
    """`archive-dryrun` 代码路径在合成归档上可运行（真实归档只在子命令运行时读取）。"""

    def test_dryrun_runs_on_synthetic_archives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fx = Fx(root / "a2")
            fx.process(3)
            fx.ask_presented("r1")
            fx.confirm_designate("BOUND")
            fx.process(10, lambda f: RED_BOX)
            fx.stop()
            fx.copy_doc = None
            fx.write()
            for frame_id in range(fx.next_frame):
                (fx.unity / "frames" / f"frame_{frame_id:010d}.jpg").write_bytes(b"j")
            (fx.session / "frames" / "frame_0000000000.jpg").write_bytes(b"j")
            f1 = root / "f1"
            (f1 / "retained_frame_metadata").mkdir(parents=True)
            (f1 / "retained_frame_images").mkdir()
            for frame_id in range(3):
                (f1 / "retained_frame_metadata" / f"frame_{frame_id:010d}.json").write_bytes(fx.sidecar_bytes(frame_id))
                (f1 / "retained_frame_images" / f"frame_{frame_id:010d}.jpg").write_bytes(b"j")
            (f1 / "frames.jsonl").write_text((fx.unity / "runs" / "s-resident1" / "frames.jsonl").read_text())
            (f1 / "m3_body_truth.jsonl").write_text((fx.unity / "m3_body_truth.jsonl").read_text())
            (f1 / "manifest.json").write_text(json.dumps({"body_planner": {"effective_scenario_sha256": "x"}}))
            scenario = {
                "anchor_world_m": {"x": 3.0, "y": 0.0, "z": 0.0},
                "drone": {"initial_altitude_m": 25.0},
                "gimbal": {"maximum_off_nadir_deg": 45.0},
                "sensor": {"width": 640, "height": 480, "vertical_fov_deg": 60.0},
            }
            untethered = root / "untethered.json"
            untethered.write_text(json.dumps(scenario))
            paths = fx.write()
            document = ap.archive_dryrun(fx.session, fx.unity, f1, reference_scenario=paths.reference_scenario,
                                         untethered_scenario=untethered, geometry=fx.geometry())
        self.assertEqual(document["schema"], ap.DRYRUN_SCHEMA)
        self.assertTrue(all(item["verdict"] in {"一致", "不一致"} for item in document["comparison"]))
        self.assertEqual(document["attempt2"]["score_summary"]["layout_binding"]["status"], "layout_unbound")
        self.assertEqual(document["attempt2"]["score_summary"]["intent_status"]["valid"], 1)
        self.assertIn("frame001_play2", document)


def write_fixture_evidence(out: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fx = Fx(Path(tmp) / "fixture")
        build_comprehensive(fx)
        report = fx.score()
    report.pop("inputs", None)
    document = {
        "provenance": {
            "command": f".venv-yoloe/bin/python tests/test_eng_loop2_analyze.py --write-evidence {out}",
            "generated_at_utc": ap._now(),
            "git_head_at_run": ap._git_head(),
            "fixture": "tests/test_eng_loop2_analyze.py::build_comprehensive（合成夹具，迷你几何；非真实归档）",
        },
        **report,
    }
    Path(out).write_text(json.dumps(document, ensure_ascii=False, indent=1, default=ap._json_default) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--write-evidence":
        write_fixture_evidence(Path(sys.argv[2]))
    else:
        unittest.main()
