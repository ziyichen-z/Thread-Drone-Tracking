# COORD-010 — independent verification

Reviewer/role: 复核角色 / independent verification（新鲜上下文会话，Fable 池；
档位不低于实现者）
Round: R1@batch1（提案 §7 步骤 1「规则候选」批；提案未定义 ASCII 停点短名，
本文取 `batch1`，后续核对/复核轮与提交信息逐字复用）
Date: 2026-09-07
Implementation snapshot: 候选 = 状态板 Active handoffs `COORD-010` 行指向的
批 1 提交（`git log -1` 主题「COORD-010 批 1 规则候选：工程轨道路由 + 双 check
工具（协调批次）」），30 个文件：27 改 + 3 新
（`docs/engineering-workflow.md`、`docs/project-background.md`、提案），
`controller/`、`Assets/`、`config/`、`runtime/`、`ProjectSettings/`、
`Packages/`、`tools/githooks/`、`tools/dist_data/` 零字节改动
round_candidate: 46158d78789611f90e508abb4e31a4592304b09f
Verdict: REWORK_REQUIRED

## 0. 范围、轨道判定与方法

- **轨道判定**：提案抬头无 `Workflow:` 行，且 `COORD-010` 是既有 work ID
  （AGENTS.md「工作流轨道路由」：既有 work ID 不得追加该行）→ 研究轨道
  （缺省），本轮按 `docs/collaboration-workflow.md` §4.4 与
  `docs/roles/review.md` 执行；本文件是该 work ID 的唯一复核文件。
- **复核对象来源**：状态板 Active handoffs 行「Review（批 1 复核）→ 接受
  （状态迁移批）| `COORD-010`」，声明范围「上列 27 改 + 3 新文件，逐文件
  diff」。候选 = 主树 HEAD（父提交为 DATA-002 颜色诊断文档提交，与候选之间
  只有这一个提交）。本 work ID 无上一通过候选，全量 diff 基线 = 父提交。
- **开轮资格（COORD-007 R1）**：`git diff <父>..<候选>` 在 PLAY_GOVERNING 集合
  上非空——`tools/check_docs.py`、`tools/check_role_writes.py`、
  `tests/test_check_docs.py`、`tests/test_check_role_writes.py`（4 文件，
  +149/−52）→ 开轮。未触及 Play 治理门文件（`analyze_m3_body.py`、
  `preflight_reanchor_env.py`、`controller/run_log.py`），无闭环轮义务。
- **停点自证（§4.3.1）**：协调批次，合规凭据 = 账本「2026-09-07 COORD-010 —
  批准 §10 A+B+C 整体落地」条目（提交信息逐字引用），无核对轮 `C<n>`；
  交接行给出范围、候选、聚焦回归主张与未验证项，四项条件成立，不给
  `REVIEW_BLOCKED`。
- **副本**：`git worktree add --detach .claude/worktrees/review-COORD-010
  <候选>`；读码、重跑、探针全部在副本内，主树对实现文件只读；收工删除。
- **重跑（不信报告数字）**：副本内
  `python3 -m unittest tests.test_check_docs tests.test_check_role_writes`
  → `Ran 38 tests … OK`（输出写 scratchpad `coord-010-focused.log`，只回显
  摘要）；`python3 tools/check_docs.py` → 通过（回显「分节上限、执行轨道
  纪律、Gate-echo、复核文件、消耗性门 blocks、DONE 行双证据、commit 引用、
  Last updated、hooksPath 均符合要求」）。测试树哈希：`HEAD:tests` =
  `30f089c7083d1cd2dd9616b3402914c550c22401`，`HEAD:tools` =
  `cef08232e3e95ba86f11ca46d495b4b864290909`；四个触及文件 blob：
  `tests/test_check_docs.py` `5029813…`、`tests/test_check_role_writes.py`
  `a00e784…`、`tools/check_docs.py` `6271b4f…`、`tools/check_role_writes.py`
  `b57859e…`。
- **额外探针**（副本内，`violations_for_role` / `violations_for_infra_fix`
  19+2 例，日志 `coord-010-probe-role-writes.log`）：接受 → `controller/*`、
  `docs/reviews/*`、`tools/check_docs.py`、`docs/engineering-workflow.md` 均
  DENY，`docs/project-background.md` ALLOW；辅助 → `docs/reviews/*`、
  `docs/proposals/*` DENY，`docs/project-background.md` ALLOW；复核 →
  `tools/check_docs.py`、`docs/engineering-workflow.md`、
  `docs/project-background.md` DENY，`docs/reviews/COORD-010.md` ALLOW；
  实现 → `docs/engineering-workflow.md`、`docs/reviews/*` DENY（INFRA 分支先于
  allow `*` 拦下），`controller/*` ALLOW；构思/设计审查 →
  `docs/project-background.md` DENY；`--infra-fix` 对
  `docs/engineering-workflow.md` DENY、对两 check 工具 ALLOW。与 §8 T5 一致。
