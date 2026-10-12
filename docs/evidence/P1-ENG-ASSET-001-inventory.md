# P1-ENG-ASSET-001 — 旧资产适配盘点报告

Work ID: `P1-ENG-ASSET-001`（工程轨道 `engineering-v1`，唯一必经停点 `K4`）
合同: `docs/proposals/P1-ENG-ASSET-001-legacy-asset-inventory-and-minimal-instruction-set.md`
（D3 用户收敛版，2026-09-08 `ACCEPTED`；AC-1…6 与首次接受释义冻结）
角色: 实现（本轮在 Claude Code 备用入口执行）　日期: 2026-09-08
状态: `IMPLEMENTED`（未经接受角色核对轮与独立复核，**不等于 `DONE`**）

本报告只支持事实陈述：不声称语言选框、跟踪性能或任何研究主张，不定义新指标，
不冻结评估集，不关闭任何旧门。全部执行为本地桌面 CPU、纯离线：
**模型/API/GPU/Play/正式 ID/下载/发布 = 0**，原件只读。

## 0. 复用与不变量

- 执行域 = `tools/dist_data/build_catalog.py:550` `frame_world(entry, field_catalog)`，
  调用形态与 `run_pipeline` 的 S7 相同：**不传** `world_xz` / `route_side`，因此
  `nearest_to` / `on_route_side` 恒为 `relation_available=False`，只有
  `viewer_left_of` / `viewer_right_of` 可判（缺口 G-7）。
- 最小程序 = `tools/dist_data/build_catalog.py:644`
  `minimal_program_with_reference(...)`，确定性顺序原样沿用；本项不自写冲突判定。
- `field_catalog` 取 S5 `attempt-2` 原样，**未调用** `apply_audit_downgrades`
  （S6 审计从未执行，本项不伪造降级集）。
- 表面形由 `tools/dist_data/tier1_lang.py:143` `render()` 生成，词表即 ontology/v1 闭集。
- Unity 真值未进入任何控制器/感知路径；本项不运行任何跟踪器，
  `tools/eng_asset/` 不 import `controller.track_loop` / `controller.run_log` /
  `controller.trackers`（机检 `tests.test_eng_asset_inventory.WriteBoundaryTests.test_no_controller_runtime_imports`）。

## 1. 对账与输入清单（AC-1）

一次执行读六件 `attempt-2` 工件并逐件登记字节与 SHA-256，随后逐分片复核
SHA-256 与压缩字节；manifest 计数与冻结期望逐项比较。任一不符即 fail-closed：
只写 `receipts/failure-*.json`，零派生工件（回归
`tests.test_eng_asset_inventory.ReconciliationTests.test_shard_hash_mismatch_writes_failure_receipt_only`）。

| 对账项 | 冻结期望 | 实测 | 结果 |
|---|---|---|---|
| S3 `frames_catalog` 帧数 / 行数 | 43,535 | 43,535 / 43,535 | 相等 |
| S3 分片 SHA-256 | 151 片 | 151 片逐片相等 | 相等 |
| S3 `skipped_invalid_frames` / `skipped_unbound_frames` | 19 / 157 | 19 / 157 | 相等 |
| S4 `splits` train/dev/test/d3 | 2,523 / 13,144 / 8,450 / 0 | 同左（`frame_counts` 与 `frames` 列表长度双侧一致） | 相等 |
| S4 分片 SHA-256 | 7 片 | 7 片逐片相等 | 相等 |
| S5 `field_catalog` 对象 / 车辆 / 双验证 | 690 / 93 / 37 | 690 / 93 / 37 | 相等 |

六件工件的本次实测 SHA-256 由工具写入
`P1-ENG-ASSET-001-fields.json` → `reconciliation.artifact_sha256` 与
`P1-ENG-ASSET-001-instructions-summary.json` → `source_artifact_sha256`
（COORD-007 R7：可派生标识运行时解析，不手写进文档）。

输入清单 `runtime/eng-asset/P1-ENG-ASSET-001/receipts/input-manifest.json` 按阶段
保存 `before`/`after` 两份并逐条比较，本次盘点执行的 **164** 个输入文件执行前后**逐条相等**（`equal: true`；6 件工件 + 151 个 S3 分片
+ 7 个 S4 分片）；面板阶段另登记
`inventory.json`、指令逐行文件、`label-audit.md` 与 60 张归档帧原图，同样逐条相等。
`inventory.json` 在盘点阶段只做完整性登记、不解析（AC-1 释义允许图像 SHA 取已核验的
S1 引用），其 `records[].sha256` 索引在面板阶段加载，逐张读图时与实际字节比对。

## 2. 问题 1 — 类别、颜色、框哪些可用，哪些仍需验证（AC-2）

对账域 = S3 中 `layout_binding_valid ∧ sidecar_complete` 的行：
**43,535 帧全部入域，排除 0 行**；域内 (帧, 车) 对 **57,430**，与指令逐行文件行数
逐字相等（`tests.test_eng_asset_inventory.FieldTableTests.test_object_table_sums_match_s3_referable_counts`）。

| split | 帧 | (帧,车) 对 |
|---|---|---|
| train | 2,523 | 3,305 |
| dev | 13,144 | 20,617 |
| test | 8,450 | 11,231 |
| 未入划分 | 19,418 | 22,277 |
| 合计 | 43,535 | 57,430 |

按（布局类, 采集族, split∪`unassigned`, 用途类）共 30 个桶，逐桶三量见
`P1-ENG-ASSET-001-fields.json` → `buckets`；布局类分列不合并：`default` 27,686 帧、
`scene-004` 15,849 帧，覆盖 15 个采集族。

**三栏回答：**

| 字段 | 可用（USABLE） | 仍需验证（UNVERIFIED） | 不可用（UNUSABLE） |
|---|---|---|---|
| 类别 `class` | 93/93 S5 目录车 `class_verified` | — | — |
| 颜色 `color` | 37 辆 `color_status=VERIFIED`（词表 blue/gray/green/purple/red/yellow） | 37 辆 `GROUP_INCONSISTENT` + 19 辆无主色 = 56 辆 | — |
| 框 `visible_norm_xywh` | — | 全部 57,430 行（几何投影，非人工标注） | — |
| 布局车条目 | — | — | 8 辆无 S5 条目（`NO_S5_ENTRY`） |

101 辆布局车逐辆一行（`fields.json` → `layout_vehicles`，含逐 split OK 帧数、
最佳短边、S5 有无条目、可用性与证据指针）：37 `USABLE` / 56 `UNVERIFIED` /
8 `UNUSABLE`。8 辆无 S5 条目者：`Vehicle_Bus_color01`、`Vehicle_Car_color01 (2)`、
`Vehicle_Car_color02 (3)`、`Vehicle_Pick up Truck_color02 (3)`、`Vehicle_Police Car (3)`、
`Vehicle_SUV_color01 (7)`、`Vehicle_SUV_color02 (1)`、`Vehicle_SUV_color03 (2)`。
两个布局类各含同一 101 辆的位置版本，按布局类分列统计，不合并。

**证据指针（UNVERIFIED / UNUSABLE 逐条）**：颜色降级取 S5 记录的
`color_status` 与 `color_downgrade_reason`，并指向 `P1-VLM-DATA-002` 颜色诊断
（状态板 2026-09-07「补采不会移动 U_F1」）；框的 UNVERIFIED 依据是
DATA-001 S6 人工审计从未执行（`docs/implementation-status.md` 工程继承清单），
本项 n ≤ 60 的抽查是描述性的，不构成审计通过。

## 3. 问题 2 — 沿用 Tier-1 模板能形成哪些无歧义指令（AC-3）

七值互斥判定（合同 §3 表 C）全部由既有函数返回派生；逐 split × `mother_usage`
的完整直方图见 `P1-ENG-ASSET-001-instructions-summary.json`。合计：

