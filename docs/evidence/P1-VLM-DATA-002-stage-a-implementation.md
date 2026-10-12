# P1-VLM-DATA-002 阶段 A 实现证据（巡览工具 + DATA-001 合同增量）

Work ID: `P1-VLM-DATA-002`
Role: 实现角色（implementation）
Date: 2026-09-03
授权：用户 2026-09-03 逐字签发提案 §6 授权 #1（阶段 A 实现 + ≤3 次 COORD-005
诊断 Play；保真 PASS 后才可创建 ≤10 个首选正式 plan/scenario ID）
基线 HEAD（初版开工时）：`61a089c`；初版候选 `ceb3a19`
返工依据：接受角色 `d5705fe` 实现期裁定 BC-SURVEY-7…13（设计 v0.3.31）；
接受轮 4 `78600ce` 追加 BC-SURVEY-14/15（Overall → `STAGE_A_R4_REWORK_REQUIRED_BC14_BC15`）
返工提交：R1–R4 见 `29581f0`，R5（BC-14/15 与自查修复）见 `eda6aa9`；
本文覆盖接受轮 5 窄返工（§14）、阶段 A 停点与 COORD-005 保真（§10/§11）、
`C1@stageA` 八项闭合（§15）、`R1@stageA` 的 F1/F2（§16）、实现角色自查披露（§17）
冻结集裁定后的 F5/F6/I17 返工（§18），
以及授权 #2 下的阶段 B pilot 与阶段 C 七会话采集（§19）

> **正式身份状态**：COORD-005 保真 PASS（§11）之后，按 §2.3 步 3 与 §5 第 6 条生成了
> 七对首选正式 plan/config（§10 表）；零正式采集 Play、零 session/run ID、零 API、零 GPU、
> 零下载；用例里的计划一律生成在临时目录内。

## 1. 交付范围（提案 §7 的六个包）

| 包 | 落点 | 状态 |
|---|---|---|
| (1) 闭集增量、占位 family、逐帧 selection、S0 会话表与 allowlist | `tools/dist_data/{roots,contract,build_inventory}.py` | 完成 |
| (2) `write_composite` supersession + 六个写点 + `supersession_chain` | `tools/dist_data/{artifacts,contract,run_pipeline}.py` | 完成 |
| (3) `target_parked` 绑定、审计/证人/净空权威判定、停放阻断体 | `tools/dist_data/{bind_layout,build_catalog,run_pipeline}.py` | 完成 |
| (4) S5 精确 refs 与具名回归 | `tools/dist_data/run_pipeline.py` | 完成 |
| (5) `tools/run_grounding_survey.py` 六个子命令 + §5 第 1 条全部拒绝回归 | 新文件 2,173 行 | 完成 |
| **返工 R1** BC-SURVEY-7：S0 顶层 `root_manifest` + S1 枚举前对账 + 冻结字节夹具回归 | `roots.root_manifest()`、`contract_document()`、`build_inventory.reconcile_root_manifest()`、`run_pipeline.stage1_inventory()`、`tests/fixtures/p1-vlm-data-001-contract-attempt-1.json` | 完成 |
| **返工 R2** BC-SURVEY-13：`view_id` 语法 + 已复核 plan 成员双重校验 | `contract.parse_survey_view_id/load_pinned_survey_plan/survey_plan_view_ids/validate_selection_view_id`；S1/S2/`close`/`drive`/`verify` 全部改判 | 完成 |
| **返工 R3** BC-SURVEY-8…12 的措辞与机检对齐 | 见 §6 | 完成 |
| **返工 R4** 横扫查出的三处 fail-open + 套件在新 worktree 全 skip | 见 §12 | 完成 |
| **返工 R5** BC-SURVEY-14：`survey_acquisition` 投影 + 六入口钉子核对 | `contract.py`、`run_grounding_survey.py`、`build_inventory.py`、`run_pipeline.py` | 完成 |
| **返工 R5** BC-SURVEY-15：中心命中改半开 | `bind_layout.evaluate_parked_witness` | 完成 |
| **返工 R5** 对抗验证查出的 6 项 material | 见 §12 | 完成 |
| **返工 R6** BC-SURVEY-14 两条 fail-open：重入与 `verify` 的完整所钉 plan 核对 | `assert_archived_pinned_plan`、`verify_session` | 完成 |
| **返工 R6** BC-SURVEY-16/18：按冻结次序穷举全部候选，只给首个合法者建身份 | `resolve_anchor_plan`、`resolve_anchor_sequence`、`write_plan`、`install_diagnostic`、CLI `anchors` | 完成 |
| **返工 R7** `C1@stageA` 的 4 项不满足 + 4 项关注项 | 见 §15 | 完成 |
| **返工 R8** `R1@stageA` 的 F1/F2 两条阻断 + F4 补丁 | `run_pipeline.resolve_predecessor()`、`first_unpublished_stage()`、`run_stages(resume=True)` | 完成 |
| **(6) 诊断 Play 保真 → 停点自证** | §11 保真 PASS（诊断 Play 1/3）；§10 四项自证 + 逐 BC 证据指针；7 份正式 plan/config | **完成——本批到达 §4.3.1 停点** |

改动文件：

```
 M tools/dist_data/artifacts.py
 M tools/dist_data/bind_layout.py
 M tools/dist_data/build_catalog.py
 M tools/dist_data/build_inventory.py
 M tools/dist_data/contract.py
 M tools/dist_data/roots.py
 M tools/dist_data/run_pipeline.py
 ?? tools/run_grounding_survey.py
 ?? tests/test_survey_tool.py
 ?? tests/test_dist_data_survey.py
 ?? docs/evidence/P1-VLM-DATA-002-stage-a-implementation.md
 ?? tests/fixtures/p1-vlm-data-001-contract-attempt-1.json   ← 返工新增（BC-SURVEY-7 明文允许「逐字 bytes fixture」）
```

## 2. BC-SURVEY-1…18 的逐条落点

