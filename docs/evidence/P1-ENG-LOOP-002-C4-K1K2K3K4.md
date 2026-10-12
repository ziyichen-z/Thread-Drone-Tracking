# P1-ENG-LOOP-002 — C4@K1K2K3K4 候选异源核对

日期：2026-10-07；Acceptance / Codex；候选实现者 Claude Opus。Dispatch-Id：`P1-ENG-LOOP-002-C4@K1K2K3K4-20261007T171403Z-ed9e`；requested.round：`C4@K1K2K3K4`。

## 0. 对象与读取范围

候选、代码候选、最近通过与轮候选基线，均逐字执行 `docs/evidence/P1-ENG-LOOP-002-stable-candidate.md` §0 解析式取得，不把当前派发登记 HEAD 当候选。全量核对为 `$PASSED..$CAND`，修复触及行为 `$R2_ROUND..$CAND`；另读 `$MID..$CODE`、`$CODE..$CAND`。最近实际通过/轮候选两基线相同；后者至候选的 PLAY_GOVERNING diff 非空（7路径），仅证明 diff 开轮资格的一部分。代码候选至稳定收工只有4份状态/证据文档，未混入新实现。派发登记之后开工工作树干净。

完整22路径 diff 已逐文件重读，未排除授权、协调/其他角色内容；直接关联读取覆盖 HttpAdapter 全路径、SingleFlightRuntime/HTTP handler/账与 llama 启动、LlamaServerAdapter、测量/收据生产入口、LanguageSession.__init__/validate_jetson_session、摘要函数、旧 HTTP 用例及冻结测试。合同沿 D4 ACCEPTED 的 engineering-v1、AC-1…18、三条早期解释、AC-7修订2/3、AC-10修订1、AC-15修订1及现行授权边界；逐条追 stable §2–9、r3answer §1–5、C3 PR-8…14、复核 R1/R2与旧 R3派发 O-1…6、precheck完整原流与核清、mini准备、全套/红绿日志。继承清单、完整缺陷账本与本项 H-1…12及暂停承接限制已核；旧证据只携带既有范围，不升级诊断/负结果。

全局消耗门机读来源覆盖全部 reviews 与 implementation-status：唯一实质 block 为 ACQ R2-1，同文件后续 release 顺序配对（R2 §3 / R3 §3），无未释放 block；本轮不写 blocks/releases。全部交接核后0消耗性+2零消耗；Gate-echo一致，暂停不恢复。

