# P1-ENG-LOOP-002 — R3答复后新候选（Implementation；中间提交，**非稳定候选**；停在待裁定 IR-N1/IR-N2）

- 登记轮次：`R3答复后新候选`（Implementation，Opus 子代理，supervisor 派发；Dispatch-Id `P1-ENG-LOOP-002-R3答复后新候选-20261007T154748Z-0f05`；base 为派发登记提交）。
- 机器：MacBook Air（`Mac16,12`），仓库 `.venv-yoloe` 只读在盘、未装包；开发期 focused 用系统 `python3`（3.14，与既往 focused 同口径）。
- 合同：同名提案「R3六题答复落实」§2–4（AC-7 修订 2(a)(b)、AC-10 修订 1(a)(b)）；随带同名复核「R3@K1K2K3K4 派发」§2 O-1…O-6 与 `docs/evidence/P1-ENG-LOOP-002-C3-K1K2K3K4.md` §3 PR-8…14。
- 信封：账本 2026-10-06「用户首签 N-1 阶段 A 停点全套额度」——**本轮未动用**（停点全套累计仍 2/3，余 1 留给裁定后的稳定候选）；B-main 运行未放行：SSH、复制、板、Jetson、Unity/Play、5060、下载、pip、runtime 均 0。

> **更正（2026-10-07，登记轮次 `稳定候选`，Implementation；按同名提案「IR-N裁定」§1，原文保留不删）**：本文件第「状态与结论」节、第 3 节 IR-N1「事实」条与选项 A/C 的投影读法撤回为**未核投影**，不是已证事实或实测结论：(1)「收据 35 次推理本身就无法在 200 内完成」「约 16–17 次即 `S-ENVELOPE`」「每请求约 9–10 次 `/result`」都以本机缺原件、未独立核实的 JET 旧时延 1.7–2.0 s 推出；旧 0.2 s 节奏的轮询数应为 `1 + ceil(L/0.2)`，第几次 STOP 取决于逐行耗时/失败/预算快照；(2)「即使每次推理只需 5 次轮询，35 × 6 = 210 也已超过 200」把 35 个 `POST /query`（推理账）与 175 个 `GET /result`（非推理账）加进同一个 200 分母，是混账，撤回；(3)选项 C「阶段 B 实际不可执行、等同暂停」与选项 A 的「批次 #3 剩约 90–125、约 70–100 次推理」同样只是投影，不作保证。已证的只是资源风险与已签停止要求。IR-N1 已由用户选 A（`CHANGE:5`）、接受冻结为 AC-7 修订 3；IR-N2 已由接受冻结为 AC-15 修订 1；两者的实现与现行证据见 `docs/evidence/P1-ENG-LOOP-002-stable-candidate.md`。

## 状态与结论

**本轮不是 `K1K2K3K4` 稳定候选，不交 C4。** 按冻结文本完成了代码与操作单的绝大部分返工（第 1–2 节），但落实 AC-7 修订 2(b) 时发现一处合同层面的可执行性缺口，按派发「合同歧义报 needs_user 并停下、不自行重新解释」停在此处：

- **IR-N1**（第 3 节）：在「非推理 HTTP ≤200 两批共账、`/result` 逐次计入」下，现行 `/result` 轮询间隔 0.2 s 使**收据 35 次推理本身就无法在 200 内完成**（投影约 16–17 次即 `S-ENVELOPE`，收据重测 0 → 阶段 B 停全部）。改轮询节奏或请求协议属于改阈值，§2(b) 末句与 IR-M7 裁定要求先另提具体变化裁定、由用户决定，实现不能自选。
- **IR-N2**（第 3 节）：`language_latency measure --host jetson` 现行沿用 `measure_host(max_rounds=2)`，首轮任一失败即自动再跑一整轮（再 35 次推理 + 1 次绑定 `/status`），与已签「收据 35、收据重测 0」及 §2(b)「有限次数」不一致。

