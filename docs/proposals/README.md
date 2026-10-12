# 提案模板（双轨）

构思角色（ideation，历史名 Claude Fable）为每个工作项在本目录创建一个文件，
文件名用稳定 work ID，例如 `P1-TRACK-001-first-sot-baseline.md`；纯协作/流程
事项用 `COORD-NNN`。任何角色都不得自行把提案标记为 `ACCEPTED`。

**轨道路由（COORD-010 §6）**：本目录有两套模板，按提案头部的 `Workflow:` 字段
路由，缺省仍走旧流程：

- **研究轨道（缺省）**：不写 `Workflow:` 字段的提案，以及所有既有 work ID，
  一律沿用下面的研究轨道模板与 BC 表规则，不因换轨作废。
- **工程轨道**：头部逐字写 `Workflow: engineering-v1` 的新工程提案，用文末的
  短任务合同模板。工程轨道规则的权威正文是 `docs/engineering-workflow.md`，
  本 README 只给模板与指针，冲突时以该文件为准。

两轨共同规则：同一 work ID 贯穿提案、状态板、复核、Unity 记录与里程碑证据；
接受后只追加澄清/决策行，不追加轮次章节；600 行信号（COORD-008 S3）与设计轮
退修上限（同一提案第 2 次 `REVISION_REQUESTED` 后上交用户；决策信封 D1 在效、
残留数非递增且本提案已代拍少于 3 次时改交 supervisor 仅代选 (a)，workflow §4.2/COORD-015 §5.1；COORD-016 §2.1/BC-1）对
两轨同样有效。`COORD-*` 协调提案的作者缺省为 supervisor（COORD-015 §2.1/§6，
5 天窗口节流）；supervisor 未启用前仍由用户直接指挥的协调会话起草。

## 研究轨道模板（缺省）

复制下面的模板；决策由接受角色写，构思角色不自行标记接受。

```markdown
# <work-id> — <title>

Status: PROPOSED
Author/role: 构思角色 / design ideation
Created:
Last updated:

## Problem and research value

## Proposed behavior

## Inputs, outputs, and affected interfaces

## Compatibility with the current v0.3 design

## Acceptance criteria

## Baselines and ablations

## Failure modes and resource risks

## Real-data dry run

## Suggested implementation scope

## Open questions

## Binding clarifications (BC table)

复核项覆盖：行为 ✓ | 几何时序 ✓ | 边界失败 ✓ | 测试覆盖 ✓ | 文档一致 ✓

## Pending rulings（待裁定）

## Contract conformance（核对表）

## Acceptance rulings（复判）

## Codex review decision

Decision: PENDING
Rationale:
Required revisions:
Accepted design-document changes:
```

Allowed decision values are `ACCEPTED`, `REVISION_REQUESTED`, and `REJECTED`.
Accepted behavior must be reflected in the canonical design before or together
with implementation.

`Real-data dry run` 在涉及真实归档或数据尺度的合同时必填（workflow §4.1
第 8 要素，COORD-008 S5）。接受后提案只追加 BC 表行与「待裁定」问答，不
追加轮次章节；超过 600 行即是内容放错地方的信号（COORD-008 S3）。

BC 表列（COORD-009）：`编号 | 条款 | 复核项 | 证明方式 | 标签 | 依据 | 日期`。
复核项取 `行为` / `几何时序` / `边界失败` / `测试覆盖` / `文档一致`（多值用 `/`），表下
一行 `复核项覆盖：` 逐项写 ✓ 或 `N/A（理由）`；证明方式写 `test:` / `artifact:` / `cmd:`
前缀之一加具名对象；标签：接受轮的行 `BASE`，`ACCEPTED` 后新增行 `CLARIFY`
（引用被解释条款号）或 `NEW_OBLIGATION`（每 work ID ≤ 2）。`Contract
conformance（核对表）` 节由接受角色在实现后必经的异源候选核对轮写，只保留
最新一版：`编号 | 结论 {满足, 不满足, 证据缺失} | 理由`；理由为自由文本，
必须指向具体 diff/证据或明确缺项，非 BC 问题另列「预复核关注项」
`Acceptance rulings（复判）` 节：接受角色对 CLASS_1/分级争议/用户要求/冻结集的复判，
每条一行（复核文件/轮次/finding、裁定、日期）；接受角色不写 `docs/reviews/*`，`SCOPE_GAP`
改标走 `implementation-status.md` 账本行（COORD-009 修订 B）
（workflow §4.3.3）。
## 工程轨道模板（`Workflow: engineering-v1`）