| `uniqueness_status` | train | dev | test | 未入划分 | 合计 |
|---|---|---|---|---|---|
| `UNIQUE_CLASS` | 605 | 14,901 | 6,553 | 16,913 | 38,972 |
| `UNIQUE_CLASS_COLOR` | 0 | 447 | 934 | 1,545 | 2,926 |
| `UNIQUE_RELATION` | 95 | 1,102 | 578 | 562 | 2,337 |
| `COLOR_UNVERIFIED` | 247 | 3,491 | 1,108 | 1,219 | 6,065 |
| `AMBIGUOUS_SAME_CLASS` | 848 | 625 | 809 | 1,009 | 3,291 |
| `WILDCARD_UNKNOWN_CLASS` | 1,510 | 51 | 1,249 | 1,029 | 3,839 |
| `NOT_CLASS_VERIFIED` | 0 | 0 | 0 | 0 | 0 |
| 合计 | 3,305 | 20,617 | 11,231 | 22,277 | 57,430 |

**有唯一指令的行合计 44,235 / 57,430（77.0%）**，其中关系程序 2,337 行——
`viewer_left_of` / `viewer_right_of` 在 S7 调用形态下确实可用，这是 §8 表 2 的
近似规则（明确「不算静态关系」）没有覆盖的部分，也是本表与 §8 规划数字差异的
主要来源；§8 数字按合同 §6 保持「规划估计」定性，不升级为证据。

去重与重叠（域 = 各 split 的 `UNIQUE_*` 目标行）：

| split | 去重 (对象, 程序) | 去重对象 |
|---|---|---|
| train | 32 | 19 |
| dev | 99 | 36 |
| test | 116 | 53 |
| 未入划分 | 161 | 58 |

- train∪dev∪test 有 ≥1 唯一指令的目录车 **84 / 93**（含未入划分为 86 / 93）。
- train∩test **14** 辆、dev∩test **10** 辆、test 独有 **31** 辆。
- S4 `held_out_objects.held_out_object_ids` 共 32 个，其中 20 个出现在 test 的
  `UNIQUE_*` 行中，标记原样继承。
- test 的 53 辆按类：suv 11、taxi 10、pickup truck 9、car 5、container truck 5、
  bus 4、truck 4、police car 3、ambulance 2。

**`WILDCARD_UNKNOWN_CLASS` 的成因（全量复算，AC 未要求，本节据实补充）**：3,839 行通配阻断
不是分散噪声，而是单一来源。含通配行的 **1,644 帧中 100%（0 例外）** 的 `blocking` 里含 §2 那
8 辆无 S5 条目的布局车之一——它们的 `class_word` 在 `frame_world` 里走
`build_catalog.py:572` 的 `elif record is None` 分支取 `None`，按 `_noun_conflicts` 的通配语义
阻断同帧**所有**可指称车的唯一性。逐辆命中帧数：`Vehicle_SUV_color03 (2)` 819、
`Vehicle_SUV_color02 (1)` 270、`Vehicle_Car_color01 (2)` 247、`Vehicle_Bus_color01` 225、
`Vehicle_Car_color02 (3)` 206、`Vehicle_Pick up Truck_color02 (3)` 200、
`Vehicle_Police Car (3)` 160、`Vehicle_SUV_color01 (7)` 131。

影响集中在 train：**train 3,305 行中 1,510 行（45.7%）** 因此不可用（dev 51、test 1,249、
未入划分 1,029）。且**在冻结归档内不可修复**：这 8 辆按 §2 从未以 `OK` 出现于任何 BOUND 帧，
而 S5 目录正由 OK 观测构建（`build_catalog.py:407-438`），补条目必须新采集，该额度随
`P1-VLM-DATA-002` 的终止处置出局。

**两条机制的区分（AC-3 修订 3）**：表 C 第 5 值统称「执行域未知类别阻断体」，闭集有两条来源——
(a) 无 S5 条目的**非幻影布局对象**；(b) **源身份未绑定的动态目标**。在 attempt-2 上只有 (a) 发生：
`target_source_bound` 为真 43,535 次、为假 **0** 次，故 (b) 在冻结输入上不可达。两条机制各有具名回归
（`test_missing_s5_blocker_yields_wildcard_unknown_class` 走生产 `frame_world` +
`minimal_program_with_reference` 复算 (a)；`test_unbound_dynamic_target_yields_wildcard_unknown_class`
保留覆盖 (b)），判定条件、优先序与计数不变。

对用户问题 1 的直接含义：这 8 辆不是「8 个不可用目标」，而是**指令唯一性的最大单一破坏源**，
以遮挡体身份连坐整帧。本段只陈述计数与成因，不推断任何可用性结论或修复方案。

**重叠表只描述既有划分**：既不得读作「对象从未出现在训练图像中」，也不构成
正式评估集；`frozen_evaluation_set: false` 写在摘要里，正式评估集由后续任务确定。

**母集候选复算对照**：`prospective_mother_eligible` 在对账域全部帧上得
**27,074**，与 DATA-002 上界报告的 27,074 **逐个相等**；AC-3 要求的 S4 已划分帧
域为 **17,337**（train 700 / dev 8,572 / test 8,065 / d3 0），差 **9,737** 全部来自
未入划分帧（9,737）。差异来源仅是统计域不同，谓词逐字复用上游函数，未作放宽。
本项不调用 S7 门、不物化 S8、不写 `mother_candidates`、不冻结任何评估集。

## 4. 分层标签抽查（AC-4，判定已取得）

抽样契约与逐张清单见 `P1-ENG-ASSET-001-label-audit.md`（种子/配额已先行提交，
面板生成绑定该提交）。分层分母与实取：

| 层 | 定义 | 分母（行 / 去重对象） | 配额 | 实取 |
|---|---|---|---|---|
| S1 | `color_status != VERIFIED` | 26,027 / 56 | 20 | 20 |
| S2 | `uniqueness_status ∈ {AMBIGUOUS_SAME_CLASS, WILDCARD_UNKNOWN_CLASS, UNIQUE_CLASS_COLOR, UNIQUE_RELATION}` | 8,482 / 36 | 15 | 15 |
| S3 | `short_side_px < 32` | 467 / 23 | 15 | 15 |
| S4 | `uniqueness_status = UNIQUE_CLASS ∧ short_side_px ≥ 64` | 15,983 / 27 | 10 | 10 |

四层均足额，共 **60 张**面板（上限 60），每对象每层 ≤ 2 行，层内按
`SHA-256(seed‖frame_id‖object_id)` 升序。面板与原图副本落本地
`outputs/eng-asset/P1-ENG-ASSET-001/panel/`（按 AC-4 修订 1 / AC-6 修订 1 自
`runtime/eng-asset/P1-ENG-ASSET-001/panel/` 原字节迁移，见 §6 迁移收据）；逐张 `overlay_sha256` 回填清单，
`panel-receipt.json` 由工具在运行时解析并记录配额文件的提交 SHA（`quota_file_commit`）
与其 `git status --porcelain` 为空的断言，本报告不复写该标识。

**用户判定已取得并代录（2026-09-11）**：判定原文由辅助角色逐字代录进
`docs/unity-test-log.md` 的 `UT-P1-ENG-ASSET-001-label-audit`（`OFFLINE_VISUAL_CHECK`，零 Play），
统计由工具只读该条目计算，本报告不复制原文。60 张全部判定齐备（`Judgment state: COMPLETE`，
索引 1–60 升序且与清单逐项相等）。逐层结果：

| 层 | 面板 | 已判定 | 类别 对/错/不确定 | 颜色 对/错/不确定 | 框 对/错/不确定 |
|---|---|---|---|---|---|
| S1（颜色未验证） | 20 | 20 | 20/0/0 | 20/0/0 | 20/0/0 |
| S2（歧义或带色/关系程序） | 15 | 15 | 15/0/0 | 14/1/0 | 13/0/2 |
| S3（短边 < 32 px） | 15 | 15 | 15/0/0 | 15/0/0 | 9/0/6 |
| S4（类别唯一且短边 ≥ 64 px） | 10 | 10 | 10/0/0 | 10/0/0 | 10/0/0 |
| 合计 | 60 | 60 | 60/0/0 | 59/1/0 | 52/0/8 |

