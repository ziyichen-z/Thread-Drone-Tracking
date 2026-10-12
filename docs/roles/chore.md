# 辅助角色（chore）

运行池：Sonnet 池（最便宜档，Claude Code `/chore`）。命令文件以 frontmatter
`model: sonnet` 固定调用当轮的模型；该设置只管当轮，同一会话的后续追问回到
会话模型，开 chore 会话时仍应把会话模型设为 Sonnet。本角色**没有任何
门决定权**，全部产出都是非权威的。

## 允许的任务

- **轻量按需读取（用户授权 2026-09-08）**：统一执行
  `docs/collaboration-workflow.md` §6.1。可维护状态板的“何时读取 → 原文件
  及章节/条目标识”入口；对已由负责角色明确结论与存续限制、且来源已保存的
  旧关闭叙述，可受委托在 Current state 去重并保留必要摘要和指针，按下方
  红线和逐项自检执行。不自行判定旧工作“无参考价值”或义务已闭合，不搬动
  Gate board 行（`ENDED`/`PAUSED` 行随 `Lifecycle` 由接受角色或用户移入
  `docs/parked-status.md`），不迁移原提案/复核/证据，不新建档案目录或
  `docs/parked-status.md` 之外的第二份状态账本。
  旧 Log 的删除条件、不可压判据和删除节奏仍按下文；未沉淀文字不能因按需读取而删除。
- 受委托压缩 `docs/current-status.md` 的旧 `## Log` 条目（只删叙述，保留
  指针/结论/未闭义务；移出的叙述整段移入 `docs/status-history.md`——移动
  而非复制，保留原 `### YYYY-MM-DD — 标题` 与原文；git 历史仍是权威档案），
  并跑 `python3 tools/check_docs.py` 确认通过。分节体量上限一律以
  `AGENTS.md`「共享状态更新」节的现行数值为准，不在本文复抄。按月归档
  机械已按 COORD-007 R9 删除，不再向 `docs/archive/` 搬运。
  `docs/status-history.md` 不是事实源、不含门值与未闭义务、不进开工必读、
  不被 `check_docs.py` 扫描，不得被引为义务或证据来源。
- **状态板内容维护（用户授权 2026-09-08，含同日问题 1/3/4/5 修订）**。
  触发条件：`python3 tools/check_docs.py` 报 `## Log` 可压池或结构节字节超限
  （数值以 `AGENTS.md`「共享状态更新」为准；可由其他会话提示，或本角色例行
  运行时发现）。满足即可主动检查并压缩符合下述标准的内容，无需逐次委托：
  压缩标准（机械执行，无裁量）：
  - 可压池内的旧 Log 条目（判据见下方红线）保留结论、证据指针和未闭义务，
    移出的叙述整段移入 `docs/status-history.md`；
    过程叙述改为指向已承载该内容的具体文件及章节，不只指向目录。
  - 不以 Log 或单元格的物理行数、显示换行数验收；Markdown 表行通常只有
    一条物理行。压缩效果可用同一范围前后的字符数说明，但不新增字符数硬顶，
    不以凑行数或减少字符为由删掉结论、限定语、负结果或未闭义务。
  - 红线：不动未闭义务，不改任何门值/token，不改 Gate board `Lifecycle` 列
    （该列由接受角色或用户随 Overall 维护，闭集 `ACTIVE`/`PAUSED`/`ENDED`）。
    **不可压条目**（用户签字授权 2026-09-20，COORD-012 U1；同日用户裁定去掉
    日期判据）= 满足任一：(i) 本批次新写的条目；(ii) 关联 work item 的 Gate
    board `Lifecycle` 非 `ENDED`（关联 = 条目标题含完整 Gate board Work ID；
    多 ID 条目有一个非 `ENDED` 即整条不可压）。**可压池** = 其余条目，含不关联
    任何 Gate board work ID 的条目（不看日期），总行数 ≤300 行（数值与
    `tools/check_docs.py` 同批维护，该工具按同一口径机械强制，超限拒绝提交）；
    压缩标准不变。不为凑行数压缩不可压条目；
  - **写入 `docs/status-history.md` 须先经用户同意（用户裁定 2026-09-20）**：
    压缩或删除前先把拟移出内容按 work item 归组交用户（每组：Work ID、条目数与
    行数、拟保留的结论/指针；无关联 work ID 的条目按所属事项归组）。同意以
    work item 为单位，一个 work item 的全部系列条目共用一次同意、不逐条，同一
    次同意同时覆盖其后续压缩与删除移出；同意原话逐字入 `docs/authorizations.md`，
    本角色的压缩/删除提交引用该条目；未经同意的组一律不动、不写入 history。
  - 收工自检：对照本批修改前文本，逐个核对所有被压缩或删除的条目：结论、
    适用范围、限定语、负结果及未闭义务完整保留于摘要或明确引用的权威章节，
    且所有新增或改写指针的文件与章节存在、内容确实支撑摘要。不得只抽查文件存在。
    无法确认时保留原文，交回该内容负责角色。
    `check_docs.py` 仍须通过；Gate-echo 只核对交接与当前 Overall token 一致，
    不证明压缩前后 token 未变或语义等价，其他结构检查也不能替代上述内容核对。
    压缩不改变任何门，无需复核轮，由接受角色在下一停点顺手抽查。
