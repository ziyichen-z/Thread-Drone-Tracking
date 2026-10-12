"""P1-ENG-LOOP-002 AC-6（§3.2 / A8）：jetson 单宿主测量报告、K 收据生成器与会话启动校验。

零模型、零网络：HTTP 服务端用注入的 opener 替身（返回 `/status`、`/query`、`/result` 的闭集 JSON），
部署摘要与桌面重算在临时源码根（只复制部署清单文件）上求值，git 状态注入。两宿主旧路径与
candidates 路径的既有用例在 `test_language_k_binding.py`/`test_language_loop.py`，本文件不改它们。
"""

from __future__ import annotations

import contextlib
from dataclasses import replace
import io
import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import urllib.request

from controller import language_bridge as bridge
from controller.language_loop import (
    ConfigMismatch,
    JETSON_HOST,
    KReceipt,
    LanguageSession,
    SessionConfig,
    build_k_receipt,
    validate_measurement_sources,
)
from controller.language_selector import HttpAdapter, SelectorError, _prompt_identity
from tools import language_latency as latency
from tools.eng_loop2 import deploy_digest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HEAD = "c" * 40
ENDPOINT = "http://board.example:8762"
MACHINE = "jetson-board"
UNIQUE = '{"status": "unique", "bbox_2d": [100, 200, 300, 400]}'
SCHEMA_BREAK = '{"status": "unique", "box": [1, 2, 3, 4]}'


def copy_deploy_root(destination: Path) -> Path:
    """部署清单所列文件复制到临时源码根（桌面重算与板端同一函数、同一文件集）。"""
    for relative in deploy_digest.manifest_paths(PROJECT_ROOT):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, target)
    return destination


def llama_identity(code_root: Path, **changes) -> dict:
    digests = deploy_digest.desktop_identity_digests(code_root)
    identity = {
        "backend": "http",
        "model_form": "c2-merged",
        "base_repo_revision": None,
        "weights_sha256": "a" * 64,
        "device": "cuda",
        **_prompt_identity(False),
        "mmproj_sha256": "b" * 64,
        "runtime_binary_sha256": "d" * 64,
        "runtime_build": "b11381",
        "quantization": "Q4_K_M",
        "response_format_sha256": digests["response_format_sha256"],
        "decode_config_sha256": digests["decode_config_sha256"],
    }
    identity.update(changes)
    return identity


#: `FakeService` 的输出标记：该次推理在服务端失败（回包 `state: failed`），客户端得到 `SelectorError`。
FAILED_INFERENCE = object()


class FakeService:
    """`language_serve` llama 分支的回包替身（HttpAdapter 的 opener 注入点）。

    AC-7 修订 3：绑定六键 llama 身份的客户端以 `GET /result/<id>?wait_s=<w>` 长轮询；替身与真实服务
    一样分离 query_id 与参数并回显 `wait_s`。`status_error` 非空时 `/status` 回包缺 `state`（身份探针/绑定失败）。"""

    def __init__(self, identity: dict, serve_code: str, machine: str = MACHINE, outputs=()):
        self.identity = identity
        self.serve_code = serve_code
        self.machine = machine
        self.outputs = list(outputs)
        self.pending: dict[str, object] = {}
        self.calls: list[tuple[str, str]] = []
        self.status_ok = True

    def __call__(self, request: urllib.request.Request, timeout: float) -> bytes:
        target = request.full_url.split("://", 1)[1].split("/", 1)[1]
        self.calls.append((request.get_method(), "/" + target))
        path, _, query = target.partition("?")
        document: dict = {"model_identity": self.identity}
        if path == "status":
            if self.status_ok:
                document.update(state="idle", serve_code_sha256=self.serve_code, machine=self.machine)
            else:
                document = {"error": "boom"}
        elif path == "query":
            query_id = request.data.split(b'name="query_id"\r\n\r\n', 1)[1].split(b"\r\n", 1)[0].decode()
            self.pending[query_id] = self.outputs.pop(0) if self.outputs else UNIQUE
            document.update(accepted=True, query_id=query_id)
        elif path.startswith("result/"):
            query_id = path.split("/", 1)[1]
            if query:
                document["wait_s"] = float(query.split("=", 1)[1])
            text = self.pending.pop(query_id)
            if text is FAILED_INFERENCE:
                document.update(state="failed", query_id=query_id, error="worker_died", detail="injected")
            else:
                document.update(
                    state="done",
                    query_id=query_id,
                    record={"raw_output": text, "finish_reason": "stop", "gen_tokens": 20,
                            "latency_ms": 10.0, "prompt_sha256": "p" * 64, "model_id": "a" * 64},
                )
        return json.dumps(document).encode("utf-8")

    def count(self, method: str, prefix: str) -> int:
        return sum(1 for seen_method, seen_path in self.calls if seen_method == method and seen_path.startswith(prefix))


