#!/usr/bin/env python3
"""P1-ENG-SFT-002 K3 云端运行器、代码束与回传校验的无 GPU 具名回归（AC-7/8/11/12/13）。

夹具全部由生产路径产出：`tests/fixtures/eng_sft/synth.py` 的合成小世界跑 K4 的
build → plan → 代录 → precheck → 提交 → freeze → package，再跑 K3 的 `bundle`；
云端作业用真实的编排（`run_job_a` / `run_job_b`、启动账、预算守卫、作业收据），
只把模型调用换成 `FakeEngine`（继承 `TorchEngine`，只替换加载权重/推理/训练的方法）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.fixtures.eng_sft import synth  # noqa: E402
from tools.eng_sft import build_sft_data as build  # noqa: E402
from tools.eng_sft import cloud_runner, evaluate, label_audit, prompt_v2, receipts, train_lora  # noqa: E402
from tools.eng_sft import verify_return  # noqa: E402

BASE_ID = f"{train_lora.BASE_REPO}@{train_lora.BASE_REVISION}"
RAW = {
    "none": '{"status": "none"}',
    "unique": '{"status": "unique", "bbox_2d": [100, 100, 300, 300]}',
    "ambiguous": '{"status": "ambiguous", "candidates": [{"bbox_2d": [100, 100, 300, 300]}, '
                 '{"bbox_2d": [500, 500, 700, 700]}]}',
}
NOW = datetime(2026, 9, 20, 8, 0, 0, tzinfo=timezone.utc)
REAL_CHECK_PINS = cloud_runner.check_pins
RATES = {"gpu_usd_per_hour": 0.55, "storage_usd_per_hour": 0.02,
         "inbound_usd_per_tb": 2.0, "outbound_usd_per_tb": 2.0}


def no_drift(pins):
    """本机没有 GPU 栈：测试把「已装版本」当成等于钉版本；漂移拒绝另有专测（不经任何绕过开关）。"""
    return {"pinned": dict(pins), "installed": dict(pins), "drift": []}


def copy_bundle_sources(root: Path) -> None:
    """把 K3 代码束的源文件复制进夹具仓库（与仓库字节相同，随后提交）。"""
    for _, source in cloud_runner.BUNDLE_MEMBERS:
        if source is None:
            continue
        destination = Path(root) / source
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT_ROOT / source, destination)


def sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class FakeEngine(cloud_runner.TorchEngine):
    """只替换模型相关方法；文件型方法（base/tokenizer 文件定位与 SHA）用生产实现。"""

    def __init__(self, case: "K3Case", *, smoke_loss: float = 0.01, fail_once: tuple[str, ...] = (),
                 gpu_name: str = "NVIDIA GeForce RTX 5090", tokenizer_tamper: bool = False) -> None:
        super().__init__(micro_batch=8, device="cpu")
        self.case = case
        self.smoke_loss = smoke_loss
        self.fail_once = set(fail_once)
        self.gpu_name = gpu_name
        self.tokenizer_tamper = tokenizer_tamper
        self.missing: list[str] = []
        self.trained: list[str] = []
        self.predicted: list[tuple[str, int]] = []
        self.gold = {row["sample_id"]: row["state"] for row in case.read_local("smoke.jsonl")}
        self.gold.update({row["sample_id"]: row["state"] for row in case.read_local("select-eval.jsonl")})

    def environment(self) -> dict:
        return {"cuda_available": True, "gpu_count": 1, "gpu_name": self.gpu_name, "torch": "fake"}

    def ensure_base(self, work: Path, ledger: cloud_runner.StageLedger) -> cloud_runner.ModelSource:
        base = Path(work) / cloud_runner.BASE_DIRNAME
        if not (base / cloud_runner.BASE_COMPLETE_MARKER).is_file():
            base.mkdir(parents=True, exist_ok=True)
            for name in cloud_runner.TOKENIZER_FILES:
                shutil.copy2(self.case.tokenizer_dir / name, base / name)
            if self.tokenizer_tamper:
                (base / "vocab.json").write_text('{"other": 1}', encoding="utf-8")
            (base / "model.safetensors").write_bytes(b"fake-weights")
            (base / cloud_runner.BASE_COMPLETE_MARKER).write_text("fake\n", encoding="utf-8")
            ledger.document["base_download"] = {"completed_utc": receipts.utc_stamp()}
            ledger.save()
        return cloud_runner.ModelSource(str(base), None)

    def encoder(self, tokenizer_json: Path):
        return self.case.encode, {"library": "stub", "version": "0"}

    def check_grids(self, source, package_root, frame_paths, should_stop=None):
        for frame_path in frame_paths:
            if should_stop is not None and should_stop():
                raise train_lora.BudgetStop("fake grid stop")
            assert (Path(package_root) / frame_path).is_file(), frame_path
        return {"unity": {"expected": [1, 30, 40], "checked": len(frame_paths), "mismatches": 0}}

    def missing_modules(self) -> list[str]:
        return list(self.missing)

    def locate_model(self, source):
        return {"location": source.location, "kind": "fake"}

    def _status(self, row: dict, adapter: str | None) -> str:
        if adapter is not None and row["row_id"] in self.gold:
            if "C2" in adapter or "smoke" in adapter:
                return self.gold[row["row_id"]]  # C2 与冒烟：状态全对
        digest = int(hashlib.sha256(f"{adapter}|{row['row_id']}".encode()).hexdigest(), 16)
        return ("unique", "ambiguous", "none")[digest % 3]

    def predict(self, source, rows, package_root, out_path, *, adapter_dir=None, should_stop=None):
        model_id = BASE_ID if adapter_dir is None else receipts.sha256_file(
            Path(adapter_dir) / "adapter_model.safetensors")
        adapter = None if adapter_dir is None else Path(adapter_dir).parent.name

        def generate():
            for row in rows:
                if should_stop is not None and should_stop():
                    raise train_lora.BudgetStop("fake budget stop")
                prompt = prompt_v2.build_prompt(row["frame_path"], row["surface"], bool(row["g4"]), row["vocab"])
                yield train_lora.prediction_record(
                    row_id=row["row_id"], model_id=model_id, prompt_sha256=prompt["prompt_sha256"],
                    image_grid_thw=[1, 30, 40], raw_output=RAW[self._status(row, adapter)],
                    finish_reason="stop", gen_tokens=12, latency_ms=1.0)

        written = train_lora.write_jsonl_atomic(out_path, generate())
        self.predicted.append((str(out_path), written))
        return {"rows": written, "prediction_sha256": receipts.sha256_file(out_path), "model_id": model_id}

    def train(self, source, samples, package_root, out_dir, *, lr, epochs, expand, max_steps,
              predict_rows, predict_out, should_stop=None, micro_batch=None):
        label = Path(out_dir).name
        if label in self.fail_once:
            self.fail_once.discard(label)
            raise RuntimeError(f"simulated crash in {label}")
        indices = train_lora.expand_multiset(samples) if expand else list(range(len(samples)))
        plan = train_lora.plan_batches(indices, epochs)
        if max_steps is not None:
            plan = plan[:max_steps]
        out_dir = Path(out_dir)
        (out_dir / "adapter").mkdir(parents=True, exist_ok=True)
        (out_dir / "train-log.jsonl").write_text(json.dumps({"steps": len(plan)}) + "\n", encoding="utf-8")
        weights = out_dir / "adapter" / "adapter_model.safetensors"
        weights.write_bytes(f"fake-{label}-{lr}-{epochs}".encode())
        (out_dir / "adapter" / "adapter_config.json").write_text("{}", encoding="utf-8")
        self.trained.append(label)
        result = {
            "steps": len(plan), "warmup_steps": train_lora.warmup_steps(len(plan)), "epochs": epochs,
            "lr": lr, "multiset_rows": len(indices),
            "last_loss": self.smoke_loss if label == "smoke" else 0.2,
            "elapsed_s": 0.1, "peak_gpu_memory_bytes": None,
            "adapter_sha256": receipts.sha256_file(weights), "adapter_bytes": weights.stat().st_size,
            "train_log_sha256": receipts.sha256_file(out_dir / "train-log.jsonl"),
            "lora": {"lora_modules": 196, "expected": 196, "visual_lora_modules": 0},
        }
        result["predictions"] = self.predict(source, predict_rows, package_root, predict_out,
                                             adapter_dir=out_dir / "adapter", should_stop=should_stop)
        return result


class K3Case(unittest.TestCase):
    """K4 全链 + K3 `bundle`；`cloud()` 模拟把 `upload/` 传上云端。"""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="eng-sft-k3-"))
        self.cloud_root = Path(tempfile.mkdtemp(prefix="eng-sft-cloud-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.cloud_root, ignore_errors=True)
        self.world = synth.build_world(self.root)
        self.local = synth.local_root(self.root)
        synth.run_build(self.world)
        plan = label_audit.run_plan(repo_root=self.root, local_root=self.local)
        synth.write_unity_verdicts(self.root, plan)
        synth.copy_frozen_scripts(self.root)
        self.tokenizer_dir, self.encode = synth.stub_tokenizer(self.root)
        original = build._load_tokenizer
        build._load_tokenizer = lambda path: (self.encode, {"library": "stub", "version": "0"})
        try:
            build.run_precheck(repo_root=self.root, local_root=self.local, tokenizer_path=self.tokenizer_dir)
        finally:
            build._load_tokenizer = original
        copy_bundle_sources(self.root)
        synth.git_commit_all(self.root)
        build.run_freeze(repo_root=self.root, local_root=self.local)
        build.run_package(repo_root=self.root, local_root=self.local)
        self.upload = self.local / build.UPLOAD_DIRNAME
        pins = mock.patch.object(cloud_runner, "check_pins", no_drift)
        pins.start()
        self.addCleanup(pins.stop)

    def read_local(self, name: str) -> list[dict]:
        return train_lora.read_jsonl(self.local / build.DATA_DIRNAME / name)

    def bundle(self) -> dict:
        return cloud_runner.run_bundle(repo_root=self.root, local_root=self.local)

    def cloud(self) -> tuple[Path, Path]:
        package = self.cloud_root / "package"
        if package.exists():
            shutil.rmtree(package)
        shutil.copytree(self.upload, package)
        work = self.cloud_root / "work"
        work.mkdir(exist_ok=True)
        if not (work / cloud_runner.BUDGET_NAME).exists():
            cloud_runner.init_budget(work, minutes_since_start=0, now=NOW, **RATES)
        return package, work

    def job_a(self, package: Path, work: Path, engine: FakeEngine, **kwargs) -> dict:
        kwargs.setdefault("clock", lambda: NOW + timedelta(minutes=10))
        kwargs.setdefault("watchdog_fire", lambda: None)  # 真实动作是 os._exit，测试里不能杀掉测试进程
        return cloud_runner.run_job_a(package, work, engine, code_location_check=False, **kwargs)

    def job_b(self, package: Path, work: Path, engine: FakeEngine, **kwargs) -> dict:
        kwargs.setdefault("clock", lambda: NOW + timedelta(hours=3))
        kwargs.setdefault("watchdog_fire", lambda: None)
        return cloud_runner.run_job_b(package, work, engine, code_location_check=False, **kwargs)

    def bring_back(self, work: Path, job_id: str) -> Path:
        destination = self.local / verify_return.RETURNED_DIRNAME / job_id
        shutil.copytree(work / "returned" / job_id, destination)
        return destination

    def rebundle_changed(self) -> dict:
        """生产路径造一份合法但不同的代码束：改一个受束源文件、提交、重打（K4 数据包不动）。"""
        source = self.root / "tools" / "eng_sft" / "train_lora.py"
        source.write_text(source.read_text(encoding="utf-8") + "\n# changed after the job started\n",
                          encoding="utf-8")
        synth.git_commit_all(self.root)
        return self.bundle()

    def snapshot(self, root: Path) -> dict[str, str]:
        return {path.relative_to(root).as_posix(): receipts.sha256_file(path)
                for path in sorted(root.rglob("*")) if path.is_file()}


class PackageTests(K3Case):
    def test_missing_or_extra_member_in_either_manifest_refuses_run(self) -> None:
        self.bundle()
        package, work = self.cloud()
        result = cloud_runner.verify_package(package)
        self.assertEqual(result["frozen_chain"], "OK")
        self.assertTrue(result["full"])
        good = self.snapshot(package)

        def expect(mutate, reason="PACKAGE_INCOMPLETE") -> None:
            mutate()
            with self.assertRaises(receipts.EngSftError) as raised:
                cloud_runner.verify_package(package)
            self.assertEqual(raised.exception.reason, reason)
            # 作业也拒绝启动：启动账一条都不记。
            with self.assertRaises(receipts.EngSftError):
                self.job_a(package, work, FakeEngine(self))
            self.assertEqual(cloud_runner.StageLedger(work).entries, [])
            self.cloud()  # 还原成原包

        code_member = package / "code/tools/eng_sft/train_lora.py"
        frame = next(iter(sorted((package / "frames").iterdir())))
        expect(lambda: code_member.unlink())                                   # K3 缺件
        expect(lambda: (package / "code/tools/eng_sft/extra.py").write_text("x"))  # K3 多件
        expect(lambda: frame.unlink())                                         # K4 缺件
        expect(lambda: (package / "data/notes.txt").write_text("x"))           # K4 多件
        expect(lambda: frame.write_bytes(frame.read_bytes() + b"\0"))          # 帧字节不等于文件名
        expect(lambda: (package / "code/tools/eng_sft/__pycache__").mkdir()
               or (package / "code/tools/eng_sft/__pycache__/x.pyc").write_bytes(b"x"))
        self.assertEqual(self.snapshot(package), good)

    def test_code_manifest_lists_every_bundle_member_except_itself(self) -> None:
        document = self.bundle()
        manifest = json.loads((self.upload / cloud_runner.CODE_MANIFEST_NAME).read_text(encoding="utf-8"))
        on_disk = {path.relative_to(self.upload).as_posix()
                   for path in (self.upload / "code").rglob("*") if path.is_file()}
        self.assertEqual(set(manifest["members"]), on_disk)
        self.assertEqual(set(manifest["members"]), {member for member, _ in cloud_runner.BUNDLE_MEMBERS})
        self.assertNotIn(cloud_runner.CODE_MANIFEST_NAME, manifest["members"])
        for name, entry in manifest["members"].items():
            self.assertEqual(entry["sha256"], receipts.sha256_file(self.upload / name))
            self.assertEqual(entry["bytes"], (self.upload / name).stat().st_size)
        self.assertEqual(manifest["members"]["code/tools/__init__.py"]["bytes"], 0)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True,
                              text=True, check=True).stdout.strip()
        self.assertEqual(manifest["source_head"], head)
        for excluded in cloud_runner.BUNDLE_EXCLUDED:
            self.assertNotIn(f"code/{excluded}", on_disk)
        self.assertFalse([name for name in on_disk if name.endswith(("three_state.py", "evaluate.py",
                                                                     "build_sft_data.py", "label_audit.py"))])
        self.assertEqual(manifest["upload_manifest_sha256"],
                         receipts.sha256_file(self.upload / cloud_runner.UPLOAD_MANIFEST_NAME))
        self.assertEqual(document["code_manifest_sha256"],
                         receipts.sha256_file(self.upload / cloud_runner.CODE_MANIFEST_NAME))
        bundle_receipt = self.local / receipts.RECEIPTS_DIRNAME / cloud_runner.BUNDLE_RECEIPT_NAME
        self.assertEqual(json.loads(bundle_receipt.read_text(encoding="utf-8"))["source_head"], head)

    def test_bundle_refuses_uncommitted_source(self) -> None:
        runner = self.root / "tools/eng_sft/cloud_runner.py"
        runner.write_text(runner.read_text(encoding="utf-8") + "\n# local edit\n", encoding="utf-8")
        with self.assertRaises(receipts.EngSftError) as raised:
            self.bundle()
        self.assertEqual(raised.exception.reason, "FROZEN_FILE_DIRTY")
        self.assertFalse((self.upload / "code").exists())
        self.assertFalse((self.upload / cloud_runner.CODE_MANIFEST_NAME).exists())
        self.assertTrue(list((self.local / receipts.RECEIPTS_DIRNAME).glob("failure-bundle-*.json")))


class FreezeTests(K3Case):
    def _rewrite_member(self, package: Path, member: str, payload: bytes) -> None:
        """改一个代码成员并同步改 code-manifest（成员核对能过，冻结链必须拦住）。"""
        (package / member).write_bytes(payload)
        manifest_path = package / cloud_runner.CODE_MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["members"][member] = dict(manifest["members"][member], sha256=sha_bytes(payload),
                                           bytes=len(payload))
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    def test_mismatched_manifest_or_receipt_refuses_run(self) -> None:
        self.bundle()
        package, work = self.cloud()
        # (1) 代码束里的 prompt_v2 被改过（清单也跟着改）：与冻结收据不符。
        member = "code/tools/eng_sft/prompt_v2.py"
        self._rewrite_member(package, member, (package / member).read_bytes() + b"\n# drift\n")
        with self.assertRaises(receipts.EngSftError) as raised:
            cloud_runner.verify_package(package)
        self.assertEqual(raised.exception.reason, "FROZEN_SET_MISMATCH")
        # (2) 数据包清单被改：code-manifest 绑定的不是这一份。
        package, work = self.cloud()
        manifest_path = package / cloud_runner.UPLOAD_MANIFEST_NAME
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        document["note"] = "edited"
        manifest_path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(receipts.EngSftError) as raised:
            cloud_runner.verify_package(package)
        self.assertEqual(raised.exception.reason, "FROZEN_SET_MISMATCH")
        # (3) 冻结收据副本与数据包清单记录不符（副本被换、清单成员也被改齐）。
        package, work = self.cloud()
        freeze_copy = package / "manifests" / cloud_runner.FREEZE_RECEIPT_NAME
        payload = freeze_copy.read_bytes().replace(b'"work_id"', b'"work_id_x"', 1)
        freeze_copy.write_bytes(payload)
        manifest_path = package / cloud_runner.UPLOAD_MANIFEST_NAME
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        document["members"]["manifests/freeze-receipt.json"] = {"bytes": len(payload), "sha256": sha_bytes(payload)}
        manifest_path.write_text(json.dumps(document), encoding="utf-8")
        code_path = package / cloud_runner.CODE_MANIFEST_NAME
        code = json.loads(code_path.read_text(encoding="utf-8"))
        code["upload_manifest_sha256"] = receipts.sha256_file(manifest_path)
        code_path.write_text(json.dumps(code), encoding="utf-8")
        with self.assertRaises(receipts.EngSftError) as raised:
            cloud_runner.verify_package(package)
        self.assertEqual(raised.exception.reason, "FROZEN_SET_MISMATCH")
        with self.assertRaises(receipts.EngSftError):
            self.job_a(package, work, FakeEngine(self))
        self.assertEqual(cloud_runner.StageLedger(work).entries, [])

    def test_frozen_files_and_data_package_untouched_by_candidate_2(self) -> None:
        data_manifest = json.loads((self.upload / "manifest.json").read_text(encoding="utf-8"))
        k4_members = {name: receipts.sha256_file(self.upload / name) for name in data_manifest["members"]}
        k4_manifest = receipts.sha256_file(self.upload / "manifest.json")
        freeze = json.loads((self.local / receipts.RECEIPTS_DIRNAME / "freeze-receipt.json").read_text(encoding="utf-8"))
        frozen_before = {name: receipts.sha256_file(self.root / name) for name in freeze["frozen_set"]}
        data_before = self.snapshot(self.local / build.DATA_DIRNAME)
        self.bundle()
        self.bundle()  # 重打一次也只换代码束
        self.assertEqual({name: receipts.sha256_file(self.upload / name) for name in data_manifest["members"]},
                         k4_members)
        self.assertEqual(receipts.sha256_file(self.upload / "manifest.json"), k4_manifest)
        self.assertEqual({name: receipts.sha256_file(self.root / name) for name in freeze["frozen_set"]},
                         frozen_before)
        for name, entry in freeze["frozen_set"].items():
            self.assertEqual(frozen_before[name], entry["sha256"])
        self.assertEqual(self.snapshot(self.local / build.DATA_DIRNAME), data_before)
        top = {path.name for path in self.upload.iterdir()}
        self.assertEqual(top, {"frames", "data", "manifests", "manifest.json", "code", "code-manifest.json"})

    @unittest.skipUnless(
        (PROJECT_ROOT / receipts.LOCAL_ROOT / receipts.RECEIPTS_DIRNAME / "freeze-receipt.json").is_file(),
        "本机没有 K4 冻结收据（一次性 worktree）",
    )
    def test_real_frozen_set_still_matches_local_freeze_receipt(self) -> None:
        """候选 2 不改真实仓库里的冻结闭集：八个冻结文件 SHA 仍等于 K4 冻结收据。"""
        receipt = PROJECT_ROOT / receipts.LOCAL_ROOT / receipts.RECEIPTS_DIRNAME / "freeze-receipt.json"
        freeze = json.loads(receipt.read_text(encoding="utf-8"))
        for name, entry in freeze["frozen_set"].items():
            self.assertEqual(receipts.sha256_file(PROJECT_ROOT / name), entry["sha256"], name)


class LedgerTests(K3Case):
    def test_launch_limits_count_failures_and_refuse_excess(self) -> None:
        work = self.cloud_root / "ledger"
        ledger = cloud_runner.StageLedger(work)
        first = ledger.start("zero_shot", job_id="j", label="zero-shot")
        ledger.finish(first, "failed:EXCEPTION")
        second = ledger.start("zero_shot", job_id="j", label="zero-shot")
        ledger.finish(second, "succeeded")
        with self.assertRaises(cloud_runner.LaunchRefused):  # 零样本 ≤ 2（失败也计）
            ledger.start("zero_shot", job_id="j", label="zero-shot")
        for _ in range(4):
            ledger.start("train", job_id="j", label="C1")
        with self.assertRaises(cloud_runner.LaunchRefused):  # 训练 ≤ 4
            ledger.start("train", job_id="j", label="C1")
        ledger.start("smoke", job_id="j", label="smoke")
        ledger.start("smoke", job_id="j", label="smoke")
        with self.assertRaises(cloud_runner.LaunchRefused):  # 总启动 ≤ 8
            ledger.start("eval", job_id="j", label="eval")
        reloaded = cloud_runner.StageLedger(work)  # 持久化在实例上，重开进程也记得
        self.assertEqual(sum(reloaded.counts().values()), 8)

    def test_budget_guard_caps_hours_and_dollars(self) -> None:
        cheap = self.cloud_root / "cheap"
        document = cloud_runner.init_budget(cheap, minutes_since_start=5, now=NOW, gpu_usd_per_hour=0.55,
                                            storage_usd_per_hour=0.0, inbound_usd_per_tb=0.0,
                                            outbound_usd_per_tb=0.0)
        self.assertEqual(document["effective_cap_hours"], 8.0)  # 0.55 美元/h：8 GPU·h 先到
        self.assertEqual(document["binding_cap"], "gpu_hours")
        self.assertEqual(document["destroy_deadline_utc"], "20260920T155500Z")  # 开机 07:55 + 8 h
        self.assertEqual(document["guard_stop_utc"], "20260920T154900Z")       # 提前 6 分钟
        guard = cloud_runner.BudgetGuard(cheap, clock=lambda: NOW + timedelta(hours=7, minutes=48))
        self.assertFalse(guard.should_stop())  # 开机 5 分钟 + 7 h 48 min = 7 h 53 min < 8 h − 6 min
        guard = cloud_runner.BudgetGuard(cheap, clock=lambda: NOW + timedelta(hours=7, minutes=50))
        self.assertTrue(guard.should_stop())  # 7 h 55 min ≥ 7 h 54 min：停
        dear = self.cloud_root / "dear"
        document = cloud_runner.init_budget(dear, minutes_since_start=0, now=NOW, gpu_usd_per_hour=1.0,
                                            storage_usd_per_hour=0.0, inbound_usd_per_tb=0.0,
                                            outbound_usd_per_tb=0.0)
        self.assertEqual(document["effective_cap_hours"], 6.0)  # 1 美元/h：6 美元先到
        guard = cloud_runner.BudgetGuard(dear, clock=lambda: NOW + timedelta(hours=5, minutes=50))
        with self.assertRaises(train_lora.BudgetStop):
            guard.require("train")
        with self.assertRaises(cloud_runner.LaunchRefused):  # 只初始化一次
            cloud_runner.init_budget(dear, minutes_since_start=0, now=NOW, **RATES)
        with self.assertRaises(cloud_runner.LaunchRefused):  # 不得超出信封
            cloud_runner.init_budget(self.cloud_root / "x", minutes_since_start=0, now=NOW,
                                     cap_gpu_hours=9, **RATES)

    def test_budget_plan_reserves_storage_and_transfer_inside_six_dollars(self) -> None:
        plan = cloud_runner.budget_plan(gpu_usd_per_hour=0.70, storage_usd_per_hour=0.05,
                                        inbound_usd_per_tb=20.0, outbound_usd_per_tb=20.0)
        transfer = (cloud_runner.DEFAULT_INBOUND_GB + cloud_runner.DEFAULT_OUTBOUND_GB) / 1000 * 20.0
        self.assertAlmostEqual(plan["transfer_reserve_usd"], round(transfer, 4))
        self.assertAlmostEqual(plan["absolute_cap_hours"], round((6.0 - transfer) / 0.75, 4))
        self.assertEqual(plan["binding_cap"], "usd")  # 0.75 美元/h 含存储 → 美元先到（< 8 h）
        self.assertAlmostEqual(plan["guard_stop_hours"], round(plan["absolute_cap_hours"] - 0.1, 4), places=3)
        self.assertEqual(plan["estimated_need_hours"], cloud_runner.ESTIMATED_NEED_HOURS)
        for bad in ({"storage_usd_per_hour": -1.0}, {"inbound_usd_per_tb": None}, {"gpu_usd_per_hour": 0.0}):
            rates = dict(gpu_usd_per_hour=0.55, storage_usd_per_hour=0.0, inbound_usd_per_tb=0.0,
                         outbound_usd_per_tb=0.0)
            rates.update(bad)
            with self.assertRaises(cloud_runner.LaunchRefused):  # 费率不明/不合理 → 不租
                cloud_runner.budget_plan(**rates)
        with self.assertRaises(cloud_runner.LaunchRefused):  # 流量就吃光 6 美元
            cloud_runner.budget_plan(gpu_usd_per_hour=0.5, storage_usd_per_hour=0.0,
                                     inbound_usd_per_tb=600.0, outbound_usd_per_tb=0.0)
        self.assertFalse(cloud_runner.budget_plan(gpu_usd_per_hour=2.0, storage_usd_per_hour=0.0,
                                                  inbound_usd_per_tb=0.0, outbound_usd_per_tb=0.0)["estimate_fits"])
        with self.assertRaises(SystemExit):  # 命令行四项费率缺一不可
            cloud_runner.main(["budget-plan", "--gpu-usd-per-hour", "0.5"])

    def test_watchdog_fires_without_waiting_for_a_step_callback(self) -> None:
        work = self.cloud_root / "watchdog"
        cloud_runner.init_budget(work, minutes_since_start=0, now=NOW, **RATES)
        moments = iter([NOW + timedelta(minutes=1)] * 2 + [NOW + timedelta(hours=9)] * 100)
        guard = cloud_runner.BudgetGuard(work, clock=lambda: next(moments))
        fired = []
        dog = cloud_runner.Watchdog(guard, on_fire=lambda: fired.append(True), poll_seconds=0.05).start()
        dog._thread.join(timeout=5)
        self.assertEqual(fired, [True])
        self.assertTrue(dog.fired)

    def test_watchdog_exit_records_stop_before_exiting(self) -> None:
        self.bundle()
        package, work = self.cloud()
        engine = FakeEngine(self)
        receipt = self.job_a(package, work, engine)
        job = cloud_runner.Job(work, "A", "x", resume=receipt["job_id"])
        ledger = cloud_runner.StageLedger(work)
        ledger.start("eval", job_id=job.id, label="eval")  # 模拟卡在某一阶段中途
        guard = cloud_runner.BudgetGuard(work, clock=lambda: NOW + timedelta(hours=9))
        with mock.patch.object(cloud_runner.os, "_exit", side_effect=SystemExit(3)):
            with self.assertRaises(SystemExit):
                cloud_runner._hard_exit_after(job, ledger, guard)()
        self.assertEqual(cloud_runner.StageLedger(work).entries[-1]["status"], "stopped_budget_watchdog")
        self.assertTrue((job.dir / "watchdog-stop.json").is_file())
        final = json.loads((job.dir / cloud_runner.JOB_RECEIPT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(final["outcome"], "stopped_budget_watchdog")
        self.assertIn("watchdog-stop.json", final["artifacts"])

    def test_budget_stop_mid_stage_voids_partial_predictions(self) -> None:
        self.bundle()
        package, work = self.cloud()
        engine = FakeEngine(self)
        state = {"rows": 0}
        original = engine._status

        def counting_status(row, adapter):
            state["rows"] += 1  # 零样本已写出若干行后越线
            return original(row, adapter)

        engine._status = counting_status

        def clock() -> datetime:
            return NOW + (timedelta(minutes=10) if state["rows"] < 5 else timedelta(hours=8))

        with self.assertRaises(train_lora.BudgetStop):
            self.job_a(package, work, engine, clock=clock)
        self.assertEqual(state["rows"], 5)
        ledger = cloud_runner.StageLedger(work)
        self.assertEqual([entry["status"] for entry in ledger.entries], ["stopped_budget"])
        returned = next((work / "returned").iterdir())
        self.assertFalse((returned / "predictions" / "zero-shot.jsonl").exists())
        self.assertFalse(list(returned.rglob("*.partial")))
        receipt = json.loads((returned / cloud_runner.JOB_RECEIPT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(receipt["outcome"], "stopped_budget")
        self.assertTrue(list((returned / "receipts").glob("run-stop-*.json")))


class SetupStopTests(K3Case):
    def test_budget_stop_during_setup_leaves_stop_receipt(self) -> None:
        self.bundle()
        package, work = self.cloud()
        ticks = {"n": 0}

        def clock() -> datetime:
            ticks["n"] += 1  # 前置检查通过，下载/网格预检时越线
            return NOW + (timedelta(minutes=10) if ticks["n"] <= 3 else timedelta(hours=8))

        with self.assertRaises(train_lora.BudgetStop):
            self.job_a(package, work, FakeEngine(self), clock=clock, watchdog_fire=lambda: None)
        self.assertEqual(cloud_runner.StageLedger(work).entries, [])  # 没有阶段启动
        returned = next((work / "returned").iterdir())
        self.assertTrue(list((returned / "receipts").glob("run-stop-*.json")))
        receipt = json.loads((returned / cloud_runner.JOB_RECEIPT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(receipt["outcome"], "stopped_budget")


class SelfcheckTests(K3Case):
    def _pack(self) -> Path:
        self.bundle()
        out = self.cloud_root / "desk" / cloud_runner.SELFCHECK_TRANSPORT_NAME
        document = cloud_runner.run_selfcheck_pack(out_path=out, repo_root=self.root, local_root=self.local)
        self.assertEqual(document["data_files"], ["data/smoke.jsonl"])
        return out

    def test_selfcheck_pack_carries_only_smoke_code_and_manifests(self) -> None:
        out = self._pack()
        with tarfile.open(out) as archive:
            names = sorted(member.name for member in archive.getmembers())
        smoke_frames = {row["frame_path"] for row in self.read_local("smoke.jsonl")}
        self.assertEqual({n for n in names if n.startswith("upload/frames/")},
                         {f"upload/{frame}" for frame in smoke_frames})
        self.assertEqual([n for n in names if n.startswith("upload/data/")], ["upload/data/smoke.jsonl"])
        for forbidden in ("train.jsonl", "select-eval", "eval.blind.jsonl", "eval.jsonl"):
            self.assertFalse([n for n in names if forbidden in n], forbidden)
        self.assertIn("upload/code/tools/eng_sft/cloud_runner.py", names)
        self.assertIn("upload/code-manifest.json", names)
        with self.assertRaises(receipts.EngSftError):  # 不能写进包根
            cloud_runner.run_selfcheck_pack(out_path=self.upload / "x.tar", repo_root=self.root,
                                            local_root=self.local)

    def _laptop(self) -> tuple[Path, Path, cloud_runner.ModelSource]:
        out = self._pack()
        laptop = self.cloud_root / "laptop"
        with tarfile.open(out) as archive:
            archive.extractall(laptop, filter="data")
        model = self.cloud_root / "model"
        model.mkdir()
        for name in cloud_runner.TOKENIZER_FILES:
            shutil.copy2(self.tokenizer_dir / name, model / name)
        return laptop / "upload", laptop / "work", cloud_runner.ModelSource(str(model), None)

    def test_selfcheck_runs_on_transport_copy_and_counts_runs(self) -> None:
        package, work, source = self._laptop()
        engine = FakeEngine(self)
        report = cloud_runner.run_selfcheck(package, work, engine, source=source, code_location_check=False)
        self.assertEqual(report["status"], "succeeded")
        self.assertEqual(report["nature"], "DIAGNOSTIC_NOT_EVIDENCE")
        self.assertFalse(report["verify"]["full"])
        self.assertEqual(set(report["tokenizer_recheck"]["files"]), {"smoke.jsonl"})
        self.assertEqual(report["zero_shot"]["rows"], 4)
        self.assertEqual(report["train"]["steps"], 5)
        self.assertEqual(report["adapter_reload"]["rows"], 4)
        self.assertIn("note", report["pins"])
        # 读取域：模型只看过 smoke 行。
        for path, _rows in engine.predicted:
            self.assertTrue(Path(path).is_relative_to(work), path)
        cloud_runner.run_selfcheck(package, work, engine, source=source, code_location_check=False)
        cloud_runner.run_selfcheck(package, work, engine, source=source, code_location_check=False)
        with self.assertRaises(cloud_runner.LaunchRefused):  # 第 4 次：信封用完
            cloud_runner.run_selfcheck(package, work, engine, source=source, code_location_check=False)
        with self.assertRaises(cloud_runner.LaunchRefused):  # 超出行数/步数信封
            cloud_runner.run_selfcheck(package, self.cloud_root / "w2", engine, source=source, rows=5,
                                       code_location_check=False)

    def test_selfcheck_preflight_refusal_is_not_counted(self) -> None:
        package, work, source = self._laptop()
        engine = FakeEngine(self)
        engine.missing = ["peft"]
        with self.assertRaises(cloud_runner.LaunchRefused):
            cloud_runner.run_selfcheck(package, work, engine, source=source, code_location_check=False)
        counter = work / "selfcheck-count.json"
        self.assertFalse(counter.exists() and json.loads(counter.read_text(encoding="utf-8"))["runs"])
        self.assertEqual(engine.predicted, [])
        engine.missing = []
        failing = FakeEngine(self, tokenizer_tamper=False)
        failing.encoder = lambda path: (lambda text: 10_000, {"library": "stub"})  # 复核必失败 → 计次
        with self.assertRaises(receipts.EngSftError):
            cloud_runner.run_selfcheck(package, work, failing, source=source, code_location_check=False)
        runs = json.loads(counter.read_text(encoding="utf-8"))["runs"]
        self.assertEqual([run["status"] for run in runs], ["failed"])

    def test_selfcheck_rejects_out_of_range_values_before_counting(self) -> None:
        # C1-K3-3：负数/零同样越出 ≤4 行、≤5 步信封（`--rows -1` 会让 [:rows] 取 31 行），计次与模型调用前拒绝。
        package, work, source = self._laptop()
        engine = FakeEngine(self)
        for kwargs in ({"rows": -1}, {"rows": 0}, {"rows": 5}, {"steps": -1}, {"steps": 0}, {"steps": 6},
                       {"micro_batch": 0}, {"micro_batch": -2}, {"rows": True}):
            with self.subTest(**kwargs), self.assertRaises(cloud_runner.LaunchRefused):
                cloud_runner.run_selfcheck(package, work, engine, source=source, code_location_check=False,
                                           **kwargs)
        self.assertFalse((work / "selfcheck-count.json").exists())
        self.assertEqual(engine.predicted, [])
        self.assertEqual(engine.trained, [])
        for bad in (0, -1):
            with self.subTest(micro_batch=bad), self.assertRaises(cloud_runner.LaunchRefused):
                cloud_runner.TorchEngine(micro_batch=bad)


class JobTests(K3Case):
    def test_job_a_resume_skips_finished_stages_and_counts_retry(self) -> None:
        self.bundle()
        package, work = self.cloud()
        engine = FakeEngine(self, fail_once=("C2",))
        with self.assertRaises(RuntimeError):
            self.job_a(package, work, engine)
        first = next((work / "returned").iterdir())
        receipt = json.loads((first / cloud_runner.JOB_RECEIPT_NAME).read_text(encoding="utf-8"))
        self.assertFalse(receipt["complete"])
        self.assertEqual(receipt["stages"]["C2"]["status"], "failed:EXCEPTION")
        self.job_a(package, work, engine, resume=first.name)
        self.assertEqual(engine.trained, ["smoke", "C1", "C2", "C3"])  # 零样本/冒烟/C1 不重跑
        ledger = cloud_runner.StageLedger(work)
        self.assertEqual(ledger.counts(), {"zero_shot": 1, "smoke": 1, "train": 4, "eval": 0})
        receipt = json.loads((first / cloud_runner.JOB_RECEIPT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(receipt["complete"])
        self.assertEqual(sorted(receipt["runs"]), ["C1", "C2", "C3"])
        self.assertEqual(receipt["transfer_branch"], "NOT_RUN(SFT_003_NOT_DONE)")
        self.assertEqual(receipt["image_grid"]["unity"]["expected"], [1, 30, 40])
        self.assertTrue(receipt["tokenizer_recheck"]["matches_precheck_receipt"])
        self.assertEqual(set(receipt["tokenizer_recheck"]["files"]), {"train.jsonl", "smoke.jsonl"})
        rows = train_lora.read_jsonl(first / "predictions" / "zero-shot.jsonl")
        self.assertEqual(len(rows), len(self.read_local("eval.blind.jsonl")))
        self.assertTrue(re.fullmatch(r"sft-\d{8}T\d{6}Z-[0-9a-f]{8}", first.name))
        # 同包续跑：包身份与环境记录保持首跑原值，续跑只追加一条记录。
        self.assertEqual(len(receipt["resumes"]), 1)
        self.assertEqual(cloud_runner.package_identity(receipt["resumes"][0]["package"]),
                         cloud_runner.package_identity(receipt["package"]))

    def test_resume_with_changed_bundle_or_environment_is_refused_before_any_write(self) -> None:
        # C1-K3-1：旧阶段产物不能被记成另一份代码束或另一套环境的产出。
        self.bundle()
        package, work = self.cloud()
        engine = FakeEngine(self, fail_once=("C2",))
        with self.assertRaises(RuntimeError):
            self.job_a(package, work, engine)
        first = next((work / "returned").iterdir())
        before = self.snapshot(first)
        counts = cloud_runner.StageLedger(work).counts()
        other_env = dict(engine.environment(), torch="other")
        with mock.patch.object(engine, "environment", return_value=other_env), \
                self.assertRaises(cloud_runner.LaunchRefused):
            self.job_a(package, work, engine, resume=first.name)
        self.assertEqual(self.snapshot(first), before)
        self.rebundle_changed()
        package, work = self.cloud()
        with self.assertRaises(cloud_runner.LaunchRefused):
            self.job_a(package, work, engine, resume=first.name)
        self.assertEqual(self.snapshot(first), before)
        self.assertEqual(cloud_runner.StageLedger(work).counts(), counts)
        self.assertEqual(engine.trained, ["smoke", "C1"])

    def test_job_b_refuses_job_a_from_another_bundle_before_creating_job(self) -> None:
        # C1-K3-1：作业 B 消费 A 的 adapter 前，A 记录的包身份须等于当前全包校验结果。
        self.bundle()
        package, work = self.cloud()
        engine = FakeEngine(self)
        receipt_a = self.job_a(package, work, engine)
        self.rebundle_changed()
        package, work = self.cloud()
        jobs = sorted(path.name for path in (work / "returned").iterdir())
        with self.assertRaises(cloud_runner.LaunchRefused):
            self.job_b(package, work, engine, from_job=receipt_a["job_id"], adapter="C2")
        self.assertEqual(sorted(path.name for path in (work / "returned").iterdir()), jobs)
        self.assertEqual(cloud_runner.StageLedger(work).counts()["eval"], 0)

    def test_smoke_failure_stops_before_training(self) -> None:
        self.bundle()
        package, work = self.cloud()
        engine = FakeEngine(self, smoke_loss=0.2)
        with self.assertRaises(receipts.EngSftError) as raised:
            self.job_a(package, work, engine)
        self.assertEqual(raised.exception.reason, "SMOKE_FAILED")
        self.assertEqual(engine.trained, ["smoke"])
        returned = next((work / "returned").iterdir())
        self.assertTrue((returned / "smoke" / "smoke-result.json").is_file())
        self.assertFalse((returned / "smoke" / "adapter").exists())
        self.assertTrue(list((returned / "receipts").glob("failure-job-a-smoke-*.json")))

    def test_job_refuses_wrong_gpu_or_version_drift(self) -> None:
        self.bundle()
        package, work = self.cloud()
        with self.assertRaises(cloud_runner.LaunchRefused):
            self.job_a(package, work, FakeEngine(self, gpu_name="NVIDIA A100-SXM4-80GB"))
        with mock.patch.object(cloud_runner, "check_pins", REAL_CHECK_PINS):  # 本机没装钉版本 → 漂移
            with self.assertRaises(cloud_runner.LaunchRefused):
                self.job_a(package, work, FakeEngine(self))
        with self.assertRaises(SystemExit):  # 命令行没有任何绕过开关（AC-13 修订 1）
            cloud_runner.main(["job-a", "--package", str(package), "--work", str(work), "--allow-version-drift"])
        self.assertEqual(cloud_runner.StageLedger(work).entries, [])
        self.assertFalse((work / "returned").exists() and any((work / "returned").iterdir()))

    def test_tokenizer_file_mismatch_stops_before_inference(self) -> None:
        self.bundle()
        package, work = self.cloud()
        engine = FakeEngine(self, tokenizer_tamper=True)
        with self.assertRaises(receipts.EngSftError) as raised:
            self.job_a(package, work, engine)
        self.assertEqual(raised.exception.reason, "TOKENIZER_MISMATCH")
        self.assertEqual(engine.predicted, [])
        self.assertEqual(cloud_runner.StageLedger(work).entries, [])
        returned = next((work / "returned").iterdir())
        self.assertTrue(list((returned / "receipts").glob("failure-job-a-preflight-*.json")))
        receipt = json.loads((returned / cloud_runner.JOB_RECEIPT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(receipt["outcome"], "failed:TOKENIZER_MISMATCH")


class ReturnTests(K3Case):
    def _job_a(self) -> tuple[Path, Path, Path, FakeEngine]:
        self.bundle()
        package, work = self.cloud()
        engine = FakeEngine(self)
        receipt = self.job_a(package, work, engine)
        local_dir = self.bring_back(work, receipt["job_id"])
        return package, work, local_dir, engine

    def test_return_hash_mismatch_refuses_scoring(self) -> None:
        _package, _work, returned, _engine = self._job_a()
        verify_return.verify_returned(returned, repo_root=self.root, local_root=self.local)
        target = returned / "runs" / "C1" / "select-predictions.jsonl"
        target.write_bytes(target.read_bytes().replace(b'"none"', b'"unique"', 1))
        with self.assertRaises(receipts.EngSftError) as raised:
            verify_return.verify_returned(returned, repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "RETURN_HASH_MISMATCH")
        with self.assertRaises(receipts.EngSftError) as raised:
            verify_return.select_adapter(returned, repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "RETURN_HASH_MISMATCH")
        self.assertFalse(list((self.local / receipts.RECEIPTS_DIRNAME).glob("selection-*.json")))
        self.assertTrue(list((self.local / receipts.RECEIPTS_DIRNAME).glob("failure-return-*.json")))

    def test_summarise_refuses_selection_not_bound_to_current_job_a(self) -> None:
        # C1-K3-2：对未完成的 A 做过 select，A 续跑完成后旧选优收据不能被当成当前选优。
        self.bundle()
        package, work = self.cloud()
        engine = FakeEngine(self, fail_once=("C3",))
        with self.assertRaises(RuntimeError):
            self.job_a(package, work, engine)
        job_id = next((work / "returned").iterdir()).name
        partial = self.bring_back(work, job_id)
        stale = verify_return.select_adapter(partial, repo_root=self.root, local_root=self.local)
        self.assertEqual(stale["missing_runs"], ["C3"])
        self.job_a(package, work, engine, resume=job_id)
        shutil.rmtree(partial)
        returned_a = self.bring_back(work, job_id)
        with self.assertRaises(receipts.EngSftError) as raised:
            verify_return.summarise(returned_a, repo_root=self.root, local_root=self.local, write=False)
        self.assertEqual(raised.exception.reason, "RETURN_HASH_MISMATCH")
        fresh = verify_return.select_adapter(returned_a, repo_root=self.root, local_root=self.local)
        self.assertEqual(fresh["missing_runs"], [])
        self.assertNotEqual(fresh["job_receipt_sha256"], stale["job_receipt_sha256"])
        summaries = verify_return.summarise(returned_a, repo_root=self.root, local_root=self.local, write=False)
        self.assertEqual(summaries["train"]["selection"]["job_receipt_sha256"], fresh["job_receipt_sha256"])

    def test_returned_manifest_must_match_local_package_and_bundle(self) -> None:
        _package, _work, returned, _engine = self._job_a()
        self.bundle()  # 本地重打代码束：收据里的 code-manifest SHA 不变（字节相同）
        verify_return.verify_returned(returned, repo_root=self.root, local_root=self.local)
        bundle_receipt = self.local / receipts.RECEIPTS_DIRNAME / cloud_runner.BUNDLE_RECEIPT_NAME
        document = json.loads(bundle_receipt.read_text(encoding="utf-8"))
        document["code_manifest_sha256"] = "0" * 64
        bundle_receipt.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(receipts.EngSftError) as raised:
            verify_return.verify_returned(returned, repo_root=self.root, local_root=self.local)
        self.assertEqual(raised.exception.reason, "RETURN_HASH_MISMATCH")

    def test_end_to_end_select_job_b_and_summaries(self) -> None:
        package, work, returned_a, engine = self._job_a()
        selection = verify_return.select_adapter(returned_a, repo_root=self.root, local_root=self.local)
        self.assertEqual(selection["selection"]["chosen"], "C2")  # 夹具里 C2 的选层状态全对
        self.assertEqual(selection["missing_runs"], [])
        receipt_b = self.job_b(package, work, engine, from_job=returned_a.name, adapter="C2")
        self.assertEqual(cloud_runner.StageLedger(work).counts(),
                         {"zero_shot": 1, "smoke": 1, "train": 3, "eval": 1})
        returned_b = self.bring_back(work, receipt_b["job_id"])
        summaries = verify_return.summarise(returned_a, returned_b, repo_root=self.root, local_root=self.local)
        verdict = summaries["eval"]["verdict"]
        self.assertIn(verdict["functional_gate"]["status"], {"GATE_MET", "GATE_NOT_MET"})
        self.assertIn(verdict["vocabulary_non_inferiority"]["status"], {"NON_INFERIOR", "INFERIOR"})
        self.assertEqual(verdict["transfer"]["status"], "NOT_RUN(SFT_003_NOT_DONE)")
        self.assertNotIn("vocabulary_non_inferiority", summaries["zero_shot"]["verdict"])
        self.assertEqual(summaries["train"]["adapter_manifest"]["adapter_sha256"],
                         selection["chosen_adapter_sha256"])
        self.assertEqual(summaries["train"]["accounting"]["total_launches"], 6)
        for relative in (verify_return.ZERO_SHOT_SUMMARY, verify_return.TRAIN_SUMMARY, verify_return.EVAL_SUMMARY):
            path = self.root / relative
            self.assertTrue(path.is_file(), relative)
            self.assertLessEqual(path.stat().st_size, verify_return.VERSIONED_FILE_MAX_BYTES)
        # AC-13：失败案例按判定组 min(10, 失败数) 条、row_id 升序，只列真失败行。
        eval_rows = train_lora.read_jsonl(self.local / "data" / "eval.jsonl")
        adapter_rows = train_lora.read_jsonl(returned_b / "predictions" / "eval-adapter.jsonl")
        scores = {s.row_id: s for s in evaluate.score_rows(eval_rows, adapter_rows)
                  if s.group in verify_return.FAILURE_CASE_GROUPS}
        cases = summaries["eval"]["failure_cases"]
        self.assertEqual(set(cases["groups"]), set(verify_return.FAILURE_CASE_GROUPS))
        for group, entry in cases["groups"].items():
            failing = sorted(r for r, s in scores.items() if s.group == group and (
                not s.strict_success if group in evaluate.SET_GROUPS else not s.success))
            self.assertEqual(entry["failures"], len(failing), group)
            self.assertEqual([c["row_id"] for c in entry["cases"]], failing[:10], group)
        capped = verify_return.failure_cases(eval_rows, adapter_rows, limit=1)
        for group, entry in capped["groups"].items():
            self.assertEqual(entry["shown"], min(1, entry["failures"]), group)
        self.assertTrue(any(entry["failures"] for entry in capped["groups"].values()))
        # AC-11 命令读得出判定。
        self.assertEqual(evaluate.main(["--verdict", str(self.root / verify_return.EVAL_SUMMARY)]), 0)
        # 作业 B 用了不是选优结果的 adapter → 拒绝。
        receipt_bad = self.job_b(package, work, engine, from_job=returned_a.name, adapter="C1")
        returned_bad = self.bring_back(work, receipt_bad["job_id"])
        with self.assertRaises(receipts.EngSftError) as raised:
            verify_return.summarise(returned_a, returned_bad, repo_root=self.root, local_root=self.local,
                                    write=False)
        self.assertEqual(raised.exception.reason, "RETURN_HASH_MISMATCH")


class TransferTests(K3Case):
    def test_syndrone_frames_never_in_training_package(self) -> None:
        self.bundle()
        manifest = json.loads((self.upload / cloud_runner.CODE_MANIFEST_NAME).read_text(encoding="utf-8"))
        self.assertEqual(manifest["transfer_branch"], {"status": "NOT_RUN(SFT_003_NOT_DONE)", "syndrone_members": 0})
        names = [path.relative_to(self.upload).as_posix() for path in self.upload.rglob("*") if path.is_file()]
        self.assertFalse([name for name in names if "syndrone" in name.lower()])
        training = verify_return.package_frame_sha256(self.upload)
        self.assertTrue(training)
        verify_return.assert_transfer_frames_disjoint({"f" * 64}, training)
        with self.assertRaises(receipts.EngSftError) as raised:
            verify_return.assert_transfer_frames_disjoint({"f" * 64, next(iter(training))}, training)
        self.assertEqual(raised.exception.reason, "CONSERVATION_MISMATCH")

    def test_incompatible_schema_yields_not_run(self) -> None:
        self.assertEqual(verify_return.transfer_decision("PROPOSED_D2", False), "NOT_RUN(SFT_003_NOT_DONE)")
        self.assertEqual(verify_return.transfer_decision("DONE", False), "NOT_RUN(SFT_003_NOT_DONE)")
        rows = [{"row_id": "r1", "frame_path": "f.jpg", "group": "G1", "gate_row": True, "surface": "the car",
                 "gold_state": "unique", "gold_boxes_norm_xywh": [[0.1, 0.1, 0.1, 0.1]]}]  # 缺 stratum
        blind = [{"row_id": "r1", "frame_path": "f.jpg", "surface": "the car", "g4": False, "vocab": "x"}]
        problems = evaluate.validate_transfer_rows(rows, blind)
        decision = verify_return.transfer_decision("DONE", True, problems)
        self.assertEqual(decision, "NOT_RUN(INCOMPATIBLE_EVAL_SCHEMA:MISSING_FIELDS:stratum)")
        rows[0]["stratum"] = "M"
        self.assertEqual(verify_return.transfer_decision("DONE", True, evaluate.validate_transfer_rows(rows, blind)),
                         "RUN")
        verdict = evaluate.transfer_verdict({}, None, not_run_reason=verify_return.SFT_003_NOT_DONE)
        self.assertEqual(verdict["status"], "NOT_RUN(SFT_003_NOT_DONE)")


class WriteBoundaryTests(K3Case):
    MODULES = ("tools/eng_sft/train_lora.py", "tools/eng_sft/cloud_runner.py", "tools/eng_sft/verify_return.py")

    def test_no_controller_imports_and_forbidden_roots(self) -> None:
        for relative in self.MODULES:
            source = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"^\s*(from|import)\s+controller\b", source, re.M), relative)
            self.assertIsNone(re.search(r"^\s*(from|import)\s+tools\.dist_data\b", source, re.M), relative)
        forbidden_local = self.root / "runtime" / "frames" / "eng-sft"
        with self.assertRaises(receipts.EngSftError) as raised:
            cloud_runner.run_bundle(repo_root=self.root, local_root=forbidden_local)
        self.assertEqual(raised.exception.reason, "OUTPUT_PATH_FORBIDDEN")
        self.assertFalse(forbidden_local.exists())
        with self.assertRaises(receipts.EngSftError) as raised:
            verify_return._write_evidence(self.root, Path("controller/summary.json"), {"x": 1})
        self.assertEqual(raised.exception.reason, "OUTPUT_PATH_FORBIDDEN")

    def test_bundle_modules_import_only_bundled_code(self) -> None:
        bundled = {Path(source).stem for _, source in cloud_runner.BUNDLE_MEMBERS
                   if source and source.endswith(".py")}
        for _, source in cloud_runner.BUNDLE_MEMBERS:
            if not source or not source.endswith(".py"):
                continue
            text = (PROJECT_ROOT / source).read_text(encoding="utf-8")
            for match in re.finditer(r"^\s*from\s+tools\.(\w+)(?:\.(\w+))?\s+import\s+([\w, ]+)", text, re.M):
                package, module, names = match.group(1), match.group(2), match.group(3)
                self.assertIn(package, {"eng_sft", "eng_asset"}, source)
                imported = [module] if module else [name.strip() for name in names.split(",")]
                for name in imported:
                    self.assertIn(name, bundled, f"{source} imports tools.{package}.{name}")


if __name__ == "__main__":
    unittest.main()
