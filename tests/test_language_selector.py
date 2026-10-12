"""P1-ENG-LOOP-001 AC-8/AC-9：统一推理适配、三后端与合并等价判定。

无 GPU、无 torch：`local-hf` 用打桩的 `predict_rows`，`http` 用真实的本地单工服务
配脚本后端，`replay` 用临时盲索引/预测文件，外加一次对真实冻结资产的 sha 核对。
"""

import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from controller.language_bridge import REJECT_REASONS
from controller.language_selector import (
    MERGE_EQUIVALENCE_IOU,
    VERIFY_IOU,
    HttpAdapter,
    LocalHfAdapter,
    RawSelection,
    ReplayAdapter,
    ScriptedAdapter,
    SelectorError,
    box_1000_to_norm_xywh,
    boxes_match_one_to_one,
    interpret,
    iou_norm_xywh,
    selections_equivalent,
    sha256_file,
)
from tools.language_serve import SingleFlightRuntime, build_server

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SFT002 = PROJECT_ROOT / "outputs" / "eng-sft" / "P1-ENG-SFT-002"
EVIDENCE = PROJECT_ROOT / "docs" / "evidence"


def _raw(text: str, finish_reason: str = "stop") -> RawSelection:
    return RawSelection(
        raw_output=text,
        finish_reason=finish_reason,
        gen_tokens=31,
        latency_ms=1234.5,
        prompt_sha256="p" * 64,
        model_id="m" * 64,
    )


UNIQUE = '{"status": "unique", "bbox_2d": [100, 200, 300, 400]}'
AMBIGUOUS = (
    '{"status": "ambiguous", "candidates": [{"bbox_2d": [10, 20, 30, 40]}, '
    '{"bbox_2d": [500, 500, 600, 600]}]}'
)
NONE = '{"status": "none"}'


class InterpretTests(unittest.TestCase):
    """三态解析、框转换与截断路径（AC-8 的 `finish_reason` 保留）。"""

    def test_unique_ambiguous_none(self) -> None:
        unique = interpret(_raw(UNIQUE))
        self.assertEqual(unique.status, "unique")
        self.assertEqual(len(unique.candidates), 1)
        self.assertEqual(unique.candidates[0].bbox_2d_1000, (100, 200, 300, 400))
        self.assertAlmostEqual(unique.candidates[0].bbox_xywh_norm[0], 0.1)
        self.assertAlmostEqual(unique.candidates[0].bbox_xywh_norm[2], 0.2)
        self.assertFalse(unique.candidates[0].clipped)

        ambiguous = interpret(_raw(AMBIGUOUS))
        self.assertEqual(ambiguous.status, "ambiguous")
        self.assertEqual([c.index for c in ambiguous.candidates], [0, 1])

        self.assertEqual(interpret(_raw(NONE)).status, "none")

    def test_parse_failures_and_truncation(self) -> None:
        broken = interpret(_raw("not json at all"))
        self.assertEqual(broken.status, "parse_failed")
        self.assertEqual(broken.parse_error, "JSON_ERROR")
        self.assertEqual(broken.candidates, ())

        truncated = interpret(_raw(UNIQUE, finish_reason="length"))
        self.assertEqual(truncated.status, "parse_failed")
        self.assertEqual(truncated.parse_error, "TRUNCATED")

    def test_box_conversion_round_trip(self) -> None:
        box, clipped = box_1000_to_norm_xywh([0, 0, 1000, 1000])
        self.assertEqual(box, (0.0, 0.0, 1.0, 1.0))
        self.assertFalse(clipped)

    def test_iou_helper(self) -> None:
        self.assertAlmostEqual(
            iou_norm_xywh((0.0, 0.0, 0.2, 0.2), (0.0, 0.0, 0.2, 0.2)), 1.0
        )
        self.assertEqual(iou_norm_xywh((0.0, 0.0, 0.1, 0.1), (0.5, 0.5, 0.1, 0.1)), 0.0)
        self.assertEqual(VERIFY_IOU, 0.5)


class EquivalenceTests(unittest.TestCase):
    """AC-9 §3.5 等价判定：状态、unique IoU、ambiguous 一对一匹配、parse_error。"""

    def test_identical_rows_are_equivalent(self) -> None:
        left = interpret(_raw(UNIQUE))
        right = interpret(_raw(UNIQUE))
        self.assertEqual(selections_equivalent(left, right), (True, "equivalent"))

    def test_status_difference_breaks_equivalence(self) -> None:
        ok, reason = selections_equivalent(interpret(_raw(UNIQUE)), interpret(_raw(NONE)))
        self.assertFalse(ok)
        self.assertEqual(reason, "status")

    def test_unique_box_must_reach_the_threshold(self) -> None:
        near = '{"status": "unique", "bbox_2d": [102, 202, 300, 400]}'
        far = '{"status": "unique", "bbox_2d": [400, 500, 700, 800]}'
        ok, _ = selections_equivalent(interpret(_raw(UNIQUE)), interpret(_raw(near)))
        self.assertTrue(ok)
        ok, reason = selections_equivalent(interpret(_raw(UNIQUE)), interpret(_raw(far)))
        self.assertFalse(ok)
        self.assertEqual(reason, "unique_iou")
        self.assertEqual(MERGE_EQUIVALENCE_IOU, 0.9)

    def test_ambiguous_matching_is_order_independent(self) -> None:
        swapped = (
            '{"status": "ambiguous", "candidates": [{"bbox_2d": [500, 500, 600, 600]}, '
            '{"bbox_2d": [10, 20, 30, 40]}]}'
        )
        ok, _ = selections_equivalent(interpret(_raw(AMBIGUOUS)), interpret(_raw(swapped)))
        self.assertTrue(ok)

    def test_ambiguous_count_difference_breaks_equivalence(self) -> None:
        three = (
            '{"status": "ambiguous", "candidates": [{"bbox_2d": [10, 20, 30, 40]}, '
            '{"bbox_2d": [500, 500, 600, 600]}, {"bbox_2d": [700, 700, 800, 800]}]}'
        )
        ok, reason = selections_equivalent(interpret(_raw(AMBIGUOUS)), interpret(_raw(three)))
        self.assertFalse(ok)
        self.assertEqual(reason, "candidate_count")

    def test_parse_error_on_either_side_is_not_equivalent(self) -> None:
        ok, reason = selections_equivalent(
            interpret(_raw(UNIQUE)), interpret(_raw("{bad"))
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "parse_error")

    def test_one_to_one_matching_refuses_double_booking(self) -> None:
        # 两个预测框都只与同一个参考框重合：不存在一对一完美匹配。
        left = [[0, 0, 100, 100], [0, 0, 100, 100]]
        right = [[0, 0, 100, 100], [900, 900, 1000, 1000]]
        self.assertFalse(boxes_match_one_to_one(left, right))


