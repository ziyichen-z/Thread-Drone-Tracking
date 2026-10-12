# COORD-009 — 复核收敛：核对轮、复核范围与轮次上限、BC 标签、消耗性门机检

Status: LANDED（2026-09-03 用户直接授权协调批次，T1–T10 已落地；同日用户
修订接受角色核对轮为实现后必经的异源候选检查；均不经接受轮，账本当日条目）
Author/role: 用户指派的监督会话起草（非构思角色的常规产出）；诊断初稿由用户转来的
外部审读提供，监督会话核对证据并修订
Created: 2026-09-03
Last updated: 2026-09-03

> 本文是提案，不是授权，也不是已接受设计。它提议修改工作流基础设施
> （`AGENTS.md`、`CLAUDE.md`、`docs/collaboration-workflow.md`、`docs/roles/`、
> `.claude/commands/`、`.cursor/commands/`、`tools/check_docs.py`、两份模板），
> 按 workflow §7 规则 7 这类修改**只能**由用户直接授权的协调批次执行，合规凭据
> 是 `docs/authorizations.md` 中的对应条目；本文自身不构成该授权。
> **本文硬预算 ≤ 400 行。** 本提案不改任何运行时代码：唯一的代码改动是文档自检
> 工具 `tools/check_docs.py` 与其回归，单独提交，由下一轮复核逐文件 diff
> （COORD-007 R5 通道）。

## 1. 诊断（磁盘证据核对后）

循环不是目标不明也不是架构问题，是复核环节结构性不收敛，且实际流程偏离了
文档。样本 = `P1-VLM-DATA-002` 2026-09-03 的 3 轮设计审查 + 3 次实现期退回。

- **候选从未到过复核角色**：`docs/reviews/` 没有 DATA-002 文件。实现期三次退回
  （裁定 BC-SURVEY-7…13、接受轮 4、接受轮 5）全部发生在接受↔实现之间；接受轮 1、2
  是提案退修，属设计好的构思↔接受路径，不计入本诊断。
- **S1 删了停点确认，但拒收权无范围、无次数、无输出格式**：`docs/roles/acceptance.md`
  第 15 行保留的拒收权实际上把停点确认换了个名字留下来。接受角色未违规；轮 4、5
  复跑 193 个测试、穷举 135/128 个停放候选，是这个洞的直接后果。
- **BC 表在 `ACCEPTED` 之后持续增长**：6 → 13 → 15 → 16，设计 v0.3.30 → v0.3.33，
  实现端追的是移动目标。BC-SURVEY-15 是接受角色自查代码后追加的条款。
- **复核规则自身有棘轮**：CLASS_2 按类别定义无范围边界；每轮对"上一通过候选"全量
  重审且新鲜上下文；无轮次上限。DATA-001 复核轮 3 仅因证据叙述计数不符（F15）开了
  一整轮返工。
- **代码层缺跨厂商多样性**：三次实现提交署 Claude Opus 5，复核在 Fable 池；设计层有
  Codex（GPT）接受兜底，代码层没有。
- **三次实现期退回没有一次是纯证据指针缺失**：全是行为缺陷、新义务或回归覆盖不足。
  因此核对轮的"不满足"与"证据缺失"同计不会误伤。

## 2. 提议的修改（T1–T10，逐文件；协调批次按字面执行）

**T1｜核对轮：接受角色的合同符合性核对，取代无边界拒收权**
- `docs/collaboration-workflow.md` 新增 §4.3.3：输入 = 候选 commit + 实现角色按 BC
  编号逐条附的证据指针；输出 = 提案固定小节 `## Contract conformance（核对表）`
  只保留最新一版，每条 BC 一行 {满足, 不满足, 证据缺失} + 理由；只核字面，不审代码
  质量，不跑测试，不读指针之外的代码，不新增 BC 行；同一停点退回 ≤ 1 次，"不满足"
  与"证据缺失"同计；第 2 次照交复核，核对表随候选附上作为待核实主张。核对轮不计
  复核轮次。这是 Codex 池在代码层的异源检查落点。
