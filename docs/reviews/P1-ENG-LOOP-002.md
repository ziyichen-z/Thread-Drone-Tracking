# P1-ENG-LOOP-002 独立复核（闭环接入与四类数字首测阶段 A 代码候选，engineering-v1，合并停点 `K1K2K3K4`）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-LOOP-002-R1-K1K2K3K4-20261007T021503Z-8200`，`requested.round = R1@K1K2K3K4`）。
轨道：提案抬头逐字 `Workflow: engineering-v1`，接受角色在「D4 接受裁定」`ACCEPTED` 时逐字裁定生效 → 按 `docs/engineering-workflow.md` 复核；依据列仍写 `BC-n`，读作任务合同第 n 条验收项 `AC-n`（含「待裁定答复」「C1返工读法答复」的修订与 IR 释义）。
零消耗：零 scenario/session/run ID、零 Unity Play、零 VLM/API/GPU、零板端/ssh、零下载/安装、零真实模型构造、零归档回放（§5.1 零模型回放额度本轮未动用，不计数）、零全套重跑。只在一次性副本内读码、重跑 focused、做两次修前红复算与两个零模型探针；主树只写本文件与状态板。

## R1@K1K2K3K4（2026-10-06）

### §0 候选、基线与开轮资格

- `round_candidate: 5262a535fa95111a614cb862b30afff60b387ebd`（派发块指定；运行时核：`git log main --grep='^P1-ENG-LOOP-002 C1返工 收工'` 唯一命中且相等，是 `origin/main` 祖先；派发日志 `P1-ENG-LOOP-002-C1返工-20261007T013203Z-70a4` 的 `finished.candidate` 同值）。
- 全量 diff 基线：本文件此前不存在，无 `passed_candidate`；`$BASE = 259fe54cb2845397aa9bbd69378982d6620d5e8b`（`N-1答复落实 supervisor 核销` 唯一命中，与交接解析式、`tests/test_loop2_freeze.py::BASE_COMMIT` 相同）。`git diff --name-only $BASE..$CAND` = **35 路径**，与接受 C2 文件表逐一相同（下表按类归并）。候选 1 → 本候选增量（`$PREV = 32406ac0…cf0ea6` → `$RW_CODE = dfd4131e…281c0`）为 5 个生产文件 + 5 个测试文件 + 操作单；`$RW_CODE..$CAND` 只有证据/状态文档。
- 开轮资格：PLAY_GOVERNING（`controller/` 4、`tools/` 6、`tests/` 7、`config/` 2）diff 非空 → 开 `R1`。首个复核轮，无上一复核轮候选。
- 停点自证（交接「C1返工候选」四条件）：①范围/接口冻结成立（闭集外 PLAY_GOVERNING diff 本轮以 `git diff --stat $BASE..$CAND -- <冻结件/禁改路径>` 复核为空，见 §2 AC-2/12/13）；②相称测试：focused 本轮重跑全绿（下），全套 2/3 由实现者证据承担、本轮不重跑；③零 Unity，不适用；④候选解析式、AC 指针、风险、状态板齐备。交接把 AC-7 标「修复，待 C2 核对」而接受核对表判 AC-7 不满足——这是待核实主张，不是自证条件不成立 → 不判 `REVIEW_BLOCKED`，开轮并在 §3 给结论。
- 复核副本 `.claude/worktrees/review-P1-ENG-LOOP-002`（detach 于候选）；测试树哈希（`git ls-files tests | xargs cat | sha256` 前 16 位）`fd4ee7cfc7adc287`。解释器：系统 `python3`（与实现者 focused 同口径）；账本 2026-09-29 约定的数据根解释器 `~/TetheredDroneTracking-full/.venv-yoloe` 在本机不存在（`ls` 复核），跟踪器相关套件本轮未单跑（本候选未改 `trackers.py`/`det_assoc_tracker.py`/`track_loop.py`，`git diff` 为空）。
- **focused 重跑**（副本内，`YOLO_OFFLINE=true YOLO_AUTOINSTALL=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`，九个模块 `test_language_loop / test_language_bridge / test_language_latency / test_llama_server_adapter / test_eng_loop2_analyze / test_loop2_isolation / test_loop2_freeze / test_language_selector / test_language_k_binding`，输出写会话暂存目录只回显摘要）：**Ran 452 — OK（skipped=4）**，50.9 s；与交接逐模块计数（205+50+18+36+63+3+3+61+13 = 452）一致。跑后副本 `git status --porcelain` 为空。
- **实现者修前红主张复算**（副本内只回退对应生产文件、保留新测试，跑完 `git checkout HEAD --` 恢复）：回退 `tools/language_serve.py` 至 `$PREV` → `tests.test_llama_server_adapter` **4 FAIL + 7 ERROR**（交接写 4 FAIL + 7 ERROR，一致）；回退 `tools/eng_loop2/analyze_play.py` 至 `$PREV` → `ReworkC1AC8Tests` + `Loop2ScorerProductionSequenceTests` **3 FAIL + 11 ERROR**（交接 2F+10E 与 1F+1E 之和，一致）。
- **零模型探针**（副本内，脚本在会话暂存目录、不入仓）：(a) `LlamaServerAdapter` 身份块经 `build_k_receipt → payload → KReceipt.from_document` 往返后与服务端 `model_identity()` 逐键相等（`_validate_model_block` 只增 `None` 值可选键、不丢键）——§3.2 比较链在真实 llama 身份形状下成立；(b) PR-7 复现：见 R1-1。

### §1 逐文件核对摘要（35 路径全部读完整 diff）

| 文件 | 结论 |
|---|---|
| `controller/language_bridge.py` | `STATE_REASONS` 末尾追加 `rebuild_limit`、`geometry_rejected`（不重排）；`validate_llama_identity` 六键以「键存在」判出现、全有/全无、hex64/闭集/构建号正则、`backend http` + `model_form c2-merged` 前置；`_validate_model_block` 只在全有时并入六键，旧块字节形态不变。 |
| `controller/language_selector.py` | `HttpAdapter.bind_identity` 先 `validate_llama_identity` 再 `status()`；新增 `status_document()` 只读 `/status` 原文，不改 idle/在途记账；`_call` 逐键比较照旧。 |
| `controller/gated_publisher.py` | `hold_body(reason)` 闭集 `{loop_start, acquiring, acquire_failed}`，`hold_receipts=True`（常驻路径）时沿 `body_safety_hold` 通道补收据（`detail.reason`，顶层 `reason` 仍 `None`），写失败留 `WRITE_FAILED` 后抛；缺省 False = 段式路径逐字不变；`finalize` 后直通。 |
| `controller/language_loop.py` | A1 `--body-policy`/`_bind_standoff_runtime`（要求 `runtime/scenario_config.json` 存在且与 `--body-scenario-config` 逐值相等、`capture_hz`/`expires_after_s` 核、经 FRAME-001 `_build_body_runtime(..., "standoff", runtime=)`）；threshold 分支调用序列逐字不变。A4 `designate_options`/`_receipt` 只把 `intent`/`delay_s` 写回执；`result_arrived` → `_pending_presentation` → `_maybe_present`（Δ 到期、epoch 变即 `epoch_changed` 丢弃、离开 `QUERYING` 即 `state_changed` 丢弃；呈现步骤与原代码逐行同，预览代码不改）；`_resume_designate_retry` 挂起中不发查询。A5 `_SessionModelCache` 经 `create_tracker(..., model_loader=)` 透传（`DetAssocTracker.__init__` 第 276 行确有 `model_loader` 参数并以其替代 `_default_model_loader`，本轮读码核实）；`duration_reached` → `stop()` 不重建；`rebuild_limit` 第 3 次；`backend_fatal` 常驻 → `TERMINAL`；`model_cache.json` 随段落盘。A6 `frames_processed.metadata_sha256` 当刻字节 sha、缺失 `null`+原因。§3.2 `_validate_jetson_source`/`validate_jetson_session`/`code_git_state`（整个工作树 `--porcelain --untracked-files=normal`）。A7 `geometry_rejected`。`JOURNAL_KINDS` 闭集 + `_journal` 抛错。 |
| `tools/language_serve.py` | llama 分支：预检（三 sha、`--version` 构建号、`--expect-assets`、量化闭集、部署摘要）→ 前台子进程 → `/health` 就绪 → 单工运行时（`delete_images_after_run`）→ `handle_request` 循环；SIGTERM/子进程退出收尾（`server_close`、`_stop_child`、`rmtree`）。计量：`_CountingReader/_CountingWriter`、`handle_one_request` 的 `finally` 逐请求落行、`parse_request`/`end_headers`/`send_response` 取边界、`_drain_declared_body` 有界读走、12 键 JSONL。**见 R1-1**。local-hf 分支读写/回包逐字不变（本轮读 diff 核实）。 |
| `tools/language_latency.py` | jetson 测量（身份只取 `/status`、`classify=True` 逐样本三态/`parse_error` 不过滤）；`build_single_host_receipt` 的拒绝链（host/verdict/backend/endpoint/git_head/dirty/六键/machine → HEAD 相等 + 干净树 → `desktop_identity_digests` 重算 response_format/decode/部署摘要 + prompt 身份 → hz/R）；退出码 0/6/8；旧两宿主路径不变。 |
| `tools/eng_loop2/deploy_digest.py` | 纯标准库；规范 JSON、清单路径校验（相对/无 `..`/去重/含自身）、`deploy_digest`、`DECODE_CONFIG`/`response_format_object` 唯一定义（AC-7 修订 1）。 |
| `tools/eng_loop2/llama_adapter.py` | 只连 `127.0.0.1`、无代理；prompt v2 逐字 + 入仓 schema + 解码常量 + 原样 base64；传输失败映射闭集；`finish_reason`/`gen_tokens`/原文原样进 `RawSelection`；身份自算六键并自校验。 |
| `tools/eng_loop2/analyze_play.py` | §3.5 唯一算法全文 2,315 行已读：样本/意图/X_s/`worker_abandoned`、C1–C6、`_unavailable_origin_epoch`（IR-16 边界：向前只跨 TERMINAL，遇受理样本行/指定/不可用行即止）、`_own_pointer_bound`（同 epoch、同常驻代、遇指定/采纳/受理/TERMINAL/重建即止，`claimed` 防双占）、`split_at_time`（闭端点、未知时刻不推定）、存活七类与原函数差异、捕获同帧优先级 f_p > acquire_failed > E > 截止、time-to-center 三结局与两起点时长、误锁时长、按真值来源分列 + 守恒 + 无合并表、H-2 (1)–(4)、布局绑定不调 `apply_layout`、`_reject_runtime_inputs`。 |
| `config/vlm-three-state.schema.json`、`config/p1-eng-loop-002-board-deploy.json` | 三态 `oneOf`（`unique` bbox 4 整数 0–1000；`ambiguous` 2–8 候选；`none`）、`additionalProperties false`；部署清单 16 路径含自身，无 `analyze_play`/`train_lora`/`eng_jet`。 |
| `tests/test_llama_server_adapter.py` | 假 OpenAI 服务、失败映射、拒启、部署摘要、隔离子进程、`AccessLogEveryRequestTests`（9 例，线路实际字节）；**无部分写入失败用例**（R1-1）。 |
| `tests/test_language_loop.py` | `Loop2BodyPolicyTests`/`Loop2SingleLoadTests`（三类终止）/`Loop2ContractTests`/`Loop2DelayTests`（10 例）/`Loop2ScorerProductionSequenceTests`（真实 `LanguageSession` 产日志喂评分器，PR-3/4）。 |
| `tests/test_language_latency.py` | `SingleHostReceiptTests`/`JetsonMeasurementTests`/`JetsonSessionStartTests`/`CleanWorkingTreeProductionPathTests`（真实临时 git 仓库、不注入 `git_state`，tests/docs/未跟踪/config 均判脏，忽略目录不计）/`ModelBlockCompatibilityTests`。 |
| `tests/test_language_bridge.py` | 六键类型/域/部分/`null` 出现（C1-AC6）、`STATE_REASONS` 追加顺序。 |
| `tests/test_eng_loop2_analyze.py` | 1,375 行：十二类/冲突/布局/篡改/存活/捕获/分母/归档 + `ReworkC1AC8Tests` 10 例。 |
| `tests/test_loop2_isolation.py`、`tests/test_loop2_freeze.py` | AST 导入闭集恰为五项、真值记号零、`intent` 只在五个函数；冻结件 sha 运行时取自 `$BASE`、围栏/禁改路径 diff 空。本轮另以 `git diff --stat` 独立复核为空，以 `ast.get_source_segment` 核 `LanguageWorker`/`CandidatesBackend`/`_validate_candidates_source`/`LanguageSession._preview`/`render_preview` 与 `$BASE` 逐字相等。 |
| `runtime/README.md` | 入库文档；新 reason/六键/`delay_s`/`intent`/hold 收据/事件名/`metadata_sha256` 说明与代码一致；无运行时写入（IR-12）。 |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md` | 13 节闭集齐；§1.1 取末条 `passed_candidate` 且须在末条 `round_candidate` 之后（本文件本轮无通过行 → 当前必 NOT_OK，正确）；§9 三剧本命令逐字、令牌运行时取值。 |
| 其余（交接、两份测试日志、两份回放 JSON、两份合成夹具 JSON、`-assets-local.json`、提案、正式设计、C1/C2 证据、账本、状态板、派发登记） | 均读；不含运行时代码或工作流基础设施改动；账本新增条目为 supervisor 代录的用户 N1-LOAD-RECONCILE 答复，非本角色所写。 |

### §2 AC 逐项与 C2 预复核关注项（依据列 `BC-n` 读作 AC-n）

| AC | 结论 | 依据 |
|---|---|---|
| AC-1 | 成立 | `Loop2BodyPolicyTests` + 读码：standoff 显式覆盖文件、逐值相等、`runtime=`、manifest `body_planner.name`/sha；threshold 调用序列不变。 |
| AC-2 | 成立 | 六冻结件与 `scenario_tether.py`、`track_loop.py`、`resident_core.py`、`trackers.py`、`det_assoc_tracker.py`、`tools/eng_sft`、`tools/eng_jet`、`Assets/`、`config/scenario.*` 的 `git diff --stat $BASE..$CAND` 为空（本轮 cmd）。 |
| AC-3 | 成立（替身加载器） | `_SessionModelCache.loads` 只计底层调用；三类终止各有用例；真实 `DetAssocTracker` 接受 `model_loader` 已读码核实，端到端真实加载留阶段 B（额度 0）。 |
| AC-4 | 成立 | 三种 reason 收据、无观测帧无 `WRITTEN` 速度、SUSPECTED 两分支、`JOURNAL_KINDS` 覆盖全部调用点（AST 用例）。 |
| AC-5 | 成立 | 恰延 Δ、事件字段、只挂 `unique/ambiguous`、挂起中 `QUERYING`/`confirm_in_QUERYING`、新 ask/respecify/stop 丢弃且无结果行、越过检查点带 `delay_injected_s`、域拒绝、worker 空闲、`intent` 隔离、`metadata_sha256` 同序。PR-2 见下。 |
| AC-6 | 成立 | 退出码 0/6/8、§3.2 每项错配拒绝、六键五种拒绝、旧块照常；C1-AC6 两处闭合（整树 dirty 真实 git 夹具；`null` 出现即拒）。 |
| AC-7（含修订 1） | **不成立** | 适配器/拒启/部署摘要/前台生命周期/无残留/逐请求有行均成立；但「访问日志逐请求含请求体/响应体字节」在异常 IO 路径记 0 而非实际字节 → R1-1（接受 C2 的 PR-7 本轮独立复现为真缺陷）。 |
| AC-8（含修订 1/2） | 成立 | 十二类守恒、C1–C6、归属链、IR-14/16 边界、`split_at_time` 闭端点、三来源分列与守恒、time-to-center 时长输出、生产序列夹具；读码逐条对照 §3.5.1–3.5.6 未见偏离（PR-3/4/5 核实见下）。 |
| AC-9 | 成立 | AST 闭集恰五项（含 `tools.eng_loop2.deploy_digest`）、部署侧零真值导入与记号、`intent` 不进决策函数；`validate_jetson_session` 的惰性导入在闭集内。 |
| AC-10 | 成立 | §1.1 末条通过候选解析、§1.2 整树干净同口径、§9 逐字命令含 confirm/reject/release/stop、§5.2 计量记录模板、§13 STOP 表；当前不可执行（无 `passed_candidate`），正确。 |
| AC-11 | 成立 | 五个具名符号 AST 源码段与 `$BASE` 逐字相等（本轮重算）、`candidates_preflight.py` diff 空；预览路径未触及（H-9）；清理清单零删除。旧 OPEN 债不销。 |
| AC-12 | 成立 | `scenario_tether.py` diff 空；R1-3 账本行未改。 |
| AC-13 | 成立 | 19 个 PLAY_GOVERNING 路径全部在 §4.1 归属表内，文档 diff 在允许表内；两份全套日志失败名集合相同（接受已核；本轮未重跑全套）。 |
| AC-14 / AC-15 / AC-18 | `NOT_RUN` | 阶段 B 未签；本轮不代签。 |
| AC-16 | 阶段 A 部分成立；板端 `NOT_RUN` | `-assets-local.json` 只哈希、不引用 JET 诊断读数。 |
| AC-17 | 成立 | `geometry_rejected` cause + `STATE_REASONS` 追加 + 回归。 |

C2 预复核关注项核实：

- **PR-1（停机时后台线程/图像清理）**：读码——`submit` 在锁内先写图再起线程，`_run` 只读图、`finally` `unlink(missing_ok=True)`，不新建文件；`_main_llama` 的 `finally` 顺序 `server_close → _stop_child → rmtree`：在途线程遇子进程退出得 `worker_died`、遇 `rmtree` 后读图得 `OSError → worker_died`，均在 `_run` 捕获；进程退出时 daemon 线程随之结束，不产生新文件。`runtime.join` 未调用只影响该在途结果不被回收（服务已停、无客户端可取），不产生残留。**非 finding**（接受「相称核实」在本轮以读码完成；真实时序留阶段 B 如实记）。
- **PR-2（Δ 到期与新命令同 tick）**：`tick` 顺序 `_poll_worker → _maybe_present → _consume_request`；到期同 tick 且单槽已有新 `ask` 时旧结果先呈现（写结果行、进 `AWAITING_CONFIRMATION`）再受理新命令（`_begin_designate` 丢弃候选）。A4 以「受理」为界，受理发生在 `_consume_request`，字面成立；评分侧该样本入类 7 `UNCONFIRMED_SUPERSEDED` 而非类 1 `SUPERSEDED(presentation_pending)`，两类均不进数字一/二/三/误锁/显式比例的分子分母，读数不受影响。**非 finding**，记为已知边界（不加合同）。
- **PR-3（IR-16）**：`_unavailable_origin_epoch` 只在不可用行 epoch 不属任何样本时启用，向前扫描见 TERMINAL 置标、遇受理样本行/`designation`/`designation_unavailable` 即 `None`、到 `confirm`（APPLIED）才返回其 epoch；生产序列用例（真实 `LanguageSession`，`planned_duration_s` 到期）断言 `INTERRUPTED(designation_unavailable, session_terminal)`、无冲突、`reattributed = 1`。本轮修前红复算该用例确为 `ATTRIBUTION_CONFLICT`。成立。
- **PR-4（AC-8 修订 1）**：`_own_pointer_bound` 同 epoch + 同常驻代 + 遇边界即止；`claimed` 防两样本占同一 `pointer_bound`；生产序列两代各从 1 编号、各得本代 `track_id`、无 C6。成立。
- **PR-5（闭端点/空窗/布局）**：`split_at_time` 以 `t > 窗尾` 出窗（`t == 窗尾` 在窗内，不加容差）；存活 `CENSORED_END` 判据 `sim(f_p)+W > sim(E)`、`TRUTH_GAP(empty_window)` 显式排除（含 f_p→首帧间隔）、窗外 `no_pose_ext`、31 帧判据；time-to-center `beyond` 非空或 `sim(E) ≥ 窗尾` 才 `CENTER_NOT_REACHED`；布局排除在数字一/二/三/捕获第一步后单列且守恒。成立。
- **PR-6（轮次）**：本文件为 `R1@K1K2K3K4`；阶段 B 证据核实按 IR-13 届时解析，本轮不预记。
- **PR-7**：见 R1-1。

### §3 Findings

| ID | 分级 | 依据 | 阻断 | 摘要 |
|---|---|---|---|---|
| R1-1 | CLASS_2 | `BC-7` | 是 | `tools/language_serve.py` 计量模式在写入/读取异常路径只记「调用成功返回」的字节：响应体 `sendall` 中途抛错时已交给内核的字节记 0（探针复现：客户端实收 10 B，日志 `response_body_bytes 0`），`_drain_declared_body` 超时时 `BufferedReader` 已消费的部分块同样不计；与 AC-7「逐请求含请求体/响应体字节」、§5.2 计量口径及已裁 IR-11/IR-15「不接受把异常调用已传输的部分字节按 0 计」不符 |

#### R1-1 异常 IO 路径的实际字节未计（`tools/language_serve.py::_CountingWriter.write`、`_CountingReader.read/readline`、`_drain_declared_body`）

- 合同：AC-7「访问日志逐请求含请求体/响应体字节」；§5.2「计量 = 板端 `language_serve` 逐请求访问日志（…请求体字节、响应体字节…）求和」，是 HTTP 有效载荷 ≤ 60,000,000 B 信封的唯一计量来源；接受「待裁定答复」IR-11（不接受漏记豁免）与「C1返工读法答复」IR-15（**不接受把异常调用已传输的部分字节按 0 计的豁免**；未读/未解析部分不以 Content-Length 补算）。
- 实现：`_CountingWriter.write` 在 `self._raw.write(data)` 返回后才 `count += len(data)`；`wfile` 是 `socketserver._SocketWriter`（`wbufsize=0`），其 `write` 调用 `socket.sendall`——`sendall` 在部分字节已交给内核后抛 `BrokenPipeError`/`ConnectionResetError` 时不返回已发字节数，该次整体不计。`_CountingReader.read` 同样在 `BufferedReader.read(n)` 返回后加数；`_drain_declared_body` 对连接设 10 s 超时后分块读走，`BufferedReader` 在原始读超时时丢弃本次已取回的部分块（CPython `_bufferedreader_read_generic` 行为），该部分字节既已从套接字消费又未入账，只在 `error` 列留 `timeout`。
- 复现（零模型探针，副本内，脚本不入仓）：以生产 `build_server(runtime, port=0, access_log=…)` 起服务，在 handler `setup` 把底层套接字换成「第 2 次 `sendall`（响应体）只真实发送 10 B 后抛 `BrokenPipeError`」的透传代理，客户端 `GET /status`：客户端实收响应体 **10 B**；访问日志该行 `response_head_bytes 156`、**`response_body_bytes 0`**、`error "BrokenPipeError: …"`。
- 可达性：阶段 B 生产路径——Unity 主机会话 `HttpAdapter` 的 `HTTP_IO_DEADLINE_S` 到期关连接、Tailscale 链路复位、`llama-server` 退出时服务端收尾——均是客户端在响应写出途中断开的真实失败路径；§6.2 `S-ENVELOPE` 以该日志求和判越界，undercount 使越界判定与 `-ledger.json` 的「实际字节」口径失真。接受 C2 已以同一依据判 AC-7 不满足，本轮独立复现为真缺陷，非 `上游漏检`。
- 修复方向（不限定实现）：把计数层下移到套接字：在 `setup` 以透传代理包裹 `self.request`/`self.connection`，`sendall` 改为对 `send()` 循环逐次累加返回值（异常抛出前已累加的即「实际交给内核的字节」），`recv`/`recv_into` 同样按返回长度累加；`rfile`/`wfile` 的头/体边界仍取 `parse_request`/`end_headers` 时刻的计数。`_drain_declared_body` 的超时/断连按同一计数口径入账。docstring「sendall 抛错该次不计」随之改写。local-hf 分支（无 `--access-log`）不得受影响。
- 闭合绑定（workflow §4.4 四条）：具名回归测试放 `tests/test_llama_server_adapter.py::AccessLogEveryRequestTests`（生产路径：真实 `build_server` + 真实回环套接字，只把底层套接字替换为「第 2 次写入接受前 10 B 后抛 `BrokenPipeError`」的代理，与本轮探针同构），断言该行 `response_body_bytes == 10`（= 实际交给套接字的字节）且 `error` 非空；修前该断言为 `0 != 10` 必失败。读取侧补一例：客户端只发声明长度的一部分后保持连接不关（服务端 drain 超时），断言 `request_body_bytes` 等于客户端实际已发送字节、`request_body_complete false`、`error` 含 `timeout`。下一轮由本角色在副本内以修前红/修后绿核实。`NOT_MECHANIZABLE` 不适用。

其余核对未产生 finding：未发现 CLASS_1、`RED_LINE`（真值隔离 AST 用例 + 本轮读码：`controller/`、`llama_adapter.py`、`language_serve.py`、`deploy_digest.py` 零真值/评分导入；评分器不被运行时导入；`intent` 不进决策）、`上游漏检`、`上轮漏检`。

### §4 UNITY_NA

本候选未申请 `UNITY_NA`（交接明示「不申请」）；AC-14/15/18 与 AC-16 板端为 `NOT_RUN`。本角色无附议对象；阶段 A 代码候选即使通过也只到独立复核通过，`DONE` 仍需阶段 B 的 Unity/板端证据。

### §5 限制、未验证与消耗

- 本轮未重跑停点全套、未做归档回放、未碰板/Unity/VLM；全套 2/3 与回放 1/2（本候选）由实现者证据与接受核对承担，本轮不重计。
- 跟踪器相关套件未在数据根解释器下重跑（本机不存在该环境，不安装、不改约定）；本候选未改跟踪器文件。
- 真实 `llama-server` b11381 旗标/`--version`/`response_format` 形状、板端 `/health`、Tailscale 半包时序、真实 `DetAssocTracker` 经缓存加载器的端到端构造均未在本机验证（实现交接已如实列出），本轮不加主张。
- 已知边界（非 finding）：PR-2 同 tick 顺序（§2）；会话 `stop()`/`close()` 之后 `_designate_resident` 仍追加 `designation_unavailable` 行（`_journal` 逐次 append 打开文件，功能上成立，生产序列用例覆盖）。
- consumed = none（零 ID/Play/API/GPU/下载/pip/板操作；零模型；零回放）。

### Verdict（R1@K1K2K3K4）

**`REWORK_REQUIRED`**（本停点第 1 次，1/2）。阻断：R1-1（CLASS_2，`BC-7`）。修复直接回本角色 `R2@K1K2K3K4`，不经核对轮；是否开 `R2` 按 workflow §4.4 开轮资格（PLAY_GOVERNING diff 非空；`tools/language_serve.py` + `tests/test_llama_server_adapter.py` 必非空）决定。不写 `passed_candidate`。返工只限 R1-1 触及文件；AC-1…6、8…13、17 本轮成立的结论随候选携带，下一轮按增量规则只在修复触及行上找新阻断。

## R2@K1K2K3K4（2026-10-06）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-LOOP-002-R2-K1K2K3K4-20261007T024111Z-d545`，`requested.round = R2@K1K2K3K4`）。增量轮（COORD-009 (b)）：先读 R1 全文；新阻断只来自修复触及行上的 CLASS_1/2、R1-1 闭合失败、`RED_LINE`、未改动行上标 `上轮漏检` 的 CLASS_1。零消耗：零 ID/Play/API/GPU/板/下载/pip、零真实模型、零归档回放、零全套重跑；只在一次性副本内读码、重跑 focused、做 R1-1 修前红/修后绿与两个零模型探针（脚本在会话暂存目录、不入仓）。

### §0 候选、基线与开轮资格

