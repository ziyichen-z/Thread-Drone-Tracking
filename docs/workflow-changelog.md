# 工作流规则修订史与来历

`AGENTS.md`、`docs/collaboration-workflow.md`、`docs/engineering-workflow.md`
只写**现行规则**。每条规则的来历——哪一批协调批次（`COORD-nnn`）提出、
哪一次用户授权生效、替换或删除了什么旧机制、为什么——统一记在本文。
本文不是规则：与规则文件冲突时以规则文件为准；授权原话与日期以
`docs/authorizations.md` 为准，本文只给指针。

## 0. 阅读与维护

- 想知道某条规则为什么存在：按 §2 的文件/章节索引找到对应条目。
- 想知道某个协调批次改了什么：看 §1 的批次索引。
- 2026-09-11 分离之前的规则文件原文（来历内嵌在正文里）存于
  `docs/archive/rules-before-provenance-split-2026-09-11/`，供对比审查；
  此后的修订以 git 历史为档案。
- 本文随规则文件由用户直接授权的协调批次同批维护：新增或修改规则时，在
  §2 对应章节加一行来历（批次、账本条目日期、替换了什么）。

## 1. 协调批次索引（时间序）

| 批次 | 用户授权（账本条目日期） | 内容 | 主要落点 |
|---|---|---|---|
| COORD-002 | 2026-07-30 | 按对话结论重构协作工作流：角色与模型解耦（构思/接受/实现/复核/辅助），Cursor 实现角色改为手动指令调起，补记协调批次收工约定，修订批次（审查发现 #1–#6） | workflow §1/§1.1、`docs/roles/`、§7 规则 7、`docs/authorizations.md` 账本起点（2026-07-30 起账本没有的授权视为未发生） |
| COORD-003 | 2026-07-31 | 单线执行纪律入工作流基础设施（一次只推进一条活跃交接） | AGENTS「执行轨道纪律」、workflow §7 规则 0（后被 COORD-007 R8 修订） |
| COORD-004 | 2026-07-31 | 状态板行数纪律改按单条约束，并修补压缩规则盲区 | 状态板体量（后被 COORD-007 R9 删除） |
| COORD-005 | 2026-08-04 | 开发期诊断验证通道与渲染管线人眼保真检查（P1-SCENE-006 F23 教训） | workflow §4.3.2、AGENTS「角色边界」用户条 |
| COORD-006 | 2026-08-09 | 协调批次修复 `tests/test_check_docs.py` 既有失败（工具债，不改规则） | `tests/test_check_*.py` |
| COORD-007 | 2026-08-12（R1–R8 + R9）；2026-08-12（修复复核轮 2 三条漏洞 F3/F4/F5）；2026-08-13（§4.4 条件 2 复算与 N12 显式裁定） | 流程开销削减：把散文门改成机器门。R1 复核开轮资格机械化；R2 删停点条件 5；R3 finding 由回归测试关闭、取消纯闭环复核轮；R4 finding 分级、CLASS_3 不阻断；R5 infra 自修复例外 + 修两处漂移；R6 提案退修上限；R7 禁止手写可派生标识 + 机读候选指针；R8 单线执行改为约束消耗性资源并换成 Gate-echo 触发器；R9 四个滚动节合并为 `## Log`、删除按月归档。R10/R11/R12 未授权未开工 | AGENTS 全文、workflow §4.2/§4.3.1/§4.4/§6/§7、`tools/check_docs.py`、`tools/check_role_writes.py` |
| COORD-008 | 2026-09-02（S1–S7 全部采纳，不经接受轮） | 流程减法：S1 停点自证直接交复核；S2 复核结论直通实现角色；S3 接受记录不再逐轮追加到提案；S4 授权改信封；S5 真数据试跑先于合同冻结；S6 CLASS_3 闭集补一项；S7 仓库外同步（`~/.codex/prompts/codex.md`） | workflow §4.1/§4.2/§4.3.1/§4.4/§4.6/§6、AGENTS、三份角色细则、命令文件、模板、账本格式 |
| COORD-009 | 2026-09-03（T1–T10）；同日「修订」：接受角色核对轮定为实现后必经的异源候选检查；同日「修订 B」：接受角色的复判与 release 落在自己的文件、机检配对改顺序；同日闭集定义补全 | 复核收敛：T1 核对轮取代无边界拒收权；T2 BC 表结构、自检与 `CLARIFY`/`NEW_OBLIGATION` 标签；T3 复核 (a)(d) 范围判据与依据列；T4 复核 (b) 增量轮、双基线、`上轮漏检` 与消耗性门机检；T5 复核 (c) 同停点第 2 次 `REWORK_REQUIRED` 后冻结未闭集、轮 3 终局；T6 归因机械派生 + 「范围外已知缺陷」账本；T7 三个计数器分开 + 轮次命名；T8 测试输出纪律；T9 `P1-VLM-DATA-002` 处置；T10 仓库外同步 | workflow §1/§2/§4.2/§4.3/§4.3.1/§4.3.3/§4.4/§4.6/§6、AGENTS、`CLAUDE.md`、四份角色细则、`tools/check_docs.py` 消耗性门机检 |
| COORD-010 | 2026-09-07（批准 §10 A+B+C，含两项点名澄清：Jetson 探测前移但独立立项与额度；多角色分工与并发纪律维持现状）；2026-09-08（用户按 §8 T1–T7 验收状态迁移批） | 工程换轨与旧数据采集收口：新增工程轨道 `Workflow: engineering-v1`，`docs/engineering-workflow.md` 只替换 §6 机制表 11 项；移除状态板全文 500 行硬阻断；§3 旧工作项终止/延期处置。规则批经 `R1@batch1` REWORK_REQUIRED → `R2@batch1` PASS_WITH_NOTES（`docs/reviews/COORD-010.md`） | AGENTS「工作流轨道路由」、workflow「适用轨道」及各节工程轨道段、`docs/engineering-workflow.md`、`tools/check_docs.py`（删 500 行检查）、`tools/check_role_writes.py`（INFRA_PATTERNS 加入 engineering-workflow） |
| （无批次号） | 2026-09-08 | 用户直接授权四项：轻量按需读取机制（workflow §6.1）；chore 压缩规则修复问题 1/3/4/5；chore Log 条目彻底删除标准与节奏；chore 新增状态板 500 行有效维护职责 | workflow §6/§6.1、AGENTS「共享状态更新」、`docs/roles/chore.md` |
| COORD-011 | 2026-09-11 | 规则正文与来历分离：三份规则文件剥离来历注释到本文，章节编号与标题不变，意图零语义变化；旧版整份存档供对比审查 | 本文、`docs/archive/rules-before-provenance-split-2026-09-11/` |
| COORD-012 | 2026-09-20（账本「用户签字授权 U1/U2/U3 落地（一个协调批次）」；第一批 N1/N2 属 chore 2026-09-08 常设授权，无需新授权） | 会话读取成本削减第二批。U1：chore 旧 Log 不可压判据由「本批次 + 7 天内」改为三项（本批次新写 / 关联 work item 的 Gate board Overall 非终态 / 无关联 ID 且 7 天内），可压池 ≤300 行由 `check_docs.py` 机械强制（取代 D1 对 N6(a) 的「早于当天−7 天」口径；提案原「Log 全文 ≤300 行」）；U2：彻底删除节奏由「里程碑关闭时」改为「可压池压缩后仍超阈值时」，三条删除标准逐字不改；U3（N7）：新增单向沉淀池 `docs/status-history.md`（移动而非复制、不是事实源、不进必读、不被扫描、不得引为义务/证据来源），修改 AGENTS「不为此新增归档系统」「删除的内容以 git 历史为档案」两句并确认「单一 `## Log` 节」对其不适用，chore 写入白名单同步。**同日用户裁定（账本「用户裁定：无关联条目直接入可压池…」）**：U1 判据 (iii) 取消（无关联 work ID 的条目直接入池，工具去日期解析）；Gate board 新增 `Lifecycle` 列（`ACTIVE`/`PAUSED`/`ENDED`）逐行明示暂停/终止，工具 (ii) 改读该列；写入 history 须先经用户同意，以 work item 为单位一次同意。N3/N4 未授权；N5/N6(b) 接受角色 D1 不采 | AGENTS「共享状态更新」、`docs/roles/chore.md`、`docs/status-history.md`、`tools/check_docs.py`（第 10 项检查）、`tools/check_role_writes.py`（chore 白名单）；同日第三批（账本「授权把 workflow §6/§6.1 与 engineering-workflow §10 的三处同句改成与 AGENTS.md 一致」）把 workflow §6 状态板体量段、§6.1 与 `docs/engineering-workflow.md` §10 的「不新增归档系统 / 删除内容以 git 历史为档案」改成同样措辞，并在 §6 补可压池上限与 `Lifecycle` 列；第四批（账本「授权 N3」）：§7 规则 1 与 AGENTS「修改前重新读取」的全文重读口径改为按 §6.1 执行 |
| COORD-013 | 2026-09-21（账本「COORD-013 — 用户直接授权落地状态板接力成本批次」；不经接受轮） | 状态板只装当前工作、交接一件事只写一处：非活跃项移入 `docs/parked-status.md`（事实源，开工不读），`ENDED` 行不留板、`PAUSED` 行与暂停交接行一行索引；七项字节上限机检（结构节 ≤ 30000 B 等）；O4（COORD-008/009/010 改 ENDED）未执行 | AGENTS「共享状态更新」、workflow §6/§6.1、engineering-workflow §10、`docs/roles/chore.md`、`docs/roles/acceptance.md`、`tools/check_docs.py` 第 11 项、`tools/check_role_writes.py`（接受角色可写 parked） |
| COORD-014 | 2026-09-22（账本「COORD-014 — 用户直接授权修正停点自证的写入位置与 chore 规则过时项」；不经接受轮） | 停点自证改写入 `docs/evidence/` 下该停点证据文件的具名小节、交接行只放指针（解除与活跃交接行 ≤ 800 B 的冲突）；chore 命令以 `model: sonnet` 固定调用当轮模型；chore 触发条件改为 `check_docs.py` 可压池/结构节超限，删去 COORD-013 后失效的「压缩终态 Gate board 行」；白名单 `docs/archive/*` 与 chore 的 parked 写权限未改 | AGENTS「复核强制停点」「共享状态更新」、workflow §4.3.1/§6、engineering-workflow §10、`docs/roles/implementation.md`、`docs/roles/chore.md`、`.claude/commands/implement.md`、`.claude/commands/chore.md`、`.cursor/commands/coding.md` |
| COORD-015 | 2026-09-25（账本「用户授权协调落地：§9.2/§12 落地批次（U1–U9 按缺省；不含 CLI 下载、信封与首次启用）」；设计经 D6 接受 + 接受后修订 1） | supervisor 角色落地：S0 接力调度（全局同一时刻至多 1 个写仓库角色、派发登记/核销/对账、`supervisor-dispatch.jsonl`）；S1 提交后事实核查（F1–F10，非权威）；S2/S3 有界代拍与两类信封块（`supervisor_decision_envelope`/`supervisor_subdelegation`，只能用户逐字签发；代拍/撤销/否决条目带 `at:` 机读行）；T 协调批次 5 天窗口节流；P 池重分配（实现 Cursor→Claude Opus `/implement` 主入口、Cursor 留为 U8 遗留手动入口、接受可被 `codex exec` 无人值守拉起）；派发提交尾注 `Dispatch-Id`/`Role-Check`；退修上限 D1 句改「信封在效且残留数严格递减（`open_items:` 机读行，自首次退修起每轮必填）时交 supervisor 仅代选 (a)」。U1=D/U2=B/U9=B：D2a/D2b/D3/F7 相关原句不变 | AGENTS「角色边界」「共享状态更新」、CLAUDE.md、workflow §1/§1.1/§4.2/§4.3.3/§6/§7、engineering §3/§8、新增 `docs/roles/supervisor.md` 与其余五份角色细则（报告段与尾注、acceptance 加 `open_items:` 义务）、`.claude/commands/`（新增 supervisor.md；implement/accept/codex 池同步）、`.cursor/` 遗留标注、`docs/proposals/README.md`、账本文件头、`tools/check_role_writes.py`、新增 `tools/check_ledger.py` 与 `tools/make_supervisor_drill.py`、`tools/githooks/pre-commit` |
| COORD-015（修订 2/3 对应句同步） | 2026-09-25（账本「用户指示修订 2」「用户指示修订 3」「提案记录移至新文件」；接受角色「接受后修订 2/3 审核」确认，BC-13） | supervisor 运行地去池/CLI/模型绑定：AGENTS「角色边界」supervisor 条「Opus 池」改「本机 CLI 会话（CLI 与模型由用户当轮选择、可更换，不写死）」；workflow §1.1 池表 supervisor 移出 Opus 池行（删「与常驻调度」）、另起「不绑定池」行；`docs/roles/supervisor.md` 开头运行地句改写（不写死 CLI/模型名）、模型升降改交用户决定当轮选择、设计依据指针改指 `COORD-015-supervisor-role-record.md`（D6 + 接受后修订 1–3，BC-1…13）；`.claude/commands/supervisor.md` 删 frontmatter `model: opus`、description 与正文去 Opus 绑定。历史行不回改；其余角色池与 U1–U9 其余选择不变 | AGENTS「角色边界」、workflow §1.1、`docs/roles/supervisor.md`、`.claude/commands/supervisor.md` |
| COORD-015（修订 4 恢复） | 2026-09-25（账本「用户指示修订 4」：撤销修订 2/3、直接恢复 D6 原文，不重写） | 修订 2/3 的对应句同步整体回退：AGENTS supervisor 条恢复「Opus 池」；workflow §1.1 池表删「不绑定池」行、恢复 Opus 行原句；`docs/roles/supervisor.md` 恢复「运行池 Opus + frontmatter 固定 + A9 升 Fable」原句（设计依据指针同步指到改名后的提案记录，标注修订 2/3 已撤销）；`.claude/commands/supervisor.md` 恢复 `model: opus` 与 Opus 绑定。历史行不回改 | AGENTS「角色边界」、workflow §1.1、`docs/roles/supervisor.md`、`.claude/commands/supervisor.md` |
| COORD-015（接受提供方回退） | 2026-09-26（账本「全局 — 用户授权协调批次：把接受角色提供方回退规则写入 supervisor 细则与入口」；规则原文见同日「全局 — 用户指示：接受角色缺省 ChatGPT 登录、额度耗尽回退 Kimi…」） | `docs/roles/supervisor.md` 新增「接受派发的提供方与回退」：缺省 gpt-6-sol，额度 ≥ 95% 或额度错误回退 Kimi k3-256k；`.claude/commands/supervisor.md` 第 2 步加指向句。 |
| COORD-016 | 2026-09-26（账本「COORD-016 — 用户授权零消耗协调落地批次：按提案 §3–4 与 BC-1…6 执行；U1=A…U3=A…U4=B…」；设计经 D3 接受，BC-1…6） | 代拍放宽：D1 判据「严格递减」改「非递增」并加每提案累计上限 3（计数含后被否决/撤销者）；新增 D7（预注册合同数值按接受角色推荐，限 `ACCEPTED` 后 BC/AC 行条款格内 `d7_range:` 正向资格 + 非 D 轮裁定节 `d7_recommend:`，同源已提交快照、精确十进制比较；须新签含 `D7` 的决策信封），「永不代拍」闭集加唯一例外句；启用 D2b（须信封显式列入；批准后按开轮资格分路：有资格开轮 4，无资格走回归通道在原复核文件「回归核实」小节写终局，任一未闭回用户），九处「轮 3 终局」句同步；COORD-015 R2-1 夹具债修复（`inject_open_items` 按 `### D<n>` 节插入，维持 `OPEN` 至独立复核核实）；新增具名路由检查 `tools/check_route_text.py`。U4=B：D3 不动 | `docs/roles/supervisor.md`（代拍类表 D1/D2b/D7、D7 预注册判据、永不代拍例外句、信封块注释、必填机读字段与失败关闭）、workflow §4.4、AGENTS「共享状态更新」「复核强制停点」、`docs/roles/{review,acceptance}.md`、`.claude/commands/{accept,review}.md`、账本文件头、`tools/check_ledger.py`、`tools/make_supervisor_drill.py`、新增 `tools/check_route_text.py` 与 `docs/evidence/COORD-016-route-spec.json` |
| COORD-016（补充同步） | 2026-09-26（账本「用户授权补充同步协调批次」） | workflow §4.2、`docs/roles/acceptance.md`、`docs/roles/ideation.md`、`.claude/commands/accept.md` 的 D1 句改为非递增+每提案上限 3；`.claude/commands/supervisor.md` D2b/D7 须信封显式列入；路由规格加 S01–S07/S00 与 closure 标记。 |
| COORD-016（补充同步第 2 批） | 2026-09-27（账本「用户授权补充同步第 2 批」） | `docs/engineering-workflow.md` §3 与 `docs/proposals/README.md` 的 D1 句改为非递增+每提案上限 3；路由规格加 S08/S09 与旧句归零；仓库外 `~/.codex/prompts/codex.md` 同步 D1 句与 D7 两句。 |
| supervisor 启动形式（COORD-015 续） | 2026-09-27（账本「用户授权协调批次：明确 supervisor 拉起 codex exec 的命令形式与每台机器前提」） | supervisor 细则新增「启动调用的形式与每台机器的前提」：单条以 `codex exec` 开头的字面命令、登记/启动/取证分三次调用、被拒即停不换写法、每机允许规则三条与 `KIMI_API_KEY` 前提（`~/.codex/.env` 或 `~/.zshenv`）；`/supervisor` 入口第 1/2 步同步；续批（账本同日「用户授权续批：接受角色 codex exec 显式推理强度」）：启动模板显式 `-c model_reasoning_effort` （openai `high`、Kimi `medium`） | `docs/roles/supervisor.md`、`.claude/commands/supervisor.md`、`docs/evidence/COORD-015-codex-launch-form.md` |
| 工程轨道构思改 Opus（COORD-015 修订 5） | 2026-09-28（账本「全局 — 用户指示：工程轨道构思改用 Opus 池，复核不变」；不经接受轮） | 工程轨道构思由 Fable 池改为 Opus 池，研究轨道构思、复核、DR-* 不变 | workflow §1.1、AGENTS「角色边界」构思条、`docs/roles/ideation.md`、`docs/roles/supervisor.md` 边界表、`/fable` 入口、COORD-015 提案 |
| supervisor 会话卫生（COORD-015 修订 6） | 2026-09-28（账本「全局 — 用户指示：supervisor 会话卫生阈值改 25/30 万 token、按节读取细则」；不经接受轮） | 删「每处理 20 次交接」；15 万 token 改为 25 万（当前派发核销与核查完成时重开）/30 万（即停）；细则按节读取 | `docs/roles/supervisor.md`、`/supervisor` 入口第 1/5 步、COORD-015 提案 §3.10 与回应索引 |
| 接受角色模型换 gpt-6.1-sol（COORD-015 续） | 2026-10-01（账本「全局 — 用户指示：接受角色模型切换为 gpt-6.1-sol；本机探测未通过，待升级 codex CLI 后复测」，含同日后续确认；不经接受轮） | supervisor 细则「接受派发的提供方与回退」「启动调用的形式与每台机器的前提」三处 `-m "gpt-6-sol"` 改为 `-m "gpt-6.1-sol"`，推理强度 `high`、Kimi 回退与其余参数不变；前提为 codex-cli ≥ 0.159（0.157.0 对该型号报 400），探测见 `docs/evidence/COORD-015-codex-launch-form.md`「gpt-6.1-sol 切换」 | `docs/roles/supervisor.md` |
| 接受角色 Kimi 回退推理强度改 high（COORD-015 续） | 2026-10-02（账本「全局 — 用户指示：接受角色 Kimi 回退推理强度改 high」；不经接受轮） | supervisor 细则「接受派发的提供方与回退」「启动调用的形式与每台机器的前提」Kimi 路径 `model_reasoning_effort` 由 `medium` 改为 `high`（两条路径均 `high`），提供方切换条件与其余参数不变；本机真实端点探测见 `docs/evidence/COORD-015-codex-launch-form.md`「推理强度事实」2026-10-02 补测 | `docs/roles/supervisor.md` |
| Codex 四角色入口迁移（无批次号） | 2026-10-01（账本「全局 — 用户指示：复制 Claude 的 supervisor、implement、review、chore 到 Codex」） | 从 Claude 命令迁移四个项目技能，适配 Codex 元数据、用户消息参数和会话说明；职责、停点、独立性、全局模型池与派发映射沿用现行规则 | `.agents/skills/{supervisor,implement,review,chore}/` |
| Codex 构思入口迁移（无批次号续批） | 2026-10-01（账本「全局 — 用户指示：复制 Claude 构思角色到 Codex」） | 沿用四角色迁移方式，增加构思技能；提案权限、轨道路由、模型池与派发映射沿用现行规则 | `.agents/skills/fable/` |
| COORD-017 | 2026-10-04（账本「全局 — 用户授权协调批次：按 JET-001 阶段 A 复盘修改七处流程文件」与同日「全局 — 用户确认 COORD-017 草案并指示现在落地」；不经接受轮） | P1-ENG-JET-001 阶段 A 复盘的流程修订：信封默认含每候选一次停点全套的本机模型加载额度；只改具名文件的窄修以 focused 加修前红/修后绿代替全套；候选含不可重跑的消耗步骤时先过停点再消耗；端侧环境事实先只读预检、未核实假设所依赖的维度不申请签发；接受角色核对通过线出处、描述性读数线、合同档判定与 `STOP` 缺省处置；被 supervisor 拉起的角色在交接行逐字写登记轮次；实现角色下载额度纪律。原列第七项（提案字节上限）与「答复只能追加、原文不覆盖不删除」冲突，未落地。 | `docs/proposals/README.md` 工程模板、`docs/engineering-workflow.md` §4/§6/§9、`docs/roles/` 六个细则、`.claude/commands/` 五个入口与 `.agents/skills/` 四个入口；取证见 `docs/evidence/COORD-017-stage-a-retro-process-fixes.md` |
| COORD-019 | 2026-10-10（账本「全局 — 用户直接授权协调批次 COORD-019：双路并发…」；不经构思/接受轮，supervisor 会话一轮落地） | 双路并发：Active handoffs 加 `Lane` 列（闭集 `fast`/`vlm`），执行轨道上限由全局 1 消耗性 + 2 零消耗改为每路 1 消耗性 + 2 零消耗；归路由写行角色判断、接受角色可更正；Gate-echo、`PAUSED_*`、消耗性定义、共享槽位互斥与信封来源不变；不拆第二个状态板文件；同批开 VLM 诊断道独立板 `docs/evidence/COORD-VLM-DIAG-2026-10-10/status.md` | AGENTS「工作流轨道路由」「执行轨道纪律」、workflow §7 规则 0、engineering §8、`docs/roles/{acceptance,implementation}.md`、`docs/proposals/README.md`、`tools/check_docs.py`、`tests/test_check_docs.py`、状态板交接表、`docs/evidence/COORD-019-dual-lane-batch-2026-10-10.md` |
| COORD-019（补充同步） | 2026-10-10（账本「全局 — 用户选 (a)：单写者规则改按路…」；不经接受轮，同窗口补充） | 单写者改按路：supervisor 细则「唯一执行」「派发登记」（`requested.lane`）「启动前登记与全局去重 (i)」「重启后对账」「并发/消耗纪律与会话卫生」改为每路至多 1 个写仓库角色、派发去重与重启对账只看本路、并行期间共享文件只追加或锚点增量；同步 AGENTS 角色边界 supervisor 条、workflow §1.1 池表、engineering §8、两份 supervisor 入口 | `docs/roles/supervisor.md`、AGENTS「角色边界」、workflow §1.1、engineering §8、`.claude/commands/supervisor.md`、`.agents/skills/supervisor/SKILL.md` |

