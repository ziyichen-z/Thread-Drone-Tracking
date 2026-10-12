"""P1-ENG-LOOP-002 OpsK1K2K3K4：阶段 B 统一分阶段入口（AC-8/9/10/14/15/16 修订；O1–O4）。

合同来源：同名提案「OPS九题答复落实」§1–6（十条 AC 修订、W1–W5、O1–O4、§3 文件闭集、§5 零消耗边界）。
本工具把操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md` 各节的**既有命令**组合成一个按阶段推进的
入口；不新增板服务、不改控制/感知/模型/评分，所有门值、原因码与资源上限沿原合同。

阶段（子命令；每个阶段只在前置门具名有效放行且机械检查成功时推进，任何失败非零退出、停依赖动作）：

* ``plan``   Play 前离线：运行原 ``analyze_play derive-bc``（独立进程），逐字核对操作单第 7 节读数，冻结
  计划 ``ops-plan.json``（只含文字/intent/Δ/观察时长；无任何几何量）。几何结果不进在线判断。
* ``gate``   第 1 节 1.0–1.5 机械核对（严格双来源、最新有效 passed_candidate、PLAY_GOVERNING、全局
  blocks/releases、HEAD/status/_Recovery、操作单 sha、账本命中与自检）。各单元开始前自动再跑。
* ``source`` 第 0.3 节来源核验（OPS:SOURCE:2：只核 Air 现有原件，缺件即停；不复制）。
* ``prep``   单元 #1（要求 G1/G2/G3/G5）：只读准备读脚本，读齐即停，交接受 G4 核清。
* ``receipt`` 单元 #2（另要求 G4 机读放行）：建根/资产/部署/前台服务监督/身份/measure→k-receipt/停止释放/日志回传。
* ``play``   单元 #3：前台服务、每剧本等待本人 Play、会话、本机操作网页（W1–W5）、原计划调度（本人发送/跳过、
  候选选择）、停止/归档、服务停止释放、日志回传；收尾后在**独立进程**调用 ``summarize_ops``。

在线部分（会话期间的调度与网页）只使用实时传感器画面、会话原流与 Play 前冻结的文字/intent 计划；
不读真值、评分产物或几何，不导入评分/几何工具（AC-9 修订 1；`tests/test_loop2_isolation.py`）。

「OPS验证额度落实与IR裁定」§3 IR-OPS-1…6 已裁定并在此落实（AC-10 修订 4 / AC-14 修订 2 / AC-16 修订 3）：
G4 机读行 ``g4_release: <prep.stdout sha256>``（只由接受写）、Unity 日志登记行 ``release_raw_sha256=<sha>``
（只由当轮发令角色写）、``TERMINAL(rebuild_limit)`` 一律 ``S-REBUILD``/UNKNOWN 停全部、新入口无任何环境性
重试路径、观察/跟随只锚定会话原流（receipt 写盘时刻 / 同纪元 TRACKING 事件，不以 CLI 返回、点击或轮询
时刻补值）。

* ``diag``（仅 ``--mode diagnostic``）：IR-OPS-5 诊断模式（同节 §4）；request_id 按诊断条目闭表 ``DIAG_ENTRIES`` 绑定（同名提案
  「诊断绑定方案答复」BIND-1…6，AC-10 修订 9）：现行唯一已签 ``P1-ENG-LOOP-002:DIAG:RETRY:1``（仅 P1）须在发布引用账本唯一条目内
  命中反引号完整 id，代码已独立通过（``passed_candidate``）且接受机读放行行 ``diag_release: <request_id> <passed sha>``；
  旧 SUB:3（``sub3_release``）只作历史，代码级无条件拒续；同 id 粗账读坏或 ``consumed`` 非字面 false 即拒启；独立 Air/板根、
  ``ops-diagnostic-ledger.json`` 粗账、两条主连接/一次服务启动/一次 Play、四类 STOP 与 ``DIAG_FAULT`` 分流；
  不写正式 assets/收据/ledger/ID，不作任何门判定。正式阶段在诊断模式一律拒启，``diag`` 在正式模式拒启。
  DIAG-CONTROL-1（AC-10 修订 8）：诊断主连接的 ControlPath 放在本进程新建的短私有临时目录（不在诊断根下），
  按编码后实际路径 + OpenSSH 临时后缀核本机 AF_UNIX 上限并实测 bind；建不成即拒启（未消耗）。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shlex
import secrets
import shutil
import socket
import stat
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - 直接以脚本运行时
    sys.path.insert(0, str(REPO_ROOT))

from controller import language_bridge as bridge  # noqa: E402
from tools.eng_loop2 import operator_web as web  # noqa: E402

WORK_ID = "P1-ENG-LOOP-002"
DEFAULT_OUT = "outputs/eng-loop2/P1-ENG-LOOP-002"
DEFAULT_PY = ".venv-yoloe/bin/python"
HOST_ALIAS = "Jetson"
PLAY_OPS_DOC = "docs/evidence/P1-ENG-LOOP-002-play-ops.md"
DIAG_OPS_DOC = "docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md"
MINI_PREP_DOC = "docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md"
PROPOSAL = "docs/proposals/P1-ENG-LOOP-002-closed-loop-four-numbers.md"
REVIEW_FILE = "docs/reviews/P1-ENG-LOOP-002.md"
#: 本增量冻结操作单集合（「OPS九题答复落实」§3 末段：三份均视为 PLAY_GOVERNING）。
OPS_SHEETS = (PLAY_OPS_DOC, DIAG_OPS_DOC, MINI_PREP_DOC)
#: workflow §4.4 PLAY_GOVERNING 的逐项展开（操作单第 1.0 节同一列表）。
PG_PATHS = ("controller/", "Assets/", "tools/", "tests/", "config/", "ProjectSettings/", "Packages/packages-lock.json")
LEDGER_HITS = ("用户答 Mac mini 补核核清四题", "SLOT:FACT:1")
BOARD_ROOT = "/home/jetson/eng-loop2"
BOARD_CODE = BOARD_ROOT + "/code"
BOARD_LOGS = BOARD_ROOT + "/logs"
LLAMA_PORT = 18081
SERVE_PORT = 18082
#: 第 0.6 节「预留的来源」：按单元机械派生，不手填。
RESERVE_BY_UNIT = {2: 25, 3: 11}
SRC_NAMES = (
    "WEIGHTS", "EXP_WEIGHTS_SHA", "EXP_WEIGHTS_BYTES", "MMPROJ", "EXP_MMPROJ_SHA", "EXP_MMPROJ_BYTES",
    "LLAMA_BIN", "EXP_LLAMA_BIN_SHA", "EXP_LLAMA_BIN_BYTES",
)
#: 第 0.5 节通道闭集（顺序、每个恰 1 次）。
CHANNELS = {
    1: ("prep-read",),
    2: ("root-create", "assets", "deploy-tar", "deploy-expect", "deploy-verify", "serve", "logs-2"),
    3: ("serve", "logs-3"),
}
#: 第 0.4 节已签上限（执行时守账；成功、失败、重试共账，耗尽即停）。
LIMITS = {
    "ssh_units": 3, "unit_wall_s": 3600.0, "ssh_wall_total_s": 10800.0, "serve_starts": 2, "sessions": 5,
    "plays": 5, "play_wall_s": 420.0, "play_wall_total_s": 2100.0, "t_sess_s": 290.0, "overlay_generations": 5,
    "residual_moves": 1, "version_calls": 3, "transfer_batches": 3, "transfer_bytes": 20_000_000,
    "archive_per_play_bytes": 225_000_000, "residency_s": 3600.0,
}
STOP_CODES = (
    "S-PRECHECK", "S-RECEIPT", "S-IDENTITY", "S-ENVELOPE", "S-LOAD", "S-BACKEND", "S-REBUILD",
    "S-WALL", "S-ARCHIVE", "S-SERVICE", "S-RING",
)
#: IR-OPS-1 / IR-OPS-2（「OPS验证额度落实与IR裁定」§3 采纳）：G4 放行行只由接受写在同名提案具名
#: 「G4准备核清与放行」节；Unity 日志登记行只由当轮发令角色写。缺行/不匹配/读取失败 → S-PRECHECK。
G4_RELEASE_LINE = re.compile(r"^[ \t]*([-*][ \t]+)?`?g4_release: ([0-9a-f]{64})(`|\s|$)")
UNITY_LOG_SHA_LINE = "release_raw_sha256="
SESSION_IDS = {"P1": "loop2-p1", "P2": "loop2-p2", "P3": "loop2-p3"}
PLAN_SCHEMA = "p1-eng-loop-002-ops-plan/v1"
PLAY_START_WAIT_S = 120.0
UNITY_STOP_QUIET_S = 5.0
#: C6-2：失败/超时/中断收尾时发出（至多一次的）stop 之后等会话进程自行退出的上限；到时仍在运行照记 UNKNOWN，不杀进程。
SESSION_STOP_WAIT_S = 30.0
#: C6-2：越过工具截止后为**安全归档**再等本人停 Play 的上限（只是收尾等待，不是额度；越界照记、不追认）。
UNITY_STOP_CLOSEOUT_WAIT_S = 120.0
LISTEN_WAIT_S = 420.0
SERVE_EXIT_WAIT_S = 120.0
TICK_S = 0.1
#: IR-OPS-6：选择受理后等待会话原流写出该 request_id 的 receipt / 同纪元 TRACKING 事件的上限（原 CLI 自身
#: 等回执也是 5 s）。超时只触发 UNKNOWN 停依赖，**从不**把 CLI 返回、网页点击或轮询发现时刻当作原流时刻补值。
ANCHOR_WAIT_S = 5.0


class Stop(Exception):
    """命中操作单第 13 节原因码（或 `S-SSH` 按 `S-PRECHECK` 处置）；只做已签安全收尾。"""

    def __init__(self, code: str, detail: str, *, stop_all: bool = True, report: Mapping[str, Any] | None = None):
        if code not in STOP_CODES:
            raise ValueError(f"unknown stop code {code!r}")
        super().__init__(f"{code} {detail}")
        self.code, self.detail, self.stop_all = code, detail, stop_all
        #: 抛出前已产生的事实（例如已完成的归档移动清单/体积），供尝试记录保留（C6-3）。
        self.report = dict(report) if report is not None else None


class UnknownOutcome(Exception):
    """OPSR1返工 R1-3：收尾/摘要中无法证明的结局（归档跳过或失败、摘要/评分非 0 等）：记 `UNKNOWN`、停全部依赖、交接受。

    不是第 13 节原因码，也不冒充任何一码；与 Ctrl-C/不明异常同一记录形态（`describe_failure`）。
    """

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str | bytes) -> str:
    return hashlib.sha256(text.encode("utf-8") if isinstance(text, str) else text).hexdigest()


# --- 记录与执行 -----------------------------------------------------------------


class Recorder:
    """本次调用的原流：`play-ops.jsonl` 逐事件、各命令 stdout/stderr 原样落文件；只追加、不改写。"""

    def __init__(self, root: Path, stage: str, *, clock: Callable[[], float] = time.time):
        self.root = Path(root) / "ops" / f"{stage}-{utc_now()}"
        suffix = 1
        base = self.root
        while self.root.exists():
            suffix += 1
            self.root = base.with_name(f"{base.name}-{suffix}")
        self.root.mkdir(parents=True)
        self.clock = clock
        self.log = web.OpsLog(self.root / "play-ops.jsonl", clock=clock)
        self.counter = 0

    def event(self, kind: str, **fields: Any) -> None:
        self.log.write(kind, **fields)

    def stream_paths(self, name: str) -> tuple[Path, Path]:
        self.counter += 1
        stem = f"{self.counter:03d}-{re.sub(r'[^A-Za-z0-9._-]+', '_', name)}"
        return self.root / f"{stem}.stdout", self.root / f"{stem}.stderr"


@dataclass
class Completed:
    rc: int
    stdout: str
    stderr: str
    stdout_path: Path
    stderr_path: Path


class Shell:
    """执行一条本机命令并把原流落盘；从不重试。"""

    def __init__(self, recorder: Recorder, *, cwd: Path, env: Mapping[str, str] | None = None):
        self.recorder, self.cwd = recorder, Path(cwd)
        self.env = dict(env) if env is not None else None

    def run(
        self,
        name: str,
        argv: Sequence[str],
        *,
        stdin_bytes: bytes | None = None,
        stdin_path: Path | None = None,
        stdout_path: Path | None = None,
        timeout: float | None = None,
        env: Mapping[str, str] | None = None,
        cwd: Path | None = None,
    ) -> Completed:
        out_path, err_path = self.recorder.stream_paths(name)
        if stdout_path is not None:
            out_path = Path(stdout_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
        started = time.time()
        merged_env = None
        if self.env is not None or env is not None:
            merged_env = dict(os.environ)
            merged_env.update(self.env or {})
            merged_env.update(env or {})
        stdin = open(stdin_path, "rb") if stdin_path is not None else None
        try:
            with out_path.open("wb") as out, err_path.open("wb") as err:
                kwargs: dict[str, Any] = {"input": stdin_bytes} if stdin is None and stdin_bytes is not None else {
                    "stdin": stdin if stdin is not None else subprocess.DEVNULL}
                try:
                    done = subprocess.run(
                        list(argv), cwd=cwd or self.cwd, stdout=out, stderr=err,
                        timeout=timeout, env=merged_env, check=False, **kwargs,
                    )
                    rc = done.returncode
                except subprocess.TimeoutExpired:
                    rc = 124
                except OSError as error:
                    err.write(f"{type(error).__name__}: {error}\n".encode())
                    rc = 127
        finally:
            if stdin is not None:
                stdin.close()
        stdout = out_path.read_bytes().decode("utf-8", errors="replace")
        stderr = err_path.read_bytes().decode("utf-8", errors="replace")
        self.recorder.event("command", name=name, argv=list(argv), rc=rc, started_unix_s=started,
                            finished_unix_s=time.time(), stdout_path=str(out_path), stderr_path=str(err_path),
                            stdout_sha256=sha256_text(stdout), stderr_sha256=sha256_text(stderr))
        return Completed(rc, stdout, stderr, out_path, err_path)


class Ledger:
    """第 0.4 节逐维度守账（持久化于 `$OUT/ops-ledger.json`）；每次消耗性动作**之前**检查。"""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.data: dict[str, float] = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.data = {}

    def used(self, key: str) -> float:
        return float(self.data.get(key, 0))

    def take(self, key: str, amount: float = 1, *, limit_key: str | None = None) -> None:
        limit = LIMITS[limit_key or key]
        if self.used(key) + amount > limit:
            raise Stop("S-ENVELOPE", f"{key} would exceed {limit} (used {self.used(key)}, +{amount})")
        self.data[key] = self.used(key) + amount
        self.path.write_text(json.dumps(self.data, sort_keys=True, indent=1) + "\n", encoding="utf-8")

    def add(self, key: str, amount: float) -> None:
        self.data[key] = self.used(key) + amount
        self.path.write_text(json.dumps(self.data, sort_keys=True, indent=1) + "\n", encoding="utf-8")


@dataclass
class Context:
    repo: Path
    out: Path
    python: str
    recorder: Recorder
    shell: Shell
    ledger: Ledger
    ssh: str = "ssh"
    alias: str = HOST_ALIAS
    docwt: Path | None = None
    board_ts: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)


def make_context(arguments: argparse.Namespace, stage: str) -> Context:
    repo = Path(arguments.repo).resolve()
    out = (repo / arguments.out).resolve() if not Path(arguments.out).is_absolute() else Path(arguments.out)
    out.mkdir(parents=True, exist_ok=True)
    python = arguments.python if Path(arguments.python).is_absolute() else str(repo / arguments.python)
    recorder = Recorder(out, stage)
    shell = Shell(recorder, cwd=repo)
    ledger = Ledger(out / "ops-ledger.json")
    docwt = Path(arguments.docwt).resolve() if getattr(arguments, "docwt", None) else None
    context = Context(repo, out, python, recorder, shell, ledger, ssh=arguments.ssh, alias=arguments.alias, docwt=docwt)
    recorder.event("stage_start", stage=stage, argv=sys.argv, repo=str(repo), out=str(out), python=python)
    return context


# --- 文档块（单一来源：操作单/证据中的附录原文） ------------------------------------------


def extract_block(document: Path, heading_prefix: str, language: str) -> str:
    """取 `heading_prefix` 开头的标题之后第一个 ```<language> 围栏块的原文。"""
    lines = Path(document).read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith(heading_prefix))
    except StopIteration as error:
        raise Stop("S-PRECHECK", f"block_heading_missing {heading_prefix!r} in {document}") from error
    try:
        open_at = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == f"```{language}")
        close_at = next(i for i in range(open_at + 1, len(lines)) if lines[i].strip() == "```")
    except StopIteration as error:
        raise Stop("S-PRECHECK", f"block_fence_missing {heading_prefix!r}") from error
    return "\n".join(lines[open_at + 1 : close_at]) + "\n"


# --- 第 1 节 接受放行核对（G1/G3 机械部分；1.0–1.5） ------------------------------------------


@dataclass
class GateResult:
    ok: bool
    rel: str | None
    passed: str | None
    raw_path: Path
    block_11_14: str
    stops: list[str]


MR = r"^[ \t]*([-*][ \t]+)?`?"


def _last_key_line(text: str, key: str) -> tuple[int | None, str | None]:
    pattern = re.compile(MR + key + r": ([0-9a-f]{40})(`|[ \t]|$)")
    found: tuple[int | None, str | None] = (None, None)
    for number, line in enumerate(text.splitlines(), start=1):
        match = pattern.match(line)
        if match:
            found = (number, match.group(2))
    return found


CONSUMING_GATE_SNIPPET = r'''
import importlib.util, json, sys
from pathlib import Path
root = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("rel_check_docs", root / "tools" / "check_docs.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
open_blocks = mod.open_consuming_gate_blocks(root / "docs" / "reviews")
released = mod.ledger_released_findings(root / "docs" / "implementation-status.md")
remaining = {}
for name, ids in open_blocks.items():
    left = [f for f in ids if f not in released.get(name[: -len(".md")], set())]
    if left:
        remaining[name] = left
print("consuming_gate_open_blocks_by_file_order=" + json.dumps(open_blocks, ensure_ascii=False, sort_keys=True))
print("ledger_released_scope_gap=" + json.dumps({k: sorted(v) for k, v in released.items()}, ensure_ascii=False, sort_keys=True))
print("consuming_gate_unreleased=" + json.dumps(remaining, ensure_ascii=False, sort_keys=True))
sys.exit(4 if remaining else 0)
'''


def release_gate(ctx: Context, ledger_hits: Sequence[str] = LEDGER_HITS) -> GateResult:
    """操作单第 1.0–1.5 节的机械部分；原流写 `$OUT/release/<UTC>.txt`。不 checkout、不写已跟踪路径。

    `ledger_hits`：1.5 账本命中项（正式 = 第 1.5 节两条；诊断 = 调用方传入的 `DIAG_ENTRIES` 条目标题片段与完整 request_id）。
    """
    git = ["git", "-C", str(ctx.repo)]
    lines: list[str] = []
    stops: list[str] = []

    def note(text: str) -> None:
        lines.append(text)

    def gate_stop(text: str) -> None:
        stops.append(text)
        note(f"STOP S-PRECHECK {text}")

    def git_out(name: str, args: Sequence[str]) -> Completed:
        return ctx.shell.run(name, [*git, *args])

    release_dir = ctx.out / "release"
    release_dir.mkdir(parents=True, exist_ok=True)
    fetch = git_out("git-fetch", ["fetch", "origin"])
    note(f"git_fetch_rc={fetch.rc}")
    if fetch.rc != 0:
        gate_stop(f"git_fetch_failed rc={fetch.rc}")
    rel_run = git_out("rev-parse-origin", ["rev-parse", "origin/main"])
    rel = rel_run.stdout.strip() if rel_run.rc == 0 and re.fullmatch(r"[0-9a-f]{40}", rel_run.stdout.strip()) else None
    passed = None
    if rel is None:
        gate_stop("rel_unresolved")
    else:
        review = git_out("show-review", ["show", f"{rel}:{REVIEW_FILE}"])
        if review.rc != 0:
            gate_stop("review_file_unreadable")
        round_line, round_sha = _last_key_line(review.stdout, "round_candidate")
        pass_line, passed = _last_key_line(review.stdout, "passed_candidate")
        note(f"rel={rel} last_round_line={round_line} last_round_candidate={round_sha} pass_line={pass_line} passed_candidate={passed}")
        if round_line is None:
            gate_stop("no_valid_round_candidate_line")
        if pass_line is None:
            gate_stop("no_valid_passed_candidate_line")
        if round_line is not None and pass_line is not None and not pass_line > round_line:
            gate_stop(f"latest_round_not_passed last_round_line={round_line} pass_line={pass_line}")
        if passed is not None:
            ancestor = git_out("is-ancestor", ["merge-base", "--is-ancestor", passed, rel])
            if ancestor.rc != 0:
                gate_stop("passed_not_ancestor_of_rel")
        if not stops:
            note("RELEASE_REF_OK")
        workflow = git_out("show-workflow", ["show", f"{rel}:docs/collaboration-workflow.md"])
        wl = workflow.stdout.splitlines()
        definition = "\n".join(
            "\n".join(wl[i : i + 3]) for i, line in enumerate(wl) if "唯一权威定义" in line
        )
        for path in PG_PATHS:
            if f"`{path}`" not in definition:
                gate_stop(f"pg_definition_drift {path}")
        if passed is not None:
            diff = git_out("pg-diff", ["diff", "--name-only", passed, rel, "--", *PG_PATHS, *OPS_SHEETS])
            note(f"pg_diff_rc={diff.rc} pg_diff_passed_to_rel=[{diff.stdout.strip()}]")
            if diff.rc != 0:
                gate_stop(f"pg_diff_failed rc={diff.rc}")
            elif diff.stdout.strip():
                gate_stop("play_governing_changed_after_pass")
            else:
                note("PG_DIFF_EMPTY_OK")
            other = git_out("all-diff", ["diff", "--name-only", passed, rel])
            note("other_diff_passed_to_rel=[" + " ".join(other.stdout.split()) + "]")
        # 消耗性门（tools/check_docs.py 第 9 项两个函数，取 $REL 原文件，不改工具）
        export = Path(tempfile.mkdtemp(prefix=f"cg-tree-{utc_now()}-", dir=release_dir))
        archive_path = export.with_suffix(".tar")
        exported = git_out("cg-archive", ["archive", "--format=tar", "-o", str(archive_path), rel,
                                          "docs/reviews", "docs/implementation-status.md", "tools/check_docs.py"])
        cg_rc = 99
        if exported.rc == 0:
            with tarfile.open(archive_path) as archive:
                archive.extractall(export, filter="data")
            check = ctx.shell.run("consuming-gate", [ctx.python, "-I", "-B", "-", str(export)],
                                  stdin_bytes=CONSUMING_GATE_SNIPPET.encode())
            note(check.stdout.strip())
            cg_rc = check.rc
        else:
            gate_stop("cg_export_failed")
        if cg_rc == 0:
            note("CONSUMING_GATE_OK")
        elif cg_rc == 4:
            gate_stop("consuming_gate_blocked")
        else:
            gate_stop(f"consuming_gate_check_failed rc={cg_rc}")
        # 1.5 账本命中（发布引用上）
        ledger = git_out("show-ledger", ["show", f"{rel}:docs/authorizations.md"])
        for needle in ledger_hits:
            hit = needle in ledger.stdout
            note(f"ledger_hit[{needle}]={'yes' if hit else 'no'}")
            if not hit:
                gate_stop(f"ledger_entry_missing {needle}")
    # 1.1–1.4（执行检出）
    block: list[str] = []
    head = git_out("rev-parse-head", ["rev-parse", "HEAD"]).stdout.strip()
    block.append(f"head={head}")
    if passed is None or head != passed:
        gate_stop("head_not_passed_candidate (关闭 Unity 后由操作者 git checkout --detach <passed>)")
    else:
        block.append("HEAD_EQ_PASSED_OK")
    status = git_out("status", ["status", "--porcelain", "--untracked-files=normal"])
    block.append("status=[" + status.stdout.rstrip("\n") + "]")
    if status.rc != 0 or status.stdout.strip():
        gate_stop("worktree_not_clean")
    recovery = ctx.repo / "Assets" / "_Recovery"
    if recovery.exists() or recovery.is_symlink():
        block.append("STOP S-PRECHECK unity_recovery_present")
        stops.append("unity_recovery_present")
    else:
        block.append("NO_UNITY_RECOVERY")
    for sheet in OPS_SHEETS:
        local = ctx.repo / sheet
        blob = git_out(f"show-passed-{Path(sheet).name}", ["show", f"{passed}:{sheet}"]) if passed else None
        local_sha = sha256_file(local) if local.is_file() else None
        passed_sha = sha256_text(blob.stdout.encode()) if blob is not None and blob.rc == 0 else None
        block.append(f"sheet {sheet} local={local_sha} passed={passed_sha}")
        if local_sha is None or local_sha != passed_sha:
            gate_stop(f"ops_sheet_not_passed_version {sheet}")
    lines.extend(block)
    # 1.5 自检（文档检出 $DOCWT 须位于 $REL）
    if ctx.docwt is None:
        gate_stop("docwt_unset")
    elif rel is not None:
        dw_head = ctx.shell.run("docwt-head", ["git", "-C", str(ctx.docwt), "rev-parse", "HEAD"]).stdout.strip()
        note(f"docwt_head={dw_head}")
        if dw_head != rel:
            gate_stop("docwt_not_at_rel")
        for tool in ("tools/check_ledger.py", "tools/check_docs.py"):
            run = ctx.shell.run(f"docwt-{Path(tool).stem}", ["python3", tool], cwd=ctx.docwt)
            note(f"{tool}_rc={run.rc}")
            if run.rc != 0:
                gate_stop(f"self_check_failed {tool}")
    ok = not stops
    note("RELEASE_GATE_OK" if ok else f"STOP S-PRECHECK release_gate stops={len(stops)}")
    handle, name = tempfile.mkstemp(prefix=f"{utc_now()}-", suffix=".txt", dir=release_dir)
    os.close(handle)
    raw_path = Path(name)
    raw_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ctx.recorder.event("release_gate", ok=ok, rel=rel, passed=passed, raw_path=str(raw_path),
                       raw_sha256=sha256_file(raw_path), stops=stops)
    return GateResult(ok, rel, passed, raw_path, "\n".join(block) + "\n", stops)


