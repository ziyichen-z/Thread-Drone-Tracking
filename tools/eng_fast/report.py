"""报告与收口件（合同 §6.2、AC-1/7/8/9）：`-inputs.json`、`-ledger.json`、`-report.md`。

报告只按 §6.2 预注册读数表逐格填值，每格附证据指针与「不可推出」原文，不写「换栈/保留」结论句。
"""

from __future__ import annotations

import subprocess
from typing import Any, Mapping, Sequence

from tools.eng_fast import common, ledger

W = common.WORK_ID
EV = common.EVIDENCE_DIR


def _ev(name: str) -> Any:
    return common.read_json(EV / f"{W}-{name}")


def _md(text: str) -> str:
    """表格单元内的 `|` 会拆列：统一换成 ` · `。"""
    return str(text).replace("|", " · ")


def _pct(k: int | None, n: int | None) -> str:
    if not n:
        return "—"
    return f"{k}/{n}（{100.0 * k / n:.1f}%）"


def _cell(cell: Mapping[str, Any] | None) -> str:
    if not cell:
        return "—"
    return f"{_pct(cell['hit_030'], cell['n'])} / {_pct(cell['hit_050'], cell['n'])}"


# --- inputs.json / ledger.json ------------------------------------------------


def build_inputs() -> dict[str, Any]:
    stage = common.read_json(common.OUT_ROOT / "cache" / "stage-inputs.json")
    detect_identity = common.read_json(common.OUT_ROOT / "cache" / "detect-identity.json")
    document = {
        **stage,
        "detector_identity": detect_identity,
        "assertions_summary": {k: v["passed"] for k, v in stage["isolation_assertions"].items()},
        "note": "任一必需输入缺失、sha 不符、SPLIT_LOOKUP_MISSING 或交集非空即整体失败（inputs.InputFailure）；本文件存在即全部通过",
    }
    common.write_json(EV / f"{W}-inputs.json", document)
    return document["assertions_summary"]


def build_ledger() -> dict[str, Any]:
    before_rows = common.read_jsonl(common.OUT_ROOT / "ledger" / "runtime-before.jsonl.gz")
    after = ledger.runtime_manifest()
    common.write_jsonl(
        common.OUT_ROOT / "ledger" / "runtime-after.jsonl.gz",
        [{"root": after["root"], "files": after["files"], "tree_sha256": after["tree_sha256"]}]
        + [{"p": e[0], "b": e[1], "s": e[2]} for e in after["entries"]],
    )
    before_entries = {(r["p"], r["b"], r["s"]) for r in before_rows[1:]}
    after_entries = {tuple(e) for e in after["entries"]}
    porcelain = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "runtime"],
        capture_output=True,
        text=True,
        cwd=common.PROJECT_ROOT,
    ).stdout
    document = ledger.Ledger().load()
    document["runtime_readonly"] = {
        "before": before_rows[0],
        "after": {"files": after["files"], "tree_sha256": after["tree_sha256"]},
        "identical": before_rows[0]["tree_sha256"] == after["tree_sha256"],
        "added_or_changed": sorted(e[0] for e in after_entries - before_entries)[:50],
        "removed_or_changed": sorted(e[0] for e in before_entries - after_entries)[:50],
        "git_status_porcelain_runtime": porcelain,
        "method": "runtime/ 全树逐文件 (相对路径, 字节, sha256) 清单前后比对 + git status --porcelain -- runtime",
    }
    common.write_json(EV / f"{W}-ledger.json", document)
    return {"counters": document["counters"], "runtime_identical": document["runtime_readonly"]["identical"]}


# --- 报告 ---------------------------------------------------------------------