class JetsonFixture(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.code_root = copy_deploy_root(self.root / "code")
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        self.identity = llama_identity(self.code_root)
        self.serve_code = deploy_digest.deploy_digest(self.code_root)
        self.report = {
            "work_id": "P1-ENG-LOOP-002",
            "host": JETSON_HOST,
            "backend": "http",
            "model_form": "c2-merged",
            "verdict": "OK",
            "tier": "A",
            "p95_s": 2.0,
            "hz": 5.0,
            "retained_frame_count": 128,
            "model_identity": dict(self.identity),
            "transport": {"endpoint": ENDPOINT},
            "environment": {"python": "3", "git_head": HEAD, "dirty": False},
            "serve_code_sha256": self.serve_code,
            "machine": MACHINE,
        }
        self.report_path = self.root / "jetson-report.json"
        self.write_report()

    def write_report(self, report: dict | None = None) -> None:
        self.report_path.write_text(json.dumps(report or self.report, sort_keys=True), encoding="utf-8")

    def scenario(self) -> dict:
        from controller.language_loop import read_scenario  # noqa: PLC0415

        return read_scenario(self.runtime)

    def generate(self, report: dict | None = None, *, head: str = HEAD, dirty: bool = False) -> dict:
        return latency.build_single_host_receipt(
            report if report is not None else self.report,
            self.report_path,
            scenario=self.scenario(),
            code_root=self.code_root,
            git_state=lambda: (head, dirty),
        )

    def receipt(self, **changes) -> KReceipt:
        document = self.generate()
        document.update(changes)
        return KReceipt.from_document(document)

    def session(self, receipt: KReceipt | None = None, *, service: FakeService | None = None,
                endpoint: str = ENDPOINT, head: str = HEAD, dirty: bool = False) -> LanguageSession:
        receipt = receipt or self.receipt()
        service = service or FakeService(dict(receipt.model_identity), self.serve_code)
        adapter = HttpAdapter(endpoint, t_ret_s=receipt.t_ret_s, t_hard_s=60.0, opener=service,
                              model_form="c2-merged")
        adapter.identity = dict(receipt.model_identity)
        session = LanguageSession(
            SessionConfig(
                session_id="jet1",
                session_root=self.root / "sessions",
                runtime=self.runtime,
                receipt=receipt,
                adapter=adapter,
                code_root=self.code_root,
                git_state=lambda: (head, dirty),
                pid=4242,
                is_alive=lambda pid: True,
            )
        )
        self.addCleanup(session.close)
        return session

    def assert_refused(self, regex: str = "", *, before_dirs: bool = True, **kwargs) -> None:
        with self.assertRaisesRegex(ConfigMismatch, regex):
            self.session(**kwargs)
        if before_dirs:
            # jetson 新增校验都在建会话目录之前；hz/R 沿用既有检查（其位置在建目录之后，未改）。
            self.assertFalse((self.root / "sessions").exists(), "refusal must happen before the session directory")


class SingleHostReceiptTests(JetsonFixture):
    """`k-receipt --single-host jetson`：由报告生成、六键/身份/部署摘要/代码版本逐项核对。"""

    def test_generator_binds_report_bytes_and_derives_k_from_report_and_scenario(self) -> None:
        document = self.generate()
        receipt = KReceipt.from_document(document)
        self.assertEqual((receipt.host, receipt.backend, receipt.model_form), ("jetson", "http", "c2-merged"))
        self.assertEqual(receipt.k_ret, math.ceil(2.0 * 5.0) + 2)
        self.assertEqual((receipt.retained_frame_count, receipt.scenario_id), (128, "deterministic-loop-default"))
        self.assertEqual(set(document["source_reports"]), {"jetson"})
        self.assertEqual(document["source_reports"]["jetson"]["sha256"], deploy_digest.sha256_path(self.report_path))
        self.assertTrue(document["qualifies"])
        self.assertEqual(dict(receipt.model_identity), self.identity)
        self.assertEqual(validate_measurement_sources(receipt), self.report)

    def test_generator_rejects_every_listed_mismatch(self) -> None:
        cases = {
            "host": dict(self.report, host="5060"),
            "verdict": dict(self.report, verdict="FAIL", p95_s=None),
            "backend": dict(self.report, backend="local-hf"),
            "model_form": dict(self.report, model_form="c2-adapter"),
            "transport": {k: v for k, v in self.report.items() if k != "transport"},
            "git_head": dict(self.report, environment={"dirty": False}),
            "dirty": dict(self.report, environment={"git_head": HEAD, "dirty": True}),
            "serve_code": dict(self.report, serve_code_sha256="e" * 64),
            "machine": dict(self.report, machine=""),
            "response_format": dict(self.report, model_identity=dict(self.identity, response_format_sha256="e" * 64)),
            "decode": dict(self.report, model_identity=dict(self.identity, decode_config_sha256="e" * 64)),
            "prompt": dict(self.report, model_identity=dict(self.identity, prompt_template_sha256="e" * 64)),
            "partial_keys": dict(self.report, model_identity={k: v for k, v in self.identity.items() if k != "mmproj_sha256"}),
            "no_keys": dict(self.report, model_identity={k: v for k, v in self.identity.items() if k not in bridge.LLAMA_IDENTITY_KEYS}),
            "hex64": dict(self.report, model_identity=dict(self.identity, mmproj_sha256="B" * 64)),
            "runtime_build": dict(self.report, model_identity=dict(self.identity, runtime_build="11381")),
            "quantization": dict(self.report, model_identity=dict(self.identity, quantization="Q8_0")),
            "identity_backend": dict(self.report, model_identity=dict(self.identity, backend="local-hf")),
            "identity_form": dict(self.report, model_identity=dict(self.identity, model_form="base")),
            "hz": dict(self.report, hz=10.0),
        }
        for name, report in cases.items():
            with self.subTest(name=name), self.assertRaises(latency.ReceiptRejected):
                self.generate(report)
        with self.assertRaises(latency.ReceiptRejected):
            latency.build_single_host_receipt(None, self.report_path, scenario=self.scenario(),
                                              code_root=self.code_root, git_state=lambda: (HEAD, False))  # 报告缺失
        with self.assertRaisesRegex(latency.ReceiptRejected, "HEAD"):
            self.generate(head="f" * 40)
        with self.assertRaisesRegex(latency.ReceiptRejected, "dirty"):
            self.generate(dirty=True)
        (self.code_root / "config" / "vlm-three-state.schema.json").write_text("{}\n")
        with self.assertRaisesRegex(latency.ReceiptRejected, "serve_code_sha256"):
            self.generate()

    def test_cli_exit_codes_0_6_8_and_two_host_path_untouched(self) -> None:
        out = self.root / "k.json"

        def run(*argv: str) -> int:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with patch.object(latency, "code_git_state", lambda root: (HEAD, False)), patch.object(
                    latency, "PROJECT_ROOT", self.code_root
                ), patch.object(latency.deploy_digest, "desktop_identity_digests",
                                lambda root, _orig=deploy_digest.desktop_identity_digests: _orig(self.code_root)):
                    return latency.main(["k-receipt", *argv, "--runtime", str(self.runtime), "--out", str(out)])

        self.assertEqual(run("--single-host", "jetson", "--report", str(self.report_path)), 0)
        self.assertEqual(json.loads(out.read_text())["host"], "jetson")
        out.unlink()
        self.write_report(dict(self.report, model_identity=dict(self.identity, quantization="Q8_0")))
        self.assertEqual(run("--single-host", "jetson", "--report", str(self.report_path)), 6)
        self.assertFalse(out.exists(), "exit 6 must not leave a receipt")
        self.assertEqual(run("--single-host", "jetson", "--report", str(self.root / "missing.json")), 6)
        self.assertEqual(run("--single-host", "jetson"), 6)
        self.write_report(dict(self.report, p95_s=30.0))  # K_ret + K_conf + K_pub > R − 8
        self.assertEqual(run("--single-host", "jetson", "--report", str(self.report_path)), 8)
        self.assertFalse(json.loads(out.read_text())["qualifies"])
        for argv in (("--single-host", "jetson", "--report", str(self.report_path), "--mac", str(self.report_path)),
                     ("--report", str(self.report_path))):
            with self.assertRaises(SystemExit):
                run(*argv)
        # 两宿主旧路径：`build_receipt_document` 与 `decide_host` 未改（缺一宿主即不出收据）。
        self.assertEqual(latency.build_receipt_document(None, None)["decision"], "MEASUREMENT_INCOMPLETE")


class JetsonMeasurementTests(JetsonFixture):
    """`measure --host jetson`：身份只取自 `/status`；逐请求状态含解析/约束失败，失败行不过滤。"""

    def rows(self) -> list[dict]:
        image = self.root / "frame.jpg"
        image.write_bytes(b"jpeg-bytes")
        return [{"row_id": f"r{i}", "image_path": image, "surface": "the red car", "g4": False} for i in range(32)]

    def test_identity_comes_from_status_and_failures_stay_in_the_report(self) -> None:
        outputs = [UNIQUE] * 3 + [SCHEMA_BREAK if i % 8 == 0 else UNIQUE for i in range(32)]
        service = FakeService(self.identity, self.serve_code, outputs=outputs)
        factory, served = latency.jetson_adapter_factory(ENDPOINT, t_ret_s=60.0, t_hard_s=60.0, opener=service)
        self.assertEqual(served["model_identity"], self.identity)
        report = latency.measure_host(factory, self.rows(), host=JETSON_HOST, backend="http", model_form="c2-merged",
                                      hz=5.0, retained_frame_count=128, classify=True)
        samples = report["rounds"][0]["samples"]
        self.assertEqual(len(samples), 32)
        self.assertEqual([s["status"] for s in samples].count("parse_failed"), 4)
        self.assertEqual({s["parse_error"] for s in samples if s["status"] == "parse_failed"}, {"SCHEMA_ERROR"})
        self.assertEqual(report["model_identity"], self.identity)
        fields = latency.jetson_report_fields(served, ENDPOINT, git_state=lambda: (HEAD, False))
        self.assertEqual((fields["transport"], fields["serve_code_sha256"], fields["machine"]),
                         ({"endpoint": ENDPOINT}, self.serve_code, MACHINE))
        self.assertEqual(fields["environment_git"], {"git_head": HEAD, "dirty": False})

    def test_status_without_six_keys_or_weights_is_a_load_failure(self) -> None:
        for identity in ({k: v for k, v in self.identity.items() if k not in bridge.LLAMA_IDENTITY_KEYS},
                         dict(self.identity, weights_sha256=None),
                         dict(self.identity, runtime_build="v1")):
            with self.subTest(identity=sorted(identity)), self.assertRaises(SelectorError):
                latency.jetson_adapter_factory(ENDPOINT, t_ret_s=60.0, t_hard_s=60.0,
                                               opener=FakeService(identity, self.serve_code))

    def test_measure_cli_takes_no_identity_arguments(self) -> None:
        """测量工具不接受用户传入的身份 sha（只从 `/status` 读）。"""
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            latency.main(["measure", "--host", "jetson", "--backend", "http", "--smoke", "x", "--package-root", "x",
                          "--model-form", "c2-merged", "--out", "x", "--weights-sha256", "a" * 64])


class JetsonSingleRoundStopTests(JetsonFixture):
    """AC-15 修订 1：jetson 生产入口只测一轮、首个测量失败即停本轮剩余调用；其他宿主仍可第二轮。"""

    def rows(self) -> list[dict]:
        image = self.root / "frame.jpg"
        image.write_bytes(b"jpeg-bytes")
        return [{"row_id": f"r{i}", "image_path": image, "surface": "the red car", "g4": False} for i in range(32)]

    def write_smoke(self) -> tuple[Path, Path]:
        package = self.root / "package"
        (package / "frames").mkdir(parents=True)
        (package / "frames" / "f.jpg").write_bytes(b"jpeg-bytes")
        smoke = self.root / "smoke.jsonl"
        smoke.write_text("".join(
            json.dumps({"row_id": f"r{i}", "frame_path": "frames/f.jpg", "surface": "the red car"}) + "\n"
            for i in range(32)
        ), encoding="utf-8")
        return smoke, package

    def run_cli(self, service: FakeService) -> tuple[int, dict]:
        smoke, package = self.write_smoke()
        out = self.root / "jetson-report.out.json"
        original = latency.jetson_adapter_factory
        builds: list[int] = []

        def counting_factory(*args, **kwargs):
            # 生产 `jetson_adapter_factory` 原样执行（身份探针在其中），只注入 opener 并数每次建适配器。
            factory, served = original(*args, **dict(kwargs, opener=service))

            def build():
                builds.append(1)
                return factory()

            return build, served

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), \
                patch.object(latency, "code_git_state", lambda root: (HEAD, False)), \
                patch.object(latency, "jetson_adapter_factory", counting_factory):
            code = latency.main([
                "measure", "--host", "jetson", "--backend", "http", "--model-form", "c2-merged",
                "--server-url", ENDPOINT, "--smoke", str(smoke), "--package-root", str(package),
                "--runtime", str(self.runtime), "--out", str(out),
            ])
        self.builds = len(builds)
        return code, json.loads(out.read_text(encoding="utf-8"))

    def test_success_is_exactly_three_warmups_plus_thirty_two_timed_requests(self) -> None:
        service = FakeService(self.identity, self.serve_code)
        code, report = self.run_cli(service)
        self.assertEqual(code, 0)
        self.assertEqual(report["verdict"], "OK")
        self.assertEqual(len(report["rounds"]), 1)
        self.assertEqual(self.builds, 1)
        self.assertEqual(service.count("POST", "/query"), 35)
        # 身份探针 1 + bind 1；每次推理恰一次长轮询 GET（替身即时 done）。
        self.assertEqual(service.count("GET", "/status"), 2)
        self.assertEqual(service.count("GET", "/result/"), 35)
        self.assertTrue(all("?wait_s=" in path for method, path in service.calls if path.startswith("/result/")))
        self.assertEqual(report["rounds"][0]["not_attempted"], 0)
        self.assertFalse(report["rounds"][0]["stopped_after_first_failure"])

    def test_first_round_failure_builds_no_second_adapter_and_sends_no_more_status(self) -> None:
        outputs = [UNIQUE] * 3 + [UNIQUE] * 9 + [FAILED_INFERENCE] + [UNIQUE] * 40
        service = FakeService(self.identity, self.serve_code, outputs=outputs)
        code, report = self.run_cli(service)
        self.assertEqual(code, latency.EXIT_MEASURE_NOT_OK)
        self.assertEqual(code, 7)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(len(report["rounds"]), 1, "no automatic second round")
        self.assertEqual(self.builds, 1, "no second adapter factory call")
        self.assertEqual(service.count("GET", "/status"), 2, "no second bind/status")
        self.assertEqual(service.count("POST", "/query"), 13, "stop right after the failed (13th) request")
        round_summary = report["rounds"][0]
        self.assertEqual(round_summary["verdict"], "INVALID")
        self.assertTrue(round_summary["stopped_after_first_failure"])
        self.assertEqual(round_summary["not_attempted"], 35 - 13)
        self.assertEqual(len(round_summary["samples"]), 10)  # 9 个成功计时 + 1 个失败计时行（保留）
        self.assertEqual([s["failed"] for s in round_summary["samples"]].count(True), 1)
        self.assertEqual(round_summary["failures"][0]["reason"], "worker_died")
        self.assertIsNone(round_summary["p95_ms"], "fewer than 32 timed samples never yields a p95")
        self.assertIsNone(report["p95_s"])

    def test_warmup_failure_stops_before_any_timed_request(self) -> None:
        service = FakeService(self.identity, self.serve_code, outputs=[UNIQUE, FAILED_INFERENCE] + [UNIQUE] * 40)
        code, report = self.run_cli(service)
        self.assertEqual(code, 7)
        self.assertEqual(service.count("POST", "/query"), 2)
        round_summary = report["rounds"][0]
        self.assertEqual(len(round_summary["warmup"]), 2)
        self.assertEqual(round_summary["samples"], [])
        self.assertEqual(round_summary["not_attempted"], 33)

    def test_identity_probe_failure_writes_a_failed_report_without_inference(self) -> None:
        service = FakeService(self.identity, self.serve_code)
        service.status_ok = False
        code, report = self.run_cli(service)
        self.assertEqual(code, 7)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertIn("load_failure", report["load_error"])
        self.assertEqual(service.count("POST", "/query"), 0)
        self.assertEqual(service.count("GET", "/result/"), 0)
        self.assertEqual(service.count("GET", "/status"), 1, "the probe is not retried")
        with self.assertRaises(latency.ReceiptRejected):
            self.generate(report)

    def test_envelope_failure_keeps_its_budget_reason(self) -> None:
        service = FakeService(self.identity, self.serve_code)
        factory, _served = latency.jetson_adapter_factory(ENDPOINT, t_ret_s=60.0, t_hard_s=60.0, opener=service)

        def factory_with_tight_budget():
            adapter = factory()
            adapter.http_budget = {"non_inference_used": 198, "non_inference_limit": 200, "reserve": 2,
                                   "inference_used": 0, "inference_limit": 335}
            return adapter

        report = latency.measure_host(factory_with_tight_budget, self.rows(), host=JETSON_HOST, backend="http",
                                      model_form="c2-merged", hz=5.0, retained_frame_count=128,
                                      max_rounds=latency.JETSON_MAX_ROUNDS, classify=True, stop_on_failure=True)
        failures = report["rounds"][0]["failures"]
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["reason"], "worker_stuck")
        self.assertTrue(failures[0]["detail"].startswith("S_ENVELOPE"), failures[0]["detail"])
        self.assertEqual(report["rounds"][0]["not_attempted"], 34)
        self.assertEqual(report["verdict"], "FAIL")

    def test_other_hosts_keep_the_default_second_round(self) -> None:
        attempts: list[int] = []

        class FlakyAdapter:
            identity = {"backend": "local-hf", "model_form": "c2-merged"}

            def __init__(self, round_number: int):
                self.round_number = round_number

            def predict_one(self, query_id, image_path, surface, g4):
                if self.round_number == 1 and query_id.endswith("timed-0"):
                    raise SelectorError("timeout", "first round flake")
                from controller.language_selector import RawSelection  # noqa: PLC0415
                return RawSelection(raw_output=UNIQUE, finish_reason="stop", gen_tokens=5, latency_ms=1.0,
                                    prompt_sha256="p", model_id="m")

        def factory():
            attempts.append(1)
            return FlakyAdapter(len(attempts))

        report = latency.measure_host(factory, self.rows(), host="mac", backend="local-hf", model_form="c2-merged",
                                      hz=5.0, retained_frame_count=128)
        self.assertEqual(len(attempts), 2)
        self.assertEqual([r["verdict"] for r in report["rounds"]], ["INVALID", "OK"])
        self.assertEqual(len(report["rounds"][0]["samples"]), 32, "old path keeps calling after a failure")
        self.assertNotIn("not_attempted", report["rounds"][0])


