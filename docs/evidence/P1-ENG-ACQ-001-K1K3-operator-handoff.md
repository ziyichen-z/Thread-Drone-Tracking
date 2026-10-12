# P1-ENG-ACQ-001 — K1K3 停点自证（Play D1 本地操作页窄范围代码批次）

派发：`P1-ENG-ACQ-001-K1K3操作页-20260930T023124Z-c1b0`（Implementation，Opus 子代理，supervisor 派发，2026-09-29）。
合同：提案「Play D1 本地操作页窄范围代码批次 CLARIFY（2026-09-29）」全文与 AC-22/23/24、AC-18 修订 4；执行信封：账本 2026-09-29
「用户授权窄范围代码批次：把 LOOP-001 带按钮本地操作页适配为 Play D1 操作页」（Consuming = no）。
候选 = 本批主题以「P1-ENG-ACQ-001 K1K3操作页」开头的实现提交；提交号可由 `git log --grep` 派生，本文不手写。

## R2@K1K3返工（K1K3-R2-1，2026-09-30）

派发：`P1-ENG-ACQ-001-R2@K1K3返工-20260930T040057Z-ce72`（Implementation，Opus 子代理，supervisor 派发）。依据：`docs/reviews/P1-ENG-ACQ-001.md`「R2@K1K3」
§3 阻断 finding K1K3-R2-1（CLASS_2，依据 `BC-24` 读作 AC-24）及其闭合要求；合同不变（CLARIFY、AC-22/23/24、AC-18 修订 4）。复核返工，**直接交
Review `R3@K1K3`，不经核对轮**。**本节覆盖下文两节的测试数、全套数字与复核范围**，下文保留为既往记录。本轮两笔提交，主题均以
「P1-ENG-ACQ-001 R2@K1K3返工」开头：先「页面修复」一笔（只改页面），后「回归测试与证据」一笔（测试、证据、状态板）；当前候选 = 后一笔，提交号由 `git log --grep` 派生，本文不手写；修复触及行 = 候选相对 R2@K1K3 的 `round_candidate`。

### 自证四项（本轮）

1. **范围与接口已冻结**：只改 `docs/evidence/P1-ENG-ACQ-001-operator-web.py`（`Monitor.poll`/新 `_poll`、`_read_state` 多返回信封 `issued_unix_s`、
   `_read_logs` 记首条 TERMINAL 记录的 `at_unix_s`、新 `_activity_after_close`、`_block_reason`；`App.log` 加锁；页面脚本 `paintButtons`/`render`
   的结果未知框重绘键）、`tests/test_eng_acq_operator_web.py`（新增 4 例、1 例改名，其余未改），以及本节、红绿日志与全套日志。操作单 §4 不改
   （「结束后又有活动」的语义未变，只是判据不再误报）。页面入口、HTTP 端点、CLI argv、日志路径不变；旧 LOOP-001 页面、`controller/`、`Assets/`、
   `config/`、`tools/`、`ProjectSettings/`、桥协议、会话写入顺序与运行时控制语义零改动。
2. **实现者测试通过**：focused 72/72（`.venv-yoloe` 3.12.13 与系统 python3 各一次）；修前红/变异红/修后绿见
   `docs/evidence/P1-ENG-ACQ-001-K1K3-operator-redgreen.log`「R2@K1K3返工」块；停点全套本轮新增失败 0（见下）。
3. **已知 Unity 失败**：本轮零 Play、零会话，无已知 Unity 失败待修。
4. **状态与风险已更新**：`docs/current-status.md` 本项交接行交 Review `R3@K1K3`、Log 一条；未验证项见本节末。

### K1K3-R2-1（AC-24）：只在能证明状态晚于结束时判「结束后又有活动」

- **根因**（复核 §3）：会话先 `_journal` 写 TERMINAL 再 `write_tracker_state`；页面一次轮询先读状态后读日志，落在两次写之间就见到「已结束 + 旧的
  非 TERMINAL 状态」，旧判据据此写粘滞 `block`；并发轮询下较旧的状态读取还可能在较新的日志读取之后入锁。
- **修法**：(1) `Monitor.poll` 用 `poll_lock` 串行化整次轮询（读文件 + 判定 + 写快照），后一轮询的读取必晚于前一轮询，较旧读取不再在较新日志之后
  判定、也不再覆盖较新快照；读序（先状态后日志）不变。(2) `_activity_after_close` 只在两种可证明情形判定：(a) 本号 `tracker_state = TERMINAL`
  已被此前某次（串行）轮询读到，其后又读到非 TERMINAL；(b) 非 TERMINAL 状态的信封 `issued_unix_s` 严格晚于首条 TERMINAL 日志记录的 `at_unix_s`
  （会话写结束前的状态信封必早于该记录，同一 `time.time` 钟）。其余情形——包括复核指出的窗口——不判复用；结束后 `legal` 仍为空（`closed` 即不给动作），
  不因此放开任何按钮。
