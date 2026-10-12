# P1-ENG-LOOP-002 — `K1K2K3K4` 稳定候选（Implementation；登记轮次 `稳定候选`）

- 派发：Dispatch-Id `P1-ENG-LOOP-002-稳定候选-20261007T164349Z-4ffd`（`requested.round` = `稳定候选`；Opus 子代理，单写者，supervisor 派发）。
- 机器：MacBook Air（`sysctl hw.model` = `Mac16,12`，Unity 主机）；仓库 `.venv-yoloe` 只读、未装包；开发期 focused 用系统 `python3`（与既往 focused 同口径），停点全套用 `.venv-yoloe`。
- 合同：同名提案「R3六题答复落实」§2（AC-7 修订 2(a)(b)、AC-10 修订 1(a)(b)）、「IR-N裁定」§1–2（投影更正、AC-15 修订 1）、「CHANGE5答复落实」§2–3（AC-7 修订 3）；随带同名复核「R3@K1K2K3K4 派发」§2 O-1…O-6 与 `docs/evidence/P1-ENG-LOOP-002-C3-K1K2K3K4.md` §3 PR-8…14。前一中间提交的落点见 `docs/evidence/P1-ENG-LOOP-002-r3answer-candidate.md` §1（本文件不重述，只写本轮增量与稳定门自证）。
- 执行信封：`docs/authorizations.md` 2026-10-06「P1-ENG-LOOP-002 — 用户首签 N-1 阶段 A 停点全套额度（按提案 §5.1 表；supervisor 会话代录）」。适用性逐项核对见 §6；B-main 已签但运行未放行：SSH、复制、板、Jetson、Unity/Play、5060、下载、pip、runtime 本轮一律 0。

## 0. 派生标识与完整候选 diff 解析式（运行时解析，不手抄）

```bash
PASSED=$(grep -oE 'passed_candidate: [0-9a-f]{40}' docs/reviews/P1-ENG-LOOP-002.md | tail -n 1 | awk '{print $2}')   # R2 通过候选 = 全量基线
R2_ROUND=$(grep -oE 'round_candidate: [0-9a-f]{40}' docs/reviews/P1-ENG-LOOP-002.md | tail -n 1 | awk '{print $2}') # R2 §0 轮候选 = 修复触及行基线（R3 派发 §0：与 PASSED 同值）
MID=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 R3答复后新候选 中间提交')     # 中间提交（非稳定）
DISPATCH=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 稳定候选 supervisor 派发登记')  # 本轮派发 base
CODE=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 稳定候选 代码候选')           # 代码候选（全套在其上执行，工作树干净）
CAND=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 稳定候选 收工')               # 本停点稳定候选（交 C4）
git diff "$PASSED".."$CAND"                       # 完整候选 diff（相对上一通过候选；C4 核对对象）
git diff --name-only "$PASSED".."$CAND"           # 路径闭集（见 §5）
git diff "$R2_ROUND".."$CAND" -- controller tools tests config Assets ProjectSettings Packages/packages-lock.json docs/evidence/P1-ENG-LOOP-002-play-ops.md   # PLAY_GOVERNING 增量
git diff "$MID".."$CODE" -- controller tools tests docs/evidence/P1-ENG-LOOP-002-play-ops.md   # 本轮相对中间提交的增量
git diff --stat "$CODE".."$CAND"                  # 代码候选之后只有证据/状态文档
```

## 1. 状态与结论

- **本提交是 `K1K2K3K4` 稳定候选**，交接受 `C4@K1K2K3K4`（同停点首退 1/1 已用，不重置），核对后交独立 Review 核稳定门与 `R3@K1K2K3K4` 资格。只记 `IMPLEMENTED`（未复核），不记 `DONE`；不改 Gate board 门值。
- 本轮在中间提交上完成：AC-7 修订 3（有界长轮询，客户端 + 服务端）、AC-15 修订 1（jetson 单轮、首失败停、操作单逐步退出码）、操作单第 0.6 节有限路径/预留重算与投影更正、第 4 节去占位、第 5 节逐步检查退出码、smoke 集路径与 Air 前置核验；中间证据加更正注记（不删原文）。
- 停点全套 1 次（N-1 第 3/3）：`Ran 2336 — FAILED (failures=4, errors=9, skipped=19)`，13 项与上一全套逐名相同（基线既有），**本批新增失败 0**；模型加载与 §5.1 表同型（§6）。
- AC-14、AC-15（板端生产收据）、AC-18 与 AC-16 板端部分 = `NOT_RUN`；不申请 `UNITY_NA`。

