# P1-ENG-FAST-001 快层替换探针报告（K4 候选；全离线、零 Play）

> 口径：全部数字是离线、桌面、oracle 候选或 oracle 参考条件下的描述性结果；gold 为 amodal 投影 AABB（`UNVERIFIED`）；
> 单次 greedy、单 seed，bootstrap 区间只作描述（2,000 轮，seed 20260923）。本报告只按合同 §6.2 逐格填值，**不给「换栈/保留」结论**，裁定归用户。
> 合同未写死处的实现读法逐条见 `docs/evidence/P1-ENG-FAST-001-K4-handoff.md`「实现读法（待裁定）」，交 `C1@K4` 裁定。

## 输入与身份（AC-1）

证据：`docs/evidence/P1-ENG-FAST-001-inputs.json`。

| 来源 | 帧 | 已配对真值 | 可见且带框 | 参考库 | 隔离断言 |
|---|---|---|---|---|---|
| body-armA | 640 | 640 | 431 | a2：车 `BANK_PARTIAL(5/9)`、红立方体 `COMPLETE` | 通过 |
| body-armB | 512 | 512 | 149 | td：车 `COMPLETE`、红立方体 `COMPLETE` | 通过 |
| catalog-448 | 448 | —（目录对象） | — | td：车 `COMPLETE`、红立方体 `COMPLETE` | 通过 |
| scout-1 | 768 | 705 | 659 | a2：车 `BANK_PARTIAL(5/9)`、红立方体 `COMPLETE` | 通过 |
| scout-4 | 2405 | 2405 | 2405 | td：车 `COMPLETE`、红立方体 `COMPLETE` | 通过 |

- 参考库 `a2`（池 = train 原子 {a2}）：车辆参考帧 2 张 `p1-vlm-survey-a2-p1-c1-s1/frame_0000000570.jpg`（ambulance, container truck, taxi）; `p1-vlm-survey-a2-p1-c1-s1/frame_0000001466.jpg`（pickup truck, truck）；红立方体参考帧 `frame_0000000112.jpg`（`same_instance_by_design`）。
- 参考库 `td`（池 = train∪dev 原子）：车辆参考帧 5 张 `p1-vlm-survey-a7-p1-c1-s1/frame_0000002550.jpg`（ambulance, container truck, pickup truck, truck）; `p1-vlm-survey-a7-p1-c1-s1/frame_0000001423.jpg`（car, suv）; `p1-vlm-survey-a1-p1-c1-s2/frame_0000001987.jpg`（taxi）; `p1-vlm-survey-a1-p1-c1-s2/frame_0000002160.jpg`（police car）; `p1-vlm-survey-a1-p1-c1-s2/frame_0000002152.jpg`（bus）；红立方体参考帧 `frame_0000000112.jpg`（`same_instance_by_design`）。

## P1 分桶召回（AC-2）

证据：`docs/evidence/P1-ENG-FAST-001-recall.json`（逐格 `hit/n`、95% CI、FP/帧、适用域矩阵；全交叉 短边×距离 表在 JSON）。每格写「IoU≥0.30 / IoU≥0.50」。

### 斜距表（scout-1 / scout-4 / BODY-001）

按距离档：

| 来源 × 检测器 | 种类 × 实例标记 | <35 | 35–50 | 50–65 | ≥65 | NA |
|---|---|---|---|---|---|---|
| body-all · T0-bank(a2 armA, td armB) | red_primitive · same_instance_by_design | 76/145（52.4%） / 76/145（52.4%） | 35/192（18.2%） / 29/192（15.1%） | 12/240（5.0%） / 1/240（0.4%） | 0/3（0.0%） / 0/3（0.0%） | — |
| body-armA · T0-bank-a2 | red_primitive · same_instance_by_design | 0/50（0.0%） / 0/50（0.0%） | 11/138（8.0%） / 5/138（3.6%） | 12/240（5.0%） / 1/240（0.4%） | 0/3（0.0%） / 0/3（0.0%） | — |
| body-armA · T0-oracle | — | `N/A(NO_SESSION_REFERENCE)` | | | | |
| body-armA · T1a | — | `N/A(NOT_AUTHORIZED_T1_UNSIGNED)` | | | | |
| body-armA · T1b | — | `N/A(NOT_AUTHORIZED_T1_UNSIGNED)` | | | | |
| body-armB · T0-bank-td | red_primitive · same_instance_by_design | 76/95（80.0%） / 76/95（80.0%） | 24/54（44.4%） / 24/54（44.4%） | — | — | — |
| body-armB · T0-oracle | — | `N/A(NO_SESSION_REFERENCE)` | | | | |
| body-armB · T1a | — | `N/A(NOT_AUTHORIZED_T1_UNSIGNED)` | | | | |
| body-armB · T1b | — | `N/A(NOT_AUTHORIZED_T1_UNSIGNED)` | | | | |
| default-geometry(scout-1+BODY) · T0-bank(a2 for scout-1/armA, td for armB) | catalog_vehicle · not_in_bank | — | — | — | — | 218/278（78.4%） / 218/278（78.4%） |
| default-geometry(scout-1+BODY) · T0-bank(a2 for scout-1/armA, td for armB) | red_primitive · same_instance_by_design | 204/391（52.2%） / 204/391（52.2%） | 61/293（20.8%） / 55/293（18.8%） | 29/466（6.2%） / 18/466（3.9%） | 2/89（2.2%） / 0/89（0.0%） | — |
| scout-1 · T0-bank-a2 | catalog_vehicle · not_in_bank（BANK_PARTIAL(5/9)） | — | — | — | — | 218/278（78.4%） / 218/278（78.4%） |
| scout-1 · T0-bank-a2 | red_primitive · same_instance_by_design | 128/246（52.0%） / 128/246（52.0%） | 26/101（25.7%） / 26/101（25.7%） | 17/226（7.5%） / 17/226（7.5%） | 2/86（2.3%） / 0/86（0.0%） | — |
| scout-1 · T0-oracle | catalog_vehicle · not_in_bank | — | — | — | — | 0/278（0.0%） / 0/278（0.0%） |
| scout-1 · T0-oracle | red_primitive · same_instance_by_design | 220/246（89.4%） / 220/246（89.4%） | 93/101（92.1%） / 93/101（92.1%） | 4/226（1.8%） / 4/226（1.8%） | 0/86（0.0%） / 0/86（0.0%） | — |
| scout-1 · T1a | — | `N/A(NOT_AUTHORIZED_T1_UNSIGNED)` | | | | |
| scout-1 · T1b | — | `N/A(NOT_AUTHORIZED_T1_UNSIGNED)` | | | | |
| scout-4 · T0-bank-td | catalog_vehicle · not_in_bank | — | — | — | — | 798/2648（30.1%） / 94/2648（3.5%） |
| scout-4 · T0-bank-td | red_primitive · same_instance_by_design | 1215/2405（50.5%） / 918/2405（38.2%） | — | — | — | — |
| scout-4 · T0-oracle | catalog_vehicle · not_in_bank | — | — | — | — | 6/2648（0.2%） / 6/2648（0.2%） |
| scout-4 · T0-oracle | red_primitive · same_instance_by_design | 2169/2405（90.2%） / 1893/2405（78.7%） | — | — | — | — |
| scout-4 · T1a | — | `N/A(NOT_AUTHORIZED_T1_UNSIGNED)` | | | | |
| scout-4 · T1b | — | `N/A(NOT_AUTHORIZED_T1_UNSIGNED)` | | | | |