- **回归**（均用生产写入器：`Env.terminal()` = `LanguageSession._journal`，`Env.state()` = `bridge.write_tracker_state`）：
  - `SidDuringRunTests::test_normal_end_between_journal_and_state_is_not_reuse`（**本 finding 的具名回归**）：TRACKING → 写 TERMINAL 日志 → poll →
    再写 `tracker_state` TERMINAL → poll：无 `sid_block`、`timer.mark_block` 为空、`mark_play_start` 不因同号被拒、操作日志无 `refused`、零 CLI。
  - `::test_concurrent_poll_with_older_state_read_is_not_reuse`（第二条路径）：一次轮询读到旧 TRACKING 后暂停，期间写完两条结束记录并发起第二次轮询，
    再放行：无 `sid_block`，最终快照为 TERMINAL。
  - 正例保持为红（阻断）：原 `::test_activity_after_close_record_blocked`（见过 TERMINAL 状态后又出现 IDLE）未改且通过；新增
    `::test_new_state_after_close_record_blocked_without_seeing_terminal_state`（页面未见过 TERMINAL 状态，但新状态信封晚于 TERMINAL 记录 → 阻断）。
  - 复核 §4 第三条：原 `::test_archive_or_activity_after_close_disables_play_mark` 改名 `::test_archive_disables_play_mark`（内容不变），另增
    `::test_activity_after_close_disables_play_mark`（结束后又有活动 → 计时标记服务端拒绝）。

### 复核 §4 非 finding 观察的处理

- 第一条（重绘键含随帧变化的 `late`）：重绘键改用 `retry_allowed`（ok/blocked），「不能重试：…」原因文字在 `paintButtons` 中就地更新，不再整排重建；
  现有 node 例 `PageScriptButtonTests` 仍绿（未另加专例）。
- 第五条（操作日志写入无跨线程锁）：`App.log` 加 `log_lock`。
- 第三条见上；第二条（状态栏显示 `tracker_state` 新旧）不是合同义务，本轮未做；第四条（操作单 §4 旧句）归接受角色，本轮未改。

### 测试与红绿（本轮）

- **focused**：`.venv-yoloe/bin/python -m unittest discover -s tests -p test_eng_acq_operator_web.py` → `Ran 72 … OK`；系统 `python3` 同命令 → OK。
- **修前红/修后绿**：同一测试文件经 `ACQ_OPERATOR_WEB_PATH` 指向返工前页面（HEAD 版本，临时复制到同目录，运行后删除）→ `Ran 72`、2 failures，红的恰为
  两条「正常结束非复用」回归；两条阻断正例在修前即绿（守住覆盖、不是回归）。变异 V1（撤 `poll_lock`）→ 并发例红；V2（撤信封时刻判据）→ 未见 TERMINAL
  状态的复用正例红；本轮页面 → 72 OK。逐名见红绿日志。复核 R3 可对本轮「页面修复」提交 `git revert -n`（测试在另一笔，保留）复现修前红。
- **停点全套**：`.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-ACQ-001-K1K3-operator-tests.log 2>&1` → `Ran 1984`，
  `FAILED (failures=4, errors=9, skipped=19)`；与上轮全套（`Ran 1980`，同 4/9/19）逐名对比 **FAIL/ERROR 名单完全相同**（13 项环境既有失败），
  增量 4 例即本轮新测试且全过：**本轮新增失败 0**。
- 零消耗：测试全在临时目录，会话日志行由 `LanguageSession._journal` 写、桥文件由 `controller.language_bridge` 写，CLI 为假；不起会话、不读仓库
  `runtime/`、不加载权重。

### 复核范围（`R3@K1K3`）

修复触及行 = 候选相对 R2@K1K3 `round_candidate` 的 diff：`Monitor.__init__`（`poll_lock`/`closed_at`/`terminal_state_seen`）、`_read_state`、
`_read_logs` 的 TERMINAL 分支、`_activity_after_close`、`_block_reason`、`poll`/`_poll`；`App.__init__`/`App.log`；页面脚本 `paintButtons`、`render`
的重绘键与结果未知框；`tests/test_eng_acq_operator_web.py` 的 `SidDuringRunTests` 新增/改名各例。闭合核实：`git revert -n <本轮「页面修复」提交>` 后
`test_normal_end_between_journal_and_state_is_not_reuse` 红，恢复后绿。

