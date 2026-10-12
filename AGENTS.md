# Agent 协作规则

本仓库采用 `docs/collaboration-workflow.md` 定义的多角色流程（角色细则
与模型池映射见 `docs/roles/` 和 workflow §1.1）。所有 Agent 共享同一
文件系统和全局状态板，但对话上下文不会自动共享。

本文只写现行规则。每条规则的来历（哪一批协调批次、哪一次用户授权、
被替换的旧机制及原因）统一记在 `docs/workflow-changelog.md`，按需查阅，
不在正文复述。

## 必读顺序

开始实质工作前：

1. 读取 `docs/current-status.md`，确认全局状态和当前交接；按 workflow §6.1
   先读当前结构节和全部交接，再查本项及依赖项的 Gate board 行，历史按需展开。
2. 按「执行轨道纪律」一节自查；活跃交接超出轨道上限时先停下处置，再谈本职工作。
3. 读取 `docs/collaboration-workflow.md`，确认状态门和角色边界；工作项走
   工程轨道（判据见「工作流轨道路由」一节）时另读 `docs/engineering-workflow.md`。
4. 读取相关提案/复核文件及 `docs/phase1-single-drone-design.md` 对应章节。
5. 涉及里程碑证据时读取 `docs/implementation-status.md` 的对应章节；复用旧资产
   时先读其工程继承清单与缺陷账本，再沿来源读相关证据。按需读取不减免本角色
   必须完整核对的候选、合同、复核轮次或全局消耗性门检查（workflow §6.1）。

## 工作流轨道路由

本仓库并行两条工作流轨道，**缺省是研究轨道**：

- **研究轨道（缺省）**：`docs/collaboration-workflow.md` 的完整状态门、
  轮次命名（`D<n>` / `C<n>@<停点>` / `R<n>@<停点>`）、BC 表与核对/复核
  规则。提案抬头元数据块（`Status:`/`Revision:` 所在的那几行）里 `Workflow:`
  缺失，或取值不是逐字的 `Workflow: engineering-v1` 的，一律走这条轨道
  （存量提案无该行，全部属研究轨道）。
- **工程轨道**：提案抬头逐字写 `Workflow: engineering-v1` 的工程提案及其
  派生 work item，按 `docs/engineering-workflow.md` 执行任务合同（稳定编号
  的 AC-n 验收项）、K1–K5 必经停点与复核收敛规则。该文件**只替换**
  COORD-010 §6 机制表逐行列出的那 11 项机制；本文件与
  `docs/collaboration-workflow.md` 中未被其逐条替换的规则对工程轨道全部
  继续适用——**未提及不等于豁免**，包括「复核强制停点」、可派生标识禁手写、
  复核机读行与 `blocks_consuming_gate` / `releases_consuming_gate` 配对及
  消耗性门机检、测试输出纪律。

提案抬头那一行只是**申请**：是否走工程轨道由接受角色在 `ACCEPTED` 时逐字
裁定并写进提案，构思/实现角色不得自行判定。缺省、申请被驳回、`Workflow:`
取值不在闭集（当前闭集只有 `engineering-v1`），或接受角色未写明裁定的，
一律按研究轨道处理并停下问接受角色（fail-closed）；**既有 work ID 一律不得
追加该行**。轨道不从题材、目录或口头约定推断。COORD-010 §3 点名的旧工作项
只执行该表具名的终止/延期动作；**历史实现与复核不回溯套用工程轨道规则**，
既有 verdict、证据、负结果与主张上限按当时规则解读。

两条轨道共同适用、工程轨道不得放宽的红线：本文件「执行轨道纪律」的每路
1 条消耗性 + 2 条零消耗上限（双路 `fast`/`vlm`，COORD-019）与 Gate-echo；Play/采集操作单沿用的共享槽位互斥
使用约定按现状保留，不另立条文；「角色边界」的写权限划分（接受/复核角色
不写运行时代码，复核角色发现缺陷只写复核文件）；「完成规则」的 `DONE`
三证据与 `UNITY_NA` 复核附议；用户关键授权逐字记入 `docs/authorizations.md`。
`CLOSED_*` 只表示停止该范围的工作，任何轨道都不得冒充验收通过。

