from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import threading
import time
import unittest

from controller.reanchor import (
    BufferedFrame,
    Candidate,
    DEFAULT_CONFIG,
    FrameHistory,
    GateAnchor,
    ReplayResult,
    RoundDecision,
    SingleFlightWorker,
    TripleGateState,
    load_reanchor_config,
    replay_tracker,
    world_los,
)
from controller.reanchor_models import ProposalBatch
from controller.reanchor_runtime import ReanchorRuntime
from controller.trackers import ScriptedTracker, TrackerResult


def metadata(rotation=(0.0, 0.0, 0.0, 1.0)):
    return {
        "schema_version": "tethered-sensor-frame/v3",
        "width": 200,
        "height": 100,
        "intrinsics_px": {"fx": 100.0, "fy": 100.0, "cx": 100.0, "cy": 50.0},
        "camera_right_world": [1.0, 0.0, 0.0],
        "camera_up_world": [0.0, 1.0, 0.0],
        "camera_forward_world": [0.0, 0.0, 1.0],
        "camera_rotation_xyzw": list(rotation),
        "capture_monotonic_s": 1.0,
        "capture_monotonic_clock_id": "system-stopwatch/v1",
    }


class FakeImage:
    shape = (100, 200, 3)

    def copy(self):
        return self


class EmptyProposer:
    def propose(self, image):
        return ProposalBatch((), (), 0.0)


class OneCandidateProposer:
    def propose(self, image):
        return ProposalBatch(((0.45, 0.4, 0.1, 0.2),), (0.9,), 0.0)


class UnitEmbedder:
    def embed(self, image, box):
        return (1.0,)

    def cosine(self, left, right):
        return 0.9


class BlockingGate:
    def __init__(self):
        self.anchor = GateAnchor((0.0, 0.0, 1.0), 0.0)
        self.entered = threading.Event()
        self.release = threading.Event()

    def evaluate(self, *args, **kwargs):
        self.entered.set()
        self.release.wait(1.0)
        return RoundDecision("NO_CANDIDATE", None, None, (), False, True)


