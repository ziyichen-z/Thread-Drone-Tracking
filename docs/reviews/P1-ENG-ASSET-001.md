# P1-ENG-ASSET-001 — 独立复核（engineering-v1）

Reviewer/role: 复核角色 / independent verification（新鲜上下文会话，Fable 池；
档位不低于实现者）
Workflow: engineering-v1（接受角色 2026-09-08 于 D3 `ACCEPTED` 时逐字裁定生效，
提案抬头第 4 行逐字 `Workflow: engineering-v1`；本轮按 `docs/engineering-workflow.md`
§5/§6 与 `docs/roles/review.md`「工程轨道」节执行）
Round: R1@K4
Date: 2026-09-11
Implementation snapshot: 候选 = 状态板 Active handoffs 行「C2@K4 已完成，随提案核对表
交独立 R1@K4」指向的主树 HEAD（`git log -1` 主题「P1-ENG-ASSET-001 C2@K4 核对完成并附
未决关注交独立复核」）；实现内容与其父提交（主题「C1@K4 六项回交全部修复，交 C2@K4」）
相同，HEAD 本身只改四份 A3 文档。本 work ID 无上一通过候选，全量 diff 基线 =
`tools/eng_asset/inventory.py` 首次引入提交的父提交（`git log --diff-filter=A
--format=%H -- tools/eng_asset/inventory.py` 的父，主题「D3 接受收敛合同并记录执行授权」）：
18 个文件 +11,234/−23 —— `tools/eng_asset/{__init__,receipts,inventory,label_panel}.py`
（26/374/904/1,466 行）、`tests/test_eng_asset_{inventory,label_panel}.py`（592/749 行）、
五份 `docs/evidence/P1-ENG-ASSET-001-*`、`.gitignore` 一条 `/outputs/eng-asset/P1-ENG-ASSET-001/`
规则、七份他角色文档（提案/状态板/账本/Unity 日志/implementation-status/正式设计）。
`controller/`、`Assets/`、`config/`、`tools/dist_data/`、`ProjectSettings/`、`Packages/`
零字节改动。
round_candidate: 920cc59d04bcb87aedd8a992a2ac950d7ae45ea9
Verdict: REWORK_REQUIRED
Latest round: R2@K4 — PASS_WITH_NOTES（见文末「## R2@K4 — 2026-09-11」；本抬头保留 R1@K4 原文，轮次只追加）

## 0. 复核范围与停点

- **轨道判定**：提案抬头逐字 `Workflow: engineering-v1`，且接受角色在决策记录 D3
  `ACCEPTED` 条逐字写「本工作项适用 `Workflow: engineering-v1`，自本次 ACCEPTED 生效」
  → 工程轨道。依据列仍取 workflow §4.4 六值闭集，`BC-n` 读作任务合同 `AC-n`，对应关系
  写在各 finding 首行「依据条款」。停点 = 合同 §7 唯一必经停点 `K4`（派生指令标签与分层
  抽查判定）；AC-1…6 合并为一个候选。
- **复核对象来源**：状态板 Active handoffs `P1-ENG-ASSET-001` 行（`AWAITING_INDEPENDENT_REVIEW_K4`）
  与提案「Contract conformance（核对表）」C2@K4（结论 AC-2/3/5 满足、AC-1/4 不满足、AC-6
  证据缺失；预复核关注项 C2-P1…4）。核对表与报告 §9「六项全部修复」只作待核实主张。
- **开轮资格（COORD-007 R1）**：`git diff <基线>..<候选>` 在 PLAY_GOVERNING 集合上非空
  （`tools/eng_asset/*` 四文件、`tests/test_eng_asset_*` 两文件，均为新增）→ 开轮。未触及
  Play 治理门文件（`analyze_m3_body.py`、`preflight_reanchor_env.py`、`controller/run_log.py`），
  无闭环轮义务。本停点无消耗性交接，无 `blocks_consuming_gate` 行。
- **停点自证核实（workflow §4.3.1 四项）**：条件 1（范围/接口冻结）、2（相称测试：
  停点全套日志 `docs/evidence/P1-ENG-ASSET-001-tests.log` 末尾 `Ran 1152 tests` /
  `FAILED (errors=9, skipped=21)` + `.venv-yoloe` 附录 `Ran 15 tests … OK`，9 个 ERROR
  逐条是系统 `python3` 缺 `cv2`/`numpy` 的导入失败，与实现者声明的基线同集）、3（零 Unity
  Play；唯一新增自动失败已按 AC-4 修订 1 闭合）、4（状态板/候选/未验证风险已更新）按字面
  成立，**不给 `REVIEW_BLOCKED`**。但条件 4 中「候选 commit 已推送」**不实**：复核时
  `git ls-remote --heads origin main` = `a108a1e…`（2026-09-09「显示确认通过」提交），本地
  `main` 领先 5 个提交（含候选与 HEAD），见 F4。
- **副本**：`git worktree add --detach .claude/worktrees/review-P1-ENG-ASSET-001 <候选>`；
  读码、重跑、探针全部在副本内；本地派生目录（`runtime/eng-asset/P1-ENG-ASSET-001/`、
  `outputs/eng-asset/P1-ENG-ASSET-001/`，git 忽略）与 `runtime/dist-data/*/attempt-2` 只在主树
  按绝对路径**只读**核对，未运行任何会写主树 `runtime/`/`outputs/` 的阶段；收工删除副本。
- **重跑（不信报告数字）**：副本内 `python3 -m unittest tests.test_eng_asset_inventory
  tests.test_eng_asset_label_panel`（系统 python3 3.14.6，无 Pillow）→ `Ran 26 tests … OK
  (skipped=1)`；`.venv-yoloe/bin/python`（3.12.13，Pillow 12.3.0）脚本模式 →
  `tests/test_eng_asset_label_panel.py` `Ran 15 tests … OK`（0 skip，AC-4 修订 2 像素用例
  真实执行）、`tests/test_eng_asset_inventory.py` `Ran 11 tests … OK`。输出写会话 scratchpad
  `focused-sys.log` / `focused-venv-label.log` / `focused-venv-inv.log`，只回显摘要。测试树
  哈希：`HEAD:tests` = `2a8e00aaf0b8acb0b0e4b6fe50507142f06db08b`，`HEAD:tools` =
  `4e5f7178d3949305608d5b4afc0c272be45008fa`，`HEAD:tools/eng_asset` =
  `c3ef60834c84251268997d3f391d865a236f9f1e`；四个触及源文件 blob：`inventory.py`
  `f0be9ab3…`、`label_panel.py` `7644b8d5…`、`receipts.py` `6e85c3e9…`、
  `test_eng_asset_inventory.py` `4c5125af…`、`test_eng_asset_label_panel.py` `4729283f…`。
  全套自动测试是实现者停点义务，本轮不重跑全套（workflow §4.4）。
- **独立复算（真实 attempt-2，只读）**：用副本代码中的上游函数按合同 §3 表 C 自写判定，
  逐行流式重算全部 151 个 S3 分片（43,535 域内帧、57,430 (帧,车) 行，62.2 s），与
  `runtime/eng-asset/P1-ENG-ASSET-001/instructions.ndjson.gz` 逐行比对 `frame_id/object_id/
  split/uniqueness_status/program/surface/resolved_reference_object_id/prospective_mother_eligible/
  mother_usage/visible_norm_xywh/short_side_px` **十一字段 0 不符**；七值直方图与报告 §3 表
  逐格相等（38,972 / 2,926 / 2,337 / 6,065 / 3,291 / 3,839 / 0）。受版本控制的 `fields.json` /
  `instructions-summary.json` 重新计数：101 辆布局车、8 辆 `NO_S5_ENTRY`、37/56/8、30 桶、
  57,430 对、去重 32/99/116/161、重叠 14/10/31、留出 32/20、母集 27,074 / 17,337 / 差 9,737、
  84/93 与 86/93，与报告 §2/§3 一致。