| 完整diff路径 | 核对范围/归属 |
|---|---|
| controller/language_selector.py | HTTP账快照/守账、429、绑定后长轮询、等待/期限/失败映射；§4 PR-15…17。 |
| tools/language_serve.py | 十旗标、真实健康尝试记账、跨批账、长轮询参数/条件变量/访问日志、启动退出与释放；原计量修复携带R2。 |
| tools/eng_loop2/llama_adapter.py | health_attempt失败终点；请求/响应/loopback/identity直接关联全文。 |
| tools/language_latency.py | Jetson单轮/首失败停止、身份失败报告/退出7；旧宿主缺省两轮保持。 |
| tests/test_llama_server_adapter.py | 完整增量与直接生产符号映射；软/硬done覆盖，迟到failed/亚毫秒见§4。 |
| tests/test_language_latency.py | 完整增量、替身长轮询回显、测量首失败及旧宿主保持。 |
| docs/evidence/P1-ENG-LOOP-002-play-ops.md | 全文及完整diff；属PLAY_GOVERNING，不作普通docs豁免。 |
| docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md | 准备入口统一chan、旧全套2/3纠正；历史轮未跑与最新3/3分开。 |
| docs/evidence/P1-ENG-LOOP-002-precheck.md | Air停止、mini补核全部新增原流/接受解释；UNKNOWN后续读偏差/库与Python事实限制保留。 |
| docs/evidence/P1-ENG-LOOP-002-r3answer-candidate.md | 中间提交非稳定、原投影与追加更正，不能以摘要代替代码。 |
| docs/evidence/P1-ENG-LOOP-002-stable-candidate.md | 全文，四条件/AC/文件/资源/读法五项/未验证逐项核。 |
| docs/evidence/P1-ENG-LOOP-002-tests-stable.log | 全部失败栈/摘要/计数：2336，4 failures+9 errors；与rework1的13个FAIL/ERROR名称排序逐行相等（只读解析，不跑测试）。 |
| docs/evidence/P1-ENG-LOOP-002-stable-redgreen.log | 全部20例结果：17红（含2超时）、3保持绿；不称全部20修前红。 |
| docs/evidence/P1-ENG-LOOP-002-C3-K1K2K3K4.md | 旧11路径核对与PR-8…14原主张；不覆盖新代码。 |
| docs/proposals/P1-ENG-LOOP-002-closed-loop-four-numbers.md | 完整候选diff，现行AC修订/原签效力/未闭门；本轮只更新核对表和交接，不改合同。 |
| docs/reviews/P1-ENG-LOOP-002.md | 完整diff及真实R1/R2、旧REVIEW_BLOCKED/O表；未开R3、无新机读轮候选。只读。 |
| docs/authorizations.md | 完整候选diff原话/范围/信封；不从实现摘要生成或扩大授权，不写账本。 |
| docs/evidence/supervisor-dispatch.jsonl | 全部区间派发/核销及本次requested；是角色调度记录，不免除候选范围核对。 |
| docs/current-status.md | 所有相关门/交接、原计次与当前未闭义务；本轮同步新C4指针。 |
| docs/implementation-status.md | 全部diff、工程继承/债账；ACQ具名cause CLOSED仅限LOOP已审修复，其他OPEN保留。 |
| docs/parked-status.md | 旧ACQ具名cause指针同步，其他角色暂停台账；不恢复或追认旧候选。 |
| docs/phase1-single-drone-design.md | 完整diff及对应架构/接口/本项合同/硬件边界；不回溯研究轨道。 |

§4.1之外的 dispatch/parked 为其他角色调度/暂停台账同步，非功能或基础设施修改；已逐文件核实际内容，不以“其他角色”或“都是docs”豁免。其余功能diff均在归属表，冻结件、LanguageWorker、CandidatesBackend及预览/采集/保存路径未触及。

## 1. 结论与稳定门边界

**C4已核，附不满足项与未决关注照交新鲜Review，先独立核稳定四条件，再判 R3@K1K2K3K4 资格。** 同停点首退1/1已用，不能再退回。最新逐AC核对表只在提案「Contract conformance（核对表）」；AC-7修订3的I/O证明与R-1不一致，AC-10修订1(b)后续门/许可差异核对不完整，具体见§4；不签独立finding/分级/verdict，不替Review预签稳定门或开轮。

| workflow §4.3.1条件 | stable §2自证与本轮核对 |
|---|---|
| ①范围/接口冻结、按AC具名自证 | 三项原未决执行口径及IR-N1/2已在合同层冻结，IR-M7占位消除；有22路径完整解析和逐AC证据。冻结后忠实性仍有本轮具名异议，不能把R-1读法当改合同。Review独立判断自证条件是否成立。 |
| ②已知自动失败处理与相称验证 | focused488 OK/skipped3；全套2336 FAILED(4/9/skipped19)，13名称与上一轮逐行相等、新增0。失败归类仅沿原证据，不把未重跑基线说成新实测；红绿20例中17红/3保持绿。代码触及真实加载器路径，按冻结要求用了N-1最后一次全套；bash-n11/11仅语法证据。 |
| ③已知Unity失败 | 本轮无Unity/Play，没有新Unity失败；不是Unity通过或UNITY_NA。 |
| ④完整范围/状态/推送/风险 | stable §0/§5/§7/§9提供对象、范围、未核项和已推送指针；本轮把异议及最新合同表一并交Review。 |

