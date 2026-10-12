# P1-ENG-ACQ-001 K1K2K3 候选交接（C1 首退后返工 → C2 → `R1@K1K2K3` `REWORK_REQUIRED` 后返工 → `R2@K1K2K3` `PASS_WITH_NOTES`（R2-1 阻断消耗性门）→ R2-1 返工，交新鲜上下文 `R3@K1K2K3`）

实现角色（supervisor 派发的 Opus 子代理；Dispatch-Id `P1-ENG-ACQ-001-K1K2K3-20260929T033849Z-3a61`，续派
`P1-ENG-ACQ-001-K1K2K3-20260929T142800Z-9b04`、第二次续派 `P1-ENG-ACQ-001-K1K2K3-20260929T150551Z-e3c8`；`C1@K1K2K3` 首退（a2817cb）后的返工派发
`P1-ENG-ACQ-001-K1K2K3-20260929T171016Z-c5a7`，上一候选 d991b86；`R1@K1K2K3` `REWORK_REQUIRED`（e6c75a0，被复核候选 798881e）后的返工派发
`P1-ENG-ACQ-001-K1K2K3-20260929T180309Z-1d8f`；`R2@K1K2K3` R2-1（`上轮漏检` CLASS_2，`blocks_consuming_gate: R2-1`）经提案决策记录「R2@K1K2K3 通过轮消费与 R2-1 处置（2026-09-29）」裁定路径 (a) 后的返工派发
`P1-ENG-ACQ-001-K1K2K3-20260929T184801Z-7a42`）。合同：提案 §1–8、§4 AC-1…20、
「§4.2(a) 接受处置」的 AC-3/7/19 接受释义、「§5 信封与 §7 (g)(h)(i) 答复落实」的 AC-7/9/16/17/18/20 修订 1、
「信封修订 SUB:1/SUB:2 落实（2026-09-29；CLARIFY）」的 AC-7/20 修订 2、「信封修订 SUB:3 落实（2026-09-29；CLARIFY）」的 AC-7/20 修订 3；执行信封 =
`docs/authorizations.md` 2026-09-28「P1-ENG-ACQ-001 — 用户签发 §5 阶段 1+2 执行信封…」，经 2026-09-29「用户批准实现角色追加申请 SUB:1…与 SUB:2…」
与同日「用户批准实现角色追加申请 SUB:3（scout-1 第二级每 (k,o) SOT 帧上限 ≤87）…」修订；合同另加提案决策记录「C1 待用户裁定落实（2026-09-29；CLARIFY）」的
AC-11 修订 1、AC-15 修订 1（依据账本 2026-09-29「用户裁定 C1 待用户两项…」）与核对表「IR-1…21 读法裁定（C1）」。

- **候选**：本文件最后一次修改所在提交（`git log -1 --format=%H -- docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`）；完整候选 diff =
  `git diff <首派 3a61 requested 行的 base_head>..<候选>`（base_head 见 `docs/evidence/supervisor-dispatch.jsonl`；其间夹有接受/supervisor 的
  文档提交，核对以实现文件为准）；续派 9b04 的增量 = `git diff <9b04 requested 行的 base_head>..72da3f9`；第二次续派 e3c8 的增量 =
  `git diff 84c931e..d991b86`（e3c8 requested 行的 base_head 至上一候选）；**本返工 c5a7 的增量** = `git diff fda0c6d..<候选>`（c5a7 requested 行的 base_head；
  其间夹有 supervisor 派发登记提交，核对以实现文件为准：`controller/resident_core.py`、`controller/track_loop.py`、`tests/test_resident_core.py`、
  `tests/test_track_loop.py`、`tools/eng_acq/report.py` 与证据文件）。**R1 返工 1d8f 的增量** = `git diff 798881e..<候选>`（实现文件只有
  `controller/language_loop.py`、`controller/gated_publisher.py`、`controller/track_loop.py`、`tests/test_language_loop.py`；其余为证据/状态板/派发日志）；
  三个修复与回归测试分提交（修复 922230e、7cf133c、264a034，回归 22ed467），见下「R1 返工说明」。**R2-1 返工 7a42 的增量** = `git diff e2cce88..<候选>`
  （7a42 requested 行的 base_head；实现文件只有 `controller/language_loop.py`（修复 2b50cf6）与 `tests/test_language_loop.py`（回归 3363eb2），其余为证据/账本/状态板；
  其间夹有 supervisor 派发登记提交），见下「R2-1 返工说明」。
  首派两次提交：阶段 1+2 代码/线束/证据与 H-5 清单（清单先入证据），其后 H-5 本地删除结果、交接与状态板。续派一次提交：线束两处上限改为
  修订值（a7 全样本、每 (k,o) ≤ 66 帧）、E1 两臂各两次重跑、报告/账本/测试/本文件与状态板。第二次续派一次提交：每 (k,o) 帧上限改为按序列取值
  （`tools/eng_acq/e1.py::frame_cap`：scout-1 ≤ 87，a7、m3-armA ≤ 66）、E1 两臂各两次整体重跑、报告/账本/测试/本文件与状态板；其他 AC 的实现未改。
- 阶段 1 → 阶段 2 按 §2.2 无门直通；两阶段合并为一个 `K1K2K3` 候选。Play D1 未签，零 Play。

## 自证四项（workflow §4.3.1）

1. **范围与接口冻结**：常驻插件协议（§3.1 `compat`/`resident` 互斥、`step`/`pointer_result`/`designate`/`follow`/`pointer`/`history`）、
   历史条目字段（§3.2）、六值闭集与 `level2.reason` 闭集（§3.4/§3.4.1 + AC-3 释义）、位姿单应（§3.3）、载体路径（§3.1 载体段）、
   会话九态与三个新原因（§3.6）、`slew_look_at` 通道（§3.7）、最小伺服（§3.8）、`tracker_state.designation` 字段（§3.4）均已落地；
   本候选内不再改接口。实现读法见下「待裁定」IR-1…21（已由 C1 裁定）；C1 返工新增 IR-22（C2 接受）；R1 返工新增 IR-23/24：接受角色已裁定（提案「R2@K1K2K3 通过轮消费与 R2-1 处置」：IR-23 具名残余边界；IR-24 = R2-1 路径 (a)，本返工已修）。
2. **实现者测试**：停点全套与解释器分组 focused 均已跑（R2-1 返工 7a42 重跑，见「测试」）；本批新增失败 0；R1-1/2/3 与 R2-1 各有修前红/修后绿。
3. **Unity**：本候选零 Play；无已知 Unity 失败。AC-17/18 `NOT_RUN`（Play D1 另签）。
4. **状态板、候选提交与未验证风险已更新**：状态板本行交 Review（由 supervisor 派发，新鲜上下文 `R3@K1K2K3`：R2-1 红绿核实并写 `releases_consuming_gate`；复核返工直接回复核、不经核对轮）；未验证项与限制见文末。

## AC-n 逐条证据指针