| BC | 落点 | 机检 |
|---|---|---|
| BC-SURVEY-1（`B'` 已含 +3 m 顶面；绕行只再加 1 m；三段闭集相交、`H_safe ∈ [8,30]`、每端点 ≤ 33 m） | `contract.SURVEY_DETOUR_EXTRA_M = 1.0`、`transition_waypoints` | `test_intersecting_segment_is_detoured_not_passed_through`（断言 `safe_world_y == max_y + 1.0`）、`test_h_safe_above_thirty_is_unreachable`、`test_detour_endpoint_beyond_the_tether_is_unreachable` |
| BC-SURVEY-2（审计早于 FrameWriter；`drive` 观察首帧后、发任何控制前核对；零帧 `close` 接受 pre-command refusal log） | `DriveSession.verify_preconditions` 在 `run()` 里位于任何 `send_*` 之前；`close_session` 的零帧接受集 = `{None, DRIVE_REFUSED_AUDIT, ABORTED_NO_FRAMES}` | `DrivePreconditionTest` 四条，每条都断言 `runtime/body_command.json` **未被写出**；`test_zero_frame_close_accepts_a_pre_command_refusal_log`；`test_zero_frames_with_a_post_command_terminal_is_fail_closed` |
| BC-SURVEY-3（诊断零新 ID，沿用 default 的 `scenario_id`，序号只命名 hold） | `install_diagnostic` / `collect_diagnostic` | `DiagnosticTest` 五条，含「不建 plan 目录、不建 `scenario.p1-vlm-survey-*.json`、不写活动标记」 |
| BC-SURVEY-4（读取 attempt 与写入 attempt 解绑，ref 来自实际读取） | `PipelineDriver._supersession_kwargs` 只影响写入侧；`_read_ref` 交出实际 ref | `Attempt3ReadRefTest` 两条 |
| BC-SURVEY-5（plan 存 `config/p1-vlm-survey-plans/<identity>/plan.json`，create-once、纳入版本控制） | `plan_path_for` / `_create_once_json` | `test_plan_rerun_is_byte_idempotent`、`test_create_once_rejects_different_bytes` |
| BC-SURVEY-6（两条授权原话的信封；缺项按 0；越界回用户） | `MAX_FORMAL_PLAY=10` / `MAX_PLAN_IDENTITIES=10` / `MAX_DIAGNOSTIC_PLAY=3` | `test_exhausted_envelope_is_rejected_and_does_not_count`、`test_plan_identity_envelope_caps_at_ten`、`test_diagnostic_envelope_caps_at_three` |
| BC-SURVEY-7（S0 顶层 `root_manifest`，S1 枚举前对账，allowlist 恰四键且以冻结字节比对） | `roots.ROOT_MANIFEST_ENTRY_FIELDS`/`root_manifest()`；`contract_document()` 无条件写入；`CONTRACT_PAYLOAD_SUPERSESSION_ALLOWLIST` 四键；`build_inventory.reconcile_root_manifest()`（在 `assert_empty_dirs` **之前**）；`run_pipeline.stage1_inventory` 缺键即 `PipelineError` | `ContractAllowlistTest`（5 条，前侧取自 5,014 B / sha `1d1cea17…6ddf` 夹具）、`RootManifestProjectionTest`（5 条）、`RootManifestReconciliationTest`（5 条）、`Stage1ContractGateTest`（2 条） |
| BC-SURVEY-8（三轴 4 m 闭集扩张；措辞不得称「更保守」） | `_clear_of_obstacles` docstring 与判据 | `ParkedObstacleMarginTest`（3 条，含三轴闭边界与越界放行） |
| BC-SURVEY-9（§8 只冻结锚点坐标/序号/顺序；复算只作诊断；不豁免硬门） | `ANCHOR_TABLE` 注释、`recompute_anchor_candidates` docstring 与 `note` | `test_kept_positions_satisfy_the_endpoint_extremum_assertions`、`test_full_plan_has_the_frozen_view_shape` |
| BC-SURVEY-10（`sweep_proxy` 命名与闭集顺序；不得改变既有判定） | `contract.DYNAMIC_TARGET_SCHEMAS`；`build_catalog.target_blocker_from_truth` 守卫 | `SweepProxyNamingTest`（3 条） |
| BC-SURVEY-11（`VALID_SURVEY` 唯一插入点；既有相对顺序不变） | `contract.USAGE_CLASSES` | `UsageClassOrderTest`（3 条） |
| BC-SURVEY-12（整帧 4-邻接、右/下开框、`(area, box)` 取最大，平手取字典序较大者） | `bind_layout.red_components`、新的 `select_witness_component` | `WitnessAlgorithmTest`（4 条）、`WitnessPixelTest`（2 条，需 Pillow） |
| BC-SURVEY-13（`view_id` 完整语法 + 已复核 plan 成员；禁止 `w/` 前缀） | `contract.parse_survey_view_id`/`load_pinned_survey_plan`/`survey_plan_view_ids`/`validate_selection_view_id`；`is_survey_witness_view` **已删除**；S1 `_survey_selection`、S2 `_survey_selection_rows`、`classify_frames`（必传闭集）、`close_session`、`drive_session`、`verify_session` | `ViewIdSyntaxTest`（8 条）、`SurveyPlanViewIdsTest`（4 条）、`PlanPinTest`（7 条）、`ViewIdEnforcementTest`（8 条） |
| BC-SURVEY-14（S0 顶层 `survey_acquisition`；差异键恰五；钉子贯穿 plan/manifest/S0/当前投影，六个入口各自核对） | `contract.survey_acquisition()`（自动枚举全部公开 `SURVEY_*`，89 个常量）、`survey_acquisition_sha256()`、`assert_survey_acquisition_pin()`；驱动器的锚点表/出生高度/信封/schema id 全部改为合同转发，模块内不再有决定正式结果的字面量；`prepare` 核对 plan 钉子后写入 manifest，`load_pinned_survey_plan` 双侧核对（覆盖 `drive`/`close`/`verify`/S2），`close` 重入分支经 `_assert_archived_acquisition_pin`，S1 经 `reconcile_survey_acquisition` | `SurveyAcquisitionProjectionTest`（6 条，含「漏投影即失败」与「改一个常量钉子就变」）、`SurveyAcquisitionReconciliationTest`（3 条）、`AcquisitionPinTest`（7 条，逐入口 fail-closed）、`Stage1NullKeyTest`（3 条） |
| BC-SURVEY-15（中心命中半开 `x0 ≤ cx < x1 ∧ y0 ≤ cy < y1`） | `bind_layout.evaluate_parked_witness` | `WitnessCentreContainmentTest`（5 条：右边界、下边界、左/上边界各一组，加生产源码半开断言与右/下开框机检） |
| BC-SURVEY-16（冻结顺序穷举全部候选取首个合法者；无合法候选即 `PLAN_POSITION_UNREACHABLE`，不建 ID、不耗 Play） | `resolve_anchor_plan`（只读穷举，返回逐候选拒绝记录）、`resolve_anchor_sequence`、`write_plan`（`candidate` 省略即穷举）、`install_diagnostic`、CLI `anchors` 子命令 | `AnchorTableReachabilityTest`（8 条：十锚点枚举计数、5/8 逐候选全量无效、10 空集、七锚点首个合法、冻结序列、候选复用等价、不可达零身份） |
| BC-SURVEY-17（`CLARIFY`：`survey_acquisition` 顶层三键 + `constants` 恰 89 项） | `contract.survey_acquisition()` | `SurveyAcquisitionProjectionTest.test_top_level_closed_set_is_exactly_three_keys` / `test_constants_closed_set_is_exactly_eighty_nine`；另用脚本把 BC-17 逐字列出的 89 名与投影双向比对，两侧差集均空 |
| BC-SURVEY-18（`CLARIFY`：全部候选闭集 = `parked_candidates` 有序输出，逐锚点计数 `53/209/60/74/135/248/62/128/217/0`） | 同 BC-16 | `AnchorTableReachabilityTest.test_enumeration_counts_match_the_frozen_closed_set`（含 `candidate_index` 连续 1..N 无洞） |

## 3. 提案 §5 第 1 条点名的拒绝回归（逐条对照）

| §5 第 1 条项 | 用例 |
|---|---|
| `plan` 重跑字节幂等 | `PlanWriteTest.test_plan_rerun_is_byte_idempotent` |
| `prepare`/`close`/completion create-once | `test_manifest_is_create_once`、`test_create_once_rejects_different_bytes`、`test_completion_is_create_once_and_matches_the_tree` |
| 帧目录非空 | `test_non_empty_frames_directory_is_rejected` |
| 活动会话冲突 | `test_active_session_conflict_is_rejected` |
| 信封用尽 | `test_exhausted_envelope_is_rejected_and_does_not_count` |
| 位置落入 `B'` | `test_position_inside_an_expanded_box_is_raised_or_dropped`、`test_dropped_position_reports_every_attempted_height` |
| 线段/AABB 相交未绕行 | `test_intersecting_segment_is_detoured_not_passed_through` |
| `H_safe > 30` 未判不可达 | `test_h_safe_above_thirty_is_unreachable` |
| 系留 > 33 m 位置 | `test_detour_endpoint_beyond_the_tether_is_unreachable`、`test_raising_recomputes_the_ring_radius_each_step` |
| 端点极值断言 | `test_kept_positions_satisfy_the_endpoint_extremum_assertions` |
| 停放段方向非 (0,0,1) | `test_parked_segment_direction_is_exactly_plus_z` |
| 审计缺失/非零时 `drive` 拒绝 | `DrivePreconditionTest` 三条 |
| 逐帧有效性（窗内早期帧朝向 > 3° 被降级） | `test_early_in_window_frame_off_bearing_is_downgraded` |
| selection 与归档 jpg 集合不一致 | `test_verify_rejects_a_selection_that_lost_a_frame`、`test_missing_selection_row_is_fail_closed` |
| 零帧 `close` | `test_zero_frame_close_archives_only_the_session_directory` |
| `close` 三种重入 | `test_reentry_from_staging_residue`、`test_reentry_when_completion_is_missing`、`test_reentry_after_completion_with_leftover_source`、`test_reentry_moves_foreign_residue_into_a_hold` |
| 零帧且只有 pre-command refusal log | `test_zero_frame_close_accepts_a_pre_command_refusal_log` |
| `CLOSE_TREE_MISMATCH` 不删文件 | `test_tree_mismatch_keeps_every_file` |

§5 第 4 条（S0–S5 attempt-2/3）由 `tests/test_dist_data_survey.py` 覆盖，含点名的
`test_stage5_inputs_are_actual_read_refs`。

## 4. 夹具策略（为何算「生产路径产出」）

没有 Unity 的情况下，「Unity 侧」只保留两件事，其余全部走生产路径：

1. **帧字节与 sidecar 模板取自真实归档帧**（`runtime/frames.1b-diagnostic-hold`
   的首帧及其 sidecar），仿真只替换位姿相关字段；替换用的基底约定
   （`right = normalize(cross(worldUp, forward))`、`up = normalize(cross(forward, right))`、
   `fx = fy = (height/2)/tan(vfov/2)`、`cx,cy = 半画幅`）是**读归档字节实测**得到的，
   实测样本 `runtime/test-results/p1-m3-body-001-arm-b-trial-1-post-run/frames/frame_0000000730.json`
   （逐分量与 `camera_right_world`/`camera_up_world`/`intrinsics_px` 吻合到 1e-6）。
2. **控制指令由工具本身经 `controller.body_entry` / `controller.gimbal_entry` 真实写盘**，
   仿真按 `tethered-drone-control/v1` 消费。

plan、场景配置、manifest、selection、tree、completion、归档一律由
`tools/run_grounding_survey.py` 自己产出——不手写任何一份 JSON。时间用虚拟时钟，
工具里的时限常量一字未改。`DriveCase.trim_plan` 只对**生产产出的** plan 做子集
选择（保留的位置/视角/航点全是原始字节），不改任何几何或阈值；完整形状由
`test_full_plan_has_the_frozen_view_shape` 单独断言。

## 5. 实际运行的命令与结果（`R1@stageA` 返工后）

```
python3      focused test_dist_data_*.py   → 527 tests OK (skipped=9)
.venv-yoloe  focused test_survey_tool.py   → 151 tests OK
python3      全套                          → 1112 tests, errors=9, skipped=20
.venv-yoloe  全套                          → 1217 tests, failures=1, errors=1, skipped=1
```

调用形式（复核观察项 9）：一律 `python3 -m unittest discover -s tests -p '<pattern>' -q`，
`.venv-yoloe/bin/python` 同形；无 `-v`，原始输出留在会话 scratchpad。

接受/复核复跑的那一对（`test_dist_data_survey.py` 90 + `test_survey_tool.py` 151）
= **241** 条。**新增失败为零**：两个解释器的失败集合与改前基线逐名相同。

