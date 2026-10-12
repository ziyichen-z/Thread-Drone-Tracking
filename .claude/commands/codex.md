---
description: 已拆分：设计审查用 /accept（主地 Codex CLI），实现归 Claude Opus /implement
---

原 Codex 角色已拆分为两个角色：

- **接受**（设计审查、必经核对轮 `C<n>@<停点>`、关闭/返工归因）：主运行地
  Codex CLI（`/prompts:codex`），Claude Code 备用命令 `/accept`，可被
  supervisor 经 `codex exec` 无人值守拉起（COORD-015），细则
  `docs/roles/acceptance.md`。仓库外的 `~/.codex/prompts/codex.md` 只作为读取
  `AGENTS.md` 与工作流文件的入口，其正文不携带 COORD-010 之后的规则，冲突时
  不得覆盖仓库规则（COORD-010 §7）。
- **实现**（代码与自动测试）：主运行地 Claude Opus `/implement`（COORD-015
  池重分配；Cursor `/coding` 保留为遗留手动入口，U8），细则
  `docs/roles/implementation.md`。

**轨道路由（COORD-010 §6）**：无论从哪个入口开工，先判定本 work ID 的轨道——
标 `Workflow: engineering-v1` 的走 `docs/engineering-workflow.md`，其余走
`docs/collaboration-workflow.md`（缺省）。本文件是历史别名，不承载任何角色规则
或步骤，一律以入口文件与 `docs/roles/` 细则为准。

**不要在本会话以旧 Codex 角色继续工作。**请按上面的分工选择对应入口；
历史记录中的 "Codex" 指拆分前的旧角色。