按短边层：

| 来源 × 检测器 | 种类 × 实例标记 | S | M | L | NA |
|---|---|---|---|---|---|
| body-all · T0-bank(a2 armA, td armB) | red_primitive · same_instance_by_design | 0/198（0.0%） / 0/198（0.0%） | 123/370（33.2%） / 106/370（28.6%） | 0/12（0.0%） / 0/12（0.0%） | — |
| body-armA · T0-bank-a2 | red_primitive · same_instance_by_design | 0/190（0.0%） / 0/190（0.0%） | 23/229（10.0%） / 6/229（2.6%） | 0/12（0.0%） / 0/12（0.0%） | — |
| body-armB · T0-bank-td | red_primitive · same_instance_by_design | 0/8（0.0%） / 0/8（0.0%） | 100/141（70.9%） / 100/141（70.9%） | — | — |
| default-geometry(scout-1+BODY) · T0-bank(a2 for scout-1/armA, td for armB) | catalog_vehicle · not_in_bank | 0/25（0.0%） / 0/25（0.0%） | 2/26（7.7%） / 2/26（7.7%） | 216/227（95.2%） / 216/227（95.2%） | — |
| default-geometry(scout-1+BODY) · T0-bank(a2 for scout-1/armA, td for armB) | red_primitive · same_instance_by_design | 76/622（12.2%） / 74/622（11.9%） | 206/572（36.0%） / 189/572（33.0%） | 14/45（31.1%） / 14/45（31.1%） | — |
| scout-1 · T0-bank-a2 | catalog_vehicle · not_in_bank（BANK_PARTIAL(5/9)） | 0/25（0.0%） / 0/25（0.0%） | 2/26（7.7%） / 2/26（7.7%） | 216/227（95.2%） / 216/227（95.2%） | — |
| scout-1 · T0-bank-a2 | red_primitive · same_instance_by_design | 76/424（17.9%） / 74/424（17.5%） | 83/202（41.1%） / 83/202（41.1%） | 14/33（42.4%） / 14/33（42.4%） | — |
| scout-1 · T0-oracle | catalog_vehicle · not_in_bank | 0/25（0.0%） / 0/25（0.0%） | 0/26（0.0%） / 0/26（0.0%） | 0/227（0.0%） / 0/227（0.0%） | — |
| scout-1 · T0-oracle | red_primitive · same_instance_by_design | 109/424（25.7%） / 109/424（25.7%） | 189/202（93.6%） / 189/202（93.6%） | 19/33（57.6%） / 19/33（57.6%） | — |
| scout-4 · T0-bank-td | catalog_vehicle · not_in_bank | 0/212（0.0%） / 0/212（0.0%） | 4/223（1.8%） / 4/223（1.8%） | 794/2213（35.9%） / 90/2213（4.1%） | — |
| scout-4 · T0-bank-td | red_primitive · same_instance_by_design | — | 839/1390（60.4%） / 839/1390（60.4%） | 376/1015（37.0%） / 79/1015（7.8%） | — |
| scout-4 · T0-oracle | catalog_vehicle · not_in_bank | 0/212（0.0%） / 0/212（0.0%） | 0/223（0.0%） / 0/223（0.0%） | 6/2213（0.3%） / 6/2213（0.3%） | — |
| scout-4 · T0-oracle | red_primitive · same_instance_by_design | — | 1389/1390（99.9%） / 1389/1390（99.9%） | 780/1015（76.8%） / 504/1015（49.7%） | — |