用例计数：基线 972 → … → C1 返工 1209 → 本批 **1217**。

**`R1@stageA` 返工的三次反向变异**（每次还原后复测全绿）：

| 变异 | 打红的用例 |
|---|---|
| F1：前身缺席即静默省略（退回 `{}`） | `test_an_unresolvable_predecessor_is_refused_not_silently_omitted` |
| F1：缺归因不再拒绝 | `test_a_missing_reason_is_refused` |
| F2：生产入口恒从 S0 起（撤掉续跑） | `MixedAttemptReadTest` 的 5 条续跑用例 |

## 6. 原「显式取定的自由度」——已由 BC-SURVEY-8…13 全部裁定

初版把五项合同未给定的取值当作实现自由度披露（§9 的五项请求另计）。接受角色
**没有**照单接受，而是逐条冻结为 BC，其中两条改变了实现：

| 初版取定 | 裁定 | 本批落点 |
|---|---|---|
| 证人分量 4-邻接、整帧扫描（自述「更保守」） | **BC-SURVEY-12** 冻结算法；措辞不得称「更保守」，且只冻结正式数据前的算法，不声称像素门已过 | `bind_layout.red_components` docstring 改写；`select_witness_component` 提为具名函数，写死「面积同值取字典序较大 box」；`WitnessAlgorithmTest` 四条 |
| §2.1(f)(iv)「扩 4 m」取三维读法（自述「三条判据里最保守」） | **BC-SURVEY-8**：三轴各向外 4 m 闭集扩张是本合同的**唯一**语义，不得称作与纯水平判据的比较 | `_clear_of_obstacles` docstring 改写；`ParkedObstacleMarginTest` 三条（含三轴闭边界） |
| `VALID_SURVEY` 插在 `VALID_PARENT_HOLD` 之后 | **BC-SURVEY-11** 冻结该唯一插入点与既有相对顺序 | `UsageClassOrderTest` 三条，含 lineage primary 顺序与表序一致 |
| 给无名的扫掠代理分支命名 `sweep_proxy` | **BC-SURVEY-10** 采纳该名，闭集顺序冻结为 `m3, scouting, sweep_proxy, target_parked`，且命名不得改变既有判定 | `SweepProxyNamingTest` 三条，证明代理分支仍由 `schema_family is None` 触发、命名没有变成可传入的 schema 值 |
| 自定 `view_id` 语法，S2 以 `w/` 前缀认证人 | **BC-SURVEY-13 判为缺陷**：合法值必须来自 manifest 所钉、哈希相符的已复核 plan；前缀判定明令禁止 | 见 §12 |

## 7. §8 表 2/表 3 的复算对账（BC-SURVEY-9 裁定后的口径）

**BC-SURVEY-9 冻结的只有十个锚点的坐标、序号与使用顺序。** `2,684`、逐锚点覆盖
数、`99/101` 与候选生成叙述都是规划估计，**不是门，也不是可引用证据**。锚点常量
**不豁免** §2.1(c)–(f) 的位置、转场、停放候选、系留与道路审计硬门。

> **更正**：本节初稿写「`build_plan` 对表内每个锚点照跑全部硬门，
> `test_kept_positions_satisfy_the_endpoint_extremum_assertions` 逐位置复核」——**失实**。
> 该用例只跑锚点 1。逐锚点实跑后的真实结果见下表，并已由
> `AnchorTableReachabilityTest` 钉住。

**逐锚点穷举实测（BC-SURVEY-18 的闭集，走生产 `parked_candidates` + `build_plan`）：**

| 锚点 | 候选枚举数 | 结果 |
|---|---|---|
| 1、2、3、4、6、7、9 | 53 / 209 / 60 / 74 / 248 / 62 / 217 | 候选 **1** 即首个合法 plan |
| 5 | 135 | **全部 135 个候选逐一求 plan，无一有效** |
| 8 | 128 | **全部 128 个候选逐一求 plan，无一有效** |
| 备 10 | 0 | 空集，`build_plan` 直接拒绝 |

BC-SURVEY-16 已就此裁定：当前可达序列为 **1/2/3/4/6/7/9**，5/8/10 丢弃，规划性的
`99/101` 不作下调后的新承诺；F1–F4、pilot 与 §5 五项批次门不变，七锚点若最终不能过门
仍只能落 `SURVEY_FLOORS_UNREACHABLE` 回用户。实现侧据此把身份创建改为
「按冻结次序穷举全部候选、取首个过硬门者」，无合法候选即记 `PLAN_POSITION_UNREACHABLE`
且**不创建任何 ID、不消耗 Play**。

`install_diagnostic` 此前**不检查** `plan["valid"]`：对锚点 5/8 它会返回成功并把无效
计划派生的配置装进 `runtime/scenario_config.json`，正是「锚点常量豁免硬门」。已修
（`DiagnosticGateTest` 两条）。

诊断复算如实记录如下，**不参与任何判定**：

- 表 2 声明的 2,684 个候选点复算得 **2,393**（按表内锚点自身的网格相位
  x ≡ 2、z ≡ 1 mod 3）；试过的其它相位与外扩值（3/2/1.5 m、含或不含 y 判定）
  落在 2,249–3,451，无一等于 2,684。
- 表 2 的锚点 8 `(−10, −2)` 与备 10 `(191, 193)` 不满足该规划生成叙述：两点分别落在
  `Natures_Grass Tile (9)` / `(3)` 的外扩框内。两者都是**零高度地面贴片**
  （y ∈ [−2.9e-6, 2.9e-6]），而飞行位置的净空判定是三维的、世界高度 ≥ 8.2 m，
  远高于贴片扩展框顶面 3.0 m——所以这两点对任何飞行位置的判定都没有影响。
- 表 3 的候选数量级吻合：锚点 5 复算 292（表报 292）、锚点 6 复算 430（表报 430）
  逐位相同；锚点 1/2/3/4/7/8 复算 240/347/134/126/249/153，表报
  243/354/157/186/250/193。锚点 1 的「最近候选距锚点 8.9 m」与复算的 8.944 m 吻合。

`recompute_anchor_candidates` 只输出上述差异，任何不等都不会使 `plan` 或 pipeline
失败，也不会改写锚点表。

## 8. 已知限制与未验证项

- **零 Unity 验证**：本批全部证据来自 Python 侧。`drive` 的真实收敛行为、云台
  slew 速率、Unity 端 `retained_frame_count = 10000` 的实际保留、以及渲染保真，
  都**未经任何 Play 验证**。这正是 §2.3 步 2 的 COORD-005 人眼保真检查要解决的。
- **证人像素判定未在真实巡览帧上跑过**：像素侧只有合成红斑用例
  （`WitnessPixelTest`，需 Pillow），真实分母（≥ 50 帧）要等正式采集。
- **`survey_sessions` 与 attempt-2 未执行**：S0–S5 正式 attempt-2/3 属阶段 D，
  未授权、未执行。本批只证明合同增量的代码路径。
- `python3` 缺 opencv、`.venv-yoloe` 缺 opencv-contrib，两项均为既有环境事实。

## 9. 「待裁定」台账

**初版的五项请求已全部答复**（提案 §Pending rulings：「当前无未答项」）：
BC-SURVEY-7 裁定根清单键必须存在（否定了初版「按 vacuous 处理」的取定）、
BC-SURVEY-8 裁定三轴 4 m、BC-SURVEY-9 裁定锚点表只冻结坐标/序号/顺序、
BC-SURVEY-10 采纳 `sweep_proxy`、BC-SURVEY-11 冻结 `VALID_SURVEY` 的插入点。
证据 §6 中另外两项会改变结果的自由度由 BC-SURVEY-12/13 收束。

**上一轮登记的那一项已由 BC-SURVEY-14 答复**：接受角色选了选项 (a)——新增顶层
`survey_acquisition`，差异键在集合上由四键扩为五键，并要求钉子贯穿
plan/manifest/S0/当前投影，在 `prepare`/`drive`/`close`（含重入）/`verify`/S1/S2 六个
入口分别核对。已实现，见 §2 的 BC-SURVEY-14 行。

**上一轮登记的锚点可达性一项已由 BC-SURVEY-16 答复**：接受角色只读实跑补足了我
「前六个候选」的不足——5/8 的全部 135/128 个实际候选均无有效 plan，10 无候选——并
裁定当前可达序列为 1/2/3/4/6/7/9，5/8/10 丢弃，`99/101` 不作下调后的新承诺，F1–F4
与 §5 五项批次门不变。BC-SURVEY-18 进一步把「全部候选」的闭集定死为
`parked_candidates` 的有序输出与逐锚点枚举计数。已实现，见 §2 的 BC-SURVEY-16/18 行。

**本轮无新增待裁定项。** 提案 §Pending rulings 当前无未答项。

## 10. §4.3.1 停点自证（阶段 A 稳定候选）

保真门已过（§11），正式 plan/config 已生成并纳入候选。四项条件逐条自证：

**条件 1 — 实现范围和接口已冻结。** 范围 = 提案 §7 六个包 + BC-SURVEY-1…18。新增
`tools/run_grounding_survey.py`；改 `tools/dist_data/{roots,contract,build_inventory,
bind_layout,build_catalog,artifacts,run_pipeline}.py`；新增两份测试与
`tests/fixtures/p1-vlm-data-001-contract-attempt-1.json`（BC-SURVEY-7 明文允许）；
新增 7 份正式 plan/config（BC-SURVEY-5/16）。对外接口冻结点：S0 payload 顶层键
（差异恰五）、附录 A 根表、`view_id` 语法、采集协议投影，四者均已进 S0 哈希面。
**不动**：`Assets/**` 零 C#、`config/scenario.default.json`、既有冻结配置、既有归档与
正式 attempt-1、`FLOORS`、θ_occ、站位分箱、pHash、切分规则、S6–S9。

