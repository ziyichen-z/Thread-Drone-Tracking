"""AC-10 消耗账本与 AC-15 待用户项（桌面机运行）：逐维度实际用量对照 §5 阶段 A 生效值。

事件来源：`outputs/eng-jet/P1-ENG-JET-001/ledger-events.jsonl`（每次上板会话、到板传输、SR 轮、pip、下载等逐条
追加，`add` 子命令写入）；`build` 汇总为 `docs/evidence/P1-ENG-JET-001-ledger.json`，并以 `git diff --stat` 核
`Assets/`、`controller/`、`config/` 为空（基线 = 本轮开工 HEAD，运行时传入，不手写）。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

from tools.eng_jet import common

EVENTS = common.OUT_DIR / "ledger-events.jsonl"
KINDS = ("board_session", "to_board_transfer", "sr_round", "board_pip", "model_download", "board_vlm_query", "engine_export", "note",
         "sub1_pip", "sub1_network", "sub1_disk", "board_cleanup",
         "mac_full_suite_precheck", "mac_full_suite_run", "mac_model_load",
         "mac_sub5_det_assoc_load", "mac_sub5_partial_replay")

#: §7 (h)–(n) 答复状态（AC-15）：标题逐字取自 `docs/authorizations.md`；未答复项对应动作零执行。
PENDING_USER: dict[str, dict[str, Any]] = {
    "h": {"item": "中继正式链路", "status": "answered", "ledger_titles": [
        "2026-09-28 P1-ENG-JET-001 — 用户签发 §5 阶段 A 执行信封并答复 §7 (h)(n)，(i)–(m) 暂不答复（supervisor 会话代录）",
        "2026-10-02 P1-ENG-JET-001 — 用户告知 Jetson 配置完成、允许从 Mac mini 复制 frozen-V 缓存、有线链路未接（supervisor 会话代录）",
        "2026-10-03 P1-ENG-JET-001 — 用户告知 Mac mini ↔ Jetson 有线直连成功（§7 (h) 答复；supervisor 会话代录）",
        "2026-10-03 P1-ENG-JET-001 — 用户授权把 Jetson 有线地址主机密钥写入 Mac mini `~/.ssh/known_hosts`，并指示接受收工后直接派实现跑 S2（supervisor 会话代录）"],
        "effect": "答复 = 按推荐接线 + 固定 IP；10-03 有线直连已接好（mini 192.168.8.1 ↔ Jetson 192.168.8.2；mini 代理经有线可达，"
                  "known_hosts 已由用户授权追加，K1K3K4补跑E 以 StrictHostKeyChecking=yes 经有线 ssh 执行 S2）。现状（K1K3K4补跑F）：用户选 S2 处置 (α′) 后，"
                  "正式 SR 已在该有线链路执行 4 轮（f1-echo 为 STOP(RELAY_INTEGRITY) 返工轮；f2-echo / f3-track 为 forward 零链路事件轮；f4-track-drops 为断链轮），"
                  "读数见 -relay.json forward/return/disconnect；AC-4…6 是否满足由停点核对与复核判定。历史：K1K3K4补跑E 时正式 SR 尚未执行"
                  "（须 S2 可继续后另派）；10-02 告知尚未接好时只跑 ≤ 1 轮 TAILSCALE_SMOKE（非结论小节，1/1 已用）",
        "related_ledger_titles": [
            "2026-10-03 P1-ENG-JET-001 — 用户选题 7 (α)：S1 STOP 记录偏差、以方形 FP16 引擎继续（supervisor 会话代录）",
            "2026-10-03 P1-ENG-JET-001 — 用户选 S2 STOP 处置 (α′)：S2 记录偏差并继续，做原范围正式 SR（supervisor 会话代录）"]},
    "i": {"item": "量化主机", "status": "unanswered", "effect": "不租云、不 WSL2、不合并 C2；3c、3b C2 自转 GGUF 及其 S4 零执行"},
    "j": {"item": "S3a HF bf16 对照", "status": "unanswered", "effect": "3a 零执行，不为 3a 下载 base"},
    "k": {"item": "S0 非 Super 配置", "status": "unanswered", "effect": "不重刷（S0 实测为 Super，未触发）"},
    "l": {"item": "会话级 systemctl isolate", "status": "unanswered", "effect": "未执行 systemctl isolate（S0 实测已 headless，未触发）"},
    "m": {"item": "功耗模式", "status": "unanswered", "effect": "未执行 nvpmodel -m（S0 实测当前 MAXN_SUPER，未触发）"},
    "n": {"item": "信封签发方式", "status": "answered", "ledger_titles": [
        "2026-09-28 P1-ENG-JET-001 — 用户签发 §5 阶段 A 执行信封并答复 §7 (h)(n)，(i)–(m) 暂不答复（supervisor 会话代录）"],
        "effect": "先签阶段 A；阶段 B 全部维度 0 → S3–S5 NOT_RUN(阶段 B 信封未签)"},
}


#: 复核 R1-4：`build` 中以下字段是写定常量（实现侧断言/限制），不是对设备、外联或系统设置的动态测量；输出逐字带此说明。
CONSTANT_ASSERTION_NOTE: dict[str, str] = {
    "mac.pip": "常量断言（未测量）：本项流程不在 Mac 上执行 pip；本字段写定为 0，不是对 Mac 包环境的动态检测",
    "system_settings.changed": "常量断言（未测量）：本项命令集不含改系统设置的动作（由 tests/test_eng_jet_guards.py::NoSystemSettingChanges "
                               "静态检查命令文本）；本字段写定为空，不是对板上/Mac 系统设置的动态检测",
}
WITHIN_ENVELOPE_BASIS = ("只比较已记账事件（ledger-events.jsonl）的累计数量与各上限；不检测执行设备、具名范围、网络外联或系统设置，"
                         "mac.pip 与 system_settings.changed 为常量断言（见各字段 basis）；复核 R1-4 限制")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def add(kind: str, **fields: Any) -> dict[str, Any]:
    if kind not in KINDS:
        raise ValueError(f"unknown ledger kind {kind!r}")
    row = {"kind": kind, "recorded_utc": utc_now(), **fields}
    common.append_jsonl(EVENTS, row)
    return row


def _seconds(start: str, end: str) -> float:
    parse = lambda text: dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)  # noqa: E731
    return (parse(end) - parse(start)).total_seconds()


def sub1_dimension(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """SUB:1（torch/torchvision 及依赖）：包数 = 实际取回或安装的 distinct 包；下载字节取「轮子字节合计」与「板上网卡收包增量」
    两种口径之大（后者含 ssh/Tailscale 开销，是保守上界）；新增磁盘 = 最近一次 `sub1_disk` 记录。"""
    env = common.ENVELOPE_SUB1
    pips = [e for e in events if e["kind"] == "sub1_pip"]
    nets = [e for e in events if e["kind"] == "sub1_network"]
    disks = [e for e in events if e["kind"] == "sub1_disk"]
    packages = sorted({str(e["package"]).lower() for e in pips})
    wheel_bytes = sum(int(e.get("wheel_bytes", 0)) for e in pips)
    rx_bytes = sum(int(e.get("rx_bytes", 0)) for e in nets)
    download_bytes = max(wheel_bytes, rx_bytes)
    new_disk = int(disks[-1]["new_disk_bytes"]) if disks else 0
    within = len(packages) <= env["packages_max"] and download_bytes <= env["download_bytes_max"] and new_disk <= env["new_disk_bytes_max"]
    return {"signed_used": bool(pips or nets or disks), "packages": len(packages), "package_names": packages, "items": pips,
            "wheel_bytes": wheel_bytes, "network_rx_bytes": rx_bytes, "download_bytes": download_bytes,
            "download_bytes_basis": "max(轮子字节合计, 板上网卡收包增量)", "network_items": nets,
            "new_disk_bytes": new_disk, "disk_items": disks,
            "limit_packages": env["packages_max"], "limit_download_bytes": env["download_bytes_max"],
            "limit_new_disk_bytes": env["new_disk_bytes_max"], "within": within}


def sub2_dimension(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """SUB:2（AC-10 修订 3）：Mac 本机 CPU 停点全套一次内的模型加载。`mac_model_load` 每条 = 一次加载尝试（`model` 名、`count`，
    成功/失败/重试一律计入、不回退）；`mac_full_suite_run` 每条 = 一次全套执行（上限 1）；`mac_full_suite_precheck` 为跑前只读核对记录
    （不消耗）。未列名模型（如 det-assoc 冻结检测器）额度为 0，出现即越界。"""
    env = common.ENVELOPE_SUB2
    loads = [e for e in events if e["kind"] == "mac_model_load"]
    runs = [e for e in events if e["kind"] == "mac_full_suite_run"]
    prechecks = [e for e in events if e["kind"] == "mac_full_suite_precheck"]
    named = {name: 0 for name in env["model_loads_max"]}
    other: dict[str, int] = {}
    for event in loads:
        name = str(event["model"]).lower()
        count = int(event.get("count", 1))
        if name in named:
            named[name] += count
        else:
            other[name] = other.get(name, 0) + count
    within = (all(named[n] <= env["model_loads_max"][n] for n in named) and sum(other.values()) <= env["other_models_max"]
              and len(runs) <= env["full_suite_runs_max"])
    return {"request_id": common.SUB2_REQUEST_ID, "ledger_title": common.SUB2_LEDGER_TITLE, "signed": True, "effective": env,
            "model_loads": named, "other_model_loads": other, "load_items": loads,
            "full_suite_runs": len(runs), "full_suite_run_items": runs, "prechecks": prechecks,
            "within": within}


def sub5_dimension(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """SUB:5 A（AC-10 修订 5/6）：`mac_sub5_det_assoc_load` 每条 = det-assoc 冻结检测器加载/构造尝试（`count`，成功/失败/重试一律计入）；
    `mac_sub5_partial_replay` 每条 = 具名零模型部分回放（`count`）。全套次数与 SUB:2 共用（不另计）；det-assoc 只记在本处，
    不进 `sub2.other_model_loads`（不重复扣账）。"""
    env = common.ENVELOPE_SUB5
    loads = [e for e in events if e["kind"] == "mac_sub5_det_assoc_load"]
    replays = [e for e in events if e["kind"] == "mac_sub5_partial_replay"]
    det_assoc = sum(int(e.get("count", 1)) for e in loads)
    partial = sum(int(e.get("count", 1)) for e in replays)
    shared_runs = sum(1 for e in events if e["kind"] == "mac_full_suite_run")
    within = det_assoc <= env["det_assoc_loads_max"] and partial <= env["partial_replays_max"] and shared_runs <= 1
    return {"request_id": common.SUB5_REQUEST_ID, "ledger_title": common.SUB5_LEDGER_TITLE, "cpu1_ledger_title": common.CPU1_LEDGER_TITLE,
            "signed": True, "effective": env, "det_assoc_loads": det_assoc, "det_assoc_load_items": loads,
            "partial_replays": partial, "partial_replay_items": replays,
            "full_suite_runs_shared_with_sub2": shared_runs, "within": within}


def git_diff_stat(base: str, paths: Sequence[str] = ("Assets", "controller", "config")) -> dict[str, Any]:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=common.PROJECT_ROOT, capture_output=True, text=True, check=True).stdout.strip()
    committed = subprocess.run(["git", "diff", "--stat", f"{base}..HEAD", "--", *paths], cwd=common.PROJECT_ROOT,
                               capture_output=True, text=True, check=True).stdout.strip()
    worktree = subprocess.run(["git", "diff", "--stat", "HEAD", "--", *paths], cwd=common.PROJECT_ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    return {"base": base, "head_at_build": head, "paths": list(paths), "committed_diff_stat": committed, "worktree_diff_stat": worktree,
            "empty": committed == "" and worktree == ""}


def build(events: Sequence[Mapping[str, Any]], base: str, board_disk_bytes: int | None, mac_outputs_bytes: int) -> dict[str, Any]:
    env = common.ENVELOPE_STAGE_A
    sessions = [e for e in events if e["kind"] == "board_session"]
    board_wall = sum(_seconds(e["start_utc"], e["end_utc"]) for e in sessions)
    to_board = [e for e in events if e["kind"] == "to_board_transfer"]
    to_board_bytes = sum(int(e["bytes"]) for e in to_board)
    rounds = [e for e in events if e["kind"] == "sr_round"]
    pip = [e for e in events if e["kind"] == "board_pip"]
    downloads = [e for e in events if e["kind"] == "model_download"]
    queries = sum(int(e.get("count", 0)) for e in events if e["kind"] == "board_vlm_query")
    exports = [e for e in events if e["kind"] == "engine_export"]
    sub1 = sub1_dimension(events)
    sub2 = sub2_dimension(events)
    sub5 = sub5_dimension(events)
    disk_limit = env["board_disk_bytes_max"] if not sub1["signed_used"] else common.ENVELOPE_SUB1["board_disk_bytes_max_effective"]
    dims = {
        "model_downloads": {"used": len(downloads), "bytes": sum(int(e.get("bytes", 0)) for e in downloads), "items": downloads,
                            "limit": env["model_downloads"]},
        "board_pip": {"packages": len(pip), "bytes": sum(int(e.get("bytes", 0)) for e in pip), "items": pip,
                      "limit_packages": env["board_pip_packages_max"], "limit_bytes": env["board_pip_bytes_max"]},
        "quant_host": {"gpu_h": 0, "usd": 0, "instances": [], "limit": env["quant_host_gpu_h"]},
        "to_board_transfer": {"bytes": to_board_bytes, "items": to_board, "limit_bytes": env["to_board_bytes_max"]},
        "sr_rounds": {"rounds": len(rounds), "items": rounds, "limit_rounds": env["sr_rounds_max"],
                      "tailscale_smoke_rounds": sum(1 for r in rounds if r.get("mode") == "TAILSCALE_SMOKE"),
                      "limit_tailscale_smoke": env["tailscale_smoke_rounds_max"], "limit_bytes_each": env["sr_round_bytes_max"]},
        "board_wall_clock": {"seconds": round(board_wall, 1), "sessions": sessions, "limit_s": env["board_wall_s_max"],
                             "engine_exports": len(exports), "engine_export_items": exports,
                             "engine_export_limit_s_each": env["engine_export_wall_s_max_each"]},
        "board_vlm_queries": {"used": queries, "limit": env["board_vlm_queries"]},
        "board_disk": {"bytes": board_disk_bytes, "limit_bytes": disk_limit, "path": f"{common.BOARD_ROOT}/",
                       "limit_basis": "§5 阶段 A ≤ 5 GB；SUB:1 签发后生效值 ≤ 13 GB（账本同日 SUB:1 条目）" if sub1["signed_used"] else "§5 阶段 A",
                       "cleanups": [e for e in events if e["kind"] == "board_cleanup"]},
        "sub1_torch": sub1,
        "mac": {"pip": 0, "pip_basis": CONSTANT_ASSERTION_NOTE["mac.pip"], "models": sum(sub2["model_loads"].values()) + sum(sub2["other_model_loads"].values()) + sub5["det_assoc_loads"],
                "models_basis": "Mac 本机模型加载/构造尝试次数合计（SUB:2 已签前全部场景为 0；签后只在停点全套一次内按 sub2 四种分列"
                                "与 sub5 det-assoc 计入，回放不计模型加载）",
                "sub2": sub2, "sub5": sub5, "outputs_eng_jet_bytes": mac_outputs_bytes, "limit_outputs_bytes": env["mac_outputs_bytes_max"]},
        "system_settings": {"changed": [], "basis": CONSTANT_ASSERTION_NOTE["system_settings.changed"],
                            "note": "只读核验；未执行 sudo / nvpmodel -m / systemctl isolate / jetson_clocks"},
        "unity_play": 0, "scenario_session_run_ids": 0, "training_gpu_h": 0, "model_api": 0, "public_release": "no",
    }
    within = (
        dims["model_downloads"]["used"] <= env["model_downloads"]
        and dims["board_pip"]["packages"] <= env["board_pip_packages_max"] and dims["board_pip"]["bytes"] <= env["board_pip_bytes_max"]
        and to_board_bytes <= env["to_board_bytes_max"]
        and len(rounds) <= env["sr_rounds_max"] and dims["sr_rounds"]["tailscale_smoke_rounds"] <= env["tailscale_smoke_rounds_max"]
        and all(int(r["bytes"]) <= env["sr_round_bytes_max"] for r in rounds)
        and board_wall <= env["board_wall_s_max"]
        and all(float(e["wall_s"]) <= env["engine_export_wall_s_max_each"] for e in exports)
        and queries <= env["board_vlm_queries"]
        and (board_disk_bytes or 0) <= disk_limit
        and sub1["within"]
        and sub2["within"]
        and sub5["within"]
        and mac_outputs_bytes <= env["mac_outputs_bytes_max"]
    )
    diff = git_diff_stat(base)
    return {
        "work_id": common.WORK_ID,
        "envelope": {"stage": "A", "source": "docs/authorizations.md 2026-09-28「P1-ENG-JET-001 — 用户签发 §5 阶段 A 执行信封…」；"
                     "提案决策记录「§5 阶段 A 信封与 §7 (h)(n) 答复落实」", "effective": env,
                     "sub1": {"request_id": common.SUB1_REQUEST_ID, "ledger_title": common.SUB1_LEDGER_TITLE, "effective": common.ENVELOPE_SUB1},
                     "sub2": {"request_id": common.SUB2_REQUEST_ID, "ledger_title": common.SUB2_LEDGER_TITLE, "effective": common.ENVELOPE_SUB2,
                              "contract": "提案决策记录「SUB:2 落实：§5 Mac 与 IR-9（2026-10-03，CLARIFY）」；不是 supervisor SUB 代拍，"
                                          "执行信封子额度块仍未签；不把 SUB:2 读成阶段 B 已签（pending_user.n 不变）"},
                     "sub5": {"request_id": common.SUB5_REQUEST_ID, "ledger_title": common.SUB5_LEDGER_TITLE,
                              "cpu1_ledger_title": common.CPU1_LEDGER_TITLE, "effective": common.ENVELOPE_SUB5,
                              "contract": "提案决策记录「SUB:5 A 落实与 CPU 执行方案核对（2026-10-03，CLARIFY）」AC-10 修订 5 与「CPU-1 落实与下一"
                                          "实现范围（2026-10-03，CLARIFY）」AC-10 修订 6；用户直接签发，不是 supervisor SUB 代拍；不是阶段 B"}},
        "stage_b": {"signed": False, "all_dimensions": 0},
        "dimensions": dims,
        "within_envelope": within,
        "within_envelope_basis": WITHIN_ENVELOPE_BASIS,
        "git_diff_assets_controller_config": diff,
        "pending_user": PENDING_USER,
        "consuming": "no",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    a = sub.add_parser("add")
    a.add_argument("kind", choices=KINDS)
    a.add_argument("--json", required=True, help="字段 JSON")
    b = sub.add_parser("build")
    b.add_argument("--base", required=True, help="本轮开工基线 commit（运行时解析传入）")
    b.add_argument("--board-disk-bytes", type=int, default=None)
    args = parser.parse_args(argv)
    if args.action == "add":
        print(json.dumps(add(args.kind, **json.loads(args.json)), ensure_ascii=False))
        return 0
    events = common.read_jsonl(EVENTS) if EVENTS.exists() else []
    document = build(events, args.base, args.board_disk_bytes, common.disk_usage_bytes(common.OUT_ROOT))
    common.write_json(common.evidence("ledger.json"), document)
    print(json.dumps({"within_envelope": document["within_envelope"], "diff_empty": document["git_diff_assets_controller_config"]["empty"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