工程轨道「每工作项一份预算信封」不改变信封来源：信封只能由用户授权给出
并逐字记入 `docs/authorizations.md`，缺项视为 0，任何越界回到用户。
新增设备、新增额度或新的消耗类别（例如 Jetson 小规模可行性探测）须独立
立项并单独说明设备与额度，不由既有工程任务的信封覆盖。

本节属工作流基础设施，修改需用户直接授权的协调批次。

## 执行轨道纪律

**任何时刻 `docs/current-status.md` 的 Active handoffs 分两路（`Lane` 列，
闭集 `fast` / `vlm`），每路至多允许 1 条消耗性活跃交接和 2 条零消耗活跃
交接。** 消耗性 = 创建或消耗 scenario/session/run ID、Play 配额或 API
预算；交接表 `Consuming` 列（yes/no）与 `Lane` 列逐行声明，缺列或非闭集值
即拒绝提交。`fast` 路 = 快层、闭环、场景、机身与云台、采集与操作流程（执行机
Air/Unity 主机）；`vlm` 路 = 语义层（VLM 数据、训练、探针、板端 VLM 部署与
Jetson 探测；执行机 Mac mini、5060、Jetson、云 GPU）。归路由写该行的角色按
工作内容判断，接受角色可更正；零消耗的协调项按其服务的一路归入，两路都
涉及的归 `fast`。两路的信封分别由用户签发；两路要同时占用同一台执行机时，
由用户在信封里写明互斥。强制核对不挂在"暂停"动作上，而由 **Gate-echo**
机检承担：每行交接内引用的、**在 Gate board 有行的反引号标识**（work ID
与 `M1` 类里程碑行，含本行自身的；判据 = token 表成员资格）必须以
`` `<ID>`@<Overall> `` 形式逐字携带 Gate board 当前 Overall token，
不一致即拒绝提交。

- **占轨道的**只有 Active handoffs 表中 Status 不以 `PAUSED` 开头的行。
  Gate board 中 `DONE`/`CLOSED_*`/`BLOCKED_*`/`DEFERRED_*`/
  `OUT_OF_CURRENT_SCOPE` 的行不占轨道，无须暂停。
- **暂停表示法**：Status 列写 `PAUSED_<原因>`（如
  `PAUSED_SINGLE_TRACK`、`PAUSED_PENDING_REVALIDATION`）。暂停只冻结
  推进，不改变该项已有的 verdict、证据或门状态；恢复由用户决定。
- **交接文字必须与现实一致**：Gate-echo 强制门值同步；发现其他失效
  文字（前置条件已被走完、引用工件已作废）时在同一批次就地修正，
  不留给下一个接手的角色。
- 超限或 echo 不一致时 `tools/check_docs.py` 在提交前拒绝；处置是向
  用户逐条汇报 work ID、状态门与执行进度，由用户决定保留哪些，其余
  Status 改为 `PAUSED_*` 并同批提交。

本纪律属工作流基础设施，修改需用户直接授权的协调批次。

## 角色边界

角色名描述职能，不绑定模型；历史记录中的 Fable/Codex/Sonnet 指当时的
同名分工，不回改。细则以 `docs/roles/` 为准：

- **构思（ideation，研究轨道 Fable 池最强档、工程轨道 Opus 池，`/fable`）**：在 `docs/proposals/`
  提交提案；不把提案当成正式设计，不自行标记 `ACCEPTED`。
- **接受（acceptance，Codex CLI 中档，`/prompts:codex`；备用 `/accept`；
  可被 supervisor 经 `codex exec` 无人值守拉起，COORD-015）**：
  接受、退修或拒绝提案并写可逐条核对的 binding clarifications（含复核项/
  证明方式/标签列）；实现完成后必做核对轮 `C<n>@<停点>`，以 Codex/Claude
  异源检查重读完整候选 diff、BC、证据指针及其直接关联代码，每停点至多退回
  1 次；不跑测试、不改实现、不加 BC 行、不签发独立复核（workflow §4.3.3）、
  CLASS_1 或争议时复判、冻结集裁定、收尾关闭/返工归因（从复核依据列机械
  派生）、维护里程碑证据与「范围外已知缺陷」账本；不写实现代码，不签发
  独立复核。
