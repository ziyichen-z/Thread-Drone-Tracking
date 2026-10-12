# COORD-008 — 流程减法：把每步门改成每批门

Status: LANDED（2026-09-02 用户直接授权协调批次，S1–S7 已落地；未经接受轮，
用户选择；账本当日条目）
Author/role: 用户指派的监督会话起草（非构思角色的常规产出）
Created: 2026-09-02
Last updated: 2026-09-02

> 本文是提案，不是授权，也不是已接受设计。它提议修改工作流基础设施
> （`AGENTS.md`、`docs/collaboration-workflow.md`、`docs/roles/`、
> `.claude/commands/`、`.cursor/commands/`、`docs/proposals/README.md`、
> `docs/authorizations.md` 头部格式），按 workflow §7 规则 7 这类修改
> **只能**由用户直接授权的协调批次执行，合规凭据是 `docs/authorizations.md`
> 中的对应条目；本文自身不构成该授权。起草会话未修改 `docs/current-status.md`，
> 也未建立 Active handoff（当前零消耗轨道 0 + 2 已满）。**本文硬预算 ≤ 260 行**。
> 本提案只做减法：不新增工具、不新增角色、不新增档位、不改任何代码。

## 1. 问题与证据

取证口径沿 COORD-007 §3：只有能指出**具体拦截记录**的规则才算救过命。
样本 = `P1-VLM-DATA-001` 2026-08-25 至 09-02 的 31 轮接受、8 轮复核、65 次提交。

**31 轮接受的构成**：停点确认与复查 12 轮；纯消费复核结论、纯文档闭合、
授权转手 7 轮；承载设计裁定 12 轮（含 3 轮提案审查）。即 19 轮无设计内容。

**合同是在实现中才发现的**：接受时冻结 BC-DATA-1…5，实现期间又补 BC-DATA-6…26
共 21 条。族解绑（复核轮 1 F1）、S3 内存耗尽、amodal 对 clipped（BC-DATA-24）、
S4 manifest 尺度（BC-DATA-26）全部是第一次接触真实归档才暴露；合同冻结前没有
任何角色在真数据上做过只读试跑。

**每轮都在变贵**：提案文件 2,852 行，其中约 73% 是逐轮追加的接受记录；实现证据
约 150 KB；复核记录约 1,400 行。每次角色切换的新会话都要重读这些。状态板有
500 行硬顶，这三类文件没有。

**一次性窄授权把工程故障变成用户等待**：S3 内存耗尽（08-28 17:03）到重跑成功
（09-01 23:20）历时 4 天多、十几次角色切换，核心工作是把内存表改成流式存储。

**逐条拦截记录**：

| 规则 | 拦截记录 | 处置 |
|---|---|---|
| 复核一次性 worktree 独立 diff + 重跑 | 全项目 5 条 CLASS_1；DATA-001 22 条 finding 含 2 条 CLASS_1，全部在实现者测试全绿时查出 | 留 |
| 阻断 finding 绑定修复前必失败的回归测试 | F1–F22 全部由此闭合，闭合可验伪 | 留 |
| 授权账本硬语义 | 拦过未授权 Play 与 GO 复用（COORD-007 §3.1） | 留 |
| DR 设计审查、用户 Unity 验证、COORD-005 人眼保真 | 各有拦截记录；离线批次不触发 | 留 |
| 接受角色确认停点（§4.3.1） | 12 轮：8 轮纯确认；2 轮（轮 4/6）是回答实现者自己提出的合同问题；1 轮（轮 22）抓到真缺陷，类型与复核轮 1/6 所抓相同；1 轮（轮 25）改措辞 | 删必经步骤，保留答疑与拒收权 |
| 接受角色逐轮消费复核并亲自 revert 复算 | DATA-001 零改判（仅 C3-1 升一级）；复算与复核角色的修前红/修后绿重复 | 删逐轮消费，只在收尾消费一次 |
| 逐轮追加轮次章节到提案/证据 | 零拦截功能；唯一效果是阅读成本随轮次复利增长 | 删，改记 BC 表与提交信息 |
| 一次性窄授权 | 拦住越权的是账本语义，不是授权的一次性 | 措辞改信封 |

## 2. 提议的修改（S1–S7，逐文件；协调批次按字面执行）

**S1｜停点自证，直接交复核**
- `docs/collaboration-workflow.md` §4.3.1：从「实现角色整理候选与证据，接受
  角色在下列条件全部满足后确认停点成立」到「实现角色逐条自证下列四项条件，
  把自证结果写入交接行，直接把候选交给复核角色。接受角色保留拒收权：可在
  任何时候把候选退回并写明缺口，但确认停点不再是必经步骤。复核角色对自证
  条件不成立的候选给 `REVIEW_BLOCKED`，不开轮、不计复核轮次」。删除「再由
  Acceptance 重验四项条件」类语句。