### 轴向深度表（609 行的 448 目录帧；表头为相机**轴向深度**，不与斜距合并）

按距离档：

| 来源 × 检测器 | 种类 × 实例标记 | <35 | 35–50 | 50–65 | ≥65 | NA |
|---|---|---|---|---|---|---|
| catalog-448 · T0-bank-td | catalog_vehicle · not_in_bank | 240/518（46.3%） / 232/518（44.8%） | 155/237（65.4%） / 150/237（63.3%） | 98/163（60.1%） / 93/163（57.1%） | 27/90（30.0%） / 27/90（30.0%） | — |
| catalog-448 · T0-bank-td | catalog_vehicle · same_instance_in_bank | 2/2（100.0%） / 2/2（100.0%） | 22/23（95.7%） / 22/23（95.7%） | 3/3（100.0%） / 3/3（100.0%） | 0/5（0.0%） / 0/5（0.0%） | — |
| catalog-448 · T0-bank-td | red_primitive · same_instance_by_design | — | — | — | — | 98/229（42.8%） / 89/229（38.9%） |
| catalog-448 · T0-oracle | — | `N/A(NO_SESSION_REFERENCE)` | | | | |
| catalog-448 · T1a | — | `N/A(NOT_AUTHORIZED_T1_UNSIGNED)` | | | | |
| catalog-448 · T1b | — | `N/A(NOT_AUTHORIZED_T1_UNSIGNED)` | | | | |

按短边层：

| 来源 × 检测器 | 种类 × 实例标记 | S | M | L | NA |
|---|---|---|---|---|---|
| catalog-448 · T0-bank-td | catalog_vehicle · not_in_bank | 88/192（45.8%） / 88/192（45.8%） | 243/386（63.0%） / 229/386（59.3%） | 189/430（44.0%） / 185/430（43.0%） | — |
| catalog-448 · T0-bank-td | catalog_vehicle · same_instance_in_bank | 1/6（16.7%） / 1/6（16.7%） | 24/25（96.0%） / 24/25（96.0%） | 2/2（100.0%） / 2/2（100.0%） | — |
| catalog-448 · T0-bank-td | red_primitive · same_instance_by_design | 0/28（0.0%） / 0/28（0.0%） | 57/128（44.5%） / 57/128（44.5%） | 41/73（56.2%） / 32/73（43.8%） | — |

### FP/帧（描述性，不与任何决策计数比较）

| 来源 × 检测器 | 帧 | 检测数 | 未匹配检测 | FP/帧 |
|---|---|---|---|---|
| body-armA · T0-bank-a2 | 640 | 424 | 401 | 0.626563 |
| body-armB · T0-bank-td | 512 | 1134 | 1034 | 2.019531 |
| catalog-448 · T0-bank-td | 448 | 941 | 302 | 0.674107 |
| scout-1 · T0-bank-a2 | 705 | 1628 | 1221 | 1.731915 |
| scout-1 · T0-oracle | 705 | 340 | 20 | 0.028369 |
| scout-4 · T0-bank-td | 2405 | 2679 | 664 | 0.276091 |
| scout-4 · T0-oracle | 2405 | 2346 | 144 | 0.059875 |

注：scout 真值只列 1–2 辆干扰车、BODY 真值不列干扰车，真值清单之外的场景车辆被检出也计为未匹配。T1a/T1b 未签发，所有格 `N/A(NOT_AUTHORIZED_T1_UNSIGNED)`；T0-oracle 在 BODY/目录帧为 `N/A(NO_SESSION_REFERENCE)`。

## T0-oracle 旧数复算（AC-3）

| 来源 | 旧数 | 复算 | 逐 tick 命中不一致 | 与旧 max IoU 最大差 | 处置 |
|---|---|---|---|---|---|
| scout-1 | 0/45 | 0/45 | 0 | 0.0 | `ALIGNED` |
| scout-4 | 172/187 | 172/187 | 0 | 1e-06 | `ALIGNED` |

口径：以旧结果逐 tick 样本为 tick 计划（同阈值 conf≥0.25、IoU≥0.30；scout-1 的 `MISSING_*` tick 按旧政策计为漏）。

## P2a 静态 margin（AC-4）

证据：`docs/evidence/P1-ENG-FAST-001-margin.json`（逐对记录、分层/分类别统计）。嵌入器 = 冻结 DINOv2 ViT-S/14。

| Δ | 合格帧对 | 选取 | 计分 | CROP_INVALID | margin p50 | margin ≥0.1 | 自身 cos ≥0.5 | S 层 ≥0.1 | M 层 ≥0.1 | L 层 ≥0.1 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1s | 3784 | 300 | 300 | 0 | 0.352486 | 251/300（83.7%） | 287/300（95.7%） | 40/42（95.2%） | 98/119（82.4%） | 113/139（81.3%） |
| 5s | 819 | 300 | 300 | 0 | 0.186036 | 191/300（63.7%） | 260/300（86.7%） | 42/46（91.3%） | 75/103（72.8%） | 74/151（49.0%） |
| 13s | 464 | 300 | 300 | 0 | 0.068462 | 106/300（35.3%） | 238/300（79.3%） | 5/7（71.4%） | 19/85（22.4%） | 82/208（39.4%） |

## P2b 序列回放（AC-5）