### 消耗（本轮）

scenario/session/run ID 0、Unity Play 0、API/VLM 0、检测推理 0、YOLO 权重加载 0、训练 GPU·h 0、序列回放 0、下载 0、pip 0、远端访问 0；
未运行正式收据预检、未创建会话、未写 `runtime/` 共享槽；attempt 2 的 §2.7/§3 预检、放行与 Play 均未启动。

### 未验证项与已知限制（本轮）

- 判据 (b) 依赖会话与桥写入用同一墙钟（生产均为 `time.time`）；若恰在会话写结束前状态与 TERMINAL 记录之间系统钟回拨，理论上仍可误判，概率可忽略，
  且误判只会停用本就无合法动作的结束后页面。钟回拨导致漏判时，同号复用仍由第二个 `session_started`、同号归档与启动前 `sid_usage` 拦截。
- 页面仍未在真实浏览器与真实会话中验证；AC-18 仍 `NOT_RUN`。其余既往限制见下文两节。

## K1K3 操作页返工（C2@K1K3 退回 C2-1/C2-2，2026-09-29）

派发：`P1-ENG-ACQ-001-K1K3操作页返工-20260930T031648Z-14ac`（Implementation，Opus 子代理）。依据：提案「Contract conformance（核对表）」C2@K1K3
具名缺项 C2-1（AC-22）、C2-2（AC-24）与 IR-1…7 裁定；合同不变（CLARIFY、AC-22/23/24、AC-18 修订 4）。**本节覆盖下文同名小节**，下文保留为首版候选的
自证记录（其测试数、全套数字与复核范围以本节为准）。当前候选 = 首版实现提交 + 本轮主题以「P1-ENG-ACQ-001 K1K3操作页返工」开头的提交，
完整候选 diff 可由 `git log --grep` 派生；本轮相对首版的增量 diff 即本轮提交相对其父提交。

### 自证四项（本轮）

1. **范围与接口已冻结**：只改 `docs/evidence/P1-ENG-ACQ-001-operator-web.py`（`App.retry_block` 新增，`_retry`/`_click`/`_run`/`state`/`mark_play_start`
   与页面脚本 `paintButtons`/`retryOk`/`timerHtml`/`render` 的结果未知框）、`tests/test_eng_acq_operator_web.py`（新增 12 例，原 56 例未改）、
   操作单 §4 三句（同号停用含计时标记与重试、手工计时条件、重试放行条件），以及本文件、红绿与全套证据。页面入口、HTTP 端点、
   CLI argv、日志路径不变；旧 LOOP-001 页面、`controller/`、`Assets/`、`config/`、`tools/`、`ProjectSettings/`、桥协议与运行时控制语义零改动。
2. **实现者测试通过**：focused 68/68（`.venv-yoloe` 3.12.13 与系统 python3 各一次）；定点修前红/修后绿见
   `docs/evidence/P1-ENG-ACQ-001-K1K3-operator-redgreen.log`「K1K3 操作页返工」块；停点全套本轮新增失败 0（见下）。
3. **已知 Unity 失败**：本轮零 Play、零会话，无已知 Unity 失败待修。
4. **状态与风险已更新**：`docs/current-status.md` 本项交接行交 Acceptance `C3@K1K3`（附表后交 Review `R2@K1K3`）、Log 一条；未验证项见本节末。

### C2-1（AC-22）：重试前核对现态、原视图、动作闭集与 token

- **服务端**：`App.retry_block(pending, current, now)` 在任何重试 CLI 前逐项核对——同号阻断；原请求视图（`VIEW_KEYS`：会话、状态、原因、epoch、
  track/suspect/result 令牌）须等于当前视图；动作须在当前九态表 `legal` 内；存档 argv 的 `--token` 须等于当前视图的令牌；`confirm` 另须 index 仍在
  当前显示候选内、三门时效与帧差门仍可确认、预览名与字节 SHA 等于原请求确认时浏览器回报的那张（`_click` 现把 `preview_seen` 存入结果未知条目）。
  任一不符：`refused`（`action=retry`，含 `retry_of`/`view`/`current_view`/`current_legal`）写操作日志、**不发 CLI**、条目保留等迟到回执。
  `_retry` 在查同号后、`_run` 前调用它；会话自身的 request_id 去重仍是最终裁定。
- **浏览器**：`/api/state` 的每个结果未知条目带 `retry_allowed`/`retry_block`（由同一 `retry_block` 对当前快照算出）；`paintButtons` 仅在
  `retry_allowed` 为真、动作在当前 `legal` 内且条目视图等于本页所示视图时启用「用同一 request_id 重试」，否则停用并显示「不能重试：<原因>」。
