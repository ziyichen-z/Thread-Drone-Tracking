# P1-ENG-ASSET-001 — 旧资产适配盘点与最小指令集

Status: ACCEPTED（D3 用户范围收敛版，2026-09-08；R2@K4 最终通过轮已消费，工作项 DONE，合同不变）
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（Claude Code `/fable`，Fable 池）
Created: 2026-09-08
Last updated: 2026-09-11

> 承接 `COORD-010` §9「PROPOSED 任务说明 — 旧资产适配盘点与最小指令集」，以新 work ID
> 独立立项。接受角色于 2026-09-08 裁定本项适用 `Workflow: engineering-v1`，
> D3 收敛合同已接受；用户同日逐字“授权”执行，账本「授权收敛合同实现与本地盘点」
> 为执行信封来源。用户判定与统计已取得；R2@K4 通过及 UNITY_NA 附议已消费，收尾与存续债见复判节。
> 当前执行读法：§3 表 A、AC-1…6 连同下方「待裁定」的同编号修订读取；原条款保留历史。
> **D3（2026-09-08，用户范围收敛版）**：D2 第二次 `REVISION_REQUESTED` 后按 workflow §4.2
> 上交用户；用户处置为「保留方向、收敛范围为一个小任务：确认旧资产是否足以支持下一步受限
> 语言选框接入」，逐字见 `docs/authorizations.md`「P1-ENG-ASSET-001 — 用户处置 D2 第二次
> 退修：保留方向、收敛范围」。本稿据此重写 §1–§8；D1/D2 决策记录、接受侧答复与有效试读
> 逐字保留。范围变更与执行授权分条入账；本项盘点与一次 ≤60 张标签抽查已获执行授权。
> 用户同日更早的三项定局中：第 1 项（只盘点 Tier-1 闭集模板）与第 3 项（用户看图 ≤ 60 张）
> 继续有效；第 2 项（允许限次数离线重放）的探针方向已被上述范围收敛 supersede。

## 1. 目的与价值

用户已确认的首版使用过程是「自然语言指定目标 → 定位并交给跟踪器 → 持续跟踪 → 丢失时
显式报告并允许重新指定」（账本 2026-09-07）。本项是其前置的小任务：**确认旧资产是否足以
支持下一步受限语言选框接入**，只回答三个问题（用户 2026-09-08 逐字）：

1. 旧数据里的类别、颜色和框，哪些可用，哪些仍需验证？
2. 沿用既有 Tier-1 模板，可以形成哪些无歧义指令，各有多少样本、分布在哪些既有划分？
3. 后续语言选框模块要接入现有跟踪器，需要满足哪些输入和接口条件？

产出是证据，不是能力：本项不实现语言选框、不训练、不调用任何模型，也不改变既有 SOT、
帧协议或控制命令。接管行为（语言模块输出的框能否播种既有跟踪器、跟多久）**不在本项**，
并入后续语言选框接入任务，届时用语言模块实际输出的框验证。

## 2. 范围与不做的事

**交付闭集（三项）：**

1. **资产与指令盘点报告**（`docs/evidence/P1-ENG-ASSET-001-inventory.md`），附机器可核对
   统计：字段与样本清单（问题 1）、Tier-1 指令候选逐 split 统计与对象重叠（问题 2）、
   接口缺口清单（问题 3）。
2. **一次分层标签抽查**：面板 ≤ 60 张叠加框图，用户看图判定类别、颜色、框的问题；判定
   原文由接受/辅助角色按角色权限代录。
3. **接口缺口清单**：只读代码检查形成，写在报告内，不运行任何跟踪器。

**范围（全部离线、只读原件）：** 读取
`runtime/dist-data/{contract,inventory,layout,frames_catalog,splits,field_catalog}/attempt-2`
及其分片，以及面板所需的归档帧图像；指令形态只取 Tier-1 闭集模板（`tools/dist_data/tier1_lang`
的 ontology/v1：9 个车辆类词、颜色词只取 S5 已验证闭包、4 种静态关系，表面形即其 renderer
的英文）；只按 S4 既有 train/dev/test 划分统计。

**移出当前范围（用户 2026-09-08 决定）：**

- 删除真实 NanoTrack 离线播种与重放实验：跟踪时长、IoU 跌落、模型调用预算、探针工具及其
  测试；并入后续语言选框接入任务，届时使用语言模块实际输出的框验证接管行为。
- 不另做独立的固定评估集交付；本项只统计既有 train/dev/test 的可用样本及对象重叠，正式
  评估集由后续任务确定。

**不做的事（闭集）：**

- 不采集新数据、不开 Unity、不创建 scenario/session/run/attempt 身份、不动用 DATA-002
  剩余额度；不写 `runtime/dist-data` 的任何 attempt，不覆盖或修订 S5 字段。
- 不重新划分、不退役旧 benchmark、不让旧 test 回流训练；不为本项定义合格线或 floor。
- 不调用 VLM/LLM/YOLOE/DINOv2/NanoTrack，不做微调、量化、Jetson 探测；不定义中文指令表面形；
  不为被删除的探针条款增加任何替代实验。
- 不改 `controller/`、`Assets/`、`config/`、`tools/dist_data/`、帧/控制协议或安全约束；缺口
  清单发现的接口改动留给后续接入提案在其 K1/K3 停点处理。
- 不发布、不下载、不改变任何旧工作项的门、verdict 或冻结主张。

## 3. 接口与数据契约

**复用的既有契约（不改）：**

- 框协议：归一化 top-left `xywh`，裁剪到 `[0,1]`（设计 §6；`controller/trackers.py`
  `clip_box_norm`）。目录侧 `frame_id` = inventory 全局路径（DATA-001 BC-DATA-3 语义），
  运行时归档侧 `frame_id` = 整数；派生工件同时记录两者与文件 SHA-256。
- **执行域与最小程序逐字复用既有函数**：执行域 =
  `tools/dist_data/build_catalog.frame_world(entry, field_catalog)`，调用形态与
  `tools/dist_data/run_pipeline.py` 的 S7 相同——不传 `world_xz` / `route_side`，因此
  `nearest_to` 与 `on_route_side` 按既有实现恒为 `relation_available=False`，只有
  `viewer_left_of` / `viewer_right_of` 可判；`field_catalog` = S5 attempt-2 原样，不调用
  `apply_audit_downgrades`（S6 审计从未执行，本项不伪造降级集）。最小程序 =
  `build_catalog.minimal_program_with_reference(world, object_id, field_catalog)`，其确定性
  顺序（class-only → class+已验证 color → `contract.RELATION_TYPES` × 唯一 ref 枚举序）
  原样沿用；本项不自写冲突判定。幻影按 `frame_world` 既有语义：类别已知、颜色通配，
  不阻断不同已知类别；动态目标是否入域以本帧 `blocking` 与 `target_source_bound` 为准
  （`contract.dynamic_target_fields`）。
- 只读检查的接入链路（问题 3 的对象，不运行）：`runtime/frames/latest.json` →
  `controller/protocol.py` `latest_frame_bundle()` → `controller/track_loop.py`
  `TrackLoop.initialize(frame_id, box_norm)` → `controller/trackers.py` `TrackerPlugin.init/update`
  → `controller/tracking_entry.py` `observation()` 写 `runtime/tracking_observation.json`；
  `TrackerResult(box_norm, ok, confidence, confidence_source)`；NanoTrack-v2 的
  `getTrackingScore()` 只是未校准诊断分（设计 §3.4）。

**表 A 写入分层（AR2-1；三类互斥，路径闭集）**

| 类别 | 路径闭集 | 谁写 | 说明 |
|---|---|---|---|
| A1 实现者可修改的源码/测试路径 | `tools/eng_asset/__init__.py`、`tools/eng_asset/inventory.py`（对账、字段清单、指令候选、划分统计）、`tools/eng_asset/label_panel.py`（分层、面板、收据、统计）、`tools/eng_asset/receipts.py`（输入清单与收据）；`tests/test_eng_asset_inventory.py`、`tests/test_eng_asset_label_panel.py`；`tests/fixtures/eng_asset/`（夹具由生产路径产出）；`docs/evidence/P1-ENG-ASSET-001-inventory.md`（报告正文由实现者写，统计块由工具生成后粘入并注明来源收据）；提案「待裁定」节；`docs/current-status.md`（按角色权限） | 实现角色 | 受版本控制；本项实现者变更只限本行与 A2；停点检查口径见 AC-6 |
| A2 工具运行时可生成的文件 | 受版本控制：`docs/evidence/P1-ENG-ASSET-001-fields.json`、`docs/evidence/P1-ENG-ASSET-001-instructions-summary.json`、`docs/evidence/P1-ENG-ASSET-001-label-audit.md`（面板清单、分层分母、统计；不含判定原文）、`docs/evidence/P1-ENG-ASSET-001-tests.log`。本地（git 忽略）：`runtime/eng-asset/P1-ENG-ASSET-001/instructions.ndjson.gz`、`panel/*.jpg`、`panel-receipt.json`、`receipts/input-manifest.json`、`receipts/run-<stage>-<utc>.json`（成功收据）、`receipts/failure-<stage>-<utc>.json`（失败收据：只记原因与不符条目，不产出派生工件） | 工具（实现角色运行） | 每个受版本控制文件 ≤ 2 MB；本地目录合计 ≤ 32 MB；行数、字节、SHA-256 记入对应摘要 |
| A3 其他角色按权限写入 | `docs/unity-test-log.md` 条目 `UT-P1-ENG-ASSET-001-label-audit`（接受/辅助角色代录用户判定原文，`OFFLINE_VISUAL_CHECK`，零 Play）；`docs/reviews/P1-ENG-ASSET-001.md`（复核角色）；`docs/implementation-status.md` 与提案决策/核对表（接受角色） | 对应角色 | 实现角色对这些文件只读 |

**禁写闭集（原件保护）：** `runtime/frames*`、`runtime/*_command.json`、
`runtime/tracking_observation.json`、`runtime/metrics.json`、`runtime/runs`、
`runtime/dist-data`、`runtime/test-results`、`runtime/rate-study`、`runtime/p1-detect-scouting`、
`runtime/m3_body_truth*`、`config/`、`Assets/`、`controller/`、`tools/dist_data/`。工具对
输出路径做包含检查，落入上述任一根即拒绝运行并写失败收据。

**表 B 派生工件字段（schema 字符串以 `p1-eng-asset-001/<name>/v1` 命名，每件记录来源
工件 SHA-256）**