| AC | 自证结论 | 证据指针 |
|---|---|---|
| AC-1 | 满足 | test: `tests/test_det_assoc_tracker.py::ResidentProtocol::test_resident_step_without_pointer`；`::test_mode_methods_are_exclusive`；`::test_step_repeated_or_rolled_back_frame_raises` |
| AC-2 | 满足（深度缺省 128，下限 100） | test: `tests/test_det_assoc_tracker.py::ResidentProtocol::test_history_keyed_by_sensor_frame_id`；`::test_history_depth_eviction`；`tests/test_resident_core.py::History::*`；artifact: `manifest_identity().history_depth`（同测） |
| AC-3 | 满足（六值各有合成用例；第二级按 AC-3 接受释义映射；**C1 退回 IR-8 已修**：第 `coasting_limit`（30）次 step 仍未找回即转 `TRACK_ENDED`，见「C1 返工说明」） | test: `tests/test_det_assoc_tracker.py::ResidentProtocol::test_designate_bound_coasting_and_ended`；`::test_designate_no_track_ambiguous_and_out_of_history`；`tests/test_resident_core.py::Closure::test_designate_result_closed_set`；`LevelOne::*`（τ/m/备用判据边界、coasting 超时与移除转 `TRACK_ENDED`）；**`LevelOne::test_coasting_limit_boundary_fires_on_exact_step`**（limit 3 与 30：第 limit−1 次不转、第 limit 次转）；**`::test_coasting_recovered_on_exact_limit_step_is_not_ended`**（找回优先，找回后再丢不再转）；**`::test_coasting_same_id_follow_does_not_reset_count`**；`tests/test_language_loop.py::ResidentSessionTests::test_acquiring_after_coasting_timeout_same_designation`、`::test_acquiring_not_after_recovered_then_lost`；`LevelTwo::test_mapping_covers_every_replay_event`；artifact: 本文件「第二级映射」 |
| AC-4 | 满足 | test: `tests/test_det_assoc_tracker.py::ResidentProtocol::test_pointer_switch_keeps_associator`；`::test_level2_replay_keeps_associator` |
| AC-5 | 满足（合成 ≤ 0.5 px；三来源可选；a7 自检表位姿补偿中位 2.58 px vs 无补偿 95.38 px，§6(i) 不触发） | test: `tests/test_pose_gmc.py`；`tests/test_det_assoc_tracker.py::ResidentProtocol::test_gmc_source_selectable_and_pose_warp_passed`；`::ResidentLibrary::test_resident_associator_pose_warp_applied`（库）；artifact: `docs/evidence/P1-ENG-ACQ-001-e2.json`「pose_warp_selfcheck」 |
| AC-6 | 满足 | test: `tests/test_det_assoc_carrier.py::ResidentCarrierReplay::test_resident_carrier_matches_replay`（数据根 `.venv-yoloe`；scout-1 前 60 帧，缓存检测替身，零推理；最终代码通过记录见账本第 4 次 AC-6 载体自测）；`::ResidentCarrierCalls::test_resident_carrier_calls_step_once_per_frame_never_update`；`::test_legacy_carrier_call_sequence_unchanged`；cmd: `python3 -m unittest tests.test_trackers tests.test_track_loop tests.test_det_assoc_tracker tests.test_det_assoc_carrier`（系统 python3 下库用例跳过，见「测试」）；init-at-N 回放路径在常驻会话中不存在（`tests/test_language_loop.py::ResidentSessionTests` 的替身 `init`/`update` 一调即失败） |
| AC-7（修订 1/2/3、AR2-2 释义） | **满足**（第二次续派 e3c8 重跑后）：干净臂 15 桶/分母/守恒/空层/两次运行字节一致（sha256 `74cadc028333…`）均成立；a7 三种 gmc 第二级全样本运行（触发 659/757/1213 个 (k,o) 全部运行、`LEVEL2_SUBSAMPLED` 全 False、无 `not_run_ar2_2`）；每 (k,o) SOT 帧上限按序列取值（scout-1 87，a7、m3-armA 66；线束断言 `prefix.frame_cap == frame_cap(序列)` 且前缀不越限），scout-1 Δ13 需 77–87 帧已覆盖，超帧上限未运行 (k,o,Δ) = 0；E1 全部 648 层 `EVALUATED`（0 层 `NOT_EVALUABLE_*`）。与上一候选逐层比对，只有 scout-1 Δ13 的 32 层变化（旧 `NOT_EVALUABLE_FRAME_CAP` → 新 `EVALUATED`），其余 616 层逐字相同；旧候选的 `NOT_EVALUABLE_*` 读数不追溯改判，证据取本轮结果 | artifact: `docs/evidence/P1-ENG-ACQ-001-e1.json`（`layers`、`layer_status_counts`、`reproducibility`、`clean_arm.level2_budget` 的 `cap_frames_per_k_o`）；`docs/evidence/P1-ENG-ACQ-001-report.md`「E1」「第二级代价与 AR2-2 / 每 (k,o) 帧上限（信封修订 SUB:1/SUB:2/SUB:3）」；test: `tests/test_eng_acq_e1.py::Buckets::test_buckets_exhaustive_and_conserved`；`::Subsample::test_unsampled_are_not_bucketed`；`::Subsample::test_a7_full_sample_other_sequences_capped`；`::PrefixEquivalence::test_frame_cap`；`::PrefixEquivalence::test_frame_cap_by_sequence`；`::FrameCapBySequence::test_scout1_delta13_runs_under_87_others_capped_at_66`；cmd: `~/TetheredDroneTracking-full/.venv-yoloe/bin/python tools/eng_acq/run.py e1 --perturb none --run {1,2}`；`… run.py e1-merge` |
| AC-8 | 满足（27 格齐、未用 H 序列、空窗断言存在且三序列未触发） | artifact: `docs/evidence/P1-ENG-ACQ-001-e2.json`；`-report.md`「E2」；test: `tests/test_eng_acq_windows.py::EmptyWindowGuard::test_empty_window_rejected` |
| AC-9（修订 1） | 满足（读法 IR-12/13/14） | artifact: `docs/evidence/P1-ENG-ACQ-001-ledger.json`（零维度全 0）；`docs/evidence/P1-ENG-ACQ-001-cleanup.json`（唯一 runtime 例外：清单提交后移动 7 个 hold 目录）；test: `tests/test_eng_acq_guards.py` |
| AC-10 | 满足 | artifact: 本文件「承接声明」 |
| AC-11（修订 1） | 满足（权重、freeze、frozen-B/V、nanotrack 两件与既存来源散列逐项一致；`catalog-index.jsonl.gz` 先查找、确无独立既存文件散列记录，按修订 1 固定本次完整 sha256 为基线、标「既往不可核」，不冒充既存来源；AC-4 偏差声明与旧读数禁用不变） | artifact: `docs/evidence/P1-ENG-ACQ-001-assets.json`「catalog-index.jsonl.gz」（`prior_record_search`、`baseline`）；本文件「AC-11 index 散列查找」；`docs/evidence/P1-ENG-ACQ-001-report.md`「资产与偏差声明」 |
| AC-12 | 满足 | artifact: 本文件「复核范围」 |
| AC-13 | 满足 | test: `tests/test_language_loop.py::ResidentSessionTests::test_designate_while_tracking_*`（8 个）；`tests/test_language_bridge.py::TrackerStateTests::test_resident_closed_sets_and_designation_field` 与既有 `test_all_states_expressible` |
| AC-14 | 满足 | test: `tests/test_language_loop.py::ResidentSessionTests::test_acquiring_*`（9 个：恰一次转向与 hold、速度 `orphan_control`、到位 + N-of-M 收养绿、转动中到位红 + `slew_timeout`、收养超时红绿、收养歧义、coasting 超时同一指定内转第三级、找回后再丢不自动转向、stop）；`tests/test_gated_publisher_slew.py`；R1 返工：`::test_acquiring_slew_point_extrapolated_for_moving_target`（§3.7 外推转向点，R1-1）、`::test_acquiring_servo_baseline_follows_slew_command`（R1-2） |
| AC-15（修订 1） | 满足：窗口内、指针有效、过现有发布门的处理帧恰一次 `look_at`；相邻**已发**指令视线角变化 ≤ ω_max/hz；窗口外追平旧帧逐帧 `step`、逐帧记 `publish_skip_reason = outside_resident_publish_window`、不发令；发布门 ①④ 与机身规划器输入未改 | test: `tests/test_track_loop.py::ResidentServoTests::test_servo_rate_clamp`（红绿）；`::test_publish_window_skips_stale_backlog`（扩充：look_at 帧集、逐帧跳过记录）；**`::test_servo_baseline_is_last_written_look_at`**（被门拒的 look_at 不推进基准）；`::test_batch_publishes_every_processed_frame_and_body_only_latest`；artifact: 本文件「AC-15 发布窗口与跳过发布」；R1 返工：`tests/test_language_loop.py::ResidentSessionTests::test_resident_catchup_new_frame_mid_batch_not_stale`、`::test_resident_catchup_batch_end_pushed_out_skips_body_step`（R1-3）、`::test_acquiring_servo_baseline_follows_slew_command`（R1-2） |
| AC-16（修订 1） | 满足：清单先随第一笔提交入证据，其后才移动；5060 零访问、大小 `UNKNOWN_UNVERIFIED`；诊断 6 桥文件与帧只入清单 | artifact: `docs/evidence/P1-ENG-ACQ-001-cleanup.json`（`status`、`deletion.inventory_commit`、`deletion.results`） |
| AC-17（修订 1） | `NOT_RUN`（Play D1 未签）；触及声明见「人眼保真」 | artifact: 本文件「人眼保真」 |
| AC-18（修订 1） | `NOT_RUN`；即使 `K1K2K3` 通过，Overall 最高 `IMPLEMENTED_REVIEWED_AWAITING_UNITY` | — |
| AC-19 | 满足 | test: `tests/test_resident_core.py::LevelTwo::test_level2_success_adopted`；`::test_level2_failure_sot_lost`；`::test_level2_failure_no_adoption`；`::test_level2_failure_ambiguous`；`::test_level2_failure_replay_timeout`；`::test_level2_failure_init`；`::test_level2_old_frame_outside_history`；`::test_level2_old_frame_evicted_from_source`；`::test_level2_invalid_source_box`；`::test_level2_non_init_exception`；`tests/test_det_assoc_tracker.py::ResidentProtocol::test_level2_replay_keeps_associator` |
| AC-20（修订 1/2/3） | **满足**（第二次续派 e3c8 重跑后）：`c2_quantiles` 已跑、两次字节一致（sha256 `7a699b76cffd…`）、实现 p10/p25/p50 = 0.3145/0.7330/0.8557（差 0.0435/0.0100/0.0063 ≤ 0.05；样本构造未变，与上一候选相同），不读 C2 逐帧预测、不回放 H 帧；a7 全样本（触发 1124/1214/1637 全部运行）；scout-1 每 (k,o) ≤ 87 帧、a7/m3-armA ≤ 66 帧，超帧上限未运行 0；扰动臂 324 层全部 `EVALUATED`（含 scout-1 Δ13 的 16 层）；`uniform` 未执行（用户已选 `c2_quantiles`） | artifact: `docs/evidence/P1-ENG-ACQ-001-e1.json`「perturbed_arm」「perturbed_arm_budget」；`-report.md`「扰动臂分位数（AC-20 修订 1/2/3）」；cmd: `tools/eng_acq/run.py e1 --perturb c2_quantiles --run {1,2}`；test: `tests/test_eng_acq_e1.py::Perturbation::*`；`::FrameCapBySequence::*` |