## 2. 按文件与章节的来历

### 2.1 `AGENTS.md`

**必读顺序**
- 第 1/5 条的「按 workflow §6.1 先读结构节、历史按需展开」「按需读取不减免必须完整核对的范围」：2026-09-08 用户授权「轻量按需读取机制」。

**工作流轨道路由**
- 整节：COORD-010 批 1（用户授权 2026-09-07）新增。「只替换 §6 机制表 11 项」「未提及不等于豁免」「既有 work ID 不得追加该行」「fail-closed」均出自该批规则候选及其复核轮 R1/R2@batch1。
- 「COORD-010 §3 点名的旧工作项只执行具名的终止/延期动作；历史实现与复核不回溯」：COORD-010 §3/§7，用户 2026-09-07 授权。
- 「共享槽位互斥使用约定按现状保留，不另立条文」：COORD-010 §6「资源与并发」行；用户 2026-09-07 点名「多角色分工与并发纪律维持现状」，该批因此不新写槽位条文。
- 「信封只能由用户授权给出、缺项视为 0、越界回用户」：COORD-008 S4（2026-09-02）。
- 「可派生标识禁手写」：COORD-007 R7；「复核机读行与消耗性门机检」：COORD-009 T4。

**执行轨道纪律**
- 「1 条消耗性 + 2 条零消耗」：COORD-003（用户授权 2026-07-31）确立单线执行；COORD-007 R8（用户授权 2026-08-12）改为按消耗性资源分类的 1+2 上限。
- 「分两路（`Lane` 列，闭集 `fast`/`vlm`），每路 1 条消耗性 + 2 条零消耗」：COORD-019（用户直接授权 2026-10-10，不经接受轮）。来由：用户要快层修复与 VLM 调优两条线并行推进；两线的执行机与代码目录基本不重叠（Air/Unity 对 Mac mini/5060/Jetson，`controller/` 对 `tools/eng_sft*`），全局 1+2 上限只剩对用户注意力的保护；改为按路计数，归路判断交写行角色，接受角色可更正。曾考虑真分两个状态板文件，因检查器路径、六个角色白名单与跨文件 Gate-echo 都要改而未采纳。
- 「强制核对不挂在暂停动作上，而由 Gate-echo 承担」：COORD-007 R8 的换触发器理由——COORD-003 记录的三起触发事故全部是零消耗轨道的交接文字失效，暂停动作本身拦不住。
- 「判据 = token 表成员资格」：COORD-007 接受轮 5 N12 裁定（用户 2026-08-13 指令完成 §4.4 条件 2 复算与 N12 显式裁定）；此前曾用 work ID 文法作前置，漏掉多段 AREA 与里程碑行。
- 「畸形行 fail-closed」：COORD-007 复核轮 2 F5，用户 2026-08-12 授权修复。