- **依据列读法（本批次）**：提案自述「本稿未接受，无有效 BC；§8 为拟议
  验收项」，且协调批次无核对轮，故 `BC-n` 与 `上游漏检` 在本批不可用；范围内
  finding 一律填 `IN_SCOPE_NO_BC`（§4.6 归因读作「§7/§8 未有逐字验收条款覆盖」），
  对应的 §8 T-n 写在 finding 正文；阻断与否只由 CLASS 决定。无 `上轮漏检`
  （首轮）、无 `RED_LINE`（零真值/渲染路径）、无消耗性交接 → 无
  `blocks_consuming_gate` 行。
- **计数**：本停点第 1 次 `REWORK_REQUIRED`（上限 2）；修复直接回本角色
  `R2@batch1`，不经核对轮。

## 1. 逐文件核对（全量 diff，30 文件）

| 文件 | 变更要点 | 核对结论 |
|---|---|---|
| `AGENTS.md` | 必读顺序第 2/3 条改写；新增「工作流轨道路由」节（申请 + 接受裁定 + fail-closed、既有 ID 不追加、§3 旧项不回溯、共同红线、信封来源锁账本、Jetson 独立立项）；500 行阀删除改分节上限并要求与工具同批；基础设施清单加 workflow 与 engineering-workflow；「复核强制停点」加 K1–K5 段 | ✓ 无旧规则删减；路由 fail-closed 成立 |
| `CLAUDE.md` | 加 engineering-workflow 指针与双轨摘要，判据以 AGENTS.md 为准 | ✓ |
| `docs/collaboration-workflow.md` | 头部「适用轨道」节；§1/§1.1/§2/§3/§4.1/§4.2/§4.3.1/§4.6/§4.7/§6/§7 各加工程轨道段；§6 500 行段改分节上限；基础设施清单扩展 | 删减仅限 500 行文字；F5(a)、F6 |
| `docs/engineering-workflow.md`（新，195 行） | §0 路由 fail-closed、只替换 11 项、「未提及不等于豁免」；§2 任务合同；§4 K1–K5；§5 收敛；§6 复核 focused 重跑义务保留；§8 并发维持现状 + 信封缺项为 0；§9 Jetson；§10 体量；§11 完成/终止；§13 自身受 INFRA 保护 | F2（§2 `复核项覆盖：`）、F3（§8 共享槽位释义）、F4（§5「第 5 项」）、F5(b)（§0「判据只有路由行在不在」） |
| `docs/roles/acceptance.md` | 工程轨道节：裁定权、并发不变、任务合同取代 BC 表、K 停点核对轮、收敛、预算来源锁账本、设计审查、边界不变 | F2（`复核项覆盖：` 不要求；AC 行列集与模板不一致） |
| `docs/roles/ideation.md` | 申请行、fail-closed、既有 ID 不追加、合同六项、退修上限 | F2（「不承诺 `复核项覆盖：` 行」） |
| `docs/roles/implementation.md` | fail-closed 路由、小改 focused、K1–K5 停点自证按 AC-n、测试基线/新增失败分开、数据核验、边界与 INFRA 只读 | ✓ |
| `docs/roles/review.md` | 工程轨道复核差异：K 停点开轮、依据列不新造 token（`BC-n` 读作 AC-n）、一份复核文件、关键检查不豁免、红线 A 不变 | ✓ |
| `docs/roles/chore.md` | 压缩改为受委托/工具报错触发，体量数值不复抄；工程轨道预筛对象 K 停点、无门权 | ✓ |
| `.claude/commands/accept.md` | 路由段（申请/裁定/fail-closed）、第 4 步双轨说明、codex.md 仓库外入口冲突以仓库为准 | ✓ 步骤编号引用（第 4 步）核对正确 |
| `.claude/commands/implement.md` / `.cursor/commands/coding.md` | 路由段 fail-closed；「第 5/6 步」与「第 4/5 步」引用 | ✓ 编号与文件内步骤一致 |
| `.claude/commands/review.md` | 路由段 + 两轨共同不变项 | ✓（细则含裁定条件） |
| `.claude/commands/fable.md` | 工程提案写申请行、按合同要素撰写；第 4 步双轨 | ✓ |
| `.claude/commands/audit.md` / `chore.md` / `codex.md` / `sonnet.md`、`.cursor/rules/implementation-role.mdc` | 路由摘要（「标该行的按工程轨道」简写）并声明以细则为准 | ✓ 简写但转指 fail-closed 细则，见 F5 注 |
| `README.md` | 角色描述改为职能名；新增 Workflow routing 段（applies / ruled at ACCEPTED / fallback） | F9（删去 `DONE` 三证据句） |
| `docs/proposals/README.md` | 双轨模板；工程模板（AC 表、预算信封、必经停点、试读数字、核对表、决策记录） | F2（AC 表列集、无 `复核项覆盖：` 行） |
| `docs/reviews/README.md` | 双轨模板；工程模板保留机读行、依据列闭集不扩展、红线不放宽 | F5(c) |
| `tools/check_docs.py` | 删 `MAX_STATUS_LINES`/`check_line_count` 与其调用；docstring 重编号 1–9；分节报错文案与成功文案改写 | ✓ 仅删 500 行阀，其余 9 项调用保留（`collect_violations` 只少一行） |
| `tests/test_check_docs.py` | 去掉 500 行断言；新增超长正例、超长底板上 echo/轨道/DONE/blocks/分节反例、hooksPath 正反例；分节报错不再提硬顶 | ✓ 正反例真实执行（38/38） |
| `tools/check_role_writes.py` | `INFRA_PATTERNS` + `docs/engineering-workflow.md`；接受/辅助 allow + `docs/project-background.md` | ✓ 逐文件放行、INFRA 优先分支已存在 |
| `tests/test_check_role_writes.py` | 四条新测试：接受/辅助放行、其余门角色不放行、逐文件不外溢、engineering-workflow 全角色 INFRA + infra-fix 拒绝 | ✓ |
| `docs/authorizations.md` | 三条 2026-09-07 条目（方向确认、起草授权、A+B+C 批准） | ✓ 起草与落地授权分开（T1） |
| `docs/current-status.md` | Gate board 加 `COORD-010` 行；**`P1-VLM-DATA-002` Overall token 改写**；交接表改两行；下一动作/Current state 改写；Log 加两条；DATA-001 长叙述压缩为指针 | F1（旧项 token）、F7（500 行残留文字）、F8（172 行计数） |
| `docs/project-background.md`（新，17 行） | 个人背景 + 长期目标，无任务进度/门状态 | 见 N1 |
| `docs/proposals/COORD-010-…md`（新，259 行） | 提案正文；头部 `Status: APPROVED_ABC`、决策段转录用户批准 | 见 N2 |