实际C1/C2/C3/C4；复核实际R1/R2，R1一次REWORK_REQUIRED（1/2），无冻结集。旧“R3派发”只REVIEW_BLOCKED、未开轮，下一实际轮仍R3。Overall REVIEW_PASSED/ACTIVE仅保持旧R2范围，新代码/操作单未经独立通过；B-main/N-3已签但运行未放行。

## 2. 实现§8五条读法核对

| 读法 | 核对 | 原文/代码依据与界限 |
|---|---|---|
| R-1 单次I/O仅随T_hard | 不满足 | CHANGE5答复落实 AC-7修订3证明方式逐字要求“I/O随两种剩余收缩”；selector::_long_poll_result传remaining_hard，_call只min(5,hard)，新test名io_tracks_t_hard也只断言hard。w和done后重核不是I/O随T_ret收缩的证明。旧LOOP-001 AC-8注释不能覆盖本项新冻结条款；本轮不认可或追加合同豁免。PR-15。 |
| R-2 次数/软截止timeout，硬截止fatal | 满足 | _abandon_after_t_ret保留awaiting_idle/unconfirmed；第17次前退出，late done soft/hard具名夹具，hard为worker_stuck/fatal，无新原因码。迟到failed分支与<1ms边界仍有未决PR-16/17，不因此扩大本行支持范围。 |
| R-3 同一32行smoke | 满足 | 提案§3.2沿现行3预热+32计时，操作单§2/§5明确LOOP-001来源路径，生产read_smoke_rows按行序读取并核有声明的frame_sha256，前置另断言32；stable记录SMOKE_OK32。此为源集/代码静态核对与实现读数携带，非本轮新模型测量；逐图缺sha的通用兼容行为不等于本项允许无身份输入。 |
| R-4 绑定六键后启用 | 满足 | bind_identity核llama六键、先/status逐键比对成功后long_poll=True；启动/测量探针只status；原非llama与未绑定分支仍短轮询，相关旧HTTP用例与源码已读。 |
| R-5 服务保留无参数即时result | 满足 | parse_result_target/build_server/handler在llama下区分有参/无参；无参即时、无wait回显。绑定新客户端始终带wait_s并核回显，旧服务不支持即失败无短轮询回退。是向旧客户端兼容，不放宽新绑定路径。 |

## 3. 新修订、旧观察与预复核关注的逐项落点

