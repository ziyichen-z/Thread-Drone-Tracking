# 评估集 S 层初步读数（2026-10-10，supervisor 会话临时计算；非证据）

性质：supervisor 会话在聊天中用本机既有文件临时算出，未经独立复核、无脚本入仓；只用于决定 VLM 线下一步的顺序，阶段 0 审计脚本须复算并以其结果为准。

## 1. 输入

- 评估集：`outputs/eng-sft/P1-ENG-SFT-002/data/eval.jsonl`（609 行；字段 `group`、`gold_state`、`gold_bbox_2d_1000`、`stratum`）。
- C2 预测：`outputs/eng-sft/P1-ENG-SFT-002/returned/sft-20260918T223245Z-bd1f5ebb/predictions/eval-adapter.jsonl`（sha256 前缀 `0ccb4f1e262f5fc5`，与 `docs/evidence/P1-ENG-SFT-002-eval-summary.json` 的 `predictions_sha256` 一致）。
- 零样本预测：`outputs/eng-sft/P1-ENG-SFT-002/logs/job-a-live-20260918T2134Z/returned/sft-20260918T202551Z-bd1f5ebb/predictions/zero-shot.jsonl`（前缀 `f6e31c386949fa64`，与 `baseline_predictions_sha256` 一致）。
- 判定口径：成功 = `status_pred` 为 unique 且首框与 gold 首框 IoU ≥ 0.5（与 `evaluate.py` 单目标口径一致）；贴边 = gold 框任一坐标 ≤ 3 或 ≥ 997（0–1000 归一化）；短边 px = min(w·640, h·480)。

## 2. 读数

G1∪G2 单目标行按现行 `stratum` 与失败类型（C2）：

| 层 | n | 成功 | 答 none | 框落别处（IoU < 0.1） | 框偏（0.1–0.5） | 答 ambiguous |
|---|---|---|---|---|---|---|
| S | 43 | 19 | 11 | 7 | 4 | 2 |
| M | 113 | 92 | 9 | 6 | 2 | 4 |
| L | 103 | 90 | 10 | 2 | 1 | 0 |

S 层按贴边拆分（C2）：

| 子集 | n | 成功 | 答 none | 框落别处 | 框偏 | gold 短边中位 | gold 长边中位 / 最大 |
|---|---|---|---|---|---|---|---|
| 贴边 | 30 | 11 | 11 | 3 | 4 | 19 px | 53 px / 120 px |
| 不贴边 | 13 | 8 | 0 | 4 | 0 | 28 px | 未算 |

其他：
- 贴边 gold 占比：G1∪G2 S 30/43、M 57/113、L 55/103；G4 S 3/22、M 14/38、L 9/26。
- C2 答 none 的误报按层：S 11/11 贴边、M 6/9、L 8/10。与阶段摘要「贴边 134 行漏报 18.7%」同一现象。
- 不贴边 S 行的类别：car 5、taxi 4、container truck 3、pickup truck 1；G1∪G2 中没有短边 < 23 px 的未截断车辆。
- G3 歧义（C2）按层：S 21 行中答 unique 13、只报 2 候选而 gold 为 3 的 5、严格正确 3；M 14 行严格正确 6；L 13 行严格正确 3。
- 零样本 S 层：答 none 23、解析失败 12、成功 4、框落别处 4。

## 3. 读法与对下一步的影响

- 现行 S 层七成是被画面边切掉的近车，不是远处小车；S 层主要失败是对半截车答 none，全部落在贴边子集。真正的远处小目标只有 13 行，失败形态是选到别的对象，不是看不见。
- 因此「ROI 放大 / 更高分辨率补像素」不是当前评估集暴露的首要问题；首要问题是部分可见对象的 gold 定义与模型对半截车的回答方式，这正是持久任务「入画即跟」时刻的情形。
- VLM 线排序：阶段 0 审计（本文件待复算与补全） → 接口 B 零训练探针（按 S/M/L × 贴边分层、两级成功率） → 分类器出来后做必要性基线与跨场景 → 训练只在短板被定位为数据时才开。解冻 ViT、换模型、高分辨率采集后置。
- 快层对 S 档车辆的召回约 0.9 到 0.95（`docs/evidence/P1-ENG-FAST-002-report.md` R3 H），接口 B 的候选上限在 S 层不是主要问题，但探针仍须分开报端到端与候选充分条件下两级成功率。

## 4. 限制

- 单次临时计算，未做重复运行；贴边阈值 3‰ 为 supervisor 选定；未用对象真值重算 amodal 框与可见比例；G4 S 行短边未算；未统计每帧对象数。以上均为阶段 0 审计待补项。