## 2. 稳定候选四条件自证（workflow §4.3.1；按 AC-n 附指针）

1. **实现范围与接口冻结：成立。** 本轮代码只改 §4.1 具名文件 `controller/language_selector.py`、`tools/language_serve.py`、`tools/language_latency.py` 与对应测试 `tests/test_llama_server_adapter.py`、`tests/test_language_latency.py`（cmd: `git diff --name-only "$MID".."$CODE"`）；`LanguageWorker` 未改（AC-11，§4）。对外接口变化只有已冻结的两处：`GET /result/<id>?wait_s=<w>`（AC-7 修订 3(a)，只在六键 llama 路径）与 `measure --host jetson` 单轮/首失败停（AC-15 修订 1(a)(b)）；其余 CLI、账、身份块、K 派生不变。R3 派发 §1 ① 指出的三处未冻结项已消除：IR-M7 占位改为现行 300 s（中间提交已落）、IR-M1 十旗标已冻结并落地、IR-M3 主连接口径已冻结并落入操作单第 0.5 节；本轮又去掉第 4 节 `<n>`/`<R_n>` 占位（`N` ∈ {2,3} 经 `case` 机械派生 `R_N`，其余即 STOP）。操作单剩余尖括号只是运行时由规则决定的取值（候选序号 `<i>`、按公式算的 `<T_sess>`、Play 前预登记的 `<P2 对象>`、函数用法说明），不是待裁定的合同值。合同歧义：无新增（§8 只列实现读法供 C4 核对）。
2. **相称测试/编译通过：成立（带基线失败）。** focused 九模块（系统 `python3`）`Ran 488 — OK（skipped=3）`（= 中间提交 468 + 本轮 20 例）；新增 20 例在改前代码上为红（17 例失败/超时，3 例为既有行为的保持性断言照绿，§3）；停点全套 1 次、新增失败 0（artifact: `docs/evidence/P1-ENG-LOOP-002-tests-stable.log`）。本候选触及 `llama-server` 启动路径与客户端结果接纳（真实模型加载器路径），**不适用窄修替代**，故用了 N-1 最后 1 次全套（「R3六题答复落实」§3 末段、「CHANGE5答复落实」§3）。操作单 11 个 `bash` 代码块逐块 `bash -n` rc 0（只是语法检查，不是 Air/板执行验证）。
3. **已知 Unity 失败：不适用。** 本轮零 Unity、零 Play；无新 Unity 失败。
4. **复核范围、状态板、候选提交与未验证风险已更新：成立。** 本文件（§7 复核范围、§9 未验证）、状态板交接行（Owner Acceptance，Status 含 `稳定候选`）、`$CODE` 与 `$CAND` 均已推送到 `origin/main`。

## 3. 冻结修订与观察的落点（本轮增量；中间提交已落者见其证据 §1）