| 合同/原ID | 静态核对与证据覆盖 | 未闭界限 |
|---|---|---|
| AC-7修订2(a) / PR-11 | LLAMA_RESOURCE_FLAGS十项逐字固定，llama_server_command及LlamaResourceFlagsTests对应；300s原值、0.25s未改。 | 真实二进制/板端资源兼容未验证，JET诊断不替代。 |
| AC-7修订2(b) / PR-9 | HttpBudgetLedger健康每次成功/失败终点落账；两批复用同一账且上限一致；客户端_call前business守账，服务请求前守账/429，health预算不足退出6；操作单§0.4/0.6列H2/H3、status3/≤11、result≤16/次、收尾0与预留25/11。相关HealthPollLedger/TwoBatchLedger/ClientBudgetGuardTests源码及日志齐。 | 保存终点前SIGKILL可能丢最后在途落盘，stable§9披露；失败停止/故障重启0不改变。潜在560/4800大于200，不能保证全部做完；未齐JET时延原件UNKNOWN。 |
| AC-7修订3(a) | query_id参数分离、有限正w≤4、完成/失败条件通知、stuck重核、pending到w；LongPollServerTests对应。 | 毫秒量化另见PR-17。 |
| AC-7修订3(b) | 无额外sleep、第17次前停、HTTP错误不重试不回退、每result前守账；LongPollClientTests对应真实入口端到端一次wait。 | 每次socket I/O与回包截止见PR-15/16。 |
| AC-7修订3(c) | w同时收缩，done重核软硬截止、测量60s/K派生不改，旧非llama保持。 | I/O两种剩余证明不成立，PR-15；failed回包PR-16。 |
| AC-7修订3(d) | §0.6逐条路径、预留来源/实际两批式与失败终点齐，旧必然不可完成投影追加更正。 | 正式账未产出，不以规划或假时钟做板端耗量保证。 |
| AC-10修订1(a) / O-2、PR-10 | ops§0.5主连接/有限通道表、unit_open/chan/unit_close与§2/_Recovery/准备入口统一；mini§2.3调用chan，旧Popen直连删除。chan先-O check失败返回99，不到后续ssh；竞态回退改为localhost:1/Proxy none/BatchMode，不对板新认证。尝试/失败/关闭计时原账不免除。 | 零板静态检查支持“无socket先停”的显式分支；真实SSH竞态/控制通道/Ctrl-C未验证，沿stable§9披露，不尝试连接。 |
| AC-10修订1(b) / O-1、PR-8 | ops§1固定REL、从该引用读review/账本；候选祖先+最新pass位于latest round后；完整PG含本操作单。只读git解析的当前7路径非空，旧R2 PASS+新操作单会输出STOP；§1.1实际HEAD、1.2整树status、1.6原流先于独立文档登记/再核同值。 | 后续门状态/其余许可差异未完整核，PR-18；静态设计不等于正式现场HEAD/status或Unity日志已齐。 |
| O-3 | ops§14把单元STOP与仅非主臂S-REBUILD下一既定剧本分开，原因不明/主臂仍停全部。 | 不重跑本次/不开新单元重试。 |
| O-4 | 抬头全部块bash，板serve块exec bash+pipefail，PATHS分词环境固定。 | bash-n11/11不作Air/板运行验证。 |
| O-5 | serve块cd … || exit97，错误目录不能继续后续语句。 | 启动ss失败边界仍PR-19。 |
| O-6 / PR-13 | mini§7历史轮纠正2/3/该轮未跑；stable§6最新3/3用尽。 | 13既有失败仍FAILED，不重置/转用全套。 |
| PR-12 | G1/3/5先于准备，G4由准备产生；附录P readelf/ldd/Machine/pgrep/ss逐项fail-fast；_Recovery按-e或-L存在即停。 | §4另一个ss启动检查仍有失败当无监听路径，PR-19。 |
| PR-14 | 目标Python动态闭包、ABI/函数内标准库依赖仍UNKNOWN；ENV:2条件性未签0。 | 不以CPython源树/少量PyInit/隔离/文件存在宣称可import；正式环境事实门保持。 |
| AC-15修订1(a)/(b) | JETSON_MAX_ROUNDS=1，Jetson stop_on_failure=True；首SelectorError/60s失败停余下，not_attempted/stopped_after_first_failure；探针失败写FAIL报告且零推理/退出7；S_ENVELOPE detail保留。JetsonSingleRoundStopTests/原JetsonMeasurementTests对应。 | 板生产收据NOT_RUN，旧宿主缺省2轮不改。 |
| AC-15修订1(c) | ops§5 measure rc非零即停，不调用k-receipt/不开Play；7先分budget原因，否则主臂首失败停全部；0才进0/6/8收据语义。 | 不重测，不从335余额重启；真实退出/收据未知。 |

## 4. 带具体依据的预复核关注（待核实主张，不是finding）

编号沿C3 PR-8…14继续，不改历史结论、不新增AC或预定finding分级。