- **实现（implementation，Claude Opus 大量程，`/implement` 主入口；Cursor
  `/coding` 保留为遗留手动入口，COORD-015 U8）**：只实现已 `ACCEPTED` 范围；clarifications 按字面
  执行，歧义退回接受角色；不得给自己的实现签发独立复核通过。
- **复核（review，最强池，`/review`；档位不得低于实现者，永远不用最便
  宜档）**：新鲜上下文重读真实代码，只在一次性 worktree 接触实现代码，
  在 `docs/reviews/` 记录 verdict；发现缺陷的唯一合法动作是写复核文件，
  一行代码也不许修，修复交回实现角色。
- **辅助（chore，Sonnet 池最便宜档，`/chore`）**：轮换归档、代录、
  检索、非权威预筛；无任何门决定权。
- **调度（supervisor，Opus 池，`/supervisor`；COORD-015）**：接力调度
  （按状态板拉起下一角色，每路同一时刻至多 1 个写仓库角色，COORD-019）、提交后
  事实核查（非权威，只核验凭据与磁盘事实）、决策信封内的有界代拍与
  子额度审批（逐条入账）、检查点摘要、COORD 提案起草（5 天窗口节流）、
  用户授权/反馈当场代录；不写运行时代码/配置/测试/工具，不写
  `docs/reviews/`、`docs/design-reviews/`、`docs/implementation-status.md`，
  不签发 `ACCEPTED`/verdict/`DONE`/`CLOSED_*`，不首签任何信封；
  不可代拍事项（COORD-015 §5.2 闭集）直达用户；协调批次仅凭用户逐字
  授权执行。细则 `docs/roles/supervisor.md`；派发日志
  `docs/evidence/supervisor-dispatch.jsonl`。
- **用户（Unity 验证与关键授权）**：运行 Unity 用例并反馈；关键授权由
  当场会话逐字记入 `docs/authorizations.md`；反馈可由接受/辅助角色代录
  进 `docs/unity-test-log.md`。另可应实现角色之请做诊断性 Play/目检
  （非证据、不耗 ID）；新渲染管线冻结前须有人眼保真检查
  （细则见 workflow §4.3.2）。

M2、M5 和投稿前还必须进行一次新鲜上下文设计审查。审查者不能是相关提案
作者，也不应是该设计的主要接受/实现者；里程碑以终止性 disposition 收束
但仍产生研究主张时同样到期，推迟须经用户批准。规则见协作流程 §4.7。

## 共享状态更新

- 提案、实现、复核、Unity 验证和状态条目始终使用同一 work ID。
- 修改前按 workflow §6.1 重读 `docs/current-status.md` 的待改章节（开工读取
  同按 §6.1，不要求全文重读）。跨多轮工作先声明 owner、范围和状态。
- 实质代码修改、验证结论、已接受设计决策或阻塞变化，必须在同一工作批次
  更新 `docs/current-status.md`；里程碑证据变化时同步
  `docs/implementation-status.md`。
- **状态板只装当前工作，一件事只写一处。** 活跃项（Gate board `Lifecycle`
  = `ACTIVE`）的门值、交接、下一动作与未闭义务留在状态板；非活跃项
  （`PAUSED`/`ENDED`）的门值、未闭义务、停点与约束原文在 `docs/parked-status.md`
  （事实源，开工不读；恢复暂停项、引用已终止项、开新工作项前读），状态板只留
  `PAUSED` 行的一行索引。每次交接：交接行是写「谁接手、做什么、读哪个文件」的
  唯一处；Gate board 行只改门值 token 与证据指针；`## Log` 新条目一句结论加
  指针；Current state 只在未闭义务增减时改；Immediate next actions 不复述交接行。
  字节上限由 `tools/check_docs.py` 机检：`## Log` 之前的结构节合计 ≤ 30000 B；
  本提交改动过的 `ACTIVE` Gate board 行与活跃交接行各 ≤ 800 B；`PAUSED` 行
  ≤ 400 B；暂停交接行 ≤ 300 B；本批次新写 Log 条目 ≤ 600 B（字节按 UTF-8）。
