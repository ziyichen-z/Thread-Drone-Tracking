# P1-ENG-LOOP-002 — OpsK1K2K3K4 停点交接（Implementation，MacBook Air；**现行返工候选 `5218cc2`（轮次 `OPSR1返工`），直接交 `R2@OpsK1K2K3K4`**；以下 `d3c3ff0`/`C7` 为前版）

- **现行（登记轮次 `签发全套执行`；Dispatch-Id `P1-ENG-LOOP-002-签发全套执行-20261008T185356Z-0b91`）**：已签 `P1-ENG-LOOP-002:42979c14:SUB:1` 对合批候选（代码 `0112b4a`）执行停点全套 1 次：2474 例、16 项历史失败逐名照现、新增失败 0；四条件自证与完整候选 diff 见第 15 节，交接受 `C8@OpsScoreDiagK1K4`。
- **前版进度（登记轮次 `评分诊断合批修复`；Dispatch-Id `P1-ENG-LOOP-002-评分诊断合批修复-20261008T172306Z-224f`）**：DIAG-CONTROL-1 与 AC-10 修订 7/8 已在 `OpsScoreDiagK1K4` 闭集内窄修，focused/红绿/本机 AF_UNIX 已过；engineering §6 替代不成立、未跑全套，**非稳定候选、不交 C8**，额外全套申请 `P1-ENG-LOOP-002:42979c14:SUB:1` 待用户首签，见第 14 节。
- **前版（登记轮次 `OPSR1返工`；Dispatch-Id `P1-ENG-LOOP-002-OPSR1返工-20261008T055822Z-5084`；派发 base_head `2fdf2ec`；依据 `docs/reviews/P1-ENG-LOOP-002.md` R1@OpsK1K2K3K4 §3–5）**：R1-1…4 修于返工候选 `5218cc2`，SUB:1 第 3 个（末个）候选全套 1 次、新增失败 0；落点/红绿/全套/待裁定见第 12 节。复核返工直接回 `R2@OpsK1K2K3K4`，不经核对轮；R1-4 语义争议与 R1-5 SCOPE_GAP 交接受裁定。未经复核只记 `IMPLEMENTED`。
- 前版登记轮次（历史）：`OPS裁定落实与停点验证`；Dispatch-Id `P1-ENG-LOOP-002-OPS裁定落实与停点验证-20261008T015311Z-836a`；派发 base_head `b309b36`。
- 合同：同名提案「OPS验证额度落实与IR裁定（2026-10-08，Acceptance）」§1–5（IR-OPS-1…6、AC-10 修订 4 / AC-14 修订 2 / AC-16 修订 3、§4 诊断模式合同、§5 执行顺序 1–2）与「OPS九题答复落实」§1–5；签发来源 `docs/authorizations.md`「用户按申请签发 OPS 验证额度 SUB:1/SUB:2/SUB:3…」条（f4d1c90 代录）。
- 前版候选代码提交（历史；现行候选见下）：`d0bba83`（代码/测试/三份操作页/runtime README 定稿）；停点全套 `SUB:1` 针对该提交执行一次。
- 前版结论（`OPS裁定落实与停点验证`，历史）：IR-OPS-1…6 与 §4 诊断模式合同已落实（`d0bba83`），`SUB:1` 见第 4 节；当时 `SUB:2` NOT_RUN、12 项新基线待裁定，故未交 C6。
- **现行（登记轮次 `OPSC6返工`；Dispatch-Id `P1-ENG-LOOP-002-OPSC6返工-20261008T041335Z-1edf`；派发 base_head `7c341ba`；依据 `docs/evidence/P1-ENG-LOOP-002-C6-OpsK1K2K3K4.md` §2–5）**：C6-1/2/3 修复于候选 `b6bd195`，SUB:1 第 2 个候选全套 1 次暴露 1 项新增失败（本轮新测试揭示的真实竞态），竞态窄修于**现行候选 `d3c3ff0`**（未再跑全套，engineering §6 替代）；落点/红绿/全套见第 11 节，四条件现行自证见第 7.0 节，**交 `C7@OpsK1K2K3K4`**（C 已退回 1/1，C7 只核对不退回、照交新鲜 `R1@OpsK1K2K3K4`）。SUB:2 对本候选的对应关系待接受判读（第 11.4 节）。未经复核只记 `IMPLEMENTED`。
- **前版（登记轮次 `OPS稳定候选`；Dispatch-Id `P1-ENG-LOOP-002-OPS稳定候选-20261008T034709Z-e13b`；派发 base_head `c747e88`；合同 = 同名提案「OPS基线与IR78裁定（2026-10-08，Acceptance）」§1–5）**：接受已把 12 项接受为本停点环境基线、条件②满足（该节 §1）；用户本人 `SUB:2` 两张一致（第 5.1 节）；IR-OPS-7/8 已裁并落实于**候选提交 `49e83f5`**（第 10 节），窄修按 engineering §6 以已有停点全套 + 零模型 focused + 修前红/修后绿替代、**补丁未跑全套**。四条件逐条自证见第 7 节，**交 `C6@OpsK1K2K3K4`**。未经复核，新 Ops 范围只记 `IMPLEMENTED`，不记 DONE。

## 1. IR-OPS-1…6 与三条追加修订的逐项落点

| 裁定 | 落点（文件/函数） | 证据（具名测试） |
|---|---|---|
| IR-OPS-1 G4 机读行（采纳） | `play_ops.require_g4`：从发布引用的同名提案取 `g4_release: <prep.stdout sha256>`；提案读不出、缺行或不匹配 → `S-PRECHECK`；格式说明同步正式单第 0A 节 | `ReleaseGateTests.test_registration_and_g4_machine_lines_fail_closed`；`EndToEndTests.test_receipt_requires_g4_then_runs_unit_2` |
| IR-OPS-2 Unity 日志登记行（采纳） | `play_ops.require_gate(need_registration=True)`：发布引用 `docs/unity-test-log.md` 含 `release_raw_sha256=<登记文件 sha256>` 且 1.1–1.4 逐行相同；诊断不写/不核该行 | 同上；`DiagTests.*`（诊断不调用 `need_registration`） |
| IR-OPS-3 `S-REBUILD`（保持 fail-closed） | `play_ops.classify_terminal`：`rebuild_limit` 一律 `S-REBUILD`/UNKNOWN 停全部；正式单第 13 节 OPS 段改写为已裁定 | `ArchiveAndStopTests.test_terminal_reasons_map_to_original_stops` |
| IR-OPS-4 无环境性重试（确认） | `stage_play`/`run_attempt` 无重试路径；Unity 未进 Play 停依赖交回（文案改为 IR-OPS-4）；正式单第 10 节 OPS 段改写；诊断 Play ≤ 1、故障重启 0 | `EndToEndTests.*`；`DiagAccountTests.test_limits_wall_and_disk` |
| IR-OPS-5 诊断模式（采纳；见第 2 节） | `play_ops.DiagnosticRun`/`stage_diag`/`DiagAccount`/`DiagConnection`/`DiagServe`；`main` 按模式独立路由 | `DiagTests.*`、`DiagAccountTests.*`、`ArchiveAndStopTests.test_modes_route_independently` |
| IR-OPS-6 原流锚点（采纳） | `PlanScheduler._anchor`（只取该 request_id 的会话 receipt `at_unix_s`，5 s 内不可绑定 → UNKNOWN 停依赖；**删去旧 `cli_return_no_journal` 补值**）、`_bind_tracking`（只认选择后同纪元 TRACKING 状态事件；状态槽已 TRACKING 而原流无事件 5 s → UNKNOWN；**删去旧 `poll` 补值**）、`_seeded_selection`（拒绝与带拒收细节的 confirm 不建立跟随）；`operator_web.Monitor` 回执记录增绑纪元；NO_CANDIDATE/NO_DECISION/SKIPPED 不开观察窗 | `ObservationAnchorTests.*`（6 例）；`SchedulerTests.test_send_present_confirm_observe_then_next_step`、`test_follow_window_anchors_at_tracking_entry`、`test_release_only_when_tracking_with_same_track_and_stop_once`（夹具改为写同纪元原流事件） |
| AC-10 修订 4 | 上述各项 + 两操作页与 mini 来源块引用同步（第 3 节） | 同上 |
| AC-14 修订 2 | 正式无重试动作；诊断只此一次（同 request_id 已消耗即拒）、本人操作、粗账只在诊断根 | `DiagTests.test_service_refusal_counts_the_single_start_and_never_plays`（含二次启动拒绝）、`DiagTests.test_end_to_end_single_play_web_closeout_and_summary` |
| AC-16 修订 3 | 诊断资产期望只按诊断页附录 1 从 precheck R02 原流解析、`gen` 生成诊断输入、附录 5 判据核 `/status`（无 `http_budget`），全部只写诊断根；不写正式 assets/收据/`ops-ledger.json` | `DiagTests.test_status_with_formal_budget_is_fault_and_no_receipt`、`test_end_to_end_…`（断言不存在正式 `ops-ledger.json`） |

## 2. 诊断模式合同 §4.1–4.8 逐条落点

| §4 | 实现 | 测试 |
|---|---|---|
| 1 显式模式与根 | `--mode diagnostic diag --request-id <SUB:3>`，request_id 逐字比对；账本两项命中（签发条目片段 + 完整 request_id，经 `release_gate(ledger_hits=…)`）；横幅「诊断；不进证据链；不作任何门判定」（终端、网页页首、粗账、NOTES）；Air 根 `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/<UTC>/` 与板根 `/home/jetson/eng-loop2-diag/<同一 UTC>/` 均必须新建；会话 `run --diagnostic`、`diag-loop2-<HHMMSS>`、`--session-root`/`--diagnostics-root` 均在诊断根；runtime 残留只移入 `hold/held/`、收尾归位 | `test_modes_route_independently`、`test_refused_when_ledger_entry_missing`、`test_end_to_end_…` |
| 2 现场核与源码同步 | 放行核对（干净树/_Recovery/通过候选/PLAY_GOVERNING/blocks/文档检出自检）、Air 工具/环境/det-assoc 资产/烟测；附录 1 `resolve`、附录 2 板上只读核、附录 1 `gen`；16 路径 tar 同步 + 逐文件 sha 核；部署摘要 Air 重算；附录 3/4 + `serve-diag.env` + `expect-assets.json` 放入 `run/` | `test_existing_board_root_is_fault_before_code_sync`、`test_end_to_end_…` |
| 3 启动块唯一来源 | 按标题前缀原样提取附录 3/4/5/7；可见前台 `ssh -tt` 交互 bash 中运行 `serve-diag.sh 1`（附录 3 已同步为只许编号 1）；只认 `DIAG language-serve listening on http://<BOARD_TS>:18082` 行；`/status` 恰一次 + 附录 5；Ctrl-C → `serve_diag_sh_rc` → 同会话附录 7 释放核 | `test_end_to_end_…`（编号 1、无 `--http-ledger`/`--non-inference-reserve`、`echo DIAG_CLOSEOUT_DONE`）、`test_service_refusal_…` |
| 4 两连接与一次加载 | `DiagAccount.take("master_connections")` 在尝试前扣次（≤ 2）；`d1` 准备、`d2` 服务/轮询/回传；控制套接字失效记 UNKNOWN 不回退；服务启动含拒启占 1、故障重启 0；measure 与 Play 共用同一次服务驻留 | `DiagAccountTests.test_limits_wall_and_disk`、`test_service_refusal_…`（2/1/0） |
| 5 诊断输入与网页 | measure ≤ 1、仅 rc 0 才 k-receipt ≤ 1、只写 `receipt/`；一次 Play/一会话；开跑前 `--playbook` 冻结一个剧本；网页 W1–W5、本人发送/跳过与确认/拒绝 | `test_measure_failure_never_runs_k_receipt_or_play`、`test_end_to_end_…` |
| 6 粗账/磁盘/截止 | `ops-diagnostic-ledger.json`（用途+request_id、起止 UTC/epoch、elapsed、主连接尝试与 rc、服务启动/重启/GGUF 加载、Play/会话/f₀/T_sess/YOLO 加载、按钮时刻 UNKNOWN、两端读数/峰值/来源、STOP/故障/UNKNOWN/未执行阶段与步骤、收尾）；`ops-events.jsonl`、`play/ops-web.jsonl`、`NOTES.md`、`raw/` 同根；每个受限动作前查额；Play 期间 Air 10 s/板 60 s 轮询，达 90% 即 STOP1；墙钟留 420 s 收尾预留；越界照记 deviation 不追认 | `DiagAccountTests.test_limits_wall_and_disk`、`test_end_to_end_…` |
| 7 四类 STOP 与故障 | `DiagStop(1…4)` 与 `DiagFault`（含复用正式辅助函数抛出的原文，只记为诊断故障、不套正式码）；故障后只做安全收尾、不重启/重测/新连接/新 Play；非 0 退出并列未执行阶段 | `test_service_refusal_…`、`test_status_…`、`test_measure_…` |
| 8 收尾/证据边界 | 停会话 → 本人停 Play → 帧环/真值只移入 `play/<SID>/` → Ctrl-C/服务退出 → 同会话释放核 → 日志 tar（不含缓存）→ 关连接 → 覆盖文件入 `hold/overlay-diag.json`、残留归位 → 结束计时；之后独立进程 `summarize_ops --mode diagnostic`（不评分、不读真值/四表）；诊断原件不进 `docs/evidence/` | `test_end_to_end_…`；`tests/test_loop2_isolation.py::OpsIsolationTests.test_diagnostic_summary_only_after_closeout_without_scoring` |

## 3. 逐文件范围（「OPS九题答复落实」§3 闭集内；本轮 `b309b36..d0bba83`）

| 路径 | 本轮改动 | AC |
|---|---|---|
| `tools/eng_loop2/play_ops.py` | IR-OPS-1/2/4 文案与 `require_g4` 读失败闭合；IR-OPS-6 调度；`archive_attempt` 增诊断只移动模式（真值文件仍只在此函数、无读取）；`measure_argv`/`k_receipt_argv`/`session_argv`/`first_measure_failure` 抽出共用；正式与诊断交互 bash 首行关闭行编辑与回显（`set +o emacs +o vi; stty -echo`，标记行不被预键入回显夹杂）；诊断模式全部新增 | 8/9/10/14/15/16 |
| `tools/eng_loop2/operator_web.py` | 回执记录增绑纪元；`App(banner=…)` 与页首横幅 | 5/10/11 |
| `tests/test_eng_loop2_play_ops.py` | 替身扩展（板核/同步/诊断服务/附录 7/状态核/诊断会话段根）；`ObservationAnchorTests` 6 例、`DiagAccountTests` 1 例、`DiagTests` 7 例、模式路由 1 例；旧调度用例改写同纪元原流事件 | 8/10/14/15/16 |
| `tests/test_loop2_isolation.py` | 只在本增量上轮新增的 `OpsIsolationTests` 内：摘要调用所有者由 `{stage_play}` 扩为 `{stage_play, run_offline_summary}`（删除行 2，均为该断言本身），并追加更强的新断言（诊断摘要只在收尾后、`--mode diagnostic`、诊断类无评分/真值/几何字符串）；pre-Ops 既有断言零改动 | 9 |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md` | 修订记录；第 0A 节 IR-OPS-1/2 机读行与模式路由；第 1、9、10、13 节 OPS 段按 IR-OPS-1…4/6 改写 | 10/14/15/16 |
| `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` | 页首许可改为现行 SUB:3；新增「现行 SUB:3」节（前提、唯一命令、工具步骤与本页第 1–7 步对照、本人操作、STOP/故障、原件边界）；附录 3 只许编号 1（标题与提示同步）；附录 4/5/7 与其余步骤原样 | 10/11/14/16 |
| `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md` | 只加一段说明：诊断不使用附录 A/B；块正文不变 | 10/16 |
| `runtime/README.md` | 诊断模式在 `runtime/` 的只移动/归位说明 | 10/13 |
| 本文件、`docs/evidence/P1-ENG-LOOP-002-ops-tests.log`、`docs/current-status.md` | 停点证据、全套原输出、交接行 | 11/13 |

禁改路径（`controller/`、`Assets/`、`config/`、`ProjectSettings/`、`Packages/`、`tools/language_serve.py`、`tools/language_latency.py`、`tools/eng_loop2/{__init__,llama_adapter,deploy_digest,analyze_play}.py`、LOOP-001 旧载体）自本增量起点 `db10b5e` 至 `d0bba83` 零 diff（`git diff --stat db10b5e..d0bba83 -- <上列>` 为空）；无第三方依赖、无新板服务、部署 16 路径不变。

## 4. 停点全套（SUB:1，`P1-ENG-LOOP-002:9bac8fd0:SUB:1`；本候选 1/1，已用尽本候选次数）

- 命令（清单 §2 原样，不带 `-v`）：`/usr/bin/time -l python3 -m unittest discover -s tests > docs/evidence/P1-ENG-LOOP-002-ops-tests.log 2>&1`；执行检出 HEAD `d0bba83`、工作树干净（`git status --porcelain` 0 行）；MacBook Air 系统 `python3`（`/opt/homebrew/bin/python3`，3.14.6）；未装包、未设数据根。
- 起止 `2026-10-08T02:22:16Z` → `02:33:46Z`；`/usr/bin/time` 690.07 s real（≤ 900 s）；峰值内存 786,072,632 B；原输出 `docs/evidence/P1-ENG-LOOP-002-ops-tests.log` 44,896 B（≤ 2 MB）；网络/设备/Play/正式 ID 0；归档回放 0。
- 结果：`Ran 2430 tests`，`FAILED (failures=5, errors=13, skipped=54)`，rc 1。**本增量的测试（`test_eng_loop2_play_ops`、`test_eng_loop2_operator_web`、`test_eng_loop2_summarize_ops`、`test_loop2_isolation`）及 `test_language_loop`、`test_eng_loop2_analyze` 在全套中零失败。**
- 真实模型加载：新三份工具测试与隔离追加 = 0；既有部分执行前静态复核——NanoTrack-v2 真实 ONNX 构造只在 `tests/test_trackers.py`/`tests/test_track_loop.py` 各 1 例（资产缺失即跳过）、CSRT 构造尝试同两文件各 1 例（系统 `python3` 无 `cv2`，本次随之跳过/不执行）、det-assoc/YOLOE 只在有 `ultralytics`+`lap` 时运行（系统 `python3` 无，跳过），DINOv2/VLM/HF 0。**本次全套内实际加载数 UNKNOWN**（未插桩；按签发口径如实记，不以静态数冒充）。

### 4.1 基线失败与新增失败分列（对照 N-1 三份全套日志同一 13 项基线，`-tests.log`/`-tests-stable.log`/`-tests-rework1.log` 逐名一致）

| 类别 | 项（`docs/evidence/P1-ENG-LOOP-002-ops-tests.log` 原名） | 归因与核验 |
|---|---|---|
| 基线仍失败（6） | `test_dist_data_round8` ×2（ambiguous_manifest、m3_armA_family）；`test_rate3_protocol.Rate2ArchiveRegressionTests.test_archived_decision_a_recomputes_identically`；`test_dist_data_round4.RealArchiveClosureTest` ×3（arm_a_truth、void_run、zero_unmatched） | 与 N-1 同名同类（主树 `runtime/`/归档残留相关的既有基线） |
| 基线不再出现（7） | `test_eng_sft_audit/build/cloud/evaluate`、`test_language_k_binding`（原为导入失败）；`test_trackers…csrt…`、`test_track_loop…csrt…` | 未逐一核原因；CSRT 两例随系统 `python3` 无 `cv2` 不再执行；不据此称修复 |
| 相对 N-1 新出现，归因**环境**（10） | 导入失败 8：`test_benchmark_reanchor`、`test_detector_scouting`、`test_rate2_protocol`、`test_rate3_difficulty_audit`、`test_rate_study`、`test_scene004_gate0_probe`、`test_scene004_scouting`、`test_scene006_probe`；用例 2：`test_rate3_protocol…test_rate3_reanchor_clock_mismatch_raises_defensively`、`test_eng_jet_bench…test_rect_engine_imgsz_override_only_in_harness` | 原文均为 `ModuleNotFoundError: No module named 'numpy'`/`'cv2'`。现场核：系统 `python3` 3.14.6 现在 `import numpy`、`import cv2` 均失败（N-1 时这些模块可导入）——解释器环境漂移，非代码改动；本派发不得装包，未修 |
| 相对 N-1 新出现，归因**既有/环境**（2） | `test_eng_jet_relay.LoopbackTwoProcess.test_atomic_publish_order`（`AssertionError: 16/17/18 != 25`）、`test_eng_jet_track_responder.LoopbackTrackWithDrop.test_analyze_track_return_and_disconnect`（`0 != 1`） | 主树 focused 复跑同样失败；在派发 base `b309b36`（本轮改动之前）的一次性 worktree 中以只读符号链接补 A7 帧后 focused 复跑**同样失败**（`17 != 25`、`0 != 1`）；两模块不导入 `tools/eng_loop2` 任何文件（`grep` 核）。属本轮之前已存在于当前环境的失败（回环计时类，机器负载 load avg ≈ 4），非本轮新增 |
| **本轮代码导致的新增失败** | **0** | 改动只在 `tools/eng_loop2/{play_ops,operator_web}.py`、其测试与文档；上表 12 项失败模块均不导入这些文件 |

**判读**：全套不绿；按派发「新增失败先修复」要求，相对 N-1 的 12 项新出现失败经上表核验均非本轮代码引起，本派发内无可修的代码缺陷（环境修复需装包，签发为 0）；**未跑第二次全套**。新的环境基线（12 项）是否接受为本停点基线、或先恢复系统 `python3` 的 numpy/cv2 再用下一候选的 SUB:1 重跑，交用户/接受决定（报告 needs_user）。

## 5. 承接声明与人眼保真（SUB:2；执行人 = 用户本人；**已执行 1 次：两张一致**，记录见 5.1；以下至 5.1 之前为前版准备记录，保留为历史）

**承接声明**：网页只显示会话写出的预览原字节（文件名 + 字节 sha256 绑定，浏览器解码后才回报「已显示」），不重绘、不换框、不补几何身份提示；原预览生成/采集/帧环/保存协议与 `controller/`（含 LanguageWorker/CandidatesBackend/`_validate_candidates_source`/`candidates_preflight`）零 diff（第 3 节）。本轮对呈现相关代码的唯一改动是页首横幅（`S.mode_banner`），候选图 `<img>`、按钮与绑定逻辑未改。

**实现只做的准备（零模型、0 B、未看图）**：

- 样图（清单与签发所列 Air 第三、四次诊断现有候选预览，只读、不复制、不转证据），运行时只读核得：

  | # | 路径 | 字节 | 尺寸 | sha256 |
  |---|---|---|---|---|
  | 1（第三次） | `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261007T231337Z/sessions/diag-loop2-231911/previews/328-diag-loop2-231911-q1.png` | 87,844 | 640×480 | `721c37b990aa003e473cd98c468b4d325def635f7b0378200cc5032a46d93946` |
  | 2（第四次） | `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261007T234520Z/sessions/diag-loop2-234800/previews/188-diag-loop2-234800-q1.png` | 87,711 | 640×480 | `29add607ea57486fc5ceb9b285bfb7d22bc8d0e33cbe9a4815afab692073a4fb` |

  旁记（只读事实，不作判断）：第四次目录三张预览（q1/q2/q3）字节 sha 完全相同，故第四次只取 1 张。
- 对应候选呈现代码：`tools/eng_loop2/operator_web.py` 于 `d0bba83` 的 blob `3ecd79602634e988c4223af18fa41731fbec7fdf`（保真页 `FIDELITY_PAGE` 与操作页候选预览同一 `<img>` 呈现方式）；此后若该文件呈现代码改变，本记录不再对应，须在剩余额度内重做。
- `operator_web.load_fidelity_samples` 对两张样图只读解析通过（PNG 签名/尺寸/文件名闭集）；**实现未启动保真页、未在浏览器看图**。

**用户本人需执行的确切一条命令**（MacBook Air 终端，系统 `python3`，只读页仅监听 127.0.0.1:8773，≤ 15 min，不复制样图）：

```bash
cd ~/TetheredDroneTracking && python3 -m tools.eng_loop2.operator_web fidelity outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261007T231337Z/sessions/diag-loop2-231911/previews/328-diag-loop2-231911-q1.png outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261007T234520Z/sessions/diag-loop2-234800/previews/188-diag-loop2-234800-q1.png
```

然后在浏览器打开 `http://127.0.0.1:8773/`；对照原图可另在 Finder/预览中直接打开上表两条路径（只读）。看完在终端按 Ctrl-C 结束。

**要看什么**：每张样图面板下的提示行是否为绿色「浏览器收到字节 sha256 一致：…」并带「已解码 640×480」；网页上显示的图与直接打开的原图在外观语义上是否一致——候选框的数量、各框位置/大小、框上的序号标注及其顺序完全相同，没有被重绘、缩放裁切、换框或额外叠加任何提示；图像没有损坏/错色/截断。