两题都会改变新候选的代码与第 0.6 节分配表，且下一稳定候选因触及 `llama-server` 启动命令（真实模型加载器路径）不能用窄修替代全套（「R3六题答复落实」§3 末段），须用掉 N-1 最后 1 次全套；为不把最后 1 次花在注定要再改的版本上，本轮**不跑全套、不置稳定候选**。本提交只记 `IMPLEMENTED`（未复核的中间成果），不记 `DONE`，不改 Gate board 门值。

## 1. 冻结项与观察的落点（本轮已做 / 待裁定后补）

| 项 | 落点 | 状态 |
|---|---|---|
| AC-7 修订 2(a) 十项旗标 | `tools/language_serve.py::LLAMA_RESOURCE_FLAGS` 与 `llama_server_command`（原 `-m`/`--mmproj`/`--host 127.0.0.1`/`--port` 后逐字接十项；prompt/schema/decode、资产三键、local-hf 未动） | 已做；`LlamaResourceFlagsTests` 两例 |
| AC-7 修订 2(b) 健康轮询计量与守账 | `_wait_llama_ready`：每次 loopback `/health` **发出前**核「已用 + 1 + 本批预留 ≤ 上限」，不足 → `ReadyFailure(envelope)` → 退出码 6；每次尝试记结局（HTTP 码 / `error:` / `timeout:`，`llama_adapter.health_attempt`）；GGUF 加载前已无余量 → 直接退出 6、不起子进程。上限 300 s / 间隔 0.25 s 未改 | 已做；`HealthPollLedgerTests` 四例 |
| AC-7 修订 2(b) 两批共用累计账 | `HttpBudgetLedger`（`--http-ledger` JSONL，必需）：启动读入既有行累计、写 `batch_start`；Air→板每个请求到达即计数（`POST /query` = 推理尝试，其余 = 非推理），结束时落行（码/错误/字节/`query_id` 关联）；两批上限不一致、账损坏、未知 kind → 拒启（退出码 3）；`--non-inference-limit`/`--inference-limit` 只许调低 | 已做；`TwoBatchLedgerTests` 两例 |
| AC-7 修订 2(b) 下一请求前核预算 | 服务端回包附 `http_budget` 快照（含本次）；`HttpAdapter._budget_guard`：`/result` 与恢复 `/status` = 业务（已用 + 1 + 预留 ≤ 上限），启动身份 `/status` = 必需（已用 + 1 ≤ 上限），`POST /query` = 推理（≤ 335 且至少还能发一次业务轮询）；不足即 `worker_stuck: S_ENVELOPE…`、置 fatal、此后零请求；服务端 429 `S_ENVELOPE` 同判据兜底；旧服务端无快照时客户端行为逐字不变 | 已做；`ClientBudgetGuardTests` 六例 |
| AC-7 修订 2(b) 操作单分配/预留/两批交接 | 操作单第 0.6 节（路径有限次数、预留来源 25/11、两批同一 `http-ledger.jsonl`）、第 4 节启动命令（`--http-ledger`、`--non-inference-reserve`、`--llama-ready-timeout-s 300`、退出码 6）、第 11 节账行汇总、第 13 节 `S-ENVELOPE` 触发源 | 机制已写；**分配数值依 IR-N1 裁定重算** |
| AC-10 修订 1(a) SSH 单位 | 操作单第 0.5 节：每单元一条认证主连接（`unit_open`/`chan`/`unit_close` 三函数逐字），通道闭集 1/7/2，`-O check` 套接字检查 + 失败闭合回退选项，失败计次不重试，墙钟起止；第 2 节准备发起块改用同一协议（旧直接 `Popen ssh` 已废，mini 证据第 2 节标替代） | 已做（O-2/PR-10） |
| AC-10 修订 1(b) 严格双来源 | 操作单第 1 节：`$REL` 固定为 40 位 SHA；`$PASSED..$REL` 的 PLAY_GOVERNING（workflow §4.4 逐项展开 + 本操作单，先核展开与 `$REL` 上定义一致）差异须为空；执行检出 detach 到 `$PASSED`、整树干净；操作单 sha 与通过版本相等；实际 HEAD/status 原流 → 独立 `git worktree` 文档检出登记 Unity 日志并推送 → 回执行检出重做 1.1–1.4 逐行相同 | 已做（O-1/PR-8） |
| O-3 单元 STOP vs `S-REBUILD` 剧本继续 | 操作单第 14 节末段逐字区分 | 已做 |
| O-4 bash | 操作单抬头：全部命令块在 `bash --noprofile --norc` 中执行（含板端交互会话） | 已做 |
| O-5 `cd` 失败即停 | 第 4 节 `cd … \|\| exit 97`；第 3.5 节 `deploy-verify` 同样 `cd … \|\| exit 97`；`mkdir`、端口/残留检查失败即退出 | 已做（含 PR-12 同类） |
| O-6 / PR-13 全套计数 | `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md` 第 7 节改为「累计 2/3、本轮未跑，余 1 不是派发测试许可」 | 已做 |
| PR-9 HTTP 计量 | 同 AC-7 修订 2(b) 四行（健康 GET 现入账；失败有终点；下一请求前守总账） | 已做 |
| PR-11 旗标 | 同 AC-7 修订 2(a) | 已做 |
| PR-12 门循环 / 读脚本失败路径 / `_Recovery` | 抬头「门与单元对应」：#1 要 G1/G2/G3/G5，#2/#3 另加 G4；附录 P 读脚本 `readelf`/`ldd` 失败即停、扩展 `Machine` 须 AArch64、`pgrep` rc 0/1/≥2 分流；第 1.3 步以 `[ -e ] \|\| [ -L ]` 判 `Assets/_Recovery` | 已做 |
| PR-14 目标 Python 动态闭包 | 不变：板端闭包仍 UNKNOWN，ENV:2 条件性未签；第 9 节风险保留 | 保持 |
| IR-N1 / IR-N2 | 第 3 节 | **待裁定** |