class ReplayAdapterTests(unittest.TestCase):
    """AC-9：按 `row_id` 连接、两份 sha 核对、重复键与冲突、无 gold。"""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.root = Path(self._directory.name)
        self.frames = self.root / "frames"
        self.frames.mkdir()
        self.shas: dict[str, str] = {}
        for name in ("a", "b", "c"):
            payload = f"jpeg-bytes-{name}".encode("utf-8")
            digest = __import__("hashlib").sha256(payload).hexdigest()
            (self.frames / f"{digest}.jpg").write_bytes(payload)
            self.shas[name] = digest

    def tearDown(self) -> None:
        self._directory.cleanup()

    def _write(self, blind_rows, prediction_rows) -> tuple[Path, Path]:
        blind = self.root / "eval.blind.jsonl"
        predictions = self.root / "predictions.jsonl"
        blind.write_text(
            "".join(json.dumps(row) + "\n" for row in blind_rows), encoding="utf-8"
        )
        predictions.write_text(
            "".join(json.dumps(row) + "\n" for row in prediction_rows), encoding="utf-8"
        )
        return blind, predictions

    def _blind(self, row_id, sha, surface="the red car", g4=False) -> dict:
        return {
            "row_id": row_id,
            "frame_path": f"frames/{sha}.jpg",
            "surface": surface,
            "g4": g4,
            "vocab": "unity-v2",
        }

    def _prediction(self, row_id, raw=UNIQUE, finish_reason="stop") -> dict:
        return {
            "row_id": row_id,
            "raw_output": raw,
            "finish_reason": finish_reason,
            "gen_tokens": 31,
            "latency_ms": 42.0,
            "prompt_sha256": "p" * 64,
            "model_id": "4044dd4f",
        }

    def test_join_and_identity(self) -> None:
        blind, predictions = self._write(
            [self._blind("R1", self.shas["a"])], [self._prediction("R1")]
        )
        adapter = ReplayAdapter(
            blind,
            predictions,
            expected_blind_sha256=sha256_file(blind),
            expected_predictions_sha256=sha256_file(predictions),
        )
        raw = adapter.predict_one(
            "s1-q1", self.frames / f"{self.shas['a']}.jpg", "the red car", False
        )
        self.assertEqual(raw.raw_output, UNIQUE)
        self.assertEqual(raw.finish_reason, "stop")
        self.assertEqual(adapter.identity["backend"], "replay")
        self.assertEqual(adapter.identity["weights_sha256"], "4044dd4f")
        self.assertIsNotNone(adapter.identity["prompt_template_sha256"])

    def test_sha_mismatch_is_fail_closed(self) -> None:
        blind, predictions = self._write(
            [self._blind("R1", self.shas["a"])], [self._prediction("R1")]
        )
        with self.assertRaises(SelectorError) as caught:
            ReplayAdapter(blind, predictions, expected_blind_sha256="0" * 64)
        self.assertEqual(caught.exception.reason, "replay_identity_mismatch")
        with self.assertRaises(SelectorError) as caught:
            ReplayAdapter(blind, predictions, expected_predictions_sha256="0" * 64)
        self.assertEqual(caught.exception.reason, "replay_identity_mismatch")

    def test_missing_key_is_replay_miss(self) -> None:
        blind, predictions = self._write(
            [self._blind("R1", self.shas["a"])], [self._prediction("R1")]
        )
        adapter = ReplayAdapter(blind, predictions)
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one(
                "s1-q1", self.frames / f"{self.shas['b']}.jpg", "the red car", False
            )
        self.assertEqual(caught.exception.reason, "replay_miss")
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one(
                "s1-q2", self.frames / f"{self.shas['a']}.jpg", "the bus", False
            )
        self.assertEqual(caught.exception.reason, "replay_miss")

    def test_duplicate_key_with_identical_output_takes_the_smallest_row_id(self) -> None:
        blind, predictions = self._write(
            [self._blind("R2", self.shas["a"]), self._blind("R1", self.shas["a"])],
            [self._prediction("R1"), self._prediction("R2")],
        )
        adapter = ReplayAdapter(blind, predictions)
        self.assertEqual(
            adapter.row_ids_for(self.shas["a"], "the red car", False), ["R1", "R2"]
        )
        raw = adapter.predict_one(
            "s1-q1", self.frames / f"{self.shas['a']}.jpg", "the red car", False
        )
        self.assertEqual(raw.raw_output, UNIQUE)

    def test_duplicate_key_with_different_output_is_replay_conflict(self) -> None:
        blind, predictions = self._write(
            [self._blind("R1", self.shas["a"]), self._blind("R2", self.shas["a"])],
            [self._prediction("R1"), self._prediction("R2", raw=NONE)],
        )
        adapter = ReplayAdapter(blind, predictions)
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one(
                "s1-q1", self.frames / f"{self.shas['a']}.jpg", "the red car", False
            )
        self.assertEqual(caught.exception.reason, "replay_conflict")

    def test_gold_in_the_index_is_refused(self) -> None:
        row = self._blind("R1", self.shas["a"])
        row["gold_state"] = "unique"
        blind, predictions = self._write([row], [self._prediction("R1")])
        with self.assertRaises(SelectorError) as caught:
            ReplayAdapter(blind, predictions)
        self.assertEqual(caught.exception.reason, "replay_identity_mismatch")

    def test_g4_is_part_of_the_key(self) -> None:
        blind, predictions = self._write(
            [self._blind("R1", self.shas["a"], surface="the suv", g4=True)],
            [self._prediction("R1")],
        )
        adapter = ReplayAdapter(blind, predictions)
        self.assertEqual(adapter.row_ids_for(self.shas["a"], "the suv", True), ["R1"])
        self.assertEqual(adapter.row_ids_for(self.shas["a"], "the suv", False), [])


@unittest.skipUnless(
    (SFT002 / "data" / "eval.blind.jsonl").is_file()
    and (EVIDENCE / "P1-ENG-SFT-002-eval-manifest.json").is_file(),
    "SFT-002 冻结资产不在本机",
)
class FrozenReplayAssetTests(unittest.TestCase):
    """AC-9：对真实冻结资产核对两份 sha 并连接 609 行盲索引。"""

    def test_blind_and_prediction_sha_match_the_frozen_receipts(self) -> None:
        manifest = json.loads(
            (EVIDENCE / "P1-ENG-SFT-002-eval-manifest.json").read_text(encoding="utf-8")
        )
        summary = json.loads(
            (EVIDENCE / "P1-ENG-SFT-002-eval-summary.json").read_text(encoding="utf-8")
        )
        blind = SFT002 / "data" / "eval.blind.jsonl"
        predictions = next(
            SFT002.glob("returned/*/predictions/eval-adapter.jsonl"), None
        )
        if predictions is None:
            self.skipTest("C2 预测文件不在本机")
        adapter = ReplayAdapter(
            blind,
            predictions,
            expected_blind_sha256=manifest["files"]["eval.blind.jsonl"]["sha256"],
            expected_predictions_sha256=summary["predictions_sha256"],
        )
        frames = SFT002 / "upload" / "frames"
        row = json.loads(blind.read_text(encoding="utf-8").splitlines()[0])
        image = frames / Path(row["frame_path"]).name
        raw = adapter.predict_one("s1-q1", image, row["surface"], bool(row["g4"]))
        self.assertIsInstance(raw.raw_output, str)
        self.assertEqual(interpret(raw).status in {"unique", "ambiguous", "none"}, True)