「未提及不等于豁免」自查：规则文件中的删除行只有 AGENTS.md/workflow/
chore 三处 500 行阀文字与被扩展的基础设施清单；无其他条款被删或改弱。
信封来源：AGENTS.md、workflow §7 规则 0、acceptance.md、proposals README、
implement/coding 均写明只来自账本；engineering-workflow §8 以 §0 引用 +
「同口径」承接（见 N5）。

## 2. Findings

| 编号 | CLASS | 依据 | 范围判据 | 位置 |
|---|---|---|---|---|
| F1 | CLASS_2 | `IN_SCOPE_NO_BC` | 可达：状态迁移批直接消费 Gate board；Gate-echo 已因该 token 改动重写两行交接 | `docs/current-status.md` Gate board `P1-VLM-DATA-002` 行 |
| F2 | CLASS_2 | `IN_SCOPE_NO_BC` | 可达：§9 首个工程提案将直接套用模板与角色细则 | `docs/engineering-workflow.md` §2、`docs/roles/acceptance.md`、`docs/roles/ideation.md`、`docs/proposals/README.md` |
| F3 | CLASS_3 | `IN_SCOPE_NO_BC` | — | `docs/engineering-workflow.md` §8 |
| F4 | CLASS_3 | `IN_SCOPE_NO_BC` | — | `docs/engineering-workflow.md` §5 |
| F5 | CLASS_3 | `IN_SCOPE_NO_BC` | — | workflow 头部、engineering-workflow §0、reviews README |
| F6 | CLASS_3 | `IN_SCOPE_NO_BC` | — | workflow §2 |
| F7 | CLASS_3 | `IN_SCOPE_NO_BC` | — | `docs/current-status.md` 引言与 Log 节头 |
| F8 | CLASS_3 | `IN_SCOPE_NO_BC` | — | `docs/current-status.md` Gate board `COORD-010` 行 |
| F9 | CLASS_3 | `IN_SCOPE_NO_BC` | — | `README.md` |

### Blocking

