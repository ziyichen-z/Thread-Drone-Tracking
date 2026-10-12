# P1-ENG-LOOP-002 — OPS操作增量实现进度与缺口（Implementation，MacBook Air，零消耗；**非稳定候选**）

- 登记轮次：`OPS操作增量实现`；Dispatch-Id `P1-ENG-LOOP-002-OPS操作增量实现-20261008T003015Z-a43a`；派发 base_head `db10b5e`。
- 合同唯一来源：同名提案「OPS九题答复落实（2026-10-07，Acceptance）」§1–6（十条 AC 修订、W1–W5、O1–O4、§3 逐文件闭集、§4 停点 `OpsK1K2K3K4`、§5 零消耗边界）；用户答复来源为 `docs/authorizations.md` 2026-10-07 该项四条 supervisor 代录条目。参照载体 `docs/evidence/P1-ENG-LOOP-002-operator-web.py`（LOOP-001）只读、未启动。
- 状态：代码、测试与三份操作单文本已按 §3 闭集落地并通过 focused；**停点全套与 AC-11 人眼保真不在本信封内，未执行**，故不交稳定候选、不写 `-OpsK1K2K3K4-handoff.md`、不交 `C6@OpsK1K2K3K4`。验证清单与待裁定见 `docs/evidence/P1-ENG-LOOP-002-ops-validation-plan.md`。未经复核，只记 `IMPLEMENTED`（新范围），不记 DONE。

## 1. 逐文件闭集（§3）与动作

