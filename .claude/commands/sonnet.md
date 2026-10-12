---
description: 已更名：独立复核请改用 /review（复核不再绑定 Sonnet 模型）
---

此命令已更名为 `/review`。独立复核角色已与 Sonnet 模型解耦，必须运行
在最强可用池（档位不得低于实现者）。

**不要在本会话继续复核工作。**请先确认当前会话使用的是最强池模型，
然后运行 `/review $ARGUMENTS`。角色细则见 `docs/roles/review.md`；
历史复核记录中的 "Sonnet" 均指该角色的旧名。

**轨道路由（COORD-010 §6）**：`/review` 会先判定被复核 work ID 的轨道——标
`Workflow: engineering-v1` 的按 `docs/engineering-workflow.md`，其余按
`docs/collaboration-workflow.md`（缺省）。本文件是历史别名，不承载复核规则，
也不代表任何仍然生效的步骤；一律以 `/review` 与 `docs/roles/review.md` 为准。