def build() -> dict[str, Any]:
    assertions = build_inputs()
    ledger_summary = build_ledger()
    recall = _ev("recall.json")
    margin = _ev("margin.json")
    replay = _ev("replay.json")
    arms = _ev("vlm-arms.json")
    latency = _ev("latency.json")
    lines: list[str] = []
    add = lines.append
    add(f"# {W} 快层替换探针报告（K4 候选；全离线、零 Play）\n")
    add("> 口径：全部数字是离线、桌面、oracle 候选或 oracle 参考条件下的描述性结果；gold 为 amodal 投影 AABB（`UNVERIFIED`）；")
    add("> 单次 greedy、单 seed，bootstrap 区间只作描述（2,000 轮，seed 20260923）。本报告只按合同 §6.2 逐格填值，**不给「换栈/保留」结论**，裁定归用户。")
    add("> 合同未写死处的实现读法逐条见 `docs/evidence/P1-ENG-FAST-001-K4-handoff.md`「实现读法（待裁定）」，交 `C1@K4` 裁定。\n")
    add(_section_inputs(assertions))
    add(_section_recall(recall))
    add(_section_legacy(recall))
    add(_section_margin(margin))
    add(_section_replay(replay))
    add(_section_arms(arms))
    add(_section_p4())
    add(_section_latency(latency))
    add(_section_readout(recall, margin, replay, arms, latency))
    add(_section_ledger(ledger_summary))
    add(_section_limits())
    text = "\n".join(lines).rstrip() + "\n"
    common.atomic_write_bytes(EV / f"{W}-report.md", text.encode("utf-8"))
    return {"report_bytes": len(text.encode("utf-8")), "ledger": ledger_summary, "assertions": assertions}


def _section_inputs(assertions: Mapping[str, bool]) -> str:
    stage = common.read_json(EV / f"{W}-inputs.json")
    rows = ["## 输入与身份（AC-1）\n", "证据：`docs/evidence/P1-ENG-FAST-001-inputs.json`。\n", "| 来源 | 帧 | 已配对真值 | 可见且带框 | 参考库 | 隔离断言 |", "|---|---|---|---|---|---|"]
    for key, source in stage["sources"].items():
        if "sequences" in source:
            frames = sum(s["frames"] for s in source["sequences"])
            paired = sum(s["paired"] for s in source["sequences"])
            visible = sum(s["visible_with_box"] for s in source["sequences"])
        else:
            frames, paired, visible = source["frames"], "—（目录对象）", "—"
        bank = stage["bank_of_source"][key]
        status = stage["banks"][bank]
        rows.append(
            f"| {key} | {frames} | {paired} | {visible} | {bank}：车 `{status['vehicle_status']}`、红立方体 `{status['target_primitive_status']}` | "
            f"{'通过' if assertions[key] else '失败'} |"
        )
    rows.append("")
    for name, bank in stage["banks"].items():
        refs = [f"`{r['frame_id'].split('/')[-3]}/{r['frame_id'].split('/')[-1]}`（{', '.join(b['class_word'] for b in r['boxes'])}）" for r in bank["vehicle"]]
        prim = bank["target_primitive"]
        rows.append(
            f"- 参考库 `{name}`（池 = {'train 原子 {a2}' if name == 'a2' else 'train∪dev 原子'}）：车辆参考帧 {len(refs)} 张 {'; '.join(refs)}；"
            f"红立方体参考帧 {('`' + prim['frame_id'].split('/')[-1] + '`') if prim else '无'}（`same_instance_by_design`）。"
        )
    rows.append("")
    return "\n".join(rows)


def _table_rows(table: Mapping[str, Any], label: str, kinds: Sequence[str], axis: str = "by_distance") -> list[str]:
    out = []
    for key, value in table.items():
        if "status" in value and len(value) == 1:
            continue
        kind = key.split("|")[0]
        if kind not in kinds:
            continue
        cells = value[axis]
        order = [*common.DISTANCE_BINS, "NA"] if axis == "by_distance" else [*common.STRATA, "NA"]
        bank = f"（{value['bank_status']}）" if "bank_status" in value else ""
        out.append(f"| {_md(label)} | {_md(key)}{bank} | " + " | ".join(_cell(cells.get(b)) for b in order) + " |")
    return out