- §4.3.1 的"接受角色保留拒收权：可在任何时候把候选退回"改为指向 §4.3.3；§1 角色表、
  `AGENTS.md`「角色边界」「复核强制停点」、`docs/roles/acceptance.md`、
  `.claude/commands/accept.md`、`docs/roles/implementation.md`、
  `.claude/commands/implement.md`、`.cursor/commands/coding.md` 同句同步。
- `docs/proposals/README.md` 模板加节 `## Contract conformance（核对表）`。

**T2｜BC 表结构、自检与 `CLARIFY` / `NEW_OBLIGATION` 标签（替代冻结）**
- §4.2：BC 表每条一行：编号、条款、复核项（映射 §4.4 五项，每项至少一条或
  `N/A + 理由`）、证明方式（具名测试/工件/命令之一）、标签、依据、日期。全称量词
  （全部/所有/任一/均须）必须指向条款内已枚举或点名文件的闭集，否则退回重写。
  `REJECTED` 限定为需用户授权的偏离。
- `ACCEPTED` 后每新行标 `CLARIFY`（解释既有条款，须引用条款号，允许用"指向具名提交
  中的具名工件"枚举闭集）或 `NEW_OBLIGATION`（只能源于实现角色「待裁定」或复核
  `SCOPE_GAP`，禁止源于接受角色自查代码，每 work ID ≤ 2，超出回用户）。与 COORD-008
  S3"答复即 BC 表新行"兼容。存量行不打标签、不回改；计数自 2026-09-03 起。
- `docs/roles/acceptance.md`、`.claude/commands/accept.md`、`docs/proposals/README.md` 同步。

**T3｜复核 (a)(d)：范围判据与依据列**
- §4.4 新段：可达 = 触发状态是提案、BC 或验收条件点名的，或生产入口能从已归档
  工件产生的。依据列闭集六值：`BC-n`（可达且有 BC 覆盖，阻断）、`IN_SCOPE_NO_BC`
  （可达、在范围内、无任何 BC 覆盖，仍阻断）、`SCOPE_GAP`（不可达，独立非阻断标签，
  不进 CLASS_3 闭集，直接路由接受角色）、`上轮漏检`、`上游漏检`（核对轮放过的字面
  不符）、`RED_LINE`（真值泄漏、人眼保真等红线，永远阻断，不受 (b)(c) 限制）。
- `docs/roles/review.md`、`.claude/commands/review.md`、`docs/reviews/README.md` 同步。

**T4｜复核 (b)：增量轮、双基线、`上轮漏检` 与消耗性门机检**
- §4.4 新段：第 N+1 轮先读既有轮次。修复触及行 = `git diff <上一复核轮候选>..<候选>`，
  由复核文件每轮 §0 机读行 `round_candidate: <40 位 SHA>` 派生（新增义务，通过轮
  同时写 `passed_candidate`）；全量 diff 相对上一通过候选仍必做，只用于核实声明范围与
  红绿验证。新阻断只来自：修复触及行上的 CLASS_1/2；旧 finding 闭合失败；`RED_LINE`；
  未改动行上标 `上轮漏检` 的 CLASS_1。未改动行上的 `上轮漏检` CLASS_2 不阻断本轮，
  改为阻断下一个消耗性门。
- 机读行**不带 work ID**：`blocks_consuming_gate: <finding-id>` / 同文件后续轮
  `releases_consuming_gate: <finding-id>`。理由：DATA-001 未改动行上的 partition 缺陷
  （复核轮 4 F17 类）烧掉的可能是 DATA-002 的 attempt；过严的代价是一次人工 release，
  过松的代价是一个 attempt。
- 不死锁：复核角色主工作树本就允许写 `docs/current-status.md`，加 blocks 行的提交必须
  同时把受影响的消耗性交接改为 `PAUSED_CONSUMING_GATE_BLOCKED_<finding-id>`；
  `tools/check_docs.py` 对任何提交只核一条不变量：存在未 release 的 blocks 行时，
  Active handoffs 不得有未暂停的 `Consuming=yes` 行。release 只有两条路径：复核角色
  红绿核实修复后写；接受角色按 COORD-008 S2 复判路径改标 `SCOPE_GAP` 后写。
