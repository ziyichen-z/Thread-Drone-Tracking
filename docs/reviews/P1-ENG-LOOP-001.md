# P1-ENG-LOOP-001 — 独立复核（engineering-v1）

Reviewer/role: 复核角色 / independent verification（新鲜上下文会话，Fable 池；档位不低于实现者）
Workflow: engineering-v1（提案抬头第 3 行逐字 `Workflow: engineering-v1`；接受角色 2026-09-19 D4
`ACCEPTED` 时逐字裁定「engineering-v1 在本工作项生效」；本轮按 `docs/engineering-workflow.md` §5/§6
与 `docs/roles/review.md`「工程轨道」节执行，依据列沿用 workflow §4.4 六值闭集，`BC-n` 读作合同 `AC-n`）
Round: R1@K1K3
Date: 2026-09-20
Implementation snapshot: 候选 = 状态板 Active handoffs 行「C1@K1K3 核对已通过，执行独立复核 R1@K1K3」
所指的交接提交（实现批次最后一个提交，从 git 解析：主题「P1-ENG-LOOP-001 D4 finalize K1K3 stage-A
candidate and live K binding」，其父 = manifest `head_before_candidate_commit` `cdf8112…`）。其后两笔提交
（COORD-012 文档、`C1@K1K3` 核对）与候选只在 `docs/authorizations.md`、`docs/current-status.md`、提案三个
文档文件重叠，实现文件零重叠。本 work ID 无上一通过候选；全量 diff 基线 = manifest
`baseline_before_first_runtime_file` `40229e6d…`：96 文件 +28,906/−14，其中实现文件 12 个——
`controller/{language_bridge,gated_publisher,language_selector,language_loop,language_demo}.py`
（1,257/567/830/2,654/494 行）、`tools/{language_serve,language_latency}.py`（300/623 行）、
`tools/requirements-language.txt`、`tests/test_language_{bridge,selector,loop,k_binding}.py`
（796/1,263/3,232/156 行）；另 `runtime/README.md`（+25）、`.gitignore`（+3）、78 份
`docs/evidence/P1-ENG-LOOP-001-*` 与四份他角色文档。
round_candidate: 3fe929a21fa0c81f1db044ab5cd4775a7e5a69b4
Verdict: REWORK_REQUIRED

## 0. 复核范围与停点

- **轨道判定**：提案抬头逐字 `Workflow: engineering-v1`，决策记录 D4 行逐字「`ACCEPTED`；engineering-v1
  生效」→ 工程轨道。停点 = 提案 §7 合并停点 `K1K3`（K1：桥文件、检查点与拒收、静音播种、最终门与收据、
  停帧/坏元数据映射、状态镜像、K 收据 → AC-1…4/10/11；K3：三态→确认→播种、有界重试、重指定与谱系、
  核验语义、worker 与请求生命周期、模型身份与后端、等价 → AC-5…9/12/16/17）。合同 = §1…8、AC-1…17、
  八行首次接受释义、十行实现期修订（P-A-1…8、P-B-1/2），冲突处以后者为准。
- **复核对象来源**：状态板交接行与提案「Contract conformance」C1@K1K3 核对表（AC-1…12/16/17 满足、
  AC-13…15 未到时点、关注项 C1-1…5）。核对表、K1K3-handoff、实现报告与实测报告只作待核实主张。
- **开轮资格（COORD-007 R1）**：`git diff 40229e6..3fe929a` 在 PLAY_GOVERNING 上非空（五个 `controller/`
  新模块、两个 `tools/` 新模块、requirements、四份 `tests/`）→ 开轮。Play 治理门文件
  （`tools/analyze_m3_body.py`、`tools/preflight_reanchor_env.py`、`controller/run_log.py`）零改动，无闭环轮义务。
  冻结边界（`Assets/`、`config/`、`tools/eng_sft/`、`controller/{protocol,tracking_entry,track_loop}.py`、
  `ProjectSettings/`、`Packages/packages-lock.json`）`git diff --stat` 为空，与 manifest
  `frozen_changed_paths=[]` 一致。本停点无消耗性交接（`Consuming=no`），无 `blocks_consuming_gate` 行。
- **停点自证核实（workflow §4.3.1 四项）**：条件 1（范围/接口冻结：合同十行修订后无新 AC、桥闭集与
  合同逐字相符，见 §1）、条件 2（相称测试：停点全套 `tests.log` `Ran 1504 / FAILED (errors=9, skipped=24)`，
  9 个 ERROR 与 `docs/evidence/P1-ENG-SFT-002-tests.log` 的 9 个同名、同因（系统解释器缺 `cv2`），本批新增
  失败 0；本轮 focused 重跑见下）、条件 3（阶段 A 零 Unity，无本批 Unity 失败；K 绑定缺口已在候选内修复并
  红绿）、条件 4（状态板/交接/候选/风险已更新；候选 `3fe929a` 是本地 `origin/main` 的祖先，已推送）
  按字面成立 → **开轮，不给 `REVIEW_BLOCKED`**。
- **副本**：`git worktree add --detach .claude/worktrees/review-P1-ENG-LOOP-001 3fe929a…`；读码、重跑、探针
  全部在副本内；主树对实现文件只读；收工删除副本。副本无 git 忽略的 `outputs/`，故对 SFT-002 冻结资产
  的两项测试改以一条指向主树 `outputs/` 的只读符号链接补跑（不写主树、不改资产）。
- **重跑（不信报告数字；测试树哈希 `HEAD:tests` = `0b659bae392ac8f40e8e9d26efd7bf85051ea06f`，
  `HEAD:controller` = `ce48e17b6f029f7f559c2dd5009235bbc211f4c9`，`HEAD:tools` = `630bc37a1e20dbcd9b6a014589feaa0cc54161c9`）**：
  - `.venv-language/bin/python -m unittest tests.test_language_bridge tests.test_language_selector
    tests.test_language_loop tests.test_language_k_binding` → `Ran 257 … OK (skipped=2)`；两项 skip 均为
    「SFT-002 冻结资产不在本机」（`FrozenReplayAssetTests`、`ReplayDemoTests`，原因是副本无 `outputs/`）。
    经只读链接补跑这两项 → `Ran 2 … OK`，零 skip。合计 257/257 实际执行通过，含 `PreviewRenderTests` 两项
    真实 Pillow 逐像素用例与 `test_language_k_binding` 13 项。
  - 系统 `python3`（3.14.6，无 Pillow）同四模块 → `Ran 257 … OK (skipped=4)`（上述两项 + 两项无 Pillow
    跳过；与实现者 `tests.log` 的「新增 3 项 skip」口径一致：停点全套里多一项属 `ReplayDemoTests` 的
    Pillow 门）。
  - AC-10 修订 1 K 绑定修复的修前红/修后绿：副本内把 `controller/language_loop.py`、
    `controller/language_selector.py`、`tools/language_serve.py` 检出到父提交 `cdf8112…`（修前源码）后跑
    `tests.test_language_k_binding` → 13 项中 4 E + 8 F + 1 通过后进程在第 14 个结果处**挂起**（修前
    `HttpAdapter` 无 `bind_identity`/身份回包核对，回环服务用例等待不返回；实现者的
    `tests-k-binding-before.log` 也只跑了 1 项即失败），本角色 kill 进程并 `git checkout HEAD --` 恢复三文件，
    `git status --porcelain` 干净；恢复后同套件 `Ran 13 … OK`。修前确实转红、修后全绿。
  - 输出全部写会话 scratchpad（`focused-venv-language.log`、`focused-py314.log`、`focused-frozen-assets.log`、
    `kbinding-red.log`、`kbinding-green.log`），上下文只回显摘要，不带 `-v`（只为定位 skip 名另跑了一次
    `-v` 到文件，不回显）。
- **证据复算（标准库，无模型、零查询、零下载）**：
  - `latency-mac.json`：一轮 `OK`，3 预热 + 32 计时、失败 0；升序第 31 个样本重算 p95 = 8.7562978750002 s
    = 报告值；`k_ret = ceil(8.756×5)+2 = 46`、`k_conf = 50`、`46+50+2 = 98 ≤ 120` 合格、p95 > 6.0 → B。
  - `latency-5060.json`：一轮 `OK`，同口径；p95 重算 = 5.429160666999451 s = 报告值；`k_ret = 30`、
    `30+50+2 = 82 ≤ 120`、p95 ≤ 6.0 → A；`transport.endpoint` `http://100.100.100.100:8760`。
  - `k-receipt.json`：决策 `5060`/`gpu_tier_a`、backend `http`、形态 `c2-adapter`、hz 5/R 128、K 30/50/2、
    `t_ret_s` 6.0、`t_pub_s` 0.4；`source_reports` 两份报告路径的 sha256 与主树/副本文件现算逐字节相符；
    `model_identity` 八字段与 5060 报告一致（`weights_sha256 4044dd4f…` = SFT-002 C2 adapter）。
  - `merge-equivalence.json`：32 行、`equivalent=false`、选 `c2-adapter`、执行顺序 merged→adapter；
    不等价 2 行（`s-5a455675e4a36073` `unique_iou`、`s-db144c39f7b3db1a` `ambiguous_match`）；用候选的
    `interpret`+`selections_equivalent` 从 64 条 `raw_records` 重算，结果**逐行相同**。
  - 信封账本：Mac `merges 2 / model_loads 3 / query_rows 35 / base_downloads 1`；5060 ledger 141 条事件
    计数器最大值 `merges 1 / model_loads 6 / query_rows 134`（等价 64 + 修前 35 + 修后 35），
    `cleanup-5060.json` 监听 0、残留服务 0；均在阶段 A 信封内（Mac ≤2/≤6/≤70/1；5060 ≤2/≤6/≤134），
    5060 启动与查询恰好耗尽。
  - `live-binding-5060.json`：`verified=true`、收据 sha = `k-receipt.json` 现算、匹配身份可构造 `IDLE`、
    换权重 → `worker_stuck`/`MODEL_IDENTITY_MISMATCH`/`fatal`，两次 `GET /status`、`model_queries 0`、
    共享 runtime 零写入；`k-binding-diagnostic.json`（修前 `changed_weights_rejected=false`）与
    `k-binding-after.json`（修后 `true`）对照保留。
  - `pip-check-{mac,5060}.log` 均 `No broken requirements found`；`requirements-language.txt` 九个钉版与
    `tools/requirements-eng-sft.txt` 逐行同版，唯一差异是 torch/torchvision 去掉 `+cu128` 后缀，与文件内
    声明一致。
- **直接关联冻结代码**（只读）：`track_loop.py` 的 `FrameRepository.{latest_frame_id,load}`（`image_loader`
  注入点、`validate_system_monotonic_frame`）、`RuntimePublisher`、`TrackLoop.{initialize,process_available,
  _publish_latest,_append_record,_record_terminal_error}`（先整批 `load` 再逐帧 `update`、只在批末
  `_publish_latest`、`ValueError` 在无 rate lifecycle 时直接抛出、`GAP`/`REINIT_REQUIRED` 终止事件）、
  `sensor_protocol.validate_system_monotonic_frame`、`run_log.RunLogger.__init__/finalize`
  （`<runtime>/runs/<run_id>` 且 `exist_ok=False`）、`protocol.packet`（`command_id = time.time_ns()`）。

## 1. 逐条 AC 核对（本角色独立结论；核对表只作主张）

| 编号 | 结论 | 本轮核实（代码 → 测试 → 证据） |
|---|---|---|
| AC-1（含修订 1） | **不满足（F1、F2）** | 三桥 schema/闭集/可空规则与原子发布在 `language_bridge.py` 强制，读写两侧 fail-closed；九 action、七 outcome、九 status、十三 reject_reason、八态、二十一 reason、五 verdict、四 inconclusive_reason、三 skip、五 pairing_unavailable 闭集与合同逐字相符；写者锁 O_EXCL/`WRITER_BUSY`/持有者释放、会话锁 `SESSION_SLOT_BUSY`/死锁替换有具名测试；`runtime/README.md` 三条目与 `confidence_source` 未校准声明在案。**但**修订 1「死写者锁清理并记日志」无生产落点（F1），§3.2(a)「已消费的 id 再现 → `IGNORED_DUPLICATE`」在会话内不可达、同 ID 重试在有中间请求后拿不到任何回执（F2）。 |
| AC-2（含修订 1） | 满足 | `_acquire_frame`（查询检查点：`latest` 不可读/缺成员/元数据非法/同 ID 换图四个出口）、`_check_return`（帧差 → 墙钟含停帧 → `verify_frame_identity` 身份重核）、`_check_confirmation`（累计帧差 `K_ret+K_conf`、累计截止 `T_ret+T_conf`、呈现窗口 `0≤now−首次呈现≤T_conf`、身份重核）共用同一不可变 `QuerySnapshot`；`StaleRejectionTests` 10 条每例断言三桥文件内容未写入且收据为空，本轮实际执行。 |
| AC-3（含修订 1/2） | 满足 | `FrameSnapshotRing.image_loader` 只读一次字节、复制入帧环、记两种加载时刻；`SnapshotRepository.load` 在 bundle 交给跟踪器前 `bind` 该次 load 的完整元数据，重复加载不覆盖信任根、哈希/元数据不等即 `FrameIdentityChanged`；`GatedPublisher._gate` 五项（关联帧=最近加载、盘上 JPEG 哈希、元数据完整值、`latest` 帧差 `0≤L_w−f≤K_pub`、`0≤now−load≤T_pub` 与 `0≤unix−capture≤T_stall`、未来采集时刻 → `metadata_invalid`）；静音期观测/云台 `MUTED_DROPPED`、`hold_body`/`set_nadir` 透传；`_derived` 无关联 → `orphan_control`；拒绝不倒改已 `WRITTEN` 收据、不推进 `last_published_frame_id`、`finalize` 后零新增；`_advance_segment` 把 `ValueError`→`metadata_invalid`、`FileNotFoundError`→`bundle_missing`、`FrameIdentityChanged`→同名、`fatal_reason`→同名、`T_stall` 无进展→`frame_stall`。`GatedSeedingTests`/`PublishGateTests`/`CatchUpTests` 覆盖六个出口与批末发布，均执行。 |
| AC-4（含修订 1/2） | 满足（离线半边） | `raw_lost = any(not ok)` 取批内逐帧记录（`RecordingRunLogger` 在记录写入后登记）；`_tracker_raw_state` 镜像批末 `loop.state`；`sequence` 单调；`SUSPECTED` 只由人/段终止离开；未映射终端事件 `_terminal_reason` 逐字记 `unexpected_segment_end` 并按 `metadata_invalid` 终止、已知 `GAP`/`REINIT_REQUIRED` 不被兜底覆盖；`StateMirrorTests` 7 条执行，`test_frozen_paths_are_untouched_in_the_working_tree` 机检 + 本轮 `git diff` 为空。Play 半边随 AC-13 待阶段 B。 |
| AC-5（含修订 1） | 满足（离线证据） | `unique`/`ambiguous` 均停 `AWAITING_CONFIRMATION`；token/epoch/index 非法只 `REQUEST_INVALID`；`candidate_preview_path is None` → 确认 `REQUEST_INVALID` 且零副作用（注入失败渲染器与 `OSError` 两条用例，不挂 skip）；预览绑定帧环副本、index 一一对应；`PreviewRenderTests` 两项真实 Pillow 逐像素用例在 `.venv-language` 实际执行通过。 |
| AC-6（含修订 1） | 满足 | `_designate_failure` 五类失败共用：`attempt` 严格递增至 `attempt_limit`、超限 `retry_exhausted` 带 `last_status`/`last_reject_reason` 并按有无过段落 `REINIT_REQUIRED`/`IDLE`；取帧前失败也分配 `query_id`（`_emit_result` 无 job 时铸号）、四个帧字段 null、`query_unix_s` 记尝试时刻；帧递增下界只由取得帧的尝试抬高；`worker.calls_started` 只在 `_start` 计数并写 `query_started`。`BoundedRetryTests` 8 条、`AmbiguousTests` 执行。 |
| AC-7 | 满足 | `LOST`/`REINIT_REQUIRED`/`SUSPECTED` 的 `respecify` 开新段（`track_id` 递增）；`_finalize_segment` 追加 `retired_track_ids` 恰一次（GAP/release/confirm_lost 三路径参数化）；`TRACKING` 下拒绝；缺省沿用 `confirmed_instruction or current_instruction`，无可沿用 → `REQUEST_INVALID`。 |
| AC-8（含修订 1/2） | 满足（另见 F3 非阻断） | `HttpAdapter`：每次 I/O `min(5 s, 剩余)`、总截止锚在原提交时刻、`awaiting_idle` 前不重入、迟到 idle 先核截止再清零、`health_check` 使不再 ask 也到期、`SERVER_BUSY`/`SERVER_STUCK` 不排队、`T_ret` 到期放弃且不接纳该 `query_id`；服务端 `SingleFlightRuntime` 模型真正结束才离开 busy、stuck 后拒单直到重启、每回包带身份；`worker_died` 限于 `predict_one` 边界的普通异常并保留类型与消息；在途帧 `pin`/`unpin`。`HttpAdapterTests` 21 条（真实回环 `HTTPServer`）、loop 侧 `test_a_timeout_while_the_server_is_busy_never_re_enters_it` 执行；`FrozenContractTests` 读源断言观测协议常量与 `confidence_source` 闭集不变，`git diff` 为空。 |
| AC-9 | 满足 | `ReplayAdapter` 键 `(sha(frame), surface, g4)`、按 `row_id` 连接、两份 sha 核对、索引带 gold 即拒、`replay_miss`/`replay_conflict`/重复键取最小 `row_id`；`FrozenReplayAssetTests` 与 `ReplayDemoTests` 对真实 609 行冻结资产在本轮实际执行通过（走查覆盖 designate 五状态与 verify 五 verdict、两段谱系、零 `PUBLISH_REJECTED`）；等价 2/32 不等价从原始输出重算相同，依 §3.5 回退 `c2-adapter` 并以该形态实测。 |
| AC-10（含修订 1） | 满足 | 规则常数与合同逐字（`HostDecisionTests.test_frozen_constants`）；`host_tier`/`decide_host` 先资格后分档、平局取 Mac、双不合格 `HOST_UNDECIDED`；两机报告 p95/K 重算相符；`KReceipt.from_document` 自洽核对、`validate_measurement_sources` 绑定两份源报告 SHA、宿主决策重算、backend/形态/身份/hz/R/p95 逐项比对；`LanguageSession.__init__` 再核 adapter 身份、HTTP 端点与 `bind_identity` 真实握手；13 项 `test_language_k_binding` 修前红/修后绿由本角色复现（§0）；真实服务正反验证在案。 |
| AC-11 | 满足 | 停点全套 `tests.log` 1504/0 failures/9 errors/24 skips，9 个 ERROR 与 SFT-002 基线同名同因，新增失败 0；本轮 focused 257/257 执行通过（§0）。 |
| AC-12（含修订 1/2） | 满足 | 钉版与 SFT-002 同版（平台轮子差异已声明）；两机 `pip check` 干净；`operations.md` 阶段 A 不使用 `--allow-shared-runtime`（第 26 行明示）；`resolves_to_shared_runtime` 只 stat 不写、`resolve()`+`st_dev/st_ino` 双判；`run` 与九个操作者子命令共用守卫，拒绝前零写入（`DiagnosticSessionTests` 8 条执行，含符号链接/相对路径/`..` 别名）；诊断会话 `diag-` 前缀、`RunLogger` 根指向诊断根。报告 §10 第 10 条如实披露子目录穿过守卫，与修订 2「解析到 runtime 根」措辞一致。 |
| AC-13/14/15 | 未到证据时点 | 阶段 B 未授权；候选未产生也未冒充 Play 证据；不申请 `UNITY_NA`（见文末附议节）。 |
| AC-16（含修订 1/2/3） | 满足 | 配对帧 = `_latest_record()`（本段最近已处理帧，非 latest）；同帧/无框/滞后三种发起前跳过只写 `verify_skipped`；配对帧快照缺失/身份失败/latest 不可读写 `verify_pairing_unavailable` 五值闭集并带 `P.frame_id`；核验走同一条 `_check_return`，`VERIFY_RETURN_INCONCLUSIVE` 六值映射按返回值取、`verdict` 字面恒 `inconclusive`；五 verdict 与单计数器（none/drift 交替累计、ambiguous 立即疑似、inconclusive 不改计数不解除疑似）；`dismiss`/`confirm_lost`/新段/`stop` 使 `verify_epoch+1`，旧回包按三键丢弃；核验从不 `initialize`/写桥；`due` 重排、同源 3 s 限频。`VerifyTests` 31 条执行。 |
| AC-17（含修订 1） | 满足 | `StateTableTests.test_every_cell` 参数化覆盖八态 × 未列动作 → `REQUEST_INVALID` 且状态/epoch/候选不变；`TERMINAL` 一律 `IGNORED_TERMINAL`；pending 至多一条、`SUPERSEDED` 回执；`T_hard` → `worker_stuck` → `REINIT_REQUIRED(backend_fatal)` 且此后只许 `stop`/读状态（designate/verify 两路径、旧世代回包不吞终止、adapter 自报 stuck 不派发 pending）；`stop` join ≤ `WORKER_JOIN_S` 并对 stranded 线程记 `worker_abandoned`（真实线程正反两例）；写者锁并发 → `WRITER_BUSY`。`WorkerTests` 19 条执行。 |

## 2. 读过的文件与测试