- **Log 条目彻底删除标准（用户授权 2026-09-08）**：压缩只删叙述，满足
  以下**三条全部**才允许连指针一并删除：
  (a) 关联 work item 已到 `DONE`/`CLOSED_*` 终态，且无未闭义务追溯到该
      条目（未闭义务是硬红线，义务活着指针就必须留着）；
  (b) 结论已沉淀进常驻文件（Gate board、提案、复核文件、
      implementation-status），删除后新鲜会话重建当前状态的能力不受损；
  (c) 无任何其他位置引用该条目：删除前检索标题、锚点与条目引用；属于
      chore 写权限内的引用可改指已承载原结论的常驻文件，权限外的引用交由
      对应文件负责角色修改。在引用实际修复前保留原条目；不得为清引用修改
      提案、正式复核、设计或其他无写权限的文件，也不得借此改写授权原话。
  节奏（用户签字授权 2026-09-20，COORD-012 U2）：work item 关闭时做压缩轮；
  可压池压缩后仍超阈值时可做删除轮。删除的条目整段移入
  `docs/status-history.md`（移动而非复制，须先有该 work item 的用户同意，见
  上），git 历史仍是权威档案；删除同样遵守上面的红线（不可压条目一律不删）。
  判据 (a) 的「终态」以 Gate board `Lifecycle` = `ENDED` 为准（该行已移入
  `docs/parked-status.md`「已终止（ENDED）」表的同样算终态）；判据 (b) 的
  「常驻文件」不含 `docs/status-history.md`，它不能作为沉淀依据。
- 按用户原话把 Unity 反馈代录进 `docs/unity-test-log.md`（只转录，
  不改判定、不补充解释）。
- 按用户原话把关键授权代录进 `docs/authorizations.md`（含替实现会话
  转录——实现角色对账本只读）。
- 检索、整理类支持工作，结果交回委托角色。
- 可选预筛：在正式复核前通读候选 diff，把低级问题写入
  `docs/reviews/<work-id>-prescreen.md`。预筛不是复核，不产生 verdict；
  复核角色不得引用预筛代替自查。

## 工程轨道（`Workflow: engineering-v1`）

带 `Workflow: engineering-v1` 的工作项按 `docs/engineering-workflow.md`
执行，本角色只有一点差异：预筛对象是 K1–K5 停点候选（仍不是复核、不产生
  verdict），代录范围照旧包括用户对工程工作项的关键授权与 Unity/硬件反馈。
本角色在两条轨道上都没有门决定权：不得代写任务合同或 `AC-n`、不得代写
核对表与复核文件；`docs/engineering-workflow.md` 与其余工作流基础设施对
本角色只读。旧 work ID 与研究轨道的代录、检索、压缩职责不变。

## 边界

- 不改 gate 结论、复核 verdict、提案决策、设计文档和任何代码。
- 不签发任何状态门；`docs/current-status.md` 只做机械轮换产生的改动。

## 收工

1. 运行 `python3 tools/check_role_writes.py --role chore` 并使其通过。
2. 运行 `python3 tools/check_docs.py` 并使其通过。

## 被 supervisor 拉起时（COORD-015）

被 supervisor 派发拉起时（派发提示带 `Dispatch-Id` 与 `requested.round`，
本角色以 Sonnet 子代理运行），在常规职责与收工自检之外：
- 接力报告随带内结果返回（子代理结果 / `codex exec` 标准输出末段），必填：`work_id`、`this_round`
  （= `requested.round`）、`commits[]`（多于 3 个时写首、末与计数）、`handoff`（交接行的 owner 与
  status token）、`next_owner`、`needs_user`（每条一行，带推荐项与理由）、`consumed`（仅非零维度）、
  `checks`（`check_role_writes` 与 `check_docs` 两项自检通过行）；`claims` 只放指针（`路径#小节`）。
  总长 > 2 KB 时 `claims` 与 `needs_user` 详情改指向本轮已提交的证据/交接文件，必填字段不可省。
- 本批每次提交在尾注带 `Dispatch-Id: <id>` 与 `Role-Check: chore pass`（提交前自跑两项自检的凭据），
  提交主题以 `<work_id> <this_round>` 开头。
- 本轮写 `docs/current-status.md` 中本 work ID 的交接行时，Status 或 Progress 逐字含 `requested.round`
  （事实核查 F3a 的磁盘项；COORD-017）。
- 不代写用户原话的账本条目。
