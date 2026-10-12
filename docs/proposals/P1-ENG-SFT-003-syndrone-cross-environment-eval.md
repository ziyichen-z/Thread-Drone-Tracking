# P1-ENG-SFT-003 — SynDrone 全新虚拟环境三态评估集与零样本基线（只评不训）

Status: PROPOSED（D2，2026-09-13；回应接受侧 D1 首次 `REVISION_REQUESTED`（AR1-1…4）——**该裁定原文已被构思会话整文件覆盖丢失，待接受角色重写**；用户关闭 SFT-001 后改为自带三态规则、解析器与评分器；S0/S1 下载与试读待用户授权）；**PAUSED_BY_USER（2026-09-13）**——用户指示暂停，S0/S1 授权申请搁置，恢复由用户决定
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（Claude Code `/fable`，Fable 池）
Created: 2026-09-12
Last updated: 2026-09-13

> 由用户 2026-09-12 训练线方向讨论拆出（账本「训练线方向讨论四项定局」），2026-09-13 用户关闭 `P1-ENG-SFT-001` 并指示「继续 003
> 的工作」（账本「用户关闭 SFT-001、继续 SFT-003」）。本项现在**自带**三态标签规则、prompt、严格解析器、评分器与收据（数据源无关，
> 后续可加 Unity 或其他适配器），在 SynDrone（CARLA 渲染、资产与车辆分类学都不同于 SimplePoly City 的合成航拍）上建一份冻结的三态
> 评估集，并以 Qwen3-VL-2B 零样本基线一次（用户按探针方式在 5060 自跑，零租金）——与 Unity 零样本探针（`UT-OFFLINE-PROBE-2026-09-12`，
> 非门证据）作描述性对照。**SynDrone 不进任何训练**；本项不训练。`P1-ENG-SFT-002` 维持用户暂停。`Workflow: engineering-v1` 只是
> 申请；§5 为申请值。**按 workflow §4.1 第 8 要素，S1 只读试读数字落盘前，接受角色不得冻结适配器 schema 与评估集规模**（本稿 §8
> 只有公开资料与 HEAD 探测到的包体积）。

## 1. 目的与价值

1. 给「语言选框三态协议」一份与训练环境无关的考卷：同一三态定义、同一评分器，图像分布与类别闭集都不同。将来任何在 Unity（或其他
   来源）上训练的模型都可在此零样本考核，陈述「协议行为是否迁移到未见合成环境」。
2. 先取得基础模型在此环境的零样本基线：类别选框成功率、严格歧义报告率、none 率、误报率、延迟——与 Unity 探针并列，看零样本的弱点
   （类别词、歧义零报告、小目标）是否跨环境一致。这是后续训练目标是否成立的第二份证据（第一份是 Unity 探针）。
3. 交付可复用的工具：统一对象记录 → 三态 → 评估集 → 盲文件 → 解析/评分，数据源无关。

不主张真实航拍效果（合成到合成是迁移到真实的必要非充分条件）；不训练；不接入运行时；不比较模型。

## 2. 范围与不做的事

**交付闭集（两个准备步 + 一个 K4 候选 + 一个用户自跑的零样本基线）：**

