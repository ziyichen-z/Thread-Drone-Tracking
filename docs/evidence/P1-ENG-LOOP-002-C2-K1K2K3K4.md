# P1-ENG-LOOP-002 — C2@K1K2K3K4 异源候选核对

日期：2026-10-06（Unity主机本地）；角色：Acceptance / Codex；实现：Claude Opus。派发：`P1-ENG-LOOP-002-C2-K1K2K3K4-20261007T020009Z-5fdb`。

## 结论与边界

IR-13…17先裁于提案「C1返工读法答复」，随后完整重读候选35文件diff、AC-1…18及已追加释义、四条件自证、C1偏差/PR处置与直接关联代码。逐条核对结果唯一现行表为提案「Contract conformance（核对表）」：AC-7不满足；AC-14/15/16/18阶段B证据缺失；其余满足（限本阶段代码/离线证据）。**首退已用，附表与未决关注项照交新鲜上下文 Review R1@K1K2K3K4，不再退回。** 本文不是独立复核，不分级finding、不签verdict、通过候选或Unity通过，不授权B、消耗或后续实现。

本轮未跑测试/模型/评分重放、未写runtime、未连接板/Unity、未用API/GPU/Play、未创建scenario/session/run ID；consumed=none。只做git/AST源码文本比对与既有日志/JSON读取，不将这些检查当功能测试。Overall=IMPLEMENTED、Lifecycle=ACTIVE保持。

## 候选解析与完整范围

派发日志finished.candidate为权威候选来源；本轮运行时核验其与唯一C1返工收工提交相等且可由origin/main到达。BASE为N-1答复落实核销，PREV为首次实现收工；既读BASE..RW_CAND完整范围，也核PREV..RW_CAND返工增量，不用增量代替完整候选。派发base_head只用于会话对账，不替代实现基线。

```bash
BASE=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 N-1答复落实 supervisor 核销' | head -n 1)
PREV=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 阶段A实现 收工' | head -n 1)
RW_CODE=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 C1返工 代码候选' | head -n 1)
RW_CAND=$(python3 -c 'import json; rows=[json.loads(s) for s in open("docs/evidence/supervisor-dispatch.jsonl")]; print(next(r["candidate"] for r in reversed(rows) if r["event"]=="finished" and r["dispatch_id"]=="P1-ENG-LOOP-002-C1返工-20261007T013203Z-70a4"))')
STOP=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 C1返工 收工' | head -n 1)
test "$STOP" = "$RW_CAND"
git merge-base --is-ancestor "$RW_CAND" origin/main
git diff --name-only "$BASE".."$RW_CAND"
git diff "$BASE".."$RW_CAND"
git diff "$PREV".."$RW_CAND"
```

JSON工件按全部键值无损紧排后分块读取；两个完整测试日志均读全（包括失败栈、计数及资源末段），不是只读摘要。直接关联源码补读SingleFlightRuntime/handler/llama主循环、tick/请求受理/追平指定与scorer归属/窗口/输出；冻结边界以完整AST源码段和git blob文本比对。来源不导入执行生产模块。

## 完整候选逐文件核对

下表35项均已读完整diff；新增文件读其全部内容。其他角色文档/授权/派发未排除。功能修改在提案§4.1闭集，runtime/README是入库文档，非运行时状态；候选没有工作流基础设施改动。