副本内全文读取：`controller/gated_publisher.py`、`controller/language_bridge.py`、`controller/language_selector.py`、
`controller/language_loop.py`、`controller/language_demo.py`、`tools/language_serve.py`、`tools/language_latency.py`、
`tools/requirements-language.txt`、`tests/test_language_loop.py`、`tests/test_language_k_binding.py`；
`tests/test_language_bridge.py` 与 `tests/test_language_selector.py` 读用例清单与锁/回环服务/冻结资产段；
`runtime/README.md` 与 `.gitignore` 的候选 diff；上列直接关联冻结代码。证据：K1K3-handoff 全文、实现报告
§10/§11、实测报告 §5/§6/§8、`operations.md` 章节与守卫/环境行、上列 JSON/日志。合同：提案全文
（§0…8、AC 表、首次释义、Pending rulings、Contract conformance、决策记录）、正式设计 §1 候选 diff。

## 3. Findings

### Blocking

**F1 — AC-1 修订 1「死写者锁在确认 pid 已死后清理并记日志」无生产落点。** CLASS_2 · 依据列 `BC-1`
（读作 AC-1 修订 1）· 范围判据：可达——生产入口 CLI（`python3 -m controller.language_loop <action> …` →
`send_request` → `bridge.acquire_writer_lock`）；触发状态 = 上一个 CLI 在建锁后、删锁前被终止（Ctrl-C /
kill）留下死锁，下一条 CLI 接管。
- 位置：`controller/language_bridge.py` `acquire_writer_lock`（`FileExistsError` 后 `not is_alive(existing.pid)`
  分支 `unlink` 并重建，只返回新持有者，不返回也不记录被清理的持有者）；`controller/language_loop.py`
  `send_request`（只调 `acquire_writer_lock`，无任何输出/日志）。`clear_dead_writer_lock`（返回被清理持有者
  「供日志记录」）只被 `tests/test_language_bridge.py` 调用，生产链路不经过它。
- 问题：合同要求清理**并记日志**；候选清理了但无处记录，操作者与证据链都看不到「锁被接管」这一事实
  （`operations.md` 与会话 JSONL 都无落点）。`WriterLockTests.test_acquire_takes_over_a_dead_lock` 只断言
  接管成功，不断言记录。
- 闭合要求（workflow §4.4 四条）：(1) 生产路径 fixture——用 `bridge.acquire_writer_lock(..., pid=<已死 pid>)`
  真实建死锁后走 `send_request`（或 CLI `main`），禁止手写锁文件；(2) 具名回归测试修前必红，例如
  `RequestLifecycleTests.test_a_dead_writer_lock_is_reclaimed_and_reported_by_the_cli`：断言 CLI 输出/返回
  字典（或 stderr）含被清理的 pid/request_id/创建时间，且锁被本次请求持有；(3) 不触及 Play 治理门；
  (4) 可机械断言。实现建议（不构成义务）：让 `acquire_writer_lock` 像 `acquire_session_lock` 一样返回
  `(holder, replaced)`，`send_request` 把 `replaced` 写进返回字典并打印一行；只改 `language_bridge.py`/
  `language_loop.py`/测试，不改任何闭集。

**F2 — §3.2(a)「已消费的 id 再现 → `IGNORED_DUPLICATE`」在会话内不可达；同 ID 重试在有中间请求后拿不到回执。**
CLASS_2 · 依据列 `BC-1`（读作 AC-1「outcome 七值闭集逐一枚举」+ §3.2(a) 表 + AC-1 修订 1「同 ID 重试由会话
去重」与 CLI 文案「重试请用同一个 --request-id」）· 范围判据：可达——生产入口 CLI：请求 A 被会话消费
（`APPLIED`）→ 操作者的 CLI 因 5 s 内未见回执报「结果未知」并删锁（例如会话正在追平一批帧、tick 延迟）→
另一条请求 B 被消费（`last_request` 变为 B）→ 操作者按文案用同一 `--request-id` 重发 A。
- 位置：`controller/language_loop.py` `_consume_request`：`if envelope.request_id in self.consumed_requests: return`
  静默返回，全文件无任何 `IGNORED_DUPLICATE` 产出；`tests/test_language_loop.py`
  `RequestLifecycleTests.test_exactly_once_and_duplicate_id` 只断言 epoch 不变且 `last_request` 仍是原回执，
  钉住的是静默行为。
- 问题：合同把该 outcome 列为可达回执；候选下上述路径的 CLI 只能再次超时报「结果未知」，操作者无法从
  桥文件得知 A 早已执行。去重本身（不再执行第二次）正确，缺的是回执。注意合同不可能要求对**同一份**槽内
  残留内容每 20 ms 重复回执——候选每 tick 重读槽文件并靠 `consumed_requests` 去重是必要的；因此修复须区分
  「槽内残留」与「同 ID 被**重新写入**」：`read_request` 已带 `command_id`（`protocol.packet` 取
  `time.time_ns()`，每次 `write_request` 必然不同）与 `issued_unix_s`，会话在消费时记住该请求的
  `command_id`，再见同 `request_id` 而 `command_id` 变化即一次真实再现 → 回执 `IGNORED_DUPLICATE`
  恰一次（之后同 `command_id` 的重读仍静默）。
- 闭合要求：(1) fixture 经 `bridge.write_request`（第二次写入用新的 `packet`）而非手写 JSON；(2) 具名回归
  修前必红，例如 `RequestLifecycleTests.test_a_rewritten_duplicate_id_gets_an_ignored_duplicate_receipt`：
  A `APPLIED` → B `APPLIED` → 重写 A → `last_request == {request_id: A, outcome: IGNORED_DUPLICATE}`、
  epoch/状态/候选不变、`worker.calls_started` 不变、会话 JSONL 恰一条该回执；并保留一条用例钉住
  「槽内残留重读不产生回执」（现 `test_exactly_once_and_duplicate_id` 可改为断言无新 receipt 行）；
  (3) 不触及 Play 治理门；(4) 可机械断言。桥闭集不动（`OUTCOMES` 已含该值）。
- 分级说明：本角色裁定为实现与合同字面不符的失败路径（CLASS_2）；若实现或接受角色认为「静默去重 +
  `last_request` 快照」是合同可接受的读法，按 workflow §4.4 提分级争议交接受角色复判，不由实现自行解释。

### Non-blocking

**F3 — pending 任务的 `T_hard` 从任务创建时刻而非开始在途时刻起算。** CLASS_2 · 依据列 `SCOPE_GAP`
（不可达，非阻断，路由接受角色）· 位置：`controller/language_loop.py` `LanguageWorker.poll`
（`elapsed = now − self._in_flight.submitted_monotonic_s`），`submitted_monotonic_s` 在 `_submit_query` 建
`QueryJob` 时记录；`PENDING_QUEUED` 的任务在 `poll()` 里 `_start` 时**不重记**。
- 后果：在途 A 耗时 D_A、B 在 A 在途期间排队并在 A 结束后启动，若 `D_A + D_B > T_hard`（60 s）则 B 在
  真正在途不足 60 s 时即被记 `worker_stuck` → `REINIT_REQUIRED(backend_fatal)`、要求重启进程——误判为
  后端卡死。§3.4「在途有界…超硬限记 `worker_stuck`」与 AC-8 修订 1「从首次提交起…≤T_hard」都以在途/提交
  为起点，排队等待不应计入。
- 不可达判据：两机实测 p95 8.76 s / 5.43 s、SFT-002 事实 11 的单次 max 16.97 s；两次调用相加 < 60 s，
  信封内测得的时延无法触发；只有单次调用本身接近 T_hard 时才可能，此时 A 自己已近 stuck。
  （B 的 `wall_deadline_exceeded`/`frames_late_exceeded` 以创建时刻起算是**正确**的——帧 N 确在变旧。）
- 建议处置：接受角色记 `SCOPE_GAP` 入 `docs/implementation-status.md` 账本，或在下一次触及 `LanguageWorker`
  时把 `_start` 处的在途起点单独记录（不改 `QueryJob.submitted_monotonic_s` 的检查点语义）。

## 4. 非阻断注记（不是 finding，不带依据列；供接受角色、实现角色与阶段 B 决策参考）

1. **C1-3（`_submit_query` 的防御性 `raise`）**：`worker.submit` 只在 `self.stuck` 时抛；两个调用方
   （`_issue_designate`、`_request_verification`）都先查 `worker.stuck`，该分支现行不可达。若日后可达，
   异常会逃出 `tick()` 使 `run()` 退出而会话未 `TERMINAL`（违反 AC-17 修订 1 意图）。建议改为记 JSONL 后
   `return None`/让调用方处理，不作 finding。
2. **C1-4（inconclusive 也把配对帧记为已核验）**：`_handle_verify_outcome` 对任何非 stale 回包都置
   `last_verified_frame_id = P`。与 §3.6「`P.frame_id > 上一次核验的配对帧`」及 AC-13 修订 1「F_out 只取
   实际完成的不同配对帧核验」「截止前同帧跳过不作一次完成」一致：inconclusive 是一次已完成、有结果行的
   核验。正常 5 Hz 供帧下下一次核验自然配到新帧，停帧时段 3 s 内即 `frame_stall`。**裁定：不构成 finding**；
   接受角色若希望 inconclusive 不消耗配对帧，须以 Pending ruling 明示。
3. **C1-5（阶段 B 客户端解释器组合）**：K 选 5060/http 后，Mac 上的会话进程同时需要 `cv2`
   （`load_cv_image`）、NanoTrack-v2 依赖（`.venv-track`）、Pillow（预览门）与标准库 HTTP 客户端；
   `requirements-language.txt` 只覆盖模型侧。操作单 C 须写明该解释器组合并实测 `pip check`。不是本候选缺陷。
4. **帧环副本在身份核对前被覆盖**：`FrameSnapshotRing.image_loader` 先 `copy_path.write_bytes(payload)` 再由
   `bind` 比对既有快照的 sha。同一 `frame_id` 二次加载且字节不同（同 ID 换图）时会抛 `FrameIdentityChanged`
   而副本已被换成新字节，信任根 `copy_path` 的内容 ≠ `image_sha256`。二次加载只发生在 `initialize(N)`
   （无在途查询指向 N）与停帧下重复 `_acquire_frame`（同样立即拒绝），候选下无功能后果；但模块 docstring
   「副本哈希 = 快照哈希，由构造保证」在该失败路径上不成立。建议在 `bind` 比对通过前不覆盖既有副本
   （先比对 `digest` 再写）。
5. **`due` 触发跳过时不推进 `next_due`**：`_request_verification("due")` 只在成功提交后重排 `next_due`；
   `_pairing_frame()` 返回 None（同帧/无框/滞后/配对不可用）时 `_maybe_verify` 每 tick（20 ms）重试并各写
   一行 `verify_skipped`/`verify_pairing_unavailable`。功能无碍（跳过本就应重试），只是这些窗口内会话 JSONL
   有短促重复行；阶段 B 分析日志时须知。
6. **阶段 B 前置风险（合同字面实现，非缺陷，提请用户与接受角色在签发 B 信封前知悉）**：发布最终门 ④
   `0≤L_w−frame_id≤K_pub(2)` 与 ⑤ `now−加载时刻≤T_pub(0.4 s)` 合起来要求**整个追平批的末帧从加载到写桥
   不超过 0.4 s**，且批末帧与真实 latest 相差 ≤2 帧。冻结 `TrackLoop.process_available` 先整批 `load` 再逐帧
   `update`，末帧的加载时刻在所有 `update` 之前，所以 ⑤ 的 0.4 s 要容纳整批 `update` 之和。确认后首批追平 =
   模型时延（5060 K_ret 30 帧）+ 人工确认（最多 K_conf 50 帧）≈ 80 帧，即每帧解码+`update` 须 ≤ 5 ms
   （NanoTrack-v2 在 Mac 上的每帧时延本轮未测）。若超出，段在首批追平即 `publish_expired`/`catchup_stale`
   → `REINIT_REQUIRED`，AC-13 的「`TRACKING` ≥ 25 帧且有 `WRITTEN`」将难以达成。AC-10 修订 1 已明写
   「资格仅证明模型时延与保留窗预算相容，不证明追平耗时合格」，故不是本停点缺陷；建议阶段 B 先用诊断
   会话（`--diagnostic`，零正式 ID）测一次确认后首批追平的 `load_elapsed_s`/`frame_delta`（收据 `detail`
   已带这两个字段）再动用正式 Play 额度。
7. **取帧前失败的重试在同一 tick 内耗尽**：`bundle_missing`/`metadata_invalid` 未取得帧时 `_retry_min_frame_id`
   不抬高、无等待，三次尝试在一个 tick 内连发并 `retry_exhausted`。与 AC-6 修订 1 字面一致（帧递增只约束
   取得帧的尝试），如实记下供操作者理解 `results.jsonl` 里毫秒级的三行。
8. **`ILLEGAL_WRITER_SUSPECTED` 会命中合法的迟到消费**：CLI 5 s 超时删锁后请求仍在槽内，会话稍后消费时
   锁已不存在 → 记 `ILLEGAL_WRITER_SUSPECTED`。与 §3.2「观察到 `request_id` 变化而锁文件缺失时另记」字面
   一致（名字本就是「疑似」），阶段 B 读日志时勿当成越权写者证据。
9. 测试脚手架的真实性：`Harness` 用 `FixtureFramePublisher` 真实写 v3 帧包与原子指针、`SnapshotRepository`
   + `GatedPublisher` + `RecordingRunLogger` + 冻结 `TrackLoop` + 闭集内 `scripted` 跟踪器；`PublishGateTests`
   以包装 `_gate` 在加载后/写桥前改盘上字节制造六个出口，属生产路径 fixture；`StateMirrorTests`
   `_force_terminal_record` 经 `RecordingRunLogger.append` 驱动兜底路径，符合 AC-4 修订 2「无需启用…来演练」。
   HTTP 用例用真实回环 `HTTPServer`。未发现「测试挡不住回退」的空断言。

## 5. 交回实现角色的动作（`REWORK_REQUIRED`，修复直接回本角色 R2@K1K3，不经核对轮）

1. [实现] F1：`acquire_writer_lock` 返回被清理的死锁持有者并由 `send_request`/CLI 记录（输出与返回字典），
   补具名回归（修前红）。
2. [实现] F2：`_consume_request` 以 `command_id`（或 `issued_unix_s`）区分槽内残留重读与同 ID 重新写入，
   后者回执 `IGNORED_DUPLICATE` 恰一次；改写 `test_exactly_once_and_duplicate_id` 并新增重写用例（修前红）。
3. [实现] 两项修复只触及 `controller/language_bridge.py`、`controller/language_loop.py`、
   `tests/test_language_{bridge,loop}.py`；不改任何闭集常量、不改 `tools/`、不触及 Play 治理门文件、不改
   证据 JSON。修后 focused 一次 + 全套一次写 `docs/evidence/`，提交/推送后更新状态板交接行交 R2@K1K3。
4. [接受] F3 `SCOPE_GAP` 记债或裁定；注记 2 若要改口径写 Pending ruling；注记 6 在阶段 B 信封决策前评估。
5. 第 2 轮新阻断只来自修复触及行（相对本轮 `round_candidate`）上的 CLASS_1/2、F1/F2 闭合失败、`RED_LINE`
   与未改动行上的 `上轮漏检` CLASS_1；全量 diff 仍做，只用于核实范围与红绿。

## `UNITY_NA` 附议

本工作项**不申请** `UNITY_NA`（提案 §4「AC-13…15 是 DONE 所需的 Unity 证据，本项不申请 UNITY_NA」；
Gate board 行同）。本轮无附议对象，不附议、不反对；AC-13…15 仍是 `DONE` 的必要证据，须待独立复核通过且用户
另行签发阶段 B 信封后由真实 Play 产生。

## 6. 边界自查（R1@K1K3 收工）