| 步/# | 内容 | 授权 |
|---|---|---|
| S0 | 许可与条款核对记录：仓库 `LICENSE`（Apache-2.0，覆盖代码）、分发页无条款、论文引用要求；结论入报告，不满足则 `CLOSED_LICENSE` | 用户授权 |
| S1 | 下载 `splits.zip`（6.6 KB）+ **一个** town 的 Color 包（首选 Town01，4.98 GB；含 RGB、语义分割、相机外参、框真值）到 T7 或 5060；只读试读：标注文件格式（2D/3D、字段、类别 id）、每帧对象数与类别分布、图像尺寸、可见性能否由语义掩膜推导；数字入 §8 → D2 | 用户授权 |
| 1 | `tools/eng_sft3/receipts.py`（本项收据）、`adapters/syndrone.py`（原标注 → 统一对象记录）、`three_state.py`、`build_eval_set.py`（评估集、盲文件、泄漏/完整性断言、冻结收据）、`prompt_v2.py`（词表段可替换）、`parse.py`、`evaluate.py`；无模型夹具测试 | — |
| 2 | 受版本控制冻结工件：`docs/evidence/P1-ENG-SFT-003-{eval-manifest,integrity-report}.json`（各 ≤ 2 MB） | — |
| 3 | 本地：`outputs/eng-sft3/syndrone-eval.jsonl`（含 gold）、`syndrone-eval.blind.jsonl`、`receipts/`；原始下载件存 T7 `TDT-SYNDRONE/`（不入库） | — |
| 4 | 零样本基线：用户在 5060 上按本项冻结的盲文件、prompt 与运行脚本跑 `Qwen/Qwen3-VL-2B-Instruct` 一次；预测回传后本地评分；结果代录 `docs/unity-test-log.md`（`OFFLINE_GPU_RUN`，零 Play） | 用户授权（模型已在 5060） |
| 5 | 报告 `docs/evidence/P1-ENG-SFT-003-report.md`：许可记录、试读数字、适配规则、评估集实取、零样本基线各组指标与失误解剖、与 Unity 探针的描述性对照、字节与执行收据 | — |

**不做的事：** 不训练、不用 SynDrone 或任何数据微调；不下载全部 129.6 GB（只下载 S1 的一个 town，不足再申请第二个）；不做深度/LiDAR；
不做真实航拍；不比较多个模型；不接入 `controller/`；不再分发 SynDrone 数据（仓库只存 manifest 与 SHA）；不发布；不改任何旧工作项。

## 3. 接口与数据契约

**输入闭集（只读；身份 = 下载后现算 SHA 记入输入清单，不手写）：** `splits.zip`、`Town01_Opt_120_color.zip`（HEAD 探测
4,980,680,712 B；实际以下载后现算为准）及其解包件；只使用官方 test split 中的帧作评估候选。不读取其他 town、depth、lidar。

**统一对象记录（适配器输出；schema `p1-eng-sft-003/object/v1`）**

| 字段 | 规则 |
|---|---|
| `object_id` | 标注实例 id（跨帧稳定则沿用，否则 帧内序号） |
| `class_word` | ∈ 词表闭集（S1 定；预计 car, truck, bus, motorcycle, bicycle；rider 合并类按其载具计）；非车辆类别（person 等）不入执行域 |
| `color_word` | 恒 `None`（无颜色标注；本项不生成颜色指令） |
| `visible_norm_xywh` | 2D 框归一化 top-left xywh；若原标注只有 3D 框，用提供的相机参数投影为 AABB 并裁剪到画幅（与 Unity gold 同为 amodal 投影口径），投影代码与投影残差核对写入 §8 |
| `status` | `NOT_IN_VIEW`（框不在画幅内或投影无效）；`TOO_SMALL`（可见短边 < 12 px）；`TRUNCATED`（框触及画幅边界且裁剪后/裁剪前面积 < 0.25）；`EXCLUDED_OCCLUDED`（语义掩膜中该实例所属类别在框内像素占比 < 0.5，作遮挡代理；若掩膜无实例 id，用类别像素占比并在报告披露）；否则 `OK`。阈值常量逐字取 `tools/dist_data/contract.py`（`MIN_VISIBLE_SIDE_PX`、`TRUNCATION_VISIBLE_AREA_RATIO`、`THETA_OCC`） |
| `referable` | `status == OK` |

执行域 D = 全部 `status ≠ NOT_IN_VIEW` 的车辆对象。SynDrone 无未知类别对象、无 phantom、无动态目标代理。

**表 A 三态派生（`three_state(D, noun)`；本项 noun 只有 `{class}`）**：C = {o ∈ D : class 相等}（本项无未知字段，故可能匹配 =
确证类别相等），M = {o ∈ C : referable}。按序互斥：`none` ⇔ C = ∅；`unique` ⇔ C = M ∧ |M| = 1；`ambiguous` ⇔ C = M ∧ 2 ≤ |M| ≤ 4；
`gray_overflow` ⇔ C = M ∧ |M| ≥ 5（排除，计数）；`gray_definite_plus_uncertain` ⇔ |M| ≥ 1 ∧ C ≠ M（评估 G3′，诊断）；
`gray_uncertain_none` ⇔ M = ∅ ∧ C ≠ ∅（排除，不标 none）。gold：unique = M 的框；ambiguous = M 全部框按 (x1, y1, x2, y2) 升序。

