"""P1-ENG-LOOP-001 AC-2…AC-7 / AC-12 / AC-16 / AC-17：会话状态机与 K1 时间语义。

无 GPU、无 torch、无 cv2：帧由 `FixtureFramePublisher` 产出、图像解码注入成「读字节」、
跟踪器用冻结闭集里的 `scripted` 替身、推理用 `ScriptedAdapter`，全部写临时目录。
时钟是可控的假时钟，所以 `T_ret` / `T_conf` / `T_pub` / `T_stall` / `T_hard` 都能精确触发。
"""

import json
import math
from pathlib import Path
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from controller import language_bridge as bridge
from controller.gated_publisher import sha256_bytes
from controller.language_loop import (
    ATTEMPT_LIMIT,
    PreviewUnavailable,
    QueryOutcome,
    CONSECUTIVE_ALERT,
    K_PUB,
    T_CONF_S,
    T_HARD_S,
    T_STALL_S,
    T_V_S,
    ConfigMismatch,
    FixtureFramePublisher,
    KReceipt,
    LanguageSession,
    QueryJob,
    SessionConfig,
    build_k_receipt,
    decide_host,
    host_tier,
    inline_spawn,
    k_conf_of,
    k_ret_of,
    qualifies,
    resolves_to_shared_runtime,
    send_request,
)
from controller.language_selector import RawSelection, ScriptedAdapter, SelectorError
from controller.trackers import ScriptedTracker, TrackerResult

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BODY_PLANNER_CONFIG = PROJECT_ROOT / "config" / "p1-m3-body-001.json"
BODY_SCENARIO_CONFIG = PROJECT_ROOT / "config" / "scenario.default.json"

UNIQUE = '{"status": "unique", "bbox_2d": [300, 300, 500, 500]}'
UNIQUE_FAR = '{"status": "unique", "bbox_2d": [10, 10, 80, 80]}'
AMBIGUOUS = (
    '{"status": "ambiguous", "candidates": [{"bbox_2d": [300, 300, 500, 500]}, '
    '{"bbox_2d": [600, 600, 800, 800]}]}'
)
NONE = '{"status": "none"}'
BROKEN = "definitely not json"

TRACKER_BOX = (0.3, 0.3, 0.2, 0.2)
TRACKER_BOX_FAR = (0.75, 0.05, 0.1, 0.1)

#: 预览渲染的三种颜色（`render_preview` 逐字使用）。
BACKDROP = (20, 20, 20)
CANDIDATE_RED = (255, 0, 0)
TRACKER_GREEN = (0, 255, 0)


def raw(text: str, finish_reason: str = "stop") -> RawSelection:
    return RawSelection(
        raw_output=text,
        finish_reason=finish_reason,
        gen_tokens=30,
        latency_ms=800.0,
        prompt_sha256="p" * 64,
        model_id="m" * 64,
    )


class FakeClock:
    def __init__(self, start_unix_s: float = 1_800_000_000.0):
        self.unix_s = float(start_unix_s)
        self.monotonic_s = 500.0

    def advance(self, seconds: float) -> None:
        self.unix_s += float(seconds)
        self.monotonic_s += float(seconds)

    def unix(self) -> float:
        return self.unix_s

    def monotonic(self) -> float:
        return self.monotonic_s


class StubPreview:
    """无 Pillow 的桩渲染器：写一个占位 PNG，并记录候选 index 以供断言。"""

    def __init__(self) -> None:
        #: (源帧, 预览路径, 候选 index, 是否带配对跟踪框)
        self.calls: list[tuple[Path, Path, list[int], bool]] = []

    def __call__(self, source, destination, candidates, tracker_box=None):
        destination.parent.mkdir(parents=True, exist_ok=True)
        indices = [candidate.index for candidate in candidates]
        destination.write_bytes(b"\x89PNG\r\n\x1a\n")
        destination.with_suffix(".json").write_text(
            json.dumps(
                {
                    "source": str(source),
                    "indices": indices,
                    "tracker_box": list(tracker_box or []),
                }
            ),
            encoding="utf-8",
        )
        self.calls.append(
            (Path(source), Path(destination), indices, tracker_box is not None)
        )
        return destination


