# P1-VLM-DATA-002 — independent verification

Reviewer/role: 复核角色（review，独立代码复核；Fable 池，档位不低于实现者）
Work ID: `P1-VLM-DATA-002`（面向 grounding 的场景内巡览采集批，阶段 A）
Accepted design: `docs/proposals/P1-VLM-DATA-002-grounding-survey-acquisition.md`
（BC-SURVEY-1…16 + `CLARIFY` 行 BC-SURVEY-17/18；核对表 `C1@stageA`）
Implementer evidence: `docs/evidence/P1-VLM-DATA-002-stage-a-implementation.md`

轮次按 COORD-009 命名 `R<n>@<停点>`；本文件只追加，不删除旧发现。

## R1@stageA — 2026-09-04

### 0. 候选、开轮资格与方法

- **候选**：`dbb02776b8f2927708a80b618a1ba95f9f612f76`（实现角色闭合 `C1@stageA`
  4 项不满足 + 4 项关注项的批次；主树 HEAD 与候选同一提交）。
- round_candidate: dbb02776b8f2927708a80b618a1ba95f9f612f76
- **开轮资格（COORD-007 R1）**：本 work ID 尚无通过指针行；被改动的七个
  `tools/dist_data/` 模块的上一通过候选由 `docs/reviews/P1-VLM-DATA-001.md` 最近一行
  通过指针行派生 = `4739a39`（DATA-001 复核轮 8）。运行时派生范围
  `git diff 4739a39..dbb0277` 于 PLAY_GOVERNING 上非空：27 个文件——新增
  `tools/run_grounding_survey.py`（2,574 行）、`tests/test_survey_tool.py`（2,370 行）、
  `tests/test_dist_data_survey.py`（1,045 行）、`tests/fixtures/p1-vlm-data-001-contract-attempt-1.json`、
  7 份 `config/scenario.p1-vlm-survey-a{1,2,3,4,6,7,9}-p1-c1.json` + 7 份
  `config/p1-vlm-survey-plans/<identity>/plan.json`；修改
  `tools/dist_data/{artifacts,bind_layout,build_catalog,build_inventory,contract,roots,run_pipeline}.py`；
  另有 `tools/check_docs.py` 与 `tests/test_check_docs.py`（COORD-009 协调批次
  `f6ccce3`/`00bd7b2`/`adb0f67`，提交信息引用账本授权条目；`adb0f67` 自述走 COORD-007 R5
  通道，本轮按该通道要求逐文件 diff：消耗性门机检、账本 `RELEASED_SCOPE_GAP` 视同 release、
  README/预筛/围栏排除，与 AGENTS.md / workflow §4.4 条文一致，**无 finding**）。
  `controller/`、`Assets/`、`ProjectSettings/`、`Packages/packages-lock.json`、
  `config/scenario.default.json` 与既有冻结配置全区间零改动（实测 diff）。
- **区间归属**：work item 基线 `61a089c`（授权登记，纯文档）→ 候选共 19 个提交；
  PLAY_GOVERNING 只出现在 6 个实现批次（`ceb3a19`、`29581f0`、`eda6aa9`、`6bf3582`、
  `bc83728`、`dbb0277`）与 3 个 COORD-009 协调批次；接受轮/裁定/CLARIFY 提交均纯文档。
  `git diff --check` 全区间只有 `docs/current-status.md` Gate board 一行行尾空白（本轮随状态板
  更新顺手清除，非 finding）。
- **方法**：一次性复核副本 `git worktree add --detach .claude/worktrees/review-P1-VLM-DATA-002 dbb0277`；
  `tools/run_grounding_survey.py` 全文、七个 dist_data 模块相对 `4739a39` 的全部 diff、两份测试
  全文、7 份 plan/config、夹具逐一读完；不读任何角色的转述代替读码。提案 §2.1–§2.4、§5、BC 表、
  `C1@stageA` 核对表、证据 §1–§15、授权账本 2026-09-03 条目、workflow §4.3/§4.4 重读。
  自写探针只在副本与 scratchpad 内运行；主树实现文件零改动（收工 `check_role_writes --role review`
  核对）。
- **测试树哈希**（`git rev-parse dbb0277:<tree>`）：`tests` = `1894abcecf134e81c1f2fd73dca8d6a1f73af3c4`，
  `tools` = `78066d6ba20ff74107e36a125859926d2989b6ae`，`config` = `945dd14772fdcf336e40ee673019e033568286ff`。

### 1. 复核自跑的证据（不信报告数字，全部重跑）

| 项 | 实测 | 与声明比对 |
|---|---|---|
| focused `tests.test_dist_data_survey`（副本，python3 3.14.6） | **82 OK** | ✓ 证据 §5 |
| focused `tests.test_survey_tool`（副本，python3，无 Pillow） | **151 OK，skipped=5**（Pillow 门） | ✓ |
| focused `test_survey_tool.py`（副本，`.venv-yoloe` 3.12.13，`unittest discover -s tests -p`） | **151 OK，0 skip**（`WitnessPixelTest`/`WitnessScanExtentTest` 实跑） | ✓ 证据 §5「151 OK」 |
| focused `test_dist_data_survey.py`（副本，`.venv-yoloe`，discover） | **82 OK** | ✓ |
| 合计焦点对 | **233** | ✓ 状态板/证据「233」 |
| 7 份正式 plan/config | 副本内重算 `build_plan`/`build_scenario_config`：7/7 与盘上字节**逐字相同**；`survey_acquisition_sha256` 7/7 = 当前投影 `b4ad4f7bde5fa22d7913aa5e4adf2ddfd724c33dc7116904ddb53c87045b80bf`；7/7 `valid`，候选均为 1；保留位置/视角 14/224、12/192、14/224、14/224、14/224、14/224、11/176，证人视角 3、预测证人帧 60；a2 丢 R14-120/R14-180、a9 丢 R14-120/R14-180/R26-180（均 `PLAN_POSITION_UNREACHABLE`）；专用配置相对 default 的差异恰为 `scenario_id`、`anchor_world_m.{x,z}`、`target.route_world_m`、`target.speed_mps`、`sensor.retained_frame_count` | ✓ 证据 §10 表 |
| BC-SURVEY-7 字节夹具 | `tests/fixtures/p1-vlm-data-001-contract-attempt-1.json` 5,014 B，SHA-256 `1d1cea17…6ddf`，与主树正式 `runtime/dist-data/contract/attempt-1/contract.json` **逐字节相同** | ✓ 证据 §2 |
| 真实仓库只读 S1/S2 preflight（副本代码 + 主树 `runtime/`，`run_pipeline` 默认 preflight） | `records 30110`、`zero_match 0`、`multi_match 0`、`included_images 23706`、`bound_frames 23549`、`EXCLUDED_DIAGNOSTIC_CHANNEL 315`、`invalid_partitions []`；跑后 `runtime/dist-data/` 仍 92 文件、最新 mtime 仍为 09-01 | ✓ 证据 §10「真实仓库上的只读 S1 preflight」 |
| 相机基底约定（`synthetic_camera`） | 对归档 `…arm-b-trial-1-post-run/frames/frame_0000000730.json` 复算：`right = normalize(cross(worldUp, forward))`、`up = normalize(cross(forward, right))` 与 sidecar 分量最大偏差 1.6e-7；`fx = (480/2)/tan(30°) = 415.692` 与 `intrinsics_px` 一致 | ✓ 证据 §4 |
| S2 端到端探针（副本，生产路径：`DriveCase` 跑 `drive`→`close`，再 `build_inventory`→`build_layout`） | 137 帧归档，巡览 unit 经子树快照绑定 **`BOUND`** 到 `session/scenario_config.json`，`survey_validation` 产出 `INSUFFICIENT_WITNESS_FRAMES` → partition `INVALID`（裁剪计划下证人分母不足，符合预期） | 现有测试未覆盖此端到端路径（见 §5） |
| 反向变异 A（BC-14：`survey_sessions` 退回条件写入） | `test_the_shape_the_driver_would_actually_publish_today` **FAIL** | ✓ 证据 §5 |
| 反向变异 B（BC-16：撤掉 `prepare` 的 `assert_anchor_enabled`） | `test_prepare_refuses_an_ungated_backup_anchor` **FAIL** | ✓ |
| 反向变异 C（BC-2：`drive_log_is_pre_command_only` 恒真） | `test_zero_frame_close_refuses_a_log_that_issued_commands`、`…_without_the_command_count` **2/2 FAIL** | ✓ |
| 反向变异 D（BC-4：`resolve_read_attempt` 退回只读 `self.attempt`） | `MixedAttemptReadTest` **3 errors** | ✓ |
| 变异恢复后 | 上述 10 条 **全绿**；副本 `git status` 干净 | ✓ |

