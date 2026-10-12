#!/usr/bin/env python3
"""K3 云端运行器（表 K ⑥⑦、表 H、表 I）：代码束、包校验、作业 A/B 与上云前自检。

子命令（全部用 `python -B -m tools.eng_sft.cloud_runner <子命令>` 运行；`-B` 让解释器
不在包根写 `__pycache__`，否则 `verify` 会把它当成多出来的文件拒绝）：

- `bundle`（本地，实现角色）：`freeze`/`package` 收据存在后，把表 K 的 K3 代码束复制到
  `upload/code/`，写 `upload/code-manifest.json`（逐文件路径/字节/SHA/来源，记来源 HEAD，
  不含自身）与本地 `bundle` 收据；K4 数据包及其清单一个字节不改。
- `verify`（云端或自检机）：按两份清单逐文件现算 SHA，缺 / 多 / 不符 → `PACKAGE_INCOMPLETE`；
  jsonl/盲文件 SHA = manifest 记录 = 冻结收据副本、prompt/parse 副本 = 冻结收据，
  否则 `FROZEN_SET_MISMATCH`。
- `budget-plan`（租机前，本机即可）：按报价的 GPU/存储小时价与进出流量单价算出最长可用时长；
  `budget-init`（云端，登录后第一件事）：记下开机时刻与费率，写出**销毁截止时刻**。之后每个阶段开始前、
  每行/每步、以及后台看门狗都按「累计 ≤ 8 GPU·h、租金 ≤ 6 美元（含存储与流量），先达即停」检查
  （账本 2026-09-18；AC-13 修订 1）。运行器只能停自己，实例由用户在截止前销毁。
- `job-a`（云端）：校验 → base 权重下载一次 → tokenizer 复核 → 图像网格预检 → 零样本对照
  → 冒烟 → C1/C2/C3 训练 + 盲选层预测，产物写 `returned/<job_id>/`。
- `job-b`（云端，本地选优之后）：被选 adapter 在 Unity 盲评估集预测一次。
- `selfcheck-pack`（本地）：生成只含代码束、清单与 smoke 及其帧的自检运输副本（K3-P2）。
- `selfcheck`（用户 5060 笔记本，诊断，**不是证据**）：只用 `smoke.jsonl` 及其帧，≤ 4 行零样本、
  ≤ 5 步训练、≤ 4 行 adapter 推理，看能否跑通与显存/速度；信封须先由接受/辅助角色入账。
- `status`（云端）：打印启动计次与预算余量。

每个阶段启动（零样本 / 冒烟 / 训练 / 正式评估）都先记入实例上的启动账
`stage-ledger.json`，按信封上限（各阶段子上限、总启动 ≤ 8）拒绝超额启动；失败与中断也计
一次（表 H「中断/失败」）。部分预测文件作废不续跑。

红线：本模块不 import `controller.*`、不 import `tools.dist_data`；评分与判定只在本地
（`verify_return` + 冻结的 `evaluate.py`），选层/评估 gold 永不上云。
"""

from __future__ import annotations

import sys

if sys.platform == "win32":  # pragma: no cover - 只在用户 Windows 自检机上生效
    # `tools.eng_asset.receipts` 为峰值 RSS 导入了 Unix 专有的 `resource`；Windows 上给一个
    # 只返回 0 的替身，让自检能 import 收据模块。Linux 云端与本机测试不受影响。
    try:
        import resource  # noqa: F401
    except ImportError:
        import types

        _shim = types.ModuleType("resource")
        _shim.RUSAGE_SELF = 0
        _shim.getrusage = lambda who: types.SimpleNamespace(ru_maxrss=0)
        sys.modules["resource"] = _shim

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import gc
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import threading
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

from tools.eng_sft import parse, prompt_v2, receipts, train_lora

PROJECT_ROOT = receipts.PROJECT_ROOT

# --- 表 K：K3 代码束闭集 ------------------------------------------------------

UPLOAD_DIRNAME = "upload"
CODE_DIRNAME = "code"
UPLOAD_MANIFEST_NAME = "manifest.json"
CODE_MANIFEST_NAME = "code-manifest.json"
FREEZE_RECEIPT_NAME = "freeze-receipt.json"
PRECHECK_RECEIPT_NAME = "precheck-receipt.json"
PACKAGE_RECEIPT_NAME = "package-receipt.json"
BUNDLE_RECEIPT_NAME = "bundle-receipt.json"
UPLOAD_DIR_MAX_BYTES = 300 * 1024 * 1024  # 与 K4 `package` 同一上限（§5「上传」≤ 0.3 GB）

#: (包内路径, 仓库源路径)；源为 None 的是生成的空文件。
BUNDLE_MEMBERS: tuple[tuple[str, str | None], ...] = (
    # 仓库里的 `tools/` 是隐式命名空间包，没有 `__init__.py`；表 K 点名该成员，按空文件生成。
    ("code/tools/__init__.py", None),
    ("code/tools/eng_sft/__init__.py", "tools/eng_sft/__init__.py"),
    ("code/tools/eng_sft/cloud_runner.py", "tools/eng_sft/cloud_runner.py"),
    ("code/tools/eng_sft/train_lora.py", "tools/eng_sft/train_lora.py"),
    ("code/tools/eng_sft/prompt_v2.py", "tools/eng_sft/prompt_v2.py"),
    ("code/tools/eng_sft/parse.py", "tools/eng_sft/parse.py"),
    ("code/tools/eng_sft/receipts.py", "tools/eng_sft/receipts.py"),
    ("code/tools/eng_asset/__init__.py", "tools/eng_asset/__init__.py"),
    ("code/tools/eng_asset/receipts.py", "tools/eng_asset/receipts.py"),
    ("code/tools/requirements-eng-sft.txt", "tools/requirements-eng-sft.txt"),
)
#: 表 K 明令不进代码束的本地模块（评分/构建/抽查/回传校验只在本地）。
BUNDLE_EXCLUDED: tuple[str, ...] = (
    "tools/eng_sft/three_state.py",
    "tools/eng_sft/build_sft_data.py",
    "tools/eng_sft/evaluate.py",
    "tools/eng_sft/label_audit.py",
    "tools/eng_sft/verify_return.py",
)
#: 代码束中的 K4 冻结代码副本（AC-7 修订 1：须与冻结收据匹配）。
FROZEN_CODE_COPIES: dict[str, str] = {
    "code/tools/eng_sft/prompt_v2.py": "tools/eng_sft/prompt_v2.py",
    "code/tools/eng_sft/parse.py": "tools/eng_sft/parse.py",
}
REQUIREMENTS_MEMBER = "code/tools/requirements-eng-sft.txt"

# 表 K (e)：K4 数据包的 data/ 成员（全部要和冻结收据、dataset/eval manifest 三方一致）。
PACKAGE_DATA_FILES: tuple[str, ...] = (
    "train.jsonl",
    "smoke.jsonl",
    "select-eval.blind.jsonl",
    "eval.blind.jsonl",
)

# AC-12：签发日（2026-09-18）一次性判定为终态，本候选不含任何 SynDrone 成员。
TRANSFER_STATUS = "NOT_RUN(SFT_003_NOT_DONE)"

# --- 信封（账本 2026-09-18）------------------------------------------------------

STAGE_LIMITS: dict[str, int] = {"zero_shot": 2, "smoke": 2, "train": 4, "eval": 2}
TOTAL_LAUNCH_LIMIT = 8
CAP_GPU_HOURS = 8.0
CAP_USD = 6.0
BUDGET_RESERVE_HOURS = 0.1  # 守卫比绝对截止早 6 分钟停，留出回传与销毁实例的时间（AC-13 修订 1）
#: 流量预留的缺省估算（GB，进 = 实例下载，出 = 实例上传）：权重 4.4 + pip 依赖约 6 + 数据包 0.13 + 余量；
#: 回传约 0.3 + 日志 + 余量。只是估算，按报价的 $/TB 折成美元后从 6 美元里先扣掉。
DEFAULT_INBOUND_GB = 12.0
DEFAULT_OUTBOUND_GB = 1.0
#: 全流程耗时**估算**（小时，未实测；K3-P3）：装环境与下载 0.4 + 零样本 0.35 + 冒烟 0.15 + 三次训练与选层预测
#: 2.9 + A→B 等待 0.3 + 正式评估 0.35。只用于租机前判断报价是否明显不够，不作守卫依据。
ESTIMATED_NEED_HOURS = 4.45
#: 各阶段开始前的「最乐观」耗时估计（小时）：只在明显放不下时拒绝启动；进行中另有逐行/逐步检查与看门狗硬停。
STAGE_MIN_HOURS: dict[str, float] = {
    "setup": 0.02,
    "zero_shot": 0.10,
    "smoke": 0.03,
    "train": 0.15,
    "eval": 0.10,
}
WATCHDOG_POLL_SECONDS = 20.0
REQUIRED_GPU_SUBSTRING = "5090"
#: 5060 自检要用到、但自检信封只允许加装 peft/accelerate 的模块；缺了就拒绝，不自动安装（K3-P2）。
SELFCHECK_MODULES: tuple[str, ...] = (
    "torch", "torchvision", "transformers", "peft", "accelerate", "PIL", "tokenizers",
    "huggingface_hub", "safetensors",
)
SELFCHECK_TRANSPORT_NAME = "sft-selfcheck.tar"
SELFCHECK_RUN_LIMIT = 3
SELFCHECK_MAX_ROWS = 4
SELFCHECK_MAX_STEPS = 5

BASE_DIRNAME = "base"
BASE_COMPLETE_MARKER = ".complete"
TOKENIZER_FILES: tuple[str, ...] = ("tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt")

JOB_RECEIPT_NAME = "job-receipt.json"
LEDGER_NAME = "stage-ledger.json"
BUDGET_NAME = "budget.json"

PackageIncomplete = receipts.PackageIncomplete
FrozenSetMismatch = receipts.FrozenSetMismatch
ReturnHashMismatch = receipts._error("ReturnHashMismatch", "RETURN_HASH_MISMATCH")


class LaunchRefused(RuntimeError):
    """信封之外的动作（超额启动、非 5090、重复下载、版本漂移）：不启动，回到用户。"""


def _whole_number_between(value: Any, low: int, high: int | None) -> bool:
    """命令行数值边界：真整数（不收 bool）且落在 [low, high]；high 为 None 表示不设上界。"""
    return isinstance(value, int) and not isinstance(value, bool) and value >= low and (high is None or value <= high)


def _say(message: str) -> None:
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}Z] {message}", flush=True)


def _json_dump(path: Path, document: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)
    return path


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _dir_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in Path(path).rglob("*") if item.is_file())


