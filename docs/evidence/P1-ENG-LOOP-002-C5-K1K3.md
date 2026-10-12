# P1-ENG-LOOP-002 — C5@K1K3 接受侧只读核对

Acceptance / Codex，2026-10-07；Dispatch-Id `P1-ENG-LOOP-002-C5@K1K3-20261007T213122Z-e1ce`，requested.round=`C5@K1K3`。异源检查Claude Opus「身份修复K1K3」候选；不签独立复核，不运行测试/探针，不SSH/复制/加载模型/碰Jetson/Unity/runtime。consumed=none。

## 0. 输入、解析与核对结论

输入：同名提案AC-1…18及追加解释，重点「R4消费与诊断故障裁定」§2–5（AC-7修订5、AC-16修订1、AC-10修订2及五文件闭集）；实现 `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md` §0–9及附录X；同名复核R4原范围；账本DIAG:RESUME:1 A。最新逐AC表在提案固定「Contract conformance」。

候选采用实现证据§0的CAND/FIX/DISPATCH解析；本轮读取范围的全量基线明确为原R4终局通过指针，后续新通过轮不得改变这次核对的基线：

```bash
PASSED=$(sed -n '/^## R4@K1K2K3K4/,/^## /p' docs/reviews/P1-ENG-LOOP-002.md | sed -n 's/^passed_candidate: \([0-9a-f]\{40\}\)$/\1/p')
DISPATCH=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 身份修复K1K3 supervisor 派发登记')
FIX=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 身份修复K1K3 修复候选')
CAND=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 身份修复K1K3 收工')
git diff --name-only "$PASSED".."$CAND"
git diff "$PASSED".."$CAND"
git diff --name-only "$DISPATCH".."$FIX"
git diff --stat "$FIX".."$CAND"
```

实际先读文件清单，再完整读13文件diff（含新文件全部正文）、各证据指针和必要直接关联代码；候选之后至本轮开工只有账本/派发日志文档diff，无新实现。不以实现摘要替代代码或排除夹带文档。

**结论：可交新鲜独立Review R1@K1K3，未退回。** 相对R4通过候选的PLAY_GOVERNING增量确为language_serve、适配器测试与冻结操作单，非空，有开轮资格。新K1K3首次C（连续名C5）、退回0/1；原K1K2K3K4终局/2次返工不重开。Review自行裁稳定门/充分性与独立verdict。当前Overall REWORK_REQUIRED/ACTIVE，未签UNITY_NA/DONE或运行放行。

## 1. 完整diff逐文件核对

