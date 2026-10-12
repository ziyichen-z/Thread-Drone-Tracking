# COORD-007 — 流程开销削减：把散文门改成机器门

Status: ACCEPTED_WITH_BINDING_CLARIFICATIONS（2026-08-12；第一批
R1–R8 + R9 已获用户授权并落地，R10/R11 与 R12 未授权未开工）
Author/role: 用户指派的监督会话起草（非构思角色的常规产出）
Created: 2026-08-12
Last updated: 2026-08-12

> 本文是提案，不是授权，也不是已接受设计。它提议修改工作流基础设施
> （`AGENTS.md`、`docs/collaboration-workflow.md`、`tools/check_*.py`、
> `tools/githooks/`），按 workflow §7 规则 7 这类修改**只能**由用户直接
> 授权的协调批次执行，合规凭据是 `docs/authorizations.md` 中的对应条目；
> 本文自身不构成该授权。起草会话未修改 `docs/current-status.md`，也未
> 建立任何 Active handoff。**本文硬预算 ≤ 400 行**：本项目最大的单个提案
> 是 3,709 行、其中 86% 是裁定文本，一份论证"文档过量"的提案不能自己越界。

## 1. 问题与研究价值

流程在 21 天里被六起真实事故逐层加固，每一层单独看都合理，合起来的稳态是：
**产出一个 31.25 秒的实验样本需要 74 次提交、44 个裁定轮、6 天。**按当前
速率外推，M3′ 剩余 9 个 trial 需 18–54 天，M4′/M5 落在 2027 年中之后。
研究价值不在于"更快"本身，而在于：以现速率本项目无法在可接受时间内产生
足以支撑论文的样本量，而流程开销与研究效度之间**并非同向关系**——§3 的
取证显示，成本最高的规则恰好是拦截记录为零的那几条。

### 1.1 取证口径

全部数字于 2026-08-12 在 `main`（`b6fdff3`）上实测复现。

| 指标 | 实测值 |
|---|---|
| 总提交 / 纯文档提交 | 415 / 326 = **78.6%** |
| 携带 `docs/archive/` 搬运的提交 | 213 / 415 = **51.3%** |
| `docs/current-status.md` 累计改动 vs 当前体积 | +10,499 / −10,119 行 vs 373 行（≈整体重写 28 遍） |
| 距上一次新增 `DONE` | 16 天；此后 271 次提交（65.3%）零关闭 |
| 21 天累计可写进论文的实测数据点 | **1**（A1，`C_geom=0.5784550774`） |
| 五个 `NOT_STARTED` 提案 | 6,837 行、29 轮构思↔接受往返、**0 行代码、0 次 Play** |
| `P1-M3-BODY-001` 单项 | 74 提交（**59 次零代码**）、38 接受轮 + 6 复核轮、11 版操作单、4 次 Play（3 次作废） |
| 44 个裁定轮的成因 | 真缺陷 18（41%）、**纯重跑仪式 16（36%）**、角色边界 5（11%）、文档措辞 3（7%）、等用户 2（5%） |
| **最刺眼的一条** | 最后一次代码字节变更是 `0ca13cb`（08-10），此后到 GO 生效仍有 8 个裁定轮、14 次提交，而 `git diff --stat 7156f7e..HEAD -- controller Assets tools tests config` **为空** |

## 2. 提议的行为

把**返工的触发条件从人的谨慎程度改为机器判据**，并把三道目前以散文形式
存在的关键门下沉为代码断言。不减少研究效度门的**内容**，只减少它们的
**触发频率**和**执行形态**。核心主张一句话：**三次 Play 作废没有一次是被
现有门当场拦下的，全部是先发生、再由接受角色事后归因，三次的修复也全部是
新写机器断言。所以答案不是加门，是把门从散文改成机器。**

## 3. 证据：哪些门救过命，哪些没有

判据：只有能指出**具体拦截记录**的才算救过命；"这道门存在期间事故没发生"
不算。

### 3.1 救过命（→ §6 红线，本提案不动）

| 门 | 拦截记录 |
|---|---|
| 复核逐文件 diff + 独立重跑 | 5 个 CLASS_1 缺陷**全部**在实现者测试已全绿时查出：DETECT-001 R1 B1（89/89 全绿，复核原文 "silently, with no exception and no failed test"）；SCENE-006 R6 F16（Unity 219/219 + full 326 全绿）；M3-BODY R3 F1/F2（Unity 267/267 + py 448 全绿）；RATE-003 R3 finding 2（279/279 + 162/162 + Play 3/3 全绿）。其中 2 个原理上自动测试抓不到 |
| 接受角色对复核**非阻断注记**的独立再判定与升格权 | 全项目最高价值缺陷（`CoverageEvaluator` 按 Game view aspect 而非 640×480 采集 aspect 投影，方向是**抬高**主指标 `C_geom`，在 M0 冻结代码里存活 16 天、穿过 43 轮复核）是以非阻断注记 N1 提出的，靠接受角色独立复判"比注记标题更重"才升格为 BC-BODY1-17 并立项 `P1-EVAL-001` |
| §4.7 DR-* 设计审查 | DR-P1-M2-001 R1 的 B1：主端点 `C_track\|geom` 的分母（几何可见时长）本身是受处理变量，5 Hz 档指向失败会让分母坍缩、伪装天花板。两次 `DESIGN_REVISION_REQUIRED` 全部在 batch-2 数据产生**之前**修完。代码复核原理上抓不到指标有效性错误 |
| 预注册 fail-closed 处置表 + 机器不变量 + 廉价 smoke | 全档案**唯一"当场拦下且零数据损失"**的类别：RATE-002 backlog race（不变量 `0 <= current-last_processed <= 1` 拒绝，停 HOLD，正式配额零消耗）；metrics cutoff（5.040644030 s vs 4.301775455 s，差 0.738868575 s > 容差 0.050001 s）；SCENE-003（1,257/1,257 确定性 `SUPPORT_HEIGHT_MISMATCH`，零 ID 消耗） |
| 用户真实 Unity Play | 复核已 PASS 之后仍被实跑抓到 ≥5 个缺陷（RATE-002 R3/R6/R7、SCENE-002 R2/R3） |
| COORD-005 人眼保真 | F23：正式 T1′ 测的是 `CreateTargetReplica` 造的无材质灰块，而运行时 `AddCarVisual` 涂红车。帧一直在盘上，哈希/计数/协议链按定义覆盖不到。另有 UT-P1-SCENE-001 用户截图发现出租车压路灯 |
| 授权账本硬语义 | 「上一轮的『查看一下 review 结果』已明确不解释为 GO」阻止了一次未授权 Play；「旧 GO 因进入 Play 而消耗、不追溯恢复」阻止 GO 复用；round 20 §B.4/§B.6 接受角色自行许可修改受保护路径，因账本无用户条目而被作为勘误撤销 |

### 3.2 未救过命（→ §5 削减对象）

| 规则 | 实测 |
|---|---|
| 停点条件 5（`check_role_writes --base` 逐路径归因） | 记录在案 50 次运行，真阳性 **0**；唯一一次真实 infra 越权（round 21，实现角色改 `tools/check_track_env.py`）该工具返回 **PASS**（假阴性），是人工抓的 |
| COORD-004 单条行数纪律（≤8 行 / ≤6 行） | 零内容错误拦截记录——它只压篇幅，不检查正确性 |
| 四个 `Recent *` 滚动节 + `rotate_docs.py` 按月归档 | 51.3% 的提交携带搬运动作 |
| 纯闭环复核轮（只核查上轮 finding 是否关闭） | 12 轮，新增阻断 **0**，新增 CLASS_1 **0** |
| 单线执行的 17 行多线汇报模板（`AGENTS.md`:33-49） | 12 天零触发，且**结构上不可能触发**——`check_docs.py` 在落盘前就拒绝，多线状态进不了磁盘 |