- `tools/check_docs.py`：新增 `check_consuming_gate_blocks`（扫描 `docs/reviews/*.md`，
  排除 `README.md`、`*-prescreen.md` 与围栏代码块内的行，同文件按 finding-id 配对）；
  `tests/test_check_docs.py` 加两条回归（未 release + 未暂停消耗行 → 拒绝；暂停或
  release 后通过；README/prescreen/围栏内的示例不计）。单独提交。
- `AGENTS.md`「共享状态更新」加机读行与机检一条；`docs/roles/review.md`、
  `.claude/commands/review.md`、`docs/reviews/README.md` 同步。

**T5｜复核 (c)：同停点第 2 次 `REWORK_REQUIRED` 后冻结未闭集，轮 3 终局**
- §4.4 新段：未闭 finding 集合冻结，交接受角色逐条裁定「范围内必修」或 `SCOPE_GAP`
  记债。轮 3 检查范围 = 冻结集 + `RED_LINE` + 修复触及行上的 CLASS_1/2（与 (b) 第一项
  一致，不豁免修复自身引入的回归）。轮 3 终局：通过，或回用户。锁的是未改动代码上的
  范围蔓延，不是轮数。复核返工直接回复核，不经核对轮。
- `docs/roles/{acceptance,review}.md`、两条命令同步。

**T6｜归因机械派生 + 「范围外已知缺陷」账本**
- §4.6：`BC-n` → 实现错误；`IN_SCOPE_NO_BC` 与 `SCOPE_GAP` → BC 缺失（同一归属，按阻断性
  分计）；`上轮漏检` → 复核标准；`上游漏检` → 核对轮；`RED_LINE` → 不进四类，单独列出，
  修复仍由实现角色承担。
- `docs/implementation-status.md` 新增节「范围外已知缺陷（SCOPE_GAP 账本）」：按 work ID
  列，每条带来源复核文件与轮次、依据值、裁定日期、状态；由接受角色写；work ID 置
  `DONE` 时随证据一并列出未闭条目。复核文件是原始记录，账本是唯一待办入口。
- `docs/roles/acceptance.md`、`CLAUDE.md` 事实源列表、workflow §6 表同步。

**T7｜三个计数器分开 + 轮次命名**
- §4.2 R6 只数设计轮；§4.3.3 核对轮每停点 ≤ 1；§4.4 复核 `REWORK_REQUIRED` 每停点
  ≤ 2；互不合并。
- §2 新增轮次命名：设计轮 `D<n>`、核对轮 `C<n>@<停点>`、复核轮 `R<n>@<停点>`；提交
  信息主题以 `<work-id> D2` / `C1@<停点>` / `R2@<停点>` 开头；存量「接受轮 N」不回改。
  `AGENTS.md`、`docs/roles/ideation.md` 同步。

**T8｜测试输出纪律**
- §4.3：开发期只跑 focused；全套在停点跑一次，输出写入 `docs/evidence/` 证据文件，
  上下文只回显末尾摘要，不带 `-v`。核对轮不跑测试。复核 = focused 一次 + 每条阻断
  finding 修前红/修后绿一次。
- `CLAUDE.md` 测试命令、`docs/roles/{implementation,review}.md`、三条命令同步。

**T9｜`P1-VLM-DATA-002` 处置（计数追溯生效）**
- 理由：R6 先例（BC-C7-8）按既有轮次追溯；实现期退回已 3 次，超出核对轮上限；BC-14
  含未枚举的全称量词，字面核对做不了，再开一次核对轮只会复制裁判轮。