## 2. 代码改动与相称验证（开发期 focused；未跑停点全套）

改动文件（全部在 §4.1 归属表内）：`tools/language_serve.py`（M）、`tools/eng_loop2/llama_adapter.py`（M：`health_attempt`，`health_status` 改为其包装、语义不变）、`controller/language_selector.py`（M：`HttpAdapter` 快照与守账）、`tests/test_llama_server_adapter.py`（M：夹具加 `--http-ledger`/`--non-inference-reserve`，假 `llama-bin` 加 `no_listen`/`slow_health` 两模式，新增 14 例）。文档：本文件（N）、操作单（M）、mini 证据（M，两处）、状态板。

| 命令（工作树 = 本提交内容，系统 `python3`） | 结果 |
|---|---|
| `python3 -m unittest tests.test_llama_server_adapter`（改前基线） | Ran 38，OK |
| `python3 -m unittest tests.test_language_loop tests.test_language_bridge tests.test_language_latency tests.test_llama_server_adapter tests.test_eng_loop2_analyze tests.test_loop2_isolation tests.test_loop2_freeze tests.test_language_selector tests.test_language_k_binding` | **Ran 468，OK（skipped=3）**，44.3 s（R2 时 454 + 本轮 14） |
| 新增 4 个类在**改前代码**上（一次性 worktree detach 于派发 base，只替换测试文件） | Ran 14，FAILED（failures=4, errors=12）——新例确实约束新行为 |
| 操作单 10 个 `bash` 代码块逐块 `bash -n` | 全部 rc 0（只是语法检查，不是 Air/板执行验证） |