- `AGENTS.md`「复核强制停点」节同句同步。
- `docs/roles/acceptance.md` 职责删「确认稳定候选停点成立…把候选交给复核角色」；
  `docs/roles/implementation.md`「到稳定候选停点必须停」改为「到停点自证四项
  条件并直接交复核」；`.claude/commands/accept.md` 第 4 条、`implement.md`
  第 4 条、`.cursor/commands/coding.md` 第 4 条同步。
- 省：DATA-001 样本中约 8–10 轮。

**S2｜复核结论直通实现角色**
- `docs/collaboration-workflow.md` §4.4 finding 分级段：从「分级由接受角色独立
  复判并逐条写下同意/升格」到「CLASS_2/3 finding 由复核角色直接交回实现角色；
  接受角色只在 (a) CLASS_1、(b) 复核或实现角色提出分级争议、(c) 用户要求时
  复判，复判写在复核文件对应轮次下，不另开轮」。CLASS_3 补丁由拥有该文件
  写权限的角色在下一次提交应用，不开轮。
- §4.4 阻断 finding 闭合四条件：删条件 (2)「接受角色亲自复算」，改为「复核
  角色在下一轮以修前红/修后绿核实」；(1)(3)(4) 原文保留。
- §4.6：接受角色只在最终通过轮消费 verdict 并关闭或返工归因；中间轮不消费。
- `docs/roles/acceptance.md` 删「对复核 finding 独立复判分级」与「阻断 finding
  闭合时亲自复算」两条，改为「CLASS_1 或争议时复判；收尾消费通过轮」；
  `docs/roles/review.md` 加一句「CLASS_2/3 直接交回实现角色」；
  `.claude/commands/accept.md` 第 4 条、`review.md` 第 5 条同步。
- 省：约 5–7 轮。

**S3｜接受记录不再逐轮追加到提案**
- `docs/collaboration-workflow.md` §4.2 加段：「接受后的提案文件只承载已接受
  设计与 BC 表（每条一行：编号、条款、依据、日期）。实现期间的合同问题由
  实现角色写在提案末尾『待裁定』节，接受角色的答复直接成为 BC 表新行；
  不追加轮次章节，轮次叙述进提交信息。提案文件超过 600 行即是信号：内容
  放错了地方」。§6 表 `docs/proposals/` 行同步；`docs/evidence/` 加一行
  「只保留当前状态，机器生成优先，不逐轮追加」。
- 存量不回改：`docs/proposals/P1-VLM-DATA-001-grounding-data-foundation.md`
  顶部加一段 banner「§16–§43 是 COORD-008 之前流程下的逐轮记录，保留为
  历史，不作后续批次的流程范例」。不搬、不删、不转录 BC（避免转录错误）。
- 省：每轮的阅读成本不再随轮次增长。

**S4｜授权改信封**
- `docs/authorizations.md` 头部格式加可选字段：`- 信封：阶段 = …；尝试次数
  上限 = …；GPU·h 上限 = …；API 次数上限 = …；Unity/Play = 否`。规则句：
  「信封内的工程性重试与 supersession 不需要新授权，由接受角色在 BC 表记一行
  归因；缺项视为 0；任何越界回到用户」。
- `AGENTS.md`「共享状态更新」的授权句同步一句。
- 省：内存耗尽一类故障从 4 天变同日。

**S5｜真数据试跑先于合同冻结（本提案唯一加法，可单独不采）**
- `docs/collaboration-workflow.md` §4.1 加第 8 要素：「涉及真实归档或数据尺度
  的合同，附只读试跑数字：行数、单条体积、内存投影、绑定率」；§4.2 加句
  「缺该节时接受角色不得冻结 schema 或尺度类 BC」。
- `docs/proposals/README.md` 模板加节 `## Real-data dry run`。
- 依据：§1 列出的四次最贵返工全部可由一次只读试跑提前暴露。

**S6｜CLASS_3 闭集补一项**
- `docs/collaboration-workflow.md` §4.4 CLASS_3 闭集加「证据叙述中的计数或枚举，
  若不驱动任何工具或操作员动作」；判据句「操作员或工具的行为会不会因这段
  文字而不同」原文不动。F15 类缺陷由此不再开轮。

**S7｜仓库外同步**
- `~/.codex/prompts/codex.md` 由用户手动同步 S1/S2 措辞。**顺带修正**：该文件
  第 4 条至今仍要求「运行 `check_role_writes.py --role implementation --base`」，
  这是 COORD-007 R2 于 2026-08-12 已删除的条件 5（BC-C7-4 约定由用户同步，
  实测未同步）。