- **回归**（`tests/test_eng_acq_operator_web.py`）：`RetryStateTransitionTests` 7 例——`test_ask_unknown_then_acquiring_retry_sends_nothing`、
  `test_confirm_unknown_then_terminal_retry_sends_nothing`、`test_release_unknown_then_backend_fatal_retry_sends_nothing`、
  `test_confirm_unknown_then_new_result_token_retry_sends_nothing`、`test_confirm_unknown_past_deadline_retry_sends_nothing`、
  `test_confirm_unknown_preview_replaced_retry_sends_nothing`（均断言零 CLI、拒绝落日志、条目 `retry_allowed=false`），正对照
  `test_unchanged_view_retry_resends_the_same_request`（视图未变时原 argv 原样重发）；`PageScriptButtonTests::test_retry_button_follows_current_state_table`
  （用真实 `/api/state` 快照在 node 中执行页面脚本 `paintButtons`：IDLE 未变可点、转 `ACQUIRING` 后停用）。原
  `OperatorLogTests::test_every_click_refusal_unknown_retry_and_timer_logged`（状态未变的重试）不变且仍绿。

### C2-2（AC-24）：同号阻断时停用计时标记（界面与服务端入口）

- **服务端**：`App.mark_play_start` 先 `monitor.poll()`；读取失败或 `sid_block`（第二个 `session_started`、同号归档、结束后又有活动、`acq-d1-1`）时
  `refused`（`action=play_start_mark`）落日志、不写 `play_start_marked`，提示手工计时。`/api/state` 的 `timer.mark_block` 给出同号原因。
- **浏览器**：`paintButtons` 对 `#mark` 与其他按钮同用 `dead`（在途/取数失败/`sid_block`）并加 `timer.mark_block`；计时区显示停用原因。
  §4 T2 手工计时与 T3 CLI 回退不受影响。
- **回归**：`SidDuringRunTests::test_second_session_started_disables_play_mark`、`::test_archive_or_activity_after_close_disables_play_mark`、
  `::test_unreadable_state_does_not_let_the_mark_through`（服务端入口：拒绝、无标记、日志有拒绝、计时仍 unmarked、零 CLI）；
  `PageScriptButtonTests::test_mark_button_disabled_on_same_number_block`（node 执行 `paintButtons`：无阻断可点、第二个 `session_started` 后停用）。

### 测试与红绿（本轮）

- **focused**：`.venv-yoloe/bin/python -m unittest discover -s tests -p test_eng_acq_operator_web.py` → `Ran 68 … OK`；系统 `python3` 同命令 → OK。
  （`.venv-yoloe` 下 `-m unittest tests.test_eng_acq_operator_web` 仍因 site-packages 的 `tests` 包遮蔽报导入错，沿用 `discover -s tests -p`。）
- **定点修前红/修后绿**：同一测试文件经 `ACQ_OPERATOR_WEB_PATH` 指向返工前页面（HEAD 版本，临时复制到同目录运行后删除）→ `Ran 68`、
  11 failures + 1 error，红的恰为本轮新增 12 例（C2-1 六例在状态/令牌/时效/预览已变时仍发 CLI；C2-2 三例仍写标记；页面脚本两例不停用；正对照缺字段报错），
  原 56 例全绿；本轮页面 → 68 OK。逐名见红绿日志「K1K3 操作页返工」块。
- **停点全套**：`.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-ACQ-001-K1K3-operator-tests.log 2>&1` →
  `Ran 1980`，`FAILED (failures=4, errors=9, skipped=19)`。与上一轮同机同解释器的全套（`Ran 1968`，同为 4 failures/9 errors/19 skipped）逐名对比
  **FAIL/ERROR 名单完全相同**（13 项，环境归因见下文「测试与红绿」与提案核对表「范围与测试归因」），增量 12 例即本轮新测试且全过：**本轮新增失败 0**。
- 零消耗：测试全在临时目录，收据/报告由真实 `candidates_preflight` 适配器生成，会话日志行由 `LanguageSession._journal` 写，CLI 为假；页面脚本测试
  只用本机 `node` 执行内嵌脚本（无浏览器、无网络；无 node 时这 2 例 skip）。

### 复核范围（`R2@K1K3`，本轮增补）

在下文「复核范围」之上重点读：`App.retry_block`、`App._retry`、`App._click`（`preview` 存档）、`App._run`（`preview` 入条目）、`App.state`
（`retry_allowed`/`retry_block`/`timer.mark_block`）、`App.mark_play_start`；页面脚本 `paintButtons`、`retryOk`、`timerHtml`、`render` 的结果未知框与重绘键；
`tests/test_eng_acq_operator_web.py` 的 `RetryStateTransitionTests`、`PageScriptButtonTests`、`SidDuringRunTests` 新 3 例；操作单 §4 改动三句。

