# P1-ENG-ACQ-001 离线 E1/E2 报告（阶段 1；描述性）

生成：`tools/eng_acq/report.py`（只读证据 JSON）。合同：提案 §3.9、AC-5/7/8/9/11/20 及修订 1、AC-7/20 修订 2/3、AR2-2 接受处置与「信封修订 SUB:1/SUB:2 落实」「信封修订 SUB:3 落实」。离线单进程、无 Unity 同机负载、无发布门；**不设资格门、不给通过/不通过、不外推为在线成绩**（§6）。

## E1

陈旧指定解析（§3.9；AC-7 修订 1/2/3 / AC-20 修订 1/2/3）。样本 (k, o) = 序列帧 k × k 帧 OK 可见对象；Δ ∈ {1, 2, 4.2, 5.4, 8, 13} s；解析帧 r = 同段内首个 t ≥ t_k + Δ 的帧；每个 (k, o, Δ) 落入 15 桶之一，逐层逐 Δ 守恒（线束断言 + `tests/test_eng_acq_e1.py`）。干净臂 = 真值框；扰动臂 `c2_quantiles` = 固定种子缩放 + 平移。分层 = 序列 × {静止, 红车} × S/M/L × gmc_source × 臂，完整 648 行（含空层）在 `docs/evidence/P1-ENG-ACQ-001-e1.json`「layers」。**读数只作描述，不设门，不外推为在线捕获成功率。**

**复现**（固定种子两次运行字节一致）：`c2_quantiles` 2 次 → byte_identical = True（sha256 7a699b76cffd…）；`none` 2 次 → byte_identical = True（sha256 74cadc028333…）。

**层状态**：{"EVALUATED": 648}（648 = 2 臂 × 3 序列 × 2 类 × 3 尺寸 × 3 gmc × 6 Δ）。

### 第二级代价与 AR2-2 / 每 (k,o) 帧上限（信封修订 SUB:1/SUB:2/SUB:3）

| 序列 / gmc / 臂 | (k,o) 样本 | 第二级触发 | 运行（上限） | LEVEL2_SUBSAMPLED | 每 (k,o) 帧上限 | 超帧上限未运行 (k,o,Δ) |
|---|---|---|---|---|---|---|
| a7/none/c2_quantiles | 6458 | 1637 | 1637（full_sample） | False | 66 | 0 |
| a7/none/none | 6458 | 1213 | 1213（full_sample） | False | 66 | 0 |
| a7/optflow/c2_quantiles | 6458 | 1214 | 1214（full_sample） | False | 66 | 0 |
| a7/optflow/none | 6458 | 757 | 757（full_sample） | False | 66 | 0 |
| a7/pose/c2_quantiles | 6458 | 1124 | 1124（full_sample） | False | 66 | 0 |
| a7/pose/none | 6458 | 659 | 659（full_sample） | False | 66 | 0 |
| m3-armA/none/c2_quantiles | 2605 | 306 | 306（600） | False | 66 | 0 |
| m3-armA/none/none | 2605 | 106 | 106（600） | False | 66 | 0 |
| m3-armA/optflow/c2_quantiles | 2605 | 306 | 306（600） | False | 66 | 0 |
| m3-armA/optflow/none | 2605 | 106 | 106（600） | False | 66 | 0 |
| m3-armA/pose/c2_quantiles | 2605 | 306 | 306（600） | False | 66 | 0 |
| m3-armA/pose/none | 2605 | 106 | 106（600） | False | 66 | 0 |
| scout-1/none/c2_quantiles | 2240 | 214 | 214（600） | False | 87 | 0 |
| scout-1/none/none | 2240 | 74 | 74（600） | False | 87 | 0 |
| scout-1/optflow/c2_quantiles | 2240 | 212 | 212（600） | False | 87 | 0 |
| scout-1/optflow/none | 2240 | 68 | 68（600） | False | 87 | 0 |
| scout-1/pose/c2_quantiles | 2240 | 207 | 207（600） | False | 87 | 0 |
| scout-1/pose/none | 2240 | 62 | 62（600） | False | 87 | 0 |