## 3. 不动的红线

COORD-007 §3.1 七条与红线 A/B 全部保留：复核一次性 worktree 与五路径零修改、
回归测试闭合条件 (1)(3)(4)、真值隔离与反调参、账本硬语义、DR 审查、Unity
验证、`UNITY_NA` 复核附议。另保留：PLAY_GOVERNING 开轮资格、`passed_candidate`
机读行、写入白名单与 pre-commit、执行轨道纪律与 Gate-echo、退修上限、
CLAUDE.md 全文。本提案不改任何 `tools/`、`tests/`、`controller/`、`Assets/`、
`config/` 字节，PLAY_GOVERNING diff 为空，落地件不需要复核轮。

## 4. 可证伪的验收条件

1. 落地后第一个离线 work item 从 `ACCEPTED` 到复核通过：接受轮 ≤ 4、复核轮 ≤ 3
   （基线：DATA-001 31 / 8）。
2. 该 work item 关闭时提案文件 ≤ 600 行（基线：2,852）。
3. 该 work item 中零「接受角色停点确认」轮、零「纯文档 finding 开接受轮」。
4. 该 work item 的用户介入次数 ≤ 2（开批信封 + 收尾）（基线：5）。
5. **反向验收（沿 COORD-007 §7.6）**：采纳后 6 个月内若任何 CLASS_1 缺陷进入
   正式数据且能归因到本提案删除的**具体某一条**规则，该条立即回滚；归因不到
   删除项的不作为本提案的失败证据。

## 5. 失败模式与风险

| 风险 | 处置 |
|---|---|
| 实现者把半成品交给最强池复核 | `REVIEW_BLOCKED` 已是现有 verdict，不开轮不计次；DATA-001 候选 4 自查抓到 4 条阻断说明自证可行 |
| 接受角色失去中途抓缺陷的机会（轮 22 类） | 拒收权保留；该类缺陷属复核轮 1/6 已证明会抓的生产路径 fail-closed 类型 |
| 新会话模仿旧记录继续开轮 | S3 banner + 新 work item 从零开始 + 三处角色 prompt 同批改 |
| 合同问题无处问 | S3「待裁定」节即问答通道，答复即 BC 行 |
| 信封被读成放开范围 | 字段逐项显式、缺项为 0、越界回用户 |
| 文档与 prompt 漂移（COORD-007 R5 教训） | 规则文本与 `.claude/commands/`、`.cursor/commands/`、`docs/roles/` 必须同一提交；`~/.codex` 由用户同步并在账本记一句 |

## 6. 实施：一个协调批次，半天

1. 用户逐字授权；本会话（用户直接指挥的协调会话）当场代录进
   `docs/authorizations.md`，写明采纳 S1–S7 中哪些项。
2. 按 §2 逐文件应用文本改动；改动文件清单：`docs/collaboration-workflow.md`、
   `AGENTS.md`、`docs/roles/{acceptance,implementation,review}.md`、
   `.claude/commands/{accept,implement,review}.md`、`.cursor/commands/coding.md`、
   `docs/proposals/README.md`、`docs/authorizations.md`（头部格式）、
   `docs/proposals/P1-VLM-DATA-001-grounding-data-foundation.md`（banner）、
   `docs/current-status.md`（Gate board 加 `COORD-008` 行 + Log 一条；不占轨道）。
3. `python3 tools/check_docs.py` 通过；一次提交，提交信息引用账本条目。
4. 用户同步 `~/.codex/prompts/codex.md`（S7）。
5. 首个受益批次 = 下一份离线提案（生成器批次或 C1）。

## 7. 待用户决定

1. 是否采纳 S5（唯一加法）。建议：采纳。
2. 是否采纳 S4 信封。它改变的是你的授权粒度，不是角色权限。建议：采纳。
3. 是否要求接受角色先审一轮本提案。建议：不要，直接授权；本提案不改代码，
   落地件由 `check_docs.py` 与下一批次的验收条件（§4）检验。
4. 授权原话建议（逐字入账）：「授权 COORD-008 协调批次，按提案 §2 落地
   S1–S7，不改代码，不涉及 Play/ID/API/GPU」；不采 S5 或 S4 时在句中删去。

## Codex review decision

Decision: NOT_APPLICABLE（用户 2026-09-02 逐字「采纳三个建议」选择直接授权，
不经接受轮；账本当日条目；落地提交见 git 历史）
Rationale:
Required revisions:
Accepted design-document changes: 无（不改 `docs/phase1-single-drone-design.md`）