class LocalHfAdapterTests(unittest.TestCase):
    """AC-8：`local-hf` 把一次查询包成一行 rows 调冻结的 `predict_rows`。"""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.root = Path(self._directory.name)
        self.image = self.root / "frame_0000000012.jpg"
        self.image.write_bytes(b"jpeg")

    def tearDown(self) -> None:
        self._directory.cleanup()

    def _adapter(self) -> LocalHfAdapter:
        return LocalHfAdapter(
            object(),
            output_directory=self.root / "queries",
            model_form="c2-merged",
            weights_sha256="w" * 64,
            base_repo_revision="89644892",
            device="mps",
        )

    def test_single_row_is_passed_through(self) -> None:
        captured: dict = {}

        def fake_predict_rows(loaded, rows, package_root, out_path, **kwargs):
            captured["rows"] = list(rows)
            captured["package_root"] = Path(package_root)
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            Path(out_path).write_text(
                json.dumps(
                    {
                        "row_id": rows[0]["row_id"],
                        "raw_output": UNIQUE,
                        "finish_reason": "stop",
                        "gen_tokens": 31,
                        "latency_ms": 900.0,
                        "prompt_sha256": "p" * 64,
                        "model_id": "w" * 64,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            return {"rows": 1}

        with patch("tools.eng_sft.train_lora.predict_rows", fake_predict_rows):
            raw = self._adapter().predict_one("s1-q1", self.image, "the red car", False)
        self.assertEqual(raw.raw_output, UNIQUE)
        self.assertEqual(raw.finish_reason, "stop")
        self.assertEqual(len(captured["rows"]), 1)
        row = captured["rows"][0]
        self.assertEqual(row["row_id"], "s1-q1")
        self.assertEqual(row["frame_path"], self.image.name)
        self.assertEqual(row["vocab"], "unity-v2")
        self.assertFalse(row["g4"])
        self.assertNotIn("gold", row)
        self.assertEqual(captured["package_root"], self.image.parent)
        self.assertTrue((self.root / "queries" / "s1-q1.jsonl").is_file())

    def test_g4_flag_is_forwarded(self) -> None:
        seen: dict = {}

        def fake_predict_rows(loaded, rows, package_root, out_path, **kwargs):
            seen["g4"] = rows[0]["g4"]
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            Path(out_path).write_text(
                json.dumps({"row_id": rows[0]["row_id"], "raw_output": NONE,
                            "finish_reason": "stop"}) + "\n",
                encoding="utf-8",
            )
            return {"rows": 1}

        with patch("tools.eng_sft.train_lora.predict_rows", fake_predict_rows):
            self._adapter().predict_one(
                "s1-q2",
                self.image,
                "the suv to the viewer's left of the bus",
                True,
            )
        self.assertTrue(seen["g4"])

    def test_backend_exception_becomes_backend_error(self) -> None:
        def explode(*args, **kwargs):
            raise RuntimeError("CUDA out of memory")

        with patch("tools.eng_sft.train_lora.predict_rows", explode):
            with self.assertRaises(SelectorError) as caught:
                self._adapter().predict_one("s1-q3", self.image, "the bus", False)
        # §3.2(b)：后端问题的状态是 `backend_error`，细分原因在 `reject_reason`。
        self.assertEqual(caught.exception.status, "backend_error")
        self.assertEqual(caught.exception.reason, "worker_died")
        self.assertIn(caught.exception.reason, REJECT_REASONS)

    def test_selector_errors_stay_inside_the_closed_sets(self) -> None:
        from controller.language_bridge import LanguageBridgeError

        with self.assertRaises(LanguageBridgeError):
            SelectorError("made_up_reason")
        with self.assertRaises(LanguageBridgeError):
            SelectorError("timeout", status="made_up_status")

    # --- AC-8 修订 2（P-A-6）---

    def test_the_exception_message_survives_into_the_detail(self) -> None:
        def explode(*args, **kwargs):
            raise RuntimeError("CUDA out of memory: tried to allocate 2.00 GiB")

        with patch("tools.eng_sft.train_lora.predict_rows", explode):
            with self.assertRaises(SelectorError) as caught:
                self._adapter().predict_one("s1-q3", self.image, "the bus", False)
        self.assertEqual(caught.exception.reason, "worker_died")
        self.assertIn("RuntimeError", caught.exception.detail)
        self.assertIn("CUDA out of memory", caught.exception.detail)

    def test_a_missing_prediction_record_uses_a_closed_set_reason(self) -> None:
        def write_nothing(loaded, rows, package_root, out_path, **kwargs):
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            Path(out_path).write_text("", encoding="utf-8")
            return {"rows": 0}

        with patch("tools.eng_sft.train_lora.predict_rows", write_nothing):
            with self.assertRaises(SelectorError) as caught:
                self._adapter().predict_one("s1-q4", self.image, "the bus", False)
        # `backend_error` 是 status 不是 reason；用它构造 SelectorError 会先抛契约错。
        self.assertIn(caught.exception.reason, REJECT_REASONS)
        self.assertEqual(caught.exception.reason, "worker_died")
        self.assertEqual(caught.exception.status, "backend_error")
class _ServerCase(unittest.TestCase):
    def _serve(self, adapter, *, t_hard_s: float = 60.0, monotonic=None):
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        runtime_kwargs = {"scratch_directory": Path(self._directory.name) / "images",
                          "t_hard_s": t_hard_s}
        if monotonic is not None:
            runtime_kwargs["monotonic"] = monotonic
        self.runtime = SingleFlightRuntime(adapter, **runtime_kwargs)
        self.server = build_server(self.runtime, port=0)
        self.addCleanup(self.server.server_close)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (self.server.shutdown(), thread.join(5)))
        return f"http://127.0.0.1:{self.server.server_port}"

    def _image(self) -> Path:
        path = Path(self._directory.name) / "frame.jpg"
        path.write_bytes(b"jpeg-payload")
        return path


class HttpAdapterTests(_ServerCase):
    """AC-8 修订 1：单工提交/轮询、忙不排队、放弃后 idle 前不重入、stuck 需重启。"""

    def test_round_trip_preserves_finish_reason_and_identity(self) -> None:
        base = self._serve(ScriptedAdapter([_raw(UNIQUE, finish_reason="length")]))
        adapter = HttpAdapter(base, t_ret_s=10.0, t_hard_s=30.0, poll_interval_s=0.01)
        raw = adapter.predict_one("s1-q1", self._image(), "the red car", False)
        self.assertEqual(raw.finish_reason, "length")
        self.assertEqual(interpret(raw).parse_error, "TRUNCATED")
        self.assertEqual(adapter.identity["backend"], "http")

    def test_multipart_carries_surface_and_g4(self) -> None:
        scripted = ScriptedAdapter([_raw(NONE), _raw(NONE)])
        base = self._serve(scripted)
        adapter = HttpAdapter(base, t_ret_s=10.0, t_hard_s=30.0, poll_interval_s=0.01)
        adapter.predict_one("s1-q1", self._image(), "the red car", False)
        adapter.predict_one(
            "s1-q2", self._image(), "the suv to the viewer's right of the bus", True
        )
        self.assertEqual(scripted.calls[0][2], "the red car")
        self.assertFalse(scripted.calls[0][3])
        self.assertTrue(scripted.calls[1][3])

    def test_server_busy_is_not_queued_and_blocks_re_entry(self) -> None:
        release = threading.Event()
        entered = threading.Event()

        def block(query_id: str) -> None:
            entered.set()
            release.wait(5)

        scripted = ScriptedAdapter([_raw(NONE), _raw(UNIQUE)], on_call=block)
        base = self._serve(scripted)
        first = HttpAdapter(base, t_ret_s=10.0, t_hard_s=30.0, poll_interval_s=0.01)
        worker = threading.Thread(
            target=first.predict_one,
            args=("s1-q1", self._image(), "the red car", False),
            daemon=True,
        )
        worker.start()
        self.assertTrue(entered.wait(5))

        second = HttpAdapter(base, t_ret_s=10.0, t_hard_s=30.0, poll_interval_s=0.01)
        with self.assertRaises(SelectorError) as caught:
            second.predict_one("s1-q2", self._image(), "the bus", False)
        self.assertEqual(caught.exception.reason, "timeout")
        self.assertTrue(second.awaiting_idle)

        # idle 之前不得重入：这一次连提交都不做。
        with self.assertRaises(SelectorError) as caught:
            second.predict_one("s1-q2", self._image(), "the bus", False)
        self.assertEqual(caught.exception.reason, "timeout")
        self.assertEqual(len(scripted.calls), 1)

        release.set()
        worker.join(5)
        # 服务端回到 idle 后才允许再次提交。
        raw = second.predict_one("s1-q3", self._image(), "the bus", False)
        self.assertEqual(raw.raw_output, UNIQUE)
        self.assertFalse(second.awaiting_idle)

    def test_client_deadline_abandons_without_re_entering(self) -> None:
        release = threading.Event()
        entered = threading.Event()

        def block(query_id: str) -> None:
            entered.set()
            release.wait(5)

        scripted = ScriptedAdapter([_raw(NONE)], on_call=block)
        base = self._serve(scripted)
        adapter = HttpAdapter(base, t_ret_s=0.2, t_hard_s=30.0, poll_interval_s=0.01)
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("s1-q1", self._image(), "the red car", False)
        self.assertEqual(caught.exception.reason, "timeout")
        self.assertTrue(adapter.awaiting_idle)
        self.assertTrue(entered.is_set())
        release.set()

    def test_server_hard_limit_marks_stuck_and_needs_a_restart(self) -> None:
        clock = {"value": 0.0}
        release = threading.Event()

        def block(query_id: str) -> None:
            clock["value"] += 120.0
            release.wait(5)

        scripted = ScriptedAdapter([_raw(NONE), _raw(NONE)], on_call=block)
        base = self._serve(
            scripted, t_hard_s=60.0, monotonic=lambda: clock["value"]
        )
        adapter = HttpAdapter(base, t_ret_s=5.0, t_hard_s=30.0, poll_interval_s=0.01)
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("s1-q1", self._image(), "the red car", False)
        self.assertIn(caught.exception.reason, {"worker_stuck", "timeout"})
        self.assertEqual(self.runtime.status()["state"], "stuck")
        release.set()
        self.runtime.join(5)
        # stuck 之后即使模型结束也不再接单。
        self.assertEqual(self.runtime.status()["state"], "stuck")
        self.assertFalse(
            self.runtime.submit("s1-q2", b"jpeg", "the bus", False)["accepted"]
        )

    def test_unreachable_server_is_worker_died(self) -> None:
        adapter = HttpAdapter(
            "http://127.0.0.1:9", t_ret_s=1.0, t_hard_s=2.0, poll_interval_s=0.01
        )
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("s1-q1", Path(__file__), "the bus", False)
        self.assertEqual(caught.exception.reason, "worker_died")

    def test_backend_failure_is_reported_as_backend_error(self) -> None:
        scripted = ScriptedAdapter([SelectorError("worker_died", "boom")])
        base = self._serve(scripted)
        adapter = HttpAdapter(base, t_ret_s=10.0, t_hard_s=30.0, poll_interval_s=0.01)
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("s1-q1", self._image(), "the red car", False)
        self.assertEqual(caught.exception.reason, "worker_died")
        self.assertEqual(caught.exception.status, "backend_error")

    # --- AC-8 修订 2（P-A-6）---

    def test_a_server_side_exception_message_reaches_the_client(self) -> None:
        class Exploding:
            identity = {"backend": "http", "model_form": "c2-merged"}

            def predict_one(self, query_id, image_path, surface, g4):
                raise RuntimeError("kernel panic in the vision tower")

        base = self._serve(Exploding())
        adapter = HttpAdapter(base, t_ret_s=10.0, t_hard_s=30.0, poll_interval_s=0.01)
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("s1-q1", self._image(), "the red car", False)
        self.assertEqual(caught.exception.reason, "worker_died")
        self.assertIn("RuntimeError", caught.exception.detail)
        self.assertIn("kernel panic", caught.exception.detail)

    def test_a_known_server_side_reason_is_preserved(self) -> None:
        base = self._serve(ScriptedAdapter([SelectorError("replay_miss", "no row")]))
        adapter = HttpAdapter(base, t_ret_s=10.0, t_hard_s=30.0, poll_interval_s=0.01)
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("s1-q1", self._image(), "the red car", False)
        self.assertEqual(caught.exception.reason, "replay_miss")
        self.assertIn("no row", caught.exception.detail)

    def test_an_unconfirmed_server_becomes_backend_fatal_past_t_hard(self) -> None:
        """断联/无法确认 idle 也有总截止，不能靠普通重试无限绕（AC-8 修订 1/2）。"""
        clock = {"value": 0.0}
        adapter = HttpAdapter(
            "http://127.0.0.1:9",
            t_ret_s=1.0,
            t_hard_s=5.0,
            poll_interval_s=0.01,
            monotonic=lambda: clock["value"],
        )
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("s1-q1", Path(__file__), "the bus", False)
        self.assertEqual(caught.exception.reason, "worker_died")
        self.assertFalse(adapter.fatal)

        clock["value"] += 6.0  # 超过 T_hard 仍未确认服务可用
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("s1-q2", Path(__file__), "the bus", False)
        self.assertEqual(caught.exception.reason, "worker_stuck")
        self.assertTrue(adapter.fatal)

        # fatal 之后只能重启：再提交仍是 worker_stuck，不重入服务端。
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("s1-q3", Path(__file__), "the bus", False)
        self.assertEqual(caught.exception.reason, "worker_stuck")

    def test_a_confirmed_idle_clears_the_unconfirmed_clock(self) -> None:
        clock = {"value": 0.0}
        scripted = ScriptedAdapter([_raw(NONE), _raw(UNIQUE)])
        base = self._serve(scripted)
        adapter = HttpAdapter(
            base,
            t_ret_s=10.0,
            t_hard_s=5.0,
            poll_interval_s=0.01,
            monotonic=lambda: clock["value"],
        )
        adapter.predict_one("s1-q1", self._image(), "the red car", False)
        self.assertIsNone(adapter._unconfirmed_since)
        clock["value"] += 100.0
        raw = adapter.predict_one("s1-q2", self._image(), "the bus", False)
        self.assertEqual(raw.raw_output, UNIQUE)
        self.assertFalse(adapter.fatal)

    # --- U-A-1：提交已被接纳但响应丢失 / 轮询断联 ---

    def _fake_http(self):
        """可控的 HTTP 传输：记录每次调用的方法与路径，可按需制造断联。"""
        import urllib.error

        class Fake:
            def __init__(self) -> None:
                self.calls: list[tuple[str, str]] = []
                self.state = "idle"
                self.fail = False

            def __call__(self, request, timeout):
                path = request.full_url.split("127.0.0.1:0", 1)[-1]
                self.calls.append((request.get_method(), path, timeout))
                if self.fail:
                    raise urllib.error.URLError("connection reset")
                if path == "/query":
                    self.state = "busy"
                    return b'{"accepted": true, "query_id": "q"}'
                if path == "/status":
                    return json.dumps({"state": self.state}).encode()
                if path.startswith("/result/"):
                    self.state = "idle"
                    return json.dumps(
                        {
                            "state": "done",
                            "record": {
                                "raw_output": NONE,
                                "finish_reason": "stop",
                                "gen_tokens": 5,
                                "latency_ms": 12.0,
                            },
                        }
                    ).encode()
                raise AssertionError(path)

        return Fake()

    def _jpeg(self) -> Path:
        """新测试不起真实服务，自己造一张图（`_image()` 依赖 `_serve()` 的临时目录）。"""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "frame.jpg"
        path.write_bytes(b"jpeg-payload")
        return path

    def _clocked_adapter(self, fake, clock, *, t_ret_s=10.0, t_hard_s=5.0):
        return HttpAdapter(
            "http://127.0.0.1:0",
            t_ret_s=t_ret_s,
            t_hard_s=t_hard_s,
            poll_interval_s=0.0,
            monotonic=lambda: clock["value"],
            sleep=lambda seconds: None,
            opener=fake,
        )

    def test_a_lost_response_forces_a_status_check_before_the_next_submit(self) -> None:
        fake = self._fake_http()
        clock = {"value": 0.0}
        adapter = self._clocked_adapter(fake, clock)
        fake.fail = True
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("q1", self._jpeg(), "the red car", False)
        self.assertEqual(caught.exception.reason, "worker_died")
        self.assertTrue(adapter.awaiting_idle)

        fake.fail = False
        submits_before = [call for call in fake.calls if call[0] == "POST"]
        fake.state = "busy"  # 服务端还没回到 idle
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("q2", self._jpeg(), "the bus", False)
        self.assertEqual(caught.exception.reason, "timeout")
        # 下一次请求必须是状态确认，而不是直接 POST。
        self.assertEqual(fake.calls[-1][:2], ("GET", "/status"))
        self.assertEqual(
            [call for call in fake.calls if call[0] == "POST"], submits_before
        )

    def test_the_total_deadline_is_anchored_at_the_original_submission(self) -> None:
        fake = self._fake_http()
        clock = {"value": 0.0}
        adapter = self._clocked_adapter(fake, clock, t_hard_s=5.0)

        # 提交在 t=0 被接纳；轮询在 t=3 断联（此时离提交 3 s，未到 T_hard）。
        original_call = fake.__call__

        def failing_after_submit(request, timeout):
            if request.get_method() == "GET" and "/result/" in request.full_url:
                clock["value"] = 3.0
                raise __import__("urllib.error", fromlist=["error"]).URLError("reset")
            return original_call(request, timeout)

        adapter._opener = failing_after_submit
        with self.assertRaises(SelectorError):
            adapter.predict_one("q1", self._jpeg(), "the red car", False)

        # t=6：离断联才 3 s，但离**原提交**已 6 s > T_hard=5 → 必须已到期。
        clock["value"] = 6.0
        with self.assertRaises(SelectorError) as caught:
            adapter.health_check()
        self.assertEqual(caught.exception.reason, "worker_stuck")
        self.assertTrue(adapter.fatal)

    def test_health_check_expires_without_another_query(self) -> None:
        """有界退出不依赖「再 ask 一次」：操作者不再发查询也会到期。"""
        fake = self._fake_http()
        clock = {"value": 0.0}
        adapter = self._clocked_adapter(fake, clock, t_hard_s=5.0)
        fake.fail = True
        with self.assertRaises(SelectorError):
            adapter.predict_one("q1", self._jpeg(), "the red car", False)
        calls = len(fake.calls)

        adapter.health_check()  # 未到期：不抛、也不打服务端
        clock["value"] = 99.0
        with self.assertRaises(SelectorError) as caught:
            adapter.health_check()
        self.assertEqual(caught.exception.reason, "worker_stuck")
        self.assertEqual(len(fake.calls), calls)

    def test_an_unexplainable_result_state_also_blocks_re_entry(self) -> None:
        """无法解释的 state 同样是「服务端状态不明」：下一次必须先确认 idle。"""
        fake = self._fake_http()
        clock = {"value": 0.0}
        adapter = self._clocked_adapter(fake, clock, t_hard_s=5.0)

        original = fake.__call__

        def weird_result(request, timeout):
            if "/result/" in request.full_url:
                return b'{"state": "weird"}'
            return original(request, timeout)

        adapter._opener = weird_result
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("q1", self._jpeg(), "the red car", False)
        self.assertEqual(caught.exception.reason, "worker_died")
        self.assertTrue(adapter.awaiting_idle)
        clock["value"] = 99.0
        with self.assertRaises(SelectorError) as caught:
            adapter.health_check()
        self.assertEqual(caught.exception.reason, "worker_stuck")

    def test_each_http_exchange_carries_a_shrinking_deadline(self) -> None:
        """每次 I/O 的截止是 `min(5 s, 本次剩余等待)`，不是固定 5 s。"""
        fake = self._fake_http()
        clock = {"value": 0.0}
        adapter = self._clocked_adapter(fake, clock, t_ret_s=100.0, t_hard_s=2.0)

        original = fake.__call__

        def slow_poll(request, timeout):
            if "/result/" in request.full_url:
                # 自己记一笔：这一支不再经过 `fake.__call__`。
                fake.calls.append(("GET", "/result/q1", timeout))
                clock["value"] += 1.0
                return b'{"state": "busy"}'
            return original(request, timeout)

        adapter._opener = slow_poll
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("q1", self._jpeg(), "the red car", False)
        self.assertEqual(caught.exception.reason, "worker_stuck")
        timeouts = [call[2] for call in fake.calls if call[1].startswith("/result/")]
        self.assertTrue(timeouts)
        self.assertLess(timeouts[-1], 5.0)
        self.assertLessEqual(timeouts[-1], timeouts[0])

    def test_a_confirmed_idle_after_a_disconnection_restores_service(self) -> None:
        fake = self._fake_http()
        clock = {"value": 0.0}
        adapter = self._clocked_adapter(fake, clock, t_hard_s=50.0)
        fake.fail = True
        with self.assertRaises(SelectorError):
            adapter.predict_one("q1", self._jpeg(), "the red car", False)
        self.assertTrue(adapter.awaiting_idle)

        fake.fail = False
        fake.state = "idle"
        marker = len(fake.calls)
        raw_selection = adapter.predict_one("q2", self._jpeg(), "the bus", False)
        self.assertEqual(raw_selection.raw_output, NONE)
        # 恢复那一次必须先确认 idle 再提交，而不是直接 POST。
        self.assertEqual(
            [call[:2] for call in fake.calls[marker : marker + 2]],
            [("GET", "/status"), ("POST", "/query")],
        )
        self.assertFalse(adapter.awaiting_idle)
        self.assertIsNone(adapter._unconfirmed_since)
        adapter.health_check()  # 恢复之后不再到期

        # 锚点随成功确认而重置：再断联一次，计时应从**第二次提交**起算。
        clock["value"] = 10.0
        fake.fail = True
        with self.assertRaises(SelectorError):
            adapter.predict_one("q3", self._jpeg(), "the bus", False)
        clock["value"] = 10.0 + adapter.t_hard_s - 1.0
        adapter.health_check()  # 距第二次提交未满 T_hard
        clock["value"] = 10.0 + adapter.t_hard_s + 1.0
        with self.assertRaises(SelectorError) as caught:
            adapter.health_check()
        self.assertEqual(caught.exception.reason, "worker_stuck")
    # --- U-A-1 残留：恢复用的 `GET /status` 也归原在途任务的总截止管 ---

    def test_the_recovery_status_check_shrinks_to_the_remaining_budget(self) -> None:
        """恢复确认不是固定 5 s：截止按**原提交**起算的剩余等待收缩（AC-8 修订 1）。"""
        fake = self._fake_http()
        clock = {"value": 0.0}
        adapter = self._clocked_adapter(fake, clock, t_ret_s=100.0, t_hard_s=5.0)
        fake.fail = True
        with self.assertRaises(SelectorError):
            adapter.predict_one("q1", self._jpeg(), "the red car", False)  # 锚点 = t0 = 0
        self.assertTrue(adapter.awaiting_idle)

        fake.fail = False
        fake.state = "busy"  # 服务端还没回到 idle
        clock["value"] = 3.0
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("q2", self._jpeg(), "the bus", False)
        self.assertEqual(caught.exception.reason, "timeout")
        status_calls = [call for call in fake.calls if call[1] == "/status"]
        self.assertEqual(len(status_calls), 1)
        # 缺省 5 s 会整整越过 `T_hard`；这里必须是 min(5, 5-3)=2。
        self.assertAlmostEqual(status_calls[-1][2], 2.0)

    def test_a_late_idle_past_the_total_deadline_is_still_fatal(self) -> None:
        """确认迟到：`GET /status` 跨过原总截止才回 idle → 仍 `backend_fatal`，不再提交。"""
        fake = self._fake_http()
        clock = {"value": 0.0}
        adapter = self._clocked_adapter(fake, clock, t_ret_s=100.0, t_hard_s=5.0)
        fake.fail = True
        with self.assertRaises(SelectorError):
            adapter.predict_one("q1", self._jpeg(), "the red car", False)  # 锚点 = t0 = 0

        fake.fail = False
        fake.state = "idle"
        original = fake.__call__

        def slow_status(request, timeout):
            if request.full_url.endswith("/status"):
                clock["value"] += 3.0  # 这次确认本身耗到 t=7 > T_hard=5
            return original(request, timeout)

        adapter._opener = slow_status
        clock["value"] = 4.0  # 发起时还没到期
        posts_before = [call for call in fake.calls if call[0] == "POST"]
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("q2", self._jpeg(), "the bus", False)
        self.assertEqual(caught.exception.reason, "worker_stuck")
        self.assertTrue(adapter.fatal)
        self.assertTrue(adapter.awaiting_idle)
        self.assertIsNotNone(adapter._unconfirmed_since)  # 迟到的 idle 不清零锚点
        self.assertEqual(
            [call for call in fake.calls if call[0] == "POST"], posts_before
        )

    def test_a_fatal_raised_during_the_status_check_blocks_the_submit(self) -> None:
        """会话线程在这次确认期间判死后端：恢复线程不得接着 POST（AC-17 修订 1）。"""
        fake = self._fake_http()
        clock = {"value": 0.0}
        adapter = self._clocked_adapter(fake, clock, t_ret_s=100.0, t_hard_s=50.0)
        fake.fail = True
        with self.assertRaises(SelectorError):
            adapter.predict_one("q1", self._jpeg(), "the red car", False)

        fake.fail = False
        fake.state = "idle"
        original = fake.__call__

        def fatal_during_status(request, timeout):
            document = original(request, timeout)
            if request.full_url.endswith("/status"):
                # 会话每 tick 调一次 `health_check()`，到期时它就是这样置 fatal 的；
                # 这里单独模拟并发判死，时钟不动，好把这条检查与总截止分开验。
                adapter.fatal = True
            return document

        adapter._opener = fatal_during_status
        posts_before = [call for call in fake.calls if call[0] == "POST"]
        with self.assertRaises(SelectorError) as caught:
            adapter.predict_one("q2", self._jpeg(), "the bus", False)
        self.assertEqual(caught.exception.reason, "worker_stuck")
        self.assertEqual(
            [call for call in fake.calls if call[0] == "POST"], posts_before
        )


class LatencyMeasurementTests(unittest.TestCase):
    """AC-10：测量口径（3 预热 + 32 计时、p95 取第 31 个、两轮 INVALID → FAIL）。"""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.root = Path(self._directory.name)
        self.image = self.root / "frame.jpg"
        self.image.write_bytes(b"jpeg")
        self.rows = [
            {"row_id": f"R{index}", "image_path": self.image, "surface": "the bus", "g4": False}
            for index in range(32)
        ]

    def tearDown(self) -> None:
        self._directory.cleanup()

    def _clock(self, readings):
        """按顺序返回预先排好的绝对时刻（每次调用两读：开始、结束）。"""
        state = {"index": 0}

        def monotonic() -> float:
            index = min(state["index"], len(readings) - 1)
            state["index"] += 1
            return readings[index]

        return monotonic

    def test_p95_is_the_thirty_first_sample(self) -> None:
        from tools.language_latency import (
            TIMED_SAMPLES,
            WARMUP_ROUNDS,
            measure_round,
            summarize_round,
        )

        # 每次调用消耗两个时钟读数（开始、结束）；让第 i 个计时样本耗时 (i+1) ms。
        readings = []
        for index in range(WARMUP_ROUNDS):
            readings.extend([float(index), float(index) + 0.001])
        for index in range(TIMED_SAMPLES):
            start = 100.0 + index
            readings.extend([start, start + (index + 1) / 1000.0])
        adapter = ScriptedAdapter([_raw(UNIQUE)] * (WARMUP_ROUNDS + TIMED_SAMPLES))
        result = measure_round(adapter, self.rows, monotonic=self._clock(readings))
        summary = summarize_round(result)
        self.assertEqual(summary["verdict"], "OK")
        self.assertEqual(summary["timed_samples"], 32)
        self.assertEqual(summary["warmup_samples"], 3)
        self.assertAlmostEqual(summary["p95_ms"], 31.0, places=6)
        self.assertAlmostEqual(summary["max_ms"], 32.0, places=6)
        self.assertEqual(len(summary["warmup_latency_ms"]), 3)

    def test_one_failed_sample_invalidates_the_round(self) -> None:
        from tools.language_latency import WARMUP_ROUNDS, measure_round, summarize_round

        responses = [_raw(UNIQUE)] * (WARMUP_ROUNDS + 10)
        responses.append(SelectorError("timeout", "sample timed out"))
        responses.extend([_raw(UNIQUE)] * 40)
        result = measure_round(ScriptedAdapter(responses), self.rows)
        summary = summarize_round(result)
        self.assertEqual(summary["verdict"], "INVALID")
        self.assertEqual(len(summary["failures"]), 1)
        self.assertIsNone(summary["p95_ms"])

    def test_a_late_local_return_is_not_a_valid_latency_sample(self) -> None:
        from tools.language_latency import measure_round, summarize_round
        readings = [value for index in range(35) for value in (index * 100., index * 100. + 61.)]
        result = measure_round(ScriptedAdapter([_raw(UNIQUE)] * 35), self.rows,
                               monotonic=self._clock(readings))
        summary = summarize_round(result)
        self.assertEqual(summary["verdict"], "INVALID")
        self.assertEqual(len(summary["failures"]), 35)
        self.assertIsNone(summary["p95_ms"])

    def test_second_invalid_round_fails_the_host(self) -> None:
        from tools.language_latency import measure_host

        def factory():
            return ScriptedAdapter([SelectorError("timeout", "always")] * 100)

        report = measure_host(
            factory,
            self.rows,
            host="mac",
            backend="local-hf",
            model_form="c2-merged",
            hz=5.0,
            retained_frame_count=128,
        )
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["tier"], "FAIL")
        self.assertIsNone(report["p95_s"])
        self.assertEqual(len(report["rounds"]), 2)

    def test_load_failure_is_a_fail_without_running_rounds(self) -> None:
        from tools.language_latency import measure_host

        def factory():
            raise SelectorError("load_failure", "OOM")

        report = measure_host(
            factory,
            self.rows,
            host="mac",
            backend="local-hf",
            model_form="c2-merged",
            hz=5.0,
            retained_frame_count=128,
        )
        self.assertEqual(report["verdict"], "FAIL")
        self.assertIn("load_failure", report["load_error"])

    def test_k_receipt_picks_the_host_and_refuses_when_neither_qualifies(self) -> None:
        from tools.language_latency import build_receipt_document

        mac = {"tier": "B", "p95_s": 7.0, "hz": 5.0, "retained_frame_count": 128,
               "backend": "local-hf", "model_form": "c2-merged", "model_identity": {}}
        gpu = {"tier": "A", "p95_s": 1.4, "hz": 5.0, "retained_frame_count": 128,
               "backend": "http", "model_form": "c2-merged", "model_identity": {}}
        document = build_receipt_document(mac, gpu)
        self.assertEqual(document["decision"], "5060")
        self.assertEqual(document["k_ret"], 9)
        self.assertEqual(document["k_conf"], 50)
        self.assertEqual(document["k_pub"], 2)
        undecided = build_receipt_document(
            {"tier": "C", "p95_s": 40.0}, {"tier": "FAIL", "p95_s": None}
        )
        self.assertEqual(undecided["decision"], "HOST_UNDECIDED")
        self.assertNotIn("k_ret", undecided)

    def test_merge_equivalence_report(self) -> None:
        from tools.language_latency import merge_equivalence

        merged = ScriptedAdapter([_raw(UNIQUE)] * 32)
        adapter = ScriptedAdapter([_raw(UNIQUE)] * 32)
        report = merge_equivalence(merged, adapter, self.rows)
        self.assertTrue(report["equivalent"])
        self.assertEqual(report["selected_model_form"], "c2-merged")
        self.assertEqual(report["rows"], 32)

        drifted = ScriptedAdapter([_raw(NONE)] * 32)
        report = merge_equivalence(
            ScriptedAdapter([_raw(UNIQUE)] * 32), drifted, self.rows
        )
        self.assertFalse(report["equivalent"])
        self.assertEqual(report["selected_model_form"], "c2-adapter")

    def test_missing_host_report_cannot_freeze_a_receipt(self) -> None:
        from tools.language_latency import build_receipt_document
        mac = {"tier": "A", "p95_s": 1.0, "hz": 5.0, "retained_frame_count": 128,
               "backend": "local-hf", "model_form": "c2-merged", "model_identity": {}}
        report = build_receipt_document(mac, None)
        self.assertEqual(report["decision"], "MEASUREMENT_INCOMPLETE")
        self.assertEqual(report["missing_hosts"], ["5060"])
        self.assertNotIn("k_ret", report)

    def test_smoke_accepts_frozen_sample_ids_and_checks_source_bytes(self) -> None:
        from tools.language_latency import read_smoke_rows
        from controller.language_selector import sha256_file
        smoke = self.root / "smoke.jsonl"
        smoke.write_text(json.dumps({"sample_id": "s-frozen", "frame_path": self.image.name,
            "surface": "the taxi", "frame_sha256": sha256_file(self.image)}) + "\n")
        self.assertEqual(read_smoke_rows(smoke, self.root)[0]["row_id"], "s-frozen")
        self.image.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            read_smoke_rows(smoke, self.root)

    def test_equivalence_releases_first_model_before_loading_second(self) -> None:
        import weakref
        from tools.language_latency import sequential_merge_equivalence
        refs = []
        calls = []
        class Recording(ScriptedAdapter):
            def predict_one(inner, query_id, *args):
                calls.append(query_id)
                return super().predict_one(query_id, *args)
        def first():
            model = Recording([SelectorError("worker_died", "first row failure")] + [_raw(UNIQUE)] * 31)
            refs.append(weakref.ref(model))
            return model
        def second():
            self.assertIsNone(refs[0]())
            return Recording([_raw(UNIQUE)] * 32)
        report = sequential_merge_equivalence(first, second, self.rows)
        self.assertEqual(len(calls), 64)
        self.assertFalse(report["equivalent"])
        self.assertTrue(all(row["equivalent"] for row in report["comparisons"][1:]))
        self.assertEqual(len(report["raw_records"]["adapter"]), 32)

    def test_equivalence_rejects_a_short_smoke_before_loading(self) -> None:
        from tools.language_latency import sequential_merge_equivalence
        def forbidden():
            self.fail("must reject before loading a model")
        with self.assertRaises(ValueError):
            sequential_merge_equivalence(forbidden, forbidden, self.rows[:31])

    def test_merged_identity_tracks_the_actual_weight_bytes(self) -> None:
        from controller.language_selector import load_local_adapter, sha256_file
        from tools.eng_sft import train_lora
        weights = self.root / "model.safetensors"
        weights.write_bytes(b"first model")
        (self.root / "._model.safetensors").write_bytes(b"AppleDouble metadata, not a weight shard")
        with patch.object(train_lora, "load_model", return_value=object()):
            def load():
                return load_local_adapter(source=self.root, adapter_dir=None, device="mps",
                    model_form="c2-merged", output_directory=self.root / "queries")
            first = load().identity["weights_sha256"]
            self.assertEqual(first, sha256_file(weights))
            weights.write_bytes(b"different merged weights")
            self.assertNotEqual(load().identity["weights_sha256"], first)


@unittest.skipUnless(
    (SFT002 / "upload" / "frames").is_dir()
    and any(SFT002.glob("returned/*/predictions/eval-adapter.jsonl")),
    "SFT-002 冻结资产不在本机",
)
class ReplayDemoTests(unittest.TestCase):
    """AC-9：`replay-demo` 覆盖 designate 四路径与 verify 五 verdict。

    AC-5 修订 1 之后没有预览就不能确认播种，所以走查必须在有 Pillow 的解释器上跑；
    系统解释器没有 Pillow 时本类整体跳过，证据取 `.venv-yoloe`（同版 pillow）那一跑。
    """

    def setUp(self) -> None:
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("本解释器没有 Pillow；replay-demo 证据取有 Pillow 的那一跑")

    def test_demo_covers_every_path(self) -> None:
        from controller.language_demo import build_demo_assets, run_demo

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        assets = build_demo_assets(
            frames_dir=SFT002 / "upload" / "frames",
            blind_path=SFT002 / "data" / "eval.blind.jsonl",
            adapter_predictions=next(
                SFT002.glob("returned/*/predictions/eval-adapter.jsonl")
            ),
            base_predictions=next(
                SFT002.glob("returned/*/predictions/zero-shot.jsonl"), None
            ),
            destination=root / "assets",
        )
        report = run_demo(assets=assets, session_root=root)
        self.assertEqual(report["final_state"], "TERMINAL")
        self.assertEqual(
            sorted(report["verify_verdicts"]),
            ["ambiguous", "consistent", "drift", "inconclusive", "none"],
        )
        for status in ("unique", "ambiguous", "none", "parse_failed", "retry_exhausted"):
            self.assertIn(status, report["designate_statuses"])
        self.assertEqual(len(report["retired_track_ids"]), 2)
        self.assertGreater(report["publish_receipts"]["written"], 0)
        self.assertEqual(report["publish_receipts"]["rejected"], 0)
        manifest = json.loads(assets.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["rows"]), 4)
        for row in manifest["rows"]:
            self.assertIn("source_predictions", row)