全套（python3 1104 / `.venv-yoloe` 1209）未重跑：按 workflow §4.4 全套是实现者停点证据的义务，
不是复核开轮义务；实现者数字已记录在证据 §5。测试输出全部写入 scratchpad 日志，上下文只回显摘要。

环境事实（非候选缺陷）：`.venv-yoloe` 的 site-packages 装有第三方顶层包 `tests`，仓库 `tests/` 是无
`__init__.py` 的命名空间包，故 `python -m unittest tests.test_survey_tool`（及路径形式）在该解释器下
`ModuleNotFoundError`；`unittest discover -s tests -p <file>` 正常。实现者「151 OK」按 discover 形式可复现。

### 2. BC-SURVEY-1…18 与 `C1@stageA` 八项闭合的逐条核实

| 条款 | 复核结论 | 核实方式（代码 + 测试） |
|---|---|---|
| BC-1 | 满足 | `transition_waypoints`：`safe_world_y = max(start.y, end.y, max(B'.max_y)+1)`，`H_safe∈[8,30]`、两个绕行端点 ≤33 m、三段重测；`PlanGeometryTest` 三条；plan a1/a2/a7 的 `detour` 记录读值一致 |
| BC-2 | **闭合成立** | `DriveSession.run` 在 `verify_preconditions` 之前零 `send_*`；`RuntimeBridge.commands_issued` 由三个发令方法累加、写入 drive-log 头；零帧 `close` 要求终态∈{None, DRIVE_REFUSED_AUDIT, ABORTED_NO_FRAMES} **且** `commands_issued == 0`，缺键/非整数/负数一律拒绝，日志缺席（bootstrap 抛错）接受；反向变异 C 打红 |
| BC-3 | 满足 | `install_diagnostic` 逐字沿用 default `scenario_id`，不建 plan/config/session/标记；`collect_diagnostic` create-once hold；证据 §11 记诊断 Play 1/3、HEAD `6bf3582` 干净树、hold 路径、两张样帧 SHA、确认人与结论 |
| BC-4 | **读侧闭合成立；「从首个未发布阶段续跑」未闭合 → F2** | `read_chain()` attempt-3 = (`attempt-3`,`attempt-2`)，attempt-1 不进混合路线；`_read_ref`/`_catalog_stream`/S2 均经 `resolve_read_attempt` 逐依赖解析并交出实际 ref，全缺即 `PipelineError`；`MixedAttemptReadTest` 真正构造混合状态（S3 `inputs` = `[(inventory,attempt-2),(layout,attempt-3)]`，SHA 等于盘上字节）；反向变异 D 打红。但 `run_stages`/`main --run` 恒从 S0 起，见 F2 |
| BC-5 | 满足 | `write_plan` → `_create_once_json`（`os.link` 原子不覆盖，字节相同幂等）；7 对文件已纳入版本控制并随候选进入本轮 |
| BC-6 | 满足 | 三个上限全部来自合同投影常量；`prepare`（拒绝不计次）、`write_plan`、`install_diagnostic` 越界前拒绝；三条边界回归 |
| BC-7 | 满足 | `roots.root_manifest()` 按声明顺序投影四成员与五操作字段（无 `note`/regex）；`reconcile_root_manifest` 在 `assert_empty_dirs` 之前按 canonical 字节比对；`stage1_inventory` 要求两键均为对象；夹具即真实 attempt-1 字节 |
| BC-8 | 满足 | `_clear_of_obstacles` 三轴闭集 ±4 m；`ParkedObstacleMarginTest` 三条 |
| BC-9 | 满足 | 锚点表只作序号/坐标/顺序；`recompute_anchor_candidates` 只报告差异；`install_diagnostic`/`write_plan` 均经 `resolve_anchor_plan` 过全部硬门 |
| BC-10 | 满足 | `DYNAMIC_TARGET_SCHEMAS = (m3, scouting, sweep_proxy, target_parked)`；`target_blocker_from_truth` 的代理分支仍由 `schema_family is None` 触发 |
| BC-11 | 满足 | `VALID_SURVEY` 唯一插于 `VALID_PARENT_HOLD` 之后；旧序逐字不变（`UsageClassOrderTest`） |
| BC-12 | 满足 | `red_components` 整帧、union-find 4-邻接、右/下开框、与真实字节尺寸对账、`WITNESS_CONNECTIVITY` 实际消费；`select_witness_component` 按 `(area, box)` 取最大 |
| BC-13 | 满足 | `parse_survey_view_id` 完整语法；`load_pinned_survey_plan` 钉 plan 路径/字节/身份 + 双侧采集钉子；S1/S2/`close`/`drive`/`verify` 全部走 `validate_selection_view_id`；`is_survey_witness_view` 已删除 |
| BC-14 | **闭合成立** | `contract_document` 无条件写 `survey_sessions`（缺省空表）；`stage0_contract` 传实际表；attempt-1 夹具差异键恰五（两种形状）；六入口钉子核对读码确认（`prepare`/`drive`/`close` 三分支/`verify`/S1 `reconcile_survey_acquisition`/S2 `_survey_selection_rows`）；反向变异 A 打红 |
| BC-15 | 满足 | `evaluate_parked_witness` 中心命中 `x0 ≤ cx < x1 ∧ y0 ≤ cy < y1`（源码断言测试） |
| BC-16 | **闭合成立** | `BACKUP_ANCHORS` 由 `SURVEY_ANCHOR_TABLE[-2:]` 派生 = (9, 10)；`assert_anchor_enabled` 在 `prepare_session` 安装现场之前执行，前置锚点 `PENDING` 即拒绝；`anchor_disposition` 以「任一会话写出 completion」为 `CLOSED`、无正式身份且穷举无合法候选为 `UNREACHABLE`；反向变异 B 打红 |
| BC-17 | 满足 | `survey_acquisition()` 顶层恰三键；`constants` 自动枚举 = 89 项，与 `dir(contract)` 的 `SURVEY_*` 双向对齐 |
| BC-18 | 满足 | `AnchorTableReachabilityTest` 逐锚点计数 53/209/60/74/135/248/62/128/217/0、5/8 全量无效、10 空集、七锚点候选 1；本轮 7 份 plan 复现同结论 |
| 关注项 1 | 闭合成立 | `planned_view_counts(plan)` 给分母，`classify_frames` 必传；`executed_*` 单独报告；`C1UnmetTest` 两条 |
| 关注项 2 | 闭合成立 | `validate_survey_partition` 读 `runtime/p1-vlm-survey/<session>/completion.json` 的 `tentative_witness`，缺失/不等五字段均 `LayoutError`；`close` 在低达成率降级**之后**取 VALID 帧算临时结论，与 S2 取 selection 的 VALID 行同源，降级会话两侧同为 `INSUFFICIENT_WITNESS_FRAMES`（读码确认，无误判风险） |
| 关注项 3 | 闭合成立 | 查重 → 按 `session_id` 排序逐位置比对 → 闭集外字段拒绝；`InventoryIntegrationTest` 四条 |
| 关注项 4 | 闭合成立 | 证据 §10 指针前缀已为 ASCII `test:`/`artifact:`/`cmd:` |