- 状态历史统一记录在单一 `## Log` 节：最新置顶，每条以
  `### YYYY-MM-DD — 标题` 开头。不设滚动日志节，不做按月归档；
  `docs/archive/` 是只读遗留，不再向其归档状态板。从 `## Log` 压缩或删除
  移出的叙述整段移入 `docs/status-history.md`（移动而非复制，保留原标题与
  原文；移入前须先经用户同意，以 work item 为单位一次同意、不逐条，同意原话
  记入 `docs/authorizations.md`）；git 历史仍是权威档案。「单一 `## Log` 节」的约束不适用于
  `docs/status-history.md`：它是单向沉淀池，不是事实源，不含门值与未闭
  义务，不进任何角色开工必读，不被 `tools/check_docs.py` 扫描，不得被引为
  义务或证据来源，状态板指针仍只指向权威文件。
- `docs/current-status.md` 的硬上限只有分节上限：Current state ≤ 100 行、
  Immediate next actions ≤ 50 行、Active handoffs ≤ 70 行、`## Log` 可压池
  ≤ 300 行（可压池 = 全部 Log 条目扣除本批次新写的条目与关联 Gate board
  `Lifecycle` 非 `ENDED` 的 work item 的条目；无关联 work ID 的条目直接计入，
  判据细则见 `docs/roles/chore.md`「允许的任务」）；全文不设行数硬顶。Gate
  board `Lifecycle` 列（闭集 `ACTIVE`/`PAUSED`/`ENDED`）逐行明示只是暂停还是
  已经终止，由接受角色或用户随 Overall 维护，`ENDED` 是唯一进入可压池的终止
  标识，缺列或非闭集值由 `tools/check_docs.py` 拒绝。`ENDED` 行不留在状态板：
  关闭方在同一提交把整行移入 `docs/parked-status.md`「已终止（ENDED）」表（其
  Log 条目随之按无关联计入可压池）；转 `PAUSED` 时同一提交把行压成一行索引、
  原行与停点移入该文件。上限数值的任何
  修改须与 `tools/check_docs.py` 同批提交，不得先落文档后改工具。同样的
  分节上限见 `docs/collaboration-workflow.md` §6。
- 体量治理靠分节上限（含 `## Log` 可压池上限）和下一条的「内容放错了地方」
  判断，不为总行数反复压缩提交：分节写不下时压缩或删除**旧** Log 条目的
  叙述，只保留指针、结论和未闭义务，禁止为腾空间压缩本批次新条目或删减
  他人未沉淀的内容；已提升为常驻规则的叙述在压缩前确认已落入对应常驻
  文件。除 `docs/status-history.md`（单向沉淀池，不是事实源）与
  `docs/parked-status.md`（非活跃项台账，是事实源，开工不读）外不为此新增归档
  系统或状态文件，也不把过程叙述搬进状态板换取行数。
- chore 常设内容维护统一见 `docs/roles/chore.md`「允许的任务」：可按该节
  主动检查/压缩旧 Log，并按其条件处理旧 Log 删除；
  全文行数仅作排查提示，不设全文提交门，也不以行数验收。分节硬上限、
  角色写权限和证据门均不放宽。
- 写不下就是**信号：内容放错了地方**。状态板只放指针、当前门和
  未闭义务；过程叙述（哪一轮怎么失败、跑了多少帧、复核怎么走的）属于
  `docs/reviews/`、`docs/evidence/`、`docs/design-reviews/` 和
  `docs/unity-test-log.md`，在状态板重写一遍只会制造多份内容漂移。
- **可派生标识禁手写**：上一通过候选、工件 SHA、run 目录名、HEAD 等可从
  git 与复核文件派生的标识一律运行时解析，禁止写进手维护文档，存量不
  回改；复核通过轮在复核文件写机读行 `passed_candidate: <40 位 SHA>`
  （`REWORK_REQUIRED` 轮禁止出现）。