- **面板与判定核实（真实工件，只读）**：60 张叠加图 SHA-256 与 `label-audit.md` §3 清单逐张
  相等；60 张原图副本与 `panel-receipt.json` `source_sha256`、S1 `records[].sha256`、当前归档
  帧字节三方逐张相等；`panel-receipt.json` `quota_file_commit` = 首次提交 `label-audit.md`
  的提交（主题「AC-1…3 实现与 AC-4 抽样契约」），SHA `edaae148…` 与清单 §4 相等；render-fix
  收据 60 张 `original_sha256_unchanged` 全真、`after` SHA 全部出现在清单。用 Pillow 对 60 张
  叠加图做像素级核对：画布全部 640×496（原帧 640×480 + 16 px 标题带），原帧区域与原图副本
  逐像素比较，排除框线外一个 JPEG 块（±8 px）后最大绝对差 10（纯 q95/4:4:4 二次编码基线
  5–8），无任何区域被覆盖 → AC-4 修订 2 在真实交付物上成立。Unity 日志条目按代录机读格式
  v1 独立解析：60 行、索引 1–60、逐层 20/0/0、15/0/0、15/0/0、10/0/0（类别）、颜色
  20/0/0、14/1/0、15/0/0、10/0/0、框 20/0/0、13/0/2、9/0/6、10/0/0，颜色错 = #27
  （S5 记录 `bus` / `gray` / `VERIFIED` / 双验证，与报告 §4 第 2 点并列陈述一致），框不确定 =
  {22, 31, 37, 43, 44, 47, 49, 50}，与报告 §4 表逐格相等。
- **停点输入并集复核（合同 §3 表 B「停点复核此前成功执行所读输入的并集」）**：
  `receipts/input-manifest.json` 五个阶段（inventory 164、panel-plan 2、panel 64、
  render-fix 3、audit-stats 64）各自 `equal: true`/`successful: true`；`union` 289 条重算：
  **287 条字节/SHA 与当前文件相等**（六件工件、151+7 分片、60 张归档原图、指令逐行文件、
  面板收据、重绘收据、60 张叠加图），**2 条不等**且都是合法变化：
  `docs/unity-test-log.md`（并集值来自 2026-09-11T04:13 的旧 stats 执行，其后辅助角色以提交
  「代录用户 60 张标签判定，修正条目内两处失效文字」改动了条目；当前 SHA 与最新 stats 收据
  `verdict_source` 相等）与 `docs/evidence/P1-ENG-ASSET-001-label-audit.md`（并集值来自 panel /
  render-fix 阶段的 PENDING 版，当前为 stats 写出的统计版）。原件零改动成立；并集复核结果与
  两条合法变化的解释**未出现在报告 §8**，随 F1 一并返工。
- **探针（副本内，临时目录，零写主树）**：(a) F1 红：`stage_stats` 在解析判定后、写出前
  改动 Unity 日志 → 仍成功写统计与成功收据，收据 `verdict_source.sha256` 等于**改动后**
  字节而非实际解析字节，`stages.audit-stats.before` 不含日志；(b) F2 红：生产 `stage_plan`
  重跑（清单 `overlay_sha256` 回到 `(pending)`）后 `stage_stats` 成功并把 `(pending)` 写进
  统计版清单；(c) F3 红：无指令逐行文件时 `stage_plan` 写出 `failure-panel-plan-*.json`，
  `reason: OUTPUT_PATH_FORBIDDEN`、`message: 指令逐行文件缺失…`；(d) F5 红：`panel_root`
  落禁写根且其下预置 `.staging-panel/keep.txt` 时，`stage_panels` 拒绝后 `finally` 删除了该
  文件与目录；(e) 夹具覆盖：`tests.test_eng_asset_inventory` 夹具 10 行的状态直方图 =
  UNIQUE_CLASS 4 / AMBIGUOUS_SAME_CLASS 1 / COLOR_UNVERIFIED 1 / WILDCARD_UNKNOWN_CLASS 3 /
  NOT_CLASS_VERIFIED 1，无 UNIQUE_CLASS_COLOR、UNIQUE_RELATION，布局车 `s5_entry=False` 0 辆（§4）。
- **依据列读法**：`BC-n` 读作 `AC-n`；C2 关注项被本轮核实的写 `BC-n`/`IN_SCOPE_NO_BC`，
  不写 `上游漏检`（核对轮已点名、未放过）；首轮无 `上轮漏检`；零真值/渲染红线触发，无
  `RED_LINE`。
- **计数**：本停点第 1 次 `REWORK_REQUIRED`（上限 2）；修复直接回本角色 `R2@K4`，不经
  核对轮（COORD-009；engineering-workflow §5）。设计退修 2、C 2/退回 1 不变。

## 1. 逐条 AC 核对

| 编号 | 结论 {满足, 不满足, 证据缺失} | 证据 | 理由 |
|---|---|---|---|
| AC-1（修订 1） | 不满足 | `inventory` 阶段 164 输入 before/after 逐条相等（收据 + 副本重跑 `ReconciliationTests` 2/2）；`reconcile` 计数与 151+7 分片 SHA 逐项相等（`fields.json` → `reconciliation`）；fail-closed 只写失败收据（`test_shard_hash_mismatch_writes_failure_receipt_only` + F3 探针）；并集 289 条 287 相等、2 条合法变化 | `stage_stats` 读取 Unity 日志却**不登记**为输入：`audit-stats` 阶段 64 条 before/after 不含日志，`verdict_source.sha256` 在清单与统计写出之后才现算（F1，探针 (a) 红）；AC-4 修订 3 逐字要求「源日志执行前后哈希核验纳入 AC-1；成功 stats 收据绑定实际读取的日志…字节/SHA」；报告 §8 未给出停点并集复核 |
| AC-2 | 满足 | `fields.json` 重新计数：101 辆逐辆有行、8 辆 `NO_S5_ENTRY`/`UNUSABLE`、`split_ok_frames` 逐 split 之和 3,305/20,617/11,231/0/22,277 = 57,430 = 指令行数；`FieldTableTests` 1/1；报告 §2 三栏 | 对账域定义、逐 split 车辆 OK 计数与行数相等、三栏回答均成立；夹具未覆盖 `NO_S5_ENTRY` 分支（§4 N1，非阻断，真实工件已覆盖） |
| AC-3（修订 1/2/3） | 满足 | 151 分片 57,430 行十一字段独立复算 0 不符；`NOT_CLASS_VERIFIED` 保护分支只在 `classify_uniqueness` 返回裸 `None` 时短路且不调用 `prospective_mother_eligible`（`inventory.py` 403–408）；`InstructionTests` 6/6（含两条通配机制）；摘要 `programs_by_split` 逐 split 与逐行文件相等 | 七值互斥按表 C 优先序由既有函数返回派生；`frame_world` 不传 `world_xz`/`route_side`（与 S7 形态一致）；母集复算域内 27,074 = 上界报告、已划分 17,337、差 9,737 全在未划分帧；`frozen_evaluation_set: false`；夹具无表 C 第 3/4 行样本（§4 N1） |
| AC-4（修订 1/2/3/4） | 不满足 | 抽样规则/配额/每对象上限/确定性（`test_stratum_priority_quota_and_per_object_cap`）；配额文件提交绑定（`panel-receipt.json` 指向首次提交、porcelain 空断言；`test_panel_generation_refuses_uncommitted_quota_file`）；60 张叠加图/原图字节三方相等；像素级核对 60/60 原帧完整、标题在帧外、框同步平移；机读格式 v1 严格解析（`test_verdict_table_format_mismatch_fails_closed` 14 例 + `test_stats_writes_only_failure_receipt_on_bad_verdict_table`）；统计逐层与本角色独立重算相等 | (i) 冻结清单 `overlay_sha256` 为 `""`/`(pending)` 时 `stage_stats` 不报差异并把该值写进成功统计（`label_panel.py` 1325 / 1355；F2，探针 (b) 红），违反修订 3「清单…当前 overlay_sha256 映射为图像身份依据」；(ii) 源日志未纳入执行前后核验（F1）。当前真实清单 60 项均为有效 SHA 且与实图相等，用户判定与统计本身不受影响，不要求重抽样或重新看图 |
| AC-5（修订 1） | 满足 | 报告 §5 全部 `file:line` 逐条对照副本代码：`track_loop.py` 336–347/110–129/230–231/251/354/985–993/65/560–561/943/969、`trackers.py` 42/45/61/463/474、`protocol.py` 22–35/39–58/61–71、`tracking_entry.py` 12–20/48/79、`sensor_protocol.py` 13–43、`build_catalog.py` 550–560/572/644、`tier1_lang.py` 304–312/338–342 均与正文陈述相符 | 10 条输入条件与 G-1…7 及归属停点成立；条件 3 已按 C1-6 改为「单帧时钟字段合法性，非跨帧保证」；箭头链声明为只读检查对象而非调用链；未运行任何跟踪器 |
| AC-6（修订 1/2/3） | 不满足 | 全量 diff 18 文件逐文件核对：实现者写入只含表 A A1/A2 与 `.gitignore` 单条规则，A3 七份为他角色提交；`WriteBoundaryTests` 2/2（含干净子进程 import 探针）；受版本控制 A2 最大 89,133 B ≤ 2 MB；两本地目录 2,152,022 B + 8,092,871 B = 10,244,893 B ≤ 32 MB；收据峰值 RSS 最大 382.8 MB ≤ 1 GB；全套日志 1152/9 ERROR 基线同集（实现者证据，本轮不重跑） | (i) §8 条件 4「候选 commit 已推送」不实（F4）；(ii) `PanelError.reason` 借用闭集 token，`stage_plan` 失败收据把「指令逐行文件缺失」记成 `OUTPUT_PATH_FORBIDDEN`（F3，探针 (c) 红）；(iii) §6 收据表/§6 测试摘要/§9 多处数字与当前收据/测试不符（F6，CLASS_3）。原件零写入、写出闭集、体积与零消耗边界本身成立 |