单线执行纪律本身**有一次真实拦截**（2026-08-06 修正 SCENE-005/007 的失效
交接文字），但拦截发生的机制是"暂停动作强制核对"，与"消耗性资源"无关。
见 §5 R8 的修正设计。

## 4. 三处必须先修的事实（对抗性检验发现）

以下三条推翻了"现状已经比 attempt 1-3 时期安全"的假设。**任何批量放行
方案都必须先修这三条**，否则削减流程会净增风险。

### 4.1 暂停窗**不是**机器门

实测 `grep -rn "2\.000000" tools controller Assets` → **0 命中**。唯一命中在
`docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md:369`，判据变量逐字写作
`reported_sim_t`——**操作员目视 HUD 后自己报的数**。HUD 滞后一帧（5 Hz 下
0.2 s），显示 9.97 时暂停、实际 `sim_t=10.03`、报 `9.970`，门 1 PASS，越窗
样本进入配对比较。attempt 2 的第一条根因（`sim_t=10.854090` 超窗）就是它，
当时的修法是**重写文档**，不是写断言。修法：Unity 暂停时把 `sim_t` 写进
`runtime/metrics.json`（`elapsed_simulation_s` 家族字段已存在），起 tracker
前读文件断言 `2.0 <= t < 10.0`，不符即拒绝启动并写
`TRIAL_VOID_PAUSE_WINDOW_VIOLATION`。**约 15 行 + 一条修复前必失败的测试。**

### 4.2 解释器绑定是散文

实测 `preflight_reanchor_env.py` 只把 `sys.executable` 写进输出 JSON
（:378-379、:441-442），**没有任何机制**把该值绑定到之后启动
`controller.track_loop` 的解释器。attempt 1 的作废（`.venv-track` 缺
torch/ultralytics，`YoloeProposer` 构造时 `ModuleNotFoundError`，exit 1，
发生在创建 run 目录之前，零产出）今天可以逐字重演。修法：预检把
`interpreter.executable` 写进 pre-Play 收据，tracker 启动命令必须**字符串
逐字相等**于 `<该路径> -m controller.track_loop`。三行。

### 4.3 `runtime/` 不受版本控制，收据在那里等于不存在

实测 `.gitignore:30-31` 为 `/runtime/*` + `!/runtime/README.md`；
`git ls-files runtime/` 只返回 `runtime/README.md`。后果两层：(a) 写在
`runtime/` 的 pre-Play 收据可被静默原地覆盖、事后无法验伪，与 attempt 2 的
第二条根因（记录只留在会话消息里）在可验伪性上同档；(b) 复核角色按 §4.4 用
`git worktree add --detach` 开副本，未跟踪文件不会带过去，复核**物理上看不见**
`runtime/` 下的收据与 run 数据。修法：收据留在 `runtime/` 作机器复算副本，
其 SHA-256 追加写入受追踪的 append-only ledger 并提交——一行哈希、一次提交，
且提交发生在进 Play **之前**，不与"Play 时工作树干净"冲突。

## 5. 提议的修改（按批次）

### 第一批 —— 一个协调批次，零新工具，不碰任何 M3′ 冻结项

不改 charter、阈值、采集 ID、测量窗、指标口径，**不触发反调参纪律，不需
重走停点**。

**R1｜复核开轮资格机械化**
- 文件/节：`docs/collaboration-workflow.md` §4.4 开头、§4.3.1 末段
- 从：返工后一律"回到同一停点，再次等待该 work item 的复核 verdict"
- 到：开轮资格 = `git diff --stat <上一通过候选>..<候选>` 在
  **PLAY_GOVERNING 集合**上非空。为空时禁止开新复核轮，缺陷按 R4 处理。
- PLAY_GOVERNING = `controller/`、`Assets/`、`tools/`、`tests/`、`config/`、
  **`ProjectSettings/`、`Packages/packages-lock.json`**、以及该 work item
  冻结集点名的操作单文件。后三项是对抗性检验的修正：
  `ProjectSettings/TimeManager.asset` 实测含 `Fixed Timestep: 0.02` /
  `Maximum Allowed Timestep: 0.33333334` 且 `git ls-files` 可见，而本项目
  已自证无 `captureDeltaTime` 钉住、dt 不同则轨迹不同；操作单则是人手执行
  的实验协议本身（F3 就是"冻结操作单逐字执行会停摆"，而它零代码字节）。
- 省：约 6 轮 / 12 次提交（诚实：不是 8 轮——`7156f7e` 与 `6019f33` 都是
  操作单改版，修好口径后仍会开 2 轮）。依赖：必须与 R4、R7 同批

**R2｜删停点条件 5**
- 文件/节：`docs/collaboration-workflow.md` §4.3.1 条件 5（5 条 → 4 条）
- 到：删除。写入合规交给 pre-commit 钩子。**同批必须做**：
  `tools/githooks/pre-commit` 实测只 `exec python3 tools/check_docs.py`，
  **不跑** `check_role_writes.py`——要么真接进钩子（角色从提交信息 trailer
  取），要么明写该检查已移除。留着一个 50 次运行 0 真阳性、1 假阴性的动作
  当收工仪式，正是本提案要砍的形状。
- 证据：§3.2 第一行

**R3｜finding 由回归测试关闭，取消纯闭环复核轮**
- 文件/节：`docs/collaboration-workflow.md` §4.4；`docs/roles/review.md`
- 到：每条阻断 finding 绑定一条**修复前必失败**的具名回归测试，闭合需四条
  同时成立：(1) **fixture 由生产路径产出**——调用真实写盘函数或消费已归档
  真实 run 的字节副本，禁止手工 `mkdir` / 手写 JSON 造状态；(2) 接受角色
  **亲自复算**（`git revert -n <fix>` → 重跑该测试 → 观察失败 → 恢复，
  约 5 分钟、零角色切换）；(3) 修复若触及 Play 治理门
  （`analyze_m3_body.py`、`preflight_reanchor_env.py`、`controller/run_log.py`）
  则**闭环复核不得省**；(4) 复核可标 `NOT_MECHANIZABLE`（仓库里不存在可写
  断言，如 F23/N1 类），这类需**定点**复看具名文件，不重跑全套。
- 条件 1/2 的必要性：RATE-003 R3 finding 2 中两条声称"覆盖"校准 receipt 的
  测试手工伪造 `runs/<calib-slot>` 目录，复核原文判 "a state production
  cannot reach … asserts the claim in name only"——"pre-fix 会失败的具名测试"
  这个判据在本仓库已被证明可以完全为空；条件 2 同时补回 CLAUDE.md 那条
  "实现者不能给自己的代码签发独立复核通过"。
- 省：约 10 轮（12 轮减去条件 3 保留的部分）

**R4｜finding 分级，CLASS_3 不阻断**
- 文件/节：`docs/collaboration-workflow.md` §4.4
- CLASS_1（改数字或结论）/ CLASS_2（边界、失败路径、并发原子性、真值泄漏）
  → `REWORK_REQUIRED`；CLASS_3 → 不阻断，复核给逐字替换补丁、接受同轮应用，
  **不得改动任何数字、哈希、run ID、disposition**。分级由接受角色独立复判
  并逐条写下同意/升格（与 §3.1 第二条同款条款）。