## C1 返工说明（派发 `P1-ENG-ACQ-001-K1K2K3-20260929T171016Z-c5a7`；逐项对应核对表 C1 退回）

| C1 退回项 | 返工 | 证据 |
|---|---|---|
| AC-3 / IR-8（第 30 次 coasting 仍不转 `TRACK_ENDED`） | `controller/resident_core.py::_update_coasting` 由 `steps > coasting_limit` 改为 `>=`：自指定起第 `coasting_limit` 次 step 仍在 `lost` 池即 `COASTING_TO_TRACK_ENDED(cause=coasting_limit)`；同帧找回优先于超时；同 id 重复 `follow` 不重置计数、找回后再丢不自动转向均保留 | 新增 3 用例修前红（`FAILED (failures=3)`）修后绿；AC-3 行 |
| AC-11（index 来源散列缺失） | 按修订 1 先查找独立既存记录，确无；固定本次完整 sha256 为基线、标「既往不可核」 | 下节「AC-11 index 散列查找」；AC-11 行 |
| AC-15 / IR-3（窗口外处理帧不发 `look_at`） | 按修订 1：窗口内逐帧 `look_at`（经现有发布门）；窗口外旧帧照常 `step` 并逐帧显式记录跳过发布；另按「相邻**已发**指令」字面，被门拒的 `look_at` 不推进限速基准（IR-22） | 下节「AC-15 发布窗口与跳过发布」；AC-15 行 |

**E1/E2 不重跑（理由）**：E1 线束每次 `designate` 解析分桶后立即 `follow(None)`（IR-20），指定与撤指针之间没有 `record`，coasting 计数从不递增，`_ended_ids` 从不经 `coasting_limit` 写入，故 IR-8 边界对 E1 结果无影响；E2 不调用 `designate`，只用库 `track_buffer`；AC-15 改动只在 `TrackLoop` 常驻发布路径，E1/E2 线束不经过它。AC-6 `ResidentCarrierReplay` 比对的是逐帧 `(state, box, reason)`，本返工未改该路径，未复跑（每次计 2 次序列回放）。报告只重生成「资产与偏差声明」与「消耗」两段文字，E1/E2 段逐字节不变。

## R1 返工说明（派发 `P1-ENG-ACQ-001-K1K2K3-20260929T180309Z-1d8f`；逐条对应 `docs/reviews/P1-ENG-ACQ-001.md`「R1@K1K2K3」§3）

修复与回归分提交，复核可对每个修复提交单独 `git revert -n` 验红绿（本会话已在 HEAD 一次性 worktree 实测三次 revert 均无冲突，结果见
`docs/evidence/P1-ENG-ACQ-001-focused-venv-tests.log` 末段）。回归全部是会话级：`tests/test_language_loop.py::ResidentSessionTests`，真实
`GatedPublisher` 收据、`FixtureFramePublisher` 生产格式帧包、常驻替身 `FakeResident`（`ResidentCore` 真实现）；解释器 `.venv-language`。

| Finding | 修复提交 | 修复内容 | 回归测试 | 修前红（revert 该修复） / 修后绿 |
|---|---|---|---|---|
| R1-1 转向指令未用外推世界点 | 922230e | `controller/language_loop.py::_begin_acquiring`：`slew_look_at` 的点 = `_acquire_point(acquire, 发令时历史头 simulation_time_s)` = k 帧点 + 地面差分速度 ×（t_head − t_k）；无速度即 k 帧点；acquire 记录追加 `slew_time_s`、`slew_point_world_m`（只进会话日志 `acquire_started`，`designation.acquire` 键集不变） | `test_acquiring_slew_point_extrapolated_for_moving_target`（track 5 逐帧右移约 2 m/s，k 后 3 帧确认：收据点 = 外推点、距 k 帧点 > 0.5 m；静止目标收据点 = k 帧点） | 红：`128.120… != 129.284…`（收据仍为 k 帧点）；绿：OK |
| R1-2 转向后伺服限速基准仍是旧目标点 | 7cf133c | `controller/gated_publisher.py`：`last_gimbal_point_world_m` = 云台通道最后一条 `WRITTEN` 的点（伺服 `look_at` 与 `slew_look_at` 共用；拒绝/静音/写失败不推进）；`controller/track_loop.py::_servo_baseline` 以之为 `_publish_resident` 的限速基准，无该属性的直写发布器退回 `last_servo_point`（IR-22 不变） | `test_acquiring_servo_baseline_follows_slew_command`：(a) 收养 track 9 后首条伺服与转向点视线角 ≤ 6°（旧伺服点距转向点 > 12°）；(b) `ACQUIRE_FAILED(adopt_timeout)` 后新 `BOUND`（track 11）首条伺服同样 ≤ 6° | 红：`27.563… not less than or equal to 6.000001`；绿：OK |
| R1-3 追平窗口按批首 latest 判定、与门 ④ 不同源 | 264a034 | `controller/track_loop.py::_resident_frame`：每帧发布前（该帧 `step` 之后）经 `_publish_time_latest` 重读门 ④ 同一个 `latest.json`（只增不减，读不到退回批首值），按之判定窗口；窗口外帧照常 `step`、逐帧记 `publish_skip_reason`、不发观测/`look_at`；批末帧若被挤出窗口则本批不做机身步（否则门控速度只能对上一已发帧关联，必被门 ①/`orphan_control` 判 fatal），下一批批末帧照常；帧记录追加 `publish_latest_frame_id`。门 ①–⑤、`K_pub`、门拒 fatal 处理均未改 | `test_resident_catchup_new_frame_mid_batch_not_stale`（积压 6 帧，处理到批首 latest−3 时夹具写出 1 帧：批内零 `PUBLISH_REJECTED`、载体不拆、观测/`look_at` 只在 latest−1、latest，latest−5…latest−2 逐帧记跳过；下一 tick 照常发布并发帧）；附带 `test_resident_catchup_batch_end_pushed_out_skips_body_step`（`body=True` 冻结阈值规划器，批内写出 3 帧使批末帧出窗：零观测/`look_at`/机身速度收据、无门拒，下一批批末帧以同帧合格观测写出速度） | 红：主用例批内出现 `observation` `PUBLISH_REJECTED(catchup_stale)`；附带用例同样门拒（另核：只去掉机身步守卫时附带用例仍红）；绿：OK |

- **R1-4**（`SCOPE_GAP`，路由接受角色记债）：本派发不修，`_begin_acquiring` 几何被拒仍上报 `cause=slew_timeout`。
- **复核 §5 观察**：未处理（非 finding）。
- **E1/E2 不重跑（理由）**：`tools/eng_acq/` 不导入 `track_loop`/`gated_publisher`/`language_loop`；三处修复只在会话转向与 `TrackLoop` 常驻发布
  路径，E1/E2 线束不经过。AC-6 `ResidentCarrierReplay` 比对逐帧 `(state, box, reason)`，其载体用无窗口的 `RuntimePublisher`（窗口为空时不重读、
  无 `last_gimbal_point_world_m` 时基准回退原值），`step`/`pointer_result` 路径未改，未复跑（每次计 2 次序列回放）。报告 `P1-ENG-ACQ-001-report.md`
  未重生成，其「消耗」段停在 R1 前读数，以账本 JSON 为准。