| 路径 | 动作 | 主要内容 | AC |
|---|---|---|---|
| `tools/eng_loop2/play_ops.py` | 新增 | 分阶段入口 `plan`/`gate`/`source`/`prep`/`receipt`/`play`；第 1 节机械门（严格双来源、最新有效 passed_candidate、PLAY_GOVERNING 含三份操作单、全局 blocks/releases 用 `$REL` 上原 `check_docs.py` 两函数、HEAD/status/_Recovery、操作单 sha、账本命中、`$DOCWT` 自检）；SOURCE:2 来源核（附录 A 原文 + `src_check` 同判据）；SSH 单元（单主连接、通道闭集与顺序、每通道前 `-O check`、失败闭合回退选项、计次不重试）；前台服务监督（`-tt` 交互 bash 逐行键入第 4 节、监听行识别、Ctrl-C、同会话释放核对）；measure→k-receipt 退出码门；身份 `/status` 恰 1 次；第 0.4 节逐维度守账；冻结计划（只文字/intent/Δ/时长）；`PlanScheduler`（O2）；只移动归档；O3 原因码分流；诊断模式拒启 | 8/9/10/14/15/16 |
| `tools/eng_loop2/operator_web.py` | 新增 | 127.0.0.1 标准库内嵌页（W1 按钮闭集）；W2 呈现快照与预览字节 sha 绑定、浏览器解码后回报、提交前重读字节、同 result_id 两读不一致永久不可确认；W3 两截止取早、帧差门、数据缺失/回退/过期不可确认、刷新不续期；W4 runner 与网页共用 `Submitter`（全局在途互斥、一次提交记录、每会话 stop 至多一次、先落 request_id 再调用、UNKNOWN 不重发、迟到回执只核清）；W5 `ops-web.jsonl` 原流、nonce + Host/Origin、预览/实时帧路径绑定；`fidelity` 只读离线样帧保真核对页 | 5/9/10/11/14 |
| `tools/eng_loop2/summarize_ops.py` | 新增 | 收尾独立离线摘要：计划—实际（跳过不成样本、失败分母保持）、客观事件（未播种即未验证、初始 LOST 不代证）、计划↔提交↔回执↔显示一致性、逐提交回执时间线、本人反馈分列（缺失=未反馈）；正式模式每归档**恰一次**原 CLI `analyze_play score`（已有输出不重跑），只引用漏斗与四表原值；诊断模式不评分 | 8/9/14/18 |
| `tests/test_eng_loop2_play_ops.py` | 新增 | 生产入口 `play_ops.main` + 临时 bare origin/执行检出/文档检出 + 假 `ssh`/`curl` + Python 替身逐阶段正常/失败（48 例） | 8/10/15/16 |
| `tests/test_eng_loop2_operator_web.py` | 新增 | W1–W5 合法/非法状态、旧页/错令牌/新 epoch、跨标签并发、图失败与显示门、两截止与刷新不续期、Δ 挂起、重复、UNKNOWN 与迟到回执、WRITER_BUSY、本机访问拒绝、保真页、真实 CLI 往返（30 例） | 5/10/11/14 |
| `tests/test_eng_loop2_summarize_ops.py` | 新增 | 计划与实际漏斗/跳过分离、失败分母、缺日志/未播种/初始 LOST/未反馈、四表只引用与恰一次、模式隔离（10 例） | 8/14/18 |
| `tests/test_loop2_isolation.py` | 只追加（diff 删除行 0） | `OpsIsolationTests` 6 例：两在线文件不导入真值/评分/几何/离线摘要；网页无评分/几何/真值字符串；真值文件只在 `archive_attempt` 内出现且该函数无读取调用；`analyze_play` 只在 Play 前 `freeze_plan`、`summarize_ops` 只在收尾 `stage_play`；调度器无评分/几何字符串；冻结计划键闭集；离线摘要只以子进程调用原评分 | 9 |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md` | 修改 | 修订记录；新增第 0A 节阶段映射与 1.6/G4 机读形式、单写者与诊断拒启；§0.1 分工（ACTOR:1）、§0.3（SOURCE:2）、§1（GATE:8）、§2、§3、§4（前台监督）、§6、§7、§8（网页发送/跳过、候选选择、SUSPECT:5）、§9（O2）、§10（无自动重试，IR-OPS-4）、§11（自动原流与反馈分列）、§12（归档与摘要）、§13（O3 与 IR-OPS-3）、附录 P 取用说明；G1–G5/原资源/STOP 不变 | 10/14/15/16/18 |
| `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` | 修改 | 页首：四次已结束、无新许可、不沿旧额度；新分工与网页入口仅在未来具名授权下适用；`play_ops` 诊断拒启（IR-OPS-5）；§6.2 与附录 6 停用；confirm-lost/dismiss 只记录；诊断摘要不评分 | 10/11/14/16 |
| `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md` | 修改（只加说明） | §2 现行入口指向 `play_ops prep`/`source`；附录 A/B 标题前缀与正文为工具原样取用（块正文未改） | 10/16 |
| `docs/evidence/P1-ENG-LOOP-002-ops-validation-plan.md`、本文件、`docs/evidence/P1-ENG-LOOP-002-ops-focused-tests.log` | 新增 | 验证清单/待裁定；进度与缺口；focused 原输出 | 11/13 |
| `runtime/README.md` | 修改（只追加段落） | 新入口/网页只读的桥文件与日志位置、归档只改名移动 | 10/13 |
| `docs/current-status.md` | 修改 | 本项交接行 | 13 |

禁改路径（`controller/`、`Assets/`、`config/`、`ProjectSettings/`、`Packages/`、`tools/language_serve.py`、`tools/language_latency.py`、`tools/eng_loop2/{__init__,llama_adapter,deploy_digest,analyze_play}.py`、其他既有测试、JET 源、LOOP-001 旧载体）零改动；无第三方依赖、无新板服务、部署 16 路径不变（新桌面工具不入部署闭包）。LanguageWorker/CandidatesBackend/`_validate_candidates_source`/`candidates_preflight` 零 diff（`controller/` 未触）。

## 2. 十条 AC 修订的逐条证据（本轮可得部分；未完成项如实标注）

| AC 修订 | 本轮证据 | 未完成 / 后置 |
|---|---|---|
| AC-5 修订 1 | `BindingTests.*`、`DeadlineTests.*`、`SubmissionTests.test_concurrent_clicks_from_two_tabs_send_exactly_once`；`LegalActionTests.test_cli_argv_is_accepted_by_production_parser`；`RealCliTests.test_cli_runner_round_trip_through_production_cli`（真实 CLI 子进程）；既有 `tests/test_language_loop.py` 原样通过（focused 日志）；网页只经原 CLI，不写桥/锁，`controller/` 零 diff | 新停点全套（SUB:1） |
| AC-8 修订 3 | `SchedulerTests.test_none_result_closes_step_without_extra_ask_or_observation`、`test_refused_receipt_is_recorded_and_advances`、`test_skip_then_session_terminal_marks_rest_not_executed`；`SubmissionTests.test_skip_sends_nothing_and_records_reason`；`PlanVsActualTests.*`；既有 `tests/test_eng_loop2_analyze.py` 原样通过 | 计划—回执—原四表对应表须真实归档（正式证据停点） |
| AC-9 修订 1 | `tests/test_loop2_isolation.py::OpsIsolationTests`（6 例）；冻结计划无几何键（`PlanTests.test_freeze_checks_sheet_and_writes_no_geometry`） | 「输入与进程隔离」节随停点证据 |
| AC-10 修订 3 | `EndToEndTests.*`（生产入口逐阶段：prep 读齐即停交 G4、receipt 缺 G4 不开单元、部署 sha 不符停在服务前、完整 play 阶段含网页/计划/会话/归档/摘要/反馈）；`ReleaseGateTests.*`；`SshUnitTests.*`；`ServeTests.*`；两页映射见第 1 节 | 前台服务监督与 `-tt` 中断**未在真实板验证**（SUB:3 可选） |
| AC-11 修订 1 | 网页只显示会话写出的预览原字节（sha 绑定，不重绘、不换框、无几何提示）；`HttpTests.test_preview_and_frame_paths_are_bound`；`FidelityPageTests.test_fidelity_page_serves_bound_samples_read_only`；本机浏览器探针（F-2/F-3） | **≥2 张离线样帧人眼保真核对 NOT_RUN**（SUB:2，执行人待用户指定） |
| AC-13 修订 1 | 本节与第 1 节逐文件映射；验证清单先于停点；focused 原输出 | 停点全套 NOT_RUN（SUB:1）；不以待签/待测自证稳定，不申请 engineering §6 替代 |
| AC-14 修订 1 | `FeedbackTests.test_feedback_only_after_summary_once_per_attempt`；`ConsistencyTests.test_feedback_kept_verbatim_and_separate`；Play 按钮时刻记 UNKNOWN（`run_attempt`）；无自动重试（`stage_play`/IR-OPS-4） | 正式 `-play.md`/`-ledger.json`/Unity 日志后置（正式证据停点） |
| AC-15 修订 2 | `ReceiptTests.*`（measure 非 0 不跑 k-receipt；7+`S_ENVELOPE` → `S-ENVELOPE`；其余 → 停全部；k-receipt 6/8 → `S-RECEIPT`） | 真实收据后置 |
| AC-16 修订 2 | `SourceTests.*`（含缺件即停、不复制）、F-4 只读核 Air 现有原件、`EndToEndTests.test_receipt_requires_g4_then_runs_unit_2`（附录 B 原文生成 `runtime_build=b1234`）、`IdentityTests.test_identity_ok_and_failures` | 板端后置 |
| AC-18 修订 1 | `ConsistencyTests.*`（计划/提交/回执/显示一致性、外来写者、未显示即确认）、`ScoringTests.*`（恰一次、只引用） | 正式归档与独立复核重放后置 |

## 3. 实现读法（IR）

见验证清单第 4 节 IR-OPS-1…6（G4 与 1.6 登记的机读形式、`S-REBUILD` 机械证明判据、环境性重试入口、诊断模式合同、非选择分支的观察窗）。均已 fail-closed 实现，不自行放宽。另两点只作说明、无需裁定：

- **浏览器「已显示」**：预览须在可见标签页中 `img.decode()` 成功才回报；标签页隐藏时浏览器不完成解码，确认按钮保持禁用（等价于「未显示不可确认」）。
- **单写者**：运行期间第 9 节逐字命令只由工具/网页发出；手工 CLI 仅限 `status` 只读与工具停止后的后备（操作单第 0A 节）。

## 4. 稳定候选四条件（未满足；不交 C）

1. 范围完整：§3 闭集代码/测试/文档已落地——满足（待裁定项按 fail-closed 实现）。
2. 停点测试：focused 通过；**停点全套未跑**（N-1 3/3 已用尽，新额度未签）——不满足。
3. 人眼保真：AC-11 修订 1 的 ≥2 张离线样帧核对**未执行**（执行人与额度未定）——不满足。
4. 复核范围与完整 diff：可由 `git diff db10b5e..<本轮末提交>` 运行时得出；但条件 2/3 未满足，不进入核对轮。

## 5. 未核风险与已知限制

- 前台服务监督依赖 ssh `-tt` 把 `\x03` 交给远端 pty（INTR → SIGINT 到前台作业）与交互 bash 作业控制；只用本地替身验证，**真实板行为未验证**。
- 计划冻结读取操作单第 7 节两行 B/C 读数的固定写法；该两行改写即 `plan` 停。
- 收尾反馈等待有上限（`--feedback-wait-s`，缺省 1800 s；板已释放、不占资源），到期或 Ctrl-C 即记缺失为「未反馈」。e2e 测试曾因替身操作者线程读取 `state=None` 崩溃而在无上限等待处挂起，已修测试并加该上限。
- 本机探针用的替身会话不运行真实跟踪/模型；会话原流字段只覆盖本工具读取的子集。
- `operator_web` 直接导入 `controller.language_loop`（取 `KReceipt` 校验与常量），该模块的传递依赖不在隔离测试的直接导入断言内（直接导入与字符串已断言）。

## 6. 本轮用量

consumed：none（零消耗）。SSH/板/Unity/Play/真实模型/归档回放/全套/5060/云/API/下载/安装/正式 ID 均 0；本机 127.0.0.1 探针 3 次（操作页 1、保真页 1、启动核对若干 HTTP 请求），只读来源核 1 次、计划冻结探针 1 次（scratchpad，不入仓）；墙钟约 00:35Z–01:30Z。

## 7. 后续轮次 `OPS裁定落实与停点验证`（2026-10-08，Implementation）

IR-OPS-1…6 与诊断模式合同（「OPS验证额度落实与IR裁定」§3–4）已落实于候选代码 `d0bba83`；SUB:1 全套已跑 1 次、SUB:2 待用户本人看图。逐项落点、全套基线/新增分列、人眼保真准备与新待裁定 IR-OPS-7/8 见 `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md`。本文件第 4 节「未满足」判断仍成立（条件 3 未齐），不交 C6。