- `round_candidate: 47f546cc4934fcb74b25df6cf4ba7efbab102fd0`（派发块指定；运行时核：`git log main --grep='^P1-ENG-LOOP-002 R1返工 收工'` 唯一命中且相等；派发日志 `P1-ENG-LOOP-002-R1返工-20261007T023249Z-4b17` 的 `finished.candidate` 同值）。
- 修复触及行基线 = 上一复核轮候选 `5262a535fa95111a614cb862b30afff60b387ebd`（R1 §0 `round_candidate`）。`git diff --name-only $R1_CAND..$CAND` = 10 路径：PLAY_GOVERNING 只有 `tools/language_serve.py`（+86/−18）与 `tests/test_llama_server_adapter.py`（+87/−0），其余 8 个为文档/证据/派发日志/状态板/本文件（`docs/current-status.md`、`-C2-K1K2K3K4.md`、`-K1K2K3K4-handoff.md`、`-r1fix-redgreen.log`、`supervisor-dispatch.jsonl`、`phase1-single-drone-design.md` v0.3.62 条目、提案 Status 行与核对表、`docs/reviews/P1-ENG-LOOP-002.md`）；代码增量只在代码提交 `19278f96dd3c0687f599d8162a60deb540341170`，其后到候选只有证据/状态文档（本轮 `git diff --stat` 核实，与交接解析式一致）。
- 全量 diff（相对上一通过候选；本文件无 `passed_candidate` → `$BASE = 259fe54cb2845397aa9bbd69378982d6620d5e8b`）：`git diff --name-only $BASE..$CAND` = 38 路径 = R1 的 35 路径 + 3 个新文档（C2 证据、红绿日志、本文件）；非 `docs/` 路径 20 个与 R1 §1 表逐一相同，无 R1 未核对的新实现文件。R1 对未改动文件的结论随候选携带，本轮不重述。
- 开轮资格：PLAY_GOVERNING diff 非空（两文件）→ 开 `R2`。
- 停点自证（交接「R1返工候选」四条件）：①范围冻结成立（增量恰为两具名文件，CLI 旗标/12 键 JSONL/回包/身份块未变，本轮读 diff 核实）；②相称测试：focused 本轮重跑全绿（下）；**engineering §6 窄修替代全套**：相对上一个已跑全套的候选（C1返工 `$RW_CODE`）只改两具名文件，`language_serve.py` 改动只在 `import io`、`_CountingReader`、新 `_CountingSocketWriter` 与 `setup` 计量分支一行——未触及 `llama-server` 子进程/`LlamaServerAdapter`/`SingleFlightRuntime`（真实模型加载器）、数据划分或 `analyze_play.py` 对外指标路径；访问日志是 §5.2 信封计量来源而非对外指标。**本角色判替代充分，不要求全套**；全套额度保持 2/3、本候选不记全套通过。③零 Unity，不适用；④候选解析式、闭合绑定表、复核范围、状态板齐备。
- 复核副本 `.claude/worktrees/review-P1-ENG-LOOP-002`（detach 于候选）；测试树哈希（`git ls-files tests | xargs cat | sha256` 前 16 位）`3de6748fafb9668a`（R1 `fd4ee7cfc7adc287` → 本候选新增两例）。解释器：系统 `python3`（与实现者同口径）。
- **focused 重跑**（副本内，`YOLO_OFFLINE=true YOLO_AUTOINSTALL=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`，九模块同 R1，输出写会话暂存目录只回显摘要）：**Ran 454 — OK（skipped=4）**，42.5 s；= R1 452 + 本轮 2 例（skip 4 与 R1 副本同口径、交接 3 为环境差异）。跑后副本 `git status --porcelain` 为空。

### §1 修复触及行逐行核对（`git diff $R1_CAND..19278f9`）

**`tools/language_serve.py`**

- `_CountingReader`：新增 `read1(size)`（底层 `BufferedReader.read1` 一次返回即计）；`read(size)` 改为循环 `read1(remaining)`（`size<0`/`None` 时循环 `read1(64 KiB)` 至空）；`readline(size)` 改为 `peek(1)` 取缓冲窗口 → 在窗口内找 `\n` → `read1(take)`（`take ≤` 缓冲已有字节，不触发底层读）→ 命中换行或 EOF 即止、`size` 上限照旧。读码核：`BufferedReader.read1`/`peek` 在缓冲为空时恰做一次原始读，原始读抛错（超时/复位）时此前已返回的块已入 `count`，不再出现 CPython `_bufferedreader_read_generic` 丢弃已消费部分块的路径；`__getattr__` 透传 `close`/`closed` 等不变。
- `_CountingSocketWriter(io.BufferedIOBase)` 取代 `_CountingWriter`：直接持套接字，`write` 以 `memoryview(...).cast("B")` 逐次 `send()`、按返回值累加 `count`、返回全长；`writable()`/`fileno()`；`close` 走 `IOBase`（不关套接字），与 `socketserver._SocketWriter`（`wbufsize=0`）语义一致。`StreamRequestHandler.finish` 的 `wfile.flush()/close()` 与 `BaseHTTPRequestHandler.handle_one_request` 末尾 `wfile.flush()` 在 `IOBase` 上均为无操作，本轮读码核实。
- `setup`：计量分支 `self.wfile = _CountingSocketWriter(self.connection)`（旧为包装 `self.wfile`）；local-hf 分支（`access_log is None`）不进该分支，读写与回包逐字不变（`test_local_hf_default_has_no_metering_and_old_semantics` 照绿）。
- 头/体边界未改：`parse_request` 末取 `rfile.count`、`end_headers` 末取 `wfile.count`、`_drain_declared_body` 经 `rfile.read` 同口径、`_access_finish` 差值计算与 12 键 JSONL 不变；`protocol_version` 仍为缺省 HTTP/1.0（每连接一请求），未触及。

**`tests/test_llama_server_adapter.py`**：`AccessLogEveryRequestTests` 新增两例，与 R1 §3「闭合绑定」逐条对应（写侧：生产 `build_server` + 真实回环套接字、只在 `setup` 把底层套接字换成「首次写入原样、此后只接受 10 B 即抛 `BrokenPipeError`」的透传代理，代理同时实现 `send`/`sendall` 两种语义，故修前修后用同一夹具；读侧：客户端发声明 100 B 中的 30 B 且不关连接、`ACCESS_DRAIN_TIMEOUT_S` 临时 0.5 s 并 `addCleanup` 复原，两子例同段/分段）。fixture 由生产路径产出（真实服务、真实套接字、真实日志写盘），无手工造状态——闭合条件 (1) 成立。

### §2 R1-1 闭合（修前红/修后绿，副本内）

| 步骤 | 命令要点 | 结果 |
|---|---|---|
| 修前红 | 副本内 `git checkout $R1_CAND -- tools/language_serve.py`（保留新测试），跑两条具名回归 | **FAILED (failures=3)**：写侧 `0 != 10`；读侧两子例各 `0 != 30`（与实现者 `-r1fix-redgreen.log` 逐字一致） |
| 恢复 | `git checkout HEAD -- tools/language_serve.py`，`git status --porcelain` 空 | — |
| 修后绿 | 同两条回归连跑 3 次 | **OK ×3**（0.5 s 超时夹具无抖动） |

零模型探针（副本内、不入仓，补强而非替代回归）：(a) `_CountingReader` 对 `BufferedReader(BytesIO)` 的 `readline`/`read` 等价性——209 组输入 × 缓冲 1/2/4/8192 × `size ∈ {-1, None, 0, 1, 2, 3, 5, 8, 65537}` × 连续 6 次调用，另加 `readline`/`read` 混合序列：返回字节逐一相等，`count` 恒等于已返回字节总和，**0 处不一致**；原始读「先返回 30 B 再抛 `TimeoutError`」时 `count == 30`，而标准库 `BufferedReader.read(100)` 同输入抛错且 30 B 丢失（复现 R1 分析）。(b) `_CountingSocketWriter` 对假套接字：每次 `send` 只收 3 B 时 `write` 返回全长、`count` 累加正确、`memoryview` 输入可用；`send` 在累计 10 B 后抛 `BrokenPipeError` 时 `count == 10 == 实际交给套接字`。(c) 真实 `build_server` 计量模式下同段管线三请求：服务端 HTTP/1.0 只服务第 1 个即关连接（既有行为，未改），其行 `request_head_bytes` = 该请求头长、响应 258 B = 客户端实收 258 B；缓冲已预读但未消费的后续请求字节不计——与交接「待裁定」所述 IR-15 消费口径一致、与 R1 核为成立的 `test_bad_request_line_is_logged_with_actual_bytes` 同口径，非 finding。

闭合四条：(1) 生产路径 fixture 成立；(2) 本角色副本内修前红/修后绿成立；(3) 修复不触及 Play 治理门文件（`analyze_m3_body.py`/`preflight_reanchor_env.py`/`controller/run_log.py` 均不在 diff），闭环轮不适用；(4) `NOT_MECHANIZABLE` 不适用。**R1-1 闭合。**

### §3 Findings

无新 finding。修复触及行上未发现 CLASS_1/2（边界：`size=0`/`None`/负值、EOF、超长行 414 路径、`memoryview` 输入、`send` 部分写与抛错、`flush/close` 语义均核；并发：计量日志写入仍在 `_access_lock` 下、每连接单请求；真值泄漏：两文件零 `controller`/评分/真值导入，`test_loop2_isolation`/`test_loop2_freeze` 照绿）；无 `RED_LINE`；无 `上轮漏检` CLASS_1；R1-1 闭合成功。CLASS_3 无。

非 finding 备注（归属接受角色消费时处理，不加合同）：提案「Contract conformance（核对表）」AC-7 行仍为 C2 时的「不满足」措辞，核对表只留最新一版，由接受角色在消费本轮时更新；`runtime/README.md`、操作单未含「sendall 抛错不计」旧口径，无需改。

### §4 UNITY_NA

本候选未申请 `UNITY_NA`（交接明示「不申请」）；AC-14/15/18 与 AC-16 板端为 `NOT_RUN`。无附议对象；阶段 A 代码候选通过只到独立复核通过，`DONE` 仍需阶段 B 的 Unity/板端证据。

### §5 限制、未验证与消耗

- 本轮未重跑停点全套（窄修替代已在 §0 判充分）、未做归档回放、未碰板/Unity/VLM；全套 2/3、回放 3 次由实现者证据与接受核对承担。
- 新计数只在回环 HTTP/1.0 夹具、注入代理与假 IO 下验证；板端 Jetson Python 版本的 `BufferedReader.read1/peek` 行为、真实 Tailscale 半包/复位时序、`llama-server` 退出时收尾（R1 PR-1 已核非 finding）未在本机验证，阶段 B 如实记。
- 跟踪器相关套件未在数据根解释器下重跑（本机不存在该环境）；本候选未改跟踪器文件。
- consumed = none。

### Verdict（R2@K1K2K3K4）

**`PASS`**。R1-1 以生产路径具名回归修前红/修后绿闭合；修复触及行无新阻断；`RED_LINE` 无；R1 对其余 AC（AC-1…6、8…13、17 成立；AC-14/15/18 `NOT_RUN`；AC-16 板端 `NOT_RUN`）的结论随候选携带。本停点返工终计 1/2。交接受角色消费（归因、核对表 AC-7 更新、`REVIEW_PASSED` 由接受角色裁定）；阶段 B 信封仍未签，消耗性动作 0。

passed_candidate: 47f546cc4934fcb74b25df6cf4ba7efbab102fd0

## R3@K1K2K3K4 派发（2026-10-07）— `REVIEW_BLOCKED`（稳定门不成立；不开轮、不计复核轮次）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-LOOP-002-R3@K1K2K3K4-20261007T062916Z-b150`，`requested.round = R3@K1K2K3K4`）。零消耗：零 SSH/ping/复制/模型/板/Unity/runtime/功能测试/回放/全套；只在一次性副本 `.claude/worktrees/review-P1-ENG-LOOP-002`（detach 于候选）读文档与 `git diff`，主树只写本文件与状态板。本节按交接行「先核稳定门，具资格才开 R3」执行：先独立核 workflow §4.3.1 四条件，不以接受 C3 的结论代替读候选。

### §0 候选、基线与资格核对（未开轮）

- 候选（派发块指定）：`f84bb58dbe398dee8dcf20687febc7dc846dab71`。运行时核：mini 证据 §5 解析式 `git log origin/main --format=%H -n 1 --grep='^P1-ENG-LOOP-002 mini操作单准备' -- docs/evidence/P1-ENG-LOOP-002-play-ops.md` 唯一命中且相等，是 `origin/main` 祖先；派发 `base_head` 为 C3 收工提交，候选到该提交只有 6 个 C3 证据/状态/派发登记文档（`git diff --stat` 核实）。**本节不写 `round_candidate:` / `passed_candidate:` 机读行**：未开轮，下一次开轮（若有）仍编 `R3@K1K2K3K4`，其修复触及行基线仍是 R2 §0 的轮候选、全量基线仍是 R2 的通过候选（同为 `47f546cc…02fd0`）；本版操作单的改动不得因本节被当作「已复核过的行」。
- 全量 diff：`git diff --name-only 47f546c..f84bb58` = 11 路径，全部 `docs/`（`authorizations.md`、`current-status.md`、`-mini-ops-prep.md`〔新〕、`-play-ops.md`〔+169/−74，旧版 228 行→323 行〕、`-precheck.md`〔新〕、`supervisor-dispatch.jsonl`、`implementation-status.md`、`parked-status.md`、`phase1-single-drone-design.md`、提案、本文件）；`-- controller tools tests config Assets ProjectSettings Packages/packages-lock.json` 为空；副本测试树哈希 `3de6748fafb9668a` 与 R2 相同。非 PLAY_GOVERNING 的 9 个文档路径本节只核类别与写入角色（账本 4 条为 supervisor 代录的用户授权、其余为接受/实现/supervisor 的状态与证据），未开轮不做内容复核。
- PLAY_GOVERNING：只有操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md`（本 work item 点名的操作单文件；R1 §1 已按 PLAY_GOVERNING 核对）→ `git diff` 资格本身非空。但 workflow §4.3.1 规定自证条件不成立的候选「不开轮、不计复核轮次」，资格检查在稳定门之后，不构成开轮。
- focused 未重跑：未开轮无重跑义务；代码/测试相对通过候选零字节 diff（测试树哈希相同），R2 的 454 OK 结论随候选携带，本节不新增代码主张。

### §1 稳定候选四条件独立核对（workflow §4.3.1；对照 mini 证据 §6 自证与 C3 证据 §2）

| 条件 | 结论 | 本角色依据（副本内读 `-play-ops.md`、`-mini-ops-prep.md`、提案「mini操作单待裁定答复与 CHANGE 申请」） |
|---|---|---|
| ① 范围与接口冻结 | **不成立** | (a) 操作单 §4 启动命令（第 121 行）逐字含占位 `--llama-ready-timeout-s <IR-M7 裁定值>`；接受已裁 IR-M7「拒绝…自动冻结 20 s」且 `open_items` 仍含 IR-M7——操作员无法从本版得到可执行值，这不是「运行时解析」的令牌，而是未裁定的合同值。(b) §4「启动前提：IR-M1 已裁定。若裁为改代码，本节命令随新通过候选的 `language_serve` 生效」；接受已裁 IR-M1「需要另出代码候选、回 K1/K3」而 CHANGE:1 未签——本版操作单驱动的 `tools/language_serve.py` 接口（llama 旗标）确定要变、变成什么未冻结。(c) §0.5 整个计次单位（`ControlMaster` 主连接 + `ssh -S "$CM"` 复用）标「待裁定 IR-M3；未裁定前不得执行任何 SSH」，接受已裁「不能直接裁为原签含义」、CHANGE:3 未签；§0.2 `$CM`/`$BOARD_PY`、§14 IR-M8 同标待裁定。(d) 实现自证 §6 条件 1 自己写明「IR-M1/M2/M3/M4/M7/M8 的裁定可能要求操作单返工或新代码候选…本版不预设裁定结果」——裁定已落盘且 IR-M1/M3/M4/M7 均要求改动（`open_items: IR-M1,IR-M2,IR-M3,IR-M4,IR-M7`），条件 1 的前提被证伪。 |
| ② 相称测试/编译 | 成立（适用性声明） | 纯操作单候选、代码零 diff；实现只做 `bash -n` 与 `ast.parse` 并如实声明无适用 focused、不记全套通过，本角色认可该适用性声明。备注：mini §7「N-1 全套额度已用尽」与提案「R2消费」记的全套 2/3 不符（C3 PR-13 同指），属证据叙述计数错误，下一候选改正，不影响本条结论。 |
| ③ 已知 Unity 失败 | 不适用 | 本候选未运行 Unity、无新 Unity 失败。 |
| ④ 复核范围/状态板/候选/风险已更新 | 成立 | mini §5 解析式、§9 风险、§10 复核范围、状态板交接与 Log 齐备；C3 核对表与 IR 答复已落盘。 |

条件 ① 不成立 → **`REVIEW_BLOCKED`**（COORD-008 S1；workflow §4.3.1）。返工计数保持 1/2、无冻结集；本节不是 `REWORK_REQUIRED`，不产生 finding、不分级、不进未闭 finding 集。

### §2 未开轮观察（非 finding、不分级、不计次；供下一候选与下一次 R3 用，届时按增量规则重新核）

- O-1 `-play-ops.md` §1.0 第 73 行 `git diff --name-only "$PASSED" "$REL" | grep -v '^docs/'`：`grep -v` 把 `docs/evidence/…-play-ops.md`（PLAY_GOVERNING）一并过滤。副本内对本候选模拟（`PASSED=47f546c`、`REL=f84bb58`）：输出空、`non_docs_after_pass_rc=1`，即**未经复核的新操作单搭配旧通过候选可通过 §1.0**（C3 PR-8 同指）；G1 文字门不能替代这条机检。下一版应要求 `$PASSED..$REL` 的 PLAY_GOVERNING（含操作单）差异为空。开轮时涉及 AC-10/AC-6，预计 CLASS_2。
- O-2 §0.5 规定每个计次单元先建 `ControlMaster` 主连接、单元内一律 `ssh -S "$CM"` 复用；而准备单元 #1 的发起块（`-mini-ops-prep.md` §2.3）`Popen(["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", "Jetson", …])` 不带 `-S`——按 §0.5 口径单元 #1 要么是 2 条认证连接（超「准备 1」），要么 §0.5 对单元 #1 不适用而未写明；两份文件对同一动作给出不同命令（C3 PR-10 同指）。随 IR-M3/CHANGE:3 裁定一并统一。
- O-3 §14「任何单元提前 STOP 时，其余单元不再开启」与 §13 `S-REBUILD`「仅确认 A5 非主臂帧/发布段限制时下一既定剧本可继续」：后者是单元 #3 内的剧本级继续、前者是单元级停止，文字未写明 `S-REBUILD` 不算「单元提前 STOP」，操作员可能读成两种动作，应逐字写明。
- O-4 §3.5 `tar -cf … $PATHS`、附录 B `set -a; . <(…)` 依赖 bash 分词与进程替换；本版删去旧版「zsh/bash 均可」后未写明命令 shell，Air 缺省 zsh 不按空白分词。下一版在抬头写明「全部命令块在 `bash` 中执行」。
- O-5 §4 启动块 `cd "$BOARD_CODE" && umask 077; date -u +%FT%TZ` 之后 `env … /usr/bin/python3 -I -S -B tools/language_serve.py …` 独立成句：`cd` 失败时仍会执行启动（在错误目录以 `can't open file` 失败而非 STOP 码）；建议 `cd … || exit`（C3 PR-12 同类）。
- O-6 `-mini-ops-prep.md` §7「N-1 全套额度已用尽」应为「累计 2/3、本轮未跑」（见 §1 ②）。

O-1…O-6 均未在本候选上分级，不是冻结集成员。`RED_LINE`：本候选零代码、零真值路径改动，未见。

### §3 UNITY_NA

本候选未申请 `UNITY_NA`；AC-14/15/18 与 AC-16 板端仍 `NOT_RUN`。无附议对象。

### §4 消耗与限制

- consumed = none（零 SSH/ping/复制/模型/板/Unity/runtime/测试/回放/全套）。
- 未验证：操作单任何命令在 Air/板上的真实行为（本角色与实现者均未执行）；Air 侧事实（来源链原件、`.venv-yoloe`、`ssh -G`）未核；本节不对板端环境做任何主张。

### Verdict（R3@K1K2K3K4 派发）

**`REVIEW_BLOCKED`**：稳定门条件 ① 不成立（§1），不开 `R3@K1K2K3K4`、不计复核轮次、返工计数保持 1/2。下一步：接受角色消费本节并把 §2 观察转给实现；待用户对 CHANGE:1…4 与 `SLOT:FACT:1` 裁定、接受冻结文本后，实现出新稳定候选（IR-M1 若选代码路线则含 `tools/language_serve.py` 与 AC-7 测试，连同操作单返工）回同一停点 `K1K2K3K4`，按 workflow §4.3.1 自证、经接受核对后再交复核（本候选未开复核轮，「复核返工直回复核」不适用）；届时复核轮仍编 `R3@K1K2K3K4`，增量基线 = R2 §0 轮候选、全量基线 = R2 通过候选。本节不写通过指针。

## R3@K1K2K3K4（2026-10-07）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-LOOP-002-R3@K1K2K3K4-20261007T173736Z-fcae`，`requested.round = R3@K1K2K3K4`）。上一节「R3@K1K2K3K4 派发」为 `REVIEW_BLOCKED`、未开轮；本节是本停点第 3 个实际复核轮。增量轮（COORD-009 (b)）：修复触及行基线 = R2 §0 轮候选，全量基线 = R2 通过候选，两者同值（`47f546cc…02fd0`），故本轮 PLAY_GOVERNING 增量 = 全量 PG diff，逐行全读。零消耗：零 scenario/session/run ID、零 Unity/Play、零 VLM/API/GPU、零 SSH/板/复制/下载/pip/runtime、零真实模型、零归档回放、零全套重跑；只在一次性副本内读码、重跑 focused、做修前红复算与只读探针（脚本/输出在会话暂存目录，不入仓）；主树只写本文件与状态板。

### §0 候选、基线、稳定门与开轮资格

- `round_candidate: 4ba53335d4abd5598ad85b052fd3c384480e505b`（派发块指定；运行时核：`git log main --grep='^P1-ENG-LOOP-002 稳定候选 收工'` 唯一命中且相等，是 `origin/main` 祖先；代码候选 `d8d4ddc1…1a625` → 本候选只有 4 个证据/状态文档，`git diff --stat` 核实）。
- 全量/增量 diff：`git diff --name-only 47f546c..4ba5333` = 22 路径（与 C4 §0 相同）。PLAY_GOVERNING 7 路径：`controller/language_selector.py`（+193）、`tools/language_serve.py`（+490）、`tools/language_latency.py`（+116）、`tools/eng_loop2/llama_adapter.py`（+22）、`tests/test_llama_server_adapter.py`（+752）、`tests/test_language_latency.py`（+195）、操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md`（+479/−…）；冻结件/禁改路径（`language_loop.py`、`language_bridge.py`、`gated_publisher.py`、`scenario_tether.py`、`track_loop.py`、`resident_core.py`、`trackers.py`、`det_assoc_tracker.py`、`tools/eng_sft`、`tools/eng_jet`、`tools/eng_acq`、`analyze_play.py`、`deploy_digest.py`、`Assets/`、`config/`）`git diff --stat` 为空。其余 15 个 `docs/` 路径按类别与写入角色核（接受：提案各答复节/核对表、C3 证据、`implementation-status.md`、`phase1-single-drone-design.md` v0.3.63–67 指针与 LOOP-002 状态注记；supervisor：`authorizations.md` 6 条用户答复代录、`supervisor-dispatch.jsonl`、`parked-status.md` 一处指针；实现：mini/precheck/r3answer/stable 证据、两份日志、状态板；复核：本文件 R3 派发节），不含运行时代码或工作流基础设施改动。
- **稳定门（workflow §4.3.1 四条件，独立核）**：① 范围/接口冻结 **成立**——R3 派发 §1 ① 指出的三处未冻结项已消除（IR-M7 占位→现行 300 s；IR-M1 十旗标→`LLAMA_RESOURCE_FLAGS` 逐字；IR-M3 主连接→操作单第 0.5 节 `unit_open/chan/unit_close`），第 4 节 `<n>`/`<R_n>` 占位→`case` 派生；剩余尖括号为运行时取值。C4 对 R-1 的异议是「实现是否忠实于已冻结文本」，属 finding 而非未冻结，见 R3-1。② 相称测试 **成立**——focused 本轮重跑（下）全绿；停点全套 1 次由实现者证据承担：本轮只读解析 `-tests-stable.log` 与 `-tests-rework1.log` 的 `^(FAIL|ERROR): ` 集合，**逐行相同（13 项）**，新增 0；本候选触及 `llama-server` 启动命令（真实模型加载器路径），窄修替代不适用，实现已用 N-1 第 3/3 次，本角色不要求再跑全套。③ 零 Unity，不适用。④ 候选解析式、§7 复核范围、§9 风险、状态板齐备。→ 不判 `REVIEW_BLOCKED`。
- 开轮资格：PLAY_GOVERNING diff 非空 → 开 `R3@K1K2K3K4`。
- 复核副本 `.claude/worktrees/review-P1-ENG-LOOP-002`（detach 于候选）；测试树哈希（`git ls-files tests | xargs cat | sha256` 前 16 位）`d26fbfa69b6630cc`（R2 `3de6748fafb9668a` → 本候选新增两文件 34 例）。解释器：系统 `python3`（与实现者 focused 同口径）；数据根解释器 `~/TetheredDroneTracking-full/.venv-yoloe` 本机不存在（`ls` 复核），本候选未改跟踪器文件，跟踪器套件不单跑。
- **focused 重跑**（副本内，`YOLO_OFFLINE=true YOLO_AUTOINSTALL=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`，九模块同 R1/R2，输出写会话暂存目录只回显摘要）：**Ran 488 — OK（skipped=4）**，50.7 s（实现者 skipped=3，环境差异同 R2）。跑后副本 `git status --porcelain` 为空。
- **实现者修前红主张复算**（副本内 `git checkout $PASSED -- controller/language_selector.py tools/language_serve.py tools/language_latency.py tools/eng_loop2/llama_adapter.py`，保留新测试，逐类运行、90 s alarm，跑完 `git checkout HEAD --` 恢复、`git status` 空）：`JetsonSingleRoundStopTests` 2F+3E；`LongPollServerTests` 7E；`LlamaResourceFlagsTests` 2F；`HealthPollLedgerTests` 1F+5E；`TwoBatchLedgerTests` 1F+1E；`ClientBudgetGuardTests` 6E；`LongPollClientTests` 在旧客户端上**挂起**（alarm 142；旧短轮询在替身时钟下无限轮询，与 `-stable-redgreen.log` 所述 2 例超时一致）。相对 `$PASSED` 的红集合覆盖中间提交 14 例 + 本轮 20 例，新测试确实约束新行为；3 例保持性断言照绿与实现者说明一致。

### §1 修复触及行逐文件核对（7 个 PLAY_GOVERNING 路径全部读完整 diff；直接关联读 `HttpAdapter._call/predict_one/bind_identity`、`handle_one_request/_access_finish`、`measure_round/measure_host/jetson_adapter_factory`、`LanguageSession` 的 `worker_died/worker_stuck` 处理）

| 文件 | 结论 |
|---|---|
| `controller/language_selector.py` | 新增 `LONG_POLL_MAX_WAIT_S=4.0`/`LONG_POLL_MAX_RESULT_ATTEMPTS=16`/`LONG_POLL_PARAM`、`long_poll_wait_text`（向下取整毫秒、<1 ms → `None`、上限 4.000）；`HttpAdapter.long_poll` 只在 `bind_identity` 经 `validate_llama_identity` 返回六键非空且 `status()` 逐键核过后置真（R-4 成立）；`http_budget` 快照与 `_budget_guard`（`inference`/`business`/`necessary` 三类判据与操作单第 0.6 节一致；无快照不拦）、`_take_budget`（5 个 int 键、bool 排除）；`_call` 先守账再 `deadline_s<=0` fatal，回包 `error=="S_ENVELOPE"` → fatal `worker_stuck`；`predict_one` 的 `/status` 恢复路径 `business`、`POST /query` `inference`、旧短轮询 `/result` `business`；`_long_poll_result`：循环顶 `hard_left<=0` → fatal、`ret_left<=0` → abandon、`attempts>=16` → abandon（`timeout`，`awaiting_idle`）、`w=min(4,ret_left,hard_left)` 截毫秒、`_call(..., remaining_hard())`、回显核（`query_id` 相等且 `wait_s` 数值等于发出文本）不符 → `worker_died` 不回退（R-5 成立）、`done` 回包后重核两截止（逾期不接纳）、`failed`/`stuck`/未知状态映射与旧路径同（R-2 成立）、`pending/busy` 不 sleep。**I/O 截止只随 T_hard 收缩 → R3-1**。 |
| `tools/language_serve.py` | 模块文档退出码 6；`HttpBudgetLedger`（读入既有行累计、`batch_start`、上限不一致/坏行/未知 kind → `LedgerRefused`→退出 3；`admit` 计数即时、`record` 落行、`business_room`）；`parse_result_target`（`urlsplit`、`strict_parsing`、恰一个 `wait_s`、有限且 `0<w<=4`、空 query_id/fragment 拒绝）；`_result_query_id` 去查询串；`_ledger_kind`；`parse_request` 成功即 `admit`，`_access_finish` 对未解析成功的连接 `admit("other")` 并 `record`（见 §3 O-7）；`_reply` 附 `http_budget`；`_budget_refused` 429（GET 先于路由、POST 读完体后）；`do_GET` llama 分支分离参数、无参即时、有参 `result_wait`（条件变量 + 0.05 s 重核 stuck，仍持同一把锁，`submit` 完成/失败 `notify_all`）并回显 `wait_s`；local-hf 分支逐字不变（`long_poll=False`、`budget=None`）；`LLAMA_RESOURCE_FLAGS` 十项逐字接在原四项之后；`_wait_llama_ready` 每次 `/health` 发出前 `business_room()`、`admit→health_attempt→record`，不足 → `ReadyFailure(envelope)`→退出 6；`_main_llama` 新增 `--http-ledger`/`--non-inference-reserve` 必需（`_LLAMA_REQUIRED_COUNT=8`）、`--non-inference-limit`/`--inference-limit` 只许调低、预留域 `0..limit-1`、起子进程前 `business_room()` 否则退出 6 不加载、`build_server(..., budget, long_poll=True)`。 |
| `tools/eng_loop2/llama_adapter.py` | `health_attempt` 返回 `(码, None)`/`(None, "timeout|error: …")`，`health_status` 改为其包装、语义不变；只连 loopback 未改。 |
| `tools/language_latency.py` | `EXIT_MEASURE_NOT_OK=7`、`JETSON_MAX_ROUNDS=1`；`measure_round(stop_on_failure)`：`planned` 序列、首个 `failures` 非空即 `break`、`not_attempted=len(planned)-position`（`SelectorError` 与固定 60 s 截止两类失败同入 `failures`）；`summarize_round` 只在 `stop_on_failure` 时加两键（旧宿主键集不变）；`measure_host(max_rounds, stop_on_failure)` 透传、缺省 2 轮不变；`jetson_probe_failure_report`（`FAIL`、`p95_s None`、`model_identity {}`、`qualifies False`）；`main` jetson 分支 `jetson_adapter_factory` 抛 `SelectorError`（探针在工厂构造时即发 `/status`）→ 失败报告，否则 `measure_host(..., max_rounds=1, classify=True, stop_on_failure=True)`；非 OK 退出 7。 |
| `tests/test_llama_server_adapter.py` | 假 llama 加 `no_listen`/`slow_health`；夹具加 `--http-ledger`/`--non-inference-reserve`；`_recording_opener` 记录含查询串的目标；新增 `LlamaResourceFlagsTests`（2）、`HealthPollLedgerTests`（4，含真实子进程三种失败结局与退出 6 两例）、`TwoBatchLedgerTests`（2，真实两次启动共账）、`ClientBudgetGuardTests`（6，真实 `build_server`+真实回环）、`LongPollServerTests`（6，真实服务：分离/回显、11 种坏参数、完成/失败即回、stuck 即回、到期回、local-hf 旧解析）、`LongPollClientTests`（8，替身时钟/opener：w 序列与 I/O 截止、16 次、不重试不回退、守账、逾期 done、映射、未绑定短轮询、真实服务端到端一次 result）；`IsolatedDeployEntryTests` 端到端加长轮询断言。`test_wait_is_min_of_4s_and_both_remaining_deadlines_and_io_tracks_t_hard` 只断言 I/O 随 T_hard（R3-1）。 |
| `tests/test_language_latency.py` | `FakeService` 分离参数并回显 `wait_s`、`FAILED_INFERENCE`、`status_ok`；`JetsonSingleRoundStopTests`（6）经真实 `main`/`jetson_adapter_factory`（只注入 opener、计工厂调用）：成功 35 POST / 2 status / 35 result 全带 `?wait_s=`；第 13 次失败即停、无第二轮/第二 bind、`not_attempted=22`、无 p95；预热失败停；探针失败零推理且 `k-receipt` 拒绝；`S_ENVELOPE` 原因保留；旧宿主缺省两轮。 |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md` | 抬头 bash/五门/门与单元对应；第 0.4 节非推理行补长轮询口径；第 0.5 节三函数与通道闭集（1/7/2）、`-O check` 失败即 `S-SSH`、回退闭合选项指向 `127.0.0.1:1`；第 0.6 节代码守账、有限路径表（status 3/≤11 出处核与 `jetson_adapter_factory`、`LanguageSession.__init__`/`validate_jetson_session` 一致）、预留 25/11 来源、守账式、投影更正；第 1.0 节固定 `$REL`、pass/round 行序、祖先、PG 定义漂移核、PG（含本操作单）差异须空（O-1 已闭：本候选 `PASSED=47f546c`、`REL=4ba5333` 下 PG_DIFF 非空 → STOP，副本内模拟核实）——**行序正则不命中且未核 `blocks_consuming_gate` → R3-3**；第 2 节 Air 前置（`read_smoke_rows` 零模型）与单元 #1 经 `chan`（O-2 已闭）；第 3 节 `cd … || exit 97`；第 4 节 `case` 派生 `R_N`、`cd … || exit 97`（O-5 已闭）、启动命令含 `--http-ledger`/`--non-inference-reserve "$R_N"`/`--llama-ready-timeout-s 300`、退出码 3/4/5/6 分流——**`ss` 失败不停 → R3-2**；第 5 节 `measure` 非 0 即停、7 按首个 `detail` 分流、0 才 `k-receipt`（AC-15 修订 1(c) 成立）、smoke 集身份（R-3 成立）；第 13 节 `S-ENVELOPE` 含退出 6 与 `measure` 退出 7 分支、`S-RECEIPT` 排除 `measure` 非 0；第 14 节单元级 STOP 与 `S-REBUILD` 剧本级继续逐字区分（O-3 已闭）；附录 P `readelf`/`ldd`/`pgrep` 失败即停、`SS_FAIL` 显式。§3.6 节闭集 13 节与 §6.2 STOP 表齐（AC-10 结构成立）。 |