**条件 2 — 相称的实现者测试/编译通过。** 见 §5；停点全量各跑一次，新增失败为零。

**条件 3 — 已知 Unity 失败已修复并聚焦复测。** 无 Unity 失败：诊断 Play Console
无报错，bootstrap 路线合法性审计 `CLEAR` / 零违规（§11）。本批零 C# 改动。

**条件 4 — 复核范围、状态板、候选 commit 与未验证风险已更新。** 复核范围见下表；
状态板同批更新；未验证项见 §8；范围外披露见 §7。

### 逐 BC 证据指针（COORD-009：按 BC 编号附具名测试/工件/命令）

| BC | 证据指针 |
|---|---|
| 1 | test:`AnchorTableReachabilityTest`、`PlanGeometryTest.test_intersecting_segment_is_detoured_not_passed_through` / `test_h_safe_above_thirty_is_unreachable` / `test_detour_endpoint_beyond_the_tether_is_unreachable` |
| 2 | test:`DrivePreconditionTest`（4 条，每条断言 `body_command.json` 未写出）、`ZeroFrameCloseTest.test_zero_frame_close_accepts_a_pre_command_refusal_log` |
| 3 | test:`DiagnosticTest`（5 条）；artifact:`runtime/frames.p1-vlm-survey-diagnostic-1-hold/`（§11，零新 ID） |
| 4 | test:`Attempt3ReadRefTest`（2 条） |
| 5 | test:`PlanWriteTest.test_plan_rerun_is_byte_idempotent` / `test_create_once_rejects_different_bytes`；cmd:七身份重跑后聚合 SHA 不变（§5） |
| 6 | test:`test_exhausted_envelope_is_rejected_and_does_not_count`、`test_plan_identity_envelope_caps_at_ten`、`test_diagnostic_envelope_caps_at_three` |
| 7 | test:`ContractAllowlistTest`(6)、`RootManifestProjectionTest`(5)、`RootManifestReconciliationTest`(5)、`RootManifestFieldSetTest`(4)、`Stage1ContractGateTest`(2)、`Stage1NullKeyTest`(3)；artifact:`tests/fixtures/p1-vlm-data-001-contract-attempt-1.json` 5,014 B / `1d1cea17…6ddf` |
| 8 | test:`ParkedObstacleMarginTest`(3) |
| 9 | test:`AnchorTableReachabilityTest`、`DiagnosticGateTest`(2)；artifact:`recompute_anchor_candidates` 只作诊断（§7） |
| 10 | test:`SweepProxyNamingTest`(3)、`ContractAllowlistTest.test_dynamic_target_schema_closed_set_gains_target_parked` |
| 11 | test:`UsageClassOrderTest`(3) |
| 12 | test:`WitnessAlgorithmTest`(4)、`WitnessPixelTest`(2)、`WitnessScanExtentTest`(3) |
| 13 | test:`ViewIdSyntaxTest`(8)、`SurveyPlanViewIdsTest`(4)、`PlanPinTest`(7)、`ViewIdEnforcementTest`(8) |
| 14 | test:`SurveyAcquisitionProjectionTest`(8)、`SurveyAcquisitionReconciliationTest`(3)、`AcquisitionPinTest`(7)、`ArchivedPinnedPlanTest`(11) |
| 15 | test:`WitnessCentreContainmentTest`(5) |
| 16 | test:`AnchorTableReachabilityTest`(8)；artifact:7 份 plan/config，可达序列 1/2/3/4/6/7/9 |
| 17 | test:`SurveyAcquisitionProjectionTest.test_top_level_closed_set_is_exactly_three_keys` / `test_constants_closed_set_is_exactly_eighty_nine`；cmd:与 BC-17 逐字 89 名双向差集为空（§5） |
| 18 | test:`AnchorTableReachabilityTest.test_enumeration_counts_match_the_frozen_closed_set` |

### 正式 plan/config（BC-SURVEY-5/16，本候选新增）

| 计划身份 | 候选 | 保留巡览位置 | 视角 | 丢弃位置 |
|---|---|---|---|---|
| `p1-vlm-survey-a1-p1-c1` | 1 | 14 | 224+3 | 0 |
| `p1-vlm-survey-a2-p1-c1` | 1 | 12 | 192+3 | 2 |
| `p1-vlm-survey-a3-p1-c1` | 1 | 14 | 224+3 | 0 |
| `p1-vlm-survey-a4-p1-c1` | 1 | 14 | 224+3 | 0 |
| `p1-vlm-survey-a6-p1-c1` | 1 | 14 | 224+3 | 0 |
| `p1-vlm-survey-a7-p1-c1` | 1 | 14 | 224+3 | 0 |
| `p1-vlm-survey-a9-p1-c1` | 1 | 11 | 176+3 | 3 |

七份重跑逐字节幂等（聚合 SHA `5707b12c…fcb4` 前后一致）；专用配置越出 §2.1(b) 五字段的
为 **0**，`scene_adjustments` 与 default 逐字相同；七份 plan 的
`survey_acquisition_sha256` 全部等于当前投影 `b4ad4f7b…80bf`。

### 真实仓库上的只读 S1 preflight（零写入）

`records = 30110`（DATA-001 正式跑时 29,923，+187 = 本次诊断 hold），
**`zero_match = 0`、`multi_match = 0`**——187 张诊断帧被附录 A.3 恰一匹配；
`included_images = 23706` 与正式跑一致，即诊断帧**没有**混进母集；
`EXCLUDED_DIAGNOSTIC_CHANNEL = 315`（既有 1b hold 128 + 本次 187）。
跑后 `runtime/dist-data/` 仍 92 个文件、`contract/attempt-1/contract.json` 仍是
`1d1cea17…6ddf` 且与提交的夹具逐字节相同。

### 复核范围（交 `R1@stageA`）

1. BC-SURVEY-1…18 逐条落点与上表证据指针；
2. `survey_acquisition`/`root_manifest` 两条冻结面与六个入口的 fail-closed；
3. `view_id` 的语法 + 已复核 plan 成员双重校验（S1/S2/`close`/`drive`/`verify`）；
4. 7 份 plan/config 的几何、五字段边界与钉子；
5. 本文件 §12/§13 记录的自查与对抗验证修复；
6. §8 未验证项与 §7 范围外披露。

### 下一步

接受角色 `C1@stageA` 异源核对表（无退回权，不满足行随候选附给复核）→ 复核 `R1@stageA`。
**授权 #2 仍未签发**，正式采集 Play、session/run ID、S0–S5 attempt-2/3、阶段 B–D
全部关闭。

## 11. COORD-005 人眼保真检查

**结论：PASS**（诊断 Play #1，锚点 1，2026-09-03）。

| 项 | 值 |
|---|---|
| 采集前 HEAD | `6bf3582`，`git status --porcelain` 0 项 |
| 诊断配置 | 只活在 `runtime/scenario_config.json`；`scenario_id` 逐字沿用 `deterministic-loop-default`，**零新 scenario/session/run ID**（BC-SURVEY-3） |
| 锚点 / 停放点 | `anchor_world_m` (206.0, 0.2, 55.0)；`P_k` (198.0, 0.20000043511390686, 59.0)，`speed_mps = 0`，停放段方向逐位 (0, 0, 1) |
| Play | 用户进入约 30 s，**未跑驱动器**；Console 无报错（用户原话「无报错」） |
| bootstrap 路线合法性审计 | `runtime/road_scene_audit.json`：`status = CLEAR`，`road_violation_count = 0`，`obstacle_violation_count = 0`，`scenario_id` 相符 |
| 诊断 hold | `runtime/frames.p1-vlm-survey-diagnostic-1-hold/`，187 张 jpg + sidecar；附录 A.3 恰一匹配 → `DIAGNOSTIC_HOLD` / `EXCLUDED_DIAGNOSTIC_CHANNEL`，`mother`/`floor`/`test` 三项资格均为 false |
| 样帧 1（停放目标同框） | `runtime/frames.p1-vlm-survey-diagnostic-1-hold/frame_0000000000.jpg`，SHA-256 `e431775fbc3e8ded9f28c837067f68fb4b2020f322088b4f020789a9bbdd6105` |
| 样帧 2（≥3 辆目录车同框 + 零转动对照） | `runtime/frames.p1-vlm-survey-diagnostic-1-hold/frame_0000000175.jpg`，SHA-256 **同上**（见下） |
| 确认人 | 用户（本会话逐字：「朝向一致」「目前四个框选中的都是车」） |
| 信封 | 诊断 Play 用 1 / 上限 3；零正式 Play、零 session/run ID、零 API/GPU |

**样帧内容（标注版只生成在会话 scratchpad，不进仓库）**：青框 = 停放目标投影框
（短边 43.1 px）；绿框 = 状态 `OK` 的目录车 `Vehicle_Pick up Truck_color01 (1)`
（98.2×67.4 px）与 `Vehicle_Taxi`（115.4×54.4 px）；橙框 = 被画面右缘截断的
`Vehicle_Container_color02 (1)`（`TRUNCATED`，可见 28.7×92.8 px）。用户对**四个框**
逐一确认「都是车」，即停放目标与三辆目录车的渲染与运行时语义一致。