class FrozenContractTests(unittest.TestCase):
    """AC-8：观测桥的 schema 常量与 `confidence_source` 闭集不得被本项改动。"""

    def test_observation_protocol_constants(self) -> None:
        from controller import tracking_entry
        from controller.track_loop import TRACKING_STATES

        source = Path(tracking_entry.__file__).read_text(encoding="utf-8")
        self.assertIn('protocol_name="tethered-tracking-observation/v1"', source)
        self.assertIn('atomic_write("tracking_observation.json"', source)
        self.assertEqual(
            TRACKING_STATES, {"TRACKING", "LOST", "ERROR_REINIT_REQUIRED"}
        )

    def test_confidence_source_closed_set_is_unchanged(self) -> None:
        from controller import track_loop

        source = Path(track_loop.__file__).read_text(encoding="utf-8")
        self.assertIn('if source not in {"tracker", "placeholder"}:', source)
        self.assertIn('return TrackerResult.lost("invalid_confidence_source")', source)


class WindowsEngineImportTests(unittest.TestCase):
    def test_windows_engine_import_does_not_fabricate_rss(self):
        import builtins
        import sys
        from controller.language_selector import inference_engine
        real_import = builtins.__import__

        def without_unix_resource(name, *args, **kwargs):
            if name == "resource" and "resource" not in sys.modules:
                raise ImportError("resource is Unix-only")
            return real_import(name, *args, **kwargs)

        with patch.dict(sys.modules), patch("sys.platform", "win32"):
            sys.modules.pop("resource", None)
            with patch("builtins.__import__", side_effect=without_unix_resource):
                engine = inference_engine()
            self.assertTrue(callable(engine.load_model))
            with self.assertRaisesRegex(OSError, "unavailable on Windows"):
                sys.modules["resource"].getrusage(0)


if __name__ == "__main__":
    unittest.main()