**要回报什么**（经 supervisor 转呈，由实现或有权限角色原样记入本节，注明来源为用户本人）：① 看了哪两张（路径或文件名）；② 每张的结论「一致 / 不一致」及看到的提示行（绿色一致+已解码，或红色不一致/解码失败）；③ 若不一致，描述差异（哪张、哪个框/序号/位置/颜色）；④ 看图人 = 用户本人确认；⑤ 用时（可选）。不一致或打不开即先修呈现代码，在 SUB:2 剩余额度内重核。

### 5.1 用户本人结论（`P1-ENG-LOOP-002:9bac8fd0:SUB:2`；轮次 `OPS稳定候选` 按「OPS基线与IR78裁定」§4 转记）

- **来源**：`docs/unity-test-log.md`「UT-P1-ENG-LOOP-002-OPS-SUB2」（supervisor 会话代录，Status `USER_FIDELITY_REPORTED_CONSISTENT`）；接受读法见同名提案「OPS基线与IR78裁定」§4。实现角色未看图、未代判，本节只转记，不改用户日志或账本。
- **确认人**：用户本人（MacBook Air 本机终端启动上节命令，127.0.0.1:8773 只读保真页对照原图）。
- **逐张结论**（用户原话见日志条目，核心为「两张都一致」）：

  | # | 样帧（只读诊断原件，未复制入证据） | 结论 |
  |---|---|---|
  | 1 | `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261007T231337Z/sessions/diag-loop2-231911/previews/328-diag-loop2-231911-q1.png` | 一致（用户本人） |
  | 2 | `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261007T234520Z/sessions/diag-loop2-234800/previews/188-diag-loop2-234800-q1.png` | 一致（用户本人） |

- **UNKNOWN**：每张面板下提示行的实见值（绿色 sha 一致 / 已解码 640×480）——`UNKNOWN（用户未逐项报告）`；用时——`UNKNOWN（未报告）`。不代写「看到绿色」或墙钟守限；字节/解码绑定的机械核由代码与替身证据承担（`tests/test_eng_loop2_operator_web.py` 的 `FidelityPageTests.test_fidelity_page_serves_bound_samples_read_only`、`HttpTests.test_preview_and_frame_paths_are_bound`），不以自动 sha 代替人眼。
- **第 1 张消防栓追问**：用户同时问第 1 张为何标了消防栓。该框是第三次诊断当时 VLM 输出的唯一候选，归因见同名提案「第三次诊断核清与本人诊断落实」§2；这不推翻呈现一致，也不证明 VLM 选对/跟对，不作正式指标或模型通过证据。
- **呈现代码对应关系（运行时 `git rev-parse <提交>:tools/eng_loop2/operator_web.py`）**：用户日志登记 HEAD `0c1eb68`、上一候选 `d0bba83`、本候选 `49e83f5` 三者均为 blob `3ecd79602634e988c4223af18fa41731fbec7fdf`。本轮未改 `operator_web.py`（`play_ops.py` 的改动只是 `sub3_release` 文案/拒启分列，不经过保真页或候选 `<img>` 呈现），故按签发「候选间网页呈现代码不变则复用同次记录」**复用本次记录、不重做**；以后该 blob 变化则须在 SUB:2 剩余额度内请本人重核。
- **额度**：SUB:2 按已签记已执行 1 次（本候选系列）；样图新增 0 B；板/Play/正式 ID 0。

## 6. 待裁定（前版提出；**IR-OPS-7/8 已于「OPS基线与IR78裁定」§2/§3 裁定，并已在 `49e83f5` 落实，见第 10 节**；下表保留为历史原文）

| 编号 | 问题与现状 | 实现的现行读法（fail-closed） | 需要的裁定 |
|---|---|---|---|
| IR-OPS-7 | 「OPS验证额度落实与IR裁定」§5.4 要求 SUB:3 前代码「独立通过**且被接受消费**」，但「接受消费」没有机读字段；工具能机械核的只有复核文件的最新有效 `passed_candidate`、HEAD 等于它、PLAY_GOVERNING 空 diff 与全局 blocks | `diag` 另要求发布引用上的同名提案含接受写的独立行 `sub3_release: <passed_candidate 40 位小写 sha>`（可带列表记号/反引号；仿 IR-OPS-1）；缺行/不匹配 → `DIAG_REFUSED`（未消耗任何受限维度）；脚本不自签 | 采纳该行格式与写入位置（建议与消费裁定同节），或给替代机读形式 |
| IR-OPS-8 | 正式单 `$OUT=outputs/eng-loop2/P1-ENG-LOOP-002` 被第 0A/1.2 节称为「被忽略路径、不进 dirty 判据」，但仓库 `.gitignore` 只忽略 `/outputs/eng-loop/`，`git check-ignore outputs/eng-loop2/x` 返回未忽略：任一正式阶段写出 `$OUT` 后，下一次 `gate`/单元前重跑的 1.2 整树干净核对必报 `worktree_not_clean`（正式流程自阻）。`.gitignore` 不在本增量闭集，实现未改 | 不改；如实记录（诊断根在 `outputs/eng-loop/` 下，已被忽略，不受影响） | 由有权限角色在 `.gitignore` 追加 `/outputs/eng-loop2/`，或改正式 `$OUT` 到已忽略路径（后者改操作单与工具缺省值，属 PLAY_GOVERNING） |

另记（不需裁定，只说明）：诊断放行核对复用正式第 1.0 节机制，含一次 `git fetch origin`（GitHub 网络读）；SUB:3「网络/SSH」行未单列 GitHub 读取，本读法视其为放行核对的既有组成部分，若接受认为须单列，请一并裁定。

## 7. 稳定候选四条件自证（workflow §4.3.1）

### 7.0 现行自证（轮次 `OPSC6返工`；候选 `d3c3ff0`；**交 `C7@OpsK1K2K3K4`**；7.0 之后为前版 `OPS稳定候选`/`49e83f5` 的原文，保留为历史）

**候选与完整 diff 基线（运行时从本交接登记与 git 解析）**：
- 候选提交 `d3c3ff03d8c73a9f0adb40cb5c6546f9ad1a89db`（PLAY_GOVERNING 末次改动所在提交；其后只有证据/状态文档）；本轮第 1 个候选提交 `b6bd195bf1bca56f0107f82d2b802d923b614bfd`（SUB:1 实测）。
- 完整 Ops 增量 diff：`git diff db10b5e..d3c3ff0`（`db10b5e` 同前，见 `-ops-progress.md` 页首）；本轮相对上一候选：`git diff 49e83f5..d3c3ff0 -- tools tests docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md docs/evidence/P1-ENG-LOOP-002-play-ops.md`（8 路径：三工具、三测试、两操作单）；`.gitignore`、mini-prep、`runtime/README.md`、`tests/test_loop2_isolation.py` 本轮未改。
- 相对最近有效通过候选 `9d95aeb`（`R1@K1K3`）的 PG/操作单路径集合与前版相同（10 路径，`git diff --name-only 9d95aeb..d3c3ff0 -- <PG 路径> <三份操作单>`）。
- 禁改路径 `git diff --stat 49e83f5..d3c3ff0 -- controller Assets config ProjectSettings Packages tools/language_serve.py tools/language_latency.py tools/eng_loop2/__init__.py tools/eng_loop2/llama_adapter.py tools/eng_loop2/deploy_digest.py tools/eng_loop2/analyze_play.py tools/eng_jet tests/test_loop2_isolation.py` 为空。

| 条件 | 自证 | 证据指针 |
|---|---|---|
| 1 范围与接口冻结 | 只在「OPS九题答复落实」§3 逐文件闭集内修核对表 C6-1/2/3；未改 AC/修订/合同读法，无新待裁定；本候选后不再改 PLAY_GOVERNING/操作单 | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#11.1`；cmd: `git diff --stat 49e83f5..d3c3ff0`；cmd: 上列禁改路径 `git diff --stat`（空） |
| 2 相称测试 | `b6bd195` 上 SUB:1 全套 1 次（408 s，2450 例，基线 16 项照旧 + 2 项 JET 回环未现 + 新增 1 项=真实竞态）；`d3c3ff0` 竞态窄修以 engineering §6 替代（四模块 focused 133 例 OK + 修前红 3/3/修后绿 3/3），**补丁未跑全套**；C6 三项生产入口失败路径修前红/修后绿齐 | artifact: `docs/evidence/P1-ENG-LOOP-002-ops-c6rework-tests.log`；artifact: `docs/evidence/P1-ENG-LOOP-002-ops-c6rework-focused.log`；artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#11.2`、`#11.3`；cmd: `python3 -m unittest tests.test_eng_loop2_play_ops tests.test_eng_loop2_operator_web tests.test_eng_loop2_summarize_ops tests.test_loop2_isolation`（133 例 OK） |
| 3 已知 Unity 失败/人眼义务 | 无 Unity 运行、无已知 Unity 失败；AC-11 修订 1 人眼保真：呈现路径零 diff 但 `operator_web.py` blob 已变，是否须本人用 SUB:2 剩余次数重看**交接受判读**（不自看、不自称复用） | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#11.4`；cmd: `git rev-parse d3c3ff0:tools/eng_loop2/operator_web.py`；cmd: `git diff -U0 49e83f5 d3c3ff0 -- tools/eng_loop2/operator_web.py` |
| 4 复核入口/状态/候选/风险 | 复核入口 `docs/reviews/P1-ENG-LOOP-002.md`（新范围 `R1@OpsK1K2K3K4` 由复核角色开节）；状态板交接行已更新（Acceptance `C7@OpsK1K2K3K4`）；未测风险见第 8、11.5 节；核对表 §4 PR-O1/O2/O3 原样照交 | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#11.5`；artifact: `docs/evidence/P1-ENG-LOOP-002-C6-OpsK1K2K3K4.md#4`；artifact: `docs/current-status.md#Active handoffs` |

**逐 AC 证据增补（本轮；其余沿下方前版逐 AC 表，指针仍有效）**：

| AC | 本轮增补证据 | 后置/未运行 |
|---|---|---|
| AC-5 修订 1（W4 防重复/未知结果） | test: `tests/test_eng_loop2_operator_web.py::SubmissionTests.test_sealed_session_refuses_every_business_action_but_allows_one_stop`；test: `tests/test_eng_loop2_play_ops.py::HaltTests` | 真实 Play |
| AC-8 修订 3（计划逐步实际/原因） | test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_s_load_keeps_full_attempt_record_and_summary_maps_accepted_requests`；test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_backend_fatal_terminal_keeps_accepted_request_and_reason`；test: `tests/test_eng_loop2_play_ops.py::HaltTests.test_accepted_send_racing_terminal_is_recorded_before_closeout_can_read`；test: `tests/test_eng_loop2_summarize_ops.py::PlanVsActualTests` | 真实归档对应 |
| AC-10 修订 3/4（O1/O3 失败安全收尾、STOP 不重试） | test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests`（6 例）；test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_stop1_during_play_seals_runner_and_web_until_late_terminal`；test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_ctrl_c_during_play_with_unknown_stop_stays_sealed_and_never_resends`；artifact: `docs/evidence/P1-ENG-LOOP-002-play-ops.md`（第 9、13 节 OPS 增量）；artifact: `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`（现行 SUB:3「STOP 与故障」） | 前台 `ssh -tt` 真实板未验证 |
| AC-14 修订 1/2（按钮 420 s、按钮时刻 UNKNOWN、无重试） | test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_hung_session_past_wall_gets_one_stop_and_full_safe_closeout`（截止 = 等待起点 + 420 s 的缩放值）；test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_unity_still_publishing_after_deadline_is_s_wall_without_archive` | 正式三次 Play NOT_RUN |
| AC-18 修订 1（摘要一致性） | test: `tests/test_eng_loop2_summarize_ops.py::PlanVsActualTests.test_halted_accepted_steps_stay_samples_with_their_receipts`；test: `tests/test_eng_loop2_summarize_ops.py::PlanVsActualTests.test_attempt_without_step_record_is_record_unknown_not_unexecuted` | 正式归档与复核重放后置 |
| AC-13 修订 1 | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#11.3`（全套与替代适用性）；cmd: `git diff --numstat 49e83f5..d3c3ff0` | — |

### 7.1 前版自证（轮次 `OPS稳定候选`；候选 `49e83f5`；已被 C6 首退，保留为历史）


前版（`d0bba83`）判未满足：条件 2 的 12 项新基线待裁定、条件 3 的 SUB:2 NOT_RUN。两项已分别由「OPS基线与IR78裁定」§1（接受 12 项为本停点环境基线、条件②满足）与 §4/本文件 5.1（用户本人两张一致）闭合。

**候选与完整 diff 基线（运行时从本交接登记与 git 解析，不手抄派生值）**：
- 候选提交 `49e83f5e2f5f69f4b281fba8b291bd8a78810ab7`（PLAY_GOVERNING 末次改动所在提交；其后只有本文件/状态板等证据文档）。
- 完整 Ops 增量 diff：`git diff db10b5e..49e83f5`（`db10b5e` = 本增量首轮 `OPS操作增量实现` 登记的派发 base_head，见 `docs/evidence/P1-ENG-LOOP-002-ops-progress.md` 页首）；其中 PLAY_GOVERNING 与操作单、`.gitignore` 共 11 路径：`tools/eng_loop2/{play_ops,operator_web,summarize_ops}.py`（新增）、`tests/test_eng_loop2_{play_ops,operator_web,summarize_ops}.py`（新增）、`tests/test_loop2_isolation.py`（+105/−0）、三份操作单（正式单 +47/−9、诊断页 +44/−6、mini-prep +6/−0）、`.gitignore`（+2/−0）。其余为证据/状态/提案文档。
- 相对最近有效通过候选 `9d95aeb`（`R1@K1K3`）：`git diff --name-only 9d95aeb..49e83f5 -- <PG 路径> <三份操作单>` = 上述 10 个 PG/操作单路径（`.gitignore` 不在 PG 定义内）；其中诊断页另含 Ops 起点前的 `e1912e7`（「诊断页修复交付」，已由「诊断页修复核清与RESUME2落实」核清）一段，非本增量。
- 相对 SUB:1 实测提交 `d0bba83` 的改动 = 本轮 5 路径（第 10 节表）。
- 禁改路径（`controller/`、`Assets/`、`config/`、`ProjectSettings/`、`Packages/`、`tools/language_serve.py`、`tools/language_latency.py`、`tools/eng_loop2/{__init__,llama_adapter,deploy_digest,analyze_play}.py`、`tools/eng_jet/`、LOOP-001 旧载体）`git diff --stat db10b5e..49e83f5 -- <上列>` 为空；无第三方依赖、无新板服务、部署 16 路径不变。

| 条件 | 自证 | 证据指针 |
|---|---|---|
| 1 范围与接口冻结 | 「OPS九题答复落实」§3 逐文件闭集 + 「OPS基线与IR78裁定」§3 唯一 `.gitignore` 路径内全部落地；IR-OPS-1…8 与 §4 诊断模式合同均已实现，无未裁定实现读法；本候选后不再改 PLAY_GOVERNING/操作单 | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#1`、`#2`、`#3`、`#10.1`；artifact: `docs/evidence/P1-ENG-LOOP-002-ops-progress.md#1`；cmd: `git diff --stat db10b5e..49e83f5`；cmd: `git diff --stat db10b5e..49e83f5 -- controller Assets config ProjectSettings Packages tools/language_serve.py tools/language_latency.py tools/eng_loop2/__init__.py tools/eng_loop2/llama_adapter.py tools/eng_loop2/deploy_digest.py tools/eng_loop2/analyze_play.py tools/eng_jet`（空） |
| 2 相称测试 | `d0bba83` 上 SUB:1 全套 1/1（2430 例，基线 18 项经接受裁定为本停点基线，Ops 相关零失败）；本轮窄修按 engineering §6 替代：四个 Ops 模块 focused 118 例 OK（候选提交态复跑）+ IR-OPS-7/8 修前红/修后绿；**补丁未跑全套、不记全套通过**；替代适用性逐文件理由见第 10.3 节，复核可判不足 | artifact: `docs/evidence/P1-ENG-LOOP-002-ops-tests.log`（SUB:1 原输出）；artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#4.1`；artifact: `docs/evidence/P1-ENG-LOOP-002-ops-ir78-tests.log`（修前红/修后绿与 focused 原输出）；artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#10.2`、`#10.3`；cmd: `python3 -m unittest tests.test_eng_loop2_play_ops tests.test_eng_loop2_operator_web tests.test_eng_loop2_summarize_ops tests.test_loop2_isolation`（候选提交态 118 例 OK） |
| 3 已知 Unity 失败/人眼义务 | 本增量无 Unity 运行、无已知 Unity 失败待修；AC-11 修订 1 人眼保真由用户本人完成（两张一致），呈现代码 blob 不变而复用；SUB:3 诊断与正式 Play 按合同后置，不是本停点义务 | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#5.1`；artifact: `docs/unity-test-log.md#UT-P1-ENG-LOOP-002-OPS-SUB2`；cmd: `git rev-parse 49e83f5:tools/eng_loop2/operator_web.py`（= `3ecd79602634e988c4223af18fa41731fbec7fdf`，与用户日志登记一致） |
| 4 复核入口/状态/候选/风险 | 复核文件入口 `docs/reviews/P1-ENG-LOOP-002.md`（新范围 `R1@OpsK1K2K3K4` 由复核角色开节；实现不写）；状态板本项交接行已更新（Owner Acceptance）；候选 `49e83f5` 与完整 diff 基线如上；未测风险见第 8 节 | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#7`、`#8`；artifact: `docs/current-status.md#Active handoffs`；artifact: `docs/reviews/P1-ENG-LOOP-002.md`（复核入口，实现不写） |

**逐 AC 证据（本增量全部生效修订；`test:`/`artifact:`/`cmd:` 机读指针，轮次 `OPS稳定候选F10补指针` 按 supervisor 核查 F10 补齐，内容沿用原证据、不新增主张；更细用例名见 `-ops-progress.md` 第 2 节）**：

| AC | 证据 | 本停点外后置/未运行 |
|---|---|---|
| AC-5 修订 1 | test: `tests/test_eng_loop2_operator_web.py::BindingTests`；test: `tests/test_eng_loop2_operator_web.py::DeadlineTests`；test: `tests/test_eng_loop2_operator_web.py::SubmissionTests`；test: `tests/test_eng_loop2_operator_web.py::RealCliTests.test_cli_runner_round_trip_through_production_cli`；cmd: `git diff --stat db10b5e..49e83f5 -- controller`（空，网页只经原 CLI） | 真实 Play |
| AC-8 修订 3 | test: `tests/test_eng_loop2_play_ops.py::SchedulerTests`；test: `tests/test_eng_loop2_play_ops.py::ObservationAnchorTests`；test: `tests/test_eng_loop2_summarize_ops.py::PlanVsActualTests`；artifact: `docs/evidence/P1-ENG-LOOP-002-ops-tests.log`（既有 `test_eng_loop2_analyze` 在 SUB:1 零失败） | 计划—回执—原四表对应须真实归档 |
| AC-9 修订 1 | test: `tests/test_loop2_isolation.py::OpsIsolationTests`（含 `test_diagnostic_summary_only_after_closeout_without_scoring`） | — |
| AC-10 修订 3 | test: `tests/test_eng_loop2_play_ops.py::EndToEndTests`；test: `tests/test_eng_loop2_play_ops.py::ReleaseGateTests`；test: `tests/test_eng_loop2_play_ops.py::SshUnitTests`；test: `tests/test_eng_loop2_play_ops.py::ServeTests`；artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#3`；artifact: `docs/evidence/P1-ENG-LOOP-002-ops-progress.md#1`（三份操作单逐节映射） | 前台 `ssh -tt` 真实板未验证 |
| AC-10 修订 4 | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#1`（IR-OPS-1…6 落点）；test: `tests/test_eng_loop2_play_ops.py::ReleaseGateTests.test_registration_and_g4_machine_lines_fail_closed`；test: `tests/test_eng_loop2_play_ops.py::ArchiveAndStopTests.test_terminal_reasons_map_to_original_stops`；test: `tests/test_eng_loop2_play_ops.py::ObservationAnchorTests`；test: `tests/test_eng_loop2_play_ops.py::ArchiveAndStopTests.test_modes_route_independently` | — |
| AC-10 修订 5 | test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_refused_without_acceptance_release_line_and_consumes_nothing`（缺行）；test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_refused_when_release_value_is_not_the_passed_candidate`（错值）；test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_refused_when_proposal_unreadable_at_release_ref`（读取失败）；test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_contract_format_examples_are_not_release_lines`（格式示例）；test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_end_to_end_single_play_web_closeout_and_summary`（合法匹配）；test: `tests/test_eng_loop2_play_ops.py::FormalOutputIgnoreTests`（3 例）；cmd: `git diff -U0 c747e88..49e83f5 -- .gitignore`（只增两行）；cmd: `git check-ignore -v -- outputs/eng-loop2/P1-ENG-LOOP-002/release/x.txt`（原输出见 `docs/evidence/P1-ENG-LOOP-002-ops-ir78-tests.log`）；artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#10.1`（操作页对应声明） | 实际 `sub3_release` 行只由接受消费后写；本轮未写 |
| AC-11 修订 1 | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#5`（承接声明）；test: `tests/test_eng_loop2_operator_web.py::FidelityPageTests.test_fidelity_page_serves_bound_samples_read_only`；test: `tests/test_eng_loop2_operator_web.py::HttpTests.test_preview_and_frame_paths_are_bound`；artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#5.1`（用户本人两张一致） | — |
| AC-13 修订 1 | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#3`、`#7`（diff 基线）、`#10`；artifact: `docs/evidence/P1-ENG-LOOP-002-ops-validation-plan.md`；artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#4.1`；artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#10.3`（engineering §6 替代）；cmd: `git diff --numstat d0bba83..49e83f5` | — |
| AC-14 修订 1/2 | test: `tests/test_eng_loop2_operator_web.py::FeedbackTests`；test: `tests/test_eng_loop2_summarize_ops.py::ConsistencyTests.test_feedback_kept_verbatim_and_separate`；test: `tests/test_eng_loop2_play_ops.py::DiagAccountTests.test_limits_wall_and_disk`；test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_service_refusal_counts_the_single_start_and_never_plays`；artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#1`（IR-OPS-4 无环境性重试路径） | 正式三次 Play、AC-14 正式证据 NOT_RUN |
| AC-15 修订 2 | test: `tests/test_eng_loop2_play_ops.py::ReceiptTests`；test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_measure_failure_never_runs_k_receipt_or_play` | 真实收据 NOT_RUN |
| AC-16 修订 2/3 | test: `tests/test_eng_loop2_play_ops.py::SourceTests`；test: `tests/test_eng_loop2_play_ops.py::IdentityTests.test_identity_ok_and_failures`；test: `tests/test_eng_loop2_play_ops.py::EndToEndTests.test_receipt_requires_g4_then_runs_unit_2`；test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_status_with_formal_budget_is_fault_and_no_receipt`；test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_existing_board_root_is_fault_before_code_sync` | 板端 NOT_RUN |
| AC-18 修订 1 | test: `tests/test_eng_loop2_summarize_ops.py::ConsistencyTests`；test: `tests/test_eng_loop2_summarize_ops.py::ScoringTests` | 正式归档与复核重放后置 |

**复核范围建议（供 `R1@OpsK1K2K3K4`，复核角色可调整）**：首轮新范围，全量基线 = 最近有效通过 `9d95aeb`，PG diff = 上列 10 路径（Ops 增量部分自 `db10b5e` 起逐行），另读 `.gitignore` 两行；重点为 `play_ops` 门/诊断拒启与一次额度、`operator_web` 绑定与单写者、隔离测试边界、操作单与工具一致性；engineering §6 替代是否充分由复核判定。

## 8. 未核风险与已知限制

- 真实板未验证：前台 `ssh -tt` 交互 bash 中 `stty -echo` 与关闭行编辑后的行为、Ctrl-C 经 pty 送达 `serve-diag.sh` 的前台作业、附录 7 同会话释放核；本地只有替身。
- 诊断粗账的 Air 体积在 Play 期间按「诊断根 + 待移入 `runtime/frames`」投影；板体积靠 `du -sb` 轮询（60 s），两次读数之间的增长不可见，故以 90% 先停。
- （前版风险，已闭合）IR-OPS-7/8 已裁并落实（第 10 节）：诊断仍须接受另写 `sub3_release` 行才可启动（本轮无此行，SUB:3 未放行）；`$OUT` 已被精确忽略，正式 1.2 不再被自身输出自挡（替身验证；真实正式流程未运行）。
- 本轮窄修未跑全套（engineering §6 替代，第 10.3 节）；系统 `python3` 缺 numpy/cv2 的环境基线照旧，未修。
- `sub3_release` 行在提案任意位置匹配即认（与 IR-OPS-1 `g4_release` 同一读法），不限于具名节；裁定文本只要求值与门核 `passed_candidate` 一致，未要求节位置机读。
- 第四次诊断的三张预览字节完全相同（第 5 节旁记），只作事实记录。

## 9. 用量

- 前版轮次 `OPS裁定落实与停点验证`：`SUB:1` 1/1（本候选系列；全套内真实模型加载数 UNKNOWN，静态读见第 4 节）；focused 多次与一次性 worktree focused 复跑 2 次（零模型、无网络）。
- `SUB:2`：用户本人执行 1 次（第 5.1 节；supervisor 代录日志，用时 UNKNOWN）；前候选复用同次记录；对 `d3c3ff0` 的对应关系待接受判读（第 11.4 节）。
- 本轮 `OPSC6返工`：`SUB:1` 本系列第 2 个候选 1 次（`b6bd195`，408 s，日志 44,950 B，实际加载数 UNKNOWN）；零模型 focused 多次（含一次性 worktree 修前红 3 批）；未写 `sub3_release`、未 SSH/板/Unity/Play/诊断/归档回放/5060/云/API/下载/安装/正式 ID/实际 `runtime/` 写入。`SUB:3` 0。
- 本轮 `OPS稳定候选`：consumed=none——零模型 focused（新增 7 例红绿 2 轮 + 3 例红复核 1 轮 + 四模块 118 例 2 次）、本仓库 `git check-ignore` 只读命令；未跑全套、未写 `sub3_release`、未 SSH/板/Unity/Play/诊断/归档回放/5060/云/API/下载/安装/正式 ID/实际 `runtime/` 写入。`SUB:3` 0。

## 10. 轮次 `OPS稳定候选`：IR-OPS-7/8 落实与验证（候选 `49e83f5`）

### 10.1 逐文件改动（相对 `c747e88`，= 相对 SUB:1 实测提交 `d0bba83` 的全部 PG/操作单改动）

| 路径 | 改动 | 依据/AC |
|---|---|---|
| `.gitignore` | 只在 `/outputs/eng-loop/` 之后追加两行：用途注释 + `/outputs/eng-loop2/`；其他规则不删不改，无泛化 `/outputs/` | IR-OPS-8；AC-10 修订 5 |
| `tools/eng_loop2/play_ops.py` | `DIAG_RELEASE_LINE` 注释与模块说明改为已裁定读法；`DiagnosticRun.preflight` 把「提案在发布引用上读取失败」单列 `sub3_release_unreadable rc=…`，缺行/值不匹配仍 `sub3_release_missing`，三者均 `DIAG_REFUSED`、在任何受限动作之前；匹配判据（值 = 门核最新有效 `passed_candidate`）不变 | IR-OPS-7；AC-10 修订 5 |
| `tests/test_eng_loop2_play_ops.py` | `RepoFixture` 增 `gitignore` 参数（缺省值与原夹具相同）；新 `FormalOutputIgnoreTests` 3 例（用本仓库真实 `.gitignore`）；`DiagTests` 新 3 例（错值、读取失败、格式示例不是放行行） | 同上 |
| `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` | 「现行 SUB:3」执行前提中 `sub3_release` 一句改为已裁定读法（写入人/节/值/拒启/格式示例） | IR-OPS-7 |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md` | 修订记录追加本轮一句；第 0.2 节 `$OUT` 行与第 1 节 1.2 的忽略说明改为精确表述（命令/判据不变） | IR-OPS-8 |