错误类型合计：颜色错 1（其余四类均 0）。「不确定」单独计数、不计为对；四层均非空。

**可陈述的事实（描述性，n ≤ 60，不构成审计通过，也不改变任何字段的验证状态）**：

1. **类别 60/60 判对**，无一例类别错——与 §2 的 S5 `class_verified` 93/93 一致，未发现反例。
2. **颜色 1 例判错**（#27 = `Vehicle_Bus_color03`）。该对象在 S5 是 `color=gray`、
   `color_status=**VERIFIED**`、`dual_verified=true`，在 §2 属**可用（USABLE）**的 37 辆之一——
   不是未验证集。用户原话指该车实际灰红相间、目录色名按序号标注。**因此这是本次抽查对一个
   已双验证颜色标记发现的反例**，而不是对未验证字段的再确认。按合同不据抽查回写 S5、不重算指令、
   不降级该对象，也不据一例推断其余已验证颜色有误；S5 原分类原样保留，反例如实并列记录。
3. **框的 8 例「不确定」全部是边缘裁切**（用户原话：只剩约三成、"擦边"），且**集中在小目标层**：
   S3 占 6/15（40%）、S2 占 2/15，S1 与 S4 各 0。按用户澄清，车身斜放导致轴对齐框四角留背景空隙
   （#27 那类）判「对」，只有被画幅边界切掉大部分的判「不确定」。
4. 因此本次抽查未发现投影框的**语义**错误（错位、张冠李戴）；不确定项全部指向**取景裁切**这一种
   情形。这只是 60 张上的观察，DATA-001 S6 人工审计仍未执行，§2 中框字段的 `UNVERIFIED` 状态不变。

统计收据 `receipts/run-stats-<utc>.json` 绑定实际读入的日志与清单 SHA、所采用的重绘收据，
以及读入清单快照与写出清单两个分列条目（AC-1 修订 1 / AC-4 修订 2，接受侧 2026-09-09 回交项）。

**代录接口按 AC-4 修订 3 冻结**（原先的宽松解析约定作废）：解析器只消费
`### 结构化判定` 的固定表，`### 用户判定原文` 存逐字反馈不参与解析；条目唯一、四条必需行齐备、
`Judgment state: COMPLETE`、表头列序固定、每行五列、`panel_index` 无前导零且升序并与当前清单
**逐项相等**、三判定取值 ∈ {对, 错, 不确定}、错误类型仅以顿号分隔且按闭集顺序不重复。任一不符即
**失败退出**：只新增 `receipts/failure-stats-<utc>.json`（`reason: VERDICT_FORMAT_MISMATCH`，
offending 记问题与行号），不写成功收据、不覆盖已有统计/清单/日志，也不存在把错误转成「不确定」或
全零统计的分支。接受侧已按该格式建立空模板条目（`Judgment state: PENDING`，无示例数据行）。

**面板呈现（AC-4 修订 2，2026-09-08 补充裁定）**：首版把标题栏画在图内、并对短边 < 64 px 的
目标叠加放大插图；接受侧只读查看 20/42 号后裁定「插图覆盖了原图的大部分区域，原坐标框最后被
画在已替换的像素上」不满足 AC-4，交实现角色最小修复。现版：**移除插图**；画布在原帧上方加
16 px 边带放标题，**原帧整幅粘贴、不缩放不裁剪、像素零覆盖**，框按与原帧相同的偏移平移后叠加。
叠加图改用 `quality=95` + `subsampling=0`（4:4:4）——默认 4:2:0 会在标题带与原帧的强色度跳变处
产生数十级偏差，正落在判框的边界上。标题内无唯一程序时的占位符取 ASCII（PIL 默认位图字体无
中文字形，中文会渲染成方块）。

样本身份未变：`panel_index` / `frame_id` / `object_id` / `stratum` / `surface` / 种子 / 配额与
**60 张原图副本**逐项不变（重绘以原图副本为底图，`original_sha256_unchanged` 60/60 为真，
`original_copies_rewritten: 0`），未重新抽样、未增加看图轮次。重绘前须提交当前配额文件并在运行时
绑定其提交——第一次重绘改写清单后，第二次运行被前置正确拒绝（`QUOTA_FILE_DIRTY`），提交后才通过。
两次重绘的差异只有 14 张 surface 为 null 的面板（占位符由中文改 ASCII），其余 46 张字节逐一相同，
是渲染确定性的旁证。收据：`receipts/run-render-fix-<utc>.json`（修前/修后叠加图字节与 SHA、
未变的样本身份与原图 SHA、首次生成与 relocate 收据引用；旧收据原字节保留）。

**接受侧定点确认已完成（2026-09-09）**：接受侧已确认 20/42 号原帧完整且框对应原像素，
用户一次看图随后完成（统计见上）；该确认只验证显示，不替代标签判定或 C/R。

## 5. 问题 3 — 语言选框模块接入现有跟踪器的输入条件与缺口（AC-5）

只读代码检查，**未运行任何跟踪器**。下面这条箭头链是**只读检查对象与数据流示意，不是调用链**——
`protocol.latest_frame_bundle()` 并不是 `TrackLoop.initialize` 的调用上游：前者是外部入口自行取帧
（`controller/tracking_entry.py:79` 用它解析当前 `frame_id`），后者由 `TrackLoop` 自己的
`FrameRepository.load()`（`controller/track_loop.py:110`）读同一目录的精确帧。两条读取路径并存，
发布路径（`observation()` 写桥文件）又是另一条。接入链路（现状）：
`runtime/frames/latest.json` → `controller/protocol.py:61` `latest_frame_bundle()`
→ `controller/track_loop.py:336` `TrackLoop.initialize(frame_id, box_norm)`
→ `controller/trackers.py:42/45` `TrackerPlugin.init/update`
→ `controller/tracking_entry.py:12` `observation()` 写 `runtime/tracking_observation.json`。

**输入条件（现状必须满足，逐条 `file:line`）**

| # | 条件 | 依据 |
|---|---|---|
| 1 | 帧 id 必须绑定到**已完整发布**的 bundle：manifest schema 为 `tethered-frame-manifest/v1`，且图像与元数据两个成员文件都在 | `controller/protocol.py:61-71`；`controller/track_loop.py:89-99` |
| 2 | 初始化只能用**精确保留**的那一帧：`load()` 缺任一成员即 `FileNotFoundError`，元数据 `frame_id` 必须与请求相等，schema 必须匹配 | `controller/track_loop.py:110-123` |
| 3 | **单帧时钟字段的合法性**（非跨帧保证）：schema 必须是 `tethered-sensor-frame/v3`、`capture_monotonic_clock_id` 必须是 `system-stopwatch/v1`、`capture_monotonic_s` 必须是有限非负数值。该函数只接收**本帧** metadata，没有上一帧参数，**不强制跨帧单调**；语言模块若需要时序保证，属新接口 | `controller/sensor_protocol.py:13-43`（调用点 `controller/track_loop.py:126-129`） |
| 4 | 框必须是归一化 top-left `xywh` 且裁剪后非退化，否则拒绝初始化 | `controller/trackers.py:61` `clip_box_norm`；`controller/track_loop.py:340-342` |
| 5 | **初始化只允许一次**：已初始化再调用即 `RuntimeError("track loop is already initialized")` | `controller/track_loop.py:337-338` |
| 6 | 跟踪器可以拒绝初始化帧/框，此时直接抛错，不进入 TRACKING | `controller/track_loop.py:345-347` |
| 7 | `track_id` 必须非空字符串，贯穿观测与日志 | `controller/track_loop.py:230-231, 251` |
| 8 | 置信度来源是显式字段：初始化写 `"placeholder"`、NanoTrack-v2 更新写 `"tracker"`（未校准诊断分，设计 §3.4） | `controller/track_loop.py:354`（初始化）、`controller/track_loop.py:985-993`（来源闭集校验）；`controller/trackers.py:463, 474` |
| 9 | 观测包带 `expires_after_s`（默认 2.0 s）与 `command_id`/`issued_unix_s`，消费侧据此判过期 | `controller/tracking_entry.py:12-20, 48`；`controller/protocol.py:22-35` |
| 10 | 观测原子发布（临时文件 + `os.replace`），不得半写 | `controller/protocol.py:39-58` |