| 文件 | 核对依据与结论 |
|---|---|
| config/p1-eng-loop-002-board-deploy.json | 清单闭集含自身、两个config与纯推理传递依赖；不夹scorer/训练/evaluator。 |
| config/vlm-three-state.schema.json | 三态none/unique/ambiguous、候选框/文本schema；新JSON条件不改冻结prompt/parse。 |
| controller/gated_publisher.py | hold_receipts常驻开关，detail.reason三值与原body_safety_hold通道；段式缺省保持。 |
| controller/language_bridge.py | reason追加、delay/intent可选请求字段、六键全有/全无与键存在/null拒绝；旧reader丢未知字段限制保留。 |
| controller/language_loop.py | A1策略接线、A4呈现与metadata摘要、A5缓存/终止/重建、jetson身份链、cause/事件闭集；tick受理边界PR-2，生产终止指定序列PR-3。 |
| controller/language_selector.py | status_document/bind_identity保留并验证六键；候选解释仍经冻结parse，不加真值/自动重播种。 |
| tools/eng_loop2/__init__.py | 包标识纯文档字符串，无运行副作用。 |
| tools/eng_loop2/analyze_play.py | 样本/归属/C1–C6/复合键、H-2/布局与窗口完整算法；四项C1修复与来源分列v2已核，IR-14/16、PR-3/4/5仍交独立边界核实。 |
| tools/eng_loop2/deploy_digest.py | 清单自身、路径/存在性/摘要校验、规范JSON与共享DECODE_CONFIG；不把历史部署摘要当当前摘要。 |
| tools/eng_loop2/llama_adapter.py | 图像+冻结prompt单次请求、schema/decode身份、finish_reason/原始失败保留、超时/坏响应闭集；板端兼容仍是假设。 |
| tools/language_latency.py | 单jetson报告/收据生成、退出0/6/8、全树dirty、真实status身份、端点/报告/代码绑定；旧两宿主路径保留。 |
| tools/language_serve.py | 资产sha/version拒启、前台子进程/就绪/退出、逐请求日志finally；部分IO计数偏差PR-7与停机PR-1未闭。 |
| tests/test_eng_loop2_analyze.py | 1375行全部读；十二类/冲突/布局/篡改/生存/捕获/分母/归档与C1新增回归对准AC-8；端点精确0.25s夹具不加容差。 |
| tests/test_language_bridge.py | 类型/域/部分六键/null、旧块兼容、reason顺序；不只相信摘要。 |
| tests/test_language_latency.py | 单宿主错配、生产measure/会话前拒绝、真实临时git未提交docs/tests/未跟踪文件与null拒绝。 |
| tests/test_language_loop.py | 延迟/hold/单加载/策略/身份/隔离；新增真实LanguageSession日志经scorer验证终止增epoch、两代同designation_id，底层模型为替身。 |
| tests/test_llama_server_adapter.py | 请求/响应/拒启/清单/隔离部署入口与真实回环日志夹具；handler在响应前抛错、短请求体与坏请求已测，未证明部分sendall/超时read完整字节。 |
| tests/test_loop2_freeze.py | 冻结件及PLAY_GOVERNING闭集差异断言；本轮另以blob/AST读码核验实际范围。 |
| tests/test_loop2_isolation.py | 合法controller→tools闭集与真值隔离、intent仅receipt；与实际import相符。 |
| runtime/README.md | 新原因/六键/事件/metadata摘要说明，对应§7(m)/IR-12；没有运行数据写入。 |
| docs/authorizations.md | 用户N1-LOAD-RECONCILE原话与计数拆分、首次全套有效、额度不重置；既有N-1信封读取一致，非实现首签。 |
| docs/current-status.md | 实现→C1首退→返工→C2交接，Overall IMPLEMENTED；完整表内gate/消费限制已核，非功能代码。 |
| docs/phase1-single-drone-design.md | 接受侧AC释义/阶段状态同步，无新增运行义务；历史C2预记由本次IR-13统一当前读法。 |
| docs/proposals/P1-ENG-LOOP-002-closed-loop-four-numbers.md | 先IR1…12及AC同编号释义再C1，四具名偏差首退；历史D1–D4/N1裁定与授权边界完整读取，不把C1结论当复核。 |
| docs/evidence/P1-ENG-LOOP-002-C1-K1K2K3K4.md | 上轮完整逐文件表、四偏差与PR-1…6原依据；是历史核对证据，不回改。 |
| docs/evidence/P1-ENG-LOOP-002-K1K2K3K4-handoff.md | 候选1原文与返工四条件/AC指针/红绿/用量/IR13…17完整读取；候选1失效自证不混作现行。 |
| docs/evidence/P1-ENG-LOOP-002-archive-dryrun.json | 旧版全键值；两归档输入限制与唯一恒OK读数差异保留，非验收。 |
| docs/evidence/P1-ENG-LOOP-002-archive-dryrun-rework1.json | 返工全键值；试读一致项/原差异未洗掉，新scorer分列、指针epoch与真值时轴；无新Play。 |
| docs/evidence/P1-ENG-LOOP-002-assets-local.json | 本机权重/配置/钉住sha与大小来源齐全；board未核、生成时部署摘要历史性有明示，不挪用JET诊断。 |
| docs/evidence/P1-ENG-LOOP-002-four-numbers-fixture.json | 17合成样本v1历史合并/无center时长缺口保留，不当现行满足证据。 |
| docs/evidence/P1-ENG-LOOP-002-four-numbers-fixture-rework1.json | 17样本v2分列红车14/静止1/意图无效2；数字一raw7、二raw6/S4、三raw6、mislock S4按来源守恒；center时长实际输出。 |
| docs/evidence/P1-ENG-LOOP-002-play-ops.md | 末条通过候选与末轮位置守卫、完整命令、门/日志/体积/墙钟/STOP；命令备单当前不可执行。 |
| docs/evidence/P1-ENG-LOOP-002-tests.log | 全日志2275、4F/9E/19skip、187.21s及计数/原始失败栈已读。 |
| docs/evidence/P1-ENG-LOOP-002-tests-rework1.log | 全日志2300、4F/9E/19skip、191.32s；13失败名与旧日志逐字相同，新增失败0。 |
| docs/evidence/supervisor-dispatch.jsonl | 完整候选内新增10事件：首次实现、C1及返工派发/核销；返工finished与本轮requested/started亦核对。归其他角色文档，不自行删除。 |

