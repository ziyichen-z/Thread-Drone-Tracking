# P1-ENG-LOOP-002 — C1@K1K2K3K4 核对依据（2026-10-06）

Owner：Acceptance / Codex；实现者为 Claude Opus，异源候选检查。
Dispatch-Id: P1-ENG-LOOP-002-C1-K1K2K3K4-20261006T235701Z-e772

**结论：首次退回 Implementation；不签独立复核 verdict。** 唯一逐条核对表在同名提案「Contract conformance（核对表）」；IR 先决答复与 AC-7 修订 1、AC-8 修订 1/2 在其「待裁定答复」。本文件记录真实读取范围与既有条款偏差，不改合同、代码、测试、复核文件或授权。

## 候选解析与核对边界

按 `docs/evidence/P1-ENG-LOOP-002-K1K2K3K4-handoff.md` 的运行时 git 解析式得到 BASE/CODE/CAND；与 supervisor 实现派发日志 finished.candidate、收工提交及本轮派发指定候选一致。完整读取 BASE..CAND 的文件清单后逐文件读完 diff，所有新增源/测试/操作单/证据均覆盖；两个 JSON 评分工件及资产 JSON 读取全部键值，非只取摘要。CODE..CAND 仅证据/状态，没有实现改动。当前开工 HEAD 中额外的 N1 用户代录和 C1 requested/started 登记另行读取，未混作实现候选。

必读事实源覆盖：状态板结构节/全部交接/本项及依赖门，研究 workflow、engineering-v1、acceptance 细则，D4 及适用历史裁定、AC-1…18/§3.5 完整算法/§4.1，正式设计相关章节、工程继承清单与全部范围外缺陷账本。沿 H-1…6 读取原 LOOP F3/F8、FAST 空窗、ACQ 原几何 cause/报告版本及暂停承接；全球复核 blocks/releases 来源覆盖，ACQ R2-1 已按 R3 的 release 配对，无未释放消耗性门阻断。当前非暂停轨道为 0 消耗性 + 2 零消耗，Gate-echo 一致。

核对方法：静态读代码与测试断言、读取原测试日志/历史同名失败日志、git/AST 源码及冻结件字节比较；**没有运行模型、实现测试、归档评分、板操作、Unity 或创建 scenario/session/run ID**。自检工具属于规定的文档/角色检查。

## 完整候选逐文件核对

共 **28 文件**，无自行排除的他角色/协调 diff。下列记录每文件与合同的关系；满足性以提案核对表为准。