- BC-SURVEY-1..16 冻结：`NEW_OBLIGATION` 余额 0，`CLARIFY` 仍允许。接受角色先出两条
  `CLARIFY` 行：BC-14 常量闭集 = 候选提交中 `survey_acquisition` 投影的键列表；BC-16
  "全部停放候选" = 候选生成函数在冻结锚点表上的输出集合，回归以该集合的枚举计数为准。
  列表里漏掉的常量或候选不再是 BC-14/16 的"不满足"，而是复核轮的 `IN_SCOPE_NO_BC` 或
  `SCOPE_GAP`。这两行是 `CLARIFY` 机制的首个样本。
- 顺序按提案 §2.3 已接受次序不变：修复 → COORD-005 零-ID 诊断 Play（用户，≤3）→ 保真
  PASS 后 ≤10 首选 plan/scenario ID → §4.3.1 自证并按 BC 编号附证据指针 → 接受角色
  `C1@stageA` 核对表（无退回权；不满足行随候选附给复核）→ `R1@stageA`。接受角色不再
  对修复做窄复查。`implementation-status.md` 已同步到轮 5，不需修正。

**T10｜仓库外同步**
- `~/.codex/prompts/codex.md` 由用户手动同步，替换全文见 §7。

## 3. 不动的红线

COORD-007 §3.1 七条与红线 A/B 全部保留；`RED_LINE` 依据值把真值泄漏与人眼保真明确
排除在 (b)(c) 的范围与轮次限制之外。另保留：PLAY_GOVERNING 开轮资格、`passed_candidate`
机读行、写入白名单与 pre-commit、执行轨道纪律与 Gate-echo、R6 退修上限、COORD-008
S1–S7。本提案不改 `controller/`、`Assets/`、`config/`、`tools/dist_data/` 任何字节。

## 4. 可证伪的验收条件（四个度量，按 work ID 记）

| 度量 | 说明 | 首个受益批次阈值 |
|---|---|---|
| 核对轮退回次数 | 按结论列拆 {不满足, 证据缺失} | ≤ 1 / 停点（机械上限） |
| 复核轮次 | 每停点 | ≤ 3（轮 3 终局） |
| BC 缺失类 finding 条数 | `SCOPE_GAP` 与 `IN_SCOPE_NO_BC` 分计 | 报告即可，无阈值 |
| `ACCEPTED` 后新增 BC 行数 | `CLARIFY` / `NEW_OBLIGATION` 分计；前者多说明 BC 措辞不精确，后者多说明范围没圈准 | `NEW_OBLIGATION` ≤ 2（机械上限） |

"落地前"样本：DATA-002 的 BC 表 6 → 16、实现期退回 3 次、复核轮 0。反向验收沿
COORD-007 §7.6：采纳后 6 个月内若任何 CLASS_1 缺陷进入正式数据且能归因到本提案的
**具体某一条**限制（(b) 的增量范围或 (c) 的轮 3 终局），该条立即回滚。这四个数降下来
之前不动流程基础设施的其他开销。

## 5. 失败模式与风险

| 风险 | 处置 |
|---|---|
| 接受角色把异源候选检查扩大成第二次独立复核 | 只读完整候选 diff、直接关联代码与证据；不跑测试、不改实现、不签复核 verdict、不加 BC 行；退回上限仍为 1 次 |
| (b) 放过未改动行上可达的 CLASS_2 | `RED_LINE` 永远阻断；其余 `上轮漏检` CLASS_2 由 `blocks_consuming_gate` 机检拦在下一个消耗性门前 |
| blocks 行不带 work ID 过严 | 代价是一次人工 release（复核红绿或接受复判），比一个 attempt 便宜 |
| 复核者加 blocks 行时自己的提交被机检拒绝 | 同一提交暂停受影响消耗行；复核角色本就可写状态板 |
| `CLARIFY` 被用来偷渡新义务 | `CLARIFY` 必须引用被解释条款号；归因时 `CLARIFY` 多 = BC 措辞问题，可度量 |
| 文档与 prompt 漂移 | 规则文本与 `.claude/commands/`、`.cursor/commands/`、`docs/roles/` 同一批次；`~/.codex` 由用户同步并在账本记一句 |

## 6. 实施：一个协调批次，两次提交