- **读法**（不改合同，写明供 R2 核对）：R1-1 的「经过时间」取发令时刻常驻历史头帧的 `simulation_time_s` 减 k 帧的（与到位/收养判据
  `_acquire_point` 同一时间轴，仿真时刻而非墙钟）；R1-3 的发布窗口仍为 `K_pub`，只把判定所用 latest 由批首值改为发布前重读值。

## R2-1 返工说明（派发 `P1-ENG-ACQ-001-K1K2K3-20260929T184801Z-7a42`；对应 `docs/reviews/P1-ENG-ACQ-001.md`「R2@K1K2K3」§3 R2-1，裁定路径 (a)）

修复与回归分提交；复核可对修复提交单独 `git revert -n 2b50cf6` 验红绿（本会话已在 HEAD 3363eb2 一次性 worktree 实测：无冲突，结果见
`docs/evidence/P1-ENG-ACQ-001-focused-venv-tests.log` 末段）。

| Finding | 修复提交 | 修复内容 | 回归测试 | 修前红（revert 该修复） / 修后绿 |
|---|---|---|---|---|
| R2-1 常驻载体重建后限速基准丢失 | 2b50cf6 | `controller/language_loop.py`：会话新增 `_last_gimbal_point_world_m`；`_teardown_resident` 在 `finalize` 旧 `GatedPublisher` 后取出其 `last_gimbal_point_world_m`（非 `None` 才覆盖）；`_ensure_resident_loop` 新建发布器后把它设为新发布器的 `last_gimbal_point_world_m`，经既有 `TrackLoop._servo_baseline` 成为重建后首条伺服的限速基准。首个载体仍为 `None`（与原先相同）；`GatedPublisher`、`TrackLoop`、发布门 ①–⑤ 条件与失败处理、`K_pub` 均未改 | `tests/test_language_loop.py::ResidentSessionTests::test_resident_rebuild_servo_baseline_carries_last_written_gimbal_point`：监听 `RuntimePublisher.look_at` 实际写入序列；track 1 在 `BOX_A` 跟踪 → 删中间帧 → `REINIT_REQUIRED(frame_gap)`、载体拆除 → 下一 tick 重建（`resident_loops_started` 1→2）→ `ask`/`confirm` 指定 `BOX_B` 上的 track 2 → `TRACKING`；断言重建与再指定期间无云台写入、首条已写伺服相对重建前最后已写点 ≤ 6°、该帧直接地面点偏差 > 12° 且首条角度贴近上限（确被限速） | 红：`33.54443408552766 not less than or equal to 6.000001`（与复核探针 33.544° 一致）；绿：`ResidentSessionTests` 22 例 OK |

- fixture 走生产路径：真实 `LanguageSession`/`GatedPublisher`/`RuntimePublisher` 写桥与收据，`FixtureFramePublisher` 写生产格式帧包，`frame_gap` 由删除帧文件触发
  生产检测，重建由会话 `_ensure_resident_loop` 生产路径完成；常驻替身 `FakeResident` 内核为真实 `ResidentCore`（与 R1 回归同口径）。
- R1-1/2/3 四条回归在修复后保持全绿（同 `ResidentSessionTests`）。
- **E1/E2 不重跑（理由）**：修复只在会话常驻载体拆除/重建路径（`controller/language_loop.py`），`tools/eng_acq/` 不导入 `language_loop`；AC-6
  `ResidentCarrierReplay` 的载体不经会话层、`step`/`pointer_result` 路径未改，未复跑（每次计 2 次序列回放）；报告未重生成。
- IR-23（接受为具名残余边界）与 R1-4（`SCOPE_GAP`）不在本返工范围，未改。

## AC-11 index 散列查找

对象：`~/TetheredDroneTracking-full/outputs/eng-fast/P1-ENG-FAST-001/cache/catalog-index.jsonl.gz`（1,998,848 字节，本机 mtime 2026-09-24 22:02:39）。查找完整散列 `80971838…0fbb`（亦查前 8 位 `80971838`）与文件名 `catalog-index` 的既存记录，逐处过程与命中写在 `-assets.json`「catalog-index.jsonl.gz」`prior_record_search`：

1. 主仓库工作树全部文本文件（排除 `.git/`）：唯一散列命中是 `-assets.json` 本身（本工作项 08ac1b1 首记的本次实测值，不是独立既存来源）。
2. 主仓库 git 全历史 `git log --all -S80971838`：只命中 08ac1b1（同上）；`-S'catalog-index'` 命中 5659e02/a5b6bda/fd78169/2e7f942/08ac1b1，均为路径、构建代码或文字引用，无该文件散列。
3. 主仓库 `outputs/` 下 < 50 MB 的 `.gz` 解压检索：无命中。
4. 数据根 `outputs/ docs/ config/ tools/` 下 2,865 个文本文件（`.json/.jsonl/.md/.log/.txt/.csv/.tsv/.sha256`，只读）：散列无命中；文件名只命中 FAST-002 提案（路径与统计，无散列）。
5. 数据根 `outputs/` 下 11 个 < 50 MB 的 `.gz`（含 FAST-001 `ledger/runtime-before|after`、`transfer/fast001-code.tar.gz`、检测缓存）解压检索：无命中。
6. 数据根 git 全历史（HEAD 29a94db）：`-S80971838` 无；`-S'catalog-index'` 只命中 a5b6bda/5659e02，无散列。
7. 构建代码 `tools/eng_fast/inputs.py::build_catalog_index/load_catalog_index`：只把上游身份头写入索引首行并在加载时核对，从不计算或记录索引文件自身散列。

结论：**确无独立既存的该文件散列记录**。按 AC-11 修订 1 固定本次完整 sha256 `80971838f79a39b9763eb0d586d5d12a0aa787c4672d31423e60bc71e6de0fbb` 为后续比对基线（`baseline.status = BASELINE_FIXED_PRIOR_UNVERIFIABLE`，报告标「既往不可核」）。补充而非替代：索引首行身份头（`manifest_sha256`、`field_catalog_sha256`、151 分片、43,535 行）与独立入库证据 `docs/evidence/P1-ENG-FAST-001-inputs.json`「catalog_index」（5659e02）逐字段一致，上游两份目录文件当前 sha256 也一致——这只说明内容来源身份一致，不当作文件散列比对。

## AC-15 发布窗口与跳过发布

- 窗口：会话常驻载体 `resident_publish_window = K_pub`（`controller/language_loop.py` 构造常驻 `TrackLoop` 处，未改）；`latest − frame_id ≤ 窗口` 的处理帧走 `_publish_resident`：指针有效 → 观测 → 限速 `look_at`，二者都经 `GatedPublisher` 现有五项门（门 ①④ 未改）。
- 窗口外追平旧帧：照常 `step` + `pointer_result`（更新跟踪状态与历史），不调发布器；帧记录逐帧写 `publish_skip_reason = "outside_resident_publish_window"`（`controller/track_loop.py::PUBLISH_SKIP_OUTSIDE_WINDOW`）、`resident_publish_window`、`skipped_count = 1`、`published_* = False`。窗口内帧 `publish_skip_reason = null`。
- 限速基准：`_publish_resident` 以发布器收据判定本次 `look_at` 是否 `WRITTEN`；被门拒或静音丢弃时帧记录 `published_gimbal_command = False`、`look_at_world_m = null`，`last_servo_point` 不推进，下一条已发指令相对上一条已发指令限速。无收据表的直写发布器写入即视为已发。
- R1 返工（R1-3）：窗口判定所用 latest 改为每帧发布前重读 `latest.json`（与门 ④ 同源），批内新帧计入；批末帧出窗则本批不做机身步。详见「R1 返工说明」。
- 回归：`test_publish_window_skips_stale_backlog`（窗口 2、追平 0→7：step/pointer_result 各 8 次；观测与 `look_at` 均只在帧 0、5、6、7 各一次；帧 1–4 逐帧跳过记录）与 `test_servo_baseline_is_last_written_look_at`（帧 3 的 `look_at` 被拒：已发序列 0,1,2,4…9 相邻 ≤ 6°）在旧代码上红（`failures=1, errors=1`）、新代码上绿。

## 第二级映射