**表 B prompt v2（逐字冻结；`{vocab}` 为词表段，其余段与 Unity 探针 v2 设计相同）**

```text
You are given one aerial image taken by a drone camera. Locate the object described by the instruction.
Instruction: {surface}
{vocab}
Coordinates: bbox_2d = [x1, y1, x2, y2] are integers from 0 to 1000 relative to the image width and height, origin at the top-left corner, x increasing to the right and y increasing downward, with x1 < x2 and y1 < y2.
Reply with exactly one JSON object and nothing else:
- exactly one object matches: {"status": "unique", "bbox_2d": [x1, y1, x2, y2]}
- two or more objects match: {"status": "ambiguous", "candidates": [{"bbox_2d": [x1, y1, x2, y2]}, ...]} listing every matching object
- no object matches: {"status": "none"}
```

SynDrone 词表段（S1 后定稿并逐字冻结；草案）：`Vehicle categories form a closed set of five mutually exclusive labels: bicycle, bus,
car, motorcycle, truck. Always use the most specific label: "car" means a passenger car; "truck" means a cargo truck or lorry and never a bus;
"motorcycle" and "bicycle" include their rider.` surface = `the <class>`。图像原尺寸 1920×1080，处理器默认像素范围，运行时记录
`image_grid_thw`（预计 `[1, 34, 60]`，2,040 视觉 token）；解码 greedy、`max_new_tokens = 160`、batch 1。

**解析器（fail-closed）**：去 Markdown fence 并计数 → JSON → `status` 闭集 → 框长度 4、整数、0–1000、`x1<x2 ∧ y1<y2` → `candidates`
2…8；`parse_error` 闭集 {`JSON_ERROR`, `SCHEMA_ERROR`, `RANGE_ERROR`, `ORDER_ERROR`, `TRUNCATED`}；**任一 `parse_error ≠ null` 即
`status_pred = null`**（原始 status 只存 `raw_status`）；记录 `gen_tokens`、`finish_reason`、`prompt_sha256`、`image_grid_thw`。
预测 `bbox_2d/1000` 与 gold 浮点框算 IoU。

**表 C 评估集（S1 试读后定规模；申请值 ≤ 400 行）**

| 组 | 定义 | 申请配额 | 指标 |
|---|---|---|---|
| G1 | class noun `unique` | ≤ 150（S/M/L 轮转；每类 ≤ 40） | Success@IoU≥0.5（须 status=unique）、误报歧义率、误报 none 率、无效率 |
| G3 | class noun `ambiguous` | ≤ 100 | 报告率；IoU ≥ 0.5 边上的最大基数一对一匹配（≤ 4 × ≤ 8，穷举）TP/FP/FN/F1；严格成功 = 报告 ∧ F1 = 1 |
| G3′ | `gray_definite_plus_uncertain` | ≤ 50 | 诊断：报告率、status=unique 时任一 M 命中率 |
| G5 | class noun `none` | ≤ 100（每类 ≤ 20） | none 率 |

去重键 = (组, 目标对象 / 候选集串 / 类别, 序列, 高度, 俯仰角)，同键帧序号间隔 ≥ 25（25 Hz 下 1 s）、≤ 4 张；层内
`sha256(seed‖frame_id‖键)` 升序，seed `tdt-eng-sft-003-2026-09-12`；分层 S/M/L 按可见短边 32/64 px（原分辨率）。G1/G3/G5 任一为空
→ `EVAL_GROUP_EMPTY`。评分分母 = 该组全部行，任何失败不剔除；预测文件缺行/重复/多余 → 整次 `PREDICTIONS_INCOMPLETE`。
无门槛：本项只报告零样本数字，不设合格线。与 Unity 探针的对照只作描述（不同清单、不同分辨率、不同词表）。