新增具名用例（`tests/test_llama_server_adapter.py`）：`LlamaResourceFlagsTests.{test_command_is_original_four_plus_frozen_ten_flags_verbatim, test_started_child_receives_exactly_the_frozen_command}`；`HealthPollLedgerTests.{test_health_success_is_counted_with_outcome_and_reaches_status_snapshot, test_failed_health_attempts_each_have_an_outcome, test_next_health_poll_beyond_budget_stops_with_envelope_and_never_sends_it, test_no_room_before_loading_refuses_without_starting_llama_server}`；`TwoBatchLedgerTests.{test_second_batch_carries_the_first_batch_counts, test_other_limits_or_corrupt_ledger_or_raised_limit_refuse}`；`ClientBudgetGuardTests.{test_inference_and_its_result_polls_are_associated_and_counted, test_next_result_poll_beyond_budget_stops_before_sending, test_necessary_status_may_use_the_reserve_but_never_the_last_slot_beyond_limit, test_inference_limit_and_missing_poll_headroom_stop_the_post, test_server_backstop_refuses_out_of_budget_requests_with_429_and_counts_them, test_old_server_without_snapshot_keeps_old_client_behaviour}`。

未做：停点全套（N-1 余 1，留给裁定后的稳定候选）；窄修替代全套不适用（触及 `llama-server` 命令行即真实模型加载器路径）。

## 3. 待裁定（实现对提案只读，写在此处交接受；需要用户选择的由 supervisor 转呈）

### IR-N1 — `/result` 轮询节奏与「非推理 HTTP ≤200 两批共账」的可执行性

request_id 建议：`P1-ENG-LOOP-002:B-main:CHANGE:5`（新题；不是 CHANGE:2 的重问——CHANGE:2 A 定了计数口径，未定轮询节奏）。

- **事实**：`HttpAdapter.poll_interval_s` 缺省 0.2 s（代码现值，本轮未改）；每次推理 = 1 个 `POST /query` + 至 done 的 `GET /result/<id>`。JET 原读数每请求约 1.7–2.0 s（mini 证据 F-8）→ 约 9–10 次 `/result`/推理。批次 #2 必需 `/status` 3、预留（含批次 #3 最低需求）25、健康约 11 后，业务额度约 161 → **约 16–17 次推理即 `S-ENVELOPE`，收据 35 次无法完成**（收据重测 0 → 停全部、白耗 1 次 GGUF 加载与 1 个 SSH 单元）。这只是投影，不是实测；但即使每次推理只需 5 次轮询，35 × 6 = 210 也已超过 200。
- **为什么不能自定**：§2(b) 末句「需要改该上限/间隔或计数类别时先另提具体变化裁定，不借本条自行改阈值」，IR-M7 裁定「若要改轮询间隔/超时/额度先给明确合同、最坏分配、失败终点再用户决定」。改 `/result` 节奏或加阻塞等待都属此类。
- **选项**：
  - **A（推荐）：有界长轮询**。`GET /result/<id>?wait_s=W`（仅 llama-server 分支；W 固定 4.0 s，小于客户端单次 I/O 截止 5 s，且不超过本次 `T_ret`/`T_hard` 剩余）：服务端在结果就绪、失败、stuck 或 W 到期时立即回包；客户端照旧逐次计入非推理。每次推理通常 1 次 `/result`（推理 < W），最坏 ⌈min(T_ret, T_hard)/W⌉ 次；时延测量不被量化（服务端完成即回）。投影：批次 #2 ≈ 健康 11 + 必需 3 + `/result` 35–70 ≈ 50–85；批次 #3 剩约 90–125 供健康/必需/轮询 → 约 70–100 次推理（低于签发的 300，仍「不保证 335 用完」）。代价：K1 协议加一个可选查询参数与一个新的服务端等待常数，须新代码候选同停点、相称测试与复核。
  - B：把 `/result` 客户端间隔调大（例如 1.0 s）。每次推理约 2–3 次；收据约 105 + 14 可完成，Play 余约 20 次推理；时延被量化 ≤1 s（K_ret 在 5 Hz 下多 ≤5 帧，资格余量很大；数字一的呈现时刻颗粒变粗）。
  - C：保持 0.2 s。代码与本轮相同；操作单写明收据投影超额；阶段 B 实际不可执行（停在收据），等同暂停。
  - D：用户改签非推理上限或单列轮询类别（即 CHANGE:2 的 B 路线），须先按 CHANGE:2 B 文本提交有界申请。