def _section_recall(recall: Mapping[str, Any]) -> str:
    rows = ["## P1 分桶召回（AC-2）\n", "证据：`docs/evidence/P1-ENG-FAST-001-recall.json`（逐格 `hit/n`、95% CI、FP/帧、适用域矩阵；全交叉 短边×距离 表在 JSON）。每格写「IoU≥0.30 / IoU≥0.50」。\n"]
    for axis_name, axis_title in (("slant_range", "斜距表（scout-1 / scout-4 / BODY-001）"), ("axial_depth", "轴向深度表（609 行的 448 目录帧；表头为相机**轴向深度**，不与斜距合并）")):
        rows.append(f"### {axis_title}\n")
        rows.append("按距离档：\n")
        rows.append("| 来源 × 检测器 | 种类 × 实例标记 | <35 | 35–50 | 50–65 | ≥65 | NA |")
        rows.append("|---|---|---|---|---|---|---|")
        for label, table in recall["tables"][axis_name].items():
            if "status" in table:
                rows.append(f"| {_md(label)} | — | `{table['status']}` | | | | |")
                continue
            rows.extend(_table_rows(table, label, (common.TARGET_KIND_CATALOG, common.TARGET_KIND_PRIMITIVE)))
        rows.append("\n按短边层：\n")
        rows.append("| 来源 × 检测器 | 种类 × 实例标记 | S | M | L | NA |")
        rows.append("|---|---|---|---|---|---|")
        for label, table in recall["tables"][axis_name].items():
            if "status" in table:
                continue
            rows.extend(_table_rows(table, label, (common.TARGET_KIND_CATALOG, common.TARGET_KIND_PRIMITIVE), "by_stratum"))
        rows.append("")
    rows.append("### FP/帧（描述性，不与任何决策计数比较）\n")
    rows.append("| 来源 × 检测器 | 帧 | 检测数 | 未匹配检测 | FP/帧 |")
    rows.append("|---|---|---|---|---|")
    for label, fp in recall["fp_per_frame"].items():
        rows.append(f"| {_md(label)} | {fp['frames']} | {fp['detections']} | {fp['unmatched_detections']} | {fp['fp_per_frame']} |")
    rows.append("\n注：scout 真值只列 1–2 辆干扰车、BODY 真值不列干扰车，真值清单之外的场景车辆被检出也计为未匹配。T1a/T1b 未签发，所有格 `N/A(NOT_AUTHORIZED_T1_UNSIGNED)`；T0-oracle 在 BODY/目录帧为 `N/A(NO_SESSION_REFERENCE)`。\n")
    return "\n".join(rows)


def _section_legacy(recall: Mapping[str, Any]) -> str:
    rows = ["## T0-oracle 旧数复算（AC-3）\n", "| 来源 | 旧数 | 复算 | 逐 tick 命中不一致 | 与旧 max IoU 最大差 | 处置 |", "|---|---|---|---|---|---|"]
    for source, item in recall["legacy_alignment"].items():
        rows.append(
            f"| {source} | {item['expected']['hits']}/{item['expected']['denominator']} | {item['recomputed']['hits']}/{item['recomputed']['denominator']} | "
            f"{len(item['per_tick_hit_mismatches'])} | {item['max_abs_iou_delta_vs_legacy']} | `{item['disposition']}` |"
        )
    rows.append("\n口径：以旧结果逐 tick 样本为 tick 计划（同阈值 conf≥0.25、IoU≥0.30；scout-1 的 `MISSING_*` tick 按旧政策计为漏）。\n")
    return "\n".join(rows)


def _section_margin(margin: Mapping[str, Any]) -> str:
    rows = ["## P2a 静态 margin（AC-4）\n", "证据：`docs/evidence/P1-ENG-FAST-001-margin.json`（逐对记录、分层/分类别统计）。嵌入器 = 冻结 DINOv2 ViT-S/14。\n"]
    rows.append("| Δ | 合格帧对 | 选取 | 计分 | CROP_INVALID | margin p50 | margin ≥0.1 | 自身 cos ≥0.5 | S 层 ≥0.1 | M 层 ≥0.1 | L 层 ≥0.1 |")
    rows.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for delta, entry in sorted(margin["summary"].items(), key=lambda item: float(item[0].rstrip("s"))):
        strata = entry["by_stratum"]
        rows.append(
            f"| {delta} | {entry['eligible_pairs']} | {entry['selected_pairs']} | {entry['scored']} | {entry['crop_invalid']} | {entry['margin']['p50']} | "
            f"{_pct(entry['margin_ge_0_1'], entry['scored'])} | {_pct(entry['self_ge_0_5'], entry['scored'])} | "
            + " | ".join(_pct(strata[s]["margin_ge_0_1"], strata[s]["scored"]) for s in common.STRATA)
            + " |"
        )
    rows.append("")
    return "\n".join(rows)