现行上限（提案决策记录「信封修订 SUB:1/SUB:2 落实」与「信封修订 SUB:3 落实」（2026-09-29；CLARIFY），AC-7/AC-20 修订 3）：a7 的第二级触发 (k,o) 在每个 gmc_source × 臂**全样本运行**；scout-1、m3-armA 每（序列 × gmc × 臂）≤ 600；每 (k,o) SOT 帧上限按序列取值：a7 ≤ 66、m3-armA ≤ 66、scout-1 ≤ 87（各 Δ 共用前缀）。本次抽样组合：无；有超帧上限未运行 (k,o,Δ) 的组合：无。未运行的 (k,o,Δ) 不入 15 桶、不计 `NO_TRACK_AT_K` 或成功；其所在层记 `NOT_EVALUABLE_AR2-2`（抽样）或 `NOT_EVALUABLE_FRAME_CAP`（帧上限），比例只作子样本诊断（`ratios_scope = subsample_diagnostic_only`）。层状态合计：{"EVALUATED": 648}。旧候选（65 帧、a7 抽 600；及 66 帧下 scout-1 Δ13 的 32 层）的 `NOT_EVALUABLE_*` 读数不追溯改判，本报告全部取本次重跑结果。

Δ = 13 s 解析帧与 k 帧的帧号差（全部 k，只读元数据）：scout-1 77–87（n = 685）；m3-armA 65–66（n = 437）；a7 65–66（n = 3103）。按序列帧上限核对：scout-1 需 ≤ 87 帧、上限 87，已覆盖；m3-armA 需 ≤ 66 帧、上限 66，已覆盖；a7 需 ≤ 66 帧、上限 66，已覆盖。本次无 `NOT_EVALUABLE_FRAME_CAP` 层（含 scout-1 Δ13）。

### 臂 `none`：resolve_ok / false_lock（跨 S/M/L 汇总；非 EVALUATED 格标注状态）