class Harness:
    """一套会话 + 夹具帧发布器 + 假时钟，测试通过它驱动一切。"""

    def __init__(
        self,
        case: unittest.TestCase,
        *,
        responses,
        tracker_results=None,
        attempt_limit: int = ATTEMPT_LIMIT,
        verify_interval_s: float = T_V_S,
        p95_s: float = 2.0,
        diagnostic: bool = False,
        session_id: str = "s1",
        run_root: Path | None = None,
        t_hard_s: float = T_HARD_S,
        worker_spawn=inline_spawn,
        preview=None,
        body: bool = False,
        resident_tracker=None,
        acquire=None,
        adapter=None,
        receipt=None,
        setup_runtime=None,
        **config_overrides,
    ):
        self.case = case
        directory = tempfile.TemporaryDirectory()
        case.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir(parents=True, exist_ok=True)
        if setup_runtime is not None:
            # P1-ENG-LOOP-002：会话建立前在隔离 runtime 里放覆盖文件等（不碰仓库 runtime/）。
            setup_runtime(self.runtime)
        self.clock = FakeClock()
        self.publisher = FixtureFramePublisher(self.runtime, unix=self.clock.unix)
        self.adapter = adapter if adapter is not None else ScriptedAdapter(responses)
        self.preview = preview if preview is not None else StubPreview()
        self._tracker_plans = list(tracker_results or [])
        self.receipt = receipt if receipt is not None else build_k_receipt(
            hz=5.0,
            retained_frame_count=128,
            p95_s=p95_s,
            host="test",
            backend="replay",
            model_form="c2-adapter",
            model_identity=dict(self.adapter.identity),
            scenario_id="deterministic-loop-default",
        )
        config_kwargs = dict(
            session_id=session_id,
            session_root=self.root / "sessions",
            runtime=self.runtime,
            receipt=self.receipt,
            adapter=self.adapter,
            tracker_name="scripted" if resident_tracker is None else "fake-resident",
            tracker_factory=self._tracker if resident_tracker is None else (lambda: resident_tracker),
            resident=resident_tracker is not None,
            **({"acquire": acquire} if acquire is not None else {}),
            attempt_limit=attempt_limit,
            verify_interval_s=verify_interval_s,
            decode=lambda path: path.read_bytes(),
            preview=self.preview,
            worker_spawn=worker_spawn,
            monotonic=self.clock.monotonic,
            unix=self.clock.unix,
            planned_duration_s=100_000.0,
            diagnostic=diagnostic,
            run_root=run_root,
            t_hard_s=t_hard_s,
            pid=4242,
            is_alive=lambda pid: True,
            # R-B8：接冻结阈值规划器时，地面高度必须与冻结场景路线一致（0.2 m）。
            ground_plane_y_m=0.2 if body else 0.0,
            body_planner_config=BODY_PLANNER_CONFIG if body else None,
            body_scenario_config=BODY_SCENARIO_CONFIG if body else None,
        )
        config_kwargs.update(config_overrides)
        self.session = LanguageSession(SessionConfig(**config_kwargs))
        self.session.start()
        case.addCleanup(self.session.close)
        self._request_sequence = 0

    def _tracker(self):
        plan = self._tracker_plans.pop(0) if self._tracker_plans else []
        return ScriptedTracker(list(plan))

    # -- 驱动 --

    def publish(self, count: int = 1, *, tick: bool = True, payload: bytes | None = None) -> int:
        frame_id = -1
        for index in range(count):
            frame_id = self.publisher.publish(payload or f"jpeg-{index}-{self.publisher.next_frame_id}".encode())
            if tick:
                self.tick()
        return frame_id

    def tick(self, count: int = 1, advance_s: float = 0.05) -> None:
        for _ in range(count):
            self.clock.advance(advance_s)
            self.session.tick()

    def request(self, action: str, ticks: int = 2, **kwargs) -> dict:
        """写一条请求并驱动 `ticks` 次；`ticks=1` 只消费请求、不轮询回包。"""
        self._request_sequence += 1
        request_id = kwargs.pop("request_id", f"req{self._request_sequence}")
        holder = bridge.acquire_writer_lock(
            self.runtime, request_id=request_id, pid=4243, now=self.clock.unix()
        )
        bridge.write_request(
            self.runtime,
            session_id=kwargs.pop("session_id", self.session.session_id),
            request_id=request_id,
            action=action,
            **kwargs,
        )
        self.tick(ticks)
        bridge.release_writer_lock(self.runtime, request_id=request_id, pid=4243)
        return self.session.last_request or {}

    def ask(self, surface: str = "the red car", ticks: int = 2) -> dict:
        return self.request(
            "ask", ticks=ticks, instruction=bridge.parse_instruction(surface)
        )

    def confirm(self, index: int = 0) -> dict:
        return self.request(
            "confirm", candidate_index=index, token=self.session.candidate_result_id
        )

    # -- 读取 --

    def results(self) -> list[dict]:
        if not self.session.results_path.is_file():
            return []
        return [
            json.loads(line)
            for line in self.session.results_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def receipts(self) -> list[dict]:
        if not self.session.receipts_path.is_file():
            return []
        return [
            json.loads(line)
            for line in self.session.receipts_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def journal(self) -> list[dict]:
        return [
            json.loads(line)
            for line in self.session.journal_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def bridge_files(self) -> dict[str, bytes | None]:
        """三个对外桥文件的**内容**快照：存在性布尔挡不住「原地改写」。"""
        snapshot: dict[str, bytes | None] = {}
        for name in (
            "tracking_observation.json",
            "gimbal_command.json",
            "body_command.json",
        ):
            path = self.runtime / name
            snapshot[name] = path.read_bytes() if path.is_file() else None
        return snapshot

    def assert_no_bridge_writes(self) -> None:
        self.case.assertEqual(
            self.bridge_files(),
            {
                "tracking_observation.json": None,
                "gimbal_command.json": None,
                "body_command.json": None,
            },
        )
        self.case.assertEqual(self.receipts(), [])

    def frame_paths(self, frame_id: int) -> tuple[Path, Path]:
        stem = f"frame_{frame_id:010d}"
        return (
            self.runtime / "frames" / f"{stem}.jpg",
            self.runtime / "frames" / f"{stem}.json",
        )

    def seed(self, surface: str = "the red car", index: int = 0) -> None:
        """走一遍「发布 → ask → unique → confirm」，落到 TRACKING。"""
        self.publish(1)
        self.ask(surface)
        self.tick(2)
        self.case.assertEqual(self.session.state, "AWAITING_CONFIRMATION")
        self.confirm(index)
        self.tick(1)
        self.case.assertEqual(self.session.state, "TRACKING")


def tracking(box=TRACKER_BOX, count: int = 40) -> list[TrackerResult]:
    return [TrackerResult(box, True, 1.0, "placeholder")] * count


# --- AC-10：K 收据、资格与宿主决策 ----------------------------------------


class HostDecisionTests(unittest.TestCase):
    def test_frozen_constants(self) -> None:
        self.assertEqual((T_CONF_S, K_PUB, T_STALL_S, T_HARD_S, T_V_S), (10.0, 2, 3.0, 60.0, 10.0))
        self.assertEqual((ATTEMPT_LIMIT, CONSECUTIVE_ALERT), (3, 2))

    def test_k_ret_and_k_conf(self) -> None:
        self.assertEqual(k_ret_of(2.0, 5.0), 12)
        self.assertEqual(k_ret_of(1.73, 5.0), 11)
        self.assertEqual(k_conf_of(5.0), 50)

    def test_qualification_formula(self) -> None:
        # R − 12 − K_conf = 128 − 12 − 50 = 66 帧 → 13.2 s。
        self.assertTrue(qualifies(13.2, 5.0, 128))
        self.assertFalse(qualifies(13.4, 5.0, 128))

    def test_tiers(self) -> None:
        self.assertEqual(host_tier(1.5, 5.0, 128), "A")
        self.assertEqual(host_tier(6.0, 5.0, 128), "A")
        self.assertEqual(host_tier(6.1, 5.0, 128), "B")
        self.assertEqual(host_tier(40.0, 5.0, 128), "C")
        self.assertEqual(host_tier(None, 5.0, 128), "FAIL")

    def test_decision_table(self) -> None:
        self.assertEqual(decide_host("A", 1.0, "C", None)[0], "mac")
        self.assertEqual(decide_host("B", 7.0, "A", 1.0)[0], "5060")
        self.assertEqual(decide_host("B", 7.0, "B", 7.0)[0], "mac")  # 平局取 Mac
        self.assertEqual(decide_host("B", 8.0, "B", 7.0)[0], "5060")
        self.assertEqual(decide_host("B", 7.0, "C", None)[0], "mac")
        self.assertEqual(decide_host("FAIL", None, "B", 7.0)[0], "5060")
        self.assertEqual(decide_host("C", None, "FAIL", None)[0], "HOST_UNDECIDED")
        self.assertEqual(decide_host("FAIL", None, "FAIL", None)[0], "HOST_UNDECIDED")

    def test_receipt_rejects_inconsistent_constants(self) -> None:
        receipt = build_k_receipt(
            hz=5.0, retained_frame_count=128, p95_s=2.0, host="mac",
            backend="local-hf", model_form="c2-merged",
        )
        document = receipt.payload()
        document["k_ret"] = 99
        with self.assertRaises(ConfigMismatch):
            KReceipt.from_document(document)
        document = receipt.payload()
        document["backend"] = "carrier-pigeon"
        with self.assertRaises(ConfigMismatch):
            KReceipt.from_document(document)

    def test_session_refuses_a_receipt_bound_to_other_hz(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        runtime = root / "runtime"
        runtime.mkdir()
        (runtime / "scenario_config.json").write_text(
            json.dumps(
                {
                    "schema_version": "tethered-scenario/v1",
                    "scenario_id": "deterministic-loop-default",
                    "sensor": {"capture_hz": 20.0, "retained_frame_count": 128},
                }
            ),
            encoding="utf-8",
        )
        receipt = build_k_receipt(
            hz=5.0, retained_frame_count=128, p95_s=2.0, host="mac",
            backend="replay", model_form="c2-adapter",
        )
        with self.assertRaises(ConfigMismatch):
            LanguageSession(
                SessionConfig(
                    session_id="s1",
                    session_root=root / "sessions",
                    runtime=runtime,
                    receipt=receipt,
                    adapter=ScriptedAdapter([]),
                )
            )


# --- AC-17：八态 × 九动作全表 ---------------------------------------------


class StateTableTests(unittest.TestCase):
    """逐格覆盖 §3.4 的表；未列组合一律 `REQUEST_INVALID` 且状态不变。"""

    ACTIONS = bridge.ACTIONS

    ALLOWED = {
        "IDLE": {"ask", "respecify", "stop"},
        "QUERYING": {"ask", "respecify", "stop"},
        "AWAITING_CONFIRMATION": {"ask", "respecify", "confirm", "reject", "stop"},
        "TRACKING": {"verify", "release", "stop"},
        "SUSPECTED": {"verify", "respecify", "confirm_lost", "dismiss", "stop"},
        "LOST": {"ask", "respecify", "stop"},
        "REINIT_REQUIRED": {"ask", "respecify", "stop"},
    }

    def _harness(self, responses=None, tracker=None) -> Harness:
        return Harness(
            self,
            responses=responses if responses is not None else [raw(UNIQUE)] * 12,
            tracker_results=tracker or [tracking(), tracking()],
        )

    def _drive_to(self, harness: Harness, state: str) -> None:
        if state == "IDLE":
            return
        if state == "QUERYING":
            harness.publish(1)
            harness.ask()
            # 停在 QUERYING：再 ask 一次，让新查询排成 pending。
            harness.session.state = "QUERYING"
            return
        if state == "AWAITING_CONFIRMATION":
            harness.publish(1)
            harness.ask()
            harness.tick(2)
            return
        if state == "TRACKING":
            harness.seed()
            return
        if state == "SUSPECTED":
            harness.seed()
            harness.session._raise_suspect("drift", "verify_drift")
            return
        if state == "LOST":
            harness.seed()
            harness.request("release", token=harness.session.track_id)
            return
        if state == "REINIT_REQUIRED":
            harness.seed()
            harness.session._finalize_segment("frame_gap")
            harness.session._enter("REINIT_REQUIRED", reason="frame_gap")
            return
        raise AssertionError(state)

    def test_every_cell(self) -> None:
        for state, allowed in self.ALLOWED.items():
            for action in self.ACTIONS:
                if action in allowed:
                    continue
                with self.subTest(state=state, action=action):
                    harness = self._harness()
                    self._drive_to(harness, state)
                    self.assertEqual(harness.session.state, state)
                    before = harness.session.state
                    epoch = harness.session.epoch
                    candidates = harness.session.candidates
                    receipt = harness.request(
                        action,
                        instruction=(
                            bridge.parse_instruction("the bus") if action == "ask" else None
                        ),
                        candidate_index=0 if action == "confirm" else None,
                        token="bogus-token"
                        if action in {"confirm", "reject", "release", "confirm_lost", "dismiss"}
                        else None,
                    )
                    self.assertEqual(receipt.get("outcome"), "REQUEST_INVALID")
                    self.assertEqual(harness.session.state, before)
                    self.assertEqual(harness.session.epoch, epoch)
                    self.assertEqual(harness.session.candidates, candidates)

    def test_terminal_ignores_everything(self) -> None:
        harness = self._harness()
        harness.request("stop")
        self.assertEqual(harness.session.state, "TERMINAL")
        for action in ("ask", "verify", "stop", "release"):
            receipt = harness.request(
                action,
                instruction=bridge.parse_instruction("the bus") if action == "ask" else None,
                token="x" if action == "release" else None,
            )
            self.assertEqual(receipt.get("outcome"), "IGNORED_TERMINAL")
            self.assertEqual(harness.session.state, "TERMINAL")

    def test_suspected_is_only_left_by_a_human_or_a_segment_end(self) -> None:
        harness = self._harness()
        harness.seed()
        harness.session._raise_suspect("lost", "verify_none")
        # 跟踪器继续正常出框（自恢复）也不解除疑似。核验回包不解除疑似另由
        # `VerifyTests.test_inconclusive_never_clears_an_existing_suspect` 钉住。
        harness.publish(3)
        self.assertEqual(harness.session.state, "SUSPECTED")
        receipt = harness.request("dismiss", token=harness.session.suspect_id)
        self.assertEqual(receipt["outcome"], "APPLIED")
        self.assertEqual(harness.session.state, "TRACKING")


# --- AC-1/AC-17：请求生命周期与 worker ------------------------------------


class RequestLifecycleTests(unittest.TestCase):
    def _receipts_for(self, harness: Harness, request_id: str) -> list[str]:
        return [
            row["receipt"]["outcome"]
            for row in harness.journal()
            if row["kind"] == "receipt" and row["receipt"]["request_id"] == request_id
        ]

    def test_exactly_once_and_duplicate_id(self) -> None:
        """槽内残留的同一次写入每 tick 被重读：不再消费，也不再回执。"""
        harness = Harness(self, responses=[raw(UNIQUE), raw(NONE)])
        harness.publish(1)
        first = harness.request("ask", instruction=bridge.parse_instruction("the bus"),
                                request_id="dup")
        self.assertEqual(first["outcome"], "APPLIED")
        epoch = harness.session.epoch
        calls = harness.session.worker.calls_started
        self.assertTrue((harness.runtime / bridge.REQUEST_FILE).is_file())
        harness.tick(10)
        self.assertEqual(harness.session.epoch, epoch)
        self.assertEqual(harness.session.worker.calls_started, calls)
        self.assertEqual(harness.session.last_request["outcome"], "APPLIED")
        self.assertEqual(self._receipts_for(harness, "dup"), ["APPLIED"])

    def test_a_rewritten_duplicate_id_gets_an_ignored_duplicate_receipt(self) -> None:
        """R1@K1K3 F2：A 已消费、B 已消费后，同 id 重新写入 A → `IGNORED_DUPLICATE` 恰一次。"""
        harness = Harness(self, responses=[raw(UNIQUE), raw(UNIQUE)])
        harness.publish(1)
        bus = bridge.parse_instruction("the bus")
        first = harness.request("ask", instruction=bus, request_id="A")
        self.assertEqual(first["outcome"], "APPLIED")
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        second = harness.request(
            "reject", token=harness.session.candidate_result_id, request_id="B"
        )
        self.assertEqual(second["outcome"], "APPLIED")
        self.assertEqual(harness.session.state, "IDLE")
        epoch = harness.session.epoch
        calls = harness.session.worker.calls_started
        results = len(harness.results())
        # 操作者按「结果未知」文案用同一个 --request-id 重发 A（新写入，新的 command_id）。
        again = harness.request("ask", instruction=bus, request_id="A")
        self.assertEqual(
            {key: again.get(key) for key in ("request_id", "action", "outcome")},
            {"request_id": "A", "action": "ask", "outcome": "IGNORED_DUPLICATE"},
        )
        self.assertGreater(again["at_sequence"], second["at_sequence"])
        self.assertEqual(harness.session.state, "IDLE")
        self.assertEqual(harness.session.epoch, epoch)
        self.assertIsNone(harness.session.candidate_result_id)
        self.assertEqual(harness.session.worker.calls_started, calls)
        self.assertEqual(len(harness.results()), results)
        # 重写后的内容留在槽里被继续重读：不再回执。
        harness.tick(10)
        self.assertEqual(
            self._receipts_for(harness, "A"), ["APPLIED", "IGNORED_DUPLICATE"]
        )
        self.assertEqual(harness.session.worker.calls_started, calls)

    def test_foreign_session_and_residual_request(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)])
        bridge.write_request(
            harness.runtime,
            session_id="someone-else",
            request_id="foreign",
            action="stop",
        )
        harness.tick(2)
        self.assertEqual(harness.session.last_request["outcome"], "IGNORED_FOREIGN_SESSION")
        self.assertEqual(harness.session.state, "IDLE")

    def test_unknown_action_is_request_invalid_without_side_effects(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)])
        harness.publish(1)
        bridge.write_request(
            harness.runtime, session_id="s1", request_id="r1", action="stop"
        )
        path = harness.runtime / bridge.REQUEST_FILE
        document = json.loads(path.read_text(encoding="utf-8"))
        document["request"]["action"] = "launch_missiles"
        path.write_text(json.dumps(document), encoding="utf-8")
        harness.tick(2)
        self.assertEqual(harness.session.last_request["outcome"], "REQUEST_INVALID")
        self.assertEqual(harness.session.state, "IDLE")
        self.assertEqual(harness.session.epoch, 0)

    def test_receipts_are_appended_to_the_journal(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)])
        harness.publish(1)
        harness.ask()
        receipts = [row for row in harness.journal() if row["kind"] == "receipt"]
        self.assertTrue(receipts)
        self.assertEqual(receipts[-1]["receipt"]["outcome"], "APPLIED")

    def test_illegal_writer_without_the_lock_is_flagged(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)])
        bridge.write_request(
            harness.runtime, session_id="s1", request_id="sneaky", action="stop"
        )
        harness.tick(2)
        kinds = [row["kind"] for row in harness.journal()]
        self.assertIn("ILLEGAL_WRITER_SUSPECTED", kinds)

    def test_cli_reports_unknown_when_no_receipt_arrives(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        runtime = Path(directory.name)
        clock = FakeClock()

        def sleep(seconds: float) -> None:
            clock.advance(seconds)

        outcome = send_request(
            runtime,
            session_id="s1",
            action="stop",
            monotonic=clock.monotonic,
            sleep=sleep,
        )
        self.assertIsNone(outcome["receipt"])
        self.assertIn("结果未知", outcome["note"])
        # 超时后锁被释放，但请求文件仍在（会话稍后仍可能消费它）。
        self.assertIsNone(bridge.read_writer_lock(runtime))
        self.assertTrue((runtime / bridge.REQUEST_FILE).is_file())

    def test_a_dead_writer_lock_is_reclaimed_and_reported_by_the_cli(self) -> None:
        """R1@K1K3 F1：上一条 CLI 建锁后被杀；下一条 CLI 接管并记下被清理的持有者。"""
        harness = Harness(self, responses=[raw(UNIQUE)])
        crashed = subprocess.Popen([sys.executable, "-c", "pass"])
        crashed.wait()
        bridge.acquire_writer_lock(
            harness.runtime, request_id="crashed-cli", pid=crashed.pid, now=1_234.5
        )
        holders = []

        def sleep(seconds: float) -> None:
            holders.append(bridge.read_writer_lock(harness.runtime))
            harness.tick(1, advance_s=seconds)

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            outcome = send_request(
                harness.runtime,
                session_id="s1",
                action="stop",
                request_id="next",
                monotonic=harness.clock.monotonic,
                sleep=sleep,
            )
        self.assertEqual(outcome["receipt"]["outcome"], "APPLIED")
        self.assertEqual(
            outcome["replaced_writer_lock"],
            {"pid": crashed.pid, "request_id": "crashed-cli", "created_unix_s": 1_234.5},
        )
        self.assertIn(f"pid={crashed.pid}", stderr.getvalue())
        self.assertIn("request_id=crashed-cli", stderr.getvalue())
        self.assertTrue(holders)
        self.assertEqual(
            {(holder.pid, holder.request_id) for holder in holders},
            {(os.getpid(), "next")},
        )
        self.assertIsNone(bridge.read_writer_lock(harness.runtime))
        self.assertNotIn(
            "ILLEGAL_WRITER_SUSPECTED", [row["kind"] for row in harness.journal()]
        )

    def test_the_cli_reports_no_takeover_for_a_free_slot(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        clock = FakeClock()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            outcome = send_request(
                Path(directory.name),
                session_id="s1",
                action="stop",
                monotonic=clock.monotonic,
                sleep=clock.advance,
            )
        self.assertNotIn("replaced_writer_lock", outcome)
        self.assertEqual(stderr.getvalue(), "")

    def test_concurrent_cli_is_writer_busy(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        runtime = Path(directory.name)
        import os

        bridge.acquire_writer_lock(runtime, request_id="held", pid=os.getpid())
        with self.assertRaises(bridge.WriterBusy):
            send_request(runtime, session_id="s1", action="stop")
        self.assertFalse((runtime / bridge.REQUEST_FILE).is_file())


class WorkerTests(unittest.TestCase):
    """AC-17：至多一个在途 + 一条 pending、`SUPERSEDED`、`T_hard`、join。"""

    def test_pending_is_superseded(self) -> None:
        harness = Harness(
            self,
            responses=[raw(UNIQUE), raw(UNIQUE), raw(UNIQUE)],
            worker_spawn=lambda target, name: None,  # 永不完成：模拟在途
        )
        harness.publish(1)
        harness.ask("the bus")
        self.assertTrue(harness.session.worker.busy)
        harness.publish(1)
        harness.request("ask", instruction=bridge.parse_instruction("the taxi"),
                        request_id="queued")
        self.assertIsNotNone(harness.session.worker.pending)
        self.assertEqual(harness.session.last_request["outcome"], "PENDING_QUEUED")
        harness.publish(1)
        harness.request("ask", instruction=bridge.parse_instruction("the truck"),
                        request_id="newer")
        superseded = [
            row
            for row in harness.journal()
            if row["kind"] == "receipt" and row["receipt"]["outcome"] == "SUPERSEDED"
        ]
        self.assertEqual(len(superseded), 1)
        self.assertEqual(superseded[0]["receipt"]["request_id"], "queued")

    def test_hard_limit_marks_stuck_and_needs_a_restart(self) -> None:
        harness = Harness(
            self,
            responses=[raw(UNIQUE)],
            worker_spawn=lambda target, name: None,
            tracker_results=[tracking()],
        )
        harness.publish(1)
        harness.ask()
        harness.clock.advance(T_HARD_S + 1.0)
        harness.tick(2)
        self.assertTrue(harness.session.worker.stuck)
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "backend_fatal")
        # AC-17 修订 1：`backend_fatal` 之后只允许 stop / 读状态。
        harness.publish(1)
        receipt = harness.request("ask", instruction=bridge.parse_instruction("the bus"))
        self.assertEqual(receipt["outcome"], "REQUEST_INVALID")
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        receipt = harness.request("stop")
        self.assertEqual(receipt["outcome"], "APPLIED")
        self.assertEqual(harness.session.state, "TERMINAL")

    def test_stop_joins_and_reports_an_abandoned_thread(self) -> None:
        release = threading.Event()
        self.addCleanup(release.set)
        entered = threading.Event()

        def block(query_id: str) -> None:
            entered.set()
            release.wait(10)

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        runtime = root / "runtime"
        runtime.mkdir()
        publisher = FixtureFramePublisher(runtime)
        publisher.publish(b"jpeg")
        adapter = ScriptedAdapter([raw(UNIQUE)], on_call=block)
        session = LanguageSession(
            SessionConfig(
                session_id="s1",
                session_root=root / "sessions",
                runtime=runtime,
                receipt=build_k_receipt(
                    hz=5.0, retained_frame_count=128, p95_s=2.0, host="test",
                    backend="replay", model_form="c2-adapter",
                ),
                adapter=adapter,
                tracker_name="scripted",
                tracker_factory=lambda: ScriptedTracker(tracking()),
                decode=lambda path: path.read_bytes(),
                preview=StubPreview(),
            )
        )
        session.start()
        self.addCleanup(session.close)
        bridge.write_request(
            runtime,
            session_id="s1",
            request_id="r1",
            action="ask",
            instruction=bridge.parse_instruction("the bus"),
        )
        session.tick()
        self.assertTrue(entered.wait(5))
        session.worker.stop(join_s=0.2)
        self.assertEqual(session.worker.abandoned, ["s1-q1"])


# --- AC-2：查询/返回/确认三个检查点的七个出口 ------------------------------

    # --- AC-8 修订 2（P-A-6）与 AC-16 修订 1 的 backend_fatal 半边（P-A-7）---

    def test_a_plain_backend_exception_keeps_its_type_and_message(self) -> None:
        class Exploding:
            identity = {"backend": "replay", "model_form": "c2-adapter"}

            def predict_one(self, query_id, image_path, surface, g4):
                raise RuntimeError("CUDA out of memory: tried to allocate 2.00 GiB")

        harness = Harness(self, responses=[], tracker_results=[tracking()])
        harness.session.worker._adapter = Exploding()
        harness.publish(1)
        harness.ask()
        harness.tick(1)

        diagnostics = [
            row for row in harness.journal() if row["kind"] == "backend_exception"
        ]
        self.assertTrue(diagnostics)
        detail = diagnostics[-1]["detail"]
        self.assertIn("RuntimeError", detail)
        self.assertIn("CUDA out of memory", detail)
        self.assertEqual(diagnostics[-1]["reason"], "worker_died")
        self.assertEqual(diagnostics[-1]["status"], "backend_error")

        result = harness.results()[0]
        self.assertEqual(result["status"], "backend_error")
        self.assertEqual(result["reject_reason"], "worker_died")
        # 有界重试照常计次，段没有被终止。
        self.assertEqual(harness.session.attempt, 2)
        self.assertEqual(harness.session.state, "QUERYING")

    def test_a_known_selector_reason_is_not_rewritten(self) -> None:
        harness = Harness(
            self,
            responses=[SelectorError("replay_miss", "no row for this key")],
            tracker_results=[tracking()],
        )
        harness.publish(1)
        harness.ask()
        harness.tick(1)
        result = harness.results()[0]
        self.assertEqual(result["reject_reason"], "replay_miss")
        diagnostics = [
            row for row in harness.journal() if row["kind"] == "backend_exception"
        ]
        self.assertEqual(diagnostics[-1]["reason"], "replay_miss")
        self.assertIn("no row for this key", diagnostics[-1]["detail"])

    def test_model_calls_are_counted_apart_from_attempts(self) -> None:
        """AC-6 修订 1：前置拒绝占 `query_id` 与 attempt，但不冒充模型调用。"""
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.publish(1)
        harness.frame_paths(0)[0].unlink()  # 查询检查点在取帧前就失败
        harness.ask()
        harness.tick(2)
        # 帧一直取不到：三次尝试在合同上限内耗尽，全程零模型调用。
        self.assertEqual(harness.session.worker.calls_started, 0)
        self.assertGreaterEqual(harness.session._query_sequence, 3)
        self.assertEqual(harness.results()[0]["reject_reason"], "bundle_missing")
        self.assertEqual(
            [row for row in harness.journal() if row["kind"] == "query_started"], []
        )

        harness.publish(1)
        harness.ask("the bus")
        harness.tick(2)
        self.assertEqual(harness.session.worker.calls_started, 1)
        started = [row for row in harness.journal() if row["kind"] == "query_started"]
        self.assertEqual(len(started), 1)
        self.assertEqual(started[0]["model_calls_started"], 1)

    def test_a_stuck_worker_on_the_verify_path_also_needs_a_restart(self) -> None:
        harness = Harness(
            self, responses=[raw(UNIQUE), raw(UNIQUE)], tracker_results=[tracking()]
        )
        harness.seed()
        harness.publish(1)
        # 播种之后才换掉 spawn：一开始就换会让 seed() 自己卡住。
        harness.session.worker._spawn = lambda target, name: None
        harness.request("verify", ticks=1)
        harness.clock.advance(T_HARD_S + 1.0)
        harness.tick(2)
        self.assertTrue(harness.session.worker.stuck)
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "backend_fatal")
        self.assertIsNone(harness.session.loop)
        harness.publish(1)
        self.assertEqual(
            harness.request("ask", instruction=bridge.parse_instruction("the bus"))[
                "outcome"
            ],
            "REQUEST_INVALID",
        )

    def test_abandoned_queries_are_named_in_the_journal(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.publish(1)
        harness.ask(ticks=1)
        harness.request("stop")
        abandoned = [
            row for row in harness.journal() if row["kind"] == "worker_abandoned"
        ]
        # inline_spawn 下查询同步完成，没有可放弃的线程。真实线程被硬超时 strand
        # 之后 stop 如何记名，由 `test_the_session_records_the_abandoned_query_id_on_stop`
        # 端到端钉住。
        self.assertEqual(abandoned, [])
        self.assertEqual(harness.session.worker.calls_started, 1)

    def test_a_stuck_worker_never_gets_one_more_designate_query(self) -> None:
        """AC-17 修订 1：超硬限之后只允许 stop / 读状态，不得先走一次普通重试。"""
        harness = Harness(
            self,
            responses=[raw(UNIQUE), raw(UNIQUE)],
            worker_spawn=lambda target, name: None,
            tracker_results=[tracking()],
        )
        harness.publish(1)
        harness.ask()
        calls = harness.session.worker.calls_started
        sequence = harness.session._query_sequence
        harness.clock.advance(T_HARD_S + 1.0)
        harness.publish(1)  # 新帧就绪：错误实现会拿它再发一次查询
        harness.tick(2)
        self.assertTrue(harness.session.worker.stuck)
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "backend_fatal")
        self.assertEqual(harness.session.worker.calls_started, calls)
        self.assertEqual(harness.session._query_sequence, sequence)
        # 结果流里 worker_stuck 之后没有新的 designate 查询。
        statuses = [row["status"] for row in harness.results()]
        self.assertEqual(statuses[-1], "backend_error")
        self.assertEqual(
            harness.results()[-1]["reject_reason"], "worker_stuck"
        )
        # 仍能正常 stop（异常不得逃出 tick）。
        self.assertEqual(harness.request("stop")["outcome"], "APPLIED")
        self.assertEqual(harness.session.state, "TERMINAL")

    # --- U-A-2：旧世代回包不得吞掉全局 worker 生命周期故障 ---

    def _stuck_outcome(self, harness: Harness, *, purpose: str, epoch: int,
                       segment_index: int | None, verify_epoch: int,
                       query_id: str = "s1-qStale") -> QueryOutcome:
        job = QueryJob(
            query_id=query_id,
            purpose=purpose,
            epoch=epoch,
            segment_index=segment_index,
            verify_epoch=verify_epoch,
            attempt=1,
            instruction=bridge.parse_instruction("the red car"),
            frame=_any_frame(harness),
            submitted_monotonic_s=harness.clock.monotonic(),
            query_unix_s=harness.clock.unix(),
            latest_at_query=0,
            tracker_box=TRACKER_BOX if purpose == "verify" else None,
        )
        return QueryOutcome(
            job=job,
            raw=None,
            error=SelectorError("worker_stuck", "T_hard exceeded"),
            finished_monotonic_s=harness.clock.monotonic(),
            latency_ms=1.0,
        )

    def test_a_stale_designate_reply_still_escalates_worker_stuck(self) -> None:
        """真实交叉：A 在途 → ask B 换代 → A 硬超时。旧世代只丢结果，不吞全局终止。"""
        harness = Harness(
            self,
            responses=[raw(UNIQUE)] * 3,
            worker_spawn=lambda target, name: None,
            tracker_results=[tracking()],
        )
        harness.publish(1)
        harness.ask(ticks=1)
        first = harness.session.worker.in_flight
        stale_epoch = harness.session.epoch
        harness.publish(1)
        harness.request("ask", instruction=bridge.parse_instruction("the taxi"), ticks=1)
        # 换代之后仍停在 QUERYING：epoch 失配是唯一的丢弃理由。
        self.assertEqual(harness.session.state, "QUERYING")
        self.assertNotEqual(harness.session.epoch, stale_epoch)
        harness.session.worker._results.put(
            self._stuck_outcome(
                harness, purpose="designate", epoch=stale_epoch,
                segment_index=None, verify_epoch=harness.session.verify_epoch,
                query_id=first.query_id,
            )
        )
        harness.tick(1)
        ignored = [
            row for row in harness.results() if row.get("status") == "IGNORED_STALE_EPOCH"
        ]
        self.assertTrue(ignored)  # 结果照常丢弃
        self.assertEqual(ignored[-1]["query_id"], first.query_id)
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "backend_fatal")

    def test_a_stale_verify_reply_still_escalates_worker_stuck(self) -> None:
        harness = Harness(
            self, responses=[raw(UNIQUE), raw(UNIQUE)], tracker_results=[tracking()]
        )
        harness.seed()
        harness.publish(1)
        verifies_before = len(
            [
                row
                for row in harness.results()
                if row.get("purpose") == "verify"
                and row.get("status") != "IGNORED_STALE_EPOCH"
            ]
        )
        alerts = harness.session.consecutive_alert
        verdict = harness.session.last_verdict
        paired = harness.session.last_verified_frame_id
        harness.session.worker._results.put(
            self._stuck_outcome(
                harness, purpose="verify", epoch=harness.session.epoch,
                segment_index=harness.session.segment_index,
                verify_epoch=harness.session.verify_epoch - 1,
            )
        )
        harness.tick(1)
        ignored = [
            row for row in harness.results() if row.get("status") == "IGNORED_STALE_EPOCH"
        ]
        self.assertTrue(ignored)  # 旧回包的丢弃记录不能连带消失
        self.assertEqual(
            len(
                [
                    row
                    for row in harness.results()
                    if row.get("purpose") == "verify"
                    and row.get("status") != "IGNORED_STALE_EPOCH"
                ]
            ),
            verifies_before,
        )
        self.assertEqual(harness.session.consecutive_alert, alerts)
        self.assertEqual(harness.session.last_verdict, verdict)
        self.assertEqual(harness.session.last_verified_frame_id, paired)
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "backend_fatal")
        self.assertIsNone(harness.session.loop)

    def test_an_adapter_reported_stuck_does_not_dispatch_the_pending_query(self) -> None:
        """回包必须对应**在途**任务，派发分支才真正可达——否则断言是空转。"""
        harness = Harness(
            self,
            responses=[raw(UNIQUE)] * 3,
            worker_spawn=lambda target, name: None,
            tracker_results=[tracking()],
        )
        harness.publish(1)
        harness.ask(ticks=1)
        in_flight = harness.session.worker.in_flight
        self.assertIsNotNone(in_flight)
        harness.publish(1)
        harness.request("ask", instruction=bridge.parse_instruction("the taxi"), ticks=1)
        pending = harness.session.worker.pending
        self.assertIsNotNone(pending)
        calls = harness.session.worker.calls_started
        adapter_calls = len(harness.adapter.calls)
        harness.session.worker._results.put(
            self._stuck_outcome(
                harness, purpose="designate", epoch=harness.session.epoch,
                segment_index=None, verify_epoch=harness.session.verify_epoch,
                query_id=in_flight.query_id,
            )
        )
        harness.tick(1)
        self.assertTrue(harness.session.worker.stuck)
        self.assertIsNone(harness.session.worker.in_flight)
        self.assertIsNone(harness.session.worker.pending)
        # 槽位已腾空、pending 还在排队 —— 缺陷实现会在这一刻再打一次模型。
        self.assertEqual(harness.session.worker.calls_started, calls)
        self.assertEqual(len(harness.adapter.calls), adapter_calls)
        started = [row["query_id"] for row in harness.journal() if row["kind"] == "query_started"]
        self.assertNotIn(pending.query_id, started)
        # 被丢弃的 pending 必须解钉帧环，否则那一帧永远淘汰不掉。
        self.assertNotIn(pending.frame.frame_id, harness.session.ring.pinned)
        dropped = [row for row in harness.journal() if row["kind"] == "pending_dropped"]
        self.assertEqual([row["query_id"] for row in dropped], [pending.query_id])

    # --- U-A-3：硬超时后 stop 仍要 join 并记名 ---

    def test_stop_joins_and_names_a_thread_stranded_by_the_hard_limit(self) -> None:
        from controller.language_loop import LanguageWorker, thread_spawn

        release = threading.Event()
        self.addCleanup(release.set)
        entered = threading.Event()

        class Blocking:
            identity = {"backend": "replay", "model_form": "c2-adapter"}

            def predict_one(self, query_id, image_path, surface, g4):
                entered.set()
                release.wait(10)
                return raw(NONE)

        clock = FakeClock()
        worker = LanguageWorker(
            Blocking(), t_hard_s=5.0, spawn=thread_spawn, monotonic=clock.monotonic
        )
        harness = Harness(self, responses=[raw(UNIQUE)])
        harness.publish(1)
        harness.session.repository.load(0)  # 让帧环里有一份加载时快照
        job = QueryJob(
            query_id="s1-qBlocked",
            purpose="designate",
            epoch=1,
            segment_index=None,
            verify_epoch=0,
            attempt=1,
            instruction=bridge.parse_instruction("the red car"),
            frame=_any_frame(harness),
            submitted_monotonic_s=clock.monotonic(),
            query_unix_s=clock.unix(),
            latest_at_query=0,
        )
        worker.submit(job)
        self.assertTrue(entered.wait(5))
        clock.advance(6.0)
        outcomes = worker.poll()
        self.assertTrue(worker.stuck)
        self.assertEqual(outcomes[-1].error.reason, "worker_stuck")
        # 线程还活着：stop 必须 join 一次并把它记名，而不是因 handle=None 直接返回。
        self.assertEqual(worker.stop(join_s=0.2), "worker_abandoned")
        self.assertEqual(worker.abandoned, ["s1-qBlocked"])

    # --- U-A-1 的会话半边：不再 ask 也有界落到 backend_fatal ---

    class _HealthAdapter:
        """只在第 N 次 `health_check()` 到期的桩适配器。"""

        identity = {"backend": "http", "model_form": "c2-merged"}

        def __init__(self, expire_after: int):
            self.checks = 0
            self._expire_after = expire_after

        def health_check(self) -> None:
            self.checks += 1
            if self.checks >= self._expire_after:
                raise SelectorError("worker_stuck", "idle unconfirmed past T_hard")

        def predict_one(self, query_id, image_path, surface, g4):  # pragma: no cover
            raise AssertionError("本用例不应发起任何查询")

    def test_the_session_expires_an_unconfirmed_backend_without_another_ask(self) -> None:
        harness = Harness(self, responses=[], tracker_results=[tracking()])
        adapter = self._HealthAdapter(expire_after=3)
        harness.session.config.adapter = adapter
        harness.publish(1)

        harness.tick(1)
        self.assertEqual(harness.session.state, "IDLE")  # 未到期：什么都不做
        harness.tick(2)  # 第三次 health_check 到期

        self.assertGreaterEqual(adapter.checks, 3)
        self.assertTrue(harness.session.worker.stuck)
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "backend_fatal")
        diagnostics = [
            row
            for row in harness.journal()
            if row["kind"] == "backend_exception" and row["purpose"] == "health_check"
        ]
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0]["reason"], "worker_stuck")
        # 此后只允许 stop / 读状态。
        harness.publish(1)
        self.assertEqual(
            harness.request("ask", instruction=bridge.parse_instruction("the bus"))[
                "outcome"
            ],
            "REQUEST_INVALID",
        )
        self.assertEqual(harness.request("stop")["outcome"], "APPLIED")
        self.assertEqual(harness.session.state, "TERMINAL")

    def test_an_adapter_without_a_health_check_is_left_alone(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        self.assertIsNone(getattr(harness.adapter, "health_check", None))
        harness.seed()
        harness.tick(3)
        self.assertEqual(harness.session.state, "TRACKING")

    # --- AC-8 修订 1 点名的 loop 侧「超时仍 busy」 ---

    def test_a_timeout_while_the_server_is_busy_never_re_enters_it(self) -> None:
        """会话侧的「超时仍 busy」：重试只确认状态，不第二次 POST（AC-8 修订 1）。

        合同的证据指针点名 `test_language_loop（Worker：…超时仍 busy…）`；此前该侧
        只有 selector 半边。这里把**真实** `HttpAdapter` 接进会话：第一次查询在
        `T_ret` 到期时放弃，之后两次有界重试都只发 `GET /status`（服务端仍 busy），
        服务端一共只收到一次 `POST /query`。
        """
        from controller.language_selector import HttpAdapter

        harness = Harness(self, responses=[], tracker_results=[tracking()])
        calls: list[tuple[str, str]] = []

        def opener(request, timeout):
            path = request.full_url.split("127.0.0.1:0", 1)[-1]
            calls.append((request.get_method(), path))
            if path == "/query":
                return b'{"accepted": true}'
            if path == "/status":
                return b'{"state": "busy"}'  # 模型还在跑，没回到 idle
            harness.clock.advance(1.0)  # 轮询一次就过 1 s，`T_ret` 才会到期
            return b'{"state": "busy"}'

        adapter = HttpAdapter(
            "http://127.0.0.1:0",
            t_ret_s=2.0,
            t_hard_s=600.0,
            poll_interval_s=0.0,
            monotonic=harness.clock.monotonic,
            sleep=lambda seconds: None,
            opener=opener,
        )
        harness.session.config.adapter = adapter
        harness.session.worker._adapter = adapter

        harness.publish(1)
        harness.ask(ticks=1)
        for _ in range(ATTEMPT_LIMIT):  # 每次重试都要一帧新帧
            harness.publish(1)
            harness.tick(1)

        self.assertEqual([call for call in calls if call[1] == "/query"], [("POST", "/query")])
        self.assertGreaterEqual(len([call for call in calls if call[1] == "/status"]), 2)
        results = [row for row in harness.results() if row["purpose"] == "designate"]
        self.assertEqual([row["attempt"] for row in results], [1, 2, 3])
        for row in results[:-1]:
            self.assertEqual(row["status"], "backend_error")
            self.assertEqual(row["reject_reason"], "timeout")
        self.assertEqual(results[-1]["status"], "retry_exhausted")
        self.assertEqual(results[-1]["last_reject_reason"], "timeout")
        # 超时不是 `backend_fatal`：适配器只是拒绝重入，会话照常回 IDLE。
        self.assertFalse(harness.session.worker.stuck)
        self.assertFalse(adapter.fatal)
        self.assertTrue(adapter.awaiting_idle)
        self.assertEqual(harness.session.state, "IDLE")
        harness.assert_no_bridge_writes()

    # --- U-A-3 的会话半边与 join 的正向分支 ---

    class _BlockingAdapter:
        identity = {"backend": "replay", "model_form": "c2-adapter"}

        def __init__(self) -> None:
            self.entered = threading.Event()
            self.release = threading.Event()

        def predict_one(self, query_id, image_path, surface, g4):
            self.entered.set()
            self.release.wait(10)
            return raw(NONE)

    def test_the_session_records_the_abandoned_query_id_on_stop(self) -> None:
        """真实线程 → 硬超时 → stop：会话 JSONL 必须记下 query_id 与调用计数。"""
        from controller.language_loop import thread_spawn

        adapter = self._BlockingAdapter()
        self.addCleanup(adapter.release.set)
        harness = Harness(
            self, responses=[], tracker_results=[tracking()], worker_spawn=thread_spawn
        )
        harness.session.config.adapter = adapter
        harness.session.worker._adapter = adapter
        harness.publish(1)
        harness.ask(ticks=1)
        self.assertTrue(adapter.entered.wait(5))
        query_id = harness.session.worker.in_flight.query_id

        harness.clock.advance(T_HARD_S + 1.0)
        harness.tick(2)
        self.assertEqual(harness.session.reason, "backend_fatal")

        with patch("controller.language_loop.WORKER_JOIN_S", 0.2):
            harness.request("stop")
        self.assertEqual(harness.session.state, "TERMINAL")
        records = [row for row in harness.journal() if row["kind"] == "worker_abandoned"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["query_ids"], [query_id])
        self.assertEqual(
            records[0]["model_calls_started"], harness.session.worker.calls_started
        )

    def test_stop_returns_cleanly_when_the_stranded_thread_finishes_in_time(self) -> None:
        """join 那一半的正向分支：线程在预算内退出 → 不记 abandoned。"""
        from controller.language_loop import LanguageWorker, thread_spawn

        adapter = self._BlockingAdapter()
        self.addCleanup(adapter.release.set)
        clock = FakeClock()
        worker = LanguageWorker(
            adapter, t_hard_s=5.0, spawn=thread_spawn, monotonic=clock.monotonic
        )
        harness = Harness(self, responses=[raw(UNIQUE)])
        harness.publish(1)
        harness.session.repository.load(0)
        job = QueryJob(
            query_id="s1-qReleased",
            purpose="designate",
            epoch=1,
            segment_index=None,
            verify_epoch=0,
            attempt=1,
            instruction=bridge.parse_instruction("the red car"),
            frame=_any_frame(harness),
            submitted_monotonic_s=clock.monotonic(),
            query_unix_s=clock.unix(),
            latest_at_query=0,
        )
        worker.submit(job)
        self.assertTrue(adapter.entered.wait(5))
        clock.advance(6.0)
        worker.poll()
        self.assertTrue(worker.stuck)
        threading.Timer(0.2, adapter.release.set).start()
        self.assertIsNone(worker.stop(join_s=5.0))
        self.assertEqual(worker.abandoned, [])

    def test_an_in_flight_frame_copy_survives_ring_eviction(self) -> None:
        """AC-8 修订 1：在途查询的帧副本在该查询结束前不得被帧环淘汰。"""
        harness = Harness(
            self,
            responses=[raw(UNIQUE)] * 3,
            worker_spawn=lambda target, name: None,
            tracker_results=[tracking()],
        )
        harness.publish(1)
        harness.ask(ticks=1)
        in_flight = harness.session.worker.in_flight
        self.assertIsNotNone(in_flight)
        pinned = in_flight.frame.frame_id
        copy_path = in_flight.frame.copy_path
        self.assertIn(pinned, harness.session.ring.pinned)

        # 把帧环塞满到远超容量：未钉住的副本会被淘汰，钉住的这张必须留下。
        harness.session.ring.capacity = 3
        for _ in range(8):
            frame_id = harness.publisher.publish(b"filler-" + str(_).encode())
            harness.session.repository.load(frame_id)
        self.assertIsNotNone(harness.session.ring.snapshot(pinned))
        self.assertTrue(copy_path.is_file())
        self.assertLessEqual(
            len([f for f in harness.session.ring.directory.glob("*.jpg")]), 9
        )

        # 查询结束解钉之后才允许淘汰：再加载一帧越过容量，最老的那张（正是它）被淘汰。
        harness.session.ring.unpin(pinned)
        self.assertIsNotNone(harness.session.ring.snapshot(pinned))
        harness.session.repository.load(harness.publisher.publish(b"one-more"))
        self.assertIsNone(harness.session.ring.snapshot(pinned))
        self.assertFalse(copy_path.is_file())
class StaleRejectionTests(unittest.TestCase):
    """每一例都断言夹具 runtime 的三个桥文件未被写入且发布收据为空。"""

    def _harness(self, responses=None) -> Harness:
        return Harness(self, responses=responses or [raw(UNIQUE)] * 4)

    def test_query_checkpoint_bundle_missing(self) -> None:
        harness = self._harness()
        harness.publish(1)
        image, metadata = harness.frame_paths(0)
        image.unlink()
        harness.ask()
        harness.tick(2)
        first = harness.results()[0]
        self.assertEqual(first["status"], "stale_rejected")
        self.assertEqual(first["reject_reason"], "bundle_missing")
        self.assertIsNone(first["frame_id"])
        harness.assert_no_bridge_writes()

    def test_query_checkpoint_metadata_invalid(self) -> None:
        harness = self._harness()
        harness.publish(1)
        _, metadata = harness.frame_paths(0)
        document = json.loads(metadata.read_text(encoding="utf-8"))
        document["capture_monotonic_clock_id"] = "wall-clock/v9"
        metadata.write_text(json.dumps(document), encoding="utf-8")
        harness.ask()
        harness.tick(2)
        first = harness.results()[0]
        self.assertEqual(first["reject_reason"], "metadata_invalid")
        harness.assert_no_bridge_writes()

    def test_return_checkpoint_frames_late_exceeded(self) -> None:
        harness = self._harness()
        harness.publish(1)
        harness.ask(ticks=1)  # 查询已提交并入队
        harness.publish(harness.receipt.k_ret + 1, tick=False)
        harness.tick(1)
        first = harness.results()[0]
        self.assertEqual(first["status"], "stale_rejected")
        self.assertEqual(first["reject_reason"], "frames_late_exceeded")
        harness.assert_no_bridge_writes()

    def test_return_checkpoint_negative_frame_delta(self) -> None:
        harness = self._harness()
        harness.publish(3)
        harness.ask(ticks=1)
        harness.publisher.publish_pointer(0)
        harness.tick(1)
        first = harness.results()[0]
        self.assertEqual(first["reject_reason"], "negative_frame_delta")
        harness.assert_no_bridge_writes()

    def test_return_checkpoint_wall_deadline_exceeded_on_a_stalled_feed(self) -> None:
        harness = self._harness()
        harness.publish(1)
        harness.ask(ticks=1)
        # `L_r == N`（停帧）但墙钟已过 `T_ret`。
        harness.clock.advance(harness.receipt.t_ret_s + 0.5)
        harness.tick(1)
        first = harness.results()[0]
        self.assertEqual(first["reject_reason"], "wall_deadline_exceeded")
        harness.assert_no_bridge_writes()

    def test_return_checkpoint_image_identity_changed(self) -> None:
        harness = self._harness()
        harness.publish(1)
        harness.ask(ticks=1)
        image, _ = harness.frame_paths(0)
        image.write_bytes(b"different-bytes-same-frame-id")
        harness.tick(1)
        first = harness.results()[0]
        self.assertEqual(first["reject_reason"], "image_identity_changed")
        harness.assert_no_bridge_writes()

    def test_return_checkpoint_bundle_missing(self) -> None:
        harness = self._harness()
        harness.publish(1)
        harness.ask(ticks=1)
        image, metadata = harness.frame_paths(0)
        image.unlink()
        metadata.unlink()
        harness.tick(1)
        first = harness.results()[0]
        self.assertEqual(first["reject_reason"], "bundle_missing")
        harness.assert_no_bridge_writes()

    def test_return_checkpoint_metadata_invalid(self) -> None:
        harness = self._harness()
        harness.publish(1)
        harness.ask(ticks=1)
        _, metadata = harness.frame_paths(0)
        document = json.loads(metadata.read_text(encoding="utf-8"))
        document["capture_monotonic_s"] = -3.0
        metadata.write_text(json.dumps(document), encoding="utf-8")
        harness.tick(1)
        first = harness.results()[0]
        self.assertEqual(first["reject_reason"], "metadata_invalid")
        harness.assert_no_bridge_writes()

    def test_confirmation_checkpoint_beyond_t_conf(self) -> None:
        harness = self._harness()
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        harness.clock.advance(T_CONF_S + 1.0)
        harness.confirm(0)
        statuses = [row["status"] for row in harness.results()]
        self.assertIn("stale_rejected", statuses)
        self.assertEqual(harness.session.state, "IDLE")
        harness.assert_no_bridge_writes()

    def test_confirmation_checkpoint_beyond_cumulative_frames(self) -> None:
        harness = self._harness()
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        harness.publish(harness.receipt.k_ret + harness.receipt.k_conf + 1, tick=False)
        harness.confirm(0)
        rejected = [row for row in harness.results() if row["status"] == "stale_rejected"]
        self.assertTrue(rejected)
        self.assertEqual(rejected[-1]["reject_reason"], "frames_late_exceeded")
        harness.assert_no_bridge_writes()


# --- AC-3：加载时快照、静音播种、追平与发布最终门 --------------------------


class GatedSeedingTests(unittest.TestCase):
    def test_snapshot_precedes_tracker_and_publisher(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        snapshot = harness.session.ring.snapshot(0)
        self.assertIsNotNone(snapshot)
        image, _ = harness.frame_paths(0)
        self.assertEqual(snapshot.image_sha256, sha256_bytes(image.read_bytes()))
        # 帧环副本与盘上字节一致，元数据取的是 bundle 的完整值。
        self.assertEqual(snapshot.copy_path.read_bytes(), image.read_bytes())
        self.assertEqual(
            snapshot.metadata, json.loads(harness.frame_paths(0)[1].read_text("utf-8"))
        )

    def test_initialize_publication_is_dropped_while_muted(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        muted = [row for row in harness.receipts() if row["outcome"] == "MUTED_DROPPED"]
        self.assertEqual(len(muted), 2)  # 观测 + 由它推出的云台
        self.assertEqual({row["channel"] for row in muted}, {"observation", "look_at"})
        self.assertFalse((harness.runtime / "tracking_observation.json").is_file())
        # 一次性 hold 永远透传（安全回退不受静音影响）。
        self.assertTrue((harness.runtime / "body_command.json").is_file())

    def test_first_written_receipt_passes_all_five_checks(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        harness.publish(1)
        written = [row for row in harness.receipts() if row["outcome"] == "WRITTEN"]
        self.assertTrue(written)
        first = written[0]
        self.assertEqual(first["channel"], "observation")
        detail = first["detail"]
        self.assertEqual(detail["identity"], "verified")
        self.assertEqual(
            detail["snapshot_sha256"],
            sha256_bytes(harness.frame_paths(first["frame_id"])[0].read_bytes()),
        )
        self.assertLessEqual(detail["frame_delta"], K_PUB)
        self.assertGreaterEqual(detail["load_elapsed_s"], 0.0)
        self.assertLessEqual(detail["capture_age_s"], T_STALL_S)
        self.assertTrue((harness.runtime / "tracking_observation.json").is_file())

    def test_tracker_rejecting_the_seed_frame_does_not_start_a_segment(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)])
        harness._tracker_plans = []
        harness.session.config.tracker_factory = lambda: ScriptedTracker([], init_ok=False)
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        harness.confirm(0)
        self.assertIsNone(harness.session.loop)
        self.assertEqual(harness.session.state, "IDLE")
        aborts = [row for row in harness.journal() if row["kind"] == "seeding_aborted"]
        self.assertEqual(aborts[-1]["reason"], "tracker_rejected_init")

    def test_seeding_abort_leaves_only_muted_receipts_and_no_segment(self) -> None:
        """播种在 `initialize` 中途失败：收据只有静音那两条，零 WRITTEN、零关联。

        这条路径**不属于** AC-2 点名的「初始化前失败」七个出口（那七个出口在
        创建发布器之前就返回），如实记录它的实际收据形态。
        """
        # (a) 跟踪器拒绝初始化：失败发生在任何发布尝试之前，收据为空。
        harness = Harness(self, responses=[raw(UNIQUE)])
        harness.session.config.tracker_factory = lambda: ScriptedTracker([], init_ok=False)
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        harness.confirm(0)
        self.assertEqual(harness.receipts(), [])
        self.assertIsNone(harness.session.loop)
        self.assertEqual(harness.session.segments_seeded, 0)
        self.assertEqual(harness.session.retired_track_ids, [])

        # (b) 初始化里、静音发布之后才失败：收据只有那两条 MUTED_DROPPED，
        #     零 WRITTEN、零关联、不留活段。
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.publish(1)
        _, metadata = harness.frame_paths(0)
        document = json.loads(metadata.read_text(encoding="utf-8"))
        document.pop("simulation_time_s")  # `TrackLoop.initialize` 在发布之后才读它
        metadata.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
        harness.ask()
        harness.tick(2)
        harness.confirm(0)
        receipts = harness.receipts()
        self.assertEqual({row["outcome"] for row in receipts}, {"MUTED_DROPPED"})
        self.assertEqual(len(receipts), 2)
        self.assertIsNone(harness.session.loop)
        self.assertIsNone(harness.session.publisher)
        self.assertEqual(harness.session.segments_seeded, 0)
        self.assertEqual(harness.session.retired_track_ids, [])
        aborts = [row for row in harness.journal() if row["kind"] == "seeding_aborted"]
        self.assertEqual(aborts[-1]["reason"], "metadata_invalid")
class PublishGateTests(unittest.TestCase):
    """AC-3：门的六个出口各有红/绿，并且被拒帧及其衍生控制零写入。"""

    def _seeded(self) -> Harness:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        return harness

    def _observation_receipts(self, harness: Harness) -> list[dict]:
        return [row for row in harness.receipts() if row["channel"] == "observation"]

    def test_green_path_writes(self) -> None:
        harness = self._seeded()
        harness.publish(1)
        self.assertEqual(self._observation_receipts(harness)[-1]["outcome"], "WRITTEN")
        self.assertEqual(harness.session.state, "TRACKING")

    def test_image_identity_changed_between_load_and_write(self) -> None:
        harness = self._seeded()
        original = harness.session.publisher

        def swap_bytes(frame_id: int) -> None:
            image, _ = harness.frame_paths(frame_id)
            image.write_bytes(b"swapped-jpeg-same-json")

        # JSON 不变、JPEG 已换：加载后、写桥前替换字节。
        harness.publisher.publish(b"payload-a")
        frame_id = harness.publisher.next_frame_id - 1
        original_gate = original._gate

        def gate(target: int):
            swap_bytes(target)
            return original_gate(target)

        original._gate = gate
        harness.tick(1)
        receipts = self._observation_receipts(harness)
        self.assertEqual(receipts[-1]["outcome"], "PUBLISH_REJECTED")
        self.assertEqual(receipts[-1]["reason"], "image_identity_changed")
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "image_identity_changed")

    def test_frame_rollback_and_catchup_stale(self) -> None:
        harness = self._seeded()
        harness.publisher.publish(b"payload-a")
        original = harness.session.publisher
        original_gate = original._gate

        def rollback(target: int):
            harness.publisher.publish_pointer(0)
            return original_gate(target)

        original._gate = rollback
        harness.tick(1)
        receipts = self._observation_receipts(harness)
        self.assertEqual(receipts[-1]["reason"], "frame_rollback")

    def test_publish_expired_when_the_frame_head_did_not_move(self) -> None:
        harness = self._seeded()
        harness.publisher.publish(b"payload-a")
        original = harness.session.publisher
        original_gate = original._gate

        def stall(target: int):
            harness.clock.advance(harness.receipt.t_pub_s + 0.5)
            return original_gate(target)

        original._gate = stall
        harness.tick(1)
        receipts = self._observation_receipts(harness)
        self.assertEqual(receipts[-1]["reason"], "publish_expired")

    def test_bundle_missing_at_the_gate(self) -> None:
        harness = self._seeded()
        harness.publisher.publish(b"payload-a")
        frame_id = harness.publisher.next_frame_id - 1
        original = harness.session.publisher
        original_gate = original._gate

        def remove(target: int):
            harness.frame_paths(target)[0].unlink()
            return original_gate(target)

        original._gate = remove
        harness.tick(1)
        receipts = self._observation_receipts(harness)
        self.assertEqual(receipts[-1]["reason"], "bundle_missing")

    def test_orphan_control_is_refused_and_recorded(self) -> None:
        harness = self._seeded()
        publisher = harness.session.publisher
        publisher.accepted_frame_id = None
        path = publisher.look_at((1.0, 2.0, 3.0))
        self.assertIsNone(path)
        receipts = [row for row in harness.receipts() if row["channel"] == "look_at"]
        self.assertEqual(receipts[-1]["reason"], "orphan_control")
        self.assertEqual(publisher.fatal_reason, "orphan_control")

    def test_a_rejected_write_never_rewrites_an_earlier_written_receipt(self) -> None:
        harness = self._seeded()
        harness.publish(1)
        written_before = [row for row in harness.receipts() if row["outcome"] == "WRITTEN"]
        publisher = harness.session.publisher
        # 观测成功之后帧源变化 → 云台被拒，观测收据保持 WRITTEN。
        harness.frame_paths(publisher.accepted_frame_id)[0].write_bytes(b"changed")
        self.assertIsNone(publisher.look_at((1.0, 2.0, 3.0)))
        receipts = harness.receipts()
        written_after = [row for row in receipts if row["outcome"] == "WRITTEN"]
        self.assertEqual(written_before, written_after)
        self.assertEqual(receipts[-1]["channel"], "look_at")
        self.assertEqual(receipts[-1]["reason"], "image_identity_changed")

    def test_no_receipts_after_finalize(self) -> None:
        harness = self._seeded()
        harness.publish(1)
        count = len(harness.receipts())
        harness.request("release", token=harness.session.track_id)
        harness.publish(2)
        self.assertEqual(len(harness.receipts()), count)
        state = bridge.read_tracker_state(harness.runtime)["tracker_state"]
        self.assertFalse(state["publishing"])
        self.assertEqual(state["state"], "LOST")

    # --- AC-3 修订 2（P-A-2）---

    def test_a_rejected_write_neither_advances_nor_associates(self) -> None:
        """拒绝与静音都不推进 `last_published_frame_id`、不建立 `accepted_frame_id`。

        断言落在发布器对象上：段被 finalize 之后 `tracker_state` 的镜像必然是 null，
        读桥文件分不出「正确实现」与「把赋值搬到门之前的实现」。
        """
        harness = self._seeded()
        harness.publish(1)
        publisher = harness.session.publisher
        published_before = publisher.last_published_frame_id
        self.assertIsNotNone(published_before)
        self.assertEqual(publisher.accepted_frame_id, published_before)

        harness.publisher.publish(b"payload-a")
        original_gate = publisher._gate

        def reject(target: int):
            harness.frame_paths(target)[0].unlink()
            return original_gate(target)

        publisher._gate = reject
        harness.tick(1)

        rejected = [
            row for row in harness.receipts() if row["outcome"] == "PUBLISH_REJECTED"
        ]
        self.assertTrue(rejected)
        self.assertEqual(publisher.last_published_frame_id, published_before)
        self.assertIsNone(publisher.accepted_frame_id)

    def test_muted_seeding_never_associates_and_never_reports_orphan_control(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        muted = [row for row in harness.receipts() if row["outcome"] == "MUTED_DROPPED"]
        self.assertEqual({row["channel"] for row in muted}, {"observation", "look_at"})
        self.assertEqual([row["reason"] for row in muted], [None, None])
        self.assertEqual(
            [row for row in harness.receipts() if row["reason"] == "orphan_control"], []
        )
        self.assertEqual(harness.session.state, "TRACKING")
        # 静音期没有任何一条收据推进过发布帧号。
        written = [row for row in harness.receipts() if row["outcome"] == "WRITTEN"]
        self.assertEqual(written, [])
        self.assertIsNone(harness.session.publisher.last_published_frame_id)

    def test_receipt_outcomes_and_channels_stay_inside_their_closed_sets(self) -> None:
        from controller.gated_publisher import RECEIPT_CHANNELS, RECEIPT_OUTCOMES

        harness = self._seeded()
        harness.publish(2)
        # R-B8 / AC-19：机身通道的写失败与无观测安全 hold 各自单列，安全 hold 不冒充门控速度。
        self.assertEqual(
            RECEIPT_OUTCOMES[:4],
            ("WRITTEN", "PUBLISH_REJECTED", "MUTED_DROPPED", "WRITE_FAILED"),
        )
        # P1-ENG-FASTFIX-001 §3.2：末尾恰追加捕获模式的 `PUBLISH_DROPPED`（既有四个成员逐位不变；本会话是兼容路径，不产生它）。
        self.assertEqual(RECEIPT_OUTCOMES[4:], ("PUBLISH_DROPPED",))
        self.assertNotIn("PUBLISH_DROPPED", {row["outcome"] for row in harness.receipts()})
        # P1-ENG-ACQ-001 §3.7：无观测转向通道 `slew_look_at` 单列（每个 designation_id 至多一次）。
        # P1-ENG-CAPTURE-001 IR-9：既有五个成员逐位不变，末尾恰追加预测云台通道 `predicted_look_at`。
        self.assertEqual(
            RECEIPT_CHANNELS,
            ("observation", "look_at", "body_command", "body_safety_hold", "slew_look_at", "predicted_look_at"),
        )
        self.assertTrue(
            {row["outcome"] for row in harness.receipts()} <= set(RECEIPT_OUTCOMES)
        )
        self.assertTrue(
            {row["channel"] for row in harness.receipts()} <= set(RECEIPT_CHANNELS)
        )

# --- R-B8 / AC-19 / AC-4 修订 4：冻结阈值规划器接入语言会话 ----------------


def tilt_camera(harness: "Harness", off_nadir_deg: float) -> None:
    """夹具相机绕 x 轴向 +z 倾斜（正交基），模拟云台接近 45° 限位。"""
    theta = math.radians(off_nadir_deg)
    harness.publisher.camera_forward_world = (0.0, -math.cos(theta), math.sin(theta))
    harness.publisher.camera_right_world = (1.0, 0.0, 0.0)
    harness.publisher.camera_up_world = (0.0, math.sin(theta), math.cos(theta))


class BodyPlannerIntegrationTests(unittest.TestCase):
    """AC-19：每个已确认段复用冻结 threshold 规划器；速度只随同帧合格观测经门写出，
    hold 走无观测安全通道并留收据；配置不符拒绝启动；段与段之间规划器实例独立。"""

    def _harness(self, tracker_results=None, responses=None) -> Harness:
        return Harness(
            self,
            responses=responses or [raw(UNIQUE)],
            tracker_results=tracker_results or [tracking()],
            body=True,
        )

    @staticmethod
    def _body_rows(harness: Harness) -> list[dict]:
        return [
            row for row in harness.receipts()
            if row["channel"] in {"body_command", "body_safety_hold"}
        ]

    @staticmethod
    def _run_records(harness: Harness) -> list[dict]:
        records = []
        for path in sorted((harness.runtime / "runs").glob("*/frames.jsonl")):
            records.extend(
                json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        return records

    def _config_error(self, **overrides) -> str:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        planner = json.loads(BODY_PLANNER_CONFIG.read_text(encoding="utf-8"))
        scenario = json.loads(BODY_SCENARIO_CONFIG.read_text(encoding="utf-8"))
        if "capture_hz" in overrides:
            planner["command"]["capture_hz"] = overrides["capture_hz"]
        if "calibration_sha" in overrides:
            planner["calibration"]["artifact_sha256"] = overrides["calibration_sha"]
        if "gimbal_deg" in overrides:
            scenario["gimbal"]["maximum_off_nadir_deg"] = overrides["gimbal_deg"]
        planner_path = root / "planner.json"
        scenario_path = root / "scenario.json"
        planner_path.write_text(json.dumps(planner), encoding="utf-8")
        scenario_path.write_text(json.dumps(scenario), encoding="utf-8")
        runtime = root / "runtime"
        runtime.mkdir()
        adapter = ScriptedAdapter([])
        receipt = build_k_receipt(
            hz=5.0, retained_frame_count=128, p95_s=2.0, host="test", backend="replay",
            model_form="c2-adapter", model_identity=dict(adapter.identity),
            scenario_id="deterministic-loop-default",
        )
        with self.assertRaises(ConfigMismatch) as caught:
            LanguageSession(
                SessionConfig(
                    session_id="body-config",
                    session_root=root / "sessions",
                    runtime=runtime,
                    receipt=receipt,
                    adapter=adapter,
                    tracker_name="scripted",
                    ground_plane_y_m=overrides.get("ground_plane_y_m", 0.2),
                    body_planner_config=planner_path,
                    body_scenario_config=scenario_path,
                )
            )
        # 拒绝发生在任何桥写入与会话锁之前。
        self.assertFalse((runtime / "tracker_state.json").exists())
        self.assertFalse((runtime / "body_command.json").exists())
        return str(caught.exception)

    def test_a_mismatched_planner_config_refuses_to_start(self) -> None:
        self.assertIn("capture_hz", self._config_error(capture_hz=10.0))
        self.assertIn("calibration artifact hash", self._config_error(calibration_sha="0" * 64))
        self.assertIn("differs from the live", self._config_error(gimbal_deg=60.0))
        self.assertIn("ground_plane_y_m", self._config_error(ground_plane_y_m=0.0))

    def test_the_run_cli_always_binds_the_frozen_planner(self) -> None:
        from controller.language_loop import build_parser

        arguments = build_parser().parse_args(
            ["run", "--session-id", "s", "--session-root", "/tmp/x", "--runtime", "/tmp/r",
             "--k-receipt", "k.json", "--backend", "replay"]
        )
        self.assertEqual(Path(arguments.body_planner_config), BODY_PLANNER_CONFIG)
        self.assertEqual(Path(arguments.body_scenario_config), BODY_SCENARIO_CONFIG)
        harness = self._harness()
        identity = harness.session.body_runtime.identity
        self.assertEqual(identity["planner"], "threshold-corridor-v1")
        self.assertEqual(identity["contract_version"], "body-planner-contract/v1")
        self.assertEqual(
            identity["config_sha256"], sha256_bytes(BODY_PLANNER_CONFIG.read_bytes())
        )
        started = [row for row in harness.journal() if row["kind"] == "session_started"]
        self.assertEqual(started[-1]["body_planner"], identity)

    def test_seeding_keeps_the_one_time_hold_and_writes_no_image_derived_body_command(self) -> None:
        harness = self._harness()
        tilt_camera(harness, 40.0)
        harness.seed()
        # 播种：冻结 initialize() 的一次性 hold 照旧透传；此刻机身通道零收据、零速度。
        body = json.loads((harness.runtime / "body_command.json").read_text(encoding="utf-8"))
        self.assertEqual(body["command"]["mode"], "hold")
        self.assertEqual(self._body_rows(harness), [])
        self.assertEqual(
            {row["outcome"] for row in harness.receipts()}, {"MUTED_DROPPED"}
        )

    def test_a_tilted_camera_moves_the_body_with_a_same_frame_gated_velocity(self) -> None:
        harness = self._harness()
        tilt_camera(harness, 40.0)
        harness.seed()
        harness.publish(1)
        rows = harness.receipts()
        observations = [r for r in rows if r["channel"] == "observation" and r["outcome"] == "WRITTEN"]
        velocities = [r for r in rows if r["channel"] == "body_command"]
        self.assertTrue(observations and velocities)
        self.assertEqual(velocities[-1]["outcome"], "WRITTEN")
        # 速度绑定在同一帧的合格观测上，门的五项核验逐项写进收据。
        self.assertEqual(velocities[-1]["frame_id"], observations[-1]["frame_id"])
        self.assertEqual(velocities[-1]["detail"]["mode"], "velocity_world")
        self.assertEqual(velocities[-1]["detail"]["identity"], "verified")
        self.assertAlmostEqual(velocities[-1]["detail"]["velocity_world_mps"][2], 4.0)
        body = json.loads((harness.runtime / "body_command.json").read_text(encoding="utf-8"))
        self.assertEqual(body["command"]["mode"], "velocity_world")
        planner = [r for r in self._run_records(harness) if r.get("body_planner")][-1]["body_planner"]
        self.assertEqual((planner["mode"], planner["published_mode"]), ("velocity_world", "velocity_world"))
        self.assertEqual(harness.session.state, "TRACKING")

    def test_a_frame_without_an_observation_sends_a_safety_hold_and_keeps_the_segment(self) -> None:
        # 回归：门控通道只按上一帧关联核验时，无观测帧的 hold 会被判 catchup_stale 并终止整段。
        harness = self._harness(
            tracker_results=[[TrackerResult(TRACKER_BOX, True, 1.0, "tracker"), TrackerResult.lost("gone")]
                             + tracking()]
        )
        tilt_camera(harness, 40.0)
        harness.seed()
        harness.publish(1)
        harness.publish(1)
        holds = [r for r in harness.receipts() if r["channel"] == "body_safety_hold"]
        self.assertEqual([h["outcome"] for h in holds], ["WRITTEN"])
        self.assertEqual(holds[0]["detail"]["reason"], "no_observation")
        self.assertIsNone(holds[0]["frame_id"])
        self.assertNotIn(
            "PUBLISH_REJECTED", {r["outcome"] for r in harness.receipts()}
        )
        # 段还在（raw_lost 只把它升成疑似，不是发布门终止）。
        self.assertIn(harness.session.state, {"TRACKING", "SUSPECTED"})
        self.assertIsNotNone(harness.session.loop)
        self.assertIsNone(harness.session.publisher.fatal_reason)

    def test_a_rejected_velocity_falls_back_to_a_safety_hold_and_ends_the_segment(self) -> None:
        harness = self._harness()
        tilt_camera(harness, 40.0)
        harness.seed()
        publisher = harness.session.publisher
        original = publisher._derived

        def derived(channel, write, **kwargs):
            if channel == "body_command":
                image, _ = harness.frame_paths(publisher.accepted_frame_id)
                image.write_bytes(b"swapped-after-observation")
            return original(channel, write, **kwargs)

        publisher._derived = derived
        harness.publish(1)
        body = self._body_rows(harness)
        self.assertEqual(
            [(r["channel"], r["outcome"]) for r in body],
            [("body_command", "PUBLISH_REJECTED"), ("body_safety_hold", "WRITTEN")],
        )
        self.assertEqual(body[0]["reason"], "image_identity_changed")
        self.assertEqual(body[1]["detail"]["reason"], "publish_failure_fallback")
        planner = [r for r in self._run_records(harness) if r.get("body_planner")][-1]["body_planner"]
        # 日志如实区分：意图是速度，实际写出的是回退 hold。
        self.assertEqual(planner["mode"], "velocity_world")
        self.assertEqual(planner["published_mode"], "hold")
        self.assertIn("BodyCommandNotWritten", planner["publish_error"])
        written = json.loads((harness.runtime / "body_command.json").read_text(encoding="utf-8"))
        self.assertEqual(written["command"]["mode"], "hold")
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "image_identity_changed")

    def test_a_planner_exception_publishes_a_safety_hold(self) -> None:
        harness = self._harness()
        tilt_camera(harness, 40.0)
        harness.seed()

        def boom(*args, **kwargs):
            raise RuntimeError("planner blew up")

        harness.session.loop.body_planner.decide = boom
        harness.publish(1)
        body = self._body_rows(harness)
        self.assertEqual([(r["channel"], r["outcome"]) for r in body], [("body_safety_hold", "WRITTEN")])
        self.assertEqual(body[0]["detail"]["reason"], "planner_exception")
        self.assertEqual(harness.session.state, "TRACKING")

    def _failing_writes(self, harness: Harness, *, fail_hold: bool) -> None:
        runtime_publisher = harness.session.publisher._publisher
        original = runtime_publisher.body_command

        def body_command(command):
            if command.mode != "hold" or fail_hold:
                raise OSError(f"disk full ({command.mode})")
            return original(command)

        runtime_publisher.body_command = body_command

    def test_a_failed_velocity_write_is_receipted_and_falls_back_to_a_hold(self) -> None:
        harness = self._harness()
        tilt_camera(harness, 40.0)
        harness.seed()
        self._failing_writes(harness, fail_hold=False)
        harness.publish(1)
        body = self._body_rows(harness)
        self.assertEqual(
            [(r["channel"], r["outcome"]) for r in body],
            [("body_command", "WRITE_FAILED"), ("body_safety_hold", "WRITTEN")],
        )
        self.assertIn("disk full", body[0]["detail"]["error"])
        self.assertEqual(harness.session.state, "TRACKING")

    def test_a_failed_fallback_hold_fails_closed(self) -> None:
        harness = self._harness()
        tilt_camera(harness, 40.0)
        harness.seed()
        self._failing_writes(harness, fail_hold=True)
        harness.publish(1)
        body = self._body_rows(harness)
        self.assertEqual(
            [(r["channel"], r["outcome"]) for r in body],
            [("body_command", "WRITE_FAILED"), ("body_safety_hold", "WRITE_FAILED")],
        )
        # 安全 hold 再失败：冻结 TrackLoop 以 BODY_COMMAND_FAIL_CLOSED 终止段，会话按 AC-4 修订 2 兜底逐字留痕。
        unexpected = [r for r in harness.journal() if r["kind"] == "unexpected_segment_end"]
        self.assertEqual(unexpected[-1]["event"], "BODY_COMMAND_FAIL_CLOSED")
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "metadata_invalid")
        before = len(harness.receipts())
        harness.publish(3)
        self.assertEqual(len(harness.receipts()), before)

    def test_each_segment_gets_its_own_planner_and_nothing_is_written_after_retirement(self) -> None:
        harness = self._harness(
            tracker_results=[tracking(), tracking()],
            responses=[raw(UNIQUE), raw(UNIQUE)],
        )
        tilt_camera(harness, 40.0)
        harness.seed()
        harness.publish(1)
        first_planner = harness.session.loop.body_planner
        first_estimator = harness.session.loop.body_estimator
        self.assertIsNot(first_planner, harness.session.body_runtime.planner)
        self.assertTrue(first_estimator.initialized)
        harness.request("release", token=harness.session.track_id)
        self.assertEqual(harness.session.state, "LOST")
        retired = len(harness.receipts())
        harness.publish(3)
        # 退役段：发布器已关闭，机身通道零新增（没有由图像推出的命令，也没有补 hold）。
        self.assertEqual(len(harness.receipts()), retired)
        harness.request("respecify")
        harness.tick(2)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        harness.confirm(0)
        harness.tick(1)
        self.assertEqual(harness.session.state, "TRACKING")
        second_planner = harness.session.loop.body_planner
        self.assertIsNot(second_planner, first_planner)
        self.assertIsNot(harness.session.loop.body_estimator, first_estimator)
        self.assertFalse(harness.session.loop.body_estimator.initialized)
        harness.publish(1)
        second = [r for r in harness.receipts()[retired:] if r["channel"] == "body_command"]
        self.assertTrue(second and all(r["track_id"] == harness.session.track_id for r in second))


class CatchUpTests(unittest.TestCase):
    def test_only_the_batch_tail_is_published(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        harness.publish(5, tick=False)
        harness.tick(1)
        written = [
            row
            for row in harness.receipts()
            if row["outcome"] == "WRITTEN" and row["channel"] == "observation"
        ]
        # 追平 5 帧只发布批末帧一次。
        self.assertEqual(len(written), 1)
        self.assertEqual(written[0]["frame_id"], 5)
        observation = json.loads(
            (harness.runtime / "tracking_observation.json").read_text(encoding="utf-8")
        )
        self.assertEqual(observation["observation"]["frame_id"], 5)

    def test_frame_stall_terminates_the_segment(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        harness.clock.advance(T_STALL_S + 0.5)
        harness.tick(1)
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "frame_stall")

    def test_bad_metadata_during_catch_up_maps_to_reinit_required(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        harness.publisher.publish(b"payload")
        frame_id = harness.publisher.next_frame_id - 1
        _, metadata = harness.frame_paths(frame_id)
        document = json.loads(metadata.read_text(encoding="utf-8"))
        document["capture_monotonic_clock_id"] = "nope/v1"
        metadata.write_text(json.dumps(document), encoding="utf-8")
        harness.tick(1)
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "metadata_invalid")

    def test_missing_intermediate_frame_is_a_gap(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        harness.publish(3, tick=False)
        harness.frame_paths(2)[0].unlink()
        harness.tick(1)
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "frame_gap")

    def test_empty_poll_is_not_an_error(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        harness.tick(3, advance_s=0.1)
        self.assertEqual(harness.session.state, "TRACKING")


# --- AC-4：原始状态镜像 ----------------------------------------------------


class StateMirrorTests(unittest.TestCase):
    def test_raw_lost_raises_a_suspect_without_touching_the_gate(self) -> None:
        results = [
            TrackerResult(TRACKER_BOX, True, 1.0, "placeholder"),
            TrackerResult.lost("tracker_reported_failure"),
            TrackerResult(TRACKER_BOX, True, 1.0, "placeholder"),
        ] + tracking()
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[results])
        harness.seed()
        harness.publish(1)
        state = bridge.read_tracker_state(harness.runtime)["tracker_state"]
        self.assertEqual(state["tracker_raw_state"], "TRACKING")
        self.assertTrue(state["publishing"])
        harness.publish(1)  # 第二帧：跟踪器报丢
        self.assertEqual(harness.session.state, "SUSPECTED")
        state = bridge.read_tracker_state(harness.runtime)["tracker_state"]
        self.assertEqual(state["suspect_kind"], "tracker_failure")
        self.assertEqual(state["tracker_raw_state"], "LOST")
        # 提醒不改发布门。
        self.assertTrue(state["publishing"])
        harness.publish(1)  # 第三帧：跟踪器自恢复
        state = bridge.read_tracker_state(harness.runtime)["tracker_state"]
        self.assertEqual(state["tracker_raw_state"], "TRACKING")
        self.assertEqual(harness.session.state, "SUSPECTED")  # 只有人能解除
        written = [row for row in harness.receipts() if row["outcome"] == "WRITTEN"]
        self.assertTrue(any(row["frame_id"] == 3 for row in written))

    def test_sequence_is_monotonic(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        sequences = []
        for _ in range(3):
            harness.publish(1)
            sequences.append(
                bridge.read_tracker_state(harness.runtime)["tracker_state"]["sequence"]
            )
        self.assertEqual(sequences, sorted(sequences))

    def test_frozen_paths_are_untouched_in_the_working_tree(self) -> None:
        completed = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--",
                "Assets",
                "config",
                "tools/eng_sft",
                "controller/protocol.py",
                "controller/tracking_entry.py",
                "controller/track_loop.py",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.stdout.strip(), "")


# --- AC-5：首次指定必须人工确认 --------------------------------------------

    # --- AC-4 修订 1（P-A-3）与修订 2（P-A-8）---

    def test_raw_lost_inside_a_catch_up_batch_survives_a_raw_ok_tail(self) -> None:
        """一批里 LOST→TRACKING：批末 raw_ok 不抹掉逐帧事实，两者同时成立。"""
        results = [
            TrackerResult(TRACKER_BOX, True, 1.0, "placeholder"),  # 帧 1
            TrackerResult.lost("tracker_reported_failure"),  # 帧 2：批内 LOST
            TrackerResult(TRACKER_BOX, True, 1.0, "placeholder"),  # 帧 3：批末 ok
        ] + tracking()
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[results])
        harness.seed()
        before = len(harness.receipts())
        harness.publish(3, tick=False)
        harness.tick(1)

        state = bridge.read_tracker_state(harness.runtime)["tracker_state"]
        # 共存：会话疑似，而镜像的原始状态是批末那一帧的 TRACKING。
        self.assertEqual(state["state"], "SUSPECTED")
        self.assertEqual(state["tracker_raw_state"], "TRACKING")
        self.assertEqual(state["suspect_kind"], "tracker_failure")
        self.assertTrue(state["publishing"])

        raised = [row for row in harness.journal() if row["kind"] == "suspect_raised"]
        self.assertEqual(len(raised), 1)
        suspect_id = harness.session.suspect_id
        harness.publish(1)
        self.assertEqual(harness.session.suspect_id, suspect_id)

        # 本批新增收据：批末帧恰一条 WRITTEN，批内 LOST 帧一条都没有。
        fresh = harness.receipts()[before:]
        self.assertEqual(
            [row["frame_id"] for row in fresh if row["outcome"] == "WRITTEN"
             and row["channel"] == "observation"][:1],
            [3],
        )
        self.assertNotIn(2, [row["frame_id"] for row in fresh])
        self.assertEqual(
            {row["outcome"] for row in fresh} - {"WRITTEN", "PUBLISH_REJECTED", "MUTED_DROPPED"},
            set(),
        )

    def _force_terminal_record(self, harness: Harness, *, event: str, reason: str) -> int:
        """经生产路径（`RecordingRunLogger.append`）写一条终端记录并置 loop 终止。

        本项的段从不装 rate/qualification/re-anchor/body planner，所以这些事件在
        真实运行里到不了；裁定明说「无需启用……来演练此路径」，故在这里直接驱动
        `TrackLoop` 终止时会走的同一个出口。
        """
        frame_id = harness.publisher.next_frame_id
        harness.session.logger.append(
            {
                "frame_id": frame_id,
                "capture_unix_s": None,
                "simulation_time_s": None,
                "box_norm": None,
                "ok": False,
                "confidence": None,
                "confidence_source": "none",
                "state": "ERROR_REINIT_REQUIRED",
                "event": event,
                "reason": reason,
                "compute_stage": None,
                "compute_latency_ms": None,
                "frame_age_ms": None,
                "backlog_count": 0,
                "skipped_count": 0,
                "published_observation": False,
                "published_gimbal_command": False,
                "look_at_world_m": None,
                "geo_reject_reason": None,
                "recovered_from_lost": False,
                "phase": "measurement",
                "capture_monotonic_s": None,
                "measurement_elapsed_s": None,
            }
        )
        harness.session.loop.state = "ERROR_REINIT_REQUIRED"
        harness.session.loop.terminal = True
        return frame_id

    def test_an_unexpected_terminal_event_is_labelled_and_ends_the_segment(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        track_id = harness.session.track_id
        before = len(harness.receipts())
        self._force_terminal_record(
            harness, event="REANCHOR_FAIL_CLOSED", reason="detector_fail_closed"
        )
        harness.tick(1)

        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        # 兜底原因仍是既有闭集成员，不是新枚举。
        self.assertEqual(harness.session.reason, "metadata_invalid")
        self.assertIn(harness.session.reason, bridge.STATE_REASONS)
        marked = [
            row for row in harness.journal() if row["kind"] == "unexpected_segment_end"
        ]
        self.assertEqual(len(marked), 1)
        self.assertEqual(marked[0]["event"], "REANCHOR_FAIL_CLOSED")
        self.assertEqual(marked[0]["reason"], "detector_fail_closed")
        self.assertNotIn("unexpected_segment_end", bridge.STATE_REASONS)

        state = bridge.read_tracker_state(harness.runtime)["tracker_state"]
        self.assertFalse(state["publishing"])
        self.assertEqual(
            [row["track_id"] for row in harness.session.retired_track_ids], [track_id]
        )
        self.assertEqual(len(harness.receipts()), before)

    def test_a_known_terminal_reason_is_never_replaced_by_the_fallback(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        harness.publish(3, tick=False)
        harness.frame_paths(2)[0].unlink()
        harness.tick(1)
        self.assertEqual(harness.session.reason, "frame_gap")
        self.assertEqual(
            [row for row in harness.journal() if row["kind"] == "unexpected_segment_end"],
            [],
        )
        self.assertEqual(len(harness.session.retired_track_ids), 1)

    def test_an_unmapped_invalid_clock_event_also_gets_the_diagnostic(self) -> None:
        """未启用子系统的事件不被静默吸收成已定义原因（AC-4 修订 2）。"""
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        self._force_terminal_record(
            harness, event="INVALID_CLOCK", reason="frame 7 capture_monotonic_s must be numeric"
        )
        harness.tick(1)
        self.assertEqual(harness.session.reason, "metadata_invalid")
        marked = [
            row for row in harness.journal() if row["kind"] == "unexpected_segment_end"
        ]
        self.assertEqual(len(marked), 1)
        self.assertEqual(marked[0]["event"], "INVALID_CLOCK")
        self.assertIn("capture_monotonic_s", marked[0]["reason"])
class ConfirmationTests(unittest.TestCase):
    def test_unique_still_needs_a_confirmation(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        self.assertIsNone(harness.session.loop)
        self.assertIsNone(harness.bridge_files()["tracking_observation.json"])
        harness.confirm(0)
        self.assertEqual(harness.session.state, "TRACKING")

    def test_token_epoch_and_index_validation(self) -> None:
        harness = Harness(self, responses=[raw(AMBIGUOUS)], tracker_results=[tracking()])
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        before = harness.session.candidates
        receipt = harness.request("confirm", candidate_index=0, token="wrong")
        self.assertEqual(receipt["outcome"], "REQUEST_INVALID")
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        self.assertEqual(harness.session.candidates, before)
        receipt = harness.request(
            "confirm", candidate_index=9, token=harness.session.candidate_result_id
        )
        self.assertEqual(receipt["outcome"], "REQUEST_INVALID")
        self.assertEqual(harness.session.candidates, before)

    def test_preview_indexes_match_the_candidates(self) -> None:
        harness = Harness(self, responses=[raw(AMBIGUOUS)], tracker_results=[tracking()])
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        result = harness.results()[-1]
        self.assertEqual(len(result["candidates"]), 2)
        self.assertEqual([c["index"] for c in result["candidates"]], [0, 1])
        self.assertIsNotNone(result["preview_path"])
        preview = Path(result["preview_path"])
        self.assertTrue(preview.is_file())
        sidecar = json.loads(preview.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(sidecar["indices"], [0, 1])

    def test_reject_discards_the_candidates(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        receipt = harness.request("reject", token=harness.session.candidate_result_id)
        self.assertEqual(receipt["outcome"], "APPLIED")
        self.assertEqual(harness.session.state, "IDLE")
        self.assertEqual(harness.session.candidates, ())
        self.assertIsNone(harness.session.loop)


# --- AC-6：有界重试与歧义 --------------------------------------------------

    # --- AC-5 修订 1（P-A-5）---

    def test_confirm_is_refused_when_the_preview_was_not_generated(self) -> None:
        """缺依赖可以记 null，但此时确认必须 `REQUEST_INVALID`、什么都不动。

        这条用**注入的失败渲染器**驱动，不挂 `skipUnless(Pillow)`：否则在停点那一跑
        的系统解释器上它会被跳过，等于没补。
        """

        def failing_preview(source, destination, candidates, tracker_box=None):
            raise PreviewUnavailable("pillow is not installed")

        harness = Harness(
            self,
            responses=[raw(AMBIGUOUS)],
            tracker_results=[tracking()],
            preview=failing_preview,
        )
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        result = harness.results()[-1]
        self.assertIsNone(result["preview_path"])
        self.assertEqual(len(result["candidates"]), 2)

        epoch = harness.session.epoch
        candidates = harness.session.candidates
        segment_index = harness.session.segment_index
        receipt = harness.confirm(0)

        self.assertEqual(receipt["outcome"], "REQUEST_INVALID")
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        self.assertEqual(harness.session.epoch, epoch)
        self.assertEqual(harness.session.candidates, candidates)
        self.assertEqual(harness.session.segment_index, segment_index)
        self.assertIsNone(harness.session.loop)
        harness.assert_no_bridge_writes()
        unavailable = [
            row for row in harness.journal() if row["kind"] == "preview_unavailable"
        ]
        self.assertTrue(unavailable)

    def test_a_generated_preview_lets_the_confirmation_through(self) -> None:
        harness = Harness(self, responses=[raw(AMBIGUOUS)], tracker_results=[tracking()])
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        self.assertIsNotNone(harness.session.candidate_preview_path)
        self.assertEqual(harness.confirm(1)["outcome"], "APPLIED")
        self.assertEqual(harness.session.state, "TRACKING")

    def test_a_failed_confirmation_keeps_the_original_query_identity(self) -> None:
        """AC-6 修订 1：确认失败的结果沿用原查询身份，不另铸幽灵 `query_id`。"""
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        presented = harness.results()[-1]
        harness.clock.advance(T_CONF_S + 1.0)
        harness.confirm(0)
        rejected = harness.results()[-1]
        self.assertEqual(rejected["status"], "stale_rejected")
        self.assertEqual(rejected["query_id"], presented["query_id"])
        self.assertEqual(rejected["query_unix_s"], presented["query_unix_s"])
        self.assertEqual(rejected["frame_id"], presented["frame_id"])
        self.assertEqual(rejected["frame_sha256"], presented["frame_sha256"])

    def test_a_render_failure_is_refused_the_same_way_as_a_missing_dependency(self) -> None:
        def broken_preview(source, destination, candidates, tracker_box=None):
            raise OSError("disk full while writing the preview")

        harness = Harness(
            self,
            responses=[raw(UNIQUE)],
            tracker_results=[tracking()],
            preview=broken_preview,
        )
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        self.assertIsNone(harness.results()[-1]["preview_path"])
        self.assertEqual(harness.confirm(0)["outcome"], "REQUEST_INVALID")
        self.assertIsNone(harness.session.loop)
        harness.assert_no_bridge_writes()
        diagnostics = [
            row for row in harness.journal() if row["kind"] == "preview_unavailable"
        ]
        self.assertEqual(diagnostics[-1]["source"], "render_failed")
        self.assertIn("OSError", diagnostics[-1]["detail"])

    def test_the_designate_preview_is_bound_to_the_ring_copy(self) -> None:
        harness = Harness(self, responses=[raw(AMBIGUOUS)], tracker_results=[tracking()])
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        source, destination, indices, has_tracker = harness.preview.calls[-1]
        self.assertEqual(indices, [0, 1])
        self.assertFalse(has_tracker)
        self.assertEqual(source.parent, harness.session.ring.directory)
        self.assertEqual(source.read_bytes(), harness.frame_paths(0)[0].read_bytes())
class BoundedRetryTests(unittest.TestCase):
    def test_none_retries_until_the_limit(self) -> None:
        harness = Harness(self, responses=[raw(NONE), raw(NONE), raw(NONE)])
        harness.publish(1)
        harness.ask()
        for _ in range(4):
            harness.publish(1)
            harness.tick(2)
        results = [row for row in harness.results() if row["purpose"] == "designate"]
        self.assertEqual([row["attempt"] for row in results], [1, 2, 3])
        self.assertEqual(results[-1]["status"], "retry_exhausted")
        self.assertEqual(results[-1]["last_status"], "none")
        self.assertEqual(harness.session.state, "IDLE")  # 没有过段
        frame_ids = [row["frame_id"] for row in results]
        self.assertEqual(frame_ids, sorted(frame_ids))
        self.assertEqual(len(set(frame_ids)), len(frame_ids))

    def test_no_new_frame_attempt_has_null_frame_fields(self) -> None:
        harness = Harness(self, responses=[raw(NONE), raw(NONE), raw(NONE)])
        harness.publish(1)
        harness.ask()
        harness.tick(1)
        # 不再发布新帧：等满 T_ret 之后记 `no_new_frame` 并计次。
        harness.clock.advance(harness.receipt.t_ret_s + 0.2)
        harness.tick(2)
        results = [row for row in harness.results() if row["purpose"] == "designate"]
        no_frame = [row for row in results if row["status"] == "no_new_frame"]
        self.assertTrue(no_frame)
        self.assertIsNone(no_frame[0]["frame_id"])
        self.assertIsNone(no_frame[0]["frames_late"])
        self.assertGreaterEqual(no_frame[0]["attempt"], 2)

    def test_retry_exhausted_after_a_segment_goes_to_reinit_required(self) -> None:
        harness = Harness(
            self,
            responses=[raw(UNIQUE), raw(NONE), raw(NONE), raw(NONE)],
            tracker_results=[tracking()],
        )
        harness.seed()
        harness.request("release", token=harness.session.track_id)
        harness.publish(1)
        harness.request("respecify")
        for _ in range(4):
            harness.publish(1)
            harness.tick(2)
        self.assertEqual(harness.session.state, "REINIT_REQUIRED")
        self.assertEqual(harness.session.reason, "retry_exhausted")

    def test_parse_failure_counts_as_an_attempt(self) -> None:
        harness = Harness(self, responses=[raw(BROKEN), raw(BROKEN), raw(BROKEN)])
        harness.publish(1)
        harness.ask()
        for _ in range(4):
            harness.publish(1)
            harness.tick(2)
        results = [row for row in harness.results() if row["purpose"] == "designate"]
        self.assertEqual(results[0]["status"], "parse_failed")
        self.assertEqual(results[0]["parse_error"], "JSON_ERROR")
        self.assertEqual(results[-1]["status"], "retry_exhausted")

    def test_backend_error_counts_as_an_attempt(self) -> None:
        harness = Harness(
            self,
            responses=[SelectorError("replay_miss", "no row"), raw(UNIQUE)],
            tracker_results=[tracking()],
        )
        harness.publish(1)
        harness.ask()
        harness.tick(1)
        first = harness.results()[0]
        self.assertEqual(first["status"], "backend_error")
        self.assertEqual(first["reject_reason"], "replay_miss")
        harness.publish(1)
        harness.tick(2)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        self.assertEqual(harness.session.attempt, 2)

    def test_new_ask_resets_the_attempt_counter(self) -> None:
        harness = Harness(self, responses=[raw(NONE), raw(UNIQUE)])
        harness.publish(1)
        harness.ask()
        harness.tick(1)
        self.assertEqual(harness.session.attempt, 2)
        harness.publish(1)
        harness.ask("the taxi", ticks=1)
        self.assertEqual(harness.session.attempt, 1)

    # --- AC-6 修订 1（P-A-4）---

    def test_pre_frame_failures_increment_attempts_without_raising_the_frame_floor(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)] * 4)
        harness.publish(1)
        image, metadata = harness.frame_paths(0)
        image.unlink()
        harness.ask()
        harness.tick(3)
        results = [
            row
            for row in harness.results()
            if row["purpose"] == "designate" and row["status"] == "stale_rejected"
        ]
        self.assertGreaterEqual(len(results), 2)
        for row in results:
            self.assertEqual(row["reject_reason"], "bundle_missing")
            # 未建立合法快照 → 四个帧绑定字段全 null，但 query_unix_s 仍记尝试时刻。
            self.assertIsNone(row["frame_id"])
            self.assertIsNone(row["frame_sha256"])
            self.assertIsNone(row["capture_monotonic_s"])
            self.assertIsNone(row["capture_unix_s"])
            self.assertIsNone(row["frames_late"])
            self.assertIsNotNone(row["query_unix_s"])
        attempts = [row["attempt"] for row in results]
        self.assertEqual(attempts, sorted(set(attempts)))
        query_ids = [row["query_id"] for row in results]
        self.assertEqual(len(set(query_ids)), len(query_ids))
        for query_id in query_ids:
            self.assertTrue(query_id.startswith("s1-q"))
        # 严格帧递增只约束取得帧的尝试：前置失败不抬高下界。
        self.assertIsNone(harness.session._retry_min_frame_id)
        self.assertEqual(harness.session.worker.calls_started, 0)

    def test_retry_exhausted_after_pre_frame_failures_records_the_last_reason(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)] * 4)
        harness.publish(1)
        harness.frame_paths(0)[0].unlink()
        harness.ask()
        harness.tick(4)
        results = [row for row in harness.results() if row["purpose"] == "designate"]
        self.assertEqual(results[-1]["status"], "retry_exhausted")
        self.assertEqual(results[-1]["last_status"], "stale_rejected")
        self.assertEqual(results[-1]["last_reject_reason"], "bundle_missing")
        self.assertEqual(harness.session.state, "IDLE")
class AmbiguousTests(unittest.TestCase):
    def test_all_candidates_are_presented_and_one_is_chosen(self) -> None:
        harness = Harness(self, responses=[raw(AMBIGUOUS)], tracker_results=[tracking()])
        harness.publish(1)
        harness.ask()
        harness.tick(2)
        result = harness.results()[-1]
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(len(result["candidates"]), 2)
        harness.confirm(1)
        self.assertEqual(harness.session.state, "TRACKING")
        tracker_boxes = harness.session.loop.tracker.init_calls
        self.assertEqual(len(tracker_boxes), 1)
        self.assertAlmostEqual(tracker_boxes[0][0], 0.6, places=6)


# --- AC-7：重新指定与谱系 --------------------------------------------------


class RespecifyTests(unittest.TestCase):
    def test_respecify_from_lost_opens_a_new_segment(self) -> None:
        harness = Harness(
            self,
            responses=[raw(UNIQUE), raw(UNIQUE)],
            tracker_results=[tracking(), tracking()],
        )
        harness.seed()
        first_track = harness.session.track_id
        harness.request("release", token=first_track)
        self.assertEqual(harness.session.state, "LOST")
        harness.publish(1)
        harness.request("respecify")
        harness.tick(2)
        harness.confirm(0)
        self.assertEqual(harness.session.state, "TRACKING")
        self.assertNotEqual(harness.session.track_id, first_track)
        retired = harness.session.retired_track_ids
        self.assertEqual(len(retired), 1)
        self.assertEqual(retired[0]["track_id"], first_track)
        self.assertEqual(retired[0]["retired_reason"], "operator_release")

    def test_each_path_retires_exactly_once(self) -> None:
        for path in ("gap", "release", "confirm_lost"):
            with self.subTest(path=path):
                harness = Harness(
                    self, responses=[raw(UNIQUE)], tracker_results=[tracking()]
                )
                harness.seed()
                track_id = harness.session.track_id
                if path == "gap":
                    harness.publish(3, tick=False)
                    harness.frame_paths(2)[0].unlink()
                    harness.tick(2)
                elif path == "release":
                    harness.request("release", token=track_id)
                    harness.tick(2)
                else:
                    harness.session._raise_suspect("lost", "verify_none")
                    harness.request("confirm_lost", token=harness.session.suspect_id)
                    harness.tick(2)
                retired = harness.session.retired_track_ids
                self.assertEqual([row["track_id"] for row in retired], [track_id])

    def test_respecify_is_refused_while_tracking(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        receipt = harness.request("respecify")
        self.assertEqual(receipt["outcome"], "REQUEST_INVALID")
        self.assertEqual(harness.session.state, "TRACKING")

    def test_respecify_reuses_the_last_instruction(self) -> None:
        harness = Harness(
            self, responses=[raw(UNIQUE), raw(UNIQUE)], tracker_results=[tracking(), tracking()]
        )
        harness.seed("the taxi")
        harness.request("release", token=harness.session.track_id)
        harness.publish(1)
        harness.request("respecify")
        harness.tick(1)
        self.assertEqual(harness.session.current_instruction.surface, "the taxi")

    def test_respecify_without_anything_to_reuse_is_invalid(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)])
        receipt = harness.request("respecify")
        self.assertEqual(receipt["outcome"], "REQUEST_INVALID")
        self.assertEqual(harness.session.state, "IDLE")

    def test_respecify_from_suspected_retires_then_queries(self) -> None:
        harness = Harness(
            self,
            responses=[raw(UNIQUE), raw(UNIQUE)],
            tracker_results=[tracking(), tracking()],
        )
        harness.seed()
        track_id = harness.session.track_id
        harness.session._raise_suspect("drift", "verify_drift")
        harness.publish(1)
        harness.request("respecify", ticks=1)
        self.assertEqual(harness.session.state, "QUERYING")
        self.assertEqual(
            [row["track_id"] for row in harness.session.retired_track_ids], [track_id]
        )
        self.assertEqual(
            harness.session.retired_track_ids[0]["retired_reason"], "verify_drift"
        )


# --- AC-16：核验语义 -------------------------------------------------------


class VerifyTests(unittest.TestCase):
    def _harness(self, responses, tracker=None, verify_interval_s: float = T_V_S) -> Harness:
        return Harness(
            self,
            responses=responses,
            tracker_results=tracker or [tracking()],
            verify_interval_s=verify_interval_s,
        )

    def _verify_now(self, harness: Harness) -> dict:
        harness.request("verify")
        harness.tick(2)
        verifies = [row for row in harness.results() if row["purpose"] == "verify"]
        return verifies[-1]

    def test_consistent_and_drift(self) -> None:
        harness = self._harness([raw(UNIQUE), raw(UNIQUE), raw(UNIQUE_FAR)])
        harness.seed()
        harness.publish(1)
        result = self._verify_now(harness)
        self.assertEqual(result["verify"]["verdict"], "consistent")
        self.assertEqual(result["verify"]["consecutive_alert"], 0)
        harness.clock.advance(4.0)
        harness.publish(1)
        result = self._verify_now(harness)
        self.assertEqual(result["verify"]["verdict"], "drift")
        self.assertEqual(result["verify"]["consecutive_alert"], 1)
        self.assertEqual(harness.session.state, "TRACKING")

    def test_two_consecutive_alerts_raise_a_suspect(self) -> None:
        harness = self._harness([raw(UNIQUE), raw(NONE), raw(UNIQUE_FAR)])
        harness.seed()
        harness.publish(1)
        self.assertEqual(self._verify_now(harness)["verify"]["verdict"], "none")
        harness.clock.advance(4.0)
        harness.publish(1)
        result = self._verify_now(harness)
        self.assertEqual(result["verify"]["verdict"], "drift")
        # none/drift 交替同样累计。
        self.assertEqual(result["verify"]["consecutive_alert"], 2)
        self.assertEqual(harness.session.state, "SUSPECTED")
        self.assertEqual(harness.session.suspect_kind, "drift")

    def test_ambiguous_suspects_immediately(self) -> None:
        harness = self._harness([raw(UNIQUE), raw(AMBIGUOUS)])
        harness.seed()
        harness.publish(1)
        result = self._verify_now(harness)
        self.assertEqual(result["verify"]["verdict"], "ambiguous")
        self.assertEqual(harness.session.state, "SUSPECTED")
        self.assertEqual(harness.session.suspect_kind, "ambiguous")

    def test_same_frame_is_not_verified_twice(self) -> None:
        harness = self._harness([raw(UNIQUE), raw(UNIQUE), raw(UNIQUE)])
        harness.seed()
        harness.publish(1)
        self._verify_now(harness)
        before = len([row for row in harness.results() if row["purpose"] == "verify"])
        harness.clock.advance(4.0)
        harness.request("verify")
        harness.tick(2)
        after = len([row for row in harness.results() if row["purpose"] == "verify"])
        self.assertEqual(before, after)
        skips = [
            row
            for row in harness.journal()
            if row["kind"] == "verify_skipped" and row["reason"] == "same_frame"
        ]
        self.assertTrue(skips)

    def test_missing_tracker_box_skips(self) -> None:
        results = [TrackerResult.lost("tracker_reported_failure")] + tracking()
        harness = self._harness([raw(UNIQUE), raw(UNIQUE)], tracker=[results])
        harness.seed()
        harness.publish(1)
        harness.request("verify")
        harness.tick(2)
        skips = [
            row
            for row in harness.journal()
            if row["kind"] == "verify_skipped" and row["reason"] == "no_tracker_box"
        ]
        self.assertTrue(skips)

    def test_verify_never_publishes_and_never_initializes(self) -> None:
        harness = self._harness([raw(UNIQUE), raw(NONE)])
        harness.seed()
        harness.publish(1)
        receipts_before = len(harness.receipts())
        init_calls = len(harness.session.loop.tracker.init_calls)
        self._verify_now(harness)
        self.assertEqual(len(harness.receipts()), receipts_before)
        self.assertEqual(len(harness.session.loop.tracker.init_calls), init_calls)

    def test_dismiss_drops_late_replies(self) -> None:
        harness = self._harness([raw(UNIQUE), raw(NONE)])
        harness.seed()
        harness.session._raise_suspect("lost", "verify_none")
        harness.request("dismiss", token=harness.session.suspect_id)
        self.assertEqual(harness.session.state, "TRACKING")
        stale_epoch = harness.session.verify_epoch - 1
        job = QueryJob(
            query_id="s1-qX",
            purpose="verify",
            epoch=harness.session.epoch,
            segment_index=harness.session.segment_index,
            verify_epoch=stale_epoch,
            attempt=1,
            instruction=bridge.parse_instruction("the red car"),
            frame=harness.session.candidate_frame
            or _any_frame(harness),
            submitted_monotonic_s=harness.clock.monotonic(),
            query_unix_s=harness.clock.unix(),
            latest_at_query=0,
            tracker_box=TRACKER_BOX,
        )
        from controller.language_loop import QueryOutcome

        harness.session._handle_verify_outcome(
            QueryOutcome(job=job, raw=raw(NONE), error=None,
                         finished_monotonic_s=harness.clock.monotonic(), latency_ms=1.0)
        )
        ignored = [row for row in harness.results() if row.get("status") == "IGNORED_STALE_EPOCH"]
        self.assertTrue(ignored)
        self.assertEqual(harness.session.state, "TRACKING")
        self.assertEqual(harness.session.consecutive_alert, 0)

    def test_trigger_rate_limit(self) -> None:
        harness = self._harness([raw(UNIQUE), raw(UNIQUE), raw(UNIQUE)])
        harness.seed()
        harness.publish(1)
        harness.request("verify")
        harness.tick(2)
        count = len([row for row in harness.results() if row["purpose"] == "verify"])
        harness.publish(1)
        harness.request("verify")  # 3 s 内的同源触发
        harness.tick(2)
        self.assertEqual(
            len([row for row in harness.results() if row["purpose"] == "verify"]), count
        )

    def test_due_schedules_the_next_verification(self) -> None:
        harness = self._harness(
            [raw(UNIQUE), raw(UNIQUE), raw(UNIQUE)], verify_interval_s=1.0
        )
        harness.seed()
        harness.publish(1)
        harness.clock.advance(1.5)
        harness.tick(3)
        verifies = [row for row in harness.results() if row["purpose"] == "verify"]
        self.assertTrue(verifies)
        state = bridge.read_tracker_state(harness.runtime)["tracker_state"]
        self.assertIsNotNone(state["verification"]["next_due_unix_s"])

    # --- AC-16 修订 1（P-A-7）与 AC-6 修订 1 的核验半边（P-A-4）---

    def _seeded_for_verify(self, responses):
        harness = self._harness(responses)
        harness.seed()
        harness.publish(1)
        return harness

    def _submit_verify(self, harness: Harness) -> None:
        """只把核验查询发出去，不轮询回包（回包留给调用方控制的那一 tick）。"""
        harness.request("verify", ticks=1)

    @staticmethod
    def _verify_rows(harness: Harness) -> list[dict]:
        """真正的核验结果包；`IGNORED_STALE_EPOCH` 只是丢弃记录，不算结果行。"""
        return [
            row
            for row in harness.results()
            if row.get("purpose") == "verify"
            and row.get("status") != "IGNORED_STALE_EPOCH"
        ]

    def _last_verify(self, harness: Harness) -> dict:
        verifies = self._verify_rows(harness)
        self.assertTrue(verifies, "没有产生核验结果行")
        return verifies[-1]

    def _assert_inconclusive(self, result, *, status, reject_reason, reason):
        self.assertEqual(result["verify"]["verdict"], "inconclusive")
        self.assertEqual(result["verify"]["inconclusive_reason"], reason)
        self.assertEqual(result["status"], status)
        self.assertEqual(result["reject_reason"], reject_reason)
        # verdict 字面只能是五值之一，不得写成 `inconclusive(reason)`。
        self.assertIn(result["verify"]["verdict"], bridge.VERIFY_VERDICTS)

    def test_inconclusive_stale_when_the_return_deadline_passed(self) -> None:
        harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
        self._submit_verify(harness)
        harness.clock.advance(harness.receipt.t_ret_s + 0.1)
        harness.tick(1)
        self._assert_inconclusive(
            self._last_verify(harness),
            status="stale_rejected",
            reject_reason="wall_deadline_exceeded",
            reason="stale",
        )

    def test_inconclusive_stale_when_too_many_frames_arrived(self) -> None:
        harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
        self._submit_verify(harness)
        harness.publish(harness.receipt.k_ret + 1, tick=False)
        harness.tick(1)
        self._assert_inconclusive(
            self._last_verify(harness),
            status="stale_rejected",
            reject_reason="frames_late_exceeded",
            reason="stale",
        )

    def test_inconclusive_frame_identity_on_a_rollback(self) -> None:
        harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
        self._submit_verify(harness)
        harness.publisher.publish_pointer(0)
        harness.tick(1)
        self._assert_inconclusive(
            self._last_verify(harness),
            status="stale_rejected",
            reject_reason="negative_frame_delta",
            reason="frame_identity",
        )

    def test_inconclusive_frame_identity_when_the_paired_bytes_changed(self) -> None:
        harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
        paired = harness.session.processed[-1].frame_id
        self._submit_verify(harness)
        harness.frame_paths(paired)[0].write_bytes(b"swapped-after-the-query")
        harness.tick(1)
        self._assert_inconclusive(
            self._last_verify(harness),
            status="stale_rejected",
            reject_reason="image_identity_changed",
            reason="frame_identity",
        )

    def test_inconclusive_backend_error_keeps_the_specific_reason(self) -> None:
        harness = self._seeded_for_verify(
            [raw(UNIQUE), SelectorError("replay_miss", "no row for this key")]
        )
        self._submit_verify(harness)
        harness.tick(1)
        self._assert_inconclusive(
            self._last_verify(harness),
            status="backend_error",
            reject_reason="replay_miss",
            reason="backend_error",
        )

    def test_inconclusive_parse_failed_carries_no_reject_reason(self) -> None:
        harness = self._seeded_for_verify([raw(UNIQUE), raw(BROKEN)])
        self._submit_verify(harness)
        harness.tick(1)
        self._assert_inconclusive(
            self._last_verify(harness),
            status="parse_failed",
            reject_reason=None,
            reason="parse_failed",
        )

    def test_inconclusive_changes_no_counter_and_writes_nothing(self) -> None:
        harness = self._seeded_for_verify(
            [raw(UNIQUE), SelectorError("replay_miss", "no row")]
        )
        alerts = harness.session.consecutive_alert
        receipts = len(harness.receipts())
        inits = len(harness.session.loop.tracker.init_calls)
        files = harness.bridge_files()
        self._submit_verify(harness)
        harness.tick(1)
        self.assertEqual(self._last_verify(harness)["verify"]["verdict"], "inconclusive")
        self.assertEqual(harness.session.consecutive_alert, alerts)
        self.assertEqual(len(harness.receipts()), receipts)
        self.assertEqual(len(harness.session.loop.tracker.init_calls), inits)
        self.assertEqual(harness.bridge_files(), files)
        self.assertEqual(harness.session.state, "TRACKING")

    def test_stale_replies_are_dropped_on_each_of_the_three_keys(self) -> None:
        for key in ("epoch", "segment_index", "verify_epoch"):
            with self.subTest(key=key):
                harness = self._seeded_for_verify([raw(UNIQUE), raw(NONE)])
                before = len(self._verify_rows(harness))
                alerts = harness.session.consecutive_alert
                job = QueryJob(
                    query_id=f"s1-qX-{key}",
                    purpose="verify",
                    epoch=harness.session.epoch - (1 if key == "epoch" else 0),
                    segment_index=(
                        harness.session.segment_index + (1 if key == "segment_index" else 0)
                    ),
                    verify_epoch=(
                        harness.session.verify_epoch - (1 if key == "verify_epoch" else 0)
                    ),
                    attempt=1,
                    instruction=bridge.parse_instruction("the red car"),
                    frame=_any_frame(harness),
                    submitted_monotonic_s=harness.clock.monotonic(),
                    query_unix_s=harness.clock.unix(),
                    latest_at_query=0,
                    tracker_box=TRACKER_BOX,
                )
                harness.session._handle_verify_outcome(
                    QueryOutcome(
                        job=job,
                        raw=raw(NONE),
                        error=None,
                        finished_monotonic_s=harness.clock.monotonic(),
                        latency_ms=1.0,
                    )
                )
                ignored = [
                    row for row in harness.results()
                    if row.get("status") == "IGNORED_STALE_EPOCH"
                ]
                self.assertTrue(ignored)
                self.assertEqual(len(self._verify_rows(harness)), before)
                self.assertEqual(harness.session.consecutive_alert, alerts)

    def test_tracking_lag_skips_before_any_model_call(self) -> None:
        """滞后跳过发生在发起之前：不占 `query_id`、不产生结果行、不调模型。"""
        harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
        calls = len(harness.adapter.calls)
        sequence = harness.session._query_sequence
        rows = len(self._verify_rows(harness))
        harness.publish(harness.receipt.k_pub + 2, tick=False)
        harness.clock.advance(harness.session.config.verify_interval_s + 0.1)
        # 直接走周期发起：tick() 会先把新帧处理掉，配对帧就不再滞后了。
        harness.session._maybe_verify()
        skips = [
            row for row in harness.journal()
            if row["kind"] == "verify_skipped" and row["reason"] == "tracking_lag"
        ]
        self.assertTrue(skips)
        self.assertEqual(len(harness.adapter.calls), calls)
        self.assertEqual(harness.session._query_sequence, sequence)
        self.assertEqual(len(self._verify_rows(harness)), rows)

    def test_missing_box_and_same_frame_skips_make_no_model_call(self) -> None:
        results = [TrackerResult.lost("tracker_reported_failure")] + tracking()
        harness = self._harness([raw(UNIQUE), raw(UNIQUE)], tracker=[results])
        harness.seed()
        harness.publish(1)
        calls = len(harness.adapter.calls)
        sequence = harness.session._query_sequence
        harness.request("verify")
        harness.tick(2)
        skips = [
            row for row in harness.journal()
            if row["kind"] == "verify_skipped" and row["reason"] == "no_tracker_box"
        ]
        self.assertTrue(skips)
        self.assertEqual(len(harness.adapter.calls), calls)
        self.assertEqual(harness.session._query_sequence, sequence)

    def test_a_completed_verification_renders_the_paired_tracker_box(self) -> None:
        harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
        result = self._verify_now(harness)
        self.assertEqual(result["verify"]["verdict"], "consistent")
        self.assertIsNotNone(result["preview_path"])
        preview = Path(result["preview_path"])
        self.assertTrue(preview.is_file())
        self.assertEqual(
            preview.parent, harness.session.previews_dir
        )
        self.assertEqual(
            preview.name, f"{result['frame_id']}-{result['query_id']}.png"
        )
        sidecar = json.loads(preview.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(sidecar["indices"], [0])
        self.assertTrue(sidecar["tracker_box"])
        self.assertTrue(harness.preview.calls[-1][2])

    def test_inconclusive_never_clears_an_existing_suspect(self) -> None:
        harness = self._seeded_for_verify(
            [raw(UNIQUE), SelectorError("replay_miss", "no row")]
        )
        harness.session._raise_suspect("tracker_failure", "tracker_failure")
        suspect_id = harness.session.suspect_id
        self._submit_verify(harness)
        harness.tick(1)
        self.assertEqual(self._last_verify(harness)["verify"]["verdict"], "inconclusive")
        self.assertEqual(harness.session.state, "SUSPECTED")
        self.assertEqual(harness.session.suspect_id, suspect_id)
        self.assertEqual(harness.session.suspect_kind, "tracker_failure")

    def test_inconclusive_frame_identity_on_a_missing_or_invalid_bundle(self) -> None:
        for reason in ("bundle_missing", "metadata_invalid"):
            with self.subTest(reason=reason):
                harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
                paired = harness.session.processed[-1].frame_id
                self._submit_verify(harness)
                image, metadata = harness.frame_paths(paired)
                if reason == "bundle_missing":
                    metadata.unlink()
                else:
                    document = json.loads(metadata.read_text(encoding="utf-8"))
                    document["capture_monotonic_clock_id"] = "wall-clock/v9"
                    metadata.write_text(json.dumps(document), encoding="utf-8")
                harness.tick(1)
                self._assert_inconclusive(
                    self._last_verify(harness),
                    status="stale_rejected",
                    reject_reason=reason,
                    reason="frame_identity",
                )

    def test_the_verification_preview_is_bound_to_the_ring_copy(self) -> None:
        harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
        result = self._verify_now(harness)
        source, destination, indices, has_tracker = harness.preview.calls[-1]
        self.assertTrue(has_tracker)
        self.assertEqual(indices, [0])
        # 源帧取的是帧环里的加载时副本，不是 runtime/frames 里的原件。
        self.assertEqual(source.parent, harness.session.ring.directory)
        self.assertNotEqual(source.parent, harness.runtime / "frames")
        self.assertEqual(
            source.read_bytes(), harness.frame_paths(result["frame_id"])[0].read_bytes()
        )

    # --- AC-16 修订 2（P-B-1）：发起前跳过只进会话 JSONL ---

    def _skip_footprint(self, harness: Harness) -> tuple:
        """发起前跳过之后**整个可观察状态**都不应变，而不只是五个计数。"""
        session = harness.session
        result_bridge = harness.runtime / bridge.RESULT_FILE
        return (
            len(harness.adapter.calls),
            session._query_sequence,
            session._result_sequence,
            len(self._verify_rows(harness)),
            session.consecutive_alert,
            session.alert_kind,
            session.worker.calls_started,
            session.last_verified_frame_id,
            session.last_verdict,
            session.state,
            session.reason,
            session.suspect_kind,
            session.suspect_id,
            session._suspect_sequence,
            session.verify_epoch,
            session.next_due_unix_s,
            result_bridge.read_bytes() if result_bridge.is_file() else None,
        )

    def test_the_three_pre_dispatch_skips_leave_no_result_and_no_query_id(self) -> None:
        """三种跳过：只写 `verify_skipped` 日志，不产结果、不占号、不调模型、不改计数。"""
        for reason in bridge.VERIFY_SKIP_REASONS:
            with self.subTest(reason=reason):
                if reason == "no_tracker_box":
                    results = [TrackerResult.lost("tracker_reported_failure")] + tracking()
                    harness = self._harness([raw(UNIQUE), raw(UNIQUE)], tracker=[results])
                    harness.seed()
                    harness.publish(1)
                else:
                    harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
                if reason == "same_frame":
                    self._verify_now(harness)  # 先核验一次，配对帧就不再前进
                if reason == "tracking_lag":
                    harness.publish(harness.receipt.k_pub + 2, tick=False)
                before = self._skip_footprint(harness)
                # 直接走发起前那一步：不 tick、不推时钟，免得 `frame_stall`
                # 之类与本条无关的状态变化混进脚印。
                harness.session._trigger_last.clear()
                harness.session._request_verification("operator")
                skips = [
                    row
                    for row in harness.journal()
                    if row["kind"] == "verify_skipped" and row["reason"] == reason
                ]
                self.assertTrue(skips, f"没有记下 {reason} 跳过")
                self.assertEqual(self._skip_footprint(harness), before)

    def test_the_skip_reasons_are_not_result_packet_reasons(self) -> None:
        """AC-16 修订 2：三个成员已移出结果包闭集，剩余恰四个。"""
        self.assertEqual(
            set(bridge.INCONCLUSIVE_REASONS),
            {"stale", "frame_identity", "parse_failed", "backend_error"},
        )
        self.assertEqual(
            set(bridge.VERIFY_SKIP_REASONS) & set(bridge.INCONCLUSIVE_REASONS), set()
        )

    def test_an_untrustworthy_pairing_frame_is_not_mislabelled_as_one_of_the_three(self) -> None:
        """配对帧身份不可信是第四种发起前条件；不拿那三个名字错标（AC-16 修订 3）。"""
        harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
        paired = harness.session.processed[-1].frame_id
        harness.frame_paths(paired)[0].write_bytes(b"swapped-before-the-query")
        before = self._skip_footprint(harness)
        harness.request("verify")
        harness.tick(2)
        blocked = [
            row for row in harness.journal() if row["kind"] == "verify_pairing_unavailable"
        ]
        self.assertTrue(blocked)
        self.assertEqual(blocked[-1]["reason"], "image_identity_changed")
        self.assertEqual(
            [row for row in harness.journal() if row["kind"] == "verify_skipped"], []
        )
        self.assertEqual(self._skip_footprint(harness), before)

    def test_record_skip_refuses_a_reason_outside_the_skip_closed_set(self) -> None:
        """`verify_skipped` 的原因闭集恰是三个成员；结果包的四个原因不得混入。"""
        harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
        before = len([row for row in harness.journal() if row["kind"] == "verify_skipped"])
        for reason in bridge.INCONCLUSIVE_REASONS:
            with self.subTest(reason=reason):
                with self.assertRaises(bridge.LanguageBridgeError):
                    harness.session._record_skip(reason, 7)
        self.assertEqual(
            len([row for row in harness.journal() if row["kind"] == "verify_skipped"]),
            before,
        )

    def test_every_pairing_unavailable_branch_keeps_its_own_reason(self) -> None:
        """AC-16 修订 3：五个成员逐条可达、各保留自己的原因并带已知 `P.frame_id`。"""
        for branch in bridge.PAIRING_UNAVAILABLE_REASONS:
            with self.subTest(branch=branch):
                harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
                paired = harness.session.processed[-1].frame_id
                self._break_pairing(harness, branch, paired)
                before = self._skip_footprint(harness)
                harness.session._request_verification("operator")
                blocked = [
                    row
                    for row in harness.journal()
                    if row["kind"] == "verify_pairing_unavailable"
                ]
                self.assertTrue(blocked)
                self.assertEqual(blocked[-1]["reason"], branch)
                self.assertEqual(blocked[-1]["frame_id"], paired)
                self.assertEqual(
                    [row for row in harness.journal() if row["kind"] == "verify_skipped"],
                    [],
                )
                self.assertEqual(self._skip_footprint(harness), before)

    def _break_pairing(self, harness: Harness, branch: str, paired: int) -> None:
        """按五值闭集逐条制造「配对帧 P 不可用」。"""
        image, metadata = harness.frame_paths(paired)
        if branch == "snapshot_missing":
            harness.session.ring._snapshots.pop(paired)
        elif branch == "image_identity_changed":
            image.write_bytes(b"swapped")
        elif branch == "bundle_missing":
            metadata.unlink()
        elif branch == "metadata_invalid":
            document = json.loads(metadata.read_text(encoding="utf-8"))
            document["capture_monotonic_clock_id"] = "wall-clock/v9"
            metadata.write_text(json.dumps(document), encoding="utf-8")
        elif branch == "latest_unreadable":
            (harness.runtime / "frames" / "latest.json").unlink()
        else:  # pragma: no cover - 闭集新增成员时立刻失败，而不是静默漏测
            raise AssertionError(f"闭集成员 {branch} 没有对应分支")

    def test_pairing_unavailable_refuses_a_reason_outside_its_closed_set(self) -> None:
        """AC-16 修订 3 的五值闭集：既不借用那三个跳过名，也不收结果包的四个原因。"""
        self.assertEqual(
            set(bridge.PAIRING_UNAVAILABLE_REASONS),
            {
                "snapshot_missing",
                "image_identity_changed",
                "bundle_missing",
                "metadata_invalid",
                "latest_unreadable",
            },
        )
        self.assertEqual(
            set(bridge.PAIRING_UNAVAILABLE_REASONS) & set(bridge.VERIFY_SKIP_REASONS),
            set(),
        )
        harness = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
        before = len(
            [
                row
                for row in harness.journal()
                if row["kind"] == "verify_pairing_unavailable"
            ]
        )
        for reason in bridge.VERIFY_SKIP_REASONS + bridge.INCONCLUSIVE_REASONS:
            with self.subTest(reason=reason):
                with self.assertRaises(bridge.LanguageBridgeError):
                    harness.session._record_pairing_unavailable(reason, 7)
        self.assertEqual(
            len(
                [
                    row
                    for row in harness.journal()
                    if row["kind"] == "verify_pairing_unavailable"
                ]
            ),
            before,
        )

    def test_the_pairing_diagnostic_leaves_the_two_numbered_paths_alone(self) -> None:
        """AC-16 修订 3 只解释**发起前**那一步：另外两条同名失败的路径一字不改。"""
        # (a) designate 的取帧前失败：仍占 `query_id`、仍产结果行（AC-6 修订 1）。
        designating = Harness(self, responses=[raw(UNIQUE)] * 4)
        designating.publish(1)
        designating.frame_paths(0)[1].unlink()
        designating.ask()
        designating.tick(2)
        rejected = [
            row
            for row in designating.results()
            if row["purpose"] == "designate" and row["status"] == "stale_rejected"
        ]
        self.assertTrue(rejected)
        self.assertEqual(rejected[0]["reject_reason"], "bundle_missing")
        self.assertTrue(rejected[0]["query_id"].startswith("s1-q"))

        # (b) 已发起的核验，返回时同名身份失败：仍是 inconclusive(frame_identity)。
        returning = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
        paired = returning.session.processed[-1].frame_id
        self._submit_verify(returning)
        returning.frame_paths(paired)[1].unlink()
        returning.tick(1)
        self._assert_inconclusive(
            self._last_verify(returning),
            status="stale_rejected",
            reject_reason="bundle_missing",
            reason="frame_identity",
        )

        # (c) 同一个名字在**发起前**出现：既不占号也不产结果行。
        pairing = self._seeded_for_verify([raw(UNIQUE), raw(UNIQUE)])
        self._break_pairing(pairing, "bundle_missing", pairing.session.processed[-1].frame_id)
        before = self._skip_footprint(pairing)
        pairing.session._request_verification("operator")
        blocked = [
            row for row in pairing.journal() if row["kind"] == "verify_pairing_unavailable"
        ]
        self.assertEqual(blocked[-1]["reason"], "bundle_missing")
        self.assertEqual(self._skip_footprint(pairing), before)
def _any_frame(harness: Harness):
    from controller.language_loop import QuerySnapshot

    snapshot = harness.session.ring.latest_snapshot()
    return QuerySnapshot(
        frame_id=snapshot.frame_id,
        image_sha256=snapshot.image_sha256,
        copy_path=snapshot.copy_path,
        capture_monotonic_s=snapshot.capture_monotonic_s,
        capture_unix_s=snapshot.capture_unix_s,
        snapshot=snapshot,
    )


# --- AC-12：诊断会话与零正式 ID --------------------------------------------


class DiagnosticSessionTests(unittest.TestCase):
    def test_diagnostic_runs_land_in_their_own_root(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        diagnostics = Path(directory.name) / "diagnostics" / "diag-demo"
        harness = Harness(
            self,
            responses=[raw(UNIQUE)],
            tracker_results=[tracking()],
            diagnostic=True,
            session_id="diag-demo",
            run_root=diagnostics,
        )
        harness.seed()
        self.assertTrue((diagnostics / "runs" / "diag-demo-seg1").is_dir())
        self.assertFalse((harness.runtime / "runs").exists())

    def test_stage_a_runs_stay_inside_the_fixture_runtime(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        self.assertTrue((harness.runtime / "runs" / "s1-seg1").is_dir())
        self.assertFalse((PROJECT_ROOT / "runtime" / "runs" / "s1-seg1").exists())

    def test_cli_refuses_the_shared_runtime_without_an_explicit_flag(self) -> None:
        from controller.language_loop import build_parser, _run_session

        parser = build_parser()
        arguments = parser.parse_args(
            [
                "run",
                "--session-id",
                "s1",
                "--session-root",
                "/tmp/does-not-matter",
                "--runtime",
                str(PROJECT_ROOT / "runtime"),
                "--k-receipt",
                "/tmp/does-not-matter.json",
                "--backend",
                "replay",
            ]
        )
        with contextlib.redirect_stderr(io.StringIO()):
            code = _run_session(arguments)
        self.assertEqual(code, 2)


# --- 预览的真实渲染（有 Pillow 时才跑） -----------------------------------

    # --- AC-12 修订 2（P-A-1）---

    def _refusal_argv(self, runtime: str, session_root: str) -> list[str]:
        return [
            "run",
            "--session-id",
            "s1",
            "--session-root",
            session_root,
            "--runtime",
            runtime,
            # 故意指向不存在的收据：守卫一旦失效，读收据就先炸，绝不会走到
            # session.start() 去写共享 runtime。
            "--k-receipt",
            str(Path(session_root) / "no-such-receipt.json"),
            "--backend",
            "replay",
        ]

    def test_shared_runtime_is_refused_through_every_path_alias(self) -> None:
        """裁定的判据是「实际解析到」：相对路径、`..` 绕路、符号链接、同 inode 别名都算。"""
        from controller import language_loop

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        session_root = directory.name
        shared = PROJECT_ROOT / "runtime"

        aliases: list[str] = [str(shared), str(PROJECT_ROOT / "controller" / ".." / "runtime")]

        cwd = os.getcwd()
        os.chdir(PROJECT_ROOT)
        self.addCleanup(os.chdir, cwd)
        aliases.append("runtime")

        link = Path(session_root) / "runtime-link"
        link.symlink_to(shared, target_is_directory=True)
        aliases.append(str(link))

        upper = PROJECT_ROOT / "RUNTIME"
        try:
            if upper.exists() and os.path.samefile(upper, shared):
                aliases.append(str(upper))
        except OSError:
            pass

        for alias in aliases:
            with self.subTest(alias=alias):
                self.assertTrue(resolves_to_shared_runtime(Path(alias)))
                with contextlib.redirect_stderr(io.StringIO()):
                    code = language_loop.main(self._refusal_argv(alias, session_root))
                self.assertEqual(code, 2)

    def test_an_isolated_runtime_is_not_mistaken_for_the_shared_one(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.assertFalse(resolves_to_shared_runtime(Path(directory.name)))
        self.assertFalse(
            resolves_to_shared_runtime(PROJECT_ROOT / "runtime" / "frames")
        )

    def test_the_refusal_creates_no_bridge_lock_or_run_log(self) -> None:
        """拒绝前零写入：五个常量路径与 `runs/` 的条目集合前后不变。"""
        from controller import language_loop

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        shared = PROJECT_ROOT / "runtime"
        watched = [
            shared / bridge.REQUEST_FILE,
            shared / bridge.RESULT_FILE,
            shared / bridge.TRACKER_STATE_FILE,
            shared / bridge.REQUEST_LOCK_FILE,
            shared / bridge.SESSION_LOCK_FILE,
        ]
        runs = shared / "runs"

        def snapshot() -> tuple[list[bool], list[str]]:
            return (
                [path.exists() for path in watched],
                sorted(item.name for item in runs.iterdir()) if runs.is_dir() else [],
            )

        before = snapshot()
        with contextlib.redirect_stderr(io.StringIO()):
            code = language_loop.main(self._refusal_argv(str(shared), directory.name))
        self.assertEqual(code, 2)
        self.assertEqual(snapshot(), before)

    def test_the_refusal_names_the_guard_and_lets_an_isolated_runtime_through(self) -> None:
        """守卫的判别力：退出码 2 必须来自守卫本身，隔离目录不得被误拒。"""
        from controller import language_loop

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        session_root = Path(directory.name)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = language_loop.main(
                self._refusal_argv(str(PROJECT_ROOT / "runtime"), str(session_root))
            )
        self.assertEqual(code, 2)
        self.assertIn("--runtime 指向共享的 runtime/", stderr.getvalue())

        # 正向对照：隔离 runtime 不被守卫拦，失败原因换成别的（坏收据）。
        isolated = session_root / "runtime"
        isolated.mkdir()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(FileNotFoundError):
                language_loop.main(
                    self._refusal_argv(str(isolated), str(session_root))
                )
        self.assertNotIn("--runtime 指向共享的 runtime/", stderr.getvalue())

    def test_operator_subcommands_are_guarded_too(self) -> None:
        """写请求同样会在 runtime 建锁与桥文件，所以九个动作共用同一守卫。"""
        from controller import language_loop

        shared = PROJECT_ROOT / "runtime"
        watched = [
            shared / bridge.REQUEST_FILE,
            shared / bridge.REQUEST_LOCK_FILE,
        ]
        before = [path.exists() for path in watched]
        for argv in (
            ["ask", "--session-id", "s1", "--runtime", str(shared), "the red car"],
            ["stop", "--session-id", "s1", "--runtime", str(shared)],
        ):
            with self.subTest(command=argv[0]):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    code = language_loop.main(argv)
                self.assertEqual(code, 2)
                self.assertIn("拒绝写请求", stderr.getvalue())
        self.assertEqual([path.exists() for path in watched], before)
class PreviewRenderTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest(
                "本解释器没有 Pillow；AC-5 的成功预览证据取有 Pillow 的那一跑"
            )
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.root = Path(self._directory.name)

    def _canvas(self) -> Path:
        from PIL import Image

        source = self.root / "frame.png"
        Image.new("RGB", (640, 480), BACKDROP).save(source)
        return source

    def test_real_renderer_draws_every_candidate_on_the_source_frame(self) -> None:
        from PIL import Image

        from controller.language_loop import render_preview
        from controller.language_selector import interpret

        selection = interpret(raw(AMBIGUOUS))
        self.assertEqual(len(selection.candidates), 2)
        destination = render_preview(
            self._canvas(), self.root / "preview.png", selection.candidates
        )
        self.assertTrue(destination.is_file())
        with Image.open(destination) as image:
            self.assertEqual(image.size, (640, 480))  # 绑定源帧尺寸
            pixels = image.convert("RGB").load()
            for candidate in selection.candidates:
                x, y, width, height = candidate.bbox_xywh_norm
                left, top = int(x * 640), int(y * 480)
                self.assertEqual(
                    pixels[left, top + 1],
                    CANDIDATE_RED,
                    f"候选 {candidate.index} 的框没有画出来",
                )
            # 远离所有候选的采样点仍是底色：渲染器不是整张涂红。
            self.assertEqual(pixels[639, 479], BACKDROP)

    def test_a_verification_preview_also_draws_the_paired_tracker_box(self) -> None:
        from PIL import Image

        from controller.language_loop import render_preview
        from controller.language_selector import interpret

        selection = interpret(raw(UNIQUE))
        destination = render_preview(
            self._canvas(),
            self.root / "verify.png",
            selection.candidates,
            TRACKER_BOX_FAR,
        )
        with Image.open(destination) as image:
            pixels = image.convert("RGB").load()
            left = int(TRACKER_BOX_FAR[0] * 640)
            top = int(TRACKER_BOX_FAR[1] * 480)
            self.assertEqual(pixels[left, top + 1], TRACKER_GREEN)


# --- P1-ENG-ACQ-001 AC-13 / AC-14：常驻会话、跟踪中指定与转向通道 ---------------------

from controller.body_planner import BodyCommand  # noqa: E402
from controller.language_loop import AcquireParams, CandidatesBackend  # noqa: E402
from controller.resident_core import ResidentCore, ResolverConfig, TrackRow  # noqa: E402

BOX_A = (0.3, 0.3, 0.2, 0.2)  # = UNIQUE 的归一化框
BOX_B = (0.01, 0.01, 0.07, 0.07)  # = UNIQUE_FAR
BOX_NEAR_POINT = (0.35, 0.45, 0.1, 0.1)  # 中心 (256, 240) px：BOX_A 底边中点地面点在同姿态下的投影


class FakeResident:
    """常驻插件替身：`ResidentCore` 真实现 + 可编排的逐帧轨迹；`init`/`update` 一调即失败（不存在 init-at-N 路径）。"""

    name = "fake-resident"
    backend = "test"
    version = "1"
    mode = "resident"

    def __init__(self, level2=None):
        self.core = ResidentCore(128, ResolverConfig())
        self.tracked: dict[int, tuple] = {1: BOX_A}
        self.lost: dict[int, tuple] = {}
        self.removed: list[int] = []
        self.steps: list[int] = []
        self.level2 = level2
        self.level2_calls = 0
        #: R1-3 回归：处理某帧时由夹具模拟 Unity 并发写出新帧（经 `FixtureFramePublisher`，生产帧包格式）。
        self.on_step = None

    def step(self, image, frame_id, metadata):
        self.steps.append(frame_id)
        if self.on_step is not None:
            self.on_step(frame_id)
        tracked = [TrackRow(i, b, 0.9, 0, "tracked") for i, b in sorted(self.tracked.items())]
        lost = [TrackRow(i, b, 0.8, 0, "lost") for i, b in sorted(self.lost.items())]
        removed, self.removed = list(self.removed), []
        return self.core.record(frame_id, metadata, tracked, lost, removed, len(self.steps))

    def pointer_result(self, frame_id):
        return self.core.pointer_result(frame_id)

    def _runner(self):
        def runner(k_, box_, h_):
            self.level2_calls += 1
            from controller.reanchor import ReplayResult  # noqa: PLC0415

            if self.level2 is None:
                return ReplayResult("RESEED_READY", None, k_, h_, h_ - k_, 1.0, TrackerResult((0.9, 0.9, 0.05, 0.05), True, 0.9, "tracker"))
            return self.level2(k_, box_, h_)

        return runner

    def designate(self, box, k):
        return self.core.designate(box, k, self._runner())

    def resolve_designation(self, box, k, designation_id):
        """P1-ENG-CAPTURE-001 C5：与 `DetAssocTracker.resolve_designation` 同一接口（同一 runner）。"""
        return self.core.resolve_designation(box, k, self._runner(), designation_id)

    def follow(self, track_id):
        self.core.follow(track_id)

    def pointer(self):
        return self.core.pointer()

    def history(self, frame_id):
        return self.core.history(frame_id)

    def init(self, image, box):  # pragma: no cover - 必须不可达
        raise AssertionError("resident session must never call init")

    def update(self, image):  # pragma: no cover - 必须不可达
        raise AssertionError("resident session must never call update")

    def manifest_identity(self):
        return {"name": self.name, "mode": "resident"}


class ResidentSessionTests(unittest.TestCase):
    def harness(self, responses, tracker=None, **kwargs):
        tracker = tracker or FakeResident()
        harness = Harness(self, responses=[raw(r) for r in responses], resident_tracker=tracker, **kwargs)
        return harness, tracker

    def bind_first(self, harness, tracker):
        harness.publish(2)
        self.assertIsNotNone(harness.session.loop)
        harness.ask()
        harness.tick(2)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        harness.confirm(0)
        harness.tick(1)
        self.assertEqual(harness.session.state, "TRACKING")
        self.assertEqual(harness.session.track_id, "s1-t1")

    def state_doc(self, harness):
        return bridge.read_tracker_state(harness.runtime)["tracker_state"]

    def test_designate_while_tracking_resident_loop_starts_without_init(self) -> None:
        harness, tracker = self.harness([UNIQUE])
        harness.publish(3)
        self.assertEqual(harness.session.state, "IDLE")
        self.assertEqual(tracker.steps, [0, 1, 2])
        self.assertEqual(harness.session.resident_loops_started, 1)
        self.assertFalse(self.state_doc(harness)["publishing"])
        files = harness.bridge_files()  # 无指针：零观测、零云台；机身只有启动时的显式 hold（透传安全通道）
        self.assertEqual((files["tracking_observation.json"], files["gimbal_command.json"]), (None, None))
        self.assertIn(b'"mode": "hold"', files["body_command.json"])
        self.assertEqual([r for r in harness.receipts() if r["outcome"] == "WRITTEN" and r["channel"] != "body_safety_hold"], [])

    def test_designate_while_tracking_bound_switches_pointer(self) -> None:
        """TRACKING → ask → QUERYING（保留指针、继续发布）→ confirm → BOUND：换指针、不重建关联器。"""
        harness, tracker = self.harness([UNIQUE, UNIQUE_FAR])
        self.bind_first(harness, tracker)
        loop = harness.session.loop
        tracker.tracked[2] = BOX_B
        harness.publish(1)
        harness.request("ask", ticks=1, instruction=bridge.parse_instruction("the blue truck"))
        self.assertIn(harness.session.state, {"QUERYING", "AWAITING_CONFIRMATION"})
        self.assertTrue(self.state_doc(harness)["publishing"])
        harness.tick(2)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        self.assertTrue(self.state_doc(harness)["publishing"])
        observed = [r for r in harness.receipts() if r["channel"] == "observation" and r["outcome"] == "WRITTEN"]
        harness.publish(2)  # 候选待确认期间指针 track 继续发布
        observed_after = [r for r in harness.receipts() if r["channel"] == "observation" and r["outcome"] == "WRITTEN"]
        self.assertGreater(len(observed_after), len(observed))
        harness.confirm(0)
        harness.tick(1)
        self.assertEqual((harness.session.state, harness.session.track_id, tracker.pointer()), ("TRACKING", "s1-t2", 2))
        self.assertIs(harness.session.loop, loop)
        self.assertEqual(harness.session.resident_loops_started, 1)
        retired = harness.session.retired_track_ids
        self.assertEqual([(r["track_id"], r["retired_reason"]) for r in retired], [("s1-t1", "operator_release")])
        doc = self.state_doc(harness)
        self.assertEqual((doc["designation"]["result"], doc["designation"]["track_id"], doc["designation"]["resolution_level"]), ("BOUND", 2, 1))
        harness.publish(1)
        latest = json.loads((harness.runtime / "tracking_observation.json").read_text())
        self.assertIn('"s1-t2"', json.dumps(latest))
        self.assertNotIn('"s1-t1"', json.dumps(latest))

    def test_designate_while_tracking_coasting_stays_tracking_raw_lost(self) -> None:
        harness, tracker = self.harness([UNIQUE, UNIQUE_FAR])
        self.bind_first(harness, tracker)
        tracker.tracked[2] = BOX_B
        harness.publish(1)
        harness.ask("the blue truck")
        harness.tick(2)
        del tracker.tracked[2]
        tracker.lost[2] = BOX_B
        harness.publish(1)
        harness.confirm(0)
        harness.tick(1)
        self.assertEqual((harness.session.state, harness.session.designation["result"]), ("TRACKING", "BOUND_COASTING"))
        harness.publish(2)
        self.assertEqual(harness.session.state, "TRACKING")  # unmatched 不升级为 SUSPECTED
        self.assertEqual(self.state_doc(harness)["tracker_raw_state"], "LOST")

    def test_designate_while_tracking_other_three_values_restore_state(self) -> None:
        # NO_TRACK_AT_K（第二级 no_adoption）→ 回到 TRACKING，指针不变。
        harness, tracker = self.harness([UNIQUE, '{"status": "unique", "bbox_2d": [700, 700, 760, 760]}'])
        self.bind_first(harness, tracker)
        harness.ask("the green bus")
        harness.tick(2)
        harness.confirm(0)
        harness.tick(1)
        self.assertEqual((harness.session.state, harness.session.track_id, tracker.pointer()), ("TRACKING", "s1-t1", 1))
        self.assertEqual((harness.session.designation["result"], harness.session.designation["level2"]["reason"]), ("NO_TRACK_AT_K", "no_adoption"))
        self.assertEqual(tracker.level2_calls, 1)
        # AMBIGUOUS：两条同帧轨迹过门且裕度不足 → 回到 TRACKING。
        harness2, tracker2 = self.harness([UNIQUE, UNIQUE])
        self.bind_first(harness2, tracker2)
        tracker2.tracked[3] = (0.301, 0.3, 0.2, 0.2)
        harness2.publish(1)
        harness2.ask("the red car")
        harness2.tick(2)
        harness2.confirm(0)
        harness2.tick(1)
        self.assertEqual((harness2.session.state, harness2.session.designation["result"], tracker2.pointer()), ("TRACKING", "AMBIGUOUS", 1))
        # FRAME_NOT_IN_HISTORY（从 IDLE 出发）→ 回到 IDLE。
        harness3, tracker3 = self.harness([UNIQUE])
        harness3.publish(1)
        harness3.ask()
        harness3.tick(2)
        tracker3.core._history.clear()  # noqa: SLF001 — 模拟 k 帧已淘汰
        harness3.publish(1)
        harness3.confirm(0)
        harness3.tick(1)
        self.assertEqual((harness3.session.state, harness3.session.designation["result"]), ("IDLE", "FRAME_NOT_IN_HISTORY"))

    def test_designate_while_tracking_suspected_keeps_suspect_on_failure(self) -> None:
        harness, tracker = self.harness([UNIQUE, NONE, NONE, NONE], attempt_limit=1)
        self.bind_first(harness, tracker)
        del tracker.tracked[1]
        tracker.removed.append(1)
        harness.publish(1)
        self.assertEqual((harness.session.state, harness.session.suspect_kind), ("SUSPECTED", "tracker_failure"))
        suspect = harness.session.suspect_id
        harness.ask("the red car")
        harness.tick(2)
        self.assertEqual((harness.session.state, harness.session.suspect_id), ("SUSPECTED", suspect))

    def test_designate_while_tracking_removed_raises_suspect_not_reacquire(self) -> None:
        harness, tracker = self.harness([UNIQUE])
        self.bind_first(harness, tracker)
        del tracker.tracked[1]
        tracker.removed.append(1)
        tracker.tracked[7] = BOX_A  # 同位置新 id：不自动重捕
        harness.publish(2)
        self.assertEqual(harness.session.state, "SUSPECTED")
        self.assertEqual(tracker.pointer(), 1)

    def test_designate_while_tracking_unlisted_combinations_rejected(self) -> None:
        harness, tracker = self.harness([UNIQUE])
        self.bind_first(harness, tracker)
        for action, extra in (("confirm_lost", {"token": "x"}), ("dismiss", {"token": "x"}), ("reject", {"token": "x"}), ("confirm", {"token": "x", "candidate_index": 0})):
            before = harness.session.state
            receipt = harness.request(action, **extra)
            self.assertEqual((receipt["outcome"], harness.session.state), ("REQUEST_INVALID", before), action)
        self.assertIn("ACQUIRING", bridge.SESSION_STATES)
        for reason in ("acquire_failed", "slew_timeout", "adopt_timeout"):
            self.assertIn(reason, bridge.STATE_REASONS)

    # --- AC-14：转向通道 ---

    def _to_acquiring(self, harness, tracker):
        """TRACKING(t1 on track 1) → ask 指定 track 5 → 确认前 5 被移除 → TRACK_ENDED → ACQUIRING。"""
        self.bind_first(harness, tracker)
        tracker.tracked[5] = BOX_A
        tracker.tracked[1] = BOX_B
        harness.publish(1)
        harness.ask("the red car")
        harness.tick(2)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        del tracker.tracked[5]
        tracker.removed.append(5)
        harness.publish(1)
        harness.confirm(0)
        harness.tick(1)
        self.assertEqual(harness.session.state, "ACQUIRING")

    def test_acquiring_slews_exactly_once_and_holds_body(self) -> None:
        harness, tracker = self.harness([UNIQUE, UNIQUE])
        self._to_acquiring(harness, tracker)
        slews = [r for r in harness.receipts() if r["channel"] == "slew_look_at"]
        self.assertEqual([r["outcome"] for r in slews], ["WRITTEN"])
        designation_id = slews[0]["detail"]["designation_id"]
        self.assertIsNone(harness.session.publisher.slew_look_at((1.0, 0.0, 1.0), designation_id))
        self.assertEqual(harness.receipts()[-1]["reason"], "slew_repeated")
        body = json.loads((harness.runtime / "body_command.json").read_text())
        self.assertIn("hold", json.dumps(body))
        self.assertEqual(harness.session.track_id, None)
        self.assertEqual([r["track_id"] for r in harness.session.retired_track_ids], ["s1-t1"])

    def test_acquiring_velocity_rejected_as_orphan_control(self) -> None:
        harness, tracker = self.harness([UNIQUE, UNIQUE])
        self._to_acquiring(harness, tracker)
        from controller.gated_publisher import BodyCommandNotWritten  # noqa: PLC0415

        with self.assertRaises(BodyCommandNotWritten):
            harness.session.publisher.body_command(BodyCommand.velocity(1.0, 0.0, 0.4, "test"))
        self.assertEqual(harness.receipts()[-1]["reason"], "orphan_control")

    def test_acquiring_arrival_and_n_of_m_adoption(self) -> None:
        harness, tracker = self.harness([UNIQUE, UNIQUE])
        self._to_acquiring(harness, tracker)
        tracker.tracked[9] = BOX_NEAR_POINT
        harness.publish(2)  # 到位：角速率 0 < ω_arr 且投影点在画内，连续 N_arr = 2 帧
        self.assertEqual(harness.session.state, "ACQUIRING")
        self.assertTrue(harness.session._acquire["arrived"])  # noqa: SLF001
        harness.publish(3)  # N = 3 帧连续收养同一 track
        self.assertEqual((harness.session.state, harness.session.track_id, tracker.pointer()), ("TRACKING", "s1-t2", 9))
        self.assertEqual(harness.session.designation["result"], "BOUND")

    def test_acquiring_arrival_red_when_slewing(self) -> None:
        """红：相机仍以 > ω_arr 转动 → 不到位；T_slew 到时 → LOST(acquire_failed) + hold。"""
        harness, tracker = self.harness([UNIQUE, UNIQUE], acquire=AcquireParams(t_slew_s=1.0))
        self._to_acquiring(harness, tracker)
        import math as _m  # noqa: PLC0415

        for step in range(8):
            angle = _m.radians(10.0 * (step + 1))
            base = (0.7071068286895752, 0.0, 0.0, 0.7071068286895752)
            twist = (0.0, _m.sin(angle / 2), 0.0, _m.cos(angle / 2))
            x1, y1, z1, w1 = twist
            x2, y2, z2, w2 = base
            harness.publisher.camera_rotation_xyzw = (
                w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
                w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            )
            harness.publish(1, tick=False)
            harness.tick(1, advance_s=0.2)
            if harness.session.state != "ACQUIRING":
                break
        self.assertEqual((harness.session.state, harness.session.reason), ("LOST", "acquire_failed"))
        self.assertEqual(harness.session.designation["acquire"]["cause"], "slew_timeout")

    def test_acquiring_adopt_timeout_red_green(self) -> None:
        harness, tracker = self.harness([UNIQUE, UNIQUE])
        self._to_acquiring(harness, tracker)
        tracker.tracked.pop(9, None)
        harness.publish(2 + 5)  # 到位后 M = 5 帧无收养
        self.assertEqual((harness.session.state, harness.session.reason), ("LOST", "acquire_failed"))
        self.assertEqual(harness.session.designation["acquire"]["cause"], "adopt_timeout")
        holds = json.loads((harness.runtime / "body_command.json").read_text())
        self.assertIn("hold", json.dumps(holds))
        # 失败后不重试、不自动重播种：后续帧里即使出现候选也不收养。
        tracker.tracked[9] = BOX_NEAR_POINT
        harness.publish(4)
        self.assertEqual((harness.session.state, tracker.pointer()), ("LOST", None))

    def test_acquiring_ambiguous_adoption_reported(self) -> None:
        harness, tracker = self.harness([UNIQUE, UNIQUE])
        self._to_acquiring(harness, tracker)
        tracker.tracked[9] = BOX_NEAR_POINT
        tracker.tracked[10] = (0.36, 0.45, 0.1, 0.1)  # 6 px 外：裕度 < 15 px
        harness.publish(3)
        self.assertEqual((harness.session.state, harness.session.reason), ("LOST", "acquire_failed"))
        self.assertEqual((harness.session.designation["result"], harness.session.designation["candidates"]), ("AMBIGUOUS", [9, 10]))

    def test_acquiring_after_coasting_timeout_same_designation(self) -> None:
        """§3.4：`BOUND_COASTING` 从未找回、库移除 → 同一 designation_id 内转 `TRACK_ENDED` 处置（第三级转向）。"""
        harness, tracker = self.harness([UNIQUE, UNIQUE_FAR])
        self.bind_first(harness, tracker)
        tracker.tracked[2] = BOX_B
        harness.publish(1)
        harness.ask("the blue truck")
        harness.tick(2)
        del tracker.tracked[2]
        tracker.lost[2] = BOX_B
        harness.publish(1)
        harness.confirm(0)
        harness.tick(1)
        self.assertEqual(harness.session.designation["result"], "BOUND_COASTING")
        designation_id = harness.session.designation["designation_id"]
        del tracker.lost[2]
        tracker.removed.append(2)
        harness.publish(1)
        self.assertEqual((harness.session.state, harness.session.designation["result"]), ("ACQUIRING", "TRACK_ENDED"))
        slews = [r for r in harness.receipts() if r["channel"] == "slew_look_at"]
        self.assertEqual([(r["outcome"], r["detail"]["designation_id"]) for r in slews], [("WRITTEN", designation_id)])

    def test_acquiring_not_after_recovered_then_lost(self) -> None:
        """捕获后（coasting 已找回）的丢失只由人处置：→ SUSPECTED，不自动转向（D.1）。"""
        harness, tracker = self.harness([UNIQUE, UNIQUE_FAR])
        self.bind_first(harness, tracker)
        tracker.tracked[2] = BOX_B
        harness.publish(1)
        harness.ask("the blue truck")
        harness.tick(2)
        del tracker.tracked[2]
        tracker.lost[2] = BOX_B
        harness.publish(1)
        harness.confirm(0)
        harness.tick(1)
        del tracker.lost[2]
        tracker.tracked[2] = BOX_B
        harness.publish(1)  # 找回
        del tracker.tracked[2]
        tracker.removed.append(2)
        harness.publish(1)
        self.assertEqual(harness.session.state, "SUSPECTED")
        self.assertEqual([r for r in harness.receipts() if r["channel"] == "slew_look_at"], [])

    def test_acquiring_stop_is_terminal(self) -> None:
        harness, tracker = self.harness([UNIQUE, UNIQUE])
        self._to_acquiring(harness, tracker)
        harness.request("stop")
        self.assertEqual(harness.session.state, "TERMINAL")

    # --- R1@K1K2K3 返工回归（docs/reviews/P1-ENG-ACQ-001.md §3 R1-1/R1-2/R1-3） ---

    def _frame_metadata(self, harness, frame_id):
        return json.loads(harness.frame_paths(frame_id)[1].read_text(encoding="utf-8"))

    def _servo_records(self, harness):
        path = harness.session.logger.run_directory / "frames.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_acquiring_slew_point_extrapolated_for_moving_target(self) -> None:
        """R1-1（§3.7）：移动目标 `TRACK_ENDED` 确认后，唯一一次 `slew_look_at` 的世界点 =
        k 帧点 + 地面差分速度 ×（发令时历史头仿真时刻 − t_k）；静止目标仍为 k 帧点。"""
        harness, tracker = self.harness([UNIQUE, UNIQUE])
        self.bind_first(harness, tracker)
        tracker.tracked[1] = BOX_B
        for step in range(5):  # track 5 逐帧右移，查询帧 k 上恰在 BOX_A
            tracker.tracked[5] = (0.26 + 0.01 * step, 0.3, 0.2, 0.2)
            harness.publish(1)
        harness.ask("the red car")
        harness.tick(2)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        del tracker.tracked[5]
        tracker.removed.append(5)
        head = harness.publish(3)  # k 之后再过 3 帧（0.6 s）才确认
        harness.confirm(0)
        harness.tick(1)
        self.assertEqual((harness.session.state, harness.session.designation["result"]), ("ACQUIRING", "TRACK_ENDED"))
        acquire = harness.session.designation["acquire"]
        velocity = acquire["velocity_world_mps"]
        self.assertIsNotNone(velocity)
        self.assertGreater(abs(velocity[0]), 1.0)  # 约 2 m/s 的红车
        time_k = self._frame_metadata(harness, harness.session.designation["frame_id_k"])["simulation_time_s"]
        time_head = self._frame_metadata(harness, head)["simulation_time_s"]
        self.assertAlmostEqual(time_head - time_k, 0.6, places=6)
        expected = [acquire["world_point_k"][i] + velocity[i] * (time_head - time_k) for i in range(3)]
        slews = [r for r in harness.receipts() if r["channel"] == "slew_look_at"]
        self.assertEqual([r["outcome"] for r in slews], ["WRITTEN"])
        point = slews[0]["detail"]["point_world_m"]
        for i in range(3):
            self.assertAlmostEqual(point[i], expected[i], places=6)
        self.assertGreater(math.dist(point, acquire["world_point_k"]), 0.5)
        # 静止目标（k 帧命中轨迹不足 2 帧历史）：转向点就是 k 帧点。
        harness2, tracker2 = self.harness([UNIQUE, UNIQUE])
        self._to_acquiring(harness2, tracker2)
        acquire2 = harness2.session.designation["acquire"]
        self.assertIsNone(acquire2.get("velocity_world_mps"))
        slews2 = [r for r in harness2.receipts() if r["channel"] == "slew_look_at"]
        self.assertEqual(slews2[0]["detail"]["point_world_m"], acquire2["world_point_k"])

    def test_acquiring_servo_baseline_follows_slew_command(self) -> None:
        """R1-2（§3.8、AC-15 修订 1、IR-22）：转向指令写入后成为限速基准——收养后首条伺服 `look_at`
        与转向点的视线角 ≤ ω_max/hz；`ACQUIRE_FAILED` 后新 `BOUND` 的首条伺服同样以转向点为基准。"""
        from controller.track_loop import los_angle_deg  # noqa: PLC0415

        limit = 30.0 / 5.0  # ω_max / hz（缺省 30°/s、5 Hz）
        origin = (132.0, 25.2, 117.0)  # `FixtureFramePublisher` 缺省相机位置（视线原点）

        def slew_and_old(harness):
            slews = [r for r in harness.receipts() if r["channel"] == "slew_look_at" and r["outcome"] == "WRITTEN"]
            self.assertEqual(len(slews), 1)
            before = [r for r in self._servo_records(harness) if r.get("published_gimbal_command")]
            return slews[0]["detail"]["point_world_m"], before[-1]["look_at_world_m"], len(before)

        def first_after(harness, count):
            written = [r for r in self._servo_records(harness) if r.get("published_gimbal_command")]
            self.assertGreater(len(written), count)
            return written[count]["look_at_world_m"]

        # (a) 收养成功 → TRACKING：首条伺服相对转向点 ≤ 6°。
        harness, tracker = self.harness([UNIQUE, UNIQUE])
        self._to_acquiring(harness, tracker)
        slew, old, count = slew_and_old(harness)
        self.assertGreater(los_angle_deg(origin, old, slew), 2 * limit)  # 合成大偏差：旧伺服点远离转向点
        tracker.tracked[9] = BOX_NEAR_POINT
        harness.publish(5)
        self.assertEqual((harness.session.state, tracker.pointer()), ("TRACKING", 9))
        harness.publish(1)
        first = first_after(harness, count)
        self.assertLessEqual(los_angle_deg(origin, slew, first), limit + 1e-6)
        # (b) ACQUIRE_FAILED（云台停在转向点）→ 新 BOUND：首条伺服同样以转向点为基准。
        harness2, tracker2 = self.harness([UNIQUE, UNIQUE, UNIQUE])
        self._to_acquiring(harness2, tracker2)
        slew2, old2, count2 = slew_and_old(harness2)
        self.assertGreater(los_angle_deg(origin, old2, slew2), 2 * limit)
        harness2.publish(2 + 5)
        self.assertEqual((harness2.session.state, harness2.session.reason), ("LOST", "acquire_failed"))
        tracker2.tracked[11] = BOX_A
        harness2.publish(1)
        harness2.ask("the red car")
        harness2.tick(2)
        harness2.confirm(0)
        harness2.tick(1)
        self.assertEqual((harness2.session.state, tracker2.pointer()), ("TRACKING", 11))
        harness2.publish(1)
        first2 = first_after(harness2, count2)
        self.assertLessEqual(los_angle_deg(origin, slew2, first2), limit + 1e-6)

    def test_resident_catchup_new_frame_mid_batch_not_stale(self) -> None:
        """R1-3（AC-15 修订 1、IR-3、§3.4.1）：追平批内 Unity 写出新帧时，发布窗口按发布时的 `latest.json`
        判定（与门 ④ 同源）——不产生 `catchup_stale` 拒绝、不拆常驻载体；落到窗口外的帧逐帧记跳过、不发观测/look_at。"""
        harness, tracker = self.harness([UNIQUE])
        self.bind_first(harness, tracker)
        loop = harness.session.loop
        last = harness.publish(6, tick=False)  # 积压 6 帧（批首 latest = last）
        trigger = last - 3

        def concurrent_frame(frame_id):
            if frame_id == trigger:
                harness.publisher.publish(b"concurrent-unity-frame")

        tracker.on_step = concurrent_frame
        before = len(harness.receipts())
        harness.tick(1)
        tracker.on_step = None
        batch = harness.receipts()[before:]
        self.assertEqual([r for r in batch if r["outcome"] == "PUBLISH_REJECTED"], [])
        self.assertIsNone(harness.session.publisher.fatal_reason)
        self.assertIs(harness.session.loop, loop)
        self.assertEqual((harness.session.state, harness.session.track_id), ("TRACKING", "s1-t1"))
        written = lambda channel: [r["frame_id"] for r in batch if r["channel"] == channel and r["outcome"] == "WRITTEN"]  # noqa: E731
        self.assertEqual(written("observation"), [last - 1, last])  # 发布时 latest = last + 1：只有差 ≤ 2 的帧
        self.assertEqual(written("look_at"), [last - 1, last])
        records = {r["frame_id"]: r for r in self._servo_records(harness) if r.get("frame_id") is not None}
        for frame_id in range(last - 5, last - 1):
            self.assertEqual(records[frame_id]["publish_skip_reason"], "outside_resident_publish_window", frame_id)
            self.assertFalse(records[frame_id]["published_observation"], frame_id)
            self.assertIsNone(records[frame_id]["look_at_world_m"], frame_id)
        for frame_id in (last - 1, last):
            self.assertIsNone(records[frame_id]["publish_skip_reason"], frame_id)
        harness.tick(1)  # 下一 tick 追上并发帧，照常发布
        self.assertEqual([r["frame_id"] for r in harness.receipts() if r["channel"] == "observation" and r["outcome"] == "WRITTEN"][-1], last + 1)
        self.assertIs(harness.session.loop, loop)

    def test_resident_catchup_batch_end_pushed_out_skips_body_step(self) -> None:
        """R1-3 附带：批末帧被批内新帧挤出发布窗口时不再是最新帧——不发观测、不做机身步（不发无同帧
        观测的机身速度），不触发任何门拒；下一批批末帧照常以同帧合格观测发机身速度。"""
        harness, tracker = self.harness([UNIQUE], body=True)
        tilt_camera(harness, 40.0)
        self.bind_first(harness, tracker)
        loop = harness.session.loop
        harness.publish(1)
        self.assertEqual([r for r in harness.receipts() if r["channel"] == "body_command"][-1]["outcome"], "WRITTEN")
        last = harness.publish(3, tick=False)
        trigger = last - 2

        def concurrent_frames(frame_id):
            if frame_id == trigger:
                for _ in range(3):
                    harness.publisher.publish(b"concurrent-unity-frame")

        tracker.on_step = concurrent_frames
        before = len(harness.receipts())
        harness.tick(1)
        tracker.on_step = None
        batch = harness.receipts()[before:]
        self.assertEqual([r for r in batch if r["channel"] in {"observation", "look_at", "body_command"}], [])
        self.assertIsNone(harness.session.publisher.fatal_reason)
        self.assertIs(harness.session.loop, loop)
        records = {r["frame_id"]: r for r in self._servo_records(harness) if r.get("frame_id") is not None}
        self.assertEqual(records[last]["publish_skip_reason"], "outside_resident_publish_window")
        self.assertNotIn("body_planner", records[last])
        harness.tick(1)
        velocities = [r for r in harness.receipts() if r["channel"] == "body_command"]
        observations = [r for r in harness.receipts() if r["channel"] == "observation" and r["outcome"] == "WRITTEN"]
        self.assertEqual((velocities[-1]["outcome"], velocities[-1]["frame_id"]), ("WRITTEN", last + 3))
        self.assertEqual(observations[-1]["frame_id"], last + 3)
        self.assertEqual(harness.session.state, "TRACKING")

    # --- R2@K1K2K3 返工回归（docs/reviews/P1-ENG-ACQ-001.md「R2@K1K2K3」§3 R2-1） ---

    def test_resident_rebuild_servo_baseline_carries_last_written_gimbal_point(self) -> None:
        """R2-1（AC-15 修订 1、§3.6、§3.8、IR-4/IR-24）：`frame_gap` → `REINIT_REQUIRED` → 常驻载体重建 →
        远目标再指定；`gimbal_command.json` 是会话唯一云台通道，重建前后两条已写指令相邻，新 `BOUND` 的首条
        已写伺服相对重建前最后一条已写云台指令的视线角 ≤ ω_max/hz（重建不清空限速基准）。"""
        from controller.geolocate import box_ground_intersection  # noqa: PLC0415
        from controller.track_loop import RuntimePublisher, los_angle_deg  # noqa: PLC0415

        limit = 30.0 / 5.0  # ω_max / hz（缺省 30°/s、5 Hz）
        origin = (132.0, 25.2, 117.0)  # `FixtureFramePublisher` 缺省相机位置（视线原点）
        written: list[tuple[float, float, float]] = []  # 实际写入 gimbal_command.json 的点（含转向，按时间序）
        original = RuntimePublisher.look_at

        def recording(publisher, point_world_m):
            written.append(tuple(float(v) for v in point_world_m))
            return original(publisher, point_world_m)

        harness, tracker = self.harness([UNIQUE, UNIQUE_FAR])
        with patch.object(RuntimePublisher, "look_at", recording):
            self.bind_first(harness, tracker)
            harness.publish(2)
            self.assertTrue(written)
            # 生产事件：中间帧缺失 → frame_gap → REINIT_REQUIRED，常驻载体拆除。
            last = harness.publish(3, tick=False)
            harness.frame_paths(last - 1)[0].unlink()
            harness.tick(1)
            self.assertEqual((harness.session.state, harness.session.reason), ("REINIT_REQUIRED", "frame_gap"))
            self.assertIsNone(harness.session.loop)
            before_rebuild = written[-1]
            count = len(written)
            # 下一 tick 从最新帧重建常驻载体。
            harness.tick(1)
            self.assertEqual(harness.session.resident_loops_started, 2)
            self.assertIsNotNone(harness.session.loop)
            # 远目标再指定：track 2 在 BOX_B（画面左上角），与重建前最后指令视线角远超 ω_max/hz。
            tracker.tracked[2] = BOX_B
            harness.publish(1)
            harness.ask("the blue truck")
            harness.tick(2)
            self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
            harness.confirm(0)
            harness.tick(1)
            self.assertEqual((harness.session.state, tracker.pointer()), ("TRACKING", 2))
            self.assertEqual(len(written), count)  # 重建与再指定期间没有其他云台写入
            harness.publish(1)
        self.assertGreater(len(written), count)
        first = written[count]
        self.assertLessEqual(los_angle_deg(origin, before_rebuild, first), limit + 1e-6)
        servo = [r for r in self._servo_records(harness) if r.get("published_gimbal_command")]
        self.assertEqual(tuple(servo[0]["look_at_world_m"]), first)
        # 合成大偏差：该帧指针框的直接地面点与重建前最后指令相差远超上限，首条伺服确被限速到上限处。
        target = box_ground_intersection(
            BOX_B, self._frame_metadata(harness, servo[0]["frame_id"]), 0.0, harness.session.config.maximum_ground_range_m
        ).point_world_m
        self.assertGreater(los_angle_deg(origin, before_rebuild, target), 2 * limit)
        self.assertGreater(los_angle_deg(origin, before_rebuild, first), limit - 0.1)

    def test_designate_while_tracking_candidates_backend_matches_vlm_contract(self) -> None:
        backend = CandidatesBackend()
        core = ResidentCore(128)
        core.record(4, {}, [TrackRow(1, BOX_A, 0.9, 0, "tracked"), TrackRow(2, BOX_B, 0.8, 0, "tracked")], [], [], 1)
        backend.bind_history(core.history)
        selection = raw_interpret(backend.predict_one("q1", Path("frame_0000000004.jpg"), "any", None))
        self.assertEqual((selection.status, len(selection.candidates)), ("ambiguous", 2))
        self.assertEqual(raw_interpret(backend.predict_one("q2", Path("frame_0000000009.jpg"), "any", None)).status, "none")


def raw_interpret(raw_selection):
    from controller.language_selector import interpret  # noqa: PLC0415

    return interpret(raw_selection)


# --- P1-ENG-ACQ-001 AC-21（IR-17 / B1–B3）：`candidates` 后端接线 ------------------------------
# 夹具全部零消耗：合成历史行、合成帧名、临时目录；单宿主报告与收据由生产预检工具
# `tools/eng_acq/candidates_preflight.py` 在临时目录生成（开发机夹具，不是正式收据）。


def _candidates_receipt_files(root: Path, runtime: Path, samples: int = 100) -> tuple[Path, Path]:
    from tools.eng_acq import candidates_preflight as preflight  # noqa: PLC0415

    out = root / "k-receipt"
    with contextlib.redirect_stdout(io.StringIO()):
        code = preflight.run(runtime, out, samples)
    assert code == 0, code
    return out / preflight.RECEIPT_NAME, out / preflight.REPORT_NAME


def _load_receipt(path: Path) -> KReceipt:
    return KReceipt.from_document(json.loads(path.read_text(encoding="utf-8")))


class CandidatesBackendWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        self.receipt_path, self.report_path = _candidates_receipt_files(self.root, self.runtime)
        self.receipt = _load_receipt(self.receipt_path)

    def _argv(self, *extra: str) -> list[str]:
        return [
            "run", "--session-id", "cand-1", "--session-root", str(self.root / "sessions"),
            "--runtime", str(self.runtime), "--k-receipt", str(self.receipt_path),
            "--ground-plane-y-m", "0.2", *extra,
        ]

    def _session(self, receipt: KReceipt, adapter=None) -> LanguageSession:
        return LanguageSession(
            SessionConfig(
                session_id="cand-1",
                session_root=self.root / "sessions",
                runtime=self.runtime,
                receipt=receipt,
                adapter=adapter if adapter is not None else CandidatesBackend(),
                tracker_name="det-assoc-v1",
                resident=True,
            )
        )

    # -- B1：CLI 闭集 → 真实 CandidatesBackend；交叉形态启动前拒绝 --

    def test_b1_run_cli_candidates_builds_real_candidates_backend(self) -> None:
        from controller.language_loop import build_parser, _run_session  # noqa: PLC0415

        for extra in ((), ("--model-form", "detector-tracks")):
            with self.subTest(extra=extra):
                arguments = build_parser().parse_args(
                    self._argv("--backend", "candidates", "--tracker", "det-assoc-v1", "--resident", *extra)
                )
                captured = []

                def fake_run(session, **_kwargs):
                    captured.append(session)
                    return "TERMINAL"

                with patch.object(LanguageSession, "run", fake_run):
                    self.assertEqual(_run_session(arguments), 0)
                self.assertEqual(arguments.model_form, "detector-tracks")
                session = captured[0]
                self.assertIs(type(session.config.adapter), CandidatesBackend)
                self.assertEqual(session.config.adapter.calls, 0)
                self.assertEqual((session.receipt.backend, session.receipt.model_form), ("candidates", "detector-tracks"))
                self.assertEqual((session.config.tracker_name, session.resident), ("det-assoc-v1", True))
                self.assertIsNone(session.loop)  # 未出帧：常驻载体（与检测器权重）尚未建立

    def test_b1_cross_forms_and_missing_resident_refused_before_session(self) -> None:
        from controller.language_loop import build_parser, _run_session  # noqa: PLC0415

        cases = [
            ("--backend", "candidates", "--model-form", "c2-merged", "--tracker", "det-assoc-v1", "--resident"),
            ("--backend", "candidates", "--model-form", "base", "--tracker", "det-assoc-v1", "--resident"),
            ("--backend", "http", "--model-form", "detector-tracks"),
            ("--backend", "replay", "--model-form", "detector-tracks"),
            ("--backend", "local-hf", "--model-form", "detector-tracks"),
            ("--backend", "candidates", "--tracker", "det-assoc-v1"),
            ("--backend", "candidates", "--tracker", "nanotrack-v2", "--resident"),
        ]
        for extra in cases:
            with self.subTest(extra=extra):
                arguments = build_parser().parse_args(self._argv(*extra))
                with patch("controller.language_loop._build_adapter") as build, \
                        patch("controller.language_loop.validate_measurement_sources") as validate, \
                        self.assertRaisesRegex(ConfigMismatch, "CONFIG_MISMATCH"):
                    _run_session(arguments)
                build.assert_not_called()
                validate.assert_not_called()
                self.assertFalse((self.root / "sessions").exists())

    # -- B2：单宿主 mac 报告；身份/宿主/R/hz/SHA/机器名不符即会话前 CONFIG_MISMATCH --

    def test_b2_single_mac_report_validates_and_vlm_two_report_path_unchanged(self) -> None:
        from controller.language_loop import CANDIDATES_IDENTITY, validate_measurement_sources  # noqa: PLC0415

        report = validate_measurement_sources(self.receipt)
        self.assertEqual((report["host"], report["backend"], report["model_form"]), ("mac", "candidates", "detector-tracks"))
        self.assertEqual(dict(self.receipt.model_identity), CANDIDATES_IDENTITY)
        self.assertEqual(set(self.receipt.source_reports), {"mac"})
        self.assertEqual((self.receipt.hz, self.receipt.retained_frame_count), (5.0, 128))
        session = self._session(self.receipt)
        self.addCleanup(session.close)
        self.assertEqual(session.state, "IDLE")
        # VLM 后端仍要求 mac + 5060 两份报告，单份 mac 报告不能放行。
        vlm = replace_receipt(self.receipt, backend="http", model_form="c2-adapter")
        with self.assertRaisesRegex(ConfigMismatch, "both source reports"):
            validate_measurement_sources(vlm)

    def test_b2_receipt_or_report_mismatch_refused_before_session(self) -> None:
        from controller.language_loop import CANDIDATES_IDENTITY  # noqa: PLC0415
        from tools.eng_acq import candidates_preflight as preflight  # noqa: PLC0415

        document = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        report = json.loads(self.report_path.read_text(encoding="utf-8"))

        def forged(name: str, **changes) -> KReceipt:
            """改报告内容后用生产收据构造器重出收据（SHA 一致），只测内容校验。"""
            path = self.root / f"{name}.json"
            path.write_text(json.dumps(dict(report, **changes)), encoding="utf-8")
            return _load_receipt_document(preflight.build_receipt(json.loads(path.read_text()), path))

        few = [0.0] * 99
        cases = {
            "host_5060": replace_receipt(self.receipt, host="5060"),
            "weights_identity": replace_receipt(
                self.receipt, model_identity=dict(CANDIDATES_IDENTITY, weights_sha256="a" * 64)
            ),
            "source_changed": replace_receipt(self.receipt, model_identity=dict(CANDIDATES_IDENTITY, source="vlm")),
            "two_reports": replace_receipt(
                self.receipt, source_reports=dict(self.receipt.source_reports, **{"5060": self.receipt.source_reports["mac"]})
            ),
            "receipt_r": _load_receipt_document(dict(document, retained_frame_count=1500)),
            "receipt_hz": _load_receipt_document(dict(document, hz=10.0, k_ret=k_ret_of(document["p95_s"], 10.0), k_conf=k_conf_of(10.0))),
            "receipt_p95": _load_receipt_document(dict(document, p95_s=0.5, k_ret=k_ret_of(0.5, 5.0))),
            "report_fail": forged("fail", verdict="FAIL"),
            "report_http": forged("http", host="5060", backend="http"),
            "report_other_machine": forged("machine", machine_name="dev-mac-not-unity-host"),
            "report_not_qualified": forged(
                "slow", p95_s=100.0, groups={name: dict(group, samples_s=[100.0] * 100, sample_count=100, p95_s=100.0)
                                             for name, group in report["groups"].items()}
            ),
            "report_few_samples": forged(
                "few", groups=dict(report["groups"], none=dict(report["groups"]["none"], samples_s=few, sample_count=99, p95_s=0.0))
            ),
        }
        for name, receipt in cases.items():
            with self.subTest(case=name), self.assertRaisesRegex(ConfigMismatch, "CONFIG_MISMATCH"):
                self._session(receipt)
            self.assertFalse((self.root / "sessions").exists(), name)
        with self.subTest(case="this_machine_differs"), \
                patch("controller.language_loop.machine_name", return_value="another-mac"), \
                self.assertRaisesRegex(ConfigMismatch, "differs from this machine"):
            self._session(self.receipt)
        with self.subTest(case="nan_p95"), self.assertRaises(ConfigMismatch):
            _load_receipt_document(dict(document, p95_s=float("nan")))
        with self.subTest(case="cross_form_receipt"), self.assertRaises(ConfigMismatch):
            _load_receipt_document(dict(document, model_form="c2-adapter"))
        self.report_path.write_bytes(self.report_path.read_bytes() + b"\n")
        with self.subTest(case="report_sha_changed"), self.assertRaisesRegex(ConfigMismatch, "SHA changed"):
            self._session(self.receipt)
        self.assertFalse((self.root / "sessions").exists())
        with self.subTest(case="scenario_r_differs"):
            # 收据在 R=1500 的生效配置下生成，会话 runtime 生效 R=128 → 会话前拒绝。
            other = self.root / "other"
            (other / "runtime").mkdir(parents=True)
            default = json.loads(BODY_SCENARIO_CONFIG.read_text(encoding="utf-8"))
            default["sensor"]["retained_frame_count"] = 1500
            (other / "runtime" / "scenario_config.json").write_text(json.dumps(default), encoding="utf-8")
            receipt_1500, _ = _candidates_receipt_files(other, other / "runtime")
            with self.assertRaisesRegex(ConfigMismatch, "hz/R differ"):
                self._session(_load_receipt(receipt_1500))
            # 既有检查点在建会话目录之后、任何桥写入/会话锁之前：runtime 仍为空。
            self.assertEqual(list(self.runtime.iterdir()), [])
            self.assertEqual(_load_receipt(receipt_1500).retained_frame_count, 1500)

    # -- B3：真实 LanguageSession 的 ask → worker → 结果写盘 → schema 读回 → 预览 → confirm --

    def test_b3_session_ask_writes_candidates_model_block_readable_and_confirmable(self) -> None:
        tracker = FakeResident()
        tracker.tracked = {1: BOX_A, 2: BOX_B}
        backend = CandidatesBackend()
        harness = Harness(self, responses=[], resident_tracker=tracker, adapter=backend, receipt=self.receipt)
        harness.publish(2)
        self.assertIsNotNone(harness.session.loop)
        harness.ask("the red car")
        harness.tick(2)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        self.assertEqual((backend.calls, harness.session.worker.calls_started), (1, 1))
        line = harness.results()[-1]
        self.assertEqual((line["status"], line["purpose"]), ("ambiguous", "designate"))
        self.assertEqual((line["model"]["backend"], line["model"]["model_form"]), ("candidates", "detector-tracks"))
        self.assertEqual(bridge._validate_model_block(line["model"])["backend"], "candidates")
        document = bridge.read_result(harness.runtime)  # 生产 schema 读回（闭集 fail-closed）
        self.assertEqual(document["result"]["result_id"], line["result_id"])
        self.assertEqual(document["result"]["model"]["model_form"], "detector-tracks")
        # 候选 = 查询帧 N 的常驻 `tracked` 历史（面积降序），不是 VLM/真值。
        entry = tracker.core.history(line["frame_id"])
        self.assertIsNotNone(entry)
        expected = [row.box_norm for row in sorted(entry.rows("tracked"), key=lambda r: -(r.box_norm[2] * r.box_norm[3]))]
        got = [tuple(c["bbox_xywh_norm"]) for c in line["candidates"]]
        self.assertEqual(len(got), len(expected))
        for box, want in zip(got, expected):
            for value, target in zip(box, want):
                self.assertAlmostEqual(value, target, delta=1e-3)
        self.assertIsNotNone(line["preview_path"])
        self.assertTrue(Path(line["preview_path"]).is_file())
        harness.confirm(1)  # 预览 index 1 = 面积较小的 track 2
        harness.tick(1)
        self.assertEqual((harness.session.state, tracker.pointer()), ("TRACKING", 2))
        self.assertEqual(harness.session.designation["result"], "BOUND")


def replace_receipt(receipt: KReceipt, **changes) -> KReceipt:
    from dataclasses import replace  # noqa: PLC0415

    return replace(receipt, **changes)


def _load_receipt_document(document: dict) -> KReceipt:
    return KReceipt.from_document(document)



# --- P1-ENG-LOOP-002 阶段 A（K1K2K3K4）：AC-1/3/4/5/17 ---------------------------------

import ast  # noqa: E402
import hashlib  # noqa: E402

from controller import language_loop as loop_module  # noqa: E402
from controller.gated_publisher import EXPLICIT_HOLD_REASONS  # noqa: E402
from controller.geolocate import GeometryRejected  # noqa: E402
from controller.language_loop import (  # noqa: E402
    CORE_EVENT_KINDS,
    DELAY_MAX_S,
    JOURNAL_KINDS,
    RESIDENT_REBUILD_LIMIT,
    build_parser,
    designate_options,
)
from controller.protocol import atomic_write  # noqa: E402

UNTETHERED_SCENARIO = PROJECT_ROOT / "config" / "scenario.untethered.json"
FRAME_BODY_CONFIG = PROJECT_ROOT / "config" / "p1-eng-frame-001-body.json"


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_untethered_override(runtime: Path) -> None:
    """§3.1 覆盖文件形状（测试只放隔离 runtime；R 保持 128 以匹配夹具收据）。"""
    (Path(runtime) / "scenario_config.json").write_bytes(UNTETHERED_SCENARIO.read_bytes())


def loop2_request(harness: Harness, action: str, *, ticks: int = 1, delay_s=None, intent=None, **kwargs) -> dict:
    """A4：带 `delay_s`/`intent` 的请求（与 `send_request` 同一写法：`request_payload` + 原子写）。"""
    harness._request_sequence += 1  # noqa: SLF001
    request_id = kwargs.pop("request_id", f"req{harness._request_sequence}")  # noqa: SLF001
    holder = bridge.acquire_writer_lock(harness.runtime, request_id=request_id, pid=4243, now=harness.clock.unix())
    payload = bridge.request_payload(
        session_id=harness.session.session_id, request_id=request_id, action=action, **kwargs
    )
    if delay_s is not None:
        payload["request"]["delay_s"] = delay_s
    if intent is not None:
        payload["request"]["intent"] = intent
    atomic_write(bridge.REQUEST_FILE, payload, harness.runtime)
    harness.tick(ticks)
    bridge.release_writer_lock(harness.runtime, request_id=request_id, pid=4243)
    del holder
    return harness.session.last_request or {}


def journal_kinds(harness: Harness, kind: str) -> list[dict]:
    return [row for row in harness.journal() if row["kind"] == kind]


class Loop2BodyPolicyTests(unittest.TestCase):
    """AC-1：`--body-policy standoff` 接 `standoff-band-v1`；缺省 threshold 路径调用序列不变。"""

    def _standoff(self, *, setup_runtime=write_untethered_override, body_scenario=None, **overrides):
        return Harness(
            self,
            responses=[],
            resident_tracker=FakeResident(),
            setup_runtime=setup_runtime,
            body_policy="standoff",
            body_planner_config=FRAME_BODY_CONFIG,
            body_scenario_config=body_scenario or UNTETHERED_SCENARIO,
            ground_plane_y_m=0.0,
            **overrides,
        )

    def test_standoff_builds_frame_planner_with_runtime_and_manifest_identity(self) -> None:
        calls = []
        original = loop_module._build_body_runtime

        def spy(*args, **kwargs):
            calls.append((args, kwargs))
            return original(*args, **kwargs)

        with patch.object(loop_module, "_build_body_runtime", spy):
            harness = self._standoff()
        self.assertEqual(len(calls), 1)
        args, kwargs = calls[0]
        self.assertEqual(args[2], "standoff")
        self.assertEqual(Path(kwargs["runtime"]), harness.runtime)
        identity = harness.session.body_runtime.identity
        self.assertEqual((identity["name"], identity["policy"]), ("standoff-band-v1", "standoff"))
        self.assertEqual(identity["config_sha256"], _sha256_path(FRAME_BODY_CONFIG))
        self.assertEqual(identity["effective_scenario_sha256"], _sha256_path(harness.runtime / "scenario_config.json"))
        harness.publish(1)
        manifest = json.loads((harness.runtime / "runs" / "s1-resident1" / "manifest.json").read_text())
        self.assertEqual(manifest["body_planner"]["name"], "standoff-band-v1")
        self.assertEqual(manifest["body_planner"]["config_sha256"], _sha256_path(FRAME_BODY_CONFIG))
        started = journal_kinds(harness, "session_started")[0]
        self.assertEqual(started["body_policy"], "standoff")

    def test_standoff_without_override_file_is_refused(self) -> None:
        with self.assertRaisesRegex(ConfigMismatch, "scenario_config.json"):
            self._standoff(setup_runtime=None)

    def test_standoff_body_scenario_must_equal_override_value_for_value(self) -> None:
        with self.assertRaisesRegex(ConfigMismatch, "value-for-value"):
            self._standoff(body_scenario=BODY_SCENARIO_CONFIG)

        def changed(runtime: Path) -> None:
            document = json.loads(UNTETHERED_SCENARIO.read_text())
            document["sensor"]["retained_frame_count"] = 128
            document["drone"]["initial_altitude_m"] = float(document["drone"]["initial_altitude_m"]) + 1.0
            (runtime / "scenario_config.json").write_text(json.dumps(document))

        with self.assertRaises(ConfigMismatch):
            self._standoff(setup_runtime=changed)

    def test_threshold_default_resolves_default_and_keeps_call_sequence(self) -> None:
        """反例：缺省 threshold、无覆盖文件 → 解析 default，`bind_body_runtime`/`_build_body_runtime` 的
        调用实参与 ACQ-001 通过候选逐字一致（不传 policy/runtime）。"""
        binds, builds = [], []
        original_bind, original_build = loop_module.bind_body_runtime, loop_module._build_body_runtime

        def bind_spy(*args, **kwargs):
            binds.append((args, kwargs))
            return original_bind(*args, **kwargs)

        def build_spy(*args, **kwargs):
            builds.append((args, kwargs))
            return original_build(*args, **kwargs)

        with patch.object(loop_module, "bind_body_runtime", bind_spy), patch.object(
            loop_module, "_build_body_runtime", build_spy
        ):
            harness = Harness(self, responses=[], body=True)
        self.assertFalse((harness.runtime / "scenario_config.json").exists())
        self.assertEqual(len(binds), 1)
        args, kwargs = binds[0]
        self.assertEqual(args, (BODY_PLANNER_CONFIG, BODY_SCENARIO_CONFIG))
        self.assertEqual(set(kwargs), {"live_scenario", "capture_hz", "scenario_id", "ground_plane_y_m"})
        self.assertEqual(kwargs["live_scenario"]["scenario_id"], "deterministic-loop-default")
        self.assertEqual(len(builds), 1)
        self.assertEqual(builds[0][0][2], "threshold")
        self.assertNotIn("runtime", builds[0][1])
        self.assertEqual(harness.session.body_runtime.identity["policy"], "threshold")
        self.assertNotIn("name", harness.session.body_runtime.identity)

    def test_cli_body_policy_closed_set_and_default(self) -> None:
        common = ["run", "--session-id", "x", "--session-root", "s", "--runtime", "r", "--k-receipt", "k", "--backend", "replay"]
        self.assertEqual(build_parser().parse_args(common).body_policy, "threshold")
        self.assertEqual(build_parser().parse_args(common + ["--body-policy", "standoff"]).body_policy, "standoff")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            build_parser().parse_args(common + ["--body-policy", "hold"])


class _CreateTrackerSpy:
    """A5：替身 `create_tracker`——每次构造新常驻插件，并像 `DetAssocTracker.__init__` 一样调用注入的加载器。"""

    def __init__(self) -> None:
        self.created: list[tuple[FakeResident, Any]] = []

    def __call__(self, name, *, resident=False, model_loader=None, **kwargs):
        if not resident or name != "det-assoc-v1" or model_loader is None or kwargs:
            raise AssertionError(f"unexpected create_tracker call: {name!r} {resident!r} {kwargs!r}")
        model_loader(Path("weights/det-assoc-v1.pt"))
        tracker = FakeResident()
        self.created.append((tracker, model_loader))
        return tracker


from typing import Any  # noqa: E402


class Loop2SingleLoadTests(unittest.TestCase):
    """AC-3：单会话模型加载计数 = 1；三类终止分类与重建上限。"""

    def setUp(self) -> None:
        self.loaded: list[Path] = []
        self.spy = _CreateTrackerSpy()
        patcher = patch.object(loop_module, "create_tracker", self.spy)
        patcher.start()
        self.addCleanup(patcher.stop)

    def loader(self, path: Path):
        self.loaded.append(Path(path))
        return object()

    def harness(self, responses=(), **overrides) -> Harness:
        return Harness(
            self,
            responses=[raw(r) if isinstance(r, str) else r for r in responses],
            resident=True,
            tracker_name="det-assoc-v1",
            tracker_factory=None,
            model_loader=self.loader,
            **overrides,
        )

    def _model_cache_files(self, harness: Harness) -> list[dict]:
        return [json.loads(path.read_text()) for path in sorted((harness.runtime / "runs").glob("*/model_cache.json"))]

    def test_duration_reached_is_terminal_without_rebuild(self) -> None:
        harness = self.harness(planned_duration_s=1.0)
        harness.publish(12)
        self.assertEqual((harness.session.state, harness.session.reason), ("TERMINAL", "duration_reached"))
        self.assertEqual((len(self.loaded), len(self.spy.created)), (1, 1))
        harness.publish(3)
        self.assertEqual((len(self.loaded), len(self.spy.created), harness.session.resident_loops_started), (1, 1, 1))
        self.assertEqual(self._model_cache_files(harness), [{"model_loads": 1, "model_requests": 1, "resident_rebuilds": 0, "rebuild_limit": RESIDENT_REBUILD_LIMIT}])

    def test_backend_fatal_is_terminal_without_rebuild(self) -> None:
        harness = self.harness([SelectorError("worker_stuck", "scripted stuck")])
        harness.publish(2)
        harness.ask()
        harness.tick(2)
        self.assertEqual((harness.session.state, harness.session.reason), ("TERMINAL", "backend_fatal"))
        harness.publish(3)
        self.assertEqual((len(self.loaded), len(self.spy.created), harness.session.resident_loops_started), (1, 1, 1))

    def _gap(self, harness: Harness) -> None:
        last = harness.publish(3, tick=False)
        harness.frame_paths(last - 1)[0].unlink()
        harness.tick(1)

    def test_other_seg_end_rebuilds_from_cache_and_third_is_rebuild_limit(self) -> None:
        harness = self.harness()
        harness.publish(2)
        for expected_rebuilds in (1, 2):
            self._gap(harness)
            self.assertIsNone(harness.session.loop)
            self.assertEqual(harness.session.resident_rebuilds, expected_rebuilds)
            harness.publish(1)
            self.assertIsNotNone(harness.session.loop)
            self.assertEqual(harness.session.resident_loops_started, expected_rebuilds + 1)
        self._gap(harness)
        self.assertEqual((harness.session.state, harness.session.reason), ("TERMINAL", "rebuild_limit"))
        self.assertEqual(len(journal_kinds(harness, "resident_rebuild_limit")), 1)
        harness.publish(2)
        self.assertEqual(harness.session.resident_loops_started, 3)
        # 三次构造共用同一个会话缓存加载器，底层权重只加载 1 次。
        self.assertEqual(len(self.spy.created), 3)
        self.assertEqual(len({id(loader.__self__) for _t, loader in self.spy.created}), 1)
        self.assertEqual(len(self.loaded), 1)
        self.assertEqual([row["model_loads"] for row in self._model_cache_files(harness)], [1, 1, 1])
        self.assertEqual([row["resident_rebuilds"] for row in self._model_cache_files(harness)], [0, 1, 2])


class Loop2ContractTests(unittest.TestCase):
    """AC-4（§3.4 闭集、显式 hold 收据、不变式、`JOURNAL_KINDS`）与 AC-17（几何拒绝 cause）。"""

    def harness(self, responses, tracker=None, **kwargs):
        tracker = tracker or FakeResident()
        return Harness(self, responses=[raw(r) for r in responses], resident_tracker=tracker, **kwargs), tracker

    def bind_first(self, harness, tracker):
        harness.publish(2)
        harness.ask()
        harness.tick(2)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        harness.confirm(0)
        harness.tick(1)
        self.assertEqual(harness.session.state, "TRACKING")

    def to_acquiring(self, harness, tracker):
        self.bind_first(harness, tracker)
        tracker.tracked[5] = BOX_A
        tracker.tracked[1] = BOX_B
        harness.publish(1)
        harness.ask("the red car")
        harness.tick(2)
        del tracker.tracked[5]
        tracker.removed.append(5)
        harness.publish(1)
        harness.confirm(0)
        harness.tick(1)

    def explicit_holds(self, harness):
        return [r for r in harness.receipts() if r["channel"] == "body_safety_hold" and r["detail"].get("explicit")]

    def test_explicit_hold_receipts_three_reasons(self) -> None:
        harness, tracker = self.harness([UNIQUE, UNIQUE])
        harness.publish(1)
        holds = self.explicit_holds(harness)
        self.assertEqual([(r["outcome"], r["frame_id"], r["detail"]["reason"]) for r in holds], [("WRITTEN", None, "loop_start")])
        self.to_acquiring(harness, tracker)
        self.assertEqual(harness.session.state, "ACQUIRING")
        self.assertEqual([r["detail"]["reason"] for r in self.explicit_holds(harness)], ["loop_start", "acquiring"])
        tracker.tracked.pop(9, None)
        harness.publish(2 + 5)  # 到位后 M = 5 帧无收养 → acquire_failed
        self.assertEqual((harness.session.state, harness.session.reason), ("LOST", "acquire_failed"))
        self.assertEqual([r["detail"]["reason"] for r in self.explicit_holds(harness)], ["loop_start", "acquiring", "acquire_failed"])
        self.assertEqual(set(EXPLICIT_HOLD_REASONS), {"loop_start", "acquiring", "acquire_failed"})
        with self.assertRaises(ValueError):
            harness.session.publisher.hold_body(reason="search")

    def test_segment_path_explicit_hold_stays_receiptless(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], tracker_results=[tracking()])
        harness.seed()
        harness.publish(2)
        self.assertEqual(self.explicit_holds(harness), [])

    def test_no_written_velocity_on_frames_without_observation(self) -> None:
        harness, tracker = self.harness([UNIQUE], body=True)
        tilt_camera(harness, 40.0)
        self.bind_first(harness, tracker)
        harness.publish(3)
        # 指针 raw LOST（未匹配）：无观测 → hold(no_observation)，不得有 WRITTEN 速度。
        del tracker.tracked[1]
        tracker.lost[1] = BOX_A
        harness.publish(3)
        receipts = harness.receipts()
        observed = {r["frame_id"] for r in receipts if r["channel"] == "observation" and r["outcome"] == "WRITTEN"}
        velocities = [r for r in receipts if r["channel"] == "body_command" and r["outcome"] == "WRITTEN"]
        self.assertTrue(velocities)
        for receipt in velocities:
            self.assertIn(receipt["frame_id"], observed)
        no_observation = [r for r in receipts if r["channel"] == "body_safety_hold" and r["detail"].get("reason") == "no_observation"]
        self.assertTrue(no_observation)
        self.assertEqual(harness.session.state, "TRACKING")  # raw LOST 不升级、不自动重问

    def test_suspected_pointer_ok_and_not_ok_and_verify_paused(self) -> None:
        harness, tracker = self.harness([UNIQUE, NONE, NONE], verify_interval_s=1.0)
        self.bind_first(harness, tracker)
        for _ in range(4):
            harness.publish(1, tick=False)
            harness.tick(1, advance_s=1.1)
            if harness.session.state == "SUSPECTED":
                break
        self.assertEqual((harness.session.state, harness.session.suspect_reason), ("SUSPECTED", "verify_none"))
        calls = len(harness.adapter.calls)
        before = len(harness.receipts())
        harness.publish(1, tick=False)
        harness.tick(1, advance_s=1.1)
        ok_batch = harness.receipts()[before:]
        self.assertTrue(any(r["channel"] == "observation" and r["outcome"] == "WRITTEN" for r in ok_batch))
        del tracker.tracked[1]
        tracker.lost[1] = BOX_A
        before = len(harness.receipts())
        harness.publish(1, tick=False)
        harness.tick(3, advance_s=1.1)
        lost_batch = harness.receipts()[before:]
        self.assertFalse(any(r["channel"] in {"observation", "look_at"} and r["outcome"] == "WRITTEN" for r in lost_batch))
        self.assertEqual(harness.session.state, "SUSPECTED")  # 只由人解除
        self.assertEqual(len(harness.adapter.calls), calls)  # 自动核验暂停

    def test_no_automatic_ask_after_loss(self) -> None:
        harness, tracker = self.harness([UNIQUE, UNIQUE])
        self.to_acquiring(harness, tracker)
        tracker.tracked.pop(9, None)
        harness.publish(2 + 5)
        self.assertEqual(harness.session.state, "LOST")
        queries = len(journal_kinds(harness, "query_submitted"))
        harness.publish(6)
        self.assertEqual(len(journal_kinds(harness, "query_submitted")), queries)
        self.assertEqual(harness.session.state, "LOST")

    def test_journal_kinds_cover_every_call_site_and_reject_unknown(self) -> None:
        tree = ast.parse((PROJECT_ROOT / "controller" / "language_loop.py").read_text(encoding="utf-8"))
        literals = set()
        dynamic = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "_journal":
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    literals.add(first.value)
                else:
                    dynamic.append(ast.unparse(first))
        self.assertTrue(literals)
        self.assertEqual(literals - JOURNAL_KINDS, set())
        # 动态名只来自核心事件（`event.get("event", "core_event")` / `event["event"]`）。
        self.assertEqual(sorted(dynamic), sorted(["event.get('event', 'core_event')", "event['event']"]))
        core_source = (PROJECT_ROOT / "controller" / "resident_core.py").read_text(encoding="utf-8")
        import re  # noqa: PLC0415

        core_events = set(re.findall(r'"event": "([A-Za-z0-9_]+)"', core_source))
        self.assertTrue(core_events)
        self.assertEqual(core_events - set(CORE_EVENT_KINDS), set())
        harness, _tracker = self.harness([UNIQUE])
        with self.assertRaisesRegex(bridge.LanguageBridgeError, "JOURNAL_KINDS"):
            harness.session._journal("made_up_kind")  # noqa: SLF001
        harness.publish(2)
        self.assertEqual({row["kind"] for row in harness.journal()} - JOURNAL_KINDS, set())

    def test_geometry_rejected_is_its_own_cause_not_slew_timeout(self) -> None:
        """AC-17（ACQ R1-4 承接）：几何拒绝 → `acquire_failed` cause `geometry_rejected`，不产生 `slew_timeout`。"""
        harness, tracker = self.harness([UNIQUE, UNIQUE])

        def reject(*_args, **_kwargs):
            raise GeometryRejected("ray does not meet the ground plane")

        with patch.object(loop_module, "box_ground_intersection", reject):
            self.to_acquiring(harness, tracker)
        self.assertEqual((harness.session.state, harness.session.reason), ("LOST", "acquire_failed"))
        self.assertEqual(harness.session.designation["acquire"]["cause"], "geometry_rejected")
        failed = journal_kinds(harness, "acquire_failed")
        self.assertEqual([row["cause"] for row in failed], ["geometry_rejected"])
        self.assertNotIn("slew_timeout", json.dumps(harness.journal()))
        self.assertIn("geometry_rejected", bridge.STATE_REASONS)
        self.assertIn("rebuild_limit", bridge.STATE_REASONS)
        self.assertEqual([r["detail"]["reason"] for r in self.explicit_holds(harness)][-1], "acquire_failed")


class Loop2DelayTests(unittest.TestCase):
    """AC-5：逐次 Δ 呈现挂起、意图标签与 `frames_processed.metadata_sha256`。"""

    def harness(self, responses, **kwargs):
        tracker = kwargs.pop("tracker", None) or FakeResident()
        return Harness(self, responses=[raw(r) for r in responses], resident_tracker=tracker, **kwargs), tracker

    def ask(self, harness, delay_s=None, intent=None, surface="the red car"):
        return loop2_request(harness, "ask", delay_s=delay_s, intent=intent, instruction=bridge.parse_instruction(surface))

    def designate_rows(self, harness):
        return [row for row in harness.results() if row.get("purpose") == "designate" and row.get("status") in {"unique", "ambiguous"}]

    def test_presentation_waits_exactly_delta_and_worker_is_idle(self) -> None:
        harness, _ = self.harness([UNIQUE])
        harness.publish(2)
        self.ask(harness, delay_s=2.0, intent="red_car")
        harness.tick(1)  # 回包到达
        arrived = journal_kinds(harness, "result_arrived")
        self.assertEqual(len(arrived), 1)
        self.assertEqual((arrived[0]["status"], arrived[0]["delay_s"]), ("unique", 2.0))
        self.assertIsNotNone(arrived[0]["head_frame_id"])
        self.assertEqual(harness.session.state, "QUERYING")
        self.assertEqual(self.designate_rows(harness), [])
        self.assertIsNone(harness.session.candidate_presented_monotonic_s)
        self.assertFalse(harness.session.worker.busy)
        self.assertIsNone(harness.session.worker.in_flight)
        calls = len(harness.adapter.calls)
        harness.tick(3, advance_s=0.6)  # 挂起中：worker 空闲、不重发
        self.assertEqual((harness.session.state, len(harness.adapter.calls)), ("QUERYING", calls))
        receipt = loop2_request(harness, "confirm", ticks=1, candidate_index=0, token="none")
        self.assertEqual((receipt["outcome"], journal_kinds(harness, "receipt")[-1]["detail"]), ("REQUEST_INVALID", "confirm_in_QUERYING"))
        harness.clock.advance(2.0 - 0.6 * 3 - 0.05)
        harness.session.tick()
        presented = journal_kinds(harness, "result_presented")
        self.assertEqual(len(presented), 1)
        self.assertAlmostEqual(presented[0]["at_monotonic_s"] - arrived[0]["at_monotonic_s"], 2.0, places=9)
        self.assertEqual(presented[0]["delay_s"], 2.0)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        self.assertEqual(len(self.designate_rows(harness)), 1)
        self.assertEqual(harness.session.candidate_presented_monotonic_s, presented[0]["at_monotonic_s"])
        self.assertEqual(journal_kinds(harness, "receipt")[0]["intent"], "red_car")

    def test_zero_delay_presents_in_the_same_tick(self) -> None:
        harness, _ = self.harness([UNIQUE])
        harness.publish(2)
        self.ask(harness)
        harness.tick(1)
        arrived, presented = journal_kinds(harness, "result_arrived"), journal_kinds(harness, "result_presented")
        self.assertEqual((len(arrived), len(presented)), (1, 1))
        self.assertEqual(arrived[0]["at_monotonic_s"], presented[0]["at_monotonic_s"])
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        self.assertEqual(journal_kinds(harness, "receipt")[0]["delay_s"], 0.0)

    def test_failures_and_retries_are_not_held(self) -> None:
        harness, _ = self.harness([NONE, BROKEN, UNIQUE])
        harness.publish(2)
        self.ask(harness, delay_s=3.0)
        for _ in range(3):
            harness.publish(1, tick=False)
            harness.tick(1)
        arrived = journal_kinds(harness, "result_arrived")
        self.assertEqual([row["status"] for row in arrived], ["unique"])
        statuses = [row["status"] for row in harness.results() if row.get("purpose") == "designate"]
        self.assertEqual(statuses[:2], ["none", "parse_failed"])
        self.assertEqual(harness.session.state, "QUERYING")

    def test_new_ask_while_presentation_pending_discards_without_result_row(self) -> None:
        harness, _ = self.harness([UNIQUE, UNIQUE_FAR])
        harness.publish(2)
        self.ask(harness, delay_s=4.0)
        harness.tick(1)
        first = journal_kinds(harness, "result_arrived")[0]["query_id"]
        self.ask(harness)
        harness.tick(1)
        discarded = journal_kinds(harness, "presentation_discarded")
        self.assertEqual([(row["query_id"], row["reason"]) for row in discarded], [(first, "epoch_changed")])
        self.assertNotIn(first, [row["query_id"] for row in self.designate_rows(harness)])
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")

    def test_respecify_while_presentation_pending_discards_and_carries_delay_intent(self) -> None:
        harness, _ = self.harness([UNIQUE, UNIQUE])
        harness.publish(2)
        self.ask(harness, delay_s=4.0)
        harness.tick(1)
        loop2_request(harness, "respecify", delay_s=1.0, intent="Sedan_01", instruction=bridge.parse_instruction("the red car"))
        harness.tick(1)
        self.assertEqual(len(journal_kinds(harness, "presentation_discarded")), 1)
        receipt = [row for row in journal_kinds(harness, "receipt") if row["receipt"]["action"] == "respecify"][0]
        self.assertEqual((receipt["receipt"]["outcome"], receipt["intent"], receipt["delay_s"]), ("APPLIED", "Sedan_01", 1.0))
        self.assertEqual(harness.session.state, "QUERYING")
        harness.tick(1, advance_s=1.0)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        self.assertEqual(journal_kinds(harness, "result_presented")[-1]["delay_s"], 1.0)

    def test_stop_while_presentation_pending_discards_without_result_row(self) -> None:
        harness, _ = self.harness([UNIQUE])
        harness.publish(2)
        self.ask(harness, delay_s=4.0)
        harness.tick(1)
        loop2_request(harness, "stop")
        self.assertEqual(harness.session.state, "TERMINAL")
        self.assertEqual([row["reason"] for row in journal_kinds(harness, "presentation_discarded")], ["epoch_changed"])
        self.assertEqual(self.designate_rows(harness), [])
        self.assertEqual(journal_kinds(harness, "result_presented"), [])

    def test_delay_crossing_confirmation_checkpoint_uses_existing_reason(self) -> None:
        harness, _ = self.harness([UNIQUE])
        harness.publish(2)
        self.ask(harness, delay_s=DELAY_MAX_S)
        harness.tick(1)
        harness.tick(1, advance_s=DELAY_MAX_S)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        harness.clock.advance(5.0)  # 提交起 > t_ret + T_conf（K 判定代码与 Δ = 0 相同）
        harness.confirm(0)
        stale = [row for row in harness.results() if row.get("status") == "stale_rejected"]
        self.assertEqual([row["reject_reason"] for row in stale], ["wall_deadline_exceeded"])
        confirm_receipt = [row for row in journal_kinds(harness, "receipt") if row["receipt"]["action"] == "confirm"][-1]
        self.assertEqual((confirm_receipt["detail"], confirm_receipt["delay_injected_s"]), ("wall_deadline_exceeded", DELAY_MAX_S))

    def test_delay_outside_closed_interval_or_bad_intent_is_rejected(self) -> None:
        harness, _ = self.harness([UNIQUE])
        harness.publish(1)
        for delay, intent, reason in ((8.5, None, "delay_out_of_range"), (-0.1, None, "delay_out_of_range"),
                                      ("2", None, "invalid_delay"), (True, None, "invalid_delay"), (1.0, "", "invalid_intent")):
            receipt = loop2_request(harness, "ask", delay_s=delay, intent=intent, instruction=bridge.parse_instruction("the red car"))
            self.assertEqual(receipt["outcome"], "REQUEST_INVALID")
            self.assertEqual(journal_kinds(harness, "receipt")[-1]["detail"], reason)
        self.assertEqual(harness.session.state, "IDLE")
        common = ["ask", "--session-id", "s", "--runtime", "r", "the red car"]
        self.assertEqual(build_parser().parse_args(common + ["--delay-s", "8"]).delay_s, 8.0)
        for bad in ("8.01", "-1", "nan", "x"):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                build_parser().parse_args(common + ["--delay-s", bad])
        with self.assertRaises(bridge.LanguageBridgeError):
            send_request(Path(tempfile.gettempdir()), session_id="s", action="confirm", delay_s=1.0, candidate_index=0, token="t")

    def test_intent_never_reaches_queries_or_decisions(self) -> None:
        runs = {}
        for intent in (None, "red_car"):
            harness, _ = self.harness([UNIQUE])
            harness.publish(2)
            self.ask(harness, intent=intent)
            harness.tick(1)
            runs[intent] = harness
        plain, tagged = runs[None], runs["red_car"]
        self.assertEqual([call[2:] for call in plain.adapter.calls], [call[2:] for call in tagged.adapter.calls])
        self.assertEqual(plain.session.current_instruction, tagged.session.current_instruction)
        self.assertEqual(plain.session.state, tagged.session.state)
        rows = [row for row in tagged.journal() if "red_car" in json.dumps(row)]
        self.assertEqual({row["kind"] for row in rows}, {"receipt"})
        self.assertNotIn("red_car", tagged.session.results_path.read_text())
        self.assertNotIn("red_car", (tagged.runtime / "tracker_state.json").read_text())
        designate = loop_module.designate_options
        self.assertEqual(designate(None), (0.0, None, None))

    def test_frames_processed_carries_ordered_metadata_digests(self) -> None:
        harness, _ = self.harness([])
        harness.publish(1)
        harness.publish(3, tick=False)
        harness.tick(1)
        rows = journal_kinds(harness, "frames_processed")
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(len(row["metadata_sha256"]), len(row["frame_ids"]))
            for frame_id, digest, missing in zip(row["frame_ids"], row["metadata_sha256"], row["metadata_sha256_missing_reason"]):
                self.assertEqual(digest, _sha256_path(harness.frame_paths(frame_id)[1]))
                self.assertIsNone(missing)
        digests, missing = harness.session._metadata_digests([0, 999_999])  # noqa: SLF001
        self.assertEqual(digests[0], _sha256_path(harness.frame_paths(0)[1]))
        self.assertEqual((digests[1], missing[1]), (None, "file_missing"))



class Loop2ScorerProductionSequenceTests(unittest.TestCase):
    """C1 返工 PR-3/PR-4：用真实 `LanguageSession` 生产出的会话 JSONL/results 喂评分器（不是手写夹具），
    核对 AC-8 修订 1（常驻代内编号）与修订 2（追平终止后的 `designation_unavailable` 归原 e_s）。"""

    def score(self, harness: Harness) -> dict:
        from tools.eng_loop2 import analyze_play as ap  # noqa: PLC0415 — 离线评分器只在测试里调用

        unity = harness.root / "unity-empty"
        unity.mkdir(exist_ok=True)
        paths = ap.ArchivePaths(
            session_dir=harness.session.journal_path.parent,
            unity_dir=unity,
            runs_dir=harness.runtime / "runs",
            scenario_copy=None,
            reference_scenario=ap.REPO_ROOT / "config" / "scenario.default.json",
        )
        return ap.score_archive(paths, geometry={"instances": [], "source_scenario_sha256": None})

    def test_confirm_then_catchup_terminal_keeps_unavailable_with_its_sample(self) -> None:
        harness = Harness(self, responses=[raw(UNIQUE)], resident_tracker=FakeResident(), planned_duration_s=0.6)
        harness.publish(2)
        harness.ask()
        harness.tick(2)
        self.assertEqual(harness.session.state, "AWAITING_CONFIRMATION")
        harness.publish(4, tick=False)  # 确认前积压帧：追平时常驻段时长到期
        harness.confirm(0)
        harness.tick(1)
        self.assertEqual((harness.session.state, harness.session.reason), ("TERMINAL", "duration_reached"))
        rows = harness.journal()
        confirm = next(r for r in rows if r["kind"] == "receipt" and r["receipt"]["action"] == "confirm")
        unavailable = next(r for r in rows if r["kind"] == "designation_unavailable")
        self.assertEqual(unavailable["reason"], "session_terminal")
        self.assertEqual(unavailable["epoch"], confirm["epoch"] + 1, "生产序列：stop() 先增 epoch 再写不可用行")
        report = self.score(harness)
        (sample,) = report["samples"]
        self.assertEqual(sample["funnel"], "INTERRUPTED(designation_unavailable, session_terminal)")
        self.assertEqual(sample["epoch"], confirm["epoch"])
        self.assertEqual(report["attribution_conflicts"], {})
        self.assertNotIn("designation_unavailable", report["unattributed_rows"])
        self.assertEqual(report["designation_unavailable_reattributed_to_confirm_epoch"], 1)

    def test_rebuilt_generation_reuses_designation_id_without_c6_or_cross_pointer(self) -> None:
        made: list[FakeResident] = []

        def fresh() -> FakeResident:
            made.append(FakeResident())
            return made[-1]

        harness = Harness(self, responses=[raw(UNIQUE), raw(UNIQUE)], resident_tracker=FakeResident(),
                          tracker_factory=fresh)
        harness.publish(2)
        harness.ask()
        harness.tick(2)
        harness.confirm(0)
        harness.tick(1)
        self.assertEqual(harness.session.state, "TRACKING")
        last = harness.publish(3, tick=False)
        harness.frame_paths(last - 1)[0].unlink()  # 帧缺口 → seg_end → 常驻重建（新一代 ResidentCore）
        harness.tick(1)
        harness.publish(2)
        harness.ask()
        harness.tick(2)
        harness.confirm(0)
        harness.tick(1)
        self.assertEqual((harness.session.state, len(made)), ("TRACKING", 2))
        designations = [r["designation"]["designation_id"] for r in harness.journal() if r["kind"] == "designation"]
        self.assertEqual(designations, [1, 1], "两代各自从 1 编号（生产行为）")
        report = self.score(harness)
        self.assertEqual(report["attribution_conflicts"], {})
        first, second = report["samples"]
        self.assertEqual((first["funnel"], second["funnel"]), ("BOUND_DIRECT(bound)", "BOUND_DIRECT(bound)"))
        self.assertEqual([e["track_id"] for e in first["pointer_epochs"]], ["s1-t1"])
        self.assertEqual([e["track_id"] for e in second["pointer_epochs"]], ["s1-t2"])
        self.assertEqual(report["unattributed_rows"].get("pointer_bound"), None)
        self.assertEqual(report["pointer_bound_claim_conflicts"], 0)


if __name__ == "__main__":
    unittest.main()