class JetsonSessionStartTests(JetsonFixture):
    """§3.2 会话启动校验：每一项各一个错配拒绝；拒绝都发生在建任何会话目录之前。"""

    def test_matching_binding_starts_and_records_it(self) -> None:
        session = self.session()
        session.start()
        journal = [json.loads(line) for line in session.journal_path.read_text().splitlines()]
        binding = journal[0]["jetson_binding"]
        self.assertEqual((binding["git_head"], binding["machine"], binding["serve_code_sha256"]),
                         (HEAD, MACHINE, self.serve_code))

    def test_missing_report_wrong_host_and_changed_bytes(self) -> None:
        receipt = self.receipt()
        self.report_path.unlink()
        self.assert_refused("invalid K measurement binding", receipt=receipt)
        self.write_report(dict(self.report, host="5060"))
        self.assert_refused("invalid K measurement binding", receipt=replace(
            receipt, source_reports={"jetson": {"path": str(self.report_path),
                                                "sha256": deploy_digest.sha256_path(self.report_path)}}))
        self.write_report()
        self.report_path.write_text(self.report_path.read_text() + "\n")
        self.assert_refused("SHA changed", receipt=receipt)

    def _receipt_for(self, report: dict) -> KReceipt:
        """绕过生成器、按报告字节手工组一份收据（只用于测会话侧拒绝）。"""
        self.write_report(report)
        document = build_k_receipt(hz=5.0, retained_frame_count=128, p95_s=2.0, host=JETSON_HOST, backend="http",
                                   model_form="c2-merged", model_identity=report["model_identity"],
                                   scenario_id="deterministic-loop-default").payload()
        document["source_reports"] = {"jetson": {"path": str(self.report_path),
                                                 "sha256": deploy_digest.sha256_path(self.report_path)}}
        return KReceipt.from_document(document)

    def test_transport_endpoint_and_live_identity(self) -> None:
        self.assert_refused("transport", receipt=self._receipt_for({k: v for k, v in self.report.items() if k != "transport"}))
        self.assert_refused("endpoint", receipt=self._receipt_for(self.report), endpoint="http://other:8762")
        for key, value in (("weights_sha256", "e" * 64), ("mmproj_sha256", "e" * 64), ("runtime_binary_sha256", "e" * 64),
                           ("runtime_build", "b1"), ("response_format_sha256", "e" * 64), ("decode_config_sha256", "e" * 64)):
            with self.subTest(key=key):
                receipt = self._receipt_for(self.report)
                live = FakeService(dict(self.identity, **{key: value}), self.serve_code)
                self.assert_refused("live HTTP identity", receipt=receipt, service=live)

    def test_scenario_id_hz_and_retained_frame_count(self) -> None:
        receipt = self._receipt_for(self.report)
        self.assert_refused("scenario_id", receipt=replace(receipt, scenario_id="deterministic-loop-untethered"))
        default = json.loads((PROJECT_ROOT / "config" / "scenario.default.json").read_text())
        default["sensor"]["retained_frame_count"] = 1500
        (self.runtime / "scenario_config.json").write_text(json.dumps(default))
        self.assert_refused("hz/R", receipt=receipt, before_dirs=False)
        default["sensor"]["retained_frame_count"] = 128
        default["sensor"]["capture_hz"] = 10.0
        (self.runtime / "scenario_config.json").write_text(json.dumps(default))
        self.assert_refused("hz/R", receipt=receipt, before_dirs=False)

    def test_git_head_dirty_machine_and_serve_code(self) -> None:
        receipt = self._receipt_for(self.report)
        self.assert_refused("git_head", receipt=receipt, head="f" * 40)
        self.assert_refused("dirty", receipt=receipt, dirty=True)
        self.assert_refused("machine", receipt=receipt,
                            service=FakeService(self.identity, self.serve_code, machine="other-board"))
        self.assert_refused("serve_code_sha256", receipt=receipt, service=FakeService(self.identity, "e" * 64))
        dirty_report = dict(self.report, environment={"git_head": HEAD, "dirty": True})
        self.assert_refused("dirty", receipt=self._receipt_for(dirty_report))
        # 本地工作树与报告/`/status` 不一致（板上部署正确与否只能靠板端自算摘要比较）。
        (self.code_root / "tools" / "language_serve.py").write_text("# changed\n")
        self.assert_refused("serve_code_sha256", receipt=self._receipt_for(self.report))

    def test_response_format_decode_and_prompt_must_match_local_recomputation(self) -> None:
        for key in ("response_format_sha256", "decode_config_sha256", "prompt_template_sha256"):
            with self.subTest(key=key):
                identity = dict(self.identity, **{key: "e" * 64})
                receipt = self._receipt_for(dict(self.report, model_identity=identity))
                self.assert_refused(key, receipt=receipt, service=FakeService(identity, self.serve_code))

    def test_six_key_shape_errors_are_refused(self) -> None:
        bad = {
            "partial": {k: v for k, v in self.identity.items() if k != "quantization"},
            "none": {k: v for k, v in self.identity.items() if k not in bridge.LLAMA_IDENTITY_KEYS},
            "hex64": dict(self.identity, runtime_binary_sha256="g" * 64),
            "runtime_build": dict(self.identity, runtime_build="b12345678"),
            "quantization": dict(self.identity, quantization="Q4_0"),
            "backend": dict(self.identity, backend="local-hf"),
            "model_form": dict(self.identity, model_form="c2-adapter"),
        }
        for name, identity in bad.items():
            with self.subTest(name=name):
                receipt = self._receipt_for(dict(self.report, model_identity=identity))
                self.assert_refused("", receipt=receipt, service=FakeService(identity, self.serve_code))

    def test_not_qualifying_receipt_is_refused(self) -> None:
        self.write_report(dict(self.report, p95_s=30.0))
        document = build_k_receipt(hz=5.0, retained_frame_count=128, p95_s=30.0, host=JETSON_HOST, backend="http",
                                   model_form="c2-merged", model_identity=self.identity,
                                   scenario_id="deterministic-loop-default").payload()
        document["source_reports"] = {"jetson": {"path": str(self.report_path),
                                                 "sha256": deploy_digest.sha256_path(self.report_path)}}
        self.assert_refused("qualify", receipt=KReceipt.from_document(document))