**缺口 G-n（本项只列出，不动代码；归属后续接入任务的停点）**

| 编号 | 缺口 | 归属停点 |
|---|---|---|
| G-1 | **没有「候选框 → 人工确认 → 初始化」入口**：`initialize` 直接接受一个框，链路上不存在候选集、确认动作或拒绝路径；语言模块产生的候选框如何被确认后才允许播种，是新接口 | K3（模型决策与目标身份） |
| G-2 | **没有迟到结果拒收机制**：`initialize` 不比较请求帧与当前 `latest_frame_id`，语言模块若在 N 帧上算出框、到 N+k 帧才返回，只要 N 的 bundle 仍在磁盘就会被接受 | K1（帧协议与时间语义） |
| G-3 | **帧 id 绑定与过期不对称**：入方向只有「文件是否存在」，没有 `expires_after_s` 类的时效判据；出方向（观测）才有过期字段 | K1 |
| G-4 | **没有丢失的显式报告通道**：`state` 只在日志记录里出现（`TRACKING` / `LOST` / `ERROR_REINIT_REQUIRED`，`controller/track_loop.py:65, 560-561, 943, 969`），`runtime/tracking_observation.json` 只承载框与置信度，外部消费者无法从桥文件读到「已丢失、请重新指定」 | K1 + K3 |
| G-5 | **`track_id` 与置信度来源语义未对外定义**：`confidence_source` 的取值闭集与「未校准」含义只存在于代码与设计文本，桥协议未声明；语言模块重新指定后是否换 `track_id`、旧 id 如何作废，无规定 | K3 |
| G-6 | **没有重新指定入口**：`initialize` 的一次性约束与 `ERROR_REINIT_REQUIRED` 之间没有恢复路径；重新指定目前只能重建 `TrackLoop`，会丢失既有日志与 `track_id` 连续性 | K3 |
| G-7 | **`nearest_to` / `on_route_side` 在 S7 调用形态下不可用**：`frame_world` 不传 `world_xz` / `route_side` 时二者恒 `relation_available=False`（`tools/dist_data/build_catalog.py:550-560`、`tools/dist_data/tier1_lang.py:304-312, 338-342`）；本项如实报告，不补这两个入参 | K3（若后续任务要用关系指令） |

**接管行为（语言模块输出的框能否播种既有跟踪器、能跟多久）不在本项**，
按合同并入后续语言选框接入任务，届时用语言模块**实际输出的框**验证；本报告
不作任何跟踪时长、IoU 或恢复能力的陈述。

## 6. 执行收据、边界核对与测试摘要（AC-6）

**执行收据**（`runtime/eng-asset/P1-ENG-ASSET-001/receipts/`）

| 阶段 | 耗时 | 峰值 RSS | 输出 |
|---|---|---|---|
| `inventory`（AC-1/2/3） | 65.1 s | 69.2 MB | 指令逐行 57,430 行 / 1,716,404 B（本地 gz）、`fields.json` 89,133 B、`instructions-summary.json` 76,111 B |
| `panel-plan`（AC-4 抽样） | 0.3 s | 185.8 MB | `label-audit.md` |
| `panel`（AC-4 面板） | 0.9 s | 382.8 MB（加载 S1 索引；当前收据为第三次生成，前两次 376.9 / 382.3 MB） | 60 张面板 3.6 MB + 60 张原图副本 |
| `relocate`（AC-4 修订 1 迁移） | 0.1 s | 26.1 MB | 120 个文件迁至 `outputs/eng-asset/P1-ENG-ASSET-001/panel/`，迁移前后合计 6,401,346 B 逐文件字节/SHA 相等，旧落点 jpg 归零 |
| `stats`（AC-4 修订 3 统计） | 0.3 s | 185.9 MB | `label-audit.md` §5 统计块；收据绑定实际登记的日志与清单快照（R1@K4 F1 返工后重跑） |
| `render-fix`（AC-4 修订 2 重绘） | 0.6 s | 183.9 MB | 60 张叠加图按新呈现重绘（原图副本 0 改写、样本身份 0 变化）；两次运行仅 14 张 surface=null 面板字节不同 |

峰值 RSS 382.8 MB ≤ 1 GB 规划上限；受版本控制的 A2 文件各 ≤ 2 MB（最大 89,133 B）；
两个本地派生目录合计 10,249,590 B（≈ 10.2 MB）≤ 32 MB（AC-6 修订 1 口径：`runtime/eng-asset/P1-ENG-ASSET-001/` 2,156,719 B
+ `outputs/eng-asset/P1-ENG-ASSET-001/` 8,092,871 B，含 Finder 生成的两个 `.DS_Store`；重绘后叠加图因 4:4:4 与 quality=95 变大）。迁移前先单独提交 `.gitignore` 的
`/outputs/eng-asset/P1-ENG-ASSET-001/` 规则（AC-6 修订 1 授予的唯一 A1 增量），再落任何 jpg：
次序反了会让 120 个派生图片短暂成为受版本控制文件，撞上同一条信封上限。

**原件零写入**：输入清单执行前后逐条相等（§1）；写出路径做包含检查，落入禁写闭集
即拒绝并写失败收据（`tests.test_eng_asset_inventory.WriteBoundaryTests.test_output_inside_input_roots_is_refused`）。
本项实现 diff 只含合同 §3 表 A 的 A1/A2：

- A1：`tools/eng_asset/{__init__,receipts,inventory,label_panel}.py`、
  `tests/test_eng_asset_inventory.py`、`tests/test_eng_asset_label_panel.py`、
  本报告；A2：`docs/evidence/P1-ENG-ASSET-001-{fields.json,instructions-summary.json,label-audit.md,tests.log}`
  与本地 `runtime/eng-asset/P1-ENG-ASSET-001/`（git 忽略）。
- A3（其他角色写入，本角色只读）：`docs/unity-test-log.md` 的
  `UT-P1-ENG-ASSET-001-label-audit` 条目、`docs/reviews/P1-ENG-ASSET-001.md`、
  `docs/implementation-status.md` 与提案决策/核对表——本批次一行未动。
- `tests/fixtures/eng_asset/` 未使用：夹具由生产写入器 `ArtifactStore` 在测试临时目录
  内现造（`tests/test_eng_asset_inventory.py` `build_fixture`），不落库存夹具文件，
  故不新增该目录。

**AC-1…5 逐条结论**

| AC | 结论 | 主要证据 |
|---|---|---|
| AC-1（含修订 1） | 满足：六件工件 + 151+7 分片逐项相等；fail-closed 与清单复核均有具名回归；失败只发布失败收据 | §1；`ReconciliationTests`（2 例） |
| AC-2 | 满足：101 辆逐辆有行、8 辆标 `NO_S5_ENTRY`/`UNUSABLE`；对账域计数三方相等 | §2；`FieldTableTests.test_object_table_sums_match_s3_referable_counts` |
| AC-3（含修订 1/2/3） | 满足：七值互斥、null 表示、去重与重叠、母集复算对照均已产出；`NOT_CLASS_VERIFIED` 保护分支不调用会解包裸 `None` 的上游函数；两条未知类别机制各有具名回归 | §3；`InstructionTests`（6 例） |
| AC-4（含修订 1/2/3/4） | 满足：四层足额 60 张、面板落 `outputs/` 并原字节迁移、按修订 2 重绘（原帧完整、标题帧外）、代录机读格式 v1 严格解析与 fail-closed；**用户判定已取得并统计完毕**（60/60） | §4；`LabelPanelTests`（11 例，含生产 `stage_stats` 成功与输入变化两条路径） |
| AC-5（含修订 1） | 满足：10 条输入条件 + 7 条缺口，逐条 `file:line` 与归属停点；链路只作只读检查对象清单 | §5 |