`controller/resident_core.py::level2_mapping` 逐字按 AC-3 接受释义：`RESEED_READY` → h 帧同帧收养（唯一 → `BOUND`/`resolution_level 2`；
多条过门且裕度 < m → `AMBIGUOUS`；无过门 → `NO_TRACK_AT_K`/`no_adoption`）；`RESEED_DISCARDED_MISSING_FRAME` → `not_attempted_frame_missing`；
`RESEED_DISCARDED_STALE` → `source_too_old`；`RESEED_DISCARDED_NOT_CONVERGED` → `replay_timeout@<f>`（f = 首个未处理帧 = head + 1）；
`RESEED_DISCARDED_INVALID_BOX` + `invalid_source_box` → `invalid_source_box`，+ `invalid_replay_box` → `sot_lost@<f>`（f = 失败帧）；
`RESEED_FAILED` + `tracker_init_failed` → `sot_init_failed`，其余异常 → `replay_error`（异常类记 `level2.exception_class`，不扩闭集）。
第二级失败一律 `NO_TRACK_AT_K`，不加第七值；`_finish` 对结果值与 `level2.reason` 做闭集断言。运行时帧源 = `RepositoryFrameWindow`
（与载体同一 `FrameRepository` 的只读原件，逐帧惰性读取），SOT 工厂每次指定新建（缺省冻结 `nanotrack-v2`），框只用于 h 帧收养判定。
离线线束用前缀共享实现 `tools/eng_acq/e1.py::PrefixSot`，与 `replay_tracker(k→h)` 的逐事件等价由 `tests/test_eng_acq_e1.py::PrefixEquivalence` 证明。

## 承接声明

- **H-1（F3，`LanguageWorker`/延迟排队域）**：**未触及**。`LanguageWorker` 类零改动；查询帧选择（`_acquire_frame`）、在途起点、pending
  替换与排队语义零改动。常驻模式只在 `_issue_designate` 发查询前追平常驻载体（`step` 到最新帧，使查询帧 N 进入历史），不改查询时刻与年龄起点。
  故不附在途起点回归（合同：触及才须附）。
- **H-2（F8，可变归档）**：E1/E2 只读数据根归档，不改写；线束逐帧核对 JPEG sha（FAST-002 数据集清单）、sidecar `frame_id` 与文件名、
  `simulation_time_s` 与 FAST-001 时刻索引，不一致即 `IntegrityStop`（`tools/eng_acq/data.py`）；本次 4,832 帧全部一致。H-5 移动的
  `runtime/hold-diag-loopb-*` 不是 E1/E2 的输入归档。
- **H-6**：常驻逐帧处理取代「在 N 帧 init + 回放积压」；发布最终门五项与 `K_pub 2`/`T_pub`/`T_stall 3 s` 数值不变；常驻会话把门 ④ 的同一
  `K_pub` 用作「追平期间只处理不发布」的窗口（IR-3）；诊断 6 记录不改。
- **H-3/H-9**：见 AC-18/AC-8。

## 人眼保真

- 采集、保存、预览渲染代码（`render_preview`、`FrameSnapshotRing`、`SnapshotRepository`、Unity 侧）**零改动**。
- 但 S2-d 新增的 `CandidatesBackend` 把检测 track 作为候选经同一预览路径呈现给操作者——按 H-4 读作「触及预览内容」。样帧 S1/S2/S3 的用户逐张核对已记录于 `docs/unity-test-log.md`「P1-ENG-ACQ-001 — AC-17 人眼保真样帧核对」；接受裁定见提案「Play D1 信封与 AC-17 样帧核对落实（2026-09-29；CLARIFY）」。正式 Play 尚未运行，AC-18 `NOT_RUN`。

### 当前候选预览样帧清单（K1K2K3样帧派发 `P1-ENG-ACQ-001-K1K2K3样帧-20260929T192152Z-bdfc`）

**状态：用户已逐张核对 S1/S2/S3，均答“无问题”。** 来源见上述 Unity 日志与用户授权账本同日 Play D1 条目；这仅覆盖既往归档帧经当前候选路径离线渲染的人眼核对，正式 Play 同帧实时预览仍待记录。下表源帧、候选框与哈希为实现准备时记录；确认人/结论按用户代录更新，不把实现者自查充作人眼结论。

- **代码版本**：渲染时 HEAD `4162a01`；与 R3 §7 `passed_candidate` `3a2f583` 之间 `controller/`、`tools/`、`tests/`、`config/` 零差异（`git diff --stat 3a2f583 4162a01 -- controller tools tests config` 为空）。本节提交只改证据/账本/状态板，**不产生新候选**：文首「候选 = 本文件最后一次修改所在提交」的解析自本派发起改以 R3 §7 `passed_candidate` 为准。
- **渲染路径（当前候选同一预览路径）**：逐帧 `HistoryEntry` → `CandidatesBackend.bind_history` + `predict_one`（按面积降序取 ≤8 条 `tracked` 行，0–1000 取整）→
  `controller.language_selector.interpret` → `controller.language_loop.render_preview`（红框 + 候选 index；`tracker_box=None`，与 `_issue_designate` 后 `_preview` 同参）。
  命令：`~/TetheredDroneTracking-full/.venv-yoloe/bin/python outputs/eng-acq/P1-ENG-ACQ-001/human-fidelity/render_hf_samples.py`（脚本不入库，sha256 `d8861c5bfa3e1789fd781fbdcbd006bef2866147c37fd249a633919c63b036b6`；清单 `outputs/eng-acq/P1-ENG-ACQ-001/human-fidelity/manifest.json` sha256 `164d9147b24e2e81dd980fb945a5e5e7ecf01a1a6e0713ab226fa631bea0573e`）。
- **历史来源（已有输出，零回放）**：E2 已写的常驻关联记录 `outputs/eng-acq/P1-ENG-ACQ-001/records/<序列>-pose-b30.json.gz`（`gmc_source=pose`、`track_buffer=30` = 常驻插件缺省；逐帧即
  `ResidentCore.record` 的 `HistoryEntry.as_record()`，输入为冻结检测缓存 `outputs/eng-det/dets/frozen-B|V.jsonl.gz`）。sha256 与 `docs/evidence/P1-ENG-ACQ-001-e2.json` 的 `records_sha256` 一致：
  scout-1 `0102f663…f39e`、a7 `71227f75…192a`。记录写出后，产生行的代码（`det_assoc_tracker`、`pose_gmc`、`tools/eng_acq/e2.py`/`data.py`、`tools/eng_fast/replay.py`）零改动；
  `resident_core.py` 仅加 `width/height` 字段与指针/coasting 记账（不改 `record` 产出的行）。
- **源帧**：数据根只读 JPEG，先按 FAST-002 数据集清单核 sha（H-2）。这是既往 Unity 运行的归档帧，**不是本项 Play 的同帧实时画面**：离线样帧核对的是「候选框/index 是否落在图中对应车辆上、颜色身份是否可辨」，与 Play 同帧实时外观的核对只能在 Play D1 内进行。
- **挑帧规则（确定性；真值只用于挑帧和写「期望对象」，不进入候选或渲染）**：`tracked` 行 2…8（无截断、状态 `ambiguous`）；某 `tracked` 行与目标真值 IoU ≥ 0.7；目标框距四边 ≥ 1%（不贴边）；取目标面积最大，并列取段序/帧号最小。
  前两次渲染被本规则取代（首次无不贴边条件、m3-armA 选中贴边集装箱；第二次 m3-armA 无合格静止车帧，S2 改取 scout-1），产物移至 `human-fidelity/superseded-run1|2/`，不作证据。