def _section_replay(replay: Mapping[str, Any]) -> str:
    rows = ["## P2b 序列回放（AC-5）\n"]
    if replay.get("status") != "RUN":
        rows.append(f"`{replay.get('status')}`：{replay.get('error')}\n")
        return "\n".join(rows)
    rows.append(f"证据：`docs/evidence/P1-ENG-FAST-001-replay.json`。`lap {replay['lap_version']}`、ultralytics {replay['ultralytics_version']}；接口：{replay['interface']}。")
    rows.append("保持率 = KEPT / D，D = KEPT + ID_SWITCH + LOST_BEYOND_BUFFER + UNRESOLVED_END_MISS（`UNRESOLVED_END_MISS` 计入分母、不算保持，读数偏保守）。\n")
    rows.append("| 序列 | 算法 | W | V | 排除（UNBOUND/CENSORED/TRUTH_GAP） | KEPT | ID_SWITCH | LOST>buffer | UNRESOLVED_END | 保持率 | drift_return（其中 L=31） |")
    rows.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for name, sequence in replay["sequences"].items():
        if "per_algorithm" not in sequence:
            rows.append(f"| {name} | — | — | `{sequence.get('status')}` | | | | | | | |")
            continue
        for algorithm, data in sequence["per_algorithm"].items():
            for window, s in data["windows"].items():
                rows.append(
                    f"| {name} | {algorithm} | {window} | {s['V']} | {s['UNBOUND_START']}/{s['CENSORED_END']}/{s['TRUTH_GAP']} | {s['KEPT']} | {s['ID_SWITCH']} | "
                    f"{s['LOST_BEYOND_BUFFER']} | {s['UNRESOLVED_END_MISS']} | {s['retention'] if s['retention'] is not None else '—'} | {s['drift_return']}（{s['drift_return_at_L_eq_buffer_plus_1']}） |"
                )
    rows.append("\n序列级（ByteTrack）：\n")
    rows.append("| 序列 | 帧 | 可见 | 绑定 | ID 切换 | 碎片 | 最长同 ID 秒 | 帧间隔 p50 s | 30 次调用 ≈ 秒 |")
    rows.append("|---|---|---|---|---|---|---|---|---|")
    for name, sequence in replay["sequences"].items():
        if "per_algorithm" not in sequence:
            continue
        m = sequence["per_algorithm"]["bytetrack"]["sequence"]
        rows.append(
            f"| {name} | {m['frames']} | {m['visible_frames']} | {m['bound_frames']} | {m['id_switches']} | {m['fragments']} | {m['longest_same_id_s']} | "
            f"{m['frame_interval_s']['p50']} | {m['track_buffer_median_seconds']} |"
        )
    rows.append("\n库边界实测（`test_library_buffer_boundary`，两算法相同）：空检测 30 次调用 → 同 ID；**31 次 → 仍同 ID**；32 次 → 新 ID。与事实 20 的读码结论差 1 帧（IR-8）；判定阈值仍按 §3.4 字面（L ≥ 31 → `LOST_BEYOND_BUFFER`），L = 31 的原 ID 找回列在 drift_return 括号内。\n")
    return "\n".join(rows)


def _group_cell(entry: Mapping[str, Any], metric: str) -> str:
    value = entry.get(metric)
    return _pct(value["k"], value["n"]) if value else "—"