### 消耗（本轮）

scenario/session/run ID 0、Unity Play 0、API/VLM 0、检测推理 0、YOLO 权重加载 0、训练 GPU·h 0、序列回放 0、下载 0、pip 0、远端访问 0；
未运行正式收据预检、未创建会话、未写 `runtime/` 共享槽；attempt 2 的 §2.7/§3 预检、放行与 Play 均未启动。

### 未验证项与已知限制（本轮）

- 页面脚本只在 node 中执行 `paintButtons`（真实快照输入），未在用户 Mac 真实浏览器与真实会话中点击验证；AC-18 仍 `NOT_RUN`。
- 结果未知条目在状态已变后保留（等迟到回执、按钮停用并显示原因），不自动清除；会话若始终不写该 request_id 的回执，条目会一直显示，操作者按
  T2 状态判断即可。
- C2「未验证项」所列会话异常退出（无 TERMINAL）不自动禁动作仍如原述，按核对表留给 `R2@K1K3` 判断，本轮未改。
- 其余首版限制（下文「未验证项与已知限制」）不变。

## 自证四项（workflow §4.3.1）

1. **范围与接口已冻结**：新增 `docs/evidence/P1-ENG-ACQ-001-operator-web.py`（页面）与 `tests/test_eng_acq_operator_web.py`（56 例），
   改操作单 `docs/evidence/P1-ENG-ACQ-001-play-d1.md` §4（页面用法、CLI 回退、T4 行、顺序/结束行、T1 放行条件改为本批新通过候选）。
   页面入口 `$PY docs/evidence/P1-ENG-ACQ-001-operator-web.py --sid $SID [--runtime] [--play-root] [--k-receipt] [--port 8772] [--open]`。
   旧 LOOP-001 页面、`controller/`、`Assets/`、`config/`、`tools/`、`ProjectSettings/`、桥协议与运行时控制语义**零改动**。
2. **实现者测试通过**：focused 56/56（`.venv-yoloe` Python 3.12.13 与系统 python3 3.14.6 各一次）；修前红/变异红/修后绿见
   `docs/evidence/P1-ENG-ACQ-001-K1K3-operator-redgreen.log`；停点全套见「测试与红绿」，本批新增失败 0。
3. **已知 Unity 失败**：本批零 Play、零会话，无 Unity 运行，无已知 Unity 失败待修。
4. **状态与风险已更新**：`docs/current-status.md` 本项交接行交 Acceptance `C2@K1K3`、Gate board 本项实现列与 Log；未验证项见文末。

## 逐 AC 证据