def _files_under(root: Path) -> dict[str, Path]:
    root = Path(root)
    return {
        path.relative_to(root).as_posix(): path
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


# --- bundle（本地）-----------------------------------------------------------------


def _git(args: Sequence[str], repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=repo_root, check=False, capture_output=True, text=True
    )
    if completed.returncode != 0:
        raise receipts.FrozenFileDirty(
            f"git {' '.join(args)} 失败：{completed.stderr.strip()}", offending=list(args)
        )
    return completed.stdout.strip()


def _source_state(relative: str, repo_root: Path) -> dict[str, Any]:
    """代码束源文件必须已跟踪、工作区干净，且字节 = HEAD 下的 blob（不只看 status 为空）。"""
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative],
        cwd=repo_root, capture_output=True, text=True, check=False,
    ).returncode == 0
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", relative],
        cwd=repo_root, capture_output=True, text=True, check=False,
    ).stdout.strip()
    head_blob = subprocess.run(
        ["git", "rev-parse", f"HEAD:{relative}"],
        cwd=repo_root, capture_output=True, text=True, check=False,
    ).stdout.strip()
    work_blob = subprocess.run(
        ["git", "hash-object", relative],
        cwd=repo_root, capture_output=True, text=True, check=False,
    ).stdout.strip()
    clean = tracked and not status and bool(head_blob) and head_blob == work_blob
    return {"path": relative, "tracked": tracked, "status": status, "git_blob": head_blob, "clean": clean}


def run_bundle(*, repo_root: Path = PROJECT_ROOT, local_root: Path | None = None) -> dict[str, Any]:
    """表 K ⑥：生成 K3 代码束与 `upload/code-manifest.json`，写本地 `bundle` 收据。"""
    started = time.monotonic()
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    writer = receipts.ReceiptWriter(local_root=local, repo_root=root)
    manifest = receipts.InputManifest(repo_root=root)
    upload = local / UPLOAD_DIRNAME
    code_dir = upload / CODE_DIRNAME
    staging = upload / f"{CODE_DIRNAME}.staging"
    retired = upload / f"{CODE_DIRNAME}.old"
    code_manifest_path = upload / CODE_MANIFEST_NAME
    staged_manifest = upload / f"{CODE_MANIFEST_NAME}.staging"
    try:
        # 先守写出边界，再动任何目录。
        for path in (upload, code_dir, staging, retired, code_manifest_path, staged_manifest):
            receipts.assert_output_allowed(path, root)

        freeze_path = writer.receipts_dir / FREEZE_RECEIPT_NAME
        package_path = writer.receipts_dir / PACKAGE_RECEIPT_NAME
        upload_manifest_path = upload / UPLOAD_MANIFEST_NAME
        for required in (freeze_path, package_path, upload_manifest_path):
            if not required.is_file():
                raise PackageIncomplete(
                    f"缺 {required.name}：先完成 K4 的 freeze 与 package", offending=[required.name]
                )
        manifest.record(freeze_path, source="K4 冻结收据")
        manifest.record(package_path, source="K4 package 收据")
        freeze = _load_json(freeze_path)
        package_receipt = _load_json(package_path)
        upload_entry = manifest.record(upload_manifest_path, source="K4 数据包清单")
        if upload_entry.sha256 != package_receipt.get("upload_manifest_sha256"):
            raise PackageIncomplete(
                "upload/manifest.json 与 package 收据不符（K4 数据包被改动过）",
                offending=[{"package_receipt": package_receipt.get("upload_manifest_sha256"),
                            "actual": upload_entry.sha256}],
            )

        # AC-7 修订 1：代码束里的 prompt/parse 副本须与冻结收据匹配。
        frozen_set = freeze.get("frozen_set", {})
        drift = []
        for source in FROZEN_CODE_COPIES.values():
            actual = receipts.sha256_file(root / source)
            expected = frozen_set.get(source, {}).get("sha256")
            if actual != expected:
                drift.append({"path": source, "freeze": expected, "actual": actual})
        if drift:
            raise FrozenSetMismatch("冻结代码与冻结收据不符，不得打代码束", offending=drift)

        head = _git(["rev-parse", "HEAD"], root)
        states = [_source_state(source, root) for _, source in BUNDLE_MEMBERS if source is not None]
        dirty = [state for state in states if not state["clean"]]
        if dirty:
            raise receipts.FrozenFileDirty(
                "代码束源文件未跟踪/未提交/工作区不干净，先提交再打束", offending=dirty
            )
        blobs = {state["path"]: state["git_blob"] for state in states}

        if staging.exists():
            shutil.rmtree(staging)
        members: dict[str, dict[str, Any]] = {}
        for package_path_str, source in BUNDLE_MEMBERS:
            target = upload / package_path_str.replace(f"{CODE_DIRNAME}/", f"{staging.name}/", 1)
            target.parent.mkdir(parents=True, exist_ok=True)
            if source is None:
                target.write_bytes(b"")
                members[package_path_str] = {
                    "bytes": 0,
                    "sha256": receipts.sha256_file(target),
                    "source": None,
                    "generated": "empty package marker (tools/ is an implicit namespace package in the repo)",
                }
                continue
            entry = manifest.record(root / source, source="K3 代码束源文件")
            shutil.copyfile(root / source, target)
            copied = receipts.sha256_file(target)
            if copied != entry.sha256:
                raise PackageIncomplete(f"复制后字节不符：{source}", offending=[source])
            members[package_path_str] = {
                "bytes": entry.bytes,
                "sha256": entry.sha256,
                "source": source,
                "git_blob": blobs[source],
            }

        code_manifest = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/code-manifest/v1",
            "work_id": receipts.WORK_ID,
            "stop_point": "K3",
            "package_root": receipts.relative_to_root(upload, root),
            "source_head": head,
            "members": dict(sorted(members.items())),
            "member_count": len(members),
            "total_bytes": sum(value["bytes"] for value in members.values()),
            "excluded_modules": list(BUNDLE_EXCLUDED),
            "upload_manifest_sha256": upload_entry.sha256,
            "freeze_receipt_sha256": receipts.sha256_file(freeze_path),
            "frozen_code_copies": dict(FROZEN_CODE_COPIES),
            "prompt_template_sha256": prompt_v2.template_sha256(),
            "vocab_sha256": prompt_v2.vocab_sha256(train_lora.VOCAB),
            "g4_segment_sha256": prompt_v2.g4_segment_sha256(),
            "transfer_branch": {"status": TRANSFER_STATUS, "syndrone_members": 0},
            "contains_data": False,
        }
        _json_dump(staged_manifest, code_manifest)

        # 末次输入重算：打束期间读过的字节没变，才替换旧代码束。
        after = manifest.recompute()
        mismatches = manifest.diff(after)
        if mismatches:
            raise receipts.InputHashChanged("打束期间输入发生变化", offending=mismatches[:20])

        k4_before = receipts.sha256_file(upload_manifest_path)
        if retired.exists():
            shutil.rmtree(retired)
        if code_dir.exists():
            code_dir.rename(retired)
        staging.rename(code_dir)
        staged_manifest.replace(code_manifest_path)
        if retired.exists():
            shutil.rmtree(retired)
        if receipts.sha256_file(upload_manifest_path) != k4_before:
            raise PackageIncomplete("打束改动了 K4 数据包清单", offending=[UPLOAD_MANIFEST_NAME])
        upload_bytes = _dir_bytes(upload)
        if upload_bytes > UPLOAD_DIR_MAX_BYTES:
            raise PackageIncomplete(
                f"`upload/` 超过 0.3 GB：{upload_bytes}", offending=[{"bytes": upload_bytes}]
            )

        document = {
            "schema_version": f"{receipts.SCHEMA_PREFIX}/bundle-receipt/v1",
            "work_id": receipts.WORK_ID,
            "utc": receipts.utc_stamp(),
            "code_manifest_sha256": receipts.sha256_file(code_manifest_path),
            "upload_manifest_sha256": upload_entry.sha256,
            "source_head": head,
            "member_count": len(members),
            "upload_bytes": upload_bytes,
            "transfer_branch": TRANSFER_STATUS,
        }
        receipt_path = writer._write_json(writer.receipts_dir / BUNDLE_RECEIPT_NAME, document)
        writer.save_input_manifest("bundle", manifest, after, mismatches, successful=True)
        writer.write_run_receipt(
            "bundle",
            started=started,
            outputs=[receipts.output_record(code_manifest_path), receipts.output_record(receipt_path)],
            extra={"members": len(members), "upload_bytes": upload_bytes},
        )
        return document
    except receipts.EngSftError as exc:
        for leftover in (staging, staged_manifest):
            if leftover.is_dir():
                shutil.rmtree(leftover, ignore_errors=True)
            elif leftover.exists():
                leftover.unlink()
        writer.write_failure_receipt("bundle", exc.reason, exc.offending, message=str(exc))
        raise


# --- verify（云端 / 自检机）-------------------------------------------------------


def _check_members(package_root: Path, members: Mapping[str, Mapping[str, Any]], label: str,
                   only: Iterable[str] | None = None) -> int:
    problems: list[dict[str, Any]] = []
    names = sorted(members) if only is None else sorted(set(only) & set(members))
    for name in names:
        entry = members[name]
        path = package_root / name
        if not path.is_file():
            problems.append({"manifest": label, "path": name, "problem": "MISSING"})
            continue
        size = path.stat().st_size
        digest = receipts.sha256_file(path)
        if size != entry.get("bytes") or digest != entry.get("sha256"):
            problems.append({"manifest": label, "path": name, "problem": "HASH_OR_SIZE_MISMATCH",
                             "expected": entry.get("sha256"), "actual": digest})
        elif name.startswith("frames/") and Path(name).stem != digest:
            problems.append({"manifest": label, "path": name, "problem": "FRAME_NAME_NOT_SHA"})
    if problems:
        raise PackageIncomplete(f"{label} 成员缺失或字节不符", offending=problems[:20])
    return len(names)


