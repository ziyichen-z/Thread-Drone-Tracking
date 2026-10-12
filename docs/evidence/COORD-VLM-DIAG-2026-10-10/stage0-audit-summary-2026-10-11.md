# 阶段 0 评估集审计摘要（2026-10-11，supervisor 照录；diagnostic_only、gate_evidence=false）

来源：派发 `COORD-VLM-DIAG-2026-10-10-阶段0审计-20261011T001529Z-e5e7`（实现子代理，Mac mini，零消耗：未跑模型、未联网、未下载安装、未写仓库）。输出在仓库外 `~/vlm-diag/COORD-VLM-DIAG-2026-10-10/stage0-20261011/`：`audit_stage0.py`（sha256 前缀 `3688beff34f7659a`）、`audit.json`（`7938ce564253e699`，812,096 B）、`run-log.txt`。子代理的 `.md` 写入被钩子拒绝，本摘要由 supervisor 依 `audit.json` 表格照录，表名见括号。未经独立复核，只作诊断读数。

## 输入与真值

- 四个输入 sha256 全部与 `P1-ENG-SFT-002` 数据集清单及 `eval-summary.json` 一致（eval `5d86013f`、select-eval `91ad8ed7`、C2 `0ccb4f1e`、零样本 `f6e31c38`）。
- 帧旁 json 只有传感器元数据、不含对象；对象真值取自 mini 数据根 `runtime/dist-data/frames_catalog/attempt-2/`（S3 目录，49 个分片按清单逐个核 sha）。609 行、448 帧全部有真值（`coverage_by_family`）。
- 真值与 gold 框一致（521 个目标，最大绝对差 1e-16）；现行 S/M/L 分层按可见框重算 451/451 一致——现行 gold 与分层本来就是可见框口径（`truth_consistency`）。

## 任务定义 1–5 项读数

1. **贴边与可见比例**（`t1_*`）：G1∪G2 单目标行中可见比例 < 1 的全部是贴边行，下限 0.25。C2 成功率随可见比例下降：比例 1 为 108/126，0.75–1 为 31/40，0.5–0.75 为 33/43，0.25–0.5 为 29/50；零样本对应 82/126、19/40、22/43、9/50（`G1_G2_success_by_ratio_bin`）。C2 答 none 的 30 行中 25 行可见比例 < 1（`c2_none_G1_G2_visible_ratio`）。
2. **每帧车辆数**（`t2_*`）：画面内车辆中位 5、p90 13、最多 18；可指代车辆中位 2、p90 5、最多 11。
3. **按 amodal 框重分层**（`t3_current_vs_amodal_stratum`）：G1∪G2 现行 S 层 43 行变为 S 22 / M 16 / L 5；现行 M 层 113 行中 21 行升为 L。目标车在上游已被裁剪的 24 行（G1t∪G2t 23、G3 1）拿不到 amodal 框，需重投影，本轮未推导（`dynamic_target_rows_amodal_unknown`）。
4. **失败构成**（`t4_*`）：C2 在 G1、G2、G4（含截断变体）上框落别处共 30 行，其中落在另一辆车上 25 行（不同类 17、同类 8），落在无对象处 5 行（`t4_c2_elsewhere_hit_success_groups`）。
5. **远处小目标**（不贴边且可见短边 < 32 px，`t5_far_small`）：G1∪G2 13 行（C2 成功 8、零样本 4；短边 22.5–31 px；car 5、taxi 4、container truck 3、pickup truck 1），连同 G4 共 32 行（C2 成功 23、零样本 5）。select-eval 的 unique S 层 133 行中 125 行不贴边（`select_eval_state_stratum_edge`）。

## 与初步读数（`eval-set-audit-prelim-2026-10-10.md`）的差异

主要计数全部复现。三处差异：S 层按贴边拆分表各漏计 1 行 ambiguous；S 层贴边长边中位 51.4 对 53 px、不贴边短边中位 27.2 对 28 px（差 1–2 px）；未截断车辆最小短边为 22.5 px，prelim「没有短边 < 23 px」不成立。

## 对待用户裁定两题有用的事实（不替用户选择）

- 部分可见对象的 gold 定义：现行 gold 已是可见框；截断行可见比例最低 0.25，C2 在 0.25–0.5 档仍有 58%（29/50）成功；改用 amodal 框需对 24 行目标车做重投影（本轮未做）。
- 远处小目标子集：评估集只有 13 行（加 G4 共 32 行），单档成功率置信区间很宽；训练侧 select-eval 有 125 行不贴边 S 层 unique 行。