| 工件 | 必含字段 |
|---|---|
| `fields.json` | 按（布局类, 采集族, split∪`unassigned`, usage_class）的帧数/含可指称车帧数/(帧,车)对数；按 101 辆布局车的 class、`color_status`、`color_downgrade_reason`、各 split OK 帧数、最佳短边、S5 有无条目；字段三分类 `USABLE` / `UNVERIFIED` / `UNUSABLE` + 来源指针（S5 记录、DATA-002 颜色诊断、继承清单行） |
| `instructions.ndjson.gz`（逐行） | `frame_id, object_id, split（S4 四值或 unassigned）, family, layout_class, usage_class, mother_usage（布尔值：usage_class ∈ contract.MOTHER_USAGE_CLASSES）, target_unbounded, program（无程序时 null）, surface（无程序时 null）, resolved_reference_object_id（无关系时 null）, uniqueness_status（表 C 七值之一）, visible_norm_xywh, short_side_px, prospective_mother_eligible` |
| `instructions-summary.json` | 逐 split × `mother_usage` 的七值直方图；逐 split 去重 (对象, 程序) 与去重对象；逐对象在 train/dev/test/unassigned 的 `UNIQUE_*` 行数与程序集合；对象重叠表（train∩test、dev∩test、test 独有，含 `held_out_object_ids` 标记）；`prospective_mother_eligible` 在 S4 已划分帧上的候选数及与 27,074 的差异说明；`frozen_evaluation_set: false` |
| `label-audit.md` | 种子、各层定义与配额、分母、实取数；逐张 `panel_index, frame_id, object_id, stratum, surface, overlay_sha256`；`panel-receipt.json` 的 SHA；判定统计（由工具只读 Unity 日志条目计算）与该条目指针；不复制判定原文 |
| `panel-receipt.json` | 运行时解析的配额文件提交 SHA（`git log -1 --format=%H -- <label-audit.md>`）与其 `git status --porcelain` 为空的断言、输入清单 SHA、生成时间 |
| `receipts/input-manifest.json` | 每个被读文件的路径、字节、SHA-256、来源（S3/S4 manifest 引用 / S1 `records[].sha256` / 首次读取现算）；一个文件内按执行阶段保存 before/after 清单并逐条比较，成功收据绑定本次清单；停点复核此前成功执行所读输入的并集 |
| `receipts/run-*.json` / `failure-*.json` | 成功：耗时、峰值 RSS、输出文件行数/字节/SHA-256；失败：阶段、原因闭集 {`MANIFEST_COUNT_MISMATCH`, `SHARD_HASH_MISMATCH`, `INPUT_HASH_CHANGED`, `OUTPUT_PATH_FORBIDDEN`, `QUOTA_FILE_DIRTY`}、不符条目 |

**表 C `uniqueness_status` 七值（互斥，按优先序判定；全部由既有函数的返回派生）**

| 序 | 值 | 判定 |
|---|---|---|
| 1 | `NOT_CLASS_VERIFIED` | S5 无该对象记录或 `class_verified` 为假（`minimal_program_with_reference` 入口即返回 None） |
| 2 | `UNIQUE_CLASS` | program 非 null，无顶层 `relation`，且 `program["target"]` 无 `color` |
| 3 | `UNIQUE_CLASS_COLOR` | program 非 null，无顶层 `relation`，且 `program["target"]` 有 `color` |
| 4 | `UNIQUE_RELATION` | 返回程序有 `relation`（target 带不带 color 均入此值） |
| 5 | `WILDCARD_UNKNOWN_CLASS` | 返回 None，且 class-only 名词的冲突集（`tier1_lang._noun_conflicts`）含 ≥ 1 个 `class_word is None` 的对象（未绑定动态目标） |
| 6 | `COLOR_UNVERIFIED` | 返回 None，target 自身 `color_status != VERIFIED`，且 class-only 冲突集 ≥ 2 |
| 7 | `AMBIGUOUS_SAME_CLASS` | 返回 None 的其余情形（颜色已验证仍冲突，且无可用关系程序） |

**红线（继承，不因工程轨道放宽）：** Unity 真值只进 `CoverageEvaluator`。本项不运行任何
跟踪器；S3 投影框只作字段清单与看图面板对象。`tools/eng_asset/` 不 import
`controller.track_loop` / `controller.run_log` / `controller.trackers`。