def verify_package(
    package_root: Path,
    *,
    expect_code_dir: Path | None = None,
    subset: Iterable[str] | None = None,
) -> dict[str, Any]:
    """表 K ⑦：两份清单逐文件核对 + 冻结链核对。

    `subset` 只给自检用（只核对代码、清单与 smoke 相关成员，不读选层/评估文件）；云端作业
    一律全量。`expect_code_dir` 给出时还核对正在运行的模块就是包里那份代码。
    """
    root = Path(package_root)
    upload_manifest_path = root / UPLOAD_MANIFEST_NAME
    code_manifest_path = root / CODE_MANIFEST_NAME
    for required in (upload_manifest_path, code_manifest_path):
        if not required.is_file():
            raise PackageIncomplete(f"包根缺 {required.name}", offending=[required.name])
    data_manifest = _load_json(upload_manifest_path)
    code_manifest = _load_json(code_manifest_path)
    data_members = data_manifest.get("members", {})
    code_members = code_manifest.get("members", {})

    # 允许集合 = K4 成员 ∪ K3 成员 ∪ 两份清单本身；并集之外的文件一律拒绝（AC-7 修订 1）。
    allowed = set(data_members) | set(code_members) | {UPLOAD_MANIFEST_NAME, CODE_MANIFEST_NAME}
    on_disk = set(_files_under(root))
    extra = sorted(on_disk - allowed)
    if extra:
        hint = " ；含 __pycache__：请用 `python -B` 运行并删除这些目录" if any(
            "__pycache__" in name for name in extra) else ""
        raise PackageIncomplete(f"包内有清单之外的文件{hint}", offending=extra[:20])
    missing = sorted(allowed - on_disk)
    if subset is None and missing:
        raise PackageIncomplete("清单成员缺失", offending=missing[:20])

    subset_names = None if subset is None else set(subset)
    checked_data = _check_members(root, data_members, "manifest.json", subset_names)
    checked_code = _check_members(root, code_members, "code-manifest.json")

    # 两份清单互相绑定：代码束是为这一个数据包打的。
    upload_sha = receipts.sha256_file(upload_manifest_path)
    if code_manifest.get("upload_manifest_sha256") != upload_sha:
        raise FrozenSetMismatch(
            "code-manifest 绑定的数据包清单不是这一份",
            offending=[{"code_manifest": code_manifest.get("upload_manifest_sha256"), "actual": upload_sha}],
        )

    # 冻结链：jsonl/盲文件 SHA = manifest 记录 = 冻结收据副本；两份收据副本 = 清单记录。
    freeze_path = root / "manifests" / FREEZE_RECEIPT_NAME
    precheck_path = root / "manifests" / PRECHECK_RECEIPT_NAME
    freeze_sha = receipts.sha256_file(freeze_path)
    precheck_sha = receipts.sha256_file(precheck_path)
    freeze = _load_json(freeze_path)
    chain: list[dict[str, Any]] = []
    if data_manifest.get("freeze_receipt_sha256") != freeze_sha:
        chain.append({"item": "freeze_receipt", "manifest": data_manifest.get("freeze_receipt_sha256"),
                      "actual": freeze_sha})
    if code_manifest.get("freeze_receipt_sha256") != freeze_sha:
        chain.append({"item": "freeze_receipt@code-manifest"})
    if not (data_manifest.get("precheck_receipt_sha256") == precheck_sha == freeze.get("precheck_receipt_sha256")):
        chain.append({"item": "precheck_receipt", "actual": precheck_sha})
    dataset_manifest = _load_json(root / "manifests" / "dataset-manifest.json")
    eval_manifest = _load_json(root / "manifests" / "eval-manifest.json")
    for name in PACKAGE_DATA_FILES:
        member = data_members.get(f"data/{name}", {}).get("sha256")
        frozen = freeze.get("jsonl", {}).get(name, {}).get("sha256")
        declared = dataset_manifest.get("files", {}).get(name, {}).get("sha256")
        if not (member and member == frozen == declared):
            chain.append({"item": name, "manifest": member, "freeze": frozen, "dataset_manifest": declared})
    eval_declared = eval_manifest.get("files", {}).get("eval.blind.jsonl", {}).get("sha256")
    if eval_declared != data_members.get("data/eval.blind.jsonl", {}).get("sha256"):
        chain.append({"item": "eval.blind.jsonl@eval-manifest"})
    for member_path, frozen_path in FROZEN_CODE_COPIES.items():
        member = code_members.get(member_path, {}).get("sha256")
        frozen = freeze.get("frozen_set", {}).get(frozen_path, {}).get("sha256")
        if member != frozen:
            chain.append({"item": frozen_path, "code_manifest": member, "freeze": frozen})
    if code_manifest.get("prompt_template_sha256") != prompt_v2.template_sha256():
        chain.append({"item": "prompt_template_sha256"})
    if code_manifest.get("transfer_branch", {}).get("status") != TRANSFER_STATUS:
        chain.append({"item": "transfer_branch"})
    if chain:
        raise FrozenSetMismatch("冻结链不符，不运行", offending=chain)

    if expect_code_dir is not None:
        code_root = Path(expect_code_dir).resolve()
        running = {
            "prompt_v2": Path(prompt_v2.__file__).resolve(),
            "parse": Path(parse.__file__).resolve(),
            "train_lora": Path(train_lora.__file__).resolve(),
            "cloud_runner": Path(__file__).resolve(),
        }
        outside = {name: str(path) for name, path in running.items() if code_root not in path.parents}
        if outside:
            raise FrozenSetMismatch(
                "正在运行的模块不是包内代码（PYTHONPATH 须指向包根下的 code/）", offending=[outside]
            )

    return {
        "upload_manifest_sha256": upload_sha,
        "code_manifest_sha256": receipts.sha256_file(code_manifest_path),
        "freeze_receipt_sha256": freeze_sha,
        "precheck_receipt_sha256": precheck_sha,
        "data_members_checked": checked_data,
        "code_members_checked": checked_code,
        "full": subset is None,
        "frozen_chain": "OK",
        "prompt_template_sha256": prompt_v2.template_sha256(),
        "vocab_sha256": prompt_v2.vocab_sha256(train_lora.VOCAB),
        "transfer_branch": TRANSFER_STATUS,
    }


# --- 启动账与预算守卫（实例上的持久状态）----------------------------------------------


class StageLedger:
    """实例上的启动账：每次阶段启动先记账，失败/中断也算一次；超额即拒绝。"""

    def __init__(self, work: Path) -> None:
        self.path = Path(work) / LEDGER_NAME
        if self.path.is_file():
            self.document = _load_json(self.path)
        else:
            self.document = {
                "schema_version": f"{receipts.SCHEMA_PREFIX}/stage-ledger/v1",
                "work_id": receipts.WORK_ID,
                "limits": {"per_stage": STAGE_LIMITS, "total": TOTAL_LAUNCH_LIMIT},
                "entries": [],
                "base_download": None,
            }

    def save(self) -> None:
        _json_dump(self.path, self.document)

    @property
    def entries(self) -> list[dict[str, Any]]:
        return self.document["entries"]

    def counts(self) -> dict[str, int]:
        counts = {kind: 0 for kind in STAGE_LIMITS}
        for entry in self.entries:
            counts[entry["kind"]] = counts.get(entry["kind"], 0) + 1
        return counts

    def start(self, kind: str, *, job_id: str, label: str) -> int:
        if kind not in STAGE_LIMITS:
            raise ValueError(f"阶段不在闭集内：{kind}")
        counts = self.counts()
        total = sum(counts.values())
        if counts[kind] >= STAGE_LIMITS[kind] or total >= TOTAL_LAUNCH_LIMIT:
            raise LaunchRefused(
                f"启动次数已达信封上限：{kind} {counts[kind]}/{STAGE_LIMITS[kind]}，总 {total}/{TOTAL_LAUNCH_LIMIT}"
                "；不再启动，回到用户"
            )
        self.entries.append(
            {
                "kind": kind,
                "label": label,
                "job_id": job_id,
                "attempt": counts[kind] + 1,
                "launch_number": total + 1,
                "started_utc": receipts.utc_stamp(),
                "status": "started",
            }
        )
        self.save()
        return len(self.entries) - 1

    def finish(self, index: int, status: str, **extra: Any) -> dict[str, Any]:
        entry = self.entries[index]
        entry["status"] = status
        entry["ended_utc"] = receipts.utc_stamp()
        entry.update(extra)
        self.save()
        return entry

    def succeeded(self, job_id: str, label: str) -> dict[str, Any] | None:
        for entry in reversed(self.entries):
            if entry["job_id"] == job_id and entry["label"] == label and entry["status"] == "succeeded":
                return entry
        return None

    def snapshot(self) -> dict[str, Any]:
        return {
            "counts": self.counts(),
            "total": sum(self.counts().values()),
            "limits": {"per_stage": STAGE_LIMITS, "total": TOTAL_LAUNCH_LIMIT},
            "entries": [dict(entry) for entry in self.entries],
            "base_download": self.document.get("base_download"),
        }


def _parse_utc(stamp: str) -> datetime:
    return datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def budget_plan(
    *,
    gpu_usd_per_hour: float,
    storage_usd_per_hour: float,
    inbound_usd_per_tb: float,
    outbound_usd_per_tb: float,
    inbound_gb: float = DEFAULT_INBOUND_GB,
    outbound_gb: float = DEFAULT_OUTBOUND_GB,
    cap_gpu_hours: float = CAP_GPU_HOURS,
    cap_usd: float = CAP_USD,
) -> dict[str, Any]:
    """按报价的**全部**费用项算出本次实例最多能开多久（AC-13 修订 1）。

    6 美元里先扣掉流量（进/出 GB × $/TB），剩下的按「GPU 小时价 + 存储小时价」折成小时，再与 8 GPU·h
    取小。四个费率都必须由用户从报价上读出填入（没有就填 0 并在报价上确认确实免费）；费用不明就不租该报价。
    结果是保守计时下的上限，不是供应商的精确账单。
    """
    rates = {
        "gpu_usd_per_hour": gpu_usd_per_hour,
        "storage_usd_per_hour": storage_usd_per_hour,
        "inbound_usd_per_tb": inbound_usd_per_tb,
        "outbound_usd_per_tb": outbound_usd_per_tb,
    }
    if any(value is None or value < 0 for value in rates.values()):
        raise LaunchRefused(f"四项费率都必须给出且 ≥ 0：{rates}；费用不明就不租该报价")
    if gpu_usd_per_hour <= 0:
        raise LaunchRefused("GPU 小时价须 > 0")
    if cap_gpu_hours > CAP_GPU_HOURS or cap_usd > CAP_USD:
        raise LaunchRefused("上限不得超过账本信封（8 GPU·h、6 美元）")
    transfer_usd = inbound_gb / 1000.0 * inbound_usd_per_tb + outbound_gb / 1000.0 * outbound_usd_per_tb
    hourly_usd = gpu_usd_per_hour + storage_usd_per_hour
    usd_for_time = cap_usd - transfer_usd
    if usd_for_time <= 0:
        raise LaunchRefused(f"流量预留 {transfer_usd:.2f} 美元已用尽 6 美元，不租该报价")
    usd_hours = usd_for_time / hourly_usd
    absolute_cap = min(cap_gpu_hours, usd_hours)
    guard_hours = absolute_cap - BUDGET_RESERVE_HOURS
    return {
        "rates": rates,
        "transfer_gb": {"inbound": inbound_gb, "outbound": outbound_gb},
        "transfer_reserve_usd": round(transfer_usd, 4),
        "hourly_usd": hourly_usd,
        "cap_gpu_hours": cap_gpu_hours,
        "cap_usd": cap_usd,
        "usd_limited_hours": round(usd_hours, 4),
        "absolute_cap_hours": round(absolute_cap, 4),
        "binding_cap": "gpu_hours" if cap_gpu_hours <= usd_hours else "usd",
        "guard_stop_hours": round(guard_hours, 4),
        "reserve_hours": BUDGET_RESERVE_HOURS,
        "estimated_need_hours": ESTIMATED_NEED_HOURS,
        "estimate_fits": guard_hours >= ESTIMATED_NEED_HOURS,
        "note": "保守计时的上限，不是供应商精确计费；运行器不会销毁实例，截止前由用户在控制台销毁。",
    }