- **CLASS_3 定义为闭集**：拼写、格式、失效链接、已执行步骤的时态。凡涉及
  数值、阈值、ID、判据、执行顺序、终态名的文字一律最低 CLASS_2，**无论
  代码字节是否为零**。判据是"操作员或工具的行为会不会因这段文字而不同"。
- **同批必须改白名单**：`ROLE_RULES['acceptance']['allow']` 实测**不含
  `docs/evidence/*`**。不加这一行 R4 是空转条款——N24 绕整整一圈的直接
  原因就是这条白名单。
- 省：本 work item 4 轮 / 6 提交

**R5｜infra 自修复例外 + 修掉两处已记录未修的漂移**
- 文件/节：`AGENTS.md` §角色边界；`tools/check_role_writes.py:30-41`；
  `tools/check_docs.py` docstring
- 例外：允许任何角色在**只改 `tools/check_*.py` 与 `tests/test_check_*.py`
  的单独提交**里修复自检工具的假阴性/坏夹具，提交信息须贴触发的失败输出，
  不得与证据产出混在同一提交，由下一轮复核逐文件 diff。同批修两处实测
  漂移：(a) `INFRA_PATTERNS` 列 `check_docs.py`、
  `check_role_writes.py`、`rotate_docs.py` 三个**字面名**，而 `AGENTS.md`
  写通配 `tools/check_*.py`——实际存在的 `check_anchor_placement.py`、
  `check_scene_body_margin.py`、`check_track_env.py` **规则说保护、工具不
  保护**，round 21 的假阴性即由此产生；(b) `check_docs.py` docstring 写
  "每条 ≤ 28 行 / Active handoffs ≤ 40"，代码实为 `MAX_ENTRY_LINES = 8` /
  `"Active handoffs": 70`。
- 省：一次 **9 天 / 134 提交**的红灯窗口 + 23 个文档的逐份归因段

**R6｜提案退修上限**
- 文件/节：`docs/collaboration-workflow.md` §4.2
- 到：第 2 次 `REVISION_REQUESTED` 之后不得再自行发第三次退修，**上交用户
  二选一**（接受当前范围并逐条列出已知缺口 / 关闭为负结果记录）。采"上交
  用户"而非"接受角色自行改定"：后者削弱提案作者与裁定者的分离，而这个分离
  正是救出 `P1-EVAL-001` 的东西（§3.1 第二条）。
- 省：历史 29 轮往返里至少 15 轮；直接解开 VLM 两条提案的互锁（都在用文字
  回答需要数据的问题）
- **不采纳**"EMPIRICAL 类必须走零 ID 诊断 spike"：`current-status.md` 逐字
  写着「zero-ID E5-A diagnostics cannot issue binding gate evidence under
  COORD-005」，把经验性阻断项路由进一条定义上不产出有约束力证据的通道
  是新的死循环。

**R7｜禁止手写可派生标识 + 复核轮产出机读候选**
- 文件/节：`AGENTS.md` §共享状态更新；`docs/collaboration-workflow.md` §6
- 到：(a) 凡可从 git 与复核文件派生的标识（上一通过候选、工件 SHA、run
  目录名、HEAD）一律运行时解析，禁止写进手维护文档，存量不回改；
  (b) **每个复核轮必须写一行机读字段 `passed_candidate: <sha>`**
  （`REWORK_REQUIRED` 轮不产出）。(b) 是 R1/R3 的**安全前提**而非附属品：
  两者都让某类批次不开复核，若不同时钉死"上一通过候选"这个指针，它会失去
  定义、归因 diff 退化成对着过期基线空转。N24 是这件事的单提交版本。
- 省：N24 那一类（2 接受轮 + 2 提交 + 1 次角色交接换 1 个哈希字面量）

**R8｜单线执行改为约束消耗性资源，但换掉触发器**
- 文件/节：`AGENTS.md` §单线执行纪律；`docs/collaboration-workflow.md`
  §7 规则 0
- 到：**1 条消耗性轨道 + 至多 2 条零消耗轨道**（消耗性 = 创建/消耗
  scenario/session/run ID、Play 配额或 API 预算），交接表加 `Consuming` 列，
  删除 `AGENTS.md`:33-49 的 17 行多线汇报模板。
- **关键修正**：不能只按消耗性切。COORD-003 的触发事故逐字是"交接文字失效
  无人察觉、证据账本落后整轮、两条交接互相引用对方未定的状态"——**三条全部
  是零消耗失效**；而单线执行 12 天里唯一一次真实拦截，恰恰是因为暂停
  SCENE-005/007 才被迫核对、发现它们等的 recharter 已关闭。所以强制核对的
  触发器必须从"暂停"改挂到**依赖变更**：`check_docs.py` 强制每行交接把它
  引用的 work ID 的当前 Gate board `Overall` 值逐字抄进本行，不一致即拒绝
  提交（2026-08-06 那次会被抓到）。规则文本与检查器**必须同批改**
  （`AGENTS.md` + `check_docs.py:68` `MAX_ACTIVE_HANDOFFS`），否则中间窗口里
  规则说允许 3 条、检查器仍拒绝第 2 条——正是 R5 在修的那类漂移。
- 省：不省轮，解冻 4 个 work item（SCENE-005/007 在 21 天周期里冻结 12 天）

### 第二批 —— 一个实现批次 + 一轮完整复核

**R9｜四个滚动节合并为 append-only `## Log`，删除按月归档机械**
- 文件/节：`AGENTS.md`:90-104；`docs/collaboration-workflow.md` §6；
  `check_docs.py` 删 `check_rolling_sections` / `check_entry_lengths` /
  `check_current_state_bullets`，**保留** `check_line_count(500)` /
  `check_gate_board_done_rows` / `check_gate_board_reviews` /
  `check_commit_ids` / `check_hooks_path`
- **不删时间轴**：四节合并成一个 `## Log`（最新置顶），由 500 行全文上限
  自然逼出压缩；然后 `rotate_docs.py` 与 `docs/archive/` 整套**删除**——
  workflow §7 规则 6 自己写着"Git 历史负责版本追踪"。为什么不能直接删四节：
  COORD-002/003/004/005/006 每一条都是**先落在 Recent coordination decisions
  才成为规则**的；单线执行纪律之所以还站得住，靠的是有人把触发事故的叙述
  从滚动日志抄进了 `AGENTS.md`:19-22，而原始记录躺在
  `docs/archive/current-status-2026-07.md`。"没有证据链依赖归档"是幸存者
  偏差：承重部分都被提升进常驻文件了，删掉入口就把提升路径一起删了。
- 省：51.3% 提交里的搬运动作 + 每次收工的二次编辑

**R10｜`tools/trial.py`：trial 顺序执行器（~150 行，不是状态机）**
- 工具层已建成约 90%：`analyze_m3_body.py` 实测 **110 个 `raise
  AnalysisError`**，加 `preflight_reanchor_env.py` 457 行环境门；缺的只是
  穿针引线。只做四件现在由人做的事：(1) 按固定顺序调用已有工具；(2) 进
  Play **之前**写 pre-Play 收据并把其 SHA-256 提交进受追踪 ledger（§4.3）；
  (3) 暂停窗**读遥测**而非读人报数（§4.1）；(4) 解释器路径相等校验（§4.2）。
- **void 保持人工**：作废本该是昂贵、可见、需要人签字的动作；把它变成
  runner 子命令既新增"单点缺陷规模化"风险，又是选择性丢弃通道的前置条件。
  每个门配一条修复前必失败的对抗性测试；`--verify` 必须能**不经 trial.py**
  独立复算。