### §2 AC 逐项（依据列 `BC-n` 读作 AC-n；未改动行结论随 R1/R2 携带）

| AC | 结论 | 本轮依据 |
|---|---|---|
| AC-1/3/4/5/8/11/12/17 | 成立（携带） | 对应生产文件相对 `$PASSED` 零 diff（§0 cmd）；`test_loop2_freeze` 照绿。 |
| AC-2 | 成立 | 冻结件 sha 测试照绿；禁改路径 diff 空。 |
| AC-6 | 成立 | `SingleHostReceiptTests`/`JetsonSessionStartTests`/`CleanWorkingTreeProductionPathTests` 在替身改为长轮询回显后照绿；`validate_jetson_session` 的 `status_document` 走 `necessary` 守账。 |
| AC-7（含修订 1/2/3） | **不成立** | 修订 1、修订 2(a)（十旗标逐字）、2(b)（健康逐次入账、两批共账、请求前守账、429 兜底、退出 6）、修订 3(a)(b)(d) 成立；**修订 3(c)「I/O 随两种剩余收缩」不成立 → R3-1**（C4 PR-15 独立核实为真）。 |
| AC-9 | 成立 | 新 import 只有 `math`/`os`/`urllib.parse`；`test_loop2_isolation` 与 `IsolatedDeployEntryTests` 闭包用例照绿。 |
| AC-10（含修订 1） | **不成立** | 节闭集、修订 1(a) 主连接协议、1(b) 固定 `$REL`/PG 空差异/整树干净/原流先于登记均成立；**第 4 节 `ss` 失败路径 → R3-2；第 1.0 节行序正则不命中与未核消耗性门阻断 → R3-3**（C4 PR-19/PR-18 独立核实为真）。 |
| AC-13 | 成立 | 22 路径 PG 7 个均在 §4.1 归属表；全套失败集合与上一全套逐行相同（本轮解析核）；闭集外文档逐文件说明在 stable §5。 |
| AC-14 / AC-18 | `NOT_RUN` | 阶段 B 未放行。 |
| AC-15（含修订 1） | 代码/操作单成立；板端 `NOT_RUN` | `JetsonSingleRoundStopTests` 读码对照 (a)(b)(c) 逐条成立；修前红 2F+3E。 |
| AC-16 | 阶段 A 部分携带；板端 `NOT_RUN` | `-assets-local.json` 未改。 |

C4 §2 五条实现读法：R-2/R-3/R-4/R-5 本轮独立读码成立（见 §1）；R-1 不成立（R3-1）。C4 §4 PR-15 → R3-1；PR-18 → R3-3；PR-19 → R3-2；PR-16/PR-17 核为非 finding（§3 末）。

### §3 Findings

| ID | 分级 | 依据 | 阻断 | 摘要 |
|---|---|---|---|---|
| R3-1 | CLASS_2 | `BC-7` | 是 | `HttpAdapter._long_poll_result` 把单次 I/O 截止传为 `remaining_hard()`，`_call` 取 `min(5 s, T_hard 剩余)`，不随 T_ret 剩余收缩；AC-7 修订 3(c) 证明方式逐字要求「I/O 随两种剩余收缩」，具名测试只断言 T_hard；操作单第 0.6 节同样写成 `min(5 s, T_hard 剩余)`。附分级/合同争议（下） |
| R3-2 | CLASS_2 | `BC-10` | 是 | 操作单第 4 节板上启动块 `ss -ltn \| awk \| grep -E … && { STOP }`：`ss` 本身失败（非 0/无输出）时 `grep` 无命中、`&&` 不触发，`pipefail` 只改管道状态不进 STOP，随后 `pgrep` 双 rc=1 即继续启动服务（GGUF 加载 ≤2 的消耗步骤）；附录 P 的 `SS_FAIL` 只覆盖准备单元 #1，不覆盖单元 #2/#3 每次启动 |
| R3-3 | CLASS_2 | `BC-10` | 是 | 操作单第 1.0 节放行门：(a) `grep -nE '^round_candidate: [0-9a-f]{40}$'` 在本文件实际写法（`- \`round_candidate: …\`（…）`）下命中 0 行（本轮在 `$REL=HEAD` 上实测 anchored 0 / unanchored 2），`LAST_ROUND_LINE` 恒空、`PASS_LINE -gt 0` 恒真，「最新有效通过机读行」的行序判据空转；(b) 未核 `passed_candidate` 之后是否存在未按文件顺序 release 的 `blocks_consuming_gate:` 行——这是 PG 空差异无法覆盖的唯一门状态（未改动行上的 finding 阻断消耗性门），AC-10 修订 1(b) 逐字要求「核…最新有效通过机读行与其后门状态」 |

#### R3-1 单次 I/O 截止只随 T_hard 收缩（`controller/language_selector.py::_long_poll_result`、`_call`；`tests/test_llama_server_adapter.py::LongPollClientTests.test_wait_is_min_of_4s_and_both_remaining_deadlines_and_io_tracks_t_hard`；操作单第 0.6 节）

- 合同：AC-7 修订 3(c)「保持 5 s 单次 I/O 上限，剩余截止不足时收缩 I/O；回包后重新核 T_ret/T_hard」+ 证明方式「…I/O 随两种剩余收缩、回包后软/硬截止拒绝逾期 done…」。接受 C4 §2 已裁 R-1「不满足」且「不认可或追加合同豁免」。
- 实现：`document = self._call("GET", f"/result/{query_id}?wait_s=…", remaining_hard(), …)`，`_call` 内 `timeout = min(HTTP_IO_DEADLINE_S, deadline_s)`。例：T_ret 剩余 0.5 s、T_hard 剩余 10 s → `w=0.5`、I/O 5 s。具名测试第二段只在 `t_hard_s=2.0` 下断言 `io_deadlines == [2.0, 0.75]`；第一段 `t_ret_s=3.0` 只断言 `waits`，不断言 I/O。行为差异限于服务端不按 w 回包/链路停摆的失败路径：T_ret 已过后客户端最多再阻塞 4.5 s 才报 `timeout`。字面不符成立，CLASS_2（失败路径截止）。
- **分级/合同争议（交接受角色复判，workflow §4.4「复核或实现角色提出分级争议」）**：按证明方式逐字修（I/O = `min(5, T_ret 剩余, T_hard 剩余)`）时，凡 T_ret 剩余 < 4 s 即 `w == I/O 截止`：客户端在发送前起算超时、服务端在收到后起算 w（`result_wait` 另有 ≤0.05 s 重核粒度），客户端套接字超时几乎必先于服务端到期回包触发 → `_call` 捕获 `TimeoutError` 抛 `worker_died`（`_mark_unconfirmed`，**不置 `awaiting_idle`**），而非本应的 `timeout: T_ret exceeded`（`awaiting_idle`）；会话侧 `worker_died` 走 `_designate_failure` 普通失败/重试，下一次 `predict_one` 不经 `/status` 确认 idle 即再 `POST /query`（服务端仍 busy → `SERVER_BUSY`，该 POST 已按「含被拒」计入推理尝试账）。即字面修复会把 T_ret 正常到期变成原因码漂移 + 多一次推理账。实现者 R-1 的竞速理由在技术上成立，但按流程须以 CLARIFY 回接受而非自读。建议接受在冻结集裁定时二选一并冻结文本：(i) 把 (c) 证明方式改为「w 随两种剩余收缩、I/O 随 T_hard 收缩」（= R-1，代码不改，测试名/断言不改）；(ii) 保留「两种剩余」但规定 `I/O = min(5 s, T_hard 剩余, T_ret 剩余 + ε)` 并冻结 ε（例如 0.5 s）。本角色不代选。
- 闭合绑定（workflow §4.4 四条）：具名回归放 `tests/test_llama_server_adapter.py::LongPollClientTests`（替身时钟/opener 为生产 `HttpAdapter` 的注入点，与本候选既有用例同构）：在 `t_ret_s=3.0, t_hard_s=60.0` 下断言每次 `/result` 的 `timeout` 参数序列等于裁定后的公式（(ii) 例：`[3.0+ε, 1.75+ε, 0.5+ε]` 各与 5 取小）；若裁 (i) 则不改代码，闭合改为定点复看该测试名与 (c) 文本一致。下一轮由本角色修前红/修后绿核实；`NOT_MECHANIZABLE` 不适用（(ii) 时）。

#### R3-2 第 4 节启动块 `ss` 失败不停（`docs/evidence/P1-ENG-LOOP-002-play-ops.md` 第 4 节第 240 行；C4 PR-19）

- 合同：AC-10 §3.6「服务前台起停与端口释放」+ §6.2/第 13 节 `S-PRECHECK`「残留服务占端口」；PR-12 已采纳的 fail-fast 纪律（附录 P `SS=$(ss -ltn 2>&1); r=$?; … [ $r -eq 0 ] || STOP "SS_FAIL"`）。
- 实现：`ss -ltn | awk '{print $4}' | grep -E ':(18081|18082)$' && { echo "STOP S-PRECHECK port_occupied"; exit 97; }`。`ss` 失败（命令缺失/权限/非 0）→ 无输出 → `grep` rc 1 → `&&` 不执行；`set -o pipefail` 只使管道状态非 0，而该状态不被检查；下一行 `pgrep` 两次 rc=1 即继续 `env … language_serve.py`。可达：单元 #2/#3 每次服务启动（消耗 GGUF 加载 1/2、服务驻留与 SSH 单元），端口实占时结果是 `llama-server`/`language_serve` 绑定失败 → 退出 4/5 → 被记为「首次主臂失败、停全部」而非零消耗的 `S-PRECHECK`。「操作员或工具的行为会因这段文字而不同」成立 → CLASS_2。
- 修复方向：与附录 P 同型——`SS=$(ss -ltn 2>&1) || { echo "STOP S-PRECHECK ss_failed"; exit 97; }`，再对 `$SS` 做端口匹配；同块 `pgrep` 已区分 rc。
- 闭合：`NOT_MECHANIZABLE`（操作单文本，仓库无可写断言；`bash -n` 不覆盖语义）→ 下一轮定点复看第 4 节启动块。

#### R3-3 第 1.0 节放行门：行序正则空转、未核消耗性门阻断（`docs/evidence/P1-ENG-LOOP-002-play-ops.md` 第 1.0 节第 145–151 行；C4 PR-18）

- 合同：AC-10 修订 1(b)「运行时解析并固定已推送发布引用，从该引用读取复核/授权，核候选祖先关系、**最新有效通过机读行与其后门状态**；通过候选至该引用只允许规则许可的非 PLAY_GOVERNING 文档差异」。
- 实现与实测：(a) `LAST_ROUND_LINE=$(… grep -nE '^round_candidate: [0-9a-f]{40}$' …)`——本文件 R1/R2 §0 的机读行写法为 `- \`round_candidate: <sha>\`（…）`（AGENTS.md 只规定「§0 写 `round_candidate: <40 位 SHA>`」，`tools/check_docs.py` 的同类正则容许前导 `-`/`*` 与空白），anchored 正则在 `$REL=HEAD` 上命中 0 行（`grep -c` 实测 0；去锚 2），于是 `test "$PASS_LINE" -gt "${LAST_ROUND_LINE:-0}"` 恒真：`REWORK_REQUIRED` 轮写在通过行之后时该判据不会 STOP（当前靠 PG 空差异兜底，但该判据本身为空转）。(b) 未检查 `blocks_consuming_gate:` / `releases_consuming_gate:` 按文件顺序配对后是否仍有未 release 的 block；这类 block 来自**未改动行**上的 `上轮漏检` CLASS_2，候选本身 PG 可以为空，是第 1.0 节 PG 空差异检查覆盖不到、而 workflow §4.4 专门为消耗性门设置的机读门状态。状态板 `PAUSED_CONSUMING_GATE_BLOCKED_*` 与 `check_docs.py` 是另一层防线，但不在本操作单的「严格双来源」命令内，操作员按本节会打印 `RELEASE_REF_OK`/`PG_DIFF_EMPTY_OK` 继续。
- 其余（C4 PR-18 第三点「其余差异是否逐一核为许可文档」）：PG（含本操作单）空 + PG 定义漂移核 + 原样记录其余路径，本角色判足——`origin/main` 上并行工作项的文档提交不可能用本项 §4.1 白名单枚举，而「规则许可」在 PG 空的前提下即「非 PLAY_GOVERNING」；非 finding。
- 修复方向：(a) 用 `grep -noE 'round_candidate: [0-9a-f]{40}'`（同 `-stable-candidate.md` §0 的无锚形式）取行号；(b) 在 `REVIEW_TXT` 上按文件顺序配对 `blocks_consuming_gate:`/`releases_consuming_gate:`（正则同 `tools/check_docs.py`：`^\s*(?:[-*]\s+)?blocks_consuming_gate:\s*(\S+)\s*$`），存在未 release 的 block → `STOP S-PRECHECK consuming_gate_blocked <finding-id>`；账本 `RELEASED_SCOPE_GAP` 路径按 `implementation-status.md` 同一规则读取或直接复用 `$DOCWT` 内 `check_docs.py` 的结论并写明。
- 闭合：`NOT_MECHANIZABLE` → 下一轮定点复看第 1.0 节，并在副本内以 `$REL` = 候选重跑该段命令核 `LAST_ROUND_LINE` 非空、block 配对输出。

其余核对未产生 finding：未发现 CLASS_1、`RED_LINE`（真值隔离 AST 用例 + 本轮读码：`controller/`、`llama_adapter.py`、`language_serve.py` 零真值/评分导入；评分器零 diff）、`上游漏检`、`上轮漏检`。CLASS_3 无。

非 finding 备注（本轮核过，不分级、不入冻结集）：

- **PR-16（`failed` 回包跨 T_hard）**：`_long_poll_result` 的 `failed` 分支不重核截止，与旧短轮询逐字同语义（旧循环亦只在发请求前核时间）；`failed` 表示服务端模型已结束（非 stuck），AC-7 修订 3(c) 逐字只禁止「逾期 `done`」；单次 I/O ≤5 s 使跨期窗口与旧路径相同。若接受希望逾期 `failed` 也 fatal，属合同澄清，不在本轮记债。
- **PR-17（亚毫秒剩余）**：`long_poll_wait_text` 截毫秒、<1 ms 视为无正剩余，按 `hard_left <= ret_left` 决定 fatal/abandon：若改为发出 `wait_s=0.000x` 请求，服务端即时回 pending 后回包重核必然逾期，结局相同且多耗一次非推理账；1 ms 是线格式分辨率而非新容差。
- **O-7（新观察）**：计量/账模式下，连接建立后未发出任何请求行的连接（`raw_requestline` 空）也经 `_access_finish` 入账一行 `kind=other`（`method/path` 为 `null`），计入非推理 200——方向为多计（保守），本机只对 Tailscale 地址监听、生产客户端不会产生此类连接；记为已知边界，是否排除由接受定。
- **O-8**：`result_wait` 用 `time.monotonic()` 而非 `self._monotonic`（可注入时钟），只影响测试可注入性，不影响生产。

### §4 UNITY_NA

本候选未申请 `UNITY_NA`；AC-14/15/18 与 AC-16 板端为 `NOT_RUN`。无附议对象；阶段 A 代码候选通过只到独立复核通过，`DONE` 仍需阶段 B 的 Unity/板端证据。

### §5 限制、未验证与消耗

- 本轮未重跑停点全套（实现者第 3/3 次全套的失败集合本轮只读解析核与上一全套逐行相同）、未做归档回放、未碰板/Unity/VLM/SSH。
- 长轮询/单轮测量/两批账只在回环 HTTP/1.0 夹具、替身时钟与替身适配器下验证；真实 Jetson、Tailscale 半包/复位、`llama-server` b11381 对十旗标与 `response_format` 的实际行为、板端 Python 动态闭包（PR-14）均未验证（阶段 B 如实记）。
- 跟踪器相关套件未在数据根解释器下重跑（本机不存在该环境）；本候选未改跟踪器文件。
- consumed = none（零 ID/Play/API/GPU/下载/pip/SSH/板/复制/runtime；零模型；零回放）。

### Verdict（R3@K1K2K3K4）

**`REWORK_REQUIRED`**（本停点第 2 次，2/2）。阻断：R3-1（CLASS_2，`BC-7`，附分级/合同争议交接受复判）、R3-2（CLASS_2，`BC-10`）、R3-3（CLASS_2，`BC-10`）。按 workflow §4.4 / COORD-009 (c)：**未闭 finding 集 {R3-1, R3-2, R3-3} 冻结**，交接受角色逐条裁定「范围内必修」或 `SCOPE_GAP` 记债（R3-1 需同时裁定合同文本 (i)/(ii)）；实现按裁定返工后直接回本角色（不经核对轮）。下一轮 `R4@K1K2K3K4` 即 workflow §4.4 所称「轮 3」：检查范围 = 冻结集 + `RED_LINE` + 修复触及行上的 CLASS_1/2，终局——通过，或回用户（决策信封 D2b 在效时按 §4.4 回 supervisor 一次定向返工，之后终局）。是否开 `R4` 按开轮资格（PLAY_GOVERNING diff 非空：R3-2/R3-3 的操作单返工必非空）决定。不写 `passed_candidate`。AC-1…6、8、9、11…13、15（代码）、17 本轮成立的结论随候选携带。本轮不写 `blocks_consuming_gate`（三条均在修复触及行上，非未改动行 `上轮漏检`）；状态板无 `Consuming=yes` 活跃行。

## R4@K1K2K3K4（2026-10-07）— 终局轮

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-LOOP-002-R4@K1K2K3K4-20261007T195333Z-a977`，`requested.round = R4@K1K2K3K4`）。本轮是 R3 `REWORK_REQUIRED`（2/2）后的终局轮（workflow §4.4 / COORD-009 (c)「轮 3」；本停点「R3@K1K2K3K4 派发」为 `REVIEW_BLOCKED` 未计轮，故编号 R4）：检查范围 = 冻结集 {R3-1, R3-2, R3-3} + `RED_LINE` + 修复触及行上的 CLASS_1/2；结局只有通过或回用户——账本中本项无 `supervisor_decision_envelope`（既有三份信封 `classes: [D1, D4, D5, D6]` 均属他项且不含 D2b），接受「R3冻结集裁定」§3 亦写明未签 D2b，不存在定向返工路径。零消耗：零 scenario/session/run ID、零 Unity/Play、零 VLM/API/GPU、零 SSH/板/复制/下载/pip/runtime、零真实模型、零归档回放、零全套重跑；只在一次性副本内读码/读文档、重跑 focused、做三条 finding 的定点复看与只读探针（脚本与输出在会话暂存目录，一次性 `git clone --no-checkout` 与桩目录，不入仓、不写主树）；主树只写本文件与状态板。

### §0 候选、基线、稳定门与开轮资格

- `round_candidate: b5b0d5b9b20b61a94885531850b2ccdaf196fd37`（派发块指定；运行时核：`git log main --grep='^P1-ENG-LOOP-002 R3返工 收工'` 唯一命中且相等，是 `origin/main` 祖先；派发日志 `requested` 条目 `base_head` 为其后的诊断步骤核销提交）。操作单改动只在 `549a12644bfa0dc76657d3a9fbc848a8eead5d6d`（`R3返工 操作单候选`），其后到候选只有 `-r3rework.md` 与状态板（`git diff --stat` 核实）。
- 修复触及行基线 = R3 §0 轮候选 `4ba53335d4abd5598ad85b052fd3c384480e505b`：`git diff --name-only $R3_ROUND..$CAND` = 9 路径，全部 `docs/`；PLAY_GOVERNING 增量**只有**操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md`（+66/−19）；`-- . ':!docs'` 为空，即 `controller/`、`tools/`、`tests/`、`config/`、`Assets/` 相对 R3 轮候选零字节 diff；副本测试树哈希 `d26fbfa69b6630cc` 与 R3 相同。其余 8 个文档路径按类别与写入角色核（复核：本文件 R3 节；接受：提案「R3冻结集裁定」与复判表、`-C4-K1K2K3K4.md`、`implementation-status.md`、`phase1-single-drone-design.md`；supervisor：`supervisor-dispatch.jsonl`；实现：`-r3rework.md`、状态板），不含运行时代码或工作流基础设施改动。
- 全量 diff（相对上一通过候选 `47f546cc4934fcb74b25df6cf4ba7efbab102fd0`）= 24 路径 = R3 的 22 路径 + `-C4-K1K2K3K4.md` + `-r3rework.md`；非 `docs/` 的 6 个代码路径与 R3 §0 逐一相同，无 R3 未核对的新实现文件。R3 对未改动文件的结论随候选携带。
- **稳定门（workflow §4.3.1，独立核 `-r3rework.md` §2）**：① 范围/接口冻结成立——改动闭集恰为裁定 §1 点名的三处（本轮逐行读 diff：抬头修订记录与 G3 指针、第 0.6 节、第 1.0 节块与正文、第 4 节启动块四行），代码/测试零 diff，无新 AC/容差/额度/待裁定（§8 为已知限制而非待裁定）；剩余尖括号均为运行时取值。② 相称测试成立——纯操作单文本返工，不触及真实模型加载器、数据划分或对外指标路径，engineering §6 窄修/定点路径适用；N-1 全套 3/3 已用尽，实现如实写明未跑、不记全套通过，本角色**不要求全套**，也不申请新资源。③ 零 Unity，不适用。④ 解析式（§0）、落点与探针（§3）、复核范围（§7）、未验证项（§8）、状态板交接齐备。→ 不判 `REVIEW_BLOCKED`。
- 开轮资格：操作单已被冻结集点名，属 PLAY_GOVERNING（workflow §4.4 唯一定义），diff 非空 → 开 `R4@K1K2K3K4`。
- 复核副本 `.claude/worktrees/review-P1-ENG-LOOP-002`（detach 于候选）。解释器：系统 `python3` 跑 focused；`.venv-yoloe/bin/python`（3.12.13）只作第 1.0 节探针的 `$PY`（只读，不装包）。
- **focused 重跑**（副本内，`YOLO_OFFLINE=true YOLO_AUTOINSTALL=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`，输出写会话暂存目录只回显摘要）：`tests.test_loop2_freeze` **Ran 3 — OK**（冻结件 sha 与归属表外无 diff）；`tests.test_llama_server_adapter.LongPollClientTests` **Ran 8 — OK**（含 R3-1 具名测试）；`tests.test_loop2_isolation` **Ran 3 — OK**（`RED_LINE` 真值隔离 AST 用例）；`tests.test_check_docs -k test_ledger_released_scope_gap_row_counts_as_release` **Ran 1 — OK**（第 1.0 节复用的账本 release 规则的既有回归，实现本轮未跑）。跑后副本 `git status --porcelain` 为空。本候选代码零 diff，九模块 488 OK 的 R3 结论随候选携带，不重跑。