**角色边界**
- 角色与模型解耦、「历史记录中的 Fable/Codex/Sonnet 不回改」：COORD-002（2026-07-30）。
- supervisor 条「每路同一时刻至多 1 个写仓库角色」：COORD-019 补充同步（用户 2026-10-10 选 (a)）；替换 COORD-015 的「全局同一时刻至多 1 个」。
- 接受角色「核对轮 `C<n>@<停点>` 必经、每停点至多退回 1 次、不跑测试/不改实现/不加 BC 行/不签独立复核」：COORD-009 T1，经用户 2026-09-03「修订」定为实现后必经的异源候选检查。
- 用户条「诊断性 Play/目检（非证据、不耗 ID）」「新渲染管线冻结前须有人眼保真检查」：COORD-005（2026-08-04）。
- M2/M5/投稿前新鲜上下文设计审查：COORD-002 起的 §4.7 门，未改。
- 构思条「研究轨道 Fable 池、工程轨道 Opus 池」：2026-09-28 用户直接指示（账本「全局 — 用户指示：工程轨道构思改用 Opus 池，复核不变」），替换「Fable 池最强档」。

**共享状态更新**
- 单一 `## Log` 节、不设滚动节、不做按月归档、`docs/archive/` 只读：COORD-007 R9（用户授权 2026-08-12）删除了原四个滚动日志节、COORD-004 的单条行数上限与 `rotate_docs.py` 按月归档机械；既有归档文件保留只读。2026-09-11 COORD-011 经用户授权在 `docs/archive/` 下新增一份规则旧版快照目录，属一次性对比审查用途，不恢复状态板归档。
- 三条分节上限、全文不设行数硬顶：分节上限沿自 COORD-007 R8/R9 后的 `check_docs.py`；全文 500 行硬阻断由 COORD-010 §6「状态板体量」删除（用户批准 2026-09-07），当时要求文档与 `tools/check_docs.py` 同批修改，规则正文保留为一般要求「上限数值修改须与工具同批提交」。
- 「`## Log` 可压池 ≤ 300 行」与三项不可压判据：COORD-012 U1（用户签字授权 2026-09-20）。提案 N6(a) 原为「Log 全文 ≤300 行」，接受角色 D1 因 7 天保护窗（当时 59 条/519 行）不可压、硬门会卡死当日全部提交而改为「早于当天−7 天的条目 ≤300 行」；用户第二轮意见指出该判据保护错了对象（窗内 41 条/404 行全属已 `DONE` 的 `P1-ENG-SFT-002`），D2 采「关联 work item 已终态」判据并以 7 天兜底无关联 ID 的条目。数值与工具同批落地，修复前必失败测试见 `docs/evidence/COORD-012-tests.log`。落地当日实测可压池 746 行，按裁定顺序由 chore 随后执行 N2 压缩，落地提交本身以 `--no-verify` 越过钩子并在提交信息与状态板如实披露。**同日第二批（用户裁定，账本同日「用户裁定：无关联条目直接入可压池、Gate board 加终止/暂停明确标识、写入 history 须先经用户同意」）**：(iii) 取消——用户原话「我觉得无关联也直接压缩就可以了」，协调批次会话指出 (iii) 是 check_docs 中唯一随日历变化的判据且只保护 6 条 54 行；终止与否不再按 Overall token 前缀推断，改读新增的 Gate board `Lifecycle` 列——用户原话「结束的项目有一个明确的标识，表头或者其他地方标明哪些项目只是暂停，哪些项目已经终止」；初次填值 `ENDED` = U1 token 集 + `P1-M2-RATE-002`（TERMINATED）+ `P1-SCENE-001`（SUPERSEDED），其余保守 `PAUSED`/`ACTIVE`。
- 「写入 `docs/status-history.md` 须先经用户同意，以 work item 为单位一次同意、不逐条」：同一用户裁定——原话「写进历史的要先经过我同意」「不是逐条，是一个任务的所有系列状态共用一次同意」。规则文本落在 AGENTS「共享状态更新」、`docs/roles/chore.md` 与该文件抬头，无工具机检（凭据 = 账本同意条目 + chore 提交引用）。
- 「压缩/删除移出的叙述整段移入 `docs/status-history.md`、移动而非复制、git 仍是权威档案、单一 `## Log` 节约束对其不适用、除该沉淀池外不新增归档系统」：COORD-012 U3（用户签字授权 2026-09-20；用户原话「current里面删除的东西可以写一个history……平常不去读就可以」）。接受角色 D2 裁定其与 COORD-007 R9 的区分成立：R9 禁的是多份各自维护当前状态的滚动节互漂，沉淀池不维护当前状态、不含门值、不被机检、不进必读。
- 「体量治理靠分节上限与内容归属判断，不为总行数反复压缩提交」：COORD-010 §6。
- chore 常设内容维护、旧 Log 删除条件、「全文行数仅作排查提示」：用户 2026-09-08 直接授权（含同日问题 1/3/4/5 修订、Log 彻底删除标准与节奏、500 行有效维护职责），细则在 `docs/roles/chore.md`。其中「不压缩本批次新条目与 7 天内条目」红线由 COORD-012 U1 改为三项不可压判据，「里程碑关闭时才做彻底删除轮」由 COORD-012 U2 改为「可压池压缩后仍超阈值时」，三条删除标准逐字不改；移出叙述改为移入 `docs/status-history.md`（U3）——均为用户签字授权 2026-09-20。
- chore 常设维护一句删去「终态 Gate board 摘要」：COORD-014（2026-09-22）；COORD-013 后终态行由关闭方移入 parked，状态板不再有此类行。
- 「可派生标识禁手写、`passed_candidate` 机读行、存量不回改」：COORD-007 R7。
- 「`round_candidate`、`blocks_consuming_gate`/`releases_consuming_gate`、`PAUSED_CONSUMING_GATE_BLOCKED_*`、账本 `RELEASED_SCOPE_GAP` 视同 release、复判写提案」：COORD-009 T4；账本 release 路径与「接受角色不写复核文件」出自 2026-09-03「修订 B」。
- 「轮次命名 D/C/R 分开计数」：COORD-009 T7；「退修上限只数 D 轮」：COORD-007 R6 + COORD-009 T7。
- 「测试输出纪律」：COORD-009 T8。
- 「修改前按 §6.1 重读待改章节、开工读取同按 §6.1、不要求全文重读」：COORD-012 N3（接受角色 D1 采；用户 2026-09-20 授权「授权N3」，账本同日条目）。此前「修改前重新读取」为全文口径，与 §6.1 重复且无独立拦截记录。
- 「状态板只装当前工作，一件事只写一处」与五项字节上限、`ENDED` 行移入 `docs/parked-status.md`、`PAUSED` 行一行索引、「除 status-history 与 parked 外不新增归档系统或状态文件」：COORD-013（用户直接授权 2026-09-21）。替换了「除 `docs/status-history.md` 这一个单向沉淀池外不为此新增归档系统」一句的单文件口径。
- 「收工前 `check_role_writes.py` 只核对未提交改动；已提交批次不做机械审计」：COORD-007 R2 移除了原 §4.3.1 条件 5 的 `--base` 归因审计（记录在案 50 次运行 0 真阳性、1 假阴性）。
- 「工作流基础设施只读、唯一例外 `--infra-fix`」：COORD-007 R5（通配 `tools/check_*.py` 修复了只点名三个字面工具的假阴性）；「复核角色除外」出自 COORD-007 复核轮 2 F3，用户 2026-08-12 授权修复（红线 A 五路径绝对禁令优先）。
- 「协调批次不运行角色写入检查，合规凭据是账本条目」：COORD-002 补记的协调批次收工约定（2026-07-30）。
- 授权账本与「2026-07-30 起账本没有的授权视为未发生」：COORD-002；信封字段：COORD-008 S4。
- 版本化 git 钩子与 `core.hooksPath`：COORD-003/COORD-007 时期随 `check_docs.py` 一并落地。