## 2. 读过的文件与测试

- 共享文档：`AGENTS.md`、`docs/current-status.md`（结构节、全部交接、Gate board 本项及
  `COORD-010` 行、2026-09-08…11 本项全部 Log）、`docs/collaboration-workflow.md` §4.3/§4.3.1/
  §4.3.3/§4.4、`docs/engineering-workflow.md` 全文、`docs/roles/review.md`、`docs/reviews/README.md`、
  提案全文（§1–§8、待裁定与十二条修订、代录机读格式 v1、核对表 C2@K4、决策记录）、账本
  2026-09-08 本项四条、`docs/implementation-status.md`「工程继承清单」、Unity 日志条目
  `UT-P1-ENG-ASSET-001-label-audit` 全文。
- 实现（副本内全文）：`tools/eng_asset/__init__.py`、`receipts.py`、`inventory.py`、
  `label_panel.py`；上游只读依据 `tools/dist_data/build_catalog.py` 537–720（`FrameWorld`、
  `frame_world`、`_unique_reference_specs`、`minimal_program_with_reference`、
  `prospective_mother_eligible`）、`tier1_lang.py`（`SceneObject`、`render`、`canonical_bytes`、
  `_noun_conflicts`/`_noun_satisfies`、关系执行 304–342）、`contract.py`（`MOTHER_USAGE_CLASSES`、
  `RELATION_TYPES`、`DYNAMIC_TARGET_REFERABLE`）；AC-5 指向的 `controller/track_loop.py`、
  `trackers.py`、`protocol.py`、`tracking_entry.py`、`sensor_protocol.py` 相应行。
- 测试（全文）：`tests/test_eng_asset_inventory.py`（11 例）、`tests/test_eng_asset_label_panel.py`
  （15 例）。证据：五份 `docs/evidence/P1-ENG-ASSET-001-*`；本地收据 `input-manifest.json`、
  三份 `run-inventory-*`、`run-panel-plan-*`、三份 `run-panel-*`、`run-relocate-*`、两份
  `run-render-fix-*`、两份 `run-stats-*`、`failure-render-fix-*`、`panel-receipt.json`；
  `outputs/eng-asset/P1-ENG-ASSET-001/panel/` 60 + 60 张 jpg；`runtime/dist-data/*/attempt-2`
  六件工件与 158 个分片（只读）。

## 3. Findings

### Blocking

#### F1（CLASS_2，依据 `BC-1`）— `stage_stats` 不把 Unity 日志登记为输入，成功收据事后取哈希

- **依据条款**：`AC-1`（修订 1：每次执行清单「本次实际读取的每个文件」执行前后逐条相等）；
  `AC-4` 修订 3 代录机读格式 v1 末条「源日志执行前后哈希核验纳入 AC-1；成功 stats 收据绑定
  实际读取的日志与清单字节/SHA」；C2-P1 主张经本轮核实成立。
- **位置**：`tools/eng_asset/label_panel.py` `stage_stats`：1348 行 `read_unity_verdicts(log_path, …)`
  读日志但从未 `manifest.record(log_path, …)`；1358–1359 行 `recompute()/diff()` 只覆盖已登记的
  64 条（指令逐行、S5、面板收据、重绘收据、60 张叠加图）；1392–1402 行在 `save_input_manifest`
  与清单写出**之后**才 `sha256_file(log_path)` 写入 `verdict_source`。真实 `input-manifest.json`
  `stages.audit-stats.before` 64 条不含 `docs/unity-test-log.md`（报告 §9 C1-5 行「该阶段不变输入
  64 条（指令逐行、S5 目录、Unity 日志、…）」与实际不符）。
- **事实（探针 (a)）**：在解析之后、写出之前改动日志 → `stage_stats` 仍成功，统计取自旧字节，
  成功收据 `verdict_source.sha256` 等于改动后字节；`stages.audit-stats.before` 无日志。现有
  `test_stats_fails_closed_when_input_changes_midrun` 改动的是指令文件，
  `test_stats_success_binds_read_manifest_and_written_output` 未断言日志在 before/after 中，
  故绿记录不覆盖本退化。并集复核因此也把日志留在旧 stats 执行的值上（§0）。
- **范围判据**：触发状态由 AC-1 修订 1 与 AC-4 修订 3 逐字点名，生产入口 `stats` 直接可达
  → 可达，有 AC 覆盖 → `BC-1`，阻断。
- **闭合要求**：(1) 日志在读取点登记进 `manifest`（与其它不变输入同一 before/after 与
  `union`），`verdict_source` 取登记条目（实际解析的字节/SHA）而非事后现算；(2) 具名回归走
  **生产路径**：`stage_stats` 在解析后、写出前改动日志 → `InputHashChanged`、只写
  `failure-stats-*`、清单/既有统计原样；成功用例断言 `stages.audit-stats.before` 含日志且
  `verdict_source.sha256` 与登记值相等。夹具须由生产写入器产出（`stage_plan` /
  `stage_panels`（`draw_panel` 可如 C1-1 用例桩替）/ `stage_render_fix` 或 `ReceiptWriter`），
  或消费已归档真实收据的字节副本，不得像 `_legal_env` 那样手写 `panel-receipt.json` /
  `run-render-fix-*.json`（COORD-007 R3 (1)）；修前必失败，R2 红绿核实。(3) 报告 §8 补写停点
  并集复核：289 条中 287 相等、2 条（日志、清单）为合法变化及其来源，不回改历史 before/after。
  修复后重跑 stats 使 `union` 的日志条目与当前字节一致；**不重抽样、不重新看图、不改用户判定**。

#### F2（CLASS_2，依据 `BC-4`）— 冻结清单缺少图像身份（`(pending)`/空）时统计照常成功

- **依据条款**：`AC-4` 修订 3「清单的 panel_index 到 frame_id/object_id/当前 overlay_sha256
  映射为图像身份依据；正式看图开始至统计结束不改该映射」、修订 2「更新清单所指当前叠加图」；
  C2-P4 主张经本轮核实成立。
- **位置**：`tools/eng_asset/label_panel.py` 1325 行
  `if item["overlay_sha256"] not in ("", PENDING) and digest != item["overlay_sha256"]` 显式放过
  空值与 `(pending)`；1355 行 `overlays = {…: item["overlay_sha256"]}` 再把该占位值写进成功
  统计版清单；`frozen_identity_mismatches` 不检查该列。
- **事实（探针 (b)）**：生产 `stage_plan` 重跑把清单 §3 回到 `(pending)`（叠加图仍在盘上）→
  `stage_stats` 成功、写成功收据，写出的清单 §3 仍以 `(pending)` 充当 60 张的身份。真实清单
  当前 60 项均为有效 SHA，本缺陷不影响已取得的判定与统计。
- **范围判据**：`plan` → `stats` 均为生产 CLI 入口，可从已归档派生工件产生 → 可达，有 AC
  覆盖 → `BC-4`，阻断。
- **闭合要求**：冻结清单任一行 `overlay_sha256` 非 64 位十六进制即在读判定之前 fail-closed
  （沿用 `INPUT_HASH_CHANGED` 失败收据，problem 记缺失身份的 `panel_index`），不写统计；具名
  回归走生产路径（`stage_plan` 后清单为 `(pending)`、叠加图存在 → `stage_stats` 拒绝、无
  `run-stats-*`、清单原样），修前必失败；`test_stats_refuses_when_overlay_bytes_differ_from_manifest`
  保留。

#### F3（CLASS_2，依据 `IN_SCOPE_NO_BC`）— `PanelError` 借用闭集 token，`stage_plan` 失败收据错标原因