def _section_arms(arms: Mapping[str, Any]) -> str:
    rows = ["## P3 VLM 四臂（AC-6）\n", "证据：`docs/evidence/P1-ENG-FAST-001-vlm-arms.json`（逐行结果、逐查询 prompt sha/解码参数/token/时延、配对 2×2）。"]
    rows.append(f"候选集口径：{arms['candidate_set_reading']}；K=0 行 {arms['k0_rows']}（确定性 none、零查询、计入各分母）。臂 A 零新查询（既有文件 sha 见 inputs.json）。\n")
    q = arms["queries"]
    rows.append(
        f"查询：基线 B {q['baseline']['B']}/{q['planned_baseline'].get('B')}、C {q['baseline']['C']}/{q['planned_baseline'].get('C')}；重试 B {q['retry']['B']}、C {q['retry']['C']}；"
        f"合计 {q['total']}（5060 账本 {q['remote_budget']['used']}）；停臂 {q['stopped_arms'] or '无'}；smoke {q['smoke']}；Mac 复解析不一致 {len(q['reparse_mismatch'])}。\n"
    )
    labels = ("A_base", "A_C2", "B", "C", "D")
    rows.append("G3p 即合同的 G3′（诊断组，不进任何门）；LEGACY_ONLY 8 行排除所有报表。\n")
    rows.append("| 组（指标） | " + " | ".join(labels) + " |")
    rows.append("|---|" + "---|" * len(labels))
    groups = [
        ("G1", "success"), ("G1t", "success"), ("G2", "success"), ("G2t", "success"), ("G4", "success"),
        ("G3", "report"), ("G3", "strict"), ("G3t", "report"), ("G3t", "strict"), ("G5", "none"), ("G3p", "report"), ("G3p", "any_member"),
    ]
    for group, metric in groups:
        rows.append(f"| {group}（{metric}） | " + " | ".join(_group_cell(arms["scores"][a]["groups"].get(group, {}), metric) for a in labels) + " |")
    for metric in ("false_none", "false_ambiguous"):
        rows.append(f"| G1∪G2（{metric}） | " + " | ".join(_pct(arms["scores"][a]["g1_g2_false_rates"][metric]["k"], arms["scores"][a]["g1_g2_false_rates"][metric]["n"]) for a in labels) + " |")
    rows.append("\n分层（成功组 success，S / M / L）：\n")
    rows.append("| 组 | " + " | ".join(labels) + " |")
    rows.append("|---|" + "---|" * len(labels))
    for group in ("G1", "G2", "G4", "G1t", "G2t"):
        cells = []
        for a in labels:
            by = arms["scores"][a]["groups"].get(group, {}).get("success_by_stratum", {})
            cells.append(" / ".join(_pct(by[s]["k"], by[s]["n"]) if s in by else "—" for s in common.STRATA))
        rows.append(f"| {group} | " + " | ".join(cells) + " |")
    rows.append("\n计数（臂 A 的 `NO_CANDIDATE_MATCH`/`PARSE_ERROR`；B/C 的 `INVALID`/`NOT_RUN`；B/C/D 的 `K0`）：\n")
    for a in labels:
        rows.append(f"- {a}：{arms['scores'][a]['counts']}（`no_flag` = 无标记的正常输出行）")
    rows.append("\n配对诊断（§3.5.4；成功组逐行 `{det_hit × arm_ok}`，det_hit = T0-bank-td cpu 对 gold 对象 max IoU ≥ 0.3）。**这是同一行上两种独立测量的交集，不是任何链路的成功率或上界；B/C 的裁图/框来自 oracle 候选，改用检测器框后 VLM 的成绩未测量。**\n")
    rows.append("| 臂 | n | hit∧ok | hit∧fail | miss∧ok | miss∧fail | P(ok∧hit) | P(ok｜hit) |")
    rows.append("|---|---|---|---|---|---|---|---|")
    for a in labels:
        d = arms["paired_diagnostic"][a]["ALL_SUCCESS_GROUPS"]
        t = d["table"]
        rows.append(f"| {a} | {d['n']} | {t['det_hit__arm_ok']} | {t['det_hit__arm_fail']} | {t['det_miss__arm_ok']} | {t['det_miss__arm_fail']} | {d['P_arm_ok_and_det_hit']} | {d['P_arm_ok_given_det_hit']} |")
    rows.append("\n臂 A 的 SFT-002 原 IoU 口径成绩原样引用（不重算）：`docs/reviews/P1-ENG-SFT-002-stage-summary.md` §4–§5（C2：G1 76.7%、S 层 36.7%；G2 81.6%；G4 82.6%；G1t/G2t 65.2%；base：G1∪G2 51.0%、G4 8.1%）。")
    d = arms["armd_disclosure"]
    rows.append(f"\n臂 D 披露：裁图库 {d['bank']['embedded']} 张 / {d['bank']['objects']} 个对象（每对象 ≤{d['bank']['per_object_cap']}、短边 ≥{d['bank']['min_short_side_px']} px）；颜色原型 {d['prototypes']['colors']}。库内对象与评估候选多为同一场景实例（静态车辆跨族复现），逐候选 `same_instance_in_bank` 见 armd 缓存。\n")
    return "\n".join(rows)