| 样帧 | 预览 PNG（`outputs/eng-acq/P1-ENG-ACQ-001/human-fidelity/`）与 sha256 | 源帧（数据根相对路径；sha256） | frame_id / sim t | 候选（index：track id，像素 xyxy 640×480） | 期望对象（真值，仅供核对参照） | 确认人 / 结论 |
|---|---|---|---|---|---|---|
| S1 红车 | `S1-red-scout-1-seg0-frame_0000000672.png`；`b2df65afd0e77ac384cd91c6c0da27b274ba79a1852a157dc7dc55e789efb93a` | `runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames/frame_0000000672.jpg`；`d8c56dee…5b97` | 672 / 105.912 s | 0：165（403,319,484,447）；**1：107（290,201,357,277），cls 1 `target`** | 红车 = index 1 / track 107（IoU 0.72） | 用户 / 无问题 |
| S2 静止车 | `S2-static-scout-1-seg0-frame_0000000702.png`；`fa5ae2a90c7e3d33b84d2fbac7a1d749f1f60877a650aeceedd18f938d6c8d31` | 同上目录 `frame_0000000702.jpg`；`2e8619ea…0142` | 702 / 110.611 s | **0：167（419,199,550,337）**；1：165（327,90,448,216）；2：107（284,200,361,284），cls 1 | 静止 `Vehicle_Taxi (2)` = index 0 / track 167（IoU 0.87）；同帧红车 = index 2 | 用户 / 无问题 |
| S3 静止车（补充，选择域 a7） | `S3-static-a7-seg0-frame_0000001294.png`；`d15fb039ef6a54eb7aa9383d22ab25b2f2aac7000e8a5e818c251b7ca7287a81` | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000001294.jpg`；`f591addc…7e6d` | 1294 / 258.987 s | **0：395（122,265,326,473）**；1：396（0,44,104,128） | 静止 `Vehicle_Pick up Truck_color01 (2)` = index 0 / track 395（IoU 0.95） | 用户 / 无问题 |

完整候选框（0–1000 与像素）、分数、`raw_backend_text` 见 `manifest.json`。**实现者渲染自查（不是 AC-17 人眼核对）**：三张均生成、框数与 index 与上表一致；
index 用 Pillow 缺省小字号红字画在框左上角，落在红车上时（S1 index 1）对比度低；S3 期望静止车为橙红色皮卡，外观与红车同色系。两点交用户核对时判断，本轮不改代码。
消耗：序列回放 +0；本机 CPU +7.7 s（账本条目 76–79：三次渲染 1.1/0.9/0.8 s + 只读探查补记 5 s）；检测推理、YOLO 权重加载、ID/Play/API 均 0。

## 复核范围（`R3@K1K2K3`；R2-1 返工增量）

- 被复核候选 = 本文件最后一次修改所在提交；上一复核轮候选 `round_candidate` 见 `docs/reviews/P1-ENG-ACQ-001.md`「R2@K1K2K3」§0。
- 修复触及：`controller/language_loop.py::LanguageSession.__init__`（新属性）`/_ensure_resident_loop/_teardown_resident`；
  `tests/test_language_loop.py`（新增一条回归）。
- 阻断 finding 红绿：对 2b50cf6 `git revert -n`，跑上表回归（`.venv-language`）；复核写 `releases_consuming_gate: R2-1`。

## 复核范围（`R2@K1K2K3`；R1 返工增量）

- 被复核候选 = 本文件最后一次修改所在提交；上一复核轮候选 `round_candidate` 见 `docs/reviews/P1-ENG-ACQ-001.md`「R1@K1K2K3」§0。
- 修复触及：`controller/language_loop.py::_begin_acquiring`（R1-1）；`controller/gated_publisher.py::GatedPublisher.__init__/look_at/slew_look_at/_point3`、
  `controller/track_loop.py::_servo_baseline/_publish_resident`（R1-2）；`controller/track_loop.py::_process_resident`（docstring）`/_resident_frame/_publish_time_latest`（R1-3）；
  `tests/test_language_loop.py`（`FakeResident.on_step` 与四条新用例）。
- 阻断 finding 红绿：对 922230e / 7cf133c / 264a034 各 `git revert -n`，跑上表对应回归（`.venv-language`）。
- 待裁定新增 IR-23（R1-3 残余竞态与批末帧机身步）、IR-24（常驻载体重建后限速基准清空）见「待裁定」，均为读法/已知边界，不在 R1 finding 范围内。

## 复核范围（`R1@K1K2K3`；含 FAST-002 插件代码复核承接 H-7/AC-12）

- **整个** `controller/det_assoc_tracker.py`（含 FAST-002 原有 `compat` 路径全文，不只看 diff）；`controller/trackers.py` 工厂
  （`create_tracker` 含 `resident=True` 分支）；`controller/track_loop.py` CLI 闭集（`--tracker` 选项与既有路径）及新增常驻路径
  （`start`、`_process_resident`、`_resident_frame`、`_publish_resident`、`servo_clamp`、`is_resident_tracker`）。
- 新模块：`controller/resident_core.py`、`controller/pose_gmc.py`；`controller/gated_publisher.py`（`slew_look_at`、`clear_association`）；
  `controller/language_bridge.py`（闭集、`designation`）；`controller/language_loop.py`（`resident` 分支全部方法、`CandidatesBackend`、
  `--resident`）。
- 线束：`tools/eng_acq/`（`common`、`data`、`e1`、`e2`、`run`、`report`、`cleanup`）；证据 JSON 与报告。
- C1 返工增量（`git diff fda0c6d..<候选>` 的实现文件）：`controller/resident_core.py::_update_coasting` 边界；`controller/track_loop.py`
  `_resident_frame`（`publish_skip_reason`）、`_publish_resident`/`_receipt_count`/`_look_at_written`（已发基准，IR-22）、`_append_record(resident_fields)`；
  `tools/eng_acq/report.py::deviation_section/ledger_section`；对应测试。C1 预复核关注项（`_begin_acquiring` 首个 `slew_look_at` 用 k 帧世界点 vs §3.7 外推）本返工未改，仍交 R1 核实。
- K1：历史键与时间语义、`step` 帧序、发布窗口与门、静音播种退役；K2：`slew_look_at` 通道、限速、超时、`hold` 回退、速度 `orphan_control`；
  K3：指针、六值闭集、第二级、状态机、插件身份。PLAY_GOVERNING：会话与载体（非空）。
- 重跑：系统 `python3` focused（纯 Python）；`.venv-language` 跑 `tests.test_language_loop tests.test_language_bridge`；数据根
  `.venv-yoloe`（`cd tests && …/python -m unittest test_det_assoc_tracker …`）跑库用例。**`test_det_assoc_carrier.CarrierSelfTest`（FAST-002 口径 C）
  在有权重的 `.venv-yoloe` 下会做真实检测推理**，本项信封检测推理 = 0，故本批从未运行它；复核如需重跑请自行确认额度。`ResidentCarrierReplay`
  每次运行记 2 次部分序列回放。

## 测试（COORD-009；基线已有失败与本批新增失败分列）

- **R2-1 返工 7a42**：停点全套 `python3 -m unittest discover -s tests > docs/evidence/P1-ENG-ACQ-001-tests.log 2>&1`（系统 python3 3.9.6）：Ran 1641，
  `FAILED (errors=82, skipped=79)`；82 个 error 的测试名集合与上一候选（1d8f 全套）逐一相同（新回归在 `test_language_loop`，3.9 下整模块导入失败，不计入该数），
  **本批新增失败 0**。解释器分组 focused（`docs/evidence/P1-ENG-ACQ-001-focused-venv-tests.log` 末段）：系统 python3 105 通过（12 跳过为库用例）；
  `.venv-language` 四模块 244 通过（2 跳过）；数据根 `.venv-yoloe` 97 通过、**8 跳过**——`test_det_assoc_tracker` 库用例，因本机 `.venv-yoloe` 当前
  `import lap` 失败（`ModuleNotFoundError`，环境问题，与复核 R2 所记一致；未安装任何包，pip/下载 0）；该模块覆盖的 `controller/det_assoc_tracker.py` 本返工未改。
- **R1 返工 1d8f**：停点全套 `python3 -m unittest discover -s tests > docs/evidence/P1-ENG-ACQ-001-tests.log 2>&1`（系统 python3 3.9.6）：Ran 1641，
  `FAILED (errors=82, skipped=79)`；82 个 error 的测试名集合与上一候选（c5a7 全套）逐一相同（`test_language_loop` 在 3.9 下整模块导入失败，新增 4 例
  因此不计入该数），**本批新增失败 0**。解释器分组 focused（`docs/evidence/P1-ENG-ACQ-001-focused-venv-tests.log` 末段）：系统 python3 105 通过（12 跳过为库用例）；
  `.venv-language` `test_language_loop test_language_bridge test_gated_publisher_slew test_track_loop` 243 通过（2 跳过；提交前 IR-19 冻结路径用例按预期失败 1 次）；
  数据根 `.venv-yoloe` 97 通过。修前红/修后绿见「R1 返工说明」。

- 停点全套（C1 返工 c5a7 重跑）：`python3 -m unittest discover -s tests > docs/evidence/P1-ENG-ACQ-001-tests.log 2>&1`（系统 python3 = 3.9.6）：Ran 1641
  （较上一候选 1637 新增 `test_resident_core` 3 例与 `test_track_loop::test_servo_baseline_is_last_written_look_at`），`FAILED (errors=82, skipped=79)`。82 个 error 的
  测试名集合与上一候选（d991b86）全套**逐一相同**（此前已核对与首派候选、上一停点基线 `docs/evidence/P1-ENG-FAST-002-tests.log` 相同：3.9 不支持的注解语法与
  缺依赖导致的导入/运行错误，含 `test_language_loop` 整模块导入失败）；**本批新增失败 0**。
- 解释器分组 focused（`docs/evidence/P1-ENG-ACQ-001-focused-venv-tests.log` 末段）：系统 python3（AC-6 cmd 六模块）108 通过（15 跳过为库用例）；`.venv-language`
  `test_language_loop test_language_bridge` 214 通过（代码提交 22ee16c 后；提交前 IR-19 冻结路径用例按预期失败 1 次）；数据根 `.venv-yoloe` 97 通过
  （`test_det_assoc_tracker`、`test_det_assoc_carrier.ResidentCarrierCalls`、`test_resident_core`、`test_pose_gmc`、线束三模块）。修前红：新增 coasting 3 例与
  AC-15 两例在旧代码上失败（见日志）。`CarrierSelfTest`（真实检测推理）与 `ResidentCarrierReplay`（计 2 次序列回放）本返工未运行，理由见「C1 返工说明」。

## 消耗（账本 `docs/evidence/P1-ENG-ACQ-001-ledger.json`）

**R2-1 返工 7a42 增量**：序列回放 +0（累计 35 / 40）；本机 CPU 墙钟 +140 s（focused 与修前红/修后绿保守 15 s、全套 125 s；账本条目 74–75），累计约 4,638 s / 10,800 s；
其余维度仍全 0（ID/Play/API/VLM/训练/检测推理/YOLO 权重加载/下载/pip/5060 或远端访问）。

**R1 返工 1d8f 增量**：序列回放 +0；本机 CPU 墙钟 +145 s（focused 与修前红/修后绿保守 20 s、全套 125 s；账本条目 72–73），累计约 4,498 s / 10,800 s；
其余维度仍全 0。以下为此前累计叙述：

序列回放 35 / 40（27 次关联回放 + AC-6 载体自测 4 次 × 2 条部分回放，保守计；两次续派与 C1 返工均 0 次）；本机 CPU 墙钟约 4,353 s / 10,800 s（C1 返工 c5a7 增量 175 s：
AC-11 只读查找与散列 30、focused 与修前红/修后绿 15、全套 120、报告重生成 10，均保守计，账本条目 68–71；第二次续派 e3c8 增量约 1,010 s：
E1 两臂各两次 166/167/274/274 s、合并 0.03 s、全套 119 s、focused/报告/只读核对保守 10 s；上一续派 9b04 增量约 998 s）；第二级 NanoTrack 起跟 27,793 次、更新 789,215 帧
（e3c8 增量 7,348 次、212,166 帧；首派各次每 (k,o) ≤ 65 帧、每 序列 × gmc × 臂 ≤ 600 个 (k,o)；9b04 a7 全样本、其他 ≤ 600、每 (k,o) ≤ 66 帧；e3c8 同 9b04 但 scout-1 每 (k,o) ≤ 87 帧，线束断言）；
其余维度全 0（ID/Play/API/VLM/GPU/检测推理/YOLO 权重加载/下载/pip/5060 或远端访问）。失败与重复运行均已计入：E1 干净臂首次因内存增长被手动终止（46 s）；
扰动臂第 2 次被后台命令重复启动而多跑一次（输出与前两次字节一致）；IR-20 修正后 E1 两臂四次整体重跑（输出与第一轮逐字节相同）；停点全套与 focused 在最终代码上各复跑一次；
9b04 与 e3c8 各有 E1 两臂四次整体重跑（被取代的 9b04 输出移至 `outputs/eng-acq/P1-ENG-ACQ-001/e1/superseded-9b04/`，不入证据）。C1 返工派发全部运行成功，无失败条目（修前红为有意的回归验证）。

## 待裁定（实现读法，请接受角色裁定；实现角色不写提案）

- **IR-1**（§3.4 判据）：裕度 m 只在 IoU ≥ τ 的过门轨迹之间计算（唯一过门即取，不再要求与门下次佳差 ≥ m）；备用判据「轨迹框中心落在指定框内」
  只在零条过门时启用且须恰好一条满足，≥ 2 条或 0 条 = 无轨迹过门（进入第二级）。第二级收养用同一函数。
- **IR-2**（§3.1）：`TrackLoop` 以「具备 `step` 且 `mode == "resident"`」判定常驻协议（`compat` 模式 det-assoc-v1 也有 `step` 属性）。
- **IR-3**（§3.5/§3.8 与门 ①④）：常驻载体读帧、处理、发布逐帧交替；`resident_publish_window`（会话取 `K_pub`）内的帧逐帧发布观测 + 限速
  `look_at`，追平期间更旧的帧只 `step` 不发布（否则门 ①/④ 必判 `catchup_stale`）；机身步只在批末帧（规划器输入路径不变）。
  （C1 裁定：按 AC-15 修订 1 执行；C1 返工已加逐帧跳过记录，见「AC-15 发布窗口与跳过发布」。）
- **IR-4**（§3.2 帧序终止）：常驻会话遇回退/缺帧/门拒/停帧时关闭常驻载体（历史清空）；有指针或处于 `TRACKING`/`SUSPECTED`/`ACQUIRING`
  时进入 `REINIT_REQUIRED(同名)`，否则保持当前状态并在下一 tick 从最新帧重建；停帧判据只在有指针或转向中生效。
- **IR-5**（§3.5 `retired_track_ids`）：跟踪中改指定时旧纪元的 `retired_reason` 取既有闭集值 `operator_release`（不新增原因）。
- **IR-6**（§3.6/§3.7）：`TRACK_ENDED` 确认后立即退旧指针（转向期间不再服务旧目标），并清除发布器同帧关联；收养时多条满足且裕度 < 15 px
  → `ACQUIRE_FAILED`，`designation.result = AMBIGUOUS` 并列候选，状态 `LOST(acquire_failed)`（表内无单列迁移）。
- **IR-7**（§3.7 到位判据）：角速率 = 相邻历史帧四元数夹角 / 仿真时刻差；投影点 = 世界点（k 帧位姿 + 指定框底中点 ∩ 地面；k 帧命中轨迹在历史中
  有 ≥ 2 帧 tracked 时按首末地面点差分速度外推）按该帧位姿投影；`T_slew` 以会话单调时钟计。
- **IR-8**（§3.4 coasting 上限）：`BOUND_COASTING` 的等待上限 = 库移除或自指定起 `coasting_limit` 次 `step`，先到者即核心事件
  `COASTING_TO_TRACK_ENDED`；若该指定从未找回（同一 `designation_id`、尚未捕获），会话按表「超时 → 转 `TRACK_ENDED` 处置」自动进入第三级
  `ACQUIRING`（D.1 允许的同一指定之内自动执行）；若已找回（`COASTING_RECOVERED`）后再丢，属捕获后丢失，只走 `SUSPECTED`、不自动转向。
  同 id 重复 `follow` 不清 coasting 记账，换 id 才清。测试：`test_acquiring_after_coasting_timeout_same_designation`、
  `test_acquiring_not_after_recovered_then_lost`。（C1 退回：上一候选实际第 31 次才触发；C1 返工改为第 30 次触发，见「C1 返工说明」。）
- **IR-9**（信封 65 帧上限 vs Δ = 13 s）：采集帧间隔 p50 0.199 s，Δ = 13 s 的解析帧常在 k + 66；需要 > 65 帧的第二级回放不运行，
  层记 `NOT_EVALUABLE_FRAME_CAP`，不入桶、不冒充 `NO_TRACK_AT_K`（与 AR2-2 同一处理方式）。改上限属信封变更，交用户（needs_user）。
  （续派注：用户已按 SUB:2 改为 ≤ 66；处理方式不变，现行上限 66，见 IR-21。）
- **IR-10**（§5「CPU 序列回放 ≤ 40 + E1 解析」）：E1 解析读取 27 次回放中 buffer 30 的关联记录流，逐帧交同一 `ResidentCore.record` 后在 r 帧
  `designate`，记为「E1 解析」而非序列回放；第二级 SOT 按 (段, k, 框) 在同一进程内跨 gmc_source 复用、各 Δ 共用前缀（结果与 `replay_tracker`
  等价，测试见上）。
- **IR-11**（离线第二级时钟）：scout-1 sidecar 为 v1、无 `capture_monotonic_s`，线束 STALE 判定改用 `simulation_time_s`（运行时仍用 v3 单调钟）。
- **IR-12**（AC-9 `runtime/` 零写入）：读作线束运行期写入；§3.4 明令同步的已跟踪文档 `runtime/README.md` 为文档改动，不属线束写入。
- **IR-13**（AC-16 修订 1「本地删除」）：7 个 hold 目录以**移入当前用户废纸篓（可恢复）**方式从 `runtime/` 移除（本执行环境不做不可恢复删除）；
  永久清空由用户决定。「本地 `runtime/`」读作采集副本（数据根）的 `runtime/`——主树 `runtime/` 下无同名目录（清单已记 `NONE_ABSENT`）。
- **IR-14**（记账口径）：AC-6 载体自测每次计 2 次部分序列回放；开发期 focused、探针与进程启动开销合计保守记 90 s（账本条目 `overhead_and_dev`）。
- **IR-15**（E2 读数定义）：每对象 ID 切换 = 真值 IoU ≥ 0.3 逐帧绑定后的 `sequence_metrics.id_switches`；静止车 track 寿命 = 每个（静止车, 绑定 id）
  首末帧仿真秒差。红车保持率在 m3-armA 按段（会话）切窗（同 FAST-002 IR-4 方向，已在报告偏差声明中列出）。
- **IR-16**（§3.6「回到确认前状态」）：取 `ask`/`respecify` 进入 `QUERYING` 时的状态（含 `SUSPECTED` 的疑点 id 与原因）；该状态依赖的指针已不在时
  降为 `LOST`。
- **IR-17**（S2-d CLI）：`CandidatesBackend` 已实现并有测试；K 收据对非 VLM 后端的宿主/时延绑定未定义，故未接入 CLI `--backend`，
  列为 Play D1 准备项。
- **IR-18**（第二级参数生效值）：`history_depth 128`、`L_replay 128`、`T_replay 2.0 s`、`maximum_source_age = 128 / capture_hz`；
  §3.7/§3.8 申请值为会话配置缺省（`AcquireParams`、`servo_omega_max_deg_s 30`）。
- **IR-20**（E1 样本独立性）：线束在每次 `designate` 解析并分桶后撤指针（`follow(None)`），使上一次指定的 coasting 记账（含
  `coasting_limit` 标记的已结束 id）不影响下一个 (k, o, Δ) 的解析。该修正在第一轮 E1 四次运行之后加入，E1 两臂四次运行随即整体重跑；
  重跑输出与第一轮逐字节相同（两臂 sha256 不变），即第一轮未受该污染；证据取重跑结果，两轮消耗均计入账本。
- **IR-21**（续派 9b04；SUB:2 的 66 帧不覆盖 scout-1 Δ13）：IR-9 的「k + 66」只对 a7、m3-armA 成立（两序列 Δ13 帧号差 65–66）；
  scout-1 帧间隔更短，Δ13 帧号差 77–87（685 个 k，报告「E1」只读统计）。按修订 2 字面（全部序列每 (k,o) ≤ 66 帧、超过者不得伪装成已运行），
  scout-1 第二级触发 (k,o) 在 Δ13 上仍不运行，干净臂每 gmc 62–68、扰动臂 191–194 个 (k,o,Δ) 未运行，scout-1 Δ13 层（每臂每 gmc 最多 6 层，合计 32 层）
  记 `NOT_EVALUABLE_FRAME_CAP`；未自行放宽。是否再改上限属信封变更，交用户（needs_user `P1-ENG-ACQ-001:5db2576c:SUB:3`）。
  （第二次续派 e3c8 注：用户已批准 SUB:3，scout-1 现行上限 87、a7/m3-armA 仍 66（AC-7/20 修订 3）；读法与处理方式不变，结果见 AC-7/AC-20 行。）
- **IR-19**（LOOP-001 冻结测试）：`test_language_loop.StateMirrorTests::test_frozen_paths_are_untouched_in_the_working_tree` 把
  `controller/track_loop.py` 列为 LOOP-001 冻结路径；本项合同（S1-f、§3.8）必须改它。该测试只查未提交改动，候选提交后通过；其冻结意图随
  LOOP-001 `CLOSED_SUPERSEDED` 是否仍有效，请接受角色裁定是否在后续把该路径移出该测试（本批未改测试）。
- **IR-22**（C1 返工；AC-15 修订 1「相邻已发指令」）：限速基准 = 上一条**已写入**的 `look_at`。门控发布器以本次调用新增收据中是否有 `look_at`
  `WRITTEN` 判定；被门拒（`PUBLISH_REJECTED`，门条件与失败处理不变、仍置 `fatal_reason` 由会话终止该段）或静音丢弃时不推进基准、帧记录不记已发；
  无收据表的直写 `RuntimePublisher` 写入即返回、写失败抛异常，视为已发。上一候选无论是否写入都推进基准，同批后续帧可能相对未发点再限速一次
  （相邻已发指令最多 2×ω_max/hz）；回归 `test_servo_baseline_is_last_written_look_at`。
- **IR-23**（R1 返工；R1-3 的残余边界）：窗口判定与门 ④ 读同一个 `latest.json`，但两次读之间（门 ①②③ 的快照与盘上字节核验，毫秒级）
  若恰有新帧写出、且该帧差恰为 `K_pub`，门 ④ 仍会判 `catchup_stale` 并按原失败处理（fatal → `REINIT_REQUIRED`）；同样的毫秒级间隙存在于同帧观测门与
  `look_at` 门之间。本返工不改门的条件与失败处理（AC-15 修订 1），故保留该 fail-closed 残余；5 Hz 下仅在追平批的窗口边缘帧出现，概率约为门核验耗时 / 帧周期。
  若要彻底消除，须把窗口判定并入门 ④ 的同一次读取或对非最新追平帧收窄一帧，二者都改变门或窗口口径，需接受角色裁定。另：批末帧被批内新帧挤出窗口时
  本批不做机身步（`_body_step` 仍只在批末帧运行，规划器输入不变）。推荐：接受现状（fail-closed、不削弱门），Play D1 以 `catchup_stale` 次数观察。
- **IR-24**（已裁定 = R2-1 路径 (a)，R2-1 返工 7a42 已修，见「R2-1 返工说明」；以下为原记录）（R1 返工；R1-2 的边界）：限速基准来自当前常驻载体的 `GatedPublisher`；常驻载体因会话级终止（回退/缺帧/门拒/停帧）重建后，新发布器
  无已写记录，新 `BOUND` 的首条伺服不限速（与 R1 前行为相同，属重建语义，不在 R1-2 finding 的收养/`ACQUIRE_FAILED` 路径内）。推荐：接受角色裁定是否
  要求跨载体重建沿用会话级最后已写云台点（改动小：`_ensure_resident_loop` 把旧发布器的 `last_gimbal_point_world_m` 交给新发布器）；本返工未做。

## 已知限制与未验证项

- E1/E2 是离线单进程、无 Unity 同机负载、无发布门的机制读数；不外推为在线捕获成功率或转向中在线存活；不设门。
- a7 E1 全样本已在续派完成；scout-1 的 Δ = 13 s 层已在第二次续派（SUB:3，87 帧）运行，E1 无不可评估层；scout-1 的 63 个 FAST-002 整帧排除帧按不可见处理，红车误锁率可能被高估（报告偏差声明）。
- 常驻会话、转向通道、限速在真实 Unity 中的行为（云台 `RotateTowards` 120°/s 与 45° 限位、到位判据阈值、收养半径）只有 Play D1 能证实；
  本批只有替身与夹具自测。第二级运行时路径（NanoTrack 实例化于 `runtime/models/nanotrack-v2`）在主树无模型文件，需在采集副本运行。
- 候选来源后端未接 CLI（IR-17）。
- R1 返工的边界：IR-23（窗口判定与门 ④ 之间毫秒级残余竞态，fail-closed；接受为具名残余边界，Play D1 记 `catchup_stale` 次数）；IR-24 已由 R2-1 返工修复；R1-4 `SCOPE_GAP` 未修。

## Unity 用例

零 Play。Play D1（§3.10 剧本，正式用户 Unity 验证 `UT-P1-ENG-ACQ-001-D1`）须用户另签 1 次 Play 信封，并先完成人眼保真 ≥ 2 张样帧。

## 待用户（needs_user）

- R2-1 返工无新增待用户、无新增待裁定。
- R1 返工无新增待用户；IR-23/24 交接受角色裁定（不阻断 R2）。
- 以下为此前记录：无新增。C1 的两项待用户（IR-3/AC-15、AC-11 来源散列）已由用户裁定（账本 2026-09-29「用户裁定 C1 待用户两项…」），本返工按修订 1 落实。
  Play D1 信封仍另签（AC-17/18 `NOT_RUN`），不属本轮申请；推荐 R1 通过且人眼保真前置准备完成后由用户另签。