**工件 schema（`p1-eng-sft-003/<name>/v1`）**：`eval-row`（`row_id, frame_id, frame_sha256, sequence, height_m, pitch_deg, group,
gate_row, surface, noun, gold_state ∈ {unique, ambiguous, none, null}, diagnostic, definite_ids[], target_object_ids[],
gold_boxes_norm_xywh[], stratum`）；`blind-row`（`row_id, frame_path, surface, vocab`——无 gold）；`prediction`（同解析器字段 + 评分
字段）；`eval-manifest`（内容、计数、规则常量与实取、jsonl/盲文件行数与 SHA、帧数量与总字节；不含自身/提交 SHA）；`freeze` 收据
（本地，提交后生成：HEAD、冻结闭集文件的跟踪/干净状态与 SHA）；`run-receipt`（5060：模型 revision、env、prompt SHA、盲文件 SHA、
逐行延迟、`image_grid_thw`）。

**写入分层**：A1 实现者：`tools/eng_sft3/`（上列模块）、`tests/test_eng_sft3_{adapter,three_state,parse,evaluate,build}.py`、夹具
（由生产路径从样本 town 产出的 ≤ 5 帧裁片，若条款允许入库；否则合成 JSON 夹具）、`tools/requirements-eng-sft3.txt`、报告、提案
「待裁定」节、状态板（按权限）；A2 受版本控制 `docs/evidence/P1-ENG-SFT-003-{eval-manifest,integrity-report,zero-shot-summary}.json`、
`tests.log`；本地 `outputs/eng-sft3/`（jsonl、盲文件、`receipts/`、回传预测）；原始下载件 T7 `TDT-SYNDRONE/`；A3：Unity 日志条目
`UT-P1-ENG-SFT-003-zero-shot`（接受/辅助代录用户 5060 运行事实与结果指针，`OFFLINE_GPU_RUN`）、复核/接受文件。禁写闭集沿
`P1-ENG-ASSET-001` §3，再加 `outputs/eng-sft/`。红线：不 import `controller.*`；不改运行时任何文件。

## 4. 验收项（AC 表）

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | 许可与来源：报告记录仓库 LICENSE 类型、分发页原文（无条款）、引用条目；下载件 URL、字节、SHA 入输入清单；`splits.zip` 与 town 包解包后文件计数与清单相符；不满足使用条件以 `CLOSED_LICENSE` 终止 | `artifact:docs/evidence/P1-ENG-SFT-003-report.md` §1；`artifact:docs/evidence/P1-ENG-SFT-003-integrity-report.json` | K4 | 2026-09-13 |
| AC-2 | 适配器：原标注 → 统一对象记录；每种 `status` 与投影/裁剪路径有具名回归；只使用官方 test split 帧；若为 3D 框投影，报告给出投影残差核对（与语义掩膜外接框的 IoU 分布） | `test:tests.test_eng_sft3_adapter.AdapterTests.test_status_rules_and_projection`；`test:tests.test_eng_sft3_adapter.AdapterTests.test_only_official_test_split_frames` | K4 | 2026-09-13 |
| AC-3 | 三态与评估集：`three_state` 按表 A，六态各有回归；评估集按表 C 去重/配额/分层生成；`eval-row`/`blind-row` schema 相符；盲文件不含 gold 字段且行数相等；G1/G3/G5 任一为空 → `EVAL_GROUP_EMPTY` | `test:tests.test_eng_sft3_three_state.ThreeStateTests.test_six_states`；`test:tests.test_eng_sft3_build.EvalSetTests.test_quota_dedupe_and_empty_group`；`test:tests.test_eng_sft3_build.BlindTests.test_blind_rows_have_no_gold`；`artifact:docs/evidence/P1-ENG-SFT-003-eval-manifest.json` | K4 | 2026-09-13 |
| AC-4 | prompt、解析、评分：prompt 逐字等于表 B（词表段单独冻结并导出哈希），构造函数只接受 (图像路径, surface, 词表段名)；解析器按表 B 闭集，`parse_error ≠ null ⇒ status_pred = null`；评分器实现一对一最大匹配、分母不剔除失败、完整性检查；全部无模型夹具测试 | `test:tests.test_eng_sft3_parse.ParserTests.test_error_closed_set_clears_status_pred`；`test:tests.test_eng_sft3_evaluate.MatchingTests.test_max_cardinality_one_to_one_matching`；`test:tests.test_eng_sft3_evaluate.CompletenessTests.test_missing_or_duplicate_rows_invalidate_run`；`test:tests.test_eng_sft3_evaluate.PromptTests.test_prompt_builder_cannot_see_gold` | K4 | 2026-09-13 |
| AC-5 | 零样本基线：冻结收据生成后，用户在 5060 用本项运行脚本对盲文件跑 base 模型一次；回传预测经 SHA 与完整性校验后本地评分；`zero-shot-summary.json` 给出表 C 各组指标、S/M/L 与类别分层、失误解剖（框到其他类别 / 同类另一辆 / 无车 / 无效）、延迟 p50/p95；运行事实代录 Unity 日志 | `artifact:docs/evidence/P1-ENG-SFT-003-zero-shot-summary.json`；`artifact:docs/unity-test-log.md#UT-P1-ENG-SFT-003-zero-shot` | K4 | 2026-09-13 |
| AC-6 | 报告与边界：报告含 S0/S1 记录、试读数字、评估集实取、零样本结果与 Unity 探针的描述性对照（明写口径差异）、字节与执行收据；实现 diff 只含 A1/A2；本地目录 ≤ 64 MB（原始件不在内）；不 import `controller.*`；全套测试摘要区分基线已有失败与新增失败 | `test:tests.test_eng_sft3_build.WriteBoundaryTests.test_no_controller_imports`；`cmd:python3 -m unittest discover -s tests > docs/evidence/P1-ENG-SFT-003-tests.log 2>&1; tail -n 3 docs/evidence/P1-ENG-SFT-003-tests.log`；`artifact:docs/evidence/P1-ENG-SFT-003-report.md` | K4 | 2026-09-13 |

