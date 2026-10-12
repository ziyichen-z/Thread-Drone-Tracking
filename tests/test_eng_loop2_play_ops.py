"""P1-ENG-LOOP-002 OpsK1K2K3K4：`tools/eng_loop2/play_ops.py`（AC-8/10/15/16 修订；O1–O4）。

生产入口 `play_ops.main` / 生产函数 + 临时本地替身：临时 git 仓库（bare origin + 执行检出 + 文档检出）、
假 `ssh`（主连接/控制套接字/通道/交互 serve 会话）、假 `curl`（/status）、Python 替身（只拦截 measure/
k-receipt/derive-bc/score/run/烟测/部署摘要，其余原样转真实解释器）。零模型、零 SSH/板/Unity、
不写实际 runtime/。
"""

from __future__ import annotations

import http.client
import io
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from controller import language_bridge as bridge
from controller.language_loop import FixtureFramePublisher, build_k_receipt
from tools.eng_loop2 import operator_web as web
from tools.eng_loop2 import play_ops as ops
from tools.eng_loop2 import summarize_ops as summ

REPO = Path(__file__).resolve().parents[1]
REAL_PY = sys.executable
BOARD_TS = "100.100.100.100"

FAKE_SSH = r'''#!__PY__
import json, os, sys, hashlib, time
cfg = json.load(open(os.environ["FAKE_CFG"]))
args = sys.argv[1:]
log = open(os.environ["FAKE_LOG"], "a")
log.write(json.dumps({"tool": "ssh", "argv": args}) + "\n"); log.flush()
def opt(name):
    return args[args.index(name) + 1] if name in args else None
if args[:1] == ["-G"]:
    print("hostname " + cfg.get("board_ts", "100.100.100.100")); print("user jetson"); sys.exit(0)
if "-O" in args:
    cm = opt("-S"); op = opt("-O")
    if op == "check":
        marker = cfg.get("check_fail_marker")
        sys.exit(0 if os.path.exists(cm) and not cfg.get("check_fail") and not (marker and os.path.exists(marker)) else 255)
    if op == "exit":
        if cfg.get("exit_keeps_socket"):
            sys.exit(255)
        if os.path.exists(cm): os.remove(cm)
        sys.exit(0)
if "-fN" in args:
    if cfg.get("master_rc", 0):
        sys.exit(cfg["master_rc"])
    path = [a.split("=", 1)[1] for a in args if a.startswith("ControlPath=")][0]
    if cfg.get("real_control_socket"):
        # 同 OpenSSH mux.c muxserver_listen：先在 <ControlPath>.<16 位随机> 上真实 bind 本机 AF_UNIX，再改名为 ControlPath
        import random, socket, string
        tmp = path + "." + "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            listener.bind(tmp)
        except OSError as error:
            sys.stderr.write('unix_listener: path "%s" too long for Unix domain socket (%s)\n' % (tmp, error)); sys.exit(255)
        listener.close(); os.rename(tmp, path); sys.exit(0)
    open(path, "w").close(); sys.exit(0)
remote = args[-1]
d = cfg.get("diag", {})
def du_line(text):
    import shlex
    path = shlex.split(text.split("du -sb", 1)[1].split(";")[0].split("&&")[0])[0]
    return "%d\t%s" % (d.get("board_du", 4096), path)
if remote == "bash -s":
    script = sys.stdin.buffer.read().decode()
    import shlex
    first = dict(kv.split("=", 1) for kv in shlex.split(script.splitlines()[0]))
    lines = ["=== board check ===", "2026-10-08T00:00:00Z", "hostname=jetson-orin arch=aarch64 user=jetson"]
    lines.append(("DIAG_FAULT diag_root_exists " if d.get("root_exists") else "diag_root_absent ") + first["R"])
    for key in ("WEIGHTS", "MMPROJ", "LLAMA_BIN"):
        lines.append("%s|regular file|1" % cfg["paths"][key])
    for key in ("WEIGHTS", "MMPROJ", "LLAMA_BIN"):
        lines.append("%s  %s" % (cfg["sha"][key], cfg["paths"][key]))
    lines += ["sha_rc=0", cfg.get("version_line", "version: 1234 (deadbeef)"), "version_rc=0", "ss_rc=0", "pgrep_rc=1",
              "Python 3.10.12", "BOARD_CHECK_DONE"]
    print("\n".join(lines)); sys.exit(0)
if "CODE_SYNC_OK" in remote:
    sys.stdin.buffer.read()
    if not d.get("root_exists"): print("CODE_SYNC_OK")
    sys.exit(0 if not d.get("root_exists") else 1)
if "RUN_FILES_OK" in remote:
    sys.stdin.buffer.read(); print("RUN_FILES_OK"); print(du_line(remote)); sys.exit(0)
if remote.startswith("du -sb"):
    print(du_line(remote)); sys.exit(0)
if "bash -s" in remote and "timeout" in remote:
    sys.stdin.buffer.read(); print(cfg.get("prep_stdout", "P01 ok\nfinal=OK")); sys.exit(cfg.get("prep_rc", 0))
if "ROOT_CREATED" in remote:
    print("ROOT_CREATED"); sys.exit(0)
if "--version" in remote:
    for key in ("WEIGHTS", "MMPROJ", "LLAMA_BIN"):
        print("%s  %s" % (cfg["sha"][key], cfg["paths"][key]))
    print(cfg.get("version_line", "version: 1234 (deadbeef)")); print("rc=0"); sys.exit(0)
if remote.startswith("tar -xf") or remote.startswith("cat >"):
    sys.stdin.buffer.read(); sys.exit(0)
if "sha256sum --" in remote:
    import shlex
    for p in shlex.split(remote.split("sha256sum --", 1)[1].split(";")[0]):
        data = open(p, "rb").read()
        if cfg.get("tamper") == p: data += b"x"
        print("%s  %s" % (hashlib.sha256(data).hexdigest(), p))
    print(du_line(remote)); sys.exit(0)
if remote.startswith("tar -cf -"):
    sys.stdout.buffer.write(b"LOGTAR"); sys.exit(0)
if "exec bash" in remote:
    out = sys.stdout
    serve = cfg.get("serve", {})
    buf = b""; serving = False; diag_serving = False; board_root = None
    while True:
        ch = sys.stdin.buffer.read(1)
        if not ch: break
        if ch == b"\x03":
            if diag_serving:
                out.write("^C\nDIAG serve_rc=0\nserve_rc=0\nserve_diag_sh_rc=0\n"); out.flush(); diag_serving = False
            elif serving:
                out.write("^C\nserve_rc=%d\n" % serve.get("rc_after_interrupt", 0)); out.flush(); serving = False
            continue
        buf += ch
        if ch != b"\n": continue
        line = buf.decode(); buf = b""
        log.write(json.dumps({"tool": "serve-typed", "line": line.strip()}) + "\n"); log.flush()
        if line.startswith("R="):
            import shlex
            board_root = shlex.split(line[2:])[0]
            continue
        if "serve-diag.sh" in line:
            if d.get("serve_fault"):
                out.write("DIAG_FAULT missing_input WEIGHTS (no preflight, no load)\nserve_diag_sh_rc=97\n"); out.flush(); continue
            out.write("=== banner ===\nDIAG preflight ok serve_code_sha256=x machine=jetson\nDIAG_LOAD_START llama-server child (GGUF load)\n")
            out.write("DIAG language-serve listening on http://%s:18082 (llama-server pid 7 on 127.0.0.1:18081); Ctrl-C to stop\n"
                      % d.get("listen_host", cfg.get("board_ts", "100.100.100.100")))
            out.flush(); diag_serving = True; continue
        if "PORTS_RELEASED" in line:
            out.write(("STILL_LISTENING 0.0.0.0:18082" if d.get("still_listening") else "PORTS_RELEASED") + "\n"); out.flush(); continue
        if "NO_RESIDUAL_PROCESS" in line:
            if not d.get("residual"): out.write("NO_RESIDUAL_PROCESS\n"); out.flush()
            continue
        if 'du -sb "$R"' in line:
            out.write("%d\t%s\n" % (d.get("board_du", 4096), board_root)); out.flush(); continue
        if line.strip() == "echo DIAG_CLOSEOUT_DONE":
            out.write("DIAG_CLOSEOUT_DONE\n"); out.flush(); continue
        if "tools/language_serve.py" in line:
            if serve.get("startup_stop"):
                out.write(serve["startup_stop"] + "\n"); out.flush(); sys.exit(97)
            if "early_rc" in serve:
                out.write("serve_rc=%d\n" % serve["early_rc"]); out.flush(); continue
            out.write("language-serve listening on http://%s:18082\n" % serve.get("listen_host", cfg.get("board_ts", "100.100.100.100"))); out.flush()
            serving = True
        elif "release_ss_rc" in line:
            out.write("release_ss_rc=0\n")
            if serve.get("still_listening"): out.write("LISTENING 0.0.0.0:18082\n")
            out.flush()
        elif "release_pgrep_llama_rc" in line:
            out.write("release_pgrep_llama_rc=1\nrelease_pgrep_serve_rc=%d\n" % serve.get("pgrep_serve_rc", 1)); out.flush()
        elif "RELEASE_CHECK_DONE" in line:
            out.write("RELEASE_CHECK_DONE\n"); out.flush()
        elif line.strip() == "exit":
            sys.exit(0)
    sys.exit(0)
sys.exit(3)
'''

FAKE_CURL = r'''#!__PY__
import json, os, sys
cfg = json.load(open(os.environ["FAKE_CFG"]))
open(os.environ["FAKE_LOG"], "a").write(json.dumps({"tool": "curl", "argv": sys.argv[1:]}) + "\n")
status = cfg.get("status")
if status is None:
    sys.exit(7)
print(json.dumps(status))
'''

STUB_PY = r'''#!__PY__
import json, os, sys, time
real = os.environ["REAL_PY"]
cfg = json.load(open(os.environ["FAKE_CFG"]))
args = sys.argv[1:]
open(os.environ["FAKE_LOG"], "a").write(json.dumps({"tool": "python", "argv": args}) + "\n")
def out_arg():
    return args[args.index("--out") + 1]
if args[:3] == ["-m", "tools.language_latency", "measure"]:
    json.dump(cfg.get("report", {"verdict": "OK", "rounds": []}), open(out_arg(), "w"))
    sys.exit(cfg.get("measure_rc", 0))
if args[:3] == ["-m", "tools.language_latency", "k-receipt"]:
    if cfg.get("k_receipt_rc", 0) == 0:
        json.dump(cfg["k_receipt"], open(out_arg(), "w"))
    sys.exit(cfg.get("k_receipt_rc", 0))
if args[:4] == ["-m", "tools.eng_loop2.analyze_play", "derive-bc", "--out"]:
    json.dump(cfg["derive_bc"], open(out_arg(), "w")); sys.exit(cfg.get("derive_rc", 0))
if args[:4] == ["-m", "tools.eng_loop2.analyze_play", "score", "--session-dir"]:
    json.dump({"schema": "p1-eng-loop-002-four-numbers/v2", "funnel": {"n_accepted": 0}, "number_one": {"t": 1}}, open(out_arg(), "w"))
    sys.exit(cfg.get("score_rc", 0))
if args[:2] == ["-m", "tools.eng_loop2.deploy_digest"]:
    print(json.dumps({"serve_code_sha256": cfg["digest"]})); sys.exit(0)
if len(args) >= 3 and args[0] == "-I" and args[1] == "-c" and "read_smoke_rows" in args[2]:
    print("SMOKE_OK 32"); sys.exit(0)
if len(args) >= 2 and args[0] == "-c" and "import numpy, cv2, lap" in args[1]:
    print("ultralytics 8.4.104 torch 2.x mps True"); sys.exit(cfg.get("air_env_rc", 0))
if args == ["-I", "-"]:
    data = sys.stdin.read()
    if "det-assoc-v1.models.json" in data:
        print("weights w OK\nfreeze f OK"); sys.exit(0)
if len(args) == 4 and args[:2] == ["-I", "-B"] and args[2].endswith("status-check.py"):
    status = json.load(open(args[3]))
    bad = []
    if not status.get("model_identity"):
        bad.append("model_identity lacks the six llama keys")
    if status.get("serve_code_sha256") != cfg["digest"]:
        bad.append("serve_code_sha256 mismatch")
    if "http_budget" in status:
        bad.append("http_budget present: this is not the budget=None diagnostic server")
    print("state=%s" % status.get("state"))
    print("\n".join("DIAG_FAULT " + b for b in bad) if bad else "DIAG_STATUS_OK"); sys.exit(0)
if args[:3] == ["-m", "controller.language_loop", "run"]:
    os.environ["PYTHONPATH"] = os.environ["REAL_REPO"]
    os.execv(real, [real, os.environ["FAKE_SESSION"]] + args[3:])
env = dict(os.environ, PYTHONPATH=os.environ["REAL_REPO"])
os.execve(real, [real] + args, env)
'''

#: 替身会话：只用生产桥函数写回执/状态/结果；ask → none 结果回 IDLE；stop → TERMINAL(operator_stop)。
#: `cfg["session"]`（C6 失败路径）：`model_loads`；`terminal_after_requests` {n, reason}（第 n 个业务请求受理后即
#: TERMINAL(reason) 退出）；`stop_mode` = late_terminal（回执即写、`terminal_delay_s` 后才 TERMINAL）/ ignore（不回执、
#: 不 TERMINAL，`exit_after_ignore_s` 后退出，模拟 stop 结果未知与会话挂起）。
FAKE_SESSION = r'''
import argparse, json, os, sys, time
from pathlib import Path
from controller import language_bridge as bridge
cfg = json.load(open(os.environ["FAKE_CFG"])).get("session", {})
p = argparse.ArgumentParser(); p.add_argument("--session-id"); p.add_argument("--session-root"); p.add_argument("--runtime")
p.add_argument("--diagnostic", action="store_true"); p.add_argument("--diagnostics-root")
a, _ = p.parse_known_args()
runtime = Path(a.runtime); sdir = Path(a.session_root) / a.session_id; sdir.mkdir(parents=True, exist_ok=True)
(sdir.parent / (a.session_id + ".fake-pid")).write_text(str(os.getpid()))
if a.diagnostic:
    assert a.session_id.startswith("diag-")
    runs = Path(a.diagnostics_root) / a.session_id / "seg-0"
else:
    runs = runtime / "runs" / (a.session_id + "-resident-0")
runs.mkdir(parents=True, exist_ok=True)
(runs / "model_cache.json").write_text(json.dumps({"model_loads": cfg.get("model_loads", 1), "model_requests": 0}))
seq = [0]; qn = [0]; business = [0]; exit_at = [None]
def journal(kind, **f):
    with (sdir / "language-session.jsonl").open("a") as h:
        h.write(json.dumps({"at_unix_s": time.time(), "session_id": a.session_id, "kind": kind, "epoch": 1, **f}) + "\n")
def state(name, reason=None, receipt=None):
    seq[0] += 1
    bridge.write_tracker_state(runtime, bridge.tracker_state_payload(session_id=a.session_id, state=name, sequence=seq[0], epoch=1,
                               publishing=False, reason=reason, last_request=receipt))
    journal("state", state=name, reason=reason)
state("IDLE")
seen = set()
deadline = time.time() + 60
while time.time() < deadline:
    if exit_at[0] is not None and time.time() >= exit_at[0]:
        sys.exit(0)
    env = bridge.read_request(runtime)
    if env is None or env.request_id in seen:
        time.sleep(0.02); continue
    seen.add(env.request_id)
    if env.action == "stop" and cfg.get("stop_mode") == "ignore":
        exit_at[0] = time.time() + cfg.get("exit_after_ignore_s", 2.0); continue
    receipt = {"request_id": env.request_id, "action": env.action, "outcome": "APPLIED", "at_sequence": seq[0] + 1}
    journal("receipt", receipt=receipt)
    if env.action == "stop":
        if cfg.get("stop_mode") == "late_terminal":
            time.sleep(cfg.get("terminal_delay_s", 2.0))
        state("TERMINAL", reason="operator_stop", receipt=receipt); sys.exit(0)
    business[0] += 1
    after = cfg.get("terminal_after_requests")
    if after and business[0] >= after["n"]:
        state("TERMINAL", reason=after["reason"], receipt=receipt); sys.exit(0)
    state("QUERYING", receipt=receipt)
    qn[0] += 1
    record = {"query_id": "%s-q%d" % (a.session_id, qn[0]), "result_id": "%s-res%d" % (a.session_id, qn[0]),
              "request_id": env.request_id, "purpose": "designate", "status": "none", "epoch": 1}
    with (sdir / "results.jsonl").open("a") as h:
        h.write(json.dumps(record) + "\n")
    time.sleep(0.05)
    state("IDLE", receipt=receipt)
sys.exit(1)
'''


def write_exec(path: Path, text: str) -> Path:
    path.write_text(text.replace("__PY__", REAL_PY), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True,
                          env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
                                   GIT_COMMITTER_EMAIL="t@t"))
    return done.stdout.strip()


CHECK_DOCS_STUB = '''import json, sys
from pathlib import Path
def open_consuming_gate_blocks(reviews):
    p = Path(reviews) / "BLOCKS.json"
    return json.loads(p.read_text()) if p.exists() else {}
def ledger_released_findings(path):
    return {}
if __name__ == "__main__":
    sys.exit(0)
'''

#: 精简的 Mac mini R02 原流（诊断页附录 1 `resolve` 的同一解析对象；路径/sha 与假板一致）。
PRECHECK = """# precheck

## Mac mini只读补核原始读数与逐维度用量
hostname=jetson-orin
=== R02-Q4 weights
/home/jetson/eng-jet/q4/model-Q4_K_M.gguf|regular file|x|y|100
""" + "a" * 64 + """  /home/jetson/eng-jet/q4/model-Q4_K_M.gguf
sha_match=yes
=== R02-MMPROJ mmproj
/home/jetson/eng-jet/mmproj-c2.gguf|regular file|x|y|50
""" + "b" * 64 + """  /home/jetson/eng-jet/mmproj-c2.gguf
sha_match=yes
=== R02-SERVER server
/home/jetson/eng-jet/batch/build/bin/llama-server|regular file|x|y|777
""" + "c" * 64 + """  /home/jetson/eng-jet/batch/build/bin/llama-server
sha_match=yes
=== END
"""

WORKFLOW = """# workflow
PLAY_GOVERNING 的唯一权威定义：
`controller/` `Assets/` `tools/` `tests/` `config/` `ProjectSettings/` `Packages/packages-lock.json`
"""