def _stamp(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _both_clocks(moment: datetime) -> str:
    local = moment.astimezone()
    return f"{moment.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC（本机时区 {local.strftime('%Y-%m-%d %H:%M %Z')}）"


def init_budget(
    work: Path,
    *,
    gpu_usd_per_hour: float,
    storage_usd_per_hour: float,
    inbound_usd_per_tb: float,
    outbound_usd_per_tb: float,
    minutes_since_start: float = 0.0,
    inbound_gb: float = DEFAULT_INBOUND_GB,
    outbound_gb: float = DEFAULT_OUTBOUND_GB,
    cap_gpu_hours: float = CAP_GPU_HOURS,
    cap_usd: float = CAP_USD,
    now: datetime | None = None,
) -> dict[str, Any]:
    """记下实例开机时刻与报价费率，写出**绝对截止时刻**；只写一次（重写等于把计时清零，不允许）。"""
    path = Path(work) / BUDGET_NAME
    if path.exists():
        raise LaunchRefused(f"{path} 已存在：预算计时只初始化一次")
    plan = budget_plan(
        gpu_usd_per_hour=gpu_usd_per_hour, storage_usd_per_hour=storage_usd_per_hour,
        inbound_usd_per_tb=inbound_usd_per_tb, outbound_usd_per_tb=outbound_usd_per_tb,
        inbound_gb=inbound_gb, outbound_gb=outbound_gb, cap_gpu_hours=cap_gpu_hours, cap_usd=cap_usd,
    )
    if minutes_since_start < 0:
        raise ValueError("已开机分钟数须 ≥ 0")
    current = now or datetime.now(timezone.utc)
    started = current - timedelta(minutes=float(minutes_since_start))
    deadline = started + timedelta(hours=plan["absolute_cap_hours"])
    guard_stop = started + timedelta(hours=plan["guard_stop_hours"])
    document = {
        "schema_version": f"{receipts.SCHEMA_PREFIX}/budget/v2",
        "work_id": receipts.WORK_ID,
        "instance_started_utc": _stamp(started),
        "initialised_utc": _stamp(current),
        **plan,
        "effective_cap_hours": plan["absolute_cap_hours"],
        "destroy_deadline_utc": _stamp(deadline),
        "guard_stop_utc": _stamp(guard_stop),
        "destroy_deadline_readable": _both_clocks(deadline),
    }
    _json_dump(path, document)
    return document


class BudgetGuard:
    """计算层守卫：先触及 8 GPU·h 或 6 美元（含存储与流量预留）即停。

    它只能停本进程，**不能替用户销毁实例、也不能终止实例计费**；实例在 `destroy_deadline_utc`
    之前由用户在控制台销毁（AC-13 修订 1）。
    """

    def __init__(self, work: Path, *, clock: Callable[[], datetime] | None = None) -> None:
        path = Path(work) / BUDGET_NAME
        if not path.is_file():
            raise LaunchRefused("缺 budget.json：登录实例后先运行 budget-init")
        self.document = _load_json(path)
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.started = _parse_utc(self.document["instance_started_utc"])

    def elapsed_hours(self) -> float:
        return (self.clock() - self.started).total_seconds() / 3600.0

    def limit_hours(self) -> float:
        return float(self.document["effective_cap_hours"]) - float(self.document["reserve_hours"])

    def remaining_hours(self) -> float:
        return self.limit_hours() - self.elapsed_hours()

    def should_stop(self) -> bool:
        return self.remaining_hours() <= 0.0

    def require(self, kind: str) -> None:
        need = STAGE_MIN_HOURS[kind]
        if self.remaining_hours() < need:
            raise train_lora.BudgetStop(
                f"预算守卫：剩余 {self.remaining_hours():.2f} h < 启动 {kind} 所需的最少 {need:.2f} h"
            )

    def snapshot(self) -> dict[str, Any]:
        elapsed = self.elapsed_hours()
        return {
            "instance_started_utc": self.document["instance_started_utc"],
            "elapsed_hours": round(elapsed, 4),
            "estimated_usd": round(elapsed * float(self.document["hourly_usd"])
                                   + float(self.document.get("transfer_reserve_usd", 0.0)), 4),
            "effective_cap_hours": self.document["effective_cap_hours"],
            "remaining_hours": round(self.remaining_hours(), 4),
            "hourly_usd": self.document["hourly_usd"],
            "destroy_deadline_utc": self.document.get("destroy_deadline_utc"),
            "note": "保守计时估算，不是供应商账单",
        }


class Watchdog:
    """看门狗：守卫时刻一到就结束本进程，不依赖下一次逐行/逐步检查（K3-P1）。

    单步卡住、下载或网络挂起时，后台线程照样按时触发：先尽力写下停机记录，再 `os._exit(3)`。
    它只结束运行器，实例仍在计费；销毁实例是用户在截止时刻前的动作。
    """

    def __init__(self, guard: BudgetGuard, *, on_fire: Callable[[], None],
                 poll_seconds: float = WATCHDOG_POLL_SECONDS) -> None:
        self.guard = guard
        self.on_fire = on_fire
        self.poll_seconds = poll_seconds
        self.fired = False
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="budget-watchdog", daemon=True)

    def _run(self) -> None:
        while not self._stop.is_set():
            remaining = self.guard.remaining_hours() * 3600.0
            if remaining <= 0:
                self.fired = True
                self.on_fire()
                return
            self._stop.wait(max(0.05, min(self.poll_seconds, remaining)))

    def start(self) -> "Watchdog":
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive() and self._thread is not threading.current_thread():
            self._thread.join(timeout=5)


def _hard_exit_after(job: "Job", ledger: StageLedger, guard: BudgetGuard) -> Callable[[], None]:
    """看门狗触发时的动作：尽力记账与写收据，然后立刻结束进程（退出码 3）。"""

    def fire() -> None:
        try:
            for index, entry in enumerate(ledger.entries):
                if entry.get("status") == "started":
                    ledger.finish(index, "stopped_budget_watchdog")
            _json_dump(job.path("watchdog-stop.json"), {"budget": guard.snapshot(), "utc": receipts.utc_stamp()})
            job.finalize(complete=False, ledger=ledger, guard=guard, outcome="stopped_budget_watchdog")
        except BaseException:  # noqa: BLE001 - 记录失败也必须停
            pass
        print(f"预算看门狗：到达守卫时刻，运行器已停。请下载 {job.dir} 并在 "
              f"{guard.document.get('destroy_deadline_readable')} 之前销毁实例。", file=sys.stderr, flush=True)
        os._exit(3)

    return fire


# --- 环境、版本与作业目录 ------------------------------------------------------------


def requirement_pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        name, _, version = line.partition("==")
        pins[name.strip()] = version.strip()
    return pins


def check_pins(pins: Mapping[str, str]) -> dict[str, Any]:
    installed: dict[str, str | None] = {}
    drift: list[dict[str, Any]] = []
    for name, version in sorted(pins.items()):
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual = None
        installed[name] = actual
        if actual != version:
            drift.append({"package": name, "pinned": version, "installed": actual})
    return {"pinned": dict(pins), "installed": installed, "drift": drift}


def environment_record() -> dict[str, Any]:
    record: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "executable": sys.executable,
    }
    try:
        import torch  # noqa: PLC0415

        record["torch"] = torch.__version__
        record["torch_cuda"] = torch.version.cuda
        record["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            record["gpu_count"] = torch.cuda.device_count()
            record["gpu_name"] = torch.cuda.get_device_name(0)
            record["gpu_capability"] = list(torch.cuda.get_device_capability(0))
            record["gpu_total_memory_bytes"] = int(torch.cuda.get_device_properties(0).total_memory)
    except ImportError:
        record["torch"] = None
    try:
        smi = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=15, check=False,
        )
        if smi.returncode == 0:
            record["nvidia_smi"] = smi.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return record


def require_envelope_gpu(env: Mapping[str, Any]) -> None:
    """信封设备 = 云端**单张** RTX 5090；其他卡或多卡都在信封之外。"""
    if not env.get("cuda_available"):
        raise LaunchRefused("没有可用的 CUDA 设备")
    if env.get("gpu_count") != 1:
        raise LaunchRefused(f"信封是单卡，实例有 {env.get('gpu_count')} 张 GPU")
    if REQUIRED_GPU_SUBSTRING not in str(env.get("gpu_name", "")):
        raise LaunchRefused(f"信封设备是 RTX 5090，实例是 {env.get('gpu_name')}")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return train_lora.read_jsonl(path)