def _section_p4() -> str:
    return "\n".join(
        [
            "## P4 与 DETECT-001 的关系（AC-7）\n",
            "- **验收 4 缺口原文**（`docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md` 验收 4 / 合同事实 3）：「背景锁定打破测试」——冻结 B2 困难场景、含 t≈40 s 交接点的 ≥150 s 窗口、incorrect/matched < 0.5 且 ≥1 次三门通过的 DISAGREE 重播种——**从未运行**，是该项未闭的证据缺口。",
            "- **qual-3 数字读法**：detector 节奏 75/75 是检测**节奏**达成，不是召回；决策 AGREE 36 / TENTATIVE 19 / NO_CANDIDATE 20 是三门**决策计数**，不是 FP，本报告的 FP/帧不与之并列；零 REANCHOR。",
            "- **本项复用的冻结件**：`config/detector-reanchor.models.json`（阈值 0.25、`imgsz` 640、权重/源码 sha 与 torch/ultralytics 钉版）、`controller/reanchor_models.YoloeProposer`（T0-oracle 与 T0-bank 的 YOLOE 构造与视觉提示路径）、`DinoV2Embedder`（P2a 与臂 D），全部只导入、零字节改动。",
            "- **差异**：DETECT-001 的检测器每 2 s 一次、以同会话初始化框为单类提示并经三门决策；本项 T0-bank 以跨会话参考库（原子隔离）固定两类嵌入、逐帧检测、类别无关计分，T0-oracle 只用于与 scouting 旧数对齐；本项不做决策门、不重播种、不接入运行时。",
            "- **本项不闭合该缺口**：验收 4 需要困难场景 Play，本项零 Play（合同 §2.2-6）。",
            "- **待复现风险**：(1) 远端（≥65 m）召回与 scouting 0/45 同源几何，在线 5 Hz、同机 Unity 负载下未测；(2) 背景锁定的触发机制（模板交接给静态背景）属于 NanoTrack，本项的检测+关联路线未在 B2 困难场景回放；(3) 参考库单来源（{a2}）条件下的 T0-bank 数字换参考库可能不同；(4) 红立方体只有同一锚点、同一路线的样本。\n",
        ]
    )


def _section_latency(latency: Mapping[str, Any]) -> str:
    d = latency["detection_ms"]
    rows = [
        "## 时延（AC-10；只报 Mac 桌面数字）\n",
        f"主机：{latency['host']['chip']}，torch {latency['host']['torch']}，ultralytics {latency['host']['ultralytics']}；同机 Unity 运行：{'是' if latency['unity_running_same_host'] else '否'}。\n",
        "| 项 | CPU p50 / p95 ms | MPS p50 / p95 ms |",
        "|---|---|---|",
        f"| T0 检测（{d['cpu']['frames']} 帧，含预处理） | {d['cpu']['p50']} / {d['cpu']['p95']} | {d['mps']['p50']} / {d['mps']['p95']} |",
        f"| DINOv2 单裁图 | {latency['dinov2_single_crop_ms']['cpu']['p50']} / {latency['dinov2_single_crop_ms']['cpu']['p95']} | {latency['dinov2_single_crop_ms']['mps']['p50']} / {latency['dinov2_single_crop_ms']['mps']['p95']} |",
        f"| ByteTrack `update` | {latency['bytetrack_update_ms_cpu']['p50']} / {latency['bytetrack_update_ms_cpu']['p95']} | — |",
        f"\nCPU/MPS 框一致性：{latency['cpu_mps_box_consistency']}。\n",
    ]
    return "\n".join(rows)


def _fmt_cells(table: Mapping[str, Any], kind: str, bins: Sequence[str]) -> str:
    out = []
    for key, value in table.items():
        if not key.startswith(kind) or "by_distance" not in value:
            continue
        for b in bins:
            cell = value["by_distance"].get(b)
            if cell:
                out.append(f"{key.split('|')[1]} {b}: {_cell(cell)}")
    return "；".join(out) or "—"