**测试摘要**（COORD-009 纪律：开发期只跑 focused，全套在停点跑一次并写入
`docs/evidence/P1-ENG-ASSET-001-tests.log`，只回显摘要、不带 `-v`）

- Focused：`tests.test_eng_asset_inventory` 11 例、`tests.test_eng_asset_label_panel` 19 例（系统 python3 上 1 例 Pillow 用例 skip，另在 `.venv-yoloe` 实跑 19 例 0 skip），全通过。
- 全套（本批，工作树含本项 A2 本地产物）：`Ran 1138 tests`，
  `FAILED (failures=1, errors=9, skipped=20)`。
- 基线（`4b60238`，临时 worktree，`git worktree add <dir> 4b60238` 后同命令）：
  `Ran 1126 tests`，`FAILED (errors=9, skipped=62)`。基线 worktree 没有 `runtime/`
  数据，故真实归档类用例在那里是 skip 而非执行，skip 数不同不代表回归。

| 分类 | 条目 | 判定 |
|---|---|---|
| **基线已有失败（不变）** | 9 个 `ERROR`：`test_benchmark_reanchor`、`test_detector_scouting`、`test_rate2_protocol`、`test_rate3_difficulty_audit`、`test_rate3_protocol.Rate3GuardTests.test_rate3_reanchor_clock_mismatch_raises_defensively`、`test_rate_study`、`test_scene004_gate0_probe`、`test_scene004_scouting`、`test_scene006_probe` | 全部是导入期失败：系统 `python3`（3.14.6）缺 `cv2`（8 例）与 `numpy`（1 例）。基线（`4b60238` 临时 worktree）与本批逐条同集，非本批引入 |
| **本批新增失败** | **0** | 迁移前的唯一新增失败 `test_dist_data_round4.RealArchiveClosureTest.test_zero_unmatched_and_zero_multi_matched_jpg`（`zero-match 120`）已按 AC-4 修订 1 / AC-6 修订 1 闭合 |

**修后复测（AC-6 修订 1 要求的口径）**：在保留新落点完整 120 张面板、旧落点无 jpg 的**真实工作副本**中
运行具名归档检查 `python3 -m unittest tests.test_dist_data_round4.RealArchiveClosureTest.test_zero_unmatched_and_zero_multi_matched_jpg`
→ `Ran 1 test … OK`（1.031 s，实际遍历归档树，**不是 skip**）。

**停点全套（`R1@K4` F1–F5 返工后重跑）**：`Ran 1156 tests`、
`FAILED (errors=9, skipped=21)`——failures 归零，9 个 ERROR 与 `4b60238` 基线逐条同集。
附的 Pillow 实跑同步为 `Ran 19 tests … OK`。

**Pillow 依赖用例的实际执行**：AC-4 修订 2 的具名回归
`test_panel_preserves_source_frame_and_box_coordinates` 需要图像库解码/编码，系统 `python3`（3.14.6）
无 Pillow，在上面的全套里记为 skip（skipped 由 20 增至 21 即此项）。为不让 skip 冒充通过，
同一份证据文件追加了 `.venv-yoloe/bin/python tests/test_eng_asset_label_panel.py` 的实跑记录
（当前批次为 `Ran 19 tests … OK`；2026-09-09 那次为 9 例，属历史记录），该用例真实执行并通过。其几何契约另由纯算术用例
`test_panel_layout_keeps_frame_unscaled_without_image_library` 覆盖，后者在系统 `python3` 上照常执行。

## 7. 实现期合同问题（交接受角色裁定，实现者不自行解释）

按 AC-6 修订 2 的路由：实现者写本节，接受角色按来源转录进提案「待裁定」并答复。
**问题 1–6 全部已裁定并实现完毕**：问题 1→AC-4 修订 1（迁移，§6）；问题 2→AC-6 修订 2（本节路由）；
问题 3→AC-3 修订 1（保护分支）；问题 4→AC-4 修订 2（移除插图、原帧完整、标题置于帧外，§4）；
问题 5→AC-4 修订 3（代录机读格式 v1 + fail-closed，§4）；问题 6→AC-3 修订 3（两条机制区分与具名回归，§3）。
**接受侧 2026-09-09 只读检查**：显示定点确认 `ACCEPTED`（20/42 号原帧完整、640×496 画布顶部
16 px 放标题、框与原帧同步下移、无插图；60 张叠加图与 render-fix 收据/清单相符，60 张原图副本与
首次 `panel-receipt` 相符）；**统计实现 `REVISION_REQUESTED`，回交两项**，答复与证据见下方问题 7/8。
两项均为既有 AC 下的实现问题回交，不是设计退修，D 退修仍为 2、C/R 仍为 0。


**问题 1（已裁定并执行完毕）：A2 面板落点与 DATA-001 附录 A 的归档闭包检查冲突。**
合同 §3 表 A 把面板固定在本地 `runtime/eng-asset/P1-ENG-ASSET-001/panel/*.jpg`，
而 DATA-001 附录 A 的根清单枚举 `runtime/**` 全部 jpg 并断言每个文件**恰匹配一个
pattern**（`tools/dist_data/roots.py:39-46` `ENUMERATION_ROOTS` /
`ROOT_EXCLUDED_PREFIXES`），`test_dist_data_round4.RealArchiveClosureTest` 据此
要求 zero-match = 0。60 张面板 + 60 张原图副本共 120 个 jpg 全部 zero-match，
该用例因此失败。

本项**不得**自行处置：改落点要动已接受的表 A，改 pattern 要动
`tools/dist_data/`（§2「不做的事」明确禁止），两者都超出实现角色权限。
可选处置（供裁定，不是实现者的选择）：
(a) 在 `roots.py` 的 `ROOT_EXCLUDED_PREFIXES` 加 `runtime/eng-asset/`
（与既有 `runtime/models/`、`runtime/yoloe/` 同类，属协调批次或后续任务）；
(b) 把面板落到 `runtime/` 之外并同步修订表 A；
(c) 接受该用例在「本地存在本项面板时失败」的现状，按 `SCOPE_GAP` 记债。
在裁定前，面板保留原地——删掉它们就没有可供用户看图的对象。

**问题 2（已裁定，AC-6 修订 2 改为「实现者写报告 §7 → 接受角色转录」）：`待裁定` 节的写入权限与表 A 冲突。**
合同 §3 表 A A1 把「提案『待裁定』节」列为实现者可写路径，但
`tools/check_role_writes.py:88-98` 对 `implementation` 角色 deny `docs/proposals/*`
（工作流基础设施，本角色只读）。因此本节写在报告里而不是提案里；若接受角色要求
落到提案，请由接受角色转录或先行调整该机检（属协调批次）。

**问题 3（非阻断，只作披露）：上游 `prospective_mother_eligible` 的裸 `None` 解包**，
见 §6「未验证项与已知限制」第 2 条。

**问题 4（已裁定并实现：AC-4 修订 2）：面板的两处渲染偏离至今未获裁定，却已被 AC-4 修订 1 的「不重新渲染」冻结。**
本报告 §4 逐字把「标题栏避开框所在边」与「短边 < 64 px 的放大插图」标为「实现者判断，
交核对轮确认」，并写明「若接受角色认为放大插图超出『每张只画该行的框与 surface』，
删掉插图重生成即可」。截至本次修订，提案、状态板与 `implementation-status.md` 中没有对这两处的
任何裁定；而同批 AC-4 修订 1 已逐字写「不重新抽样、**不重新渲染**，不增加看图轮次」，把带插图的
这一批图片钉为交付物。**请求在用户看图之前裁定**：插图是否满足 AC-4「每张只画该行的框与
surface」。若判不满足，此刻重生成的代价是零（尚未消耗看图额度）；若等到 `C1@K4` 之后，
重生成将作废用户唯一一次 ≤60 张判定。

