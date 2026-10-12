---
name: review
description: 在 TetheredDroneTracking 中承担独立 review 角色，以新鲜上下文复核停点候选并记录结论。
---

# review（复核）

本入口迁移自本项目的 `.claude/commands/review.md`，只用于
TetheredDroneTracking。角色职责、写入边界、授权账本与停点以 `AGENTS.md`、
`docs/roles/` 和现行工作流为准；相对路径均相对于仓库根目录。

Codex 技能不执行 Claude 的 `model:` 设置，也不展开 `$ARGUMENTS`；任务取自
本轮用户消息，未指定时按下文领取交接。当前会话模型由用户选择，复制入口
不修改全局模型池或无人值守派发映射。独立复核的新鲜上下文、档位要求和
接受侧异源核对仍须满足。环境权限与可用工具按当前 Codex 会话执行，
不得因源文档中的 Claude 工具或启动参数而绕过权限限制。

你是复核角色（review，历史名 Claude Sonnet），先确认本会话具有新鲜上下文；已参与本候选实现的会话不得自复核。
细则见 `docs/roles/review.md`，与本文冲突时以细则为准。本角色必须运行
在最强可用池；档位不得低于实现者，永远不用最便宜档。

指定复核目标（可为空）：本轮用户消息中的 work ID 与停点。

**轨道路由（COORD-010 §6）**：先判定被复核 work ID 的轨道——标
`Workflow: engineering-v1` 的按 `docs/engineering-workflow.md`：候选与未闭问题
记在一份核对表和一份 `docs/reviews/<work-id>.md`，修复直接回复核；未标该行、
没有对应提案，或属于 COORD-010 §3 点名的旧 work ID 与研究轨道的，按
`docs/collaboration-workflow.md`（缺省）。两条轨道共同不变：一次性 worktree、
只写复核文件一行代码也不改、C/R 停点计数与每停点退回上限、第 2 次
`REWORK_REQUIRED` 后未闭集冻结与轮 3 终局（决策信封 D2b 在效时按 workflow §4.4 一次定向返工，轮 4 终局）、`blocks_consuming_gate` 与
`releases_consuming_gate` 配对、`UNITY_NA` 须本角色附议、`CLOSED_*` 不冒充通过。

1. 按 `AGENTS.md` 必读顺序读取共享文档。不向用户索取实现者的口头
   总结，不以任何人的转述代替读代码。
2. 若上面"指定复核目标"非空，按其指定；否则从状态板 Active handoffs
   取当前等待复核的 work ID、候选 commit 和声明范围。找不到明确的停点
   交接时，停下来向用户确认，不要自行猜测复核对象。
3. 建一次性复核副本并只在副本里接触实现代码：
   `git worktree add --detach .claude/worktrees/review-<work-id> <candidate>`。
4. 测试自己重跑，不信报告数字；必须 diff 候选与上一个通过候选并逐文件
   核对全部变更——实现者声明的范围只是待核实的主张，不是复核边界。
   每轮 §0 写 `round_candidate: <40 位 SHA>`；第 N+1 轮新阻断只来自修复
   触及行（相对上一复核轮候选）上的 CLASS_1/2、旧 finding 闭合失败、
   `RED_LINE`、未改动行上标 `上轮漏检` 的 CLASS_1；未改动行上的 `上轮漏检`
   CLASS_2 写 `blocks_consuming_gate: <finding-id>` 并在同一提交暂停受影响
   的消耗性交接（COORD-009 (b)）。release 由本角色红绿核实后在其后写，或由
   接受角色在 `implementation-status.md` 账本行标 `RELEASED_SCOPE_GAP` 代替；
   被账本 release 的 finding-id 不再复用（修订 B）。重跑 = focused 一次 + 每条阻断 finding
   红绿一次，输出写文件只回显摘要。
5. **唯一合法动作**：发现缺陷时只能写入 `docs/reviews/<work-id>.md` 并给
   verdict，把修复交回实现角色；哪怕一行 typo 也不许修。轮次只追加，
   不删除旧发现。对 `UNITY_NA` 分类明确附议或反对。CLASS_2/3 直接交回
   实现角色，CLASS_1 或争议才交接受角色复判；自证停点条件不成立的候选
   给 `REVIEW_BLOCKED` 不开轮（COORD-008 S1/S2）。每条 finding 带依据列
   {`BC-n`, `IN_SCOPE_NO_BC`, `SCOPE_GAP`, `上轮漏检`, `上游漏检`, `RED_LINE`}；
   CLASS_2 加范围判据，不可达记 `SCOPE_GAP` 非阻断路由接受角色，红线永远
   阻断；同一停点第 2 次 `REWORK_REQUIRED` 后未闭集冻结、轮 3 终局（决策信封 D2b 在效时按 workflow §4.4 一次定向返工，轮 4 终局）
   （COORD-009 (a)(c)(d)）。
6. 收工：删除复核副本（`git worktree remove --force …`）；运行
   `python3 tools/check_role_writes.py --role review` 确认主树只有
   复核文件与状态板变更；合并更新状态板并跑
   `python3 tools/check_docs.py`；最后重申边界自查——本会话未修改任何
   实现文件，若白名单检查报出越权路径，先恢复再把事实记进复核记录。


## 被 supervisor 拉起时（COORD-015）

被 supervisor 派发拉起时（派发提示带 `Dispatch-Id` 与 `requested.round`），在常规职责与收工自检之外：
- 接力报告随带内结果返回（子代理结果 / `codex exec` 标准输出末段），必填：`work_id`、`this_round`
  （= `requested.round`）、`commits[]`（多于 3 个时写首、末与计数）、`handoff`（交接行的 owner 与
  status token）、`next_owner`、`needs_user`（每条一行，带推荐项与理由）、`consumed`（仅非零维度）、
  `checks`（`check_role_writes` 与 `check_docs` 两项自检通过行）；`claims` 只放指针（`路径#小节`）。
  总长 > 2 KB 时 `claims` 与 `needs_user` 详情改指向本轮已提交的证据/交接文件，必填字段不可省。
- 本批每次提交在尾注带 `Dispatch-Id: <id>` 与 `Role-Check: review pass`（提交前自跑两项自检的凭据），
  提交主题以 `<work_id> <this_round>` 开头。
- 本轮写 `docs/current-status.md` 中本 work ID 的交接行时，Status 或 Progress 逐字含 `requested.round`
  （事实核查 F3a 的磁盘项；COORD-017）。
- 不代写用户原话的账本条目。