class ReanchorTests(unittest.TestCase):
    def setUp(self):
        self.config = load_reanchor_config()

    def test_strict_config_rejects_extra_key(self):
        value = json.loads(DEFAULT_CONFIG.read_text())
        value["extra"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "keys mismatch"):
                load_reanchor_config(path)

    def test_runtime_rejects_legacy_or_mismatched_capture_clock(self):
        runtime = ReanchorRuntime(
            self.config,
            lambda: ScriptedTracker([]),
            proposer=object(),
            embedder=object(),
        )
        for field, value, message in (
            ("schema_version", "tethered-sensor-frame/v2", "requires sensor frame schema"),
            (
                "capture_monotonic_clock_id",
                "unity-process-relative/v1",
                "requires capture_monotonic_clock_id",
            ),
            ("capture_monotonic_s", float("nan"), "finite and non-negative"),
        ):
            frame_metadata = metadata()
            frame_metadata[field] = value
            bundle = type(
                "Bundle",
                (),
                {"frame_id": 1, "image": FakeImage(), "metadata": frame_metadata},
            )()
            with self.assertRaisesRegex(ValueError, message):
                runtime.after_frame(
                    bundle,
                    TrackerResult((0.4, 0.4, 0.1, 0.2), True, 0.9, "tracker"),
                    released=False,
                )

    def test_world_los_uses_top_left_sign_and_validates_quaternion(self):
        center = world_los((0.45, 0.4, 0.1, 0.2), metadata())
        self.assertAlmostEqual(center[2], 1.0)
        upper = world_los((0.45, 0.0, 0.1, 0.2), metadata())
        self.assertGreater(upper[1], 0.0)
        invalid = metadata()
        invalid["camera_rotation_xyzw"] = [0.0, 0.0, 0.0, 2.0]
        with self.assertRaisesRegex(ValueError, "quaternion"):
            world_los((0.45, 0.4, 0.1, 0.2), invalid)

    def test_world_los_remains_world_consistent_during_gimbal_rotation(self):
        angle = math.pi / 4.0
        rotated = metadata((0.0, 0.0, math.sin(angle), math.cos(angle)))
        rotated["camera_right_world"] = [0.0, 1.0, 0.0]
        rotated["camera_up_world"] = [-1.0, 0.0, 0.0]
        upper = world_los((0.45, 0.0, 0.1, 0.2), rotated)
        lower = world_los((0.45, 0.8, 0.1, 0.2), rotated)
        self.assertLess(upper[0], 0.0)
        self.assertGreater(lower[0], 0.0)

    def _candidate(self, index, reid, det, angle, box=(0.1, 0.1, 0.2, 0.2)):
        return Candidate(index, box, det, reid, (0.0, 0.0, 1.0), angle)

    def test_tie_break_and_ambiguous_reset(self):
        gate = TripleGateState(self.config)
        gate.anchor = GateAnchor((0.0, 0.0, 1.0), 0.0)
        first = self._candidate(3, 0.8, 0.9, 0.05)
        second = self._candidate(2, 0.75, 0.99, 0.01)
        decision = gate.evaluate([second, first], sot_box_norm=(0.8, 0.8, 0.1, 0.1), capture_monotonic_s=1.0)
        self.assertEqual(decision.outcome, "AMBIGUOUS")
        self.assertEqual(decision.winner.index, 3)
        self.assertEqual(gate.disagree_count, 0)

    def test_k_hysteresis_and_agree_refresh(self):
        gate = TripleGateState(self.config)
        gate.set_anchor((0.0, 0.0, 1.0), 0.0)
        candidate = self._candidate(0, 0.9, 0.9, 0.01)
        one = gate.evaluate([candidate], sot_box_norm=(0.7, 0.7, 0.1, 0.1), capture_monotonic_s=1.0)
        two = gate.evaluate([candidate], sot_box_norm=(0.7, 0.7, 0.1, 0.1), capture_monotonic_s=3.0)
        self.assertFalse(one.trigger_reseed)
        self.assertTrue(two.trigger_reseed)
        agree = gate.evaluate([candidate], sot_box_norm=candidate.box_norm, capture_monotonic_s=5.0)
        self.assertEqual(agree.outcome, "AGREE")
        self.assertEqual(gate.disagree_count, 0)
        self.assertEqual(gate.anchor.capture_monotonic_s, 5.0)

    def test_crop_invalid_is_not_no_candidate(self):
        gate = TripleGateState(self.config)
        gate.set_anchor((0.0, 0.0, 1.0), 0.0)
        result = gate.evaluate([], sot_box_norm=None, capture_monotonic_s=1.0, class_candidate_count=1, crop_invalid_count=1)
        self.assertEqual(result.outcome, "TENTATIVE_CROP_INVALID")

    def _history(self):
        history = FrameHistory(6.0)
        for frame_id in range(4):
            history.append(BufferedFrame(frame_id, float(frame_id), FakeImage(), metadata(), (0.1, 0.1, 0.2, 0.2)))
        return history

    def test_replay_initializes_exact_source_and_orders_frames(self):
        created = []
        def factory():
            tracker = ScriptedTracker([
                TrackerResult((0.11, 0.1, 0.2, 0.2), True, 0.9, "tracker"),
                TrackerResult((0.12, 0.1, 0.2, 0.2), True, 0.9, "tracker"),
            ])
            created.append(tracker)
            return tracker
        result = replay_tracker(factory, self._history(), source_frame_id=1, source_box_norm=(0.1, 0.1, 0.2, 0.2), target_head_frame_id=3, maximum_source_age_s=3.0, catchup_timeout_s=2.0)
        self.assertEqual(result.event, "RESEED_READY")
        self.assertEqual(result.replay_count, 2)
        self.assertEqual(len(created[0].init_calls), 1)
        for actual, expected in zip(created[0].init_calls[0], (0.1, 0.1, 0.2, 0.2)):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(created[0].update_calls, 2)

    def test_frame_history_is_deeply_immutable_after_publication(self):
        source_metadata = metadata()
        history = FrameHistory(6.0)
        history.append(BufferedFrame(1, 1.0, FakeImage(), source_metadata, None))
        source_metadata["intrinsics_px"]["fx"] = 7.0
        frozen = history.get(1)
        self.assertEqual(frozen.metadata["intrinsics_px"]["fx"], 100.0)
        with self.assertRaises(TypeError):
            frozen.metadata["intrinsics_px"]["fx"] = 8.0

    def test_replay_missing_stale_timeout_and_invalid(self):
        history = self._history()
        factory = lambda: ScriptedTracker([TrackerResult.lost("bad")] * 3)
        self.assertEqual(replay_tracker(factory, history, source_frame_id=9, source_box_norm=(0.1, 0.1, 0.2, 0.2), target_head_frame_id=3, maximum_source_age_s=3, catchup_timeout_s=2).event, "RESEED_DISCARDED_MISSING_FRAME")
        self.assertEqual(replay_tracker(factory, history, source_frame_id=0, source_box_norm=(0.1, 0.1, 0.2, 0.2), target_head_frame_id=3, maximum_source_age_s=2, catchup_timeout_s=2).event, "RESEED_DISCARDED_STALE")
        self.assertEqual(replay_tracker(factory, history, source_frame_id=1, source_box_norm=(0.1, 0.1, 0.2, 0.2), target_head_frame_id=3, maximum_source_age_s=3, catchup_timeout_s=2).event, "RESEED_DISCARDED_INVALID_BOX")
        outside_factory = lambda: ScriptedTracker([
            TrackerResult((-0.01, 0.1, 0.2, 0.2), True, 0.9, "tracker")
        ])
        self.assertEqual(
            replay_tracker(
                outside_factory,
                history,
                source_frame_id=2,
                source_box_norm=(0.1, 0.1, 0.2, 0.2),
                target_head_frame_id=3,
                maximum_source_age_s=3,
                catchup_timeout_s=2,
            ).event,
            "RESEED_DISCARDED_INVALID_BOX",
        )

    def test_single_flight_busy_failure_and_timeout(self):
        worker = SingleFlightWorker(timeout_s=0.02, failure_limit=3)
        release = threading.Event()
        self.assertEqual(worker.submit(lambda: release.wait(1.0)).event, "ROUND_STARTED")
        self.assertEqual(worker.submit(lambda: None).event, "ROUND_SKIPPED_BUSY")
        time.sleep(0.03)
        self.assertEqual(worker.poll().event, "ROUND_TIMEOUT")
        self.assertTrue(worker.timed_out_alive)
        release.set()
        self.assertTrue(worker.close(1.0))
        completed = worker.poll()
        self.assertEqual(completed.event, "ROUND_FAILED_AFTER_TIMEOUT")
        self.assertEqual(worker.consecutive_failures, 1)

    def test_single_flight_allows_only_one_confirmed_death_restart(self):
        worker = SingleFlightWorker(timeout_s=1.0, failure_limit=3)
        for expected in ("WORKER_DIED_RESTART_ALLOWED", "WORKER_DIED"):
            thread = threading.Thread(target=lambda: None)
            thread.start()
            thread.join()
            worker._thread = thread
            worker._result = None
            worker._started = time.monotonic()
            self.assertEqual(worker.poll().event, expected)
        self.assertTrue(worker.fail_closed)
        self.assertEqual(
            worker.submit(lambda: None).event,
            "WORKER_RESTART_EXHAUSTED",
        )

    def test_gate_evaluation_and_main_swap_share_runtime_lock(self):
        runtime = ReanchorRuntime(
            self.config,
            lambda: ScriptedTracker([]),
            proposer=EmptyProposer(),
            embedder=object(),
        )
        blocking_gate = BlockingGate()
        runtime.gate = blocking_gate
        runtime.anchor_embedding = (1.0,)
        capture = time.monotonic()
        runtime.next_tick_capture_s = capture
        frame_metadata = metadata()
        frame_metadata["capture_monotonic_s"] = capture
        bundle = type(
            "Bundle",
            (),
            {"frame_id": 1, "image": FakeImage(), "metadata": frame_metadata},
        )()
        runtime.after_frame(
            bundle,
            TrackerResult((0.4, 0.4, 0.1, 0.2), True, 0.9, "tracker"),
            released=True,
        )
        self.assertTrue(blocking_gate.entered.wait(1.0))
        main_completed = threading.Event()

        def main_boundary():
            runtime.before_update(1)
            main_completed.set()

        main_thread = threading.Thread(target=main_boundary)
        main_thread.start()
        self.assertFalse(main_completed.wait(0.03))
        blocking_gate.release.set()
        main_thread.join(1.0)
        self.assertTrue(main_completed.is_set())
        self.assertTrue(runtime.close())

    def test_reseed_failure_increment_uses_runtime_lock(self):
        runtime = ReanchorRuntime(
            self.config,
            lambda: ScriptedTracker([]),
            proposer=object(),
            embedder=object(),
        )
        incremented = threading.Event()

        def increment():
            runtime._increment_reseed_failure()
            incremented.set()

        with runtime._lock:
            thread = threading.Thread(target=increment)
            thread.start()
            self.assertFalse(incremented.wait(0.03))
        thread.join(1.0)
        self.assertTrue(incremented.is_set())
        self.assertEqual(runtime.reseed_failures, 1)

    def test_reseed_failure_limit_sets_fail_closed_reason_without_worker_message(self):
        runtime = ReanchorRuntime(
            self.config,
            lambda: ScriptedTracker([]),
            proposer=object(),
            embedder=object(),
        )
        with runtime._lock:
            runtime.reseed_failures = int(
                self.config.parameters["consecutive_failure_limit"]
            )
        runtime.poll()
        self.assertEqual(
            runtime.fatal_reason,
            "reanchor_consecutive_failure_limit",
        )

    def _trigger_runtime(self):
        runtime = ReanchorRuntime(
            self.config,
            lambda: ScriptedTracker([]),
            proposer=OneCandidateProposer(),
            embedder=UnitEmbedder(),
        )
        runtime.anchor_embedding = (1.0,)
        runtime.gate.set_anchor((0.0, 0.0, 1.0), time.monotonic() - 1.0)
        return runtime

    def _submit_round(self, runtime, frame_id, result):
        capture = time.monotonic()
        frame_metadata = metadata()
        frame_metadata["capture_monotonic_s"] = capture
        bundle = type(
            "Bundle",
            (),
            {"frame_id": frame_id, "image": FakeImage(), "metadata": frame_metadata},
        )()
        runtime.next_tick_capture_s = capture
        runtime.after_frame(bundle, result, released=True)
        self.assertTrue(runtime.close())
        runtime.poll()

    def test_events_distinguish_lost_direct_and_k_hysteresis_reseeds(self):
        lost_runtime = self._trigger_runtime()
        self._submit_round(
            lost_runtime,
            1,
            TrackerResult.lost("synthetic_lost"),
        )
        lost_events = lost_runtime.drain_events()
        lost_decision = next(event for event in lost_events if event.event == "DISAGREE")
        self.assertEqual(lost_decision.fields["trigger_reason"], "LOST_DIRECT")
        self.assertIsNotNone(lost_runtime.before_update(1))
        lost_reanchor = lost_runtime.drain_events()[-1]
        self.assertEqual(lost_reanchor.fields["trigger_reason"], "LOST_DIRECT")

        k_runtime = self._trigger_runtime()
        disagreeing_sot = TrackerResult(
            (0.05, 0.05, 0.1, 0.1),
            True,
            0.9,
            "tracker",
        )
        self._submit_round(k_runtime, 1, disagreeing_sot)
        first_events = k_runtime.drain_events()
        first_decision = next(event for event in first_events if event.event == "DISAGREE")
        self.assertIsNone(first_decision.fields["trigger_reason"])
        self._submit_round(k_runtime, 2, disagreeing_sot)
        second_events = k_runtime.drain_events()
        second_decision = next(event for event in second_events if event.event == "DISAGREE")
        self.assertEqual(second_decision.fields["trigger_reason"], "K_HYSTERESIS")
        self.assertIsNotNone(k_runtime.before_update(2))
        k_reanchor = k_runtime.drain_events()[-1]
        self.assertEqual(k_reanchor.fields["trigger_reason"], "K_HYSTERESIS")

    def test_atomic_swap_refreshes_motion_anchor_from_catchup_head(self):
        clock = [3.5]
        runtime = ReanchorRuntime(
            self.config,
            lambda: ScriptedTracker([]),
            proposer=object(),
            embedder=object(),
            monotonic=lambda: clock[0],
            monotonic_clock_id="system-stopwatch/v1",
        )
        for frame_id in range(1, 4):
            runtime.history.append(
                BufferedFrame(
                    frame_id,
                    float(frame_id),
                    FakeImage(),
                    metadata(),
                    (0.4, 0.4, 0.1, 0.2),
                )
            )
        runtime.gate.set_anchor((1.0, 0.0, 0.0), 1.0)
        replacement = ScriptedTracker([])
        runtime._pending = ReplayResult(
            "RESEED_READY",
            replacement,
            2,
            3,
            1,
            4.0,
            TrackerResult((0.45, 0.4, 0.1, 0.2), True, 0.9, "tracker"),
        )
        runtime._pending_fields = {
            "source_capture_monotonic_s": 2.0,
            "detector_confidence": 0.8,
            "reid_cosine": 0.9,
            "motion_angle_rad": 0.01,
            "margin": None,
        }
        self.assertIs(runtime.before_update(3), replacement)
        self.assertEqual(runtime.gate.anchor.capture_monotonic_s, 3.0)
        self.assertAlmostEqual(runtime.gate.anchor.los_world[2], 1.0)

    def test_atomic_swap_discards_stale_pending_tracker(self):
        clock = [5.1]
        runtime = ReanchorRuntime(
            self.config,
            lambda: ScriptedTracker([]),
            proposer=object(),
            embedder=object(),
            monotonic=lambda: clock[0],
            monotonic_clock_id="system-stopwatch/v1",
        )
        runtime.history.append(
            BufferedFrame(3, 3.0, FakeImage(), metadata(), (0.4, 0.4, 0.1, 0.2))
        )
        runtime._pending = ReplayResult(
            "RESEED_READY",
            ScriptedTracker([]),
            2,
            3,
            1,
            4.0,
            TrackerResult((0.45, 0.4, 0.1, 0.2), True, 0.9, "tracker"),
        )
        runtime._pending_fields = {"source_capture_monotonic_s": 2.0}
        self.assertIsNone(runtime.before_update(3))
        self.assertEqual(runtime.drain_events()[0].event, "RESEED_DISCARDED_STALE")


if __name__ == "__main__":
    unittest.main()