> **如实记录的边界**：「≥ 3 辆目录车同框」在本帧是 **2 辆完整 + 1 辆边缘截断**。
> 实现角色没有自行判定该截断辆是否计数，而是把两种走法（改用锚点 3 重拍 / 就用本帧）
> 摆给用户，用户选择先看图，看后确认四个框都是车。此处按用户的逐张确认记 PASS，
> 并把「2 完整 + 1 截断」的事实原样留在记录里，供接受/复核角色自行判定。

**机检佐证：187 帧逐字节相同。** 对 hold 内全部 187 张 jpg 求 SHA-256，互异值只有
**1 个**（`e431775f…6105`），跨 `simulation_time_s` 0.181 → 37.383 s（37.20 s）；
sidecar 的 `camera_position_world_m` 与 `camera_forward_world` 首末完全一致
（(206.0, 25.2, 55.0) / (0, −1, 0)）。这是 §2.1(f)「停放段方向恰为世界 +z ⇒
`LookRotation(+z)` = 单位四元数 ⇒ 从第 0 帧起旋转恒为单位四元数」的**首次实测**
证明——此前只有读 `LoopTargetVehicle.Step` 源码得出的推证。相机与云台同时零漂移，
也确认了「不跑驱动器时机身停在出生点」。

**保真 PASS 解锁的下一步**（§2.3 步 3、§5 条件 6）：允许创建首选正式 plan/config
并纳入首个稳定候选；BC-SURVEY-16 之后可达锚点为 1/2/3/4/6/7/9，故至多 **7** 个
正式 plan/scenario ID。

## 12. 返工期间自查出的缺陷（不在 BC 之内，但同类）

BC-SURVEY-7/13 惩罚的是两种模式：**自证循环的测试**与**宽松分类**。按同一标准
横扫本批自有文件，另找到四处，一并修复：

1. **整份巡览用例在新鲜 worktree 里会全部 skip。** `TEMPLATE_FRAME_DIR` 原指
   `runtime/frames.1b-diagnostic-hold`，而 `runtime/` 是 gitignored 的：复核角色
   在干净 worktree 里跑会得到 `Ran 73 tests … OK (skipped=73)`——一份什么都没执行
   的绿色套件，而证据却把这 73 条计入回归数。改指**已纳入版本控制**的
   `docs/evidence/P1-M3-BODY-001-1b`（与 hold 内同名帧逐字节相同），并把「夹具缺失」
   从 skip 改成硬失败。**实测**：在 `git worktree add` 出来的干净副本里（`runtime/`
   只有 `README.md`）现在是 `Ran 73 … OK (skipped=2)`，2 项是既有的 Pillow 门。
2. **转场记录的 `.get("reachable")` 真值测试 + 宽松回退。** 缺记录或缺该键时原实现
   直飞终点，等于把 BC-SURVEY-1 算出的绕行几何整条丢掉、径直穿越扩展框。改为
   缺键即拒绝、保留位置无可达转场即拒绝（`PlanIntegrityTest` 两条）。
3. **重入分支 2 的终态默认成功且不查闭集。** 归档 `selection.json` 缺
   `session_terminal` 时原实现取 `CLOSED_OK`，并把它写进 **create-once** 的
   `completion.json`——之后再也改不了。改为缺键/越闭集一律拒绝（`PlanIntegrityTest`
   两条）。
4. **未知 `kind` 落进巡览分母。** `classify_frames` 原用 `else` 兜底，任何非
   `witness` 的 kind 都会进入 90% 达成率门的分母。改为闭集判定
   （`test_classify_frames_rejects_an_unknown_kind`）。

另有一项**未自行处置**、已登记为待裁定：本批新增的 `SURVEY_*` 常量未进入 S0 哈希
冻结面。接受角色以 BC-SURVEY-14 采纳了选项 (a)，已实现。

## 13. 接受轮 4 前的对抗性验证查出的缺陷（9 个独立复核者，0 阻断、6 项 material）

在接受轮 4 落地**之前**，我对 `29581f0` 起了一轮专门想推翻各条 BC 的验证。其中一条与
接受角色独立查到同一处：`evaluate_parked_witness` 用闭区间消费右/下开框——即
BC-SURVEY-15。其余五项：

1. **`"root_manifest": null` 能通过 S1 的存在性检查**，然后走进「无声明」诊断分支什么
   都不比。验证者端到端演示了在这种 S0 下夹带第 60 行根表规则、把 `runtime/models/`
   下的帧偷渡成 `VALID_FORMAL`。已改为两个键都必须是对象（`Stage1NullKeyTest`）。
2. **`build_inventory` 的模块 CLI 默认就写 create-once 工件**，完全不对账（`--dry-run`
   是选项而不是默认）。已改为该 CLI 只允许 `--dry-run`，发布一律走 `run_pipeline`。
3. **`ROOT_MANIFEST_ENTRY_FIELDS` 的唯一测试是自证循环**：它拿被测常量本身当期望值。
   验证者把 `kind`/`usage_class` 从元组里删掉，494 条 dist_data 用例**全绿**——而那正是
   BC-SURVEY-7 明禁的「用途类代替根映射冻结」。已改为逐字钉住五个字段名，并补两条
   「用途类/kind 改动必须被 S1 看见」的回归。
4. **`WITNESS_CONNECTIVITY` 是装饰性常量**，`red_components` 从不读它。已改为实际消费，
   改成 8 即抛错。
5. **整帧扫描建立在 sidecar 自述尺寸上**，谎报偏小会静默变成左上角裁窗（验证者实测：
   64×48 帧按 32×24 扫，整辆红车漏掉且不抛异常）。已与真实字节尺寸对账
   （`WitnessScanExtentTest`）。

另有两项来自同轮横扫：`SurveyContractError` 在 `drive`/`close` 的 CLI 路径上会裸抛出去
（已在 `main` 的处置里合并该域错误），以及「`contract_document(None)` 不写
`survey_sessions`」这条断言在重建 `ContractAllowlistTest` 时被删掉（已补回，并加上
driver 今天真正会发布的四键形状断言）。

## 14. 接受轮 5 的窄返工（BC-SURVEY-14 两条 fail-open + BC-SURVEY-16）

接受角色在窄复查里查出 BC-SURVEY-14 的两处执行不完整，以及 BC-SURVEY-9/16 的一处
覆盖不足：

1. **重入分支只核对了采集协议钉子，没核对所钉 plan 本身。** `close` 的两条重入分支
   走的是只查 `survey_acquisition_sha256` 的窄版本，于是 plan 文件缺失、plan 字节漂移、
   plan 侧钉子漂移、manifest 的 `plan_path` 被改都能一路走到**释放现场 / 补写
   create-once completion**。已统一改走 `assert_archived_pinned_plan`，它调用
   `load_pinned_survey_plan` 做完整核对（plan 路径 + plan 字节 SHA + manifest 与 plan
   两侧钉子 + 当前投影），并在释放/补写**之前**失败。7 条重入回归，其中 3 条断言
   `completion.json` 在失败后**没有**被补写。
2. **`verify` 的核对挂在 `selection.json` 存在与否上。** 零帧归档没有 selection，整条
   核对被跳过。已把核对提到函数开头无条件执行，`selection` 分支只复用它得到的合法集合。
   4 条回归覆盖零帧归档的钉子漂移、plan 缺失、plan 字节漂移，以及有帧归档的钉子漂移。
3. **身份创建只试了候选 1（早前甚至不查有效性）。** BC-SURVEY-16 要求按冻结次序穷举
   **全部**候选、取首个过硬门者。已加 `resolve_anchor_plan`（只读穷举，返回逐候选拒绝
   记录）与 `resolve_anchor_sequence`；`write_plan` 的 `candidate` 省略即穷举，
   `install_diagnostic` 同样走穷举解；新增只读 CLI 子命令 `anchors` 报告可达序列。
   穷举复用同一份候选枚举以免逐候选重算（枚举占单次 build 的 ~92%），
   `test_precomputed_candidates_change_nothing` 钉住等价性。

BC-SURVEY-15 上一轮已闭合。BC-SURVEY-17/18 是 `CLARIFY`，不新增义务，只把两条的闭集
定死；两者的闭集断言见 §5。

## 15. `C1@stageA` 的四项不满足与四项关注项（本批闭合）

接受角色的核对表判 14 满足 / **4 不满足** / 0 证据缺失，另列 4 条预复核关注项。C1
无退回权，但按 workflow「不把明显失败的中间版本交给复核」，本批先修再交。

### 四项不满足

**BC-SURVEY-2**（零帧 `close` 只读日志首行终态，证明不了「仅含」pre-command 事件）。
改法不是列一份「哪些事件算 pre-command」的白名单——那份白名单本身就是会影响正式
结果的常量，按 BC-SURVEY-14 得投影进 `survey_acquisition`，而那会把 BC-SURVEY-17
冻结的 89 项变成 91 项，**并且**改动钉子、使 `bc83728` 里 7 份 create-once plan 全部
失效。改成让运行时**数事实**：`RuntimeBridge` 统计 `commands_issued`，`drive` 写进
日志头，零帧 `close` 直接读它并要求为 0；缺该键即拒绝（老形状不得蒙混）。零新增
受投影常量，钉子不变。