| 文件 | 已读变更 / 核对落点 |
|---|---|
| config/p1-eng-loop-002-board-deploy.json | 部署路径闭集含清单自身；与 A2(e)/部署摘要及临时根隔离夹具对应。 |
| config/vlm-three-state.schema.json | 三态、unique bbox、ambiguous 候选、none；仅本项新 JSON 条件，不覆盖冻结 prompt/parse。 |
| controller/gated_publisher.py | 常驻专用显式 hold 收据开关、三 reason、写入/失败收据；旧开关缺省关闭。 |
| controller/language_bridge.py | 六身份字段条件校验与两 reason 追加；AC-6 的 null 键存在判断偏差。 |
| controller/language_loop.py | standoff 接线、会话模型缓存、重建/终止、挂起呈现、metadata 字节摘要、jetson 比较链、delay/intent CLI；AC-6 干净树偏差及 PR-2/3。 |
| controller/language_selector.py | bind_identity 六键验证、status_document 原始身份读数；旧 HTTP 有界单工代码仍是直接比较链依据。 |
| docs/current-status.md | IMPLEMENTED 候选和 Acceptance C1 交接；当时 N1 待用户的文字由本轮现行用户答复/状态更新覆盖，历史实现记录保留。 |
| docs/evidence/P1-ENG-LOOP-002-K1K2K3K4-handoff.md | 四条件自证、18 AC 指针、AC-8 具名测试、用量/包装源码、H-1…12、IR-1…12、未核限制及完整范围；待裁定由提案追加答复覆盖。 |
| docs/evidence/P1-ENG-LOOP-002-archive-dryrun.json | 全部输入/读数/41 对照；40 match、描述读数 1 mismatch；旧摘要/意图缺口如实保留，非正式验收。 |
| docs/evidence/P1-ENG-LOOP-002-assets-local.json | 冻结检测器/配置/清单字节及部署摘要资产来源，board NOT_RUN，不引用 JET 诊断身份。 |
| docs/evidence/P1-ENG-LOOP-002-four-numbers-fixture.json | 全部 17 样本/守恒/四数字值；time-to-center 只有计数，真值源汇总合并，不能替代原输出要求。 |
| docs/evidence/P1-ENG-LOOP-002-play-ops.md | 13 节、B/C 派生表、逐字命令/放行及 STOP 模板；C1-AC10 的省略命令与第一 passed_candidate 选择。当前不可执行门正确。 |
| docs/evidence/P1-ENG-LOOP-002-tests.log | 完整停点输出，2275 / 4F+9E / 19 skips；原始计数及墙钟；同名既有失败与 FRAME R7 来源核对，没有另跑基线/候选测试。 |
| docs/evidence/supervisor-dispatch.jsonl | 候选区间仅实现派发 requested/started 两行，角色/范围/零消耗信封与现状一致；这是调度事实记录，无新授权/规则或门决定，不略过。 |
| runtime/README.md | 新 model 字段、事件、收据 reason 文档；IR-12 在 §4.1 允许表，不是运行时文件写入。 |
| tests/test_eng_loop2_analyze.py | 完整 53 例，十二类/意图/冲突/绑定/存活/捕获/布局/H-2/归档夹具；中心时长输出、分源汇总、跨重建消歧与无真值时钟未被最终 JSON 断言证明。 |
| tests/test_language_bridge.py | 六键与原 reason 列表兼容断言；null 键存在路径遗漏。 |
| tests/test_language_latency.py | jetson 测量/收据/会话拒绝、失败行保留与旧六键全无兼容；dirty 注入不能代替真实 git 路径范围检查。 |
| tests/test_language_loop.py | 新参数 Harness 兼容及 body/cache/hold/delay/geometry 25 例，旧用例断言保持；本轮只读，没有重跑。 |
| tests/test_llama_server_adapter.py | 完整假 OpenAI 服务、原始失败映射、启动拒绝、部署字节/临时根前台/端口释放/正常 access 字节/残留隔离断言；非真实 b11381 验证。 |
| tests/test_loop2_freeze.py | 基线冻结件、围栏读取与 PLAY_GOVERNING 闭集断言，对应实际候选。 |
| tests/test_loop2_isolation.py | controller import 闭集、真值标记隔离、intent 仅允许收据与 CLI/request，实际导入对准。 |
| tools/eng_loop2/__init__.py | 本项工具包文档，未引入额外运行时导入。 |
| tools/eng_loop2/analyze_play.py | 全部 2118 行：输入索引/样本归属/十二漏斗/四数字/布局/H-2/投影/派生/归档/CLI；C1-AC8 与 IR-3 逐项读法边界。 |
| tools/eng_loop2/deploy_digest.py | 纯标准库规范 JSON/闭集摘要、共享 DECODE_CONFIG 与桌面身份，符合 IR-4 答复。 |
| tools/eng_loop2/llama_adapter.py | 原始图像/prompt/schema/解码参数、HTTP 请求/失败映射/三态解析/身份，schema 形状待真实板端。 |
| tools/language_latency.py | 新单 jetson 报告与收据、0/6/8、文件/HEAD/摘要/身份比较，旧双宿主保留；复用 code_git_state 的范围偏差。 |
| tools/language_serve.py | 全部 llama 分支、资产/version/启动与生命周期、HTTP handler 计量与临时图片清理；C1-AC7。 |

必要直接代码还包括：HttpAdapter 现行身份绑定/每回包检查，SingleFlightRuntime.submit/_run/result，既有 resident 指定/stop/pointer_bound/帧发布关联函数、冻结构造器与评分所复用的几何/窗口语义。没有据摘要跳过完整变更文件。

只读 git/AST 比对：LanguageWorker、CandidatesBackend、_validate_candidates_source、render_preview、_preview 的具名源码段与 BASE 逐字相等；candidates_preflight、scenario_tether 以及 AC-2 的六个冻结件字节相等。该方法不导入 controller/tools、不执行代码，不把未匹配符号的空集合当相等。

## 四条件与证据前置