**问题 5（已裁定并实现：AC-4 修订 3）：AC-4 的代录条目是跨角色机读交换格式，合同只定了落点、未定格式与失败语义。**
AC-4 规定判定原文由接受/辅助角色代录进 `docs/unity-test-log.md` 的
`UT-P1-ENG-ASSET-001-label-audit`、「统计工具只读该条目出逐层计数」，但没有冻结该条目的机读结构。
实现被迫自造解析约定（`tools/eng_asset/label_panel.py` `read_unity_verdicts`：标题行含条目名 →
markdown 管道表 → 第 0 列纯数字 → 第 1–3 列取值 ∈ {对, 错, 不确定} → 第 4 列按 `、,，/` 切），
**且对不匹配的行是静默丢弃、找不到条目直接返回空**。散文式代录会得到
`judged=0 / unjudged=60` 的统计而不是失败收据——这与 AC-1 自己确立的 fail-closed 范式相反，
且发生在用户看图**之后**，届时踩空不可回滚。请求：冻结表头列序、取值闭集与分隔符，
并补一条 fail-closed（条目缺失或解析行数 ≠ 面板数即写失败收据、不得输出 `judged=0` 当结果）；
相应地给 AC-4 加一条覆盖「代录格式不匹配」的 `test:` 指针。

**问题 6（已裁定并实现：AC-3 修订 3）：表 C 第 5 值的病因括注在冻结输入上出现 0 次，AC-3 的一条 `test:` 指针因此打在不可达分支。**
表 C 第 5 行把 `WILDCARD_UNKNOWN_CLASS` 的病因括注为「（未绑定动态目标）」。全量复算：
attempt-2 的 43,535 帧里 `target_source_bound` 为 `true` 43,535 次、`false` **0 次**，该病因一次都不
可能发生；真实成因 100% 是 §3 新增段落所述的另一条分支。受影响的还有 AC-3 的具名证据
`test:tests.test_eng_asset_inventory.InstructionTests.test_unbound_dynamic_target_yields_wildcard_unknown_class`
——它验证的分支在生产数据上零命中（测试本身正确且通过，只是覆盖不到真实成因）。
请求裁定：(a) 是否更正表 C 第 5 行的病因括注（判定条件本身正确，无须改）；(b) 是否要求补一条
打在真实成因（`blocking` 含无 S5 记录布局车）上的具名测试。本项不自行改动已冻结的表 C。

**问题 7（接受侧回交，已修复）：`stage_stats` 的输入核验未阻止成功写出。**
回交原文指出：`stage_stats` 先登记清单/日志，随后改写同一清单，再无条件以 `successful=True`
保存清单并写成功收据；`save_input_manifest` 只记 `mismatches` 不抛错。后果是首次完整合法判定必然
把 PENDING 清单改成统计正文，导致自身 before/after 不等却仍算成功，真实输入变化也没有失败分支；
成功收据里的 `panel_manifest` 还是写后工件，缺少对实际读入清单的绑定。**判定属实**，已按其要求
区分「读入清单快照」与「合法输出」：

- 清单不再进不变输入集，改为在读取点取**快照**（路径/字节/SHA-256）。不变输入是指令逐行文件、
  S5 目录与 Unity 日志。
- 写出前做唯一一次核验：不变输入逐条相等，且清单自读入以来未被他人改动；任一不符即
  **只写失败收据**（`reason: INPUT_HASH_CHANGED`）、`successful=False`，不写统计、不覆盖既有清单。
- 成功收据分列 `panel_manifest_read`（本次统计所依据的面板身份）与 `panel_manifest_written`
  （本次产出），另记 `overlay_source_receipt`。
- 机制层同步 fail-closed：`ReceiptWriter.save_input_manifest` 现在拒绝「带不符条目却标成功」的调用，
  其余阶段一并受保护。

证据（接受侧指出现有测试只覆盖格式失败分支，故按其要求补生产路径两条）：
`test:tests.test_eng_asset_label_panel.LabelPanelTests.test_stats_success_binds_read_manifest_and_written_output`
（驱动生产 `stage_stats` 走完整合法成功路径）与
`test:tests.test_eng_asset_label_panel.LabelPanelTests.test_stats_fails_closed_when_input_changes_midrun`
（在解析之后、写出之前改动不变输入）。两条在修复前均失败（`AssertionError: InputHashChanged not raised`，
`FAILED (failures=2)`），修复后通过——红/绿各跑一次。

**问题 8（接受侧回交，已修复）：清单丢失当前重绘来源。**
回交原文指出：`stage_stats` 已采用最新 render-fix 的 overlay SHA，却未把 `render_fix_receipt` 传给
`render_audit_document`，该函数因此默认输出「当前叠加图为首次生成版本」——用户判定合法后必然写出
与 overlay SHA 不一致的来源叙述。**判定属实**，已改为：采用了哪份重绘的 overlay，清单就引用哪份
收据（`overlay_source_receipt` 同时进成功收据）。证据同上第一条用例，其中直接断言清单包含该
render-fix 收据路径与其 overlay SHA、且不含「首次生成版本」字样；未重新生成任何图片，看图额度不变。

## 8. `K4` 停点自证（workflow §4.3.1 四项条件）

本节是 `K4` 停点的实现者自证（`C1@K4`/`C2@K4` 已完成，候选交独立复核）。**未经独立复核通过，本项仍是
`IMPLEMENTED`，不是 `DONE`**；`UNITY_NA` 已由复核角色在 `docs/reviews/P1-ENG-ASSET-001.md` R1@K4 附议（仅本项）。

| 条件 | 自证 | 证据指针 |
|---|---|---|
| 1. 实现范围与接口已冻结 | 成立。交付闭集仍是 D3 §2 的三项；AC-1…6 与**十二条**修订（AC-1 修订 1；AC-3 修订 1/2/3；AC-4 修订 1/2/3/4；AC-5 修订 1；AC-6 修订 1/2/3）全部落实，实现期未自行扩大范围：两次落点/呈现变更与代录格式冻结均由接受角色裁定后执行，本轮无新增待裁定 | 提案「待裁定」节；报告 §7 问题 1–8 全部标已裁定并实现 |
| 2. 相称的实现者测试/编译通过 | 成立。停点全套跑一次：`Ran 1156 tests`、`FAILED (errors=9, skipped=21)`，**本批新增失败 0**；9 个 ERROR 与 `4b60238` 基线逐条同集（系统 `python3` 缺 `cv2`/`numpy`）。Pillow 依赖用例另附实跑记录，不以 skip 充当通过 | `artifact:docs/evidence/P1-ENG-ASSET-001-tests.log`；§6 测试摘要 |
| 3. 已知 Unity 失败已修复并聚焦复测 | 成立（本项零 Unity Play）。唯一一次本批引入的自动测试失败（归档闭包 `zero-match 120`）已按 AC-4 修订 1 迁移闭合，并在保留新落点完整面板、旧落点无 jpg 的真实工作副本中复测 `Ran 1 test … OK`（1.031 s，非 skip）。接受侧回交的两项统计偏差各附一条修复前必失败的具名回归（红 `FAILED (failures=2)` → 绿） | `test:tests.test_dist_data_round4.RealArchiveClosureTest.test_zero_unmatched_and_zero_multi_matched_jpg`；§6；§7 问题 7/8 |
| 4. 复核范围、状态板、候选 commit 与未验证风险已更新 | 成立。复核范围见下；状态板 Active handoffs 与 Gate board 同批更新且 `check_docs.py` 通过；候选已本地提交**并推送**，推送状态由 `git status -sb` 与 `git ls-remote --heads origin main` 运行时核实（不手写 SHA）；未验证项与已知限制见 §6 | `cmd:git status -sb`；`cmd:git ls-remote --heads origin main`；`docs/current-status.md`；§6「未验证项与已知限制」 |