**BC-SURVEY-4**（`_read_ref`/`_catalog_stream`/S2 只读 `self.attempt`，没有逐依赖
解析）。新增 `PipelineDriver.read_chain()` 与 `resolve_read_attempt()`：写入 attempt
与读取 attempt 解绑，attempt-3 逐依赖按「已发布 attempt-3 优先，否则 attempt-2」
解析并携带**实际**ref；attempt-1 是旧表示的不可变基线，不进混合路线。S2 也改为按
解析后的 inventory attempt 构建。新增 `MixedAttemptReadTest` 真正构造混合状态
（attempt-2 有 inventory+layout、attempt-3 只有 layout），断言 S3 的 `inputs` 恰为
`[(inventory, attempt-2), (layout, attempt-3)]` 且每个 ref 的 SHA 等于盘上真实字节。

**BC-SURVEY-14**（`stage0_contract` 传 `sessions or None`，零归档时省略
`survey_sessions`，差异只有四键）。改为无条件写入（缺省空表），两种形状的差异键都恰
为五。原先那条明确接受四键的用例已改为断言五键。

**BC-SURVEY-16**（`prepare_session` 不检查前八项处置，也不限制备 9/10 依序启用）。
新增 `anchor_disposition()`（`CLOSED` / `UNREACHABLE` / `PENDING`）与
`assert_anchor_enabled()`，在 `prepare_session` 安装现场**之前**执行。备用锚点由已
投影的 `SURVEY_ANCHOR_TABLE` 末两行派生为 `(9, 10)`，不新立会改动钉子的字面量。

### 四项关注项

1. **达成率分母被抬高**：`classify_frames` 原用实际完成的窗当分母，被跳过的位置与未
   稳定的视角因此从分母里消失。新增 `planned_view_counts(plan)`，分母改由**计划**给出，
   并把执行数单独报告（两者不等即说明有跳过）。
2. **临时/权威证人结论从不比对**：S2 重算后不读 `completion.json.tentative_witness`，
   §2.1(f)「两者不等即硬错误」在生产路径上不存在。已在 `validate_survey_partition`
   里逐字段比对，缺失或不等均 `LayoutError`。
3. **会话表 dict 化掩盖重复行**：改为查重 + 按 `session_id` 排序后**逐位置**比对，并
   拒绝闭集外字段。
4. **证据指针前缀**：`工件:`/`命令:` 全部改为 COORD-009 冻结的 `artifact:`/`cmd:`。

### 一项如实披露（不是缺陷，是设计后果）

钉子设计让 **plan/config 的创建时机与代码冻结强耦合**：任何受投影常量的改动都会移动
`survey_acquisition_sha256`，使已发布的 create-once plan 全部失效。本批因此在修 BC-2
时刻意绕开新增受投影常量。后续若接受角色裁定需要新增，则 7 份 plan/config 必须一并
处置（换身份或另行授权），实现角色不自行决定。

## 16. `R1@stageA` 的两条阻断 finding（本批闭合）

复核 verdict `REWORK_REQUIRED`（本停点第 1 次），两条 CLASS_2 阻断 + 两条 CLASS_3。

**F1（`IN_SCOPE_NO_BC`）— 写侧 supersession 不按「最新已发布前身」解析。** 原实现只取
操作员传入的**单一** `--supersedes`，该 attempt 在某阶段未发布时直接返回 `{}`，写出
`supersedes: null` 的断链工件；而正式 attempt-1 的 S0–S5 六件全部存在，前身从不缺席，
所以 `{}` 不是「不伪造」。更难看的是**我那条测试把这个偏差写成了期望值**
（`test_supersession_kwargs_skip_absent_predecessors`）。闭合：新增
`PipelineDriver.resolve_predecessor()`，按阶段从 store 解析「当前 attempt 之前最新已发布
者」；attempt ≥ 2 解析不到前身或缺归因一律**拒绝写入**；CLI 的 `--supersedes` 删除，操作员
只给 `--supersession-reason`。原测试按复核要求的语义改写为 `SupersessionResolutionTest`
（6 条，含 attempt-2 缺席时回退 attempt-1、无前身即拒、缺归因即拒、envelope 携带解析结果）。

**F2（`BC-SURVEY-4`）— 生产入口没有「从首个未发布阶段续跑」。** `--run` 恒从 `contract`
起，会把已发布的 S0/S1/S2 也重新以 attempt-3 发布，于是各阶段都读到刚写的 attempt-3，
BC-4 的「attempt-3 优先、否则 attempt-2」回退在生产入口**永不触发**——`MixedAttemptReadTest`
是逐阶段直接调用方法造出的状态。闭合：新增 `first_unpublished_stage()`，`run_stages` 默认
`resume=True`，相对被 supersede 的 attempt 确定首个未发布阶段并从该阶段起跑、不重发已发布
阶段，并把跳过的阶段名 emit 出来。新增 5 条**经生产入口**的回归，分别让 S2/S3/S4/S5 成为
首个未发布阶段，断言实际读取 ref 的 attempt 与 §2.2 第 5 条一致（S2 读 inventory@2；S3 读
inventory+layout@2；S4 读 frames_catalog@2；S5 读 frames_catalog+layout@2），并断言已发布
阶段**没有**被重发。为让 S2 的阶段体在生产入口下真跑，夹具把冻结基础几何与 default 场景
字节复制进临时根。

**F4（CLASS_3，本文件）** 的逐字补丁已应用（页首自述与 §10/§11 的时态矛盾）。**F3**
属设计文档，由接受角色在下次提交应用。

修复只触及 `tools/dist_data/run_pipeline.py` 与两份测试；**7 份 create-once plan 的钉子
未被移动**（仍 `b4ad4f7b…80bf`）。

## 17. 实现角色自查发现：F2 修复自身引入的第三处回归（交接受角色裁定，未自行修复）

`R2@stageA` 把未闭集冻结为 {F5, F6, F3} 之后、接受角色裁定之前，实现角色对 R3 的检查面
（冻结集 + `RED_LINE` + **修复触及行上的 CLASS_1/2**）做了一轮对抗性预审：4 个独立猎手
按不同攻击面扫，每条候选再派独立验证者专门推翻。结果 **1 条确认、11 条被推翻**。

### 确认项（CLASS_2，依据 `IN_SCOPE_NO_BC`；正文引 BC-SURVEY-4）

**S7/S8 把 `splits` 的读取绑死在写入 attempt 上，于是凡续跑起点在 `field_catalog` 及其后的
运行，都会在写出一件 create-once 工件之后撞死，且不留 S9 收束记录。**

- 位置：`tools/dist_data/run_pipeline.py:688`（`stage7_gate`）与 `:756`
  （`stage8_mother_set`），两处均为 `self._store.composite_manifest("splits", self.attempt, …)`。
  driver 里其余每一处跨阶段读取都已按 BC-SURVEY-4 经 `resolve_read_attempt()` 解析
  （`_read_ref`、`_catalog_stream`），这两处是仅剩的硬绑。
- **实现角色独立复现**（`git archive 85adf93` 到 `/tmp` 的一次性副本，生产入口
  `run_stages(..., through="g0_report")` 即**默认** `--through`；attempt-1 发布到
  `field_catalog`，attempt-2 发布到 `splits`，即 attempt-2 死在 S5 之前）：

  ```
  first_unpublished_stage: field_catalog
  emit: {"resumed_from": "field_catalog",
         "skipped_published_stages": ["contract","inventory","layout","frames_catalog","splits"]}
  emit: {"field_catalog": {..., "sha256": "957a2a41…"}}
  RAISED: DistDataError: 工件缺失：…/runtime/dist-data/splits/attempt-3/splits.json
  published@attempt-2: ['contract','frames_catalog','inventory','layout','splits']
  published@attempt-3: ['field_catalog']
  stop_point@attempt-3 存在: False
  ```

- **为什么这不是「fail-closed 所以没关系」**：输入并不缺失——`splits` 就发布在 attempt-2，
  而同一个方法里 `frames_catalog` 正是经 `resolve_read_attempt` 从 attempt-2 读到的；
  splits@attempt-2 的 lineage 输入恰是那件 frames_catalog@attempt-2，所以 attempt-2 才是
  **自洽**的 splits。报错点名的是续跑自己决定跳过的工件，而它对操作员暗示的唯一出路
  （发布 splits@attempt-3）正是 §2.2 第 5 条「已发布阶段不重发」与 create-once 所禁止的。
  这是**解析错了**恰好报了错，不是 fail-closed 的门。
- **后果**：(a) attempt-3 被永久卡死，重试撞同一堵墙，恢复要走 attempt-4；(b) 一件
  create-once 工件（`field_catalog@attempt-3`）烧进一个永远跑不完的 attempt 且按合同不可删除；
  (c) 没有 S9 收束记录；(d) R1-F2 修复的全部目的——让 BC-SURVEY-4 的回退在生产入口可达——
  在 S5 之后原地失效。
- **为什么落在 R3 范围内**：688/756 文本上不是 `85adf93` 触及的行，但
  `docs/collaboration-workflow.md:316` 逐字写明「锁的是未改动代码上的范围蔓延，**不豁免修复
  自身引入的回归**」。`85adf93` 之前 `run_stages` 恒从 `contract` 起，splits@self.attempt 在
  S7 前必然存在，这处硬绑是惰性的；正是我新加的 resume 切片让它致命。

### 我自己的回归为什么没抓到

