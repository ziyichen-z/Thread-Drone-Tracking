# P1-ENG-LOOP-002 K1K2K3K4 交接（Implementation，Claude Opus 子代理；候选 1 登记轮次 `阶段A实现`（2026-10-06），C1返工候选登记轮次 `C1返工`（2026-10-06），R1返工候选登记轮次 `R1返工`（2026-10-06））

工作项：`P1-ENG-LOOP-002`（`Workflow: engineering-v1`，D4 接受裁定生效；合并停点 `K1K2K3K4`，提案 §7）。
合同：`docs/proposals/P1-ENG-LOOP-002-closed-loop-four-numbers.md`（§0–§8、AC-1…18、§4.1 归属表、决策记录「D4 接受裁定」「N-1答复落实」）。
执行信封：`docs/authorizations.md` 2026-10-06「P1-ENG-LOOP-002 — 用户首签 N-1 阶段 A 停点全套额度（按提案 §5.1 表；supervisor 会话代录）」。
派发：Dispatch-Id `P1-ENG-LOOP-002-阶段A实现-20261006T231621Z-97fb`（`requested.round` = `阶段A实现`；执行机 MacBook Air = Unity 主机；Opus 子代理，另并行派出两个编码助手只写各自文件，见「改动文件」）。

## R1返工候选（2026-10-06；登记轮次 `R1返工`；**先读本节**）

派发：Dispatch-Id `P1-ENG-LOOP-002-R1返工-20261007T023249Z-4b17`（`requested.round` = `R1返工`；执行机 MacBook Air = Unity 主机；Opus 子代理，单写者）。
依据：`docs/reviews/P1-ENG-LOOP-002.md`「R1@K1K2K3K4」§3 R1-1（CLASS_2 `BC-7`）与其「闭合绑定」；同名提案 AC-7（修订 1）、§5.2、IR-11/IR-15。只改 R1-1 触及文件（`tools/language_serve.py`、`tests/test_llama_server_adapter.py`）；合同、AC、阈值、采样、STOP、信封未改。C1返工候选节下各 AC 结论（复核 R1 判成立者）随候选携带，不重述。

**派生标识一律运行时解析（不写死）：**

```bash
R1_CAND=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 C1返工 收工')        # R1@K1K2K3K4 所核候选（= 5262a53…）
R1FIX_CODE=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 R1返工 代码候选')  # 返工代码提交（红绿与 focused 在其上执行）
R1FIX_CAND=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 R1返工 收工')      # 本停点新候选（送 R2）
git diff --name-only "$R1_CAND".."$R1FIX_CODE"    # = tools/language_serve.py、tests/test_llama_server_adapter.py
git diff "$R1_CAND".."$R1FIX_CODE"                # 修复增量（R2 增量核对对象）
git diff --stat "$R1FIX_CODE".."$R1FIX_CAND"      # 代码提交之后只有证据/状态文档
```

### 状态与结论（R1返工）

- R1-1 已修：计量模式写侧改为逐次 `send()` 取到即计（`_CountingSocketWriter`，替换 `_CountingWriter` 包装 `_SocketWriter.sendall`），中途 `BrokenPipeError`/`ConnectionResetError` 时 `count` 即实际交给套接字的字节；读侧 `_CountingReader.read/readline` 改以至多一次底层读的 `read1`/`peek` 逐块取数即计，`BufferedReader` 底层读超时/断连丢弃部分块的字节不再漏计（`_drain_declared_body` 经 `read` 同口径，未改该函数）。头/体边界仍取 `parse_request`/`end_headers` 时刻计数；12 键 JSONL 字段与语义不变；local-hf 分支（无 `--access-log`）`setup` 不替换 `rfile`/`wfile`，读写与回包逐字不变（`test_local_hf_default_has_no_metering_and_old_semantics` 照绿）。
- 两条具名回归按复核「闭合绑定」写入并修前红/修后绿（见下）；focused 九模块 454 OK。
- 停点全套：**未跑，不记全套通过**（engineering §6 窄修条款，自证见条件 2）；`R2@K1K2K3K4` 可判替代不足并要求全套（信封剩 1/3）。
- AC-14、AC-15、AC-18 与 AC-16 板端部分 = `NOT_RUN`（阶段 B 未签）；不申请 `UNITY_NA`。下一步：Review `R2@K1K2K3K4`（复核返工直回复核，不经核对轮）。

### 稳定候选四条件自证（R1返工）

workflow §4.3.1 四项，按 AC-n 附指针：

1. **实现范围与接口冻结**：成立。`git diff --name-only "$R1_CAND".."$R1FIX_CODE"` 恰为 `tools/language_serve.py`、`tests/test_llama_server_adapter.py`（均在 §4.1 功能闭集内）；对外接口无变化（CLI 旗标、12 键访问日志 schema、回包、身份块不变）；改动只在 `_CountingReader`、新 `_CountingSocketWriter`、`LanguageRequestHandler.setup` 计量分支一行与 `import io`（标准库，`test_isolated_import_closure_of_llama_branch_is_stdlib_plus_closed_set` 照绿）。
2. **相称测试通过**：成立。focused（系统 `python3 -m unittest`、离线环境变量，HEAD = `$R1FIX_CODE`）：`test_language_loop`、`test_language_bridge`、`test_language_latency`、`test_llama_server_adapter`（36 → 38）、`test_eng_loop2_analyze`、`test_loop2_isolation`、`test_loop2_freeze`、`test_language_selector`、`test_language_k_binding` 合计 **Ran 454 — OK（skipped=3）**，51.6 s（= R1 复核 452 + 本轮 2 例；skip 数 3 与 C1返工交接同口径，复核副本 4 为副本环境差异）。`AccessLogEveryRequestTests` 连跑 5 次全绿（无时序抖动）。**窄修替代全套的自证（engineering §6）**：相对上一个已跑停点全套的候选（C1返工节解析式 `$RW_CODE`，全套 2/3）只改上述两具名文件；改动不触及真实模型加载器（`llama-server` 子进程/适配器/`SingleFlightRuntime` 未改）、数据划分或对外指标路径（`analyze_play.py` 评分、四类数字未改；访问日志是 §5.2 信封计量来源，不是对外指标）；所修 finding 有修前红/修后绿。故以 focused + 红绿代替本候选停点全套，**未跑全套、不记全套通过**，信封全套额度保持 2/3。
3. **已知 Unity 失败**：不适用（零 Unity、零 Play）。
4. **复核范围、状态板、候选提交与未验证风险已更新**：本节、状态板交接行（Owner Review，Status `AWAITING_REVIEW_R2_K1K2K3K4`，Progress 含 `R1返工`）、候选提交（`$R1FIX_CODE` 代码、`$R1FIX_CAND` 收工，均已推送）、「复核范围（R2@K1K2K3K4）」「未验证项与已知限制（R1返工）」。

### R1-1 闭合（复核 §3「闭合绑定」逐条）

| 绑定项 | 具名回归（`tests/test_llama_server_adapter.py::AccessLogEveryRequestTests`） | 修前（`tools/language_serve.py` = `$R1_CAND` 版、保留新测试） | 修后（`$R1FIX_CODE`） |
|---|---|---|---|
| 写侧：生产 `build_server` + 真实回环套接字，底层套接字换为「响应头整写、此后只再接受 10 B 即抛 `BrokenPipeError`」代理；断言 `response_body_bytes == 10` 且 `error` 非空 | `test_r1_1_response_body_partial_send_counts_bytes_handed_to_socket`（代理同时实现 `sendall`/`send` 两种语义，修前修后同一代理） | **FAIL `0 != 10`** | OK（客户端实收 10 B = 日志 10；`error` 含 `BrokenPipeError`） |
| 读侧：客户端只发声明 100 B 中的 30 B 且不关连接，服务端 drain 超时；断言 `request_body_bytes` = 实发 30、`request_body_complete false`、`error` 含 timeout | `test_r1_1_drain_timeout_counts_partial_body_actually_received`（两子例：正文与头同段 / 正文分段后发；测试把 `ACCESS_DRAIN_TIMEOUT_S` 临时设 0.5 s 并复原） | **FAIL `0 != 30` ×2 子例** | OK（`error` = `TimeoutError: timed out`，断言不区分大小写含 `timeout`） |

红绿输出原样：`docs/evidence/P1-ENG-LOOP-002-r1fix-redgreen.log`（修前 `Ran 2 … FAILED (failures=3)`；修后 `Ran 2 … OK`；focused 九模块全文）。`NOT_MECHANIZABLE` 不适用。

### §5.1 累计用量（R1返工；N-1 信封）

| 维度 | 上限 | 候选 1 | C1返工候选 | R1返工候选 | 累计 |
|---|---|---|---|---|---|
| 停点全套 | 每候选 1、≤ 3 候选 | 1 | 1 | **0**（窄修替代，见条件 2） | **2/3** |
| NanoTrack / det-assoc / CSRT / 其余模型 | 见 C1返工节 | 同前 | 同前 | **0**（focused 不构造模型） | — |
| 零模型归档回放 | 每候选 ≤ 2 | 2/2 | 1/2 | **0/2** | 3 |
| 墙钟 | ≤ 15 min/次 | 187 s | 191 s | 无全套（focused 52 s） | — |
| 新增磁盘（证据） | 阶段 A 总额 ≤ 20 MB | ≈ 0.15 MB | ≈ 0.09 MB | `-r1fix-redgreen.log` 4,406 B + 文档增量 | ≈ 0.25 MB |
| scenario/session/run ID、Play、VLM、板、5060、API、GPU、下载、pip | 0 | 0 | 0 | **0** | 0 |