## 5. 预算信封（申请值；S0/S1 与零样本基线分别授权，缺项视为 0）

| 项目 | 上限（申请） |
|---|---|
| Consuming | no |
| 下载 | `splits.zip`（6.6 KB）+ 1 个 town Color 包（Town01 4.98 GB；不足时再申请第二个，≤ 6 GB）；存 T7 `TDT-SYNDRONE/`（或 5060 本地） |
| 模型运行 | 零样本基线 1 次（≤ 400 行 + ≤ 8 行冒烟），用户 5060 自跑，模型已在本地；无租金、无 API |
| 训练 GPU·h / 云端 / 上传 / Unity Play / scenario·session·run ID | 0 |
| 本地计算 | 桌面 CPU：解包、适配、试选 ≤ 15 min，峰值 RSS ≤ 2 GB（1920×1080 掩膜） |
| 磁盘 | T7 ≤ 12 GB（zip + 解包）；Mac 本地 ≤ 64 MB 派生工件 |
| 本地构建累计尝试（解包、适配、试选；含失败） | ≤ 5 次；每次 ≤ 15 min CPU |
| 零样本运行启动（含失败/中断；5060） | ≤ 2 次（+ ≤ 2 次 ≤ 8 行冒烟） |
| 用户决策点 | ≤ 3（S0/S1 授权；接受与授权入账；零样本运行与代录） |
| 发布 | 否 |

## 6. 限制与不承诺

- 零样本基线只是描述性数字（单模型、单次 greedy、≤ 400 行），不设合格线，不是门证据；与 Unity 探针的对照口径不同（清单、分辨率、
  词表），只能看趋势。
- 合成到合成的结论不支持真实航拍主张；没有训练就没有迁移主张，本项只为将来的迁移评估准备考卷与基线。
- 遮挡状态用语义掩膜代理，与 Unity 的画家序遮挡不等价；若标注只有 3D 框，2D gold 是投影 AABB（与 Unity 同口径但同样非人工紧框）。
- 词表闭集不同于 Unity（无 taxi/police/ambulance/pickup/suv/container），rider 合并类的口径以 S1 为准。
- 1920×1080 使每张约 2,040 视觉 token，5060 上单行推理估 5–10 s，400 行约 1 小时。
- `DONE` 需实现证据 + `R<n>@K4` 通过 + `UNITY_NA` 经复核附议；零样本运行事实代录不替代复核。