#### F1 — 批 1 改写了旧工作项 `P1-VLM-DATA-002` 的 Gate board Overall token，与本批自述的「旧项门维持原状」不变量矛盾（CLASS_2，`IN_SCOPE_NO_BC`，对应 §8 T2「表内其余门不变」与 §7 两批次序）

- **事实**（全量 diff，Gate board 节）：`P1-VLM-DATA-002` 行 Overall 由
  `SURVEY_FLOORS_UNREACHABLE_AWAITING_USER_DECISION` 改为
  `CLOSEOUT_APPROVED_COORD010_PENDING_STATE_MIGRATION`；DATA-001 行与
  COORD-010 行的 Gate-echo 随之重写。
- **矛盾的四处自述**（同一提交内）：提案头部「在状态迁移批落地前，DATA-002、
  DATA-001、DIST-001 与里程碑门一律维持原状」；提案 §7 步骤 1「失败则规则仍
  未生效，旧状态不终止；只回退本批候选」；状态板 Immediate next actions
  「no old work item or milestone changes state before it」；交接行「迁移批
  完成前旧项终态一律不变」。
- **为何 CLASS_2**：workflow §4.4——涉及门/终态名的文字最低 CLASS_2，判据是
  工具或操作员行为是否因此不同：`check_docs.py` 的 Gate-echo 因该 token
  改动而要求两行交接重写（已发生）；Overall 列同时丢掉了负结果 token
  `SURVEY_FLOORS_UNREACHABLE`（§3 处置表明确要「原判定 … 保留」），而 §3
  处置尚未写入。如实说明：新 token 的内容（用户已批准 A、迁移待执行）是
  真实的且自带 `PENDING`，本 finding 针对的是候选违反自身与已批准提案的
  不变量，不是内容失实。
- **闭合路径（二选一）**：(a) Gate board 该行 Overall 逐字恢复为批前 token，
  把「用户 2026-09-07 已批准 A，处置待状态迁移批」写进交接行 Progress /
  Return to 文字，两处 Gate-echo 同步恢复；或 (b) 接受角色在提案
  `## Acceptance rulings（复判）` 节裁定「非终态过渡 token 可先于迁移批写入」，
  并把上述四处不变量改写为「迁移批前旧项不得获得 §3 处置或终态」。
- **闭合核实**：`NOT_MECHANIZABLE`（仓库无断言该不变量的工具）；闭合改为
  定点复看 Gate board `P1-VLM-DATA-002` 行与四处不变量文字。

#### F2 — 工程任务合同的格式在同一批次的五处文本互斥（CLASS_2，`IN_SCOPE_NO_BC`，对应 §8 T4「职责…在入口和模板一致」）

- **事实**：
  1. `docs/engineering-workflow.md` §2：「AC-n 清单下保留一行 `复核项覆盖：`，
     对 `行为` / `几何时序` / `边界失败` / `测试覆盖` / `文档一致` 逐一写 ✓ 或
     `N/A（理由）`」——**要求**该行。
  2. `docs/roles/acceptance.md` 工程轨道节：「不要求七列 BC 表、`复核项覆盖：`
     行、`BASE`/`CLARIFY` 标签与 `NEW_OBLIGATION` … 配额」——**不要求**该行；
     AC 行列集为「编号、验收项、证明方式、证据指针、日期」。
  3. `docs/roles/ideation.md` 工程轨道节：「不预写七列 BC 表，也不承诺
     `复核项覆盖：` 行」。
  4. `docs/proposals/README.md` 工程模板：AC 表列为
     `| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |`，无 `复核项覆盖：`
     行，也无「证明方式」列。
  5. 提案 §6「任务合同」行只要求「验收项稳定编号 AC-n，附证据指针」；
     workflow §4.2 工程段亦未提该行。
- **为何 CLASS_2**：两份 README 都写「工程轨道规则的权威正文是
  `docs/engineering-workflow.md`，冲突时以该文件为准」，因此按角色细则/模板
  写出的合同会被权威文件判为不合格，反之亦然；这决定构思/接受角色的实际
  产出物形态（操作员行为不同）。§8 T4 在这一点上不成立。
- **闭合路径**：选定一种形态并对齐全部五处。与提案 §6 一致的最小修法是删去
  engineering-workflow §2 的 `复核项覆盖：` 句，并统一 AC 表列集（以模板
  `编号 | 验收项 | 证据指针 | 停点 | 日期` 为准修改 acceptance.md 的列举，或反之
  在模板加「证明方式」列）；若选择保留该行，则模板、ideation.md、
  acceptance.md 三处同批补上。
- **闭合核实**：`NOT_MECHANIZABLE`；闭合改为定点复看上述五处。

