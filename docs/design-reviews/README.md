# 新鲜上下文设计审查模板

独立设计审查是里程碑级门控，不代替 Sonnet 的逐功能代码复核。M2、M5 和
投稿前各执行一次。审查者必须使用新鲜上下文重新建立问题模型，不能是相关
提案作者，也不应是该设计的主要接受/实现者。

文件名示例：`DR-P1-M2-001.md`。

```markdown
# <design-review-id> — <milestone> 独立设计审查

Status: PENDING
Reviewer:
Reviewer independence: <why this is fresh and non-author review>
Date:
Design snapshot: <document version / commit>

## Claims and research questions reviewed

## Metric validity and ceiling analysis

## Ground-truth leakage and information fairness

## Baseline/ablation identifiability

## Scenario coverage and statistical protocol

## Deployment/resource assumptions

## Findings

### Blocking

### Non-blocking

## Verdict

PENDING

## Required design changes and owner
```

允许的 verdict：`DESIGN_AUDIT_PASSED`、`PASS_WITH_NOTES`、
`DESIGN_REVISION_REQUIRED`、`DESIGN_AUDIT_BLOCKED`。失败记录不得删除；修改
后在同一文件追加新一轮。
