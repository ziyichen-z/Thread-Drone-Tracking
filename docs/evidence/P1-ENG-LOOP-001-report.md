# P1-ENG-LOOP-001 阶段 A 实现报告（当前 K1K3 候选；下文保留离线批历史）

Work ID: `P1-ENG-LOOP-001`
Workflow: `engineering-v1`（提案抬头逐字，接受角色 D4 `ACCEPTED` 时写明裁定）
合同: 提案 §1…8、AC-1…17、文末八行首次接受释义，以及 Pending rulings 的**十行实现期修订**
（P-A-1…8、P-B-1 与 P-B-2，2026-09-20；冲突处以后者优先）
信封: `docs/authorizations.md` 2026-09-19「签发阶段 A（候选 1，离线）执行信封，交实现角色」
Owner: Implementation（Claude Code `/implement`）
Last updated: 2026-09-20（U-A-1 残留修正、P-B-2 裁定同步与 AC-8 loop 侧补证之后更新）

## 当前实测批（2026-09-20，Implementation / Cursor）

本文件下文 §0…11 保留此前离线批历史。当前批依据用户当场指令执行可访问机器，
并按后续 T7 指令迁移下载、模型、依赖与中间件；最新结果以
`P1-ENG-LOOP-001-measurement-report.md` 为准，最新操作单为
`P1-ENG-LOOP-001-operations.md`。旧文中的「零下载/零模型、实测待安排」只指此前
离线批，不再代表当前累计消耗。当前实测及 AC-10 运行时绑定修复已齐，最终选择 5060/http/c2-adapter，K=30/50/2。当前为 K1K3 稳定候选，完整结果见实测报告 §6…8，自证与核对范围见 `P1-ENG-LOOP-001-K1K3-handoff.md`。下文旧批的待测/未到停点状态均属历史；阶段 B 仍未授权。

## 0. 本批的状态与边界（先说清楚它**不是**什么）

本批只做阶段 A 合同里**纯离线**的那一半：代码、无 GPU 测试、依赖说明、操作单、
可运行示例。用户当日选定的执行分工是「先代码 + 测试，两机实测另批安排」，因此：

- **AC-9 的合并等价、AC-10 的两机时延、AC-12 的 `pip check` 都还没有实测数据**，
  三份证据 JSON（`-latency-mac.json` / `-latency-5060.json` / `-merge-equivalence.json`）
  **有意不创建**——AC-10 修订 1 写明「实机时延值尚未产生，不虚填」。本报告的
  §K 收据一节因此是空的，只写产出方式。
- 所以本批**不构成 `K1K3` 停点候选**，不进接受角色核对轮 `C1@K1K3`：
  workflow §4.3.1 的四项自证里「证据齐备」一条不成立。状态只记 `IMPLEMENTING`。
- **2026-09-20 追记**：接受侧对报告 §9 的八问作出裁定，追加八行同编号 AC 修订
  （提案 `## Pending rulings`，新 AC = 0）。本批已按八行逐条落实代码、测试与本报告；
  其中 **P-A-5 驳回了原来的预览退化做法**，现在没有生成预览就不许确认播种。
  两个解释器各跑一次的理由见 §3。
- **2026-09-20 再追记（本次增量）**：① 修完接受侧在用户指定增量查看里点名的
  **U-A-1 残留**（恢复用的 `GET /status` 跨原总截止），见 §9.5；② P-B-2 已裁定
  采纳 (a) 并追加 **AC-16 修订 3**，本报告与具名证据同步，见 §9.2 与 §2.2；
  ③ 补上 §2.1 自披露的 **AC-8 修订 1 loop 侧「超时仍 busy」缺口**。
  本次增量仍是离线件，仍不构成 `K1K3` 停点候选，仍零消耗。
- 本批**零消耗**：0 次模型运行、0 次合并、0 次下载、0 次 Play、0 个 scenario/
  session/run ID（所有会话与段归档只写临时目录）、0 次外部 API。信封额度分文未动。

## 1. 交付件

| 文件 | 内容 | 对应 AC |
|---|---|---|
| `controller/language_bridge.py` | 三个桥文件的 schema/闭集/可空规则与原子发布、§3.7 受限文法、写者锁与会话锁 | AC-1 |
| `controller/gated_publisher.py` | 加载时快照、会话帧环（可钉住在途查询帧）、`SnapshotRepository`、发布最终门五项与收据 | AC-3 |
| `controller/language_selector.py` | `InferenceAdapter` 协议、三态解析（调冻结 `parse_prediction`）、等价判定、`replay`/`local-hf`/`http` 三后端 | AC-8、AC-9 |
| `controller/language_loop.py` | K 收据与宿主决策、`LanguageWorker`、八态×九动作状态机、四个检查点、静音播种与追平、角色 B 核验、`FixtureFramePublisher`、操作者 CLI | AC-2、4…7、10、16、17 |
| `controller/language_demo.py` | `replay-demo`：夹具帧 + 冻结资产真实预测的协议走查 | AC-9 |
| `tools/language_serve.py` | 5060 单工提交/轮询 HTTP 服务 | AC-8 |
| `tools/language_latency.py` | 时延测量、合并等价、K 收据生成 | AC-9、AC-10 |
| `tools/requirements-language.txt` | `.venv-language` 钉版（与 SFT-002 同版，平台差异只在 torch 轮子） | AC-12 |
| `runtime/README.md` | 新增三条目 + `confidence_source` 闭集与**未校准**含义 | AC-1 |
| `tests/test_language_bridge.py` / `test_language_selector.py` / `test_language_loop.py` | 无 GPU 测试，全部写临时目录 | AC-1…9、12、16、17 |

`Assets/`、`config/`、`tools/eng_sft/` 与 `controller/` 的既有文件**零改动**（见 §4）。

## 2. 逐 AC 自证状态

「满足」= 本批有可复现的具名测试或工件；「待实测」= 代码就绪、缺两机实测；
「待 Play」= 阶段 B 授权后才可能产生。带 † 的证据只在有 Pillow 的解释器上跑，
见 §3 的第二跑。

### 2.1 原 AC-1…17（含首次八行释义）