证据：`docs/evidence/P1-ENG-FAST-001-replay.json`。`lap 0.5.13`、ultralytics 8.4.104；接口：BYTETracker(args)/BOTSORT(args)，args=IterableSimpleNamespace(**YAML.load(check_yaml(<algo>.yaml)))；无 frame_rate；每帧一次 update(Boxes(tensor[N,6]).cpu().numpy(), img)。
保持率 = KEPT / D，D = KEPT + ID_SWITCH + LOST_BEYOND_BUFFER + UNRESOLVED_END_MISS（`UNRESOLVED_END_MISS` 计入分母、不算保持，读数偏保守）。

| 序列 | 算法 | W | V | 排除（UNBOUND/CENSORED/TRUTH_GAP） | KEPT | ID_SWITCH | LOST>buffer | UNRESOLVED_END | 保持率 | drift_return（其中 L=31） |
|---|---|---|---|---|---|---|---|---|---|---|
| body-arm-a-trial-1-attempt-4 | botsort | 13s | 0 | 0/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-a-trial-1-attempt-4 | botsort | 8s | 0 | 0/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-a-trial-1-attempt-4 | bytetrack | 13s | 0 | 0/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-a-trial-1-attempt-4 | bytetrack | 8s | 0 | 0/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-a-trial-2-attempt-2 | botsort | 13s | 93 | 90/0/0 | 0 | 0 | 3 | 0 | 0.0 | 0（0） |
| body-arm-a-trial-2-attempt-2 | botsort | 8s | 93 | 90/0/0 | 0 | 0 | 3 | 0 | 0.0 | 0（0） |
| body-arm-a-trial-2-attempt-2 | bytetrack | 13s | 93 | 90/0/0 | 0 | 0 | 3 | 0 | 0.0 | 0（0） |
| body-arm-a-trial-2-attempt-2 | bytetrack | 8s | 93 | 90/0/0 | 0 | 0 | 3 | 0 | 0.0 | 0（0） |
| body-arm-a-trial-3 | botsort | 13s | 112 | 112/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-a-trial-3 | botsort | 8s | 112 | 112/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-a-trial-3 | bytetrack | 13s | 112 | 112/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-a-trial-3 | bytetrack | 8s | 112 | 112/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-a-trial-4 | botsort | 13s | 98 | 98/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-a-trial-4 | botsort | 8s | 98 | 98/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-a-trial-4 | bytetrack | 13s | 98 | 98/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-a-trial-4 | bytetrack | 8s | 98 | 98/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-a-trial-5 | botsort | 13s | 128 | 122/0/0 | 0 | 0 | 6 | 0 | 0.0 | 0（0） |
| body-arm-a-trial-5 | botsort | 8s | 128 | 122/0/0 | 0 | 0 | 6 | 0 | 0.0 | 0（0） |
| body-arm-a-trial-5 | bytetrack | 13s | 128 | 122/0/0 | 0 | 0 | 6 | 0 | 0.0 | 0（0） |
| body-arm-a-trial-5 | bytetrack | 8s | 128 | 122/0/0 | 0 | 0 | 6 | 0 | 0.0 | 0（0） |
| body-arm-b-trial-1 | botsort | 13s | 0 | 0/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-b-trial-1 | botsort | 8s | 0 | 0/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-b-trial-1 | bytetrack | 13s | 0 | 0/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-b-trial-1 | bytetrack | 8s | 0 | 0/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-b-trial-2 | botsort | 13s | 46 | 21/0/18 | 0 | 0 | 7 | 0 | 0.0 | 0（0） |
| body-arm-b-trial-2 | botsort | 8s | 46 | 21/0/0 | 0 | 0 | 25 | 0 | 0.0 | 0（0） |
| body-arm-b-trial-2 | bytetrack | 13s | 46 | 21/0/18 | 0 | 0 | 7 | 0 | 0.0 | 0（0） |
| body-arm-b-trial-2 | bytetrack | 8s | 46 | 21/0/0 | 0 | 0 | 25 | 0 | 0.0 | 0（0） |
| body-arm-b-trial-4 | botsort | 13s | 0 | 0/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-b-trial-4 | botsort | 8s | 0 | 0/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-b-trial-4 | bytetrack | 13s | 0 | 0/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-b-trial-4 | bytetrack | 8s | 0 | 0/0/0 | 0 | 0 | 0 | 0 | — | 0（0） |
| body-arm-b-trial-5 | botsort | 13s | 103 | 33/28/0 | 0 | 34 | 8 | 0 | 0.0 | 0（0） |
| body-arm-b-trial-5 | botsort | 8s | 103 | 33/2/0 | 1 | 34 | 33 | 0 | 0.014706 | 0（0） |
| body-arm-b-trial-5 | bytetrack | 13s | 103 | 36/28/0 | 0 | 31 | 8 | 0 | 0.0 | 0（0） |
| body-arm-b-trial-5 | bytetrack | 8s | 103 | 36/2/0 | 1 | 31 | 33 | 0 | 0.015385 | 0（0） |
| scout-1 | botsort | 13s | 659 | 517/45/1 | 25 | 62 | 9 | 0 | 0.260417 | 0（0） |
| scout-1 | botsort | 8s | 659 | 517/35/0 | 44 | 53 | 10 | 0 | 0.411215 | 0（0） |
| scout-1 | bytetrack | 13s | 659 | 506/44/1 | 43 | 57 | 8 | 0 | 0.398148 | 0（0） |
| scout-1 | bytetrack | 8s | 659 | 506/37/0 | 64 | 43 | 9 | 0 | 0.551724 | 0（0） |
| scout-4 | botsort | 13s | 2405 | 1244/202/0 | 0 | 0 | 959 | 0 | 0.0 | 43（43） |
| scout-4 | botsort | 8s | 2405 | 1244/147/0 | 242 | 25 | 747 | 0 | 0.238659 | 73（73） |
| scout-4 | bytetrack | 13s | 2405 | 1323/189/0 | 0 | 3 | 890 | 0 | 0.0 | 43（43） |
| scout-4 | bytetrack | 8s | 2405 | 1323/134/0 | 242 | 28 | 678 | 0 | 0.255274 | 73（73） |