def require_gate(ctx: Context, registered: Path | None, *, need_registration: bool) -> GateResult:
    """每单元/Play 前：重跑第 1 节；正式单元另核 1.6（登记原流 1.1–1.4 逐行相同，且已推送进 Unity 日志）。"""
    result = release_gate(ctx)
    if not result.ok:
        raise Stop("S-PRECHECK", "release_gate " + ";".join(result.stops))
    if need_registration:
        if registered is None or not Path(registered).is_file():
            raise Stop("S-PRECHECK", "registered_release_missing (1.6 现场原流先于登记)")
        text = Path(registered).read_text(encoding="utf-8")
        if result.block_11_14 not in text:
            raise Stop("S-PRECHECK", "registered_release_1_1_to_1_4_differs (回接受)")
        log = ctx.shell.run("show-unity-log", ["git", "-C", str(ctx.repo), "show", f"{result.rel}:docs/unity-test-log.md"])
        marker = UNITY_LOG_SHA_LINE + sha256_file(Path(registered))
        if log.rc != 0 or marker not in log.stdout:
            raise Stop("S-PRECHECK", f"unity_log_registration_missing {marker} (IR-OPS-2；回接受)")
    return result


def require_g4(ctx: Context, gate: GateResult) -> str:
    """G4（接受核清准备读数并明确放行）的机读行（IR-OPS-1 采纳）；缺/不匹配/读取失败即停（不自签门）。"""
    prep_stdout = ctx.out / "prep" / "prep.stdout"
    if not prep_stdout.is_file():
        raise Stop("S-PRECHECK", "prep_stdout_missing (G4 未核清)")
    prep_sha = sha256_file(prep_stdout)
    proposal = ctx.shell.run("show-proposal", ["git", "-C", str(ctx.repo), "show", f"{gate.rel}:{PROPOSAL}"])
    if proposal.rc != 0:
        raise Stop("S-PRECHECK", f"proposal_unreadable rc={proposal.rc} (IR-OPS-1)")
    released = {m.group(2) for line in proposal.stdout.splitlines() if (m := G4_RELEASE_LINE.match(line))}
    ctx.recorder.event("g4_check", prep_stdout_sha256=prep_sha, release_lines=sorted(released))
    if prep_sha not in released:
        raise Stop("S-PRECHECK", f"g4_release_missing prep_stdout_sha256={prep_sha} (接受未明确放行；IR-OPS-1)")
    return prep_sha


# --- 第 0.3 节 来源核验（SOURCE:2） -------------------------------------------------------


def check_source_vars(data: bytes) -> dict[str, str]:
    """`src_check` 的同一判据：≤ 8,192 B，闭集变量各恰一次，值非空且逐字为 `shlex.quote` 形式。"""
    if not data or len(data) > 8192:
        raise Stop("S-PRECHECK", f"source_vars_size={len(data)}")
    values: dict[str, str] = {}
    for line in data.decode("utf-8").splitlines():
        key, sep, raw = line.partition("=")
        try:
            tokens = shlex.split(raw)
        except ValueError:
            tokens = []
        if not sep or key not in SRC_NAMES or key in values or len(tokens) != 1 or not tokens[0] or raw != shlex.quote(tokens[0]):
            raise Stop("S-PRECHECK", f"source_vars_bad_line {key!r}")
        values[key] = tokens[0]
    missing = [name for name in SRC_NAMES if name not in values]
    if missing:
        raise Stop("S-PRECHECK", "source_vars_missing " + " ".join(missing))
    return values


def source_check(ctx: Context) -> dict[str, str]:
    """附录 A 原文（mini 证据）解析 Air 现有原件；退出码 0、恰 10 行、末行 RESOLVE_OK；缺件即停、不复制。"""
    prep = ctx.out / "prep"
    prep.mkdir(parents=True, exist_ok=True)
    script = prep / "resolve-src.py"
    script.write_text(extract_block(ctx.repo / MINI_PREP_DOC, "## 附录 A 来源解析块", "python"), encoding="utf-8")
    env_path = prep / "source.env"
    run = ctx.shell.run("resolve-src", [ctx.python, "-I", "-B", str(script)], stdout_path=env_path)
    lines = run.stdout.splitlines()
    if run.rc != 0 or len(lines) != 10 or lines[-1] != "RESOLVE_OK":
        raise Stop("S-PRECHECK", f"source_resolve rc={run.rc} lines={len(lines)} last={lines[-1] if lines else ''}")
    vars_data = ("\n".join(lines[:-1]) + "\n").encode()
    values = check_source_vars(vars_data)
    (prep / "source.vars").write_bytes(vars_data)
    ctx.recorder.event("source_ok", source_env_sha256=sha256_file(env_path), names=sorted(values))
    return values


# --- 第 0.5 节 SSH 计次单元 ------------------------------------------------------------