**R11｜抗选择性丢弃：作废决策与指标计算的因果隔离**
- 现状风险：`analyze_m3_body.py` 在同一次 `--verify` 里既算
  `h1.full_loop_c_geom` 又打 `disposition`，操作员跑完立刻看见落点；而 void
  现场全部落在 gitignored 的 `runtime/`（§4.3）。本项目现有的抗选择性丢弃
  能力**完全来自"每次作废都被迫改一次受复核的代码"**——那两个手写进
  `analyze_m3_body.py:127-131` 的 predecessor SHA。
- 三条修法：(1) 作废理由必须在**任何指标被计算之前**发出——完成握手与暂停
  窗遥测门通过即把该 acquisition 标为 irrevocably counted，之后 `--verify`
  才允许运行，已计数的 run 任何情况下不得作废；(2) void 收据追加写入**受
  追踪**的 append-only `docs/evidence/P1-M3-BODY-001-void-ledger.jsonl`；
  (3) 论文补充材料报告**全部** acquisition 及机器作废理由，不只报 5 个。
- 同批：acquisition ID 的合法形状**参数化并预注册**为
  `<canonical-slot>[-attempt-N]`（N ≤ 冻结重试上限），`attempt>1` 者须携带
  predecessor void 现场 SHA（沿用 `a1_predecessor_*` 门的写法，从字面量改成
  从 ledger 读）。否则一次合法作废就让 `arm_a_trial_ids_not_frozen_sequence`
  硬失败，唯一出路是**在已看到数据之后编辑分析器**——正是红线 B 禁止的形状。
  A1 的 attempt-4 映射就是这条路径的实测代价：9 接受轮 + 2 复核轮 + 约 20 提交。

### 第三批 —— 需先攒证据：**R12｜批次配额 GO**

- `docs/authorizations.md` 条目格式加机读 grant 块
  （`grants / count / run_ids / preconditions / expires`）。保留不变的两条
  硬语义：「账本没有的授权视为未发生」「旧 GO 已因进入 Play 而消耗、不追溯
  恢复」——改由机器执行，语义更强不更弱
- **配额上限 2，不是 8。** 每完成一对插一次完整性检查点：对全部已完成槽位
  重跑 `--verify`、重算冻结集字节门、把新 run 的
  `metrics.final.json.evaluation_projection` 与五份 create-once 配置 SHA
  与 A1 逐项比对，通过才解锁下一对。理由：RATE-001 = 统一协议缺陷 + 批量
  执行 + 只有事后检测 = **12/12 全批损失**（穿过提案 ACCEPTED + 4 轮全 PASS
  复核 + 12/12 逐 run 准入）；而
  `metrics_projection_aspect_mismatch`（`analyze_m3_body.py:1232-1239`）住在
  analyze 里、Play 花完之后才响，它把静默污染换成响亮作废——对论文是好事，
  对 Play 预算是灾难。配额压到 2 把爆炸半径从 8 次 Play 降到 2 次，而瓶颈是
  用户一天能给几次 Play、不是 GO 往返，进度损失接近零。
- 前置条件（全满足才放开 `count>1`）：① R10 落地并跑通至少 1 个真实 trial；
  ② 冻结集字节身份门生效（每次 arm 重算，含 `ProjectSettings/`）；
  ③ §4.1/§4.2/§4.3 三条修完；④ `metrics_projection_aspect_mismatch` 在链路上
  （**已满足**：`61ea20b` 于 2026-08-07 落地）

## 6. 红线（本提案不动）

§3.1 表七条全部保留，另加两条执行细则：**红线 A** 复核物理隔离（一次性
worktree）+ 不改一行实现代码（21 轮零污染；可放宽到"对非实现路径给逐字
替换补丁"，但 `controller/ Assets/ tools/ tests/ config/` 一行不许改）；
**红线 B** 真值隔离 + 反调参纪律，且**必须在 workflow 明写其边界**——若连
GO 一起重发（改 config、重拿授权、再跑），机械上拦不住，只能靠账本时序与
复核兜底，不能让它看起来比实际更硬。

§3.1 第一条（复核逐文件 diff）可降**频率**（只在 PLAY_GOVERNING 非空的新
批次首轮），不可降**内容**。其中"重跑全套测试"可砍：5 个 CLASS_1 全部在
测试已全绿时查出，价值在 diff 不在重跑。改为跑 focused 套件 + 记录测试树
tree hash，全套留给 pre-commit。Review round 6 为核验一次纯文档编辑重跑了
focused 50/50 + preflight 36/36 + 全套 510，是这条的最坏体现。

## 7. 验收条件

可证伪，逐条对应 §1.1 的基线：

1. 第一个完成的 trial（A2）成本 ≤ **3 次提交 / 2 次角色切换 / 1 天**
   （基线：A1 = 74 提交 / 6 天）。
2. 不再出现"PLAY_GOVERNING diff 为空却开复核轮"的轮次（基线：8 轮）。
3. 新增提交中携带 `docs/archive/` 搬运的比例 ≤ 5%（基线：51.3%）。
4. 第二批落地后 `grep -rn "2\.000000" tools controller` 有命中且为可执行
   断言（基线：0 命中）。
5. R11 落地后任一 void 事件在 `git log` 中可见（基线：三次 void 现场全部
   仅存在于未追踪目录）。
6. **反向验收（防退化）**：采纳后 6 个月内若出现任何 CLASS_1 缺陷进入正式
   数据，必须归因到本提案删除的**具体某一条**规则；归因不到删除项的不作为
   本提案的失败证据，归因得到的对应条款立即回滚。

## 8. 失败模式与资源风险

| 风险 | 缓解 |
|---|---|
| R3 取消闭环复核后，测试覆盖之外的语义回归无新鲜眼睛（历史基率 0/12，样本小） | R3 条件 1/2/3 |
| R9 删归档后跨 work item 时间轴丢失 | 合并为 `## Log` 而非删除；git 历史兜底 |
| R10 单点缺陷规模化 | 每门配对抗性测试；`--verify` 可不经 trial.py 复算；void 不自动化 |
| R12 批量 GO 放大 RATE-001 类全批损失 | 配额 2 + 每对检查点 |
| 削减本身制造新流程债 | 本提案不新增文档类型、不新增手维护台账。注记仍以 `docs/reviews/` 为唯一事实源，需要索引时由工具从 `N<k>` 块**派生打印**，不落新 markdown |

## 9. 建议的实施范围（不强制）

**迁移路径 —— 剩余 9 个 trial。**已核实的前置事实：A1 =
`0.5784550773737355` ∈ [0.5645, 0.95)，BC-BODY1-15 首跑门已过；`61ea20b`
（aspect 修复）于 2026-08-07 落地、attempt 4 于 2026-08-12 采集，**A1 与
剩余 9 个在同一投影契约下**，历史 `C_geom` 族的未受控 aspect 债不污染本
批次配对比较。

0. **今天**：签第一批 R1–R8（不碰冻结项，不触发反调参，不需重走停点）。
1. **trial A2**（半天，目标 2 次角色切换 / 2–3 次提交）：先由接受角色发
   操作单 **revision 12**，走 R4 通道（零代码字节、CLASS_2、同轮应用、
   不开复核轮）。**不得以"本次不逐字执行冻结操作单"的方式绕过**——round 20
   §B.4/§B.6 已有先例，接受角色自行许可修改受保护路径被作为勘误撤销。
   revision 12 至少含：(a) §2.5 第 9 项 ID →
   `p1-m3-body-001-arm-a-trial-2`（实测 §2.5 的 1/2/3/8 四项在当前 runtime
   上已成立，所谓"§2 对 A2 已不可执行"**只对第 9 项成立**）；(b) **新增
   §2.6「有效 trial 轮换」**——现有 §2.1–§2.4 只覆盖 **void** 现场，无一节
   描述有效 Play 之后共享槽位怎么轮换，而每次有效 Play 都会往
   `runtime/frames/` 写 620+ 项、以 `FileMode.Create` **截断**
   `m3_body_truth.jsonl`、重写 `metrics.json` 和三个发布文件（round 12
   阻断项逐字：「A1 原始输入不得被 A2 覆盖」）；规定分析通过后**移动**
   （禁止删除）到 `runtime/<stem>.<acquisition-id>-hold.<ext>`，前后
   计数/行数/SHA-256 逐项相等；(c) §4.1/§4.2 两条断言落地（约 20 行）。
   这一步的价值是**在不写新工具的前提下验证 R1–R4 够不够用**。