### 待裁定（R1返工新增）

无。已知边界（非合同改读，随 IR-15 既有口径）：读侧「实际字节」仍按服务端从缓冲**消费**的字节计；连接关闭时 `BufferedReader` 已预读入用户态缓冲但请求解析从未消费的字节（如坏请求行之后同段到达的余字节）不计——与 R1 复核核为成立的 `test_bad_request_line_is_logged_with_actual_bytes` 口径相同，本轮未改。

### 改动文件（R1返工）

代码提交 `$R1FIX_CODE`：`tools/language_serve.py`、`tests/test_llama_server_adapter.py`。收工提交：本文件、`docs/evidence/P1-ENG-LOOP-002-r1fix-redgreen.log`、`docs/current-status.md`。`runtime/README.md`、操作单未改（计量日志字段与口径未变）。闭集外 PLAY_GOVERNING diff：无（`test_loop2_freeze` 照绿）。

### 复核范围（R2@K1K2K3K4）

增量 `git diff "$R1_CAND".."$R1FIX_CODE"`：`_CountingReader.read1/read/readline`、`_CountingSocketWriter.write`、`LanguageRequestHandler.setup` 计量分支；连带读 `parse_request`/`end_headers` 边界、`_drain_declared_body`、`_access_finish` 在新计数下的一致性，与 `socketserver.StreamRequestHandler.finish` 对 `wfile.flush/close` 的调用。副本内按「闭合绑定」修前红/修后绿各一次。是否需要全套由复核按 engineering §6 判。

### 未验证项与已知限制（R1返工）

- 新计数只在回环 HTTP/1.0 夹具与注入代理下验证；板端 Jetson Python、真实 Tailscale 半包/复位时序、`llama-server` 退出时收尾未验证（阶段 B）。
- 写侧逐次 `send` 在套接字设超时时为「每次 send 各自计时」，与 `sendall` 的整体计时略有差异；计量模式服务端套接字未设超时（`StreamRequestHandler.timeout` 为 `None`），drain 只设读超时，故无实际行为差异。
- 其余同「C1返工候选 · 未验证项与已知限制」。

## C1返工候选（2026-10-06；登记轮次 `C1返工`；R1@K1K2K3K4 已核为 `REWORK_REQUIRED`，以下原文保留）

派发：Dispatch-Id `P1-ENG-LOOP-002-C1返工-20261007T013203Z-70a4`（`requested.round` = `C1返工`；执行机 MacBook Air = Unity 主机；Opus 子代理，单写者，无并行编码助手）。
依据：同名提案「待裁定答复」（IR-1…12 裁定、AC-7 修订 1、AC-8 修订 1/2、IR-3 逐项读法边界）、「Contract conformance（核对表）」、`docs/evidence/P1-ENG-LOOP-002-C1-K1K2K3K4.md`「既有条款偏差」C1-AC6/7/8/10 与「预复核关注项」PR-1…6。只改冻结 §4.1 文件闭集；合同、AC、阈值、采样、STOP、信封未改。

**派生标识一律运行时解析（不写死）：**

```bash
BASE=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 N-1答复落实 supervisor 核销' | head -n 1)   # 同候选 1
PREV_CAND=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 阶段A实现 收工')                       # C1 已核的候选 1
RW_CODE=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 C1返工 代码候选')                         # 返工代码候选（全套与回放在其上执行，工作树干净）
RW_CAND=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 C1返工 收工')                             # 本停点新候选（送 C2/R1）
git diff --name-only "$BASE".."$RW_CAND"     # 完整候选文件集（含他角色提交，按真实 diff 核）
git diff "$BASE".."$RW_CAND"                 # 完整候选 diff
git diff "$PREV_CAND".."$RW_CODE"            # 返工增量（代码 + 测试 + 操作单）
git diff --stat "$RW_CODE".."$RW_CAND"       # 代码候选之后只有证据/状态文档
```

### 状态与结论（C1返工）

- C1-AC6、C1-AC7、C1-AC8（1–4）、C1-AC10 已按原条款与 IR 答复修复，逐条闭合指针见「C1 偏差逐条闭合」；PR-3 是真缺陷（生产序列下旧评分器把确认后追平终止的样本判成 `ATTRIBUTION_CONFLICT(C5)`），已随 AC-8 修订 2 修复并以真实会话生产序列回归；PR-1/2/5/6 处置见「预复核关注项处置」。
- 新候选停点全套 1 次（累计 2/3）：`Ran 2300 / failures 4 / errors 9 / skipped 19`，**13 项与候选 1 全套逐名相同（均为基线既有），本批新增失败 0**（`docs/evidence/P1-ENG-LOOP-002-tests-rework1.log`）。加载计数与候选 1 同型，按用户已认可的 N1-LOAD-RECONCILE 口径为真实 cv2 CSRT 尝试 2/实例 0。
- 归档回放（本候选）1/2：`-archive-dryrun-rework1.json` 39 项对照与候选 1 逐项相等（唯一不一致仍为 IR-1 已裁的描述读数），旧两归档评分时刻全部来自真值行（`frames_without_truth_time` = 0）。
- AC-14、AC-15、AC-18 与 AC-16 板端部分 = `NOT_RUN`（阶段 B 未签）；不申请 `UNITY_NA`。下一步：Acceptance `C2@K1K2K3K4` 只读核对（C1 首退已用，核对后照交新鲜上下文 `R1@K1K2K3K4`，不再退回）。

### 稳定候选四条件自证（C1返工）

workflow §4.3.1 四项，按 AC-n 附指针：

1. **实现范围与接口冻结**：成立。返工只动 §4.1 功能闭集内 `controller/language_bridge.py`、`controller/language_loop.py`、`tools/language_latency.py`、`tools/language_serve.py`、`tools/eng_loop2/analyze_play.py` 与闭集内 5 个测试文件、操作单 `-play-ops.md`（`git diff --name-only "$PREV_CAND".."$RW_CODE"`）；接口变化只有：`language_serve` 计量日志字段扩充（见 IR-15）、`analyze_play score` 输出 schema `p1-eng-loop-002-four-numbers/v2`（按真值来源分列，C1-AC8-4）。新增读法列为 IR-13…17（「待裁定（C1返工新增）」），不自行扩合同。
2. **相称测试通过**：成立（带基线失败）。focused（系统 `python3 -m unittest`，开发期）：`test_language_loop` 205 OK（2 skip）、`test_language_bridge` 50 OK、`test_language_latency` 18 OK、`test_llama_server_adapter` 36 OK、`test_eng_loop2_analyze` 63 OK、`test_loop2_isolation` 3 OK、`test_loop2_freeze` 3 OK、`test_language_selector` 61 OK（1 skip）、`test_language_k_binding` 13 OK。每条偏差的修前红/修后绿见下节。停点全套 1 次：新增失败 0。
3. **已知 Unity 失败**：不适用（零 Unity、零 Play）。
4. **复核范围、状态板、候选提交与未验证风险已更新**：本节、状态板交接行（Owner Acceptance，Status `AWAITING_ACCEPTANCE_C2`，Progress 含 `C1返工`）、候选提交（`$RW_CODE` 代码、`$RW_CAND` 收工，均已推送）、「复核范围（C1返工）」「未验证项与已知限制（C1返工）」。

### AC-n 逐条证据指针（C1返工候选）

| AC | 结论 | 证据指针 |
|---|---|---|
| AC-1/2/3/4/5/9/11/12/17 | 满足（C1 已判满足；本轮相关代码路径未改，回归仍绿） | 同候选 1 指针（下文「候选 1 记录」AC 表）；本轮全套与 focused 全绿；`language_loop.py` 本轮只改 `code_git_state`（AC-6）；`LanguageWorker`/`CandidatesBackend`/`_validate_candidates_source`/`render_preview`/`_preview` 与 `$BASE` 的 AST 源码段仍逐字相同、`candidates_preflight.py` diff 空（cmd 同 AC-11） |
| AC-6 | 修复，待 C2 核对 | test: `tests/test_language_latency.py::CleanWorkingTreeProductionPathTests`（真实临时 git 仓库、不注入 `git_state`：tests/ 修改、文档修改、tests/ 未跟踪文件、config 修改均判脏，忽略的 `runtime/`/`outputs/` 不计；`k-receipt` 生成器、`measure` 报告字段、会话启动三条生产路径各自拒绝，拒绝在建会话目录之前）；`tests/test_language_bridge.py::Loop2BridgeTests.test_llama_key_present_with_null_value_is_not_absent`（六键任一以 `null` 出现即按全有/全无与类型拒绝，`_validate_model_block` 同；六键全无旧块照常）；既有 AC-6 用例未改且通过 |
| AC-7（含修订 1） | 修复，待 C2 核对 | test: `tests/test_llama_server_adapter.py::AccessLogEveryRequestTests`（坏请求行 400/505 三例、头部过多 431、未支持方法 PUT 501、未知 POST 路径 404、Content-Length 不可解析、短正文、畸形 multipart/正常 GET/未知 GET、处理异常、local-hf 无计量且旧语义不变）；`IsolatedDeployEntryTests.test_isolated_root_serves_query_then_releases_ports_without_residue`（真实子进程 `-I -S` 临时源码根，访问日志键集扩为 12 键、逐请求字节与客户端实测相等、`request_body_complete` 真、`error` 空） |
| AC-8（含修订 1/2） | 修复，待 C2 核对 | test: `tests/test_eng_loop2_analyze.py::ReworkC1AC8Tests`（10 例，C1-AC8 (1)–(4) 与 PR-3/4/5）、`tests/test_language_loop.py::Loop2ScorerProductionSequenceTests`（2 例，真实 `LanguageSession` 生产的 JSONL/results 喂评分器）；既有 53 例改为按真值来源取表后全绿（误锁时长断言由「65 或 66」收紧为按闭端点判据精确计算）；artifact: `docs/evidence/P1-ENG-LOOP-002-four-numbers-fixture-rework1.json`（schema v2、三来源分列与守恒、静止车 CENTERED 样本带 `time_to_center_from_f_p_s`/`from_h_s`）、`docs/evidence/P1-ENG-LOOP-002-archive-dryrun-rework1.json` |
| AC-10 | 修复，待 C2 核对 | artifact: `docs/evidence/P1-ENG-LOOP-002-play-ops.md` §1.1（命令块：取最后一条 `passed_candidate` 且须位于最后一条 `round_candidate` 之后，HEAD 须等于它，打印 `RELEASE_CHECK_1_1_OK` 才过；不再用 `grep -m1`）、§1.2（整个工作树干净，与会话/收据同口径）、§9（P1/P2/P3 每条命令全部参数逐字写出，`confirm`/`reject`/`release`/`stop` 齐全，令牌由只读函数运行时解析）、§11 有效载荷行 |
| AC-13 | 满足（本候选） | artifact: `docs/evidence/P1-ENG-LOOP-002-tests-rework1.log`；cmd: `git diff --stat "$BASE".."$RW_CAND"`；`tests/test_loop2_freeze.py`（闭集外 PLAY_GOVERNING 无 diff）通过 |
| AC-14/15/18 | `NOT_RUN` | 阶段 B 未签；AC-18 轮次名见 IR-13 |
| AC-16 | 阶段 A 部分满足（未改）；板端 `NOT_RUN` | `-assets-local.json` 未变 |