另新增证据 `docs/evidence/P1-ENG-LOOP-002-ops-ir78-tests.log`。

### 10.2 修前红/修后绿与命令证据（原输出 `docs/evidence/P1-ENG-LOOP-002-ops-ir78-tests.log`）

| 用例 | 修前（`c747e88` + 仅新测试） | 修后 |
|---|---|---|
| `FormalOutputIgnoreTests.test_repo_gitignore_adds_only_the_exact_formal_output_line` | FAIL `0 != 1` | OK |
| `FormalOutputIgnoreTests.test_formal_output_ignored_but_stray_and_tracked_changes_stay_dirty` | FAIL（`$OUT` 未被忽略） | OK |
| `FormalOutputIgnoreTests.test_release_gate_is_not_blocked_by_its_own_formal_output` | FAIL `['worktree_not_clean']`（正式门被自身输出自挡，即 IR-OPS-8 原缺陷） | OK |
| `DiagTests.test_refused_when_proposal_unreadable_at_release_ref` | FAIL（读取失败与缺行未分列） | OK |
| `DiagTests.test_refused_when_release_value_is_not_the_passed_candidate`、`test_contract_format_examples_are_not_release_lines`、`test_refused_without_acceptance_release_line_and_consumes_nothing` | OK（既有 fail-closed 行为的覆盖补齐，非红绿） | OK |

第 1 次修后运行 6/7 过，唯一失败是新测试自身断言写法（夹具 `git()` 去首尾空白，`" M"` 前导空格丢失），改断言后重跑 7/7；为确认改后断言仍有判别力，又把 `.gitignore` 临时还原为 HEAD 版本重跑 `FormalOutputIgnoreTests`，3 例均 FAIL，随即恢复（日志「修前复核」段）。本仓库只读命令：`git check-ignore -v` 对 `outputs/eng-loop2/P1-ENG-LOOP-002/release/x.txt` 命中新行（rc 0），对 `outputs/eng-loop2x/y`、`outputs/other/y`、`tools/eng_loop2/stray.py` 均 rc 1，诊断根仍由 `/outputs/eng-loop/` 忽略；替身中无关未跟踪与已跟踪改动仍使 `git status --porcelain` 非空、`release_gate` 报 `worktree_not_clean`。四个 Ops 模块 focused：118 例 OK（定稿工作树一次、候选提交 `49e83f5` 干净树一次）。

### 10.3 engineering §6 替代适用性（**补丁未跑全套，不记全套通过**）

- 已有停点全套：`SUB:1` 于 `d0bba83` 跑 1 次，接受裁定 12 项为本停点环境基线、条件②满足（「OPS基线与IR78裁定」§1）；该结论只限 `d0bba83`。
- 本窄修相对 `d0bba83` 只改第 10.1 节 5 个具名路径：`.gitignore` 两行（版本管理配置，不被任何运行时代码导入）；`play_ops.py` 一处拒启分支拆分与注释（诊断入口放行前提，不触模型加载器、数据划分或对外指标路径）；一份测试文件追加用例与夹具可选参数（缺省行为不变）；两份操作单措辞。
- 覆盖改动的零模型 focused：`play_ops` 全部用例 + `operator_web`/`summarize_ops`/隔离三模块（凡复制或解析操作单的夹具都在内），候选提交态 118 例 OK；所修两项各有修前红/修后绿（10.2）。
- 不跑全套的理由：SUB:1 本候选系列 1/1 已用、同候选不得重跑；改动不触真实模型加载器/数据划分/对外指标，满足 engineering §6 前提。若复核判替代不足，可按「OPS基线与IR78裁定」§5 用 SUB:1 剩余至多 2 个候选次数（新具名 `ops-*` 日志）补跑。

## 11. 轮次 `OPSC6返工`：C6@OpsK1K2K3K4 首退三项的修复（**现行候选 `d3c3ff0`** = `b6bd195` + 竞态窄修；派发 base_head `7c341ba`）

- Dispatch-Id `P1-ENG-LOOP-002-OPSC6返工-20261008T041335Z-1edf`；依据 `docs/evidence/P1-ENG-LOOP-002-C6-OpsK1K2K3K4.md` §2（C6-1/2/3 完成条件）、§3、§4、§5，同名提案三节 OPS 合同；未新增 AC/修订，未改合同读法。
- 写入只在原 OPS 逐文件闭集内：`tools/eng_loop2/{play_ops,operator_web,summarize_ops}.py`、三份对应测试、两份操作单（正式单与诊断页的 OPS 增量段措辞），以及本文件、`-ops-c6rework-*.log` 两份新证据与状态板。`.gitignore`、mini-prep、`runtime/README.md`、`tests/test_loop2_isolation.py` 未改。

### 11.1 对核对表 §2 逐项的落点与证据