| AC | 状态 | 证据指针 |
|---|---|---|
| AC-1 | 满足 | `tests.test_language_bridge`（42 项：三 schema、七值回执逐一枚举、可空规则、未知 `action`/`status`/`reason`/`verdict` fail-closed、写者锁 `WRITER_BUSY` 与持有者规则、会话锁 `SESSION_SLOT_BUSY`、`runtime/README.md` 三条目）；`test_language_loop.RequestLifecycleTests`（去重、外来会话、槽内残留、非法写者、CLI 5 s 超时「结果未知」不换 id 重发） |
| AC-2 | 满足 | `StaleRejectionTests`（10 项：查询/返回/确认三处共七个出口 + 确认的两条累计门；每例断言观测/云台/机身三个桥文件未被写入且收据为空） |
| AC-3 | 满足（含修订 2） | `GatedSeedingTests` / `PublishGateTests` / `CatchUpTests`；修订 2 的负向义务见 §2.2 |
| AC-4 | 满足（离线半边，含修订 1/2）；**Play 半边待 AC-13** | `StateMirrorTests`；批内逐帧与兜底路径见 §2.2。修订 2 的「兜底若在真实 Play 出现 → `PROTOCOL_ABORT`/会话 FAIL、不改记环境 BLOCKED」随 AC-13 待阶段 B |
| AC-5 | 满足（代码与离线证据，含修订 1）；**「缺预览不得用返回时画面补判」的目检约束随 AC-13 待阶段 B** | `ConfirmationTests`（`unique` 也必须确认、令牌/index 非法只 `REQUEST_INVALID`、`reject` 丢弃候选、**缺预览拒绝确认**、有预览才放行、确认失败沿用原查询身份）；†`PreviewRenderTests`（真实 Pillow 渲染逐像素核对候选框与配对跟踪框） |
| AC-6 | 满足（含修订 1） | `BoundedRetryTests` / `AmbiguousTests` / `StaleRejectionTests`；前置拒绝与三列分列见 §2.2 |
| AC-7 | 满足 | `RespecifyTests`（从 `LOST`/`REINIT_REQUIRED`/`SUSPECTED` 开新段、GAP/`release`/`confirm_lost` 三条路径各 finalize 恰一次、`TRACKING` 下被拒、缺省沿用上次指令、无可沿用 → `REQUEST_INVALID`） |
| AC-8 | 部分满足（协议与异常口径满足；**实机三后端一致性待实测**） | `tests.test_language_selector`（`finish_reason` 经三后端保留、`length` → `TRUNCATED`、失败包可空规则、`SERVER_BUSY`/`timeout` 后 idle 前不重入、断联 → `worker_died`、每次 I/O 截止逐次收缩、观测桥常量与 `confidence_source` 闭集未变）。合同指针另点名 `test_language_loop（Worker：提交回执丢失、轮询断联、超时仍 busy、迟到结果、stuck 后返回、帧环淘汰）`——该侧现由 `WorkerTests` 覆盖：提交回执丢失/轮询断联 → `test_the_session_expires_an_unconfirmed_backend_without_another_ask`；迟到结果 → 两条 stale 升级用例与 `VerifyTests.test_stale_replies_are_dropped_on_each_of_the_three_keys`；stuck 后返回 → `test_a_stuck_worker_never_gets_one_more_designate_query`；帧环淘汰 → `test_an_in_flight_frame_copy_survives_ring_eviction`。「超时仍 busy」原先只有 selector 侧（`test_client_deadline_abandons_without_re_entering`），本次增量补上 loop 侧 `WorkerTests.test_a_timeout_while_the_server_is_busy_never_re_enters_it`（真实 `HttpAdapter` 接进会话：`T_ret` 到期放弃后，两次有界重试都只发 `GET /status`，服务端一共只收到**一次** `POST /query`，三条结果行 `backend_error(timeout)` → `retry_exhausted`，且非 `backend_fatal`）——缺口已闭。修订 2 见 §2.2 |
| AC-9 | 部分满足（回放连接与判定满足；**5060 等价实测待做**） | `ReplayAdapterTests`（两份 sha 核对、重复键取最小 `row_id`、冲突/无匹配、索引带 gold 即拒）；`FrozenReplayAssetTests`（对真实 609 行盲索引与 C2 预测核 sha）；†`ReplayDemoTests`（走查覆盖 designate 四路径与 verify 五 verdict）；`LatencyMeasurementTests.test_merge_equivalence_report` |
| AC-10 | **待实测** | 判定与产出器就绪并有测试（`LatencyMeasurementTests`：3 预热 + 32 计时、p95 取升序第 31 个、单样本失败即 `INVALID`、二轮 `INVALID` → `FAIL`、加载失败 → `FAIL`、决策表与 `HOST_UNDECIDED`）；冻结常数见 `HostDecisionTests`。实机 JSON 未产生，见 §5 |
| AC-11 | 本批已跑（停点须重跑） | `docs/evidence/P1-ENG-LOOP-001-tests.log`，见 §3 |
| AC-12 | 部分满足（互锁与操作单就绪；`pip check` 待实测批） | `tools/requirements-language.txt`；本报告 §6/§7；`DiagnosticSessionTests`（诊断根隔离、阶段 A 段归档只落夹具 runtime、共享 `runtime/` 默认拒绝）；修订 2 见 §2.2 |
| AC-13…15 | **待 Play**（阶段 B 未授权） | — |
| AC-16 | 满足（含修订 1/2/3） | `VerifyTests`（配对帧 = 本段最近已处理帧、同帧不重复、无框跳过、五 verdict、none/drift 交替累计到 2、`ambiguous` 立即疑似、`dismiss` 后旧回包丢弃、核验从不 `initialize`/从不写桥、触发 3 s 限频、`due` 重排）；五条 inconclusive 映射见 §2.2 |
| AC-17 | 满足（含修订 1） | `StateTableTests`（参数化遍历八态×九动作的全部非法格，逐格断言 `REQUEST_INVALID` 且状态/epoch/候选不变；`TERMINAL` 一律 `IGNORED_TERMINAL`；疑似只由人或段终止离开）；`WorkerTests`（pending 至多一条、`SUPERSEDED` 回执、`T_hard` → `worker_stuck` → `REINIT_REQUIRED(backend_fatal)` 且此后只允许 `stop`、join 超时记 `worker_abandoned`） |

### 2.2 2026-09-20 的八行实现期修订（P-A-1…8）

