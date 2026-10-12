"""Fail-closed coverage for the re-anchor environment preflight.

Acceptance round 21 §B.3/§B.4/§B.5. The heavy real models are never built here;
the production constructors are injected so each failure mode is isolated. The
real end-to-end PASS is recorded in the implementation evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import preflight_reanchor_env as preflight
from tools.preflight_reanchor_env import PreflightError, run_preflight


REANCHOR_CONFIG = PROJECT_ROOT / "config" / "detector-reanchor.models.json"
TOOL = PROJECT_ROOT / "tools" / "preflight_reanchor_env.py"

PINS = {
    "torch_pin": "2.13.0",
    "torchvision_pin": "0.28.0",
    "ultralytics_pin": "8.4.104",
    "device": "cpu",
}
OPENCV_TESTED = "5.0.0"

RAW_VERSIONS = {
    "cv2": OPENCV_TESTED,
    "torch": "2.13.0",
    "torchvision": "0.28.0",
    "ultralytics": "8.4.104",
}


class _FakeConfig:
    def __init__(self, runtime: dict[str, str] | None = None):
        self.raw = {
            "schema_version": "tethered-detector-reanchor/v1",
            "carrier": "minimal-triple-gated-re-anchor",
            "runtime": dict(runtime or PINS),
        }
        self.sha256 = "a" * 64
        self.tracker_factory = {
            "name": "nanotrack-v2",
            "spec": "config/nanotrack-v2.models.json",
            "model_dir": "runtime/models/nanotrack-v2",
        }


class _FakeNanoTrack:
    def __init__(self, identity: dict | None = None):
        self._identity = identity or {
            "name": "nanotrack-v2",
            "backend": "opencv-dnn-default/cpu",
            "opencv_version": OPENCV_TESTED,
            "opencv_package_pin": "opencv-contrib-python==5.0.0.93",
            "preprocessing_id": "opencv-tracker-nano-5.0.0-default-v1",
            "model_sha256": {"backbone": "b" * 64, "neckhead": "c" * 64},
        }

    def manifest_identity(self):
        return self._identity


class _FakeProposer:
    pass


class _FakeEmbedder:
    pass


def _importer(versions: dict[str, str], missing: set[str] | None = None):
    missing = missing or set()

    def importer(name: str):
        if name in missing:
            raise ImportError(f"No module named {name!r}")
        module = types.ModuleType(name)
        if versions.get(name) is not None:
            module.__version__ = versions[name]
        return module

    return importer


def _run(tmp_root: Path, **overrides):
    kwargs = dict(
        project_root=tmp_root,
        importer=_importer(RAW_VERSIONS),
        config_loader=lambda path: _FakeConfig(),
        spec_loader=lambda path: {"opencv": {"tested_version": OPENCV_TESTED}},
        nanotrack_factory=lambda spec, model_dir: _FakeNanoTrack(),
        yoloe_factory=lambda config: _FakeProposer(),
        dinov2_factory=lambda config: _FakeEmbedder(),
    )
    kwargs.update(overrides)
    return run_preflight(REANCHOR_CONFIG, **kwargs)


class PassReportTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def test_pass_report_carries_every_required_field(self):
        report = _run(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["interpreter"]["executable"], sys.executable)
        self.assertEqual(
            report["interpreter"]["prefix"], str(Path(sys.prefix).resolve())
        )
        self.assertEqual(
            set(report["packages"]), {"cv2", "torch", "torchvision", "ultralytics"}
        )
        self.assertEqual(report["reanchor_config"]["sha256"], "a" * 64)
        self.assertEqual(
            set(report["nanotrack"]["model_sha256"]), {"backbone", "neckhead"}
        )
        self.assertTrue(report["constructors"]["yoloe_proposer"].endswith("_FakeProposer"))
        self.assertTrue(report["constructors"]["dinov2_embedder"].endswith("_FakeEmbedder"))

    def test_report_states_only_the_checks_actually_performed(self):
        report = _run(self.root)
        identity = report["side_effect_identity"]
        self.assertTrue(identity["unchanged"])
        checked = identity["checked"]
        self.assertIn("runtime/runs direct child directory names", checked)
        for relative in preflight.GUARDED_FILES:
            self.assertIn(f"{relative} present/size/sha256", checked)
        # metrics.json must be one of the guarded files (round 21 §B.4).
        self.assertIn("runtime/metrics.json", preflight.GUARDED_FILES)
        # No unmeasured claim is smuggled into the report.
        blob = json.dumps(report)
        for forbidden in ("network", "inference", "frames_read"):
            self.assertNotIn(forbidden, blob)

    def test_packages_record_raw_string_and_pin_only(self):
        report = _run(self.root)
        for package, entry in report["packages"].items():
            self.assertEqual(set(entry), {"raw", "pin", "pin_source"})
            self.assertEqual(entry["raw"], entry["pin"], package)


class RawVersionLiteralityTest(unittest.TestCase):
    """Round 21 §B.3: raw `__version__` must equal the pin verbatim."""

    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def test_local_build_suffix_fails_closed(self):
        for package, suffixed in (
            ("torch", "2.13.0+cpu"),
            ("torchvision", "0.28.0+cpu"),
            ("ultralytics", "8.4.104+dirty"),
            ("cv2", "5.0.0+local"),
        ):
            with self.subTest(package=package):
                versions = dict(RAW_VERSIONS)
                versions[package] = suffixed
                with self.assertRaises(PreflightError) as caught:
                    _run(self.root, importer=_importer(versions))
                message = str(caught.exception)
                self.assertIn(package, message)
                self.assertIn("verbatim", message)
                self.assertIn(suffixed, message)

    def test_plain_pin_mismatch_fails_closed(self):
        for package, wrong in (
            ("torch", "2.12.0"),
            ("torchvision", "0.27.0"),
            ("ultralytics", "8.4.103"),
            ("cv2", "4.11.0"),
        ):
            with self.subTest(package=package):
                versions = dict(RAW_VERSIONS)
                versions[package] = wrong
                with self.assertRaises(PreflightError):
                    _run(self.root, importer=_importer(versions))

    def test_missing_package_fails_closed(self):
        for missing in ("cv2", "torch", "torchvision", "ultralytics"):
            with self.subTest(missing=missing):
                with self.assertRaises(PreflightError) as caught:
                    _run(self.root, importer=_importer(RAW_VERSIONS, missing={missing}))
                self.assertIn(missing, str(caught.exception))

    def test_missing_dunder_version_fails_closed(self):
        versions = dict(RAW_VERSIONS)
        versions["ultralytics"] = None
        with self.assertRaises(PreflightError) as caught:
            _run(self.root, importer=_importer(versions))
        self.assertIn("__version__", str(caught.exception))

    def test_cv2_pin_comes_from_the_spec_tested_version(self):
        report = _run(self.root)
        self.assertEqual(
            report["packages"]["cv2"]["pin_source"],
            "nanotrack spec opencv.tested_version",
        )
        self.assertEqual(report["packages"]["cv2"]["pin"], OPENCV_TESTED)


class SideEffectIdentityTest(unittest.TestCase):
    """Round 21 §B.4: names, present/absent, size and SHA-256 must all hold."""

    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (self.root / "runtime").mkdir()

    def test_existing_publication_rewritten_in_place_fails_closed(self):
        target = self.root / "runtime" / "body_command.json"
        target.write_text('{"mode": "hold"}')

        def rewriting(config):
            # Same file, still present, different bytes.
            target.write_text('{"mode": "velocity_world"}')
            return _FakeEmbedder()

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, dinov2_factory=rewriting)
        message = str(caught.exception)
        self.assertIn("runtime/body_command.json", message)
        self.assertIn("changed bytes", message)

    def test_same_size_different_bytes_fails_closed(self):
        target = self.root / "runtime" / "tracking_observation.json"
        target.write_text("AAAA")

        def rewriting(config):
            target.write_text("BBBB")  # identical size, different content
            return _FakeEmbedder()

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, dinov2_factory=rewriting)
        self.assertIn("changed bytes", str(caught.exception))

    def test_metrics_creation_fails_closed(self):
        def creating(config):
            (self.root / "runtime" / "metrics.json").write_text("{}")
            return _FakeEmbedder()

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, dinov2_factory=creating)
        message = str(caught.exception)
        self.assertIn("runtime/metrics.json", message)
        self.assertIn("was created", message)

    def test_metrics_rewrite_fails_closed(self):
        metrics = self.root / "runtime" / "metrics.json"
        metrics.write_text('{"c_geom": false}')

        def rewriting(config):
            metrics.write_text('{"c_geom": true}')
            return _FakeEmbedder()

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, dinov2_factory=rewriting)
        self.assertIn("runtime/metrics.json", str(caught.exception))
        self.assertIn("changed bytes", str(caught.exception))

    def test_publication_deletion_fails_closed(self):
        target = self.root / "runtime" / "gimbal_command.json"
        target.write_text("{}")

        def deleting(config):
            target.unlink()
            return _FakeEmbedder()

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, dinov2_factory=deleting)
        self.assertIn("was deleted", str(caught.exception))

    def test_created_run_directory_fails_closed(self):
        (self.root / "runtime" / "runs").mkdir()

        def leaky(config):
            (self.root / "runtime" / "runs" / "p1-m3-body-001-arm-a-trial-1").mkdir()
            return _FakeEmbedder()

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, dinov2_factory=leaky)
        self.assertIn("run directories created", str(caught.exception))

    def test_untouched_runtime_passes(self):
        (self.root / "runtime" / "runs").mkdir()
        (self.root / "runtime" / "runs" / "existing-run").mkdir()
        (self.root / "runtime" / "metrics.json").write_text('{"kept": true}')
        report = _run(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(
            report["side_effect_identity"]["before"],
            report["side_effect_identity"]["after"],
        )

    def test_fingerprint_records_size_and_sha256(self):
        metrics = self.root / "runtime" / "metrics.json"
        metrics.write_text("hello")
        fingerprint = preflight.side_effect_fingerprint(self.root)
        entry = fingerprint["guarded_files"]["runtime/metrics.json"]
        self.assertTrue(entry["present"])
        self.assertEqual(entry["size_bytes"], 5)
        self.assertEqual(len(entry["sha256"]), 64)


class FailurePathIdentityTest(unittest.TestCase):
    """Round 22 §C: a factory that writes and *then* raises must still report
    the side-effect delta. The construction error is retained as secondary
    context; it never replaces or downgrades the delta, and nothing is deleted
    or written back to hide the polluted site.
    """

    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (self.root / "runtime").mkdir()

    def test_metrics_rewritten_then_raise_names_both(self):
        metrics = self.root / "runtime" / "metrics.json"
        metrics.write_text("before")

        def write_then_raise(config):
            metrics.write_text("after!")
            raise RuntimeError("DINOv2 weights verification failed")

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, dinov2_factory=write_then_raise)
        message = str(caught.exception)
        self.assertIn("runtime/metrics.json", message)
        self.assertIn("changed bytes", message)
        # the original failure survives as secondary context
        self.assertIn("secondary context", message)
        self.assertIn("DinoV2Embedder construction failed", message)
        self.assertIn("DINOv2 weights verification failed", message)
        # the site is left exactly as the factory left it
        self.assertEqual(metrics.read_text(), "after!")

    def test_run_directory_created_then_raise_names_both(self):
        runs = self.root / "runtime" / "runs"
        runs.mkdir()

        def write_then_raise(config):
            (runs / "p1-m3-body-001-arm-a-trial-1").mkdir()
            raise RuntimeError("YOLOE weights verification failed")

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, yoloe_factory=write_then_raise)
        message = str(caught.exception)
        self.assertIn("run directories created", message)
        self.assertIn("p1-m3-body-001-arm-a-trial-1", message)
        self.assertIn("secondary context", message)
        self.assertIn("YoloeProposer construction failed", message)
        self.assertIn("YOLOE weights verification failed", message)
        # the leaked directory is preserved, not cleaned up behind the operator
        self.assertTrue((runs / "p1-m3-body-001-arm-a-trial-1").is_dir())

    def test_clean_failure_reports_only_the_construction_error(self):
        """No pollution -> the delta clause must not appear at all."""
        def factory(config):
            raise RuntimeError("plain failure")

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, dinov2_factory=factory)
        message = str(caught.exception)
        self.assertIn("DinoV2Embedder construction failed", message)
        self.assertNotIn("changed protected runtime state", message)
        self.assertNotIn("secondary context", message)

    def test_after_fingerprint_runs_exactly_once_on_both_paths(self):
        """Mechanical proof the comparison happens, rather than being implied
        by a nonzero exit code."""
        original = preflight.side_effect_fingerprint
        calls: list[str] = []

        def counting(project_root):
            calls.append("call")
            return original(project_root)

        preflight.side_effect_fingerprint = counting
        try:
            calls.clear()
            _run(self.root)
            self.assertEqual(len(calls), 2, "success path: before + after")

            calls.clear()
            def factory(config):
                raise RuntimeError("boom")

            with self.assertRaises(PreflightError):
                _run(self.root, dinov2_factory=factory)
            self.assertEqual(len(calls), 2, "failure path: before + after")
        finally:
            preflight.side_effect_fingerprint = original

    def test_loader_that_pollutes_then_raises_is_reported(self):
        """The guard covers loaders, not just the model factories."""
        target = self.root / "runtime" / "body_command.json"
        target.write_text("{}")

        def loader(path):
            target.write_text('{"mode": "velocity_world"}')
            raise ValueError("unsupported reanchor config")

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, config_loader=loader)
        message = str(caught.exception)
        self.assertIn("runtime/body_command.json", message)
        self.assertIn("changed bytes", message)
        self.assertIn("secondary context", message)


class ConstructionFailureTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def test_bad_config_schema_fails_closed(self):
        def loader(path):
            raise ValueError("unsupported reanchor config 'bogus/v9'")

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, config_loader=loader)
        self.assertIn("failed strict parsing", str(caught.exception))

    def test_bad_spec_fails_closed(self):
        def loader(path):
            raise ValueError("model spec.models.backbone.sha256 must be lowercase")

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, spec_loader=loader)
        self.assertIn("NanoTrack spec", str(caught.exception))

    def test_absent_config_path_fails_closed(self):
        with self.assertRaises(PreflightError) as caught:
            run_preflight(self.root / "nope.json", project_root=self.root)
        self.assertIn("does not exist", str(caught.exception))

    def test_model_hash_failure_fails_closed(self):
        def factory(spec, model_dir):
            raise RuntimeError("NanoTrack-v2 backbone SHA-256 mismatch")

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, nanotrack_factory=factory)
        self.assertIn("SHA-256 mismatch", str(caught.exception))

    def test_identity_mismatch_fails_closed(self):
        identity = {"name": "csrt", "model_sha256": {"backbone": "b" * 64, "neckhead": "c" * 64}}
        with self.assertRaises(PreflightError) as caught:
            _run(self.root, nanotrack_factory=lambda s, m: _FakeNanoTrack(identity))
        self.assertIn("does not match", str(caught.exception))

    def test_partial_model_hashes_fail_closed(self):
        identity = {"name": "nanotrack-v2", "model_sha256": {"backbone": "b" * 64}}
        with self.assertRaises(PreflightError) as caught:
            _run(self.root, nanotrack_factory=lambda s, m: _FakeNanoTrack(identity))
        self.assertIn("both backbone and neckhead", str(caught.exception))

    def test_yoloe_construction_failure_fails_closed(self):
        def factory(config):
            raise ModuleNotFoundError("No module named 'ultralytics'")

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, yoloe_factory=factory)
        self.assertIn("YoloeProposer construction failed", str(caught.exception))

    def test_dinov2_construction_failure_fails_closed(self):
        def factory(config):
            raise ValueError("DINOv2 extracted source file set mismatch")

        with self.assertRaises(PreflightError) as caught:
            _run(self.root, dinov2_factory=factory)
        self.assertIn("DinoV2Embedder construction failed", str(caught.exception))

    def test_import_success_alone_is_not_a_pass(self):
        def factory(config):
            raise RuntimeError("YOLOE weights verification failed")

        with self.assertRaises(PreflightError):
            _run(self.root, importer=_importer(RAW_VERSIONS), yoloe_factory=factory)


class SubprocessContractTest(unittest.TestCase):
    """Round 21 §B.5: real subprocess locks the stdout/CLI contract."""

    def _run_tool(self, argv: list[str], executable: str = sys.executable):
        return subprocess.run(
            [executable, str(TOOL), *argv],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

    def test_reanchor_config_argument_is_required(self):
        result = self._run_tool([])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--reanchor-config", result.stderr)

    def test_unknown_argument_is_rejected(self):
        result = self._run_tool(
            ["--reanchor-config", str(REANCHOR_CONFIG), "--verbose"]
        )
        self.assertNotEqual(result.returncode, 0)

    def test_failure_leaves_stdout_empty_and_exits_nonzero(self):
        """This interpreter lacks the re-anchor stack, so it must fail closed."""
        result = self._run_tool(["--reanchor-config", str(REANCHOR_CONFIG)])
        if result.returncode == 0:
            self.skipTest("interpreter satisfies the re-anchor stack; see evidence")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        payload = json.loads(result.stderr[result.stderr.index("{"):])
        self.assertEqual(payload["status"], "FAIL")
        self.assertTrue(payload["reason"])

    def test_absent_config_reports_json_on_stderr_only(self):
        result = self._run_tool(["--reanchor-config", "config/does-not-exist.json"])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        payload = json.loads(result.stderr[result.stderr.index("{"):])
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("does not exist", payload["reason"])

    def test_successful_stdout_is_exactly_one_json_document(self):
        """When the stack is satisfiable, stdout must parse with json.loads alone."""
        result = self._run_tool(["--reanchor-config", str(REANCHOR_CONFIG)])
        if result.returncode != 0:
            self.skipTest("interpreter lacks the re-anchor stack; see evidence")
        payload = json.loads(result.stdout)  # no slicing, no filtering
        self.assertEqual(payload["status"], "PASS")

    def test_success_path_stdout_purity_in_any_interpreter(self):
        """Deterministic PASS-path contract: a constructor that prints to stdout
        must not corrupt the report, in a real subprocess, without the heavy
        models. This locks §B.5 even where the re-anchor stack is unavailable.
        """
        harness = f'''
import sys
sys.path.insert(0, {str(PROJECT_ROOT)!r})
from tools import preflight_reanchor_env as p


class Cfg:
    raw = {{
        "schema_version": "tethered-detector-reanchor/v1",
        "carrier": "minimal-triple-gated-re-anchor",
        "runtime": {json.dumps(PINS)},
    }}
    sha256 = "a" * 64
    tracker_factory = {{
        "name": "nanotrack-v2",
        "spec": "config/nanotrack-v2.models.json",
        "model_dir": "runtime/models/nanotrack-v2",
    }}


class Nano:
    def manifest_identity(self):
        return {{
            "name": "nanotrack-v2",
            "model_sha256": {{"backbone": "b" * 64, "neckhead": "c" * 64}},
        }}


class Proposer:
    pass


class Embedder:
    pass


def importer(name):
    import types
    module = types.ModuleType(name)
    module.__version__ = {json.dumps(RAW_VERSIONS)}[name]
    return module


def noisy_yoloe(config):
    print("Could not import `tifffile`, TIFFImageDataDecoder will be disabled")
    return Proposer()


def noisy_dinov2(config):
    print("xFormers is not available (Attention)")
    return Embedder()


p._import_module = importer
p._default_config_loader = lambda path: Cfg()
p._default_spec_loader = lambda path: {{"opencv": {{"tested_version": {OPENCV_TESTED!r}}}}}
p._default_nanotrack_factory = lambda spec, model_dir: Nano()
p._default_yoloe_factory = noisy_yoloe
p._default_dinov2_factory = noisy_dinov2

sys.exit(p.main(["--reanchor-config", {str(REANCHOR_CONFIG)!r}]))
'''
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
            handle.write(harness)
            harness_path = handle.name
        try:
            result = subprocess.run(
                [sys.executable, harness_path],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
            )
        finally:
            Path(harness_path).unlink()
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)  # must parse with no slicing
        self.assertEqual(payload["status"], "PASS")
        # The chatter is not lost — it is on stderr where it belongs.
        self.assertIn("tifffile", result.stderr)
        self.assertIn("xFormers", result.stderr)


if __name__ == "__main__":
    unittest.main()
