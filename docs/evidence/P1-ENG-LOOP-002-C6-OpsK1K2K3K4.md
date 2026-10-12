# P1-ENG-LOOP-002 — C6@OpsK1K2K3K4 核对依据

角色：Acceptance / Codex；2026-10-08。Dispatch-Id：`P1-ENG-LOOP-002-C6@OpsK1K2K3K4-20261008T040053Z-0d34`。
这是对 Claude Opus 实现的异源只读合同核对，不是独立复核。未跑测试、SSH、板服务、Unity/Play、模型、回放或 API；未改实现/测试/AC/复核文件/用户原话账本。consumed=none。

## 0. 输入与基线

候选从 `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md` §7 的“候选提交”行解析；完整 Ops 增量基线从该节“完整 Ops 增量 diff”及 `docs/evidence/P1-ENG-LOOP-002-ops-progress.md` 页首派发基线解析。独立复核的全量基线从 `docs/reviews/P1-ENG-LOOP-002.md` 最新已消费的 `R1@K1K3` 的 `passed_candidate` 解析，不能用最近文档提交替代。

读取了两段完整 diff：上一通过候选至 Ops 派发基线，以及 Ops 派发基线至本候选；合起来为上一通过候选至本候选全部 29 路径。候选至本轮开工 HEAD 的上述 PLAY_GOVERNING/操作单/精确忽略路径差异为空；后续证据指针补充也已读，未拿文档 HEAD 冒充代码候选。标识均沿已有机读行/派发记录运行时解析，不在本文件手写派生 SHA。

生效合同：同名提案原 AC-1…18 和全部追加修订，重点完整重读「OPS九题答复落实」§1–6、「OPS验证额度落实与IR裁定」§1–5、「OPS基线与IR78裁定」§1–5；累计修订25、新 AC 0。已读取四条件/逐 AC 指针、原测试日志、窄修红绿及替代适用性、人眼记录，以及最新 R1@K1K3 与继承限制/缺陷账本；没有重跑其中命令。

## 1. 完整候选范围

以下逐文件读过 diff 与理解变更所需的代码/证据。`tools/eng_loop2/play_ops.py`、`operator_web.py`、`summarize_ops.py` 及对应三份新增测试完整读取；隔离测试增量和直接关联的原 CLI/会话/确认/收据/评分接口一并核对。