- **依据条款**：合同 §3 表 B 末行失败原因闭集 {`MANIFEST_COUNT_MISMATCH`, `SHARD_HASH_MISMATCH`,
  `INPUT_HASH_CHANGED`, `OUTPUT_PATH_FORBIDDEN`, `QUOTA_FILE_DIRTY`} + AC-4 修订 3 追加
  `VERDICT_FORMAT_MISMATCH`；`AC-1`「只写 receipts/failure-*.json」的 fail-closed 语义依赖
  `reason` 如实归因。无 AC 直接约束「原因 token 必须与真实病因一致」→ `IN_SCOPE_NO_BC`。
- **位置**：`tools/eng_asset/label_panel.py` 90–93 行 `class PanelError(receipts.EngAssetError):
  reason = "OUTPUT_PATH_FORBIDDEN"`（docstring 自述「不属失败收据闭集原因」）；`stage_plan`
  817–822 行 `except EngAssetError` 后按 `exc.reason in FAILURE_REASONS` 无条件写失败收据，
  而 `stage_panels`（967）/`stage_render_fix`（1245）用 `isinstance` 过滤掉了 `PanelError`。
- **事实（探针 (c)）**：无指令逐行文件时 `python3 -m tools.eng_asset.label_panel plan` 写出
  `failure-panel-plan-<utc>.json`，`reason: OUTPUT_PATH_FORBIDDEN`、`message: 指令逐行文件缺失…`；
  同一路径还覆盖「抽样行数超过面板上限」等 `PanelError`。终态名错标会让操作员/停点核对把
  「先跑 plan 后跑 inventory」的次序错误当成原件保护事件。
- **范围判据**：生产 CLI `plan` 在 `inventory run` 之前执行即触发 → 可达；阻断。
- **闭合要求**：`PanelError` 不得携带闭集内的 `reason`（或改为不继承 `EngAssetError`），
  `stage_plan` 的失败收据只为闭集内真实原因写出（与其它阶段的过滤一致）；若实现者认为这类
  前置失败也需要收据，按 AC-6 修订 2 路由写报告 §7 请接受角色追加 token，本角色不代加。具名
  回归：`stage_plan` 缺指令文件 → 抛错且**不**出现任何 `reason` 在闭集内却与病因不符的失败
  收据；修前必失败。

#### F4（CLASS_2，依据 `IN_SCOPE_NO_BC`；`NOT_MECHANIZABLE`）— 自证「候选 commit 已推送」不实

- **依据条款**：AGENTS.md「复核强制停点」「到达停点后必须更新状态、提交并推送候选版本」；
  workflow §4.3.1 条件 4；报告 §8 条件 4「候选 commit 已推送」与状态板/核对表「推送声明待
  核实」。无 AC 覆盖 → `IN_SCOPE_NO_BC`。
- **事实**：复核时 `git ls-remote --heads origin main` = `a108a1eb17931d2cfa0250cafec280f2e1e1d1bd`
  （2026-09-09「显示确认通过」提交），本地 `main` 领先 5 个提交：两项统计偏差修复、辅助角色
  代录、C1@K4、C1 六项修复（候选）、C2@K4。候选与用户判定代录均**未推送**。§4.3.1 四项按字面
  成立，故不给 `REVIEW_BLOCKED`；但该句会让接手角色不再推送，属驱动操作员动作的失效文字。
- **范围判据**：停点义务，可达；阻断（修复代价为一次推送 + 一句改正）。
- **闭合要求**：推送候选与返工提交；报告 §8 条件 4 改为不手写 SHA 的可核实表述（例如
  「候选已本地提交并推送，推送状态由 `git status -sb` 与 `git ls-remote --heads origin main`
  运行时核实」）。仓库内无法写断言远端状态的测试 → `NOT_MECHANIZABLE`，R2 以 `git ls-remote`
  定点复看。

### Non-blocking

#### F5（CLASS_2，依据 `SCOPE_GAP`；非阻断，路由接受角色）— 拒绝禁写根之后的 `finally` 清理仍会删除禁写根下的目录

- **依据条款**：合同 §3「禁写闭集（原件保护）：…落入上述任一根即拒绝运行并写失败收据」、
  AC-6「原件零写入」；C2-P3 主张经本轮核实成立。
- **位置**：`tools/eng_asset/label_panel.py` `stage_panels` 867–869 行对 `panel_dir` 做包含
  检查并抛 `OutputPathForbidden`；970–975 行 `finally` 用**未经检查**的
  `resolve_panel_dir(repo_root, panel_root).parent / ".staging-panel"` 直接 `_clear_directory` +
  `rmdir`。另：913–917 行先把 120 张图片发布到 `panel_dir`，934 行才检查 `local /
  panel-receipt.json` 的目的地；`stage_plan`/`stage_render_fix`/`stage_stats` 不像
  `inventory.run`（722–723 行）那样在任何写入前检查 `local_root` 自身。
- **事实（探针 (d)）**：`panel_root` 落在 `runtime/dist-data/…` 且其下预置 `.staging-panel/keep.txt`
  → 抛 `OutputPathForbidden`、写失败收据，但 `finally` 删除了 `keep.txt` 与目录。
- **范围判据**：触发需要调用方经 Python API 显式传入禁写根，且该根下已存在 `.staging-panel`；
  生产 CLI 三个入口只用固定缺省根（`outputs/eng-asset/<work-id>`、`runtime/eng-asset/<work-id>`），
  从已归档工件不可产生 → 不可达 → `SCOPE_GAP`，非阻断，交接受角色裁定「范围内必修」或记入
  `docs/implementation-status.md`「范围外已知缺陷」账本。首轮，非 `上轮漏检`，不写
  `blocks_consuming_gate`。
- **建议闭合（若裁定范围内）**：`finally` 只清理本次实际创建的 staging 路径（在 assert 通过后
  绑定变量），发布前对 `local` 与 `panel_dir` 全部目的地先整体检查；具名回归复现探针 (d)。

#### F6（CLASS_3，依据 `IN_SCOPE_NO_BC`；证据叙述计数）— 报告数字与当前收据/测试不符（逐字替换补丁）

均不驱动工具或操作员动作（阈值 1 GB / 2 MB / 32 MB 远未触及，结论不变）。由实现角色在下一次
提交应用，本角色一行不改；R2 定点复看。补丁以「旧 →」「新 →」成对给出，围栏内为逐字文本。

1. `docs/evidence/P1-ENG-ASSET-001-inventory.md` §6 执行收据表（当前收据：`run-inventory-20260911T061929Z` /
   `run-panel-plan-20260909T001647Z` / `run-panel-20260909T002902Z` / `run-relocate-20260909T031939Z` /
   `run-render-fix-20260909T034849Z` / `run-stats-20260911T062609Z`）：

```text
旧 → | `inventory`（AC-1/2/3） | 65.1 s | 69.3 MB | 指令逐行 57,430 行 / 1.86 MB（本地 gz）、`fields.json` 89 KB、`instructions-summary.json` 43 KB |
新 → | `inventory`（AC-1/2/3） | 65.1 s | 69.2 MB | 指令逐行 57,430 行 / 1,716,404 B（本地 gz）、`fields.json` 89,133 B、`instructions-summary.json` 76,111 B |
旧 → | `panel-plan`（AC-4 抽样） | < 2 s | 96 MB | `label-audit.md` |
新 → | `panel-plan`（AC-4 抽样） | 0.3 s | 185.8 MB | `label-audit.md` |
旧 → | `panel`（AC-4 面板） | 1.0 s | 377 MB（加载 S1 索引） | 60 张面板 3.6 MB + 60 张原图副本 |
新 → | `panel`（AC-4 面板） | 0.9 s | 382.8 MB（加载 S1 索引；当前收据为第三次生成，前两次 376.9 / 382.3 MB） | 60 张面板 3.6 MB + 60 张原图副本 |
旧 → | `relocate`（AC-4 修订 1 迁移） | < 2 s | 30 MB |
新 → | `relocate`（AC-4 修订 1 迁移） | 0.1 s | 26.1 MB |
旧 → | `render-fix`（AC-4 修订 2 重绘） | < 3 s | 62 MB |
新 → | `render-fix`（AC-4 修订 2 重绘） | 0.6 s | 183.9 MB |
```

   `relocate`/`render-fix` 两行只替换行首至第三列，第四列不变；在 `render-fix` 行之后**新增**一行：

```text
| `stats`（AC-4 修订 3 统计） | 0.3 s | 185.9 MB | `label-audit.md` §5 统计块；收据绑定日志/清单快照（F1 返工后以重跑收据为准） |
```

   同节正文两处：