冻结核验：LanguageWorker、CandidatesBackend、_validate_candidates_source、render_preview、_preview完整AST源码段与BASE相等；scenario_tether、candidates_preflight、resident_core、track_loop、standoff_planner、冻结prompt/parse、det-assoc spec、FRAME body配置及implementation-status blob相等。故H-1等待域/H-4旧预检/H-5围栏不触发；H-2新metadata生产/评分与H-3cause有代码和夹具，不据此销旧债。

## C1偏差闭合与自证核对

| C1具名偏差 | 本轮核对 |
|---|---|
| C1-AC6 | 两处均闭合：全工作树dirty与部分/null六键拒绝；真实git夹具覆盖跟踪/未跟踪docs/tests，报告/收据/会话拒绝链仍在建会话目录之前。 |
| C1-AC7 | send_error/不支持方法/提前拒绝POST体的原漏记已补；handle_one_request finally逐请求、drain实际字节/完整标志有夹具。**异常IO部分字节尚未闭合**，见PR-7，不能把“每请求有一行”当“实际字节完整”。 |
| C1-AC8 | 四项闭合：Archive.time只真值；_own_pointer_bound限epoch/代/样本边界；center两起点values/median及三结局输出；红车/静止车比率分列。PR-3生产序列修复与PR-4复合编号生产夹具已补。 |
| C1-AC10 | 末条passed_candidate且位于末条round_candidate后，P2/P3等逐字命令含token/session/runtime/共享槽；原操作范围不变。 |

四条件来源为实现交接「稳定候选四条件自证（C1返工）」；本轮仅核其内容/指针与磁盘事实，不代Review裁REVIEW_BLOCKED：范围闭集与未验证风险声明齐全；focused/全套新失败0与已认可基线失败分列成立（自证测试指针可达，未重跑）；Unity已知失败本阶段无新项；候选提交/推送及状态/范围指针齐全。但AC-7“全部满足”的自证主张与上表不一致，Review需据真实代码/四条件决定是否开轮。不得因C轮首退上限放宽自证门。

用量核清（仅读既有来源）：返工全套1次，累计2/3；本返工候选归档回放1/2，候选1回放2/2；每次NanoTrack2，CSRT真实尝试2/实例0（用户已裁替身调用不计），det-assoc0；187.21/191.32s均<15min；交接磁盘约0.24MB<20MB。其他模型加载沿原静态清单“未插桩、无反证”，不拔高为独立计量；跟踪focused数据根解释器缺失及未新Play/真实det-assoc缓存加载未核限制保留。本轮不重跑有效全套或重置计数。

## 预复核关注项

以下沿C1 PR编号续记，非finding、无CLASS/verdict；每项只说明读码依据和未证实边界，不增加AC。