- **复核机读行与消耗性门机检**：复核文件每轮 §0 写
  `round_candidate: <40 位 SHA>`（第 N+1 轮的"修复触及行"基线）；未改动行
  上的 `上轮漏检` CLASS_2 写 `blocks_consuming_gate: <finding-id>`（不带
  work ID），同一提交把受影响的消耗性交接改为
  `PAUSED_CONSUMING_GATE_BLOCKED_<finding-id>`；闭合时写
  `releases_consuming_gate: <finding-id>`（复核角色红绿核实后写，按文件顺序
  配对）；接受角色改标 `SCOPE_GAP` 时不写复核文件，改在
  `docs/implementation-status.md` 账本行标 `RELEASED_SCOPE_GAP`，
  `check_docs.py` 视同 release；复判写提案「复判」节。`tools/check_docs.py`
  拒绝"存在未 release 的 blocks 行且 Active handoffs 有未暂停 `Consuming=yes`
  行"的任何提交。每条 finding 带依据列：`BC-n` / `IN_SCOPE_NO_BC` /
  `SCOPE_GAP` / `上轮漏检` / `上游漏检` / `RED_LINE`。
- **轮次命名**：设计轮 `D<n>`、核对轮 `C<n>@<停点>`、复核轮 `R<n>@<停点>`
  分开计数（退修上限只数 D 轮；核对轮每停点 ≤ 1 次退回；复核
  `REWORK_REQUIRED` 每停点 ≤ 2 次，第 2 次后未闭集冻结、轮 3 终局（决策信封 D2b 在效时按 workflow §4.4 一次定向返工，轮 4 终局））；提交
  信息主题以 `<work-id> D2` / `C1@<停点>` / `R2@<停点>` 开头；存量「接受轮 N」
  不回改。
- **测试输出纪律**：开发期只跑 focused；全套在停点跑一次并写入证据文件；
  核对轮不跑测试；复核 focused 一次 + 每条阻断 finding 红绿一次；测试输出
  写文件、上下文只回显摘要，不带 `-v`。
- 基于磁盘最新内容合并，保留其他角色的新条目，不得用旧上下文整文件覆盖。
- 修改批次不是 Git commit，不得虚构 commit ID。
- 任何角色更新 `docs/current-status.md` 后应运行
  `python3 tools/check_docs.py` 并使其通过。
- 每个角色收工提交前运行 `python3 tools/check_role_writes.py --role
  <role>`，按写入白名单核对本批次**未提交**改动；越权路径先恢复再
  提交。已提交批次的写入归因不做机械审计。工作流基础设施（本文件、
  `CLAUDE.md`、`docs/collaboration-workflow.md`、`docs/engineering-workflow.md`、
  `.claude/`、`.cursor/`、`docs/roles/`、`tools/check_*.py`、`tools/githooks/`）
  仅用户直接授权的协调批次可修改；**唯一例外（复核角色除外）**：非复核
  角色可在只改 `tools/check_*.py` 与 `tests/test_check_*.py` 的单独提交里
  修复自检工具的假阴性或坏夹具，提交信息贴出触发的失败输出，不与证据产出
  混在同一提交，用 `--infra-fix` 模式核对，由下一轮复核逐文件 diff。复核
  角色不适用本例外：红线 A 对 `controller/`、`Assets/`、`tools/`、`tests/`、
  `config/` 的绝对禁令优先，复核发现自检工具缺陷时只写复核文件。协调批次
  不运行角色写入检查，其合规凭据是提交信息引用的 `docs/authorizations.md`
  授权条目，无条目支撑的 infra 改动视为越权。