2. **R10 + R11**（1.5–2 天）：有代码字节 → 走完整复核。
3. **R12 配额 2 的批次 GO**（4–5 天）：布防只做 ≤30 s 零 ID smoke + 2 张
   样帧人眼保真，**不做全时长诊断 Play**——attempt 4 刚在同一份冻结代码上
   跑完整条链（130.0018 s、自然退出 0、`--verify` PASS），且
   `canonical_trial_id()`（`analyze_m3_body.py:485-505`）对十个冻结 ID 之外
   的一切抛 `run_id_not_frozen_trial`，诊断 Play 要么用非冻结 ID 使 110 个门
   一个都跑不到、要么直接消耗一个正式槽。替代方案是**离线重放语料**：
   `runtime/runs/…-attempt-4/frames.jsonl`（含那 30 条补追行）+
   `m3_body_truth.jsonl` 已在盘上且字节冻结，规定任何改动分析器门的批次
   必须对该语料重跑并逐字节复现 A1 receipt。零 Play，覆盖全部 110 个门。
4. **批次关闭**（半天）：`--compare` 前强制对全部槽位 audit-all；复核第二次
   也是最后一次上场，范围是真实工件（打开实际帧图、**不经 trial.py** 独立
   复算至少一个 trial、核对每份收据的冻结集 SHA、核对无 void 现场被静默复用）。

**合计约 7–9 个工作日**（对照历史速率外推的 18–54 天）。**不投工具的下限
方案**：只做步骤 0 + 把步骤 1 重复 9 次 ≈ 4.5 天纯执行 + 9 条 GO；工具买的
是"0 次角色切换"和"不会再手滑"，不是必需品。

## 10. 待决问题

1. 第一批八条整体签还是拆开？R1 依赖 R4+R7、R2 依赖 pre-commit 改动、
   R8 的 `AGENTS.md` 与 `check_docs.py` 必须同批——**这四组内部不可拆**。
2. R9 删除 `rotate_docs.py` 与 `docs/archive/` 是否可接受？现有两个归档文件
   （3,790 + 1,122 行）保留只读，不再新增。
3. R12 的配额上限 2 是否够用？取证判断瓶颈在用户 Play 可用性而非 GO 往返。
4. §9 步骤 1 的操作单 revision 12 由谁写？按白名单 `docs/evidence/*` 目前
   只有实现角色可写（R4 建议加接受角色）。

## Codex review decision

Decision: **`ACCEPTED_WITH_BINDING_CLARIFICATIONS`**（Acceptance round 1，
2026-08-12——**仅技术接受，零执行授权**；三个批次每一批都需
`docs/authorizations.md` 用户逐字条目后方可开工）
Rationale: 见 Acceptance round 1 §A（事实核验）与 §E（依据摘要）。
Required revisions: 无——可定死的歧义全部以 BC-C7-1…13 钉死，不退修。
Accepted design-document changes: 无。`docs/phase1-single-drone-design.md`
（v0.3.17）不因本提案改动；本提案不触及研究主张、阶段边界、主指标、
硬件目标；冻结的 M3′ 采集/测量/指标语义零变化。

## Acceptance round 1（2026-08-12）

审查者：接受角色（Claude Code 备用入口 `/accept`），非起草会话、非实现
会话。起草身份披露：本文由用户指派的监督会话起草，非构思角色常规产出；
起草行为零消耗、零门权、不携带任何授权效力（授权账本无且无需相应条目），
本轮按 workflow §4.2 作常规提案处理。

### §A 事实核验（2026-08-12，工作树 `b6fdff3` + 本未跟踪文件）

**逐字复现（15 项，与声称一致）：**

1. `tools/githooks/pre-commit` 只 `exec python3 tools/check_docs.py`，
   不跑 `check_role_writes.py`（R2 前提）。
2. `grep -rn "2\.000000" tools controller Assets` 零命中；唯一判据文本在
   `docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md:369`，变量逐字
   `reported_sim_t`（§4.1 成立：暂停窗是人报数门，不是机器门）。
3. `tools/preflight_reanchor_env.py` 457 行；`sys.executable` 仅写进输出
   JSON（:378-379、:441-442），无任何机制绑定后续 tracker 解释器
   （§4.2 成立）。
4. `.gitignore:30-31` 为 `/runtime/*` + `!/runtime/README.md`；
   `git ls-files runtime/` 仅 README（§4.3 成立）。
5. `ROLE_RULES['acceptance']['allow']` 不含 `docs/evidence/*`（R4 前提）。
6. `INFRA_PATTERNS` 只点名三个字面工具名；`tools/check_anchor_placement.py`、
   `tools/check_scene_body_margin.py`、`tools/check_track_env.py` 存在且
   不受保护（R5(a)）。
7. `check_docs.py` docstring 写“每条 <= 28 行 / Active handoffs <= 40”，
   代码实为 `MAX_ENTRY_LINES = 8`（:49）与 `"Active handoffs": 70`（:57）
   （R5(b)）。
8. `ProjectSettings/TimeManager.asset` 受 git 追踪，含
   `Fixed Timestep: 0.02` / `Maximum Allowed Timestep: 0.33333334`；
   `Packages/packages-lock.json` 受追踪（R1 集合修正成立）。
9. `git diff --stat 7156f7e..HEAD -- controller Assets tools tests config`
   为空；`0ca13cb`（2026-08-10）之后 14 次提交（§1.1 末行成立）。
10. 总提交 415；触及 `docs/archive/` 的 213（51.3%）。
11. `docs/current-status.md` 累计 +10,499/−10,119 行 vs 现文件 373 行。
12. `P1-M3-BODY-001` 74 次提交，其中 59 次零代码路径字节。
13. 最大提案 3,709 行（BODY-001）；五个 `NOT_STARTED` 提案合计 6,837 行。
14. `61ea20b` 于 2026-08-07 落地（R12 前置 ④ 已满足）。
15. `analyze_m3_body.py`：110 个 `raise AnalysisError`；`canonical_trial_id`
    （:486-505）冻结十 ID 且拒绝一切新 attempt 后缀；predecessor SHA 是
    :127-131 手写字面量；`metrics_projection_aspect_mismatch` 在
    :1232-1239（R10/R11/R12 前提）。

**口径差异（方向成立、数值口径不同，不构成缺陷）：**

- “纯文档提交 326/415 = 78.6%”：按“不触碰五个代码路径”口径实测
  415−83 = 332（80.0%）；按“仅 docs/”口径实测 394（94.9%）。两口径均
  支持论点，实际比声称更极端。
- “此后 271 次提交零关闭”：`--since=2026-07-27` 实测 293；量级一致。