| ID / 合同指针 | 直接依据与可区分的关注 |
|---|---|
| PR-15 / AC-7修订3(c)及其证明方式 | selector.py::_long_poll_result约912–916向_call传remaining_hard()，而冻结证明要求“I/O随两种剩余收缩”；test_wait_is_min_of_4s_and_both_remaining_deadlines_and_io_tracks_t_hard明确只核hard。例：T_ret剩余0.5s、T_hard剩余10s时w=0.5而I/O=5s。R-1对竞速的理由不改变冻结条款，不能签满足。Review核其行为及证明差异。 |
| PR-16 / AC-7修订3(c)、既有硬截止/失败映射 | _long_poll_result约931–938只在done分支取after/检查两截止；约953–961 failed直接清awaiting_idle、in_flight/unconfirmed再抛原error。若failed回包跨T_hard，未置fatal且锚点清掉，可与迟到done判死不同；当前failed测试是即时失败，late测试只done。Review核“回包后重新核T_ret/T_hard”是否被该分支漏掉及会话路径后果，本轮不运行探针。 |
| PR-17 / AC-7修订3(a)(c) | long_poll_wait_text向下整毫秒，_long_poll_result约905–910在hard_left=0.0005s、ret_left更大时已判worker_stuck，即实数正剩余仍在却按T_hard exceeded/fatal。合同是“没有正剩余即停止”，没有冻结1ms到期容差；夹具未区分亚毫秒正数/真正零。Review核是否改变截止语义及所需证明；不在C轮追加容差。 |
| PR-18 / AC-10修订1(b)、O-1/PR-8 | ops§1.0约144–159仅取last round/pass序号与祖先、检查PG空、打印其余文件；没有核passed行之后REVIEW_BLOCKED/其他门状态，也没有逐一核其余差异是否为规则许可文档。旧R3派发实际不含round_candidate，故“没有新round行”不等价后续门未阻断。§1.5两自检不判本项新操作单独立通过/运行放行，§1.6称日志仅允许许可文档却不补该核对。当前候选会因PG非空拒绝，不能因此证明以后“PG空但后门已阻断”也拒绝；Review核全流程中的有效门/白名单是否齐。 |
| PR-19 / AC-10、PR-12停止纪律 | ops§4约240的ss -ltn | awk | grep … && STOP，即使pipefail开启，ss失败也只令AND左边失败、没有进入STOP；其后pgrep可能均rc1而继续启动。附录P已有SS_FAIL显式停止，但那是较早准备单元，不替代每次serve启动这一调用失败。Review核此真实命令的未知监听处理；不在接受会话修脚本或运行它。 |

SSH竞态回退、Ctrl-C/释放、真实flag/栈兼容、TCP时延/半包、账在请求结束落盘、预留不随本批必需status递减等限制按stable§9原样随交；非本轮已核硬件行为。没有通过这些未知项默示消耗性放行，也没有把观察升级finding或冻结集。

## 5. 用量、未闭项与Review交接

本轮只读文档/源码/git与日志文本解析、文档编辑、自检及提交推送；不跑功能测试或复核探针、不加载模型、不SSH/复制/Jetson/Unity/runtime，consumed=none；不写用户原话账本或复核文件。

N-1最新累计3/3用尽（stable§6），若Review判还需全套先回用户另签；本轮不预定窄修替代或新增测试额度。miniSSH1/1结束、Air旧余额作废、旧N-1各轮/回放账和偏差/UNKNOWN不改。AC-14/15/18与AC-16板端NOT_RUN，无UNITY_NA/DONE；ACQ暂停/非verdict/清理与OPEN债保持，无新release/里程碑证据。

下一Owner Review、新鲜上下文、一次性worktree，requested R3@K1K2K3K4；先按stable§0解析真实候选并完整核§2四条件（本文件§1异议同读），再按工程§6/workflow§4.4判开轮资格。具资格时基线取最近实际round_candidate/通过行、完整PLAY_GOVERNING增量与直接关联代码、适用AC及本文件§2–4；未改动行按既有增量规则，不能把本轮关注当已签finding。稳定门不成立由Review记录REVIEW_BLOCKED、不开轮。B-main执行等待新候选通过、Air本人FACT:2/目标依赖事实与接受逐维度放行、现场HEAD/status/Unity日志及AC-18后续证据停点；本C不代这些门。