- 用户关键授权（GO/NO-GO、范围与协议变更、消耗性资源动用、里程碑
  关闭）由授权发生所在会话逐字记入 `docs/authorizations.md`；实现会话
  中的授权转交接受/辅助角色记录（实现角色对账本和 Unity 日志只读）。
  账本没有的授权视为未发生（2026-07-30 起）。授权可带信封（阶段、尝试
  次数上限、GPU·h 上限、API 次数上限、Unity/Play=否）：信封内的工程性
  重试与 supersession 不需要新授权，由接受角色在 BC 表记一行归因；缺项
  视为 0；任何越界回到用户。supervisor 的决策信封
  （`supervisor_decision_envelope`）与执行信封子额度块
  （`supervisor_subdelegation`）同样只能由用户逐字签发入账，缺项视为
  不启用；代拍、撤销与否决条目带 `at:` 等机读字段，由
  `tools/check_ledger.py` 机检（COORD-015 §5）。
- **派发凭据与调度日志（COORD-015）**：被 supervisor 拉起的角色每次
  派发提交在尾注带 `Dispatch-Id` 与 `Role-Check: <role> pass`，提交主题
  以 `<work_id> <this_round>` 开头；接力报告必填字段见各角色细则
  「被 supervisor 拉起时」。supervisor 的派发登记/核销/对账写入
  `docs/evidence/supervisor-dispatch.jsonl`。
- 版本化 git 钩子 `tools/githooks/pre-commit` 会在每次提交前自动运行
  该自检并在违规时拒绝提交。新环境 clone 后执行一次
  `git config core.hooksPath tools/githooks` 启用。
- 接受角色在 Codex CLI 的开工 prompt 存放在用户级
  `~/.codex/prompts/codex.md`（命令 `/prompts:codex [WORK_ID]`）。

## 完成规则

`IMPLEMENTED` 不等于 `DONE`。运行时功能只有在实现者证据、独立复核和
用户 Unity 验证均通过后才能关闭。不影响 Unity 的纯文档/离线事项可使用
`UNITY_NA`，但必须写明理由并经复核角色附议。Unity 采集开始前，当轮
发令角色记录 `git rev-parse HEAD` 与 `git status --porcelain` 并写入
Unity 日志条目，确保采集对应被复核通过的候选。M2、M5 和投稿节点还受
独立设计审查门约束。

## 复核强制停点

实现角色整理稳定候选，按 workflow §4.3.1 的四项条件逐条自证，自证结果
（按 BC 编号逐条附证据指针）写入 `docs/evidence/` 下该停点证据文件的具名
小节，交接行只写该文件与小节的指针；先进入接受角色核对轮再交复核角色。
核对轮是必经的 Codex/Claude 异源候选检查（workflow §4.3.3）：读取完整
候选 diff 与直接关联代码但不跑测试、不改实现、不签独立复核，同一停点至多
退回 1 次，第 2 次照交复核并附核对表和未决关注项；自证条件不成立的候选由
复核角色给 `REVIEW_BLOCKED`，不开轮。到达停点后必须更新状态、提交并推送
候选版本、准备准确的复核范围，然后停止启动依赖该结果的后续实现。已知的
自动测试或 Unity 失败应先由实现角色修复并复测，不把明显失败的中间版本交给
复核；复核判定返工后修复回到同一停点，是否开新复核轮由 workflow §4.4 开轮
资格（PLAY_GOVERNING diff 非空）决定，阻断 finding 的闭合走 §4.4 回归测试
通道。复核返工直接回复核，不经核对轮；同一停点第 2 次 `REWORK_REQUIRED`
后未闭 finding 集冻结、轮 3 终局（决策信封 D2b 在效时按 workflow §4.4 一次定向返工，轮 4 终局）。

强制停点包括：M0、M2、M3、M4、M5、可选 M6、M7 的关闭候选，以及任何
改变帧/控制协议、坐标时间语义、主指标定义、安全约束或模型决策逻辑的独立
work item。纯文档、日志、测试补强和不改变语义的小修可合并到下一停点。

工程轨道（`Workflow: engineering-v1`）的强制停点是 K1–K5（帧/控制协议与坐标
时间语义、安全约束/控制命令、模型决策与目标身份/重播种、数据划分/标签或对外
指标、对外发布候选），细则见 `docs/engineering-workflow.md`；各 K 停点同样保留
接受侧只读核对与独立复核，不以「工程」豁免上述关键检查，也不借用旧里程碑
（M0–M7）的关闭或已延期的设计审查门。