**未独立复验（作者自证，不承载本决策任何门槛）：** 44 裁定轮的
18/16/5/3/2 成因分类；条件 5“50 次运行 0 真阳性”的精确计数；“12 轮纯
闭环复核 0 新阻断”。§3.1 七条拦截记录与 `docs/reviews/`、状态板、授权
账本既有叙述抽查一致（round 20 §B.4/§B.6 勘误、round 21
`check_track_env.py` 假阴性均有记载锚点）。

### §B 逐项处置

| 项 | 处置 |
|---|---|
| R1 | 接受。PLAY_GOVERNING 定义唯一化见 BC-C7-2；重述同步见 BC-C7-4 |
| R2 | 接受。机制分叉在授权时定死（BC-C7-3）；各角色收工自检不受 R2 影响 |
| R3 | 接受。四条件逐字保留；接受角色复算的接触隔离见 BC-C7-5 |
| R4 | 接受。CLASS_3 闭集逐字执行；白名单加 `docs/evidence/*` 与分级同批生效 |
| R5 | 接受。§A 第 6/7 项两处已证实漂移的修复是第一批必含项 |
| R6 | 接受。对存量提案追溯适用（BC-C7-8） |
| R7 | 接受。`passed_candidate` 行格式定死（BC-C7-9） |
| R8 | 技术接受。它修改用户授权的 COORD-003，仅用户可签；同批契约见 BC-C7-10 |
| R9 | 技术接受，但归协调批次而非实现批次（BC-C7-6）；删归档机械与否是独立用户决策（§10.2） |
| R10 | 接受为实现范围；新开 work ID 走完整六步 + 强制停点（BC-C7-6） |
| R11 | 接受。counted-invalid 语义预注册（BC-C7-7）；ID 参数化触及冻结采集身份契约，须用户点名授权 + 冻结语料回归（BC-C7-11） |
| R12 | 方向接受，本轮不决；前置 ①②③ 齐备后由用户另行授权；配额上限 2 予以背书 |

### §C Binding clarifications（协调/实现批次按字面执行）

- **BC-C7-1（零授权）**：本接受不构成任何执行授权。每一批开工前必须存在
  `docs/authorizations.md` 用户逐字条目；协调批次提交信息必须引用该条目
  （workflow §7 规则 7 原语义不变）。
- **BC-C7-2（PLAY_GOVERNING 唯一定义）**：集合的权威文本定义只落
  workflow §4.4 一处（成员照本文 §5 R1 逐字，含 `ProjectSettings/`、
  `Packages/packages-lock.json`、work item 冻结集点名的操作单文件）；
  其他文件只引用名字不复抄；后续机械化实现必须读同一定义或自带一致性
  断言。第一批不新增工具。
- **BC-C7-3（R2 机制定死）**：授权时二选一并写死其一：(a) 以 commit-msg
  钩子（pre-commit 阶段读不到提交信息）从角色 trailer 调用
  `check_role_writes.py`；(b) 工作流明文写“已提交批次的写入归因不再机械
  检查”。各角色收工的未提交自检（`--role <role>`）保留，不受 R2 影响。
- **BC-C7-4（重述位置全覆盖）**：第一批必须同批修改全部重述位置，实测
  清单——条件 5：workflow §4.3.1、`AGENTS.md:145`、
  `docs/roles/acceptance.md:15`、`.claude/commands/accept.md:19`；
  滚动节机械（若 R9 获批）：`AGENTS.md`、workflow §6、
  `docs/roles/chore.md`、`.claude/commands/chore.md`、`check_docs.py` +
  `rotate_docs.py` + `tests/test_check_docs.py`；单线纪律：`AGENTS.md`、
  workflow §7 规则 0、`check_docs.py`（`MAX_ACTIVE_HANDOFFS`）。
  **复核轮 1 F2 追加**：`docs/current-status.md` 自身两处散文重述——
  表头的归档/轮换句（属 R9 清单）与 Active handoffs 节首的单线纪律句
  （属 R8 清单）。仓库外 `~/.codex/prompts/codex.md`
  （AGENTS.md:129-130）由用户手动同步，账本记一句。漏改任一处即 R5 类
  漂移，批次不合格。
- **BC-C7-5（R3 条件 2 接触隔离）**：接受角色 revert→跑测→恢复的复算在
  一次性 worktree 或等价隔离中进行，主工作树对实现文件保持零字节改动。
- **BC-C7-6（批次结构）**：R9 是基础设施改动，归协调批次；R10/R11 新开
  独立 work ID（建议 `P1-M3-TOOL-001`）走已接受范围 → 实现 → 强制停点
  （触及 Play 治理与试验协议）→ 完整复核的正常路径。
- **BC-C7-7（counted-invalid 预注册）**：完成握手 + 暂停窗遥测门通过后
  acquisition 即不可作废；此后任何机器门失败的处置预注册为：槽位照常
  消耗、终态 `TRIAL_COUNTED_INVALID_<gate>`、写入受追踪 ledger、进论文
  附录、不重试、不重跑、不得因此修改任何门或参数；R12 语境下消耗配额、
  不触发追加 GO。这与 §5 R12“响亮作废”的用语统一为：post-count 失败是
  counted-invalid，不是可重试的 void。
- **BC-C7-8（R6 追溯）**：退修计数按既有轮次追溯生效：`P1-SCENE-005`
  （4 轮）、`P1-SCENE-007`（2 轮）、`P1-VLM-SCOPE-001`（4 轮）、
  `P1-VLM-CAL-001`（4 轮）解冻后直接进入用户二选一，不再有自行退修轮。
- **BC-C7-9（passed_candidate 格式）**：通过轮在 `docs/reviews/<id>.md`
  verdict 块内写一行 `passed_candidate: <40 位完整 SHA>`；
  `REWORK_REQUIRED` 轮禁止出现该行；存量不回改。
- **BC-C7-10（R8 同批 + 解析契约）**：`AGENTS.md`/workflow 文本、
  `MAX_ACTIVE_HANDOFFS` 常量、`Consuming` 列、Gate-echo 检查同一提交
  落地。echo 语义定死：Active handoffs 行内每个被引用的 work ID（含本行
  自身的）都必须携带其 Gate board Overall 列当前反引号内 token 的逐字
  拷贝，检查器逐一比对，不一致拒绝提交；精确解析格式由该协调批次定义
  并配测试。
- **BC-C7-11（冻结语料回归）**：任何触及 `analyze_m3_body.py` 门逻辑的
  批次必须对 attempt-4 冻结语料（`runtime/runs/…-attempt-4/` 帧与真值）
  重跑并逐字节复现 A1 receipt；十个冻结采集 ID 的现行拒绝语义在真实
  void 发生前保持激活——参数化 attempt 是休眠能力，`attempt>1` 仅凭
  ledger 中真实 predecessor void 收据启用。
- **BC-C7-12（A1 门不对称披露）**：R10 遥测暂停窗上线后，A1（人报数门）
  与后续 trial（遥测门）的实施差异必须写进批次证据与论文材料；是否对
  A1 归档遥测做仅披露性回算由用户决定，无论结果如何 round 38 的 A1
  关闭处置不重开，除非用户显式重开。
- **BC-C7-13（预算口径）**：本文 ≤400 行硬预算约束提案正文（§1–§10，
  实测 395 行，达标）；验收决策记录不计入该预算。

### §D 用户决策点（本轮零授权，逐条待用户签字）

1. **第一批 R1–R8 是否整体授权。** 推荐整体签：R1↔R4/R7、R2↔钩子改动、
   R8 文本↔检查器四组内部不可拆（§10.1）；请一并选定 BC-C7-3 的
   (a)/(b) 分支。
2. **R9 是否授权**，含是否删除 `rotate_docs.py` 与按月归档机械
   （§10.2；现有两个归档文件保留只读）。