class RepoFixture:
    """bare origin + 执行检出（分离于 passed）+ 文档检出（位于 REL）；三份操作单取真实原文。"""

    def __init__(self, root: Path, gitignore: str = "outputs/\nruntime/\n"):
        self.root = root
        self.origin = root / "origin.git"
        self.repo = root / "exec"
        self.docwt = root / "docwt"
        self.bin = root / "bin"
        self.bin.mkdir()
        self.cfg_path = root / "fake-cfg.json"
        self.log_path = root / "fake-log.jsonl"
        self.cfg: dict[str, Any] = {"board_ts": BOARD_TS, "digest": "d" * 64}
        self.save()
        git(root, "init", "--bare", "-b", "main", str(self.origin))
        git(root, "clone", "-q", str(self.origin), str(self.repo))
        r = self.repo
        git(r, "symbolic-ref", "HEAD", "refs/heads/main")
        for sheet in ops.OPS_SHEETS:
            (r / sheet).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / sheet, r / sheet)
        (r / "docs/collaboration-workflow.md").write_text(WORKFLOW, encoding="utf-8")
        (r / "docs/authorizations.md").write_text("用户答 Mac mini 补核核清四题\nSLOT:FACT:1\n", encoding="utf-8")
        (r / "docs/implementation-status.md").write_text("# s\n", encoding="utf-8")
        (r / "docs/unity-test-log.md").write_text("# log\n", encoding="utf-8")
        (r / "docs/proposals").mkdir(parents=True)
        (r / ops.PROPOSAL).write_text("# proposal\n", encoding="utf-8")
        (r / "docs/reviews").mkdir(parents=True)
        (r / "docs/reviews/README.md").write_text("x\n", encoding="utf-8")
        (r / "tools").mkdir()
        (r / "tools/check_docs.py").write_text(CHECK_DOCS_STUB, encoding="utf-8")
        (r / "tools/check_ledger.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
        (r / "docs/evidence/P1-ENG-LOOP-002-precheck.md").write_text(PRECHECK, encoding="utf-8")
        (r / "config").mkdir()
        (r / "config/deploy-a.txt").write_text("alpha\n", encoding="utf-8")
        (r / "config/p1-eng-loop-002-board-deploy.json").write_text(json.dumps({"paths": ["config/deploy-a.txt", "tools/check_ledger.py"]}), encoding="utf-8")
        shutil.copyfile(REPO / "config/scenario.untethered.json", r / "config/scenario.untethered.json")
        (r / ".gitignore").write_text(gitignore, encoding="utf-8")
        (r / "runtime").mkdir()
        self.write_sources()
        git(r, "add", "-A")
        git(r, "commit", "-m", "A")
        self.passed = git(r, "rev-parse", "HEAD")
        (r / ops.REVIEW_FILE).write_text(f"- `round_candidate: {self.passed}`（C）\n\npassed_candidate: {self.passed}\n", encoding="utf-8")
        git(r, "add", "-A")
        git(r, "commit", "-m", "B review")
        git(r, "push", "origin", "main")
        self.rel = git(r, "rev-parse", "HEAD")
        git(r, "worktree", "add", "--detach", str(self.docwt), self.rel)
        git(r, "checkout", "--detach", self.passed)
        self.out = r / "outputs/eng-loop2/P1-ENG-LOOP-002"
        self.ssh = write_exec(self.bin / "ssh", FAKE_SSH)
        write_exec(self.bin / "curl", FAKE_CURL)
        self.py = write_exec(self.bin / "python-stub", STUB_PY)
        self.session = root / "fake_session.py"
        self.session.write_text(FAKE_SESSION, encoding="utf-8")

    def write_sources(self) -> None:
        r = self.repo
        j = r / "outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic"
        step = j / "steps/011"
        step.mkdir(parents=True)
        for name in ("budget.jsonl", "checkpoint.json"):
            (j / name).write_text("{}\n", encoding="utf-8")
        weights, mmproj, server = "/home/jetson/eng-jet/q4/model-Q4_K_M.gguf", "/home/jetson/eng-jet/mmproj-c2.gguf", "/home/jetson/eng-jet/batch/build/bin/llama-server"
        (j / "state.json").write_text(json.dumps({"board": {"step": str(step.relative_to(r))},
                                                  "q4": {"basename": "model-Q4_K_M.gguf", "bytes": 100, "sha256": "a" * 64}}), encoding="utf-8")
        (step / "receipt.json").write_text(json.dumps({
            "transfer": {"admitted": f"{weights}|x|100"}, "server": {"argv": [server, "--model", weights, "--mmproj", mmproj]},
            "board_paths": {"mmproj": mmproj, "server": server}, "server_sha256_now": "c" * 64}), encoding="utf-8")
        (r / "docs/evidence").mkdir(parents=True, exist_ok=True)
        (r / "docs/evidence/P1-ENG-JET-001-stageb-transfer.json").write_text(json.dumps({"objects": [
            {"cls": "G", "basename": "mmproj-c2.gguf", "board_final": mmproj, "expected_sha256": "b" * 64, "expected_bytes": 50}]}), encoding="utf-8")
        (r / "docs/evidence/P1-ENG-JET-001-stageb-build-rerun.json").write_text(json.dumps({
            "board_batch_dir": {"path": "/home/jetson/eng-jet/batch/"}, "products": {"llama_server_stat_raw": "f|r|777"}}), encoding="utf-8")
        self.cfg["paths"] = {"WEIGHTS": weights, "MMPROJ": mmproj, "LLAMA_BIN": server}
        self.cfg["sha"] = {"WEIGHTS": "a" * 64, "MMPROJ": "b" * 64, "LLAMA_BIN": "c" * 64}
        self.save()

    def save(self) -> None:
        self.cfg_path.write_text(json.dumps(self.cfg), encoding="utf-8")

    def env(self) -> dict[str, str]:
        return {"FAKE_CFG": str(self.cfg_path), "FAKE_LOG": str(self.log_path), "REAL_PY": REAL_PY,
                "REAL_REPO": str(REPO), "FAKE_SESSION": str(self.session),
                "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}"}

    def calls(self, tool: str) -> list[list[str]]:
        if not self.log_path.exists():
            return []
        return [r.get("argv") or [r.get("line")] for r in map(json.loads, self.log_path.read_text().splitlines()) if r["tool"] == tool]

    def commit_docs(self, path: str, text: str) -> None:
        """在文档检出追加规则许可文档并推送（REL 前进），执行检出不动。"""
        target = self.docwt / path
        target.write_text(target.read_text(encoding="utf-8") + text, encoding="utf-8")
        git(self.docwt, "add", path)
        git(self.docwt, "commit", "-m", f"docs {path}")
        git(self.docwt, "push", "origin", "HEAD:main")
        self.rel = git(self.docwt, "rev-parse", "HEAD")

    def main(self, *argv: str) -> tuple[int, str]:
        buffer = io.StringIO()
        base = ["--repo", str(self.repo), "--out", str(self.out), "--python", str(self.py), "--ssh", str(self.ssh),
                "--docwt", str(self.docwt)]
        with patched_env(self.env()), redirect_stdout(buffer):
            rc = ops.main([*base, *argv])
        return rc, buffer.getvalue()


class patched_env:
    def __init__(self, values: dict[str, str]):
        self.values, self.saved = values, {}

    def __enter__(self) -> None:
        for key, value in self.values.items():
            self.saved[key] = os.environ.get(key)
            os.environ[key] = value

    def __exit__(self, *exc: Any) -> None:
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class RepoTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fx = RepoFixture(Path(self.tmp.name))

    def context(self, stage: str = "t") -> ops.Context:
        ns = ops.build_parser().parse_args(["--repo", str(self.fx.repo), "--out", str(self.fx.out), "--python", str(self.fx.py),
                                            "--ssh", str(self.fx.ssh), "--docwt", str(self.fx.docwt), "gate"])
        return ops.make_context(ns, stage)

    def gate(self) -> ops.GateResult:
        with patched_env(self.fx.env()):
            return ops.release_gate(self.context())

    def register(self) -> Path:
        """1.6：放行原流登记进 Unity 日志（建议机读行）并推送；返回登记的原流文件。"""
        result = self.gate()
        self.assertTrue(result.ok, result.stops)
        self.fx.commit_docs("docs/unity-test-log.md", f"\n{ops.UNITY_LOG_SHA_LINE}{ops.sha256_file(result.raw_path)}\n")
        return result.raw_path


# --- 第 1 节放行核对 ---------------------------------------------------------------


class ReleaseGateTests(RepoTestBase):
    def test_all_mechanical_checks_pass(self) -> None:
        result = self.gate()
        self.assertTrue(result.ok, result.stops)
        text = result.raw_path.read_text(encoding="utf-8")
        for marker in ("RELEASE_REF_OK", "PG_DIFF_EMPTY_OK", "CONSUMING_GATE_OK", "HEAD_EQ_PASSED_OK", "NO_UNITY_RECOVERY", "RELEASE_GATE_OK"):
            self.assertIn(marker, text)
        self.assertEqual((result.rel, result.passed), (self.fx.rel, self.fx.passed))

    def test_latest_round_without_pass_line_stops(self) -> None:
        self.fx.commit_docs(ops.REVIEW_FILE, f"\n- `round_candidate: {self.fx.passed}`（R2）\n")
        result = self.gate()
        self.assertFalse(result.ok)
        self.assertTrue(any(s.startswith("latest_round_not_passed") for s in result.stops))

    def test_play_governing_change_after_pass_stops(self) -> None:
        self.fx.commit_docs("tools/check_ledger.py", "# changed\n")
        self.assertIn("play_governing_changed_after_pass", self.gate().stops)

    def test_ops_sheet_change_after_pass_stops(self) -> None:
        self.fx.commit_docs(ops.DIAG_OPS_DOC, "\nchange\n")
        self.assertIn("play_governing_changed_after_pass", self.gate().stops)

    def test_unreleased_consuming_block_stops(self) -> None:
        (self.fx.docwt / "docs/reviews/BLOCKS.json").write_text(json.dumps({"X.md": ["F1"]}), encoding="utf-8")
        git(self.fx.docwt, "add", "-A")
        git(self.fx.docwt, "commit", "-m", "block")
        git(self.fx.docwt, "push", "origin", "HEAD:main")
        self.assertIn("consuming_gate_blocked", self.gate().stops)

    def test_head_dirty_tree_recovery_and_sheet_drift_stop(self) -> None:
        (self.fx.repo / "Assets/_Recovery").mkdir(parents=True)
        (self.fx.repo / ops.PLAY_OPS_DOC).write_text("edited\n", encoding="utf-8")
        stops = self.gate().stops
        self.assertIn("worktree_not_clean", stops)
        self.assertIn("unity_recovery_present", stops)
        self.assertIn(f"ops_sheet_not_passed_version {ops.PLAY_OPS_DOC}", stops)

    def test_head_not_passed_and_docwt_not_at_rel(self) -> None:
        git(self.fx.repo, "checkout", "--detach", self.fx.rel)
        git(self.fx.docwt, "checkout", "--detach", self.fx.passed)
        stops = self.gate().stops
        self.assertTrue(any(s.startswith("head_not_passed_candidate") for s in stops))
        self.assertIn("docwt_not_at_rel", stops)

    def test_ledger_entries_required(self) -> None:
        target = self.fx.docwt / "docs/authorizations.md"
        target.write_text("nothing\n", encoding="utf-8")
        git(self.fx.docwt, "commit", "-am", "drop")
        git(self.fx.docwt, "push", "origin", "HEAD:main")
        self.assertIn("ledger_entry_missing SLOT:FACT:1", self.gate().stops)

    def test_registration_and_g4_machine_lines_fail_closed(self) -> None:
        with patched_env(self.fx.env()):
            ctx = self.context()
            with self.assertRaises(ops.Stop) as caught:
                ops.require_gate(ctx, None, need_registration=True)
            self.assertIn("registered_release_missing", caught.exception.detail)
            raw = ops.release_gate(ctx).raw_path
            with self.assertRaises(ops.Stop) as caught:
                ops.require_gate(ctx, raw, need_registration=True)
            self.assertIn("unity_log_registration_missing", caught.exception.detail)
        raw = self.register()
        with patched_env(self.fx.env()):
            ctx = self.context()
            gate = ops.require_gate(ctx, raw, need_registration=True)
            (self.fx.out / "prep").mkdir(parents=True, exist_ok=True)
            (self.fx.out / "prep/prep.stdout").write_text("final=OK\n", encoding="utf-8")
            with self.assertRaises(ops.Stop) as caught:
                ops.require_g4(ctx, gate)
            self.assertIn("g4_release_missing", caught.exception.detail)
        self.fx.commit_docs(ops.PROPOSAL, f"\n- `g4_release: {ops.sha256_file(self.fx.out / 'prep/prep.stdout')}`\n")
        with patched_env(self.fx.env()):
            ctx = self.context()
            gate = ops.require_gate(ctx, raw, need_registration=True)
            self.assertEqual(ops.require_g4(ctx, gate), ops.sha256_file(self.fx.out / "prep/prep.stdout"))


class FormalOutputIgnoreTests(RepoTestBase):
    """IR-OPS-8 / AC-10 修订 5：仓库 `.gitignore` 精确忽略正式输出根 `$OUT`，整树干净核仍报无关/已跟踪改动。

    替身执行检出使用本仓库真实 `.gitignore` 原文（不是夹具缺省的泛化 `outputs/`）。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fx = RepoFixture(Path(self.tmp.name), gitignore=(REPO / ".gitignore").read_text(encoding="utf-8"))

    def status(self) -> str:
        return git(self.fx.repo, "status", "--porcelain", "--untracked-files=normal")

    def ignored(self, rel: str) -> bool:
        done = subprocess.run(["git", "check-ignore", "-q", "--", rel], cwd=self.fx.repo)
        self.assertIn(done.returncode, (0, 1))
        return done.returncode == 0

    def test_repo_gitignore_adds_only_the_exact_formal_output_line(self) -> None:
        lines = [line.strip() for line in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(lines.count("/outputs/eng-loop2/"), 1)
        for broad in ("/outputs/", "outputs/", "/outputs/*", "outputs/*", "/outputs", "outputs"):
            self.assertNotIn(broad, lines)
        self.assertTrue(ops.DEFAULT_OUT.startswith("outputs/eng-loop2/"))

    def test_formal_output_ignored_but_stray_and_tracked_changes_stay_dirty(self) -> None:
        produced = self.fx.repo / ops.DEFAULT_OUT / "release" / "raw.txt"
        produced.parent.mkdir(parents=True)
        produced.write_text("raw\n", encoding="utf-8")
        self.assertTrue(self.ignored(f"{ops.DEFAULT_OUT}/release/raw.txt"))
        self.assertEqual(self.status(), "")
        for stray in ("outputs/eng-loop2x/y.txt", "outputs/other/y.txt", "tools/eng_loop2/stray.py"):
            path = self.fx.repo / stray
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x\n", encoding="utf-8")
            self.assertFalse(self.ignored(stray), stray)
            self.assertNotEqual(self.status(), "", stray)
            path.unlink()
        self.assertEqual(self.status(), "")
        (self.fx.repo / "config/deploy-a.txt").write_text("beta\n", encoding="utf-8")
        self.assertEqual(self.status(), "M config/deploy-a.txt")  # git() 去首尾空白；原行为「 M config/deploy-a.txt」

    def test_release_gate_is_not_blocked_by_its_own_formal_output(self) -> None:
        first = self.gate()
        self.assertTrue(first.ok, first.stops)
        self.assertTrue(str(first.raw_path).startswith(str(self.fx.out / "release")))
        second = self.gate()
        self.assertTrue(second.ok, second.stops)
        (self.fx.repo / "tools/stray.py").write_text("x\n", encoding="utf-8")
        self.assertIn("worktree_not_clean", self.gate().stops)


# --- 第 0.3 节来源 -------------------------------------------------------------------


class SourceTests(RepoTestBase):
    def test_resolves_existing_air_originals(self) -> None:
        with patched_env(self.fx.env()):
            values = ops.source_check(self.context())
        self.assertEqual(values["WEIGHTS"], self.fx.cfg["paths"]["WEIGHTS"])
        self.assertEqual(values["EXP_LLAMA_BIN_BYTES"], "777")
        self.assertEqual(len((self.fx.out / "prep/source.vars").read_text().splitlines()), 9)

    def test_missing_original_stops_without_copying(self) -> None:
        (self.fx.repo / "outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/checkpoint.json").unlink()
        with patched_env(self.fx.env()), self.assertRaises(ops.Stop) as caught:
            ops.source_check(self.context())
        self.assertEqual(caught.exception.code, "S-PRECHECK")
        self.assertIn("source_resolve rc=3", caught.exception.detail)

    def test_source_vars_checker_matches_src_check(self) -> None:
        good = "\n".join(f"{n}=v{i}" for i, n in enumerate(ops.SRC_NAMES)) + "\n"
        self.assertEqual(len(ops.check_source_vars(good.encode())), 9)
        for bad in (good.replace("WEIGHTS=v0", "WEIGHTS='v 0'x"), good + "WEIGHTS=v9\n", good.replace("MMPROJ=v3\n", ""),
                    good.replace("WEIGHTS=v0", "OTHER=v0"), "", "A" * 9000):
            with self.assertRaises(ops.Stop):
                ops.check_source_vars(bad.encode())


# --- 第 0.5 节 SSH 单元 ----------------------------------------------------------------


class SshUnitTests(RepoTestBase):
    def test_check_before_each_channel_closed_set_and_order(self) -> None:
        with patched_env(self.fx.env()):
            ctx = self.context()
            unit = ops.SshUnit(ctx, 3)
            unit.open()
            with self.assertRaises(ops.Stop):
                unit.chan("logs-3", "true")  # 顺序：serve 在前
            with self.assertRaises(ops.Stop):
                unit.chan("prep-read", "true")  # 闭集外
            unit.close()
        ssh = self.fx.calls("ssh")
        self.assertEqual(sum(1 for a in ssh if "-fN" in a), 1)
        fallback = [a for a in ssh if "ControlMaster=no" in a]
        self.assertEqual(fallback, [])
        self.assertEqual(ctx.ledger.used("ssh_units"), 1)

    def test_socket_lost_before_channel_is_s_ssh_without_new_auth(self) -> None:
        self.fx.cfg["check_fail"] = True
        self.fx.save()
        with patched_env(self.fx.env()):
            unit = ops.SshUnit(self.context(), 1)
            unit.open()
            with self.assertRaises(ops.Stop) as caught:
                unit.chan("prep-read", "timeout -k 5 900 bash -s")
            unit.close()
        self.assertIn("S-SSH", caught.exception.detail)
        ssh = self.fx.calls("ssh")
        self.assertEqual(sum(1 for a in ssh if "-fN" in a), 1)
        self.assertFalse(any("ControlMaster=no" in a for a in ssh))

    def test_master_failure_counted_once_no_retry(self) -> None:
        self.fx.cfg["master_rc"] = 255
        self.fx.save()
        with patched_env(self.fx.env()):
            ctx = self.context()
            unit = ops.SshUnit(ctx, 1)
            with self.assertRaises(ops.Stop) as caught:
                unit.open()
            unit.close()
        self.assertIn("ssh_master_failed", caught.exception.detail)
        self.assertEqual(ctx.ledger.used("ssh_units"), 1)
        self.assertEqual(sum(1 for a in self.fx.calls("ssh") if "-fN" in a), 1)

    def test_channel_uses_fail_closed_fallback_options(self) -> None:
        with patched_env(self.fx.env()):
            unit = ops.SshUnit(self.context(), 1)
            argv = unit.channel_argv(["-T"], "true")
        for option in ("HostName=127.0.0.1", "Port=1", "ProxyCommand=none", "ProxyJump=none", "BatchMode=yes", "ControlMaster=no"):
            self.assertIn(option, argv)

    def test_ssh_unit_budget_exhausted_is_envelope(self) -> None:
        with patched_env(self.fx.env()):
            ctx = self.context()
            ctx.ledger.take("ssh_units", 3)
            with self.assertRaises(ops.Stop) as caught:
                ops.SshUnit(ctx, 1).open()
        self.assertEqual(caught.exception.code, "S-ENVELOPE")
        self.assertEqual(self.fx.calls("ssh"), [])


# --- 第 4 节前台服务 / 第 5 节收据 ------------------------------------------------------------


class ServeTests(RepoTestBase):
    def serve(self, **serve_cfg: Any) -> tuple[ops.ServeSession, ops.Context]:
        self.fx.cfg["serve"] = serve_cfg
        self.fx.save()
        (self.fx.out / "ops-ledger.json").unlink(missing_ok=True)  # 每个替身服务独立计账
        ctx = self.context()
        ctx.board_ts = BOARD_TS
        unit = ops.SshUnit(ctx, 3)
        unit.open()
        values = {"WEIGHTS": "/w", "MMPROJ": "/m", "LLAMA_BIN": "/l"}
        self.addCleanup(unit.close)
        return ops.ServeSession(ctx, unit, 3, values), ctx

    def test_listen_interrupt_and_release_in_same_session(self) -> None:
        with patched_env(self.fx.env()):
            serve, ctx = self.serve()
            serve.start()
            report = serve.stop_and_release()
        self.assertTrue(report["released"], report)
        self.assertEqual(report["serve_rc"], 0)
        typed = [c[0] for c in self.fx.calls("serve-typed")]
        self.assertTrue(any("--non-inference-reserve \"$R_N\"" in t for t in typed))
        self.assertIn("N=3", typed)
        self.assertEqual(ctx.ledger.used("serve_starts"), 1)

    def test_not_released_when_port_still_listening(self) -> None:
        with patched_env(self.fx.env()):
            serve, _ = self.serve(still_listening=True)
            serve.start()
            report = serve.stop_and_release()
        self.assertFalse(report["released"])

    def test_early_exit_codes_map_to_original_stops(self) -> None:
        for rc, code in ((3, "S-IDENTITY"), (4, "S-BACKEND"), (5, "S-BACKEND"), (6, "S-ENVELOPE")):
            with self.subTest(rc=rc), patched_env(self.fx.env()):
                serve, _ = self.serve(early_rc=rc)
                with self.assertRaises(ops.Stop) as caught:
                    serve.start()
                self.assertEqual(caught.exception.code, code)
                serve.finish_channel()
                serve.unit.close()

    def test_startup_stop_line_is_precheck(self) -> None:
        with patched_env(self.fx.env()):
            serve, _ = self.serve(startup_stop="STOP S-PRECHECK port_occupied 0.0.0.0:18082")
            with self.assertRaises(ops.Stop) as caught:
                serve.start()
        self.assertEqual(caught.exception.code, "S-PRECHECK")

    def test_unexpected_listen_endpoint_is_identity(self) -> None:
        with patched_env(self.fx.env()):
            serve, _ = self.serve(listen_host="0.0.0.0")
            with self.assertRaises(ops.Stop) as caught:
                serve.start()
            serve.stop_and_release()
        self.assertEqual(caught.exception.code, "S-IDENTITY")

    def test_reserve_is_derived_from_unit_only(self) -> None:
        with patched_env(self.fx.env()):
            serve, _ = self.serve()
            with self.assertRaises(ops.Stop):
                ops.ServeSession(serve.ctx, serve.unit, 4, {})
        self.assertEqual(ops.RESERVE_BY_UNIT, {2: 25, 3: 11})


class ReceiptTests(RepoTestBase):
    def run_receipt(self, **cfg: Any) -> tuple[Any, ops.Context]:
        self.fx.cfg.update(cfg)
        self.fx.cfg.setdefault("k_receipt", {"ok": 1})
        self.fx.save()
        with patched_env(self.fx.env()):
            ctx = self.context()
            ctx.board_ts = BOARD_TS
            try:
                return ops.run_measure_and_receipt(ctx), ctx
            except ops.Stop as stop:
                return stop, ctx

    def k_receipt_calls(self) -> int:
        return sum(1 for a in self.fx.calls("python") if a[:3] == ["-m", "tools.language_latency", "k-receipt"])

    def test_measure_zero_then_k_receipt_zero(self) -> None:
        result, _ = self.run_receipt()
        self.assertEqual(result, {"measure_rc": 0, "k_receipt_rc": 0})

    def test_measure_failure_never_runs_k_receipt(self) -> None:
        stop, _ = self.run_receipt(measure_rc=7, report={"verdict": "FAIL", "rounds": [{"failures": [{"detail": "S_ENVELOPE x"}]}]})
        self.assertEqual(stop.code, "S-ENVELOPE")
        self.assertEqual(self.k_receipt_calls(), 0)
        stop, _ = self.run_receipt(measure_rc=7, report={"verdict": "FAIL", "rounds": [{"failures": [{"detail": "timeout"}]}]})
        self.assertEqual(stop.code, "S-BACKEND")
        stop, _ = self.run_receipt(measure_rc=1)
        self.assertEqual(stop.code, "S-BACKEND")
        self.assertEqual(self.k_receipt_calls(), 0)

    def test_k_receipt_6_or_8_is_s_receipt(self) -> None:
        for rc in (6, 8):
            stop, _ = self.run_receipt(measure_rc=0, k_receipt_rc=rc)
            self.assertEqual(stop.code, "S-RECEIPT")


class IdentityTests(RepoTestBase):
    def status(self, **override: Any) -> dict[str, Any]:
        document = {"model_identity": {k: "x" for k in bridge.LLAMA_IDENTITY_KEYS}, "serve_code_sha256": "d" * 64,
                    "machine": "jetson", "http_budget": {"batch": 2}}
        document.update(override)
        return document

    def check(self, status: Any) -> Any:
        self.fx.cfg["status"] = status
        self.fx.save()
        with patched_env(self.fx.env()):
            ctx = self.context()
            ctx.board_ts = BOARD_TS
            try:
                return ops.identity_check(ctx, 3, "d" * 64)
            except ops.Stop as stop:
                return stop

    def test_identity_ok_and_failures(self) -> None:
        self.assertIsInstance(self.check(self.status()), dict)
        self.assertEqual(self.check(self.status(http_budget={"batch": 1})).code, "S-IDENTITY")
        self.assertEqual(self.check(self.status(serve_code_sha256="e" * 64)).code, "S-IDENTITY")
        self.assertEqual(self.check(self.status(model_identity={"quantization": "Q4_K_M"})).code, "S-IDENTITY")
        self.assertEqual(self.check(None).code, "S-BACKEND")
        self.assertEqual(len(self.fx.calls("curl")), 5)  # 每次核对恰一次 /status，不轮询


# --- 计划冻结与在线调度 ---------------------------------------------------------------------


DERIVE = {"status": "OK", "B": {"scene_object_name": "Vehicle_SUV_color01 (1)", "description": "the suv", "xz_distance_m": 6.7},
          "C": {"scene_object_name": "Vehicle_Taxi (2)", "description": "the taxi", "xz_distance_m": 9.3}}


class PlanTests(RepoTestBase):
    def test_freeze_checks_sheet_and_writes_no_geometry(self) -> None:
        self.fx.cfg["derive_bc"] = DERIVE
        self.fx.save()
        rc, out = self.fx.main("plan", "--p2-object", "red_car")
        self.assertEqual(rc, 0, out)
        plan, sha = ops.load_plan(self.fx.out / "plan/ops-plan.json")
        self.assertEqual([s["action"] for s in plan["playbooks"]["P1"]], ["ask", "ask", "ask", "ask", "stop"])
        self.assertEqual([s["instruction"] for s in plan["playbooks"]["P1"][:4]], ["the suv", "the taxi", "the red car", "the suv"])
        self.assertEqual([s["delay_s"] for s in plan["playbooks"]["P3"][:3]], [0.0, 2.0, 4.0])
        self.assertEqual([s["release_after"] for s in plan["playbooks"]["P3"][:3]], [True, True, False])
        self.assertEqual(plan["playbooks"]["P1"][2]["follow_s"], 20.0)
        self.assertEqual(plan["playbooks"]["P2"][0]["intent"], "red_car")
        text = (self.fx.out / "plan/ops-plan.json").read_text()
        for geometry in ("xz_distance", "off_nadir", "camera_position", "projection"):
            self.assertNotIn(geometry, text)
        rc, out = self.fx.main("plan", "--p2-object", "B")
        self.assertEqual(rc, 3)
        self.assertIn("ops_plan_already_frozen", out)

    def test_derived_bc_must_equal_ops_sheet(self) -> None:
        self.fx.cfg["derive_bc"] = dict(DERIVE, C={"scene_object_name": "Vehicle_Car_color01", "description": "the car"})
        self.fx.save()
        rc, out = self.fx.main("plan", "--p2-object", "red_car")
        self.assertEqual(rc, 3)
        self.assertIn("bc_differs_from_ops_sheet", out)
        self.fx.cfg["derive_bc"] = {"status": "BC_DERIVATION_LT_2"}
        self.fx.save()
        rc, out = self.fx.main("plan", "--p2-object", "red_car")
        self.assertIn("derive_bc status", out)

    def test_load_plan_rejects_extra_keys(self) -> None:
        plan = ops.build_plan({"intent": "B", "text": "the suv"}, {"intent": "C", "text": "the taxi"}, "C")
        plan["playbooks"]["P1"][0]["xz_distance_m"] = 1.0
        path = Path(self.tmp.name) / "p.json"
        path.write_text(json.dumps(plan))
        with self.assertRaises(ops.Stop):
            ops.load_plan(path)


class SchedulerBase(unittest.TestCase):
    """真实 Monitor（生产写函数写桥文件）+ 共享 Submitter（记录型 CLI 替身）+ 假时钟。"""

    def setUp(self) -> None:
        from tests.test_eng_loop2_operator_web import Clock, FakeCli, Fixture

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.clock = Clock(1_800_000_000.0)
        self.fx = Fixture(Path(self.tmp.name), self.clock)
        self.cli = FakeCli()
        self.log = web.OpsLog(Path(self.tmp.name) / "ops.jsonl", clock=self.clock)
        builder = web.CliRunner("python3", Path(self.tmp.name), self.fx.runtime)
        self.submitter = web.Submitter(self.cli, builder, self.log)
        self.monitor = web.Monitor(self.fx.runtime, "loop2-p1", self.fx.session_dir, self.fx.receipt, clock=self.clock)
        plan = ops.build_plan({"intent": "Vehicle_SUV_color01 (1)", "text": "the suv"}, {"intent": "Vehicle_Taxi (2)", "text": "the taxi"}, "red_car")
        self.plan = plan

    def scheduler(self, playbook: str = "P1") -> ops.PlanScheduler:
        return ops.PlanScheduler(self.plan["playbooks"][playbook], playbook=playbook, session_id="loop2-p1", plan_sha256="f" * 64,
                                 monitor=self.monitor, submitter=self.submitter, log=self.log, clock=self.clock)

    def send(self, scheduler: ops.PlanScheduler) -> dict[str, Any]:
        step = scheduler.current_send_step(scheduler.snapshot()["current"]["step_id"])
        key = json.dumps({"button": "send_or_skip", "step_id": step["step_id"], "attempt": step["attempt"]}, sort_keys=True)
        reply = self.submitter.submit(source="web", action=step["action"], session_id="loop2-p1", binding={}, binding_key=key,
                                      instruction=step["instruction"], intent=step["intent"], delay_s=step["delay_s"])
        scheduler.record_send(step["step_id"], reply)
        return reply

    def tick(self, scheduler: ops.PlanScheduler) -> None:
        self.monitor.poll()
        scheduler.tick()

    def status(self, scheduler: ops.PlanScheduler) -> list[str]:
        return [s["status"] for s in scheduler.snapshot()["steps"]]


class SchedulerTests(SchedulerBase):
    def test_send_present_confirm_observe_then_next_step(self) -> None:
        s = self.scheduler()
        self.fx.publish_frames(3)
        self.fx.state("IDLE")
        self.tick(s)
        self.assertEqual(s.snapshot()["current"]["phase"], "await_send")
        reply = self.send(s)
        rid = reply["request_id"]
        self.assertEqual(s.snapshot()["current"]["phase"], "await_result")
        from tests.test_eng_loop2_operator_web import png_bytes

        frame = self.fx.publish_frames(1)
        self.fx.result(frame_id=frame, query_unix_s=self.clock.now - 0.5, n=1, request_id=rid, preview=png_bytes(2))
        self.fx.state("AWAITING_CONFIRMATION")
        self.tick(s)
        self.assertEqual(s.snapshot()["decision_step"], "P1-1")
        self.assertEqual(s.decision_step(rid), "P1-1")
        decision = self.submitter.submit(source="web", action="confirm", session_id="loop2-p1", binding={}, binding_key="d1",
                                         token="loop2-p1-res1", index=0)
        s.record_decision("P1-1", "confirm", decision)
        self.fx.journal(kind="receipt", epoch=1, receipt={"request_id": decision["request_id"], "action": "confirm", "outcome": "APPLIED", "at_sequence": 5})
        self.fx.journal(kind="state", state="TRACKING", epoch=1)
        self.fx.state("TRACKING", track_id="t7")
        self.tick(s)
        self.assertEqual(s.snapshot()["current"]["phase"], "observing")
        self.clock.now += 14.0
        self.tick(s)
        self.assertEqual(s.snapshot()["current"]["step_id"], "P1-1")
        self.clock.now += 1.1
        self.tick(s)
        self.assertEqual(self.status(s)[:2], ["DONE", "AWAIT_SEND"])
        step = s.steps[0]
        self.assertEqual((step["anchor_source"], step["tracking_established"], step["track_id"], step["tracking_at_source"]),
                         ("journal_receipt", True, "t7", "journal_state"))
        self.assertTrue(step["follow_verified"])
        self.assertEqual([c[3] for c in self.cli.calls], ["ask", "confirm"])

    def test_none_result_closes_step_without_extra_ask_or_observation(self) -> None:
        s = self.scheduler()
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        rid = self.send(s)["request_id"]
        with (self.fx.session_dir / "results.jsonl").open("a") as handle:
            handle.write(json.dumps({"purpose": "designate", "request_id": rid, "status": "none", "result_id": "r1"}) + "\n")
        self.fx.state("IDLE")
        self.tick(s)
        self.assertEqual(self.status(s)[:2], ["NO_CANDIDATE", "AWAIT_SEND"])
        for _ in range(5):
            self.clock.now += 5
            self.tick(s)
        self.assertEqual(len(self.cli.calls), 1)  # 不追加 ask，不自动发下一步

    def test_refused_receipt_is_recorded_and_advances(self) -> None:
        s = self.scheduler()
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        self.cli.outcomes.append({"outcome": "REQUEST_INVALID"})
        self.send(s)
        self.assertEqual(self.status(s)[:2], ["REFUSED", "AWAIT_SEND"])

    def test_no_decision_by_deadline_never_defaults(self) -> None:
        from tests.test_eng_loop2_operator_web import png_bytes

        s = self.scheduler()
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        rid = self.send(s)["request_id"]
        frame = self.fx.publish_frames(1)
        self.fx.result(frame_id=frame, query_unix_s=self.clock.now, n=2, request_id=rid, preview=png_bytes(3))
        self.fx.state("AWAITING_CONFIRMATION")
        self.tick(s)
        self.clock.now += 10.5
        self.tick(s)
        self.assertEqual(self.status(s)[0], "NO_DECISION")
        self.assertEqual(len(self.cli.calls), 1)

    def test_unknown_send_blocks_all_progression(self) -> None:
        s = self.scheduler()
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        self.cli.outcomes.append({"raw": {"exit": None, "timeout": True, "stdout": "", "stderr": ""}})
        self.send(s)
        self.assertIn("UNKNOWN", s.blocked())
        self.assertIsNone(s.current_send_step("P1-2"))
        self.clock.now += 100
        self.tick(s)
        self.assertEqual(self.status(s)[:2], ["UNKNOWN", "PENDING"])

    def test_skip_then_session_terminal_marks_rest_not_executed(self) -> None:
        s = self.scheduler()
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        s.record_skip("P1-1", self.clock.now)
        self.fx.state("TERMINAL", reason="duration_reached")
        self.tick(s)
        self.assertEqual(self.status(s), ["SKIPPED_NOT_IN_VIEW"] + ["NOT_EXECUTED"] * 4)
        self.assertTrue(s.snapshot()["finished"])
        self.assertEqual(self.cli.calls, [])

    def test_release_only_when_tracking_with_same_track_and_stop_once(self) -> None:
        from tests.test_eng_loop2_operator_web import png_bytes

        s = self.scheduler("P3")

        def designate_and_track(track: str) -> None:
            rid = self.send(s)["request_id"]
            frame = self.fx.publish_frames(1)
            n = len(s.steps[s.index].get("decisions", [])) + s.index + 1
            self.fx.result(frame_id=frame, query_unix_s=self.clock.now, n=1, request_id=rid, seq=n, preview=png_bytes(n))
            self.fx.state("AWAITING_CONFIRMATION")
            self.tick(s)
            decision = self.submitter.submit(source="web", action="confirm", session_id="loop2-p1", binding={},
                                             binding_key=f"d{n}", token=f"loop2-p1-res{n}", index=0)
            s.record_decision(s.steps[s.index]["step_id"], "confirm", decision)
            self.fx.journal(kind="receipt", epoch=1, receipt={"request_id": decision["request_id"], "action": "confirm", "outcome": "APPLIED", "at_sequence": 9})
            self.fx.journal(kind="state", state="TRACKING", epoch=1)
            self.fx.state("TRACKING", track_id=track)
            self.tick(s)

        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        designate_and_track("t1")
        self.clock.now += 15.5
        self.tick(s)
        release = [c for c in self.cli.calls if c[3] == "release"]
        self.assertEqual(len(release), 1)
        self.assertEqual(release[0][release[0].index("--token") + 1], "t1")
        self.assertEqual(s.steps[0]["release"]["sent"], True)
        # 第二步：跟踪 id 在观察期变了 → 不发 release
        self.fx.state("IDLE")
        self.tick(s)
        designate_and_track("t2")
        self.fx.state("TRACKING", track_id="t3")
        self.clock.now += 15.5
        self.tick(s)
        self.assertEqual(len([c for c in self.cli.calls if c[3] == "release"]), 1)
        self.assertFalse(s.steps[1]["release"]["sent"])
        # 第三步跳过 → 计划末 stop：中止按钮先发过则不再发
        s.record_skip("P3-3", self.clock.now)
        self.submitter.submit(source="web", action="stop", session_id="loop2-p1", binding={},
                              binding_key=json.dumps({"button": "stop", "session_id": "loop2-p1"}, sort_keys=True))
        self.tick(s)
        self.assertEqual(len([c for c in self.cli.calls if c[3] == "stop"]), 1)
        self.assertEqual(s.steps[-1]["status"], "DONE")

    def test_follow_window_anchors_at_tracking_entry(self) -> None:
        from tests.test_eng_loop2_operator_web import png_bytes

        s = self.scheduler()
        s.index = 2  # P1-3：red 跟随 20 s
        s.steps[0]["status"] = s.steps[1]["status"] = "DONE"
        s.steps[2]["status"] = "AWAIT_SEND"
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        rid = self.send(s)["request_id"]
        frame = self.fx.publish_frames(1)
        self.fx.result(frame_id=frame, query_unix_s=self.clock.now, n=1, request_id=rid, preview=png_bytes(4))
        self.fx.state("AWAITING_CONFIRMATION")
        self.tick(s)
        decision = self.submitter.submit(source="web", action="confirm", session_id="loop2-p1", binding={}, binding_key="d", token="loop2-p1-res1", index=0)
        s.record_decision("P1-3", "confirm", decision)
        self.fx.journal(kind="receipt", epoch=1, receipt={"request_id": decision["request_id"], "action": "confirm", "outcome": "APPLIED", "at_sequence": 5})
        self.tick(s)
        self.clock.now += 4.0
        self.fx.journal(kind="state", state="TRACKING", epoch=1)
        self.fx.state("TRACKING", track_id="t9")
        self.tick(s)
        self.clock.now += 19.0  # 距确认 23 s，距进入 TRACKING 19 s
        self.tick(s)
        self.assertEqual(s.steps[2]["status"], "OBSERVING")
        self.clock.now += 1.1
        self.tick(s)
        self.assertEqual(s.steps[2]["status"], "DONE")


class HaltTests(SchedulerBase):
    """C6-1：`PlanScheduler.halt` + 共享 `Submitter.seal`：STOP/故障/中断后 runner 与网页业务不可逆封住；迟到 TERMINAL/
    回执只记录、不恢复；已受理步骤保留 request_id 记 HALTED（C6-3）。"""

    def app(self, scheduler: ops.PlanScheduler) -> web.App:
        app = web.App(monitor_factory=lambda sid, sdir: self.monitor, submitter=self.submitter, log=self.log, scheduler=scheduler,
                      feedback_path=Path(self.tmp.name) / "feedback.jsonl", clock=self.clock)
        app.bind_session("loop2-p1", self.fx.session_dir)
        return app

    def test_halt_during_decision_seals_web_and_runner_and_late_terminal_never_resumes(self) -> None:
        from tests.test_eng_loop2_operator_web import png_bytes

        s = self.scheduler("P3")
        app = self.app(s)
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        rid = self.send(s)["request_id"]
        frame = self.fx.publish_frames(1)
        self.fx.result(frame_id=frame, query_unix_s=self.clock.now, n=1, request_id=rid, preview=png_bytes(5))
        self.fx.state("AWAITING_CONFIRMATION")
        self.tick(s)
        self.assertEqual(s.snapshot()["decision_step"], "P3-1")
        s.halt("STOP1 test")
        view = {"session_id": "loop2-p1", "state": "AWAITING_CONFIRMATION", "reason": None, "epoch": 1, "result_id": "loop2-p1-res1",
                "query_id": "loop2-p1-q1", "request_id": rid, "frame_id": frame, "step_id": "P3-1"}
        for button in ("confirm", "reject", "send", "skip"):
            reply = app.action({"button": button, "view": view, "index": 0})
            self.assertFalse(reply["ok"])
            self.assertIn("封住", reply["message"])
        direct = self.submitter.submit(source="runner", action="release", session_id="loop2-p1", binding={}, binding_key="r", token="t1")
        self.assertTrue(direct["refused"] and direct.get("sealed"))
        # 迟到 TERMINAL：只记录，不发观察/release/计划末 stop，不恢复下一步
        self.fx.state("TERMINAL", reason="operator_stop")
        for _ in range(3):
            self.clock.now += 30
            self.tick(s)
        self.assertEqual([c[3] for c in self.cli.calls], ["ask"])
        self.assertEqual([st["status"] for st in s.snapshot()["steps"]], ["HALTED", "NOT_EXECUTED", "NOT_EXECUTED", "NOT_EXECUTED"])
        self.assertEqual(s.snapshot()["steps"][0]["request_id"], rid)
        self.assertIsNone(s.current_send_step("P3-2"))
        self.assertIn("STOP1 test", s.blocked())
        # 只剩原 stop：本会话至多一次
        key = json.dumps({"button": "stop", "session_id": "loop2-p1"}, sort_keys=True)
        first = self.submitter.submit(source="runner", action="stop", session_id="loop2-p1", binding={}, binding_key=key)
        second = self.submitter.submit(source="web", action="stop", session_id="loop2-p1", binding={}, binding_key=key)
        self.assertFalse(first["refused"])
        self.assertTrue(second["refused"])
        self.assertEqual([c[3] for c in self.cli.calls], ["ask", "stop"])

    def test_send_in_flight_when_halted_is_kept_as_accepted_not_unexecuted(self) -> None:
        s = self.scheduler()
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        step = s.current_send_step("P1-1")
        key = json.dumps({"button": "send_or_skip", "step_id": "P1-1", "attempt": step["attempt"]}, sort_keys=True)
        # 发送已过封住检查、CLI 在途时封住；回执随后到达
        reply = self.submitter.submit(source="web", action="ask", session_id="loop2-p1", binding={}, binding_key=key,
                                      instruction=step["instruction"], intent=step["intent"])
        s.halt("DIAG_FAULT test")
        self.assertEqual(s.snapshot()["steps"][0]["status"], "NOT_EXECUTED")
        s.record_send("P1-1", reply)
        first = s.snapshot()["steps"][0]
        self.assertEqual((first["status"], first["request_id"]), ("HALTED", reply["request_id"]))
        self.clock.now += 60
        self.tick(s)
        self.assertEqual([st["status"] for st in s.snapshot()["steps"]][1:], ["NOT_EXECUTED"] * 4)
        self.assertEqual(len(self.cli.calls), 1)

    def test_accepted_send_racing_terminal_is_recorded_before_closeout_can_read(self) -> None:
        """C6-3 竞态（OPSC6返工 SUB:1 全套中 `test_backend_fatal_…` 暴露）：网页发送已受理、TERMINAL 先被处理时，
        收尾持有共享在途锁后读到的逐步记录必须已含该 request_id，不能记成未执行。"""
        s = self.scheduler()
        app = self.app(s)
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        self.cli.delay_s = 0.3
        real_record = s.record_send

        def slow_record(step_id: str, reply: dict[str, Any]) -> None:
            time.sleep(0.3)  # 计划记录晚于 CLI 返回：放大原竞态窗口
            real_record(step_id, reply)

        s.record_send = slow_record  # type: ignore[method-assign]
        view = {"session_id": "loop2-p1", "state": "IDLE", "reason": None, "epoch": 1, "step_id": "P1-1", "plan_sha256": "f" * 64}
        worker = threading.Thread(target=lambda: app.action({"button": "send", "view": view}))
        worker.start()
        while not self.cli.calls:
            time.sleep(0.01)
        self.fx.state("TERMINAL", reason="backend_fatal")
        self.tick(s)  # TERMINAL 先处理：当前步此刻仍是等待发送
        self.assertTrue(self.submitter.in_flight.acquire(timeout=10))  # 收尾同一做法：先持有在途锁
        try:
            first = s.snapshot()["steps"][0]
        finally:
            self.submitter.in_flight.release()
        worker.join(timeout=10)
        self.assertEqual((first["status"], bool(first["request_id"])), ("NO_CANDIDATE", True))
        self.assertIn("backend_fatal", first["reason"])

    def test_unknown_result_seals_the_shared_channel_too(self) -> None:
        s = self.scheduler()
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        self.cli.outcomes.append({"raw": {"exit": None, "timeout": True, "stdout": "", "stderr": ""}})
        self.send(s)
        reply = self.submitter.submit(source="runner", action="ask", session_id="loop2-p1", binding={}, binding_key="x", instruction="y")
        self.assertTrue(reply.get("sealed"))
        self.assertEqual(len(self.cli.calls), 1)


class OpsR1ReworkSchedulerTests(SchedulerBase):
    """OPSR1返工（R1@OpsK1K2K3K4）R1-1 / R1-2：生产 `PlanScheduler` + 真实 `Monitor`/桥写函数 + 共享 `Submitter`。"""

    def present(self, s: ops.PlanScheduler, n: int = 1) -> str:
        from tests.test_eng_loop2_operator_web import png_bytes

        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        rid = self.send(s)["request_id"]
        frame = self.fx.publish_frames(1)
        self.fx.result(frame_id=frame, query_unix_s=self.clock.now, n=n, request_id=rid, preview=png_bytes(4))
        self.fx.state("AWAITING_CONFIRMATION")
        self.tick(s)
        self.assertEqual(s.snapshot()["decision_step"], "P1-1")
        return rid

    # R1-1：候选呈现中（已受理、待选择）会话 TERMINAL → 与 halt 同口径记 HALTED 并保留 request_id，仍是样本
    def test_r1_1_terminal_during_presentation_keeps_accepted_step_as_sample(self) -> None:
        s = self.scheduler()
        rid = self.present(s, n=2)
        self.fx.state("TERMINAL", reason="operator_stop")
        self.tick(s)
        steps = s.snapshot()["steps"]
        self.assertEqual((steps[0]["status"], steps[0]["request_id"]), ("HALTED", rid))
        self.assertIn("session_terminal:operator_stop", steps[0]["reason"])
        self.assertEqual([st["status"] for st in steps[1:]], ["NOT_EXECUTED"] * 4)
        pva = summ.plan_vs_actual(self.plan["playbooks"]["P1"], steps)
        self.assertEqual((pva["steps"][0]["status"], pva["steps"][0]["is_sample"]), ("HALTED", True))
        self.assertEqual((pva["designate_sent"], pva["designate_not_executed"], pva["designate_halted"]), (1, 3, 1))

    # R1-1：结果未知（W4）的步骤遇会话 TERMINAL 仍记 UNKNOWN（不改写成未执行），request_id 保留
    def test_r1_1_unknown_step_stays_unknown_when_session_terminal(self) -> None:
        s = self.scheduler()
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        self.cli.outcomes.append({"raw": {"exit": None, "timeout": True, "stdout": "", "stderr": ""}})
        reply = self.send(s)
        self.fx.state("TERMINAL", reason="duration_reached")
        self.tick(s)
        steps = s.snapshot()["steps"]
        self.assertEqual((steps[0]["status"], steps[0]["request_id"]), ("UNKNOWN", reply["request_id"]))
        self.assertIn("session_terminal:duration_reached", steps[0]["reason"])
        self.assertEqual([st["status"] for st in steps[1:]], ["NOT_EXECUTED"] * 4)
        pva = summ.plan_vs_actual(self.plan["playbooks"]["P1"], steps)
        self.assertTrue(pva["steps"][0]["is_sample"])
        self.assertEqual(pva["designate_not_executed"], 3)

    # R1-2：confirm 在途（CLI 等回执）时会话先受理并写 receipt/TRACKING → 不得记 NO_DECISION；回执记入、按 receipt 锚点观察
    def test_r1_2_confirm_in_flight_when_state_changes_is_recorded_and_observed(self) -> None:
        s = self.scheduler()
        self.present(s)
        self.cli.delay_s = 0.5
        replies: list[dict[str, Any]] = []
        worker = threading.Thread(target=lambda: replies.append(self.submitter.submit(
            source="web", action="confirm", session_id="loop2-p1", binding={}, binding_key="decide-1", token="loop2-p1-res1", index=0,
            on_reply=lambda r: s.record_decision("P1-1", "confirm", r))))
        worker.start()
        while len(self.cli.calls) < 2:
            time.sleep(0.01)
        crid = self.cli.calls[1][self.cli.calls[1].index("--request-id") + 1]
        receipt_at = self.clock.now
        self.fx.journal(kind="receipt", epoch=1, receipt={"request_id": crid, "action": "confirm", "outcome": "APPLIED", "at_sequence": 5})
        self.fx.journal(kind="state", state="TRACKING", epoch=1)
        self.fx.state("TRACKING", track_id="t7")
        self.tick(s)  # 回执尚在途：状态已变也不得关闭为 NO_DECISION
        self.assertNotEqual(s.snapshot()["steps"][0]["status"], "NO_DECISION")
        worker.join(timeout=10)
        self.assertFalse(replies[0]["refused"])
        self.tick(s)
        step = s.steps[0]
        self.assertEqual((step["status"], step.get("decision"), step.get("decision_request_id")), ("OBSERVING", "confirm", crid))
        self.assertEqual((step["anchor_unix_s"], step["anchor_source"]), (receipt_at, "journal_receipt"))
        self.assertTrue(step["tracking_established"])
        self.clock.now += 20.5
        self.tick(s)
        self.assertEqual(self.status(s)[:2], ["DONE", "AWAIT_SEND"])
        self.assertTrue(s.steps[0]["follow_verified"])

    # R1-2：提交前的窗口里该步已因呈现结束关闭（无在途）→ 迟到的已受理选择照记，且其后尚无动作时恢复该步观察
    def test_r1_2_accepted_decision_after_step_closed_reopens_observation(self) -> None:
        s = self.scheduler()
        self.present(s)
        self.fx.state("QUERYING")
        self.tick(s)
        self.assertEqual(self.status(s)[:2], ["NO_DECISION", "AWAIT_SEND"])
        reply = self.submitter.submit(source="web", action="confirm", session_id="loop2-p1", binding={}, binding_key="decide-1",
                                      token="loop2-p1-res1", index=0, on_reply=lambda r: s.record_decision("P1-1", "confirm", r))
        receipt_at = self.clock.now
        self.fx.journal(kind="receipt", epoch=1, receipt={"request_id": reply["request_id"], "action": "confirm", "outcome": "APPLIED", "at_sequence": 6})
        step = s.steps[0]
        self.assertEqual((step["status"], step.get("decision"), step.get("decision_request_id")), ("OBSERVING", "confirm", reply["request_id"]))
        self.assertEqual(s.steps[1]["status"], "PENDING")
        self.assertEqual(s.snapshot()["current"]["step_id"], "P1-1")
        self.assertTrue(step["decisions"][-1]["late"])
        self.tick(s)
        self.assertEqual(step["anchor_unix_s"], receipt_at)

    # R1-2：迟到的已受理选择到达时其后已有本人动作（跳过）→ 不能恢复：该步 UNKNOWN、停依赖推进（照记，不删）
    def test_r1_2_accepted_decision_after_later_action_is_unknown_and_blocks(self) -> None:
        s = self.scheduler()
        self.present(s)
        self.fx.state("QUERYING")
        self.tick(s)
        s.record_skip("P1-2", self.clock.now)
        reply = self.submitter.submit(source="web", action="confirm", session_id="loop2-p1", binding={}, binding_key="decide-1",
                                      token="loop2-p1-res1", index=0, on_reply=lambda r: s.record_decision("P1-1", "confirm", r))
        step = s.steps[0]
        self.assertEqual((step["status"], step["decisions"][-1]["request_id"]), ("UNKNOWN", reply["request_id"]))
        self.assertIn("UNKNOWN", s.blocked())
        self.assertEqual(self.status(s)[1], "SKIPPED_NOT_IN_VIEW")


class ObservationAnchorTests(SchedulerBase):
    """IR-OPS-6：观察/跟随只锚定会话原流；缺原流 → UNKNOWN 停依赖；拒绝/未播种/旧纪元不算新指定已跟随。"""

    def present_and_decide(self, s: ops.PlanScheduler, action: str, *, seq: int = 1) -> dict[str, Any]:
        from tests.test_eng_loop2_operator_web import png_bytes

        rid = self.send(s)["request_id"]
        frame = self.fx.publish_frames(1)
        self.fx.result(frame_id=frame, query_unix_s=self.clock.now, n=1, request_id=rid, seq=seq, preview=png_bytes(seq + 10))
        self.fx.state("AWAITING_CONFIRMATION")
        self.tick(s)
        decision = self.submitter.submit(source="web", action=action, session_id="loop2-p1", binding={}, binding_key=f"{action}{seq}",
                                         token=f"loop2-p1-res{seq}", index=0 if action == "confirm" else None)
        s.record_decision(s.steps[s.index]["step_id"], action, decision)
        return decision

    def start(self, playbook: str = "P1") -> ops.PlanScheduler:
        s = self.scheduler(playbook)
        self.fx.publish_frames(1)
        self.fx.state("IDLE")
        self.tick(s)
        return s

    def test_missing_selection_receipt_blocks_unknown_instead_of_cli_time(self) -> None:
        s = self.start()
        self.present_and_decide(s, "confirm")
        self.fx.state("TRACKING", track_id="t1")
        self.fx.journal(kind="state", state="TRACKING", epoch=1)
        self.tick(s)
        self.assertIsNone(s.blocked())
        self.clock.now += ops.ANCHOR_WAIT_S + 0.1
        self.tick(s)
        self.assertIn("selection_receipt_missing_in_journal", s.blocked())
        step = s.steps[0]
        self.assertEqual(step["status"], "UNKNOWN")
        self.assertNotIn("anchor_unix_s", step)  # 不以 CLI 返回时刻补值
        self.clock.now += 60
        self.tick(s)
        self.assertEqual(self.status(s)[:2], ["UNKNOWN", "PENDING"])

    def test_reject_never_establishes_follow_even_if_tracking_resumes(self) -> None:
        s = self.start("P3")
        decision = self.present_and_decide(s, "reject")
        self.fx.journal(kind="receipt", epoch=1, receipt={"request_id": decision["request_id"], "action": "reject", "outcome": "APPLIED", "at_sequence": 4})
        self.fx.journal(kind="state", state="TRACKING", epoch=1)  # 回到确认前的旧目标
        self.fx.state("TRACKING", track_id="t-old")
        self.tick(s)
        self.clock.now += 15.1
        self.tick(s)
        step = s.steps[0]
        self.assertEqual((step["status"], step.get("tracking_established"), step["follow_verified"]), ("DONE", None, False))
        self.assertFalse(step["release"]["sent"])  # P3 release 只给本步建立的跟踪
        self.assertEqual([c[3] for c in self.cli.calls], ["ask", "reject"])

    def test_confirm_with_reject_detail_is_not_seeded(self) -> None:
        s = self.start()
        decision = self.present_and_decide(s, "confirm")
        self.fx.journal(kind="receipt", epoch=1, detail="candidate_expired",
                        receipt={"request_id": decision["request_id"], "action": "confirm", "outcome": "APPLIED", "at_sequence": 4})
        self.fx.journal(kind="state", state="TRACKING", epoch=1)
        self.fx.state("TRACKING", track_id="t9")
        self.tick(s)
        self.clock.now += 15.1
        self.tick(s)
        self.assertEqual((s.steps[0]["status"], s.steps[0]["follow_verified"]), ("DONE", False))

    def test_old_epoch_tracking_does_not_count(self) -> None:
        s = self.start()
        decision = self.present_and_decide(s, "confirm")
        self.fx.journal(kind="receipt", epoch=2, receipt={"request_id": decision["request_id"], "action": "confirm", "outcome": "APPLIED", "at_sequence": 4})
        self.fx.journal(kind="state", state="TRACKING", epoch=1)
        self.fx.state("TRACKING", epoch=1, track_id="t-old")
        self.tick(s)
        self.clock.now += 15.1
        self.tick(s)
        self.assertEqual((s.steps[0]["status"], s.steps[0]["follow_verified"]), ("DONE", False))
        self.assertIsNone(s.blocked())

    def test_tracking_state_without_journal_event_is_unknown(self) -> None:
        s = self.start()
        decision = self.present_and_decide(s, "confirm")
        self.fx.journal(kind="receipt", epoch=1, receipt={"request_id": decision["request_id"], "action": "confirm", "outcome": "APPLIED", "at_sequence": 4})
        self.fx.state("TRACKING", track_id="t3")
        self.tick(s)
        self.clock.now += ops.ANCHOR_WAIT_S + 0.1
        self.tick(s)
        self.assertIn("tracking_state_without_journal_event", s.blocked())
        self.assertNotEqual(s.steps[0].get("tracking_at_source"), "poll")

    def test_no_candidate_and_skip_open_no_observation_window(self) -> None:
        s = self.start()
        s.record_skip("P1-1", self.clock.now)
        rid = self.send(s)["request_id"]
        with (self.fx.session_dir / "results.jsonl").open("a") as handle:
            handle.write(json.dumps({"purpose": "designate", "request_id": rid, "status": "none", "result_id": "r9"}) + "\n")
        self.fx.state("IDLE")
        self.tick(s)
        self.assertEqual(self.status(s)[:3], ["SKIPPED_NOT_IN_VIEW", "NO_CANDIDATE", "AWAIT_SEND"])
        self.assertEqual(s.snapshot()["current"]["phase"], "await_send")  # 立即列下一步，无观察计时


# --- 归档、STOP 分流、守账、模式 ------------------------------------------------------------


class ArchiveAndStopTests(unittest.TestCase):
    def test_archive_moves_only_listed_files_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, out = Path(tmp) / "repo", Path(tmp) / "out"
            runtime = repo / "runtime"
            (runtime / "frames/retained_frame_metadata").mkdir(parents=True)
            (runtime / "frames/frame_0000000001.jpg").write_bytes(b"\xff\xd8\xff")
            (runtime / "frames/frame_0000000001.json").write_text("{}")
            (runtime / "frames/latest.json").write_text("{}")
            (runtime / "m3_body_truth.jsonl").write_text("x\n")
            (runtime / "runs/loop2-p1-resident-0").mkdir(parents=True)
            (runtime / "runs/other-run").mkdir(parents=True)
            (runtime / "scenario_config.json").write_text("{}")
            report = ops.archive_attempt(repo, out, "loop2-p1")
            self.assertIn("runs/loop2-p1-resident-0", report["moved"])
            self.assertTrue((runtime / "frames/latest.json").exists())
            self.assertTrue((runtime / "runs/other-run").exists())
            self.assertFalse((runtime / "m3_body_truth.jsonl").exists())
            (runtime / "scenario_config.json").write_text("{}")
            with self.assertRaises(ops.Stop) as caught:
                ops.archive_attempt(repo, out, "loop2-p1")
            self.assertEqual(caught.exception.code, "S-ARCHIVE")

    def test_archive_without_layout_copy_is_s_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "repo/runtime").mkdir(parents=True)
            with self.assertRaises(ops.Stop) as caught:
                ops.archive_attempt(Path(tmp) / "repo", Path(tmp) / "out", "loop2-p2")
            self.assertIn("layout_copy_missing", caught.exception.detail)

    def test_terminal_reasons_map_to_original_stops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            journal = Path(tmp) / "j.jsonl"
            journal.write_text(json.dumps({"kind": "backend_fatal", "detail": "worker_stuck: S_ENVELOPE inference"}) + "\n{broken\n")
            self.assertIsNone(ops.classify_terminal("operator_stop", journal))
            self.assertIsNone(ops.classify_terminal("duration_reached", journal))
            self.assertEqual(ops.classify_terminal("backend_fatal", journal).code, "S-ENVELOPE")
            journal.write_text(json.dumps({"kind": "backend_fatal", "detail": "timeout"}) + "\n")
            self.assertEqual(ops.classify_terminal("backend_fatal", journal).code, "S-BACKEND")
            rebuild = ops.classify_terminal("rebuild_limit", journal)
            self.assertEqual((rebuild.code, rebuild.stop_all), ("S-REBUILD", True))
            self.assertIn("UNKNOWN", rebuild.detail)

    def test_ledger_limits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = ops.Ledger(Path(tmp) / "l.json")
            for _ in range(5):
                ledger.take("overlay_generations")
            with self.assertRaises(ops.Stop) as caught:
                ledger.take("overlay_generations")
            self.assertEqual(caught.exception.code, "S-ENVELOPE")
            self.assertEqual(ops.Ledger(Path(tmp) / "l.json").used("overlay_generations"), 5)
            ledger.take("residual_moves")
            with self.assertRaises(ops.Stop):
                ledger.take("residual_moves")

    def test_modes_route_independently(self) -> None:
        from contextlib import redirect_stderr

        diag = ["diag", "--request-id", ops.DIAG_REQUEST_ID, "--playbook", "P1", "--p2-object", "red_car"]
        for argv, needle in ((["--mode", "diagnostic", "gate"], "诊断模式只运行 diag"),
                             (["--mode", "diagnostic", "play"], "诊断模式只运行 diag"),
                             (diag, "diag_stage_requires_mode_diagnostic"),
                             (["--mode", "diagnostic", "diag", "--request-id", "P1-ENG-LOOP-002:9bac8fd0:SUB:1", "--playbook", "P1",
                               "--p2-object", "red_car"], "DIAG_REFUSED request_id")):
            stderr = io.StringIO()
            with self.subTest(argv=argv), redirect_stderr(stderr):
                self.assertEqual(ops.main(argv), 3)
                self.assertIn(needle, stderr.getvalue())


class DiagAccountTests(unittest.TestCase):
    """§2 SUB:3 粗维度：先查额/先记占额，越界即 STOP1；墙钟留收尾预留；体积按读数核。"""

    def test_limits_wall_and_disk(self) -> None:
        from tests.test_eng_loop2_operator_web import Clock

        with tempfile.TemporaryDirectory() as tmp:
            clock = Clock(1000.0)
            account = ops.DiagAccount(Path(tmp), "20261008T000000Z", "/home/jetson/eng-loop2-diag/20261008T000000Z", clock=clock)
            account.take("master_connections")
            account.take("master_connections")
            with self.assertRaises(ops.DiagStop) as caught:
                account.take("master_connections")
            self.assertEqual(caught.exception.category, 1)
            account.take("serve_starts")
            for key in ("serve_starts", "fault_restarts"):
                with self.assertRaises(ops.DiagStop):
                    account.take(key)
            account.take("plays")
            with self.assertRaises(ops.DiagStop):
                account.take("plays")
            clock.now += ops.DIAG_LIMITS["wall_s"] - ops.DIAG_CLOSEOUT_RESERVE_S - 100
            account.require_time(99, "ok")
            with self.assertRaises(ops.DiagStop):
                account.require_time(101, "too late")
            self.assertTrue(account.near_limit("board", 180_000_000))
            self.assertFalse(account.near_limit("air", 100_000_000))
            account.disk("board", 210_000_000, "probe")
            clock.now += 1000
            account.finish()
            data = json.loads((Path(tmp) / "ops-diagnostic-ledger.json").read_text())
            self.assertEqual(data["used"]["master_connections"], 2)
            self.assertEqual(data["request_id"], ops.DIAG_REQUEST_ID)
            self.assertEqual(len(data["deviations"]), 2)  # 板端越界 + 墙钟越界，照记不追认
            self.assertIn("UNKNOWN", data["play"]["button_start_unix_s"])


# --- 端到端：生产入口逐阶段 ---------------------------------------------------------------------


class EndToEndTests(RepoTestBase):
    def test_prep_unit_reads_and_stops_for_g4(self) -> None:
        raw = self.register()
        rc, out = self.fx.main("prep", "--registered-release", str(raw))
        self.assertEqual(rc, 0, out)
        self.assertIn("NEXT_GATE G4", out)
        tally = (self.fx.out / "ssh/unit-1.tsv").read_text()
        self.assertEqual(tally.count("channel\tprep-read\tstart"), 1)
        script = (self.fx.out / "prep/prep-read.sh").read_text()
        self.assertTrue(script.startswith("EXP_HOST=jetson-orin\n"))
        self.assertIn("STOP() {", script)  # 附录 P 原文

    def test_prep_stop_line_from_board_stops(self) -> None:
        raw = self.register()
        self.fx.cfg["prep_stdout"] = "\nSTOP P04_PORT_OCCUPIED\n"
        self.fx.save()
        rc, out = self.fx.main("prep", "--registered-release", str(raw))
        self.assertEqual(rc, 3)
        self.assertIn("STOP S-PRECHECK prep_read", out)

    def test_receipt_requires_g4_then_runs_unit_2(self) -> None:
        raw = self.register()
        self.assertEqual(self.fx.main("prep", "--registered-release", str(raw))[0], 0)
        rc, out = self.fx.main("receipt", "--registered-release", str(raw))
        self.assertEqual(rc, 3)
        self.assertIn("g4_release_missing", out)
        self.assertEqual(sum(1 for a in self.fx.calls("ssh") if "-fN" in a), 1)  # 未开单元 #2
        self.fx.commit_docs(ops.PROPOSAL, f"\n- `g4_release: {ops.sha256_file(self.fx.out / 'prep/prep.stdout')}`\n")
        receipt = build_k_receipt(hz=5.0, retained_frame_count=1500, p95_s=2.6, host="jetson", backend="http", model_form="c2-merged")
        self.fx.cfg.update(k_receipt=receipt.payload(), status={"model_identity": {k: "x" for k in bridge.LLAMA_IDENTITY_KEYS},
                                                                "serve_code_sha256": "d" * 64, "http_budget": {"batch": 1}})
        self.fx.save()
        rc, out = self.fx.main("receipt", "--registered-release", str(raw))
        self.assertEqual(rc, 0, out)
        tally = (self.fx.out / "ssh/unit-2.tsv").read_text()
        for name in ops.CHANNELS[2]:
            self.assertEqual(tally.count(f"channel\t{name}\tstart"), 1, name)
        outcome = json.loads((self.fx.out / "receipt-outcome.json").read_text())
        self.assertEqual((outcome["measure_rc"], outcome["k_receipt_rc"], outcome["release"]["released"]), (0, 0, True))
        assets = json.loads((self.fx.out / "b0b/assets.json").read_text())
        self.assertEqual(assets["runtime_build"], "b1234")
        ledger = json.loads((self.fx.out / "ops-ledger.json").read_text())
        self.assertEqual((ledger["ssh_units"], ledger["serve_starts"], ledger["version_calls"], ledger["transfer_batches"]), (2, 1, 2, 2))
        self.assertTrue((self.fx.repo / "runtime/scenario_config.json").is_file())

    def test_receipt_deploy_mismatch_stops_before_serve(self) -> None:
        raw = self.register()
        self.assertEqual(self.fx.main("prep", "--registered-release", str(raw))[0], 0)
        self.fx.commit_docs(ops.PROPOSAL, f"\n- `g4_release: {ops.sha256_file(self.fx.out / 'prep/prep.stdout')}`\n")
        self.fx.cfg["tamper"] = "config/deploy-a.txt"
        self.fx.save()
        rc, out = self.fx.main("receipt", "--registered-release", str(raw))
        self.assertEqual(rc, 3)
        self.assertIn("S-IDENTITY deploy_sha_mismatch", out)
        self.assertNotIn("serve", (self.fx.out / "ssh/unit-2.tsv").read_text())

    def test_play_stage_runs_web_plan_session_archive_summary(self) -> None:
        raw = self.register()
        self.assertEqual(self.fx.main("prep", "--registered-release", str(raw))[0], 0)
        self.fx.commit_docs(ops.PROPOSAL, f"\n- `g4_release: {ops.sha256_file(self.fx.out / 'prep/prep.stdout')}`\n")
        receipt = build_k_receipt(hz=5.0, retained_frame_count=1500, p95_s=2.6, host="jetson", backend="http", model_form="c2-merged")
        self.fx.cfg.update(k_receipt=receipt.payload(), derive_bc=DERIVE,
                           status={"model_identity": {k: "x" for k in bridge.LLAMA_IDENTITY_KEYS}, "serve_code_sha256": "d" * 64,
                                   "http_budget": {"batch": 1}})
        self.fx.save()
        self.assertEqual(self.fx.main("receipt", "--registered-release", str(raw))[0], 0)
        self.assertEqual(self.fx.main("plan", "--p2-object", "red_car")[0], 0)
        self.fx.cfg["status"]["http_budget"] = {"batch": 2}
        self.fx.save()
        (self.fx.repo / "runtime/scenario_config.json").unlink()
        port = free_port()
        stop_frames = threading.Event()
        clicks: list[str] = []

        def frames() -> None:
            publisher = FixtureFramePublisher(self.fx.repo / "runtime", scenario_id="deterministic-loop-untethered")
            while not stop_frames.is_set():
                publisher.publish(b"\xff\xd8\xff\xe0x")
                time.sleep(0.1)

        def operator() -> None:
            nonce = None
            deadline = time.time() + 60
            while time.time() < deadline:
                try:
                    if nonce is None:
                        page = http_get(port, "/").decode()
                        nonce = page.split('const NONCE="', 1)[1].split('"', 1)[0]
                    state = json.loads(http_get(port, "/api/state"))
                except (OSError, IndexError, ValueError):
                    time.sleep(0.1)
                    continue
                if state.get("summary"):
                    http_post(port, nonce, {"button": "feedback", "view": {"attempt": "loop2-p1"}, "label": "BLOCKED", "text": "替身"})
                    return
                session = state.get("session") or {}
                current = (state.get("plan") or {}).get("current") or {}
                if session.get("state") and current.get("phase") == "await_send" and not state.get("blocked"):
                    st = session["state"]
                    button = "skip" if current["step_id"] == "P1-2" else "send"
                    view = {"session_id": session["session_id"], "state": st["state"], "reason": st["reason"], "epoch": st["epoch"],
                            "step_id": current["step_id"], "plan_sha256": state["plan"]["plan_sha256"]}
                    reply = http_post(port, nonce, {"button": button, "view": view})
                    if reply.get("ok"):
                        clicks.append(f"{button}:{current['step_id']}")
                if (session.get("state") or {}).get("state") == "TERMINAL":
                    stop_frames.set()
                time.sleep(0.15)

        threading.Thread(target=frames, daemon=True).start()
        worker = threading.Thread(target=operator, daemon=True)
        worker.start()
        old_quiet = ops.UNITY_STOP_QUIET_S
        ops.UNITY_STOP_QUIET_S = 0.5
        self.addCleanup(setattr, ops, "UNITY_STOP_QUIET_S", old_quiet)
        try:
            rc, out = self.fx.main("play", "--registered-release", str(raw), "--playbooks", "P1", "--port", str(port),
                                   "--feedback-wait-s", "30")
        finally:
            stop_frames.set()
            worker.join(timeout=10)
        self.assertEqual(rc, 0, out)
        self.assertEqual(clicks, ["send:P1-1", "skip:P1-2", "send:P1-3", "send:P1-4"])
        record = json.loads((self.fx.out / "play/play-record.json").read_text())
        steps = {s["step_id"]: s["status"] for s in record["attempts"][0]["steps"]}
        self.assertEqual(steps, {"P1-1": "NO_CANDIDATE", "P1-2": "SKIPPED_NOT_IN_VIEW", "P1-3": "NO_CANDIDATE", "P1-4": "NO_CANDIDATE", "P1-5": "DONE"})
        self.assertEqual(record["attempts"][0]["terminal_reason"], "operator_stop")
        self.assertTrue((self.fx.out / "play/loop2-p1/unity-runtime/scenario_config.json").is_file())
        summary = json.loads((self.fx.out / "play/ops-summary.json").read_text())
        attempt = summary["attempts"][0]
        self.assertEqual(attempt["plan_vs_actual"]["designate_skipped_not_in_view"], 1)
        self.assertEqual(attempt["consistency_issues"], [])
        self.assertTrue(attempt["score_call"]["called"])
        feedback = (self.fx.out / "play/feedback.jsonl").read_text()
        self.assertIn('"BLOCKED"', feedback)
        tally = (self.fx.out / "ssh/unit-3.tsv").read_text()
        self.assertEqual([tally.count(f"channel\t{n}\tstart") for n in ops.CHANNELS[3]], [1, 1])
        asks = [a for a in self.fx.calls("python") if a[:3] == ["-m", "controller.language_loop", "ask"]]
        self.assertEqual(len(asks), 3)


# --- C6@OpsK1K2K3K4：正式 play 生产入口的失败/超时/中断路径（C6-1/C6-2/C6-3；零模型替身） -----------------------------


def cli_calls(fx: RepoFixture, action: str) -> list[list[str]]:
    return [a for a in fx.calls("python") if a[:3] == ["-m", "controller.language_loop", action]]


def wait_pid_gone(pid_file: Path, timeout_s: float = 30.0) -> None:
    """替身会话在测试内自行退出（不杀进程）；清理临时目录前等它结束。"""
    if not pid_file.is_file():
        return
    pid = int(pid_file.read_text())
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            return
        time.sleep(0.1)


class OperatorClient:
    """本机网页的本人操作替身（只经 HTTP + nonce，与真实浏览器同一服务端路径）。"""

    def __init__(self, port: int):
        self.port, self.nonce = port, None

    def state(self) -> dict[str, Any]:
        if self.nonce is None:
            page = http_get(self.port, "/").decode()
            self.nonce = page.split('const NONCE="', 1)[1].split('"', 1)[0]
        return json.loads(http_get(self.port, "/api/state"))

    def click(self, state: dict[str, Any], button: str, step_id: str | None = None) -> dict[str, Any]:
        session = state["session"]
        st = session["state"]
        current = (state.get("plan") or {}).get("current") or {}
        view = {"session_id": session["session_id"], "state": st["state"], "reason": st["reason"], "epoch": st["epoch"],
                "step_id": step_id or current.get("step_id"), "plan_sha256": state["plan"]["plan_sha256"]}
        return http_post(self.port, self.nonce, {"button": button, "view": view})


class FormalFailurePathTests(RepoTestBase):
    """C6-1/C6-2/C6-3：`play_ops play` 生产入口 + 临时目录替身；失败也须封住业务、发原 stop、等会话、提示本人停 Play、
    只移动归档、保留完整尝试记录，并照做服务释放/日志/单元关闭/记录/摘要/网页关闭（一步失败不跳过其余）。"""

    def setUp(self) -> None:
        super().setUp()
        self.raw = self.register()
        self.assertEqual(self.fx.main("prep", "--registered-release", str(self.raw))[0], 0)
        self.fx.commit_docs(ops.PROPOSAL, f"\n- `g4_release: {ops.sha256_file(self.fx.out / 'prep/prep.stdout')}`\n")
        receipt = build_k_receipt(hz=5.0, retained_frame_count=1500, p95_s=2.6, host="jetson", backend="http", model_form="c2-merged")
        self.fx.cfg.update(k_receipt=receipt.payload(), derive_bc=DERIVE,
                           status={"model_identity": {k: "x" for k in bridge.LLAMA_IDENTITY_KEYS}, "serve_code_sha256": "d" * 64,
                                   "http_budget": {"batch": 1}})
        self.fx.save()
        self.assertEqual(self.fx.main("receipt", "--registered-release", str(self.raw))[0], 0)
        self.assertEqual(self.fx.main("plan", "--p2-object", "red_car")[0], 0)
        self.fx.cfg["status"]["http_budget"] = {"batch": 2}
        self.fx.save()
        (self.fx.repo / "runtime/scenario_config.json").unlink()
        # 用 getattr 取原值：修前代码没有收尾等待常量时同样可跑（修前红只来自行为，不来自缺属性）。
        names = ("UNITY_STOP_QUIET_S", "SESSION_STOP_WAIT_S", "UNITY_STOP_CLOSEOUT_WAIT_S")
        saved = ({n: getattr(ops, n, None) for n in names}, ops.LIMITS["play_wall_s"])

        def restore() -> None:
            for name, value in saved[0].items():
                if value is None:
                    if hasattr(ops, name):
                        delattr(ops, name)
                else:
                    setattr(ops, name, value)
            ops.LIMITS["play_wall_s"] = saved[1]

        self.addCleanup(restore)
        ops.UNITY_STOP_QUIET_S = 0.5
        self.port = free_port()
        self.client = OperatorClient(self.port)
        self.stop_frames = threading.Event()
        self.refusals: list[dict[str, Any]] = []
        self.addCleanup(lambda: wait_pid_gone(self.fx.out / "play/sessions/loop2-p1.fake-pid"))

    def frames(self, max_s: float = 60.0) -> None:
        publisher = FixtureFramePublisher(self.fx.repo / "runtime", scenario_id="deterministic-loop-untethered")
        end = time.time() + max_s
        while not self.stop_frames.is_set() and time.time() < end:
            publisher.publish(b"\xff\xd8\xff\xe0x")
            time.sleep(0.1)

    def operator(self, policy) -> None:
        deadline = time.time() + 120
        fed_back = False
        while time.time() < deadline:
            try:
                state = self.client.state()
            except (OSError, IndexError, ValueError):
                if fed_back:
                    return
                time.sleep(0.1)
                continue
            if state.get("summary") and not fed_back:
                for item in state["summary"]["attempts"]:
                    http_post(self.port, self.client.nonce, {"button": "feedback", "view": {"attempt": item["session_id"]},
                                                             "label": "BLOCKED", "text": "替身"})
                fed_back = True
            elif state.get("session", {}) and (state["session"] or {}).get("state"):
                policy(state)
            time.sleep(0.15)

    def standard(self, state: dict[str, Any]) -> None:
        current = (state.get("plan") or {}).get("current") or {}
        if current.get("phase") == "await_send" and not state.get("blocked"):
            self.client.click(state, "skip" if current["step_id"] == "P1-2" else "send")
        if state["session"]["state"]["state"] == "TERMINAL":
            self.stop_frames.set()

    def play(self, policy, *, frames_max_s: float = 60.0, playbooks: tuple[str, ...] = ("P1",)) -> tuple[int, str]:
        threading.Thread(target=self.frames, args=(frames_max_s,), daemon=True).start()
        worker = threading.Thread(target=self.operator, args=(policy,), daemon=True)
        worker.start()
        try:
            return self.fx.main("play", "--registered-release", str(self.raw), "--playbooks", *playbooks, "--port", str(self.port),
                                "--feedback-wait-s", "3")
        finally:
            self.stop_frames.set()
            worker.join(timeout=15)

    def record(self) -> dict[str, Any]:
        return json.loads((self.fx.out / "play/play-record.json").read_text())

    def summary_attempt(self) -> dict[str, Any]:
        return json.loads((self.fx.out / "play/ops-summary.json").read_text())["attempts"][0]

    def assert_closeout_complete(self) -> None:
        """服务释放、日志、单元关闭、记录、摘要与本地网页关闭都做过（任一失败均记在 closeout，不跳过其余）。"""
        record = self.record()
        self.assertTrue(record["release"]["released"])
        self.assertTrue((self.fx.out / "play/ops-summary.json").is_file())
        self.assertTrue(any("-O" in a and "exit" in a and str(a[a.index("-S") + 1]).endswith("cm-3") for a in self.fx.calls("ssh")))
        with self.assertRaises(OSError):
            http_get(self.port, "/api/state")
        closing = [json.loads(l) for l in (self.fx.out / "play" / web.OPS_LOG).read_text().splitlines()]
        tail = [r for r in closing if r["kind"] == "closeout_tail"][-1]["closeout"]
        self.assertEqual({k: tail[k] for k in ("service_release", "unit_close", "record", "web_shutdown")},
                         dict.fromkeys(("service_release", "unit_close", "record", "web_shutdown"), "done"))
        self.assertEqual(tail["summary"], "rc=0")

    # C6-3：S-LOAD（收尾才发现）也保留同一份完整尝试记录，摘要逐步对上原回执
    def test_s_load_keeps_full_attempt_record_and_summary_maps_accepted_requests(self) -> None:
        self.fx.cfg["session"] = {"model_loads": 2}
        self.fx.save()
        rc, out = self.play(self.standard)
        self.assertEqual(rc, 3, out)
        self.assertIn("STOP S-LOAD model_loads=[2]", out)
        attempt = self.record()["attempts"][0]
        steps = {s["step_id"]: (s["status"], bool(s["request_id"])) for s in attempt["steps"]}
        self.assertEqual(steps, {"P1-1": ("NO_CANDIDATE", True), "P1-2": ("SKIPPED_NOT_IN_VIEW", False), "P1-3": ("NO_CANDIDATE", True),
                                 "P1-4": ("NO_CANDIDATE", True), "P1-5": ("DONE", True)})
        self.assertEqual((attempt["session_rc"], attempt["terminal_reason"], attempt["model_loads"], attempt["stop"]["code"]),
                         (0, "operator_stop", [2], "S-LOAD"))
        self.assertIn("frames", " ".join(attempt["archive"]["moved"]))
        self.assertTrue(attempt["unity_frames_quiet"])
        summary = self.summary_attempt()
        pva = summary["plan_vs_actual"]
        self.assertEqual((pva["designate_sent"], pva["designate_skipped_not_in_view"], pva["designate_not_executed"],
                          pva["designate_record_unknown"]), (3, 1, 0, 0))
        self.assertEqual(summary["consistency_issues"], [])
        self.assertTrue(all(r["session_receipt"] != "MISSING" for r in summary["request_timeline"]))
        self.assertEqual(summary["stop"]["code"], "S-LOAD")
        self.assert_closeout_complete()

    # C6-3：会话 TERMINAL(backend_fatal) 终止失败：已受理 ask 与原因保留，其余确实未执行
    def test_backend_fatal_terminal_keeps_accepted_request_and_reason(self) -> None:
        self.fx.cfg["session"] = {"terminal_after_requests": {"n": 1, "reason": "backend_fatal"}}
        self.fx.save()
        rc, out = self.play(self.standard)
        self.assertEqual(rc, 3, out)
        self.assertIn("STOP S-BACKEND session TERMINAL(backend_fatal)", out)
        attempt = self.record()["attempts"][0]
        first, *rest = attempt["steps"]
        self.assertEqual((first["status"], bool(first["request_id"])), ("NO_CANDIDATE", True))
        self.assertIn("backend_fatal", first["reason"])
        self.assertEqual({s["status"] for s in rest}, {"NOT_EXECUTED"})
        self.assertEqual((attempt["terminal_reason"], attempt["session_rc"]), ("backend_fatal", 0))
        self.assertTrue(attempt["archive"]["moved"])
        summary = self.summary_attempt()
        self.assertEqual((summary["plan_vs_actual"]["designate_sent"], summary["plan_vs_actual"]["designate_not_executed"]), (1, 3))
        self.assertEqual(summary["consistency_issues"], [])
        self.assertEqual(len(cli_calls(self.fx, "ask")), 1)
        self.assert_closeout_complete()

    # C6-2：会话挂起越过工具截止 → 封住、原 stop 一次（结果未知不重发）、等会话、照记仍在运行、不移动归档、完整收尾
    def test_hung_session_past_wall_gets_one_stop_and_full_safe_closeout(self) -> None:
        ops.LIMITS["play_wall_s"] = 4.0
        ops.SESSION_STOP_WAIT_S = 1.0
        ops.UNITY_STOP_CLOSEOUT_WAIT_S = 3.0
        self.fx.cfg["session"] = {"stop_mode": "ignore", "exit_after_ignore_s": 9.0}
        self.fx.save()

        def idle(state: dict[str, Any]) -> None:
            if cli_calls(self.fx, "stop"):
                self.stop_frames.set()  # 本人看到中止后停 Play

        rc, out = self.play(idle, frames_max_s=30.0)
        self.assertEqual(rc, 3, out)
        self.assertIn("STOP S-WALL loop2-p1 会话在工具截止", out)
        self.assertEqual(len(cli_calls(self.fx, "stop")), 1)
        self.assertEqual(cli_calls(self.fx, "ask"), [])
        attempt = self.record()["attempts"][0]
        self.assertTrue(attempt["session_process"].startswith("still_running_after_stop_wait"))
        self.assertTrue(attempt["closeout_stop"]["unknown"])
        self.assertIn("会话进程仍在运行", attempt["archive"]["skipped"])
        self.assertEqual([s["code"] for s in attempt["stops_all"]][:2], ["S-WALL", "S-WALL"])
        self.assertEqual({s["status"] for s in attempt["steps"]}, {"NOT_EXECUTED"})
        self.assertTrue(all("封住" in s["reason"] for s in attempt["steps"]))
        self.assertLessEqual(attempt["tool_deadline_unix_s"] - attempt["play_wait_started_unix_s"], 4.0)
        self.assertTrue((self.fx.repo / "runtime/frames").is_dir())  # 未确认可移动：原样留在 runtime/
        self.assert_closeout_complete()

    # C6-2：会话正常结束但 Unity 仍出帧越过工具截止（等待 Play 不延长 420 s）→ S-WALL、不移动帧环、完整收尾
    def test_unity_still_publishing_after_deadline_is_s_wall_without_archive(self) -> None:
        ops.LIMITS["play_wall_s"] = 6.0
        ops.UNITY_STOP_CLOSEOUT_WAIT_S = 1.5

        def skip_all(state: dict[str, Any]) -> None:
            current = (state.get("plan") or {}).get("current") or {}
            if current.get("phase") == "await_send" and not state.get("blocked"):
                self.client.click(state, "skip")

        rc, out = self.play(skip_all, frames_max_s=20.0)
        self.assertEqual(rc, 3, out)
        self.assertIn("STOP S-WALL loop2-p1 出帧在工具截止", out)
        attempt = self.record()["attempts"][0]
        self.assertEqual([s["status"] for s in attempt["steps"]], ["SKIPPED_NOT_IN_VIEW"] * 4 + ["DONE"])
        self.assertEqual((attempt["terminal_reason"], attempt["unity_frames_quiet"]), ("operator_stop", False))
        self.assertIn("Unity 停止未确认", attempt["archive"]["skipped"])
        self.assertTrue((self.fx.repo / "runtime/frames").is_dir())
        self.assertFalse((self.fx.out / "play/loop2-p1/unity-runtime").exists())
        self.assertEqual(len(cli_calls(self.fx, "stop")), 1)
        self.assertEqual(self.summary_attempt()["plan_vs_actual"]["designate_skipped_not_in_view"], 4)
        self.assert_closeout_complete()

    # C6-1/C6-2：活动 Play 中 Ctrl-C → 立即封住 runner 与网页业务、原 stop 一次、等会话、归档、摘要/网页关闭照做
    def test_ctrl_c_during_play_seals_business_and_still_closes_out(self) -> None:
        import _thread

        fired = threading.Event()

        def policy(state: dict[str, Any]) -> None:
            current = (state.get("plan") or {}).get("current") or {}
            if state["session"]["state"]["state"] == "TERMINAL":
                self.stop_frames.set()
            if not fired.is_set():
                if current.get("phase") == "await_send" and current.get("step_id") == "P1-1":
                    self.client.click(state, "send")
                elif current.get("step_id") == "P1-2":
                    fired.set()
                    _thread.interrupt_main()
            elif state.get("blocked") and len(self.refusals) < 2:
                self.refusals.append(self.client.click(state, "send", step_id="P1-2"))
                self.refusals.append(self.client.click(state, "skip", step_id="P1-2"))

        rc, out = self.play(policy)
        self.assertEqual(rc, 3, out)
        self.assertIn("STOP UNKNOWN operator Ctrl-C", out)
        self.assertEqual(len(self.refusals), 2)
        for reply in self.refusals:
            self.assertFalse(reply["ok"])
            self.assertIn("封住", reply["message"])
        self.assertEqual((len(cli_calls(self.fx, "ask")), len(cli_calls(self.fx, "stop"))), (1, 1))
        attempt = self.record()["attempts"][0]
        self.assertEqual(attempt["stop"]["code"], "UNKNOWN")
        statuses = [(s["status"], bool(s["request_id"])) for s in attempt["steps"]]
        self.assertEqual(statuses, [("NO_CANDIDATE", True)] + [("NOT_EXECUTED", False)] * 4)
        self.assertTrue(all("封住" in s["reason"] for s in attempt["steps"][1:]))
        self.assertEqual(attempt["terminal_reason"], "operator_stop")
        self.assertTrue(attempt["archive"]["moved"])
        pva = self.summary_attempt()["plan_vs_actual"]
        self.assertEqual((pva["designate_sent"], pva["designate_not_executed"]), (1, 3))
        web_log = [json.loads(l) for l in (self.fx.out / "play" / web.OPS_LOG).read_text().splitlines()]
        self.assertTrue(any(r["kind"] == "sealed" for r in web_log))
        self.assert_closeout_complete()

    # C6-2：收尾中一步失败（日志回传前控制套接字失效）不跳过单元关闭、记录、摘要与网页关闭
    def test_partial_closeout_failure_does_not_skip_remaining_safe_steps(self) -> None:
        marker = Path(self.tmp.name) / "socket-lost"
        self.fx.cfg["check_fail_marker"] = str(marker)
        self.fx.save()

        def policy(state: dict[str, Any]) -> None:
            self.standard(state)
            if state["session"]["state"]["state"] == "TERMINAL":
                marker.touch()

        rc, out = self.play(policy)
        self.assertEqual(rc, 3, out)
        self.assertIn("STOP S-PRECHECK S-SSH control_socket_unavailable before logs-3", out)
        record = self.record()
        self.assertIn("control_socket_unavailable before logs-3", record["closeout"]["logs"])
        self.assertEqual(record["stop"]["code"], "S-PRECHECK")
        self.assertEqual(record["attempts"][0]["stop"], None)
        self.assertEqual(len(record["attempts"][0]["steps"]), 5)
        self.assert_closeout_complete()


    # OPSR1返工 R1-3(a)：收尾等待本人停 Play 时 Ctrl-C → 记 UNKNOWN（不被吞）、归档跳过记 UNKNOWN、不开下一剧本、rc 3
    def test_r1_3_ctrl_c_in_closeout_unity_wait_is_unknown_and_stops_next_playbook(self) -> None:
        self.patch_ops("PLAY_START_WAIT_S", 3.0)

        def interrupted(*args: Any, **kwargs: Any) -> Any:
            self.stop_frames.set()
            raise KeyboardInterrupt

        self.patch_ops("wait_unity_stopped", interrupted)
        rc, out = self.play(self.standard, playbooks=("P1", "P2"))
        self.assertEqual(rc, 3, out)
        self.assertIn("STOP UNKNOWN operator Ctrl-C", out)
        first, second = self.record()["attempts"]
        self.assertEqual(first["stop"]["code"], "UNKNOWN")
        self.assertIn("interrupted", first["closeout"]["unity"])
        self.assertIn("UNKNOWN", first["archive"]["skipped"])
        self.assertIn("UNKNOWN", [s["code"] for s in first["stops_all"]])
        self.assertFalse(second["attempted"])
        self.assertFalse((self.fx.out / "play/sessions/loop2-p2").exists())
        self.assertTrue((self.fx.repo / "runtime/frames").is_dir())  # 未证明可移动：原样留在 runtime/

    # OPSR1返工 R1-3(b)：归档改名抛 OSError（跨设备/权限）→ UNKNOWN 停依赖、不开下一剧本、rc 3
    def test_r1_3_archive_oserror_is_unknown_and_stops_next_playbook(self) -> None:
        self.patch_ops("PLAY_START_WAIT_S", 3.0)

        def broken(*args: Any, **kwargs: Any) -> Any:
            raise OSError(18, "Invalid cross-device link")

        self.patch_ops("archive_attempt", broken)
        rc, out = self.play(self.standard, playbooks=("P1", "P2"))
        self.assertEqual(rc, 3, out)
        self.assertIn("STOP UNKNOWN", out)
        first, second = self.record()["attempts"]
        self.assertEqual(first["stop"]["code"], "UNKNOWN")
        self.assertIn("OSError", first["closeout"]["archive"])
        self.assertIn("UNKNOWN", first["archive"]["skipped"])
        self.assertFalse(second["attempted"])
        self.assertFalse((self.fx.out / "play/sessions/loop2-p2").exists())

    # OPSR1返工 R1-3(c)：原评分 CLI 非 0 → 摘要非 0 退出 → play 置失败、rc 3（不打印正常收尾）
    def test_r1_3_score_nonzero_rc_fails_play(self) -> None:
        self.fx.cfg["score_rc"] = 4
        self.fx.save()
        rc, out = self.play(self.standard)
        self.assertEqual(rc, 3, out)
        self.assertIn("STOP UNKNOWN", out)
        self.assertIn("summarize_ops rc=3", out)
        summary = json.loads((self.fx.out / "play/ops-summary.json").read_text())
        self.assertEqual(summary["attempts"][0]["score_call"]["rc"], 4)
        self.assertEqual([f["code"] for f in summary["failures"]], ["UNKNOWN"])
        closing = [json.loads(l) for l in (self.fx.out / "play" / web.OPS_LOG).read_text().splitlines()]
        tail = [r for r in closing if r["kind"] == "closeout_tail"][-1]
        self.assertEqual((tail["closeout"]["summary"], tail["stop"]["code"]), ("rc=3", "UNKNOWN"))

    def patch_ops(self, name: str, value: Any) -> None:
        saved = getattr(ops, name)
        setattr(ops, name, value)
        self.addCleanup(setattr, ops, name, saved)


# --- 诊断模式（IR-OPS-5）：生产入口 + 本地替身 ---------------------------------------------------------


class DiagTestBase(RepoTestBase):
    #: 「诊断绑定方案答复」BIND-1 冻结值（测试独立写出合同字面，再与 `ops.DIAG_ENTRIES` 静态比对）；
    #: C10-1 纠正：定义收在允许类闭集内（类属性），各允许类经 `self.` 引用，字面值不变。
    RETRY1 = "P1-ENG-LOOP-002:DIAG:RETRY:1"
    RETRY1_TITLE = "用户按推荐签发新全套 42979c14:SUB:1 与新诊断 DIAG:RETRY:1"
    SUB3 = "P1-ENG-LOOP-002:9bac8fd0:SUB:3"

    #: DIAG-CONTROL-1：True 时把执行检出放进加长目录，使旧式「诊断根/ssh/cm-d1」带 OpenSSH 后缀超过本机上限（同生产 120 B）。
    long_root = False

    def setUp(self) -> None:
        if self.long_root:
            self.tmp = tempfile.TemporaryDirectory()
            self.addCleanup(self.tmp.cleanup)
            root = Path(self.tmp.name)
            pad = max(1, 125 - len(os.fsencode(str(root / "exec" / ops.DIAG_AIR_PARENT / "20261008T155230Z" / "ssh" / "cm-d1"))))
            root = root / ("L" * pad)
            root.mkdir()
            self.fx = RepoFixture(root)
        else:
            super().setUp()
        # 短私有 ControlPath 父目录：独立临时目录（测试结束连同残留一起清掉）；假 ssh 真实 bind 本机 AF_UNIX
        self.control_parent = tempfile.TemporaryDirectory(prefix="c", dir=tempfile.gettempdir())
        self.addCleanup(self.control_parent.cleanup)
        saved_parent = ops.DIAG_CONTROL_PARENT if hasattr(ops, "DIAG_CONTROL_PARENT") else None
        if hasattr(ops, "DIAG_CONTROL_PARENT"):
            ops.DIAG_CONTROL_PARENT = self.control_parent.name
            self.addCleanup(setattr, ops, "DIAG_CONTROL_PARENT", saved_parent)
        self.fx.cfg["real_control_socket"] = True
        # BIND-4 放行行（接受程序写入的格式）与 BIND-3 账本唯一条目（标题片段 + 正文反引号完整 id）；先提案后账本两笔提交
        self.fx.commit_docs(ops.PROPOSAL, f"\n- `diag_release: {self.RETRY1} {self.fx.passed}`\n")
        self.fx.commit_docs("docs/authorizations.md", f"\n## x — {self.RETRY1_TITLE}\n- `{self.RETRY1}`\n")
        receipt = build_k_receipt(hz=5.0, retained_frame_count=1500, p95_s=2.6, host="jetson", backend="http", model_form="c2-merged")
        self.fx.cfg.update(k_receipt=receipt.payload(), derive_bc=DERIVE, diag={},
                           status={"model_identity": {k: "x" for k in bridge.LLAMA_IDENTITY_KEYS}, "serve_code_sha256": "d" * 64,
                                   "machine": "jetson"})
        self.fx.save()
        self.parent = self.fx.repo / ops.DIAG_AIR_PARENT
        old = (ops.UNITY_STOP_QUIET_S, ops.DIAG_UNITY_STOP_WAIT_S)
        ops.UNITY_STOP_QUIET_S, ops.DIAG_UNITY_STOP_WAIT_S = 0.5, 5.0
        self.addCleanup(lambda: (setattr(ops, "UNITY_STOP_QUIET_S", old[0]), setattr(ops, "DIAG_UNITY_STOP_WAIT_S", old[1])))

    def diag(self, *extra: str) -> tuple[int, str]:
        time.sleep(1.05)  # 诊断根以秒级 UTC 命名，必须新建
        return self.fx.main("--mode", "diagnostic", "diag", "--request-id", self.RETRY1, "--playbook", "P1",
                            "--p2-object", "red_car", *extra)

    def ledger(self) -> dict[str, Any]:
        roots = sorted(self.parent.glob("*/ops-diagnostic-ledger.json"))
        return json.loads(roots[-1].read_text())


class DiagTests(DiagTestBase):
    def test_refused_without_acceptance_release_line_and_consumes_nothing(self) -> None:
        git(self.fx.docwt, "revert", "--no-edit", "HEAD~1")  # 撤掉 diag_release 行
        git(self.fx.docwt, "push", "origin", "HEAD:main")
        rc, out = self.diag()
        self.assertEqual(rc, 3)
        self.assertIn("DIAG_REFUSED", out)
        self.assertIn("diag_release_missing", out)
        self.assertEqual(self.fx.calls("ssh"), [])
        self.assertFalse(self.ledger()["consumed"])

    def test_refused_when_release_value_is_not_the_passed_candidate(self) -> None:
        git(self.fx.docwt, "revert", "--no-edit", "HEAD~1")  # 撤掉合法行，换成另一个 40 位 sha（发布引用本身）
        git(self.fx.docwt, "push", "origin", "HEAD:main")
        self.fx.commit_docs(ops.PROPOSAL, f"\n- `diag_release: {self.RETRY1} {self.fx.rel}`\ndiag_release: {self.RETRY1} {self.fx.passed.upper()}\n")
        rc, out = self.diag()
        self.assertEqual(rc, 3)
        self.assertIn("diag_release_mismatch", out)
        self.assertEqual(self.fx.calls("ssh"), [])
        self.assertFalse(self.ledger()["consumed"])

    def test_refused_when_proposal_unreadable_at_release_ref(self) -> None:
        git(self.fx.docwt, "rm", "-q", ops.PROPOSAL)
        git(self.fx.docwt, "commit", "-m", "drop proposal")
        git(self.fx.docwt, "push", "origin", "HEAD:main")
        rc, out = self.diag()
        self.assertEqual(rc, 3)
        self.assertIn("diag_release_unreadable", out)
        self.assertEqual(self.fx.calls("ssh"), [])
        self.assertFalse(self.ledger()["consumed"])

    def test_contract_format_examples_are_not_release_lines(self) -> None:
        examples = [line for line in (REPO / ops.PROPOSAL).read_text(encoding="utf-8").splitlines()
                    if "sub3_release: <" in line]
        self.assertTrue(examples)
        self.assertEqual([line for line in examples if ops.DIAG_RELEASE_LINE.match(line)], [])

    def test_refused_when_ledger_entry_missing(self) -> None:
        target = self.fx.docwt / "docs/authorizations.md"
        target.write_text(target.read_text().replace(self.RETRY1, "x"), encoding="utf-8")
        git(self.fx.docwt, "commit", "-am", "drop")
        git(self.fx.docwt, "push", "origin", "HEAD:main")
        rc, out = self.diag()
        self.assertEqual(rc, 3)
        self.assertIn(f"ledger_entry_missing {self.RETRY1}", out)
        self.assertEqual(self.fx.calls("ssh"), [])

    def test_service_refusal_counts_the_single_start_and_never_plays(self) -> None:
        (self.fx.repo / "runtime/scenario_config.json").write_text("{\"held\": 1}\n", encoding="utf-8")
        self.fx.cfg["diag"] = {"serve_fault": True}
        self.fx.save()
        rc, out = self.diag()
        self.assertEqual(rc, 3, out)
        data = self.ledger()
        self.assertEqual((data["used"]["master_connections"], data["used"]["serve_starts"], data["used"]["plays"]), (2, 1, 0))
        self.assertEqual(data["serve"]["gguf_loads"], 0)
        self.assertTrue(any("service exited before ready" in f["detail"] for f in data["faults"]))
        self.assertEqual(data["stages_not_executed"], ["start_service", "check_status", "make_receipt", "play"])
        self.assertTrue(data["serve"]["release"]["released"])
        typed = [c[0] for c in self.fx.calls("serve-typed")]
        self.assertEqual(sum("serve-diag.sh" in t for t in typed), 1)
        self.assertFalse(any(" 2;" in t or " 3;" in t for t in typed if "serve-diag.sh" in t))
        self.assertEqual(sum(1 for a in self.fx.calls("python") if a[:3] == ["-m", "tools.language_latency", "measure"]), 0)
        self.assertEqual((self.fx.repo / "runtime/scenario_config.json").read_text(), "{\"held\": 1}\n")  # 归位
        self.assertFalse((self.fx.out / "ops-ledger.json").exists())  # 不写正式账
        before = len(self.fx.calls("ssh"))
        rc, out = self.diag()  # 结束或失败即用尽：不续试
        self.assertEqual(rc, 3)
        self.assertIn(f"request_consumed {self.RETRY1} 已于", out)
        self.assertEqual(len(self.fx.calls("ssh")), before)

    def test_status_with_formal_budget_is_fault_and_no_receipt(self) -> None:
        self.fx.cfg["status"]["http_budget"] = {"batch": 2}
        self.fx.save()
        rc, out = self.diag()
        self.assertEqual(rc, 3, out)
        data = self.ledger()
        self.assertTrue(any("status_check" in f["detail"] for f in data["faults"]))
        self.assertEqual(data["measure"]["runs"], 0)
        self.assertEqual(len(self.fx.calls("curl")), 1)
        self.assertTrue(data["serve"]["release"]["released"])

    def test_measure_failure_never_runs_k_receipt_or_play(self) -> None:
        self.fx.cfg["measure_rc"] = 7
        self.fx.save()
        rc, out = self.diag()
        self.assertEqual(rc, 3, out)
        data = self.ledger()
        self.assertEqual((data["measure"]["runs"], data["k_receipt"]["runs"], data["used"]["plays"]), (1, 0, 0))

    def test_existing_board_root_is_fault_before_code_sync(self) -> None:
        self.fx.cfg["diag"] = {"root_exists": True}
        self.fx.save()
        rc, out = self.diag()
        self.assertEqual(rc, 3, out)
        data = self.ledger()
        self.assertEqual(data["used"]["master_connections"], 1)
        self.assertTrue(any("board_check" in f["detail"] for f in data["faults"]))
        tally = (sorted(self.parent.glob("*/ssh/d1.tsv"))[-1]).read_text()
        self.assertNotIn("root-code", tally)

    def test_end_to_end_single_play_web_closeout_and_summary(self) -> None:
        runtime = self.fx.repo / "runtime"
        (runtime / "scenario_config.json").write_text("{\"held\": 1}\n", encoding="utf-8")
        port = free_port()
        stop_frames = threading.Event()
        clicks: list[str] = []

        def frames() -> None:
            deadline = time.time() + 90
            while not list(self.parent.glob("*/receipt/jetson-k-receipt.json")) and time.time() < deadline:
                time.sleep(0.05)
            publisher = FixtureFramePublisher(runtime, scenario_id="deterministic-loop-untethered")
            while not stop_frames.is_set():
                publisher.publish(b"\xff\xd8\xff\xe0x")
                time.sleep(0.1)

        def operator() -> None:
            nonce = None
            deadline = time.time() + 90
            while time.time() < deadline:
                try:
                    if nonce is None:
                        page = http_get(port, "/").decode()
                        nonce = page.split('const NONCE="', 1)[1].split('"', 1)[0]
                    state = json.loads(http_get(port, "/api/state"))
                except (OSError, IndexError, ValueError):
                    time.sleep(0.1)
                    continue
                self.assertEqual(state.get("mode_banner"), ops.DIAG_BANNER)
                session = state.get("session") or {}
                if state.get("summary"):
                    http_post(port, nonce, {"button": "feedback", "view": {"attempt": session.get("session_id")}, "label": "FAIL", "text": "替身"})
                    return
                current = (state.get("plan") or {}).get("current") or {}
                if session.get("state") and current.get("phase") == "await_send" and not state.get("blocked"):
                    st = session["state"]
                    button = "skip" if current["step_id"] == "P1-2" else "send"
                    view = {"session_id": session["session_id"], "state": st["state"], "reason": st["reason"], "epoch": st["epoch"],
                            "step_id": current["step_id"], "plan_sha256": state["plan"]["plan_sha256"]}
                    if http_post(port, nonce, {"button": button, "view": view}).get("ok"):
                        clicks.append(f"{button}:{current['step_id']}")
                if (session.get("state") or {}).get("state") == "TERMINAL":
                    stop_frames.set()
                time.sleep(0.15)

        threading.Thread(target=frames, daemon=True).start()
        worker = threading.Thread(target=operator, daemon=True)
        worker.start()
        try:
            rc, out = self.diag("--port", str(port), "--feedback-wait-s", "20")
        finally:
            stop_frames.set()
            worker.join(timeout=10)
        self.assertEqual(rc, 0, out)
        self.assertIn("DIAG_DONE", out)
        self.assertEqual(clicks, ["send:P1-1", "skip:P1-2", "send:P1-3", "send:P1-4"])
        root = sorted(self.parent.glob("*/ops-diagnostic-ledger.json"))[-1].parent.resolve()
        data = self.ledger()
        self.assertEqual(data["used"], {"master_connections": 2, "serve_starts": 1, "fault_restarts": 0, "plays": 1, "sessions": 1,
                                        "measure_runs": 1, "k_receipt_runs": 1})
        self.assertEqual((data["serve"]["gguf_loads"], data["serve"]["sh_rc"], data["serve"]["release"]["released"]), (1, 0, True))
        self.assertEqual(data["play"]["terminal_reason"], "operator_stop")
        self.assertIn("UNKNOWN", data["play"]["button_start_unix_s"])
        self.assertEqual(data["yolo_loads"], 1)
        self.assertIsNone(data["stop"])
        self.assertTrue(data["disk"]["board"] and data["disk"]["air"])
        # 两条主连接，各自通道闭集；只启动编号 1；不碰正式根/预算旗标
        ssh = self.fx.calls("ssh")
        self.assertEqual(sum(1 for a in ssh if "-fN" in a), 2)
        remotes = " ".join(a[-1] for a in ssh)
        self.assertNotIn("/home/jetson/eng-loop2/", remotes.replace("/home/jetson/eng-loop2-diag", ""))
        typed = [c[0] for c in self.fx.calls("serve-typed")]
        self.assertTrue(any(t.endswith("/run/serve-diag.sh 1; echo \"serve_diag_sh_rc=$?\"") for t in typed))
        self.assertFalse(any("--http-ledger" in t or "--non-inference-reserve" in t for t in typed))
        self.assertIn("echo DIAG_CLOSEOUT_DONE", typed)
        # 会话：--diagnostic + 独立根；不写 runtime/runs；只 measure/k-receipt 各一次；/status 恰一次
        run = [a for a in self.fx.calls("python") if a[:3] == ["-m", "controller.language_loop", "run"]]
        self.assertEqual(len(run), 1)
        argv = run[0]
        self.assertIn("--diagnostic", argv)
        self.assertTrue(argv[argv.index("--session-id") + 1].startswith("diag-loop2-"))
        self.assertTrue(argv[argv.index("--session-root") + 1].startswith(str(root)))
        self.assertTrue(argv[argv.index("--diagnostics-root") + 1].startswith(str(root)))
        self.assertFalse((runtime / "runs").exists())
        self.assertEqual(len(self.fx.calls("curl")), 1)
        # 收尾：帧环/真值只移入本次段目录，布局覆盖进 hold，开工前残留归位；正式账/正式根不写
        sid = argv[argv.index("--session-id") + 1]
        self.assertTrue((root / "play" / sid / "frames").is_dir())
        self.assertFalse((runtime / "frames").exists())
        self.assertTrue((root / "hold/overlay-diag.json").is_file())
        self.assertEqual((runtime / "scenario_config.json").read_text(), "{\"held\": 1}\n")
        self.assertFalse((self.fx.out / "ops-ledger.json").exists())
        # 摘要：独立进程、诊断模式、不评分；本人反馈分列
        summary = json.loads((root / "play/ops-summary.json").read_text())
        self.assertEqual(summary["mode"], "diagnostic")
        self.assertFalse(summary["attempts"][0]["score_call"]["called"])
        self.assertEqual(summary["attempts"][0]["plan_vs_actual"]["designate_skipped_not_in_view"], 1)
        self.assertFalse(any(a[:3] == ["-m", "tools.eng_loop2.analyze_play", "score"] for a in self.fx.calls("python")))
        self.assertIn('"FAIL"', (root / "play/feedback.jsonl").read_text())
        for name in ("ops-events.jsonl", "NOTES.md", "board/serve-channel-1.log", "board/board-logs.tar", "play/ops-web.jsonl"):
            self.assertTrue((root / name).exists(), name)
        # BIND-2：新粗账 / NOTES / 事件 / play-record 均用新 id，粗账记完整 entry_binding
        self.assertEqual(data["request_id"], self.RETRY1)
        self.assertEqual(json.loads((root / "play/play-record.json").read_text())["request_id"], self.RETRY1)
        self.assertIn(f"request_id {self.RETRY1}", (root / "NOTES.md").read_text())
        events = [json.loads(line) for line in (root / "ops-events.jsonl").read_text().splitlines()]
        self.assertEqual([e["request_id"] for e in events if e["kind"] == "diag_start"], [self.RETRY1])
        self.assertEqual(data["entry_binding"]["release_value"], self.fx.passed)
        # 一次性：再次启动即拒（结束或失败即用尽）
        before = len(self.fx.calls("ssh"))
        rc, out = self.diag()
        self.assertEqual((rc, len(self.fx.calls("ssh"))), (3, before))
        self.assertIn(f"request_consumed {self.RETRY1} 已于", out)

    # --- C6-1：活动 Play 中 STOP/中断后不可逆封住业务（生产入口 + 替身；TERMINAL 迟到/stop 结果未知） ---

    def run_sealed_diag(self, policy) -> tuple[int, str, list[dict[str, Any]]]:
        port = free_port()
        client = OperatorClient(port)
        stop_frames = threading.Event()
        runtime = self.fx.repo / "runtime"

        def frames() -> None:
            deadline = time.time() + 90
            while not list(self.parent.glob("*/receipt/jetson-k-receipt.json")) and time.time() < deadline:
                time.sleep(0.05)
            publisher = FixtureFramePublisher(runtime, scenario_id="deterministic-loop-untethered")
            while not stop_frames.is_set() and time.time() < deadline:
                publisher.publish(b"\xff\xd8\xff\xe0x")
                time.sleep(0.1)

        refusals: list[dict[str, Any]] = []

        def operator() -> None:
            deadline = time.time() + 90
            while time.time() < deadline:
                try:
                    state = client.state()
                except (OSError, IndexError, ValueError):
                    time.sleep(0.1)
                    continue
                if state.get("summary"):
                    return
                session = state.get("session") or {}
                if session.get("state"):
                    if session["state"]["state"] == "TERMINAL" or cli_calls(self.fx, "stop"):
                        stop_frames.set()
                    policy(client, state, refusals)
                time.sleep(0.15)

        threading.Thread(target=frames, daemon=True).start()
        worker = threading.Thread(target=operator, daemon=True)
        worker.start()
        try:
            rc, out = self.diag("--port", str(port), "--feedback-wait-s", "1")
        finally:
            stop_frames.set()
            worker.join(timeout=15)
            for pid_file in self.parent.glob("*/play/sessions/*.fake-pid"):
                wait_pid_gone(pid_file)
        return rc, out, refusals

    def test_stop1_during_play_seals_runner_and_web_until_late_terminal(self) -> None:
        saved = ops.DIAG_LIMITS["air_bytes"]
        self.addCleanup(ops.DIAG_LIMITS.__setitem__, "air_bytes", saved)
        ops.DIAG_LIMITS["air_bytes"] = 1  # Play 中首个 Air 轮询即达 90% → STOP1
        self.fx.cfg["session"] = {"stop_mode": "late_terminal", "terminal_delay_s": 3.0}
        self.fx.save()

        def policy(client: OperatorClient, state: dict[str, Any], refusals: list[dict[str, Any]]) -> None:
            # stop 已发、TERMINAL 尚未到：本人此时再点发送/跳过都必须被拒（不能续行业务）
            if cli_calls(self.fx, "stop") and state["session"]["state"]["state"] != "TERMINAL" and len(refusals) < 2:
                refusals.append(client.click(state, "send", step_id="P1-1"))
                refusals.append(client.click(state, "skip", step_id="P1-1"))

        rc, out, refusals = self.run_sealed_diag(policy)
        self.assertEqual(rc, 3, out)
        self.assertEqual(len(refusals), 2)
        for reply in refusals:
            self.assertFalse(reply["ok"])
            self.assertIn("封住", reply["message"])
        self.assertEqual((len(cli_calls(self.fx, "ask")), len(cli_calls(self.fx, "stop"))), (0, 1))
        data = self.ledger()
        self.assertEqual(data["stop"]["category"], 1)
        self.assertTrue(data["play"]["halted"]["reason"].startswith("STOP1"))
        self.assertEqual(data["play"]["terminal_reason"], "operator_stop")  # 迟到的 TERMINAL 照记，不恢复任何动作
        self.assertEqual({s["status"] for s in data["play"]["steps"]}, {"NOT_EXECUTED"})
        root = sorted(self.parent.glob("*/ops-diagnostic-ledger.json"))[-1].parent
        web_log = [json.loads(l) for l in (root / "play" / web.OPS_LOG).read_text().splitlines()]
        self.assertTrue(any(r["kind"] == "sealed" for r in web_log))
        self.assertEqual(json.loads((root / "play/ops-summary.json").read_text())["attempts"][0]["plan_vs_actual"]["designate_sent"], 0)

    def test_ctrl_c_during_play_with_unknown_stop_stays_sealed_and_never_resends(self) -> None:
        import _thread

        self.fx.cfg["session"] = {"stop_mode": "ignore", "exit_after_ignore_s": 2.0}
        self.fx.save()
        fired = threading.Event()

        def policy(client: OperatorClient, state: dict[str, Any], refusals: list[dict[str, Any]]) -> None:
            current = (state.get("plan") or {}).get("current") or {}
            if not fired.is_set():
                if current.get("phase") == "await_send" and current.get("step_id") == "P1-1":
                    client.click(state, "send")
                elif current.get("step_id") == "P1-2":
                    fired.set()
                    _thread.interrupt_main()
            elif cli_calls(self.fx, "stop") and len(refusals) < 2:
                refusals.append(client.click(state, "send", step_id="P1-2"))
                refusals.append(client.click(state, "skip", step_id="P1-2"))

        rc, out, refusals = self.run_sealed_diag(policy)
        self.assertEqual(rc, 3, out)
        self.assertEqual(len(refusals), 2)
        for reply in refusals:
            self.assertFalse(reply["ok"])
            self.assertIn("封住", reply["message"])
        self.assertEqual((len(cli_calls(self.fx, "ask")), len(cli_calls(self.fx, "stop"))), (1, 1))  # 结果未知不重发 stop
        data = self.ledger()
        self.assertEqual(data["stop"]["category"], 4)
        self.assertTrue(any("result unknown" in u["detail"] for u in data["unknown"]))
        self.assertIsNone(data["play"]["terminal_reason"])
        steps = [(s["status"], bool(s["request_id"])) for s in data["play"]["steps"]]
        self.assertEqual(steps, [("NO_CANDIDATE", True)] + [("NOT_EXECUTED", False)] * 4)



def _socket_capacity() -> int:
    return getattr(ops, "UNIX_SOCKET_PATH_CAPACITY", 108 if sys.platform.startswith("linux") else 104)


def _bind_probe(path: str) -> None:
    """本机 AF_UNIX 实际 bind/关闭（OpenSSH 临时名 = 路径 + "." + 16 字符）；路径过长即 OSError。"""
    probe = path + "." + "q" * 16
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(probe)
    finally:
        listener.close()
        if os.path.lexists(probe):
            os.unlink(probe)


class DiagBindingTests(DiagTestBase):
    """「诊断绑定方案答复」BIND-1…6（AC-10 修订 9；停点 OpsDiagBindK1K2）：条目闭表、旧 SUB:3 无条件拒续、坏粗账 fail-closed、
    账本唯一条目与新机读放行行、新 id 身份记录。生产入口 `play_ops.main` + 临时 git/假 ssh；回归粗账由生产 `DiagAccount`
    写盘（`consume()` 置位）后在其字节上定点破坏；放行/账本夹具只在临时文档检出提交，不碰真实账本或放行行。"""

    LABEL = "20260101T000000Z"

    def run_main(self, request_id: str, playbook: str = "P1") -> tuple[int, str]:
        """生产入口一次（stdout+stderr 合并）；未捕获异常不是干净拒启，直接判失败。"""
        from contextlib import redirect_stderr

        err = io.StringIO()
        try:
            with redirect_stderr(err):
                rc, out = self.fx.main("--mode", "diagnostic", "diag", "--request-id", request_id, "--playbook", playbook,
                                       "--p2-object", "red_car")
        except Exception as error:  # noqa: BLE001
            self.fail(f"未捕获异常，不是干净拒启：{type(error).__name__}: {error}")
        return rc, out + err.getvalue()

    def roots(self) -> set[str]:
        return {p.name for p in self.parent.iterdir()} if self.parent.is_dir() else set()

    @staticmethod
    def guard_id() -> str:
        """只桥身份：本工具一次性守账所保护的 id（候选 = 新条目；修前基线工具只有旧 SUB:3 一个 id，经同一生产守账路径）。"""
        return DiagTestBase.RETRY1 if hasattr(ops, "DIAG_ENTRIES") else ops.DIAG_REQUEST_ID

    def production_ledger(self, request_id: str, *, consume: bool = True, label: str | None = None) -> Path:
        """生产 `DiagAccount` 写盘 +（可选）`consume()` 置位；只桥构造参数 request_id（基线构造无该参数、固定写旧 id）。"""
        import inspect

        label = label or self.LABEL
        root = self.parent / label
        root.mkdir(parents=True)
        kwargs = {"request_id": request_id} if "request_id" in inspect.signature(ops.DiagAccount).parameters else {}
        account = ops.DiagAccount(root, label, f"{ops.DIAG_BOARD_PARENT}/{label}", **kwargs)
        if consume:
            account.consume()
        self.assertEqual(json.loads(account.path.read_text())["request_id"], request_id)
        return account.path

    @staticmethod
    def corrupt(path: Path, how: str) -> None:
        """在生产写出的字节上定点破坏（不另造账）。"""
        raw = path.read_bytes()
        if how == "directory":
            path.unlink()
            path.mkdir()
            return
        if how == "truncated":
            data = raw[: len(raw) // 2]
        elif how == "not_utf8":
            data = b"\xff\xfe" + raw
        elif how == "list":
            data = b"[" + raw + b"]"
        elif how == "string":
            data = json.dumps(raw.decode("utf-8")).encode()
        elif how == "number":
            data = b"0\n"
        else:
            document = json.loads(raw)
            key, _, value = how.partition("=")
            if value == "<missing>":
                document.pop(key)
            else:
                document[key] = json.loads(value)
            data = json.dumps(document, ensure_ascii=False).encode()
        path.write_bytes(data)

    def drop_release_line(self) -> None:
        git(self.fx.docwt, "revert", "--no-edit", "HEAD~1")  # 撤掉 setUp 的 diag_release 行（建根后前提拒启，不进 SSH）
        git(self.fx.docwt, "push", "origin", "HEAD:main")
        self.fx.rel = git(self.fx.docwt, "rev-parse", "HEAD")

    def assert_refused_before_root(self, rc: int, out: str, needle: str, before: set[str]) -> None:
        self.assertEqual(rc, 3, out)
        self.assertIn("DIAG_REFUSED", out)
        self.assertIn(needle, out)
        self.assertEqual(self.roots(), before)  # 未建新根、未写新粗账
        self.assertEqual(self.fx.calls("ssh"), [])  # 受限动作 0

    def assert_refused_after_root(self, rc: int, out: str, needle: str) -> dict[str, Any]:
        self.assertEqual(rc, 3, out)
        self.assertIn(needle, out)
        data = self.ledger()
        self.assertFalse(data["consumed"])
        self.assertEqual(set(data["used"].values()), {0})  # 主连接/服务/Play/会话/measure/k-receipt 均 0
        self.assertEqual(self.fx.calls("ssh"), [])
        return data

    # --- BIND-2：一次性守账 fail-closed（修前红：基线经同一生产守账路径吞坏账 / 放过非法 consumed） ---

    def test_unreadable_or_nonobject_ledger_refuses(self) -> None:
        for how in ("truncated", "not_utf8", "list", "string", "number", "directory",
                    "request_id=<missing>", "request_id=123", "request_id=null"):
            with self.subTest(how=how):
                try:
                    path = self.production_ledger(self.guard_id())
                    self.corrupt(path, how)
                    before = self.roots()
                    rc, out = self.run_main(self.guard_id())
                    self.assert_refused_before_root(rc, out, "diag_ledger_unreadable", before)
                finally:
                    shutil.rmtree(self.parent, ignore_errors=True)

    def test_retry1_own_consumed_ledger_refuses(self) -> None:
        """同 id 只有字面 false 未消耗；true 与 "false"/1 原本即拒（保持性），缺键/null/0/空串为本次修复的 fail-open。"""
        for how in ("consumed=true", "consumed=\"false\"", "consumed=1",
                    "consumed=<missing>", "consumed=null", "consumed=0", "consumed=\"\""):
            with self.subTest(how=how):
                try:
                    path = self.production_ledger(self.guard_id())
                    self.corrupt(path, how)
                    before = self.roots()
                    rc, out = self.run_main(self.guard_id())
                    self.assert_refused_before_root(rc, out, "已于", before)
                finally:
                    shutil.rmtree(self.parent, ignore_errors=True)

    def test_literal_false_own_ledger_passes_guard(self) -> None:
        """正向：同 id 字面 false（建根后前提拒启留下的账）不阻断；在放行行前提处拒启（建根后，consumed=false）。"""
        self.production_ledger(self.guard_id(), consume=False)
        self.drop_release_line()
        before = self.roots()
        time.sleep(1.05)
        rc, out = self.run_main(self.guard_id())
        self.assertEqual(rc, 3, out)
        self.assertNotIn("已于", out)
        self.assertNotIn("diag_ledger_unreadable", out)
        self.assertEqual(len(self.roots() - before), 1)
        self.assertFalse(self.ledger()["consumed"])
        self.assertEqual(self.fx.calls("ssh"), [])

    # --- BIND-1/2：条目闭表与建根前拒启 ---

    def test_sub3_refused_as_exhausted_even_without_any_ledger(self) -> None:
        self.assertFalse(self.parent.exists())
        rc, out = self.run_main(self.SUB3)
        self.assert_refused_before_root(rc, out, f"request_exhausted {self.SUB3}", set())
        self.assertFalse(self.parent.exists())
        # 即使存在旧 id 的「未消耗」粗账也无条件拒续（不依赖 outputs/）
        self.production_ledger(self.SUB3, consume=False)
        before = self.roots()
        rc, out = self.run_main(self.SUB3)
        self.assert_refused_before_root(rc, out, "request_exhausted", before)

    def test_unknown_request_id_refused(self) -> None:
        """保持性：基线对非 SUB:3 的 id 原本即建根前拒（`DIAG_REFUSED request_id…`）；新增前缀扩展/大小写/空串子例。"""
        for request_id in ("P1-ENG-LOOP-002:9bac8fd0:SUB:1", f"{self.RETRY1}:WINDOW", self.RETRY1.lower(), f"{self.RETRY1} ", "",
                           "P1-ENG-LOOP-002:42979c14:SUB:1"):
            with self.subTest(request_id=request_id):
                rc, out = self.run_main(request_id)
                self.assert_refused_before_root(rc, out, "DIAG_REFUSED request_id", set())

    def test_retry1_refuses_unsigned_playbooks(self) -> None:
        for playbook in ("P2", "P3"):
            with self.subTest(playbook=playbook):
                rc, out = self.run_main(self.RETRY1, playbook)
                self.assert_refused_before_root(rc, out, f"playbook_not_signed {playbook}", set())

    def test_old_sub3_consumed_ledger_does_not_block_retry1(self) -> None:
        self.production_ledger(self.SUB3, consume=True)  # 本机实有旧账同形：旧 id、consumed=true
        self.drop_release_line()
        time.sleep(1.05)
        rc, out = self.run_main(self.RETRY1)
        data = self.assert_refused_after_root(rc, out, "diag_release_missing")
        self.assertNotIn("已于", out)
        self.assertEqual(data["request_id"], self.RETRY1)
        self.assertEqual(len(self.roots()), 2)
        # 旧粗账原样保留（不删改/不改 id/不移根）
        old = json.loads((self.parent / self.LABEL / "ops-diagnostic-ledger.json").read_text())
        self.assertEqual((old["request_id"], old["consumed"]), (self.SUB3, True))

    # --- BIND-4：新机读放行行 ---

    def test_release_missing_or_only_sub3_line_refuses(self) -> None:
        passed = self.fx.passed
        self.drop_release_line()
        variants = ("", f"- `sub3_release: {passed}`", "- 格式`diag_release: <request_id> <40位小写sha>`",
                    f"diag_release: {self.RETRY1}:WINDOW {passed}", f"diag_release: {self.RETRY1} {passed.upper()}",
                    f"diag_release: {self.RETRY1} {passed[:12]}", f"diag_release: {self.SUB3} {passed}",
                    f"diag_release:{self.RETRY1} {passed}", f"diag_release: {self.RETRY1}{passed}", f"x diag_release: {self.RETRY1} {passed}")
        for text in variants:
            with self.subTest(line=text):
                if text:
                    self.fx.commit_docs(ops.PROPOSAL, f"\n{text}\n")
                rc, out = self.diag()
                self.assert_refused_after_root(rc, out, f"diag_release_missing {self.RETRY1}")

    def test_release_mismatch_refuses(self) -> None:
        passed, rel = self.fx.passed, self.fx.rel
        self.drop_release_line()
        self.fx.commit_docs(ops.PROPOSAL, f"\n- `diag_release: {self.RETRY1} {rel}`\n- diag_release: {self.RETRY1} {'0' * 40}\n"
                                          f"diag_release: {self.RETRY1} {passed.upper()}\ndiag_release: {self.SUB3} {passed}\n")
        rc, out = self.diag()
        self.assert_refused_after_root(rc, out, f"diag_release_mismatch {self.RETRY1}")
        entry = ops.DIAG_ENTRIES[self.RETRY1]
        with self.assertRaises(ops.DiagRefused) as caught:  # rel（发布引用）不得当 passed
            ops.diag_release_binding(f"diag_release: {self.RETRY1} {rel}\n", entry, passed)
        self.assertIn("diag_release_mismatch", str(caught.exception))
        self.assertEqual(ops.diag_release_binding(f"x\n* `diag_release: {self.RETRY1} {passed}`\n", entry, passed),
                         {"release_line_no": 2, "release_value": passed})
        with self.assertRaises(ops.DiagRefused):
            ops.diag_release_binding(f"diag_release: {self.RETRY1} {passed}\n", entry, None)

    def test_release_proposal_unreadable_refuses(self) -> None:
        git(self.fx.docwt, "rm", "-q", ops.PROPOSAL)
        git(self.fx.docwt, "commit", "-m", "drop proposal")
        git(self.fx.docwt, "push", "origin", "HEAD:main")
        rc, out = self.diag()
        self.assert_refused_after_root(rc, out, "diag_release_unreadable")
        with self.assertRaises(ops.DiagRefused) as caught:
            ops.diag_release_binding(None, ops.DIAG_ENTRIES[self.RETRY1], self.fx.passed)
        self.assertIn("diag_release_unreadable", str(caught.exception))

    # --- BIND-3：账本唯一条目 ---

    def test_ledger_title_missing_duplicate_or_id_outside_entry_refuses(self) -> None:
        base = "用户答 Mac mini 补核核清四题\nSLOT:FACT:1\n"
        cases = (
            (f"\n## y — 其他条目\n- `{self.RETRY1}`\n", "ledger_entry_missing"),
            (f"\n## a — {self.RETRY1_TITLE}\n- `{self.RETRY1}`\n## b — {self.RETRY1_TITLE}（重复）\n- `{self.RETRY1}`\n", "ledger_entry_ambiguous"),
            (f"\n## a — {self.RETRY1_TITLE}\n- 无完整 id\n## b — 他条\n- `{self.RETRY1}`\n", "ledger_request_id_missing"),
            (f"\n## a — {self.RETRY1_TITLE}\n- `{self.RETRY1}:WINDOW`\n", "ledger_request_id_missing"),
            (f"\n## a — {self.RETRY1_TITLE}\n- {self.RETRY1} 未加反引号\n", "ledger_request_id_missing"),
            (f"\n## a — {self.RETRY1_TITLE} `{self.RETRY1}`\n- 正文无 id\n", "ledger_request_id_missing"),
        )
        target = self.fx.docwt / "docs/authorizations.md"
        for text, needle in cases:
            with self.subTest(needle=needle, text=text):
                target.write_text(base + text, encoding="utf-8")
                git(self.fx.docwt, "commit", "-qam", "ledger variant")
                git(self.fx.docwt, "push", "origin", "HEAD:main")
                rc, out = self.diag()
                self.assert_refused_after_root(rc, out, needle)
        entry = ops.DIAG_ENTRIES[self.RETRY1]
        with self.assertRaises(ops.DiagRefused) as caught:
            ops.diag_ledger_binding(None, entry)
        self.assertIn("ledger_unreadable", str(caught.exception))
        # 三级小标题不切条目；正文命中即绑定，记录标题行原文与行号
        self.assertEqual(ops.diag_ledger_binding(f"# t\n## a — {self.RETRY1_TITLE}\n### 细节\n- `{self.RETRY1}`\n## b\n", entry),
                         {"ledger_title_line_no": 2, "ledger_title_line": f"## a — {self.RETRY1_TITLE}"})

    # --- BIND-1/2：已签条目、限额与身份记录 ---

    def test_retry1_account_records_binding_and_signed_limits(self) -> None:
        self.assertEqual(set(ops.DIAG_ENTRIES), {self.SUB3, self.RETRY1})
        self.assertEqual(ops.DIAG_RETRY1_REQUEST_ID, self.RETRY1)
        self.assertEqual(ops.DIAG_REQUEST_ID, self.SUB3)  # 旧常量名与值不改
        old, new = ops.DIAG_ENTRIES[self.SUB3], ops.DIAG_ENTRIES[self.RETRY1]
        self.assertEqual((old.status, old.release_key), ("exhausted", "sub3_release"))
        self.assertEqual((new.status, new.ledger_title, new.release_key, new.playbooks),
                         ("signed", self.RETRY1_TITLE, "diag_release", ("P1",)))
        # 「全套与诊断签发落实」§3 已签维度逐项（同一 DIAG_LIMITS 对象，不按条目复制）
        self.assertEqual(ops.DIAG_LIMITS, {"master_connections": 2, "serve_starts": 1, "fault_restarts": 0, "plays": 1, "sessions": 1,
                                           "measure_runs": 1, "k_receipt_runs": 1, "wall_s": 2700.0,
                                           "air_bytes": 250_000_000, "board_bytes": 200_000_000})
        self.fx.cfg["diag"] = {"root_exists": True}  # 走过全部绑定前提后在板核处故障收尾（不进服务/Play）
        self.fx.save()
        rc, out = self.diag()
        self.assertEqual(rc, 3, out)
        data = self.ledger()
        root = sorted(self.parent.glob("*/ops-diagnostic-ledger.json"))[-1].parent
        self.assertEqual(data["request_id"], self.RETRY1)
        self.assertTrue(data["consumed"])
        self.assertEqual(data["limits"], ops.DIAG_LIMITS)
        self.assertEqual(data["used"]["master_connections"], 1)
        binding = data["entry_binding"]
        self.assertEqual({k: binding[k] for k in ("request_id", "status", "ledger_title", "release_key", "playbooks",
                                                  "ledger_title_line", "release_value", "passed_candidate", "rel")},
                         {"request_id": self.RETRY1, "status": "signed", "ledger_title": self.RETRY1_TITLE, "release_key": "diag_release",
                          "playbooks": ["P1"], "ledger_title_line": f"## x — {self.RETRY1_TITLE}", "release_value": self.fx.passed,
                          "passed_candidate": self.fx.passed, "rel": self.fx.rel})
        self.assertIsInstance(binding["ledger_title_line_no"], int)
        self.assertIsInstance(binding["release_line_no"], int)
        events = [json.loads(line) for line in (root / "ops-events.jsonl").read_text().splitlines()]
        self.assertEqual([e["request_id"] for e in events if e["kind"] in {"diag_start", "diag_entry_binding"}], [self.RETRY1, self.RETRY1])
        self.assertIn(f"request_id {self.RETRY1}", (root / "NOTES.md").read_text())

    def test_contract_format_examples_are_not_release_lines(self) -> None:
        for document in (ops.PROPOSAL, ops.DIAG_OPS_DOC):
            with self.subTest(document=document):
                examples = [line for line in (REPO / document).read_text(encoding="utf-8").splitlines() if "diag_release: <" in line]
                self.assertTrue(examples)
                self.assertEqual([line for line in examples if ops.DIAG_RELEASE_KEY_LINE.match(line)], [])


class DiagControlPathTests(DiagTestBase):
    """评分诊断合批修复 / DIAG-CONTROL-1（AC-10 修订 8）：生产长诊断根下 ControlPath 的本机限制、同路径、计次、释放。"""

    long_root = True

    def ssh_by_path(self) -> dict[str, list[list[str]]]:
        """按实际 ControlPath 分组：-fN 的 ControlPath=… 与 -S … 的值。"""
        groups: dict[str, list[list[str]]] = {}
        for argv in self.fx.calls("ssh"):
            if "-fN" in argv:
                path = [a.split("=", 1)[1] for a in argv if a.startswith("ControlPath=")][0]
            elif "-S" in argv:
                path = argv[argv.index("-S") + 1]
            else:
                continue
            groups.setdefault(path, []).append(argv)
        return groups

    def test_diag_control_long_production_root_master_binds_real_unix_socket(self) -> None:
        """修前必红：旧 ControlPath 在诊断根 ssh/ 下，带 OpenSSH 后缀超本机上限 → 真实 bind 失败 rc 255（SUB:3 原故障）。"""
        old_style = self.fx.repo / ops.DIAG_AIR_PARENT / "20261008T155230Z" / "ssh" / "cm-d1"
        self.assertGreater(len(os.fsencode(str(old_style))) + 17, _socket_capacity() - 1)  # 前提：长根已复现
        old_style.parent.mkdir(parents=True)
        with self.assertRaises(OSError) as too_long:
            _bind_probe(str(old_style))  # 本机 AF_UNIX 实测：旧式路径带后缀放不下
        self.assertIn("too long", str(too_long.exception))
        shutil.rmtree(self.fx.repo / ops.DIAG_AIR_PARENT / "20261008T155230Z")
        self.fx.cfg["diag"] = {"serve_fault": True}  # 走到 d2 与收尾即可（服务拒启），不进 Play
        self.fx.save()
        rc, out = self.diag()
        self.assertEqual(rc, 3, out)
        data = self.ledger()
        self.assertFalse([f for f in data["faults"] if "ssh_master_failed" in f["detail"]], data["faults"])
        self.assertEqual([c["rc"] for c in data["master_connections"]], [0, 0])
        self.assertEqual(data["used"]["master_connections"], 2)
        root = sorted(self.parent.glob("*/ops-diagnostic-ledger.json"))[-1].parent.resolve()
        control = data["control_dir"]
        paths = {name: control["paths"][name]["control_path"] for name in ("d1", "d2")}
        # 两条主连接各自独立的短路径，同一本次私有目录，位于诊断根之外；带后缀字节 ≤ 本机上限
        self.assertNotEqual(paths["d1"], paths["d2"])
        self.assertEqual({str(Path(v).parent) for v in paths.values()}, {control["path"]})
        self.assertFalse(control["path"].startswith(str(root)))
        self.assertTrue(control["path"].startswith(self.control_parent.name))
        for name, value in paths.items():
            self.assertEqual(control["paths"][name]["bytes_with_suffix"], len(os.fsencode(value)) + 17)
            self.assertLessEqual(control["paths"][name]["bytes_with_suffix"], _socket_capacity() - 1)
            self.assertEqual(control["probe"][name]["bind"], "ok")
        self.assertEqual((control["mode"], control["uid"]), ("0o700", os.getuid()))
        # 每条连接：ControlMaster 创建、check、通道、exit 全用同一实际路径；无第三条主连接/无隐式直连
        groups = self.ssh_by_path()
        self.assertEqual(set(groups), set(paths.values()))
        for name, value in paths.items():
            kinds = [("master" if "-fN" in a else a[a.index("-O") + 1] if "-O" in a else "channel") for a in groups[value]]
            self.assertEqual(kinds[0], "master")
            self.assertEqual(kinds.count("master"), 1)
            self.assertIn("check", kinds)
            self.assertIn("channel", kinds)
            self.assertEqual(kinds[-1], "exit")
        self.assertEqual(sum(1 for a in self.fx.calls("ssh") if "-fN" in a), 2)
        self.assertFalse([a for a in self.fx.calls("ssh") if "-G" not in a and "-fN" not in a and "-S" not in a])
        # 收尾：主连接退出后才释放，空目录已删；释放前 Air 读数含该目录；原流留指针
        self.assertTrue(control["released"]["removed"])
        self.assertEqual(control["released"]["left_entries"], [])
        self.assertFalse(Path(control["path"]).exists())
        self.assertIn("ControlPath", data["disk"]["air_source"])
        self.assertTrue(any(r["source"] == "before control dir release" for r in data["disk"]["air"]))
        events = [json.loads(l)["kind"] for l in (root / "ops-events.jsonl").read_text().splitlines()]
        self.assertLess(events.index("diag_control_dir"), events.index("diag_control_dir_release"))
        self.assertIn(f"control_path\t{paths['d1']}", (root / "ssh" / "d1.tsv").read_text())
        self.assertEqual(data["unknown"], [])

    def test_diag_control_allocation_binds_af_unix_with_suffix_and_is_private_and_unique(self) -> None:
        """本机 AF_UNIX 实际 bind/关闭核短路径（含 OpenSSH 17 字节后缀）；生产缺省父目录；0700/本用户/跨批唯一。"""
        saved = ops.DIAG_CONTROL_PARENT
        ops.DIAG_CONTROL_PARENT = None  # 生产缺省（tempfile.gettempdir()）
        self.addCleanup(setattr, ops, "DIAG_CONTROL_PARENT", saved)
        first = ops.DiagControlDir.allocate(("d1", "d2"))
        self.addCleanup(shutil.rmtree, first.path, True)
        second = ops.DiagControlDir.allocate(("d1", "d2"))
        self.addCleanup(shutil.rmtree, second.path, True)
        self.assertNotEqual(first.path, second.path)  # 跨批不复用
        for control in (first, second):
            info = os.lstat(control.path)
            self.assertTrue(stat.S_ISDIR(info.st_mode))
            self.assertEqual((stat.S_IMODE(info.st_mode), info.st_uid), (0o700, os.getuid()))
            self.assertEqual(control.entries(), [])  # 探针已删
            for name in ("d1", "d2"):
                _bind_probe(str(control.control_path(name)))  # 不抛即本机可 bind
        with self.assertRaises(ops.DiagFault):
            first.control_path("d3")
        # 释放：空目录才删；残留套接字不删（不能删除/复用未知或未退出主连接的套接字），记残留
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(second.control_path("d2")))
        listener.close()
        kept = second.release()
        self.assertEqual((kept["removed"], kept["left_entries"]), (False, ["d2"]))
        self.assertTrue(os.path.lexists(second.control_path("d2")))
        removed = first.release()
        self.assertTrue(removed["removed"])
        self.assertFalse(first.path.exists())

    def test_diag_no_safe_short_path_is_refused_before_consumption(self) -> None:
        deep = Path(self.control_parent.name) / ("p" * 90)
        deep.mkdir()
        ops.DIAG_CONTROL_PARENT = str(deep)
        rc, out = self.diag()
        self.assertEqual(rc, 3, out)
        self.assertIn("DIAG_REFUSED control_path_too_long", out)
        self.assertFalse(self.ledger()["consumed"])
        self.assertEqual([a for a in self.fx.calls("ssh") if "-G" not in a], [])
        self.assertEqual(os.listdir(deep), [])  # 没有留下任何目录
        rc, out = self.diag()  # 未消耗：之后仍可在条件满足时启动（此处同样拒启，不计次）
        self.assertIn("DIAG_REFUSED", out)

    def test_diag_unsafe_control_dir_is_fault_before_master_attempt(self) -> None:
        with patched_env(self.fx.env()):
            ctx = self.context()
        account = ops.DiagAccount(Path(self.tmp.name), "20261008T000000Z", "/home/jetson/eng-loop2-diag/x")
        control = ops.DiagControlDir.allocate(("d1", "d2"), parent=self.control_parent.name)
        os.chmod(control.path, 0o755)
        connection = ops.DiagConnection(ctx, account, "d1", control)
        with patched_env(self.fx.env()), self.assertRaises(ops.DiagFault) as caught:
            connection.open()
        self.assertIn("control_dir_unsafe", caught.exception.detail)
        self.assertEqual(account.data["used"]["master_connections"], 0)
        self.assertEqual([a for a in self.fx.calls("ssh") if "-fN" in a], [])

    def test_diag_master_failure_counted_no_fallback_and_control_dir_released(self) -> None:
        self.fx.cfg["master_rc"] = 255
        self.fx.save()
        rc, out = self.diag()
        self.assertEqual(rc, 3, out)
        data = self.ledger()
        self.assertEqual(data["used"]["master_connections"], 1)
        self.assertTrue(any("ssh_master_failed d1" in f["detail"] for f in data["faults"]))
        ssh = [a for a in self.fx.calls("ssh") if "-G" not in a]
        self.assertEqual(len(ssh), 1)  # 只有那一次主连接尝试：无 check/通道/exit、无直连、无重试、无 d2
        self.assertIn("-fN", ssh[0])
        self.assertTrue(data["control_dir"]["released"]["removed"])
        self.assertFalse(Path(data["control_dir"]["path"]).exists())
        self.assertEqual(data["stages_not_executed"], ["prepare_board", "start_service", "check_status", "make_receipt", "play"])

    def test_diag_socket_lost_is_fault_without_new_auth_and_released(self) -> None:
        self.fx.cfg["check_fail"] = True
        self.fx.save()
        rc, out = self.diag()
        self.assertEqual(rc, 3, out)
        data = self.ledger()
        self.assertTrue(any("control_socket_unavailable before board-check" in f["detail"] for f in data["faults"]))
        ssh = self.fx.calls("ssh")
        self.assertEqual(sum(1 for a in ssh if "-fN" in a), 1)
        self.assertFalse([a for a in ssh if "-S" in a and "-O" not in a])  # 没有任何通道
        self.assertEqual(len(self.ssh_by_path()), 1)
        self.assertTrue(data["control_dir"]["released"]["removed"])

    def test_diag_leftover_socket_after_exit_is_unknown_and_not_deleted(self) -> None:
        self.fx.cfg["exit_keeps_socket"] = True
        self.fx.cfg["diag"] = {"serve_fault": True}
        self.fx.save()
        rc, out = self.diag()
        self.assertEqual(rc, 3, out)
        data = self.ledger()
        control = data["control_dir"]
        self.assertFalse(control["released"]["removed"])
        self.assertEqual(control["released"]["left_entries"], ["d1", "d2"])
        for name in ("d1", "d2"):
            self.assertTrue(os.path.lexists(control["paths"][name]["control_path"]))
        self.assertTrue(any("not removed" in u["detail"] and control["path"] in u["detail"] for u in data["unknown"]))


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def http_get(port: int, path: str) -> bytes:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request("GET", path, headers={"Host": f"127.0.0.1:{port}"})
    return connection.getresponse().read()


def http_post(port: int, nonce: str, body: dict[str, Any]) -> dict[str, Any]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    connection.request("POST", "/api/action", body=json.dumps(body).encode(),
                       headers={"Host": f"127.0.0.1:{port}", "Content-Type": "application/json", "X-Ops-Nonce": nonce})
    return json.loads(connection.getresponse().read())


if __name__ == "__main__":
    unittest.main()
