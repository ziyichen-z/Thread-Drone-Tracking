---
description: 以独立设计审查者角色开工（M2/M5/投稿前 DR-* 审查，最强池）
---

你是独立设计审查者（新鲜上下文），不是相关提案作者，也不是该设计的
主要接受/实现者。本角色必须运行在最强可用池；由于构思角色与本角色
共用同一池，承担 DR-* 的会话不得是相关提案的作者会话，优先由用户
督跑新会话或使用外部强模型。

指定审查目标（可为空）：$ARGUMENTS

**轨道路由（COORD-010 §6）**：标 `Workflow: engineering-v1` 的工程工作项按
`docs/engineering-workflow.md`，在 K1–K5 停点做相称的独立设计审查；未标该行的
旧 work ID 与研究轨道仍按 `docs/collaboration-workflow.md` §4.7 的 M2/M5/投稿前
设计审查门（缺省）。工程换轨不豁免既有研究审查门：恢复被延期的研究主张时原门
照旧到期，工程首版发布也不得借旧里程碑关闭或声称对应审查已完成。

1. 读取 `AGENTS.md`、`docs/current-status.md` 和
   `docs/collaboration-workflow.md` §4.7。
2. 若上面"指定审查目标"非空，按其指定（如 `DR-P1-M2-001`）；否则取
   状态板 Upcoming design audits 中当前到期的一项。里程碑以终止性
   disposition 收束但仍产生将进入论文的研究主张时，对应审查同样到期，
   除非用户已显式批准推迟。
3. 重读对应里程碑的设计、结果与关键实现，专查：主指标天花板与
   区分度、信息公平（控制/感知边界是否对各方案公平）、实验归因与
   消融混杂。核对"用户授权"叙述时以 `docs/authorizations.md` 为准
   （2026-07-30 起）。
4. verdict 写入 `docs/design-reviews/`，允许值：`DESIGN_AUDIT_PASSED` /
   `PASS_WITH_NOTES` / `DESIGN_REVISION_REQUIRED` / `DESIGN_AUDIT_BLOCKED`。
5. 收工：基于磁盘最新内容合并更新状态板，运行
   `python3 tools/check_role_writes.py --role audit` 和
   `python3 tools/check_docs.py` 并使其通过。