class Job:
    """一次作业的回传目录 `returned/<job_id>/` 与其 `job-receipt.json`（表 I）。"""

    def __init__(self, work: Path, kind: str, freeze_sha: str, *, resume: str | None = None) -> None:
        self.kind = kind
        if resume:
            self.id = resume
            self.dir = Path(work) / "returned" / resume
            receipt = self.dir / JOB_RECEIPT_NAME
            if not receipt.is_file():
                raise LaunchRefused(f"找不到要续跑的作业：{receipt}")
            self.receipt = _load_json(receipt)
            if self.receipt.get("job_kind") != kind:
                raise LaunchRefused(f"{resume} 不是作业 {kind}")
        else:
            # `job_id = sft-<utc>-<冻结收据 SHA 前 8 位>`（表 I）；同一秒内重名就等下一秒。
            for _ in range(3):
                self.id = f"sft-{receipts.utc_stamp()}-{freeze_sha[:8]}"
                self.dir = Path(work) / "returned" / self.id
                if not self.dir.exists():
                    break
                time.sleep(1.05)
            self.dir.mkdir(parents=True, exist_ok=False)
            self.receipt = {
                "schema_version": f"{receipts.SCHEMA_PREFIX}/job-receipt/v1",
                "work_id": receipts.WORK_ID,
                "job_id": self.id,
                "job_kind": kind,
                "started_utc": receipts.utc_stamp(),
                "complete": False,
                "stages": {},
                "cost_usd": None,
                "cost_note": "费用由用户按 vast.ai 账单回填（报告与云端运行代录）",
                "transfer_branch": TRANSFER_STATUS,
            }
        self.writer = receipts.ReceiptWriter(local_root=self.dir, repo_root=self.dir)

    def path(self, *parts: str) -> Path:
        return self.dir.joinpath(*parts)

    def record(self, key: str, value: Any) -> None:
        self.receipt[key] = value
        self.save()

    def stage_done(self, label: str) -> bool:
        return self.receipt["stages"].get(label, {}).get("status") == "succeeded"

    def save(self, *, ledger: StageLedger | None = None, guard: BudgetGuard | None = None) -> Path:
        self.receipt["updated_utc"] = receipts.utc_stamp()
        if ledger is not None:
            self.receipt["launches"] = ledger.snapshot()
        if guard is not None:
            self.receipt["budget"] = guard.snapshot()
        return _json_dump(self.path(JOB_RECEIPT_NAME), self.receipt)

    def finalize(self, *, complete: bool, ledger: StageLedger | None, guard: BudgetGuard | None,
                 outcome: str) -> Path:
        """写最终收据：回传目录里除收据自身外的每个文件都列出字节与 SHA。"""
        self.receipt["complete"] = complete
        self.receipt["outcome"] = outcome
        self.receipt["ended_utc"] = receipts.utc_stamp()
        artifacts = {}
        for name, path in _files_under(self.dir).items():
            if name == JOB_RECEIPT_NAME or name.endswith(".tmp") or name.endswith(".partial"):
                continue
            artifacts[name] = {"bytes": path.stat().st_size, "sha256": receipts.sha256_file(path)}
        self.receipt["artifacts"] = artifacts
        return self.save(ledger=ledger, guard=guard)


# --- 引擎：真实 torch 实现（测试注入替身）-----------------------------------------------


@dataclass
class ModelSource:
    """base 从哪里来：云端 = 实例上 `base/` 目录；自检 = 本机已有的同版缓存或目录。"""

    location: str
    revision: str | None
    local_files_only: bool = True


class TorchEngine:
    """把 `train_lora` 的模型函数接到作业编排上；每个阶段独立加载、结束即释放显存。"""

    def __init__(self, *, micro_batch: int = 8, device: str = "cuda") -> None:
        if not _whole_number_between(micro_batch, 1, None):
            raise LaunchRefused(f"micro-batch 须是 ≥ 1 的整数（收到 {micro_batch!r}）")
        self.micro_batch = micro_batch
        self.device = device

    # 环境 ---------------------------------------------------------------
    def environment(self) -> dict[str, Any]:
        return environment_record()

    def missing_modules(self) -> list[str]:
        """自检所需模块里本机缺哪些（只查不装，K3-P2）。"""
        return [name for name in SELFCHECK_MODULES if importlib.util.find_spec(name) is None]

    def locate_model(self, source: ModelSource) -> dict[str, Any]:
        """确认同版权重已在本机（目录或 HF 缓存），**不联网、不下载**；找不到即拒绝。"""
        root = Path(source.location)
        if root.is_dir():
            missing = [name for name in ("config.json", "tokenizer.json") if not (root / name).is_file()]
            if missing or not list(root.glob("*.safetensors")):
                raise LaunchRefused(f"权重目录不完整：{root}（缺 {missing or '*.safetensors'}）")
            return {"location": str(root), "kind": "directory"}
        try:
            from huggingface_hub import hf_hub_download  # noqa: PLC0415

            config = hf_hub_download(source.location, "config.json", revision=source.revision,
                                     local_files_only=True)
        except Exception as exc:  # noqa: BLE001 - 任何找不到都按「本机没有」拒绝
            raise LaunchRefused(
                f"本机 HF 缓存里没有 {source.location}@{source.revision}（{type(exc).__name__}）；"
                "自检信封不允许下载权重，请用 --model 指向已有的权重目录"
            ) from exc
        return {"location": source.location, "revision": source.revision, "kind": "hf-cache",
                "config": str(config)}

    def ensure_base(self, work: Path, ledger: StageLedger) -> ModelSource:
        """base 权重下载一次（账本 2026-09-18）；已完成就直接用，不重新下载。"""
        base = Path(work) / BASE_DIRNAME
        marker = base / BASE_COMPLETE_MARKER
        if marker.is_file():
            return ModelSource(str(base), None)
        previous = ledger.document.get("base_download")
        if previous and previous.get("completed_utc"):
            raise LaunchRefused("base 权重已完整下载过一次但目录已不完整；重新下载超出信封，回到用户")
        from huggingface_hub import snapshot_download  # noqa: PLC0415

        ledger.document["base_download"] = {
            "repo": train_lora.BASE_REPO,
            "revision": train_lora.BASE_REVISION,
            "started_utc": receipts.utc_stamp(),
            "completed_utc": None,
        }
        ledger.save()
        _say(f"下载 base 权重 {train_lora.BASE_REPO}@{train_lora.BASE_REVISION[:12]}（约 4.4 GB，只下载这一次）")
        snapshot_download(
            repo_id=train_lora.BASE_REPO, revision=train_lora.BASE_REVISION, local_dir=str(base)
        )
        marker.write_text(train_lora.BASE_REVISION + "\n", encoding="utf-8")
        ledger.document["base_download"]["completed_utc"] = receipts.utc_stamp()
        ledger.save()
        return ModelSource(str(base), None)

    def base_files(self, source: ModelSource) -> dict[str, Any]:
        root = Path(source.location)
        if not root.is_dir():
            return {"location": source.location, "revision": source.revision, "files": "hf-cache"}
        files = {
            name: {"bytes": path.stat().st_size, "sha256": receipts.sha256_file(path)}
            for name, path in _files_under(root).items()
            if not name.startswith(".cache/") and name != BASE_COMPLETE_MARKER
        }
        return {"location": str(root), "revision": train_lora.BASE_REVISION, "files": files}

    def tokenizer_files(self, source: ModelSource) -> dict[str, Path]:
        root = Path(source.location)
        if root.is_dir():
            return {name: root / name for name in TOKENIZER_FILES}
        from huggingface_hub import hf_hub_download  # noqa: PLC0415

        return {
            name: Path(hf_hub_download(source.location, name, revision=source.revision,
                                       local_files_only=source.local_files_only))
            for name in TOKENIZER_FILES
        }

    def encoder(self, tokenizer_json: Path) -> tuple[Callable[[str], int], dict[str, Any]]:
        import tokenizers  # noqa: PLC0415
        from tokenizers import Tokenizer  # noqa: PLC0415

        tokenizer = Tokenizer.from_file(str(tokenizer_json))

        def encode(text: str) -> int:
            return len(tokenizer.encode(text, add_special_tokens=False).ids)

        return encode, {"library": "tokenizers", "version": tokenizers.__version__}

    def check_grids(self, source: ModelSource, package_root: Path, frame_paths: Sequence[str],
                    should_stop: Callable[[], bool] | None = None) -> dict[str, Any]:
        """任何推理前，对本次要用的每张帧断言 Unity 网格 [1, 30, 40]。"""
        from transformers import AutoProcessor  # noqa: PLC0415

        kwargs: dict[str, Any] = {"local_files_only": source.local_files_only}
        if source.revision:
            kwargs["revision"] = source.revision
        processor = AutoProcessor.from_pretrained(source.location, **kwargs)
        for position, frame_path in enumerate(frame_paths):
            if should_stop is not None and should_stop():
                raise train_lora.BudgetStop(f"预算守卫：网格预检第 {position} 张前停止")
            image = train_lora.load_image(Path(package_root) / frame_path)
            output = processor.image_processor(
                images=[image], size=dict(prompt_v2.PROCESSOR_SIZE), return_tensors="pt"
            )
            grid = [int(value) for value in output["image_grid_thw"][0].tolist()]
            train_lora.check_grid(grid, train_lora.UNITY_DATASET, row_id=frame_path)
            if (position + 1) % 500 == 0:
                _say(f"  网格预检 {position + 1}/{len(frame_paths)}")
        return {
            train_lora.UNITY_DATASET: {
                "expected": list(train_lora.EXPECTED_GRID[train_lora.UNITY_DATASET]),
                "checked": len(frame_paths),
                "mismatches": 0,
            }
        }

    def _release(self) -> None:
        """调用方先把模型引用置空，这里再回收并清显存缓存，避免下一阶段叠加占用。"""
        gc.collect()
        try:
            import torch  # noqa: PLC0415

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:  # pragma: no cover
            pass

    def predict(self, source: ModelSource, rows: Sequence[Mapping[str, Any]], package_root: Path,
                out_path: Path, *, adapter_dir: Path | None = None,
                should_stop: Callable[[], bool] | None = None) -> dict[str, Any]:
        loaded = train_lora.load_model(
            source.location, revision=source.revision, device=self.device,
            adapter_dir=adapter_dir, local_files_only=source.local_files_only,
        )
        try:
            result = train_lora.predict_rows(
                loaded, rows, package_root, out_path, should_stop=should_stop,
                progress=_progress("预测"),
            )
            result["model_id"] = loaded.model_id
            return result
        finally:
            loaded = None
            self._release()

    def train(self, source: ModelSource, samples: Sequence[Mapping[str, Any]], package_root: Path,
              out_dir: Path, *, lr: float, epochs: int, expand: bool, max_steps: int | None,
              predict_rows: Sequence[Mapping[str, Any]], predict_out: Path,
              should_stop: Callable[[], bool] | None = None,
              micro_batch: int | None = None) -> dict[str, Any]:
        """训练一次 → 存 adapter → 用内存中的同一 adapter 预测给定盲行。"""
        loaded = train_lora.load_model(
            source.location, revision=source.revision, device=self.device, trainable=True,
            local_files_only=source.local_files_only,
        )
        try:
            modules = train_lora.lora_module_count(loaded)
            if modules["lora_modules"] != modules["expected"] or modules["visual_lora_modules"]:
                raise receipts.FrozenSetMismatch("LoRA 挂载位置与表 H 不符", offending=[modules])
            result = train_lora.train_candidate(
                loaded, samples, package_root, lr=lr, epochs=epochs, out_dir=out_dir,
                micro_batch=micro_batch or self.micro_batch, expand=expand, max_steps=max_steps,
                should_stop=should_stop, log=_step_logger(),
            )
            result["lora"] = modules
            loaded.model_id = result["adapter_sha256"]
            result["predictions"] = train_lora.predict_rows(
                loaded, predict_rows, package_root, predict_out, should_stop=should_stop,
                progress=_progress("预测"),
            )
            return result
        finally:
            loaded = None
            self._release()


def _progress(label: str) -> Callable[[int, int], None]:
    def report(done: int, total: int) -> None:
        if done == total or done % 50 == 0:
            _say(f"  {label} {done}/{total}")

    return report