### 3. Findings（CLASS_1/2 → `REWORK_REQUIRED`；每条恰一个依据值）

#### Blocking

#### F1（CLASS_2，依据 `IN_SCOPE_NO_BC`）— attempt-2/3 写侧 supersession 不按「最新已发布前身」解析

- **位置**：`tools/dist_data/run_pipeline.py` `PipelineDriver._supersession_kwargs`（约第 213–228 行）
  与 `main` 的 `--supersedes/--supersession-reason`；测试
  `tests/test_dist_data_survey.py::Attempt3ReadRefTest.test_supersession_kwargs_skip_absent_predecessors`。
- **事实**：(a) 前身只取操作员传入的**单一** `--supersedes` 值；该 attempt 在某阶段未发布时直接返回
  `{}`，该阶段的 attempt-3 工件 `supersedes: null`。提案 §2.2 第 5 条逐字要求「每个 attempt-3 工件
  `supersedes` 该阶段**最新已发布前身**（attempt-2 若已发布，否则 attempt-1），并写原因」——正式
  attempt-1 六件 S0–S5 全部存在，前身从不缺席，`{}` 不是「不伪造」而是断链。上述测试把这一偏差写成了
  期望值。(b) `--supersedes` 缺省为 `None`：`--run --attempt attempt-2` 不带该参数即静默写出六件
  `supersedes: null` 的 attempt-2 工件，违反 §2.2 第 4 条「S0–S5 attempt-2 各自 `supersedes: attempt-1`」
  与 §5 验收条件 4「每件各自 `supersedes` 最新已发布前身」。
- **范围判据**：触发状态由提案 §2.2 第 4/5 条与 §5 条件 4 点名，且可由已归档 attempt-1 六件 + 生产
  写盘函数造出的部分 attempt-2 产生 → 可达；无 BC 覆盖写侧前身解析 → `IN_SCOPE_NO_BC`，阻断。
- **闭合要求**：前身按阶段从 store 解析（当前 attempt 之前最新已发布者），不取操作员单值；attempt ≥ 2 的
  写入若无法解析前身或缺原因须拒绝而非静默省略。绑定具名回归（fixture 走真实 `ArtifactStore.write` /
  `write_composite`，修前必失败）：至少 (i) attempt-3 在 `frames_catalog@attempt-2` 缺席、
  `frames_catalog@attempt-1` 存在时 envelope `supersedes == "attempt-1"` 且带原因；(ii) attempt-2 未声明
  前身时要么解析为 `attempt-1` 要么拒绝写入。现有 `test_supersession_kwargs_skip_absent_predecessors` 须
  改写为上述语义。

#### F2（CLASS_2，依据 `BC-SURVEY-4`）— 生产入口没有「从首个未发布阶段续跑」，BC-4 的混合读取路径只在测试里可达

- **位置**：`tools/dist_data/run_pipeline.py` `default_stage_order`/`run_stages`/`main`（`--run` 恒从
  `contract` 起，`--through` 只限终点）。
- **事实**：BC-SURVEY-4 的前提与 §2.2 第 5 条（AR2-5）明文是「attempt-3 从**首个未发布阶段**起重跑」；
  `C1@stageA` 判 BC-4 不满足的理由逐字包含「`run_stages()` 也总从 S0 开始」，证据 §15 的闭合只处理了读侧
  解析，未触及此项。当前 `--run --attempt attempt-3 --supersedes attempt-2 …` 会把 S0/S1/S2 也重新以
  attempt-3 发布（尽管 attempt-2 已发布且完好），随后各阶段都读到刚写的 attempt-3 → 「attempt-3 优先、
  否则 attempt-2」的回退在生产入口**永不触发**；`MixedAttemptReadTest` 是逐阶段直接调用方法造出的状态。
  另按 §5 条件 4「失败落在 S2/S3/S4/S5 的具名回归逐一证明」：只有 S3 用例真正走了回退；
  `test_stage5_inputs_follow_the_same_resolution` 读到的两件都已是 attempt-3（未触发回退）；S2/S4 无用例。