**完成规则**
- 「`IMPLEMENTED` 不等于 `DONE`」「三证据」「`UNITY_NA` 须复核附议」「采集前记录 HEAD 与 porcelain」：COORD-002 基线，未改。

**复核强制停点**
- 「先进入接受角色核对轮再交复核」：COORD-008 S1（停点自证直接交复核，取消逐轮停点确认）+ COORD-009 用户修订（核对轮必经）。
- 「原条件 5 的 `--base` 归因审计」：COORD-007 R2 移除。
- 「复核返工直接回复核，不经核对轮；第 2 次 `REWORK_REQUIRED` 后冻结、轮 3 终局」：COORD-009 (c)/T5；两处「轮 3 终局」句末「（决策信封 D2b 在效时按 workflow §4.4 一次定向返工，轮 4 终局）」：COORD-016 §2.3（用户授权 2026-09-26，U3=A 启用 D2b）。
- 工程轨道 K1–K5 停点：COORD-010 §6「必经停点」行。
- 「自证结果写入 `docs/evidence/` 下该停点证据文件的具名小节，交接行只写指针」：COORD-014（用户直接授权 2026-09-22），替换「逐条自证并写入交接行（按 BC 编号逐条附证据指针）」；原因是与 COORD-013 活跃交接行 ≤ 800 B 冲突。