| AC | 实现要点 | 证据（均在 `tests/test_eng_acq_operator_web.py`，命令见下） |
|---|---|---|
| AC-22 | `legal_actions` 按 CLARIFY 九态表（`STATE_ACTIONS`）；`respecify` 仅在会话日志出现 ask/respecify 的 `APPLIED`/`PENDING_QUEUED` 回执后出现；`ACQUIRING` 仅 stop；`backend_fatal` 仅 stop；`TERMINAL`/表外状态无按钮；`TRACK_ENDED` 是 `designation.result`，只显示「最近指定」与自动路径；每个动作只经 `CliRunner`（`sys.executable -m controller.language_loop <action>`，cwd = 页面所在仓库）；页面只写自己的操作日志；只监听 127.0.0.1，POST 需 nonce 与同源 | `LegalActionTableTests`（6 例：`test_nine_state_closed_table_per_state`、`test_tracking_allows_ask`、`test_acquiring_offers_only_stop`、`test_every_non_terminal_state_has_stop`、`test_backend_fatal_only_stop`、`test_terminal_unknown_and_missing_state_have_no_action`）；`CliExitTests::test_argv_same_interpreter_same_worktree_language_loop_cli`、`::test_main_uses_this_interpreter_and_repository`、`::test_actions_outside_table_do_not_run_cli`、`::test_instruction_known_only_from_accepted_ask`、`::test_track_ended_acquiring_path_shows_only_automatic_progress`、`::test_no_automatic_confirmation_or_action_while_polling`、`::test_page_never_writes_bridge_request_or_lock`；`HttpBoundaryTests::test_listens_on_loopback_only`、`::test_post_requires_nonce_and_same_origin` |
| AC-23 | `ReceiptCheck` 每次轮询用会话自己的 `KReceipt.from_document` 解析收据，核身份 `mac`/`candidates`/`detector-tracks` 与 `CANDIDATES_IDENTITY`、`t_conf_s = T_CONF_S`、`t_ret_s = k_ret/hz`，经会话自己的 `validate_measurement_sources` 核 §2.7 报告（字节 SHA、机器名、逐项绑定、样本），核生效 R/hz，核收据 payload 与会话日志 `session_started.k_receipt` 逐项相等；任一不符即禁确认并列原因。时效三门（查询起 + T_ret + T_conf、首次呈现起 + T_conf、`latest − N ≤ k_ret + k_conf`）的数值只取自该收据，时刻只取自会话写盘数据。确认须：index 在本次显示且候选 index 连续、结果 `model` 为 `candidates`/`detector-tracks` 且 `k_ret` 与收据一致、预览为本会话 `previews/<frame>-<query>.png` 的有效 PNG、浏览器解码成功后回报的 `{name, sha256}` 与服务端重读一致、视图含同一 `result_id`；`/preview` 只按 sha 发同一份字节；`APPLIED` 文案为「只表示受理，不等于绑定」 | `ReceiptBindingTests`（7 例：绑定通过、旧 LOOP-001 收据拒、缺收据/缺报告、报告字节变、生效 R 不符、`session_started` 用了另一收据、会话未启动即未绑定）；`ReceiptValuesTests::test_gate_values_read_from_receipt_not_hand_copied`；`ConfirmGateTests`（13 例：三门取先到者两向、轮询/刷新/重启不续期、截止已过、帧差门、快照过期/读不到、错 index、index 错位、未显示/错图/错 sha、显示后换图、坏图/缺图/跨会话图、旧 token、非 candidates 结果或 k_ret 不符、`APPLIED` 不误报绑定）；`HttpBoundaryTests::test_preview_endpoint_serves_only_the_bound_bytes` |
| AC-24 | 启动前 `sid_usage`：`acq-d1-1`（`RETIRED_SIDS`）、同号归档 `<play-root>/<SID>/unity-runtime`、会话目录无 `session_started`/多个 `session_started`/有 TERMINAL 记录、目录在但无该号活会话锁 → 报「同号不可复用」、退出码 2、不建任何目录；运行中出现第二个 `session_started`、同号归档或 TERMINAL 后又有活动 → 全部按钮禁用（含 stop；CLI 回退仍可用）。SID 须 `acq-d1-<n>`。Play 计时只认用户点「标记 Play 开始」写入操作日志的首次标记，重启/刷新从日志读回；180 s 到点只显示提示并记一次 `play_deadline_notice`，不发任何 CLI；日志不可完整读取时提示手工计时、不显示剩余时间、拒绝再标记。操作日志 `<play-root>/<SID>/operator/operator-web.jsonl` 记点击、拒绝、结果未知（`result_unknown`）、同 request_id 重试、迟到回执、计时标记/到点提示与回执、绑定视图、argv 与时刻；不写会话 JSONL | `SidGuardTests`（8 例）；`SidDuringRunTests`（4 例）；`PlayTimerTests`（4 例：未标记不以页面/会话启动冒充、标记持久化且重启/刷新不重置且只能标记一次、到点只提示不自动 stop、日志坏则手工计时）；`OperatorLogTests::test_every_click_refusal_unknown_retry_and_timer_logged`；`OperationSheetSection4Tests::test_page_usage_documented_and_parses`、`::test_cli_fallback_commands_parse_with_the_real_cli`（§4 页面命令用页面解析器解析、T1/T2/T3 回退命令用真实 `controller.language_loop` 解析器解析） |
| AC-18 修订 4 | 页面不改 Play D1 信封；§4 写明本批须新 `passed_candidate`、attempt 2 按 §2.7/§3 重新预检与 Acceptance 放行，页面不替代 §3；`acq-d1-1` 硬拒；AC-18 仍 `NOT_RUN` | artifact：`docs/evidence/P1-ENG-ACQ-001-play-d1.md` §4；cmd：`$PY docs/evidence/P1-ENG-ACQ-001-operator-web.py --sid acq-d1-1` → 退出码 2、「同号不可复用」、未写文件（本机只读运行一次） |

## 测试与红绿

- **focused**：`.venv-yoloe/bin/python -m unittest discover -s tests -p test_eng_acq_operator_web.py` → `Ran 56 … OK`；
  `python3 -m unittest discover -s tests -p test_eng_acq_operator_web.py`（3.14.6）→ `Ran 56 … OK`。
  注：`.venv-yoloe` 的 site-packages 带一个名为 `tests` 的包，遮蔽仓库 `tests/`，故该解释器下 `-m unittest tests.test_eng_acq_operator_web` 报
  `ModuleNotFoundError`；用 `discover -s tests -p` 即可（全套命令本来就是 `discover -s tests`）。