| 文件 | 本轮核对用途 |
|---|---|
| `tools/eng_loop2/play_ops.py` | 正式/诊断路由、门、SSH单元、监督、调度、预算、STOP、收尾与归档 |
| `tools/eng_loop2/operator_web.py` | 原CLI、绑定/时序、共享提交、防重复、预览与反馈 |
| `tools/eng_loop2/summarize_ops.py` | 计划实际映射、客观事件/原评分引用与隔离 |
| `tests/test_eng_loop2_play_ops.py` | 生产入口替身与模式、门、原流锚点、预算/失败覆盖 |
| `tests/test_eng_loop2_operator_web.py` | 状态/令牌/时限/并发/反馈覆盖 |
| `tests/test_eng_loop2_summarize_ops.py` | 计划映射/原流一致性/评分引用覆盖 |
| `tests/test_loop2_isolation.py` | 在线工具/离线评分边界扩展 |
| `.gitignore` | IR8精确 `/outputs/eng-loop2/`，没有泛化忽略 |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md` | 正式步骤、原门/STOP/额度映射 |
| `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` | 旧启动块窄修和现行SUB:3诊断入口 |
| `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md` | 现行准备入口说明 |
| `runtime/README.md` | 原CLI/新桌面入口说明 |
| `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md` | 完整交付/四条件/逐AC/风险/IR78替代说明 |
| `docs/evidence/P1-ENG-LOOP-002-ops-progress.md` | 基线、初始实现、证据与限制 |
| `docs/evidence/P1-ENG-LOOP-002-ops-validation-plan.md` | 验证清单与消费边界 |
| `docs/evidence/P1-ENG-LOOP-002-ops-tests.log` | SUB:1全套原输出及基线失败 |
| `docs/evidence/P1-ENG-LOOP-002-ops-focused-tests.log` | 初始focused原输出 |
| `docs/evidence/P1-ENG-LOOP-002-ops-ir78-tests.log` | 窄修修前红/修后绿及118例记录 |
| `docs/evidence/P1-ENG-LOOP-002-C5-K1K3.md` | 已通过范围的核对依据 |
| `docs/evidence/P1-ENG-LOOP-002-diag-page-fix.md` | 原诊断页窄修与离线限制 |
| `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md` | 旧证据计数逐字补丁 |
| `docs/proposals/P1-ENG-LOOP-002-closed-loop-four-numbers.md` | 生效合同/修订/历史裁定 |
| `docs/reviews/P1-ENG-LOOP-002.md` | 上一有效通过与范围/计数/未验证项 |
| `docs/authorizations.md` | 原话及逐维度授权；只读 |
| `docs/unity-test-log.md` | 本人两张保真与旧诊断记录；只读 |
| `docs/evidence/supervisor-dispatch.jsonl` | 派发基线、实现来源与核销；只读 |
| `docs/current-status.md` | 当前门、交接与未闭义务 |
| `docs/phase1-single-drone-design.md` | 已接受合同与主张上限 |
| `docs/implementation-status.md` | 继承/未闭债务与旧范围证据 |

未改变 controller、Assets、config、模型加载器、原 analyze_play 指标算法及其数据划分。不能把新增调度层的失败遗漏按“底层零diff”豁免。

## 2. 首次退回核对项

本节编号只是核对表行，不是独立 finding；不签 CLASS、BC 归因、blocks/releases 或 Review verdict。逐项对应已有条款，未新增 AC 或修订。**Ops停点首次 C 核对，退回使用 1/1；本次交实现。**

| 核对项 / 结果 | 现有合同依据 | 可核实的代码与后果 | 交实现逐项核对的完成条件 |
|---|---|---|---|
| C6-1 / 不满足 | AC-10修订3 W4/O3；修订4 IR-OPS-5及诊断§4.7；AC-14修订2 | `DiagnosticRun.play()` 捕获 DiagStop/DiagFault/首次 Ctrl-C 后仅设局部 `halted` 并调用 `request_stop()`。下一轮仍调用 `PlanScheduler.tick()`；`finish_play()` 也继续 tick。`request_stop()` 没有封住调度器业务状态；`App.action()` 只靠 `scheduler.blocked()` 禁止非stop，读到尚未TERMINAL的有效状态仍可发送/跳过/确认/拒绝。因而 STOP/故障后，在stop回执/终态延迟或未知期间仍能新增业务，旧观察也可推进release/下一步。 | STOP/故障/中断一发生即不可逆地封住 runner 与网页的业务动作，只保留原合法stop和安全收尾；迟到回执/状态不能自动恢复。stop仍沿共享原CLI通道、同会话至多一次，不加重试/换id。提交覆盖活动Play中STOP1/故障/Ctrl-C且TERMINAL迟到或UNKNOWN的零模型生产路径证据，核前后业务动作均不能续行。 |
| C6-2 / 不满足 | AC-10修订3 O1/O3及失败安全收尾；AC-14原按钮墙钟420s与修订1 | `run_attempt()` 的session进程到硬截止仍在运行时直接抛S-WALL；没有发原stop、等待该会话、提示本人停Unity及归档。正常进程退出后若出帧未静止也在归档前抛S-WALL。外层 `stage_play()` finally只停止/核释板服务、回传日志、关闭单元、写记录，持有的局部session进程未收尾；KeyboardInterrupt/其他异常还会跳过摘要/反馈收尾和本地网页关闭。截止是等待起点+420+120，不能证明按钮420s。 | 正式失败/超时/中断也经过已签的会话中断/等待、本人停Play提示、保留式记录/归档及独立的服务释放/本地退出；一项收尾失败不能跳过其余安全步骤。不能杀未知进程/清锁或伪造按钮时刻；无法证明的退出/按钮墙钟记UNKNOWN、停依赖。Play前等待不能算作把按钮420s扩成540s的许可。交具名零模型替身核挂起session、Unity仍出帧、Ctrl-C/异常及部分收尾失败路径。 |
| C6-3 / 不满足 | AC-8修订3完整预登记计划逐步实际/原因；AC-10修订3保留失败原流/rc/原因/实账；AC-14修订1；AC-18修订1对应一致性 | `run_attempt()` 已填局部record的steps/会话rc/终止/计时/加载/归档后，在S-LOAD、S-BACKEND、S-REBUILD等路径抛异常，局部record未返回。`stage_play()` catch只保留调用前的playbook/session_id占位，再附stop；写出的attempt丢失既有实际步骤等。`summarize_ops.summarize()` 把缺失steps传给 `plan_vs_actual()`，全计划变NO_PLAY_RECORD、已发送数0/未执行数增加，即使原流已有受理请求。原流未被删除、原四表算法也未改，但新增摘要与实际矛盾且失败对应记录丢失。 | 所有退出路径持久化同一完整尝试记录；已知步骤、request_id、拒收/失败/停止原因、rc、可得时刻、加载与已产归档指针保留，确实未执行与记录未知分列。失败不把已发送/受理步骤改成未执行，不事后删样本或补造受理。交生产入口S-LOAD/终止失败/部分收尾失败到计划—原回执—摘要的具名零模型证据，证明已受理命令及失败原因仍可逐步对上。 |

上述覆盖要求是现有“生产入口逐阶段正常/失败”“完整计划实际对应”“安全收尾”证明方式的核对，不另立测试合同。现有 EndToEnd/Diag正常路径和前置拒启测试不能证明这三条失败路径；本接受轮只读测试，没有执行。

## 3. 稳定门与证据限制

①范围/接口已经冻结，IR1…8有裁定；本轮不打开合同解释，也不增改AC。②SUB:1全套2430例、5 failures/13 errors/54 skipped及12项新增环境基线接受按先前裁定携带，不能改称全绿；IR78窄修118例及修前红/修后绿指针齐、替代理由已列，但不证明本节遗漏的失败路径。返工须先修已知问题并提供相称证据，补跑若涉及SUB:1只能依原剩余候选次数/逐候选一次/具名原输出规则。③本人两张保真已经转记候选，代码呈现未变；提示行/用时未报告仍UNKNOWN。④已提交推送、自证与准确指针齐，依赖动作已停。

本轮可做C核对，但三个合同不满足不能据自证文字签通过。正式AC-14/15/18和AC-16板端仍NOT_RUN，诊断/正式运行均未发生；不把缺后置实跑证据作为新的C退回理由，不签UNITY_NA/DONE。旧R4终局/冻结集闭合/返工2/2与新K1K3 R1 PASS/返工0/2、N-1全套3/3及既有债/偏差/UNKNOWN/暂停保持。

## 4. 预复核未决关注项

- **PR-O1，sub3_release全文匹配**：交付风险已核。`DIAG_RELEASE_LINE` 与 `DiagnosticRun.preflight()` 在提案全文搜索值；IR7裁定要求只有接受角色在「OpsK1K2K3K4通过消费与SUB:3放行」节写真实行，值必须等于门核最新有效passed_candidate，但未把“节定位解析”单列为机读判据。本轮不添加解析节限定AC，不写真实放行行。交Review核全文匹配在现合同下的风险，尤其旧行/示例/重复行与值绑定；现有示例占位、读失败/缺行/错值均拒启的测试范围不能冒充真实消费。此项作为未决关注随下一C照交。
- **PR-O2，真实板前台监督**：`SshUnit/ServeSession` 与 `DiagConnection/DiagServe` 的真实SSH交互、Ctrl-C传播、120s等待及同主连接释放仅有本地替身；没有本轮真实板验证。原合同明确SUB:3后置代码C/R通过消费，不能为补C证据提前消耗一次诊断。本轮保留未验证风险，Review可核替身证明范围，不把静态核对称板端通过。
- **PR-O3，正式评分失败与调用预算**：`stage_play()` 完成各剧本后才启动独立 `summarize_ops`，后者逐归档调用原score，`main()`未把嵌套score非0自动作为退出失败；正式S-ARCHIVE/layout_unbound/frame_identity_mismatch处置与摘要一致性需要Review核实。正式操作页新增映射所说逐归档评分，与既有实现≤2正式评分/回放次数的计量单位及执行顺序也须核清；本轮不放行运行、不授权第3次或任何回放，不允许真值结果回流在线。若实现遇合同实质歧义，仍提交具名待裁定项，不自行扩额或改变停止条件。

## 5. 下一交接与复核范围

本次 **C6@OpsK1K2K3K4 首退1/1**，由实现仅在已接受闭集内完成§2三项，按原四条件/逐AC证据整理新候选、提交推送并停止依赖动作，交下一实际 **C7@OpsK1K2K3K4**。该次核对不得第二次退回，即使有未满足/证据缺失也将附最新版核对表与§4未决关注照交新鲜独立 **R1@OpsK1K2K3K4**；稳定条件是否成立由Review先行核实，不满足给REVIEW_BLOCKED不开轮。

独立复核范围：修复候选由新交付机读/具名证据运行时解析，完整基线仍取上一通过R1@K1K3的passed_candidate；读完整diff、不仅返工diff。PLAY_GOVERNING为 `tools/eng_loop2/{play_ops,operator_web,summarize_ops}.py`、三个对应新测试、`tests/test_loop2_isolation.py`；三份具名操作单、`runtime/README.md`及`.gitignore`一并核查，实际全量路径由git派生。重点为§2三条、全部生效Ops AC/修订、隔离/身份/检查点/原流锚点、模式/资源/STOP/安全收尾、失败与摘要对应、IR78及替代适用性和§4。不把旧R4终局计数或旧K1K3通过套到新范围。

本轮不签新的复核结论、门release或消费许可。状态板Overall REVIEW_PASSED/ACTIVE仍仅限旧已消费范围；新Ops实现列为C6不满足待返工，SUB:3仍待新范围独立通过及接受消费/sub3_release，G1–G5/现场登记/正式证据门保持。needs_user=none（现有合同三项返工不需另签；未来遇新增消耗或实质歧义另路由）。