| 修订 | 落实要点 | 具名证据 |
|---|---|---|
| AC-12 修订 2（P-A-1） | 九个操作者子命令与 `run` **共用**同一守卫与开关（写请求同样会在 runtime 建锁与桥文件）；守卫改判「**实际解析到**」：`resolve()` 字符串相等之外再比目录身份（`st_dev`/`st_ino`），覆盖相对路径、`..` 绕路、符号链接与大小写别名；拒绝走在读收据与建任何会话对象之前，**只 stat 不写**；开关只是阶段 B 入口，操作单 A/B 不使用它 | `DiagnosticSessionTests.test_shared_runtime_is_refused_through_every_path_alias`（四/五种写法经 `main()` 断退出码 2）、`..test_the_refusal_creates_no_bridge_lock_or_run_log`（五个常量路径与 `runs/` 条目集合前后不变）、`..test_an_isolated_runtime_is_not_mistaken_for_the_shared_one`、`..test_the_refusal_names_the_guard_and_lets_an_isolated_runtime_through`（断言退出码 2 确实来自守卫文案，且隔离目录不被误拒）、`..test_operator_subcommands_are_guarded_too` |
| AC-3 修订 2（P-A-2） | 收据三值闭集；拒绝与静音都不推进 `last_published_frame_id`、不建立 `accepted_frame_id`；初始化静音记 `MUTED_DROPPED` 而非 `orphan_control`，不终止段 | `PublishGateTests.test_a_rejected_write_neither_advances_nor_associates`（断言落在发布器对象上：段 finalize 后桥镜像必为 null，读桥分不出正确实现与变异实现）、`..test_muted_seeding_never_associates_and_never_reports_orphan_control`、`..test_receipt_outcomes_stay_inside_the_three_value_closed_set` |
| AC-4 修订 1（P-A-3） | 追平一批内出现 `ok=False` 即 `raw_lost`；批末 `raw_ok` 不抹掉逐帧事实、不解除疑似、不改 `suspect_id`；提醒不碰发布门 | `StateMirrorTests.test_raw_lost_inside_a_catch_up_batch_survives_a_raw_ok_tail`（一次桥读数同时断言 `SUSPECTED` + `tracker_raw_state=TRACKING` + `publishing=true`；本批恰一条 `suspect_raised`；本批首条 `WRITTEN` observation 是批末帧，批内 LOST 帧零收据；「恰一条批末发布」另由 `CatchUpTests.test_only_the_batch_tail_is_published` 钉住） |
| AC-6 修订 1（P-A-4） | 前置拒绝也分配唯一 `query_id` 并计一次 `attempt`，四个帧绑定字段为 null 而 `query_unix_s` 非 null；严格帧递增只约束取得帧的尝试；**尝试数 / `query_id` 序号 / 真实模型调用数三列分列**；verify 的三种发起前跳过不冒充调用 | `BoundedRetryTests.test_pre_frame_failures_increment_attempts_without_raising_the_frame_floor`、`..test_retry_exhausted_after_pre_frame_failures_records_the_last_reason`、`WorkerTests.test_model_calls_are_counted_apart_from_attempts`、`VerifyTests.test_tracking_lag_skips_before_any_model_call`、`..test_missing_box_and_same_frame_skips_make_no_model_call`、`ConfirmationTests.test_a_failed_confirmation_keeps_the_original_query_identity`；计数口径见 §11 |
| AC-5 修订 1（P-A-5） | **没有生成预览就不许确认播种**（缺依赖与渲染异常走同一条 `preview_unavailable` 出口，不再有未捕获的渲染异常）：`confirm` 回 `REQUEST_INVALID`，候选/epoch/段不变，不 `initialize`、不写观测或控制；缺依赖仍记 `preview_path=null` 与 `preview_unavailable` 诊断 | `ConfirmationTests.test_confirm_is_refused_when_the_preview_was_not_generated`（用**注入的失败渲染器**驱动，**不挂** `skipUnless(Pillow)`，所以在停点那一跑也真的执行）、`..test_a_generated_preview_lets_the_confirmation_through`、`..test_a_render_failure_is_refused_the_same_way_as_a_missing_dependency`、`..test_the_designate_preview_is_bound_to_the_ring_copy`（预览绑定的是帧环里的加载时副本）、†`PreviewRenderTests` 两条 |
| AC-8 修订 2（P-A-6） | 超硬限之后**不再走普通重试**（原实现会先重试一次，且 `worker.submit` 的异常会逃出 `tick()` 使会话无法 `stop`）；`worker_died` 只限 `predict_one` 执行边界抛出的普通异常（实参在 try 之外求值；服务端 `_record_of` 移出 try）；异常**类型与消息**进会话 JSONL 的 `backend_exception`；已知 `SelectorError` 沿用原具体原因；**断联/无法确认 idle 也有 `T_hard` 总截止** → `backend_fatal` | `WorkerTests.test_a_plain_backend_exception_keeps_its_type_and_message`、`..test_a_known_selector_reason_is_not_rewritten`、`..test_a_stuck_worker_never_gets_one_more_designate_query`、`..test_the_session_records_the_abandoned_query_id_on_stop`（会话 JSONL 的 `worker_abandoned` 带 `query_ids` 与调用计数）、`..test_stop_returns_cleanly_when_the_stranded_thread_finishes_in_time`；`test_language_selector`：`LocalHfAdapterTests` 两条（消息入 detail、无记录用闭集 reason）、`HttpAdapterTests` 四条（服务端异常消息上线路、已知原因保留、无法确认 idle 超 `T_hard` → `worker_stuck` 且此后只能重启、确认 idle 清零计时） |
| AC-16 修订 1（P-A-7） | 核验改走**同一条**返回检查点，`frames_late_exceeded` 与 `negative_frame_delta` 因此可达；`verdict` 字面只有 `inconclusive`，原因另置；五条映射按 `_check_return` 的**返回值**取 | `VerifyTests` 六条 inconclusive 映射（`wall_deadline_exceeded`/`frames_late_exceeded`→`stale`；`negative_frame_delta`/`image_identity_changed`→`frame_identity`；`replay_miss`→`backend_error`；`parse_failed`）、`..test_inconclusive_changes_no_counter_and_writes_nothing`、`..test_stale_replies_are_dropped_on_each_of_the_three_keys`（epoch / segment_index / verify_epoch 三键各一）、`..test_inconclusive_never_clears_an_existing_suspect`、`..test_inconclusive_frame_identity_on_a_missing_or_invalid_bundle`、`WorkerTests.test_a_stuck_worker_on_the_verify_path_also_needs_a_restart` |
| AC-16 修订 2（P-B-1） | 裁定采纳 (a)：`same_frame`/`no_tracker_box`/`tracking_lag` 是**发起前**跳过，**移出结果包闭集**，只在会话 JSONL 记 `verify_skipped`——不产结果、不占 `query_id`、不调模型、不计完成核验、不改连续告警或疑似。`INCONCLUSIVE_REASONS` 收窄为 `{stale, frame_identity, parse_failed, backend_error}` | `VerifyTests.test_the_three_pre_dispatch_skips_leave_no_result_and_no_query_id`（逐个跳过断言五元组「适配器调用数 / `query_id` 序号 / 核验结果行数 / 连续告警 / 真实模型调用数」前后不变）、`..test_the_skip_reasons_are_not_result_packet_reasons`、`..test_an_untrustworthy_pairing_frame_is_not_mislabelled_as_one_of_the_three` |
| AC-16 修订 3（P-B-2） | 裁定采纳 (a)：§3.6 的**第四条**发起前条件（配对帧 P 仍在盘且身份一致）正式取名 `verify_pairing_unavailable`，`reason` 走自己的**五值闭集** `{snapshot_missing, image_identity_changed, bundle_missing, metadata_invalid, latest_unreadable}` 并带已知 `P.frame_id`；只进会话 JSONL，不占 `query_id`、不产结果行、不调模型、不计完成核验、不改连续告警/疑似。闭集现由 `bridge.PAIRING_UNAVAILABLE_REASONS` 机检（此前只是自由字符串），不扩充 `verify_skipped` 三值或结果原因四值闭集 | `VerifyTests.test_every_pairing_unavailable_branch_keeps_its_own_reason`（参数化**遍历闭集本身**的五个成员，逐条断言原因、`frame_id == P.frame_id`、无 `verify_skipped`、17 元组脚印不变；闭集新增成员而无对应分支即失败）、`..test_pairing_unavailable_refuses_a_reason_outside_its_closed_set`（写死期望五值；那三个跳过名与结果包四值逐一 `assertRaises` 且日志零新增）、`..test_the_pairing_diagnostic_leaves_the_two_numbered_paths_alone`（同一个 `bundle_missing`：designate 前置失败仍占号并产结果行、已发起的 verify 返回失败仍 `inconclusive(frame_identity)`、发起前跳过两者皆无）、`test_language_bridge.test_the_pairing_unavailable_reasons_live_in_a_third_closed_set` |
| AC-4 修订 2（P-A-8） | 未映射的终端事件（含 `INVALID_CLOCK`、`REANCHOR_FAIL_CLOSED` 等未启用子系统的事件，**不再被静默吸收成已定义原因**）按 `metadata_invalid` 终止段，原事件逐字进会话 JSONL 并标 **`unexpected_segment_end`**；该标签不是 `tracker_state.reason` 的新增枚举；已定义原因不被兜底覆盖 | `StateMirrorTests.test_an_unexpected_terminal_event_is_labelled_and_ends_the_segment`（含 `publishing=false`、retire 恰一次、收据零新增、标签不在 `STATE_REASONS`）、`..test_a_known_terminal_reason_is_never_replaced_by_the_fallback`、`..test_an_unmapped_invalid_clock_event_also_gets_the_diagnostic` |

## 3. 测试（COORD-009 纪律：开发期 focused，停点全套一次写文件）

**两跑，各有各的用处。**

**(a) 停点全套 —— 系统解释器（Python 3.14.6），与基线可比：**
```
python3 -m unittest discover -s tests > docs/evidence/P1-ENG-LOOP-001-tests.log 2>&1
```