- 本会话未修改任何实现文件：`controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零改动。副本内为复现修前红
  曾把三份实现文件检出到父提交，随后 `git checkout HEAD --` 恢复，副本 `git status --porcelain` 干净后删除；
  副本内为补跑两项测试建立的 `outputs` 只读符号链接随副本删除，主树 `outputs/` 未写入。
- 主树本批写入：`docs/reviews/P1-ENG-LOOP-001.md`（本文件）与 `docs/current-status.md`；
  `python3 tools/check_role_writes.py --role review` 与 `python3 tools/check_docs.py` 结果记在状态板 Log。
- 零消耗：未启动模型/服务/Play、未下载、未创建 scenario/session/run ID、未触碰真实 `runtime/`。

---

# R2@K1K3 — 增量轮：复核 R1@K1K3 F1/F2 修复

Reviewer/role: 复核角色 / independent verification（新鲜上下文会话，Fable 池；档位不低于实现者）
Workflow: engineering-v1（同 R1；依据列沿用 workflow §4.4 六值闭集，`BC-n` 读作合同 `AC-n`）
Round: R2@K1K3
Date: 2026-09-21
Implementation snapshot: 候选 = 首次加入 `docs/evidence/P1-ENG-LOOP-001-K1K3-r1-fix.md` 的提交（按其 §1 由
`git log -1 --diff-filter=A --format=%H -- <该文件>` 运行时解析；主题「P1-ENG-LOOP-001 R1@K1K3 返工：修复 F1
（死写者锁清理记日志）与 F2（同 id 重写回执 IGNORED_DUPLICATE），交 R2@K1K3」），是本地 `origin/main` 的祖先。
修复触及行基线 = R1 §0 `round_candidate`（`3fe929a…`）。两者之间另有 14 笔提交（COORD-012 协调批次 ×12、
`C1@K1K3` 核对、R1 复核记录）；其中触及 PLAY_GOVERNING 的只有 COORD-012 的 `tools/check_docs.py`、
`tools/check_role_writes.py`、`tests/test_check_docs.py`、`tests/test_check_role_writes.py`（用户直接授权的协调
批次，提交信息引用 `docs/authorizations.md` 2026-09-20 的八条 COORD-012 条目；与本项实现文件零重叠，不是 Play
治理门文件，不属本 work ID 候选内容）。本 work ID 仍无上一通过候选（R1 为 `REWORK_REQUIRED`），全量 diff
基线仍为 manifest `baseline_before_first_runtime_file` `40229e6…`。
round_candidate: 9e73509bd2109ebfb888fc0395a7e5dc98960446
Verdict: PASS_WITH_NOTES
passed_candidate: 9e73509bd2109ebfb888fc0395a7e5dc98960446

## 0. 复核范围、开轮资格与重跑

- **轨道与停点**：不变（提案抬头逐字 `Workflow: engineering-v1`、D4 `ACCEPTED` 裁定生效；停点 `K1K3`）。合同在
  两候选之间无变化：提案 diff 只增 `C1@K1K3` 核对块与决策记录一行，`docs/implementation-status.md` 只增接受侧
  进度段；无新 AC、无 AC-1 改写、无 F3 账本行。
- **开轮资格（COORD-007 R1 / workflow §4.4）**：无上一通过候选；`git diff 3fe929a..9e73509` 于 PLAY_GOVERNING
  非空——本 work ID 的实现文件恰为交接行声明的四个：`controller/language_bridge.py`（+68/−）、
  `controller/language_loop.py`（+41）、`tests/test_language_bridge.py`（+27）、`tests/test_language_loop.py`
  （+115），全部在单一提交内 → 开轮。Play 治理门三文件（`tools/analyze_m3_body.py`、
  `tools/preflight_reanchor_env.py`、`controller/run_log.py`）、冻结边界（`Assets/`、`config/`、`tools/eng_sft/`、
  `controller/{protocol,tracking_entry,track_loop}.py`、`ProjectSettings/`、`Packages/packages-lock.json`）与
  `controller/{gated_publisher,language_selector,language_demo}.py`、`tools/language_{serve,latency}.py`、
  `tools/requirements-language.txt` 的 `git diff --stat` 全部为空，与交接行「零改动」声明一致；既有证据 JSON
  无一修改（全量 diff stat 中 `docs/evidence/` 只新增五个文件）。
- **停点自证核实（workflow §4.3.1 四项）**：条件 1（范围/接口冻结：无新 AC、闭集成员、桥文件或 schema 字段；
  `IGNORED_DUPLICATE` 原已在 `OUTCOMES`；CLI 返回字典新键 `replaced_writer_lock` 只在接管时出现、不在桥协议内）、
  条件 2（相称测试：见下方重跑）、条件 3（阶段 A 零 Unity，无本批 Unity 失败）、条件 4（状态板交接行、候选解析
  规则、风险 §7 已更新；候选已推送）按字面成立 → **开轮，不给 `REVIEW_BLOCKED`**。
- **增量轮范围（COORD-009 (b)）**：新阻断只来自修复触及行上的 CLASS_1/2、F1/F2 闭合失败、`RED_LINE`、未改动行上
  标 `上轮漏检` 的 CLASS_1。本轮无 `blocks_consuming_gate` 行（交接 `Consuming=no`，且未发现未改动行上的
  `上轮漏检` CLASS_2）。
- **副本**：`git worktree add --detach .claude/worktrees/review-P1-ENG-LOOP-001 9e73509…`；副本无 `outputs/`，
  同 R1 以一条指向主树 `outputs/` 的只读符号链接补跑冻结资产用例；读码、重跑、红绿全部在副本内，主树实现文件
  只读；收工删除副本。
- **重跑（不信报告数字；测试树哈希 `HEAD:tests` = `69f53a3d956aadd1fcb418aaf4bea3ca814a6349`、
  `HEAD:controller` = `c86831216e963fdd79fa9ffb65771eeae782cc33`、`HEAD:tools` = `5cedaf4887a6a6f0ff8c82a2dd3907399a86974f`）**：
  - focused：`TMPDIR=/private/tmp .venv-language/bin/python -m unittest tests.test_language_bridge
    tests.test_language_selector tests.test_language_loop tests.test_language_k_binding` → `Ran 260 … OK`，
    **零 skip**（冻结资产两项与 Pillow 预览用例实际执行）。257 + 本批新增 3 = 260，与实现者
    `-tests-r1-fix-focused.log` 一致。
  - 红绿（每条阻断 finding 一次）：副本内把 `controller/language_bridge.py`、`controller/language_loop.py` 检出到
    `round_candidate` `3fe929a…`（修前源码 + 修后测试），跑 7 条具名用例 → `Ran 7 / FAILED (failures=2, errors=3)`：
    F1 回归 `test_a_dead_writer_lock_is_reclaimed_and_reported_by_the_cli` `KeyError: 'replaced_writer_lock'`（接管
    静默发生、回执照常）；F2 回归 `test_a_rewritten_duplicate_id_gets_an_ignored_duplicate_receipt` 断言失败
    （`last_request` 仍是 B 的 `APPLIED`）；两条锁辅助 `test_acquire_takes_over_a_dead_lock` /
    `test_second_writer_is_refused` `TypeError`（无 `on_dead_lock_cleared`）；桥辅助
    `test_unknown_action_reads_as_invalid_not_raise` `command_id None != <写入值>`；残留静默钉子
    `test_exactly_once_and_duplicate_id` 与无接管 `test_the_cli_reports_no_takeover_for_a_free_slot` 修前即绿
    （钉住既有行为，不作阻断绑定）。`git checkout HEAD --` 恢复两文件后同 7 条 → `Ran 7 … OK`；副本
    `git status --porcelain` 除本角色的 `outputs` 链接外干净。与实现者 `-tests-r1-fix-before.log`（2 F + 3 E，
    同名）/ `-after.log`（7 OK）逐名同结果。
  - 实现者全套 `-tests-r1-fix.log`：`Ran 1515 / FAILED (errors=9, skipped=24)`、FAIL 0；9 个 ERROR 名与 K1K3
    停点 `P1-ENG-LOOP-001-tests.log` 的 9 个逐名相同（排序 diff 为空，同因缺 `cv2`/`numpy`）→ 本批新增失败 0。
    全套是实现者停点义务，本轮只读日志核对，不重跑。
  - 输出写会话 scratchpad（`r2-focused-venv-language.log`、`r2-f1f2-red.log`、`r2-f1f2-green.log`），上下文只
    回显摘要，不带 `-v`。

## 1. F1 / F2 闭合核实（逐条对照 R1 闭合要求四条）

**F1 — CLOSED。** 代码：`acquire_writer_lock` 新增关键字参数 `on_dead_lock_cleared`，在确认持有 pid 已死并
`unlink` 之后、重建之前当场把 `existing`（`LockHolder`：pid、request_id、created_unix_s）交给回调；重建输给并发
写者仍抛 `WriterBusy` 但回调已发生；活锁与坏锁（`pid=-1`）不触发回调；返回类型不变，`language_demo.py` 的无
回调调用兼容。`send_request`（九个 CLI 动作的唯一写入路径）传入 `report_cleared`：向 stderr 打一行
`已清理死写者锁：pid=… request_id=… created_unix_s=…`，并把三字段放进 `replaced_writer_lock` 随返回字典在**两条**
返回路径（回执到达、5 s 超时「结果未知」）一起返回；`main` 以 `json.dumps` 原样打印到 stdout。无接管时无键、
无输出。测试：`RequestLifecycleTests.test_a_dead_writer_lock_is_reclaimed_and_reported_by_the_cli`——真实已退出
子进程 pid + `bridge.acquire_writer_lock(..., pid=<已死 pid>)` 建死锁（不手写锁文件）+ `send_request` 缺省
`os.kill` 探活 + `Harness` 真实 tick；断言回执 `APPLIED`、`replaced_writer_lock` 三字段逐值相等、stderr 含 pid 与
request_id、等待期间锁持有者恒为 `(os.getpid(), "next")`、结束后锁已释放、会话 JSONL 无
`ILLEGAL_WRITER_SUSPECTED`。四条：(1) 生产路径 fixture ✓；(2) 修前红/修后绿由本角色复现 ✓；(3) 不触及 Play
治理门 ✓；(4) 可机械断言 ✓。合同「并记日志」未指定落点，R1 闭合要求已明写接受「CLI 输出/返回字典（或
stderr）」，本轮按字面闭合；持久化边界见注记 1。

**F2 — CLOSED。** 代码：`LanguageSession.consumed_requests` 改为 `dict[request_id → (command_id, issued_unix_s)]`，
`_consume_request` 对已消费 id 分三路：写入身份与记录相同（槽内同一次写入每 20 ms 重读）→ 静默；身份缺失
`(None, None)` → 按残留静默；身份变化（`protocol.packet` 每次 `write_request` 铸新 `time.time_ns()`）→ 更新记录并
`_receipt(envelope, "IGNORED_DUPLICATE")` 恰一次（此后同身份重读再次落入「相同」分支）；不 `_dispatch`、不改
状态/epoch/候选/段、不起查询。`read_request` 对可寻址的结构非法请求也带出 `command_id`/`issued_unix_s`（七处
非法分支改走局部 `invalid(reason)`，`invalid_reason` 取值与判定顺序逐项不变：`unknown_action` →
`instruction_unsupported` → `invalid_candidate_index`×2 → `invalid_token` → `missing_instruction` →
`missing_candidate_index`；不可寻址的五个出口仍不带写入头）。判定顺序与 R1 候选相同（去重 → 锁缺失记
`ILLEGAL_WRITER_SUSPECTED` → 记身份 → 外会话 → `TERMINAL` → 非法 → dispatch）。`consumed_requests` 经 grep 无其他
读者或序列化点。测试：`RequestLifecycleTests.test_a_rewritten_duplicate_id_gets_an_ignored_duplicate_receipt`——
A `ask` → `APPLIED`（`AWAITING_CONFIRMATION`）→ B `reject` → `APPLIED`（`IDLE`，`last_request` 变为 B）→ 持写者锁经
`Harness.request` → `bridge.write_request` 用同 id 重写 A（新 packet，不手写 JSON）；断言 `last_request` =
`{A, ask, IGNORED_DUPLICATE}` 且 `at_sequence` 大于 B、状态 `IDLE`、epoch、候选 `None`、`worker.calls_started`、
结果行数全部不变；再 tick 10 次后 A 的回执序列恰为 `[APPLIED, IGNORED_DUPLICATE]`。改写后的
`test_exactly_once_and_duplicate_id` 钉住「槽内残留重读不回执」（10 tick 后回执序列恰为 `[APPLIED]`）。四条：
(1) ✓；(2) ✓（本角色复现）；(3) ✓；(4) ✓。桥闭集未动。

## 2. 修复触及行核查（本轮新阻断的唯一来源；结论：无 CLASS_1/2）

- 坐标/单位/时间戳/帧绑定与过期语义：`issued_unix_s` 只作写入身份比较，不参与任何过期或帧判断；无改动。
- 边界与失败路径：`acquire_writer_lock` 回调只在「已死 → unlink」之后，坏锁/活锁不触发（`test_second_writer_is_refused`
  断言 `cleared == []`）；`send_request` 在 `WriterBusy` 逃逸时 stderr 行已打印、`main` 仍报 `WRITER_BUSY` 退出码 4；
  `replaced_writer_lock` 值均可 JSON 序列化（`request_id` 可为 `null`）。
- 并发/原子性：写者锁语义（O_EXCL、持有者匹配释放）无改动；重写去重靠会话内记录，单槽单会话，无新竞态。
- 真值泄漏：无（改动不接触帧/评估器）。
- 测试真实覆盖：两条具名回归均走生产写盘函数与真实 tick；红绿由本角色复现（§0）。
- 文档一致性：`acquire_writer_lock`/`send_request` docstring 与行为相符；`runtime/README.md` 与桥 schema 无需改动
  （CLI 输出不在桥协议内）；实现者 §7 如实披露 F1 落点与 pid 复用风险。

## 3. Findings

### Blocking

无。F1、F2 闭合（§1）；修复触及行上无 CLASS_1/2；无 `RED_LINE`；无旧 finding 闭合失败。

### Non-blocking

**F3**（R1，`SCOPE_GAP`，pending 任务 `T_hard` 从创建时刻起算）状态不变：本轮修复未触及 `LanguageWorker`，
`docs/implementation-status.md` 尚无该 finding 的账本行——仍路由接受角色记债或裁定，不阻断本轮。

## 4. 非阻断注记（不是 finding，不带依据列）

1. **F1 的「日志」只落 CLI 进程**（stderr 一行 + stdout 返回字典），不进会话 JSONL；CLI 与会话是两个进程，持久化
   须新增桥文件或日志文件（扩协议），本轮未做且不在 R1 闭合要求内。阶段 B 操作单须提示操作者保存 CLI 输出；接受
   角色若要求会话侧持久化，以 Pending ruling 明示，不由实现自行扩协议。
2. **两类 ignored 回执的优先级**：重写的重复 id 在 `TERMINAL` 下回 `IGNORED_DUPLICATE` 而非 `IGNORED_TERMINAL`；
   外会话残留 id 被本会话操作者手动重用同样回 `IGNORED_DUPLICATE`。判定顺序与 R1 候选完全相同（R1 下这两种情形是
   静默无回执），两者都不派发、不改状态，`_receipt → _publish_state(force=True)` 与既有 `IGNORED_*` 同路径；合同
   §3.2(a) 按 id 定义该回执、未写两类 ignored 的优先级，本角色不作 finding。
3. **写入身份的分辨率**：同 id 两次写入落在同一 `time.time_ns()` 才会被当成残留；CLI 重试相隔 ≥ 5 s 超时，不可达；
   测试内两次写入之间隔真实文件 I/O 与 tick。
4. **死锁回归的环境风险**：依赖已退出子进程的 pid 在毫秒窗内未被复用（实现者 §7 已披露）；偶发时表现为
   `WriterBusy` 错误而非漏检，不影响生产逻辑。
5. `clear_dead_writer_lock` 仍只被测试调用（生产链路改走回调），保留无害。
6. R1 注记 1…9 与 F3 按用户指示未被本轮修复吸收，状态不变；注记 6（确认后首批追平 0.4 s 门）仍请在阶段 B 信封
   决策前评估。

## 5. Verdict 与交接

- **`PASS_WITH_NOTES`**：K1K3 停点独立复核通过。AC-1（含修订 1）改判**满足**；AC-2…12/16/17 结论沿用 R1（修复未
  触及）；AC-13…15 待阶段 B。通过候选 = 本节抬头 `passed_candidate` 所指提交。K1K3 C/R=1/2（C 退回 0、R 退回 1）。
- [接受] 消费本 verdict；F3 `SCOPE_GAP` 记入「范围外已知缺陷」账本或裁定范围内必修；注记 1/2 若要改口径写 Pending
  ruling；随后向用户申请阶段 B 信封（AC-13…15 真实 Play 证据）。
- [用户] 阶段 B 信封另行签发；本轮不消耗任何额度。

## `UNITY_NA` 附议

本工作项**不申请** `UNITY_NA`（提案 §4 与 Gate board 行同）。本轮无附议对象，不附议、不反对；AC-13…15 仍是
`DONE` 的必要证据，须待用户另行签发阶段 B 信封后由真实 Play 产生。通过本停点不等于 `DONE`。

## 6. 边界自查（R2@K1K3 收工）

- 本会话未修改任何实现文件：`controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零改动。副本内为复现修前红曾把
  两份实现文件检出到 `3fe929a…`，随后 `git checkout HEAD --` 恢复；副本内的 `outputs` 只读符号链接随副本删除，主树
  `outputs/` 未写入。
- 主树本批写入：`docs/reviews/P1-ENG-LOOP-001.md`（追加本节）与 `docs/current-status.md`；
  `python3 tools/check_role_writes.py --role review` 与 `python3 tools/check_docs.py` 结果记在状态板 Log。
- 零消耗：未启动模型/服务/Play、未下载、未创建 scenario/session/run ID、未触碰真实 `runtime/`。
- 收工自检结果：`python3 tools/check_docs.py` 通过；`python3 tools/check_role_writes.py --role review` 报出 1 个路径
  `docs/evidence/COORD-013-tests-before.log`——这是**并发的 COORD-013 会话**在主树写入的未跟踪红跑日志（mtime
  2026-09-21 19:31:20，内容为 `tests.test_check_docs.RelayCostTest` 修复前失败；同一时段该会话还曾短暂改写并恢复
  `tools/check_*.py` 与 `tests/test_check_*.py`），不是本角色写入。本角色**未删除、未恢复**该文件（删除会毁掉他人
  在途工作），本批提交只暂存 `docs/reviews/P1-ENG-LOOP-001.md` 与 `docs/current-status.md` 两个路径；越权路径
  归因由该会话自行处理。

---

# R3@K1K3 — 单字段设置与操作单 C 冻结集候选（C2@K1K3 → R3）

Reviewer/role: 复核角色 / independent verification（新鲜上下文会话，Fable 池；档位不低于实现者）
Workflow: engineering-v1（同 R1/R2；依据列沿用 workflow §4.4 六值闭集，`BC-n` 读作合同 `AC-n`）
Round: R3@K1K3
Date: 2026-09-22
Implementation snapshot: 候选 = 首次加入 `docs/evidence/P1-ENG-LOOP-001-K1K3-c2-handoff.md` 的提交（按其 §1 由
`git log --diff-filter=A --format=%H -- <该文件>` 运行时解析；主题「P1-ENG-LOOP-001 C2@K1K3 候选：runInBackground 单字段与
操作单 C 冻结集（R-B1…4 落实，零消耗）」），= 本地 `origin/main`，已推送；主树 HEAD 在其后一笔（接受角色 C2 核对提交，只改
状态板/提案/账本）。上一通过候选 = R2 `passed_candidate`（`9e73509…`），上一复核轮候选 = R2 `round_candidate`（同一提交），
两条基线重合：全量 diff = 修复触及行 = `git diff 9e73509…..4914830…`，17 笔提交、42 文件（+4726/−290）。
round_candidate: 49148306707d3ea6020a8458a63a8eb974014b04
Verdict: REWORK_REQUIRED

## 0. 复核范围、停点资格、开轮资格与重跑

- **轨道与停点**：不变（提案抬头逐字 `Workflow: engineering-v1`、D4 `ACCEPTED` 裁定生效）。本候选不是 R2 的返工，
  而是 R-B1…4 裁定（AC-4 修订 3 / AC-12 修订 3）派生的同停点新候选，经 C2@K1K3 后交本轮；C/R 计数沿用，本轮为 R3。
  合同 = §1…8、AC-1…17、八行首次释义、十二行实现期修订（P-A-1…8、P-B-1/2、R-B1…4 的 AC-4/12 修订 3），冲突处以后者为准。
- **停点自证核实（workflow §4.3.1 四项）**：条件 1（范围/接口冻结：`controller/`、`Assets/`、`config/`、`Packages/`、
  `tools/eng_sft/`、`tools/language_*`、`tools/requirements-language.txt` 相对 R2 通过候选 `git diff --stat` 为空，
  `HEAD:controller` 树哈希 `c86831216e963fdd79fa9ffb65771eeae782cc33` 与 R2 逐字相同；`ProjectSettings/` 只有
  `runInBackground: 0 → 1` 一行，本角色 `git diff` 现算）、条件 2（相称测试：载体自测 21/21、语言 focused 260、`lc_check`/
  `lc_run` 负向运行均由本角色复现，见下；全套日志唯一新增 failure 经本角色独立复算为环境残留、与候选零交集，见 §1 AC-11
  与注记 2）、条件 3（唯一已知 Unity 问题 = 失焦停帧，本批按裁定改设置且如实写明「效果未验证」，无待修代码类 Unity 失败）、
  条件 4（状态板交接行、候选解析规则、未验证风险 §4、复核范围 §5 均在案；候选已推送）按字面成立 → **开轮，不给
  `REVIEW_BLOCKED`**（C2-1 所问「§4.3.1 条件 2 能否成立」：成立）。
- **开轮资格（COORD-007 R1 / workflow §4.4）**：`git diff 9e73509…..4914830…` 于 PLAY_GOVERNING 非空：
  `ProjectSettings/ProjectSettings.asset`（+1/−1）；R-B1 点名的本 work item 冻结操作单四文件
  `docs/evidence/P1-ENG-LOOP-001-{operations-c.md,operator.sh,operator-watch.py,5060-runner-b.py}`（相对 R2 整文件新增：
  176/181/261/201 行）；以及 COORD-013 协调批次的 `tools/check_docs.py`（+189/−22）、`tools/check_role_writes.py`（+3）、
  `tests/test_check_docs.py`、`tests/test_check_role_writes.py`（+13）→ 开轮。Play 治理门三文件（`tools/analyze_m3_body.py`、
  `tools/preflight_reanchor_env.py`、`controller/run_log.py`）零改动，无闭环轮义务。本停点交接 `Consuming=no`，无
  `blocks_consuming_gate` 行。
- **增量轮范围（COORD-009 (b)）**：上一复核轮候选 = 上一通过候选，故本轮"修复触及行"= 全量 diff；四个冻结操作单文件与
  单字段全部在触及行内，其上的 CLASS_1/2 是本轮合法的新阻断来源。
- **副本**：`git worktree add --detach .claude/worktrees/review-P1-ENG-LOOP-001 4914830…`；副本无 `outputs/`，同 R1/R2 以
  一条指向主树 `outputs/` 的只读符号链接补跑冻结资产用例；读码、重跑、探针全部在副本内；`lc_check` 负向运行按脚本硬编码
  路径读主树（只读）并在主树被忽略的 `outputs/eng-loop/…/operator/diag-review-r3-check/` 写了本角色自己的 `precheck.log`，
  运行后已删除该目录；收工删除副本。
- **重跑（不信报告数字；候选树哈希 `HEAD:tests` = `ab4081d2593788b0aea75c6c0878bf32bbd94a0b`、
  `HEAD:controller` = `c86831216e963fdd79fa9ffb65771eeae782cc33`、`HEAD:tools` = `8533c6ee570bb97909e656a59a4e1e6e8fddd5c5`、
  `HEAD:ProjectSettings` = `d876cff76d4cfe187004d83efb6202be007160b3`）**：
  - 语言 focused：`TMPDIR=/private/tmp .venv-language/bin/python -m unittest tests.test_language_bridge
    tests.test_language_selector tests.test_language_loop tests.test_language_k_binding` → `Ran 260 … OK`，零 skip。
  - 协调批次工具 focused：`python3 -m unittest tests.test_check_docs tests.test_check_role_writes` → `Ran 55 … OK`。
  - 载体自测：`python3 docs/evidence/P1-ENG-LOOP-001-c2-carrier-selftest.py <主树 runtime/frames.1b-diagnostic-hold>`
    → 21 项 `ok`、`OK: 0 failed`、退出码 0；副本内把 runner 与 watch 检出到候选父提交 `1b08fc4…`（准备批次版本）再跑 →
    第 2 项 `FAIL runner: amend and serve blocks found` 后以未捕获 `KeyError: 'serve'` 退出码 1（红），随后
    `git checkout HEAD --` 恢复，副本 `git status --porcelain` 除本角色的 `outputs` 链接外干净。
  - `lc_check`/`lc_run` 负向运行（Unity 未开、5060 离线、主树 HEAD 含未通过的新候选、`runtime/` 有诊断残留）：zsh 与 bash
    下 `lc_check` 退出码 1、`lc_run` 退出码 2、会话未启动；逐项输出与实现者 `-c2-carrier-selftest.log` §4 同形（`FAIL main
    tree differs from passed_candidate on: ProjectSettings/… + 四个操作单文件`、`FAIL Unity is not open`、五个槽位文件、
    `runtime/frames not an empty directory`、`FAIL 5060 /status not idle`），并多出 `ok main tree status empty on the same
    paths`（本轮主树干净）。
  - C2-1 探针（只读；用副本的 `tools.dist_data.roots` 对主树 `runtime/` 复现 `RealArchiveClosureTest._images` 的枚举）：
    枚举 44,750 个 JPG，零匹配 404 = `runtime/frames/` 128 + `runtime/hold-diag-loopb-2/frames/` 148 +
    `runtime/hold-diag-loopb-2b/frames/` 128，三目录之外零匹配 0、多匹配 0——与实现者 §2 归因逐文件相符。
  - 全套日志只读核对：`-tests-c2.log` `Ran 1524 / FAILED (failures=1, errors=9, skipped=24)`；9 个 `ERROR:` 名与
    `-tests-r1-fix.log`（`Ran 1515 / errors=9 / skipped=24 / failures=0`）排序 diff 为空；+9 项 = `RelayCostTest` 8 项 +
    `test_acceptance_can_write_parked_status` 1 项（COORD-013 协调批次测试）。全套仍是实现者停点义务，本轮不重跑。
  - 输出写会话 scratchpad（`r3-focused-venv-language.log`、`r3-check-tools.log`、`r3-carrier-{green,red}.log`、
    `r3-lc-check-{zsh,bash}.log`、`r3-c2-1-probe.{py,log}`），上下文只回显摘要，不带 `-v`。
- **直接关联冻结代码**（只读，候选与 R2 同字节）：`language_loop.py` 的 `tick`、`_seed_segment`（`initialize` → `unmute` →
  `_enter("TRACKING")`）、`_advance_segment`、`_maybe_verify`/`_request_verification`、`_handle_verify_outcome`（先
  `_emit_verify_result` 写结果、后 `_raise_suspect` 写状态）、`_enter`/`_publish_state`（整份镜像变化即重写）、
  `_action_{confirm,reject,confirm_lost,dismiss,release,verify}`（令牌 = `candidate_result_id` / `suspect_id` / `track_id`；
  `verify` 在 `SUSPECTED` 允许）、`send_request`、`resolves_to_shared_runtime`、`_run_session`（`--diagnostic` 时
  `run_root = <diagnostics-root>/<session>`）、`build_parser`（`run` 与九个请求子命令的参数名）、`main`（`status` 只读）；
  `language_bridge.tracker_state_payload`（含 `publishing`、`last_published_frame_id`、`suspect_*`、
  `verification.last_query_id`）；`gated_publisher.py` `unmute`/`publishing`/`last_published_frame_id`；
  `tests/test_dist_data_round4.py` `RealArchiveClosureTest._images` 与 `tools/dist_data/roots.py` `ENUMERATION_ROOTS`
  （`runtime` 全递归，只排除 `runtime/models/`、`runtime/yoloe/`）。