### Non-blocking（CLASS_3，逐字替换补丁；由持有该文件写权限的角色在下一次提交应用，不改任何数字/ID/终态）

#### F3 — `docs/engineering-workflow.md` §8 给「共享槽位互斥」写了第二种定义（`IN_SCOPE_NO_BC`）

仓库中该词的既有指向（父提交 `docs/evidence/P1-M3-BODY-001-1c-preflight.md`
「shared 槽位此刻装着 B5 的产物」「槽位轮换」）是 Play/采集操作单的共享
输出槽位约定，本批 AGENTS.md 与 workflow §7 规则 0 也按此指向写「按现状
保留，本批不新写该约定的条文」；§8 却把它释为 workflow §7 规则 3（文件级
互斥 + worktree），即交接行自述已修的「假指针」仍残留一处。补丁：

```text
- - **共享槽位互斥**按现状保留（操作单层面的既有约定，本批不新写条文）：两个
-   角色不同时修改同一实现文件；复核角色只在一次性 worktree 接触实现代码，
-   主工作树保持只读。
+ - **共享槽位互斥**：Play/采集操作单沿用的共享槽位互斥使用约定按现状保留
+   （`AGENTS.md`「工作流轨道路由」、workflow §7 规则 0），本批不新写该约定的
+   条文；两个角色不同时修改同一实现文件、复核角色只在一次性 worktree 接触
+   实现代码是 workflow §7 规则 3，在本轨道同样不变。
```

#### F4 — `docs/engineering-workflow.md` §5 引用「`tools/check_docs.py` 第 5 项」已随本批 docstring 重编号失效（`IN_SCOPE_NO_BC`）

本批把 docstring 由 10 项重编为 9 项，复核文件同名核对由第 5 项变为第 4 项。
补丁：`（`tools/check_docs.py` 第 5 项按 Gate board 的` → `（`tools/check_docs.py` 第 4 项按 Gate board 的`。

#### F5 — 三处规则正文的路由句省略了「经接受角色裁定」条件（`IN_SCOPE_NO_BC`）

AGENTS.md 与四份角色细则把路由行定义为申请、以接受裁定为准、缺裁定
fail-closed；下列三句单独读会被理解为「写了该行即生效」。补丁：

```text
docs/collaboration-workflow.md 头部「适用轨道」节：
- - **工程轨道（`engineering-v1`）**：仅当提案头部逐字写有
-   `Workflow: engineering-v1` 时生效，细则见 `docs/engineering-workflow.md`。
+ - **工程轨道（`engineering-v1`）**：仅当提案头部逐字写有
+   `Workflow: engineering-v1`（该行只是申请）且经接受角色在 `ACCEPTED` 时
+   写明裁定后生效，细则见 `docs/engineering-workflow.md`。

docs/engineering-workflow.md §0 第三个 bullet 末句：
- 判据只有路由行在不在。
+ 判据只有路由行在不在，以及接受角色是否在 `ACCEPTED` 时写明裁定；缺任一即
+ 研究轨道。

docs/reviews/README.md 轨道路由段：
- 逐字写了 `Workflow: engineering-v1` 时，用文末的工程轨道模板。
+ 逐字写了 `Workflow: engineering-v1` 且接受角色已在 `ACCEPTED` 时写明裁定时，
+ 用文末的工程轨道模板。
```

注：`.claude/commands/audit.md`/`chore.md`/`codex.md`/`sonnet.md` 与
`.cursor/rules/implementation-role.mdc` 用「标该行的按工程轨道」简写，但均
声明以细则/入口为准，细则含 fail-closed 条件；不要求补丁。

#### F6 — workflow §2「确需改轨按 §4.2 重新提交范围」与 AGENTS.md「既有 work ID 一律不得追加该行」的衔接缺一句（`IN_SCOPE_NO_BC`）

补丁（workflow §2「轨道标注」bullet）：
`确需改轨按 §4.2 重新提交范围并由接受角色记录决策。` →
`确需改轨按 §4.2 以新 work ID 重新提案（既有 work ID 不得追加该行，见 AGENTS.md「工作流轨道路由」）并由接受角色记录决策。`

#### F7 — `docs/current-status.md` 引言与 `## Log` 节头仍写 500 行全文上限（`IN_SCOPE_NO_BC`）

本批已删除该阀（AGENTS.md、workflow §6、`check_docs.py` 同批），状态板自身
的两段说明未同步。补丁：