_GIT_ENV_KEYS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CEILING_DIRECTORIES", "GIT_COMMON_DIR", "GIT_PREFIX")


class CleanWorkingTreeProductionPathTests(JetsonFixture):
    """C1-AC6（IR-6 不接受缩窄）：§3.2/§3.6「干净工作树」= 整个工作树 `git status --porcelain` 为空。

    不注入 `git_state`：临时目录里建一个真实 git 仓库（部署闭集 + tests/ + docs/ + .gitignore），
    由生产路径 `code_git_state` 取值；tests/、文档的未提交改动与未跟踪文件都必须判脏，只有
    `.gitignore` 忽略的 `runtime/`、`outputs/` 不计。
    """

    def setUp(self) -> None:
        super().setUp()
        environment = patch.dict("os.environ")
        environment.start()
        self.addCleanup(environment.stop)
        import os  # noqa: PLC0415

        for key in _GIT_ENV_KEYS:
            os.environ.pop(key, None)
        repo = self.code_root
        (repo / "tests").mkdir(exist_ok=True)
        (repo / "tests" / "test_probe.py").write_text("# probe\n", encoding="utf-8")
        (repo / "docs").mkdir(exist_ok=True)
        (repo / "docs" / "note.md").write_text("note\n", encoding="utf-8")
        (repo / ".gitignore").write_text("runtime/\noutputs/\n", encoding="utf-8")
        self._git("init", "-q")
        self._git("add", "-A")
        self._git("commit", "-q", "--no-verify", "-m", "fixture")
        self.head = self._git("rev-parse", "HEAD").strip()
        self.report["environment"] = {"python": "3", "git_head": self.head, "dirty": False}
        self.write_report()

    def _git(self, *argv: str) -> str:
        import subprocess  # noqa: PLC0415

        return subprocess.run(
            ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
             "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *argv],
            cwd=self.code_root, capture_output=True, text=True, check=True,
        ).stdout

    def _dirty_cases(self):
        repo = self.code_root
        return (
            ("tests_modified", lambda: (repo / "tests" / "test_probe.py").write_text("# changed\n", encoding="utf-8")),
            ("docs_modified", lambda: (repo / "docs" / "note.md").write_text("changed\n", encoding="utf-8")),
            ("tests_untracked", lambda: (repo / "tests" / "test_new.py").write_text("# new\n", encoding="utf-8")),
            ("config_modified", lambda: (repo / "config" / "vlm-three-state.schema.json").write_text("{}\n", encoding="utf-8")),
        )

    def _restore(self) -> None:
        self._git("checkout", "-q", "--", ".")
        self._git("clean", "-q", "-f", "--", "tests", "docs", "config")

    def test_code_git_state_reads_the_whole_working_tree(self) -> None:
        from controller.language_loop import code_git_state  # noqa: PLC0415

        self.assertEqual(code_git_state(self.code_root), (self.head, False))
        for name, change in self._dirty_cases():
            with self.subTest(case=name):
                change()
                self.assertEqual(code_git_state(self.code_root), (self.head, True))
                self._restore()
                self.assertEqual(code_git_state(self.code_root), (self.head, False))
        (self.code_root / "runtime").mkdir()
        (self.code_root / "runtime" / "scenario_config.json").write_text("{}", encoding="utf-8")
        (self.code_root / "outputs").mkdir()
        (self.code_root / "outputs" / "log.txt").write_text("x", encoding="utf-8")
        self.assertEqual(code_git_state(self.code_root), (self.head, False), "ignored runtime/ outputs/ do not count")

    def test_receipt_generator_and_measure_refuse_uncommitted_tests_or_docs(self) -> None:
        document = latency.build_single_host_receipt(
            self.report, self.report_path, scenario=self.scenario(), code_root=self.code_root
        )
        self.assertEqual(document["host"], JETSON_HOST)
        served = {"serve_code_sha256": self.serve_code, "machine": MACHINE}
        self.assertEqual(latency.jetson_report_fields(served, ENDPOINT, code_root=self.code_root)["environment_git"],
                         {"git_head": self.head, "dirty": False})
        for name, change in self._dirty_cases()[:3]:
            with self.subTest(case=name):
                change()
                with self.assertRaisesRegex(latency.ReceiptRejected, "dirty"):
                    latency.build_single_host_receipt(
                        self.report, self.report_path, scenario=self.scenario(), code_root=self.code_root
                    )
                fields = latency.jetson_report_fields(served, ENDPOINT, code_root=self.code_root)
                self.assertEqual(fields["environment_git"], {"git_head": self.head, "dirty": True})
                self._restore()

    def test_session_start_refuses_uncommitted_tests_or_docs(self) -> None:
        receipt = KReceipt.from_document(latency.build_single_host_receipt(
            self.report, self.report_path, scenario=self.scenario(), code_root=self.code_root
        ))

        def production_session() -> LanguageSession:
            service = FakeService(dict(receipt.model_identity), self.serve_code)
            adapter = HttpAdapter(ENDPOINT, t_ret_s=receipt.t_ret_s, t_hard_s=60.0, opener=service,
                                  model_form="c2-merged")
            adapter.identity = dict(receipt.model_identity)
            session = LanguageSession(SessionConfig(
                session_id="jet1", session_root=self.root / "sessions", runtime=self.runtime, receipt=receipt,
                adapter=adapter, code_root=self.code_root, git_state=None, pid=4242, is_alive=lambda pid: True,
            ))
            self.addCleanup(session.close)
            return session

        for name, change in self._dirty_cases()[:3]:
            with self.subTest(case=name):
                change()
                with self.assertRaisesRegex(ConfigMismatch, "dirty"):
                    production_session()
                self.assertFalse((self.root / "sessions").exists())
                self._restore()
        production_session().start()