- **范围判据**：触发状态由 BC-4/§2.2 第 5 条/§5 条件 4 点名 → 可达；有 BC 覆盖 → `BC-SURVEY-4`，阻断。
- **闭合要求**：生产入口（`run_stages`/`--run`）须相对被 supersede 的 attempt 确定首个未发布阶段并从该
  阶段起跑，不重发已发布阶段；配经**生产入口**的具名回归，分别让 S2、S3、S4、S5 成为首个未发布阶段并
  断言实际读取 ref 的 attempt 与 §2.2 第 5 条一致（S2 读 inventory@2；S3 读 inventory+layout@2；S4 读
  frames_catalog@2；S5 读 frames_catalog+layout@2/3），修前必失败。F1/F2 同属一条返工，修复预期只触及
  `tools/dist_data/run_pipeline.py` 与测试，不得移动 7 份 create-once plan 的钉子。

#### Non-blocking（CLASS_3，逐字替换补丁，由拥有该文件写权限的角色在下一次提交应用；本角色一行不改）

#### F3（CLASS_3，依据 `IN_SCOPE_NO_BC`；文档一致性）— 设计文档版本状态行与 M6 行时态过期

- 文件 `docs/phase1-single-drone-design.md`（接受角色维护）。
- 第 210 行：`v0.3.31 为当前已接受研究设计` → `v0.3.34 为当前已接受研究设计`（页首版本条已是 v0.3.34）。
- 第 1006 行 M6 行内子句：`Acceptance round 5 确认 BC15 已闭合、接受七锚点事实但仍退回 BC14 重入/零帧 verify 与 BC16 穷举回归；BC17/18 已按 COORD-009 将两条全称量词收束为具名闭集；诊断 Play 尚未执行、正式身份尚未创建；`
  → `BC17/18 已按 COORD-009 将两条全称量词收束为具名闭集；阶段 A 稳定候选已过 COORD-005 保真并进入独立复核（当前门与轮次见 docs/current-status.md）；`。
- 补丁不改任何数字、哈希、ID 或 disposition。

#### F4（CLASS_3，依据 `IN_SCOPE_NO_BC`；已执行步骤的时态）— 证据文件页首自述与 §10/§11 矛盾

- 文件 `docs/evidence/P1-VLM-DATA-002-stage-a-implementation.md`（实现角色维护）。
- 第 11–12 行：`本批为接受轮 5 的窄返工——BC-SURVEY-14 两条 fail-open + BC-SURVEY-16 全候选穷举，` / `闭集由 BC-SURVEY-17/18 两条 `CLARIFY` 定死`
  → `本文覆盖接受轮 5 窄返工（§14）、阶段 A 停点与 COORD-005 保真（§10/§11）以及 `C1@stageA` 八项闭合（§15）`。
- 第 14–18 行引用块整段：`> **本批未创建任何正式身份**：…因此本批到此为止。`
  → `> **正式身份状态**：COORD-005 保真 PASS（§11）之后，按 §2.3 步 3 与 §5 第 6 条生成了七对首选正式 plan/config（§10 表）；零正式采集 Play、零 session/run ID、零 API、零 GPU、零下载；用例里的计划一律生成在临时目录内。`
- 补丁只更正时态与指针，不改任何数字、哈希、ID 或 disposition。

说明：F3/F4 依据列按闭集只能填一个值，此处取 `IN_SCOPE_NO_BC`（范围内、无 BC 的文档一致性项）；两者为
CLASS_3，不阻断、不进 COORD-009「BC 缺失」阻断计数，接受角色派生归因时请按 CLASS_3 单列。

### 4. 观察项（不分级、不阻断；随返工顺带处置或留档即可）

1. COORD-005 两张样帧（frame 0 与 frame 175）SHA 相同——187 帧逐字节相同是 §2.1(f) 零转动的实测证明，
   但也意味着保真检查实际只看了一幅图像内容；「≥3 辆同框」为 2 完整 + 1 截断，证据 §11 已如实披露。
   本角色附议 `C1` 对 BC-3 的「满足」：§4.3.2 要求的样帧路径/SHA/确认人/结论齐备，条款未要求完整框。
2. 工具本身没有「授权阶段」门：`prepare` 只按 ≤10 次正式 Play 拒绝，不知道授权 #2 是否签发；阶段 B 之前
   由状态板与账本担任该门（AGENTS.md：账本没有的授权视为未发生）。
3. `parked_candidates` 的排序键 `(|d − 8|, x, z)` 里的「8」取自 `SURVEY_PARKED_MIN_CATALOG_VEHICLE_M`
   （当前同为 8.0），是常量复用而非语义绑定；同 patch 平手规则以取负 UTF-8 码列表求 `max` 实现「id 升序」，
   在一个 id 是另一个 id 前缀且余量恰好相等的角落与字面规则相反。两者都在 S0 哈希面内，任何改动都会移动
   钉子并使 7 份 create-once plan 失效，故只记录，不要求改动。
4. `spent_play_count` 以「写出 completion 的会话数」计 Play；`CLOSE_TREE_MISMATCH` 不写 completion 但保留
   活动标记，只有人工删除标记才可能少计一次——需人工干预的状态，不算工具缺陷。
5. 诊断信封以 hold 数计（`next_diagnostic_index − 1`），无帧的诊断 Play 不会被计入；当前 1/3 与账本一致。
6. `close` 不核对每张 sidecar 的 `scenario_id`（`drive` 只核首帧）；在 `prepare` 拒绝非空帧目录的前提下，
   现场只可能有 override 场景的帧，故不可达。
7. 巡览视角离天底 44° 距 `TetheredGimbal.maximumOffNadirDeg = 45°` 仅 1°；位置误差把几何推过 45° 会被
   云台夹紧并 `Saturated`，逐帧朝向门随即把这类帧判 `PROTOCOL_INVALID`（fail-closed）。属提案冻结常量的
   设计裕量，阶段 B pilot 的达成率会直接反映，此处只提示。
8. `GimbalCommandReceiver` 只在摄入时判租约过期，`LookAtWorld` 设定的目标持续生效，故单次 `look_at`
   + 4 s 证人停留可行；`BodyCommandReceiver` 过期即 `Hold`，与 §2.1(g)「一死指令即过期、机身 hold」一致。
9. `.venv-yoloe` 的 `tests` 包遮蔽问题见 §1；后续证据请写明测试调用形式。

### 5. Missing or weak tests

- 无任何用例端到端跑 `bind_layout.build_layout`（S2）于巡览归档：现有 `SurveyLayoutAuthorityTest`/
  `TentativeWitnessComparisonTest` 直接调用 `validate_survey_partition` 并手工构造 `record`。本轮探针证明
  绑定经 `_unit_subtree_snapshot` 成立，但该路径应有生产回归（建议随 F2 返工一并补，非阻断）。