`test_resume_starts_at_field_catalog_when_s5_is_first_unpublished` 用的是
`through="field_catalog"`——**恰好停在断点前一个阶段**，而生产默认是 `g0_report`。这是本批
第四次出现同一模式：我写的测试选了一个绕开缺陷的参数（前三次是
`ROOT_MANIFEST_ENTRY_FIELDS` 自证循环、`WITNESS_CONNECTIVITY` 装饰性常量、
`test_supersession_kwargs_skip_absent_predecessors` 把偏差固化为期望值）。

### 未自行修复的理由

`R2@stageA` 已按 COORD-009 (c) 把未闭集**冻结**为 {F5, F6, F3}，交接行 owner 是接受角色。
本项不在冻结集内；冻结的用意正是止住轮次膨胀，因此实现角色**不自行扩大候选 diff**——
那本身会加宽 R3 的「修复触及行」面，正是这一批已经栽过两次的地方。请接受角色与 F5/F6
一并裁定「范围内必修」或 `SCOPE_GAP` 记债。

复核给出的闭合要求形状（供裁定参考）：688/756 改为
`self.resolve_read_attempt("splits")`；因为解析后是跨代读取，另需在解析到的 splits manifest
所记 `inputs` 的 frames_catalog ref 与本次实际读到的 ref 字节不符时 fail-closed（两个 ref 都
现成：`stream.reference` 与 manifest `inputs`）；绑一条以**生产默认** `through="g0_report"`
驱动 `run_stages` 的具名回归，断言要么干净过 S7、要么 `PipelineError` 点名不一致，且零半成品
attempt。修复只触及 `run_pipeline.py` 与测试，**不动任何 `SURVEY_*` 常量**，故 7 份 plan 的
钉子 `b4ad4f7b…80bf` 与 BC-SURVEY-17 的 89 项闭集均不受影响。

### 同轮被推翻的 11 条候选（记录扫过的面，供 R3 参考）

路径穿越型 attempt id 破坏不可变 attempt-1、数字别名 attempt id（`attempt-01`/`attempt-0`/
`attempt-002`/`attempt-03`）绕过谱系门、`bind_layout` 与 `build_inventory` 的模块 CLI 作为
第二写点、store 的 supersession 原因空串检查、S6 A1 拒绝被静默丢弃、`require_audit` 只查存在
不查 verdict、resume 切掉 `g0_report` 绕过 BC-DATA-2 门，以及同一处 splits 硬绑的两个较弱变体。
每条都由独立验证者复现失败或指出已有守卫覆盖。

## 18. `R2@stageA` 冻结集裁定后的返工：F5 / F6 / I17（本批闭合）

依据接受角色 2026-09-05 的冻结集裁定（提案「Acceptance rulings（复判）」节）：F5、F6
判「范围内必修，不改标 `SCOPE_GAP`」，F3 的 CLASS_3 补丁由接受角色自行应用，§17 的自查项
记为 **I17，范围内必修**——其义务由 BC-SURVEY-4「实际读取 attempt 与写入 attempt 不得强绑」
覆盖，不新增 BC。修复只触及 `tools/dist_data/run_pipeline.py` 与
`tests/test_dist_data_survey.py`，**未动任何 `SURVEY_*` 常量**，7 份 create-once plan 的钉子
仍是 `b4ad4f7bde5fa22d7913aa5e4adf2ddfd724c33dc7116904ddb53c87045b80bf`，BC-SURVEY-17 的 89
项闭集不受影响。

### 18.1 F5 —— `--through` 在续跑后仍是执行停止界

`run_stages` 先算出续跑切片，再在**跑任何阶段之前**校验停止界是否落在实际会跑的阶段序里；
不在即 `PipelineError`，零阶段、零写入，连续跑说明行也不发出（拒绝路径不产生任何输出）。
拼写错误的 `--through` 因此同样被这道门挡住，而不是一路跑到 S7。

### 18.2 F6 —— attempt 身份在构造时收束为闭集

`PipelineDriver.__post_init__` 用 `ATTEMPT_NAME = ^attempt-[1-9][0-9]*$` fail-closed，
不合式即 `PipelineError`。因为拦在构造点，不合式身份下**一件工件也写不出**。前导零一并拒绝
（`attempt-01` 会在另一个目录下开出与 `attempt-1` 同号的第二棵树，正是 §6 授权 #2「attempt
身份上限 = 2」要挡的第三个身份）。`_attempt_number()` 随之不再有 `None` 分支——那个分支正是
让 `_supersession_kwargs` 静默返回 `{}` 的入口；`read_chain`/`resolve_predecessor`/
`first_unpublished_stage` 三处的 `current is None` 判断一并删除。`attempt-1` 行为一字未变。

### 18.3 I17 —— `splits` 的跨阶段读取按 BC-SURVEY-4 解析，并加同代校验

S7/S8 改经新的 `_composite_manifest()` 取数（与 `_read_ref`/`_catalog_stream` 同一解析规则），
不再按写入 attempt 硬绑。裁定同时要求「不一致时在发布新的 attempt 工件前失败」，而缺 `audit`
只是**缺件**、不是不一致，所以另加 `_assert_splits_lineage()`：把 splits 信封 `inputs` 里记录的
`frames_catalog` ref 与本次实际读到的 `CatalogStream.reference` 逐字段比对，混代即在本阶段
写出任何工件之前 `PipelineError`。两个 ref 都现成，不新增读取路径。真实归档
`splits@attempt-1` 的 `inputs` 记的正是 `frames_catalog@attempt-1`
（`a2119a36…a364`，与磁盘实测一致），故 attempt-1 路径不受影响。

### 18.4 具名回归（7 条，全部经生产入口）

| 用例 | 闭合的项 | 断言 |
|---|---|---|
| `test_through_pointing_at_a_skipped_stage_runs_no_stage` | F5 | 停止界被跳过 → `PipelineError`，attempt-3 零工件，零输出行 |
| `test_through_still_stops_at_the_named_stage_after_resume` | F5 正对照 | 停止界落在会跑的阶段上 → 只写出该阶段一件 |
| `test_malformed_attempt_is_refused_at_construction` | F6 | 7 种不合式身份（含 `attempt-01`/`attempt-0`/大小写/尾空格）构造即失败、目录不存在 |
| `test_wellformed_attempt_identities_are_unchanged` | F6 正对照 | `attempt-1` 的 `read_chain`/`_supersession_kwargs`/`resolve_predecessor` 不变；`attempt-10` 链正确 |
| `test_default_through_reads_splits_from_the_predecessor_attempt` | I17 | 生产默认 `through="g0_report"`：一致 lineage 跑到 S9 收束，`splits` 仍只有 attempt-2 一份 |
| `test_missing_audit_fails_before_publishing_any_attempt3_artifact` | I17 | attempt-2 完整发布到 S5 时失败点名 `audit` 而非 `splits`，attempt-3 零工件 |
| `test_mixed_generation_splits_and_catalog_fail_before_any_write` | I17 同代门 | `frames_catalog@attempt-3` + `splits@attempt-2` → `lineage 不一致`，零新工件 |

### 18.5 修前必失败（整体换回 `9c2ce62` 的 `run_pipeline.py`，测试不变）

5 个用例打红（8 failures + 3 errors，含 subTest 展开）：上表除两条正对照外的 5 条。其中 F5
一条的实际现场即 R2 的病灶——操作员要求「跑到 S1 为止」，工具却执行到 S7 才以
`缺 audit@attempt-3` 停下，沿途写出三件 create-once 工件。两条正对照修前修后皆绿，正是它们
作为对照的意义。

### 18.6 四次反向变异（每次只撤一处，还原后复测全绿）

| 变异 | 打红的用例 | 是否只红自己 |
|---|---|---|
| 撤掉 F5 的停止界校验 | `test_through_pointing_at_a_skipped_stage_runs_no_stage` | 是（1 条） |
| 撤掉 F6 的构造期命名门 | `test_malformed_attempt_is_refused_at_construction` | 是（1 条，7 个 subTest） |
| 把 S7/S8 的 `splits` 读取绑回写入 attempt | I17 的 3 条 | 是 |
| 只删两处 `_assert_splits_lineage` 调用 | `test_mixed_generation_splits_and_catalog_fail_before_any_write` | 是（1 条） |

`m3` 的失败签名逐字复现了 §17 的现场：`工件缺失：…/runtime/dist-data/splits/attempt-3/splits.json`。

### 18.7 本轮实际运行的命令与结果

```
python3      focused test_dist_data_survey.py  → 97 tests OK
.venv-yoloe  focused test_dist_data_survey.py  → 97 tests OK
python3      focused test_survey_tool.py       → 151 tests OK (skipped=5)
.venv-yoloe  focused test_survey_tool.py       → 151 tests OK
python3      全套                              → 1119 tests, errors=9, skipped=20
.venv-yoloe  全套                              → 1224 tests, failures=1, errors=1, skipped=1
```

调用形式同 §5（`-m unittest discover -s tests -p '<pattern>' -q`，无 `-v`）。基线为
`9c2ce62` 在**同一工作树**上的实测（1112 / 1217），故计数差恰为新增的 7 条；两个解释器的
失败集合与基线 `diff` 逐名相同，**新增失败为零**。接受/复核复跑的那一对 = 97 + 151 = **248**。

用例计数：基线 972 → C1 返工 1209 → `R2@stageA` 1217 → 本批 **1224**。

## 19. 阶段 B pilot 与阶段 C 采集（授权 #2，2026-09-05/06）