## 1. 逐条 AC 核对（只列本候选触及或 C2 核对表提问的条款；其余 AC-1…10/16/17 运行时零改动，沿用 R2 结论）

| 编号 | 结论 | 本轮核实 |
|---|---|---|
| AC-4（含修订 3） | 满足（离线半边） | `git diff --numstat 9e73509… 4914830… -- ProjectSettings` = `1 1 ProjectSettings/ProjectSettings.asset`，diff 正文仅 `-  runInBackground: 0` / `+  runInBackground: 1`；`Assets/`、`config/`、`tools/eng_sft/`、`Packages/`（含 `packages-lock.json`）零差异；`Assets/**/*.cs` 无 `runInBackground`/`OnApplicationFocus`/`OnApplicationPause`/`targetFrameRate` 覆写。持续供帧效果按裁定留待诊断，候选未声称生效。 |
| AC-11 | 满足（实质；字面偏差已披露并经本角色独立复算） | 本批新增失败 = 0 归因于候选：日志中唯一 `FAIL:` `RealArchiveClosureTest.test_zero_unmatched_and_zero_multi_matched_jpg` 的 404 个零匹配文件由本角色以同一枚举规则复算，全部是阶段 B 诊断 Play 在 git 忽略的 `runtime/` 下留下的帧（三目录，见 §0），产生于 R1 修复批基线之后、不在任何提交内；被测代码（`tools/dist_data/*`、该测试）相对 R2 零改动；9 个 ERROR 逐名同基线、skip 数相同。实现者已把它与基线失败分列并写明原因（AC-11「分列」要求满足）。字面「新增失败 0」在本机主树上不可能由候选代码达成，属测试对 `runtime/` 残留敏感（另一 work item 的测试合同），路由见注记 2；下一候选的停点全套须在无残留的隔离副本跑出新增失败 0（§5）。 |
| AC-12（含修订 1/2/3） | **不满足（F4、F5）** | 额度：runner `LIMITS` 与信封逐字相同，`amend` 冻结已计费旧诊断会话（`diag-loopb-2`）、新诊断恰 ≤2、第三个拒绝、`serve` 未 `amend` 拒绝、per-session 40 / 总 400 / 正式 8 不变——21 项自测由本角色复现，旧 runner 红。对应性：`lc_check` 十项（worktree HEAD = 最后一条 `passed_candidate` 且 `--untracked-files=all` 干净；主树 `Assets config ProjectSettings Packages` + 四冻结文件相对候选 `diff --name-only` 为空且同路径 `status --porcelain --untracked-files=all` 为空——`Assets/_Recovery/` 未被任何 `.gitignore` 忽略，会被列出；`runInBackground: 1` 逐字；Unity 进程 `pgrep`；槽位/锁/帧目录/进程/5060 idle）与 AC-12 修订 3 列举的不对应情形逐项对应，`lc_run` 不过即拒绝（负向运行复现）。顺序：操作单 §2「先 Unity 后检查」、§4 第 2 步「先持续供帧后 ask」、§0 硬停止与 R-B4 一致；`lc_run` 参数名与冻结 CLI `build_parser` 逐字匹配，诊断产物落 `<diagnostics-root>/<session>`、正式段落 `runtime/runs/`。5060：清单构建脚本从新候选 git 对象取源、`tools/check_*.py` 列入 `not_verified`（COORD-013 改动不致重建失败），runner preflight 逐文件核哈希。**但**操作单 §4/§5 依赖的 watch 呈现有两处与文字/合同不符（F4 发布帧号不可见、F5 告警预览未按 `query_id` 绑定），操作单作为 AC-12 修订 3 的验收工件不能记满足。 |
| AC-13（含修订 1） | 未到证据时点 | 正式 Play 0 次；不申请 `UNITY_NA`。修订 1「提示绑定核验源帧副本与 `query_id`」对操作工具的要求见 F5。 |
| AC-14 / AC-15 | 未到证据时点 | 同上。 |
| AC-1…3/5…10/16/17 | 沿用 R2 | `controller/`、`tools/language_*` 零改动（树哈希同 R2），focused 260/260 本轮实际执行。 |

## 2. 全量 diff 逐文件处置（42 文件）

- **A 本批 PLAY_GOVERNING**：`ProjectSettings/ProjectSettings.asset`（见 AC-4）；四个冻结操作单文件整文件读毕（F4/F5/F6、注记 1/3/4/5）。
- **B 本批证据**：`-K1K3-c2-handoff.md`（自证四项与逐 AC 指针核实）、`-c2-carrier-selftest.py`/`.log`（绿/红复现；§3 见 F6）、
  `-tests-c2.log`（见 AC-11）、`-stage-b-prep.md` §7（单字段核对叙述与 diff 相符）。
- **B 阶段 B 准备与诊断记录**（R2 之后本批之前，实现角色）：`-build-stage-b-manifest.py`（候选从复核文件最后一条
  `passed_candidate` 解析；`changed == TRANSFER` 严格断言；`NOT_VERIFIED` 含两个 check 工具）、`-transfer-manifest-5060-stage-b.json`
  （118 文件，`passed_candidate` = R2 通过候选；R3 后须重建）、`-service-5060-b.log`、`-tests-client-env.log`（260 OK、2 skip，
  与 prep §3 一致）、`-stage-b-prep.md` §1…6（诊断 1/2、登记外 Play、恢复目录如实记录）。
- **C COORD-013/014 协调批次**（用户直接授权，账本 2026-09-21/22 同名条目）：`tools/check_docs.py`、`tools/check_role_writes.py`、
  `tests/test_check_docs.py`、`tests/test_check_role_writes.py` 逐 hunk 读毕——只增状态板字节上限/ENDED 行/parked DONE 行检查与
  `docs/parked-status.md` 写权限，不导入运行时、不触及 Play 治理门；四文件全部来自 `5b6ca44`（COORD-013 落地），COORD-014 提交
  `88ad385` 未触及 `tools/`/`tests/`，与其授权条目「明确未授权改 tools/、tests/」一致；协调批次自身的 focused 55/55 本轮重跑。
  其余为 `AGENTS.md`、两份 workflow、`docs/roles/*`、命令文件、`docs/parked-status.md`、`docs/workflow-changelog.md`、
  COORD-013 提案与证据。按 R-B1 裁定如实列为独立协调批次，不是本 work item 候选内容，本轮不签发其复核结论。
- **D 其他角色文档**：`docs/{authorizations,current-status,implementation-status,unity-test-log}.md`、提案、本复核文件、
  `docs/phase1-single-drone-design.md`（v0.3.47 只加单字段例外与 R-B 指针，与裁定一致）。

## 3. Findings

### Blocking

**F4 — 操作单 §4 第 4 步 / §5 第 2 步要求操作者在 T2 看到 `last_published` 出现帧号并增长，但 watch 的 STATE 去重键不含
`last_published_frame_id`，该值只随状态/原因/疑似/段/publishing 变化打印一次，首条 `WRITTEN` 之后永不刷新。** CLASS_2 ·
依据列 `BC-12`（读作 AC-12 修订 3：操作单 C 与三个执行载体是本停点的验收工件；R-B4 要求新增诊断核实首批追平）· 范围判据：
可达——每次播种必经。
- 位置：`docs/evidence/P1-ENG-LOOP-001-operator-watch.py` `Watch.on_state`（key 五元组 `state/reason/suspect_id/track_id/publishing`，
  第 145–154 行）；`docs/evidence/P1-ENG-LOOP-001-operations-c.md` §4 第 4 步、§5 第 2 步。
- 代码事实（副本内读 `controller/language_loop.py`）：`_seed_segment` 在 `initialize` 后 `unmute` 并 `_enter("TRACKING")` →
  `_publish_state(force=True)`，此刻 `last_published_frame_id` 为 `None`（初始化发布被静音，首条 `WRITTEN` 在后续 tick 的
  `_advance_segment` 批末才产生）；之后镜像确会随 `last_published_frame_id` 变化重写（tick 末 `_publish_state` 比较整份文档），
  但 watch 的去重键不变 → 终端上唯一一行 STATE 永远是 `last_published=None`。`lc status`（T3）能读到该字段，操作单未写这条路径。
- 后果：`diag-loopb-3` 第 4 步判据无法按文字执行，操作者可能把 `None` 误判为首批追平失败而提前 `lc stop`（消耗新增诊断 1/2）；
  正式 P1 第 2 步「`last_published` 在增长」同样看不到。
- 闭合要求（workflow §4.4 四条）：(1) fixture 经 `controller.language_bridge.tracker_state_payload` + `write_tracker_state`
  （真实写盘函数）写两份同键状态、`last_published_frame_id` 由 `None` → N，禁止手写 JSON；(2) 具名回归修前必红，例如自测
  `check("watch: last_published change is printed", …)`：第二次 tick 后 `watch.log` 含 `last_published=N`；(3) 不触及 Play 治理门；
  (4) 可机械断言。实现建议（不构成义务）：把 `last_published_frame_id` 纳入去重键（只在变化时打印一行）或在 10 s 一行的 `sim_t`
  行加 `last_published=`，并同步操作单文字（或改写为「T3 `lc status` 看 `last_published_frame_id`」）。

**F5 — SUSPECTED 告警「自动打开触发告警的核验预览」未按 `query_id` 绑定：watch 用 `open_next_verify` 悬挂标志消费「下一条」
核验结果，跨两个桥文件的读取时序可使触发告警的预览不被打开，而稍后另一帧的核验预览被当作告警预览打开。** CLASS_2 · 依据列
`BC-13`（读作 AC-13 含修订 1「目检与**提示**都绑定核验源帧副本与 `query_id`」；操作单 §5 第 3 步据此让操作者决定
confirm-lost/dismiss；AC-12 修订 3 把操作单列为验收工件）· 范围判据：可达——每个 `SUSPECTED(lost|drift|ambiguous)` 事件的生产
写入顺序就是触发条件。
- 位置：`-operator-watch.py` `tick`（先读 `tracker_state.json` 再读 `language_result.json`）、`on_state`（第 158–164 行置
  `open_next_verify`）、`on_result`（第 167–169 行按 `result_id` 去重；第 192–194 行消费标志）；`-operations-c.md` §5 第 3 步。
- 代码事实：`_handle_verify_outcome` 先 `_emit_verify_result` → `bridge.write_result`（`language_result.json`）与 `results.jsonl`，
  **再** `_raise_suspect` → `_enter("SUSPECTED")` → `write_tracker_state`，两次写入之间还有两行会话 JSONL。若某次 watch tick 的两次
  读取落在两次写入之间（读到旧 `TRACKING` + 新核验结果 Q），`on_result` 以 `result_id` 把 Q 记为已处理且不打开（标志尚未置位）；
  下一 tick 才见 `SUSPECTED` 并置 `open_next_verify=True`，但 Q 已被去重，永不打开；标志随后由任意一条核验结果消费——在
  `SUSPECTED` 下周期核验停止（`_maybe_verify` 只在 `TRACKING`），下一条只能来自操作者 `lc verify`（`_action_verify` 允许
  `SUSPECTED`），其配对帧晚于告警帧，却按操作单被当作「自动打开的核验预览」。告警行 `!!! SUSPECTED(...) suspect_id=…` 本身不带
  触发 `query_id` 与预览路径，操作者只能靠上一行 RESULT 的邻接推断；状态镜像 `verification.last_query_id` 已提供绑定键而 watch 未用。
  `tracker_failure` 类疑似无触发核验结果，操作单 §5 第 3 步「按预览如实判断」未写明须先 `lc verify` 才有预览。
- 后果：操作者可能按错误帧做 confirm-lost/dismiss（误 dismiss 真告警 → 事件 `E1_CHAIN_INCOMPLETE`，消耗正式 Play ≤8 之一）；
  AC-13 修订 1 的「提示绑定 `query_id`」在操作层不成立。发生概率低（straddle 窗口约毫秒级/每 250 ms tick），但每次 Play 的每个
  告警都暴露一次，且一旦发生结果是确定性的错帧。
- 闭合要求：(1) fixture 经 `bridge.write_result` 与 `write_tracker_state` 按生产顺序（先结果、后状态）写盘，模拟 straddle：
  tick₁ 读到旧 `TRACKING` + 新核验结果 Q，tick₂ 读到 `SUSPECTED`（`verification.last_query_id = Q`）；(2) 具名回归修前必红：
  tick₂ 后 `watch.log` 含 Q 的 `预览文件：file://…` 行，且随后另一核验结果 R 不被当作告警预览打开；(3) 不触及 Play 治理门；
  (4) 可机械断言。实现建议（不构成义务）：进入 `SUSPECTED` 时读 `state.verification.last_query_id`，按 `query_id` 相等打开对应
  结果的预览（不靠 `result_id` 去重与悬挂标志），并在告警行打印 `query_id` 与预览路径；`tracker_failure` 在告警行提示
  `lc verify`；操作单 §5 第 3 步同步。

### Non-blocking

**F6 — `-c2-carrier-selftest.log` §3 的「FAIL runner part raised KeyError: 'serve'」「FAIL watch part raised AttributeError …」
「FAILED: 3 failed」不是已提交自测脚本能产生的输出。** CLASS_3 · 依据列 `IN_SCOPE_NO_BC`（可达、在范围内、无 AC 覆盖证据日志
的脚本版本对应性；CLASS_3 按 §4.4 不阻断）· 事实：已提交的 `-c2-carrier-selftest.py` `main()` 无异常包装，对准备批次 runner
在第 2 项断言后即以未捕获 `KeyError: 'serve'` 退出（本角色复现，退出码 1，watch 部分未执行到）；§3 三行只能来自未提交的带
包装版本。红的结论不变（断言确不空转），只是日志与脚本版本不对应。逐字替换补丁（由该文件写权限角色在下一次提交应用，不改
数字/哈希/ID/disposition）——把 §3 中

```
FAIL runner part raised KeyError: 'serve'
16:59:38 sim_t=2.6s latest_frame=12 max_query_seq=0
FAIL watch part raised AttributeError: 'Watch' object has no attribute 'unfocused_frames'
FAILED: 3 failed
```

替换为

```
KeyError: 'serve'（已提交的自测脚本无异常包装：对旧 runner 在第 2 项断言后即以未捕获 KeyError 退出码 1 终止，旧 watch 未执行到；本节原「FAIL … raised …」两行与「FAILED: 3 failed」来自未提交的带包装版本，R3@K1K3 复核复现后更正）
```

**F3**（R1，`SCOPE_GAP`，账本 2026-09-22 `OPEN`）状态不变：本候选未触及 `LanguageWorker`；操作单 §0/§8 已按裁定把「F3 实际触发
→ 保留失败、走返工渠道」写入硬停止，与账本口径一致。

## 4. 非阻断注记（不是 finding，不带依据列）

1. **`lc_check` 的 Unity 进程检查正向路径尚未在真实 Unity 打开时跑过**（自测 §4 与本轮负向运行都是 Unity 关闭）。本角色只读
   `~/Library/Logs/Unity/Editor.log`（与 `Editor-prev.log`）的 `COMMAND LINE ARGUMENTS`：Hub 以
   `…/6000.4.1f1/Unity.app/Contents/MacOS/Unity -projectpath …` 启动，与 `pgrep -f` 模式的小写 `-projectpath` 一致，预期可匹配；
   若不匹配则 fail-closed（不启动会话），且 §2 第 4 步的 `lc_check` 在 5060 启动前执行，零额度代价。首次真实 `lc_check` 的输出
   须原样入 prep 文件（操作单 §2 第 5 步已要求）。
2. **归档闭合测试对 `runtime/` 诊断残留敏感（C2-1 的根源，路由接受角色）**：`tests/test_dist_data_round4.py`
   `RealArchiveClosureTest` 递归枚举 `runtime/` 全部 JPG（只排除 `models/`、`yoloe/`），凡阶段 B 诊断/正式 Play 或 `hold-*` 隔离
   目录存在，该测试在本机主树即失败；`runtime/` 被 git 忽略，任何候选都无法用代码使其转绿。这是 DIST-DATA 测试合同与阶段 B
   `runtime/` 使用之间的既有冲突，不属本 work item 范围；请接受角色裁定：把停点全套的运行位置定为无残留的隔离副本（COORD-013
   `0311e98` 先例），或为该测试的枚举排除立项。本轮不作 finding、不要求删除任何残留。
3. **`_lc_candidate` 在本轮之后仍解析到 R2 通过候选**（本轮无 `passed_candidate` 行）：主树 `ProjectSettings` 与四个操作单相对
   R2 候选有差异 → `lc_check` 必 FAIL → 任何 Play 都启动不了。这是 AC-12 修订 3「新候选未通过前不开 Play」的机械体现，符合预期；
   R4 通过后须先把采集 worktree `~/TetheredDroneTracking-loop-b-capture` 重新 `checkout --detach` 到新的通过候选
   （现停在 `9e73509…`），再按操作单 §1 重建清单并传输。
4. **载体自测的 fixture 边界**：watch 自测直接写 `latest.json`（复制归档真实帧元数据），未经 `controller` 写盘函数；F4/F5 的闭合
   回归须走 `language_bridge` 的真实写者（§3 闭合要求 (1)），不得延续这种手写方式。
5. **`lc_run` 的管道退出码被 `tee -a` 掩盖**（zsh/bash 未开 `pipefail`）：会话进程异常退出时 T1 的 `$?` 为 0；操作单不依赖该
   退出码（watch 与 `session-process.log` 可见），只提醒实现者读日志而非退出码。
6. **两类 ignored 回执、inconclusive 消耗配对帧、跳过行重复、`ILLEGAL_WRITER_SUSPECTED` 迟到消费**：操作单 §8 的解读与 R1/R2
   注记一致，不再重复。
7. **COORD-013/014 协调批次**：见 §2 C 类；其对本 work item 的唯一运行时影响是清单构建脚本已把两个 check 工具列为
   `not_verified`，5060 preflight 不会因其变化失败。

## 5. Verdict、冻结集与交接

- **`REWORK_REQUIRED`**（K1K3 第 2 次；R1 为第 1 次，R2 通过）。按 workflow §4.4 (c)：**未闭 finding 集自本轮起冻结 =
  {F4（CLASS_2，`BC-12`）、F5（CLASS_2，`BC-13`）、F6（CLASS_3，`IN_SCOPE_NO_BC`，补丁在案）、F3（`SCOPE_GAP`，账本 OPEN）}**，
  交接受角色逐条裁定「范围内必修」或 `SCOPE_GAP` 记债；**下一轮 R4@K1K3 终局**：检查范围 = 冻结集 + `RED_LINE` + 修复触及行
  （相对本轮 `round_candidate`）上的 CLASS_1/2，结果只能是通过或回用户。修复直接回本角色，不经核对轮。
- [实现] F4/F5：只改 `docs/evidence/P1-ENG-LOOP-001-operator-watch.py`、`-operations-c.md`（必要时 `-operator.sh`）与
  `-c2-carrier-selftest.py`；不改 `controller/`、`tools/`、`tests/`、`config/`、`Assets/`、`ProjectSettings/`；两条具名回归经
  `language_bridge` 真实写者建 fixture、修前红/修后绿写证据文件；载体自测绿；停点全套在**无 `runtime/` 诊断残留的隔离副本**
  跑一次并写 `docs/evidence/`，新增失败 0（基线 9 个 ERROR 分列；`RealArchiveClosureTest` 在副本内 skip 须写明）；应用 F6 补丁；
  提交/推送后更新状态板交接行，直接交 R4@K1K3。零 Play、零模型、零传输。
- [接受] 冻结集逐条裁定（预期 F4/F5 范围内必修：两者都在 R-B1 点名的冻结操作单范围内且每次 Play 可达）；注记 2 的归档闭合测试
  与阶段 B `runtime/` 残留冲突的处置（隔离副本跑全套或另立项）；AC-11 的字面读法若与本角色「实质满足」结论不同，按 §4.4 (b)
  提分级争议复判。
- [用户] 本轮不消耗任何额度；R4 通过前不开任何 Play（诊断或正式）。

## `UNITY_NA` 附议

本工作项**不申请** `UNITY_NA`（提案 §4 与 Gate board 行同）。本轮无附议对象，不附议、不反对；AC-13…15 仍是 `DONE` 的必要证据，
须待 R4@K1K3 通过、采集 worktree 对齐新通过候选并按 R-B4 完成新增诊断后由真实 Play 产生。`runInBackground` 单字段修改的效果
未验证，本轮不以字段值推定 Unity 问题已消除。

## 6. 边界自查（R3@K1K3 收工）

- 本会话未修改任何实现文件：`controller/`、`Assets/`、`tools/`、`tests/`、`config/`、`ProjectSettings/` 零改动；`docs/evidence/`
  零改动（F6 补丁只写在本文件，未应用）。副本内为复现载体自测的红曾把两个 `docs/evidence/` 载体检出到 `1b08fc4…`，随后
  `git checkout HEAD --` 恢复；副本内的 `outputs` 只读符号链接随副本删除，主树 `outputs/` 只多出又删除了本角色自己的
  `…/operator/diag-review-r3-check/`（被忽略路径），主树 `runtime/` 未写入。
- 主树本批写入：`docs/reviews/P1-ENG-LOOP-001.md`（追加本节）与 `docs/current-status.md`；
  `python3 tools/check_role_writes.py --role review` 与 `python3 tools/check_docs.py` 结果记在状态板 Log。
- 零消耗：未启动模型/服务/Play、未下载、未创建 scenario/session/run ID、未向 5060 传输；`lc_check` 负向运行只向 5060 发了一次
  只读 `GET /status`（5 s 超时、无响应）。

---