```text
引言第 10–13 行：
- and run `python3 tools/check_docs.py` after every update; hard limits
- (500 lines total, per-section caps, track discipline, Gate-echo) are set
- in AGENTS.md; history lives in the single `## Log` section, newest first,
- compressed under the 500-line cap with git history as the archive.
+ and run `python3 tools/check_docs.py` after every update; hard limits
+ (per-section caps, track discipline, Gate-echo; the 500-line full-file cap
+ was removed by COORD-010 §6 on 2026-09-07) are set in AGENTS.md; history
+ lives in the single `## Log` section, newest first, with git history as the archive.

`## Log` 节头：
- Newest first; one `### YYYY-MM-DD — title` per entry. Compress old
- entries' narrative under the 500-line cap (keep pointers, conclusions and
- open obligations); git history is the archive (COORD-007 R9).
+ Newest first; one `### YYYY-MM-DD — title` per entry. Compress old
+ entries' narrative only when a per-section cap bites (keep pointers,
+ conclusions and open obligations); git history is the archive (COORD-007 R9).
```

持有状态板写权限的任何角色均可在下一次提交应用；本轮复核未代为应用。

#### F8 — Gate board `COORD-010` 行「新增 `docs/engineering-workflow.md`（172 行）」计数与落盘不符（`IN_SCOPE_NO_BC`）

副本内 `wc -l` = 195 行（diffstat 同为 195 插入）。证据叙述计数，不驱动
动作。补丁：`（172 行）` → `（195 行）`（提交信息中的同一数字不可改，
仅记录）。

#### F9 — `README.md` 删去了「Runtime work is `DONE` only after …」一句（`IN_SCOPE_NO_BC`）

规则之家在 AGENTS.md/CLAUDE.md/workflow，README 已改为指向 AGENTS.md，
不构成规则放宽；但本批把「`DONE` 三证据」列为两轨共同红线，入口却失去
该句。补丁（Collaboration workflow 节 user bullet 之后加一段）：

```text
+ Runtime work is `DONE` only after implementation evidence, independent
+ review, and the user's Unity validation all pass; `CLOSED_*` means work in
+ that scope stopped and never substitutes for `DONE`.
```

## 3. 非 finding 记录

- **N1** `docs/project-background.md` 为本批新文件，但不在提案 §7 文件闭集
  表内；其存在由 §7「接受/辅助白名单仅增加 docs/project-background.md」行与
  当日 Log 条目隐含。副本内核对：17 行，仅个人背景与长期目标，无任务进度、
  门状态或证据（与「个人记忆不存任务进度」一致）。建议状态迁移批（可追加
  提案）把该文件补进 §7 表；不计 finding。
- **N2** 提案头 `Status: APPROVED_ABC`、决策段 `Decision: USER_APPROVED_ABC`
  不是既往 COORD 批次用过的 token（COORD-008/009 用 `LANDED` 与
  `NOT_APPLICABLE（用户…直接授权）`）；§3 状态门闭集不约束 COORD 提案头，
  仅记录。
- **N3** 提交信息主张逐条核实：五份角色细则、十份命令/规则文件、三份
  README 数目相符；父提交 `tests/test_check_docs.py` 无任何 hooks 断言
  （「此前全仓零覆盖」属实）；27 改 + 3 新与 diffstat 相符；零运行时路径字节。
- **N4** `check_docs.py` 「只删 500 行阀」核实：删除 `MAX_STATUS_LINES`、
  `check_line_count` 及其唯一调用，其余 9 项检查的调用与实现未动；两处
  文案改写不改判据。
- **N5** engineering-workflow §8 未逐字写「信封来源只能是账本」，靠 §0
  「授权账本与信封纪律」引用与「字段与 AGENTS.md 授权信封同口径」承接；
  AGENTS.md 已把来源锁死，可接受。返工时若顺手在 §8 首句加「信封只能由用户
  授权给出并逐字记入 `docs/authorizations.md`」更稳，不计 finding。
- **N6** T1 成立（起草授权与落地授权分开入账）；T2/T3 属状态迁移批，本轮
  不评（T2「表内其余门不变」的批 1 部分见 F1）；T5 成立（38/38 + 探针）；
  T6 成立（本批无发布/下载动作，§5 未声称实机/Jetson 性能/教师增量）；T7
  部分成立（交接表只含实际下一动作；`COORD-007` 行按 §3「起草阶段仍保留」
  留待迁移批）。

## 4. `UNITY_NA` 附议

**附议**：批 1 对 `controller/`、`Assets/`、`config/`、`runtime/`、
`ProjectSettings/`、`Packages/` 零字节改动（副本内 `git diff --stat` 为空），
仅改文档自检工具及其测试并有自身聚焦回归，不消耗 Play/ID/API/GPU；本批
可用 `UNITY_NA`。该附议不延伸到状态迁移批，也不改变 DATA-002 的 Unity
来源缺口记载。

## 5. Requested implementation action（交回实现角色/协调会话的动作）

1. 闭合 F1（路径 (a) 或 (b)）与 F2（五处对齐）；两者均 `NOT_MECHANIZABLE`，
   在提交信息写明选择的路径与触及文件。
2. 可在同一返工提交应用 F3–F9 的逐字补丁（同一账本凭据下的协调批次）。
3. 修复直接回本角色开 `R2@batch1`，不经核对轮；本停点已用 1 次
   `REWORK_REQUIRED`（上限 2）。状态迁移批在 `R2@batch1` 通过前不得执行，
   旧项终态一律不变。

## 6. Re-review result

（待 `R2@batch1`。）

---

# R2@batch1 — 增量轮（COORD-009 (b)）

Reviewer/role: 复核角色 / independent verification（同一复核会话续轮；返工由
协调会话完成，本角色未参与）
Round: R2@batch1
Date: 2026-09-07
Implementation snapshot: 返工提交（主题「COORD-010 R1@batch1 返工：F1/F2 闭合 +
F3–F9 逐字补丁（协调批次）」），7 文件：`README.md`、
`docs/collaboration-workflow.md`、`docs/current-status.md`、
`docs/engineering-workflow.md`、`docs/reviews/COORD-010.md`（本文件 R1 记录，
由该提交代为入库，内容逐字未改）、`docs/reviews/README.md`、
`docs/roles/acceptance.md`
round_candidate: 8246db2bb1b39be9fe4dfaaf0255c84890efe022
Verdict: PASS_WITH_NOTES
passed_candidate: 8246db2bb1b39be9fe4dfaaf0255c84890efe022

## 0. 范围与方法

- **双基线**：修复触及行 = `git diff <R1 候选>..<本候选>`（上列 7 文件，
  +396/−39，其中 324 行是本文件 R1 记录）；全量 diff = 相对父提交
  `6ed7017`（31 文件，本 work ID 尚无更早通过候选），只用于核实声明范围。
- **开轮资格**：PLAY_GOVERNING 集合相对 R1 候选**零字节**（`tools/`、`tests/`
  未动，`HEAD:tests` = `30f089c7…`、`HEAD:tools` = `cef08232…` 与 R1 相同）；
  本轮是 R1 `REWORK_REQUIRED` 的阻断 finding 闭合轮，按 §4.4 回归通道处理；
  F1/F2 均为 `NOT_MECHANIZABLE`，闭合改定点复看具名文件。
- **副本**：`.claude/worktrees/review-COORD-010` detached 于本候选；收工删除。
- **重跑**：副本内 focused
  `python3 -m unittest tests.test_check_docs tests.test_check_role_writes`
  → `Ran 38 tests … OK`（`coord-010-r2-focused.log`）；`python3 tools/check_docs.py`
  → 通过。无阻断 finding 绑定测试，故无红绿对；替代动作是下述定点复看。
- **新阻断来源自查**：修复触及行上无 CLASS_1/2；旧 finding 闭合全部成立；
  无 `RED_LINE`；未改动行上无 `上轮漏检` CLASS_1。未改动行上发现 1 条
  `上轮漏检` CLASS_3（F10），非阻断，不触发 `blocks_consuming_gate`。

## 1. 旧 finding 闭合核实

| 编号 | 闭合方式 | 定点复看结果 |
|---|---|---|
| F1 | 路径 (a) | Gate board 节与批前提交逐字 diff：**唯一差异是新增 `COORD-010` 行**（及其后一条指针条目，见 F10）；`P1-VLM-DATA-002` 行 Overall 恢复为 `SURVEY_FLOORS_UNREACHABLE_AWAITING_USER_DECISION`，Active handoffs 中两处 `P1-VLM-DATA-002` echo 均携带该 token，`check_docs.py` 通过。提案头「一律维持原状」、§7 步骤 1、状态板 Current state「No old work item or milestone changes state before migration」、交接行「旧项终态一律不变」四处未改写且现在为真；提案 `## Acceptance rulings（复判）` 仍为「无」，与路径 (a) 一致。**闭合成立。** |
| F2 | 提案 §6 最小形态 | `docs/engineering-workflow.md` §2 改为「表列集与 `docs/proposals/README.md` 的工程模板一致：`编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期`」并明写「不要求 … `复核项覆盖：` 行」；`docs/roles/acceptance.md` 工程轨道节列集改为同一五列；`docs/roles/ideation.md`（不承诺该行）、`docs/proposals/README.md` 工程模板（五列、无该行）、提案 §6、workflow §4.2 工程段均未改且与之一致；研究轨道 BC 表的 `复核项覆盖：` 行（workflow §4.2、proposals README 研究模板）原样保留。**闭合成立。** |
| F3 | 补丁逐字应用 | engineering-workflow §8 共享槽位 bullet 与 R1 补丁逐字相同 ✓ |
| F4 | 补丁逐字应用 | §5 改为「第 4 项」✓ |
| F5 | 补丁逐字应用 | workflow 头部、engineering-workflow §0、reviews README 三处均含「经接受角色在 `ACCEPTED` 时写明裁定」✓ |
| F6 | 补丁逐字应用 | workflow §2「以新 work ID 重新提案（既有 work ID 不得追加该行 …）」✓ |
| F7 | 补丁逐字应用 | 状态板引言与 `## Log` 节头均不再提 500 行阀 ✓ |
| F8 | 补丁应用 | Gate board 行「（195 行）」✓ |
| F9 | 补丁逐字应用 | README 补回 `DONE` 三证据 / `CLOSED_*` 句 ✓ |
| N5 | 采纳 | engineering-workflow §8 首句「信封只能由用户授权给出并逐字记入 `docs/authorizations.md`」✓ |