| 核对项 | 落点（文件/函数） | 证据（机读指针） |
|---|---|---|
| C6-1 STOP/故障/中断后封住业务，只剩 stop/状态读取 | `operator_web.Submitter.seal`/`sealed_reason`：同一把锁内不可逆封住本会话，`submit` 对非 stop 一律拒（runner 与网页同一通道，消除「过检查后再提交」竞态），`claim` 同拒；`App.action` 在 stop 分支之后、任何业务之前核封住。`play_ops.PlanScheduler.halt`：封通道、计划不再推进（观察/release/计划末 stop/下一步都停），在途步骤分列（已受理 → `HALTED`，未知 → `UNKNOWN`，未开始 → `NOT_EXECUTED`）；`_block`（结果未知/原流不可绑定）同样封通道；`record_send/record_decision` 在封住或计划已结束后只经 `_late_reply` 记事实、不推进；`current_send_step/decision_step` 封住即 None。诊断 `DiagnosticRun.halt`：STOP/故障/Ctrl-C/到时一发生即调用，随后每个循环只在 stop 未发出且无在途提交时补发**一次** stop（在途被拒不是发送；结果未知不重发/不换 id）；`finish_play`/`_close_session` 收尾再 `_record_play`。正式 `attempt_closeout` 第 1 步：失败或会话仍在运行即 `halt`。 | test: `tests/test_eng_loop2_play_ops.py::HaltTests`（3 例：待选择时封住→网页确认/拒绝/发送/跳过与 runner release 全拒、迟到 TERMINAL 不恢复、stop 恰一次；在途发送封住后受理记 `HALTED`；结果未知封通道）；test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_stop1_during_play_seals_runner_and_web_until_late_terminal`（生产入口：Play 中 STOP1、TERMINAL 迟到 3 s，期间网页发送/跳过被拒、ask 0、stop 1）；test: `tests/test_eng_loop2_play_ops.py::DiagTests.test_ctrl_c_during_play_with_unknown_stop_stays_sealed_and_never_resends`（生产入口：Ctrl-C、stop 结果 UNKNOWN、不重发、业务被拒）；test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_ctrl_c_during_play_seals_business_and_still_closes_out`；test: `tests/test_eng_loop2_operator_web.py::SubmissionTests.test_sealed_session_refuses_every_business_action_but_allows_one_stop`；artifact: `docs/evidence/P1-ENG-LOOP-002-ops-c6rework-focused.log`（修前红/修后绿） |
| C6-2 正式失败路径安全收尾 | `play_ops.run_attempt` 改为「调用方持有记录、任何退出路径（`BaseException`）先收尾再抛」；`attempt_closeout` 正常与失败同一路径、每步独立记录在 `closeout`、一步失败（含 Ctrl-C）不跳过其余：封住 → `stop_and_wait_session`（`send_session_stop` 沿共享通道、每会话至多一次；等会话自行退出 ≤ `SESSION_STOP_WAIT_S`，仍运行照记 `still_running_after_stop_wait`/UNKNOWN、不杀进程）→ 末次读原流逐步记录 → 提示本人停 Play、等出帧静止 → 加载计数 → 只移动归档（会话或 Unity 未确认停止则不移动、照记）→ 原因码分流。**工具截止 = 等待 Play 起点 + 420 s**（`tool_deadline_unix_s`；不再加 120 s 等待，按钮起止仍 UNKNOWN）：截止时会话仍运行 → `S-WALL`，会话结束后出帧未静止 → `S-WALL`，再等 ≤ `UNITY_STOP_CLOSEOUT_WAIT_S` 只为安全归档（不是额度，照记 `unity_stop_closeout_wait_s`）。`stage_play`：服务停止释放、日志回传、关单元、写 `play-record.json`、独立进程摘要、反馈窗口、关闭本地网页各自 try，失败记 `closeout` 并成为（首个）失败；Ctrl-C/不明异常记 `UNKNOWN` 照做全部收尾，`main` 打印 `STOP UNKNOWN …` 非 0 退出。未开始的剧本以「前序停止：未开始」逐步列入记录。 | test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_hung_session_past_wall_gets_one_stop_and_full_safe_closeout`（会话挂起越截止：stop 恰一次且结果未知、照记仍运行、不移动归档、截止 = 等待起点 + 420 s 的替身缩放值）；test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_unity_still_publishing_after_deadline_is_s_wall_without_archive`（Unity 仍出帧）；test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_ctrl_c_during_play_seals_business_and_still_closes_out`（Ctrl-C）；test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_partial_closeout_failure_does_not_skip_remaining_safe_steps`（日志回传前控制套接字失效：单元关闭、记录、摘要、网页关闭照做）；各例共用 `assert_closeout_complete`（服务已释放、`ssh -O exit` 单元 3、`play-record.json`、`ops-summary.json`、本地网页已关、`closeout_tail` 各步 done）；artifact: `docs/evidence/P1-ENG-LOOP-002-ops-c6rework-focused.log` |
| C6-3 失败尝试保留完整记录、摘要正确对应 | **竞态窄修（`d3c3ff0`）**：`Submitter.submit(on_reply=…)` 在释放共享在途锁之前把结果记入计划（`App` 的发送/选择/停止三处改用），正式 `attempt_closeout` 第 2 步与诊断 `_record_play` 先持有在途锁（≤ CLI 超时 + 5 s）再 tick/封住/读逐步记录，故「会话受理后立即 TERMINAL、网页线程稍后才记录」时已受理请求不再被读成未执行（SUB:1 全套 `b6bd195` 暴露，见 11.3）。`stage_play` 先把尝试记录登记进 `attempts` 再调用 `run_attempt(record=…)`，后者原地填写；收尾写入 `steps`（逐步状态/原因/request_id）与 `steps_detail`（回执/选择/锚点/release 等全部已知事实）、`session_rc`、`session_process`、`terminal_reason`、`f0`/`t_sess_s`/可得时刻、`model_loads`、`archive`（`archive_attempt` 抛 `S-ARCHIVE` 时经 `Stop.report` 保留已移动清单与体积）、`stop`/`stops_all`（触发失败在前、收尾发现的依原顺序追加）、`halted`、`closeout`。会话未启动的步骤记 `NOT_EXECUTED`（原因带 STOP 码），不再缺省。`summarize_ops`：有尝试记录但无逐步记录 → `MISSING_RECORD`（记录未知），不冒充 `NO_PLAY_RECORD`；`designate_not_executed` 只计确实未执行，另列 `designate_record_unknown` 与 `designate_halted`；`HALTED` 仍是样本；尝试原记录字段并入摘要。 | test: `tests/test_eng_loop2_play_ops.py::HaltTests.test_accepted_send_racing_terminal_is_recorded_before_closeout_can_read`（竞态确定性回归，修前红 3/3）；test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_s_load_keeps_full_attempt_record_and_summary_maps_accepted_requests`（S-LOAD：发送 3/跳过 1/未执行 0，一致性问题 0，逐提交都对上会话回执）；test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_backend_fatal_terminal_keeps_accepted_request_and_reason`（终止失败：已受理 ask 保留 request_id 与 backend_fatal 原因，其余确实未执行）；test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_partial_closeout_failure_does_not_skip_remaining_safe_steps`（部分收尾失败仍有完整尝试记录）；test: `tests/test_eng_loop2_summarize_ops.py::PlanVsActualTests.test_attempt_without_step_record_is_record_unknown_not_unexecuted`；test: `tests/test_eng_loop2_summarize_ops.py::PlanVsActualTests.test_halted_accepted_steps_stay_samples_with_their_receipts`；artifact: `docs/evidence/P1-ENG-LOOP-002-ops-c6rework-focused.log` |

新测试全用临时目录替身（临时 git 仓库、假 `ssh`/`curl`、只拦截 measure/k-receipt/derive-bc/score/run 的 Python 替身、生产桥函数写回执/状态的替身会话；Ctrl-C 以 `_thread.interrupt_main()` 注入到生产入口所在主线程），零模型、零 SSH/板/Unity、不写实际 `runtime/`。替身会话新增三种配置（`model_loads`、`terminal_after_requests`、`stop_mode=late_terminal|ignore`），假 `ssh` 新增 `check_fail_marker`；均只在测试文件内。

### 11.2 修前红 / 修后绿（原输出 `docs/evidence/P1-ENG-LOOP-002-ops-c6rework-focused.log`）

- **修前**：一次性 worktree 检出上一候选 `49e83f5`（工具三文件为修前版本），只换入本轮（`b6bd195`）三份测试文件，跑新增 14 例：13 例一批 `FAILED (failures=6, errors=8)`（S-LOAD/终止失败两例因尝试记录丢失 `KeyError: 'steps'`；部分收尾失败例 `play-record.json` 不存在；挂起会话例无 `S-WALL`、会话跑到替身自身 60 s 截止；Unity 仍出帧例 rc 0；诊断两例网页发送未被封住；摘要两例分列缺失；`HaltTests`/网页封住例因修前无封住机制 `AttributeError`）；正式 Ctrl-C 例单独一批：`KeyboardInterrupt` 穿出生产入口、整批中止 rc 130（修前 `stage_play` 不收尾摘要/网页即抛出）。端到端例的修前红都来自行为（正式例夹具对修前代码缺少的收尾常量用 `getattr` 兼容）；`HaltTests` 与网页封住例的修前红是「封住机制不存在」。
- **修后**：候选 `b6bd195` 干净树，同 14 例 `OK`；四个 Ops 模块 focused 132 例 `OK`（原 118 + 新 14）。
- **竞态窄修**：一次性 worktree 检出 `b6bd195`、只换入 `d3c3ff0` 的测试文件，新回归例 3 次均 `FAIL`（`('NOT_EXECUTED', False) != ('NO_CANDIDATE', True)`）；`d3c3ff0` 上 3 次均 `OK`，四个 Ops 模块 focused **133 例 `OK`**（日志 F 段；工作树仅有未跟踪的全套日志）。
- 修前 worktree 用后已移除；修前运行的替身会话在其自身截止内退出。

### 11.3 停点全套（SUB:1 `P1-ENG-LOOP-002:9bac8fd0:SUB:1`，本系列第 2 个候选，1/1）

- 命令（清单 §2 原样，不带 `-v`）：`/usr/bin/time -l python3 -m unittest discover -s tests > docs/evidence/P1-ENG-LOOP-002-ops-c6rework-tests.log 2>&1`；执行检出 HEAD `b6bd195`（本轮第 1 个候选提交）、工作树干净；MacBook Air 系统 `python3`（Homebrew 3.14.6）；未装包、未设数据根；网络/设备/Play/正式 ID/归档回放 0。
- 起止 `2026-10-08T04:49:52Z` → `04:56:40Z`；`/usr/bin/time` **408.22 s real**（≤ 900 s）；峰值内存 1,053,310,976 B；原输出 44,950 B（≤ 2 MB）。实际模型加载数 **UNKNOWN**（未插桩；静态读同第 4 节，新三份工具测试加载 0）。
- 结果：`Ran 2450 tests`，`FAILED (failures=4, errors=13, skipped=54)`，rc 1（2430 + 上一轮 IR78 新增 6 + 本轮新增 14 = 2450）。
- **与第 4.1 节接受的 18 项基线逐名对照**（`grep -E '^(FAIL|ERROR):'` 两份日志 `comm`）：基线 16 项照旧失败；基线中 JET 回环 2 项（`test_eng_jet_relay…test_atomic_publish_order`、`test_eng_jet_track_responder…test_analyze_track_return_and_disconnect`）本次未出现在失败列表——未核原因，不称已修；**新增失败 1 项** = 本轮新测试 `FormalFailurePathTests.test_backend_fatal_terminal_keeps_accepted_request_and_reason`（`('NOT_EXECUTED', False) != ('NO_CANDIDATE', True)`），在 focused 中 5 次均过、全套负载下暴露真实竞态（已受理 ask 被收尾读成未执行，正是 C6-3 要防的情形）。
- **处置**：按「新增失败先修复」在 `d3c3ff0` 做竞态窄修并加确定性回归（11.1 C6-3 行、11.2）；本派发全套至多 1 次，**`d3c3ff0` 未再跑全套**。`d3c3ff0` 相对 `b6bd195` 只改 `tools/eng_loop2/operator_web.py`（`Submitter.submit` 的 `on_reply` 与 `App` 三处调用）、`tools/eng_loop2/play_ops.py`（收尾两处先持有在途锁）与一份测试文件；不触真实模型加载器、数据划分或对外指标路径，按 engineering §6 以「`b6bd195` 停点全套 + 覆盖改动的四模块 focused 133 例 + 修前红/修后绿」替代，**补丁未跑全套、不记全套通过**；复核可判替代不足，届时 SUB:1 剩余第 3 个候选次数（1 次）须新派发使用。

### 11.4 SUB:2 人眼保真与本轮网页改动的对应关系（**需接受判读，可能需用户本人重看**）

`tools/eng_loop2/operator_web.py` 的文件 blob 已变（`git rev-parse d3c3ff0:tools/eng_loop2/operator_web.py` = `13db5f1…` ≠ 第 5.1 节登记的 `3ecd796…`），故第 5.1 节「blob 不变而复用」的读法**不再成立**。本轮改动行（`git diff -U0 49e83f5 d3c3ff0 -- tools/eng_loop2/operator_web.py` 的 15 个块）只在模块说明（W4 一段）、`Submitter`（`sealed`/`seal`/`sealed_reason`/`claim`/`submit` 的封住检查与 `on_reply`）与 `App.action`/`_send_or_skip`/`_decide`/`_stop` 的封住拒绝与 `on_reply` 调用；`PAGE`/`FIDELITY_PAGE`、`FidelityHandler`、`load_fidelity_samples`、`preview_bytes`/`frame_bytes`、`Monitor._presentation`/`preview_identity` 等呈现路径零 diff。实现**未看图、不自判**；是否按「OPS验证额度落实与IR裁定」§2 SUB:2「呈现代码变化则在已签剩余额度内请本人重核」要求用户本人用 SUB:2 第 2 个候选次数重看，交接受判读（见报告 needs_user）。在接受判读前，人眼保真对本候选记「呈现路径零 diff、文件 blob 已变，待接受判读」，不写已复用。

### 11.5 未核风险与已知限制（增补第 8 节）

- 失败路径收尾仍只有本地替身证据：真实板前台 `ssh -tt` Ctrl-C、真实 Unity 停止/出帧、真实会话对 stop 的时延均未验证（PR-O2 原样保留）。
- 工具截止改为「等待 Play 起点 + 420 s」后，本人若在提示后较晚按 Play，会话正常时长（`T_sess` ≤ 290 s，公式未改）加停 Play 余量可能逼近截止并触发 `S-WALL`（fail-closed）；这是把按钮墙钟不可证明处按保守侧处理的代价，未改 `T_sess` 公式或等待 Play 上限。
- 挂起会话例中会话进程在收尾等待后仍运行时，工具不杀进程、不移动归档；该进程随后自行退出的事实只在会话原流/进程日志中，工具记录停留在 `still_running_after_stop_wait`。
- `Submitter.seal` 只按会话封住；正式三剧本中封住后本就停全部后续，未加跨会话封住。
- 测试中「会话挂起」例结束时 Python 报 `ResourceWarning: subprocess … is still running`（不杀进程的预期副作用；替身会话随后自行退出）。
- PR-O1（`sub3_release` 全文匹配）、PR-O3（正式评分失败与调用预算）未在本轮改动，原样交复核。

## 12. 轮次 `OPSR1返工`：R1@OpsK1K2K3K4 阻断 R1-1…4 的修复（**现行返工候选 `5218cc2`**；派发 base_head `2fdf2ec`）

- Dispatch-Id `P1-ENG-LOOP-002-OPSR1返工-20261008T055822Z-5084`；依据复核文件 R1@OpsK1K2K3K4 §3（修复方向与闭合条件）、§5（返工候选须停点全套一次）。未新增 AC/修订，未改合同读法；R1-4 的「≤ 2 次」语义未自行裁定（12.4）。
- 写入只在原 OPS 闭集内：`tools/eng_loop2/{play_ops,summarize_ops}.py`、两份对应测试、正式操作单 §12 一句（评分守账措辞），以及本文件、`-ops-r1rework-{focused,tests}.log` 与状态板。`operator_web.py`（含全部呈现路径）、`tests/test_eng_loop2_operator_web.py`、`tests/test_loop2_isolation.py`、诊断页、mini-prep、`.gitignore`、`runtime/README.md` 与禁改路径均零 diff（cmd: `git diff --stat 2fdf2ec..5218cc2 -- tools/eng_loop2/operator_web.py tests/test_eng_loop2_operator_web.py tests/test_loop2_isolation.py docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md .gitignore runtime controller Assets config ProjectSettings Packages tools/eng_jet tools/eng_loop2/analyze_play.py` 为空）。
- 完整返工 diff：`git diff 2fdf2ec..5218cc2 -- tools tests docs/evidence/P1-ENG-LOOP-002-play-ops.md`（5 路径，+375/−13）。

### 12.1 逐 finding 落点与证据

| Finding | 落点 | 证据（机读指针） |
|---|---|---|
| R1-1（`BC-8`）TERMINAL 改写已受理步骤 | `PlanScheduler._not_executed_rest` 与 `halt` 同口径：`UNKNOWN` 仍记 `UNKNOWN`（reason 追加 `session_terminal:<reason>`）；`AWAIT_DECISION` 或带 request_id 的当前步记 `HALTED`（仍是样本，request_id/回执保留）；`SENT`/`OBSERVING` 原结局不变；只有确实未发送的步骤记 `NOT_EXECUTED`。`summarize_ops.consistency` 新增「记为未执行却带 request_id」告警 | test: `tests/test_eng_loop2_play_ops.py::OpsR1ReworkSchedulerTests.test_r1_1_terminal_during_presentation_keeps_accepted_step_as_sample`（含 `summarize_ops.plan_vs_actual` 该行 `is_sample=True`）；test: `tests/test_eng_loop2_play_ops.py::OpsR1ReworkSchedulerTests.test_r1_1_unknown_step_stays_unknown_when_session_terminal`；test: `tests/test_eng_loop2_summarize_ops.py::ConsistencyTests.test_r1_1_not_executed_step_carrying_request_id_is_reported` |
| R1-2（`BC-10`）确认在途竞态丢受理 | `_await_decision` 状态/结果变化分支在共享在途锁持有时不关 `NO_DECISION`（下个 tick 再判，与截止分支同口径）；`record_decision` 对非当前/已关闭步骤改走新 `_late_decision`：照记 `decisions`（`late: true`）与日志 `late_decision`；APPLIED 且该步是刚关闭的 `NO_DECISION`、其后无任何发送/跳过时恢复该步 `OBSERVING`（`reopened_from`，锚点仍只取会话 receipt 写盘时刻）；不能恢复或结果未知 → 该步 `UNKNOWN` 并停依赖推进 | test: `tests/test_eng_loop2_play_ops.py::OpsR1ReworkSchedulerTests.test_r1_2_confirm_in_flight_when_state_changes_is_recorded_and_observed`（CLI 替身延时 + 会话先写 receipt/`TRACKING`：不 `NO_DECISION`、记 `decision`/`decision_request_id`、锚点 = receipt 时刻、跟随 ≥ 20 s 后 `DONE`）；test: `…::test_r1_2_accepted_decision_after_step_closed_reopens_observation`；test: `…::test_r1_2_accepted_decision_after_later_action_is_unknown_and_blocks` |
| R1-3（`BC-10`）收尾失败与评分 rc 不传播 | (a) `attempt_closeout.failed` 对任何异常（含 Ctrl-C/OSError）都追加进 `found`；(b) 归档因 Unity 未确认停止/会话仍运行被跳过时追加新 `UnknownOutcome`（记 `UNKNOWN`、不是原 11 码），归档中异常记 `archive.skipped`「已移动部分未证明」；`describe_failure` 识别 `UnknownOutcome`；(c) `summarize_ops` 评分 rc≠0 或守账越界时摘要照写并列 `failures`、自身退出 3；`stage_play` 对摘要非 0 置失败（`S-ENVELOPE` 照原码，其余 `UNKNOWN`）→ `play` rc 3，不开下一剧本 | test: `tests/test_eng_loop2_play_ops.py::FormalFailurePathTests.test_r1_3_ctrl_c_in_closeout_unity_wait_is_unknown_and_stops_next_playbook`；test: `…::test_r1_3_archive_oserror_is_unknown_and_stops_next_playbook`；test: `…::test_r1_3_score_nonzero_rc_fails_play`；test: `tests/test_eng_loop2_summarize_ops.py::ScoringTests.test_r1_3_score_nonzero_rc_makes_summary_exit_nonzero` |
| R1-4（`BC-10`，附合同争议）评分次数无守账 | `summarize_ops.take_score_call`：每次评分调用**之前**读 `$OUT/play/score-ledger.json`（`formal_score_calls`），会越过 `FORMAL_SCORE_LIMIT` 即不调用、照记 `S-ENVELOPE`；通过则先计一次再调用（成功/失败共账）；账本不可读即不评分（fail-closed）；已有 `score.json` 的归档不调用、不计。操作单 §12 原句「对每个归档恰调用一次…（计入实现自证 ≤ 2 次）」改为守账描述 | test: `tests/test_eng_loop2_summarize_ops.py::ScoringTests.test_r1_4_formal_score_calls_are_guarded_before_each_call`（三归档 → 恰 2 次调用、第 3 次拒并记 `S-ENVELOPE`、rc 3；换摘要重跑不再调用；账本损坏拒评）；artifact: `docs/evidence/P1-ENG-LOOP-002-play-ops.md`（§12 OPS 增量段） |

回归全用临时目录替身（生产 `PlanScheduler` + 真实 `Monitor`/桥写函数；正式入口用既有临时 git 仓库/假 ssh/Python 替身，替身新增 `score_rc`/`STUB_SCORE_RC` 两个配置；Ctrl-C/OSError 以替换模块函数注入收尾步骤）。零模型、零 SSH/板/Unity、不写实际 `runtime/`。

### 12.2 修前红 / 修后绿（原输出 `docs/evidence/P1-ENG-LOOP-002-ops-r1rework-focused.log`）

- **修前**：工具代码为派发基线 `2fdf2ec` 版本、测试为本轮新增 11 例：`FAILED (failures=10, errors=1)`，全部来自行为（`NOT_EXECUTED`≠`HALTED`/`UNKNOWN`；`NO_DECISION`；Ctrl-C/OSError 后 P2 照常开始并以 `S-PRECHECK` 收尾；评分 rc 4 时 `play` rc 0；摘要无一致性告警；三归档 3 次评分且 rc 0；迟到选择连 `decisions` 都不记 → `KeyError`）。缺常量处用 `getattr` 按已签字面 2 兼容，红不来自缺属性。
- **修后**：同 11 例 `OK`；四个 Ops 模块 focused **144 例 `OK`**（133 + 11）。

### 12.3 停点全套（SUB:1 `P1-ENG-LOOP-002:9bac8fd0:SUB:1`，本系列第 3 个即末个候选，1/1）

- 命令（不带 `-v`）：`python3 -m unittest discover -s tests > docs/evidence/P1-ENG-LOOP-002-ops-r1rework-tests.log 2>&1`；执行检出 HEAD `5218cc2`、工作树干净；MacBook Air 系统 `python3`；未装包；网络/设备/Play/正式 ID/归档回放 0。
- 起止 `2026-10-08T06:11:04Z` → `06:18:05Z`（421 s 墙钟 ≤ 900 s；unittest 自报 418.59 s）；原输出 43,304 B（≤ 2 MB）。实际模型加载数 UNKNOWN（未插桩；新增回归加载 0）。
- 结果：`Ran 2462 tests`，`FAILED (failures=3, errors=13, skipped=54)`（2451 + 本轮 11 = 2462）。
- **与上一全套 `-ops-c6rework-tests.log` 逐名对照**（`grep -E '^(FAIL|ERROR):'` 排序后 `comm`）：16 项 = 第 4.1/11.3 节已接受的环境/既有基线逐名相同；上次新增的 `test_backend_fatal_terminal_keeps_accepted_request_and_reason`（竞态，`d3c3ff0` 已窄修）本次通过；**本轮新增失败 0**。`d3c3ff0` 竞态窄修因此首次在全套负载下通过（此前只有 focused 替代）。
- SUB:1 至此 3 个候选各 1 次全部用尽；R2 若再要求全套，须用户另签。

### 12.4 待裁定与范围外（交接受）

- **R1-4 合同争议（未自行裁定）**：已签「正式归档零模型回放：实现 ≤ 2 次、复核 ≤ 1 次」读作「总次数」还是「每归档」。工具按字面总次数 2 守账（`summarize_ops.FORMAL_SCORE_LIMIT`，fail-closed）：照此，正式 3 剧本全部归档时第 3 次评分会被拒、`play` 以 `S-ENVELOPE` 非 0 退出；若接受裁定为每归档或改合同/信封，只改该常量（及守账键）并补回归。复核核实 ≤ 1 次不经本工具。
- **R1-5 SCOPE_GAP（未实现）**：`Submitter.submit` 的 `on_reply` 异常与在途锁 35 s 未取得两条路径照旧，按复核路由由接受记债或裁定。
- 呈现路径：`operator_web.py` 本轮零 diff（blob 仍为 R1 已核 `13db5f1…`），R1 §4 附议的 SUB:2 两张一致记录按原读法可携带；不申请 `UNITY_NA`。

### 12.5 未核风险与已知限制（增补第 8、11.5 节）

- R1-2 恢复观察只在「刚关闭的 NO_DECISION 且其后无动作」时发生；其余迟到受理一律 `UNKNOWN` 停依赖（fail-closed），不会自动续推。
- R1-3 后，收尾中的任何不明失败都会停后续剧本（含此前只记文本的情形）；真实板/Unity 下的 Ctrl-C 与归档仍只有本地替身证据（PR-O2 照旧）。
- 评分账本按 `$OUT/play` 持久计数；绕过 `summarize_ops` 手工运行 `analyze_play score` 不会入账（操作单未授权该路径）。


## 13. 轮次 `SUB3诊断P1`：已签 SUB:3 诊断整批 1 次的执行指针（**诊断；不进证据链；不作任何门判定**）

- Dispatch-Id `P1-ENG-LOOP-002-SUB3诊断P1-20261008T154457Z-a7f0`；派发基线 `ce6f623`（执行时 origin/main = `334155d`，supervisor 派发登记）。依据：同名提案「OpsK1K2K3K4通过消费与SUB:3放行」§4、诊断页「现行 SUB:3」、账本 2026-10-07「用户按申请签发 OPS 验证额度…」与 2026-10-08 两条（剧本 P1、窗口为现在、先诊断后改评分上限）。本节只给指针与故障/用量/UNKNOWN 说明；原件只在 Air 诊断根，不复制进本目录，不判 AC-14/15/16/18、不写 G4。
- 诊断根（Air，未入版本控制）：`outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261008T155230Z/`（粗账 `ops-diagnostic-ledger.json`、`ops-events.jsonl`、`raw/`、`release/`、`ssh/d1.tsv`、`plan/ops-plan.json`）。板根 `/home/jetson/eng-loop2-diag/20261008T155230Z` **未建**（d1 主连接失败，未执行任何板上命令）。

### 13.1 执行经过

1. 派发时 Unity 未运行（`pgrep` 无进程）；在 Unity 关闭状态下把执行检出（主目录）`git checkout --detach e24e13f`（= 复核 R2 有效 `passed_candidate` = 提案 `sub3_release` 值；相对 `334155d` 只差 7 个 docs 文件，PLAY_GOVERNING/操作单空 diff），工作树干净；另建文档检出 `git worktree add --detach ../TetheredDroneTracking-sub3-docs origin/main`（`334155d`），其中 `check_ledger`/`check_docs` 均 rc 0。
2. 在用户可见终端面板运行包装脚本：先打印本人步骤并等待本人打开 Unity 闭环场景（不按 Play）后按回车；脚本复核 HEAD = 通过候选、`dirty_lines=0`、检测到 Unity 进程后，`exec` 诊断页唯一命令：`.venv-yoloe/bin/python -m tools.eng_loop2.play_ops --docwt <文档检出> --mode diagnostic diag --request-id P1-ENG-LOOP-002:9bac8fd0:SUB:3 --playbook P1 --p2-object red_car`。`--p2-object` 为 CLI 必填项，P1 计划不使用它（`build_plan` 的 P1 只用 B/C/红车），取 `red_car` 同验证计划 F-5 先例，不是 P2 预登记。
3. 本人回车时刻 `2026-10-08T15:52:30Z`。工具 preflight 全过：`RELEASE_GATE_OK`（rel `334155d`、passed `e24e13f`、PG diff 空、消耗性门 OK、账本命中、文档检出自检 rc 0），`sub3_release` 机读行匹配，`derive-bc` 后冻结 P1 计划，Air 环境（ultralytics 8.4.104、MPS True）、det-assoc 资产、`SMOKE_OK 32` 均过；随后移开 runtime 残留（帧环、真值文件）。
4. 第 1 个受限动作 = 主连接 d1：先计 1 次后执行 `ssh -o ControlMaster=yes -o ControlPath=<诊断根>/ssh/cm-d1 … -fN Jetson`，**rc 255**，stderr 原文 `unix_listener: path "…/20261008T155230Z/ssh/cm-d1.gYP1n7UwGTd3hFDK" too long for Unix domain socket`（`raw/026-ssh-master-d1.stderr`）→ `DIAG_FAULT ssh_master_failed d1 (counted; no retry, no new connection)`。按诊断页只做安全收尾：无会话/服务/连接可停，runtime 两项已放回，工作树 0 行；工具输出 `DIAG_END_WITH_ISSUES stop=None faults=1 unknown=0`，结束 `15:52:34Z`。本人未按 Play（工具未走到 Play 提示）。
5. 收尾后执行检出切回 `main`（`334155d`；只差 docs，Unity 未在 Play），文档检出 worktree 已删除。终端面板已向本人说明结果、无需按 Play。

### 13.2 逐维度实账（SUB:3 已签上限 → 实际）

| 维度 | 上限 | 实际 |
|---|---|---|
| 整批次数 | 1 | **1，已用尽**（粗账 `consumed: true`；失败即用掉，不续开） |
| 墙钟 | ≤ 45 min | 3.9 s（15:52:30Z → 15:52:34Z） |
| SSH 主连接 | ≤ 2 | 1（尝试即计；本机控制套接字创建失败 rc 255） |
| 板服务启动 / 故障重启 / GGUF 加载 | 1 / 0 / ≤ 1 | 0 / 0 / 0（粗账 `gguf_loads` 字面 `UNKNOWN`，因服务从未启动且无板上命令，实际为 0） |
| YOLO 加载 / Play / 会话 | ≤ 1 / ≤ 1 / 1 | 0 / 0 / 0（粗账 `yolo_loads` 字面 `UNKNOWN`，未到 Play 与会话，实际为 0） |
| measure / k-receipt | 1 / 1 | 0 / 0 |
| 板新增磁盘 | ≤ 200 MB | 0（未执行板上命令；无板上读数） |
| Air 诊断根 | ≤ 250 MB | 峰值 14,648,011 B（含待归位 runtime 计入），收尾 5,901,361 B |
| 评分/正式 ID/下载/安装/5060/云 | 0 | 0 |

UNKNOWN：ssh 在报错前是否已完成到板的 TCP/认证握手未知（`-N` 不执行远端命令；墙钟 0.28 s），不影响上表（板上无任何命令执行）。本人按钮时刻不适用（未 Play）。

### 13.3 故障归因材料（交接受分级，实现不自裁）

- 位置：`tools/eng_loop2/play_ops.py::DiagConnection.__init__` 把控制套接字放在 `ctx.out / "ssh" / f"cm-{name}"`，诊断根 = 仓库根 + `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/<UTC>/`；OpenSSH 建立 ControlMaster 时在路径后追加 17 字符随机后缀，本机实际路径 120 字节 > macOS `sun_path` 上限 104，故在本机仓库路径下必然失败（与板、网络、Unity 无关）。
- 正式入口 `SshUnit` 用 `outputs/eng-loop2/P1-ENG-LOOP-002/ssh/cm-uN`，本机同口径长度 92 字节，低于上限（只算长度，未实跑）。
- 已有替身测试用假 ssh，不创建真实 Unix 套接字，因而未暴露；修复需按工程轨道正常停点（修前必失败的具名回归 + 复核），本轮未改任何代码。
- 用户 2026-10-08 已签次序：评分上限 ≤ 3 的合同修订/常量/复核排在本诊断之后；本故障修复可与之同批进入一轮复核（是否合批由接受定）。之后若要再跑诊断，需用户另签新的诊断额度（见状态板交接行与派发报告 `needs_user`）。

## 14. 轮次 `评分诊断合批修复`：DIAG-CONTROL-1 与 AC-10 修订 7/8 合批（**进度：零消耗窄修 + focused/红绿/本机 AF_UNIX 已完成；稳定条件②未满足 → 非稳定候选，不交 `C8@OpsScoreDiagK1K4`**）

- Dispatch-Id `P1-ENG-LOOP-002-评分诊断合批修复-20261008T172306Z-224f`；派发基线 `1e1c3b2`（执行时 HEAD `5fff16a`，两者 `tools/`、`tests/` 零 diff）。唯一任务来源：状态板本 work ID 实现交接行与同名提案「SUB3核清与评分上限落实」§2–5（DIAG-CONTROL-1、AC-10 修订 7/8、§4 修改闭集与稳定停点条件）。
- 执行信封：零消耗。SSH 0、板 0、Play 0、真实归档评分/回放 0、停点全套 0、下载/安装 0、写实际 `runtime/` 0、模型加载 0（本轮新增测试与所跑 focused 均零模型）。新诊断（§5 `DIAG:RETRY:1`）与额外全套均未签，未执行。

### 14.1 逐文件变更（§4 修改闭集内）

| 文件 | 变更 |
|---|---|
| `tools/eng_loop2/play_ops.py` | 仅诊断 ControlPath 分配/释放/临时计量：新增常量 `UNIX_SOCKET_PATH_CAPACITY`（macOS/BSD 104、Linux 108、其他按 104）、`OPENSSH_CONTROL_SUFFIX_BYTES = 17`、`DIAG_CONTROL_PARENT`（缺省 None = `tempfile.gettempdir()`）、`DIAG_CONTROL_PREFIX`；新函数 `unix_socket_path_fits`；新类 `DiagControlDir`（`allocate`/`control_path`/`verify`/`entries`/`bytes`/`release`）；`DiagConnection.__init__` 改收 `control` 并以 `control.control_path(name)` 为 `self.cm`，`open` 先 `control.verify()`、残留判定改 `os.path.lexists`、`ssh/<name>.tsv` 记 `control_path` 行、粗账 `master_connections[]` 记 `control_path`；`DiagnosticRun` 新增 `allocate_control`（`prepare_board` 中在 `account.consume()` 之前）、`_release_control`（`_close_connections` 关完主连接后），`air_reading` 加本目录字节。正式 `SshUnit` 及其动作域零改动（`DiagConnection` 继承的 `chan`/`chan_popen`/`channel_argv`/`close` 不变，只是 `self.cm` 来源变了）。 |
| `tools/eng_loop2/summarize_ops.py` | `FORMAL_SCORE_LIMIT` 2 → 3 及模块/常量/函数说明；`take_score_call` 原账读入改为「缺文件 = 0；文件存在但缺键/布尔/小数/负数/非对象 = 不可读拒评」（原读法缺键当 0、`int()` 截小数、负数放行）。`run_score` 调用参数、`cite_score`、`SCORE_KEYS`、分母/四表引用零改动。 |
| `tests/test_eng_loop2_play_ops.py` | 假 ssh 增两项可选行为：`real_control_socket`（同 OpenSSH `muxserver_listen`：在 `<ControlPath>.<16 位随机>` 上真实 bind 本机 AF_UNIX 后改名，放不下即 rc 255 + `unix_listener … too long` 原样报错）、`exit_keeps_socket`；`DiagTests` 的 setUp 抽成 `DiagTestBase`（所有诊断测试改为真实 bind + 独立短父目录，测试结束连同残留清掉）；新增 `DiagControlPathTests` 7 例（`long_root = True`：执行检出放进加长目录，旧式路径带后缀 ≥ 125 B）。 |
| `tests/test_eng_loop2_summarize_ops.py` | 评分替身增 `STUB_SCORE_NO_OUT`（失败且无输出）；R1-4 用例改为按现行常量 N（N+1 个归档 → N 次、第 N+1 拒）；新增 AC-10 修订 7 用例 5 例。 |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md` | 第 0.4 表「正式归档零模型回放」行、第 12 节 OPS 增量段与评分句：≤ 2 → 全批实际调用总上限 ≤ 3（AC-10 修订 7）及其口径。 |
| `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` | 「现行 SUB:3」节首加本轮增量说明（SUB:3 已用尽、本修复不使其可再执行；短私有 ControlPath 的位置/核验/释放/指针）；工具表第 7 步加「释放本次私有 ControlPath 目录」。附录（工具抽取的 bash/python 块）零改动。 |
| `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md` | **零 diff**：全文无评分上限或诊断 ControlPath 的现行说明（第 266 行「第 12 节评分额度…未改」是该轮历史陈述），无需改。 |
| 本文件第 14 节、`docs/evidence/P1-ENG-LOOP-002-score-diag-fix-focused.log`、`docs/current-status.md` | 证据与交接。 |

闭集外零 diff：`operator_web.py`（含呈现）与其测试、`tests/test_loop2_isolation.py`、`.gitignore`、`runtime/`、`controller/`、`Assets/`、`config/`（含部署 16 路径清单）、`tools/eng_loop2/analyze_play.py`、`tools/language_serve.py`/`tools/language_latency.py`、`tools/eng_jet/`、基础设施（cmd: `git diff --stat 1e1c3b2..HEAD -- tools/eng_loop2/operator_web.py tests/test_eng_loop2_operator_web.py tests/test_loop2_isolation.py .gitignore runtime controller Assets config tools/eng_loop2/analyze_play.py tools/language_serve.py tools/language_latency.py tools/eng_jet tools/check_docs.py tools/check_role_writes.py AGENTS.md CLAUDE.md docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md` 为空）。

### 14.2 AC-10 修订 7（评分全批实际调用总上限 3）落点与证据

| 合同点 | 落点 | 证据（机读指针） |
|---|---|---|
| 三允许、第 4 次实际调用在调用前拒（`S-ENVELOPE`、非 0、账不超 3） | `FORMAL_SCORE_LIMIT = 3`；`take_score_call` 先核后扣 | test: `tests/test_eng_loop2_summarize_ops.py::ScoringTests.test_ac10_r7_three_archives_scored_fourth_call_refused_before_call`（4 个有归档尝试 → 3 次调用、账 1/3→3/3、第 4 次 `S-ENVELOPE … (used 3, +1)`、无 `score.json`、rc 3）；test: `…::test_ac10_r7_three_archives_all_scored_exit_zero`（三归档全评、rc 0） |
| 成功/失败共账、调用前扣次、没有免费重评、跨摘要共账 | 原 `take_score_call` 先写账再调用（未改） | test: `…::test_ac10_r7_failed_calls_consume_and_no_free_rescore`（三次失败且无输出 → 已扣 3；换摘要重评 0 次调用、全部 `S-ENVELOPE`） |
| 原账继承不重置（已用 2 只剩 1） | 持久键 `score-ledger.json`/`formal_score_calls` 原样 | test: `…::test_ac10_r7_inherited_ledger_is_not_reset` |
| 已有输出只引用、不调用不计；原账不可读拒评 | `run_score` 已有输出分支（未改）；原账读入收紧 | test: `…::test_ac10_r7_existing_output_cited_not_counted_and_bad_ledger_refused`（含 `{broken`/`{}`/`true`/`1.5`/`-5`/`[2]` 六种坏账） |
| 诊断不评分 | 未改 | test: `…::test_formal_without_archive_and_diagnostic_never_score`（既有） |
| 三页相关现行说明 | play-ops 三处；诊断页无评分上限说明（只写诊断不评分，未改）；mini-prep 零 diff | artifact: `docs/evidence/P1-ENG-LOOP-002-play-ops.md`（第 0.4 表、第 12 节） |

R1-4 原用例 `test_r1_4_formal_score_calls_are_guarded_before_each_call` 按修订 7 改为随现行常量（N+1 归档 → N 次），修前（N=2）与修后（N=3）都通过；它不是本轮的修前红证据。

### 14.3 AC-10 修订 8（DIAG-CONTROL-1）落点与证据

**短私有目录（实现写明的口径）**：