| 项 | 落点（文件::符号 / 操作单节） | 证据（test:/artifact:/cmd:） |
|---|---|---|
| AC-7 修订 3(a) 路径与等待协议 | 客户端 `controller/language_selector.py::HttpAdapter._long_poll_result`（只在 `bind_identity` 核过六键 llama 身份后 `long_poll=True`）、`long_poll_wait_text`（毫秒向下取整，<1 ms 视为无正剩余）、常数 `LONG_POLL_MAX_WAIT_S=4.0`/`LONG_POLL_MAX_RESULT_ATTEMPTS=16`；服务端 `tools/language_serve.py::parse_result_target`（只认一个 `wait_s`，有限正数且 ≤4 s，否则 400）、`SingleFlightRuntime.result_wait`（条件变量：完成/失败即醒，stuck 按 0.05 s 重核）、`build_server(long_poll=True)` 只由 `_main_llama` 传入、回包回显 `wait_s`；账行 `query_id` 去查询串（`_result_query_id`） | test: `tests/test_llama_server_adapter.py::LongPollServerTests.{test_query_id_and_wait_are_separated_and_wait_is_echoed, test_invalid_wait_or_extra_parameters_are_bad_requests, test_completion_and_failure_reply_immediately_not_at_wait_expiry, test_stuck_replies_immediately, test_pending_or_busy_replies_when_the_wait_expires, test_local_hf_server_keeps_the_old_target_parsing}`；`LongPollClientTests.test_end_to_end_one_long_poll_per_inference_on_the_real_server`；`IsolatedDeployEntryTests.test_isolated_root_serves_query_then_releases_ports_without_residue`（真实 llama 分支入口 + 绑定客户端：恰一次 `?wait_s=`） |
| AC-7 修订 3(b) 有限次数与守账 | `_long_poll_result`：不 sleep；第 17 次之前以 `timeout` 放弃（`awaiting_idle`）；`_call` 抛错即退出（不重试）；服务端不回显 `wait_s` → `worker_died`、不回退短轮询；每次请求前 `_call` → `_budget_guard("business")` | test: `LongPollClientTests.{test_sixteen_result_attempts_at_most_then_stop_without_a_seventeenth, test_http_failure_is_not_retried_and_never_falls_back_to_short_polling, test_budget_is_checked_before_every_result_request}` |
| AC-7 修订 3(c) 截止与结果接纳 | `w = min(4, T_ret 剩余, T_hard 剩余)`；单次 I/O 截止仍为 `_call` 的 `min(5 s, T_hard 剩余)`；回包后重核：逾期 T_hard → `worker_stuck` fatal，逾期 T_ret → `timeout` 且 `awaiting_idle`，不接纳 `done`；健康 300 s/0.25 s、K 派生、测量 60 s 未改 | test: `LongPollClientTests.{test_wait_is_min_of_4s_and_both_remaining_deadlines_and_io_tracks_t_hard, test_late_done_after_t_ret_or_t_hard_is_not_accepted, test_completion_failure_and_stuck_states_map_as_before}`；旧路径不变：`test_unbound_or_non_llama_client_keeps_the_old_short_poll` 及既有 `tests/test_language_selector.py` HTTP 用例全绿 |
| AC-7 修订 3(d) 分配与失败终点 | 操作单第 0.6 节重写：两批有限路径表（health 实际 `H2/H3`、必需 status 3 / ≤11 及其代码出处、POST、result 1…16 次/推理且上界 560 / 4,800 远超 200、恢复 status 收据批 0、收尾 0）、预留来源（25 = 3 + 11 + 规划 11；11 = ≤11）、守账式 | artifact: `docs/evidence/P1-ENG-LOOP-002-play-ops.md` 第 0.6 节 |
| 「IR-N裁定」§1 投影更正 | 操作单第 0.6 节「投影的更正」段替代旧「现行轮询节奏下的投影」段；中间证据文件顶部加更正注记（原文保留） | artifact: 操作单第 0.6 节；`docs/evidence/P1-ENG-LOOP-002-r3answer-candidate.md`「更正」注记 |
| AC-15 修订 1(a) 单轮 | `tools/language_latency.py::JETSON_MAX_ROUNDS = 1`，`main` jetson 分支 `measure_host(..., max_rounds=JETSON_MAX_ROUNDS, stop_on_failure=True)`；`measure_host` 缺省 2 轮与旧两宿主路径不变 | test: `tests/test_language_latency.py::JetsonSingleRoundStopTests.{test_success_is_exactly_three_warmups_plus_thirty_two_timed_requests, test_first_round_failure_builds_no_second_adapter_and_sends_no_more_status, test_other_hosts_keep_the_default_second_round}` |
| AC-15 修订 1(b) 首失败停 | `measure_round(stop_on_failure=True)`：首个 `SelectorError` 或 60 s 测量截止失败后不再发起剩余调用，记 `not_attempted`/`stopped_after_first_failure`（只在 jetson 报告出现），不足 32 不出 p95；身份探针失败 → `jetson_probe_failure_report`（`FAIL`、零推理）→ 退出 7（`EXIT_MEASURE_NOT_OK`）；`S_ENVELOPE` 原因原样留在 `failures[].detail` | test: `JetsonSingleRoundStopTests.{test_warmup_failure_stops_before_any_timed_request, test_identity_probe_failure_writes_a_failed_report_without_inference, test_envelope_failure_keeps_its_budget_reason}`；既有 `JetsonMeasurementTests`（解析/约束失败照记、不过滤）照绿 |
| AC-15 修订 1(c) 逐步检查退出码 | 操作单第 5 节：`measure` 非 0 即停（不执行 `k-receipt`、不开 Play），7 按首个失败 `detail` 分流 `S-ENVELOPE` / 首次主臂失败停全部，非 0 非 7 停全部；`measure` 为 0 才执行 `k-receipt`（0/6/8 原语义）；第 13 节 `S-RECEIPT`/`S-ENVELOPE`/首次失败条同步 | artifact: 操作单第 5、13 节 |
| AC-7 修订 2(a)(b)、AC-10 修订 1(a)(b) | 中间提交已落（十旗标、两批账与守账、主连接/通道协议、严格双来源）；本轮未改其代码，操作单第 0.4 节非推理行补长轮询口径 | 中间证据 §1–2；test: `LlamaResourceFlagsTests`、`HealthPollLedgerTests`、`TwoBatchLedgerTests`、`ClientBudgetGuardTests`（照绿）；artifact: 操作单第 0.5、1 节 |
| O-1…O-6、PR-8…14 | 中间提交已落（O-1/PR-8 第 1.0 节 PLAY_GOVERNING 空差异；O-2/PR-10 第 0.5 节与第 2 节统一主连接；O-3 第 14 节末段；O-4 抬头 bash；O-5 `cd … \|\| exit 97`；O-6/PR-13 mini 证据第 7 节 2/3；PR-9 计量；PR-11 旗标；PR-12 门对应/读脚本失败路径/`_Recovery`）；PR-14 目标 Python 动态闭包仍 UNKNOWN（ENV:2 条件性未签） | 中间证据 §1 表；artifact: 操作单对应节 |
| 第 4 节占位 | `<n>`/`<R_n>` → 板端 `N=2|3` + `case` 派生 `R_N`（25/11），其余 STOP；Air 侧命令用 `$UNIT` | artifact: 操作单第 4 节 |
| smoke 集 | 第 5 节写明 LOOP-001 同一 32 行 smoke 路径（§8 读法 R-3）；第 2 节 Air 前置以生产 `read_smoke_rows` 零模型核 32 行与逐图 `frame_sha256`（本机读到 `SMOKE_OK 32`） | artifact: 操作单第 2、5 节 |