### 2.2 `docs/collaboration-workflow.md`

**适用轨道**
- 整节：COORD-010（用户授权 2026-09-07）新增；原标题曾带「（COORD-010，2026-09-07 用户授权）」后缀，2026-09-11 去掉。

**§1 角色与责任、§1.1 模型池映射**
- 池表 supervisor 行「每路同一时刻至多 1 个写仓库角色」：COORD-019 补充同步（用户 2026-10-10 选 (a)）。
- 角色解耦与四池映射：COORD-002（2026-07-30）。表中「历史名」保留，用于解读旧记录。
- 接受角色越权栏「核对轮不跑测试、不改实现、不因读码新增 BC 行」：COORD-009 T1/T2。
- 「工程轨道不改变本表」：COORD-010；2026-09-28 用户直接指示（账本「全局 — 用户指示：工程轨道构思改用 Opus 池，复核不变」）改为「工程轨道沿用同一池映射…，唯一差异是构思跑 Opus 池」，池表 Fable 行改「研究轨道构思」、Opus 行加「工程轨道构思」，「构思与复核共用最强池」限定为研究轨道。

**§2 统一工作 ID**
- 「轨道标注 `Workflow: engineering-v1`」：COORD-010。
- 「轮次命名 D/C/R 分开计数、存量『接受轮 N』不回改」：COORD-009 T7。