### §1 修复触及行逐处核对（`git diff $R3_ROUND..$CAND -- docs/evidence/P1-ENG-LOOP-002-play-ops.md` 全读）

| 位置 | 结论 |
|---|---|
| 抬头修订记录 | 追加「R3返工」版说明，指向「R3冻结集裁定」§1–2 与 `-r3rework.md`，写明未经复核、不预签通过；旧版叙述未改。非 finding。 |
| 执行门 G3 | 合同答复列表加「R3冻结集裁定」§2；其余 G1–G5 与门/单元对应逐字不变。非 finding。 |
| 第 0.6 节 | 标题加「修订 4」；长轮询条目去掉旧「单次 I/O 截止 `min(5 s, T_hard 剩余)`；回包后重核…」句，移入新条目「截止与结果接纳（AC-7 修订 4…）」：引用块逐字收录提案修订 3(c) 现行澄清文本（见 §2 R3-1），再写代码落点、具名测试与裁定 (i) 的三句说明（不承诺 T_ret 时刻立即返回、不承诺消除竞速、硬截止/fatal 与 HTTP 失败映射照旧）。`w` 公式、16 次、不回退、守账句未改。与代码/测试/裁定一致，见 §2。 |
| 第 1.0 节块与正文 | 见 §2 R3-3。块内其余（`REL` 固定、PG 展开与定义漂移核、PG 差异含操作单、其余差异原样记录）语义保持，只把 `echo STOP` 改为 `gate_stop`（置 `GATE=1`）并给 `git diff` 加退出码检查；正文把放行条件改为「末行 `RELEASE_GATE_OK` 且整段无 `STOP`」并写明与第 1.5 步 `check_docs.py` 互不替代、`$CGT` 只读不删。 |
| 第 4 节启动块 | 见 §2 R3-2。四行替换一行；其后 `pgrep` 判据、`env` 记录与启动命令逐字不变。 |

### §2 冻结集逐条闭合（副本内；探针脚本/输出在会话暂存目录，不入仓）

**R3-1（`BC-7`，AC-7 修订 4 选 (i)；裁定路径 = 文本一致性定点复看，无代码修复、不构造红绿）— 闭合。**

- 修订 4 文本 ↔ 操作单：以正则 `\*\*修订3\(c\)现行逐字澄清文本：\*\* (.*)` 从提案「R3冻结集裁定」§2 取出 294 字符，确认以 `  > <原文>\n` 整段出现在操作单第 0.6 节且只出现 1 次（Python 字符串包含判定，True）。
- 操作单 ↔ 真实代码：`controller/language_selector.py` 第 652 行 `self._opener(request, min(HTTP_IO_DEADLINE_S, deadline_s))`（`HTTP_IO_DEADLINE_S = 5.0`，第 515 行）；`_long_poll_result` 第 915 行 `self._call("GET", f"/result/{query_id}?{LONG_POLL_PARAM}={wait_text}", remaining_hard(), budget_kind="business")`；`w` 由 `long_poll_wait_text(min(LONG_POLL_MAX_WAIT_S, ret_left, hard_left))` 取；`done` 回包后重核两截止（逾期不接纳）。函数 docstring (c)「单次 I/O 截止仍为 `min(5 s, T_hard 剩余)`」与修订 4 同义。代码相对 R3 轮候选零 diff（§0）。
- 操作单 ↔ 具名测试：`tests/test_llama_server_adapter.py::LongPollClientTests.test_wait_is_min_of_4s_and_both_remaining_deadlines_and_io_tracks_t_hard`（第 1502 行起）存在、名称未改：第一段 `t_ret_s=3.0, t_hard_s=60.0` 断言 `waits == [3.0, 1.75, 0.5]`（w 随 T_ret）、原因 `timeout`、`awaiting_idle`；第二段 `t_ret_s=50.0, t_hard_s=2.0` 断言 `waits == [2.0, 0.75]` 且 `io_deadlines == [2.0, 0.75]`、全部 ≤ 5.0（w 与 I/O 随 T_hard）。没有任何断言要求 I/O 随 T_ret——与修订 4「T_ret 不作为在途单次 I/O 的 timeout 参数」一致。本轮重跑该类 8 例 OK。
- 残留旧口径检索：`controller/`、`tools/`、`tests/`、`runtime/README.md`、操作单中「两种剩余」只出现在第 0.6 节引用块（修订 4 原文自身对 w 的描述）与其后一句「断言 `w` 随两种剩余、I/O 随 T_hard」，无「I/O 随两种剩余」旧读法残留。提案「CHANGE5答复落实」§2 修订 3(c) 原句由修订 4 显式替代，属接受文件，不在本角色范围。

**R3-2（`BC-10`，操作单第 4 节启动块；`NOT_MECHANIZABLE` → 定点复看 + 桩探针）— 闭合。**

- 读码：`SS=$(ss -ltn 2>&1); ss_rc=$?` 先捕获；`[ "$ss_rc" -eq 0 ] && [ -n "$SS" ] || { STOP ss_failed; exit 97; }` 停在 `pgrep` 与启动之前；之后 `awk '$4 ~ /:(18081|18082)$/ {print $4; f=1} END {exit f ? 0 : 1}'` 以退出码三分（0 占用 / 1 空闲 / 其余 awk 失败），`case` 对三种都给出动作，非 1 一律 `exit 97`。不再有 `grep -q`，`pipefail` 歧义消失；`ss` 只打印表头（无监听）时 `SS` 非空 → 走端口判定 → 空闲，符合预期。
- 探针（副本内抽出候选块「`SS=` 行 … `pgrep` 判据行」追加 `echo REACHED_SERVICE_START`，`PATH` 前置桩 `ss`/`pgrep`（`pgrep` 恒 rc 1），Air `/bin/bash` 3.2 `--noprofile --norc -c 'set -o pipefail; . 片段'`）：`ss` rc 1 无输出 → rc 97 `ss_failed rc=1`；rc 0 空输出 → rc 97 `ss_failed rc=0`；rc 2 只有 stderr 文本 → rc 97 `ss_failed rc=2`；成功且 `100.100.100.100:18082` 被占 → rc 97 `port_occupied 100.100.100.100:18082`；成功且只有 22/46273/`[::]:22` → `PORTS_FREE_OK` 并到达启动。**五个分支均未在失败时到达服务启动。**
- 修前对照（R3 轮候选同一片段）：三种 `ss` 失败分支**全部** rc 0 到达 `REACHED_SERVICE_START`（复现 R3-2），被占时 STOP、空闲时启动——与新版差异恰为三条失败分支。
- 板端 `awk`（mawk/gawk）未运行：`$4 ~ /…/`、`END {exit expr}` 为 POSIX 写法；即使板端 awk 语法不兼容，退出码非 0/1 → `port_check_failed` STOP，方向 fail-closed，不构成 finding（实现 §8 已如实列为未验证）。

**R3-3（`BC-10`，操作单第 1.0 节放行门；`NOT_MECHANIZABLE` → 定点复看 + 以 `$REL` = 候选等重跑）— 闭合。**

- 读码：(a) `MR='^[[:space:]]*([-*][[:space:]]+)?`?'` 配合 `round_candidate: [0-9a-f]{40}` + `(`|[[:space:]]|$)`，只认行首（可带列表记号/反引号）的键值行，正文引用（如「本节不写 `round_candidate:` / `passed_candidate:` 机读行」）不命中；取最后一条 round 行与 pass 行，缺任一、`PASS_LINE ≤ LAST_ROUND_LINE`、或 `PASSED` 非 `$REL` 祖先均 `gate_stop`；(b) `pg_rc` 非 0 → `pg_diff_failed`，不再把失败当空差异；(c) `git archive "$REL"` 导出 `docs/reviews`、`docs/implementation-status.md`、`tools/check_docs.py` 到 `$OUT/release/cg-tree.*`，以 `importlib` 载入 `$REL` 上的 `check_docs.py`，调 `open_consuming_gate_blocks`（按文件顺序配对、排除 README/预筛/围栏）与 `ledger_released_findings`（账本 `RELEASED_SCOPE_GAP`），按 `check_consuming_gate_blocks` 同式 `name[:-len(".md")]` 扣除，剩余 → 退出 4 → `consuming_gate_blocked`，其他非 0 → `consuming_gate_check_failed`；`CG_RC` 初值 99 使导出失败也不放行；(d) 全部 STOP 置 `GATE=1`，末行只在 `GATE=0` 打印 `RELEASE_GATE_OK`。`$OUT`/`$PY` 缺失路径：`gate_stop out_or_py_unset` 后续步骤仍 fail-closed（`mkdir`/`mktemp`/`$PY` 调用各自失败并 STOP）。
- 探针（一次性 `git clone --no-checkout` 于会话暂存目录；从候选操作单抽出第 1.0 节块，只把 `git fetch origin` 换成空操作、`origin/main` 换成 `$PROBE_REL`；`/bin/bash` 3.2 + `pipefail`，`$PY` = `.venv-yoloe/bin/python`，`$OUT` 指向暂存目录）：
  - `$REL` = 本候选 `b5b0d5b9…`：`last_round_line=220 last_round_candidate=4ba53335…（R3 §0）pass_line=166 passed_candidate=47f546cc…（R2）` → `STOP latest_round_not_passed`、`STOP play_governing_changed_after_pass`（PG 差异 7 路径）、`consuming_gate_open_blocks_by_file_order={}`/`ledger_released_scope_gap={}`/`consuming_gate_unreleased={}` → `CONSUMING_GATE_OK`，末行 `STOP release_gate GATE=1`。**正确**：R3 未通过、PG 已变。
  - 修前对照（R3 轮候选第 1.0 节，同一 `$REL`）：`last_round_line=` 为空却打印 `RELEASE_REF_OK`（复现 R3-3(a) 空转），无任何门状态输出（复现 R3-3(b)）。
  - 允许路径：`$REL` = R2 通过提交（`git log --grep='^P1-ENG-LOOP-002 R2@K1K2K3K4 独立复核通过'` = `92a415ef…`）→ `last_round_line=114 < pass_line=166`、`RELEASE_REF_OK`、`PG_DIFF_EMPTY_OK`、`CONSUMING_GATE_OK`、末行 `RELEASE_GATE_OK`。
  - 未 release 拒绝（真实字节）：`$REL` = `P1-ENG-ACQ-001` R2 写 block 的提交（`787b48e2…`）→ `consuming_gate_unreleased={"P1-ENG-ACQ-001.md": ["R2-1"]}`、`STOP consuming_gate_blocked`；配对后允许：`$REL` = 同项 R3 写 release 的提交（`72403109…`）→ `{}`、`CONSUMING_GATE_OK`。两历史引用上本项复核文件不存在，同时出现 `review_file_unreadable`/`no_valid_*`/`pg_diff_failed rc=128` 等 STOP 并 `GATE=1`——缺有效行时应有的 fail-closed 结果。
  - 账本 `RELEASED_SCOPE_GAP` 分支（仓库历史无真实行）：在**暂存目录的导出副本**（非仓库文件）的账本表里插入一行 `P1-ENG-ACQ-001 | R2-1 | … | RELEASED_SCOPE_GAP`，对同一导出树跑候选块中的 Python 片段 → `ledger_released_scope_gap={"P1-ENG-ACQ-001": ["R2-1"]}`、`consuming_gate_unreleased={}`、rc 0；键名 `name[:-len(".md")]` 与 `ledger_released_findings` 的 work ID 键一致，扣除式与 `check_docs.py` 同。该规则的既有回归 `tests/test_check_docs.py::test_ledger_released_scope_gap_row_counts_as_release` 本轮在副本重跑 OK。
- 已知限制（非 finding，裁定 §1 不另加判据）：第 1.0 节不核「最新 pass 的候选 == 最新 round 的候选」（通过轮按规则同时写两行同一 SHA）；round/pass 解析不排除围栏块（本项复核文件无围栏，block/release 扫描已排除）；`$CGT` 每次执行留一个只读导出目录。

### §3 Findings

**无。** 修复触及行上未发现 CLASS_1/2（第 0.6 节文本与代码/测试/裁定一致；第 4 节与第 1.0 节的失败路径逐分支 fail-closed，`pipefail`/退出码/空值边界均核）；冻结集 R3-1/R3-2/R3-3 均闭合；`RED_LINE` 无（代码零 diff，`test_loop2_isolation`/`test_loop2_freeze` 照绿）；无 `上轮漏检` CLASS_1、无 `上游漏检`；CLASS_3 无。不写 `blocks_consuming_gate`。

### §4 UNITY_NA

本候选未申请 `UNITY_NA`（交接明示「不申请」）；AC-14/15/18 与 AC-16 板端为 `NOT_RUN`。无附议对象；本轮通过只到独立复核通过，`DONE` 仍需阶段 B 的 Unity/板端证据。

### §5 限制、未验证与消耗

- 本轮未重跑停点全套（N-1 3/3 用尽；本候选代码零 diff，窄修/定点替代已在 §0 判充分）、未做归档回放、未碰板/Unity/VLM/SSH；操作单任何命令在板上的真实行为（含板端 `awk`/`ss`）未执行，仅桩探针与只读 git 探针。
- 阶段 B 运行放行**不由本轮签发**：操作单 G1–G5、第 1.0 节在真实 `origin/main` 上的放行、G4 接受核清与 G5 Air 对齐仍待各自角色；本轮写出 `passed_candidate` 只使 G1 的「复核文件写出新的 `passed_candidate`」一项成为可能。
- consumed = none（零 ID/Play/API/GPU/下载/pip/SSH/板/复制/runtime；零模型；零回放）。

### Verdict（R4@K1K2K3K4，终局）

**`PASS`**。冻结集 R3-1（文本一致性定点复看：修订 4 逐字 ↔ 操作单第 0.6 节 ↔ 具名测试 ↔ 真实 `_long_poll_result` → `_call`）、R3-2（第 4 节 `ss` 五分支桩探针修前红/修后绿）、R3-3（第 1.0 节在候选/R2 通过/ACQ block/ACQ release 四个固定引用与账本 release 分支上的只读探针修前红/修后绿）全部闭合；修复触及行无新阻断；`RED_LINE` 无。R1/R2/R3 对其余 AC 的结论随候选携带：AC-1…6、8、9、11…13、15（代码/操作单）、17 成立；AC-7（含修订 1/2/3/4）与 AC-10（含修订 1）本轮成立；AC-14/15/18 与 AC-16 板端 `NOT_RUN`。本停点返工终计 2/2，终局通过，不回用户。交接受角色消费（归因、核对表 AC-7/AC-10 更新、Overall 由接受角色裁定）；阶段 B 运行未放行、消耗性动作 0。

passed_candidate: b5b0d5b9b20b61a94885531850b2ccdaf196fd37

## R1@K1K3（2026-10-07）— 新停点 `K1K3` 身份修复候选（首轮）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-LOOP-002-R1@K1K3-20261007T214025Z-c3a6`，`requested.round = R1@K1K3`）。轨道：提案抬头逐字 `Workflow: engineering-v1`、D4 裁定生效 → 按 `docs/engineering-workflow.md` 复核；依据列 `BC-n` 读作 `AC-n`（含「R4消费与诊断故障裁定」§3–4 的 AC-7 修订 5、AC-16 修订 1、AC-10 修订 2）。本停点是接受「R4消费与诊断故障裁定」§5 新开的 `K1K3`（K1 字段来源/一致性链、K3 VLM 身份拒启），不是旧 `K1K2K3K4` 的 R5：旧终局/返工 2/2/冻结集闭合不变，本停点 C 1 次（C5）/退回 0、R 本轮为第 1 轮。零消耗：零 scenario/session/run ID、零 Unity/Play、零 VLM/API/GPU、零 SSH/板/复制/下载/pip/runtime、零真实模型/二进制、零归档回放、零全套重跑；只在一次性副本内读码/读文档、重跑 focused、做修前红/修后绿与离线 bash 3.2 探针（脚本与输出在会话暂存目录，不入仓；副本内只加了被 `.gitignore` 忽略的只读符号链接 `.venv-yoloe` 供探针 `$PY` 使用）；主树只写本文件与状态板。

### §0 候选、基线、稳定门与开轮资格

- `round_candidate: 9d95aeb817795db992d55f29991ccacdec8b5b88`（派发块指定；运行时核：`git log main --grep='^P1-ENG-LOOP-002 身份修复K1K3 收工'` 唯一命中且相等，是 `origin/main` 祖先）。代码/测试/操作单改动只在 `963fa43dc1fe295d34767fa6428c57cdea05fb6f`（`身份修复K1K3 修复候选`，相对派发登记 `0ee0c80d…1f11` 恰 5 个具名文件），其后到候选只有 `-idfix-k1k3.md` 与状态板（`git diff --stat` 核实）；候选到本轮开工 HEAD 只有 C5 证据/账本/派发日志/提案/状态板/正式设计/账本，无实现改动。
- 全量基线 = 上一通过候选 `b5b0d5b9b20b61a94885531850b2ccdaf196fd37`（R4 §Verdict `passed_candidate`，本文件最近一行）。`git diff --name-only $PASSED..$CAND` = **13 路径**，与 C5 §1 文件表逐一相同；PLAY_GOVERNING 恰 3 个：`tools/language_serve.py`（+45/−6，含 `parse_runtime_build`）、`tests/test_llama_server_adapter.py`（+118）、操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md`（+63/−5）；`controller/`、`config/`、`Assets/`、`ProjectSettings/`、`Packages/packages-lock.json` 零 diff。首轮无「上一复核轮候选」，修复触及行 = 全量 PG diff，逐行全读。
- **稳定门（workflow §4.3.1 四条件，独立核 `-idfix-k1k3.md` §2）**：① 范围/接口冻结成立——改动闭集恰为裁定 §5 五文件；`read_runtime_build` 签名、`VERSION_PATTERN`（旧式原样）、`EXPECT_ASSET_KEYS`、`llama_preflight` 比较链、六键 `model_identity`、`llama_server_command`/`_wait_llama_ready`/`SingleFlightRuntime`/`build_server`、`LlamaServerAdapter` 均零 diff（本轮读 diff 核实）；无新 AC/容差/额度/待裁定（§8 IR-K1…K6 为读法确认，C5 已确认）。② 相称测试成立——focused 本轮重跑全绿、修前红/修后绿与原块探针本轮复算（下）；**engineering §6 窄修替代全套**：相对上一个已跑全套的候选（`稳定候选` `d8d4ddc1…`，N-1 第 3/3 次）本候选只改 `--version` 原流解析与其测试/操作单文本，不触及真实模型加载器（子进程命令、就绪轮询、运行时与适配器零 diff）、数据划分或对外指标路径；N-1 全套 3/3 已用尽，实现如实写明未跑、不记全套通过。**本角色判替代充分，不要求全套、不申请新验证信封。** ③ 零 Unity，不适用。④ 解析式（§0）、AC 指针（§4）、复核范围（§7）、未验证项（§9）、状态板交接齐备。→ 不判 `REVIEW_BLOCKED`。
- 开轮资格：PLAY_GOVERNING diff 非空 → 开 `R1@K1K3`。
- 复核副本 `.claude/worktrees/review-P1-ENG-LOOP-002`（detach 于候选）；测试树哈希（`git ls-files tests | xargs cat | sha256` 前 16 位）`b2342e7550578a26`（R3/R4 `d26fbfa69b6630cc` → 本候选 `test_llama_server_adapter.py` 新增两类 7 例）。解释器：系统 `python3` 3.14.6 跑 focused（与实现者同口径）；探针 `$PY` = `.venv-yoloe/bin/python` 3.12.13（只读）；`/bin/bash` 3.2.57。
- **focused 重跑**（副本内，`YOLO_OFFLINE=true YOLO_AUTOINSTALL=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`，十模块 = R1–R3 九模块 + `test_eng_acq_guards`，输出写会话暂存目录只回显摘要）：**Ran 501 — OK（skipped=4）**，50.7 s（R3 488 + 本候选 7 例 + `test_eng_acq_guards` 6 例；skip 4 与前轮同口径环境差异）。跑后副本 `git status --porcelain` 只有被忽略的 `.venv-yoloe` 链接（`??`，未跟踪、不在树内）。
- **实现者修前红主张复算**（副本内 `git checkout $DISPATCH -- tools/language_serve.py`、保留候选测试，跑 `SemverVersionParseTests` + `SemverVersionPreflightTests` + `StartupRefusalTests` 12 例 → **FAILED (failures=3, errors=20)**：`test_missing_duplicate_conflicting_or_out_of_domain_refuse` 14 E、`test_accepted_forms_take_the_explicit_build_number` 5 E、`test_semver_bytes_with_mismatched_expected_build_refuse_before_loading` 2 F、`test_semver_bytes_with_b0_assets_serve_identity_runtime_build_b0` 1 F、`test_fake_binary_emits_the_verbatim_fixture_bytes` 1 E；与 `-idfix-k1k3.md` §3.1 逐条一致，`StartupRefusalTests` 5 例与 `test_semver_refusal_branches_on_the_production_path`/`test_timeout_or_oserror_refuse` 修前照绿亦一致）；`git checkout HEAD -- tools/language_serve.py` 恢复后同 12 例 **OK ×2**。
- **附录 X 探针原样重跑**（从候选 `-idfix-k1k3.md` 逐字抽出，sha256 `7e5fde48…5ac7` 与实现者记录相等；`python3 ops_probe.py <副本根> $DISPATCH <暂存目录>`）：加载 9 例与 §3.2 表逐格相同——修前块在 bash 3.2 下合法来源 `load_rc=0` 而九变量**全部未设**、陈旧 `WEIGHTS` 保留、解析 STOP 后仍到达下一动作（复现 OPS-SOURCE-1）；候选块合法/陈旧两例 `SOURCE_RESOLVE_OK→SOURCE_VARS_PRE_OK→SOURCE_VARS_POST_OK→SOURCE_LOAD_OK`、`source_rc=0`、值与替身逐字一致（含带空格路径），解析失败/过滤失败/加载失败/非 `shlex.quote` 行四例均 `STOP S-PRECHECK …`、`source_rc=97`、未到达下一动作且注入行未执行。gen 16/16：候选 mini 附录 B 与诊断附录 1 对 8 种原流的结论与 `parse_runtime_build` 逐例一致（`semver_verbatim`→`b0`、`legacy`→`b11381`、其余 6 种同拒；修前两条 gen 对 `conflicting` 取首行 `b11381` 与生产不一致、对原样两行 STOP——复现 DIAG-VERSION-1）。

### §1 修复触及行逐文件核对（PG 3 路径全读 diff；直接关联读 `read_runtime_build`/`llama_preflight`、`language_bridge._RUNTIME_BUILD`、mini 附录 A、诊断页全文 531 行）

| 文件 | 结论 |
|---|---|
| `tools/language_serve.py` | 新增 `SEMVER_VERSION_PATTERN`（整行 `\Z`、预发布/元数据字符集 `[0-9A-Za-z.-]`、`(build <ASCII 整数>, commit <无空白/括号/逗号非空记号>)`）、`VERSION_LINE_PREFIX`、`BUILD_NUMBER_PATTERN`（`^[0-9]{1,7}$`，与 `controller/language_bridge.py::_RUNTIME_BUILD` 的 `^b[0-9]{1,7}$` 同域）与纯函数 `parse_runtime_build`：行首 `version:` 候选行恰一条（0 条/≥2 条含逐字重复均拒，IR-K1）→ 旧式 `VERSION_PATTERN.match`（原式、仍要求整数后一空格）或语义版本 `match`（IR-K2）→ 构建号 1–7 位 ASCII 数字（`\d` 命中的非 ASCII 数字在此被拒，前导零保留原文，IR-K3）→ `b<n>`；任一不符 `StartRefused`，无缺省值。`read_runtime_build` 子进程调用（`stderr=STDOUT`、超时、非 0 退出拒启）不变，只把 `VERSION_PATTERN.search` 换为委托并前缀二进制路径；`llama_preflight` 仍在三 sha 之后、`--expect-assets` 逐键比较之前取构建号，比较不等即拒启、不起子进程。无新 import。 |
| `tests/test_llama_server_adapter.py` | 假 `llama-bin` 加 `version_sleep_s`（超时夹具），`version_text` 原样字节输出到 stderr 由 `test_fake_binary_emits_the_verbatim_fixture_bytes` 逐字节断言；`SemverVersionParseTests`（2 例 19 子例：5 接受/14 拒绝，含 `duplicate_identical`、`conflicting_forms`、`conflicting_builds`、`legacy_out_of_domain`、`non_ascii_digit`、`trailing_text`、`not_semver`）；`SemverVersionPreflightTests`（5 例：真实 `main`→`llama_preflight`→`/status` 身份 `runtime_build=b0` 并 SIGTERM 后端口释放；期望 `b11381`/`b00` 错配 → 退出 3、`runtime_build mismatch: computed 'b0'`、假服务未起、端口未开；六种拒绝分支生产路径退出 3；超时/OSError）；旧 `StartupRefusalTests` 5 例未改。fixture 由生产路径产出（真实子进程、真实回环、真实 `/status`），无手工造状态。 |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md` | 抬头修订记录追加本版并写明未经复核/未在真实板验证；O-4 段删「进程替换」并写明 bash 3.2 下 `. <(…)` 不读入变量（本轮探针复现为真）。第 0.3 节改为「来源加载块」：`src_resolve`（附录 A 退出码 0、恰 10 行、末行 `RESOLVE_OK`）、`src_load`（重核 env → `grep -v` 过滤退出码 → `src_check pre`：闭集 9 名各恰一次、非空、逐字 `shlex.quote` 形式、≤ 8,192 B → `unset` 九变量 → `set -a; . source.vars; rc=$?; set +a` 核 `.` 退出码 → `src_check post` 环境值与文件值逐字一致），每步 STOP 返回 97。第 2 节 Air 前置块以 `src_resolve && src_load; echo "source_rc=$?"` 取代旧 `tail` 目视（IR-K4）；第 3 节第 4 步把 `src_load` 移到 `chan assets` **之前**（IR-K5），附录 B 调用改 `GEN=$(…); gen_rc=$?` 并逐条列出 `S-IDENTITY`/`S-PRECHECK` 方向与两种版本格式、`runtime_version_line` 只作审计（IR-K6）。其余节（含第 1.0 节放行门、第 4 节启动块、第 13 节 STOP 表）零 diff，R4 结论携带。 |

非 PG 路径（本轮按内容/类别核）：`docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md`（只改附录 B：抬头指向操作单第 3 节第 4 步与第 0.3 节块；gen 加六个来源变量缺失即 `STOP S-PRECHECK source_vars_missing`、版本解析改为与生产同式、加 `runtime_version_line`；附录 A 零 diff，打印 9 行 `shlex.quote` + `RESOLVE_OK` = 10 行，与 `SRC_NAMES` 九名及 `src_resolve` 的「恰 10 行」一致）；`docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`（全量新文件 531 行全读：首版来自轮次 `诊断操作步骤`、从未经核对/复核；本轮只改抬头说明、§2 一条说明与附录 1 gen 版本解析，见 §2 PR-K3）；`-idfix-k1k3.md`（实现自证，全文含附录 X）；本文件 R4 节、提案「诊断冒烟授权落实」「R4消费与诊断故障裁定」（接受）、`docs/implementation-status.md` 两段与 `docs/phase1-single-drone-design.md` 两处指针（接受）、`docs/authorizations.md` 14 行（supervisor 代录的用户诊断三项选择）、`supervisor-dispatch.jsonl` 20 条（5 轮 requested/started/end_confirmed/finished）、状态板——均不含运行时代码或工作流基础设施改动。

### §2 AC 逐项、IR 确认与 C5 预复核关注项（依据列 `BC-n` 读作 AC-n；未改动文件结论随 R4 通过候选携带）