### C1 偏差逐条闭合

| 偏差 | 修复（代码落点） | 证据 |
|---|---|---|
| C1-AC6 干净工作树 | `controller/language_loop.py::code_git_state` 改为整个工作树 `git status --porcelain --untracked-files=normal`（显式覆盖用户 `status.showUntrackedFiles`），删去 `CODE_PATHS` 过滤；`tools/language_latency.py` 两处复用同一函数，提示文字改为「工作树」 | `CleanWorkingTreeProductionPathTests` 三例（修前 9 子例 FAIL） |
| C1-AC6 六键「出现」 | `controller/language_bridge.py::validate_llama_identity` 以 `key in value` 判出现/缺失；`null` 随后由 hex64/闭集/构建号校验拒绝 | `test_llama_key_present_with_null_value_is_not_absent`（修前 10 子例 FAIL） |
| C1-AC7 访问日志逐请求 | `tools/language_serve.py`：计量模式（`--access-log` 给出时）以计数包装 `rfile`/`wfile`，在 `handle_one_request` 的 `finally` 中逐请求落一行；头/体边界取 `parse_request`/`end_headers` 时刻的实际字节；状态码取 `send_response`；响应后对客户端已声明而未读的正文有界读走计数（≤ 64 MiB、10 s 超时）；Content-Length 不可解析 → 400 并关连接、`request_body_complete:false`；未知 POST 路径先读正文再 404；不保存正文；`local-hf` 分支（无 `--access-log`）读写与回包逐字不变 | `AccessLogEveryRequestTests` 9 例 + 隔离子进程用例（修前 4 FAIL + 7 ERROR） |
| C1-AC8-1 时刻来源 | `analyze_play.Scorer._index_frames/sim`：只取真值行时刻；`intent_pose` 无真值时刻 → `NO_POSE`；窗口按帧轴切分（`split_at_time`，首个已知时刻越过窗尾的帧起为窗外，闭端点），未知时刻帧留在窗内按 `NO_POSE` 据实排除；存活/误锁/time-to-center 不再用段日志时刻；E 无真值时刻时按 IR-14 处理；输出 `frame_time_source`（段日志时刻只作诊断计数，`segment_log_time_used_for_numbers:false`） | `test_segment_time_never_substitutes_missing_truth_time`、`test_end_frame_without_truth_time_is_not_censored_by_segment_time` |
| C1-AC8-2 指针归属 | `_attribute_downstream`：锚点（BOUND 的 `designation` 或同复合键 `acquire_adopted`）之后**紧随**、同 e_s 且同常驻代的 `pointer_bound` 才归 s；遇其他指定去向/采纳/受理样本行/`TERMINAL`/`resident_loop_started`/epoch 改变即止；同一行不被两个样本占用（`pointer_bound_claim_conflicts`）；未归属计 `unattributed_rows.pointer_bound`；逐样本输出 `pointer_epochs` | `test_pointer_bound_is_not_borrowed_from_another_generation`、`test_pointer_bound_after_other_sample_designation_is_not_borrowed`、`test_two_generations_reuse_designation_id_each_keep_own_pointer`、生产序列 `test_rebuilt_generation_reuses_designation_id_without_c6_or_cross_pointer` |
| C1-AC8-3 time-to-center 输出 | `time_to_center` 返回结局 + `center_run_start_frame` + `time_to_center_from_f_p_s`/`from_h_s`；数字三表 `time_to_center` 输出三结局计数与两组时长（n、无真值时刻数、中位、逐值）；`time_to_bind_s` 同；逐样本 `capture` 全量输出 | `test_time_to_center_durations_are_output`、`test_time_to_center_not_reached_and_censored`；`-four-numbers-fixture-rework1.json` |
| C1-AC8-4 来源分列 | `report()` 重构：数字一/二/三/误锁/显式比例（漏斗口径）全部 `by_truth_source` ∈ {`red_car_unity_truth`, `static_vehicle_geometry_approx`, `intent_not_valid`}，各列原始 n 与分母；顶层只留守恒（`n_raw_total` = 各来源之和，不等即抛 `ConservationError`），无合并计数/比率；ACQ §3.10 口径只用运行时六值去向，不涉真值，保持整体并标 `truth_used:false`；漏斗/冲突/意图守恒不变 | `test_red_car_and_static_numbers_are_reported_separately`；既有 53 例改按来源取表 |
| C1-AC10 逐字命令 | 见 AC-10 行 | `-play-ops.md` §1.1/§1.2/§9/§11；§1.1 命令块在 zsh 与 bash 下对两份合成复核文件（末轮未通过 / 末轮通过）分别得 NOT_OK / `RELEASE_CHECK_1_1_OK`；§9 取值函数对测试会话 runtime 取到的 token 与会话内存值相等（会话临时目录内一次性核对，未入仓） |

### 预复核关注项处置（PR-1…6）

- **PR-1（AC-7 临时图像清理）**：未改代码。读码依据：llama 分支 `HTTPServer.handle_request` 在主线程串行处理，循环退出后无在途 handler；`SingleFlightRuntime.submit` 在锁内写图后起模型线程，线程只读图并在 `finally` 删除；退出路径先停 `llama-server` 子进程使在途请求失败，再 `rmtree` 图像目录（线程随后的 `unlink(missing_ok=True)` 无副作用）；访问日志写失败不产生图像文件。夹具仍只证明已完成请求与前台退出；在途中退出的真实时序留复核。
- **PR-2（AC-5 到期 tick 竞争）**：未改代码。读法：同一 tick 中 Δ 到期时，新命令尚在请求槽、未经 `_consume_request` 受理；合同「挂起中新受理命令丢弃」以受理为界，故先呈现后受理不违反字面。是否需调序属 AC-5 释义，AC-5 已判满足，本轮不改，留复核。
- **PR-3（AC-8 修订 2 生产归属）**：**确认缺陷并修复**：`stop()` 先增 epoch 再写 `designation_unavailable(session_terminal)`，旧评分器按行 epoch 归属失败 → 该样本 C5 冲突。修复：不可用行 epoch 不属任何样本时，沿其前最近的受理 `confirm` 归回原 e_s（二者之间只允许 `TERMINAL`，否则不归；计 `designation_unavailable_reattributed_to_confirm_epoch`）。生产序列回归 `Loop2ScorerProductionSequenceTests.test_confirm_then_catchup_terminal_keeps_unavailable_with_its_sample`（修前 `ATTRIBUTION_CONFLICT(C5)`）。
- **PR-4（AC-8 修订 1 两代编号）**：真实会话两代均从 1 编号，评分无 C6、各样本只得本代指针（生产序列回归）；跨代借指针由合成回归覆盖。F8/H-2 债不因此关闭。
- **PR-5（13 s 闭端点等）**：窗口统一由 `split_at_time` 以「已知时刻 > 窗尾才出窗」切分（闭端点，不加容差）；误锁时长断言改为按同一判据精确计数；time-to-center 增闭端点确定性用例（连续段末帧恰在 f_p+13 s 计 CENTERED，晚一帧 NOT_REACHED）；空窗显式排除与布局排除后显式失败独立计数逻辑未改。
- **PR-6（轮次/AC-18）**：本轮不改 AC-18；轮号冲突列 IR-13 交接受裁定。

### 修前红/修后绿（具名回归；修前 = 只回退对应生产文件、保留新测试）