| 序列 | 类 | gmc | Δ=1s | Δ=2s | Δ=4.2s | Δ=5.4s | Δ=8s | Δ=13s |
|---|---|---|---|---|---|---|---|---|
| scout-1 `TRAINED_ON_ATOM` | static | pose | 0.999 / 0.062 (n_vis 1412) | 0.995 / 0.098 (n_vis 1304) | 0.987 / 0.135 (n_vis 1123) | 0.985 / 0.144 (n_vis 1034) | 0.983 / 0.158 (n_vis 866) | 0.972 / 0.158 (n_vis 612) |
| scout-1 `TRAINED_ON_ATOM` | static | optflow | 0.989 / 0.063 (n_vis 1412) | 0.967 / 0.096 (n_vis 1304) | 0.919 / 0.125 (n_vis 1123) | 0.904 / 0.136 (n_vis 1034) | 0.889 / 0.149 (n_vis 866) | 0.938 / 0.154 (n_vis 612) |
| scout-1 `TRAINED_ON_ATOM` | static | none | 0.979 / 0.081 (n_vis 1412) | 0.958 / 0.130 (n_vis 1304) | 0.917 / 0.167 (n_vis 1123) | 0.899 / 0.160 (n_vis 1034) | 0.883 / 0.162 (n_vis 866) | 0.935 / 0.156 (n_vis 612) |
| scout-1 `TRAINED_ON_ATOM` | red | pose | 0.912 / 0.068 (n_vis 660) | 0.912 / 0.089 (n_vis 645) | 0.878 / 0.100 (n_vis 632) | 0.872 / 0.094 (n_vis 624) | 0.842 / 0.081 (n_vis 602) | 0.814 / 0.067 (n_vis 569) |
| scout-1 `TRAINED_ON_ATOM` | red | optflow | 0.906 / 0.060 (n_vis 660) | 0.891 / 0.073 (n_vis 645) | 0.842 / 0.072 (n_vis 632) | 0.827 / 0.074 (n_vis 624) | 0.772 / 0.084 (n_vis 602) | 0.717 / 0.071 (n_vis 569) |
| scout-1 `TRAINED_ON_ATOM` | red | none | 0.920 / 0.060 (n_vis 660) | 0.929 / 0.073 (n_vis 645) | 0.907 / 0.074 (n_vis 632) | 0.899 / 0.071 (n_vis 624) | 0.870 / 0.081 (n_vis 602) | 0.822 / 0.087 (n_vis 569) |
| m3-armA `TRAINED_ON_ATOM` | static | pose | 1.000 / 0.003 (n_vis 1835) | 1.000 / 0.002 (n_vis 1761) | 1.000 / 0.002 (n_vis 1598) | 1.000 / 0.003 (n_vis 1505) | 1.000 / 0.003 (n_vis 1311) | 1.000 / 0.004 (n_vis 933) |
| m3-armA `TRAINED_ON_ATOM` | static | optflow | 1.000 / 0.003 (n_vis 1835) | 1.000 / 0.002 (n_vis 1761) | 1.000 / 0.002 (n_vis 1598) | 1.000 / 0.003 (n_vis 1505) | 1.000 / 0.003 (n_vis 1311) | 1.000 / 0.004 (n_vis 933) |
| m3-armA `TRAINED_ON_ATOM` | static | none | 1.000 / 0.003 (n_vis 1835) | 1.000 / 0.002 (n_vis 1761) | 1.000 / 0.002 (n_vis 1598) | 1.000 / 0.003 (n_vis 1505) | 1.000 / 0.003 (n_vis 1311) | 1.000 / 0.004 (n_vis 933) |
| m3-armA `TRAINED_ON_ATOM` | red | pose | 0.862 / 0.000 (n_vis 650) | 0.876 / 0.000 (n_vis 619) | 0.879 / 0.000 (n_vis 553) | 0.882 / 0.000 (n_vis 516) | 0.854 / 0.000 (n_vis 439) | 0.775 / 0.000 (n_vis 289) |
| m3-armA `TRAINED_ON_ATOM` | red | optflow | 0.862 / 0.000 (n_vis 650) | 0.876 / 0.000 (n_vis 619) | 0.879 / 0.000 (n_vis 553) | 0.882 / 0.000 (n_vis 516) | 0.854 / 0.000 (n_vis 439) | 0.775 / 0.000 (n_vis 289) |
| m3-armA `TRAINED_ON_ATOM` | red | none | 0.862 / 0.000 (n_vis 650) | 0.876 / 0.000 (n_vis 619) | 0.879 / 0.000 (n_vis 553) | 0.882 / 0.000 (n_vis 516) | 0.854 / 0.000 (n_vis 439) | 0.775 / 0.000 (n_vis 289) |
| a7 `SELECTION_DOMAIN` | static | pose | 0.920 / 0.065 (n_vis 3576) | 0.913 / 0.080 (n_vis 2732) | 0.885 / 0.045 (n_vis 1827) | 0.863 / 0.046 (n_vis 1516) | 0.821 / 0.021 (n_vis 1223) | 0.407 / 0.009 (n_vis 1571) |
| a7 `SELECTION_DOMAIN` | static | optflow | 0.864 / 0.089 (n_vis 3576) | 0.826 / 0.108 (n_vis 2732) | 0.809 / 0.048 (n_vis 1827) | 0.806 / 0.038 (n_vis 1516) | 0.790 / 0.014 (n_vis 1223) | 0.393 / 0.007 (n_vis 1571) |
| a7 `SELECTION_DOMAIN` | static | none | 0.671 / 0.200 (n_vis 3576) | 0.547 / 0.233 (n_vis 2732) | 0.629 / 0.152 (n_vis 1827) | 0.665 / 0.123 (n_vis 1516) | 0.627 / 0.071 (n_vis 1223) | 0.367 / 0.036 (n_vis 1571) |
| a7 `SELECTION_DOMAIN` | red | pose | 0.883 / 0.036 (n_vis 1494) | 0.854 / 0.052 (n_vis 1353) | 0.782 / 0.080 (n_vis 1074) | 0.761 / 0.081 (n_vis 951) | 0.674 / 0.045 (n_vis 858) | 0.392 / 0.025 (n_vis 1013) |
| a7 `SELECTION_DOMAIN` | red | optflow | 0.809 / 0.074 (n_vis 1494) | 0.735 / 0.094 (n_vis 1353) | 0.697 / 0.062 (n_vis 1074) | 0.695 / 0.047 (n_vis 951) | 0.626 / 0.025 (n_vis 858) | 0.363 / 0.015 (n_vis 1013) |
| a7 `SELECTION_DOMAIN` | red | none | 0.627 / 0.249 (n_vis 1494) | 0.499 / 0.314 (n_vis 1353) | 0.534 / 0.229 (n_vis 1074) | 0.530 / 0.198 (n_vis 951) | 0.476 / 0.088 (n_vis 858) | 0.306 / 0.042 (n_vis 1013) |

### 臂 `c2_quantiles`：resolve_ok / false_lock（跨 S/M/L 汇总；非 EVALUATED 格标注状态）

