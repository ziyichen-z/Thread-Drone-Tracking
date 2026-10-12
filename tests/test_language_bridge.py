"""P1-ENG-LOOP-001 AC-1：三个桥文件的 schema、闭集、可空规则、原子发布与两把锁。

纯标准库、无 GPU、只写临时目录。
"""

import json
import os
from pathlib import Path
import tempfile
import unittest

from controller.language_bridge import (
    ACTIONS,
    BRIDGE_EXPIRES_AFTER_S,
    INCONCLUSIVE_REASONS,
    INSTRUCTION_CLASSES,
    INSTRUCTION_COLORS,
    LANGUAGE_REQUEST_SCHEMA,
    LANGUAGE_RESULT_SCHEMA,
    OUTCOMES,
    REJECT_REASONS,
    REQUEST_FILE,
    REQUEST_LOCK_FILE,
    RESULT_FILE,
    RESULT_STATUS,
    SESSION_LOCK_FILE,
    SESSION_STATES,
    STATE_REASONS,
    TRACKER_STATE_FILE,
    TRACKER_STATE_SCHEMA,
    VERIFY_VERDICTS,
    Instruction,
    InstructionUnsupported,
    LanguageBridgeError,
    SessionSlotBusy,
    WriterBusy,
    acquire_session_lock,
    acquire_writer_lock,
    clear_dead_writer_lock,
    instruction_from_payload,
    parse_instruction,
    read_request,
    read_result,
    read_tracker_state,
    release_session_lock,
    release_writer_lock,
    result_payload,
    tracker_state_payload,
    write_request,
    write_result,
    write_tracker_state,
)


def _dead(pid: int) -> bool:
    return False


def _alive(pid: int) -> bool:
    return True