- §5 条件 4 的「失败落在 S2/S3/S4/S5 的具名回归逐一证明」目前只有 S3 真正触发回退（见 F2）。
- `Attempt3ReadRefTest.test_supersession_kwargs_skip_absent_predecessors` 把 F1 的偏差固定为期望值，须改写。

### 6. `UNITY_NA` 分类

本候选未申请 `UNITY_NA`（§5 条件 6 明令 Unity 列 = 用户 Play 采集记录），Gate board Unity 列为
`NOT_RUN 正式采集`，无须附议或反对。COORD-005 人眼保真检查按 workflow §4.3.2 记入证据 §11（样帧路径、
SHA、确认人、结论、hold 路径、采集前 HEAD 与干净树），本角色确认其存在且未进入证据链、零新 ID。

### 7. Verdict

**`REWORK_REQUIRED`**（本停点 `stageA` 第 1 次；COORD-009 (c)：第 2 次后未闭集冻结、轮 3 终局）。

- 阻断：F1（CLASS_2，`IN_SCOPE_NO_BC`）、F2（CLASS_2，`BC-SURVEY-4`）→ 直接交回实现角色（COORD-008 S2），
  修复后**直接交回复核** `R2@stageA`，不经核对轮；修复触及 `tools/dist_data/run_pipeline.py`
  （PLAY_GOVERNING）→ R2 必开轮，范围 = F1/F2 闭合红绿 + 修复触及行上的 CLASS_1/2 + `RED_LINE`。
- 非阻断：F3（接受角色，设计文档）、F4（实现角色，证据文件）按 §3 逐字补丁在各自下一次提交应用。
- 本轮无 `上轮漏检`，不写消耗性门阻断机读行；无 `RED_LINE`（真值只进入 `CoverageEvaluator`/
  真值 join 路径，巡览工具与 S1–S5 增量未读取 Unity 真值；人眼保真已完成）。
- 本轮为 `REWORK_REQUIRED`，**不写**通过指针行。

#### Requested action

1. 实现角色：修 F1/F2，各绑定修前必失败的具名回归（生产路径 fixture），更新证据 §15/§5 与状态板交接行，
   应用 F4 补丁，直接交 `R2@stageA`。
2. 接受角色：不消费本轮（中间轮不消费，COORD-008 S2）；下次提交顺带应用 F3 补丁；归因派生时 F3/F4 按 CLASS_3
   单列。
3. 用户：无需动作；授权 #2 与全部正式采集/后续阶段保持关闭。

#### 边界自查

本会话只写入 `docs/reviews/P1-VLM-DATA-002.md` 与 `docs/current-status.md`；`controller/`、`Assets/`、
`tools/`、`tests/`、`config/` 零改动（反向变异只在一次性副本内进行并已 `git checkout` 恢复，副本已删除）；
`check_role_writes.py --role review` 结果见收工记录。

## R2@stageA — 2026-09-04

### 0. 候选、修复触及行与方法

- **候选**：`85adf93e1e52bd71eb443ee78cfa350147d97c9f`（实现角色闭合 `R1@stageA` F1/F2 的返工批；
  主树 HEAD 与候选同一提交）。复核返工直接回复核，不经核对轮（COORD-009）。
- round_candidate: 85adf93e1e52bd71eb443ee78cfa350147d97c9f
- **修复触及行**（COORD-009 (b)，基线 = 上一复核轮候选 `dbb0277`）：`git diff dbb0277..85adf93` 于
  PLAY_GOVERNING 上恰为 2 个文件——`tools/dist_data/run_pipeline.py`（新增 `_attempt_number`、
  `resolve_predecessor`、`first_unpublished_stage`、`run_stages(resume=True)`；`_supersession_kwargs` 改为
  按阶段解析并拒绝无前身/无归因；CLI 删 `--supersedes`）与 `tests/test_dist_data_survey.py`
  （`Attempt3ReadRefTest` → `SupersessionResolutionTest` 6 条；`MixedAttemptReadTest` 重写为 10 条，含 5 条
  经 `run_stages` 的续跑回归）。文档侧改 `docs/evidence/…stage-a-implementation.md`（F4 补丁 + §16）与
  状态板。`config/`、`tools/dist_data/contract.py`、`tools/run_grounding_survey.py` 零改动（实测
  diff 为空）→ 7 份 create-once plan 的钉子不可能移动。开轮资格：修复触及 PLAY_GOVERNING，必开轮。
- **全量 diff**（相对 DATA-001 上一通过候选 `4739a39`）仍为 27 个文件，与 R1 §0 相同集合，用于核实
  声明范围与红绿，不作为本轮阻断范围。
- **方法**：一次性副本 `git worktree add --detach … 85adf93`；修复 diff 全文读完；修前红 = 在副本把
  `run_pipeline.py` 整体换回 `dbb0277` 版本再跑候选测试，另加三次语义变异；恢复后复绿；一条自写探针只在
  副本内运行。主树实现文件零改动。
- **过程事实**：`85adf93` 是实现角色的提交，它顺带提交了本角色 R1 收工时未提交的状态板改动；本复核
  文件当时仍未跟踪，实现角色按只读边界未纳入。R1 内容经核对完整（227 行、F1–F4、机读行在位），
  由本角色随 R2 一并提交。

### 1. 复核自跑的证据（不信报告数字，全部重跑）

| 项 | 实测 | 与声明比对 |
|---|---|---|
| focused `test_dist_data_survey.py`（副本，python3 / `.venv-yoloe`，discover） | **90 OK / 90 OK** | ✓ 证据 §5「90」 |
| focused `test_survey_tool.py`（副本，python3 / `.venv-yoloe`，discover） | **151 OK skipped=5 / 151 OK 0 skip** | ✓ |
| 合计焦点对 | **241** | ✓ 状态板/证据「241」 |
| 修前红 0：副本内 `run_pipeline.py` 整体换回 `dbb0277` × 候选测试 | `SupersessionResolutionTest` + `MixedAttemptReadTest` 16 条 → **failures=3, errors=9** | 候选测试确实依赖修复 |
| 修前红 1（F1）：前身缺席退回静默 `{}` | `test_an_unresolvable_predecessor_is_refused_not_silently_omitted` **FAIL**（恰 1 条） | ✓ 证据 §5 变异表 |
| 修前红 2（F1）：缺归因不再拒绝 | `test_a_missing_reason_is_refused` **FAIL**（恰 1 条） | ✓ |
| 修前红 3（F2）：`run_stages` 默认 `resume=False` | 5 条续跑用例 **全部 ERROR**（S2/S3/S4/S5 + skipped 报告） | ✓ |
| 恢复候选后 | 16 条**全绿**；副本 `git status` 干净 | ✓ |