修前红/修后绿：`docs/evidence/P1-ENG-LOOP-002-stable-redgreen.log`（一次性 worktree detach 于派发登记提交、只替换两个测试文件、逐例子进程每例 ≤20 s）：新增 20 例中 15 例失败/错误、2 例超时（旧短轮询客户端在替身时钟下无限轮询——即旧代码没有 16 次硬限/回显核验），3 例照绿（`test_budget_is_checked_before_every_result_request`、`test_completion_failure_and_stuck_states_map_as_before`、`test_other_hosts_keep_the_default_second_round` 是既有行为在新路径上的保持性断言）；`IsolatedDeployEntryTests` 端到端例在旧代码上红（无长轮询）。改后 focused 488 OK。worktree 已移除。

## 4. AC-n 逐条证据指针（本候选）

| AC | 结论 | 证据指针 |
|---|---|---|
| AC-1 | 满足（携带） | test: `tests/test_language_loop.py`（`Loop2BodyPolicyTests` 等）；`controller/language_loop.py` 相对 `$PASSED` 零 diff（cmd: `git diff "$PASSED".."$CAND" -- controller/language_loop.py` 为空） |
| AC-2 | 满足 | test: `tests/test_loop2_freeze.py::Loop2FreezeTests.test_frozen_files_are_byte_identical_to_the_baseline`；artifact: `-tests-stable.log`（threshold/段式既有用例全过） |
| AC-3 | 满足（携带） | test: `tests/test_language_loop.py`（`Loop2SingleLoadTests`）；`language_loop.py` 零 diff |
| AC-4 | 满足（携带） | test: `tests/test_language_loop.py`；`language_loop.py`、`gated_publisher.py` 零 diff |
| AC-5 | 满足（携带） | test: `tests/test_language_loop.py`；`LanguageWorker` AST 段与 `$BASE`（`tests/test_loop2_freeze.py::BASE_COMMIT`）逐字相同（§4 cmd） |
| AC-6 | 满足 | test: `tests/test_language_latency.py`（`SingleHostReceiptTests`、`JetsonSessionStartTests`、`CleanWorkingTreeProductionPathTests`，替身改为长轮询回显后照绿）、`tests/test_language_k_binding.py` |
| AC-7（含修订 1/2/3） | 满足（代码与本地夹具；板端未验证） | test: `tests/test_llama_server_adapter.py`（§3 表各类）；artifact: 操作单第 0.4–0.6、4 节 |
| AC-8（含修订 1/2） | 满足（携带） | test: `tests/test_eng_loop2_analyze.py`；artifact: `-four-numbers-fixture-rework1.json`、`-archive-dryrun-rework1.json`；`tools/eng_loop2/analyze_play.py` 零 diff，本轮零回放 |
| AC-9 | 满足 | test: `tests/test_loop2_isolation.py`、`tests/test_llama_server_adapter.py::TruthIsolationTests`、`IsolatedDeployEntryTests.test_isolated_import_closure_of_llama_branch_is_stdlib_plus_closed_set`；本轮新增 import 只有标准库 `math`、`urllib.parse` |
| AC-10（含修订 1） | 自证满足，待 C4/Review | artifact: `docs/evidence/P1-ENG-LOOP-002-play-ops.md`（§3.6 节闭集 + 第 0.5 节主连接/通道、第 1 节严格双来源、第 0.6 节分配、第 5 节逐步退出码、第 13 节 STOP 表）；`bash -n` 11/11 |
| AC-11 | 满足 | cmd: `git diff "$PASSED".."$CAND" -- controller/language_loop.py tools/eng_acq/candidates_preflight.py` 为空（`LanguageWorker`、`CandidatesBackend`、`_validate_candidates_source`、`render_preview`、`_preview` 均在该文件内）；预览/采集/保存路径未触及（H-9 不触发）；清理零删除；artifact: `-K1K2K3K4-handoff.md`「承接声明」携带 |
| AC-12 | 满足 | test: `tests/test_loop2_freeze.py`；`scenario_tether.py` 零 diff |
| AC-13 | 满足（本候选） | artifact: `docs/evidence/P1-ENG-LOOP-002-tests-stable.log`（§6 基线/新增分列）；cmd: `git diff --stat "$PASSED".."$CAND"`；`tests/test_loop2_freeze.py::test_play_governing_paths_outside_the_ownership_table_have_no_diff` 通过；闭集外文档逐文件说明见 §5 |
| AC-14 | `NOT_RUN` | 阶段 B 运行未放行 |
| AC-15（含修订 1） | 代码/操作单落实；板端生产收据 `NOT_RUN` | test: `tests/test_language_latency.py::JetsonSingleRoundStopTests`；artifact: 操作单第 5 节 |
| AC-16 | 阶段 A 部分携带；板端 `NOT_RUN` | artifact: `-assets-local.json`（未改） |
| AC-17 | 满足（携带） | test: `tests/test_language_loop.py`；`language_loop.py`、`language_bridge.py` 零 diff |
| AC-18 | `NOT_RUN` | 阶段 B 证据未产出 |