- **修前红/变异红/修后绿**（`docs/evidence/P1-ENG-ACQ-001-K1K3-operator-redgreen.log`）：同一测试文件经 `ACQ_OPERATOR_WEB_PATH` 指向
  ① 旧 LOOP-001 页面（本批「修前」）→ 56 例中 4 failures + 49 errors（`ACQUIRING` 无 stop、无收据绑定、无 SID/计时等）；
  ② 本批页面逐一撤掉一项门的 10 个变异（副本在会话暂存目录，不入库）→ 每个均至少 1 例红：M1 `ACQUIRING` 无按钮、M2 不查收据身份、
  M3 不查 `session_started` 绑定、M4 不核预览 sha、M5 未标记时拿页面启动当 Play 开始、M6 到点自动 stop、M7 不拦 `acq-d1-1`、
  M8 时效手抄 LOOP-001 常数、M9 `respecify` 无条件出现、M10 第二个 `session_started` 不拦；③ 本批页面 → 56 OK。
- **停点全套**：`.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-ACQ-001-K1K3-operator-tests.log 2>&1`
  → `Ran 1968`，`FAILED (failures=4, errors=9, skipped=19)`。**本批新增失败 0**（新测试文件 56 例全过）。13 项均为本机环境既有、
  与本批无关（本批不改任何被它们导入的模块）：
  - 5 个 import 错误（`test_eng_sft_audit`/`_build`/`_cloud`/`_evaluate`、`test_language_k_binding`）：上述 `tests` 包遮蔽，`tests.fixtures`/`tests.test_language_selector` 无法导入；
  - `test_trackers::test_pinned_opencv_csrt_initializes_and_updates`、`test_track_loop::test_cli_runs_pinned_csrt_to_a_versioned_summary`：本机 cv2 无 `TrackerCSRT_create`（非 contrib 版）；
  - `test_dist_data_round8`（2 例）、`test_rate3_protocol`（1 例）、`test_dist_data_round4::RealArchiveClosureTest`（3 例）：本机 `runtime/runs/` 缺对应归档/存在其他残留。
  上一停点的全套在另一台机器用系统 python3 3.9.6 跑（1642 例、82 errors），解释器与机器不同，逐名基线不可直接对比；本批归因依据是上面的模块级核对。
- 测试全部在临时目录：收据/报告由真实 `tools/eng_acq/candidates_preflight`（只调适配器，零模型、零读图）生成，会话日志行由
  `LanguageSession._journal` 写，桥文件由 `controller.language_bridge` 写，CLI 为假；不起会话、不加载权重、不读写仓库 `runtime/`。

## 完整候选 diff（供 C2 核对）

本批实现提交相对其父提交：新增 `docs/evidence/P1-ENG-ACQ-001-operator-web.py`、`tests/test_eng_acq_operator_web.py`、
`docs/evidence/P1-ENG-ACQ-001-K1K3-operator-{handoff.md,redgreen.log,tests.log}`；修改 `docs/evidence/P1-ENG-ACQ-001-play-d1.md`（仅 §4）
与 `docs/current-status.md`（本项 Gate board 行、交接行、Log 一条）。页面相对旧 LOOP-001 页面的实质差异：九态表与条件 `respecify`、
`ReceiptCheck`（替换 `load_receipt`）、预览 sha 绑定与 `/preview?sha=`、候选结果身份/`k_ret`/index 连续校验、`sid_usage` 与运行中同号拦截、
「最近指定」显示、Play 计时与 `/api/play-start`、`result_unknown` 日志字段、去掉 LOOP-001 的查询/仿真时长上限提示；其余（请求身份绑定、
结果未知与同 request_id 重试、迟到回执、告警预览绑定、Host/Origin/nonce）按旧页逻辑沿用。

## 实现读法（CLARIFY 未逐字规定处；如有异议请接受角色裁定，本批未扩大范围）

- **IR-1 同号与本次活动会话**：「启动前既有会话目录表明 SID 已用」读作：目录存在且（无 `session_started`、多于 1 个、已有 TERMINAL，或
  runtime 会话锁不是该号的活进程）即拒启动；目录存在且恰 1 个 `session_started`、无结束记录、会话锁为该号活进程，视为「T1 已启动后的本次活动会话」允许启动。
  同号归档取操作单 §7 的 `<play-root>/<SID>/unity-runtime`。`acq-d1-1` 另列硬拒。
- **IR-2 「有指令」**：`tracker_state` 不含指令字段，页面以会话日志中 ask/respecify 的 `APPLIED`/`PENDING_QUEUED` 回执为「已有可重用指令」
  （会话 `_begin_designate` 在写这些回执前已设指令）。