| 回退文件 | 运行 | 修前 | 修后 |
|---|---|---|---|
| `controller/language_bridge.py` | `python3 -m unittest tests.test_language_bridge` | `test_llama_key_present_with_null_value_is_not_absent` 10 子例 FAIL | 50 OK |
| `controller/language_loop.py` + `tools/language_latency.py` | `python3 -m unittest tests.test_language_latency` | `CleanWorkingTreeProductionPathTests` 9 子例 FAIL | 18 OK |
| `tools/language_serve.py` | `python3 -m unittest tests.test_llama_server_adapter` | 4 FAIL + 7 ERROR（新增 9 例中 8 例失败，坏请求行用例 3 个子例；另加隔离用例键集）；`test_local_hf_default_has_no_metering_and_old_semantics` 修前修后均过（旧语义不变） | 36 OK |
| `tools/eng_loop2/analyze_play.py` | `python3 -m unittest tests.test_eng_loop2_analyze.ReworkC1AC8Tests` | 2 FAIL + 10 ERROR | 10 OK |
| `tools/eng_loop2/analyze_play.py` | `python3 -m unittest tests.test_language_loop.Loop2ScorerProductionSequenceTests` | 1 FAIL（`ATTRIBUTION_CONFLICT(C5)`）+ 1 ERROR | 2 OK |

### 停点全套（C1返工候选，AC-13）

命令（工作树干净，HEAD = `$RW_CODE`）：`env -u ENG_DET_DATA_ROOT YOLO_OFFLINE=true YOLO_AUTOINSTALL=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LOOP2_COUNTS_OUT=<会话临时目录>/LOOP2_COUNTS-rework1.json /usr/bin/time -l .venv-yoloe/bin/python <计数包装> > docs/evidence/P1-ENG-LOOP-002-tests-rework1.log 2>&1`；计数包装与候选 1 逐字相同（源码见下文「候选 1 记录 · 停点全套」末，从本文件原样抽出执行，不入仓）。

结果：`Ran 2300 tests in 186.513s — FAILED (failures=4, errors=9, skipped=19)`，退出 1；2026-10-07T01:51:52Z–01:55:03Z，`/usr/bin/time` real 191.32 s，峰值 RSS 1,000,144,896 B。失败集合（`^(FAIL|ERROR): ` 行排序后）与候选 1 的 `-tests.log` **逐行相同**（13 项：`test_dist_data_round8` ×2、`tests` 包遮蔽 5 个模块、`test_rate3_protocol` 1、两 CSRT、`test_dist_data_round4` ×3），归类与依据同候选 1 表。**本批新增失败：0**。测试数 2275 → 2300 = 本轮新增 25 个用例。

### §5.1 累计用量（N-1 信封；首签额度内，不转用他项）

| 维度 | 上限 | 候选 1 | C1返工候选 | 累计 |
|---|---|---|---|---|
| 停点全套 | 每候选 1、≤ 3 候选 | 1 | **1** | **2/3** |
| NanoTrack-v2 ONNX 构造 | ≤ 2/次 | 2 | **2**（插桩） | — |
| det-assoc 检测器加载 | 0 | 0 | **0**（插桩） | 0 |
| CSRT 尝试/实例 | 真实 ≤ 2/0 | 原始 6/5 → 真实 2/0 | 原始 6/5 → 真实 **2/0**（同 N1-LOAD-RECONCILE 已认可拆分：5 次替身模块 + 进程内 1 + 子进程 1；本机 cv2 无 `TrackerCSRT_create`） | — |
| YOLOE/DINOv2/VLM/HF | 0 | 0（静态口径） | 0（未插桩；无下载/加载输出；`transformers`/`onnxruntime` 未导入，`torch`/`ultralytics` 仅导入） | 0 |
| 零模型归档回放 | 每候选 ≤ 2 | 2/2 | **1/2**（`archive-dryrun` 2026-10-07T01:55:18Z–01:55:26Z，退出 0，HEAD = `$RW_CODE`） | 3 |
| 墙钟 | ≤ 15 min/次 | 187 s | **191 s** | — |
| 新增磁盘（证据与夹具） | 阶段 A 总额 ≤ 20 MB | ≈ 0.15 MB | 新文件 85,243 B（`-tests-rework1.log` 26,765 + `-archive-dryrun-rework1.json` 22,512 + `-four-numbers-fixture-rework1.json` 35,966）+ 文档增量 | 本项证据合计 ≈ 0.24 MB |
| scenario/session/run ID、Play、VLM、板、5060、API、GPU、下载、pip | 0 | 0 | **0** | 0 |

旧工件（`-tests.log`、`-archive-dryrun.json`、`-four-numbers-fixture.json`）原样保留为候选 1 记录，未覆盖、未重计零。合成夹具工件 `-four-numbers-fixture-rework1.json` 由 `.venv-yoloe/bin/python tests/test_eng_loop2_analyze.py --write-evidence …` 生成，不读归档，不计回放。

### 待裁定（C1返工新增；实现角色对提案只读，写在此处交接受）

- **IR-13（PR-6 轮号）**：C1 首退后本次代码核对按规则为 `C2@K1K2K3K4`；AC-18 文字把阶段 B 证据只读核对也预记为 `C2@K1K2K3K4`。建议后续证据核对连续计数（如 `C3@K1K2K3K4`），AC-18 文字不改、只释义；请接受裁定。
- **IR-14（缺真值时刻的据实处理）**：存活：E 无真值时刻且 (f_p, E] 内无已知时刻 ≥ 窗尾 → 截尾不可判定，记 `TRUTH_GAP(no_pose)`（不以段日志时刻判 `CENSORED_END`）；time-to-center：已越过窗尾的帧存在或 sim(E) ≥ 窗尾 → `CENTER_NOT_REACHED`，否则（含 E 时刻未知）→ `CENTER_CENSORED`；Δ_eff、time-to-bind 端点缺真值 → `null`（Δ 桶 `NO_POSE`）；窗口内未知时刻帧按 `NO_POSE` 处理。
- **IR-15（计量日志字段与计量模式行为）**：每行 12 键：`method`、`path`、`status`、`request_head_bytes`、`request_body_bytes`、`request_declared_body_bytes`、`request_body_complete`、`response_head_bytes`、`response_body_bytes`、`error`、`started_unix_s`、`finished_unix_s`；§5.2 有效载荷 = `request_body_bytes + response_body_bytes` 之和（实际读写字节，不以声明长度补）。请求行不可解析时 Python 按 HTTP/0.9 回包（无响应头），日志如实记 0 头字节；头部超限（431）时服务端未读完的请求头字节不可计，`request_body_complete:false` 标出。计量模式下 Content-Length 不可解析由原「处理异常断连」改为 400 + 关连接；未知 POST 路径先读正文再 404——仅 llama 分支，local-hf 不变。
- **IR-16（不可用行归属）**：`designation_unavailable` 行 epoch 不属任何样本时，沿其前最近受理 `confirm` 归回该 confirm 的 epoch，条件是二者之间至少一行 `TERMINAL` 且无受理样本行/`designation`/`designation_unavailable`；其余仍按行 epoch 或计未归属。
- **IR-17（「干净」含未跟踪文件）**：未被 `.gitignore` 忽略的未跟踪文件（任意目录）也判脏；操作单 §1.2 同口径。

### 改动文件（C1返工；`git diff --name-only "$PREV_CAND".."$RW_CAND"` 中本角色部分）