## 4. 验收项（AC 表）

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | 对账与输入清单：工具只读六件 attempt-2 工件，逐件核对 manifest 计数（S3 43,535 帧、S4 2,523/13,144/8,450/0、S5 690 对象/93 车辆/37 双验证）与 151+7 个分片 SHA-256；任一不符即 fail-closed：只写 `receipts/failure-*.json`，零派生工件。每次执行生成 `receipts/input-manifest.json`（本次实际读取的每个文件的字节与 SHA-256：分片对 S3/S4 manifest；图像对 S1 `records[].sha256`；sidecar 首次读取现算），执行结束与停点自证时重算并逐条相等 | `test:tests.test_eng_asset_inventory.ReconciliationTests.test_shard_hash_mismatch_writes_failure_receipt_only`；`test:tests.test_eng_asset_inventory.ReconciliationTests.test_input_manifest_reverified_after_run`；`artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §1 | K4 | 2026-09-08 |
| AC-2 | 问题 1——字段与样本清单按 §3 表 B 生成；101 辆布局车逐辆有行（S5 无条目的 8 辆标 `NO_S5_ENTRY`、`UNUSABLE`）；对账域 = S3 中 `layout_binding_valid ∧ sidecar_complete` 的行，逐 split（含 `unassigned`）的「车辆 OK 计数」= 各行 `referable` 长度之和，与指令逐行文件的行数相等；每个 `UNVERIFIED`/`UNUSABLE` 字段附原证据指针；报告 §2 以「可用 / 仍需验证 / 不可用」三栏回答问题 1 | `test:tests.test_eng_asset_inventory.FieldTableTests.test_object_table_sums_match_s3_referable_counts`；`artifact:docs/evidence/P1-ENG-ASSET-001-fields.json` | K4 | 2026-09-08 |
| AC-3 | 问题 2——指令候选：对对账域内每个 (帧, `referable` 对象) 用 §3 指定的 `frame_world(entry, field_catalog)` 与 `minimal_program_with_reference` 求程序，`uniqueness_status` 按表 C 七值互斥判定，无程序时 `program`/`surface`/`resolved_reference_object_id` 为 null；摘要给出逐 split × `mother_usage` 七值直方图、去重 (对象, 程序) 与去重对象、逐对象在各 split 的 `UNIQUE_*` 行数与程序集合、对象重叠表（含 `held_out_object_ids`）；另按 `prospective_mother_eligible` 在 S4 已划分帧上复算候选数，与 DATA-002 上界报告的 27,074 对照并写明差异来源；不调用 S7 门、不物化 S8、不写 `mother_candidates`、不冻结任何评估集 | `test:tests.test_eng_asset_inventory.InstructionTests.test_status_derivation_matches_minimal_program_on_production_slice`；`test:tests.test_eng_asset_inventory.InstructionTests.test_unbound_dynamic_target_yields_wildcard_unknown_class`；`test:tests.test_eng_asset_inventory.InstructionTests.test_phantom_of_other_class_does_not_block`；`test:tests.test_eng_asset_inventory.InstructionTests.test_overlap_table_matches_per_object_rows`；`artifact:docs/evidence/P1-ENG-ASSET-001-instructions-summary.json` | K4 | 2026-09-08 |
| AC-4 | 分层标签抽查：抽样单位 = 指令逐行文件的一行 (帧, 对象)，域 = 对账域全部行；四层按优先序归层、每行只属第一个命中层：S1 `color_status != VERIFIED`；S2 `uniqueness_status ∈ {AMBIGUOUS_SAME_CLASS, WILDCARD_UNKNOWN_CLASS, UNIQUE_CLASS_COLOR, UNIQUE_RELATION}`；S3 `short_side_px < 32`；S4 `uniqueness_status = UNIQUE_CLASS ∧ short_side_px ≥ 64`；配额 20/15/15/10；层内按 SHA-256(seed‖frame_id‖object_id) 升序取样，每对象每层 ≤ 2 行，层不足额时留空不回填，唯一图片总数 ≤ 60，各层分母与实取数写入 `label-audit.md`。种子与配额写入该文件并提交后，生成器运行时解析其 `git status --porcelain`（须为空）与 `git log -1 --format=%H`，写入 `panel-receipt.json`，不满足即写失败收据 `QUOTA_FILE_DIRTY`；面板每张只画该行的框与 surface，原图另存副本。用户逐张对类别、颜色、框紧致度各给 对/错/不确定，错误类型按闭集 {类别错, 颜色错, 框不紧或截断, 遮挡误判, 车辆缺失或幻影} 多选；判定原文只由接受/辅助角色代录进 `docs/unity-test-log.md` 条目 `UT-P1-ENG-ASSET-001-label-audit`（`OFFLINE_VISUAL_CHECK`，零 Play），统计工具只读该条目出逐层计数，「不确定」单独计数、不计为对，空层不计为通过 | `test:tests.test_eng_asset_label_panel.LabelPanelTests.test_stratum_priority_quota_and_per_object_cap`；`test:tests.test_eng_asset_label_panel.LabelPanelTests.test_panel_generation_refuses_uncommitted_quota_file`；`test:tests.test_eng_asset_label_panel.LabelPanelTests.test_statistics_read_only_from_unity_log_entry`；`cmd:git status --porcelain -- docs/evidence/P1-ENG-ASSET-001-label-audit.md`（生成面板时须为空）；`artifact:docs/evidence/P1-ENG-ASSET-001-label-audit.md` | K4 | 2026-09-08 |
| AC-5 | 问题 3——接口缺口清单（只读代码检查，不运行跟踪器）：报告 §5 以 `file:line` 指针列出 §3 接入链路对语言选框模块的**输入条件**（帧 id 绑定到已完整发布的 bundle、归一化裁剪框、`track_id`、置信度来源语义、`expires_after_s` 过期、初始化只允许一次等）与**缺口** G-n，至少覆盖：候选框→人工确认→初始化入口、迟到结果拒收、帧 id 绑定与过期、丢失显式报告通道、`track_id`/置信度来源、重新指定入口、`nearest_to`/`on_route_side` 在 S7 调用形态下不可用；每条标注归属后续接入任务的 K1/K2/K3 哪一停点；接管行为验证明确写为后续任务范围 | `artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §5 | K4 | 2026-09-08 |
| AC-6 | 原件零写入与交付：每次执行前后 `receipts/input-manifest.json` 逐条相等（AC-1）；停点候选相对开工基线的本项实现 diff（含已提交改动）只含表 A 的 A1/A2；同时记录 `git status --porcelain` 检查未提交差异，A3 的其他角色文档单列、不得冒充实现者写入；本地目录 `runtime/eng-asset/P1-ENG-ASSET-001/` 合计 ≤ 32 MB；工具不 import `controller.track_loop` / `controller.run_log` / `controller.trackers`；报告含 AC-1…5 逐条结论、对三个问题的直接回答、执行收据（耗时、峰值 RSS ≤ 1 GB）与全套测试摘要（基线已有失败与本批新增失败分开） | `test:tests.test_eng_asset_inventory.WriteBoundaryTests.test_output_inside_input_roots_is_refused`；`test:tests.test_eng_asset_inventory.WriteBoundaryTests.test_no_controller_runtime_imports`；`cmd:python3 -m unittest discover -s tests > docs/evidence/P1-ENG-ASSET-001-tests.log 2>&1; tail -n 3 docs/evidence/P1-ENG-ASSET-001-tests.log`；`artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §6 | K4 | 2026-09-08 |

AC 编号一经接受即稳定；实现期合同问题写「待裁定」节，答复只追加（`AC-n 修订 <m>` 或新 AC）。
D2 → D3 编号映射见「决策记录」D3 条。

**首次接受时的合同释义（并入上述 AC，不新增交付或实验）：**
- AC-1/6：输入清单的 before/after 保存在表 A 已准许的同一文件内；失败只发布失败收据，
  不发布该次成功工件。工件里的图像 SHA 可取已核验 S1 引用，面板实际读图时核验其字节；
  无需为每条指令重新读像素。源码修改与原件保护分别按 A1/A2 与 AC-1 核对。
- AC-3：先按表 C 第 1 行处理缺记录/类别未验证；其余解包既有函数的 `(program, ref)`。
  “返回 None”指无 program；颜色读 `program["target"]`，关系读顶层 `relation`。
  `prospective_mother_eligible` 输出为既有同名函数返回非 None 的布尔值。
  对象重叠表的域为各 split 的 `UNIQUE_*` 目标行；S4 `held_out_objects.held_out_object_ids`
  标记原样继承，两者不得混称“对象从未出现在训练图像中”，也不宣称已建立正式评估集。
- AC-4：无唯一程序时 surface 仍为 null；用户看图时配合该对象的 S5 类别/颜色/验证状态
  （引用 fields 清单）判定，不把 null 编造为指令。未验证或无颜色记录可判不确定；
  该抽查不回写 S5，也不据抽查结果重算原样 S5 下的指令候选。
- AC-5/6：链路是只读检查对象清单，不预断言各函数互相调用；输入条件按真实代码标出
  所属层及缺口。五分钟为规划估计，不是性能验收线；实现 focused、停点全套与复核验证
  只用无模型夹具，本项不调用真实模型；报告如实注明因此未重跑的既有模型集成测试。


## 5. 预算信封

信封来源：`docs/authorizations.md` 2026-09-08「P1-ENG-ASSET-001 — 授权收敛合同实现与本地盘点」，用户逐字“授权”；下表原申请值已获批准，缺项视为 0。

| 项目 | 上限（已授权） |
|---|---|
| Consuming | no |
| scenario/session/run ID | 0 |
| Unity Play | 否（0 次；纯离线） |
| 模型 API 次数 | 0 |
| 训练 GPU·h | 0 |
| 模型推理（含本地 NanoTrack/YOLOE/VLM） | 0（本项不运行任何模型） |
| 下载/发布 | 否 |
| 用户看图 | 一次 ≤ 60 张叠加图（AC-4） |
| 派生工件写出 | 仅 §3 表 A 的 A2；受版本控制文件各 ≤ 2 MB，本地目录 ≤ 32 MB |
| 用户决策点 | ≤ 2（接受与授权入账；看图判定） |

资源估算依据 §8：S3 全量流式扫描 59.7 s / 峰值 RSS 51.6 MB；S1 路径→SHA 索引 0.3 s /
峰值 RSS 361 MB；面板读取 ≤ 60 张图像，哈希按实测 ≈ 150 MB/s 可忽略；指令逐行文件约
27.6 MB 未压缩（gzip 估 ≤ 5 MB）。全部为本地桌面 CPU，单次执行预计 ≤ 5 min，无 GPU。

## 6. 限制与不承诺

- 本项产出**只支持事实陈述**：不声称语言选框、跟踪性能、恢复能力或任何研究主张；不定义
  新指标（继承清单：旧 `C_geom`/`C_track` 只用于原定义覆盖的部分）。
- 「接管行为」（语言模块输出的框能否播种既有跟踪器、跟多久）不在本项，由后续语言选框接入
  任务用语言模块实际输出的框验证；本项报告只写接入的输入条件与缺口。
- §8 表 2/表 6 的试读数字是**规划估计**（作者近似规则），不是 `minimal_program_with_reference`
  的输出；AC-3 用既有函数重算。既有 S7 调用形态下 `nearest_to`/`on_route_side` 不可用，
  本项不补 `world_xz`/`route_side`，只如实报告。
- 颜色字段现状：93 辆 S5 目录车 37 辆 `VERIFIED`、37 辆 `GROUP_INCONSISTENT`、19 辆无主色；
  已验证词表只有 {blue, gray, green, purple, red, yellow}。本项**不改**颜色估计器与冻结常量；
  颜色未验证对象按既有函数只能得到 class-only 或无色关系程序。
- 8 辆布局车在 S5 无条目（从未以 `OK` 出现于任何 BOUND 帧），只能列为 `UNUSABLE`。
  2 个布局类（`default` 12 族、`scene-004` 3 族）继承各自的 6 条 relocation/removal，盘点
  按布局类分列，不合并。
- 对象重叠统计只描述既有划分，不构成评估集；正式评估集由后续任务确定。
- DATA-002 来源缺口（采集前工作树、逐会话 Console、Unity 版本/场景确认）继续如实记载；
  本项不补证、不修复，也不把它转为 SCOPE_GAP。
- 抽查 n ≤ 60、描述性，不构成审计通过或 F1–F4 结论；DATA-001 S6 人工审计仍未完成。
- `IMPLEMENTED` ≠ `DONE`：本项 `DONE` 需实现证据 + `R<n>@K4` 通过 + `UNITY_NA` 经复核
  附议；`CLOSED_*` 不冒充通过。
- 范围决定本身不授予执行额度；执行依据是账本同日独立的“授权收敛合同实现与本地盘点”
  条目。用户判定已代录，仍不得以授权或描述性抽查代替独立复核。

## 7. 必经停点

- **唯一必经停点：`K4`**（数据划分、标签或对外指标）——本项派生指令标签与分层抽查判定
  属该类；AC-1…AC-6 合并为**一个候选**走 `C1@K4` → `R1@K4`。
- 不触发 `K1`（不改帧/控制协议与坐标时间语义）、`K2`（不发控制命令、不改安全约束）、
  `K3`（不运行、不改运行时模型决策/身份/重播种）、`K5`（不发布）。缺口清单发现的接口改动
  由后续接入提案在其 K1/K3 停点处理，本项不动代码。
- 停点自证按 workflow §4.3.1 四项条件，证据指针按 AC 编号逐条附上；核对轮不跑测试；
  复核 `REWORK_REQUIRED` 直接回复核。Unity 列申请 `UNITY_NA`（纯离线、零运行时行为），
  须复核角色在 `docs/reviews/P1-ENG-ASSET-001.md` 附议。

## 8. 只读试读与试运行数字

2026-09-08 构思侧只读试跑（零写入、零 ID、零模型；脚本留在会话 scratchpad 不入库；
未经复核，只作规划）。读法：标准库 JSON 流式解析 S3 151 个分片 + S4 `frames` 集合 +
S5 `objects`，按本文作者的近似规则计数。D2 §8 表 5（探针种子绑定核对）随探针范围移除，
其数字保留在 D2 版提案的 git 历史中供后续接入任务参考，不再是本合同的依据。

**表 1 工件尺度与执行收据**

| 量 | 本次读数 |
|---|---|
| S3 `frames_catalog@attempt-2` | 43,535 帧 / 151 分片（约 1.56 GiB 压缩）；manifest 63,141 B；`skipped_invalid_frames` 19、`skipped_unbound_frames` 157 |
| S4 `splits@attempt-2` | train 2,523 / dev 13,144 / test 8,450 / d3 0；未入划分 19,418；atoms 4 |
| S5 `field_catalog@attempt-2` | 690 对象；`Vehicle_*` 93（class 93/93 验证；颜色 37 VERIFIED / 37 GROUP_INCONSISTENT / 19 无主色）；101 辆布局车中 8 辆无 S5 条目 |
| S1 图像 | INCLUDED 43,711 张，全部 640×480 JPEG，合计 1,993,706,652 B；`records[].sha256` 覆盖全部 50,115 条（含 5,769 条真值文件）；帧 sidecar `.json` 不在 S1 索引内 |
| 一次 S3 全量流式扫描 | 59.7 s，峰值 RSS 51.6 MB（不读像素） |
| S1 路径→SHA 索引 | 加载 + 建索引 0.3 s，峰值 RSS 361 MB |
| SHA-256 吞吐 | 200 个归档文件 4.5 MB 用 0.03 s ≈ 150 MB/s |
| 布局绑定 | 17 partition / 16 BOUND；`default` 12 族、`scene-004` 3 族；a1-s1 INVALID 已被 S3 排除 |

**表 2 指令候选估计（近似规则：class-only 唯一 → class+已验证 color 唯一；未验证颜色、
未绑定动态目标通配阻断；不算静态关系。规划标签，不是 AC-3 合同的证据）**

| split | 帧 | 含可指称车帧 | (帧,车) 对 | 类别唯一 | 类别+颜色唯一 | 同类歧义（颜色已验证仍冲突） | 颜色未验证 | 通配阻断 | 含 ≥1 指令帧 | 去重 (对象,程序) | 去重对象 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| train | 2,523 | 1,633 | 3,305 | 582 | 22 | 917 | 274 | 1,510 | 459 | 16 | 16 |
| dev | 13,144 | 10,023 | 20,617 | 14,644 | 460 | 938 | 4,516 | 59 | 9,046 | 36 | 32 |
| test | 8,450 | 5,986 | 11,231 | 6,377 | 995 | 1,032 | 1,572 | 1,255 | 4,947 | 50 | 45 |
| 未入划分 | 19,418 | 13,710 | 22,277 | 16,775 | 1,576 | 1,232 | 1,659 | 1,035 | 12,774 | 59 | 52 |

- train/dev/test 合计有 ≥ 1 指令的目录车 **75 / 93**；train∩test 12 辆、dev∩test 6 辆、
  test 独有 29 辆。test 的 45 辆按类：suv 10、taxi 9、pickup truck 8、container truck 5、
  bus 4、truck 4、ambulance 2、police car 2、car 1。
- 域差异：本表全帧域的类别/颜色唯一对合计 41,431，大于 DATA-002 上界报告在 S7 语义下的
  冻结候选外延 27,074（该外延另加 `MOTHER_USAGE_CLASSES`/非 `TARGET_UNBOUNDED` 等条件）；
  两者不可互换，AC-3 按 `prospective_mother_eligible` 复算对照。
- train 是单一巡览会话 `p1-vlm-survey-a2-p1-c1-s1`：3,305 对里 1,859 对有 2 辆同类车同框，
  1,510 对因动态目标未绑定被通配阻断——颜色与关系程序对 train 影响最大。

**表 3 可指称目录车的可见框短边（px）**

| split | n | p10 | p50 | p90 | < 24 px | < 12 px |
|---|---|---|---|---|---|---|
| train | 3,305 | 28.3 | 55.2 | 120.5 | 144 | 0 |
| dev | 20,617 | 31.5 | 55.3 | 95.6 | 1,586 | 0 |
| test | 11,231 | 32.6 | 69.7 | 118.8 | 442 | 0 |

**表 4 动目标（冻结红色 `car`，`target_source_bound` 且可见；只作字段清单）**

| split | 可见帧 | 短边 < 24 px |
|---|---|---|
| train | 1,247 | 79 |
| dev | 4,274 | 612 |
| test | 4,843 | 242 |
| 未入划分 | 5,599 | 193 |

**表 6 派生工件行字节与体积投影（真实样本内存序列化，紧凑 JSON 一行一记录）**

| 工件 | 样本 | 单行字节 | 行数投影 | 体积投影 | 落点 |
|---|---|---|---|---|---|
| 指令逐行 | 400 行真实 S3 (帧,车) 对 | 均值 481、最大 499 | 57,430（对账域全部对） | ≈ 27.6 MB 未压缩，gzip 估 ≤ 5 MB | 本地 `.ndjson.gz` + 摘要 |
| 面板 | — | — | ≤ 60 张 | ≤ 60 × 60 KB ≈ 3.6 MB | 本地 `panel/` |
| 摘要与报告 | — | — | — | 各 ≤ 2 MB | `docs/evidence/` |

驻留：逐行流可流式写出，峰值以 S1 索引 361 MB 为主，规划上限 1 GB（AC-6）。

**表 7 抽查分层分母（近似规则，逐行归第一命中层；AC-4 的正式分层统计以工具输出为准）**

| 层 | 定义 | 行数 | 去重对象 | train / dev / test / 未入划分 |
|---|---|---|---|---|
| S1 | 颜色未验证 | 26,027 | 56 | 1,779 / 12,187 / 4,660 / 7,401 |
| S2 | 同类 ≥ 2 车同框（颜色已验证） | 8,498 | 36 | 1,298 / 1,412 / 2,486 / 3,302 |
| S3 | 短边 < 32 px | 467 | 23 | 31 / 125 / 60 / 251 |
| S4 | 类别唯一且短边 ≥ 64 px（对照） | 15,973 | 27 | 194 / 3,891 / 3,262 / 8,626 |
| 不入层 | 其余 | 6,465 | 31 | 3 / 3,002 / 763 / 2,697 |

配额 20/15/15/10 在四层均可足额；每对象每层 ≤ 2 行的上限下 S3 层（23 个对象）仍可足额。

## Pending rulings（待裁定）

1. **动目标段的初始化框来源**：M3′ post-run 归档帧段与 run 日志追踪框帧段不重叠，没有
   运行时产生的框可用；本文建议 AC-6 动目标段以首归档帧的 evaluator 真值框作离线替身
   （逐段标 `evaluator_truth_offline_standin`，探针不 import 运行时模块、不写桥文件）。
   若接受角色裁定不允许真值进入任何 tracker 输入（含离线探针），AC-6 改为只做 ≤ 28 段
   静止目录车段，动目标段记 `NOT_PROBED_TRUTH_ISOLATION`。
2. **AC-4 用户判定原文的代录落点**：本文建议沿用 COORD-005 人眼保真检查先例，由接受/
   辅助角色代录进 `docs/unity-test-log.md`（条目名 `UT-P1-ENG-ASSET-001-label-audit`，
   状态 `OFFLINE_VISUAL_CHECK`，不是 Unity Play），证据文件只引用不复制；若接受角色另定
   落点，AC-4 证据指针按其裁定改写。

**接受侧答复（2026-09-08，D1；本提案尚未接受）：**

1. 不批准 `evaluator_truth_offline_standin` 作为 tracker 初始化输入。正式设计 §6、
   `docs/engineering-workflow.md` §0 和状态板 Active constraints 的真值隔离规则没有
   “离线 tracker”例外；不 import `track_loop`、不写桥文件和限制主张不能解除输入禁令。
   同理，S3 的 Unity 几何投影监督框也不能仅通过改名为 `s3_projection` 获得 tracker
   输入资格，原建议的“只剩静止段”不是完整修复。按 AR1-1 重写，不在本轮扩大红线例外。
2. 同意原文代录落在 `docs/unity-test-log.md` 的本 work ID 离线标签抽查条目，标
   `OFFLINE_VISUAL_CHECK`，明确零 Play、不是 Unity 验证通过；实现者的 label-audit
   文件只存面板、统计和该条目指针，不复制用户判定原文。这是本轮对待裁定问题的答复，
   不声称已收到判定，也不代替本项最终 `UNITY_NA` 的独立复核附议。按 AR1-5 同步正文。

**D2 落实（构思侧，2026-09-08）**：答复 1 → §2/§3 表 A/AC-6 已删除真值与投影框种子，
种子闭集只含人工参考框与 run 日志感知框，不可探段记 `NOT_PROBED_TRUTH_ISOLATION`；
答复 2 → §3 表 B 与 AC-4 已把判定原文落点改为 Unity 日志条目，说明文件不复制原文。
D2 无新增待裁定。

**D3 说明（构思侧，2026-09-08）**：待裁定 1 随探针范围移除而失效（本项不运行任何跟踪器）；
待裁定 2 的答复继续有效，落点见 §3 表 A 的 A3。D3 无新增待裁定；范围变更本身待接受角色
逐字记录并裁定。

**实现期问题转录及接受侧答复（2026-09-08；来源：盘点报告 §7，非新 D/C/R 轮）：**

本会话 owner = acceptance；范围仅三项合同问题及共享文档同步。以下问题由接受侧
按报告转录（概述，非用户授权原话），没有把报告中的建议当成复核 verdict。

1. **面板落点冲突。** 报告 §7 问题 1：A2 的 `runtime/eng-asset/P1-ENG-ASSET-001/panel/`
   中 60 张叠加图与 60 张原图副本触发 DATA-001 附录 A 零匹配失败；实现者不能自行改
   A2 或 `tools/dist_data/`。**裁定：接受方案 (b)，仅将面板移到仓库内
   `outputs/eng-asset/P1-ENG-ASSET-001/panel/`。** DATA-001 附录 A、
   `tools/dist_data/roots.py` 的枚举/排除规则及原件不改；不接受带本批新增失败进入停点。
   路径修订与迁移合同见 AC-4/6 修订 1；本次只定合同，不代实现角色搬图或修工具。
2. **提案写权限冲突。** 报告 §7 问题 2：A1 允许写提案「待裁定」，但角色检查器
   拒绝 implementation 写 `docs/proposals/*`。**裁定：本项由实现者写报告 §7，
   接受角色转录到本节并答复**（AC-6 修订 2）。问题已通过该通道接收，不要求实现者
   绕过机检；不修改角色细则、检查器或其他工作流基础设施。
3. **上游裸 None 解包。** 报告 §7 问题 3/§6 限制 2：S5 缺条目或类别未验证时，
   `minimal_program_with_reference` 返回裸 `None`，而 `prospective_mother_eligible`
   解包返回值会报错；报告称真实 attempt-2 不触发。只读源码支持该分支说明，
   本次未重跑夹具或真实数据。**裁定：按 AC-3 首次接受释义先处理
   `NOT_CLASS_VERIFIED`，该行母集资格为 false，其他行继续调用既有函数；
   不改上游实现。** 具体见 AC-3 修订 1。披露进入工程继承清单，供后续使用者核对；
   当前没有复核 finding 或冻结集裁定，不擅自填 SCOPE_GAP 账本、不签 release。

以下为工程轨道的追加修订，引用并限定既有 AC；不是重写原验收项或新增实验。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-4 修订 1 | 解释 AC-4 与 §3 表 A A2：面板唯一落点改为 `outputs/eng-asset/P1-ENG-ASSET-001/panel/*.jpg`（叠加图及同名规则的原图副本）；其余本地 A2 路径不变。迁移既有清单绑定的同一批 60 张叠加图及 60 张原图副本，文件名、逐文件字节/SHA、panel_index、frame_id、object_id、stratum、surface、种子与配额不变；不重新抽样、不重新渲染，不增加看图轮次。保留原 panel-receipt 与执行收据字节，原路径作为历史来源；在现有 `receipts/run-<stage>-<utc>.json` 命名下新增 stage=relocate 收据，记录旧新路径映射、迁移前后计数/字节/SHA、原 panel-receipt SHA 及本裁定来源。逐文件核对相等后才移除旧落点对应的派生图片；失败保留源副本并按既有失败收据机制记录，不触碰归档原图。清单/报告引用新落点及迁移收据，不把旧生成收据重写成在新位置生成 | `artifact:docs/evidence/P1-ENG-ASSET-001-label-audit.md`；`artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §4/§6（迁移收据与同批图片核对） | K4 | 2026-09-08 |
| AC-6 修订 1 | 解释 AC-6、§3 表 A 与 §5：A1 仅增加 `.gitignore` 中一条 `/outputs/eng-asset/P1-ENG-ASSET-001/` 规则的写权限；A2 图片落点按 AC-4 修订 1，其余写入闭集不变。32 MB 是 `runtime/eng-asset/P1-ENG-ASSET-001/` 与 `outputs/eng-asset/P1-ENG-ASSET-001/` 两目录总和，含迁移临时副本；不扩大信封。生成器与路径检查适配新落点；旧 panel 路径停止作为写出目的地。实现者在保留新落点完整面板且旧落点无 jpg 的真实工作副本中，聚焦复测具名归档检查与本项受影响测试，记录新增失败闭合后再整理 K4 候选；报告保留此前 1 FAIL/9 ERROR 的分类，按工程 workflow §6 提供修后停点全套摘要，不以无归档副本的 skip 充当修复通过 | `test:tests.test_dist_data_round4.RealArchiveClosureTest.test_zero_unmatched_and_zero_multi_matched_jpg`；`artifact:docs/evidence/P1-ENG-ASSET-001-tests.log`；`artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §6 | K4 | 2026-09-08 |
| AC-6 修订 2 | 解释 AC-6 的 A1/A3 文档归属：本项实现者不直接写提案，合同问题写 A1 已允许的报告 §7，接受角色按来源转录至提案「待裁定」并答复；候选写入核对将提案修改归 A3。表 A A1 原「提案待裁定」许可在本项按此路由执行，其他角色权限不变；不要求修改或绕过 `check_role_writes.py` | `artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §7；`artifact:docs/proposals/P1-ENG-ASSET-001-legacy-asset-inventory-and-minimal-instruction-set.md` 待裁定 | K4 | 2026-09-08 |
| AC-3 修订 1 | 解释 AC-3 及首次接受释义：表 C 第 1 行 `NOT_CLASS_VERIFIED` 分支直接写 program/surface/resolved_reference_object_id=null、prospective_mother_eligible=false，不调用会解包裸 None 的上游资格函数；其余六值分支按原合同调用既有函数并取非 None 布尔值。本项不修 `tools/dist_data/`，不把该保护分支当作上游已修复或真实输入曾触发的证据 | `artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §6 限制 2；`test:tests.test_eng_asset_inventory.InstructionTests.test_status_derivation_matches_minimal_program_on_production_slice` | K4 | 2026-09-08 |

**补充裁定（2026-09-08；用户本会话指令及实现报告 §7 问题 4–6；非 C 轮）：**

- **问题 4——插图：当前呈现不满足 AC-4，交实现角色修复。** 接受侧只读查看
  `outputs/eng-asset/P1-ENG-ASSET-001/panel/panel-020.jpg`、其
  `original/panel-020-original.jpg` 和 `panel-042.jpg`，并读 `draw_panel` /
  `_paste_zoom_inset`。20 号插图覆盖了原图的大部分区域，原坐标框最后被画在已替换的
  像素上；“框最后画”只能保住框线，不能保住原坐标对应的图像。42 号展示了同一目标
  放大辅助的用途，但不能据此接受整批。这里裁定显示是否忠实，不代用户判断类别/颜色/框。
  标题避让目标的方向可接受；同一行目标的放大视图并非额外样本，但不得覆盖原图再
  沿用原坐标框。本项采用最小修复：移除插图，完整原帧加本行框，标题放在原帧外。
  AC-4 修订 2 限定本次重绘；原修订 1 的“不重新渲染”只约束原字节迁移，不再阻止该修复。
- **问题 5——机读条目：按 AC-4 修订 3 冻结下方格式及失败语义。** 原散文/宽松管道表
  约定不再作为交换合同。尚未收到用户判定，Unity 日志只建立空模板；实现角色先适配和
  验证解析器，格式错误不得静默丢行或输出全零统计。本次不要求用户提前填表或重新看图。
- **首次接受释义的归属：** 原文保留，逐项按下表挂到唯一主 AC 编号；核对表与实现者
  自证必须同时引用该 AC 的追加修订，不再把共享标题“AC-1/6”“AC-5/6”当作可省略项。
- **问题 6——未知类别病因：** 实现报告提出的无 S5 条目布局车分支也可使
  `frame_world` 产生 `class_word=None`，原括注“未绑定动态目标”不是穷尽病因。
  按 AC-3 修订 3 澄清并补针对实际成因的测试；不改七值判据、不删除原动态目标回归。
  报告所述 43,535/0 与 100% 成因计数本次未复算，不升级为接受侧或独立复核证据。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-4 修订 2 | 解释 AC-4 的“每张只画该行的框与 surface”和修订 1：当前带插图批次不用于正式用户判定。移除插图，以原帧完整画面为底图仅叠加本行 visible_norm_xywh 对应框；标题可保留本行索引/对象/surface，置于原帧外，不遮挡像素，不缩放或裁掉原帧；若画布增加边带，框与原帧同步平移。同一批 panel_index/frame_id/object_id/stratum/surface/种子/配额与原图副本不变，仅修复叠加图呈现；不得新抽样或增加看图轮次。实现者按既有成功收据命名新增 stage=render-fix 收据，记录修前/修后叠加图字节/SHA、未变的样本身份与原图 SHA、旧生成及 relocate 收据引用；保留旧收据原字节，更新清单所指当前叠加图及收据。种子/配额原先先提交的证据保留，重绘前提交当前配额文件并运行时绑定；不伪造新的抽样。图片仍落 outputs，原件只读，两本地目录（含临时副本）合计 ≤32 MB。修后由接受侧定点确认 20/42 号原帧完整且框对应原像素，再交用户一次看图；此确认仅验证显示，不替代标签判定或 C/R | `artifact:docs/evidence/P1-ENG-ASSET-001-label-audit.md`；`artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §4/§6；`test:tests.test_eng_asset_label_panel.LabelPanelTests.test_panel_preserves_source_frame_and_box_coordinates`（待实现，无模型合成图夹具） | K4 | 2026-09-08 |
| AC-4 修订 3 | 解释 AC-4 代录/只读统计接口：使用下方“代录机读格式 v1”；日志只能由接受/辅助代录，原话与结构化表同在该条目，统计只消费结构化表。stats 对条目缺失/重复、未完成、格式/取值错误、缺失/重复/额外 panel_index、有效行数与当前清单不相等的任一情况失败退出，只新增既有 failure-stats 收据，reason=`VERDICT_FORMAT_MISMATCH`（追加到 §3 表 B 失败原因闭集），offending 记录问题与行号；不写成功收据、不覆盖已有统计/清单/日志、不把错误转换为不确定或全零结果。完整合法输入才计算逐层统计、错误类型计数与不确定计数；不存在以残缺表交付部分统计的分支 | `test:tests.test_eng_asset_label_panel.LabelPanelTests.test_statistics_read_only_from_unity_log_entry`；`test:tests.test_eng_asset_label_panel.LabelPanelTests.test_verdict_table_format_mismatch_fails_closed`（待实现，覆盖本行失败闭集）；`artifact:docs/unity-test-log.md` 的本项条目 | K4 | 2026-09-08 |
| AC-1 修订 1 | 对应首次释义 AC-1/6：before/after 保存在 A2 已允许的同一 input-manifest 文件；失败只发布失败收据，不发布该次成功工件。图像 SHA 可取已核验 S1 引用，实际读图时逐张核验字节，不要求为每条指令读像素。原件保护按 AC-1 核对；实现路径权限由 AC-6 及其修订核对 | `artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §1/§6；`test:tests.test_eng_asset_inventory.ReconciliationTests.test_input_manifest_reverified_after_run` | K4 | 2026-09-08 |
| AC-3 修订 2 | 对应首次释义 AC-3：表 C 第 1 行按 AC-3 修订 1；其余解包 (program, ref)，“返回 None”指 program 为空，颜色取 program.target.color、关系取顶层 relation；母集资格取既有函数非 None 布尔值。对象重叠域仅各 split 的 UNIQUE_* 目标行，S4 held_out_objects.held_out_object_ids 标记原样继承；两者均不得表述成“对象从未出现在训练图像中”或已经建立正式评估集 | `test:tests.test_eng_asset_inventory.InstructionTests.test_overlap_table_matches_per_object_rows`；`artifact:docs/evidence/P1-ENG-ASSET-001-instructions-summary.json`；`artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §3 | K4 | 2026-09-08 |
| AC-4 修订 4 | 对应首次释义 AC-4：无唯一程序时 surface 保持 null，不编造指令；用户看图配合 fields 清单中该对象的 S5 类别/颜色/验证状态，缺记录或未验证可判不确定。抽查不回写 S5，不据抽查重算原样 S5 下的指令候选；机读表中的“不确定”只来自用户判定，不替代缺失记录 | `artifact:docs/evidence/P1-ENG-ASSET-001-label-audit.md`；`artifact:docs/unity-test-log.md` 的本项条目；`artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §4 | K4 | 2026-09-08 |
| AC-5 修订 1 | 对应首次释义 AC-5/6 的接口部分：§3 链路只是只读检查对象清单，不预断言函数互相调用；报告按真实代码给出各输入条件所属层与缺口及 file:line，接管实验仍归后续任务 | `artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §5 | K4 | 2026-09-08 |
| AC-6 修订 3 | 对应首次释义 AC-5/6 的测试/资源部分：五分钟只是规划估计，不是性能验收线；实现 focused、停点全套、复核验证只用无模型验证（含合成图等夹具），不用真实模型；报告注明因此未重跑的既有模型集成测试。AC-6 的 RSS、文件体积与零消耗边界保持；原件保护与输入核验按 AC-1 修订 1 逐项附证据 | `artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §6；`artifact:docs/evidence/P1-ENG-ASSET-001-tests.log` | K4 | 2026-09-08 |
| AC-3 修订 3 | 对应实现报告 §7 问题 6：表 C 第 5 值的括注解释为“执行域未知类别阻断体，包括无 S5 条目的非幻影布局对象或源身份未绑定的动态目标”；判定仍为返回无 program 且 class-only 冲突集包含 class_word=None，不改变优先序/计数/原函数。在原动态目标测试之外，使用生产 frame_world 及最小程序路径补无 S5 条目布局车 blocking 导致 WILDCARD_UNKNOWN_CLASS 的具名测试；报告区分两条机制与其真实数据证据 | `test:tests.test_eng_asset_inventory.InstructionTests.test_missing_s5_blocker_yields_wildcard_unknown_class`（待实现）；`artifact:docs/evidence/P1-ENG-ASSET-001-inventory.md` §3/§7 | K4 | 2026-09-08 |

**代录机读格式 v1（AC-4 修订 3 的组成部分）：**

- UTF-8 Markdown；文件中恰一处完整二级标题 `## UT-P1-ENG-ASSET-001-label-audit`；
  条目到下一个二级或一级标题之前结束。必有单行 `Schema: p1-eng-asset-001/verdicts/v1`、
  `Status: OFFLINE_VISUAL_CHECK`、`Judgment state: PENDING` 或 `Judgment state: COMPLETE`；
  stats 仅接受 COMPLETE。另有固定 `Panel manifest: docs/evidence/P1-ENG-ASSET-001-label-audit.md`。
- 恰一个三级小节 `### 结构化判定`，小节内只有以下表头、分隔行及数据行（可有空行）；
  到下一个标题结束。`### 用户判定原文` 独立存逐字反馈和会话/代录说明，不从该节解析表格。
- 表头与列序固定如下；单元格去掉首尾空格后判值，不接受反引号、额外列或合并单元格：

```text
| panel_index | 类别 | 颜色 | 框 | 错误类型 |
|---|---|---|---|---|
```

- 每个数据行恰五列；panel_index 为不带前导零的十进制正整数，按清单升序、恰一行对应
  当前面板清单中的一个 index；索引集合和行数必须与清单逐项相等（当前为 1–60），不能
  用重复 index 补足数量。类别/颜色/框各取 {对, 错, 不确定}；没有“未判定”或空值替代。
- 错误类型可为空；非空只允许 {类别错, 颜色错, 框不紧或截断, 遮挡误判, 车辆缺失或幻影}，
  多选唯一分隔符为中文顿号 `、`，不重复；按该闭集顺序写。不接受逗号/斜杠或未知词，
  不自动丢弃错误项。错误类型是否勾选以用户原话为准，不从其他三列自行推断。
- 接受/辅助取得反馈后原样保存，再据明确含义填表；含义不明保留待澄清，条目仍 PENDING，
  不补造结论。仅在所有面板三项判定齐备、与原文核对后置 COMPLETE；机器失败不消耗
  新看图额度，可修复代录/解析后重算。尚未取得反馈时空模板不含任何示例数据行。
- 清单的 panel_index 到 frame_id/object_id/当前 overlay_sha256 映射为图像身份依据；正式
  看图开始至统计结束不改该映射。源日志执行前后哈希核验纳入 AC-1；成功 stats 收据绑定
  实际读取的日志与清单字节/SHA。失败原因只写失败收据，不在原话或判定表中插入报错行。

## Acceptance rulings（复判）

| 来源（复核文件/轮次/finding） | 裁定 | 日期 |
|---|---|---|
| docs/reviews/P1-ENG-ASSET-001.md / R1@K4 F5；R2@K4 §1 修复核实 | 范围内必修（已修）。合同 §3 禁写根保护与 AC-6 原件零写入不因调用者传入覆盖路径而失效；采用 R2 的红/绿核实闭合，不新增接口或 AC。原复核依据 SCOPE_GAP 保留，账本 CLOSED；归因仍按原依据机械归入 BC 缺失，不擅改复核记录。 | 2026-09-11 |
| docs/reviews/P1-ENG-ASSET-001.md / R2@K4 F8 | 保留 SCOPE_GAP，账本 OPEN，非阻断。接受复核对本候选固定 CLI 与归档域的不可达判断；显式指定不存在的日志路径时裸 FileNotFoundError、无失败收据，但不发布统计。当前不扩大到此 Python API 失败路径；后续若复用可变日志入口或覆盖日志文件缺失，须先把此债纳入其合同/失败验证。 | 2026-09-11 |

**收尾决定：ACCEPTED；工作项 DONE（2026-09-11）。** 只消费最终 `R2@K4`
`PASS_WITH_NOTES`，不另开 C/R。通过候选从同名复核文件最后一条 passed_candidate
运行时解析；当前四模块、两测试、五证据、用户日志及 .gitignore 与该候选无差异。
F1–F4 已由复核闭合，F5 按上表闭合，F6/F7 补丁已核实；F9 为非阻断 CLASS_3，
两处逐字计数补丁仍交实现角色下一次提交应用，不开轮，本会话不改实现者报告。

三证据：实现报告 §6/§8/§10 与 tests.log（1156 例，0 failures、9 个既有环境 ERROR、
21 skip，另 Pillow 19 例 OK）；独立复核 R2@K4 §0–2（AC-1…6 满足，具名红/绿闭合）；
同文件 R2@K4 的 UNITY_NA 附议（纯离线，零 Play，不改变运行时行为）。本轮未跑测试，
未签独立复核。此前 C2 表是当时候选记录，其未决项由 R2 闭合记录及本节处置承接，
不把历史核对表改写成对返工候选的新核对。

未闭账本项为 F8；F9 文档补丁交接保留。S6 未执行、上游裸 None、原归档来源缺口、
框 UNVERIFIED 等继承限制保持；#27 的 S5 VERIFIED 与用户颜色判错并列，不回写 S5。
本项 DONE 仅验收盘点、描述性抽查与接口缺口清单，不证明语言选框/跟踪性能，
不冻结评估集，不关闭 COORD-010 迁移批或旧研究里程碑，不授权后续接入。

**归因与四项度量（按复核依据列机械派生）：** F1/F2 的 BC-1/BC-4 → 实现错误 2；
F3/F4/F6/F7/F9 的 IN_SCOPE_NO_BC → BC 缺失 5（阻断 2、非阻断 CLASS_3 3）；
F5/F8 的 SCOPE_GAP → BC 缺失 2（非阻断，分别 CLOSED/OPEN）。上轮漏检、上游漏检、
RED_LINE 均 0，不因接受侧曾提出关注而改归因。C 共 2、退回 1（同次包含“不满足”与
“证据缺失”，不重复计数）；K4 复核 2、REWORK_REQUIRED 1；BC 缺失按前述 5/2 分计。
ACCEPTED 后研究 BC 行 0（CLARIFY 0 / NEW_OBLIGATION 0）；本工程合同追加 AC 修订
12 条、新 AC 0，本次追加 0（工程轨道不套研究标签）。无冻结集终局、block/release 动作。

## Contract conformance（核对表）

本表保留 C2 候选的核对结论；返工后的最终处置以本提案复判节及独立 R2@K4 为准。

**C2@K4（接受角色，2026-09-11）：核对完成，附本表与未决关注项交独立复核。**
D3 `ACCEPTED` 与 AC-1…6/十二条修订保持；设计退修累计 2，C 已核对 2 / 退回 1，R 0。
本停点唯一 C 退回额度已在 C1 使用，本轮不再退回。下一角色核实开轮条件后决定
`R1@K4` 或 `REVIEW_BLOCKED`；本表不签独立 verdict，不分 CLASS/依据标签，不新增 AC。

**候选与读取范围。** 开工工作树干净，C1 后实现修复已完整提交。候选从本轮开工 HEAD
运行时解析，增量基线为前一接受侧 C1 提交；已读取其九文件完整变更（摘要 JSON 逐对象
展开全部新增程序集合并核实其余字段未变）、直接关联生产入口/清单机制/测试、报告
§4–9、全部 AC 及修订与本地收据。累计候选范围仍为 C1 已完整读取的四模块、两测试、
五证据与 `.gitignore` 单条 outputs 规则；开工基线为 inventory 首次引入提交的父提交。
A3 合同/日志及直接关联上游、控制协议是只读依据，不因不在实现修改范围而排除读取。
本地 origin/main 尚未包含开工候选（ahead 4）；报告 §8 的“已推送”缺本轮可核实依据，
未访问远端，不把本地跟踪引用当成远端最新状态。复核侧须核实完整候选交付与开轮条件。

只读现有工件：最新 stats 收据的 verdict_source 与当前日志 SHA 相等、读入/写出清单
均与当前清单相等；audit-stats 的 64 条登记输入当前字节与所记 SHA 相等，**不含日志**。
60 张叠加图及 60 张原图副本仍分别匹配既有重绘收据的 after/original 哈希。两派生目录
合计 10,244,893 B。未运行实现测试、盘点、stats 或重绘；实现者日志为 1152 例、9 个
既有环境 ERROR、21 skip，另有 Pillow 环境 15 例 OK；不表述为全套全绿。

| AC（含追加修订） | 结论 | 理由与具体指针 |
|---|---|---|
| AC-1（修订 1） | 不满足 | C1-1 的核验前发布已改次序；inventory 164 输入对账证据保留。但 stats 删除日志登记，执行末尾才计算 verdict_source，且停点并集未完成当前核验，见 C2-P1/P2；64 条 equal=true 不能证明日志未变。 |
| AC-2 | 满足 | fields 的 101 辆/8 辆无 S5/57,430 行分类保持；报告 §4 已并列 #27 的原 S5 VERIFIED/USABLE 与用户颜色判错，不再误归 UNVERIFIED，C1-4 已修正。 |
| AC-3（修订 1/2/3） | 满足 | inventory.py:612 新增 programs_by_split；摘要的 86 个 UNIQUE_* 对象已逐项提供五个 split 集合，其余内容未改；test_per_object_programs_are_split_scoped 对准跨 split 对象。原函数复用、17,337/27,074 域差及未冻结评估集保持，C1-3 已修正。 |
| AC-4（修订 1/2/3/4） | 不满足 | C1-2 的冻结身份比对与图片实字节检查已加入，生产夹具也有面板表；但源日志未作前后核验（C2-P1），空/PENDING overlay 哈希跳过比对（C2-P4）。当前 60 行判定与统计继续有效：类别 60/0/0、颜色 59/1/0、框 52/0/8；不要求重新看图。 |
| AC-5（修订 1） | 满足 | 报告 §5 按真实代码写明单帧 schema/clock_id/有限非负校验，无跨帧单调保证；箭头链明确为检查对象而非调用链。10 条条件与 G-1…7 保留，C1-6 已修正，不触及运行时实现。 |
| AC-6（修订 1/2/3） | 证据缺失 | 本地完整提交候选与体积/实现者测试证据已补齐；停点输入并集与推送证据仍缺（C2-P2）。原件保护的异常清理/后置路径检查需复核生产路径（C2-P3）；本轮不自行签其通过。 |

**C1 回交的处置。** C1-3/4/6 在本轮只读核对中满足；C1-1 的 plan/panels/render-fix
发布已移至输入核验后，inventory 也先核验三件输出目的地，但异常/后置路径检查仍有
C2-P3 关注；C1-2 已比对 frame/object/stratum/surface 并读取冻结 overlay，仍有 C2-P1/P4；
C1-5 的未提交交付物和最新 stats 单次日志 SHA 不符已修正，停点并集缺口仍见 C2-P2。
C1 全文回交理由保留于 Git 历史，报告 §9 是实现者回应，不以“六项全部修复”代替本表。

**预复核关注项（待核实主张，不是新增合同或独立 finding）：**

1. **C2-P1 — stats 源日志核验被删除（AC-1 修订 1、AC-4 修订 3）。**
   本次 diff 删除旧 `manifest.record(log_path, ...)`。现 `label_panel.py:1348` 解析日志，
   1358 行 recompute 只覆盖已登记的 64 个输入，1400 行在发布清单后才重新计算日志 SHA。
   若日志在解析后、发布前变化，统计仍来自旧字节，成功收据却能绑定新字节。当前真实
   audit-stats 的非图片输入只有 instructions、S5、panel-receipt、render-fix 四件，
   加 60 图恰为 64；报告 §9 所列“含 Unity 日志的 64 条”与实际不符。
   `test_stats_fails_closed_when_input_changes_midrun`（tests:523）修改的是 instructions，
   成功用例（478）也未断言日志在 before/after 中，故现有绿记录未覆盖该退化。
2. **C2-P2 — 停点输入并集和交付自证仍不完整（AC-1/6、workflow §4.3.1）。**
   input-manifest.union 中日志与 audit 两行的字节/SHA 仍不等于当前文件；前者还因
   C2-P1 未被本次 stats 刷新。render-fix 历史阶段仍只有三条输入，60 原图副本的登记
   仅补在新代码（1158），未成为本次停点并集证据；本轮原图与旧收据相符不补造历史
   before/after。合法清单输出、合法日志代录与受保护原件须分别解释，不能覆盖旧收据
   或仅以单阶段 equal=true 代替并集核验。报告 §8 推送声明亦见上方候选说明。
   保留既有用户判定和面板，不以补证为由重新生成它们。
3. **C2-P3 — 失败发布与禁写保护的生产边界尚待核实（C1-1 及原预复核关注）。**
   `stage_panels` 的 finally（label_panel.py:970）无条件从传入 panel_root 重算
   `.staging-panel` 并清空；若传入禁写根且其下已有该目录，868 行拒绝后仍会执行清理。
   同入口 913–916 行先发布图片，934 行才检查 panel-receipt 目的地；local_root 为禁写根
   时仍可能已发布图片再失败。新增两条发布回归覆盖 plan 输入变化、panels 第二图哈希
   不符；未覆盖上述拒绝分支，亦无生产 stage_render_fix 的中途失败回归。
   inventory 本次先整体检查三目的地的修正可见；不要把 helper 测试视为这些入口已验证。
4. **C2-P4 — 冻结图像 SHA 缺失会跳过比对（AC-4 修订 2/3）。**
   `label_panel.py:1325` 显式允许清单 overlay_sha256 为 `""` 或 PENDING 而不报差异，
   后续仍用该清单值写成功统计。当前真实清单 60 项均有有效 SHA、与实图相符；关注的是
   缺失身份凭据的失败分支。新 `test_stats_refuses_when_overlay_bytes_differ_from_manifest`
   只覆盖一个非空哈希不符，未覆盖空/PENDING；请复核其与冻结映射合同的相符性。

报告 §1 输入数已修正为 164，§8 修订数为十二；§9 末段仍写 Pillow 11，实际日志为 15，
属叙述残留，随证据一致性核实。COORD-010 迁移批独立复核/UNITY_NA、上游裸 None、
S6 未执行等既有义务不变；本轮无 SCOPE_GAP/release，不启动后续接入，不记 DONE。

## 决策记录

- 2026-09-08 D1 `PROPOSED`：构思角色落盘；承接 `COORD-010` §9 交接。用户三项范围定局
  （逐字：「只盘点 Tier-1 闭集模板（推荐）」「允许，限 CPU/零 ID/限次数（推荐）」「用户看图，
  ≤ 60 张（推荐）」）见账本同日「P1-ENG-ASSET-001 — 提案范围三项定局（方向层）」，不构成
  执行额度。轨道申请 `engineering-v1` 待接受裁定；执行信封待 `ACCEPTED` 后用户授权入账。
- Decision: **REVISION_REQUESTED**（接受角色，2026-09-08，D1；第一次设计退修）。
- 轨道：本项是 COORD-010 后的新 ID，六项任务说明及 Tier-1/离线盘点方向与已授权
  工程首版范围相符；但本轮未 `ACCEPTED`，`Workflow: engineering-v1` 仍只是申请，
  不签发生效裁定，不冻结 AC/schema/信封。修订后再在接受时逐字裁定。
- 保留的有效部分：§8 已有真实 S3/S4/S5 行数、绑定数与流式扫描收据，不要求重做全量
  扫描；只盘点旧划分、固定评估集候选不冻结、无语言模型调用、不借用旧里程碑关闭的
  边界成立。COORD-010 迁移批独立复核与本批 UNITY_NA 缺口仍保留。

**退修闭集 AR1-1…AR1-5（构思角色修正文档后交 D2；不是独立复核 finding）：**

| 编号 | 具体问题与依据 | 修订要求 |
|---|---|---|
| AR1-1 | §3/AC-6 把 evaluator 真值框及 S3 投影监督框送入 tracker，违反上述输入隔离；静止段替代不能消除来源问题。 | 删除这两类初始化输入。只在能逐帧绑定既有、非真值来源的人工/感知框时提出实播种；明确来源闭集、帧对应证明及可用段数。缺少合规种子的段如实记 `NOT_PROBED_TRUTH_ISOLATION`，只交接口缺口，不伪称探针执行。IoU 对照保持 evaluator 侧，不用于选择/修正种子或触发 tracker 更新/重播种。不得自行增加人工标框任务或红线例外；确需例外须另提具体用户授权，不能由本角色解释放行。 |
| AR1-2 | §5 的“≤40 段”只限制不同序列，配合“工程性重试不重复授权”没有累计尝试上限；§8 的旧 p95 不是整条读图/初始化/评分流程的耗时上界。AC-6 未定义段选取/截断及 init/update 失败、参考框缺失、序列结束仍未跌落的记录。 | 根据 AR1-1 的实际可用种子重列申请值：阶段、不同段数、包含失败与重试的累计真实模型重放次数、每次最多帧数及累计处理帧上限；明确开发/停点/复核中真实模型调用如何计入同一信封，纯 mock 夹具单列。定义确定性段选择与截断顺序、上述失败/缺参照/未跌落的状态与 null 语义，报告实际执行数与未执行原因。删除无界重试解释；收据估算区分旧内核 benchmark 与本次端到端，任何执行额度仍待用户授权。 |
| AR1-3 | §3 要求 probe.json 内嵌最多 128k 帧记录、eval-candidate.json 内含 test 候选，却同时限制 docs/evidence 单文件≤2 MB；§8 只测输入扫描，缺新行体积及这两项输出投影。AC-8 的 git status 加六件 manifest SHA 也不能证明被忽略的原图/sidecar/分片/日志零改动（三个 runtime 原件目录均被 git ignore）。§2 探针“不写 runtime/”与 §3 的 runtime/eng-asset 派生输出、AC-8 路径闭集与 tests.log 互相冲突。 | 用少量真实样本只读、内存序列化补新输出的行字节数、数量上界和驻留估算；无需重跑全量或模型。为超限明细指定本地有界/流式落点，摘要记录行数、字节及可验证来源；同步 §2/§3/§5/AC-8 的唯一写出闭集，含测试日志及失败收据。把原件保护核验落到具名输入清单的实际字节/树成员或可证实的只读隔离，覆盖本项实际读取的 manifest、分片、图像、sidecar、日志；不能用未改变的 manifest 代替其引用文件的核验。既有原件不回写。 |
| AR1-4 | §3 的“一律通配阻断”未区分未知字段与已知类别，§6“颜色未验证对象只能进 class-only”又排除了 AC-3 允许的无色关系程序。既有 `tools/dist_data/tier1_lang.py` `_noun_conflicts` 按字段冲突，`tools/dist_data/build_catalog.py` `minimal_program_with_reference` 会在颜色未验证时继续搜索无色关系；§3 六值结果没有约定多失败重叠时优先序及无唯一程序的空值。 | 明确复用既有构域/最小程序函数及其确定性顺序，或逐项给出与它们等价的适配合同；不把 phantom/颜色未知改成无条件阻断不同已知类别，动态目标是否加入以本帧 blocking 为准。统一 §3/§6/AC-3，定义六值互斥统计优先序、无程序时 program/surface 的表示、未入划分帧的标记与 AC-2 总数对账域。AC-7 保留目标及关系 ref 的对象来源/重叠信息，并明确记录粒度是逐帧三元组还是对象分组内列帧，不能在“按对象去重”时丢失程序与帧绑定。§8 近似数保留规划标签，不升级为上述精确合同的证据。 |
| AR1-5 | AC-4 四层可重叠且可能不足额，未给去重/归层/不足额规则；其命令只证明配额提交早于判定，无法证明早于面板生成。§3 仍把用户原话放在实现证据，与本轮待裁定答复落点不一致。 | 写明面板抽样单位、四层重叠处理、各层配额及不足额处置，使唯一图片总数≤60且各层分母可复算；定义错误类型可否多选和“不确定”的计数。生成面板前提交配额/种子，面板生成收据在运行时解析并绑定该提交及输入来源，不能手写候选 SHA 或以判定时间代替生成顺序。用户原话仅由接受/辅助角色代录进离线日志条目，工具据该记录出统计；不把未判定或空层当通过，也不启动新的人眼任务。 |

本轮只做设计决策与既有接口的只读核查，未运行实现测试、全量盘点或模型；不新增
BC/AC，不修改实现或复核文件。预算申请尚未形成可授权的完整信封，故先完成上述修订，
不向用户请求批准一个仍有冲突的版本。D/C/R 计数分别为设计退修 1、核对 0、复核 0；
若 D2 再次退修，按 workflow §4.2 上交用户二选一，不自行发出第三次退修。

- 2026-09-08 D2 `PROPOSED`（构思角色，回应 AR1-1…5；待接受裁定）。逐条映射：AR1-1 →
  §2 不做清单、§3 表 A 种子闭集与红线、AC-6、§8 表 5（真值/投影框种子全部删除，绑定
  证明与可用段数逐条给出）；AR1-2 → §5 信封按单次/累计/夹具分列、AC-6 段选取/截断/失败/
  缺参照/未跌落语义、§8 表 5 调用计数与端到端估算；AR1-3 → §3 表 B/表 C 唯一写出闭集、
  AC-1 输入清单、AC-8、§8 表 1/表 6 真实行字节与驻留；AR1-4 → §3 逐字复用 `frame_world` +
  `minimal_program_with_reference`、表 D 七值优先序与 null 表示、AC-2 对账域、AC-3、AC-7
  粒度与 ref 重叠、§6；AR1-5 → AC-4 抽样单位/归层优先序/配额/不足额/每对象上限、运行时
  收据绑定提交、错误类型多选与「不确定」计数、原文落点。§8 只补只读样本数字，未重跑
  全量扫描、未运行模型。D2 无新增待裁定；执行信封仍待 `ACCEPTED` 后用户授权入账。

- Decision: **REVISION_REQUESTED**（接受角色，2026-09-08，D2；第二次设计退修）。
  已完整读取 D2 合同、D1 五项要求、继承清单/缺陷账本、相关正式设计、原上界证据及
  `build_catalog` / `tier1_lang` / `trackers` 的直接接口；本次为提案决策，非 C 轮或独立复核。
  未运行实现测试、全量扫描或模型，未生成盘点工件。轨道申请仍未生效，AC/schema 不冻结，
  §5 仍为申请值，执行额度仍为 0；正式设计没有已接受变更需要同步。

| D1 要求 | D2 裁定 |
|---|---|
| AR1-1 | 设计层闭合：种子改为既有人工/感知框，表 A/表 5 给出逐帧绑定规则与可用规模；真值和 S3 投影只留评估侧。绑定数字是构思侧试读，本轮不冒充独立重算或执行证据。 |
| AR1-2 | 部分闭合：确定性分段、单次与累计真实调用上限、失败计费和夹具区分已写；失败与未跌落仍混淆，见 AR2-2。20 ms/帧仅为规划假设，不是实测上界或执行保证。 |
| AR1-3 | 部分闭合：已有真实行字节/驻留估算、本地流式明细与实际输入哈希复核；唯一写出闭集与实现交付互斥，见 AR2-1。 |
| AR1-4 | 设计层闭合：构域/最小程序指定复用函数；幻影与动态目标按字段冲突，关系程序与 null、未划分对账域、目标/ref 的逐帧绑定均已写；近似数字不升级为精确合同证据。 |
| AR1-5 | 设计层闭合：抽样单位、归层顺序、不足额不回填、对象上限、配额提交绑定与不确定计数均已定义；用户原文代录落点保留。§8 表 7 仍是近似分母，不能替代 AC-4 的正式分层统计。 |

**剩余缺口闭集（交用户决定，不是发给构思角色的第三轮退修指令）：**

| 编号 | 可定位的问题与后果 | 保留当前范围时须明确的处理 |
|---|---|---|
| AR2-1 | §3 红线段要求代码放在 `tools/eng_asset/`，AC-1…8 要求新增 `tests.test_eng_asset_inventory` / `tests.test_eng_asset_probe`，但表 C「唯一写出闭集」只有七份证据、本地工件、提案/状态更新，AC-8 又要求受版本控制的改动只含表 C 第 1、3 行。故实现者写工具/测试会违反 AC-8，不写则不能实现本合同；AC-4 要求接受/辅助代录的 Unity 日志也未列入该闭集。另 AC-1 的“任一不符即零派生工件写出”与每次执行收据需要区分成功工件与失败收据。 | 明确区分角色可修改的源文件闭集、工具运行时输出闭集及失败收据；具名纳入本项工具/测试与接受/辅助日志路径，保持原件禁写。不能由实现者自行把“唯一”解释成例外；本轮不代作者改写或扩大路径授权。 |
| AR2-2 | AC-6 把 `update` 不 ok 的帧记 `LOST` 且框/分数为空，但 `first_drop_index` 只看 `iou_ref < 0.3`，无一次可计算的低 IoU 就记 `NO_DROP`。具体反例：初始化有参照且 IoU 合格，此后每帧 tracker 均返回 lost；后续 IoU 因无预测框为 null，该段却仍可记 `NO_DROP`，既不是“无参照段”，也不能回答“播种后跟多久”。初始化失败、部分参照缺失与序列截断之间的 drop 状态优先序也未唯一化。 | 将 tracker 丢失与可计算参照下的 IoU 跌落分列，或明确统一事件规则；给 init 失败、全部/部分缺参照、LOST、截断与观察结束的确定性状态/null 优先序。保留原阈值与零重播种，不把不可评估或 tracker 失败表示成持续跟踪成功；不得据当前 `NO_DROP` 汇总跟踪时长结论。 |

两项均来自 D1 已点名的合同一致性/失败语义，尚无实现候选，不签发复核 finding，
不使用 CLASS 或 SCOPE_GAP 账本代替设计裁定。有效范围、合规种子方案与只读试读保留；
COORD-010 迁移批独立复核和本批 UNITY_NA 缺口不变。

按 `docs/collaboration-workflow.md` §4.2：设计退修累计 **2**，核对 **0**，复核 **0**。
**下一动作只交用户二选一**：(a) 接受当前范围并逐条保留上述两项已知缺口，明确其处理后
由接受角色落定合同与轨道，再另行落实执行信封；(b) 将本项关闭为负结果记录，保留 D1/D2
与有效试读，不记 DONE。不自行启动 D3，不把用户尚未答复写成授权；本轮未接受或关闭本项。

- 2026-09-08 D3 `PROPOSED`（构思角色；**用户范围收敛版，非第三次常规退修**；待接受角色
  逐字记录范围变更并裁定）。依据：账本同日「P1-ENG-ASSET-001 — 用户处置 D2 第二次退修：
  保留方向、收敛范围」。用户处置不是 §4.2 二选一中的任一项，而是保留方向并主动收敛范围，
  指示构思角色据此修订；本条只转录该决定，不构成接受或授权。改动：§1 改为用户逐字的三个
  问题；§2 交付收敛为盘点报告、一次分层抽查、只读代码检查的缺口清单，删除离线播种/重放
  实验（跟踪时长、IoU 跌落、模型调用预算、探针工具及其测试）并注明并入后续语言选框接入
  任务，取消固定评估集交付；§3 表 A 按 AR2-1 分三类写清 A1 实现者可修改的源码/测试路径、
  A2 工具运行时可生成的文件（含失败收据）、A3 其他角色按权限写入（含 Unity 日志代录条目），
  禁写闭集与输入清单核对保留；既有指令函数复用（`frame_world` + `minimal_program_with_reference`、
  七值优先序）与抽样规则保留；§5 模型推理为 0；§8 复用已取得的只读数字，表 5 随探针移除。
  AC 映射：D2 AC-1 → AC-1（加失败收据）；AC-2 → AC-2；AC-3 + AC-7 的划分/重叠统计 → AC-3
  （不冻结评估集）；AC-4 → AC-4；AC-5 → AC-5（只读代码检查，加输入条件清单）；AC-6 探针
  删除（并入后续任务）；AC-7 固定评估集删除；AC-8 → AC-6。AR2-1 由表 A 闭合；AR2-2 因探针
  移除而失效，其失败语义要求随该范围转入后续接入任务。K4 核对、独立复核与 `UNITY_NA`
  附议要求保留。执行授权（实现、数据加工、用户看图）仍待 `ACCEPTED` 后用户逐字入账。


- Decision: **ACCEPTED**（接受角色，2026-09-08，D3 用户范围收敛裁定）。
  用户逐字决定：“我选择保留这项工作的方向，并把范围收敛为一个小任务：确认旧资产是否足以
  支持下一步受限语言选框接入。”完整原文已由授权发生所在构思会话记录在账本同日
  「用户处置 D2 第二次退修：保留方向、收敛范围」条目；本角色消费该条，不重复制造授权。
  **范围裁定：同意该收敛，当前合同仅为 §2 三项交付。** 这是用户直接调整范围，非接受角色
  自行开启第三次常规退修；历史设计退修计数仍为 2，C/R 为 0，不重置计数。
- **轨道裁定：本工作项适用 `Workflow: engineering-v1`，自本次 ACCEPTED 生效。**
  理由：COORD-010 后独立新 ID，自初稿即有申请行；六项合同齐全；只做离线资产与指令盘点、
  标签抽查和只读接口检查，不改运行时安全/主指标，不涉硬件目标或对外发布。AC-1…6 与
  首次接受释义一并冻结，日期已填；K4 合并候选保留 C/R 与 UNITY_NA 附议，不能以盘点取代旧门。
- **上轮缺口处置：** AR2-1 的源码、工具输出和其他角色记录已分为 A1/A2/A3，失败收据已
  独立，首次接受时补明本项 diff 与他角色 A3 的检查口径；AR2-2 随真实探针移出当前范围，
  不再阻塞本项，也不冒称其失败语义已经通过验证。后续接入若引入该实验，应自行定义其合同。
- **接受理由：** 三个问题逐项对应 AC-2/3/5，AC-1/6 保护来源和交付，AC-4 提供语义抽查；
  §8 已有输入尺度、绑定情况、真实行字节与驻留估算。原函数复用、原 S5 未审计限制、
  旧划分不回流、零模型与原件不覆盖均保留；没有以另名恢复探针或固定评估集交付。
  本轮只读合同、继承依据与直接接口；未跑实现测试或模型，不签发独立复核。
- **执行仍关闭：** §5 只是申请值。下一步请求用户授权实现 A1、在桌面 CPU 上按 AC-1…6
  进行本地盘点/测试及 A2 写出，并生成一次 ≤60 张面板供用户判定；本地工件 ≤32 MB，
  受版本控制的 A2 文件各 ≤2 MB，峰值 RSS ≤1 GB，模型/API/GPU/Play/正式 ID/下载/发布均为 0。
  获授权前不交实现者开工。正式设计同步 v0.3.37；COORD-010 迁移批复核/UNITY_NA 缺口不变。

- 2026-09-08 执行授权入账（接受角色，不新增 D/C/R 轮）：用户逐字“授权”，对应本会话
  对已接受合同的实现、本地 CPU 盘点与一次 ≤60 张面板请求；完整信封见账本同日
  「授权收敛合同实现与本地盘点」。§5 申请转为已授权，AC 与范围不变；交 Cursor
  实现角色开工，先按 AC-4 提交抽样种子/配额再生成面板，用户判定由接受/辅助代录，
  稳定候选按 AC-1…6 自证后交 C1@K4。无模型/API/GPU/Play/正式 ID/下载/发布额度。

- 2026-09-08 实现期合同裁定（接受角色）：D3 `ACCEPTED` 与 engineering-v1 保持；
  报告 §7 三问按「待裁定」追加 AC-4 修订 1、AC-6 修订 1/2、AC-3 修订 1。
  面板迁移和相关代码/测试修复归账本同日信封内「本地工程性修复」，只改变派生图片
  落点并保留同一批图片，零新增看图/模型/API/GPU/Play/正式 ID/下载/发布。
  已有实现者证据不冒充稳定候选通过；先交实现角色修复并提交/推送，再看图、代录与统计，
  自证后进入 C1@K4。本次未跑实现测试、未签独立复核、未新增用户授权。

- 2026-09-08 补充合同裁定（接受角色，用户本会话要求）：报告 §7 问题 4/5/6 均已答复；
  当前插图呈现不满足 AC-4，按修订 2 做同一批显示修复；修订 3 冻结机读条目/失败语义；
  首次释义全部归入同编号修订。修复不增加样本、看图轮次或模型/资源额度；未代用户判定。
  迁移成功及全套新增失败归零仅按实现证据更新状态，不自签实现通过或独立复核，D/C/R 不增。

- 2026-09-09 用户要求检查实现结果（接受角色）：AC-4 修订 2 的 20/42 显示确认通过；统计成功路径的
  输入核验/来源保留两项偏差见核对表节的实现期记录，交实现角色修复。修复归既有信封内本地工程性修复，
  不重抽样、不新增看图轮次或模型/资源额度，不改 AC。用户标签仍 PENDING，D 退修 2、C/R 0。

- 2026-09-11 C1@K4（接受角色）：按核对表 C1-1…6 退回实现；K4 的 C 退回额度已用 1/1，
  修后 C2@K4 随表交独立复核。D3 ACCEPTED/全部 AC 不变，未跑实现测试、不签独立复核。