全套（python3 1112 / `.venv-yoloe` 1217）未重跑，理由同 R1 §1。

### 2. F1/F2 闭合与 F3/F4 状态

- **F1 闭合成立。** `resolve_predecessor()` 从 `attempt-(n−1)` 向下扫到 `attempt-1` 取该阶段最新已发布者；
  `_supersession_kwargs` 对 attempt ≥ 2 无前身即 `PipelineError`（不再 `{}`）、缺归因即拒绝；操作员只给
  `--supersession-reason`。R1 要求的两条回归都在：(i) `test_attempt3_falls_back_to_attempt1_when_attempt2_is_absent`
  （`write_composite` 真实写出 `frames_catalog@attempt-1`，attempt-3 解析到 attempt-1 并携带原因）；
  (ii) `test_a_missing_reason_is_refused`。原把偏差固化为期望值的用例已删除并改写。修前红/修后绿见 §1。
- **F2 闭合成立。** `first_unpublished_stage()` 相对 `attempt-(n−1)` 取首个未发布阶段；`run_stages`
  生产默认 `resume=True` 跳过已发布阶段并 emit `resumed_from`/`skipped_published_stages`；五条回归经
  `run_stages` 分别让 S2/S3/S4/S5 成为首个未发布阶段，断言实际读取 ref 的 attempt 与 §2.2 第 5 条一致且已
  发布阶段未被重发（§5 条件 4 的「逐一」现已成立）。修前红/修后绿见 §1。
- **F4 补丁已逐字应用**（证据页首两处），**F3 未应用**（设计文档属接受角色，`85adf93` 未动该文件），
  仍为未闭 CLASS_3。

### 3. Findings（本轮新阻断只来自修复触及行上的 CLASS_1/2；每条恰一个依据值）

#### Blocking

#### F5（CLASS_2，依据 `IN_SCOPE_NO_BC`）— 续跑后 `--through` 指向被跳过的阶段时，越过操作员停止界一路跑到 S7

- **位置**：`tools/dist_data/run_pipeline.py` `run_stages`（修复触及行）：`resume` 把 `order` 切到
  `start` 之后，循环里的 `if name == through: break` 因 `through` 已不在 `order` 内而永不命中。
- **事实（副本探针，生产路径夹具）**：attempt-2 发布到 `layout` 为止，attempt-3 调用
  `run_stages(…, through="inventory")`：`resumed_from = frames_catalog` 后连续写出
  `frames_catalog`/`splits`/`field_catalog`@attempt-3 三件 **create-once** 工件，随后在 `g0_report`
  以 `缺 audit@attempt-3` 抛 `PipelineError` 才停。操作员要求「跑到 S1 为止」，工具却执行了 S3–S5。
  `--through` 在本项目就是执行授权的机械边界（DATA-001 接受轮 28「只放行一次 S3→S4→S5」），越界写出的
  create-once 工件按合同永不删除，且占用 attempt-3 身份。
- **范围判据**：生产入口 `--run --attempt attempt-3 --through <被跳过阶段>` 可从已归档 attempt-1 六件 +
  部分 attempt-2 产生 → 可达；无 BC 覆盖 → `IN_SCOPE_NO_BC`；位于修复触及行 → 按 COORD-009 (b) 阻断。
- **闭合要求**：`through` 不在续跑后的 `order` 内（即被跳过或已发布）时**一个阶段也不跑**，以
  `PipelineError`（或显式「无阶段可跑」结果）fail-closed；绑定经 `run_stages` 的具名回归，断言
  attempt-3 零工件写出，修前必失败。

#### F6（CLASS_2，依据 `IN_SCOPE_NO_BC`）— attempt 命名不合式时，新加的谱系门被静默绕过

- **位置**：`_attempt_number()` 对非 `attempt-<n>` 形式返回 `None`；`_supersession_kwargs` 于
  `current is None` 直接 `return {}`；`first_unpublished_stage` 同样返回 `None`（从 S0 起跑）；
  `ArtifactStore.path_for` 只做路径拼接，不校验 attempt 命名（修复触及行 + 既有 store 行为）。
- **事实**：`--run --attempt attempt3`（或任何 typo）会在 `runtime/dist-data/<artifact>/attempt3/` 下
  写出整棵 **无 supersession、无前身校验** 的 create-once 工件树——恰是 F1 要堵的「断链」形状，只是换了
  一个不合式的身份；修复前同样的 typo 至少还携带操作员显式传入的 `--supersedes`。§6 授权 #2 信封
  「attempt 身份上限 = 2」以身份计，不合式身份是第三个身份。
- **范围判据**：生产入口带一个不合式参数即可产生 → 可达；无 BC → `IN_SCOPE_NO_BC`；`_attempt_number`
  与 `current is None → {}` 均为修复新增行 → 阻断。
- **闭合要求**：driver 在构造（`__post_init__`）或最迟在 `_supersession_kwargs`/`run_stages` 入口对
  attempt 命名 fail-closed（闭集 `attempt-<正整数>`），不合式即 `PipelineError`、零写入；具名回归修前
  必失败。修复不得改变 `attempt-1` 的既有路径与行为。

#### Non-blocking

- **F3（CLASS_3）仍未应用**，补丁原文见 R1 §3，由接受角色在下次提交应用。

### 4. 观察项（不分级、不阻断）

10. `first_unpublished_stage` 也扫描 S7/S8：attempt-2 已完整发布到 S5 时，attempt-3 会从 `g0_report` 起跑，
    随即在 `composite_manifest("splits", attempt-3)` / `require_audit` 上失败，零写入。S6–S9 属「一字不动」
    范围，且 DATA-001 CLI 的 `--through` 默认值 `g0_report` 未变，只提示操作员显式传 `--through field_catalog`。
11. 证据 §5 已写明 discover 调用形式（R1 观察项 9 已处置）。
12. 过程事实见 §0：R1 状态板改动由实现角色的提交携带，复核文件本身由本角色提交；两轮内容未被他人改动。

### 5. Missing or weak tests

- F5/F6 各需一条经生产入口、修前必失败的具名回归（闭合条件）。
- R1 §5 第 1 项（S2 端到端 `build_layout` 于巡览归档）仍未补，非阻断，随下次触及 `bind_layout` 的批次处置。

### 6. `UNITY_NA` 分类

与 R1 相同：未申请，无须附议或反对；本轮修复不触及 Unity 与采集工具。

### 7. Verdict

**`REWORK_REQUIRED`**（本停点 `stageA` **第 2 次**）。按 COORD-009 (c)：未闭 finding 集合**冻结** =
{F5（CLASS_2）, F6（CLASS_2）, F3（CLASS_3）}，交接受角色逐条裁定「范围内必修」或 `SCOPE_GAP` 记债
（记入 `docs/implementation-status.md`「范围外已知缺陷」）；`R3@stageA` 检查范围 = 冻结集 + `RED_LINE` +
修复触及行上的 CLASS_1/2，**轮 3 终局**（通过，或回用户）。