```text
旧 → 峰值 RSS 377 MB ≤ 1 GB 规划上限；受版本控制的 A2 文件各 ≤ 2 MB（最大 89 KB）；
新 → 峰值 RSS 382.8 MB ≤ 1 GB 规划上限；受版本控制的 A2 文件各 ≤ 2 MB（最大 89,133 B）；
旧 → 两个本地派生目录合计 10.1 MB ≤ 32 MB（AC-6 修订 1 口径：`runtime/eng-asset/P1-ENG-ASSET-001/` 2.0 MB
新 → 两个本地派生目录合计 10,244,893 B（≈ 10.2 MB）≤ 32 MB（AC-6 修订 1 口径：`runtime/eng-asset/P1-ENG-ASSET-001/` 2,152,022 B
旧 → + `outputs/eng-asset/P1-ENG-ASSET-001/` 8.1 MB；重绘后叠加图因 4:4:4 与 quality=95 变大）。
新 → + `outputs/eng-asset/P1-ENG-ASSET-001/` 8,092,871 B，含 Finder 生成的两个 `.DS_Store`；重绘后叠加图因 4:4:4 与 quality=95 变大）。
```

2. 同文件 §6 测试摘要：

```text
旧 → - Focused：`tests.test_eng_asset_inventory` 9 例、`tests.test_eng_asset_label_panel` 3 例，全通过。
新 → - Focused：`tests.test_eng_asset_inventory` 11 例、`tests.test_eng_asset_label_panel` 15 例（系统 python3 上 1 例 Pillow 用例 skip，另在 `.venv-yoloe` 实跑），全通过。
```

3. 同文件 §9 (b)：

```text
旧 → Pillow 实跑记录同步为 11 例
新 → Pillow 实跑记录同步为 15 例
```

4. `tests/test_eng_asset_inventory.py` 158 行注释（夹具真实语义：红车因灰车颜色通配而不唯一）：

```text
旧 →     # 同类两车、目标颜色已验证：class+color 唯一；灰车颜色未验证。
新 →     # 同类两车：红车颜色已验证但灰车颜色未验证（通配冲突）——红车判 AMBIGUOUS_SAME_CLASS、灰车判 COLOR_UNVERIFIED（表 C 第 6/7 行）。
```

#### F7（CLASS_3，依据 `IN_SCOPE_NO_BC`；已执行步骤的时态）— 报告两处仍写成尚未发生

1. `docs/evidence/P1-ENG-ASSET-001-inventory.md` §4 末段（两行）：

```text
旧 → **待接受侧定点确认**：AC-4 修订 2 要求由接受侧确认 20/42 号原帧完整且框对应原像素后，才交用户
旧 → 一次看图；该确认只验证显示，不替代标签判定或 C/R。
新 → **接受侧定点确认已完成（2026-09-09）**：接受侧已确认 20/42 号原帧完整且框对应原像素，
新 → 用户一次看图随后完成（统计见上）；该确认只验证显示，不替代标签判定或 C/R。
```

2. 同文件 §8 首段（两行）：

```text
旧 → 本节是交接受角色核对轮 `C1@K4` 前的实现者自证。**未经核对轮与独立复核，本项仍是
旧 → `IMPLEMENTED`，不是 `DONE`**；`UNITY_NA` 仍须复核角色在 `docs/reviews/P1-ENG-ASSET-001.md` 附议。
新 → 本节是 `K4` 停点的实现者自证（`C1@K4`/`C2@K4` 已完成，候选交独立复核）。**未经独立复核通过，本项仍是
新 → `IMPLEMENTED`，不是 `DONE`**；`UNITY_NA` 已由复核角色在 `docs/reviews/P1-ENG-ASSET-001.md` R1@K4 附议（仅本项）。
```

## 4. 缺失或薄弱的测试（非阻断记录）

- **N1 夹具覆盖**：`tests.test_eng_asset_inventory` 夹具（探针 (e)）没有 `UNIQUE_CLASS_COLOR`、
  `UNIQUE_RELATION` 行，也没有无 S5 条目的布局车，故 AC-3 具名测试
  `test_status_derivation_matches_minimal_program_on_production_slice` 未在夹具上验证表 C 第 3/4
  行，AC-2 具名测试断言 `all(row["s5_entry"])` 从未走 `fields_document` 的 `NO_S5_ENTRY`/
  `UNUSABLE` 分支。真实工件（57,430 行 0 不符、8 辆 `UNUSABLE`）已由本轮覆盖，不阻断；建议
  R2 顺带补两帧夹具（一辆带已验证颜色的同类第二车；一辆不在 S5 的布局车进 layout 分区）。
- **N2 夹具来源**：`_legal_env` 手写 `panel-receipt.json` / `run-render-fix-*.json` / 叠加图字节，
  不是生产写入器产物；作为 C 轮回交的闭合可以接受，但 F1/F2 的阻断闭合回归须满足
  COORD-007 R3 (1)。
- **N3 非 `EngAssetError` 异常**：`inventory.json`/清单缺失（`FileNotFoundError`）、上游 `TypeError`
  等不写失败收据，但也不发布任何工件（staging 在 `finally` 清理）→ 与 fail-closed 一致，只作
  披露。`stage_panels` 在输出路径检查之前先加载 50 MB `inventory.json`（861–865 行），只是效率。
- **N4 体量口径**：`outputs/eng-asset/P1-ENG-ASSET-001/` 内有 Finder 生成的两个 `.DS_Store`
  （16,392 B）计入 32 MB 预算，无害。
- **N5 环境**：`.claude/worktrees/` 下另有两个非本会话创建的 detached 副本
  （`clever-brattain-6de4d8`、`epic-morse-0d4596`），本轮未触碰。

## 5. 交回实现角色的动作

1. F1：`stage_stats` 登记 Unity 日志为不变输入并让 `verdict_source` 取登记值；生产路径具名
   回归（修前红）；报告 §8 补停点并集复核与两条合法变化说明；重跑 stats 刷新 `union`。
2. F2：冻结清单缺失/占位 `overlay_sha256` 即 fail-closed；生产路径具名回归（修前红）。
3. F3：`PanelError` 不携带闭集 `reason`，`stage_plan` 不为闭集外病因写闭集原因收据；具名回归。
4. F4：推送候选与返工提交；改正报告 §8 条件 4 文字。
5. 应用 F6/F7 的逐字补丁；F5 交接受角色裁定（范围内必修则一并修复并补回归）。
6. 只允许触及表 A A1/A2：`tools/eng_asset/label_panel.py`、`tools/eng_asset/receipts.py`、两份
   `tests/test_eng_asset_*.py`、报告与由工具重写的 A2 文件；**不重抽样、不重绘、不改用户判定
   与 Unity 日志、不动 `tools/dist_data/`**。修后按 workflow §4.3.1 自证，直接交 `R2@K4`，
   不经核对轮；第 2 次 `REWORK_REQUIRED` 后未闭集冻结、轮 3 终局。

## `UNITY_NA` 附议

**附议**（仅限本 work ID 的 `K4` 候选）：全量 diff 证实 `controller/`、`Assets/`、`config/`、
`ProjectSettings/`、`Packages/` 零字节改动，工具不 import 运行时模块（干净子进程探针），
只读取已归档帧与 attempt-2 工件，零 Play/scenario/session/run/attempt 身份，不改变任何运行时
行为；AC-4 的用户看图是 `OFFLINE_VISUAL_CHECK`，不是 Unity 验证，也不冒充 `UNITY_PASSED`。
本附议不延伸到 `COORD-010` 迁移批（其独立复核与 `UNITY_NA` 附议仍缺），也不构成 `DONE`
（仍需 `R<n>@K4` 通过）。

## 6. 再复核结果

待 `R2@K4`：核实 F1–F4 的修前红/修后绿（F4 以 `git ls-remote` 定点复看）、F6/F7 补丁已应用、
F5 的接受角色裁定；新阻断只来自修复触及行（相对本轮 `round_candidate`）上的 CLASS_1/2、旧
finding 闭合失败与 `RED_LINE`。

## R2@K4 — 2026-09-11

Reviewer/role: 复核角色 / independent verification（新鲜上下文会话，Fable 池；档位不低于实现者）
Workflow: engineering-v1（同 R1；按 `docs/engineering-workflow.md` §5/§6 与 `docs/roles/review.md`「工程轨道」节执行）
Round: R2@K4
Date: 2026-09-11
Implementation snapshot: 候选 = 状态板 Active handoffs `P1-ENG-ASSET-001` 行（`READY_FOR_R2_K4`）指向的
`R1@K4` 返工提交（主题「P1-ENG-ASSET-001 R1@K4 返工：F1–F5 修复 + F6/F7 补丁 + N1/N2 夹具，交 R2@K4」）。
开工时主树 HEAD 即该提交；复核期间另一会话提交了协调批次 COORD-011（只改三份规则文件、账本、状态板、
修订史与规则存档，未触及本项任何候选文件），候选不变，本轮复核提交落在其后。
round_candidate: 9ba6ae80e88a4457b01ef02de092f8825c5afecd
Verdict: PASS_WITH_NOTES
passed_candidate: 9ba6ae80e88a4457b01ef02de092f8825c5afecd