def _section_readout(recall, margin, replay, arms, latency) -> str:
    tables = recall["tables"]["slant_range"]
    default = next(v for k, v in tables.items() if k.startswith("default-geometry"))
    body = next(v for k, v in tables.items() if k.startswith("body-all"))
    r1_catalog = _fmt_cells(default, common.TARGET_KIND_CATALOG, ("50-65", ">=65"))
    if r1_catalog == "—":
        r1_catalog = "无斜距格（scout 干扰车真值不带斜距、BODY 真值不列干扰车，目录车全部落 NA 档，见斜距表）"
    r1 = "目录车：" + r1_catalog + "。红立方体：" + _fmt_cells(default, common.TARGET_KIND_PRIMITIVE, ("50-65", ">=65"))
    prim = body.get(f"{common.TARGET_KIND_PRIMITIVE}|same_instance_by_design", {})
    r2 = "；".join(f"{s}: {_cell(prim.get('by_stratum', {}).get(s))}" for s in common.STRATA) if prim else "—"
    r3 = "；".join(f"{_md(k)}: {v['fp_per_frame']}" for k, v in recall["fp_per_frame"].items())
    r4_parts = []
    undefined = []
    if replay.get("status") == "RUN":
        for name, sequence in replay["sequences"].items():
            if "per_algorithm" not in sequence:
                continue
            windows = {a: d["windows"] for a, d in sequence["per_algorithm"].items()}
            if all(w[k]["D"] == 0 for w in windows.values() for k in w):
                undefined.append(name)
                continue
            r4_parts.append(
                f"{name}：" + "，".join(
                    f"{a} 8s {w['8s']['retention']}（D={w['8s']['D']}）/13s {w['13s']['retention']}（D={w['13s']['D']}）"
                    for a, w in windows.items()
                )
            )
    r4 = "；".join(r4_parts) if r4_parts else f"`{replay.get('status')}`"
    if undefined:
        r4 += f"；D=0（保持率不可定义：无可见帧或起点全部无绑定）：{'、'.join(undefined)}"
    r5 = "；".join(
        f"Δ{d}: " + " / ".join(_pct(e["by_stratum"][s]["margin_ge_0_1"], e["by_stratum"][s]["scored"]) for s in common.STRATA)
        for d, e in margin["summary"].items()
    )

    def s_rate(arm: str, group: str) -> str:
        by = arms["scores"][arm]["groups"].get(group, {}).get("success_by_stratum", {})
        return _pct(by["S"]["k"], by["S"]["n"]) if "S" in by else "—"

    r6 = "；".join(f"{a} G1-S {s_rate(a, 'G1')}" for a in ("A_base", "A_C2", "B", "C"))
    r7 = "；".join(
        f"{a} G1 {_group_cell(arms['scores'][a]['groups']['G1'], 'success')}、G2 {_group_cell(arms['scores'][a]['groups']['G2'], 'success')}、"
        f"G4 {_group_cell(arms['scores'][a]['groups']['G4'], 'success')}、G3 严格 {_group_cell(arms['scores'][a]['groups']['G3'], 'strict')}"
        for a in ("B", "C", "D")
    )
    d = latency["detection_ms"]
    r8 = f"CPU p95 {d['cpu']['p95']} ms、MPS p95 {d['mps']['p95']} ms（5 Hz 预算 200 ms）"
    rows = [
        "## 读数表（§6.2 预注册；AC-8）\n",
        "「读法」全部是条件句、描述性，供用户裁定；「不可推出」为硬约束。本表不含「换栈/保留」结论。\n",
        "| 格 | 取值（证据） | 参考线 | 读法（条件性） | 不可推出 |",
        "|---|---|---|---|---|",
        f"| R1 默认几何远端召回（T0-bank，scout-1 + BODY，≥50/≥65 m，IoU 0.30 / 0.50） | {r1}（recall.json `default-geometry`） | scout-1 T0-oracle 0/45（≥65 m）；VLM C2 S 层 36.7% | 若远端召回接近 0，则预训练检测器不能覆盖默认路线远端，换栈需另立数据/模型工作；若明显非零，则「持续检测」在远端有输入 | 任何闭环跟踪成绩；在线 5 Hz 下的召回 |",
        f"| R2 脚本红车召回（BODY 全档，S/M/L） | {r2}（recall.json `body-all`） | 无既有证据 | 若目录车可检而红立方体不可检，则演示目标本身是换栈的阻断项，需换目标外观或换样例策略 | 换成网格车后的召回 |",
        f"| R3 FP/帧（描述性） | {r3}（recall.json `fp_per_frame`） | 无同口径既有证据（qual-3 的 NO_CANDIDATE/TENTATIVE 是决策计数，不并列） | 若 FP/帧高，则关联层每帧要在更多干扰候选中匹配；配合 R5 读 | 换 ID 频率（由 R4 直接测量） |",
        f"| R4 8 s / 13 s 窗口 ID 保持率 | {r4}（replay.json） | 指定→确认实测 8–13 s 只给出窗口长度来历 | 离线回放是必要条件读法：若离线也保不住，则在线更难；若离线保得住，只说明归档几何上关联层不先天失败；须与 R1 并读区分「检测不到」与「关联丢 ID」 | 在线可行性；真实指定期的保持率；同机负载下的表现 |",
        f"| R5 静态 margin ≥0.1 通过率（S / M / L） | {r5}（margin.json） | scout-4 174/187、scout-1 0 机会 | 若 S 层通过率低，则同类多车场景仍需 ReID 或人工，定局 ④ 不变 | 训练后的 ReID 能力 |",
        f"| R6 臂 B/C 相对 A(base)/A(C2) 的 S 层差值（oracle 候选） | {r6}（vlm-arms.json） | A(C2) G1 S 36.7%（原 IoU 口径）、G1t/G2t 65.2% | 若 oracle 候选下裁图/编号选择显著高于整帧，则值得另立探针用检测器候选复测 B/C；若不高，则裁图放大不是 S 层的出路 | 检测器候选下的成绩；任何架构结论 |",
        f"| R7 臂 D 相对各 VLM 臂（oracle 候选） | {r7}（vlm-arms.json） | — | 若 D 在 G1/G2 接近 B/C，则这两类指令的选择步骤有无 VLM 替代方案值得另测；G3/G4 另看 | 「不需要 VLM」；检测器候选下的成绩 |",
        f"| R8 Mac 检测 p95 与 5 Hz 预算 200 ms | {r8}（latency.json） | DETECT-001 detector 74–98 ms（CPU） | 若 p95 > 200 ms，则桌面 5 Hz 持续检测在本机不成立（与 Jetson 无关）；若 ≤，则只说明单模型单进程可达 | 同机 Unity 负载下的时延；Jetson 时延 |",
        "",
    ]
    return "\n".join(rows)