**停点输入并集复核（AC-1；R1@K4 F1 (3) 要求）**：`receipts/input-manifest.json` 的 `union`
累积历次成功执行读过的输入，本次停点共 **289** 条。按当前字节重算：**288 条逐条相等**，
唯一不等的 1 条是 `docs/evidence/P1-ENG-ASSET-001-label-audit.md`——它是本阶段的**合法输出**
（清单被统计正文改写），并集里留的是 stats 读取时的快照，两者本就不该相等；成功收据用
`panel_manifest_read` / `panel_manifest_written` 分列记录。原件类输入（六件 attempt-2 工件、
158 个分片、60 张归档帧、60 张原图副本、指令逐行文件、Unity 代录条目）全部相等。
历史 before/after 一律不回改：`26b0e9c` 对 Unity 日志的代录属**原件的合法来源变化**，
本次重跑 stats 后并集中的日志条目已与当前字节一致（`stages.audit-stats.before` 65 条含日志，
`equal: true`）。

**逐 AC 证据指针**：见 §6 的「AC-1…5 逐条结论」表与各 AC 行的 `test:` / `artifact:` / `cmd:` 指针；
AC-6 及其修订的边界核对（原件零写入、写出闭集、两目录 ≤32 MB、峰值 RSS、零消耗）见 §6。

**给复核角色的范围**：`tools/eng_asset/`（四个模块）、`tests/test_eng_asset_{inventory,label_panel}.py`、
`docs/evidence/P1-ENG-ASSET-001-*`（五件）、`.gitignore` 的单条 outputs 规则；本地派生产物
`runtime/eng-asset/P1-ENG-ASSET-001/`（收据与指令逐行文件）与 `outputs/eng-asset/P1-ENG-ASSET-001/`
（120 个图片文件，git 忽略，需在本机工作副本核对）。**不在范围内**：`tools/dist_data/`、`controller/`、
`config/`、`Assets/`（本项一行未动），以及 `docs/unity-test-log.md`、`docs/implementation-status.md`、
提案与账本（其他角色写入）。

**申请 `UNITY_NA`**：本项纯离线，零 Unity Play、零 scenario/session/run 身份、不改变任何运行时行为；
AC-4 的用户看图是 `OFFLINE_VISUAL_CHECK`，不是 Unity 验证。须复核角色附议后方可成立。

**未闭事项（不随本停点关闭）**：DATA-001 S6 人工审计未执行、框字段仍 `UNVERIFIED`；8 辆无 S5 条目
布局车在冻结归档内不可解；`build_catalog.prospective_mother_eligible` 的裸 `None` 上游缺陷已披露未修；
`COORD-010` 迁移批独立复核与其 `UNITY_NA` 缺口不变。

## 9. `C1@K4` 核对轮回交项的回应（接受角色 2026-09-11）

`C1@K4` 使用了本停点唯一一次 C 退回额度，回交 C1-1…6 与两条随候选带给复核的关注项。
以下逐条回应；**六项均已修复，不改合同、不新增 AC，未重抽样、未覆盖用户已判定的面板**。

| 编号 | 回应 | 修复与证据 |
|---|---|---|
| C1-1 失败前已发布派生工件 | 属实。`stage_plan` 先写清单后核验、`stage_panels` 逐张直接落正式落点、`stage_render_fix` 直接覆盖既有叠加图，失败收据无法让已发布内容消失；`inventory.run` 也在逐个检查目的地后立即 `replace`，且 staging 创建早于路径检查 | 四处生产路径一律改为 **staging → 核验 → 发布**：清单在输入核验通过后才写；面板与原图副本先落 `.staging-panel`、全部输入核验通过后整体发布；重绘先落 `.staging-render`、核验后才覆盖；`inventory.run` 先整体核验全部目的地再逐件发布，路径检查提前到 staging 创建之前，异常路径清理 staging。回归：`test:…LabelPanelTests.test_plan_publishes_manifest_only_after_input_verification`、`test:…LabelPanelTests.test_panels_publish_nothing_when_a_later_source_hash_mismatches`（第 2 张源图声明哈希不符时，第 1 张不得留在正式落点） |
| C1-2 统计未绑定用户所看的样本映射 | 属实。原实现只从清单取种子/配额再重建计划，把连续 index 当 expected；`panel-receipt` 与 render-fix 收据不在 `InputManifest`；清单快照取于重建之后 | 新增 `parse_audit_panels` 解析清单 §3 的冻结身份表，`frozen_identity_mismatches` 逐条比 `panel_index/frame_id/object_id/stratum/surface`；60 张叠加图逐张核验实际字节与清单 `overlay_sha256` 相等；`panel-receipt` 与所采用的 render-fix 收据登记为本阶段输入；清单快照提前到任何解析/重建之前；`expected` 改取冻结清单索引。任一不符只写失败收据。回归：`test:…test_stats_refuses_when_panel_identity_differs_from_manifest`（同数量样本替换）、`test:…test_stats_refuses_when_overlay_bytes_differ_from_manifest` |
| C1-3 缺逐对象逐划分的程序集合 | 属实。`per_object.programs` 只是跨 split 并集 | 摘要新增 `programs_by_split`（train/dev/test/d3/unassigned 逐项），并集保留但不再替代它。回归：`test:tests.test_eng_asset_inventory.InstructionTests.test_per_object_programs_are_split_scoped`（逐 split 与逐行文件复算相等，并要求夹具覆盖同一对象跨 split 的情形）。重跑盘点后**指令逐行文件 SHA-256 逐字节不变**（`06565a95…`），冻结身份与用户判定不受影响 |
| C1-4 唯一颜色错例的来源状态写反 | 属实。#27 是 `Vehicle_Bus_color03`，S5 为 `VERIFIED` + `dual_verified`，报告却写成属 `UNVERIFIED` 集 | §4 第 2 点已改为并列陈述：S5 原状态 `VERIFIED`/`USABLE`，用户本次判颜色=错，**这是对已双验证颜色标记发现的反例**；不回写 S5、不降级、不据一例外推 |
| C1-5 完整候选与停点输入证据缺失 | 属实。统计/自证增量当时未提交；旧 stats 收据绑定的日志字节已非当前日志（辅助角色 `26b0e9c` 代录并修正条目内两处失效文字，属**合法的来源变化**）；重绘实际读取的 60 张原图副本未登记为该阶段输入 | 本批提交完整候选（源码/测试/五份证据/状态板同批）。已重跑统计，`verdict_source` 与 `input-manifest` 的 `audit-stats` 现绑定**当前**日志字节；该阶段不变输入 65 条（指令逐行、S5 目录、Unity 日志、`panel-receipt`、render-fix 收据、60 张叠加图；`R1@K4` F1 返工后重跑）`equal: true`。`stage_render_fix` 现把 60 张原图副本登记为输入。旧收据原字节保留，不回改历史输入值；**合法输出变化**（清单被统计正文改写）与**原件变化**（日志代录）分列记录 |
| C1-6 接口检查把字段合法性写成时序保证 | 属实。`validate_system_monotonic_frame`（`controller/sensor_protocol.py:13-43`）只接收本帧 metadata，校验 schema、`clock_id` 与单值有限非负，无上一帧参数 | §5 条件 3 已按真实代码重写为「单帧时钟字段合法性，非跨帧保证」，并注明需要时序保证属新接口；§5 开头已声明箭头链是只读检查对象/数据流示意，`protocol.latest_frame_bundle()` 不是 `TrackLoop.initialize` 的调用上游。既有缺口照实保留，不新增运行时实现义务 |

**两条关注项**：(a) `inventory.run` 的逐件发布与 staging 次序问题随 C1-1 一并修复（先整体核验全部目的地、路径检查提前）；(b) 叙述核对三处已更正——§1 输入总数 159 → **164**、§8「八条修订」→ **十二条**、§4 与 §6 的历史叙述已与当前状态分列（PENDING 模板与显示确认写为过程记录，Pillow 实跑记录同步为 19 例）。

**运行时解析候选范围的方法**（不手写可派生标识）：本项实现提交可由
`git log --oneline --follow -- tools/eng_asset` 与 `git log --oneline -- tests/test_eng_asset_*.py docs/evidence/P1-ENG-ASSET-001-*` 解析；
开工基线为 `tools/eng_asset/inventory.py` 首次引入提交的父提交。本批提交后工作树为空
（`git status --porcelain` 无输出），不存在未提交的交付物。