# R4@K1K3 — 终局轮：复核 R3@K1K3 F4/F5 修复与 F6 补丁（冻结集 + RED_LINE + 修复触及行）

Reviewer/role: 复核角色 / independent verification（Fable 池；档位不低于实现者）
Workflow: engineering-v1（同 R1…R3；依据列沿用 workflow §4.4 六值闭集，`BC-n` 读作合同 `AC-n`）
Round: R4@K1K3（同一停点第 2 次 `REWORK_REQUIRED` 之后的终局轮，workflow §4.4 (c)）
Date: 2026-09-22
Implementation snapshot: 候选 = 首次加入 `docs/evidence/P1-ENG-LOOP-001-K1K3-r3-fix.md` 的提交（按其 §1 由
`git log -1 --diff-filter=A --format=%H -- <该文件>` 运行时解析；主题「P1-ENG-LOOP-001 R3@K1K3 返工：F4 watch 显示发布帧号、
F5 告警预览按 query_id 绑定、F6 补丁，直接交 R4@K1K3」），= 本地 `origin/main`，已推送。修复触及行基线 = R3 §0
`round_candidate`（`4914830…`）；两者之间另有接受角色 C2 核对提交与本角色 R3 复核提交（只改状态板、提案、
implementation-status、正式设计、本文件），与修复触及文件零重叠。全量 diff 基线仍 = R2 `passed_candidate`（`9e73509…`）。
**上下文披露**：本轮由 R3 的同一会话执行（用户 2026-09-22 指示「做 R4@K1K3」），不满足细则「新鲜上下文会话」的字面；增量轮
本就要求先读既有轮次，本轮所有结论只依据副本内代码、diff 与本角色重跑，未采用实现者转述。
round_candidate: 737527964a62f7098cbf483ce808458fe0ba1e57
Verdict: PASS_WITH_NOTES
passed_candidate: 737527964a62f7098cbf483ce808458fe0ba1e57

## 0. 检查范围、开轮资格与重跑

- **检查范围（终局轮）** = 冻结集 {F4、F5、F6、F3} + `RED_LINE` + 修复触及行上的 CLASS_1/2；全量 diff 只用于核实声明范围与红绿。
- **修复触及行**：`git diff 4914830…..7375279…` 在本 work item 冻结操作单集合上 = `-operator-watch.py`（+67/−9）、
  `-operations-c.md`（+18/−11）；载体自测 `-c2-carrier-selftest.py`（+132/−4）与其日志（+1/−4，F6 补丁）；新增证据四份
  （`-K1K3-r3-fix.md`、`-tests-r3-fix-{before,after}.log`、`-tests-r3-fix.log`）。`-operator.sh`、`-5060-runner-b.py` 零改动。
  `git diff --stat 4914830…..7375279… -- controller Assets tools tests config ProjectSettings Packages/packages-lock.json` 为空，
  候选树哈希 `HEAD:tests`/`HEAD:controller`/`HEAD:tools`/`HEAD:ProjectSettings` 与 R3 候选逐字相同
  （`ab4081d2…`/`c8683121…`/`8533c6ee…`/`d876cff7…`）。实现者提交 `7375279…` 只含 `docs/evidence/` 九文件与状态板，
  在 R3 §5 [实现] 允许范围内；接受角色 C2 提交只改其白名单文档。
- **开轮资格（workflow §4.4）**：`git diff <上一通过候选 9e73509…>..<候选>` 于 PLAY_GOVERNING 非空（`ProjectSettings/` 1 行、
  R-B1 点名的冻结操作单、COORD-013 的 `tools/check_*.py` 与 `tests/test_check_*.py`）→ 开轮；本停点第 2 次 `REWORK_REQUIRED`
  后的第一轮，即终局。修复直接回复核、不经核对轮，符合 §4.3.1。
- **停点自证核实（§4.3.1 四项）**：条件 1（只动允许文件，合同/K 收据/协议/Unity 设置不变）、条件 2（修前红/修后绿与隔离全套，
  本角色复现见下）、条件 3（无新增 Unity 失败；后台运行效果、首批追平、人眼保真按裁定留待诊断）、条件 4（交接行、候选、风险 §7
  在案；候选已推送）成立 → 开轮。
- **副本**：`git worktree add --detach .claude/worktrees/review-P1-ENG-LOOP-001 7375279…`；同前以只读符号链接补跑冻结资产用例；
  读码、重跑全部在副本内；收工删除。
- **重跑（不信报告数字）**：
  - 载体自测（候选载体）：`python3 docs/evidence/P1-ENG-LOOP-001-c2-carrier-selftest.py <主树 runtime/frames.1b-diagnostic-hold>`
    → 28 项 `ok`、`OK: 0 failed`、退出码 0（= 实现者 `-tests-r3-fix-after.log` 28/0）。
  - 修前红（每条阻断 finding 一次）：同一已提交脚本 `--watch <git show 4914830…:…-operator-watch.py>` → 22 `ok` + 6 `FAIL`
    （`last_published change is printed (F4)`、`straddled alert opens the triggering query's preview (F5)`、
    `a later verify result is not opened as the alert preview (F5)` 与三项加固）、`FAILED: 6 failed`、退出码 1，
    与 `-tests-r3-fix-before.log` 逐名相同。
  - 追加：脚本指向准备批次载体（`1b08fc4…` 的 runner 与 watch）→ 9 `FAIL`，含 `runner: part raised KeyError: 'serve'` 与
    `watch: part raised AttributeError …`——证实新脚本的分部异常捕获使 F6 所指的旧日志形态现在可由已提交脚本产生。
  - 语言 focused：`.venv-language` 四模块 `Ran 260 … OK`，零 skip；协调批次工具 focused `Ran 55 … OK`（两者代码相对 R3 候选零改动）。
  - `lc_check`/`lc_run`：`-operator.sh` 零改动，不重跑，沿用 R3 负向复现。
  - 隔离全套 `-tests-r3-fix.log`（实现者义务，只读核对）：`Ran 1524 / FAILED (errors=9, skipped=68)`、`FAIL:` 0；9 个 ERROR 名与
    `-tests-r1-fix.log` 排序 diff 为空；`## skipped tests` 逐项列出 68 项，含 `RealArchiveClosureTest` 5 项「真实归档不在本工作副本中」
    与冻结资产/Pillow/钉死环境类；被测树哈希与候选相同。新增失败 0 成立；该归档闭合测试在副本内未执行，实现者已如实写明。
  - 输出写会话 scratchpad（`r4-carrier-{green,red,red-prep}.log`、`r4-focused-venv-language.log`、`r4-check-tools.log`），只回显摘要。

## 1. 冻结集逐条闭合核实

**F4 — CLOSED。** 代码：`Watch.on_published(state)` 在每次读到本会话状态时调用（早于 STATE 去重键比较）：记录 `last_published`，
某 `track_id` 的 `last_published_frame_id` 首次非空时打印一行 `PUBLISHED first track=<id> last_published=<帧号>（首批已写出）`
（每段恰一次，`published_tracks` 集合）；10 s 一行的 `sim_t` 行增加 `last_published=<当前值>`；STATE 去重键不变。操作单 §3 T2 行、
§4 第 4 步（首批判据改为出现 `PUBLISHED first` 行，并写明播种瞬间 `last_published=None` 是初始化静音的正常值、可用 T3 `lc status`）、
§5 第 2 步同步。测试：`test_watch_bridge` → `watch: last_published change is printed (F4)`，fixture 经
`controller.language_bridge.tracker_state_payload` + `write_tracker_state` 写两份同键 `TRACKING` 状态（`None` → 57），断言日志含
`PUBLISHED first track=diag-selftest-t1 last_published=57`。四条：(1) 生产写盘函数 ✓；(2) 修前红/修后绿由本角色复现 ✓；(3) 不触及 Play
治理门 ✓；(4) 可机械断言 ✓。

**F5 — CLOSED。** 代码：删除悬挂标志 `open_next_verify`（三文件 grep 无残留）。`on_result` 把每条核验结果按 `query_id` 存入
`verify_results`；`on_state` 首次见到新 `suspect_id` 时建立 `alert`：`lost`/`drift`/`ambiguous` 绑定该状态的 `verification.last_query_id`
（副本内核对 `_handle_verify_outcome`：`last_verify_query_id` 在写结果与写状态之前置为触发查询，且 `_raise_suspect` 的 kind 取自最后
一条 verdict，故触发结果 verdict 与 `TRIGGER_VERDICT[kind]` 恒一致），告警行打印 `触发核验 q=…`；`tracker_failure` 不绑定旧核验，
告警行提示先 `lc verify`。`open_alert_preview` 只在绑定的 `query_id` 已在 `verify_results` 时打开**该**结果的预览（先于或晚于状态读到
均可），每告警至多一次，verdict 与类别不符则不打开并提示 `lc status`；告警期间其他核验结果标「不是告警触发帧」只打印路径；离开
`SUSPECTED` 清除告警。操作单 §3 T2 行、§5 第 3 步同步（按告警行 `query_id` 看预览；`tracker_failure` 先 `lc verify`；标「不是告警触发帧」
的不作依据）。测试：`test_watch_bridge` 用 `language_bridge.result_payload` + `write_result` 与 `tracker_state_payload` +
`write_tracker_state` 按生产顺序（先结果、后状态）写盘，`open` 经替换模块内 `subprocess` 记录：straddle 用例（tick₁ 旧 `TRACKING` +
新结果 Q，tick₂ `SUSPECTED` 且 `last_query_id=Q` → 只打开 Q）、后续核验 R 不打开、告警先于结果读到时到达即打开、`tracker_failure`
不打开旧核验并提示 `lc verify`、verdict 不符不打开、fixture 目录只有两个桥文件。四条 ✓（修前红/修后绿由本角色复现）。
AC-13 修订 1「提示绑定核验源帧副本与 `query_id`」在操作层成立。

**F6 — 补丁已按 R3 §3 逐字应用**（`git diff` 显示删除四行、新增一行与补丁文本逐字相同，其他行未动）；根因随脚本改造消除。

**F3**（`SCOPE_GAP`，账本 2026-09-22 `OPEN`）：`LanguageWorker` 未触及（`controller/` 树哈希同 R2），状态不变，不阻断。

## 2. 修复触及行核查（新阻断唯一来源；结论：无 CLASS_1/2）与 RED_LINE

- 坐标/单位/时间戳/帧绑定：watch 不做任何过期或帧判断，只呈现；绑定键改为 `query_id`，与会话镜像语义一致。
- 边界与失败路径：`alert["query_id"]` 为 `None`（`tracker_failure`）时 `None not in verify_results`（键均为字符串，`tick` 已过滤
  `query_id` 不以 `<session>-q` 开头的结果）→ 不会进入 `TRIGGER_VERDICT[...]`；同一 `suspect_id` 不会在离开 `SUSPECTED` 后复现
  （`_suspect_sequence` 递增）；watch 重启中途的告警由「结果到达即打开」覆盖；`verify_results` 上界为每次 Play ≤40 条。
- 并发/原子性：watch 仍只读 `runtime/`，只写 `<opdir>/`；两桥文件的读取时序问题正是本修复对象，straddle 用例覆盖。
- 真值泄漏：无（不接触帧/评估器/控制器）。`RED_LINE`：无；人眼保真检查在首次正式采集前由操作单 §4 第 6 步承担，尚未到时点。
- 测试真实覆盖：fixture 走 `language_bridge` 真实写者与校验；`open` 被记录而非执行（实现者 §7 已披露，真实可见性只有诊断能证实）。
- 文档一致性：操作单与 watch 行为逐条相符；`-K1K3-r3-fix.md` 叙述与 diff 相符；本轮未发现数字/阈值/ID 变动。

## 3. Findings

### Blocking

无。冻结集 F4/F5 闭合、F6 已应用、F3 记债不阻断；修复触及行无 CLASS_1/2；无 `RED_LINE`。

### Non-blocking

无新 finding。

## 4. 非阻断注记（不是 finding，不带依据列）

1. `tracker_failure` 告警期间操作者按操作单 `lc verify` 后，该结果行打印「该核验不是告警触发帧（告警 q=None），不自动打开；预览：file://…」——
   措辞对无触发核验的告警略生硬，但路径已打印、操作单 §5 第 3 步已写明点该路径，操作者动作不受影响。
2. 冻结集裁定（R3 §5 [接受]）在本轮开轮时尚未写入提案（`git diff b60f820…..7375279… -- docs/proposals` 为空）；本轮以红绿把 F4/F5
   闭合、F6 已应用，剩余待裁定项只有 F3（已在账本 `OPEN`）与 R3 注记 2（归档闭合测试对 `runtime/` 残留敏感的处置），接受角色消费本轮
   时一并裁定即可。
3. 本轮通过后 `_lc_candidate` 解析到本候选：采集 worktree `~/TetheredDroneTracking-loop-b-capture` 现停在 `9e73509…`，
   须先 `checkout --detach` 到本候选，主树 `Assets config ProjectSettings Packages` + 四冻结文件相对本候选已零差异（后续文档提交不
   触及），再按操作单 §1 重建 5060 清单（脚本从复核文件最后一条 `passed_candidate` 解析）并传输 runner/清单，`amend` → `preflight`。
4. R3 注记 1（`lc_check` Unity 进程检查的正向路径）与注记 5（`lc_run` 管道退出码）不变；首次真实 `lc_check` 输出须原样入 prep 文件。
5. 隔离副本全套的 skip 从主树的 24 升到 68，全部为「资产不在副本」或「解释器无 Pillow」类，已在日志逐项列名；不构成对归档闭合的正向证据，
   实现者已写明。

## 5. Verdict 与交接

- **`PASS_WITH_NOTES`**：K1K3 停点在单字段 + 冻结操作单候选上独立复核通过；通过候选 = 本节抬头 `passed_candidate`。AC-4 修订 3、
  AC-12 修订 3 改判**满足**（操作单与载体呈现缺陷已闭合）；AC-11 沿用 R3 结论（隔离副本新增失败 0）；AC-1…10/16/17 沿用 R2；
  AC-13…15 待阶段 B 真实 Play。K1K3 C/R = 2/4（C 退回 0、R 返工 2），终局通过。
- [接受] 消费本 verdict；冻结集收尾（F3 保持账本 `OPEN`；R3 注记 2 的归档闭合测试处置裁定）；随后按操作单 §1/§2 交实现对齐采集
  worktree、重建/传输清单、`amend`，再由用户按 R-B4 用 `diag-loopb-3` 做新增诊断（持续供帧 → 首批追平 → 人眼保真），产物不进
  AC-13…15。消耗性交接由接受角色在 Active handoffs 声明。
- [用户] 本轮零消耗；新增诊断 0/2 与正式 Play 0/8 不变。

## `UNITY_NA` 附议

本工作项**不申请** `UNITY_NA`（提案 §4 与 Gate board 行同）。本轮无附议对象，不附议、不反对；AC-13…15 仍是 `DONE` 的必要证据。
通过本停点不等于 `DONE`，也不推定 `runInBackground` 修改已生效。

## 6. 边界自查（R4@K1K3 收工）

- 本会话未修改任何实现文件：`controller/`、`Assets/`、`tools/`、`tests/`、`config/`、`ProjectSettings/`、`docs/evidence/` 零改动；
  修前红用 `git show` 到 scratchpad 的旧载体经 `--watch`/`--runner` 参数运行，副本内未检出任何文件；副本 `outputs` 只读链接随副本删除。
- 主树本批写入：`docs/reviews/P1-ENG-LOOP-001.md`（追加本节）与 `docs/current-status.md`；
  `python3 tools/check_role_writes.py --role review` 与 `python3 tools/check_docs.py` 结果记在状态板 Log。
- 零消耗：未启动模型/服务/Play、未下载、未创建 scenario/session/run ID、未向 5060 传输、未触碰真实 `runtime/`。

---

# R5@K1K3 — 本地按钮操作页 / runner 修订4 迁移 / 操作单 C 修订候选（C3→C4@K1K3 → R5）

Reviewer/role: 复核角色 / independent verification（新鲜上下文会话，Fable 池；档位不低于实现者）
Workflow: engineering-v1（同 R1…R4；依据列沿用 workflow §4.4 六值闭集，`BC-n` 读作合同 `AC-n`）
Round: R5@K1K3
Date: 2026-09-23
Implementation snapshot: 候选 = C4 核对提交之前最后修改 `docs/evidence/P1-ENG-LOOP-001-K1K3-c3-handoff.md` 的提交（按其 §1 由
`git log -1 --format=%H -- <该文件>` 运行时解析；主题「P1-ENG-LOOP-001 K1K3 候选（C3 后替换）：修 C3-1…3，交 C4@K1K3（零消耗）」），
是本地 `origin/main` 的祖先；主树 HEAD 在其后一笔（接受角色 C4 核对提交，只改状态板/提案/implementation-status）。上一通过候选 =
R4 `passed_candidate`（`7375279…`），上一复核轮候选 = R4 `round_candidate`（同一提交），两条基线重合：全量 diff = 修复触及行 =
`git diff 7375279…..e78f470…`，13 笔提交、20 文件（+3,867/−240）。
round_candidate: e78f470aaa4e7c50dcaf93ee6fbfe6f0bc7d54db
Verdict: REWORK_REQUIRED

## 0. 复核范围、停点资格、开轮资格与重跑

- **轨道与停点**：不变（提案抬头逐字 `Workflow: engineering-v1`、D4 `ACCEPTED` 裁定生效）。本候选不是 R4 的返工，而是 R-B5…7 裁定
  （AC-18 新增、AC-12 修订4/5）派生的同停点新候选，经 C3@K1K3（其间按用户选择替换一次修 UI-1…4）与 C4@K1K3（按用户选择修 C3-1…3）后
  交本轮；C/R 计数沿用，本轮为 R5。合同 = §1…8、AC-1…18、八行首次释义、十四行实现期修订（P-A-1…8、P-B-1/2、R-B1…4 的 AC-4/12 修订3、
  R-B5…7 的 AC-18 与 AC-12 修订4/5），冲突处以后者为准。
- **停点自证核实（workflow §4.3.1 四项）**：条件 1（范围/接口冻结：`controller/ Assets/ tools/ tests/ config/ ProjectSettings/
  Packages/packages-lock.json` 相对 R4 通过候选 `git diff --stat` 为空，本角色现算；候选树哈希 `HEAD:tests`/`controller`/`tools`/
  `ProjectSettings` = `ab4081d2…`/`c8683121…`/`8533c6ee…`/`d876cff7…` 与 R3/R4 候选逐字相同；K 收据、桥协议、闭集零改动；页面只用
  会话已写的只读数据，没有回 Pending rulings 的缺字段）、条件 2（相称测试：载体自测 90/90 与四组旧载体红跑由本角色复现，停点全套隔离
  副本日志逐名核对，见下）、条件 3（本批不触及 Unity，无待修 Unity 失败；后台供帧/首批追平/人眼保真按裁定留待诊断）、条件 4（状态板
  交接行、候选解析规则、风险 §4、复核范围 §5 在案；候选已推送）按字面成立 → **开轮，不给 `REVIEW_BLOCKED`**。
- **开轮资格（COORD-007 R1 / workflow §4.4）**：`git diff 7375279…..e78f470…` 于 PLAY_GOVERNING 非空——R-B5 点名的本项冻结操作单集合
  六文件：`docs/evidence/P1-ENG-LOOP-001-{operations-c.md（242 行）,operator.sh（205）,operator-watch.py（335）,operator-web.py（新，1,184）,
  5060-runner-b.py（235）,build-stage-b-manifest.py（102）}` → 开轮。Play 治理门三文件（`tools/analyze_m3_body.py`、
  `tools/preflight_reanchor_env.py`、`controller/run_log.py`）零改动。本停点交接 `Consuming=no`，无 `blocks_consuming_gate` 行。
- **增量轮范围（COORD-009 (b)）**：两条基线重合，本轮"修复触及行" = 全量 diff；六个冻结文件（含整份新文件）都在触及行内，其上的
  CLASS_1/2 是本轮合法新阻断来源。本轮不是 R3 之后的终局轮（R4 已终局通过）；C4 核对表与 R-B5…7 裁定逐字写明「原冻结集与终局限制不重置，
  不授予新返工配额；若新轮不能通过，交用户裁定，不自行循环」，处置见 §5。
- **副本**：`git worktree add --detach .claude/worktrees/review-P1-ENG-LOOP-001 e78f470…`；副本无 `runtime/`、`outputs/`；载体自测的
  帧目录以主树 `runtime/frames.1b-diagnostic-hold` 只读传入；读码、重跑、探针全部在副本内，只写临时目录与会话 scratchpad；主树实现文件
  只读；收工删除副本。
- **重跑（不信报告数字）**：
  - 载体自测（候选载体）：`python3 docs/evidence/P1-ENG-LOOP-001-c2-carrier-selftest.py <主树 runtime/frames.1b-diagnostic-hold>`
    → 90 项 `ok`、`OK: 0 failed`、退出码 0（= 实现者 `-c3-carrier-selftest.log` §2）；含两次真实 CLI 子进程往返（回执 `APPLIED`；
    5 s 无回执 → 结果未知）与一次真实外层超时。
  - 红跑（非空性；`git show` 旧载体到 scratchpad，经 `--web/--runner/--watch` 指向）：C3 所核对候选的 `-operator-web.py` → 4 FAIL
    （C3-2 两项、日志连带一项、C3-3）；C3 所核对候选的 runner → 1 FAIL（C3-1）；R4 通过候选的 runner → 10 FAIL；R4 通过候选的 watch →
    3 FAIL。四组与实现者日志 §3 逐名相同。
  - 语言 focused：`TMPDIR=/private/tmp .venv-language/bin/python -m unittest tests.test_language_bridge tests.test_language_selector
    tests.test_language_loop tests.test_language_k_binding` → `Ran 260 … OK (skipped=2)`；2 skip = 冻结资产不在副本；被测树哈希与 R4
    候选逐字相同、R4 已零 skip 执行，本轮不再补链接。
  - 停点全套 `-tests-c3.log`（实现者义务，只读核对）：首行树哈希 = 候选；`Ran 1524`、`FAIL:` 0；9 个 `ERROR:` 名与
    `-tests-r3-fix.log` 排序 diff 为空；`## skipped tests` 68 项排序 diff 为空 → 新增失败 0。`RealArchiveClosureTest` 5 项仍 skip，
    不作归档闭合证据（接受裁定）。
  - `-build-stage-b-manifest.py` 的拒绝路径只读核对日志 §4，未重跑（重建须待新的通过候选）。
  - C4-1 探针（副本、临时目录、自测夹具 + StubCli）：见 §3 F7。
  - 输出写会话 scratchpad（`r5-carrier-green.log`、`r5-carrier-red-{c3-web,c3-runner,r4-runner,r4-watch}.log`、
    `r5-focused-venv-language.log`、`r5-c4-1-probe.{py,log}`），上下文只回显摘要，不带 `-v`。