- F1/F2 已闭合并红绿核实；F5/F6 不是「旧 finding 闭合失败」，而是修复触及行上新暴露的边界。
- 无 `上轮漏检`、无 `RED_LINE`，不写消耗性门阻断机读行（状态板亦无消耗性活跃交接）。
- 本轮为 `REWORK_REQUIRED`，**不写**通过指针行。

#### Requested action

1. 接受角色：对冻结集逐条裁定（F5/F6 建议「范围内必修」——两处都是一行级 fail-closed，且不移动钉子）；
   应用 F3 补丁；归因派生时 F5/F6 记 `IN_SCOPE_NO_BC`。
2. 实现角色：按裁定修复，各绑定修前必失败的具名回归，直接交 `R3@stageA`；修复仍应只触及
   `tools/dist_data/run_pipeline.py` 与测试。
3. 用户：无需动作；授权 #2 与全部正式采集/后续阶段保持关闭。

#### 边界自查

本轮只写入 `docs/reviews/P1-VLM-DATA-002.md` 与 `docs/current-status.md`；副本内的文件回退与语义变异均已
`git checkout` 恢复并确认树干净，副本收工删除；主树 `controller/`、`Assets/`、`tools/`、`tests/`、`config/`
零改动。

## R3@stageA — 2026-09-05（终局）

### 0. 候选、检查范围与方法

- **候选**：`f8add522969bf05230024c2b97156357193849cf`（实现角色按接受角色 2026-09-05 冻结集裁定闭合
  F5/F6/I17 的批次；主树 HEAD 与候选同一提交）。
- round_candidate: f8add522969bf05230024c2b97156357193849cf
- **检查范围（COORD-009 (c) 终局轮）**：冻结集 {F5, F6, F3} + `RED_LINE` + 修复触及行上的 CLASS_1/2；另按
  接受角色复判节的裁定核实 I17（实现角色证据 §17 自查披露的 S7/S8 `splits` 读取硬绑，裁为 BC-SURVEY-4
  覆盖的范围内必修、不新增 BC）。本角色附议该裁定：I17 是 F2 续跑修复自身引入的回归，workflow §4.4 (c)
  逐字「不豁免修复自身引入的回归」，属 R3 的修复触及面。
- **修复触及行**（基线 = 上一复核轮候选 `85adf93`）：`git diff 85adf93..f8add52` 于 PLAY_GOVERNING 上恰为
  2 个文件——`tools/dist_data/run_pipeline.py`（+143/−29：`ATTEMPT_NAME` 构造期命名门、`_composite_manifest`、
  `_assert_splits_lineage`、`run_stages` 的停止界校验与 `resume_note` 重排、`_attempt_number` 去 `None` 分支）
  与 `tests/test_dist_data_survey.py`（+164：7 条经生产入口的具名回归，含两条正对照）。区间 4 个提交中
  `9c2ce62`（§17 披露）、`464f476`（本文件 R2）、`b18c288`（裁定）均纯文档；`9c2ce62` 与 `85adf93` 在
  PLAY_GOVERNING 上字节相同，故实现角色的「修前基线 `9c2ce62`」= R2 候选。`config/`、
  `tools/dist_data/contract.py`、`tools/run_grounding_survey.py` 零改动 → 7 份 create-once plan 的钉子不可能移动。
- **全量 diff**（相对 `4739a39`）仍是 R1 §0 的 27 个文件集合，只用于核实范围与红绿。
- **方法**：一次性副本 `git worktree add --detach … f8add52`；修复 diff 全文读完；修前红 = 副本内把
  `run_pipeline.py` 整体换回 `85adf93` 版本再跑候选测试，另加四次语义变异；恢复后复绿；对主树真实
  attempt-1 归档只读核对新同代门；F3 在设计文档两处逐字核对。**如实记录**：本轮第一批红/绿运行无效——
  zsh 不拆分未加引号的变量，七个用例名被当作一个参数传入 unittest，每次只得到 1 个加载错误；发现后改为
  类级用例名重做，下表为重做结果，无效日志一并留在 scratchpad。

### 1. 复核自跑的证据（不信报告数字，全部重跑）

| 项 | 实测 | 与声明比对 |
|---|---|---|
| focused `test_dist_data_survey.py`（副本，python3 / `.venv-yoloe`，discover） | **97 OK / 97 OK** | ✓ 证据 §18.7 |
| focused `test_survey_tool.py`（副本，python3 / `.venv-yoloe`，discover） | **151 OK skipped=5 / 151 OK 0 skip** | ✓ |
| 合计焦点对 | **248** | ✓ 状态板/证据「248」 |
| 修前红 0：副本内 `run_pipeline.py` 整体换回 `85adf93` × 候选 `MixedAttemptReadTest`(17)+`SupersessionResolutionTest`(6) | **failures=8, errors=3**：`test_through_pointing_at_a_skipped_stage_runs_no_stage`（F5）FAIL、`test_malformed_attempt_is_refused_at_construction`（F6）7 subTest FAIL、I17 三条 ERROR；两条正对照与其余 16 条绿 | ✓ 证据 §18.5「5 个用例打红（8 failures + 3 errors）」逐名一致 |
| 修前红 1（F5）：撤掉 `through not in runnable` 校验 | 恰 1 条 FAIL：F5 用例 | ✓ 证据 §18.6 |
| 修前红 2（F6）：撤掉构造期 `ATTEMPT_NAME` 门 | 恰 1 条用例 FAIL（7 subTest）：F6 用例 | ✓ |
| 修前红 3（I17）：`_composite_manifest` 绑回 `self.attempt` | 恰 I17 三条红（1 ERROR + 2 FAIL），错误文本逐字复现 §17 现场 `工件缺失：…/runtime/dist-data/splits/attempt-3/splits.json` | ✓ |
| 修前红 4（I17 同代门）：删去两处 `_assert_splits_lineage` 调用 | 恰 1 条 FAIL：`test_mixed_generation_splits_and_catalog_fail_before_any_write` | ✓ |
| 恢复候选后 | 23 条**全绿**；副本 `git status` 干净 | ✓ |
| 真实归档同代门核对（主树只读） | `splits@attempt-1` 信封 `inputs` 恰为 `frames_catalog@attempt-1`，sha `a2119a364c03c941e67afa841414054bcece6afed30d8bea18e0c8d1e5a9a364` = 磁盘实测 → `_assert_splits_lineage` 对正式 attempt-1 路径放行 | ✓ 证据 §18.3 |
| F3 补丁 | 设计文档第 210 行已为 `v0.3.34 为当前已接受研究设计`；M6 行过期子句已按 R1 §3 逐字替换（`诊断 Play 尚未执行` 零命中） | ✓ 裁定「已应用」 |