序列级（ByteTrack）：

| 序列 | 帧 | 可见 | 绑定 | ID 切换 | 碎片 | 最长同 ID 秒 | 帧间隔 p50 s | 30 次调用 ≈ 秒 |
|---|---|---|---|---|---|---|---|---|
| body-arm-a-trial-1-attempt-4 | 128 | 0 | 0 | 0 | 0 | 0.0 | 0.199875 | 5.996246 |
| body-arm-a-trial-2-attempt-2 | 128 | 93 | 3 | 0 | 2 | 0.399994 | 0.199905 | 5.997162 |
| body-arm-a-trial-3 | 128 | 112 | 0 | 0 | 1 | 0.0 | 0.199982 | 5.999451 |
| body-arm-a-trial-4 | 128 | 98 | 0 | 0 | 1 | 0.0 | 0.199524 | 5.985718 |
| body-arm-a-trial-5 | 128 | 128 | 6 | 0 | 3 | 1.19899 | 0.200195 | 6.005859 |
| body-arm-b-trial-1 | 128 | 0 | 0 | 0 | 0 | 0.0 | 0.19989 | 5.996704 |
| body-arm-b-trial-2 | 128 | 46 | 25 | 0 | 3 | 5.396393 | 0.199371 | 5.98114 |
| body-arm-b-trial-4 | 128 | 0 | 0 | 0 | 0 | 0.0 | 0.199799 | 5.993958 |
| body-arm-b-trial-5 | 128 | 103 | 67 | 1 | 7 | 7.999619 | 0.200211 | 6.006317 |
| scout-1 | 768 | 659 | 153 | 5 | 36 | 21.801116 | 0.199245 | 5.977364 |
| scout-4 | 2405 | 2405 | 1082 | 15 | 78 | 11.999683 | 0.049988 | 1.499634 |

库边界实测（`test_library_buffer_boundary`，两算法相同）：空检测 30 次调用 → 同 ID；**31 次 → 仍同 ID**；32 次 → 新 ID。与事实 20 的读码结论差 1 帧（IR-8）；判定阈值仍按 §3.4 字面（L ≥ 31 → `LOST_BEYOND_BUFFER`），L = 31 的原 ID 找回列在 drift_return 括号内。

## P3 VLM 四臂（AC-6）

证据：`docs/evidence/P1-ENG-FAST-001-vlm-arms.json`（逐行结果、逐查询 prompt sha/解码参数/token/时延、配对 2×2）。
候选集口径：IR-1：OK 目录车辆（适配器执行域）∪ 帧级已绑定动态目标（规则 ① 有框）；K=0 行 26（确定性 none、零查询、计入各分母）。臂 A 零新查询（既有文件 sha 见 inputs.json）。

查询：基线 B 583/583、C 583/583；重试 B 9、C 26；合计 1201（5060 账本 {'base_start': 1, 'query_baseline': 1166, 'query_retry': 35, 'query_total': 1201}）；停臂 无；smoke {'B': {'invalid_rate': 0.0, 'queries': 32}, 'C': {'invalid_rate': 0.03125, 'queries': 32}}；Mac 复解析不一致 0。

G3p 即合同的 G3′（诊断组，不进任何门）；LEGACY_ONLY 8 行排除所有报表。

| 组（指标） | A_base | A_C2 | B | C | D |
|---|---|---|---|---|---|
| G1（success） | 108/210（51.4%） | 161/210（76.7%） | 126/210（60.0%） | 83/210（39.5%） | 100/210（47.6%） |
| G1t（success） | 9/23（39.1%） | 15/23（65.2%） | 5/23（21.7%） | 4/23（17.4%） | 19/23（82.6%） |
| G2（success） | 24/49（49.0%） | 40/49（81.6%） | 36/49（73.5%） | 22/49（44.9%） | 25/49（51.0%） |
| G2t（success） | 9/23（39.1%） | 15/23（65.2%） | 8/23（34.8%） | 11/23（47.8%） | 13/23（56.5%） |
| G4（success） | 7/86（8.1%） | 71/86（82.6%） | 5/86（5.8%） | 0/86（0.0%） | 28/86（32.6%） |
| G3（report） | 0/48（0.0%） | 19/48（39.6%） | 9/48（18.8%） | 22/48（45.8%） | 25/48（52.1%） |
| G3（strict） | 0/48（0.0%） | 12/48（25.0%） | 1/48（2.1%） | 4/48（8.3%） | 19/48（39.6%） |
| G3t（report） | 0/12（0.0%） | 5/12（41.7%） | 8/12（66.7%） | 12/12（100.0%） | 8/12（66.7%） |
| G3t（strict） | 0/12（0.0%） | 0/12（0.0%） | 0/12（0.0%） | 0/12（0.0%） | 5/12（41.7%） |
| G5（none） | 76/100（76.0%） | 79/100（79.0%） | 80/100（80.0%） | 68/100（68.0%） | 98/100（98.0%） |
| G3p（report） | 0/50（0.0%） | 13/50（26.0%） | 13/50（26.0%） | 29/50（58.0%） | 11/50（22.0%） |
| G3p（any_member） | 16/50（32.0%） | 40/50（80.0%） | 34/50（68.0%） | 39/50（78.0%） | 29/50（58.0%） |
| G1∪G2（false_none） | 78/259（30.1%） | 30/259（11.6%） | 67/259（25.9%） | 56/259（21.6%） | 100/259（38.6%） |
| G1∪G2（false_ambiguous） | 0/259（0.0%） | 6/259（2.3%） | 23/259（8.9%） | 53/259（20.5%） | 24/259（9.3%） |