| 轮次 | 结果 |
|---|---|
| 基线（本批开工前，`main`） | `Ran 1247 / FAILED (errors=9, skipped=21)` |
| 本批 | `Ran 1477 / FAILED (errors=9, skipped=24)` |

- **基线已有失败 9 项**，全部是系统解释器缺 `cv2` 的既有导入/跳过失败：
  `test_benchmark_reanchor`、`test_detector_scouting`、`test_rate2_protocol`、
  `test_rate3_difficulty_audit`、`test_rate3_reanchor_clock_mismatch_raises_defensively`、
  `test_rate_study`、`test_scene004_gate0_probe`、`test_scene004_scouting`、
  `test_scene006_probe`。与 `docs/evidence/P1-ENG-SFT-002-tests.log` 记录的基线逐项相同。
- **本批新增失败 0 项**；新增用例 230 项。
- 新增的 3 项 skip 全部是「这台解释器没有 Pillow」：`PreviewRenderTests` 两条与
  `ReplayDemoTests` 一条。**这三条的证据不取自这一跑**——AC-5 修订 1 明写
  「缺依赖的 skip 不是 AC-5 满足」，所以另有 (b)。
  注意：`ConfirmationTests` 里「缺预览拒绝确认」那一条**没有**挂 skip，用注入的
  失败渲染器驱动，在这一跑里真的执行了。

**(b) 有 Pillow 的具名跑 —— `.venv-yoloe`（Python 3.12.13，`pillow==12.3.0`）：**
```
.venv-yoloe/bin/python -m unittest discover -s tests -p 'test_language_*.py'
```
结果 `Ran 230 / OK`，**零 skip**：真实 `render_preview` 与 `replay-demo` 都实跑。
逐条输出与三个具名子集（`PreviewRenderTests` 2 条、`ConfirmationTests` 9 条、
`ReplayDemoTests` 1 条、`VerifyTests` 28 条、`WorkerTests` 18 条）见 `docs/evidence/P1-ENG-LOOP-001-tests-pillow.log`。

为什么用 `.venv-yoloe`：它已经钉着与 `tools/requirements-language.txt` 同版的
`pillow==12.3.0`，跑测试**不改动该环境**，也不动信封（零安装、零下载、零模型运行）。
阶段 A 的 `.venv-language` 那一跑仍在操作单 A 第 5 步，实测批执行后逐字补进本节。

**(c) 本次增量（U-A-1 残留 + P-B-2 同步 + AC-8 loop 侧补证）只跑 focused：**
```
python3 -m unittest tests.test_language_loop tests.test_language_selector tests.test_language_bridge
```
结果 `Ran 237 / OK (skipped=3)`（3 项 skip 仍是这台解释器没有 Pillow 的那三条），
比上一跑多 7 条新增用例。COORD-009 的纪律是**开发期只跑 focused**，所以上面
(a)/(b) 两份日志仍是上一批的产物、未重跑；`K1K3` 停点候选时按 AC-11 各重跑一次
并覆盖这两份日志。本次还对新增的三项代码修正与两项闭集机检各做了一轮定向变异
检查（逐条反改实现，确认对应用例转红）。

## 4. 冻结边界的核对

```
git status --porcelain -- Assets config tools/eng_sft controller/protocol.py controller/tracking_entry.py controller/track_loop.py
```
输出为空（`StateMirrorTests.test_frozen_paths_are_untouched_in_the_working_tree` 每次
跑测试都机检一次）。本批只新增文件，未改这些路径的任何既有字节；`controller/` 下
仅新增 `language_bridge.py` / `gated_publisher.py` / `language_selector.py` /
`language_loop.py` / `language_demo.py`。停点候选交核对轮时另附
`git diff --stat <基线>..HEAD -- Assets/ config/ tools/eng_sft/` 的逐字输出。

## 5. K 收据（此前离线批；当前见实测报告）

AC-10 修订 1 把 K 收据的绑定项定死：宿主 / backend / 模型形态及身份 / `hz` / `R` /
所用测量报告，**变更任一项都不得沿用旧收据**。本批没有实机测量，所以不写收据。
产出方式已就绪：

```
# ① 两台机各测一次（各自在本机跑，产物是 JSON）
python3 tools/language_latency.py measure --host mac   --backend local-hf --model-form c2-merged ... --out docs/evidence/P1-ENG-LOOP-001-latency-mac.json
python3 tools/language_latency.py measure --host 5060  --backend http     --model-form c2-merged ... --out docs/evidence/P1-ENG-LOOP-001-latency-5060.json
# ② 5060 上的合并等价（32 行 smoke、同 greedy）
python3 tools/language_latency.py merge-equivalence --backend local-hf ... --out docs/evidence/P1-ENG-LOOP-001-merge-equivalence.json
# ③ 由两份报告按 §3.3 决策表生成 K 收据；两边都不合格时退出码 6 且写 HOST_UNDECIDED
python3 tools/language_latency.py k-receipt --mac ... --gpu ... --out outputs/eng-loop/P1-ENG-LOOP-001/k-receipt.json
```

会话启动会把收据里的 `hz`/`R` 与**实际生效**的场景配置对照，不一致即
`CONFIG_MISMATCH` 拒绝启动（`HostDecisionTests.test_session_refuses_a_receipt_bound_to_other_hz`）。

## 6. 操作单 A 历史草稿（已由 operations.md 取代，勿直接执行）

信封计数：合并 ≤ 2 次、模型进程启动 ≤ 6 次、查询行 ≤ 70（测量 ≤ 2 轮 × 35）、
base 权重下载 1 次（校验失败可重试 1 次）。**每一步都要把实际计数记进本节的表格**，
成功、失败、重试全计；计数口径（三列分列）见 §11。

**纪律（AC-12 修订 2）**：本操作单**不得**使用 `--allow-shared-runtime`。该开关只是
阶段 B 的操作入口，不是授权凭据；阶段 A 的一切会话与段归档都走隔离目录。诊断
Play 同样属于阶段 B，须另行签发 B 信封。

1. **建环境**（不动既有两个虚拟环境）
   ```bash
   python3 -m venv .venv-language
   .venv-language/bin/python -m pip install --upgrade pip
   .venv-language/bin/python -m pip install -r tools/requirements-language.txt
   .venv-language/bin/python -m pip check
   ```
   `pip check` 的输出逐字贴进报告。若某个钉版在 macOS 上没有轮子，**停下来报偏差**，
   不要自行换版本（合同是「钉 SFT-002 同版」）。
2. **下载 base 权重**（1 次，约 4.26 GB；revision 逐字）
   ```bash
   .venv-language/bin/python -c "from huggingface_hub import snapshot_download; \
     print(snapshot_download('Qwen/Qwen3-VL-2B-Instruct', revision='89644892e4d85e24eaac8bacfd4f463576704203'))"
   ```
3. **合并 C2 adapter**（≤ 2 次尝试，产物不入库）
   ```bash
   .venv-language/bin/python - <<'PY'
   from pathlib import Path
   from tools.eng_sft import train_lora
   loaded = train_lora.load_model(<base 目录>, revision=train_lora.BASE_REVISION,
                                  device="mps", adapter_dir=Path("<C2 adapter 目录>"))
   merged = loaded.model.merge_and_unload()
   merged.save_pretrained("outputs/eng-loop/P1-ENG-LOOP-001/model/c2-merged")
   loaded.processor.save_pretrained("outputs/eng-loop/P1-ENG-LOOP-001/model/c2-merged")
   PY
   ```