- 范围/接口已有 D4 冻结，IR-1 不触发 schema 重冻；IR-2/4/9 的待裁定答复在 C1 前追加。实现侧自证能定位真实稳定候选；发现的忠实性偏差走 C1 首退，没有由接受角色给 REVIEW_BLOCKED。
- 全套原件的 13 项失败与未改测试/历史 FRAME R7 同名同类相符：dist_data 缺旧归档、tests 包遮蔽五模块、rate3 缺历史 manifest、两 CSRT 缺符号；新增失败 0 是实现者原结论，本轮只读核对其来源。用户 10-06「用户答复 N1-LOAD-RECONCILE：认可 CSRT 计数拆分，阶段 A 首次全套有效」已认可真实 cv2 尝试 2/实例 0 与替身 5 次拆分；本轮按有效消费，不重开、不补跑或加额。
- 阶段 A 没有 Unity 用例，不能拿「不适用本轮」签 UNITY_NA；AC-14/15/18 及 AC-16 板端仍 NOT_RUN。
- 范围、证据、风险和提交可解析；本轮覆盖旧「N1 待确认」的现行交接文字。返工需更新候选/自证和具体证据，保留首次有效全套及旧工件。

## 既有条款偏差

这些是接受侧待核实主张，未作独立 finding 分级/依据列。按已有 AC 返工；C1 核对不新增义务。

### C1-AC6 — 干净工作树与六键存在条件

依据：A2(d)、§3.2、AC-6；代码 `controller/language_loop.py::code_git_state` / `tools/language_latency.py::jetson_report_extra,build_single_host_receipt`。
code_git_state 的 git status 带 controller/tools/config 路径过滤，未提交 tests/文档时 dirty 可以为 false，与干净工作树合同及操作单 §1.2 不一致。现有测试通过注入 git_state 的布尔值检查 dirty 拒绝，只证明布尔拒绝，不证明生产路径取值完整。

另 `controller/language_bridge.py::validate_llama_identity` 用 value.get(key) is not None 定「出现」；例如旧身份块只追加 mmproj_sha256:null 时 present=[] 返回 {}，部分键出现且值不合类型被当作全无。全无旧块应继续通过，出现 null 不能等同未出现。按已有全有/全无及类型条件修复、补证；不改变旧合法六键全无报告。

### C1-AC7 — 访问日志不能覆盖逐请求字节

依据：AC-7、§5.2；代码 `tools/language_serve.py::LanguageRequestHandler._reply,_log_access,do_POST`。
日志在 _reply 成功 wfile.write 之后才写。IR-11 已指出 BaseHTTPRequestHandler.send_error（坏请求行、未支持方法）不入此路径；未知 POST 路径在读正文前回 404，request_body_bytes 仍 0；Content-Length 无法转 int 的错误也绕过日志。现有 access 正常 GET/POST 测试不覆盖这些路径。修复/证据须满足原「逐请求双向有效载荷」计量，错误/部分处理不能以假设极少省略；计量不保存正文，不新增磁盘/服务或访问授权。旧 HF 分支语义仍保留。

### C1-AC8 — 唯一评分算法的实际输出与归属

依据：§3.3、§3.5.1、§3.5.5/6、AC-8 与 IR 来源修订。

1. `Scorer._index_frames` 无真值行时将段 simulation_time_s 存入 self.time，sim() 被窗口/截止/时长使用。顶层 time_fallback 计数不能使四类数字的另一时钟来源合法；缺真值按原 NO_POSE/不可评估类据实处理，段读数只可诊断。
2. `Scorer._attribute_downstream` 的 pointer_bound 选择仅 i>anchor，取全局下一条，没有 e_s/常驻代/后续受理边界限定；同一 pointer 行可以被多个样本采用。缺自身指针时不得借下一样本指针；限定 s 的指针 epoch，其他行应计未归属/按原规则处理。E 的时间截止不能替代归属键本身。
3. `Scorer.time_to_center` 计算 from_f_p/from_h 时长，但 run() 仅累加 center 标签，number_three.time_to_center 只给分类计数，sample_record 也未输出时长。合成工件中的 CENTERED=1 没有任何中心耗时值，数字三的合同输出缺失。按既有起点/连续 5 帧/三种结局导出可复算时间，第二起点只并列，不改定义。
4. `Scorer.run` 将 red_car 和静止 intent 的结果汇总为同一 four_numbers 比率，无真值源分列；合成 17 样本工件也如此。§3.5.1 明文要求 Unity 真值与几何近似分列、不合并同口径。保留全部漏斗/冲突/意图守恒，并按原要求分列数字与原始分母，不能用总表替代。