- **直接关联冻结代码**（只读，候选与 R4 同字节）：`language_loop.py` `main`（退出码 0 = 有回执、5 = 无回执、4 = `WRITER_BUSY`、
  2 = 守卫/文法拒绝；`status` 只读）、`send_request`（5 s 等待、超时只释放锁并报「结果未知」、死锁接管回调）、`build_parser`（九个请求
  子命令的参数名与 `--allow-shared-runtime`）、`_consume_request`（同 id 重新写入 → `IGNORED_DUPLICATE` 恰一次）、`_receipt`/`_journal`
  （`kind=receipt` 行带 `session_id` 与 `receipt.request_id`）、九个 `_action_*` 守卫（`respecify` 在 `SUSPECTED` 不要令牌并先 finalize、
  `verify` 在 `SUSPECTED` 允许、`backend_fatal` 只许 `stop`）、`_check_confirmation`（累计帧差 `K_ret+K_conf`、查询起 `T_ret+T_conf`、
  呈现窗口 `T_conf`）、候选呈现顺序（`_emit_result` 写结果槽与 `results.jsonl` **之后**才置 `candidate_presented_monotonic_s`）、
  `_publish_state`（`since_unix_s`、`verification.last_query_id`/`in_flight_query_id`、`last_published_frame_id`）、`_run_session`
  （诊断 `run_root`）、`language_bridge.{tracker_state_payload,result_payload,read_result,read_tracker_state}`、`protocol.packet`
  （`issued_unix_s`）；`gated_publisher` 收据 `detail` 的 `frame_delta`/`load_elapsed_s`/`capture_age_s`（操作单 §4 第 7 步所引）；
  归档帧元数据含 `capture_unix_s`（页面帧新鲜度所依）。

## 1. 逐条 AC 核对（只列本候选触及或 C4 核对表提问的条款；其余沿用 R2/R4）

| 编号 | 结论 | 本轮核实 |
|---|---|---|
| AC-18 | **不满足（F7）** | 本机 `127.0.0.1`、标准库、内嵌页面、无下载（`HOST`、`PAGE`、只 import 标准库；HTTP 用例：无 nonce / 外来 `Origin` / 错 `Host` 一律 403，预览只按名从本会话 `previews/` 取）；状态、绑定 `query_id`/源帧的候选与核验预览、确认剩余时间均在；动作闭集九项，`legal_actions` 表与 `_action_*` 守卫逐态相符（`backend_fatal` 只 `stop`、`TERMINAL` 无按钮；`IDLE` 的 `respecify` 以 `results.jsonl` 出现过 designate 为条件，与会话「有可沿用指令」等价）；每次点击 = 采集 worktree 一条 `python -m controller.language_loop <action> … --allow-shared-runtime`（cwd = worktree），不写桥/请求/锁（自测「wrote nothing into the runtime」）；身份绑定：服务端重读桥文件后比较 posted view 七键，令牌只取 posted view，旧页面拒绝、不换绑；预览缺失/不符/非 PNG/未在浏览器显示成功 → 不可确认且不发送；F5 绑定与后到核验不替代；倒计时取 `query_unix_s+T_ret+T_conf` 与结果信封 `issued_unix_s+T_conf` 较早者并显示累计帧差门，`issued_unix_s` 早于会话置呈现时刻（保守），轮询/刷新/重启不续期，页面计时归零只置灰不发送、无事件；防重复（busy 锁 + 1.5 s 同键窗口）；未知/超时按 `request_id` 逐条保留、同 id 重试沿用 argv/令牌、迟到回执按 id 从会话 JSONL 关联；点击/拒绝/重试/迟到回执写 `<opdir>/operator-web.jsonl`；`APPLIED` 文案不冒称播种/发布；页面模式 watch 不弹窗、CLI 后备保留；桥/结果/会话日志/预览走生产写者。**但**同 id 重试遇 `WRITER_BUSY`（或任何非 0/5/超时退出）即删除该「结果未知」条目，同视图同动作守卫与迟到回执关联随之丢失（F7 = C4-1 属实）。真实浏览器呈现/点击与人眼检查按合同留获准诊断，本轮未做。 |
| AC-12 修订 4 | 满足 | runner：`DIAG_AMENDMENTS` 两条；`recorded_amendments` 保留 rev3 原位（`diag_amendment`）、后续入 `later_diag_amendments`；`amend` 只在缺最后一条时追加一次并写事件，重复不加额，缺/改 rev3 断言拒绝且不写盘、不重建；`serve` 要求两条 id 齐全；`session_refusal` 冻结集 = 全部修订 `diag_sessions_before` 并集，新标签白名单（旧号含账本从未见过的零查询 `diag-loopb-1` 拒 `session_label:diag`），第 4 个新号拒绝，正式 8 / 每会话 40 / 总 400 / 启动 10 不变；`open_ledger` 在模块入口任何写盘前拒绝缺账本（退出码 2，不建目录、不建零账本；C3-1）；清单脚本从候选 git 对象取 runner，工作树不同即拒绝生成。自测 runner 20 项由本角色复现，旧 runner 红 10 / 1。F 盘实际迁移与传输**未执行**（R5 通过后按操作单 §1），本轮不冒称已迁移。 |
| AC-12 修订 5 | 满足 | 操作单 C：文首「这一阶段验证什么」；§0 额度表含第二次追加 3 次与固定标签 `diag-loopb-5…7`、Play 登记与服务端账本分列；§3「确认时效」三门（结果出现起 ≤10 s、查询起 ≤16 s、帧差 ≤80，与 K 收据 30/50、5 Hz 一致）并明写不是「候选出现后还有 16 s」、无自动过期、只有合法 `confirm` 触发时效检查；§4 先供帧后 ask、时间窗标为推算且不进控制/感知/自动触发；watch 候选行同句（自测）。 |
| AC-13 修订 1（操作层） | 沿用 R4；页面同样绑定 | 页面 `_alert` 按首见 `suspect_id` 时的 `verification.last_query_id` 绑定，verdict 与类别不符不显示并提示 `lc status`；结果按 `query_id` 从 `results.jsonl` 取，不依赖单槽读序；UI-4 按核验发起时刻标「告警前参考 / 告警后核验」。真实 Play 证据仍缺。 |
| AC-1 修订 1 / AC-17 修订 1 | 沿用 R2/R4 | 页面不自动换 id 重发，同 id 重试由会话去重（`_consume_request` 未改）；合法动作表与状态表相符。 |
| AC-4 修订 3 / AC-11 | 沿用 R4；AC-11 本候选满足 | Unity 路径与冻结 SFT 工具零差异（本角色现算）；停点全套逐名核对见 §0。 |
| AC-2…10 / AC-16 | 沿用 R2/R4 | 运行时零改动（树哈希相同）。 |
| AC-13 / 14 / 15 | 未到证据时点 | 正式 Play 0；不申请 `UNITY_NA`。 |

## 2. 全量 diff 逐文件处置（20 文件）

- **A 本批 PLAY_GOVERNING（冻结操作单集合 6）**：六文件全文读毕（新文件整份、其余按 diff + 全文）；F7 在 `-operator-web.py`。
- **B 本批自测/证据**：`-c2-carrier-selftest.py`（+923：runner 迁移 20 项、watch 页面模式、web 60 余项、真实 CLI 与真实超时）、
  `-c3-carrier-selftest.log`（绿/红复现）、`-tests-c3.log`（逐名核对）、`-K1K3-c3-handoff.md`（自证四项与逐 AC 指针核实）、
  `-stage-b-prep.md` §8/§9（§8 是 R4 之后本批之前的诊断 3/4 记录，如实读毕；§9 为本批落实叙述）。
- **C 诊断 3/4 前按 R4 候选产生的执行工件**：`-service-5060-b.log`（+启动 3 段）、`-transfer-manifest-5060-stage-b.json`（`passed_candidate`
  = R4 候选、runner `3120e516…`）：不属本批实现；新 runner 的清单须 R5 通过后重建（C4 已注，§4 注记 8）。
- **D 其他角色文档**：`docs/{authorizations,current-status,implementation-status,unity-test-log,phase1-single-drone-design}.md`、提案、
  本复核文件：读 diff；设计 v0.3.48 只加 R-B5…7 指针；授权账本「本地按钮操作页与追加三次诊断」逐字在案，本批范围与之一致。

## 3. Findings

### Blocking

**F7 — 同 `request_id` 重试遇 `WRITER_BUSY`（或任何非 0 / 5 / 超时的退出）时，页面删除该「结果未知」条目：同视图同动作守卫消失、迟到回执
不再关联，操作者随后再点原按钮会以新 `request_id` 重发。** CLASS_2 · 依据列 `BC-18`（读作 AC-18「未知/超时结果遵循 AC-1 修订 1，不自动换
request_id 重发；记录点击/回执」与 C3-2 已接受语义「各自守卫同视图的同一动作、各自同 id 重试、迟到回执只解除对应一条」；AC-1 修订 1 点名
`WRITER_BUSY` 与「同 ID 重试由会话去重」）· 范围判据：可达——触发状态 = 一条结果未知的请求 + 重试时另一 CLI 写者持锁。操作单 §3 保留终端
`lc`（T4）为后备并写明「停止也要等它结束（终端 lc stop 同样要等写者锁）」，页面与终端并用是操作单预期的生产路径；任一 `lc` 与页面重试落在
同一 5 s 写者窗内即触发。= C4 预复核关注项 C4-1，本角色核实属实。
- 位置：`docs/evidence/P1-ENG-LOOP-001-operator-web.py` `App._run`（`with self.pending_lock:` 下 `if receipt is None and (timeout or
  exit in {0, 5})` 保留条目，`else: self.unknowns.pop(request_id, None)`）；`App._retry`（不先 `resolve_late_receipts()`、不核当前视图即
  调 `_run`）；`interpret`（exit 4 → 「写者锁忙…本次未写入」，receipt `None`）。
- 代码事实（副本内读冻结 CLI）：退出码 4 只证明**这次重写**没有写入（`main` 捕获 `WriterBusy` 直接返回 4，`send_request` 未写请求、
  未等回执）；原请求 A 是否已被会话消费（`APPLIED`/`REQUEST_INVALID`）或仍在槽内待消费，页面无从得知，只有会话 JSONL 的 `receipt` 行能
  回答；`unknowns.pop` 之后 `resolve_late_receipts` 不再查该 id，`_click` 的 `same` 守卫不再命中，`paintButtons` 恢复原按钮。退出码 1
  （CLI 异常）走同一路径。
- 探针（`r5-c4-1-probe.py`，副本临时目录，自测既有 `Fixture` + `StubCli`）：A = `verify` exit 5 → 未知条目 `[A]`；同 id 重试 stub
  exit 4 → `unknowns == []`；再点同视图 `verify` → 未被拒绝，以新 `request_id` 发出（CLI 调用计 3 次）；随后经
  `LanguageSession._journal` 写 A 的 `APPLIED` 回执 → 页面不显示「迟到回执」。三项均与候选自测宣称的 C3-2 语义相反。
- 后果：阶段 B 中 `verify` 可被双发（多耗查询，每次 Play ≤40）、`ask`/`respecify` 双发（新 epoch 替换在途查询，耗尝试与查询）；
  `confirm-lost`/`dismiss`/`stop` 双发只得 `REQUEST_INVALID`/`IGNORED_*`。无控制副作用，但操作者判断「A 到底执行没有」的依据被删除，
  与 AC-18 / AC-1 修订 1「不能宣称未执行」相悖。
- 闭合要求（workflow §4.4 四条）：(1) fixture 经自测既有 `Fixture`（桥/会话文件走 `language_bridge` 写者与 `LanguageSession._journal`），
  CLI 用 `StubCli` 返回 exit 4（另补 exit 1 一例）；(2) 具名回归修前必红，例如 `check("web: a same-id retry refused by WRITER_BUSY keeps
  the unknown entry, its guard and its late-receipt match (F7)", …)`：重试 exit 4 后 `pending_list(app) == [A]`、同视图同动作被拒且不调 CLI、
  A 的迟到回执经 `Fixture.receipt` 到达后被关联显示；(3) 不触及 Play 治理门；(4) 可机械断言。实现建议（不构成义务）：`_run` 只在拿到
  回执时移除条目，其他结果保留并把本次重试的退出码/文案记进该条目（页面框内显示「上次重试：写者锁忙」）；`_retry` 开头先
  `resolve_late_receipts()`，已解决即拒绝重试并显示原回执。只改 `-operator-web.py` 与 `-c2-carrier-selftest.py`（必要时操作单 §3 一句），
  不改 `controller/`、`tools/`、`tests/`、`config/`、`Assets/`、`ProjectSettings/`。

### Non-blocking

**F3**（R1，`SCOPE_GAP`，账本 2026-09-22 `OPEN`）状态不变：`LanguageWorker` 未触及。

## 4. 非阻断注记（不是 finding，不带依据列）

1. **重试先于迟到回执被读到**（A 已被会话消费，页面尚未从 JSONL 读到回执；窗口 ≤ 300 ms 轮询）时，重试得 `IGNORED_DUPLICATE` 并移除条目，
   页面只显示「已处理过」而不显示 A 的原回执（`APPLIED` 还是 `REQUEST_INVALID`）；建议随 F7 一并在 `_retry` 先解析迟到回执。同一路径，不单列。
2. **边界处页面放行、会话拒绝**：帧差门与截止在轮询时刻（≤ 0.1 s 前）评估，点击到会话受理约 0.3–0.5 s（实现者 §4 第 3 条）；会话按
   `_check_confirmation` 拒绝时依 §3.4 记 `stale_rejected`、候选作废（`IDLE` 或 `REINIT_REQUIRED(candidate_expired)`）。这是合同行为
   （页面只提示、会话最终检查），操作单 §3 已写「来不及就驳回或重新指定，不要赶」；不作 finding。可在操作单提醒剩余 < 1 s 或帧差 ≥ 78 时
   不点确认（非义务）。
3. 自测 `Fixture.frame` 手写 `latest.json` 与帧元数据（页面只读 `frame_id`/`simulation_time_s`/`capture_unix_s`）；帧的生产写者是 Unity，
   Python 侧 `FixtureFramePublisher` 亦是夹具；桥、结果、会话日志、预览均走生产写者，AC-18「fixture 调用生产写盘函数」在可用范围内成立。
4. 页面在告警期间启动时的绑定沿用 watch 限制（R4 §1）：绑定当时 `last_query_id`，verdict 不符即不显示并提示 `lc status`。
5. 操作单 §3「本机服务读不到会话文件时页首红色横幅」：`tracker_state.json` 尚不存在时页面只显示「等待会话写出 tracker_state」且无按钮
   （无横幅）；文件不可读/损坏才有横幅。两种情形都不能确认，操作者动作不受影响，不作 finding。
6. 浏览器端行为（图片 load/error 门、断连置灰、在途仍刷新）只有页面源码断言；AC-18 明写留获准诊断，本轮未开浏览器。
7. 语言 focused 在副本 2 skip（冻结资产不在副本），被测树哈希与 R4 候选相同。
8. 本轮通过后须按操作单 §1 重建/传输清单并在 5060 执行 `amend`；当前入库清单仍指向 R4 候选的 runner（C4 已注）。`_lc_candidate` 在本轮
   之后仍解析到 R4 通过候选，主树/采集树含按钮页与新 runner 即 `lc_check` 必 FAIL，Play 与 5060 服务启动继续被机械阻止。
9. C4-1 经本角色核实为 F7；C4 未放过它，不计 `上游漏检`。

## 5. Verdict、计数与交接

- **`REWORK_REQUIRED`**（K1K3 第 3 次：R1、R3、R5）。本停点 `REWORK_REQUIRED` 已达每停点 2 次上限（workflow §4.4 (c) / COORD-009 (c)），
  R4 已是终局轮；C4 核对表与 R-B5…7 裁定逐字写明「原冻结集与终局限制不重置，不授予新返工配额；若新轮不能通过，交用户裁定，不自行循环」。
  因此本轮**不向实现角色派发返工**：未闭 finding 集冻结 = {F7（CLASS_2，`BC-18`）、F3（`SCOPE_GAP`，账本 `OPEN`）}，交接受角色按
  §4.4 (b)(c) 处理并回用户裁定。K1K3 C/R = 4/5、C 退回 0、R 返工 3（超上限 1；本轮计入，不构成新配额）。
- 本轮无 `passed_candidate`；无 `blocks_consuming_gate` 行（交接 `Consuming=no`，F7 在触及行上，不属未改动行的 `上轮漏检`）。
- [接受/用户] 可选处置（由用户裁定，本角色不预判）：(a) 用户授权本停点一次超限返工（限 F7 闭合，逐字入账），实现修复后直接交新鲜上下文
  R6@K1K3，R6 只查 F7 闭合红绿 + 修复触及行上的 CLASS_1/2 + `RED_LINE`；(b) 接受角色按 §4.4 (b) 对 F7 的分级或范围判据提复判（若认定
  页面与终端 `lc` 并用属可由操作纪律禁止的路径而改标 `SCOPE_GAP`，须在操作单明令禁止并用并记债）；(c) 关闭本范围为 `CLOSED_*`（不等于通过）。
  任一处置落地前不开 Play、不启动 5060 模型服务、不执行账本迁移与传输。
- [实现] 本轮不派发；F7 闭合要求见 §3，供处置后使用。
- 零消耗：未启动模型/服务/Play、未下载、未创建 scenario/session/run ID、未向 5060 传输、未触碰真实 `runtime/`。

## `UNITY_NA` 附议

本工作项**不申请** `UNITY_NA`（提案 §4 与 Gate board 行同）。本轮无附议对象，不附议、不反对；AC-13…15 仍是 `DONE` 的必要证据。

## 6. 边界自查（R5@K1K3 收工）

- 本会话未修改任何实现文件：`controller/`、`Assets/`、`tools/`、`tests/`、`config/`、`ProjectSettings/`、`docs/evidence/` 零改动；
  副本内未检出任何文件（红跑用 `git show` 到 scratchpad 的旧载体经 `--web/--runner/--watch` 运行）；探针只写临时目录与 scratchpad；
  副本 `git status --porcelain` 干净后删除。
- 主树本批写入：`docs/reviews/P1-ENG-LOOP-001.md`（追加本节）与 `docs/current-status.md`；
  `python3 tools/check_role_writes.py --role review` 与 `python3 tools/check_docs.py` 结果记在状态板 Log。

# R6@K1K3 — 用户授权的一次 F7 定向超限返工（R5 → R6，不经核对轮）

Reviewer/role: 复核角色 / independent verification（新鲜上下文会话；模型 Claude Opus 5.5，与实现者同档——实现提交 trailer 为 Opus 5.5——
不低于实现者、不是最便宜档；R5 用 Fable 池，本会话未能确认 Fable 池此刻是否可用，按 docs/roles/review.md「降到与实现者同档」披露，
是否接受由接受角色/用户判断）
Workflow: engineering-v1（同 R1…R5；依据列沿用 workflow §4.4 六值闭集，`BC-n` 读作合同 `AC-n`）
Round: R6@K1K3
Date: 2026-09-23
Implementation snapshot: 候选 = 首次加入 `docs/evidence/P1-ENG-LOOP-001-K1K3-r5-fix.md` 的提交（按其 §1 由
`git log -1 --diff-filter=A --format=%H -- <该文件>` 运行时解析；主题「P1-ENG-LOOP-001 R6@K1K3 候选（R5/F7 定向返工）…」），是本地
`origin/main` 的祖先，开轮时即主树 HEAD。上一复核轮候选 = R5 `round_candidate`（`e78f470…`）；上一通过候选 = R4 `passed_candidate`
（`7375279…`）。修复触及行 = `git diff e78f470…..7ef8cc0…`：5 笔提交、11 文件，其中实现文件仅 `docs/evidence/` 下三个
（`-operator-web.py`、`-operations-c.md`、`-c2-carrier-selftest.py`，+195/−16）加三份新证据；其余为 C4/R5/接受裁定/授权入账提交所改
`docs/{authorizations,current-status,implementation-status}.md`、提案与本文件。
round_candidate: 7ef8cc0f87348b86ccd7f815aa1c3e3a3c9f55e5
Verdict: PASS_WITH_NOTES
passed_candidate: 7ef8cc0f87348b86ccd7f815aa1c3e3a3c9f55e5

## 0. 复核范围、授权、开轮资格与重跑

- **授权与范围**：`docs/authorizations.md` 2026-09-23「R5/F7 一次定向超限返工」逐字在案（用户原话「授权一次定向返工」）；提案 Acceptance
  rulings R5/F7 两行一致。本轮范围按授权 = F7 闭合红绿 + 修复触及行上的 CLASS_1/2 + `RED_LINE`；不经 C5；不通过则回用户，不自动 R7。
  冻结集 {F7、F3}：F3 仍为 `SCOPE_GAP`（账本 `OPEN`），不在本轮闭合义务内。