新工程工作项写一份短任务合同：目的、范围、接口、验收项、预算、限制六件事写
清楚即可，不要求七列 BC 表，也没有 `NEW_OBLIGATION` 配额。接口或验收项的实质
变化必须先记录并由接受角色确认，不能边实现边解释扩大范围。

```markdown
# <work-id> — <title>

Status: PROPOSED
Workflow: engineering-v1
Author/role:
Created:
Last updated:

## 1. 目的与价值

## 2. 范围与不做的事

## 3. 接口与数据契约

## 4. 验收项（AC 表）

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 |  |  |  |  |

## 5. 预算信封

| 项目 | 上限 |
|---|---|
| Consuming | yes / no |
| scenario/session/run ID |  |
| Unity Play |  |
| 模型 API 次数 |  |
| 训练 GPU·h |  |
| 下载/发布 | 否 |
| 停点全套（每候选 1 次、至多 N 个候选）的本机模型加载/回放 |  |

## 6. 限制与不承诺

## 7. 必经停点

## 8. 只读试读与试运行数字

## Contract conformance（核对表）

## 决策记录
```

AC 编号一经接受即稳定：不重排、不复用、不改写旧编号。每条 AC 附证据指针，前缀
取 `test:` / `artifact:` / `cmd:` 之一加具名对象（与研究轨道证明方式同口径）。接受
后新增或改写 AC，必须在「决策记录」单独一行写明编号、原因和确认人。

「必经停点」逐条点名本工作项触发的 K1–K5（K1 帧/控制协议及坐标时间语义；K2 安全
约束/控制命令；K3 模型决策、目标身份/重播种；K4 数据划分/标签或对外指标；K5 对外
发布候选），短名逐字用 `K1`…`K5`，交接行、核对轮 `C<n>@K<n>` 与复核轮 `R<n>@K<n>`
复用同一短名。相互关联的触发可以合并成一个候选，但不得以「工程轨道」为由跳过任一
停点的接受侧只读核对与独立复核。

「预算信封」缺项视为 0；信封内的工程性重试与 supersession 不需要新授权，但接受角色
须在「决策记录」记一行归因（工程轨道无 BC 表，`AGENTS.md` 的「在 BC 表记一行归因」
在本轨道落到决策记录）；**任何越界回到用户**（COORD-008 S4）。账本没有的授权视为
未发生，信封不得由实现或复核角色自行扩写。执行轨道纪律不变：Active handoffs 每路（`fast`/`vlm`）至多
1 条消耗性 + 2 条零消耗活跃交接，Gate-echo 照旧，共享槽位互斥按现状保留（用户
2026-09-07 点名维持现状）。涉及板端/硬件的可行性
探测必须独立立项，单列设备与额度，不并入软件任务的信封。

「预算信封」须为停点全套留出额度（COORD-017）：停点全套会加载本机模型或回放数据时，
按「每个候选 1 次、至多 N 个候选」写明执行机器、模型加载与回放次数上限（先在该机器
只读核对全套会加载什么），随信封一次签发；不写即按缺项为 0，停点全套无法运行
（`docs/engineering-workflow.md` §6）。

「只读试读与试运行数字」在合同涉及真实归档、数据尺度或资源上限时必填：本次实际
读到的行数、单条体积、内存投影、绑定率等（COORD-008 S5 同口径）；缺这些数字时接受
角色不得冻结 schema、数据规模或资源上限。

`Contract conformance（核对表）` 由接受角色在实现后必经的异源候选核对轮写，只保留
最新一版，列为 `编号 | 结论 {满足, 不满足, 证据缺失} | 理由`，编号取 `AC-n`；每停点
至多退回 1 次。`决策记录` 每条一行（日期、轮次、结论、理由指针），允许的结论值与
研究轨道一致：`ACCEPTED`、`REVISION_REQUESTED`、`REJECTED`。