| AC | 结论 | 本轮依据 |
|---|---|---|
| AC-7（含修订 1…5） | **成立** | 修订 1…4 范围代码零 diff 携带；修订 5：两种格式各取明确 build（原样两行 → `b0`）、缺行/重复或冲突/缺 build/非法域/非 0/超时/OSError 一律拒启、三 sha 与 `runtime_build` 逐键不等仍在加载前拒启——读码 + 12 例修前红 3F+20E/修后绿 ×2 + 真实 `/status` 身份用例。IR-K1/K2/K3 读法本轮读码确认与 C5 一致。 |
| AC-16（含修订 1） | 代码/文本成立；板端 `NOT_RUN` | 两条 gen 与 `parse_runtime_build` 三处正则逐字相同（`SEMVER_VERSION_PATTERN.pattern`、`^version: (\d+) `、`^[0-9]{1,7}$` 程序化比对相等；行过滤 `startswith("version:")` 与「恰一行」同式）、16/16 结论一致；原样版本行只进 `runtime_version_line`/原流 `assets-raw.txt`，`--expect-assets` 读键 `EXPECT_ASSET_KEYS` 五键不变、`model_identity` 六键域不变（IR-K6）。`-assets-local.json` 未改。 |
| AC-10（含修订 1/2） | **成立** | 修订 1 三处（第 0.5/1.0/4 节）零 diff 携带；修订 2：三步分别核退出状态、`set +a` 不作凭据、仅成功且完整输入进入下一动作——操作块离线探针（附录 X 9 例 + 本角色加测 10 例，见下）全部 fail-closed；第 2 节/第 3 节第 4 步调用顺序与停步说明见 PR-K1。 |
| AC-6 | 成立（携带） | 六键域/逐键比较代码零 diff；新解析输出同域 `b<1–7 位>`；`test_language_latency`/`test_language_k_binding`/`test_language_bridge` 照绿。 |
| AC-9 | 成立 | `language_serve.py` 无新 import；`test_loop2_isolation`（AST 闭集）与 `IsolatedDeployEntryTests` 照绿。 |
| AC-13 | 成立 | PG 3 路径均在 §4.1 归属表；13 路径逐文件在 `-idfix-k1k3.md` §5 与 C5 §1 说明（含 `docs/` 根下的诊断页，属接受「诊断冒烟授权落实」§5 指定的诊断页，不在 §4.1 允许表但已逐文件说明）；未跑全套已如实写明、不记全套通过。 |
| AC-1/2/3/4/5/8/11/12/17 | 成立（携带） | 对应生产文件相对 `$PASSED` 零 diff；`test_loop2_freeze` 照绿。 |
| AC-14 / AC-18 | `NOT_RUN` | 阶段 B 未放行。 |
| AC-15（含修订 1） | 代码/操作单成立（携带）；板端 `NOT_RUN` | 零 diff。 |

本角色加测探针（副本内、/bin/bash 3.2、替身附录 A、脚本不入仓）：值含单引号/`$HOME`/反引号 → 逐字加载（无展开）、`SOURCE_LOAD_OK`；`RESOLVE_OK` 非末行、11 行、`$OUT` 未设 → `source_resolve` STOP；10 行但缺 `MMPROJ` 多 `OTHER`、未加引号含空格值、空值、重复键、总长 8,717 B → `source_vars_invalid` STOP（各打印具名 `bad_line`/`size`）；预先 `export` 陈旧 `MMPROJ`/`LLAMA_BIN` → 先 `unset` 后加载为来源值。BSD `wc -l` 前导空格在 `[ -eq ]` 下按整数比较（`lines=      10` 通过、`11` 拒）。

C5 预复核关注项核实：

- **PR-K1（来源块调用的停步边界）**：第 2 节 Air 前置是一个粘贴块：`src_resolve && src_load; echo "source_rc=$?"` 失败时打印 `STOP S-PRECHECK …`、`source_rc=97`，块内其后三行（`EXP_HOST` 读取、`prep-read.sh` 拼接、`bash -n`/`shasum`）仍会执行——但全是 Air 本机零消耗文本操作；SSH 单元 #1 的发起（`UNIT=1; unit_open || exit 99; chan prep-read …`）在**另一个**块，须操作员读到 `SOURCE_LOAD_OK` 后另起；与同块既有 `|| echo "STOP S-PRECHECK tool_missing/smoke_set"` 的 Air 侧约定一致。第 3 节第 4 步是单元 #2 内的散文步骤：`src_load; echo "source_rc=$?"` → 操作员核 → `mkdir -p` → `chan assets`，三条独立命令，与第 3 节步骤 1–3/5 的「→ S-PRECHECK」散文约定同型，且写明失败「按第 13 节停并 `unit_close`，不发 `chan assets`、不生成资产」。裁定 §4「失败须 STOP 停在资产生成/SSH/服务之前」在**操作员逐步执行语义**下成立；块内没有像 R3-2 那样「失败未被检测、消耗步骤自动继续」的路径。**非 finding**；已知边界：Air 侧 STOP 仍是打印 + 操作员停步，不是 `exit`（第 1.0 节 R3-3 修复亦明文「不以 exit 结束操作者 shell」）。若接受希望机械化，可把第 3 节第 4 步写成 `src_load && mkdir -p "$OUT/b0b" && chan assets …`，属合同澄清，不在本轮记债。
- **PR-K2（探针与真实来源/平台）**：生产、mini gen、诊断 gen 三处版本解析正则逐字相同（程序化比对，见 AC-16 行）、退出码/停止方向一致（gen 退出 3 对应 `S-IDENTITY`/`DIAG_FAULT`，生产 `StartRefused` → 退出 3）；真实附录 A、Air 来源原件、板端 `/usr/bin/python3` 3.12.3 与真实 `llama-server --version` 原流本轮均未执行，不把本机读数当板上通过（§5）。
- **PR-K3（诊断页全量新增）**：诊断页不在 PLAY_GOVERNING、不在任何 AC 覆盖内，属 workflow §4.3.2 诊断通道（「不进证据链；不作任何门判定」）；裁定 §5 闭集只点名其附录 1 gen。本轮全文读过并做静态核：附录 4 引用的 `ls._raise_terminate/_Terminate/_stop_child/EXIT_*/DEFAULT_T_HARD_S/SingleFlightRuntime/build_server(host,port,extra_reply_fields,access_log,budget,long_poll)/_wait_llama_ready(…, budget=)/llama_server_command` 全部存在且签名相符；§5/§6.1 的 `measure`/`k-receipt`/`run` 旗标全部存在于当前解析器；附录 3 `ss` 失败即停、`PIPESTATUS` 核端口、`pgrep` 三分；`deploy_digest --root` 存在。观察（不分级、不入 finding）：§2 的 `resolve … ; tail -n 1` 未核退出码、随后 `set -a; . assets-src.env; set +a` 是普通文件（bash 3.2 可读入），resolve 失败时 `DIAG_FAULT` 行会被当命令执行而变量未设 → 板上 check 以空路径 `DIAG_FAULT asset_missing` 失败、gen `KeyError` 无 `DIAG_ASSETS_OK`，结局 fail-closed（不起服务、不占启动编号），只是现象不整洁；该路径不在裁定闭集，用户首次诊断已在真实条件下走通 resolve 成功路径（`check.txt` 三 sha 匹配）。本轮不借本节为诊断页全步骤签通过。
- **PR-K4（证据计数）**：`-idfix-k1k3.md` §4 AC-7 行写 `SemverVersionPreflightTests`「4 例」，源码 5 个 `test_` 方法（AST 计数），§3.1 表与「12 = 2 + 5 + 5」均按 5 → **K1K3-R1-1（CLASS_3）**。
- **PR-K5（续试计时覆盖）**：诊断页 §0/1/7 与附录 0 仍写 180 min 原总量；接受「DIAG续试授权落实」已明文「本轮未改实现操作页；交本人时必须同时提供本节覆盖口径」，属接受交付义务，不是本代码候选缺陷；非 finding。

### §3 Findings

| ID | 分级 | 依据 | 阻断 | 摘要 |
|---|---|---|---|---|
| K1K3-R1-1 | CLASS_3 | `BC-7` | 否 | `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md` §4 AC-7 行的证据叙述计数「`::SemverVersionPreflightTests`（4 例）」与源码 5 个测试方法不符；不驱动任何工具或操作员动作（CLASS_3 闭集「证据叙述中的计数」） |

#### K1K3-R1-1 逐字替换补丁（由拥有该文件写权限的实现角色在下一次提交应用；不改数字以外任何内容）

- 文件 `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md` §4 表 AC-7 行：把 `` `tests/test_llama_server_adapter.py::SemverVersionPreflightTests`（4 例） `` 替换为 `` `tests/test_llama_server_adapter.py::SemverVersionPreflightTests`（5 例） ``。

其余核对未产生 finding：修复触及行上未发现 CLASS_1/2（边界：空输出、仅 `built with` 行、逐字重复、两格式冲突、缺 build/commit、行尾多余、非 ASCII 数字、8 位构建号、前导零、`\Z` 行界、超时/OSError、期望 `b00` 与 `b0` 不等；来源块：空值/重复键/多余键/未加引号/超长/`RESOLVE_OK` 位置/行数/`$OUT` 未设/陈旧导出/引号与 `$`/反引号字面化；并发：无新共享状态；真值泄漏：无新 import，`test_loop2_isolation` 照绿）；无 `RED_LINE`；无 `上轮漏检`/`上游漏检`。不写 `blocks_consuming_gate`。

### §4 UNITY_NA

本候选未申请 `UNITY_NA`（交接明示「不申请」）；AC-14/15/18 与 AC-16 板端为 `NOT_RUN`。无附议对象；本轮通过只到独立复核通过，`DONE` 仍需阶段 B 的 Unity/板端证据。

### §5 限制、未验证与消耗

- 本轮未重跑停点全套（N-1 3/3 用尽；窄修替代已在 §0 判充分）、未做归档回放、未碰板/Unity/VLM/SSH；未对真实 `llama-server` 二进制执行 `--version`——原样两行只来自用户诊断 `check.txt` 引文（裁定 §2），真实板原流若含其他行首 `version:` 行或不同空白形态，按现行语义会拒启（fail-closed），须在真实条件下如实记。
- 板端 `/usr/bin/python3` 3.12.3 上的 `parse_runtime_build`、真实附录 A 与 Air 来源原件（`FACT:2` A 尚未对齐）、板端 GNU `wc`/`grep` 行为（来源块只在 Air 运行，与本机 BSD 工具同为 POSIX 子集）均未验证；实现 §9 已如实列出。
- 诊断页除附录 1 gen 外的步骤本轮只做静态核与读码，未签其全步骤通过（PR-K3）。
- consumed = none（零 ID/Play/API/GPU/下载/pip/SSH/板/复制/runtime；零模型；零回放）。

### Verdict（R1@K1K3）

**`PASS`**。新停点 `K1K3` 首轮：AC-7 修订 5 与 AC-16 修订 1 以生产路径具名回归（修前红 3F+20E/修后绿）与三处正则逐字相同的 16/16 离线对照核实；AC-10 修订 2 以候选来源加载块在 Air `/bin/bash` 3.2 下 9 + 10 例离线探针（成功两例逐字一致、失败十七例全部 `STOP S-PRECHECK` 且不到达下一动作）核实；修复触及行无 CLASS_1/2；`RED_LINE` 无；唯一 finding K1K3-R1-1 为 CLASS_3 非阻断（补丁见 §3）。R4 对其余 AC 的结论随候选携带：AC-1…6、8、9、11…13、15（代码/操作单）、17 成立；AC-7（含修订 1…5）、AC-10（含修订 1/2）本轮成立；AC-14/15/18 与 AC-16 板端 `NOT_RUN`。本停点返工计 0/2。交接受角色消费（归因、核对表 AC-7/10/16 更新、Overall 裁定、CLASS_3 补丁转实现、「DIAG续试授权落实」前置之一已满足）；阶段 B 正式运行与诊断续试均**不由本轮放行**，消耗性动作 0。

passed_candidate: 9d95aeb817795db992d55f29991ccacdec8b5b88

## R1@OpsK1K2K3K4（2026-10-08）— 新停点 `OpsK1K2K3K4` 操作增量候选（首轮）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-LOOP-002-R1@OpsK1K2K3K4-20261008T051959Z-b97c`，`requested.round = R1@OpsK1K2K3K4`）。轨道：同上（engineering-v1，依据列 `BC-n` 读作 AC-n，含「OPS九题答复落实」「OPS验证额度落实与IR裁定」「OPS基线与IR78裁定」三节追加修订与 W1–W5 / O1–O4 / IR-OPS-1…8）。零消耗：零 SSH/板/Unity/Play、零模型、零归档回放、零全套重跑、零 SUB:1/2/3 动用；只在一次性副本内读码、重跑 focused、跑三组零模型探针；主树只写本文件与状态板。

### §0 候选、基线、稳定门与开轮资格

- `round_candidate: c8e8b3c52abfcbb3de9ff42c5753fc3f89357b73`（派发块指定 = 上一实现派发 `OPSC6返工` 的证据/交接提交；运行时核：是 `origin/main` 祖先）。代码候选 `d3c3ff03d8c73a9f0adb40cb5c6546f9ad1a89db`（交接 §7.0 首项；`git diff --stat d3c3ff0 c8e8b3c` 只有 `docs/current-status.md`、`-OpsK1K2K3K4-handoff.md` 与两份 `-ops-c6rework-*.log`，实现文件零 diff）。本轮 PG 结论对两者同值。
- 全量基线 = 上一通过候选 `9d95aeb817795db992d55f29991ccacdec8b5b88`（R1@K1K3 `passed_candidate`，本文件最近一行；是候选祖先）。`git diff --name-only 9d95aeb..c8e8b3c` = **32 路径**（C7 §1 表 30 路径 + 其后的 C7 证据与派发日志增量），PLAY_GOVERNING + 三份操作单恰 **10 路径**，与 C7 §1 列表逐一相同；另旁读 `.gitignore`（+2）与 `runtime/README.md`（+26）。`controller/`、`config/`、`Assets/`、`ProjectSettings/`、`Packages/packages-lock.json`、`tools/language_serve.py`、`tools/language_latency.py`、`tools/eng_loop2/{__init__,llama_adapter,deploy_digest,analyze_play}.py`、`tools/eng_jet/` 零 diff（副本内 `git diff --stat` 核实）。
- 开轮资格：PLAY_GOVERNING diff 非空（三工具 4,843 行新增、四测试 3,295 行新增、三操作单 +113/−20）→ 开 `R1@OpsK1K2K3K4`。新停点首轮，无上一复核轮候选；修复触及行 = 全量 PG diff，逐行全读。旧 `K1K2K3K4` R4 终局与 `K1K3` R1 通过范围携带，不回溯、不套用到新工具。
- 稳定门四条件（交接 §7.0 自证，独立核）：①范围/接口冻结——写入只在「OPS九题答复落实」§3 闭集 + IR-OPS-8 具名 `.gitignore` 一行内（上列禁改路径零 diff），成立；②相称测试——`b6bd195` 停点全套一次（`-ops-c6rework-tests.log`：2450 例，4 failure/13 error/54 skipped，对比 `-ops-tests.log` 的新增失败集恰 1 项 = `FormalFailurePathTests.test_backend_fatal_terminal_keeps_accepted_request_and_reason`，副本内 `comm` 复算一致）+ `d3c3ff0` 窄修 focused/红绿（`-ops-c6rework-focused.log` 末段 133 OK、修前红 3/3）——本轮 focused 重跑一致，engineering §6 替代适用性见 §5，条件成立；③无已知 Unity 失败，AC-11 修订 1 人眼义务见 §4，成立；④复核入口/状态板/候选/未核风险齐，成立。C7 §2 的 C6-2/C6-3「不满足」是实现忠实性主张，不是自证条件不成立 → 不判 `REVIEW_BLOCKED`，开轮并在 §3 给结论。
- 复核副本 `.claude/worktrees/review-P1-ENG-LOOP-002`（detach 于 `c8e8b3c`）；测试树哈希（`git ls-files tests | xargs cat | sha256` 前 16 位）`c49f25f06d3df348`。focused 重跑（系统 `python3`，与实现者同口径）：`python3 -m unittest tests.test_eng_loop2_play_ops tests.test_eng_loop2_operator_web tests.test_eng_loop2_summarize_ops tests.test_loop2_isolation` → **Ran 133 tests in 167.349s, OK**（输出在会话暂存目录，只回显摘要）。

### §1 逐文件核对（10 PG 路径 + 2 旁读全读；直接关联读 `controller/language_loop.py` 的 `RESULTS_FILE/SESSION_JOURNAL/T_CONF_S/KReceipt` 导出、`language_bridge.read_tracker_state/read_result/parse_instruction/LLAMA_IDENTITY_KEYS`、`analyze_play.main` 的 `score`/`derive-bc` 退出码、`tools/check_docs.py` 的两函数签名）