| 序列 | 类 | gmc | Δ=1s | Δ=2s | Δ=4.2s | Δ=5.4s | Δ=8s | Δ=13s |
|---|---|---|---|---|---|---|---|---|
| scout-1 `TRAINED_ON_ATOM` | static | pose | 0.940 / 0.061 (n_vis 1412) | 0.933 / 0.098 (n_vis 1304) | 0.927 / 0.127 (n_vis 1123) | 0.926 / 0.140 (n_vis 1034) | 0.924 / 0.153 (n_vis 866) | 0.922 / 0.148 (n_vis 612) |
| scout-1 `TRAINED_ON_ATOM` | static | optflow | 0.930 / 0.061 (n_vis 1412) | 0.906 / 0.096 (n_vis 1304) | 0.865 / 0.120 (n_vis 1123) | 0.852 / 0.134 (n_vis 1034) | 0.838 / 0.143 (n_vis 866) | 0.892 / 0.145 (n_vis 612) |
| scout-1 `TRAINED_ON_ATOM` | static | none | 0.921 / 0.080 (n_vis 1412) | 0.899 / 0.129 (n_vis 1304) | 0.866 / 0.157 (n_vis 1123) | 0.848 / 0.155 (n_vis 1034) | 0.836 / 0.157 (n_vis 866) | 0.892 / 0.147 (n_vis 612) |
| scout-1 `TRAINED_ON_ATOM` | red | pose | 0.879 / 0.071 (n_vis 660) | 0.878 / 0.091 (n_vis 645) | 0.845 / 0.104 (n_vis 632) | 0.838 / 0.098 (n_vis 624) | 0.807 / 0.087 (n_vis 602) | 0.779 / 0.075 (n_vis 569) |
| scout-1 `TRAINED_ON_ATOM` | red | optflow | 0.874 / 0.063 (n_vis 660) | 0.859 / 0.078 (n_vis 645) | 0.810 / 0.079 (n_vis 632) | 0.796 / 0.080 (n_vis 624) | 0.743 / 0.089 (n_vis 602) | 0.687 / 0.079 (n_vis 569) |
| scout-1 `TRAINED_ON_ATOM` | red | none | 0.886 / 0.063 (n_vis 660) | 0.891 / 0.078 (n_vis 645) | 0.870 / 0.081 (n_vis 632) | 0.862 / 0.077 (n_vis 624) | 0.832 / 0.087 (n_vis 602) | 0.786 / 0.093 (n_vis 569) |
| m3-armA `TRAINED_ON_ATOM` | static | pose | 0.924 / 0.015 (n_vis 1835) | 0.918 / 0.014 (n_vis 1761) | 0.922 / 0.013 (n_vis 1598) | 0.920 / 0.015 (n_vis 1505) | 0.922 / 0.014 (n_vis 1311) | 0.929 / 0.016 (n_vis 933) |
| m3-armA `TRAINED_ON_ATOM` | static | optflow | 0.924 / 0.015 (n_vis 1835) | 0.918 / 0.014 (n_vis 1761) | 0.922 / 0.013 (n_vis 1598) | 0.920 / 0.015 (n_vis 1505) | 0.922 / 0.014 (n_vis 1311) | 0.929 / 0.016 (n_vis 933) |
| m3-armA `TRAINED_ON_ATOM` | static | none | 0.923 / 0.015 (n_vis 1835) | 0.918 / 0.014 (n_vis 1761) | 0.922 / 0.013 (n_vis 1598) | 0.920 / 0.015 (n_vis 1505) | 0.921 / 0.014 (n_vis 1311) | 0.929 / 0.016 (n_vis 933) |
| m3-armA `TRAINED_ON_ATOM` | red | pose | 0.815 / 0.005 (n_vis 650) | 0.822 / 0.006 (n_vis 619) | 0.828 / 0.004 (n_vis 553) | 0.835 / 0.004 (n_vis 516) | 0.815 / 0.002 (n_vis 439) | 0.744 / 0.000 (n_vis 289) |
| m3-armA `TRAINED_ON_ATOM` | red | optflow | 0.815 / 0.005 (n_vis 650) | 0.822 / 0.006 (n_vis 619) | 0.828 / 0.004 (n_vis 553) | 0.835 / 0.004 (n_vis 516) | 0.815 / 0.002 (n_vis 439) | 0.744 / 0.000 (n_vis 289) |
| m3-armA `TRAINED_ON_ATOM` | red | none | 0.815 / 0.005 (n_vis 650) | 0.822 / 0.006 (n_vis 619) | 0.828 / 0.004 (n_vis 553) | 0.835 / 0.004 (n_vis 516) | 0.815 / 0.002 (n_vis 439) | 0.744 / 0.000 (n_vis 289) |
| a7 `SELECTION_DOMAIN` | static | pose | 0.858 / 0.064 (n_vis 3576) | 0.850 / 0.082 (n_vis 2732) | 0.827 / 0.044 (n_vis 1827) | 0.807 / 0.046 (n_vis 1516) | 0.764 / 0.023 (n_vis 1223) | 0.379 / 0.012 (n_vis 1571) |
| a7 `SELECTION_DOMAIN` | static | optflow | 0.809 / 0.084 (n_vis 3576) | 0.772 / 0.104 (n_vis 2732) | 0.756 / 0.044 (n_vis 1827) | 0.757 / 0.037 (n_vis 1516) | 0.737 / 0.016 (n_vis 1223) | 0.366 / 0.009 (n_vis 1571) |
| a7 `SELECTION_DOMAIN` | static | none | 0.627 / 0.188 (n_vis 3576) | 0.513 / 0.220 (n_vis 2732) | 0.589 / 0.145 (n_vis 1827) | 0.624 / 0.117 (n_vis 1516) | 0.590 / 0.069 (n_vis 1223) | 0.342 / 0.037 (n_vis 1571) |
| a7 `SELECTION_DOMAIN` | red | pose | 0.837 / 0.035 (n_vis 1494) | 0.812 / 0.049 (n_vis 1353) | 0.749 / 0.074 (n_vis 1074) | 0.727 / 0.074 (n_vis 951) | 0.649 / 0.046 (n_vis 858) | 0.380 / 0.028 (n_vis 1013) |
| a7 `SELECTION_DOMAIN` | red | optflow | 0.762 / 0.072 (n_vis 1494) | 0.701 / 0.086 (n_vis 1353) | 0.669 / 0.059 (n_vis 1074) | 0.669 / 0.044 (n_vis 951) | 0.606 / 0.025 (n_vis 858) | 0.354 / 0.018 (n_vis 1013) |
| a7 `SELECTION_DOMAIN` | red | none | 0.593 / 0.234 (n_vis 1494) | 0.486 / 0.288 (n_vis 1353) | 0.520 / 0.210 (n_vis 1074) | 0.523 / 0.176 (n_vis 951) | 0.469 / 0.086 (n_vis 858) | 0.301 / 0.044 (n_vis 1013) |