- **停点自证（workflow §4.3.1 四项）**：条件 1（`controller/ Assets/ tools/ tests/ config/ ProjectSettings/ Packages/packages-lock.json`
  相对 R5 `round_candidate` 与 R4 `passed_candidate` 的 `git diff --stat` 均为空，本角色现算；树哈希 `tests`/`controller`/`tools`/
  `ProjectSettings` = `ab4081d2…`/`c8683121…`/`8533c6ee…`/`d876cff7…` 与 R3/R4/R5 候选逐字相同；Play 治理门三文件零改动）、条件 2（载体
  自测与红跑由本角色复现，停点全套日志只读逐名核对，见下）、条件 3（本批不触及 Unity）、条件 4（交接行、候选解析规则、复核范围 §9、
  已知限制 §8 在案，候选已推送）按字面成立 → **开轮，不给 `REVIEW_BLOCKED`**。
- **开轮资格**：`git diff 7375279…..7ef8cc0…` 于 PLAY_GOVERNING 非空（R-B5 点名的冻结操作单集合中的 `-operator-web.py`、
  `-operations-c.md`）→ 开轮。本停点交接 `Consuming=no`，无 `blocks_consuming_gate` 行。
- **副本**：`git worktree add --detach .claude/worktrees/review-P1-ENG-LOOP-001 7ef8cc0…`；副本无 `runtime/`、`outputs/`；帧目录以主树
  `runtime/frames.1b-diagnostic-hold` 只读传入；读码、重跑、探针全部在副本与临时目录，只写会话 scratchpad；副本 `git status
  --porcelain --untracked-files=all` 全程为空；收工删除。
- **重跑（不信报告数字；输出写 scratchpad `r6/`，只回显摘要，不带 `-v`）**：
  - focused（本批改动的 focused 套件 = 载体自测）：`python3 docs/evidence/P1-ENG-LOOP-001-c2-carrier-selftest.py <帧目录>` → 99 `ok`、
    `OK: 0 failed`、退出码 0（= 实现者 `-r5-fix-carrier-selftest.log` §2）。测试树哈希见上；语言 focused 被测树与 R5 逐字相同，未重跑。
  - F7 红绿：同一份已提交自测加 `--web` 指向 `git show e78f470…:docs/evidence/P1-ENG-LOOP-001-operator-web.py`（即只撤销本批按钮页修复，
    等价于在副本 `git revert -n` 该文件）→ 8 `FAIL`、退出码 1，含具名回归「web: a same-id retry refused by WRITER_BUSY keeps the unknown
    entry, its guard and its late-receipt match (F7)」与「…exits 1 (CLI error)…(F7)」；修后同名两项 `ok`。与实现者日志 §3.1 逐名相同。
  - 本角色独立探针 `r6-f7-probe.py`（17 项；夹具复用自测 `Fixture`，回执经 `LanguageSession._journal`，桥/状态经 `language_bridge`
    生产写者）：P1/P2 用**真实冻结 CLI 子进程**（`web.CliRunner` → `python -m controller.language_loop verify …`，无会话消费 → 5 s 后
    exit 5；本进程以活 pid 持写者锁 → 真实 `WriterBusy` → exit 4）。修后 17/17 绿；对修前按钮页 12 红（P1 的 R5 原场景三项全红：
    重试后条目丢失、同视图再点以新 id 发出、A 的迟到回执不再关联）。其余探针覆盖实现者自测未点名的分支：重试超时、重试 exit 2、
    重试前读取失败、`IGNORED_DUPLICATE` 而日志无原回执、`_read_logs` 覆盖规则（`PENDING_QUEUED`→重复→`SUPERSEDED` 仍以
    `SUPERSEDED` 结束、首见的重复照记）、两条未知中一条重试锁忙、新点击 exit 1/超时/3 留未知与 exit 2/4 不留。
  - 页面内嵌脚本抽出后 `node --check` 通过（新增行含嵌套模板字符串）。
  - 停点全套 `-tests-r5-fix.log`（实现者义务，只读核对）：首行树哈希 = 候选；`Ran 1524`、`FAIL:` 0；9 个 `ERROR:` 名与 `-tests-c3.log`
    排序 diff 为空；`## skipped tests` 排序 diff 为空（68）→ 新增失败 0。
- **直接关联冻结代码**（只读，候选与 R4/R5 同字节）：`language_loop.main` 退出码——2 只出现在 `send_request` 之前（共享 runtime 拒绝、
  `instruction_unsupported`；argparse 错误亦在其前）；4 只来自 `WriterBusy`，由 `acquire_writer_lock` 在 `write_request` 之前抛出，
  `release_writer_lock` 只返回布尔、不抛 `WriterBusy`；未捕获异常（exit 1）可发生在写入之后（等待循环中非 `LanguageBridgeError` 的
  `OSError`、`finally`）。`_consume_request` 先判重复 id 再判 `IGNORED_FOREIGN_SESSION`/`IGNORED_TERMINAL`，所以已消费 id 的重试只会得
  `IGNORED_DUPLICATE`，不会以「会话已结束：未执行」冒充原请求结果。`send_request` 在 `last_request.request_id` 等于本 id 即返回，重试
  可能直接拿到原请求的回执（页面据此移除条目，含义正确）。

## 1. F7 闭合核实（workflow §4.4 四条）

| 条件 | 结论 | 依据 |
|---|---|---|
| (1) fixture 由生产路径产出 | 成立 | 桥/状态经 `language_bridge.tracker_state_payload` + `write_tracker_state`，回执经 `LanguageSession._journal`（与 R5 已接受的夹具相同）；CLI 用 `StubCli` 返回 exit 4 与 exit 1，符合 R5 §3 闭合要求 (1)；本角色另以真实 CLI 子进程复现 exit 4 路径（P1）。 |
| (2) 修前红 / 修后绿 | 成立 | 具名回归在 R5 候选按钮页上红、在本候选上绿（见 §0）；真实 CLI 探针同向。断言覆盖 R5 §3 要求的三件事：重试 exit 4 后 `[A]` 仍在且 `last_retry.exit == 4`、同视图同动作被拒且不调 CLI、A 的迟到回执到达后被关联为 `APPLIED`。 |
| (3) Play 治理门 | 不触及 | `tools/analyze_m3_body.py`、`tools/preflight_reanchor_env.py`、`controller/run_log.py` 相对 R4/R5 零改动。 |
| (4) 可机械断言 | 是 | 不适用 `NOT_MECHANIZABLE`。 |

**F7 闭合**（CLASS_2 · `BC-18`）。AC-18「未知/超时结果遵循 AC-1 修订 1，不自动换 request_id 重发」与 C3-2「各自守卫、各自同 id 重试、
迟到回执只解除对应一条」在锁忙、CLI 出错、超时、再次无回执、`IGNORED_DUPLICATE` 五种重试结局下均成立（自测 + 探针 P1–P6、P8）。

## 2. 修复触及行核查（新阻断唯一来源；结论：无 CLASS_1/2）与 RED_LINE

- `App._run`（重试分支）：只有非 `IGNORED_DUPLICATE` 回执才移除；其余结局保留原条目（argv/视图/令牌/`since_unix_s` 不变）并记
  `last_retry`；运行期间被迟到回执解除的不复活（`late_messages`）。`pending_lock` 覆盖判定与写入；`pending()` 浅拷贝而 `last_retry`
  整体替换，线程间无半写可见。无新增发送路径。
- `App._retry`：先 `monitor.poll()` 再 `resolve_late_receipts()`；读取失败 → 不发、条目保留（P5）；已解决 → 不发并给出原回执；
  `IGNORED_DUPLICATE` → 重读日志用原请求自己的回执解除（日志中原回执总先于重复回执写入）。只减少发送，不增加。
- `App._run`（新点击分支，用户选择 2）：无回执时只有 exit 2/4 不留未知，与上段冻结 CLI 事实一致；exit 1 等「可能已写入」改留未知、
  只可同 id 重试——修复前该路径显示「CLI 退出码 1」后允许以新 id 重点，属 F7 同类缺陷；改后更保守，由会话按 id 去重，无双执行。
- `Monitor._read_logs`：同 id 已有回执时跳过后到的 `IGNORED_DUPLICATE`，其余回执仍后写覆盖（P7）。
- `interpret` 其余退出码文案、页面「上次重试」行（`esc` 转义；渲染键含 `last_retry.at_unix_s`）、操作单 §3 两句与首段状态行：
  与代码一致，未改任何阈值、ID、判据或执行顺序。
- 自测：新增 9 项与 `StubCli` 可调用结局；未改既有断言。
- **RED_LINE**：无。改动只在本机操作页的请求结果记账与显示；不读 Unity 真值、不进感知/控制输入，不涉及渲染管线或样帧。

## 3. Findings

### Blocking

无。F7 已闭合（§1）；修复触及行无 CLASS_1/2（§2）；无 `RED_LINE`；未改动行上未发现 `上轮漏检` CLASS_1/2。

### Non-blocking

**F3**（R1，`SCOPE_GAP`，账本 2026-09-22 `OPEN`）状态不变：`LanguageWorker` 未触及。

## 4. 非阻断注记（不是 finding，不带依据列）

1. **「x s 前」只在渲染键变化时重画**：`render` 只在键（视图、合法动作、主图、告警/核验 id、未知条目 id 与 `last_retry.at_unix_s`）变化时重建
   「结果未知」框，所以框内 `since_unix_s` 与新加的「上次重试（x s 前）」会停在渲染当时的数值（前者及 `secondFor`「发起于」是 R5 候选既有
   写法，新行沿用）。只影响显示；AC-18 的确认倒计时在 `statusHtml`，每次刷新重算，不受影响；重试由会话按 id 去重，操作单也只写「稍后
   再点」，不据此数值行动。建议（非义务）：「结果未知」框的时间单独每次刷新，或改显示绝对时刻。
2. **文案重复**：条目在重试运行期间被迟到回执解除、且重试恰得 `IGNORED_DUPLICATE` 时，`_run` 已追加「原请求已有回执——X」，`_retry`
   再追加「；X」，同一句出现两次。纯显示。
3. **用户选择 2 的范围归属**：F7 原文针对同 id 重试；新点击 exit 1 留未知不在 F7 字面内，但属同类缺陷、落在本批已触及的 `_run` 判定行、
   在 AC-18/AC-1 修订 1 已接受语义内，本角色按同一标准核查无 CLASS_1/2。是否视为授权信封「仅闭合 F7」之内、两项会话内选择是否需入账
   （实现者 §3 已提问），由接受角色判断；本角色不据此阻断。
4. 操作单 §3 列举「写者锁忙、CLI 出错或再次无回执」时框保留；重试超时与 exit 2 同样保留（P3/P4），操作者动作相同，不作 finding。
5. 自测「exits 2 … and 4 …」一项只执行 exit 2；新点击 exit 4 不留未知由既有「WRITER_BUSY is reported as not written (not unknown)」与探针
   P9 覆盖。
6. 真实浏览器呈现/点击与人眼检查按 AC-18 留获准诊断，本轮未开浏览器；页面行为只有源码断言与 `node --check`。
7. 通过后的执行链（接受角色裁定是否放行）：`_lc_candidate` 此后解析到本轮 `passed_candidate`；采集 worktree 仍在 R4 通过候选，须对齐；
   按操作单 §1 从新 `passed_candidate` 重建 5060 清单（当前入库清单仍指向 R4 候选的 runner）、按既有授权传输 runner/清单、`amend` →
   `preflight`，其后才可用新增诊断检查首批追平与至少两张样帧人眼保真。AC-13…15 仍 `NOT_RUN`，本轮不替代。

## 5. Verdict、计数与交接

- **`PASS_WITH_NOTES`**：R5 冻结集中的 F7 在用户授权的定向返工候选上闭合；K1K3 停点在按钮页 / runner 修订4 迁移 / 操作单 C 候选
  （R5 范围）加 F7 修复上独立复核通过；通过候选 = 本节抬头 `passed_candidate`。F3 仍为 `SCOPE_GAP` 债（账本 `OPEN`）。
- 计数：K1K3 C/R = 4/6、C 退回 0、R 返工 3（另用尽用户授权的一次，本轮通过不再派发）；本轮无 `blocks_consuming_gate`/
  `releases_consuming_gate` 行。
- 交接：接受角色消费 R6（汇总、注记 3 的范围归属、是否放行 §4 注记 7 的零消耗准备与后续获准诊断/Play），再路由实现与用户；本角色不放行
  任何消耗性动作。
- 零消耗：未启动模型/服务/Play、未下载、未创建 scenario/session/run ID、未向 5060 传输、未触碰真实 `runtime/`（探针的真实 CLI 只写
  临时目录）。

## `UNITY_NA` 附议

本工作项**不申请** `UNITY_NA`（提案 §4 与 Gate board 行同）。本轮无附议对象，不附议、不反对；AC-13…15 仍是 `DONE` 的必要证据。

## 6. 边界自查（R6@K1K3 收工）

- 本会话未修改任何实现文件：`controller/`、`Assets/`、`tools/`、`tests/`、`config/`、`ProjectSettings/`、`docs/evidence/` 零改动；
  副本内未检出或改动任何文件（修前按钮页经 `git show` 写到 scratchpad、以 `--web` 传入）；探针只写临时目录与 scratchpad；副本删除前
  `git status --porcelain` 为空。
- 主树本批写入：`docs/reviews/P1-ENG-LOOP-001.md`（追加本节）与 `docs/current-status.md`；
  `python3 tools/check_role_writes.py --role review` 与 `python3 tools/check_docs.py` 结果记在状态板 Log。

---

# R7@K1K2K3 — 机身跟随接入、一圈取样与操作单（R-B8…11；含 C5 退回修复）独立复核（Review，新鲜上下文，2026-09-23）

Implementation snapshot: 候选 = 首次加入 `docs/evidence/P1-ENG-LOOP-001-K1K2K3-c5-fix.md` 的提交（按其 §1 由
`git log -1 --diff-filter=A --format=%H -- <该文件>` 运行时解析；主题「P1-ENG-LOOP-001 K1K2K3 候选（C5 退回后修复）…」），是本地
`main` 的祖先；主树 HEAD 为接受角色 C6 提交，相对候选只改 `docs/current-status.md` 与提案（PLAY_GOVERNING 零差异）。上一通过候选 =
R6 `passed_candidate`（`7ef8cc0…`），上一复核轮候选 = R6 `round_candidate`（同一提交），两条基线重合：全量 diff = 修复触及行 =
`git diff 7ef8cc0…..<候选>`，24 文件（+3531/−192）；C5 所核对候选（首次加入 `-K1K2K3-handoff.md` 的提交，`7851b68…`）到本候选
的修复 diff 9 文件，只动两个新载体、自测、操作单 §5 与证据。
round_candidate: ac3899d58c3f944faf3072f0b55d72e875ef9e1e
Verdict: PASS_WITH_NOTES
passed_candidate: ac3899d58c3f944faf3072f0b55d72e875ef9e1e

## 0. 复核范围、轨道、停点资格、开轮资格与重跑

- **轨道与范围**：提案抬头 `Workflow: engineering-v1`、D4 `ACCEPTED` 时裁定生效；R-B8 裁定新候选走 `K1K2K3` 合并停点，先 C5 再新鲜
  上下文 R7，原 C/R 与返工计数不重置、不借 R5/F7 一次性授权。本轮是本停点第 1 个复核轮；依据列按工程轨道读法 `BC-n` = `AC-n`。
  用户机身跟随原话在 `docs/authorizations.md` 2026-09-23 条目逐字在案，信封不增额；R-B8…11 与 AC-4 修订4 / AC-12 修订6 /
  AC-13 修订2 / AC-19 在提案 Pending rulings 逐字在案。
- **停点自证（workflow §4.3.1 四项）**：条件 1（范围冻结：`controller/body_planner.py`、`controller/track_loop.py`、
  `controller/language_bridge.py`、`config/`、`Assets/`、`ProjectSettings/`、`Packages/`、`tools/`、5060 runner、操作页相对 R6 通过候选
  `git diff --stat` 为空，本角色现算；树哈希 `tools`/`ProjectSettings` = `8533c6ee…`/`d876cff7…` 与 R3…R6 逐字相同，`tests`/`controller`
  = `59b6be80…`/`f194e7e2…` 与两份停点全套日志首行一致）、条件 2（focused、载体自测与红跑由本角色复现，见下）、条件 3（本批不触及
  Unity）、条件 4（交接行、候选解析规则、复核范围 handoff §6、已知限制 handoff §5 / c5-fix §6 在案）按字面成立 → **开轮，不给
  `REVIEW_BLOCKED`**。
- **开轮资格**：全量 diff 于 PLAY_GOVERNING 非空（`controller/gated_publisher.py`、`controller/language_loop.py`、
  `tests/test_language_loop.py`，加 R-B5 冻结操作单集合中的 `-operations-c.md`、`-operator.sh`、`-operator-watch.py`、
  `-build-stage-b-manifest.py` 与 R-B10 点名冻结的两个新载体 `-frame-keeper.py`、`-lap-samples.py`）→ 开轮。本停点交接
  `Consuming=no`，无 `blocks_consuming_gate` 行。
- **副本**：`git worktree add --detach .claude/worktrees/review-P1-ENG-LOOP-001 ac3899d…`；副本无 `runtime/`、`outputs/`；载体自测的
  帧目录以主树 `runtime/frames.1b-diagnostic-hold` 只读传入；读码、重跑、探针全部在副本与会话 scratchpad；副本
  `git status --porcelain --untracked-files=all` 在每次红跑恢复后与收工前均为 0 行；收工删除。
- **重跑（不信报告数字；输出写 scratchpad `r7/`，只回显摘要，不带 `-v`）**：
  - focused（`.venv-language`）：`tests.test_language_loop` → `Ran 151 / OK`（含新增 `BodyPlannerIntegrationTests` 10 项与四值闭集
    测试）；`tests.test_m3_body_tools tests.test_m3_body_policy` → `Ran 85 / OK`（冻结规划器回归）。实现者 handoff §5 的 326/113
    是含桥/选择器/K 绑定/track_loop 等更大集合的计数，被测树同一哈希，本角色只重跑与本批相称的两组。
  - 载体自测（`.venv-loop-client`，操作者解释器）：`P1-ENG-LOOP-001-c2-carrier-selftest.py` → 117 `ok`、`OK: 0 failed`、退出码 0
    （= c5-fix 自测日志 §2 的 117/117；渲染项含 Pillow 实跑）。
  - 红跑 1（控制器）：副本内 `git checkout 7ef8cc0… -- controller/gated_publisher.py`（只撤销发布门的机身通道，等价 `git revert -n`
    该文件）→ `BodyPlannerIntegrationTests` + 闭集测试 11 项 → `FAILED (failures=6, errors=1)`，失败名与 handoff 自测日志 §4 逐名
    相同（tilted/no_observation/rejected/planner_exception/write_failed/fallback_failed 六项 + 闭集）；`git checkout HEAD -- …` 恢复后
    副本干净。
  - 红跑 2（C5 退回修复的非空性）：同一份已提交自测加 `--lap`/`--keeper` 指向 `git show 7851b68…:` 的 C5 所核对候选脚本（写到
    scratchpad）→ `FAILED: 7 failed`：六项具名 C5 反证（末帧晚处理拒收照算、坏日志 fail-closed、C5-1、C5-2、C5-3 取样侧、C5-3 保存侧）
    全部红，加正向运行项（旧报告无新增哈希字段）；与 c5-fix 自测日志 §3 逐名相同。
  - 本角色独立探针 `r7-lap-probe.py`（真实 `LanguageSession` + 冻结规划器经单元测试 `Harness` 驱动，保存器与取样脚本为候选原件，
    全部在临时目录）：C6-2 四种停点时序 + C6-1 四种损坏/错配，结果见 §4 注记 1/2。
  - 停点全套 `-tests-k1k2k3-c5-fix.log`（实现者义务，只读核对）：首行树哈希 = 候选；`Ran 1534`、`FAILED (errors=9, skipped=68)`、
    `FAIL:` 0；9 个 `ERROR:` 名与 R6 基线 `-tests-r5-fix.log` 排序 diff 为空；`## skipped tests` 清单排序 diff 为空 → 新增失败 0。
- **直接关联冻结代码**（只读，候选与 R6 同字节）：`TrackLoop._body_step`（只在 `is_latest` 帧、无 rate/qualification 生命周期时运行；
  无观测 → `hold(no_observation)`；规划器异常 → `hold(planner_exception)`；发布抛错 → 恰一次 `hold(publish_failure_fallback)`；再失败
  → `_body_fail_closed_reason` → `_record_terminal_error(event=BODY_COMMAND_FAIL_CLOSED)`）、`_build_body_runtime`（schema/合同版本/
  `expires_after_s`/场景 id/锚点/云台限位/路线高度 = `ground_plane_y_m`/校准工件哈希/估计器/策略 fail-closed；身份七字段含
  `config_sha256`、`scenario_config_sha256`）、`ThresholdBodyPlanner.decide`（只读 `PlatformState`，`no_platform_state`/`no_estimate`/
  `margin_unconstructible`/滞回/走廊缩短或阻挡 → `hold`）、`RuntimePublisher.body_command`（hold/velocity 各走 `body_entry`，有效期取
  `command.expires_after_s`）、`GatedPublisher._set_fatal`（首因优先）、`_gate` 五项核验与 detail 键（与机身 `extra` 三键无重叠）、
  `LanguageSession.tick` 顺序（`_consume_request` → `_advance_segment`）、`_advance_segment`（`frames_processed` 日志带 `frame_ids`；
  fatal → finalize → `REINIT_REQUIRED`）、`_terminal_reason`（`ERROR_REINIT_REQUIRED` → `unexpected_segment_end` + `metadata_invalid`）。