| 路径 | 核对摘要 |
|---|---|
| `tools/eng_loop2/play_ops.py`（新，3,240 行） | 阶段入口 `plan/gate/source/prep/receipt/play` + `--mode diagnostic diag`；`release_gate` 与 R4 已核的操作单 1.0–1.5 同判据（MR 正则、PG 定义漂移核、`check_docs.py` 两函数导出核消耗性门、账本命中、HEAD=PASSED、整树干净、`_Recovery`、三操作单 sha、`$DOCWT` 自检）；`require_g4`/`DIAG_RELEASE_LINE` 行首锚定 + 值绑定（IR-OPS-1/7）；`SshUnit` 通道闭集/顺序/`-O check`/失效不回退；`ServeSession.startup_lines` 与操作单第 4 节逐行同文（`PS1=; PS2=; set -o pipefail; set +o emacs +o vi; stty -echo` 为 OPS 增量注明）；`PlanScheduler` 的 O2/IR-OPS-6 锚点规则成立（`_anchor` 只取 receipt `at_unix_s`、`_bind_tracking` 只认同纪元 journal `state=TRACKING`、`ANCHOR_WAIT_S` 后 UNKNOWN 停依赖、`_seeded_selection` 排除拒绝/带拒收细节）；`halt`/`_block`/`Submitter.seal` 同锁不可逆封住（C6-1 成立）；`run_attempt`/`attempt_closeout` 任一主路径异常先收尾再抛、每步 try（C6-2 主路径成立，收尾内部失败见 R1-3）；`archive_attempt` 只 `rename`、不读内容、目标已存在即 `S-ARCHIVE`；`classify_terminal` 按 O3/IR-OPS-3；诊断模式独立根/粗账/两连接/一次启动/四类 STOP/`DIAG_FAULT` 分流与 §4.1–4.8 逐条对应。**缺陷**：R1-1（TERMINAL 路径改写已受理步骤）、R1-2（确认在途竞态）、R1-3（收尾内部失败不传播）、R1-4（评分次数无守账）；R1-5 为 SCOPE_GAP。 |
| `tools/eng_loop2/operator_web.py`（新，1,261 行） | W1 按钮闭集 `BUTTONS`/`CLI_ACTIONS`、只监听 `127.0.0.1`、内嵌页面无外部资源；W2 `preview_identity` 文件名=`<frame_id>-<query_id>.png`、目录限 `previews/`、字节 sha + IHDR 尺寸、`first_seen` 两次读出不一致永久不可确认、确认前服务端重读字节；W3 两截止取早者、帧差门、`stale`/回退/时钟漂移均不可确认、`public()` 不续期；W4 `in_flight` 全局互斥、`used_bindings` 一次提交、`stop_sent` 每会话一次、`interpret` 把超时/5/4/2/其它退出码记 UNKNOWN、`resolve_late` 只核清不恢复；W5 `ops-web.jsonl` 逐条、nonce/Host/Origin 核、`/preview/` 与 `/frame/latest.jpg` 绑定读；`Submitter.submit` 的 `on_reply` 在释放在途锁前记录（C6-3 竞态窄修成立，例外见 R1-5）；`App.action` 在 stop 分支之后、业务之前核封住（C6-1 成立）。保真页 `FidelityHandler/load_fidelity_samples` 只读、按序号+sha 服务。呈现路径与登记版本逐字相同（§4）。 |
| `tools/eng_loop2/summarize_ops.py`（新，342 行） | 独立进程；`plan_vs_actual` 跳过不成样本、`HALTED` 仍是样本、`MISSING_RECORD`/`NO_PLAY_RECORD` 与 `NOT_EXECUTED` 分列（C6-3 摘要侧成立）；`objective_events` 初始 LOST 不代证、状态名不证明跟对；`consistency()` 核跳过带 rid、submit_begin/动作/回执/第二写者/确认无显示记录；`run_score` 每归档一次原 CLI、输出存在不重跑、只 `cite_score` 不重算；诊断模式不评分。**缺陷**：`main` 在 `run_score` rc≠0 时仍返回 0（R1-3 第二项）；无评分次数守账（R1-4）；`consistency()` 不报「`NOT_EXECUTED` 带 request_id」（随 R1-1 闭合）。 |
| `tests/test_eng_loop2_play_ops.py`（新，2,251 行） | 临时 git 仓库 + 假 `ssh`/`curl`/Python 替身（只拦截 measure/k-receipt/derive-bc/score/run）+ 生产桥函数写回执/状态的替身会话；覆盖放行门 9 例、精确忽略 3 例、来源/SSH/服务/收据/身份/计划、调度器 9 例、`HaltTests` 4 例（含确定性竞态回归）、锚点 6 例、归档/STOP/模式、诊断粗账、端到端 prep/receipt/play、`FormalFailurePathTests` 6 例（S-LOAD/backend_fatal/挂起/仍出帧/Ctrl-C/部分收尾失败）、`DiagTests` 11 例（含 STOP1/Ctrl-C 封住）。声明的 C6-1/2/3 用例确实走生产入口；**未覆盖**：候选呈现中/结果未知时的会话 TERMINAL（R1-1）、确认在途时状态先变（R1-2）、收尾内部 Ctrl-C/OSError 与评分非零 rc（R1-3）、评分次数（R1-4）。 |
| `tests/test_eng_loop2_operator_web.py`（新，678 行） | 合法动作表、按钮闭集、生产解析器接受 argv、W2 绑定 9 例（显示门、旧视图/新纪元/错结果、字节变化永久禁确认、损坏/越界/Δ 挂起/跨文件不一致）、W3 截止 4 例、W4 提交 7 例（双标签页恰一次、UNKNOWN 与迟到回执、WRITER_BUSY、stop 一次、绑定一次、跳过、TERMINAL/backend_fatal、封住后只剩一次 stop）、反馈、HTTP（回环、无外部资源、nonce/Host/Origin、路径绑定）、保真页、真实 CLI 往返。与声明一致。 |
| `tests/test_eng_loop2_summarize_ops.py`（新，261 行） | 计划—实际/分母 4 例（含 MISSING_RECORD、HALTED）、客观事件 2 例、一致性 4 例、评分 2 例（正式恰一次且只引用、第二次拒绝覆盖、无归档/诊断不评分）。与声明一致；未断言 `main` 在评分 rc≠0 时的退出码（R1-3）。 |
| `tests/test_loop2_isolation.py`（+105，只追加） | AST：两在线文件不导入真值/评分/几何/摘要、无 `CoverageEvaluator`；`operator_web` 无真值/评分/几何字符串；真值文件只在 `archive_attempt` 出现且无读调用；`analyze_play` 只在 `freeze_plan`、`summarize_ops` 只在 `stage_play`/`run_offline_summary`；`PlanScheduler` 无评分/几何字符串；冻结计划键闭集；诊断摘要在 `closeout` 之后且不评分；摘要只经子进程用原评分器。既有断言未改（diff 只追加）。AC-9 修订 1 成立。 |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md`（+48/−9） | 页首执行人改「本人 Unity Play/停止 + 网页发送/跳过/确认/拒绝/停止会话/反馈」与「代理/脚本持有可见前台 SSH」；§0.3/§1/§2/§3/§4/§6/§7/§8/§9/§10/§11/§12/§13 各加「OPS 增量」段，与 `play_ops` 行为逐条对照一致（1.2 精确忽略口径、工具截止 = 等待 Play 起点 + 420 s、O2/IR-OPS-6 锚点、IR-OPS-4 无重试、O3/C6 封住与收尾顺序）；第 4 节明示「该前台监督未在真实板上运行验证」。**§12 新句「对每个归档恰调用一次…（计入实现自证 ≤ 2 次）」与 3 剧本 3 次评分自相矛盾**（R1-4）。附录 P 正文未改（只加提取说明）。 |
| `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`（+59/−11） | 页首「四次已结束、旧许可耗尽、唯一入口 SUB:3」；新「现行 SUB:3」节：执行前提（含 `sub3_release` 机读行读法）、唯一命令、8 步表与 §4.1–4.8 逐条对应、本人动作闭集、STOP/故障分流、原件边界；6.2/附录 6 标停用；附录 3 改只许编号 1、载入失败/缺输入拒启；附录 4 五项输入缺项拒启（与 K1K3 诊断页修复一致）。与 `DiagnosticRun` 行为一致。 |
| `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md`（+6） | 只加入口引用与「诊断模式不使用附录 A/B」说明、附录 A/B 提取标题前缀说明；附录 A/B 正文未改。 |
| `.gitignore`（+2） | 仅注释 + `/outputs/eng-loop2/`（IR-OPS-8 具名一行），`FormalOutputIgnoreTests` 三例核实。 |
| `runtime/README.md`（+26） | 新入口、网页只读范围、归档只改名、诊断 hold/归位说明；与代码一致，无运行时产物改动。 |

其余 20 个 `docs/` 路径（提案三节 OPS 合同与最新核对表、C5/C6/C7 证据、交接 §1–§11、五份测试日志摘要行与新增失败集、ops-progress/validation-plan、实现状态、正式设计 v 条目、账本 11 条代录标题、Unity 日志 SUB2 条目、派发日志）按 §0 全量 diff 读取或核摘要行；历史文档不取得新通过效力，本轮未改任何一份。

### §2 AC 逐项（依据列 `BC-n` 读作 AC-n；未改动文件结论随 R1@K1K3 通过候选携带）

| AC | 本轮结论 | 依据 |
|---|---|---|
| AC-1/2/3/4/6/7/12/17 | 成立（携带） | 对应运行时文件零 diff；`test_loop2_freeze`/`test_loop2_isolation` 既有断言照绿。 |
| AC-5 修订 1 | 成立 | 网页只经原 CLI（`CliRunner.argv` 闭集、`RealCliTests` 真实解析器）；Δ/intent/帧摘要与检查点不改；W3 不续期；到期只禁确认。 |
| AC-8 修订 3 | **不成立** | R1-1：会话 TERMINAL 时呈现中/结果未知的已受理步骤被改写为 `NOT_EXECUTED`（事后删样本）；R1-2：受理的 confirm 被记为 `NO_DECISION` 并丢失。 |
| AC-9 修订 1 | 成立 | §1 隔离测试；在线工具只读实时画面/会话原流/冻结计划；评分只在收尾独立进程。 |
| AC-10 修订 1…5 | **不成立** | R1-3（收尾内部失败与评分失败不非零退出、不停依赖）、R1-4（评分次数无守账）；其余 O1/O3/W/IR-OPS-1…8 与 §3 闭集成立；C6-1 成立。 |
| AC-11 修订 1 | 成立 | 呈现路径逐字不变（§4），本人两张一致记录可复用；H-1…12 零 diff。 |
| AC-13 修订 1 | 成立（限已测代码） | 完整 diff 逐文件在闭集内；全套与 focused/红绿指针可复算；窄修替代见 §5。 |
| AC-14 修订 1/2 | **不成立**（代码侧） | R1-3：本人 Ctrl-C 于收尾等待被吞、下一剧本照常开始；与「不自动重试/失败停依赖」相悖。正式证据仍 `NOT_RUN`。 |
| AC-15 修订 2、AC-16 修订 2/3 | 代码侧成立；证据 `NOT_RUN` | measure 非 0 不跑 k-receipt、首失败分流、6/8 → `S-RECEIPT`；来源/gen/版本/身份拒启替身齐；真实板未验证。 |
| AC-18 修订 1 | 证据 `NOT_RUN`；摘要一致性检查有缺口 | `consistency()` 不报 `NOT_EXECUTED` 带 request_id（随 R1-1 闭合）；正式归档与复核重放后置。 |

### §3 Findings

| 编号 | 分级 | 依据列 | 范围判据（可达？） | 内容 |
|---|---|---|---|---|
| R1-1 | CLASS_2 | `BC-8` | 可达：AC-8 D4 夹具点名 `INTERRUPTED(presentation_pending, operator_stop)`/`duration_reached`；本人在候选呈现期间点「停止会话」即触发 | `PlanScheduler._not_executed_rest`（`play_ops.py` 1245–1253，由 `tick` 1309–1312 在会话 `TERMINAL` 时调用）只把 `SENT`/`OBSERVING` 记为 `NO_CANDIDATE`/`DONE`，其余一律 `NOT_EXECUTED`：**`AWAIT_DECISION`（请求已受理、候选已呈现）与 `UNKNOWN`（W4 结果未知）的当前步被改写为 `NOT_EXECUTED`**，与同一候选 `halt()`（1084–1092）对同类步骤记 `HALTED`/保留 `UNKNOWN` 不一致。后果：`summarize_ops.plan_vs_actual` 该行 `is_sample=False`、`designate_not_executed+1` 而 `designate_sent+1`（request_id 仍在），`consistency()`（150–184）不报。副本探针：呈现中 `TERMINAL(operator_stop)` → `NOT_EXECUTED`（request_id 保留）；`UNKNOWN` + `TERMINAL(duration_reached)` → `NOT_EXECUTED`。违反 AC-8 修订 3「已受理命令…不得事后删样本」与 C6-3 完成条件。修复方向：TERMINAL 路径对 `AWAIT_DECISION`/有 request_id/`UNKNOWN` 的步骤与 `halt` 同口径（`HALTED` 或保留 `UNKNOWN`，reason 带 `session_terminal:<reason>`）；`consistency()` 增加「`NOT_EXECUTED` 带 request_id」告警。闭合：具名回归（生产 `PlanScheduler` + 真实 `Monitor`/桥写函数夹具）两例修前红/修后绿，且 `summarize_ops` 回归断言该行 `is_sample=True`。 |
| R1-2 | CLASS_2 | `BC-10` | 可达：正常确认路径即触发——网页 confirm 在途（CLI 等回执 ≤ 5 s）期间会话受理并写 `TRACKING`，runner 每 0.1 s tick | `_await_decision`（1342–1346）在状态离开 `AWAITING_CONFIRMATION` 或 `result_id` 变化时立即 `NO_DECISION`，**不检查 `submitter.in_flight.locked()`**（同函数截止分支 1350 却检查了）；其后 `record_decision`（1200–1202）因 `phase != await_decision` 静默返回，连 `decisions` 也不记。副本探针：持有 `in_flight` 模拟在途 confirm、会话写出 receipt(APPLIED)+`TRACKING` 后 tick → 该步 `NO_DECISION`「无已受理的选择」；释放后 `record_decision(APPLIED)` → 仍 `NO_DECISION`、`decision=None`、`decisions=None`、index 已推进。后果：受理的 confirm 从计划记录消失，O2 的观察 ≥ 15 s / 红车跟随 ≥ 20 s / P3 `release` 都不发生，`consistency()` 不报（confirm rid 在 `submits` 中）。违反 AC-10 修订 3（O2「仅 confirm/reject 受理后观察」、W4「迟到回执只按原 id 核清」但须记录）与 AC-8 修订 3。修复方向：状态变化分支在 `in_flight` 持有时等待下一个 tick；`record_decision` 对已关闭的步骤按 `_late_reply` 口径记录受理事实，APPLIED 时恢复该步到 `OBSERVING`（锚点仍只取 receipt 写盘时刻）。闭合：回归用 CLI 替身延时 + 会话先写 receipt/`TRACKING`，断言该步记录 `decision`/`decision_request_id`、不为 `NO_DECISION`、观察窗按 receipt 锚点开启；修前红/修后绿。 |
| R1-3 | CLASS_2 | `BC-10` | 可达：STOP:9/AC-14 修订 2 点名本人 Ctrl-C；`--out` 可配置，`rename` 跨设备/权限 OSError 为生产入口可达的环境失败；`analyze_play score` 非 0 退出为既有生产路径 | (a) `attempt_closeout.failed()`（1937–1941）只把 `Stop` 追加进 `found`，`KeyboardInterrupt`/其它异常只写 `closeout[name]` 文本。收尾第 3 步等本人停 Play 时 Ctrl-C → `unity=interrupted`，第 4 步归档跳过（文本「UNKNOWN，交接受」但无 Stop）、第 5 步无 Stop → `found` 空 → `run_attempt`（1918–1920）正常返回 → `stage_play`（2097–2101）开始下一剧本：本人中止被吞、帧环未归档留在 `runtime/`、下一次 Play 与上一次产物混在同一帧环。(b) `archive_attempt` 的 `rename` 抛 OSError → `closeout["archive"]="OSError…"`、`record["archive"]=None`，同样继续。副本探针 P3(a)(b)：`found=[]`。(c) `stage_play` 2141–2153：`summarize_ops` 非零 rc 只记 `closeout["summary"]="rc=N"` 不置 failure；`summarize_ops.main`（319–338）在 `run_score` rc≠0（210–221）时仍返回 0 → 评分失败、摘要缺四表时 `play` 退出 0、打印正常收尾（测试 `assert_closeout_complete` 断言 `summary=="rc=0"`，生产不强制）。违反 AC-10 修订 3「失败保留原流/rc/原因/实账并非零退出，仅做已签安全收尾」、O3、C6-2 完成条件「无法证明…记 UNKNOWN、停依赖」与 AC-14 修订 2。修复方向：收尾内非 Stop 异常与 Ctrl-C 一律转为 `found` 中的 UNKNOWN（`describe_failure` 已有形态）；归档被跳过/未证明（UNKNOWN）时 `found` 必追加；`summarize_ops` 评分 rc≠0 自身非零退出，`stage_play` 对摘要/评分非零 rc 置 failure。闭合：三条具名回归（Ctrl-C 注入收尾等待、归档 OSError 替身、score 替身非零）→ `play` rc 3、不开下一剧本、`record.stop` 非空；修前红/修后绿。 |
| R1-4 | CLASS_2（附合同争议，交接受复判） | `BC-10` | 可达：正式 3 剧本正常完成即触发 | 已签 B-main「正式归档零模型回放：实现 ≤ 2 次、独立复核 ≤ 1 次」（提案「Mac mini四题答复落实」§2 表、§5.2），`summarize_ops.summarize`（274–277）对每个有归档的尝试各调用一次 `analyze_play score`，正式 3 剧本 → 3 次；正式 `Ledger.LIMITS`（93–98）无回放/评分维度，`run_score` 只按输出存在去重，**评分前无守账、越界不停**（O1/§0.4「每次消耗性动作之前检查」、O4「扣原实现回放次数」）。操作单 §12 新句「对每个归档恰调用一次…（计入实现自证 ≤ 2 次）」自相矛盾。争议交接受：≤ 2 的语义（总次数 vs 每归档）及是否须先改合同/信封；无论裁定，工具须在每次评分前守账、越界即停并照记（`S-ENVELOPE` 或等价），不得静默超额。闭合：Ledger/摘要侧守账 + 回归（第 N+1 次评分前拒并记录；N 按裁定）；修前红/修后绿。 |
| R1-5 | CLASS_2 | `SCOPE_GAP`（非阻断，路由接受角色） | 不可达：触发需 `OpsLog` 写失败或 CLI 子进程在 30 s kill 后仍 > 35 s 不返回，均非提案/AC 点名、不能由归档工件产生 | `Submitter.submit` 的 `on_reply` 异常只记 `record_reply_failed`（`operator_web.py` 650–655），计划不记录该已受理请求；`attempt_closeout`（1962–1963）与 `_record_play`（2926）`in_flight.acquire(timeout=35)` 失败后仍读快照并 `halt`，在途步骤会被记 `NOT_EXECUTED`（`in_flight_quiesced=False` 虽入记录但不转 UNKNOWN、不停依赖）。建议记「范围外已知缺陷」或后续修订：quiesce 失败 → 该步 `UNKNOWN` + 停依赖；`on_reply` 失败 → 该步 `UNKNOWN`。 |

其余核对未产生 finding：PR-O1（`sub3_release` 全文匹配）——`DIAG_RELEASE_LINE`/`G4_RELEASE_LINE` 行首锚定（可带列表记号/反引号）、值须逐字等于门核得到的最新有效 `passed_candidate`，合同格式示例（非 40 位 hex）不命中（`DiagTests.test_contract_format_examples_are_not_release_lines`），IR-OPS-7 裁定以值绑定为判据、未设节定位判据，残余风险只来自接受角色自己写的行 → 不构成 finding；PR-O2（真实板前台监督）见 §5；保守截止（等待 Play 起点 + 420 s）与 C6-2 裁定「Play 前等待不能扩成 540 s」一致，fail-closed，非 finding；`Stop.stop_all` 从未被读取、`record["first_frame_seen_unix_s"]` 在未出帧时也被置值（只影响 Unity 未进 Play 的失败路径记录）——观察，非 finding；`RED_LINE` 无（在线工具无真值/评分/几何导入，`test_loop2_isolation` 照绿；呈现路径不重绘换框）；无 `上轮漏检`/`上游漏检`（新停点首轮）；CLASS_3 无。不写 `blocks_consuming_gate`（四条阻断均在本轮候选新增行上，非未改动行 `上轮漏检`；状态板无 `Consuming=yes` 活跃行）。

### §4 UNITY_NA 与人眼保真

- 候选未对任何 AC 申请 `UNITY_NA`：AC-14/15/18 与 AC-16 板端按交接 `NOT_RUN`，本轮无可附议项，也不签发任何 `UNITY_NA`。
- AC-11 修订 1 / SUB:2（C7 §3 判读）独立核：用户日志 `UT-P1-ENG-LOOP-002-OPS-SUB2` 登记呈现 HEAD `0c1eb68`、blob `3ecd796…`；候选 blob `13db5f1…`。副本内以 AST 定位源码片段逐字比较：`PAGE`、`FIDELITY_PAGE`、`FidelityHandler`、`load_fidelity_samples`、`build_fidelity_server`、`Monitor._presentation/preview_identity/_read_frames/_read_result`、`App.preview_bytes/frame_bytes/displayed_preview`、`Handler`、`png_dimensions`、`PREVIEW_NAME`、`FRAME_NAME` **全部相同**；变化只在 `Submitter`（seal/claim/submit/on_reply）与 `App.action/_send_or_skip/_decide/_stop`。附议 C7：本人两张一致记录可携带到本候选呈现路径，无须重看；提示行/用时仍 UNKNOWN，不代判模型/Unity/正式指标。

### §5 限制、未验证与消耗

- engineering §6 替代（C7 §4(b)）：`d3c3ff0` 相对已跑全套的 `b6bd195` 只改 `operator_web.py`/`play_ops.py` 收尾与一份测试，不触真实模型加载器、数据划分或 `analyze_play` 指标算法；focused 133 + 确定性红绿本轮复算一致 → 对该窄修**替代适用且充分**，但不记 `d3c3ff0` 全套通过。**对返工候选：本角色要求跑停点全套一次**（SUB:1 余第 3 真候选 1 次）——理由：R1-1…R1-4 的修复落在调度器/收尾/摘要路径，本停点唯一真实竞态正是在全套负载下才暴露，而 `d3c3ff0` 本身未跑全套；若实现/接受认为应保留该次额度，须在交接写明并回接受裁定，R2 届时按 §6 重判。
- 真实板/Unity 未验证（PR-O2 原样保留）：前台 `ssh -tt` 交互 bash、`stty -echo`、Ctrl-C 经 pty 送达、同会话端口/进程释放核、真实会话对 stop 的时延、Unity 真实出帧/停止均只有本地替身；本轮不签任何板端或 Play 结论。
- 消耗：零 SUB:1/2/3、零 SSH/板/Unity/Play/模型/回放/API/正式 ID；副本内 focused 一次 + 三组零模型探针（输出在会话暂存目录，不入仓）。
- 边界自查：本会话未修改任何实现文件；主树只写本文件与 `docs/current-status.md`。

### Verdict（R1@OpsK1K2K3K4）

**`REWORK_REQUIRED`**（本停点第 1 次，1/2）。阻断：R1-1（CLASS_2，`BC-8`）、R1-2（CLASS_2，`BC-10`）、R1-3（CLASS_2，`BC-10`）、R1-4（CLASS_2，`BC-10`，附合同争议交接受复判 ≤ 2 次语义）；R1-5（CLASS_2，`SCOPE_GAP`）非阻断，路由接受角色记债或裁定。修复直接回本角色 `R2@OpsK1K2K3K4`，不经核对轮；是否开 `R2` 按 workflow §4.4 开轮资格（PLAY_GOVERNING diff 非空；`play_ops.py`/`summarize_ops.py` 与对应测试必非空）决定。不写 `passed_candidate`。AC-1…7、9、11、12、13、15/16（代码侧）、17 本轮成立的结论随候选携带，下一轮按增量规则只在修复触及行上找新阻断。SUB:3 放行、正式 G1–G5/B-main 运行不由本轮签发；Overall `REVIEW_PASSED` 仍只指旧范围。

## R2@OpsK1K2K3K4（2026-10-08）— 返工候选（R1-1…R1-4 闭合核实；增量轮）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-LOOP-002-R2@OpsK1K2K3K4-20261008T062040Z-33ba`，`requested.round = R2@OpsK1K2K3K4`）。轨道：同 R1（engineering-v1，依据列 `BC-n` 读作 AC-n）。零消耗：零 SSH/板/Unity/Play、零模型、零归档回放、零全套重跑、零 SUB:1/2/3 动用；只在一次性副本内读码、重跑 focused 一次、红绿一次；主树只写本文件与状态板。

### §0 候选、基线、稳定门与开轮资格

- `round_candidate: e24e13f020cdec9163d01ffc71d7e52ecc587f8a`（派发块指定 = `OPSR1返工` 的证据/交接提交；运行时核：是 `origin/main` 祖先；上一复核轮候选 `c8e8b3c…` 与上一通过候选 `9d95aeb…` 均为其祖先）。代码候选 `5218cc2`（交接 §12 首项）：`git diff --stat 5218cc2..e24e13f -- tools tests` 为空，实现文件零 diff，本轮 PG 结论对两者同值。
- **修复触及行** = `git diff c8e8b3c..e24e13f`（上一复核轮 §0 `round_candidate` 派生）于 PLAY_GOVERNING + 操作单：恰 **5 路径**（+375/−13）——`tools/eng_loop2/play_ops.py`（84 行变更）、`tools/eng_loop2/summarize_ops.py`（49）、`tests/test_eng_loop2_play_ops.py`（181）、`tests/test_eng_loop2_summarize_ops.py`（72）、`docs/evidence/P1-ENG-LOOP-002-play-ops.md`（§12 一句）。与 `git diff e9610e1..e24e13f` 同路径集逐字相同（R1 verdict 提交到候选之间无隐藏实现改动）。`operator_web.py`、`tests/test_eng_loop2_operator_web.py`、`tests/test_loop2_isolation.py`、诊断页、mini-prep、`.gitignore`、`runtime/`、`controller/`、`config/`、`Assets/`、`ProjectSettings/`、`Packages/packages-lock.json`、`tools/eng_loop2/analyze_play.py` 自 `c8e8b3c` 起零 diff（副本内 `git diff --stat` 核实），交接 §12 第 2 条范围主张成立。
- **全量 diff** = 相对上一通过候选 `9d95aeb`：`git diff --name-only` = **35 路径**（R1 §0 的 32 + 本轮 `-ops-r1rework-{focused,tests}.log` 与 `-C7-OpsK1K2K3K4.md`），PG + 三操作单仍恰 10 路径，与 R1 §0 相同；只用于核实声明范围与红绿，不作本轮阻断范围。
- 开轮资格：PG diff 非空 → 开 `R2@OpsK1K2K3K4`（本停点第 2 轮；返工计数 1/2）。增量轮：新阻断只来自修复触及行上的 CLASS_1/2、旧 finding 闭合失败、`RED_LINE`、未改动行上 `上轮漏检` CLASS_1。
- 稳定门：R1 §5 要求返工候选跑停点全套一次——已满足：`docs/evidence/P1-ENG-LOOP-002-ops-r1rework-tests.log` `Ran 2462 tests`、`FAILED (failures=3, errors=13, skipped=54)`（2451 + 新增 11）；本角色以 `grep -E '^(FAIL|ERROR):' | sort | comm` 与上一全套 `-ops-c6rework-tests.log`（2450，4F/13E）逐名对照：**只在新日志 0 项**，只在旧日志 1 项 = `FormalFailurePathTests.test_backend_fatal_terminal_keeps_accepted_request_and_reason`（`d3c3ff0` 窄修首次在全套负载下通过），其余 16 项逐名相同 = 已接受环境/既有基线 → 本轮新增失败 0，交接 §12.3 主张成立。候选未申请 `UNITY_NA`。四条件（范围闭集 / 相称测试 / 无已知 Unity 失败 / 复核入口齐）成立。
- 复核副本 `.claude/worktrees/review-P1-ENG-LOOP-002`（detach 于 `e24e13f`）；测试树哈希（`git ls-files tests | xargs cat | sha256` 前 16 位）`7abfb727001a77fa`（R1 为 `c49f25f06d3df348`，差异 = 两份测试文件的新增用例）。focused 重跑（系统 `python3`，与实现者同口径）：`python3 -m unittest tests.test_eng_loop2_play_ops tests.test_eng_loop2_operator_web tests.test_eng_loop2_summarize_ops tests.test_loop2_isolation` → **Ran 144 tests in 182.374s, OK**（输出在会话暂存目录，只回显摘要）。
- **修前红/修后绿**（副本内；`git checkout 2fdf2ec -- tools/eng_loop2/play_ops.py tools/eng_loop2/summarize_ops.py` 把工具代码退到派发基线、测试保持候选版本 → 跑 11 例具名回归 → 恢复候选 → 再跑）：修前 `Ran 11 tests … FAILED (failures=10, errors=1)`，失败全部来自行为——`('NOT_EXECUTED', rid) != ('HALTED', rid)`、`('NOT_EXECUTED', rid) != ('UNKNOWN', rid)`、`('NO_DECISION', None, None) != ('OBSERVING', 'confirm', rid)`、`'NO_DECISION' == 'NO_DECISION'`（在途时被关闭）、`KeyError: 'decisions'`（迟到选择连记录都没有）、`0 != 3`×2 与 `'STOP UNKNOWN' not found`×2（Ctrl-C/OSError/评分 rc 4 后 `play` rc 0、下一剧本照常开始）、`0 == 0`（摘要评分失败仍 rc 0）、`False is not true : []`（无一致性告警）、评分 3 次 ≠ 2 次；无一例因缺属性失败（`getattr` 兼容成立）。修后同 11 例 **OK**（19.5 s）。恢复后副本 `git status --porcelain` 为空。

### §1 修复触及行逐处核对（5 路径全读 diff；直接关联读 `PlanScheduler.halt/_late_reply/record_decision/_close/_block/tick/_await_result/_observe/_send_stop`、`Submitter.submit`（在途锁 `threading.Lock`、`on_reply` 在释放前）、`App._decide`、`run_attempt`、`stage_play` 全文、`analyze_play.main` 的 `score` 分支、`summarize_ops.plan_vs_actual/consistency`、测试 `SchedulerBase`/`Fixture`/`FakeCli`/`FormalFailurePathTests` 基类）

| Finding | 修复落点核对 | 闭合四条件（workflow §4.4） | 结论 |
|---|---|---|---|
| R1-1（`BC-8`） | `_not_executed_rest`（1292–1310）：`SENT/OBSERVING` 原结局不变；`UNKNOWN` → `_close(…, "UNKNOWN", reason 追加 "session_terminal:<reason>（结果仍未知）", closed_by)`；`AWAIT_DECISION` 或带 `request_id` → `HALTED`（request_id/回执/`decisions` 保留，reason 含 `session_terminal:<reason>`）；仅无 request_id 的 `AWAIT_SEND/PENDING` → `NOT_EXECUTED`。与 `halt()`（1078–1104）对同类步骤的口径一致。`summarize_ops.consistency`（+172–173）新增「记为未执行却带 request_id」告警；`plan_vs_actual` 对 `HALTED` 已 `is_sample=True`（C6-3 既有）。 | (1) 夹具：生产 `PlanScheduler` + 真实 `web.Monitor` + `language_bridge.write_tracker_state/write_result` 写桥文件（`Fixture.state/result`），journal 行由夹具按生产字段追加（与 R1 已接受的同一替身，非手造终态）；(2) 红绿见 §0（2 例调度器 + 1 例摘要）；(3) 不触 Play 治理门三文件；(4) 可机械断言。 | **闭合** |
| R1-2（`BC-10`） | `_await_decision`（1399–1410）：状态/结果已变分支先查 `submitter.in_flight.locked()`，持有即返回等下个 tick（与截止分支同口径；不重试 CLI）。`record_decision`（1201–1229）对「非当前步或 phase≠await_decision」改走 `_late_decision`（1231–1265）：无论结局先记 `decisions[{…, late: true, step_status_when_replied}]` + 日志 `late_decision`；拒收只记；APPLIED 且该步为刚关闭的 `NO_DECISION`（`position == index-1`）、其后步骤均 `PENDING/AWAIT_SEND` 且无 request_id、phase=`await_send` → 回退 index、恢复 `OBSERVING`（`reopened_from`，`decided_cli_unix_s` 只作等待原流超时起点，锚点仍由 `_anchor` 取 journal receipt `at_unix_s`）；否则（其后已有动作或结果未知）→ 该步 `UNKNOWN` + `_block`（封住、停依赖）。封住/finished 后仍走既有 `_late_reply`（只记）。核：`App._decide` 在 `decision_step()` 与 `in_flight.acquire(blocking=False)` 之间的窗口不在锁保护内，但其唯一后果（tick 先关 `NO_DECISION`）正由 reopen 路径接住（`test_r1_2_accepted_decision_after_step_closed_reopens_observation`）；若计划末 `stop` 先取得锁则 confirm 被 `在途` 拒绝、根本不发送，不会丢受理；`_send_stop` 被 `在途` 拒绝时不改 stop 步状态与 `stop_sent`，不破坏 `untouched` 判据。 | (1) 同上 + `FakeCli.delay_s` 真实线程并发（`Submitter` 生产锁/顺序）；(2) 红绿 3 例；(3) 不触治理门；(4) 可断言（锚点 = receipt 时刻、`DONE`/`follow_verified`、`UNKNOWN` + `blocked()`）。 | **闭合** |
| R1-3（`BC-10`） | (a) `attempt_closeout.failed`（1998–2002）：任何异常（含 `KeyboardInterrupt`/`OSError`）都 `found.append`；`describe_failure` 把 `KeyboardInterrupt`/不明异常/新 `UnknownOutcome` 记 `UNKNOWN`；`run_attempt` 对非空 `found` 抛首项，`stage_play` 捕获置 `failure`、后续剧本记 `attempted=False`，`main` 对 `KeyboardInterrupt/Exception` 返回 3。(b) 归档跳过（Unity 停止未确认 / 会话仍在运行）→ `record["archive"]={moved: [], skipped}` **且** `found.append(UnknownOutcome(…))`（2088–2093）；归档中异常 → `record["archive"]={moved: "UNKNOWN", skipped: "归档中失败…"}` + `failed("archive")`。原 `S-WALL` 先入 `found`、UNKNOWN 依序追加（`stops_all` 全列、`stop` 取首项）。(c) `summarize_ops.summarize` 对 `called ∧ rc≠0` 记 `failures[{code: UNKNOWN}]`，`S-ENVELOPE` 拒评记 `failures[{code: S-ENVELOPE}]`；`main` 有 `failures` 即 stderr 打印并 `return 3`（摘要文件照写）；`stage_play`（2218–2222）`summary.rc≠0` → `failure = failure or Stop("S-ENVELOPE", …)`（有 S-ENVELOPE 项）/ `UnknownOutcome(…)`（其它，含 rc 2 拒绝覆盖已有摘要），`closeout["summary"]="rc=N"` 照记、`closeout_tail` 带 `stop`。核：`analyze_play score` 只在 `_write` 后 `return 0`，异常路径不写 `--out` → 「`score.json` 已存在但 rc≠0 被下次引用」不可达（替身写后再退非 0 只是替身形态）。 | (1) 生产入口 `play_ops.main("play", …)` + 临时 git 仓库/假 ssh/假会话（既有 `FormalFailurePathTests` 基座）；Ctrl-C/OSError 以替换模块函数注入收尾步骤（`patch_ops`，`addCleanup` 还原）、评分非 0 以替身配置 `score_rc`/`STUB_SCORE_RC`；(2) 红绿 4 例（3 play + 1 摘要）；(3) 不触治理门；(4) 可断言（rc 3、`STOP UNKNOWN`、`second["attempted"]=False`、`loop2-p2` 会话目录不存在、`runtime/frames` 原样留存、`closeout_tail.stop.code`）。 | **闭合** |
| R1-4（`BC-10`，附合同争议） | `summarize_ops.take_score_call`（220–234）：在 `run_score` 的 `out.exists()` 去重之后、调用之前读 `$OUT/play/score-ledger.json`（`formal_score_calls`）；非 dict / 非 int / 不可读 → `used=None` → 拒评 `S-ENVELOPE …不可读（fail-closed）`；`used+1 > FORMAL_SCORE_LIMIT(=2)` → 拒评并照记 `S-ENVELOPE formal_score_calls would exceed …`；否则先写 `used+1` 再调用（成功/失败共账）。`run_score` 返回带 `ledger` 说明；`summarize` 把 S-ENVELOPE 列入 `failures` → `main` rc 3 → `stage_play` 置 `Stop("S-ENVELOPE")` → `play` 非 0 退出。操作单 §12 新句与代码逐字一致（至多一次/每次调用前守账/按字面总次数/待裁定/`play` 非 0）。`FORMAL_SCORE_LIMIT` 按已签字面「实现自证对正式归档 ≤ 2 次」取**总次数**，并明示语义待接受裁定——满足 R1-4「无论裁定，工具须在每次评分前守账、越界即停并照记，不得静默超额」。 | (1) `OpsDir` 夹具 + 生产 `summarize/run_score/main`，评分 CLI 为记录型替身；(2) 红绿 1 例（三归档 → 恰 2 次调用、第 3 次 `S-ENVELOPE`、rc 3、重跑不再调用、账本损坏拒评）；(3) 不触治理门；(4) 可断言。 | **闭合（机制）**；`N` 的语义按接受裁定（见 §3 说明） |

修复触及行上的其它边界核（未产生 finding）：`_late_decision` 在 `finished`/`halted` 时不会被调用（`record_decision` 先分流 `_late_reply`，与 R1-1 后的 `HALTED` 结局相容）；reopen 时 `self.steps[self.index]["status"]="PENDING"` 有 `index < len` 守卫、`finished=False` 冗余无害；`_late_decision` 在 `_blocked` 已置时仍可能 reopen 为 `OBSERVING`，但 `tick` 因 `_blocked` 不推进、收尾 `halt` 记 `HALTED`，不丢记录；`_await_decision` 等待的在途锁若由操作者 stop 持有，只多等一个 tick，TERMINAL 由 `tick` 先行处理；`failed()` 对 `Stop` 的追加与原行为相同（无重复追加）；`stage_play` 的 `envelope[0]` 只在列表非空时取用；`take_score_call` 的账本写入非原子（崩溃损坏 → 下次 fail-closed 不评分，符合守账方向）；`attempts_in` 为空时 `failures=[]`、`main` rc 0 不变。

### §2 AC 逐项（依据列 `BC-n` 读作 AC-n；未改动文件结论随 R1@K1K3 通过候选与 R1@OpsK1K2K3K4 §2 携带）

| AC | 本轮结论 | 依据 |
|---|---|---|
| AC-1/2/3/4/6/7/12/17 | 成立（携带） | 对应运行时文件自 `9d95aeb` 零 diff；`test_loop2_isolation` 既有断言照绿（focused 144 OK）。 |
| AC-5 修订 1、AC-9 修订 1、AC-11 修订 1、AC-13 修订 1、AC-15/16（代码侧） | 成立（携带；AC-13 本轮完整 diff 逐文件在闭集内、全套/focused/红绿指针可复算） | `operator_web.py` 零 diff；在线工具无新 import（隔离测试照绿）；§4。 |
| AC-8 修订 3 | **成立**（R1 不成立项已闭） | R1-1/R1-2 闭合：已受理命令在会话 TERMINAL / 确认在途 / 迟到受理三类路径均不被事后改写为未执行或 `NO_DECISION`；一致性检查补告警。 |
| AC-10 修订 1…5 | **成立（代码侧）** | R1-3/R1-4 闭合：失败保留原流/rc/原因/实账并非零退出、停依赖；评分前守账、越界 `S-ENVELOPE` 照记。守账上限 `N` 的合同语义待接受裁定（§3）。 |
| AC-14 修订 1/2 | 代码侧成立；正式证据 `NOT_RUN` | 本人 Ctrl-C 与收尾不明失败一律 UNKNOWN、不开下一剧本、非零退出；真实板/Unity 未验证。 |
| AC-18 修订 1 | 摘要一致性缺口已闭；证据 `NOT_RUN` | `consistency()` 新增告警；正式归档与复核重放后置。 |