def _step_logger() -> Callable[[dict[str, Any]], None]:
    def report(entry: dict[str, Any]) -> None:
        if entry["step"] == 1 or entry["step"] % 20 == 0:
            _say(f"  step {entry['step']} loss {entry['loss']:.4f} lr {entry['lr']:.2e} "
                 f"{entry['elapsed_s']:.0f}s")

    return report


# --- 作业编排 ----------------------------------------------------------------------


def _frame_paths(package_root: Path, names: Sequence[str]) -> list[str]:
    seen: dict[str, None] = {}
    for name in names:
        for row in _read_jsonl(Path(package_root) / "data" / name):
            seen.setdefault(row["frame_path"], None)
    return list(seen)


def tokenizer_recheck(engine: Any, source: ModelSource, package_root: Path,
                      files: Sequence[str] = train_lora.RECOUNT_FILES) -> dict[str, Any]:
    """AC-8：同版 tokenizer 文件 SHA = 本地预检收据；train+smoke 的 gold 重算 = 收据。"""
    precheck = _load_json(Path(package_root) / "manifests" / PRECHECK_RECEIPT_NAME)
    paths = engine.tokenizer_files(source)
    expected = precheck.get("tokenizer", {}).get("files", {})
    file_problems = []
    shas = {}
    for name, path in sorted(paths.items()):
        digest = receipts.sha256_file(path)
        shas[name] = digest
        if expected.get(name, {}).get("sha256") != digest:
            file_problems.append({"file": name, "precheck": expected.get(name, {}).get("sha256"),
                                  "cloud": digest})
    if file_problems:
        raise receipts.TokenizerMismatch("tokenizer 文件与本地预检收据不是同一版", offending=file_problems)
    encode, library = engine.encoder(paths["tokenizer.json"])
    recounts = {name: train_lora.recount_gold_tokens(Path(package_root) / "data" / name, encode)
                for name in files}
    result = train_lora.compare_recount(precheck, recounts)
    result["tokenizer_files_sha256"] = shas
    result["library"] = library
    return result