1. 用户逐字授权；本会话当场代录进 `docs/authorizations.md`。
2. 提交 1：T1–T3、T5–T9 的文本改动 + 状态板（Gate board 加 `COORD-009` 行 + Log 一条；
   不占轨道）+ 本提案。
3. 提交 2：T4 的 `tools/check_docs.py` + `tests/test_check_docs.py`（焦点测试红/绿输出贴进
   提交信息；由下一轮复核逐文件 diff）。
4. 两次提交均 `python3 tools/check_docs.py` 通过，提交信息引用账本条目。
5. 用户同步 `~/.codex/prompts/codex.md`（§7）。
6. 首个受益批次 = `P1-VLM-DATA-002` 阶段 A 的 `C1@stageA` / `R1@stageA`。

## 7. 仓库外同步：`~/.codex/prompts/codex.md` 替换全文

```markdown
---
description: 以接受角色（设计审查/异源候选检查/复判/收尾归因）开工，从状态板领取任务
argument-hint: "[WORK_ID]"
---

你是接受角色（acceptance，历史名 Codex 的审查半边）。实现工作已拆给
Cursor 上的实现角色；本会话不写实现代码。细则见仓库内
`docs/roles/acceptance.md`，与本文冲突时以细则为准。

指定任务（可为空）：$ARGUMENTS

1. 按 `AGENTS.md` 必读顺序读取共享文档。
2. 若上面"指定任务"非空，处理该 work ID；否则从状态板的
   Active handoffs / Immediate next actions 中取当前属于接受角色的条目
   （提案决策、核对轮、CLASS_1/分级争议/用户要求的复判、冻结集裁定、
   收尾关闭或返工归因、授权或 Unity 代录）。
3. 审查时给出 `ACCEPTED` / `REVISION_REQUESTED` / `REJECTED`，理由写进
   提案文件；若触及核心研究主张、阶段边界、主指标、硬件目标或范围
   扩大，先停下来问用户，并把用户关键授权逐字记入
   `docs/authorizations.md`。`REJECTED` 限定为需用户授权的偏离。
4. 接受时把 binding clarifications 写成可逐条核对的条款——实现角色将
   按字面执行，歧义会被退回而不是被解释。BC 表每条一行：编号、条款、
   复核项、证明方式、标签、依据、日期；全称量词必须指向已枚举闭集
   （COORD-009）。同一提案第 2 次 `REVISION_REQUESTED`（设计轮 D2）后，
   不再自行发出第 3 次退修，按 workflow §4.2 上交用户二选一；该计数不
   与核对轮、复核轮合并。涉及真实归档或数据尺度的提案缺少只读真数据
   试跑数字时，不冻结 schema/尺度类 BC（COORD-008 S5）。实现期间的合同
   问题在提案「待裁定」节答复，答复即 BC 表新行并标 `CLARIFY`（引用被
   解释条款号）或 `NEW_OBLIGATION`（只能源于待裁定或复核 `SCOPE_GAP`，
   禁止源于本角色自查代码，每 work ID ≤ 2），不追加轮次章节（S3）。
   实现角色自证后先进入必经核对轮 `C<n>@<停点>` 再交复核（S1；workflow
   §4.3.3）：重读完整候选 diff、BC、证据指针及直接关联代码，检查实现
   忠实性、失败路径和测试是否对准条款；在提案「核对表」写 {满足, 不满足,
   证据缺失} + 自由文本理由，另可列具体「预复核关注项」。不跑测试、不改
   实现、不签独立复核、不新增 BC 行；同一停点至多退回 1 次，第 2 次照交
   复核并附核对表与未决关注项。CLASS_2/3 finding 由复核角色直接交回实现角色；
   本角色只在 CLASS_1、分级争议或用户要求时复判，并只消费最终通过轮的
   verdict（S2）；同停点第 2 次 `REWORK_REQUIRED` 后对冻结的未闭集逐条
   裁定「范围内必修」或 `SCOPE_GAP` 记债（记入 `implementation-status.md`
   「范围外已知缺陷」）。复判写提案「复判」节；`SCOPE_GAP` 改标写账本行
   （状态 `RELEASED_SCOPE_GAP`，即消耗性门 release）；本角色不写
   `docs/reviews/*`。收尾归因从复核依据列机械派生：`BC-n` → 实现
   错误；`IN_SCOPE_NO_BC`/`SCOPE_GAP` → BC 缺失；`上轮漏检` → 复核标准；
   `上游漏检` → 核对轮；`RED_LINE` 单列。
5. 边界：不写实现代码；核对轮仅只读完整候选 diff、直接关联代码与证据，
   不跑测试、不扩大成独立复核、不因读码新增义务；不给任何实现签发独立
   复核；`UNITY_NA` 需复核角色在复核文件中附议；实现会话中的用户授权由
   本角色（或辅助角色）转录进 `docs/authorizations.md`。
6. 收工：基于磁盘最新内容合并更新状态板，运行
   `python3 tools/check_role_writes.py --role acceptance` 和
   `python3 tools/check_docs.py` 并使其通过。
```

### 7.1 2026-09-03 用户修订：实现后异源候选检查

用户在本提案落地后明确要求实现完成后重新经过接受角色，以利用 Codex 接受与
Claude/Cursor 实现的模型异源性发现隐藏问题；随后逐字授权「可以，接受段在你这里，
修改一下就可以」（账本同日修订条目）。本节修订取代 T1 与 §7 中“只核 BC 字面、
不读指针外代码”的旧限制：C 轮仍然必经且每停点至多退回 1 次，但可只读完整候选
diff、直接关联代码与证据并列预复核关注项；仍禁止跑测试、改实现、新增 BC、签发
独立复核或自行给非 BC 问题定 finding 分级/依据值。正常 Review 后只机械收尾，
CLASS_1、分级争议、`SCOPE_GAP`、冻结集终局或用户要求时才复判。

### 7.2 2026-09-03 修订 B：接受角色的复判与 release 落在自己的文件

Codex 修订后指出：接受角色写入白名单不含 `docs/reviews/*`，S2「复判写在复核文件」与
T4「接受角色改标 `SCOPE_GAP` 后写 release 行」在机检层面走不通；配对机检不看顺序（已在
`00bd7b2` 改为按文件顺序开闭）。用户逐字「选择B，另外把你的修改也推送一下」：复判写提案
`## Acceptance rulings（复判）` 节；`SCOPE_GAP` 改标写 `implementation-status.md` 账本行，
状态 `RELEASED_SCOPE_GAP`，`check_docs.py` 视同对应复核文件该 finding 的 release；账本
状态闭集 `OPEN` / `RELEASED_SCOPE_GAP` / `CLOSED`；被账本 release 的 finding-id 不得再次
block。角色写入白名单不动（A 路径未授权）。

### 7.3 2026-09-03 闭集定义补全（与修订 B 同批，单独提交）

复核项 token `行为` / `几何时序` / `边界失败` / `测试覆盖` / `文档一致` 与表下覆盖声明行；
证明方式前缀 `test:` / `artifact:` / `cmd:`（实现角色证据指针同前缀）；标签 `BASE`（接受轮
行）；账本状态 `OPEN` / `RELEASED_SCOPE_GAP` / `CLOSED`（§7.2）；`<停点>` 为提案定义的 ASCII
短名；finding-id 逐字取标题编号，依据列每条 finding 恰一值。原则：每个闭集只在一处定义；
值必须能靠读该列所指工件判定，需要判断的内容进自由文本列；不设 OTHER 逃生值；工具解析
的用 ASCII，只给人读的用中文。存量提案不回改。

## Codex review decision

Decision: NOT_APPLICABLE（用户 2026-09-03 逐字「好的，我授权你开始修改条款…」直接
授权，不经接受轮；账本当日条目；落地提交见 git 历史）
Rationale:
Required revisions:
Accepted design-document changes: 无（不改 `docs/phase1-single-drone-design.md`）