class ModelBlockCompatibilityTests(unittest.TestCase):
    """A2(d)：六键全无的旧 HF/candidates/replay 结果照常通过；新结果六键逐键校验。"""

    def _result(self, model: dict) -> dict:
        return bridge.result_payload(
            query_id="q1", result_id="r1", request_id=None, epoch=1, segment_index=None, attempt=1,
            attempt_limit=3, purpose="designate", status="none", frame_id=None, frame_sha256=None,
            capture_monotonic_s=None, capture_unix_s=None, query_unix_s=1.0, model=model,
        )

    def test_legacy_blocks_pass_byte_shape_unchanged_and_new_keys_validate(self) -> None:
        for model in ({"backend": "local-hf", "model_form": "c2-merged", "weights_sha256": "w"},
                      {"backend": "candidates", "model_form": "detector-tracks"},
                      {"backend": "replay", "model_form": "c2-adapter", "weights_sha256": "scripted"}):
            block = self._result(model)["result"]["model"]
            self.assertFalse(set(block) & set(bridge.LLAMA_IDENTITY_KEYS))
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        identity = llama_identity(copy_deploy_root(root))
        block = self._result(identity)["result"]["model"]
        self.assertEqual({k: block[k] for k in bridge.LLAMA_IDENTITY_KEYS}, {k: identity[k] for k in bridge.LLAMA_IDENTITY_KEYS})
        with self.assertRaises(bridge.LanguageBridgeError):
            self._result(dict(identity, quantization="Q5_K_M"))
        with self.assertRaises(bridge.LanguageBridgeError):
            self._result({k: v for k, v in identity.items() if k != "decode_config_sha256"})


if __name__ == "__main__":
    unittest.main()