- **推荐理由**：A 维持 200 总账与「逐次计入」的用户选择，不新增预算类别，请求数最少且时延口径最准；B 次之（实现更小，但时延量化影响对外数字的口径）。四个选项都不扩大任何已签上限。

### IR-N2 — `measure --host jetson` 的自动第二轮与「收据重测 0」

request_id 建议：`P1-ENG-LOOP-002:B-main:CHANGE:6`（或由接受裁为既有签发的直接落实，不需用户题）。

- **事实**：`tools/language_latency.py` jetson 分支调用 `measure_host(...)` 未传 `max_rounds`，缺省 2；首轮任一失败（`INVALID`）即新建适配器（+1 绑定 `/status`）再跑 3 + 32 次。已签 B-main 写「推理 收据 35、收据重测 0」，§2(b) 要求各路径有限次数列齐。
- **选项**：**A（推荐）**：jetson 分支固定 `max_rounds=1`（首轮 `INVALID` → 报告 `verdict` 非 OK → `k-receipt` 退出 6 → `S-RECEIPT`），同步 `tests/test_language_latency.py` 具名用例；两宿主旧路径不变。B：保持代码，操作单要求操作者在首轮失败后中断 `measure`（人工、易错，不推荐）。
- **推荐理由**：A 让代码与签发逐字一致，是对已签上限的收紧而非放宽；因涉及 AC-6/15 生产路径行为，仍请接受明确裁定，本轮未改。

## 4. 验证适用性与原账

- N-1：停点全套累计 2/3（未变），本轮未跑；模型加载 0（focused 不含 `test_trackers`/`test_track_loop`/det-assoc）；零模型回放 0。
- B-main 各维度 0；mini/Air 旧余额不触及；无下载/安装。
- 一次性 worktree（红测用）已移除。

## 5. 未核风险与已知限制

- 第 0.5 节失败闭合回退选项（`HostName=127.0.0.1`/`Port=1`/`ProxyCommand=none`）依据 OpenSSH 复用客户端在连不上控制套接字时才走直连的行为写成，**未运行验证**；`-O check` 与 `-t` 交互会话的 Ctrl-C 传递同样未验证。
- 账行在请求结束时落盘：进程被 `SIGKILL` 或账文件写失败时，最后一个在途请求可能计入内存而未落盘，第二批会少计；回包快照与访问日志可交叉核对。
- 每 session ≤60 次推理的分项上限仍只靠操作者按 `http_budget.inference_used` 监控，代码只守总 335。
- 板端 Python 动态闭包、`llama-server` 十旗标在本二进制上的实际行为、`response_format` 被 b11381 接受与否均未核（真实板运行全部后置）。
- 操作单第 0.6 节预留 25/11 与投影基于 JET 诊断时延和规划次数，不是实测或保证余量。

## 6. 裁定后的最短接续

接受（与用户，经 supervisor）裁定 IR-N1/IR-N2 并冻结文本 → 实现按裁定改代码（A/A 路线：`language_serve` 长轮询 + `HttpAdapter` 使用 + `language_latency` 单轮，及测试）、重算第 0.6 节分配并去掉 `<R_n>` 占位 → 停点全套 1 次（N-1 第 3/3）→ 四条件逐条自证、完整候选 diff 解析式 → 提交推送并交 `C4@K1K2K3K4` → 独立复核核稳定门与 `R3@K1K2K3K4` 资格。

## 7. 本轮用量

consumed：无签发维度消耗（SSH 0、ping 0、复制 0、模型加载 0、停点全套 0、回放 0、板/Unity/runtime 0、下载/安装 0）。只有开发期 focused 与 `bash -n`，以及 scratchpad 内一次性 worktree。