**§3 状态门**
- 基线：COORD-002；「工程轨道使用同一张状态门表、`CLOSED_*` 不是验收通过」：COORD-010。

**§4.1 构思角色**
- 第 8 要素「只读真数据试跑数字」：COORD-008 S5（2026-09-02，本提案唯一加法）。

**§4.2 接受角色**
- 「`REJECTED` 限定为需用户授权的偏离」：COORD-009。
- 「提案文件的形态」（接受后只承载已接受设计 + BC 表，不逐轮追加，600 行信号）：COORD-008 S3。
- 「BC 表结构与自检」（复核项闭集、覆盖声明、证明方式前缀、全称量词闭集、`BASE`/`CLARIFY`/`NEW_OBLIGATION` 标签与配额、计数自 2026-09-03 起）：COORD-009 T2。
- 「工程轨道的合同形态」（`AC-n`）：COORD-010。
- 「真数据试跑先于合同冻结」：COORD-008 S5。
- 「退修上限：第 2 次退修后上交用户二选一」：COORD-007 R6（用户授权 2026-08-12）；「计数按提案既有轮次追溯生效」出自其接受轮 BC-C7-8；「只数设计轮」：COORD-009 T7。

**§4.3 实现角色**
- 「逐条 BC 的证据指针」：COORD-009 T1；「测试输出纪律」：COORD-009 T8。