PLAY_GOVERNING（§4.1 功能闭集内）：`controller/language_bridge.py`、`controller/language_loop.py`、`tools/language_latency.py`、`tools/language_serve.py`、`tools/eng_loop2/analyze_play.py`；操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md`。测试（§4.1 内）：`tests/test_language_bridge.py`、`tests/test_language_latency.py`、`tests/test_llama_server_adapter.py`、`tests/test_eng_loop2_analyze.py`、`tests/test_language_loop.py`。证据：本文件、`-tests-rework1.log`、`-archive-dryrun-rework1.json`、`-four-numbers-fixture-rework1.json`；状态板 `docs/current-status.md`。同区间他角色提交（按真实 diff 核）：接受 C1 核对（提案、`-C1-K1K2K3K4.md`、正式设计、状态板）、supervisor 代录与派发登记（`docs/authorizations.md`、`supervisor-dispatch.jsonl`）。闭集外 PLAY_GOVERNING diff：无（`test_loop2_freeze` 机检）。`runtime/README.md` 本轮未改（计量日志在板端 `--access-log`，非 `runtime/` 文件）。

### 复核范围（C2@K1K2K3K4 只读核对后照交 R1@K1K2K3K4）

完整候选 `git diff "$BASE".."$RW_CAND"`（重读候选 1 全部内容）与返工增量 `git diff "$PREV_CAND".."$RW_CODE"`；重点：`code_git_state` 与三条调用路径、`validate_llama_identity`、`LanguageRequestHandler` 计量路径（`setup`/`handle_one_request`/`parse_request`/`end_headers`/`_drain_declared_body`/`do_POST` 两分支）、`Scorer` 的 `split_at_time`/`survival`/`time_to_center`/`mislock_duration`/`_attribute_downstream`/`_own_pointer_bound`/`_unavailable_origin_epoch`/`report` 分列与守恒、操作单 §1.1/§9；连同 C1 文件「预复核关注项」PR-1/2 的读码结论与 IR-13…17。跟踪器相关复核重跑须用数据根解释器（本机不存在，见下）。

### 未验证项与已知限制（C1返工）

- **跟踪器相关 focused 阻塞（照旧）**：账本 2026-09-29 约定的 `~/TetheredDroneTracking-full/.venv-yoloe` 在本机不存在（本轮 `ls` 复核）；未安装、未改约定；跟踪器测试只在 N-1 停点全套中以仓库 `.venv-yoloe` 跑过（基线 CSRT 失败同前）。本轮未改 `trackers.py`/`det_assoc_tracker.py`/`track_loop.py`。
- 计量路径只在回环 HTTP/1.0 夹具与隔离子进程验证；板端真实流量、Tailscale 下的半包/断连时序未验证（阶段 B）。
- 评分器新逻辑只在合成夹具、真实会话生产序列（替身跟踪器/适配器）与两份旧归档上运行；新 Play 归档未有。
- 操作单 §9 取值函数只对测试会话 runtime 验证过一次（会话临时目录内），真实 Play 时 `last_result` 可能被核验结果覆盖——断言会拦下并照记，但未在真实会话中演练。
- 其余同候选 1「未验证项与已知限制」。

---

## 候选 1 记录（登记轮次 `阶段A实现`；C1@K1K2K3K4 已核并首次退回；以下原文保留，不作现行自证）

**派生标识一律运行时解析（不写死）：**

```bash
# 基线 = 派发块 base_head（N-1 答复落实核销提交）= 本轮开工提交之前的 P1-ENG-LOOP-002 提交
BASE=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 N-1答复落实 supervisor 核销' | head -n 1)
# 代码候选（全套在其上执行，工作树干净）
CODE=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 阶段A实现 代码候选')
# 停点候选（送 C1/R1）= 唯一收工提交（触及本文件、已推送）
CAND=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 阶段A实现 收工')
git diff --name-only "$BASE".."$CAND"   # 完整候选文件集（含 supervisor 派发日志等他角色提交，按真实 diff 核）
git diff "$BASE".."$CAND"               # 完整候选 diff
git diff --stat "$CODE".."$CAND"        # 代码候选之后只有证据/状态文档
```

## 候选 1 状态与结论（原文）

- 阶段 A 代码候选已在 §4.1 文件闭集内实现（A1–A9），停点全套已按 N-1 跑 **1 次**（≤ 3 候选中的第 1 个候选），结果 `Ran 2275 / failures 4 / errors 9 / skipped 19`，**13 项全部为基线既有失败、本批新增失败 0**（见「停点全套」）。
- §5.1 首次全套实际加载核对：插桩原始计数 `nanotrack 2 / det-assoc 0 / csrt_attempts 6 / csrt_instances 5`；按调用对象拆分后真实 cv2 的 CSRT = 尝试 2、实例 0，与静态清单一致（拆分依据见「§5.1 实际用量」）。**因原始计数字面与清单不同，此判读列为 needs_user N1-LOAD-RECONCILE 交用户确认**；若用户认定属不符，按 N-1 条款本次全套作废、不补跑。
- A6 归档确认：41 项对照 40 项一致；唯一不一致是 §8 描述性读数「只以车辆为遮挡体 attempt 2 末段静止机位 6 辆恒 OK」实测 7 辆恒 OK（全 1500 帧口径）。实现判读：不属于 §3.5.1 输入 schema 字段缺失/改名或绑定失败率矛盾，故未按 A6 停止；**请接受先裁定 IR-1 再开 `C1`**（若裁为合同不符则走合同修订，C1 不补合同）。
- B/C 派生 = 2 辆（`Vehicle_SUV_color01 (1)` "the suv"、`Vehicle_Taxi (2)` "the taxi"），与 F27 一致，未触发 < 2 辆即停。
- AC-14、AC-15、AC-18 与 AC-16 板端部分 = `NOT_RUN`（阶段 B 未签）；不申请 `UNITY_NA`。

## 稳定候选四条件自证（候选 1，原文）

workflow §4.3.1 四项（工程轨道按 AC-n 附指针）：

1. **实现范围与接口冻结**：成立。§2.1 A1–A9 全部实现于 §4.1 功能闭集（`git diff --name-only "$BASE".."$CODE"` 见「改动文件」）；接口：`run --body-policy`、`ask/respecify --delay-s --intent`、`k-receipt --single-host jetson --report`、`measure --host jetson`、`language_serve --backend llama-server`、`analyze_play {score,archive-dryrun,derive-bc}`；合同未写清处列为 IR-1…IR-12（「待裁定」），不自行扩大合同。
2. **相称测试通过**：成立（带基线失败）。focused：`test_language_loop` 203 OK（除工作树依赖的 `test_frozen_paths_are_untouched_in_the_working_tree` 在未提交时必失败、提交后全套中通过）、`test_language_bridge` 49 OK、`test_language_latency` 15 OK、`test_llama_server_adapter` 27 OK、`test_eng_loop2_analyze` 53 OK、`test_loop2_isolation` 3 OK、`test_loop2_freeze` 3 OK、`test_language_selector` 61 OK、`test_language_k_binding` 13 OK（系统 `python3`；`.venv-yoloe` 下为基线既有导入遮蔽错误）。停点全套 1 次：`docs/evidence/P1-ENG-LOOP-002-tests.log`，新增失败 0。
3. **已知 Unity 失败**：不适用（零 Unity、零 Play）。
4. **复核范围、状态板、候选提交与未验证风险已更新**：本文件、状态板交接行（Status `AWAITING_ACCEPTANCE_C1`，Progress 含 `阶段A实现`）、候选提交（`$CODE` 代码、`$CAND` 收工）、未验证项见「未验证项与已知限制」。

### AC-n 逐条证据指针

| AC | 停点 | 结论 | 证据指针 |
|---|---|---|---|
| AC-1 | K2 | 满足 | test: `tests/test_language_loop.py::Loop2BodyPolicyTests`（standoff 构造间谍、`runtime=` 已传、manifest `body_planner.name`=`standoff-band-v1` 与 `config_sha256` 运行时 sha；缺覆盖文件拒绝；body 场景不逐值相等拒绝；反例：缺省 threshold 无覆盖 → default、`bind_body_runtime`/`_build_body_runtime` 实参与旧调用一致、身份块无 `name`；CLI 闭集）；`controller/scenario_tether.py` diff 空（test_loop2_freeze） |
| AC-2 | K2 | 满足 | test: 停点全套（threshold/段式既有用例未改且通过，`test_language_loop` 既有 178 例全过）；`tests/test_loop2_freeze.py::Loop2FreezeTests.test_frozen_files_are_byte_identical_to_the_baseline`（6 个冻结件 sha 运行时取自 `$BASE`） |
| AC-3 | K3 | 满足 | test: `tests/test_language_loop.py::Loop2SingleLoadTests`（`duration_reached`→`TERMINAL` 不重建；`backend_fatal`→`TERMINAL`；`frame_gap` 两次重建复用同一缓存加载器、底层加载 1 次，第 3 次 → `TERMINAL(rebuild_limit)`；每段 `model_cache.json` 落盘 `model_loads=1`） |
| AC-4 | K2（收据格式 K1，(l)） | 满足 | test: `tests/test_language_loop.py::Loop2ContractTests`（三种显式 hold 收据 `loop_start/acquiring/acquire_failed`；段式路径显式 hold 仍无收据；无观测帧无 WRITTEN 速度；SUSPECTED ok/不 ok 两分支与核验暂停；丢失后无自动 ask；`JOURNAL_KINDS` 覆盖全部 `_journal` 调用点（AST）与 `resident_core` 事件名、闭集外抛错）；§3.4 其余行由 ACQ 既有用例覆盖（`ResidentSessionTests` 全过） |
| AC-5 | K1 | 满足 | test: `tests/test_language_loop.py::Loop2DelayTests`（恰延 Δ、事件字段含 `status`/`head_frame_id`、挂起中 `QUERYING`、confirm `REQUEST_INVALID(confirm_in_QUERYING)`、结果行与迁移在呈现时；失败/重试不挂起；挂起中新 ask/respecify/stop 丢弃不写结果行；越过确认检查点按现行 `wall_deadline_exceeded` 并带 `delay_injected_s`；Δ 越界/类型错与空 intent 拒绝；CLI `--delay-s` 域；`intent` 不进查询/状态/结果；`frames_processed.metadata_sha256` 同序等于文件字节 sha、缺失 → `null`+`file_missing`）；`LanguageWorker` 源码与基线 AST 相同（cmd 见 AC-11） |
| AC-6 | K1 | 满足 | test: `tests/test_language_latency.py`（`SingleHostReceiptTests` 生成器与 0/6/8 退出码、逐项拒绝；`JetsonMeasurementTests` 身份只取 `/status`、失败行不过滤；`JetsonSessionStartTests` §3.2 每项错配拒绝且在建目录前；`ModelBlockCompatibilityTests` 六键全无旧块照常）；`tests/test_language_bridge.py::Loop2BridgeTests`（六键类型/值域）；`tests/test_language_k_binding.py` 13 例未改且通过（系统 python3） |
| AC-7 | K3 | 满足 | test: `tests/test_llama_server_adapter.py`（`RequestBodyTests`、`ResponseMappingTests`、`StartupRefusalTests`、`DeployDigestTests`、`IsolatedDeployEntryTests`（`-I -S` 临时源码根前台子进程、端口释放、无残留、访问日志字节）、`TruthIsolationTests`） |
| AC-8 | K4 | 满足（IR-1/IR-2 待裁） | test: `tests/test_eng_loop2_analyze.py`（53 例，AC-8 子项逐条对应见下表）；artifact: `docs/evidence/P1-ENG-LOOP-002-four-numbers-fixture.json`、`docs/evidence/P1-ENG-LOOP-002-archive-dryrun.json` |
| AC-9 | K3 | 满足 | test: `tests/test_loop2_isolation.py`（controller→tools 恰为五项闭集且五项都出现；controller 与部署侧不导入真值/评分闭集、无 `m3_body_truth`/`CoverageEvaluator` 记号；`intent` 只出现在请求解析/回执/CLI 函数）；既有 `test_eng_acq_guards.py` 未改且通过 |
| AC-10 | K1 | 满足（阶段 A 只备单） | artifact: `docs/evidence/P1-ENG-LOOP-002-play-ops.md`（§3.6 节闭集 1–13：放行核对、B0a 引用、B0b、覆盖文件与 sha、板上服务前台起停与端口释放、K 收据、三剧本逐字命令与 `T_sess`、B/C 派生输出与 < 2 辆即停、只凭预览规则、计次、记录模板（墙钟/末帧/体积/有效载荷/峰值磁盘）、归档含场景副本、§6.2 STOP 表） |
| AC-11 | K3 | 满足 | artifact: 本文件「承接声明」；cmd: `git diff --stat "$BASE".."$CAND" -- tools/eng_acq/candidates_preflight.py` 为空；`LanguageWorker`/`CandidatesBackend`/`_validate_candidates_source`/`render_preview`/`_preview` 在 `$BASE` 与 `$CAND` 的 AST 源码段逐字相同（复核可用 `ast.get_source_segment` 对比） |
| AC-12 | K2 | 满足 | test: `tests/test_loop2_freeze.py::Loop2FreezeTests.test_fence_reading_code_has_no_diff`；FRAME-001 R1-3 账本行未改 |
| AC-13 | K1K2K3K4 | 满足 | artifact: `docs/evidence/P1-ENG-LOOP-002-tests.log`（基线/新增分列见「停点全套」）；cmd: `git diff --stat "$BASE".."$CAND"`；`tests/test_loop2_freeze.py::test_play_governing_paths_outside_the_ownership_table_have_no_diff`；闭集外 diff 逐文件说明见「改动文件」 |
| AC-14 | K1K2K3K4 | `NOT_RUN` | 阶段 B 未签 |
| AC-15 | K1 | `NOT_RUN` | 阶段 B 未签（生产路径已就绪：AC-6） |
| AC-16 | K3 | 阶段 A 部分满足；板端 `NOT_RUN` | artifact: `docs/evidence/P1-ENG-LOOP-002-assets-local.json`（检测器权重 sha/大小与 spec 钉住值相符、`freeze.json`、FRAME body 配置钉住件相符；只哈希、零加载）；未引用 JET-001 诊断读数 |
| AC-17 | K1 | 满足 | test: `tests/test_language_loop.py::Loop2ContractTests.test_geometry_rejected_is_its_own_cause_not_slew_timeout`；`test_language_bridge.py::Loop2BridgeTests.test_state_reasons_appended_without_reordering` |
| AC-18 | K1K2K3K4 | `NOT_RUN` | 阶段 B 后 |

### AC-8 子项 → 具名测试（`tests/test_eng_loop2_analyze.py`）

十二类守恒 `FunnelTests.test_twelve_classes_each_once_and_conservation` / `test_conservation_violation_raises`；查询未返回四种终止 `test_query_pending_{stop_with,stop_without}_worker_abandoned`、`test_query_pending_duration_reached`、`test_query_pending_backend_fatal_without_result_row`、`test_query_pending_log_truncated_without_terminal`；呈现挂起 `test_presentation_pending_stop_and_new_ask`；三种被替换 `test_query_pending_superseded_in_flight_queued_and_waiting`；`test_designation_unavailable_interrupted`；重试 `test_retry_paths`；`request_id` 异形 `test_null_request_id_retry_and_confirm_request_id_stale_row_attributed`；`test_request_invalid_is_not_a_sample`；`test_unattributed_design_rows`；`test_duplicate_coasting_rows_counted_once`；C1–C6 `ConflictTests.*`；意图 `IntentAndNumberTests.test_no_intent_and_intent_unknown_in_funnel_not_in_denominators`；静默错误 `test_silent_error_counted_once`；分母 `test_rates_zero_denominator_and_insufficient_n`、`test_capture_timeout_and_acquire_failed`；`test_no_pose_and_invisible_reported_separately`；存活 `SurvivalTests.*`（KEPT/UNBOUND_START/CENSORED_END/三种 TRUTH_GAP/ID_SWITCH/LOST_BEYOND_BUFFER/尾延伸三例/窗口外 NO_POSE/track_id 变化/守恒与差异）；布局 `LayoutAndIdentityTests.test_layout_*`（相等时间谍断言不调用 `apply_layout`）；H-2 `test_h2_tamper_{basis_vectors,intrinsics,position_within_tolerance}`、`test_h2_runtime_digest_null_is_metadata_unbound`、`test_h2_result_frame_sha_against_session_ring`；`test_red_car_blocker_depth`；归档可运行 `ArchiveDryrunSmokeTests` + 真实运行。

### K 触发覆盖

- **K1**：jetson 单宿主收据/启动校验（AC-6）、Δ 注入与时间语义（AC-5，仿真帧轴只在评分器）、`model` 块六键（AC-6/7）、`STATE_REASONS` 追加（AC-3/17）、显式 hold 收据格式（AC-4，(l)）、请求体 `delay_s`/`intent` 可选字段（AC-5）。
- **K2**：standoff 接线（AC-1）、§3.4 机身/云台合同与 hold 收据（AC-4）、冻结件/围栏不变（AC-2/12）。
- **K3**：llama 适配器身份与解析、`c2q4-json-v1`（AC-7）、单加载与终止分类（AC-3）、R1-4 cause（AC-17）、隔离（AC-9）。
- **K4**：四类数字唯一算法与脚本（AC-8），归档试读（A6）。

## §5.1 实际用量（候选 1，N-1 信封逐维度）

| 维度 | 上限 | 实际 | 依据 |
|---|---|---|---|
| 执行机器 / 解释器 | MacBook Air；`.venv-yoloe` 只读，不装包，`ENG_DET_DATA_ROOT` 不设 | 同；全套环境 `ENG_DET_DATA_ROOT=null`，四个离线变量已设 | `-tests.log` 末 `LOOP2_COUNTS.env` |
| 停点全套 | 每候选 1 次、≤ 3 候选 | **1 次**（候选 1，执行版本 = `$CODE`，工作树干净） | `-tests.log` |
| NanoTrack-v2 ONNX 构造 | ≤ 2（静态 2） | **2**（插桩 `cv2.TrackerNano_create`；`test_trackers` 1 + `test_track_loop` 进程内 `nanotrack-cli` 1） | `LOOP2_COUNTS.nanotrack_onnx_constructions` |
| det-assoc 冻结检测器 CPU 加载 | 0 | **0**（插桩 `_default_model_loader`） | `LOOP2_COUNTS.det_assoc_detector_loads` |
| CSRT 构造尝试 / 实例 | 尝试 ≤ 2（静态 2）/ 实例 0 | 插桩原始：尝试 6 / 返回 5。拆分：5 次为 `tests/test_trackers.py` 的 `Cv2Stub`/`LegacyCv2Stub` 替身模块（行 199/213/217 经 `CsrtTracker.init`，行 224/225 直接调用；返回的是替身对象，非 OpenCV 构造）；真实 cv2：进程内 1 次（行 363 `test_pinned_opencv_csrt_initializes_and_updates`）+ 子进程 1 次（`test_track_loop.py` 行 693 起 `test_cli_runs_pinned_csrt_to_a_versioned_summary` 的 `subprocess.run`，插桩不到，失败栈见 `-tests.log`）= **尝试 2、实例 0**（本机 `cv2` 5.0.0 `hasattr(cv2,'TrackerCSRT_create')` 与 `cv2.legacy` 均 False，故真实实例必为 0） | `LOOP2_COUNTS.csrt_*`；needs_user N1-LOAD-RECONCILE |
| YOLOE/DINOv2/VLM/HF | 0 | 未插桩（§5.1 口径本为静态清单）；全套日志无下载/加载输出，离线变量已设；进程结束时 `torch`、`ultralytics` 模块已被导入（导入 ≠ 权重加载），`transformers`、`onnxruntime` 未导入 | `LOOP2_COUNTS.modules_present`；记为「未插桩，静态清单口径，无反证」 |
| 零模型数据回放 | 每候选 ≤ 2 | **2**（`archive-dryrun` 两次，每次覆盖两份归档：2026-10-06T23:44:43Z–23:44:50Z 退出 0；23:45:35Z–23:45:42Z 退出 0；第 1 次的输出被第 2 次覆盖，原因：红车像素差两读数按序比对误判，改为无序比对并补 §8 一项）。`derive-bc` 不读归档、另计 0。本候选回放额度已用尽 | 编码助手运行记录；`-archive-dryrun.json` `provenance` |
| 墙钟 | 每次全套 ≤ 15 min | **187 s**（2026-10-06T23:48:18Z–23:51:25Z；`/usr/bin/time` real 187.21 s，峰值 RSS 992,247,808 B） | `-tests.log` 末 |
| 新增磁盘（证据与夹具） | ≤ 20 MB（阶段 A 总额） | 本项 `docs/evidence/P1-ENG-LOOP-002-*` 合计约 0.1 MB；测试夹具全在临时目录 | `du -ch docs/evidence/P1-ENG-LOOP-002-*` |
| scenario/session/run ID、Play、VLM、板、5060、API、GPU、下载、pip | 0 | **0** | — |

## 停点全套（候选 1，AC-13）

命令（工作树干净，HEAD = `$CODE`）：`env -u ENG_DET_DATA_ROOT YOLO_OFFLINE=true YOLO_AUTOINSTALL=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /usr/bin/time -l .venv-yoloe/bin/python <计数包装> > docs/evidence/P1-ENG-LOOP-002-tests.log 2>&1`；计数包装只给 `cv2.TrackerNano_create`、`controller.trackers.create_csrt_backend`、`controller.det_assoc_tracker._default_model_loader` 加计数器后原样 `unittest.defaultTestLoader.discover("tests")`（无 `-v`、无过滤），不新增任何加载。包装脚本在会话临时目录、不入仓（源码逐字附于本节末）。

结果：`Ran 2275 tests in 182.623s — FAILED (failures=4, errors=9, skipped=19)`，退出 1。

| 失败 | 归类 | 依据 |
|---|---|---|
| `test_dist_data_round8.ScenarioBindingTest` ×2（ERROR） | 基线既有 | 本批未改该文件与 `tools/dist_data`；FRAME-001 R7 全套（`docs/evidence/P1-ENG-FRAME-001-R7-full-suite.log`）同名同类 |
| `test_eng_sft_{audit,build,cloud,evaluate}`、`test_language_k_binding`（loader `_FailedTest`） | 基线既有 | `.venv-yoloe` site-packages 内 ultralytics 携带同名 `tests` 包遮蔽仓库 `tests/` 的 `from tests.… import`；同 R7 日志；`test_language_k_binding` 本批未改，系统 `python3 -m unittest tests.test_language_k_binding` 13 例 OK |
| `test_rate3_protocol.Rate2ArchiveRegressionTests.test_archived_decision_a_recomputes_identically`（ERROR） | 基线既有 | 同 R7 日志；文件未改 |
| `test_trackers.TrackerAdapterTests.test_pinned_opencv_csrt_initializes_and_updates`（ERROR）、`test_track_loop.TrackLoopTests.test_cli_runs_pinned_csrt_to_a_versioned_summary`（FAIL） | 基线既有 | 本机 `opencv_python` 5.0 非 contrib 无 `TrackerCSRT_create`（§5.1 已列）；同 R7 日志 |
| `test_dist_data_round4.RealArchiveClosureTest` ×3（FAIL） | 基线既有 | 主树 `runtime/` 诊断残留使归档闭合测试必失败（已知坑）；同 R7 日志；文件未改 |

**本批新增失败：0**。R7 日志中的 `test_language_selector` HTTP 回环 ERROR 与三条 `listens_on_loopback`/`nonce`/`preview_endpoint` ERROR 本次均通过（环境差异，非本批修复）。基线未在 `$BASE` 上另跑全套（额度只有每候选 1 次）；「基线既有」以失败文件未改 + 同机历史全套同名失败为据。

计数包装源码（逐字）：

```python
"""P1-ENG-LOOP-002 阶段 A 停点全套：计数包装（只计数、不新增加载）后原样执行 `unittest discover -s tests`。

计数对象（§5.1 静态清单的可插桩部分）：
* NanoTrack-v2 ONNX 构造 = `cv2.TrackerNano_create` 调用次数；
* CSRT 构造尝试 = `controller.trackers.create_csrt_backend` 调用次数，实例 = 其成功返回次数；
* det-assoc 冻结检测器 CPU 加载 = `controller.det_assoc_tracker._default_model_loader` 调用次数；
* 另记结束时 `sys.modules` 里是否出现 torch/transformers/ultralytics/onnxruntime（导入 ≠ 加载，只作旁证）。
"""
import json, os, sys, time, unittest
from pathlib import Path
sys.path.insert(0, os.getcwd())  # 仓库根（与 `python -m unittest discover -s tests` 相同的导入根）
counts = {"nanotrack_onnx_constructions": 0, "csrt_attempts": 0, "csrt_instances": 0, "det_assoc_detector_loads": 0}
import cv2  # noqa: E402
_nano = getattr(cv2, "TrackerNano_create", None)
if _nano is not None:
    def _counted_nano(*a, **k):
        counts["nanotrack_onnx_constructions"] += 1
        return _nano(*a, **k)
    cv2.TrackerNano_create = _counted_nano