| ID | 现行依据、读码理由与交Review的关注 |
|---|---|
| PR-1 | AC-7前台生命周期/临时图像清理。_main_llama是串行HTTPServer.handle_request，故HTTP handler本身不并发；但SingleFlightRuntime.submit另起daemon线程，POST已回accepted时predict_one可仍在途。finally只server_close→_stop_child→rmtree，没有runtime.join（方法存在未用）。_run仅finally unlink、不写新图像，降低残留风险，却未证明停机等待/读文件竞争无异常；现有隔离用例先等结果done再SIGTERM，不能覆盖在途/就绪失败/子进程退出各清理阶段。实现“非并发HTTP”理由不足以关闭背景线程风险，交独立读码与相称核实。 |
| PR-2 | A4/AC-5受理新命令才丢弃挂起结果。LanguageSession.tick顺序_check_adapter_health→_poll_worker→_maybe_present→_consume_request；延迟到期且单槽已有新ask/respecify/stop时，旧结果可能先展示，再受理新命令。按“受理”字面，此时尚未受理新命令，故本轮未判现合同不满足；但“到期同tick”的受理/呈现receipt、epoch与CLI可见结果边界未有具名同刻竞争用例。现有丢弃用例在到期前受理，不能代替该边界。Review按既有受理语义核实，不据此给新命令抢占加合同。 |
| PR-3 | AC-8修订2/IR-16。_designate_resident先_advance_resident，stop增epoch并写TERMINAL后写unavailable；scorer._unavailable_origin_epoch先限原epoch无样本，再最近confirm/terminal/新受理或指定阻断。Loop2ScorerProductionSequenceTests通过真实LanguageSession产journal，经Scorer验证原样本INTERRUPTED、不再C5；生产路径证据缺口已补（非真实模型）。反向扫描不得跨新受理样本/指定/不可用；独立核实负边界与优先级。 |
| PR-4 | AC-8修订1。常驻代+designation_id复合键与_own_pointer_bound的epoch/代/下一指定边界；新增真实会话两代复用编号夹具和合成“不借其他代/下一样本”夹具。证据已补，独立核其定位与pointer_claim守恒，旧H-2/F8 OPEN不因夹具消除。 |
| PR-5 | §3.5/IR-3/IR-14真值闭时间窗。split_at_time按首个已知t>窗尾截断，包含t==窗尾；误锁帧数从65/66宽松改为同判据精确值，另以0.25s精确夹具覆盖center段末恰截止/再晚一帧。仍须核真值缺时刻、E未知、窗口尾miss延伸和浮点端点无容差；不把由实现公式生成expected的单例当独立算法证明。 |
| PR-6 | AC-18/§7轮次。IR-13已裁本代码核对C2，B证据下次实际C轮（无插入则C3）；不回写原AC。R1尚未开/通过；后续无PLAY_GOVERNING diff只在原复核文件具名证据核实，不虚开R2，不由接受自签证据通过。 |
| PR-7 | AC-7/§5.2/IR-11/15异常字节。tools/language_serve.py::_CountingWriter.write在raw.write成功返回后才count，docstring明确sendall抛错该次不计；socket已发送部分正文再BrokenPipe/Reset时日志会漏该部分。_CountingReader.read/readline同样在返回后加数，BufferedReader可能取到部分正文后timeout/终止，_drain_declared_body捕错留error/incomplete仍不能恢复丢失计数。外层finally解决漏行，不能保证实际字节；当前tests::AccessLogEveryRequestTests.test_handler_exception_is_logged_with_error令runtime.status在任何响应写入前抛错并断言体0，短请求体用EOF让read返回部分，均未覆盖已传部分再抛错。本轮AC-7不满足，交Review独立核实，不改日志/测试，不以字段增加免除原义务。 |

## 全局消耗门与继承限制

开工0消耗性+2零消耗（JET用户方向、LOOP接受）；交Review后仍0+2，Gate-echo按现行Overall。全局reviews机读blocks/releases搜索不按work过滤，实质ACQ R2-1已有同文件顺序release；完整SCOPE_GAP账本无未释放block。相关原始LOOP F3/F8、ACQ R1-4/K1K3-R1-1、FAST R1-2、FRAME R1-3与parked承接/暂停义务已读取；状态未改、不恢复旧项。B六题未签0、没有消耗性放行；不删除旧资产/清理义务/非verdict失败，不关闭研究里程碑。

## needs_user（六题原文保持）

以下逐字取自提案「N-1答复落实」needs_user（原题来源D2接受裁定）；本轮不提请执行、不由supervisor代选。N-1/N1-LOAD-RECONCILE已答，IR-13…17归接受已答，不列用户残留。

- (h) 阶段 B 读数入 `docs/unity-test-log.md` 按正式用户验证还是 workflow §4.3.2 诊断通道（推荐正式，理由：这是主线数字的首次产出，应可被引用）；
- (i) §5 阶段 B 信封签发（`R1@K1K2K3K4` 通过后）；推荐在 D2 预算修正、预检核清与代码复核通过后按确定的逐维度上限签发，理由：现申请值存在 AR1-8 的计量/前置缺口，当前不能签发执行。
- (j) 5060 备用臂启用条件（推荐：仅当板上收据不过资格线或 B0 可达性失败且 Jetson 侧当日不可修复时启用，启用即另签右列）；理由：保持用户已选 Jetson 主臂且不借备用臂扩大未签额度。
- (k) 阶段 B 执行机器：会话与快层在 Unity 主机（用户 Mac），板上服务由谁启动（推荐：用户本人经既有 SSH 启动，角色只给逐字命令；理由：Unity 主机 → Jetson 的 SSH/网络放行归用户本机设置）。
- N-2 B-pre 只读预检。推荐在设计范围确定且到达其前置门后，单签 §5.2 B-pre（只读SSH≤2、每次≤10min、ping≤10包，推理/写入/启动0）；理由：Unity主机链路与板环境尚未核，B-main依赖读数，预检本身不是板执行无限许可。
- N-3 STOP 缺省处置（随 B-main 信封）。推荐 AR1-8 修正资源口径后，逐码确认 §6.2（含S-RING记录NO_POSE并继续，非强保证帧覆盖）；理由：COORD-017禁止接受角色让未确认处置自行生效，不把描述性阈值变性能门。