现有 IR-2 消歧/IR-9 原因标签按答复核对；复核需要确认其生产归属与边界，见 PR-3/4。任何修复不动主指标、阈值、采样或 STOP。

### C1-AC10 — 操作单的逐字命令与通过候选选择

依据：§3.6 操作单闭集、AC-10。
`-play-ops.md` §9 将共同参数缩成 …，P2 的 confirm/reject、P3 的 confirm 与 stop 等未给完整命令/必要 token；section 存在不等于合同所需三剧本逐字命令已齐。补全已有命令，参数仍运行时解析，不新增采样/操作。

§1.1 用 grep -m1 取复核文件第一条 passed_candidate，多轮时取旧通过候选，与运行时解析「通过候选」放行目的不一致。应由复核文件当前适用通过轮解析，不能手抄 SHA；本项当前未复核，操作单尚不可执行，不能借这个问题要求实际 Play 试跑。

## 预复核关注项

- **PR-1（AC-7）**：`language_serve.SingleFlightRuntime` 暂存查询 JPEG，推理 finally 删除；access 错误/断连/退出及模型线程仍在途时的清理路径须复核，现有测试只证明已完成请求与前台退出的夹具。真实 b11381 旗标/response_format/health/version 仍属 B 假设，不用网络补证。
- **PR-2（AC-5）**：`LanguageSession.tick` 顺序 _poll_worker → _maybe_present_designate → _consume_request；Δ 到期同 tick 已有新 ask/stop 时，旧结果可能先呈现。现有挂起丢弃测试在到期前读新命令；请复核原「挂起中新受理命令丢弃」边界是否在此顺序成立，核对未修改 AC-5。
- **PR-3（AC-8 修订 2）**：`_designate_resident` 追平触发 stop 后 epoch 增加，再写 designation_unavailable；confirm 回执与去向是否仍能沿原 e_s 归属？现有 scorer 人工 unavailable 夹具不是该生产序列，不能仅凭原因字符串证明收口。
- **PR-4（AC-8 修订 1）**：现有 C6 夹具证明同代同编号冲突；还需核实两代重复编号不冲突且新代下游不串旧代，尤其 acquire_adopted/指针行的代边界。本项不关闭 F8/H-2 债，正式新归档摘要/布局链仍待 B。
- **PR-5（AC-8）**：`mislock/time_to_center/survival` 的 13 s 闭端点浮点处理、空窗排除与窗口外延伸、layout 排除后显式失败的独立计数，继续按原合同核实。当前误锁测试允许 65 或 66 帧；它不是新增容差授权。
- **PR-6（轮次/AC-18）**：本停点 C1 首退已用，修复后下一代码核对为 C2@K1K2K3K4，必须照交 Review，不能第二次退回。原 AC-18 把后续 B 证据核对预记为 C2；实际发生时应连续计数，不能重复使用代码 C2 名称。B 门到期前按角色规则处理这一轮次占位，不能以预记代替核对或消耗放行。本轮没有基于读码改写 AC-18。

## 交接与授权边界

唯一行动请求见状态板 Active handoffs；实现按提案核对表与本文件 C1-AC6/7/8/10 修复并整理同停点新候选。下一次 C 核对重读完整候选及差异、自证与原未决关注后照交新鲜上下文 Review R1；本轮没有独立复核、通过候选、Unity/板端结论或 DONE。

阶段 A 首次全套仍记 1/3，本候选归档回放 2/2；后续仅在用户 N-1 已签剩余额度内，不转用 JET/旧 LOOP/ACQ 余额。本轮 consumed=none。六题 (h)–(k)、N-2、N-3 原题/推荐/理由逐字保留于同名提案「N-1答复落实」needs_user，按原前置门转呈；不是现在索取答复或授权，未签0。ACQ 暂停、旧 OPEN 债/非 verdict/清理义务保持。

## 自检

收工凭据见本轮提交 Role-Check 尾注和接力报告；文档/角色检查命令为：
`python3 tools/check_role_writes.py --role acceptance`；
`python3 tools/check_docs.py`。
这两项是规定自检，不是实现测试或独立复核。