### 结果桶分布示例（干净臂、gmc = pose、跨尺寸汇总，Δ = 4.2 s）

| 序列 | 类 | 状态 | NO_RESOLVE_FRAME | BOUND_V_CORRECT | BOUND_V_WRONG | BOUND_INVISIBLE | COASTING_V_CORRECT | COASTING_V_WRONG | COASTING_INVISIBLE | ENDED_V | ENDED_INVISIBLE | NOTRACK_V | NOTRACK_INVISIBLE | AMBIG_V | AMBIG_INVISIBLE | OUTHIST_V | OUTHIST_INVISIBLE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| scout-1 | static | EVALUATED | 66 | 1108 | 0 | 183 | 0 | 15 | 49 | 0 | 113 | 0 | 1 | 0 | 0 | 0 | 0 |
| scout-1 | red | EVALUATED | 25 | 531 | 0 | 48 | 24 | 20 | 0 | 0 | 0 | 57 | 0 | 0 | 0 | 0 | 0 |
| m3-armA | static | EVALUATED | 321 | 1598 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| m3-armA | red | EVALUATED | 129 | 440 | 0 | 0 | 46 | 0 | 0 | 0 | 0 | 67 | 0 | 0 | 0 | 0 | 0 |
| a7 | static | EVALUATED | 42 | 1517 | 2 | 136 | 100 | 78 | 656 | 1 | 1839 | 125 | 301 | 4 | 4 | 0 | 0 |
| a7 | red | EVALUATED | 21 | 742 | 0 | 0 | 98 | 130 | 113 | 12 | 365 | 86 | 80 | 6 | 0 | 0 | 0 |

### 扰动臂分位数（AC-20 修订 1/2/3）

来源：docs/proposals/P1-ENG-ACQ-001-pointer-fast-layer-target-switch-acquisition.md §0 事实 14 / §8（347 行；中位 0.862、p25 0.743、p10 0.358、≥0.5 占 0.870、≥0.3 占 0.905）；只取三个统计量，`reads_c2_prediction_file = False`、`replays_h_frames = False`；种子 20260929。