import controller.trackers as trackers  # noqa: E402
_csrt = trackers.create_csrt_backend
def _counted_csrt(*a, **k):
    counts["csrt_attempts"] += 1
    value = _csrt(*a, **k)
    counts["csrt_instances"] += 1
    return value
trackers.create_csrt_backend = _counted_csrt
import controller.det_assoc_tracker as det  # noqa: E402
_loader = det._default_model_loader
def _counted_loader(*a, **k):
    counts["det_assoc_detector_loads"] += 1
    return _loader(*a, **k)
det._default_model_loader = _counted_loader
started = time.time()
suite = unittest.defaultTestLoader.discover("tests")
result = unittest.TextTestRunner(verbosity=1).run(suite)
counts.update(
    wall_s=round(time.time() - started, 3),
    tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
    modules_present={name: name in sys.modules for name in ("torch", "transformers", "ultralytics", "onnxruntime")},
    env={k: os.environ.get(k) for k in ("YOLO_OFFLINE", "YOLO_AUTOINSTALL", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "ENG_DET_DATA_ROOT")},
)
Path(os.environ["LOOP2_COUNTS_OUT"]).write_text(json.dumps(counts, indent=2, sort_keys=True) + "\n")
print("LOOP2_COUNTS " + json.dumps(counts, sort_keys=True), file=sys.stderr)
sys.exit(0 if result.wasSuccessful() else 1)
```

## 承接声明（§2.5 H-1…H-12；AC-11）

| # | 处置 |
|---|---|
| H-1 LOOP-001 F3 | Δ 是会话侧呈现挂起，发生在 `_poll_worker` 取回 `QueryOutcome` 之后；`LanguageWorker` 类源码与 `$BASE` 逐字相同（AST）；测试 `Loop2DelayTests.test_presentation_waits_exactly_delta_and_worker_is_idle` 断言挂起期间 `worker.busy` 为假、`in_flight` 为空、不再调用适配器（`T_hard` 只对在途任务计时）。未触及 worker；账本原行保持 OPEN |
| H-2 LOOP-001 F8 | 运行时侧摘要 `frames_processed.metadata_sha256` 已加（只改 `language_loop.py`）；评分器 (1)–(4) 核验与三种篡改夹具见 AC-8；旧两归档无摘要 → 静止车一律 `metadata_unbound`，**不作 F8 承接证据**；只对新 Play 归档承接，F8 账本行由接受决定 |
| H-3 ACQ R1-4 | cause 改 `geometry_rejected`（追加入 `STATE_REASONS`）+ 回归 AC-17；被淘汰 k 帧路径沿现行 `FRAME_NOT_IN_HISTORY`（`l_replay_frames` 128 未改） |
| H-4 ACQ K1K3-R1-1 | 不触发：`CandidatesBackend`、`_validate_candidates_source`、`tools/eng_acq/candidates_preflight.py` diff 为空；账本行 OPEN 不变 |
| H-5 FRAME-001 R1-3 | 不触发：`controller/scenario_tether.py` diff 空（AC-12） |
| H-6 FAST-001 R1-2 | 评分器把空窗显式转成 `TRUTH_GAP(empty_window)`，不抛 `EmptyWindow`、不 `KEPT`（`SurvivalTests.test_empty_window_excluded_not_raised`）；`EMPTY_WINDOW_MAX_GAP_S` 8.0 照抄不 import（IR-9） |
| H-7 ACQ attempt 2 §7 | A5 单加载缓存 + 终止分类（AC-3）；操作单 §5.2 硬上限与 §6.2 STOP 表 |
| H-8 runtime 覆盖残留 | 操作单 B0b 第 1 步复核不存在、若存在只移入 `runtime/hold-acq-d1/` |
| H-9 ACQ AC-17 人眼保真 | **未触及**预览生成/保存代码：`render_preview` 与 `_preview` 源码与 `$BASE` 逐字相同；只把呈现步骤（含 `_preview` 调用）整体后移到 Δ 到期时；会话帧环/采集/保存路径未改。故不触发 Play 前重做 |
| H-10 清理清单 | 零删除；未触碰 5060 `repo-b`、`hold-diag-loopb-*` |
| H-11 FRAME-001 §9.1 | 即 A1：生效场景回退不改，`standoff` 要求显式覆盖文件 |
| H-12 JET-001 板上产物 | 未引用任何 JET-001 读数；板端 sha 核实留阶段 B（AC-16 板端 `NOT_RUN`） |

ACQ-001 非 verdict、AC-18 `NOT_RUN`、清理清单与旧余额原样保留。

## 待裁定（候选 1 的 IR-1…12；接受已在提案「待裁定答复」裁定）

- **IR-1（A6 归档确认的唯一不一致）**：§8 写「只以车辆为遮挡体时 attempt 2 末段静止机位有 7 辆车出现 `OK`（6 辆恒 `OK`）」；`archive-dryrun` 以「车辆 + 红车」为遮挡体、全 1500 帧口径实测**恒 OK 7 辆**（`Bus_color02 (1)`、`Pick up Truck_color02`、`SUV_color01 (4)`、`SUV_color03 (1)`、`Taxi (1)`、`Truck_color01`、`Truck_color02 (3)`）；「出现过 OK」的车辆数 7/6 及池内 1 辆与 §8 一致。该读数是 §8 的描述性试读，不是 §3.5.1 输入字段，也不影响池内 6 辆的状态分布（逐项一致）。实现判读为**非 schema 不符、未停止**；请接受裁定是否属 A6 停止条件（是则先合同修订再 C1）。
- **IR-2（评分器 designation_id 归属键）**：`ResidentCore` 每次常驻重建从 1 重新编号，按字面只用 `designation_id` 归属会在重建后误判 C6；评分器改以（常驻代 = 该行之前 `resident_loop_started` 行数，`designation_id`）为键，下游去重键（kind, 代, `designation_id`, `frame_id`）。偏离 §3.5.1 (ii)/(iii) C6 字面，请确认。
- **IR-3（评分器其余读法）**：编码助手逐条列出的读法（「按 sequence 先后」用文件行序；E 取该行之前最后 `frames_processed` 帧号；f_p 限于 s 的指针 epoch（`pointer_bound` 帧不含至同 `track_id` 的 `segment_retired.to_frame_id` 含）；30/52 帧窗口按帧号相加；捕获同帧优先级 f_p > acquire_failed > E > 截止；results.jsonl 与 JSONL 无共同行序，确认后过期行按 query_id/request_id 认定；C2 相邻两行都判冲突；C3 epoch 来源不含 `presentation_discarded`；`worker_abandoned` 标志取 L_s..X_s 区间；`coasting_timeout` 判据；布局未绑定的静止车意图样本在数字一/二/三/误锁第一步后紧接 `NOT_EVALUABLE(layout_*)`，数字二守恒式因此多一项；manifest 缺 `effective_scenario_sha256` 记 `layout_unbound`；H-2 判定顺序与无副本时跳过 (4) 计数；无真值行帧时刻退用段日志；偏轴/斜距分桶定义；time-to-center 两种起点并列；ACQ §3.10 口径分母；误锁收据过滤；13 s 窗端点浮点；`command_invalid` 键；意图闭集与非字符串记 `intent_unknown`；derive-bc 相机约定与描述只取对象名）均已实现为代码注释与测试，原文清单见编码助手交回（本轮会话）——接受核对时以 `tools/eng_loop2/analyze_play.py` 源码为准逐条确认。
- **IR-4（DECODE_CONFIG 定义位置）**：A2(d) 写「常量入 `llama_adapter.py`」；但会话 jetson 启动须在 `controller/` 内桌面重算 decode/response_format 身份，而 AC-9 只允许 controller 导入 `tools.eng_loop2.deploy_digest`。实现把唯一定义放在纯标准库 `deploy_digest.py`，`llama_adapter.DECODE_CONFIG` 是同一对象（测试 `test_decode_config_is_the_deploy_digest_object`）。
- **IR-5（`response_format` 形状）**：取 OpenAI 兼容 `{"type":"json_schema","json_schema":{"name":"vlm_three_state","strict":true,"schema":…}}`；llama-server b11381 是否接受此形状本机未核（合同 A2(c) 已列阶段 B 前置假设）。
- **IR-6（工作树「干净」的口径）**：会话启动与 `k-receipt`/`measure` 的 `dirty` 只看代码路径 `controller/`、`tools/`、`config/`（`git status --porcelain -- …`）；文档改动与忽略的 `runtime/`/`outputs/` 不计。
- **IR-7（jetson 收据资格）**：会话对不合格（`K_ret + K_conf + K_pub > R − 8`）的 jetson 收据也拒启（`k-receipt` 照合同以退出码 8 生成）；属 fail-closed 加严。
- **IR-8（显式 hold 收据只在常驻路径开启）**：`GatedPublisher(hold_receipts=True)` 只由常驻载体使用；LOOP-001 段式路径的显式 hold 仍无收据（AC-2「段式路径不变」）。收据 `detail.reason` 承载三值，顶层 `reason` 仍为 `null`（与规划器 hold 同位）。
- **IR-9（A5 终止细节）**：追平途中会话已终止时，在途 `ask` 回执 `IGNORED_TERMINAL(session_terminal)`，确认中的指定记 `designation_unavailable(reason=session_terminal)` 且不回退状态；呈现挂起中状态离开 `QUERYING`（如 seg_end 进 `REINIT_REQUIRED`）时同样丢弃呈现，`presentation_discarded.reason = state_changed`。
- **IR-10（服务端退出码与新增参数）**：`language_serve` llama 分支退出码 3 拒启 / 4 未就绪 / 5 服务期 llama-server 退出；新增 `--llama-ready-timeout-s`（缺省 300、上限 1800）、`--llama-request-timeout-s`（缺省 50，须 < `--t-hard-s`）；`--expect-assets` 允许多余键；`--version` 返回码非 0 也拒启；llama-server 旗标只给 `-m/--mmproj/--host 127.0.0.1/--port`（b11381 形状待板上核实）；`serve_code_sha256` 启动时算一次。
- **IR-11（访问日志漏记）**：`BaseHTTPRequestHandler` 在分派前直接 `send_error` 的请求（坏请求行、PUT 等）不进访问日志，§5.2 有效载荷计量会漏这类极少字节。
- **IR-12（`runtime/README.md` 与派发约束）**：派发块写「不写 `runtime/`（测试用临时目录）」；§4.1 允许文档 diff 含 `runtime/README.md`，且 §7 (m) 裁定新增 `STATE_REASONS` 须同步 runtime README。实现只改了这一个**入库文档**（字段/事件/收据 reason 说明），未写任何运行时文件；如 supervisor 认为越界请回退该文件。

## 待用户（候选 1 时；N1-LOAD-RECONCILE 已由用户答复认可）

- **N1-LOAD-RECONCILE**：首次全套插桩原始 CSRT 计数 6/5 与 §5.1 静态「尝试 2、实例 0」字面不同；按调用对象拆分（5 次为测试替身模块、真实 cv2 尝试 2 实例 0）后一致。推荐：确认该拆分判读、本次全套有效；理由：替身模块不构造任何 OpenCV 对象，真实 cv2 无该符号，子进程那次有失败栈为证。若用户认定属不符：按 N-1 条款本次全套作废、停止阶段 A 后续，不补跑。
- 其余六题（(h)、(i)、(j)、(k)、N-2、N-3）原题、推荐与理由不变，唯一原文在提案「D2 接受裁定」needs_user；按原前置门（代码独立复核通过后）转呈，本轮不提请。

## 改动文件（候选 1，`git diff --name-only "$BASE".."$CAND"`）

PLAY_GOVERNING（均在 §4.1 功能闭集内）：`controller/language_loop.py`、`controller/language_bridge.py`、`controller/language_selector.py`（新增 `status_document()`、`bind_identity` 校验六键）、`controller/gated_publisher.py`、`tools/language_serve.py`、`tools/language_latency.py`、`tools/eng_loop2/{__init__,llama_adapter,deploy_digest,analyze_play}.py`、`config/vlm-three-state.schema.json`、`config/p1-eng-loop-002-board-deploy.json`。
测试：`tests/test_language_loop.py`、`tests/test_language_bridge.py`（M）；`tests/test_language_latency.py`、`tests/test_llama_server_adapter.py`、`tests/test_eng_loop2_analyze.py`、`tests/test_loop2_isolation.py`、`tests/test_loop2_freeze.py`（N）；`tests/test_language_k_binding.py` 在 §4.1 列为 M/N 但**未改**（AC-6 新用例放在 `test_language_latency.py`）。
文档（§4.1 允许表内）：`docs/evidence/P1-ENG-LOOP-002-{K1K2K3K4-handoff.md,tests.log,archive-dryrun.json,four-numbers-fixture.json,play-ops.md,assets-local.json}`、`runtime/README.md`（IR-12）、`docs/current-status.md`。他角色提交：`docs/evidence/supervisor-dispatch.jsonl`（supervisor 派发登记，按真实 diff 核）。
闭集外 PLAY_GOVERNING 文件 diff：无（`test_loop2_freeze` 机检）。

编写分工（同一实现角色会话内）：本角色写 controller/*、`tools/language_latency.py`、`tools/eng_loop2/deploy_digest.py`、两 config、AC-1/3/4/5/6/9/12/17 测试与证据；并行编码助手 1 只写 `tools/eng_loop2/llama_adapter.py`、`tools/language_serve.py`、`tests/test_llama_server_adapter.py`；编码助手 2 只写 `tools/eng_loop2/analyze_play.py`、`tests/test_eng_loop2_analyze.py`、两份评分证据 JSON。三方均无 git 写入以外的越界；全部由本角色集成、自检与提交。

## 复核范围（候选 1 时）

完整候选 diff `git diff "$BASE".."$CAND"`；重点：§3.2 比较链（`validate_jetson_session`、`_validate_jetson_source`、`build_single_host_receipt`）、A4 呈现挂起与 `_resume_designate_retry` 守卫、A5 `_advance_resident` 终止分类与 `_SessionModelCache`、`GatedPublisher.hold_body`、`designate_options`、`language_serve` llama 分支生命周期与访问日志、`analyze_play` §3.5 唯一算法与 IR-2/IR-3。跟踪器相关复核重跑须用数据根解释器（本机 `~/TetheredDroneTracking-full/.venv-yoloe` 不存在，见下）。

## 未验证项与已知限制（候选 1）

- **跟踪器相关 focused 阻塞**：账本 2026-09-29 约定的数据根解释器 `~/TetheredDroneTracking-full/.venv-yoloe` 在本机不存在；本轮未用它跑跟踪器相关 focused（`test_trackers`/`test_track_loop`/`test_det_assoc_*` 未在开发期单跑），只在 N-1 签发的停点全套中以仓库 `.venv-yoloe` 跑过（含既有基线失败）。本批未改 `trackers.py`/`det_assoc_tracker.py`/`track_loop.py`。
- 真实 llama-server（b11381）旗标、`--version` 输出格式、`response_format` 形状、板端 `/health` 行为均只以假服务验证（IR-5/IR-10）；Python 与 Unity 单调钟同钟未核（评分只用仿真帧轴）。
- `model_cache.json` 的单加载只以替身 `create_tracker`/加载器验证；真实 `DetAssocTracker` 经缓存加载器的端到端构造未在本机执行（检测器加载额度 0）。
- 评分器只在合成夹具与两份旧归档（无会话意图、无元数据摘要）上运行；新 Play 归档的 H-2 摘要链、布局副本绑定无真实数据验证。
- `test_language_k_binding` 在 `.venv-yoloe` 全套中因 `tests` 包遮蔽无法导入（基线既有）。