### 0. 候选、修复触及行与方法

- **修复触及行**（COORD-009 (b)，基线 = R1 `round_candidate`）：`git diff <R1 候选>..<候选>` 共 6 个文件
  +349/−110：`tools/eng_asset/label_panel.py`（`PanelError` 改继承 `RuntimeError` 且不带 `reason`；`stage_plan`
  失败收据改按 `isinstance` 过滤；`stage_panels`/`stage_render_fix` 新增 `created_staging` 变量、`local` 根前置
  检查与发布前对 `panel_dir`/`original_dir`/`panel-receipt.json` 的整体检查；`stage_stats` 对清单 `overlay_sha256`
  非 64 位十六进制即记 `MANIFEST_OVERLAY_SHA_MISSING_OR_PLACEHOLDER`、在解析前 `manifest.record(log_path)` 并让
  `verdict_source` 取登记条目）、`tests/test_eng_asset_label_panel.py`（`_legal_env` 改为生产 `stage_plan` →
  `stage_panels` → `stage_render_fix` 产出，仅绘制与 git 提交门桩替；4 条新回归；成功用例加 F1 断言；两条既有
  用例随夹具调整）、`tests/test_eng_asset_inventory.py`（N1 夹具：两帧、两辆已验证颜色车、布局分区加一辆无 S5
  条目车；AC-2 具名测试断言 `NO_S5_ENTRY`/`UNUSABLE`）、报告 §4/§6/§8/§9/§10、`tests.log`、状态板。
  `tools/eng_asset/receipts.py`/`inventory.py`/`__init__.py` 未改（blob 与 R1 相同）；`controller/`、`Assets/`、
  `config/`、`tools/dist_data/`、`ProjectSettings/`、`Packages/` 零字节改动；未触及 Play 治理门文件。修复触及
  PLAY_GOVERNING（`tools/`、`tests/`）→ 开轮（COORD-007 R1）。
- **全量 diff**（相对开工基线 = `tools/eng_asset/inventory.py` 首次引入提交的父提交，同 R1）：19 个文件
  +11,861/−23（R1 的 18 文件 + 本复核文件），只用于核实声明范围与红绿，不作本轮阻断范围：实现者写入仍只含表 A
  A1/A2、`.gitignore` 单条规则与状态板（角色权限内）；A3 七份为他角色提交。
- **副本与重跑**：一次性副本 `git worktree add --detach .claude/worktrees/review-P1-ENG-ASSET-001 <候选>`；读码、
  重跑、探针全在副本；主树 `runtime/`、`outputs/`、`docs/unity-test-log.md` 只按绝对路径**只读**核对，未运行任何
  会写主树的阶段。focused：系统 `python3` 3.14.6 `python3 -m unittest tests.test_eng_asset_inventory
  tests.test_eng_asset_label_panel` → `Ran 30 tests … OK (skipped=1)`；`.venv-yoloe/bin/python`（3.12.13，
  Pillow 12.3.0）脚本模式 `tests/test_eng_asset_label_panel.py` → `Ran 19 tests … OK`（0 skip，AC-4 修订 2 像素
  用例实跑）、`tests/test_eng_asset_inventory.py` → `Ran 11 tests … OK`（该 venv 下模块模式被 site-packages 的
  同名 `tests` 包遮蔽，与 R1 同用脚本模式）。输出写会话 scratchpad `r2-focused-*.log`，只回显摘要。测试树哈希：
  `HEAD:tests` = `c86dead154fbf3279f2d9f666f17148a8891c9c8`，`HEAD:tools` = `dbe3e72e86db9b734de20c57b128881767719529`，
  `HEAD:tools/eng_asset` = `bf1dad941969b2e7e8f8ea4b65e595bbb1649d90`；触及源文件 blob：`label_panel.py`
  `4376b1c6…`、`test_eng_asset_label_panel.py` `983a68e3…`、`test_eng_asset_inventory.py` `dc240bf0…`；未改文件
  blob 与 R1 相同（`inventory.py` `f0be9ab3…`、`receipts.py` `6e85c3e9…`）。全套自动测试是实现者停点义务
  （`tests.log`：`Ran 1156 tests`、`FAILED (errors=9, skipped=21)`，9 个 ERROR 与 R1 所见同集；附 Pillow 实跑
  `Ran 19 tests … OK`），本轮不重跑全套。
- **红/绿（COORD-007 R3 (2)）**：在副本把 `tools/eng_asset/label_panel.py` 整体换回 R1 候选版本（blob 回到
  `7644b8d5…`），只跑 5 条具名用例 → `Ran 5 tests … FAILED (failures=5)`：
  `test_stats_fails_closed_when_verdict_log_changes_midrun`（F1）、
  `test_stats_refuses_placeholder_overlay_identity_in_manifest`（F2）、
  `test_plan_failure_does_not_write_closed_set_failure_receipt`（F3）、
  `test_forbidden_panel_root_is_refused_without_touching_its_contents`（F5）、
  `test_stats_success_binds_read_manifest_and_written_output`（F1 成功路径断言）全部 FAIL；`git checkout --`
  恢复（blob 回到 `4376b1c6…`，`git status --porcelain` 空）后同 5 条 → `Ran 5 tests … OK`。实现者报告的
  「4 条修前全失败」与此一致（第 5 条是被改的既有成功用例）。夹具来源：全部派生工件由生产写入器产出
  （`ArtifactStore`、`inventory._write_instructions`、`stage_plan`、`stage_panels`、`stage_render_fix`），只有
  `draw_panel` 与 `quota_file_commit` 桩替，各自另有具名回归 → 满足 COORD-007 R3 (1)。
- **F4 定点复看（`NOT_MECHANIZABLE`）**：主树 `git status -sb` 首行 `## main...origin/main`（无 ahead/behind），
  `git ls-remote origin refs/heads/main` = 候选 SHA（开工与本轮写入前各核一次）；候选、辅助角色代录与 R1 复核
  提交均已在远端。（COORD-011 提交在本轮写入时尚未推送，不属本项候选。）
- **真实工件复核（主树只读）**：`receipts/input-manifest.json` 五阶段——`inventory` 164、`panel-plan` 2、
  `panel` 64、`render-fix` 3（`utc` 均为旧值，历史 before/after 未回改）、`audit-stats` **65** 条含
  `docs/unity-test-log.md`（`equal: true` / `successful: true`，`utc` 为本次返工重跑）；`union` 289 条按当前字节
  重算 **288 相等、1 不等**——唯一不等是 `docs/evidence/P1-ENG-ASSET-001-label-audit.md`（并集值 18,393 B 为
  panel/render-fix 阶段读到的 PENDING 版，当前 18,963 B 为 stats 输出），与报告 §8 逐字一致；日志条目已与当前
  字节相等。最新 `run-stats-*` 收据 `verdict_source` = {`path`, `bytes` 356,965, `sha256` `b45b1970…`,
  `rows` 60, 来源注记}，与 `stages.audit-stats.before` 的日志条目及当前日志字节三方相等；其 `outputs[0]`
  SHA `3590539b…` 与工作树、候选提交中的 `label-audit.md` 三方相等（重跑输出逐字节等于已提交版，故该文件不在
  返工 diff 中）。60 张叠加图 SHA 与清单 §3 及最新 render-fix 收据 `after` 逐张相等（60/60）；60 张原图副本与
  `panel-receipt.json` `source_sha256` 逐张相等（60/60）；`panel-receipt.json`、render-fix、relocate 收据的 `utc`
  与 R1 所见相同 → 未重抽样、未重绘、未增加看图。`docs/unity-test-log.md` 相对候选零改动（用户判定未动）。
  两本地目录 2,156,719 + 8,092,871 = 10,249,590 B ≤ 32 MB（比报告 §6 多 4,697 B = 新 stats 收据 4,181 B +
  清单文件增长，见 F9）；stats 峰值 RSS 185.9 MB，全部收据最大仍 382.8 MB ≤ 1 GB；`receipts/` 仅有的失败收据
  仍是 2026-09-09 的 `failure-render-fix-*`，无任何错标 `OUTPUT_PATH_FORBIDDEN` 的 plan 收据。