**§4.3.1 复核稳定候选停点**
- 「核对轮是必经但有界的异源候选检查」：COORD-008 S1 取消了接受角色逐轮停点确认，COORD-009 T1 + 用户 2026-09-03 修订把接受角色原先无范围、无次数的拒收权替换为固定输出、每停点至多退回 1 次的核对轮。
- 四项自证条件：COORD-002 起；原条件 5（`check_role_writes.py --base` 逐路径归因）按 COORD-007 R2 移除，依据是记录在案的 50 次运行 0 真阳性、1 假阴性；已提交批次的写入归因改由各角色收工未提交自检（§7 规则 7）与 COORD-007 R5 修复后的基础设施保护承担。
- 「返工直接回复核，不经核对轮；开新轮由 §4.4 开轮资格决定」：COORD-009。
- 「自证结果写入证据文件具名小节、交接行只写指针」：COORD-014（2026-09-22），替换「把自证结果写入交接行」。
- 工程轨道 K1–K5 段：COORD-010；「可行性探测可前移，独立立项与额度不减」：用户 2026-09-07 批准 A+B+C 时的点名澄清。

**§4.3.2 诊断验证通道与人眼保真检查**
- 整节：COORD-005（用户授权 2026-08-04）。起因是 P1-SCENE-006 F23：正式 T1′ 测了无材质灰色替身，帧一直在盘上，却没有任何流程步骤要求人眼核对——正式证据纪律核对哈希、计数与协议链，不覆盖「渲染出来的东西对不对」这类范畴错误。原标题曾带「（COORD-005）」后缀。

**§4.3.3 核对轮**
- 整节：COORD-009 T1，用户 2026-09-03 修订定为实现后必经；原标题曾带「（COORD-009 用户修订）」后缀。

**§4.4 复核角色**
- 「开轮资格与 PLAY_GOVERNING 唯一定义」：COORD-007 R1。
- 「finding 分级、CLASS_3 不阻断」：COORD-007 R4；CLASS_3 闭集补入「证据叙述中的计数或枚举（当且仅当不驱动动作）」：COORD-008 S6。
- 「finding 路由：CLASS_2/3 直交实现角色，接受角色只在 CLASS_1/争议/用户要求时复判」：COORD-008 S2；「复判写提案 `## Acceptance rulings（复判）`，接受角色无 `docs/reviews/*` 写权限」：COORD-009 修订 B（2026-09-03）。
- 「范围判据与依据列六值」：COORD-009 (a)(d)/T3。
- 「增量轮与双基线、`round_candidate`、`blocks_consuming_gate`、账本 release 按 finding-id 匹配」：COORD-009 (b)/T4；账本 release 路径出自修订 B。
- 「轮次上限与冻结集、轮 3 终局」：COORD-009 (c)/T5；终局句扩为「D2b 在效时 supervisor 仅可批准 1 次定向返工…返工后按开轮资格分路（有资格开轮 4；无资格走回归通道）」及阻断 finding 闭合段「D2b 无资格路径下『下一轮』指原复核文件『回归核实』小节、写终局 verdict 与 `passed_candidate`、不新编轮号」：COORD-016 §2.3/BC-4（用户授权 2026-09-26）。
- 「阻断 finding 的闭合四条件、`NOT_MECHANIZABLE`、不设例行纯闭环复核轮」：COORD-007 R3；条件 (2) 中接受角色的重复复算由 COORD-008 S2 删除，只剩复核角色的修前红/修后绿。
- 「机读通过指针 `passed_candidate`」：COORD-007 R7。
- 「只在一次性 worktree 接触实现代码、一行也不许修」：COORD-002 基线。

**§4.5 用户**
- 基线：COORD-002；「采集前记录 HEAD 与 porcelain」同期。

**§4.6 接受角色：关闭或返工**
- 「只在最终通过轮消费 verdict（中间轮不消费）」：COORD-008 S2。
- 「归因机械派生、『范围外已知缺陷』账本、四个度量」：COORD-009 T6 及 §4 验收度量。
- 「工程轨道同一套关闭动作」：COORD-010。

**§4.7 周期性新鲜上下文设计审查**
- 基线：COORD-002；「工程轨道不新增第四个节点」：COORD-010。

**§5 交接记录最小字段**
- `progress`/`consuming` 字段：COORD-003 与 COORD-007 R8。

**§6 共享文件的职责**
- 表中 `docs/proposals/` 行「接受后 = 已接受设计 + BC 表 + 待裁定 + 核对表，不逐轮追加」：COORD-008 S3 + COORD-009；`docs/implementation-status.md` 行「范围外已知缺陷账本」：COORD-009 T6；`docs/evidence/` 行「只保留当前状态、不逐轮追加」：COORD-008 S3；`docs/engineering-workflow.md` 行：COORD-010。
- 状态板体量段：单条行数上限（COORD-004）、四个滚动节与 `rotate_docs.py` 按月归档（COORD-007 R9 删除，2026-08-12）、全文 500 行提交阻断（COORD-010 §6 删除，2026-09-07）三代机制依次退场，现行只剩分节上限 + 内容归属判断。
- chore 常设内容维护段：用户 2026-09-08 授权及同日问题 1/3/4/5 修订。
- chore 常设内容维护段删去「终态 Gate board 摘要」：COORD-014（2026-09-22）。
- §6 状态板体量段的「`## Log` 可压池上限、Gate board `Lifecycle` 列、除 `docs/status-history.md` 外不新增归档系统、移出叙述移入该文件且须用户按 work item 一次同意、git 仍是权威档案」与 §6.1「除该沉淀池外不新增归档系统」：COORD-012 第三批，用户 2026-09-20 授权「把这三处改成和agentmd一样的措辞」（账本同日条目）；措辞与 AGENTS「共享状态更新」逐句对应。
- §6 状态板体量段「`ENDED` 行由关闭方整行移入 parked、`PAUSED` 行只留一行索引」「状态板只承载当前工作与非活跃项一行索引」与 §6.1 前言、第 1/3/4 项的 parked 口径：COORD-013（用户直接授权 2026-09-21）。替换了 §6.1 第 4 项「Gate board 全表仍在原处…不迁出行」与第 3 项「不建立另一份状态表；未闭义务不因指向历史文件而退出当前入口」的旧口径。
- 「可派生标识禁手写」：COORD-007 R7。
- §6.1 轻量按需读取：用户 2026-09-08 授权；原标题曾带「（用户授权 2026-09-08）」后缀。