### §3 Findings

**新阻断：无。** 修复触及行上未发现 CLASS_1/2；R1-1、R1-2、R1-3、R1-4 均闭合（§1）；`RED_LINE` 无（在线工具无真值/评分/几何导入，`test_loop2_isolation` 照绿；呈现路径零 diff）；无 `上轮漏检`/`上游漏检`；CLASS_3 无。不写 `blocks_consuming_gate`（无未改动行 `上轮漏检` CLASS_2；状态板无 `Consuming=yes` 活跃行）。

路由接受角色（非阻断、非本轮新 finding）：
- **R1-4 的 `N` 语义**（交接 §12.4）：代码按字面总次数 `FORMAL_SCORE_LIMIT = 2`，正式 3 剧本全部归档时第 3 次评分**必然**被拒并以 `S-ENVELOPE` 非零退出——这是合同字面的直接后果，不是缺陷。接受裁定「总次数 2」则现状即终态；裁定「每归档 1 次（合计 3）」或改信封，则须改该常量并更新 `test_r1_4_*`——该改动落在 PLAY_GOVERNING（`tools/`、`tests/`），按 workflow §4.4 开轮资格进入新复核轮，不得作为静默常量调整合并。
- **R1-5**（CLASS_2，`SCOPE_GAP`）保持不可达判定、未实现，仍由接受角色记债（`docs/implementation-status.md`「范围外已知缺陷」）或裁定；本轮未对其写 block，无需 release。

### §4 UNITY_NA 与人眼保真

- 候选未对任何 AC 申请 `UNITY_NA`；AC-14/15/18 与 AC-16 板端按交接 `NOT_RUN`，本轮无可附议项，也不签发任何 `UNITY_NA`。
- SUB:2（AC-11 修订 1）：`tools/eng_loop2/operator_web.py` 在 `c8e8b3c` 与 `e24e13f` 的 blob 同为 `13db5f119e0976b05db08cf5ff358ac70a2814a7`（R1 §4 已核该 blob 的全部呈现路径与登记版本 `3ecd796…` 逐字相同）→ R1 的附议**原样携带**：本人两张一致记录可用于本候选，无须重看；提示行/用时仍 UNKNOWN。

### §5 限制、未验证与消耗

- 全套自动测试本轮未重跑（实现者停点义务，日志逐名对照见 §0）；focused 一次 + 11 例红绿一次。
- 真实板/Unity 未验证（PR-O2 原样保留）：前台 `ssh -tt`、`stty -echo`、Ctrl-C 经 pty 送达、真实会话对 stop 的时延、Unity 真实出帧/停止、归档 `rename` 跨设备行为均只有本地替身；本轮不签任何板端或 Play 结论；评分账本只对经 `summarize_ops` 的调用守账（手工直跑 `analyze_play score` 不入账，操作单未授权该路径，交接 §12.5 已披露）。
- 消耗：零 SUB:1/2/3、零 SSH/板/Unity/Play/模型/回放/API/正式 ID。
- 边界自查：本会话未修改任何实现文件；副本内红绿用 `git checkout` 切换后已恢复、`git status --porcelain` 为空；主树只写本文件与 `docs/current-status.md`。

### Verdict（R2@OpsK1K2K3K4）

**`PASS`**。R1-1…R1-4 闭合（修前红/修后绿 11/11，focused 144 OK，全套新增失败 0），修复触及行上无新 CLASS_1/2，无 `RED_LINE`。本停点返工计数止于 1/2。
passed_candidate: e24e13f020cdec9163d01ffc71d7e52ecc587f8a
通过只覆盖 `OpsK1K2K3K4` 停点的代码与操作单（含 K1K3、旧 K1K2K3K4 已通过范围的携带）；不签发 SUB:3 放行、G1–G5/B-main 正式运行、AC-14/15/16/18 证据、`UNITY_NA` 或 `DONE`。下一动作：接受角色消费本轮通过（SUB:3/正式运行是否放行按其合同与信封），裁定 R1-4 `N` 语义与 R1-5 `SCOPE_GAP` 记债；若裁定改 `FORMAL_SCORE_LIMIT`，按 §3 走新复核轮。

## R1@OpsScoreDiagK1K4（2026-10-08）— 新停点 `OpsScoreDiagK1K4` 评分/诊断合批候选（首轮）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-LOOP-002-R1@OpsScoreDiagK1K4-20261008T192429Z-c030`，`requested.round = R1@OpsScoreDiagK1K4`）。轨道：同名提案抬头逐字 `Workflow: engineering-v1`、D4 `ACCEPTED` 时裁定生效 → 按 `docs/engineering-workflow.md` 复核，依据列 `BC-n` 读作 AC-n。零消耗：零 SSH/板/Unity/Play、零模型、零归档回放、零全套重跑、零 SUB:1/2/3、`DIAG:RETRY:1` 未启动、不改绑定；只在一次性副本内读码、重跑 focused 一次、红绿一次；主树只写本文件与状态板。

### §0 候选、基线、稳定门与开轮资格

- `round_candidate: 539fd6d4444045c385a994ce4dffb23d84a98ed5`（派发块指定；运行时核：C9 §1 解析式 `git log --format=%H --fixed-strings --grep='Dispatch-Id: P1-ENG-LOOP-002-C8退回纠正-20261008T191546Z-376a' -- docs/evidence/P1-ENG-LOOP-002-play-ops.md` 唯一命中且相等；是 `origin/main` 祖先）。代码候选 `0112b4af5f9186044adce15af3d6b7a1c0a10e8f`（交接 §14/§15.3 首项）：`git diff --stat 0112b4a..539fd6d -- tools tests config controller Assets` 为空，实现文件零 diff，本轮 PG 结论对两者同值；候选到开工 HEAD（`ccd3131`）只有状态板/提案 C9 节/派发日志（`git diff --stat` 核实），无实现改动。
- 全量基线 = 上一通过候选 `e24e13f020cdec9163d01ffc71d7e52ecc587f8a`（R2@OpsK1K2K3K4 `passed_candidate`，本文件最近一行有效行；是候选祖先）。`git diff --name-only e24e13f..539fd6d` = **16 路径（+2061/−74）**，与 C9 §1 逐一相同；PLAY_GOVERNING + 操作单恰 **6 路径**：`tools/eng_loop2/play_ops.py`（+200/−5）、`tools/eng_loop2/summarize_ops.py`（+12/−8）、`tests/test_eng_loop2_play_ops.py`（+225/−2）、`tests/test_eng_loop2_summarize_ops.py`（+106/−9）、`docs/evidence/P1-ENG-LOOP-002-play-ops.md`（3 处）、`docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`（2 处）；其余 10 路径为账本/状态板/交接证据/两份日志/派发日志/implementation-status/正式设计快照/提案/本文件（已读）。`controller/`、`config/`、`Assets/`、`ProjectSettings/`、`Packages/packages-lock.json`、`.gitignore`、`runtime/`、`tools/eng_loop2/{operator_web,analyze_play,llama_adapter,deploy_digest,__init__}.py`、`tools/language_serve.py`、`tools/language_latency.py`、`tools/eng_jet/`、`tests/test_eng_loop2_operator_web.py`、`tests/test_loop2_isolation.py`、mini-ops-prep 零 diff（副本内 `git diff --stat` 核实）；修改闭集（「SUB3核清与评分上限落实」§4）成立。PG 触及的实现提交只有 `0112b4a` 与 `539fd6d`（后者仅 play-ops §12 一句），无隐藏实现改动。
- 开轮资格：PG diff 非空 → 开 `R1@OpsScoreDiagK1K4`（新停点首轮；返工计数 0/2）。首轮无「上一复核轮候选」，修复触及行 = 全量 PG diff，逐行全读。
- 稳定门（workflow §4.3.1 四条件，对照交接 §15.3/§16 与 C9 §2）：①范围/接口冻结成立（上条）；②相称测试成立——已签 `42979c14:SUB:1` 停点全套 1 次（`-score-diag-fix-tests.log`：`Ran 2474 tests`、`FAILED (failures=3, errors=13, skipped=54)`），本角色以 `grep -E '^(FAIL|ERROR):' | sort | comm` 与 `-ops-r1rework-tests.log`（2462，同 3F/13E/54 skip）逐名对照：**双向差集均空、16/16 逐名相同、新增失败 0**；16 项为 cv2/numpy 库门 10 项、旧 `runtime/runs` 工件缺失 5 项、`zero_unmatched`（运行时树图像模式）1 项，与本增量无关；本候选全套不绿、不记全套通过；12 例红绿与 focused 156 指针齐（§0 末两条本角色复算）；③无已知 Unity 失败，呈现路径 `operator_web.py` 零 diff（blob 仍 `13db5f11…`），SUB:2 本人两张一致记录按 R1@OpsK1K2K3K4 §4 附议原样携带，无须重看；④复核入口/状态板/候选/风险齐（§15.4、§14.7、C8 §3 四项披露）。候选未申请 `UNITY_NA`。
- 复核副本 `.claude/worktrees/review-P1-ENG-LOOP-002`（detach 于 `539fd6d`）；测试树哈希（`git ls-files tests | xargs cat | sha256` 前 16 位）`c27590a3569dbb93`（R2 为 `7abfb727001a77fa`，差异 = 两份测试文件的新增用例）。focused 重跑（系统 `python3` 3.14.6 `/opt/homebrew/bin/python3`，与实现者同口径）：`python3 -m unittest tests.test_eng_loop2_play_ops tests.test_eng_loop2_operator_web tests.test_eng_loop2_summarize_ops tests.test_loop2_isolation` → **Ran 156 tests in 203.121s, OK**（输出在会话暂存目录，只回显摘要；1 条既有 `ResourceWarning: subprocess … is still running`，与 PR-C8-3 同类）。
- **修前红/修后绿**（副本内；`git checkout e24e13f -- tools/eng_loop2/play_ops.py tools/eng_loop2/summarize_ops.py` 把工具代码退到上一通过候选、测试保持候选版本 → 跑 12 例具名回归 → 恢复候选 → 再跑）：修前 `Ran 12 tests … FAILED (failures=8, errors=4)`——行为红 8：长根 d1 真实 bind `ssh_master_failed d1 … rc 255`（= SUB:3 原故障逐字复现）、过长父目录未 `DIAG_REFUSED control_path_too_long` 而走到故障、套接字失效用例无 `control_dir`、三归档/四归档只评 2 次（`2 != 3`×2）、失败扣次 `3 != 0`、继承账 `0 != 1`、`{}` 坏账被当 0（`True is not false`）；接口 error 4：无 `DiagControlDir`/`DIAG_CONTROL_PARENT`、粗账无 `control_dir`×2。与交接 §14.4 自述逐项一致。修后同 12 例 **OK**（15.5 s）。恢复后副本 `git status --porcelain` 为空。

### §1 修复触及行逐文件核对（6 PG 路径全读 diff；直接关联读 `SshUnit.open/_check_and_claim/channel_argv/chan/chan_popen/close`、`tree_bytes`、`DiagAccount.take/consume/unknown/disk`、`DiagConnection.open/_check_and_claim`、`DiagServe.start/stop_and_release`、`DiagnosticRun.air_reading/prepare_board/start_service/closeout/_close_session/_close_service/_close_logs/_restore_runtime/execute`、`stage_diag`、`main`、`extract_block`、`summarize_ops.run_score/cite_score/summarize` 失败出口、测试 `DiagTestBase/DiagTests/RepoFixture` 假 ssh 全文）

| 路径 | 核对 | 结论 |
|---|---|---|
| `tools/eng_loop2/play_ops.py` | 常量 `UNIX_SOCKET_PATH_CAPACITY`（linux 108 / 其他 104，fail-closed）、`OPENSSH_CONTROL_SUFFIX_BYTES=17`（mux.c `muxserver_listen` 的 `.<16 随机>`，与 SUB:3 原 stderr 103→120 一致）、`DIAG_CONTROL_PARENT=None`→`tempfile.gettempdir()`。`unix_socket_path_fits` 按 `os.fsencode` 字节 + 17 ≤ 容量−1（macOS 103），不按字符数。`DiagControlDir.allocate`：先以 `前缀+8 位`（Python `mkdtemp` 随机名恰 8 字符）+ 最长名字预核，过长不建目录；`mkdtemp`（O_EXCL、0700）后 `lstat` 核目录/非链接/`uid==getuid()`/无组他人位；逐名核字节并以同字节长度探针 `<name>.<token_hex(8)>` **实际 bind 本机 AF_UNIX** 后关闭+`unlink`（`finally` 保证探针不残留）；任一失败 `except BaseException` 只 `rmdir` 刚建空目录后重抛 `DiagRefused`。`control_path(name)` 闭集外名字 `DiagFault`。`verify()`：`lstat` 复核目录/uid/权限/与初建 uid 一致，缺失 `DiagFault control_dir_missing`。`entries/bytes`：`listdir` + 逐项 `lstat`（不跟随、不含子目录；缺目录 0）。`release()`：仅 `left==[]` 且 `is_dir` 且非链接才 `rmdir`，失败记 `error`；任何残留不删、返回清单；`released=True`。`DiagConnection.__init__` 改收 `control`，`self.cm = control.control_path(name)`——继承的 `channel_argv`（`-S cm`）、`_check_and_claim`（`-S cm -O check`）、`close`（`-S cm -O exit`）与 `open`（`ControlPath=cm`）**同一实际路径**，正式 `SshUnit` 零 diff。`open()`：先 `control.verify()`（在 `account.take("master_connections")` 之前 → 不计次）、残留判 `os.path.lexists`、`ssh/<name>.tsv` 记 `control_path`、粗账 `master_connections[]` 记 `control_path`。`DiagnosticRun.allocate_control` 在 `prepare_board` 内 `resolve_board_ts` 之后、`account.consume()` 之前：`DiagRefused` 经 `execute()` 的 `except DiagRefused: raise` → 外层 `consumed=False` → `finish`+`shutdown_web`+`DIAG_REFUSED` 返回 3（与既有 `resolve_board_ts` 拒启路径同形；此时 `hold_runtime` 尚未执行，无需归位）；成功则粗账 `control_dir` 记录全量、`disk.air_source` 追加说明、事件 `diag_control_dir`。`start_service` 以同一 `control` 建 d2。`air_reading` 加 `control.bytes()`（未释放时）。`_close_connections` 改为 `try: 逐连接 close; conn=None finally: _release_control()`——释放严格在 `-O exit` 之后；`_release_control`：先 `air_reading("before control dir release")`（峰值在释放前取到），若任一连接 `close` 未完成则只记 UNKNOWN 保留目录，否则 `release()` → 事件 `diag_control_dir_release`，未删即 UNKNOWN（含残留清单/错误）。`closeout` 对 `connections` 步骤异常统一记 UNKNOWN 并继续后续安全步骤（既有）。 | 与 AC-10 修订 8 合同（短私有本进程目录、编码字节+后缀留量、实测 bind、同路径、失效不直连/不认证/不重试、成功失败均计次、只删本次空目录、残留 UNKNOWN、计入 Air 峰值、不改全局 SSH/仓库路径/输出根/双来源门）逐条一致；无新共享状态、无新线程；新 import 仅标准库 `secrets/socket/stat`。**无 finding** |
| `tools/eng_loop2/summarize_ops.py` | `FORMAL_SCORE_LIMIT` 2→3（模块/常量说明同步为「全批实际调用总上限，非每归档/每摘要」）。`take_score_call`：文件不存在 → `{key: 0}`；存在 → 须 dict 且 `raw` 为非负 `int`（排除 `bool`、小数、负数、缺键、非对象），否则 `used=None` → `S-ENVELOPE …不可读（fail-closed）`；`OSError/ValueError(JSONDecodeError/UnicodeDecodeError)/TypeError` 同拒评；`used+1 > 3` → 拒评照记；否则**先写** `used+1` 再返回可调用（成功/失败共账）。`run_score` 的已有输出分支（不调用不计）、`cite_score`、`summarize` 失败出口、`main` rc 3 零 diff。 | 与 AC-10 修订 7（三允许/第 4 次调用前拒、先扣后调、共账、继承不重置、坏账拒评、已有输出只引用、诊断不评分）一致；与 play-ops §12 纠正后文字（「不存在时首次从 0 建立；已存在不可读/缺计数键/计数非法即拒评」）逐字对准 → C8-1 闭合核实。写入非原子为 R2 已记观察，未改动。**无 finding** |
| `tests/test_eng_loop2_play_ops.py` | 假 ssh 新增 `real_control_socket`（同 OpenSSH：先在 `<ControlPath>.<16 随机>` 上**真实 bind** 本机 AF_UNIX 再 `rename`，放不下即 stderr `unix_listener … too long` + rc 255）与 `exit_keeps_socket`（`-O exit` rc 255 且不删套接字）。`DiagTestBase`：`long_root=True` 时把执行检出放进加长目录使旧式 `诊断根/ssh/cm-d1` 带后缀 ≥125 B（测试内断言 `> 容量−1`）；独立短父目录 `c<随机>`（`addCleanup` 连残留清掉）并把 `DIAG_CONTROL_PARENT` 指向它（`addCleanup` 还原）；所有既有 `DiagTests` 12 例改为真实 bind 运行。`DiagControlPathTests` 7 例：生产入口长根端到端（先本机 `_bind_probe` 实证旧式路径 too long，再核 d1/d2 rc 0、路径不同/同目录/诊断根外/带后缀 ≤ 上限/探针 ok/0o700+uid、每连接 master→check→channel→…→exit 同路径且各恰一次 master、无 `-G/-fN/-S` 以外直连、释放在 exit 后且空目录已删、`air_source` 含说明、`before control dir release` 读数存在、事件顺序、tsv `control_path` 行、`unknown==[]`）；生产缺省父目录直接 `allocate` 两次（唯一、0o700、探针已删、`_bind_probe` 不抛、闭集外名字 `DiagFault`、残留套接字不删 `left=['d2']`、空目录删）；过长父目录 `DIAG_REFUSED control_path_too_long`、`consumed=false`、除 `-G` 外 ssh 0、父目录无残留、再次仍拒启；目录 `chmod 0755` → `open()` 前 `control_dir_unsafe`、计次 0、无 `-fN`；主连接 rc 255 → 计 1、无 check/通道/exit/直连/重试/d2、目录已释放；`check_fail` → `control_socket_unavailable`、1 次 master、无通道、单路径、已释放；`exit_keeps_socket` → `removed=False`、`left=['d1','d2']`、套接字仍在、UNKNOWN 含路径。 | 生产入口 + 真实 AF_UNIX bind（非假 ssh 成功作唯一证明），修前红逐例由行为触发（§0），断言覆盖合同各点；夹具对 `$TMPDIR` 过长环境会 fail-closed（§14.7 已披露，非缺陷）。**无 finding** |
| `tests/test_eng_loop2_summarize_ops.py` | 替身增 `STUB_SCORE_NO_OUT`（失败且无输出）；R1-4 用例改按现行常量 N（N+1 归档 → N 次、第 N+1 拒、重跑不再调用、`{broken` 拒评）；新增 5 例：四归档 → 3 次调用、账 `1/3→3/3`、第 4 次 `S-ENVELOPE … (used 3, +1)` 且无 `score.json`、rc 3；三归档全评 rc 0；三次失败无输出 → 已扣 3、换摘要 0 次调用全 `S-ENVELOPE`；继承 `{"formal_score_calls": 2}` → 恰 1 次、账 3；已有输出只引用不计 + 六种坏账（`{broken`/`{}`/`true`/`1.5`/`-5`/`[2]`）拒评、调用数不变。 | 生产 `summarize/run_score/main` 入口 + 记录型替身；覆盖修订 7 全部合同点。**无 finding** |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md` | 第 0.4 表「正式归档零模型回放」行、第 12 节 OPS 增量段与评分命令括注：≤2 → 全批实际调用总上限 ≤3（AC-10 修订 7 / `SCORE:CHANGE:1`），账本语义按 C8-1 纠正，独立复核 ≤1 不变。 | 与 `summarize_ops.py` 逐字一致；不驱动与代码不同的操作员动作。**无 finding** |
| `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` | 「现行 SUB:3」节首加增量说明（SUB:3 已用尽、本修复不使其可再执行、短私有目录位置/核验/同路径/释放/UNKNOWN/指针/未真实验证）；工具表第 7 步加「释放本次私有 ControlPath 目录（空才删；残留记 UNKNOWN、不删）」。附录围栏块（`extract_block` 读取的 bash/python）零改动。 | 与代码一致；`DIAG_REQUEST_ID` 与粗账拒启判据未改，不放行新诊断。**无 finding** |

修复触及行上的其它边界核（未产生 finding）：`allocate` 的 `names` 来自 `tuple(DIAG_CHANNELS)`（d1,d2），非空；探针 bind 失败时套接字文件不会被创建，`lexists` 守卫使 `unlink` 不误删；`release()` 对符号链接目录不删（`is_symlink` 判在 `is_dir` 之后，结果 `removed=False` → UNKNOWN，fail-closed）；`released=True` 后 `air_reading("final")` 不再计该目录——残留只可能是 0 B 套接字且峰值取 `max`、释放前已读数，峰值不受影响；`_release_control` 在 `close()` 抛异常时保留目录并记 UNKNOWN，此时 `released=False`，终读数仍计入；`DiagRefused` 于 `allocate_control` 发生在 `consume()` 之前，粗账 `refused` 落盘、`consumed=false`，与 `test_diag_no_safe_short_path_is_refused_before_consumption` 一致；`verify()` 于 `take()` 之前，故障不计次；`take_score_call` 对超大整数/`0` 正常；并发：摘要为独立进程、无新线程；真值泄漏：无新 `controller`/评分/几何 import，`test_loop2_isolation` 照绿（focused 156）。

### §2 AC 逐项（依据列 `BC-n` 读作 AC-n；未改动文件结论随 R2@OpsK1K2K3K4 通过候选携带）

| AC | 本轮结论 | 依据 |
|---|---|---|
| AC-1/2/3/4/6/7/12/17 | 成立（携带） | 对应运行时文件自 `e24e13f` 零 diff；隔离测试照绿。 |
| AC-5 修订 1、AC-8 修订 3、AC-11 修订 1、AC-15/16（代码侧） | 成立（携带） | `operator_web.py`/`analyze_play.py`/调度受理记录零 diff；SUB:2 附议携带；R1-5 `SCOPE_GAP`/OPEN 不冒称已修。 |
| AC-9 修订 1 | 成立 | 新 import 仅 `secrets/socket/stat`；摘要独立进程边界未改；`test_loop2_isolation` OK。 |
| AC-10 修订 1…6 现行部分 | 成立（携带） | 正式 `SshUnit` 动作域、三阶段/有限通道/失败停依赖/双来源门零 diff；修订 6 的 N=2 部分被修订 7 替代。 |
| AC-10 修订 7 | **成立（代码侧）** | §1 `summarize_ops.py` 与 5 例红绿；play-ops 三处说明一致（C8-1 闭合核实）。正式归档评分 `NOT_RUN`。 |
| AC-10 修订 8 | **成立（本机实现证据）** | §1 `play_ops.py` 与 7 例红绿 + 既有 `DiagTests` 真实 bind；真实 OpenSSH/板未实跑（§4/§5）。 |
| AC-13 修订 1 | 成立 | 全 16 路径 diff 已读并归属；全套逐名对照与 12 例红绿/focused 156 由本角色复算（§0）；§6 窄修替代不适用（K4 路径）故跑全套，判断正确。 |
| AC-14 修订 1/2、AC-15、AC-16、AC-18 修订 1 | 代码侧携带；正式证据 `NOT_RUN` | 真实板/Unity 未验证；本轮不签。 |

### §3 Findings

**阻断：无。** 修复触及行上未发现 CLASS_1/2；`RED_LINE` 无（在线工具无真值/评分/几何导入，`test_loop2_isolation` 照绿；呈现路径零 diff）；无 `上轮漏检`/`上游漏检`（新停点首轮）。不写 `blocks_consuming_gate`（状态板无 `Consuming=yes` 活跃行）。

CLASS_3（非阻断；拥有写权限的实现角色在下一次提交应用，不开轮）：
- **OSD-R1-1（CLASS_3，`BC-10`，对应 AC-10 修订 8；PR-C8-1 的文字面）**：`tools/eng_loop2/play_ops.py::DiagControlDir.verify` 的 docstring「被替换/改权限即拒绝连接」比代码判据宽——代码核的是目录/非链接/uid/0o077/初建 uid，不记录或比较 dev/inode，**同用户同权限的目录替换不会被识别**。可达性判读：父目录为本用户私有 `$TMPDIR`（macOS `/var/folders/…/T` 0700）或测试独立临时目录，其他用户不可写，root 不在威胁模型内；同用户替换等价于操作者自毁，不在冻结的「本进程拥有的短私有临时目录」归属域内 → 不构成 CLASS_2，`release()` 误删非本对象目录同样只在该不可达路径上。逐字替换补丁（仅 docstring 一行）：`"""主连接尝试前复核目录仍是本次所建的私有目录（被替换/改权限即拒绝连接）。"""` → `"""主连接尝试前复核目录仍为本用户 0700 私有目录（改权限/换属主/非目录/缺失即拒绝连接；不比较 dev/inode，同用户同权限的目录替换不在判据内）。"""`；交接 §14.3「主连接尝试前 `verify()` 复核仍是该私有目录（被改权限/替换即 `DIAG_FAULT control_dir_unsafe`，不占主连接次数）」同样读作「改权限/换属主/非目录」。不改数字、判据或执行顺序。

路由接受角色（观察，非 finding，不阻断）：
- PR-C8-2 已独立核（§1 第一行与边界核）：`bytes()`/`air_reading`/`_release_control` 的峰值取法与释放顺序正确；真实 OpenSSH ControlMaster/`-O check`/`-O exit` 与 Jetson 未实跑，本机替身 + AF_UNIX bind 不等于真实验证（§5）。
- PR-C8-3：全套原输出 8 处 `ResourceWarning`（unclosed file / subprocess still running）与本轮 focused 1 处同类，均为既有替身子进程生命周期告警，不据此推断新代码缺陷；两空目录归属与套件外预核用量 UNKNOWN 原样保留（C8 §3）。
- 正式 `SshUnit` 路径（未改动行，闭集外）：`outputs/eng-loop2/P1-ENG-LOOP-002/ssh/cm-u1` 本机带后缀 92 B ≤ 103 B，余量 11 B，当前仓库路径下可达且可用；仓库移到更长路径时正式首用会同样失败——交接 §14.7 已记为风险、接受已读，不记 finding、不扩闭集。

### §4 UNITY_NA 与人眼保真

- 候选未对任何 AC 申请 `UNITY_NA`；AC-14/15/18 与 AC-16 板端按交接 `NOT_RUN`，本轮无可附议项，也不签发任何 `UNITY_NA`。
- SUB:2（AC-11 修订 1）：`tools/eng_loop2/operator_web.py` 在 `e24e13f` 与 `539fd6d` 的 blob 同为 `13db5f119e0976b05db08cf5ff358ac70a2814a7` → R1@OpsK1K2K3K4 §4 的附议原样携带，本人两张一致记录可用于本候选，无须重看；提示行/用时仍 UNKNOWN。

### §5 限制、未验证与消耗

- 全套自动测试本轮未重跑（实现者停点义务；日志逐名对照见 §0）；focused 一次 + 12 例红绿一次。
- 真实 OpenSSH/板未实跑：ControlMaster 在新短路径上的创建、`-O check`、通道、`-O exit` 与残留行为只有假 ssh（真实 bind + rename）与本机 AF_UNIX 探针；OpenSSH 后缀长度 17 若改版需重核（§14.7）；`$TMPDIR` 被改成长路径时 fail-closed 拒启、不自动换父目录。真实板/Unity 闭环、正式三剧本归档评分 ≤3、AC-14/15/16/18 证据均 `NOT_RUN`；本轮不签任何板端、Play 或正式门结论；`DIAG:RETRY:1` 的执行前提（通过消费、入口绑定、现场核、本人新窗口）不由本轮签发。
- 评分账本只对经 `summarize_ops` 的调用守账（手工直跑 `analyze_play score` 不入账，R2 §5 已披露，未改）。
- 消耗：零 SUB:1/2/3、零 `DIAG:RETRY:1`、零 SSH/板/Unity/Play/模型/回放/API/正式 ID。
- 边界自查：本会话未修改任何实现文件；副本内红绿用 `git checkout` 切换后已恢复、`git status --porcelain` 为空；主树只写本文件与 `docs/current-status.md`。

### Verdict（R1@OpsScoreDiagK1K4）

**`PASS`**。全量 16 路径 diff 逐文件核对，6 个 PG 路径全读；AC-10 修订 7/8 代码侧成立，修前红 8F/4E 与修后绿 12/12 由本角色在副本内复算，focused 156 OK，全套新增失败 0（16/16 历史项逐名相同）；无 CLASS_1/2、无 `RED_LINE`；1 条 CLASS_3 文字补丁（OSD-R1-1）交实现角色下一次提交应用。本停点返工计数 0/2。
passed_candidate: 539fd6d4444045c385a994ce4dffb23d84a98ed5
通过只覆盖 `OpsScoreDiagK1K4` 停点的代码与操作单（含旧 Ops/K1K3/K1K2K3K4 已通过范围的携带）；不签发 `DIAG:RETRY:1` 放行、G1–G5/B-main 正式运行、AC-14/15/16/18 证据、`UNITY_NA` 或 `DONE`。下一动作：接受角色消费本轮通过（新诊断/正式运行是否放行按其合同、信封与执行前提另裁），OSD-R1-1 CLASS_3 补丁由实现角色在下一次提交应用（不开轮）。

## R1@OpsDiagBindK1K2（2026-10-08）— 新停点 `OpsDiagBindK1K2` 诊断入口绑定候选（首轮）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-LOOP-002-R1@OpsDiagBindK1K2-20261008T204627Z-7c0f`，`requested.round = R1@OpsDiagBindK1K2`）。轨道：同名提案抬头逐字 `Workflow: engineering-v1`、D4 `ACCEPTED` 时裁定生效 → 按 `docs/engineering-workflow.md` 复核，依据列 `BC-n` 读作 AC-n。零消耗：零 SSH（含 `ssh -G`）/板/Unity/Play、零模型、零归档回放、零全套重跑、零下载/装包、零 `42979c14:SUB:1`/旧 SUB:1/2/3、`DIAG:RETRY:1` 未启动、不写任何 `diag_release:` 实际行；只在一次性副本内读码、重跑 focused 一次、新测试树修前红一次；主树只写本文件与状态板。