全套（python3 1119 / `.venv-yoloe` 1224）未重跑，理由同 R1 §1；实现者数字在证据 §18.7。

### 2. 冻结集与 I17 逐条核实

- **F5 闭合成立。** `run_stages` 先算续跑切片，再于**任何阶段执行之前**校验 `through ∈ runnable`；不在即
  `PipelineError`，零阶段、零写入，且续跑说明行在校验之后才 emit（拒绝路径零输出）。正对照
  `test_through_still_stops_at_the_named_stage_after_resume` 证明停止界落在会跑阶段上时只写出该阶段一件。
  CLI 侧 `main` 仍先以 `parser.error` 拒绝不在阶段名闭集内的 `--through`，两道门叠加。符合裁定「运行任一
  阶段前拒绝…修前会写、修后零写」。
- **F6 闭合成立。** `PipelineDriver.__post_init__` 以 `^attempt-[1-9][0-9]*$` fail-closed，拦在 store 构造之前，
  不合式身份下一件工件也写不出；7 种不合式变体（含 `attempt-01`/`attempt-0`/大小写/尾空格）逐一拒绝；
  `attempt-1` 的 `read_chain`/`_supersession_kwargs`/`resolve_predecessor` 一字未变，`attempt-10` 链正确。
  `_attempt_number` 因此无 `None` 分支，`read_chain`/`resolve_predecessor`/`first_unpublished_stage` 三处
  `current is None` 判断删除后语义等价。全仓 `PipelineDriver(` 调用方（`run_pipeline.main`、
  `test_dist_data_driver`/`_round29`/`_survey`）传入的 attempt 字面量只有 `attempt-1/2/3/10` 与用作反例的
  `attempt3`，无其它调用方受影响；焦点 248 全绿佐证。
- **F3 闭合成立**（见 §1 表末行；CLASS_3，接受角色已应用）。
- **I17 闭合成立。** S7/S8 的 `splits` 改经 `_composite_manifest()`，与 `_read_ref`/`_catalog_stream` 同一
  `resolve_read_attempt` 规则；新增 `_assert_splits_lineage()` 把 splits 信封 `inputs` 中的 `frames_catalog` ref
  与本次实际读到的 `CatalogStream.reference.as_reference()` 逐字段比对（同为 `{artifact, attempt, sha256}`
  三键，形状一致），混代即在本阶段写出任何工件之前失败。三条回归覆盖：生产默认 `through="g0_report"` 下
  一致 lineage 跑到 S9 收束且 `splits` 不重发；attempt-2 完整到 S5 时失败点名 `audit` 而非 `splits`、零工件；
  跨代混用时 `lineage 不一致`、零新工件。真实 attempt-1 归档上同代门放行（§1）。符合裁定「一致 lineage
  可完成；不一致时在发布新的 attempt 工件前失败」。

### 3. Findings

- 修复触及行上的 CLASS_1/2：**无**。
- `RED_LINE`：**无**（触及代码只涉工件读取解析、命名校验与停止界，不接触 Unity 真值或采集帧）。
- 旧 finding 闭合失败：**无**（F1/F2 于 R2 核实，F3/F5/F6/I17 于本轮核实，F4 于 R2 核实）。

### 4. 观察项（不分级、不阻断；供阶段 D 与 S6 授权时参考）

13. `require_audit` 仍按写入 attempt 读 `audit@self.attempt`（既有 S6 代码，S6–S9「一字不动」范围，
    非修复触及行）：attempt-3 从 S7 续跑时要求一份 attempt-3 的人工审计，即便 S5 产物来自 attempt-2。
    方向 fail-closed，只在 S6 授权讨论时需要知道。
14. DATA-001 CLI 的 `--through` 默认值仍是 `g0_report`；阶段 D 只执行 S0–S5 时操作员应显式传
    `--through field_catalog`，否则会在 S7 以缺 `audit` 停下（零写入，但多一条无谓报错）。
15. 正式 `field_catalog@attempt-1` 信封 `inputs` 为空（S5 lineage 债，账本已记，§2.2 第 6 条由 attempt-2 起
    补齐）；与本轮同代门无交集。
16. 本停点复核共 3 轮（R1/R2 `REWORK_REQUIRED`、R3 通过），对应 COORD-009 度量「每停点复核轮次 = 3」；
    阻断 `IN_SCOPE_NO_BC` finding 3（F1/F5/F6）、`BC-n` 1（F2）、CLASS_3 2（F3/F4）、实现自查纳入 1（I17）、
    `SCOPE_GAP` 0，供接受角色机械汇总。
17. 本轮第一批红/绿因 zsh 变量拆分无效并重做（§0），记录在案以便审计。

### 5. Missing or weak tests

- R1 §5 第 1 项（S2 端到端 `build_layout` 于巡览归档）仍未补，非阻断；建议在下一次触及 `bind_layout`
  的批次补一条生产回归。

### 6. `UNITY_NA` 分类

未申请，无须附议或反对；阶段 A 的 Unity 列保持 `NOT_RUN`（正式采集属阶段 B–D，须先有授权 #2），
COORD-005 保真检查（证据 §11）成立不变。

### 7. Verdict

**`PASS_WITH_NOTES`**（`stageA` 终局轮；观察项 13–17 均非阻断）。

- passed_candidate: f8add522969bf05230024c2b97156357193849cf
- 阶段 A 的独立复核门就此关闭；本角色不授予任何 Play、scenario/session/run ID、attempt 身份或 API/GPU。

#### Requested action

1. 接受角色：按 workflow §4.6 消费本轮通过 verdict，机械汇总归因（依据列见观察项 16），关闭阶段 A 的
   复核门并同步 `docs/implementation-status.md`；阶段 A 无 Unity 采集证据，Unity 列如实保持 `NOT_RUN`。
2. 用户：决定是否按提案 §6 授权 #2 原话打开阶段 B–D；不授权则本 work item 停在阶段 A 已复核候选上。
3. 实现角色：无待办；若授权 #2 签发，pilot 前任何新 p2/候选 plan/config 都是 PLAY_GOVERNING diff，须重走
   停点与复核（BC-SURVEY-5）。

#### 边界自查

本轮只写入 `docs/reviews/P1-VLM-DATA-002.md` 与 `docs/current-status.md`；副本内的文件回退与四次变异均已
`git checkout` 恢复并确认树干净，副本收工删除；主树 `controller/`、`Assets/`、`tools/`、`tests/`、`config/`
零改动。