- **探针（副本内，临时目录）**：(a) 用生产 `inventory.run` 跑 `tests.test_eng_asset_inventory` 夹具：15 行，
  七值直方图 `UNIQUE_CLASS` 5 / `UNIQUE_CLASS_COLOR` 2 / `UNIQUE_RELATION` 2 / `COLOR_UNVERIFIED` 1 /
  `AMBIGUOUS_SAME_CLASS` 1 / `WILDCARD_UNKNOWN_CLASS` 3 / `NOT_CLASS_VERIFIED` 1，与报告 §10 N1 行逐值相等；
  `fields.json` 8 辆布局车含 1 辆 `s5_entry=false` → `UNUSABLE`/`NO_S5_ENTRY`（AC-2 具名测试现真正走该分支）。
  (b) F8：生产 `stage_stats` 以不存在的 `unity_log` 路径运行——候选抛裸 `FileNotFoundError`、无 `failure-stats-*`；
  换回 R1 候选源码同一探针 → `VerdictFormatMismatch`（`ENTRY_LOG_MISSING`）并写 `failure-stats-*`。
- **依据列读法**：同 R1（`BC-n` 读作 `AC-n`）。本轮新阻断只来自修复触及行上的 CLASS_1/2、旧 finding 闭合失败、
  `RED_LINE`；无 `上轮漏检` CLASS_1，无 `blocks_consuming_gate` 行（本停点无消耗性交接，R1 亦无 block）。零真值/
  渲染红线。
- **计数**：R 2（本停点 `REWORK_REQUIRED` 已用 1/2，本轮通过）；D 退修 2、C 2/退回 1 不变。

### 1. 旧 finding 闭合核实

| Finding | R2 结论 | 依据 |
|---|---|---|
| F1（CLASS_2，`BC-1`） | **闭合** | `stage_stats` 在 `read_unity_verdicts` 之前 `manifest.record(log_path)`，写出前 `recompute()/diff()` 覆盖该条目，`verdict_source` 取 `log_entry.path/bytes/sha256`（副本代码）；红/绿 §0；真实 `audit-stats` 65 条含日志 `equal: true`，收据、登记条目、当前日志三方相等；报告 §8 已补停点并集复核（289 条、288 相等、唯一不等为合法输出清单及其来源），并写明历史 before/after 未回改——R1 闭合要求 (1)(2)(3) 全部成立 |
| F2（CLASS_2，`BC-4`） | **闭合** | 清单任一行 `overlay_sha256` 非 64 位十六进制（含 `""`/`(pending)`）即记 `MANIFEST_OVERLAY_SHA_MISSING_OR_PLACEHOLDER` 并 fail-closed（`INPUT_HASH_CHANGED` 失败收据，problem 记 `panel_index`，不写统计、清单原样）；回归走生产 `stage_plan` 重跑制造占位；红/绿 §0；`test_stats_refuses_when_overlay_bytes_differ_from_manifest` 保留；真实清单 60 项均为有效 SHA |
| F3（CLASS_2，`IN_SCOPE_NO_BC`） | **闭合** | `PanelError(RuntimeError)` 不继承 `EngAssetError`、无 `reason`；六处 raise 点（超上限、缺种子/配额行、git 失败、缺 Pillow、缺指令文件、缺归档帧/原图副本）均只抛错；`stage_plan` 与 panel/render-fix 同口径按 `isinstance` 过滤；回归断言无新增失败收据且 `PanelError` 不带闭集 token；红/绿 §0；未自行扩大闭集 |
| F4（CLASS_2，`IN_SCOPE_NO_BC`，`NOT_MECHANIZABLE`） | **闭合（定点复看）** | 远端 `main` = 候选 SHA（§0）；报告 §8 条件 4 改为「候选已本地提交并推送，推送状态由 `git status -sb` 与 `git ls-remote --heads origin main` 运行时核实（不手写 SHA）」并给 `cmd:` 指针 |
| F5（CLASS_2，`SCOPE_GAP`，非阻断） | **修复核实；处置权仍在接受角色** | `created_staging` 只在路径检查通过后绑定、`finally` 只清理本次实际创建者；`stage_panels`/`stage_render_fix` 在任何写入前检查 `local`，发布前整体检查 `panel_dir`/`original_dir`/`panel-receipt.json`；回归复现 R1 探针 (d)（禁写根下预置 `.staging-panel/keep.txt` 原样保留）；红/绿 §0。残留：`stage_plan`/`stage_stats` 未加同样的 `local` 前置检查，但两者的每一次写出都经 `ReceiptWriter._write_json` → `assert_output_allowed`，不存在未受保护的写出，故报告 §10 F5 行「`local` 收据根在任何写入前检查」仅对 panels/render-fix 逐字成立。接受角色按 workflow §4.6 裁定「范围内必修（已修）」或记账 |
| F6（CLASS_3） | **已应用** | §6 收据表五行、两处体量口径、Focused 计数、§9 (b)、夹具注释均已替换；计数按返工后实际改为 19 例（正确，非逐字 15）；`stats` 行插在 `render-fix` 行之前而非之后（与补丁指令位置不同，不改任何数字，可接受，见 F9 备注） |
| F7（CLASS_3） | **已应用** | §4 末段与 §8 首段两处逐字替换在位 |
| N1 / N2 | **已落实** | 探针 (a) 七值齐全、`NO_S5_ENTRY` 分支被断言；`_legal_env` 改生产写入器（§0） |
| N3 / N4 / N5 | 无动作 | 披露保持；`.DS_Store` 口径已写入 §6；两个非本会话副本仍未触碰 |

### 2. 逐条 AC 核对

| 编号 | 结论 {满足, 不满足, 证据缺失} | 证据 | 理由 |
|---|---|---|---|
| AC-1（修订 1） | 满足 | `inventory` 164 条 before/after 相等（未改）；`audit-stats` 65 条含 Unity 日志 `equal: true`；并集 289 条 288 相等、唯一不等为本阶段合法输出清单（§0 独立重算，与报告 §8 一致）；失败只写失败收据（F1/F2 回归 + 探针） | R1 的 F1 闭合；每次执行实际读取的每个文件（含日志）执行前后逐条相等；原件零改动 |
| AC-2 | 满足 | 真实工件同 R1（101 辆、8 辆 `NO_S5_ENTRY`、57,430 行）；夹具现覆盖 `NO_S5_ENTRY`/`UNUSABLE` 分支（探针 (a)、`FieldTableTests` 1/1） | 未改实现，N1 夹具补齐 |
| AC-3（修订 1/2/3） | 满足 | 真实工件同 R1（0 不符）；夹具七值齐全（探针 (a)）；`InstructionTests` 6/6 | 未改实现，N1 夹具补齐表 C 第 3/4 行 |
| AC-4（修订 1/2/3/4） | 满足 | 冻结清单身份：`panel_index`→`frame_id/object_id/stratum/surface/overlay_sha256` 逐条核对且占位/缺失身份 fail-closed（F2）；源日志纳入执行前后核验（F1）；60 张叠加图/原图字节与判定零改动；统计逐层与 R1 独立重算相同（类别 60/0/0、颜色 59/1/0、框 52/0/8）；`test_verdict_table_format_mismatch_fails_closed` 14 例 + `test_stats_writes_only_failure_receipt_on_bad_verdict_table` | R1 的 (i)(ii) 均闭合；未重抽样、未重新看图、未改用户判定 |
| AC-5（修订 1） | 满足 | 报告 §5 未改，R1 逐条对照仍成立 | 未运行任何跟踪器 |
| AC-6（修订 1/2/3） | 满足 | 候选已推送（F4）；`stage_plan` 不再写错标原因的收据（F3）；实现者写入只含 A1/A2 + `.gitignore` 单条 + 状态板；两目录 10,249,590 B ≤ 32 MB、受版本控制 A2 最大 89,133 B ≤ 2 MB、峰值 RSS ≤ 382.8 MB ≤ 1 GB；`WriteBoundaryTests` 2/2；全套日志基线/新增分开（1156/9 基线 ERROR/0 failures） | R1 的 (i)(ii) 闭合，(iii) 补丁已应用；残留只有 F9 的两处叙述计数（CLASS_3，不改结论） |

### 3. 读过的文件与测试