- **位置**：父目录缺省 `tempfile.gettempdir()`（macOS 为本用户私有 `$TMPDIR`，本机 `/var/folders/jg/…/T`，48 B）；子目录 `tempfile.mkdtemp(prefix="el2d-")`。本机实际 ControlPath 形如 `$TMPDIR/el2d-XXXXXXXX/d1`，65 B，带 OpenSSH 17 B 后缀 82 B ≤ 103 B（余量 21 B）。不改全局 SSH 配置、仓库路径、诊断/正式输出根、dirty 判据与双来源放行门。
- **权限/归属/唯一性**：`mkdtemp` 原子新建（已存在即换名，不复用），建后 `lstat` 核是目录、非链接、`uid == getuid()`、无组/他人权限（0700）；每次 `DiagnosticRun` 新建一个，d1、d2 用目录内独立名字 `d1`/`d2`；主连接尝试前 `verify()` 复核仍为本用户 0700 私有目录（改权限/换属主/非目录即 `DIAG_FAULT control_dir_unsafe`、缺失即 `DIAG_FAULT control_dir_missing`，均不占主连接次数；不比较 dev/inode，同用户同权限的目录替换不在判据内，按复核 R1@OpsScoreDiagK1K4 §3 OSD-R1-1 的「本进程拥有的短私有临时目录」归属域读法）。
- **有效性**：先按「父目录 + 前缀 + 8 位 + 最长名字」预核，过长不建目录；建后对每个名字按 `os.fsencode` 编码后字节 + 17 核 `UNIX_SOCKET_PATH_CAPACITY − 1`，并在该目录内以同字节长度的探针名（`<name>.<16 位十六进制>`）**实际 bind 本机 AF_UNIX 后关闭并删除探针**。任一不成立 → 删掉刚建的空目录、`DIAG_REFUSED control_path_*`，此时尚未 `consume()`，不占任何受限维度。
- **同路径**：每条 `DiagConnection` 的 `self.cm` = 该名字的唯一路径；ControlMaster 创建（`ControlPath=`）、`-O check`、全部通道 `-S`、`-O exit` 均用它（继承 `SshUnit` 原调用，只改路径来源）。失效仍 `DIAG_FAULT control_socket_unavailable`，不隐式直连/不新认证/不重试；主连接成功、失败都按原账先计次。
- **生命周期**：占额前建立 → 两条主连接使用 → 收尾 `_close_connections` 关完主连接后 `_release_control`：先做一次 Air 读数（来源 `before control dir release`），再仅当目录为空才 `rmdir`；有任何残留（如主连接 `-O exit` 失败留下的套接字）不删、不复用，记 UNKNOWN（含路径与残留清单）。关闭本身异常未完成时也不删、记 UNKNOWN。
- **计量**：`air_reading` = 诊断根逐文件 + 待移入 runtime + 本目录各项 lstat 字节（套接字通常 0 B，照计）；粗账 `disk.air_source` 写明。
- **原流指针**：粗账 `control_dir`（路径、父目录、pid、建立时刻、模式、uid、容量/后缀、每个名字的路径与带后缀字节、探针 bind 结果、释放结果）；`ops-events.jsonl` 事件 `diag_control_dir`、`diag_control_dir_release`；`ssh/d1.tsv`/`d2.tsv` 的 `control_path` 行；`master_connections[].control_path`。

| 合同点 | 证据（机读指针） |
|---|---|
| 生产长诊断根下修前必失败、修后通过（生产入口 + 真实 bind） | test: `tests/test_eng_loop2_play_ops.py::DiagControlPathTests.test_diag_control_long_production_root_master_binds_real_unix_socket`（先以本机 AF_UNIX 实测旧式 `诊断根/ssh/cm-d1` 带后缀 bind 报 too long；再走 `play_ops.main --mode diagnostic diag`：修前 d1 `ssh_master_failed` rc 255 = SUB:3 原故障，修后两条主连接 rc 0、d1≠d2 同目录且在诊断根外、每条连接 master/check/通道/exit 同一路径且各恰一次 master、无 `-S` 以外的直连、收尾空目录已删、事件与 tally 指针齐、UNKNOWN 0） |
| 本机 AF_UNIX 实际 bind/关闭核短路径；生产缺省父目录；0700/本用户/跨批唯一；残留不删 | test: `…::test_diag_control_allocation_binds_af_unix_with_suffix_and_is_private_and_unique` |
| 无法建立安全短路径即拒启、未消耗 | test: `…::test_diag_no_safe_short_path_is_refused_before_consumption`（父目录过长 → `DIAG_REFUSED control_path_too_long`、`consumed=false`、除 `-G` 外 ssh 0、不留目录） |
| 目录被改权限 → 主连接尝试前故障、不计次 | test: `…::test_diag_unsafe_control_dir_is_fault_before_master_attempt` |
| 主连接失败计 1 次、无回退/重试/d2，空目录释放 | test: `…::test_diag_master_failure_counted_no_fallback_and_control_dir_released` |
| 套接字失效 → 故障、不新认证、无通道，释放 | test: `…::test_diag_socket_lost_is_fault_without_new_auth_and_released` |
| `-O exit` 后残留 → UNKNOWN、不删 | test: `…::test_diag_leftover_socket_after_exit_is_unknown_and_not_deleted` |
| 既有诊断行为（拒启、服务拒启计次、STOP1/Ctrl-C 封住、端到端一次 Play 与收尾）在真实 bind 下不变 | test: `tests/test_eng_loop2_play_ops.py::DiagTests`（全部改为真实 bind 运行） |

假 ssh 只提供「先在带后缀名上 bind 再改名」的有限行为与通道替身；路径长度另由测试进程内的本机 AF_UNIX bind 直接证明（上表前两行），不以假 ssh 成功作唯一证明。真实 OpenSSH 与 Jetson 未接触。

### 14.4 修前红 / 修后绿与 focused（原输出 `docs/evidence/P1-ENG-LOOP-002-score-diag-fix-focused.log`）

- **修前**：工具代码 = 派发基线（`5fff16a`，`tools/`/`tests/` 同 `1e1c3b2`）的 scratchpad 一次性检出，测试 = 本轮新增 12 例：`FAILED (failures=8, errors=4)`。行为红：长根 d1 `ssh_master_failed` rc 255（命名回归）、过长父目录未拒启而是 `DIAG_FAULT`、套接字失效用例无 `control_dir` 释放、评分只 2 次（三归档/四归档/失败扣次）、继承账 0 次、`{}` 坏账被当 0；4 个 error 是修前无 `DiagControlDir`/`DIAG_CONTROL_PARENT`/粗账 `control_dir`（新接口用例）。
- **修后**：同 12 例 `OK`。
- 四个 Ops 模块 focused（`python3 -m unittest tests.test_eng_loop2_play_ops tests.test_eng_loop2_operator_web tests.test_eng_loop2_summarize_ops tests.test_loop2_isolation`）：实现提交 `0112b4a` 干净工作树复跑 **156 例 `OK`**（144 + 12；439 s；日志末段）。开发期同树另跑一次亦 156 OK（未入日志）。

### 14.5 稳定条件②：engineering §6 窄修替代适用性（逐文件；**结论：不成立，不冒称稳定**）

§6 替代前提是「相对上一个已跑过停点全套的候选（`5218cc2`，`-ops-r1rework-tests.log`）只改具名文件，且不触及真实模型加载器、数据划分或对外指标路径」；同名提案「第四次诊断核清与操作流程修改路线」`:VALIDATION:7` 行要求实现能证明「完全不触对外指标路径」才可另报窄修适用性。

| 文件 | 真实模型加载器 | 数据划分 | 对外指标路径 | 判断 |
|---|---|---|---|---|
| `play_ops.py`（诊断 ControlPath） | 否（无 import/加载改动） | 否 | 否（诊断模式不评分、不进证据） | 单看可窄修 |
| `summarize_ops.py`（评分上限 2→3、原账读入收紧） | 否（`analyze_play` 零 diff，摘要进程不加载模型） | 否 | **是**：它决定正式摘要对第 3 个归档是否调用原评分并引用其四表；本停点被接受定为 K4（对外指标/评分调用资源边界） | 不满足「完全不触」 |
| 两份测试、三页文档 | — | — | — | 不单独决定 |

因此本合批候选**不能以 focused + 红绿替代停点全套**；`5218cc2` 之后 `tools/`、`tests/` 只有本轮改动（cmd: `git diff --stat 5218cc2..1e1c3b2 -- tools tests` 为空），但这不改变上表结论。SUB:1 三候选与 N-1 均已用尽，本轮没有全套额度，**未跑全套、不记全套通过、未自证四条件、不交 C8/R1**。下一步需要用户首签下节申请，再按接受落实后的合同跑一次全套并补齐四条件自证。

### 14.6 VALIDATION:7 申请清单（未签，各维度当前 0；不得先跑后补签）

申请信封标题：`P1-ENG-LOOP-002 评分诊断合批验证信封（OpsScoreDiagK1K4）`，标题 sha256 前 8 位 `42979c14`（`printf '%s' '<标题>' | shasum -a 256`；同法复算旧信封得 `9bac8fd0`）→ request_id `P1-ENG-LOOP-002:42979c14:SUB:1`。

| 字段 | 申请值 |
|---|---|
| 目的 / 覆盖 AC | `OpsScoreDiagK1K4` 停点全套一次（稳定条件②；AC-10 修订 7/8 与既有 Ops/AC 回归；基线失败与新增失败逐名分列，对照 `-ops-r1rework-tests.log` 16 项） |
| 执行机 / 解释器 | MacBook Air；系统 `python3`（与 SUB:1 三次、N-1 三次同口径）；不装包 |
| 命令 | `python3 -m unittest discover -s tests > docs/evidence/P1-ENG-LOOP-002-score-diag-fix-tests.log 2>&1; tail -n 3 docs/evidence/P1-ENG-LOOP-002-score-diag-fix-tests.log`（不带 `-v`；执行检出 = 候选提交、工作树干净） |
| 真实模型加载 | 本轮新增 12 例 = 0；既有部分每次全套内实际加载数 UNKNOWN（此前全套未插桩；不拿旧静态清单假定一致，以实际计入证据） |
| 本项正式评分 / 独立归档回放 | 0（新增 12 例与 Ops 四模块评分全用替身执行检出与临时根；不对正式/诊断归档调用评分、不回放、不写 `outputs/eng-loop2/` 或 `outputs/eng-loop/`）（§14.8 A） |
| 既有测试内数据使用 | **非 0**（全套补正撤回原「0（不读正式或旧真实归档）」）：既有测试按 §14.8 B 只读读取/枚举主树 `runtime/` 与 `outputs/eng-sft/P1-ENG-SFT-002/` 下已有归档，部分把真实字节复制进临时根；不改写/删除/移动源归档，不新增读取对象 |
| 每候选次数 / 最多候选数 | 每候选 1 次；最多 3 个候选（本候选 + 至多 2 次返工候选） |
| 墙钟 / 磁盘 | 每次 ≤ 15 min（上次 421 s，本轮新增约 35 s，诊断用例改真实 bind 后增量未实测）；证据日志 ≤ 2 MB（只限日志）；测试临时增长（`$TMPDIR` 下各测试临时目录、新 AF_UNIX 父目录、仓库树内短暂写入）由 §14.8 D 披露，逐例清理但**峰值不为 0、总峰值 UNKNOWN**，本申请不另设临时磁盘额度（§14.8 E） |
| 预览样图 / 人眼 | 不需要（`operator_web.py` 零 diff，SUB:2 本人两张一致记录按原读法携带） |
| 网络 / 设备 / Play / 正式 ID | 仅 127.0.0.1 回环与本机 AF_UNIX 临时套接字；SSH 0、板 0、Unity/Play 0、正式 scenario/session/run ID 0；下载/安装/5060/云 0 |
| 未核事实 | 16 项基线在本机今日是否逐名不变：UNKNOWN；真实模型加载数：UNKNOWN；全套 `$TMPDIR` 临时峰值与进程内存峰值：UNKNOWN（已知下界见 §14.8 D） |

**全套清单补正（2026-10-08，SUITE-LIST-1）**：上表「数据」「磁盘」两行已按 §14.8 改写；命令、解释器、次数、候选数、墙钟、日志上限等申请值不变。本节仍未签、各维度当前 0，须接受再核清后才呈首签。

推荐签（理由：评分调用路径属 K4，替代不成立；不跑全套则本合批无法成为稳定候选，`DIAG:RETRY:1` 与正式线都排在其通过消费之后）。备选：不签，则本候选停在进度态。

### 14.7 未核风险与已知限制

- 真实 OpenSSH 的 ControlMaster/`-O check`/`-O exit` 在新路径上未实跑（本机只证 AF_UNIX bind 与替身改名语义）；后缀长度 17 B 取自 OpenSSH `muxserver_listen` 与 SUB:3 原 stderr，若未来 OpenSSH 改后缀长度需重核。
- `$TMPDIR` 被用户环境改成很长路径时会拒启（fail-closed），不会自动换父目录。
- 主连接 `-O exit` 失败留下的套接字与目录按设计保留，需人工按 UNKNOWN 指针处理；工具不杀未知进程、不删未知套接字。
- 正式 `SshUnit` 路径不在本修复范围（§4 闭集明确不改正式动作域）：本轮复算本机 `~/TetheredDroneTracking/outputs/eng-loop2/P1-ENG-LOOP-002/ssh/cm-u1` 为 75 B、带 17 B 后缀 92 B ≤ 103 B（与 §13.3 的 92 B 一致，余量 11 B，只算长度、未实跑）；仓库若移到比现路径长 11 B 以上的位置，正式首用会同样失败。仅作风险记录，不提新待裁定。

### 14.8 全套清单补正（SUITE-LIST-1；轮次 `全套清单补正`，零消耗）

合同：同名提案「合批进度与全套清单核清」§2–4。被补正对象：§14.6（`P1-ENG-LOOP-002:42979c14:SUB:1`）。**方法**：只读源码 + `ls`/`stat`/`du`/`find` 元数据（2026-10-08，主树 `3bcc060`）；未运行任何测试、探测或解释器导入检查，未改代码/测试/工具/配置/归档。

**执行条件读法**：存在门按今日 `stat` 结果，执行时以实际为准。库门：系统 `python3` = `/opt/homebrew/bin/python3`（→ Cellar `python@3.14` 3.14.6），`/opt/homebrew/lib/python3.14/site-packages` 只列 `mlx`/`pip`/`wheel`、用户 site 空、`PYTHONPATH` 空 → **推断** Pillow/numpy/cv2/ultralytics 不可导入（未执行验证；与上次全套 8 个模块因 cv2/numpy 导入失败一致）。**次数读法**：下表「次数」为每次全套；信封上限再 ×3（每候选 1 次、最多 3 候选）。unittest 单进程顺序执行，仅 jet 回环与 Ops 替身用例内有子进程/线程。

#### A. 本项正式评分 / 独立归档回放：0（保留）

新增 12 例与 Ops 四模块（`test_eng_loop2_play_ops`/`_operator_web`/`_summarize_ops`/`test_loop2_isolation`）只用替身执行检出与临时根（只复制已跟踪的 `config/scenario.untethered.json` 与操作页文档）；不对正式或诊断归档调用评分、不回放、不写 `outputs/eng-loop2/`、`outputs/eng-loop/`。这只说明本项，不说明全套。

#### B. 既有测试内数据使用（撤回原「0（不读正式或旧真实归档）」）

B1 读取真实归档并复制字节进临时根：

| # | 具名测试 | 来源根 | 执行条件（今日） | 用途 | 次数 | 可得字节 / 峰值依据 |
|---|---|---|---|---|---|---|
| 1 | `tests/test_dist_data_driver.py::CrossValidationTest` 三例：`test_s2_cross_validation_invalidates_shifted_static_layout_and_reports_it`、`…_clips_projection_to_archived_viewport_domain`、`test_s2_partial_truth_absence_skips_missing_frames_without_masking_corruption`（`ArchiveS2Case._place_frames/_copy`） | `runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames`（1,537 项，du 51,604 kB）、`runtime/p1-detect-scouting/p1-detect-001-scout-1/truth`（705 项）、同单元 `scenario_config.json` 3,252 B、`runtime/scenario_config.p1-scene-004.hold.json` 2,537 B | setUp 门=两份已跟踪文件（在）；源帧非空（在）；不足 60 对另 skip（今日可凑 140） | 生产 S2 交叉验证金标 | 3 | 每例复制前 140 个有真值帧（jpg+json+truth）stat 累加 7,182,700 B，加已跟踪几何 364,830 B、default 3,257 B、快照 ≤3,252 B → 单例临时峰 ≈7.55 MB（`build_layout` 写出物 UNKNOWN）；累计复制 ≈22.7 MB；tearDown 清理 |
| 2 | 同类 `test_s2_m3_target_check_uses_center_ratio_without_static_pair_backfill` | `runtime/test-results/p1-m3-body-001-arm-a-trial-3-post-run/frames`（257 项，在）；`runtime/runs/p1-m3-body-001-arm-a-trial-3/`（不在） | 先复制 40 帧再因 m3 真值缺而 skip | 同上 | 1 | 40 帧 jpg+json 3,085,973 B 复制后 skip（skip ≠ 未读） |
| 3 | `tests/test_dist_data_round8.py::ScenarioBindingTest` 四例（`ArchiveCopyCase.copy/place_frame`） | scout-4 帧根（4,811 项）首帧、`runtime/p1-scene-004-scouting/p1-scene-004-scout-4/manifest.json` 633 B、provider 2,537 B；m3 post-run 首帧；rate 两单元首帧与 `scenario_config.json` | 门=provider 在 → 执行；`runtime/runs/p1-m3-body-001-arm-a-trial-3/scenario.json` 不在 → m3、ambiguous 两例在 copy2 处 ERROR（同上次两条 ERROR） | 场景绑定回归 | 4 | scout4 32,850 B；m3 77,218 B 后 ERROR；rate 112,818 B；ambiguous 77,218 B 后 ERROR；累计 300,104 B，单例峰 112,818 B |
| 4 | `tests/test_dist_data_inventory.py` 11 例（JpegDimension 2、EmptyBridge 1、MatchAssertion 2、InventoryRecord 4、Lineage 2；`InventoryFixture.setUp/_place`） | `runtime/frames.1b-diagnostic-hold` 首帧（31,042+1,118 B）；`test_distinct_bytes_stay_separate` 另取 `runtime/frames.qual3-leftover-hold` 首帧（25,704+1,107 B） | 门=两目录有帧、sidecar 在 | S1 清单金标 | 11 | 每例 ≤2 份副本，单例峰 ≤64,320 B；累计上界 707,520 B |
| 5 | `tests/test_eng_jet_relay.py::LoopbackTwoProcess::test_atomic_publish_order` | a7 帧根 `common.a7_frames_dir()`：数据根 `~/TetheredDroneTracking-full` 不在 → 回落主树 `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames`（6,337 项，du 155,168 kB） | 类门 `frame_0000000000.jpg` 在；回环端口门 | 中继回环 | 1 | 帧 0..24 共 658,994 B，写入桌面/板侧两份临时运行目录 ≈1.32 MB（RETAIN 128 不裁）+ 日志；mkdtemp + addCleanup rmtree |
| 6 | `tests/test_eng_jet_track_responder.py::LoopbackTrackWithDrop::test_analyze_track_return_and_disconnect` | 同 a7 | 类门 `frame_0000000040.jpg` 在 | 跟踪回环 | 1 | 帧 0..59 共 1,558,281 B ×2 份 ≈3.12 MB + 日志 |
| 7 | `tests/test_eng_jet_track_responder.py::ResponderInProcess` 四例（模块函数 `publish`） | 同 a7 | 类门 `frame_0000000012.jpg` 在 | 应答器 | 4 | 读帧 0..10 上界 349,468 B，副本同量级 |
| 8 | `tests/test_eng_jet_relay.py::DesktopNoBacklog`、`::DesktopStalePointer`（**无门**，a7 缺则 ERROR）、`::ReplayAndEcho` | 同 a7 | 前后两类门在 | 中继单元 | 3 | 帧 0（31,993+1,114 B）各读 1 次、临时发布 2–3 份；ReplayAndEcho 帧 10..12 共 81,076 B |

B2 只读源归档字节（无临时副本）：

| # | 具名测试 | 来源根 | 执行条件（今日） | 用途 | 次数 | 可得字节 / 峰值依据 |
|---|---|---|---|---|---|---|
| 9 | `tests/test_dist_data_driver.py` 模块导入时 `FORMAL_ROOT_SNAPSHOT = _formal_root_snapshot()` + `PreflightTest::test_tests_never_write_the_formal_artifact_root` | `runtime/dist-data`（256 文件，合计 3,222,868,612 B；最大 `splits/attempt-1/splits.json` 515,074,557 B） | **无门**，导入即执行（`test_dist_data_survey` 亦导入本模块，同进程缓存不重复） | 正式输出根写保护快照（逐文件 `read_bytes` 后 sha256） | 2 遍 | 读量 ≈6.45 GB/全套（本清单最大读量项，计入墙钟）；无临时副本；内存峰值 UNKNOWN，静态下界 ≥515,074,557 B 单缓冲 |
| 10 | `tests/test_dist_data_layout.py::RoadDataTest` 两例（`test_hash_equal_current_config_may_serve_as_byte_provider` 门=已跟踪 default；`test_unmatched_hash_reports_unavailable_without_crashing` 无门） | `roots.ROAD_DATA_PROVIDERS`：`runtime/**/road_data.json`、`runtime/test-results/**/road_data.json`、`config/road_data.json` | 门在/无门 | road_data 字节绑定 | 2 | 每例全树递归枚举 `runtime/`（今日 98,764 文件/363 目录，两模式各一遍）并对命中逐个 sha256：5 份 ×93,331 B ×2 模式 + config 93,331 B → 上界 1,026,641 B/例（前者可能提前返回） |
| 11 | `tests/test_dist_data_layout.py::RelocationTest::test_scene004_registers_three_phantoms`、`…_relocations_land_on_archived_positions` | `runtime/scenario_config.p1-scene-004.hold.json` | 方法门在 | 布局回归 | 2 | 2,537 B ×2 |
| 12 | `tests/test_dist_data_projection.py::…::test_real_archived_sidecar_projects` | `runtime/frames.qual3-leftover-hold`（8,193 项） | glob 非空 | 相机构造 | 1 | 列目录 + 读 1,107 B |
| 13 | `tests/test_rate3_protocol.py::Rate2ArchiveRegressionTests::test_archived_decision_a_recomputes_identically` | 相对 cwd 的 `runtime/rate-study/P1-M2-RATE-002-B2/decision_a.json`（3,077 B）与 `runtime/runs/<run_id>/` | 门在 → 执行；runs 不在 → ERROR（同上次） | 归档决策复算 | 1 | 3,077 B + 失败前探 runs |
| 14 | `tests/test_language_selector.py::FrozenReplayAssetTests::test_blind_and_prediction_sha_match_the_frozen_receipts` | `outputs/eng-sft/P1-ENG-SFT-002/data/eval.blind.jsonl` 112,096 B；`returned/sft-20260918T223245Z-bd1f5ebb/predictions/eval-adapter.jsonl` 339,567 B；`upload/frames` 首行帧 42,419 B（sha） | 类门两文件在；不需 Pillow | 冻结回放资产核对 | 1 | 三文件 494,082 B，sha+解析遍数未插桩（UNKNOWN），读量上界约 1.5 MB |
| 15 | `tests/test_eng_sft_cloud.py::…::test_real_frozen_set_still_matches_local_freeze_receipt` | `outputs/eng-sft/P1-ENG-SFT-002/receipts/freeze-receipt.json` 3,469 B（另哈希 8 个已跟踪文件） | 门在 | 冻结闭集核对 | 1 | 3,469 B |
| 16 | `tests/test_preflight_reanchor_env.py::SubprocessContractTest` 四例子进程（failure、absent config、success、stdout purity） | 主树 `runtime/` 四个活动桥文件 body_command 208/gimbal_command 339/tracking_observation 457/metrics 2,059 B，及 `runtime/runs` 子目录名 | 无门（指纹先于库导入） | 写入前后指纹 | 4 子进程 ×前后 2 | 24,504 B + 8 次列目录 |

B3 只枚举/元数据（不读内容）：`tests/test_dist_data_round4.py::RealArchiveClosureTest` 五例——setUp 门 `runtime/p1-scene-006/probe-baseline-vfov60/frames` 在；三例各对 `roots.ENUMERATION_ROOTS`（`runtime` 全树 + 已跟踪 `docs/evidence/P1-M3-BODY-001-1b`）`rglob("*.jpg")` 一遍（今日 45,802 jpg）；两例 glob `runtime/runs/*/m3_body_truth.jsonl`（今日只命中两个 frame-001 真值，非 arm-a → 两例 FAIL）；zero-unmatched 例 FAIL；三条 FAIL 同上次。内容字节 0，枚举 3 遍。另：`test_language_loop` 共享 runtime 拒写类与各 jet/selector/analyze 类门只做 `exists`/`is_file`/glob 元数据。