分层（成功组 success，S / M / L）：

| 组 | A_base | A_C2 | B | C | D |
|---|---|---|---|---|---|
| G1 | 2/30（6.7%） / 43/95（45.3%） / 63/85（74.1%） | 11/30（36.7%） / 77/95（81.1%） / 73/85（85.9%） | 6/30（20.0%） / 63/95（66.3%） / 57/85（67.1%） | 2/30（6.7%） / 32/95（33.7%） / 49/85（57.6%） | 12/30（40.0%） / 46/95（48.4%） / 42/85（49.4%） |
| G2 | 2/13（15.4%） / 7/18（38.9%） / 15/18（83.3%） | 8/13（61.5%） / 15/18（83.3%） / 17/18（94.4%） | 6/13（46.2%） / 14/18（77.8%） / 16/18（88.9%） | 1/13（7.7%） / 9/18（50.0%） / 12/18（66.7%） | 2/13（15.4%） / 9/18（50.0%） / 14/18（77.8%） |
| G4 | 1/22（4.5%） / 1/38（2.6%） / 5/26（19.2%） | 16/22（72.7%） / 33/38（86.8%） / 22/26（84.6%） | 1/22（4.5%） / 1/38（2.6%） / 3/26（11.5%） | 0/22（0.0%） / 0/38（0.0%） / 0/26（0.0%） | 10/22（45.5%） / 12/38（31.6%） / 6/26（23.1%） |
| G1t | 0/11（0.0%） / 5/7（71.4%） / 4/5（80.0%） | 4/11（36.4%） / 7/7（100.0%） / 4/5（80.0%） | 0/11（0.0%） / 2/7（28.6%） / 3/5（60.0%） | 0/11（0.0%） / 1/7（14.3%） / 3/5（60.0%） | 8/11（72.7%） / 6/7（85.7%） / 5/5（100.0%） |
| G2t | 0/11（0.0%） / 5/7（71.4%） / 4/5（80.0%） | 4/11（36.4%） / 7/7（100.0%） / 4/5（80.0%） | 0/11（0.0%） / 4/7（57.1%） / 4/5（80.0%） | 1/11（9.1%） / 5/7（71.4%） / 5/5（100.0%） | 4/11（36.4%） / 5/7（71.4%） / 4/5（80.0%） |

计数（臂 A 的 `NO_CANDIDATE_MATCH`/`PARSE_ERROR`；B/C 的 `INVALID`/`NOT_RUN`；B/C/D 的 `K0`）：

- A_base：{'NO_CANDIDATE_MATCH': 22, 'PARSE_ERROR': 103, 'no_flag': 484}（`no_flag` = 无标记的正常输出行）
- A_C2：{'NO_CANDIDATE_MATCH': 70, 'no_flag': 539}（`no_flag` = 无标记的正常输出行）
- B：{'INVALID': 9, 'K0': 26, 'no_flag': 574}（`no_flag` = 无标记的正常输出行）
- C：{'INVALID': 26, 'K0': 26, 'no_flag': 557}（`no_flag` = 无标记的正常输出行）
- D：{'K0': 26, 'no_flag': 583}（`no_flag` = 无标记的正常输出行）

配对诊断（§3.5.4；成功组逐行 `{det_hit × arm_ok}`，det_hit = T0-bank-td cpu 对 gold 对象 max IoU ≥ 0.3）。**这是同一行上两种独立测量的交集，不是任何链路的成功率或上界；B/C 的裁图/框来自 oracle 候选，改用检测器框后 VLM 的成绩未测量。**

| 臂 | n | hit∧ok | hit∧fail | miss∧ok | miss∧fail | P(ok∧hit) | P(ok｜hit) |
|---|---|---|---|---|---|---|---|
| A_base | 391 | 94 | 96 | 63 | 138 | 0.240409 | 0.494737 |
| A_C2 | 391 | 157 | 33 | 145 | 56 | 0.401535 | 0.826316 |
| B | 391 | 98 | 92 | 82 | 119 | 0.250639 | 0.515789 |
| C | 391 | 67 | 123 | 53 | 148 | 0.171355 | 0.352632 |
| D | 391 | 92 | 98 | 93 | 108 | 0.235294 | 0.484211 |

臂 A 的 SFT-002 原 IoU 口径成绩原样引用（不重算）：`docs/reviews/P1-ENG-SFT-002-stage-summary.md` §4–§5（C2：G1 76.7%、S 层 36.7%；G2 81.6%；G4 82.6%；G1t/G2t 65.2%；base：G1∪G2 51.0%、G4 8.1%）。

臂 D 披露：裁图库 1112 张 / 62 个对象（每对象 ≤20、短边 ≥16.0 px）；颜色原型 {'blue': 20, 'gray': 143, 'green': 40, 'purple': 10, 'red': 10}。库内对象与评估候选多为同一场景实例（静态车辆跨族复现），逐候选 `same_instance_in_bank` 见 armd 缓存。

## P4 与 DETECT-001 的关系（AC-7）