## 1. 逐条 AC 核对（只列本候选触及或 C6 核对表提问的条款；其余 AC-1、2、5…10、16、17、18 运行时路径零改动，沿用 R2/R4/R6）

| 编号 | 本角色结论 | 依据（真实代码与本角色复现） |
|---|---|---|
| AC-19 | 满足（离线部分） | `bind_body_runtime` 先核 body 场景文档 == 生效场景文档（`effective_scenario_document`，含 `runtime/scenario_config.json` 覆盖）、`command.capture_hz` == K 收据 hz，再调冻结 `_build_body_runtime("threshold")`，再核 `expires_after_s` == 2/hz；任何 `OSError/ValueError/TypeError/KeyError/AttributeError` → `ConfigMismatch`，发生在 `LanguageSession.__init__`、帧环/会话锁/任何桥写入之前（测试断言 `tracker_state.json`/`body_command.json` 不存在），无降级分支。`run` 子命令两参数带冻结缺省、无关闭开关；`lc_run` 显式传两文件。速度只经 `_body_step` → `GatedPublisher.body_command` → `_derived`：`accepted_frame_id` 必须是本帧刚 `WRITTEN` 的观测（`observation()` 每次先清关联），写前重跑同一 `_gate`（快照/身份/latest 帧差/两条截止），detail 逐项进收据；静音→`MUTED_DROPPED`、无关联→`orphan_control`、门拒→`PUBLISH_REJECTED(reason)` 均不写并抛 `BodyCommandNotWritten`，由冻结 `_body_step` 补恰一次 hold。所有 `hold`（判停、无观测、规划器异常、回退）走 `_safety_hold`：不绑帧、不过门、`frame_id` 为空、收据通道 `body_safety_hold`，不冒充门控速度；底层写失败先记 `WRITE_FAILED`（速度通道带 `frame_id`，安全通道 `frame_id` 空）再原样抛出；回退 hold 再失败 → 冻结 fail-closed。收据闭集 `WRITTEN/PUBLISH_REJECTED/MUTED_DROPPED/WRITE_FAILED` × `observation/look_at/body_command/body_safety_hold`。日志 `body_planner.mode/reason` 记意图、`published_mode/published_reason/publish_error` 记实际（测试断言「意图速度、实写 hold」）。在线路径只读 v3 帧元数据（`camera_forward_world`、`camera_position_world_m`）与配置/校准常量，不读任何真值文件（RED_LINE 无）。十项具名用例经真实会话+冻结规划器+真实发布器执行；六项在 R6 门上红（本角色复现）。**真实 Unity 机身运动仍未证**，只能由获准诊断证实。 |
| AC-4 修订 4 | 满足 | `BodyRuntime.fresh()` 每段 `copy.deepcopy` 规划器与估计器，原型从不交给段；`test_each_segment_gets_its_own_planner_…` 断言两段实例互异、第二段估计器未初始化、退役后 `publish(3)` 收据零新增、第二段速度收据 `track_id` 为新段。未确认/初始化静音/退役/终态：`initialize()` 不调 `_body_step`（一次性 `hold_body()` 照旧，测试断言此刻机身通道零收据）；`finalize()` 后 `closed` 使两条机身通道都直接返回 `None`。`raw_lost` → `SUSPECTED(tracker_failure)`、`BODY_COMMAND_FAIL_CLOSED` → AC-4 修订2 兜底（测试断言 `unexpected_segment_end.event` 逐字、`reason=metadata_invalid`、之后收据零新增）。 |
| AC-3 | 满足 | 观测五项 `_gate` 与 `WRITTEN` 关联规则未改；机身速度复用同一 `accepted_frame_id` 与同一 `_gate`，被拒帧零速度（`orphan_control` 或门拒后只写回退 hold）。`_set_fatal` 首因优先，所以观测被拒时段终止原因仍是观测的拒收原因，不被后续 `look_at`/速度的 `orphan_control` 覆盖。 |
| AC-13 修订 2（工具与规则冻结部分） | 满足（Play 证据仍 `NOT_RUN`） | `-lap-samples.py` 逐条落实修订2 与 C5 裁定：t0 = 首条 `WRITTEN` 观测帧的保存帧仿真时刻（t0 帧未保存 → `t0_frame_not_kept`）；九点 `t0 + i·106.5/8` 只由 t0 决定；最近保存帧、容差 2/hz、等距取较早；`NO_VALID_BOX`（段运行日志无框或 `ok=false`）、`NO_WRITTEN_OBSERVATION`（C5-1）、`KEPT_FRAME_IDENTITY_MISMATCH`（保存 JPEG sha 与索引 `jpg_sha256`、观测收据 `snapshot_sha256` 三方一致，C5-3）；窗口归属按帧仿真时刻，无帧记录按 t0 收据到第一次全在窗口之后的 `frames_processed` 之间，找不到即 `window_not_fully_processed` 且其后记录全计（C5）；四日志缺失/坏行/重复帧号 fail-closed；`window_incomplete`、`lap_window_beyond_220s`（C5-2）、窗口内 LOST/REINIT_REQUIRED/TERMINAL、该段退役、`unexpected_segment_end`、`PUBLISH_REJECTED`、他段 `WRITTEN` 观测、≥1 条 `body_command` `WRITTEN` 且 `detail.mode=velocity_world`、保存帧元数据 `camera_position_world_m` 相对 t0 最大位移 ≥ 0.5 m；脚本只输出 `mechanical` OK/FAIL 与逐项失败，`user_confirmation` 恒 `PENDING`，从不宣告 `LAP_DEMO_PASSED`；只读会话输出与保存帧。`-frame-keeper.py`：只读跟随 `latest.json`、逐帧原字节复制、回读 sha 核对（不符即删并记 `copy_verify_failed`）、被淘汰帧记缺口不补造、帧号回退记 `frame_rollback`（重复帧号在取样侧 fail-closed）、拒绝写入 runtime 树内。操作单 §5 文字与脚本常量逐项一致（106.5、9、0.4 s、220 s、0.5 m、失败名）。本角色探针与自测红绿见 §0/§4。 |
| AC-12 修订 6（操作单部分） | 满足（执行证据缺失） | `-operations-c.md` §0 额度表改为诊断 1/3 已用、标签只剩 `-6/-7`、旧号 1…5 禁用，硬停止集合加机身 fail-closed（`unexpected_segment_end.event=BODY_COMMAND_FAIL_CLOSED` 或收据 `WRITE_FAILED`）；§1 传输集合改三源文件（`-build-stage-b-manifest.py` `TRANSFER` 同步，漂移 ≠ 传输集合即拒绝生成，本角色核对其判定逻辑）；§2 第 6 步把两张具名样帧人眼保真（路径/确认人/结论）与一圈规则冻结列为正式 P1 前提；§3 加 T4 `lc_keep`、`lc_lap`；§4 改诊断 6/7 内容与顺序；§5 冻结取样规则；§7 证据复制加 `lap-samples/`、索引与九帧源帧。`-operator.sh`：`lc_check` 加残留帧保存进程检查；`lc_run` 显式传冻结规划器两文件；`lc_lap` 的 `run_root` 诊断/正式分支与 `LanguageSession._run_root()`（诊断 `diagnostics_root/<session>`、正式 `runtime/`）一致。新候选尚未对齐两处 checkout、未重建清单、未传输、未 `preflight`，这些仍是通过后的执行义务，不能提前算完成。 |
| AC-11 | 满足 | 见 §0 只读核对：1534 / 0 failures / 9 个与 R6 基线逐名相同的环境 errors / skip 清单相同，新增失败 0；本角色不重跑全套。 |
| AC-1 / AC-17 | 满足 | 桥 schema、请求回执、八态九动作与 worker 相对 R6 零改动（diff 不触及）；新闭集只在 Python 侧发布收据文件。 |
| AC-14 / AC-15 | 证据缺失 | 正式 Play 0/8；操作单 §6/§7 保留并按修订6 补机身收据计数/位移/缺口/九图原话，不写成跟踪性能主张。 |

K1（帧/控制协议与时间语义）：机身速度与同帧 `WRITTEN` 观测绑定并重核五项截止；安全 hold 不绑帧且单列；取样窗口按帧仿真时刻归属。
K2（安全约束与控制命令）：hold 恒可写、速度须过门；写失败恰一次回退、再失败终止段；退役/终态零写入；速度只由冻结规划器从发布平台量推出，
不读估计、不读真值。K3（人工决策边界）：人工判丢/重指定/停止路径零改动；取样工具不裁定通过，九图逐张确认留给用户。三项均逐条核过。

## 2. 全量 diff 逐文件处置（24 文件）

- **运行时（2）**：`controller/gated_publisher.py`（+93/−11：机身通道、`BodyCommandNotWritten`、`_safety_hold`、`_derived` 的 `extra`/
  `record_write_failure`、两闭集各加一值、模块 docstring）、`controller/language_loop.py`（+106/−6：`effective_scenario_document` 拆出、
  `SessionConfig` 两字段、`BodyRuntime`/`bind_body_runtime`、构造期绑定、`session_started` 与段日志抬头 `body_planner` 身份、每段深拷贝
  接入 `TrackLoop`、`FixtureFramePublisher` 相机姿态可设、`run` 两参数）——逐行核过，见 §1。
- **测试（1）**：`tests/test_language_loop.py`（+309/−3：`Harness(body=True)` 地面高度 0.2 与两配置、`tilt_camera`、
  `BodyPlannerIntegrationTests` 十项、闭集测试改四值×四值）——夹具经生产写者（真实会话/发布器/规划器），故障注入只替换 `_derived`
  钩子、`RuntimePublisher.body_command` 与 `planner.decide`，不手写桥文件。
- **操作载体（PLAY_GOVERNING，7）**：`-operations-c.md`（+98/−75）、`-operator.sh`（+25）、`-operator-watch.py`（+42：一圈窗口行、
  `body_pos/body_disp/body_cmd`、窗口已满提示，只供择时）、`-build-stage-b-manifest.py`（+7：`TRANSFER` 三文件）、`-frame-keeper.py`
  （新 162 行）、`-lap-samples.py`（新 322 行）、`-c2-carrier-selftest.py`（+296：keeper/lap/watch-lap 三部分与 C5 六项反证）——见 §1。
- **传输清单（1）**：`-transfer-manifest-5060-stage-b.json`（R6 后由实现按操作单 §1 重建：只变 `passed_candidate` → R6 与 runner 哈希两行；
  是 R6 执行史工件，`transferred` 仍两源文件，**新候选通过后须再重建**，见 §4 注记 9）。
- **证据（6）**：`-K1K2K3-handoff.md`、`-K1K2K3-c5-fix.md`（两份实现者自证，与代码相符）、`-k1k2k3-carrier-selftest.log`、
  `-k1k2k3-c5-fix-selftest.log`（自测/红跑/零改动机检，与本角色复现一致）、`-tests-k1k2k3.log`、`-tests-k1k2k3-c5-fix.log`（停点全套，
  只读核对）、`-stage-b-prep.md`（+107：§5 第 5 行诊断 5 记账、§10 对齐、§11 诊断 5 事实、§12 用户原话与裁定请求；与授权账本一致）。
- **事实源（6）**：`docs/authorizations.md`（+10：用户机身跟随原话与 R5/F7 定向返工两条）、`docs/current-status.md`、
  `docs/implementation-status.md`（R-B8…11 段）、`docs/phase1-single-drone-design.md`（v0.3.49）、提案（R-B8…11、四行 AC、C5/C6 核对表）、
  `docs/reviews/P1-ENG-LOOP-001.md`（R6 节）——只核对与代码/合同一致，不属本轮实现。
- **PLAY_GOVERNING 零改动**：`controller/body_planner.py`、`controller/track_loop.py`、`controller/language_bridge.py`、`config/`、
  `Assets/`、`ProjectSettings/`、`Packages/`、`tools/`、`-5060-runner-b.py`、`-operator-web.py`、Play 治理门三文件（`analyze_m3_body.py`、
  `preflight_reanchor_env.py`、`controller/run_log.py`）。

## 3. Findings

### Blocking

无。修复触及行（= 全量 diff）上未发现 CLASS_1/2；无 `RED_LINE`；无旧 finding 闭合失败（R6 无未闭阻断）；未改动行上未发现 `上轮漏检`。

### Non-blocking

**F8** · CLASS_2（证据工件的边界/失败路径） · 依据列 **`SCOPE_GAP`**（不可达，非阻断，路由接受角色） · `docs/evidence/P1-ENG-LOOP-001-lap-samples.py`
`analyse()`/`position()`/`frame_time()`（C6-1 的答复）：取样脚本对保存帧的**图像**做三方哈希核对，但对**元数据**不做任何核对——
(a) `position()` 直接读保存 JSON 的 `camera_position_world_m`，不与索引 `json_sha256` 比对；(b) 索引 `simulation_time_s` 直接用于选帧与
窗口归属，不与段运行日志同帧 `simulation_time_s` 交叉核对。本角色探针（副本临时目录，对通过会话输出的副本人为篡改）：截断 t0 帧 JSON →
`body_displacement_below_0.5m`（fail-closed）；截断非取样帧 JSON → 静默忽略，无失败项；把一帧 JSON 的位置改动 50 m（仍合法 JSON）→
`body_max_displacement_m` 10.64 → 50.00 且 `mechanical=OK`；把远处一帧的索引 `simulation_time_s` 改到取样点 4 附近 → 该帧被选为取样 4、
状态 `READY_FOR_USER`、无失败项。**范围判据**：生产写者无法产生这两种错配——保存器从同一份字节解析出 `simulation_time_s` 并记
`json_sha256`，回读不符即删并记缺口；Unity 不重写同帧号（回退在门与保存器两侧都 fail-closed）；跟踪器 `WRITTEN` 时 `verify_frame_identity`
已核对盘上元数据完整值。只有事后人为改写保存文件或索引才可达，故 `SCOPE_GAP`。**建议闭合（若接受角色裁定范围内必修）**：`position()`
与 `frame_time()` 先核保存 JSON sha == 索引 `json_sha256`，取样帧另核索引 `simulation_time_s` == 段运行日志同帧值，不符记
`KEPT_FRAME_IDENTITY_MISMATCH`/`corrupt_log`；回归测试可复用本角色探针 (b)(c)(d) 三种副本篡改（生产会话输出的副本）。改动落在冻结载体上，
按 R-B10 属 PLAY_GOVERNING，若修则并入下一候选走 C/R。

**F3**（R1，`SCOPE_GAP`，账本 2026-09-22 `OPEN`）状态不变：`LanguageWorker` 未触及。

## 4. 非阻断注记（不是 finding，不带依据列；供接受角色、实现角色与诊断 6/7 决策参考）

1. **C6-2 答复（停点时序）**：机械门要求 t0 收据之后出现**一次**所有帧都在窗口末之后的 `frames_processed`。探针：紧接窗口末帧就
   `stop` → `window_not_fully_processed` + `segment_retired_in_window:operator_stop` + `state_TERMINAL_in_window`（保守失败）；再处理
   **一帧**（单帧 tick）后 `stop` → `OK`；窗口末被一批追平跨过（如 [531,532,533]）后立即 `stop` → 失败，再单帧处理一次后窗口判定即满足。
   会话主循环 `POLL_INTERVAL_S` = 0.02 s、5 Hz 供帧，watch 的「一圈窗口已满」按 `latest.json` 帧仿真时刻打印，之后 ≤ 0.3 s 内会话即处理出
   第一帧窗口后帧；操作者按 §5 第 4 步看到提示后再点「停止会话…」的人工延迟远大于此，操作指令与机械门一致，假阴性只在「提示后 0.3 s 内
   停止」或会话恰在窗口末停帧时出现。建议（非义务）：§5 第 4 步加一句「看到提示后再等约 2 s 再停」。
2. **C6-1 答复（索引/JSON 损坏与错配）**：见 F8；损坏方向 fail-closed 或不影响判定，错配方向不可达但未设防。
3. **取样点 8 与追平批**：t_8 = t0 + 106.5 s 落在两帧正中，等距取较早帧；若窗口末恰被一批追平（批中间帧无自身 `WRITTEN` 观测），
   取样 8 判 `NO_WRITTEN_OBSERVATION`（C5-1 保守读法；探针第 3/4 种时序即如此）。诊断 5 的实测是首批后 350 帧仅 1 帧无自身观测，
   九点命中此类帧的概率约每次 Play 百分之二三；这是接受角色已裁定的保守读法，本角色不改口径，只提示正式 P1 的假阴性来源。
4. **段 finalize 不补 hold（handoff §4 解读 2）**：人工判丢/释放/停止或协议终止时最后一条速度命令留在桥上、由接收器 0.4 s 过期回落；
   AC-19 只要求列举的四种情形发出显式 hold、AC-4 要求 finalize 后收据零新增、冻结合同只许 `_body_step` 写机身。实现与合同字面一致；
   若接受角色希望终止时也有显式 hold，须改冻结合同或另给写入点并再走 C/R，请在 Acceptance rulings 明示裁定，避免日后争议。
5. **冻结配置的身份只记录不钉死**：`bind_body_runtime` 校验 schema/合同/hz/有效期/场景/校准哈希，但不核对规划器配置文件本身的 sha
   （策略值来自该文件）；`config_sha256` 记入 `session_started.body_planner` 与段日志抬头，可事后核对。Play 路径下 `lc_run` 传采集
   worktree 的冻结文件、`lc_check` 要求 worktree HEAD = 通过候选且 `config/` 零差异，故对应性由 AC-12 修订6 的候选对应检查承担。
6. **「机身位置」= `camera_position_world_m`**：v3 帧元数据无独立机身位置字段，取样、watch 与冻结规划器（`PlatformState.position_world_m`）
   都用相机位置；若相机相对机身有非零偏置，云台转动会贡献 ≤ 偏置量的「位移」，0.5 m 门槛下不致误判，但正式 P1 报告应写明该代理关系。
7. **保存器重启**：`Keeper.__init__` 续接时逐行 `json.loads` 索引，若上次 Ctrl-C 恰截断末行，重启会抛 `JSONDecodeError` 不能续跑
   （取样侧对该坏行仍 fail-closed）；操作单未写重启保存器的步骤，实际影响是缺口增多 → `MISSING_FRAME`（保守）。
8. `lc_lap` 不传 `--hz`，脚本缺省 5.0 = K 收据与场景 hz；hz 冻结不变时无影响，改 hz 须同步。
9. **通过后的执行链（接受角色裁定是否放行）**：`_lc_candidate` 与清单脚本此后解析到本轮 `passed_candidate`；采集 worktree 仍在 R6 候选，
   须 `checkout --detach` 对齐；按操作单 §1 重建清单（新 `TRANSFER` 三源文件；本角色核对清单脚本对阶段 A 副本的漂移集合 = 三文件）、按
   既有授权传输五文件、`amend`（幂等）→ `preflight`，之后才可用 `diag-loopb-6`（`-7` 余量）验证机身命令与运动、首批追平、操作页与两张
   具名样帧人眼保真。AC-13…15 仍 `NOT_RUN`，本轮不替代。
10. **人眼保真（workflow §4.3.2）**：正式采集尚未发生，两张具名样帧的逐张确认按 AC-12 修订6/R-B11 是正式 P1 之前的硬性前提，本轮不构成
    `RED_LINE` 触发；若正式 P1 在该记录缺失时开跑，下一轮按 `RED_LINE` 阻断。
11. 5060 侧服务不执行机身通道，`gated_publisher.py` 入传输集合只为保持 `language_loop` 导入与哈希一致；runner 零改动。

## 5. Verdict、计数与交接

- **`PASS_WITH_NOTES`**：K1K2K3 停点候选（机身跟随接入 + 一圈取样与操作单 + C5 退回修复）在真实代码上独立复核通过；通过候选 = 本节抬头
  `passed_candidate`。F8 `SCOPE_GAP` 非阻断，路由接受角色（记入「范围外已知缺陷」账本 `OPEN`，或裁定范围内必修并入下一候选）；F3 不变。
- 计数：K1K3 C/R = 4/6（C 退回 0、R 返工 3 + 用户授权 1 次）沿用；K1K2K3 C/R = 2/1，C 退回 1（C5）、R 返工 0；本轮无
  `blocks_consuming_gate`/`releases_consuming_gate` 行。
- 交接：接受角色消费 R7（F8 处置、注记 4 裁定、注记 1 的操作单一句是否派发、放行注记 9 的零消耗对齐与获准诊断），再路由实现与用户；
  本角色不放行任何消耗性动作。
- 零消耗：未启动模型/服务/Play、未下载、未创建 scenario/session/run ID、未向 5060 传输、未触碰真实 `runtime/`（自测与探针只读主树
  `runtime/frames.1b-diagnostic-hold`，写入只在临时目录与 scratchpad）。

## `UNITY_NA` 附议

本工作项**不申请** `UNITY_NA`（提案 §4 与 Gate board 行同）。本轮无附议对象，不附议、不反对；AC-13…15 仍是 `DONE` 的必要证据，
机身在真实 Unity 中的运动只能由获准诊断与正式 Play 证实。

## 6. 边界自查（R7@K1K2K3 收工）

- 本会话未修改任何实现文件：`controller/`、`Assets/`、`tools/`、`tests/`、`config/`、`ProjectSettings/`、`docs/evidence/` 零改动；副本内
  红跑 1 用 `git checkout <R6> -- controller/gated_publisher.py` 临时撤销并已 `git checkout HEAD -- …` 恢复，红跑 2 的旧脚本经 `git show`
  写到 scratchpad 并以 `--lap/--keeper` 传入；探针只写临时目录与 scratchpad；副本删除前 `git status --porcelain --untracked-files=all`
  为 0 行。
- 主树本批写入：`docs/reviews/P1-ENG-LOOP-001.md`（追加本节）与 `docs/current-status.md`；
  `python3 tools/check_role_writes.py --role review` 与 `python3 tools/check_docs.py` 结果记在状态板 Log。