B4 今日门不满足 → skip、不读（门变化时转为读取，量另核）：`tests/test_analyze_m3_body.py::ArchivedRunLoopDomainTests` 4 例（`runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4` 与 `…-void-attempt-3-hold` 不在；在则每例 copytree 两目录，量 UNKNOWN）；`tests/test_dist_data_review2.py::A2SubtreeConsistencyTest` 5 例（`runtime/runs/rate20-calib/manifest.json` 不在）；`tests/test_dist_data_round8_followup.py::DefaultPremiseTest::test_real_archive_premise_is_resolvable` 与 `AmbiguityNotMaskedTest` 3 例（`runtime/runs/p1-m3-body-001-arm-a-trial-3/scenario.json` 不在；在则 `build_provider_index(PROJECT_ROOT)` 全仓扫描哈希，量 UNKNOWN）；`tests/test_dist_data_pixels.py::FailClosedTest` corrupt/truncated 两例与 `ArchiveFrameTest` 全类（Pillow 门先于 `require_archive`，推断 skip；有 Pillow 则复制 scout-3 前 2 帧 28,588/33,668 B 及旁车）；`tests/test_det_assoc_carrier.py` 两类（数据根不在 + 库门）；`test_det_assoc_tracker`/`test_eng_fast_replay` 库门、`test_eng_jet_bench::InjectionOnly` ultralytics 门、`test_trackers`/`test_track_loop` NanoTrack cv2 门（`runtime/models/nanotrack-v2` 模型在门后）、`test_language_selector::ReplayDemoTests`/`test_language_loop::PreviewRenderTests`/`test_survey_tool` Pillow 门（推断 skip）；8 个导入失败模块（`test_benchmark_reanchor`、`test_detector_scouting`、`test_rate2_protocol`、`test_rate3_difficulty_audit`、`test_rate_study`、`test_scene004_gate0_probe`、`test_scene004_scouting`、`test_scene006_probe`）用例体不执行。

C. 已跟踪文件（非归档、不计）：`tests/fixtures/`、`config/`、`docs/evidence/`（如场景几何、`P1-M3-BODY-001-1b` 副本、SFT-002/JET/ACQ 收据与账本、SCENE-006 证据）按版本控制字节读取或复制进临时根。

#### D. 临时目录与仓库树内短暂写入（含新 AF_UNIX 父目录）

- `$TMPDIR` = `/var/folders/jg/1yygvdgs6813xcxn23ml4vy40000gn/T/`（48 B）：全部 `TemporaryDirectory`/`mkdtemp`（B1 副本、Ops 替身执行检出与 git 仓库、jet `eng-jet-*` 等），逐例 cleanup/addCleanup。
- **新 AF_UNIX 父目录**：`tests/test_eng_loop2_play_ops.py::DiagTests` 12 例 + `::DiagControlPathTests` 7 例每例建 `$TMPDIR/c<随机>`（`TemporaryDirectory(prefix="c")`，结束连同残留删除）；其内生产代码 `mkdtemp` 出 `el2d-<8>` 子目录、套接字 `d1`/`d2` 与 `<name>.<16hex>` 探针（套接字 0 B，探针 bind 后即删）；`test_diag_control_allocation_binds_af_unix_with_suffix_and_is_private_and_unique` 用生产缺省父目录直接建两个 `$TMPDIR/el2d-*`（addCleanup rmtree）；`test_diag_no_safe_short_path_is_refused_before_consumption` 在 `c*` 内建 90 字符深目录；长根两例另在临时目录内建加长替身检出。
- **仓库树内短暂写入**（不在 `$TMPDIR`，`finally` 删除，进程被杀会残留）：`tests/test_m3_body_tools.py` 在主树 `runtime/` 写 `test-m3-anchor-tamper.json` 5 次（源 1,465 B）、`test-m3-geometry-tamper.json`/`test-m3-geometry-short.json` 各 1 次（源 364,830 B 的紧凑重写，≤ ≈365 KB）；`tests/test_scene006_trace_hash.py` 在 `tests/fixtures/` 写 `.tmp-mismatch.json`/`.tmp-wrong-schema.json`（源 1,652 B）。今日 `ls` 无残留。
- **峰值**：已知单例归档副本上界 ≈7.55 MB（B1-1）、jet 回环 ≈3.12 MB+日志；全套 `$TMPDIR` 总峰值 UNKNOWN（顺序执行、逐例清理，其余用例生成量未盘点，不拍数）；内存峰值 UNKNOWN，静态下界 ≥515 MB（B2-9）。

#### E. 申请维度与临时增长的覆盖关系

- 命令、解释器、每候选 1 次/最多 3 候选、每次 ≤15 min、日志 ≤2 MB 均不变；15 min 已覆盖上次实测 421 s（含 B2-9 读量）。
- §14.6「数据」改为两行：A=0；B=既有测试按本节只读使用已有归档，复制只进临时根，不改写/删除/移动源，不新增读取对象。
- 「磁盘」：日志上限只管日志；测试临时增长、读量、内存由 D 披露，**本申请不设额度**，UNKNOWN 不拍数。若要求为临时磁盘/读量/内存另设上限，属新增申请维度，交接受与用户裁定（不自扩）。
- 上次 16 项基线中与本清单直接相关的 6 项：round4 三 FAIL（B3）、round8 两 ERROR（B1-3）、Rate2Archive 一 ERROR（B2-13），均由 `runtime/runs/` 旧 M3/RATE 运行目录今日不在引起（今日 `runtime/runs/` 只有 `p1-eng-frame-001-play-1/-2`）；其余 10 项为导入失败与环境项。今日是否逐名不变仍 UNKNOWN。

## 15. 轮次 `签发全套执行`：已签 `42979c14:SUB:1` 停点全套与四条件自证（**合批候选 `OpsScoreDiagK1K4`；交 `C8@OpsScoreDiagK1K4`**）

- Dispatch-Id `P1-ENG-LOOP-002-签发全套执行-20261008T185356Z-0b91`；派发基线 `fd26962`（执行时 HEAD `e1db4b9`，两者间只有状态板/派发登记）。唯一合同：同名提案「全套与诊断签发落实」§2/§4；执行闭集本文件 §14.6、§14.8 A–E；签发来源 `docs/authorizations.md` 2026-10-08「用户按推荐签发新全套 42979c14:SUB:1 与新诊断 DIAG:RETRY:1」。
- 未做：SSH/板/Unity/Play/正式 ID/下载/安装/5060/云 0；本项正式评分与独立归档回放 0；源归档未改/未移；诊断绑定未改、`DIAG:RETRY:1` 未启动；本轮代码/测试零改动。

### 15.1 执行记录（`P1-ENG-LOOP-002:42979c14:SUB:1`，本候选 1/1；信封 3 候选中第 1 个）

- 执行检出：HEAD `e1db4b9`，工作树干净（`git status --short` 空）；相对代码候选 `0112b4a` 的 `tools`/`tests`/`config`/`controller`/`Assets`/两份操作页/`.gitignore` 零 diff（cmd: `git diff --stat 0112b4a..e1db4b9 -- tools tests config controller Assets docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md docs/evidence/P1-ENG-LOOP-002-play-ops.md .gitignore` 为空）。
- 解释器：MacBook Air 系统 `python3` = `/opt/homebrew/bin/python3`（3.14.6）；未装包、未设数据根、`PYTHONPATH` 空。
- 命令（§2 原样，不带 `-v`）：`python3 -m unittest discover -s tests > docs/evidence/P1-ENG-LOOP-002-score-diag-fix-tests.log 2>&1`，随后 `tail -n 3` 该日志。外层只套 `/usr/bin/time -l sh -c '<上述命令>' 2> <scratchpad>`（计时与资源，`time` 输出不进证据日志）。执行前做过一次与套件无关的本机 127.0.0.1/AF_UNIX bind 可用性预核（零模型、零归档，未计入套件）。
- 起止 `2026-10-08T18:55:27Z` → `19:02:49Z`；`/usr/bin/time` **442.26 s real**（≤ 900 s），user 140.26 s / sys 86.25 s；unittest 自报 438.868 s；子进程最大常驻内存 1,044,905,984 B；退出码 **1**；原输出 43,316 B（≤ 2 MB），原样保留于 artifact: `docs/evidence/P1-ENG-LOOP-002-score-diag-fix-tests.log`。
- 末 3 行回显为 AC-15 夹具计数的两行 stdout 与空行（stdout 缓冲在 stderr 之后落盘）；结果行在日志第 539/541 行：`Ran 2474 tests in 438.868s`、`FAILED (failures=3, errors=13, skipped=54)`（2462 + 本合批 12 = 2474；skipped 54 与上次同）。
- 真实模型加载数：**UNKNOWN**（未插桩；本合批 12 例与 Ops 四模块为 0；库门同 §14.8 读法，cv2/numpy 缺失使 8 模块导入失败、相关真实模型用例未执行）。
- 临时增长与清理：仓库树内短暂写入（`runtime/test-m3-*.json`、`tests/fixtures/.tmp-*`）跑后无残留；`$TMPDIR` 跑前/跑后列表对比多出 2 个**空目录** `tmpcei5jic2`、`tmpx0tatyf1`（各 64 B 目录项、内容 0 B、mtime 均 `18:56:00Z`，落在全套窗口内），归属哪个测试**未核（UNKNOWN）**，未删除、未改动；`el2d-*` 与 `c*` AF_UNIX 父目录跑后 0 个。`$TMPDIR` 总峰值与读量未测（UNKNOWN，§2 不设数值上限）。无强制中止。
- 未出现：闭集外读取对象、网络外连、SSH 调用（替身除外）、`outputs/eng-loop2/` 或 `outputs/eng-loop/` 写入。

### 15.2 与 `-ops-r1rework-tests.log` 16 项历史失败逐名对照

方法：cmd: `grep -E '^(FAIL|ERROR):' <log> | sort` 两份后 `comm`；两侧各 16 行，`comm -23`、`comm -13` 均空。

| 类别 | 项（本次结果） | 归因依据（本次日志原文） |
|---|---|---|
| **本次仍现（16/16）** | 导入失败 8：`test_benchmark_reanchor`（numpy）、`test_detector_scouting`、`test_rate2_protocol`、`test_rate3_difficulty_audit`、`test_rate_study`、`test_scene004_gate0_probe`、`test_scene004_scouting`、`test_scene006_probe`（cv2） | `ModuleNotFoundError: No module named 'cv2'`/`'numpy'`（系统 `python3` 库门，§14.8 B4） |
| | 库门 ERROR 2：`test_eng_jet_bench.InjectionOnly.test_rect_engine_imgsz_override_only_in_harness`（numpy）、`test_rate3_protocol.Rate3GuardTests.test_rate3_reanchor_clock_mismatch_raises_defensively`（cv2） | 同上 `ModuleNotFoundError` |
| | 旧 runs 工件缺失 ERROR 3：`test_dist_data_round8.ScenarioBindingTest` 的 `test_ambiguous_manifest_hard_fails_without_parent_fallback`、`test_m3_armA_family_binds_via_run_snapshot`；`test_rate3_protocol.Rate2ArchiveRegressionTests.test_archived_decision_a_recomputes_identically` | `FileNotFoundError: …/runtime/runs/p1-m3-body-001-arm-a-trial-3/scenario.json`（两条）；`FileNotFoundError: … 'runtime/runs/rs2-r20-follow-1/manifest.json'` |
| | 旧 runs 真值缺失 FAIL 2：`test_dist_data_round4.RealArchiveClosureTest` 的 `test_arm_a_truth_patterns_cover_exactly_five_files`、`test_void_run_truth_pattern_matches_exactly_one_file` | 断言 `[] != ['runtime/runs/p1-m3-body-001-arm-a-trial-…jsonl']`：glob 命中为空 |
| | **zero-unmatched FAIL 1**：`test_dist_data_round4.RealArchiveClosureTest.test_zero_unmatched_and_zero_multi_matched_jpg` | **不归为旧 runs 缺失**（按同名提案「全套清单再核清」限缩段）：断言首报 `runtime/frames/frame_0000001324.jpg` 等 5 条、`zero-match 1490`，即主树 `runtime/` 全树 jpg 按图像模式枚举后有 1490 张无匹配模式（首报均在当前活动帧目录 `runtime/frames/`，该目录今日 257 项、mtime `2026-10-04`）；与 `-ops-r1rework-tests.log`、`-ops-c6rework-tests.log` 首报 5 条与计数 1490 逐字相同。本合批对 `tests/test_dist_data_round4.py`、`roots` 枚举模式与 `runtime/` 零改动，故判为既有运行时树状态项、与本增量无关；不签更深根因（哪些运行留下这 1490 张及应否登记模式未核） |
| 未再出现 / 未执行 | 0 | — |
| **新增失败** | **0** | 本合批 12 例（`DiagControlPathTests` 7 例、`ScoringTests.test_ac10_r7_*` 5 例）与 Ops 四模块全部不在失败列表；Ops 测试文件无 skip 装饰器，且总 skipped 54 与上次相同 → 已执行且通过 |

结论：本候选全套不绿，但不绿项 16/16 与历史逐名相同、归因均在本增量之外；**新增失败 0**，无闭集外/Ops 相关/无法归因的新失败，无需修复或返工候选。信封余量：本候选 0 次，返工候选至多 2 次（各 1 次）未用。

### 15.3 稳定候选四条件自证（workflow §4.3.1；候选代码 `0112b4a`，本节所在提交为证据候选提交）

**完整候选 diff**：
- 相对上一个已跑停点全套且 R2 `PASS` 的候选 `5218cc2`：cmd: `git diff 5218cc2..0112b4a -- tools tests docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md docs/evidence/P1-ENG-LOOP-002-play-ops.md`（6 文件，+527/−43：`tools/eng_loop2/play_ops.py`、`tools/eng_loop2/summarize_ops.py`、`tests/test_eng_loop2_play_ops.py`、`tests/test_eng_loop2_summarize_ops.py`、两份操作页）；逐文件说明见 §14.1。`0112b4a..e1db4b9` 上述路径零 diff。
- 禁改路径 cmd: `git diff --stat 5218cc2..e1db4b9 -- tools/eng_loop2/operator_web.py tests/test_eng_loop2_operator_web.py tests/test_loop2_isolation.py .gitignore controller Assets config tools/eng_loop2/analyze_play.py tools/language_serve.py tools/language_latency.py tools/eng_jet tools/eng_loop2/llama_adapter.py tools/eng_loop2/deploy_digest.py tools/eng_loop2/__init__.py` 为空；`operator_web.py` blob 仍 `13db5f1…`。

| 条件 | 自证 | 证据指针 |
|---|---|---|
| 1 范围与接口冻结 | 只在「SUB3核清与评分上限落实」§4 修改闭集内落实 DIAG-CONTROL-1 与 AC-10 修订 7/8；本轮零代码改动；无新待裁定；本候选后不再改 PLAY_GOVERNING/操作页 | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#14.1`；cmd: `git diff --stat 5218cc2..0112b4a`；cmd: 上列禁改路径 `git diff --stat`（空） |
| 2 相称测试 | 已签 SUB:1 停点全套 1 次（2474 例，新增失败 0，16 项历史失败逐名同、归因见 15.2）；12 例修前红/修后绿与四模块 focused 156 OK（§14.4） | artifact: `docs/evidence/P1-ENG-LOOP-002-score-diag-fix-tests.log`；artifact: `docs/evidence/P1-ENG-LOOP-002-score-diag-fix-focused.log`；artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#15.2`；cmd: `python3 -m unittest discover -s tests` |
| 3 已知 Unity 失败/人眼义务 | 无 Unity 运行、无已知 Unity 失败；呈现路径 `operator_web.py` 零 diff，SUB:2 本人两张一致记录按原读法携带（是否充分由接受判读，实现不自称复用） | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#5.1`；cmd: `git rev-parse 0112b4a:tools/eng_loop2/operator_web.py` |
| 4 复核入口/状态/候选/风险 | 复核入口 `docs/reviews/P1-ENG-LOOP-002.md`（新范围由复核角色开节）；状态板本项交接行已更新为 Acceptance `C8@OpsScoreDiagK1K4`；未验证风险见 15.4 与 §14.7 | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#15.4`；artifact: `docs/current-status.md#Active handoffs` |

**逐 AC 指针（本合批）**：

| AC | 证据 | 后置/未运行 |
|---|---|---|
| AC-10 修订 7（评分全批实际调用 ≤ 3） | test: `tests/test_eng_loop2_summarize_ops.py::ScoringTests.test_ac10_r7_three_archives_scored_fourth_call_refused_before_call`；test: `…::test_ac10_r7_three_archives_all_scored_exit_zero`；test: `…::test_ac10_r7_failed_calls_consume_and_no_free_rescore`；test: `…::test_ac10_r7_inherited_ledger_is_not_reset`；test: `…::test_ac10_r7_existing_output_cited_not_counted_and_bad_ledger_refused`；artifact: `#14.2` | 正式归档评分 NOT_RUN |
| AC-10 修订 8（DIAG-CONTROL-1 短私有 ControlPath） | test: `tests/test_eng_loop2_play_ops.py::DiagControlPathTests`（7 例，含 `test_diag_control_long_production_root_master_binds_real_unix_socket`、`test_diag_no_safe_short_path_is_refused_before_consumption`）；test: `tests/test_eng_loop2_play_ops.py::DiagTests`（真实 bind 下回归）；artifact: `#14.3` | 真实 OpenSSH/板 未运行；`DIAG:RETRY:1` 未放行 |
| AC-13（停点测试/替代） | artifact: `docs/evidence/P1-ENG-LOOP-002-score-diag-fix-tests.log`；artifact: `#15.2`；artifact: `#14.5`（§6 替代不成立，故跑全套） | — |
| 既有 Ops/AC 回归（AC-5/8/10 修订 3/4、AC-14/18 本地部分） | 全套中 Ops 四模块全过（同 15.2 新增失败 0）；指针沿 §7.0 逐 AC 表 | 同 §7.0 后置项 |

### 15.4 未在真实条件下验证的风险（增补 §8、§11.5、§12.5、§14.7）

- 真实 OpenSSH ControlMaster/`-O check`/`-O exit` 在新短私有路径上未实跑，Jetson 未接触；`DIAG:RETRY:1` 执行前提（通过消费、绑定、现场核、本人新窗口）均未齐。
- 评分 ≤ 3 只经替身归档验证，正式三剧本归档评分 NOT_RUN；正式 `SshUnit` 路径余量 11 B 的风险照 §14.7。
- 全套 `$TMPDIR` 遗留 2 个空目录（15.1），归属未核；模型加载数、`$TMPDIR` 峰值、读量 UNKNOWN。
- 16 项历史失败中 zero-unmatched 的更深根因（1490 张未匹配帧来源）未核，仅确认与本增量无关且逐字不变。
- 真实板/Unity 闭环、AC-14/15/18 与 AC-16 正式板端仍 NOT_RUN；本节不构成独立复核或 DONE。

## 16. 轮次 `C8退回纠正`：C8@OpsScoreDiagK1K4 首次退回 C8-1 的文档纠正（**零消耗；仅操作页文字；交下一实际 C 轮**）

- Dispatch-Id `P1-ENG-LOOP-002-C8退回纠正-20261008T191546Z-376a`；派发基线 `658dcf0`。唯一合同：同名提案「C8@OpsScoreDiagK1K4核对」§4（C8-1）与 §5。
- 纠正：`docs/evidence/P1-ENG-LOOP-002-play-ops.md` §12「OPS 增量」段原短语「原账继承不重置，账本缺失/不可读/计数非法即拒评」改为「账本文件不存在时首次从 0 建立；已存在的账本不可读/缺计数键/计数非法即拒评，原账继承不重置」（§4 给定读法逐字）。核对依据：`tools/eng_loop2/summarize_ops.py::take_score_call` 现行为（文件不存在 → `formal_score_calls` 从 0 起；存在但非对象/缺键/布尔/非整数/负数 → `S-ENVELOPE` 拒评），与 §14.1/§14.2 原说明一致，二者无需改。同页其他位置、诊断页与本文件其余小节无同类相反短语（cmd: `grep -n 拒评` 三文件）。
- 未做：代码/测试/工具/配置零改动；未运行测试、全套、探测或任何套件外预核；SSH/板/Unity/Play/加载模型/回放/下载/装包 0；未删旧账、未重置计数，N=3、原键、原评分函数/采样、诊断绑定不变；`DIAG:RETRY:1` 未启动。
- 四条件影响：候选代码仍 `0112b4a`（`tools`/`tests` 相对其零 diff），§15.2 全套结果与 §15.3 条件 1–3 原样携带；PLAY_GOVERNING 中仅 `play-ops.md` 本行文字变化（下一 R1 完整 diff 须含之）。纯文字纠正不构成真实返工候选，不重跑全套；全套信封本候选 0、返工候选至多 2 次未用，均不变。§15.4 风险与 C8 §3 四项披露（两空目录 UNKNOWN、套件外预核越界记账等）原样保留。

## 17. 轮次 `诊断绑定方案`：`P1-ENG-LOOP-002:DIAG:RETRY:1` 新入口绑定方案与 OSD-R1-1 逐字补丁（**零消耗；仅方案 + 逐字文字补丁；交接受具名合同答复**）

- Dispatch-Id `P1-ENG-LOOP-002-诊断绑定方案-20261008T194042Z-cd71`；派发基线 `c3d6b5e`。唯一合同：同名提案「R1通过消费与新诊断前提盘点」§2–3；补丁原文：`docs/reviews/P1-ENG-LOOP-002.md`「R1@OpsScoreDiagK1K4」§3 OSD-R1-1；资源合同：同名提案「全套与诊断签发落实」§3–4、「SUB3核清与评分上限落实」§5。
- 未做：绑定代码、常量、旧许可名均未改；未运行测试/全套/探测/加载/回放；SSH/板/Unity/Play/下载/装包 0；未写任何机读放行行。`DIAG:RETRY:1` 未启动、未放行，consumed=none。

### 17.1 OSD-R1-1 应用（CLASS_3，不开轮）

- `tools/eng_loop2/play_ops.py::DiagControlDir.verify` 仅 docstring 一行按复核逐字替换为「主连接尝试前复核目录仍为本用户 0700 私有目录（改权限/换属主/非目录/缺失即拒绝连接；不比较 dev/inode，同用户同权限的目录替换不在判据内）。」；判据、数字、执行顺序零改（`git diff` 仅该 1 行）。
- 本文件 §14.3「权限/归属/唯一性」条同步为同一归属域读法（改权限/换属主/非目录 → `control_dir_unsafe`、缺失 → `control_dir_missing`，不比较 dev/inode）。三操作页与 `play-ops.md` 无同类相反短语（cmd: `grep -n 被改权限/替换\|被替换`，0 命中）。
- **PG 影响（须知）**：本行使 `git diff 539fd6d..HEAD -- tools/` 非空，故正式与诊断 `release_gate` 在下一次通过前都会 `play_governing_changed_after_pass` 拒启（fail-closed，与「R1通过消费…」§2「后续 CLASS_3/入口适配会改变 PG」一致）。建议并入下方绑定候选的完整 PG diff 由同一 R 轮覆盖，不单独开轮。`play_ops.py` 不在 `config/p1-eng-loop-002-board-deploy.json` 部署闭集内，板端部署摘要不受影响。

### 17.2 现状读数（只读代码与本机已有粗账；方案的出发点）

| 位置 | 现状 | 对新入口的问题 |
|---|---|---|
| `DIAG_REQUEST_ID` / `stage_diag` / argparse | 唯一常量 = 旧 `…:9bac8fd0:SUB:3`，`--request-id` 须逐字等于它 | 新 request_id 无入口；只改常量 = 改名旧许可（禁止） |
| `DIAG_LEDGER_HITS` → `release_gate(ledger_hits=…)` | 账本全文两段子串独立命中（旧 SUB:1/2/3 标题 + 旧 id） | 不核两者属同一条目；新条目无绑定 |
| `DIAG_RELEASE_LINE` / `preflight` | 只认 `sub3_release: <40 sha>`，值 ∈ 行集合且 = 门核 `passed` | 旧行只属耗尽 SUB:3 与旧通过代码；新许可无键 |
| `_refuse_if_consumed` | 扫 `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/*/ops-diagnostic-ledger.json`，同 id 且 `consumed` 真即拒 | **读不出/非 JSON 被 `read_json(...) or {}` 当成未消耗（fail-open）**；非对象 JSON 会抛未捕获异常而非干净拒启；一次性只依赖未跟踪的 `outputs/` |
| `DiagAccount` / NOTES / 摘要记录 / 拒启文案 | `request_id` 固定写旧 id；文案「未消耗 SUB:3 受限维度」 | 新整批粗账须写新 id |
| `--playbook` | P1/P2/P3 任选 | 新签发 P1 固定 |
| `DIAG_LIMITS` | master 2 / serve 1 / fault 0 / plays 1 / sessions 1 / measure 1 / k_receipt 1 / 2700 s / Air 250,000,000 B / 板 200,000,000 B | 与「全套与诊断签发落实」§3 已签维度逐项相同，**无需改数** |

本机现有粗账：仅 `20261008T155230Z/ops-diagnostic-ledger.json`（`request_id`=旧 SUB:3，`consumed`=true）；`20261007T*` 四个旧手工诊断根无粗账文件。

### 17.3 绑定方案（BIND-1…6；均待接受具名答复，未实现）