class SshUnit:
    """一条认证主连接 + 有限通道；控制套接字失效即 `S-SSH`（按 `S-PRECHECK`），不回退新认证、不重试。"""

    def __init__(self, ctx: Context, unit: int):
        if unit not in CHANNELS:
            raise ValueError(unit)
        self.ctx, self.unit = ctx, unit
        ssh_dir = ctx.out / "ssh"
        ssh_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(ssh_dir, 0o700)
        self.cm = ssh_dir / f"cm-{unit}"
        self.tally = ssh_dir / f"unit-{unit}.tsv"
        self.used: list[str] = []
        self.opened_at: float | None = None
        self.open_ok = False

    def _tally(self, *fields: Any) -> None:
        with self.tally.open("a", encoding="utf-8") as handle:
            handle.write("\t".join(str(f) for f in ("unit", self.unit, *fields)) + "\n")

    def open(self) -> None:
        if self.cm.exists():
            raise Stop("S-PRECHECK", "stale_control_socket")
        self.ctx.ledger.take("ssh_units")
        self.opened_at = time.time()
        self._tally("master_attempt_epoch", f"{self.opened_at:.6f}")
        run = self.ctx.shell.run(f"ssh-master-{self.unit}", [
            self.ctx.ssh, "-o", "ControlMaster=yes", "-o", f"ControlPath={self.cm}", "-o", "ControlPersist=no",
            "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", "-fN", self.ctx.alias,
        ])
        self._tally("master_rc", run.rc, "epoch", f"{time.time():.6f}")
        if run.rc != 0:
            raise Stop("S-PRECHECK", f"ssh_master_failed rc={run.rc} (counted, no retry)")
        self.open_ok = True

    def _check_and_claim(self, name: str) -> None:
        allowed = CHANNELS[self.unit]
        if name not in allowed or name in self.used:
            raise Stop("S-PRECHECK", f"channel_outside_closed_set {name} unit={self.unit}")
        expected = allowed[len(self.used)]
        if name != expected:
            raise Stop("S-PRECHECK", f"channel_out_of_order {name} expected {expected}")
        check = self.ctx.shell.run(f"ssh-check-{name}", [self.ctx.ssh, "-S", str(self.cm), "-O", "check", self.ctx.alias])
        if check.rc != 0:
            raise Stop("S-PRECHECK", f"S-SSH control_socket_unavailable before {name}")
        self.used.append(name)

    def channel_argv(self, extra: Sequence[str], remote: str) -> list[str]:
        return [
            self.ctx.ssh, "-S", str(self.cm), "-o", "ControlMaster=no", "-o", "HostName=127.0.0.1", "-o", "Port=1",
            "-o", "ProxyCommand=none", "-o", "ProxyJump=none", "-o", "BatchMode=yes", "-o", "ConnectTimeout=3",
            *extra, self.ctx.alias, remote,
        ]

    def chan(self, name: str, remote: str, *, extra: Sequence[str] = ("-T",), stdin_path: Path | None = None,
             stdout_path: Path | None = None, timeout: float | None = None) -> Completed:
        self._check_and_claim(name)
        self._tally("channel", name, "start", f"{time.time():.6f}")
        run = self.ctx.shell.run(f"chan-{name}", self.channel_argv(extra, remote), stdin_path=stdin_path,
                                 stdout_path=stdout_path, timeout=timeout)
        self._tally("channel", name, "rc", run.rc, "end", f"{time.time():.6f}")
        return run

    def chan_popen(self, name: str, remote: str, *, extra: Sequence[str] = ("-tt",)) -> subprocess.Popen:
        self._check_and_claim(name)
        self._tally("channel", name, "start", f"{time.time():.6f}")
        argv = self.channel_argv(extra, remote)
        self.ctx.recorder.event("popen", name=f"chan-{name}", argv=argv)
        return subprocess.Popen(argv, cwd=self.ctx.repo, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def channel_done(self, name: str, rc: int | None) -> None:
        self._tally("channel", name, "rc", rc, "end", f"{time.time():.6f}")

    def close(self) -> None:
        if not self.open_ok:
            self._account()
            return
        run = self.ctx.shell.run(f"ssh-exit-{self.unit}", [self.ctx.ssh, "-S", str(self.cm), "-O", "exit", self.ctx.alias])
        self._tally("master_exit_rc", run.rc, "epoch", f"{time.time():.6f}")
        self._account()

    def _account(self) -> None:
        if self.opened_at is None:
            return
        wall = time.time() - self.opened_at
        self.ctx.ledger.add("ssh_wall_total_s", wall)
        self.ctx.recorder.event("unit_wall", unit=self.unit, wall_s=wall)
        if wall > LIMITS["unit_wall_s"] or self.ctx.ledger.used("ssh_wall_total_s") > LIMITS["ssh_wall_total_s"]:
            self.ctx.recorder.event("stop", code="S-ENVELOPE", detail=f"unit_wall_s={wall:.1f} recorded after the fact")


# --- 第 4 节 前台服务监督（ACTOR:1：代理/脚本持有可见前台 SSH 子进程） ---------------------------


LISTEN_LINE = re.compile(r"language-serve listening on http://(\S+)")
SERVE_RC_LINE = re.compile(r"^serve_rc=(\d+)$")


class ServeSession:
    """在 `serve` 通道的交互 bash 中逐行键入第 4 节命令；前台运行、Ctrl-C 正常停止、同会话核释放。"""

    def __init__(self, ctx: Context, unit: SshUnit, n: int, values: Mapping[str, str]):
        if n not in RESERVE_BY_UNIT:
            raise Stop("S-PRECHECK", f"bad_unit N={n}")
        self.ctx, self.unit, self.n, self.values = ctx, unit, n, dict(values)
        self.reserve = RESERVE_BY_UNIT[n]
        self.log_path = ctx.out / f"serve-channel-{n}.log"
        self.lines: list[str] = []
        self.cond = threading.Condition()
        self.proc: subprocess.Popen | None = None
        self.reader: threading.Thread | None = None
        self.started_unix_s: float | None = None
        self.stopped_unix_s: float | None = None
        self.serve_rc: int | None = None
        self.exited = False

    def startup_lines(self) -> list[str]:
        v = self.values
        exports = " ".join(f"{k}={shlex.quote(v[k])}" for k in ("WEIGHTS", "MMPROJ", "LLAMA_BIN"))
        return [
            # 关闭行编辑与回显：预先键入的命令不再回显进输出流，原流里的标记行（监听/serve_rc/释放核对）不被
            # 回显或括号粘贴控制序列夹杂（Ctrl-C 的 INTR 不受 -echo 影响）。
            "PS1=; PS2=; set -o pipefail; set +o emacs +o vi; stty -echo",
            f"N={self.n}",
            'case "$N" in 2) R_N=25 ;; 3) R_N=11 ;; *) echo "STOP S-PRECHECK bad_unit N=$N"; exit 97 ;; esac',
            f"cd {BOARD_CODE} || exit 97",
            'umask 077; date -u +%FT%TZ; echo "unit=$N reserve=$R_N"',
            f"export BOARD_ROOT={BOARD_ROOT} BOARD_CODE={BOARD_CODE} BOARD_LOGS={BOARD_LOGS} BOARD_TS={shlex.quote(str(self.ctx.board_ts))} {exports}",
            'mkdir -p "$BOARD_LOGS/tmp" "$BOARD_LOGS/cache/llama" "$BOARD_LOGS/cache/cuda" "$BOARD_LOGS/scratch" || exit 97',
            "SS=$(ss -ltn 2>&1); ss_rc=$?; printf '%s\\nss_rc=%s\\n' \"$SS\" \"$ss_rc\"",
            '[ "$ss_rc" -eq 0 ] && [ -n "$SS" ] || { echo "STOP S-PRECHECK ss_failed rc=$ss_rc"; exit 97; }',
            "PORTS=$(printf '%s\\n' \"$SS\" | awk '$4 ~ /:(18081|18082)$/ {print $4; f=1} END {exit f ? 0 : 1}'); port_rc=$?",
            'case "$port_rc" in 0) echo "STOP S-PRECHECK port_occupied $PORTS"; exit 97 ;; 1) echo PORTS_FREE_OK ;; *) echo "STOP S-PRECHECK port_check_failed rc=$port_rc"; exit 97 ;; esac',
            'pgrep -a -f llama-server; r1=$?; pgrep -a -f language_serve; r2=$?',
            '[ "$r1" -eq 1 ] && [ "$r2" -eq 1 ] || { echo "STOP S-PRECHECK residual_or_pgrep_rc=$r1/$r2"; exit 97; }',
            "env | grep -E '^(LLAMA_|GGML_|MTMD_|HF_|HUGGINGFACE_)|_proxy=|_PROXY='",
            "UNSETS=$(env | grep -E '^(LLAMA_|GGML_|MTMD_|HF_|HUGGINGFACE_)|_proxy=|_PROXY=' | cut -d= -f1 | sed 's/^/-u /' | tr '\\n' ' ')",
            (
                'env $UNSETS TMPDIR="$BOARD_LOGS/tmp" XDG_CACHE_HOME="$BOARD_LOGS/cache" LLAMA_CACHE="$BOARD_LOGS/cache/llama" '
                'CUDA_CACHE_PATH="$BOARD_LOGS/cache/cuda" CUDA_CACHE_MAXSIZE=134217728 '
                '/usr/bin/python3 -I -S -B tools/language_serve.py --backend llama-server '
                f'--llama-bin "$LLAMA_BIN" --weights "$WEIGHTS" --mmproj "$MMPROJ" --llama-port {LLAMA_PORT} '
                '--expect-assets "$BOARD_LOGS/expect-assets.json" --access-log "$BOARD_LOGS/access-$N.jsonl" '
                '--http-ledger "$BOARD_LOGS/http-ledger.jsonl" --non-inference-reserve "$R_N" '
                '--scratch "$BOARD_LOGS/scratch" --llama-ready-timeout-s 300 '
                f'--host "$BOARD_TS" --port {SERVE_PORT} 2>&1 | tee -i "$BOARD_LOGS/serve-$N.log"; '
                'echo "serve_rc=${PIPESTATUS[0]}"; date -u +%FT%TZ'
            ),
        ]

    RELEASE_LINES = (
        "SS=$(ss -ltn 2>&1); echo \"release_ss_rc=$?\"; printf '%s\\n' \"$SS\" | awk '$4 ~ /:(18081|18082)$/ {print \"LISTENING \" $4}'",
        'pgrep -a -f llama-server; echo "release_pgrep_llama_rc=$?"; pgrep -a -f language_serve; echo "release_pgrep_serve_rc=$?"',
        'du -sb "$BOARD_ROOT"; df -B1 /home/jetson; date -u +%FT%TZ; echo RELEASE_CHECK_DONE',
    )

    def _reader(self) -> None:
        assert self.proc is not None and self.proc.stdout is not None
        buffer = b""
        with self.log_path.open("ab") as log:
            while True:
                chunk = self.proc.stdout.read1(4096) if hasattr(self.proc.stdout, "read1") else self.proc.stdout.read(1)
                if not chunk:
                    break
                log.write(chunk)
                log.flush()
                buffer += chunk
                while b"\n" in buffer:
                    raw, buffer = buffer.split(b"\n", 1)
                    with self.cond:
                        self.lines.append(raw.decode("utf-8", errors="replace").strip("\r"))
                        self.cond.notify_all()
        with self.cond:
            if buffer:
                self.lines.append(buffer.decode("utf-8", errors="replace").strip("\r"))
            self.exited = True
            self.cond.notify_all()

    def type(self, text: str) -> None:
        assert self.proc is not None and self.proc.stdin is not None
        self.ctx.recorder.event("serve_typed", unit=self.n, text=text)
        try:
            self.proc.stdin.write(text.encode("utf-8") + b"\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            self.ctx.recorder.event("serve_type_failed", unit=self.n, error=str(error))

    def wait_for(self, predicate: Callable[[str], Any], timeout_s: float, *, start: int = 0) -> tuple[Any, int]:
        """返回 (首个 predicate 真值, 行号)；进程退出或超时返回 (None, 行数)。"""
        deadline = time.time() + timeout_s
        index = start
        with self.cond:
            while True:
                while index < len(self.lines):
                    value = predicate(self.lines[index])
                    index += 1
                    if value:
                        return value, index
                if self.exited or time.time() >= deadline:
                    return None, index
                self.cond.wait(timeout=min(0.2, max(0.0, deadline - time.time())))

    def start(self) -> None:
        self.ctx.ledger.take("serve_starts")
        self.ctx.ledger.take("version_calls")  # 启动自核 --version（第 0.4 节「--version / 身份」）
        self.proc = self.unit.chan_popen("serve", "exec bash --noprofile --norc -i")
        self.reader = threading.Thread(target=self._reader, daemon=True)
        self.reader.start()
        self.started_unix_s = time.time()
        for line in self.startup_lines():
            self.type(line)
        listen, _ = self.wait_for(lambda line: LISTEN_LINE.search(line) or SERVE_RC_LINE.match(line) or
                                  (line.startswith("STOP ") and line), LISTEN_WAIT_S)
        if isinstance(listen, re.Match) and listen.re is LISTEN_LINE:
            expected = f"{self.ctx.board_ts}:{SERVE_PORT}"
            if listen.group(1) != expected:
                raise Stop("S-IDENTITY", f"listening_on_unexpected_endpoint {listen.group(1)} != {expected}")
            self.ctx.recorder.event("serve_listening", unit=self.n, line=listen.group(0))
            return
        self._classify_early_exit(listen)

    def _classify_early_exit(self, value: Any) -> None:
        if isinstance(value, re.Match) and value.re is SERVE_RC_LINE:
            self.serve_rc = int(value.group(1))
        elif isinstance(value, str) and value.startswith("STOP "):
            self.finish_channel()
            parts = value.split()
            code = parts[1] if len(parts) > 1 and parts[1] in STOP_CODES else "S-PRECHECK"
            raise Stop(code, "serve_startup " + value)
        else:
            rc, _ = self.wait_for(lambda line: SERVE_RC_LINE.match(line), 5.0)
            self.serve_rc = int(rc.group(1)) if rc else None
        raise self.serve_exit_stop()

    def serve_exit_stop(self) -> Stop:
        rc = self.serve_rc
        if rc == 3:
            return Stop("S-IDENTITY", "serve_rc=3 assets/build/quantization/deploy/http-ledger mismatch")
        if rc == 6:
            return Stop("S-ENVELOPE", "serve_rc=6 non-inference HTTP budget")
        return Stop("S-BACKEND", f"first_main_arm_failure serve_rc={rc} (not ready/llama exited/unknown; restart 0)")

    def stop_and_release(self) -> dict[str, Any]:
        """Ctrl-C → 等 serve_rc → 同会话核端口/进程/磁盘 → exit；未释放 → `S-SERVICE`（照记，不清未知进程）。"""
        report: dict[str, Any] = {"unit": self.n}
        if self.proc is None:
            return report
        if self.serve_rc is None and not self.exited:
            self.ctx.recorder.event("serve_interrupt", unit=self.n)
            assert self.proc.stdin is not None
            try:
                self.proc.stdin.write(b"\x03")
                self.proc.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            rc, _ = self.wait_for(lambda line: SERVE_RC_LINE.match(line), SERVE_EXIT_WAIT_S)
            self.serve_rc = int(rc.group(1)) if rc else None
        self.stopped_unix_s = time.time()
        report["serve_rc"] = self.serve_rc
        report["residency_s"] = (self.stopped_unix_s - self.started_unix_s) if self.started_unix_s else None
        mark = len(self.lines)
        for line in self.RELEASE_LINES:
            self.type(line)
        done, end = self.wait_for(lambda line: line == "RELEASE_CHECK_DONE", 60.0, start=mark)
        window = self.lines[mark:end]
        ss_rc = next((l.split("=", 1)[1] for l in window if l.startswith("release_ss_rc=")), None)
        listening = [l for l in window if l.startswith("LISTENING ")]
        p1 = next((l.split("=", 1)[1] for l in window if l.startswith("release_pgrep_llama_rc=")), None)
        p2 = next((l.split("=", 1)[1] for l in window if l.startswith("release_pgrep_serve_rc=")), None)
        report.update(release_check_done=bool(done), ss_rc=ss_rc, listening=listening, pgrep_llama_rc=p1, pgrep_serve_rc=p2)
        released = bool(done) and ss_rc == "0" and not listening and p1 == "1" and p2 == "1"
        report["released"] = released
        self.finish_channel()
        self.ctx.ledger.add("residency_s", report["residency_s"] or 0.0)
        self.ctx.recorder.event("serve_release", **report)
        return report

    def finish_channel(self) -> None:
        if self.proc is None:
            return
        if not self.exited:
            self.type("exit")
        try:
            rc = self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            rc = None  # 不杀未知进程：照记 UNKNOWN（本机 ssh 客户端仍在则由 unit_close 关主连接）
        if self.reader is not None:
            self.reader.join(timeout=5)
        for stream in (self.proc.stdin, self.proc.stdout):
            try:
                if stream is not None:
                    stream.close()
            except OSError:
                pass
        self.unit.channel_done("serve", rc)


def identity_check(ctx: Context, unit: int, desktop_digest: str) -> dict[str, Any]:
    """第 4 节身份核对：必需 `/status` 计 1（不轮询）；六键齐、部署摘要相等、http_budget.batch = unit − 1。"""
    url = f"http://{ctx.board_ts}:{SERVE_PORT}/status"
    out_path = ctx.out / f"status-{unit}.json"
    run = ctx.shell.run(f"status-{unit}", ["curl", "-s", "--noproxy", "*", "--max-time", "5", url], stdout_path=out_path)
    try:
        document = json.loads(run.stdout)
    except ValueError:
        raise Stop("S-BACKEND", f"status_unreachable_or_invalid rc={run.rc} (first main-arm failure; stop all)")
    identity = document.get("model_identity") or {}
    missing = [k for k in bridge.LLAMA_IDENTITY_KEYS if not identity.get(k)]
    budget = document.get("http_budget") or {}
    problems = []
    if missing:
        problems.append("model_identity_missing " + ",".join(missing))
    if document.get("serve_code_sha256") != desktop_digest:
        problems.append("serve_code_sha256_mismatch")
    if budget.get("batch") != unit - 1:
        problems.append(f"http_budget_batch={budget.get('batch')} expected {unit - 1}")
    ctx.recorder.event("identity", unit=unit, machine=document.get("machine"), http_budget=budget, problems=problems)
    if problems:
        raise Stop("S-IDENTITY", "; ".join(problems))
    return document


def desktop_digest(ctx: Context) -> str:
    run = ctx.shell.run("deploy-digest", [ctx.python, "-m", "tools.eng_loop2.deploy_digest", "--root", "."])
    try:
        return str(json.loads(run.stdout)["serve_code_sha256"])
    except (ValueError, KeyError) as error:
        raise Stop("S-PRECHECK", f"deploy_digest_failed rc={run.rc}") from error


def resolve_board_ts(ctx: Context) -> str:
    run = ctx.shell.run("ssh-G", [ctx.ssh, "-G", ctx.alias])
    host = next((line.split()[1] for line in run.stdout.splitlines() if line.startswith("hostname ") and len(line.split()) > 1), None)
    if run.rc != 0 or not host:
        raise Stop("S-PRECHECK", "board_ts_unresolved")
    return host


# --- 计划（Play 前离线冻结；B/C 派生仅沿原离线预登记步骤） ------------------------------------------


BC_DOC_LINE = re.compile(r'\*\*(B|C)\*\* = `([^`]+)`，预登记描述 \*\*"([^"]+)"\*\*')
PLAN_STEP_KEYS = frozenset({"step_id", "kind", "action", "instruction", "intent", "delay_s", "description", "observe_s", "follow_s", "release_after"})


def build_plan(b: Mapping[str, str], c: Mapping[str, str], p2_object: str) -> dict[str, Any]:
    """第 9 节三剧本逐字展开（N-5 已批采样顺序；ask/respecify 每条都等本人发送/跳过）。"""
    red = {"intent": "red_car", "text": "the red car"}
    objects = {"red_car": red, "B": b, "C": c}
    if p2_object not in objects:
        raise Stop("S-PRECHECK", f"p2_object {p2_object!r} not in red_car/B/C")
    p2 = objects[p2_object]

    def step(sid: str, action: str, text: str, intent: str, description: str, *, delay: float | None = None,
             observe: float = 0.0, follow: float = 0.0, release: bool = False) -> dict[str, Any]:
        return {"step_id": sid, "kind": "designate", "action": action, "instruction": text, "intent": intent,
                "delay_s": delay, "description": description, "observe_s": observe, "follow_s": follow,
                "release_after": release}

    def stop(sid: str) -> dict[str, Any]:
        return {"step_id": sid, "kind": "stop", "action": "stop", "instruction": None, "intent": None, "delay_s": None,
                "description": None, "observe_s": 0.0, "follow_s": 0.0, "release_after": False}

    playbooks = {
        "P1": [
            step("P1-1", "ask", b["text"], b["intent"], b["text"], observe=15.0),
            step("P1-2", "ask", c["text"], c["intent"], c["text"], observe=15.0),
            step("P1-3", "ask", red["text"], red["intent"], red["text"], follow=20.0),
            step("P1-4", "ask", b["text"], b["intent"], b["text"], observe=15.0),
            stop("P1-5"),
        ],
        "P2": [
            step("P2-1", "ask", "the car", p2["intent"], p2["text"]),
            step("P2-2", "respecify", red["text"], red["intent"], red["text"], observe=15.0),
            stop("P2-3"),
        ],
        "P3": [
            step("P3-1", "ask", red["text"], red["intent"], red["text"], delay=0.0, observe=15.0, release=True),
            step("P3-2", "ask", red["text"], red["intent"], red["text"], delay=2.0, observe=15.0, release=True),
            step("P3-3", "ask", red["text"], red["intent"], red["text"], delay=4.0, observe=15.0),
            stop("P3-4"),
        ],
    }
    for steps in playbooks.values():
        for item in steps:
            if item["instruction"] is not None:
                bridge.parse_instruction(item["instruction"])  # 原文法；不合即抛（冻结前发现）
    return {"schema": PLAN_SCHEMA, "work_id": WORK_ID, "p2_object": p2_object, "playbooks": playbooks}


def freeze_plan(ctx: Context, p2_object: str) -> Path:
    """Play 前离线：运行原 `derive-bc`（独立进程），逐字核对操作单第 7 节，写冻结计划（无几何量）。"""
    plan_dir = ctx.out / "plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    derived = plan_dir / f"derive-bc-{utc_now()}.json"
    run = ctx.shell.run("derive-bc", [ctx.python, "-m", "tools.eng_loop2.analyze_play", "derive-bc", "--out", str(derived)])
    if run.rc != 0 or not derived.is_file():
        raise Stop("S-PRECHECK", f"derive_bc rc={run.rc} (得 < 2 辆即停并回接受)")
    document = json.loads(derived.read_text(encoding="utf-8"))
    if document.get("status") != "OK":
        raise Stop("S-PRECHECK", f"derive_bc status={document.get('status')}")
    sheet = {m.group(1): (m.group(2), m.group(3)) for m in BC_DOC_LINE.finditer((ctx.repo / PLAY_OPS_DOC).read_text(encoding="utf-8"))}
    chosen = {}
    for key in ("B", "C"):
        row = document.get(key) or {}
        name, text = row.get("scene_object_name"), row.get("description")
        if key not in sheet or sheet[key] != (name, text):
            raise Stop("S-PRECHECK", f"bc_differs_from_ops_sheet {key}: derived={(name, text)} sheet={sheet.get(key)} (回接受)")
        chosen[key] = {"intent": str(name), "text": str(text)}
    plan = build_plan(chosen["B"], chosen["C"], p2_object)
    plan["derive_bc_output_sha256"] = sha256_file(derived)
    path = plan_dir / "ops-plan.json"
    if path.exists():
        raise Stop("S-PRECHECK", "ops_plan_already_frozen (不改既有预登记)")
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    ctx.recorder.event("plan_frozen", path=str(path), sha256=sha256_file(path), p2_object=p2_object)
    return path


def load_plan(path: Path) -> tuple[dict[str, Any], str]:
    """在线只读冻结计划；键闭集外（例如几何量）即拒绝。"""
    data = Path(path).read_bytes()
    plan = json.loads(data)
    if plan.get("schema") != PLAN_SCHEMA:
        raise Stop("S-PRECHECK", "plan_schema")
    for steps in plan.get("playbooks", {}).values():
        for item in steps:
            if set(item) != PLAN_STEP_KEYS:
                raise Stop("S-PRECHECK", f"plan_step_keys {sorted(set(item) ^ PLAN_STEP_KEYS)}")
    return plan, hashlib.sha256(data).hexdigest()


# --- 原计划调度（在线；只看会话原流与冻结计划） ---------------------------------------------------


#: `HALTED`（C6@OpsK1K2K3K4 C6-1/C6-3）：请求已受理后被 STOP/故障/中断封住、不再推进；保留 request_id/回执/
#: 选择等已知事实，仍是样本（不改成未执行），结局只看会话原流。
TERMINAL_STEP = {"DONE", "SKIPPED_NOT_IN_VIEW", "REFUSED", "NO_CANDIDATE", "NO_DECISION", "NOT_EXECUTED", "UNKNOWN", "HALTED"}
PHASE_TEXT = {
    "await_send": "等待本人看实时画面后点「发送」或「跳过（不在画面）」；不点不发",
    "await_result": "已发送，等待会话呈现结果",
    "await_decision": "候选已呈现：按预登记描述恰一个相符点该序号，零/多个相符点拒绝",
    "observing": "观察计时中（沿会话原流事件锚点）",
}


class PlanScheduler:
    """O2：按冻结计划推进；ask/respecify 只在本人点「发送」后发出，「跳过」记 SKIPPED_NOT_IN_VIEW。

    不因 none/错误/拒绝/未 TRACKING 追加请求；无点击只等原截止/会话结束；release 只在 TRACKING 且
    track_id 仍等于该步建立的 track_id 时发；stop 计划末或中止至多一次（共用 `Submitter`）。
    结果未知（W4）即停止依赖推进，只剩停止会话与安全收尾。

    IR-OPS-6：NO_CANDIDATE / NO_DECISION / SKIPPED_NOT_IN_VIEW 不开观察窗、直接列下一步待本人发送/跳过；
    仅 confirm/reject 受理后观察 ≥ 15 s，锚点 = 该 request_id 的会话 receipt 写盘时刻（`at_unix_s`）；
    红车跟随 ≥ 20 s 从该选择之后**同纪元**首个 TRACKING 状态事件起，未进入则从选择时刻起并记跟随未验证。
    拒绝、未播种（confirm 受理但带拒收细节）或旧纪元的 TRACKING 一律不算新指定已跟随。原流缺失或
    不可绑定 → UNKNOWN 停依赖（`ANCHOR_WAIT_S`），不以 CLI 返回/点击/轮询时刻补值。
    """

    def __init__(self, steps: Sequence[Mapping[str, Any]], *, playbook: str, session_id: str, plan_sha256: str,
                 monitor: web.Monitor, submitter: web.Submitter, log: web.OpsLog, clock: Callable[[], float] = time.time):
        self.steps = [dict(s, status="PENDING", reason=None) for s in steps]
        self.playbook, self.session_id, self.plan_sha256 = playbook, session_id, plan_sha256
        self.monitor, self.submitter, self.log, self.clock = monitor, submitter, log, clock
        self.index = 0
        self.phase = "await_send"
        self.lock = threading.RLock()
        self._blocked: str | None = None
        self.halted: str | None = None
        self.finished = False
        self.operator_stop_request: str | None = None
        self.terminal_reason: str | None = None
        if self.steps:
            self.steps[0]["status"] = "AWAIT_SEND"
        else:
            self.finished = True

    # -- 封住（C6-1：STOP/故障/中断一发生即不可逆停业务；只剩原合法 stop 与安全收尾） --

    def halt(self, reason: str) -> None:
        """不可逆封住：共享提交通道封住本会话业务动作，计划不再推进（含观察/release/计划末 stop/下一步）。

        当前步若已有受理请求（已发送/待选择/观察中）记 `HALTED` 并保留 request_id/回执/选择；结果未知仍记
        `UNKNOWN`；其余未开始的步骤记 `NOT_EXECUTED`（原因 = 封住原因）。之后的迟到回执/状态只记录，不恢复。
        计划已正常走完时只封通道、不改任何步骤结局。
        """
        with self.lock:
            if self.halted is not None:
                return
            self.halted = reason
            self.submitter.seal(self.session_id, reason)
            self.log.write("plan_halted", reason=reason, finished=self.finished,
                           step_id=self.steps[self.index]["step_id"] if self.index < len(self.steps) else None)
            if self.finished:
                return
            self._block(f"HALTED {reason}")
            while self.index < len(self.steps):
                step = self.steps[self.index]
                status = step["status"]
                if status == "UNKNOWN":
                    self._close(step, "UNKNOWN", str(step.get("reason")), halted_by=reason)
                elif status in {"SENT", "AWAIT_DECISION", "OBSERVING"} or step.get("request_id"):
                    self._close(step, "HALTED", f"已受理后被封住（{reason}）：不再推进，结局见会话原流", halted_by=reason)
                else:
                    self._close(step, "NOT_EXECUTED", f"封住（{reason}）：未发送", halted_by=reason)
            self.finished = True

    def _step(self, step_id: Any) -> dict[str, Any] | None:
        return next((s for s in self.steps if s["step_id"] == step_id), None)

    def _late_reply(self, step_id: Any, what: str, reply: Mapping[str, Any]) -> None:
        """封住或计划已结束（会话 TERMINAL 先被处理）之后才返回的在途提交：只记事实（受理/拒收/未知），
        不推进、不解封；已受理的请求不留在「未执行」（C6-3）。"""
        step = self._step(step_id)
        if step is None:
            return
        outcome = (reply.get("receipt") or {}).get("outcome")
        after = f"封住于 {self.halted}" if self.halted is not None else f"计划已因 session_terminal:{self.terminal_reason} 结束"
        step.setdefault("late_replies", []).append({"what": what, "request_id": reply.get("request_id"), "outcome": outcome,
                                                     "unknown": bool(reply.get("unknown"))})
        if what == "send":
            step["request_id"] = step.get("request_id") or reply.get("request_id")
            step["send_receipt"] = reply.get("receipt")
            if reply.get("unknown"):
                step.update(status="UNKNOWN", reason=f"在途发送结果未知（{after}）")
            elif outcome in {"APPLIED", "PENDING_QUEUED"} and self.halted is not None:
                step.update(status="HALTED", reason=f"在途发送于封住后受理（{after}）：不再推进，结局见会话原流")
            elif outcome in {"APPLIED", "PENDING_QUEUED"}:
                step.update(status="NO_CANDIDATE", reason=f"已受理，回执晚于终止处理到达（{after}）")
            else:
                step.update(status="REFUSED", reason=f"会话拒收：{outcome}")
        self.log.write("late_reply_after_halt", step_id=step_id, what=what, request_id=reply.get("request_id"),
                       outcome=outcome, unknown=bool(reply.get("unknown")), status=step["status"])

    # -- 网页接口 --

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            current = None
            if not self.finished and self.index < len(self.steps):
                step = self.steps[self.index]
                current = {k: step.get(k) for k in ("step_id", "action", "instruction", "intent", "delay_s", "description")}
                current.update(phase=self.phase, phase_text=PHASE_TEXT.get(self.phase, self.phase))
            return {
                "playbook": self.playbook, "attempt": self.session_id, "plan_sha256": self.plan_sha256,
                "current": current, "decision_step": (current or {}).get("step_id") if self.phase == "await_decision" else None,
                "steps": [{k: s.get(k) for k in ("step_id", "action", "instruction", "status", "reason", "request_id")} for s in self.steps],
                "finished": self.finished,
            }

    def blocked(self) -> str | None:
        with self.lock:
            return self._blocked

    def current_send_step(self, step_id: Any) -> dict[str, Any] | None:
        with self.lock:
            if self.finished or self._blocked or self.halted is not None or self.index >= len(self.steps) or self.phase != "await_send":
                return None
            step = self.steps[self.index]
            if step["step_id"] != step_id or step["kind"] != "designate":
                return None
            return dict(step, attempt=self.session_id)

    def decision_step(self, request_id: Any) -> str | None:
        with self.lock:
            if self.finished or self.halted is not None or self.phase != "await_decision" or self.index >= len(self.steps):
                return None
            step = self.steps[self.index]
            return step["step_id"] if request_id and step.get("request_id") == request_id else None

    def record_skip(self, step_id: str, at: float) -> None:
        with self.lock:
            if self.halted is not None or self.finished or self.index >= len(self.steps):
                return  # 封住后不记跳过（网页侧已拒）；不改已关闭步骤
            step = self.steps[self.index]
            if step["step_id"] != step_id:
                return
            self._close(step, "SKIPPED_NOT_IN_VIEW", "本人点击跳过（不在画面）：未发请求、不成样本", skipped_unix_s=at)

    def record_send(self, step_id: str, reply: Mapping[str, Any]) -> None:
        with self.lock:
            if self.halted is not None or self.finished or self.index >= len(self.steps):
                self._late_reply(step_id, "send", reply)
                return
            step = self.steps[self.index]
            if step["step_id"] != step_id:
                return
            step["request_id"] = reply.get("request_id")
            step["send_receipt"] = reply.get("receipt")
            if reply.get("unknown"):
                step["status"] = "UNKNOWN"
                step["reason"] = reply.get("message")
                self._block(f"UNKNOWN request_id={reply.get('request_id')}（W4：停依赖推进，不自动重发）")
                return
            outcome = (reply.get("receipt") or {}).get("outcome")
            if outcome in {"APPLIED", "PENDING_QUEUED"}:
                step["status"] = "SENT"
                self.phase = "await_result"
                self.log.write("step_sent", step_id=step_id, request_id=step["request_id"], outcome=outcome)
                return
            self._close(step, "REFUSED", f"会话拒收：{outcome}")

    def record_decision(self, step_id: str, action: str, reply: Mapping[str, Any]) -> None:
        with self.lock:
            if self.halted is not None or self.finished or self.index >= len(self.steps):
                step = self._step(step_id)
                if step is not None:
                    step.setdefault("decisions", []).append({"action": action, "request_id": reply.get("request_id"),
                                                             "receipt": reply.get("receipt"), "unknown": reply.get("unknown"),
                                                             "after_halt": True})
                self._late_reply(step_id, action, reply)
                return
            step = self.steps[self.index]
            if step["step_id"] != step_id or self.phase != "await_decision":
                self._late_decision(step_id, action, reply)
                return
            step.setdefault("decisions", []).append({"action": action, "request_id": reply.get("request_id"),
                                                     "receipt": reply.get("receipt"), "unknown": reply.get("unknown")})
            if reply.get("unknown"):
                step["status"] = "UNKNOWN"
                step["reason"] = f"{action} 结果未知"
                self._block(f"UNKNOWN request_id={reply.get('request_id')}（W4：停依赖推进，不自动重发）")
                return
            if (reply.get("receipt") or {}).get("outcome") == "APPLIED":
                step["decision"] = action
                step["decision_request_id"] = reply.get("request_id")
                # 仅作等待原流写出的超时起点（IR-OPS-6），从不作为观察/跟随锚点。
                step["decided_cli_unix_s"] = self.clock()
                step["status"] = "OBSERVING"
                self.phase = "observing"
                self.log.write("step_decided", step_id=step_id, action=action, request_id=reply.get("request_id"))

    def _late_decision(self, step_id: Any, action: str, reply: Mapping[str, Any]) -> None:
        """R1-2：选择在该步已关闭（提交前窗口里呈现结束 → NO_DECISION）之后才返回：照记受理事实，从不静默丢弃。

        APPLIED 且该步是上一个关闭的 `NO_DECISION`、其后尚无任何发送/跳过时，恢复该步观察（锚点仍只取会话原流 receipt
        写盘时刻，IR-OPS-6）；否则（其后已有动作，或结果未知）该步记 `UNKNOWN` 并停依赖推进。拒收只记录。
        """
        step = self._step(step_id)
        if step is None:
            return
        outcome = (reply.get("receipt") or {}).get("outcome")
        step.setdefault("decisions", []).append({"action": action, "request_id": reply.get("request_id"),
                                                 "receipt": reply.get("receipt"), "unknown": reply.get("unknown"), "late": True,
                                                 "step_status_when_replied": step["status"]})
        self.log.write("late_decision", step_id=step_id, action=action, request_id=reply.get("request_id"), outcome=outcome,
                       unknown=bool(reply.get("unknown")), step_status=step["status"])
        if not reply.get("unknown") and outcome != "APPLIED":
            return
        position = self.steps.index(step)
        later = self.steps[position + 1:self.index + 1]
        untouched = all(s["status"] in {"PENDING", "AWAIT_SEND"} and not s.get("request_id") for s in later)
        if (not reply.get("unknown") and step["status"] == "NO_DECISION" and position == self.index - 1 and untouched
                and self.phase == "await_send"):
            if self.index < len(self.steps):
                self.steps[self.index]["status"] = "PENDING"
            self.index = position
            self.finished = False
            step.update(status="OBSERVING", reason=None, decision=action, decision_request_id=reply.get("request_id"),
                        decided_cli_unix_s=self.clock(), reopened_from="NO_DECISION")
            self.phase = "observing"
            self.log.write("step_reopened", step_id=step_id, action=action, request_id=reply.get("request_id"))
            return
        step.update(status="UNKNOWN", reason=f"{action} {'结果未知' if reply.get('unknown') else '已受理'}但该步已先关闭"
                                             f"（{step.get('reason')}）且之后已有动作：不能恢复观察")
        self._block(f"UNKNOWN late {action} request_id={reply.get('request_id')}（R1-2：停依赖推进）")

    def record_operator_stop(self, reply: Mapping[str, Any]) -> None:
        with self.lock:
            self.operator_stop_request = reply.get("request_id")
            if reply.get("unknown"):
                self._block(f"UNKNOWN stop request_id={reply.get('request_id')}")
            self.log.write("operator_stop", request_id=reply.get("request_id"), receipt=reply.get("receipt"))

    # -- 内部 --

    def _block(self, reason: str) -> None:
        if self._blocked is None:
            self._blocked = reason
            self.log.write("plan_blocked", reason=reason, step_id=self.steps[self.index]["step_id"] if self.index < len(self.steps) else None)
        # 结果未知/原流不可绑定同样不可逆封住共享通道的业务动作（W4 停依赖推进；只剩 stop 与收尾）。
        self.submitter.seal(self.session_id, self._blocked)

    def _close(self, step: dict[str, Any], status: str, reason: str, **fields: Any) -> None:
        step.update(status=status, reason=reason, **fields)
        self.log.write("step_closed", step_id=step["step_id"], status=status, reason=reason, **fields)
        self.index += 1
        self.phase = "await_send"
        if self.index < len(self.steps):
            self.steps[self.index]["status"] = "AWAIT_SEND"
        else:
            self.finished = True

    def _not_executed_rest(self, reason: str) -> None:
        """会话 TERMINAL：当前步按已受理事实收尾，其余未开始的步骤记 `NOT_EXECUTED`。

        R1@OpsK1K2K3K4 R1-1：与 `halt` 同口径——结果未知仍记 `UNKNOWN`；候选已呈现待选择（`AWAIT_DECISION`）或已带
        request_id 的步骤记 `HALTED`（仍是样本，request_id/回执保留）；只有确实未发送的步骤才是 `NOT_EXECUTED`。
        """
        while self.index < len(self.steps):
            step = self.steps[self.index]
            status = step["status"]
            if status in {"SENT", "OBSERVING"}:
                step["closed_by"] = reason
                self._close(step, "DONE" if status == "OBSERVING" else "NO_CANDIDATE", reason)
            elif status == "UNKNOWN":
                self._close(step, "UNKNOWN", f"{step.get('reason')}；{reason}（结果仍未知）", closed_by=reason)
            elif status == "AWAIT_DECISION" or step.get("request_id"):
                self._close(step, "HALTED", f"已受理后会话结束（{reason}）：不再推进，结局见会话原流", closed_by=reason)
            else:
                self._close(step, "NOT_EXECUTED", reason)
        self.finished = True

    def _unbound(self, step: dict[str, Any], what: str) -> None:
        """IR-OPS-6：原流缺失/不可绑定 → 该步 UNKNOWN、停依赖推进（不补值、不重发）。"""
        step["status"] = "UNKNOWN"
        step["reason"] = f"{what}：原流不可绑定（不以 CLI 返回/点击/轮询时刻补值）"
        self._block(f"UNKNOWN {what} step={step['step_id']}（IR-OPS-6：停依赖推进）")

    def _anchor(self, step: dict[str, Any]) -> float | None:
        """该选择 request_id 的会话 receipt 写盘时刻；`ANCHOR_WAIT_S` 内读不到 → UNKNOWN 停依赖。"""
        if "anchor_unix_s" in step:
            return step["anchor_unix_s"]
        record = self.monitor.receipt_record(str(step.get("decision_request_id")))
        if record and web.finite(record.get("at_unix_s")):
            step.update(anchor_unix_s=float(record["at_unix_s"]), anchor_source="journal_receipt",
                        anchor_epoch=record.get("epoch"), anchor_detail=record.get("detail"))
            self.log.write("step_anchor", step_id=step["step_id"], request_id=step.get("decision_request_id"),
                           anchor_unix_s=step["anchor_unix_s"], epoch=step["anchor_epoch"], detail=step["anchor_detail"])
            return step["anchor_unix_s"]
        if self.clock() - float(step.get("decided_cli_unix_s", self.clock())) > ANCHOR_WAIT_S:
            self._unbound(step, "selection_receipt_missing_in_journal")
        return None

    def _seeded_selection(self, step: dict[str, Any]) -> bool:
        """只有 confirm 受理且回执无拒收细节（例如 candidate_expired）才可能建立新指定的跟随。"""
        return step.get("decision") == "confirm" and step.get("anchor_detail") in (None, "")

    def _bind_tracking(self, step: dict[str, Any], state: Mapping[str, Any], anchor: float, now: float) -> None:
        epoch = step.get("anchor_epoch")
        if epoch is None:
            self._unbound(step, "selection_receipt_without_epoch")
            return
        events = [e for e in self.monitor.events_since(anchor)
                  if e.get("kind") == "state" and e.get("state") == "TRACKING" and e.get("epoch") == epoch]
        live = state.get("state") == "TRACKING" and state.get("epoch") == epoch and state.get("track_id")
        if events:
            if live:
                step.update(tracking_established=True, track_id=state.get("track_id"),
                            tracking_at_unix_s=float(events[0]["at_unix_s"]), tracking_at_source="journal_state",
                            tracking_epoch=epoch)
                self.log.write("step_tracking", step_id=step["step_id"], track_id=step["track_id"],
                               at_unix_s=step["tracking_at_unix_s"], epoch=epoch)
            return
        if live:
            # 状态槽已是同纪元 TRACKING，但会话原流里还没有对应事件：限时等待，超时 UNKNOWN（不拿轮询时刻补值）。
            seen = step.setdefault("tracking_unbound_seen_unix_s", now)
            if now - float(seen) > ANCHOR_WAIT_S:
                self._unbound(step, "tracking_state_without_journal_event")

    def tick(self) -> None:
        with self.lock:
            if self.finished:
                return
            now = self.clock()
            snap = self.monitor.public(now)
            state = snap.get("state") or {}
            if state.get("state") == "TERMINAL":
                self.terminal_reason = state.get("reason")
                self._not_executed_rest(f"session_terminal:{state.get('reason')}")
                return
            if self._blocked:
                return
            step = self.steps[self.index]
            if step["kind"] == "stop":
                self._send_stop(step)
                return
            if self.phase == "await_result":
                self._await_result(step, snap, state)
            elif self.phase == "await_decision":
                self._await_decision(step, snap, state, now)
            elif self.phase == "observing":
                self._observe(step, state, now)

    def _await_result(self, step: dict[str, Any], snap: Mapping[str, Any], state: Mapping[str, Any]) -> None:
        block = snap.get("presentation") or {}
        rid = step.get("request_id")
        if state.get("state") == "AWAITING_CONFIRMATION" and block.get("request_id") == rid and block.get("result_id"):
            step.update(result_id=block["result_id"], query_id=block.get("query_id"), result_status=block.get("status"),
                        status="AWAIT_DECISION")
            self.phase = "await_decision"
            self.log.write("step_presented", step_id=step["step_id"], request_id=rid, result_id=block["result_id"])
            return
        results = self.monitor.results_for(str(rid))
        if results and state.get("state") not in {"QUERYING", "AWAITING_CONFIRMATION"}:
            last = results[-1]
            if last.get("status") not in {"unique", "ambiguous"}:
                self._close(step, "NO_CANDIDATE", f"结果 {last.get('status')}（{last.get('reject_reason')}）：不追加请求",
                            result_status=last.get("status"), result_id=last.get("result_id"))

    def _await_decision(self, step: dict[str, Any], snap: Mapping[str, Any], state: Mapping[str, Any], now: float) -> None:
        block = snap.get("presentation") or {}
        if state.get("state") != "AWAITING_CONFIRMATION" or block.get("result_id") != step.get("result_id"):
            if self.submitter.in_flight.locked():
                return  # R1-2：一条选择可能已被会话受理、回执在途：等其先记入计划（下个 tick 再判，不是重试 CLI）
            self._close(step, "NO_DECISION", "呈现已结束（状态/结果已变）且无已受理的选择")
            return
        deadline = block.get("deadline_unix_s")
        if deadline is None and block.get("query_deadline_unix_s") is not None:
            deadline = min(block["query_deadline_unix_s"], block["presented_deadline_unix_s"])
        if deadline is not None and now > deadline and not self.submitter.in_flight.locked():
            self._close(step, "NO_DECISION", "原确认截止已过且本人未选择：不造事件、不默认拒绝、不重问")

    def _observe(self, step: dict[str, Any], state: Mapping[str, Any], now: float) -> None:
        anchor = self._anchor(step)
        if anchor is None:
            return
        if self._seeded_selection(step) and not step.get("tracking_established"):
            self._bind_tracking(step, state, anchor, now)
            if self._blocked:
                return
        duration = float(step.get("follow_s") or step.get("observe_s") or 0.0)
        if step.get("follow_s") and step.get("tracking_established"):
            end = float(step["tracking_at_unix_s"]) + duration
        else:
            end = anchor + duration
        if now < end:
            return
        step["observe_end_unix_s"] = now
        if step.get("release_after"):
            if self.submitter.in_flight.locked():
                return  # 另一提交在途：下个 tick 再判（不是重试 CLI）
            self._release(step, state)
            if step.get("release", {}).get("pending"):
                return
            if self._blocked:
                return
        if step.get("tracking_established"):
            note = "（本选择同纪元已建立 TRACKING）"
        elif step.get("decision") == "reject":
            note = "（本人拒绝：不建立跟随）"
        else:
            note = "（未建立本选择的 TRACKING：跟随未验证）"
        self._close(step, "DONE", "观察/跟随计时结束" + note, follow_verified=bool(step.get("tracking_established")))

    def _release(self, step: dict[str, Any], state: Mapping[str, Any]) -> None:
        if state.get("state") != "TRACKING" or not step.get("tracking_established") or state.get("track_id") != step.get("track_id"):
            step["release"] = {"sent": False, "reason": f"未发：state={state.get('state')} track={state.get('track_id')} 建立={step.get('track_id')}"}
            self.log.write("release_not_sent", step_id=step["step_id"], **step["release"])
            return
        key = json.dumps({"runner": "release", "step_id": step["step_id"], "attempt": self.session_id}, sort_keys=True)
        reply = self.submitter.submit(source="runner", action="release", session_id=self.session_id,
                                      binding={"step_id": step["step_id"], "track_id": state.get("track_id")},
                                      binding_key=key, token=str(state.get("track_id")))
        if reply.get("refused") and "在途" in str(reply.get("message")):
            step["release"] = {"pending": True}
            return
        step["release"] = {"sent": not reply.get("refused"), "request_id": reply.get("request_id"),
                           "outcome": (reply.get("receipt") or {}).get("outcome"), "message": reply.get("message")}
        if reply.get("unknown"):
            self._block(f"UNKNOWN release request_id={reply.get('request_id')}")

    def _send_stop(self, step: dict[str, Any]) -> None:
        if self.session_id in self.submitter.stop_sent:
            step["request_id"] = self.submitter.stop_sent[self.session_id]
            self._close(step, "DONE", "stop 已由中止按钮发出（每会话至多一次）")
            return
        key = json.dumps({"button": "stop", "session_id": self.session_id}, sort_keys=True)
        reply = self.submitter.submit(source="runner", action="stop", session_id=self.session_id,
                                      binding={"step_id": step["step_id"]}, binding_key=key)
        if reply.get("refused"):
            if self.session_id in self.submitter.stop_sent:
                step["request_id"] = self.submitter.stop_sent[self.session_id]
                self._close(step, "DONE", "stop 已由中止按钮发出（每会话至多一次）")
            return  # 在途：下个 tick
        step["request_id"] = reply.get("request_id")
        if reply.get("unknown"):
            step["status"] = "UNKNOWN"
            self._block(f"UNKNOWN stop request_id={reply.get('request_id')}")
            return
        self._close(step, "DONE", f"计划末 stop：{(reply.get('receipt') or {}).get('outcome')}")


# --- 归档（停 Play 后只移动不删除；不读文件内容） ----------------------------------------------------


def archive_attempt(repo: Path, out: Path, session_id: str, *, diagnostic_dest: Path | None = None,
                    include_layout: bool = True) -> dict[str, Any]:
    """第 12 节：把本次 Unity 帧环、`runtime/` 真值文件、段目录与布局副本移入 `$OUT/play/<SID>/unity-runtime`。

    只 `rename`（目标已存在即停，不覆盖），不打开/读取任何被移动文件；体积只用 `stat`。

    诊断模式（`diagnostic_dest`，IR-OPS-5 §4.1/§4.8；诊断页第 2 步与 6.4 同一口径）：把整个 `runtime/frames`、
    真值文件与（`include_layout` 时）布局覆盖文件**只移动**到给定目录（开工前移入 hold、Play 后移入本次段目录）；
    不碰 `runtime/runs/`（诊断段写在独立 `--diagnostics-root`），不做正式布局/体积门（体积由诊断粗账核）。
    """
    runtime = Path(repo) / "runtime"
    diagnostic = diagnostic_dest is not None
    dest = Path(diagnostic_dest) if diagnostic else Path(out) / "play" / session_id / "unity-runtime"
    dest.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    sources: list[Path] = []
    frames = runtime / "frames"
    if diagnostic:
        if frames.exists() or frames.is_symlink():
            sources.append(frames)
    elif frames.is_dir():
        sources += sorted(p for p in frames.iterdir() if re.fullmatch(r"frame_[0-9]{10}\.(jpg|json)", p.name))
        if (frames / "retained_frame_metadata").exists():
            sources.append(frames / "retained_frame_metadata")
    truth = runtime / "m3_body_truth.jsonl"
    if truth.exists():
        sources.append(truth)
    runs = runtime / "runs"
    if runs.is_dir() and not diagnostic:
        sources += sorted(p for p in runs.iterdir() if p.name.startswith(f"{session_id}-resident"))
    layout = runtime / "scenario_config.json"
    layout_present = layout.exists()
    if layout_present and include_layout:
        sources.append(layout)
    for source in sources:
        relative = source.relative_to(runtime)
        target = dest / relative
        if target.exists() or target.is_symlink():
            raise Stop("S-ARCHIVE", f"archive_target_exists {target}",
                       report={"session_id": session_id, "moved": list(moved), "partial": True, "dest": str(dest)})
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
        moved.append(str(relative))
    total = 0
    for path in dest.rglob("*"):
        if path.is_file():
            total += path.stat().st_size
    session_dir = Path(out) / "play" / "sessions" / session_id
    session_bytes = sum(p.stat().st_size for p in session_dir.rglob("*") if p.is_file()) if session_dir.is_dir() else 0
    report = {"session_id": session_id, "moved": moved, "unity_runtime_bytes": total, "session_bytes": session_bytes,
              "layout_copy_present": layout_present}
    if diagnostic:
        report["dest"] = str(dest)
        return report
    if not layout_present:
        raise Stop("S-ARCHIVE", f"layout_copy_missing {session_id} (layout_unbound)", report=report)
    if total + session_bytes > LIMITS["archive_per_play_bytes"]:
        raise Stop("S-ARCHIVE", f"archive_bytes={total + session_bytes} > 225 MB", report=report)
    return report


# --- 阶段实现 ------------------------------------------------------------------------


def stage_plan(ctx: Context, arguments: argparse.Namespace) -> int:
    path = freeze_plan(ctx, arguments.p2_object)
    print(f"PLAN_FROZEN {path} sha256={sha256_file(path)}")
    return 0


def stage_gate(ctx: Context, arguments: argparse.Namespace) -> int:
    result = release_gate(ctx)
    print(result.raw_path.read_text(encoding="utf-8"), end="")
    return 0 if result.ok else 3


def stage_source(ctx: Context, arguments: argparse.Namespace) -> int:
    values = source_check(ctx)
    print("SOURCE_LOAD_OK " + " ".join(sorted(values)))
    return 0


def air_preconditions(ctx: Context) -> None:
    """第 2 节 Air 本机零消耗前置（不连接）；任一失败即停、不开 SSH。"""
    for tool in ("ssh", "tar", "shasum", "curl", "du", "git"):
        if shutil.which(tool) is None and not (tool == "ssh" and Path(ctx.ssh).is_file()):
            raise Stop("S-PRECHECK", f"tool_missing {tool}")
    if (ctx.repo / "runtime" / "scenario_config.json").exists():
        ctx.recorder.event("note", text="RESIDUAL_OVERLAY_PRESENT（只记录；移动在收据单元 3.1）")
    smoke = ctx.shell.run("smoke-check", [ctx.python, "-I", "-c", (
        'import sys; sys.path.insert(0, "."); from tools.language_latency import read_smoke_rows; '
        'r = read_smoke_rows("outputs/eng-sft/P1-ENG-SFT-002/data/smoke.jsonl", "outputs/eng-sft/P1-ENG-SFT-002/upload"); '
        'assert len(r) == 32, len(r); print("SMOKE_OK", len(r))')])
    if smoke.rc != 0 or "SMOKE_OK 32" not in smoke.stdout:
        raise Stop("S-PRECHECK", "smoke_set")


def stage_prep(ctx: Context, arguments: argparse.Namespace) -> int:
    gate = require_gate(ctx, arguments.registered_release, need_registration=True)
    values = source_check(ctx)  # G5（SOURCE:2）
    air_preconditions(ctx)
    ctx.board_ts = resolve_board_ts(ctx)
    precheck = (ctx.repo / "docs/evidence/P1-ENG-LOOP-002-precheck.md").read_text(encoding="utf-8")
    tail = precheck.split("## Mac mini只读补核原始读数与逐维度用量", 1)
    exp_host = next((l.split("=", 1)[1] for l in (tail[1] if len(tail) == 2 else "").splitlines() if l.startswith("hostname=")), None)
    if not exp_host:
        raise Stop("S-PRECHECK", "exp_host_unresolved")
    body = extract_block(ctx.repo / PLAY_OPS_DOC, "## 附录 P 准备读脚本正文", "bash")
    prep = ctx.out / "prep"
    selected = [f"{k}={shlex.quote(values[k])}" for k in ("WEIGHTS", "MMPROJ", "LLAMA_BIN", "EXP_WEIGHTS_BYTES", "EXP_MMPROJ_BYTES", "EXP_LLAMA_BIN_BYTES")]
    script = prep / "prep-read.sh"
    script.write_text(f"EXP_HOST={shlex.quote(exp_host)}\n" + "\n".join(selected) + "\n" + body, encoding="utf-8")
    syntax = ctx.shell.run("bash-n", ["bash", "-n", str(script)])
    if syntax.rc != 0:
        raise Stop("S-PRECHECK", "prep_script_syntax")
    unit = SshUnit(ctx, 1)
    try:
        unit.open()
        run = unit.chan("prep-read", "timeout -k 5 900 bash -s", stdin_path=script, stdout_path=prep / "prep.stdout")
        (prep / "prep.stderr").write_text(run.stderr, encoding="utf-8")
    finally:
        unit.close()
    stops = [l for l in run.stdout.splitlines() if l.startswith("STOP ")]
    ctx.recorder.event("prep_done", rc=run.rc, stops=stops, prep_stdout_sha256=sha256_file(prep / "prep.stdout"), rel=gate.rel)
    if run.rc != 0 or stops:
        raise Stop("S-PRECHECK", f"prep_read rc={run.rc} {stops[:1]}")
    print(f"NEXT_GATE G4 prep_stdout_sha256={sha256_file(prep / 'prep.stdout')}（读齐即停，交接受核清；脚本不自签）")
    return 0


def move_residual_overlay(ctx: Context) -> None:
    overlay = ctx.repo / "runtime" / "scenario_config.json"
    if not overlay.exists():
        return
    hold = ctx.repo / "runtime" / "hold-acq-d1"
    hold.mkdir(parents=True, exist_ok=True)
    target = hold / "scenario_config.json"
    if target.exists():
        raise Stop("S-PRECHECK", "hold_target_exists (回接受)")
    ctx.ledger.take("residual_moves")
    overlay.rename(target)
    ctx.recorder.event("residual_moved", target=str(target))


def generate_overlay(ctx: Context, *, account: bool = True) -> str:
    """第 3 节第 2 步 / 诊断页第 5 步同一覆盖文件命令；`account=False` 只用于诊断（不进正式守账）。"""
    if account:
        ctx.ledger.take("overlay_generations")
    run = ctx.shell.run("overlay-gen", [ctx.python, "-c", (
        "import json;d=json.load(open('config/scenario.untethered.json'));d['sensor']['retained_frame_count']=1500;"
        "open('runtime/scenario_config.json','w').write(json.dumps(d,indent=2)+'\\n')")])
    if run.rc != 0:
        raise Stop("S-PRECHECK", f"overlay_gen rc={run.rc}")
    digest = sha256_file(ctx.repo / "runtime" / "scenario_config.json")
    ctx.recorder.event("overlay", sha256=digest)
    return digest


def stage_receipt(ctx: Context, arguments: argparse.Namespace) -> int:
    gate = require_gate(ctx, arguments.registered_release, need_registration=True)
    values = source_check(ctx)
    require_g4(ctx, gate)
    ctx.board_ts = resolve_board_ts(ctx)
    b0b = ctx.out / "b0b"
    b0b.mkdir(parents=True, exist_ok=True)
    digest = desktop_digest(ctx)
    unit = SshUnit(ctx, 2)
    serve: ServeSession | None = None
    outcome: dict[str, Any] = {"measure_rc": None, "k_receipt_rc": None}
    failure: Stop | None = None
    try:
        unit.open()
        move_residual_overlay(ctx)  # 第 3 节第 1 步（Air）
        generate_overlay(ctx)  # 第 3 节第 2 步（Air）
        root = unit.chan("root-create", f"test ! -e '{BOARD_ROOT}' && test ! -L '{BOARD_ROOT}' && mkdir -m 700 '{BOARD_ROOT}' '{BOARD_CODE}' '{BOARD_LOGS}' && echo ROOT_CREATED")
        if "ROOT_CREATED" not in root.stdout.split():
            raise Stop("S-PRECHECK", "root_create (已存在或失败；不覆盖、不删)")
        ctx.ledger.take("version_calls")
        raw = b0b / "assets-raw.txt"
        unit.chan("assets", f"sha256sum -- '{values['WEIGHTS']}' '{values['MMPROJ']}' '{values['LLAMA_BIN']}'; '{values['LLAMA_BIN']}' --version 2>&1; echo rc=$?", stdout_path=raw)
        gen_script = ctx.out / "prep" / "assets-gen.py"
        gen_script.write_text(extract_block(ctx.repo / MINI_PREP_DOC, "## 附录 B 资产 JSON 生成块", "python"), encoding="utf-8")
        gen = ctx.shell.run("assets-gen", [ctx.python, "-I", "-B", str(gen_script), str(raw), str(b0b / "assets.json")], env=values)
        last = gen.stdout.strip().splitlines()[-1:] or [""]
        if gen.rc != 0 or last[0] != "ASSETS_OK":
            code = "S-PRECHECK" if "source_vars_missing" in gen.stdout else "S-IDENTITY"
            raise Stop(code, f"assets_gen rc={gen.rc} {last[0]}")
        paths = json.loads((ctx.repo / "config/p1-eng-loop-002-board-deploy.json").read_text(encoding="utf-8"))["paths"]
        tar_path = b0b / "deploy.tar"
        if ctx.shell.run("deploy-tar-create", ["tar", "-cf", str(tar_path), *paths]).rc != 0:
            raise Stop("S-PRECHECK", "deploy_tar_create")
        shutil.copyfile(b0b / "assets.json", b0b / "expect-assets.json")
        batch_bytes = tar_path.stat().st_size + (b0b / "expect-assets.json").stat().st_size
        ctx.ledger.take("transfer_batches")
        ctx.ledger.take("transfer_bytes", batch_bytes)
        if unit.chan("deploy-tar", f"tar -xf - -C '{BOARD_CODE}'", stdin_path=tar_path).rc != 0:
            raise Stop("S-PRECHECK", "deploy_tar")
        if unit.chan("deploy-expect", f"cat > '{BOARD_LOGS}/expect-assets.json'", stdin_path=b0b / "expect-assets.json").rc != 0:
            raise Stop("S-PRECHECK", "deploy_expect")
        air = ctx.shell.run("air-sha", ["shasum", "-a", "256", *paths], stdout_path=b0b / "air.sha")
        quoted = " ".join(shlex.quote(p) for p in paths)
        board = unit.chan("deploy-verify", f"cd '{BOARD_CODE}' || exit 97; sha256sum -- {quoted}; du -sb '{BOARD_ROOT}'; df -B1 /home/jetson",
                          stdout_path=b0b / "board-verify.txt")
        board_sha = [l for l in board.stdout.splitlines() if re.match(r"^[0-9a-f]{64}  ", l)]
        if air.rc != 0 or board.rc != 0 or board_sha != air.stdout.splitlines():
            raise Stop("S-IDENTITY", "deploy_sha_mismatch")
        serve = ServeSession(ctx, unit, 2, values)
        serve.start()
        identity_check(ctx, 2, digest)
        outcome.update(run_measure_and_receipt(ctx))
    except Stop as stop:
        failure = stop
    finally:
        release = serve.stop_and_release() if serve is not None and serve.proc is not None else None
        if serve is not None and serve.proc is not None and unit.open_ok:
            fetch_logs(ctx, unit, 2)
        unit.close()
    outcome["release"] = release
    (ctx.out / "receipt-outcome.json").write_text(json.dumps(outcome, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if failure is not None:
        raise failure
    if release is not None and not release.get("released"):
        raise Stop("S-SERVICE", "release_not_proven (照记 UNKNOWN；不清未知进程)")
    if outcome.get("k_receipt_rc") != 0:
        raise Stop("S-RECEIPT", f"k_receipt_rc={outcome.get('k_receipt_rc')}")
    print("RECEIPT_OK k_receipt_rc=0（单元 #2 已收尾）")
    return 0


def fetch_logs(ctx: Context, unit: SshUnit, n: int) -> None:
    """日志回传（传输批次 2/3；服务停止后）。批次额度不足只照记、不发（不跨维度借）。"""
    try:
        ctx.ledger.take("transfer_batches")
    except Stop as stop:
        ctx.recorder.event("stop", code=stop.code, detail="logs not fetched: " + stop.detail)
        return
    target = ctx.out / f"board-logs-{n}.tar"
    unit.chan(f"logs-{n}", f"tar -cf - -C '{BOARD_LOGS}' access-{n}.jsonl serve-{n}.log http-ledger.jsonl expect-assets.json",
              stdout_path=target)
    ctx.ledger.add("transfer_bytes", target.stat().st_size if target.is_file() else 0)
    if ctx.ledger.used("transfer_bytes") > LIMITS["transfer_bytes"]:
        ctx.recorder.event("stop", code="S-ENVELOPE", detail="transfer_bytes over limit (recorded after the fact)")


def measure_argv(ctx: Context, report: Path) -> list[str]:
    """第 5 节 / 诊断页第 5 步同一生产 measure 命令（固定 3 预热 + 32 计时由生产代码决定）。"""
    return [
        ctx.python, "-m", "tools.language_latency", "measure", "--host", "jetson", "--backend", "http",
        "--server-url", f"http://{ctx.board_ts}:{SERVE_PORT}", "--model-form", "c2-merged",
        "--smoke", "outputs/eng-sft/P1-ENG-SFT-002/data/smoke.jsonl", "--package-root", "outputs/eng-sft/P1-ENG-SFT-002/upload",
        "--runtime", "runtime", "--out", str(report)]


def k_receipt_argv(ctx: Context, report: Path, out: Path) -> list[str]:
    return [ctx.python, "-m", "tools.language_latency", "k-receipt", "--single-host", "jetson", "--report", str(report),
            "--runtime", "runtime", "--out", str(out)]


def first_measure_failure(report: Path) -> Any:
    try:
        document = json.loads(Path(report).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    failures = [x for rd in document.get("rounds", []) for x in rd.get("failures", [])]
    return failures[0] if failures else None


def run_measure_and_receipt(ctx: Context) -> dict[str, Any]:
    """第 5 节：measure 非 0 即停、不跑 k-receipt；k-receipt 只认 0，6/8 → S-RECEIPT。收据重测 0。"""
    out = ctx.out / "k-receipt"
    out.mkdir(parents=True, exist_ok=True)
    report = out / "jetson-report.json"
    measure = ctx.shell.run("measure", measure_argv(ctx, report), stdout_path=out / "measure.stdout")
    (out / "measure.stderr").write_text(measure.stderr, encoding="utf-8")
    result: dict[str, Any] = {"measure_rc": measure.rc}
    if measure.rc != 0:
        first = first_measure_failure(report)
        result["first_failure"] = first
        if measure.rc == 7 and str((first or {}).get("detail", "")).startswith("S_ENVELOPE"):
            raise Stop("S-ENVELOPE", "measure_rc=7 first failure S_ENVELOPE")
        raise Stop("S-BACKEND", f"measure_rc={measure.rc} first main-arm failure; no k-receipt, no Play")
    receipt = ctx.shell.run("k-receipt", k_receipt_argv(ctx, report, out / "jetson-k-receipt.json"),
                            stdout_path=out / "k-receipt.stdout")
    (out / "k-receipt.stderr").write_text(receipt.stderr, encoding="utf-8")
    result["k_receipt_rc"] = receipt.rc
    if receipt.rc != 0:
        raise Stop("S-RECEIPT", f"k_receipt_rc={receipt.rc}")
    return result


def wait_for_play(repo: Path, since: float, timeout_s: float, clock: Callable[[], float] = time.time) -> int | None:
    """本人按 Play 后出帧：`latest.json` 指向的帧旁车 `capture_unix_s` 晚于 `since`；返回 f₀（不是按钮时刻）。"""
    deadline = clock() + timeout_s
    while clock() < deadline:
        frame_id = frame_since(repo, since)
        if frame_id is not None:
            return frame_id
        time.sleep(0.25)
    return None


def frame_since(repo: Path, since: float) -> int | None:
    """一次只读检查：`latest.json` 指向的帧旁车 `capture_unix_s` 晚于 `since` 则返回其帧号（出帧事实，不是按钮时刻）。"""
    frames = Path(repo) / "runtime" / "frames"
    latest = web.read_json(frames / "latest.json")
    if isinstance(latest, dict) and isinstance(latest.get("frame_id"), int):
        meta = web.read_json(frames / f"frame_{latest['frame_id']:010d}.json")
        captured = (meta or {}).get("capture_unix_s") if isinstance(meta, dict) else None
        if web.finite(captured) and float(captured) > since:
            return int(latest["frame_id"])
    return None


def wait_unity_stopped(repo: Path, quiet_s: float, hard_deadline: float) -> tuple[bool, int | None]:
    """出帧停止 `quiet_s` 秒视为本人已停 Play（记「末次出帧」，不冒充按钮时刻）；超 `hard_deadline` 返回 False。"""
    frames = Path(repo) / "runtime" / "frames"
    last_id, last_change = None, time.time()
    while time.time() < hard_deadline:
        latest = web.read_json(frames / "latest.json")
        frame_id = latest.get("frame_id") if isinstance(latest, dict) else None
        if frame_id != last_id:
            last_id, last_change = frame_id, time.time()
        elif time.time() - last_change >= quiet_s:
            return True, last_id
        time.sleep(0.25)
    return False, last_id


def classify_terminal(reason: str | None, journal: Path) -> Stop | None:
    """O3：会话 TERMINAL 原因 → 原 STOP；S-REBUILD 不能机械证明属允许继续闭集 → UNKNOWN 停全部。"""
    if reason in {"operator_stop", "duration_reached"}:
        return None
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.is_file() else ""
    if reason == "backend_fatal":
        records = []
        for line in text.splitlines():
            try:
                records.append(json.loads(line))
            except ValueError:
                continue
        envelope = any("S_ENVELOPE" in json.dumps(r, ensure_ascii=False) for r in records
                       if isinstance(r, dict) and r.get("kind") == "backend_fatal")
        return Stop("S-ENVELOPE" if envelope else "S-BACKEND", "session TERMINAL(backend_fatal)")
    if reason == "rebuild_limit":
        return Stop("S-REBUILD", "TERMINAL(rebuild_limit)：不能机械证明属 A5 非主臂允许继续闭集 → UNKNOWN，停全部交接受")
    return Stop("S-BACKEND", f"TERMINAL({reason}) 原因不在已知闭集 → UNKNOWN 停全部")


def model_loads_ok(repo: Path, session_id: str) -> list[int]:
    loads = []
    for path in sorted((Path(repo) / "runtime" / "runs").glob(f"{session_id}-resident*/model_cache.json")):
        document = web.read_json(path) or {}
        loads.append(int(document.get("model_loads", -1)))
    return loads


def session_argv(ctx: Context, session_id: str, session_root: Path, receipt_path: Path, t_sess: float,
                 diagnostics_root: Path | None = None) -> list[str]:
    """第 9 节 / 诊断页 6.1 同一会话命令；诊断另列 `--diagnostic` 与独立 `--diagnostics-root`（IR-OPS-5 §4.1）。"""
    head = [ctx.python, "-m", "controller.language_loop", "run"]
    if diagnostics_root is not None:
        head.append("--diagnostic")
    argv = head + [
        "--session-id", session_id, "--session-root", str(session_root),
    ]
    if diagnostics_root is not None:
        argv += ["--diagnostics-root", str(diagnostics_root)]
    return argv + [
        "--runtime", "runtime", "--allow-shared-runtime", "--backend", "http", "--server-url", f"http://{ctx.board_ts}:{SERVE_PORT}",
        "--model-form", "c2-merged", "--k-receipt", str(receipt_path), "--tracker", "det-assoc-v1", "--resident",
        "--condition", "follow", "--ground-plane-y-m", "0.2", "--body-policy", "standoff",
        "--body-planner-config", "config/p1-eng-frame-001-body.json", "--body-scenario-config", "runtime/scenario_config.json",
        "--scenario-id", "deterministic-loop-untethered", "--planned-duration-s", f"{t_sess:.3f}",
    ]


def send_session_stop(submitter: web.Submitter, session_id: str, why: str) -> dict[str, Any] | None:
    """沿共享原 CLI 通道发本会话 stop（与网页中止按钮、计划末 stop 同一绑定）：每会话至多一次，已发即返回 None。

    「在途被拒」（另一提交尚未返回）没有发送，由调用方在等待窗口内再试；结果未知不换 id、不重发（W4）。
    """
    if session_id in submitter.stop_sent:
        return None
    key = json.dumps({"button": "stop", "session_id": session_id}, sort_keys=True)
    return submitter.submit(source="runner", action="stop", session_id=session_id, binding={"why": why}, binding_key=key)


def stop_and_wait_session(submitter: web.Submitter, session_id: str, process: subprocess.Popen, why: str,
                          record: dict[str, Any]) -> bool:
    """C6-2：发原 stop（至多一次）后等会话进程自行退出 ≤ `SESSION_STOP_WAIT_S`；到时仍运行返回 False（不杀进程）。"""
    deadline = time.time() + SESSION_STOP_WAIT_S
    while process.poll() is None and time.time() < deadline:
        if session_id not in submitter.stop_sent and not submitter.in_flight.locked():
            reply = send_session_stop(submitter, session_id, why)
            if reply is not None and not reply.get("refused"):
                record["closeout_stop"] = {"request_id": reply.get("request_id"), "unknown": bool(reply.get("unknown")),
                                           "outcome": (reply.get("receipt") or {}).get("outcome"), "message": reply.get("message")}
                deadline = max(deadline, time.time() + SESSION_STOP_WAIT_S)
        time.sleep(TICK_S)
    if session_id in submitter.stop_sent:
        record["stop_request_id"] = submitter.stop_sent[session_id]
    return process.poll() is not None


def not_executed_steps(steps: Sequence[Mapping[str, Any]], reason: str) -> list[dict[str, Any]]:
    """会话未启动时的逐步记录：确实未执行（与「记录缺失/未知」分列；C6-3）。"""
    return [{"step_id": s.get("step_id"), "action": s.get("action"), "instruction": s.get("instruction"),
             "status": "NOT_EXECUTED", "reason": reason, "request_id": None} for s in steps]


def describe_failure(error: BaseException | None) -> dict[str, Any] | None:
    """尝试/阶段失败的记录形态：原 11 码原样；Ctrl-C 与不明异常记 UNKNOWN（STOP:9：停依赖、交接受，不自动重试）。"""
    if error is None:
        return None
    if isinstance(error, Stop):
        return {"code": error.code, "detail": error.detail}
    if isinstance(error, UnknownOutcome):
        return {"code": "UNKNOWN", "detail": error.detail}
    if isinstance(error, KeyboardInterrupt):
        return {"code": "UNKNOWN", "detail": "operator Ctrl-C（中断；已做已签安全收尾，停全部后续交接受）"}
    return {"code": "UNKNOWN", "detail": f"unexpected {type(error).__name__}: {error}（不明故障；停全部后续交接受）"}


def run_attempt(ctx: Context, app: web.App, submitter: web.Submitter, plan: Mapping[str, Any], plan_sha: str,
                playbook: str, receipt_path: Path, receipt: Mapping[str, float], registered: Path | None,
                record: dict[str, Any] | None = None) -> dict[str, Any]:
    """一个剧本（一次 Play / 一个 session）；STOP 抛出。

    `record` 由调用方持有、在此原地填写：任何退出路径（STOP/故障/Ctrl-C）都保留已产生的实际步骤、request_id、
    rc、终止原因、可得时刻、加载与归档指针（C6-3），并先经 `attempt_closeout` 的已签安全收尾再抛出（C6-2）。

    工具截止 = 开始等待本人 Play 的时刻 + 420 s（按钮墙钟上限；**等待 Play 不延长它**）。按钮起止无可靠来源，
    照记 UNKNOWN；截止时会话或出帧仍未停 → `S-WALL`（不能证明 ≤ 420 s，fail-closed）。
    """
    record = {} if record is None else record
    session_id = SESSION_IDS[playbook]
    planned = plan["playbooks"][playbook]
    record.update(playbook=playbook, session_id=session_id, play_button_times="UNKNOWN（出帧/TERMINAL 不冒充按钮时刻）",
                  steps=not_executed_steps(planned, "会话未启动"))
    found: list[BaseException] = []
    process: subprocess.Popen | None = None
    monitor: web.Monitor | None = None
    scheduler: PlanScheduler | None = None
    waiting_since: float | None = None
    deadline: float | None = None
    try:
        require_gate(ctx, registered, need_registration=True)  # 第 1 节：每次 Play 前再核一次
        ctx.ledger.take("plays")
        ctx.ledger.take("sessions")
        record["play_and_session_counted"] = True
        record["overlay_sha256"] = generate_overlay(ctx)
        waiting_since = time.time()
        deadline = waiting_since + LIMITS["play_wall_s"]
        record.update(play_wait_started_unix_s=waiting_since, tool_deadline_unix_s=deadline,
                      tool_deadline_rule="等待本人 Play 起点 + 420 s（等待 Play 不延长按钮墙钟；按钮起止 UNKNOWN）")
        print(f"等待本人在 Unity 按 Play（{playbook}，{session_id}）；会话与出帧须在 {LIMITS['play_wall_s']:.0f} s 内结束……", flush=True)
        f0 = wait_for_play(ctx.repo, waiting_since, PLAY_START_WAIT_S)
        record["first_frame_seen_unix_s"] = time.time()
        if f0 is None:
            record["env_failure"] = "unity_not_in_play"
            raise Stop("S-PRECHECK", "Unity 未进 Play（环境性原因；IR-OPS-4：新入口无重试路径，停依赖、收尾交用户/接受）")
        t_sess = min(LIMITS["t_sess_s"], (1490 - f0) / 5.0)
        record.update(f0=f0, t_sess_s=t_sess, t_sess_formula="min(290, (1490 - f0) / 5)")
        if t_sess <= 0:
            raise Stop("S-PRECHECK", f"t_sess_nonpositive f0={f0}")
        session_root = ctx.out / "play" / "sessions"
        session_root.mkdir(parents=True, exist_ok=True)
        argv = session_argv(ctx, session_id, session_root, receipt_path, t_sess)
        log_path = ctx.out / "play" / f"{session_id}.session-process.log"
        ctx.recorder.event("session_start", session_id=session_id, argv=argv)
        with log_path.open("ab") as log:
            process = subprocess.Popen(argv, cwd=ctx.repo, stdout=log, stderr=subprocess.STDOUT)
        record["session_started_unix_s"] = time.time()
        monitor = app.bind_session(session_id, session_root / session_id)
        scheduler = PlanScheduler(planned, playbook=playbook, session_id=session_id, plan_sha256=plan_sha,
                                  monitor=monitor, submitter=submitter, log=app.log)
        app.scheduler = scheduler
        while process.poll() is None:
            try:
                monitor.poll()
            except Exception as error:  # 读不到就不推进
                monitor.fail(error)
            scheduler.tick()
            if time.time() > deadline:
                raise Stop("S-WALL", f"{session_id} 会话在工具截止（等待 Play 起点 + 420 s）仍在运行：按钮墙钟不能证明 ≤ 420 s，"
                                     "停本次及全部后续")
            time.sleep(TICK_S)
    except BaseException as error:  # noqa: BLE001 - 任何退出路径都先安全收尾（C6-2），记录后再抛
        found.append(error)
        if isinstance(error, Stop) and error.report:
            record.setdefault("failure_report", error.report)
    attempt_closeout(ctx, record, submitter, session_id, planned, process, monitor, scheduler, waiting_since, deadline, found)
    record["stops_all"] = [describe_failure(error) for error in found]
    record["stop"] = record["stops_all"][0] if found else None
    if found:
        raise found[0]
    return record


def attempt_closeout(ctx: Context, record: dict[str, Any], submitter: web.Submitter, session_id: str,
                     planned: Sequence[Mapping[str, Any]], process: subprocess.Popen | None, monitor: web.Monitor | None,
                     scheduler: PlanScheduler | None, waiting_since: float | None, deadline: float | None,
                     found: list[BaseException]) -> None:
    """C6-1/C6-2/C6-3：单次尝试的安全收尾，正常与失败同一路径；每步独立记录，一步失败（含 Ctrl-C）不跳过其余。

    顺序：封住业务（失败或会话仍在运行时立即）→ 原 stop（至多一次）并等会话退出 → 末次读原流、逐步记录 →
    提示本人停 Play 并等出帧静止 → 加载计数 → 只移动归档（会话或 Unity 未确认停止则不移动、照记 UNKNOWN）→
    原因码分流。不杀进程、不清锁、不伪造按钮时刻；收尾中发现的 STOP 追加在触发失败之后，全部入记录。
    """
    closeout = record.setdefault("closeout", {})
    first = describe_failure(found[0]) if found else None
    why = first["code"] + " " + first["detail"] if first else "attempt closeout"

    def failed(name: str, error: BaseException) -> None:
        closeout[name] = ("interrupted（Ctrl-C；继续其余安全收尾）" if isinstance(error, KeyboardInterrupt)
                          else f"{type(error).__name__}: {error}")
        # R1-3：收尾内任何失败（含 Ctrl-C/OSError）都进 found → 记 UNKNOWN、非 0 退出、停后续剧本（不被吞）。
        found.append(error)

    # 1. 封住 + 原 stop + 等会话
    try:
        running = process is not None and process.poll() is None
        if found or running:
            if scheduler is not None:
                scheduler.halt(why)
            else:
                submitter.seal(session_id, why)
            record["halted"] = why
        if running:
            assert process is not None
            if not stop_and_wait_session(submitter, session_id, process, why, record):
                record["session_process"] = "still_running_after_stop_wait（不杀进程；退出未证明 → UNKNOWN）"
        closeout["session"] = "done"
    except BaseException as error:  # noqa: BLE001
        failed("session", error)
    # 2. 末次读原流与逐步记录（先持有共享在途锁：在途提交及其计划记录必先完成，之后的新提交一律在途被拒）
    try:
        if monitor is not None and scheduler is not None:
            held = submitter.in_flight.acquire(timeout=web.CLI_TIMEOUT_S + 5.0)
            record["in_flight_quiesced"] = held
            try:
                try:
                    monitor.poll()
                except Exception as error:  # noqa: BLE001
                    monitor.fail(error)
                scheduler.tick()
                scheduler.halt("attempt closeout")  # 计划已走完时只封通道；未走完（进程无 TERMINAL 退出）则封住并分列
            finally:
                if held:
                    submitter.in_flight.release()
            state = (monitor.public(time.time()).get("state") or {})
            record["terminal_reason"] = state.get("reason") if state.get("state") == "TERMINAL" else None
            record["steps"] = scheduler.snapshot()["steps"]
            with scheduler.lock:
                record["steps_detail"] = json.loads(json.dumps(scheduler.steps, default=str))
            record["blocked"] = scheduler.blocked()
        elif process is None:
            reason = f"会话未启动（{first['code']}）" if first else "会话未启动"
            record["steps"] = not_executed_steps(planned, reason)
        if process is not None:
            record["session_rc"] = process.poll()
            record.setdefault("session_process", "exited" if process.poll() is not None else "still_running（UNKNOWN）")
        closeout["record"] = "done"
    except BaseException as error:  # noqa: BLE001
        failed("record", error)
    # 3. 提示本人停 Play、等出帧静止（不冒充按钮时刻）
    played = False
    try:
        played = record.get("f0") is not None or (waiting_since is not None and frame_since(ctx.repo, waiting_since) is not None)
        record["unity_play_detected"] = played
        if played and deadline is not None:
            print("会话已结束或已中止：请本人在 Unity 按停止……", flush=True)
            stopped, last_frame = wait_unity_stopped(ctx.repo, UNITY_STOP_QUIET_S, deadline)
            if not stopped:
                found.append(Stop("S-WALL", f"{session_id} 出帧在工具截止（等待 Play 起点 + 420 s）仍未静止：按钮墙钟不能证明 ≤ 420 s"))
                print("已越过工具截止：请本人立即停止 Play（此后等待只为安全归档，不是额度）……", flush=True)
                extra_from = time.time()
                stopped, later = wait_unity_stopped(ctx.repo, UNITY_STOP_QUIET_S, extra_from + UNITY_STOP_CLOSEOUT_WAIT_S)
                last_frame = later if later is not None else last_frame
                record["unity_stop_closeout_wait_s"] = time.time() - extra_from
            since = record.get("first_frame_seen_unix_s") or waiting_since
            record.update(unity_frames_quiet=stopped, last_frame_id=last_frame, frames_window_s=time.time() - float(since),
                          frames_window_from="first_frame_seen" if record.get("first_frame_seen_unix_s") else "play_wait_start")
            ctx.ledger.add("play_wall_total_s", record["frames_window_s"])
            if last_frame is not None and last_frame >= 1500:
                record["s_ring"] = True  # 不停，照记
        closeout["unity"] = "done"
    except BaseException as error:  # noqa: BLE001
        failed("unity", error)
    # 4. 加载计数（段目录仍在 runtime/ 时读）与只移动归档
    loads: list[int] | None = None
    try:
        if process is not None:
            loads = model_loads_ok(ctx.repo, session_id)
            record["model_loads"] = loads
        closeout["loads"] = "done"
    except BaseException as error:  # noqa: BLE001
        failed("loads", error)
    try:
        session_running = process is not None and process.poll() is None
        skipped = None
        if played and not record.get("unity_frames_quiet"):
            skipped = "Unity 停止未确认：不移动帧环/段目录（UNKNOWN，交接受）"
        elif session_running:
            skipped = "会话进程仍在运行：不移动（UNKNOWN，交接受）"
        if skipped is not None:
            record["archive"] = {"moved": [], "skipped": skipped}
            # R1-3：归档未做/未证明 → 必入 found（停依赖、非 0 退出），不只写文本。
            found.append(UnknownOutcome(f"{session_id} 归档跳过：{skipped}"))
        elif played:
            try:
                record["archive"] = archive_attempt(ctx.repo, ctx.out, session_id)
            except Stop as stop:
                record["archive"] = dict(stop.report or {}, stop={"code": stop.code, "detail": stop.detail})
                found.append(stop)
        closeout["archive"] = "done"
    except BaseException as error:  # noqa: BLE001
        record["archive"] = {"moved": "UNKNOWN", "skipped": f"归档中失败（{type(error).__name__}: {error}）：已移动部分未证明（UNKNOWN，交接受）"}
        failed("archive", error)
    # 5. 原因码分流（触发失败在前，收尾发现的依原顺序追加）
    try:
        if process is not None:
            if loads is not None and (any(n != 1 for n in loads) or not loads):
                found.append(Stop("S-LOAD", f"model_loads={loads}"))
            session_dir = ctx.out / "play" / "sessions" / session_id
            terminal = classify_terminal(record.get("terminal_reason"), session_dir / "language-session.jsonl")
            if terminal is not None:
                found.append(terminal)
            blocked = record.get("blocked")
            if blocked and not str(blocked).startswith("HALTED "):  # 封住本身已有触发原因，不重复记
                found.append(Stop("S-BACKEND", f"计划停止推进：{blocked} → UNKNOWN，停全部交接受"))
        closeout["classify"] = "done"
    except BaseException as error:  # noqa: BLE001
        failed("classify", error)


def stage_play(ctx: Context, arguments: argparse.Namespace) -> int:
    gate = require_gate(ctx, arguments.registered_release, need_registration=True)
    values = source_check(ctx)
    require_g4(ctx, gate)
    outcome = web.read_json(ctx.out / "receipt-outcome.json") or {}
    receipt_path = ctx.out / "k-receipt" / "jetson-k-receipt.json"
    if outcome.get("k_receipt_rc") != 0 or not receipt_path.is_file():
        raise Stop("S-RECEIPT", "unit #2 k-receipt not 0 (单元 #3 不开)")
    plan, plan_sha = load_plan(ctx.out / "plan" / "ops-plan.json")
    receipt = web.load_receipt(receipt_path)
    ctx.board_ts = resolve_board_ts(ctx)
    digest = desktop_digest(ctx)
    log = web.OpsLog(ctx.out / "play" / web.OPS_LOG)
    cli = web.CliRunner(ctx.python, ctx.repo, ctx.repo / "runtime")
    submitter = web.Submitter(cli, cli, log)

    class Idle:
        def snapshot(self) -> dict[str, Any]:
            return {"playbook": None, "attempt": None, "plan_sha256": plan_sha, "current": None, "decision_step": None, "steps": []}

        def blocked(self) -> str | None:
            return None

        current_send_step = decision_step = staticmethod(lambda *_: None)
        record_skip = record_send = record_decision = record_operator_stop = staticmethod(lambda *_: None)

    app = web.App(monitor_factory=lambda sid, sdir: web.Monitor(ctx.repo / "runtime", sid, sdir, receipt), submitter=submitter,
                  log=log, scheduler=Idle(), feedback_path=ctx.out / "play" / "feedback.jsonl")
    server = web.build_server(app, arguments.port)
    stop_event = threading.Event()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    threading.Thread(target=web.poll_forever, args=(app, stop_event), daemon=True).start()
    print(f"操作页 http://{web.HOST}:{server.server_address[1]}/ （只本机）")
    unit = SshUnit(ctx, 3)
    serve: ServeSession | None = None
    attempts: list[dict[str, Any]] = []
    failure: BaseException | None = None
    closeout: dict[str, Any] = {}
    try:
        unit.open()
        serve = ServeSession(ctx, unit, 3, values)
        serve.start()
        identity_check(ctx, 3, digest)
        for playbook in arguments.playbooks:
            attempt: dict[str, Any] = {"playbook": playbook, "session_id": SESSION_IDS[playbook], "attempted": True}
            attempts.append(attempt)  # 先登记再执行：任何退出路径都保留同一份已填写的尝试记录（C6-3）
            run_attempt(ctx, app, submitter, plan, plan_sha, playbook, receipt_path, receipt, arguments.registered_release,
                        record=attempt)
    except BaseException as error:  # noqa: BLE001 - STOP/Ctrl-C/不明异常一律先走下列安全收尾（C6-2）
        failure = error
    # —— 以下收尾每步独立；一步失败（含 Ctrl-C）不跳过其余安全步骤（C6-2）——
    stopped_by = describe_failure(failure)
    for playbook in arguments.playbooks[len(attempts):]:
        attempts.append({"playbook": playbook, "session_id": SESSION_IDS[playbook], "attempted": False,
                         "steps": not_executed_steps(plan["playbooks"][playbook],
                                                     f"前序停止（{stopped_by['code'] if stopped_by else '—'}）：本剧本未开始")})
    release: dict[str, Any] | None = None
    try:
        release = serve.stop_and_release() if serve is not None and serve.proc is not None else None
        closeout["service_release"] = "done"
    except BaseException as error:  # noqa: BLE001
        closeout["service_release"] = f"{type(error).__name__}: {error}"
        failure = failure or error
    try:
        if serve is not None and serve.proc is not None and unit.open_ok:
            fetch_logs(ctx, unit, 3)
        closeout["logs"] = "done"
    except BaseException as error:  # noqa: BLE001
        closeout["logs"] = f"{type(error).__name__}: {error}"
        failure = failure or error
    try:
        unit.close()
        closeout["unit_close"] = "done"
    except BaseException as error:  # noqa: BLE001
        closeout["unit_close"] = f"{type(error).__name__}: {error}"
        failure = failure or error
    record = {"attempts": attempts, "release": release, "stop": describe_failure(failure), "closeout": closeout,
              "plan_sha256": plan_sha, "rel": gate.rel, "passed": gate.passed}
    try:
        (ctx.out / "play" / "play-record.json").write_text(json.dumps(record, ensure_ascii=False, indent=1, default=str) + "\n",
                                                           encoding="utf-8")
        closeout["record"] = "done"
    except BaseException as error:  # noqa: BLE001
        closeout["record"] = f"{type(error).__name__}: {error}"
        failure = failure or error
    # 收尾摘要：独立进程调用 summarize_ops（正式评分在其中经原 CLI；输出不回流在线工具）；失败/中断也照做
    attempted = [a for a in attempts if a.get("attempted")]
    try:
        summary = ctx.shell.run("summarize-ops", [ctx.python, "-m", "tools.eng_loop2.summarize_ops", "--ops-dir", str(ctx.out / "play"),
                                                  "--plan", str(ctx.out / "plan" / "ops-plan.json"), "--mode", "formal",
                                                  "--python", ctx.python])
        summary_json = web.read_json(ctx.out / "play" / "ops-summary.json") or {}
        md = ctx.out / "play" / "ops-summary.md"
        text = md.read_text(encoding="utf-8") if md.is_file() else summary.stdout
        app.set_summary({"attempts": [{"session_id": a.get("session_id")} for a in attempted], "text": text,
                         "summary_sha256": summary_json.get("summary_sha256")})
        closeout["summary"] = f"rc={summary.rc}"
        if summary.rc != 0:
            # R1-3/R1-4：摘要或其中的原评分失败、评分守账越界 → 置失败（非 0 退出），不打印正常收尾。
            envelope = [f for f in summary_json.get("failures") or [] if f.get("code") == "S-ENVELOPE"]
            failure = failure or (Stop("S-ENVELOPE", f"summarize_ops rc={summary.rc}: {envelope[0].get('detail')}") if envelope
                                  else UnknownOutcome(f"summarize_ops rc={summary.rc}（摘要/评分未证明完成；停依赖交接受）"))
    except BaseException as error:  # noqa: BLE001
        closeout["summary"] = f"{type(error).__name__}: {error}"
        failure = failure or error
    try:
        print(f"收尾摘要已就绪：请在操作页对每次尝试点「通过/失败/受阻」；最多等 {arguments.feedback_wait_s:.0f} s 或 Ctrl-C（缺反馈记未反馈）")
        feedback_deadline = time.time() + arguments.feedback_wait_s
        while len(app.feedback_given) < len(attempted) and time.time() < feedback_deadline:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    missing = sorted({a.get("session_id") for a in attempted} - set(app.feedback_given))
    log.write("feedback_window_closed", missing_feedback=missing, note="缺失即「未反馈」，不默认通过")
    try:
        stop_event.set()
        server.shutdown()
        server.server_close()
        closeout["web_shutdown"] = "done"
    except BaseException as error:  # noqa: BLE001
        closeout["web_shutdown"] = f"{type(error).__name__}: {error}"
    log.write("closeout_tail", closeout=closeout, stop=describe_failure(failure))
    if failure is not None:
        raise failure
    if release is not None and not release.get("released"):
        raise Stop("S-SERVICE", "release_not_proven")
    return 0


# --- 诊断模式（IR-OPS-5；「OPS验证额度落实与IR裁定」§2 SUB:3 与 §4） ----------------------------------------


#: 旧 SUB:3（**历史，已耗尽**；常量名与值不改，「诊断绑定方案答复」BIND-1）：`DIAG_ENTRIES` 里 status=exhausted，代码级无条件拒续。
DIAG_REQUEST_ID = "P1-ENG-LOOP-002:9bac8fd0:SUB:3"
#: 旧 SUB:3 账本命中（历史）：签发条目标题片段 + 完整 request_id。
DIAG_LEDGER_HITS = ("用户按申请签发 OPS 验证额度 SUB:1/SUB:2/SUB:3", DIAG_REQUEST_ID)
#: 现行唯一已签诊断条目（账本 10-08「用户按推荐签发新全套 42979c14:SUB:1 与新诊断 DIAG:RETRY:1」；signed 只表示资源已签，不是执行许可）。
DIAG_RETRY1_REQUEST_ID = "P1-ENG-LOOP-002:DIAG:RETRY:1"
DIAG_BANNER = "诊断；不进证据链；不作任何门判定"
DIAG_AIR_PARENT = "outputs/eng-loop/P1-ENG-LOOP-002/diagnostics"
DIAG_BOARD_PARENT = "/home/jetson/eng-loop2-diag"
DIAG_SESSION_PREFIX = "diag-loop2-"
#: §2 SUB:3 已签维度；DIAG:RETRY:1 已签维度逐项相同（「全套与诊断签发落实」§3；同一对象、不按条目复制）。成功、失败、拒启、中止均计；
#: 下一动作会越界即 STOP1。
DIAG_LIMITS = {
    "master_connections": 2, "serve_starts": 1, "fault_restarts": 0, "plays": 1, "sessions": 1,
    "measure_runs": 1, "k_receipt_runs": 1, "wall_s": 2700.0, "air_bytes": 250_000_000, "board_bytes": 200_000_000,
}
#: §4.4：一个准备用途主连接、一个前台服务/释放/回传主连接；通道只在存活主连接上复用。
DIAG_CHANNELS = {"d1": ("board-check", "root-code", "code-verify", "run-files"), "d2": ("serve", "board-du", "logs")}
DIAG_REPEATABLE = frozenset({"board-du"})
#: （历史：旧 SUB:3 键，新条目不认；现行键见 `DIAG_RELEASE_KEY_LINE`）「接受消费」的机读放行行（IR-OPS-7 已裁定：同名提案「OPS基线与IR78裁定」§2；只由接受在
#: 「OpsK1K2K3K4通过消费与SUB:3放行」节写，值 = 门核得到的最新有效 passed_candidate；读取失败、缺行或
#: 不匹配均 DIAG_REFUSED、不开任何受限动作；脚本不自签，合同格式示例不是放行行）。
DIAG_RELEASE_LINE = re.compile(MR + r"sub3_release: ([0-9a-f]{40})(`|[ \t]|$)")


@dataclass(frozen=True)
class DiagEntry:
    """诊断条目闭表的一项（「诊断绑定方案答复」BIND-1）：request_id ↔ 唯一已签账本条目 / 放行键 / 已签剧本。"""

    request_id: str
    status: str  # "exhausted"（历史，无条件拒续） | "signed"（资源已签；执行仍须全部机读前提）
    ledger_title: str
    release_key: str
    playbooks: tuple[str, ...]


#: BIND-1 冻结闭表：只两项；未知 id 无入口。限额对所有条目沿用同一 `DIAG_LIMITS` 对象（不按条目复制数字）。
DIAG_ENTRIES: Mapping[str, DiagEntry] = types.MappingProxyType({
    DIAG_REQUEST_ID: DiagEntry(DIAG_REQUEST_ID, "exhausted", DIAG_LEDGER_HITS[0], "sub3_release", ("P1", "P2", "P3")),
    DIAG_RETRY1_REQUEST_ID: DiagEntry(DIAG_RETRY1_REQUEST_ID, "signed", "用户按推荐签发新全套 42979c14:SUB:1 与新诊断 DIAG:RETRY:1",
                                      "diag_release", ("P1",)),
})
#: BIND-4 新机读放行键：`diag_release: <完整 request_id> <40 位小写 sha>`（行首可带列表记号/反引号，同 `MR`）；只认完整 id 与
#: 合法候选值，占位格式、大写/短 sha、他 id（含前缀扩展）、旧 `sub3_release:` 均不计。只由接受程序写入，脚本/实现不自签。
DIAG_RELEASE_KEY_LINE = re.compile(MR + r"diag_release: (\S+) ([0-9a-f]{40})(`|[ \t]|$)")


def diag_entry_for(request_id: str, playbook: str) -> DiagEntry:
    """BIND-2 建根前的条目检查（不建根、不写粗账、不消耗）：未知 id / 已耗尽 / 剧本未签 → `DiagRefused`。"""
    entry = DIAG_ENTRIES.get(request_id)
    if entry is None:
        raise DiagRefused(f"request_id_unknown {request_id!r}（诊断条目闭表只有 {', '.join(DIAG_ENTRIES)}；未知 id 无入口）")
    if entry.status != "signed":
        raise DiagRefused(f"request_exhausted {request_id}（历史条目，已耗尽；代码级无条件拒续，不依赖 outputs/ 粗账）")
    if playbook not in entry.playbooks:
        raise DiagRefused(f"playbook_not_signed {playbook}（{request_id} 只签 {'/'.join(entry.playbooks)}）")
    return entry


def diag_ledger_binding(text: str | None, entry: DiagEntry) -> dict[str, Any]:
    """BIND-3：发布引用账本按 `## ` 二级标题分条；标题含条目标题片段的恰一条，且其正文含反引号包住的完整 id。

    `text` 为 None = 读取失败。不按全文两子串命中放行（标题在 A、id 在 B / 仅前缀扩展 / 0 或多条均拒）。
    """
    if text is None:
        raise DiagRefused("ledger_unreadable（发布引用上账本读取失败）")
    lines = text.splitlines()
    heads = [i for i, line in enumerate(lines) if line.startswith("## ")]
    hits = [i for i in heads if entry.ledger_title in lines[i]]
    if not hits:
        raise DiagRefused(f"ledger_entry_missing {entry.ledger_title}")
    if len(hits) > 1:
        raise DiagRefused(f"ledger_entry_ambiguous {entry.ledger_title} lines={[i + 1 for i in hits]}")
    start = hits[0]
    end = next((i for i in heads if i > start), len(lines))
    token = f"`{entry.request_id}`"
    if not any(token in line for line in lines[start + 1 : end]):
        raise DiagRefused(f"ledger_request_id_missing {entry.request_id}（唯一条目第 {start + 1} 行正文无反引号完整 id）")
    return {"ledger_title_line_no": start + 1, "ledger_title_line": lines[start]}


def diag_release_binding(text: str | None, entry: DiagEntry, passed: str | None) -> dict[str, Any]:
    """BIND-4：发布引用提案中本 id 的严格 `diag_release:` 行；读取失败 / 无本 id 合法行 / 无值等于门核 passed 均拒。"""
    if text is None:
        raise DiagRefused(f"diag_release_unreadable passed_candidate={passed}（发布引用上提案读取失败）")
    own = [(number, match.group(3)) for number, line in enumerate(text.splitlines(), start=1)
           if (match := DIAG_RELEASE_KEY_LINE.match(line)) and match.group(2) == entry.request_id]
    if not own:
        raise DiagRefused(f"diag_release_missing {entry.request_id} passed_candidate={passed}（接受未写本 id 的机读放行行）")
    matched = [(number, value) for number, value in own if passed is not None and value == passed]
    if not matched:
        raise DiagRefused(f"diag_release_mismatch {entry.request_id} passed_candidate={passed} "
                          f"lines={[number for number, _ in own]}（放行值不等于门核最新有效 passed_candidate）")
    number, value = matched[-1]
    return {"release_line_no": number, "release_value": value}


DIAG_LISTEN = re.compile(r"^DIAG language-serve listening on http://(\S+) ")
DIAG_SH_RC = re.compile(r"^serve_diag_sh_rc=(-?\d+)$")
DIAG_DU_LINE = re.compile(r"^([0-9]+)\t(/\S+)$")
#: 为安全收尾预留的墙钟（停会话、本人停 Play、Ctrl-C 等服务退出 ≤ 120 s、同会话释放核、日志回传、归位）。
DIAG_CLOSEOUT_RESERVE_S = 420.0
#: 监测到两端体积达到上限的该比例即停业务、收尾（不只看末次体积）。
DIAG_DISK_STOP_FRACTION = 0.9
DIAG_AIR_DU_INTERVAL_S = 10.0
DIAG_BOARD_DU_INTERVAL_S = 60.0
DIAG_SESSION_STOP_WAIT_S = 30.0
DIAG_UNITY_STOP_WAIT_S = 120.0
#: DIAG-CONTROL-1（同名提案「SUB3核清与评分上限落实」§2，AC-10 修订 8）：本机 AF_UNIX `sun_path` 容量（字节，含结尾
#: NUL）。macOS/BSD 104、Linux 108；其他平台按较小的 104（fail-closed）。路径字节数须 ≤ 容量 − 1。
UNIX_SOCKET_PATH_CAPACITY = 108 if sys.platform.startswith("linux") else 104
#: OpenSSH ControlMaster 先在 `<ControlPath>.<16 位随机字符>` 上监听、再改名为 ControlPath（mux.c
#: `muxserver_listen`）；本机限制按带这 17 字节后缀的实际路径核（SUB:3 原 stderr：后缀前 103、带后缀 120 字节）。
OPENSSH_CONTROL_SUFFIX_BYTES = 17
#: 短私有目录的父目录；None = `tempfile.gettempdir()`（macOS 为本用户私有 `$TMPDIR`）。只在本次进程内用 mkdtemp 新建
#: 唯一子目录（0700、本用户、非链接），不复用旧目录、不改全局 SSH 配置/仓库路径/诊断与正式输出根。
DIAG_CONTROL_PARENT: str | None = None
DIAG_CONTROL_PREFIX = "el2d-"


class DiagRefused(Exception):
    """开工前提不满足（未消耗任何受限维度）：拒启，非 0 退出。"""


class DiagStop(Exception):
    """四类诊断 STOP（§4.7）：立即停依赖/新增业务并安全收尾。"""

    def __init__(self, category: int, detail: str):
        if category not in (1, 2, 3, 4):
            raise ValueError(category)
        super().__init__(f"STOP{category} {detail}")
        self.category, self.detail = category, detail


class DiagFault(Exception):
    """普通故障（缺库/HTTP/解析/收据/启动错误/UNKNOWN）：记 `DIAG_FAULT` 与原 rc，不套正式 11 码、不改成 STOP。"""

    def __init__(self, detail: str, rc: Any = None):
        super().__init__(f"DIAG_FAULT {detail}")
        self.detail, self.rc = detail, rc


def tree_bytes(path: Path) -> int:
    """十进制字节（逐文件 `lstat` 求和；不跟随链接、不读内容）。"""
    total = 0
    root = Path(path)
    if not root.exists():
        return 0
    if root.is_file() or root.is_symlink():
        return root.lstat().st_size
    for item in root.rglob("*"):
        try:
            if item.is_file() and not item.is_symlink():
                total += item.lstat().st_size
        except OSError:
            continue
    return total


class DiagAccount:
    """§4.6 粗账 `ops-diagnostic-ledger.json`：每个受限动作之前查额/先记占额；缺实测值写 UNKNOWN，不默认 0。"""

    def __init__(self, root: Path, label: str, board_root: str, *, request_id: str = DIAG_REQUEST_ID,
                 entry_binding: Mapping[str, Any] | None = None, clock: Callable[[], float] = time.time):
        # request_id 缺省保留旧值只为既有构造接口兼容；生产 `DiagnosticRun` 一律显式传入闭表条目 id 与 entry_binding（BIND-2）。
        self.path = Path(root) / "ops-diagnostic-ledger.json"
        self.clock = clock
        self.start = clock()
        self.data: dict[str, Any] = {
            "purpose": f"{WORK_ID} OPS 新入口实跑诊断（IR-OPS-5）；{DIAG_BANNER}",
            "request_id": request_id, "entry_binding": dict(entry_binding) if entry_binding is not None else None,
            "label": label, "air_root": str(root), "board_root": board_root,
            "start_utc": _dt.datetime.fromtimestamp(self.start, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "start_epoch_s": self.start, "end_utc": None, "end_epoch_s": None, "elapsed_s": None,
            "limits": dict(DIAG_LIMITS), "used": {k: 0 for k in DIAG_LIMITS if k not in {"wall_s", "air_bytes", "board_bytes"}},
            "consumed": False, "refused": None,
            "head": None, "passed_candidate": None, "rel": None, "playbook": None, "p2_object": None,
            "master_connections": [], "serve": {"starts": 0, "fault_restarts": 0, "gguf_loads": "UNKNOWN", "serve_rc": None,
                                                "sh_rc": None, "listen_line": None, "release": None},
            "play": {"count": 0, "session_id": None, "f0": None, "t_sess_s": None, "first_frame_seen_unix_s": None,
                     "last_frame_id": None, "frames_quiet": None,
                     "button_start_unix_s": "UNKNOWN（仅本人可靠记录；f₀/出帧/网页时间不替代）",
                     "button_stop_unix_s": "UNKNOWN（仅本人可靠记录；末帧/TERMINAL/网页时间不替代）",
                     "terminal_reason": None, "session_rc": None},
            "yolo_loads": "UNKNOWN", "measure": {"runs": 0, "rc": None, "first_failure": None}, "k_receipt": {"runs": 0, "rc": None},
            "disk": {"air": [], "board": [], "air_peak_bytes": None, "board_peak_bytes": None,
                     "air_source": "本次 Air 诊断根逐文件 lstat 求和 + 待移入的 runtime 帧环/真值文件",
                     "board_source": "板上 `du -sb <本次诊断根>` 原流（board-check/同步/轮询/收尾）"},
            "stop": None, "faults": [], "unknown": [], "not_executed": [], "deviations": [], "closeout": {},
            "post_closeout": {},
        }
        self.save()

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n",
                             encoding="utf-8")

    def elapsed(self) -> float:
        return self.clock() - self.start

    def remaining(self) -> float:
        return DIAG_LIMITS["wall_s"] - self.elapsed()

    def take(self, key: str, amount: int = 1) -> None:
        if self.data["used"][key] + amount > DIAG_LIMITS[key]:
            raise DiagStop(1, f"{key} would exceed {DIAG_LIMITS[key]} (used {self.data['used'][key]})")
        self.data["used"][key] += amount
        self.save()

    def consume(self) -> None:
        """首个受限动作（主连接尝试）之前置位：本 request_id 的这一次从此视为已用。"""
        self.data["consumed"] = True
        self.save()

    def require_time(self, needed_s: float, what: str) -> None:
        if self.elapsed() + needed_s + DIAG_CLOSEOUT_RESERVE_S > DIAG_LIMITS["wall_s"]:
            raise DiagStop(1, f"wall: {what} needs {needed_s:.0f} s + closeout reserve {DIAG_CLOSEOUT_RESERVE_S:.0f} s; "
                              f"elapsed {self.elapsed():.0f} s of {DIAG_LIMITS['wall_s']:.0f} s")

    def fault(self, detail: str, rc: Any = None) -> None:
        self.data["faults"].append({"at_unix_s": self.clock(), "detail": detail, "rc": rc})
        self.save()

    def unknown(self, detail: str) -> None:
        self.data["unknown"].append({"at_unix_s": self.clock(), "detail": detail})
        self.save()

    def stop(self, stop: DiagStop) -> None:
        if self.data["stop"] is None:
            self.data["stop"] = {"category": stop.category, "detail": stop.detail, "at_unix_s": self.clock()}
        else:
            self.data.setdefault("later_stops", []).append({"category": stop.category, "detail": stop.detail})
        self.save()

    def disk(self, side: str, value: int | None, source: str) -> None:
        self.data["disk"][side].append({"at_unix_s": self.clock(), "bytes": value, "source": source})
        if value is not None:
            key = f"{side}_peak_bytes"
            self.data["disk"][key] = max(self.data["disk"][key] or 0, value)
            if value > DIAG_LIMITS[f"{side}_bytes"]:
                self.data["deviations"].append(f"{side} bytes {value} > {DIAG_LIMITS[side + '_bytes']}（实际越界，照记；不追认额度）")
        self.save()

    def near_limit(self, side: str, value: int | None) -> bool:
        return value is not None and value >= DIAG_DISK_STOP_FRACTION * DIAG_LIMITS[f"{side}_bytes"]

    def finish(self) -> None:
        end = self.clock()
        self.data.update(end_epoch_s=end, elapsed_s=end - self.start,
                         end_utc=_dt.datetime.fromtimestamp(end, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        if end - self.start > DIAG_LIMITS["wall_s"]:
            self.data["deviations"].append(f"wall {end - self.start:.0f} s > {DIAG_LIMITS['wall_s']:.0f} s（照记；不追认）")
        self.save()

    def clean(self) -> bool:
        release = (self.data["serve"].get("release") or {})
        return (self.data["stop"] is None and not self.data["faults"] and not self.data["unknown"]
                and not self.data["deviations"] and (self.data["serve"]["starts"] == 0 or bool(release.get("released")))
                and self.data["play"]["terminal_reason"] in {"operator_stop", "duration_reached"})


class DiagRecorder(Recorder):
    """诊断根下 `ops-events.jsonl` 逐事件、子进程原 stdout/stderr 落 `raw/`（只追加）。"""

    def __init__(self, root: Path, *, clock: Callable[[], float] = time.time):
        self.root = Path(root) / "raw"
        self.root.mkdir(parents=True)
        self.clock = clock
        self.log = web.OpsLog(Path(root) / "ops-events.jsonl", clock=clock)
        self.counter = 0


def unix_socket_path_fits(path: Path | str, suffix_bytes: int = OPENSSH_CONTROL_SUFFIX_BYTES) -> tuple[bool, int]:
    """(是否放得下, 带后缀的实际字节数)：按 `os.fsencode` 编码后的字节计，不按字符数。"""
    used = len(os.fsencode(str(path))) + suffix_bytes
    return used <= UNIX_SOCKET_PATH_CAPACITY - 1, used


class DiagControlDir:
    """DIAG-CONTROL-1：本次诊断进程独占的短私有 ControlPath 目录（AC-10 修订 8）。

    * 归属/唯一：`tempfile.mkdtemp` 新建（O_EXCL 语义，0700，本用户），lstat 核是目录、非链接、uid 为本用户、无组/他人权限；
      每次 `DiagnosticRun` 新建一个，d1/d2 各用目录内独立名字，跨批不复用。
    * 有效：每个名字按编码后实际路径 + OpenSSH 17 字节临时后缀核 `UNIX_SOCKET_PATH_CAPACITY`，并在本目录内以同字节长度
      的探针名实际 `bind`/关闭本机 AF_UNIX 套接字（探针是本对象刚建的文件，随即删除）；任一不成立即删掉这个空目录并
      `DiagRefused`（在占额之前，未消耗）。
    * 生命周期：主连接全部关闭后 `release()`；只删除本对象创建的目录且仅当其为空——残留任何项（含未退出主连接的
      套接字）都不删、不复用，记 UNKNOWN 与路径指针；目录内各项 lstat 字节计入 Air 读数（不因位于诊断根外免账）。
    """

    def __init__(self, path: Path, names: Sequence[str], record: dict[str, Any]):
        self.path, self.names, self.record = path, tuple(names), record
        self.released = False

    @classmethod
    def allocate(cls, names: Sequence[str], parent: str | None = None) -> "DiagControlDir":
        base = parent if parent is not None else (DIAG_CONTROL_PARENT or tempfile.gettempdir())
        # 先按名字长度预核（目录名 = 前缀 + 8 位随机），过长即不建目录
        projected = Path(base) / f"{DIAG_CONTROL_PREFIX}XXXXXXXX" / max(names, key=lambda n: len(os.fsencode(n)))
        fits, used = unix_socket_path_fits(projected)
        if not fits:
            raise DiagRefused(f"control_path_too_long projected {used} B > {UNIX_SOCKET_PATH_CAPACITY - 1} B under {base}"
                              "（不改全局 SSH 配置/仓库与输出根；未消耗）")
        try:
            path = Path(tempfile.mkdtemp(prefix=DIAG_CONTROL_PREFIX, dir=base))
        except OSError as error:
            raise DiagRefused(f"control_dir_create_failed {base}: {error}（未消耗）") from error
        record: dict[str, Any] = {"path": str(path), "parent": str(base), "pid": os.getpid(), "created_unix_s": time.time(),
                                  "capacity_bytes": UNIX_SOCKET_PATH_CAPACITY, "suffix_bytes": OPENSSH_CONTROL_SUFFIX_BYTES,
                                  "paths": {}, "probe": {}, "released": None}
        try:
            info = os.lstat(path)
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise DiagRefused(f"control_dir_unsafe {path} mode={oct(stat.S_IMODE(info.st_mode))} uid={info.st_uid}")
            record.update(mode=oct(stat.S_IMODE(info.st_mode)), uid=info.st_uid)
            for name in names:
                control = path / name
                fits, used = unix_socket_path_fits(control)
                record["paths"][name] = {"control_path": str(control), "bytes_with_suffix": used}
                if not fits:
                    raise DiagRefused(f"control_path_too_long {name} {used} B > {UNIX_SOCKET_PATH_CAPACITY - 1} B")
                probe = path / f"{name}.{secrets.token_hex(8)}"  # 与 OpenSSH 临时名同字节长度
                if os.path.lexists(probe):
                    raise DiagRefused(f"control_probe_exists {probe}")
                listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                try:
                    listener.bind(os.fsencode(str(probe)))
                except OSError as error:
                    raise DiagRefused(f"control_path_bind_failed {name} ({len(os.fsencode(str(probe)))} B): {error}") from error
                finally:
                    listener.close()
                    if os.path.lexists(probe):
                        os.unlink(probe)
                record["probe"][name] = {"bytes": len(os.fsencode(str(probe))), "bind": "ok", "removed": True}
        except BaseException:
            try:
                os.rmdir(path)  # 只删本次刚建的空目录
            except OSError:
                pass
            raise
        return cls(path, names, record)

    def control_path(self, name: str) -> Path:
        if name not in self.names:
            raise DiagFault(f"control_name_outside_allocation {name}")
        return self.path / name

    def verify(self) -> None:
        """主连接尝试前复核目录仍为本用户 0700 私有目录（改权限/换属主/非目录/缺失即拒绝连接；不比较 dev/inode，同用户同权限的目录替换不在判据内）。"""
        try:
            info = os.lstat(self.path)
        except OSError as error:
            raise DiagFault(f"control_dir_missing {self.path}: {error}") from error
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077
                or (self.record.get("uid") is not None and info.st_uid != self.record["uid"])):
            raise DiagFault(f"control_dir_unsafe {self.path}")

    def entries(self) -> list[str]:
        try:
            return sorted(os.listdir(self.path))
        except FileNotFoundError:
            return []

    def bytes(self) -> int:
        """目录内各项（文件/套接字/链接，不跟随）lstat 字节之和；不存在即 0。"""
        total = 0
        for name in self.entries():
            try:
                info = os.lstat(self.path / name)
            except OSError:
                continue
            if not stat.S_ISDIR(info.st_mode):
                total += info.st_size
        return total

    def release(self) -> dict[str, Any]:
        """全部主连接关闭之后调用：空目录才删除；有残留不删不复用，返回残留清单（调用方记 UNKNOWN）。"""
        left = self.entries()
        result: dict[str, Any] = {"at_unix_s": time.time(), "left_entries": left, "removed": False}
        if not left and self.path.is_dir() and not self.path.is_symlink():
            try:
                os.rmdir(self.path)
                result["removed"] = True
            except OSError as error:
                result["error"] = f"{type(error).__name__}: {error}"
        self.released = True
        self.record["released"] = result
        return result


class DiagConnection(SshUnit):
    """一条诊断主连接（尝试前即计次，成功/失败均计；≤ 2）+ 存活主连接上的有限通道；失效不回退新认证。

    DIAG-CONTROL-1：ControlPath = 本次 `DiagControlDir` 内本连接独立的名字；ControlMaster 创建、`-O check`、通道 `-S`、
    `-O exit` 全部用这同一个实际路径（继承 `SshUnit` 的同一 `self.cm`）；通话计次表仍在诊断根 `ssh/` 下。
    """

    def __init__(self, ctx: Context, account: DiagAccount, name: str, control: DiagControlDir):
        self.ctx, self.unit, self.account = ctx, name, account
        ssh_dir = ctx.out / "ssh"
        ssh_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(ssh_dir, 0o700)
        self.control = control
        self.cm = control.control_path(name)
        self.tally = ssh_dir / f"{name}.tsv"
        self.allowed = DIAG_CHANNELS[name]
        self.used: list[str] = []
        self.opened_at: float | None = None
        self.open_ok = False

    def open(self) -> None:
        self.control.verify()
        if os.path.lexists(self.cm):
            raise DiagFault("stale_control_socket")
        self.account.take("master_connections")
        self.opened_at = time.time()
        self._tally("master_attempt_epoch", f"{self.opened_at:.6f}")
        self._tally("control_path", str(self.cm))
        run = self.ctx.shell.run(f"ssh-master-{self.unit}", [
            self.ctx.ssh, "-o", "ControlMaster=yes", "-o", f"ControlPath={self.cm}", "-o", "ControlPersist=no",
            "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", "-fN", self.ctx.alias,
        ])
        self._tally("master_rc", run.rc, "epoch", f"{time.time():.6f}")
        self.account.data["master_connections"].append({"name": self.unit, "attempt_unix_s": self.opened_at, "rc": run.rc,
                                                        "control_path": str(self.cm)})
        self.account.save()
        if run.rc != 0:
            raise DiagFault(f"ssh_master_failed {self.unit} (counted; no retry, no new connection)", run.rc)
        self.open_ok = True

    def _check_and_claim(self, name: str) -> None:
        if name not in self.allowed or (name in self.used and name not in DIAG_REPEATABLE):
            raise DiagFault(f"channel_outside_closed_set {name} on {self.unit}")
        check = self.ctx.shell.run(f"ssh-check-{name}", [self.ctx.ssh, "-S", str(self.cm), "-O", "check", self.ctx.alias])
        if check.rc != 0:
            self.account.unknown(f"control socket {self.unit} unavailable before {name}（不隐式直连、不第三次认证）")
            raise DiagFault(f"control_socket_unavailable before {name}", check.rc)
        self.used.append(name)

    def _account(self) -> None:
        if self.opened_at is not None:
            self.ctx.recorder.event("connection_wall", name=self.unit, wall_s=time.time() - self.opened_at)


class DiagServe(ServeSession):
    """诊断页附录 3（只编号 1）在可见前台交互 bash 中运行；Ctrl-C 正常停止，同会话按附录 7 核释放。"""

    def __init__(self, ctx: Context, connection: DiagConnection, account: DiagAccount, board_root: str):
        self.ctx, self.unit, self.n, self.values = ctx, connection, 1, {}
        self.account, self.board_root = account, board_root
        self.log_path = ctx.out / "board" / "serve-channel-1.log"
        self.lines: list[str] = []
        self.cond = threading.Condition()
        self.proc: subprocess.Popen | None = None
        self.reader: threading.Thread | None = None
        self.started_unix_s: float | None = None
        self.stopped_unix_s: float | None = None
        self.serve_rc: int | None = None
        self.sh_rc: int | None = None
        self.exited = False

    def _note_rc(self) -> None:
        with self.cond:
            lines = list(self.lines)
        for line in lines:
            if (m := SERVE_RC_LINE.match(line)):
                self.serve_rc = int(m.group(1))
            if (m := DIAG_SH_RC.match(line)):
                self.sh_rc = int(m.group(1))
        self.account.data["serve"].update(serve_rc=self.serve_rc, sh_rc=self.sh_rc,
                                          gguf_loads=1 if any(l.startswith("DIAG_LOAD_START") for l in lines) else 0)
        self.account.save()

    def start(self) -> None:
        self.account.take("serve_starts")  # 含拒启；本批只许编号 1，故障重启 0
        self.account.data["serve"]["starts"] += 1
        self.account.save()
        self.proc = self.unit.chan_popen("serve", "exec bash --noprofile --norc -i")
        self.reader = threading.Thread(target=self._reader, daemon=True)
        self.reader.start()
        self.started_unix_s = time.time()
        self.type("PS1=; PS2=; set +o emacs +o vi; stty -echo")  # 同正式：不回显预键入命令，标记行不被夹杂
        script = shlex.quote(f"{self.board_root}/run/serve-diag.sh")
        self.type(f'bash --noprofile --norc {script} 1; echo "serve_diag_sh_rc=$?"')
        value, _ = self.wait_for(lambda line: DIAG_LISTEN.match(line) or DIAG_SH_RC.match(line), LISTEN_WAIT_S)
        self._note_rc()
        if isinstance(value, re.Match) and value.re is DIAG_LISTEN:
            self.account.data["serve"]["listen_line"] = value.string
            self.account.save()
            expected = f"{self.ctx.board_ts}:{SERVE_PORT}"
            if value.group(1) != expected:
                raise DiagFault(f"listening_on_unexpected_endpoint {value.group(1)} != {expected}")
            self.ctx.recorder.event("serve_listening", line=value.string)
            return
        faults = [l for l in self.lines if l.startswith("DIAG_FAULT") or l.startswith("DIAG refused")]
        if isinstance(value, re.Match):
            raise DiagFault(f"service exited before ready sh_rc={self.sh_rc} serve_rc={self.serve_rc} {faults[:2]}", self.sh_rc)
        self.account.unknown(f"service not ready within {LISTEN_WAIT_S:.0f} s and no exit line")
        raise DiagFault("service_not_ready_unknown", None)

    def stop_and_release(self) -> dict[str, Any]:
        """Ctrl-C → 等 `serve_diag_sh_rc` → 同会话附录 7 核端口/本次进程/磁盘 → exit；未核清即 UNKNOWN（不清未知进程）。"""
        report: dict[str, Any] = {"unit": self.unit.unit}
        if self.proc is None:
            return report
        if self.sh_rc is None and not self.exited:
            self.ctx.recorder.event("serve_interrupt")
            assert self.proc.stdin is not None
            try:
                self.proc.stdin.write(b"\x03")
                self.proc.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            self.wait_for(lambda line: DIAG_SH_RC.match(line), SERVE_EXIT_WAIT_S)
        self._note_rc()
        self.stopped_unix_s = time.time()
        report.update(serve_rc=self.serve_rc, sh_rc=self.sh_rc,
                      residency_s=(self.stopped_unix_s - self.started_unix_s) if self.started_unix_s else None)
        mark = len(self.lines)
        if not self.exited:
            self.type(f"R={shlex.quote(self.board_root)}")
            for line in extract_block(self.ctx.repo / DIAG_OPS_DOC, "### 附录 7 ", "bash").splitlines():
                if line.strip():
                    self.type(line)
            self.type("echo DIAG_CLOSEOUT_DONE")
        done, end = self.wait_for(lambda line: line == "DIAG_CLOSEOUT_DONE", 60.0, start=mark)
        window = self.lines[mark:end]
        du = [m for l in window if (m := DIAG_DU_LINE.match(l)) and m.group(2).rstrip("/") == self.board_root.rstrip("/")]
        report.update(closeout_done=bool(done), ports_released="PORTS_RELEASED" in window,
                      still_listening=[l for l in window if l.startswith("STILL_LISTENING ")],
                      no_residual_process="NO_RESIDUAL_PROCESS" in window,
                      board_du_bytes=int(du[-1].group(1)) if du else None)
        report["released"] = bool(done) and report["ports_released"] and report["no_residual_process"] and not report["still_listening"]
        self.finish_channel()
        self.ctx.recorder.event("serve_release", **report)
        return report


class DiagnosticRun:
    """IR-OPS-5 一次诊断：模式/根 → 现场核与源码同步 → 前台服务 → 诊断输入 → 一次 Play/会话/网页 → 收尾 → 摘要。"""

    def __init__(self, arguments: argparse.Namespace):
        self.arguments = arguments
        self.repo = Path(arguments.repo).resolve()
        self.python = arguments.python if Path(arguments.python).is_absolute() else str(self.repo / arguments.python)
        self.label = utc_now()
        if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", self.label):
            raise DiagRefused(f"bad label {self.label!r}")
        self.root = self.repo / DIAG_AIR_PARENT / self.label
        self.board_root = f"{DIAG_BOARD_PARENT}/{self.label}"
        #: BIND-1/2：闭表条目（建根前；未知/耗尽/剧本未签即拒，不建根、不写粗账）。
        self.entry = diag_entry_for(arguments.request_id, arguments.playbook)
        self._refuse_if_consumed()
        try:
            self.root.mkdir(parents=True, exist_ok=False)
        except FileExistsError as error:
            raise DiagRefused(f"air_root_exists {self.root}（必须新建，不覆盖）") from error
        for name in ("prep", "board", "receipt", "play", "segments", "hold", "plan"):
            (self.root / name).mkdir()
        self.account = DiagAccount(self.root, self.label, self.board_root, request_id=self.entry.request_id,
                                   entry_binding={"request_id": self.entry.request_id, "status": self.entry.status,
                                                  "ledger_title": self.entry.ledger_title,
                                                  "release_key": self.entry.release_key,
                                                  "playbooks": list(self.entry.playbooks)})
        self.recorder = DiagRecorder(self.root)
        self.shell = Shell(self.recorder, cwd=self.repo)
        docwt = Path(arguments.docwt).resolve() if arguments.docwt else None
        self.ctx = Context(self.repo, self.root, self.python, self.recorder, self.shell, None,  # type: ignore[arg-type]
                           ssh=arguments.ssh, alias=arguments.alias, docwt=docwt)
        self.conn1: DiagConnection | None = None
        self.conn2: DiagConnection | None = None
        #: DIAG-CONTROL-1：本次进程独占的短私有 ControlPath 目录（占额前建立并实测；主连接全关后释放）。
        self.control: DiagControlDir | None = None
        self.serve: DiagServe | None = None
        self.values: dict[str, str] = {}
        self.plan: dict[str, Any] | None = None
        self.plan_sha: str | None = None
        self.receipt_path: Path | None = None
        self.app: web.App | None = None
        self.server: Any = None
        self.web_stop = threading.Event()
        self.submitter: web.Submitter | None = None
        self.scheduler: PlanScheduler | None = None
        self.monitor: web.Monitor | None = None
        self.session_proc: subprocess.Popen | None = None
        self.session_id: str | None = None
        #: C6-1：STOP/故障/中断/到时的封住原因（一旦置位不可逆；只剩至多一次 stop 与安全收尾）。
        self.halted_reason: str | None = None
        self.blocked_noted = False
        self.play_started = False
        self.frames_moved = False
        self.held = False
        self.overlay_written = False
        self.last_board_du = 0.0
        self.last_air_du = 0.0
        self.recorder.event("diag_start", banner=DIAG_BANNER, request_id=self.entry.request_id, root=str(self.root),
                            board_root=self.board_root, argv=sys.argv)

    # -- 前提（不消耗任何受限维度） --

    def _refuse_if_consumed(self) -> None:
        """BIND-2（fail-closed）：扫描域内任一粗账读不出/非法 JSON/非对象/缺或非字符串 request_id → 拒启（不用 `or {}` 吞错，
        身份不明的账不猜是旧账而跳过）；同 id 只有 `consumed` 为字面 false 才可继续（缺键/null/0/空串/其他非布尔/true 均已用）。
        身份可读的其他 id 粗账不占本 id 次数。建根前执行：拒启不建根、不写粗账、不消耗。"""
        parent = self.repo / DIAG_AIR_PARENT
        own = self.entry.request_id
        for ledger in sorted(parent.glob("*/ops-diagnostic-ledger.json")) if parent.is_dir() else []:
            try:
                document = json.loads(ledger.read_bytes().decode("utf-8"))
            except (OSError, UnicodeDecodeError, ValueError) as error:
                raise DiagRefused(f"diag_ledger_unreadable {ledger}（{type(error).__name__}）") from error
            if not isinstance(document, dict):
                raise DiagRefused(f"diag_ledger_unreadable {ledger}（非对象 JSON：{type(document).__name__}）")
            identity = document.get("request_id")
            if not isinstance(identity, str):
                raise DiagRefused(f"diag_ledger_unreadable {ledger}（request_id 缺失或非字符串）")
            if identity != own:
                continue
            if document.get("consumed", None) is not False:
                raise DiagRefused(f"request_consumed {own} 已于 {ledger.parent.name} 用掉（consumed="
                                  f"{document.get('consumed', '<missing>')!r}；仅字面 false 视为未消耗；结束或失败即用尽，不续试）")

    def preflight(self) -> None:
        print(f"=== {WORK_ID} {DIAG_BANNER} === Air {self.root} 板 {self.board_root}", flush=True)
        (self.root / "NOTES.md").write_text(
            f"<!-- {DIAG_BANNER}；request_id {self.entry.request_id}；自动粗账见 ops-diagnostic-ledger.json -->\n"
            + extract_block(self.repo / DIAG_OPS_DOC, "### 附录 0 ", "text"), encoding="utf-8")
        gate = release_gate(self.ctx, ledger_hits=(self.entry.ledger_title, self.entry.request_id))
        self.account.data.update(head=gate.block_11_14.splitlines()[0].split("=", 1)[1] if gate.block_11_14 else None,
                                 passed_candidate=gate.passed, rel=gate.rel)
        self.account.save()
        if not gate.ok:
            raise DiagRefused("release_gate " + ";".join(gate.stops))
        # BIND-3：发布引用账本唯一条目绑定（release_gate 的 1.5 子串命中照旧，此处另核同一条目）
        ledger = self.shell.run("show-ledger-entry", ["git", "-C", str(self.repo), "show", f"{gate.rel}:docs/authorizations.md"])
        binding = diag_ledger_binding(ledger.stdout if ledger.rc == 0 else None, self.entry)
        # BIND-4：本 id 的机读放行行，值须等于门核最新有效 passed_candidate（不以发布引用 rel 代替）
        proposal = self.shell.run("show-proposal", ["git", "-C", str(self.repo), "show", f"{gate.rel}:{PROPOSAL}"])
        binding.update(diag_release_binding(proposal.stdout if proposal.rc == 0 else None, self.entry, gate.passed))
        binding.update(passed_candidate=gate.passed, rel=gate.rel)
        self.account.data["entry_binding"].update(binding)
        self.account.save()
        self.recorder.event("diag_entry_binding", **self.account.data["entry_binding"])
        playbook, p2_object = self.arguments.playbook, self.arguments.p2_object
        self.account.data.update(playbook=playbook, p2_object=p2_object)
        self.account.save()
        path = freeze_plan(self.ctx, p2_object)
        self.plan, self.plan_sha = load_plan(path)
        self.recorder.event("diag_plan_frozen", playbook=playbook, plan_sha256=self.plan_sha)
        self.air_checks()

    def air_checks(self) -> None:
        """诊断页第 2 步 Air 本机只读核（干净树/_Recovery 已由放行核对；此处工具/环境/资产/烟测）。"""
        problems = [f"tool_missing {t}" for t in ("ssh", "tar", "shasum", "curl")
                    if shutil.which(t) is None and not (t == "ssh" and Path(self.ctx.ssh).is_file())]
        env = self.shell.run("air-env", [self.python, "-c", (
            "import numpy, cv2, lap, PIL, torch, ultralytics; print('ultralytics', ultralytics.__version__, "
            "'torch', torch.__version__, 'mps', torch.backends.mps.is_available())")])
        if env.rc != 0:
            problems.append(f"python_env rc={env.rc}")
        assets = self.shell.run("air-det-assets", [self.python, "-I", "-"], stdin_bytes=(
            "import hashlib, json\n"
            "d = json.load(open('config/det-assoc-v1.models.json'))\n"
            "for k in ('weights', 'freeze'):\n"
            "    p = d[k]['path']\n"
            "    try:\n"
            "        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()\n"
            "        print(k, p, 'OK' if h == d[k]['sha256'] else 'DIAG_FAULT sha_mismatch')\n"
            "    except OSError as e:\n"
            "        print(k, p, 'DIAG_FAULT', e)\n").encode())
        if assets.rc != 0 or "DIAG_FAULT" in assets.stdout or assets.stdout.count(" OK") != 2:
            problems.append(f"det_assoc_assets rc={assets.rc}")
        smoke = self.shell.run("smoke-check", [self.python, "-I", "-c", (
            'import sys; sys.path.insert(0, "."); from tools.language_latency import read_smoke_rows; '
            'r = read_smoke_rows("outputs/eng-sft/P1-ENG-SFT-002/data/smoke.jsonl", "outputs/eng-sft/P1-ENG-SFT-002/upload"); '
            'assert len(r) == 32, len(r); print("SMOKE_OK", len(r))')])
        if smoke.rc != 0 or "SMOKE_OK 32" not in smoke.stdout:
            problems.append("smoke_set")
        if problems:
            raise DiagRefused("air_checks " + "; ".join(problems) + "（补齐若需下载/安装即 STOP2 范畴，交回）")

    # -- 消耗性步骤 --

    def hold_runtime(self) -> None:
        report = archive_attempt(self.repo, self.root, "hold", diagnostic_dest=self.root / "hold" / "held")
        self.held = True
        self.recorder.event("runtime_held", moved=report["moved"])

    def air_reading(self, source: str) -> int:
        pending = 0
        if self.play_started and not self.frames_moved:
            pending = tree_bytes(self.repo / "runtime" / "frames")
        control = self.control.bytes() if self.control is not None and not self.control.released else 0
        value = tree_bytes(self.root) + pending + control
        self.account.disk("air", value, source)
        return value

    def board_reading(self, text: str, source: str) -> int | None:
        values = [int(m.group(1)) for line in text.splitlines()
                  if (m := DIAG_DU_LINE.match(line)) and m.group(2).rstrip("/") == self.board_root]
        value = values[-1] if values else None
        self.account.disk("board", value, source)
        return value

    def prepare_board(self) -> None:
        resolve_script = self.root / "prep" / "diag-assets.py"
        resolve_script.write_text(extract_block(self.repo / DIAG_OPS_DOC, "### 附录 1 ", "python"), encoding="utf-8")
        resolved = self.shell.run("diag-resolve", [self.python, "-I", "-B", str(resolve_script), "resolve"],
                                  stdout_path=self.root / "prep" / "assets-src.env")
        lines = resolved.stdout.splitlines()
        if resolved.rc != 0 or not lines or lines[-1] != "# DIAG_RESOLVE_OK":
            raise DiagRefused(f"diag_resolve rc={resolved.rc} last={lines[-1] if lines else ''}")
        for line in lines[:-1]:
            key, _, raw = line.partition("=")
            tokens = shlex.split(raw)
            if len(tokens) != 1:
                raise DiagRefused(f"diag_resolve_bad_line {key!r}")
            self.values[key] = tokens[0]
        for key in ("WEIGHTS", "MMPROJ", "LLAMA_BIN", "EXP_WEIGHTS_SHA", "EXP_MMPROJ_SHA", "EXP_LLAMA_BIN_SHA"):
            if not self.values.get(key):
                raise DiagRefused(f"diag_resolve_missing {key}")
        try:
            self.ctx.board_ts = resolve_board_ts(self.ctx)
        except Stop as stop:
            raise DiagRefused(stop.detail) from stop
        self.allocate_control()  # DIAG-CONTROL-1：建不成短私有 ControlPath 即拒启（尚未占额）
        # —— 以下开始消耗（主连接尝试前即扣次）——
        self.account.consume()
        self.hold_runtime()
        self.air_reading("before board connection")
        self.conn1 = DiagConnection(self.ctx, self.account, "d1", self.control)
        self.conn1.open()
        check = self.root / "prep" / "board-check.sh"
        check.write_text("W={} M={} B={} R={}\n".format(*(shlex.quote(v) for v in (
            self.values["WEIGHTS"], self.values["MMPROJ"], self.values["LLAMA_BIN"], self.board_root)))
            + extract_block(self.repo / DIAG_OPS_DOC, "### 附录 2 ", "bash"), encoding="utf-8")
        run = self.conn1.chan("board-check", "bash -s", stdin_path=check, stdout_path=self.root / "board" / "check.txt")
        faults = [l for l in run.stdout.splitlines() if l.startswith("DIAG_FAULT")]
        if run.rc != 0 or "BOARD_CHECK_DONE" not in run.stdout.splitlines() or faults:
            raise DiagFault(f"board_check rc={run.rc} {faults[:3]}（若补齐需下载/传板即 STOP2，交回）", run.rc)
        gen = self.shell.run("diag-gen", [self.python, "-I", "-B", str(resolve_script), "gen", str(self.root / "board" / "check.txt"),
                                          str(self.root / "board" / "expect-assets.json")], env=self.values)
        if gen.rc != 0 or gen.stdout.strip().splitlines()[-1:] != ["DIAG_ASSETS_OK"]:
            raise DiagFault(f"diag_gen rc={gen.rc} {gen.stdout.strip().splitlines()[-1:]}", gen.rc)
        paths = json.loads((self.repo / "config/p1-eng-loop-002-board-deploy.json").read_text(encoding="utf-8"))["paths"]
        code_tar = self.root / "board" / "code.tar"
        if self.shell.run("code-tar", ["tar", "-cf", str(code_tar), *paths], env={"COPYFILE_DISABLE": "1"}).rc != 0:
            raise DiagFault("code_tar_create")
        air_sha = self.shell.run("air-sha", ["shasum", "-a", "256", *paths], stdout_path=self.root / "board" / "air.sha")
        if code_tar.stat().st_size >= DIAG_DISK_STOP_FRACTION * DIAG_LIMITS["board_bytes"]:
            raise DiagStop(1, f"board bytes: code.tar {code_tar.stat().st_size} B would approach the 200 MB root limit")
        root = shlex.quote(self.board_root)
        sync = self.conn1.chan("root-code", (
            f"mkdir -p -m 700 {DIAG_BOARD_PARENT} && mkdir -m 700 {root} {root}/code {root}/logs {root}/run "
            f"&& tar -xf - -C {root}/code && echo CODE_SYNC_OK"), stdin_path=code_tar)
        if "CODE_SYNC_OK" not in sync.stdout.split():
            raise DiagFault(f"code_sync rc={sync.rc}（根已存在或失败；不覆盖、不删）", sync.rc)
        quoted = " ".join(shlex.quote(p) for p in paths)
        verify = self.conn1.chan("code-verify", f"cd {root}/code || exit 97; sha256sum -- {quoted}; du -sb {root}; df -B1 /home/jetson",
                                 stdout_path=self.root / "board" / "board-verify.txt")
        board_sha = [l for l in verify.stdout.splitlines() if re.match(r"^[0-9a-f]{64}  ", l)]
        self.board_reading(verify.stdout, "after code sync")
        if air_sha.rc != 0 or verify.rc != 0 or board_sha != air_sha.stdout.splitlines():
            raise DiagFault("code_sha_mismatch")
        digest = desktop_digest(self.ctx)
        (self.root / "board" / "air-deploy-digest.txt").write_text(digest + "\n", encoding="utf-8")
        board = self.root / "board"
        (board / "serve-diag.sh").write_text(extract_block(self.repo / DIAG_OPS_DOC, "### 附录 3 ", "bash"), encoding="utf-8")
        (board / "serve-diag.py").write_text(extract_block(self.repo / DIAG_OPS_DOC, "### 附录 4 ", "python"), encoding="utf-8")
        inputs = {"BOARD_DIAG": self.board_root, "WEIGHTS": self.values["WEIGHTS"], "MMPROJ": self.values["MMPROJ"],
                  "DIAG_LLAMA_BIN": self.values["LLAMA_BIN"], "BOARD_TS": self.ctx.board_ts or ""}
        missing = [k for k, v in inputs.items() if not v]
        if missing:
            raise DiagFault("missing_input " + " ".join(missing))
        (board / "serve-diag.env").write_text("export " + " ".join(f"{k}={shlex.quote(v)}" for k, v in inputs.items()) + "\n",
                                              encoding="utf-8")
        run_tar = board / "run-files.tar"
        if self.shell.run("run-tar", ["tar", "-cf", str(run_tar), "-C", str(board), "expect-assets.json", "serve-diag.env",
                                      "serve-diag.sh", "serve-diag.py"], env={"COPYFILE_DISABLE": "1"}).rc != 0:
            raise DiagFault("run_tar_create")
        files = self.conn1.chan("run-files", f"tar -xf - -C {root}/run && echo RUN_FILES_OK && du -sb {root}", stdin_path=run_tar)
        self.board_reading(files.stdout, "after run files")
        if "RUN_FILES_OK" not in files.stdout.split():
            raise DiagFault(f"run_files rc={files.rc}", files.rc)
        self.conn1.close()
        self.conn1 = None
        self.air_reading("after board preparation")

    def allocate_control(self) -> None:
        """DIAG-CONTROL-1：建本次独占短私有目录并实测 d1/d2 两个 ControlPath（带 OpenSSH 后缀）可 bind；原流留指针。"""
        self.control = DiagControlDir.allocate(tuple(DIAG_CHANNELS))
        self.account.data["control_dir"] = self.control.record
        self.account.data["disk"]["air_source"] = (self.account.data["disk"]["air_source"]
                                                   + " + 本次私有 ControlPath 临时目录内各项 lstat 字节（诊断根外，照计）")
        self.account.save()
        self.recorder.event("diag_control_dir", **self.control.record)

    def start_service(self) -> None:
        self.account.require_time(LISTEN_WAIT_S, "service start (cold load ≤ 300 s)")
        assert self.control is not None
        self.conn2 = DiagConnection(self.ctx, self.account, "d2", self.control)
        self.conn2.open()
        self.serve = DiagServe(self.ctx, self.conn2, self.account, self.board_root)
        self.serve.start()

    def check_status(self) -> None:
        """身份核：`/status` 恰一次 + 诊断页附录 5 判据（六键、部署摘要与 Air 重算一致、无 `http_budget`）。"""
        out = self.root / "board" / "status-1.json"
        self.shell.run("status-1", ["curl", "-s", "--noproxy", "*", "--max-time", "5",
                                    f"http://{self.ctx.board_ts}:{SERVE_PORT}/status"], stdout_path=out)
        script = self.root / "prep" / "status-check.py"
        script.write_text(extract_block(self.repo / DIAG_OPS_DOC, "### 附录 5 ", "python"), encoding="utf-8")
        check = self.shell.run("status-check", [self.python, "-I", "-B", str(script), str(out)], env={"REPO": str(self.repo)})
        last = check.stdout.strip().splitlines()[-1:]
        if check.rc != 0 or last != ["DIAG_STATUS_OK"]:
            raise DiagFault(f"status_check rc={check.rc} {[l for l in check.stdout.splitlines() if l.startswith('DIAG_FAULT')][:3]}"
                            "（错接正式服务或身份不符：拒绝继续）", check.rc)

    def make_receipt(self) -> None:
        """诊断页第 5 步：覆盖文件 → measure（≤ 1）→ 仅 rc 0 才 k-receipt（≤ 1）；只留诊断根，不重测、不手造。"""
        digest = generate_overlay(self.ctx, account=False)
        self.overlay_written = True
        (self.root / "prep" / "overlay.sha").write_text(digest + "  runtime/scenario_config.json\n", encoding="utf-8")
        report = self.root / "receipt" / "jetson-report.json"
        self.account.take("measure_runs")
        self.account.data["measure"]["runs"] += 1
        measure = self.shell.run("measure", measure_argv(self.ctx, report), stdout_path=self.root / "receipt" / "measure.stdout")
        (self.root / "receipt" / "measure.stderr").write_text(measure.stderr, encoding="utf-8")
        self.account.data["measure"].update(rc=measure.rc, first_failure=first_measure_failure(report) if measure.rc else None)
        self.account.save()
        if measure.rc != 0:
            raise DiagFault(f"measure_rc={measure.rc}（不跑 k-receipt、不进 Play）", measure.rc)
        out = self.root / "receipt" / "jetson-k-receipt.json"
        self.account.take("k_receipt_runs")
        self.account.data["k_receipt"]["runs"] += 1
        receipt = self.shell.run("k-receipt", k_receipt_argv(self.ctx, report, out), stdout_path=self.root / "receipt" / "k-receipt.stdout")
        (self.root / "receipt" / "k-receipt.stderr").write_text(receipt.stderr, encoding="utf-8")
        self.account.data["k_receipt"]["rc"] = receipt.rc
        self.account.save()
        if receipt.rc != 0:
            raise DiagFault(f"k_receipt_rc={receipt.rc}（非合格不进依赖会话）", receipt.rc)
        self.receipt_path = out

    def start_web(self, receipt: Mapping[str, float]) -> None:
        log = web.OpsLog(self.root / "play" / web.OPS_LOG)
        cli = web.CliRunner(self.python, self.repo, self.repo / "runtime")
        self.submitter = web.Submitter(cli, cli, log)
        plan_sha = self.plan_sha

        class Idle:
            def snapshot(self) -> dict[str, Any]:
                return {"playbook": None, "attempt": None, "plan_sha256": plan_sha, "current": None, "decision_step": None, "steps": []}

            def blocked(self) -> str | None:
                return None

            current_send_step = decision_step = staticmethod(lambda *_: None)
            record_skip = record_send = record_decision = record_operator_stop = staticmethod(lambda *_: None)

        self.app = web.App(monitor_factory=lambda sid, sdir: web.Monitor(self.repo / "runtime", sid, sdir, receipt),
                           submitter=self.submitter, log=log, scheduler=Idle(), feedback_path=self.root / "play" / "feedback.jsonl",
                           banner=DIAG_BANNER)
        self.server = web.build_server(self.app, self.arguments.port)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        threading.Thread(target=web.poll_forever, args=(self.app, self.web_stop), daemon=True).start()
        print(f"操作页 http://{web.HOST}:{self.server.server_address[1]}/ （只本机；{DIAG_BANNER}）", flush=True)

    def request_stop(self, why: str) -> None:
        """安全中止：沿 W4 共用提交通道发本会话 stop（每会话至多一次，与网页中止按钮同一绑定）。

        另一提交在途时不发（不是发送、也不是重试），由调用方下个循环再试；已发过即不再发，结果未知不换 id。
        """
        if self.submitter is None or self.session_id is None or self.submitter.in_flight.locked():
            return
        reply = send_session_stop(self.submitter, self.session_id, why)
        if reply is None or (reply.get("refused") and self.session_id not in self.submitter.stop_sent):
            return
        self.recorder.event("diag_stop_request", why=why, reply=reply)
        self.account.data["play"]["stop_request_id"] = self.submitter.stop_sent.get(self.session_id)
        self.account.save()
        if reply.get("unknown"):
            self.account.unknown(f"stop request_id={reply.get('request_id')} result unknown")

    def halt(self, why: str) -> None:
        """C6-1：一发生 STOP/故障/中断/到时即不可逆封住 runner 与网页的业务动作（共享通道 `Submitter.seal`），
        计划不再推进；随即沿共享通道请求原 stop（至多一次）。迟到回执/状态不解封。"""
        if self.halted_reason is None:
            self.halted_reason = why
            self.account.data["play"]["halted"] = {"reason": why, "at_unix_s": time.time()}
            self.account.save()
            if self.scheduler is not None:
                self.scheduler.halt(why)
            elif self.submitter is not None and self.session_id is not None:
                self.submitter.seal(self.session_id, why)
            self.recorder.event("diag_halt", reason=why)
        self.request_stop(why)

    def monitor_limits(self) -> None:
        """Play 期间两端轮询读数；将达上限或墙钟只剩收尾预留即 STOP1、停业务收尾。"""
        now = time.time()
        if now - self.last_air_du >= DIAG_AIR_DU_INTERVAL_S:
            self.last_air_du = now
            if self.account.near_limit("air", self.air_reading("play poll")):
                raise DiagStop(1, "Air diagnostic root approaching 250 MB")
        if now - self.last_board_du >= DIAG_BOARD_DU_INTERVAL_S and self.conn2 is not None and self.conn2.open_ok:
            self.last_board_du = now
            du = self.conn2.chan("board-du", f"du -sb {shlex.quote(self.board_root)}")
            if self.account.near_limit("board", self.board_reading(du.stdout, "play poll")):
                raise DiagStop(1, "board diagnostic root approaching 200 MB")
        if self.account.remaining() <= DIAG_CLOSEOUT_RESERVE_S:
            raise DiagStop(1, f"wall: only closeout reserve left ({self.account.remaining():.0f} s)")

    def play(self) -> None:
        assert self.plan is not None and self.receipt_path is not None
        playbook = self.arguments.playbook
        self.account.require_time(PLAY_START_WAIT_S + LIMITS["t_sess_s"] + UNITY_STOP_QUIET_S + 60, f"Play ({playbook})")
        try:
            receipt = web.load_receipt(self.receipt_path)
        except Exception as error:  # noqa: BLE001 - 诊断：记故障
            raise DiagFault(f"k_receipt_invalid {type(error).__name__}: {error}") from error
        self.start_web(receipt)
        self.account.take("plays")
        self.account.take("sessions")
        self.account.data["play"]["count"] += 1
        self.account.save()
        waiting_since = time.time()
        print(f"请本人在 Unity 按 Play（诊断；剧本 {playbook}；仅此一次）……", flush=True)
        self.play_started = True
        f0 = wait_for_play(self.repo, waiting_since, PLAY_START_WAIT_S)
        self.account.data["play"]["first_frame_seen_unix_s"] = time.time()
        if f0 is None:
            raise DiagFault("unity_not_in_play（Play 已计 1 次；不重试、不开第二次）")
        t_sess = min(LIMITS["t_sess_s"], (1490 - f0) / 5.0)
        self.account.data["play"].update(f0=f0, t_sess_s=t_sess)
        self.account.save()
        if t_sess <= 0:
            raise DiagFault(f"t_sess_nonpositive f0={f0}")
        self.account.require_time(t_sess + 60, "session")
        self.session_id = DIAG_SESSION_PREFIX + time.strftime("%H%M%S", time.gmtime())
        self.account.data["play"]["session_id"] = self.session_id
        self.account.save()
        sessions = self.root / "play" / "sessions"
        sessions.mkdir(parents=True, exist_ok=True)
        argv = session_argv(self.ctx, self.session_id, sessions, self.receipt_path, t_sess, diagnostics_root=self.root / "segments")
        self.recorder.event("session_start", session_id=self.session_id, argv=argv)
        with (self.root / "play" / f"{self.session_id}.session-process.log").open("ab") as log:
            self.session_proc = subprocess.Popen(argv, cwd=self.repo, stdout=log, stderr=subprocess.STDOUT)
        assert self.app is not None and self.submitter is not None
        self.monitor = self.app.bind_session(self.session_id, sessions / self.session_id)
        self.scheduler = PlanScheduler(self.plan["playbooks"][playbook], playbook=playbook, session_id=self.session_id,
                                       plan_sha256=str(self.plan_sha), monitor=self.monitor, submitter=self.submitter, log=self.app.log)
        self.app.scheduler = self.scheduler
        hard_deadline = waiting_since + LIMITS["play_wall_s"] + PLAY_START_WAIT_S
        # 一旦 STOP/故障/中断：`halt` 立即不可逆封住业务（计划不再推进、网页只剩 stop），只发一次 stop，
        # 之后只读原流、等会话退出再收尾；迟到的 TERMINAL/回执不恢复任何动作（C6-1）。
        while self.session_proc.poll() is None and time.time() < hard_deadline:
            try:
                try:
                    self.monitor.poll()
                except Exception as error:  # noqa: BLE001 - 读不到就不推进
                    self.monitor.fail(error)
                self.scheduler.tick()
                if self.halted_reason is None:
                    self.monitor_limits()
                else:
                    self.request_stop(self.halted_reason)  # 仅在 stop 尚未发出且无在途提交时真正发送一次
                time.sleep(TICK_S)
            except DiagStop as stop:
                self.account.stop(stop)
                self.halt(f"STOP{stop.category} {stop.detail}")
            except DiagFault as fault:
                self.account.fault(fault.detail, fault.rc)
                self.halt(f"DIAG_FAULT during play: {fault.detail}")
            except KeyboardInterrupt:
                if self.halted_reason is not None:
                    raise
                self.account.stop(DiagStop(4, "operator Ctrl-C during play"))
                self.halt("STOP4 operator Ctrl-C during play")
        self.finish_play()

    def finish_play(self) -> None:
        assert self.monitor is not None and self.scheduler is not None and self.session_proc is not None
        if self.session_proc.poll() is None:
            self.halt(self.halted_reason or "play wall reached")
            self._wait_session()
        self._record_play()
        self.stop_unity_and_move_frames()

    def _wait_session(self) -> None:
        """等会话进程自行退出 ≤ `DIAG_SESSION_STOP_WAIT_S`（期间 stop 只在未发出时补发一次）；不杀进程。"""
        assert self.session_proc is not None
        deadline = time.time() + DIAG_SESSION_STOP_WAIT_S
        while self.session_proc.poll() is None and time.time() < deadline:
            self.request_stop(self.halted_reason or "closeout")
            time.sleep(TICK_S)

    def _record_play(self) -> None:
        """末次读原流并记录 rc/终止原因/逐步结局（幂等；收尾中可再调用，C6-3）。"""
        if self.monitor is None or self.scheduler is None or self.session_proc is None or self.submitter is None:
            return
        held = self.submitter.in_flight.acquire(timeout=web.CLI_TIMEOUT_S + 5.0)  # 在途提交及其计划记录先完成
        try:
            try:
                self.monitor.poll()
            except Exception as error:  # noqa: BLE001
                self.monitor.fail(error)
            self.scheduler.tick()
            self.scheduler.halt(self.halted_reason or "play closeout")  # 已走完只封通道；未走完则封住并分列
        finally:
            if held:
                self.submitter.in_flight.release()
        state = (self.monitor.public(time.time()).get("state") or {})
        play = self.account.data["play"]
        play.update(session_rc=self.session_proc.poll(),
                    terminal_reason=state.get("reason") if state.get("state") == "TERMINAL" else None,
                    steps=self.scheduler.snapshot()["steps"])
        blocked = self.scheduler.blocked()
        if blocked and not self.blocked_noted:
            self.blocked_noted = True
            self.account.unknown(f"plan blocked: {blocked}")
        self.account.data["not_executed"] = [s["step_id"] for s in self.scheduler.snapshot()["steps"] if s["status"] == "NOT_EXECUTED"]
        self.account.save()

    def stop_unity_and_move_frames(self) -> None:
        if not self.play_started or self.frames_moved:
            return
        print("会话已结束：请本人在 Unity 按停止……", flush=True)
        quiet, last = wait_unity_stopped(self.repo, UNITY_STOP_QUIET_S, time.time() + DIAG_UNITY_STOP_WAIT_S)
        self.account.data["play"].update(frames_quiet=quiet, last_frame_id=last)
        self.account.save()
        if not quiet:
            self.account.unknown("Unity frames still advancing after the stop wait（未移动帧环；请本人停止 Play）")
            return
        dest = self.root / "play" / (self.session_id or "no-session")
        report = archive_attempt(self.repo, self.root, self.session_id or "no-session", diagnostic_dest=dest, include_layout=False)
        self.frames_moved = True
        self.recorder.event("frames_moved", **report)
        if self.session_id:
            loads = []
            for path in sorted((self.root / "segments" / self.session_id).rglob("model_cache.json")):
                loads.append(int((web.read_json(path) or {}).get("model_loads", -1)))
            self.account.data["yolo_loads"] = sum(loads) if loads else "UNKNOWN（无段 model_cache 原流）"
            if loads and sum(loads) > 1:
                self.account.data["deviations"].append(f"YOLO loads {loads} > 1（照记）")
            self.account.save()

    # -- 收尾（§4.8；每步独立记录，不因前一步失败而跳过安全释放） --

    def closeout(self) -> None:
        steps = (
            ("session", self._close_session),
            ("unity_and_frames", self.stop_unity_and_move_frames),
            ("service_release", self._close_service),
            ("logs", self._close_logs),
            ("connections", self._close_connections),
            ("runtime_restore", self._restore_runtime),
        )
        for name, action in steps:
            try:
                action()
                self.account.data["closeout"].setdefault(name, "done")
            except KeyboardInterrupt:
                self.account.data["closeout"][name] = "interrupted"
                self.account.unknown(f"closeout {name} interrupted by Ctrl-C")
            except Exception as error:  # noqa: BLE001 - 收尾：记录后继续下一步安全动作
                self.account.data["closeout"][name] = f"{type(error).__name__}: {error}"
                self.account.unknown(f"closeout {name}: {type(error).__name__}: {error}")
            self.account.save()
        self.air_reading("final")
        status = self.shell.run("final-status", ["git", "-C", str(self.repo), "status", "--porcelain", "--untracked-files=normal"])
        self.account.data["closeout"]["worktree_status_lines"] = len([l for l in status.stdout.splitlines() if l.strip()])
        self.account.finish()

    def _close_session(self) -> None:
        if self.session_proc is None:
            return
        if self.session_proc.poll() is None:
            self.halt(self.halted_reason or "closeout")
            self._wait_session()
            if self.session_proc.poll() is None:
                self.account.unknown("session process still running after stop（本工具不杀进程）")
                self.account.stop(DiagStop(3, "session process cannot be stopped safely"))
        self._record_play()

    def _close_service(self) -> None:
        if self.serve is None or self.serve.proc is None:
            return
        report = self.serve.stop_and_release()
        self.account.data["serve"]["release"] = report
        self.account.save()
        if report.get("board_du_bytes") is not None:
            self.account.disk("board", report["board_du_bytes"], "closeout appendix 7")
        if not report.get("released"):
            self.account.unknown(f"release not proven {report}（不清未知进程）")
            self.account.stop(DiagStop(3, "board port/process release cannot be confirmed"))

    def _close_logs(self) -> None:
        if self.conn2 is None or not self.conn2.open_ok or self.serve is None:
            return
        root = shlex.quote(self.board_root)
        target = self.root / "board" / "board-logs.tar"
        run = self.conn2.chan("logs", f"tar -cf - -C {root} --exclude=logs/cache --exclude=logs/tmp --exclude=logs/scratch logs run",
                              stdout_path=target)
        self.account.data["closeout"]["logs_rc"] = run.rc

    def _close_connections(self) -> None:
        try:
            for connection in (self.conn1, self.conn2):
                if connection is not None:
                    connection.close()
            self.conn1 = self.conn2 = None
        finally:
            self._release_control()

    def _release_control(self) -> None:
        """主连接关闭（`-O exit`）之后才释放：只删本次所建空目录；有残留不删不复用，记 UNKNOWN 与路径指针。"""
        if self.control is None or self.control.released:
            return
        self.air_reading("before control dir release")
        if self.conn1 is not None or self.conn2 is not None:
            self.account.unknown(f"control dir {self.control.path} kept: connection close not completed")
            self.account.data["control_dir"] = self.control.record
            self.account.save()
            return
        result = self.control.release()
        self.account.data["control_dir"] = self.control.record
        self.account.save()
        self.recorder.event("diag_control_dir_release", path=str(self.control.path), **result)
        if not result["removed"]:
            self.account.unknown(f"control dir {self.control.path} not removed: left={result['left_entries']}"
                                 f"{' ' + result['error'] if result.get('error') else ''}（不删未知/未退出的套接字，不复用）")

    def _restore_runtime(self) -> None:
        if not self.held:
            return
        runtime = self.repo / "runtime"
        overlay = runtime / "scenario_config.json"
        if self.overlay_written and overlay.exists():
            target = self.root / "hold" / "overlay-diag.json"
            if target.exists():
                raise DiagFault("overlay hold target exists")
            overlay.rename(target)
        if self.play_started and not self.frames_moved and (runtime / "frames").exists():
            # 本批产物只移动（未能确认 Unity 已停则不碰）
            self.account.unknown("frames not moved: Unity stop not confirmed; left in runtime/")
        restored = []
        held = self.root / "hold" / "held"
        for item in sorted(held.iterdir()) if held.is_dir() else []:
            target = runtime / item.name
            if target.exists() or target.is_symlink():
                self.account.unknown(f"hold item {item.name} not restored: runtime/{item.name} exists")
                continue
            item.rename(target)
            restored.append(item.name)
        self.account.data["closeout"]["restored"] = restored

    # -- 摘要与本人反馈（独立进程；不评分、不判门） --

    def run_offline_summary(self) -> None:
        if self.plan is None or self.session_id is None:
            return
        record = {"mode": "diagnostic", "banner": DIAG_BANNER, "request_id": self.entry.request_id, "attempts": [{
            "playbook": self.arguments.playbook, "session_id": self.session_id,
            "steps": self.scheduler.snapshot()["steps"] if self.scheduler else None,
            "terminal_reason": self.account.data["play"]["terminal_reason"],
            "model_loads": self.account.data["yolo_loads"], "stop": self.account.data["stop"],
            "play_button_times": "UNKNOWN（出帧/TERMINAL 不冒充按钮时刻）"}]}
        (self.root / "play" / "play-record.json").write_text(json.dumps(record, ensure_ascii=False, indent=1, default=str) + "\n",
                                                             encoding="utf-8")
        summary = self.shell.run("summarize-diagnostic", [
            self.python, "-m", "tools.eng_loop2.summarize_ops", "--ops-dir", str(self.root / "play"),
            "--plan", str(self.root / "plan" / "ops-plan.json"), "--mode", "diagnostic", "--python", self.python])
        self.account.data["post_closeout"]["summary_rc"] = summary.rc
        self.account.save()
        if self.app is None:
            return
        text_path = self.root / "play" / "ops-summary.md"
        summary_json = web.read_json(self.root / "play" / "ops-summary.json") or {}
        self.app.set_summary({"attempts": [{"session_id": self.session_id}],
                              "text": text_path.read_text(encoding="utf-8") if text_path.is_file() else summary.stdout,
                              "summary_sha256": summary_json.get("summary_sha256")})
        window = max(0.0, min(float(self.arguments.feedback_wait_s), self.account.remaining()))
        print(f"诊断摘要已就绪（{DIAG_BANNER}）：可在操作页点「通过/失败/受阻」；最多等 {window:.0f} s 或 Ctrl-C", flush=True)
        deadline = time.time() + window
        try:
            while not self.app.feedback_given and time.time() < deadline:
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        self.account.data["post_closeout"].update(feedback_window_s=window, feedback_given=sorted(self.app.feedback_given))
        self.account.save()

    def shutdown_web(self) -> None:
        self.web_stop.set()
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()

    # -- 主流程 --

    STAGES = ("preflight", "prepare_board", "start_service", "check_status", "make_receipt", "play")

    def execute(self) -> int:
        consumed_phase = False
        done: list[str] = []
        try:
            try:
                for name in self.STAGES:
                    getattr(self, name)()
                    done.append(name)
                    consumed_phase = consumed_phase or name == "preflight"
            except DiagRefused:
                raise
            except DiagStop as stop:
                self.account.stop(stop)
            except DiagFault as fault:
                self.account.fault(fault.detail, fault.rc)
            except Stop as stop:  # 复用的正式辅助函数抛出：只记原文为诊断故障，不套正式码
                self.account.fault(stop.detail)
            except KeyboardInterrupt:
                self.account.stop(DiagStop(4, "operator Ctrl-C"))
            except Exception as error:  # noqa: BLE001 - 诊断：未知错误即 UNKNOWN 并安全收尾
                self.account.fault(f"UNEXPECTED {type(error).__name__}: {error}")
                self.account.unknown(f"unexpected {type(error).__name__}")
        except DiagRefused as refused:
            self.account.data["refused"] = str(refused)
            self.account.save()
            if not self.account.data["consumed"]:
                self.account.finish()
                self.shutdown_web()
                print(f"DIAG_REFUSED {refused}（未消耗 {self.entry.request_id} 受限维度）")
                return 3
            self.account.fault(f"refused after consumption: {refused}")
        self.account.data["stages_done"] = done
        self.account.data["stages_not_executed"] = [n for n in self.STAGES if n not in done]
        self.account.save()
        if consumed_phase or self.account.data["consumed"]:
            self.closeout()
        try:
            self.run_offline_summary()
        except BaseException as error:  # noqa: BLE001 - 摘要/反馈一步失败只记录，不跳过关闭本地网页与非 0 出口（C6-2）
            self.account.unknown(f"offline summary step: {type(error).__name__}: {error}")
        finally:
            try:
                self.shutdown_web()
            except BaseException as error:  # noqa: BLE001
                self.account.unknown(f"web shutdown: {type(error).__name__}: {error}")
        data = self.account.data
        if self.account.clean():
            print(f"DIAG_DONE {self.root}/ops-diagnostic-ledger.json（{DIAG_BANNER}）")
            return 0
        print(f"DIAG_END_WITH_ISSUES stop={data['stop']} faults={len(data['faults'])} unknown={len(data['unknown'])} "
              f"not_executed={data['not_executed']} ledger={self.root}/ops-diagnostic-ledger.json（{DIAG_BANNER}）")
        return 3


def stage_diag(arguments: argparse.Namespace) -> int:
    """`play_ops --mode diagnostic diag --request-id <已签条目 id> --playbook P1 --p2-object …`（IR-OPS-5；BIND-1…5）。"""
    try:
        diag_entry_for(arguments.request_id, arguments.playbook)  # 建根前：未知 / 已耗尽 / 剧本未签
    except DiagRefused as refused:
        print(f"DIAG_REFUSED {refused}（建根前拒启；未消耗任何受限维度）", file=sys.stderr)
        return 3
    try:
        run = DiagnosticRun(arguments)
    except DiagRefused as refused:
        print(f"DIAG_REFUSED {refused}（未消耗 {arguments.request_id} 受限维度）")
        return 3
    return run.execute()


# --- CLI ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="play_ops", description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".")
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--python", default=DEFAULT_PY)
    parser.add_argument("--ssh", default="ssh")
    parser.add_argument("--alias", default=HOST_ALIAS)
    parser.add_argument("--docwt", default=None)
    parser.add_argument("--mode", choices=("formal", "diagnostic"), default="formal")
    sub = parser.add_subparsers(dest="stage", required=True)
    plan = sub.add_parser("plan", help="Play 前离线冻结计划（运行原 derive-bc，核对操作单第 7 节）")
    plan.add_argument("--p2-object", required=True, choices=("red_car", "B", "C"))
    sub.add_parser("gate", help="第 1 节 1.0–1.5 机械核对")
    sub.add_parser("source", help="第 0.3 节来源核验（只核 Air 现有原件）")
    diag = sub.add_parser("diag", help=f"IR-OPS-5 诊断（仅 --mode diagnostic；{DIAG_BANNER}）")
    diag.add_argument("--request-id", required=True,
                      help=f"须逐字为已签诊断条目 {DIAG_RETRY1_REQUEST_ID}（旧 {DIAG_REQUEST_ID} 已耗尽、无条件拒；其他 id 无入口）")
    diag.add_argument("--playbook", required=True, choices=("P1", "P2", "P3"),
                      help="开跑前本人选定并冻结的一个既定剧本；须在条目已签剧本内（DIAG:RETRY:1 只签 P1，其余建根前拒）")
    diag.add_argument("--p2-object", required=True, choices=("red_car", "B", "C"))
    diag.add_argument("--port", type=int, default=web.DEFAULT_PORT)
    diag.add_argument("--feedback-wait-s", type=float, default=300.0, help="摘要后等待本人反馈的上限（再受 45 min 总墙钟约束）")
    for name in ("prep", "receipt", "play"):
        stage = sub.add_parser(name)
        stage.add_argument("--registered-release", type=Path, default=None, help="1.6 已登记进 Unity 日志的放行原流文件")
        if name == "play":
            stage.add_argument("--playbooks", nargs="+", default=["P1", "P2", "P3"], choices=("P1", "P2", "P3"))
            stage.add_argument("--port", type=int, default=web.DEFAULT_PORT)
            stage.add_argument("--feedback-wait-s", type=float, default=1800.0,
                               help="收尾摘要就绪后等待本人反馈的上限（板已释放，不占资源）")
    return parser


STAGES = {"plan": stage_plan, "gate": stage_gate, "source": stage_source, "prep": stage_prep, "receipt": stage_receipt, "play": stage_play}


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    # IR-OPS-5：模式按显式选择独立路由；正式与诊断不混根、不混账、不互转。
    if arguments.mode == "diagnostic":
        if arguments.stage != "diag":
            print(f"STOP diagnostic_mode_refused: 诊断模式只运行 diag 阶段（{DIAG_BANNER}）；正式阶段不在诊断模式执行",
                  file=sys.stderr)
            return 3
        return stage_diag(arguments)
    if arguments.stage == "diag":
        print("STOP S-PRECHECK diag_stage_requires_mode_diagnostic（正式模式不执行诊断）", file=sys.stderr)
        return 3
    ctx = make_context(arguments, arguments.stage)
    try:
        code = STAGES[arguments.stage](ctx, arguments)
    except Stop as stop:
        ctx.recorder.event("stop", code=stop.code, detail=stop.detail)
        print(f"STOP {stop.code} {stop.detail}")
        return 3
    except (KeyboardInterrupt, Exception) as error:  # noqa: BLE001 - 阶段内已安全收尾；不明/中断记 UNKNOWN 非 0 退出
        failure = describe_failure(error) or {}
        ctx.recorder.event("stop", code=failure.get("code"), detail=failure.get("detail"))
        print(f"STOP {failure.get('code')} {failure.get('detail')}")
        return 3
    ctx.recorder.event("stage_end", rc=code)
    return code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