4. **时延测量**（3 预热 + 32 计时，顺序固定；一轮 ≤ 35 行，最多 2 轮）
   ```bash
   .venv-language/bin/python tools/language_latency.py measure \
     --host mac --backend local-hf --model-form c2-merged \
     --merged-source outputs/eng-loop/P1-ENG-LOOP-001/model/c2-merged \
     --smoke outputs/eng-sft/P1-ENG-SFT-002/data/smoke.jsonl \
     --package-root outputs/eng-sft/P1-ENG-SFT-002/upload \
     --scratch outputs/eng-loop/P1-ENG-LOOP-001/scratch \
     --device mps --out docs/evidence/P1-ENG-LOOP-001-latency-mac.json
   ```
   退出码 0 = 该轮 `OK`；非 0 表示 `INVALID`/`FAIL`，按合同只许再跑 1 轮。
5. **在 `.venv-language` 跑一次具名预览/确认测试**（AC-5 修订 1 要求的 Pillow 环境证据；
   本步**不起模型、不发查询**，不消耗 §5 的合并/启动/查询行额度）
   ```bash
   .venv-language/bin/python -m unittest discover -s tests -p 'test_language_*.py'
   .venv-language/bin/python -m unittest discover -s tests -p 'test_language_*.py' -k PreviewRenderTests
   .venv-language/bin/python -m unittest discover -s tests -p 'test_language_*.py' -k ConfirmationTests
   ```
   逐字输出补进 §3 (b)。（本机已先用同版 `pillow==12.3.0` 的 `.venv-yoloe` 出了一份
   等效证据，见 §3 (b)；`.venv-language` 那一跑是操作单自己的确认。）
6. **记账**：合并次数 __ / 2，模型进程启动 __ / 6，查询行 __ / 70，下载 __ / 1。

## 7. 操作单 B 历史草稿（已由 operations.md 取代，勿直接执行）

信封计数：合并 ≤ 2 次、模型进程启动 ≤ 6 次、查询行 ≤ 134（等价 2 形态 × 32 = 64，
测量 ≤ 2 轮 × 35 = 70）。adapter 69.8 MB 经局域网/T7 传输，不上公网。

**纪律（AC-12 修订 2）**：同操作单 A——本操作单不使用 `--allow-shared-runtime`。

1. **建环境**：同操作单 A 第 1 步，但 torch 装 CUDA 12.8 轮子：
   ```bash
   python -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 torch==2.11.0+cu128 torchvision==0.26.0+cu128
   python -m pip install -r tools/requirements-language.txt --no-deps  # 其余钉版
   python -m pip check
   ```
2. **合并 C2 adapter**：同操作单 A 第 3 步，`device="cuda"`（≤ 2 次）。
3. **合并等价**（32 行 smoke，同设备、同 greedy）
   ```bash
   python tools/language_latency.py merge-equivalence --backend local-hf \
     --merged-source <合并目录> --model-source <base 目录> --adapter-dir <C2 adapter 目录> \
     --smoke outputs/eng-sft/P1-ENG-SFT-002/data/smoke.jsonl \
     --package-root outputs/eng-sft/P1-ENG-SFT-002/upload --device cuda \
     --out docs/evidence/P1-ENG-LOOP-001-merge-equivalence.json
   ```
   `equivalent=false` 时形态自动回退 `c2-adapter`，并以**该形态**重测时延（合同规定的
   唯一自动回退），回退事实要在报告里披露。
4. **起单工服务**（Mac 当客户端时用）
   ```bash
   python tools/language_serve.py --port 8760 --model-form c2-merged \
     --model-source <合并目录> --scratch <临时目录> --device cuda
   ```
   服务是提交/轮询式：忙时 `SERVER_BUSY` 不排队；`T_hard`（60 s）到期标 `stuck`，
   之后必须重启进程才能接单。
5. **时延测量**：同操作单 A 第 4 步，`--host 5060`（本机 `local-hf`）或从 Mac 用
   `--backend http --server-url http://<5060>:8760`（客户端口径含传输）。
6. **记账**：合并次数 __ / 2，模型进程启动 __ / 6，查询行 __ / 134，传输 __。

> 操作单 C（Play 剧本 P1/P2）属阶段 B，用户另行签发信封后再写，本批不预写。

## 8. 可运行示例（零模型、零 ID）

**需要 Pillow**：AC-5 修订 1 之后没有预览就不能确认播种，走查因此到不了播种。
无 Pillow 的解释器上 `replay-demo` 直接给出提示并返回退出码 8，不会跑出半截结果。

```bash
.venv-yoloe/bin/python -m controller.language_loop replay-demo \
  --session-root <临时目录> \
  --frames outputs/eng-sft/P1-ENG-SFT-002/upload/frames \
  --replay-blind outputs/eng-sft/P1-ENG-SFT-002/data/eval.blind.jsonl \
  --replay-predictions outputs/eng-sft/P1-ENG-SFT-002/returned/<job>/predictions/eval-adapter.jsonl \
  --base-predictions outputs/eng-sft/P1-ENG-SFT-002/returned/<job>/predictions/zero-shot.jsonl
```

本机实跑结果（2026-09-20 用 `.venv-yoloe` 复跑，写临时目录；八行修订落实后再跑一次，数字不变）：15 步走查，designate 覆盖
`unique`/`ambiguous`/`none`/`parse_failed`/`retry_exhausted`，verify 覆盖
`consistent`/`drift`/`none`/`ambiguous`/`inconclusive`，两个段谱系
（`verify_none` 与 `operator_release` 各 finalize 一次），发布收据 60 `WRITTEN` /
4 `MUTED_DROPPED` / 0 拒绝，预览 7 张（真实 Pillow 渲染，每张绑定 `<frame_id>-<query_id>`）。**演示口径**（写进 `demo-report.json` 的 `caveats`）：
虚拟时钟、`T_v` 取命令行值（缺省 1.0 s）而非冻结的 10 s、演示索引是冻结资产的派生
子集（每行记来源文件与原 `row_id`）、不产生任何 AC-13…15 的 Play 证据。

## 9. 实现期发现的合同问题（**已于 2026-09-20 全部裁定**）

实现角色对 `docs/proposals/` 只读，无法自行写入该节，故当时列在这里。接受角色已在
提案 `## Pending rulings` 把八条逐字转录为 P-A-1…8 并答复，追加**八行同编号 AC 修订**
（新 AC = 0）。下面保留原问题文本不改字，只在每条后标注裁定落点；落实情况见 §2.2。

**裁定索引**：P-A-1 → AC-12 修订 2（保留开关，但判据改为「实际解析到」且拒绝前零写入）；
P-A-2 → AC-3 修订 2（保留三值闭集，补两条负向义务）；P-A-3 → AC-4 修订 1（确认）；
P-A-4 → AC-6 修订 1（确认，并要求三列分列）；**P-A-5 → AC-5 修订 1（驳回原退化做法：
缺预览必须拒绝确认）**；P-A-6 → AC-8 修订 2（有限确认，边界收窄 + 断联总截止）；
P-A-7 → AC-16 修订 1（确认分层，并给定五条映射）；P-A-8 → AC-4 修订 2（有条件保留，
必须标 `unexpected_segment_end`）。

1. **AC-12 / 安全互锁**：新增 CLI 开关 `--allow-shared-runtime`。不带它时，
   `--runtime` 指向仓库真实 `runtime/` 一律拒绝启动（退出码 2），以机械保证阶段 A
   「不写 `runtime/runs/`、不占共享槽」。合同没写这个开关，请裁定保留还是删除。
2. **AC-3 / 收据第三类**：收据文件除 `WRITTEN`、`PUBLISH_REJECTED` 外，播种瞬态被
   静音丢弃的尝试记第三类 `MUTED_DROPPED`，并把「发布证据」定义为**只数 `WRITTEN`**。
   这样「`initialize` 即时发布被丢弃」才可机检。请裁定。