| 分位 | C2 347 行 | 实现（全样本） | 差 | 容差 |
|---|---|---|---|---|
| p10 | 0.358 | 0.314486 | 0.043514 | ≤ 0.05 |
| p25 | 0.743 | 0.733028 | 0.009972 | ≤ 0.05 |
| p50 | 0.862 | 0.855732 | 0.006268 | ≤ 0.05 |

逐序列实现分位：{"a7": {"p10": 0.298508, "p25": 0.73141, "p50": 0.854761}, "m3-armA": {"p10": 0.294586, "p25": 0.723515, "p50": 0.856852}, "scout-1": {"p10": 0.367174, "p25": 0.743845, "p50": 0.857304}}（p10 接近容差边缘，只作描述）。

## E2

转向存活（§3.9；AC-8）：3 序列 × 3 gmc_source × track_buffer {10, 20, 30} 次调用（名义 2/4/6 s）= 27 格全部产出。红车保持率为 FAST-001 R4 口径 A 13 s（`window_summary` 七类结局与守恒式逐字复用，另加 H-9「空窗即拒绝」断言：三序列最大帧间隔 0.325 s，断言存在且未触发）；ID 切换为每对象按真值 IoU ≥ 0.3 逐帧绑定后的切换数合计；静止车 track 寿命 = 每个（静止车, 绑定 track id）从首帧到末帧的仿真秒数。a7 为压力序列（扫视跳变），scout-1、m3-armA 为对照。**只作描述，不设门。**

| 序列 | gmc | buffer | 红车 13 s 保持率 (KEPT/D) | 静止车 ID 切换 / 对象 | 红车 ID 切换 | 静止车 track 寿命 中位 / 均值 s |
|---|---|---|---|---|---|---|
| scout-1 `TRAINED_ON_ATOM` | pose | 10 | 0.852 (482/566) | 6 / 14 | 2 | 7.30 / 12.04 |
| scout-1 `TRAINED_ON_ATOM` | pose | 20 | 0.852 (482/566) | 6 / 14 | 2 | 7.30 / 12.04 |
| scout-1 `TRAINED_ON_ATOM` | pose | 30 | 0.852 (482/566) | 6 / 14 | 2 | 7.30 / 12.04 |
| scout-1 `TRAINED_ON_ATOM` | optflow | 10 | 0.758 (428/565) | 8 / 14 | 3 | 6.30 / 10.93 |
| scout-1 `TRAINED_ON_ATOM` | optflow | 20 | 0.758 (428/565) | 8 / 14 | 3 | 6.30 / 10.93 |
| scout-1 `TRAINED_ON_ATOM` | optflow | 30 | 0.758 (428/565) | 8 / 14 | 3 | 6.30 / 10.93 |
| scout-1 `TRAINED_ON_ATOM` | none | 10 | 0.881 (498/565) | 15 / 14 | 3 | 3.80 / 8.13 |
| scout-1 `TRAINED_ON_ATOM` | none | 20 | 0.881 (498/565) | 16 / 14 | 3 | 3.80 / 8.25 |
| scout-1 `TRAINED_ON_ATOM` | none | 30 | 0.881 (498/565) | 16 / 14 | 3 | 3.80 / 8.25 |
| m3-armA `TRAINED_ON_ATOM` | pose | 10 | 0.739 (178/241) | 0 / 16 | 1 | 25.40 / 23.94 |
| m3-armA `TRAINED_ON_ATOM` | pose | 20 | 0.739 (178/241) | 0 / 16 | 1 | 25.40 / 23.94 |
| m3-armA `TRAINED_ON_ATOM` | pose | 30 | 0.739 (178/241) | 0 / 16 | 1 | 25.40 / 23.94 |
| m3-armA `TRAINED_ON_ATOM` | optflow | 10 | 0.739 (178/241) | 0 / 16 | 1 | 25.40 / 23.94 |
| m3-armA `TRAINED_ON_ATOM` | optflow | 20 | 0.739 (178/241) | 0 / 16 | 1 | 25.40 / 23.94 |
| m3-armA `TRAINED_ON_ATOM` | optflow | 30 | 0.739 (178/241) | 0 / 16 | 1 | 25.40 / 23.94 |
| m3-armA `TRAINED_ON_ATOM` | none | 10 | 0.739 (178/241) | 0 / 16 | 1 | 25.40 / 23.94 |
| m3-armA `TRAINED_ON_ATOM` | none | 20 | 0.739 (178/241) | 0 / 16 | 1 | 25.40 / 23.94 |
| m3-armA `TRAINED_ON_ATOM` | none | 30 | 0.739 (178/241) | 0 / 16 | 1 | 25.40 / 23.94 |
| a7 `SELECTION_DOMAIN` | pose | 10 | 0.626 (350/559) | 201 / 28 | 47 | 2.10 / 3.76 |
| a7 `SELECTION_DOMAIN` | pose | 20 | 0.521 (350/672) | 201 / 28 | 47 | 2.10 / 3.76 |
| a7 `SELECTION_DOMAIN` | pose | 30 | 0.378 (350/927) | 201 / 28 | 47 | 2.10 / 3.76 |
| a7 `SELECTION_DOMAIN` | optflow | 10 | 0.663 (364/549) | 223 / 28 | 59 | 1.59 / 3.37 |
| a7 `SELECTION_DOMAIN` | optflow | 20 | 0.550 (364/662) | 223 / 28 | 59 | 1.59 / 3.37 |
| a7 `SELECTION_DOMAIN` | optflow | 30 | 0.400 (364/909) | 223 / 28 | 59 | 1.59 / 3.37 |
| a7 `SELECTION_DOMAIN` | none | 10 | 0.573 (303/529) | 328 / 28 | 94 | 1.20 / 2.00 |
| a7 `SELECTION_DOMAIN` | none | 20 | 0.476 (303/636) | 342 / 28 | 95 | 1.20 / 1.95 |
| a7 `SELECTION_DOMAIN` | none | 30 | 0.351 (303/863) | 354 / 28 | 95 | 1.20 / 1.90 |