def _section_ledger(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "## 账目与只读（AC-9）\n",
            f"证据：`docs/evidence/P1-ENG-FAST-001-ledger.json`。计数：{summary['counters']}；`runtime/` 前后全树清单一致：{summary['runtime_identical']}。零 Play、零 ID、零训练、零云端；产物只在 `outputs/eng-fast/` 与 `docs/evidence/`。\n",
        ]
    )


def _section_limits() -> str:
    return "\n".join(
        [
            "## 限制与不承诺（§6.1 摘要）\n",
            "1. 离线、桌面、oracle 候选/参考条件下的描述性结果；T0-oracle 只是 oracle-pointed 可检测性上界；配对表只是同行交集。",
            "2. gold 为 amodal 投影 AABB（`UNVERIFIED`）；目录帧距离是相机轴向深度，与斜距分表不混算。",
            "3. C2 adapter 不套用到 B/C；A(base) 才是 B/C 的同模型对照。",
            "4. 回放不含 Unity 同机负载、云台/机身闭环、5 Hz 实时约束与 K1 发布门；保持率不是闭环跟踪主张。",
            "5. 红立方体只有同一锚点、同一路线的样本；其他路线/光照无证据。",
            "6. 不主张 Jetson/TensorRT 性能、开放词表、真实航拍、跨环境；不闭合 DETECT-001 验收 4；不改任何 LOOP-001 verdict。",
            "7. 单次 greedy、单 seed；bootstrap CI 只是描述性区间；不冻结任何合格线。",
            "8. 评 scout-1 与 arm A 时参考池只有 {a2}（`BANK_PARTIAL(5/9)`），相应 T0-bank 数字是「单来源参考库」条件下的数字。",
            "9. 保持率分母把 `UNRESOLVED_END_MISS` 算作未保持，读数偏保守；须与 R1 远端召回并读。",
        ]
    )