- **验收 4 缺口原文**（`docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md` 验收 4 / 合同事实 3）：「背景锁定打破测试」——冻结 B2 困难场景、含 t≈40 s 交接点的 ≥150 s 窗口、incorrect/matched < 0.5 且 ≥1 次三门通过的 DISAGREE 重播种——**从未运行**，是该项未闭的证据缺口。
- **qual-3 数字读法**：detector 节奏 75/75 是检测**节奏**达成，不是召回；决策 AGREE 36 / TENTATIVE 19 / NO_CANDIDATE 20 是三门**决策计数**，不是 FP，本报告的 FP/帧不与之并列；零 REANCHOR。
- **本项复用的冻结件**：`config/detector-reanchor.models.json`（阈值 0.25、`imgsz` 640、权重/源码 sha 与 torch/ultralytics 钉版）、`controller/reanchor_models.YoloeProposer`（T0-oracle 与 T0-bank 的 YOLOE 构造与视觉提示路径）、`DinoV2Embedder`（P2a 与臂 D），全部只导入、零字节改动。
- **差异**：DETECT-001 的检测器每 2 s 一次、以同会话初始化框为单类提示并经三门决策；本项 T0-bank 以跨会话参考库（原子隔离）固定两类嵌入、逐帧检测、类别无关计分，T0-oracle 只用于与 scouting 旧数对齐；本项不做决策门、不重播种、不接入运行时。
- **本项不闭合该缺口**：验收 4 需要困难场景 Play，本项零 Play（合同 §2.2-6）。
- **待复现风险**：(1) 远端（≥65 m）召回与 scouting 0/45 同源几何，在线 5 Hz、同机 Unity 负载下未测；(2) 背景锁定的触发机制（模板交接给静态背景）属于 NanoTrack，本项的检测+关联路线未在 B2 困难场景回放；(3) 参考库单来源（{a2}）条件下的 T0-bank 数字换参考库可能不同；(4) 红立方体只有同一锚点、同一路线的样本。

## 时延（AC-10；只报 Mac 桌面数字）

主机：Apple M4，torch 2.13.0，ultralytics 8.4.104；同机 Unity 运行：否。

| 项 | CPU p50 / p95 ms | MPS p50 / p95 ms |
|---|---|---|
| T0 检测（320 帧，含预处理） | 64.414729 / 68.071273 | 24.681875 / 29.761829 |
| DINOv2 单裁图 | 19.868146 / 21.477548 | 13.942395 / 15.082254 |
| ByteTrack `update` | 0.172083 / 0.2543 | — |

CPU/MPS 框一致性：{'count_mismatch_frames': 0, 'frames': 320, 'max_abs_coord_or_score_diff': 1e-05}。

## 读数表（§6.2 预注册；AC-8）

「读法」全部是条件句、描述性，供用户裁定；「不可推出」为硬约束。本表不含「换栈/保留」结论。