## 7. 必经停点

- 准备步 S0/S1 需用户授权（许可核对、下载、只读试读）；完成后本稿以 D3 补 §8 数字并定稿词表段与规模，接受角色再冻结。
- 表 C 的规模只能等于同一算法的只读试选实取（各组行数、并集帧数、逐张 SHA 绑定、字节、峰值内存同一次产出），正文与试读脚本使用同一实现；不以公开资料或估算冒充实测。
- **唯一停点 `K4`**：AC-1…6 一个候选（工具、冻结评估集、零样本结果、报告），`C1@K4` → `R<n>@K4`；零样本基线是评估执行，不触发
  K3（无模型决策逻辑接入运行时）。不触发 K1/K2/K5。
- Unity 列申请 `UNITY_NA`，须复核附议。

## 8. 只读试读与试运行数字（公开资料 + 2026-09-13 HEAD 探测；真实试读待 S1 授权后补入 D2）

| 项 | 数字 |
|---|---|
| 规模与组织 | 72k 帧，8 个 town（Town01–07、Town10HD），高度 20/50/80 m，俯仰 30/60/90°，25 Hz；官方划分 60k 训练 / 12k 测试（`splits.zip`） |
| 标注 | 每帧 RGB、深度、语义分割、相机外参、框真值（论文：带唯一 id 的框；2D/3D 待 S1 核对）；可移动对象 8 类：car, truck, bus, motorcycle, bicycle, motorcyclist, bicyclist, person |
| 图像 | 1920×1080 |
| 许可 | 仓库 `LICENSE` Apache-2.0（代码）；分发页无条款；论文要求引用 |
| 分发页 | 26 个压缩包共约 129.6 GB；`syndrone.zip` 105 GB；Color 包 4.4–7.8 GB/town |
| HEAD 探测（Content-Length） | `splits.zip` 6,620 B；`Town01_Opt_120_color.zip` 4,980,680,712 B；`Town02` 5,264,997,987 B；`Town10HD` 5,912,972,506 B |
| 本机 | Mac 剩余约 29 GB（不作解包落点）；T7 可写性与余量见状态板/报告 |

## Pending rulings（待裁定）

无。

## Contract conformance（核对表）

待 `C1@K4`。

## Acceptance rulings（复判）

无。

## 决策记录

- 2026-09-12 D1 `PROPOSED`：构思角色落盘；由用户训练线方向讨论拆出。只评不训；原设计复用 SFT-001 三态/解析/评分。
- 2026-09-13 接受侧 D1 裁定：`REVISION_REQUESTED`（首次），AR1-1…4——**原文已丢失**：构思会话 01:10 用整文件覆盖重写本提案，而接受角色
  00:50 已写入该裁定；本机无快照、无副本可恢复。状态板与 Log 保留的摘要：先补可审批的 S0/S1 准备方案（下载件、字节、尝试上限）、
  标签/接口与主张边界；S0/S1 须具体授权后才做；缺真实试读不得冻结 schema 与规模；不更换数据集。**待接受角色从其会话重写该块**，
  本条只是占位，不代替原文。
- 2026-09-13 D2（构思角色；回应上述摘要，并因用户关闭 SFT-001 改为自带三态规则、prompt、解析器、评分器与收据 `tools/eng_sft3/`）：
  新增零样本基线（用户 5060 自跑，零租金）为 AC-5；§5 写明下载件与体积（HEAD 探测）、本地构建与运行的累计尝试上限；S0/S1 待用户
  授权，试读数字落盘（D3）前不冻结 schema 与规模，正文规模须等于同一算法的试读实取；接口与主张边界见 §1/§6。轨道申请待裁定；
  零实现、零下载、零模型运行。设计退修计数 1。
- 2026-09-13 用户暂停（账本同日「用户指示暂停 003、恢复 002」）：本项转 `PAUSED_BY_USER`；D2 内容、设计退修计数 1 与接受角色重写
  丢失的 D1 裁定原文的义务保留；恢复由用户决定。