修复触及行逐 hunk 核对：README +4 行（F9）；workflow 2 hunk（F5(a)、F6）；
engineering-workflow 5 hunk（F5(b)、F2、F4、F3、N5）；reviews README 1 hunk
（F5(c)）；acceptance.md 1 hunk（F2）；状态板：引言（F7）、Current state 段、
Gate board `P1-VLM-DATA-002` 行恢复与 `COORD-010` 行（F8 + Overall token）、
Active handoffs 两行、Immediate next actions 段、Log 节头（F7）与两条新条目。
**无超出 F1–F9 + N5 的改动**；零运行时路径字节。

## 2. Findings（本轮新增）

| 编号 | CLASS | 依据 | 位置 |
|---|---|---|---|
| F10 | CLASS_3 | `上轮漏检` | `docs/current-status.md` Gate board 节 |

#### F10 — Gate board 节内误置了一条 Log 式指针条目（CLASS_3，`上轮漏检`，未改动行，非阻断）

批 1 在 Gate board 表后的说明段与「YOLOE simulation/deployment split」子表
之间插入了 `### 2026-09-07 — COORD-010 提案：起草授权 → 用户批准 A+B+C（指针）`
及其一条 bullet；`## Log` 已有同日「COORD-010 用户批准 A+B+C」条目承载同一
事实。格式误置，不驱动工具或操作员动作（`check_docs.py` 只解析表行）。
补丁：删除 Gate board 节内的这三行（标题、空行、bullet），不在 Log 重复新增。
持有状态板写权限的任何角色可在下一次提交应用；本轮未代为应用。