3. **R10/R11 是否开工**（新 work ID；其中 R11 的 ID 参数化改动冻结采集
   身份契约，需点名授权）。
4. **R12 本轮不决**；前置齐备后另议，配额上限 2 已获接受角色背书（§10.3）。
5. **操作单 revision 12 作者**（§10.4）：推荐 R4 白名单落地后由接受角色
   撰写；否则维持实现角色，多一次角色切换。
6. **轨道关系**：`P1-M3-BODY-001` 的下一个 GO 决策不受本轮影响；若签
   第一批，A2 是否按 §9 步骤 1 通道执行由该 GO 的逐字条款决定。

### §E 依据摘要

有实际拦截记录的门（§3.1 七条 + 红线 A/B）全部原样保留；削减对象全部
落在零拦截记录的规则上；三处“必须先修”的事实（§4.1/4.2/4.3）逐字核验
成立，且每一处都对应一次已发生的作废。本决策引用的全部机械声称已在 §A
复现；未复现项仅是动机统计，不承载任何门槛。

## Acceptance round 2（2026-08-12）

- **复核轮 1 消化**（`docs/reviews/COORD-007.md`，`PASS_WITH_NOTES` on
  `84b0787`）：F1 闭合——头部 Status 已更新；F2 闭合——BC-C7-4 追加
  状态板自身两处重述（见上），且两处改写与清单修正落在同一个授权批次
  提交内，新规则文本生效时无失效散文窗口。
- N1–N6 留档采纳：N4 行号以 `def canonical_trial_id`（:486）为准；
  N3 两口径均在 ≤400 预算内；N2 转为 R10/R11 批次的证据义务（"30 条
  补追行"须给出机器出处或删去）；N5 建议（提案在决策前先行落盘）自
  下一提案起执行。
- **用户授权与执行**（账本 2026-08-12 COORD-007 条目）：第一批
  R1–R8 + R9 获整体授权，R2 取 BC-C7-3 (b) 明写移除，操作单
  revision 12 归接受角色（R4 白名单生效后）。本轮产出即协调批次本身：
  workflow §4.2/§4.3.1/§4.4/§5/§6/§7、AGENTS.md、五份角色细则、
  `/accept`、`/chore` 命令、`check_docs.py`（执行轨道纪律 + Gate-echo）、
  `check_role_writes.py`（通配 INFRA、`--infra-fix`、接受角色
  `docs/evidence/*`）、测试更新、`rotate_docs.py` 与其测试删除、状态板
  `## Log` 合并。R10/R11 与 R12 仍未授权未开工。

## Acceptance round 3（2026-08-12）—— 落地件的复核缺口与停点确认

触发：`/accept` 常规开工，状态板无待处置接受项（唯一消耗性轨道
`P1-M3-BODY-001` 等用户 GO，三条零消耗行按用户指示 `PAUSED_*`）。逐条
核对第一批落地件时发现下列缺口。本轮零执行授权，不改任何既有 verdict。

### §A 缺口：落地件的 PLAY_GOVERNING 半边从未被独立复核

- 复核轮 1 的候选是"提案正文 + Acceptance round 1"同一提交
  （`docs/reviews/COORD-007.md` 的 `passed_candidate` 行），该提交**零**
  `tools/`/`tests/` 字节——复核文件自述"全部为文档路径，零
  `controller/ Assets/ tools/ tests/ config/` 字节"。
- 协调批次落地提交（`git log --grep="^COORD-007: 协调批次落地第一批"`，
  实测唯一命中）在 PLAY_GOVERNING 上改动 6 条路径：`tools/check_docs.py`、
  `tools/check_role_writes.py`、`tests/test_check_docs.py`、
  `tests/test_check_role_writes.py`，加 `tools/rotate_docs.py` 与
  `tests/test_rotate_docs.py` 的删除。
- 按 workflow §4.4 开轮资格（R1，本批次自身引入）：
  `<passed_candidate>..<落地提交>` 在 PLAY_GOVERNING 上非空，复核轮 2
  **有资格开启**。
- 严重性：这段代码现在是每次提交的**活门**（`tools/githooks/pre-commit`
  只 exec `check_docs.py`），且执行轨道纪律与 Gate-echo 两项机检是 R8
  的全部机械载体。任一项形同虚设，正是 §5 R5(a) 自己诊断出的"规则说
  保护、工具不保护"型漂移——只是这次漂移会落在新代码里。接受角色不签发
  独立复核（workflow §1 边界），故只记缺口、定范围，不作判定。

明确：这**不是** §4.3.1 的强制停点——该清单不含基础设施批次，本批不改
帧/控制协议、坐标或时间语义、主指标定义、安全约束或模型决策逻辑。开轮
依据是 §4.4 开轮资格加上"活门代码零独立复核"这一事实，由接受角色判断
开启，不追认为强制项。

### §B 停点确认（workflow §4.3.1 四条件）

1. **范围与接口冻结**：成立。第一批 R1–R9 已落地；R10/R11（新 work ID）
   与 R12 未授权未开工，账本条目逐条列明未授权项。
2. **相称的实现者测试通过**：成立，且由本角色**独立重跑**（非转述提交
   信息）——`python3 -m unittest tests.test_check_docs
   tests.test_check_role_writes` → `Ran 22 tests … OK`；
   `.venv-track/bin/python -m unittest discover -s tests` →
   `Ran 513 tests … OK (skipped=1)`；`python3 tools/check_docs.py` 在
   当前树通过。三项与提交信息声称逐字一致。
3. **已知 Unity 失败**：不适用，本批零运行时行为、无 Unity 用例。本条
   **不构成** `UNITY_NA` 主张（`UNITY_NA` 须复核角色附议，本轮不申请）。
4. **复核文件/状态板/候选/未验证风险已更新**：本轮同批更新状态板并写明
   §C 未验证风险清单。

### §C 交给复核轮 2 的范围（是待核实的主张，不是复核边界）

- Diff 端点：起点由 `docs/reviews/COORD-007.md` 最近一行
  `passed_candidate` 运行时派生（R7 禁手写可派生标识），终点为上述唯一
  命中的落地提交；逐文件核对 6 条 PLAY_GOVERNING 路径与同批文档路径。
- 接受角色的未验证风险（非穷举，不预设结论）：
  1. `check_track_discipline`：`Consuming` 取值校验、`PAUSED` 前缀判定
     （大小写与反引号剥离）、分隔行与短行跳过，是否会静默漏计交接行。
  2. `check_handoff_gate_echo`：现实现只对**同时**满足"落在反引号内"且
     "在 Gate board 有行"的 work ID 生效——散文中未加反引号的引用、以及
     Gate board 无行的 ID（如 `COORD-007` 自身）不触发 echo。BC-C7-10
     的 echo 语义原文是"行内每个被引用的 work ID"；这是有意设计还是
     假阴性，由复核判定。
  3. `INFRA_PATTERNS` 改通配 `tools/check_*.py` 后，`--infra-fix` 的
     路径闭集是否真的排除其他一切路径（R5 例外不得成为万能通道）。
  4. 接受角色白名单新增 `docs/evidence/*` 是否越出 R4 授权语义。
  5. `rotate_docs.py` 及其测试删除后是否留下悬挂引用或失效导入；
     `docs/archive/` 现有两文件的只读性未被任何代码路径触碰。
  6. 状态板四滚动节并入 `## Log` 时是否丢失任何未闭义务（合并前后条目
     逐条对照）。
- 不在范围：R10/R11/R12（未授权未开工）、任何 M3′ 冻结项、任何 Play。

### §D 轨道与后续