3. **AC-4 / `raw_lost` 的判据**：追平一批内若中间帧报丢、批末帧又 ok，按
   「批内任一帧 `ok=False` 即 `raw_lost`」触发 `SUSPECTED(tracker_failure)`
   （与「段内自恢复不算恢复」一致）。请确认这是预期口径。
4. **AC-6 / 未取得帧的尝试也占 `query_id`**：查询检查点在取帧前就失败
   （`bundle_missing`/`metadata_invalid`）时没有查询 job，实现仍分配一个 `query_id`
   并计一次 `attempt`（§3.2(b)「`seq` 对每次 designate/verify **尝试**严格递增」）。请确认。
5. **AC-5 / 预览的退化路径**：预览用 Pillow 渲染；解释器没有 Pillow 时
   `preview_path` 记 `null`，并在会话 JSONL 记 `preview_unavailable`。合同没写这条
   退化路径（阶段 B 的 `.venv-language` 必装 Pillow）。请确认。
6. **AC-8 / 后端异常的闭集归类**：`reject_reason` 闭集里没有「通用后端异常」一项，
   实现把后端抛出的非 `SelectorError` 异常统一记 `worker_died`，`status=backend_error`。请确认。
7. **AC-16 / 核验的 `inconclusive` 如何落进结果包**：后端失败时结果为
   `status=backend_error` + `reject_reason=<闭集>` + `verify.verdict=inconclusive(backend_error)`；
   超时与身份失败为 `status=stale_rejected` + `reject_reason=wall_deadline_exceeded`/
   `<身份失败原因>` + `inconclusive(stale|frame_identity)`。请确认这一映射。
8. **AC-4 / 不可达终端事件的兜底**：本项的段从不装 rate/qualification/re-anchor/
   body planner，所以 `TrackLoop` 的 `REANCHOR_FAIL_CLOSED` 等终端事件结构上不可达；
   万一出现，实现把原事件逐字记进会话 JSONL 并按 `metadata_invalid` 终止段。请确认兜底选择。

## 9.1 P-B-1（**已于 2026-09-20 裁定：采纳 (a)**，见提案 AC-16 修订 2）

原问题逐字保留如下；裁定结论与落实见 §2.2 的 `AC-16 修订 2（P-B-1）` 一行。
实现已按 (a) 把三个成员移出 `INCONCLUSIVE_REASONS`（现为
`{stale, frame_identity, parse_failed, backend_error}`），并新增 `VERIFY_SKIP_REASONS`
承载三种发起前跳过的日志原因。


**P-B-1 / AC-16**：`INCONCLUSIVE_REASONS` 闭集里的 `same_frame`、`no_tracker_box`、
`tracking_lag` 三个成员**当前不可达**。§3.6 的措辞是「同帧不重复核验，跳过记
`inconclusive(same_frame)`」，读起来像要产出一条结果包；而 AC-6 修订 1 要求这三种
**发起前**跳过「不冒充已调用模型」。实现取了后者：三者只写会话 JSONL 的
`verify_skipped`，不产结果行、不占 `query_id`、不调模型（`VerifyTests` 三条用例钉住）。
两种读法都自洽，但闭集里留着三个永不出现的值会让下游消费者误以为能收到它们。

请裁定二选一：**(a)** 明确这三种跳过只入会话 JSONL、不产生结果包，并相应从
`INCONCLUSIVE_REASONS` 移除这三个成员；或 **(b)** 让它们各发一条不带 `model` 块、
不占 `query_id` 的 `inconclusive` 结果行。在答复前实现保持现状 (a) 的行为、闭集不动。

## 9.2 落实 U-A-1…3 与 P-B-1 时新发现的一条合同问题（**已于 2026-09-20 裁定：采纳 (a)**，见提案 AC-16 修订 3）

**P-B-2 / AC-16 修订 2**：AC-16 修订 2 把 `verify_skipped` 的原因闭集定死为
`{same_frame, no_tracker_box, tracking_lag}` 三个成员。但 §3.6 的发起前条件其实有
**四条**——第一条是「P 仍在盘且身份一致」，它在合同里从没被取名。实现里它对应三种
情形：帧环里没有该帧的快照、盘上字节/元数据与快照不符、`latest.json` 读不出来。

把它们硬塞进那三个名字会**错标**（我一度误改成 `no_tracker_box`，已回退）；留在
`verify_skipped` 里又会突破刚被定死的闭集。当前实现取第三条路：另记一种诊断
`verify_pairing_unavailable`（`reason` 取 `snapshot_missing` / `image_identity_changed` /
`bundle_missing` / `metadata_invalid` / `latest_unreadable`），语义与三种跳过一致——
只进会话 JSONL、不产结果、不占 `query_id`、不调模型、不改计数。

还有**同一问的另一半**（复核指出，一并提请）：designate 的查询检查点遇到
`bundle_missing`/`metadata_invalid` 时，按 AC-6 修订 1 要**分配唯一 `query_id` 并落一条
结果行**；而核验这条同名失败当前既不占号也不产结果行，两边不对称。

请裁定：**(a)** 认可这条独立诊断（并给它一个合同名），且确认核验侧**不**占号、
**不**产结果行；或 **(b)** 把它并入 `verify_skipped` 并扩充那三成员的闭集；或
**(c)** 按 designate 的查询检查点**对称处理**（走结果行：`status=stale_rejected`、
`reject_reason` 取原闭集值、`verify.inconclusive_reason=frame_identity`、四个帧绑定
字段可空）。答复前实现保持现状 (a)。

**裁定与落实。** 接受侧采纳 **(a)** 并追加 **AC-16 修订 3**：这条诊断的合同名就是
`verify_pairing_unavailable`，`reason` 是上面那五个值的闭集，须带已知 `P.frame_id`；
核验侧**不**占号、**不**产结果行；`designate` 的 AC-6 前置失败与**已发起**的 verify
返回身份失败两条路径一字不改。本批按此同步：

1. 五值闭集从「实现自取的自由字符串」升格为机检常量
   `controller/language_bridge.py: PAIRING_UNAVAILABLE_REASONS`，
   `_record_pairing_unavailable` 经 `bridge._require_member` 校验，越界即
   `LanguageBridgeError`（闭集外的名字再也写不进会话 JSONL）。
2. 代码注释里「P-B-2 待裁定」的措辞改为引 AC-16 修订 3。
3. 具名证据见 §2.2 的 AC-16 修订 3 行：五个成员逐条参数化（此前只覆盖三条）、
   `frame_id` 断言、闭集拒收断言，以及 designate/verify 两条编号路径的对照用例。

## 9.3 U-A-1…3（用户指定增量查看，2026-09-20）的处置