## 10. `R1@K4` 独立复核回交项的回应（复核角色 2026-09-11，`REWORK_REQUIRED`）

复核附议了 `UNITY_NA`（仅本 work ID 的 K4 候选），给出 F1–F4 阻断、F5 `SCOPE_GAP`、
F6/F7 逐字补丁与 N1–N5 记录。**F1–F5 全部已修并各附修复前必失败的具名回归，F6/F7 补丁已逐字应用，
N1 建议的夹具覆盖已补**。按 COORD-009，返工直接交 `R2@K4`，不经核对轮。

| 编号 | 回应 | 修复与证据 |
|---|---|---|
| F1（CLASS_2，`BC-1`） | 属实，且是我在修 C1-2 时引入的退化：`stage_stats` 读日志却从未 `manifest.record`，`verdict_source` 在写出后才现算。报告 §9 那句「64 条含 Unity 日志」本身算术就不成立（1+1+1+1+60=64，没有日志的位置），我当时没核对 | 日志在解析前登记为不变输入，`verdict_source` 取登记条目（`path`/`bytes`/`sha256` + 来源注记）。真实重跑：`stages.audit-stats.before` **65** 条且含 `docs/unity-test-log.md`，`equal: true`；并集 289 条复核见 §8。回归 `test:…test_stats_fails_closed_when_verdict_log_changes_midrun`（生产 `stage_stats`，解析后改日志 → `InputHashChanged`、只写 `failure-stats-*`、清单原样），成功用例加断言「日志在 before 中且 `verdict_source.sha256` 等于登记值」 |
| F2（CLASS_2，`BC-4`） | 属实。`(pending)` 与空值被显式放过，还会被写进成功统计版清单充当身份 | 冻结清单任一行 `overlay_sha256` 非 64 位十六进制即 fail-closed（`MANIFEST_OVERLAY_SHA_MISSING_OR_PLACEHOLDER`，记 `panel_index`），不写统计。回归 `test:…test_stats_refuses_placeholder_overlay_identity_in_manifest` 走生产路径制造占位（重跑 `stage_plan` 使清单回到 `(pending)`、叠加图仍在盘上） |
| F3（CLASS_2，`IN_SCOPE_NO_BC`） | 属实。`PanelError` 借用 `OUTPUT_PATH_FORBIDDEN`，`stage_plan` 还按 `reason in FAILURE_REASONS` 无条件写收据，把「先跑 plan 后跑 inventory」的次序错误记成原件保护事件 | `PanelError` 改为继承 `RuntimeError`、**不携带任何闭集 `reason`**；`stage_plan` 的失败收据与 panel/render-fix/stats 同口径按 `isinstance` 过滤。未自行扩大闭集；如需为这类前置失败留收据，按 AC-6 修订 2 路由请接受角色追加 token。回归 `test:…test_plan_failure_does_not_write_closed_set_failure_receipt` |
| F4（CLASS_2，`IN_SCOPE_NO_BC`，`NOT_MECHANIZABLE`） | 属实。候选与用户判定代录均未推送，而 §8 条件 4 写着「已推送」——属驱动操作员动作的失效文字 | 本批已推送候选与返工提交；§8 条件 4 改为不手写 SHA 的可核实表述，证据指针给 `cmd:git status -sb` 与 `cmd:git ls-remote --heads origin main`，由 R2 定点复看 |
| F5（CLASS_2，`SCOPE_GAP`，非阻断） | 属实。`finally` 用未经检查的路径清理，拒绝禁写根后仍会删除该根下的同名目录；发布次序也未先整体检查全部目的地 | 未等裁定即在 A1 内修复（不改合同、不扩范围）：staging 变量只在路径检查通过后绑定，`finally` 只清理**本次实际创建**的那一个；`local` 收据根在任何写入前检查；发布前对 `panel_dir`/`original_dir`/`panel-receipt.json` 全部目的地先整体检查。回归 `test:…test_forbidden_panel_root_is_refused_without_touching_its_contents` 复现探针 (d)。**接受角色仍拥有该项处置权**：若裁定应记账而非修复，本修复可保留、账本另记 |
| F6 / F7（CLASS_3） | 属实 | 两组逐字补丁已全部应用（执行收据五行 + 新增 `stats` 行、两处正文体量口径、Focused 计数、§9 (b) Pillow 15 例、夹具注释、§4 显示确认时态、§8 首段时态） |
| N1（非阻断建议） | 已补 | 夹具新增两帧与一辆已验证蓝车：同类两车异色 → `UNIQUE_CLASS_COLOR`；同类同色两车 + 唯一参照 → `UNIQUE_RELATION`；布局分区加入一辆无 S5 条目的车，使 `fields_document` 真正走 `NO_S5_ENTRY`/`UNUSABLE` 分支并被 AC-2 具名测试断言。夹具现覆盖表 C **全部七值**（复算：`UNIQUE_CLASS` 5、`UNIQUE_CLASS_COLOR` 2、`UNIQUE_RELATION` 2、`COLOR_UNVERIFIED` 1、`AMBIGUOUS_SAME_CLASS` 1、`WILDCARD_UNKNOWN_CLASS` 3、`NOT_CLASS_VERIFIED` 1） |
| N2 夹具来源 | 已改 | `_legal_env` 不再手写 `panel-receipt.json` / `run-render-fix-*.json` / 叠加图字节：改为依次调用生产 `stage_plan` → `stage_panels` → `stage_render_fix` 产出（COORD-007 R3 (1)）。仅绘制与 git 提交门用桩替身，两者各有自己的具名回归 |
| N3 / N4 / N5 | 只作披露，无动作 | 非 `EngAssetError` 异常不写收据但也不发布工件（staging 在 `finally` 清理）；`.DS_Store` 计入体量已写进 §6 体量口径；`.claude/worktrees/` 下两个非本会话副本未触碰 |

**红/绿**：F1/F2/F3/F5 四条具名回归在修复前一次性全失败（`Ran 4 tests … FAILED (failures=4)`），
修复后全绿（`Ran 4 tests … OK`）。F4 不可机检（`NOT_MECHANIZABLE`），由 R2 以 `git ls-remote` 定点复看。
本轮只触及表 A A1/A2：`tools/eng_asset/{label_panel,receipts}.py`、两份 `tests/test_eng_asset_*.py`、
本报告与由工具重写的 A2 文件；**未重抽样、未重绘、未改用户判定与 Unity 日志、未动 `tools/dist_data/`**。

## 11. `R2@K4` 通过轮的 F9 补丁（`PASS_WITH_NOTES`，2026-09-11）

`R2@K4` 核实 F1–F4 的修前红/修后绿、F5 已修、F6/F7 补丁已应用，判 `PASS_WITH_NOTES`
（`passed_candidate` 见复核文件机读行，本文不手写可派生标识），并把 `UNITY_NA` 附议延伸至该候选；
接受角色已消费该轮并关闭本工作项，F5 记「范围内必修·已修」、F8 记入「范围外已知缺陷」账本 `OPEN`。

本次提交按 R2@K4 第 6 节交回动作第 2 条，**只应用 F9 的两处逐字计数补丁**（CLASS_3，
不驱动工具或操作员动作、不开轮、不跑功能测试）：

1. §6 体量口径：两个本地派生目录合计 `10,244,893 B` → `10,249,590 B`，其中
   `runtime/eng-asset/P1-ENG-ASSET-001/` `2,152,022 B` → `2,156,719 B`（F1 返工重跑 stats
   新增一份收据后的当前值）。
2. §9 C1-5 行：「该阶段不变输入 64 条」→「65 条（… ；`R1@K4` F1 返工后重跑）」——
   该句原本与 §10 F1 行自陈的算术不一致，现两处统一为返工后的真实值。

F9 备注（复核明示不要求动作）：§6 收据表的 `stats` 行当前排在 `render-fix` 行之前，
行内数字正确，顺序不影响任何判据，故不调整。R2@K4 的 N6/N7 为披露性记录，无动作要求。