### pose_warp_selfcheck（AC-5 第三条）

相邻帧相机旋转 ≥ 5° 时，静止车真值框经位姿单应（四角 AABB）映射后与下一帧真值框中心误差，对照无补偿（px）：

| 序列 | 帧对 | 对象对 | 位姿单应 中位 / p90 | 无补偿 中位 / p90 |
|---|---|---|---|---|
| a7 | 578 | 585 | 2.58 / 26.14 | 95.38 / 165.55 |
| m3-armA | 0 | 0 | null / null | null / null |
| scout-1 | 20 | 21 | 1.27 / 1.67 | 50.24 / 66.72 |

a7 上位姿补偿优于无补偿，§6(i) 预注册处置不触发；`gmc_source` 缺省保持 `pose`。残差 p90 主要来自机身平移与扫视中目标出画（v1 忽略平移，§3.3）。

## 资产与偏差声明

复用资产本机 sha256（AC-11；详表 `docs/evidence/P1-ENG-ACQ-001-assets.json`）：

| 资产 | sha256（前 16） | 来源记录 | 一致 |
|---|---|---|---|
| detector weights last.pt | `d6a0d6a9cdee06a0` | config/det-assoc-v1.models.json weights.sha256（提案事实 3） | True |
| freeze.json | `f231e450d967c301` | config/det-assoc-v1.models.json freeze.sha256（提案事实 3） | True |
| frozen-B.jsonl.gz | `412592fbe55119c5` | 提案事实 10（本会话前由构思角色只读复核） | True |
| frozen-V.jsonl.gz | `783ec7e26b6b33de` | 提案事实 10 | True |
| catalog-index.jsonl.gz | `80971838f79a39b9` | 提案事实 11（FAST-001 缓存）；按 AC-11 修订 1 先查找独立既存文件散列记录，确无，固定本次基线（既往不可核），见 prior_record_search | 既往不可核（无既存记录；本次固定基线） |
| catalog-sim-times.jsonl.gz | `65a09ee11888b1c4` | 提案事实 11（同上） | 无既存记录（本次首记） |
| P1-ENG-FAST-002-dataset-frames.jsonl.gz | `3bcfc89944c6ca27` | 逐帧 JPEG sha 参照（FAST-002 数据集清单，已入库） | 无既存记录（本次首记） |
| nanotrack-v2 backbone | `530bdd0cd00f19af` | config/nanotrack-v2.models.json（提案事实 17） | True |
| nanotrack-v2 neckhead | `0d8c0637be849f09` | config/nanotrack-v2.models.json（提案事实 17） | True |