## 3. 非 finding 记录

- N1、N2（R1）继续有效：`docs/project-background.md` 仍不在提案 §7 文件闭集
  表内（建议迁移批追加）；`Status: APPROVED_ABC` 属 COORD 提案头的非既往
  token。
- 返工提交信息写「三处 Gate-echo 同步」，副本内 Active handoffs 只有两处
  `P1-VLM-DATA-002` echo（第三处应指 Gate board 行本身）；计数叙述，不影响
  结论。
- 返工提交把本文件 R1 记录一并入库并在提交信息声明未改其内容；副本内核对
  行数（324）与 §0–§6 全文与本角色 R1 落盘版本一致。

## 4. `UNITY_NA` 附议

R1 附议继续有效：本候选相对 R1 候选运行时路径零字节。

## 5. 收尾动作（交接受角色）

1. 批 1 规则候选通过；`docs/engineering-workflow.md` 与双轨路由自本候选起
   按状态板 `COORD-010` 行生效。
2. 执行提案 §7 步骤 2 状态迁移批：§3 旧项处置（含 `P1-VLM-DATA-002`、
   `P1-VLM-DATA-001`、`P1-VLM-DIST-001` 的具名 disposition）、§3.1 来源缺口
   收口说明（Unity 日志）、§3.2 继承清单（implementation-status）、交接更新
   （含 `COORD-007` 行离开 Active handoffs）、§9 下一项任务说明；旧项终态只在
   该批改。可顺带应用 F10 补丁并按 N1 把 `docs/project-background.md` 补进
   §7 表。
3. 迁移批完成后由用户按 §8 T1–T7 验收；本轮不覆盖迁移批，其 T2/T3/T7 仍待
   落地后核对。