- 本轮零执行授权：不申请 GO、不创建/消耗 scenario/session/run ID、不动
  Play 配额或 API 预算；`P1-M3-BODY-001` 的下一个 GO 决策轨道不受影响。
- 新交接行 `Consuming = no`，占两条零消耗名额之一，符合 R8 修订后的
  执行轨道纪律。
- 复核轮 2 若为 `REWORK_REQUIRED`，修复属基础设施，只能走两条路径之一：
  workflow §7 规则 7 的 COORD-007 R5 自修复例外（只改 `tools/check_*.py`
  与 `tests/test_check_*.py` 的单独提交，提交信息贴失败输出），或另开
  用户授权的协调批次；两者都不得与证据产出混在同一提交。

## Acceptance round 4（2026-08-12）—— 复核轮 2 返工闭合执行

触发：复核轮 2 `REWORK_REQUIRED`（F3/F4/F5，全 CLASS_2）；用户当轮
指令"查看review的结果，修改流程上的漏洞"逐字入账（账本 2026-08-12
「授权修复复核轮 2 判定的三条流程漏洞」条目）。

### §A 修复执行（两条通道，各自单独提交）

- **F4/F5 —— R5 `--infra-fix` 单独提交**（非复核角色=本接受会话执行，
  符合复核轮 2 对执行者的限定）：`split_table_row` 反引号感知切列
  （F4 根因）；`gate_overall_tokens` 行长不足/Overall 无 token 即违规
  （F4/N9 fail-closed）；`check_track_discipline` 畸形行响亮拒绝
  （F5）。四条修复前必失败的具名回归测试（含复核建议的两条名字），
  失败输出贴在提交信息；`--infra-fix` 纯度检查通过（恰 2 路径）。
- **同批自查新增**：真实板篡改探针复跑时发现 **F4 同类第四洞**——
  `WORK_ID_RE` 只匹配单段 AREA，`P1-M3-BODY-001`、`P1-VLM-CAL-001`、
  `P1-M3M4-SCOPE-002` 等多段 ID 在**引用侧**从未进入 echo 执法（token
  侧修复后仍漏）。同一 `--infra-fix` 提交内修复并配第四条必失败测试；
  修复后 BODY-001/VLM-CAL/M3M4-SCOPE/SCENE-005 四路 `@STALE_TOKEN`
  篡改探针全部被拒。交复核轮 3 独立验证。
- **F3 —— 协调批次**（引用上述账本条目）：AGENTS.md 与 workflow §7
  规则 7 的 R5 例外句改为"非复核角色"，明写红线 A 五路径绝对禁令
  优先；`check_role_writes.py` docstring 同批注明。复核给出的两种等价
  改法取"排除复核角色"形；`CLAUDE.md` 的复核绝对句经此排除后与例外句
  一致，无需改动（对齐即闭合，`NOT_MECHANIZABLE` 定点复看三文件由
  复核轮 3 执行）。

### §B 证据与后续

- focused 26/26 + 14/14；真实状态板 `check_docs.py` 通过；修复前失败
  输出与修复后探针结果在 `--infra-fix` 提交信息内。
- 按 R1 开轮资格，`passed_candidate`（复核文件派生）至修复后候选在
  PLAY_GOVERNING 上非空 → **复核轮 3 成立**，范围=区间全部路径；F3 的
  `NOT_MECHANIZABLE` 定点复看与 F4/F5 回归测试核验（含 §4.4 闭合四
  条件）在该轮执行。本轮零执行授权，零 Play/ID/配额，BODY-001 GO
  轨道不变。

## Acceptance round 5（2026-08-13）—— F3/F4/F5 正式闭合与 N12 裁定

触发：复核轮 3 `PASS_WITH_NOTES` on `544cd18`；用户指令逐字入账（账本
2026-08-13「指令完成 §4.4 条件 2 复算与 N12 显式裁定」条目）。复核轮 3
批次由复核会话遗留未提交，本会话代执行 git commit（内容零改动，路径按
`--role review` 白名单核对通过，纯代录）。

### §A F3/F4/F5 按 §4.4 四条件正式闭合 —— **CLOSED**

1. **fixture 生产路径**：采纳复核轮 3 N14 的裁量——`check_docs.py` 的
   生产输入即状态板 markdown 文本，夹具为真实形状（含反引号内
   `C_track|geom` gate 行），另有真实板篡改探针补强；不判违反。N14 的
   "真实板冒烟断言"建议记为 R10/R11 批次证据设计输入（与 N16 并列）。
2. **接受角色亲自 revert 复算（本轮执行）**：一次性副本
   `accept-c2-COORD-007`（detached HEAD）内 `git checkout c617a98^ --
   tools/check_docs.py`（字面 `git revert -n` 会连同绑定测试一并回退、
   无法观察失败，按条款意图执行"旧代码 + 新测试"）；实测
   `Ran 12 … FAILED (failures=4)`，失败恰为四条具名测试、其余 8 条
   仍绿；恢复后 `OK`。副本已删，主树零字节接触（BC-C7-5）。
3. **Play 治理门**：零触碰，不触发。
4. **NOT_MECHANIZABLE 定点复看**：F3 三文件由复核轮 3 完成且附议定级。

F4、F5、F3 与第四洞（多段 `WORK_ID_RE`）至此**正式闭合**；复核轮 3 的
`passed_candidate: 544cd18` 为新的上一通过候选。

### §B F6 复判与 Notes 处置

- **F6（CLASS_3）**：同意定级（轨道会计正确、纯已执行步骤时态）；
  **追认**复核的就地应用——该句因复核自身合法的收工更新而失效，
  AGENTS「交接文字必须与现实一致…同一批次就地修正」当批适用且已完整
  披露，不回退。界线记录：R4 的"接受角色同轮应用"约束对**其他**工件的
  CLASS_3 补丁；`docs/current-status.md` 交接时效文字由收工角色当批
  就地修正、事后由接受角色复判追认。
- N11（提案 §5 R5 原文"任何角色"）：同意不回改正文；活规则以三处已改
  文件为准。N13/N15：附议为设计选择/既有行为。N16 + N14 建议：记为
  R10/R11 批次输入。

### §C N12 显式裁定（用户授权执行）

**裁定：凡在 Gate board 有行的反引号标识（work ID 与 `M1` 类里程碑行）
被交接行引用即进入 Gate-echo 执法；执法判据 = token 表成员资格，不再
以 work ID 形状正则作前置。** 理由：token 侧已收录的标识在引用侧免检
就是第四洞的形状；里程碑行的 Overall 同样是活门（M1 closure 待用户
授权），BC-C7-10 的解析契约随本裁定更新为成员资格判据。落地：
`--infra-fix` 提交删除 `WORK_ID_RE`（绑修复前必失败测试
`test_milestone_rows_enter_echo_grammar`）；协调批次同步 AGENTS.md 与
workflow §7 规则 0 措辞。**实战命中**：新判据启用即在 COORD-007 交接
行抓到一处真实裸 `M1` 引用（复核轮 3 收工文字），已先行补注记——
裁定生效当分钟即产生第一次真实拦截。

### §D 残留与轨道

- 本轮四个提交（复核轮 3 代录、账本、M1 注记、`--infra-fix`）加措辞
  协调批次与本记录，构成 `544cd18` 之后的全部 delta；其中 tools/tests
  改动按 R5 由**下一轮复核**逐文件 diff 覆盖，不强制立即开专轮。
- R10/R11 与 R12 仍未授权未开工；零 Play/ID/配额；`P1-M3-BODY-001`
  GO 决策仍是唯一消耗性轨道。