def _run_stage(job: Job, ledger: StageLedger, guard: BudgetGuard | None, kind: str, label: str,
               action: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """一个阶段：预算预检 → 记账启动 → 执行 → 记账结束；异常一律记账后再抛。"""
    if guard is not None:
        guard.require(kind)
    index = ledger.start(kind, job_id=job.id, label=label)
    began = time.monotonic()
    _say(f"阶段 {label}（{kind} 第 {ledger.entries[index]['attempt']} 次，总第 {ledger.entries[index]['launch_number']} 次）开始")
    try:
        result = action()
    except train_lora.BudgetStop as exc:
        ledger.finish(index, "stopped_budget", elapsed_s=round(time.monotonic() - began, 1), message=str(exc))
        job.receipt["stages"][label] = {"kind": kind, "status": "stopped_budget", "message": str(exc)}
        job.writer.write_run_receipt("stop", started=began, outputs=[],
                                     extra={"stage": label, "budget_guard": guard.snapshot() if guard else None})
        exc.receipt_written = True
        raise
    except receipts.EngSftError as exc:
        ledger.finish(index, f"failed:{exc.reason}", elapsed_s=round(time.monotonic() - began, 1))
        job.receipt["stages"][label] = {"kind": kind, "status": f"failed:{exc.reason}"}
        job.writer.write_failure_receipt(f"job-{job.kind.lower()}-{label}", exc.reason, exc.offending, message=str(exc))
        exc.receipt_written = True
        raise
    except BaseException as exc:
        ledger.finish(index, "failed:EXCEPTION", elapsed_s=round(time.monotonic() - began, 1),
                      message=f"{type(exc).__name__}: {exc}"[:500])
        job.receipt["stages"][label] = {"kind": kind, "status": "failed:EXCEPTION",
                                        "message": f"{type(exc).__name__}: {exc}"[:500]}
        raise
    elapsed = round(time.monotonic() - began, 1)
    ledger.finish(index, "succeeded", elapsed_s=elapsed)
    result = {"kind": kind, "status": "succeeded", "elapsed_s": elapsed,
              "attempt": ledger.entries[index]["attempt"], **result}
    job.receipt["stages"][label] = result
    job.save(ledger=ledger, guard=guard)
    _say(f"阶段 {label} 完成（{elapsed:.0f} s）")
    return result


PACKAGE_IDENTITY_KEYS: tuple[str, ...] = (
    "upload_manifest_sha256",
    "code_manifest_sha256",
    "freeze_receipt_sha256",
    "precheck_receipt_sha256",
    "prompt_template_sha256",
    "vocab_sha256",
)


def package_identity(verify: Mapping[str, Any] | None) -> dict[str, Any]:
    """全包校验结果里标识「哪一份 K4 数据包 + K3 代码束」的字段。"""
    return {key: (verify or {}).get(key) for key in PACKAGE_IDENTITY_KEYS}


def require_same_package(recorded: Mapping[str, Any] | None, current: Mapping[str, Any], *, what: str) -> None:
    """续跑与 A→B（C1-K3-1）：已记录的包身份须等于当前全包校验结果；缺字段也拒绝。

    在改写任何旧收据、跳过任何已完成阶段、消费作业 A 的 adapter 之前调用；不一致只拒绝，不改写旧身份。
    """
    expected, actual = package_identity(recorded), package_identity(current)
    if any(value is None for value in expected.values()) or expected != actual:
        differ = [key for key in PACKAGE_IDENTITY_KEYS if expected[key] != actual[key] or expected[key] is None]
        raise LaunchRefused(f"{what}：当前包与已记录的包身份不同（{differ}）；不续用旧结果，回到实现角色")


def _prepare(package_root: Path, work: Path, engine: Any, *, kind: str, resume: str | None,
             clock: Callable[[], datetime] | None, code_location_check: bool = True,
             expected_package: tuple[str, Mapping[str, Any] | None] | None = None,
             ) -> tuple[Job, StageLedger, BudgetGuard, dict[str, Any], dict[str, Any]]:
    """作业前置：全包校验、预算守卫、单张 5090、钉版本——都是信封条件，没有任何绕过开关（AC-13 修订 1）。

    `expected_package`（作业 B 传入作业 A 的记录）与续跑时旧收据的包身份、环境、已装版本都在建目录或写收据
    之前核对（C1-K3-1）；续跑不改写首跑记录，只追加一条 `resumes`。
    """
    package_root = Path(package_root)
    work = Path(work)
    verify = verify_package(
        package_root, expect_code_dir=_code_dir(package_root) if code_location_check else None)
    guard = BudgetGuard(work, clock=clock)
    guard.require("setup")
    ledger = StageLedger(work)
    env = engine.environment()
    require_envelope_gpu(env)
    pins = check_pins(requirement_pins(package_root / REQUIREMENTS_MEMBER))
    if pins["drift"]:
        raise LaunchRefused(f"已装版本与 requirements 钉版本不符：{pins['drift']}")
    if expected_package is not None:
        what, recorded = expected_package
        require_same_package(recorded, verify, what=what)
    job = Job(work, kind, verify["freeze_receipt_sha256"], resume=resume)
    if resume:
        require_same_package(job.receipt.get("package"), verify, what=f"续跑 {resume}")
        env_path = job.path("env.json")
        recorded_env = _load_json(env_path) if env_path.is_file() else {}
        current_env = json.loads(json.dumps({"environment": env, "pins": pins}))  # 与落盘同形（tuple → list）
        if recorded_env.get("environment") != current_env["environment"] or \
                (recorded_env.get("pins") or {}).get("installed") != current_env["pins"].get("installed"):
            raise LaunchRefused(f"续跑 {resume}：运行环境或已装版本与首跑记录不同；不续用旧结果，回到实现角色")
        job.receipt.setdefault("resumes", []).append(
            {"utc": receipts.utc_stamp(), "package": package_identity(verify)})
    else:
        _json_dump(job.path("env.json"), {"environment": env, "pins": pins})
        job.receipt["package"] = verify
        job.receipt["pins"] = pins
        job.receipt["env_sha256"] = receipts.sha256_file(job.path("env.json"))
        job.receipt["gpu"] = env.get("gpu_name")
    job.save(ledger=ledger, guard=guard)
    return job, ledger, guard, verify, env


def _budget_stop_outside_stage(job: Job, guard: BudgetGuard, exc: BaseException) -> None:
    """阶段之外（下载、网格预检）被预算守卫停下时同样留 `stop` 收据。"""
    if not getattr(exc, "receipt_written", False):
        job.writer.write_run_receipt("stop", started=time.monotonic(), outputs=[],
                                     extra={"stage": "setup", "budget_guard": guard.snapshot(), "message": str(exc)})
        exc.receipt_written = True


def _preflight_failure(job: Job, exc: BaseException) -> None:
    """阶段之外（tokenizer 复核、网格预检、adapter 核对）的合同失败也留失败收据。"""
    if isinstance(exc, receipts.EngSftError) and not getattr(exc, "receipt_written", False):
        job.writer.write_failure_receipt(f"job-{job.kind.lower()}-preflight", exc.reason, exc.offending, message=str(exc))
        exc.receipt_written = True


def _code_dir(package_root: Path) -> Path:
    """云端/自检一律从包根的 code/ 运行（PYTHONPATH=<包根>/code）。"""
    return Path(package_root) / CODE_DIRNAME


def run_job_a(package_root: Path, work: Path, engine: Any, *, resume: str | None = None,
              clock: Callable[[], datetime] | None = None, code_location_check: bool = True,
              watchdog_fire: Callable[[], None] | None = None) -> dict[str, Any]:
    """作业 A：校验 → base → tokenizer 复核 → 网格预检 → 零样本 → 冒烟 → C1/C2/C3（含盲选层预测）。

    看门狗从前置检查通过起全程在后台：下载、网格预检、单步卡住也会在守卫时刻结束进程。
    """
    package_root = Path(package_root)
    job, ledger, guard, verify, _env = _prepare(
        package_root, work, engine, kind="A", resume=resume, clock=clock,
        code_location_check=code_location_check,
    )
    watchdog = Watchdog(guard, on_fire=watchdog_fire or _hard_exit_after(job, ledger, guard)).start()
    outcome = "incomplete"
    try:
        guard.require("setup")
        source = engine.ensure_base(Path(work), ledger)
        job.record("base", engine.base_files(source))
        job.record("tokenizer_recheck", tokenizer_recheck(engine, source, package_root))
        frames = _frame_paths(package_root, PACKAGE_DATA_FILES)
        guard.require("setup")
        job.record("image_grid", engine.check_grids(source, package_root, frames, should_stop=guard.should_stop))

        eval_rows = _read_jsonl(package_root / "data" / "eval.blind.jsonl")
        select_rows = _read_jsonl(package_root / "data" / "select-eval.blind.jsonl")
        smoke = _read_jsonl(package_root / "data" / "smoke.jsonl")
        train = _read_jsonl(package_root / "data" / "train.jsonl")

        if not job.stage_done("zero-shot"):
            out = job.path("predictions", "zero-shot.jsonl")
            _run_stage(job, ledger, guard, "zero_shot", "zero-shot", lambda: engine.predict(
                source, eval_rows, package_root, out, should_stop=guard.should_stop))

        if not job.stage_done("smoke"):
            def smoke_action() -> dict[str, Any]:
                out_dir = job.path("smoke")
                if out_dir.exists():
                    shutil.rmtree(out_dir)  # 上一次失败的残留作废，不续跑
                result = engine.train(
                    source, smoke, package_root, out_dir, lr=train_lora.CANDIDATES[0].lr,
                    epochs=train_lora.smoke_epochs(len(smoke)), expand=False,
                    max_steps=train_lora.SMOKE_MAX_STEPS,
                    predict_rows=train_lora.blind_rows_from_samples(smoke),
                    predict_out=out_dir / "smoke-predictions.jsonl",
                    should_stop=guard.should_stop,
                )
                verdict = train_lora.smoke_verdict(
                    result["last_loss"], smoke, _read_jsonl(out_dir / "smoke-predictions.jsonl"))
                _json_dump(out_dir / "smoke-result.json", {"train": result, "verdict": verdict})
                # 冒烟 adapter 只为验证流程，不参与选优；记下身份后删掉，控制回传体积。
                shutil.rmtree(out_dir / "adapter", ignore_errors=True)
                if not verdict["passed"]:
                    raise train_lora.SmokeFailed("冒烟未通过：停止，回接受角色", offending=[verdict])
                return {"train": result, "verdict": verdict}

            _run_stage(job, ledger, guard, "smoke", "smoke", smoke_action)

        runs = job.receipt.setdefault("runs", {})
        for config in train_lora.CANDIDATES:
            if job.stage_done(config.name):
                continue

            def train_action(config: train_lora.CandidateConfig = config) -> dict[str, Any]:
                out_dir = job.path("runs", config.name)
                if out_dir.exists():
                    shutil.rmtree(out_dir)  # 上一次失败的残留作废，不续跑
                result = engine.train(
                    source, train, package_root, out_dir, lr=config.lr, epochs=config.epochs,
                    expand=True, max_steps=None, predict_rows=select_rows,
                    predict_out=out_dir / "select-predictions.jsonl", should_stop=guard.should_stop,
                )
                result["config"] = {"name": config.name, "epochs": config.epochs, "lr": config.lr}
                runs[config.name] = result
                return {"run": config.name}

            _run_stage(job, ledger, guard, "train", config.name, train_action)
        outcome = "complete"
        return job.receipt
    except train_lora.BudgetStop as exc:
        outcome = "stopped_budget"
        _budget_stop_outside_stage(job, guard, exc)
        raise
    except BaseException as exc:
        outcome = f"failed:{getattr(exc, 'reason', type(exc).__name__)}"
        _preflight_failure(job, exc)
        raise
    finally:
        watchdog.stop()
        job.finalize(complete=outcome == "complete", ledger=ledger, guard=guard, outcome=outcome)
        _say(f"作业 A {job.id} 结束：{outcome}；回传目录 {job.dir}；"
             f"实例最迟 {guard.document.get('destroy_deadline_readable')} 前销毁")


def run_job_b(package_root: Path, work: Path, engine: Any, *, from_job: str, adapter: str,
              resume: str | None = None, clock: Callable[[], datetime] | None = None,
              code_location_check: bool = True,
              watchdog_fire: Callable[[], None] | None = None) -> dict[str, Any]:
    """作业 B：被选 adapter 在 Unity 盲评估集预测一次（不重训、不合并选层集）。"""
    package_root = Path(package_root)
    names = [config.name for config in train_lora.CANDIDATES]
    if adapter not in names:
        raise LaunchRefused(f"adapter 须是 {names} 之一")
    job_a_dir = Path(work) / "returned" / from_job
    job_a = _load_json(job_a_dir / JOB_RECEIPT_NAME)
    if job_a.get("job_kind") != "A" or not job_a.get("complete"):
        raise LaunchRefused(f"{from_job} 不是已完成的作业 A")
    run = job_a.get("runs", {}).get(adapter)
    adapter_dir = job_a_dir / "runs" / adapter / "adapter"
    weights = adapter_dir / "adapter_model.safetensors"
    if not run or not weights.is_file() or receipts.sha256_file(weights) != run.get("adapter_sha256"):
        raise ReturnHashMismatch(
            "被选 adapter 与作业 A 收据记录不符", offending=[{"adapter": adapter, "path": str(weights)}]
        )
    job, ledger, guard, verify, _env = _prepare(
        package_root, work, engine, kind="B", resume=resume, clock=clock,
        code_location_check=code_location_check,
        expected_package=(f"作业 B 使用作业 A {from_job} 的 adapter", job_a.get("package")),
    )
    watchdog = Watchdog(guard, on_fire=watchdog_fire or _hard_exit_after(job, ledger, guard)).start()
    outcome = "incomplete"
    try:
        base = Path(work) / BASE_DIRNAME
        if not (base / BASE_COMPLETE_MARKER).is_file():
            raise LaunchRefused("作业 B 不下载权重：实例上的 base/ 不完整，回到用户")
        source = ModelSource(str(base), None)
        job.record("selected_adapter", {
            "from_job": from_job, "config": adapter, "adapter_sha256": run["adapter_sha256"],
            "adapter_bytes": weights.stat().st_size,
        })
        job.record("tokenizer_recheck", tokenizer_recheck(engine, source, package_root))
        job.record("image_grid", engine.check_grids(
            source, package_root, _frame_paths(package_root, ("eval.blind.jsonl",)),
            should_stop=guard.should_stop))
        eval_rows = _read_jsonl(package_root / "data" / "eval.blind.jsonl")
        if not job.stage_done("eval"):
            out = job.path("predictions", "eval-adapter.jsonl")
            _run_stage(job, ledger, guard, "eval", "eval", lambda: engine.predict(
                source, eval_rows, package_root, out, adapter_dir=adapter_dir,
                should_stop=guard.should_stop))
        outcome = "complete"
        return job.receipt
    except train_lora.BudgetStop as exc:
        outcome = "stopped_budget"
        _budget_stop_outside_stage(job, guard, exc)
        raise
    except BaseException as exc:
        outcome = f"failed:{getattr(exc, 'reason', type(exc).__name__)}"
        _preflight_failure(job, exc)
        raise
    finally:
        watchdog.stop()
        job.finalize(complete=outcome == "complete", ledger=ledger, guard=guard, outcome=outcome)
        _say(f"作业 B {job.id} 结束：{outcome}；回传目录 {job.dir}；"
             f"实例最迟 {guard.document.get('destroy_deadline_readable')} 前销毁")


# --- 5060 自检（诊断，非证据）---------------------------------------------------------


def selfcheck_subset(package_root: Path) -> list[str]:
    """自检只核对 smoke.jsonl、它的帧与清单/收据，不读选层集与评估集。"""
    smoke = _read_jsonl(Path(package_root) / "data" / "smoke.jsonl")
    names = {"data/smoke.jsonl", "manifests/dataset-manifest.json", "manifests/eval-manifest.json",
             "manifests/freeze-receipt.json", "manifests/precheck-receipt.json"}
    names.update(row["frame_path"] for row in smoke)
    return sorted(names)


def run_selfcheck_pack(*, out_path: Path, repo_root: Path = PROJECT_ROOT,
                       local_root: Path | None = None) -> dict[str, Any]:
    """（本地）自检运输副本：只含代码束、两份清单、`manifests/` 与 `smoke.jsonl` 及其帧（K3-P2）。

    训练/选层/评估文件与其余帧不进这份副本；原 K4 包一个字节不改。副本写到包外（例如桌面），
    打包前先按自检子集核对一遍，保证笔记本上收到的是与云端同一份代码与清单。
    """
    root = Path(repo_root)
    local = Path(local_root) if local_root is not None else root / receipts.LOCAL_ROOT
    upload = local / UPLOAD_DIRNAME
    for required in (upload / UPLOAD_MANIFEST_NAME, upload / CODE_MANIFEST_NAME):
        if not required.is_file():
            raise PackageIncomplete(f"缺 {required.name}：先跑 bundle", offending=[required.name])
    out = Path(out_path).expanduser().resolve()
    if out == upload.resolve() or upload.resolve() in out.parents:
        raise PackageIncomplete("运输副本不能写进包根（会变成清单之外的文件）", offending=[str(out)])
    receipts.assert_output_allowed(out, root)
    subset = selfcheck_subset(upload)
    verify_package(upload, subset=subset)
    code_manifest = _load_json(upload / CODE_MANIFEST_NAME)
    members = [UPLOAD_MANIFEST_NAME, CODE_MANIFEST_NAME, *sorted(code_manifest["members"]), *subset]
    leaked = [name for name in members if name.startswith("data/") and name != "data/smoke.jsonl"]
    if leaked:
        raise PackageIncomplete("运输副本混入了 smoke 以外的数据文件", offending=leaked)
    out.parent.mkdir(parents=True, exist_ok=True)
    partial = out.with_name(out.name + ".partial")
    try:
        with tarfile.open(partial, "w", format=tarfile.PAX_FORMAT) as archive:
            for name in members:
                source_path = upload / name
                info = archive.gettarinfo(str(source_path), arcname=f"{UPLOAD_DIRNAME}/{name}")
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mtime = 0
                with open(source_path, "rb") as handle:
                    archive.addfile(info, handle)
        partial.replace(out)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    return {
        "out": str(out),
        "members": len(members),
        "frames": sum(1 for name in members if name.startswith("frames/")),
        "data_files": [name for name in members if name.startswith("data/")],
        "bytes": out.stat().st_size,
        "sha256": receipts.sha256_file(out),
    }


def run_selfcheck(package_root: Path, work: Path, engine: Any, *, source: ModelSource,
                  rows: int = SELFCHECK_MAX_ROWS, steps: int = SELFCHECK_MAX_STEPS,
                  micro_batch: int = 1, code_location_check: bool = True) -> dict[str, Any]:
    """上云前诊断：≤ 4 行零样本 → ≤ 5 步训练 → 重新加载 adapter 跑 ≤ 4 行。结果不进证据。"""
    # C1-K3-3：上下界都查（负数经 [:rows] 会变成「几乎全部 smoke 行」）；在计次与任何模型调用之前拒绝。
    if not (_whole_number_between(rows, 1, SELFCHECK_MAX_ROWS)
            and _whole_number_between(steps, 1, SELFCHECK_MAX_STEPS)
            and _whole_number_between(micro_batch, 1, None)):
        raise LaunchRefused(f"自检信封：推理 1–{SELFCHECK_MAX_ROWS} 行、训练 1–{SELFCHECK_MAX_STEPS} 步、"
                            f"micro-batch ≥ 1（收到 rows={rows!r}、steps={steps!r}、micro_batch={micro_batch!r}）")
    package_root = Path(package_root)
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    counter_path = work / "selfcheck-count.json"
    counter = _load_json(counter_path) if counter_path.is_file() else {"runs": []}
    if len(counter["runs"]) >= SELFCHECK_RUN_LIMIT:
        raise LaunchRefused(f"自检已运行 {len(counter['runs'])} 次，达到信封上限 {SELFCHECK_RUN_LIMIT}")
    # 不计次的前置：只查不装、只读本机。缺模块/没 CUDA/本机没有同版权重 → 拒绝，此时还没碰数据或模型。
    missing = engine.missing_modules()
    if missing:
        raise LaunchRefused(
            f"本机环境缺 {missing}；自检信封只允许加装 peft 与 accelerate，其余请回到探针环境（未计次）")
    preflight_env = engine.environment()
    if not preflight_env.get("cuda_available"):
        raise LaunchRefused("没有可用的 CUDA 设备（未计次）")
    model_location = engine.locate_model(source)
    stamp = receipts.utc_stamp()
    counter["runs"].append({"utc": stamp, "status": "started"})
    _json_dump(counter_path, counter)
    out = work / f"selfcheck-{stamp}"
    report: dict[str, Any] = {
        "schema_version": f"{receipts.SCHEMA_PREFIX}/selfcheck/v1",
        "work_id": receipts.WORK_ID,
        "nature": "DIAGNOSTIC_NOT_EVIDENCE",
        "utc": stamp,
        "limits": {"rows": rows, "steps": steps, "micro_batch": micro_batch},
    }
    status = "failed"
    try:
        report["verify"] = verify_package(
            package_root, expect_code_dir=_code_dir(package_root) if code_location_check else None,
            subset=selfcheck_subset(package_root),
        )
        report["environment"] = preflight_env
        report["model_location"] = model_location
        # 只记录与云端钉版本的差异，不据此声称云端同版已验证（K3-P2）。
        report["pins"] = check_pins(requirement_pins(package_root / REQUIREMENTS_MEMBER))
        report["pins"]["note"] = "诊断机版本记录；不是云端钉版本的验证"
        report["tokenizer_recheck"] = tokenizer_recheck(engine, source, package_root, files=("smoke.jsonl",))
        smoke = _read_jsonl(package_root / "data" / "smoke.jsonl")
        report["image_grid"] = engine.check_grids(
            source, package_root, sorted({row["frame_path"] for row in smoke}))
        blind = train_lora.blind_rows_from_samples(smoke)[:rows]
        report["zero_shot"] = engine.predict(source, blind, package_root, out / "zero-shot.jsonl")
        training = engine.train(
            source, smoke, package_root, out / "train", lr=train_lora.CANDIDATES[0].lr,
            epochs=max(1, -(-steps // max(1, train_lora.steps_per_epoch(len(smoke))))),
            expand=False, max_steps=steps, predict_rows=[], predict_out=out / "train" / "unused.jsonl",
            micro_batch=micro_batch,
        )
        report["train"] = training
        report["adapter_reload"] = engine.predict(
            source, blind, package_root, out / "adapter.jsonl", adapter_dir=out / "train" / "adapter")
        report["parsed"] = {
            name: [
                {"row_id": row["row_id"], "status_pred": row["status_pred"], "parse_error": row["parse_error"],
                 "raw_output": row["raw_output"][:200]}
                for row in _read_jsonl(out / f"{name}.jsonl")
            ]
            for name in ("zero-shot", "adapter")
        }
        status = "succeeded"
        return report
    except BaseException as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc)[:2000],
                           "reason": getattr(exc, "reason", None),
                           "offending": getattr(exc, "offending", None)}
        raise
    finally:
        report["status"] = status
        _json_dump(out / "selfcheck.json", report)
        counter["runs"][-1]["status"] = status
        _json_dump(counter_path, counter)
        _say(f"自检结束：{status}；报告 {out / 'selfcheck.json'}")


# --- CLI ---------------------------------------------------------------------------


def _print_status(work: Path) -> None:
    ledger = StageLedger(work)
    print(json.dumps(ledger.snapshot()["counts"], ensure_ascii=False), f"总 {sum(ledger.counts().values())}/{TOTAL_LAUNCH_LIMIT}")
    budget = Path(work) / BUDGET_NAME
    if budget.is_file():
        print(json.dumps(BudgetGuard(work).snapshot(), ensure_ascii=False, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-SFT-002 K3 云端运行器")
    sub = parser.add_subparsers(dest="command", required=True)

    bundle = sub.add_parser("bundle", help="（本地）生成 K3 代码束与 code-manifest.json")
    bundle.add_argument("--repo-root", default=str(PROJECT_ROOT))
    bundle.add_argument("--local-root", default=None)

    verify = sub.add_parser("verify", help="按两份清单逐文件核对包根")
    verify.add_argument("--package", required=True)

    def add_rates(command: argparse.ArgumentParser) -> None:
        # 四项费率都必须从报价上读出填写（免费就填 0）；不给就不算，费用不明不租（AC-13 修订 1）。
        command.add_argument("--gpu-usd-per-hour", type=float, required=True)
        command.add_argument("--storage-usd-per-hour", type=float, required=True)
        command.add_argument("--inbound-usd-per-tb", type=float, required=True)
        command.add_argument("--outbound-usd-per-tb", type=float, required=True)
        command.add_argument("--inbound-gb", type=float, default=DEFAULT_INBOUND_GB)
        command.add_argument("--outbound-gb", type=float, default=DEFAULT_OUTBOUND_GB)

    plan = sub.add_parser("budget-plan", help="（租机前，本机即可）按报价算最长可用时长，不写任何文件")
    add_rates(plan)

    budget = sub.add_parser("budget-init", help="（云端）记录开机时刻与报价费率，写出销毁截止时刻")
    budget.add_argument("--work", required=True)
    budget.add_argument("--minutes-since-start", type=float, required=True)
    add_rates(budget)

    pack = sub.add_parser("selfcheck-pack", help="（本地）生成只含 smoke 的自检运输副本")
    pack.add_argument("--out", required=True)
    pack.add_argument("--repo-root", default=str(PROJECT_ROOT))
    pack.add_argument("--local-root", default=None)

    for name in ("job-a", "job-b"):
        job = sub.add_parser(name)
        job.add_argument("--package", required=True)
        job.add_argument("--work", required=True)
        job.add_argument("--micro-batch", type=int, default=8)
        job.add_argument("--resume", default=None)
        if name == "job-b":
            job.add_argument("--from-job", required=True)
            job.add_argument("--adapter", required=True, choices=[c.name for c in train_lora.CANDIDATES])

    check = sub.add_parser("selfcheck", help="（5060 笔记本）上云前诊断，不是证据")
    check.add_argument("--package", required=True)
    check.add_argument("--work", required=True)
    check.add_argument("--model", default=train_lora.BASE_REPO,
                       help="本机已有的同版权重目录，或 repo id（只读本机缓存，不下载）")
    check.add_argument("--rows", type=int, default=SELFCHECK_MAX_ROWS)
    check.add_argument("--steps", type=int, default=SELFCHECK_MAX_STEPS)
    check.add_argument("--micro-batch", type=int, default=1)

    status = sub.add_parser("status")
    status.add_argument("--work", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "bundle":
            document = run_bundle(
                repo_root=Path(args.repo_root),
                local_root=Path(args.local_root) if args.local_root else None,
            )
            print(json.dumps(document, ensure_ascii=False, indent=2))
        elif args.command == "verify":
            package = Path(args.package)
            result = verify_package(package, expect_code_dir=_code_dir(package))
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command in ("budget-plan", "budget-init"):
            rates = {
                "gpu_usd_per_hour": args.gpu_usd_per_hour,
                "storage_usd_per_hour": args.storage_usd_per_hour,
                "inbound_usd_per_tb": args.inbound_usd_per_tb,
                "outbound_usd_per_tb": args.outbound_usd_per_tb,
                "inbound_gb": args.inbound_gb,
                "outbound_gb": args.outbound_gb,
            }
            if args.command == "budget-plan":
                document = budget_plan(**rates)
            else:
                document = init_budget(Path(args.work), minutes_since_start=args.minutes_since_start, **rates)
            print(json.dumps(document, ensure_ascii=False, indent=2))
            if args.command == "budget-init":
                print(f"\n>>> 实例最迟在 {document['destroy_deadline_readable']} 之前由你在 vast.ai 控制台销毁；"
                      "无论是否在等回传、等答复或遇到报错，到点都销毁。运行器不会替你销毁实例。")
            elif not document["estimate_fits"]:
                print("\n>>> 该报价下的守卫时长短于全流程估算，建议换更便宜的报价（估算未实测）。")
        elif args.command == "selfcheck-pack":
            document = run_selfcheck_pack(
                out_path=Path(args.out), repo_root=Path(args.repo_root),
                local_root=Path(args.local_root) if args.local_root else None,
            )
            print(json.dumps(document, ensure_ascii=False, indent=2))
        elif args.command == "job-a":
            run_job_a(Path(args.package), Path(args.work), TorchEngine(micro_batch=args.micro_batch),
                      resume=args.resume)
        elif args.command == "job-b":
            run_job_b(Path(args.package), Path(args.work), TorchEngine(micro_batch=args.micro_batch),
                      from_job=args.from_job, adapter=args.adapter, resume=args.resume)
        elif args.command == "selfcheck":
            model = Path(args.model)
            source = (ModelSource(str(model), None) if model.is_dir()
                      else ModelSource(args.model, train_lora.BASE_REVISION))
            report = run_selfcheck(Path(args.package), Path(args.work), TorchEngine(micro_batch=args.micro_batch),
                                   source=source, rows=args.rows, steps=args.steps,
                                   micro_batch=args.micro_batch)
            print(json.dumps({k: report.get(k) for k in ("status", "train", "parsed")},
                             ensure_ascii=False, indent=2, default=str)[:6000])
        elif args.command == "status":
            _print_status(Path(args.work))
    except receipts.EngSftError as exc:
        print(f"失败（{exc.reason}）：{exc}", file=sys.stderr)
        return 1
    except train_lora.BudgetStop as exc:
        print(f"预算守卫停止：{exc}", file=sys.stderr)
        return 3
    except LaunchRefused as exc:
        print(f"拒绝启动：{exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