用户 2026-09-05 逐字「授权继续」签发提案 §6 授权 #2（`docs/authorizations.md` 同日条目）。
本节记录阶段 B 的 pilot 与阶段 C 的六个锚点会话；全部经生产入口
`prepare` → `drive` → `close`，`close`/`verify` 一律用钉死解释器
`.venv-yoloe/bin/python`（`python3` 缺 Pillow，工具已 fail-closed 并指名，见 §19.5）。

### 19.1 会话总表

| 会话 | 视角 | 达成率 | 归档帧 | 证人 | 净空 | 终态 | tree_sha256 |
|---|---|---|---|---|---|---|---|
| `…a1-p1-c1-s1` | 0 / 224 | — | 19 | `INSUFFICIENT_WITNESS_FRAMES` | — | `CLOSED_PROTOCOL_INVALID` | `b3acfa34…eef0` |
| `…a1-p1-c1-s2` | 227 / 227 | 1.0 | 2916 | `WITNESS_PASS` 0.876 | PASS | `CLOSED_OK` | `a0edc431…b415` |
| `…a2-p1-c1-s1` | 195 / 195 | 1.0 | 2523 | `WITNESS_PASS` 0.899 | PASS | `CLOSED_OK` | `cbb8dcdd…93a1` |
| `…a3-p1-c1-s1` | 227 / 227 | 1.0 | 2818 | `WITNESS_PASS` 0.890 | PASS | `CLOSED_OK` | `290a9a83…5817` |
| `…a4-p1-c1-s1` | 227 / 227 | 1.0 | 2822 | `WITNESS_PASS` 0.923 | PASS | `CLOSED_OK` | `97469204…57f1` |
| `…a6-p1-c1-s1` | 227 / 227 | 1.0 | 2943 | `WITNESS_PASS` 0.898 | PASS | `CLOSED_OK` | `567f9dcc…6f74` |
| `…a7-p1-c1-s1` | 227 / 227 | 1.0 | 3168 | `WITNESS_PASS` 0.918 | PASS | `CLOSED_OK` | `7a80069e…e01b` |
| `…a9-p1-c1-s1` | 179 / 179 | 1.0 | 2796 | `WITNESS_PASS` 0.903 | PASS | `CLOSED_OK` | `88a035d4…577d` |

七个有效会话共 **19,986 帧**（954 MB）。证人中心命中率七次全是 **1.0**，分母 61/61/62/62/61/61/62
（下限 50）。`a1-s2` 的归档树另经 `verify` 独立重算，`tree_sha256` 与 `close` 逐字一致
（member_count 5839）。

### 19.2 `a1-s1` 作废：环境阻塞，非实现缺陷

首次 pilot 的 `drive` 以 `ABORTED_NO_FRAMES` 中止：`preconditions_ok`（首帧 12、`scenario_id`
匹配、路网审计零违规）后发出 49 条指令，t = 10.02 s 在 `C14` 中止，零视角完成。实测
`ProjectSettings/ProjectSettings.asset:85` 为 `runInBackground: 0`——Unity Editor 失去窗口焦点
即停止推进 Play，用户按下 Play 后切窗口告知实现角色时帧流冻结（最后一帧落盘 18:08:47，
80 s 后仍无新帧）。**这是操作程序/环境阻塞，不是工具缺陷**；驱动器的 10 s 无帧门按设计
fail-closed。19 帧仍按合同无损归档。改用「先起 `drive`、再点回 Unity 并全程保持焦点」的
顺序后，其后七次全部一次通过。**未修改 `runInBackground`**：那是纳入版本控制的项目设置，
影响面超出本批与授权 #2 的五字段。

**待接受角色裁定（合同歧义，未自行解释）**：§2.4 的失败出口只有 `PILOT_FAIL_TOOL` 与
`PILOT_FAIL_SCENE`，而「达成率 < 90% → `PILOT_FAIL_TOOL`」会要求「修复 → 停点 → 按 §4.4
资格复核 → 再试采」。本次无任何代码改动可修（零 PLAY_GOVERNING diff，开不了复核轮），
故实现角色不自行选取宽松解释，请裁定 `a1-s1` 归为 `PILOT_FAIL_TOOL` 还是状态机之外的
作废会话。信封计数不受裁定影响：§2.1(a) 明文「每次 Play 计入信封（含零帧会话）」。

### 19.3 pilot 判定（`a1-s2`）：`PILOT_PASS`

§2.4 四项判据逐条实测（只读分析，不写正式工件）：

| 判据 | 阈值 | 实测 |
|---|---|---|
| 达成率 | ≥ 0.90 | **1.0**（224/224 巡览 + 3/3 证人） |
| 证人 | `WITNESS_PASS` | 分母 61，中心命中 1.0，IoU 中位 0.876 |
| 事后净空 | 通过 | **零违规**：2916 帧实际位姿 × 678 个扩展障碍框；最大系留 31.895 m（限 33），高度 ∈ [14.0, 26.0]（限 [8,30]） |
| 55 m 内目录车 `OK` | ≥ 60% | **16 / 20 = 80%** |

四辆零 `OK` 的车（38.34–48.20 m）状态直方图全部由 `EXCLUDED_OCCLUDED` 主导
（206/218/158/152 帧），即该锚点视线被建筑遮挡，不是采集参数问题；可调集里无参数可解。

**不提 §2.4 的「唯一一次修订」**，两条独立理由：(1) 四门全过且有余量，失败模式是遮挡；
(2) 信封上不可行——修订会把计划版本推到 v = 2，剩余 6 个锚点各需新身份，而
plan/scenario ID 上限 10、已用 7，只剩 3 个。故 **v = 1 继续**。

### 19.4 跨会话覆盖（只读汇总）

七个有效会话的 `VALID_SURVEY` 帧共 **9,500** 帧，逐帧经 `project_boxes.project_instances`
与 `layout attempt-1` 的 default 布局实例（779 个，其中 101 辆目录车）投影：

- **89 / 101 辆目录车**在至少一帧取得 `OK` → 覆盖 **88.1%**
- `OK` 对象-帧总数 **13,147**
- 每辆车最佳短边：最小 22.5 px、中位 89.2 px（`MIN_VISIBLE_SIDE_PX` = 12）
- 单会话覆盖 22–25 辆，七个锚点并起来才到 89——**多锚点的意义正在于此**

（89 与 BC-SURVEY-17 的 89 项常量闭集无关，纯属数字巧合。）

### 19.5 运行纪律的一条实测记录

`close` 首次用 `python3` 执行**失败**：`ModuleNotFoundError: No module named 'PIL'`，
经 `pixel_source._require_pillow` 抛 `PixelError` 并逐字指名「请改用钉死环境
`.venv-yoloe/bin/python`（接受轮 14 §26.2：不下载、不安装新包、不改依赖清单）」。
换钉死解释器后成功。结论：`close`/`verify` 必须用 `.venv-yoloe/bin/python`（证人评估读像素），
`prepare`/`drive` 无此依赖。这是 fail-closed 生效的正例，非缺陷。

### 19.6 信封账目

```
正式 Play        8 / 10   （a1-s1 作废亦计入）
plan/scenario    7 / 10   （阶段 A 已建，本阶段零新增）
session ID       8 / 10
attempt 身份     0 / 2    （阶段 D 未开始）
API / GPU        0 / 0
```

锚点 1/2/3/4/6/7/9 全部 close，冻结锚点表无剩余可达锚点。现场已复原：`runtime/frames/` 空、
运行时 override 卸载、活动标记解除。

## 20. 阶段 D：S0–S5 attempt-2 与审计前上界报告

六件工件已以 attempt-2 create-once 落盘（`--through field_catalog`，S6–S9 未触及），
逐件 supersede attempt-1 且无一断链。完整的上界表、结构定位、实测摘要与执行记录见
**`docs/evidence/P1-VLM-DATA-002-S0-S5-pre-audit-upper-bound.md`**（格式对齐
DATA-001 轮 20/28）。本节只留指针与三条需要 acceptance 处置的事实：

1. **预注册产出线五项中四项达成**：`U_F3`（494 / 633）、`U_F4`（49 / 55）、
   `U_F1` 类覆盖（7 类 ≥ 6）、train split 非空（2,523 帧）均过；**`U_F1` 对象数
   37 < 60 未达**。按 §5 第 5 条，机械结论是 **`SURVEY_FLOORS_UNREACHABLE`**，
   后续只按 §2.4 回用户二选一；下限永不移动，实现角色不作任何调参或补采提议。
2. **未达的结构定位**：S5 的 93 个车辆对象 **class 全部通过**，卡点全在颜色——
   37 `VERIFIED` / 37 `GROUP_INCONSISTENT` / 19 主色带不足。与 attempt-1 的关键差别是
   结构上限由 16 升到 93，**60 的下限首次在结构上可达**，未达原因转移为颜色验证。
3. **BC-SURVEY-4 的跨代回退路径未被触发**：本次自 S0 连续跑到 S5，F2/I17 所修的
   attempt-3 混代读取在真实归档上仍只有测试夹具证据。如实记录，不作已验证声明。

另有一条运行事实：首次 preflight 因 `p1-vlm-survey-a1-p1-c1-s2/` 内出现 macOS 的
`.DS_Store` 而以 `归档树摘要不符` fail-closed。该文件**移出隔离而非删除**，移出后
`verify` 重算 `tree_sha256` 与 `close` 记录逐字一致。归档目录不应用 Finder 打开。