### §0 候选、基线、稳定门与开轮资格

- `round_candidate: c4973d03e1db374c3b837e2ec7d0754a73eac378`（派发块指定 = 上一实现派发 `C10退回纠正` 的证据/交接提交；运行时核：C11 §1 解析式 `git log --format=%H --fixed-strings --grep='Dispatch-Id: P1-ENG-LOOP-002-C10退回纠正-20261008T202817Z-3304' -- docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md` 唯一命中且相等；是 `origin/main` 祖先）。纠正候选代码提交 `4f350f315bc8b451bfc7d93dd09c4d1286347ea7`（交接 §19 解析式唯一命中），前版候选代码提交 `ec9cd72a6548486ba317d3f51296de8c12ae084e`（§18 解析式唯一命中）：`git diff --stat 4f350f3..c4973d0` 只有状态板、Ops 交接 §19 与 `-c10-rework-focused.log`，实现文件零 diff；`ec9cd72..4f350f3` 的实现增量只有 `tests/test_eng_loop2_play_ops.py`（+60/−60），生产 `tools/eng_loop2/play_ops.py` blob 在 `ec9cd72` 与候选同为 `ec675f70dd7aad19e9ae103f53a4d643e2b63bec`；候选到开工 HEAD（`d0da638`）在 `tools/`、`tests/`、三操作单上零 diff（副本内 `git diff --stat HEAD origin/main` 核实），无隐藏实现改动。
- 全量基线 = 上一通过候选 `539fd6d4444045c385a994ce4dffb23d84a98ed5`（R1@OpsScoreDiagK1K4 `passed_candidate`，本文件最近一行有效行，位于最近 `round_candidate` 之后；是候选祖先）。`git diff --name-only 539fd6d..c4973d0` = **11 路径（+1653/−69）**，与 C11 §1 逐一相同；PLAY_GOVERNING + 三操作单恰 **3 路径（+487/−44）**：`tools/eng_loop2/play_ops.py`（+168 行变更）、`tests/test_eng_loop2_play_ops.py`（+326）、`docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`（+37）；其余 8 路径为状态板、Ops 交接 §17–19、两份 focused 日志、派发日志（32 条）、implementation-status（接受「R1通过消费与新诊断前提」节）、提案（答复/C10/C11 节）、本文件（R1@OpsScoreDiagK1K4 节），逐一读归属，无协调基础设施、无账本改动。`controller/`、`config/`、`Assets/`、`ProjectSettings/`、`Packages/packages-lock.json`、`tools/eng_loop2/{operator_web,summarize_ops,analyze_play,llama_adapter,deploy_digest,__init__}.py`、`tools/language_serve.py`、`tools/check_*.py`、`docs/evidence/P1-ENG-LOOP-002-play-ops.md`、mini-ops-prep 零 diff（副本内 `git diff --stat` 核实）；修改闭集（「诊断绑定方案答复」§2）成立，C10-1 纠正后测试 hunk 全部落在 `DiagTestBase`/`DiagTests`/`DiagBindingTests` 类体内（本角色读完整 diff 核实，无模块级新定义）。
- 开轮资格：PG diff 非空 → 开 `R1@OpsDiagBindK1K2`（新停点首轮；返工计数 0/2）。首轮无「上一复核轮候选」，修复触及行 = 全量 PG diff，逐行全读。
- 稳定门（workflow §4.3.1 四条件，对照交接 §18.4/§19.3 与 C11 §2）：①范围/接口冻结成立（上条；BIND-1…6/Q1=A 接口与答复 §1 逐条对应，见 §1）；②相称测试成立——按 AC-13 修订 2 / engineering §6 窄修替代：改动只在诊断段与其测试，不触真实模型加载器、数据划分、评分/对外指标路径（`summarize_ops.py`/`analyze_play.py` 零 diff，`run_offline_summary` 只改记录的 id 值），`play_ops.py` 不在板部署闭集，全部导入者在 focused 四模块内；本角色判替代**充分**（PR-C11-1 闭：新树红绿本角色自跑，见下条），未跑全套、不记全套通过，旧全套 16 项历史失败/两空目录/套件外预核 UNKNOWN 原样携带；③无已知 Unity 失败，呈现路径 `operator_web.py` blob 在 `539fd6d` 与候选同为 `13db5f119e0976b05db08cf5ff358ac70a2814a7`，板输入围栏块零改（下条），SUB:2 附议携带；④复核入口/状态板/候选/风险齐（§18.5、§19.4、C10 §3、C11 §3）。候选未申请 `UNITY_NA`。
- 复核副本 `.claude/worktrees/review-P1-ENG-LOOP-002`（detach 于 `c4973d0`）；测试树哈希（`git ls-files tests | xargs cat | sha256` 前 16 位）`323b2b2630ffdb06`（R1@OpsScoreDiagK1K4 为 `c27590a3569dbb93`，差异 = `test_eng_loop2_play_ops.py` 本候选 hunk）。focused 重跑（系统 `python3` 3.14.6 `/opt/homebrew/bin/python3`，与实现者同口径）：`python3 -m unittest tests.test_eng_loop2_play_ops tests.test_eng_loop2_operator_web tests.test_eng_loop2_summarize_ops tests.test_loop2_isolation` → **Ran 169 tests in 238.509s, OK**（输出在会话暂存目录，只回显摘要；1 条既有 `ResourceWarning: subprocess … is still running`，与 PR-C8-3 同类）。
- **新测试树修前红（PR-C11-1）**：会话暂存目录内 `git archive c4973d0` 导出副本，仅把 `tools/eng_loop2/play_ops.py` 换成 `539fd6d` blob（`ff86eaf`），测试保持候选版（sha256 `84ddf521…b741b227` = 交接 §19.2 所记新候选测试哈希）→ `python3 -m unittest tests.test_eng_loop2_play_ops.DiagBindingTests` → **Ran 13, FAILED (failures=35, errors=4), rc 1**，与 §18.3 逐类相同：fail-open 生产守账红 13 子例（`test_unreadable_or_nonobject_ledger_refuses` 9：7 子例基线吞坏账建根进 preflight、`list`/`string` 2 子例基线抛未捕获 `AttributeError: 'list'/'str' object has no attribute 'get'`；`test_retry1_own_consumed_ledger_refuses` 缺键/null/0/空串 4 子例基线放过建根）；保持性绿绿（`test_unknown_request_id_refused` 6 子例、consumed=true/"false"/1、`test_literal_false_own_ledger_passes_guard`）；新接口缺口 F/E（旧入口不认新 id 的提前拒、`DIAG_ENTRIES`/`DIAG_RELEASE_KEY_LINE` 缺失 4 E）单列不计红证据。修后绿 = 上条 focused 169 OK（含 `DiagBindingTests` 13、`DiagTests` 12、`DiagControlPathTests` 7、`DiagAccountTests`）。导出副本已删除，复核副本 `git status --porcelain` 为空。
- 板输入围栏零改核实（BIND-6/Q1=A）：副本内以候选 `extract_block` 对 `539fd6d` 与候选两版诊断页逐一取附录 0–7 的 bash 围栏块求 sha256，8/8 逐字节相同（`4f6da2bf…`×3、`eedb0b42…`、`19f3d1d8…`×3、`86173e58…`）；候选新增的围栏只有「现行 DIAG:RETRY:1」节的唯一命令（页内围栏 40 → 42 处）。

### §1 修复触及行逐文件核对（3 PG 路径全读 diff；直接关联读 `release_gate` 全文（1.0–1.5、`rel`/`passed`/PG/全局 blocks/`$DOCWT`）、`_last_key_line`、`MR`、`Shell.run`、`Recorder.event`/`DiagRecorder`、`DiagAccount.__init__/save/consume/finish`、`DiagnosticRun.__init__/_refuse_if_consumed/preflight/prepare_board(consume 时点)/execute/run_offline_summary`、`stage_diag`、`build_parser`、`extract_block`；测试 `RepoFixture.commit_docs/main`、`DiagTestBase`、`DiagTests`、`DiagBindingTests`、`DiagControlPathTests`/`DiagAccountTests` 构造点）

| 路径 | 核对 | 结论 |
|---|---|---|
| `tools/eng_loop2/play_ops.py` | **BIND-1**：`DiagEntry`（frozen dataclass）+ `DIAG_ENTRIES`（`MappingProxyType`，恰两项）：旧 `DIAG_REQUEST_ID`/`DIAG_LEDGER_HITS`/`DIAG_RELEASE_LINE` 名与值零改（后者生产已无调用点，仅作历史常量）、旧条目 `exhausted`/`sub3_release`；新 `DIAG_RETRY1_REQUEST_ID = "P1-ENG-LOOP-002:DIAG:RETRY:1"`、`signed`、标题片段逐字 = 账本 10-08 二级标题片段、`diag_release`、`("P1",)`；`DIAG_LIMITS` 对象与十个数值零改，与账本签发维度逐项相同（本角色对照账本第 57 行）。**BIND-2**：`diag_entry_for` 在 `stage_diag`（建 `DiagnosticRun` 前，stderr、rc 3）与 `DiagnosticRun.__init__`（`root` 计算后、`mkdir` 前）各调用一次，未知 id → `request_id_unknown`、非 `signed` → `request_exhausted`（无条件，不读 `outputs/`）、剧本不在 `playbooks` → `playbook_not_signed`；`_refuse_if_consumed` 重写：`read_bytes().decode("utf-8")` + `json.loads`，`OSError/UnicodeDecodeError/ValueError` → `diag_ledger_unreadable <路径>`，非 `dict` 同拒、`request_id` 非 `str` 同拒（**原 `web.read_json(...) or {}` fail-open 已修**），同 id 仅 `document.get("consumed", None) is not False` 为假（即 JSON 字面 `false`）才继续，其他 id 可读即跳过；执行点仍在 `mkdir` 之前 → 拒启不建根、不写账。`DiagAccount.__init__` 新增关键字 `request_id`/`entry_binding`，`"consumed": False` 初值、`consume()`（`prepare_board` 内首个主连接前）与 `finish()`（不动 `consumed`）零改；`DiagnosticRun` 唯一生产构造点显式传 `self.entry.request_id` 与五键 `entry_binding`。**BIND-3**：`preflight` 在 `release_gate(ctx, ledger_hits=(entry.ledger_title, entry.request_id))` 通过后（`release_gate` 函数体零改，1.5 仍是发布引用全文两子串），`git show <rel>:docs/authorizations.md` 经 `Shell.run`（本机 git，原流落 `raw/`，不计任何受限维度）→ `diag_ledger_binding`：`rc != 0` → `None` → `ledger_unreadable`；按 `line.startswith("## ")` 分条，标题含片段恰一条（0 `ledger_entry_missing`/>1 `ledger_entry_ambiguous`），正文（标题行之后到下一 `## ` 之前）含 `` `<完整 id>` `` 记号否则 `ledger_request_id_missing`——`…:WINDOW` 扩展因紧随字符为 `:` 非反引号不命中、标题行自身不算正文、`### ` 不切条；返回标题行号/原文。**BIND-4**：`DIAG_RELEASE_KEY_LINE = MR + r"diag_release: (\S+) ([0-9a-f]{40})(`|[ \t]|$)"`，`MR` 恰一个捕获组 → `group(2)` 为 id、`group(3)` 为 sha（与 `_last_key_line`/旧 `DIAG_RELEASE_LINE` 同约定），`diag_release_binding`：id 须逐字相等（他 id/前缀扩展/旧键/占位 `<…>`/大写/短 sha/无空格均不命中）、读取失败 `diag_release_unreadable`、无本 id 行 `diag_release_missing`、有行无一等于门核 `passed`（`passed is None` 亦拒）→ `diag_release_mismatch`，取最后一条匹配行号/值；不以 `gate.rel` 代 `passed`。两处绑定结果 `update` 进 `account.data["entry_binding"]`（`__init__` 已置 dict，非 None）并 `save`，事件 `diag_entry_binding`（`Recorder.event(kind, **fields)`，键名 `request_id/status/ledger_title/release_key/playbooks/ledger_title_line(_no)/release_line_no/release_value/passed_candidate/rel` 与 `kind` 无冲突）。顺序：`release_gate` → BIND-3 → BIND-4 → 剧本记录 → …，全部在 `prepare_board` 的 `consume()` 之前；任一 `DiagRefused` 经 `execute()` 既有路径 `consumed=false` → `finish`+`shutdown_web`+`DIAG_REFUSED …（未消耗 <条目 id> 受限维度）` rc 3。**BIND-5**：`diag_start` 事件、`NOTES.md` 页首、`play-record.json`、拒启文案改用 `self.entry.request_id`；`stage_diag` 文档串与 `--request-id`/`--playbook` help 改指新条目（argparse `choices` 仍 P1/P2/P3，P2/P3 由闭表在建根前拒）。模块 docstring 第 28–31 行同步。OSD-R1-1 `DiagControlDir.verify` docstring 一行逐字 = R1@OpsScoreDiagK1K4 §3 补丁，判据零改。新 import 仅标准库 `types`。 | 与「诊断绑定方案答复」§1 BIND-1…6 及 AC-10 修订 9 逐条一致；无新共享状态/线程；fail-closed 路径逐分支核（读失败、非 UTF-8、非对象、身份缺失/非字符串、`consumed` 缺键/null/0/空串/字符串/true、账本缺条/重复/跨条/WINDOW/读取失败、放行行缺/不匹配/读取失败、`passed None`）。**无 finding** |
| `tests/test_eng_loop2_play_ops.py` | `DiagTestBase`：三常量 `RETRY1`/`RETRY1_TITLE`/`SUB3` 为类属性（C10-1 纠正；字面与 `ops.DIAG_ENTRIES` 独立比对），夹具改为先提案 ``- `diag_release: <RETRY1> <passed>` `` 后账本 ``## x — <标题片段>`` 与 ``- `<RETRY1>` `` 两行，`diag()` 用新 id/P1；`DiagTests` 四例改断言 `diag_release_missing/mismatch/unreadable`、`ledger_entry_missing <RETRY1>`、`request_consumed <RETRY1> 已于`，e2e 加新 id 身份断言（粗账/play-record/NOTES/`diag_start`、`entry_binding.release_value == passed`）与再次启动拒；**`DiagBindingTests`** 13 例全走生产入口 `play_ops.main`（stderr 合并、未捕获异常直接判 F）：坏账 9 子例与非法 `consumed` 7 子例的粗账由生产 `DiagAccount` 写盘 + `consume()` 后在字节上定点破坏，`guard_id()` 只桥身份（基线 = 旧 id，经同一生产守账路径）、`production_ledger` 只桥构造参数；建根前拒启断言 rc 3 + 根集合不变 + ssh 0；建根后前提拒启断言 rc 3 + `consumed=false` + `used` 全 0 + ssh 0；正向 `test_literal_false_own_ledger_passes_guard`（字面 false 不阻断、在放行行处拒）、`test_old_sub3_consumed_ledger_does_not_block_retry1`（旧账原样保留）、`test_retry1_account_records_binding_and_signed_limits`（闭表/常量/限额逐维度字面断言 + `root_exists` 替身走过全部绑定前提后在板核处收尾，`consumed=true`、`master_connections=1`、`entry_binding` 九键逐值、两事件 id）；BIND-4 十种非法行变体 + `rel`/全零/大写/旧 id 行 mismatch + 纯函数 `rel≠passed`/列表记号行/`passed None`；BIND-3 六种账本变体 + 纯函数 `None`/`### ` 不切条；`test_contract_format_examples_are_not_release_lines` 扫真实提案与诊断页的 `diag_release: <` 示例均不命中正则。 | 修前红 35F/4E 由本角色在新树复算，类别划分与 §18.3 相同；`DiagControlPathTests` 7 例随基类改走新 id（披露 1）在 focused 内照绿。**无 finding** |
| `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` | 页首要点改指「现行 DIAG:RETRY:1」并写明旧 SUB:3 于 `20261008T155230Z` 用尽；新节：签发来源与维度（与 `DIAG_LIMITS`/账本逐项相同）、执行前提 1（建根前机械核，原因码与代码逐字一致）/2（建根后机械核：放行核对全部 + 账本唯一条目 + `diag_release:` 严格格式，原因码逐字一致，示例为占位符）/3（接受核撤回/消耗、现场核、本人新窗口 `…:DIAG:RETRY:1:WINDOW` 当前未给）、唯一命令（`--playbook P1` 固定、尖括号占位）、拒启与用尽（建根前/后、`consume` 时点、旧账不动、删账不可恢复）、身份记录（粗账/NOTES/事件/play-record）、工具步骤指向历史节表；原节改题「历史 SUB:3（…已耗尽）」并加历史说明、原文保留；附录 3 标题改写 + BIND-Q1 选 A 说明块，围栏块字节零改（§0 末条核实）。 | 与代码判据/原因码/执行顺序一致；不放行、不改额度；操作员按本页不会得到与工具不同的动作。**无 finding** |

修复触及行上的其它边界核（未产生 finding）：`stage_diag` 与 `__init__` 各调一次 `diag_entry_for`（冗余但无副作用，第二次不可能失败）；建根前拒启打印到 stderr、建根后到 stdout（既有分流，测试两路都捕获，诊断页只要求 `DIAG_REFUSED` 文案）；`_refuse_if_consumed` 扫描域仍为 `<repo>/outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/*/ops-diagnostic-ledger.json` 一层（§18.5 已披露）；`diag_ledger_binding` 不识别围栏内同形 `## ` 行——本角色在副本内对真实账本调用：真实账本第 21 行有一处围栏内 `## `（位于目标条目之前），绑定仍唯一解析到第 50 行标题、正文第 57 行反引号完整 id 命中，`DIAG_RETRY1` 条目在真实账本上可达且唯一；对真实提案调用 `diag_release_binding(…, passed=539fd6d…)` → `diag_release_missing`（正确：接受尚未写实际行），提案内唯一 `diag_release: <` 为 BIND-4 表格示例、不命中；`DiagAccount` 缺省 `request_id` 仍为旧 id（披露 2）只有闭集外 `DiagAccountTests` 直接构造可达，生产唯一构造点显式传条目 id，不构成可达缺陷；并发：无新线程/共享状态；真值泄漏：无新 `controller`/评分/几何 import，`test_loop2_isolation` 照绿。

### §2 AC 逐项与 C10/C11 预复核关注（依据列 `BC-n` 读作 AC-n；未改动文件结论随 R1@OpsScoreDiagK1K4 通过候选携带）

| AC / 关注 | 本轮结论 | 依据 |
|---|---|---|
| AC-1/2/3/4/5/6/7/8/9/11/12/15/16（代码侧）/17 | 成立（携带） | 对应运行时文件自 `539fd6d` 零 diff；隔离测试照绿；R1-5 `SCOPE_GAP`/OPEN 不冒称已修。 |
| AC-10 修订 1…8 现行部分 | 成立（携带） | `release_gate`/`require_gate`/`require_g4`/`SshUnit`/正式各 stage/`DiagControlDir`/`DiagConnection`/`DiagServe`/收尾逻辑零 diff；`DiagControlPathTests` 7 例照绿。 |
| AC-10 修订 9 | **成立（本机实现证据）** | §1 三文件；修前红 35F/4E（新树本角色复算）→ 修后绿 13/13 + focused 169 OK；真实 OpenSSH/板/Unity 未实跑；`diag_release:` 实际行未写；`DIAG:RETRY:1` 未放行（§4/§5）。 |
| AC-13 修订 2 | **成立** | 11 路径 diff 已读并归属；窄修替代前提成立（§0 条件②）；新树 focused + 红绿由本角色复算；未跑全套、不记全套通过。 |
| AC-14 修订 1/2、AC-15、AC-16 板端、AC-18 修订 1 | 代码侧携带；正式证据 `NOT_RUN` | 真实板/Unity 未验证；本轮不签。 |
| PR-C11-1（红绿携带充分性） | **闭**：不靠携带，本角色在新测试树自跑修前红（§0）；修后绿在 focused 169 内 | §0 第 6–7 条。 |
| PR-C10-1（`release_gate` docstring 陈旧） | CLASS_3，见 §3 OSB-R1-1 | 参数实际来自 `self.entry`，不驱动工具/操作员动作。 |
| PR-C10-2（BIND-2 扫描域/生产写盘红绿/字面 False/建根前后资源 0；BIND-3/4 正向与拒绝分支） | 已独立核，无 finding | §1 第一、二行与边界核；红证据不含新 API 缺失 E 或旧入口早拒 F。 |

### §3 Findings

**阻断：无。** 修复触及行上未发现 CLASS_1/2；`RED_LINE` 无（在线工具无真值/评分/几何导入，`test_loop2_isolation` 照绿；呈现路径与板输入围栏零 diff）；无 `上轮漏检`/`上游漏检`（新停点首轮）。不写 `blocks_consuming_gate`（状态板无 `Consuming=yes` 活跃行）。

CLASS_3（非阻断；不开轮）：
- **OSB-R1-1（CLASS_3，`BC-10`，对应 AC-10 修订 9；= PR-C10-1）**：`tools/eng_loop2/play_ops.py::release_gate` docstring 第二段「`ledger_hits`：1.5 账本命中项（正式 = 第 1.5 节两条；诊断 = SUB:3 签发条目与完整 request_id）。」陈旧——诊断实际传入 `DIAG_ENTRIES` 条目的 `(ledger_title, request_id)`。判据：该文字不驱动任何工具或操作员动作（函数体零改、参数由调用方给出、CLI/help/诊断页均指新条目）→ CLASS_3。逐字替换补丁（仅 docstring 一行；旧行 → 新行，均含四格缩进）：

  ```text
      `ledger_hits`：1.5 账本命中项（正式 = 第 1.5 节两条；诊断 = SUB:3 签发条目与完整 request_id）。
  →
      `ledger_hits`：1.5 账本命中项（正式 = 第 1.5 节两条；诊断 = 调用方传入的 `DIAG_ENTRIES` 条目标题片段与完整 request_id）。
  ```

  不改数字、判据或执行顺序。**应用时点由接受角色定**：`release_gate` 在「诊断绑定方案答复」§2 列为明确不改，本补丁只改文档串不改行为，可由实现角色在接受确认后于下一次提交应用，或并入下一停点；在此之前保持原文不影响本轮通过。

路由接受角色（观察，非 finding，不阻断）：
- 真实账本第 21 行存在围栏内 `## ` 行（目标条目之前）；当前不影响 `DIAG:RETRY:1` 条目解析（§1 边界核）。未来在该条目正文内写入含行首 `## ` 的围栏时会截断正文判定，接受写 `diag_release:` 实际行前按 BIND-3 已明示的「写标记前核清」自行核一次即可，不扩合同。
- `DIAG_RELEASE_LINE`（旧 `sub3_release` 正则）生产已无调用点，仅按 BIND-1「常量名与值不改」保留；不建议删除，不记债。

### §4 UNITY_NA 与人眼保真

- 候选未对任何 AC 申请 `UNITY_NA`；AC-14/15/18 与 AC-16 板端按交接 `NOT_RUN`，本轮无可附议项，也不签发任何 `UNITY_NA`。
- SUB:2（AC-11 修订 1）：`tools/eng_loop2/operator_web.py` 在 `539fd6d` 与 `c4973d0` 的 blob 同为 `13db5f119e0976b05db08cf5ff358ac70a2814a7`，板输入围栏块 8/8 字节相同 → R1@OpsK1K2K3K4 §4 的附议原样携带，本人两张一致记录可用于本候选，无须重看；提示行/用时仍 UNKNOWN。

### §5 限制、未验证与消耗

- 全套自动测试本轮未重跑，候选亦未跑全套（AC-13 修订 2 窄修替代，本角色判充分）；旧全套 16 项历史失败、两空目录归属、套件外预核用量 UNKNOWN 原样携带，不记全套通过。
- 真实 OpenSSH（含 `ssh -G`）/板/Unity 未实跑：BIND-3/4 只在临时 bare origin + 文档检出上验证，真实发布引用上 `release_gate` 当前必以 `play_governing_changed_after_pass`（PG 相对 `539fd6d` 非空）拒启，直到接受消费本轮通过并写出 `diag_release: P1-ENG-LOOP-002:DIAG:RETRY:1 <本轮 passed_candidate>` 实际行；该行、现场核、干净执行树、本人新窗口（`…:DIAG:RETRY:1:WINDOW`）均不由本轮签发。
- 守账承诺只限扫描域与旧 id 代码级硬拒（§18.5）；删除新账后不可恢复耗用事实，执行前由接受核。
- 消耗：零 `42979c14:SUB:1`/旧 SUB:1/2/3、零 `DIAG:RETRY:1`、零 SSH/板/Unity/Play/模型/回放/API/下载/装包/正式 ID。
- 边界自查：本会话未修改任何实现文件；修前红在会话暂存目录的导出副本内进行（已删除），复核副本 `git status --porcelain` 为空；主树只写本文件与 `docs/current-status.md`。

### Verdict（R1@OpsDiagBindK1K2）

**`PASS`**。全量 11 路径 diff 逐文件核对，3 个 PG 路径全读；AC-10 修订 9 / AC-13 修订 2 代码侧成立，修前红 35F/4E 由本角色在新测试树复算、修后绿 13/13 + focused 169 OK，板输入围栏 8/8 字节零改；无 CLASS_1/2、无 `RED_LINE`；1 条 CLASS_3 文字补丁（OSB-R1-1，`release_gate` docstring）应用时点交接受角色定。本停点返工计数 0/2。
passed_candidate: c4973d03e1db374c3b837e2ec7d0754a73eac378
通过只覆盖 `OpsDiagBindK1K2` 停点的代码与诊断页（含旧 Ops/K1K3/K1K2K3K4/OpsScoreDiagK1K4 已通过范围的携带）；不签发 `DIAG:RETRY:1` 放行、`diag_release:` 实际行、G1–G5/B-main 正式运行、AC-14/15/16/18 证据、`UNITY_NA` 或 `DONE`。下一动作：接受角色消费本轮通过（按 BIND-4 从本文件机读行运行时解析、程序写入 `diag_release:` 实际行；现场核与本人新窗口按其合同与信封另裁）。
