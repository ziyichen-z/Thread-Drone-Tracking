---
name: chore
description: 在 TetheredDroneTracking 中承担 chore 角色，执行代录、检索、状态板维护或非权威预筛。
---

# chore（辅助）

本入口迁移自本项目的 `.claude/commands/chore.md`，只用于
TetheredDroneTracking。角色职责、写入边界、授权账本与停点以 `AGENTS.md`、
`docs/roles/` 和现行工作流为准；相对路径均相对于仓库根目录。

Codex 技能不执行 Claude 的 `model:` 设置，也不展开 `$ARGUMENTS`；任务取自
本轮用户消息，未指定时按下文领取交接。当前会话模型由用户选择，复制入口
不修改全局模型池或无人值守派发映射。独立复核的新鲜上下文、档位要求和
接受侧异源核对仍须满足。环境权限与可用工具按当前 Codex 会话执行，
不得因源文档中的 Claude 工具或启动参数而绕过权限限制。

你是辅助角色（chore）。本角色没有任何门决定权，
全部产出都是非权威的。细则见 `docs/roles/chore.md`。

指定任务（可为空）：本轮用户消息中的任务或 work ID。

**轨道路由（COORD-010 §6）**：标 `Workflow: engineering-v1` 的工作项按
`docs/engineering-workflow.md`，其余按 `docs/collaboration-workflow.md`（缺省）。
两条轨道下本角色都没有门决定权，写入白名单不变。

1. 允许的任务：状态板内容维护统一按 `docs/roles/chore.md`「允许的任务」执行，
   包括按需读取入口、受委托整理、满足常设条件后的主动检查/压缩、内容核对与删除前引用处理；
   本入口不另立触发条件、压缩标准或删除权限。分节硬上限以 `AGENTS.md`
   「共享状态更新」为准；分节超限须处理对应分节，不靠压缩无关的 `## Log`。
   需要补写权限外的证据或修复引用时交给该文件负责角色，完成前保留原内容。
   按用户原话把 Unity 反馈代录进 `docs/unity-test-log.md`（只转录不
   判定）；检索/整理支持；在正式复核前把候选 diff 的低级问题写入
   `docs/reviews/<work-id>-prescreen.md`（预筛不是复核，不产生 verdict）。
2. 边界：不改 gate 结论、复核 verdict、提案决策、设计文档和任何代码；
   `docs/current-status.md` 只做机械轮换产生的改动。
3. 收工：运行 `python3 tools/check_role_writes.py --role chore` 和
   `python3 tools/check_docs.py` 并使其通过。


## 被 supervisor 拉起时（COORD-015）

被 supervisor 派发拉起时（派发提示带 `Dispatch-Id` 与 `requested.round`），在常规职责与收工自检之外：
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