- **BIND-1 条目闭表（新 request_id ↔ 唯一已签条目）**：新增诊断专用闭表 `DIAG_ENTRIES`（`request_id` → 冻结 `DiagEntry(status, ledger_title, release_key, playbooks)`），只两项：
  - `P1-ENG-LOOP-002:9bac8fd0:SUB:3`：`status=exhausted`，原标题/原 `sub3_release` 键原样保留作历史；`DIAG_REQUEST_ID` 常量名与值不改、不改名。
  - `P1-ENG-LOOP-002:DIAG:RETRY:1`（新常量 `DIAG_RETRY1_REQUEST_ID`）：`status=signed`，`ledger_title` = 账本标题片段「用户按推荐签发新全套 42979c14:SUB:1 与新诊断 DIAG:RETRY:1」，`release_key=diag_release`，`playbooks=("P1",)`。
  - 限额沿用 `DIAG_LIMITS` 同一对象，不按条目复制数字；加一条静态断言测试核其逐维度等于已签值。
- **BIND-2 旧已用记录继续拒续 / 新整批一次**：`stage_diag` 在建任何根之前：id 不在闭表 → `DIAG_REFUSED request_id_unknown`；`exhausted` → `DIAG_REFUSED request_exhausted <id>`（代码级无条件，不依赖 `outputs/` 是否还在）；`--playbook` 不在条目 `playbooks` → `DIAG_REFUSED playbook_not_signed`。`signed` 条目再扫粗账（`__init__` 内、建根前，同现位置）：任一粗账读不出/非对象/`request_id` 非字符串 → `DIAG_REFUSED diag_ledger_unreadable <路径>`（**修补上表 fail-open**）；同 id 且 `consumed` 不是字面 `false` → `DIAG_REFUSED request_consumed`。其他 id 的粗账（含旧 SUB:3 已消耗账）不阻断新 id。新粗账 `request_id` = 条目 id，新增 `entry_binding`（id、账本标题行原文、`release_key`、放行行行号与值、`passed_candidate`、`rel`）；`consume()` 语义与「拒启不消耗、结束或失败即用尽」不变。
- **BIND-3 账本唯一条目绑定**：`release_gate` 与其 1.5 子串命中逻辑**零改**（正式路径不动），诊断传入条目的 `(ledger_title, request_id)`；`preflight` 另从发布引用 `git show <rel>:docs/authorizations.md` 读原文按 `## ` 切条目：标题含 `ledger_title` 的条目须恰 1 个（0 → `ledger_entry_missing`，>1 → `ledger_entry_ambiguous`），且该条目正文含反引号包住的完整 id 精确记号（`P1-ENG-LOOP-002:DIAG:RETRY:1` 后紧接反引号；`…:WINDOW` 等前缀扩展不算）→ 否则 `ledger_request_id_missing`；读取失败 → `ledger_unreadable`。限制：机器不识别用户后续撤回条目，由接受在写放行行时核。
- **BIND-4 新机读消费键（关联 request_id 与最新有效通过候选）**：格式 `diag_release: <request_id> <40 位小写 sha>`（行首可带列表记号/反引号，同 `MR`），即一行同时绑定许可与候选。只由未来接受在消费绑定候选有效通过轮后，于同名提案新具名节从复核文件最新有效 `passed_candidate` 行运行时解析、程序写入；实现/脚本不自签、本方案不写实际行。工具从 `<rel>:` 提案读取：读取失败 → `diag_release_unreadable`；无本 id 的严格匹配行 → `diag_release_missing`；有本 id 行但无一等于门核 `passed` → `diag_release_mismatch`；大写/短 sha/他 id/旧 `sub3_release:` 行一律不计。门核 `passed` 本身仍须是最新有效通过轮、为 `rel` 祖先、= HEAD、PG 与三操作单空 diff、全局 blocks/releases 与 `$DOCWT` 自检通过（`release_gate` 现有，零改）；一行匹配不替其他门，也不转正式 G4。
- **BIND-5 操作页/调用格式**：诊断页新增「现行 DIAG:RETRY:1」节（唯一命令 `.venv-yoloe/bin/python -m tools.eng_loop2.play_ops --docwt <文档检出> --mode diagnostic diag --request-id P1-ENG-LOOP-002:DIAG:RETRY:1 --playbook P1 --p2-object <red_car|B|C>`，执行前提按「全套与诊断签发落实」§3 列全，放行行格式示例写成占位符 `<…>`），原「现行 SUB:3」节改为历史/已耗尽说明（不删原文）；页首两条要点改指新节。拒启文案改为「未消耗 <request_id> 受限维度」。
- **BIND-6 待裁定 BIND-Q1（附录围栏块）**：附录 3 `serve-diag.sh` 的 `DIAG_FAULT SUB:3 allows start number 1 only` 与日志横幅「SUB:3」是板上脚本字面。**推荐 A：围栏块零改**（`extract_block` 读取内容不变、启动编号仅 1 的行为与新签「板服务启动 ≤ 1」一致），在诊断页注明该字面是历史标签、真实 id 以 Air 粗账/NOTES/事件为准；备选 B：改成不含 id 的中性字样（多一处板上输入变化，须进同一复核 diff）。

### 17.4 实际修改文件闭集（实现时；本轮未改）

| 文件 | 允许改动 | 明确不改 |
|---|---|---|
| `tools/eng_loop2/play_ops.py` | 诊断段：`DiagEntry`/`DIAG_ENTRIES`/`DIAG_RETRY1_REQUEST_ID`/新放行行正则；`DiagnosticRun.__init__`（条目解析、`_refuse_if_consumed` fail-closed）、`preflight`（BIND-3/4）、`DiagAccount.__init__`（收 `request_id`/`entry_binding`）、`run_offline_summary` 记录 id、`execute`/`stage_diag` 拒启文案与条目检查、diag 子命令 help；模块 docstring 第 28–29 行 | `release_gate`/`require_gate`/`require_g4`/`SshUnit`/正式各 stage、`DIAG_LIMITS` 数值、`DiagControlDir`/`DiagConnection`/`DiagServe`/收尾逻辑 |
| `tests/test_eng_loop2_play_ops.py` | `DiagTestBase` 改用新条目（提案行 `diag_release: <id> <passed>`、账本新标题 + 反引号 id）；`DiagTests` 现有拒启用例改断言新拒启记号；新增 `DiagBindingTests` | 其余测试类 |
| `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` | BIND-5 文字；BIND-Q1 选 A 时只加说明 | 附录围栏块（选 A 时） |
| 证据/状态 | 本文件新具名节、`docs/evidence/P1-ENG-LOOP-002-diag-binding-focused.log`、状态板 | 账本、复核、提案、implementation-status |

闭集外（越出先具名待裁定）：`summarize_ops.py`、`operator_web.py`、`analyze_play.py`、`controller/`、`config/`、`Assets/`、`.gitignore`、部署 16 路径、`play-ops.md`、mini-ops-prep、`tools/check_*.py`。`play_ops` 的全部导入者（`summarize_ops`、`operator_web`、两份测试与隔离测试）都在下述 focused 四模块内。

### 17.5 fail-closed 回归指针（计划用例名；修前须红）

`DiagBindingTests`：`test_sub3_refused_as_exhausted_even_without_any_ledger`（无根、ssh 0）；`test_unknown_request_id_refused`；`test_retry1_refuses_unsigned_playbooks`（P2/P3，建根前）；`test_old_sub3_consumed_ledger_does_not_block_retry1`；`test_retry1_own_consumed_ledger_refuses`（含 `consumed` 非布尔）；`test_unreadable_or_nonobject_ledger_refuses`；`test_release_missing_or_only_sub3_line_refuses`；`test_release_mismatch_refuses`（大写 sha、`rel` sha、他 id）；`test_release_proposal_unreadable_refuses`；`test_ledger_title_missing_duplicate_or_id_outside_entry_refuses`；`test_retry1_account_records_binding_and_signed_limits`；`test_contract_format_examples_are_not_release_lines`（扫提案与诊断页的 `diag_release: <` 示例）。另：`DiagTests` 端到端用例的「再次启动即拒」改用新 id 复核；`ReleaseGateTests`/正式路径用例零改照绿。每个拒启用例断言 rc 3、`consumed=false`、除 `-G` 外 ssh 0。

### 17.6 与本停点通过范围的关系、K 停点、相称验证与资源

- **通过范围**：`R1@OpsScoreDiagK1K4` 通过（`539fd6d`）只覆盖当时代码与操作单，已被消费；它是新候选的复核基线（上一有效 `passed_candidate`），不覆盖本方案改动。新候选相对 `539fd6d` 的 PG diff = 17.1 docstring 行 + 17.4 闭集改动，诊断与正式 `release_gate` 在新通过前都拒启。正式路径代码零 diff，其旧通过结论按惯例携带。
- **K 停点（建议，接受定）**：新增量停点 `OpsDiagBindK1K2`——K1：诊断入口/调用格式与 request_id/放行行协议；K2：一次性守账、拒启 fail-closed 等安全约束。不触 K3（模型决策/身份）、K4（数据/指标/评分）、K5。流程：实现窄修 → 四条件自证（本文件新节）→ 下一实际 C 轮 → 新鲜独立 R1；不预签豁免或轮号。
- **相称验证（推荐，零消耗）**：本机系统 `python3`，focused `python3 -m unittest tests.test_eng_loop2_play_ops tests.test_eng_loop2_operator_web tests.test_eng_loop2_summarize_ops tests.test_loop2_isolation`（零模型、仅 127.0.0.1/本机 AF_UNIX，上次约 200 s）写 `docs/evidence/P1-ENG-LOOP-002-diag-binding-focused.log`；17.5 用例修前红/修后绿各一次（测试保持候选版，工具退到 `539fd6d`）。SSH/板/Unity/Play/模型/回放/下载/装包 0。
- **停点全套**：推荐按 engineering §6 窄修替代、不跑全套——改动只在诊断模式函数，不触真实模型加载器、数据划分或对外指标/评分路径，`play_ops` 不在板部署闭集，全部导入者在 focused 内（区别于 §14.5：那次触及 K4 评分路径）。若接受或复核判替代不成立，须另列清单交用户签（机/解释器 Air 系统 `python3`；命令同 §14.6 形式、新日志名；每候选 1 次、候选数与墙钟/日志上限由用户定；模型加载 UNKNOWN 照旧列明；数据闭集同 §14.8；网络仅本机；SSH/板/Play 0），**不得挪用 `42979c14:SUB:1` 未用的 2 个返工候选**。
- **之后的顺序**：新候选通过并被接受消费 → 接受按 BIND-4 写 `diag_release:` 实际行 → 执行时现场核 → 用户本人新在线窗口（`…:DIAG:RETRY:1:WINDOW`）→ 才可执行一次。本节不改变任何已签额度。

## 18. 轮次 `诊断绑定实现`：停点 `OpsDiagBindK1K2`（BIND-1…6、BIND-Q1=A；AC-10 修订 9 / AC-13 修订 2）四条件自证（**零消耗；交接受下一实际 C 轮**）

- Dispatch-Id `P1-ENG-LOOP-002-诊断绑定实现-20261008T195247Z-a7f3`；派发基线 `6c74135`。唯一合同：同名提案「诊断绑定方案答复（2026-10-08，Acceptance）」§1–4；方案原文本文件 §17。
- 候选代码提交 = 主题以「P1-ENG-LOOP-002 诊断绑定实现：BIND-1…6 候选代码」开头的提交（cmd: `git log -1 --format=%H --grep '^P1-ENG-LOOP-002 诊断绑定实现：BIND-1…6 候选代码'`）；本节所在提交为证据提交（只加本节、验证日志与状态板，`tools`/`tests`/三操作单相对候选代码提交零 diff）。上一有效通过基线不手抄，按复核文件最后一行有效 `passed_candidate` 运行时解析（cmd: `python3 -c "import sys;sys.path.insert(0,'.');from tools.eng_loop2 import play_ops as o;print(o._last_key_line(open('docs/reviews/P1-ENG-LOOP-002.md',encoding='utf-8').read(),'passed_candidate')[1])"`）；验证日志页首记录了两者的原始 40 位值。
- 未做：真实 ssh（含 `ssh -G`）/接板/Unity/Play/真实模型加载/真实归档读取或回放/下载/安装/外网/正式 ID 均 0；未写账本、任何 `diag_release:` 实际行或其他机读放行行、复核、implementation-status、提案；`run_offline_summary` 只改记录的 request_id 值，摘要调用（独立进程 `summarize_ops --mode diagnostic`）与评分/算法零改；未挪用 `42979c14:SUB:1` 返工额度；未跑全套。`DIAG:RETRY:1` 未启动、未放行。

### 18.1 逐 BIND 落点（`tools/eng_loop2/play_ops.py` 诊断段）

| BIND | 落点 | 读法要点 |
|---|---|---|
| 1 条目闭表 | `DiagEntry`（frozen）、`DIAG_ENTRIES`（`MappingProxyType`，只两项）、`DIAG_RETRY1_REQUEST_ID` | 旧 `DIAG_REQUEST_ID`/`DIAG_LEDGER_HITS`/`DIAG_RELEASE_LINE` 名与值不改，注释标历史；旧条目 `exhausted`/`sub3_release`；新条目 `signed`、标题片段逐字取账本 10-08 标题、`diag_release`、`("P1",)`。`DIAG_LIMITS` 对象与数值零改（仅注释注明两条目同一对象）。 |
| 2 建根前拒启 / 守账 fail-closed | `diag_entry_for`（`stage_diag` 与 `DiagnosticRun.__init__` 各调用一次，均在建根前）；`DiagnosticRun._refuse_if_consumed` 重写 | 未知 id `request_id_unknown`、旧 id `request_exhausted`（无条件，不看 outputs）、P2/P3 `playbook_not_signed`，均 stderr、rc 3、不建根不写账。扫描域内任一粗账 `read_bytes`+UTF-8+`json.loads` 失败、非 dict、`request_id` 缺或非 str → `diag_ledger_unreadable <路径>`（**原 `web.read_json(...) or {}` fail-open 在本候选修复**）；同 id 仅 `consumed is False` 继续，否则 `request_consumed <id> 已于 <根> 用掉`。其他可读 id 不占次数。`consume()` 置位时点与「结束或失败即用尽」零改。 |
| 3 账本唯一条目 | `diag_ledger_binding`；`preflight` 在 `release_gate` 通过后从 `git show <rel>:docs/authorizations.md` 读取 | `release_gate` 函数零改，诊断传入 `(条目标题片段, 完整 id)` 作 1.5 命中；另按 `## ` 分条，标题含片段恰一条（0 `ledger_entry_missing`/多 `ledger_entry_ambiguous`），正文含 `` `<完整 id>` ``（否则 `ledger_request_id_missing`），读取失败 `ledger_unreadable`。 |
| 4 新机读键 | `DIAG_RELEASE_KEY_LINE`、`diag_release_binding` | 严格 `diag_release: <id> <40 位小写 sha>`（`MR` 行首规则）；须完整 id 逐字相等；无本 id 合法行 `diag_release_missing`、有但无值 = 门核 `passed` `diag_release_mismatch`、提案读取失败 `diag_release_unreadable`；不以 `rel` 代替 `passed`；其余门仍由 `release_gate` 全部承担。 |
| 2/5 身份记录 | `DiagAccount.__init__` 新增关键字 `request_id`/`entry_binding`；`diag_start` 事件、`NOTES.md` 页首、`play-record.json`、拒启文案用条目 id；新事件 `diag_entry_binding` | 粗账 `entry_binding` = id、status、标题片段、release_key、playbooks + 绑定后补 `ledger_title_line(_no)`、`release_line_no`/`release_value`、`passed_candidate`、`rel`。 |
| 5 调用/页面 | `stage_diag` 文档串、`diag` 子命令 help；诊断页新增「现行 DIAG:RETRY:1」节、原节改标题为「历史 SUB:3（原「现行 SUB:3」节，已耗尽…）」并加历史说明（原文保留）、页首两条要点改指新节 | 唯一命令固定 `--playbook P1`；放行行示例为占位符；`--p2-object` 只作既有冻结计划输入。 |
| 6 / Q1=A | 诊断页附录 3 标题改写并加说明块；围栏块零改 | 附录 0/1/2/3/4/5/7 经 `extract_block` 取出内容的 sha256 改前改后逐一相同（本机核对；cmd: 对 `DIAG_OPS_DOC` 各附录调用 `ops.extract_block` 求 sha256 比对）。 |

### 18.2 修改闭集核对与两处披露

- 相对上一有效通过基线的 PLAY_GOVERNING + 三操作单 diff 恰 3 路径：`tools/eng_loop2/play_ops.py`（含 §17.1 OSD-R1-1 docstring 一行 + 本节 BIND 改动）、`tests/test_eng_loop2_play_ops.py`、`docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`（cmd: `git diff --stat <BASE> <候选代码提交> -- controller/ Assets/ tools/ tests/ config/ ProjectSettings/ Packages/packages-lock.json docs/evidence/P1-ENG-LOOP-002-play-ops.md docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md`，+487/−44）。`release_gate`/`require_gate`/`require_g4`/`SshUnit`/正式各 stage、`DiagControlDir`/`DiagConnection`/`DiagServe`/收尾逻辑、`summarize_ops.py`、`operator_web.py`、`analyze_play.py`、`controller/`、`config/`、部署 16 路径、`play-ops.md`、mini-ops-prep、`tools/check_*.py` 零 diff。
- 测试文件 hunk：`DiagTestBase`、`DiagTests`、新增 `DiagBindingTests`（插在 `DiagControlPathTests` 之前），**另有一处闭集字面外的模块级常量** `RETRY1`/`RETRY1_TITLE`/`SUB3`（紧贴 `DiagTestBase` 之前，测试独立写出合同字面供两类共用）；其余测试类零 diff。**披露 1**：`DiagControlPathTests`（闭集外）继承 `DiagTestBase`，其代码零改，但经基类改为走新 id/新夹具，行为随之覆盖新入口（7 例全过）。
- **披露 2**：`DiagAccount` 的 `request_id` 关键字缺省保留旧 SUB:3 值，仅为闭集外 `DiagAccountTests`（直接构造并断言缺省 id）零改兼容；生产唯一构造点 `DiagnosticRun` 一律显式传条目 id（e2e 与 `test_retry1_account_records_binding_and_signed_limits` 断言粗账 id = 新 id）。另：`release_gate` 文档串仍写「诊断 = SUB:3 签发条目与完整 request_id」，因该函数列为明确不改而未动，属陈旧文字。

### 18.3 验证（原输出 `docs/evidence/P1-ENG-LOOP-002-diag-binding-focused.log`；本机系统 `python3` 3.14.6；未跑全套）

- **四模块 focused 一次**（候选代码提交、仓库根）：`python3 -m unittest tests.test_eng_loop2_play_ops tests.test_eng_loop2_operator_web tests.test_eng_loop2_summarize_ops tests.test_loop2_isolation` → 169 例 OK、rc 0、237 s（原 156 + 新 13）；`ReleaseGateTests` 与正式路径用例代码零改照绿。日志含 1 条既有替身子进程 ResourceWarning（同 R1 读法，不据此签全部子进程已退出）。
- **修前红 / 修后绿各一次**：临时副本 = `git archive <候选代码提交>`，红副本仅把 `tools/eng_loop2/play_ops.py` 换成基线 blob（测试保持候选版，两副本测试 sha256 相同，已记日志页首），各跑 `python3 -m unittest tests.test_eng_loop2_play_ops.DiagBindingTests` 一次；红 13 例 FAILED（failures=35 子例, errors=4）rc 1；绿 13 例 OK rc 0。副本已删除。按 §3 分类：

| 类别 | 用例 / 子例 | 基线结果与原因 |
|---|---|---|
| **fail-open 缺口（生产守账路径红证据）** | `test_unreadable_or_nonobject_ledger_refuses` 9 子例（截断、非 UTF-8、list、string、number、目录、缺 request_id、request_id=123/null）；`test_retry1_own_consumed_ledger_refuses` 中 consumed 缺键/null/0/空串 4 子例 | 粗账由生产 `DiagAccount` 写盘 + `consume()` 后在其字节上破坏；测试只桥身份（守账所保护的 id：基线 = 旧 id，经同一生产入口 `play_ops.main` 进入基线 `_refuse_if_consumed`）与构造参数。基线：7 子例吞坏账后**建新根进入 preflight**（断言 `diag_ledger_unreadable` 不在输出 → F）；list/string 2 子例在基线守账内抛未捕获 `AttributeError: 'list'/'str' object has no attribute 'get'`（测试捕获后判 F：不是干净拒启）；consumed 4 子例放过并建根（F）。均非 ImportError/新 API 缺失、非旧入口不认新 id 的提前拒启。 |
| 保持性（绿绿） | `test_unknown_request_id_refused` 6 子例；consumed=true/"false"/1 3 子例；`test_literal_false_own_ledger_passes_guard` | 基线原本即建根前拒 / 拒已用 / 字面 false 放行，分列为保持性覆盖，不计红证据。 |
| 新入口功能缺口（基线无新条目） | `test_sub3_refused_as_exhausted_even_without_any_ledger`（基线放旧 id 建根 → F，旧 id 硬拒缺口）、`test_retry1_refuses_unsigned_playbooks`、`test_old_sub3_consumed_ledger_does_not_block_retry1`、`test_release_missing_or_only_sub3_line_refuses`（10 子例）、`test_release_mismatch_refuses`、`test_release_proposal_unreadable_refuses`、`test_ledger_title_missing_duplicate_or_id_outside_entry_refuses`（6 子例 F + 纯函数部分 E）、`test_retry1_account_records_binding_and_signed_limits`（E）、`test_contract_format_examples_are_not_release_lines`（2 子例 E） | 基线 F 多因新 id 在旧入口被拒（`request_id must be exactly …SUB:3`）或其 stderr 未进入 stdout 断言；4 个 E 为新符号 `DIAG_ENTRIES`/`DIAG_RELEASE_KEY_LINE` 缺失。只说明新接口此前不存在，**不作为 fail-open 缺口的红证据**。 |

- 建根前拒启断言 rc 3、无新根/粗账、ssh 0；建根后前提拒启断言 rc 3、`consumed=false`、`used` 全 0、ssh 0；正向新条目（`root_exists` 替身，在板核处故障收尾）走过全部绑定前提并记完整 `entry_binding`，证明非一律拒启。
- 临时件：每例 `tempfile.TemporaryDirectory`（bare origin/执行检出/文档检出/假 ssh、curl、python）+ 短 ControlPath 父目录，用例结束清理；红绿副本位于会话 scratchpad，跑完删除。旧全套 16 项历史失败、两空目录归属、套件外预核 UNKNOWN 未重核；零模型替身不证明真实 OpenSSH/板/Unity 链路。

### 18.4 稳定候选四条件自证（workflow §4.3.1；按 AC-10 修订 9 / AC-13 修订 2）

**完整候选 diff**：cmd: `git diff <BASE> <候选代码提交> -- tools/eng_loop2/play_ops.py tests/test_eng_loop2_play_ops.py docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`（BASE 按上述命令运行时解析；3 文件 +487/−44）；`<候选代码提交>..HEAD` 在 PLAY_GOVERNING 与三操作单上零 diff（cmd: `git diff --stat <候选代码提交> HEAD -- tools tests docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md docs/evidence/P1-ENG-LOOP-002-play-ops.md docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md`）。

| 条件 | 自证 | 证据指针 |
|---|---|---|
| 1 范围与接口冻结 | 只在答复 §2 修改闭集内实现 BIND-1…6 与 Q1=A；接口（闭表、原因码、`diag_release:` 格式、`entry_binding` 键、唯一命令）冻结；闭集字面外仅测试模块级常量一处（18.2 披露）；无新待裁定 | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#18.1`、`#18.2`；cmd: 上列完整候选 diff 与 18.2 PG `git diff --stat` |
| 2 相称测试（AC-13 修订 2 窄修替代） | 四模块 focused 169 OK；修前红/修后绿各一次，fail-open 红证据来自生产守账路径；**未跑全套**（窄修替代依答复 §3；是否充分由复核判，不预判稳定条件② 满足、不记全套通过） | artifact: `docs/evidence/P1-ENG-LOOP-002-diag-binding-focused.log`；test: `tests.test_eng_loop2_play_ops.DiagBindingTests`（13 例）、`tests.test_eng_loop2_play_ops.DiagTests`（12 例，含 e2e 新 id 记录与再次启动 `request_consumed`）、`DiagControlPathTests`、`DiagAccountTests`、`ArchiveAndStopTests.test_modes_route_independently`；cmd: §18.3 两条命令 |
| 3 已知 Unity 失败/人眼义务 | 无 Unity 运行、无已知 Unity 失败；呈现/采集路径（`operator_web.py`、板输入围栏块）零改，无新增人眼要求，SUB:2 附议与 UNKNOWN 原样携带 | artifact: `#18.1`（BIND-6 行）；cmd: `git diff --stat <BASE> <候选代码提交> -- tools/eng_loop2/operator_web.py`（空） |
| 4 复核入口/状态/候选/风险 | 复核入口 `docs/reviews/P1-ENG-LOOP-002.md`（新停点首轮由复核角色开节，PG 非空）；状态板本项交接行已交 Acceptance 下一实际 C 轮；风险见 18.5 | artifact: `#18.5`；artifact: `docs/current-status.md#Active handoffs` |