| 文件 | 核对与归属 |
|---|---|
| `tools/language_serve.py` | 实现闭集：仅新增parse_runtime_build及正则、read_runtime_build委托。读唯一行/明确build/ASCII 1–7位，非0/异常先拒；llama_preflight逐键比较仍先于_main_llama子进程加载。EXPECT_ASSET_KEYS、旗标/守账、adapter、部署清单未改。 |
| `tests/test_llama_server_adapter.py` | 实现闭集：假二进制仅增version_sleep_s；新2个parse及5个preflight具名方法。读_ServeFixture的_assets/_llama_arguments/_main_in_process/_start_serve/_fake_started，原样字节及实际main路径覆盖b0身份/错配拒启/非法分支/超时/OSError，旧StartupRefusalTests保留。未运行。 |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md` | 实现闭集：§0.3九键普通文件来源块，§2同块调用，§3第4步移到assets通道前，版本说明/审计键；其余R4范围携带。src_check按quote、闭集、唯一/完整、8192 B和加载后环境逐值核；失败有STOP/nonzero和操作员停步说明。 |
| `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md` | 实现闭集：附录B去进程替换命令，指向统一块；两格式版本解析与生产相同、缺变量STOP、runtime_version_line仅审计。直接关联附录A全文读过：九行shlex.quote+RESOLVE_OK，Q4/mmproj/server来源选择零diff，不伪造来源。 |
| `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` | 全量为531行新文件，完整读取。首版源于已签诊断步骤，身份修复仅gen/说明；budget=None组合/16源码同步/三诊断选项/人工预览/四类STOP不提升正式门。附录1gen同生产语义；其余未验证部分见§3，不能声称原R4已审过此页。 |
| `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md` | 实现自证文档，全文含附录X读过；五文件/170例摘要、12例红绿、加载与两gen原块探针/§9限制均具名；摘要是实现证据，本C不重跑、不独立认证输出。计数披露见PR-K4。 |
| `docs/reviews/P1-ENG-LOOP-002.md` | 复核R4新增段完整读过；PASS消费/冻结集三条闭合与机读通过指针相符，不是本次新候选PASS。不改复核文件。 |
| `docs/proposals/P1-ENG-LOOP-002-closed-loop-four-numbers.md` | 接受角色诊断授权落实、R4消费/三解释修订、表和当前指针。修复范围来源明确、engineering-v1已由D4接受生效；历史计数/故障归属与新停点分开。 |
| `docs/authorizations.md` | 完整diff为首次粗诊断授权14行；与诊断用途/3h/5Play/3启动含1故障重启相符。候选之后的续试A条另按本轮任务读取/落实，不回填原候选或改原话。 |
| `docs/evidence/supervisor-dispatch.jsonl` | 20条追加记录逐条读取，登记/核销/报告涉及旧返工、诊断授权/步骤、R4、故障裁定及身份修复派发；没有新运行授权，不把核销作独立verdict。 |
| `docs/current-status.md` | 门保留R4已消费PASS而当前REWORK_REQUIRED，新候选只IMPLEMENTED；C5/诊断暂停交接及Log属各角色文档。失效的“待实现/用户未答”在本轮按最新盘面就地更新。 |
| `docs/implementation-status.md` | 接受角色R4消费/计数/新故障边界，与原复核/提案相符；NOT_RUN和旧债保持，无诊断原件作为门证据。 |
| `docs/phase1-single-drone-design.md` | 接受同步当前范围与指针，两处更新不改安全/时间/指标/六键域、设备或预算；本轮同步C5/续试已答指针。 |

DISPATCH→FIX严格五文件，FIX→CAND仅本项实现证据/状态板。controller、Assets、config、llama_adapter、实际模型加载器、冻结件/指标/数据划分零diff；改动不越裁定§5。闭集外全量文档已逐项说明，未自行排除“协调变更”。

## 2. IR-K1…K6与稳定门主张

以下为既有修订的实现读法确认，不追加/改写AC义务（AC解释仍11、新AC0）：

| 读法 | 裁定与依据 |
|---|---|
| IR-K1 | 确认。startsWith version:候选行恰一条；同字节重复也拒，落实修订5“重复或冲突”。诊断/正式gen一致。 |
| IR-K2 | 确认该有限格式读法：三段ASCII数字、可选实现列出的预发布/元数据字符集、明确build/非空commit记号、整行截止；不是承诺一般SemVer语法规范或任意文本宽松解析。原样0.5.0-dev完整落在界内，不引入推断/缺省。 |
| IR-K3 | 确认。两格式均在解析时检查1–7位ASCII数字，保持前导零为字面标签；与bridge的fullmatch同域。当前夹具b0与b00错配拒启，007分支覆盖充分性留Review核。 |
| IR-K4 | 确认。§2也是同文件同来源前置义务，复用块不改变来源选择或新增动作/设备；不是闭集外扩修。 |
| IR-K5 | 确认。assets SSH前先核本shell来源变量，正是失败停在SSH/资产gen之前的既有义务；不改变SSH额度。 |
| IR-K6 | 确认。两gen原样version行仅JSON审计字段，读取期望只核五键、adapter六键域不改；raw/rc与来源指针保留。mini缺变量STOP是既有失败路径具名化，不新增身份类别。 |

四条件输入核对：①五文件冻结、IR已确认；②具名focused/红绿/原块探针相称，满足窄修替代的适用前提，N-1全套3/3用尽、未跑本候选全套；③本批零Unity、无本修复已知Unity失败可供复测；④候选/解析/状态交接与风险已记录、git核候选属于本轮所述提交链。Review仍独立核稳定门，可认为替代不足；若要全套，须先回用户新增验证信封，不能跑第4次。

## 3. 预复核关注项（待核实主张，未签finding或分级）

- **PR-K1：来源块调用的停步边界。** 正式操作单§2是`src_resolve && src_load; echo source_rc`后另有prep-read.sh生成；附录X成功门用`&& echo next_step_reached`，不等于整个§2复制粘贴时自动退出。§0.3/§2/§3第4步有逐步STOP说明。请定点核对既有操作员逐步执行语义是否兑现AC-10修订2；不要只重跑函数或bash -n后声称所有后续SSH自动不可达。
- **PR-K2：探针与实际来源/平台。** -idfix-k1k3.md §3.2/附录X用附录A替身，合法带空格/陈旧值/解析、生成、加载失败可定位；真实附录A和Air来源原件未验证，板Python3.12.3未运行。生产版本解析、mini/diag两个复制正则/退出码与错配拒启须核同一语义；不能把本机Python3.14/替身读数当板上通过。
- **PR-K3：诊断页全量新增边界。** diagnostic-smoke-ops.md §2的resolve→普通文件加载仍用tail/set+a且未核状态/清陈旧变量，附录1gen缺env会KeyError；本修复§5仅改gen/说明，OPS-SOURCE-1点名正式页，不意味着诊断页整链已通过。附录3/7的ss/pgrep及附录4启动清理均未实跑；复核完整diff与RED_LINE时区分诊断授权和正式安全检查，不借本C为该页全步骤签通过。
- **PR-K4：证据计数。** -idfix-k1k3.md §4将SemverVersionPreflightTests写“4例”，源码有5个test方法，§3.1的组合12=2+5+5一致。19个parse子例=5接受+14拒绝；本C按具名方法核，不以错误计数提升证据或改写实现者记录。
- **PR-K5：续试计时覆盖。** diagnostic-smoke-ops.md §0/1 elapsed/§7/附录0仍显示180 min原总量；本轮提案「DIAG续试授权落实」明确新增10410 s、旧390 s共账。后续交本人必须给覆盖口径，不能只转旧操作页；新目录计时不得重置180 min。C5完成不等于R1通过或已可续试。

## 4. 交接与未闭项

Review接手新鲜R1@K1K3，先核四条件，按§0解析完整候选/全量diff，独立核§1五文件、原生产preflight、两gen/来源加载闭环与RED_LINE；准许的重跑仅现行零模型focused+定点红绿/离线探针，不SSH/复制资产/板/Unity/runtime/全套。新候选与原R4终局不混轮；通过指针由Review写，Acceptance随后消费。

诊断A落实唯一详表在提案「DIAG续试授权落实」；其Consuming=yes行暂停至R1通过消费后才交本人。全局实质blocks/releases只ACQ R2-1，先block后release；账本无新增RELEASED_SCOPE_GAP行。本轮不写复核/账本，不解锁正式B-main/N-3/G1–G5。AC-14/15/18和AC-16板端NOT_RUN、Air正式原件/环境、现场HEAD/status/Unity日志与AC-18证据停点、OPEN债/偏差/UNKNOWN、ACQ暂停保持。当前needs_user=none，条件题实际触发后再转呈。