**catalog-index.jsonl.gz（AC-11 修订 1，既往不可核）**：先按 `-assets.json`「prior_record_search」逐处查找独立既存的该文件散列记录（7 处：主仓库工作树与 git 全历史、主仓库 outputs 压缩件、数据根文本文件与压缩件及其 git 全历史、FAST-001 构建代码），结论 NOT_FOUND：无独立既存的该文件散列记录；唯一命中是本工作项上一候选自记的本次实测值，不是既存来源。故按修订 1 固定本次完整 sha256 `80971838f79a39b9763eb0d586d5d12a0aa787c4672d31423e60bc71e6de0fbb`（1998848 字节）为后续比对基线，**既往不可核**，不冒充既存来源记录。补充（不是文件散列比对）：索引首行内容身份头与 `docs/evidence/P1-ENG-FAST-001-inputs.json「catalog_index」（5659e02，2026-09-24 入库）` 逐字段一致，上游两份目录文件当前 sha256 亦与之一致（True）。

三序列 4,832 帧逐帧 JPEG sha 与 FAST-002 数据集清单一致（4832 帧、不一致 0），sidecar `frame_id` 与文件名、`simulation_time_s` 与 FAST-001 时刻索引一致（容差 0.001 s），不一致即停（H-2）。

**AC-4 口径偏差声明（承接 FAST-002 H-8）**：

1. 序列单位：E2 按帧目录会话分段（m3-armA 7 段各自新建关联器、窗口在段内），与 FAST-002 IR-4「按会话替代按族」同向；本项 E1 的 r 也只在同段内取（§3.9 字面「m3-armA：同段」）。
2. scout-1 的 63 个 FAST-002 整帧排除帧（`TARGET_UNBOUNDED`：红车可见但无可用框）仍在回放中；本项真值取 FAST-001 目录索引，这些帧红车 `dynamic` 为空 → 按「不可见」处理。影响：E2 红车窗口在这些帧按真值缺失扫描（同 FAST-002 偏差）；E1 红车样本的 k 帧不会取到这些帧，但以它们为解析帧 r 的红车 (k,o,Δ) 共 294 个（干净臂，全部 gmc 同数）会被判 `…_INVISIBLE` 桶——其中若绑定红车 track 会记为 `BOUND_INVISIBLE`（误锁），即 scout-1 红车 false_lock 可能被高估、report_ok_invisible 可能被低估。
3. 本报告**不引用** FAST-002 的 G-5/G-6 读数或任何 H 域读数作为本项证据；H 域序列与 `frozen-H.jsonl.gz` 不读。
4. 检测来自冻结缓存（conf 0.25、imgsz 640、`device mps` 时算出）；scout-1、m3-armA 在检测器训练原子内（`TRAINED_ON_ATOM`，检测偏乐观），a7 为选择域（`SELECTION_DOMAIN`）。E1/E2 量的是关联与解析机制，不是检测器泛化。

## 消耗

账本 `docs/evidence/P1-ENG-ACQ-001-ledger.json`：序列回放 35 / 40（27 次 E2/E1 关联回放 + AC-6 载体自测 4 次 × 2 条部分回放）；本机 CPU 墙钟合计 4353 s / 10,800 s；第二级 NanoTrack 起跟 27793 次、更新 789215 帧（旧候选各次运行：每 (k,o) ≤ 65 帧、每 序列×gmc×臂 ≤ 600 个 (k,o)；SUB:1/SUB:2 后的重跑：a7 全样本、其他序列 ≤ 600、每 (k,o) ≤ 66 帧；SUB:3 后的重跑：同上但 scout-1 每 (k,o) ≤ 87 帧；线束断言）；其余维度（ID/Play/API/VLM/GPU/检测推理/YOLO 权重加载/下载/pip/远端访问）全 0。失败、重复与作废运行同样计入：E1 干净臂第 1 次因 NanoTrack 实例驻留致内存增长被手动终止（46 s）；第一轮扰动臂第 2 次因后台命令重复启动而多跑一次；第一轮 E1 四次运行后加入「逐次指定相互独立」修正（交接 IR-20），两臂四次随即整体重跑，重跑输出与第一轮逐字节相同；信封修订 SUB:1/SUB:2 后 E1 两臂各两次整体重跑（续派 `P1-ENG-ACQ-001-K1K2K3-20260929T142800Z-9b04`，E1 解析计 0 次序列回放）；信封修订 SUB:3 后 E1 两臂再各两次整体重跑（续派 `P1-ENG-ACQ-001-K1K2K3-20260929T150551Z-e3c8`，0 次序列回放），证据取这一轮结果。C1 返工（派发 `P1-ENG-ACQ-001-K1K2K3-20260929T171016Z-c5a7`）只改 coasting 上限边界、常驻发布记录与限速基准，E1/E2 不受影响、未重跑，0 次序列回放。