**逐 AC 指针**：

| AC | 证据 | 后置/未运行 |
|---|---|---|
| AC-10 修订 9（BIND-1…6/Q1 绑定、旧 SUB:3 硬拒、坏粗账 fail-closed、同 id 仅字面 false、身份记录、不自签） | test: `tests.test_eng_loop2_play_ops.DiagBindingTests`；test: `tests.test_eng_loop2_play_ops.DiagTests`；artifact: `#18.1`、诊断页「现行 DIAG:RETRY:1」节、`docs/evidence/P1-ENG-LOOP-002-diag-binding-focused.log` | 真实 OpenSSH/板/Unity 未运行；`diag_release:` 实际行未写；DIAG:RETRY:1 未放行 |
| AC-13 修订 2（§2 闭集窄修 + focused + 修前红/修后绿替代此候选全套） | artifact: `#18.2`–`#18.4`、`docs/evidence/P1-ENG-LOOP-002-diag-binding-focused.log`；cmd: 完整候选 diff（BASE 运行时解析） | 未跑全套；旧全套 16 项历史失败等未重核；复核仍可判替代不足 |
| 携带：AC-10 修订 7/8、既有 Ops/AC | 四模块 focused 全过（含 `DiagControlPathTests` 7 例、`summarize_ops` 评分 ≤ 3 用例）；指针沿 §15.3 | 同 §15.3/§15.4 后置项 |

### 18.5 未在真实条件下验证的风险（增补 §15.4）

- 绑定只经临时 git/替身验证；真实发布引用上的账本/提案读取、真实 OpenSSH、板、Unity 闭环均未运行。`diag_release:` 实际行须由接受在消费本候选有效通过后程序写入，在此之前工具对真实仓库必拒（`release_gate` 先以 `play_governing_changed_after_pass` 等拒启；且发布引用上尚无本 id 的 `diag_release:` 行）。
- 守账承诺只限 `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/*/ops-diagnostic-ledger.json` 扫描域与旧 id 代码级硬拒：操作者删除新账后工具无法恢复耗用事实；扫描域外或不同仓库检出的粗账不可见（执行前由接受核新 id 未消耗）。本机现有旧 SUB:3 账（consumed=true）可读、身份明确，不阻断新 id；若本机将来出现读坏的粗账，新 id 将一律拒启直至人工处置（fail-closed 设计后果）。
- 账本条目按 `## ` 行切分，未识别围栏代码块内的同形行；用户后续撤回/否决条目不被机器识别（答复 BIND-3 已明示由接受写标记前核清）。
- 18.2 两处披露（测试模块级常量、`DiagAccount` 缺省 id）与 `release_gate` 文档串陈旧文字；本节不构成独立复核或 DONE。

## 19. 轮次 `C10退回纠正`：停点 `OpsDiagBindK1K2` 首退 C10-1 纠正（测试模块级三常量收回允许类闭集）四条件自证（**零消耗；交接受下一实际 C 轮**）

- Dispatch-Id `P1-ENG-LOOP-002-C10退回纠正-20261008T202817Z-3304`；派发基线 `0f1d853`（开工 HEAD `297ebaa`，其后仅派发登记）。唯一纠正入口：同名提案「C10@OpsDiagBindK1K2核对（2026-10-08，Acceptance）」§3 首条与 §4（C10-1）；合同仍为「诊断绑定方案答复」§1–4、AC-10 修订 9 / AC-13 修订 2。
- 纠正后候选代码提交 = 主题以「P1-ENG-LOOP-002 C10退回纠正：候选代码」开头的提交（cmd: `git log -1 --format=%H --grep '^P1-ENG-LOOP-002 C10退回纠正：候选代码'`）；本节所在提交为证据提交（只加本节、`docs/evidence/P1-ENG-LOOP-002-c10-rework-focused.log` 与状态板，PG/三操作单相对纠正候选代码提交零 diff）。§18 原候选代码提交（`git log -1 --format=%H --grep '^P1-ENG-LOOP-002 诊断绑定实现：BIND-1…6 候选代码'`）作为前版保留。上一有效通过基线仍按 §18 命令从复核文件最后一行有效 `passed_candidate` 运行时解析（本轮解析得 `539fd6d…`，不手抄作依据）。
- 未做：真实 ssh（含 `ssh -G`）/接板/Unity/Play/真实模型加载/真实归档读取或回放/下载/安装/外网/正式 ID 均 0；未改生产代码（`tools/eng_loop2/play_ops.py` blob `ec675f70…` 零改）、诊断页、闭集外任何测试类；未写账本、`diag_release:` 实际行或任何机读放行行、复核、implementation-status、提案；未挪用 `42979c14:SUB:1` 或任何余额；未跑全套；未重跑红绿。`DIAG:RETRY:1` 未放行、未启动。

### 19.1 改动（唯一功能路径 `tests/test_eng_loop2_play_ops.py`，+60/−60）

- 删除诊断节开头、`DiagTestBase` 之前的模块级 `RETRY1`/`RETRY1_TITLE`/`SUB3` 三定义；同字面值改为 `DiagTestBase` 类属性（类体首部，附 C10-1 说明注释）。
- 引用：`DiagTestBase`（`setUp` 3、`diag` 1）、`DiagTests`（4 个用例共 10）、`DiagBindingTests`（共 62）中裸名改 `self.<名>`；`DiagBindingTests.guard_id`（`@staticmethod`，无 `self`）改 `DiagTestBase.RETRY1`，装饰器与签名不变。合计 76 处引用 + 3 处定义；AST 核改后全文件已无裸名引用、无模块级定义。
- `DiagControlPathTests`、`DiagAccountTests` 及其他类代码零 diff；`DiagControlPathTests` 经继承获得同名类属性（与 §18.2 披露 1 同一既有继承关系，非新增修改）。
- 相对上一有效通过基线，测试文件全部 hunk 均落在 `DiagTestBase`/`DiagTests`/`DiagBindingTests` 行域内（唯一非类行为 `DiagBindingTests` 与 `DiagControlPathTests` 之间两行空行）；模块级越闭集定义已不存在。cmd: `git diff -U0 <BASE> <纠正候选代码提交> -- tests/test_eng_loop2_play_ops.py` 逐 hunk 对照 `ast` 类行域。

### 19.2 验证（原输出 `docs/evidence/P1-ENG-LOOP-002-c10-rework-focused.log`；本机系统 `python3` 3.14.6；未跑全套）

- **四模块 focused 一次（新测试树）**：`python3 -m unittest tests.test_eng_loop2_play_ops tests.test_eng_loop2_operator_web tests.test_eng_loop2_summarize_ops tests.test_loop2_isolation` → 169 例 OK、rc 0、238 s（例数与 §18.3 相同）。日志含 1 条既有替身子进程 ResourceWarning（读法同 §18.3，不据此签全部子进程已退出）。在工作树未提交态运行，日志页首所记改后测试 blob `43dea8b3…` 与提交内 blob 一致。
- **静态等价核（非测试）**：把新文件 AST 中 `self.X`/`DiagTestBase.X`（X∈三常量）还原为裸名、三类属性移回类前模块级后，与改前文件 `ast.dump` 逐字节相等（`ast_equal True`），三字面值相等（`literals_equal True`）；脚本全文与输出记在日志末节。改前文件 sha256 `ab671a45…` = §18 红绿日志所记候选测试 sha256。
- **携带与不携带**：
  - 可携带：§18.3 修前红（BASE 工具 + 候选测试，13 例 35F+4E rc 1）与修后绿（13 OK rc 0）的**行为结论**——生产 `play_ops.py` 与守账路径零改，红副本所换 BASE 工具 blob 不变，且测试名绑定以外的 AST 与红绿所用测试字节等价；§18.3 的类别划分（fail-open 生产守账红证据 / 保持性绿绿 / 新接口缺口 E/F 不计红）原样适用。
  - 不携带：§18.3 日志页首记录的测试 sha256 `ab671a45…` 只属前版候选，**不是新候选测试哈希**；新候选测试 blob `43dea8b3…`（sha256 `84ddf521…`），夹具字节变化仅限三常量所在行及 76 处名绑定行，夹具写出的文档/账本/放行行字面不变。红绿未对新测试树重跑（合同 §3 修前/修后各一次已用于 §18；本轮相称验证为新树 focused 一次 + 静态等价核）。
- 临时件：每例 `tempfile.TemporaryDirectory` 与短 ControlPath 父目录，用例结束清理；静态核脚本与改前副本位于会话 scratchpad，跑完删除。旧全套 16 项历史失败/两空目录归属、套件外预核 UNKNOWN 未重核；零模型替身不证明真实 OpenSSH/板/Unity 链路。

### 19.3 稳定候选四条件自证（workflow §4.3.1；按 AC-10 修订 9 / AC-13 修订 2；纠正 C10-1 后）

**完整候选 diff**：cmd: `git diff <BASE> <纠正候选代码提交> -- tools/eng_loop2/play_ops.py tests/test_eng_loop2_play_ops.py docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`（BASE 按 §18 命令运行时解析；3 文件 +487/−44，与 §18 同计数，因三常量为移动）；本轮增量 cmd: `git diff <§18 候选代码提交> <纠正候选代码提交>`（仅测试文件 +60/−60）；`<纠正候选代码提交>..HEAD` 在 PLAY_GOVERNING 与三操作单上零 diff（cmd: `git diff --stat <纠正候选代码提交> HEAD -- tools tests docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md docs/evidence/P1-ENG-LOOP-002-play-ops.md docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md`）。

| 条件 | 自证 | 证据指针 |
|---|---|---|
| 1 范围与接口冻结 | C10-1 已纠正：测试修改全部落在答复 §2 点名的 `DiagTestBase`/`DiagTests`/`DiagBindingTests`，模块级定义移除；生产/诊断页/闭集外测试类零改；BIND 接口沿 §18.1 冻结；无新待裁定。§18.2 披露 2（`DiagAccount` 缺省旧 id）与 `release_gate` 陈旧文档串按 C10 §3 保持（PR-C10-1 交复核关注） | artifact: `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md#19.1`、`#18.1`、`#18.2`；cmd: 上列完整候选 diff 与 19.1 逐 hunk 行域对照 |
| 2 相称测试（AC-13 修订 2 窄修替代） | 新测试树四模块 focused 169 OK；静态等价核 `ast_equal True`；§18.3 红绿行为结论按 19.2 携带、哈希不携带；**未跑全套**，是否充分由复核判，不预判条件②满足 | artifact: `docs/evidence/P1-ENG-LOOP-002-c10-rework-focused.log`、`docs/evidence/P1-ENG-LOOP-002-diag-binding-focused.log`；test: `tests.test_eng_loop2_play_ops.DiagBindingTests`、`tests.test_eng_loop2_play_ops.DiagTests`、`tests.test_eng_loop2_play_ops.DiagControlPathTests`、`tests.test_eng_loop2_play_ops.DiagAccountTests`；cmd: 19.2 focused 命令 |
| 3 已知 Unity 失败/人眼义务 | 无 Unity 运行、无已知 Unity 失败；呈现/采集与板输入围栏零改，无新增人眼要求，SUB:2 附议与 UNKNOWN 携带 | artifact: `#18.1`（BIND-6 行）；cmd: `git diff --stat <BASE> <纠正候选代码提交> -- tools/eng_loop2/operator_web.py`（空） |
| 4 复核入口/状态/候选/风险 | 复核入口 `docs/reviews/P1-ENG-LOOP-002.md`（新停点首轮由复核角色开节）；状态板本项交接行交 Acceptance 下一实际 C 轮；风险见 19.4 | artifact: `#19.4`；artifact: `docs/current-status.md#Active handoffs` |

**逐 AC 指针**：

| AC | 证据 | 后置/未运行 |
|---|---|---|
| AC-10 修订 9 | test: `tests.test_eng_loop2_play_ops.DiagBindingTests`；test: `tests.test_eng_loop2_play_ops.DiagTests`；artifact: `#18.1`、`docs/evidence/P1-ENG-LOOP-002-c10-rework-focused.log` | 同 §18.4；真实 OpenSSH/板/Unity 未运行；`diag_release:` 实际行未写；DIAG:RETRY:1 未放行 |
| AC-13 修订 2 | artifact: `#19.1`–`#19.3`、`docs/evidence/P1-ENG-LOOP-002-c10-rework-focused.log`；cmd: 完整候选 diff（BASE 运行时解析） | 未跑全套；红绿未对新树重跑（行为结论携带，见 19.2）；复核仍可判替代不足 |
| 携带：AC-10 修订 7/8、既有 Ops/AC | 四模块 focused 全过；指针沿 §15.3/§18.4 | 同 §15.3/§15.4/§18.5 后置项 |

### 19.4 风险（增补 §18.5）

- 本轮只改测试名绑定；§18.5 全部风险原样保留。新增：红绿未在新测试树重跑，携带依据为生产零改 + AST 等价核；若复核不认可静态等价核替代，需另行具名安排新树红绿（零模型，仍在原 focused 用途内），本轮不自行扩展。

## 20. 轮次 `诊断P1执行`：`P1-ENG-LOOP-002:DIAG:RETRY:1` 一次 P1 诊断执行记录（**诊断；不进证据链；不作任何门判定**；交接受 `诊断P1核清`）

依据：同名提案「诊断窗口落实」§1–4、诊断页「现行 DIAG:RETRY:1」唯一命令；Dispatch-Id `P1-ENG-LOOP-002-诊断P1执行-20261008T213418Z-5f16`，派发基线 `97a5a35`（开工 HEAD `1433c9c`）。执行人 = 实现角色（Opus 子代理），机器 = MacBook Air（Unity 主机），板 = Host Jetson。本人在线窗口起点 = 账本同日条 at 约 21:27Z。本节只记录诊断事实与指针，原件只留两端诊断根，不复制进正式证据/Unity 验收日志；不判门、不签 UNITY_NA/DONE；代码/测试/工具/配置零改，OSB-R1-1 未应用。

### 20.1 双检出与实际执行顺序（UTC，2026-10-08）

- 文档检出：临时 worktree `~/TetheredDroneTracking-diagretry1-docs` @ `1433c9c`（= 当时 origin/main 发布引用，含「诊断窗口落实」与 `diag_release:` 行），工具自检 `check_ledger`/`check_docs` rc 0；收尾后 `git worktree remove`。
- 执行检出：主树 `git checkout --detach c4973d03e1db374c3b837e2ec7d0754a73eac378`（= 同名复核最新有效 `passed_candidate`；与发布引用差异仅 6 个文档路径，PG 与三操作页空 diff；Unity 已打开主树、未重启），树干净、无 `Assets/_Recovery`；收尾后 `git checkout main`（`1433c9c`），树干净。
- 用户可见入口：Claude 桌面终端面板标签 `DIAG RETRY1 P1`，由 scratchpad 包装脚本先打印中文本人操作说明，再逐字运行诊断页唯一命令（`--playbook P1 --p2-object red_car`）。
- 时间线：21:35:14 开工读合同 → 21:36:34 建双检出 → **21:36:53 工具起（诊断根 `20261008T213653Z`）** → 21:36:55 放行门 `RELEASE_GATE_OK`、账本唯一条目/`diag_release` 绑定、计划冻结 → 21:36:57 Air 环境/det-assoc 资产/烟测 32 行 rc 0 → 21:36:57–21:37:00 主连接 d1（板只读核、16 路径同步与逐文件 sha、`run/` 放置）后关闭 → 21:37:00 主连接 d2、前台服务编号 1 → 21:37:05 `listening`、`/status` 一次与核对 rc 0 → 21:37:05–21:38:07 measure rc 0 → k-receipt rc 0 → 操作页 `http://127.0.0.1:8772/` → 本人按 Play（按钮时刻 UNKNOWN；首帧 21:40:05）→ 会话 `diag-loop2-214005` → 21:40:42–21:42:44 P1 四步 ask 均本人「发送」、四次候选均本人「确认」、计划末 stop APPLIED → 本人在 Unity 停止（按钮时刻 UNKNOWN；21:42:56 帧环/真值移入诊断根）→ 21:42:56 向板服务发 Ctrl-C → 见 20.3 → 21:49:07 日志回传、关 d2、私有 ControlPath 目录已删（空）、runtime 归位、摘要 rc 0 → 300 s 反馈等待（本人未在操作页点反馈）→ **21:54:08 工具退出 rc 3（`DIAG_END_WITH_ISSUES`）** → 21:54:37 主树回 main、文档检出移除，整批结束。

### 20.2 粗账实账（原件：Air `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261008T213653Z/ops-diagnostic-ledger.json`）

| 维度 | 已签上限 | 实际 |
|---|---|---|
| 整批 | ≤ 1，P1 固定 | 1，P1（`consumed=true`，本 id 已用尽） |
| 墙钟 | ≤ 2700 s | 工具 21:36:53→21:54:08 = 1035 s（粗账 `elapsed_s` 733.97 截至 21:49:07，不含其后 300 s 反馈等待）；含开工准备与检出收尾 21:35:14→21:54:37 ≈ 1163 s |
| SSH 主连接 | ≤ 2 | 2（d1、d2，rc 0）；未另开连接 |
| 板服务启动 / GGUF 加载 / 故障重启 | ≤ 1 / ≤ 1 / 0 | 1 / 1 / 0 |
| YOLO 加载 | ≤ 1 | 1 |
| 本人 Play / 会话 | ≤ 1 / ≤ 1 | 1 / 1（`session_rc` 0） |
| measure / k-receipt | ≤ 1 / ≤ 1 | 1（rc 0）/ 1（rc 0） |
| Air 新增 | ≤ 250,000,000 B | 工具峰值 87,074,184 B（诊断根+待移帧环+ControlPath）；另文档检出临时件 75,197,059 B（跟踪文件字节和，已删除），同时存在上界约 162.3 MB |
| 板新增 | ≤ 200,000,000 B | 轮询峰值 385,629 B（`du -sb` 诊断根）；21:42:05 后无读数，收尾 du 未取得 → 终值 UNKNOWN |
| 表列 0 项 | 0 | 0（无下载/安装/编译/模型或库传板/正式 ID/5060/云） |

### 20.3 停止原因、问题与偏差（只记录，不判门、不归因定级）

1. **STOP3（工具判定）**：`board port/process release cannot be confirmed`。21:42:56 经 d2 前台 `-tt` 通道写入 Ctrl-C 后，板端无任何新输出（`board/serve-channel-1.log` 与回传 `logs/serve-1.log` 末行停在 21:42:37 的 llama 推理日志，无 `serve_rc`/`serve_diag_sh_rc`）；120 s 后同会话键入附录 7 收尾核对，60 s 内无 `DIAG_CLOSEOUT_DONE`；键入 `exit` 后 30 s 通道未退出。粗账 `serve.release`：`serve_rc`/`sh_rc` null、`ports_released`/`no_residual_process` false、`released` false，`unknown` 1 条。**板上服务（llama-server pid 89781、端口 18081/18082）是否已退出 UNKNOWN**；本批未另开连接核清。
2. **工具挂起（新观察）**：`finish_channel` 在读线程仍阻塞于 `stdout.read1` 时关闭 `proc.stdout`，主线程卡在缓冲区锁上（`sample` 显示主线程 `__psynch_cvwait`、读线程阻塞 `read`），超过工具自身全部等待时限仍不前进。
3. **实现角色手工动作（偏差，须核清）**：21:49:07 对**本批自己的** d2 前台通道 ssh 客户端（本机 pid 20690，argv 含本批 ControlPath `el2d-3ctbt4r4/d2`）发 SIGTERM，使读线程得 EOF、工具按原流程继续收尾；未新开连接、未重启/重试、未杀板上或其他进程。远端 pty 随之关闭（"Shared connection to 127.0.0.1 closed."），远端是否因此挂断服务 UNKNOWN。终端随后出现读线程 `ValueError: read of closed file` 回溯（守护线程，未影响后续收尾）。事前已在终端面板另开标签 `notice` 用中文告知用户。粗账 `deviations` 为空（工具不知此动作），以本条为准。
4. **一致性提示**：摘要 `consistency_issues` 1 条——会话开始时共享 runtime 中残留的旧请求 `diag-loop2-234800-req-52e0fb26`（confirm）被会话判 `IGNORED_FOREIGN_SESSION`（`play/sessions/diag-loop2-214005/language-session.jsonl` 第 3 行），非本工具提交。
5. 其余：`faults` 0、`not_executed` 0；Play/停止按钮时刻 UNKNOWN（本人未提供）；本人未在操作页给「通过/失败/受阻」反馈（`post_closeout.feedback_given=[]`）。

### 20.4 会话客观事件（`play/ops-summary.json`；只是事件，不证明跟对）

四步 ask（the suv / the taxi / the red car / the suv）均 `APPLIED`，designation 4 次均 `BOUND`，进入 `TRACKING` 4 个纪元；`SUSPECTED` 1 次（`tracker_failure`，原显式报告原样记录）；`confirm` APPLIED 4；跳过（不在画面）0；`TERMINAL` 原因 `operator_stop`（计划末 stop）；模型加载 1；会话流 840 行、坏行 0。

### 20.5 原件指针与收尾状态

- Air 根：`outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261008T213653Z/`（粗账、`ops-events.jsonl`、`play/ops-web.jsonl`、`play/ops-summary.json`、`play/diag-loop2-214005/`、`raw/`、`board/serve-channel-1.log`、`board/board-logs.tar`、`ssh/d1.tsv`/`d2.tsv`、`release/`）；板根 `/home/jetson/eng-loop2-diag/20261008T213653Z` 保留不删。旧粗账未动。
- runtime 归位：粗账 `closeout.runtime_restore=done`，开工前残留 `frames`/`m3_body_truth.jsonl` 已移回，覆盖文件进 `hold/`；`runtime/scenario_config.json` 不存在；主树 `git status` 0 行。
- 交 Acceptance `诊断P1核清`：核资源/偏差/问题及结束事实（尤其 20.3 第 1–3 条：板端释放 UNKNOWN、收尾挂起、手工 SIGTERM），再安排 OSB-R1-1 后置补丁；本轮不改代码、不自行重启或补核。

## 21. 轮次 `OSB文字补丁`：OSB-R1-1 逐字应用履行（**零消耗；仅一行 docstring；交 Acceptance 文字履行核清**）

- Dispatch-Id `P1-ENG-LOOP-002-OSB文字补丁-20261008T220251Z-851b`；派发基线 `2ff7e02`（开工 HEAD `ded0717`，其间仅 supervisor 派发登记）。唯一合同：同名提案「诊断P1核清（2026-10-08，Acceptance）」§3；补丁原文：`docs/reviews/P1-ENG-LOOP-002.md`「R1@OpsDiagBindK1K2（2026-10-08）」§3 OSB-R1-1 旧行→新行。

### 21.1 逐字 diff（`git diff -- tools/eng_loop2/play_ops.py`，唯一功能路径）

```diff
@@ -381,7 +381,7 @@ sys.exit(4 if remaining else 0)
 def release_gate(ctx: Context, ledger_hits: Sequence[str] = LEDGER_HITS) -> GateResult:
     """操作单第 1.0–1.5 节的机械部分；原流写 `$OUT/release/<UTC>.txt`。不 checkout、不写已跟踪路径。
 
-    `ledger_hits`：1.5 账本命中项（正式 = 第 1.5 节两条；诊断 = SUB:3 签发条目与完整 request_id）。
+    `ledger_hits`：1.5 账本命中项（正式 = 第 1.5 节两条；诊断 = 调用方传入的 `DIAG_ENTRIES` 条目标题片段与完整 request_id）。
     """
```

- 应用前核对：磁盘旧行与复核原文旧行逐字一致（含四格缩进，文件内恰 1 处）；新行逐字取自复核原文；替换后 `--stat` 为 1 文件 +1/−1。函数体、参数、判据、数值、顺序及其他功能文件零 diff。
- 未改 finding 分级/依据，未自记复核 CLOSED，未改旧 passed_candidate 或机读放行行；本补丁使 PG diff 非空，随未来候选全 PG 比较携带（同提案「诊断P1核清」§3）。

### 21.2 未运行行为验证声明

本轮只做文字履行核对（上方逐字 diff），**未运行任何功能测试**、未加载模型；零 SSH/板/Play/回放/下载/装包/正式 ID；未借 `42979c14:SUB:1` 余额或已耗尽诊断；未顺带修「诊断P1核清」§2 任一功能问题。consumed=none。