class TempRuntimeCase(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.runtime = Path(self._directory.name)

    def tearDown(self) -> None:
        self._directory.cleanup()


class InstructionGrammarTests(unittest.TestCase):
    """§3.7：闭集文法解析并重新序列化；自由文本一律拒绝。"""

    def test_g1_g2_g4_round_trip(self) -> None:
        g1 = parse_instruction("The SUV")
        self.assertEqual(g1.surface, "the suv")
        self.assertEqual(g1.target_class, "suv")
        self.assertIsNone(g1.color)
        self.assertFalse(g1.g4)

        g2 = parse_instruction("the red car")
        self.assertEqual(g2.surface, "the red car")
        self.assertEqual(g2.color, "red")
        self.assertFalse(g2.g4)

        g4 = parse_instruction(
            "the suv to the viewer's left of the pickup truck"
        )
        self.assertEqual(
            g4.surface, "the suv to the viewer's left of the pickup truck"
        )
        self.assertEqual(g4.target_class, "suv")
        self.assertEqual(g4.side, "left")
        self.assertEqual(g4.reference_class, "pickup truck")
        self.assertTrue(g4.g4)

    def test_multiword_classes_beat_their_suffix(self) -> None:
        for name in ("container truck", "pickup truck", "police car"):
            parsed = parse_instruction(f"the {name}")
            self.assertEqual(parsed.target_class, name)

    def test_every_class_and_color_is_accepted(self) -> None:
        for name in INSTRUCTION_CLASSES:
            self.assertEqual(parse_instruction(f"the {name}").target_class, name)
        for color in INSTRUCTION_COLORS:
            self.assertEqual(parse_instruction(f"the {color} car").color, color)

    def test_free_text_is_rejected(self) -> None:
        for text in (
            "",
            "the vehicle",
            "red car",
            "the car near the tree",
            "the orange car",
            "the car to the viewer's up of the bus",
            "find the red car please",
        ):
            with self.assertRaises(InstructionUnsupported):
                parse_instruction(text)

    def test_payload_round_trip_and_disagreement(self) -> None:
        instruction = parse_instruction("the red car")
        restored = instruction_from_payload(instruction.payload())
        self.assertEqual(restored, instruction)
        tampered = dict(instruction.payload())
        tampered["color"] = "blue"
        with self.assertRaises(InstructionUnsupported):
            instruction_from_payload(tampered)
        missing_relation = dict(
            parse_instruction(
                "the car to the viewer's right of the bus"
            ).payload()
        )
        missing_relation["relation"] = None
        with self.assertRaises(InstructionUnsupported):
            instruction_from_payload(missing_relation)


class RequestBridgeTests(TempRuntimeCase):
    """(a) `language_request.json`：头、闭集、必填与非法值的 fail-closed。"""

    def test_write_and_read_round_trip(self) -> None:
        path = write_request(
            self.runtime,
            session_id="s1",
            request_id="r1",
            action="ask",
            instruction=parse_instruction("the red car"),
        )
        self.assertEqual(path.name, REQUEST_FILE)
        document = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(document["protocol"], LANGUAGE_REQUEST_SCHEMA)
        for field in ("command_id", "issued_unix_s", "expires_after_s"):
            self.assertIn(field, document)
        self.assertEqual(document["expires_after_s"], BRIDGE_EXPIRES_AFTER_S)
        envelope = read_request(self.runtime)
        self.assertIsNotNone(envelope)
        assert envelope is not None
        self.assertIsNone(envelope.invalid_reason)
        self.assertEqual(envelope.action, "ask")
        self.assertEqual(envelope.session_id, "s1")
        self.assertEqual(envelope.request_id, "r1")
        assert envelope.instruction is not None
        self.assertEqual(envelope.instruction.surface, "the red car")

    def test_missing_slot_reads_as_none(self) -> None:
        self.assertIsNone(read_request(self.runtime))

    def test_every_action_is_writable(self) -> None:
        # IR-3：旧动作闭集与接受基线运行时逐位比较，仅末尾追加 click。
        from tools.eng_capture.common import accepted_base_literal  # noqa: PLC0415

        base = accepted_base_literal("controller/language_bridge.py", "ACTIONS")
        if base is not None:
            self.assertEqual(ACTIONS, tuple(base) + ("click",))
        self.assertEqual(ACTIONS[-1], "click")
        self.assertEqual(len(ACTIONS), len(set(ACTIONS)))
        for index, action in enumerate(ACTIONS):
            write_request(
                self.runtime,
                session_id="s1",
                request_id=f"r{index}",
                action=action,
                instruction=(
                    parse_instruction("the bus") if action == "ask" else None
                ),
                candidate_index=0 if action == "confirm" else None,
                token="t" if action in {"confirm", "reject", "release"} else None,
                # P1-ENG-CAPTURE-001 C7：`click` 动作随附点击字段（其余动作不带，请求字节不变）。
                click={"x_px": 1.0, "y_px": 2.0, "frame_id": 3, "image_sha256": "a" * 64} if action == "click" else None,
            )
            envelope = read_request(self.runtime)
            assert envelope is not None
            self.assertEqual(envelope.action, action)
            self.assertIsNone(envelope.invalid_reason)

    def test_write_rejects_missing_required_fields(self) -> None:
        with self.assertRaises(LanguageBridgeError):
            write_request(
                self.runtime, session_id="s1", request_id="r1", action="ask"
            )
        with self.assertRaises(LanguageBridgeError):
            write_request(
                self.runtime, session_id="s1", request_id="r1", action="confirm"
            )
        with self.assertRaises(LanguageBridgeError):
            write_request(
                self.runtime, session_id="", request_id="r1", action="stop"
            )
        with self.assertRaises(LanguageBridgeError):
            write_request(
                self.runtime, session_id="s1", request_id="r1", action="launch"
            )

    def test_unknown_action_reads_as_invalid_not_raise(self) -> None:
        write_request(
            self.runtime, session_id="s1", request_id="r1", action="stop"
        )
        path = self.runtime / REQUEST_FILE
        document = json.loads(path.read_text(encoding="utf-8"))
        document["request"]["action"] = "self_destruct"
        path.write_text(json.dumps(document), encoding="utf-8")
        envelope = read_request(self.runtime)
        assert envelope is not None
        self.assertEqual(envelope.invalid_reason, "unknown_action")
        # AC-1 修订 1：仍可回执，因为身份可信。
        self.assertTrue(envelope.addressable)
        self.assertEqual(envelope.session_id, "s1")
        self.assertEqual(envelope.request_id, "r1")
        # 写入头照样带出：会话靠它区分槽内残留与同 id 重新写入（R1@K1K3 F2）。
        self.assertEqual(envelope.command_id, document["command_id"])
        self.assertEqual(envelope.issued_unix_s, document["issued_unix_s"])

    def test_structural_damage_is_not_addressable(self) -> None:
        path = self.runtime / REQUEST_FILE
        path.write_text("{not json", encoding="utf-8")
        envelope = read_request(self.runtime)
        assert envelope is not None
        self.assertEqual(envelope.invalid_reason, "malformed_json")
        self.assertFalse(envelope.addressable)

        path.write_text(
            json.dumps({"protocol": "other/v1", "request": {}}), encoding="utf-8"
        )
        envelope = read_request(self.runtime)
        assert envelope is not None
        self.assertEqual(envelope.invalid_reason, "schema_mismatch")

    def test_free_text_instruction_in_slot_is_flagged(self) -> None:
        write_request(
            self.runtime,
            session_id="s1",
            request_id="r1",
            action="ask",
            instruction=parse_instruction("the bus"),
        )
        path = self.runtime / REQUEST_FILE
        document = json.loads(path.read_text(encoding="utf-8"))
        document["request"]["instruction"]["surface"] = "the shiny vehicle"
        path.write_text(json.dumps(document), encoding="utf-8")
        envelope = read_request(self.runtime)
        assert envelope is not None
        self.assertEqual(envelope.invalid_reason, "instruction_unsupported")

    def test_negative_candidate_index_is_flagged(self) -> None:
        write_request(
            self.runtime,
            session_id="s1",
            request_id="r1",
            action="confirm",
            candidate_index=0,
            token="tok",
        )
        path = self.runtime / REQUEST_FILE
        document = json.loads(path.read_text(encoding="utf-8"))
        document["request"]["candidate_index"] = -1
        path.write_text(json.dumps(document), encoding="utf-8")
        envelope = read_request(self.runtime)
        assert envelope is not None
        self.assertEqual(envelope.invalid_reason, "invalid_candidate_index")


def _candidate(index: int) -> dict:
    return {
        "index": index,
        "bbox_xywh_norm": [0.1, 0.2, 0.3, 0.4],
        "bbox_2d_1000": [100, 200, 400, 600],
        "clipped": False,
    }


def _model_block() -> dict:
    return {
        "backend": "replay",
        "model_form": "c2-adapter",
        "base_repo_revision": "89644892",
        "weights_sha256": "4044dd4f",
        "prompt_template_sha256": "aaaa",
        "vocab_sha256": "bbbb",
        "g4_segment_sha256": None,
        "device": "cpu",
        "finish_reason": "stop",
        "gen_tokens": 24,
    }


class ResultBridgeTests(TempRuntimeCase):
    """(b) `language_result.json`：九状态、可空规则、候选基数与 verify 块。"""

    def _designate(self, **overrides):
        base = dict(
            query_id="s1-q1",
            result_id="res-1",
            request_id="r1",
            epoch=1,
            segment_index=None,
            attempt=1,
            attempt_limit=3,
            purpose="designate",
            status="unique",
            frame_id=12,
            frame_sha256="a" * 64,
            capture_monotonic_s=1.5,
            capture_unix_s=1_700_000_000.0,
            query_unix_s=1_700_000_000.5,
            candidates=[_candidate(0)],
            model=_model_block(),
            latency_ms=1234.5,
            frames_late=2,
            k_ret=11,
            wall_elapsed_s=2.4,
        )
        base.update(overrides)
        return result_payload(**base)

    def test_round_trip_and_atomic_publish(self) -> None:
        path = write_result(self.runtime, self._designate())
        self.assertEqual(path.name, RESULT_FILE)
        document = read_result(self.runtime)
        assert document is not None
        self.assertEqual(document["protocol"], LANGUAGE_RESULT_SCHEMA)
        body = document["result"]
        self.assertEqual(body["status"], "unique")
        self.assertEqual(len(body["candidates"]), 1)
        self.assertEqual(body["model"]["backend"], "replay")
        self.assertIsNone(body["verify"])

    def test_all_nine_statuses_are_expressible(self) -> None:
        for status in RESULT_STATUS:
            if status in {"unique", "ambiguous"}:
                candidates = [_candidate(0)] if status == "unique" else [
                    _candidate(0),
                    _candidate(1),
                ]
                payload = self._designate(status=status, candidates=candidates)
            elif status == "stale_rejected":
                payload = self._designate(
                    status=status, candidates=[], reject_reason="frames_late_exceeded"
                )
            elif status == "retry_exhausted":
                payload = self._designate(
                    status=status,
                    candidates=[],
                    last_status="none",
                    last_reject_reason=None,
                )
            elif status in {"no_new_frame", "instruction_unsupported"}:
                payload = self._designate(
                    status=status,
                    candidates=[],
                    frame_id=None,
                    frame_sha256=None,
                    capture_monotonic_s=None,
                    capture_unix_s=None,
                    frames_late=None,
                )
            else:
                payload = self._designate(status=status, candidates=[])
            self.assertEqual(payload["result"]["status"], status)

    def test_candidate_cardinality_is_enforced(self) -> None:
        with self.assertRaises(LanguageBridgeError):
            self._designate(status="unique", candidates=[_candidate(0), _candidate(1)])
        with self.assertRaises(LanguageBridgeError):
            self._designate(status="ambiguous", candidates=[_candidate(0)])
        with self.assertRaises(LanguageBridgeError):
            self._designate(
                status="ambiguous",
                candidates=[_candidate(index) for index in range(9)],
            )
        with self.assertRaises(LanguageBridgeError):
            self._designate(status="none", candidates=[_candidate(0)])

    def test_candidate_index_must_match_position(self) -> None:
        skewed = [_candidate(0), _candidate(5)]
        with self.assertRaises(LanguageBridgeError):
            self._designate(status="ambiguous", candidates=skewed)

    def test_frame_fields_are_all_or_nothing(self) -> None:
        with self.assertRaises(LanguageBridgeError):
            self._designate(
                status="no_new_frame",
                candidates=[],
                frame_id=None,
                frames_late=None,
            )
        with self.assertRaises(LanguageBridgeError):
            self._designate(
                status="no_new_frame",
                candidates=[],
                frame_id=None,
                frame_sha256=None,
                capture_monotonic_s=None,
                capture_unix_s=None,
                frames_late=4,
            )

    def test_reject_reason_rules(self) -> None:
        with self.assertRaises(LanguageBridgeError):
            self._designate(status="stale_rejected", candidates=[])
        with self.assertRaises(LanguageBridgeError):
            self._designate(
                status="unique", reject_reason="timeout"
            )
        with self.assertRaises(LanguageBridgeError):
            self._designate(
                status="stale_rejected",
                candidates=[],
                reject_reason="not_a_reason",
            )
        for reason in REJECT_REASONS:
            payload = self._designate(
                status="stale_rejected", candidates=[], reject_reason=reason
            )
            self.assertEqual(payload["result"]["reject_reason"], reason)

    def test_last_status_belongs_to_retry_exhausted_only(self) -> None:
        with self.assertRaises(LanguageBridgeError):
            self._designate(status="none", candidates=[], last_status="none")
        with self.assertRaises(LanguageBridgeError):
            self._designate(status="retry_exhausted", candidates=[])

    def test_verify_block_rules(self) -> None:
        verify = {
            "paired_frame_id": 30,
            "tracker_box_at_frame": [0.1, 0.1, 0.2, 0.2],
            "iou": 0.72,
            "verdict": "consistent",
            "inconclusive_reason": None,
            "consecutive_alert": 0,
            "alert_kind": None,
        }
        payload = self._designate(purpose="verify", verify=verify)
        self.assertEqual(payload["result"]["verify"]["verdict"], "consistent")
        with self.assertRaises(LanguageBridgeError):
            self._designate(purpose="verify")
        with self.assertRaises(LanguageBridgeError):
            self._designate(purpose="designate", verify=verify)
        for verdict in VERIFY_VERDICTS:
            self._designate(
                purpose="verify", verify={**verify, "verdict": verdict}
            )
        with self.assertRaises(LanguageBridgeError):
            self._designate(
                purpose="verify", verify={**verify, "verdict": "probably_fine"}
            )
        # AC-16 修订 2：结果包的原因闭集恰是四个；写死期望集合，不自循环常量。
        self.assertEqual(
            set(INCONCLUSIVE_REASONS),
            {"stale", "frame_identity", "parse_failed", "backend_error"},
        )
        for reason in INCONCLUSIVE_REASONS:
            self._designate(
                purpose="verify",
                verify={
                    **verify,
                    "verdict": "inconclusive",
                    "inconclusive_reason": reason,
                },
            )
        # 三个发起前跳过的原因已移出闭集：写与读两侧都必须拒绝。
        for reason in ("same_frame", "no_tracker_box", "tracking_lag", "felt_wrong"):
            with self.subTest(reason=reason):
                with self.assertRaises(LanguageBridgeError):
                    self._designate(
                        purpose="verify",
                        verify={
                            **verify,
                            "verdict": "inconclusive",
                            "inconclusive_reason": reason,
                        },
                    )

    def test_reader_fails_closed_on_a_pre_dispatch_skip_reason(self) -> None:
        verify = {
            "paired_frame_id": 30,
            "tracker_box_at_frame": None,
            "iou": None,
            "verdict": "inconclusive",
            "inconclusive_reason": "stale",
            "consecutive_alert": 0,
            "alert_kind": None,
        }
        write_result(self.runtime, self._designate(purpose="verify", verify=verify))
        path = self.runtime / RESULT_FILE
        document = json.loads(path.read_text(encoding="utf-8"))
        document["result"]["verify"]["inconclusive_reason"] = "same_frame"
        path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(LanguageBridgeError):
            read_result(self.runtime)

    def test_the_skip_reasons_live_in_their_own_closed_set(self) -> None:
        from controller.language_bridge import VERIFY_SKIP_REASONS

        self.assertEqual(
            set(VERIFY_SKIP_REASONS), {"same_frame", "no_tracker_box", "tracking_lag"}
        )
        self.assertEqual(set(VERIFY_SKIP_REASONS) & set(INCONCLUSIVE_REASONS), set())

    def test_the_pairing_unavailable_reasons_live_in_a_third_closed_set(self) -> None:
        """AC-16 修订 3：配对不可用有自己的五值闭集，不扩充另外两个（写死期望集合）。"""
        from controller.language_bridge import (
            PAIRING_UNAVAILABLE_REASONS,
            VERIFY_SKIP_REASONS,
        )

        self.assertEqual(
            set(PAIRING_UNAVAILABLE_REASONS),
            {
                "snapshot_missing",
                "image_identity_changed",
                "bundle_missing",
                "metadata_invalid",
                "latest_unreadable",
            },
        )
        self.assertEqual(
            set(PAIRING_UNAVAILABLE_REASONS) & set(VERIFY_SKIP_REASONS), set()
        )
        # 它也不是结果包的原因：读写两侧都必须拒绝。
        verify = {
            "paired_frame_id": 30,
            "tracker_box_at_frame": None,
            "iou": None,
            "verdict": "inconclusive",
            "inconclusive_reason": "stale",
            "consecutive_alert": 0,
            "alert_kind": None,
        }
        for reason in PAIRING_UNAVAILABLE_REASONS:
            with self.subTest(reason=reason):
                with self.assertRaises(LanguageBridgeError):
                    self._designate(
                        purpose="verify",
                        verify={**verify, "inconclusive_reason": reason},
                    )

    def test_reader_fails_closed_on_unknown_status(self) -> None:
        write_result(self.runtime, self._designate())
        path = self.runtime / RESULT_FILE
        document = json.loads(path.read_text(encoding="utf-8"))
        document["result"]["status"] = "probably_unique"
        path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(LanguageBridgeError):
            read_result(self.runtime)

    def test_reader_fails_closed_on_unknown_verdict(self) -> None:
        verify = {
            "paired_frame_id": 30,
            "tracker_box_at_frame": None,
            "iou": None,
            "verdict": "inconclusive",
            "inconclusive_reason": "stale",
            "consecutive_alert": 1,
            "alert_kind": "lost",
        }
        write_result(self.runtime, self._designate(purpose="verify", verify=verify))
        path = self.runtime / RESULT_FILE
        document = json.loads(path.read_text(encoding="utf-8"))
        document["result"]["verify"]["verdict"] = "maybe"
        path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(LanguageBridgeError):
            read_result(self.runtime)

    def test_unknown_backend_or_form_is_rejected(self) -> None:
        with self.assertRaises(LanguageBridgeError):
            self._designate(model={**_model_block(), "backend": "grpc"})
        with self.assertRaises(LanguageBridgeError):
            self._designate(model={**_model_block(), "model_form": "c3"})

    def test_b3_candidates_model_block_pairs_only_with_detector_tracks(self) -> None:
        """P1-ENG-ACQ-001 AC-21（B3）：`candidates`/`detector-tracks` 入闭集且只能成对；原 3×3 组合不变。"""
        candidates = {**_model_block(), "backend": "candidates", "model_form": "detector-tracks"}
        write_result(self.runtime, self._designate(model=candidates))
        document = read_result(self.runtime)
        assert document is not None
        self.assertEqual(
            (document["result"]["model"]["backend"], document["result"]["model"]["model_form"]),
            ("candidates", "detector-tracks"),
        )
        for backend in ("local-hf", "http", "replay"):
            for form in ("c2-merged", "c2-adapter", "base"):
                with self.subTest(backend=backend, form=form):
                    self._designate(model={**_model_block(), "backend": backend, "model_form": form})
        for backend, form in [("candidates", "c2-merged"), ("candidates", "base"),
                              ("http", "detector-tracks"), ("replay", "detector-tracks"),
                              ("local-hf", "detector-tracks")]:
            with self.subTest(cross=(backend, form)), self.assertRaises(LanguageBridgeError):
                self._designate(model={**_model_block(), "backend": backend, "model_form": form})
        # 已写盘的交叉组合读回同样 fail-closed。
        path = self.runtime / RESULT_FILE
        document = json.loads(path.read_text(encoding="utf-8"))
        document["result"]["model"]["model_form"] = "c2-adapter"
        path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(LanguageBridgeError):
            read_result(self.runtime)


class TrackerStateBridgeTests(TempRuntimeCase):
    """(c) `tracker_state.json`：八态、原因闭集、回执七值与发布门标志。"""

    def _state(self, **overrides):
        base = dict(
            session_id="s1",
            state="IDLE",
            sequence=3,
            epoch=1,
            publishing=False,
        )
        base.update(overrides)
        return tracker_state_payload(**base)

    def test_round_trip(self) -> None:
        path = write_tracker_state(self.runtime, self._state())
        self.assertEqual(path.name, TRACKER_STATE_FILE)
        document = read_tracker_state(self.runtime)
        assert document is not None
        self.assertEqual(document["protocol"], TRACKER_STATE_SCHEMA)
        self.assertEqual(document["tracker_state"]["state"], "IDLE")

    def test_all_states_expressible(self) -> None:
        for state in SESSION_STATES:
            extra = {}
            if state == "SUSPECTED":
                extra = {"suspect_kind": "drift", "suspect_id": "sus-1"}
            if state in {"LOST", "REINIT_REQUIRED", "TERMINAL"}:
                extra = {"reason": "operator_stop"}
            self.assertEqual(self._state(state=state, **extra)["tracker_state"]["state"], state)

    def test_resident_closed_sets_and_designation_field(self) -> None:
        """P1-ENG-ACQ-001 AC-13：`ACQUIRING` 与三个新原因入闭集；`designation.result` 只取六值、`level2.reason` 只取闭集。"""
        from controller.language_bridge import PUBLISHING_STATES  # noqa: PLC0415

        self.assertIn("ACQUIRING", SESSION_STATES)
        self.assertEqual(len(SESSION_STATES), 9)
        for reason in ("acquire_failed", "slew_timeout", "adopt_timeout"):
            self.assertIn(reason, STATE_REASONS)
        self.assertEqual(set(PUBLISHING_STATES), {"TRACKING", "SUSPECTED", "QUERYING", "AWAITING_CONFIRMATION"})
        good = {"designation_id": 3, "frame_id_k": 10, "head_frame_id": 14, "result": "NO_TRACK_AT_K", "resolution_level": None, "track_id": None, "level2": {"reason": "sot_lost@12"}}
        document = self._state(state="TRACKING", publishing=True, designation=good)
        self.assertEqual(document["tracker_state"]["designation"]["result"], "NO_TRACK_AT_K")
        write_tracker_state(self.runtime, document)
        self.assertEqual(read_tracker_state(self.runtime)["tracker_state"]["designation"]["level2"]["reason"], "sot_lost@12")
        for bad in ({**good, "result": "ACQUIRE_FAILED"}, {**good, "level2": {"reason": "timeout"}}, {**good, "resolution_level": 3}):
            with self.assertRaises(LanguageBridgeError):
                self._state(state="TRACKING", designation=bad)
        self.assertNotIn("designation", self._state()["tracker_state"])  # 段式会话文档字段集不变
        with self.assertRaises(LanguageBridgeError):
            self._state(state="ACQUIRING", publishing=True)

    def test_suspect_fields_are_state_bound(self) -> None:
        with self.assertRaises(LanguageBridgeError):
            self._state(state="SUSPECTED")
        with self.assertRaises(LanguageBridgeError):
            self._state(state="TRACKING", suspect_kind="drift", suspect_id="x")
        with self.assertRaises(LanguageBridgeError):
            self._state(
                state="SUSPECTED", suspect_kind="vanished", suspect_id="x"
            )

    def test_terminal_states_require_a_reason_from_the_closed_set(self) -> None:
        for state in ("LOST", "REINIT_REQUIRED", "TERMINAL"):
            with self.assertRaises(LanguageBridgeError):
                self._state(state=state)
        for reason in STATE_REASONS:
            self.assertEqual(
                self._state(state="LOST", reason=reason)["tracker_state"]["reason"],
                reason,
            )
        with self.assertRaises(LanguageBridgeError):
            self._state(state="LOST", reason="just_because")

    def test_publishing_requires_an_active_segment(self) -> None:
        with self.assertRaises(LanguageBridgeError):
            self._state(state="IDLE", publishing=True)
        self.assertTrue(
            self._state(state="TRACKING", publishing=True)["tracker_state"][
                "publishing"
            ]
        )

    def test_receipt_outcomes_are_the_seven_value_closed_set(self) -> None:
        for outcome in OUTCOMES:
            payload = self._state(
                last_request={
                    "request_id": "r1",
                    "action": "ask",
                    "outcome": outcome,
                    "at_sequence": 2,
                }
            )
            self.assertEqual(payload["tracker_state"]["last_request"]["outcome"], outcome)
        self.assertEqual(len(OUTCOMES), 7)
        with self.assertRaises(LanguageBridgeError):
            self._state(
                last_request={
                    "request_id": "r1",
                    "action": "ask",
                    "outcome": "MAYBE",
                    "at_sequence": 2,
                }
            )

    def test_pending_and_retired_validation(self) -> None:
        payload = self._state(
            pending_request={"request_id": "r2", "action": "verify", "at_sequence": 4},
            retired_track_ids=[
                {
                    "track_id": "s1-t1",
                    "from_frame_id": 4,
                    "to_frame_id": 40,
                    "retired_reason": "operator_release",
                }
            ],
        )
        self.assertEqual(payload["tracker_state"]["pending_request"]["action"], "verify")
        self.assertEqual(len(payload["tracker_state"]["retired_track_ids"]), 1)
        with self.assertRaises(LanguageBridgeError):
            self._state(
                retired_track_ids=[
                    {
                        "track_id": "s1-t1",
                        "from_frame_id": 4,
                        "to_frame_id": 40,
                        "retired_reason": "got_bored",
                    }
                ]
            )

    def test_reader_fails_closed_on_unknown_reason(self) -> None:
        write_tracker_state(self.runtime, self._state(state="LOST", reason="operator_stop"))
        path = self.runtime / TRACKER_STATE_FILE
        document = json.loads(path.read_text(encoding="utf-8"))
        document["tracker_state"]["reason"] = "vibes"
        path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(LanguageBridgeError):
            read_tracker_state(self.runtime)


class WriterLockTests(TempRuntimeCase):
    """§3.2 写者锁：并发 CLI → `WRITER_BUSY`；只有持有者能释放。"""

    def test_second_writer_is_refused(self) -> None:
        acquire_writer_lock(self.runtime, request_id="r1", pid=4242, is_alive=_alive)
        cleared = []
        with self.assertRaises(WriterBusy):
            acquire_writer_lock(
                self.runtime,
                request_id="r2",
                pid=4343,
                is_alive=_alive,
                on_dead_lock_cleared=cleared.append,
            )
        self.assertTrue((self.runtime / REQUEST_LOCK_FILE).is_file())
        self.assertEqual(cleared, [])

    def test_only_the_matching_holder_releases(self) -> None:
        acquire_writer_lock(self.runtime, request_id="r1", pid=4242, is_alive=_alive)
        self.assertFalse(release_writer_lock(self.runtime, request_id="r1", pid=9999))
        self.assertFalse(release_writer_lock(self.runtime, request_id="rX", pid=4242))
        self.assertTrue((self.runtime / REQUEST_LOCK_FILE).is_file())
        self.assertTrue(release_writer_lock(self.runtime, request_id="r1", pid=4242))
        self.assertFalse((self.runtime / REQUEST_LOCK_FILE).is_file())

    def test_dead_holder_lock_is_reclaimed_and_reported(self) -> None:
        acquire_writer_lock(self.runtime, request_id="r1", pid=4242, is_alive=_alive)
        cleared = clear_dead_writer_lock(self.runtime, is_alive=_dead)
        assert cleared is not None
        self.assertEqual(cleared.pid, 4242)
        self.assertEqual(cleared.request_id, "r1")
        self.assertFalse((self.runtime / REQUEST_LOCK_FILE).is_file())

    def test_live_holder_lock_is_never_reclaimed(self) -> None:
        acquire_writer_lock(self.runtime, request_id="r1", pid=4242, is_alive=_alive)
        self.assertIsNone(clear_dead_writer_lock(self.runtime, is_alive=_alive))
        self.assertTrue((self.runtime / REQUEST_LOCK_FILE).is_file())

    def test_acquire_takes_over_a_dead_lock(self) -> None:
        acquire_writer_lock(
            self.runtime, request_id="r1", pid=4242, now=77.0, is_alive=_alive
        )
        cleared = []
        holder = acquire_writer_lock(
            self.runtime,
            request_id="r2",
            pid=5555,
            is_alive=_dead,
            on_dead_lock_cleared=cleared.append,
        )
        self.assertEqual(holder.request_id, "r2")
        body = json.loads((self.runtime / REQUEST_LOCK_FILE).read_text(encoding="utf-8"))
        self.assertEqual(body["pid"], 5555)
        # AC-1 修订 1「并记日志」：被清理的持有者交给调用方。
        self.assertEqual(
            [(dead.pid, dead.request_id, dead.created_unix_s) for dead in cleared],
            [(4242, "r1", 77.0)],
        )

    def test_corrupt_lock_is_treated_as_held(self) -> None:
        (self.runtime / REQUEST_LOCK_FILE).write_text("junk", encoding="utf-8")
        with self.assertRaises(WriterBusy):
            acquire_writer_lock(
                self.runtime, request_id="r1", pid=4242, is_alive=_dead
            )


class SessionLockTests(TempRuntimeCase):
    """§3.2 会话锁：活锁 → `SESSION_SLOT_BUSY`；死锁被替换并可记录。"""

    def test_live_session_blocks_a_second_start(self) -> None:
        holder, replaced = acquire_session_lock(
            self.runtime, session_id="s1", pid=4242, is_alive=_alive
        )
        self.assertIsNone(replaced)
        self.assertEqual(holder.session_id, "s1")
        with self.assertRaises(SessionSlotBusy):
            acquire_session_lock(
                self.runtime, session_id="s2", pid=4343, is_alive=_alive
            )

    def test_dead_session_lock_is_replaced_and_returned(self) -> None:
        acquire_session_lock(self.runtime, session_id="s1", pid=4242, is_alive=_alive)
        holder, replaced = acquire_session_lock(
            self.runtime, session_id="s2", pid=4343, is_alive=_dead
        )
        self.assertEqual(holder.session_id, "s2")
        assert replaced is not None
        self.assertEqual(replaced.session_id, "s1")
        self.assertEqual(replaced.pid, 4242)

    def test_release_requires_the_matching_owner(self) -> None:
        acquire_session_lock(self.runtime, session_id="s1", pid=4242, is_alive=_alive)
        self.assertFalse(release_session_lock(self.runtime, session_id="s1", pid=1))
        self.assertFalse(release_session_lock(self.runtime, session_id="sX", pid=4242))
        self.assertTrue(release_session_lock(self.runtime, session_id="s1", pid=4242))
        self.assertFalse((self.runtime / SESSION_LOCK_FILE).is_file())


class RuntimeReadmeTests(unittest.TestCase):
    """AC-1：`runtime/README.md` 必须公开三个新桥文件与 `confidence_source` 口径。"""

    def test_readme_documents_the_three_bridge_files(self) -> None:
        readme = (
            Path(__file__).resolve().parents[1] / "runtime" / "README.md"
        ).read_text(encoding="utf-8")
        for name in ("language_request.json", "language_result.json", "tracker_state.json"):
            self.assertIn(name, readme)
        self.assertIn("confidence_source", readme)
        self.assertIn("placeholder", readme)
        self.assertIn("uncalibrated", readme)



class Loop2BridgeTests(unittest.TestCase):
    """P1-ENG-LOOP-002 §7 (m)/AC-3/AC-17/AC-6：`STATE_REASONS` 追加不重排；六个 llama 身份键条件必需。"""

    def test_state_reasons_appended_without_reordering(self) -> None:
        self.assertEqual(STATE_REASONS[24:26], ("rebuild_limit", "geometry_rejected"))
        self.assertEqual(len(STATE_REASONS), len(set(STATE_REASONS)))
        # 前 24 个成员与本项开工前的闭集逐位相同（acquire_failed/slew_timeout/adopt_timeout 收尾）。
        self.assertEqual(STATE_REASONS[21:24], ("acquire_failed", "slew_timeout", "adopt_timeout"))
        # P1-ENG-CAPTURE-001 §3.6 / AR1-2：其后只在末尾追加 11 个（位次不重排）。
        self.assertEqual(
            STATE_REASONS[26:37],
            (
                "predicting", "no_new_observation", "continuity_repaired", "continuity_broken", "continuity_disputed",
                "language_disabled", "image_mismatch", "superseded_by_click", "click_unavailable",
                "binding_rollback_failed", "authorization_input_inconsistent",
            ),
        )
        # P1-ENG-FASTFIX-001 §3.2/§3.3：其后只在末尾再追加 5 个（CAPTURE 的 37 项前缀逐位不变）。
        self.assertEqual(
            STATE_REASONS[37:],
            ("publish_degraded", "reacquiring", "reacquire_failed", "reacquire_ambiguous", "rebuild_reacquired"),
        )
        self.assertEqual(len(STATE_REASONS), 42)
        # IR-3/IR-5：旧完整前缀（26 项）与接受基线运行时逐位比较；其后恰为 §3.6 十项 + 一致性原因（第 37 项）。
        from tools.eng_capture.common import accepted_base_literal  # noqa: PLC0415

        base = accepted_base_literal("controller/language_bridge.py", "STATE_REASONS")
        if base is not None:
            self.assertEqual(len(base), 26)
            self.assertEqual(STATE_REASONS[:26], tuple(base))
            self.assertEqual(STATE_REASONS, tuple(base) + STATE_REASONS[26:])
        self.assertEqual(STATE_REASONS[36], "authorization_input_inconsistent")
        for reason in ("rebuild_limit", "geometry_rejected"):
            document = tracker_state_payload(
                session_id="s", state="TERMINAL", sequence=1, epoch=1, publishing=False, reason=reason
            )
            self.assertEqual(document["tracker_state"]["reason"], reason)
        # IR-5：新追加原因（含一致性原因）经桥 payload 写出并读回，不被闭集拒绝。
        with tempfile.TemporaryDirectory() as directory:
            for reason in STATE_REASONS[26:]:
                write_tracker_state(Path(directory), tracker_state_payload(
                    session_id="s", state="TRACKING", sequence=1, epoch=1, publishing=False, reason=reason
                ))
                self.assertEqual(read_tracker_state(Path(directory))["tracker_state"]["reason"], reason)

    def test_llama_identity_keys_all_or_none_with_types(self) -> None:
        from controller.language_bridge import LLAMA_IDENTITY_KEYS, validate_llama_identity  # noqa: PLC0415

        good = {
            "backend": "http", "model_form": "c2-merged", "weights_sha256": "a" * 64,
            "prompt_template_sha256": "b" * 64, "mmproj_sha256": "c" * 64, "runtime_binary_sha256": "d" * 64,
            "runtime_build": "b11381", "quantization": "Q4_K_M", "response_format_sha256": "e" * 64,
            "decode_config_sha256": "f" * 64,
        }
        self.assertEqual(set(validate_llama_identity(good)), set(LLAMA_IDENTITY_KEYS))
        self.assertEqual(validate_llama_identity({"backend": "local-hf", "model_form": "c2-merged"}), {})
        bad = [
            {k: v for k, v in good.items() if k != "mmproj_sha256"},
            dict(good, mmproj_sha256="C" * 64),
            dict(good, decode_config_sha256="e" * 63),
            dict(good, runtime_build="11381"),
            dict(good, runtime_build="b12345678"),
            dict(good, quantization="Q8_0"),
            dict(good, backend="local-hf"),
            dict(good, model_form="base"),
            dict(good, weights_sha256="scripted"),
            dict(good, prompt_template_sha256=None),
        ]
        for value in bad:
            with self.subTest(value=sorted(value.items())), self.assertRaises(LanguageBridgeError):
                validate_llama_identity(value)

    def test_llama_key_present_with_null_value_is_not_absent(self) -> None:
        """C1-AC6：键出现即「出现」——旧身份块只追加一个 `null` 键不得被当作六键全无而放行。"""
        from controller.language_bridge import (  # noqa: PLC0415
            LLAMA_IDENTITY_KEYS,
            _validate_model_block,
            validate_llama_identity,
        )

        legacy = {"backend": "http", "model_form": "c2-merged", "weights_sha256": "a" * 64,
                  "prompt_template_sha256": "b" * 64}
        self.assertEqual(validate_llama_identity(legacy), {})
        self.assertFalse(set(_validate_model_block(legacy)) & set(LLAMA_IDENTITY_KEYS))
        for key in LLAMA_IDENTITY_KEYS:
            with self.subTest(single_null=key), self.assertRaisesRegex(LanguageBridgeError, "all-or-none"):
                validate_llama_identity(dict(legacy, **{key: None}))
            with self.subTest(model_block=key), self.assertRaises(LanguageBridgeError):
                _validate_model_block(dict(legacy, **{key: None}))
        all_null = dict(legacy, **{key: None for key in LLAMA_IDENTITY_KEYS})
        with self.assertRaises(LanguageBridgeError):
            validate_llama_identity(all_null)


if __name__ == "__main__":
    unittest.main()