| 编号 | 接受侧指出的问题 | 落实 | 具名证据 |
|---|---|---|---|
| U-A-1 | `_mark_unconfirmed` 只记时不置 `awaiting_idle`，下一次 `predict_one` 可直接 POST；断联截止只在再次 `predict_one` 时检查，不再 `ask` 就不会到期；计时起点是断联/`T_ret` 返回时而非原提交时 | ① `_mark_unconfirmed` 同时置 `awaiting_idle`，响应丢失后的下一次请求**必须**先 `GET /status`；② 新增 `health_check()`，会话每 `tick` 调一次，于是「不再 ask」也有界落到 `backend_fatal`；③ 计时起点改为**本次在途任务的原提交时刻** `_in_flight_since`，不被软超时/重试推后 | `HttpAdapterTests.test_a_lost_response_forces_a_status_check_before_the_next_submit`（断言下一次调用是 `GET /status` 且 POST 计数不增）、`..test_the_total_deadline_is_anchored_at_the_original_submission`（断联后 3 s、离原提交 6 s > `T_hard` 即到期——**锚在断联时刻的旧实现在此必红**，所以这条用例能区分新旧）、`..test_health_check_expires_without_another_query`（不打服务端也到期）、`..test_a_confirmed_idle_after_a_disconnection_restores_service` |
| U-A-2 | 旧世代回包在 `_handle_designate_outcome` / `_handle_verify_outcome` 里先 `return`，吞掉 `worker_stuck` 的全局终止；适配器直报 `worker_stuck` 时 `poll` 的 pending 派发先于会话处理该错误 | ① `_poll_worker` 在分派之后补一道：回包带 `worker_stuck`、会话不在 `TERMINAL`、且尚未进 `backend_fatal` 时升级（结果照常按旧世代丢弃；`stop` 之后不再改状态）；② `LanguageWorker.poll` 遇到带 `worker_stuck` 的回包立刻置 `stuck` 并清 pending，不再多派发一次 | `WorkerTests.test_a_stale_designate_reply_still_escalates_worker_stuck`、`..test_a_stale_verify_reply_still_escalates_worker_stuck`、`..test_an_adapter_reported_stuck_does_not_dispatch_the_pending_query`（合成回包用**在途任务的真 `query_id`**，槽位真的被腾空，派发分支才可达；并断言被丢的 pending 已解钉帧环） |
| U-A-3 | 硬超时后 `poll` 清掉 `_in_flight` 与 `_handle`，随后 `stop` 因 `handle=None` 直接返回，既不 join 也不记 `worker_abandoned`/`query_id` | 硬超时时把「线程句柄 + `query_id`」留进 `_stranded`；`stop()` 对它们同样 join 并记名，已等过一轮就不再为后续线程重复等满（`stop` 仍有界） | `WorkerTests.test_stop_joins_and_names_a_thread_stranded_by_the_hard_limit`（真实线程 + 假时钟，断言 `stop` 返回 `worker_abandoned` 且 `abandoned == ["s1-qBlocked"]`） |

**接受侧对本节的复查结论（2026-09-20 非 C 轮）：** U-A-2 / U-A-3 已见对应修复；
U-A-1 的三处主要路径也已补，但**总截止仍有一处残留**，修正见 §9.5。

## 9.4 对 §9.3 的一轮对抗复核及其修补（2026-09-20）

落实 P-B-1 与 U-A-1…3 之后又做了一轮只读对抗复核（四项各一个复核者 + 一轮弱测试
变异检查），确认**义务本身基本成立**（P-B-1 14/16、U-A-1 4/4、U-A-2 4/4、U-A-3 5/6），
但挖出 4 处真实代码缺陷与 7 条「测试挡不住回退」，已同批修完：

| 类别 | 发现 | 修补 |
|---|---|---|
| 代码 | `/result` 与 `/status` 返回**无法解释的 state** 时不置 `awaiting_idle`、不武装 `T_hard` 锚点，下一次 `predict_one` 会直接 POST 重入可能仍在跑的服务端 | 两处抛出前补 `_mark_unconfirmed()`；新增 `HttpAdapterTests.test_an_unexplainable_result_state_also_blocks_re_entry` |
| 代码 | `_call` 的「预算耗尽」出口抛 `worker_stuck` 却不置 `fatal`/`awaiting_idle`——这是唯一一条 stuck 之后适配器仍可被再次提交的路径 | 与其它 `worker_stuck` 出口对齐（置 `fatal` + `_mark_unconfirmed`） |
| 代码 | 为 U-A-2 新增的「清 pending」不解钉帧环副本，被丢弃查询的帧会永久钉住、淘汰不掉 | `LanguageWorker` 把被丢的 job 交回 `dropped_jobs`，`_poll_worker` 逐个 `ring.unpin` 并记 `pending_dropped`（与 `SUPERSEDED` 分支对齐） |
| 代码 | `stop()` 的 join 预算只在「发现线程存活」时才归零，`≤5 s` 依赖「`stuck` 永不复位」这一未声明的不变量而非循环本身 | 改成总截止 `deadline = now + join_s`，每次 join 取剩余；`join_s` 默认值改为调用时取模块常量（便于测试收紧等待，行为不变） |
| 测试 | 会话侧 `_check_adapter_health`（U-A-1 的「不再 ask 也有界退出」落点）**整条零覆盖**——夹具适配器都没有 `health_check` 属性 | `WorkerTests.test_the_session_expires_an_unconfirmed_backend_without_another_ask`（桩适配器第三次到期，全程不发任何请求，断言 `REINIT_REQUIRED`/`backend_fatal`/`worker.stuck`/`purpose="health_check"` 的诊断/此后只许 stop）+ `..test_an_adapter_without_a_health_check_is_left_alone` |
| 测试 | 「不多派发一次模型调用」的用例用了不匹配的 `query_id`，派发分支根本不可达，断言空转 | 见上表 U-A-2 行的加固 |
| 测试 | 两条旧世代用例在旧实现下同样绿（inline 完成 / 无交叉世代） | 改成真实交叉：非完成 spawn + A 在途 → ask B 换代 → 注入 A 世代的 stuck 回包；verify 侧补 `IGNORED_STALE_EPOCH`、核验行数、计数三项未被改写的断言 |
| 测试 | `stop` 的 join 只覆盖「线程一直活着」分支；会话层 `worker_abandoned` 记账行零断言 | `..test_stop_returns_cleanly_when_the_stranded_thread_finishes_in_time`（正向分支）+ `..test_the_session_records_the_abandoned_query_id_on_stop`（真实线程端到端，断言 `query_ids` 与 `model_calls_started`） |
| 测试 | 三种跳过的「脚印」只看五个计数，把跳过当成已完成核验或顺手提醒都不会红 | `_skip_footprint` 扩成 17 元组（含 `last_verified_frame_id`/`state`/`reason`/`suspect_*`/`verify_epoch`/`next_due`/结果桥字节），并改为直接调 `_request_verification` 以隔离无关状态变化 |
| 测试 | 闭集证据是自指循环：三个成员加回去也不会红 | `test_language_bridge` 改成对**写死期望集合**断言，并对三个被移出的名字在写/读两侧各加 `assertRaises`；另加 `VerifyTests.test_record_skip_refuses_a_reason_outside_the_skip_closed_set` |
| 测试 | `verify_pairing_unavailable` 只覆盖了三条分支中的一条 | `..test_every_pairing_unavailable_branch_keeps_its_own_reason` 参数化三条（快照缺失 / 字节改写 / `latest.json` 读不出） |
| 测试 | AC-8 修订 1 点名的「帧环淘汰」无覆盖 | `..test_an_in_flight_frame_copy_survives_ring_eviction`（钉住的副本越过容量不被淘汰，解钉后再加载一帧才淘汰） |
| 测试 | 每次 I/O 的 `min(5 s, 剩余)` 截止无断言 | `..test_each_http_exchange_carries_a_shrinking_deadline`（假传输记录 timeout，断言逐次收缩且 < 5 s） |

**报告自身的三处纠正**（复核指出）：① §9.3 U-A-1 的括注原写「旧实现在此必绿」，
**方向写反了**，应是「必红」——已改；② §9.3 U-A-2 原把第三条测试当作「不再多派发」
的证据，属夸大（当时那条用例走不到派发分支）——已连同测试一并修好后改述；
③ §9.3 U-A-2 原写「一律升级」，实际守卫还带 `state != "TERMINAL"` 条件——已补。