| 格 | 取值（证据） | 参考线 | 读法（条件性） | 不可推出 |
|---|---|---|---|---|
| R1 默认几何远端召回（T0-bank，scout-1 + BODY，≥50/≥65 m，IoU 0.30 / 0.50） | 目录车：无斜距格（scout 干扰车真值不带斜距、BODY 真值不列干扰车，目录车全部落 NA 档，见斜距表）。红立方体：same_instance_by_design 50-65: 29/466（6.2%） / 18/466（3.9%）；same_instance_by_design >=65: 2/89（2.2%） / 0/89（0.0%）（recall.json `default-geometry`） | scout-1 T0-oracle 0/45（≥65 m）；VLM C2 S 层 36.7% | 若远端召回接近 0，则预训练检测器不能覆盖默认路线远端，换栈需另立数据/模型工作；若明显非零，则「持续检测」在远端有输入 | 任何闭环跟踪成绩；在线 5 Hz 下的召回 |
| R2 脚本红车召回（BODY 全档，S/M/L） | S: 0/198（0.0%） / 0/198（0.0%）；M: 123/370（33.2%） / 106/370（28.6%）；L: 0/12（0.0%） / 0/12（0.0%）（recall.json `body-all`） | 无既有证据 | 若目录车可检而红立方体不可检，则演示目标本身是换栈的阻断项，需换目标外观或换样例策略 | 换成网格车后的召回 |
| R3 FP/帧（描述性） | body-armA · T0-bank-a2: 0.626563；body-armB · T0-bank-td: 2.019531；catalog-448 · T0-bank-td: 0.674107；scout-1 · T0-bank-a2: 1.731915；scout-1 · T0-oracle: 0.028369；scout-4 · T0-bank-td: 0.276091；scout-4 · T0-oracle: 0.059875（recall.json `fp_per_frame`） | 无同口径既有证据（qual-3 的 NO_CANDIDATE/TENTATIVE 是决策计数，不并列） | 若 FP/帧高，则关联层每帧要在更多干扰候选中匹配；配合 R5 读 | 换 ID 频率（由 R4 直接测量） |
| R4 8 s / 13 s 窗口 ID 保持率 | body-arm-a-trial-2-attempt-2：botsort 8s 0.0（D=3）/13s 0.0（D=3），bytetrack 8s 0.0（D=3）/13s 0.0（D=3）；body-arm-a-trial-5：botsort 8s 0.0（D=6）/13s 0.0（D=6），bytetrack 8s 0.0（D=6）/13s 0.0（D=6）；body-arm-b-trial-2：botsort 8s 0.0（D=25）/13s 0.0（D=7），bytetrack 8s 0.0（D=25）/13s 0.0（D=7）；body-arm-b-trial-5：botsort 8s 0.014706（D=68）/13s 0.0（D=42），bytetrack 8s 0.015385（D=65）/13s 0.0（D=39）；scout-1：botsort 8s 0.411215（D=107）/13s 0.260417（D=96），bytetrack 8s 0.551724（D=116）/13s 0.398148（D=108）；scout-4：botsort 8s 0.238659（D=1014）/13s 0.0（D=959），bytetrack 8s 0.255274（D=948）/13s 0.0（D=893）；D=0（保持率不可定义：无可见帧或起点全部无绑定）：body-arm-a-trial-1-attempt-4、body-arm-a-trial-3、body-arm-a-trial-4、body-arm-b-trial-1、body-arm-b-trial-4（replay.json） | 指定→确认实测 8–13 s 只给出窗口长度来历 | 离线回放是必要条件读法：若离线也保不住，则在线更难；若离线保得住，只说明归档几何上关联层不先天失败；须与 R1 并读区分「检测不到」与「关联丢 ID」 | 在线可行性；真实指定期的保持率；同机负载下的表现 |
| R5 静态 margin ≥0.1 通过率（S / M / L） | Δ13s: 5/7（71.4%） / 19/85（22.4%） / 82/208（39.4%）；Δ1s: 40/42（95.2%） / 98/119（82.4%） / 113/139（81.3%）；Δ5s: 42/46（91.3%） / 75/103（72.8%） / 74/151（49.0%）（margin.json） | scout-4 174/187、scout-1 0 机会 | 若 S 层通过率低，则同类多车场景仍需 ReID 或人工，定局 ④ 不变 | 训练后的 ReID 能力 |
| R6 臂 B/C 相对 A(base)/A(C2) 的 S 层差值（oracle 候选） | A_base G1-S 2/30（6.7%）；A_C2 G1-S 11/30（36.7%）；B G1-S 6/30（20.0%）；C G1-S 2/30（6.7%）（vlm-arms.json） | A(C2) G1 S 36.7%（原 IoU 口径）、G1t/G2t 65.2% | 若 oracle 候选下裁图/编号选择显著高于整帧，则值得另立探针用检测器候选复测 B/C；若不高，则裁图放大不是 S 层的出路 | 检测器候选下的成绩；任何架构结论 |
| R7 臂 D 相对各 VLM 臂（oracle 候选） | B G1 126/210（60.0%）、G2 36/49（73.5%）、G4 5/86（5.8%）、G3 严格 1/48（2.1%）；C G1 83/210（39.5%）、G2 22/49（44.9%）、G4 0/86（0.0%）、G3 严格 4/48（8.3%）；D G1 100/210（47.6%）、G2 25/49（51.0%）、G4 28/86（32.6%）、G3 严格 19/48（39.6%）（vlm-arms.json） | — | 若 D 在 G1/G2 接近 B/C，则这两类指令的选择步骤有无 VLM 替代方案值得另测；G3/G4 另看 | 「不需要 VLM」；检测器候选下的成绩 |
| R8 Mac 检测 p95 与 5 Hz 预算 200 ms | CPU p95 68.071273 ms、MPS p95 29.761829 ms（5 Hz 预算 200 ms）（latency.json） | DETECT-001 detector 74–98 ms（CPU） | 若 p95 > 200 ms，则桌面 5 Hz 持续检测在本机不成立（与 Jetson 无关）；若 ≤，则只说明单模型单进程可达 | 同机 Unity 负载下的时延；Jetson 时延 |

## 账目与只读（AC-9）

证据：`docs/evidence/P1-ENG-FAST-001-ledger.json`。计数：{'download': 1, 'gpu5060_base_start': 2, 'gpu5060_query': 1201, 'gpu5060_query_retry': 35, 'mac_start_dinov2': 3, 'mac_start_yoloe': 2, 'model_api_call': 0, 'pip_install_5060': 0, 'pip_install_mac': 1, 'scenario_session_run_id': 0, 'training_gpu_hours': 0, 'unity_play': 0}；`runtime/` 前后全树清单一致：True。零 Play、零 ID、零训练、零云端；产物只在 `outputs/eng-fast/` 与 `docs/evidence/`。

## 限制与不承诺（§6.1 摘要）

1. 离线、桌面、oracle 候选/参考条件下的描述性结果；T0-oracle 只是 oracle-pointed 可检测性上界；配对表只是同行交集。
2. gold 为 amodal 投影 AABB（`UNVERIFIED`）；目录帧距离是相机轴向深度，与斜距分表不混算。
3. C2 adapter 不套用到 B/C；A(base) 才是 B/C 的同模型对照。
4. 回放不含 Unity 同机负载、云台/机身闭环、5 Hz 实时约束与 K1 发布门；保持率不是闭环跟踪主张。
5. 红立方体只有同一锚点、同一路线的样本；其他路线/光照无证据。
6. 不主张 Jetson/TensorRT 性能、开放词表、真实航拍、跨环境；不闭合 DETECT-001 验收 4；不改任何 LOOP-001 verdict。
7. 单次 greedy、单 seed；bootstrap CI 只是描述性区间；不冻结任何合格线。
8. 评 scout-1 与 arm A 时参考池只有 {a2}（`BANK_PARTIAL(5/9)`），相应 T0-bank 数字是「单来源参考库」条件下的数字。
9. 保持率分母把 `UNRESOLVED_END_MISS` 算作未保持，读数偏保守；须与 R1 远端召回并读。
