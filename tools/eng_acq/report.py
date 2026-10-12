#!/usr/bin/env python3
"""P1-ENG-ACQ-001 E1/E2 描述性报告（§3.9；AC-7/AC-8/AC-11/AC-20）→ `docs/evidence/P1-ENG-ACQ-001-report.md`。

只读 `-e1.json`、`-e2.json`、`-assets.json`、`-ledger.json` 与三序列元数据（计数用，不做任何解析或回放）。
报告只作机制描述：不设门、不写「通过」、不引用 FAST-002 的 G-5/G-6/H 读数作为本项证据。
"""

from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_acq import common, data  # noqa: E402
from tools.eng_acq.e1 import BUCKETS, DELTAS_S, VISIBLE_BUCKETS, resolve_frame_index  # noqa: E402

GMC = ("pose", "optflow", "none")
SEQS = ("scout-1", "m3-armA", "a7")


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "null"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def pooled(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """同一（序列 × 类 × gmc × 臂 × Δ）跨 S/M/L 汇总；任一层非 EVALUATED 则整格记其状态。"""
    statuses = {r["status"] for r in rows}
    counts = Counter()
    for row in rows:
        counts.update(row["buckets"])
    n_vis = sum(counts[b] for b in VISIBLE_BUCKETS)
    n_res = sum(r["N_res"] for r in rows)
    status = "EVALUATED" if statuses == {"EVALUATED"} else ",".join(sorted(s for s in statuses if s != "EVALUATED"))
    resolve_ok = (counts["BOUND_V_CORRECT"] + counts["COASTING_V_CORRECT"]) / n_vis if n_vis else None
    false_lock = (counts["BOUND_V_WRONG"] + counts["BOUND_INVISIBLE"] + counts["COASTING_V_WRONG"]) / n_res if n_res else None
    return {"status": status, "n_all": sum(r["N_all"] for r in rows), "n_vis": n_vis, "resolve_ok": resolve_ok, "false_lock": false_lock, "counts": counts}


def e1_section(e1: Mapping[str, Any]) -> list[str]:
    lines = ["## E1", ""]
    lines.append(
        "陈旧指定解析（§3.9；AC-7 修订 1/2/3 / AC-20 修订 1/2/3）。样本 (k, o) = 序列帧 k × k 帧 OK 可见对象；Δ ∈ {1, 2, 4.2, 5.4, 8, 13} s；"
        "解析帧 r = 同段内首个 t ≥ t_k + Δ 的帧；每个 (k, o, Δ) 落入 15 桶之一，逐层逐 Δ 守恒（线束断言 + `tests/test_eng_acq_e1.py`）。"
        "干净臂 = 真值框；扰动臂 `c2_quantiles` = 固定种子缩放 + 平移。分层 = 序列 × {静止, 红车} × S/M/L × gmc_source × 臂，"
        "完整 648 行（含空层）在 `docs/evidence/P1-ENG-ACQ-001-e1.json`「layers」。**读数只作描述，不设门，不外推为在线捕获成功率。**"
    )
    lines.append("")
    rep = e1["reproducibility"]
    lines.append("**复现**（固定种子两次运行字节一致）：" + "；".join(
        f"`{arm}` {v['runs']} 次 → byte_identical = {v.get('byte_identical')}（sha256 {sorted(set(v.get('sha256', {}).values()))[0][:12] if v.get('sha256') else '—'}…）" for arm, v in rep.items()
    ) + "。")
    lines.append("")
    status_counts = e1["layer_status_counts"]
    lines.append(f"**层状态**：{json.dumps(status_counts, ensure_ascii=False)}（648 = 2 臂 × 3 序列 × 2 类 × 3 尺寸 × 3 gmc × 6 Δ）。")
    lines.append("")
    budgets = dict((e1.get("clean_arm") or {}).get("level2_budget") or {})
    budgets.update(e1.get("perturbed_arm_budget") or {})
    caps_by_sequence: dict[str, set] = defaultdict(set)
    for key, b in budgets.items():
        caps_by_sequence[key.split("/")[0]].add(b.get("cap_frames_per_k_o"))
    cap_text = "、".join(f"{seq} ≤ {'/'.join(str(c) for c in sorted(caps, key=str))}" for seq, caps in sorted(caps_by_sequence.items()))
    lines.append("### 第二级代价与 AR2-2 / 每 (k,o) 帧上限（信封修订 SUB:1/SUB:2/SUB:3）")
    lines.append("")
    lines.append("| 序列 / gmc / 臂 | (k,o) 样本 | 第二级触发 | 运行（上限） | LEVEL2_SUBSAMPLED | 每 (k,o) 帧上限 | 超帧上限未运行 (k,o,Δ) |")
    lines.append("|---|---|---|---|---|---|---|")
    for key in sorted(budgets):
        b = budgets[key]
        lines.append(f"| {key} | {b['samples_k_o']} | {b['level2_triggered_k_o']} | {b['level2_selected_k_o']}（{b.get('cap_k_o')}） | {b['LEVEL2_SUBSAMPLED']} | {b.get('cap_frames_per_k_o')} | {b['not_run_frame_cap_k_o_delta']} |")
    lines.append("")
    subsampled = sorted(k for k, b in budgets.items() if b["LEVEL2_SUBSAMPLED"])
    capped = sorted(k for k, b in budgets.items() if b["not_run_frame_cap_k_o_delta"])
    status_counts_all = e1["layer_status_counts"]
    lines.append(
        "现行上限（提案决策记录「信封修订 SUB:1/SUB:2 落实」与「信封修订 SUB:3 落实」（2026-09-29；CLARIFY），AC-7/AC-20 修订 3）：a7 的第二级触发 (k,o) 在每个 gmc_source × 臂"
        f"**全样本运行**；scout-1、m3-armA 每（序列 × gmc × 臂）≤ 600；每 (k,o) SOT 帧上限按序列取值：{cap_text}（各 Δ 共用前缀）。"
        f"本次抽样组合：{', '.join(subsampled) if subsampled else '无'}；有超帧上限未运行 (k,o,Δ) 的组合：{', '.join(capped) if capped else '无'}。"
        "未运行的 (k,o,Δ) 不入 15 桶、不计 `NO_TRACK_AT_K` 或成功；其所在层记 `NOT_EVALUABLE_AR2-2`（抽样）或 `NOT_EVALUABLE_FRAME_CAP`（帧上限），"
        "比例只作子样本诊断（`ratios_scope = subsample_diagnostic_only`）。"
        f"层状态合计：{json.dumps(status_counts_all, ensure_ascii=False)}。"
        "旧候选（65 帧、a7 抽 600；及 66 帧下 scout-1 Δ13 的 32 层）的 `NOT_EVALUABLE_*` 读数不追溯改判，本报告全部取本次重跑结果。"
    )
    lines.append("")
    gaps = _delta13_frame_gaps()
    coverage = []
    for seq, g in gaps.items():
        caps = caps_by_sequence.get(seq, set())
        cap = min(caps) if caps else None
        if cap is None:
            coverage.append(f"{seq} 无本次预算记录")
        elif g["max"] is not None and g["max"] <= cap:
            coverage.append(f"{seq} 需 ≤ {g['max']} 帧、上限 {cap}，已覆盖")
        else:
            coverage.append(f"{seq} 需至多 {g['max']} 帧、上限 {cap}，**未覆盖**")
    frame_cap_layers = status_counts_all.get("NOT_EVALUABLE_FRAME_CAP", 0)
    lines.append(
        "Δ = 13 s 解析帧与 k 帧的帧号差（全部 k，只读元数据）："
        + "；".join(f"{seq} {g['min']}–{g['max']}（n = {g['n']}）" for seq, g in gaps.items())
        + "。按序列帧上限核对：" + "；".join(coverage) + "。"
        + (f"本次仍有 {frame_cap_layers} 层 `NOT_EVALUABLE_FRAME_CAP`，见上表组合。" if frame_cap_layers else "本次无 `NOT_EVALUABLE_FRAME_CAP` 层（含 scout-1 Δ13）。")
    )
    lines.append("")
    for arm in ("none", "c2_quantiles"):
        arm_rows = [r for r in e1["layers"] if r["arm"] == arm]
        if not arm_rows:
            continue
        lines.append(f"### 臂 `{arm}`：resolve_ok / false_lock（跨 S/M/L 汇总；非 EVALUATED 格标注状态）")
        lines.append("")
        header = "| 序列 | 类 | gmc | " + " | ".join(f"Δ={d:g}s" for d in DELTAS_S) + " |"
        lines.append(header)
        lines.append("|" + "---|" * (3 + len(DELTAS_S)))
        for seq in SEQS:
            tag = data.SEQUENCES[seq]["tag"]
            for cls in ("static", "red"):
                for gmc in GMC:
                    cells = []
                    for delta in DELTAS_S:
                        rows = [r for r in arm_rows if r["sequence"] == seq and r["class"] == cls and r["gmc_source"] == gmc and r["delta_s"] == delta]
                        p = pooled(rows)
                        if p["status"] != "EVALUATED":
                            cells.append(f"NE({p['status'].replace('NOT_EVALUABLE_', '')})")
                        else:
                            cells.append(f"{fmt(p['resolve_ok'])} / {fmt(p['false_lock'])} (n_vis {p['n_vis']})")
                    lines.append(f"| {seq} `{tag}` | {cls} | {gmc} | " + " | ".join(cells) + " |")
        lines.append("")
    lines.append("### 结果桶分布示例（干净臂、gmc = pose、跨尺寸汇总，Δ = 4.2 s）")
    lines.append("")
    lines.append("| 序列 | 类 | 状态 | " + " | ".join(BUCKETS) + " |")
    lines.append("|" + "---|" * (3 + len(BUCKETS)))
    for seq in SEQS:
        for cls in ("static", "red"):
            rows = [r for r in e1["layers"] if r["arm"] == "none" and r["sequence"] == seq and r["class"] == cls and r["gmc_source"] == "pose" and r["delta_s"] == 4.2]
            p = pooled(rows)
            lines.append(f"| {seq} | {cls} | {p['status']} | " + " | ".join(str(p["counts"][b]) for b in BUCKETS) + " |")
    lines.append("")
    perturbed = e1.get("perturbed_arm") or {}
    if perturbed.get("model") == "c2_quantiles":
        lines.append("### 扰动臂分位数（AC-20 修订 1/2/3）")
        lines.append("")
        lines.append(f"来源：{perturbed['source']}；只取三个统计量，`reads_c2_prediction_file = {perturbed['reads_c2_prediction_file']}`、`replays_h_frames = {perturbed['replays_h_frames']}`；种子 {perturbed['seed']}。")
        lines.append("")
        lines.append("| 分位 | C2 347 行 | 实现（全样本） | 差 | 容差 |")
        lines.append("|---|---|---|---|---|")
        for key in ("p10", "p25", "p50"):
            lines.append(f"| {key} | {perturbed['source_quantiles'][key]} | {perturbed['realized_quantiles'][key]} | {perturbed['abs_differences'][key]} | ≤ {perturbed['tolerance']} |")
        lines.append("")
        lines.append(f"逐序列实现分位：{json.dumps(perturbed['realized_by_sequence'], ensure_ascii=False)}（p10 接近容差边缘，只作描述）。")
        lines.append("")
    return lines


def e2_section(e2: Mapping[str, Any]) -> list[str]:
    lines = ["## E2", ""]
    lines.append(
        "转向存活（§3.9；AC-8）：3 序列 × 3 gmc_source × track_buffer {10, 20, 30} 次调用（名义 2/4/6 s）= 27 格全部产出。红车保持率为 "
        "FAST-001 R4 口径 A 13 s（`window_summary` 七类结局与守恒式逐字复用，另加 H-9「空窗即拒绝」断言：三序列最大帧间隔 0.325 s，断言存在且未触发）；"
        "ID 切换为每对象按真值 IoU ≥ 0.3 逐帧绑定后的切换数合计；静止车 track 寿命 = 每个（静止车, 绑定 track id）从首帧到末帧的仿真秒数。"
        "a7 为压力序列（扫视跳变），scout-1、m3-armA 为对照。**只作描述，不设门。**"
    )
    lines.append("")
    lines.append("| 序列 | gmc | buffer | 红车 13 s 保持率 (KEPT/D) | 静止车 ID 切换 / 对象 | 红车 ID 切换 | 静止车 track 寿命 中位 / 均值 s |")
    lines.append("|---|---|---|---|---|---|---|")
    for cell in sorted(e2["cells"], key=lambda c: (SEQS.index(c["sequence"]), GMC.index(c["gmc_source"]), c["track_buffer_calls"])):
        r = cell["red_retention_13s_caliber_A"] or {}
        life = cell["static_track_lifetime_s"]
        sw = cell["id_switches"]
        lines.append(
            f"| {cell['sequence']} `{cell.get('tag')}` | {cell['gmc_source']} | {cell['track_buffer_calls']} | {fmt(r.get('retention'))} ({r.get('KEPT')}/{r.get('D')}) | {sw['static_total']} / {sw['static_objects']} | {sw['red_total']} | {fmt(life['median'], 2)} / {fmt(life['mean'], 2)} |"
        )
    lines.append("")
    lines.append("### pose_warp_selfcheck（AC-5 第三条）")
    lines.append("")
    lines.append("相邻帧相机旋转 ≥ 5° 时，静止车真值框经位姿单应（四角 AABB）映射后与下一帧真值框中心误差，对照无补偿（px）：")
    lines.append("")
    lines.append("| 序列 | 帧对 | 对象对 | 位姿单应 中位 / p90 | 无补偿 中位 / p90 |")
    lines.append("|---|---|---|---|---|")
    for seq, v in e2["pose_warp_selfcheck"]["by_sequence"].items():
        a, b = v["center_error_px_pose_homography"], v["center_error_px_no_compensation"]
        lines.append(f"| {seq} | {v['frame_pairs']} | {v['object_pairs']} | {fmt(a['median'], 2)} / {fmt(a['p90'], 2)} | {fmt(b['median'], 2)} / {fmt(b['p90'], 2)} |")
    lines.append("")
    a7 = e2["pose_warp_selfcheck"]["by_sequence"]["a7"]
    better = (a7["center_error_px_pose_homography"]["median"] or 1e9) < (a7["center_error_px_no_compensation"]["median"] or 0)
    lines.append(
        f"a7 上位姿补偿{'优于' if better else '不优于'}无补偿，§6(i) 预注册处置{'不触发' if better else '触发（缺省改回 optflow）'}；`gmc_source` 缺省保持 `pose`。"
        "残差 p90 主要来自机身平移与扫视中目标出画（v1 忽略平移，§3.3）。"
    )
    lines.append("")
    return lines


def deviation_section(assets: Mapping[str, Any]) -> list[str]:
    lines = ["## 资产与偏差声明", ""]
    lines.append("复用资产本机 sha256（AC-11；详表 `docs/evidence/P1-ENG-ACQ-001-assets.json`）：")
    lines.append("")
    lines.append("| 资产 | sha256（前 16） | 来源记录 | 一致 |")
    lines.append("|---|---|---|---|")
    for item in assets["assets"]:
        if item.get("baseline"):
            verdict = "既往不可核（无既存记录；本次固定基线）"
        else:
            verdict = item["match"] if item["match"] is not None else "无既存记录（本次首记）"
        lines.append(f"| {item['label']} | `{item['sha256'][:16]}` | {item['source']} | {verdict} |")
    lines.append("")
    for item in assets["assets"]:
        baseline = item.get("baseline")
        search = item.get("prior_record_search")
        if not baseline or not search:
            continue
        identity = search["supplementary_content_identity_check"]
        lines.append(
            f"**{item['label']}（AC-11 修订 1，{baseline['label']}）**：先按 `-assets.json`「prior_record_search」逐处查找独立既存的该文件散列记录"
            f"（{len(search['scope_and_result'])} 处：主仓库工作树与 git 全历史、主仓库 outputs 压缩件、数据根文本文件与压缩件及其 git 全历史、FAST-001 构建代码），"
            f"结论 {search['conclusion']}；唯一命中是本工作项上一候选自记的本次实测值，不是既存来源。故按修订 1 固定本次完整 sha256 "
            f"`{baseline['sha256']}`（{baseline['size_bytes']} 字节）为后续比对基线，**既往不可核**，不冒充既存来源记录。"
            f"补充（不是文件散列比对）：索引首行内容身份头与 `{identity['independent_record']}` 逐字段一致，上游两份目录文件当前 sha256 亦与之一致（{identity['match']}）。"
        )
        lines.append("")
    integrity = assets["frame_integrity"]
    lines.append(
        f"三序列 4,832 帧逐帧 JPEG sha 与 FAST-002 数据集清单一致（{integrity['jpeg_sha_checked']} 帧、不一致 {integrity['mismatches']}），sidecar `frame_id` 与文件名、"
        f"`simulation_time_s` 与 FAST-001 时刻索引一致（容差 {integrity['sim_time_tolerance_s']} s），不一致即停（H-2）。"
    )
    lines.append("")
    lines.append("**AC-4 口径偏差声明（承接 FAST-002 H-8）**：")
    lines.append("")
    lines.append(
        "1. 序列单位：E2 按帧目录会话分段（m3-armA 7 段各自新建关联器、窗口在段内），与 FAST-002 IR-4「按会话替代按族」同向；"
        "本项 E1 的 r 也只在同段内取（§3.9 字面「m3-armA：同段」）。"
    )
    counts = _excluded_red_counts()
    lines.append(
        f"2. scout-1 的 63 个 FAST-002 整帧排除帧（`TARGET_UNBOUNDED`：红车可见但无可用框）仍在回放中；本项真值取 FAST-001 目录索引，"
        f"这些帧红车 `dynamic` 为空 → 按「不可见」处理。影响：E2 红车窗口在这些帧按真值缺失扫描（同 FAST-002 偏差）；E1 红车样本的 k 帧不会取到这些帧，"
        f"但以它们为解析帧 r 的红车 (k,o,Δ) 共 {counts['red_r_in_excluded']} 个（干净臂，全部 gmc 同数）会被判 `…_INVISIBLE` 桶——其中若绑定红车 track 会记为 `BOUND_INVISIBLE`（误锁），"
        "即 scout-1 红车 false_lock 可能被高估、report_ok_invisible 可能被低估。"
    )
    lines.append("3. 本报告**不引用** FAST-002 的 G-5/G-6 读数或任何 H 域读数作为本项证据；H 域序列与 `frozen-H.jsonl.gz` 不读。")
    lines.append(
        "4. 检测来自冻结缓存（conf 0.25、imgsz 640、`device mps` 时算出）；scout-1、m3-armA 在检测器训练原子内（`TRAINED_ON_ATOM`，检测偏乐观），"
        "a7 为选择域（`SELECTION_DOMAIN`）。E1/E2 量的是关联与解析机制，不是检测器泛化。"
    )
    lines.append("")
    return lines


def _delta13_frame_gaps() -> dict[str, dict[str, int]]:
    result = {}
    for seq, segments in data.load_sequences(list(SEQS)).items():
        gaps = []
        for frames in segments:
            for k_index, frame in enumerate(frames):
                r = resolve_frame_index(frames, k_index, 13.0)
                if r is not None:
                    gaps.append(frames[r].frame_id - frame.frame_id)
        result[seq] = {"min": min(gaps), "max": max(gaps), "n": len(gaps)} if gaps else {"min": None, "max": None, "n": 0}
    return result


def _excluded_red_counts() -> dict[str, int]:
    excluded = set()
    with gzip.open(data.DATASET_FRAMES, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("excluded"):
                excluded.add(row["frame_id"])
    frames = data.load_sequences(["scout-1"])["scout-1"][0]
    total = 0
    for k_index, frame in enumerate(frames):
        if frame.red is None:
            continue
        for delta in DELTAS_S:
            r = resolve_frame_index(frames, k_index, delta)
            if r is not None and frames[r].path in excluded:
                total += 1
    return {"red_r_in_excluded": total}


def ledger_section(ledger: Mapping[str, Any]) -> list[str]:
    totals = ledger["totals"]
    lines = ["## 消耗", ""]
    lines.append(
        f"账本 `docs/evidence/P1-ENG-ACQ-001-ledger.json`：序列回放 {totals['sequence_replays']} / 40（27 次 E2/E1 关联回放 + AC-6 载体自测 4 次 × 2 条部分回放）；"
        f"本机 CPU 墙钟合计 {totals['cpu_wall_s']:.0f} s / 10,800 s；第二级 NanoTrack 起跟 {totals['level2_sot_runs']} 次、更新 {totals['level2_sot_frames']} 帧"
        "（旧候选各次运行：每 (k,o) ≤ 65 帧、每 序列×gmc×臂 ≤ 600 个 (k,o)；SUB:1/SUB:2 后的重跑：a7 全样本、其他序列 ≤ 600、每 (k,o) ≤ 66 帧；"
        "SUB:3 后的重跑：同上但 scout-1 每 (k,o) ≤ 87 帧；线束断言）；"
        "其余维度（ID/Play/API/VLM/GPU/检测推理/YOLO 权重加载/下载/pip/远端访问）全 0。"
        "失败、重复与作废运行同样计入：E1 干净臂第 1 次因 NanoTrack 实例驻留致内存增长被手动终止（46 s）；第一轮扰动臂第 2 次因后台命令重复启动而多跑一次；"
        "第一轮 E1 四次运行后加入「逐次指定相互独立」修正（交接 IR-20），两臂四次随即整体重跑，重跑输出与第一轮逐字节相同；"
        "信封修订 SUB:1/SUB:2 后 E1 两臂各两次整体重跑（续派 `P1-ENG-ACQ-001-K1K2K3-20260929T142800Z-9b04`，E1 解析计 0 次序列回放）；"
        "信封修订 SUB:3 后 E1 两臂再各两次整体重跑（续派 `P1-ENG-ACQ-001-K1K2K3-20260929T150551Z-e3c8`，0 次序列回放），证据取这一轮结果。"
        "C1 返工（派发 `P1-ENG-ACQ-001-K1K2K3-20260929T171016Z-c5a7`）只改 coasting 上限边界、常驻发布记录与限速基准，E1/E2 不受影响、未重跑，0 次序列回放。"
    )
    lines.append("")
    return lines


def main() -> int:
    e1 = common.read_json(common.evidence("e1.json"))
    e2 = common.read_json(common.evidence("e2.json"))
    assets = common.read_json(common.evidence("assets.json"))
    ledger = common.read_json(common.LEDGER_PATH)
    lines = [
        "# P1-ENG-ACQ-001 离线 E1/E2 报告（阶段 1；描述性）",
        "",
        "生成：`tools/eng_acq/report.py`（只读证据 JSON）。合同：提案 §3.9、AC-5/7/8/9/11/20 及修订 1、AC-7/20 修订 2/3、AR2-2 接受处置与「信封修订 SUB:1/SUB:2 落实」「信封修订 SUB:3 落实」。"
        "离线单进程、无 Unity 同机负载、无发布门；**不设资格门、不给通过/不通过、不外推为在线成绩**（§6）。",
        "",
    ]
    lines += e1_section(e1)
    lines += e2_section(e2)
    lines += deviation_section(assets)
    lines += ledger_section(ledger)
    common.atomic_write_bytes(common.evidence("report.md"), "\n".join(lines).encode("utf-8"))
    print("report written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