- **IR-3 收据问题只禁确认**：按 CLARIFY「禁确认并报告原因」，收据不符时页面照常启动与显示，其他合法动作（含 stop）不受影响。
- **IR-4 同号拦截禁全部动作**：运行中同号复用时连 stop 也禁用，停止改用 §4 T3 CLI。
- **IR-5 计时**：Play 开始仅由「标记 Play 开始」按钮（二次确认）写入，只允许一次；日志不可完整读取时拒绝再标记、提示手工计时；150 s 起提示接近、180 s 到点提示。
- **IR-6 附加的确认前校验**：结果 `model` 块须 `candidates`/`detector-tracks`、结果 `k_ret` 须等于收据 `k_ret`、候选 index 须为 0…n−1，
  作为「身份绑定」「index 缺失/错位」的具体化；页面的会话号须 `acq-d1-<n>`（操作单 §4 号制）。
- **IR-7**：旧页 LOOP-001 专属的「查询序号 ≥36」「sim_t ≥280 s」提示不属 ACQ 信封，已去掉（查询序号仍显示）。

## 人眼试看（非证据）

在浏览器面板用临时目录假会话（假 CLI，端口 8779，零消耗）看过两屏：`AWAITING_CONFIRMATION`（三候选按钮、倒计时到点后变「不可确认 已过截止」
并禁用确认、标记 Play 开始后计时显示、预览解码后点「确认候选 1」经服务端校验发出假 CLI，操作日志记 argv `confirm … --token acq-d1-2-res1 1` 与
`APPLIED`）与 `ACQUIRING`（只有「停止会话」、显示 `TRACK_ENDED`/`SLEWING`、180 s 到点红框提示且未发任何动作）；控制台无脚本错误。
这不是用户 Mac 上的真实浏览器验证，也不涉及真实会话。

## 复核范围（`R2@K1K3`）

`docs/evidence/P1-ENG-ACQ-001-operator-web.py` 全文（`legal_actions`、`sid_usage`、`ReceiptCheck.evaluate`、`Monitor._read_logs`/
`_block_reason`/`preview_file`/`_candidate`/`poll`/`public`、`App._load_timer`/`timer`/`mark_play_start`/`_click`/`_retry`/`_run`、
`Handler.do_GET`/`do_POST`、`main`，以及页面脚本 `previewShown`/`confirmReady`/`paintButtons`/`timerHtml`/`render`）；
`tests/test_eng_acq_operator_web.py` 全文；`docs/evidence/P1-ENG-ACQ-001-play-d1.md` §4。直接关联只读：`controller/language_loop.py`
（`KReceipt`、`validate_measurement_sources`、`read_scenario`、`LanguageSession._action_*`/`_check_confirmation`/`_journal`、CLI `main`）、
`controller/language_bridge.py`（`read_result`/`read_tracker_state`、会话锁文件）、`tools/eng_acq/candidates_preflight.py`。
本批不改变帧/控制协议与会话语义；K1（确认时效）与 K3（候选身份/目标动作）只在页面的展示与发令前门上。

## 消耗

scenario/session/run ID 0、Unity Play 0、API/VLM 0、检测推理 0、YOLO 权重加载 0、训练 GPU·h 0、序列回放 0、下载 0、pip 0、远端访问 0。
未运行正式收据预检、未创建会话、未写 `runtime/`。本机只读运行过一次 `--sid acq-d1-1`（拒启动、未写文件）与一次只读 `sid_usage` 对真实
`acq-d1-1` 目录的判定（结果「已有同号归档」）。

## 未验证项与已知限制

- 未在真实会话与 Unity 主机真实浏览器中运行；实时预览图尺寸、真实时延下的倒计时观感、用户 Mac 浏览器的解码行为未验证（AC-18 仍 `NOT_RUN`）。
- 「浏览器解码成功」由页面脚本在 `load` 且 `naturalWidth > 0` 后回报 `{name, sha256}`；服务端只能核对名字与字节 sha，不能独立证明浏览器已渲染。
- 会话进程异常退出（无 TERMINAL）时页面不自动禁用动作；此时 CLI 会以退出码 5 报结果未知，页面记「结果未知」。
- 页面计时起点是用户点击标记的时刻，与 Unity 实际按下 Play 之间有人为间隔。
- 操作单 §4 之外的文字（抬头「当前结论」、§1、§5 S0 的人工记录）按范围未改；§5 仍要求人工记 Play 开始时刻，页面标记不替代 §6 模板。
- K1K3-R1-1、R1-4 `SCOPE_GAP`/`OPEN` 不在本批范围。