**§7 并发与冲突规则**
- 规则 0 执行轨道纪律：COORD-003（用户授权 2026-07-31）确立；COORD-019（用户直接授权 2026-10-10）改为分两路 `fast`/`vlm`、每路 1 消耗性 + 2 零消耗；COORD-007 R8（用户授权 2026-08-12）改为 1 消耗性 + 2 零消耗并换成 Gate-echo 触发器；「判据 = token 表成员资格」为 COORD-007 接受轮 5 N12 裁定；「两轨逐字相同、共享槽位互斥按现状保留、每工作项一份预算信封」：COORD-010 §6「资源与并发」行，用户 2026-09-07 点名「维持现状」，该批不新写槽位条文。
- 规则 1「开工读取与修改前重读均按 §6.1 执行，不要求全文重读」：COORD-012 N3（用户 2026-09-20 授权，账本同日条目）；原文「所有 Agent 开工前和交付前都重新读取 `current-status.md`」出自 COORD-002 时期，与 2026-09-08 §6.1 重复。
- 规则 3「复核只在一次性 worktree」：COORD-002。
- 规则 7「收工前未提交自检」：COORD-002/COORD-003；「已提交批次的写入归因不做机械检查」：COORD-007 R2 移除原 §4.3.1 条件 5 的 `--base` 审计；「唯一例外 `--infra-fix`」：COORD-007 R5；「复核角色除外」：COORD-007 复核轮 2 F3（用户 2026-08-12 授权修复）；「协调批次不运行角色写入检查、凭据是账本条目」：COORD-002 补记的收工约定。

### 2.3 `docs/engineering-workflow.md`

- **生效依据**：依据 `docs/proposals/COORD-010-engineering-transition-and-data-closeout.md` §6 机制表，经用户 2026-09-07 批准该提案 §10 的 A+B+C（账本条目「COORD-010 — 批准 §10 A+B+C 整体落地（含两项点名澄清）」），规则候选经 `R1@batch1` REWORK_REQUIRED（F1/F2 阻断）→ `R2@batch1` PASS_WITH_NOTES（`docs/reviews/COORD-010.md`）后生效；状态迁移批经用户 2026-09-08 按 §8 T1–T7 验收。原文头段曾写「本文不自证生效，以状态板 COORD-010 行与复核文件为准」。
- **§0 适用范围与路由**：「只替换 11 项机制、未提及不等于豁免、fail-closed、既有 work ID 不得追加该行」出自 COORD-010 批 1 规则候选及复核 R1/R2@batch1。点名沿用的旧规则中，「可派生标识禁手写」来自 COORD-007 R7，「诊断验证通道与人眼保真检查」来自 COORD-005。
- **§2 任务合同**：`AC-n` 取代七列 BC 表、不受 `NEW_OBLIGATION` 配额、依据列不新造 token：COORD-010 §6「任务合同」行及复核轮对「不新造 token」的裁定。
- **§4 K1–K5**：COORD-010 §6「必经停点」行。
- **§8 资源与并发**：原标题「（维持现状）」与开头「用户 2026-09-07 逐字澄清：多角色分工与并发纪律维持现状」记录的是批准 A+B+C 时的点名澄清；「本批不新写共享槽位条文」是该批的执行说明，2026-09-11 一并移入本文。
- **§8 资源与并发**（续）：「每路 1 条消耗性 + 2 条零消耗（双路 `fast`/`vlm`）」：COORD-019（用户直接授权 2026-10-10）。
- **§8 资源与并发**（再续）：「每路同一时刻最多 1 个写仓库角色、两路可并行」：COORD-019 补充同步（用户 2026-10-10 选 (a)）。
- **§9 硬件与端侧探测**：「Jetson 小规模可行性探测可以前移，但仍须独立立项、独立说明设备与额度」出自同一次点名澄清（用户原话「jetson同意前调」）。
- **§10 状态板体量**：全文 500 行硬阻断由 COORD-010 §6 批准移除，当时落点是 `AGENTS.md`「共享状态更新」、workflow §6 与 `tools/check_docs.py` 的同批修改；chore 常设内容维护出自用户 2026-09-08 授权及同日问题 1/3/4/5 修订。「除 `docs/status-history.md` 这一个单向沉淀池外不新增归档系统」：COORD-012 第三批，用户 2026-09-20 授权（账本同日条目）。
- **§10 状态板体量**（续）：「只放当前工作与非活跃项一行索引」「除 status-history 与 parked 外不新增归档系统」：COORD-013（用户直接授权 2026-09-21）。
- **§10 状态板体量**（再续）：chore 维护一句删去「终态 Gate board 摘要」：COORD-014（2026-09-22）。
- **§4 K1–K5**（续）：「候选含不可重跑的消耗步骤时先过一次停点再消耗」：COORD-017（用户 2026-10-04 授权）。来由：P1-ENG-JET-001 阶段 A 只有合并停点 `K1K3K4`，中继正式轮 5/5 用尽后复核才发现回程去重缺陷，补丁未能上板验证。
- **§6 测试**（续）：「停点全套的本机模型加载属信封维度、随信封一次签发」「具名文件窄修以 focused 加修前红/修后绿代替全套」：COORD-017。来由：同一工作项为一次约 4 分钟的全套先后追加 SUB:2/SUB:5/SUB:6 并由用户具名破例，约 12 次派发、6 次用户表态。
- **§9 硬件与端侧探测**（续）：「先核环境事实再定合同」：COORD-017。来由：该工作项合同假设板上有可复用的 torch，实际没有，装栈用了 3 次实现派发与 6 次用户表态，并因依赖干跑多取回 2.3 GB。
- **§13 修改权限**：COORD-010 批 1 同批把 `docs/engineering-workflow.md` 加入 `tools/check_role_writes.py` 的 `INFRA_PATTERNS` 并补 `tests/test_check_role_writes.py` 正反例；原文「该常量修改未落地时本节按未生效处理，本文件不得单独合入」是该批的合入条件，已满足，2026-09-11 移入本文。

## 3. 本文的来历

- 2026-09-11 COORD-011：用户授权「首先修改一下规则正文和来历的内容，保存旧版方便后续对比审查」（账本同日条目）。监督会话把三份规则文件中的批次号、授权日期、被替换机制、事故叙述与一次性执行说明剥离到本文，规则正文保留全部现行要求，章节编号与标题不变，意图零语义变化；旧版整份存于 `docs/archive/rules-before-provenance-split-2026-09-11/`。对比审查后若发现语义漂移，以旧版回退对应段落并在本节记一行。