- 共享文档：`AGENTS.md`（含 COORD-011 后版本）、`docs/current-status.md`（结构节、全部交接、本项与 `COORD-010`
  行、本项全部 Log）、`docs/collaboration-workflow.md` §4.3/§4.3.1/§4.3.3/§4.4/§4.6/§6.1/§7、
  `docs/engineering-workflow.md` 全文、`docs/roles/review.md`、`docs/reviews/README.md`、提案全文（合同、十二条
  修订、代录机读格式 v1、核对表 C2@K4、决策记录）、账本本项四条、`docs/implementation-status.md` 工程继承清单
  本项行、本文件 R1 全文。
- 实现（副本内）：`tools/eng_asset/label_panel.py` 全文（重点 `PanelError`、`stage_plan`、`stage_panels`、
  `stage_render_fix`、`stage_stats`、`parse_audit_panels`、`read_unity_verdicts`、`main`）、`receipts.py` 全文；
  `inventory.py`/`__init__.py` 未改，只核 blob。
- 测试（全文）：`tests/test_eng_asset_label_panel.py`（19 例）、`tests/test_eng_asset_inventory.py`（11 例，重点
  N1 夹具与 `FieldTableTests`）。
- 证据：`docs/evidence/P1-ENG-ASSET-001-inventory.md`（返工 diff 全文 + §6/§8/§9/§10）、`-tests.log`、
  `-label-audit.md`（与收据输出三方核对）；本地 `input-manifest.json`、三份 `run-stats-*`、两份
  `run-render-fix-*`、`panel-receipt.json`、`receipts/` 全目录列表；`outputs/…/panel/` 60 + 60 张 jpg；
  `docs/unity-test-log.md` 相对候选的 diff（空）。

### 4. Findings

#### Blocking

无。修复触及行上未发现 CLASS_1/2；旧阻断 finding F1–F4 全部闭合；无 `RED_LINE`。

#### Non-blocking

##### F8（CLASS_2，依据 `SCOPE_GAP`；非阻断，路由接受角色）— 日志文件缺失时 `stage_stats` 抛裸异常、不写失败收据（F1 修复引入）

- **依据条款**：`AC-4` 修订 3「stats 对条目缺失/…的任一情况失败退出，只新增既有 failure-stats 收据，
  reason=`VERDICT_FORMAT_MISMATCH`」；`AC-1` 修订 1「失败只发布失败收据」。
- **位置**：`tools/eng_asset/label_panel.py` `stage_stats` 修复触及行 `log_entry = manifest.record(log_path, …)`
  位于 `read_unity_verdicts` 之前；`InputManifest.record` 先 `stat()`，文件不存在即抛 `FileNotFoundError`，
  `read_unity_verdicts` 内既有的 `ENTRY_LOG_MISSING` → `VerdictFormatMismatch` → 失败收据分支从该入口已不可达。
- **事实（探针 (b)）**：候选 → 裸 `FileNotFoundError`、无 `failure-stats-*`、无 `run-stats-*`、清单原样；R1 候选源码
  → `VerdictFormatMismatch`（`ENTRY_LOG_MISSING`）并写 `failure-stats-*`。不产出统计、不发布工件，与 fail-closed
  的结果一致，但失败收据契约在该分支退化（与 R1 N3 披露的其它非 `EngAssetError` 路径同类）。
- **范围判据**：生产 CLI 固定读 `docs/unity-test-log.md`（受版本控制、始终存在），只有 Python API 显式传入不存在的
  `unity_log` 才触发；从已归档工件不可产生 → 不可达 → `SCOPE_GAP`，非阻断。AC-4 修订 3 的「条目缺失」由
  `test_verdict_table_format_mismatch_fails_closed` 末段按「日志文件存在但没有本项条目」覆盖，不受影响。
- **建议闭合（若裁定范围内）**：`stage_stats` 在 `manifest.record(log_path)` 之前对 `log_path.is_file()` 为假时
  改走 `read_unity_verdicts` 同一失败通道（`VerdictFormatMismatch` + `failure-stats-*`），或在登记处捕获
  `FileNotFoundError` 转为该异常；具名回归：生产 `stage_stats` 以不存在的日志路径运行 → 只写
  `failure-stats-*`（reason `VERDICT_FORMAT_MISMATCH`，problem `ENTRY_LOG_MISSING`）。首轮提出，非 `上轮漏检`，
  不写 `blocks_consuming_gate`。

##### F9（CLASS_3，依据 `IN_SCOPE_NO_BC`；证据叙述计数）— 报告两处计数与返工后的真实收据不符（逐字替换补丁）

均不驱动工具或操作员动作（阈值远未触及、结论不变）；由实现角色在下一次提交应用，本角色一行不改，不开轮。

1. `docs/evidence/P1-ENG-ASSET-001-inventory.md` §6 体量口径（返工重跑 stats 新增一份收据后的当前值）：

```text
旧 → 两个本地派生目录合计 10,244,893 B（≈ 10.2 MB）≤ 32 MB（AC-6 修订 1 口径：`runtime/eng-asset/P1-ENG-ASSET-001/` 2,152,022 B
新 → 两个本地派生目录合计 10,249,590 B（≈ 10.2 MB）≤ 32 MB（AC-6 修订 1 口径：`runtime/eng-asset/P1-ENG-ASSET-001/` 2,156,719 B
```

2. 同文件 §9 C1-5 行（实现者自己在 §10 F1 行已指出该句算术不成立，但 §9 原句未改；返工后真实值为 65 条）：

```text
旧 → 该阶段不变输入 64 条（指令逐行、S5 目录、Unity 日志、`panel-receipt`、render-fix 收据、60 张叠加图）`equal: true`
新 → 该阶段不变输入 65 条（指令逐行、S5 目录、Unity 日志、`panel-receipt`、render-fix 收据、60 张叠加图；`R1@K4` F1 返工后重跑）`equal: true`
```

备注（不要求动作）：§6 收据表的 `stats` 行按 R1 补丁应在 `render-fix` 行之后，当前在其之前；行内数字正确，
顺序不影响任何判据。

### 5. 缺失或薄弱的测试（非阻断记录）

- **N6**：无 stage 级用例覆盖「日志文件不存在」的失败收据路径（见 F8）；函数级 `ENTRY_LOG_MISSING` 分支只在
  直接调用 `read_unity_verdicts` 时可达。
- **N7**：`test_forbidden_panel_root_is_refused_without_touching_its_contents` 只覆盖 `panel_root` 落禁写根；
  `local_root` 落禁写根的前置拒绝（本轮新增的 `assert_output_allowed(local, …)`）无具名用例，行为由
  `receipts.assert_output_allowed` 的既有用例间接覆盖。披露，不阻断。

### 6. 交回动作

1. **接受角色**：按 workflow §4.6 消费本轮 `PASS_WITH_NOTES`——汇总实现者证据、本轮独立复核与 `UNITY_NA` 附议
   决定 `DONE` 或列出未闭条目；裁定 F5（代码已修，记「范围内必修·已修」或记入「范围外已知缺陷」账本）与 F8
   （`SCOPE_GAP`：账本 `OPEN` 或纳入范围修复）；本轮无 `blocks_consuming_gate`，无 release 义务。
2. **实现角色**：下一次提交应用 F9 两处逐字补丁（不开轮）；若 F8 被裁定范围内，按 §4 建议补修复与具名回归。
3. 不启动依赖本项结果的后续接入；真实跟踪探针与固定评估集交付仍不在本项。

## `UNITY_NA` 附议（R2@K4，延伸至本候选）

**附议**（仅限本 work ID 的 `K4` 候选，即上方 `passed_candidate`）：返工 diff 只触及 `tools/eng_asset/label_panel.py`、
两份 `tests/test_eng_asset_*.py` 与文档；全量 diff 证实 `controller/`、`Assets/`、`config/`、`ProjectSettings/`、
`Packages/` 零字节改动；工具不 import 运行时模块（`WriteBoundaryTests.test_no_controller_runtime_imports` 干净子进程
探针在 focused 中通过），只读取已归档帧与 attempt-2 工件，零 Play/scenario/session/run/attempt 身份，不改变任何
运行时行为；AC-4 的用户看图是 `OFFLINE_VISUAL_CHECK`，不是 Unity 验证，也不冒充 `UNITY_PASSED`。本附议不延伸到
`COORD-010` 迁移批（其独立复核与 `UNITY_NA` 附议仍缺），`DONE` 的关闭动作归接受角色。

### 7. 边界自查

本会话未修改任何实现文件：副本内对 `label_panel.py` 的两次换回均已 `git checkout --` 恢复并以 blob 与
`git status --porcelain` 核实；主树只写本文件与 `docs/current-status.md`；`python3 tools/check_role_writes.py
--role review` 结果记于状态板 Log；复核副本收工删除。