## 5. 改动文件闭集（`git diff --name-only "$PASSED".."$CAND"`）

- **PLAY_GOVERNING（均在 §4.1 归属表内）**：`controller/language_selector.py`、`tools/language_serve.py`、`tools/language_latency.py`、`tools/eng_loop2/llama_adapter.py`（中间提交）、`tests/test_llama_server_adapter.py`、`tests/test_language_latency.py`、操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md`。闭集外 PLAY_GOVERNING：无（`test_loop2_freeze` 机检）。
- **本角色证据**：本文件、`-tests-stable.log`、`-stable-redgreen.log`、`-r3answer-candidate.md`（中间证据 + 更正注记）、`-mini-ops-prep.md`（中间提交两处）。
- **他角色同区间提交（按真实 diff，不由本表豁免）**：接受（提案各答复节与核对表、`-C3-K1K2K3K4.md`、`docs/implementation-status.md`、`docs/phase1-single-drone-design.md`）、复核（`docs/reviews/P1-ENG-LOOP-002.md` R3 派发节）、supervisor（`docs/authorizations.md` 代录、`docs/evidence/supervisor-dispatch.jsonl`、`docs/parked-status.md`）、实现（`-precheck.md`、状态板）。
- `runtime/README.md` 未改（`/result` 参数是服务协议，不是 `runtime/` 文件字段）。

## 6. 停点全套与 N-1 适用性/累计用量

**适用性先核（逐项与 §5.1 表 / 账本信封对照，全部相符才执行）**：机器 = MacBook Air ✓；解释器 = 仓库 `.venv-yoloe` 原样、未装包 ✓；`ENG_DET_DATA_ROOT` 未设（`env -u`）✓；每候选 1 次、累计 2/3 → 本次第 3/3 ✓；全局约定的 `~/TetheredDroneTracking-full/.venv-yoloe` 本机仍不存在（只读 `ls`），按 N-1 原签用仓库 `.venv-yoloe`，与前两次同口径。

命令（工作树干净，HEAD = `$CODE`）：`env -u ENG_DET_DATA_ROOT YOLO_OFFLINE=true YOLO_AUTOINSTALL=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LOOP2_COUNTS_OUT=<会话临时目录>/LOOP2_COUNTS-stable.json /usr/bin/time -l .venv-yoloe/bin/python <计数包装> > docs/evidence/P1-ENG-LOOP-002-tests-stable.log 2>&1`；计数包装从 `-K1K2K3K4-handoff.md`「候选 1 记录 · 停点全套」末逐字抽出执行，不入仓。

结果：`Ran 2336 tests in 202.289s — FAILED (failures=4, errors=9, skipped=19)`，退出 1；2026-10-07T17:06:02Z–17:09:29Z，`/usr/bin/time` real 206.52 s，峰值内存 1,217,382,200 B。失败集合（`^(FAIL|ERROR): ` 排序）与 `-tests-rework1.log` **逐行相同**（13 项：`test_dist_data_round8` ×2、`.venv-yoloe` 的 `tests` 包遮蔽 5 个模块、`test_rate3_protocol` 1、两 CSRT、`test_dist_data_round4` ×3），归类与依据同 `-K1K2K3K4-handoff.md` 候选 1 表——**基线既有 13，本批新增 0**。测试数 2300 → 2336 = R1 返工 2 + 中间提交 14 + 本轮 20。基线未在 `$PASSED` 上另跑全套（额度每候选 1 次）。

| 维度 | 上限（N-1） | 本候选 | 累计 |
|---|---|---|---|
| 停点全套 | 每候选 1、≤ 3 候选 | **1** | **3/3（用尽）** |
| NanoTrack-v2 ONNX 构造 | ≤ 2/次 | 2（插桩） | — |
| det-assoc 检测器加载 | 0 | 0（插桩） | 0 |
| CSRT 尝试/实例 | 真实 ≤ 2/0 | 原始 6/5 → 真实 2/0（与前两次同型，按用户已认可的 N1-LOAD-RECONCILE 拆分；本机 cv2 无 `TrackerCSRT_create`） | — |
| YOLOE/DINOv2/VLM/HF | 0 | 0（未插桩；离线变量已设，无下载/加载输出；`transformers`/`onnxruntime` 未导入，`torch`/`ultralytics` 仅导入） | 0 |
| 零模型归档回放 | 每候选 ≤ 2 | **0**（`analyze_play.py` 零 diff，不重放） | 3 |
| 墙钟 | ≤ 15 min/次 | 206.5 s | — |
| 新增磁盘（证据与夹具） | 阶段 A 总额 ≤ 20 MB | 新文件 `-tests-stable.log` 26,801 B + `-stable-redgreen.log` 2,567 B + 本文件 + 文档增量 | 本项证据合计约 0.3 MB |
| scenario/session/run ID、Play、VLM、板、5060、API、GPU、下载、pip、SSH、复制、runtime | 0 | 0 | 0 |

N-1 全套额度已用尽：此后任何候选若需全套（含复核判窄修替代不足），须先回用户另签，不从 B-main 借。另：开发期 focused 与一次性红测 worktree 不属信封计量维度；Air 前置的 smoke 核读（`read_smoke_rows`，零模型、只读本机被忽略文件）一次。

## 7. 复核范围（下一实际 C4@K1K2K3K4 → 独立 `R3@K1K2K3K4`）

- 增量（修复触及行基线 `$R2_ROUND`，与 `$PASSED` 同值）：`git diff "$R2_ROUND".."$CAND"` 的 PLAY_GOVERNING 部分——`HttpAdapter`（`_budget_guard`/`_take_budget`/`_call` 的 `http_budget` 与 429 分支、`bind_identity` 的 `long_poll`、`predict_one` 分派、`_long_poll_result`、`long_poll_wait_text`）、`language_serve`（`HttpBudgetLedger`、`_wait_llama_ready` 守账、`LLAMA_RESOURCE_FLAGS`、`parse_result_target`/`_result_query_id`、`SingleFlightRuntime.result_wait`/`_result_locked`/`_changed`、`do_GET` 长轮询分支、`build_server(long_poll)`、`_main_llama` 新参数与退出码 6）、`llama_adapter.health_attempt`、`language_latency`（`measure_round(stop_on_failure)`、`summarize_round` 新键、`measure_host` 参数、`jetson_probe_failure_report`、`main` jetson 分支）、两个测试文件，与操作单全文（第 0.4–0.6、1、2、4、5、13、14 节为主）。
- 连带读：`tests/test_language_selector.py` 旧 HTTP 用例（旧短轮询路径不变的证据）、`controller/language_loop.py::LanguageSession.__init__`/`validate_jetson_session`（第 0.6 节必需 status 计数出处，未改）。
- 是否需要另跑全套由复核按 engineering §6 判；N-1 已用尽，若判需要须先回用户。

## 8. 实现读法（非合同改动；逐条给依据，供 C4 核对，有异议即退回）

- R-1 **单次 I/O 截止**：长轮询请求沿 `_call` 的 `min(5 s, T_hard 剩余)`（AC-8 修订 1 ①「剩余等待」= 至 T_hard），T_ret 一侧由 `w ≤ T_ret 剩余` 与回包后重核承担；若把 I/O 也收缩到 `T_ret 剩余`，服务端恰在 w 到期回包时客户端会与之竞速超时。依据 AC-7 修订 3(c)「保持 5 s 单次 I/O 上限，剩余截止不足时收缩 I/O」+「回包后重新核 T_ret/T_hard」。
- R-2 **16 次耗尽与逾期 done 的状态码**：均按现行 T_ret 到期同一路径报 `timeout` 并置 `awaiting_idle`（下一次提交前须 `GET /status` 报 idle，AC-8 修订 1 ③）；逾期 T_hard 报 `worker_stuck` 并 fatal。不新造原因码。
- R-3 **smoke 集身份**：收据测量用 LOOP-001 K 收据的同一 32 行 smoke（提案 §3.2「3 预热 + 32 计时…现行同口径」）；前版操作单该处是 `<32 行 smoke 集>` 占位。
- R-4 **长轮询只在绑定后启用**：`long_poll` 在 `bind_identity` 经 `/status` 逐键核过六键身份后才置真；身份探针（未绑定）只发 `/status`。旧 HF/candidates/replay 与未绑定客户端逐字保持 0.2 s 短轮询。
- R-5 **服务端无参数 `/result`**：llama 分支仍接受无 `wait_s` 的 `/result/<id>`（即时回复、不回显），以免旧客户端失配；绑定六键身份的客户端一律带参数。

待裁定：**无**（本轮未发现需改合同的歧义）。

## 9. 未验证项与已知限制

- 长轮询、单轮测量与全部计量只在回环 HTTP/1.0 夹具、替身时钟与替身适配器下验证；真实 Jetson、Tailscale 时延/半包、`llama-server` b11381 对十旗标与 `response_format` 的实际行为、板端 Python 动态闭包（PR-14，ENV:2 条件性未签）均未验证（阶段 B）。
- `language_serve` llama 分支是单线程 `HTTPServer`：一次长轮询最多占住服务 4 s；本项客户端单工、会话启动 status 与 Play 查询不并发，故不影响已列路径，但操作者若在长轮询期间另发 `curl /status`，该请求会排队至多 4 s（仍计 1 次非推理）。
- 预留不随本批必需 status 递减（本批末尾至多多留 3 次）；「批次 #3 健康 11」只是规划分配，不保证下一批 11 次内就绪；长轮询也**不保证 35 次收据或 300 次 Play 请求全部做完**（第 0.6 节）。
- 旧 JET 时延/就绪原件本机缺失，`1.7–2.0 s`/`2.48 s` 保持 UNKNOWN；FACT:2 本人 Air 原件对齐在候选通过后，不称当前已齐。
- 第 0.5 节 SSH 失败闭合回退选项、`-O check` 与 `-t` 交互会话 Ctrl-C 传递仍未运行验证（中间证据 §5 原文）。
- 账行在请求结束时落盘：进程被 `SIGKILL` 时最后一个在途请求可能只计在内存（中间证据 §5 原文）。