## 9.5 U-A-1 残留（接受侧 2026-09-20 非 C 轮记录）的修正

接受侧在用户指定增量查看里判定 U-A-1「原三处主要路径已补，但总截止仍有一处残留；
未闭」，并给了可复现的反例：`T_hard=60`、原任务 t=0、t=59 重试，`GET /status` 在
t=62 才回 idle，旧路径**能清零并继续提交**。本批按 AC-8 修订 1/2 与 AC-17 修订 1
逐条修正 `controller/language_selector.py` 的恢复路径：

| 残留 | 旧行为 | 修正 | 具名证据（定向变异：反改任一条，对应用例转红） |
|---|---|---|---|
| 恢复确认不收缩截止 | `predict_one` 的 `awaiting_idle` 分支调 `self.status()`，用缺省 5 s | 新增 `_unconfirmed_remaining()`（`T_hard −`（now − 原提交时刻）），恢复确认按 `min(5 s, 本次剩余等待)` 收缩，剩余 ≤ 0 走既有「预算耗尽」出口（置 `fatal` + `_mark_unconfirmed`） | `HttpAdapterTests.test_the_recovery_status_check_shrinks_to_the_remaining_budget`（断言这次 `/status` 的 timeout 恰为 `min(5, 5−3)=2`，缺省 5 s 即红） |
| 迟到的 idle 能清零锚点 | `status()` 一见 idle 就清 `awaiting_idle`/`_in_flight_since`/`_unconfirmed_since` | idle 分支**先** `_check_unconfirmed_deadline()` 再清零：确认跨过原总截止即 `backend_fatal`（`fatal=True`、`awaiting_idle=True`、锚点保留），不再变成一次合法提交 | `..test_a_late_idle_past_the_total_deadline_is_still_fatal`（确认请求本身把时钟推到 t=7 > `T_hard`=5；断言 `worker_stuck`、`fatal`、锚点未清、POST 计数不变） |
| 提交前不再看 `fatal` | 确认 idle 之后直接建新起点并 POST | 确认 idle 之后、建起点之前再检查一次 `self.fatal`：会话线程的 `health_check()` 在这次 I/O 期间判死时，恢复线程不得把已判死的后端重新叫起来 | `..test_a_fatal_raised_during_the_status_check_blocks_the_submit`（时钟不动，只并发置 `fatal`，把这条检查与总截止分开验；断言 `worker_stuck` 且 POST 计数不变） |

接受侧同时指出「现有 `test_each_http_exchange_carries_a_shrinking_deadline` 只检查
`/result`，恢复 idle 测试未让 `/status` 跨原截止」——上表第一、二行的两条新用例正是
补这两处，原用例保留不动。

## 10. 已知限制（随实现披露，不影响本批结论）

1. 本批**没有**在真实模型上跑过任何一次推理；`local-hf` 与 `http` 两个后端的实机
   行为（含 `finish_reason` 的一致性、峰值内存、时延）全部待实测批验证。
2. 冻结的 NanoTrack-v2 核心无分数阈值，`confidence_source` 恒为 `placeholder`，
   所以 §3.6 的「分数骤降」触发在真实段里基本不会触发；贴边触发与 `due` 周期是
   实际起作用的两条。已在 `runtime/README.md` 对外声明该值未校准、不得当阈值用。
3. `replay-demo` 用虚拟时钟与缩短的 `T_v`，只证明协议路径可达，不构成任何时延、
   跟踪性能或模型能力主张。
4. 本报告的 §6/§7 操作单尚未被真实执行过；命令是按合同与本机代码写的，实测批
   若发现偏差（例如某个钉版在 macOS 无轮子）应如实记录并退回接受角色。
5. AC-5 修订 1 的 Pillow 环境证据取自 `.venv-yoloe`（同版 `pillow==12.3.0`），**不是**
   合同点名的 `.venv-language`——后者要等实测批建起来。两者的 Pillow 版本相同，
   但解释器与其余依赖不同；`.venv-language` 那一跑仍是操作单 A 第 5 步的义务。
6. AC-4 修订 2 的兜底路径在本项结构上不可达（段从不装 rate/qualification/
   re-anchor/body planner）。测试经生产路径的 `RecordingRunLogger.append` 直接驱动
   `TrackLoop` 终止时会走的同一个出口，**不是**真实触发过该子系统；裁定明许
   「无需启用……来演练此路径」。
7. §11 的计数是本批的**代码内计数口径**，不是实测消耗——本批模型调用为 0。
8. AC-5 修订 1 的连带后果：`replay-demo` 现在**必须在有 Pillow 的环境跑**——没有生成
   预览就不能确认播种，走查到不了播种。无 Pillow 时它给出提示并返回退出码 8，
   不跑出半截结果。系统解释器上 `ReplayDemoTests` 因此跳过，证据取 §3 (b) 那一跑。
9. `verify_pairing_unavailable` 现在是**合同取名**的诊断 kind（AC-16 修订 3，P-B-2 裁定
   采纳 (a)），`reason` 走机检的五值闭集；会话 JSONL 的 `kind` 字段本身仍没有闭集校验，
   这条诊断也不进任何桥文件的闭集。
10. 共享 `runtime/` 的互锁现在同时装在 `run` 与九个操作者子命令上；但它只认 runtime
   **根**，`--runtime runtime/frames` 之类的子目录仍会穿过（那样既不写 `runtime/runs/`
   也不占共享槽，锁文件落在子目录）。如接受侧认为「路径」应泛指子目录，请另行裁定。

## 11. 预算计数口径（AC-6 修订 1 要求的三列分列）

同一条链路上有三个不同的数，合同要求它们**不得互相冒充**：

| 列 | 含义 | 落点 |
|---|---|---|
| **尝试数** `attempt` | designate 的第几次尝试（含取帧前就失败的那些），上限 `attempt_limit=3` | `language_result.json` 与 `results.jsonl` 的 `attempt` |
| **`query_id` 序号** | 每次 designate/verify **尝试**各占一个 `<session>-q<n>`；取帧前失败也占号（否则结果行无从引用） | 结果行的 `query_id`；预览文件名 `<frame_id>-<query_id>.png` |
| **模型调用数** | **派发给推理 worker** 的次数（`_start` 里计，早于线程体真正进入 `predict_one`）——口径**偏保守、只会多计不会少计**，信封的「本地模型查询行」按它算 | `LanguageWorker.calls_started`；每次进入写一条会话 JSONL `query_started`；`stop` 时的 `worker_abandoned` 带 `query_ids` 与该计数（由 `WorkerTests.test_the_session_records_the_abandoned_query_id_on_stop` 端到端钉住） |

不冒充调用的三类：① 查询检查点在取帧前失败（`bundle_missing`/`metadata_invalid`）；
② `no_new_frame` 的等待尝试；③ 核验的三种发起前跳过（`same_frame`/`no_tracker_box`/
`tracking_lag`，按 AC-16 修订 2 只写 `verify_skipped` 日志，不产结果行、不占 `query_id`；
它们已不在结果包的 `inconclusive_reason` 闭集里）；④ 配对帧本身不可信任时的跳过
（记 `verify_pairing_unavailable`，五值闭集与「不占号、不产结果行」由 AC-16 修订 3
裁定并机检，见 §9.2）。
被 `stop` 放弃的在途查询**已经真的跑过**，按裁定仍计信封，日志里带 `query_id` 可对账。

**本批实际消耗：三列分别为「若干尝试 / 若干 `query_id` / 真实模型调用 0」**——全部测试
与走查都用回放桩或脚本替身，零模型进程、零下载、零合并。
