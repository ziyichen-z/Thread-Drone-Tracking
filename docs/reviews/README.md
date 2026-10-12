# 独立复核模板（双轨）

复核角色（review，历史名 Claude Sonnet）为每个 work ID 创建或更新一份报告，文件
名固定为 `docs/reviews/<work-id>.md`（`tools/check_docs.py` 按 Gate board 的 work ID
核对同名文件存在）。复核真实代码与需求本身，不能只读实现摘要；复核期间实现代码
只读，只在一次性 worktree 接触，发现缺陷一行也不许自己改，修复交回实现角色。

**轨道路由（COORD-010 §6）**：缺省走下面的研究轨道模板；被复核工作项的提案头部
逐字写了 `Workflow: engineering-v1` 且接受角色已在 `ACCEPTED` 时写明裁定时，
用文末的工程轨道模板。既有 work ID 与研究
轨道一律沿用旧模板，不因换轨作废。两轨的 verdict 闭集、机读行、`blocks`/`releases`
配对、finding 分级与红线通道完全相同。工程轨道规则的权威正文是
`docs/engineering-workflow.md`，本 README 只给模板与指针，冲突时以该文件为准。

## 研究轨道模板（缺省）

```markdown
# <work-id> — independent verification

Reviewer/role: 复核角色 / independent verification
Round:
Date:
Implementation snapshot: <files, artifact IDs, or commit if available>
round_candidate: <40-char SHA of this round's candidate (COORD-009)>
Verdict: PENDING

## Accepted requirements checked

## Files and tests read

## Findings

### Blocking

### Non-blocking

## Missing or weak tests

## Requirement-to-evidence mapping

## Requested implementation action（交回实现角色的动作）

## Re-review result
```

Verdicts are `PASS`, `PASS_WITH_NOTES`, `REWORK_REQUIRED`, or `REVIEW_BLOCKED`.
Use subsequent rounds in the same file so earlier findings remain auditable.

机读行（COORD-007 R7 / COORD-009）：每轮写 `round_candidate: <40 位 SHA>`；通过轮
另写 `passed_candidate: <40 位 SHA>`（`REWORK_REQUIRED` 轮禁止）。未改动行上的
`上轮漏检` CLASS_2 在该 finding 下单独一行写 `blocks_consuming_gate: <finding-id>`，
闭合时在后续轮单独一行写 `releases_consuming_gate: <finding-id>`（按文件顺序配对，
release 只关闭其前面的 block）；接受角色改标 `SCOPE_GAP` 时不写本目录，改在
`docs/implementation-status.md` 账本行标 `RELEASED_SCOPE_GAP`，`tools/check_docs.py` 视同
release；被账本 release 的 finding-id 不得再次 block，重开用新编号。未 release 时拒绝
任何未暂停的消耗性交接（本 README 与 `*-prescreen.md`、围栏代码块不参与扫描）。每条 finding 带依据列：`BC-n` /
`IN_SCOPE_NO_BC` / `SCOPE_GAP` / `上轮漏检` / `上游漏检` / `RED_LINE`（workflow §4.4），每条
finding 恰填一个值；finding-id 逐字取该 finding 的标题编号（如 `F17`）。
## 工程轨道模板（`Workflow: engineering-v1`）

工程轨道不改变复核的独立性、证据要求与红线，只把合同编号位从 `BC-n` 换成任务合同的
`AC-n`，并把停点短名固定为 K1–K5。文件名、verdict 闭集、机读行与配对规则同上。

```markdown
# <work-id> — 独立复核（engineering-v1）

Reviewer/role: 复核角色 / independent verification
Workflow: engineering-v1
Round: R<n>@K<n>
Date:
Implementation snapshot: <files, artifact IDs, or commit if available>
round_candidate: <本轮候选的 40 位 SHA>
Verdict: PENDING

## 0. 复核范围与停点

## 1. 逐条 AC 核对

| 编号 | 结论 {满足, 不满足, 证据缺失} | 证据 | 理由 |
|---|---|---|---|

## 2. 读过的文件与测试

## 3. Findings

### Blocking

### Non-blocking

## 4. 缺失或薄弱的测试

## 5. 交回实现角色的动作

## 6. 再复核结果
```

轮次命名 `R<n>@K<n>`（核对轮相应为 `C<n>@K<n>`），与任务合同「必经停点」的短名逐字
一致；每停点核对至多退回 1 次，`REWORK_REQUIRED` 每停点至多 2 次，第 2 次后未闭
finding 集冻结、轮 3 终局（COORD-009 (c)，工程轨道照旧适用）。

每条 finding 仍带依据列并恰填一个值。**依据列闭集与轨道无关**，逐字仍是 workflow
§4.4 的六值：`BC-n` / `IN_SCOPE_NO_BC` / `SCOPE_GAP` / `上轮漏检` / `上游漏检` /
`RED_LINE`；本 README 不扩展该闭集。工程轨道的任务合同编号写在该 finding 正文首行
「依据条款：`AC-n`」，不写进依据列——依据列同时是 workflow §4.6「归因机械派生与
记债」的唯一输入，加入未映射的值会让接受角色的收尾归因与 `SCOPE_GAP` 记债失去落点。

工程轨道不放宽任何红线：`RED_LINE`（真值泄漏、人眼保真等）永远阻断；复核角色不得
修改 `controller/`、`Assets/`、`tools/`、`tests/`、`config/` 的任何一行，也不复核自己
参与实现的候选；`DONE` 仍需实现证据 + 独立复核 + 相应 Unity/硬件证据，纯离线事项用
`UNITY_NA` 且须复核角色附议。
